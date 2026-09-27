# -*- coding: utf-8 -*-
"""Hilfsmodul der Rezept-Tests: den argparse-Parser eines Werkzeugs aus
dessen QUELLTEXT bauen, ohne das Werkzeug zu importieren.

Warum: `self_play.py` und `train.py` importieren beim Laden torch, `config`
und (self_play) `mosaic_rust`, und ihr Parser steht im
`if __name__ == "__main__":`-Block. Ein Import zoege die schweren Abhaengigkeiten
und liefe trotzdem nicht bis zum Parser. Stattdessen: per `ast` die Anweisungen
`parser = argparse.ArgumentParser(...)` und alle direkt folgenden
`parser.add_argument(...)` herausschneiden und in einem Namensraum ausfuehren,
der nur `argparse` und die einfachen Modul-Konstanten (`NAME = <Literal>`)
kennt. So pruefen die Tests Rezepte gegen den ECHTEN Parser des Werkzeugs.

Kein Test (Dateiname ohne `test_`), wird von den Testdateien per sys.path
eingebunden.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path


def _is_main_guard(test) -> bool:
    return (isinstance(test, ast.Compare) and isinstance(test.left, ast.Name)
            and test.left.id == "__name__" and len(test.comparators) == 1
            and isinstance(test.comparators[0], ast.Constant)
            and test.comparators[0].value == "__main__")


def _is_parser_assign(stmt, name: str) -> bool:
    return (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name) and stmt.targets[0].id == name
            and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Attribute)
            and stmt.value.func.attr == "ArgumentParser")


def _is_add_argument(stmt, name: str) -> bool:
    return (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Attribute)
            and stmt.value.func.attr == "add_argument"
            and isinstance(stmt.value.func.value, ast.Name)
            and stmt.value.func.value.id == name)


def module_constants(tree: ast.Module) -> dict:
    """Modul-Konstanten der Form `NAME = <Literal>` (z.B. PAUSE_EXIT_CODE)."""
    out = {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            try:
                out[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError, SyntaxError):
                pass
    return out


def module_literal(path, name: str):
    """Wert einer Modul-Konstante `name = <Literal>` (z.B. ein dict)."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    consts = module_constants(tree)
    if name not in consts:
        raise LookupError(f"{name} ist in {path} keine Literal-Konstante auf Modulebene")
    return consts[name]


def parser_from_main_block(path, name: str = "parser",
                           extra_names: dict | None = None) -> argparse.ArgumentParser:
    """Parser aus dem `__main__`-Block von `path` bauen (siehe Modul-Doku).
    Genommen wird der Block, der `<name> = argparse.ArgumentParser(...)`
    enthaelt, und davon die Zuweisung plus alle UNMITTELBAR folgenden
    `<name>.add_argument(...)`. `extra_names`: Namen, die der Parser aus
    IMPORTIERTEN Modulen liest (train.py: `VALUE_HEAD_VARIANTS` aus
    neural_net); fehlt einer, scheitert der Aufbau laut mit NameError."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    for node in tree.body:
        if not (isinstance(node, ast.If) and _is_main_guard(node.test)):
            continue
        body = node.body
        start = next((i for i, s in enumerate(body) if _is_parser_assign(s, name)), None)
        if start is None:
            continue
        stmts = [body[start]]
        for s in body[start + 1:]:
            if not _is_add_argument(s, name):
                break
            stmts.append(s)
        namespace = {"argparse": argparse, **module_constants(tree), **(extra_names or {})}
        code = compile(ast.Module(body=stmts, type_ignores=[]), str(path), "exec")
        exec(code, namespace)  # noqa: S102 -- nur Parser-Aufbau aus dem eigenen Repo
        return namespace[name]
    raise LookupError(f"kein __main__-Block mit `{name} = argparse.ArgumentParser` in {path}")
