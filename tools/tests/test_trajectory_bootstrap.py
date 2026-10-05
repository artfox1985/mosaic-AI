# -*- coding: utf-8 -*-
"""Trajektorien-Bootstrap (PREREG_v35_window.md par.12a, Arm v35-b03).

Prueft die reine Suchfunktion `trajectory_bootstrap_lookup`, ihre Datei-Variante
`trajectory_bootstrap_values`, den Margen-Bootstrap `margin_bootstrap_value`
(par.14, Arm v35-b04) und die Knopf-Leser
`file_cache_key._bootstrap_trajectory_horizon_key` / `_bootstrap_margin_scale_key` auf synthetischen Records im
Speicher. Kein torch, keine Dateien, kein Korpus: beide Module laden ohne
Netz-Umgebung (`trajectory_bootstrap` nur Standardbibliothek, `file_cache_key`
importiert erst beim Aufruf von `per_file_cache_key`).
"""
from __future__ import annotations

import math
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "engine" / "py"))

from file_cache_key import (  # noqa: E402
    _bootstrap_margin_scale_key,
    _bootstrap_trajectory_horizon_key,
)
from trajectory_bootstrap import (  # noqa: E402
    add_trajectory_counts,
    format_margin_counts,
    format_trajectory_counts,
    margin_bootstrap_value,
    trajectory_bootstrap_lookup,
    trajectory_bootstrap_values,
)


def rec(player, rd, root_q=None, dice_phase=None, game_id="g1"):
    """Synthetischer Record mit genau den Feldern, die die Suche liest."""
    r = {"game_id": game_id, "player": player, "state": {"round": rd}}
    if root_q is not None:
        r["root_q"] = root_q
    if dice_phase is not None:
        r["dice_phase"] = dice_phase
    return r


def full_game(game_id="g1"):
    """Zwei Spieler, Runden 1-5, je Runde und Spieler zwei Records im Wechsel.

    root_q kodiert Spieler, Runde und Position: 0.p r i als Zahl, z. B. Spieler
    1, Runde 3, zweiter Record -> 0.132. So ist jeder Treffer eindeutig lesbar.
    """
    out = []
    for rd in range(1, 6):
        for i in range(2):
            for p in (0, 1):
                out.append(rec(p, rd, root_q=q(p, rd, i), game_id=game_id))
    return out


def q(p, rd, i):
    """root_q, das `full_game` dem i-ten Record (0/1) von Spieler p in Runde rd gibt."""
    return round(p * 0.1 + rd * 0.01 + i * 0.001 + 0.001, 4)


def index_of(game, p, rd, i):
    hits = [n for n, r in enumerate(game) if r["player"] == p and r["state"]["round"] == rd]
    return hits[i]


