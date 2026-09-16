# -*- coding: utf-8 -*-
"""Waechter: die PFADFORM der Dateiliste im Fenster-Schluessel muss bei
Zusammenfueger und Verbraucher DIESELBE sein -- absolut.

DIE FALLE (docs/pitfalls.md, Eintrag "Pfadform der Dateiliste", 2026-09-16):
`corpus_dataset.window_cache_key` nimmt `str(files)` ins Schluesselmaterial.
Damit bestimmt nicht der Datensatz allein den Schluessel, sondern auch, WIE die
Eintraege der Liste geschrieben sind. Dieselben Dateien ergeben drei
verschiedene Schluessel, je nach Form: Basename, `data/x.pkl`, absolut.

DER ZWEITE VORFALL DERSELBEN FAMILIE (2026-09-17 01:19, Arm v29-b06):
`tools/window_train_split.py` rechnete den Zielnamen aus ABSOLUTEN Pfaden
(fd13f54061cd), `tools/build_cache_incremental.py --merge-out` praegte in
DIESELBE Datei den Stempel 4dd9f020b232 (Form `data/x.pkl`, weil die Eintraege
aus `os.path.join(data_dir, basename)` kommen). Der `--cache-file`-Waechter in
`train.py` lehnte den frisch gebauten Monolithen ab -- zu Recht, die
Selbstauskunft der Datei passte nicht zum Verbraucher.

WAS DIESER TEST FESTNAGELT:
  1. Beide Zusammenfueger rechnen den Stempel durch EINE gemeinsame Funktion
     (`build_cache_parallel.window_key_for_entries`), und diese liefert genau
     den Schluessel, den `window_cache_key` ueber absolute Pfade liefert.
  2. Die drei Pfadformen liefern weiterhin drei verschiedene Rohschluessel --
     das ist die Falle selbst, dokumentiert statt behoben. Die Helferfunktion
     buegelt sie fuer alle drei Eingabeformen auf den absoluten Schluessel.
  3. Die Form des VERBRAUCHERS ist absolut: `config.DATA_DIR` ist ein absoluter
     Pfad, und `train.py` wie `tools/window_train_split.py` globben darueber.

NICHT Gegenstand dieses Tests: die eigentliche Reparatur, die Dateiliste im
Schluessel auf Basenames zu NORMALISIEREN. Sie entwertet jeden vorhandenen
Monolithen auf einen Schlag, gehoert an einen Generationswechsel und ist ein
Nutzer-Entscheid (docs/pitfalls.md). Dieser Test haelt nur die Uebereinstimmung
zwischen Stempler und Verbraucher, damit sie nicht ein drittes Mal
auseinanderlaeuft.
"""
import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "engine", "py"))

import corpus_dataset  # noqa: E402
from tools.build_cache_parallel import window_key_for_entries  # noqa: E402

# Dieselben Knoepfe in jedem Aufruf -- verglichen wird die PFADFORM, nichts
# sonst. Werte wie im v29-Rezept, damit der Test nicht auf Defaults ruht.
KNOBS = dict(value_target_variant="nortv", encoder="2d", conjunction_head=False)

BASENAMES = ["selfplay_a.pkl", "selfplay_b.pkl", "selfplay_c.pkl"]

# Die Umgebungsknoepfe, die `window_cache_key` selbst liest. Sie werden fuer
# die Dauer des Tests geleert: MOSAIC_DATA_EXCLUDE koennte die Testdateien
# herausfiltern und damit ALLE Formen auf die leere Liste einebnen -- der Test
# wuerde gruen, ohne etwas geprueft zu haben.
NEUTRALIZED_ENV = ("MOSAIC_DATA_EXCLUDE", "MOSAIC_CARRIER_MANIFEST",
                   "MOSAIC_SPECIAL_PLANES_OFF", "MOSAIC_MOON_TARGET_SOURCE")


class _Env:
    """Umgebungsknoepfe leeren und hinterher zurueckstellen."""

    def __enter__(self):
        self.saved = {k: os.environ.get(k) for k in NEUTRALIZED_ENV}
        for k in NEUTRALIZED_ENV:
            os.environ.pop(k, None)
        return self

    def __exit__(self, *exc):
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return False


