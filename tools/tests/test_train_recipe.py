# -*- coding: utf-8 -*-
"""Rezeptdatei in `train.py` (Klasse = Trainings-Arm; docs/working_rules.md
"Rezeptdatei statt langer Flag-Listen").

Gegen den ECHTEN Parser von train.py (per `ast` aus dem Quelltext,
`source_parser.py`; train.py selbst wird nicht importiert):

* das Rezept setzt die Werte (am Beispiel des v33-Arm-Rezepts aus
  tools/night_v33_b03_b04.sh, `train_arm`), die Klasse ueberschreibt `common`;
* ein unbekannter Schluessel bricht ab, `MOSAIC_MOON_TARGET_SOURCE` im env auch
  (train.py setzt die Variable selbst aus --moon-target-source);
* ohne Rezept ist das Parse-Ergebnis das bisherige;
* das Trainings-Manifest traegt `recipe` und `mosaic_env`;
* das Rezept-env greift VOR `import torch` und vor dem ersten Projekt-Import;
* Code-Review #23: der Ueberschreib-Waechter steht vor dem Datenaufbau und
  laesst --resume durch.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from source_parser import module_literal, parser_from_main_block  # noqa: E402
from tools.recipe_config import (RecipeError, apply_recipe_env_from_argv,  # noqa: E402
                                 apply_to_parser, mosaic_env_snapshot)

TRAIN = REPO / "train.py"

# Das Arm-Rezept aus tools/night_v33_b03_b04.sh `train_arm` (bis auf die Laufteile).
V33_ARM_ARGV = ["--name", "v33-b03", "--load", "v32-b01_brierbest",
                "--file-list", "data/window_v33_b03_train.txt", "--cache-file", "data/.cache_x.h5",
                "--epochs", "12", "--lr", "5e-05", "--lr-schedule", "cosine", "--lr-t-max", "12",
                "--val-frac", "0.1", "--encoder", "2d", "--value-head", "wdl",
                "--value-target-variant", "nortv", "--value-target-lambda", "0.7",
                "--ownership-head-2d", "--ownership-weight", "0.0", "--moon-loss-weight", "0.0",
                "--opp-points-head", "--destretch-a", "0.0051", "--destretch-b", "1.9269",
                "--select-by-brier", "--fast-loader", "--seed", "20260957"]

ARM_RECIPE = {
    "recipe_version": 1, "tool": "train",
    "description": "Test: v33-Arm-Rezept",
    "common": {"load": "v32-b01_brierbest", "epochs": 12, "lr": 5e-05, "lr_schedule": "cosine",
               "lr_t_max": 12, "encoder": "2d", "value_head": "wdl",
               "value_target_variant": "nortv", "value_target_lambda": 0.7,
               "ownership_head_2d": True, "ownership_weight": 0.0, "moon_loss_weight": 0.0,
               "opp_points_head": True, "destretch_a": 0.0051, "destretch_b": 1.9269,
               "select_by_brier": True, "fast_loader": True, "seed": 20260957},
    "env": {"MOSAIC_FEATURES_FROM_RUST": "1"},
    "classes": {
        "b03": {"name": "v33-b03", "file_list": "data/window_v33_b03_train.txt",
                "cache_file": "data/.cache_x.h5", "val_frac": 0.1},
        "b04": {"name": "v33-b04", "file_list": "data/window_v33_b04_train.txt",
                "cache_file": "data/.cache_y.h5", "val_frac": 0.2},
    },
}


def fresh_parser():
    # `--value-head` nimmt choices=list(VALUE_HEAD_VARIANTS) aus neural_net
    # (importiert torch) -- der Wert steht dort als Literal und wird gelesen.
    return parser_from_main_block(TRAIN, extra_names={
        "VALUE_HEAD_VARIANTS": module_literal(REPO / "engine" / "py" / "neural_net.py",
                                              "VALUE_HEAD_VARIANTS")})


def write_recipe(directory: Path, content: dict) -> Path:
    path = directory / "arm.recipe.json"
    path.write_text(json.dumps(content), encoding="utf-8")
    return path


class RecipeSetsValues(unittest.TestCase):
    def test_arm_recipe_reproduces_the_v33_command_line(self):
        plain = vars(fresh_parser().parse_args(V33_ARM_ARGV))
        with tempfile.TemporaryDirectory() as d:
            path = write_recipe(Path(d), ARM_RECIPE)
            ns, overrides = apply_to_parser(fresh_parser(), ["--recipe", str(path), "--class", "b03"],
                                            str(path), "b03", tool="train")
        via = vars(ns)
        self.assertEqual(overrides, {})
        self.assertEqual({k: via[k] for k in plain}, plain)

    def test_class_overrides_common(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_recipe(Path(d), ARM_RECIPE)
            ns, _ = apply_to_parser(fresh_parser(), ["--recipe", str(path), "--class", "b04"],
                                    str(path), "b04", tool="train")
        self.assertEqual((ns.name, ns.val_frac), ("v33-b04", 0.2))
        self.assertEqual(ns.lr, 5e-05)


class RecipeRejects(unittest.TestCase):
    def test_unknown_key_aborts(self):
        bad = json.loads(json.dumps(ARM_RECIPE))
        bad["common"]["epoch"] = 12
        with tempfile.TemporaryDirectory() as d:
            path = write_recipe(Path(d), bad)
            with self.assertRaises(RecipeError) as ctx:
                apply_to_parser(fresh_parser(), ["--recipe", str(path), "--class", "b03"],
                                str(path), "b03", tool="train")
        self.assertIn("'epoch'", str(ctx.exception))

    def test_self_play_recipe_is_refused(self):
        with self.assertRaises(RecipeError):
            apply_to_parser(fresh_parser(), None, str(REPO / "models" / "v34.recipe.json"),
                            "policy", tool="train")

    def test_moon_target_source_env_is_reserved(self):
        reserved_map = module_literal(TRAIN, "RECIPE_RESERVED_ENV")
        self.assertEqual(reserved_map, {"MOSAIC_MOON_TARGET_SOURCE": "moon_target_source"})
        bad = json.loads(json.dumps(ARM_RECIPE))
        bad["env"]["MOSAIC_MOON_TARGET_SOURCE"] = "played"
        with tempfile.TemporaryDirectory() as d:
            path = write_recipe(Path(d), bad)
            env = {}
            with self.assertRaises(RecipeError):
                apply_recipe_env_from_argv(["--recipe", str(path), "--class", "b03"], tool="train",
                                           reserved={k: v for k, v in reserved_map.items()},
                                           environ=env)
        self.assertEqual(env, {})

    def test_train_sets_the_reserved_variable_itself(self):
        text = TRAIN.read_text(encoding="utf-8")
        self.assertIn('os.environ["MOSAIC_MOON_TARGET_SOURCE"] = args.moon_target_source', text)


class WithoutRecipeUnchanged(unittest.TestCase):
    def test_parse_equals_plain_parse_args(self):
        plain = vars(fresh_parser().parse_args(V33_ARM_ARGV))
        ns, overrides = apply_to_parser(fresh_parser(), V33_ARM_ARGV, None, None, tool="train")
        via = vars(ns)
        self.assertEqual(overrides, {})
        self.assertEqual({k: via[k] for k in plain}, plain)
        self.assertEqual(set(via) - set(plain), {"recipe", "recipe_class"})
        self.assertIs(via["overwrite_model"], False)


class ManifestCarriesRecipe(unittest.TestCase):
    def _write(self, recipe_block):
        import train_manifest as tm
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(tm, "MODELS_DIR", Path(d)), \
                mock.patch.object(tm, "_git_commit_hash", lambda: "abc"), \
                mock.patch.object(tm, "_git_is_dirty", lambda: False), \
                mock.patch.object(tm, "_engine_config", lambda: {}):
            tm.write_train_manifest("vtest", {"name": "vtest"}, [], "20260927_000000",
                                    policy_carriers=None, recipe=recipe_block)
            return json.loads((Path(d) / "manifest_train_vtest_20260927_000000.json")
                              .read_text(encoding="utf-8"))

    def test_without_recipe(self):
        manifest = self._write(None)
        old = {"version", "run_timestamp", "cli_args", "git_commit", "git_dirty", "engine_config",
               "python_constants", "corpus_composition", "policy_carriers"}
        self.assertTrue(old <= set(manifest))
        self.assertEqual(set(manifest) - old, {"recipe", "mosaic_env"})
        self.assertIsNone(manifest["recipe"])
        self.assertEqual(manifest["mosaic_env"], mosaic_env_snapshot())

    def test_with_recipe_block(self):
        block = {"path": "x.recipe.json", "sha256": "0" * 64, "class": "b03",
                 "content": ARM_RECIPE, "overrides": {}, "mosaic_env": {}}
        manifest = self._write(block)
        self.assertEqual(manifest["recipe"], block)


class Ordering(unittest.TestCase):
    def setUp(self):
        self.text = TRAIN.read_text(encoding="utf-8")

    def test_recipe_env_is_applied_before_imports_that_read_it(self):
        applied = self.text.index("_RECIPE_PRE = apply_recipe_env_from_argv(")
        for marker in ("\nimport torch", "\nfrom freeze_trunk import", "\nfrom config import",
                       "\nfrom train_manifest import", "\nfrom corpus_dataset import",
                       "\nfrom neural_net import"):
            self.assertLess(applied, self.text.index(marker),
                            f"Rezept-env muss VOR `{marker.strip()}` stehen")

    def test_single_extra_parser_step(self):
        """Nur EIN zusaetzlicher Schritt: kein zweites parse_args im __main__-Block."""
        main = self.text[self.text.index('\nif __name__ == "__main__":\n    parser'):]
        self.assertNotIn("parser.parse_args(", main)
        self.assertEqual(main.count("apply_to_parser("), 1)

    def test_overwrite_guard_precedes_data_loading_and_spares_resume(self):
        body = self.text[self.text.index("\ndef train("):]
        guard = body.index("if not resume and not overwrite_model:")
        self.assertLess(guard, body.index("all_files"))
        self.assertLess(guard, body.index("write_train_manifest("))


if __name__ == "__main__":
    unittest.main()
