# -*- coding: utf-8 -*-
"""Deckungs-Bericht des Ownership-Korpus (PREREG_ownership_corpus.md §2):
Positiv-Zahlen je Kriterium und Spielerseite, je Arm — mit EXAKT den
Label-Bauern des Trainings (_conjunctions_from_dome/_ownership_from_dome)."""
import glob
import json
import pickle
import sys
from collections import defaultdict
from pathlib import Path

B = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(B))                 # config.py (Wurzel)
sys.path.insert(0, str(B / "engine" / "py"))
from neural_net import _conjunctions_from_dome, _ownership_from_dome  # noqa: E402

ARME = [
    ("heur_own", "D Heuristik"),
    ("v21_own_a", "A Netz+Streuung"),
    ("v21_own_k1", "B Spaltenbau"),
    ("v21_own_k2", "C Diagonalen"),
    ("v21_own_k5", "E Eckenpaar"),
    ("v21_own_k6", "F Spezialbauer"),
]
GRUPPEN = [
    ("zeilen_voll (k0, +3)", range(0, 6)),
    ("SPALTEN_voll (k1, +7)", range(6, 12)),
    ("diagonalen (k2, +10)", range(12, 14)),
    ("ecken_3er (k5)", range(14, 16)),
    ("ecken_8er (k5)", range(16, 18)),
    ("alle_joker (k3)", range(18, 19)),
    ("farbreihen (k7, +4)", range(19, 25)),
]

bericht = {}
for prefix, name in ARME:
    dateien = sorted(glob.glob(str(B / "data" / "ownership_corpus" / f"selfplay_{prefix}_*.pkl")))
    spiele, unvollstaendig = 0, 0
    # je Gruppe und Seite: [Partien mit >=1 Einheit, Summe Einheiten]
    agg = {g: {0: [0, 0], 1: [0, 0]} for g, _ in GRUPPEN}
    offene_specials = {0: 0, 1: 0}
    for pf in dateien:
        with open(pf, "rb") as f:
            data = pickle.load(f)
        last_by_gid = {}
        for step in data:
            last_by_gid[step["game_id"]] = step
        for gid, last in last_by_gid.items():
            if not last.get("completed"):
                unvollstaendig += 1
                continue
            spiele += 1
            players = last["state"]["players"]
            for pi in (0, 1):
                grid = players[pi]["dome_grid"]
                conj = _conjunctions_from_dome(grid)
                for g, idx in GRUPPEN:
                    n = sum(conj[i] for i in idx)
                    if n:
                        agg[g][pi][0] += 1
                    agg[g][pi][1] += n
                # offene Spezialfelder direkt aus dem Grid (Platte 6, -3 je offen)
                offen = 0
                for sr in range(3):
                    for sc in range(3):
                        slot = grid[sr][sc] if sr < len(grid) and sc < len(grid[sr]) else None
                        for sp in ((slot or {}).get("spaces", []) if slot else []):
                            if sp.get("type") not in ("N", "WILD", "NORMAL", None) and sp.get("filled") is None:
                                offen += 1
                offene_specials[pi] += offen
    e = {"spiele": spiele, "unvollstaendig": unvollstaendig,
         "gruppen": {g: {"p0": agg[g][0], "p1": agg[g][1]} for g, _ in GRUPPEN},
         "offene_specials_mittel": {p: (offene_specials[p] / spiele if spiele else None) for p in (0, 1)}}
    bericht[name] = e
    print(f"\n== {name}: {spiele} Partien ({unvollstaendig} unvollstaendig) ==")
    for g, _ in GRUPPEN:
        a0, a1 = agg[g][0], agg[g][1]
        print(f"  {g:<24} p0: {a0[0]:>4} Partien / {a0[1]:>5} Einheiten | "
              f"p1: {a1[0]:>4} / {a1[1]:>5}")
    print(f"  offene Spezialfelder Ø   p0: {offene_specials[0]/spiele:.2f} | p1: {offene_specials[1]/spiele:.2f}")

aus = B / "evaluations" / "artifacts" / "ownership_corpus_coverage_report.json"
aus.write_text(json.dumps(bericht, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"\nBericht -> {aus}")
