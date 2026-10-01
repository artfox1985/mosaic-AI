# -*- coding: utf-8 -*-
"""Rezeptdatei in `self_play.py` (STATUS Fahrplan 3e, docs/working_rules.md
"Rezeptdatei statt langer Flag-Listen").

Geprueft wird gegen den ECHTEN Parser von self_play.py (per `ast` aus dem
Quelltext gebaut, `source_parser.py`), ohne self_play.py zu importieren (das
zoege torch und das Wheel):

* das Rezept setzt die Werte, und `models/v34.recipe.json` passt fuer jede
  Klasse auf den Parser;
* der v34-Entwurf bildet die v33-Erzeugung Flag fuer Flag ab (gegen die
  Aufrufe in tools/night_v33_generate.sh und tools/night_v33_b03_b04.sh);
* ein unbekannter Schluessel bricht ab, eine vom Werkzeug selbst gesetzte
  Variable im `env` des Rezepts ebenso;
* ohne Rezept ist das Parse-Ergebnis das bisherige;
* das Manifest traegt `recipe` und `mosaic_env`, ohne Rezept `recipe: null`;
* das Rezept-env greift VOR `config`/`mosaic_rust`, der Waechter VOR dem Manifest.
"""
from __future__ import annotations

import json
import re
import shlex
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
                                 apply_to_parser, load_recipe, manifest_block,
                                 mosaic_env_snapshot)

SELF_PLAY = REPO / "self_play.py"
V34 = REPO / "models" / "v34.recipe.json"
V33_GENERATE = REPO / "tools" / "night_v33_generate.sh"
V33_B03_B04 = REPO / "tools" / "night_v33_b03_b04.sh"

# In v34 absichtlich anders als in v33: Platzhalter (null) und die neuen Knoepfe.
V34_SEEDS = {"policy": 20260946, "value-wegc": 20260947, "value-excursion": 20260948}
PLACEHOLDER_OR_NEW = {"model", "version", "seed", "tie_mirror_p", "label_rng_split",
                      "excursion_reshuffle", "excursion_kl_weight", "recipe", "recipe_class"}


def fresh_parser():
    return parser_from_main_block(SELF_PLAY)


def write_recipe(directory: Path, content: dict, name: str = "r.recipe.json") -> Path:
    path = directory / name
    path.write_text(json.dumps(content), encoding="utf-8")
    return path


def shell_command_args(script: Path) -> dict[str, list[str]]:
    """Alle `self_play.py`-Aufrufe eines Ketten-Skripts, Variablen aufgeloest,
    als Argumentliste -> {version: argv}."""
    text = script.read_text(encoding="utf-8")
    variables = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Z_][A-Z0-9_]*)=(\S+)\s*$", line.strip())
        if m and "$(" not in m.group(2) and "${1" not in m.group(2) and "${2" not in m.group(2):
            variables[m.group(1)] = m.group(2).strip('"')
    joined = re.sub(r"\\\n", " ", text)
    commands = {}
    for line in joined.splitlines():
        if "self_play.py" not in line:
            continue
        tail = line.split("self_play.py", 1)[1]
        tail = re.sub(r"\$\{?([A-Z_][A-Z0-9_]*)\}?",
                      lambda m: variables.get(m.group(1), m.group(0)), tail)
        argv = shlex.split(tail)
        if "--version" not in argv:
            continue  # Kommentar oder Meldung, kein Aufruf
        commands[argv[argv.index("--version") + 1]] = argv
    return commands


