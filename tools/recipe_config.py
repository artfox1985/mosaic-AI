# -*- coding: utf-8 -*-
"""Rezeptdateien fuer Werkzeuge mit vielen Flags -- EIN gemeinsamer Helfer.

Spezifikation: `docs/working_rules.md`, Abschnitt Arbeitskonventionen, Punkt
"Rezeptdatei statt langer Flag-Listen" (Nutzer 2026-09-26). Kurzform:

* Ein Rezept ist JSON. Seine Schluessel sind die argparse-`dest`-Namen des
  Werkzeugs; der Abschnitt `env` setzt `MOSAIC_*`-Variablen VOR dem ersten
  Import der Engine. **Unbekannte Schluessel brechen ab** -- ein Tippfehler
  darf nicht still zum Default werden.
* Explizite Kommandozeilen-Flags ueberschreiben das Rezept nur MIT Protokoll
  (`overrides`, im Manifest), damit ein Abweichen sichtbar bleibt.
* Das Lauf-Manifest traegt Pfad, sha256 und Inhalt des Rezepts sowie alle
  `MOSAIC_*` der Umgebung (`manifest_block`).
* Wo die Engine meldet, was sie gelesen hat (`engine_config_json`), vergleicht
  `check_engine_config` das VOR dem Start mit dem Soll des Rezepts.
* Abgrenzung: die Spec (`models/*.spec.json`) bleibt die Suchkonfiguration JE
  SEITE; das Rezept beschreibt den LAUF und verweist auf die Spec.

Form::

    {"recipe_version": 1, "tool": "self_play", "description": "...",
     "common": {<dest>: <wert>, ...},
     "env": {"MOSAIC_X": "1", ...},
     "classes": {"<name>": {<dest>: <wert>, ..., "env": {...},
                            "description": "..."}},
     "expect_engine_config": {"input_size": 888, ...}}

`classes` ist optional (Erzeugung: Klassen; Training: Arme; Arena: Laeufe);
ohne `classes` gilt nur `common`. `description` und `expect_engine_config`
sind optional.

Ablauf im Werkzeug (Stand 2026-09-27: eingehaengt in `self_play.py`,
`train.py` und `tools/paired_gating.py`, Tests tools/tests/test_*_recipe.py;
erster Entwurf `models/v34.recipe.json`; noch nicht mit echtem Lauf gefahren):

1. GANZ OBEN, vor jedem Import, der `MOSAIC_*` liest (Engine, `config.py`,
   `neural_net.py`): `apply_recipe_env_from_argv(...)`.
2. Parser bauen, dann `apply_to_parser(parser, argv, recipe, class_name)`.
3. Vor dem Start: `check_engine_config(engine_config, recipe.get(
   "expect_engine_config", {}))`, bei Abweichung abbrechen.
4. Ins Manifest: `manifest_block(recipe, recipe.path, class_name, overrides)`.

Nur Standardbibliothek: der Helfer muss laden, BEVOR irgendetwas mit torch
oder der Engine importiert wird -- darum auch kein Import von
`corpus_dataset.mosaic_env_fingerprint` (das Muster ist unten nachgebaut).

Bezeichner englisch (CLAUDE.md 2026-08-24), Inhaltssprache deutsch.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import math
import os
from pathlib import Path

RECIPE_VERSION = 1
ENV_PREFIX = "MOSAIC_"

# Erlaubte Abschnitte auf oberster Ebene. Alles andere bricht ab (dieselbe
# Regel wie fuer Argument-Schluessel: ein Tippfehler wie "comon" darf nicht
# still einen ganzen Abschnitt verschwinden lassen).
TOP_LEVEL_KEYS = frozenset({
    "recipe_version", "tool", "description", "common", "env", "classes",
    "expect_engine_config",
})

# Schluessel innerhalb einer Klasse, die KEINE argparse-dests sind. Folge: ein
# Werkzeug mit einem dest `env` oder `description` koennte diese nicht je
# Klasse setzen -- keines der drei Zielwerkzeuge hat einen (geprueft
# 2026-09-26 an self_play.py, train.py, tools/paired_gating.py).
CLASS_META_KEYS = frozenset({"env", "description", "expect_engine_config"})

# dests, die `add_recipe_arguments` selbst anlegt. Ein Rezept, das sein
# eigenes Rezept oder seine Klasse setzen will, ist ein Zirkel.
RESERVED_DESTS = frozenset({"recipe", "recipe_class"})

# Marke fuer den Sonden-Parse in `apply_to_parser`: ein Objekt, das kein
# Kommandozeilenwert je sein kann (Identitaetsvergleich, nicht Gleichheit).
_NOT_GIVEN = object()


class RecipeError(ValueError):
    """Rezept ungueltig oder passt nicht zum Werkzeug. Das Werkzeug soll den
    Lauf damit ABBRECHEN (z.B. `parser.error(str(e))` oder `SystemExit`),
    nie weiterlaufen."""


class Recipe(dict):
    """Inhalt einer Rezeptdatei (ein normales dict, JSON-serialisierbar)
    plus die zwei Herkunftsangaben `path` und `sha256`.

    Die Herkunft haengt als ATTRIBUT am Objekt und nicht als Schluessel im
    dict: der Inhalt, der ins Manifest geht, soll genau der Dateiinhalt sein.
    """

    def __init__(self, content: dict, path: str, sha256: str):
        super().__init__(content)
        self.path = path
        self.sha256 = sha256


# ---------------------------------------------------------------------------
# Laden und Struktur
# ---------------------------------------------------------------------------

def _format_problems(title: str, problems: list[str]) -> str:
    return title + ":\n  - " + "\n  - ".join(problems)


def _suggestion(key: str, candidates) -> str:
    """Naechstliegende gueltige Namen per difflib, als Zusatz fuer eine
    Fehlermeldung. Die Flag-Schreibweise (`c-puct` statt `c_puct`) wird
    ausdruecklich erkannt, weil sie der haeufigste Fehler sein duerfte:
    Rezeptschluessel sind dests, nicht Flag-Namen."""
    names = sorted(candidates)
    close = difflib.get_close_matches(key, names, n=3, cutoff=0.6)
    normalized = key.lstrip("-").replace("-", "_")
    if normalized != key and normalized in candidates and normalized not in close:
        close.insert(0, normalized)
    if not close:
        return " (kein aehnlicher gueltiger Name)"
    return " -- naechstliegend: " + ", ".join(close)


def _reject_duplicate_keys(pairs):
    """`object_pairs_hook` fuer json.loads: doppelte Schluessel sind ein
    Fehler. Ohne das gewinnt still der letzte -- ein Rezept mit zweimal
    `games` saehe aus wie eines, meinte aber nur eine der beiden Zeilen."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise RecipeError(f"Schluessel {key!r} steht doppelt im selben Objekt")
        result[key] = value
    return result


