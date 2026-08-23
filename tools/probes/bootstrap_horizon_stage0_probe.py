# -*- coding: utf-8 -*-
"""Stufe 0 (`PREREG_bootstrap_horizon.md`, Abschnitt "Stufe 0", Nutzer-
Freigabe 2026-08-23 "im kleinen testen/debuggen"): reine Label-Diagnose
OHNE Training. Fuer 200-300 Zustaende aus fertigen Partien werden BEIDE
Value-Label-Varianten ueber `mosaic_rust.bootstrap_horizon_stage0_probe_json`
(engine/src/lib.rs) berechnet -- diese ruft intern EXAKT die produktiven
Label-Pfade auf, keine Python-Reimplementation:

- **Bestand** (a): `round_transition_deep::bootstrap_value_after_rounds`
  (Horizont 2, Abschluss per `net_leaf_eval`).
- **Anker** (b): `self_play::sample_round_transition_for_round` (die
  "rtv"-Kette: `continue_through_round{2,3,4}` bis zum Runde-5-Freebie
  `round5::exact_round5_outcome`).

Beide werden gegen das ECHTE Endresultat der jeweiligen Partie verglichen
(Sieger + Punktemarge, aus dem letzten Record der Partie).

Stellungsauswahl: `data/selfplay_v20wdl_*.pkl` (aktuelle WDL-Champion-
Generation, volle Runde-1-5-Abdeckung), stratifiziert nach Runde
(Schwerpunkt R1-R2, mind. die Haelfte) x Spaltenfortschritt (niedrig/hoch,
Schwelle wie `seed_position_curation.py`: PROGRESS>=3 = hoch) x
k1-aktiv (ja/nein). Je Runde EIN repraesentativer Tiling-Zustand pro Partie
(der ERSTE Tiling-Record der Runde -- `resolve_to_pre_chance` loest ab
JEDEM Tiling-Unterschritt deterministisch zum selben Vor-Chance-Zustand
auf, empirisch verifiziert: 10/10 Runde-2-Tiling-Unterschritte derselben
Partie lieferten identische `bootstrap_value`-Werte im Bestandskorpus).

Fortschritt = max(col_fill) UEBER BEIDE SPIELER (Annahme, nicht aus der
Prereg abgeleitet -- markiert), ueber den bestehenden Engine-Aufruf
`plate_completability_json` (keine Python-Nachimplementierung von
col_fill). k1_active = 1 in state["scoring_tile_ids"] (wie
`seed_position_curation.py`).

Korrelation gegen das echte Ergebnis: PRIMAER binaer (hat Spieler i
gewonnen? gepoolt ueber beide Spieler-Perspektiven, n_punkte = n_zustaende
x 2 -- das ist exakt die Zielgroesse, gegen die diese [0,1]-Labels beim
Training verwendet werden). SEKUNDAER (Annahme, zusaetzlich): die
Differenz value[0]-value[1] gegen die echte Punktemarge scores[0]-scores[1]
(kontinuierlich).

    python -X utf8 tools/probes/bootstrap_horizon_stage0_probe.py
"""
from __future__ import annotations

import glob
import json
import pickle
import random
import statistics as stats
import sys
import time
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASIS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASIS / "tools"))
from paired_arena_env_ab import champion_model  # noqa: E402 -- bestehende Champion-Aufloesung wiederverwenden

import mosaic_rust as mr  # noqa: E402

KORPUS_GLOB = str(BASIS / "data" / "selfplay_v20wdl_*.pkl")
OUT = BASIS / "evaluations" / "bootstrap_horizon_stage0_probe.json"

ROUNDS = (1, 2, 3)
PROGRESS_HIGH_THRESHOLD = 3  # wie seed_position_curation.py: PROGRESS=(3,4,5) = "hoch"
ROUND_TARGET = {1: 90, 2: 90, 3: 60}  # R1+R2=180/240=75% >= Haelfte, R3=60=25% "Rest"
SEED = 20260823
FILES_TO_SCAN = 120  # 120 Dateien x 10 Partien = 1200 Partien Kandidatenpool, reicht komfortabel


