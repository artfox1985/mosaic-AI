"""Task #80: Offline-Redundanzanalyse rtv (round_transition_value) vs.
bootstrap_value auf einem vorhandenen Self-Play-Korpus (default: v10b).

Fragestellung: liefert `round_transition_value` (rtv, teure rekursive
Rundenübergangs-Simulation via `round_transition_deep.rs`) gegenüber dem
billigeren `bootstrap_value` (TD-Bootstrap, kurzer Horizont) noch
eigenständige Information für das Schema-15-Value-Target (siehe
`engine/py/neural_net.py::VALUE_SCHEMA_VERSION`), oder ist rtv redundant
und könnte im Self-Play gestrichen werden (Durchsatz-Kandidat)?

Reine Lesend-Analyse -- verändert `data/` NICHT. Schreibt ein Ergebnis-JSON
nach `evaluations/`.

Aufruf:
    python tools/rtv_redundancy_report.py [--pattern data/selfplay_v10b_*.pkl]
                                           [--out evaluations/rtv_redundancy_v10b.json]
"""
import argparse
import glob
import json
import math
import pickle
import statistics
from pathlib import Path

VALUE_SCALE = 50.0  # engine/py/neural_net.py::VALUE_SCALE
TD_LAMBDA = 0.5      # engine/py/neural_net.py::TD_LAMBDA


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return float("nan")
    return sxy / math.sqrt(sxx * syy)


def spearman(xs, ys):
    def rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        ranks = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg_rank = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                ranks[order[k]] = avg_rank
            i = j + 1
        return ranks
    return pearson(rank(xs), rank(ys))


def percentiles(vals, ps=(5, 25, 50, 75, 95)):
    if not vals:
        return {p: float("nan") for p in ps}
    s = sorted(vals)
    n = len(s)
    out = {}
    for p in ps:
        idx = min(n - 1, max(0, round(p / 100.0 * (n - 1))))
        out[p] = s[idx]
    return out


