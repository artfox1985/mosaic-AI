# -*- coding: utf-8 -*-
"""Tests fuer tools/probes/sims_points_check.py (PREREG_asymmetric_selfplay.md par.8c), mit Fixture-Korpora
in einem Temp-Ordner, ohne Netz und ohne echte Daten."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tools" / "probes"))

import sims_points_check as spc  # noqa: E402
from corpus_io import dump_records  # noqa: E402


def final_record(gid: str, points: tuple[int, int], full_cols: tuple[int, int], k1: tuple[int, int]) -> dict:
    """Letzter Record einer Partie: zwei Seiten mit Punkten, Spaltenfuellung und k1-Plattenpunkten."""
    players = []
    for side in range(2):
        col_fill = [6] * full_cols[side] + [2] * (6 - full_cols[side])
        players.append({"score": points[side], "floor": [],
                        "score_geo": {"row_fill": [3] * 6, "col_fill": col_fill},
                        "scoring_tile_points": [0, k1[side], 0, 0, 0, 0, 0, 0]})
    return {"game_id": gid, "winner": 0 if points[0] >= points[1] else 1, "scores": list(points),
            "state": {"round": 5, "players": players, "scoring_tile_ids": [1, 3, 5]}}


def write_class(data: Path, cls: str, files: int, games_per_file: int, points, full_cols, k1) -> None:
    for fi in range(files):
        recs = [final_record(f"{cls}_c{fi}_g{g}", points, full_cols, k1) for g in range(games_per_file)]
        dump_records(data / f"selfplay_probe-v35-{cls}_20261004_{fi:03d}.pkl", recs)


class Reading(unittest.TestCase):
    def test_no_loss_when_ci_contains_zero_or_small_estimate(self):
        r = spc.reading({"differenz": -2.0, "ci95": [-4.0, 0.5]}, {"differenz": -0.01, "ci95": [-0.05, -0.001]})
        self.assertTrue(r["punkte_kein_verlust"] and r["spalten_kein_verlust"])
        self.assertIn("kein Verlust", r["verdikt"])

    def test_loss_needs_ci_below_zero_and_estimate_beyond_threshold(self):
        r = spc.reading({"differenz": -1.5, "ci95": [-2.5, -0.4]}, {"differenz": 0.0, "ci95": [-0.1, 0.1]})
        self.assertTrue(r["punkte_verlust"])
        self.assertIn("Mischsockel", r["verdikt"])
        r = spc.reading({"differenz": 0.2, "ci95": [-1.0, 1.0]}, {"differenz": -0.05, "ci95": [-0.08, -0.02]})
        self.assertTrue(r["spalten_verlust"])
        self.assertIn("Mischsockel", r["verdikt"])

    def test_ci_below_zero_with_small_estimate_is_no_loss(self):
        r = spc.reading({"differenz": -0.8, "ci95": [-1.4, -0.2]}, {"differenz": 0.0, "ci95": [-0.1, 0.1]})
        self.assertFalse(r["punkte_verlust"])
        self.assertTrue(r["punkte_kein_verlust"], "Schaetzer > -1,0 reicht")


class CompareGroups(unittest.TestCase):
    def test_pooled_difference_ci_and_reading_on_fixtures(self):
        with tempfile.TemporaryDirectory() as d:
            data = Path(d)
            # A: zwei Klassen, 60 Punkte und 1 volle Spalte je Seite; B: 50 Punkte, 1 volle Spalte.
            write_class(data, "a1", 2, 3, (60, 60), (1, 1), (4, 6))
            write_class(data, "a2", 1, 3, (60, 60), (1, 1), (4, 6))
            write_class(data, "b1", 3, 2, (50, 50), (1, 1), (2, 2))
            out = spc.compare_groups(data, ["a1", "a2"], ["b1"], n_boot=200, seed=1)
        self.assertEqual((out["gruppen"]["A"]["dateien"], out["gruppen"]["A"]["seiten"]), (3, 18))
        self.assertEqual((out["gruppen"]["B"]["dateien"], out["gruppen"]["B"]["seiten"]), (3, 12))
        diff = out["differenz_a_minus_b"]
        self.assertAlmostEqual(diff["punkte"]["differenz"], 10.0)
        self.assertEqual(diff["punkte"]["ci95"], [10.0, 10.0], "konstante Dateien: CI ist ein Punkt")
        self.assertAlmostEqual(diff["sp_voll"]["differenz"], 0.0)
        self.assertAlmostEqual(out["plattenpunkte_je_kriterium"]["k1"]["A"], 5.0)
        self.assertAlmostEqual(out["plattenpunkte_je_kriterium"]["k1"]["differenz"], 3.0)
        self.assertIn("kein Verlust", out["lesart"]["verdikt"])
        self.assertEqual(out["kosten_je_klasse"], {"a1": None, "a2": None, "b1": None}, "keine Manifeste")
        json.dumps(out)  # JSON-faehig

    def test_points_loss_is_read_as_mixed_base(self):
        with tempfile.TemporaryDirectory() as d:
            data = Path(d)
            write_class(data, "a1", 2, 2, (45, 47), (0, 1), (1, 1))
            write_class(data, "b1", 2, 2, (50, 52), (1, 1), (1, 1))
            out = spc.compare_groups(data, ["a1"], ["b1"], n_boot=100, seed=2)
        self.assertAlmostEqual(out["differenz_a_minus_b"]["punkte"]["differenz"], -5.0)
        self.assertAlmostEqual(out["differenz_a_minus_b"]["sp_voll"]["differenz"], -0.5)
        self.assertTrue(out["lesart"]["punkte_verlust"] and out["lesart"]["spalten_verlust"])
        self.assertIn("Mischsockel", out["lesart"]["verdikt"])

    def test_missing_class_aborts(self):
        with tempfile.TemporaryDirectory() as d:
            write_class(Path(d), "a1", 1, 1, (1, 1), (0, 0), (0, 0))
            with self.assertRaises(SystemExit):
                spc.compare_groups(Path(d), ["a1"], ["fehlt"], n_boot=10)

    def test_class_glob_does_not_mix_prefix_classes(self):
        with tempfile.TemporaryDirectory() as d:
            data = Path(d)
            write_class(data, "policy-s400-m2", 1, 1, (1, 1), (0, 0), (0, 0))
            write_class(data, "policy-s400-m2-b", 2, 1, (1, 1), (0, 0), (0, 0))
            self.assertEqual(len(spc.class_files(data, "policy-s400-m2")), 1)
            self.assertEqual(len(spc.class_files(data, "policy-s400-m2-b")), 2)


if __name__ == "__main__":
    unittest.main()
