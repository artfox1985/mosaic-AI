# -*- coding: utf-8 -*-
"""Sperre par.5 von PREREG_reachability_target.md: traegt das Vollendbarkeits-Label?

Der Zielwechsel von REALISIERUNG auf VOLLENDBARKEIT hat ein Spiegelbild-Risiko:
ist in den fruehen Runden fast jede Geometrie noch vollendbar, ist das Label
nahezu konstant und traegt so wenig Information wie "wird nicht fertig" am
anderen Ende.

VORAB-REGEL (par.5): die Positivrate muss fuer k1 UND k2 in mindestens DREI der
fuenf Runden zwischen 5 % und 95 % liegen. Sonst wird der Zielwechsel in dieser
Form nicht gebaut.

Granularitaet ist das ATOM, nicht die Stellung -- der Kopf lernt je Geometrie
(6 Spalten-Atome, 2 Diagonalen-Atome), also wird ueber (Stellung x Geometrie)
gezaehlt. Die "irgendeine"-Rate kommt als Kontext mit.

Label-Quelle ist `mosaic_rust.plate_completability_json` (Wrapper um
`column_build::column_is_completable`, Vorrat aus
`provocation::still_reachable_colors` -- nur beobachtbare Information).
"""
from __future__ import annotations

import argparse
import glob
import json
import pickle
import sys
from collections import defaultdict
from pathlib import Path

BASIS = Path(__file__).resolve().parents[2]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--states", default="data/holdout/*.pkl")
    ap.add_argument("--n-per-round", type=int, default=150)
    ap.add_argument("--phase", default="tiling")
    a = ap.parse_args()

    import mosaic_rust as mr  # noqa: PLC0415

    # je (Partie, Runde) EINE Stellung -- gegen die Pseudoreplikation, die in
    # dieser Messreihe schon dreimal ein Ergebnis entwertet hat
    zaehler: dict = defaultdict(lambda: {"sp_pos": 0, "sp_n": 0, "di_pos": 0, "di_n": 0,
                                         "sp_any": 0, "di_any": 0, "st": 0})
    gesehen: dict = {}
    genug: dict = defaultdict(int)
    for f in sorted(glob.glob(str(BASIS / a.states))):
        try:
            data = pickle.load(open(f, "rb"))
        except Exception:  # noqa: BLE001
            continue
        for s in data:
            st = s.get("state") or {}
            if st.get("phase") != a.phase:
                continue
            rd = int(st.get("round") or 0)
            if not 1 <= rd <= 5 or genug[rd] >= a.n_per_round:
                continue
            g = (f, s.get("game_id"), rd)
            if gesehen.get(g):
                continue
            gesehen[g] = True
            pi = st.get("current_player", 0)
            try:
                d = json.loads(mr.plate_completability_json(json.dumps(st), pi))
            except Exception:  # noqa: BLE001
                continue
            genug[rd] += 1
            z = zaehler[rd]
            z["st"] += 1
            z["sp_pos"] += sum(1 for x in d["columns"] if x)
            z["sp_n"] += len(d["columns"])
            z["di_pos"] += sum(1 for x in d["diagonals"] if x)
            z["di_n"] += len(d["diagonals"])
            z["sp_any"] += 1 if any(d["columns"]) else 0
            z["di_any"] += 1 if any(d["diagonals"]) else 0
        if all(genug[r] >= a.n_per_round for r in range(1, 6)):
            break

    print(f"  Phase '{a.phase}', je (Partie, Runde) eine Stellung\n")
    print("  Runde |   n | k1 Spalten-Atome | k2 Diagonalen-Atome | irgendeine Spalte | irgendeine Diag.")
    print("  ------+-----+------------------+---------------------+-------------------+-----------------")
    erg = {}
    for rd in sorted(zaehler):
        z = zaehler[rd]
        sp = z["sp_pos"] / max(z["sp_n"], 1)
        di = z["di_pos"] / max(z["di_n"], 1)
        erg[rd] = {"n": z["st"], "k1": sp, "k2": di,
                   "k1_any": z["sp_any"] / max(z["st"], 1),
                   "k2_any": z["di_any"] / max(z["st"], 1)}
        print(f"  {rd:5} | {z['st']:3} |      {100*sp:6.1f} %    |       {100*di:6.1f} %      |"
              f"      {100*erg[rd]['k1_any']:6.1f} %     |     {100*erg[rd]['k2_any']:6.1f} %")

    def im_band(x):
        return 0.05 <= x <= 0.95

    k1_ok = sum(1 for r in erg if im_band(erg[r]["k1"]))
    k2_ok = sum(1 for r in erg if im_band(erg[r]["k2"]))
    print(f"\n  Runden im Band 5-95 %:  k1 {k1_ok}/5   k2 {k2_ok}/5   (Vorabregel: je >= 3)")
    bestanden = k1_ok >= 3 and k2_ok >= 3
    print(f"  VORABREGEL par.5: {'BESTANDEN' if bestanden else 'NICHT BESTANDEN'}")
    print("  Bezug: Realisierungsrate k1 heute ~13 % (20 Spalten in 156 Partien)")

    (BASIS / "evaluations" / "probe_reachability_base_rate.json").write_text(json.dumps({
        "states": a.states, "phase": a.phase, "je_runde": erg,
        "k1_runden_im_band": k1_ok, "k2_runden_im_band": k2_ok,
        "bestanden": bestanden,
    }, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
