# -*- coding: utf-8 -*-
"""`--fixed-length` in `tools/paired_gating.py` (2026-10-08,
PREREG_v35_window.md par.19.0 Punkt 3: Schnellblick mit fester Laenge, SPRT-
Schranken nur mitgeschrieben).

Keine Engine: `play_pair_block` ist eine Attrappe (Bauform wie
test_paired_gating_resume.py), `mosaic_rust` ein leeres Modul, der Trend-Log
abgeklemmt.

Geprueft:
  - ohne Schalter stoppt ein klarer Lauf wie bisher frueh per SPRT;
  - mit Schalter laeuft derselbe Lauf bis `max_pairs`, das Artefakt traegt
    `sprt_verdict = FIXED_LENGTH`, die erste Schranken-Beruehrung und den
    Entscheid mit End-LLR; keine Champion-Uebernahme;
  - ohne Schalter fehlen die neuen Felder (Artefakt wie bisher), und die
    Zwischenstand-Konfiguration traegt `fixed_length` nur mit Schalter;
  - `--resume` setzt einen Lauf mit fester Laenge fort, auch wenn der
    Zwischenstand die Schranke schon gerissen hat; eine Abweichung im Schalter
    bricht ab;
  - die CLI kennt den Schalter, Default aus.
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

import paired_gating as pg  # noqa: E402

BASE_SEED = 20261700
STRIDE = 1_000_000


class Interrupted(Exception):
    """Simulierter Abbruch mitten im Lauf."""


def sweeping_player(calls: list, fail_at_block: int | None = None):
    """A gewinnt jedes Paar zweimal (informatives Paar zu A) -- ein SPRT mit
    Standard-Schranken entscheidet damit nach wenigen Paaren."""
    def play(mr, model_a, model_b, sims_a, sims_b, c_puct_a, c_puct_b, n, seed, threads,
             spec_a=None, spec_b=None, log_games=False):
        block_index = (seed - BASE_SEED) // STRIDE
        if fail_at_block is not None and block_index == fail_at_block:
            raise Interrupted(f"Abbruch in Block {block_index + 1}")
        calls.append((seed, n))
        g1 = [{"winner": 0, "scores": [30, 20], "total_floor": [1, 2], "completed": True}
              for _ in range(n)]
        g2 = [{"winner": 1, "scores": [20, 30], "total_floor": [2, 1], "completed": True}
              for _ in range(n)]
        return g1, g2
    return play


def run(player, directory: Path | None = None, **overrides) -> dict:
    kwargs = dict(name_a="A", name_b="B", sims_a=10, sims_b=10, block_size=5, max_pairs=50,
                  base_seed=BASE_SEED, threads=1)
    if directory is not None:
        kwargs["partial_path"] = directory / "quick.json.partial.json"
    kwargs.update(overrides)
    with mock.patch.dict(sys.modules, {"mosaic_rust": types.ModuleType("mosaic_rust")}), \
            mock.patch.object(pg, "append_run", lambda **_: None), \
            mock.patch.object(pg, "play_pair_block", player), \
            mock.patch("sys.stdout", new_callable=io.StringIO):
        return pg.run_paired_gating("a.onnx", "b.onnx", **kwargs)


class FixedLengthRunsToTheCap(unittest.TestCase):
    def test_without_switch_the_sprt_stops_early(self):
        calls = []
        result = run(sweeping_player(calls))
        self.assertEqual(result["sprt_verdict"], "A")
        self.assertLess(result["done_pairs"], 50)
        for key in ("fixed_length", "sprt_first_crossing", "sprt_decision_at_end"):
            self.assertNotIn(key, result)

    def test_with_switch_all_pairs_are_played_and_the_sprt_is_only_recorded(self):
        calls = []
        early = run(sweeping_player([]))
        result = run(sweeping_player(calls), fixed_length=True)
        self.assertEqual(result["done_pairs"], 50)
        self.assertEqual(result["n_games_total"], 100)
        self.assertEqual(len(calls), 10)
        self.assertEqual([c[0] for c in calls], [BASE_SEED + i * STRIDE for i in range(10)])
        self.assertEqual(result["sprt_verdict"], "FIXED_LENGTH")
        self.assertTrue(result["fixed_length"])
        crossing = result["sprt_first_crossing"]
        self.assertEqual(crossing["verdict"], "A")
        # Die erste Beruehrung liegt genau dort, wo der SPRT-Lauf gestoppt hat.
        self.assertEqual(crossing["done_pairs"], early["done_pairs"])
        self.assertEqual(result["sprt_decision_at_end"], "A")
        self.assertEqual(result["a_wins_total"], 100)

    def test_no_crossing_gives_null(self):
        result = run(sweeping_player([]), fixed_length=True, max_pairs=1, block_size=1)
        self.assertEqual(result["done_pairs"], 1)
        self.assertIsNone(result["sprt_first_crossing"])
        self.assertIsNone(result["sprt_decision_at_end"])

    def test_no_champion_promotion_in_fixed_mode(self):
        with mock.patch.object(pg, "_set_champion") as set_champion:
            run(sweeping_player([]), fixed_length=True, promote_winner=True)
            set_champion.assert_not_called()


class FixedLengthAndThePartial(unittest.TestCase):
    def test_partial_config_carries_the_switch_only_when_set(self):
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            partial = directory / "quick.json.partial.json"
            try:
                run(sweeping_player([], fail_at_block=1), directory, fixed_length=True)
            except Interrupted:
                pass
            self.assertTrue(json.loads(partial.read_text(encoding="utf-8"))["config"]["fixed_length"])
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            partial = directory / "quick.json.partial.json"
            try:
                run(sweeping_player([], fail_at_block=1), directory)
            except Interrupted:
                pass
            self.assertNotIn("fixed_length", json.loads(partial.read_text(encoding="utf-8"))["config"])

    def test_resume_continues_past_a_crossed_bound(self):
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            # Erstlauf bricht in Block 6 ab; nach 5 Bloecken (25 Paaren) ist die
            # obere Schranke laengst gerissen.
            try:
                run(sweeping_player([], fail_at_block=5), directory, fixed_length=True)
            except Interrupted:
                pass
            calls = []
            result = run(sweeping_player(calls), directory, fixed_length=True, resume=True)
            self.assertEqual([c[0] for c in calls], [BASE_SEED + i * STRIDE for i in range(5, 10)])
            self.assertEqual(result["done_pairs"], 50)
            self.assertEqual(result["sprt_verdict"], "FIXED_LENGTH")
            uninterrupted = run(sweeping_player([]), fixed_length=True)
            self.assertEqual(result["sprt_first_crossing"], uninterrupted["sprt_first_crossing"])

    def test_resume_with_a_different_switch_aborts(self):
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            try:
                run(sweeping_player([], fail_at_block=1), directory, fixed_length=True)
            except Interrupted:
                pass
            with self.assertRaises(SystemExit):
                run(sweeping_player([]), directory, resume=True)


class CliKnowsTheSwitch(unittest.TestCase):
    def test_flag_parses_and_defaults_off(self):
        parser = pg.build_parser()
        base = ["--model-a", "a.onnx", "--model-b", "b.onnx"]
        self.assertFalse(parser.parse_args(base).fixed_length)
        self.assertTrue(parser.parse_args(base + ["--fixed-length"]).fixed_length)


if __name__ == "__main__":
    unittest.main()
