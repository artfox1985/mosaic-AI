# -*- coding: utf-8 -*-
"""Jeder Knopf, der die ZIELE oder EINGABEN im Cache veraendert, steht im
Fenster-Cache-Schluessel.

Anlass (2026-09-14, v29): `MOSAIC_SPECIAL_PLANES_OFF` aenderte die
Planes-Kanaele, stand aber nur im BLOCK-Schluessel (`file_cache_key.py`) und
nicht im Fenster-Schluessel (`corpus_dataset.py::window_cache_key`). Folge: b02
(Schalter an) und b03 (Schalter aus) hatten dieselbe Dateiliste, damit denselben
Monolith-NAMEN -- b03 hat b02s Monolithen ueberschrieben. Die Ergebnisse jener
Generation sind unbeschaedigt, aber eine Wiederholung in anderer Reihenfolge
waere STILL falsch gewesen: der zweite Lauf haette den Monolithen des ersten
geladen und nichts haette gewarnt.

WARUM DIE PRUEFUNG BEIM LADEN NICHT REICHT: der Cache traegt seinen Schluessel
mit sich und `--cache-file` prueft ihn. Das faengt einen FALSCHEN Cache. Es
faengt NICHT den Fall, dass zwei verschiedene Datensaetze denselben Schluessel
bekommen -- dann ist die Pruefung gruen und der Inhalt trotzdem der falsche.
Die einzige Abwehr ist, dass jeder datenveraendernde Knopf im Schluessel steht.

WAS DIESER TEST TUT: er haelt eine kuratierte Liste solcher Knoepfe und prueft,
dass jeder davon im Quelltext von `window_cache_key` vorkommt -- entweder als
Variable im Schluesselmaterial oder als bedingter Marker. Rein textnah, kein
Import, kein Korpus, pre-commit-tauglich.

WER EINEN NEUEN DATEN-KNOPF BAUT, traegt ihn hier ein. Ein Knopf, der die Daten
NICHT veraendert (reiner Such- oder Laufzeitknopf), gehoert mit Begruendung in
NOT_IN_KEY -- dann sagt die Liste selbst, warum er fehlen darf.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CORPUS_DATASET = REPO / "engine" / "py" / "corpus_dataset.py"
FILE_CACHE_KEY = REPO / "engine" / "py" / "file_cache_key.py"

# Knopf -> was er an den GECACHTEN Daten aendert. Jeder Eintrag MUSS im
# Quelltext von `window_cache_key` auftauchen.
DATEN_KNOEPFE = {
    "INPUT_SIZE": "Breite des Flachvektors -- andere Eingabe je Sample",
    "NUM_ACTIONS": "Breite des Policy-Ziels",
    "VALUE_SCHEMA_VERSION": "Aufbau der Wertziele",
    "TD_LAMBDA": "Bootstrap-Blend wird VOR dem Caching eingerechnet",
    "value_target_variant": "rtv/nortv-Override wird VOR dem Caching eingerechnet",
    "POLICY_TARGET_SHARPEN_EXPONENT": "Form des Policy-Ziels",
    "_special_planes_off_key": "Ablation der Spezialfeld-Kanaele 77/78 (v29-b02)",
    "policy_carrier_set": "welche Dateien Policy tragen -- anderer Traegersatz, andere Ziele",
    "LEGACY_STRETCHED_PREFIXES": "entstauchte gegen native Bootstrap-Ziele",
    "moon_target_source": "Ziel des moon-Kopfs: No-Op-Label gegen Suchverteilung (v29-b04)",
}

# Knoepfe, die in BEIDEN Schluesseln stehen muessen: der Wert steckt schon in den
# BLOECKEN je Datei, nicht erst im zusammengefuegten Monolithen. Fehlt der
# Block-Schluessel, laedt ein neuer Arm die Bloecke des alten -- und der neue
# Fenster-Schluessel taeuscht dabei einen frischen Datensatz vor.
BOTH_KEYS = {
    "_special_planes_off_key": "Planes-Kanaele 77/78 stecken je Datei im Block",
    "moon_target_source": "moon_order_targets stecken je Datei im Block (v29-b04)",
}

# Knoepfe, die BEWUSST nicht im Fenster-Schluessel stehen, mit Grund.
NOT_IN_KEY = {
    "MOSAIC_MOON_ORDER_VARIANTS": "reiner SUCH-Knopf, wirkt in Arena/Referee, nie im Cache",
    "MOSAIC_MOON_ORDER_SEARCH_SIMS": "wie oben -- Budget der Nachsuche, kein Datenfeld",
    "MOSAIC_MOON_ORDER_SEARCH_SCALE": "wie oben (par.11, gestrichen)",
    "MOSAIC_RETURN_ORDER_MODE": "Such-/GUI-Knopf; veraendert Zuege, nicht die Kodierung",
    "moon_loss_weight": "GEWICHT im Loss, kein Datenfeld -- b05 laeuft bewusst auf b03s Monolith",
}


class WindowKeyCoversDataKnobs(unittest.TestCase):
    def setUp(self):
        text = CORPUS_DATASET.read_text(encoding="utf-8")
        start = text.index("def window_cache_key(")
        # bis zum naechsten Top-Level-def
        rest = text[start + 10:]
        end = start + 10 + (rest.index("\ndef ") if "\ndef " in rest else len(rest))
        self.body = text[start:end]

    def test_every_data_knob_appears_in_the_window_key(self):
        fehlend = [k for k in DATEN_KNOEPFE if k not in self.body]
        self.assertEqual(
            fehlend, [],
            "Diese datenveraendernden Knoepfe fehlen im Fenster-Cache-Schluessel. Zwei "
            "Datensaetze bekaemen denselben Monolith-Namen, und die Pruefung beim Laden "
            f"waere GRUEN: {[(k, DATEN_KNOEPFE[k]) for k in fehlend]}",
        )

    def test_block_level_knobs_are_in_the_per_file_key_too(self):
        """Wer die BLOECKE veraendert, muss auch im Block-Schluessel stehen.

        Sonst laedt ein neuer Arm die Bloecke des alten. Der Fenster-Schluessel
        allein reicht nicht: er benennt nur den zusammengefuegten Monolithen,
        und der wird AUS den (falschen) Bloecken gebaut -- das Ergebnis sieht
        frisch aus und traegt die alten Ziele.
        """
        block = FILE_CACHE_KEY.read_text(encoding="utf-8")
        fehlend = [k for k in BOTH_KEYS if k not in block]
        self.assertEqual(
            fehlend, [],
            "Diese Knoepfe veraendern den Inhalt der BLOECKE, fehlen aber im "
            f"Block-Schluessel: {[(k, BOTH_KEYS[k]) for k in fehlend]}",
        )
        # und im Fenster-Schluessel ebenso
        fehlend_w = [k for k in BOTH_KEYS if k not in self.body]
        self.assertEqual(
            fehlend_w, [],
            f"Im Fenster-Schluessel fehlen: {fehlend_w}",
        )

    def test_exceptions_are_documented_and_really_absent(self):
        """Was als 'nicht im Schluessel' gefuehrt wird, darf dort auch nicht auftauchen."""
        unerwartet = [k for k in NOT_IN_KEY if k in self.body]
        self.assertEqual(
            unerwartet, [],
            "Diese Knoepfe stehen als bewusste Ausnahme in NOT_IN_KEY, tauchen aber "
            f"im Schluessel auf -- Liste oder Code korrigieren: {unerwartet}",
        )

    def test_key_material_is_a_single_expression(self):
        """Der Schluessel wird an EINER Stelle gebaut; bedingte Marker haengen daran.

        Faellt dieser Test, ist der Aufbau umgebaut worden -- dann ist auch die
        Textsuche oben nicht mehr verlaesslich und dieser Waechter braucht eine
        neue Bauform.
        """
        self.assertIn("cache_key_material = (", self.body)
        self.assertTrue(
            re.search(r"cache_key_material \+= ", self.body),
            "erwartet mindestens einen bedingten Marker (`cache_key_material += ...`)",
        )


if __name__ == "__main__":
    unittest.main()
