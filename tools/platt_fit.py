# -*- coding: utf-8 -*-
"""tools/platt_fit.py -- Platt-Kalibrierungs-Fit des Value-Kopfs gegen den
tatsaechlichen Spielausgang (Frozen-Set, Runden 1-4).

Ersetzt die bisherigen Wegwerf-Skripte (v19_2d_best: B=1,9269 "full" in
value_calibration_fit.json; t34-Verdikt: B=0,97) durch ein
reproduzierbares Werkzeug. Methode identisch: y ~ sigmoid(A + B*logit(p))
per IRLS (reines Python, kein scipy), p = (value_out+1)/2 aus dem
Torch-Forward (build_model_from_checkpoint, tanh- wie WDL-Kopf liefern
value_out in [-1,1]).

Lesart: B~1 kalibriert, B>1 gestaucht/unterkonfident, B<1 ueberkonfident.
Frozen-Set-Vorbehalt (v12-Aera-Zustaende) gilt weiterhin.
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "tools"))
sys.path.insert(0, str(BASE_DIR / "engine" / "py"))

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

from chance_node_pretest import irls, logit  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--models", nargs="+", required=True,
                    help="Checkpoint-Pfade (models/alphazero_*.pth)")
    ap.add_argument("--eval-set", default="evaluations/frozen_eval_set.pkl")
    ap.add_argument("--rounds", default="1,2,3,4")
    ap.add_argument("--out", default=None,
                    help="optionales Ergebnis-JSON")
    args = ap.parse_args()

    import torch
    from neural_net import (build_model_from_checkpoint, state_to_planes,
                            state_to_tensor)

    rounds = {int(r) for r in args.rounds.split(",")}
    recs = pickle.load(open(BASE_DIR / args.eval_set, "rb"))
    recs = recs["records"] if isinstance(recs, dict) and "records" in recs else recs
    sel = [r for r in recs
           if r.get("completed") and r.get("winner") is not None
           and int(r["state"].get("round", 0)) in rounds]
    print(f"{len(sel)} Records (Runden {sorted(rounds)}) aus {args.eval_set}")

    result = {"n": len(sel), "rounds": sorted(rounds), "models": {}}
    for mp in args.models:
        blob = torch.load(BASE_DIR / mp, map_location="cpu", weights_only=False)
        model, encoder = build_model_from_checkpoint(blob)[:2]
        model.eval()
        xs, ys, briers = [], [], []
        with torch.no_grad():
            for rec in sel:
                s = rec["state"]
                x = state_to_tensor(s).unsqueeze(0)
                out = (model(state_to_planes(s).unsqueeze(0), x)
                       if encoder == "2d" else model(x))
                p = float((out[1].squeeze() + 1.0) * 0.5)
                y = 1.0 if int(rec["winner"]) == int(rec["player"]) else 0.0
                xs.append(logit(p))
                ys.append(y)
                briers.append((p - y) ** 2)
        a, b = irls(xs, ys)
        brier = sum(briers) / len(briers)
        result["models"][mp] = {"A": round(a, 4), "B": round(b, 4),
                                "brier": round(brier, 5)}
        print(f"{Path(mp).name:44} Platt-B={b:.4f}  A={a:+.4f}  Brier={brier:.5f}")

    if args.out:
        (BASE_DIR / args.out).write_text(json.dumps(result, indent=1),
                                         encoding="utf-8")
        print(f"Ergebnis: {args.out}")


if __name__ == "__main__":
    main()