def _reject_nonfinite(token):
    """`parse_constant` fuer json.loads: `NaN`, `Infinity` und `-Infinity` sind kein JSON."""
    raise RecipeError(f"{token} ist kein gueltiger Wert (kein JSON, als Knopfwert ein Tippfehler)")


def _env_section_problems(env, where: str) -> list[str]:
    if not isinstance(env, dict):
        return [f"{where} muss ein Objekt sein, ist {type(env).__name__}"]
    problems = []
    for name, value in env.items():
        if not name.startswith(ENV_PREFIX):
            problems.append(f"{where}: {name!r} hat nicht das Praefix {ENV_PREFIX}")
        if type(value) is bool or not isinstance(value, (str, int, float)):
            problems.append(
                f"{where}: {name}={value!r} -- erlaubt sind Text oder Zahl "
                "(Wahrheitswerte waeren als 'True' im Env mehrdeutig; lieber \"1\")")
    return problems


def _args_section_problems(args: dict, where: str) -> list[str]:
    problems = []
    for key, value in args.items():
        if key in RESERVED_DESTS:
            problems.append(f"{where}: {key!r} ist dem Rezept-Mechanismus vorbehalten")
        elif key.startswith(ENV_PREFIX):
            problems.append(f"{where}: {key!r} ist eine Umgebungsvariable und gehoert in 'env'")
        if isinstance(value, dict):
            problems.append(f"{where}: {key!r} ist ein Objekt; Argumentwerte sind Text, Zahl, "
                            "Wahrheitswert, null oder Liste")
    return problems


def _structure_problems(content) -> list[str]:
    if not isinstance(content, dict):
        return ["das Rezept muss ein JSON-Objekt sein"]
    problems = []
    for key in sorted(set(content) - TOP_LEVEL_KEYS):
        problems.append(f"unbekannter Abschnitt {key!r}" + _suggestion(key, TOP_LEVEL_KEYS))
    if "recipe_version" not in content:
        problems.append("recipe_version fehlt")
    elif type(content["recipe_version"]) is not int or content["recipe_version"] != RECIPE_VERSION:
        problems.append(f"recipe_version {content['recipe_version']!r} wird nicht unterstuetzt "
                        f"(erwartet {RECIPE_VERSION})")
    if not isinstance(content.get("tool"), str) or not content.get("tool"):
        problems.append("tool fehlt oder ist kein Text")
    if "description" in content and not isinstance(content["description"], str):
        problems.append("description muss Text sein")
    common = content.get("common", {})
    if not isinstance(common, dict):
        problems.append("common muss ein Objekt sein")
    else:
        problems += _args_section_problems(common, "common")
    problems += _env_section_problems(content.get("env", {}), "env")
    if "classes" in content:
        classes = content["classes"]
        if not isinstance(classes, dict) or not classes:
            problems.append("classes muss ein nicht-leeres Objekt sein (oder ganz fehlen)")
        else:
            for name, body in classes.items():
                where = f"classes.{name}"
                if not name:
                    problems.append("classes: leerer Klassenname")
                if not isinstance(body, dict):
                    problems.append(f"{where} muss ein Objekt sein")
                    continue
                problems += _env_section_problems(body.get("env", {}), where + ".env")
                if "description" in body and not isinstance(body["description"], str):
                    problems.append(f"{where}.description muss Text sein")
                if ("expect_engine_config" in body
                        and not isinstance(body["expect_engine_config"], dict)):
                    problems.append(f"{where}.expect_engine_config muss ein Objekt sein")
                problems += _args_section_problems(
                    {k: v for k, v in body.items() if k not in CLASS_META_KEYS}, where)
    if "expect_engine_config" in content and not isinstance(content["expect_engine_config"], dict):
        problems.append("expect_engine_config muss ein Objekt sein")
    return problems


