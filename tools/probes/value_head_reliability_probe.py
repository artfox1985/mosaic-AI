# -*- coding: utf-8 -*-
"""rho(r) des Value-Kopfs je Runde auf frozen_v3 plus Rauschboden (PREREG_geometric_envelope.md par.8.5, par.12a B1/B2, par.12b Punkte 1 und 2).

Reproduziert `evaluations/artifacts/value_head_reliability_by_round.json` (Bezug v23-b01_brierbest:
rho 0,143 / 0,201 / 0,390 / 0,641 / 0,881), dessen Erzeuger nicht im Baum lag, und ergaenzt:
  * B2: Spearman(Value-Kopf, Orakel-Wurzelwert @5000) je Runde (frozen_v3_oracle_labels.json,
    1.144 Labels, Runde 5 dort ausgenommen),
  * par.12b Punkt 1: Block-Bootstrap ueber die 360 Zustaende je Runde (36 Bloecke a 10 in
    Satz-Reihenfolge, 1.000 Ziehungen): SD des Masses und die 95-Prozent-Spanne der DIFFERENZ
    zweier Ziehungen desselben Netzes (Nullhypothese "gleiches Netz"),
  * par.12b Punkt 2: Spannweite der Groesse ueber die uebergebenen Netze (obere Schranke).

Spearman ohne scipy (Rangkorrelation mit Mittelraengen). Value = Ausgabe 1 des Netzes
(bei WDL-Kopf 2 p_win - 1), Sicht des Spielers am Zug; Marge = scores_unclamped[Spieler] -
scores_unclamped[Gegner]; Sieg = winner == Spieler. Vorwaertslauf auf CUDA, wenn vorhanden.

Aufruf (Minuten; Kodierung der 1.800 Zustaende ist CPU-Arbeit -> nicht neben einer Messung):
    python -X utf8 tools/probes/value_head_reliability_probe.py --models v23-b01_brierbest v24-b05_brierbest \\
        --out evaluations/artifacts/value_head_reliability_par12b.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))

import torch  # noqa: E402
import corpus_io  # noqa: E402
from neural_net import build_model_from_checkpoint, state_to_planes, state_to_tensor  # noqa: E402

FROZEN = REPO / "evaluations" / "frozen_eval_set_v3.pkl"
ORACLE = REPO / "evaluations" / "artifacts" / "frozen_v3_oracle_labels.json"
BLOCK = 10
DRAWS = 1000


def rankdata(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=float)
    sx = x[order]
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sx[j + 1] == sx[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    ra, rb = rankdata(a), rankdata(b)
    return float(np.corrcoef(ra, rb)[0, 1])


def block_bootstrap(a: np.ndarray, b: np.ndarray, rng: np.random.Generator) -> dict:
    n = len(a); nb = n // BLOCK
    idx_blocks = [np.arange(i * BLOCK, (i + 1) * BLOCK) for i in range(nb)]
    vals = []
    for _ in range(DRAWS):
        pick = rng.integers(0, nb, size=nb)
        idx = np.concatenate([idx_blocks[p] for p in pick])
        vals.append(spearman(a[idx], b[idx]))
    vals = np.array(vals)
    diffs = vals[: DRAWS // 2] - vals[DRAWS // 2:]
    return {"sd": round(float(np.nanstd(vals)), 4),
            "differenz_95_spanne": [round(float(np.nanpercentile(diffs, 2.5)), 4), round(float(np.nanpercentile(diffs, 97.5)), 4)]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=20260906)
    a = ap.parse_args()
    t0 = time.time()
    recs = corpus_io.load_records(FROZEN)["records"]
    oracle = {}
    if ORACLE.exists():
        for lbl in json.load(open(ORACLE, encoding="utf-8"))["labels"]:
            oracle[lbl["record_index"]] = lbl["root_value"]
    rounds = np.array([int(r["round"]) for r in recs])
    players = [int(r["player"]) for r in recs]
    margin = np.array([float(r["scores_unclamped"][p] - r["scores_unclamped"][1 - p]) for r, p in zip(recs, players)])
    win = np.array([1.0 if r["winner"] == p else 0.0 for r, p in zip(recs, players)])
    oracle_v = np.array([(v if isinstance(v, (int, float)) else np.nan) for v in (oracle.get(i) for i in range(len(recs)))], dtype=float)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    planes = torch.stack([state_to_planes(r["state"]).float() for r in recs])
    flat_full = torch.stack([state_to_tensor(r["state"]) for r in recs])
    print(f"{len(recs)} Zustaende kodiert ({time.time() - t0:.0f}s), Orakel-Labels {len(oracle)}", flush=True)
    rng = np.random.default_rng(a.seed)
    out = {"prereg": "PREREG_geometric_envelope.md par.8.5 / par.12a B1,B2 / par.12b Punkte 1-2", "frozen": FROZEN.name,
           "n": len(recs), "block": BLOCK, "draws": DRAWS, "nur_spieler_am_zug": True, "modelle": {}}
    for name in a.models:
        ckpt = torch.load(REPO / "models" / f"alphazero_{name}.pth", map_location="cpu", weights_only=False)
        model, encoder = build_model_from_checkpoint(ckpt)
        model.to(device).eval()
        in_size = model.input_size if hasattr(model, "input_size") else ckpt.get("input_size")
        flat = flat_full[:, :in_size]
        vals = []
        with torch.no_grad():
            for i in range(0, len(recs), 256):
                if encoder == "2d":
                    o = model(planes[i:i + 256].to(device), flat[i:i + 256].to(device))
                else:
                    o = model(flat[i:i + 256].to(device))
                vals.append(o[1].float().squeeze(-1).cpu().numpy())
        v = np.concatenate(vals)
        per_round = {}
        for rd in sorted(set(rounds.tolist())):
            m = rounds == rd
            entry = {"n": int(m.sum()), "spearman_value_marge": round(spearman(v[m], margin[m]), 3),
                     "spearman_value_sieg": round(spearman(v[m], win[m]), 3),
                     "bootstrap_marge": block_bootstrap(v[m], margin[m], rng)}
            mo = m & ~np.isnan(oracle_v)
            if mo.sum() >= 30:
                entry["n_orakel"] = int(mo.sum())
                entry["spearman_value_orakel"] = round(spearman(v[mo], oracle_v[mo]), 3)
                entry["bootstrap_orakel"] = block_bootstrap(v[mo], oracle_v[mo], rng)
            per_round[str(rd)] = entry
        out["modelle"][name] = {"encoder": encoder, "input_size": in_size, "je_runde": per_round}
        print(f"== {name}: rho(Marge) " + " / ".join(f"{per_round[k]['spearman_value_marge']:.3f}" for k in sorted(per_round))
              + " | rho(Orakel) " + " / ".join(f"{per_round[k].get('spearman_value_orakel', float('nan')):.3f}" for k in sorted(per_round))
              + " | Bootstrap-SD Marge " + " / ".join(f"{per_round[k]['bootstrap_marge']['sd']:.3f}" for k in sorted(per_round)), flush=True)
    # par.12b Punkt 2: Spannweite ueber Netze je Runde
    spann = {}
    for rd in sorted({k for mdl in out["modelle"].values() for k in mdl["je_runde"]}):
        xs = [mdl["je_runde"][rd]["spearman_value_marge"] for mdl in out["modelle"].values() if rd in mdl["je_runde"]]
        xo = [mdl["je_runde"][rd].get("spearman_value_orakel") for mdl in out["modelle"].values() if mdl["je_runde"].get(rd, {}).get("spearman_value_orakel") is not None]
        spann[rd] = {"marge_min_max": [min(xs), max(xs)], "marge_spannweite": round(max(xs) - min(xs), 3),
                     "orakel_min_max": [min(xo), max(xo)] if xo else None, "orakel_spannweite": round(max(xo) - min(xo), 3) if xo else None}
    out["netz_spannweite"] = spann
    out["laufzeit"] = {"wanduhr_s": round(time.time() - t0, 1), "cpu_s": round(time.process_time(), 1), "threads": 1, "device": device}
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("Netz-Spannweite je Runde (Marge):", {k: v["marge_spannweite"] for k, v in spann.items()})
    print(f"Artefakt: {a.out} ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
