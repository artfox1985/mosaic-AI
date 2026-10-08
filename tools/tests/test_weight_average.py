# -*- coding: utf-8 -*-
"""Gewichtsmittelung (`weight_average.py`, train.py `--weight-average`), Schwerpunkt
die Auswahl des gespeicherten Stands `--weight-average-select` (PREREG_v35_window.md
par.16b, Arm v35-b08b).

Geprueft:
* `brierbest` haelt den gemittelten Stand mit dem kleinsten Brier fest (erstes
  Minimum, streng kleiner) und setzt ihn am Ende ein;
* `final` (Default) haelt nichts fest, das Mittel bleibt der Endstand;
* die Mitschrift zieht keinen Zufallszustand (Einzelstand-Pfad bitgleich);
* `--resume` traegt den festgehaltenen Stand, aeltere Zwischenstaende ohne die
  neuen Felder laden als `final`, ein Wechsel der Auswahl bricht ab;
* Vorab-Validierung, Parser-Default und Signatur-Default sind Literale `final`;
* train.py: Mitschrift unter `preserved_rng`, Auswahl VOR der BN-Neuschaetzung,
  Fingerabdruck nur mit Knopf.
"""
from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

import torch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from source_parser import module_literal, parser_from_main_block  # noqa: E402
from weight_average import (WEIGHT_AVERAGE_SELECTS, WeightAverager,  # noqa: E402
                            validate_weight_average_args)

TRAIN = REPO / "train.py"


class TinyNet(torch.nn.Module):
    """Synthetisches Netz mit Parametern UND BN-Buffern."""

    def __init__(self):
        super().__init__()
        self.lin = torch.nn.Linear(3, 2)
        self.bn = torch.nn.BatchNorm1d(2)

    def forward(self, x):
        return self.bn(self.lin(x))


def set_weights(model, value: float) -> None:
    """Alle Gleitkomma-Eintraege des state_dict auf `value` (simuliert eine Epoche)."""
    with torch.no_grad():
        for key, t in model.state_dict().items():
            if t.is_floating_point():
                t.fill_(value)


def snapshot(model) -> dict:
    return {k: v.detach().clone() for k, v in model.state_dict().items()}


def states_equal(a: dict, b: dict) -> bool:
    return set(a) == set(b) and all(torch.equal(a[k].cpu(), b[k].cpu()) for k in a)


def run_three_epochs(select: str, briers=(0.30, 0.20, 0.25)):
    """Drei Epochen, alle gemittelt (from_epoch 1), mit vorgegebenen Brier-Werten.
    Gibt (Averager, Mittel-Schnappschuss je Epoche) zurueck."""
    model = TinyNet()
    avg = WeightAverager("ema", 0.75, 1, select)
    snaps = []
    for epoch, (value, brier) in enumerate(zip((1.0, 2.0, 3.0), briers), start=1):
        set_weights(model, value)
        assert avg.update(model, epoch)
        snaps.append(snapshot(avg.model))
        avg.observe_val_brier(brier, epoch)
    return avg, snaps


class BrierBestSelection(unittest.TestCase):
    def test_keeps_the_best_averaged_state(self):
        avg, snaps = run_three_epochs("brierbest")
        self.assertEqual((avg.best_epoch, avg.best_brier), (2, 0.20))
        self.assertTrue(states_equal(avg.best_state, snaps[1]))
        # Das Mittel selbst laeuft weiter bis Epoche 3 ...
        self.assertTrue(states_equal(snapshot(avg.model), snaps[2]))
        # ... und die Auswahl setzt den Stand nach Epoche 2 ein.
        self.assertEqual(avg.apply_selection(torch.device("cpu")), 2)
        self.assertTrue(states_equal(snapshot(avg.model), snaps[1]))
        self.assertEqual(avg.selected_brier(), 0.20)

    def test_kept_state_is_a_copy_on_cpu(self):
        avg, snaps = run_three_epochs("brierbest")
        for v in avg.best_state.values():
            self.assertEqual(v.device.type, "cpu")
        # Das Weiterlaufen des Mittels (Epoche 3) hat die Kopie nicht veraendert.
        self.assertFalse(states_equal(avg.best_state, snaps[2]))

    def test_first_minimum_wins_on_tie(self):
        avg, _ = run_three_epochs("brierbest", briers=(0.30, 0.20, 0.20))
        self.assertEqual(avg.best_epoch, 2)

    def test_none_brier_is_skipped(self):
        avg, _ = run_three_epochs("brierbest", briers=(None, 0.25, None))
        self.assertEqual(avg.best_epoch, 2)

    def test_no_brier_at_all_keeps_final_and_reports_none(self):
        avg, snaps = run_three_epochs("brierbest", briers=(None, None, None))
        self.assertIsNone(avg.apply_selection(torch.device("cpu")))
        self.assertTrue(states_equal(snapshot(avg.model), snaps[2]))

    def test_observation_draws_no_random_numbers(self):
        model = TinyNet()
        avg = WeightAverager("ema", 0.75, 1, "brierbest")
        avg.update(model, 1)
        before = torch.get_rng_state()
        self.assertTrue(avg.observe_val_brier(0.2, 1))
        self.assertTrue(torch.equal(before, torch.get_rng_state()))