def load_recipe(path) -> Recipe:
    """Rezeptdatei laden, `recipe_version` und Struktur pruefen, sha256 der
    Datei berechnen.

    Der sha256 laeuft ueber die ROHEN Bytes der Datei (wie `_spec_block` in
    `selfplay_manifest.py`), nicht ueber den geparsten Inhalt: er soll die
    Datei wiederfinden, nicht nur einen gleichbedeutenden Inhalt.

    Geprueft wird hier nur, was ohne das Werkzeug pruefbar ist (Abschnitte,
    Version, `MOSAIC_`-Praefix in `env`, doppelte Schluessel). Ob die
    Argument-Schluessel zum Werkzeug passen, prueft `apply_to_parser` gegen
    dessen Parser. Ein BOM am Dateianfang wird toleriert (Windows-Editoren).
    """
    path_text = str(path)
    try:
        raw = Path(path).read_bytes()
    except OSError as e:
        raise RecipeError(f"Rezept {path_text} nicht lesbar: {e}") from e
    try:
        # Code-Review 2 (2026-10-02) Befund 7: Pythons json nimmt `NaN`/`Infinity` an, beides ist
        # kein JSON und als Knopfwert immer ein Tippfehler -- hart abweisen.
        content = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_reject_duplicate_keys,
                             parse_constant=_reject_nonfinite)
    except RecipeError as e:
        raise RecipeError(f"Rezept {path_text}: {e}") from e
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise RecipeError(f"Rezept {path_text} ist kein gueltiges UTF-8-JSON: {e}") from e
    problems = _structure_problems(content)
    if problems:
        raise RecipeError(_format_problems(f"Rezept {path_text} ist ungueltig", problems))
    return Recipe(content, path_text, hashlib.sha256(raw).hexdigest())


def resolve(recipe: dict, class_name: str | None) -> tuple[dict, dict]:
    """`common` mit der gewaehlten Klasse zusammenfuehren -> (args, env).

    Die Klasse gewinnt, fuer Argumente wie fuer `env`. Die Meta-Schluessel
    der Klasse (`env`, `description`) sind keine Argumente und fehlen in
    `args`.

    Fehler statt Raten:
    * Rezept MIT `classes`, aber keine oder eine fehlende Klasse gewaehlt ->
      Abbruch mit der Liste der vorhandenen.
    * Rezept OHNE `classes`, aber eine Klasse gewaehlt -> Abbruch. Still nur
      `common` zu fahren hiesse, dass `--class sockel` auf einem Rezept ohne
      Klassen wirkungslos waere, ohne dass es jemand merkt.
    """
    common = dict(recipe.get("common", {}))
    env = dict(recipe.get("env", {}))
    classes = recipe.get("classes")
    if classes is None:
        if class_name is not None:
            raise RecipeError(f"Klasse {class_name!r} gewaehlt, aber das Rezept hat keine classes")
        return common, env
    available = ", ".join(sorted(classes))
    if class_name is None:
        raise RecipeError(f"das Rezept hat classes, aber keine wurde gewaehlt (--class); "
                          f"vorhanden: {available}")
    if class_name not in classes:
        raise RecipeError(f"Klasse {class_name!r} fehlt im Rezept; vorhanden: {available}")
    body = classes[class_name]
    common.update({k: v for k, v in body.items() if k not in CLASS_META_KEYS})
    env.update(body.get("env", {}))
    return common, env


def expected_engine_config(recipe: dict, class_name: str | None) -> dict:
    """Soll fuer den Waechter: `expect_engine_config` des Rezepts, ergaenzt
    bzw. ueberschrieben durch `classes.<name>.expect_engine_config`.

    Warum je Klasse (Smoke-Lauf v34, 2026-10-01): ein Knopf, den nur EINE
    Klasse setzt (`excursion_kl_weight` in `value-excursion`), stand
    rezeptweit in der Erwartung -- der Waechter brach `policy` vor dem
    ersten Spiel ab. Klassenwahl und Fehler wie `resolve`; ohne `classes`
    gilt nur die rezeptweite Erwartung.
    """
    expected = dict(recipe.get("expect_engine_config") or {})
    classes = recipe.get("classes")
    if classes is None or class_name is None or class_name not in classes:
        return expected
    expected.update(classes[class_name].get("expect_engine_config") or {})
    return expected


# ---------------------------------------------------------------------------
# argparse
# ---------------------------------------------------------------------------

def add_recipe_arguments(parser: argparse.ArgumentParser) -> None:
    """`--recipe` (dest `recipe`) und `--class` (dest `recipe_class`) an den
    Parser haengen. Idempotent: schon vorhandene dests bleiben unberuehrt.
    `class` ist ein Python-Schluesselwort, darum der dest `recipe_class`."""
    existing = {action.dest for action in parser._actions}
    if "recipe" not in existing:
        parser.add_argument("--recipe", dest="recipe", default=None,
                            help="Rezeptdatei (JSON, docs/working_rules.md 'Rezeptdatei statt "
                                 "langer Flag-Listen'); ihre Werte werden zu Defaults, explizite "
                                 "Flags ueberschreiben sie mit Protokoll im Manifest.")
    if "recipe_class" not in existing:
        parser.add_argument("--class", dest="recipe_class", default=None,
                            help="Klasse (Arm, Lauf) im Rezept; Pflicht, wenn das Rezept "
                                 "classes hat.")


