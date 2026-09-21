# -*- coding: utf-8 -*-
"""Spec-Felder als Env-Knoepfe setzen -- EINE Abbildung fuer alle Python-Leser.

Eine Spec-Datei beschreibt die Seite eines Spielers (`docs/promotion_checklist.md`:
ein Champion ist Modell PLUS Spec). Die RUST-Seite liest sie selbst und kennt in
`net_mcts.rs::KNOWN_FIELDS` jedes Feld; die Python-Seite kann das nicht, weil die
Knoepfe `OnceLock`-Getter sind und VOR dem Import der Engine stehen muessen. Sie
uebersetzt die Felder darum in Umgebungsvariablen.

ANLASS FUER DIESE SAMMELSTELLE (Durchsicht 2026-09-21, par.8h Fund 6): die
Abbildung stand zweimal wortgleich im Baum (`server.py`, `tools/claude_play.py`),
`tools/oracle_metrics.py` bezog sie ueber einen Import aus `claude_play`, um keine
dritte zu erzeugen -- und ALLE DREI lagen zwoelf Felder hinter `KNOWN_FIELDS`.
Fuenf davon sind echte Suchknoepfe mit eigenem Env-Namen:

    special_unlock_w, special_unlock_beta, moon_order_search_scale,
    round_transition_leaf, net_tiling_tiebreak

**Was das wert war, praezise:** keine registrierte Zahl haengt daran. Die neun
A/B-Specs im Baum, die diese Felder tragen (`models/tiebreak_*.spec.json`,
`rt_leaf_*`, `moon_order_scale*`, `k6_*`), sind ausnahmslos ueber `paired_gating`
gemessen worden, also ueber den Rust-Leser; und die vier Laeufe von
`oracle_metrics` protokollieren als ignoriertes Feld nur `heuristik_variante`.
Es war eine geladene, keine abgefeuerte Waffe: wer eine dieser Specs durch die
GUI oder `oracle_metrics` geschickt haette, haette ZWEI IDENTISCHE ARME gemessen
und es an den Zahlen nicht gesehen.

**Der eigentliche Schutz ist darum nicht diese Datei, sondern
`tools/tests/test_spec_env.py`:** der Test liest `KNOWN_FIELDS` aus dem Rust-Code
und verlangt, dass jedes Feld entweder hier abgebildet oder unten ausdruecklich
als nicht abzubilden begruendet ist. Ein neues Spec-Feld in Rust zwingt damit zu
einer Entscheidung auf der Python-Seite, statt still zwoelf Felder anwachsen zu
lassen.

Liegt im Wurzelverzeichnis (wie `corpus_io.py`) und NICHT unter `tools/`, weil
`server.py` es importiert: `dist/mosaic_release.spec` laesst PyInstaller mit
`pathex=[PROJECT_ROOT]` ueber `run_mosaic.py` laufen, und ein Modul, das erst
ueber ein `sys.path.insert` zur Laufzeit auffindbar waere, landet nicht im
portablen Bundle.

Knopf-Namen und ihre Bedeutung: `engine/src/knob_registry.rs`.
"""
from __future__ import annotations

import json
import os

# Spec-Feld -> Env-Knopf. Reihenfolge wie `net_mcts.rs::KNOWN_FIELDS`.
SPEC_TO_ENV = {
    "implicit_minimax_alpha": "MOSAIC_IMPLICIT_MINIMAX_A",
    "long_row_init_shaping_w": "MOSAIC_LONG_ROW_INIT_W",
    "score_utility_c": "MOSAIC_SCORE_UTILITY_C",
    "score_utility_b": "MOSAIC_SCORE_UTILITY_B",
    "envelope_search_c": "MOSAIC_ENVELOPE_SEARCH_C",
    "envelope_tiling_w": "MOSAIC_ENVELOPE_TILING_W",
    "envelope_profile": "MOSAIC_ENVELOPE_PROFILE",
    "envelope_tiling_value_w": "MOSAIC_ENVELOPE_TILING_VALUE_W",
    "envelope_projection_mode": "MOSAIC_ENVELOPE_PROJECTED",
    "envelope_flush_w": "MOSAIC_ENVELOPE_FLUSH_W",
    "envelope_hull_form": "MOSAIC_ENVELOPE_HULL_FORM",
    "special_row6_w": "MOSAIC_SPECIAL_ROW6_W",
    # par.12c (2026-09-11): beide OPTIONAL mit Default 0. Fehlende Felder
    # werden uebersprungen, aeltere Specs bleiben also unveraendert.
    "dead_cell_w": "MOSAIC_DEAD_CELL_W",
    "out_wild_w": "MOSAIC_OUT_WILD_W",
    # K4 (PREREG_round_estimate_leaf_term.md par.3/par.4): OPTIONAL; das Profil
    # ist eine Liste und wird wie envelope_profile kommasepariert uebergeben.
    "round_est_c": "MOSAIC_ROUND_EST_C",
    "round_est_b_profile": "MOSAIC_ROUND_EST_B_PROFILE",
    # K6 (PREREG_special_tile_yield.md par.13/par.13.1): OPTIONAL, Default 0
    # bzw. 2,0. NACHGETRAGEN 2026-09-21 -- siehe Kopf.
    "special_unlock_w": "MOSAIC_SPECIAL_UNLOCK_W",
    "special_unlock_beta": "MOSAIC_SPECIAL_UNLOCK_BETA",
    # PREREG_dome_return_order.md par.4: OPTIONAL, Default 0 (Ziehreihenfolge).
    "return_order_mode": "MOSAIC_RETURN_ORDER_MODE",
    # PREREG_start_dome_choice.md par.9c: OPTIONAL, Default 0 (Handregel).
    "start_by_search": "MOSAIC_START_BY_SEARCH",
    # PREREG_moon_stack_order.md par.4/par.9/par.11. `moon_order_variants` hat
    # umgekehrte Polung zu den Nachbarn: Default 1 = Fan-out AN = Bestand.
    # `moon_order_search_scale` NACHGETRAGEN 2026-09-21.
    "moon_order_variants": "MOSAIC_MOON_ORDER_VARIANTS",
    "moon_order_search_sims": "MOSAIC_MOON_ORDER_SEARCH_SIMS",
    "moon_order_search_scale": "MOSAIC_MOON_ORDER_SEARCH_SCALE",
    # PREREG_round_transition_search_sampling.md par.9: OPTIONAL, Default 0.
    # NACHGETRAGEN 2026-09-21.
    "round_transition_leaf": "MOSAIC_ROUND_TRANSITION_LEAF",
    # PREREG_round_transition_search_sampling.md par.16.10: OPTIONAL, Default
    # 1 (an = Bestand), also wieder umgekehrte Polung. NACHGETRAGEN 2026-09-21.
    "net_tiling_tiebreak": "MOSAIC_NET_TILING_TIEBREAK",
}