class CacheKeyPathFormTest(unittest.TestCase):
    """Mini-Korpus: drei leere .pkl-Dateien in <tmp>/data. Der Schluessel liest
    die Dateien nicht, nur ihre Namen -- leer genuegt."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="cachekeyform_")
        self.data_dir = os.path.join(self.tmp, "data")
        os.makedirs(self.data_dir)
        for b in BASENAMES:
            open(os.path.join(self.data_dir, b), "wb").close()
        self.cwd_before = os.getcwd()
        # Der Zusammenfueger laeuft aus der Projektwurzel mit `--data-dir data`.
        # Deshalb ist <tmp> hier die Projektwurzel-Entsprechung.
        os.chdir(self.tmp)
        self.env = _Env().__enter__()

    def tearDown(self):
        self.env.__exit__(None, None, None)
        os.chdir(self.cwd_before)
        shutil.rmtree(self.tmp, ignore_errors=True)

    # --- die drei Formen, in denen eine Dateiliste im Baum vorkommt ----------

    def _form_basename(self):
        return list(BASENAMES)

    def _form_relative(self):
        """Die Form, die `build_cache_incremental._files` erzeugt:
        `os.path.join(data_dir, basename)` mit relativem `--data-dir data`."""
        return [os.path.join("data", b) for b in BASENAMES]

    def _form_absolute(self):
        """Die Form der Verbraucher: `glob(str(config.DATA_DIR / "*.pkl"))`."""
        return [os.path.join(self.data_dir, b) for b in BASENAMES]

    def _raw_key(self, files, data_dir="data"):
        return corpus_dataset.window_cache_key(data_dir, files, **KNOBS).key

    # --- Test 1: Stempel des Zusammenfuegers == Schluessel des Verbrauchers --

    def test_merger_stamp_equals_consumer_key(self):
        """Der Kern: was `build_cache_incremental --merge-out` aufpraegt, ist
        der Schluessel, den ein Verbraucher ueber absolute Pfade rechnet.

        Links die Eintragsform des Zusammenfuegers (`data/x.pkl`), rechts die
        des Verbrauchers (absolut). Vor dem 2026-09-17 standen hier
        4dd9f020b232 gegen fd13f54061cd.
        """
        stamp = window_key_for_entries("data", self._form_relative(), **KNOBS).key
        consumer = self._raw_key(self._form_absolute())
        self.assertEqual(
            stamp, consumer,
            "Stempel und Verbraucher-Schluessel weichen ab. Genau so trug am "
            "2026-09-17 die Datei .cache_fd13f54061cd.h5 den Stempel "
            "4dd9f020b232, und train.py --cache-file lehnte den frisch "
            "gebauten Monolithen ab. Die Zusammenfueger muessen den Stempel "
            "aus ABSOLUTEN Pfaden rechnen (window_key_for_entries).")

    def test_both_mergers_route_through_the_helper(self):
        """Damit die Uebereinstimmung nicht an einer Kopie haengt: BEIDE
        Zusammenfueger muessen die gemeinsame Funktion benutzen und den
        Stempel nicht selbst nachrechnen.

        Schlaegt dieser Test fehl, weil Code umgebaut wurde: von Hand pruefen,
        dass der Stempel weiterhin aus absoluten Pfaden entsteht, und den Test
        nachziehen -- nicht einfach loeschen.
        """
        for name in ("build_cache_incremental.py", "build_cache_parallel.py"):
            path = os.path.join(_ROOT, "tools", name)
            with open(path, encoding="utf-8") as fh:
                source = fh.read()
            self.assertIn(
                "window_key_for_entries(", source,
                f"tools/{name} benutzt die gemeinsame Stempel-Funktion nicht "
                f"mehr -- die Pfadform kann dort wieder eigene Wege gehen.")
            # Die Funktion selbst ruft `window_cache_key` -- genau einmal, in
            # build_cache_parallel.py. Sonst nirgends.
            expected = 1 if name == "build_cache_parallel.py" else 0
            self.assertEqual(
                source.count("window_cache_key("), expected,
                f"tools/{name} rechnet den Fenster-Schluessel wieder selbst. "
                f"Das ist die Bauform, die zweimal auseinandergelaufen ist "
                f"(2026-09-16 und 2026-09-17); er gehoert in "
                f"build_cache_parallel.window_key_for_entries.")

    # --- Test 2: die Falle selbst, und was die Helferfunktion damit macht ----

    def test_three_path_forms_give_three_different_keys(self):
        """Dokumentiert die Falle: derselbe Datensatz, drei Schreibweisen, drei
        Schluessel. Verschwindet dieser Unterschied eines Tages, ist die
        Normalisierung auf Basenames gebaut worden -- dann ist JEDER vorhandene
        Monolith entwertet, und das ist ein Nutzer-Entscheid, kein Nebenbefund.
        """
        keys = {
            "basename": self._raw_key(self._form_basename()),
            "relativ": self._raw_key(self._form_relative()),
            "absolut": self._raw_key(self._form_absolute()),
        }
        self.assertEqual(
            len(set(keys.values())), 3,
            "Die drei Pfadformen liefern nicht mehr drei verschiedene "
            "Schluessel: " + repr(keys) + ". Wenn das Absicht ist (Basename-"
            "Normalisierung), gehoert der Befund nach docs/pitfalls.md und "
            "STATUS.md -- er entwertet jeden Bestands-Monolithen.")

    def test_helper_normalizes_relative_and_absolute_input(self):
        """Die Helferfunktion buegelt die Eingabeform auf die absolute: egal ob
        sie `data/x.pkl` oder den vollen Pfad bekommt, es kommt derselbe
        Schluessel heraus."""
        absolute_key = self._raw_key(self._form_absolute())
        for label, entries in (("relativ", self._form_relative()),
                               ("absolut", self._form_absolute())):
            self.assertEqual(
                window_key_for_entries("data", entries, **KNOBS).key,
                absolute_key,
                f"Eingabeform {label} ergibt nicht den absoluten Schluessel.")

    def test_helper_resolves_basenames_against_the_working_directory(self):
        """Die dritte Eingabeform, mit ihrer Bedingung: `os.path.abspath`
        loest gegen das ARBEITSVERZEICHNIS auf, nicht gegen `data_dir`.
        Basenames ergeben den absoluten Schluessel also nur, wenn die Dateien
        im Arbeitsverzeichnis liegen.

        Das ist der Rest-Zacken der Reparatur und steht hier, damit er nicht
        aus Versehen als behoben gilt: ein Aufrufer, der Basenames uebergibt
        UND aus einem anderen Verzeichnis startet, bekommt wieder einen
        fremden Schluessel.
        """
        # (a) aus der Projektwurzel heraus: Basenames zeigen ins falsche
        #     Verzeichnis, also anderer Schluessel.
        absolute_key = self._raw_key(self._form_absolute())
        self.assertNotEqual(
            window_key_for_entries("data", self._form_basename(), **KNOBS).key,
            absolute_key,
            "abspath() loest Basenames offenbar nicht mehr gegen das "
            "Arbeitsverzeichnis auf -- Annahme dieses Tests geprueft.")
        # (b) aus dem data-Verzeichnis heraus: dieselben Basenames ergeben den
        #     absoluten Schluessel.
        os.chdir(self.data_dir)
        try:
            self.assertEqual(
                window_key_for_entries(self.data_dir, self._form_basename(),
                                       **KNOBS).key,
                absolute_key,
                "Basenames im eigenen Arbeitsverzeichnis ergeben nicht den "
                "absoluten Schluessel.")
        finally:
            os.chdir(self.tmp)

    # --- Test 3: die Form der Verbraucher ------------------------------------

    def test_consumers_compute_absolute_paths(self):
        """Die Gegenseite der Uebereinstimmung: `config.DATA_DIR` ist absolut,
        und beide Verbraucher globben darueber. `tools/window_train_split.py`
        hat nur ein `main()` und ist ohne Umbau nicht aufrufbar -- geprueft
        wird daher die Glob-Zeile selbst, samt ihrer Pfadform.

        Schlaegt das fehl, weil eine Zeile umformuliert wurde: von Hand
        nachsehen, ob die Form noch absolut ist, und den Test nachziehen.
        """
        import config
        self.assertTrue(
            os.path.isabs(str(config.DATA_DIR)),
            "config.DATA_DIR ist nicht absolut -- dann haengt der Schluessel "
            "am Arbeitsverzeichnis des Verbrauchers.")
        expectations = {
            "train.py": 'glob.glob(str(DATA_DIR / "*.pkl"))',
            os.path.join("tools", "window_train_split.py"):
                'glob.glob(os.path.join(str(DATA_DIR), "*.pkl"))',
        }
        for rel, snippet in expectations.items():
            with open(os.path.join(_ROOT, rel), encoding="utf-8") as fh:
                source = fh.read()
            self.assertIn(
                snippet, source,
                f"{rel} bildet seine Fensterliste nicht mehr mit "
                f"{snippet!r}. Die Pfadform des Verbrauchers ist damit "
                f"unbelegt -- von Hand pruefen und diesen Test nachziehen.")


if __name__ == "__main__":
    unittest.main()
