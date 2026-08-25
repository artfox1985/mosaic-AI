# -*- coding: utf-8 -*-
"""
Mosaic-AI -- Wertungsplatten-Diagnose, Teil 3: Policy-/Value-Sensitivitaet
(2026-07-26)
============================================================================

Fragestellung: reagiert das Netz (Policy + Root-Value) auf einem FESTEN
Brettzustand ueberhaupt auf unterschiedliche Wertungsplatten-Kombinationen,
oder "ignoriert" es sie (Nutzer-Verdacht)?

Methodik
--------
Nimmt echte Drafting-Zustaende aus `evaluations/frozen_eval_set.pkl`, haelt
ALLES fix ausser `state["scoring_tile_ids"]`, und laesst `net_search_state_
json` (Task #89, bereits installiertes Wheel) mit mehreren unterschiedlichen
gueltigen 3er-Wertungsplatten-Kombinationen ueber DENSELBEN Zustand laufen
(fester `sims`/`c_puct`, `model_path` = amtierender Champion).

Da Wertungsplatten NUR die Endwertung betreffen, nicht die Zug-Legalitaet
(siehe `scoring.rs`/`validation.rs` -- keine Wertungsplatten-Abhaengigkeit in
der Zuggenerierung), ist die Kandidatenliste (`action_id`-Menge) fuer JEDE
Kombination auf demselben Zustand identisch -- Angleichung ist daher trivial
(kein "fehlende Kandidaten = 0 Masse"-Sonderfall noetig, aber der Code
behandelt es defensiv trotzdem so, falls sich das je aendert).

Baseline-Rauschen vs. Wertungsplatten-Effekt
---------------------------------------------
`net_search_state_json` ist bei festem `seed` deterministisch (kein
Root-Rauschen, `add_root_noise=false`) -- ein Vergleich derselben Kombination
mit sich selbst waere trivial 0. Der `seed`-Parameter treibt aber zusaetzlich
die Neumischung der ECHT verdeckten Information (Beutel/Turm/Kuppelstapel/
Bonusplaettchen-Pool, siehe `serialize::json_to_state`-Doku) UND die
`DETERMINIZE_ROOT_HIDDEN_INFO`-Determinisierung der Suche selbst -- das ist
die einzige Rausch-Quelle, die bei identischer Wertungsplatten-Kombination
zu unterschiedlichen Policies fuehrt, und dient hier als "Baseline-Rauschen"
(zwei Seeds, gleiche Kombination). Der Wertungsplatten-EFFEKT wird bei
FESTEM Seed gemessen (gleiche Determinisierung, nur die Kombination
unterscheidet sich) -- das isoliert den Effekt von diesem Rauschen.

Divergenz-Mass: symmetrische Jensen-Shannon-Divergenz (Bits) ueber die
MCTS-Besuchsverteilung (`mcts_visits`, normalisiert) der Wurzelkandidaten,
nach `action_id` ausgerichtet. ZUSAETZLICH wird dieselbe Divergenz auch ueber
den ROHEN Policy-Prior (`net_prob`, VOR jeder Suche) gemessen
(`raw_prior_js_vs_reference`): das Projekt nutzt an der Wurzel "Gumbel
AlphaZero" (Danihelka/Guez/Schrittwieser/Silver, ICLR 2022; siehe
`net_mcts.rs`, Abschnitt "Gumbel AlphaZero") -- Gumbel-Top-m + Sequential
Halving statt klassischem PUCT. Bei `add_root_noise=false` (wie hier, siehe
`net_search_state_json`-Doku in `lib.rs`) sind die echten Gumbel-Samples
abgeschaltet (`gumbel_scale=0`), die Top-m-Auswahl faellt dann auf reines
Ranking nach Log-Prior zurueck. Ein VERSCHOBENER, aber RANG-GLEICHER Prior
kann die `mcts_visits`-Verteilung daher UNVERAENDERT lassen, obwohl der
Policy-Head selbst klar reagiert hat -- `raw_prior_js_vs_reference` deckt
genau diesen Fall auf (siehe Ergebnis-Diskussion in
`evaluations/STATUS.md`).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import pickle
import statistics as stats

import mosaic_rust

MUTUALLY_EXCLUSIVE_PAIRS = [(0, 7), (6, 3), (4, 1), (2, 5)]


def all_valid_combos():
    """Alle gueltigen 3er-Kombinationen: 3 der 4 Ausschluss-Paare liefern
    genau 1 Seite, das vierte Paar liefert keine (siehe scoring.rs)."""
    from itertools import combinations, product

    combos = set()
    for chosen_pairs in combinations(range(4), 3):
        sides = [MUTUALLY_EXCLUSIVE_PAIRS[i] for i in chosen_pairs]
        for pick in product(*sides):
            combos.add(tuple(sorted(pick)))
    return sorted(combos)


def pick_representative_combos(n=8, seed_offset=0):
    """Deterministische, ueber alle 4 "ausgelassenes Paar"-Faelle gestreute
    Auswahl von `n` Kombinationen aus den (bei 4 Paaren) 32 gueltigen."""
    combos = all_valid_combos()
    assert len(combos) == 32, f"erwartet 32 gueltige Kombinationen, war {len(combos)}"
    step = max(1, len(combos) // n)
    chosen = [combos[(i * step + seed_offset) % len(combos)] for i in range(n)]
    # Duplikate entfernen, ggf. mit weiteren aus der Liste auffuellen.
    seen = []
    for c in chosen:
        if c not in seen:
            seen.append(c)
    i = 0
    while len(seen) < n and i < len(combos):
        if combos[i] not in seen:
            seen.append(combos[i])
        i += 1
    return seen[:n]


def policy_vector(moves, action_ids):
    """MCTS-Besuchsverteilung (normalisiert) je `action_id`, 0 fuer fehlende
    Kandidaten (sowohl komplett abwesende `action_id`s als auch Kandidaten
    mit `mcts_visits: null` -- bei sims=400 und > ~6 Kandidaten bleiben
    manche Wurzelkinder unbesucht, `null` statt `0` serialisiert; beides
    bedeutet "0 Besuche")."""
    visits = {m["action_id"]: (m["mcts_visits"] or 0) for m in moves}
    total = sum(visits.values())
    if total == 0:
        return {a: 0.0 for a in action_ids}
    return {a: visits.get(a, 0) / total for a in action_ids}


def raw_prior_vector(moves, action_ids):
    """Roher Netz-Policy-Prior (`net_prob`, VOR jeder Suche) je `action_id`,
    normalisiert -- misst, ob der Policy-HEAD selbst auf die Wertungsplatten-
    Kombination reagiert, unabhaengig davon, ob sich das auch in der
    Gumbel-Top-m-/Sequential-Halving-Suchausgabe (`mcts_visits`) niederschlaegt
    (siehe Modul-Doku: bei `add_root_noise=false` waehlt die Wurzel rein nach
    RANG des Log-Priors, nicht nach dessen Magnitude -- ein Magnitude-Shift
    ohne Rang-Wechsel bleibt in `mcts_visits` unsichtbar)."""
    priors = {m["action_id"]: (m["net_prob"] or 0.0) for m in moves}
    total = sum(priors.values())
    if total == 0:
        return {a: 0.0 for a in action_ids}
    return {a: priors.get(a, 0.0) / total for a in action_ids}


def js_divergence_bits(p: dict, q: dict) -> float:
    """Symmetrische Jensen-Shannon-Divergenz in Bits ueber gemeinsame Keys."""
    keys = set(p) | set(q)

    def kl(a, b):
        s = 0.0
        for k in keys:
            pa = a.get(k, 0.0)
            pb = b.get(k, 0.0)
            if pa <= 0:
                continue
            # b(k)==0 waere bei m=(a+b)/2 nie 0, solange a(k)>0 -- sicher.
            s += pa * math.log2(pa / pb)
        return s

    m = {k: 0.5 * (p.get(k, 0.0) + q.get(k, 0.0)) for k in keys}
    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def run_search(state, tile_ids, model_path, sims, c_puct, seed):
    s = dict(state)
    s["scoring_tile_ids"] = list(tile_ids)
    out = mosaic_rust.net_search_state_json(json.dumps(s), model_path, sims, c_puct, seed)
    return json.loads(out)


def select_states(records, n_states, rng_seed=7):
    """Waehlt `n_states` Drafting-Zustaende, ueber Runden gestreut (fuer
    Robustheit -- nicht nur eine Spielphase)."""
    import random

    by_round = {}
    for i, r in enumerate(records):
        if r["state"]["phase"] != "drafting":
            continue
        by_round.setdefault(r["state"]["round"], []).append((i, r))
    rng = random.Random(rng_seed)
    chosen = []
    rounds = sorted(by_round.keys())
    per_round = max(1, n_states // max(1, len(rounds)))
    chosen_idxs = set()
    for rnd in rounds:
        pool = by_round[rnd]
        k = min(per_round, len(pool))
        for i, r in rng.sample(pool, k):
            chosen.append((i, r))
            chosen_idxs.add(i)
    if len(chosen) < n_states:
        remaining = [(i, r) for rnd in rounds for (i, r) in by_round[rnd] if i not in chosen_idxs]
        rng.shuffle(remaining)
        chosen.extend(remaining[: n_states - len(chosen)])
    return chosen[:n_states]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-set", default="evaluations/frozen_eval_set.pkl")
    ap.add_argument("--model", default="models/alphazero_v16_best.onnx")
    ap.add_argument("--sims", type=int, default=400)
    ap.add_argument("--c-puct", type=float, default=1.5)
    ap.add_argument("--n-states", type=int, default=16)
    ap.add_argument("--n-combos", type=int, default=8)
    ap.add_argument("--out", default="evaluations/artifacts/scoring_tile_sensitivity_result.json")
    args = ap.parse_args()

    with open(args.eval_set, "rb") as f:
        data = pickle.load(f)
    records = data["records"]
    states = select_states(records, args.n_states)
    print(f"[scoring_tile_sensitivity] {len(states)} Zustaende gewaehlt "
          f"(Runden: {sorted(set(r['state']['round'] for _, r in states))})")

    combos = pick_representative_combos(args.n_combos)
    print(f"[scoring_tile_sensitivity] {len(combos)} Kombinationen: {combos}")

    per_state_results = []
    all_baseline_js = []
    all_treatment_js = []
    all_baseline_value_diff = []
    all_treatment_value_spread = []
    all_treatment_raw_prior_js = []

    for idx, (record_index, rec) in enumerate(states):
        state = rec["state"]
        original_ids = tuple(sorted(state["scoring_tile_ids"]))
        combos_for_state = [c for c in combos if c != original_ids] or combos[:]
        combos_for_state = [original_ids] + combos_for_state  # Referenz zuerst

        # -- Baseline-Rauschen: gleiche (originale) Kombination, 2 Seeds --
        out_seed_a = run_search(state, original_ids, args.model, args.sims, args.c_puct, seed=1000)
        out_seed_b = run_search(state, original_ids, args.model, args.sims, args.c_puct, seed=2000)
        moves_a, moves_b = out_seed_a["moves"], out_seed_b["moves"]
        if not moves_a or not moves_b:
            print(f"  Zustand {idx} (round={state['round']}): keine Wurzelkandidaten (Phase-Randfall), uebersprungen")
            continue
        action_ids = sorted({m["action_id"] for m in moves_a} | {m["action_id"] for m in moves_b})
        p_a = policy_vector(moves_a, action_ids)
        p_b = policy_vector(moves_b, action_ids)
        baseline_js = js_divergence_bits(p_a, p_b)
        rv_a, rv_b = out_seed_a.get("root_value"), out_seed_b.get("root_value")
        baseline_value_diff = abs(rv_a - rv_b) if rv_a is not None and rv_b is not None else None
        all_baseline_js.append(baseline_js)
        if baseline_value_diff is not None:
            all_baseline_value_diff.append(baseline_value_diff)

        # -- Behandlung: fester Seed (=1000, wie out_seed_a), variierende Kombination --
        combo_results = []
        values_fixed_seed = [out_seed_a.get("root_value")]
        ref_moves = moves_a
        ref_action_ids = {m["action_id"] for m in ref_moves}
        for combo in combos_for_state:
            if combo == original_ids:
                continue
            out_c = run_search(state, combo, args.model, args.sims, args.c_puct, seed=1000)
            moves_c = out_c["moves"]
            if not moves_c:
                continue
            combo_action_ids = {m["action_id"] for m in moves_c}
            if combo_action_ids != ref_action_ids:
                print(f"    WARNUNG Zustand {idx}: Kandidatenmenge weicht bei Kombination {combo} ab "
                      f"({combo_action_ids} vs {ref_action_ids}) -- Wertungsplatten sollten Legalitaet "
                      f"NICHT beeinflussen, wird trotzdem ausgerichtet (0-Masse fuer fehlende).")
            aligned_ids = sorted(ref_action_ids | combo_action_ids)
            p_ref = policy_vector(ref_moves, aligned_ids)
            p_c = policy_vector(moves_c, aligned_ids)
            js = js_divergence_bits(p_ref, p_c)
            # Zusaetzlich: roher Policy-Prior VOR der Suche (siehe raw_prior_vector-
            # Doku) -- unterscheidet "Policy-Head reagiert nicht" von "Policy-Head
            # reagiert, aber Gumbel-Rang-Auswahl aendert sich dadurch nicht".
            prior_ref = raw_prior_vector(ref_moves, aligned_ids)
            prior_c = raw_prior_vector(moves_c, aligned_ids)
            raw_prior_js = js_divergence_bits(prior_ref, prior_c)
            v = out_c.get("root_value")
            values_fixed_seed.append(v)
            combo_results.append({
                "combo": list(combo), "js_vs_reference": js,
                "raw_prior_js_vs_reference": raw_prior_js, "root_value": v,
            })
            all_treatment_js.append(js)
            all_treatment_raw_prior_js.append(raw_prior_js)

        non_null_values = [v for v in values_fixed_seed if v is not None]
        value_spread = (max(non_null_values) - min(non_null_values)) if len(non_null_values) >= 2 else None
        if value_spread is not None:
            all_treatment_value_spread.append(value_spread)

        per_state_results.append({
            "state_index_in_eval_set": record_index,
            "round": state["round"],
            "original_scoring_tile_ids": list(original_ids),
            "n_root_candidates": len(ref_moves),
            "baseline_js_two_seeds_same_combo": baseline_js,
            "baseline_root_value_diff_two_seeds": baseline_value_diff,
            "root_value_original_seed1000": out_seed_a.get("root_value"),
            "combo_results_fixed_seed1000": combo_results,
            "value_spread_across_combos_fixed_seed": value_spread,
        })
        raw_prior_mean = stats.mean([c["raw_prior_js_vs_reference"] for c in combo_results]) if combo_results else float("nan")
        print(f"  Zustand {idx} (round={state['round']}, cands={len(ref_moves)}): "
              f"baseline_JS={baseline_js:.4f}  treatment_JS_visits(mean)={stats.mean([c['js_vs_reference'] for c in combo_results]) if combo_results else float('nan'):.4f}  "
              f"treatment_JS_raw_prior(mean)={raw_prior_mean:.4f}  value_spread={value_spread}")

    def summarize(vals):
        vals = [v for v in vals if v is not None]
        if not vals:
            return None
        return {
            "n": len(vals), "mean": stats.mean(vals), "median": stats.median(vals),
            "stdev": stats.pstdev(vals) if len(vals) > 1 else 0.0,
            "min": min(vals), "max": max(vals),
        }

    summary = {
        "model": args.model,
        "sims": args.sims,
        "c_puct": args.c_puct,
        "n_states": len(per_state_results),
        "n_combos_tested_per_state": args.n_combos,
        "baseline_js_same_combo_diff_seed": summarize(all_baseline_js),
        "treatment_js_diff_combo_same_seed": summarize(all_treatment_js),
        "treatment_raw_prior_js_diff_combo_same_seed": summarize(all_treatment_raw_prior_js),
        "baseline_root_value_diff_two_seeds": summarize(all_baseline_value_diff),
        "treatment_value_spread_across_combos": summarize(all_treatment_value_spread),
    }

    b = summary["baseline_js_same_combo_diff_seed"]
    t = summary["treatment_js_diff_combo_same_seed"]
    if b and t and b["mean"] > 0:
        summary["effect_over_baseline_ratio_mean"] = t["mean"] / b["mean"]
    print("\n=== ZUSAMMENFASSUNG ===")
    print(json.dumps(summary, indent=2, ensure_ascii=True))

    result = {"summary": summary, "per_state": per_state_results}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nErgebnis geschrieben nach {args.out}")


if __name__ == "__main__":
    main()