class FinalUnchanged(unittest.TestCase):
    def test_final_keeps_nothing_and_saves_the_end_state(self):
        avg, snaps = run_three_epochs("final")
        self.assertIsNone(avg.best_state)
        self.assertIsNone(avg.best_epoch)
        self.assertEqual(avg.apply_selection(torch.device("cpu")), 3)
        self.assertTrue(states_equal(snapshot(avg.model), snaps[2]))
        self.assertEqual(avg.selected_brier(), 0.25)

    def test_default_select_is_final(self):
        self.assertEqual(WeightAverager("ema", 0.75, 2).select, "final")

    def test_final_and_brierbest_average_identically(self):
        """Die Auswahl greift nicht ins Mitteln ein: der Endstand des Mittels ist in beiden Modi gleich."""
        a_final, s_final = run_three_epochs("final")
        a_best, s_best = run_three_epochs("brierbest")
        for x, y in zip(s_final, s_best):
            self.assertTrue(states_equal(x, y))


class ResumeCarriesSelection(unittest.TestCase):
    def test_state_round_trip_keeps_best(self):
        avg, snaps = run_three_epochs("brierbest")
        state = avg.state()
        fresh = WeightAverager("ema", 0.75, 1, "brierbest")
        fresh.load_state(state, TinyNet(), torch.device("cpu"))
        self.assertEqual((fresh.best_epoch, fresh.best_brier), (2, 0.20))
        self.assertTrue(states_equal(fresh.best_state, snaps[1]))
        self.assertEqual(fresh.apply_selection(torch.device("cpu")), 2)
        self.assertTrue(states_equal(snapshot(fresh.model), snaps[1]))

    def test_resumed_run_continues_the_selection(self):
        """Unterbrechung nach Epoche 2, Fortsetzung mit Epoche 3 (besserer Brier) -> Epoche 3."""
        model = TinyNet()
        avg = WeightAverager("ema", 0.75, 1, "brierbest")
        for epoch, (value, brier) in enumerate(((1.0, 0.30), (2.0, 0.20)), start=1):
            set_weights(model, value)
            avg.update(model, epoch)
            avg.observe_val_brier(brier, epoch)
        fresh = WeightAverager("ema", 0.75, 1, "brierbest")
        fresh.load_state(avg.state(), TinyNet(), torch.device("cpu"))
        set_weights(model, 3.0)
        fresh.update(model, 3)
        self.assertTrue(fresh.observe_val_brier(0.10, 3))
        self.assertEqual(fresh.best_epoch, 3)

    def test_state_snapshot_is_independent(self):
        avg, _ = run_three_epochs("brierbest")
        state = avg.state()
        for v in state["best_state"].values():
            if v.is_floating_point():
                v.fill_(-7.0)
        self.assertFalse(any(torch.equal(v, torch.full_like(v, -7.0))
                             for v in avg.best_state.values() if v.is_floating_point()))

    def test_old_resume_state_loads_as_final(self):
        avg, _ = run_three_epochs("final")
        old = {k: avg.state()[k] for k in ("mode", "decay", "from_epoch", "n_averaged",
                                            "averaged_epochs", "model_state")}
        fresh = WeightAverager("ema", 0.75, 1)
        fresh.load_state(old, TinyNet(), torch.device("cpu"))
        self.assertIsNone(fresh.best_state)
        self.assertEqual(fresh.averaged_epochs, [1, 2, 3])

    def test_select_change_on_resume_aborts(self):
        avg, _ = run_three_epochs("final")
        fresh = WeightAverager("ema", 0.75, 1, "brierbest")
        with self.assertRaises(SystemExit):
            fresh.load_state(avg.state(), TinyNet(), torch.device("cpu"))

    def test_missing_best_state_aborts(self):
        avg, _ = run_three_epochs("brierbest")
        state = avg.state()
        state["best_state"] = None
        with self.assertRaises(SystemExit):
            WeightAverager("ema", 0.75, 1, "brierbest").load_state(state, TinyNet(), torch.device("cpu"))