class RecipeSetsValues(unittest.TestCase):
    def test_v34_draft_fits_the_parser_for_every_class(self):
        recipe = load_recipe(V34)
        self.assertEqual(recipe["tool"], "self_play")
        self.assertEqual(sorted(recipe["classes"]), ["policy", "value-excursion", "value-wegc"])
        for cls in recipe["classes"]:
            with self.subTest(cls=cls):
                ns, overrides = apply_to_parser(fresh_parser(), ["--recipe", str(V34), "--class", cls],
                                                str(V34), cls, tool="self_play")
                self.assertEqual(overrides, {})
                self.assertEqual(ns.mode, "network")
                self.assertEqual((ns.games, ns.sims, ns.chunk, ns.per_file), (4000, 100, 10, 10))
                self.assertEqual(ns.return_order_random_p, 0.81)
                self.assertEqual(ns.tie_mirror_p, 0.5)
                self.assertIs(ns.label_rng_split, True)
                self.assertIs(ns.excursion_reshuffle, True)
                # Entschieden 2026-09-27/10-01 (PREREG_v34_window.md par.5): Generator v33-b01,
                # Seeds im Vierer-Schritt nach v33 (42/43/44).
                self.assertEqual(ns.seed, V34_SEEDS[cls])
                self.assertEqual(ns.model, "models/alphazero_v33-b01_brierbest.onnx")
                self.assertEqual(ns.version, f"v33-b01-{cls}")
                self.assertEqual(ns.spec, "models/v33_generation.spec.json")
        ns, _ = apply_to_parser(fresh_parser(), ["--recipe", str(V34), "--class", "value-wegc"],
                                str(V34), "value-wegc", tool="self_play")
        self.assertIs(ns.value_only, True)
        # v33-b03 fuhr 10 Threads nur wegen des parallelen b04-Trainings; v34 nimmt die 11 aus common.
        self.assertEqual(ns.threads, 11)

    def test_explicit_flag_is_recorded_as_override(self):
        argv = ["--recipe", str(V34), "--class", "policy", "--seed", "20261000"]
        ns, overrides = apply_to_parser(fresh_parser(), argv, str(V34), "policy", tool="self_play")
        self.assertEqual(ns.seed, 20261000)
        self.assertEqual(overrides, {"seed": {"recipe": V34_SEEDS["policy"], "cli": 20261000}})

    def test_v34_draft_mirrors_the_v33_generation_flag_by_flag(self):
        for script in (V33_GENERATE, V33_B03_B04):
            if not script.exists():
                self.skipTest(f"{script.name} fehlt (Generationswechsel raeumt Ketten-Skripte ab) -- "
                              "der Abgleich ist dann nur noch aus der Git-Historie moeglich")
        v33 = {**shell_command_args(V33_GENERATE), **shell_command_args(V33_B03_B04)}
        mapping = {"policy": "v32-b01-policy", "value-wegc": "v32-b01-value-wegc",
                   "value-excursion": "v32-b01-value-excursion"}
        for cls, version in mapping.items():
            with self.subTest(cls=cls):
                self.assertIn(version, v33, f"v33-Aufruf fuer {version} nicht gefunden")
                old = vars(fresh_parser().parse_args(v33[version]))
                new, _ = apply_to_parser(fresh_parser(), ["--recipe", str(V34), "--class", cls],
                                         str(V34), cls, tool="self_play")
                new = vars(new)
                diff = {k: (old.get(k), new.get(k)) for k in sorted(set(old) | set(new))
                        if k not in PLACEHOLDER_OR_NEW and old.get(k) != new.get(k)}
                # Gewollte Abweichungen: die Spec heisst nach dem Generator (Inhalt byte-gleich),
                # und Weg C faehrt 11 statt 10 Threads (PREREG_v34_window.md par.5 Punkt 2).
                spec_old, spec_new = diff.pop("spec", (None, None))
                if spec_old is not None:
                    self.assertEqual((REPO / spec_old).read_bytes(), (REPO / spec_new).read_bytes(),
                                     f"{cls}: Generator-Spec nicht byte-gleich")
                if cls == "value-wegc":
                    self.assertEqual(diff.pop("threads", None), (10, 11))
                self.assertEqual(diff, {}, f"{cls}: v34-Rezept weicht von v33 ab (v33, v34)")

    def test_v34_env_matches_the_v33_chain(self):
        recipe = load_recipe(V34)
        # E1 an und Runde 5 per Netz (Nutzer 2026-10-01), beide ueber env, damit auch die
        # Label-Pfade sie lesen (PREREG_v34_window.md par.5 Punkt 3).
        self.assertEqual(recipe["env"], {"MOSAIC_STACK_DRAW_RESEARCH": "1",
                                         "MOSAIC_SINGLE_PASS_OTHER_VAL": "1",
                                         "MOSAIC_R5_NET_SOLVER": "0"})