def _type_error(key: str, flag: str, wanted: str, value) -> RecipeError:
    return RecipeError(f"{key!r} ({flag}): erwartet {wanted}, Rezept hat {value!r} "
                       f"({type(value).__name__})")


def _check_scalar(key: str, flag: str, action: argparse.Action, value, allow_none: bool):
    """Einen Einzelwert gegen `type`/`choices` einer store-Aktion pruefen und
    in den Typ bringen, den argparse von der Kommandozeile liefern wuerde.

    Streng mit Absicht: `"4000"` fuer ein int-Argument ist ein Fehler, obwohl
    argparse Text-Defaults selbst konvertieren wuerde -- ein Rezept, das Zahlen
    als Text schreibt, verbirgt, ob der Autor Zahl oder Text meinte. Einzige
    Lockerung: eine ganze Zahl fuer ein float-Argument (`2` fuer `c_puct`),
    weil JSON `2` und `2.0` nicht verlaesslich auseinanderhaelt.
    """
    if value is None:
        if allow_none:
            return None
        raise RecipeError(f"{key!r} ({flag}): null ist nur erlaubt, wo der Parser-Default "
                          f"None ist (hier {action.default!r})")
    kind = action.type
    if kind is None or kind is str:
        if not isinstance(value, str):
            raise _type_error(key, flag, "Text", value)
        converted = value
    elif kind is int:
        if type(value) is not int:
            raise _type_error(key, flag, "ganze Zahl", value)
        converted = value
    elif kind is float:
        if type(value) not in (int, float):
            raise _type_error(key, flag, "Zahl", value)
        converted = float(value)
    else:
        # Eigene Typfunktion: der Rezeptwert muss als TEXT stehen, genau wie auf
        # der Kommandozeile, und laeuft durch dieselbe Funktion.
        if not isinstance(value, str):
            raise _type_error(key, flag, f"Text fuer die Typfunktion {getattr(kind, '__name__', kind)}",
                              value)
        try:
            converted = kind(value)
        except (TypeError, ValueError, argparse.ArgumentTypeError) as e:
            raise RecipeError(f"{key!r} ({flag}): {value!r} von der Typfunktion abgelehnt: {e}") from e
    if action.choices is not None and converted not in action.choices:
        raise RecipeError(f"{key!r} ({flag}): {value!r} ist keine der erlaubten Wahlen "
                          f"{list(action.choices)}")
    return converted


def _check_for_action(key: str, action: argparse.Action, value):
    flag = "/".join(action.option_strings) or key
    if not action.option_strings:
        raise RecipeError(f"{key!r}: Positionsargumente sind nicht rezeptfaehig")
    boolean_optional = getattr(argparse, "BooleanOptionalAction", None)
    if boolean_optional is not None and isinstance(action, boolean_optional):
        if type(value) is not bool:
            raise _type_error(key, flag, "true/false", value)
        return value
    if isinstance(action, argparse._StoreConstAction):  # store_true/store_false/store_const
        if isinstance(action.const, bool):
            if type(value) is not bool:
                raise _type_error(key, flag, "true/false (Schalter)", value)
            return value
        raise RecipeError(f"{key!r} ({flag}): store_const mit Nicht-Bool-Konstante ist nicht "
                          "rezeptfaehig")
    if type(action) is not argparse._StoreAction:
        # append/count/extend: Sonden-Parse mit Marke und Rezept-Default
        # vertragen sich dort nicht (argparse haengt an den Default an bzw.
        # zaehlt ihn hoch). Keines der drei Zielwerkzeuge nutzt diese Arten.
        raise RecipeError(f"{key!r} ({flag}): Aktionsart {type(action).__name__} ist nicht "
                          "rezeptfaehig (nur store, store_true/false, BooleanOptionalAction)")
    nargs = action.nargs
    if nargs is None or nargs == argparse.OPTIONAL:
        return _check_scalar(key, flag, action, value, allow_none=action.default is None)
    if value is None and action.default is None:
        return None
    if not isinstance(value, list):
        raise _type_error(key, flag, f"Liste (nargs={nargs!r})", value)
    if nargs == argparse.ONE_OR_MORE and not value:
        raise RecipeError(f"{key!r} ({flag}): nargs='+' verlangt mindestens einen Eintrag")
    if isinstance(nargs, int) and len(value) != nargs:
        raise RecipeError(f"{key!r} ({flag}): genau {nargs} Eintraege verlangt, Rezept hat {len(value)}")
    return [_check_scalar(key, flag, action, item, allow_none=False) for item in value]


def _check_value(key: str, actions: list, value):
    """Mehrere Aktionen koennen denselben dest haben (paired_gating:
    `--promote-winner`/`--no-promote-winner`). Der Wert ist gueltig, wenn
    EINE von ihnen ihn annimmt."""
    first_error = None
    for action in actions:
        try:
            return _check_for_action(key, action, value)
        except RecipeError as e:
            if first_error is None:
                first_error = e
    raise first_error


