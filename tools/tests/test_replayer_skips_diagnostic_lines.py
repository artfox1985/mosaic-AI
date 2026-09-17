# -*- coding: utf-8 -*-
"""Diagnosezeilen im Partie-Log brechen den Replayer nicht mehr.

Die Engine haengt je Partie eine Zeile an, wenn der jeweilige Knopf an war:
`[moon_order] applied= changed=` (self_play.rs:4256-4261) und `[rt_leaf]
leaves= pseudo= applied=` (self_play.rs:4275-4281). Beide sitzen zwischen
"Das Spiel ist beendet!" und der Endwertung und gehoeren zu keinem
apply_*-Aufruf. Vor dem Fix brach JEDE Partie mit gesetztem rt_leaf-Knopf ab
(0 von 360 in evaluations/artifacts/arena_columns_rt_leaf_on_vs_off_s20261152.json).

Geprueft wird nur die Klassifikation -- keine Engine, kein Replay."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import analyze_game_log as agl  # noqa: E402


class DiagnosticLineTest(unittest.TestCase):
    def test_rt_leaf_line_is_diagnostic(self):
        # Woertlich aus dem Fehlertext des Laufs s20261152.
        self.assertTrue(agl.is_diagnostic_log_line(
            "[R5] [rt_leaf] leaves=14216 pseudo=183 applied=183"))

    def test_moon_order_line_is_diagnostic(self):
        self.assertTrue(agl.is_diagnostic_log_line(
            "[R3] [moon_order] applied=12 changed=8"))

    def test_body_without_round_prefix_is_diagnostic(self):
        self.assertTrue(agl.is_diagnostic_log_line("[rt_leaf] leaves=1 pseudo=0 applied=0"))

    def test_real_action_line_is_not_diagnostic(self):
        line = "[R5] 🏆 NetzA: Endwertung 16 Pkt → Gesamt: 69 Pkt"
        self.assertFalse(agl.is_diagnostic_log_line(line))
        self.assertEqual(agl.classify(agl.ROUND_PREFIX.match(line).group(2))[0], "FINAL_SCORE")

    def test_game_over_line_is_not_diagnostic(self):
        self.assertFalse(agl.is_diagnostic_log_line("[R5] Das Spiel ist beendet!"))

    def test_markers_are_a_list_both_entries(self):
        # Die Liste ist der Ort fuer den naechsten Marker -- wer sie umbaut,
        # soll hier stolpern, nicht erst im naechsten Nachtlauf.
        self.assertIn("[rt_leaf]", agl.DIAGNOSTIC_LINE_MARKERS)
        self.assertIn("[moon_order]", agl.DIAGNOSTIC_LINE_MARKERS)


if __name__ == "__main__":
    unittest.main()
