#!/usr/bin/env python
"""PREREG_saturating_score_utility.md par.3a: Tor "fast konstant" gegen
"fast kollinear zu wr".

Auf dem festen Messset (`evaluations/frozen_eval_set.pkl`, 1.800 Stellungen,
dasselbe Set wie `tools/oracle_metrics.py`), mit dem Champion-Netz, OHNE
Training und OHNE Arena:

1. Histogramm der rohen Kopf-Ausgabe `points[0]` (Modell-Ausgabeindex 3,
   `neural_net.py::Mosaic2DNet.forward` "Reihenfolge = ONNX-Ausgabe-
   reihenfolge"), je Runde.
2. Spannweite von `pts = value_to_win_prob(points) = (points[0]+1)/2` auf
   der [0,1]-Skala, gegen die im Entwurf angenommenen 0,111.
3. Korrelation von `pts` mit `wr = calibrate_win_prob_with(value_to_win_
   prob(value), cal_a, cal_b)` -- Default `cal_a=0, cal_b=1` (Identitaet,
   `net_mcts.rs:321/327`), also `wr = (value[0]+1)/2` (Modell-Ausgabeindex
   1), auf BLOCK-Ebene (je Korpusdatei, Waechter-Muster wie in den anderen
   Sonden dieser Nacht).
"""
import json
import sys
from pathlib import Path

import numpy as np
import torch

ENGINE_PY = Path(__file__).resolve().parents[2] / "engine" / "py"
sys.path.insert(0, str(ENGINE_PY))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from neural_net import state_to_tensor, state_to_planes, build_model_from_checkpoint  # noqa: E402
from config import INPUT_SIZE, NUM_ACTIONS  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
EVAL = ROOT / "evaluations"
OUT_JSON = EVAL / "saturating_score_utility_gate.json"
FROZEN_PKL = EVAL / "frozen_eval_set.pkl"
MODEL_PTH = ROOT / "models" / "alphazero_v21_2d_brierbest.pth"

CAL_A_DEFAULT = 0.0
CAL_B_DEFAULT = 1.0


def calibrate_win_prob_with(p, a, b):
    """Python-Spiegel von net_mcts.rs::calibrate_win_prob_with -- Logit-
    Shift+Stretch. Bei a=0,b=1 identisch zu p (Paritaet unten geprueft)."""
    p = np.clip(p, 1e-9, 1 - 1e-9)
    logit = np.log(p / (1 - p))
    shifted = a + b * logit
    return 1.0 / (1.0 + np.exp(-shifted))


def value_to_win_prob(x):
    return (x + 1.0) / 2.0


def rebuild_model():
    ckpt = torch.load(str(MODEL_PTH), map_location="cpu")
    model, encoder = build_model_from_checkpoint(ckpt, input_size=INPUT_SIZE, num_actions=NUM_ACTIONS)
    model.eval()
    return model, encoder


def forward_batch(model, encoder, states, batch_size=256):
    all_value, all_points = [], []
    with torch.no_grad():
        for i in range(0, len(states), batch_size):
            chunk = states[i:i + batch_size]
            if encoder == "2d":
                planes = torch.stack([state_to_planes(s) for s in chunk])
                flats = torch.stack([state_to_tensor(s) for s in chunk])
                out = model(planes, flats)
            else:
                flats = torch.stack([state_to_tensor(s) for s in chunk])
                out = model(flats)
            all_value.append(out[1].numpy())
            all_points.append(out[3].numpy())
    return np.concatenate(all_value).reshape(-1), np.concatenate(all_points).reshape(-1)