def _typed_values(parser: argparse.ArgumentParser, args: dict) -> dict:
    """Rezept-Argumente gegen die dests des Parsers pruefen und typisieren.
    Sammelt ALLE Probleme, bevor es abbricht -- ein Rezept mit drei
    Tippfehlern soll nicht drei Anlaeufe brauchen."""
    skipped = (argparse._HelpAction, argparse._VersionAction, argparse._SubParsersAction)
    by_dest: dict[str, list] = {}
    for action in parser._actions:
        if action.dest in (None, argparse.SUPPRESS) or action.dest in RESERVED_DESTS:
            continue
        if isinstance(action, skipped):
            continue
        by_dest.setdefault(action.dest, []).append(action)
    problems, values = [], {}
    for key in sorted(args):
        if key in RESERVED_DESTS:
            problems.append(f"{key!r} ist dem Rezept-Mechanismus vorbehalten")
            continue
        if key not in by_dest:
            problems.append(f"unbekannter Schluessel {key!r}" + _suggestion(key, by_dest))
            continue
        try:
            values[key] = _check_value(key, by_dest[key], args[key])
        except RecipeError as e:
            problems.append(str(e))
    if problems:
        raise RecipeError(_format_problems(f"Rezept passt nicht zum Parser {parser.prog!r}", problems))
    return values


def _same_path(a, b) -> bool:
    return os.path.normcase(os.path.abspath(str(a))) == os.path.normcase(os.path.abspath(str(b)))


def _check_argv_matches(namespace, recipe_path, class_name) -> None:
    """Das Rezept, das das Werkzeug angewandt hat, muss das sein, das auf der
    Kommandozeile steht. Faengt den Fall, dass der Vorab-Parse
    (`apply_recipe_env_from_argv`) etwas anderes gesehen hat als der
    Hauptparser -- z.B. eine Abkuerzung `--rec`, die nur der Hauptparser
    aufloest. Dann waere das `env` des Rezepts NICHT gesetzt worden."""
    given = getattr(namespace, "recipe", None)
    given_class = getattr(namespace, "recipe_class", None)
    if recipe_path is None:
        if given is not None or given_class is not None:
            raise RecipeError("--recipe/--class steht auf der Kommandozeile, wurde vom Werkzeug "
                              "aber nicht angewandt (Vorab-Parse fehlt oder sah es nicht)")
        return
    if given is not None and not _same_path(given, recipe_path):
        raise RecipeError(f"--recipe {given!r} auf der Kommandozeile, angewandt wurde aber "
                          f"{str(recipe_path)!r}")
    if given_class is not None and given_class != class_name:
        raise RecipeError(f"--class {given_class!r} auf der Kommandozeile, angewandt wurde aber "
                          f"{class_name!r}")


def _explicit_overrides(parser, argv, values: dict, namespace) -> dict:
    """Welche Rezeptwerte hat die Kommandozeile EXPLIZIT gesetzt?

    Verfahren: ein zweiter Parse derselben argv, in dem jeder Rezept-dest
    eine Marke (`_NOT_GIVEN`) als Default traegt. Was danach nicht mehr die
    Marke ist, hat argparse aus der Kommandozeile gesetzt. Danach werden die
    Defaults exakt wiederhergestellt (die Rezeptwerte).

    Warum so und nicht anders:
    * Wertvergleich (Ergebnis != Rezeptwert) uebersieht ein Flag, das den
      Rezeptwert WIEDERHOLT, und kann "nicht angegeben" nicht von "den
      Default angegeben" trennen. Der Identitaetsvergleich mit der Marke haengt
      nicht am Wert.
    * argv selbst nach Flag-Namen zu durchsuchen muesste nachbauen, was
      argparse ohnehin kann: Abkuerzungen, `--flag=wert`, mehrere Flags auf
      einem dest (`--promote-winner`/`--no-promote-winner`). Die Marke laesst
      argparse selbst entscheiden.
    Ein zweiter Parse kostet nichts Messbares.

    Protokolliert wird jedes explizit gesetzte Rezeptfeld, auch bei gleichem
    Wert: der Befund lautet "die Kommandozeile hat mitgeredet", und ob sie
    etwas geaendert hat, steht in den beiden Werten.
    """
    if not values:
        return {}
    saved_parser_defaults = dict(parser._defaults)
    saved_action_defaults = [(action, action.default) for action in parser._actions]
    try:
        parser.set_defaults(**{dest: _NOT_GIVEN for dest in values})
        probe = parser.parse_args(argv)
    finally:
        parser._defaults.clear()
        parser._defaults.update(saved_parser_defaults)
        for action, default in saved_action_defaults:
            action.default = default
    return {
        dest: {"recipe": values[dest], "cli": getattr(namespace, dest)}
        for dest in sorted(values)
        if getattr(probe, dest, _NOT_GIVEN) is not _NOT_GIVEN
    }


