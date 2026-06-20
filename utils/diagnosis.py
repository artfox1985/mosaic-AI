"""
utils/diagnosis.py — Sanity Check der Trainingsdaten

Prüft:
  - zero-mask rows  → sollte 0 sein
  - policy leak     → sollte < 1e-6 sein
  - p_loss          → sollte ~ln(NUM_ACTIONS) bei untrainiertem Netz sein
  - policy quality  → wie scharf/konzentriert sind die MCTS-Targets?

Verwendung:
    python -m utils.diagnosis
"""
import sys, torch, os, math, glob, pickle, random
import torch.nn.functional as F
from torch.utils.data import DataLoader
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.neural_net import MosaicDataset, MosaicNet, action_to_id
from config import DATA_DIR, INPUT_SIZE, NUM_ACTIONS


def run_diagnosis(data_dir: str, label: str):
    dataset = MosaicDataset(data_dir)
    if len(dataset) == 0:
        print(f"  ❌ Keine Daten in: {data_dir}")
        return

    print(f"\n{'='*55}")
    print(f"  DATENSATZ: {label}")
    print(f"{'='*55}")
    print(f"  Züge:         {len(dataset):,}")
    print(f"  Input Size:   {dataset.input_size}")

    loader = DataLoader(dataset, batch_size=32, shuffle=False)
    states, targets_p, targets_v, masks = next(iter(loader))

    zero_mask   = (masks.sum(1) == 0).sum().item()
    leak        = (targets_p * (1 - masks)).sum(1).max().item()
    mask_mean   = masks.sum(1).mean().item()
    mask_min    = masks.sum(1).min().item()
    mask_max    = masks.sum(1).max().item()

    model = MosaicNet(input_size=INPUT_SIZE, num_actions=NUM_ACTIONS)
    pred_p, *_ = model(states)
    masked_logits = pred_p + (masks - 1) * 1e9
    log_probs = F.log_softmax(masked_logits, dim=1)
    p_loss = (-torch.sum(targets_p * log_probs) / states.size(0)).item()

    max_loss = math.log(NUM_ACTIONS)
    has_nan  = torch.isnan(log_probs).any().item()
    has_inf  = torch.isinf(log_probs).any().item()

    print(f"{'─'*55}")
    print(f"  Mask legal/Zug: min={mask_min:.0f}  max={mask_max:.0f}  mean={mask_mean:.1f}")

    zm_icon = "✅" if zero_mask == 0 else "❌"
    print(f"  Zero-mask rows: {zero_mask}  {zm_icon}")

    leak_icon = "✅" if leak < 1e-6 else "❌"
    print(f"  Policy leak:    {leak:.6f}  {leak_icon}")

    pct = p_loss / max_loss * 100
    if pct > 95:   p_icon = "✅ ~Gleichverteilung (untrainiert)"
    elif pct > 50: p_icon = "🟡 Teilweise gelernt"
    else:          p_icon = "🟢 Gut strukturiert"
    print(f"  p_loss:         {p_loss:.4f} / {max_loss:.2f} ({pct:.1f}%)  {p_icon}")

    nan_icon = "✅" if not has_nan else "❌"
    inf_icon = "✅" if not has_inf else "❌"
    print(f"  NaN: {has_nan}  {nan_icon}    Inf: {has_inf}  {inf_icon}")
    print(f"{'='*55}")


