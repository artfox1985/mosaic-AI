# -*- coding: utf-8 -*-
"""Uebersetzt Heuristik-Variantennamen an der Grenze zu einem eingefrorenen
Artefakt (Nutzer-Anweisung 2026-08-28: Umbenennung v1 -> hv1, v2huelle -> hv2).

DAS PROBLEM
-----------
Ein Artefakt ist unveraenderlich in dem, was es TUT: sein Wheel ist die
einzige Kopie des Verhaltens. Die beiden Heuristik-Artefakte vom 2026-08-26
tragen Wheels, die nur die ALTEN Variantennamen kennen (`v1`, `v2huelle`) --
`SearchConfig::from_spec_file` und `self_play_games_with_net_labels` weisen
dort alles andere HART ab. Der Quellstand und die Spec-Dateien tragen seit dem
2026-08-28 die neuen Namen (`hv1`, `hv2`).

DIE LOESUNG: EINE UEBERSETZUNG, KEIN WIEDERHOLUNGSVERSUCH
---------------------------------------------------------
Der Repo-Treiber spricht mit einem Artefakt in DESSEN Dialekt. Welcher das
ist, steht deterministisch im Manifest des Artefakts -- Feld `name_dialect`:

    "hv"      -> das Wheel kennt die neuen Namen, nichts wird uebersetzt
    fehlt     -> Wheel vor der Umbenennung, Rueckuebersetzung auf die
    /"legacy"    Alt-Namen

AUSDRUECKLICH NICHT: "erst neu probieren, bei Fehler mit dem alten Namen
wiederholen". Ein stiller zweiter Versuch verschleiert, WELCHER Agent gerade
gespielt hat -- und genau diese Klasse von Fehler (der Aufrufer meint das
eine, die Engine tut das andere) hat am 2026-08-26 einen falschen Befund
erzeugt und die ganze Kapselung ausgeloest.

Die neuen Namen sind ueberall sonst die einzigen gueltigen: der aktuelle Build
weist `v1` genauso hart ab wie frueher `v2huelle`.
"""
from __future__ import annotations

# Kanonischer Name -> Dialekt der Wheels vor dem 2026-08-28.
LEGACY_BY_CANONICAL = {"hv1": "v1", "hv2": "v2huelle"}

# Nur zur Diagnose (Fehlermeldungen, Werkzeuge, die ein Alt-Artefakt lesen).
CANONICAL_BY_LEGACY = {legacy: new for new, legacy in LEGACY_BY_CANONICAL.items()}

CURRENT_DIALECT = "hv"


def speaks_current_dialect(manifest: dict) -> bool:
    """Kennt das Wheel dieses Artefakts schon die neuen Namen?

    Entschieden wird an EINEM Feld des Artefakt-Manifests, nicht an einem
    Versuch und auch nicht am Einfrier-Datum: ein Datum waere eine zweite,
    stillschweigende Wahrheit ueber denselben Sachverhalt.
    """
    return manifest.get("name_dialect") == CURRENT_DIALECT


def to_artifact_dialect(name: str, manifest: dict) -> str:
    """Kanonischen Variantennamen in den Dialekt des Artefakts uebersetzen.

    `name` MUSS kanonisch sein (`hv1`/`hv2`). Ein Alt-Name hier waere ein
    Aufrufer, der die Umbenennung nicht mitbekommen hat -- harter Fehler,
    kein Durchreichen.
    """
    if name not in LEGACY_BY_CANONICAL:
        hint = ""
        if name in CANONICAL_BY_LEGACY:
            hint = (f" Das ist der ALTE Name; kanonisch heisst er jetzt "
                    f"'{CANONICAL_BY_LEGACY[name]}' (Umbenennung 2026-08-28).")
        raise ValueError(
            f"Unbekannte Heuristik-Variante {name!r}. Gueltig sind "
            f"{sorted(LEGACY_BY_CANONICAL)}.{hint}")
    if speaks_current_dialect(manifest):
        return name
    return LEGACY_BY_CANONICAL[name]


def spec_in_artifact_dialect(spec: dict, manifest: dict) -> dict:
    """Kopie der Spec, deren `heuristik_variante` das Artefakt-Wheel versteht.

    Der Feldname `heuristik_variante` selbst bleibt unveraendert: er steht in
    der pyo3-Signatur des eingefrorenen Wheels und ist damit Teil des
    Protokolls, nicht des Namensschemas.
    """
    out = dict(spec)
    out["heuristik_variante"] = to_artifact_dialect(spec["heuristik_variante"], manifest)
    return out