def apply_to_parser(parser: argparse.ArgumentParser, argv, recipe_path, class_name,
                    tool: str | None = None) -> tuple[argparse.Namespace, dict]:
    """Rezept auf einen argparse-Parser anwenden -> (namespace, overrides).

    `recipe_path` ist ein Pfad, ein bereits geladenes `Recipe` (so kommt es
    aus `apply_recipe_env_from_argv`) oder None (dann ist das ein normaler
    `parse_args`, und `overrides` ist leer). `argv` wie bei `parse_args`
    (None = `sys.argv[1:]`). `tool`, wenn gesetzt, muss dem Feld `tool` des
    Rezepts gleichen -- ein Trainingsrezept am Self-Play bricht dann mit
    einer klaren Meldung ab statt mit einer Liste unbekannter Schluessel.

    Schritte:
    1. `--recipe`/`--class` an den Parser haengen (idempotent).
    2. `common` + Klasse aufloesen (`resolve`), jeden Schluessel gegen die
       dests des Parsers pruefen: **unbekannt -> Abbruch** mit den
       naechstliegenden gueltigen Namen; **falscher Typ -> Abbruch** (Wert
       muss zu `type`/`choices` bzw. zur Schalter-Art store_true/false
       passen, siehe `_check_scalar`).
    3. Fuer Rezept-dests `required` aufheben: das Rezept liefert den Wert
       (self_play `--mode`/`--version`, train `--name`, paired_gating
       `--model-a/-b`). argparse prueft `required` am Vorkommen auf der
       Kommandozeile, nicht am Default -- ohne diesen Schritt muesste man
       Pflicht-Flags trotz Rezept doppelt angeben.
    4. Rezeptwerte als Defaults setzen (`parser.set_defaults`), dann
       `parse_args(argv)`. Dieser Parse kommt ZUERST, damit Fehler und
       `--help` gegen die echte Konfiguration laufen (die Hilfe zeigt die
       Rezept-Defaults).
    5. Explizit gesetzte Rezeptfelder ermitteln (`_explicit_overrides`,
       Sonden-Parse mit Marke) -> `overrides` =
       `{dest: {"recipe": ..., "cli": ...}}`.

    Der Parser bleibt danach mit den Rezept-Defaults zurueck (so, als haette
    das Werkzeug `set_defaults` selbst gerufen).
    """
    add_recipe_arguments(parser)
    if recipe_path is None:
        if class_name is not None:
            raise RecipeError(f"Klasse {class_name!r} ohne Rezept")
        namespace = parser.parse_args(argv)
        _check_argv_matches(namespace, None, None)
        return namespace, {}
    recipe = recipe_path if isinstance(recipe_path, Recipe) else load_recipe(recipe_path)
    if tool is not None and recipe.get("tool") != tool:
        raise RecipeError(f"Rezept {recipe.path} ist fuer tool {recipe.get('tool')!r}, "
                          f"nicht fuer {tool!r}")
    args, _env = resolve(recipe, class_name)
    # Auch `common` und JEDE Klasse pruefen, nicht nur die aufgeloeste: ein
    # falscher Wert in `common`, den die gewaehlte Klasse zufaellig
    # ueberschreibt, bleibt sonst unentdeckt und schlaegt erst bei der
    # naechsten Klasse zu (Test test_wrong_type_aborts, 2026-09-27).
    # Ueber `resolve` je Klasse, damit Metadaten (z.B. `description`) genauso
    # ausgefiltert werden wie beim echten Aufloesen.
    for other in (recipe.get("classes") or {}):
        if other != class_name:
            _typed_values(parser, resolve(recipe, other)[0])
    values = _typed_values(parser, args)
    for action in parser._actions:
        if action.dest in values:
            action.required = False
    parser.set_defaults(**values)
    namespace = parser.parse_args(argv)
    _check_argv_matches(namespace, recipe.path, class_name)
    overrides = _explicit_overrides(parser, argv, values, namespace)
    return namespace, overrides


# ---------------------------------------------------------------------------
# Umgebung
# ---------------------------------------------------------------------------

