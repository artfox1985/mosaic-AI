# -*- coding: utf-8 -*-
"""E2-Arm: Margen-Schwellen am WDL-Logit (`--margin-thresholds`).

Registriert in `evaluations/PREREG_evaluator_pretests.md` par.4 (Leser (b):
gemeinsamer Logit z, Schwellen {-10,-5,0,+5,+10} Punkte auf die Endmarge,
Skala je Runde, Gleichstand an `winner`) und par.8a (Vortest bestanden); Arm in
`evaluations/PREREG_v34_window.md` par.3.

Was hier festgenagelt wird:
  1. Der Verlust (engine/py/margin_thresholds.py) an kleinen synthetischen
     Beispielen: Ziele je Schwelle, Gleichstand-Regel, Maskierung, Zahlenwert
     gegen eine Handrechnung, Rundenskalen, Gradienten.
  2. Die Endmarge je Record (`corpus_dataset.final_margin_of_step`):
     `scores_unclamped` vor `scores`, Sicht des Ziehers, NaN bei unbekanntem
     Ausgang.
  3. Der Cache-Knopf MOSAIC_CACHE_FINAL_MARGIN steht in BEIDEN Schluesseln, aus
     der Umgebung gelesen, und ohne ihn bleibt das Schluesselmaterial ohne Marker.
  4. Default byte-identisch: Flag-Defaults, und jeder E2-Zugriff in den beiden
     Epochen-Durchgaengen liegt hinter `loss_setup.margin_log_scale is not None`;
     das Dataset haengt die Marge nur mit aktivem Feld an.

Kein Korpus, kein Wheel, kein Import von train.py (Quelltext per `ast`).
"""
from __future__ import annotations

import ast
import math
import os
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import torch  # noqa: E402

from margin_thresholds import (MARGIN_THRESHOLDS, NUM_ROUNDS, INITIAL_SCALE_POINTS,  # noqa: E402
                               initial_log_scale, margin_threshold_loss,
                               margin_threshold_targets)
from source_parser import module_literal, parser_from_main_block  # noqa: E402

TRAIN = REPO / "train.py"
CORPUS_DATASET = REPO / "engine" / "py" / "corpus_dataset.py"
ENV = "MOSAIC_CACHE_FINAL_MARGIN"


def _softplus(x: float) -> float:
    return math.log1p(math.exp(-abs(x))) + max(x, 0.0)


def _bce(x: float, target: float) -> float:
    # BCE mit Logit x: target * softplus(-x) + (1 - target) * softplus(x)
    return target * _softplus(-x) + (1.0 - target) * _softplus(x)


class RegisteredConstants(unittest.TestCase):
    def test_thresholds_are_the_registered_ones(self):
        # Nutzer 2026-10-02: ohne die 0, wie im urspruenglichen Vorschlag (Recherche-Bericht E2).
        self.assertEqual(MARGIN_THRESHOLDS, (-10.0, -5.0, 5.0, 10.0))
        self.assertNotIn(0.0, MARGIN_THRESHOLDS)
        self.assertEqual(NUM_ROUNDS, 5)
        # Startwert wie im Vortest-Leser (tools/probes/evaluator_pretests.py, log_s = log(10)).
        self.assertEqual(INITIAL_SCALE_POINTS, 10.0)
        ls = initial_log_scale()
        self.assertEqual(tuple(ls.shape), (5,))
        self.assertTrue(ls.requires_grad)
        self.assertTrue(torch.allclose(torch.exp(ls.detach()), torch.full((5,), 10.0)))


class Targets(unittest.TestCase):
    def test_targets_per_threshold(self):
        y = torch.tensor([1.0, 0.0, 1.0, 0.0, 1.0])
        m = torch.tensor([7.0, -12.0, 11.0, -5.0, 5.0])
        targets, valid = margin_threshold_targets(y, m)
        self.assertTrue(bool(valid.all()))
        want = [
            [1, 1, 1, 0],   # +7: ueber -10, -5, +5; nicht ueber +10
            [0, 0, 0, 0],   # -12
            [1, 1, 1, 1],   # +11
            [1, 0, 0, 0],   # -5 strikt: nicht ueber -5
            [1, 1, 0, 0],   # +5 strikt: nicht ueber +5
        ]
        self.assertEqual(targets.tolist(), [[float(v) for v in row] for row in want])

    def test_targets_ignore_winner_without_zero_threshold(self):
        """Ohne t = 0 haengen die Ziele nur an der Marge, nicht an `winner`."""
        a, _ = margin_threshold_targets(torch.tensor([1.0]), torch.tensor([0.0]))
        b, _ = margin_threshold_targets(torch.tensor([0.0]), torch.tensor([0.0]))
        self.assertEqual(a.tolist(), b.tolist())
        self.assertEqual(a[0].tolist(), [1.0, 1.0, 0.0, 0.0])

    def test_unknown_outcome_or_margin_is_masked(self):
        y = torch.tensor([-1.0, 1.0, 0.0])
        m = torch.tensor([3.0, float("nan"), -4.0])
        _, valid = margin_threshold_targets(y, m)
        self.assertEqual(valid.tolist(), [False, False, True])


