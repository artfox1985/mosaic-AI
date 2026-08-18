# -*- coding: utf-8 -*-
"""Zielwechsel k1: Vollendbarkeit statt Realisierung als Ownership-Ziel.

Eigenes Modul, weil `neural_net.py` die Groessen-Ratsche des Konventions-Checks
reisst (Vorbild: `train_manifest.py`, aus demselben Grund ausgelagert).

Registrierung: `evaluations/PREREG_reachability_target.md`. Sperre par.5 ist
BESTANDEN (2026-08-18): das Label traegt in Runde 3-5, in Runde 1-2 ist es
konstant (100 % bzw. 98,8 % der Spalten noch vollendbar) und bleibt deshalb dort
beim Realisierungs-Label.

FOKUS-REGEL 2026-08-18: nur k1. Ersetzt werden ausschliesslich die SPALTEN-Atome
(Index 6..11 der 34 je Spieler, siehe Reihenfolge-Tabelle im Docstring von
`neural_net._conjunctions_from_dome`).
"""
import json
import os

REACH_K1_MIN_ROUND = 3
REACH_ATOMS = slice(6, 12)  # Spalten-Atome innerhalb der 34 je Spieler


def reach_target_k1_active() -> bool:
    """`MOSAIC_REACH_TARGET_K1` -- Default AUS = unveraendertes Bestandsverhalten."""
    return os.environ.get("MOSAIC_REACH_TARGET_K1", "0") not in ("", "0", "false", "False")


def reach_columns(state: dict, player: int):
    """Vollendbarkeit der 6 Spalten fuer `player` -- 1 = noch vollendbar, sonst 0.

    Quelle ist der Rust-Export `plate_completability_json` (Wrapper um
    `column_build::ist_spalte_vollendbar`); der Vorrat kommt aus
    `provocation::noch_erreichbare_farben` und zaehlt nur ueber die BRETTER
    beider Spieler, nutzt also keine verdeckte Information.

    Bewusst KEIN Python-Nachbau des Praedikats: eine zweite Fassung waere genau
    die Divergenz, die das Label entwerten wuerde.

    WARUM JE ZUSTAND: die Realisierungs-Labels entstehen EINMAL je Partie aus dem
    Endbrett; Vollendbarkeit haengt am Brett UND am Restvorrat und aendert sich
    mit jedem Zug (par.11 der Prereg). Kosten gemessen: 0,45 ms je Sample fuer
    beide Spieler inkl. `json.dumps`, also ~19 min einmalig fuer Runde 3-5.

    Gibt `None` zurueck, wenn der Export fehlt -- ein fehlendes Wheel darf einen
    Trainingslauf nicht toeten, das Label bleibt dann das alte.
    """
    try:
        import mosaic_rust
        d = json.loads(mosaic_rust.plate_completability_json(json.dumps(state), player))
        return [1 if x else 0 for x in d["columns"]]
    except Exception:  # noqa: BLE001
        return None
