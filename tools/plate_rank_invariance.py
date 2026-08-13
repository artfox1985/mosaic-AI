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


# ---------------------------------------------------------------------------
# Vorregistrierung Stufe 1 (evaluations/PREREG_points_head_plates.md,
# 2026-08-09): traegt der PUNKTE-Kopf (und der opp_points_head, sowie -- als
# Referenz -- der rohe raw_value) Wertungsplatten-Information an der WURZEL?
# Rein additiv zum obigen Gumbel-Rang-Invarianz-Test: nutzt denselben Trace
# (`value_debug`, `RootValueDebug` in net_mcts.rs ~Zeile 2539), der bei jedem
# `run_trace`-Aufruf oben schon anfaellt -- kein zusaetzliches Sims-Budget je
# Aufruf. Rauschboden-Protokoll 1:1 aus scoring_tile_sensitivity.py's
# `baseline_*_two_seeds` gespiegelt (dieselbe Original-Kombination, zwei
# Seeds), NICHT neu erfunden.
# ---------------------------------------------------------------------------
HEAD_FIELDS = ("points_forecast", "opp_points_forecast", "raw_value")


def value_debug_heads(analysis):
    """`value_debug`-Feld -> {points_forecast, opp_points_forecast, raw_value}.
    Fehlt `value_debug` komplett (laut `net_search_state_json_trace`-Doku in
    lib.rs nur der 0-Wurzelkandidaten-Randfall), liefert das Dict ueberall
    None -- ein eigenstaendiger Anomalie-Fall, kein regulaeres "Kopf fehlt"
    (siehe Aufrufer/Regel (e))."""
    vd = analysis.get("value_debug")
    if not vd:
        return {f: None for f in HEAD_FIELDS}
    return {f: vd.get(f) for f in HEAD_FIELDS}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-set", default="evaluations/frozen_eval_set.pkl")
    ap.add_argument("--model", default="models/alphazero_v16_best.onnx")
    ap.add_argument("--sims", type=int, default=400)
    ap.add_argument("--c-puct", type=float, default=1.5)
    ap.add_argument("--n-states", type=int, default=16)
    ap.add_argument("--n-combos", type=int, default=8)
    ap.add_argument("--seed", type=int, default=1000)
    ap.add_argument("--seed2", type=int, default=None,
                     help="PREREG_points_head_plates.md Stufe 1 (c): zweiter Seed fuer den "
                          "Rauschboden (dieselbe Original-Kombination, zwei Seeds -- 1:1 aus "
                          "scoring_tile_sensitivity.py's baseline_*_two_seeds gespiegelt). "
                          "Default (None) = --seed + 1000, reproduziert dort die dortigen "
                          "hartkodierten 1000/2000.")
    ap.add_argument("--arm", default="off", help="Label fuer PLATE_SHAPING_ENABLED-Zustand des installierten Wheels (nur Doku im Ergebnis-JSON, wird nicht geprueft)")
    ap.add_argument("--out", default="evaluations/plate_rank_invariance_result.json")
    args = ap.parse_args()
    seed2 = args.seed2 if args.seed2 is not None else args.seed + 1000

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
    # -- Stufe 1 (PREREG_points_head_plates.md) --
    all_plate_spread = {f: [] for f in HEAD_FIELDS}
    all_seed_noise = {f: [] for f in HEAD_FIELDS}
    heads_missing_states = {f: [] for f in HEAD_FIELDS}

    for idx, (record_index, rec) in enumerate(states):
        state = rec["state"]
        original_ids = tuple(sorted(state["scoring_tile_ids"]))
        combos_for_state = [c for c in combos if c != original_ids] or combos[:]
        combos_for_state = [original_ids] + combos_for_state

        combo_gaps = []
        # ci -> {points_forecast, opp_points_forecast, raw_value} (Stufe 1)
        head_by_combo = {}
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
            head_by_combo[ci] = value_debug_heads(out)  # Stufe 1
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

        # -- Stufe 1 (b): Platten-Spannweite je Kopf ueber die 8 (FESTER
        # Seed=args.seed) bereits oben ausgefuehrten Kombinationen -- kein
        # Zusatzaufruf. Fehlender Kopf (None) wird NICHT als 0 gerechnet
        # (Regel (e)): wird aus der Spannweite ausgeschlossen und separat als
        # "fehlt in mind. 1 Kombination" vermerkt.
        head_plate_spread = {}
        head_plate_present_all = {}
        for f in HEAD_FIELDS:
            vals = [hv[f] for hv in head_by_combo.values() if hv[f] is not None]
            n_missing = sum(1 for hv in head_by_combo.values() if hv[f] is None)
            head_plate_present_all[f] = bool(head_by_combo) and n_missing == 0
            head_plate_spread[f] = (max(vals) - min(vals)) if len(vals) >= 2 else None

        # -- Stufe 1 (c): Seed-Rauschboden, 1:1 aus scoring_tile_sensitivity.py
        # `baseline_*_two_seeds` gespiegelt -- dieselbe Original-Kombination,
        # zwei Seeds. ci=0 im obigen Loop IST bereits "Seed A" (Original-
        # Kombination, seed=args.seed); hier nur der EINE zusaetzliche
        # "Seed B"-Aufruf noetig (analog `out_seed_b` dort).
        head_seed_noise = {f: None for f in HEAD_FIELDS}
        seed_a_heads = head_by_combo.get(0)
        head_debug_seed_b = None
        if seed_a_heads is not None:
            out_seed_b = run_trace(state, original_ids, args.model, args.sims, args.c_puct, seed2)
            head_debug_seed_b = value_debug_heads(out_seed_b)
            for f in HEAD_FIELDS:
                a, b = seed_a_heads[f], head_debug_seed_b[f]
                if a is not None and b is not None:
                    head_seed_noise[f] = abs(a - b)

        for f in HEAD_FIELDS:
            if head_plate_spread[f] is not None:
                all_plate_spread[f].append(head_plate_spread[f])
            if head_seed_noise[f] is not None:
                all_seed_noise[f].append(head_seed_noise[f])
            if not head_plate_present_all[f]:
                heads_missing_states[f].append(record_index)

        head_debug_by_combo = [
            {"combo": list(combo), **head_by_combo[ci]}
            for ci, combo in enumerate(combos_for_state)
            if ci in head_by_combo
        ]

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
            # -- Stufe 1 (PREREG_points_head_plates.md), additiv --
            "head_debug_by_combo": head_debug_by_combo,
            "head_debug_seed_b_original_combo": head_debug_seed_b,
            "points_forecast_plate_spread": head_plate_spread["points_forecast"],
            "opp_points_forecast_plate_spread": head_plate_spread["opp_points_forecast"],
            "raw_value_plate_spread": head_plate_spread["raw_value"],
            "points_forecast_seed_noise_two_seeds": head_seed_noise["points_forecast"],
            "opp_points_forecast_seed_noise_two_seeds": head_seed_noise["opp_points_forecast"],
            "raw_value_seed_noise_two_seeds": head_seed_noise["raw_value"],
            "points_forecast_head_present_all_combos": head_plate_present_all["points_forecast"],
            "opp_points_forecast_head_present_all_combos": head_plate_present_all["opp_points_forecast"],
            "raw_value_head_present_all_combos": head_plate_present_all["raw_value"],
        })
        print(f"  Zustand {idx} (round={state['round']}, cands={n_root_candidates}): "
              f"gap_mean={per_state_results[-1]['rank1_2_gap_mean']}  "
              f"sigma_spread_mean={per_state_results[-1]['sibling_sigma_spread_mean']} "
              f"top2_margin_spread={top2_margin_spread} top2_flips={top2_flips}/8 "
              f"actual_decision_flips={state_decision_flips}/{state_decision_tracked} "
              f"(n_gaps={len(combo_gaps)}, n_sigma={len(state_sigma_spreads)})")
        print(f"    [Stufe1] plate_spread points={head_plate_spread['points_forecast']} "
              f"opp_points={head_plate_spread['opp_points_forecast']} raw_value={head_plate_spread['raw_value']} "
              f"| seed_noise points={head_seed_noise['points_forecast']} "
              f"opp_points={head_seed_noise['opp_points_forecast']} raw_value={head_seed_noise['raw_value']}")

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

    # -- Stufe 1 (PREREG_points_head_plates.md), additiv: Kennzahl je Kopf
    # (und raw_value als Pflicht-Referenz) = Median(Platten-Spannweite) /
    # Median(Seed-Rauschboden), plus Mittelwerte/n (Punkt (d) im Auftrag).
    summary["seed2"] = seed2
    heads_summary = {}
    for f in HEAD_FIELDS:
        plate_summary = summarize(all_plate_spread[f])
        noise_summary = summarize(all_seed_noise[f])
        ratio = None
        if plate_summary and noise_summary and noise_summary["median"] > 0:
            ratio = plate_summary["median"] / noise_summary["median"]
        heads_summary[f] = {
            "plate_spread_across_8_combos_fixed_seed": plate_summary,
            "seed_noise_floor_two_seeds_same_combo": noise_summary,
            "ratio_plate_spread_median_over_seed_noise_median": ratio,
            "n_states_with_head_missing_in_at_least_one_combo": len(heads_missing_states[f]),
            "states_with_head_missing": heads_missing_states[f],
        }
    summary["punktekopf_platten_stufe1"] = {
        "prereg": "evaluations/PREREG_points_head_plates.md (Stufe 1)",
        "seed_a": args.seed,
        "seed_b": seed2,
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