# Felder aus `KNOWN_FIELDS`, die BEWUSST keinen Env-Knopf bekommen. Der Test
# verlangt fuer jedes einen Grund; "haben wir vergessen" ist keiner.
UNMAPPED_ON_PURPOSE = {
    # Netzlose Seite: waehlt die Heuristik-Variante des GEGNERS, kein Suchknopf
    # des Netzes. `oracle_metrics` protokolliert es als ignoriertes Feld.
    "heuristik_variante": "Heuristik-Seite, kein Netz-Suchknopf",
    # Stilmittel der Erzeugung (par.4.2): sie stehen als CLI-Flag an
    # `self_play.py` bzw. kommen in der GUI aus der Schwierigkeitsstufe. Ein
    # Env-Knopf waere eine zweite Quelle fuer dieselbe Groesse.
    "sims": "Stilmittel der Erzeugung, kommt als CLI-Flag bzw. aus der Stufe",
    "root_noise": "Stilmittel der Erzeugung, CLI-Flag",
    "action_temp": "Stilmittel der Erzeugung, CLI-Flag",
    "tau_argmax_from_move": "Stilmittel der Erzeugung, CLI-Flag",
    "deviate_prob": "Stilmittel der Erzeugung, CLI-Flag",
    "deviate_candidates": "Stilmittel der Erzeugung, CLI-Flag",
}


def env_text(value) -> str:
    """Spec-Wert als Env-Text. Listen kommasepariert (wie envelope_profile)."""
    if isinstance(value, list):
        return ",".join(str(v) for v in value)
    return str(value)


def apply_spec_env(spec, environ=None, respect_existing: bool = False) -> dict:
    """Spec-Felder in Env-Knoepfe uebersetzen und einen Bericht zurueckgeben.

    `spec` ist ein Pfad oder ein bereits geladenes dict. `respect_existing`
    laesst eine schon gesetzte, ABWEICHENDE Umgebung gewinnen (so macht es die
    GUI: ein Knopf, den der Nutzer selbst gesetzt hat, sticht die Spec -- und
    das wird laut gemeldet).

    Der Bericht traegt vier Listen:
      `gesetzt`     -- "ENV=wert", tatsaechlich gesetzt
      `ueberstimmt` -- nur bei `respect_existing`: Umgebung schlaegt Spec
      `uebergangen` -- Felder aus `UNMAPPED_ON_PURPOSE`, mit Grund
      `unbekannt`   -- Felder, die WEDER abgebildet NOCH begruendet sind

    `unbekannt` ist der Fall, um dessentwillen es diese Funktion gibt: still
    uebergangen hiesse, dass ein A/B-Lauf zwei identische Arme misst.
    """
    if environ is None:
        environ = os.environ
    if not isinstance(spec, dict):
        spec = json.loads(open(spec, encoding="utf-8").read())

    applied, overridden = [], []
    for field, env_name in SPEC_TO_ENV.items():
        if field not in spec:
            continue
        text = env_text(spec[field])
        if respect_existing and env_name in environ and environ[env_name] != text:
            overridden.append(f"{env_name}={environ[env_name]} (Spec: {text})")
            continue
        environ[env_name] = text
        applied.append(f"{env_name}={text}")

    on_purpose = [f"{k} ({UNMAPPED_ON_PURPOSE[k]})" for k in sorted(spec) if k in UNMAPPED_ON_PURPOSE]
    unknown = sorted(k for k in spec if k not in SPEC_TO_ENV and k not in UNMAPPED_ON_PURPOSE)
    return {
        "gesetzt": applied,
        "ueberstimmt": overridden,
        "uebergangen": on_purpose,
        "unbekannt": unknown,
    }
