# -*- coding: utf-8 -*-
"""Namensaufloesung KI-Modell -> Elo-Leiter (Nutzer-Meldung 2026-09-09: das
KI-Rating fehlte in der Oberflaeche).

`models/champion.txt` traegt den ONNX-Basisnamen ("v26-b01_brierbest"), die
Leiter in `evaluations/elo_history.csv` den Blocknamen ("v26-b01"). Seit dem
v24-Generationswechsel passte beides nicht mehr aufeinander, und der Ausfall
war still (kein Badge, ungewertete Partie ohne Hinweis).

Geprueft wird NUR die reine Namensfunktion -- kein CSV, keine Elo-Zahlen: die
bewegen sich mit jeder neuen Arena-Kante, ein Test darauf waere ein Test auf
den Messstand statt auf die Logik."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from player_profiles import _ladder_identities  # noqa: E402


class LadderIdentityTest(unittest.TestCase):
    def test_checkpoint_suffix_yields_block_name_as_fallback(self):
        self.assertEqual(_ladder_identities("v26-b01_brierbest"),
                         ["v26-b01_brierbest", "v26-b01"])
        self.assertEqual(_ladder_identities("v26-b01_best"),
                         ["v26-b01_best", "v26-b01"])

    def test_name_without_suffix_has_no_fallback(self):
        self.assertEqual(_ladder_identities("v26-b01"), ["v26-b01"])
        self.assertEqual(_ladder_identities("Heuristik"), ["Heuristik"])

    def test_own_name_is_always_tried_first(self):
        # v23-b01_brierbest und v19_2d_best stehen SELBST in der Leiter -- der
        # Rueckfall darf sie nicht verdraengen.
        for name in ("v23-b01_brierbest", "v19_2d_best"):
            self.assertEqual(_ladder_identities(name)[0], name)

    def test_bare_suffix_is_not_stripped_to_empty(self):
        self.assertEqual(_ladder_identities("_brierbest"), ["_brierbest"])

    def test_only_one_suffix_is_stripped(self):
        # "_brierbest" trifft zuerst; danach wird nicht weiter geschnitten.
        self.assertEqual(_ladder_identities("v9_best_brierbest"),
                         ["v9_best_brierbest", "v9_best"])


if __name__ == "__main__":
    unittest.main()