def apply_env(env_dict: dict, allow_existing: bool = False, reserved: dict | None = None,
              environ=None) -> dict:
    """`MOSAIC_*`-Variablen des Rezepts in die Umgebung setzen.

    **Zeitpunkt: VOR dem ersten Import der Engine (`mosaic_rust`) bzw. vor dem
    ersten Lesen eines OnceLock-Getters.** Rust liest die Knoepfe einmal und
    behaelt den Wert fuer den ganzen Prozess; ein spaeter gesetzter Wert steht
    zwar in der Umgebung (und im Manifest!), wirkt aber nicht. Dasselbe gilt
    fuer Python-Module, die `MOSAIC_*` beim IMPORT lesen, z.B. `config.py:28`
    (`MOSAIC_DATA_DIR`) und `engine/py/neural_net.py:9`/`:115`
    (`MOSAIC_IGNORE_POLICY_TARGET_VALID`, `MOSAIC_FEATURES_FROM_RUST`).
    Kindprozesse (multiprocessing) erben die Umgebung zum Startzeitpunkt.

    Regeln:
    * Nur Namen mit Praefix `MOSAIC_`.
    * Werte werden Text: Text bleibt, Zahlen per `str()` (`1` -> "1",
      `0.81` -> "0.81"; ACHTUNG `1.0` -> "1.0", was ein ganzzahliger
      Rust-Knopf ablehnen kann -- im Rezept darum lieber Text schreiben).
      Wahrheitswerte, null, Listen: Abbruch.
    * `reserved`: {Name: Hinweis} fuer Variablen, die das Werkzeug SELBST aus
      einem Flag setzt (self_play-Worker: `MOSAIC_RETURN_ORDER_RANDOM_P` u.a.).
      Stuende so ein Name im `env`, wuerde das Werkzeug ihn still
      ueberschreiben; darum Abbruch mit dem Hinweis, welcher Rezeptschluessel
      stattdessen gilt.
    * **Doppelquelle:** ist eine Variable schon mit ANDEREM Wert gesetzt (Kette,
      Shell), bricht der Aufruf ab -- zwei Quellen fuer denselben Knopf sind
      genau die Lage, in der hinterher niemand weiss, welche galt. Gleicher
      Wert ist kein Konflikt. Mit `allow_existing=True` gewinnt das Rezept,
      und die Ersetzung steht im Bericht.
    * Alles-oder-nichts: erst werden ALLE Eintraege geprueft, gesetzt wird nur,
      wenn keiner beanstandet wurde.

    `environ` (Default `os.environ`) ist fuer Tests austauschbar. Rueckgabe:
    Bericht `{"set": [...], "unchanged": [...], "replaced": [...]}`.
    """
    if environ is None:
        environ = os.environ
    reserved = reserved or {}
    problems, planned = [], {}
    for name in sorted(env_dict):
        value = env_dict[name]
        if not isinstance(name, str) or not name.startswith(ENV_PREFIX):
            problems.append(f"{name!r}: nur Variablen mit Praefix {ENV_PREFIX} sind erlaubt")
            continue
        if name in reserved:
            problems.append(f"{name}: setzt das Werkzeug selbst -- {reserved[name]}")
            continue
        if type(value) is bool or not isinstance(value, (str, int, float)):
            problems.append(f"{name}={value!r}: erlaubt sind Text oder Zahl")
            continue
        planned[name] = value if isinstance(value, str) else str(value)
    if not allow_existing:
        for name, text in planned.items():
            if name in environ and environ[name] != text:
                problems.append(f"{name} ist schon auf {environ[name]!r} gesetzt, das Rezept will "
                                f"{text!r} (Doppelquelle: Variable aus Kette/Shell entfernen)")
    if problems:
        raise RecipeError(_format_problems("env des Rezepts abgelehnt, NICHTS gesetzt", problems))
    report = {"set": [], "unchanged": [], "replaced": []}
    for name, text in planned.items():
        old = environ.get(name)
        if old == text:
            report["unchanged"].append(name)
        elif old is None:
            report["set"].append(f"{name}={text}")
        else:
            report["replaced"].append(f"{name}: {old} -> {text}")
        environ[name] = text
    return report


def apply_recipe_env_from_argv(argv=None, tool: str | None = None, reserved: dict | None = None,
                               allow_existing: bool = False, environ=None) -> dict | None:
    """Vorab-Parse fuer den Kopf eines Werkzeugs: `--recipe`/`--class` aus
    argv lesen, Rezept laden, `env` der Klasse setzen (`apply_env`).

    Gedacht fuer die ERSTE Zeile nach den Standardbibliotheks-Importen, also
    vor `import mosaic_rust`, `from config import ...` und `neural_net`
    (siehe `apply_env` zum Zeitpunkt). Der Hauptparser des Werkzeugs steht
    dort meist noch gar nicht -- darum ein eigener Mini-Parser mit
    `parse_known_args`, der alles andere liegen laesst. `allow_abbrev=False`,
    damit er kein fremdes Flag fuer `--class` haelt; eine Abkuerzung, die nur
    der Hauptparser aufloest, faengt `apply_to_parser` spaeter ab.

    In einem Modul, das multiprocessing mit spawn nutzt, gehoert der Aufruf
    hinter `if __name__ == "__main__":` -- die Kinder importieren das Modul
    neu und erben die Umgebung ohnehin.

    Rueckgabe: None ohne `--recipe`; sonst `{"recipe": Recipe, "class": ...,
    "env_report": ...}`. `recipe` und `class` gehen danach an
    `apply_to_parser` und `manifest_block`.
    """
    pre = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    add_recipe_arguments(pre)
    known, _rest = pre.parse_known_args(argv)
    if known.recipe is None:
        if known.recipe_class is not None:
            raise RecipeError(f"--class {known.recipe_class!r} ohne --recipe")
        return None
    recipe = load_recipe(known.recipe)
    if tool is not None and recipe.get("tool") != tool:
        raise RecipeError(f"Rezept {recipe.path} ist fuer tool {recipe.get('tool')!r}, "
                          f"nicht fuer {tool!r}")
    _args, env = resolve(recipe, known.recipe_class)
    report = apply_env(env, allow_existing=allow_existing, reserved=reserved, environ=environ)
    return {"recipe": recipe, "class": known.recipe_class, "env_report": report}


# ---------------------------------------------------------------------------
# Manifest und Waechter
# ---------------------------------------------------------------------------

def mosaic_env_snapshot(environ=None) -> dict:
    """Alle `MOSAIC_*`-Variablen der Umgebung, nach Namen sortiert.

    Muster: `mosaic_env_fingerprint` in `engine/py/corpus_dataset.py` -- KEINE
    kuratierte Liste, sondern alles, was gesetzt ist, mit Wert. Nachgebaut
    statt importiert, weil `corpus_dataset` torch zieht. Als dict statt als
    Zeichenkette, weil es ins Manifest geht und dort diffbar sein soll.
    """
    if environ is None:
        environ = os.environ
    return {name: environ[name] for name in sorted(environ) if name.startswith(ENV_PREFIX)}


