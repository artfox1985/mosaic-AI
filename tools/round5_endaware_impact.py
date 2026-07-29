# -*- coding: utf-8 -*-
"""
Mosaic-AI -- Task #21 Teil 2: Auswirkung der endwertungsbewussten
Runde-5-Alpha-Beta-Blattbewertung (`round5::player_total_exact`, Toggle
`crate::tiling_solver::ROUND5_ENDSCORING_ENABLED`), 2026-07-29
============================================================================

Misst zwei Dinge auf echten Runde-5-DRAFTING-Stellungen aus
`evaluations/frozen_eval_set.pkl`, je einmal mit dem installierten Wheel im
Toggle-Zustand AUS und einmal AN (der Toggle ist ein Rust-`const`, kann also
NICHT zur Laufzeit umgeschaltet werden -- dieses Skript muss also zweimal mit
zwei unterschiedlich gebauten Wheels laufen):

1. LAUFZEIT: `mosaic_rust.net_search_state_json` routet in Runde-5-Drafting-
   Stellungen intern auf `round5::choose_action_with_analysis` (die exakte
   Alpha-Beta-Suche, `sims` wird dort ignoriert). `player_total_exact` läuft
   an JEDEM Blatt dieser Suche -- wird die endaware-Rechnung
   (`solve_round_final_score_endaware`, eigene kleine Rekursion pro Blatt)
   die Suchzeit relevant heben?
2. ZUGWECHSEL-RATE: wie oft wählt die Suche mit endaware-Bewertung
   tatsächlich eine ANDERE Aktion als ohne? Gematcht wird über die
   `description` des gewählten Zugs (stabile, reine Funktion von
   Zustand+Aktion, siehe `label_search_move` in mcts.rs), NICHT über den
   rohen `ai_action`-Index -- die Sortierung von `moves` hängt von den
   Blattwerten ab und kann sich zwischen den beiden Toggle-Zuständen selbst
   verschieben (dasselbe Vorsichtsmuster wie in
   `tools/plate_rank_invariance.py`).

ABLAUF (zwei Wheel-Builds, je ein `--phase collect`-Lauf):

    # 1) Toggle AUS (Ist-Zustand), Wheel bauen + installieren, dann:
    python tools/round5_endaware_impact.py --phase collect --label off \\
        --out-dir evaluations/round5_endaware_impact_parts

    # 2) Toggle AN setzen, Wheel neu bauen + installieren, dann:
    python tools/round5_endaware_impact.py --phase collect --label on \\
        --out-dir evaluations/round5_endaware_impact_parts

    # 3) Beide Teil-Ergebnisse zusammenführen (kein Wheel noetig):
    python tools/round5_endaware_impact.py --phase merge \\
        --out-dir evaluations/round5_endaware_impact_parts \\
        --out evaluations/round5_endaware_impact.json

`--phase collect` wählt deterministisch bis zu `--max-states` Runde-5-
Drafting-Stellungen (Reihenfolge im frozen set, gleichmäßig gesampelt) und
ruft je Stellung `net_search_state_json` mit Seed `42+index` auf (gleicher
Seed je Stellung über beide Läufe -> gepaarter Vergleich). Stellungen, bei
denen `json_to_state` scheitert (z.B. Rekonstruktions-Kanten), werden
übersprungen (gezählt, nicht als Fehler). Die LAUFZEIT-Kennzahl nutzt nur die
ersten `--runtime-states` davon (Default 10, wie in der Aufgabenstellung),
die ZUGWECHSEL-Kennzahl alle ausgewerteten (bis `--max-states`, Default 100).
"""
from __future__ import annotations

import argparse
import json
import pickle
import statistics as stats
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FROZEN_PKL = ROOT / "evaluations" / "frozen_eval_set.pkl"
DEFAULT_MODEL = "models/alphazero_v18_best.onnx"


