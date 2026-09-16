# -*- coding: utf-8 -*-
"""Waechter fuer `tools/cache_doctor.py` -- die fuenf Defekte der Abnahme vom
2026-09-16, je einer pro Test.

Die Abnahme fand elf Defekte; fuenf davon sind hier festgenagelt, weil sie den
Doktor zu einer FALSCHAUSKUNFT gemacht haben und nicht bloss zu einer
haesslichen Zeile:

  1. HEX_RE traf `.cache_<key>.h5` nicht (der Unterstrich ist ein Wortzeichen,
     `\\b` greift dort nicht) -- belegte Caches hiessen "VERWAIST".
  2. Die Statusleiter kannte keine VAL-Caches, obwohl `train.py` in jedem Lauf
     mit `val_frac > 0` einen zweiten Monolithen aus der Val-Liste baut, den
     KEIN Manifest nennt.
  3. `hat_laufzeit` wurde erhoben und nie ausgewertet -- der Cache des gerade
     laufenden Trainings hiess "VERWAIST".
  4. Ein Bau-Artefakt, das `merge_out` und `cache_key` widerspruechlich fuehrt,
     blieb stumm, obwohl der Doktor beide Felder liest.
  5. Die Listen-Eindeutigkeit war strukturell tot, weil jeder Lauf eine
     inhaltsgleiche Kopie derselben Liste schreibt (vier byte-gleiche
     Trainingslisten im v29-Fenster).

Grundmenge jedes Tests ist ein eigener tmp-Baum mit `data/`, `models/` und
`evaluations/artifacts/` -- nie der echte Projektbaum: der Doktor liest dort
1-GB-Monolithen, und ein Test, der von der Lage im Repo abhaengt, ist kein
Waechter, sondern eine Momentaufnahme.

Die HDF5-Attributnamen sind NICHT geraten, sondern aus
`corpus_dataset.stamp_cache_key_attrs` uebernommen (CACHE_KEY_ATTR
'mosaic_cache_key', CACHE_KEY_FULL_ATTR 'mosaic_cache_key_full', dazu
'mosaic_cache_key_attrs_version', 'mosaic_files_n', 'mosaic_files_first',
'mosaic_files_last', 'mosaic_env_fingerprint').

Stil unittest (nicht pytest), weil der pre-commit-Hook `unittest discover -s
tools/tests` laeuft und pytest im Projekt-Interpreter nicht installiert ist.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

import h5py
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import cache_doctor  # noqa: E402

VAL_FILES = [f"selfplay_v28-b02-policy_20260913_12{i:02d}_g{i * 10}.pkl" for i in range(12)]
TRAIN_FILES = [f"selfplay_v27-b01-policy_20260910_09{i:02d}_g{i * 10}.pkl" for i in range(30)]


def write_list(path: Path, names: list, header: str | None = None) -> None:
    """Dateiliste wie `window_train_split.py` sie schreibt: optionale
    Kommentarzeile, dann ein Basisname je Zeile."""
    with open(path, "w", encoding="utf-8") as fh:
        if header:
            fh.write(f"# {header}\n")
        for n in names:
            fh.write(n + "\n")


def write_cache(path: Path, key: str, names: list, fingerprint: str | None = None) -> None:
    """Mini-Monolith mit genau den Attributen, die
    `corpus_dataset.stamp_cache_key_attrs` aufpraegt."""
    names = sorted(names)
    with h5py.File(path, "w") as hf:
        hf.create_dataset("values", data=np.zeros((len(names),), dtype=np.float32))
        hf.attrs["mosaic_cache_key"] = key
        hf.attrs["mosaic_cache_key_full"] = key + "0" * (32 - len(key))
        hf.attrs["mosaic_cache_key_attrs_version"] = 1
        hf.attrs["mosaic_files_n"] = len(names)
        hf.attrs["mosaic_files_first"] = names[0]
        hf.attrs["mosaic_files_last"] = names[-1]
        if fingerprint is not None:
            hf.attrs["mosaic_env_fingerprint"] = fingerprint


def write_manifest(path: Path, version: str, run_ts: str, *, with_runtime: bool,
                   cli: dict) -> None:
    """Trainings-Manifest in der Form, die `train.py` schreibt: `laufzeit`
    kommt erst nach Lauf-Ende dazu."""
    d = {"version": version, "run_timestamp": run_ts, "cli_args": cli,
         "corpus_composition": {}, "policy_carriers": {}}
    if with_runtime:
        d["laufzeit"] = {"wanduhr_s": 1.0, "cpu_s": 1.0, "threads": 1, "s_je_partie": None}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False)


def ts_ago(seconds: float) -> str:
    """`run_timestamp` im Manifest-Format, `seconds` Sekunden in der
    Vergangenheit."""
    return time.strftime(cache_doctor.MANIFEST_TS_FMT,
                         time.localtime(time.time() - seconds))


class CacheDoctorTreeTest(unittest.TestCase):
    """Gemeinsamer tmp-Baum; jeder Test baut sich seine Lage selbst."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="cache_doctor_test_"))
        self.data = self.tmp / "data"
        self.models = self.tmp / "models"
        self.artifacts = self.tmp / "evaluations" / "artifacts"
        for d in (self.data, self.models, self.artifacts):
            d.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def report(self) -> dict:
        # probe_processes=False: der PowerShell-Prozessblick ist eine Gegenprobe
        # fuer den Bediener, kein Teil der Zuordnung -- ein Test darf nicht von
        # der Prozessliste der Maschine abhaengen.
        return cache_doctor.build_report(str(self.data), self.tmp, quiet=True,
                                         probe_processes=False)

    def cache_row(self, rep: dict, filename: str) -> dict:
        rows = [c for c in rep["caches"] if c["datei"] == filename]
        self.assertEqual(len(rows), 1, f"{filename} nicht genau einmal im Bericht")
        return rows[0]

    # --- Defekt 2: HEX_RE ------------------------------------------------
    def test_hex_re_matches_cache_name_in_backticks(self) -> None:
        """`\\b[0-9a-f]{12,32}\\b` traf `.cache_7ebef2449837.h5` NICHT, weil der
        Unterstrich davor ein Wortzeichen ist -- genau die Form, in der ein
        Schluessel im Baum steht."""
        line = "Val-Cache `.cache_7ebef2449837.h5` (b01) liegt noch in data/."
        self.assertIn("7ebef2449837", cache_doctor.HEX_RE.findall(line))
        # Gegenprobe: ein 40-stelliger git-Hash wird weiterhin NICHT als
        # Cache-Schluessel gelesen (die Lookarounds verlangen beidseitig ein
        # Nicht-Hex-Zeichen).
        self.assertEqual(
            cache_doctor.HEX_RE.findall("commit 0d080491aa11bb22cc33dd44ee55ff6677889900"),
            [])

    # --- Defekt 1: VAL-Caches -------------------------------------------
    def test_val_cache_is_not_an_orphan(self) -> None:
        """Ein Monolith, dessen Attribute zu einer `window_*_val.txt` passen,
        ist der VAL-Cache eines Laufs -- kein Manifest nennt seinen Schluessel,
        und das ist die Bauweise von train.py, kein Defekt."""
        write_list(self.data / "window_vtest_val.txt", VAL_FILES)
        write_cache(self.data / ".cache_aaaabbbbcccc.h5", "aaaabbbbcccc", VAL_FILES,
                    fingerprint="MOSAIC_MOON_TARGET_SOURCE=played;MOSAIC_VAL_POOL=^selfplay_v28-")
        write_manifest(self.models / "manifest_train_vtest-b01_x.json", "vtest-b01",
                       ts_ago(4 * 3600), with_runtime=True,
                       cli={"val_frac": 0.05, "val_pool": "^selfplay_v28-",
                            "moon_target_source": "played", "encoder": "2d",
                            "value_target_variant": "nortv",
                            "file_list": "data/window_vtest.txt", "cache_file": None})
        row = self.cache_row(self.report(), ".cache_aaaabbbbcccc.h5")
        self.assertEqual(row["status"], "val-cache")
        self.assertTrue(row["val_cache"])
        self.assertEqual(row["arme"], ["vtest-b01"])
        kinds = [b["art"] for b in row["belege"]]
        self.assertIn("val-zu-vtest-b01", kinds)

    # --- Defekt 3: laufender Lauf ---------------------------------------
    def test_manifest_without_runtime_block_means_running(self) -> None:
        """Manifest ohne `laufzeit`-Block plus frischer `run_timestamp` =
        laufender Lauf. Seine Caches duerfen weder "VERWAIST" heissen noch ein
        GELB bekommen."""
        write_cache(self.data / ".cache_1111aaaa2222.h5", "1111aaaa2222", TRAIN_FILES)
        write_manifest(self.models / "manifest_train_vtest-b09_x.json", "vtest-b09",
                       ts_ago(600), with_runtime=False,
                       cli={"val_frac": 0.05, "val_pool": None,
                            "moon_target_source": "played", "encoder": "2d",
                            "value_target_variant": "nortv",
                            "file_list": "data/window_vtest.txt",
                            "cache_file": "data/.cache_1111aaaa2222.h5"})
        rep = self.report()
        row = self.cache_row(rep, ".cache_1111aaaa2222.h5")
        self.assertTrue(row["status"].startswith("LAEUFT"), row["status"])
        self.assertIn("vtest-b09", row["status"])
        self.assertEqual(len(rep["laufende_manifeste"]), 1)
        yellow = [f for f in rep["befunde"]
                if f["schwere"] == "GELB" and f.get("datei") == row["datei"]]
        self.assertEqual(yellow, [])
        # Gegenprobe: dasselbe Manifest MIT laufzeit-Block laeuft nicht mehr.
        write_manifest(self.models / "manifest_train_vtest-b09_x.json", "vtest-b09",
                       ts_ago(600), with_runtime=True,
                       cli={"val_frac": 0.05, "val_pool": None,
                            "moon_target_source": "played", "encoder": "2d",
                            "value_target_variant": "nortv",
                            "file_list": "data/window_vtest.txt",
                            "cache_file": "data/.cache_1111aaaa2222.h5"})
        row2 = self.cache_row(self.report(), ".cache_1111aaaa2222.h5")
        self.assertEqual(row2["status"], "zugeordnet")

    # --- Defekt 9: Bau-Artefakt gegen sich selbst -----------------------
    def test_build_artifact_self_contradiction_is_red(self) -> None:
        """`merge_out .cache_fd13f54061cd.h5` neben `cache_key 4dd9f020b232` im
        SELBEN Artefakt: der Name ist der Schluessel, also kann nur eines von
        beiden stimmen."""
        with open(self.artifacts / "cache_build_x.json", "w", encoding="utf-8") as fh:
            json.dump({"cache_key": "4dd9f020b232",
                       "merge_out": "data/.cache_fd13f54061cd.h5",
                       "file_list": "data/window_vtest_train.txt"}, fh)
        rep = self.report()
        red = [f for f in rep["befunde"] if f["art"] == "bau_artefakt_widerspruch"]
        self.assertEqual(len(red), 1, [f["art"] for f in rep["befunde"]])
        self.assertEqual(red[0]["schwere"], "ROT")
        self.assertIn("4dd9f020b232", red[0]["text"])
        self.assertIn("fd13f54061cd", red[0]["text"])

    # --- Defekt 5: inhaltsgleiche Listenkopien --------------------------
    def test_identical_lists_count_as_one_candidate(self) -> None:
        """Vier byte-gleiche Kopien derselben Liste sind EIN Kandidat. Vorher
        war jeder Cache dadurch "MEHRDEUTIG", und der ROT-Detektor
        'listenkonflikt' konnte nie feuern -- er haengt an
        `listen_eindeutig`."""
        header = "Trainingsanteil von data/window_vtest.txt (val_frac 0.05)"
        for name in ("window_vtest_train.txt", "window_vtest_b04_train.txt",
                     "window_vtest_vtest-b02_train.txt", "window_vtest_vtest-b03_train.txt"):
            write_list(self.data / name, TRAIN_FILES, header=header)
        write_cache(self.data / ".cache_3333cccc4444.h5", "3333cccc4444", TRAIN_FILES)
        rep = self.report()
        row = self.cache_row(rep, ".cache_3333cccc4444.h5")
        self.assertEqual(len(row["passende_listen"]), 4)
        self.assertEqual(len(row["passende_listen_gruppen"]), 1)
        self.assertTrue(row["listen_eindeutig"])
        self.assertEqual(rep["listen_gruppen_n"], 1)
        self.assertEqual(rep["listen_n"], 4)

        # Und jetzt ist der ROT-Detektor scharf: ein Split-Artefakt, das einer
        # dieser Listen einen ANDEREN Schluessel gibt, ist ein Konflikt.
        with open(self.artifacts / "vtest_split.txt", "w", encoding="utf-8") as fh:
            fh.write("Fenster 30 Dateien, Val 0\n")
            fh.write("Fenster-Schluessel des Trainingsanteils: 9999dddd8888\n")
            fh.write("Trainingsliste: data/window_vtest_train.txt\n")
        rep2 = self.report()
        row2 = self.cache_row(rep2, ".cache_3333cccc4444.h5")
        self.assertIn("listenkonflikt", [b["art"] for b in row2["belege"]])
        conflicts = [f for f in rep2["befunde"] if f["art"] == "listenkonflikt"]
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["schwere"], "ROT")


class CacheDoctorFormatTest(unittest.TestCase):
    """Die Zahl im Bericht: deutsches Dezimalkomma, richtige Einheit."""

    def test_size_reads_as_a_german_number(self) -> None:
        # `{:,.0f} MB` hatte "2,372 MB" gedruckt -- deutsch gelesen 2,372.
        self.assertEqual(cache_doctor._size(2372.0), "2,32 GiB")
        self.assertEqual(cache_doctor._size(57.7), "57,7 MiB")
        self.assertNotIn(".", cache_doctor._size(2372.0))


if __name__ == "__main__":
    unittest.main(verbosity=2)
