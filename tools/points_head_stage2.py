# -*- coding: utf-8 -*-
"""
Mosaic-AI -- PREREG_points_head_plates.md, Stufe 2 (ALLEINIGER Entscheidungspunkt,
2026-08-09)
============================================================================

Fragestellung (siehe evaluations/PREREG_points_head_plates.md, Abschnitt
"Stufe 2" + das direkt darunter stehende, VERBINDLICHE Amendment): reagieren
`net_points_forecast`, `net_opp_points_forecast` und (Pflicht-Referenz)
`net_raw_value` auf einen Wertungsplatten-Wechsel im NIVEAU (alle Wurzel-
kandidaten gemeinsam verschoben, fuer die Zugwahl wertlos -- siehe Fallgruben-
Abschnitt der Vorregistrierung, Plate-Shaping-Praezedenzfall) oder in der
ZUG-DIFFERENZIERUNG (die Kandidaten werden GEGENEINANDER verschoben, das
Ranking aendert sich)?

Datenquelle: additive Rust-Ergaenzung (bereits gebaut/installiert, siehe
Auftrag) -- jeder Eintrag in `moves[]` von `mosaic_rust.
net_search_state_json_trace` hat jetzt `net_raw_value`, `net_points_forecast`,
`net_opp_points_forecast` (vom Netz am KINDzustand berechnet). Runde-5-
Zustaende haben strukturell KEIN Netz (`has_net: False`, `value_debug: None`,
und die `net_*`-Felder fehlen in `moves[]` komplett) -- verifiziert vor dem
Bau dieses Skripts, kein Rateversuch.

Protokoll wie Stufe 1 (additiv zu `tools/plate_rank_invariance.py`, aber
NICHT dessen Datei umgebaut -- CLAUDE.md "vorhandene Skripte pruefen", hier
wird bewusst `select_states`/`pick_representative_combos` aus
`tools/scoring_tile_sensitivity.py` wiederverwendet, kein Duplikat):
Champion @400 Sims, Seed 1000, 16 Zustaende x 8 Wertungsplatten-Kombinationen
(dieselbe FESTE 8er-Liste aus `pick_representative_combos(8)` auf jeden
Zustand angewandt -- anders als in `plate_rank_invariance.py`/
`scoring_tile_sensitivity.py` wird der tatsaechlich gespielte Original-Combo
NICHT als zusaetzlicher 9. Fall vorangestellt: Stufe 2 braucht keinen
"Referenz-Combo", sondern acht gleichrangige Kombinationen fuer den
paarweisen Vergleich).

Kandidaten-Angleichung: `action_id` ist NICHT stabil zwischen getrennten
`net_search_state_json_trace`-Aufrufen (jeder Aufruf sortiert `moves`
unabhaengig neu) -- empirisch verifiziert vor dem Bau dieses Skripts
(Mismatches bei identischer `description` in mehreren Testzustaenden).
`description` (aus `label_search_move`) ist stabil, weil sie eine reine
Funktion von Zustand+Aktion ist (siehe Kommentar in
`plate_rank_invariance.py::description_to_action_id`). Alignment daher ueber
die Schnittmenge der `description`-Strings ueber ALLE 8 Kombinationen eines
Zustands.

Zerlegung je (Zustand, Groesse): NIVEAU = Mittelwert des Kopf-Werts ueber die
angeglichenen Kandidaten (ein Skalar je Kombination), ZENTRIERT = Vektor
minus NIVEAU (nur dieser Teil ist rangrelevant fuer die Zugwahl).

Primaere Entscheidungsmetrik (Kendall-Tau, `_kendall_tau_a` aus
`tools/oracle_metrics.py` -- projekteigene tau-a-Implementierung ohne
Bindungskorrektur, dort dokumentiert warum kein scipy): je Zustand der
MITTELWERT der paarweisen Tau-Werte ueber alle C(8,2)=28 Kombinationspaare
(Tau ist invariant gegen eine additive Konstante je Vektor, NIVEAU-Verschiebung
aendert den Tau-Wert also nicht -- Rohvektor und zentrierter Vektor liefern
identische Tau-Werte, es wird der Rohvektor verwendet). Der berichtete
"Tau-Median" ist dann der MEDIAN dieser Zustands-Mittelwerte ueber die
(bis zu) 16 Zustaende -- exakt die im Amendment beschriebene Reihenfolge
"alle Paare, dann Median ueber Zustaende".

Nebengroesse laut AMENDMENT (ersetzt das urspruengliche, degenerierte
Rauschboden-Kriterium -- siehe PREREG-Datei, Abschnitt
"AMENDMENT vor dem Stufe-2-Lauf"):
    mean_i |zentriert_A(i) - zentriert_B(i)| / std_i(zentriert_A(i))
Die Formel ist in A/B NICHT symmetrisch (der Nenner ist die Streuung von A
allein). Hier ausgewertet ueber ALLE GERICHTETEN Kombinationspaare
(A != B, 8*7=56 je Zustand) -- das deckt beide Richtungen jedes Paars ab,
ohne eine willkuerliche Wahl "welcher der beiden Combos ist A" treffen zu
muessen. Je Zustand wird der MEDIAN dieser 56 Werte gebildet, dann -- analog
zur Tau-Aggregation -- der MEDIAN dieser Zustandswerte ueber die Zustaende
gebildet. Diese zweistufige Aggregation (Median je Zustand, dann Median ueber
Zustaende) ist eine Praezisierung, die das Amendment offenlaesst; sie wird
hier explizit dokumentiert (siehe Bericht, Punkt "was wackelt").

Deskriptive Zusatzgroesse (nicht entscheidungsrelevant): Spannweite des
NIVEAUs ueber die 8 Kombinationen gegen die MITTLERE Spannweite der
zentrierten Komponenten je Kandidat -- zeigt, wie viel der Gesamt-
Plattenwirkung im Niveau vs. in der Differenzierung liegt.
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import statistics as stats
from itertools import combinations

import mosaic_rust

from tools.oracle_metrics import _kendall_tau_a
from tools.scoring_tile_sensitivity import pick_representative_combos, select_states

HEAD_FIELDS = ("net_points_forecast", "net_opp_points_forecast", "net_raw_value")


def run_trace(state, tile_ids, model_path, sims, c_puct, seed):
    s = dict(state)
    s["scoring_tile_ids"] = list(tile_ids)
    out = mosaic_rust.net_search_state_json_trace(
        json.dumps(s), model_path, sims, c_puct, seed
    )
    return json.loads(out)


def collect_head_vectors(out):
    """`description` -> {Groesse: Wert} fuer alle Wurzelkandidaten dieses
    Aufrufs. None, falls kein Netz (Runde-5-Randfall: `has_net=False`, die
    `net_*`-Felder fehlen in `moves[]` komplett -- struktureller Ausfall,
    kein regulaerer 'Kopf fehlt'-Fall)."""
    if not out.get("has_net", True):
        return None
    moves = out.get("moves") or []
    if not moves:
        return None
    result = {}
    for m in moves:
        if "net_points_forecast" not in m:
            return None
        result[m["description"]] = {f: m[f] for f in HEAD_FIELDS}
    return result


def summarize(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return {
        "n": len(vals),
        "mean": stats.mean(vals),
        "median": stats.median(vals),
        "stdev": stats.pstdev(vals) if len(vals) > 1 else 0.0,
        "min": min(vals),
        "max": max(vals),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-set", default="evaluations/frozen_eval_set.pkl")
    ap.add_argument("--model", default="models/alphazero_v21_2d_brierbest.onnx")
    ap.add_argument("--sims", type=int, default=400)
    ap.add_argument("--c-puct", type=float, default=1.5)
    ap.add_argument("--n-states", type=int, default=16)
    ap.add_argument("--n-combos", type=int, default=8)
    ap.add_argument("--seed", type=int, default=1000)
    ap.add_argument("--out", default="evaluations/artifacts/points_head_plates_stage2.json")
    args = ap.parse_args()

    with open(args.eval_set, "rb") as f:
        data = pickle.load(f)
    records = data["records"]
    states = select_states(records, args.n_states)
    print(f"[points_head_stage2] {len(states)} Zustaende gewaehlt "
          f"(Runden: {sorted(set(r['state']['round'] for _, r in states))})")

    combos = pick_representative_combos(args.n_combos)
    print(f"[points_head_stage2] {len(combos)} Kombinationen (fest, je Zustand identisch): {combos}")

    per_state_results = []
    tau_per_state = {f: [] for f in HEAD_FIELDS}
    relshift_per_state = {f: [] for f in HEAD_FIELDS}
    niveau_spread_per_state = {f: [] for f in HEAD_FIELDS}
    mean_centered_spread_per_state = {f: [] for f in HEAD_FIELDS}
    n_candidates_after_alignment = []
    n_skipped_no_net = 0
    n_skipped_too_few_candidates = 0
    degenerate_std_events = 0

    for idx, (record_index, rec) in enumerate(states):
        state = rec["state"]
        round_ = state["round"]

        per_combo_vectors = []
        skip_reason = None
        for combo in combos:
            out = run_trace(state, combo, args.model, args.sims, args.c_puct, args.seed)
            vecs = collect_head_vectors(out)
            if vecs is None:
                skip_reason = "kein_netz_oder_keine_kandidaten"
                break
            per_combo_vectors.append(vecs)

        if skip_reason is not None:
            n_skipped_no_net += 1
            print(f"  Zustand {idx} (round={round_}): {skip_reason} (strukturell, "
                  f"typischerweise Runde 5), uebersprungen")
            per_state_results.append({
                "state_index_in_eval_set": record_index,
                "round": round_,
                "skipped": True,
                "skip_reason": skip_reason,
            })
            continue

        common_desc = set(per_combo_vectors[0].keys())
        for v in per_combo_vectors[1:]:
            common_desc &= set(v.keys())
        common_desc = sorted(common_desc)
        n_cand = len(common_desc)
        n_candidates_after_alignment.append(n_cand)
        n_before = [len(v) for v in per_combo_vectors]

        if n_cand < 2:
            n_skipped_too_few_candidates += 1
            print(f"  Zustand {idx} (round={round_}): nur {n_cand} gemeinsame Kandidaten "
                  f"nach Angleichung (vorher je Kombo: {n_before}) -- Tau/Verschiebung nicht "
                  f"berechenbar, uebersprungen")
            per_state_results.append({
                "state_index_in_eval_set": record_index,
                "round": round_,
                "skipped": True,
                "skip_reason": "zu_wenige_kandidaten_nach_angleichung",
                "n_candidates_before_alignment_per_combo": n_before,
                "n_candidates_after_alignment": n_cand,
            })
            continue

        state_entry = {
            "state_index_in_eval_set": record_index,
            "round": round_,
            "skipped": False,
            "n_candidates_before_alignment_per_combo": n_before,
            "n_candidates_after_alignment": n_cand,
            "heads": {},
        }

        head_log_parts = []
        for f in HEAD_FIELDS:
            raw_vectors = [[v[d][f] for d in common_desc] for v in per_combo_vectors]
            niveaus = [stats.mean(vec) for vec in raw_vectors]
            centered_vectors = [
                [x - niveau for x in vec] for vec, niveau in zip(raw_vectors, niveaus)
            ]

            # -- Primaere Metrik: paarweiser Kendall-Tau (Rohvektor, invariant
            # gegen die additive NIVEAU-Konstante je Kombination) --
            pair_taus = []
            for a_i, b_i in combinations(range(len(raw_vectors)), 2):
                tau = _kendall_tau_a(raw_vectors[a_i], raw_vectors[b_i])
                if tau is not None:
                    pair_taus.append(tau)
            state_tau = stats.mean(pair_taus) if pair_taus else None

            # -- Nebengroesse (Amendment): gerichtete Paare A != B --
            pair_relshifts = []
            n_degenerate = 0
            for a_i in range(len(centered_vectors)):
                std_a = stats.pstdev(centered_vectors[a_i])
                if std_a == 0:
                    n_degenerate += 1
                    continue
                for b_i in range(len(centered_vectors)):
                    if a_i == b_i:
                        continue
                    diffs = [
                        abs(centered_vectors[a_i][k] - centered_vectors[b_i][k])
                        for k in range(n_cand)
                    ]
                    pair_relshifts.append(stats.mean(diffs) / std_a)
            degenerate_std_events += n_degenerate
            state_relshift = stats.median(pair_relshifts) if pair_relshifts else None

            # -- Deskriptiv: Niveau- vs. zentrierte Spannweite --
            niveau_spread = max(niveaus) - min(niveaus)
            per_candidate_spreads = []
            for k in range(n_cand):
                vals_k = [cv[k] for cv in centered_vectors]
                per_candidate_spreads.append(max(vals_k) - min(vals_k))
            mean_centered_spread = stats.mean(per_candidate_spreads)

            if state_tau is not None:
                tau_per_state[f].append(state_tau)
            if state_relshift is not None:
                relshift_per_state[f].append(state_relshift)
            niveau_spread_per_state[f].append(niveau_spread)
            mean_centered_spread_per_state[f].append(mean_centered_spread)

            state_entry["heads"][f] = {
                "niveau_per_combo": niveaus,
                "niveau_spread_across_combos": niveau_spread,
                "mean_centered_spread_across_candidates": mean_centered_spread,
                "state_mean_pairwise_tau": state_tau,
                "n_pairs_tau": len(pair_taus),
                "state_median_pairwise_relshift": state_relshift,
                "n_pairs_relshift": len(pair_relshifts),
                "n_degenerate_std_a_zero": n_degenerate,
            }
            tau_str = f"{state_tau:.3f}" if state_tau is not None else "n/a"
            rel_str = f"{state_relshift:.3f}" if state_relshift is not None else "n/a"
            head_log_parts.append(f"{f}: tau={tau_str} relshift={rel_str}")

        per_state_results.append(state_entry)
        print(f"  Zustand {idx} (round={round_}, n_cand={n_cand}, vorher={n_before}): "
              + "; ".join(head_log_parts))

    heads_summary = {}
    for f in HEAD_FIELDS:
        tau_summary = summarize(tau_per_state[f])
        relshift_summary = summarize(relshift_per_state[f])
        niveau_spread_summary = summarize(niveau_spread_per_state[f])
        centered_spread_summary = summarize(mean_centered_spread_per_state[f])

        tau_median = tau_summary["median"] if tau_summary else None
        relshift_median = relshift_summary["median"] if relshift_summary else None

        regel = None
        if tau_median is not None and relshift_median is not None:
            if tau_median < 0.9 and relshift_median >= 0.2:
                regel = "2a"
            else:
                regel = "2b"

        niveau_over_centered_ratio = None
        if (niveau_spread_summary and centered_spread_summary
                and centered_spread_summary["median"] > 0):
            niveau_over_centered_ratio = (
                niveau_spread_summary["median"] / centered_spread_summary["median"]
            )

        heads_summary[f] = {
            "state_mean_pairwise_tau__summary_over_states": tau_summary,
            "tau_median": tau_median,
            "state_median_pairwise_relshift__summary_over_states": relshift_summary,
            "relative_shift_median": relshift_median,
            "regel": regel,
            "niveau_spread_across_combos__summary_over_states": niveau_spread_summary,
            "mean_centered_spread_across_candidates__summary_over_states": centered_spread_summary,
            "niveau_spread_median_over_centered_spread_median_ratio_DESKRIPTIV": niveau_over_centered_ratio,
        }

    summary = {
        "prereg": "evaluations/PREREG_points_head_plates.md (Stufe 2, mit Amendment)",
        "model": args.model,
        "sims": args.sims,
        "c_puct": args.c_puct,
        "seed": args.seed,
        "n_states_requested": args.n_states,
        "n_states_selected": len(states),
        "n_states_usable": len(per_state_results) - n_skipped_no_net - n_skipped_too_few_candidates,
        "n_states_skipped_no_net_or_no_candidates": n_skipped_no_net,
        "n_states_skipped_too_few_candidates_after_alignment": n_skipped_too_few_candidates,
        "n_combos_per_state": len(combos),
        "combos": [list(c) for c in combos],
        "n_candidates_after_alignment_per_state": n_candidates_after_alignment,
        "n_candidates_after_alignment_summary": summarize(n_candidates_after_alignment),
        "degenerate_std_a_zero_events_total": degenerate_std_events,
        "aggregation_methodology_note": (
            "Tau: je Zustand Mittelwert ueber alle C(8,2)=28 Kombinationspaare "
            "(Rohvektor, tau-invariant gegen additive Konstante), dann Median "
            "dieser Zustandswerte ueber die Zustaende ('alle Paare, dann Median "
            "ueber Zustaende', wortgetreu aus dem Amendment). Relative Verschiebung: "
            "je Zustand Median ueber alle 56 GERICHTETEN Kombinationspaare (A!=B, "
            "Nenner=Streuung von A), dann Median dieser Zustandswerte ueber die "
            "Zustaende -- diese zweistufige Aggregation ist eine Praezisierung, "
            "die das Amendment nicht explizit festlegt (siehe Modul-Docstring)."
        ),
        "heads": heads_summary,
    }

    print("\n=== ZUSAMMENFASSUNG ===")
    print(json.dumps(summary, indent=2, ensure_ascii=True))

    result = {"summary": summary, "per_state": per_state_results}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nErgebnis geschrieben nach {args.out}")


if __name__ == "__main__":
    main()