def col_fill_max(state: dict) -> int:
    """Max Spaltenfortschritt UEBER BEIDE SPIELER -- Engine-Aufruf
    (`plate_completability_json`), keine Python-Nachimplementierung."""
    best = 0
    for pi in (0, 1):
        col_fill = json.loads(mr.plate_completability_json(json.dumps(state), pi))["col_fill"]
        best = max(best, max(col_fill))
    return best


def gather_candidates(files: list[str]) -> dict[tuple, list[dict]]:
    """Je Partie x Runde (1-3) EIN Kandidat -- Pools je Stratum (round,
    progress_bucket, k1_active).

    WICHTIG (Korrektur nach erstem Testlauf, siehe Scout-Bericht): das
    Label-Zustand fuer Runde r ist der ERSTE Tiling-Record der Runde r
    (das ist der Zustand, den `round_before=r` auch wirklich sieht --
    `resolve_to_pre_chance` loest ab JEDEM Tiling-Unterschritt derselben
    Runde zum selben Ergebnis auf, s.o.). Der SPALTENFORTSCHRITT dieses
    Zustands ist aber IMMER der Stand VOR Runde r's eigener Plaettchen-
    Legung (Drafting/Tiling aendern `dome_grid` erst waehrend der Tiling-
    Phase, NICHT waehrend Drafting) -- fuer Runde 1 waere das also IMMER 0
    (Brett leer). Das trifft NICHT, was die Prereg mit "hoher Fortschritt"
    meint (Investition, DIE GERADE IN DIESER RUNDE gemacht wurde). Fix:
    Fortschritt wird stattdessen am ERSTEN Tiling-Record der FOLGERUNDE
    r+1 gemessen -- deren `dome_grid` ist identisch zum Stand am ENDE von
    Runde r's Tiling (Drafting der Folgerunde aendert `dome_grid` noch
    nicht), spiegelt also exakt "wie weit ist Runde r's Legung gekommen"."""
    pools: dict[tuple, list[dict]] = defaultdict(list)
    n_games = 0
    for f in files:
        data = pickle.load(open(f, "rb"))
        per_game: dict[str, list[dict]] = defaultdict(list)
        for r in data:
            per_game[r["game_id"]].append(r)
        for gid, records in per_game.items():
            n_games += 1
            # Letzter Record der Partie = echtes Endresultat (Sieger + Marge).
            # In diesem Schema sind scores/winner je Partie konstant ueber
            # ALLE Records (verifiziert, siehe Scout-Bericht) -- trotzdem wird
            # explizit der LETZTE Record genommen, wie in der Prereg gefordert.
            final = records[-1]
            real_winner = final["winner"]
            real_scores = final["scores"]
            first_tiling_by_round: dict[int, dict] = {}
            for r in records:
                st = r["state"]
                rd = st.get("round")
                if st.get("phase") != "tiling" or rd in first_tiling_by_round:
                    continue
                first_tiling_by_round[rd] = st
            for rd in ROUNDS:
                label_state = first_tiling_by_round.get(rd)
                progress_state = first_tiling_by_round.get(rd + 1)
                if label_state is None or progress_state is None:
                    continue
                progress = col_fill_max(progress_state)
                bucket = "high" if progress >= PROGRESS_HIGH_THRESHOLD else "low"
                k1_active = 1 in label_state["scoring_tile_ids"]
                meta = {
                    "game_id": gid, "source_file": Path(f).name, "round": rd,
                    "progress": progress, "progress_bucket": bucket, "k1_active": k1_active,
                    "real_winner": real_winner, "real_scores": real_scores,
                }
                pools[(rd, bucket, k1_active)].append({"meta": meta, "state": label_state})
    print(f"  {len(files)} Dateien, {n_games} Partien gescannt, "
          f"{sum(len(v) for v in pools.values())} Stratum-Kandidaten gesamt", flush=True)
    return pools


def stratified_sample(pools: dict[tuple, list[dict]], rng: random.Random) -> list[dict]:
    selection: list[dict] = []
    for rd, target in ROUND_TARGET.items():
        cells = [(rd, b, k1) for b in ("low", "high") for k1 in (False, True)]
        quota = target // len(cells)
        remainder_pool: list[dict] = []
        taken_this_round = 0
        for cell in cells:
            pool = pools.get(cell, [])
            rng.shuffle(pool)
            take = pool[:quota]
            selection.extend(take)
            taken_this_round += len(take)
            remainder_pool.extend(pool[quota:])
        # Fehlmenge (Zellen mit zu wenig Kandidaten) aus dem Rest derselben
        # Runde auffuellen, damit ROUND_TARGET moeglichst erreicht wird.
        missing = target - taken_this_round
        if missing > 0 and remainder_pool:
            rng.shuffle(remainder_pool)
            selection.extend(remainder_pool[:missing])
    return selection


