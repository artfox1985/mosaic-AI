# -*- coding: utf-8 -*-
"""Waechter: auch der NAMENSPFAD des Fenster-Caches prueft Name gegen Inhalt.

DIE LUECKE, die dieser Test schliesst (gefunden 2026-09-16): `--cache-file`
liess sich seit dem 2026-08-28 von der Datei ausweisen
(`corpus_dataset.verify_cache_file`), der NAMENSPFAD nicht -- dort wird die
Datei ueber den errechneten Schluessel gefunden (`data/.cache_<key>.h5`), und
der Dateiname war das einzige Argument. Er luegt aber nachweislich:
`.cache_35c6bd2b9bd2.h5` traegt intern `41bfd55372ea` (docs/pitfalls.md,
"Pfadform der Dateiliste"). Ein Lauf, der 35c6bd2b9bd2 errechnet, haette damit
einen FREMDEN Datensatz trainiert, ohne dass etwas gewarnt haette.

Grundmenge der Tests ist der Namenspfad, nicht die Option: kein `--cache-file`,
kein `cache_path_override`, nur ein `data/`-Ordner mit Korpusdateien und ein
Monolith, der unter dem passenden Namen liegt. Die Korpusdateien bleiben leer --
der Schluessel haengt an ihren NAMEN, gelesen werden sie nur, wenn kein Cache
gefunden wird.

Stil unittest (nicht pytest), weil der pre-commit-Hook `unittest discover`
laeuft (tools/hooks/pre-commit:26) und pytest im Projekt-Interpreter nicht
installiert ist.
"""
import os
import shutil
import sys
import tempfile
import unittest

import h5py
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "engine", "py"))

import corpus_dataset  # noqa: E402

# Der fremde Schluessel des echten Falls aus docs/pitfalls.md: dort sagt der
# Name 35c6bd2b9bd2 und die Datei 41bfd55372ea. Der "richtige" Name ist hier
# der in der Testumgebung errechnete Schluessel, nicht der von damals.
FOREIGN_KEY = "41bfd55372ea"


def _write_cache(path, *, window_key=None, stamped_key=None, rows=3):
    """Ein Mini-Monolith mit genau den Datasets, die der Ladeweg ohne Fallback
    liest. `window_key` praegt den echten Schluessel auf, `stamped_key` einen
    frei gewaehlten (der Luegen-Fall); ohne beides entsteht ein Alt-Cache ohne
    Schluessel-Attribut."""
    with h5py.File(path, "w") as hf:
        hf.create_dataset("states", data=np.zeros((rows, 7), dtype=np.float32))
        hf.create_dataset("policies", data=np.zeros((rows, 4), dtype=np.float32))
        hf.create_dataset("values", data=np.zeros(rows, dtype=np.float32))
        hf.create_dataset("masks", data=np.zeros((rows, 4), dtype=np.uint8))
        hf.create_dataset("moon_order_targets",
                          data=np.full((rows, 5), -1.0, dtype=np.float32))
        if window_key is not None:
            corpus_dataset.stamp_cache_key_attrs(hf, window_key)
        if stamped_key is not None:
            hf.attrs[corpus_dataset.CACHE_KEY_ATTR] = stamped_key
            hf.attrs[corpus_dataset.CACHE_KEY_FULL_ATTR] = (
                stamped_key + "0" * (32 - len(stamped_key)))


class TestNamePathCacheKeyGuard(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="namepathguard_")
        self.data_dir = os.path.join(self.root, "data")
        os.makedirs(self.data_dir)
        for name in ("selfplay_test_a.pkl", "selfplay_test_b.pkl"):
            with open(os.path.join(self.data_dir, name), "wb"):
                pass
        self.wk = corpus_dataset.window_cache_key(self.data_dir)
        self.assertEqual(len(self.wk.files), 2,
                         f"Fensterbildung unerwartet: {self.wk.files!r} -- steht "
                         f"MOSAIC_DATA_EXCLUDE in der Umgebung?")
        self.assertNotEqual(self.wk.key, FOREIGN_KEY)
        self.cache_path = os.path.join(self.data_dir, f".cache_{self.wk.key}.h5")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_foreign_key_under_correct_name_aborts(self):
        """Der Kern: die Datei liegt unter dem RICHTIGEN Namen, traegt aber
        einen fremden Schluessel -> SystemExit, und die Datei bleibt
        unangetastet (kein stiller Neubau, der sie ueberschreiben wuerde)."""
        _write_cache(self.cache_path, stamped_key=FOREIGN_KEY)
        size_before = os.path.getsize(self.cache_path)

        with self.assertRaises(SystemExit) as ctx:
            corpus_dataset.MosaicDataset(self.data_dir)

        message = str(ctx.exception)
        self.assertIn(f".cache_{self.wk.key}.h5", message)   # Dateiname
        self.assertIn(FOREIGN_KEY, message)                  # eingepraegter Schluessel
        self.assertIn(self.wk.key, message)                  # errechneter Schluessel
        self.assertIn("cache_doctor.py", message)            # der Weg zur Diagnose
        self.assertEqual(os.path.getsize(self.cache_path), size_before,
                         "Die fremde Datei wurde trotz Abbruch angetastet.")

    def test_matching_key_loads_unchanged(self):
        """Gegenprobe, damit der Waechter kein Ladeverbot ist: passt der
        eingepraegte Schluessel, wird dieselbe Datei geladen wie vorher."""
        _write_cache(self.cache_path, window_key=self.wk, rows=3)

        dataset = corpus_dataset.MosaicDataset(self.data_dir)

        self.assertEqual(len(dataset), 3)
        self.assertEqual(dataset.cache_path_h5, self.cache_path)
        # Die Option war nicht gesetzt -- der Manifest-Block bleibt leer
        # (train.py traegt ihn nur unter `--cache-file` nach).
        self.assertIsNone(dataset.cache_file_info)

    def test_unstamped_old_cache_aborts(self):
        """Alt-Cache ohne Schluessel-Attribut (vor dem 2026-08-28 gebaut):
        gleiches Verhalten wie im `--cache-file`-Pfad, also Ablehnung mit
        Verweis auf `stamp_cache_key.py`. Sein Fenster ist von aussen nicht
        feststellbar, und zwei Regeln fuer denselben Waechter waeren eine
        Einladung, den strengeren Pfad zu meiden."""
        _write_cache(self.cache_path)

        with self.assertRaises(SystemExit) as ctx:
            corpus_dataset.MosaicDataset(self.data_dir)

        message = str(ctx.exception)
        self.assertIn("stamp_cache_key.py", message)
        self.assertIn(corpus_dataset.CACHE_KEY_ATTR, message)


if __name__ == "__main__":
    unittest.main()
