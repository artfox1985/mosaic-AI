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
# Netz/Dataset (PyTorch) liegen jetzt neben der Rust-Engine in engine/py/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine" / "py"))
from neural_net import MosaicDataset, MosaicNet, action_to_id
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


def _tiles_taken_from_state(state: dict, action: dict) -> int:
    """Wie viele Steine `action` (type='stone') aus `state` tatsächlich nimmt --
    Python-Pendant zu `mcts.rs::tiles_taken`. factory_index: 0-3=kleine
    Fabrik-Sonne, 4=Große-Fabrik-Sonne, 5=globaler Mond-Zug (oberste Stapel-
    Fliese je kleiner Fabrik + ALLE passenden aus dem GF-Mond-Pool)."""
    color = action.get('color')
    f_idx = action.get('factory_index', 0)
    factories = state.get('factories', [])
    large = state.get('large_factory', {}) or {}
    if f_idx <= 3:
        if f_idx < len(factories):
            return sum(1 for c in factories[f_idx].get('sun', []) if c == color)
        return 0
    if f_idx == 4:
        return sum(1 for c in large.get('sun', []) if c == color)
    if f_idx == 5:
        n = sum(
            1
            for f in factories
            for stack in f.get('moon', [])
            if stack and stack[-1] == color
        )
        n += sum(1 for c in large.get('moon', []) if c == color)
        return n
    return 0


def _row_remaining_capacity(state: dict, row_idx: int) -> int | None:
    """Freie Slots der Musterreihe `row_idx` des aktuell ziehenden Spielers,
    None wenn nicht ermittelbar (fehlendes Feld/Index)."""
    pi = state.get('current_player')
    players = state.get('players', [])
    if pi is None or not (0 <= pi < len(players)):
        return None
    rows = players[pi].get('pattern_lines', [])
    if not (0 <= row_idx < len(rows)):
        return None
    row = rows[row_idx]
    cap = row.get('capacity')
    tiles = row.get('tiles', [])
    if cap is None:
        return None
    return max(0, cap - len(tiles))


def _dome_row_has_open_matching_slot(state: dict, pi: int, row_idx: int, color: str) -> bool | None:
    """Python-Pendant zu `round_end::row_has_open_matching_slot`. None wenn
    nicht ermittelbar (fehlende Felder)."""
    players = state.get('players', [])
    if not (0 <= pi < len(players)):
        return None
    dome_grid = players[pi].get('dome_grid')
    if dome_grid is None:
        return None
    dome_row_idx = row_idx // 2
    if not (0 <= dome_row_idx < len(dome_grid)):
        return None
    valid_si = [(row_idx % 2) * 2, (row_idx % 2) * 2 + 1]
    for slot in dome_grid[dome_row_idx]:
        if not slot:
            continue
        spaces = slot.get('spaces', [])
        for si in valid_si:
            if si >= len(spaces):
                continue
            sp = spaces[si]
            if sp.get('filled') is not None or sp.get('locked'):
                continue
            typ = sp.get('type', 'NORMAL')
            if typ == 'WILD' or (typ == 'NORMAL' and sp.get('color') == color):
                return True
    return False


def _dome_row_fully_built(state: dict, pi: int, row_idx: int) -> bool | None:
    """True, wenn alle 3 Kuppelplatten der zu `row_idx` gehörigen Dome-Reihe
    bereits gelegt sind (kein leerer Slot mehr, an dem eine neue Platte mit
    passendem Space auftauchen könnte). None wenn nicht ermittelbar."""
    players = state.get('players', [])
    if not (0 <= pi < len(players)):
        return None
    dome_grid = players[pi].get('dome_grid')
    dome_row_idx = row_idx // 2
    if dome_grid is None or not (0 <= dome_row_idx < len(dome_grid)):
        return None
    return all(slot is not None for slot in dome_grid[dome_row_idx])