class Validation(unittest.TestCase):
    def test_selects(self):
        self.assertEqual(WEIGHT_AVERAGE_SELECTS, ("final", "brierbest"))

    def test_brierbest_without_averaging_aborts(self):
        with self.assertRaises(SystemExit):
            validate_weight_average_args("none", 0.75, 2, 12, False, "brierbest")

    def test_unknown_select_aborts(self):
        with self.assertRaises(SystemExit):
            validate_weight_average_args("ema", 0.75, 2, 12, False, "best")

    def test_valid_combinations_pass(self):
        validate_weight_average_args("none", 0.75, 2, 12, False)
        validate_weight_average_args("none", 0.75, 2, 12, False, "final")
        validate_weight_average_args("ema", 0.75, 2, 12, False, "brierbest")
        validate_weight_average_args("swa", 0.75, 2, 12, False, "final")


class TrainSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = TRAIN.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text)
        cls.body = cls.text[cls.text.index("\ndef train("):]

    def test_parser_default_is_literal_final(self):
        parser = parser_from_main_block(TRAIN, extra_names={
            "VALUE_HEAD_VARIANTS": module_literal(REPO / "engine" / "py" / "neural_net.py",
                                                  "VALUE_HEAD_VARIANTS")})
        self.assertEqual(parser.parse_args(["--name", "x"]).weight_average_select, "final")
        ns = parser.parse_args(["--name", "x", "--weight-average", "ema",
                                "--weight-average-select", "brierbest"])
        self.assertEqual(ns.weight_average_select, "brierbest")
        with self.assertRaises(SystemExit):
            parser.parse_args(["--name", "x", "--weight-average-select", "best"])

    def test_signature_default_is_literal_final(self):
        fn = next(n for n in self.tree.body if isinstance(n, ast.FunctionDef) and n.name == "train")
        names = [a.arg for a in fn.args.args]
        defaults = dict(zip(names[len(names) - len(fn.args.defaults):],
                            [ast.literal_eval(d) for d in fn.args.defaults]))
        self.assertEqual(defaults["weight_average_select"], "final")

    def test_observation_runs_under_preserved_rng(self):
        guard = self.body.index("with preserved_rng():")
        observe = self.body.index("weight_averager.observe_val_brier(")
        after = self.body.index('if _avg_val["epoch_val_ploss"] is not None:')
        self.assertLess(guard, observe)
        self.assertLess(observe, after)
        # eingerueckt im with-Block (16 Leerzeichen), nicht danach
        line = self.body[self.body.rindex("\n", 0, observe) + 1:observe]
        self.assertEqual(line, " " * 16)

    def test_selection_precedes_bn_recompute_and_final_validation(self):
        apply_at = self.body.index("weight_averager.apply_selection(device)")
        self.assertLess(apply_at, self.body.index("_bn_batches = recompute_bn_stats("))
        self.assertLess(apply_at, self.body.index("weight_average_final_val = _validate_one_epoch("))

    def test_fingerprint_only_with_knob(self):
        self.assertIn('if weight_average_select != "final":\n'
                      '            _resume_fingerprint["weight_average_select"] = weight_average_select',
                      self.body)


if __name__ == "__main__":
    unittest.main()
