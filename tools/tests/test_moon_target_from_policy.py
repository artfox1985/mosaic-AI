# -*- coding: utf-8 -*-
"""Das Ziel des `moon`-Kopfs aus der Suchverteilung (Arm v29-b04).

`PREREG_moon_stack_order.md` par.12.1. Geprueft wird `moon_target_from_policy`
(engine/py/corpus_dataset.py) -- die Funktion, die bei
`--moon-target-source played` das No-Op-Label ersetzt.

WARUM DIESE TESTS: die Funktion trifft zwei Entscheidungen, und beide koennen
still falsch sein. Erstens muss sie die GESPIELTE Basis-Aktion finden (die mit
der groessten Gesamtmasse, nicht irgendeine). Zweitens darf sie innerhalb der
Basis nicht die erste, sondern die WAHRSCHEINLICHSTE Reihenfolge nehmen -- sonst
liefert sie wieder die kanonische, und der ganze Arm waere ein zweites No-Op.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))
from corpus_dataset import moon_target_from_policy  # noqa: E402


def stone(colour, factory, row, order, prob):
    return {"action": {"type": "stone", "color": colour, "factory_index": factory,
                       "row": row, "moon_order": list(order)}, "prob": prob}


class MoonTargetFromPolicy(unittest.TestCase):
    def test_picks_the_most_visited_order_within_the_played_base(self):
        step = {"policy": [
            stone("schwarz", 0, 4, ["tuerkis", "rot"], 0.5864),
            stone("schwarz", 0, 4, ["rot", "tuerkis"], 0.2104),
        ]}
        self.assertEqual(moon_target_from_policy(step), ["tuerkis", "rot"])

    def test_not_simply_the_first_entry(self):
        """Die kanonische Reihenfolge steht zuerst -- gewaehlt wird trotzdem die haeufigere."""
        step = {"policy": [
            stone("rot", 1, 2, ["blau", "gelb"], 0.10),
            stone("rot", 1, 2, ["gelb", "blau"], 0.70),
        ]}
        self.assertEqual(moon_target_from_policy(step), ["gelb", "blau"])

    def test_chooses_the_base_with_the_largest_total_mass(self):
        """Zwei Basis-Aktionen: die Reihenfolge kommt aus der SCHWEREREN."""
        step = {"policy": [
            stone("rot", 1, 2, ["blau", "gelb"], 0.05),
            stone("rot", 1, 2, ["gelb", "blau"], 0.05),
            stone("blau", 3, 5, ["rot", "schwarz"], 0.60),
            stone("blau", 3, 5, ["schwarz", "rot"], 0.30),
        ]}
        self.assertEqual(moon_target_from_policy(step), ["rot", "schwarz"])

    def test_returns_none_without_moon_orders(self):
        self.assertIsNone(moon_target_from_policy({"policy": []}))
        self.assertIsNone(moon_target_from_policy(
            {"policy": [{"action": {"type": "dome", "tile_id": 3}, "prob": 1.0}]}))
        self.assertIsNone(moon_target_from_policy(
            {"policy": [stone("rot", 0, 1, [], 1.0)]}))

    def test_ignores_non_stone_actions(self):
        step = {"policy": [
            {"action": {"type": "dome", "tile_id": 7}, "prob": 0.9},
            stone("gelb", 2, 3, ["rot", "blau"], 0.1),
        ]}
        self.assertEqual(moon_target_from_policy(step), ["rot", "blau"])


if __name__ == "__main__":
    unittest.main()
