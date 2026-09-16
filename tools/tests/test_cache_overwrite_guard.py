"""Der Ueberschreib-Schutz in `build_cache_parallel.merge` (2026-09-16).

WOGEGEN ER SCHUETZT, an einem echten Vorfall: am 2026-09-16 hat der Arm
v29-b04 den Monolithen des Arms v29-b03 ueberschrieben (1,15 GB). Ursache war
ein Knopf, den `tools/window_train_split.py` nicht an `window_cache_key`
durchreichte, wodurch b04 b03s Fenster-Schluessel als Ziel ausrechnete.
Gewarnt hat nichts; aufgefallen ist es einem Menschen an der Dateigroesse.

Diese Tests halten fest, dass ein Bau an einem fremden Datensatz ABBRICHT --
und dass er einen eigenen Cache weiterhin ersetzen darf, sonst waere jeder
Neubau blockiert.
"""
import os
import sys
import tempfile
import unittest

import h5py
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "engine", "py"))

from tools.build_cache_parallel import merge  # noqa: E402


class _Key:
    """Minimale Nachbildung von `WindowCacheKey` -- `merge` liest nur `.key`
    und `.key_full`."""

    def __init__(self, key):
        self.key = key
        self.key_full = key + "0" * (32 - len(key))
        self.files = []


def _part(path, n=3):
    with h5py.File(path, "w") as hf:
        hf.create_dataset("planes_packed", data=np.zeros((n, 4), dtype=np.uint8))


def _stamped(path, key, files_n=2800, env="MOSAIC_MOON_TARGET_SOURCE=played"):
    with h5py.File(path, "w") as hf:
        hf.create_dataset("planes_packed", data=np.zeros((1, 4), dtype=np.uint8))
        hf.attrs["mosaic_cache_key"] = key
        hf.attrs["mosaic_files_n"] = files_n
        hf.attrs["mosaic_env_fingerprint"] = env


class TestCacheOverwriteGuard(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="cacheguard_")
        self.parts = [os.path.join(self.dir, f"part{i}.h5") for i in range(2)]
        for p in self.parts:
            _part(p)
        self.target = os.path.join(self.dir, "target.h5")

    def test_foreign_dataset_aborts(self):
        """Der Kern: Zieldatei traegt einen ANDEREN Schluessel -> SystemExit,
        und die Datei bleibt unangetastet."""
        _stamped(self.target, "fd13f54061cd")
        size_before = os.path.getsize(self.target)
        with self.assertRaises(SystemExit) as ctx:
            merge(self.parts, self.target, window_key=_Key("4dd9f020b232"))
        message = str(ctx.exception)
        self.assertIn("UEBERSCHREIB-SCHUTZ", message)
        self.assertIn("fd13f54061cd", message)      # wem die Datei gehoert
        self.assertIn("4dd9f020b232", message)      # was dieser Lauf wollte
        self.assertIn("played", message)            # die Umgebung der Datei
        self.assertEqual(os.path.getsize(self.target), size_before,
                         "Die fremde Datei wurde trotz Abbruch veraendert.")

    def test_own_cache_may_be_replaced(self):
        """Gegenprobe, damit der Schutz kein Neubau-Verbot ist."""
        _stamped(self.target, "4dd9f020b232")
        merge(self.parts, self.target, window_key=_Key("4dd9f020b232"))
        with h5py.File(self.target, "r") as hf:
            self.assertEqual(hf["planes_packed"].shape[0], 6)   # 2 Teile a 3 Zeilen

    def test_unstamped_cache_is_replaced(self):
        """Ein Cache aus der Zeit vor der Praegung traegt kein Attribut. Dort
        abzubrechen waere eine Bremse ohne Befund -- er wird ersetzt."""
        _part(self.target, n=1)                                  # ohne Attribute
        merge(self.parts, self.target, window_key=_Key("4dd9f020b232"))
        with h5py.File(self.target, "r") as hf:
            self.assertEqual(hf["planes_packed"].shape[0], 6)

    def test_no_window_key_means_no_guard(self):
        """`merge` ohne `window_key` (Teil-Zusammenbau) laeuft unveraendert --
        der Schutz haengt am Schluessel, den dieser Lauf aufpraegen wuerde."""
        _stamped(self.target, "fd13f54061cd")
        merge(self.parts, self.target, window_key=None)
        with h5py.File(self.target, "r") as hf:
            self.assertEqual(hf["planes_packed"].shape[0], 6)


if __name__ == "__main__":
    unittest.main()
