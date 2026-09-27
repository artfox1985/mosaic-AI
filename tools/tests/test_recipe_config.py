# -*- coding: utf-8 -*-
"""Rezeptdatei-Helfer `tools/recipe_config.py` (Regel "Rezeptdatei statt langer
Flag-Listen", docs/working_rules.md, Nutzer 2026-09-26).

Die tragenden Zusagen des Helfers, je eine Testgruppe:

* ein unbekannter Schluessel bricht ab und nennt den naechstliegenden Namen
  (ein Tippfehler darf nicht still zum Default werden);
* die Klasse ueberschreibt `common`, fuer Argumente wie fuer `env`;
* ein explizites Kommandozeilen-Flag, das einen Rezeptwert ueberschreibt,
  wird als `overrides` gemeldet -- auch wenn es denselben Wert wiederholt;
* Schalter (store_true/false) und Typen werden gegen den Parser geprueft;
* `env` setzt nur `MOSAIC_*` und bricht bei einer Doppelquelle ab, ohne
  irgendetwas zu setzen;
* der Manifest-Block traegt sha256 der Datei und alle `MOSAIC_*`;
* der Engine-Waechter findet Abweichungen und fehlende Schluessel.

Gearbeitet wird mit einem Mini-Parser, der die Bauformen der echten Werkzeuge
nachstellt (Pflicht-Flag mit choices, zwei Flags auf einem dest), nicht mit
den Werkzeugen selbst. Nur Standardbibliothek, kein Wheel, kein torch;
`os.environ` wird NICHT beruehrt (alle Env-Tests laufen ueber `environ=`).
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import pathlib
import sys
import tempfile
import unittest

_TOOLS = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_TOOLS))

from recipe_config import (  # noqa: E402
    Recipe,
    RecipeError,
    apply_env,
    apply_recipe_env_from_argv,
    apply_to_parser,
    check_engine_config,
    load_recipe,
    manifest_block,
    mosaic_env_snapshot,
    resolve,
)


def make_parser() -> argparse.ArgumentParser:
    """Mini-Parser mit den Bauformen der Zielwerkzeuge: Pflicht-Flag mit
    choices (self_play `--mode`), int/float mit Default, float mit Default
    None (`--pcr-full-prob`), store_true, zwei Flags auf EINEM dest
    (paired_gating `--promote-winner`/`--no-promote-winner`), eine Liste und
    eine append-Aktion (nicht rezeptfaehig)."""
    parser = argparse.ArgumentParser(prog="mini")
    parser.add_argument("--mode", type=str, required=True, choices=["mcts", "network"])
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--sims", type=int, default=100)
    parser.add_argument("--c-puct", dest="c_puct", type=float, default=1.5)
    parser.add_argument("--pcr-full-prob", dest="pcr_full_prob", type=float, default=None)
    parser.add_argument("--value-only", dest="value_only", action="store_true")
    parser.add_argument("--no-root-noise", action="store_true")
    parser.add_argument("--spec", type=str, default=None)
    parser.add_argument("--promote-winner", dest="promote_winner", action="store_true",
                        default=True)
    parser.add_argument("--no-promote-winner", dest="promote_winner", action="store_false")
    parser.add_argument("--profile", type=float, nargs="+", default=None)
    parser.add_argument("--tags", action="append", default=None)
    return parser


BASE_RECIPE = {
    "recipe_version": 1,
    "tool": "mini",
    "description": "Testrezept",
    "common": {"mode": "network", "games": 4000, "sims": 100},
    "env": {"MOSAIC_STACK_DRAW_RESEARCH": "1", "MOSAIC_RETURN_ORDER_MODE": "0"},
    "classes": {
        "policy": {"c_puct": 2.0, "env": {"MOSAIC_RETURN_ORDER_MODE": "1"}},
        "value": {"value_only": True, "sims": 50, "description": "Schwarm"},
    },
}


def base_content(**changes) -> dict:
    """Tiefe Kopie von BASE_RECIPE; `common_extra` wird in `common` gemischt,
    alle anderen Schluessel ersetzen die oberste Ebene."""
    content = json.loads(json.dumps(BASE_RECIPE))
    extra = changes.pop("common_extra", None)
    if extra:
        content["common"].update(extra)
    content.update(changes)
    return content


def quiet_parse_failure(test: unittest.TestCase, call) -> None:
    """argparse meldet Fehler per SystemExit und schreibt auf stderr --
    beides abfangen, damit die Testausgabe sauber bleibt."""
    with contextlib.redirect_stderr(io.StringIO()):
        with test.assertRaises(SystemExit):
            call()


class RecipeFileCase(unittest.TestCase):
    """Basis: Rezepte liegen in einem temporaeren Verzeichnis."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = pathlib.Path(tmp.name)

    def write(self, content, name: str = "r.recipe.json") -> pathlib.Path:
        path = self.dir / name
        text = content if isinstance(content, str) else json.dumps(content, indent=1)
        path.write_text(text, encoding="utf-8")
        return path

    def load(self, content=None, name: str = "r.recipe.json") -> Recipe:
        return load_recipe(self.write(base_content() if content is None else content, name))


