"""Waechter fuer Code-Review 2026-10-02 Befund 20: die Stufe-3-Arena in
`tools/arena.py` wertet keine abgebrochene Partie.

Bis dahin brach die Rust-Seite (`play_stage3_vs_stage1_game`) nach Wanduhr ab
und gab den Zwischenstand ohne Markierung zurueck; `arena.py` rechnete ihn in
Elo und SPRT ein. Jetzt traegt jedes Ergebnis `completed`, und `arena.py`
bricht bei `completed: false` laut ab (Muster
`paired_gating.py::find_incomplete_games`).

Bezeichner englisch (CLAUDE.md 2026-08-24), Inhaltssprache deutsch.
"""

import json
import pathlib
import sys
import unittest
from unittest import mock

_TOOLS = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_TOOLS))

import arena  # noqa: E402


def _game(completed, reason=None):
    g = {"scores": [10, 8], "winner": 0, "steps": 40}
    if completed is not None:
        g["completed"] = completed
    if reason:
        g["abort_reason"] = reason
    return g


class FindIncompleteStage3Games(unittest.TestCase):
    def test_only_explicit_false_counts_and_diagnostics_are_skipped(self):
        results = [
            _game(True),
            {"stage3_diagnostics": True, "decisions": 3, "rollouts_triggered": 3},
            _game(False, "step_limit"),
            _game(None),  # altes Wheel ohne Feld: hier NICHT gezaehlt
        ]
        out = arena.find_incomplete_stage3_games(results, first_game_index=10, chunk_seed=7)
        self.assertEqual(out, [{"game_index": 11, "chunk_seed": 7,
                                "abort_reason": "step_limit", "steps": 40}])

    def test_run_aborts_on_incomplete_game(self):
        fake = mock.Mock()
        fake.stage3_vs_stage1_arena_match.return_value = json.dumps(
            [_game(True), _game(False, "hang_alarm")])
        with mock.patch.object(arena, "_mr", fake):
            with self.assertRaises(RuntimeError) as ctx:
                arena.run_stage3_vs_stage1("dummy.onnx", games=2, chunk=2, seed=1,
                                           early_stop=False)
        self.assertIn("hang_alarm", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
