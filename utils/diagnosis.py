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
import sys, torch, os, math, glob, pickle
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
    pred_p, _ = model(states)
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

    files = files[:max_files]
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


def main():
    print("\n📋 DIAGNOSIS — Trainingsdaten Analyse")
    print("─" * 55)
    print("  [1] Sanity Check  — alle Daten im data/ Ordner")
    print("  [2] Sanity Check  — einzelne Datei auswählen")
    print("  [3] Policy Qualität — alle Daten im data/ Ordner")
    print("  [4] Policy Qualität — einzelne Datei auswählen")
    print("─" * 55)

    choice = input("  Auswahl (1/2/3/4): ").strip()

    if choice == "1":
        run_diagnosis(str(DATA_DIR), f"data/")

    elif choice == "2":
        print("  Öffne Datei-Dialog...")
        path = pick_file()
        if path:
            import tempfile, shutil
            with tempfile.TemporaryDirectory() as tmp:
                shutil.copy(path, tmp)
                run_diagnosis(tmp, Path(path).name)
        else:
            print("  ❌ Keine Datei ausgewählt.")

    elif choice == "3":
        run_policy_quality(str(DATA_DIR), "data/")

    elif choice == "4":
        print("  Öffne Datei-Dialog...")
        path = pick_file()
        if path:
            import tempfile, shutil
            with tempfile.TemporaryDirectory() as tmp:
                shutil.copy(path, tmp)
                run_policy_quality(tmp, Path(path).name, max_files=999)
        else:
            print("  ❌ Keine Datei ausgewählt.")

    else:
        print("  ❌ Ungültige Auswahl.")


if __name__ == "__main__":
    main()