class LoadRecipe(RecipeFileCase):
    def test_sha256_is_over_the_file_bytes(self):
        path = self.write(base_content())
        recipe = load_recipe(path)
        self.assertEqual(recipe.sha256, hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(recipe.path, str(path))
        self.assertEqual(dict(recipe), BASE_RECIPE)

    def test_wrong_version_aborts(self):
        with self.assertRaises(RecipeError) as ctx:
            self.load(base_content(recipe_version=2))
        self.assertIn("recipe_version", str(ctx.exception))

    def test_missing_tool_aborts(self):
        content = base_content()
        del content["tool"]
        with self.assertRaises(RecipeError):
            self.load(content)

    def test_unknown_section_aborts_with_suggestion(self):
        content = base_content()
        content["comon"] = {"games": 1}
        with self.assertRaises(RecipeError) as ctx:
            self.load(content)
        self.assertIn("comon", str(ctx.exception))
        self.assertIn("common", str(ctx.exception))

    def test_duplicate_key_aborts(self):
        """Ohne den Haken gewinnt in json.loads still die zweite Zeile."""
        text = ('{"recipe_version": 1, "tool": "mini", '
                '"common": {"games": 1, "games": 2}}')
        with self.assertRaises(RecipeError) as ctx:
            load_recipe(self.write(text))
        self.assertIn("games", str(ctx.exception))

    def test_env_name_without_prefix_is_rejected_on_load(self):
        with self.assertRaises(RecipeError) as ctx:
            self.load(base_content(env={"PATH": "x"}))
        self.assertIn("PATH", str(ctx.exception))

    def test_env_bool_is_rejected_on_load(self):
        with self.assertRaises(RecipeError):
            self.load(base_content(env={"MOSAIC_X": True}))

    def test_env_variable_in_argument_section_points_to_env(self):
        with self.assertRaises(RecipeError) as ctx:
            self.load(base_content(common_extra={"MOSAIC_X": "1"}))
        self.assertIn("env", str(ctx.exception))

    def test_reserved_dest_in_recipe_is_rejected(self):
        with self.assertRaises(RecipeError):
            self.load(base_content(common_extra={"recipe": "other.json"}))

    def test_byte_order_mark_is_tolerated(self):
        path = self.dir / "bom.recipe.json"
        raw = b"\xef\xbb\xbf" + json.dumps(base_content()).encode("utf-8")
        path.write_bytes(raw)
        recipe = load_recipe(path)
        self.assertEqual(recipe.sha256, hashlib.sha256(raw).hexdigest())

    def test_empty_classes_section_is_rejected(self):
        with self.assertRaises(RecipeError):
            self.load(base_content(classes={}))


class Resolve(RecipeFileCase):
    def test_class_overrides_common(self):
        args, env = resolve(self.load(), "policy")
        self.assertEqual(args, {"mode": "network", "games": 4000, "sims": 100, "c_puct": 2.0})
        self.assertEqual(env["MOSAIC_RETURN_ORDER_MODE"], "1")      # Klasse gewinnt
        self.assertEqual(env["MOSAIC_STACK_DRAW_RESEARCH"], "1")    # aus common

    def test_class_value_beats_common_value(self):
        args, _env = resolve(self.load(), "value")
        self.assertEqual(args["sims"], 50)
        self.assertTrue(args["value_only"])

    def test_class_meta_keys_are_not_arguments(self):
        args, _env = resolve(self.load(), "value")
        self.assertNotIn("description", args)
        self.assertNotIn("env", args)

    def test_missing_class_lists_the_available_ones(self):
        with self.assertRaises(RecipeError) as ctx:
            resolve(self.load(), "sockel")
        message = str(ctx.exception)
        self.assertIn("sockel", message)
        self.assertIn("policy", message)
        self.assertIn("value", message)

    def test_no_class_chosen_although_classes_exist(self):
        with self.assertRaises(RecipeError) as ctx:
            resolve(self.load(), None)
        self.assertIn("policy", str(ctx.exception))

    def test_without_classes_only_common_applies(self):
        content = base_content()
        del content["classes"]
        recipe = self.load(content)
        args, env = resolve(recipe, None)
        self.assertEqual(args, content["common"])
        self.assertEqual(env, content["env"])

    def test_class_chosen_but_recipe_has_none(self):
        """Still nur `common` zu fahren hiesse: `--class` wirkungslos, unbemerkt."""
        content = base_content()
        del content["classes"]
        with self.assertRaises(RecipeError):
            resolve(self.load(content), "policy")


class UnknownKeys(RecipeFileCase):
    def test_unknown_key_aborts_with_suggestion(self):
        recipe = self.load(base_content(common_extra={"gmes": 10}))
        with self.assertRaises(RecipeError) as ctx:
            apply_to_parser(make_parser(), [], recipe, "policy")
        message = str(ctx.exception)
        self.assertIn("gmes", message)
        self.assertIn("games", message)

    def test_flag_spelling_suggests_the_dest(self):
        recipe = self.load(base_content(common_extra={"c-puct": 2.0}))
        with self.assertRaises(RecipeError) as ctx:
            apply_to_parser(make_parser(), [], recipe, "value")
        self.assertIn("c_puct", str(ctx.exception))

    def test_all_problems_are_reported_at_once(self):
        recipe = self.load(base_content(common_extra={"gmes": 10, "simz": 5}))
        with self.assertRaises(RecipeError) as ctx:
            apply_to_parser(make_parser(), [], recipe, "value")
        self.assertIn("gmes", str(ctx.exception))
        self.assertIn("simz", str(ctx.exception))

    def test_help_is_not_a_recipe_key(self):
        recipe = self.load(base_content(common_extra={"help": True}))
        with self.assertRaises(RecipeError):
            apply_to_parser(make_parser(), [], recipe, "value")


class ApplyToParser(RecipeFileCase):
    def test_recipe_values_become_defaults(self):
        namespace, overrides = apply_to_parser(make_parser(), [], self.load(), "policy")
        self.assertEqual(namespace.mode, "network")
        self.assertEqual(namespace.games, 4000)
        self.assertEqual(namespace.c_puct, 2.0)
        self.assertEqual(namespace.sims, 100)
        self.assertEqual(overrides, {})

    def test_required_flag_is_satisfied_by_the_recipe(self):
        """`--mode` ist Pflicht; das Rezept liefert ihn, argv ist leer."""
        namespace, _ = apply_to_parser(make_parser(), [], self.load(), "value")
        self.assertEqual(namespace.mode, "network")

    def test_required_flag_stays_required_without_recipe(self):
        quiet_parse_failure(self, lambda: apply_to_parser(make_parser(), [], None, None))

    def test_without_recipe_it_is_a_plain_parse(self):
        namespace, overrides = apply_to_parser(make_parser(), ["--mode", "mcts"], None, None)
        self.assertEqual(namespace.mode, "mcts")
        self.assertEqual(namespace.games, 100)
        self.assertEqual(overrides, {})

    def test_cli_override_is_detected_and_logged(self):
        namespace, overrides = apply_to_parser(make_parser(), ["--games", "10"],
                                               self.load(), "policy")
        self.assertEqual(namespace.games, 10)
        self.assertEqual(overrides, {"games": {"recipe": 4000, "cli": 10}})

    def test_explicit_flag_with_equal_value_is_still_logged(self):
        """Der Wertvergleich wuerde das uebersehen; die Marke nicht."""
        _ns, overrides = apply_to_parser(make_parser(), ["--games", "4000"],
                                         self.load(), "policy")
        self.assertEqual(overrides, {"games": {"recipe": 4000, "cli": 4000}})

    def test_equals_form_is_detected(self):
        _ns, overrides = apply_to_parser(make_parser(), ["--c-puct=3"], self.load(), "policy")
        self.assertEqual(overrides, {"c_puct": {"recipe": 2.0, "cli": 3.0}})

    def test_flag_outside_the_recipe_is_not_an_override(self):
        namespace, overrides = apply_to_parser(make_parser(), ["--spec", "x.spec.json"],
                                               self.load(), "policy")
        self.assertEqual(namespace.spec, "x.spec.json")
        self.assertEqual(overrides, {})

    def test_parser_keeps_recipe_defaults_after_the_probe(self):
        parser = make_parser()
        apply_to_parser(parser, ["--games", "10"], self.load(), "policy")
        self.assertEqual(parser.get_default("games"), 4000)
        self.assertEqual(parser.get_default("c_puct"), 2.0)

    def test_tool_mismatch_aborts(self):
        with self.assertRaises(RecipeError) as ctx:
            apply_to_parser(make_parser(), [], self.load(), "policy", tool="train")
        self.assertIn("train", str(ctx.exception))

    def test_path_is_loaded_when_given_as_text(self):
        path = self.write(base_content())
        namespace, _ = apply_to_parser(make_parser(), [], str(path), "policy")
        self.assertEqual(namespace.games, 4000)


class SwitchesAndTypes(RecipeFileCase):
    def test_store_true_from_recipe(self):
        namespace, overrides = apply_to_parser(make_parser(), [], self.load(), "value")
        self.assertIs(namespace.value_only, True)
        self.assertEqual(overrides, {})

    def test_store_true_switched_on_by_cli_is_an_override(self):
        recipe = self.load(base_content(common_extra={"no_root_noise": False}))
        namespace, overrides = apply_to_parser(make_parser(), ["--no-root-noise"], recipe, "value")
        self.assertIs(namespace.no_root_noise, True)
        self.assertEqual(overrides, {"no_root_noise": {"recipe": False, "cli": True}})

    def test_shared_dest_store_false_from_recipe(self):
        recipe = self.load(base_content(common_extra={"promote_winner": False}))
        namespace, overrides = apply_to_parser(make_parser(), [], recipe, "value")
        self.assertIs(namespace.promote_winner, False)
        self.assertEqual(overrides, {})

    def test_shared_dest_overridden_by_the_other_flag(self):
        recipe = self.load(base_content(common_extra={"promote_winner": False}))
        namespace, overrides = apply_to_parser(make_parser(), ["--promote-winner"], recipe, "value")
        self.assertIs(namespace.promote_winner, True)
        self.assertEqual(overrides, {"promote_winner": {"recipe": False, "cli": True}})

    def test_int_is_accepted_for_float(self):
        recipe = self.load(base_content(common_extra={"c_puct": 2}))
        namespace, _ = apply_to_parser(make_parser(), [], recipe, "value")
        self.assertEqual(namespace.c_puct, 2.0)
        self.assertIsInstance(namespace.c_puct, float)

    def test_null_where_the_default_is_none(self):
        recipe = self.load(base_content(common_extra={"pcr_full_prob": None}))
        namespace, _ = apply_to_parser(make_parser(), [], recipe, "value")
        self.assertIsNone(namespace.pcr_full_prob)

    def test_list_argument(self):
        recipe = self.load(base_content(common_extra={"profile": [1, 0.5, 0]}))
        namespace, _ = apply_to_parser(make_parser(), [], recipe, "value")
        self.assertEqual(namespace.profile, [1.0, 0.5, 0.0])

    def test_wrong_type_aborts(self):
        cases = [
            ("games", "4000"),          # Zahl als Text
            ("games", 4000.5),          # Bruch fuer int
            ("games", True),            # bool ist in Python ein int -- hier nicht
            ("games", None),            # null, obwohl der Default 100 ist
            ("value_only", "yes"),      # Schalter braucht true/false
            ("value_only", 1),
            ("mode", "heuristic"),      # nicht in choices
            ("c_puct", "1.5"),
            ("spec", 3),
            ("profile", 1.0),           # nargs='+' verlangt eine Liste
            ("profile", []),
            ("profile", ["a"]),
            ("tags", ["x"]),            # append ist nicht rezeptfaehig
        ]
        for index, (key, value) in enumerate(cases):
            with self.subTest(key=key, value=value):
                recipe = self.load(base_content(common_extra={key: value}),
                                   name=f"type_{index}.recipe.json")
                with self.assertRaises(RecipeError) as ctx:
                    apply_to_parser(make_parser(), [], recipe, "value")
                self.assertIn(key, str(ctx.exception))


class CommandLineConsistency(RecipeFileCase):
    def test_recipe_on_the_command_line_must_be_the_applied_one(self):
        recipe = self.load()
        other = self.write(base_content(), name="other.recipe.json")
        with self.assertRaises(RecipeError):
            apply_to_parser(make_parser(), ["--recipe", str(other), "--class", "policy"],
                            recipe, "policy")

    def test_class_on_the_command_line_must_be_the_applied_one(self):
        recipe = self.load()
        with self.assertRaises(RecipeError):
            apply_to_parser(make_parser(), ["--recipe", recipe.path, "--class", "value"],
                            recipe, "policy")

    def test_matching_command_line_is_accepted(self):
        recipe = self.load()
        namespace, _ = apply_to_parser(make_parser(),
                                       ["--recipe", recipe.path, "--class", "policy"],
                                       recipe, "policy")
        self.assertEqual(namespace.recipe_class, "policy")

    def test_recipe_on_the_command_line_but_not_applied(self):
        """Der Vorab-Parse fehlt: dann waere `env` nie gesetzt worden."""
        path = self.write(base_content())
        with self.assertRaises(RecipeError):
            apply_to_parser(make_parser(), ["--mode", "mcts", "--recipe", str(path)], None, None)


class ApplyEnv(unittest.TestCase):
    def test_only_mosaic_names(self):
        environ = {}
        with self.assertRaises(RecipeError):
            apply_env({"PATH": "x"}, environ=environ)
        self.assertEqual(environ, {})

    def test_values_become_text(self):
        environ = {}
        report = apply_env({"MOSAIC_A": 1, "MOSAIC_B": 0.81, "MOSAIC_C": "x"}, environ=environ)
        self.assertEqual(environ, {"MOSAIC_A": "1", "MOSAIC_B": "0.81", "MOSAIC_C": "x"})
        self.assertEqual(len(report["set"]), 3)

    def test_bool_and_list_values_are_rejected(self):
        for value in (True, None, [1, 2]):
            with self.subTest(value=value):
                with self.assertRaises(RecipeError):
                    apply_env({"MOSAIC_A": value}, environ={})

    def test_double_source_aborts_and_sets_nothing(self):
        environ = {"MOSAIC_A": "1"}
        with self.assertRaises(RecipeError) as ctx:
            apply_env({"MOSAIC_A": "2", "MOSAIC_B": "3"}, environ=environ)
        self.assertIn("MOSAIC_A", str(ctx.exception))
        self.assertEqual(environ, {"MOSAIC_A": "1"})     # alles-oder-nichts

    def test_same_value_is_no_conflict(self):
        environ = {"MOSAIC_A": "1"}
        report = apply_env({"MOSAIC_A": 1}, environ=environ)
        self.assertEqual(report["unchanged"], ["MOSAIC_A"])

    def test_allow_existing_replaces_and_reports(self):
        environ = {"MOSAIC_A": "1"}
        report = apply_env({"MOSAIC_A": "2"}, allow_existing=True, environ=environ)
        self.assertEqual(environ["MOSAIC_A"], "2")
        self.assertEqual(report["replaced"], ["MOSAIC_A: 1 -> 2"])

    def test_reserved_name_is_rejected_with_hint(self):
        reserved = {"MOSAIC_RETURN_ORDER_RANDOM_P": "Schluessel return_order_random_p nehmen"}
        environ = {}
        with self.assertRaises(RecipeError) as ctx:
            apply_env({"MOSAIC_RETURN_ORDER_RANDOM_P": "0.81"}, reserved=reserved,
                      environ=environ)
        self.assertIn("return_order_random_p", str(ctx.exception))
        self.assertEqual(environ, {})


class EarlyEnvFromArgv(RecipeFileCase):
    def test_sets_the_class_env_and_ignores_other_flags(self):
        path = self.write(base_content())
        environ = {}
        result = apply_recipe_env_from_argv(
            ["--recipe", str(path), "--class", "policy", "--games", "5"], environ=environ)
        self.assertEqual(environ, {"MOSAIC_STACK_DRAW_RESEARCH": "1",
                                   "MOSAIC_RETURN_ORDER_MODE": "1"})
        self.assertEqual(result["class"], "policy")
        self.assertIsInstance(result["recipe"], Recipe)

    def test_without_recipe_nothing_happens(self):
        environ = {}
        self.assertIsNone(apply_recipe_env_from_argv(["--games", "5"], environ=environ))
        self.assertEqual(environ, {})

    def test_class_without_recipe_aborts(self):
        with self.assertRaises(RecipeError):
            apply_recipe_env_from_argv(["--class", "policy"], environ={})

    def test_tool_mismatch_aborts_before_setting_env(self):
        path = self.write(base_content())
        environ = {}
        with self.assertRaises(RecipeError):
            apply_recipe_env_from_argv(["--recipe", str(path), "--class", "policy"],
                                       tool="train", environ=environ)
        self.assertEqual(environ, {})

    def test_early_result_feeds_apply_to_parser(self):
        path = self.write(base_content())
        argv = ["--recipe", str(path), "--class", "value", "--games", "7"]
        early = apply_recipe_env_from_argv(argv, environ={})
        namespace, overrides = apply_to_parser(make_parser(), argv, early["recipe"],
                                               early["class"])
        self.assertEqual(namespace.games, 7)
        self.assertEqual(overrides, {"games": {"recipe": 4000, "cli": 7}})


class ManifestBlock(RecipeFileCase):
    def test_block_carries_sha256_content_overrides_and_env(self):
        path = self.write(base_content())
        recipe = load_recipe(path)
        environ = {"MOSAIC_B": "2", "PATH": "x", "MOSAIC_A": "1"}
        overrides = {"games": {"recipe": 4000, "cli": 10}}
        block = manifest_block(recipe, path, "policy", overrides, environ=environ)
        self.assertEqual(block["path"], str(path))
        self.assertEqual(block["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(block["class"], "policy")
        self.assertEqual(block["content"], BASE_RECIPE)
        self.assertEqual(block["overrides"], overrides)
        self.assertEqual(list(block["mosaic_env"]), ["MOSAIC_A", "MOSAIC_B"])
        self.assertNotIn("PATH", block["mosaic_env"])
        json.dumps(block)  # muss ins Manifest passen

    def test_plain_dict_is_hashed_from_the_file(self):
        path = self.write(base_content())
        block = manifest_block(base_content(), path, None, {}, environ={})
        self.assertEqual(block["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_no_recipe_means_no_block(self):
        self.assertIsNone(manifest_block(None, None, None, {}))

    def test_env_snapshot_is_sorted_and_filtered(self):
        snapshot = mosaic_env_snapshot({"MOSAIC_Z": "1", "OTHER": "2", "MOSAIC_A": "3"})
        self.assertEqual(list(snapshot.items()), [("MOSAIC_A", "3"), ("MOSAIC_Z", "1")])


class CheckEngineConfig(unittest.TestCase):
    ENGINE = {"input_size": 888, "num_actions": 414, "active_leaf": "Net",
              "use_gumbel_search": True, "gumbel_c_scale": 0.1 + 0.2}

    def test_match_is_empty(self):
        expected = {"input_size": 888, "num_actions": 414.0, "active_leaf": "Net",
                    "use_gumbel_search": True}
        self.assertEqual(check_engine_config(self.ENGINE, expected), [])

    def test_numbers_are_compared_as_floats(self):
        self.assertEqual(check_engine_config(self.ENGINE, {"gumbel_c_scale": 0.3}), [])
        self.assertEqual(check_engine_config(self.ENGINE, {"input_size": "888"}), [])

    def test_deviation_is_found(self):
        deviations = check_engine_config(self.ENGINE, {"input_size": 755, "num_actions": 414})
        self.assertEqual(len(deviations), 1)
        self.assertIn("input_size", deviations[0])

    def test_missing_key_is_a_deviation(self):
        deviations = check_engine_config(self.ENGINE, {"contract_hash": "abc"})
        self.assertEqual(len(deviations), 1)
        self.assertIn("contract_hash", deviations[0])

    def test_bool_is_not_a_number(self):
        self.assertEqual(len(check_engine_config({"flag": 1}, {"flag": True})), 1)

    def test_error_dict_is_not_green(self):
        """Das `_error`-dict aus selfplay_manifest._engine_config darf nicht
        als gruen durchgehen."""
        deviations = check_engine_config({"_error": "altes Wheel"}, {"input_size": 888})
        self.assertEqual(len(deviations), 1)
        self.assertIn("_error", deviations[0])


if __name__ == "__main__":
    unittest.main()
