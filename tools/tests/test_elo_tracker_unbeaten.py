# -*- coding: utf-8 -*-
"""Code-Review 2026-09-26 #20: ein Knoten mit NUR Siegen oder NUR Niederlagen
hat im Bradley-Terry-Fit keine endliche Schaetzung; der Report druckte eine
Scheinzahl (sie misst die Iterationszahl von `_mm_fit`). Und ein
Bootstrap-Intervall der Breite 0 sah wie hoechste Sicherheit aus.

Geprueft: `unbeaten_label` erkennt beide Faelle, `ci_label` markiert Breite 0
und uebergrosse Breite als "degeneriert" (der Anker bleibt ausgenommen), und
`report()` druckt fuer einen ungeschlagenen Knoten keine Elo-Zahl.
"""
from __future__ import annotations

import contextlib
import io
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import elo_tracker as et  # noqa: E402


class UnbeatenLabel(unittest.TestCase):
    def test_all_wins_and_all_losses(self):
        self.assertEqual(et.unbeaten_label(10, 10), "alle 10 gewonnen")
        self.assertEqual(et.unbeaten_label(0, 10), "alle 10 verloren")

    def test_mixed_or_empty_is_none(self):
        self.assertIsNone(et.unbeaten_label(5, 10))
        self.assertIsNone(et.unbeaten_label(0, 0))


class CiLabel(unittest.TestCase):
    def test_zero_width_is_degenerate(self):
        self.assertEqual(et.ci_label(2079.9, 2079.9), "degeneriert")

    def test_huge_width_stays_degenerate(self):
        self.assertEqual(et.ci_label(-2600.0, 1100.0), "degeneriert")

    def test_normal_interval(self):
        self.assertEqual(et.ci_label(900.4, 1100.6), "[900, 1101]")

    def test_anchor_is_exempt_and_missing_is_na(self):
        self.assertEqual(et.ci_label(1000.0, 1000.0, is_anchor=True), "[1000, 1000]")
        self.assertEqual(et.ci_label(None, None), "n/a")


class ReportShowsNoFakeNumber(unittest.TestCase):
    def test_sweep_against_the_anchor(self):
        row = {"date": "2026-09-27", "player_a": "sweeper", "sims_a": 400,
               "player_b": et.ANCHOR_NAME, "sims_b": et.ANCHOR_SIMS,
               "wins_a": 10, "wins_b": 0, "n": 10, "comment": "Test", "units": "",
               "early_stop": False}
        fitted, *_ = et.fit_all([row])
        sweeper = et.node_key("sweeper", 400)
        # Der Fit selbst liefert die Scheinzahl weiter (Herleitung Review #20: ~2080).
        self.assertGreater(fitted[sweeper][0], 1800)
        out = io.StringIO()
        with mock.patch.object(et, "load_rows", lambda: [row]), contextlib.redirect_stdout(out):
            et.report(n_boot=20)
        line = next(ln for ln in out.getvalue().splitlines() if ln.startswith(sweeper))
        self.assertIn("unbeschr.", line)
        self.assertIn("alle 10 gewonnen", line)
        self.assertNotIn(f"{fitted[sweeper][0]:.0f}", line)


if __name__ == "__main__":
    unittest.main()