def summarize(vals):
    if not vals:
        return {"n": 0}
    return {
        "n": len(vals),
        "mean": statistics.fmean(vals),
        "std": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
        "mean_abs": statistics.fmean(abs(v) for v in vals),
        "percentiles": percentiles(vals),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", default="data/selfplay_v10b_*.pkl",
                     help="Glob-Pattern für die zu analysierenden .pkl-Korpusdateien")
    ap.add_argument("--out", default="evaluations/rtv_redundancy_v10b.json")
    args = ap.parse_args()

    files = sorted(glob.glob(args.pattern))
    if not files:
        raise SystemExit(f"Keine Dateien für Pattern {args.pattern!r} gefunden")

    # Dedupe je (game_id, round): rtv/bootstrap_value werden von der Rust-Seite
    # EINMAL je Rundenübergang berechnet und retroaktiv auf ALLE Züge dieser
    # Runde gestempelt (self_play.rs::play_net_self_play_game) -- ohne Dedupe
    # würde derselbe Datenpunkt ~15-20x gezählt (ein Eintrag je Zug der Runde).
    seen = set()
    own_rtv_by_round = {1: [], 2: [], 3: [], 4: []}
    own_bootstrap_by_round = {1: [], 2: [], 3: [], 4: []}
    own_fallback_by_round = {1: [], 2: [], 3: [], 4: []}
    n_games = 0
    n_records_total = 0
    n_records_with_both = 0

    for fpath in files:
        with open(fpath, "rb") as fh:
            game_data = pickle.load(fh)
        game_ids_in_file = set()
        for step in game_data:
            n_records_total += 1
            gid = step.get("game_id")
            game_ids_in_file.add(gid)
            rtv = step.get("round_transition_value")
            bv = step.get("bootstrap_value")
            if rtv is None or bv is None:
                continue
            n_records_with_both += 1
            r = step["state"].get("round")
            if r not in (1, 2, 3, 4):
                continue
            key = (gid, r)
            if key in seen:
                continue
            seen.add(key)

            scores_src = step.get("scores_unclamped", step.get("scores"))
            if scores_src is None:
                continue
            for p in (0, 1):
                own_rtv = float(rtv[p]) * 2.0 - 1.0
                own_bootstrap = float(bv[p]) * 2.0 - 1.0
                own_total = float(scores_src[p])
                opp_total = float(scores_src[1 - p])
                own_fallback = math.tanh((own_total - opp_total) / VALUE_SCALE)
                own_rtv_by_round[r].append(own_rtv)
                own_bootstrap_by_round[r].append(own_bootstrap)
                own_fallback_by_round[r].append(own_fallback)
        n_games += len(game_ids_in_file)

    result = {
        "source_pattern": args.pattern,
        "n_files": len(files),
        "n_games_seen": n_games,
        "n_records_total": n_records_total,
        "n_records_with_both_rtv_and_bootstrap": n_records_with_both,
        "value_scale": VALUE_SCALE,
        "td_lambda": TD_LAMBDA,
        "per_round": {},
        "overall": {},
    }

    all_rtv, all_bv, all_fb = [], [], []
    all_delta_blend, all_delta_raw = [], []

    for r in (1, 2, 3, 4):
        rtv_v = own_rtv_by_round[r]
        bv_v = own_bootstrap_by_round[r]
        fb_v = own_fallback_by_round[r]
        # delta_raw: rtv_val - fallback_val (unblended, direkter rtv-Beitrag
        # gegenüber dem harten Endergebnis-Fallback)
        delta_raw = [a - b for a, b in zip(rtv_v, fb_v)]
        # delta_blend: tatsächlicher Unterschied im TRAINIERTEN Schema-15-Target,
        # wenn der rtv-Override entfiele (bootstrap-Blend bliebe erhalten):
        # val_mit_rtv = TD_LAMBDA*bv + (1-TD_LAMBDA)*rtv
        # val_ohne_rtv = TD_LAMBDA*bv + (1-TD_LAMBDA)*fallback
        # delta = (1-TD_LAMBDA) * (rtv - fallback)
        delta_blend = [(1.0 - TD_LAMBDA) * d for d in delta_raw]

        result["per_round"][str(r)] = {
            "n_pairs": len(rtv_v),
            "pearson_rtv_vs_bootstrap": pearson(rtv_v, bv_v),
            "spearman_rtv_vs_bootstrap": spearman(rtv_v, bv_v),
            "pearson_rtv_vs_fallback_outcome": pearson(rtv_v, fb_v),
            "pearson_bootstrap_vs_fallback_outcome": pearson(bv_v, fb_v),
            "rtv_summary": summarize(rtv_v),
            "bootstrap_summary": summarize(bv_v),
            "fallback_outcome_summary": summarize(fb_v),
            "delta_raw_rtv_minus_fallback": summarize(delta_raw),
            "delta_effective_schema15_target_if_rtv_removed": summarize(delta_blend),
        }
        all_rtv.extend(rtv_v)
        all_bv.extend(bv_v)
        all_fb.extend(fb_v)
        all_delta_raw.extend(delta_raw)
        all_delta_blend.extend(delta_blend)

    result["overall"] = {
        "n_pairs": len(all_rtv),
        "pearson_rtv_vs_bootstrap": pearson(all_rtv, all_bv),
        "spearman_rtv_vs_bootstrap": spearman(all_rtv, all_bv),
        "pearson_rtv_vs_fallback_outcome": pearson(all_rtv, all_fb),
        "pearson_bootstrap_vs_fallback_outcome": pearson(all_bv, all_fb),
        "delta_raw_rtv_minus_fallback": summarize(all_delta_raw),
        "delta_effective_schema15_target_if_rtv_removed": summarize(all_delta_blend),
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)

    print(f"Analysiert: {n_games} Spiele, {n_records_total} Records, "
          f"{n_records_with_both} mit rtv+bootstrap, {len(all_rtv)} dedupliziierte (game,round,player)-Paare.")
    print(f"Gesamt-Korrelation rtv vs bootstrap (Pearson): {result['overall']['pearson_rtv_vs_bootstrap']:.4f}")
    print(f"Gesamt-Korrelation rtv vs bootstrap (Spearman): {result['overall']['spearman_rtv_vs_bootstrap']:.4f}")
    for r in (1, 2, 3, 4):
        pr = result["per_round"][str(r)]
        print(f"  Runde {r}: n={pr['n_pairs']:5d}  pearson(rtv,bootstrap)={pr['pearson_rtv_vs_bootstrap']:.4f}  "
              f"delta_target_mean_abs={pr['delta_effective_schema15_target_if_rtv_removed']['mean_abs']:.4f}")
    print(f"Ergebnis geschrieben nach {out_path}")


if __name__ == "__main__":
    main()
