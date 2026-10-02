# -*- coding: utf-8 -*-
"""E4-Block (Angebots-Bedarfs-Sicht), Python-Seite: Spiegel, Knopf, Schaltstelle.

Bezug: `engine/src/supply_demand.rs` (Regel und Zuschnitt), `engine/py/
supply_demand_features.py` (Knopf und Wheel-Aufruf), `PREREG_v34_window.md`
par.3 (Trainings-Arm E4).

Was hier geprueft wird, laeuft OHNE Wheel und OHNE torch (pre-commit-tauglich):
  1. die Python-Spiegel der Rust-Konstanten stimmen mit dem Rust-Quelltext,
  2. der Knopf hat die Semantik "exakt 1",
  3. die gemeinsame Schaltstelle `append_supply_demand` haengt nur bei E4-Breite
     an, prueft die Basislaenge und behandelt einen fehlenden Export als harten
     Fehler (kein stiller Nullblock),
  4. die Gleichlauf-Pruefung `supply_demand_key` zwischen Knopf und
     `config.INPUT_SIZE` schlaegt in beide Richtungen an,
  5. der Knopf ist in der Rust-Registratur eingetragen.

Was hier NICHT geprueft wird (braucht den angewandten Python-Patch bzw. das neue
Wheel): Cache-Schluessel mit Marker, `config.INPUT_SIZE` 936 unter Knopf,
Bit-Gleichheit Rust gegen Zwilling -- siehe Patch-Text, Abschnitt "Tests nach dem
Anwenden".
"""
from __future__ import annotations

import os
import re
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "engine" / "py")):
    if p not in sys.path:
        sys.path.insert(0, p)

import supply_demand_features as sdf  # noqa: E402

RUST_MODULE = ROOT / "engine" / "src" / "supply_demand.rs"
RUST_FEATURES = ROOT / "engine" / "src" / "features.rs"
KNOB_REGISTRY = ROOT / "engine" / "src" / "knob_registry.rs"
KNOB = "MOSAIC_SUPPLY_DEMAND_FEATURES"


def _rust_usize_const(text: str, name: str) -> str:
    m = re.search(r"pub const " + name + r": usize = ([^;]+);", text)
    if m is None:
        raise AssertionError(f"{name} nicht im Rust-Quelltext gefunden")
    return m.group(1).strip()


class MirrorsMatchRust(unittest.TestCase):
    def test_offset_rows_quantities_and_total(self):
        src = RUST_MODULE.read_text(encoding="utf-8")
        self.assertEqual(int(_rust_usize_const(src, "SUPPLY_DEMAND_OFFSET")), sdf.SUPPLY_DEMAND_OFFSET)
        rows = int(_rust_usize_const(src, "SUPPLY_DEMAND_ROWS"))
        quantities = int(_rust_usize_const(src, "SUPPLY_DEMAND_QUANTITIES"))
        self.assertEqual(2 * rows * quantities, sdf.SUPPLY_DEMAND_VALUES)
        self.assertEqual(sdf.LEN_WITH_SUPPLY_DEMAND, 936)

    def test_offset_is_the_base_contract_width(self):
        # Der Block sitzt fest hinter dem Basisvektor (features.rs::INPUT_SIZE).
        src = RUST_FEATURES.read_text(encoding="utf-8")
        self.assertEqual(int(_rust_usize_const(src, "INPUT_SIZE").split()[0]), sdf.SUPPLY_DEMAND_OFFSET)


class KnobSemantics(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.get(KNOB)

    def tearDown(self):
        os.environ.pop(KNOB, None)
        if self._saved is not None:
            os.environ[KNOB] = self._saved

    def test_only_exact_one_switches_on(self):
        os.environ.pop(KNOB, None)
        self.assertFalse(sdf.supply_demand_features_active())
        for off in ("", "0", "true", "yes", " 1"):
            os.environ[KNOB] = off
            self.assertFalse(sdf.supply_demand_features_active(), repr(off))
        os.environ[KNOB] = "1"
        self.assertTrue(sdf.supply_demand_features_active())

    def test_key_guard_fires_when_knob_and_config_disagree(self):
        # Ohne E4-Patch an config.py (und ohne Knopf beim Start) steht dort 888.
        import config
        if config.INPUT_SIZE != sdf.SUPPLY_DEMAND_OFFSET:
            self.skipTest("Prozess wurde mit gesetztem Knopf gestartet")
        os.environ.pop(KNOB, None)
        self.assertFalse(sdf.supply_demand_key())
        os.environ[KNOB] = "1"
        with self.assertRaises(RuntimeError):
            sdf.supply_demand_key()


class _FakeWheel(types.ModuleType):
    def __init__(self, n):
        super().__init__("mosaic_rust")
        self._n = n
        self.calls = 0

    def supply_demand_values_from_json(self, state_json):
        self.calls += 1
        return [0.5] * self._n


class AppendSwitch(unittest.TestCase):
    def setUp(self):
        self._saved = sys.modules.get("mosaic_rust")

    def tearDown(self):
        if self._saved is not None:
            sys.modules["mosaic_rust"] = self._saved
        else:
            sys.modules.pop("mosaic_rust", None)

    def test_base_width_is_left_alone_and_wheel_not_called(self):
        fake = _FakeWheel(sdf.SUPPLY_DEMAND_VALUES)
        sys.modules["mosaic_rust"] = fake
        base = [0.0] * sdf.SUPPLY_DEMAND_OFFSET
        out = sdf.append_supply_demand(base, {"phase": "drafting"}, sdf.SUPPLY_DEMAND_OFFSET)
        self.assertIs(out, base)
        self.assertEqual(fake.calls, 0, "ein 888er-Encoder darf den Export nicht einmal rufen")

    def test_e4_width_appends_exactly_the_block(self):
        fake = _FakeWheel(sdf.SUPPLY_DEMAND_VALUES)
        sys.modules["mosaic_rust"] = fake
        base = [0.25] * sdf.SUPPLY_DEMAND_OFFSET
        out = sdf.append_supply_demand(base, {"phase": "drafting"}, sdf.LEN_WITH_SUPPLY_DEMAND)
        self.assertEqual(len(out), sdf.LEN_WITH_SUPPLY_DEMAND)
        self.assertEqual(out[: sdf.SUPPLY_DEMAND_OFFSET], base)
        self.assertEqual(out[sdf.SUPPLY_DEMAND_OFFSET:], [0.5] * sdf.SUPPLY_DEMAND_VALUES)

    def test_wrong_base_length_is_an_error(self):
        sys.modules["mosaic_rust"] = _FakeWheel(sdf.SUPPLY_DEMAND_VALUES)
        with self.assertRaises(RuntimeError):
            sdf.append_supply_demand([0.0] * 884, {}, sdf.LEN_WITH_SUPPLY_DEMAND)

    def test_missing_export_is_a_hard_error(self):
        sys.modules["mosaic_rust"] = types.ModuleType("mosaic_rust")
        with self.assertRaises(RuntimeError):
            sdf.supply_demand_values({})

    def test_wrong_block_length_is_a_hard_error(self):
        sys.modules["mosaic_rust"] = _FakeWheel(sdf.SUPPLY_DEMAND_VALUES - 1)
        with self.assertRaises(RuntimeError):
            sdf.supply_demand_values({})


class KnobIsRegistered(unittest.TestCase):
    def test_registry_entry_exists(self):
        text = KNOB_REGISTRY.read_text(encoding="utf-8")
        self.assertIn(f'name: "{KNOB}"', text)


if __name__ == "__main__":
    unittest.main()