class LookupTest(unittest.TestCase):
    def test_first_record_of_same_side_k_rounds_later(self):
        g = full_game()
        self.assertEqual(trajectory_bootstrap_lookup(g, index_of(g, 0, 1, 0), 2), q(0, 3, 0))
        self.assertEqual(trajectory_bootstrap_lookup(g, index_of(g, 1, 1, 1), 2), q(1, 3, 0))
        self.assertEqual(trajectory_bootstrap_lookup(g, index_of(g, 0, 2, 0), 1), q(0, 3, 0))
        self.assertEqual(trajectory_bootstrap_lookup(g, index_of(g, 1, 1, 0), 3), q(1, 4, 0))

    def test_value_is_record_space_without_remap(self):
        g = [rec(0, 1, root_q=0.9), rec(0, 3, root_q=0.25)]
        self.assertEqual(trajectory_bootstrap_lookup(g, 0, 2), 0.25)

    def test_missing_root_q_is_skipped(self):
        g = full_game()
        del g[index_of(g, 0, 3, 0)]["root_q"]
        self.assertEqual(trajectory_bootstrap_lookup(g, index_of(g, 0, 1, 0), 2), q(0, 3, 1))

    def test_dice_phase_is_skipped(self):
        g = full_game()
        g[index_of(g, 0, 3, 0)]["dice_phase"] = True
        self.assertEqual(trajectory_bootstrap_lookup(g, index_of(g, 0, 1, 0), 2), q(0, 3, 1))
        # dice_phase False zaehlt wie fehlend: der Record ist zulaessig.
        g[index_of(g, 0, 3, 1)]["dice_phase"] = False
        g[index_of(g, 0, 3, 0)]["dice_phase"] = False
        self.assertEqual(trajectory_bootstrap_lookup(g, index_of(g, 0, 1, 0), 2), q(0, 3, 0))

    def test_horizon_is_an_upper_bound_not_an_exact_distance(self):
        # Runde 3 der Seite 0 ganz ohne root_q -> der erste zulaessige spaetere
        # Record liegt in Runde 4 (>= rd + k, nicht == rd + k).
        g = full_game()
        for i in range(2):
            del g[index_of(g, 0, 3, i)]["root_q"]
        self.assertEqual(trajectory_bootstrap_lookup(g, index_of(g, 0, 1, 0), 2), q(0, 4, 0))

    def test_opponent_records_are_never_taken(self):
        g = [rec(0, 1, root_q=0.5), rec(1, 3, root_q=0.9), rec(1, 4, root_q=0.8)]
        self.assertIsNone(trajectory_bootstrap_lookup(g, 0, 2))

    def test_game_end_closer_than_k_gives_none(self):
        g = full_game()
        # k = 2 ab Runde 4, k = 3 ab Runde 3, k = 1 in Runde 5: kein Record mehr.
        self.assertIsNone(trajectory_bootstrap_lookup(g, index_of(g, 0, 4, 0), 2))
        self.assertIsNone(trajectory_bootstrap_lookup(g, index_of(g, 1, 3, 1), 3))
        self.assertIsNone(trajectory_bootstrap_lookup(g, index_of(g, 0, 5, 0), 1))
        # Grenzfall: Runde 4 mit k = 1 findet Runde 5.
        self.assertEqual(trajectory_bootstrap_lookup(g, index_of(g, 0, 4, 1), 1), q(0, 5, 0))

    def test_only_later_records_count(self):
        # Ein FRUEHERER Record mit passender Runde (falsche Dateireihenfolge)
        # wird nicht genommen: gesucht wird nur hinter dem Index.
        g = [rec(0, 3, root_q=0.7), rec(0, 1, root_q=0.5)]
        self.assertIsNone(trajectory_bootstrap_lookup(g, 1, 2))

    def test_invalid_horizon_raises(self):
        g = full_game()
        for bad in (0, -1, 2.0, None):
            with self.assertRaises(ValueError):
                trajectory_bootstrap_lookup(g, 0, bad)

    def test_record_without_round_raises(self):
        g = [{"game_id": "g1", "player": 0, "state": {}}, rec(0, 3, root_q=0.4)]
        with self.assertRaises(ValueError):
            trajectory_bootstrap_lookup(g, 0, 2)


class FileLevelTest(unittest.TestCase):
    def test_games_are_grouped_by_game_id_in_file_order(self):
        a, b = full_game("a"), full_game("b")
        # b bekommt eigene Werte, damit eine Vermischung auffiele.
        for r in b:
            r["root_q"] = round(r["root_q"] + 0.5, 4)
        # Verschraenkt ablegen: die Gruppierung darf nicht an Zusammenhang haengen.
        mixed = [r for pair in zip(a, b) for r in pair]
        out = trajectory_bootstrap_values(mixed, 2)
        self.assertEqual(len(out), len(mixed))
        for n, r in enumerate(mixed):
            own = a if r["game_id"] == "a" else b
            expect = trajectory_bootstrap_lookup(own, own.index(r), 2)
            self.assertEqual(out[n], expect)
        first_a = mixed.index(a[0])
        first_b = mixed.index(b[0])
        self.assertEqual(out[first_a], q(0, 3, 0))
        self.assertEqual(out[first_b], round(q(0, 3, 0) + 0.5, 4))

    def test_counts_add_and_format(self):
        total = {}
        add_trajectory_counts(total, {1: [3, 0, 0], 4: [0, 2, 0]})
        add_trajectory_counts(total, None)
        add_trajectory_counts(total, {"1": [1, 0, 0], 5: [0, 0, 4]})
        self.assertEqual(total, {1: [4, 0, 0], 4: [0, 2, 0], 5: [0, 0, 4]})
        lines = format_trajectory_counts(total, 2)
        self.assertEqual(len(lines), 4)
        self.assertIn("Runde 1: 4 / 0 / 0", lines[1])


