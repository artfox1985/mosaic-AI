# -*- coding: utf-8 -*-
"""Code-Review 2026-09-26 #23: `corpus_io.dump_records` schreibt atomar
(temporaere Datei daneben, dann `os.replace`).

Geprueft:
* die Bytes sind DIESELBEN wie beim frueheren Direktschreiben -- der gzip-Kopf
  traegt den Dateinamen, und der darf nicht der temporaere sein (sonst waeren
  Korpora nicht mehr byte-reproduzierbar, die PID steckte im Kopf);
* nach dem Schreiben liegt keine temporaere Datei herum, und keine davon
  haette je `*.pkl` getroffen;
* ein Fehler beim Serialisieren hinterlaesst weder Ziel- noch Temporaerdatei
  und laesst eine vorhandene Zieldatei unangetastet.
"""
from __future__ import annotations

import gzip
import os
import pickle
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import corpus_io  # noqa: E402


def legacy_dump(path, obj):
    """Die Bauform VOR dem Fix (corpus_io.py bis 2026-09-26), als Referenz."""
    with open(path, "wb") as f:
        with gzip.GzipFile(fileobj=f, mode="wb", compresslevel=corpus_io.COMPRESS_LEVEL,
                           mtime=0) as g:
            pickle.dump(obj, g)


class Unpicklable:
    def __reduce__(self):
        raise RuntimeError("absichtlich nicht serialisierbar")


class AtomicDump(unittest.TestCase):
    RECORDS = [{"game_id": "g1", "state": [1, 2, 3]}, {"game_id": "g1", "winner": 0}]

    def test_bytes_equal_the_legacy_writer(self):
        with tempfile.TemporaryDirectory() as d:
            for target in (Path(d) / "selfplay_x_g10.pkl", str(Path(d) / "selfplay_y_g10.pkl")):
                legacy = Path(d) / "legacy" / Path(target).name
                legacy.parent.mkdir(exist_ok=True)
                legacy_dump(legacy, self.RECORDS)
                corpus_io.dump_records(target, self.RECORDS)
                self.assertEqual(Path(target).read_bytes(), legacy.read_bytes(), str(target))
                self.assertEqual(corpus_io.load_records(target), self.RECORDS)

    def test_no_temp_file_left_and_none_matches_pkl(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "selfplay_x_g10.pkl"
            corpus_io.dump_records(target, self.RECORDS)
            self.assertEqual(sorted(os.listdir(d)), ["selfplay_x_g10.pkl"])
            tmp = corpus_io._temp_path_for(target)
            self.assertTrue(os.path.basename(tmp).startswith("."))
            self.assertFalse(tmp.endswith(".pkl"))

    def test_failed_write_leaves_existing_target_untouched(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "selfplay_x_g10.pkl"
            corpus_io.dump_records(target, self.RECORDS)
            before = target.read_bytes()
            with self.assertRaises(RuntimeError):
                corpus_io.dump_records(target, [Unpicklable()])
            self.assertEqual(target.read_bytes(), before)
            self.assertEqual(sorted(os.listdir(d)), ["selfplay_x_g10.pkl"])

    def test_uncompressed_path_is_atomic_too(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "plain.pkl"
            corpus_io.dump_records(target, self.RECORDS, compress=False)
            self.assertEqual(corpus_io.load_records(target), self.RECORDS)
            self.assertEqual(sorted(os.listdir(d)), ["plain.pkl"])


if __name__ == "__main__":
    unittest.main()
