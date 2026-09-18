"""Der Fenster-Cache-Schluessel muss den Ablations-Schalter kennen.

Anlass (2026-09-14, PREREG_v29_window.md par.9): `MOSAIC_SPECIAL_PLANES_OFF`
stand im BLOCK-Schluessel (`file_cache_key.py`), aber nicht im FENSTER-
Schluessel. In v29 hatten b02 (Schalter an) und b03 (Schalter aus) damit
dieselbe Dateiliste und denselben Monolith-Namen -- b03 hat b02s Monolithen
ueberschrieben. Die Ergebnisse der Generation blieben unbeschaedigt, weil b02
fertig trainiert war, bevor b03 baute; eine Wiederholung in anderer
Reihenfolge waere STILL falsch gewesen.

Der Test sichert BEIDE Haelften des Fixes ab:
  1. mit Schalter an ist der Schluessel ein anderer (die eigentliche Falle),
  2. mit Schalter aus ist er UNVERAENDERT gegenueber dem Zustand vor dem Fix
     (deshalb der eingefrorene Literal unten: er wurde am 2026-09-14 auf dem
     Stand VOR dem Fix erzeugt, mit genau der Dateiliste dieses Tests).
"""

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "engine" / "py")):
    if p not in sys.path:
        sys.path.insert(0, p)

import corpus_dataset  # noqa: E402


# Feste, kuenstliche Dateiliste: `window_cache_key` liest die Dateien NICHT,
# nur ihre Namen gehen als `str(files)` ins Schluesselmaterial. Damit haengt
# der Test an keinem Korpus und laeuft in Millisekunden.
FILES = [
    "data/selfplay_test-a_0001.pkl",
    "data/selfplay_test-a_0002.pkl",
    "data/selfplay_test-b_0001.pkl",
]

# Wert auf dem Stand VOR dem Fix (Commit-Basis 49d85df), gleiche Dateiliste,
# Schalter nicht gesetzt. Aendert sich dieser Literal, hat jemand den
# DEFAULT-Schluessel bewegt und damit jeden Bestandscache entwertet -- das
# darf nur absichtlich passieren, mit Eintrag in der Prereg.
#
# ABSICHTLICH BEWEGT am 2026-09-17: "bea417f31e0e" -> "41b98a5d3890"
# (Nutzer-Entscheid, PREREG_rust_data_layer.md par.9b, Weg (1) aus par.9a).
# Der Fenster-Schluessel traegt seither UNBEDINGT die Merkmals-Formelversion
# (`config.FEATURE_FORMULA_VERSION`, Marker "+featfmt_a2phantom-20260912") und
# die Merkmals-Quelle ("+featsrc_record" bzw. "+featsrc_rust"). Nachgeprueft:
# das Schluesselmaterial ohne diese beiden Marker ergibt exakt den alten Wert
# "bea417f31e0e" -- es hat sich nichts sonst bewegt. Die Entwertung aller
# vorhandenen Monolithen ist die gewollte Folge; der Neubau faellt mit dem
# INPUT_SIZE-Wechsel fuer den Arm v29-b07 ohnehin an.
# Bewegt 2026-09-17 (zweiter Zug desselben Tags): INPUT_SIZE 794 -> 884 durch Abschnitt 17
# (Tiling-Projektion, Variante C, Arm v29-b07, PREREG_round_transition_search_sampling.md
# par.18/18.9); INPUT_SIZE steht im Block- und damit im Fenster-Schluessel. Vorher ba128e934a4a.
# Bewegt 2026-09-18: INPUT_SIZE 884 -> 888 durch Abschnitt 18 (geordnete eigene Designs, R2/P.16,
# PREREG_dome_return_order.md par.12.6/12.8/12.10); vorher 5fd616444e86 (884), davor ba128e934a4a (794).
KEY_WITH_SWITCH_OFF = "41b98a5d3890"


class WindowCacheKeyPlanesAblationTest(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.get("MOSAIC_SPECIAL_PLANES_OFF")
        os.environ.pop("MOSAIC_SPECIAL_PLANES_OFF", None)

    def tearDown(self):
        os.environ.pop("MOSAIC_SPECIAL_PLANES_OFF", None)
        if self._saved is not None:
            os.environ["MOSAIC_SPECIAL_PLANES_OFF"] = self._saved

    def _key(self):
        return corpus_dataset.window_cache_key("data", FILES).key

    def test_switch_on_yields_a_different_key(self):
        key_off = self._key()
        os.environ["MOSAIC_SPECIAL_PLANES_OFF"] = "1"
        key_on = self._key()
        self.assertNotEqual(
            key_off, key_on,
            "Ablation und Bestand teilen sich den Monolith-Namen -- genau die "
            "Kollision aus v29 (b03 ueberschrieb b02)",
        )

    def test_switch_off_keeps_the_legacy_key(self):
        self.assertEqual(
            self._key(), KEY_WITH_SWITCH_OFF,
            "der Default-Schluessel hat sich bewegt: jeder vorhandene Cache "
            "waere damit entwertet",
        )

    def test_zero_counts_as_off(self):
        # Dieselbe Semantik wie in Rust (features.rs::special_planes_off) und
        # im Block-Schluessel: gesetzt UND nicht "0".
        key_off = self._key()
        os.environ["MOSAIC_SPECIAL_PLANES_OFF"] = "0"
        self.assertEqual(self._key(), key_off)
        os.environ["MOSAIC_SPECIAL_PLANES_OFF"] = ""
        self.assertEqual(self._key(), key_off)


if __name__ == "__main__":
    unittest.main()