def run_probes(selection: list[dict], model: str) -> list[dict]:
    results = []
    t_start = time.time()
    for i, item in enumerate(selection):
        meta, state = item["meta"], item["state"]
        seed = SEED * 1000 + i
        t0 = time.time()
        try:
            out = json.loads(mr.bootstrap_horizon_stage0_probe_json(json.dumps(state), model, seed))
        except Exception as e:
            print(f"  [{i+1}/{len(selection)}] FEHLER ({meta['game_id']} r{meta['round']}): {e}", flush=True)
            continue
        dt = time.time() - t0
        results.append({**meta, "seed": seed, **out})
        if (i + 1) % 20 == 0 or i == 0:
            elapsed = time.time() - t_start
            eta = elapsed / (i + 1) * (len(selection) - i - 1)
            print(f"  [{i+1}/{len(selection)}] r{meta['round']} prog={meta['progress']} "
                  f"k1={meta['k1_active']} dt={dt:.2f}s | verstrichen {elapsed:.0f}s, ETA {eta:.0f}s", flush=True)
    return results


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = stats.mean(xs), stats.mean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = (sum((x - mx) ** 2 for x in xs)) ** 0.5
    sy = (sum((y - my) ** 2 for y in ys)) ** 0.5
    if sx < 1e-12 or sy < 1e-12:
        return 0.0
    return cov / (sx * sy)


def spearman(xs: list[float], ys: list[float]) -> float:
    def rank(vals: list[float]) -> list[float]:
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


def correlation_block(pairs: list[tuple[float, float]]) -> dict:
    if len(pairs) < 2:
        return {"n": len(pairs), "pearson": None, "spearman": None}
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    return {"n": len(pairs), "pearson": pearson(xs, ys), "spearman": spearman(xs, ys)}


def build_datapoints(results: list[dict]) -> list[dict]:
    """Pro Zustand x Spieler EIN Datenpunkt (Label vs. binaerer Sieg) --
    genau die Groesse, gegen die diese [0,1]-Labels beim Training laufen."""
    pts = []
    for r in results:
        for pi in (0, 1):
            pts.append({
                "round": r["round"], "progress_bucket": r["progress_bucket"],
                "k1_active": r["k1_active"], "player": pi,
                "bootstrap": r["bootstrap_value"][pi], "anchor": r["anchor_value"][pi],
                "won": 1.0 if r["real_winner"] == pi else 0.0,
            })
    return pts


def is_critical(p: dict) -> bool:
    return p["round"] in (1, 2) and p["progress_bucket"] == "high"


