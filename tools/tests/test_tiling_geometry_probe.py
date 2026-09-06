# -*- coding: utf-8 -*-
"""Reine Python-Logik der Reihen-Alter-Sonde (tools/probes/tiling_geometry_probe.py,
PREREG_geometric_envelope.md par.8.13/8.14): Praedikat ja / ja_wartend / nein,
Aussen-Legen-Flag, Episoden ueber Rundenenden, Klassifikation der Enden am
Zellgewinn (Fassung 2), Zusammenfassung. Ohne Engine, ohne Korpus."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "probes"))
sys.path.insert(0, str(REPO / "tools"))
import tiling_geometry_probe as tg  # noqa: E402
import triangle_hull_coverage_probe as hull  # noqa: E402


def sp(kind, color=None, filled=None, locked=False):
    return {"type": kind, "color": color, "filled": filled, "locked": locked}


def line(i, color, k):
    return {"index": i, "capacity": i + 1, "tiles": [color] * k, "color": color if k else None, "phantom_count": 0}


def player(grid, rows):
    lines = [line(i, None, 0) for i in range(6)]
    for i, (c, k) in rows.items():
        lines[i] = line(i, c, k)
    return {"dome_grid": grid, "pattern_lines": lines}


# Platte Design 0 (dome.rs): gelb, schwarz, tuerkis, Spezial -- im Slot (2,0), also Rasterzellen
# (4,0) gelb, (4,1) schwarz, (5,0) tuerkis, (5,1) Spezialfeld.
TILE0 = {"id": 0, "bonus": 3, "spaces": [sp("NORMAL", "gelb"), sp("NORMAL", "schwarz"), sp("NORMAL", "türkis"), sp("SPECIAL", locked=True)]}


def base_state():
    grid0 = [[None, None, None], [None, None, None], [TILE0, None, None]]
    return {"round": 1, "dome_display": [], "pending_stack_draw": [], "dome_pool_mask": [1] * 18,
            "players": [player(grid0, {4: ("blau", 3), 5: ("türkis", 2)}),
                        player([[None] * 3 for _ in range(3)], {4: ("rot", 1)})]}


META = {"quelle": "test", "names": ["Mensch", "KI"]}


class RowPredicate(unittest.TestCase):
    def test_no_accepting_and_no_free_hull_cell_is_nein(self):
        st = base_state()
        h = hull.best_hull(hull.occupancy(st["players"][0]["dome_grid"]))
        self.assertEqual(tg.row_predicate(st, 0, 4, "blau", h)["pred"], "nein")

    def test_accepting_hull_cell_is_ja(self):
        st = base_state()
        h = hull.best_hull(hull.occupancy(st["players"][0]["dome_grid"]))
        self.assertEqual(tg.row_predicate(st, 0, 5, "türkis", h)["pred"], "ja")

    def test_free_hull_cell_with_tile_in_pool_is_ja_wartend(self):
        st = base_state()
        self.assertEqual(tg.row_predicate(st, 1, 4, "rot", hull.HULL_LEFT)["pred"], "ja_wartend")
        st["dome_pool_mask"] = [0] * 18
        self.assertEqual(tg.row_predicate(st, 1, 4, "rot", hull.HULL_LEFT)["pred"], "nein")
        st["dome_display"] = [{"id": 13, "bonus": 0, "spaces": [sp("NORMAL", "rot"), sp("NORMAL", "türkis"), sp("NORMAL", "gelb"), sp("WILD")]}]
        self.assertEqual(tg.row_predicate(st, 1, 4, "rot", hull.HULL_LEFT)["pred"], "ja_wartend")

    def test_outside_cell_accepting_sets_flag(self):
        st = base_state()
        st["players"][0]["dome_grid"][2][2] = {"id": 1, "bonus": 0, "spaces": [sp("WILD"), sp("NORMAL", "blau"), sp("NORMAL", "türkis"), sp("NORMAL", "schwarz")]}
        h = hull.best_hull(hull.occupancy(st["players"][0]["dome_grid"]))
        p = tg.row_predicate(st, 0, 4, "blau", h)
        self.assertEqual(p["pred"], "nein")
        self.assertTrue(p["annehmend_ausserhalb"])

    def test_unknown_color_is_unbekannt(self):
        self.assertEqual(tg.row_predicate(base_state(), 0, 4, "bunt", hull.HULL_LEFT)["pred"], "unbekannt")


class Episodes(unittest.TestCase):
    def run_three_rounds(self):
        ctx, eps = {}, []
        st1 = base_state()
        tg.track_row_ages(st1, 1, ctx, eps, META)
        st2 = copy.deepcopy(st1); st2["round"] = 2; st2["players"][0]["pattern_lines"][4] = line(4, "blau", 5)
        tg.track_row_ages(st2, 2, ctx, eps, META)
        st3 = copy.deepcopy(st2); st3["round"] = 3
        st3["players"][0]["pattern_lines"][4] = line(4, "gelb", 2)
        st3["players"][1]["pattern_lines"][4] = line(4, "rot", 4)
        tg.track_row_ages(st3, 3, ctx, eps, META)
        final = copy.deepcopy(st3)
        final["players"][1]["dome_grid"][2][0] = {"id": 13, "bonus": 0, "spaces": [sp("NORMAL", "rot", filled="rot"), sp("NORMAL", "türkis"), sp("NORMAL", "gelb"), sp("WILD")]}
        tg.close_row_ages(ctx, eps, 3, final)
        return eps

    def test_episode_ends_and_ages(self):
        eps = self.run_three_rounds()
        self.assertEqual(len(eps), 4)
        blau = next(e for e in eps if e["color"] == "blau")
        self.assertEqual((blau["ende"], blau["rundenenden"], blau["blockiert_rundenenden"]), ("voll_geraeumt", 2, 1))
        gelb = next(e for e in eps if e["color"] == "gelb")
        self.assertEqual((gelb["ende"], gelb["start_runde"]), ("offen_am_ende", 3))
        rot = next(e for e in eps if e["color"] == "rot")
        self.assertEqual((rot["ende"], rot["rundenenden"]), ("chip_gelegt", 3))

    def test_full_row_with_cell_gain_is_voll_gelegt(self):
        ctx, eps = {}, []
        a1 = base_state(); a1["players"][0]["pattern_lines"][5] = line(5, "türkis", 6)
        tg.track_row_ages(a1, 1, ctx, eps, META)
        a2 = copy.deepcopy(a1); a2["round"] = 2; a2["players"][0]["pattern_lines"][5] = line(5, None, 0)
        a2["players"][0]["dome_grid"][2][0]["spaces"][2]["filled"] = "türkis"
        tg.track_row_ages(a2, 2, ctx, eps, META)
        self.assertEqual(eps[0]["ende"], "voll_gelegt")

    def test_summary_rates(self):
        eps = self.run_three_rounds()
        summ = tg.summarize_row_ages(eps, lambda r: r["names"][r["pi"]])
        self.assertEqual(summ["Mensch"]["Reihe5"]["episoden"], 2)
        self.assertEqual(summ["KI"]["Reihe5"]["praedikat_je_rundenende"]["ja_wartend"], 3)
        self.assertEqual(summ["KI"]["Reihe5"]["chip_gelegt_anteil"], 1.0)
        self.assertEqual(summ["Mensch"]["Reihe5"]["geraeumt_anteil"], 0.5)


class DomeCatalog(unittest.TestCase):
    def test_catalog_has_18_designs_with_4_cells(self):
        self.assertEqual(len(tg.DOME_DESIGNS), 18)
        self.assertTrue(all(len(d) == 4 for d in tg.DOME_DESIGNS))
        self.assertEqual(sum(1 for d in tg.DOME_DESIGNS if any(c[0] == "S" for c in d)), 9)


if __name__ == "__main__":
    unittest.main()
