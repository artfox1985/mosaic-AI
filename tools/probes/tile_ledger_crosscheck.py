# -*- coding: utf-8 -*-
"""tools/probes/tile_ledger_crosscheck.py -- Fliesenbuchhaltung aus OEFFENTLICHER Information
gegen die Engine-Wahrheit (Nutzer 2026-09-13: "mach mal einen crosscheck ... ob du hier immer
reproduzieren kannst wieviel fliesen von jeder farbe zu jedem zug am brett/beutel/turm sind").

Eingang: der Zustands-Dump von `tools/analyze_game_log.py --dump-states` (eine JSON-Zeile je
Entscheidungspunkt, Feld `state` = `state_to_json`). Die Sonde benutzt daraus NUR, was ein Spieler
am Tisch sieht: Fabriken (Sonne/Mond/Pool), Musterreihen (echte Fliesen, Phantome abgezogen),
Strafleiste, belegte Kuppelfelder. NICHT benutzt werden `bag_colors`, `tower_colors`, `bag_count`:
die sind die Wahrheit, gegen die verglichen wird.

Buchhaltung je Farbe (13 Fliesen je Farbe, `docs/engine_manual.md` Z.26-28):
  sichtbar[c]   = Fabriken + Musterreihen + Strafleiste + Kuppelfelder
  im_umlauf[c]  = 13 - sichtbar[c]            (= Beutel + Turm, das kodiert der Encoder heute)
  turm[c]       = Ereignis-Ledger: am Rundenende gehen die Fliesen, die das Brett verlassen und
                  NICHT auf einem Kuppelfeld landen, in den Turm (Strafleiste, Ueberschuss
                  vollendeter Reihen, nicht platzierbare Reihen); Phantome verschwinden.
                  Nachfuellregel: reicht der Beutel fuer die naechste Fuellung nicht, wandert der
                  ganze Turm in den Beutel (`state.rs` refill_from_tower), Turm = 0.
  beutel[c]     = im_umlauf[c] - turm[c]
Verglichen wird an jedem Entscheidungspunkt: beutel und turm je Farbe gegen die Wahrheit.

Aufruf: python -X utf8 tools/probes/tile_ledger_crosscheck.py <states.jsonl> [--out artefakt.json]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

COLORS = ["blau", "gelb", "rot", "schwarz", "türkis"]  # Reihenfolge wie bag_colors (serialize.rs)
TILES_PER_COLOR = 13


def count_visible(state: dict) -> tuple[dict, dict, list[str]]:
    """Sichtbare Fliesen je Farbe: (gesamt, nur Bretter, Auffaelligkeiten)."""
    seen = {c: 0 for c in COLORS}
    boards = {c: 0 for c in COLORS}
    notes: list[str] = []

    def add(color, where: str, target: dict) -> None:
        # Mond-Stapel und Pools sind verschachtelte Listen (Stapel je Fabrik): rekursiv flach.
        if isinstance(color, list):
            for c in color:
                add(c, where, target)
            return
        if color in target:
            target[color] += 1
        else:
            notes.append(f"{where}: Nicht-Farbe {color!r}")

    for f in state.get("factories", []):
        for t in f.get("sun", []):
            add(t, f"F{f.get('id')} sun", seen)
        for t in f.get("moon", []):
            add(t, f"F{f.get('id')} moon", seen)
    lf = state.get("large_factory", {})
    for t in lf.get("sun", []):
        add(t, "GF sun", seen)
    for t in lf.get("moon", []):
        add(t, "GF moon", seen)
    for p in state.get("players", []):
        for pl in p.get("pattern_lines", []):
            real = len(pl.get("tiles", [])) - int(pl.get("phantom_count", 0))
            color = pl.get("color")
            if real > 0:
                if color in boards:
                    boards[color] += real
                else:
                    notes.append(f"Reihe {pl.get('index')}: Farbe {color!r} bei {real} echten Fliesen")
        for t in p.get("floor", []):
            add(t, "floor", boards)
        # dome_grid ist ein Gitter (Zeilen x Spalten) aus Platten oder null
        plates = [pl for row in (p.get("dome_grid") or []) for pl in (row if isinstance(row, list) else [row])]
        for plate in plates:
            if not plate:
                continue
            for sp in plate.get("spaces", []):
                filled = sp.get("filled")
                if filled is None:
                    continue
                if filled in boards:
                    boards[filled] += 1
                elif sp.get("type") == "SPECIAL":
                    pass  # Spezialfliese aus dem 9er-Vorrat, keine der 65
                else:
                    notes.append(f"Kuppelfeld: Belegung {filled!r} (Typ {sp.get('type')})")
    for c in COLORS:
        seen[c] += boards[c]
    return seen, boards, notes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    t0 = time.time()
    rows = [json.loads(line) for line in open(args.dump, encoding="utf-8") if line.strip()]
    tower = {c: 0 for c in COLORS}
    bag_prev = None  # Beutel je Farbe nach dem letzten Entscheidungspunkt (Ledger)
    prev_boards = None
    prev_round = None
    mismatches = []
    refills = []
    per_turn = []
    for r in rows:
        st = r["state"]
        seen, boards, notes = count_visible(st)
        rnd = r["round"]
        if prev_round is not None and rnd != prev_round:
            # Rundenwechsel: was die Bretter verlassen hat und nicht auf Kuppelfeldern liegt,
            # ist in den Turm gegangen (Kuppelfelder zaehlen in `boards` mit, deshalb ist die
            # Differenz genau der Turm-Zugang; Phantome sind nie in `boards`).
            for c in COLORS:
                delta = prev_boards[c] - boards[c]
                if delta < 0:
                    notes.append(f"Rundenwechsel: Brettbestand {c} gestiegen um {-delta}")
                tower[c] += max(delta, 0)
            n_fill = sum(len(f.get("sun", [])) + len(f.get("moon", [])) for f in st["factories"])
            n_fill += len(st["large_factory"].get("sun", [])) + len(st["large_factory"].get("moon", []))
            bag_before = sum(bag_prev.values())
            if bag_before < n_fill:
                refills.append({"round": rnd, "bag_before": bag_before, "fill": n_fill,
                                "tower_into_bag": sum(tower.values())})
                tower = {c: 0 for c in COLORS}
        circulation = {c: TILES_PER_COLOR - seen[c] for c in COLORS}
        bag = {c: circulation[c] - tower[c] for c in COLORS}
        truth_bag = dict(zip(COLORS, st["bag_colors"]))
        truth_tower = dict(zip(COLORS, st["tower_colors"]))
        ok = bag == truth_bag and tower == truth_tower and sum(bag.values()) == st["bag_count"]
        if not ok or notes:
            mismatches.append({"turn": r["turn"], "round": rnd, "kind": r["kind"],
                               "ledger_bag": bag, "truth_bag": truth_bag,
                               "ledger_tower": dict(tower), "truth_tower": truth_tower,
                               "bag_count_truth": st["bag_count"], "notes": notes})
        per_turn.append({"turn": r["turn"], "round": rnd, "ok": ok,
                         "bag": [bag[c] for c in COLORS], "tower": [tower[c] for c in COLORS]})
        print(f"Zug {r['turn']:3d} R{rnd} {r['kind']:15s} Beutel {[bag[c] for c in COLORS]} "
              f"Turm {[tower[c] for c in COLORS]} {'OK' if ok else 'ABWEICHUNG'}"
              + (f"  {notes}" if notes else ""), flush=True)
        bag_prev, prev_boards, prev_round = bag, boards, rnd
    n_ok = sum(1 for x in per_turn if x["ok"])
    print(f"\nErgebnis: {n_ok} von {len(per_turn)} Entscheidungspunkten stimmen in Beutel UND Turm je Farbe "
          f"mit der Engine ueberein; Nachfuellungen aus dem Turm: {refills}", flush=True)
    wand = time.time() - t0
    if args.out:
        Path(args.out).write_text(json.dumps({
            "dump": args.dump, "n_states": len(per_turn), "n_ok": n_ok, "mismatches": mismatches,
            "refills": refills, "per_turn": per_turn, "grundmenge": "Entscheidungspunkte des Dumps",
            "einheit": "Fliesen je Farbe",
            "laufzeit": {"wanduhr_s": round(wand, 3), "cpu_s": round(time.process_time(), 3),
                         "threads": 1, "s_je_zustand": round(wand / max(1, len(per_turn)), 4)},
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Artefakt: {args.out}")
    sys.exit(0 if n_ok == len(per_turn) else 1)


if __name__ == "__main__":
    main()
