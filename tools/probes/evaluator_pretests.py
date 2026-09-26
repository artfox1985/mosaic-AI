# -*- coding: utf-8 -*-
"""tools/probes/evaluator_pretests.py -- Stufe 1 von PREREG_evaluator_pretests.md.

Offline auf dem Champion, ohne Suche und ohne Build:

  E1 (par.3)  -- Wert des Nicht-Ziehers am Blatt: geflippter zweiter Pass (heute,
                 net_mcts.rs:3401-3405) gegen 1 - p_zieher (Einpass-Konsum).
                 Versatz d = p_z + p_f - 1 je Runde, Brier beider Schaetzer gegen
                 den Ausgang des Nicht-Ziehers. Liest den Arm, entscheidet ihn nicht.
  Kontrolle   -- logistischer Leser auf der Value-Kopf-Eingabe des Champions gegen
  (par.4)        denselben Leser auf einem zufaellig initialisierten Netz.
  E2 (par.4)  -- Proportional-Odds-Leser (Margen-Schwellen, gemeinsamer Logit)
                 gegen logistischen Leser auf 1[Sieg].
  E3 (par.4)  -- Rundenleser (je Runde eigene Gewichte) gegen globalen Leser.

Substrat, Schwellen und Leseregeln stehen in der Prereg und werden hier NUR
umgesetzt; wer eine Zahl aendern will, aendert zuerst die Prereg.

Aufruf (nach der v33-Erzeugung, Maschine exklusiv):

    python -u tools/probes/evaluator_pretests.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import time
from pathlib import Path

# Merkmale ueber den Rust-Bauer (dieselbe Wahrheit wie im Spielpfad). MUSS vor
# dem Import von neural_net stehen: der Schalter wird dort beim Import gelesen
# (neural_net.py:115).
os.environ["MOSAIC_FEATURES_FROM_RUST"] = "1"

import numpy as np  # noqa: E402

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "tools"))
sys.path.insert(0, str(BASE_DIR / "engine" / "py"))

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

from runtime_block import laufzeit_block  # noqa: E402

# --- Vorregistrierte Konstanten (PREREG_evaluator_pretests.md) ---------------
FILE_SEED = 20260926          # par.2 Dateiauswahl, par.4 Faltungen, Zufalls-Trunk
BOOT_SEED = 20260927          # par.2 Block-Bootstrap
N_BOOT = 2000                 # par.2
N_PER_CLASS = 20              # par.2: 60 Dateien, je Klasse 20
N_FOLDS = 5                   # par.4
BRIER_GAIN = 0.0012           # par.4: Gewinn EINER Korpus-Verdopplung (task36)
THRESHOLDS = (-10.0, -5.0, 0.0, 5.0, 10.0)   # par.4 E2, Punkte
L2_GRID = (1e-4, 1e-3, 1e-2)  # innere Wahl der L2-Staerke
ROUNDS_DECISIVE = (1, 2, 3, 4)

DEFAULT_MODEL = "models/alphazero_v32-b01_brierbest.pth"
FROZEN_MODEL = "models/frozen_champions/v32-b01/model.pth"
DEFAULT_VAL_LIST = "data/window_v32_val.txt"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def file_class(name: str) -> str:
    """`selfplay_v31-b01-value-tempc_20260922_0953_g120.pkl` -> Klassenpraefix."""
    return re.sub(r"_\d{8}_.*$", "", Path(name).name)


def select_files(val_list: Path) -> list[str]:
    names = [ln.strip() for ln in val_list.read_text(encoding="utf-8").splitlines()
             if ln.strip() and not ln.startswith("#")]
    by_class: dict[str, list[str]] = {}
    for n in names:
        by_class.setdefault(file_class(n), []).append(n)
    rng = random.Random(FILE_SEED)
    chosen = []
    for cls in sorted(by_class):
        pool = sorted(by_class[cls])
        if len(pool) < N_PER_CLASS:
            raise SystemExit(f"Klasse {cls}: nur {len(pool)} Dateien, Prereg verlangt {N_PER_CLASS}")
        chosen.extend(rng.sample(pool, N_PER_CLASS))
    return chosen


# --- Statistik ---------------------------------------------------------------

def block_boot(values: np.ndarray, file_idx: np.ndarray, n_files: int, mask=None) -> dict:
    """Mittel ueber Zustaende mit Block-Bootstrap ueber DATEIEN (par.2)."""
    if mask is not None:
        values, file_idx = values[mask], file_idx[mask]
    if len(values) == 0:
        return {"n": 0, "mean": None, "ci95": None}
    s = np.bincount(file_idx, weights=values, minlength=n_files)
    c = np.bincount(file_idx, minlength=n_files).astype(float)
    rng = np.random.default_rng(BOOT_SEED)
    draws = rng.integers(0, n_files, size=(N_BOOT, n_files))
    cs = c[draws].sum(1)
    ok = cs > 0
    means = s[draws].sum(1)[ok] / cs[ok]
    lo, hi = np.percentile(means, [2.5, 97.5])
    return {"n": int(len(values)), "mean": float(values.mean()), "ci95": [float(lo), float(hi)]}


def standardize(train: np.ndarray, *others: np.ndarray):
    mu = train.mean(0)
    sd = train.std(0) + 1e-6
    return [(train - mu) / sd] + [(o - mu) / sd for o in others]


def fit_logistic(x, y, lam, iters=150):
    import torch
    X = torch.as_tensor(x, dtype=torch.float64)
    Y = torch.as_tensor(y, dtype=torch.float64)
    w = torch.zeros(X.shape[1], dtype=torch.float64, requires_grad=True)
    b = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    opt = torch.optim.LBFGS([w, b], max_iter=iters, line_search_fn="strong_wolfe")
    bce = torch.nn.BCEWithLogitsLoss()

    def closure():
        opt.zero_grad()
        loss = bce(X @ w + b, Y) + lam * (w * w).sum()
        loss.backward()
        return loss
    opt.step(closure)
    wn, bn = w.detach().numpy(), float(b.detach())
    return lambda z: 1.0 / (1.0 + np.exp(-(z @ wn + bn)))


def fit_prop_odds(x, win, margin, rnd, lam, iters=150):
    """Gemeinsamer Logit z = x.w + b; P(Marge > t) = sigma(z - t / s_r), s_r je
    Runde. An der Schwelle 0 ist das Ziel `winner` (Gleichstand per Zusatzregel),
    sonst 1[Marge > t]. Vorhersage fuer den Sieg: sigma(z)."""
    import torch
    X = torch.as_tensor(x, dtype=torch.float64)
    M = torch.as_tensor(margin, dtype=torch.float64)
    W = torch.as_tensor(win, dtype=torch.float64)
    R = torch.as_tensor(np.clip(rnd, 1, 5) - 1, dtype=torch.long)
    w = torch.zeros(X.shape[1], dtype=torch.float64, requires_grad=True)
    b = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    log_s = torch.full((5,), float(np.log(10.0)), dtype=torch.float64, requires_grad=True)
    opt = torch.optim.LBFGS([w, b, log_s], max_iter=iters, line_search_fn="strong_wolfe")
    bce = torch.nn.BCEWithLogitsLoss()

    def closure():
        opt.zero_grad()
        z = X @ w + b
        s = torch.exp(log_s)[R]
        loss = 0.0
        for t in THRESHOLDS:
            target = W if t == 0.0 else (M > t).double()
            loss = loss + bce(z - t / s, target)
        loss = loss / len(THRESHOLDS) + lam * (w * w).sum()
        loss.backward()
        return loss
    opt.step(closure)
    wn, bn = w.detach().numpy(), float(b.detach())
    return lambda z: 1.0 / (1.0 + np.exp(-(z @ wn + bn)))


def brier(p, y):
    return (p - y) ** 2


def pick_lambda(fit_fn, x_tr, y_tr, files_tr, extra_tr=()):
    """Innere Faltung: letztes Viertel der (geseedet gemischten) Trainingsdateien."""
    uniq = sorted(set(files_tr.tolist()))
    random.Random(FILE_SEED).shuffle(uniq)
    inner_val = set(uniq[: max(1, len(uniq) // 4)])
    iv = np.array([f in inner_val for f in files_tr])
    best = None
    for lam in L2_GRID:
        a, bb = standardize(x_tr[~iv], x_tr[iv])
        pred = fit_fn(a, *(e[~iv] for e in (y_tr,) + tuple(extra_tr)), lam)(bb)
        score = brier(pred, y_tr[iv]).mean()
        if best is None or score < best[0]:
            best = (score, lam)
    return best[1]


def oof_predictions(fit_fn, x, y, files, folds, extra=(), subset=None):
    """Out-of-fold-Vorhersagen; `subset` beschraenkt Anpassung UND Vorhersage."""
    pred = np.full(len(y), np.nan)
    idx_all = np.arange(len(y)) if subset is None else np.flatnonzero(subset)
    for k in range(N_FOLDS):
        te = idx_all[folds[files[idx_all]] == k]
        tr = idx_all[folds[files[idx_all]] != k]
        if len(te) == 0 or len(tr) == 0:
            continue
        ex_tr = tuple(e[tr] for e in extra)
        lam = pick_lambda(fit_fn, x[tr], y[tr], files[tr], ex_tr)
        a, bb = standardize(x[tr], x[te])
        pred[te] = fit_fn(a, y[tr], *ex_tr, lam)(bb)
    return pred


# --- Hauptteil ---------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--val-list", default=DEFAULT_VAL_LIST)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    t_start, c_start = time.monotonic(), time.process_time()

    import torch
    import neural_net
    from neural_net import build_model_from_checkpoint, state_to_planes, state_to_tensor
    from corpus_io import load_records
    assert neural_net._FEATURES_FROM_RUST, "Rust-Bauer nicht aktiv (MOSAIC_FEATURES_FROM_RUST)"
    torch.set_num_threads(max(1, (os.cpu_count() or 2) - 1))

    model_path = BASE_DIR / args.model
    frozen = BASE_DIR / FROZEN_MODEL
    model_sha = sha256(model_path)
    if frozen.exists() and sha256(frozen) != model_sha:
        raise SystemExit(f"{args.model} weicht vom eingefrorenen Champion ab (par.2) -- Abbruch.")

    files = select_files(BASE_DIR / args.val_list)
    print(f"[pretests] {len(files)} Dateien aus {args.val_list}, Modell {args.model}", flush=True)

    blob = torch.load(model_path, map_location="cpu", weights_only=False)
    model, encoder = build_model_from_checkpoint(blob)[:2]
    model.eval()
    rand_model, _ = build_model_from_checkpoint(blob)[:2]
    torch.manual_seed(FILE_SEED)
    for m in rand_model.modules():
        if hasattr(m, "reset_parameters"):
            m.reset_parameters()
    rand_model.eval()

    captured: dict[str, list] = {"champ": [], "rand": []}
    model.value_head.register_forward_pre_hook(
        lambda _m, inp: captured["champ"].append(inp[0].detach().numpy().copy()))
    rand_model.value_head.register_forward_pre_hook(
        lambda _m, inp: captured["rand"].append(inp[0].detach().numpy().copy()))

    def forward(net, dicts):
        flat = torch.stack([state_to_tensor(d) for d in dicts])
        if encoder == "2d":
            planes = torch.stack([state_to_planes(d) for d in dicts])
            out = net(planes, flat)
        else:
            out = net(flat)
        return ((out[1][:, 0] + 1.0) / 2.0).numpy()   # value_to_win_prob, net_mcts.rs:2825

    rows = {k: [] for k in ("file", "round", "win", "margin", "known_blocks", "p_z", "p_f")}
    n_mover_mismatch = 0
    buf: list[tuple] = []

    def flush_buf():
        if not buf:
            return
        states = [b[0] for b in buf]
        flipped = []
        for s in states:
            f = dict(s)
            f["current_player"] = 1 - int(s["current_player"])
            flipped.append(f)
        with torch.no_grad():
            pz = forward(model, states)
            n_before = len(captured["champ"])
            pf = forward(model, flipped)
            del captured["champ"][n_before:]      # Trunk nur aus dem normalen Pass
            forward(rand_model, states)
        rows["p_z"].extend(pz.tolist())
        rows["p_f"].extend(pf.tolist())
        for _, fi, rnd, win, margin, kb in buf:
            rows["file"].append(fi)
            rows["round"].append(rnd)
            rows["win"].append(win)
            rows["margin"].append(margin)
            rows["known_blocks"].append(kb)
        buf.clear()

    per_file_n = {}
    for fi, name in enumerate(files):
        path = BASE_DIR / "data" / Path(name).name
        n_file = 0
        for step in load_records(str(path)):
            st = step.get("state") or {}
            if not isinstance(st, dict) or st.get("phase") != "drafting":
                continue
            if step.get("completed", True) is False:
                continue
            if "winner" not in step or "player" not in step:
                continue
            p = int(step["player"])
            if int(st.get("current_player", p)) != p:
                n_mover_mismatch += 1
                continue
            sc = step.get("scores_unclamped", step.get("scores"))
            win = 1.0 if int(step["winner"]) == p else 0.0
            margin = float(sc[p]) - float(sc[1 - p])
            kb = bool((st.get("dome_pool_view") or {}).get("blocks"))
            buf.append((st, fi, int(st.get("round", 0)), win, margin, kb))
            n_file += 1
            if len(buf) >= args.batch:
                flush_buf()
        flush_buf()
        per_file_n[name] = n_file
        print(f"[pretests] {fi + 1}/{len(files)} {Path(name).name}: {n_file} Zustaende, "
              f"gesamt {len(rows['file'])}, {time.monotonic() - t_start:.0f} s", flush=True)

    F = len(files)
    fidx = np.array(rows["file"], dtype=np.int64)
    rnd = np.array(rows["round"], dtype=np.int64)
    win = np.array(rows["win"])
    margin = np.array(rows["margin"])
    kb = np.array(rows["known_blocks"], dtype=bool)
    pz = np.array(rows["p_z"])
    pf = np.array(rows["p_f"])
    trunk = np.concatenate(captured["champ"])
    trunk_rand = np.concatenate(captured["rand"])
    assert len(trunk) == len(win) == len(trunk_rand), (len(trunk), len(win), len(trunk_rand))
    t_extract = time.monotonic() - t_start
    print(f"[pretests] Extraktion fertig: {len(win)} Zustaende in {t_extract:.0f} s", flush=True)

    out: dict = {
        "prereg": "evaluations/PREREG_evaluator_pretests.md",
        "model": args.model, "model_sha256": model_sha,
        "val_list": args.val_list, "files": files, "states_per_file": per_file_n,
        "grundmenge": "Drafting-Zustaende (state.phase == drafting, completed), Einheit Zustand, Block Datei",
        "n_states": int(len(win)), "n_known_blocks": int(kb.sum()),
        "n_mover_mismatch_skipped": n_mover_mismatch,
        "trunk_dim": int(trunk.shape[1]),
    }

    # --- E1 (par.3) -------------------------------------------------------
    d = pz + pf - 1.0
    nonmover_win = 1.0 - win
    diff = brier(1.0 - pz, nonmover_win) - brier(pf, nonmover_win)   # B_e1 - B_flip
    e1 = {}
    for stratum, smask in (("primaer_ohne_bloecke", ~kb), ("mit_bloecken", kb)):
        blk = {}
        for r in list(ROUNDS_DECISIVE) + [5, "alle_1_4"]:
            m = smask & (np.isin(rnd, ROUNDS_DECISIVE) if r == "alle_1_4" else (rnd == r))
            blk[str(r)] = {
                "versatz_d": block_boot(d, fidx, F, m),
                "brier_flip": block_boot(brier(pf, nonmover_win), fidx, F, m),
                "brier_e1": block_boot(brier(1.0 - pz, nonmover_win), fidx, F, m),
                "diff_e1_minus_flip": block_boot(diff, fidx, F, m),
            }
        e1[stratum] = blk
    prim = e1["primaer_ohne_bloecke"]["alle_1_4"]["diff_e1_minus_flip"]
    if prim["ci95"] is None:
        e1_read = "keine Zustaende"
    elif prim["ci95"][1] < 0:
        e1_read = "B_e1 < B_flip: Einpass besser -- Staerke UND Rechenzeit erwartet"
    elif prim["ci95"][0] > 0:
        e1_read = "B_e1 > B_flip: zweiter Pass traegt Information -- Arm ist Stark-gegen-billig-Tausch"
    else:
        e1_read = "gleich gut in dieser Aufloesung -- Kostengewinn ist das Hauptmotiv"
    e1["lesart_par3"] = e1_read
    out["E1"] = e1
    print(f"[E1] primaer Runde 1-4: B_e1 - B_flip = {prim['mean']:+.5f} {prim['ci95']} -> {e1_read}",
          flush=True)

    # --- Leser (par.4) ----------------------------------------------------
    uniq = list(range(F))
    random.Random(FILE_SEED).shuffle(uniq)
    folds = np.empty(F, dtype=np.int64)
    for i, f in enumerate(uniq):
        folds[f] = i % N_FOLDS

    def logit_fit(x, y, lam):
        return fit_logistic(x, y, lam)

    def po_fit(x, y, m, r, lam):
        return fit_prop_odds(x, y, m, r, lam)

    print("[pretests] Leser: Champion-Trunk ...", flush=True)
    p_a = oof_predictions(logit_fit, trunk, win, fidx, folds)
    print("[pretests] Leser: Zufalls-Trunk ...", flush=True)
    p_rand = oof_predictions(logit_fit, trunk_rand, win, fidx, folds)
    print("[pretests] Leser: Proportional-Odds (E2) ...", flush=True)
    p_b = oof_predictions(po_fit, trunk, win, fidx, folds, extra=(margin, rnd))
    print("[pretests] Leser: je Runde (E3) ...", flush=True)
    p_r = np.full(len(win), np.nan)
    for r in range(1, 6):
        sub = rnd == r
        if sub.sum() < 50:
            continue
        pr = oof_predictions(logit_fit, trunk, win, fidx, folds, subset=sub)
        p_r[sub] = pr[sub]

    dec = np.isin(rnd, ROUNDS_DECISIVE)
    ok = ~np.isnan(p_a) & ~np.isnan(p_rand) & ~np.isnan(p_b)

    ctrl = block_boot(brier(p_rand, win) - brier(p_a, win), fidx, F, ok & dec)
    trunk_carries = ctrl["ci95"] is not None and ctrl["ci95"][0] > 0
    out["kontrolle"] = {"brier_rand_minus_champ": ctrl, "trunk_traegt": trunk_carries}

    head_vs_reader = {}
    for r in list(ROUNDS_DECISIVE) + [5]:
        m = ok & (rnd == r)
        head_vs_reader[str(r)] = {
            "brier_kopf": block_boot(brier(pz, win), fidx, F, m),
            "brier_leser": block_boot(brier(p_a, win), fidx, F, m),
            "kopf_minus_leser": block_boot(brier(pz, win) - brier(p_a, win), fidx, F, m),
        }
    out["kopf_gegen_leser_berichtsgroesse"] = head_vs_reader

    e2 = block_boot(brier(p_a, win) - brier(p_b, win), fidx, F, ok & dec)
    e2_pass = (trunk_carries and e2["mean"] is not None and e2["mean"] >= BRIER_GAIN
               and e2["ci95"][0] > 0)
    out["E2"] = {"brier_a_minus_b_runde_1_4": e2, "besteht": e2_pass}

    e3_rounds, n_pass = {}, 0
    for r in list(ROUNDS_DECISIVE) + [5]:
        m = ok & ~np.isnan(p_r) & (rnd == r)
        g = block_boot(brier(p_a, win) - brier(p_r, win), fidx, F, m)
        passed = (r in ROUNDS_DECISIVE and g["mean"] is not None and g["mean"] >= BRIER_GAIN
                  and g["ci95"][0] > 0)
        n_pass += int(passed)
        e3_rounds[str(r)] = {"brier_global_minus_runde": g, "besteht": passed}
    out["E3"] = {"je_runde": e3_rounds, "runden_bestanden_1_4": n_pass,
                 "besteht": trunk_carries and n_pass >= 2}

    print(f"[Kontrolle] Brier Zufall - Champion (R1-4): {ctrl['mean']:+.5f} {ctrl['ci95']} "
          f"-> Trunk traegt: {trunk_carries}", flush=True)
    print(f"[E2] Brier a - b (R1-4): {e2['mean']:+.5f} {e2['ci95']} -> besteht: {e2_pass}", flush=True)
    print(f"[E3] Runden bestanden: {n_pass} -> besteht: {out['E3']['besteht']}", flush=True)

    out["laufzeit"] = laufzeit_block(t_start, cpu_start=c_start, threads=torch.get_num_threads(),
                                     n_units=int(len(win)), unit="zustand")
    out["laufzeit"]["extraktion_s"] = round(t_extract, 1)
    out_path = Path(args.out) if args.out else (
        BASE_DIR / "evaluations" / "artifacts"
        / f"evaluator_pretests_stage1_{Path(args.model).stem.replace('alphazero_', '')}.json")
    if not out_path.is_absolute():
        out_path = BASE_DIR / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Ergebnis: {out_path}  ({out['laufzeit']['wanduhr_s']} s)", flush=True)


if __name__ == "__main__":
    main()
