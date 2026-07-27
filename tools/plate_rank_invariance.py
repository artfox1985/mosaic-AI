# -*- coding: utf-8 -*-
"""
Mosaic-AI -- Task #5, Teil 1a: Score-Luecke vs. Platten-Signal (Gumbel-Rang-
Invarianz-Diagnose, 2026-07-27)
============================================================================

Folgetest zu "Wertungsplatten-Diagnose Teil 3" (evaluations/STATUS.md,
2026-07-26): dort zeigte sich, dass die MCTS-Besuchsverteilung (mcts_visits)
in 124/124 getesteten Faellen NICHT auf unterschiedliche Wertungsplatten-
Kombinationen reagierte, obwohl der rohe Policy-Prior klar reagierte (JS bis
0.58 Bit). Erklaerung dort (aus dem Code): bei `add_root_noise=false` faellt
die Gumbel-Top-m-/Sequential-Halving-Rangfolge auf reines Ranking nach
`g + ln(prior) + sigma(Q)` zurueck (g=0) -- ein verschobener, aber RANG-
GLEICHER Score aendert am Ranking nichts.

Dieses Skript quantifiziert das DIREKT statt nur strukturell zu argumentieren:
nutzt den granularen Gumbel-Trace (Task #95, `mosaic_rust.
net_search_state_json_trace`, PLATE_RANK_INVARIANCE-Ergaenzung Task #5) auf
denselben 16 Zustaenden x 8 Kombinationen wie Teil 3
(`tools/scoring_tile_sensitivity.py`, wiederverwendet fuer Zustands-/Kombi-
Auswahl -- KEIN Duplikat, siehe CLAUDE.md "vorhandene Skripte pruefen").

Zwei Groessen, BEIDE in denselben additiven Score-Einheiten
(`score = g + ln(prior) + sigma(Q)`, siehe net_mcts.rs):

1. Rang-1/2-Score-Luecke in der LETZTEN Sequential-Halving-Phase je
   (Zustand, Kombination) -- wie gross muesste ein Shift sein, um die
   Zugentscheidung an dieser Stelle zu kippen.
2. Platteninduzierte Sibling-Score-Spannweite je Kandidat-Aktion (ueber
   Kombinationen bei FESTEM Seed/Zustand gematcht per Beschreibungstext --
   `action_id` ist NICHT stabil zwischen getrennten `net_search_state_json`-
   Aufrufen, da jeder Aufruf `moves` unabhaengig neu nach Besuchen sortiert;
   die `description` (aus `label_search_move`) IST stabil, weil sie eine
   reine Funktion von Zustand+Aktion ist und Wertungsplatten die Zug-
   Legalitaet/-Kandidatenmenge nachweislich nicht beeinflussen, siehe
   Modul-Doku `scoring_tile_sensitivity.py`) -- die tatsaechliche
   Sigma-Verschiebung, die das Netz durch eine andere Plattenwahl je
   Kandidat erzeugt (`sigma_q` je Kandidat aus der jeweils LETZTEN Phase, in
   der er noch auftaucht, d.h. sein bestmoeglicher Schaetzwert innerhalb
   dieser Kombination-Suche).

Kernzahl: Faktor = Median(Rang-1/2-Luecke) / Median(Sibling-Sigma-Spannweite)
-- "um wieviel muesste das Plattensignal verstaerkt werden, damit es im
Median die Rang-1/2-Luecke erreicht".
"""
from __future__ import annotations

import argparse
import json
import os
import statistics as stats

import mosaic_rust

from tools.scoring_tile_sensitivity import pick_representative_combos, select_states


def run_trace(state, tile_ids, model_path, sims, c_puct, seed):
    s = dict(state)
    s["scoring_tile_ids"] = list(tile_ids)
    out = mosaic_rust.net_search_state_json_trace(
        json.dumps(s), model_path, sims, c_puct, seed
    )
    return json.loads(out)


def description_to_action_id(analysis):
    """`moves[].description` -> `action_id`, nur falls eindeutig (Beschreibung
    nicht doppelt vorkommt -- defensiv, sollte fuer Drafting-Zuege nicht
    passieren, siehe `label_search_move`)."""
    counts = {}
    mapping = {}
    for m in analysis.get("moves") or []:
        d = m["description"]
        counts[d] = counts.get(d, 0) + 1
        mapping[d] = m["action_id"]
    return {d: a for d, a in mapping.items() if counts[d] == 1}