def q(xs, p):
    if not xs:
        return float("nan")
    s = sorted(xs)
    i = (len(s) - 1) * p
    lo, hi = int(i), min(int(i) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def select_round5_drafting_states(max_states: int):
    records = pickle.loads(FROZEN_PKL.read_bytes())["records"]
    cand = [
        r["state"] for r in records
        if r["state"].get("phase") == "drafting" and int(r["state"].get("round", 0)) >= 5
    ]
    if not cand:
        raise SystemExit("Keine Runde-5-Drafting-Stellungen im frozen set.")
    step = max(1, len(cand) // max_states)
    return cand[::step][:max_states]


def phase_collect(args) -> None:
    import mosaic_rust as mr

    states = select_round5_drafting_states(args.max_states)
    print(f"{len(states)} Runde-5-Drafting-Stellungen ausgewaehlt (Label={args.label}, "
          f"Modell={args.model})")

    out_records = []
    n_skipped = 0
    for i, st in enumerate(states):
        seed = 42 + i
        t0 = time.perf_counter()
        try:
            raw = mr.net_search_state_json(json.dumps(st), args.model, 1, 1.5, seed)
        except Exception as e:  # json_to_state / Netz-Ladefehler etc. -- ueberspringen
            n_skipped += 1
            if n_skipped <= 3:
                print(f"  [skip] Stellung {i} (Runde {st.get('round')}): {e}")
            continue
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        analysis = json.loads(raw)
        ai_action = analysis.get("ai_action")
        moves = analysis.get("moves") or []
        desc = None
        if ai_action is not None and 0 <= ai_action < len(moves):
            desc = moves[ai_action].get("description")
        out_records.append({
            "index": i, "seed": seed, "round": int(st.get("round", 0)),
            "ai_action": ai_action, "num_actions": analysis.get("num_actions"),
            "chosen_description": desc, "elapsed_ms": elapsed_ms,
        })
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{len(states)} ...", flush=True)

    runtime_sample = out_records[: args.runtime_states]
    rt_ms = [r["elapsed_ms"] for r in runtime_sample]

    out = {
        "label": args.label, "model": args.model,
        "n_selected": len(states), "n_evaluable": len(out_records), "n_skipped": n_skipped,
        "runtime_sample_size": len(rt_ms),
        "runtime_median_ms": q(rt_ms, 0.5) if rt_ms else None,
        "runtime_max_ms": max(rt_ms) if rt_ms else None,
        "runtime_mean_ms": stats.mean(rt_ms) if rt_ms else None,
        "records": out_records,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / f"round5_endaware_impact_{args.label}.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nn_evaluable={len(out_records)} n_skipped={n_skipped}")
    if rt_ms:
        print(f"Laufzeit (n={len(rt_ms)}): Median {q(rt_ms,0.5):.1f}ms Max {max(rt_ms):.1f}ms")
    print(f"Geschrieben: {out_path}")


def phase_merge(args) -> None:
    off_path = args.out_dir / "round5_endaware_impact_off.json"
    on_path = args.out_dir / "round5_endaware_impact_on.json"
    if not off_path.exists() or not on_path.exists():
        raise SystemExit(
            f"Beide Teil-Ergebnisse noetig: {off_path} und {on_path} "
            "(je ein `--phase collect --label off/on`-Lauf mit dem jeweils passend "
            "gebauten Wheel)."
        )
    off = json.loads(off_path.read_text(encoding="utf-8"))
    on = json.loads(on_path.read_text(encoding="utf-8"))

    off_by_idx = {r["index"]: r for r in off["records"]}
    on_by_idx = {r["index"]: r for r in on["records"]}
    common = sorted(set(off_by_idx) & set(on_by_idx))

    n_changed = 0
    changed_examples = []
    for idx in common:
        a, b = off_by_idx[idx], on_by_idx[idx]
        if a["seed"] != b["seed"]:
            continue  # sollte bei identischem Aufbau nicht vorkommen
        if a["chosen_description"] != b["chosen_description"]:
            n_changed += 1
            if len(changed_examples) < 10:
                changed_examples.append({
                    "index": idx, "round": a["round"],
                    "off": a["chosen_description"], "on": b["chosen_description"],
                })

    def runtime_block(d):
        return {
            "sample_size": d["runtime_sample_size"],
            "median_ms": d["runtime_median_ms"],
            "max_ms": d["runtime_max_ms"],
            "mean_ms": d["runtime_mean_ms"],
        }

    off_rt, on_rt = runtime_block(off), runtime_block(on)
    ratio_median = (
        on_rt["median_ms"] / off_rt["median_ms"]
        if off_rt["median_ms"] not in (None, 0) and on_rt["median_ms"] is not None
        else None
    )
    ratio_max = (
        on_rt["max_ms"] / off_rt["max_ms"]
        if off_rt["max_ms"] not in (None, 0) and on_rt["max_ms"] is not None
        else None
    )

    result = {
        "model": off.get("model"),
        "n_selected_off": off["n_selected"], "n_selected_on": on["n_selected"],
        "n_evaluable_off": off["n_evaluable"], "n_evaluable_on": on["n_evaluable"],
        "n_skipped_off": off["n_skipped"], "n_skipped_on": on["n_skipped"],
        "runtime": {"off": off_rt, "on": on_rt,
                    "ratio_median_on_over_off": ratio_median,
                    "ratio_max_on_over_off": ratio_max},
        "move_change": {
            "n_common": len(common), "n_changed": n_changed,
            "rate": (n_changed / len(common)) if common else None,
            "examples": changed_examples,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=" * 70)
    print("  Runde-5-Alpha-Beta: endaware-Blattbewertung -- Auswirkung")
    print("=" * 70)
    print(f"  Laufzeit (n={off_rt['sample_size']}/{on_rt['sample_size']}):")
    print(f"    OFF: Median {off_rt['median_ms']:.1f}ms Max {off_rt['max_ms']:.1f}ms")
    print(f"    ON:  Median {on_rt['median_ms']:.1f}ms Max {on_rt['max_ms']:.1f}ms")
    if ratio_median is not None:
        print(f"    Verhaeltnis ON/OFF: Median x{ratio_median:.2f}, Max x{ratio_max:.2f}")
    mc = result["move_change"]
    print(f"  Zugwechsel: {mc['n_changed']}/{mc['n_common']} "
          f"({(mc['rate'] or 0):.1%})")
    print("=" * 70)
    print(f"\nErgebnis: {args.out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", choices=["collect", "merge"], required=True)
    ap.add_argument("--label", choices=["off", "on"], help="nur fuer --phase collect")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--max-states", type=int, default=100)
    ap.add_argument("--runtime-states", type=int, default=10)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "evaluations" / "round5_endaware_impact_parts")
    ap.add_argument("--out", type=Path, default=ROOT / "evaluations" / "round5_endaware_impact.json")
    args = ap.parse_args()

    if args.phase == "collect":
        if not args.label:
            raise SystemExit("--phase collect braucht --label off|on")
        phase_collect(args)
    else:
        phase_merge(args)


if __name__ == "__main__":
    main()
