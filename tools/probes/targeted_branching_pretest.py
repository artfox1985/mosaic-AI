# -*- coding: utf-8 -*-
"""tools/probes/targeted_branching_pretest.py -- Stufe 1 von PREREG_targeted_branching.md (par.3).

Frage: zeigt die Diskrepanz zwischen Value-Kopf und Wurzel-Q (bzw. zwischen Prior und Suche) auf
die Stellungen, an denen der Kopf gegen den Ausgang falsch liegt?

  A  Brier(Kopf) im obersten Dezil der Value-Diskrepanz gegen die untere Haelfte (Block-CI).
  B  im obersten Dezil: Brier(root_q) gegen Brier(Kopf), gepaart je Zustand.
  C  Spearman Value-Diskrepanz gegen Policy-Diskrepanz, Ueberlapp der obersten Dezile, A fuer die
     Policy-Diskrepanz.
  Primaer: rohe Diskrepanz |root_q - v_kopf|; zusaetzlich die bereinigte (Residuum nach linearer
  Anpassung von root_q auf v_kopf je Runde, 5-fach ueber Dateien).

Substrat, Schwellen und Leseregeln stehen in der Prereg (par.2, par.3 samt Praezisierung).

    python -u tools/probes/targeted_branching_pretest.py

Offline-Pruefung par.7a (Doppel-Differenz): mit `--model-new` rechnet das Werkzeug zusaetzlich den
Kopf eines NEUEN Modells auf denselben Zustaenden. KL und Dezile bleiben beim `--model` (Generator
der Daten), damit beide Koepfe auf denselben Zustaenden verglichen werden:

    DiD = [Brier(neu) - Brier(Generator)]_oberstes KL-Dezil - [...]_untere KL-Haelfte

Block-Bootstrap ueber Dateien; die Ziehungen landen im Artefakt. `--combine V34.json V33.json`
rechnet daraus E = DiD(v34) - DiD(v33) mit CI aus paarweise differenzierten Ziehungen (ohne Netz).
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

os.environ["MOSAIC_FEATURES_FROM_RUST"] = "1"   # vor dem Import von neural_net

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
from evaluator_pretests import (  # noqa: E402  (dieselben Konstanten wie Stufe 1 der Bewerter-Vortests)
    BOOT_SEED, FILE_SEED, N_BOOT, N_FOLDS, block_boot, select_files, sha256,
)

GAIN = 0.01                      # par.3: Kopf im obersten Dezil um >= 0,01 Brier schlechter
DEFAULT_MODEL = "models/alphazero_v32-b01_brierbest.pth"
DEFAULT_VAL_LIST = "data/window_v33_val.txt"
ROUNDS = (1, 2, 3, 4)


def policy_kl(logits_row, targ: dict) -> float:
    """KL(Ziel || Prior) in der OFFLINE-Definition (par.3/par.7): Prior = Softmax der Logits,
    eingeschraenkt auf die Aktions-IDs des Ziels, f64, Epsilon 1e-12. Einzige Stelle der Formel;
    auch die KL-Abnahme am Ausflug (`excursion_kl_acceptance.py`) rechnet hierueber."""
    ids = np.array(list(targ.keys()), dtype=np.int64)
    t = np.array(list(targ.values()), dtype=np.float64)
    t = t / t.sum()
    lg = logits_row[ids].astype(np.float64)
    lg = lg - lg.max()
    prior = np.exp(lg) / np.exp(lg).sum()
    return float(np.sum(np.where(t > 0, t * (np.log(np.clip(t, 1e-12, None))
                                             - np.log(np.clip(prior, 1e-12, None))), 0.0)))


def boot_group_diff(values, fidx, n_files, mask_a, mask_b) -> dict:
    """Mittel(values | mask_a) - Mittel(values | mask_b), Block-Bootstrap ueber Dateien."""
    def sums(mask):
        s = np.bincount(fidx[mask], weights=values[mask], minlength=n_files)
        c = np.bincount(fidx[mask], minlength=n_files).astype(float)
        return s, c
    sa, ca = sums(mask_a)
    sb, cb = sums(mask_b)
    point = values[mask_a].mean() - values[mask_b].mean()
    rng = np.random.default_rng(BOOT_SEED)
    draws = rng.integers(0, n_files, size=(N_BOOT, n_files))
    na, nb = ca[draws].sum(1), cb[draws].sum(1)
    ok = (na > 0) & (nb > 0)
    d = sa[draws].sum(1)[ok] / na[ok] - sb[draws].sum(1)[ok] / nb[ok]
    lo, hi = np.percentile(d, [2.5, 97.5])
    return {"n_a": int(mask_a.sum()), "n_b": int(mask_b.sum()), "diff": float(point),
            "ci95": [float(lo), float(hi)]}


def spearman(x, y) -> float:
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    return float(np.corrcoef(rx, ry)[0, 1])


def residual_disc(rq, ph, rnd, fidx, n_files) -> np.ndarray:
    """|root_q - (a_r + b_r * v_kopf)|, a/b je Runde auf den Trainingsfaltungen angepasst."""
    uniq = list(range(n_files))
    random.Random(FILE_SEED).shuffle(uniq)
    folds = np.empty(n_files, dtype=np.int64)
    for i, f in enumerate(uniq):
        folds[f] = i % N_FOLDS
    out = np.full(len(rq), np.nan)
    for k in range(N_FOLDS):
        te = folds[fidx] == k
        for r in ROUNDS:
            tr_m = (~te) & (rnd == r)
            te_m = te & (rnd == r)
            if tr_m.sum() < 10 or te_m.sum() == 0:
                continue
            b, a = np.polyfit(ph[tr_m], rq[tr_m], 1)
            out[te_m] = np.abs(rq[te_m] - (a + b * ph[te_m]))
    return out


def did_boot(delta, fidx, n_files, mask_a, mask_b) -> dict:
    """Wie `boot_group_diff`, gibt zusaetzlich die Bootstrap-Ziehungen zurueck (fuer --combine)."""
    def sums(mask):
        s = np.bincount(fidx[mask], weights=delta[mask], minlength=n_files)
        c = np.bincount(fidx[mask], minlength=n_files).astype(float)
        return s, c
    sa, ca = sums(mask_a)
    sb, cb = sums(mask_b)
    point = float(delta[mask_a].mean() - delta[mask_b].mean())
    rng = np.random.default_rng(BOOT_SEED)
    draws = rng.integers(0, n_files, size=(N_BOOT, n_files))
    na, nb = ca[draws].sum(1), cb[draws].sum(1)
    ok = (na > 0) & (nb > 0)
    d = np.full(N_BOOT, np.nan)
    d[ok] = sa[draws].sum(1)[ok] / na[ok] - sb[draws].sum(1)[ok] / nb[ok]
    lo, hi = np.nanpercentile(d, [2.5, 97.5])
    return {"n_a": int(mask_a.sum()), "n_b": int(mask_b.sum()), "did": point,
            "ci95": [float(lo), float(hi)], "draws": [None if np.isnan(x) else float(x) for x in d]}


def combine(path_new: str, path_ctrl: str) -> None:
    """par.7a: E = DiD(v34) - DiD(v33), CI aus paarweise differenzierten unabhaengigen Ziehungen."""
    a = json.loads(Path(path_new).read_text(encoding="utf-8"))["did"]
    b = json.loads(Path(path_ctrl).read_text(encoding="utf-8"))["did"]
    for key in ("gesamt", "ausflug", "uebrige"):
        da = np.array([np.nan if x is None else x for x in a[key]["draws"]])
        db = np.array([np.nan if x is None else x for x in b[key]["draws"]])
        # Beide Laeufe ziehen mit demselben BOOT_SEED dieselben INDEX-Muster, aber ueber disjunkte
        # Dateimengen; die Werte je Ziehung sind damit unabhaengig, die Differenz je Ziehung ist
        # eine Ziehung von E.
        e = da - db
        lo, hi = np.nanpercentile(e, [2.5, 97.5])
        point = a[key]["did"] - b[key]["did"]
        verdict = ("wirkt (E < 0)" if hi < 0 else "WENIGER gelernt (E > 0)" if lo > 0
                   else "nicht zuordenbar (CI ueberdeckt 0)")
        print(f"[par.7a {key}] DiD neu {a[key]['did']:+.5f}, Kontrolle {b[key]['did']:+.5f} -> "
              f"E {point:+.5f} [{lo:+.5f}; {hi:+.5f}] -> {verdict}", flush=True)


def analyse(disc, name, brier_head, brier_rq, win, fidx, n_files, valid) -> dict:
    d = disc.copy()
    m = valid & ~np.isnan(d)
    q90 = np.quantile(d[m], 0.9)
    q50 = np.quantile(d[m], 0.5)
    top = m & (d >= q90)
    low = m & (d <= q50)
    a = boot_group_diff(brier_head, fidx, n_files, top, low)
    b = block_boot(brier_rq - brier_head, fidx, n_files, top)       # < 0: root_q besser
    a_pass = a["diff"] >= GAIN and a["ci95"][0] > 0
    b_pass = b["ci95"] is not None and b["ci95"][1] < 0
    print(f"[{name}] A: Brier Kopf oberstes Dezil - untere Haelfte = {a['diff']:+.5f} {a['ci95']} "
          f"-> {'besteht' if a_pass else 'nicht'} | B: Brier(root_q) - Brier(Kopf) im Dezil = "
          f"{b['mean']:+.5f} {b['ci95']} -> {'besteht' if b_pass else 'nicht'}", flush=True)
    return {"schwelle_dezil": float(q90), "A": a, "A_besteht": a_pass, "B": b, "B_besteht": b_pass,
            "besteht": a_pass and b_pass}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--val-list", default=DEFAULT_VAL_LIST)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--out", default="evaluations/artifacts/targeted_branching_stage1_v32-b01.json")
    ap.add_argument("--model-new", default=None,
                    help="par.7a: zweiter Kopf (neues Modell); KL und Dezile bleiben beim --model")
    ap.add_argument("--combine", nargs=2, metavar=("NEU_JSON", "KONTROLLE_JSON"), default=None,
                    help="par.7a: E aus zwei --model-new-Artefakten rechnen (kein Netz)")
    args = ap.parse_args()
    if args.combine:
        combine(*args.combine)
        return
    t_start, c_start = time.monotonic(), time.process_time()

    import torch
    import neural_net
    from neural_net import action_to_id, build_model_from_checkpoint, state_to_planes, state_to_tensor
    from corpus_io import load_records
    assert neural_net._FEATURES_FROM_RUST, "Rust-Bauer nicht aktiv"
    torch.set_num_threads(max(1, (os.cpu_count() or 2) - 1))

    model_path = BASE_DIR / args.model
    files = select_files(BASE_DIR / args.val_list)
    print(f"[branching] {len(files)} Dateien aus {args.val_list}, Modell {args.model}", flush=True)
    blob = torch.load(model_path, map_location="cpu", weights_only=False)
    model, encoder = build_model_from_checkpoint(blob)[:2]
    model.eval()
    model_new = encoder_new = None
    if args.model_new:
        blob_new = torch.load(BASE_DIR / args.model_new, map_location="cpu", weights_only=False)
        model_new, encoder_new = build_model_from_checkpoint(blob_new)[:2]
        model_new.eval()

    rows = {k: [] for k in ("file", "round", "win", "root_q", "p_head", "kl", "p_new")}
    buf: list = []
    n_skip_ids = 0

    def flush_buf():
        nonlocal n_skip_ids
        if not buf:
            return
        states = [b[0] for b in buf]
        with torch.no_grad():
            flat = torch.stack([state_to_tensor(d) for d in states])
            if encoder == "2d":
                out = model(torch.stack([state_to_planes(d) for d in states]), flat)
            else:
                out = model(flat)
        logits = out[0].numpy()
        ph = ((out[1][:, 0] + 1.0) / 2.0).numpy()
        pn = None
        if model_new is not None:
            with torch.no_grad():
                if encoder_new == "2d":
                    out_n = model_new(torch.stack([state_to_planes(d) for d in states]), flat)
                else:
                    out_n = model_new(flat)
            pn = ((out_n[1][:, 0] + 1.0) / 2.0).numpy()
        for i, (_st, fi, rnd, win, rq, targ) in enumerate(buf):
            kl = policy_kl(logits[i], targ)
            rows["file"].append(fi); rows["round"].append(rnd); rows["win"].append(win)
            rows["root_q"].append(rq); rows["p_head"].append(float(ph[i])); rows["kl"].append(kl)
            rows["p_new"].append(float(pn[i]) if pn is not None else float("nan"))
        buf.clear()

    for fi, name in enumerate(files):
        n_file = 0
        for step in load_records(str(BASE_DIR / "data" / Path(name).name)):
            st = step.get("state") or {}
            if not isinstance(st, dict) or st.get("phase") != "drafting" or step.get("completed", True) is False:
                continue
            rnd = int(st.get("round", 0))
            if rnd not in ROUNDS or step.get("root_q") is None or "winner" not in step:
                continue
            pol = step.get("policy") or []
            targ: dict[int, float] = {}
            try:
                for pe in pol:
                    aid = action_to_id(pe["action"])
                    targ[aid] = targ.get(aid, 0.0) + float(pe["prob"])
            except Exception:  # noqa: BLE001  (unbekannte Aktionsart -> Zustand auslassen, gezaehlt)
                n_skip_ids += 1
                continue
            if len(targ) < 2 or sum(targ.values()) <= 0:
                continue
            p = int(step["player"])
            buf.append((st, fi, rnd, 1.0 if int(step["winner"]) == p else 0.0, float(step["root_q"]), targ))
            n_file += 1
            if len(buf) >= args.batch:
                flush_buf()
        flush_buf()
        print(f"[branching] {fi + 1}/{len(files)} {Path(name).name}: {n_file} Zustaende, "
              f"gesamt {len(rows['file'])}, {time.monotonic() - t_start:.0f} s", flush=True)

    F = len(files)
    fidx = np.array(rows["file"], dtype=np.int64)
    rnd = np.array(rows["round"], dtype=np.int64)
    win = np.array(rows["win"])
    rq_raw = np.array(rows["root_q"])
    ph = np.array(rows["p_head"])
    kl = np.array(rows["kl"])
    valid = np.ones(len(win), dtype=bool)

    # Sichtpruefung (Praezisierung par.3): aus wessen Sicht steht root_q?
    b_as_is = float(np.mean((rq_raw - win) ** 2))
    b_flipped = float(np.mean(((1.0 - rq_raw) - win) ** 2))
    rq = rq_raw if b_as_is <= b_flipped else 1.0 - rq_raw
    print(f"[branching] Sicht root_q: Brier wie gespeichert {b_as_is:.5f}, gespiegelt {b_flipped:.5f} "
          f"-> {'wie gespeichert' if b_as_is <= b_flipped else 'GESPIEGELT'}", flush=True)

    brier_head = (ph - win) ** 2
    brier_rq = (rq - win) ** 2
    disc_raw = np.abs(rq - ph)
    disc_res = residual_disc(rq, ph, rnd, fidx, F)

    out = {
        "prereg": "evaluations/PREREG_targeted_branching.md", "model": args.model,
        "model_sha256": sha256(model_path), "val_list": args.val_list, "files": files,
        "grundmenge": "Drafting-Records Runde 1-4 mit root_q (completed), Einheit Zustand, Block Datei",
        "n_states": int(len(win)), "n_skipped_unknown_action": n_skip_ids,
        "sicht_root_q": {"brier_wie_gespeichert": b_as_is, "brier_gespiegelt": b_flipped,
                         "gewaehlt": "wie gespeichert" if b_as_is <= b_flipped else "gespiegelt"},
        "brier_gesamt": {"kopf": float(brier_head.mean()), "root_q": float(brier_rq.mean())},
    }
    out["primaer_roh"] = analyse(disc_raw, "roh", brier_head, brier_rq, win, fidx, F, valid)
    out["bereinigt"] = analyse(disc_res, "bereinigt", brier_head, brier_rq, win, fidx, F, valid)
    out["policy_kl"] = analyse(kl, "policy-KL", brier_head, brier_rq, win, fidx, F, valid)

    top_v = disc_raw >= np.quantile(disc_raw, 0.9)
    top_p = kl >= np.quantile(kl, 0.9)
    out["C"] = {"spearman_wert_gegen_kl": spearman(disc_raw, kl),
                "anteil_beide_oberstes_dezil": float((top_v & top_p).mean()),
                "anteil_erwartet_unabhaengig": 0.01}
    out["verteilung_je_runde"] = {
        str(r): {"n": int((rnd == r).sum()), "disc_mittel": float(disc_raw[rnd == r].mean()),
                 "anteil_im_obersten_dezil": float(top_v[rnd == r].mean())} for r in ROUNDS}
    klasse = np.array([Path(files[f]).name.split("_")[1] for f in fidx])
    out["verteilung_je_klasse"] = {
        k: {"n": int((klasse == k).sum()), "anteil_im_obersten_dezil": float(top_v[klasse == k].mean())}
        for k in sorted(set(klasse))}
    out["verdikt_primaer"] = "BESTEHT" if out["primaer_roh"]["besteht"] else "TOT"
    if model_new is not None:
        # par.7a: Doppel-Differenz, Dezile nach der KL des GENERATORS (--model).
        p_new = np.array(rows["p_new"])
        delta = (p_new - win) ** 2 - brier_head
        q90, q50 = np.quantile(kl, 0.9), np.quantile(kl, 0.5)
        top, low = kl >= q90, kl <= q50
        is_exc = np.array(["excursion" in k for k in klasse])
        out["model_new"] = args.model_new
        out["model_new_sha256"] = sha256(BASE_DIR / args.model_new)
        out["did"] = {}
        for key, sel in (("gesamt", np.ones_like(top)), ("ausflug", is_exc), ("uebrige", ~is_exc)):
            r = did_boot(delta, fidx, F, top & sel, low & sel)
            r["brier"] = {g: {"generator": float(brier_head[m].mean()), "neu": float(((p_new - win) ** 2)[m].mean())}
                          for g, m in (("oberstes_dezil", top & sel), ("untere_haelfte", low & sel))}
            out["did"][key] = r
            print(f"[par.7a {key}] DiD {r['did']:+.5f} {r['ci95']} (n {r['n_a']} / {r['n_b']})", flush=True)
    print(f"[C] Spearman Wert/KL {out['C']['spearman_wert_gegen_kl']:+.3f}, beide im obersten Dezil "
          f"{out['C']['anteil_beide_oberstes_dezil']:.3f} (unabhaengig 0,01)", flush=True)
    print(f"[branching] VERDIKT (roh, par.3): {out['verdikt_primaer']}", flush=True)
    out["laufzeit"] = laufzeit_block(t_start, cpu_start=c_start, threads=torch.get_num_threads(),
                                     n_units=int(len(win)), unit="zustand")
    op = BASE_DIR / args.out
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Ergebnis: {op} ({out['laufzeit']['wanduhr_s']} s)", flush=True)


if __name__ == "__main__":
    main()
