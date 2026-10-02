# -*- coding: utf-8 -*-
"""E4: Angebots-Bedarfs-Block des Encoders, Python-Seite.

Trainings-Arm E4 (`evaluations/PREREG_evaluator_pretests.md` par.8c,
`evaluations/PREREG_v34_window.md` par.3). Die Regel steckt AUSSCHLIESSLICH in
der Engine (`engine/src/supply_demand.rs`); dieses Modul holt den Block aus dem
Wheel (`mosaic_rust.supply_demand_values_from_json`) und haelt den Knopf, der
ihn im Python-Encoder einschaltet. Ein Nachbau der Zugfolge hier waere eine
zweite Wahrheitsquelle fuer eine Spielregel (CLAUDE.md Regel 0, Ausloeser 3).

Der Knopf `MOSAIC_SUPPLY_DEMAND_FEATURES` wirkt NUR in Python (Cache-Bau,
Training, Python-Sonden): er hebt `config.INPUT_SIZE` von 888 auf 936 und
laesst `neural_net.state_to_tensor` den Block anhaengen. Die Engine braucht
ihn nicht -- Suche, Self-Play, Arena und GUI erkennen ein E4-Modell an seiner
Flach-Breite (`features.rs::features_for_layout`).

Eigenes, importarmes Modul (kein torch, kein neural_net), aus denselben
Gruenden wie `file_cache_key.py`: der Cache-Schluessel liest den Knopf, und
`neural_net.py` liegt ueber der Groessen-Schwelle.
"""
from __future__ import annotations

import json
import os

# Spiegel von `supply_demand.rs::SUPPLY_DEMAND_VALUES` (2 Spieler x 6 Reihen x
# 4 Groessen). `tools/tests/test_supply_demand_features.py` haelt den Spiegel
# gegen den Rust-Quelltext.
SUPPLY_DEMAND_VALUES = 48
# Spiegel von `supply_demand.rs::SUPPLY_DEMAND_OFFSET`: der Block sitzt fest
# hinter dem 888er-Basisvektor (= `neural_net.LEN_WITH_ORDERED_DESIGNS`).
SUPPLY_DEMAND_OFFSET = 888
# Flach-Breite eines E4-Modells.
LEN_WITH_SUPPLY_DEMAND = SUPPLY_DEMAND_OFFSET + SUPPLY_DEMAND_VALUES


def supply_demand_features_active() -> bool:
    """Liest `MOSAIC_SUPPLY_DEMAND_FEATURES`. Exakt "1", nichts sonst.

    Bei JEDEM Aufruf gelesen, nicht gecacht: Cache-Arbeiter starten als frische
    Prozesse (`feedback_watcher_workers_reimport_config`), und der Schluessel
    muss dieselbe Bindungszeit sehen wie die Bauschleife.
    """
    return os.environ.get("MOSAIC_SUPPLY_DEMAND_FEATURES") == "1"


def supply_demand_key() -> bool:
    """Der Knopf fuer BEIDE Cache-Schluessel, mit Gleichlauf-Pruefung.

    Die Breite steht ohnehin im Schluessel (`str(INPUT_SIZE)`), aber sie wird
    beim IMPORT von `config` gebunden, der Knopf dagegen hier zur Aufrufzeit
    gelesen. Laufen beide auseinander (Knopf nach dem Import gesetzt, oder
    `config.py` ohne den E4-Patch), truege ein Schluessel mit E4-Marker
    888er-Vektoren -- oder umgekehrt. Das ist ein harter Fehler, kein stiller
    Schluessel. Erwartet wird: Knopf an <=> `config.INPUT_SIZE` == 936, Knopf
    aus <=> 888.
    """
    active = supply_demand_features_active()
    from config import INPUT_SIZE
    expected = LEN_WITH_SUPPLY_DEMAND if active else SUPPLY_DEMAND_OFFSET
    if INPUT_SIZE != expected:
        raise RuntimeError(
            "MOSAIC_SUPPLY_DEMAND_FEATURES=%s, aber config.INPUT_SIZE=%d (erwartet %d). "
            "Knopf VOR dem Prozessstart setzen (config bindet die Breite beim Import) "
            "bzw. den E4-Patch an config.py anwenden."
            % ("1" if active else "aus", INPUT_SIZE, expected)
        )
    return active


def supply_demand_values(data) -> list:
    """Die 48 Werte fuer EIN Zustands-Dict (`serialize::state_to_json`).

    Ein fehlender Export ist ein HARTER Fehler und kein stiller Nullblock: ein
    Nullblock unter dem 936er-Cache-Schluessel waere genau die Sorte
    Cache-Unfall, die am 2026-09-11 24 Bloecke gekostet hat.
    """
    import mosaic_rust
    if not hasattr(mosaic_rust, "supply_demand_values_from_json"):
        raise RuntimeError(
            "Das installierte Wheel kennt `supply_demand_values_from_json` nicht, der "
            "E4-Block (MOSAIC_SUPPLY_DEMAND_FEATURES=1) ist aber verlangt. Wheel neu bauen "
            "und installieren -- ein Nullblock waere ein stiller Cache-Unfall."
        )
    values = mosaic_rust.supply_demand_values_from_json(json.dumps(data))
    if len(values) != SUPPLY_DEMAND_VALUES:
        raise RuntimeError(
            "supply_demand_values_from_json lieferte %d Werte, erwartet %d"
            % (len(values), SUPPLY_DEMAND_VALUES)
        )
    return list(values)


def append_supply_demand(features: list, data, input_size: int) -> list:
    """Haengt den Block an `features` (888 Basiswerte), wenn `input_size` ihn
    verlangt; sonst unveraendert zurueck.

    Gemeinsame Schaltstelle fuer beide Python-Bauer (`state_to_tensor_rust`
    und `state_to_tensor_python`), damit sie nicht auseinanderlaufen. Die
    Laenge der Basis wird GEPRUEFT: steht sie nicht genau auf dem Offset, saesse
    der Block an falscher Stelle -- das ist ein Fehler, keine Kuerzung.
    """
    if input_size < LEN_WITH_SUPPLY_DEMAND:
        return features
    if len(features) != SUPPLY_DEMAND_OFFSET:
        raise RuntimeError(
            "E4-Block verlangt einen Basisvektor von genau %d Werten, geliefert %d -- "
            "der Block saesse an falscher Stelle." % (SUPPLY_DEMAND_OFFSET, len(features))
        )
    return list(features) + supply_demand_values(data)