def main() -> None:
    rng = random.Random(SEED)
    model = champion_model()
    print(f"Modell: {Path(model).name}")

    files = sorted(glob.glob(KORPUS_GLOB))
    rng.shuffle(files)
    files = files[:FILES_TO_SCAN]
    print(f"Kandidaten-Scan: {len(files)} von {len(sorted(glob.glob(KORPUS_GLOB)))} v20wdl-Dateien", flush=True)

    pools = gather_candidates(files)
    pool_sizes = {f"r{rd}_{b}_k1={k1}": len(v) for (rd, b, k1), v in sorted(pools.items())}
    print("Pool-Groessen je Zelle:", json.dumps(pool_sizes, indent=1))

    selection = stratified_sample(pools, rng)
    rng.shuffle(selection)
    print(f"Stichprobe: {len(selection)} Zustaende (Ziel je Runde: {ROUND_TARGET})", flush=True)

    print("Starte Label-Berechnung (beide Varianten je Zustand, sequentiell) ...", flush=True)
    results = run_probes(selection, model)
    print(f"Fertig: {len(results)}/{len(selection)} erfolgreich gelabelt", flush=True)

    datapoints = build_datapoints(results)

    # (i) Divergenz-Landkarte Runde x Fortschritt (|a-b| je Spieler-Datenpunkt).
    divergence_map: dict[str, dict] = {}
    for rd in ROUNDS:
        for bucket in ("low", "high"):
            cell = [p for p in datapoints if p["round"] == rd and p["progress_bucket"] == bucket]
            diffs = [abs(p["bootstrap"] - p["anchor"]) for p in cell]
            divergence_map[f"r{rd}_{bucket}"] = {
                "n": len(diffs),
                "mean_abs_diff": stats.mean(diffs) if diffs else None,
                "median_abs_diff": stats.median(diffs) if diffs else None,
                "max_abs_diff": max(diffs) if diffs else None,
            }

    # (ii) Korrelation beider Varianten mit dem echten Endresultat, gesamt +
    # kritische Zellen (R1-2 x hoher Fortschritt).
    all_pairs_boot = [(p["bootstrap"], p["won"]) for p in datapoints]
    all_pairs_anchor = [(p["anchor"], p["won"]) for p in datapoints]
    crit = [p for p in datapoints if is_critical(p)]
    crit_pairs_boot = [(p["bootstrap"], p["won"]) for p in crit]
    crit_pairs_anchor = [(p["anchor"], p["won"]) for p in crit]

    korrelationen = {
        "gesamt": {
            "bootstrap_vs_ergebnis": correlation_block(all_pairs_boot),
            "anchor_vs_ergebnis": correlation_block(all_pairs_anchor),
        },
        "kritische_zellen_r1_r2_hoher_fortschritt": {
            "bootstrap_vs_ergebnis": correlation_block(crit_pairs_boot),
            "anchor_vs_ergebnis": correlation_block(crit_pairs_anchor),
        },
    }

    # Sekundaer (Annahme, zusaetzlich): Differenz-Label gegen echte Punktemarge.
    margin_pairs_boot = [(r["bootstrap_value"][0] - r["bootstrap_value"][1],
                            r["real_scores"][0] - r["real_scores"][1]) for r in results]
    margin_pairs_anchor = [(r["anchor_value"][0] - r["anchor_value"][1],
                              r["real_scores"][0] - r["real_scores"][1]) for r in results]
    margin_crit_idx = [i for i, r in enumerate(results) if r["round"] in (1, 2) and r["progress_bucket"] == "high"]
    korrelationen_margin_sekundaer = {
        "gesamt": {
            "bootstrap_diff_vs_punktemarge": correlation_block(margin_pairs_boot),
            "anchor_diff_vs_punktemarge": correlation_block(margin_pairs_anchor),
        },
        "kritische_zellen_r1_r2_hoher_fortschritt": {
            "bootstrap_diff_vs_punktemarge": correlation_block([margin_pairs_boot[i] for i in margin_crit_idx]),
            "anchor_diff_vs_punktemarge": correlation_block([margin_pairs_anchor[i] for i in margin_crit_idx]),
        },
    }

    # (iii) Rechenzeit je Label.
    def time_stats(vals: list[float]) -> dict:
        if not vals:
            return {"n": 0}
        return {
            "n": len(vals), "mean_ms": stats.mean(vals), "median_ms": stats.median(vals),
            "min_ms": min(vals), "max_ms": max(vals),
        }

    zeit_gesamt = {
        "bootstrap_time_ms": time_stats([r["bootstrap_time_ms"] for r in results]),
        "anchor_time_ms": time_stats([r["anchor_time_ms"] for r in results]),
    }
    zeit_je_runde = {
        f"r{rd}": {
            "bootstrap_time_ms": time_stats([r["bootstrap_time_ms"] for r in results if r["round"] == rd]),
            "anchor_time_ms": time_stats([r["anchor_time_ms"] for r in results if r["round"] == rd]),
        }
        for rd in ROUNDS
    }
    mean_boot = zeit_gesamt["bootstrap_time_ms"].get("mean_ms", 0.0)
    mean_anchor = zeit_gesamt["anchor_time_ms"].get("mean_ms", 0.0)
    kostengate_vorschau = {
        "kommentar": "Grobe Vorschau, KEIN Stufe-1-Ersatz (dort: 50-Partien-Wallclock-A/B, "
                     "ganze Self-Play-Partie inkl. Drafting-Suche, nicht nur das Label). "
                     "Hier nur das Verhaeltnis der reinen Label-Rechenzeit je Rundenuebergang.",
        "anchor_ist_x_mal_teurer_als_bootstrap": (mean_anchor / mean_boot) if mean_boot > 0 else None,
    }

    report = {
        "prereg": "evaluations/PREREG_bootstrap_horizon.md, Stufe 0",
        "modell": Path(model).name,
        "korpus_glob": KORPUS_GLOB,
        "dateien_gescannt": len(files),
        "seed": SEED,
        "annahmen_markiert": [
            "Fortschritt = max(col_fill) UEBER BEIDE SPIELER (nicht in der Prereg festgelegt)",
            "Korrelation primaer BINAER (Label vs. hat-Spieler-i-gewonnen), gepoolt ueber beide "
            "Spielerperspektiven -- entspricht der Trainingsverwendung dieser [0,1]-Labels",
            "Punktemarge-Korrelation (Differenz-Label vs. echte Marge) ist SEKUNDAER/zusaetzlich, "
            "nicht in der Prereg gefordert",
        ],
        "pool_groessen_je_zelle": pool_sizes,
        "stichprobe": {
            "ziel_je_runde": ROUND_TARGET,
            "n_zustaende_ausgewaehlt": len(selection),
            "n_zustaende_erfolgreich_gelabelt": len(results),
            "je_runde": {f"r{rd}": sum(1 for r in results if r["round"] == rd) for rd in ROUNDS},
            "je_runde_x_fortschritt": {
                f"r{rd}_{b}": sum(1 for r in results if r["round"] == rd and r["progress_bucket"] == b)
                for rd in ROUNDS for b in ("low", "high")
            },
            "k1_aktiv_in_auswahl": sum(1 for r in results if r["k1_active"]),
        },
        "divergenz_landkarte_runde_x_fortschritt": divergence_map,
        "korrelation_mit_echtem_ergebnis": korrelationen,
        "korrelation_mit_punktemarge_sekundaer": korrelationen_margin_sekundaer,
        "rechenzeit_je_label": {"gesamt": zeit_gesamt, "je_runde": zeit_je_runde},
        "kostengate_vorschau": kostengate_vorschau,
        "raw_results": results,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")

    print()
    print("=== ZUSAMMENFASSUNG ===")
    print(f"n Zustaende: {len(results)}, davon je Runde: {report['stichprobe']['je_runde']}")
    print("Divergenz (mean |a-b|) je Zelle:")
    for k, v in divergence_map.items():
        print(f"  {k}: n={v['n']} mean={v['mean_abs_diff']}")
    print("Korrelation GESAMT (binaer, Label vs. Sieg):")
    print(f"  bootstrap: pearson={korrelationen['gesamt']['bootstrap_vs_ergebnis']['pearson']}, "
          f"spearman={korrelationen['gesamt']['bootstrap_vs_ergebnis']['spearman']}")
    print(f"  anchor:    pearson={korrelationen['gesamt']['anchor_vs_ergebnis']['pearson']}, "
          f"spearman={korrelationen['gesamt']['anchor_vs_ergebnis']['spearman']}")
    kz = korrelationen["kritische_zellen_r1_r2_hoher_fortschritt"]
    print("Korrelation KRITISCHE ZELLEN (R1-2 x hoher Fortschritt):")
    print(f"  bootstrap: n={kz['bootstrap_vs_ergebnis']['n']} pearson={kz['bootstrap_vs_ergebnis']['pearson']}, "
          f"spearman={kz['bootstrap_vs_ergebnis']['spearman']}")
    print(f"  anchor:    n={kz['anchor_vs_ergebnis']['n']} pearson={kz['anchor_vs_ergebnis']['pearson']}, "
          f"spearman={kz['anchor_vs_ergebnis']['spearman']}")
    print(f"Rechenzeit Mittel: bootstrap={mean_boot:.1f}ms, anchor={mean_anchor:.1f}ms "
          f"(Faktor {kostengate_vorschau['anchor_ist_x_mal_teurer_als_bootstrap']})")
    print(f"Artefakt: {OUT}")


if __name__ == "__main__":
    main()
