# -*- coding: utf-8 -*-
"""Tests fuer tools/probes/tiling_surprise_probe.py (evaluations/PREREG_tiling_surprise_probe.md par.2).

Attrappen statt Netz und Wheel: synthetische Record-Folgen in der Form der Self-Play-Records
(`state` mit `phase`, `round`, `current_player`, `players[i].score/estimated_score`; Tiling-Records mit
genau einem Policy-Eintrag), Kopfausgaben als Zahlen. Geprueft werden Zustandsauszug (S_pre/S_post),
Perspektive, Differenz und Einheiten sowie die Datei-Block-Statistik.

Bezeichner englisch (CLAUDE.md 2026-08-24), Inhaltssprache deutsch.
"""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "probes"))

import tiling_surprise_probe as tsp  # noqa: E402


def state(phase, rnd, cp, scores, est=(0, 0), tag=""):
    return {"phase": phase, "round": rnd, "current_player": cp, "tag": tag,
            "players": [{"score": scores[0], "estimated_score": est[0]},
                        {"score": scores[1], "estimated_score": est[1]}]}


def drafting(rnd, player, scores, root_q=None, tag="", est=(0, 0)):
    rec = {"game_id": "g", "player": player, "policy": [{"action": {"type": "stone"}}] * 3,
           "state": state("drafting", rnd, player, scores, est, tag)}
    if root_q is not None:
        rec["root_q"] = root_q
    return rec


def tiling(rnd, player, scores, act, tag="", est=(0, 0)):
    return {"game_id": "g", "player": player, "policy": [{"action": {"type": act}}],
            "state": state("tiling", rnd, player, scores, est, tag)}


def one_round_game():
    """Runde 1: zwei Drafting-Records (der letzte ohne root_q), Tiling 1 (end) / 0 (tile, end),
    danach ein Record der Runde 2 mit Strafe."""
    return [
        drafting(1, 0, (5, 5), root_q=0.6),
        drafting(1, 1, (5, 5), root_q=None),
        tiling(1, 0, (5, 5), "end_tiling", tag="pre", est=(3, 4)),
        tiling(1, 1, (5, 5), "tiling"),
        tiling(1, 1, (5, 8), "end_tiling", tag="post"),
        drafting(2, 1, (5, 7)),
    ]


class ExtractRoundPairs(unittest.TestCase):

    def test_pre_post_and_fields(self):
        pairs, skips = tsp.extract_round_pairs(one_round_game(), rounds=(1,))
        self.assertEqual(len(pairs), 1)
        self.assertEqual(sum(skips.values()), 0)
        p = pairs[0]
        self.assertEqual(p["s_pre"]["tag"], "pre")
        self.assertEqual(p["s_post"]["tag"], "post")
        self.assertEqual(p["last_drafter"], 1)
        self.assertEqual(p["score_pre"], [5, 5])
        self.assertEqual(p["score_post"], [5, 8])
        self.assertEqual(p["score_next"], [5, 7])
        self.assertEqual(p["estimated_pre"], [3, 4])
        # root_q vom letzten Drafting-Record MIT root_q, ein Record davor
        self.assertEqual(p["root_q"], 0.6)
        self.assertEqual(p["root_q_player"], 0)
        self.assertEqual(p["root_q_lag"], 1)

    def test_absent_round_is_counted_not_paired(self):
        # Ausflugspartie: beginnt in Runde 2, Runde 1 fehlt
        seq = [r for r in one_round_game()]
        pairs, skips = tsp.extract_round_pairs(seq, rounds=(1, 2))
        self.assertEqual(len(pairs), 1)
        self.assertEqual(skips["round_absent"], 1)

    def test_unclosed_tiling_is_skipped(self):
        seq = one_round_game()
        seq[4] = tiling(1, 1, (5, 8), "tiling")   # zweites end_tiling fehlt
        pairs, skips = tsp.extract_round_pairs(seq, rounds=(1,))
        self.assertEqual(pairs, [])
        self.assertEqual(skips["tiling_not_closed"], 1)

    def test_missing_next_round_keeps_pair_without_settled_points(self):
        seq = one_round_game()[:-1]
        pairs, skips = tsp.extract_round_pairs(seq, rounds=(1,))
        self.assertEqual(len(pairs), 1)
        self.assertIsNone(pairs[0]["score_next"])
        self.assertEqual(skips["no_next_round_record"], 1)
        rows = tsp.null_rows(pairs[0], 0)
        self.assertNotIn("own_settled_points", rows)
        self.assertIn("own_tiling_points", rows)


