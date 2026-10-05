"""Code-Review 2 (2026-10-02), Paket Messkette: Befunde 1, 3 und 4.

1: welche Checkpoint-Datei die Brier-beste ist (`tools/brier_best_checkpoint.py`, Regel wie train.py).
3: Block-z ohne Division durch null (`tools/gating_block_z.py`).
4: paired_gating prueft seine Parameter (`tools/paired_gating.py::validate_gating_params`).
"""
import math
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "tools"))

from brier_best_checkpoint import choose_suffix, first_argmin  # noqa: E402
from gating_block_z import block_z  # noqa: E402
from paired_gating import validate_gating_params  # noqa: E402


class BrierBestCheckpoint(unittest.TestCase):
    def test_first_minimum_wins_ties_and_skips_none(self):
        self.assertEqual(first_argmin([0.3, 0.2, 0.2, None]), 2)
        self.assertIsNone(first_argmin([None, None]))

    def test_suffix_rule_matches_train_py(self):
        # v34-b02: Brier-Minimum Epoche 1 = best_epoch -> _best (kein _brierbest geschrieben)
        self.assertEqual(choose_suffix([0.1, 0.2, 0.3], [1.0, 1.1, 1.2])[0], "_best")
        # v34-b03: Brier Epoche 3, best_epoch 1 -> _brierbest
        self.assertEqual(choose_suffix([0.3, 0.2, 0.1, 0.2], [1.0, 1.1, 1.2, 1.3])[0], "_brierbest")
        # Brier-Minimum in der letzten Epoche -> finaler Stand
        self.assertEqual(choose_suffix([0.3, 0.2, 0.1], [1.0, 1.1, 1.2])[0], "")
        # letzte Epoche ist zugleich best_epoch und Brier-best -> finaler Stand
        self.assertEqual(choose_suffix([0.3, 0.1], [1.0, 0.9])[0], "")
        with self.assertRaises(ValueError):
            choose_suffix([None], [1.0])

    def test_averaged_checkpoint_only_when_strictly_better(self):
        # PREREG_v35_window.md par.16: gespeicherter `_avg` streng unter dem Einzel-Minimum -> _avg
        self.assertEqual(choose_suffix([0.3, 0.2, 0.25], [1.0, 1.1, 1.2], avg_brier=0.19)[0], "_avg")
        # Gleichstand oder schlechter -> Bestandsregel (hier _brierbest)
        self.assertEqual(choose_suffix([0.3, 0.2, 0.25], [1.0, 1.1, 1.2], avg_brier=0.2)[0], "_brierbest")
        self.assertEqual(choose_suffix([0.3, 0.2, 0.25], [1.0, 1.1, 1.2], avg_brier=0.21)[0], "_brierbest")
        # ohne Mittel (None, Default) unveraendert, auch im info-Dict
        self.assertEqual(choose_suffix([0.1, 0.2, 0.3], [1.0, 1.1, 1.2], avg_brier=None),
                         choose_suffix([0.1, 0.2, 0.3], [1.0, 1.1, 1.2]))
        # ohne Einzel-Brier bleibt es ein Fehler, auch mit Mittel
        with self.assertRaises(ValueError):
            choose_suffix([None], [1.0], avg_brier=0.1)


class BlockZ(unittest.TestCase):
    def test_single_block_has_no_z(self):
        r = block_z([0.7])
        self.assertIsNone(r["z"])
        self.assertIsNone(r["sd"])

    def test_identical_blocks(self):
        self.assertEqual(block_z([1.0, 1.0, 1.0])["z"], math.inf)
        self.assertEqual(block_z([0.2, 0.2])["z"], -math.inf)
        self.assertEqual(block_z([0.5, 0.5])["z"], 0.0)

    def test_regular_case_unchanged(self):
        r = block_z([0.6, 0.4, 0.8, 0.6])
        self.assertAlmostEqual(r["z"], (0.6 - 0.5) / (r["sd"] / 2.0))

    def test_empty(self):
        self.assertIsNone(block_z([])["z"])


class GatingParams(unittest.TestCase):
    def test_valid(self):
        validate_gating_params(5, 200, 0.65, 0.05, 0.05)
        validate_gating_params(5, 200, 0.65, 1e-12, 1e-12)

    def test_rejects(self):
        for args in ((0, 200, 0.65, 0.05, 0.05), (5, 0, 0.65, 0.05, 0.05), (5, 200, 1.0, 0.05, 0.05),
                     (5, 200, 0.5, 0.05, 0.05), (5, 200, 0.4, 0.05, 0.05), (5, 200, 0.65, 0.0, 0.05),
                     (5, 200, 0.65, 0.05, 1.0)):
            with self.assertRaises(ValueError, msg=args):
                validate_gating_params(*args)


if __name__ == "__main__":
    unittest.main()