def run_policy_quality(data_dir: str, label: str, max_files: int = 100):
    """
    Analysiert die Qualität der MCTS Policy-Targets:
    - Wie konzentriert sind die Wahrscheinlichkeiten?
    - Wie viele Aktionen bekommen >10% Wahrscheinlichkeit?
    - Welche Action-IDs werden am häufigsten gewählt?
    """
    files = sorted(glob.glob(os.path.join(data_dir, "*.pkl")))
    if not files:
        print(f"  ❌ Keine .pkl-Dateien in: {data_dir}")
        return
    if len(files) > max_files:
        files = random.sample(files, max_files)

    print(f"\n{'='*55}")
    print(f"  POLICY QUALITÄT: {label}")
    print(f"  (Analyse von {len(files)} Datei(en))")
    print(f"{'='*55}")

    total_steps = 0
    entropy_sum = 0.0
    max_prob_sum = 0.0
    concentrated_count = 0   # max_prob > 0.9
    flat_count = 0            # max_prob < 0.3
    actions_over_10pct = []
    action_id_dist = Counter()

    for f in files:
        with open(f, 'rb') as fh:
            data = pickle.load(fh)

        for step in data:
            policy = step.get('policy', [])
            if not policy:
                continue
            total_steps += 1
            probs = [p['prob'] for p in policy]
            max_p = max(probs)
            entropy = -sum(p * math.log(p + 1e-9) for p in probs)
            over_10 = sum(1 for p in probs if p > 0.1)

            entropy_sum     += entropy
            max_prob_sum    += max_p
            actions_over_10pct.append(over_10)

            if max_p > 0.9: concentrated_count += 1
            if max_p < 0.3: flat_count += 1

            for p in policy:
                if p['prob'] > 0.1:
                    action_id_dist[action_to_id(p['action'])] += 1

    if total_steps == 0:
        print("  ❌ Keine Schritte gefunden")
        return

    avg_entropy  = entropy_sum / total_steps
    avg_max_prob = max_prob_sum / total_steps
    avg_over_10  = sum(actions_over_10pct) / len(actions_over_10pct)
    max_entropy  = math.log(NUM_ACTIONS)

    print(f"{'─'*55}")
    print(f"  Analysierte Schritte: {total_steps:,}")
    print(f"{'─'*55}")

    # Entropie
    ent_pct = avg_entropy / max_entropy * 100
    if ent_pct < 20:   ent_icon = "🟢 Sehr scharf (gut für Training)"
    elif ent_pct < 40: ent_icon = "🟡 Moderat scharf"
    elif ent_pct < 70: ent_icon = "🟠 Eher flach"
    else:              ent_icon = "🔴 Sehr flach — kaum Signal"
    print(f"  Ø Entropie:     {avg_entropy:.3f} / {max_entropy:.2f} ({ent_pct:.1f}%)  {ent_icon}")

    # Max-Wahrscheinlichkeit
    if avg_max_prob > 0.7:   mp_icon = "🟢 Klare Präferenz"
    elif avg_max_prob > 0.4: mp_icon = "🟡 Moderate Präferenz"
    else:                    mp_icon = "🔴 Keine klare Präferenz"
    print(f"  Ø Max-Prob:     {avg_max_prob:.3f}  {mp_icon}")

    print(f"  Ø Aktionen >10%:{avg_over_10:.1f}")
    print(f"  Konzentriert (>90%): {concentrated_count/total_steps*100:.1f}%")
    print(f"  Sehr flach   (<30%): {flat_count/total_steps*100:.1f}%")

    print(f"{'─'*55}")
    print(f"  Top 10 Action-IDs (häufig >10% Prob):")
    for aid, cnt in action_id_dist.most_common(10):
        print(f"    ID {aid:4d}: {cnt:5d}×")

    print(f"{'='*55}")

    # ── Stone-only Analyse (strategische Züge ohne Pflichtaktionen) ────────────
    # Obligatorische Aktionen herausfiltern:
    # pass(0), end_tiling(1), bonus_chip(478-481), dome(328-435), dome_stack(436-471)
    OBLIGATORY = set(range(328, 482))  # dome + dome_stack + bonus_chip
    OBLIGATORY.add(0)   # pass
    OBLIGATORY.add(1)   # end_tiling

    stone_steps = 0
    stone_entropy_sum = 0.0
    stone_max_prob_sum = 0.0
    stone_concentrated = 0
    stone_flat = 0
    stone_id_dist = Counter()

    for f in files:
        with open(f, 'rb') as fh:
            data = pickle.load(fh)
        for step in data:
            policy = step.get('policy', [])
            if not policy:
                continue
            # Nur Schritte wo die Top-Aktion eine Stone-Aktion ist (10-273)
            top_action = max(policy, key=lambda p: p['prob'])
            top_id = action_to_id(top_action['action'])
            if top_id in OBLIGATORY:
                continue  # Schritt überspringen wenn Pflichtaktion dominiert

            # Nur Stone-Aktionen in der Policy berücksichtigen
            stone_policy = [p for p in policy if 10 <= action_to_id(p['action']) <= 273]
            if not stone_policy:
                continue

            # Renormalisieren
            total_p = sum(p['prob'] for p in stone_policy)
            if total_p < 1e-6:
                continue
            stone_probs = [p['prob'] / total_p for p in stone_policy]

            max_p = max(stone_probs)
            entropy = -sum(p * math.log(p + 1e-9) for p in stone_probs)

            stone_entropy_sum  += entropy
            stone_max_prob_sum += max_p
            stone_steps += 1

            if max_p > 0.9: stone_concentrated += 1
            if max_p < 0.3: stone_flat += 1

            for p, prob in zip(stone_policy, stone_probs):
                if prob > 0.1:
                    stone_id_dist[action_to_id(p['action'])] += 1

    if stone_steps > 0:
        avg_s_ent  = stone_entropy_sum / stone_steps
        avg_s_maxp = stone_max_prob_sum / stone_steps
        max_stone_entropy = math.log(240)  # max Stone-Aktionen ~240

        ent_pct_s = avg_s_ent / max_stone_entropy * 100
        if ent_pct_s < 20:   ent_icon_s = "🟢 Sehr scharf"
        elif ent_pct_s < 40: ent_icon_s = "🟡 Moderat scharf"
        elif ent_pct_s < 70: ent_icon_s = "🟠 Eher flach"
        else:                ent_icon_s = "🔴 Sehr flach"

        print(f"\n{'='*55}")
        print(f"  STONE-ONLY ANALYSE (strategische Züge)")
        print(f"  (Pflichtaktionen herausgefiltert: Chips, Kuppel, Pass)")
        print(f"{'─'*55}")
        print(f"  Analysierte Schritte: {stone_steps:,} / {total_steps:,} ({stone_steps/total_steps*100:.0f}%)")
        print(f"{'─'*55}")
        print(f"  Ø Entropie:     {avg_s_ent:.3f} / {max_stone_entropy:.2f} ({ent_pct_s:.1f}%)  {ent_icon_s}")
        print(f"  Ø Max-Prob:     {avg_s_maxp:.3f}")
        print(f"  Konzentriert (>90%): {stone_concentrated/stone_steps*100:.1f}%")
        print(f"  Sehr flach   (<30%): {stone_flat/stone_steps*100:.1f}%")
        print(f"{'─'*55}")
        print(f"  Top 10 Stone-IDs (häufig >10% Prob):")

        def decode_stone(aid):
            # stone = 10 + color_idx*48 + r_id*6 + factory_index
            # r_id = row + 1: r_id=0 → Strafleiste, r_id=1..6 → Reihe 1-6
            # factory: 0-3=F1-F4, 4=GF, 5=Mond
            a       = aid - 10
            f_idx   = a % 6
            r_id    = (a // 6) % 8
            c_id    = a // 48
            colors  = ['blau','gelb','rot','schwarz','türkis']
            sources = ['F1','F2','F3','F4','GF','Mond']
            color   = colors[c_id]  if c_id  < 5 else '?'
            source  = sources[f_idx] if f_idx < 6 else '?'
            row_str = 'Strafleiste' if r_id == 0 else f'Reihe {r_id}'
            return f"{color} von {source} → {row_str}"

        for aid, cnt in stone_id_dist.most_common(10):
            print(f"    ID {aid:4d}: {cnt:5d}×  ({decode_stone(aid)})")
        print(f"{'='*55}")


def pick_file() -> str | None:
    """Öffnet einen nativen Datei-Dialog (Windows/Mac/Linux)."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        path = filedialog.askopenfilename(
            title="Trainingsdatei auswählen",
            initialdir=str(DATA_DIR),
            filetypes=[("Pickle files", "*.pkl"), ("Alle Dateien", "*.*")]
        )
        root.destroy()
        return path if path else None
    except Exception as e:
        print(f"  ⚠️  Datei-Dialog nicht verfügbar: {e}")
        return None


def pick_files() -> list[str]:
    """Öffnet einen Datei-Dialog mit MEHRFACH-Auswahl (Strg/Shift im Dialog).
    Gibt eine Liste der gewählten Pfade zurück (leer wenn abgebrochen)."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        paths = filedialog.askopenfilenames(
            title="Trainingsdatei(en) auswählen — mehrere mit Strg/Shift",
            initialdir=str(DATA_DIR),
            filetypes=[("Pickle files", "*.pkl"), ("Alle Dateien", "*.*")]
        )
        root.destroy()
        return list(paths) if paths else []
    except Exception as e:
        print(f"  ⚠️  Datei-Dialog nicht verfügbar: {e}")
        return []


