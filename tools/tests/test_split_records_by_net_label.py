# -*- coding: utf-8 -*-
"""tools/split_records_by_net_label.py (Bauplan evaluations/exploiter_build_plan.md D3):
die Kopie traegt genau die Records der gewaehlten Netz-Seite, gleiche Basenames,
eine Dateiliste; fehlende Felder, leere Ergebnisse und vorhandene Ziele brechen ab."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from corpus_io import dump_records, load_records  # noqa: E402
from split_records_by_net_label import main, split_records  # noqa: E402


def recs(gid: str, side: int) -> list[dict]:
    return [{"game_id": gid, "player": p, "opponent_side": side,
             "net_label": "opponent" if p == side else "primary", "winner": 0, "i": i}
            for i, p in enumerate([0, 1, 0, 1, 1])]


class SplitRecords(unittest.TestCase):
    def test_keeps_exactly_the_chosen_side(self):
        r = recs("g1", 1)
        self.assertEqual([x["i"] for x in split_records(r, "opponent")], [1, 3, 4])
        self.assertEqual([x["i"] for x in split_records(r, "primary")], [0, 2])

    def test_record_without_label_is_an_error(self):
        with self.assertRaises(ValueError):
            split_records([{"game_id": "g", "player": 0}], "opponent")

    def test_main_writes_copies_and_list(self):
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d) / "src", Path(d) / "out"
            src.mkdir()
            dump_records(src / "selfplay_x_a.pkl", recs("a", 0))
            dump_records(src / "selfplay_x_b.pkl", recs("b", 1))
            self.assertEqual(main(["--data-dir", str(src), "--pattern", "selfplay_x_*.pkl",
                                   "--net-label", "opponent", "--out-dir", str(out)]), 0)
            a = load_records(out / "selfplay_x_a.pkl")
            self.assertTrue(all(x["player"] == 0 and x["net_label"] == "opponent" for x in a))
            self.assertEqual(len(a), 2)
            names = [ln for ln in (out / "files.txt").read_text(encoding="utf-8").splitlines()
                     if ln and not ln.startswith("#")]
            self.assertEqual(names, ["selfplay_x_a.pkl", "selfplay_x_b.pkl"])
            with self.assertRaises(SystemExit):  # Ziel liegt schon
                main(["--data-dir", str(src), "--pattern", "selfplay_x_*.pkl",
                      "--net-label", "opponent", "--out-dir", str(out)])


if __name__ == "__main__":
    unittest.main()
