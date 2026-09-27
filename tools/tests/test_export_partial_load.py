# -*- coding: utf-8 -*-
"""Code-Review 2026-09-26 #18: der ONNX-Export bricht ab, wenn der Checkpoint
nicht vollstaendig auf das Modell passt, statt einen Kopf still zufaellig zu
exportieren (`export_onnx.load_state_checked`).

Kleines torch-Modell statt eines echten Checkpoints: geprueft werden die drei
Klassen (Shape-Abweichung, fehlender, ueberzaehliger Schluessel), der Ausweg
`allow_partial=True` und der verlustfreie Normalfall. Dazu textnah, dass der
Auto-Export in train.py eine `Exception` faengt -- `PartialLoadError` muss
eine sein, sonst schnitte der Abbruch den Rest des Trainingslaufs ab.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import torch  # noqa: E402

import export_onnx  # noqa: E402
from export_onnx import PartialLoadError, load_state_checked  # noqa: E402


class Tiny(torch.nn.Module):
    def __init__(self, width: int = 3):
        super().__init__()
        self.body = torch.nn.Linear(width, 2)
        self.head = torch.nn.Linear(2, 1)


class LoadStateChecked(unittest.TestCase):
    def test_exact_checkpoint_loads(self):
        torch.manual_seed(0)
        src, dst = Tiny(), Tiny()
        load_state_checked(dst, src.state_dict(), allow_partial=False, label="t")
        for k, v in src.state_dict().items():
            self.assertTrue(torch.equal(v, dst.state_dict()[k]), k)

    def test_shape_mismatch_aborts(self):
        with self.assertRaises(PartialLoadError) as ctx:
            load_state_checked(Tiny(3), Tiny(4).state_dict(), allow_partial=False, label="t")
        self.assertIn("body.weight", str(ctx.exception))

    def test_missing_key_aborts(self):
        state = {k: v for k, v in Tiny().state_dict().items() if not k.startswith("head.")}
        with self.assertRaises(PartialLoadError) as ctx:
            load_state_checked(Tiny(), state, allow_partial=False, label="t")
        self.assertIn("head.weight", str(ctx.exception))

    def test_unexpected_key_aborts(self):
        state = dict(Tiny().state_dict())
        state["extra_head.weight"] = torch.zeros(1)
        with self.assertRaises(PartialLoadError) as ctx:
            load_state_checked(Tiny(), state, allow_partial=False, label="t")
        self.assertIn("extra_head.weight", str(ctx.exception))

    def test_allow_partial_loads_the_rest(self):
        torch.manual_seed(1)
        src = Tiny(4)
        dst = Tiny(3)
        load_state_checked(dst, src.state_dict(), allow_partial=True, label="t")
        self.assertTrue(torch.equal(dst.head.weight, src.head.weight),
                        "passende Teile werden trotz Abweichung geladen")

    def test_error_is_an_exception_for_the_train_autoexport(self):
        self.assertTrue(issubclass(PartialLoadError, Exception))
        text = (REPO / "train.py").read_text(encoding="utf-8")
        auto = text[text.index("from export_onnx import export"):]
        self.assertIn("except Exception as e:", auto[:400])

    def test_export_default_is_strict(self):
        import inspect
        self.assertIs(inspect.signature(export_onnx.export).parameters["allow_partial_load"].default,
                      False)


if __name__ == "__main__":
    unittest.main()