class LossValue(unittest.TestCase):
    def _hand_loss(self, z, scale, margin, y):
        total = 0.0
        for t in MARGIN_THRESHOLDS:
            target = 1.0 if margin > t else 0.0
            total += _bce(z - t / scale, target)
        return total / len(MARGIN_THRESHOLDS)

    def test_matches_hand_computation(self):
        log_scale = torch.log(torch.tensor([10.0, 10.0, 10.0, 20.0, 10.0]))
        z = torch.tensor([0.5, -0.3])
        y = torch.tensor([1.0, 0.0])
        m = torch.tensor([7.0, 0.0])          # zweiter Zustand: Gleichstand, winner = Gegner
        rounds = torch.tensor([2, 4], dtype=torch.int8)
        loss, w = margin_threshold_loss(z, y, m, rounds, log_scale)
        want = (self._hand_loss(0.5, 10.0, 7.0, 1.0) + self._hand_loss(-0.3, 20.0, 0.0, 0.0)) / 2
        self.assertAlmostEqual(float(loss), want, places=5)
        self.assertEqual(w, 2.0)

    def test_masked_rows_do_not_count(self):
        log_scale = initial_log_scale()
        z = torch.tensor([0.5, 2.0, -1.0])
        y = torch.tensor([1.0, -1.0, 0.0])
        m = torch.tensor([7.0, 3.0, float("nan")])
        rounds = torch.tensor([1, 1, 1], dtype=torch.int8)
        loss, w = margin_threshold_loss(z, y, m, rounds, log_scale)
        only, w1 = margin_threshold_loss(z[:1], y[:1], m[:1], rounds[:1], log_scale)
        self.assertEqual((w, w1), (1.0, 1.0))
        self.assertAlmostEqual(float(loss), float(only), places=6)

    def test_sample_weight_masks_like_exclude_round5(self):
        log_scale = initial_log_scale()
        z = torch.tensor([0.5, -0.4])
        y = torch.tensor([1.0, 0.0])
        m = torch.tensor([7.0, -6.0])
        rounds = torch.tensor([3, 5], dtype=torch.int8)
        rw = torch.tensor([1.0, 0.0])
        loss, w = margin_threshold_loss(z, y, m, rounds, log_scale, rw)
        only, _ = margin_threshold_loss(z[:1], y[:1], m[:1], rounds[:1], log_scale)
        self.assertEqual(w, 1.0)
        self.assertAlmostEqual(float(loss), float(only), places=6)

    def test_no_valid_row_gives_finite_zero(self):
        log_scale = initial_log_scale()
        z = torch.tensor([0.3], requires_grad=True)
        loss, w = margin_threshold_loss(z, torch.tensor([-1.0]), torch.tensor([float("nan")]),
                                        torch.tensor([2], dtype=torch.int8), log_scale)
        self.assertEqual(w, 0.0)
        self.assertEqual(float(loss), 0.0)
        loss.backward()
        self.assertTrue(torch.isfinite(z.grad).all())
        self.assertTrue(torch.isfinite(log_scale.grad).all())


