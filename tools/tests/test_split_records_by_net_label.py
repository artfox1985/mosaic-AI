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
from split_records_by_net_label import main, mute_policy_of_lost_games, split_records  # noqa: E402


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


class PolicyOnlyWon(unittest.TestCase):
    """par.7c Punkt 1: Records verlorener Partien behalten das Wertziel, ihr Policy-Ziel
    wird ueber `policy_target_valid = False` stumm; gewonnene bleiben unberuehrt."""

    def test_lost_game_is_muted_won_game_untouched(self):
        won = [dict(r, winner=1) for r in recs("w", 1) if r["player"] == 1]
        lost = [dict(r, winner=0) for r in recs("l", 1) if r["player"] == 1]
        out, cnt = mute_policy_of_lost_games(won + lost)
        self.assertEqual(cnt, {"games_won": 1, "games_lost": 1, "records_policy_muted": len(lost)})
        self.assertTrue(all("policy_target_valid" not in r for r in out[:len(won)]))
        self.assertTrue(all(r["policy_target_valid"] is False for r in out[len(won):]))
        self.assertTrue(all("policy_target_valid" not in r for r in lost), "Eingabe unveraendert")

    def test_existing_true_flag_is_overwritten_in_lost_games(self):
        r = dict(recs("l", 0)[0], winner=1, policy_target_valid=True)
        out, _ = mute_policy_of_lost_games([r])
        self.assertIs(out[0]["policy_target_valid"], False)

    def test_aborted_game_counts_as_not_won(self):
        r = dict(recs("a", 0)[0], winner=0, completed=False)
        out, cnt = mute_policy_of_lost_games([r])
        self.assertEqual(cnt["games_lost"], 1)
        self.assertIs(out[0]["policy_target_valid"], False)

    def test_main_reports_and_writes(self):
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d) / "src", Path(d) / "out"
            src.mkdir()
            dump_records(src / "selfplay_x_a.pkl", [dict(r, winner=0) for r in recs("a", 0)])  # E gewinnt
            dump_records(src / "selfplay_x_b.pkl", [dict(r, winner=0) for r in recs("b", 1)])  # E verliert
            self.assertEqual(main(["--data-dir", str(src), "--pattern", "selfplay_x_*.pkl",
                                   "--net-label", "opponent", "--out-dir", str(out),
                                   "--policy-only-won"]), 0)
            a = load_records(out / "selfplay_x_a.pkl")
            b = load_records(out / "selfplay_x_b.pkl")
            self.assertTrue(all("policy_target_valid" not in r for r in a))
            self.assertTrue(b and all(r["policy_target_valid"] is False for r in b))


if __name__ == "__main__":
    unittest.main()