class RecipeRejects(unittest.TestCase):
    def test_unknown_key_aborts(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_recipe(Path(d), {"recipe_version": 1, "tool": "self_play",
                                          "common": {"mode": "network", "version": "x",
                                                     "simss": 100}})
            with self.assertRaises(RecipeError) as ctx:
                apply_to_parser(fresh_parser(), ["--recipe", str(path)], str(path), None,
                                tool="self_play")
        self.assertIn("simss", str(ctx.exception))
        self.assertIn("sims", str(ctx.exception).split("simss", 1)[1])

    def test_env_that_the_tool_sets_itself_is_rejected(self):
        reserved_map = module_literal(SELF_PLAY, "RECIPE_RESERVED_ENV")
        reserved = {name: f"Schluessel {dest!r}" for name, dest in reserved_map.items()}
        with tempfile.TemporaryDirectory() as d:
            path = write_recipe(Path(d), {"recipe_version": 1, "tool": "self_play",
                                          "env": {"MOSAIC_RETURN_ORDER_RANDOM_P": "0.81"}})
            env = {}
            with self.assertRaises(RecipeError) as ctx:
                apply_recipe_env_from_argv(["--recipe", str(path)], tool="self_play",
                                           reserved=reserved, environ=env)
        self.assertIn("return_order_random_p", str(ctx.exception))
        self.assertEqual(env, {}, "nichts darf gesetzt sein (alles oder nichts)")

    def test_every_worker_variable_is_reserved(self):
        """Jede Variable, die der Worker aus einem Flag setzt, muss reserviert sein --
        sonst koennte ein Rezept sie per env setzen und der Worker ueberschriebe sie still."""
        text = SELF_PLAY.read_text(encoding="utf-8")
        worker = text[text.index("def _worker_run_chunk("):text.index("def _recover_partial_progress(")]
        set_in_worker = set(re.findall(r'os\.environ\["(MOSAIC_[A-Z0-9_]+)"\]\s*=', worker))
        self.assertGreaterEqual(len(set_in_worker), 10, "Worker-Setzungen nicht gefunden -- Regex pruefen")
        reserved = set(module_literal(SELF_PLAY, "RECIPE_RESERVED_ENV"))
        self.assertEqual(sorted(set_in_worker - reserved), [])
        # Und jeder reservierte Name zeigt auf einen existierenden dest.
        dests = {a.dest for a in fresh_parser()._actions}
        for name, dest in module_literal(SELF_PLAY, "RECIPE_RESERVED_ENV").items():
            self.assertIn(dest, dests, f"{name} verweist auf unbekannten dest {dest!r}")


class WithoutRecipeUnchanged(unittest.TestCase):
    V33_LIKE = ["--mode", "network", "--model", "m.onnx", "--spec", "s.spec.json",
                "--games", "4000", "--sims", "100", "--value-only", "--version", "v-x",
                "--threads", "11", "--chunk", "10", "--per-file", "10", "--seed", "1",
                "--return-order-random-p", "0.81", "--excursion-prob", "1.0",
                "--tau-argmax-from-move", "1", "--no-root-noise", "--start-slot-random-p", "0.15"]

    def test_parse_equals_plain_parse_args(self):
        plain = vars(fresh_parser().parse_args(self.V33_LIKE))
        ns, overrides = apply_to_parser(fresh_parser(), self.V33_LIKE, None, None, tool="self_play")
        via = vars(ns)
        self.assertEqual(overrides, {})
        self.assertEqual({k: via[k] for k in plain}, plain)
        self.assertEqual(set(via) - set(plain), {"recipe", "recipe_class"})
        self.assertIsNone(via["recipe"])
        # Die neuen Knoepfe bleiben ohne Flag "nicht gesetzt" -> Variable unberuehrt.
        self.assertIsNone(via["tie_mirror_p"])
        self.assertIs(via["label_rng_split"], False)
        self.assertIs(via["excursion_reshuffle"], False)
        self.assertIs(via["excursion_kl_weight"], False)

    def test_new_knobs_only_touch_the_environment_when_given(self):
        text = SELF_PLAY.read_text(encoding="utf-8")
        self.assertIn('if tie_mirror_p is not None:\n        os.environ["MOSAIC_TIE_MIRROR_P"]', text)
        self.assertIn('if label_rng_split:\n        os.environ["MOSAIC_LABEL_RNG_SPLIT"] = "1"', text)
        self.assertIn('if excursion_reshuffle:\n        os.environ["MOSAIC_EXCURSION_RESHUFFLE"] = "1"',
                      text)
        self.assertIn('if excursion_kl_weight:\n        os.environ["MOSAIC_EXCURSION_KL_WEIGHT"] = "1"',
                      text)


class ManifestCarriesRecipe(unittest.TestCase):
    OLD_KEYS = {"version", "run_timestamp", "cli_args", "git_commit", "git_dirty",
                "engine_config", "spec_file"}

    def _write(self, recipe_block):
        import selfplay_manifest as sm
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(sm, "DATA_DIR", Path(d)), \
                mock.patch.object(sm, "_git_commit_hash", lambda: "abc"), \
                mock.patch.object(sm, "_git_is_dirty", lambda: False), \
                mock.patch.object(sm, "_engine_config", lambda: {"tie_mirror_p": 0.0}):
            sm._write_run_manifest("vtest", "20260927_000000", {"games": 1, "spec": None},
                                   recipe=recipe_block)
            return json.loads((Path(d) / "manifest_vtest_20260927_000000.json")
                              .read_text(encoding="utf-8"))

    def test_without_recipe_old_fields_plus_null_recipe_and_env(self):
        manifest = self._write(None)
        self.assertEqual(set(manifest) - self.OLD_KEYS, {"recipe", "mosaic_env", "engine_config_parent"})
        self.assertTrue(self.OLD_KEYS <= set(manifest))
        self.assertIsNone(manifest["recipe"])
        self.assertEqual(manifest["mosaic_env"], mosaic_env_snapshot())
        self.assertEqual(manifest["cli_args"], {"games": 1, "spec": None})

    def test_with_recipe_block(self):
        recipe = load_recipe(V34)
        block = manifest_block(recipe, recipe.path, "policy", {"seed": {"recipe": None, "cli": 7}})
        manifest = self._write(block)
        self.assertEqual(manifest["recipe"]["sha256"], recipe.sha256)
        self.assertEqual(manifest["recipe"]["class"], "policy")
        self.assertEqual(manifest["recipe"]["content"], json.loads(V34.read_text(encoding="utf-8")))
        self.assertEqual(manifest["recipe"]["overrides"], {"seed": {"recipe": None, "cli": 7}})
        self.assertIsInstance(manifest["mosaic_env"], dict)


class Ordering(unittest.TestCase):
    def setUp(self):
        self.text = SELF_PLAY.read_text(encoding="utf-8")

    def test_recipe_env_is_applied_before_config_and_engine_imports(self):
        applied = self.text.index("_RECIPE_PRE = apply_recipe_env_from_argv(")
        for marker in ("from config import", "import mosaic_rust as _mr", "import torch",
                       "from selfplay_manifest import", "from corpus_io import"):
            self.assertLess(applied, self.text.index(marker),
                            f"Rezept-env muss VOR `{marker}` stehen (OnceLock/Import-Zeit-Lesen)")

    def test_guard_runs_before_manifest_and_first_chunk(self):
        body = self.text[self.text.index("def generate_data("):]
        guard = body.index("check_engine_config(")
        self.assertLess(guard, body.index("_write_run_manifest(version_name"))
        self.assertLess(guard, body.index("make_chunk(n, chunk_idx"))

    def test_new_knobs_reach_the_worker_before_the_engine_import(self):
        worker = self.text[self.text.index("def _worker_run_chunk("):]
        import_at = worker.index("import mosaic_rust as mr")
        for env in ("MOSAIC_TIE_MIRROR_P", "MOSAIC_LABEL_RNG_SPLIT", "MOSAIC_EXCURSION_RESHUFFLE",
                    "MOSAIC_EXCURSION_KL_WEIGHT"):
            self.assertLess(worker.index(f'os.environ["{env}"]'), import_at)


if __name__ == "__main__":
    unittest.main()
