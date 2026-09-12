"""Block-Bootstrap und Frueh-Stopp-Markierung im Elo-Tracker (2026-09-12).

Prueft, dass
- `parse_units` den String "k:w1,w2,..." gegen wins_a und n haelt,
- `units_from_paired_artifact` einen Block je Seed bildet und gegen die Summen prueft,
- der Bootstrap bei perfekt korrelierten Bloecken ein BREITERES Intervall liefert als das
  Binomial-Resampling derselben Zeile (das ist der Grund fuer die Spalte),
- Altzeilen ohne die neuen Spalten unveraendert lesbar bleiben.
"""
import csv
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import elo_tracker as et  # noqa: E402


class ParseUnits(unittest.TestCase):
    def test_empty_is_none(self):
        self.assertIsNone(et.parse_units("", 5, 10))
        self.assertIsNone(et.parse_units(None, 5, 10))

    def test_full_blocks(self):
        self.assertEqual(et.parse_units("10:4,6,5", 15, 30), [(4, 10), (6, 10), (5, 10)])

    def test_last_block_may_be_short(self):
        self.assertEqual(et.parse_units("10:4,6,2", 12, 24), [(4, 10), (6, 10), (2, 4)])

    def test_rejects_wrong_sum_and_size(self):
        with self.assertRaises(ValueError):
            et.parse_units("10:4,6,5", 14, 30)
        with self.assertRaises(ValueError):
            et.parse_units("10:4,6,5", 15, 40)
        with self.assertRaises(ValueError):
            et.parse_units("10:4,11", 15, 20)
        with self.assertRaises(ValueError):
            et.parse_units("4,6,5", 15, 30)


class UnitsFromArtifact(unittest.TestCase):
    def test_one_unit_per_block_seed(self):
        pairs = []
        for blk, seed in enumerate((100, 200, 300)):
            for i in range(5):
                pairs.append({"pair_index": blk * 5 + i, "block_seed": seed,
                              "a_wins_pair": 2 if i == 0 else 1})
        doc = {"per_pair_scores": pairs, "a_wins_total": 18, "n_games_total": 30}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(doc, f)
        try:
            self.assertEqual(et.units_from_paired_artifact(f.name), "10:6,6,6")
            doc["a_wins_total"] = 17
            with open(f.name, "w", encoding="utf-8") as g:
                json.dump(doc, g)
            with self.assertRaises(ValueError):
                et.units_from_paired_artifact(f.name)
        finally:
            os.unlink(f.name)


def _row(a, b, wa, wb, units="", early=0):
    return {"date": "2026-09-12", "player_a": a, "sims_a": 400, "player_b": b, "sims_b": 150,
            "wins_a": wa, "wins_b": wb, "n": wa + wb, "comment": "", "contract": "", "knobs": "",
            "units": units, "early_stop": early}


class BlockBootstrapWidth(unittest.TestCase):
    def test_correlated_blocks_widen_the_interval(self):
        # 20 Bloecke a 10 Partien, je Block entweder 10:0 oder 0:10 -- perfekte Korrelation
        # innerhalb des Blocks, Siegquote 50 %. Binomial sieht 200 unabhaengige Muenzwuerfe.
        anchor = et.ANCHOR_NAME
        units = "10:" + ",".join("10" if i % 2 == 0 else "0" for i in range(20))
        rows_block = [_row("x", anchor, 100, 100, units=units)]
        rows_binom = [_row("x", anchor, 100, 100)]
        ci_block = et.bootstrap_ci(rows_block, n_boot=400, seed=1)[et.node_key("x", 400)]
        ci_binom = et.bootstrap_ci(rows_binom, n_boot=400, seed=1)[et.node_key("x", 400)]
        self.assertGreater(ci_block[1] - ci_block[0], 1.5 * (ci_binom[1] - ci_binom[0]))

    def test_independent_blocks_match_binomial_roughly(self):
        anchor = et.ANCHOR_NAME
        units = "10:" + ",".join("5" for _ in range(20))
        rows_block = [_row("x", anchor, 100, 100, units=units)]
        ci = et.bootstrap_ci(rows_block, n_boot=200, seed=1)[et.node_key("x", 400)]
        # identische Bloecke: Resampling aendert nichts, Intervall entartet auf den Punkt
        self.assertLess(ci[1] - ci[0], 1e-6)


class LegacyCsv(unittest.TestCase):
    def test_rows_without_new_columns_load_with_defaults(self):
        old_header = et.HEADER[:11]
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8",
                                         newline="") as f:
            w = csv.writer(f)
            w.writerow(old_header)
            w.writerow(["2026-09-12", "x", 400, et.ANCHOR_NAME, 150, 30, 20, 50, "alt", "", ""])
        saved = et.CSV_PATH
        try:
            et.CSV_PATH = f.name
            rows = et.load_rows()
            self.assertEqual(rows[0]["units"], "")
            self.assertEqual(rows[0]["early_stop"], 0)
            et.add_result("y", 400, et.ANCHOR_NAME, 150, 12, 8, 20, comment="neu",
                          contract="", knobs="", units="10:6,6", early_stop=True)
            rows = et.load_rows()
            self.assertEqual(rows[1]["units"], "10:6,6")
            self.assertEqual(rows[1]["early_stop"], 1)
            with self.assertRaises(ValueError):
                et.add_result("z", 400, et.ANCHOR_NAME, 150, 12, 8, 20, contract="", knobs="",
                              units="10:5,6")
        finally:
            et.CSV_PATH = saved
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