class Perspective(unittest.TestCase):

    def test_with_perspective_copies(self):
        st = state("tiling", 1, 1, (0, 0))
        out = tsp.with_perspective(st, 0)
        self.assertEqual(out["current_player"], 0)
        self.assertEqual(st["current_player"], 1)
        self.assertIs(out["players"], st["players"])

    def test_root_q_flip(self):
        self.assertAlmostEqual(tsp.perspective_root_q(0.7, 1, 1), 0.7)
        self.assertAlmostEqual(tsp.perspective_root_q(0.7, 1, 0), 0.3)
        self.assertIsNone(tsp.perspective_root_q(None, 1, 0))

    def test_subsets(self):
        pair = {"last_drafter": 1}
        self.assertEqual(tsp.subsets_for(pair, 1), ("all", "last_drafter"))
        self.assertEqual(tsp.subsets_for(pair, 0), ("all",))


class Differences(unittest.TestCase):

    def setUp(self):
        self.pair = tsp.extract_round_pairs(one_round_game(), rounds=(1,))[0][0]

    def test_value_difference_in_win_probability(self):
        rows = tsp.surprise_rows(self.pair, 1, {"value": 0.0, "points": 0.0, "opp_points": 0.0},
                                 {"value": 0.5, "points": 0.0, "opp_points": 0.0})
        self.assertAlmostEqual(rows["value"][0], 0.25)       # 0,75 - 0,5
        self.assertAlmostEqual(rows["value_level_pre"][0], 0.5)
        # root_q 0,6 gehoert Spieler 0 -> fuer Spieler 1 gilt 0,4
        self.assertAlmostEqual(rows["value_vs_root_q"][0], 0.75 - 0.4)

    def test_points_in_points_with_tiling_regressor(self):
        x_pre, x_post = math.tanh(40 / 50), math.tanh(43 / 50)
        rows = tsp.surprise_rows(self.pair, 1, {"value": 0.0, "points": x_pre, "opp_points": None},
                                 {"value": 0.0, "points": x_post, "opp_points": None})
        self.assertAlmostEqual(rows["points"][0], 3.0, places=6)
        self.assertEqual(rows["points"][1], 3)                # Spieler 1 tilt 5 -> 8
        self.assertAlmostEqual(rows["points_raw"][0], x_post - x_pre)
        self.assertNotIn("opp_points", rows)                  # Kopf fehlt -> keine Zeile

    def test_null_rows(self):
        rows = tsp.null_rows(self.pair, 1)
        self.assertEqual(rows["own_tiling_points"][0], 3)
        self.assertEqual(rows["opp_tiling_points"][0], 0)
        self.assertEqual(rows["own_settled_points"][0], 2)    # 5 -> 7 inkl. Strafe
        self.assertEqual(rows["projection_gap_own"][0], 2 - 4)
        self.assertEqual(rows["root_q_lag"][0], 1)

    def test_head_points_clips_at_the_edge(self):
        self.assertTrue(math.isfinite(tsp.head_points(1.0)))
        self.assertAlmostEqual(tsp.head_points(0.0), 0.0)