def run_penalty_bias(data_dir: str, label: str, max_files: int = 100):
    """
    Prüft, WARUM Steine auf der Strafleiste landen -- drei Kategorien:
    1. Explizit gewählt, KEINE Reihen-Alternative vorhanden (erzwungen, harmlos).
    2. Explizit gewählt, OBWOHL eine Reihen-Alternative existierte (verdächtig --
       möglicher Rest eines Bewertungs-/Perspektiv-Problems).
    3. Überlauf: eine Reihe wurde gewählt, aber mehr Steine genommen als noch
       Platz war (z.B. 3× türkis auf ein Feld mit nur 2 freien Slots) -- der
       Rest landet automatisch auf der Strafleiste, unabhängig von der Wahl.
    Alle drei nur anhand der TOP-Policy-Aktion je Schritt (nicht des real
    gespielten Zugs, der wird hier nicht mitgeführt).
    """
    from neural_net import action_to_id

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
    penalty_offered = 0       # Strafleisten-Zug (row=-1) war in der Policy
    penalty_prob_sum = 0.0
    penalty_chosen = 0        # Strafleiste (row=-1) hatte HÖCHSTE prob
    penalty_when_alt = 0      # ... obwohl ein Reihen-Zug verfügbar war
    overflow_chosen = 0       # TOP-Aktion zielt auf eine Reihe, überläuft aber
    overflow_tiles_sum = 0    # Summe der übergelaufenen Steine (TOP-Aktion)
    missing_state = 0
    kat2_cases = []           # Details je Kategorie-2-Fall (für Aufschlüsselung)

    for f in files:
        with open(f, 'rb') as fh:
            data = pickle.load(fh)
        for step in data:
            policy = step.get('policy', [])
            if not policy:
                continue
            n_steps += 1
            state = step.get('state')

            best_prob = -1.0
            best_action = None
            has_row_alt = False
            best_alt_prob = -1.0
            best_alt_action = None
            for entry in policy:
                a = entry.get('action', {})
                p = entry.get('prob', 0.0)
                is_penalty = a.get('type') == 'stone' and a.get('row', 0) == -1
                if is_penalty:
                    penalty_offered += 1
                    penalty_prob_sum += p
                elif a.get('type') == 'stone' and a.get('row') not in (None, -1):
                    has_row_alt = True
                    if p > best_alt_prob:
                        best_alt_prob = p
                        best_alt_action = a
                if p > best_prob:
                    best_prob = p
                    best_action = a

            if best_action is None:
                continue
            if best_action.get('type') == 'stone' and best_action.get('row', 0) == -1:
                penalty_chosen += 1
                if has_row_alt:
                    penalty_when_alt += 1
                    pi = state.get('current_player') if state else None
                    alt_row = best_alt_action.get('row') if best_alt_action else None
                    alt_color = best_alt_action.get('color') if best_alt_action else None
                    doomed_alt = None
                    if state is not None and pi is not None and alt_row is not None:
                        fully_built = _dome_row_fully_built(state, pi, alt_row)
                        has_slot = _dome_row_has_open_matching_slot(state, pi, alt_row, alt_color)
                        if fully_built is not None and has_slot is not None:
                            doomed_alt = fully_built and not has_slot
                    kat2_cases.append({
                        'round': state.get('round') if state else None,
                        'scoring_tile_ids': tuple(sorted(state.get('scoring_tile_ids', []))) if state else None,
                        'color': best_action.get('color'),
                        'penalty_prob': best_prob,
                        'alt_prob': best_alt_prob,
                        'margin': best_prob - best_alt_prob,
                        'doomed_alt': doomed_alt,
                    })
            elif best_action.get('type') == 'stone' and best_action.get('row', -1) >= 0:
                if state is None:
                    missing_state += 1
                    continue
                n_taken = _tiles_taken_from_state(state, best_action)
                remaining = _row_remaining_capacity(state, best_action['row'])
                if remaining is not None and n_taken > remaining:
                    overflow_chosen += 1
                    overflow_tiles_sum += n_taken - remaining

    print(f"{'─'*55}")
    print(f"  Schritte analysiert:             {n_steps:,}")
    if missing_state:
        print(f"  (⚠️ {missing_state} Schritte ohne 'state' -- Überlauf dort nicht prüfbar)")
    print(f"  Strafleisten-Zug angeboten:      {penalty_offered:,}")
    if penalty_offered:
        avg_p = penalty_prob_sum / penalty_offered
        print(f"  Ø Prob wenn angeboten:           {avg_p:.3f}")
    else:
        avg_p = 0.0
    pct_chosen = 100 * penalty_chosen / max(n_steps, 1)
    print(f"  1) Explizit TOP-Wahl:            {penalty_chosen:,} ({pct_chosen:.1f}%)")
    print(f"     davon mit Reihen-Alternative:  {penalty_when_alt:,}  ← Kategorie 2 (verdächtig)")
    pct_overflow = 100 * overflow_chosen / max(n_steps, 1)
    print(f"  3) Überlauf bei Reihen-TOP-Wahl: {overflow_chosen:,} ({pct_overflow:.1f}%)"
          f"  Ø {overflow_tiles_sum/max(overflow_chosen,1):.1f} Steine übergelaufen" if overflow_chosen else
          f"  3) Überlauf bei Reihen-TOP-Wahl: 0")
    print(f"{'─'*55}")

    if kat2_cases:
        print(f"  KATEGORIE-2-AUFSCHLÜSSELUNG ({len(kat2_cases):,} Fälle):")
        n = len(kat2_cases)

        doomed = sum(1 for c in kat2_cases if c['doomed_alt'] is True)
        not_doomed = sum(1 for c in kat2_cases if c['doomed_alt'] is False)
        unknown_doomed = n - doomed - not_doomed
        print(f"    Alternative-Reihe selbst schon aussichtslos: {doomed:,} ({100*doomed/n:.1f}%)")
        print(f"    Alternative-Reihe noch offen (echter Fehlgriff-Verdacht): {not_doomed:,} ({100*not_doomed/n:.1f}%)")
        if unknown_doomed:
            print(f"    (nicht ermittelbar: {unknown_doomed:,})")

        rounds = Counter(c['round'] for c in kat2_cases if c['round'] is not None)
        print(f"    Nach Runde: " + ", ".join(f"R{r}={cnt}" for r, cnt in sorted(rounds.items())))

        colors = Counter(c['color'] for c in kat2_cases)
        print(f"    Nach Farbe: " + ", ".join(f"{c}={cnt}" for c, cnt in colors.most_common()))

        tiles = Counter(c['scoring_tile_ids'] for c in kat2_cases if c['scoring_tile_ids'] is not None)
        print(f"    Top-5 Wertungsplatten-Kombis:")
        for ids, cnt in tiles.most_common(5):
            print(f"      {ids}: {cnt}")

        margins = [c['margin'] for c in kat2_cases]
        confident = sum(1 for m in margins if m > 0.2)
        close = sum(1 for m in margins if abs(m) <= 0.2)
        print(f"    Prob-Marge (Strafleiste - beste Reihen-Alt.): "
              f"deutlich ({'>'}0.2)={confident} ({100*confident/n:.1f}%), knapp={close} ({100*close/n:.1f}%)")
        print(f"{'─'*55}")

    if penalty_offered and avg_p < 0.15 and not overflow_chosen:
        print("  → ✅ HARMLOS: angeboten, aber kaum bevorzugt (niedrige Prob)")
    elif penalty_chosen and penalty_when_alt > penalty_chosen * 0.5:
        print("  → ⚠️ VERDÄCHTIG: Strafleiste oft TROTZ Reihen-Alternative gewählt (Kategorie 2)")
        print("     (möglicher Rest eines Bewertungs-/Perspektiv-Problems)")
    elif overflow_chosen > n_steps * 0.02:
        print("  → 🟠 Nennenswerter Anteil Überlauf-Züge (Kategorie 3) -- Policy nimmt")
        print("     bewusst mehr Steine als eine Reihe fasst (kann bei mehreren")
        print("     gleichzeitig fertigstellbaren Reihen trotzdem korrekt sein).")
    else:
        print("  → 🟡 Strafleiste meist nur wenn keine Alternative (erzwungen, ok)")
    print(f"{'='*55}")