class RoundScales(unittest.TestCase):
    def test_round_index_is_clamped_and_only_its_scale_gets_gradient(self):
        log_scale = initial_log_scale()
        z = torch.tensor([0.2, -0.1])
        y = torch.tensor([1.0, 0.0])
        m = torch.tensor([7.0, -7.0])
        rounds = torch.tensor([0, 9], dtype=torch.int8)   # 0 -> Runde 1, 9 -> Runde 5
        loss, _ = margin_threshold_loss(z, y, m, rounds, log_scale)
        loss.backward()
        g = log_scale.grad.tolist()
        self.assertNotEqual(g[0], 0.0)
        self.assertNotEqual(g[4], 0.0)
        self.assertEqual(g[1:4], [0.0, 0.0, 0.0])

    def test_gradient_reaches_the_shared_logit(self):
        log_scale = initial_log_scale()
        z = torch.tensor([0.0], requires_grad=True)
        # Marge +11, Sieg: alle fuenf Ziele 1 -> der Verlust will z groesser.
        loss, _ = margin_threshold_loss(z, torch.tensor([1.0]), torch.tensor([11.0]),
                                        torch.tensor([3], dtype=torch.int8), log_scale)
        loss.backward()
        self.assertLess(float(z.grad[0]), 0.0)


class FinalMarginOfStep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import corpus_dataset
        cls.f = staticmethod(corpus_dataset.final_margin_of_step)

    def test_unclamped_before_clamped_and_mover_perspective(self):
        step = {"player": 1, "winner": 1, "scores": [0, 4], "scores_unclamped": [-3, 4]}
        self.assertEqual(self.f(step), 7.0)
        step0 = dict(step, player=0, winner=1)
        self.assertEqual(self.f(step0), -7.0)

    def test_fallback_to_scores(self):
        self.assertEqual(self.f({"player": 0, "winner": 0, "scores": [61, 55]}), 6.0)

    def test_tie_is_zero_and_winner_is_not_baked_in(self):
        self.assertEqual(self.f({"player": 0, "winner": 1, "scores": [50, 50],
                                 "scores_unclamped": [50, 50]}), 0.0)

    def test_unknown_outcome_is_nan(self):
        self.assertTrue(math.isnan(self.f({"player": 0, "scores": [1, 2]})))
        self.assertTrue(math.isnan(self.f({"player": 0, "winner": 0})))
        self.assertTrue(math.isnan(self.f({"player": 0, "winner": 0, "scores": [9, 1],
                                           "completed": False})))
        self.assertEqual(self.f({"player": 0, "winner": 0, "scores": [9, 1],
                                 "completed": True}), 8.0)


class _Env:
    def __init__(self, value):
        self.value, self.before = value, None

    def __enter__(self):
        self.before = os.environ.get(ENV)
        if self.value is None:
            os.environ.pop(ENV, None)
        else:
            os.environ[ENV] = self.value
        return self

    def __exit__(self, *_):
        if self.before is None:
            os.environ.pop(ENV, None)
        else:
            os.environ[ENV] = self.before
        return False


class CacheKeys(unittest.TestCase):
    FILES = ["selfplay_e2_a.pkl", "selfplay_e2_b.pkl"]
    WINDOW_KW = dict(value_target_variant="nortv", encoder="2d", conjunction_head=False)
    BLOCK_KW = dict(value_target_variant="nortv", encoder="2d", conjunction_head=False,
                    bootstrap_native=True)

    def _keys(self):
        import corpus_dataset
        from file_cache_key import per_file_cache_key
        wk = corpus_dataset.window_cache_key("data", self.FILES, **self.WINDOW_KW)
        return wk.key, wk.material, per_file_cache_key(self.FILES[0], **self.BLOCK_KW)

    def test_without_knob_no_marker(self):
        """Ohne Knopf: kein Marker -- jeder vorhandene Schluessel bleibt."""
        with _Env(None):
            _, material, _ = self._keys()
        self.assertNotIn("finalmargin", material)

    def test_knob_changes_both_keys_from_the_environment(self):
        with _Env(None):
            w0, _, b0 = self._keys()
        with _Env("1"):
            w1, material, b1 = self._keys()
        with _Env("0"):
            w2, _, b2 = self._keys()
        self.assertIn("+finalmargin_v1", material)
        self.assertNotEqual(w0, w1, "Fenster-Schluessel ignoriert MOSAIC_CACHE_FINAL_MARGIN")
        self.assertNotEqual(b0, b1, "Block-Schluessel ignoriert MOSAIC_CACHE_FINAL_MARGIN")
        self.assertEqual((w0, b0), (w2, b2), "nur exakt '1' schaltet ein")

    def test_block_key_source_has_the_marker(self):
        text = (REPO / "engine" / "py" / "file_cache_key.py").read_text(encoding="utf-8")
        self.assertIn('material += "|finalmargin_v1"', text)


