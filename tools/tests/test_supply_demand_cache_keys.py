# -*- coding: utf-8 -*-
"""E4-Knopf in BEIDEN Cache-Schluesseln, Default unberuehrt (braucht den Patch).

`feedback_feature_knob_belongs_in_both_cache_keys`: mit Knopf aendern sich Block-
UND Fenster-Schluessel; ohne Knopf bleibt der Fenster-Schluessel auf dem Stolperdraht
`KEY_WITH_SWITCH_OFF` (test_window_cache_key_planes_ablation.py). `config` bindet die
Breite beim Import, deshalb wird es fuer den Knopf-Fall neu geladen und am Ende
zurueckgesetzt.
"""
import importlib
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "engine" / "py")):
    if p not in sys.path:
        sys.path.insert(0, p)

import config  # noqa: E402
import corpus_dataset  # noqa: E402
import file_cache_key  # noqa: E402

KNOB = "MOSAIC_SUPPLY_DEMAND_FEATURES"
FILES = ["data/selfplay_test-a_0001.pkl", "data/selfplay_test-b_0001.pkl"]
KEY_WITH_SWITCH_OFF = "41b98a5d3890"  # aus test_window_cache_key_planes_ablation.py


def _block_key():
    return file_cache_key.per_file_cache_key(
        "selfplay_test-a_0001.pkl", value_target_variant="nortv", encoder="2d",
        conjunction_head=False, bootstrap_native=True)


class SupplyDemandCacheKeys(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.get(KNOB)
        os.environ.pop(KNOB, None)
        importlib.reload(config)

    def tearDown(self):
        os.environ.pop(KNOB, None)
        if self._saved is not None:
            os.environ[KNOB] = self._saved
        importlib.reload(config)

    def test_default_is_888_and_keeps_the_legacy_window_key(self):
        self.assertEqual(config.INPUT_SIZE, 888)
        three = ["data/selfplay_test-a_0001.pkl", "data/selfplay_test-a_0002.pkl",
                 "data/selfplay_test-b_0001.pkl"]
        self.assertEqual(corpus_dataset.window_cache_key("data", three).key, KEY_WITH_SWITCH_OFF)

    def test_knob_moves_both_keys_and_the_width(self):
        w_off = corpus_dataset.window_cache_key("data", FILES).key
        b_off = _block_key()
        os.environ[KNOB] = "1"
        importlib.reload(config)
        self.assertEqual(config.INPUT_SIZE, 936)
        self.assertNotEqual(corpus_dataset.window_cache_key("data", FILES).key, w_off)
        self.assertNotEqual(_block_key(), b_off)

    def test_knob_without_config_reload_is_a_hard_error(self):
        os.environ[KNOB] = "1"  # config bleibt auf 888 gebunden
        with self.assertRaises(RuntimeError):
            _block_key()
        with self.assertRaises(RuntimeError):
            corpus_dataset.window_cache_key("data", FILES)


if __name__ == "__main__":
    unittest.main()
