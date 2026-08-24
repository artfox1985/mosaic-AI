#!/usr/bin/env python
"""PREREG_score_correlation.md, komplett (par.2-par.7).

Prueft, ob eigener und gegnerischer Endpunktestand stark genug korreliert
sind, dass P(Sieg) sich nicht aus den Randverteilungen falten laesst --
die einzige Begruendung fuer einen dritten (Differenz-)Kopf im
Verteilungskopf-Entwurf.

Kein Training, keine Arena, keine Engine-Aenderung -- reine Pickle-
Auswertung. Ein Zahlenpaar (X,Y) = Endstand beider Seiten JE PARTIE
(scores_unclamped, ungeclampt, Waechter 2), fuer den bedingten Teil
(par.4) zusaetzlich die live-gepflegte GECLAMPTE Marge `state.players[i]
.score` am Ende jeder Runde 1-4 (scores_unclamped ist auf allen
Datensaetzen einer Partie auf den FINALEN Wert zurueckgeschrieben,
"Fund 7"-Backfill -- fuer den Zwischenstand also ungeeignet, dafuer
braucht es das live gefuehrte `state`-Feld).
"""
import glob
import json
import math
import pickle
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EVAL = ROOT / "evaluations"
OUT_JSON = EVAL / "score_correlation_probe.json"

ROUNDS = (1, 2, 3, 4)
N_BOOT = 500
RNG = np.random.default_rng(20260824)


def stratified_sample(files, stride):
    groups = defaultdict(list)
    for f in files:
        m = re.search(r"selfplay_([a-zA-Z0-9]+)_", Path(f).name)
        groups[m.group(1) if m else "?"].append(f)
    out = []
    for gen in sorted(groups):
        out.extend(sorted(groups[gen])[::stride])
    return sorted(out)


def collect_games(files):
    """game_id -> dict(X, Y, completed, M={round: clamped_margin}, file)."""
    games = {}
    for f in files:
        with open(f, "rb") as fh:
            recs = pickle.load(fh)
        for r in recs:
            gid = r["game_id"]
            g = games.get(gid)
            if g is None:
                g = dict(X=None, Y=None, completed=None, M={}, file=f,
                         _xset=set(), _yset=set())
                games[gid] = g
            scu = r.get("scores_unclamped")
            if scu is not None:
                g["X"] = scu[0]
                g["Y"] = scu[1]
                g["_xset"].add(scu[0])
                g["_yset"].add(scu[1])
            comp = r.get("completed")
            if comp is not None:
                g["completed"] = comp
            st = r.get("state") or {}
            rnd = st.get("round")
            players = st.get("players")
            if rnd in ROUNDS and isinstance(players, list) and len(players) == 2:
                own = players[0].get("score")
                opp = players[1].get("score")
                if own is not None and opp is not None:
                    g["M"][rnd] = own - opp
    return games


def finalize(games):
    """Filtert auf completed==True mit vorhandenem (X,Y); Backfill-Konsistenz
    pruefen (Waechter/REGEL-0-Geist: Rechenprobe VOR Weitergabe)."""
    bad = 0
    out = {}
    for gid, g in games.items():
        if g["completed"] is not True or g["X"] is None or g["Y"] is None:
            continue
        if len(g["_xset"]) > 1 or len(g["_yset"]) > 1:
            bad += 1
            continue
        out[gid] = g
    return out, bad


