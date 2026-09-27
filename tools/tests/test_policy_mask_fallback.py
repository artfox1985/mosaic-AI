# -*- coding: utf-8 -*-
"""Code-Review 2026-09-26 #16: ein Record mit `fallback_random_action: true`
(die Netz-Suche fiel auf einen Zufallszug zurueck, self_play.rs
fallback_random_action_field) darf kein Policy-Ziel tragen.

Rein textnah (kein torch, kein Korpus), wie test_selfplay_manifest_flags.py:
die Maske sitzt mitten in der Record-Schleife von `corpus_dataset.py`, ein
echter Datensatz-Bau waere fuer einen Einzeiler unverhaeltnismaessig. Geprueft
wird, was die Zeile tragen muss:

* sie steht direkt hinter der `return_order_randomized`-Maske und VOR dem
  Anhaengen von `pol_w` (sonst wirkt sie nicht auf den gespeicherten Wert);
* ihre Bedingung kennt KEINE `_IGNORE_PTV`-Ausnahme -- die Ketten fahren
  MOSAIC_IGNORE_POLICY_TARGET_VALID=1, eine Maske ueber
  `policy_target_valid` waere dort wirkungslos (Review #16, Hinweis);
* sie vergleicht mit `is True`, damit Alt-Records ohne Feld (None) byte-gleich
  bleiben.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CORPUS_DATASET = REPO / "engine" / "py" / "corpus_dataset.py"


class FallbackMask(unittest.TestCase):
    def setUp(self):
        self.text = CORPUS_DATASET.read_text(encoding="utf-8")

    def test_mask_sits_between_return_order_mask_and_append(self):
        ret = self.text.index('if step.get("return_order_randomized") is True:')
        fb = self.text.index('if step.get("fallback_random_action") is True:')
        append = self.text.index("polw_l.append(np.float32(pol_w))")
        self.assertLess(ret, fb)
        self.assertLess(fb, append)
        self.assertEqual(self.text.count('step.get("fallback_random_action")'), 1)

    def test_mask_zeroes_pol_w_without_ptv_exception(self):
        m = re.search(r'( *)if step\.get\("fallback_random_action"\) is True:\n\1    pol_w = 0\.0\n',
                      self.text)
        self.assertIsNotNone(m, "Maske setzt pol_w nicht direkt auf 0.0")
        line = self.text[m.start():m.end()]
        self.assertNotIn("_IGNORE_PTV", line)

    def test_only_comments_between_the_two_masks(self):
        ret = self.text.index('if step.get("return_order_randomized") is True:')
        fb = self.text.index('if step.get("fallback_random_action") is True:')
        between = self.text[ret:fb].splitlines()[2:]  # nach Bedingung und pol_w-Zeile
        code = [ln for ln in between if ln.strip() and not ln.strip().startswith("#")]
        self.assertEqual(code, [], f"zwischen den Masken steht Code: {code}")


if __name__ == "__main__":
    unittest.main()
