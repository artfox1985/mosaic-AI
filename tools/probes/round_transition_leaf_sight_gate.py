# -*- coding: utf-8 -*-
"""Sichttor der Variante B: nimmt die Fuellung im Suchblatt NUR Steine aus
Beutel, Turm und Rundenende-Abraum, und fallen Beutel plus Turm um genau die
gezogenen Steine?

Vorregistriert in `evaluations/PREREG_round_transition_search_sampling.md`
par.10 ("Tor dazu (vorab)") und par.17.5 Punkt 2; Fahrplan Nr. 34. Die Lesart
steht DORT: **ein einziger Verstoss ist ROT**, und ROT beendet den Bau (kein
Reparaturversuch, Nutzer-Entscheid).

## Was hier gemessen wird, und was nicht

Gemessen wird die GEBAUTE Funktion `round_transition::round_transition_leaf_
state` (Wirkort des Knopfs `MOSAIC_ROUND_TRANSITION_LEAF`, par.17.2), ueber den
dafuer angelegten Diagnose-Export `mosaic_rust.round_transition_leaf_fill_diag_
json`. Nicht gemessen wird `advance_after_tiling_json`: dem fehlen der
Betrachter der Wurzel, die Mischregel `determinize_dome_pool` und der
stellungsgebundene Seed. Der Knopf selbst wird NICHT gesetzt; das Tor prueft
den Uebergang, nicht den Suchpfad.

## Die drei Kennzahlen, Schwellen VOR dem Lauf festgelegt

* **T1 Quelle (par.10, ROT-Kriterium):** die Farb-Multimenge der Fuellung ist
  enthalten in `pre_chance.bag + pre_chance.tower + pre_chance.board_leftovers`
  (Musterreihen-Reste plus Strafleiste, der "Abraum" aus par.10). Erlaubt:
  0 Verstoesse.
* **T2 Bilanz (par.10 "bag_count faellt entsprechend", ROT-Kriterium):**
  `(pre.bag + pre.tower + pre.leftovers) - (next.bag + next.tower +
  next.leftovers) == fill`, Farbe fuer Farbe. Das ist die exakte Fassung von
  "faellt entsprechend": `bag_count` ALLEIN kann legitim STEIGEN, weil
  `draw_with_refill` den Turm in den Beutel mischt, sobald der Beutel die
  volle Zahl nicht mehr liefert (`state.rs::draw_with_refill`). Erlaubt:
  0 Verstoesse.
* **T3 sichere Steine (par.10 "enthaelt alle Beutel-Steine"):** die Fuellung
  enthaelt die ganze Beutel-Multimenge des pre-chance-Zustands. KEIN
  ROT-Kriterium fuer sich, weil der Regelpfad eine legitime Ausnahme hat: der
  monochrome Redraw der grossen Manufaktur legt gezogene Steine in den Beutel
  ZURUECK und mischt neu (`state.rs`, `bag.tiles.extend(tiles)` in
  `fill_large_factory`). Die Zahl wird berichtet; Abweichungen werden je Fall
  mit Beutel-, Turm- und Abraum-Groesse ausgewiesen, damit ein Mensch
  entscheiden kann.

## Grundmenge und Einheit

Grundmenge: Blatt-Zustaende (`phase == "tiling"`) der Runden 3 und 4 mit
`bag_count` < 21 aus dem Korpus (Default `data/selfplay_v28-b02-policy_*.pkl`).
Einheit: Zustaende. Die Schranke 21 ist die Fuellmenge einer Runde (5 in der
grossen Manufaktur plus 4 x 4 in den kleinen); darunter reicht der Beutel
allein nicht, der Turm wird also sicher angezapft, und genau diese Lage prueft
par.10.

Aufruf (ohne Pipe, ohne Umleitung, CLAUDE.md):

    python -X utf8 -u tools/probes/round_transition_leaf_sight_gate.py
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

# corpus_io liegt im Projektstamm, mosaic_rust unter engine/py
# (Muster tools/probes/counterfactual_tiling_ranking.py:66-70).
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))

import corpus_io  # noqa: E402
import mosaic_rust as mr  # noqa: E402

FILL_PER_ROUND = 21  # 5 (grosse Manufaktur) + 4 x 4 (kleine), state.rs::fill_factories


def counter_minus(a: Counter, b: Counter) -> Counter:
    """a - b, NEGATIVE Reste behalten (Counter.__sub__ wirft sie weg, und genau
    die negativen Eintraege sind hier der Befund)."""
    out = Counter()
    for k in set(a) | set(b):
        d = a.get(k, 0) - b.get(k, 0)
        if d:
            out[k] = d
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--glob", default="data/selfplay_v28-b02-policy_*.pkl")
    ap.add_argument("--n", type=int, default=300, help="Zielzahl Blatt-Zustaende")
    ap.add_argument("--rounds", default="3,4")
    ap.add_argument("--max-bag", type=int, default=FILL_PER_ROUND,
                    help="nur Zustaende mit bag_count STRIKT darunter")
    ap.add_argument("--max-per-file", type=int, default=2,
                    help="je Datei UND je Runde (Muster counterfactual_tiling_ranking.py: ein "
                         "Gesamtdeckel liesse die spaete Runde verhungern, weil die Records in "
                         "Partie-Reihenfolge liegen)")
    ap.add_argument("--max-files", type=int, default=400)
    ap.add_argument("--salt-base", type=int, default=0x5163_A7E)
    ap.add_argument("--out", default="evaluations/artifacts/rt_leaf_sight_gate.json")
    a = ap.parse_args()

    if os.environ.get("MOSAIC_VOLLE_VERSORGUNG", "0").strip() not in ("", "0", "false", "False"):
        print("ABBRUCH: MOSAIC_VOLLE_VERSORGUNG ist gesetzt -- die Fabriken wuerden "
              "deterministisch aus dem Farbkreis befuellt, das Tor waere gegenstandslos "
              "(state.rs::fill_factories).", flush=True)
        return 2

    rounds = {int(x) for x in a.rounds.split(",") if x.strip()}
    files = sorted(glob.glob(str(REPO / a.glob)))[: a.max_files]
    if not files:
        print(f"ABBRUCH: kein Korpus unter {a.glob}", flush=True)
        return 2

    cfg = json.loads(mr.engine_config_json())
    print(f"Sichttor par.10 | Wheel-Kontrakt {cfg.get('contract_hash')} | "
          f"Manifest round_transition_leaf={cfg.get('round_transition_leaf')} | "
          f"{len(files)} Korpusdateien | Ziel n={a.n} | Runden {sorted(rounds)} | "
          f"bag_count < {a.max_bag}", flush=True)

    # Der Deckel gilt JE RUNDE (n/2 je Runde bei zwei Runden): die Records liegen
    # in Partie-Reihenfolge, ein Gesamtdeckel liesse die spaetere Runde leer.
    target_per_round = max(1, a.n // max(1, len(rounds)))
    used_by_round: Counter = Counter()
    scanned = 0            # Blatt-Zustaende der Runden 3/4 insgesamt gesehen
    used = 0               # davon geprueft (bag_count < Schranke)
    errors: list[dict] = []
    t1_violations: list[dict] = []
    t2_violations: list[dict] = []
    t3_exceptions: list[dict] = []
    bag_counts: list[int] = []
    tower_counts: list[int] = []
    leftover_counts: list[int] = []
    fill_sizes: list[int] = []
    bag_delta: list[int] = []
    by_round: Counter = Counter()
    t0 = time.time()
    c0 = time.process_time()

    for f in files:
        if used >= a.n:
            break
        try:
            recs = corpus_io.load_records(f)
        except Exception as exc:  # defensiv: eine kaputte Datei beendet den Lauf nicht
            errors.append({"file": os.path.basename(f), "error": f"load: {exc}"})
            continue
        per_file: Counter = Counter()
        for rec in recs:
            if used >= a.n or all(per_file[r] >= a.max_per_file for r in rounds):
                break
            st = rec.get("state") if isinstance(rec, dict) else None
            if not st or st.get("phase") != "tiling":
                continue
            rnd = int(st.get("round", 0))
            if rnd not in rounds:
                continue
            scanned += 1
            if per_file[rnd] >= a.max_per_file or used_by_round[rnd] >= target_per_round:
                continue
            if int(st.get("bag_count", 10**6)) >= a.max_bag:
                continue
            viewer = int(st.get("current_player", 0))
            salt = a.salt_base + used
            try:
                d = json.loads(mr.round_transition_leaf_fill_diag_json(
                    json.dumps(st), viewer, salt, used))
            except Exception as exc:
                errors.append({"file": os.path.basename(f), "round": st.get("round"),
                               "error": str(exc)})
                continue

            pre, nxt = d["pre_chance"], d["next"]
            sources = Counter(pre["bag"]) + Counter(pre["tower"]) + Counter(pre["board_leftovers"])
            fill = Counter(nxt["fill"])
            after = Counter(nxt["bag"]) + Counter(nxt["tower"]) + Counter(nxt["board_leftovers"])

            case = {"file": os.path.basename(f), "round": int(st["round"]),
                    "bag_count_leaf": int(st["bag_count"]),
                    "pre_bag": len(pre["bag"]), "pre_tower": len(pre["tower"]),
                    "pre_leftovers": len(pre["board_leftovers"]),
                    "fill": len(nxt["fill"]),
                    "next_bag": len(nxt["bag"]), "next_tower": len(nxt["tower"]),
                    "salt": salt}

            # T1: keine Farbe darf haeufiger in der Fuellung liegen als vorhanden.
            over = {k: v for k, v in counter_minus(fill, sources).items() if v > 0}
            if over:
                t1_violations.append({**case, "ueberschuss_je_farbe": over})

            # T2: exakte Bilanz.
            residual = counter_minus(sources, after + fill)
            if residual:
                t2_violations.append({**case, "restbetrag_je_farbe": dict(residual)})

            # T3: alle sicheren Beutel-Steine in der Fuellung.
            missing = {k: -v for k, v in counter_minus(fill, Counter(pre["bag"])).items() if v < 0}
            if missing:
                t3_exceptions.append({**case, "fehlende_beutel_steine": missing})

            bag_counts.append(len(pre["bag"]))
            tower_counts.append(len(pre["tower"]))
            leftover_counts.append(len(pre["board_leftovers"]))
            fill_sizes.append(len(nxt["fill"]))
            bag_delta.append(len(nxt["bag"]) - len(pre["bag"]))
            by_round[rnd] += 1
            used_by_round[rnd] += 1
            used += 1
            per_file[rnd] += 1
            if used % 25 == 0:
                print(f"  {used}/{a.n} Zustaende | T1 {len(t1_violations)} | "
                      f"T2 {len(t2_violations)} | T3 {len(t3_exceptions)} | "
                      f"{time.time() - t0:.0f} s", flush=True)

    wall = time.time() - t0
    cpu = time.process_time() - c0
    verdict = "GRUEN" if (used > 0 and not t1_violations and not t2_violations) else "ROT"

    def stats(xs: list[int]) -> dict:
        if not xs:
            return {"n": 0}
        return {"n": len(xs), "min": min(xs), "median": statistics.median(xs),
                "mean": round(statistics.fmean(xs), 2), "max": max(xs)}

    art = {
        "prereg": "evaluations/PREREG_round_transition_search_sampling.md par.10 (Sichttor), Fahrplan Nr. 34",
        "gemessene_funktion": "round_transition::round_transition_leaf_state "
                              "ueber mosaic_rust.round_transition_leaf_fill_diag_json",
        "verdikt": verdict,
        "n": used,
        "grundmenge": f"Blatt-Zustaende (phase=tiling) der Runden {sorted(rounds)} mit "
                      f"bag_count < {a.max_bag} aus {a.glob}",
        "einheit": "Zustaende",
        "gesehen_runden_3_4": scanned,
        "je_runde": {str(k): v for k, v in sorted(by_round.items())},
        "tore": {
            "T1_quelle_fuellung_teilmenge_von_beutel_turm_abraum": {
                "erlaubt": 0, "verstoesse": len(t1_violations), "rot_kriterium": True},
            "T2_bilanz_quellen_minus_nachher_gleich_fuellung": {
                "erlaubt": 0, "verstoesse": len(t2_violations), "rot_kriterium": True},
            "T3_alle_sicheren_beutel_steine_in_der_fuellung": {
                "abweichungen": len(t3_exceptions), "rot_kriterium": False,
                "legitime_ausnahme": "monochromer Redraw der grossen Manufaktur legt "
                                     "gezogene Steine in den Beutel zurueck "
                                     "(state.rs::fill_large_factory)"},
        },
        "verstoesse_T1": t1_violations[:20],
        "verstoesse_T2": t2_violations[:20],
        "abweichungen_T3": t3_exceptions[:20],
        "fehler": errors[:20],
        "n_fehler": len(errors),
        "verteilungen": {
            "beutel_vor_ziehung": stats(bag_counts),
            "turm_vor_ziehung": stats(tower_counts),
            "abraum_vor_ziehung": stats(leftover_counts),
            "fuellung": stats(fill_sizes),
            "bag_count_differenz_nachher_minus_vorher": stats(bag_delta),
        },
        "standard_kennzahlen": "Die sechs Kennzahlen aus CLAUDE.md (Reihen-, Spalten-, "
                               "Strafleistenauslastung, Plattenpunkte, eigene Punkte, Margin) "
                               "haben hier keine Grundmenge: das Tor spielt keine Partie, es "
                               "prueft EINEN Zufallsknoten auf Korpus-Zustaenden. Statt ihrer "
                               "stehen oben die Verteilungen der Torgroessen (Beutel, Turm, "
                               "Abraum, Fuellung). Die sechs gehoeren in den A/B (par.9, "
                               "Fahrplan Nr. 36).",
        "engine": {"contract_hash": cfg.get("contract_hash"),
                   "input_size": cfg.get("input_size"),
                   "round_transition_leaf_manifest": cfg.get("round_transition_leaf")},
        "cli_args": vars(a),
        "laufzeit": {"wanduhr_s": round(wall, 1), "cpu_s": round(cpu, 1), "threads": 1,
                     "s_je_zustand": round(wall / used, 3) if used else None},
    }
    out = REPO / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    io.open(out, "w", encoding="utf-8", newline="").write(
        json.dumps(art, ensure_ascii=False, indent=2))

    print(f"\n{verdict}: n={used} Zustaende (Grundmenge Runden {sorted(rounds)}, "
          f"bag_count < {a.max_bag}) | T1 {len(t1_violations)} | T2 {len(t2_violations)} | "
          f"T3 {len(t3_exceptions)} | Fehler {len(errors)}", flush=True)
    print(f"laufzeit: Wanduhr {wall:.1f}s, CPU {cpu:.1f}s, 1 Thread", flush=True)
    print(f"Artefakt: {out}", flush=True)
    return 0 if verdict == "GRUEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
