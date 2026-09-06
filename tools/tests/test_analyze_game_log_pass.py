# -*- coding: utf-8 -*-
"""Pass als eigene Log-Zeile (Nutzer 2026-09-07; PREREG_action_id_logging.md S2, Luecke 1
geschlossen): der Replayer klassifiziert die Zeile `⏭️ <Name>: passt` als PASS und
behandelt sie als primaere Aktionszeile. Ohne Engine (nur die Zeilen-Klassifikation)."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import analyze_game_log as agl  # noqa: E402


class PassLineTest(unittest.TestCase):
    def test_pass_line_is_primary_category(self):
        cat, m = agl.classify("⏭️ NetzA: passt")
        self.assertEqual(cat, "PASS")
        self.assertEqual(m.group("name"), "NetzA")
        self.assertIn("PASS", agl.PRIMARY_CATEGORIES)

    def test_pass_line_with_space_in_name(self):
        cat, m = agl.classify("⏭️ Spieler 1: passt")
        self.assertEqual(cat, "PASS")
        self.assertEqual(m.group("name"), "Spieler 1")

    def test_round_prefix_is_stripped_like_other_lines(self):
        mm = agl.ROUND_PREFIX.match("[R3] ⏭️ KI: passt")
        self.assertIsNotNone(mm)
        self.assertEqual(agl.classify(mm.group(2))[0], "PASS")

    def test_similar_text_is_not_pass(self):
        self.assertNotEqual(agl.classify("⏭️ NetzA: passt nicht")[0], "PASS")


if __name__ == "__main__":
    unittest.main()


class ChipLineTest(unittest.TestCase):
    """Bonuschip-Zeile: Symbol 🎴 (Nutzer 2026-09-07) und der Plaettchen-Zusatz.
    Altlogs tragen 🎫 und keinen Zusatz und muessen weiter replaybar bleiben."""

    def setUp(self):
        self.rep = agl.Replayer.__new__(agl.Replayer)
        self.rep.emoji_toleriert = 0
        self.rep.chip_zusatz_toleriert = 0
        self.rep.chip_symbol_toleriert = 0

    def test_both_symbols_classify(self):
        for sym in ("🎫", "🎴"):
            cat, m = agl.classify(f"{sym} NetzA komplettiert Reihe 3 mit Bonus-Chips!")
            self.assertEqual(cat, "CHIPS_COMPLETE", sym)
            self.assertEqual(m.group("row"), "3")

    def test_new_line_with_chip_list_classifies(self):
        cat, m = agl.classify("🎴 KI komplettiert Reihe 5 mit Bonus-Chips (3 Plättchen: rot, gelb+blau, schwarz)!")
        self.assertEqual(cat, "CHIPS_COMPLETE")
        self.assertEqual(m.group("name"), "KI")

    def test_old_log_line_equals_new_engine_line(self):
        old = "[R3] 🎫 KI komplettiert Reihe 5 mit Bonus-Chips!"
        new = "[R3] 🎴 KI komplettiert Reihe 5 mit Bonus-Chips (2 Plättchen: rot, rot)!"
        self.assertTrue(self.rep._lines_equal(old, new))
        self.assertEqual(self.rep.chip_symbol_toleriert, 1)
        self.assertEqual(self.rep.chip_zusatz_toleriert, 1)

    def test_symbol_only_difference_is_tolerated(self):
        old = "[R2] 🎫 KI komplettiert Reihe 4 mit Bonus-Chips!"
        new = "[R2] 🎴 KI komplettiert Reihe 4 mit Bonus-Chips!"
        self.assertTrue(self.rep._lines_equal(old, new))
        self.assertEqual(self.rep.chip_symbol_toleriert, 1)

    def test_different_row_is_not_tolerated(self):
        old = "[R3] 🎫 KI komplettiert Reihe 5 mit Bonus-Chips!"
        new = "[R3] 🎴 KI komplettiert Reihe 4 mit Bonus-Chips (2 Plättchen: rot, rot)!"
        self.assertFalse(self.rep._lines_equal(old, new))

    def test_different_round_is_not_tolerated(self):
        old = "[R2] 🎫 KI komplettiert Reihe 5 mit Bonus-Chips!"
        new = "[R3] 🎴 KI komplettiert Reihe 5 mit Bonus-Chips (2 Plättchen: rot, rot)!"
        self.assertFalse(self.rep._lines_equal(old, new))
