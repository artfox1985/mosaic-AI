# -*- coding: utf-8 -*-
"""Rezeptdatei in `tools/paired_gating.py` (Klasse = Lauf; docs/working_rules.md
"Rezeptdatei statt langer Flag-Listen").

Das Gating laeuft hier gegen ein ATTRAPPEN-`mosaic_rust` (sys.modules), kein
Wheel, kein Netz: `net_vs_net_arena_match` liefert feste Records,
`engine_config_json` eine feste Konfiguration. Der Trend-Log-Eintrag
(`append_run`) ist abgeklemmt, damit der Test nichts ins Repo schreibt.

Geprueft: das Rezept setzt die Werte, ein unbekannter Schluessel bricht ab,
das Artefakt traegt `recipe` und `mosaic_env` (ohne Rezept `recipe: null` und
sonst die bisherigen Felder), der Waechter bricht bei Abweichung VOR dem ersten
Block ab.
"""
from __future__ import annotations

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

import paired_gating as pg  # noqa: E402
from recipe_config import (RecipeError, apply_recipe_env_from_argv,  # noqa: E402
                           apply_to_parser, load_recipe, manifest_block, mosaic_env_snapshot)

# Feldmenge des Artefakts VOR der Rezeptdatei (run_paired_gating, Stand 2026-09-26).
OLD_RESULT_KEYS = {
    "name_a", "name_b", "model_a", "model_b", "spec_a", "spec_b", "sims_a", "sims_b",
    "c_puct_a", "c_puct_b", "done_pairs", "n_games_total", "a_wins_total", "b_wins_total",
    "pair_a_sweeps_b", "pair_b_sweeps_c", "pair_splits", "sprt_verdict", "sprt_llr",
    "sprt_bounds", "sprt_p0", "sprt_p1", "sprt_alpha", "sprt_beta", "report_mcnemar_p",
    "mean_pair_diff", "ci95", "base_seed", "blocks", "avg_score_a", "avg_score_b",
    "per_pair_scores", "avg_floor_a", "avg_floor_b", "zerozero_anteil", "laufzeit",
}

GATING_RECIPE = {
    "recipe_version": 1, "tool": "paired_gating",
    "common": {"model_a": "a.onnx", "model_b": "b.onnx", "name_a": "A", "name_b": "B",
               "sims_a": 400, "sims_b": 400, "c_puct": 1.5, "block_size": 5, "max_pairs": 5,
               "sprt_alpha": 1e-12, "sprt_beta": 1e-12, "threads": 1, "log_games": False,
               "promote_winner": False},
    "classes": {"s1": {"seed": 20261680}, "s2": {"seed": 20261681}},
    "expect_engine_config": {"tie_mirror_p": 0.5},
}


def fake_engine(engine_config: dict):
    """Attrappe: Brett 0 gewinnt jede Partie (-> nur Splits), feste Punkte."""
    def net_vs_net_arena_match(model_a, model_b, sims_a, sims_b, n_games, seed, num_threads,
                               c_puct_a, c_puct_b, spec_a=None, spec_b=None, **_):
        return json.dumps([{"winner": 0, "scores": [30, 20], "total_floor": [1, 2]}
                           for _ in range(n_games)])
    module = types.ModuleType("mosaic_rust")
    module.net_vs_net_arena_match = net_vs_net_arena_match
    module.engine_config_json = lambda: json.dumps(engine_config)
    return module


def write_recipe(directory: Path, content: dict) -> Path:
    path = directory / "gating.recipe.json"
    path.write_text(json.dumps(content), encoding="utf-8")
    return path


