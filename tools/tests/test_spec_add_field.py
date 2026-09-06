# -*- coding: utf-8 -*-
"""tools/spec_add_field.py: Feld landet vor 'heuristik_variante', wird nie ueberschrieben, --check schreibt nicht."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import spec_add_field  # noqa: E402


class SpecAddField(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "x.spec.json"
        self.path.write_text(json.dumps({"envelope_search_c": 1.0, "envelope_projection_mode": 1, "heuristik_variante": "hv1"}, indent=2) + "\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_field_inserted_before_variant(self):
        self.assertEqual(spec_add_field.add_field(self.path, "envelope_flush_w", 0.0, check_only=False), "ergaenzt")
        keys = list(json.loads(self.path.read_text(encoding="utf-8")).keys())
        self.assertEqual(keys, ["envelope_search_c", "envelope_projection_mode", "envelope_flush_w", "heuristik_variante"])

    def test_existing_value_not_overwritten(self):
        spec_add_field.add_field(self.path, "envelope_flush_w", 0.5, check_only=False)
        self.assertEqual(spec_add_field.add_field(self.path, "envelope_flush_w", 0.0, check_only=False), "vorhanden")
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8"))["envelope_flush_w"], 0.5)

    def test_check_mode_does_not_write(self):
        before = self.path.read_text(encoding="utf-8")
        self.assertEqual(spec_add_field.add_field(self.path, "envelope_flush_w", 0.0, check_only=True), "FEHLT")
        self.assertEqual(self.path.read_text(encoding="utf-8"), before)

    def test_field_without_variant_goes_last(self):
        self.path.write_text(json.dumps({"a": 1}) + "\n", encoding="utf-8")
        spec_add_field.add_field(self.path, "b", 2, check_only=False)
        self.assertEqual(list(json.loads(self.path.read_text(encoding="utf-8")).keys()), ["a", "b"])


if __name__ == "__main__":
    unittest.main()