def last_phase_rank_gap(analysis):
    """Score-Luecke Rang1-Rang2 in der letzten Halving-Phase, plus die
    sortierte Kandidatenliste dieser Phase (fuer Debug/Nachvollziehbarkeit).
    None, falls kein Gumbel-Trace vorliegt oder die letzte Phase < 2
    Kandidaten hat (sollte laut `build_gumbel_tree`-Schleifeninvariante --
    `keep = max(current.len()/2, 2)` -- nicht vorkommen, ausser bei nur 1
    Wurzelkandidaten insgesamt, dann werden ueberhaupt keine Phasen
    aufgezeichnet)."""
    gt = analysis.get("gumbel_trace")
    if not gt or not gt.get("phases"):
        return None, None
    last = gt["phases"][-1]
    cands = sorted(last["candidates"], key=lambda c: c["score"], reverse=True)
    if len(cands) < 2:
        return None, None
    return cands[0]["score"] - cands[1]["score"], cands


def per_candidate_final_sigma(analysis):
    """description -> sigma_q aus der jeweils LETZTEN Phase, in der der
    Kandidat noch auftaucht (= sein bestmoeglicher, am staerksten
    besuchsgestuetzter sigma_q-Schaetzwert innerhalb dieser Suche)."""
    gt = analysis.get("gumbel_trace")
    out = {}
    if not gt:
        return out
    for phase in gt.get("phases") or []:
        for c in phase["candidates"]:
            out[c["description"]] = c["sigma_q"]
    return out


def chosen_description(analysis):
    """Beschreibung der TATSAECHLICH gewaehlten Wurzelaktion (`ai_action`
    indiziert in `moves`, `mcts_visits`-basiert -- exakt dasselbe Feld, das
    `tools/scoring_tile_sensitivity.py`s JS-Divergenz-Test ueber
    `mcts_visits` bereits maass). Dient als ungeschminkter Ground-Truth-
    Gegencheck zum abgeleiteten `top2_margin`-Flip (der nur eine PROXY-
    Grosse aus der letzten Halving-Phase ist, siehe `main`-Kommentar) --
    """
    ai_action = analysis.get("ai_action")
    moves = analysis.get("moves") or []
    if ai_action is None or ai_action >= len(moves):
        return None
    return moves[ai_action]["description"]