class RecipeSetsValues(unittest.TestCase):
    def test_class_and_common_reach_the_namespace(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_recipe(Path(d), GATING_RECIPE)
            ns, overrides = apply_to_parser(pg.build_parser(),
                                            ["--recipe", str(path), "--class", "s2"],
                                            str(path), "s2", tool="paired_gating")
        self.assertEqual(overrides, {})
        self.assertEqual((ns.model_a, ns.model_b, ns.seed), ("a.onnx", "b.onnx", 20261681))
        self.assertEqual((ns.sprt_alpha, ns.max_pairs, ns.threads), (1e-12, 5, 1))
        self.assertIs(ns.promote_winner, False)

    def test_unknown_key_aborts(self):
        bad = json.loads(json.dumps(GATING_RECIPE))
        bad["common"]["max_pair"] = 200
        with tempfile.TemporaryDirectory() as d:
            path = write_recipe(Path(d), bad)
            with self.assertRaises(RecipeError) as ctx:
                apply_to_parser(pg.build_parser(), ["--recipe", str(path), "--class", "s1"],
                                str(path), "s1", tool="paired_gating")
        self.assertIn("max_pair", str(ctx.exception))

    def test_without_recipe_parse_unchanged(self):
        argv = ["--model-a", "a.onnx", "--model-b", "b.onnx", "--sims-a", "400", "--sims-b", "400",
                "--c-puct", "1.5", "--block-size", "5", "--max-pairs", "200", "--sprt-alpha", "1e-12",
                "--sprt-beta", "1e-12", "--seed", "1", "--threads", "10", "--log-games",
                "--no-promote-winner", "--out", "x.json"]
        plain = vars(pg.build_parser().parse_args(argv))
        ns, overrides = apply_to_parser(pg.build_parser(), argv, None, None, tool="paired_gating")
        via = vars(ns)
        self.assertEqual(overrides, {})
        self.assertEqual({k: via[k] for k in plain}, plain)
        self.assertEqual(set(via) - set(plain), {"recipe", "recipe_class"})


class ArtifactCarriesRecipe(unittest.TestCase):
    def _run(self, engine_config, **kwargs):
        with mock.patch.dict(sys.modules, {"mosaic_rust": fake_engine(engine_config)}), \
                mock.patch.object(pg, "append_run", lambda **_: None):
            return pg.run_paired_gating("a.onnx", "b.onnx", name_a="A", name_b="B",
                                        sims_a=10, sims_b=10, block_size=5, max_pairs=5,
                                        base_seed=1, threads=1, **kwargs)

    def test_without_recipe_old_fields_plus_null_recipe_and_env(self):
        result = self._run({})
        self.assertTrue(OLD_RESULT_KEYS <= set(result))
        self.assertEqual(set(result) - OLD_RESULT_KEYS, {"recipe", "mosaic_env"})
        self.assertIsNone(result["recipe"])
        self.assertEqual(result["mosaic_env"], mosaic_env_snapshot())
        self.assertEqual(result["pair_splits"], 5)

    def test_with_recipe_block_and_green_guard(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_recipe(Path(d), GATING_RECIPE)
            recipe = load_recipe(path)
            block = manifest_block(recipe, recipe.path, "s1", {})
        result = self._run({"tie_mirror_p": 0.5, "other": 1},
                           expected_engine_config=recipe["expect_engine_config"],
                           recipe_block=block)
        self.assertEqual(result["recipe"]["sha256"], recipe.sha256)
        self.assertEqual(result["recipe"]["class"], "s1")
        self.assertEqual(result["recipe"]["engine_config_check"]["deviations"], [])
        self.assertIsInstance(result["mosaic_env"], dict)

    def test_guard_aborts_before_the_first_block(self):
        calls = []
        engine = fake_engine({"tie_mirror_p": 0.0})
        original = engine.net_vs_net_arena_match
        engine.net_vs_net_arena_match = lambda *a, **k: calls.append(1) or original(*a, **k)
        with mock.patch.dict(sys.modules, {"mosaic_rust": engine}), \
                mock.patch.object(pg, "append_run", lambda **_: None):
            with self.assertRaises(SystemExit) as ctx:
                pg.run_paired_gating("a.onnx", "b.onnx", block_size=5, max_pairs=5, base_seed=1,
                                     threads=1, expected_engine_config={"tie_mirror_p": 0.5})
        self.assertIn("tie_mirror_p", str(ctx.exception))
        self.assertEqual(calls, [], "kein Block darf vor dem Waechter laufen")

    def test_main_writes_recipe_into_the_artifact(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_recipe(Path(d), GATING_RECIPE)
            out = Path(d) / "result.json"
            argv = ["--recipe", str(path), "--class", "s1", "--out", str(out)]
            pre = apply_recipe_env_from_argv(argv, tool="paired_gating", environ={})
            with mock.patch.dict(sys.modules, {"mosaic_rust": fake_engine({"tie_mirror_p": 0.5})}), \
                    mock.patch.object(pg, "append_run", lambda **_: None):
                pg.main(argv, recipe_pre=pre)
            artifact = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(artifact["recipe"]["class"], "s1")
        self.assertEqual(artifact["recipe"]["overrides"],
                         {}, "--out steht nicht im Rezept, ist also keine Abweichung")
        self.assertEqual(artifact["base_seed"], 20261680)
        self.assertIn("mosaic_env", artifact)


if __name__ == "__main__":
    unittest.main()
