# -*- coding: utf-8 -*-
"""Auswertung der Wirkungs-Probe (Arm A/B/C/E/F) -- fuer JEDE der 30 Partien
je Arm die k1/k2/k5/k6-Rohpunkte BEIDER Spieler aus dem letzten (fertigen)
Record berechnen, unabhaengig davon, ob die jeweilige Platte in der Partie
selbst gezogen wurde (end_scoring_from_state_json rechnet jedes Kriterium
aus dem fertigen dome_grid nach, siehe tools/scoring_tile_impact.py-Moduldoku)."""
import json
from pathlib import Path
import mosaic_rust as mr

BASIS = Path(__file__).resolve().parent.parent
OUT = BASIS / "data" / "corpus_probe"
TILE_IDS = [1, 2, 5, 6]
ARMS = ["A", "B", "C", "E", "F"]

print(f"{'Arm':<4}{'n':>4}" + "".join(f"{'k'+str(t)+'_p0':>10}{'k'+str(t)+'_p1':>10}" for t in TILE_IDS))
for arm in ARMS:
    sp = OUT / f"summary_wirkungsprobe_{arm}_g30.json"
    d = json.load(open(sp, encoding="utf-8"))
    sums = {t: [0.0, 0.0] for t in TILE_IDS}
    n = len(d["final_states"])
    for g in d["final_states"]:
        st = g["state"]
        out = json.loads(mr.end_scoring_from_state_json(json.dumps(st), TILE_IDS))
        for t in TILE_IDS:
            for pi in (0, 1):
                det = next(x for x in out[f"player_{pi}"]["details"] if x["id"] == t)
                sums[t][pi] += det["score"]
    row = f"{arm:<4}{n:>4}"
    for t in TILE_IDS:
        row += f"{sums[t][0]/n:>10.2f}{sums[t][1]/n:>10.2f}"
    print(row)
