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