class DefaultsAndGuards(unittest.TestCase):
    """Ohne `--margin-thresholds` laeuft train.py Operation fuer Operation wie bisher."""

    @classmethod
    def setUpClass(cls):
        cls.text = TRAIN.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text)

    def test_flag_defaults(self):
        parser = parser_from_main_block(TRAIN, extra_names={
            "VALUE_HEAD_VARIANTS": module_literal(REPO / "engine" / "py" / "neural_net.py",
                                                  "VALUE_HEAD_VARIANTS")})
        ns = parser.parse_args(["--name", "x"])
        self.assertIs(ns.margin_thresholds, False)
        self.assertEqual(ns.margin_threshold_weight, 1.0)

    def test_train_signature_defaults(self):
        fn = next(n for n in self.tree.body if isinstance(n, ast.FunctionDef) and n.name == "train")
        names = [a.arg for a in fn.args.args]
        defaults = dict(zip(names[len(names) - len(fn.args.defaults):],
                            [ast.literal_eval(d) for d in fn.args.defaults]))
        self.assertIs(defaults["margin_thresholds"], False)
        self.assertEqual(defaults["margin_threshold_weight"], 1.0)

    def test_loss_setup_defaults_off(self):
        cls = next(n for n in self.tree.body if isinstance(n, ast.ClassDef) and n.name == "LossSetup")
        fields = {s.target.id: s.value for s in cls.body if isinstance(s, ast.AnnAssign)}
        self.assertIsNone(ast.literal_eval(fields["margin_log_scale"]))
        self.assertEqual(ast.literal_eval(fields["margin_threshold_weight"]), 0.0)

    def _guarded(self, func_name, names, allowed_plain=()):
        """Jeder Zugriff auf `names` in `func_name` liegt in einem `if`, dessen
        Bedingung `margin_log_scale is not None` lautet -- ausser den genannten
        Initialisierungen `X = None`."""
        fn = next(n for n in self.tree.body if isinstance(n, ast.FunctionDef) and n.name == func_name)
        parents = {}
        for node in ast.walk(fn):
            for child in ast.iter_child_nodes(node):
                parents[child] = node
        offenders = []
        for node in ast.walk(fn):
            if not (isinstance(node, ast.Name) and node.id in names):
                continue
            stmt = node
            while not isinstance(stmt, ast.stmt):
                stmt = parents[stmt]
            if (isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Constant)
                    and stmt.value.value is None and node.id in allowed_plain):
                continue
            cur, ok = node, False
            while cur in parents:
                cur = parents[cur]
                if isinstance(cur, ast.If) and "margin_log_scale is not None" in ast.unparse(cur.test):
                    ok = True
                    break
            if not ok:
                offenders.append((node.id, node.lineno))
        return offenders

    def test_train_epoch_touches_e2_only_behind_the_switch(self):
        offenders = self._guarded(
            "_train_one_epoch",
            {"margin_loss", "s_final_margin", "margin_threshold_loss", "t_marginloss"},
            allowed_plain={"s_final_margin"})
        # `t_marginloss = 0` (Startwert) und die Rueckgabe sind ungefaehrlich: sie
        # beruehren keinen Tensor und keine Verlustsumme.
        offenders = [o for o in offenders if o[0] != "t_marginloss"]
        self.assertEqual(offenders, [])

    def test_validate_epoch_touches_e2_only_behind_the_switch(self):
        offenders = self._guarded(
            "_validate_one_epoch",
            {"v_final_margin", "margin_threshold_loss", "_vm_loss", "_vm_w"},
            allowed_plain={"v_final_margin"})
        self.assertEqual(offenders, [])

    def test_original_optimizer_call_and_env_switch(self):
        self.assertIn("        optimizer = optim.Adam(ftz.trainable_params(model), lr=effective_lr)",
                      self.text)
        self.assertIn('    if args.margin_thresholds:\n        os.environ["MOSAIC_CACHE_FINAL_MARGIN"] = "1"',
                      self.text)
        self.assertIn("    if margin_thresholds:\n        _resume_fingerprint[\"margin_thresholds\"] = True",
                      self.text)

    def test_dataset_tuple_unchanged_without_field(self):
        text = CORPUS_DATASET.read_text(encoding="utf-8")
        self.assertIn("        self.final_margin = None\n", text)
        self.assertEqual(text.count("if self.final_margin is not None:"), 2)  # __getitem__, get_batch
        start = text.index("_BATCH_FIELDS = (")
        self.assertNotIn("final_margin", text[start:text.index(")", start)])


if __name__ == "__main__":
    unittest.main()