def run_penalty_bias(data_dir: str, label: str, max_files: int = 100):
    """
    Prüft ob die MCTS-Policy Strafleisten-Züge (r_id=0) nur ANBIETET oder
    tatsächlich BEVORZUGT. Unterscheidet 'harmlos erzwungen' (am Rundenende
    bleiben unpassende Steine übrig) von 'problematischer Fehlpräferenz'
    (Strafleiste trotz verfügbarer Reihen-Alternative gewählt).

    Strafleisten-Stone-IDs vom Mond (f_idx=5, alle 5 Farben): 15, 63, 111, 159, 207
    """
    from agents.neural_net import action_to_id

    PENALTY_MOON_IDS = {15, 63, 111, 159, 207}

    files = sorted(glob.glob(os.path.join(data_dir, "*.pkl")))
    if not files:
        print(f"  ❌ Keine .pkl-Dateien in: {data_dir}")
        return
    if len(files) > max_files:
        files = random.sample(files, max_files)

    print(f"\n{'='*55}")
    print(f"  STRAFLEISTEN-BIAS: {label}")
    print(f"  (Analyse von {len(files)} Datei(en))")
    print(f"{'='*55}")

    n_steps = 0
    penalty_offered = 0       # Strafleisten-Zug war in der Policy
    penalty_prob_sum = 0.0    # Summe seiner Wahrscheinlichkeiten
    penalty_chosen = 0        # Strafleiste hatte HÖCHSTE prob
    penalty_when_alt = 0      # Strafleiste TOP obwohl Reihen-Zug verfügbar

    for f in files:
        with open(f, 'rb') as fh:
            data = pickle.load(fh)
        for step in data:
            policy = step.get('policy', [])
            if not policy:
                continue
            n_steps += 1

            best_prob = -1.0
            best_is_penalty = False
            has_row_alt = False
            for entry in policy:
                a = entry.get('action', {})
                p = entry.get('prob', 0.0)
                try:
                    aid = action_to_id(a)
                except Exception:
                    aid = None
                is_penalty = aid in PENALTY_MOON_IDS
                if is_penalty:
                    penalty_offered += 1
                    penalty_prob_sum += p
                elif a.get('type') == 'stone' and a.get('pattern_row') not in (None, -1):
                    has_row_alt = True
                if p > best_prob:
                    best_prob = p
                    best_is_penalty = is_penalty
            if best_is_penalty:
                penalty_chosen += 1
                if has_row_alt:
                    penalty_when_alt += 1

    print(f"{'─'*55}")
    print(f"  Schritte analysiert:             {n_steps:,}")
    print(f"  Strafleisten-Zug angeboten:      {penalty_offered:,}")
    if penalty_offered:
        avg_p = penalty_prob_sum / penalty_offered
        print(f"  Ø Prob wenn angeboten:           {avg_p:.3f}")
    else:
        avg_p = 0.0
    pct_chosen = 100 * penalty_chosen / max(n_steps, 1)
    print(f"  Strafleiste war TOP-Wahl:        {penalty_chosen:,} ({pct_chosen:.1f}%)")
    print(f"    davon mit Reihen-Alternative:  {penalty_when_alt:,}")
    print(f"{'─'*55}")
    if penalty_offered and avg_p < 0.15:
        print("  → ✅ HARMLOS: angeboten, aber kaum bevorzugt (niedrige Prob)")
    elif penalty_chosen and penalty_when_alt > penalty_chosen * 0.5:
        print("  → ⚠️ VERDÄCHTIG: Strafleiste oft TROTZ Reihen-Alternative gewählt")
        print("     (möglicher Rest eines Bewertungs-/Perspektiv-Problems)")
    else:
        print("  → 🟡 Strafleiste meist nur wenn keine Alternative (erzwungen, ok)")
    print(f"{'='*55}")