def per_candidate_final_score(analysis):
    """Wie `per_candidate_final_sigma`, aber der volle additive Score
    (`g + ln(prior) + sigma_q`) je Kandidat aus seiner letzten Phase --
    fuer den gezielten Top-2-Margin-Test (siehe `main`): verfolgt die
    beiden KONKRETEN Kandidaten, die im Referenz-Combo Rang 1/2 belegen,
    durch alle 8 Kombinationen und prueft, ob ihre Score-Differenz
    (dieselbe Groesse wie die Rang1/2-Luecke) je das Vorzeichen wechselt --
    im Gegensatz zur ungezielten "alle Kandidaten"-Spannweite (die auch
    laengst abgehaengte Long-Tail-Kandidaten mit stark schwankendem,
    aber fuer die Zugwahl irrelevantem sigma_q mitzaehlt)."""
    gt = analysis.get("gumbel_trace")
    out = {}
    if not gt:
        return out
    for phase in gt.get("phases") or []:
        for c in phase["candidates"]:
            out[c["description"]] = c["score"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-set", default="evaluations/frozen_eval_set.pkl")
    ap.add_argument("--model", default="models/alphazero_v16_best.onnx")
    ap.add_argument("--sims", type=int, default=400)
    ap.add_argument("--c-puct", type=float, default=1.5)
    ap.add_argument("--n-states", type=int, default=16)
    ap.add_argument("--n-combos", type=int, default=8)
    ap.add_argument("--seed", type=int, default=1000)
    ap.add_argument("--arm", default="off", help="Label fuer PLATE_SHAPING_ENABLED-Zustand des installierten Wheels (nur Doku im Ergebnis-JSON, wird nicht geprueft)")
    ap.add_argument("--out", default="evaluations/plate_rank_invariance_result.json")
    args = ap.parse_args()

    import pickle

    with open(args.eval_set, "rb") as f:
        data = pickle.load(f)
    records = data["records"]
    states = select_states(records, args.n_states)
    print(f"[plate_rank_invariance] {len(states)} Zustaende gewaehlt "
          f"(Runden: {sorted(set(r['state']['round'] for _, r in states))})")

    combos = pick_representative_combos(args.n_combos)
    print(f"[plate_rank_invariance] {len(combos)} Kombinationen: {combos}")

    per_state_results = []
    all_gaps = []
    all_sigma_spreads = []
    all_top2_margin_spreads = []
    all_top2_flip_counts = []  # je Zustand: Anzahl Kombinationen (von 8), die die Marge <=0 drehen
    all_actual_decision_flips = 0
    all_actual_decision_tracked = 0
    n_skipped_single_candidate = 0
    n_skipped_no_finalphase = 0

    for idx, (record_index, rec) in enumerate(states):
        state = rec["state"]
        original_ids = tuple(sorted(state["scoring_tile_ids"]))
        combos_for_state = [c for c in combos if c != original_ids] or combos[:]
        combos_for_state = [original_ids] + combos_for_state

        combo_gaps = []
        # description -> {combo_index: sigma_q}
        sigma_by_desc = {}
        # ci -> {description: score}  (fuer den gezielten Top-2-Margin-Test)
        score_by_combo = {}
        ref_top1_desc = ref_top2_desc = None
        ref_chosen_desc = None
        n_root_candidates = None
        state_decision_flips = 0
        state_decision_tracked = 0
        for ci, combo in enumerate(combos_for_state):
            out = run_trace(state, combo, args.model, args.sims, args.c_puct, args.seed)
            if not out.get("moves"):
                continue
            n_root_candidates = len(out["moves"])
            gap, cands = last_phase_rank_gap(out)
            if gap is None:
                if n_root_candidates <= 1:
                    n_skipped_single_candidate += 1
                else:
                    n_skipped_no_finalphase += 1
            else:
                combo_gaps.append(gap)
                all_gaps.append(gap)
                if ci == 0:
                    ref_top1_desc = cands[0]["description"]
                    ref_top2_desc = cands[1]["description"]

            # Ground-Truth-Gegencheck (unabhaengig vom score-basierten
            # top2-Proxy oben): die TATSAECHLICH von `mcts_visits`
            # bestimmte Zugwahl -- exakt dieselbe Groesse, die Teil 3
            # (JS-Divergenz ueber `mcts_visits`) bereits maass.
            cdesc = chosen_description(out)
            if ci == 0:
                ref_chosen_desc = cdesc
            elif ref_chosen_desc is not None and cdesc is not None:
                state_decision_tracked += 1
                if cdesc != ref_chosen_desc:
                    state_decision_flips += 1

            desc_map = description_to_action_id(out)
            sigmas = per_candidate_final_sigma(out)
            for desc, sigma in sigmas.items():
                if desc not in desc_map:
                    continue  # nicht eindeutig einer action_id zuordenbar, verwerfen
                sigma_by_desc.setdefault(desc, {})[ci] = sigma

            score_by_combo[ci] = per_candidate_final_score(out)

        all_actual_decision_flips += state_decision_flips
        all_actual_decision_tracked += state_decision_tracked

        state_sigma_spreads = []
        for desc, per_combo in sigma_by_desc.items():
            vals = list(per_combo.values())
            if len(vals) < 2:
                continue
            spread = max(vals) - min(vals)
            state_sigma_spreads.append(spread)
            all_sigma_spreads.append(spread)

        # Gezielter Top-2-Margin-Test (siehe `per_candidate_final_score`-Doku):
        # verfolgt NUR die im Referenz-Combo tatsaechlich fuehrenden zwei
        # Kandidaten durch alle 8 Kombinationen -- direkt vergleichbar mit
        # der Rang1/2-Luecke (dieselbe additive Score-Einheit), im
        # Gegensatz zur oben berechneten "alle Kandidaten"-Spannweite.
        top2_margins = []
        if ref_top1_desc is not None and ref_top2_desc is not None:
            for ci, fs in score_by_combo.items():
                if ref_top1_desc in fs and ref_top2_desc in fs:
                    top2_margins.append(fs[ref_top1_desc] - fs[ref_top2_desc])
        top2_margin_spread = (max(top2_margins) - min(top2_margins)) if len(top2_margins) >= 2 else None
        top2_flips = sum(1 for m in top2_margins if m < 0) if top2_margins else None
        if top2_margin_spread is not None:
            all_top2_margin_spreads.append(top2_margin_spread)
        if top2_flips is not None:
            all_top2_flip_counts.append(top2_flips)

        per_state_results.append({
            "state_index_in_eval_set": record_index,
            "round": state["round"],
            "original_scoring_tile_ids": list(original_ids),
            "n_root_candidates": n_root_candidates,
            "n_combos_with_gap": len(combo_gaps),
            "rank1_2_gap_mean": stats.mean(combo_gaps) if combo_gaps else None,
            "rank1_2_gap_min": min(combo_gaps) if combo_gaps else None,
            "n_candidates_with_sigma_spread": len(state_sigma_spreads),
            "sibling_sigma_spread_mean": stats.mean(state_sigma_spreads) if state_sigma_spreads else None,
            "sibling_sigma_spread_max": max(state_sigma_spreads) if state_sigma_spreads else None,
            "top2_n_combos_tracked": len(top2_margins),
            "top2_margin_spread": top2_margin_spread,
            "top2_margin_min": min(top2_margins) if top2_margins else None,
            "top2_flips_of_8": top2_flips,
            "actual_decision_flips": state_decision_flips,
            "actual_decision_tracked": state_decision_tracked,
        })
        print(f"  Zustand {idx} (round={state['round']}, cands={n_root_candidates}): "
              f"gap_mean={per_state_results[-1]['rank1_2_gap_mean']}  "
              f"sigma_spread_mean={per_state_results[-1]['sibling_sigma_spread_mean']} "
              f"top2_margin_spread={top2_margin_spread} top2_flips={top2_flips}/8 "
              f"actual_decision_flips={state_decision_flips}/{state_decision_tracked} "
              f"(n_gaps={len(combo_gaps)}, n_sigma={len(state_sigma_spreads)})")

    def summarize(vals):
        vals = [v for v in vals if v is not None]
        if not vals:
            return None
        return {
            "n": len(vals), "mean": stats.mean(vals), "median": stats.median(vals),
            "stdev": stats.pstdev(vals) if len(vals) > 1 else 0.0,
            "min": min(vals), "max": max(vals),
        }

    gap_summary = summarize(all_gaps)
    sigma_summary = summarize(all_sigma_spreads)
    top2_spread_summary = summarize(all_top2_margin_spreads)
    total_top2_flips = sum(all_top2_flip_counts)
    total_top2_tracked = sum(r["top2_n_combos_tracked"] for r in per_state_results)
    summary = {
        "model": args.model,
        "sims": args.sims,
        "c_puct": args.c_puct,
        "seed": args.seed,
        "plate_shaping_arm": args.arm,
        "n_states": len(per_state_results),
        "n_combos_tested_per_state": args.n_combos,
        "n_skipped_single_candidate_state_combo": n_skipped_single_candidate,
        "n_skipped_no_final_phase_state_combo": n_skipped_no_finalphase,
        "rank1_2_score_gap": gap_summary,
        # ACHTUNG (siehe `per_candidate_final_sigma`-Doku): enthaelt auch
        # laengst abgehaengte Long-Tail-Kandidaten (grosse, aber fuer die
        # Zugwahl irrelevante sigma_q-Schwankungen bei nur 1 Besuch/Phase-1)
        # -- NICHT direkt als "das Plattensignal, das die Entscheidung
        # bedroht" interpretieren, siehe `top2_margin_spread` fuer die
        # gezielte Version.
        "sibling_sigma_spread_all_candidates_CAUTION_includes_irrelevant_long_tail": sigma_summary,
        # Gezielter Test: NUR die im Referenz-Combo tatsaechlich fuehrenden
        # zwei Kandidaten, ueber alle 8 Kombinationen verfolgt -- direkt
        # vergleichbar mit `rank1_2_score_gap` (identische additive
        # Score-Einheit, s. `per_candidate_final_score`-Doku).
        "top2_margin_spread": top2_spread_summary,
        "top2_flips_total": total_top2_flips,
        "top2_combos_tracked_total": total_top2_tracked,
        "top2_flip_rate": (total_top2_flips / total_top2_tracked) if total_top2_tracked else None,
        # GROUND TRUTH (dieselbe Groesse wie Teil 3s JS-Divergenz-Test ueber
        # `mcts_visits`, hier direkt als binaerer "hat sich `ai_action`
        # geaendert"-Vergleich): massgeblich fuer die Handlungsempfehlung,
        # NICHT der score-basierte `top2_flip_rate`-Proxy oben (der misst
        # nur, ob die REIHENFOLGE der letzten Halving-Phase kippt, was bei
        # asymmetrischen Halving-Baeumen -- n_root keine Zweierpotenz --
        # nicht immer 1:1 der finalen `mcts_visits`-Entscheidung entspricht).
        "actual_decision_flips_total": all_actual_decision_flips,
        "actual_decision_tracked_total": all_actual_decision_tracked,
        "actual_decision_flip_rate": (all_actual_decision_flips / all_actual_decision_tracked) if all_actual_decision_tracked else None,
    }
    if gap_summary and sigma_summary and sigma_summary["median"] > 0:
        summary["factor_gap_median_over_sigma_spread_median_ALL_CANDIDATES"] = gap_summary["median"] / sigma_summary["median"]
    if gap_summary and top2_spread_summary and top2_spread_summary["median"] > 0:
        summary["factor_gap_median_over_top2_margin_spread_median"] = gap_summary["median"] / top2_spread_summary["median"]

    print("\n=== ZUSAMMENFASSUNG ===")
    print(json.dumps(summary, indent=2, ensure_ascii=True))

    result = {"summary": summary, "per_state": per_state_results}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nErgebnis geschrieben nach {args.out}")


if __name__ == "__main__":
    main()
