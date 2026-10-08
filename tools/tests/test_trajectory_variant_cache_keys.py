# -*- coding: utf-8 -*-
"""Varianten b11 bis b15 des Trajektorien-Bootstraps in BEIDEN Cache-Schluesseln
(PREREG_v35_window.md par.19), Bestand bitgleich.

Stolperdraht: die Schluessel ohne Knopf, mit b03/b05/b06 (trajectory k = 1..3)
und mit b04 (margin 20) sind die Werte, die der Code VOR dem Bau der Varianten
lieferte (am 2026-10-08 mit den HEAD-Fassungen von corpus_dataset.py,
file_cache_key.py, trajectory_bootstrap.py und neural_net.py gerechnet und
gegen den neuen Code verglichen: identisch). Faellt einer, sind die liegenden
Bloecke und Monolithen der Arme b02 bis b06 nicht mehr adressierbar.

Danach: jeder neue Knopf steht als Marker im Material BEIDER Schluessel und
bewegt beide Hashes; MOSAIC_TD_LAMBDA (b14) wird ueber den wirksamen Wert
`TD_LAMBDA` geprueft (er wird beim Import von neural_net gelesen, darum hier per
Patch des Namens in beiden Modulen).
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "engine" / "py")):
    if p not in sys.path:
        sys.path.insert(0, p)

import corpus_dataset  # noqa: E402
import file_cache_key  # noqa: E402
import neural_net  # noqa: E402

FILES = ["data/selfplay_test-a_0001.pkl", "data/selfplay_test-b_0001.pkl"]
BLOCK_BASENAME = "selfplay_test-a_0001.pkl"
BOOTSTRAP_KNOBS = (
    "MOSAIC_BOOTSTRAP_SOURCE", "MOSAIC_BOOTSTRAP_HORIZON_ROUNDS", "MOSAIC_BOOTSTRAP_MARGIN_SCALE",
    "MOSAIC_BOOTSTRAP_TRAJ_LAMBDA", "MOSAIC_BOOTSTRAP_TRAJ_OPPONENT", "MOSAIC_BOOTSTRAP_TRAJ_MIX",
    "MOSAIC_BOOTSTRAP_TRAJ_CONF_SCALE", "MOSAIC_TD_LAMBDA",
)
# (Fenster-Schluessel, Block-Schluessel) vor dem Bau der Varianten, siehe Kopf.
LEGACY_KEYS = {
    "stock": ({}, ("9265c716df2c", "6a49515020e0")),
    "b03_traj_k1": ({"MOSAIC_BOOTSTRAP_SOURCE": "trajectory", "MOSAIC_BOOTSTRAP_HORIZON_ROUNDS": "1"},
                    ("105cf14d0dab", "79b36dbe8262")),
    "b05_traj_k2": ({"MOSAIC_BOOTSTRAP_SOURCE": "trajectory", "MOSAIC_BOOTSTRAP_HORIZON_ROUNDS": "2"},
                    ("f26608661f49", "a534f08ebb0d")),
    "b06_traj_k3": ({"MOSAIC_BOOTSTRAP_SOURCE": "trajectory", "MOSAIC_BOOTSTRAP_HORIZON_ROUNDS": "3"},
                    ("55946918b67f", "f5d0a4b5993d")),
    "b04_margin_20": ({"MOSAIC_BOOTSTRAP_SOURCE": "margin", "MOSAIC_BOOTSTRAP_MARGIN_SCALE": "20"},
                      ("2335ef1fb1dc", "ad89e70203e7")),
}
# Arm -> (Umgebung, Marker im Fenster-Material, Marker im Block-Material).
VARIANTS = {
    "b11": ({"MOSAIC_BOOTSTRAP_SOURCE": "trajectory_lambda", "MOSAIC_BOOTSTRAP_TRAJ_LAMBDA": "0.5"},
            "+bootstraptrajlambda_l0.5_v1", "|bootstraptrajlambda_l0.5_v1"),
    "b12": ({"MOSAIC_BOOTSTRAP_SOURCE": "trajectory_lambda", "MOSAIC_BOOTSTRAP_TRAJ_LAMBDA": "0.5",
             "MOSAIC_BOOTSTRAP_TRAJ_OPPONENT": "1"},
            "+bootstraptrajlambda_l0.5_opp1_v1", "|bootstraptrajlambda_l0.5_opp1_v1"),
    "b13": ({"MOSAIC_BOOTSTRAP_SOURCE": "trajectory", "MOSAIC_BOOTSTRAP_HORIZON_ROUNDS": "1",
             "MOSAIC_BOOTSTRAP_TRAJ_MIX": "0.5"},
            "+bootstraptraj_h1_mix0.5_v1", "|bootstraptraj_h1_mix0.5_v1"),
    "b15": ({"MOSAIC_BOOTSTRAP_SOURCE": "trajectory", "MOSAIC_BOOTSTRAP_HORIZON_ROUNDS": "1",
             "MOSAIC_BOOTSTRAP_TRAJ_CONF_SCALE": "0.0116"},
            "+bootstraptraj_h1_conf0.0116_v1", "|bootstraptraj_h1_conf0.0116_v1"),
}


def env_with(**env):
    clean = {k: v for k, v in os.environ.items() if k not in BOOTSTRAP_KNOBS}
    clean.update(env)
    return mock.patch.dict(os.environ, clean, clear=True)


def window_key():
    return corpus_dataset.window_cache_key("data", FILES, value_target_variant="nortv",
                                           encoder="2d", conjunction_head=False)


def block_material_and_key():
    """Block-Schluessel plus das Material, aus dem er gehasht wird (md5 wird
    abgefangen, damit der Test den Marker im Text sehen kann)."""
    import hashlib
    seen = {}

    def spy(data):
        seen["material"] = data.decode()
        return hashlib.new("md5", data)

    # per_file_cache_key importiert hashlib lokal und ruft hashlib.md5 einmal.
    with mock.patch.object(hashlib, "md5", spy):
        key = file_cache_key.per_file_cache_key(BLOCK_BASENAME, value_target_variant="nortv", encoder="2d",
                                                conjunction_head=False, bootstrap_native=True)
    return seen["material"], key


class LegacyKeysUnchanged(unittest.TestCase):
    def test_stock_and_existing_arms_keep_their_keys(self):
        for name, (env, (want_window, want_block)) in LEGACY_KEYS.items():
            with self.subTest(arm=name), env_with(**env):
                self.assertEqual(window_key().key, want_window)
                self.assertEqual(block_material_and_key()[1], want_block)

    def test_stock_material_has_no_variant_marker(self):
        with env_with():
            material = window_key().material
            block_material, _ = block_material_and_key()
        for marker in ("bootstraptraj", "bootstrapmargin", "tdlambda"):
            self.assertNotIn(marker, material)
            self.assertNotIn(marker, block_material)


class VariantMarkersInBothKeys(unittest.TestCase):
    def test_each_variant_marks_both_keys_and_moves_both_hashes(self):
        with env_with():
            stock_window = window_key().key
            stock_block = block_material_and_key()[1]
        seen_window, seen_block = {stock_window}, {stock_block}
        for name, (env, window_marker, block_marker) in VARIANTS.items():
            with self.subTest(arm=name), env_with(**env):
                wk = window_key()
                material, bk = block_material_and_key()
                self.assertIn(window_marker, wk.material)
                self.assertIn(block_marker, material)
                self.assertEqual(wk.material.count("+bootstrap"), 1)
                self.assertEqual(material.count("|bootstrap"), 1)
                self.assertNotIn(wk.key, seen_window)
                self.assertNotIn(bk, seen_block)
                seen_window.add(wk.key)
                seen_block.add(bk)

    def test_td_lambda_marks_both_keys_only_off_default(self):
        for value, marker in ((0.5, None), (0.7, "tdlambda0.7")):
            with self.subTest(td_lambda=value), env_with(
                    MOSAIC_BOOTSTRAP_SOURCE="trajectory", MOSAIC_BOOTSTRAP_HORIZON_ROUNDS="1"), \
                    mock.patch.object(corpus_dataset, "TD_LAMBDA", value), \
                    mock.patch.object(neural_net, "TD_LAMBDA", value):
                wk = window_key()
                material, bk = block_material_and_key()
                if marker is None:
                    self.assertNotIn("tdlambda", wk.material)
                    self.assertNotIn("tdlambda", material)
                    self.assertEqual((wk.key, bk), LEGACY_KEYS["b03_traj_k1"][1])
                else:
                    self.assertIn("+" + marker + "_v1", wk.material)
                    self.assertIn("|" + marker + "_v1", material)
                    self.assertNotEqual(wk.key, LEGACY_KEYS["b03_traj_k1"][1][0])
                    self.assertNotEqual(bk, LEGACY_KEYS["b03_traj_k1"][1][1])

    def test_neural_net_reads_the_stock_value_without_knob(self):
        # Der Prozess dieser Suite laeuft ohne MOSAIC_TD_LAMBDA (sonst waere der
        # Stolperdraht oben ohnehin rot): der importierte Wert ist der Bestand.
        if os.environ.get("MOSAIC_TD_LAMBDA"):
            self.skipTest("MOSAIC_TD_LAMBDA in der Test-Umgebung gesetzt")
        self.assertEqual(neural_net.TD_LAMBDA, 0.5)
        self.assertIs(corpus_dataset.TD_LAMBDA, neural_net.TD_LAMBDA)


if __name__ == "__main__":
    unittest.main()