def run_policy_cutoff_exclusion(data_dir: str, label: str, max_files: int = 100):
    """
    Praeziseres, schaerferes Problem als die Kategorie-2-Analyse: der
    POLICY_MASS_CUTOFF (95%) in net_mcts.rs::build_untried_actions kappt den
    Kandidaten-Long-Tail, BEVOR ueberhaupt ein Kindknoten entsteht -- c_puct
    kann nur unter bereits existierenden Kindern gewichten, nicht bei einer
    Aktion, die nie zum Kandidaten wurde. Diese Funktion prueft direkt: wurde
    beim TOP-Strafleisten-Zug eine farbgleiche Reihen-Alternative, die laut
    `valid_actions` (alle legalen Zuege) existierte, ueberhaupt NIRGENDS in
    der durchsuchten `policy` (den ueberlebenden Cutoff-Kandidaten) sichtbar?
    Falls ja: die Suche hatte NIE eine Chance, diese Alternative zu entdecken
    -- unabhaengig von c_puct/Sims.
    """
    files = sorted(glob.glob(os.path.join(data_dir, "*.pkl")))
    if not files:
        print(f"  ❌ Keine .pkl-Dateien in: {data_dir}")
        return
    if len(files) > max_files:
        files = random.sample(files, max_files)

    print(f"\n{'='*55}")
    print(f"  POLICY-CUTOFF-AUSSCHLUSS: {label}")
    print(f"  (Analyse von {len(files)} Datei(en))")
    print(f"{'='*55}")

    n_penalty_top = 0     # Schritte, bei denen Strafleiste die TOP-Policy-Wahl war
    n_excluded = 0         # ... davon: farbgleiche Reihen-Alt. existierte, aber NICHT in policy

    for f in files:
        with open(f, 'rb') as fh:
            data = pickle.load(fh)
        for step in data:
            policy = step.get('policy', [])
            valid_actions = step.get('valid_actions')
            if not policy or valid_actions is None:
                continue

            best_prob, best_action = -1.0, None
            for entry in policy:
                p = entry.get('prob', 0.0)
                if p > best_prob:
                    best_prob, best_action = p, entry.get('action', {})
            if best_action is None:
                continue
            if not (best_action.get('type') == 'stone' and best_action.get('row', 0) == -1):
                continue
            n_penalty_top += 1
            color = best_action.get('color')

            # Farbgleiche Reihen-Alternative laut Regelwerk (nicht nur Suche)?
            has_valid_alt = any(
                a.get('type') == 'stone' and a.get('color') == color and a.get('row', -1) >= 0
                for a in valid_actions
            )
            if not has_valid_alt:
                continue

            # Erscheint SO EINE Alternative irgendwo in der durchsuchten policy?
            in_policy = any(
                entry.get('action', {}).get('type') == 'stone'
                and entry.get('action', {}).get('color') == color
                and entry.get('action', {}).get('row', -1) >= 0
                for entry in policy
            )
            if not in_policy:
                n_excluded += 1

    print(f"{'─'*55}")
    print(f"  Strafleiste als TOP-Policy-Wahl:                {n_penalty_top:,}")
    if n_penalty_top:
        pct = 100 * n_excluded / n_penalty_top
        print(f"  ... davon: farbgleiche Reihen-Alt. existierte,")
        print(f"      erschien aber NIRGENDS in der policy:    {n_excluded:,} ({pct:.1f}%)")
    print(f"{'─'*55}")
    if n_penalty_top and n_excluded / n_penalty_top > 0.15:
        print("  → 🔴 Nennenswerter Anteil: der Cutoff schliesst die Alternative aus,")
        print("     BEVOR die Suche sie je anschauen kann -- c_puct/mehr Sims helfen hier nicht.")
    else:
        print("  → 🟢 Meist wird die Alternative wenigstens als Kandidat betrachtet")
        print("     (auch wenn sie dann evtl. zu wenig Besuche bekommt, siehe Kategorie 2).")
    print(f"{'='*55}")