def manifest_block(recipe, recipe_path, class_name, overrides, environ=None) -> dict | None:
    """Rezept-Block fuer ein Lauf-Manifest oder Arena-Artefakt.

    `{"path", "sha256", "class", "content", "overrides", "mosaic_env"}`:
    Pfad wie angegeben, sha256 der Datei (vom Laden; bei einem rohen dict
    frisch aus der Datei), der VOLLSTAENDIGE Inhalt (alle Klassen, damit die
    Geschwister eines Laufs ohne die Datei vergleichbar bleiben), die
    Kommandozeilen-Abweichungen aus `apply_to_parser` und der Stand ALLER
    `MOSAIC_*` zum Zeitpunkt des Aufrufs (also auch die, die nicht aus dem
    Rezept kamen).

    None ohne Rezept (wie `_spec_block`). Best-effort wie alle Manifest-Teile
    im Baum: ein unlesbarer Pfad fuer den Nachhash landet als `_error` im
    Block, statt den Lauf zu stoppen.
    """
    if recipe is None:
        return None
    if recipe_path is None:
        recipe_path = getattr(recipe, "path", None)
    block = {"path": None if recipe_path is None else str(recipe_path)}
    sha256 = getattr(recipe, "sha256", None)
    if sha256 is None:
        try:
            sha256 = hashlib.sha256(Path(recipe_path).read_bytes()).hexdigest()
        except (OSError, TypeError) as e:
            block["_error"] = f"sha256 nicht berechenbar: {e!r}"
    block["sha256"] = sha256
    block["class"] = class_name
    block["content"] = json.loads(json.dumps(dict(recipe)))
    block["overrides"] = json.loads(json.dumps(overrides or {}))
    block["mosaic_env"] = mosaic_env_snapshot(environ)
    return block


def _as_float(value):
    if type(value) is bool:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _values_match(expected, actual) -> bool:
    """Zahlen tolerant (als float, auch "888" gegen 888), Wahrheitswerte
    streng (True ist hier NICHT 1), Listen elementweise, sonst Gleichheit."""
    if type(expected) is bool or type(actual) is bool:
        return type(expected) is bool and type(actual) is bool and expected == actual
    if isinstance(expected, list) or isinstance(actual, list):
        return (isinstance(expected, list) and isinstance(actual, list)
                and len(expected) == len(actual)
                and all(_values_match(e, a) for e, a in zip(expected, actual)))
    expected_number, actual_number = _as_float(expected), _as_float(actual)
    if expected_number is not None and actual_number is not None:
        return math.isclose(expected_number, actual_number, rel_tol=1e-9, abs_tol=1e-12)
    # Pfade (2026-10-04, PREREG_asymmetric_selfplay.md par.7b): self_play.py loest
    # `--opponent-model` ueber pathlib auf und meldet ihn unter Windows mit
    # Rueckstrichen, das Rezept schreibt Vorwaertsstriche. Zwei Texte, von denen der
    # erwartete einen Pfadtrenner enthaelt, werden darum normalisiert verglichen
    # (`normpath` + `normcase`, wie die Manifest-Pruefung in
    # tools/night_v35_exploiter_chain.sh). Relativ gegen absolut bleibt ungleich.
    if (isinstance(expected, str) and isinstance(actual, str)
            and ("/" in expected or "\\" in expected)):
        return (os.path.normcase(os.path.normpath(expected))
                == os.path.normcase(os.path.normpath(actual)))
    return expected == actual


def check_engine_config(engine_config: dict, expected: dict) -> list[str]:
    """Soll (`expect_engine_config` des Rezepts) gegen das, was
    `mosaic_rust.engine_config_json()` meldet. Rueckgabe: Abweichungen als
    Text, leere Liste = gruen. Das Werkzeug bricht bei nicht-leerer Liste ab.

    Ein Schluessel, den `engine_config` nicht fuehrt, ist eine Abweichung und
    kein Freispruch -- sonst waere ein altes Wheel ohne das Feld (oder das
    `_error`-dict aus `selfplay_manifest._engine_config`) automatisch gruen.

    Grenze, die man kennen muss (STATUS 6 Punkt 7 laut
    `selfplay_manifest._spec_block`): fuer Spec-Felder meldet `engine_config`
    den ENV-Default, nicht den wirksamen Spec-Wert. Spec-Felder gehoeren
    darum NICHT in `expect_engine_config`.
    """
    if not isinstance(engine_config, dict):
        return [f"engine_config ist kein Objekt: {engine_config!r}"]
    deviations = []
    for key in sorted(expected):
        wanted = expected[key]
        if key not in engine_config:
            note = (f" (engine_config meldet _error: {engine_config['_error']})"
                    if "_error" in engine_config else "")
            deviations.append(f"{key}: fehlt in engine_config (erwartet {wanted!r}){note}")
            continue
        if not _values_match(wanted, engine_config[key]):
            deviations.append(f"{key}: erwartet {wanted!r}, Engine meldet {engine_config[key]!r}")
    return deviations
