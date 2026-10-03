# -*- coding: utf-8 -*-
"""Policy-Masken des asymmetrischen Self-Plays in der Bauschleife (Bauplan 7, Tests 8.3).

`evaluations/PREREG_asymmetric_selfplay.md` par.3/par.3a:

* S-Maske: Records der Stoerer-Seite (`player == aggr_side`) mit `own_q_gap > eps`
  bekommen Policy-Gewicht 0; eps aus `MOSAIC_AGGR_OWN_Q_EPS`, ungesetzt = Maske aus.
* W-Maske (optional): Ausloeser-Records (`dice_trigger: true`) hinter
  `MOSAIC_MASK_DICE_TRIGGER=1`.
* Beide Knoepfe stehen in BEIDEN Cache-Schluesseln (Block und Fenster), nur als
  Marker, wenn gesetzt -- ohne Knopf bleibt jeder vorhandene Schluessel.
* Wertziele bleiben: die Maske beruehrt nur `pol_w`.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))

CORPUS_DATASET = REPO / "engine" / "py" / "corpus_dataset.py"
FILE_CACHE_KEY = REPO / "engine" / "py" / "file_cache_key.py"
EPS_ENV = "MOSAIC_AGGR_OWN_Q_EPS"
DICE_ENV = "MOSAIC_MASK_DICE_TRIGGER"


class _Env:
    """Setzt/entfernt Variablen fuer die Dauer des Blocks (None = entfernen)."""

    def __init__(self, **values):
        self.values, self.before = values, {}

    def __enter__(self):
        for k, v in self.values.items():
            self.before[k] = os.environ.get(k)
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return self

    def __exit__(self, *_):
        for k, v in self.before.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return False


class MaskRule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import corpus_dataset
        cls.f = staticmethod(corpus_dataset.asymmetric_policy_masked)

    def test_without_knobs_nothing_is_masked(self):
        for step in ({"player": 1, "aggr_side": 1, "own_q_gap": 0.9},
                     {"player": 0, "dice_trigger": True},
                     {"player": 0}):
            self.assertFalse(self.f(step, None, False), step)

    def test_aggressor_mask_by_eps(self):
        s = {"player": 1, "aggr_side": 1, "own_q_gap": 0.05}
        self.assertTrue(self.f(s, 0.02, False), "gap > eps -> maskiert")
        self.assertFalse(self.f(s, 0.05, False), "gap == eps kommt durch (<= eps)")
        self.assertFalse(self.f(s, 0.10, False))
        self.assertFalse(self.f({"player": 0, "aggr_side": 1, "own_q_gap": 0.9}, 0.0, False),
                         "die G-Seite wird nie maskiert")
        self.assertFalse(self.f({"player": 1, "aggr_side": 1}, 0.0, False),
                         "Stoerer-Record ohne echte Suche (kein own_q_gap) bleibt")
        self.assertFalse(self.f({"player": 1, "own_q_gap": 0.9}, 0.0, False),
                         "ohne aggr_side keine S-Partie")

    def test_dice_trigger_mask(self):
        self.assertTrue(self.f({"player": 0, "dice_trigger": True}, None, True))
        self.assertFalse(self.f({"player": 0}, None, True))
        self.assertFalse(self.f({"player": 0, "dice_trigger": True}, None, False))


class CacheKeys(unittest.TestCase):
    FILES = ["selfplay_asym_a.pkl", "selfplay_asym_b.pkl"]
    WINDOW_KW = dict(value_target_variant="nortv", encoder="2d", conjunction_head=False)
    BLOCK_KW = dict(value_target_variant="nortv", encoder="2d", conjunction_head=False,
                    bootstrap_native=True)

    def _keys(self):
        import corpus_dataset
        from file_cache_key import per_file_cache_key
        wk = corpus_dataset.window_cache_key("data", self.FILES, **self.WINDOW_KW)
        return wk.key, wk.material, per_file_cache_key(self.FILES[0], **self.BLOCK_KW)

    def test_without_knobs_no_marker(self):
        with _Env(**{EPS_ENV: None, DICE_ENV: None}):
            w0, material, b0 = self._keys()
        with _Env(**{EPS_ENV: "", DICE_ENV: "0"}):
            w1, _, b1 = self._keys()
        self.assertNotIn("aggrownq", material)
        self.assertNotIn("maskdicetrigger", material)
        self.assertEqual((w0, b0), (w1, b1), "leer bzw. '0' ist Bestand")

    def test_eps_changes_both_keys_and_is_canonical(self):
        with _Env(**{EPS_ENV: None, DICE_ENV: None}):
            w0, _, b0 = self._keys()
        with _Env(**{EPS_ENV: "0.02", DICE_ENV: None}):
            w1, material, b1 = self._keys()
        with _Env(**{EPS_ENV: "0.020", DICE_ENV: None}):
            w2, _, b2 = self._keys()
        with _Env(**{EPS_ENV: "0.05", DICE_ENV: None}):
            w3, _, b3 = self._keys()
        self.assertIn("+aggrownq_eps0.02_v1", material)
        self.assertNotEqual(w0, w1, "Fenster-Schluessel ignoriert MOSAIC_AGGR_OWN_Q_EPS")
        self.assertNotEqual(b0, b1, "Block-Schluessel ignoriert MOSAIC_AGGR_OWN_Q_EPS")
        self.assertEqual((w1, b1), (w2, b2), "gleiche Zahl, gleiche Schluessel")
        self.assertNotEqual(w1, w3, "anderes eps, anderer Fenster-Schluessel")
        self.assertNotEqual(b1, b3, "anderes eps, anderer Block-Schluessel")

    def test_invalid_eps_is_a_hard_error(self):
        from file_cache_key import _aggr_own_q_eps_key
        for bad in ("abc", "nan", "inf"):
            with _Env(**{EPS_ENV: bad}):
                with self.assertRaises(ValueError):
                    _aggr_own_q_eps_key()

    def test_dice_trigger_knob_changes_both_keys(self):
        with _Env(**{EPS_ENV: None, DICE_ENV: None}):
            w0, _, b0 = self._keys()
        with _Env(**{EPS_ENV: None, DICE_ENV: "1"}):
            w1, material, b1 = self._keys()
        self.assertIn("+maskdicetrigger_v1", material)
        self.assertNotEqual(w0, w1, "Fenster-Schluessel ignoriert MOSAIC_MASK_DICE_TRIGGER")
        self.assertNotEqual(b0, b1, "Block-Schluessel ignoriert MOSAIC_MASK_DICE_TRIGGER")


class DicePlaceMask(unittest.TestCase):
    """par.3c: Platzwahl-Record -> Legalitaetsmaske nur ueber `dice_place_ids`."""

    @classmethod
    def setUpClass(cls):
        import numpy as np
        import corpus_dataset
        cls.np = np
        cls.f = staticmethod(corpus_dataset.restrict_mask_to_dice_place_ids)

    def test_without_field_mask_is_unchanged(self):
        mask = self.np.zeros(10, dtype=self.np.float32)
        mask[[1, 2, 7]] = 1.0
        out = self.f(mask, {"player": 0}, [1])
        self.assertIs(out, mask, "ohne Feld dasselbe Objekt (byte-identisch)")

    def test_field_restricts_the_mask_to_the_ids(self):
        mask = self.np.zeros(10, dtype=self.np.float32)
        mask[[1, 2, 3, 7, 9]] = 1.0  # alle legalen Plattenaktionen des Zustands
        out = self.f(mask, {"dice_place": True, "dice_place_ids": [2, 3]}, [3])
        self.assertEqual(out.nonzero()[0].tolist(), [2, 3], "Verlust nur ueber die Plaetze der Wuerfel-Platte")
        self.assertEqual(mask.nonzero()[0].tolist(), [1, 2, 3, 7, 9], "Eingabe unveraendert")
        out = self.f(mask, {"dice_place_ids": [2]}, [5])
        self.assertEqual(out.nonzero()[0].tolist(), [2, 5], "Policy-Aktionen bleiben (Selbstkonsistenz)")

    def test_build_loop_applies_it_before_append(self):
        text = CORPUS_DATASET.read_text(encoding="utf-8")
        call = "mask = restrict_mask_to_dice_place_ids(mask, step, pol_ids)"
        self.assertLess(text.index(call), text.index("masks_l.append(mask)"))


class BuildLoopWiring(unittest.TestCase):
    """Textnah: die Bauschleife wendet die Maske auf `pol_w` an, NACH den Bestandsmasken
    und VOR dem Anhaengen; die Knoepfe kommen aus denselben Lesern wie die Schluessel."""

    def test_mask_sits_before_polw_append(self):
        text = CORPUS_DATASET.read_text(encoding="utf-8")
        call = "if asymmetric_policy_masked(step, _aggr_own_q_eps, _mask_dice_trigger):"
        at = text.index(call)
        self.assertLess(text.index('if step.get("fallback_random_action") is True:'), at)
        self.assertLess(at, text.index("polw_l.append(np.float32(pol_w))"))
        self.assertIn("from file_cache_key import _aggr_own_q_eps_key, _mask_dice_trigger_key",
                      text[text.index("def __init__(self, data_dir="):])

    def test_block_key_source_has_the_markers(self):
        text = FILE_CACHE_KEY.read_text(encoding="utf-8")
        self.assertIn('material += "|aggrownq_eps" + _aggr_eps + "_v1"', text)
        self.assertIn('material += "|maskdicetrigger_v1"', text)


PHASE_ENV = "MOSAIC_MASK_DICE_PHASE_VALUE"
TRAIN = REPO / "train.py"


class DicePhaseValueMask(unittest.TestCase):
    """par.5d (Eroeffnungs-Wuerfel): unter `MOSAIC_MASK_DICE_PHASE_VALUE=1` bekommen
    Records mit `dice_phase: true` (beide Seiten) KEIN Wertziel. Mechanismus: das
    Zusatzfeld `value_weights` im Cache, train.py faltet es in den Gewichtsweg der
    Wertverluste (`rw`, wie --exclude-round5). Policy-Ziele bleiben."""

    def test_rule(self):
        import corpus_dataset
        f = corpus_dataset.dice_phase_value_weight
        self.assertEqual(f({"player": 0, "dice_phase": True}), 0.0)
        self.assertEqual(f({"player": 1, "dice_phase": True}), 0.0, "beide Seiten")
        self.assertEqual(f({"player": 0, "dice_phase": False}), 1.0)
        self.assertEqual(f({"player": 0}), 1.0, "ohne Feld (G-G, Alt-Korpus) bleibt das Wertziel")

    def test_policy_mask_is_untouched(self):
        import corpus_dataset
        for knob in (False, True):
            self.assertFalse(corpus_dataset.asymmetric_policy_masked(
                {"player": 0, "dice_phase": True}, None, knob), "dice_phase beruehrt pol_w nicht")

    def _keys(self):
        import corpus_dataset
        from file_cache_key import per_file_cache_key
        wk = corpus_dataset.window_cache_key("data", CacheKeys.FILES, **CacheKeys.WINDOW_KW)
        return wk.key, wk.material, per_file_cache_key(CacheKeys.FILES[0], **CacheKeys.BLOCK_KW)

    def test_knob_off_keeps_both_keys(self):
        with _Env(**{EPS_ENV: None, DICE_ENV: None, PHASE_ENV: None}):
            w0, material, b0 = self._keys()
        with _Env(**{EPS_ENV: None, DICE_ENV: None, PHASE_ENV: "0"}):
            w1, _, b1 = self._keys()
        self.assertNotIn("maskdicephasevalue", material)
        self.assertEqual((w0, b0), (w1, b1), "'0' ist Bestand")

    def test_knob_changes_both_keys(self):
        with _Env(**{EPS_ENV: None, DICE_ENV: None, PHASE_ENV: None}):
            w0, _, b0 = self._keys()
        with _Env(**{EPS_ENV: None, DICE_ENV: None, PHASE_ENV: "1"}):
            w1, material, b1 = self._keys()
        self.assertIn("+maskdicephasevalue_v1", material)
        self.assertNotEqual(w0, w1, "Fenster-Schluessel ignoriert MOSAIC_MASK_DICE_PHASE_VALUE")
        self.assertNotEqual(b0, b1, "Block-Schluessel ignoriert MOSAIC_MASK_DICE_PHASE_VALUE")

    def test_dataset_appends_the_field_only_with_the_knob(self):
        """Ohne Feld exakt die bisherige Tupel-Form; mit Feld als letztes Element,
        in `__getitem__` UND `get_batch`."""
        import torch
        import corpus_dataset
        ds = corpus_dataset.MosaicDataset.__new__(corpus_dataset.MosaicDataset)
        n = 3
        for name in corpus_dataset.MosaicDataset._BATCH_FIELDS:
            setattr(ds, name, torch.arange(n, dtype=torch.float32))
        ds.final_margin, ds.value_weights, ds.encoder = None, None, "flat"
        base_item, base_batch = ds[1], ds.get_batch([0, 2])
        self.assertEqual(len(base_item), len(corpus_dataset.MosaicDataset._BATCH_FIELDS))
        ds.value_weights = torch.tensor([1.0, 0.0, 1.0])
        item, batch = ds[1], ds.get_batch([0, 2])
        self.assertEqual(len(item), len(base_item) + 1)
        self.assertEqual(float(item[-1]), 0.0)
        self.assertEqual(batch[-1].tolist(), [1.0, 1.0])
        ds.final_margin = torch.tensor([5.0, -3.0, 0.0])
        item = ds[1]
        self.assertEqual((float(item[-2]), float(item[-1])), (-3.0, 0.0), "Wertgewicht HINTER der Endmarge")

    def test_build_loop_and_cache_wiring(self):
        text = CORPUS_DATASET.read_text(encoding="utf-8")
        init = text[text.index("def __init__(self, data_dir="):]
        self.assertIn("from file_cache_key import _mask_dice_phase_value_key", init)
        append = "value_weights_l.append(dice_phase_value_weight(step))"
        self.assertLess(text.index("values_l.append([val])"), text.index(append))
        self.assertLess(text.index(append), text.index("polw_l.append(np.float32(pol_w))"))
        self.assertIn("hf.create_dataset('value_weights'", text)
        self.assertIn("self.value_weights = torch.from_numpy(hf['value_weights'][:])", text)
        self.assertIn('material += "|maskdicephasevalue_v1"', FILE_CACHE_KEY.read_text(encoding="utf-8"))

    def test_train_folds_the_weight_into_the_value_path_after_the_policy_weight(self):
        """Die Maske wirkt NUR auf Wert-artige Verluste: das Falten in `rw` steht
        HINTER dem Policy-Verlust und VOR `rw2`/den Wertverlusten, in beiden
        Durchgaengen; das Feld wird vor der Endmarge abgetrennt."""
        text = TRAIN.read_text(encoding="utf-8")
        tr = text[text.index("def _train_one_epoch("):text.index("def _validate_one_epoch(")]
        fold = "rw = _vw if rw is None else rw * _vw"
        self.assertLess(tr.index("s_value_w = _batch[-1]"), tr.index("s_final_margin = _batch[-1]"))
        self.assertLess(tr.index("p_loss = (per_sample_ce * w).sum()"), tr.index(fold))
        self.assertLess(tr.index(fold), tr.index("rw2 = rw.view(-1, 1) if rw is not None else None"))
        va = text[text.index("def _validate_one_epoch("):]
        vfold = "v_rw = _v_vw if v_rw is None else v_rw * _v_vw"
        self.assertLess(va.index("v_value_w = _v_batch[-1]"), va.index("v_final_margin = _v_batch[-1]"))
        self.assertLess(va.index("v_p_loss = (v_per_sample_ce * v_w).sum()"), va.index(vfold))
        self.assertLess(va.index(vfold), va.index("v_rw2 = v_rw.view(-1, 1)"))

    def test_masked_value_loss_ignores_dice_phase_records(self):
        """Rechnerisch: mit Gewicht 0 traegt ein Record nichts zum Wertverlust bei
        (dieselbe Formel wie der rw-Zweig in train.py), Policy-Verlust unveraendert."""
        import torch
        import torch.nn.functional as F
        logit = torch.tensor([0.3, -1.2, 2.0])
        target = torch.tensor([0.9, 0.1, 0.0])
        vw = torch.tensor([1.0, 0.0, 1.0]).view(-1, 1)
        bce = F.binary_cross_entropy_with_logits(logit, target, reduction="none")
        masked = (bce.view(-1, 1) * vw).sum() / vw.sum()
        ref = F.binary_cross_entropy_with_logits(logit[[0, 2]], target[[0, 2]])
        self.assertAlmostEqual(float(masked), float(ref), places=6)


if __name__ == "__main__":
    unittest.main()