def _run_on_selected_files(runner, max_files: int | None = None):
    """Hilfsfunktion: lässt mehrere Dateien wählen, kopiert sie in ein
    Temp-Verzeichnis und führt die übergebene Analyse-Funktion darauf aus."""
    import tempfile, shutil
    print("  Öffne Datei-Dialog (Mehrfach-Auswahl mit Strg/Shift)...")
    paths = pick_files()
    if not paths:
        print("  ❌ Keine Datei ausgewählt.")
        return
    # Label: bei einer Datei der Name, sonst Anzahl
    if len(paths) == 1:
        label = Path(paths[0]).name
    else:
        label = f"{len(paths)} Dateien"
    print(f"  ✓ {len(paths)} Datei(en) gewählt.")
    with tempfile.TemporaryDirectory() as tmp:
        for p in paths:
            shutil.copy(p, tmp)
        if max_files is not None:
            runner(tmp, label, max_files=max_files)
        else:
            runner(tmp, label)


def run_value_simulation(data_dir: str, label: str, max_files: int = 100):
    """
    Berechnet optimale margin_cap und max_winner_score aus den Spielergebnissen.
    Ziel: maximaler Anteil im mittleren/starken Bereich, wenig gecappt bei 1.0.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from agents.neural_net import compute_win_val

    files = sorted(glob.glob(os.path.join(data_dir, "*.pkl")))
    if len(files) > max_files:
        files = random.sample(files, max_files)
    if not files:
        print(f"  ❌ Keine .pkl-Dateien in: {data_dir}")
        return

    # Rohe Spielergebnisse sammeln
    results_dict = {}
    for f in files:
        with open(f, 'rb') as fh:
            data = pickle.load(fh)

        for step in data:
            if "game_id" in step and "scores" in step and "winner" in step:
                # Da jeder Schritt das Spiel-Ergebnis enthält, überschreiben wir 
                # es im Dictionary einfach. Am Ende hat jede game_id exakt 1 Eintrag.
                gid = step["game_id"]
                results_dict[gid] = (step["scores"], step["winner"])

    # Das Dictionary wieder in eine einfache Liste umwandeln
    results = list(results_dict.values())

    if not results:
        print("  ❌ Keine Spielergebnisse mit 'game_id' gefunden (altes Format?)")
        return

    n = len(results)
    margins      = [abs(s[0]-s[1]) for s,w in results]
    winner_scores= [s[w] for s,w in results]
    zerozero     = sum(1 for m,ws in zip(margins,winner_scores) if m==0 and ws==0)

    import statistics as _st
    import numpy as np

    print(f"\n{'='*55}")
    print(f"  VALUE SIMULATION: {label}")
    print(f"  ({n} Spiele aus {len(files)} Datei(en))")
    print(f"{'─'*55}")
    print(f"  0:0 Spiele:        {zerozero:4d} ({zerozero/n*100:.1f}%)")
    print(f"  Ø Winner-Score:    {_st.mean(winner_scores):.1f}  (Max: {max(winner_scores)})")
    print(f"  Ø Margin:          {_st.mean(margins):.1f}  (Max: {max(margins)})")

    # Optimale Parameter berechnen
    # margin_cap: 75. Perzentil der Margins (nicht-null) → cap wo ~75% der Spiele darunter sind
    non_zero_margins = [m for m in margins if m > 0]
    non_zero_ws      = [ws for ws,m in zip(winner_scores,margins) if m > 0 or ws > 0]

    if non_zero_margins:
        margin_cap_opt = max(5, int(np.percentile(non_zero_margins, 75)))


    else:
        margin_cap_opt = 10

    if non_zero_ws:
        max_ws_opt = max(10, int(np.percentile(non_zero_ws, 80)))
    else:
        max_ws_opt = 20

    margin_cap_opt = round(margin_cap_opt / 5) * 5 or 5
    max_ws_opt     = round(max_ws_opt / 5) * 5 or 10

    print(f"{'─'*55}")
    print(f"  📊 EMPFOHLENE PARAMETER:")
    print(f"     --margin_cap       {margin_cap_opt}")
    print(f"     --max_winner_score {max_ws_opt}")
    print(f"{'─'*55}")
    print(f"  ℹ️  Die Empfehlung kalibriert die Skala auf den NORMALBEREICH:")
    print(f"     margin_cap = 75. Perzentil der Margins, max_winner = 80.")
    print(f"     Perzentil der Sieger-Scores. Der obere Score-Schwanz (klare,")
    print(f"     hohe Siege) wird damit bewusst auf win_val=1.0 gestaucht.")
    print(f"     → Für FRÜHE Trainingsgenerationen (Bootstrap/Iteration 0) ist")
    print(f"       das oft suboptimal: gerade die hohen Siege liefern die")
    print(f"       Abstufung 'solide vs. vernichtend gewonnen'. Dort lieber ein")
    print(f"       großzügigeres max_winner_score (z.B. 40) wählen, das fast")
    print(f"       nichts cappt (volle Auflösung). Faustregel: Gecappt-Anteil")
    print(f"       unten im Vergleich beachten — für Iteration 0 möglichst < 2%.")

    from agents.neural_net import compute_win_val
    for margin_cap, max_ws, desc in [
        (margin_cap_opt, max_ws_opt, "Empfohlen"),
        (15, 40, "Standard (15/40)"),
    ]:
        values = [compute_win_val(s, w, margin_cap, max_ws) for s, w in results]
        capped = sum(1 for v in values if v >= 1.0)
        weak   = sum(1 for v in values if v <= 0.15)
        medium = sum(1 for v in values if 0.15 < v <= 0.5)
        strong = sum(1 for v in values if v > 0.5)

        print(f"\n  [{desc}]  margin_cap={margin_cap}, max_winner={max_ws}")
        print(f"  Ø win_val: {_st.mean(values):.3f}  |  Gecappt (=1.0): {capped} ({capped/n*100:.1f}%)")
        print(f"  Schwach  (≤0.15): {weak:4d} ({weak/n*100:.1f}%)")
        print(f"  Mittel (0.15-0.5):{medium:4d} ({medium/n*100:.1f}%)")
        print(f"  Stark    (> 0.5): {strong:4d} ({strong/n*100:.1f}%)")

    print(f"\n{'='*55}")

    # Strafleisten-Bias direkt mit ausgeben (gehört thematisch zur Ergebnis-/
    # Entscheidungs-Analyse, daher kein eigener Menüpunkt mehr).
    run_penalty_bias(data_dir, label, max_files=max_files)


def main():
    print("\n📋 DIAGNOSIS — Trainingsdaten Analyse")
    print("─" * 55)
    print("  [1] Sanity Check  — alle Daten im data/ Ordner")
    print("  [2] Sanity Check  — Datei(en) auswählen (mehrere möglich)")
    print("  [3] Policy Qualität — alle Daten im data/ Ordner")
    print("  [4] Policy Qualität — Datei(en) auswählen (mehrere möglich)")
    print("  [5] Value Simulation + Strafleisten-Bias — alle Daten")
    print("  [6] Value Simulation + Strafleisten-Bias — Datei(en) auswählen")
    print("─" * 55)

    choice = input("  Auswahl (1/2/3/4/5/6): ").strip()

    if choice == "1":
        run_diagnosis(str(DATA_DIR), "data/")

    elif choice == "2":
        _run_on_selected_files(run_diagnosis)

    elif choice == "3":
        run_policy_quality(str(DATA_DIR), "data/")

    elif choice == "4":
        _run_on_selected_files(run_policy_quality, max_files=999)

    elif choice == "5":
        run_value_simulation(str(DATA_DIR), "data/")

    elif choice == "6":
        _run_on_selected_files(run_value_simulation, max_files=999)

    else:
        print("  ❌ Ungültige Auswahl.")


if __name__ == "__main__":
    main()