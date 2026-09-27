# -*- coding: utf-8 -*-
"""tools/probes/e4_supply_demand_pretest.py -- E4-Vortest, PREREG_evaluator_pretests.md par.5c.

Frage: traegt der Trunk des Champions die Angebots-Bedarfs-Groessen schon (dann lohnt kein
Encoder-Abschnitt), oder fehlt die Relation "welche Quelle fuellt welche Musterreihe"?

Groessen je Zustand und EIGENER Musterreihe r (0..5), aus `mosaic_rust.stone_move_outcomes_from_json`
(jeder legale Steinzug auf einem Klon ausgefuehrt, keine nachgebaute Regel):
  max_into_no_overflow[r]  stetig: groesste Steinzahl, die ein Zug OHNE Ueberlauf in die Reihe legt
  fill_exact[r]            binaer: ein Zug fuellt die Reihe genau (voll, kein Ueberlauf)
  min_overflow_fill[r]     stetig, nur wo ein Zug die Reihe fuellt: kleinster Ueberlauf dabei
Lineare Ridge-Probe auf der Value-Kopf-Eingabe (Champion und Zufalls-Trunk), 5-fach ueber Dateien,
Mass EV = 1 - MSE/Var auf den ausgehaltenen Faltungen, Block-Bootstrap ueber Dateien.
Schwelle und Leseregel: Prereg par.5c (nachgetragen 2026-09-27 VOR dem Lauf).

    python -u tools/probes/e4_supply_demand_pretest.py
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

os.environ["MOSAIC_FEATURES_FROM_RUST"] = "1"

import numpy as np  # noqa: E402

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "tools"))
sys.path.insert(0, str(BASE_DIR / "tools" / "probes"))
sys.path.insert(0, str(BASE_DIR / "engine" / "py"))
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

from runtime_block import laufzeit_block  # noqa: E402
from evaluator_pretests import (  # noqa: E402
    BOOT_SEED, DEFAULT_MODEL, DEFAULT_VAL_LIST, FILE_SEED, N_BOOT, N_FOLDS, select_files, sha256,
)

EV_CARRIES = 0.9
RIDGE_GRID = (1.0, 10.0, 100.0, 1000.0)
ROWS = range(6)


def quantities(outcomes: list[dict]) -> dict:
    q = {}
    for r in ROWS:
        mv = [o for o in outcomes if o.get("row") == r]
        no_over = [o["tiles_into_row"] for o in mv if o.get("overflow_to_floor", 0) == 0]
        q[f"max_into_no_overflow_r{r}"] = float(max(no_over) if no_over else 0)
        fills = [o for o in mv if o.get("row_full_after")]
        q[f"fill_exact_r{r}"] = 1.0 if any(o.get("overflow_to_floor", 0) == 0 for o in fills) else 0.0
        q[f"min_overflow_fill_r{r}"] = float(min(o["overflow_to_floor"] for o in fills)) if fills else float("nan")
    return q


def ridge_oof(x, y, fidx, folds):
    pred = np.full(len(y), np.nan)
    for k in range(N_FOLDS):
        te = folds[fidx] == k
        tr = ~te
        if te.sum() == 0 or tr.sum() < 20:
            continue
        # innere Wahl der Staerke: letztes Viertel der Trainingsdateien
        tr_files = sorted(set(fidx[tr].tolist()))
        random.Random(FILE_SEED).shuffle(tr_files)
        inner = np.isin(fidx, tr_files[: max(1, len(tr_files) // 4)]) & tr
        fit = tr & ~inner
        best = None
        for lam in RIDGE_GRID:
            w, b, mu, sd = _ridge_fit(x[fit], y[fit], lam)
            mse = np.mean((((x[inner] - mu) / sd) @ w + b - y[inner]) ** 2)
            if best is None or mse < best[0]:
                best = (mse, lam)
        w, b, mu, sd = _ridge_fit(x[tr], y[tr], best[1])
        pred[te] = ((x[te] - mu) / sd) @ w + b
    return pred


def _ridge_fit(x, y, lam):
    mu, sd = x.mean(0), x.std(0) + 1e-6
    xs = (x - mu) / sd
    b = y.mean()
    a = xs.T @ xs + lam * np.eye(xs.shape[1])
    w = np.linalg.solve(a, xs.T @ (y - b))
    return w, b, mu, sd


def ev_boot(y, pred, fidx, n_files) -> dict:
    m = ~np.isnan(pred) & ~np.isnan(y)
    y, pred, f = y[m], pred[m], fidx[m]
    var = y.var()
    if len(y) < 20 or var <= 0:
        return {"n": int(len(y)), "ev": None, "ci95": None}
    ev = 1.0 - np.mean((pred - y) ** 2) / var
    se = np.bincount(f, weights=(pred - y) ** 2, minlength=n_files)
    s1 = np.bincount(f, weights=y, minlength=n_files)
    s2 = np.bincount(f, weights=y * y, minlength=n_files)
    c = np.bincount(f, minlength=n_files).astype(float)
    rng = np.random.default_rng(BOOT_SEED)
    draws = rng.integers(0, n_files, size=(N_BOOT, n_files))
    n = c[draws].sum(1)
    ok = n > 1
    mean = s1[draws].sum(1)[ok] / n[ok]
    v = s2[draws].sum(1)[ok] / n[ok] - mean ** 2
    evs = 1.0 - (se[draws].sum(1)[ok] / n[ok]) / np.where(v > 0, v, np.nan)
    lo, hi = np.nanpercentile(evs, [2.5, 97.5])
    return {"n": int(len(y)), "ev": float(ev), "ci95": [float(lo), float(hi)]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--val-list", default=DEFAULT_VAL_LIST)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--out", default="evaluations/artifacts/e4_supply_demand_pretest_v32-b01.json")
    args = ap.parse_args()
    t_start, c_start = time.monotonic(), time.process_time()

    import torch
    import mosaic_rust
    import neural_net
    from neural_net import build_model_from_checkpoint, state_to_planes, state_to_tensor
    from corpus_io import load_records
    assert neural_net._FEATURES_FROM_RUST
    torch.set_num_threads(max(1, (os.cpu_count() or 2) - 1))

    model_path = BASE_DIR / args.model
    files = select_files(BASE_DIR / args.val_list)
    blob = torch.load(model_path, map_location="cpu", weights_only=False)
    model, encoder = build_model_from_checkpoint(blob)[:2]
    model.eval()
    rand_model, _ = build_model_from_checkpoint(blob)[:2]
    torch.manual_seed(FILE_SEED)
    for mod in rand_model.modules():
        if hasattr(mod, "reset_parameters"):
            mod.reset_parameters()
    rand_model.eval()
    cap = {"champ": [], "rand": []}
    model.value_head.register_forward_pre_hook(lambda _m, i: cap["champ"].append(i[0].detach().numpy().copy()))
    rand_model.value_head.register_forward_pre_hook(lambda _m, i: cap["rand"].append(i[0].detach().numpy().copy()))

    qrows, fl = [], []
    buf = []
    n_skip = 0

    def flush():
        if not buf:
            return
        with torch.no_grad():
            flat = torch.stack([state_to_tensor(d) for d in buf])
            planes = torch.stack([state_to_planes(d) for d in buf]) if encoder == "2d" else None
            for net in (model, rand_model):
                net(planes, flat) if planes is not None else net(flat)
        buf.clear()

    for fi, name in enumerate(files):
        n_file = 0
        for step in load_records(str(BASE_DIR / "data" / Path(name).name)):
            st = step.get("state") or {}
            if not isinstance(st, dict) or st.get("phase") != "drafting" or step.get("completed", True) is False:
                continue
            va = step.get("valid_actions") or []
            if not any(isinstance(a, dict) and a.get("type") == "stone" for a in va):
                n_skip += 1
                continue
            outcomes = json.loads(mosaic_rust.stone_move_outcomes_from_json(json.dumps(st)))
            if not outcomes:
                n_skip += 1
                continue
            qrows.append(quantities(outcomes))
            fl.append(fi)
            buf.append(st)
            n_file += 1
            if len(buf) >= args.batch:
                flush()
        flush()
        print(f"[e4] {fi + 1}/{len(files)} {Path(name).name}: {n_file} Zustaende, gesamt {len(fl)}, "
              f"{time.monotonic() - t_start:.0f} s", flush=True)

    F = len(files)
    fidx = np.array(fl, dtype=np.int64)
    tc, tr = np.concatenate(cap["champ"]), np.concatenate(cap["rand"])
    assert len(tc) == len(fidx) == len(tr), (len(tc), len(fidx), len(tr))
    uniq = list(range(F))
    random.Random(FILE_SEED).shuffle(uniq)
    folds = np.empty(F, dtype=np.int64)
    for i, f in enumerate(uniq):
        folds[f] = i % N_FOLDS

    results, n_eligible, n_gap = {}, 0, 0
    for key in qrows[0]:
        y = np.array([q[key] for q in qrows])
        m = ~np.isnan(y)
        binary = key.startswith("fill_exact")
        rate = float(y[m].mean()) if m.any() else None
        eligible = (m.sum() >= 200) and ((0.05 <= rate <= 0.95) if binary else (y[m].var() > 0))
        entry = {"n": int(m.sum()), "binaer": binary, "grundrate_oder_mittel": rate, "zulaessig": bool(eligible)}
        if eligible:
            yc = y.copy()
            pc = ridge_oof(tc[m], y[m], fidx[m], folds)
            pr = ridge_oof(tr[m], y[m], fidx[m], folds)
            evc = ev_boot(y[m], pc, fidx[m], F)
            evr = ev_boot(y[m], pr, fidx[m], F)
            gap = (evc["ci95"] is not None and evc["ci95"][1] < EV_CARRIES
                   and evr["ev"] is not None and evc["ev"] > evr["ev"] and evc["ci95"][0] > evr["ci95"][1])
            entry.update({"ev_champion": evc, "ev_zufall": evr, "luecke_belegt": bool(gap),
                          "trunk_traegt": bool(evc["ev"] is not None and evc["ev"] >= EV_CARRIES)})
            n_eligible += 1
            n_gap += int(gap)
            print(f"[e4] {key}: EV Champion {evc['ev']:+.3f} {evc['ci95']} | Zufall {evr['ev']:+.3f} "
                  f"-> {'LUECKE' if gap else ('traegt' if entry['trunk_traegt'] else 'unklar')}", flush=True)
        results[key] = entry

    passed = n_eligible > 0 and n_gap * 2 >= n_eligible
    out = {"prereg": "evaluations/PREREG_evaluator_pretests.md par.5c", "model": args.model,
           "model_sha256": sha256(model_path), "val_list": args.val_list, "files": files,
           "grundmenge": "Drafting-Records mit Steinzug in valid_actions, Einheit Zustand, Block Datei",
           "n_states": int(len(fidx)), "n_skipped": n_skip, "groessen": results,
           "zulaessige_paare": n_eligible, "luecke_belegt": n_gap,
           "verdikt": "BESTEHT" if passed else "TOT"}
    print(f"[e4] zulaessig {n_eligible}, Luecke belegt {n_gap} -> VERDIKT {out['verdikt']}", flush=True)
    out["laufzeit"] = laufzeit_block(t_start, cpu_start=c_start, threads=torch.get_num_threads(),
                                     n_units=int(len(fidx)), unit="zustand")
    op = BASE_DIR / args.out
    op.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Ergebnis: {op} ({out['laufzeit']['wanduhr_s']} s)", flush=True)


if __name__ == "__main__":
    main()