class MarginBootstrapTest(unittest.TestCase):
    """par.14 (Arm v35-b04): sigmoid(Endmarge des Ziehers / b)."""

    def test_zero_margin_is_one_half(self):
        self.assertEqual(margin_bootstrap_value(0.0, 20.0), 0.5)

    def test_plus_b_is_sigmoid_one(self):
        s1 = 1.0 / (1.0 + math.exp(-1.0))
        self.assertAlmostEqual(margin_bootstrap_value(20.0, 20.0), s1, places=12)
        self.assertAlmostEqual(margin_bootstrap_value(-20.0, 20.0), 1.0 - s1, places=12)
        self.assertAlmostEqual(margin_bootstrap_value(12.5, 12.5), s1, places=12)

    def test_sign_follows_the_mover(self):
        # Gleiche Partie, Endstand 50:30. Spieler 0 sieht +20, Spieler 1 -20;
        # Margen wie final_margin_of_step: scores_unclamped[p] - scores_unclamped[1-p].
        scores = [50.0, 30.0]
        for p in (0, 1):
            margin = scores[p] - scores[1 - p]
            value = margin_bootstrap_value(margin, 20.0)
            if p == 0:
                self.assertGreater(value, 0.5)
            else:
                self.assertLess(value, 0.5)
        self.assertAlmostEqual(margin_bootstrap_value(20.0, 20.0) + margin_bootstrap_value(-20.0, 20.0),
                               1.0, places=12)

    def test_large_margins_do_not_overflow(self):
        self.assertEqual(margin_bootstrap_value(1e6, 1.0), 1.0)
        self.assertEqual(margin_bootstrap_value(-1e6, 1.0), 0.0)

    def test_invalid_scale_or_margin_raises(self):
        for bad in (0.0, -5.0, float("nan"), float("inf")):
            with self.subTest(scale=bad), self.assertRaises(ValueError):
                margin_bootstrap_value(10.0, bad)
        with self.assertRaises(ValueError):
            margin_bootstrap_value(float("nan"), 20.0)

    def test_margin_counts_format(self):
        lines = format_margin_counts({2: [7, 0, 1]}, "20")
        self.assertIn("b = 20", lines[0])
        self.assertIn("Runde 2: 7 / 0 / 1", lines[1])


SOURCE = "MOSAIC_BOOTSTRAP_SOURCE"
HORIZON = "MOSAIC_BOOTSTRAP_HORIZON_ROUNDS"
SCALE = "MOSAIC_BOOTSTRAP_MARGIN_SCALE"


class KnobReaderTest(unittest.TestCase):
    def _read(self, **env):
        clean = {k: v for k, v in os.environ.items() if k not in (SOURCE, HORIZON, SCALE)}
        clean.update(env)
        with mock.patch.dict(os.environ, clean, clear=True):
            return _bootstrap_trajectory_horizon_key()

    def _read_margin(self, **env):
        clean = {k: v for k, v in os.environ.items() if k not in (SOURCE, HORIZON, SCALE)}
        clean.update(env)
        with mock.patch.dict(os.environ, clean, clear=True):
            return _bootstrap_margin_scale_key()

    def test_margin_source_valid_and_canonical(self):
        self.assertEqual(self._read_margin(**{SOURCE: "margin", SCALE: "20"}), "20")
        self.assertEqual(self._read_margin(**{SOURCE: "margin", SCALE: "20.0"}), "20")
        self.assertEqual(self._read_margin(**{SOURCE: "margin", SCALE: "12.50"}), "12.5")
        # Die beiden Leser schliessen sich aus.
        self.assertIsNone(self._read(**{SOURCE: "margin", SCALE: "20"}))
        self.assertIsNone(self._read_margin(**{SOURCE: "trajectory", HORIZON: "2"}))
        self.assertIsNone(self._read_margin())

    def test_margin_invalid_settings_raise(self):
        bad = [
            {SOURCE: "margin"},
            {SOURCE: "margin", SCALE: "0"},
            {SOURCE: "margin", SCALE: "-3"},
            {SOURCE: "margin", SCALE: "nan"},
            {SOURCE: "margin", SCALE: "inf"},
            {SOURCE: "margin", SCALE: "zwanzig"},
            {SOURCE: "margin", SCALE: "20", HORIZON: "2"},
            {SOURCE: "trajectory", HORIZON: "2", SCALE: "20"},
            {SCALE: "20"},
        ]
        for env in bad:
            for reader in (self._read, self._read_margin):
                with self.subTest(env=env, reader=reader.__name__), self.assertRaises(ValueError):
                    reader(**env)

    def test_unset_and_empty_mean_stock(self):
        self.assertIsNone(self._read())
        self.assertIsNone(self._read(**{SOURCE: "", HORIZON: ""}))

    def test_valid_settings(self):
        for k in (1, 2, 3):
            self.assertEqual(self._read(**{SOURCE: "trajectory", HORIZON: str(k)}), k)
        self.assertEqual(self._read(**{SOURCE: " Trajectory ", HORIZON: " 2 "}), 2)

    def test_invalid_settings_raise(self):
        bad = [
            {SOURCE: "rollout", HORIZON: "2"},
            {SOURCE: "trajectory"},
            {SOURCE: "trajectory", HORIZON: "0"},
            {SOURCE: "trajectory", HORIZON: "4"},
            {SOURCE: "trajectory", HORIZON: "two"},
            {SOURCE: "trajectory", HORIZON: "2.0"},
            {HORIZON: "2"},
        ]
        for env in bad:
            with self.subTest(env=env), self.assertRaises(ValueError):
                self._read(**env)


if __name__ == "__main__":
    unittest.main()
