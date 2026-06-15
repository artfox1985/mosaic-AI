"""
utils/model_info.py — Zeigt Metadaten eines gespeicherten Modells an.

Verwendung:
    python -m utils.model_info --version v1
    python -m utils.model_info --version v2
"""
import argparse
import torch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import MODELS_DIR


LABELS = {
    "timestamp":          "Erstellt am",
    "epochs":             "Epochen (tatsächlich)",
    "epochs_requested":   "Epochen (angefragt)",
    "early_stopped":      "Early Stop",
    "early_stop_epoch":   "Early Stop ab Epoche",
    "num_games":          "Züge",
    "input_size":         "Input Size",
    "hidden_size":        "Hidden Size",
    "num_actions":        "Num Actions",
    "batch_size":         "Batch Size",
    "lr":                 "Learning Rate",
    "value_weight":       "Value Weight",
    "final_policy_loss":  "Policy Loss (final)",
    "policy_pct":         "Policy Loss %",
    "final_value_loss":   "Value Loss (final)",
    "load_version":       "Warm-Start von",
}

QUALITY = [
    (8,  "⚠️  Overfitting-Verdacht"),
    (25, "🟢 Sehr gut"),
    (40, "🟡 Gut"),
    (70, "🟠 Schwaches Signal"),
    (101,"🔴 Nichts gelernt"),
]

def policy_quality(pct):
    for threshold, label in QUALITY:
        if pct < threshold:
            return label
    return "🔴 Nichts gelernt"

def value_quality(v):
    if v > 0.3:   return "🔴 Nichts gelernt"
    if v > 0.1:   return "🟠 Schwaches Signal"
    if v > 0.05:  return "🟡 Gut"
    if v > 0.01:  return "🟢 Sehr gut"
    return "⚠️  Overfitting-Verdacht"


def show_model_info(version: str):
    path = MODELS_DIR / f"alphazero_{version}.pth"

    if not path.exists():
        print(f"❌ Model nicht gefunden: {path}")
        sys.exit(1)

    ckpt = torch.load(str(path), map_location="cpu")

    if "model_state" not in ckpt:
        print(f"⚠️  Model '{version}' enthält keine Metadaten (altes Format).")
        print(f"   Weights vorhanden: {list(ckpt.keys())[:5]} ...")
        sys.exit(0)

    meta = {k: v for k, v in ckpt.items() if k != "model_state"}

    print(f"\n{'='*55}")
    print(f"  MODEL: alphazero_{version}.pth")
    print(f"{'='*55}")

    for key, label in LABELS.items():
        val = meta.get(key)
        if val is None:
            continue

        if key == "policy_pct":
            quality = policy_quality(float(val))
            print(f"  {label:<22} {val:.1f}%  {quality}")
        elif key == "final_policy_loss":
            print(f"  {label:<22} {val:.4f}")
        elif key == "final_value_loss":
            quality = value_quality(float(val))
            print(f"  {label:<22} {val:.4f}  {quality}")
        elif key == "lr":
            print(f"  {label:<22} {val}")
        elif key == "num_games":
            print(f"  {label:<22} {val:,}")
        elif key == "load_version":
            print(f"  {label:<22} {val if val else '—'}")
        else:
            print(f"  {label:<22} {val}")

    print(f"{'='*55}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zeigt Metadaten eines gespeicherten Models")
    parser.add_argument("--version", type=str, required=True, help="Model-Version, z.B. v1")
    args = parser.parse_args()
    show_model_info(args.version)