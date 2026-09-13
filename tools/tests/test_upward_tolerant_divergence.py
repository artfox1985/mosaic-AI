"""Waechter fuer den aufwaerts-toleranten Record-Vergleich (Nutzer-Entscheid 2026-09-13).

Anlass: der additive Record `tiled_max_row` (P.14) liess die Anker-Drift ROT melden,
obwohl die Zugfolge Zug fuer Zug identisch war -- belegt in
`evaluations/artifacts/anchor_drift_counterproof_20260913_wheel1.json` (0 von 1.763
Records abweichend nach Abzug des neuen Feldes und des `game_id`-Zeitstempels, bei
GRUENER Konservierung gegen dieselbe Probe). Der Nutzer hat daraufhin Variante D
gewaehlt: nur AUFWAERTS tolerant.

Dieser Test misst die Regel an beiden Seiten, nicht nur an der bequemen
(Feedback `gate_that_is_bypassed_teaches_bypassing`: ein Waechter wird an Ausloesung
GEGEN Wirkung gemessen). Wird der Vergleich je auf "ignoriere alle Feldunterschiede"
verbreitert, fallen hier mehrere Faelle um.

Bezeichner englisch (CLAUDE.md 2026-08-24), Inhaltssprache deutsch.
"""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "probes"))

from generator_repro_probe import _first_divergence  # noqa: E402


def rec(players, **extra):
    r = {"game_id": "probe_1", "state": {"players": players}, "policy": [0.5, 0.5]}
    r.update(extra)
    return r


class UpwardTolerantDivergence(unittest.TestCase):
    def test_identical_records_are_green(self):
        ref = [rec([{"score": 3}, {"score": 5}])]
        self.assertIsNone(_first_divergence(ref, [rec([{"score": 3}, {"score": 5}])]))

    def test_added_field_is_tolerated_and_logged(self):
        """Der additive Zuwachs kippt die Pruefung nicht, bleibt aber sichtbar."""
        ref = [rec([{"score": 3}, {"score": 5}])]
        new_run = [rec([{"score": 3, "tiled_max_row": 2}, {"score": 5, "tiled_max_row": -1}])]
        added = []
        self.assertIsNone(_first_divergence(ref, new_run, added=added))
        self.assertEqual(
            sorted(set(added)),
            ["/state/players[0]/tiled_max_row", "/state/players[1]/tiled_max_row"],
        )

    def test_missing_field_stays_red(self):
        """Ein Rueckschritt ist kein Zuwachs -- die andere Richtung muss beissen."""
        ref = [rec([{"score": 3, "relevant": 7}])]
        new_run = [rec([{"score": 3}])]
        divergence = _first_divergence(ref, new_run)
        self.assertIsNotNone(divergence)
        self.assertIn("relevant", divergence[1])

    def test_changed_value_stays_red(self):
        ref = [rec([{"score": 3}])]
        new_run = [rec([{"score": 4}])]
        divergence = _first_divergence(ref, new_run)
        self.assertIsNotNone(divergence)
        self.assertIn("score", divergence[1])

    def test_changed_value_next_to_added_field_stays_red(self):
        """Der Zuwachs darf eine echte Abweichung nicht verdecken."""
        ref = [rec([{"score": 3}])]
        new_run = [rec([{"score": 4, "tiled_max_row": 2}])]
        divergence = _first_divergence(ref, new_run)
        self.assertIsNotNone(divergence)
        self.assertIn("score", divergence[1])

    def test_top_level_added_is_tolerated_but_missing_is_red(self):
        ref = [rec([{"score": 3}])]
        added = []
        self.assertIsNone(
            _first_divergence(ref, [rec([{"score": 3}], extra_field=1)], added=added)
        )
        self.assertEqual(added, ["/extra_field"])
        without_policy = [{"game_id": "probe_1", "state": {"players": [{"score": 3}]}}]
        divergence = _first_divergence(ref, without_policy)
        self.assertIsNotNone(divergence)
        self.assertEqual(divergence[1], "policy")

    def test_list_length_mismatch_stays_red(self):
        ref = [rec([{"score": 3}, {"score": 5}])]
        new_run = [rec([{"score": 3}])]
        divergence = _first_divergence(ref, new_run)
        self.assertIsNotNone(divergence)
        self.assertIn("LAENGE", divergence[1])

    def test_step_count_is_still_checked(self):
        ref = [rec([{"score": 3}]), rec([{"score": 4}])]
        new_run = [rec([{"score": 3}])]
        divergence = _first_divergence(ref, new_run)
        self.assertIsNotNone(divergence)
        self.assertEqual(divergence[1], "<schrittzahl>")


if __name__ == "__main__":
    unittest.main()