def block_bootstrap_pearson(pts, wr, block_key, n_boot=500, seed=20260824):
    rng = np.random.default_rng(seed)
    keys = sorted(set(block_key))
    idx_by_key = {k: np.where(np.array(block_key) == k)[0] for k in keys}
    out = []
    for _ in range(n_boot):
        picked = rng.choice(keys, size=len(keys), replace=True)
        idxs = np.concatenate([idx_by_key[k] for k in picked])
        if len(idxs) > 2:
            out.append(float(np.corrcoef(pts[idxs], wr[idxs])[0, 1]))
    out = np.array(out)
    return dict(mean=float(out.mean()), p2_5=float(np.percentile(out, 2.5)),
                p97_5=float(np.percentile(out, 97.5)), n_boot=len(out), n_bloecke=len(keys))


def main():
    assert abs(calibrate_win_prob_with(np.array([0.3, 0.6, 0.9]), 0.0, 1.0) -
              np.array([0.3, 0.6, 0.9])).max() < 1e-9, \
        "Selbsttest calibrate_win_prob_with(p,0,1)==p FEHLGESCHLAGEN"
    print("Selbsttest (calibrate_win_prob_with Identitaet bei a=0,b=1): bestanden.", file=sys.stderr)

    import pickle
    with open(FROZEN_PKL, "rb") as fh:
        blob = pickle.load(fh)
    recs = blob["records"]
    print(f"Messset: {len(recs)} Stellungen ({FROZEN_PKL.name})", file=sys.stderr)

    states = [r["state"] for r in recs]
    rounds = [r.get("round") for r in recs]
    block_key = [r.get("source_file", r.get("game_id", "?")) for r in recs]

    model, encoder = rebuild_model()
    print(f"Forward-Pass Batch ({encoder}-Encoder) ...", file=sys.stderr)
    value_raw, points_raw = forward_batch(model, encoder, states)

    wr = calibrate_win_prob_with(value_to_win_prob(value_raw), CAL_A_DEFAULT, CAL_B_DEFAULT)
    pts = value_to_win_prob(points_raw)

    spanne_gesamt = float(pts.max() - pts.min())
    je_runde = {}
    for rnd in sorted(set(r for r in rounds if r is not None)):
        idx = [i for i, r in enumerate(rounds) if r == rnd]
        p = pts[idx]
        je_runde[str(rnd)] = dict(
            n=len(idx), min=round(float(p.min()), 4), max=round(float(p.max()), 4),
            spanne=round(float(p.max() - p.min()), 4), mean=round(float(p.mean()), 4),
            std=round(float(p.std()), 4),
        )

    r_pearson = float(np.corrcoef(pts, wr)[0, 1])
    boot = block_bootstrap_pearson(pts, wr, block_key)

    if spanne_gesamt < 0.2 and abs(r_pearson) < 0.5:
        lesart = "FAST_KONSTANT -- Re-Zentrierung ist der richtige Hebel, Zuschnitt laeuft wie geplant weiter"
    elif spanne_gesamt >= 0.2 and abs(r_pearson) > 0.8:
        lesart = "FAST_KOLLINEAR -- Punkte-Kopf ist keine unabhaengige Groesse, Nutzer-Entscheid zu sigma-Kopf-Ziel noetig"
    else:
        lesart = "DAZWISCHEN -- beide Anteile relevant, dem Nutzer vorzulegen"

    result = dict(
        n_stellungen=len(recs),
        spanne_pts_gesamt=round(spanne_gesamt, 4),
        spanne_pts_vs_entwurfsannahme_0_111=round(spanne_gesamt - 0.111, 4),
        pearson_r_pts_wr=round(r_pearson, 4),
        pearson_r_block_bootstrap_95ci=boot,
        je_runde=je_runde,
        lesart=lesart,
        meta=dict(
            cal_a=CAL_A_DEFAULT, cal_b=CAL_B_DEFAULT,
            hinweis="wr nutzt die DEFAULT-Kalibrierung (a=0,b=1, Identitaet) "
                   "-- Selbsttest oben bestaetigt das vor der Messung.",
        ),
    )
    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n-> {OUT_JSON}")


if __name__ == "__main__":
    main()
