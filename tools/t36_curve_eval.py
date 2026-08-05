# -*- coding: utf-8 -*-
"""tools/t36_curve_eval.py -- Task #36: externe Brier-Auswertung aller
Saettigungs-Arme auf dem GEMEINSAMEN Messset (die 90 Val-Dateien des
Seed-20260707-Splits, aus allen Trainings-Pools ausgeschlossen).

PREREG_task36_value_saturation.md, Amendment (a): die internen Val-Splits
der Subset-Laeufe sind je Groesse ANDERE Dateien und steuern nur das Early
Stopping -- vergleichbar wird die Kurve erst durch diese externe Messung.

Vorgehen: Zustaende der 90 Dateien EINMAL nach Tensoren vorverarbeiten,
dann alle Checkpoints darueber forwarden. Je Modell: Brier gesamt plus
pro-Partie-Mittel (Bootstrap-Einheit ist die PARTIE, Block-Lektion).
"""
from __future__ import annotations

import glob
import json
import pickle
import random
import sys
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "engine" / "py"))

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

import torch  # noqa: E402

from neural_net import (build_model_from_checkpoint, state_to_planes,  # noqa: E402
                        state_to_tensor)


def val_files() -> list[str]:
    """Exakt der train.py-Split: Seed-20260707-Shuffle, erste 10%."""
    all_files = sorted(glob.glob(str(BASE_DIR / "data" / "*.pkl")))
    sh = all_files[:]
    random.Random(20260707).shuffle(sh)
    n_val = max(1, round(len(sh) * 0.1))
    return sorted(sh[:n_val])


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--models", nargs="+", required=True,
                    help="Versionsnamen (alphazero_<name>.pth in models/)")
    ap.add_argument("--out", default="evaluations/t36_curve_eval.json")
    ap.add_argument("--batch", type=int, default=512)
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    files = val_files()
    print(f"Messset: {len(files)} Val-Dateien | Geraet: {device}")

    # Einmalige Vorverarbeitung (identisch fuer alle Modelle).
    planes_l, flat_l, y_l, gid_l = [], [], [], []
    for f in files:
        for st in pickle.load(open(f, "rb")):
            if st.get("completed") is False or st.get("winner") is None:
                continue
            s = st["state"]
            planes_l.append(state_to_planes(s))
            flat_l.append(state_to_tensor(s))
            y_l.append(1.0 if int(st["winner"]) == int(st["player"]) else 0.0)
            gid_l.append(st["game_id"])
    planes = torch.stack(planes_l)
    flat = torch.stack(flat_l)
    y = torch.tensor(y_l)
    games = sorted(set(gid_l))
    gidx = {g: i for i, g in enumerate(games)}
    print(f"{len(y)} Zustaende aus {len(games)} Partien vorverarbeitet.")

    result = {"n_states": len(y_l), "n_games": len(games), "models": {}}
    for name in args.models:
        ck = torch.load(BASE_DIR / "models" / f"alphazero_{name}.pth",
                        map_location="cpu", weights_only=False)
        model, encoder = build_model_from_checkpoint(ck)[:2]
        model.to(device).eval()
        preds = []
        with torch.no_grad():
            for i in range(0, len(y), args.batch):
                pb = planes[i:i + args.batch].to(device)
                fb = flat[i:i + args.batch].to(device)
                out = model(pb, fb) if encoder == "2d" else model(fb)
                preds.append(((out[1].squeeze(-1) + 1.0) * 0.5).cpu())
        p = torch.cat(preds)
        sq = (p - y) ** 2
        # Pro-Partie-Mittel (Bootstrap-Einheit)
        g_sum = defaultdict(float)
        g_n = defaultdict(int)
        for e, g in zip(sq.tolist(), gid_l):
            g_sum[g] += e
            g_n[g] += 1
        per_game = [g_sum[g] / g_n[g] for g in games]
        brier = float(sq.mean())
        result["models"][name] = {
            "brier": round(brier, 5),
            "per_game_mean": [round(v, 6) for v in per_game],
            "epochs": ck.get("epochs"),
        }
        print(f"{name:26} Brier={brier:.5f}  (Checkpoint-Epoche {ck.get('epochs')})")
        model.to("cpu")

    result["games"] = games
    (BASE_DIR / args.out).write_text(json.dumps(result), encoding="utf-8")
    print(f"\nErgebnis: {args.out}")


if __name__ == "__main__":
    main()
