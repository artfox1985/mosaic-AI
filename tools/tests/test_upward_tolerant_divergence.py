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


class ChipColorCanonicalisation(unittest.TestCase):
    """Waechter fuer die Farb-Normalisierung (Nutzer-Entscheid 2026-09-20, Weg a).

    Anlass: die Kanonisierung des Bonuschip-Vorrats aendert die SCHREIBWEISE der
    Farben im serialisierten Zustand, nicht das Spiel. Die eingefrorenen Golden
    Probes tragen die alte Schreibweise und meldeten deshalb ROT, obwohl ueber
    1.763 Schritte alle Zugfelder gleich waren (par.8e).

    Gemessen wird hier an BEIDEN Seiten, wie beim aufwaerts-toleranten Vergleich:
    dass die Normalisierung greift, wo sie soll, UND dass sie nicht greift, wo die
    Reihenfolge Bedeutung traegt. Der zweite Teil ist der wichtigere -- ein
    Suffix-Kriterium haette `moon_top_colors` mitsortiert und damit einen der
    neuen Suchknoten blind gemacht.
    """

    def _rec(self, state):
        return {"game_id": "probe_1", "state": state, "policy": [0.5, 0.5]}

    def test_chip_colors_are_order_insensitive(self):
        a = [self._rec({"factories": [{"bonus_chip": {"id": 6, "colors": ["schwarz", "blau"]}}]})]
        b = [self._rec({"factories": [{"bonus_chip": {"id": 6, "colors": ["blau", "schwarz"]}}]})]
        self.assertIsNone(_first_divergence(a, b))

    def test_unused_chip_colors_are_order_insensitive(self):
        a = [self._rec({"players": [{"unused_chip_colors": ["schwarz", "gelb"]}]})]
        b = [self._rec({"players": [{"unused_chip_colors": ["gelb", "schwarz"]}]})]
        self.assertIsNone(_first_divergence(a, b))

    def test_moon_top_colors_stay_order_sensitive(self):
        """Die Reihenfolge der Mondstapel-Koepfe IST der Zug (Aktionen 406-410)."""
        a = [self._rec({"moon_top_colors": ["rot", "blau"]})]
        b = [self._rec({"moon_top_colors": ["blau", "rot"]})]
        self.assertIsNotNone(_first_divergence(a, b))

    def test_row_colors_stay_order_sensitive(self):
        """`row_colors` ist die Farbe JE Musterreihe -- der Index traegt Bedeutung."""
        a = [self._rec({"players": [{"row_colors": ["rot", "blau"]}]})]
        b = [self._rec({"players": [{"row_colors": ["blau", "rot"]}]})]
        self.assertIsNotNone(_first_divergence(a, b))

    def test_a_different_chip_colour_is_still_red(self):
        """Normalisiert wird die REIHENFOLGE, nicht der Inhalt."""
        a = [self._rec({"factories": [{"bonus_chip": {"id": 6, "colors": ["schwarz", "blau"]}}]})]
        b = [self._rec({"factories": [{"bonus_chip": {"id": 6, "colors": ["schwarz", "rot"]}}]})]
        self.assertIsNotNone(_first_divergence(a, b))

    def test_canonicalisation_is_limited_to_two_fields(self):
        """Wer die Liste erweitert, faellt hier um -- und liest den Kopfkommentar."""
        from generator_repro_probe import CHIP_COLOR_FIELDS
        self.assertEqual(tuple(CHIP_COLOR_FIELDS), ("colors", "unused_chip_colors"))
