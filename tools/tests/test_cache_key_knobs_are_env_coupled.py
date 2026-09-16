"""Waechter: jeder DATENWIRKSAME Knopf des Fenster-Schluessels muss aus der
Umgebung kommen koennen -- er darf keinen Default haben, der stillschweigend
den Schluessel eines ANDEREN Datensatzes ergibt.

DER VORFALL, den dieser Test kuenftig verhindert (2026-09-16): `moon_target_source`
war als Parameter mit Default "label" gebaut. Von den sieben Aufrufern von
`window_cache_key` reichten FUENF ihn nicht durch -- darunter
`tools/window_train_split.py` und `tools/build_cache_incremental.py`. Der Arm
v29-b04 bekam dadurch den Fenster-Schluessel des Arms v29-b03 und hat dessen
Monolithen ueberschrieben (1,15 GB), ohne eine einzige Warnung. Gefunden hat es
ein Mensch an der Dateigroesse.

DIE LEHRE, die dieser Test festhaelt: ein Knopf, den jeder Aufrufer einzeln
durchreichen muss, ist eine Bringschuld an sieben Stellen -- und eine davon
vergisst es. Ein Knopf, den die Schluesselfunktion selbst aus der Umgebung
holt, ist eine Holschuld an EINER Stelle. Die drei Alt-Knoepfe, die es schon
immer so machen (MOSAIC_CARRIER_MANIFEST, MOSAIC_SPECIAL_PLANES_OFF,
MOSAIC_DATA_EXCLUDE), haben dieses Problem nie gehabt.

Wer einen neuen Knopf hinzufuegt, hat zwei zulaessige Wege:
  (a) gar kein Parameter -- die Funktion liest die Umgebung selbst, oder
  (b) Parameter mit Default `None` = "frag die Umgebung" (der Weg, den
      `moon_target_source` seit dem 2026-09-16 geht).
Ein dritter Weg, ein Sachwert als Default, ist genau der Vorfall oben. Wer ihn
doch braucht, traegt ihn samt Begruendung in ALTBESTAND_MIT_SACHDEFAULT ein --
dann steht wenigstens im Baum, warum.
"""
import inspect
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "engine", "py"))

import corpus_dataset  # noqa: E402


# Knoepfe, die aus historischen Gruenden einen Sachwert als Default tragen.
# Sie sind NICHT vorbildlich -- sie stehen hier, damit der Test die Zahl der
# Altfaelle festnagelt und keine neuen dazukommen. Jeder Eintrag nennt, warum
# er bisher nicht umgestellt ist.
ALTBESTAND_MIT_SACHDEFAULT = {
    "value_target_variant":
        "Seit 2026-08-28 im Schluessel; alle sieben Aufrufer reichen ihn durch "
        "(geprueft 2026-09-16). Umstellung waere moeglich, ist aber ein "
        "eigener Schnitt -- der Default 'default' ist zudem der Name der "
        "Variante, nicht der eines anderen Datensatzes.",
    "encoder":
        "Wie oben; alle Aufrufer reichen ihn durch. Der Default 'flat' ist "
        "allerdings ein ECHTER anderer Datensatz als '2d' -- Wiedervorlage, "
        "sobald jemand den Schluessel ohnehin anfasst.",
    "conjunction_head":
        "Wie oben; alle Aufrufer reichen ihn durch, Default False ist der "
        "Bestandszustand.",
}


class TestCacheKeyKnobsAreEnvCoupled(unittest.TestCase):
    def test_moon_target_source_asks_the_environment(self):
        """Der Knopf aus dem Vorfall: Default muss None sein."""
        sig = inspect.signature(corpus_dataset.window_cache_key)
        p = sig.parameters["moon_target_source"]
        self.assertIsNone(
            p.default,
            "moon_target_source hat wieder einen Sachwert als Default. Genau so "
            "hat b04 am 2026-09-16 b03s Monolithen ueberschrieben: fuenf von "
            "sieben Aufrufern reichen den Knopf nicht durch, und der Default "
            "ist der Schluessel eines anderen Datensatzes.")

    def test_no_new_knob_with_a_concrete_default(self):
        """Neue Knoepfe muessen None-Default haben oder ausdruecklich als
        Altbestand eingetragen sein."""
        sig = inspect.signature(corpus_dataset.window_cache_key)
        keyword_only = [n for n, p in sig.parameters.items()
                        if p.kind is inspect.Parameter.KEYWORD_ONLY]
        verstoesse = []
        for name in keyword_only:
            p = sig.parameters[name]
            if p.default is None:
                continue                                  # (b): fragt die Umgebung
            if name in ALTBESTAND_MIT_SACHDEFAULT:
                continue                                  # bekannter Altfall
            verstoesse.append(f"{name}={p.default!r}")
        self.assertFalse(
            verstoesse,
            "Neuer Knopf mit Sachwert als Default: " + ", ".join(verstoesse) +
            ". Entweder Default None (dann die Umgebung im Rumpf abfragen, "
            "Vorbild moon_target_source) oder mit Begruendung in "
            "ALTBESTAND_MIT_SACHDEFAULT eintragen. Hintergrund: der Modulkopf "
            "dieses Tests.")

    def test_legacy_list_only_shrinks(self):
        """Die Altfall-Liste darf kleiner werden, nicht groesser -- sonst ist
        sie eine Ausrede statt einer Uebergangsregel."""
        sig = inspect.signature(corpus_dataset.window_cache_key)
        vorhanden = {n for n in ALTBESTAND_MIT_SACHDEFAULT
                     if n in sig.parameters}
        self.assertLessEqual(
            len(vorhanden), 3,
            "Mehr als drei Altfaelle -- die Liste waechst, statt abgebaut zu "
            "werden.")

    def test_env_coupling_actually_works(self):
        """Nicht nur die Signatur, sondern das Verhalten: ein Aufrufer, der den
        Knopf VERGISST, muss bei gesetzter Umgebung trotzdem den richtigen
        Schluessel bekommen. Das ist der eigentliche Schutz."""
        files = ["selfplay_test_a.pkl", "selfplay_test_b.pkl"]
        kw = dict(value_target_variant="nortv", encoder="2d",
                  conjunction_head=False)
        previous = os.environ.get("MOSAIC_MOON_TARGET_SOURCE")
        try:
            os.environ.pop("MOSAIC_MOON_TARGET_SOURCE", None)
            without_env = corpus_dataset.window_cache_key("data", files, **kw).key
            os.environ["MOSAIC_MOON_TARGET_SOURCE"] = "played"
            forgotten = corpus_dataset.window_cache_key("data", files, **kw).key
            explicit = corpus_dataset.window_cache_key(
                "data", files, moon_target_source="played", **kw).key
        finally:
            if previous is None:
                os.environ.pop("MOSAIC_MOON_TARGET_SOURCE", None)
            else:
                os.environ["MOSAIC_MOON_TARGET_SOURCE"] = previous
        self.assertEqual(forgotten, explicit,
                         "Vergessener Knopf ergibt einen anderen Schluessel als "
                         "der gesagte -- die Env-Kopplung greift nicht.")
        self.assertNotEqual(without_env, explicit,
                            "'played' und der Bestand teilen sich einen "
                            "Schluessel -- zwei Datensaetze unter einem Namen.")


if __name__ == "__main__":
    unittest.main()
