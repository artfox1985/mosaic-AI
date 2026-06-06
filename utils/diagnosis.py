"""
utils/diagnosis.py — Sanity Check der Trainingsdaten

Prüft:
  - zero-mask rows  → sollte 0 sein
  - policy leak     → sollte < 1e-6 sein
  - p_loss          → sollte ~ln(NUM_ACTIONS) bei untrainiertem Netz sein

Verwendung:
    python -m utils.diagnosis
"""
import sys, torch, os, math
import torch.nn.functional as F
from torch.utils.data import DataLoader
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.neural_net import MosaicDataset, MosaicNet
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
    print("\n📋 DIAGNOSIS — Trainingsdaten Sanity Check")
    print("─" * 55)
    print("  [1] Alle Daten im data/ Ordner prüfen")
    print("  [2] Einzelne Datei auswählen")
    print("─" * 55)

    choice = input("  Auswahl (1/2): ").strip()

    if choice == "1":
        run_diagnosis(str(DATA_DIR), f"data/ ({DATA_DIR})")

    elif choice == "2":
        print("  Öffne Datei-Dialog...")
        path = pick_file()
        if path:
            # Temporäres Verzeichnis mit nur dieser Datei simulieren
            import tempfile, shutil
            with tempfile.TemporaryDirectory() as tmp:
                shutil.copy(path, tmp)
                run_diagnosis(tmp, Path(path).name)
        else:
            print("  ❌ Keine Datei ausgewählt.")
    else:
        print("  ❌ Ungültige Auswahl.")


if __name__ == "__main__":
    main()