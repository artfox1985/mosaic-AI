# -*- coding: utf-8 -*-
"""PREREG_special_tile_yield.md par.5(1) -- Neumessung auf hv2.

Alle par.3-Zahlen stammen aus plattenblindem Spiel; die stehende Regel
(feedback_dont_calibrate_to_plate_blind_play) verlangt die Wiedervorlage
auf dem ersten plattenbewussten Korpus. Erhoben wird je Quelle und Seite
am Endbrett (letzter Record mit winner je game_id, Muster wie
ownership_tiling_consumer_eval):

* Leer-Rate je Slot-POSITION (3x3) und je Slot-REIHE: Anteil der auf
  GELEGTEN Platten vorhandenen Spezialfelder, die am Partieende nicht
  ausgeloest sind (par.3-Vergleichsgroesse; ~84 Prozent untere Reihe,
  ~13 obere auf plattenblindem Spiel).
* Freigeschaltete Spezialfelder je Partie+Seite und ihre PUNKTSUMME
  (Ertrag = pattern_row + 1, pattern_row = slot_row*2 + sp_idx//2,
  round_end.rs:361-362).
* k6 GETRENNT (scoring_tile_points[6], nur wenn Kriterium 6 aktiv;
  Grundraten-Waechter par.5(2): k6 kann nie positiv werden, gezaehlt
  werden Anzahl und Punktsumme, nicht ein Tautologie-Anteil).

Quellen: hv2-Lehrerkorpus (300 Dateien wie par.3b.5/Stufe D) und die
b06-Messdateien (data/selfplay_otw22b06w00_*, 10 Dateien) als
Netz-Vergleich.

Aufruf (reine Datenpassage):
    python -u tools/probes/special_tile_yield_measurement.py
Smoke:
    python -u tools/probes/special_tile_yield_measurement.py --limit 2
"""
from __future__ import annotations

import argparse
import glob
import json
import pathlib
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from corpus_io import load_records  # noqa: E402

ARTIFACT = _ROOT / "evaluations" / "artifacts" / "special_tile_yield_remeasure.json"
HV2_FILES = 300  # wie par.3b.5 / Stufe D: die ersten 300 sortierten Dateien


def eval_source(pattern: str, limit: int | None):
    files = sorted(glob.glob(str(_ROOT / "data" / pattern)))
    if limit:
        files = files[:limit]
    if not files:
        return None
    pos_laid = {(r, c): 0 for r in range(3) for c in range(3)}
    pos_triggered = {(r, c): 0 for r in range(3) for c in range(3)}
    per_side_triggered = []
    per_side_points = []
    k6_points = []
    games = 0
    t0 = time.time()
    for i, f in enumerate(files):
        recs = load_records(f)
        finals = {}
        for rec in recs:
            if rec.get("winner") is not None:
                finals[rec.get("game_id")] = rec
        for rec in finals.values():
            st = rec["state"]
            games += 1
            k6_active = 6 in (st.get("scoring_tile_ids") or [])
            for p in st["players"]:
                n_trig = 0
                pts = 0
                for tr, row in enumerate(p.get("dome_grid") or []):
                    for tc, slot in enumerate(row):
                        if slot is None:
                            continue
                        for sp_idx, sp in enumerate(slot.get("spaces") or []):
                            if (sp.get("type") or "").upper() != "SPECIAL":
                                continue
                            pos_laid[(tr, tc)] += 1
                            if sp.get("filled") is not None:
                                pos_triggered[(tr, tc)] += 1
                                n_trig += 1
                                pts += tr * 2 + sp_idx // 2 + 1
                per_side_triggered.append(n_trig)
                per_side_points.append(pts)
                if k6_active:
                    stp = p.get("scoring_tile_points") or []
                    if len(stp) > 6:
                        k6_points.append(stp[6])
        if (i + 1) % 25 == 0 or i + 1 == len(files):
            print(f"  {i + 1}/{len(files)} Dateien ({time.time() - t0:.0f}s)",
                  flush=True)

    def rate(laid, trig):
        return (1 - trig / laid) if laid else None

    empty_by_pos = {f"r{r}c{c}": rate(pos_laid[(r, c)], pos_triggered[(r, c)])
                    for r in range(3) for c in range(3)}
    empty_by_row = {}
    for r in range(3):
        laid = sum(pos_laid[(r, c)] for c in range(3))
        trig = sum(pos_triggered[(r, c)] for c in range(3))
        empty_by_row[f"slot_row_{r}"] = {
            "gelegt": laid, "ausgeloest": trig, "leer_rate": rate(laid, trig)}
    n = len(per_side_triggered)
    return {
        "dateien": len(files), "partien": games, "seiten": n,
        "leer_rate_je_position": empty_by_pos,
        "leer_rate_je_slot_reihe": empty_by_row,
        "ausgeloeste_spezialfelder_je_seite": sum(per_side_triggered) / n,
        "spezial_punkte_je_seite": sum(per_side_points) / n,
        "k6_punkte_je_seite_wenn_aktiv": (sum(k6_points) / len(k6_points))
                                          if k6_points else None,
        "k6_seiten_mit_aktivem_k6": len(k6_points),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--limit", type=int, default=None,
                    help="nur die ersten N Dateien je Quelle (Smoke)")
    args = ap.parse_args()
    t0 = time.time()

    result = {"prereg": "PREREG_special_tile_yield.md par.5(1)",
              "quellen": {}}
    for name, pattern, limit in (
            ("hv2_lehrer", "selfplay_hv2_*.pkl", args.limit or HV2_FILES),
            ("v22_b06", "selfplay_otw22b06w00_*.pkl", args.limit)):
        print(f"Quelle {name}:", flush=True)
        r = eval_source(pattern, limit)
        if r is None:
            print(f"  keine Dateien fuer {pattern}", flush=True)
            continue
        result["quellen"][name] = r

    result["laufzeit"] = {"wanduhr_s": round(time.time() - t0, 1),
                          "cpu_s": None, "threads": 1, "s_je_partie": None}
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(result, indent=1, ensure_ascii=False),
                        encoding="utf-8", newline="\n")
    print(f"\nArtefakt geschrieben: {ARTIFACT}", flush=True)
    for name, r in result["quellen"].items():
        rows = r["leer_rate_je_slot_reihe"]
        print(f"{name}: leer oben {rows['slot_row_0']['leer_rate']:.3f} / "
              f"mitte {rows['slot_row_1']['leer_rate']:.3f} / "
              f"unten {rows['slot_row_2']['leer_rate']:.3f} | "
              f"ausgeloest/Seite {r['ausgeloeste_spezialfelder_je_seite']:.2f} | "
              f"Punkte/Seite {r['spezial_punkte_je_seite']:.2f} | "
              f"k6 {r['k6_punkte_je_seite_wenn_aktiv']}", flush=True)


if __name__ == "__main__":
    main()