class BlockStatistics(unittest.TestCase):

    def test_pooled_moments(self):
        t = tsp.SumTable(2)
        for v in (1.0, -1.0, 2.0):
            t.add("k", 0, v)
        t.add("k", 1, 4.0)
        idx = np.random.default_rng(0).integers(0, 2, size=(50, 2))
        s = tsp.summarize(t.rows["k"], idx, with_slope=False)
        vals = [1.0, -1.0, 2.0, 4.0]
        self.assertEqual(s["n"], 4)
        self.assertAlmostEqual(s["mean"], np.mean(vals))
        self.assertAlmostEqual(s["sd"], np.std(vals, ddof=1))
        self.assertAlmostEqual(s["mean_abs"], np.mean(np.abs(vals)))

    def test_identical_files_give_degenerate_ci(self):
        t = tsp.SumTable(3)
        for f in range(3):
            for v in (0.1, 0.3):
                t.add("k", f, v)
        idx = np.random.default_rng(1).integers(0, 3, size=(200, 3))
        s = tsp.summarize(t.rows["k"], idx, with_slope=False)
        self.assertAlmostEqual(s["mean_ci95"][0], 0.2)
        self.assertAlmostEqual(s["mean_ci95"][1], 0.2)

    def test_file_is_the_block(self):
        # Datei 0 traegt nur +1, Datei 1 nur -1: das CI des Mittels muss die Dateistreuung
        # zeigen (Ziehungen mit nur einer der beiden Dateien), nicht die Zeilenzahl.
        t = tsp.SumTable(2)
        for _ in range(100):
            t.add("k", 0, 1.0)
            t.add("k", 1, -1.0)
        idx = np.random.default_rng(2).integers(0, 2, size=(400, 2))
        s = tsp.summarize(t.rows["k"], idx, with_slope=False)
        self.assertAlmostEqual(s["mean"], 0.0)
        self.assertLess(s["mean_ci95"][0], -0.9)
        self.assertGreater(s["mean_ci95"][1], 0.9)

    def test_slope_recovers_known_relation(self):
        t = tsp.SumTable(4)
        for f in range(4):
            for x in range(10):
                t.add("k", f, 0.5 * x + 1.0, x=x)
        idx = np.random.default_rng(3).integers(0, 4, size=(100, 4))
        s = tsp.summarize(t.rows["k"], idx, with_slope=True)
        self.assertAlmostEqual(s["slope"], 0.5)
        self.assertAlmostEqual(s["slope_ci95"][0], 0.5)

    def test_paired_difference_of_identical_tables_is_zero(self):
        a, b = tsp.SumTable(3), tsp.SumTable(3)
        rng = np.random.default_rng(4)
        for f in range(3):
            for v in rng.normal(size=20):
                a.add("k", f, v)
                b.add("k", f, v)
        idx = rng.integers(0, 3, size=(100, 3))
        d = tsp.paired_difference(a.rows["k"], b.rows["k"], idx)
        self.assertAlmostEqual(d["mean_abs_diff"], 0.0)
        self.assertEqual(d["mean_abs_diff_ci95"], [0.0, 0.0])

    def test_report_layout_and_reference_diff(self):
        t = tsp.SumTable(2)
        for f in range(2):
            t.add(("netA", 1, "all", "value"), f, 0.1)
            t.add(("netB", 1, "all", "value"), f, 0.3)
            t.add(("null", 1, "all", "own_tiling_points"), f, 4)
        idx = np.random.default_rng(5).integers(0, 2, size=(20, 2))
        rep = tsp.build_report(t, ["null", "netA", "netB"], idx, "netA")
        self.assertAlmostEqual(rep["by_scope"]["netB"][1]["all"]["value"]["mean"], 0.3)
        diff = rep["paired_vs_reference"]["netB_minus_netA"][1]["all"]["value"]
        self.assertAlmostEqual(diff["mean_diff"], 0.2)
        self.assertNotIn("null_minus_netA", rep["paired_vs_reference"])


class WheelGuard(unittest.TestCase):

    def test_missing_export_aborts_readably(self):
        class FakeWheel:
            __file__ = "fake_wheel"
            state_features_from_json = staticmethod(lambda js: [])
        with self.assertRaises(SystemExit) as ctx:
            tsp.require_exports(FakeWheel)
        self.assertIn("state_planes_from_json", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