def run_penalty_score_by_round(data_dir: str, label: str, max_files: int = 100):
    """
    Durchschnittlicher Strafleisten-Punktabzug pro Runde (1-5), gemittelt über
    alle Spiele und beide Spieler. Die Trainingsdaten enthalten den Abzug
    selbst nicht direkt -- ermittelt aus dem MAXIMALEN 'floor'-Füllstand je
    (Spiel, Spieler, Runde) über alle Zustands-Schnappschüsse dieser Runde
    (die Strafleiste wird erst am Rundenende abgerechnet und geleert, der
    Peak innerhalb der Runde ist daher die beste verfügbare Näherung).
    """
    files = sorted(glob.glob(os.path.join(data_dir, "*.pkl")))
    if not files:
        print(f"  ❌ Keine .pkl-Dateien in: {data_dir}")
        return
    if len(files) > max_files:
        files = random.sample(files, max_files)

    BROKEN_PENALTIES = [-1, -2, -3, -4]

    peak = {}  # (game_id, player_idx, round) -> maximaler floor-Füllstand
    for f in files:
        with open(f, 'rb') as fh:
            data = pickle.load(fh)
        for step in data:
            state = step.get('state')
            gid = step.get('game_id')
            if state is None or gid is None:
                continue
            rnd = state.get('round')
            if rnd is None:
                continue
            for pi, player in enumerate(state.get('players', [])):
                key = (gid, pi, rnd)
                n = len(player.get('floor', []))
                if n > peak.get(key, 0):
                    peak[key] = n

    print(f"\n{'='*55}")
    print(f"  STRAFLEISTEN-SCORE PRO RUNDE: {label}")
    print(f"{'='*55}")
    if not peak:
        print("  ❌ Keine auswertbaren Zustände gefunden (fehlt 'state'/'game_id'?).")
        print(f"{'='*55}")
        return

    by_round = {}
    for (_gid, _pi, rnd), n in peak.items():
        n = min(n, len(BROKEN_PENALTIES))
        penalty = sum(BROKEN_PENALTIES[:n])
        by_round.setdefault(rnd, []).append(penalty)

    for rnd in sorted(by_round):
        vals = by_round[rnd]
        avg = sum(vals) / len(vals)
        hit = sum(1 for v in vals if v < 0)
        print(f"  Runde {rnd}: Ø {avg:+.2f} Pkt  (n={len(vals):,}, davon {hit:,} mit Strafe > 0)")
    all_vals = [v for vs in by_round.values() for v in vs]
    print(f"{'─'*55}")
    print(f"  Gesamt (alle Runden): Ø {sum(all_vals)/len(all_vals):+.2f} Pkt  (n={len(all_vals):,})")
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
    Ergebnis-Übersicht der Spiele (0:0-Anteil, Ø Sieger-Score, Ø Margin) +
    Strafleisten-Bias. margin_cap/max_winner_score werden hier NICHT mehr
    kalibriert — die leben nur noch in der Arena (Elo-Skalierung).
    """
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

    print(f"\n{'='*55}")
    print(f"  ERGEBNIS-ÜBERSICHT: {label}")
    print(f"  ({n} Spiele aus {len(files)} Datei(en))")
    print(f"{'─'*55}")
    print(f"  0:0 Spiele:        {zerozero:4d} ({zerozero/n*100:.1f}%)")
    print(f"  Ø Winner-Score:    {_st.mean(winner_scores):.1f}  (Max: {max(winner_scores)})")
    print(f"  Ø Margin:          {_st.mean(margins):.1f}  (Max: {max(margins)})")
    print(f"\n{'='*55}")

    # Strafleisten-Bias + Score-pro-Runde direkt mit ausgeben (gehört
    # thematisch zur Ergebnis-/Entscheidungs-Analyse, daher kein eigener
    # Menüpunkt mehr).
    run_penalty_bias(data_dir, label, max_files=max_files)
    run_penalty_score_by_round(data_dir, label, max_files=max_files)


def main():
    print("\n📋 DIAGNOSIS — Trainingsdaten Analyse")
    print("─" * 55)
    print("  [1] Sanity Check  — alle Daten im data/ Ordner")
    print("  [2] Sanity Check  — Datei(en) auswählen (mehrere möglich)")
    print("  [3] Policy Qualität — alle Daten im data/ Ordner")
    print("  [4] Policy Qualität — Datei(en) auswählen (mehrere möglich)")
    print("  [5] Ergebnis-Übersicht + Strafleisten-Bias — alle Daten")
    print("  [6] Ergebnis-Übersicht + Strafleisten-Bias — Datei(en) auswählen")
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