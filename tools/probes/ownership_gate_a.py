# -*- coding: utf-8 -*-
"""Gate A head-quality evaluation for the ownership_weight sweep
(PREREG_ownership_corpus.md par.9 decision rule; metric contract:
PREREG_ownership_consumer.md Gate A).

Measures, per sweep arm (w0/w01/w02/w05, each `alphazero_v21_2d_own_<arm>_best.pth`
plus -- as labelled secondary -- the final-epoch checkpoint):

  1. FIELD level (72 outputs): Brier + AUC per field on held-out END states,
     against a base-rate predictor (constant = per-field fill rate over the
     TRAIN-split ownership-corpus games).
  2. CONJUNCTION level: Brier/AUC per criterion group (columns 6..11,
     diagonals 12..13, corners 14..17, joker 18; rows/colorful/layout as
     context) against the same kind of base rate.
  3. E_k RANK CORRELATION: at a MID-GAME state (last record of round 3) the
     head's expected plate points E_k per conjunctive criterion vs the
     player's ACTUAL end-of-game criterion score
     (mosaic_rust.end_scoring_from_state_json on the final record).
     Spearman + Kendall tau-b per criterion.

Held-out definition (verified, not assumed): train.py:607-612 splits on the
FILE level with a FIXED `random.Random(20260707)` shuffle of the sorted file
list, independent of --seed (which is applied later, train.py:689-691).
All four arms trained on the identical file list (manifest corpus_composition
identical, 3745 files); this script reconstructs the list exactly like
train.py:557-583 (exclude regex -> +extra dir -> sorted) and asserts the
composition against the w0 manifest before using the split.

The "plate-rich held-out games" are the val-split files from
data/ownership_corpus/ (prefixes selfplay_heur_own/selfplay_v21_own_*).

Label truth: engine/py/neural_net.py::_ownership_from_dome (36 per player)
and _conjunctions_from_dome (34 per player, index plan in its docstring).
Head output layout (neural_net.py:1840-1848): [0:36] fields me,
[36:72] fields opp, [72:106] conj me, [106:140] conj opp -- ego perspective
= state["current_player"]. Head outputs are LOGITS (train.py:1154 uses
BCEWithLogits) -> sigmoid here.

Criterion point values (verified against scoring.rs via
tools/conjunction_head_selfcheck.py suite ENGINE): rows +3, columns +7,
diagonals +10, corners +3/+3/+8/+8, joker 2 x wild_total, colorful rows +4.
E_k3 (joker) uses the independence approximation
2 * p(all wild filled) * sum(layout slot probs) -- marked as approximation.

Usage:  python tools/probes/ownership_gate_a.py
Output: evaluations/ownership_gate_a_results.json (+ console tables).
RAM: streams one pkl file at a time; only encoded tensors of the ~800
val-corpus games are held (<100 MB).
"""
import glob
import json
import os
import pickle
import random
import re
import sys
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))

import mosaic_rust  # noqa: E402
from neural_net import (  # noqa: E402
    _conjunctions_from_dome,
    _ownership_from_dome,
    build_model_from_checkpoint,
    state_to_planes,
    state_to_tensor,
)

