# -*- coding: utf-8 -*-
"""tools/r4b_zone_probe.py -- Endspiel-Zonen-URSACHENANALYSE (v20-Aera-Task,
Nachfolger des R4b-Befunds "beide Koepfe blind fuer exakte R4-End-Info,
R2~0 bei Decke 0,967").

Frage: WO geht die Information verloren? Drei Hypothesen:
  (a) INPUT traegt sie nicht (Encoding-Luecke),
  (b) TRUNK traegt sie, die Koepfe nutzen sie nicht (Ziel-/Kopf-Problem),
  (c) sie ist ueberhaupt nicht linear zugaenglich.

Methode: dieselben 72 R4-Ende-Zustaende wie R4b (select_states, Seed
20260803, deterministisch; Abgleich der game_ids gegen das R4b-Ergebnis-
JSON), Ground Truth = dessen `true_margin`/`true_winprob` (erwartete
exakte Alpha-Beta-Marge ueber 16 Refills, teuer vorberechnet). Darauf:
  - Probe TRUNK: Ridge-Regression (Leave-One-Out-CV ueber Alphas) von
    `fusion`-Embedding (512d) -> Ground Truth.
  - Probe INPUT: identisch auf den rohen Eingabe-Features
    (Planes geflattet + Flat-Vektor).
  - Baseline KOEPFE: realisierte R2 aus dem R4b-JSON (Modell-Vorhersagen).
Lesart: Probe-TRUNK >> Kopf-R2 -> (b); Probe-INPUT hoch, Probe-TRUNK
niedrig -> Trunk verwirft die Info; beide ~0 -> (a)/(c) (bei n=72 nur
indikativ, Caveat dokumentieren).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "tools"))
sys.path.insert(0, str(BASE_DIR / "engine" / "py"))

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

from r4_value_calibration import select_states  # noqa: E402

R4B_JSON = BASE_DIR / "evaluations" / "artifacts" / "r4b_value_calibration_v20_n72.json"
MODEL_KEY = "models/alphazero_v20_2d_opp_brierbest.pth"


def loo_ridge_r2(x: np.ndarray, y: np.ndarray,
                 alphas=(1.0, 10.0, 100.0, 1000.0, 10000.0)) -> dict:
    """Leave-One-Out-Ridge via Hut-Matrix-Formel (exakt, kein Refit je
    Sample): e_loo_i = (y_i - yhat_i) / (1 - h_ii). Bestes Alpha nach
    LOO-R2. Features werden standardisiert, y zentriert."""
    n = x.shape[0]
    xs = (x - x.mean(0)) / (x.std(0) + 1e-9)
    yc = y - y.mean()
    best = {"alpha": None, "r2": -np.inf}
    for a in alphas:
        # Ridge-Hut-Matrix H = X (X'X + aI)^-1 X'
        g = xs.T @ xs + a * np.eye(xs.shape[1])
        try:
            ginv = np.linalg.inv(g)
        except np.linalg.LinAlgError:
            continue
        h = xs @ ginv @ xs.T
        yhat = h @ yc
        diag = np.clip(np.diag(h), None, 0.999999)
        e_loo = (yc - yhat) / (1.0 - diag)
        r2 = 1.0 - float((e_loo ** 2).sum()) / float((yc ** 2).sum())
        if r2 > best["r2"]:
            best = {"alpha": a, "r2": r2}
    return best


def main() -> None:
    import torch
    from neural_net import (build_model_from_checkpoint, state_to_planes,
                            state_to_tensor)

    ref = json.loads(R4B_JSON.read_text(encoding="utf-8"))
    per_state = ref["per_model"][MODEL_KEY]["per_state"]
    ref_ids = [r["game_id"] for r in per_state]
    summ = ref["summary"]

    chosen, _ = select_states(summ["data_glob"], summ["n_states"],
                              summ["state_seed"])
    got_ids = [c[1] for c in chosen]  # (path, game_id, r4_rec, r5_rec)
    if got_ids != ref_ids:
        raise SystemExit("Zustands-Reproduktion weicht vom R4b-JSON ab -- Abbruch.")
    print(f"{len(chosen)} R4-Ende-Zustaende reproduziert, game_ids identisch zum R4b-Lauf.")

    blob = torch.load(BASE_DIR / MODEL_KEY, map_location="cpu", weights_only=False)
    model, encoder = build_model_from_checkpoint(blob)[:2]
    model.eval()
    assert encoder == "2d"

    captured: list[np.ndarray] = []

    def hook(_mod, inputs):
        captured.append(inputs[0].detach().cpu().numpy()[0])

    model.value_head.register_forward_pre_hook(hook)

    inputs_raw, trunk = [], []
    with torch.no_grad():
        for c in chosen:
            r4_rec = c[2]  # (path, game_id, r4_rec, r5_rec)
            s = r4_rec["state"]
            planes = state_to_planes(s)
            flat = state_to_tensor(s)
            model(planes.unsqueeze(0), flat.unsqueeze(0))
            inputs_raw.append(np.concatenate([planes.numpy().ravel(),
                                              flat.numpy().ravel()]))
    trunk = np.stack(captured)
    inputs_raw = np.stack(inputs_raw)
    y_margin = np.array([r["true_margin"] for r in per_state])
    y_win = np.array([r["true_winprob"] for r in per_state])
    print(f"Trunk-Embedding {trunk.shape}, Input-Features {inputs_raw.shape}")

    heads = ref["per_model"][MODEL_KEY]["model_r2_realized"]
    out = {"n": len(per_state), "heads_realized_r2": heads,
           "r2_max": ref["per_model"][MODEL_KEY]["r2_max"], "probes": {}}
    print("\n=== LOO-Ridge-Proben (R2 gegen Refill-Erwartungs-Ground-Truth) ===")
    for name, x in (("trunk_512", trunk), ("input_raw", inputs_raw)):
        for tgt_name, y in (("true_margin", y_margin), ("true_winprob", y_win)):
            r = loo_ridge_r2(x, y)
            out["probes"][f"{name}->{tgt_name}"] = r
            print(f"{name:10} -> {tgt_name:12}  LOO-R2={r['r2']:+.3f}  (alpha={r['alpha']})")
    print("\nBaseline Koepfe (realisiert, aus R4b-JSON):")
    for k, v in heads.items():
        print(f"  {k}: {v:+.3f}")
    print(f"Decke (R2_max): {out['r2_max']}")

    out_path = BASE_DIR / "evaluations" / "artifacts" / "r4b_zone_probe_v20.json"
    out_path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nErgebnis: {out_path}")


if __name__ == "__main__":
    main()