def pearson(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    return float(np.corrcoef(x, y)[0, 1])


def spearman(x, y):
    def rank(a):
        order = np.argsort(a, kind="mergesort")
        ranks = np.empty(len(a), dtype=float)
        ranks[order] = np.arange(len(a), dtype=float)
        # Bindungen mitteln
        a_sorted = np.asarray(a)[order]
        i = 0
        while i < len(a_sorted):
            j = i
            while j + 1 < len(a_sorted) and a_sorted[j + 1] == a_sorted[i]:
                j += 1
            if j > i:
                avg = ranks[order[i:j + 1]].mean()
                ranks[order[i:j + 1]] = avg
            i = j + 1
        return ranks
    return pearson(rank(np.asarray(x, dtype=float)), rank(np.asarray(y, dtype=float)))


def fold_pmf(px, py):
    """P(D=d) fuer D=X-Y aus zwei diskreten PMFs (dict wert->prob), exakt."""
    out = defaultdict(float)
    for xv, pxv in px.items():
        for yv, pyv in py.items():
            out[xv - yv] += pxv * pyv
    return dict(out)


def pmf_from_values(values):
    c = Counter(values)
    n = len(values)
    return {k: v / n for k, v in c.items()}


def p_gt_zero(pmf):
    return sum(p for d, p in pmf.items() if d > 0)


def p_ge_zero(pmf):
    return sum(p for d, p in pmf.items() if d >= 0)


def block_bootstrap_pearson(games_by_file, n_boot):
    files = list(games_by_file.keys())
    out = []
    for _ in range(n_boot):
        picked = RNG.choice(files, size=len(files), replace=True)
        xs, ys = [], []
        for f in picked:
            for g in games_by_file[f]:
                xs.append(g["X"])
                ys.append(g["Y"])
        if len(xs) > 2:
            out.append(pearson(xs, ys))
    out = np.array(out)
    return dict(mean=float(out.mean()), p2_5=float(np.percentile(out, 2.5)),
                p97_5=float(np.percentile(out, 97.5)), n_boot=len(out))


def conditional_round_analysis(games):
    per_round = {}
    for rnd in ROUNDS:
        rows = [g for g in games.values() if rnd in g["M"]]
        if len(rows) < 40:
            per_round[rnd] = dict(n=len(rows), buckets=[], mae=None,
                                   note="zu wenige Partien mit Zwischenstand")
            continue
        margins = np.array([g["M"][rnd] for g in rows])
        n_buckets = 10 if len(rows) >= 400 else max(3, len(rows) // 40)
        edges = np.quantile(margins, np.linspace(0, 1, n_buckets + 1))
        edges[0] -= 1
        edges[-1] += 1
        edges = np.unique(edges)
        n_buckets = len(edges) - 1
        bucket_idx = np.digitize(margins, edges[1:-1], right=True)

        buckets = []
        for b in range(n_buckets):
            sel = [rows[i] for i in range(len(rows)) if bucket_idx[i] == b]
            if len(sel) < 15:
                continue
            xs = [g["X"] for g in sel]
            ys = [g["Y"] for g in sel]
            d = [x - y for x, y in zip(xs, ys)]
            p_emp = sum(1 for dv in d if dv > 0) / len(d) + \
                    0.5 * sum(1 for dv in d if dv == 0) / len(d)
            px = pmf_from_values(xs)
            py = pmf_from_values(ys)
            pmf_d = fold_pmf(px, py)
            p_fold = p_gt_zero(pmf_d) + 0.5 * pmf_d.get(0, 0.0)
            buckets.append(dict(
                bucket=b, n=len(sel),
                margin_lo=round(float(edges[b]), 2),
                margin_hi=round(float(edges[b + 1]), 2),
                p_emp=round(p_emp, 4), p_fold=round(p_fold, 4),
                abs_err=round(abs(p_emp - p_fold), 4),
            ))
        window = [bk for bk in buckets if 0.30 <= bk["p_emp"] <= 0.70]
        mae = round(sum(bk["abs_err"] for bk in window) / len(window), 4) if window else None
        per_round[rnd] = dict(n=len(rows), n_buckets_total=len(buckets),
                              n_buckets_in_window=len(window), mae=mae,
                              buckets=buckets)
    maes = [v["mae"] for v in per_round.values() if v["mae"] is not None]
    mae_eng = max(maes) if maes else None
    return per_round, mae_eng


def run_on(files, label):
    games_raw = collect_games(files)
    games, n_bad = finalize(games_raw)
    if len(games) < 20:
        return dict(label=label, n_dateien=len(files), n_partien=len(games),
                    n_inkonsistent_verworfen=n_bad,
                    hinweis="zu wenige abgeschlossene Partien fuer eine Auswertung")

    games_by_file = defaultdict(list)
    for g in games.values():
        games_by_file[g["file"]].append(g)

    X = np.array([g["X"] for g in games.values()], dtype=float)
    Y = np.array([g["Y"] for g in games.values()], dtype=float)
    D = X - Y

    var_x, var_y, var_d = float(np.var(X, ddof=1)), float(np.var(Y, ddof=1)), float(np.var(D, ddof=1))
    cov_direct = float(np.cov(X, Y, ddof=1)[0, 1])
    cov_via_var = (var_x + var_y - var_d) / 2.0
    rechenprobe_ok = abs(cov_direct - cov_via_var) < 1e-6 * max(1.0, abs(cov_direct))

    r_pearson = pearson(X, Y)
    r_spearman = spearman(X, Y)
    boot = block_bootstrap_pearson(games_by_file, N_BOOT)

    px_g = pmf_from_values(X.tolist())
    py_g = pmf_from_values(Y.tolist())
    pmf_d_global = fold_pmf(px_g, py_g)
    p_emp_global = float(np.mean(D > 0) + 0.5 * np.mean(D == 0))
    p_fold_global = p_gt_zero(pmf_d_global) + 0.5 * pmf_d_global.get(0, 0.0)

    per_round, mae_eng = conditional_round_analysis(games)

    if mae_eng is None:
        verdikt = "KEIN_VERDIKT (keine Runde mit Fenster-Buckets)"
    elif mae_eng < 0.02:
        verdikt = "WIDERLEGT (< 0,02) -- Unabhaengigkeitsannahme traegt"
    elif mae_eng < 0.05:
        verdikt = "KENNZAHL (0,02-0,05) -- Groessenordnung der Arena-Aufloesung, kein Bau-Argument"
    else:
        verdikt = "BELEGT (>= 0,05) -- notwendige, keine hinreichende Bedingung fuer einen dritten Kopf"

    return dict(
        label=label,
        n_dateien=len(files),
        n_partien_gesamt_gesehen=len(games_raw),
        n_partien_completed_konsistent=len(games),
        n_inkonsistent_verworfen=n_bad,
        var_x=round(var_x, 3), var_y=round(var_y, 3), var_d=round(var_d, 3),
        cov_direct=round(cov_direct, 4), cov_via_var_formula=round(cov_via_var, 4),
        rechenprobe_kovarianz_stimmt_ueberein=rechenprobe_ok,
        pearson_r=round(r_pearson, 4),
        spearman_rho=round(r_spearman, 4),
        pearson_r_block_bootstrap_95ci=boot,
        p_empirisch_d_gt_0=round(p_emp_global, 4),
        p_gefaltet_d_gt_0=round(p_fold_global, 4),
        abweichung_global=round(abs(p_emp_global - p_fold_global), 4),
        mae_eng=mae_eng,
        verdikt=verdikt,
        je_runde=per_round,
    )


def main():
    stride = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    all_files = sorted(glob.glob(str(ROOT / "data" / "selfplay_*.pkl")))
    net_files = stratified_sample(all_files, stride)
    print(f"Netz-Korpus: {len(all_files)} gesamt, Stichprobe {len(net_files)}",
          file=sys.stderr)
    net_result = run_on(net_files, "netzgeneriert (Stichprobe)")

    heur_files = sorted(glob.glob(str(ROOT / "data" / "holdout" / "selfplay_hold_heur_*.pkl")))
    print(f"Heuristik-Korpus: {len(heur_files)} Dateien", file=sys.stderr)
    heur_result = run_on(heur_files, "heuristik_selfplay_bauer") if heur_files else None

    result = dict(netz=net_result, heuristik=heur_result,
                  meta=dict(fenster_netz=[Path(f).name for f in (net_files[:1] + net_files[-1:])],
                            waechter_2_ungeclampt="scores_unclamped verwendet",
                            waechter_4_politikabhaengig=True))
    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in net_result.items() if k != "je_runde"},
                     indent=2, ensure_ascii=False))
    print("\n--- je Runde (netz) ---")
    for rnd, v in net_result.get("je_runde", {}).items():
        print(rnd, {k: vv for k, vv in v.items() if k != "buckets"})
    if heur_result:
        print("\n--- heuristik (kompakt) ---")
        print({k: v for k, v in heur_result.items() if k not in ("je_runde",)})
    print(f"\n-> {OUT_JSON}")


if __name__ == "__main__":
    main()