ARMS = ["w0", "w01", "w02", "w05"]
# Wiederverwendbarkeit fuer spaetere Arme auf DEMSELBEN Held-out (z.B.
# PREREG_frozen_trunk_head.md): --arms/--model-prefix/--out ueberschreiben die
# drei Konstanten, die sonst den Sweep-Armen fest zugeordnet waren. Ohne
# Argumente laeuft das Skript unveraendert wie am 2026-08-15 -- der
# Held-out-Satz bleibt in jedem Fall derselbe, weil `reconstruct_split()` ihn
# aus der Dateiliste + fixem Random(20260707) neu aufbaut und gegen
# W0_MANIFEST prueft.
MODEL_PREFIX = "alphazero_v21_2d_own_"
W0_MANIFEST = REPO / "models" / "manifest_train_v21_2d_own_w0_20260815_015638.json"
OUT_JSON = REPO / "evaluations" / "artifacts" / "ownership_gate_a_results.json"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Conjunction index plan (verified: _conjunctions_from_dome docstring +
# tools/conjunction_head_selfcheck.py). Slices are within the 34-wide block.
CONJ_GROUPS = {
    "rows_k0": (slice(0, 6), 3.0),
    "columns_k1": (slice(6, 12), 7.0),
    "diagonals_k2": (slice(12, 14), 10.0),
    "corners_k5": (slice(14, 18), None),  # weights 3/3/8/8
    "joker_k3": (slice(18, 19), None),    # 2 x wild_total
    "colorful_k7": (slice(19, 25), 4.0),
    "layout_wild": (slice(25, 34), None),  # layout, context only
}
CORNER_WEIGHTS = np.array([3.0, 3.0, 8.0, 8.0])
# end_scoring criterion ids -> E_k names (ids verified in selfcheck suite 3)
SCORE_IDS = {"rows_k0": 0, "columns_k1": 1, "diagonals_k2": 2,
             "joker_k3": 3, "corners_k5": 5, "colorful_k7": 7}
EK_CRITERIA = ["columns_k1", "diagonals_k2", "corners_k5", "joker_k3",
               "rows_k0", "colorful_k7"]


def reconstruct_split():
    """Exact replica of train.py:557-612 (verified line numbers, 2026-08-15)."""
    excl = (REPO / "evaluations" / "v21_exclude_regex.txt").read_text().strip()
    all_files = sorted(glob.glob(str(REPO / "data" / "*.pkl")))
    all_files = [f for f in all_files if not re.search(excl, os.path.basename(f))]
    extra = sorted(glob.glob(str(REPO / "data" / "ownership_corpus" / "*.pkl")))
    all_files = sorted(all_files + extra)

    manifest = json.loads(W0_MANIFEST.read_text(encoding="utf-8"))
    want_total = sum(c["files"] for c in manifest["corpus_composition"])
    if len(all_files) != want_total:
        sys.exit(f"ABBRUCH: rekonstruiere {len(all_files)} Dateien, Manifest sagt {want_total}")
    # prefix counts must match the manifest exactly (same regex as train.py's
    # _corpus_composition would be overkill here; startswith on the known
    # prefixes is equivalent for this fixed corpus)
    for comp in manifest["corpus_composition"]:
        n = sum(1 for f in all_files
                if os.path.basename(f).startswith("selfplay_" + comp["prefix"] + "_2"))
        if n != comp["files"]:
            sys.exit(f"ABBRUCH: Praefix {comp['prefix']}: {n} != {comp['files']} (Manifest)")

    shuffled = all_files[:]
    random.Random(20260707).shuffle(shuffled)
    n_val = max(1, round(len(shuffled) * 0.1))
    val_files = sorted(shuffled[:n_val])
    train_files = sorted(shuffled[n_val:])
    return train_files, val_files


def is_corpus_file(path):
    b = os.path.basename(path)
    return b.startswith("selfplay_heur_own_") or b.startswith("selfplay_v21_own_")


def iter_games(pkl_path):
    """Yields (game_id, last_record, last_round3_record) per game in file."""
    data = pickle.load(open(pkl_path, "rb"))
    last, mid3 = {}, {}
    for step in data:
        gid = step["game_id"]
        last[gid] = step
        if step["state"].get("round") == 3:
            mid3[gid] = step
    for gid, rec in last.items():
        yield gid, rec, mid3.get(gid)


def game_labels(rec):
    players = rec["state"]["players"]
    return (np.array(_ownership_from_dome(players[0]["dome_grid"]), dtype=np.int8),
            np.array(_ownership_from_dome(players[1]["dome_grid"]), dtype=np.int8),
            np.array(_conjunctions_from_dome(players[0]["dome_grid"]), dtype=np.int8),
            np.array(_conjunctions_from_dome(players[1]["dome_grid"]), dtype=np.int8))


def actual_scores(rec):
    """{criterion_name: (score_p0, score_p1)} from the engine's end scoring."""
    raw = mosaic_rust.end_scoring_from_state_json(
        json.dumps(rec["state"]), [0, 1, 2, 3, 5, 7], 0)
    out = json.loads(raw)
    res = {}
    for name, cid in SCORE_IDS.items():
        s = []
        for pi in (0, 1):
            det = next(x for x in out[f"player_{pi}"]["details"] if x["id"] == cid)
            s.append(float(det["score"]))
        res[name] = tuple(s)
    return res


def collect_base_rates(train_files):
    """Per-field / per-conjunction fill rates over the TRAIN-split
    ownership-corpus games, both player boards pooled (the coverage report
    par.8 found p0/p1 nearly symmetric). This is the matched-distribution --
    i.e. STRICTER -- base-rate predictor for the plate-rich held-out set."""
    own_sum = np.zeros(36)
    conj_sum = np.zeros(34)
    n = 0
    for f in train_files:
        if not is_corpus_file(f):
            continue
        for _gid, rec, _mid in iter_games(f):
            if not rec.get("completed"):
                continue
            o0, o1, c0, c1 = game_labels(rec)
            own_sum += o0
            own_sum += o1
            conj_sum += c0
            conj_sum += c1
            n += 2
    return own_sum / n, conj_sum / n, n


def encode_states(states):
    flat = torch.stack([state_to_tensor(s) for s in states]).float()
    planes = torch.stack([state_to_planes(s) for s in states]).float()
    return planes, flat


def predict_ownership(model, planes, flat, batch=256):
    outs = []
    with torch.no_grad():
        for i in range(0, planes.shape[0], batch):
            o = model(planes[i:i + batch].to(DEVICE), flat[i:i + batch].to(DEVICE))
            outs.append(torch.sigmoid(o[4]).cpu().numpy())
    return np.concatenate(outs, axis=0)  # [N,140]


def auc_score(y, p):
    """Mann-Whitney AUC with tie handling (average ranks). None if one class."""
    y = np.asarray(y)
    p = np.asarray(p, dtype=np.float64)
    n_pos = int(y.sum())
    n_neg = len(y) - n_pos
    if n_pos == 0 or n_neg == 0:
        return None
    order = np.argsort(p, kind="mergesort")
    ranks = np.empty(len(p))
    sp = p[order]
    i = 0
    while i < len(sp):
        j = i
        while j + 1 < len(sp) and sp[j + 1] == sp[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return float((ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def _avg_ranks(x):
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x))
    sx = np.asarray(x)[order]
    i = 0
    while i < len(sx):
        j = i
        while j + 1 < len(sx) and sx[j + 1] == sx[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def spearman(a, b):
    ra, rb = _avg_ranks(a), _avg_ranks(b)
    if ra.std() == 0 or rb.std() == 0:
        return None
    return float(np.corrcoef(ra, rb)[0, 1])


def kendall_tau_b(a, b):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if len(a) < 2 or a.std() == 0 or b.std() == 0:
        return None
    da = np.sign(a[:, None] - a[None, :])
    db = np.sign(b[:, None] - b[None, :])
    iu = np.triu_indices(len(a), k=1)
    da, db = da[iu], db[iu]
    conc = float(np.sum((da * db) > 0))
    disc = float(np.sum((da * db) < 0))
    ties_a = float(np.sum((da == 0) & (db != 0)))
    ties_b = float(np.sum((db == 0) & (da != 0)))
    denom = np.sqrt((conc + disc + ties_a) * (conc + disc + ties_b))
    if denom == 0:
        return None
    return (conc - disc) / denom


def brier(y, p):
    return float(np.mean((np.asarray(p, dtype=np.float64) - np.asarray(y)) ** 2))


def group_metrics(labels, preds, base):
    """labels/preds [N, W], base [W] -> dict with brier, base brier, macro-AUC."""
    out = {"brier": brier(labels, preds),
           "brier_base": brier(labels, np.tile(base, (labels.shape[0], 1)))}
    aucs = [auc_score(labels[:, i], preds[:, i]) for i in range(labels.shape[1])]
    defined = [a for a in aucs if a is not None]
    out["auc_macro"] = float(np.mean(defined)) if defined else None
    out["auc_defined_outputs"] = len(defined)
    out["auc_per_output"] = aucs
    return out


def expected_points(conj_p):
    """E_k per criterion from one 34-wide probability block."""
    e = {}
    e["rows_k0"] = 3.0 * float(conj_p[0:6].sum())
    e["columns_k1"] = 7.0 * float(conj_p[6:12].sum())
    e["diagonals_k2"] = 10.0 * float(conj_p[12:14].sum())
    e["corners_k5"] = float((conj_p[14:18] * CORNER_WEIGHTS).sum())
    # independence approximation (documented in the module docstring)
    e["joker_k3"] = 2.0 * float(conj_p[18]) * float(conj_p[25:34].sum())
    e["colorful_k7"] = 4.0 * float(conj_p[19:25].sum())
    return e


def main():
    train_files, val_files = reconstruct_split()
    val_corpus = [f for f in val_files if is_corpus_file(f)]
    print(f"Split rekonstruiert: {len(train_files)} train / {len(val_files)} val "
          f"Dateien; davon Ownership-Korpus im Val: {len(val_corpus)} Dateien")

    print("Basisraten aus dem TRAIN-Split des Ownership-Korpus ...")
    base_own, base_conj, n_base = collect_base_rates(train_files)
    print(f"  {n_base} Spielerbretter")

    # ---- collect held-out games: labels, scores, encoded states -----------
    end_states, mid_states = [], []
    end_cp, mid_cp = [], []          # current_player of the encoded state
    lab_own, lab_conj = [], []       # per game: (p0,p1) label arrays
    scores = []                      # per game: {crit: (s0,s1)}
    n_games = n_incomplete = n_nomid = 0
    for f in val_corpus:
        for _gid, rec, mid in iter_games(f):
            if not rec.get("completed"):
                n_incomplete += 1
                continue
            if mid is None:
                n_nomid += 1
                continue
            o0, o1, c0, c1 = game_labels(rec)
            lab_own.append((o0, o1))
            lab_conj.append((c0, c1))
            scores.append(actual_scores(rec))
            end_states.append(rec["state"])
            end_cp.append(rec["state"].get("current_player", 0))
            mid_states.append(mid["state"])
            mid_cp.append(mid["state"].get("current_player", 0))
            n_games += 1
    print(f"Held-out-Partien: {n_games} vollstaendig "
          f"({n_incomplete} unvollstaendig, {n_nomid} ohne Runde-3-Record)")

    print("Encoding ...")
    end_planes, end_flat = encode_states(end_states)
    mid_planes, mid_flat = encode_states(mid_states)

    results = {
        "n_heldout_games": n_games,
        "n_val_corpus_files": len(val_corpus),
        "n_base_boards": n_base,
        "base_rate_own": base_own.tolist(),
        "base_rate_conj": base_conj.tolist(),
        "device": DEVICE,
        "arms": {},
    }

    for arm in ARMS:
        for tag, fname in (("best", f"{MODEL_PREFIX}{arm}_best.pth"),
                           ("final", f"{MODEL_PREFIX}{arm}.pth")):
            # Fehlende Varianten ueberspringen statt zu sterben -- gilt fuer
            # BEIDE Tags: `_best` fehlt legitim, wenn die letzte Epoche schon
            # die beste war (train.py:1956 schreibt dann keinen separaten
            # Checkpoint). Genau das passiert im Frozen-Trunk-Modus, wo der
            # Ownership-Val-Verlust monoton faellt -- dort IST `<arm>.pth` der
            # ausgewaehlte Stand. Vorher brach die Sonde hier mit
            # FileNotFoundError ab (aufgefallen bei F1, 2026-08-16).
            if not (REPO / "models" / fname).exists():
                print(f"  (kein {fname} -- uebersprungen)")
                continue
            ck = torch.load(REPO / "models" / fname, map_location="cpu",
                            weights_only=False)
            model, _enc = build_model_from_checkpoint(ck)
            model.eval().to(DEVICE)

            p_end = predict_ownership(model, end_planes, end_flat)
            p_mid = predict_ownership(model, mid_planes, mid_flat)

            # ego -> player mapping at the end state
            own_lab_me = np.stack([lab_own[i][end_cp[i]] for i in range(n_games)])
            own_lab_op = np.stack([lab_own[i][1 - end_cp[i]] for i in range(n_games)])
            conj_lab_me = np.stack([lab_conj[i][end_cp[i]] for i in range(n_games)])
            conj_lab_op = np.stack([lab_conj[i][1 - end_cp[i]] for i in range(n_games)])

            r = {"checkpoint": fname, "epochs": ck.get("epochs"),
                 "final_policy_val_loss": ck.get("final_policy_val_loss"),
                 "final_value_val_brier": ck.get("final_value_val_brier")}

            r["field_me"] = group_metrics(own_lab_me, p_end[:, 0:36], base_own)
            r["field_opp"] = group_metrics(own_lab_op, p_end[:, 36:72], base_own)
            r["conj_groups"] = {}
            for gname, (sl, _w) in CONJ_GROUPS.items():
                r["conj_groups"][gname] = {
                    "me": group_metrics(conj_lab_me[:, sl], p_end[:, 72:106][:, sl],
                                        base_conj[sl]),
                    "opp": group_metrics(conj_lab_op[:, sl], p_end[:, 106:140][:, sl],
                                         base_conj[sl]),
                }

            # E_k at the mid-game state: for each game, both players; the
            # prediction for player p comes from the me-half if p was to move
            # at the mid state, else from the opp-half.
            ek = {k: {"pred": [], "true": [], "player": []} for k in EK_CRITERIA}
            for i in range(n_games):
                e_me = expected_points(p_mid[i, 72:106])
                e_op = expected_points(p_mid[i, 106:140])
                cp = mid_cp[i]
                for p, e in ((cp, e_me), (1 - cp, e_op)):
                    for k in EK_CRITERIA:
                        ek[k]["pred"].append(e[k])
                        ek[k]["true"].append(scores[i][k][p])
                        ek[k]["player"].append(p)
            r["ek_rank_corr"] = {}
            for k in EK_CRITERIA:
                pr = np.array(ek[k]["pred"])
                tr = np.array(ek[k]["true"])
                pl = np.array(ek[k]["player"])
                r["ek_rank_corr"][k] = {
                    "n": len(pr),
                    "spearman": spearman(pr, tr),
                    "kendall": kendall_tau_b(pr, tr),
                    "spearman_p0_only": spearman(pr[pl == 0], tr[pl == 0]),
                    "true_mean": float(tr.mean()),
                    "true_sd": float(tr.std()),
                }

            results["arms"].setdefault(arm, {})[tag] = r
            print(f"\n=== {arm}/{tag} (Epoche {r['epochs']}) ===")
            print(f"  Feld-Brier me/opp: {r['field_me']['brier']:.4f}/"
                  f"{r['field_opp']['brier']:.4f}  (Basisrate: "
                  f"{r['field_me']['brier_base']:.4f})")
            print(f"  Feld-AUC(macro) me/opp: "
                  f"{r['field_me']['auc_macro']}/{r['field_opp']['auc_macro']}")
            for gname in ("columns_k1", "diagonals_k2", "corners_k5", "joker_k3"):
                g = r["conj_groups"][gname]
                print(f"  {gname:14s} Brier me {g['me']['brier']:.4f} "
                      f"(Basis {g['me']['brier_base']:.4f}) AUC me "
                      f"{g['me']['auc_macro']}")
            for k in EK_CRITERIA:
                c = r["ek_rank_corr"][k]
                sp = c["spearman"]
                print(f"  E_{k:13s} Spearman {sp if sp is None else round(sp, 3)} "
                      f"Kendall {c['kendall'] if c['kendall'] is None else round(c['kendall'], 3)}")

    OUT_JSON.write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"\nRohzahlen -> {OUT_JSON}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--arms", default=",".join(ARMS),
                    help=f"Kommaliste der Arme (Default: {','.join(ARMS)}). Jeder Arm wird als "
                         f"<prefix><arm>_best.pth (+ <prefix><arm>.pth, falls vorhanden) geladen.")
    ap.add_argument("--model-prefix", default=MODEL_PREFIX,
                    help=f"Dateipraefix in models/ (Default: {MODEL_PREFIX}).")
    ap.add_argument("--out", default=str(OUT_JSON),
                    help=f"Ziel-JSON (Default: {OUT_JSON}). Ein neuer Arm-Satz gehoert in eine "
                         f"EIGENE Datei -- sonst ueberschreibt er die Sweep-Rohzahlen.")
    _a = ap.parse_args()
    ARMS = [s.strip() for s in _a.arms.split(",") if s.strip()]
    MODEL_PREFIX = _a.model_prefix
    OUT_JSON = Path(_a.out)
    main()
