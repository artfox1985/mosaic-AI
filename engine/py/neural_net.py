import os
import glob
from corpus_io import load_records_fh as _load_records_fh

# Traeger-A/B (PREREG_v22_window.md par.4): mit "1" sieht der Policy-Kopf
# auch die Records mit policy_target_valid=false. Einmal beim Import
# gelesen, damit derselbe Prozess nicht auf halber Strecke die Semantik
# wechselt -- der Wert geht in den Cache-Schluessel ein.
_IGNORE_PTV = os.environ.get("MOSAIC_IGNORE_POLICY_TARGET_VALID") == "1"
import re
import json
import math
import pickle
import statistics
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset
# Der Datei-Cache-Schluessel (Hebel 4) liegt in einem EIGENEN Modul: er ist
# ein abgeschlossener Vertrag, und `neural_net.py` steht laut Groessen-
# Ratsche (tools/check_conventions.py Regel 1) ohnehin ueber der Schwelle.
# Re-Export, damit Aufrufer weiter `neural_net.per_file_cache_key` sehen.
from file_cache_key import per_file_cache_key  # noqa: F401
from reach_target import (REACH_ATOMS, REACH_K1_MIN_ROUND, REACH_BUF_CAP,
                          reach_columns, reach_target_k1_active,
                          reach_buffer_mode, reach_buffer_columns)
from config import (NUM_ACTIONS, HIDDEN_SIZE, OWNERSHIP_TARGETS,
                    CONJUNCTION_TARGETS, CONJUNCTIONS_PER_PLAYER,
                    POINTS_DIST_BINS)

COLOR_MAP = {"blau": 0, "gelb": 1, "rot": 2, "schwarz": 3, "türkis": 4, None: -1, "special": 5}
PHASE_MAP = {"drafting": 0, "tiling": 1, "end": 2, "final": 3}

# Platzierte-Farbe-ID je Dome-Feld: 0=leer, 1-5=Farbe, 6=Special.
FILLED_ID_MAP = {None: 0, "blau": 1, "gelb": 2, "rot": 3, "schwarz": 4, "türkis": 5, "special": 6}
# Normalisierung der aktuellen Punkte je der 8 Wertungsplatten (grobe Skalen).
SCORE_NORM = [18.0, 42.0, 20.0, 12.0, 20.0, 22.0, 12.0, 24.0]


def _padn(lst, n):
    """Liste auf genau n Einträge bringen (0-gepolstert) — robust gegen alte Daten."""
    lst = list(lst or [])
    return (lst + [0] * n)[:n]

def state_to_tensor(data):
    """Macht aus deinem Serializer-Dict ein flaches Zahlen-Array für PyTorch."""
    features = []
    
    # 1. Globale Infos
    features.append(data.get("round", 0) / 6.0)
    features.append(PHASE_MAP.get(data.get("phase", "drafting"), 0) / 3.0)
    # Beutel-Restbestand (max. 65 Fliesen zu Spielbeginn) — Signal, wie knapp
    # Farben werden könnten.
    features.append(data.get("bag_count", 0) / 65.0)
    # Beutel+Turm je Farbe (was insgesamt noch "im Umlauf" ist) -- ergänzt das
    # bisher ungenutzte Gesamt-bag_count um eine Farbaufschlüsselung. Der
    # Beutel ist für die KI nicht direkt sichtbar, seine Zusammensetzung ist
    # aber deterministisch aus dem Rest rückrechenbar (feste Gesamtzahl je
    # Farbe minus alles sichtbar Platzierte) -- direktes Auslesen liefert
    # dieselbe Zahl, nur günstiger. /13 = TILES_PER_COLOR.
    bag_colors = data.get("bag_colors", [0] * 5)
    tower_colors = data.get("tower_colors", [0] * 5)
    for i in range(5):
        bc = bag_colors[i] if i < len(bag_colors) else 0
        tc = tower_colors[i] if i < len(tower_colors) else 0
        features.append((bc + tc) / 13.0)
    # Kuppelstapel-Maske (18, tile_id-Reihenfolge): 1, falls das Design noch
    # verdeckt im Stapel liegt -- welche Designs schon verbraucht/ausgelegt
    # sind, verrät dem Netz, was noch "lauert".
    dome_mask = data.get("dome_pool_mask", [0] * 18)
    for i in range(18):
        features.append(float(dome_mask[i]) if i < len(dome_mask) else 0.0)
    # Wild-Anteil der noch verdeckten Stapelplatten -- explizites Aggregat
    # ergänzend zur rohen Maske oben (siehe Rust serialize.rs
    # `dome_wild_remaining_frac` für die Begründung). 0.5 = neutral, falls
    # das Feld fehlt (alte JSON-Snapshots ohne dieses Feld).
    features.append(float(data.get("dome_wild_remaining_frac", 0.5)))

    # 2. Wertungsplatten (Welche 3 von 8 sind aktiv?)
    scoring_ids = data.get("scoring_tile_ids", [])
    features.extend([1.0 if i in scoring_ids else 0.0 for i in range(8)])
    
    # 3. Kleine Manufakturen (Steine zählen + BONUS CHIPS)
    for f in data.get("factories", []):
        counts = [0] * 5
        for c_str in f.get("sun", []):
            if c_str in COLOR_MAP and COLOR_MAP[c_str] != -1:
                counts[COLOR_MAP[c_str]] += 1
        features.extend([c / 5.0 for c in counts])
        
        # Hat die Fabrik einen Bonus-Chip + ist er bereits aufgedeckt?
        has_chip = 1.0 if f.get("bonus_chip") is not None else 0.0
        features.append(has_chip)
        chip_revealed = 1.0 if f.get("chip_revealed", False) else 0.0
        features.append(chip_revealed)

        # Farben des Bonus-Chips (5-dim Maske) — NUR wenn aufgedeckt (sonst
        # wäre das versteckte Information, die kein Spieler kennt). Zeigt dem
        # Netz, ob der Chip 1- oder 2-farbig (= flexibler einsetzbar) ist.
        chip_colors_mask = [0.0] * 5
        if chip_revealed:
            bc = f.get("bonus_chip") or {}
            for c_name in bc.get("colors", []):
                c_id = COLOR_MAP.get(c_name, -1)
                if 0 <= c_id < 5:
                    chip_colors_mask[c_id] = 1.0
        features.extend(chip_colors_mask)

    # 4. Große Manufaktur
    lf = data.get("large_factory", {})
    lf_sun = [0] * 5
    for c_str in lf.get("sun", []):
        if c_str in COLOR_MAP and COLOR_MAP[c_str] != -1:
            lf_sun[COLOR_MAP[c_str]] += 1
    features.extend([c / 10.0 for c in lf_sun])
    
    # 5. Spieler (Ego-Perspektive)
    curr_pi = data.get("current_player", 0)
    enemy_pi = 1 - curr_pi
    players = data.get("players", [])
    
    if len(players) == 2:
        me = players[curr_pi]
        enemy = players[enemy_pi]
        
        for p in [me, enemy]:
            features.append(p.get("score", 0) / 100.0)
            features.append(p.get("estimated_score", 0) / 100.0)
            features.append(1.0 if p.get("marker", False) else 0.0)

            # Musterreihen
            for row in p.get("pattern_lines", []):
                capacity = row.get("capacity", 1)
                features.append(len(row.get("tiles", [])) / capacity)
                color_id = COLOR_MAP.get(row.get("color"), -1)
                features.extend([1.0 if i == color_id else 0.0 for i in range(5)])
                
            # Straffläche
            features.append(len(p.get("floor", [])) / 4.0)   # MAX_BROKEN=4 (nicht 7)

            # Spielerplättchen (wie viele bereits genutzt: 0/1/2)
            features.append(p.get("tokens_used", 0) / 2.0)

            # Bonusplättchen diese Runde bereits genommen (0/1/2)
            features.append(p.get("chips_taken", 0) / 2.0)

            # Bonus-Chips: welche Farben sind verfügbar (5-dim Count-Vektor)
            chip_color_counts = [0.0] * 5
            for chip in p.get("bonus_chips", []):
                for c_name in chip.get("colors", []):
                    c_id = COLOR_MAP.get(c_name, -1)
                    if 0 <= c_id < 5:
                        chip_color_counts[c_id] += 1.0
            features.extend([c / 4.0 for c in chip_color_counts])  # max 2 chips × 2 farben = 4

            # Chip-Abschließbarkeit pro Musterreihe (Reihen 2-6 = Indizes 1-5).
            # Reihe 1 (Index 0) ausgenommen: sie hat nur 1 Feld, Chip-Mehrfeld-
            # Logik irrelevant. Ein Flag je Reihe, ob sie sich per Bonuschips
            # abschließen lässt (2 gleiche ODER 3 beliebige je fehlendem Feld;
            # deckt auch Mehrfeld-Füllung ab). Quelle: chippable_tiling_rows,
            # bereits in der Engine via can_complete_row_with_chips berechnet.
            pi_real = curr_pi if p is me else enemy_pi
            chippable_rows = {
                entry.get("ri")
                for entry in data.get("chippable_tiling_rows", [])
                if entry.get("pi") == pi_real
            }
            for ri in range(1, 6):   # Reihen-Index 1..5 (Reihe 2..6)
                features.append(1.0 if ri in chippable_rows else 0.0)
            
        # 6. Kuppelzustand (pro Spieler: 9 Slots × 17 Features = 153 Features × 2 = 306)
        COLOR_ID_MAP = {"blau": 1, "gelb": 2, "rot": 3, "schwarz": 4, "türkis": 5}
        TYPE_MAP     = {"NORMAL": 0.0, "WILD": 0.5, "SPECIAL": 1.0}

        for p in [me, enemy]:
            dome = p.get("dome_grid", [])
            for sr in range(3):
                for sc in range(3):
                    row = dome[sr] if sr < len(dome) else []
                    slot = row[sc] if sc < len(row) else None

                    if slot is None:
                        # Slot leer — 17 Nullen
                        features.extend([0.0] * 17)
                    else:
                        features.append(1.0)  # slot existiert
                        for space in slot.get("spaces", [{}, {}, {}, {}]):
                            # placed-color id: 0=leer, 1-5=Farbe, 6=special
                            # (behält belegt/leer UND die platzierte Farbe)
                            filled = space.get("filled")
                            features.append(FILLED_ID_MAP.get(filled, 0) / 6.0)
                            # required_color normalisiert (0=kein, 1-5=farbe)
                            req = space.get("color")
                            features.append(COLOR_ID_MAP.get(req, 0) / 5.0)
                            # space type: NORMAL=0.0, WILD=0.5, SPECIAL=1.0
                            sp_type = space.get("type", "NORMAL")
                            features.append(TYPE_MAP.get(sp_type, 0.0))
                            # locked: nur relevant für SPECIAL (0=offen, 1=gesperrt)
                            locked = space.get("locked", False)
                            features.append(1.0 if locked else 0.0)

        # 6b. Berechnete Endwertungs-/Geometrie-Features (pro Spieler, 37 je Spieler)
        # Damit das Netz lernt, WIE Endpunkte entstehen (Quelle: Rust
        # scoring::player_scoring_features). Endkriterien sind harte geometrische
        # Prädikate, die ein flaches MLP aus der Roh-Kodierung kaum lernt.
        for p in [me, enemy]:
            pts = _padn(p.get("scoring_tile_points"), 8)
            for i in range(8):
                features.append(pts[i] / SCORE_NORM[i])
            geo = p.get("score_geo", {})
            features.extend(v / 6.0 for v in _padn(geo.get("row_fill"), 6))
            features.extend(v / 6.0 for v in _padn(geo.get("col_fill"), 6))
            features.extend(v / 6.0 for v in _padn(geo.get("diag_fill"), 2))
            features.extend(v / 5.0 for v in _padn(geo.get("row_colors"), 6))
            features.append(geo.get("border_fill", 0) / 20.0)
            features.extend(v / 4.0 for v in _padn(geo.get("corner_fill"), 4))
            features.append(geo.get("wild_filled", 0) / 8.0)
            features.append(geo.get("wild_total", 0) / 8.0)
            features.append(geo.get("special_empty", 0) / 8.0)
            features.append(geo.get("special_total", 0) / 8.0)

        # 6c. Linien-Geometrie (offensives Linien-Bauen, 23 je Spieler).
        # Punkte = zusammenhängende orthogonale Läufe → diese Struktur explizit
        # machen, damit das flache MLP Linien-Strategie repräsentieren kann
        # (Quelle: Rust scoring::player_line_features).
        for p in [me, enemy]:
            lg = p.get("line_geo", {})
            features.extend(v / 6.0 for v in _padn(lg.get("h_hist"), 5))   # Läufe len 2-6
            features.extend(v / 6.0 for v in _padn(lg.get("v_hist"), 5))
            features.append(lg.get("cluster_sq", 0) / 150.0)               # Σ länge²
            features.extend(v / 12.0 for v in _padn(lg.get("row_potential"), 6))
            features.extend(v / 12.0 for v in _padn(lg.get("col_potential"), 6))

    # 7. Mondseite kleine Fabriken (pro Fabrik: 3 Positionen × 5 Farben = 15 Features)
    # Position 0 = oben (abholbar), Position 1 = darunter, Position 2 = ganz unten
    for f in data.get("factories", []):
        moon_features = [0.0] * 15
        stacks = f.get("moon", [])
        if stacks:
            stack = stacks[0]  # max 1 Stapel pro kleiner Fabrik
            for pos, stone in enumerate(reversed(stack)):
                if pos >= 3:
                    break
                c_id = COLOR_MAP.get(stone, -1)
                if c_id >= 0:
                    moon_features[pos * 5 + c_id] = 1.0
        features.extend(moon_features)

    # 8. GF Moon-Pool (flach — Farb-Counts, keine Reihenfolge relevant)
    pool = data.get("large_factory", {}).get("moon", [])
    pool_counts = [0] * 5
    for c_str in pool:
        c_id = COLOR_MAP.get(c_str, -1)
        if c_id >= 0:
            pool_counts[c_id] += 1
    features.extend([c / 10.0 for c in pool_counts])

    # 9. Kuppel-Display (max 3 Platten × 4 Spaces × 2 Features = 24)
    # Pro Space: is_filled (1) + required_color normalisiert (1)
    DOME_COLOR_MAP = {"blau": 1, "gelb": 2, "rot": 3, "schwarz": 4, "türkis": 5}
    dome_display = data.get("dome_display", [])
    for slot_idx in range(3):
        if slot_idx < len(dome_display):
            plate = dome_display[slot_idx]
            spaces = plate.get("spaces", []) if plate else []
            for space_idx in range(4):
                if space_idx < len(spaces):
                    space = spaces[space_idx]
                    filled = space.get("filled")
                    features.append(1.0 if filled is not None else 0.0)
                    req = space.get("color")
                    features.append(DOME_COLOR_MAP.get(req, 0) / 5.0)
                else:
                    features.extend([0.0, 0.0])
        else:
            features.extend([0.0] * 8)  # leerer Slot: 4 Spaces × 2 Features

    # 10. Kuppel-Stapel (Anzahl verbleibende Platten)
    features.append(data.get("dome_stack_count", 0) / 20.0)

    # 11. Erreichbare Spaltenfuellung des ziehenden Spielers (6) -- ans Ende
    # des flachen Blocks, spiegelbildlich zu features.rs Abschnitt 11.
    # GELESEN, nicht gerechnet: die Formel steht einmal in
    # plate_builder::achievable_column_fill und wird in
    # serialize::serialize_player ausgewertet. 0.0 als Rueckfall fuer alte
    # Schnappschuesse ohne das Feld (gleiches Muster wie
    # dome_wild_remaining_frac).
    _pi = data.get("current_player", 0)
    _spieler = data.get("players", [])
    _f_max = (_spieler[_pi].get("col_f_max", []) if _pi < len(_spieler) else [])
    for _c in range(6):
        features.append(float(_f_max[_c]) / 6.0 if _c < len(_f_max) else 0.0)

    return torch.tensor(features, dtype=torch.float32)


# --- 2D-Encoder-Skelett (Task #11, Phase 1) --------------------------------
# `state_to_planes` ist der 2D-Zweig NEBEN `state_to_tensor` (das oben
# UNVERAENDERT bleibt) -- additiv, siehe docs/design_2d_encoder.md für die
# vollständige Begründung der Kanal-Aufteilung und des Geometrie-Gatings.
# Kein Training/HDF5-Cache-Bau in Phase 1 (Stopp-Linie) -- reines
# Format-Skelett, per Selbsttest (siehe tools/) gegen echte Zustände geprüft.

# Dieselben 5 Farben wie COLOR_MAP oben, aber als geordnete Liste (Index =
# Kanal-Offset in state_to_planes, siehe _board_channels).
DOME_COLORS_5 = ["blau", "gelb", "rot", "schwarz", "türkis"]
_SPACE_TYPE_IDX = {"NORMAL": 0, "WILD": 1, "SPECIAL": 2}

# Slot-Koordinaten (sr, sc) der 4 Eckplatten -- siehe
# scoring.rs::score_corner_tiles: (0,0)/(0,2) zählen 3 Pkt, (2,0)/(2,2)
# zählen 8 Pkt (asymmetrisch je Ecke) -- daher 4 EINZELNE Masken statt einer
# gemeinsamen (design_2d_encoder.md Abschnitt 4).
_CORNER_SLOTS = [(0, 0), (0, 2), (2, 0), (2, 2)]


def _build_geometry_masks() -> dict:
    """Konstante 6x6-Positions-Masken der Wertungsgeometrie (Zeilen/Spalten/
    Diagonalen/Rand/Ecken) -- unabhängig vom Spielzustand, einmal berechnet.
    Quelle der Geometrie: engine/src/scoring.rs (build_grid/score_*), siehe
    docs/design_2d_encoder.md Abschnitt 2+4."""
    row = torch.zeros(6, 6, 6)
    col = torch.zeros(6, 6, 6)
    for i in range(6):
        row[i, i, :] = 1.0
        col[i, :, i] = 1.0
    diag = torch.zeros(2, 6, 6)
    for i in range(6):
        diag[0, i, i] = 1.0       # Hauptdiagonale
        diag[1, i, 5 - i] = 1.0   # Nebendiagonale
    border = torch.zeros(1, 6, 6)
    for r in range(6):
        for c in range(6):
            if r in (0, 5) or c in (0, 5):
                border[0, r, c] = 1.0
    corner = torch.zeros(4, 6, 6)
    for k, (sr, sc) in enumerate(_CORNER_SLOTS):
        corner[k, sr * 2:sr * 2 + 2, sc * 2:sc * 2 + 2] = 1.0
    return {"row": row, "col": col, "diag": diag, "border": border, "corner": corner}


_GEOM = _build_geometry_masks()

# Kanalzahl-Buchhaltung (siehe docs/design_2d_encoder.md Abschnitt 3/4):
#   Belegung je Spieler: 16 (1 slot_exists + 5 placed_color + 1 placed_special
#                            + 5 required_color + 3 type + 1 locked)
#   -> 32 für beide Spieler (ego zuerst, dann Gegner -- state_to_tensor-Konvention)
#   Geometrie roh:     19 (6 Zeilen + 6 Spalten + 2 Diagonalen + 1 Rand + 4 Ecken)
#   Geometrie gegatet: 25 (6 Zeilen@Tile0 + 6 Zeilen@Tile7 + 6 Spalten@Tile1
#                          + 2 Diagonalen@Tile2 + 1 Rand@Tile4 + 4 Ecken@Tile5)
#   Erreichbarkeit:     1 (Kanal 76, ziehender Spieler)
#   Spezialfeld:        2 (Kanal 77 Ertrag 1..6, Kanal 78 Abstand 0..3,
#                          PREREG_special_tile_yield.md par.4a)
NUM_PLANES_CHANNELS = 2 * 16 + 19 + 25 + 1 + 2  # = 79

# Wieviele der Kanaele STRIKT BINAER (0/1) sind -- die Grenze, an der das
# Bitpacking des Korpus-Caches endet.
#
# WARUM DAS EINE EIGENE ZAHL BRAUCHT: `corpus_dataset.py::_pack_bits` schiebt
# die planes durch `np.packbits`, und das interpretiert JEDEN Wert != 0 als
# gesetztes Bit. Die zwei Spezialfeld-Kanaele tragen 1..6 bzw. 0..3 -- ohne
# diese Grenze waeren sie im Cache stillschweigend auf 0/1 plattgedrueckt,
# ohne Fehlermeldung, und das Netz haette "irgendein Spezialfeld" statt
# "Ertrag 6, noch zwei Felder offen" gelernt. Die nicht-binaeren Kanaele
# werden deshalb ROH (uint8) hinter den gepackten Block gehaengt, siehe
# `unpack_planes_batch` unten und `corpus_dataset.py::_pack_planes`.
#
# Regel fuer kuenftige Kanaele: binaere Ebenen kommen VOR diese Grenze,
# wertetragende dahinter -- sonst bricht die Zerlegung.
NUM_BINARY_PLANES_CHANNELS = 2 * 16 + 19 + 25 + 1  # = 77


def _board_channels(dome_grid) -> torch.Tensor:
    """16 Kanäle für EIN Spielerbrett (6x6) -- siehe Tabelle in
    docs/design_2d_encoder.md Abschnitt 3. `dome_grid`: 3x3-Liste von Slots
    (oder None), jeder Slot ein Dict mit `spaces` (Liste von 4 Space-Dicts,
    Reihenfolge TL,TR,BL,BR -- identisch zu scoring.rs::build_grid)."""
    ch = torch.zeros(16, 6, 6)
    for sr in range(3):
        row = dome_grid[sr] if sr < len(dome_grid) else []
        for sc in range(3):
            slot = row[sc] if sc < len(row) else None
            if slot is None:
                continue
            spaces = slot.get("spaces", [{}, {}, {}, {}])
            for si in range(4):
                sp = spaces[si] if si < len(spaces) else {}
                r = sr * 2 + si // 2
                c = sc * 2 + si % 2
                ch[0, r, c] = 1.0  # Slot vorhanden
                filled = sp.get("filled")
                if filled in DOME_COLORS_5:
                    ch[1 + DOME_COLORS_5.index(filled), r, c] = 1.0
                elif filled == "special":
                    ch[6, r, c] = 1.0
                req = sp.get("color")
                if req in DOME_COLORS_5:
                    ch[7 + DOME_COLORS_5.index(req), r, c] = 1.0
                sp_type = sp.get("type", "NORMAL")
                ch[12 + _SPACE_TYPE_IDX.get(sp_type, 0), r, c] = 1.0
                if sp.get("locked", False):
                    ch[15, r, c] = 1.0
    return ch


def state_to_planes(data) -> torch.Tensor:
    """2D-Gegenstück zu `state_to_tensor` (Task #11 Phase 1) -- Format
    [C,6,6], C=NUM_PLANES_CHANNELS=79. ADDITIV: `state_to_tensor` bleibt
    unverändert, dies ist ein PARALLELER Zweig für den geplanten
    Conv-Encoder (siehe docs/design_2d_encoder.md). Ego-Perspektive wie
    überall sonst: erst der Spieler am Zug, dann der Gegner."""
    curr_pi = data.get("current_player", 0)
    enemy_pi = 1 - curr_pi
    players = data.get("players", [])
    if len(players) != 2:
        return torch.zeros(NUM_PLANES_CHANNELS, 6, 6)

    me_grid = players[curr_pi].get("dome_grid", [])
    enemy_grid = players[enemy_pi].get("dome_grid", [])
    board = torch.cat([_board_channels(me_grid), _board_channels(enemy_grid)], dim=0)  # [32,6,6]

    scoring_ids = set(data.get("scoring_tile_ids", []))

    def gate(tid: int) -> float:
        return 1.0 if tid in scoring_ids else 0.0

    raw_geom = torch.cat(
        [_GEOM["row"], _GEOM["col"], _GEOM["diag"], _GEOM["border"], _GEOM["corner"]], dim=0
    )  # [19,6,6]

    gated = torch.cat([
        _GEOM["row"] * gate(0),
        _GEOM["row"] * gate(7),
        _GEOM["col"] * gate(1),
        _GEOM["diag"] * gate(2),
        _GEOM["border"] * gate(4),
        _GEOM["corner"] * gate(5),
    ], dim=0)  # [25,6,6]

    # Kanal 76: Erreichbarkeit je Zelle fuer den ziehenden Spieler,
    # spiegelbildlich zu features.rs. GELESEN aus `cell_reachable_mask`
    # (Bit r*6+c), nicht gerechnet -- die Formel steht einmal in
    # column_build::cell_is_completable und wird in serialize_player
    # ausgewertet. Fehlt das Feld (alte Schnappschuesse), bleibt die Ebene 0.
    _mask = int(players[curr_pi].get("cell_reachable_mask", 0))
    _reach = torch.zeros(1, 6, 6)
    for _r in range(6):
        for _c in range(6):
            if _mask >> (_r * 6 + _c) & 1:
                _reach[0, _r, _c] = 1.0

    # Kanaele 77/78 (PREREG_special_tile_yield.md par.4a), NUR ziehender
    # Spieler, spiegelbildlich zu `features.rs::write_special_tile_channels_direct`:
    #   [0] ausstehender Ertrag  = pattern_row + 1 = r + 1 (1..6) auf einem
    #       noch UNGEFUELLTEN SPECIAL-Feld (Punktformel round_end.rs:361-362),
    #   [1] Abstand zur Ausloesung = Zahl der noch ungefuellten
    #       Nicht-SPECIAL-Felder desselben Slots (0..3; WILD zaehlt als
    #       Nicht-SPECIAL, Freischaltbedingung dome.rs::try_unlock_special).
    # Alles Uebrige 0; ein Ertrag > 0 unterscheidet "Abstand 0" von
    # "kein Spezialfeld". GERECHNET aus `dome_grid`, nicht aus einem neuen
    # serialisierten Feld gelesen -- so wirken die Kanaele rueckwirkend auf
    # dem gesamten Bestandskorpus. KEINE Normalisierung: die Skalierung
    # lernt das Netz.
    _special = torch.zeros(2, 6, 6)
    for _sr in range(3):
        _row = me_grid[_sr] if _sr < len(me_grid) else []
        for _sc in range(3):
            _slot = _row[_sc] if _sc < len(_row) else None
            if _slot is None:
                continue
            _spaces = _slot.get("spaces", [{}, {}, {}, {}])
            _open_others = sum(
                1 for _sp in _spaces
                if _sp.get("type", "NORMAL") != "SPECIAL" and _sp.get("filled") is None
            )
            for _si in range(4):
                _sp = _spaces[_si] if _si < len(_spaces) else {}
                if _sp.get("type", "NORMAL") != "SPECIAL" or _sp.get("filled") is not None:
                    continue
                _r = _sr * 2 + _si // 2
                _c = _sc * 2 + _si % 2
                _special[0, _r, _c] = float(_r + 1)
                _special[1, _r, _c] = float(_open_others)

    return torch.cat([board, raw_geom, gated, _reach, _special], dim=0)  # [79,6,6]


MAX_PENDING_STACK_TILES = 4  # muss zu features.rs::MAX_PENDING_STACK_TILES passen

def action_to_id(action: dict) -> int:
    """Python-Mirror von `features.rs::action_to_id` -- MUSS bei jeder Änderung
    dort synchron gehalten werden (kein automatischer Abgleich, siehe Vorfall
    2026-07-19: `dome`/`dome_stack` kollabierten Slot+Rotation NICHT mehr in
    die ID, der Python-Mirror war noch auf dem alten 108/36-ID-Schema)."""
    t = action.get("type", "")
    if t == "pass":       return 0
    if t == "end_tiling": return 1

    if t == "stone":
        # factory_index: 0-3=kleine Fabriken, 4=GF, 5=Mondaktion
        # color: 0-4, row: -1..6 → 0..7
        c_id  = max(0, COLOR_MAP.get(action.get("color"), 0))
        r_id  = action.get("row", 0) + 1           # -1..6 → 0..7
        f_idx = action.get("factory_index", 0)     # 0-5
        return min(10 + (c_id * 48) + (r_id * 6) + f_idx, 273)
        # max: 10 + (4*48) + (7*6) + 5 = 10 + 192 + 42 + 5 = 249 ✅ < 274

    if t == "tiling":
        pr = action.get("pattern_row", 0)
        sr = action.get("slot_row", 0)
        sc = action.get("slot_col", 0)
        return 274 + (pr * 9) + (sr * 3) + sc      # 274–327

    if t == "choose_dome_slot":
        # Baustein B: Kachel (Auslage-Index 0-2) + Slot ZUSAMMEN, Rotation ist
        # eine separate Stufe-2-Aktion (choose_dome_rotation) -- ersetzt das
        # frühere kollabierte "dome"-Schema (dome_slot_head/dome_rotation_head).
        d_idx = action.get("display_index", 0)
        sr = action.get("slot_row", 0)
        sc = action.get("slot_col", 0)
        return 328 + (d_idx * 9) + (sr * 3) + sc  # 328-354

    if t == "choose_draw_stack_slot":
        # `pending_index`: Position der gewaehlten Platte in der deduplizierten
        # Pending-Liste (self_play.rs::action_to_env_dict), gedeckelt statt
        # Kachel-kodiert. + Slot zusammen, Rotation separat (siehe oben).
        p_idx = min(action.get("pending_index", 0), MAX_PENDING_STACK_TILES - 1)
        sr = action.get("slot_row", 0)
        sc = action.get("slot_col", 0)
        return 355 + (p_idx * 9) + (sr * 3) + sc  # 355-390

    if t == "choose_dome_rotation":
        # EINE gemeinsame ID-Familie fuer beide Pfade (Display/Stapel).
        rot_idx = max(0, min(3, action.get("rotation", 0) // 90))
        return 391 + rot_idx  # 391-394

    if t == "use_chips":
        return 395 + action.get("pattern_row", 0)  # 395-400

    if t == "bonus_chip":
        return 401 + action.get("factory_index", 0)  # 401-404

    if t == "dome_stack_peek":
        return 405

    return 405  # Fallback

# --- 2. DATENSATZ & NETZWERK ---

# Value-Target = das TATSÄCHLICHE ENDERGEBNIS der ganzen Partie (inkl.
# Wertungsplatten), als Ziel für JEDEN Schritt der Partie — klassisches
# AlphaZero-Prinzip (delayed reward): der Zielwert für einen Runde-1-Zustand
# ist derselbe wie für den letzten Zug, nämlich wie das Spiel am Ende wirklich
# ausging.
#
# Bewusst NICHT die pro-Runde projizierte Größe (own.score + estimated_score)
# als dichtes Zwischensignal — das wurde probiert und verworfen: die
# Heuristik maximiert bereits gierig die Rundenpunkte, hat aber keine
# Weitsicht (kein strategischer Board-Aufbau, keine Wertungsplatten). Ein
# Rundenprojektions-Ziel hätte dem Netz denselben gierigen Rundenoptimum-Bias
# beigebracht — Runde 1/2 bewusst suboptimal spielen, um in Runde 3/4 durch
# strategischen Aufbau viel mehr zu holen, wäre dann NICHT belohnt worden
# (der Zielwert für Runde-1-Zustände hätte Runde 3/4 gar nicht gesehen).
# Das reine Partie-Endergebnis als Ziel lernt automatisch, dass ein
# scheinbar suboptimaler früher Zustand gut ist, WENN er zuverlässig zu einem
# starken Endergebnis führt.
#
# own_total = step["scores"][eigener Spieler]  (bereits inkl. Wertungsplatten,
#             von apply_end_scoring() in Rust eingerechnet)
# opp_total = step["scores"][Gegner]
# value = tanh(own_total/VALUE_SCALE)
# (Schema 20, Nutzer-Entscheid 2026-08-10: der frueher abgezogene
#  VALUE_OPP_EPSILON·tanh(opp_total/VALUE_SCALE)-Term ist ENTFALLEN. Begruendung
#  in evaluations/PREREG_points_head_epsilon.md -- kurz: der Term war im
#  Suchpfad nur ueber `opp_aware_points_utility` rueckgewinnbar, und der liegt
#  hinter dem `w == 0.0`-Kurzschluss, ist also toter Code.)
#
# Getrennt gesättigt statt Differenzbildung VOR dem tanh (wie zuvor
# `own − 0.5·opp`, dann erst tanh): eine Differenz sättigt bei großem Abstand
# für BEIDE Terme gemeinsam — das Netz verliert dann jede Fähigkeit, zwischen
# "gut" und "noch besser" bzw. "schlecht" und "noch schlechter" zu
# unterscheiden, obwohl Priorität 1 (maximale eigene Punktzahl) in jeder
# Stellung weiterhin gilt. Genau das Problem, das `mcts.rs::evaluate()` schon
# durch rein absolute Pro-Spieler-Bewertung behoben hat — konsistent dazu
# bekommt jetzt auch das Value-Head-Ziel einen eigenen, unabhängig sättigenden
# own-Term (volle Differenzierung über den ganzen Bereich).
# HISTORISCH (bis Schema 19): ein Gegner-Term bildete Priorität 2 ("wenn
# möglich dem Gegner schaden") additiv NACH der Sättigung ab und konnte den
# Gesamtwert um max. ±VALUE_OPP_EPSILON verschieben. Ab Schema 20 ENTFALLEN --
# Priorität 2 gehört, wenn überhaupt, in einen eigenen Kopf mit eigenem
# Gewicht, nicht als Verunreinigung in ein Eigenpunkte-Ziel.
# VALUE_SCALE-Kalibrierung: NICHT aus aktuellen Spieldaten abgeleitet (Heuristik
# und Netz spielen beide noch schwach — jede aus dieser Verteilung abgeleitete
# Skala würde nur die aktuelle Schwäche festschreiben, nicht das echte
# Punktepotenzial des Spiels). Stattdessen an einem groben menschlichen
# Referenzwert kalibriert: ab ~100 Punkten gilt ein Ergebnis als sehr gut.
# VALUE_SCALE=50 legt den tanh-Arg bei own_total=100 auf 2.0 (tanh(2.0)≈0.96)
# — informativ, aber noch nicht voll gesättigt, sodass auch darüber hinaus
# noch Differenzierung möglich bleibt. Deutlich gröber als eine "saubere"
# Herleitung, aber begründeter als eine an aktueller Schwäche kalibrierte Zahl.
# VALUE_SCHEMA_VERSION erzwingt einen Cache-Rebuild bei Änderungen an dieser Formel.
#
# Zwei getrennte Ziele, zwei Köpfe (Value-Head zurückgeholt, siehe
# evaluations/stage2_investigation.md fuer die Historie). KORREKTUR ggue.
# frueheren Kommentarstand hier: `values` ist NICHT tot in der Suche --
# net_mcts.rs::make_node liest bei ACTIVE_LEAF=Net (aktueller Standard)
# ausschliesslich `value_to_win_prob(value)` fuer den PUCT-Blattwert, `points`
# wird dort explizit verworfen (Kommentar "reines Trainings-Zusatzsignal, hier
# nie gebraucht"). D.h. `values` treibt die Suche, `points_forecast` ist reines
# Trunk-Zusatzsignal ohne Sucheinfluss -- umgekehrt zu dem, was man aus dem
# Namen "Aux-Head" vermuten wuerde.
#   - `values`     : reines Sieg/Niederlage-Ziel (+1/-1, wer hat GEWONNEN),
#                    der klassische AlphaZero-Value-Head. Einfacher/robuster
#                    als ein Punktestand-Regressionsziel (siehe
#                    feedback_value_head_capacity.md: die alte reine
#                    Punktestand-Variante blieb bei Val-R² 0.27-0.34 haengen,
#                    vermutlich irreduzibles Ziel-Rauschen).
#   - `points_forecast`: die alte Punktestand-Formel als separater Aux-Head
#                    (tanh(eigen/SCALE) - EPSILON*tanh(gegner/SCALE)) -- liefert
#                    dem Trunk ein feineres, kontinuierliches Zusatzsignal
#                    ohne dass die SUCHE je darauf zugreift.
#                    Ab Version 11: wo vorhanden, nutzt `points_forecast`
#                    das gemittelte Rundenübergangs-Sampling
#                    (`round_transition_value`) statt der einzelnen,
#                    verrauschten Partie-Endpunktzahl (siehe
#                    round_transition.rs -- Versuch, das dokumentierte
#                    Val-R²-Plateau ueber ein rauschaermeres Ziel
#                    anzugehen). Half beim points_forecast-Head (Val-R²
#                    0.27->0.34, v8->v8b).
#                    Ab Version 12: `round_transition_value` (wo vorhanden)
#                    ersetzt jetzt AUCH `values` selbst, nicht nur
#                    `points_forecast` -- v8/v8b zeigten trotz gesenktem
#                    VALUE_WEIGHT weiterhin Val-R²<0 fuer `values` (den Head,
#                    der tatsaechlich die Suche treibt), waehrend
#                    `points_forecast` mit derselben Rauschreduktion bereits
#                    auf Val-R²=0.34 kam. Gleiche Ursache: das reine
#                    Partie-Endergebnis haengt fuer fruehe Zustaende von noch
#                    ungezogenen Fabrik-Neubefuellungen ab (siehe oben), das
#                    trifft `values` genauso wie `points_forecast`.
#                    Ab Version 13 (2026-07-19): Kalibrierungs-Diagnose auf
#                    v8e zeigte corr(val_true, pts_true) nur 0.49 (die beiden
#                    ZIELE selbst stimmen nur maessig ueberein -- points_forecast
#                    gewichtet own_total stark, values ist reines Sieg/
#                    Niederlage), UND beide Koepfe fitten die (ueberwiegend
#                    gesehenen) Trainingsdaten aehnlich gut (corr(pred,true)
#                    ~0.68-0.69) -- das Problem ist also eine echte
#                    Generalisierungsluecke, kein grundsaetzlich ungelernbares
#                    Ziel. Hypothese: das HARTE ±1-Ziel (Fallback ohne rtv)
#                    ist "schaerfer" als das weiche, kontinuierliche
#                    points_forecast-Ziel und treibt den gemeinsamen Trunk
#                    staerker Richtung Overfitting (v8e: Val-R² startet bei
#                    Epoche 1 positiv (+0.135), zerfaellt danach monoton --
#                    klassisches Overfitting-Muster). Fallback (ohne rtv)
#                    daher von hartem sign(own_total-opp_total) auf ein
#                    weiches, SYMMETRISCHES Margin-Ziel umgestellt:
#                    tanh((own_total-opp_total)/VALUE_SCALE) -- selbe
#                    zugrundeliegende Information wie zuvor, nur nicht mehr
#                    an den Raendern gesaettigt/binarisiert. `rtv` bleibt
#                    unveraendert bevorzugt, wo vorhanden.
# Ab Version 14 (Fund 7, externe Bugfix-Review Bugfixes.txt Abschnitt C):
#                    `scores` klemmt regelkonform bei 0 (PlayerBoard::apply_score)
#                    -- das verwischt im Fallback-Zweig (kein rtv) "schlecht"
#                    (0) und "desastroes" (eigentlich weit im Minus) zum
#                    selben Label. own_total/opp_total nutzen daher jetzt
#                    `scores_unclamped` (nie geklemmt, self_play.rs), mit
#                    Fallback auf `scores` falls das Feld in aelteren Daten
#                    fehlt (gleiches Graceful-Degradation-Muster wie
#                    policy_weights/points_forecast oben). `rtv`-Zweig bleibt
#                    unveraendert (eigene, bereits ungeklemmte Quelle).
# Ab Version 15 (Punkt 6, evaluations/value head tests.txt): TD-Bootstrap-
#                    Blend. Der Noise-Floor-Test (STATUS.md, 2026-07-20/21,
#                    bias-korrigiert) zeigt fuer Runde 1 einen praktisch
#                    nicht von Null unterscheidbaren Deckel fuers
#                    Endergebnis-Ziel (auch `rtv` zielt darauf, nur variance-
#                    reduziert -- gleiche niedrige Decke). `bootstrap_value`
#                    (self_play.rs::bootstrap_value_after_rounds, NUR
#                    BOOTSTRAP_HORIZON_ROUNDS Runden vorausgeschaut statt bis
#                    zum echten Spielende) zielt auf eine NAEHERE, laut der
#                    Runde-fuer-Runde-R²-Tabelle deutlich hoehere Decke.
#                    Wo vorhanden, wird es TD(lambda)-artig mit dem
#                    bisherigen Ziel gemischt (TD_LAMBDA, siehe unten) --
#                    ERSETZT `val`/`points_val` NICHT vollstaendig wie `rtv`,
#                    sondern mischt hinein. Erster, ungetesteter Wert.
# Ab Version 16 (Task #34, STATUS.md "Sieg/Niederlage-Ziel wiederherstellen"
#                    /"ZUSAMMENFUEHRUNG ... WDL ist NICHT hinfaellig"): die
#                    v13-Umstellung (siehe Version-13-Absatz oben) hat den
#                    Value-Kopf faktisch zu einem zweiten Punkte-Kopf gemacht
#                    (`corr(val_true, pts_true)` nur 0.49 vor Schema 13, seither
#                    beide Koepfe auf derselben tanh-Punkte-Marge) -- die
#                    beabsichtigte Kopf-TRENNUNG (Sieg/Niederlage vs.
#                    Punktestand) war seit Version 13 aufgehoben. Zwei neue,
#                    rein ADDITIVE Cache-Felder (aendern `values`/
#                    `points_forecast` NICHT):
#                      - `values_wdl`  : GEWINNWAHRSCHEINLICHKEIT in [0,1].
#                        Hartes Ziel `y = 1.0 falls winner==player sonst 0.0`,
#                        wo vorhanden TD(lambda)-geblendet mit `bootstrap_value`
#                        -- EXAKT dieselbe Blend-Formel/dasselbe TD_LAMBDA wie
#                        beim bisherigen Ziel oben, ABER `bootstrap_value`
#                        liegt bereits als [0,1]-Wahrscheinlichkeit vor und wird
#                        hier NICHT wie beim tanh-Ziel per `*2-1` auf [-1,1]
#                        remappt -- direkt als Wahrscheinlichkeit geblendet.
#                        Macht den TD-Blend semantisch kohaerent (STATUS.md
#                        "Bonus-Befund": beide Anteile jetzt auf derselben
#                        Skala, anders als beim tanh-Ziel, das eine
#                        Punkte-Marge mit einer Gewinnwahrscheinlichkeit
#                        mischt). Der rtv-Zweig bleibt unangetastet/deaktiviert
#                        (`nortv` ist Standard) -- `values_wdl` ignoriert ihn
#                        komplett, unabhaengig von `value_target_variant`.
#                      - `wdl_outcome` : der ROHE, UNGEBLENDETE tatsaechliche
#                        Spielausgang (0.0/1.0, -1.0 = unbekannt bei
#                        unvollstaendigen Partien) -- NICHT das Trainingsziel,
#                        sondern die Referenz fuer eine ARM-uebergreifend
#                        vergleichbare Kalibrierungskennzahl (Brier-Score,
#                        siehe train.py) -- `values`/`values_wdl` sind beide
#                        TD-geblendet und damit dafuer ungeeignet.
#                    Modellseitig (siehe `MosaicNet`/`Mosaic2DNet`,
#                    `--value-head wdl` in train.py): der Value-Kopf bekommt
#                    intern 2 Logits + Softmax -> P(Sieg), `forward()` gibt an
#                    der BESTEHENDEN Position weiterhin einen Skalar zurueck,
#                    naemlich `2*P(Sieg)-1` -- exakt dieselbe [-1,1]-Skala/
#                    Position wie der alte Tanh-Kopf. Dadurch gilt
#                    `net_mcts.rs::value_to_win_prob(2*P(Sieg)-1) == P(Sieg)`
#                    EXAKT (geprueft: `value_to_win_prob(v) = (v+1)/2`) -- KEINE
#                    Rust-Aenderung noetig, jeder bestehende ONNX-Konsument
#                    funktioniert unveraendert. Default bleibt der Tanh-Kopf
#                    (`--value-head tanh`) -- byte-identisches
#                    Bestandsverhalten, wenn das Flag nicht gesetzt ist.
# Schema 17 (2026-08-06, v20-Kampagne): `values_wdl` wird fuer Dateien von
# ALT-Generatoren (tanh-Kopf, gestauchte Marge als "Wahrscheinlichkeit")
# bereits beim Cache-Bau Platt-ENTSTAUCHT geblendet (Konstanten unten,
# v19_2d_best-Fit aus value_calibration_fit.json "full"); Dateien von
# WDL-Generatoren (Prefix-Liste) blenden den nativen [0,1]-Bootstrap roh.
# train.py's `--wdl-bootstrap-destretch` ist damit fuer Schema>=17-Caches
# UEBERFLUESSIG und darf NICHT zusaetzlich gesetzt werden (doppelte
# Streckung); der Flag bleibt nur fuer Alt-Experimente auf Schema-16.
# Schema 18 (2026-08-07, PREREG_plate_intervention.md): additive Felder
# `endgame_margin`/`endgame_mask` (ENDGAME_CACHE_FIELDS unten) -- exakter
# R5-Minimax-Wurzelwert aus den Records (root_q der R5-Drafting-Schritte,
# [0,1]-tanh-Normierung, net_mcts.rs-R5-Zweig). Labels sind GRATIS (kein
# Solver-Lauf beim Cache-Bau); Zustaende ohne root_q bzw. ausserhalb der
# R5-Drafting-Zone tragen Maske 0 (v16/v17-Dateien komplett).
# Schema 19 (2026-08-08, Task #35b, "Ranking-Loss auf Geschwister-Q"):
# additive Felder `ranking_action_ids`/`ranking_child_q`/`ranking_mask`
# (RANKING_CACHE_FIELDS unten) -- Top-K Geschwister-(Aktion,Q)-Paare fuer
# den paarweisen Policy-Ranking-Loss in train.py (`--ranking-loss-weight`,
# Default 0.0 = AUS). Quelle ist das additive `root_child_q`-JSON-Feld
# (Engine-Teil von Task #35, self_play.rs/net_mcts.rs, seit Commit-Historie
# Default AN) -- NUR vorhanden bei echter Mehr-Aktionen-Suche, GLEICHE
# Reihenfolge/Laenge wie `step["policy"]` (self_play.rs-Vertrag). Labels
# sind GRATIS wie bei Schema 18 (kein zusaetzlicher Solver-/Suchlauf beim
# Cache-Bau). v16/v17/Ein-Aktion-Zuege und Zuege mit `pol_w==0` (Tiling/
# Start-Schritte ODER `policy_target_valid=False`, siehe pol_w-Kommentar im
# Baucode unten) tragen Maske 0.
VALUE_SCHEMA_VERSION = 20
# Namenskonvention: Dateien heissen nach dem GENERATOR (v19-Aera-Modell
# t34_wdldestretch_brierbest -> "v19wdl"), NICHT nach der Ziel-Generation
# (Koordinator-Fehler #2 mit dieser Konvention, vom Nutzer 2026-08-06
# gefangen -- BEVOR falsch entstaucht wurde). Kuenftige WDL-Generatoren
# ergaenzen ihre Praefixe hier.
WDL_GENERATOR_PREFIXES = ("selfplay_v19wdl", "selfplay_v20wdl")
DESTRETCH_A = 0.0051
DESTRETCH_B = 1.9269








VALUE_OPP_EPSILON = 0.0  # inert seit Schema 20, siehe Kommentar oben
VALUE_SCALE = 50.0
# Mischgewicht fuer `bootstrap_value` (Punkt 6) -- 0.0 = nur bisheriges Ziel
# (Endergebnis bzw. rtv-Override), 1.0 = nur der kurze Bootstrap-Horizont.
# 0.5 als erster, ungetesteter Startwert (gleichgewichtiger Blend) -- noch
# keine Arena-/R²-Validierung, bei Bedarf anpassen.
TD_LAMBDA = 0.5

# λ-Misch-Value-Target-Experiment (Willemsen et al. 2021, "soft-Z" --
# Varianzreduktion des HAUPT-Value-Targets durch Mischen mit dem
# Root-Suchwert). Seit Commit 2718b9a tragen Self-Play-Records optional das
# Feld "root_q" ([0,1]-Skala, wie `rtv`) -- der aggregierte Root-Q-Wert der
# waehrend des Zugs tatsaechlich durchgefuehrten Suche (net_mcts.rs /
# self_play.rs), NUR vorhanden bei echter Mehr-Aktionen-Suche (fehlt beim
# Ein-Aktion-Kurzschluss und bei aelteren Dateien ohne dieses Feld, z.B.
# v16/v17). ABGRENZUNG zu `rtv`/`bootstrap_value` oben: jene ERSETZEN das
# Value-Target VOR dem Caching (Teil der `val`/`points_val`-Formel, daher im
# `VALUE_SCHEMA_VERSION`/Cache-Key gebunden) -- `root_q` wird dagegen NUR
# roh (remapped auf [-1,1] wie `rtv`, `*2.0-1.0`) + eine Praesenz-Maske in
# den Cache geschrieben, OHNE `values`/`points_forecast` zu veraendern. Der
# eigentliche λ-Mix (`target = λ·z + (1-λ)·root_q`) passiert ERST in
# `train.py` (Flag `--value-target-lambda`, `apply_value_target_lambda()`
# unten) -- so kann derselbe HDF5-Cache fuer beliebig viele λ-Werte im Sweep
# wiederverwendet werden, statt fuer jeden λ-Arm neu gebaut werden zu
# muessen (waere bei ~1,3 Mio. Samples/Sweep-Arm unnoetig teuer).
#
# CACHE-VERSIONIERUNG (bewusste Entscheidung, WEICHT vom `rounds`/`ownership`-
# Praezedenzfall ab): `root_q`/`root_q_mask` haengen NICHT im `cache_key`
# (kein neuer Suffix-Marker wie "+rounds_v1"). Grund: ein Marker wuerde jeden
# BESTEHENDEN Cache (auch fuer Dateien OHNE root_q, z.B. reine v16/v17-Korpora)
# einmalig zwingend neu bauen -- unnoetig teuer, wenn root_q dort ohnehin nur
# ueberall Maske=0 waere. Stattdessen rein additiv wie `policy_weights`/
# `points_forecast`: ein Alt-Cache OHNE 'root_q'-Dataset laedt weiterhin
# unveraendert (Fallback unten: Wert 0.0, Maske komplett 0 -- identisch zu
# `value_target_lambda=1.0`, dem Standardverhalten). Ein FRISCH gebauter
# Cache (neue Dateiliste, kein bestehender Treffer) enthaelt automatisch die
# echten root_q-Werte der zugrundeliegenden Dateien, weil der Baucode unten
# geaendert wurde -- ohne dass sich am `values`/`points_forecast`-Inhalt
# selbst irgendetwas aendert (der λ-Mix ist eine reine train.py-Nachbearbeitung).
ROOT_Q_CACHE_FIELDS = ("root_q", "root_q_mask")

# Task #28 (evaluations/PREREG_task28_aggression.md, "Minimal-invasiver
# Zuschnitt" Punkt 2): reine GEGNER-Punkteprognose als additives Aux-Ziel,
# NEBEN `points_forecast` (das bleibt unveraendert, epsilon-Ziel fuer den
# eigenen Punkte-Kopf). Genau wie `root_q` NICHT im `cache_key` -- ein
# Alt-Cache ohne dieses Dataset laedt unveraendert weiter, Fallback unten ist
# Wert 0.0 + Maske 0.0 (der opp-Loss in train.py wird dann fuer diese Samples
# einfach maskiert, kein erfundener Zielwert). Wird mit EXAKT derselben
# Blending-Struktur wie der own-seitige Term INNERHALB von `points_val`
# konstruiert (Basis tanh(opp_total/VALUE_SCALE), rtv-Zweig opp_rtv,
# TD-Bootstrap-Blend mit opp_bootstrap) -- NUR dadurch gilt die algebraische
# Rueckgewinnung `own_pts = points_pred + VALUE_OPP_EPSILON*opp_pred` exakt
# galt -- ab Schema 20 ist sie GEGENSTANDSLOS, weil `points_forecast` rein own
# ist (VALUE_OPP_EPSILON = 0). Die Spiegelung der Blending-Struktur bleibt
# trotzdem richtig: sie macht `opp_points_forecast` mit `points_forecast`
# vergleichbar.
OPP_POINTS_CACHE_FIELDS = ("opp_points_forecast", "opp_points_mask")

# Task #34 (STATUS.md "Sieg/Niederlage-Ziel wiederherstellen"): additive
# Cache-Felder fuers WDL-Ziel (siehe VALUE_SCHEMA_VERSION=16-Kommentar oben
# fuer die Herleitung) -- immer mitgebaut, unabhaengig davon, ob ein Lauf
# `--value-head wdl` nutzt (analog zu `points_forecast`, das auch immer
# gebaut wird, egal ob POINTS_WEIGHT>0).
WDL_CACHE_FIELDS = ("values_wdl", "wdl_outcome")

# Schema 18 (PREREG_plate_intervention.md): exakte R5-Zonen-Ziele fuer den
# additiven `endgame_head` -- immer mitgebaut (Muster points_forecast/WDL).
ENDGAME_CACHE_FIELDS = ("endgame_margin", "endgame_mask")

# Schema 19 (Task #35b, "Ranking-Loss auf Geschwister-Q", Research-Report
# Idee 7.1): additive Cache-Felder fuer den paarweisen Policy-Ranking-Loss
# in train.py (`--ranking-loss-weight`, Default 0.0 = AUS -> Feld existiert,
# wird aber nirgends gelesen, gleiches "immer mitgebaut"-Muster wie
# WDL_CACHE_FIELDS/ENDGAME_CACHE_FIELDS).
#
# FELD-DESIGN (Cache-Feld-Entscheidung, siehe Baucode unten fuer die
# Extraktion): `root_child_q` (JSON, engine-seitig) ist ein Roh-Array je
# Zug MIT VARIABLER LAENGE -- Korpus-Stichprobe (v19wdlann, 2026-08-08)
# zeigt 2 bis >300 Geschwister je Drafting-Entscheidung (frueher/breiter
# Zug = mehr Kandidaten). Ein festes Padding auf die ROHE Maximallaenge
# waere extrem RAM-ineffizient (>300 Slots fuer die grosse Mehrheit
# leer) -- stattdessen RANKING_TOPK=8 Paare je Zustand:
#   - `ranking_action_ids` : int16, Shape (N, RANKING_TOPK), Sentinel -1
#                            fuer nicht belegte Slots (Alt-Cache-Faellback/
#                            <8 Geschwister). int16 reicht komfortabel
#                            (NUM_ACTIONS=406 << 32767).
#   - `ranking_child_q`    : float16, Shape (N, RANKING_TOPK), [0,1]-Skala
#                            wie `root_q` (KEIN Remap auf [-1,1] -- die
#                            Ranking-Paarbildung in train.py braucht nur
#                            Differenzen/Vorzeichen, die Skala ist egal;
#                            float16 spart Speicher, Quantisierungsfehler
#                            ~4e-4 relativ ist fuer den |dq|>Margin-Filter
#                            irrelevant, gleiche Kompromiss-Klasse wie
#                            `states`/`policies` oben).
#   - `ranking_mask`       : float32, Shape (N,), 1.0 = Sample nutzbar
#                            (>=2 Geschwister vorhanden UND `pol_w>0` --
#                            deckt Tiling/Start-Schritte UND
#                            `policy_target_valid=False` ab, siehe
#                            pol_w-Kommentar im Baucode), sonst 0.0.
# AUSWAHL der 8 Paare bei >8 Geschwistern: die `RANKING_TOPK` Eintraege mit
# der GROESSTEN Abweichung vom Median-Q (`_ranking_topk_pairs` unten) --
# NICHT die ersten 8 in `root_child_q`-Reihenfolge (das ist die interne
# Sucheihenfolge, trägt keine Rang-Bedeutung). Die informativsten Paare
# fuer einen paarweisen Ranking-Loss sind die mit dem GROESSTEN Q-Abstand
# (klar unterscheidbare "besser/schlechter"-Paare, siehe |dq|>Margin-Filter
# in train.py) -- eine willkuerliche Erst-8-Auswahl wuerde bei hoher
# Verzweigung ueberwiegend nahezu identische Q-Werte treffen (kein Signal).
#
# SPEICHERBUDGET je Zustand (additiv, Bitpacking-Aera, siehe
# PREREG_v21_window.md "~2,6 KB/Zustand"): 8*int16 (16 B) + 8*float16
# (16 B) + 1*float32 (4 B) = 36 Byte/Zustand -- << 2% des bestehenden
# Gesamtbudgets, kein RAM-Vorbehalt.
#
# CACHE-VERSIONIERUNG: wie ENDGAME_CACHE_FIELDS ueber den
# VALUE_SCHEMA_VERSION=19-Bump erzwungen (kein separater Cache-Key-Suffix
# noetig) -- jeder Cache mit passendem Key wurde vom neuen Baucode
# geschrieben, der defensive Alt-Cache-Fallback unten (Maske komplett 0,
# IDs -1, Q 0.0) kann daher nur ueber den `.pt`-Legacy-Migrationspfad
# erreicht werden, gleiches Muster wie bei `values_wdl`/`endgame_margin`.
RANKING_TOPK = 8
RANKING_CACHE_FIELDS = ("ranking_action_ids", "ranking_child_q", "ranking_mask")



# Task #34: welcher Value-Kopf/welches Value-Ziel aktiv ist -- siehe
# `--value-head` in train.py. "tanh" (Standard) ist das BESTANDSVERHALTEN
# (Skalar-Regressionskopf auf `values`, MSE); "wdl" ist der neue
# 2-Logit-Softmax-Klassifikationskopf auf `values_wdl`, Kreuzentropie mit
# weichen Labels (siehe `MosaicNet`/`Mosaic2DNet`).
VALUE_HEAD_VARIANTS = ("tanh", "wdl")

# rtv-Ablation Phase 1 (Task #84, 2026-07-24): Trainings-Varianten, die den
# `round_transition_value`-Override beim Target-Bau ignorieren -- OHNE neues
# Self-Play, rein um zu testen, ob `rtv` (81% der Self-Play-Kosten, siehe
# #80/#81) im Value-Target ueberhaupt Staerke beitraegt.
#   "default"  : Bestandsverhalten, byte-identisch zu vor Task #84 (rtv wird
#                wie gehabt bevorzugt, wo vorhanden).
#   "nortv"    : rtv-Override komplett deaktiviert -- Value-Target faellt fuer
#                ALLE Schritte auf die tanh-Margin-Formel (own_total/opp_total)
#                zurueck, der TD-Bootstrap-Blend (Punkt 6) bleibt unveraendert
#                oben drauf.
#   "nortv_r1" : rtv-Override NUR fuer Runde-1-Zustaende deaktiviert (Teil-
#                ersparnis -- Runde 1 ist der teuerste rtv-Fall, siehe #80),
#                Runden 2-5 verhalten sich wie "default". Rundenzuordnung je
#                Record: `step["state"]["round"]`, dieselbe Quelle wie
#                `tools/offline_diagnosis.py::load_val_samples`.
VALUE_TARGET_VARIANTS = ("default", "nortv", "nortv_r1")

# Policy-Ziel-Schärfung (Experiment, 2026-07-19): die rohen MCTS-Visit-Anteile
# (`step["policy"]`s `prob`-Werte, Heuristik-Selfplay) sind selbst oft recht
# flach (Stone-only-Diagnose: Ø Max-Prob nur 0.503, 41.7% "sehr flach") --
# das gemessene Policy-Top-1 des trainierten Netzes (61.8%) liegt nah an
# dieser Ziel-eigenen Unschärfe, nicht klar darunter (siehe
# project_v8d_value_head_root_cause-Memory). Exponent >1 schärft die
# Ziel-Verteilung vor dem Training nach (p → p^k, renormiert), OHNE neues
# Self-Play zu brauchen -- reiner Trainings-Loss-Hebel auf dem bestehenden
# Korpus. 1.0 = unveraendert (bisheriges Verhalten).
POLICY_TARGET_SHARPEN_EXPONENT = 2.0


def _ownership_from_dome(dome_grid) -> list[int]:
    """36 Binaerlabels (3x3 Slots x 4 Felder) fuer EIN Spielerbrett: 1 = Feld
    ist belegt, 0 = leer. Reihenfolge slot_row-major, dann space_index -- fix
    und identisch zur Feature-Reihenfolge in `state_to_tensor`. Nicht
    existierende Slots (mid-game moeglich) zaehlen als 0; im ENDZUSTAND, aus
    dem das Ziel gebildet wird, sind empirisch alle 18 Slots belegt."""
    out: list[int] = []
    for sr in range(3):
        row = dome_grid[sr] if sr < len(dome_grid) else []
        for sc in range(3):
            slot = row[sc] if sc < len(row) else None
            spaces = (slot or {}).get("spaces", []) if slot else []
            for si in range(4):
                sp = spaces[si] if si < len(spaces) else None
                out.append(1 if (sp and sp.get("filled") is not None) else 0)
    return out


def _dome_grids_from_dome(dome_grid):
    """(filled, colors) als je 6x6-Raster fuer EIN Spielerbrett.

    Positionsabbildung EXAKT wie `scoring.rs::build_grid` (Zeile 271):
    `grid[sr*2 + si//2][sc*2 + si%2]` -- die Kuppelplaettchen sind 2x2
    (`dome.rs`), 3x3 Slots x 4 Spaces = das 6x6-Gitter.

    `filled[r][c]`  = True, wenn das Feld belegt ist (Farbe ODER Spezialstein).
    `colors[r][c]`  = Farbstring, oder None bei leer/Spezialstein -- genau die
                      Regel aus `scoring.rs::row_unique_colors` (Zeile 302),
                      die `placed_special` ueberspringt und nur `placed_color`
                      zaehlt.
    """
    filled = [[False] * 6 for _ in range(6)]
    colors: list[list[str | None]] = [[None] * 6 for _ in range(6)]
    for sr in range(3):
        row = dome_grid[sr] if sr < len(dome_grid) else []
        for sc in range(3):
            slot = row[sc] if sc < len(row) else None
            if not slot:
                continue
            for si, sp in enumerate(slot.get("spaces", [])[:4]):
                val = sp.get("filled")
                if val is None:
                    continue
                r, c = sr * 2 + si // 2, sc * 2 + si % 2
                filled[r][c] = True
                if val != "special":
                    colors[r][c] = val
    return filled, colors


def _conjunctions_from_dome(dome_grid) -> list[int]:
    """34 Binaerlabels je Spielerbrett (GEPRUEFT gegen config.py:117
    CONJUNCTIONS_PER_PLAYER=34 UND die Index-Liste unten, die bis 25..33
    laeuft = 34 Eintraege; die fruehere Fassung dieses Docstrings sagte
    faelschlich 25 -- siehe PREREG_ownership_corpus.md §3.3) -- die
    KONJUNKTIVEN Wertungskriterien,
    die sich NICHT aus Feld-Randwahrscheinlichkeiten ableiten lassen
    (`P(alle 6 Felder)` ist nicht das Produkt der Einzelwahrscheinlichkeiten).

    Ergaenzt `_ownership_from_dome`, das mit seinen 36 Feldlabels bereits den
    Randlayer stellt -- und damit die ADDITIVEN Kriterien 4 (Randfelder, +1 je
    Feld) und 6 (Spezialfelder, -3 je leerem Feld) exakt abdeckt.

    Feste Reihenfolge (== Ausgabereihenfolge im erweiterten `ownership_head`):

        Index   Kriterium                        Punktwert   Quelle (scoring.rs)
         0.. 5  Reihe r vollstaendig                 +3      score_horizontal_rows
         6..11  Spalte c vollstaendig                +7      score_vertical_rows
        12..13  Diagonale d vollstaendig            +10      score_diagonal_rows
                (d=0: (i,i), d=1: (i,5-i))
        14..17  Eckplatte voll (alle 4 Spaces)   +3/+3/+8/+8  score_corner_tiles
                (Slots (0,0),(0,2),(2,0),(2,2))
        18      ALLE Jokerfelder belegt        2 x wild_total score_wild_fields
        19..24  Reihe r hat >=5 Farben               +4       score_colorful_rows
        25..33  Slot s traegt eine Jokerplatte    (Layout)      -> E[wild_total]

    Kriterium 7 (farbenreiche Reihen) kann NICHT aus `ownership` kommen: das
    Ziel dort ist belegt/leer ohne Farbe.

    Nicht existierende Slots zaehlen als unbelegt -- im ENDZUSTAND, aus dem
    das Ziel gebildet wird, sind empirisch alle Slots belegt (siehe
    `_ownership_from_dome`).
    """
    filled, colors = _dome_grids_from_dome(dome_grid)
    out: list[int] = []

    out += [int(all(filled[r][c] for c in range(6))) for r in range(6)]
    out += [int(all(filled[r][c] for r in range(6))) for c in range(6)]
    out.append(int(all(filled[i][i] for i in range(6))))
    out.append(int(all(filled[i][5 - i] for i in range(6))))

    # Eckplatten: alle 4 Spaces des Eckslots belegt -- im 6x6-Raster sind das
    # die 2x2-Bloecke bei (sr*2, sc*2). Reihenfolge wie `corner_fill`.
    for sr, sc in ((0, 0), (0, 2), (2, 0), (2, 2)):
        r0, c0 = sr * 2, sc * 2
        out.append(int(all(filled[r0 + dr][c0 + dc] for dr in (0, 1) for dc in (0, 1))))

    # Jokerfelder: Konjunktion ueber ALLE vorhandenen Wild-Spaces. Leere Menge
    # zahlt nicht aus (`score_wild_fields` gibt dann 0) -> Label 0.
    wild = [sp
            for sr in range(3) for sc in range(3)
            for sp in (((dome_grid[sr][sc] if sr < len(dome_grid) and sc < len(dome_grid[sr]) else None) or {})
                       .get("spaces", []))
            if sp.get("type") == "WILD"]
    out.append(int(bool(wild) and all(sp.get("filled") is not None for sp in wild)))

    out += [int(len({colors[r][c] for c in range(6) if colors[r][c] is not None}) >= 5)
            for r in range(6)]

    # 25..33 -- LAYOUT, keine Konjunktion: traegt Slot s am Ende eine Platte mit
    # Jokerfeld? Liefert ueber `E[wild_total] = Summe dieser Wahrscheinlichkeiten`
    # den Multiplikator von Kriterium 3 (`2 x wild_total`), das einzige Kriterium
    # mit zustandsabhaengigem Punktwert. Reihenfolge slot_row-major wie ueberall.
    for sr in range(3):
        row = dome_grid[sr] if sr < len(dome_grid) else []
        for sc in range(3):
            slot = row[sc] if sc < len(row) else None
            spaces = (slot or {}).get("spaces", []) if slot else []
            out.append(int(any(sp.get("type") == "WILD" for sp in spaces)))

    return out






# ENTPACK-STRATEGIE (Micro-Benchmark 2026-08-07, synthetisch, Batch=256,
# 200 Batches, 1 Thread -- echte Trainings-/Self-Play-Prozesse liefen
# parallel, Messung daher CPU-gedrosselt und konservativ):
#   baseline (heute, kein Packing, direkter uint8-Read):        ~0,72-0,86 s
#   (a) Entpacken PRO SAMPLE in __getitem__ (np.unpackbits/Sample):
#                                                                 ~1,48-1,82 s  (+70-110%)
#   (b1) Entpacken PRO BATCH, torch-Bit-Shift (nach Stack):      ~1,18-1,33 s  (+40-60%)
#   (b2) Entpacken PRO BATCH, EIN np.unpackbits-Aufruf auf den
#        gesamten Batch (NOCH VOR dem Device-Move):              ~0,48-0,52 s  (SCHNELLER als baseline!)
# Variante (a) verliert klar (256 einzelne Python/NumPy-Aufrufe je Batch).
# Variante (b2) gewinnt sogar gegen die heutige Baseline: das Stapeln vieler
# KLEINER gepackter Tensoren im DataLoader-`default_collate` (342/51 B je
# Sample) ist guenstiger als das Stapeln vieler GROSSER entpackter Tensoren
# (2.736/406 B je Sample), und EIN vektorisierter `np.unpackbits`-Aufruf ueber
# den ganzen Batch schlaegt den Mehraufwand des Entpackens. GEWAEHLTE
# VARIANTE: (b2) -- Entpacken einmal pro Batch in train.py, NOCH VOR dem
# `.to(device)`-Move (siehe `unpack_planes_batch`/`unpack_masks_batch` unten,
# Aufrufstellen in train.py). Ergebnis: 0% messbarer Overhead (eher ein
# kleiner Gewinn) statt der geforderten "hoechstens ~1-2%".
# Byte-Grenzen der gepackten Planes-Zeile (siehe NUM_BINARY_PLANES_CHANNELS):
#   [0 .. PLANES_PACKED_BINARY_BYTES)  = die 77 binaeren Kanaele, bitgepackt
#   [PLANES_PACKED_BINARY_BYTES .. )   = die wertetragenden Kanaele, ROH uint8
PLANES_BINARY_BITS = NUM_BINARY_PLANES_CHANNELS * 36          # 2772
PLANES_PACKED_BINARY_BYTES = (PLANES_BINARY_BITS + 7) // 8    # 347
PLANES_RAW_VALUE_BYTES = (NUM_PLANES_CHANNELS - NUM_BINARY_PLANES_CHANNELS) * 36  # 72
PLANES_PACKED_ROW_BYTES = PLANES_PACKED_BINARY_BYTES + PLANES_RAW_VALUE_BYTES     # 419


def unpack_planes_batch(packed: torch.Tensor) -> torch.Tensor:
    """Entpackt einen KOMPLETTEN Batch gepackter planes IN EINEM
    vektorisierten `np.unpackbits`-Aufruf (gewaehlte Variante b2, siehe
    Benchmark-Kommentar oben) -- NICHT pro Sample. `packed`:
    [B,PLANES_PACKED_ROW_BYTES] uint8 (CPU, NOCH VOR dem `.to(device)`-Move,
    siehe train.py) -> [B,NUM_PLANES_CHANNELS,6,6] uint8.

    ZWEITEILIG seit den Spezialfeld-Kanaelen: die ersten
    `NUM_BINARY_PLANES_CHANNELS` Kanaele sind bitgepackt (0/1), die restlichen
    tragen Werte > 1 und liegen ROH dahinter. Umkehrfunktion zu
    `corpus_dataset.py::_pack_planes` -- beide Seiten muessen dieselbe Grenze
    benutzen, sonst verschiebt sich der gesamte Kanalblock."""
    n = packed.shape[0]
    raw = packed.numpy()
    bits = np.unpackbits(raw[:, :PLANES_PACKED_BINARY_BYTES], axis=-1, count=PLANES_BINARY_BITS)
    if PLANES_RAW_VALUE_BYTES:
        flat = np.concatenate([bits, raw[:, PLANES_PACKED_BINARY_BYTES:]], axis=-1)
    else:
        flat = bits
    return torch.from_numpy(flat.reshape(n, NUM_PLANES_CHANNELS, 6, 6))


def unpack_masks_batch(packed: torch.Tensor) -> torch.Tensor:
    """Analog zu `unpack_planes_batch` fuer masks: [B,51] uint8 (CPU) ->
    [B,NUM_ACTIONS] uint8 (0/1)."""
    flat = np.unpackbits(packed.numpy(), axis=-1, count=NUM_ACTIONS)
    return torch.from_numpy(flat)






def points_dist_bins_from_state(state: dict) -> int:
    """Task #12: Bin-Zahl des Punkte-Kopfs AUS DEM CHECKPOINT ableiten.

    Der Verteilungs-Kopf (POINTS_DIST_BINS>0) hat eine andere Ausgabebreite als
    der Skalar-Kopf. Wer einen Checkpoint laedt, ohne das zu wissen, baut das
    falsche Modell und scheitert an einem Shape-Mismatch. Statt sich auf ein
    gespeichertes Feld zu verlassen (alte Checkpoints haben es nicht), wird die
    Zahl aus der Gewichtsform gelesen -- das funktioniert fuer JEDEN Checkpoint,
    auch rueckwirkend.

    Rueckgabe: 0 = Skalar-Kopf (Bestandsverhalten), sonst die Bin-Zahl.
    """
    w = state.get("points_head.2.weight")
    if w is None:
        return 0
    n = int(w.shape[0])
    return 0 if n <= 1 else n


def conjunction_head_present(state: dict) -> bool:
    """Traegt der Checkpoint die Konjunktions-Erweiterung des Ownership-Kopfs?

    Anders als `endgame_head_present` gibt es hier KEIN
    eigenes Modul, dessen Existenz man abfragen koennte -- die Konjunktionen
    haengen an derselben letzten Linear-Schicht wie der Randlayer. Erkannt wird
    daher an deren AUSGABEBREITE: `OWNERSHIP_TARGETS` = alt,
    `OWNERSHIP_TARGETS + CONJUNCTION_TARGETS` = erweitert.
    """
    w = state.get("ownership_head.2.weight")
    if w is None:
        return False
    return int(w.shape[0]) == OWNERSHIP_TARGETS + CONJUNCTION_TARGETS


def endgame_head_present(state: dict) -> bool:
    """Schema 18: Praesenz des additiven `endgame_head` AUS DEM CHECKPOINT
    ableiten -- identisches Muster wie `opp_points_head_present`."""
    return "endgame_head.0.weight" in state


def opp_points_head_present(state: dict) -> bool:
    """Task #28 (PREREG_task28_aggression.md): ob ein Checkpoint den additiven
    `opp_points_head` (reine Gegner-Punkteprognose) traegt -- AUS DEM
    STATE_DICT abgeleitet, dasselbe Muster wie `points_dist_bins_from_state`/
    `encoder_from_state_dict`. Alt-Checkpoints ohne den Kopf liefern False und
    bleiben dadurch OHNE ihn ladbar/exportierbar (Additiv-Regel: kein
    zufallsinitialisierter Kopf wird stillschweigend an ein Alt-Modell
    angehaengt)."""
    return "opp_points_head.0.weight" in state


def value_head_variant_from_state(state: dict) -> str:
    """Task #34: 'tanh' (Skalar-Regressionskopf, Bestandsverhalten) oder
    'wdl' (2-Logit-Softmax-Klassifikationskopf) AUS DEM CHECKPOINT ableiten --
    dasselbe Muster wie `points_dist_bins_from_state`/`opp_points_head_present`.
    `value_head.2.weight` ist bei 'tanh' der letzte Linear-Layer VOR `Tanh()`
    (Ausgabebreite 1); bei 'wdl' ist es der letzte Linear-Layer des Kopfes
    (Ausgabebreite 2, rohe Logits -- Softmax passiert erst in `forward`, siehe
    dortigen Kommentar). Alt-Checkpoints (kein solcher Key, oder Breite 1)
    liefern 'tanh' und bleiben dadurch unveraendert ladbar/exportierbar."""
    w = state.get("value_head.2.weight")
    if w is None:
        return "tanh"
    return "wdl" if int(w.shape[0]) == 2 else "tanh"


def encoder_from_state_dict(state: dict) -> str:
    """Task #11 Phase 2 (M2.1): 'flat' oder '2d' AUS DEM CHECKPOINT ableiten --
    dasselbe Muster wie `points_dist_bins_from_state`. Ein 2D-Checkpoint
    (`Mosaic2DNet`) hat einen `conv.0.weight`-Key (Conv-Zweig), ein
    Flach-Checkpoint (`MosaicNet`) nicht. Funktioniert rückwirkend für JEDEN
    Checkpoint, kein zusätzliches Manifest-Feld nötig -- das optionale
    `encoder`-Feld im `.pth`-Dict (siehe `train.py`) ist nur ein
    Bequemlichkeits-/Dokumentationswert, keine Voraussetzung."""
    return "2d" if "conv.0.weight" in state else "flat"


class MosaicNet(nn.Module):
    def __init__(self, input_size, num_actions=NUM_ACTIONS, hidden_size=HIDDEN_SIZE,
                 policy_hidden=256, value_hidden=64,
                 points_dist_bins=POINTS_DIST_BINS, opp_points_head=False, endgame_head=False,
                 conjunction_head=False,
                 value_head_variant="tanh"):
        super(MosaicNet, self).__init__()
        if value_head_variant not in VALUE_HEAD_VARIANTS:
            raise ValueError(
                f"Unbekannter value_head_variant={value_head_variant!r} -- "
                f"erlaubt: {VALUE_HEAD_VARIANTS}"
            )
        self.body = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.BatchNorm1d(hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.BatchNorm1d(hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU()
        )
        # Eigene Zwischenschicht für den Policy-Head (vorher: 1 nackter Linear-
        # Layer direkt auf den geteilten Trunk — im Gegensatz zu Value-/Moon-
        # Order-Head, die beide schon eine ReLU-Zwischenschicht hatten. Bei v5
        # blieb der Policy-Loss bei 33% des Max-Werts stehen, während der
        # Value-Loss exzellent konvergierte (siehe evaluations/v5_eval.md) —
        # die Kapazitätsanalyse zeigte einen gesunden, nicht gesättigten Trunk
        # (Dead-Ratio 4%, Eff.Rank ~41%), also lag die Asymmetrie näher am Head
        # selbst als am Trunk. Ab v7 relevant (v6 lief bereits mit dem alten,
        # einlagigen Head).
        # policy_hidden=0 rekonstruiert bewusst die ALTE, einlagige Architektur
        # (kein Linear→ReLU→Linear, sondern nackter Linear-Layer) — nötig, damit
        # export_onnx.py ältere Checkpoints (v1-v6) exakt mit ihren echten
        # trainierten Gewichten neu exportieren kann, statt den neuen Head mit
        # Zufallsgewichten aufzufüllen (das würde den Policy-Head stillschweigend
        # kaputt machen, siehe Vorfall bei v6).
        if policy_hidden and policy_hidden > 0:
            self.policy_head = nn.Sequential(
                nn.Linear(hidden_size, policy_hidden),
                nn.ReLU(),
                nn.Linear(policy_hidden, num_actions)
            )
        else:
            self.policy_head = nn.Sequential(
                nn.Linear(hidden_size, num_actions)
            )
        # Moon-Order Head: 5 Logits (eine pro Farbe)
        # Hoher Wert = Farbe tief im Stapel (defensiv versteckt)
        # Niedriger Wert = Farbe oben (weniger strategisch wichtig)
        # Nur aktiv/trainiert bei Sonnenzügen
        self.moon_order_head = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Linear(32, 5)   # 5 Farben: blau, gelb, rot, schwarz, türkis
        )
        # Value-Head: Sieg/Niederlage, klassisches AlphaZero-Ziel -- zurueck-
        # geholt, aber NICHT mehr fuer die Suche gedacht (Stufe 2 bleibt tot,
        # siehe evaluations/stage2_investigation.md), sondern als Trainings-
        # Zusatzsignal fuer den gemeinsamen Trunk.
        # Task #34 (VALUE_SCHEMA_VERSION=16-Kommentar oben): zwei Varianten --
        #   "tanh" (Standard, Bestandsverhalten byte-identisch): Skalar-
        #     Regressionskopf, Tanh-aktiviert, Ausgabe direkt in [-1,1].
        #   "wdl": 2 ROHE Logits (KEIN Tanh) -- `forward()` bildet daraus per
        #     Softmax P(Sieg) und gibt an DERSELBEN Position/Skala weiterhin
        #     `2*P(Sieg)-1` aus (siehe dortiger Kommentar). Dadurch bleibt
        #     `net_mcts.rs::value_to_win_prob` unveraendert kompatibel.
        self.value_head_variant = value_head_variant
        if self.value_head_variant == "wdl":
            self.value_head = nn.Sequential(
                nn.Linear(hidden_size, value_hidden),
                nn.ReLU(),
                nn.Linear(value_hidden, 2),   # rohe Logits [P(Niederlage), P(Sieg)]
            )
        else:
            self.value_head = nn.Sequential(
                nn.Linear(hidden_size, value_hidden),
                nn.ReLU(),
                nn.Linear(value_hidden, 1),
                nn.Tanh()
            )
        # Punktestand-Prognose-Head (Aux-Ziel): dieselbe tanh-gestauchte
        # Punktedifferenz-Formel, die frueher der einzige Value-Head war --
        # jetzt als separater, feinerer Regressions-Kopf NEBEN dem robusteren
        # Sieg/Niederlage-Ziel (siehe VALUE_SCHEMA_VERSION in neural_net.py).
        # Task #12: bei POINTS_DIST_BINS > 0 sagt dieser Kopf eine VERTEILUNG
        # ueber Bins der tanh-gestauchten Punktedifferenz vorher statt eines
        # Skalars. Nach aussen bleibt die Schnittstelle identisch -- `forward`
        # gibt an derselben Stelle weiterhin einen Skalar aus, naemlich den
        # ERWARTUNGSWERT der Verteilung. `net.rs` (out[0..3], positionsbasiert)
        # merkt davon nichts.
        self.points_dist_bins = int(points_dist_bins)
        if self.points_dist_bins > 0:
            self.points_head = nn.Sequential(
                nn.Linear(hidden_size, value_hidden),
                nn.ReLU(),
                nn.Linear(value_hidden, self.points_dist_bins),
            )
            # Bin-MITTEN ueber [-1, 1] (Wertebereich des tanh-Ziels).
            # Als Buffer registriert -> wandert mit .to(device) und landet im
            # state_dict, der Checkpoint ist damit selbstbeschreibend.
            edges = torch.linspace(-1.0, 1.0, self.points_dist_bins + 1)
            self.register_buffer("points_bin_edges", edges)
            self.register_buffer("points_bin_centers", (edges[:-1] + edges[1:]) / 2)
        else:
            self.points_head = nn.Sequential(
                nn.Linear(hidden_size, value_hidden),
                nn.ReLU(),
                nn.Linear(value_hidden, 1),
                nn.Tanh()
            )
        # Ownership-Head (Task #9): je Kuppelfeld binaer "am Spielende belegt?".
        # 72 Ausgaben = 2 Spieler x 3x3 Slots x 4 Felder, ego-perspektivisch
        # (erst der Spieler am Zug, dann der Gegner -- dieselbe Reihenfolge wie
        # in `state_to_tensor`). Rohe Logits, BCEWithLogits im Training.
        # BEWUSST ZULETZT deklariert: dadurch bleibt die Initialisierungs-
        # reihenfolge aller uebrigen Module unveraendert, ein Lauf mit
        # OWNERSHIP_WEIGHT=0.0 ist also byte-identisch zum Stand ohne Kopf.
        #
        # Konjunktions-Erweiterung (2026-08-10): die 25 konjunktiven Ziele je
        # Spieler haengen HINTEN an denselben Kopf an -- sie teilen sich die
        # 128er-Zwischenschicht mit dem Randlayer, weil die Konjunktion "alle 6
        # Felder dieser Reihe" auf genau den Feldern beruht, die der Randlayer
        # ohnehin schaetzt. Bei `conjunction_head=False` bleibt die Ausgabe-
        # breite exakt `OWNERSHIP_TARGETS`, also Bestandsverhalten und
        # unveraenderter ONNX-Vertrag.
        self.conjunction_head = bool(conjunction_head)
        self.ownership_head = nn.Sequential(
            nn.Linear(hidden_size, 128),
            nn.ReLU(),
            nn.Linear(128, OWNERSHIP_TARGETS + (CONJUNCTION_TARGETS if conjunction_head else 0)),
        )
        # opp_points_head (Task #28, PREREG_task28_aggression.md "Minimal-
        # invasiver Zuschnitt" Punkt 2): reine GEGNER-Punkteprognose, additiv,
        # standardmaessig AUS (`opp_points_head=False` -> Attribut existiert
        # gar nicht, Alt-Verhalten byte-identisch, kein Zufallsgewicht
        # irgendwo im Graphen). Gleiche Architektur wie der SKALARE Zweig von
        # `points_head` (bewusste Vereinfachung: der Verteilungs-Kopf aus
        # Task #12 wird hier NICHT gespiegelt -- POINTS_DIST_BINS ist per
        # Projektstandard 0/inert, siehe STATUS.md Task #12, eine Kombination
        # aus beiden Kopf-Arten ist kein aktueller Anwendungsfall). BEWUSST
        # NACH ownership_head deklariert (gleiches "zuletzt"-Muster) --
        # Initialisierungsreihenfolge aller uebrigen Module bleibt dadurch
        # unveraendert.
        self.has_opp_points_head = bool(opp_points_head)
        if self.has_opp_points_head:
            self.opp_points_head = nn.Sequential(
                nn.Linear(hidden_size, value_hidden),
                nn.ReLU(),
                nn.Linear(value_hidden, 1),
                nn.Tanh(),
            )
        # endgame_head (PREREG_plate_intervention.md, Schema 18): exaktes
        # R5-Zonen-Ziel (Minimax-Wurzelwert), additiv/standardmaessig AUS --
        # gleiches "zuletzt deklariert"-Muster und gleiche Architektur wie
        # opp_points_head. Tanh-Ausgang [-1,1]; das [0,1]-Cache-Ziel wird in
        # train.py per 2x-1 remapped. Reines Trainingssignal (Suche liest
        # den Kopf nicht).
        self.has_endgame_head = bool(endgame_head)
        if self.has_endgame_head:
            self.endgame_head = nn.Sequential(
                nn.Linear(hidden_size, value_hidden),
                nn.ReLU(),
                nn.Linear(value_hidden, 1),
                nn.Tanh(),
            )



    def forward(self, x):
        shared = self.body(x)
        pts_out = self.points_head(shared)
        pts_logits = None
        if self.points_dist_bins > 0:
            # Erwartungswert der Verteilung -> derselbe Skalar-Ausgang wie
            # vorher (Task #12). Die Logits gehen ZUSAETZLICH raus, damit das
            # Training die Kreuzentropie darauf rechnen kann.
            pts_logits = pts_out
            probs = torch.softmax(pts_logits, dim=-1)
            pts_out = (probs * self.points_bin_centers).sum(dim=-1, keepdim=True)
        # Task #34: "wdl"-Variante liefert 2 rohe Logits statt eines
        # Tanh-Skalars -- Softmax -> P(Sieg), dann auf DIESELBE [-1,1]-Position/
        # Skala wie der alte Tanh-Kopf zurueckprojiziert (`2*P(Sieg)-1`), damit
        # `net_mcts.rs::value_to_win_prob((v+1)/2)` unveraendert `P(Sieg)`
        # liefert -- KEINE Rust-Aenderung noetig. Die rohen Logits gehen
        # ZUSAETZLICH raus (analog zu `pts_logits`), damit train.py eine
        # numerisch stabile Kreuzentropie (BCEWithLogits auf der Logit-
        # Differenz) statt manuellem log(softmax) rechnen kann.
        value_raw = self.value_head(shared)
        value_wdl_logits = None
        if self.value_head_variant == "wdl":
            value_wdl_logits = value_raw
            p_win = torch.softmax(value_wdl_logits, dim=-1)[:, 1:2]
            value_out = 2.0 * p_win - 1.0
        else:
            value_out = value_raw
        # Reihenfolge = ONNX-Ausgabereihenfolge. `ownership` steht ZULETZT,
        # damit `net.rs`s positionsbasierte Indizes out[0..3] unveraendert
        # bleiben (Rust liest den Kopf nicht -- reines Trainingssignal).
        # `points_dist` haengt bei aktivem Task #12 NOCH dahinter -- gleiches
        # Muster, dieselbe Begruendung.
        out = (
            self.policy_head(shared),
            value_out,
            self.moon_order_head(shared),
            pts_out,
            self.ownership_head(shared),
        )
        if pts_logits is not None:
            out = out + (pts_logits,)
        # Task #34: `value_wdl_logits` haengt NACH `pts_logits`, aber VOR
        # `opp_points` -- `opp_points` muss der ZULETZT angehaengte Output
        # bleiben (Task #28, ONNX-Vertrag mit der Engine-Seite).
        if value_wdl_logits is not None:
            out = out + (value_wdl_logits,)
        # Task #28: `opp_points` haengt HINTER ALLEM -- ONNX-Vertrag mit der
        # Engine-Seite: "opp_points" ist der LETZTE Output, von Rust per NAME
        # (nicht Position) erkannt.
        if self.has_opp_points_head:
            out = out + (self.opp_points_head(shared),)
        # Schema 18: endgame haengt HINTER opp_points (additiv; Rust liest
        # per NAME bzw. ignoriert unbekannte Outputs -- Indizes 0..3 stabil).
        if self.has_endgame_head:
            out = out + (self.endgame_head(shared),)
        return out

    @torch.no_grad()
    def analyze_capacity(self, x):
        """
        Misst Netzauslastung über einen Batch:
        - Dead-Neuron-Ratio pro ReLU-Schicht (Neuronen die für ALLE Samples 0 sind)
        - Effective Rank der Aktivierungen (wie viele Dimensionen real genutzt werden)
        """
        self.eval()
        layer_out = []
        h = x
        for layer in self.body:
            h = layer(h)
            if isinstance(layer, nn.ReLU):
                layer_out.append(h.clone())

        results = {}
        for idx, a in enumerate(layer_out):
            n_neurons = a.shape[1]
            active_per_neuron = (a > 1e-6).any(dim=0)
            dead = (~active_per_neuron).sum().item()
            dead_ratio = dead / n_neurons
            active_rate = (a > 1e-6).float().mean().item()
            a_centered = a - a.mean(dim=0, keepdim=True)
            try:
                sv = torch.linalg.svdvals(a_centered)
                sv = sv[sv > 1e-10]
                if len(sv) > 0:
                    p = sv / sv.sum()
                    entropy = -(p * torch.log(p)).sum()
                    eff_rank = torch.exp(entropy).item()
                else:
                    eff_rank = 0.0
            except Exception:
                eff_rank = float('nan')
            results[f"layer{idx+1}"] = {
                "n_neurons":   n_neurons,
                "dead":        dead,
                "dead_ratio":  dead_ratio,
                "active_rate": active_rate,
                "eff_rank":    eff_rank,
                "rank_pct":    eff_rank / n_neurons if n_neurons else 0,
            }
        return results


class Mosaic2DNet(nn.Module):
    """2D-Encoder-Skelett (Task #11, Phase 1) -- Conv-Zweig auf
    `state_to_planes` [C,6,6] + Flach-Zweig auf `state_to_tensor` [input_size],
    späte Fusion, dann EXAKT dieselben Köpfe/Ausgabereihenfolge wie
    `MosaicNet` (policy, value, moon, points, ownership -- ownership zuletzt,
    optional `points_dist`-Logits danach bei `points_dist_bins>0`). Siehe
    docs/design_2d_encoder.md Abschnitt 5 für die Architektur-Begründung.

    ADDITIV: ersetzt `MosaicNet` nicht, ist ein separates, paralleles Modul.
    Kein Training in Phase 1 (Stopp-Linie) -- nur Architektur-Skelett für den
    Rust<->2D-ONNX-Roundtrip-Beweis (Teil C.2 des Auftrags).

    `x_flat` ist ABSICHTLICH optional (Default `None` -> Nullen): für den
    reinen Rust-Lade-/Eval-Beweis exportiert `torch.onnx.export` das Modell
    mit NUR `x_planes` als Graph-Input (Rang 4 `[batch,C,6,6]`) -- passend zu
    `Net::load_auto`s Rang-basierter Layout-Erkennung (Teil A), die für Phase
    1 bewusst EIN Input pro Modell voraussetzt (siehe design_2d_encoder.md
    Abschnitt 6, offene Frage 3: ein echter Zwei-Input-Export ist eine
    mögliche spätere Erweiterung, kein Phase-1-Ziel). Für ein künftiges
    Training (Phase 2) wird `x_flat` regulär mitgegeben.
    """

    def __init__(self, input_size, num_actions=NUM_ACTIONS, hidden_size=HIDDEN_SIZE,
                 policy_hidden=256, value_hidden=64, points_dist_bins=POINTS_DIST_BINS,
                 planes_channels=NUM_PLANES_CHANNELS, conv_channels=48, conv_layers=2,
                 opp_points_head=False, endgame_head=False,
                 conjunction_head=False,
                 value_head_variant="tanh"):
        super().__init__()
        if value_head_variant not in VALUE_HEAD_VARIANTS:
            raise ValueError(
                f"Unbekannter value_head_variant={value_head_variant!r} -- "
                f"erlaubt: {VALUE_HEAD_VARIANTS}"
            )
        self.input_size = input_size
        self.planes_channels = planes_channels

        # Conv-Zweig: 2-3 Lagen 3x3, 32-64 Kanäle (Vorschlag, siehe
        # design_2d_encoder.md Abschnitt 5) -- BatchNorm+ReLU analog zum
        # bestehenden `MosaicNet.body`. `padding=1` erhält die 6x6-Form über
        # alle Lagen (keine Downsample-Notwendigkeit bei so kleinem Brett).
        conv = []
        in_c = planes_channels
        for _ in range(conv_layers):
            conv += [
                nn.Conv2d(in_c, conv_channels, kernel_size=3, padding=1),
                nn.BatchNorm2d(conv_channels),
                nn.ReLU(),
            ]
            in_c = conv_channels
        self.conv = nn.Sequential(*conv)
        conv_flat_size = conv_channels * 6 * 6

        # Flach-Zweig: kleine Vorverarbeitung des nicht-räumlichen Rests
        # (Fabriken/Beutel/Chips/Scores/Musterreihen -- `state_to_tensor`
        # bleibt UNVERÄNDERT als Eingabequelle) auf eine feste Breite, bevor
        # beide Zweige fusioniert werden.
        self.flat_branch = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.BatchNorm1d(hidden_size),
            nn.ReLU(),
        )

        self.fusion = nn.Sequential(
            nn.Linear(conv_flat_size + hidden_size, hidden_size),
            nn.BatchNorm1d(hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
        )

        # Köpfe: BYTE-IDENTISCHE Struktur/Reihenfolge zu `MosaicNet` (siehe
        # Klassendoku dort) -- `net.rs` (out[0..3] positionsbasiert) behandelt
        # beide Modellfamilien gleich, ohne davon zu wissen.
        if policy_hidden and policy_hidden > 0:
            self.policy_head = nn.Sequential(
                nn.Linear(hidden_size, policy_hidden),
                nn.ReLU(),
                nn.Linear(policy_hidden, num_actions),
            )
        else:
            self.policy_head = nn.Sequential(nn.Linear(hidden_size, num_actions))

        self.moon_order_head = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Linear(32, 5),
        )

        # Task #34: siehe `MosaicNet`-Kommentar -- identische Logik/Begruendung,
        # BYTE-IDENTISCHE Architektur je Variante.
        self.value_head_variant = value_head_variant
        if self.value_head_variant == "wdl":
            self.value_head = nn.Sequential(
                nn.Linear(hidden_size, value_hidden),
                nn.ReLU(),
                nn.Linear(value_hidden, 2),
            )
        else:
            self.value_head = nn.Sequential(
                nn.Linear(hidden_size, value_hidden),
                nn.ReLU(),
                nn.Linear(value_hidden, 1),
                nn.Tanh(),
            )

        self.points_dist_bins = int(points_dist_bins)
        if self.points_dist_bins > 0:
            self.points_head = nn.Sequential(
                nn.Linear(hidden_size, value_hidden),
                nn.ReLU(),
                nn.Linear(value_hidden, self.points_dist_bins),
            )
            edges = torch.linspace(-1.0, 1.0, self.points_dist_bins + 1)
            self.register_buffer("points_bin_edges", edges)
            self.register_buffer("points_bin_centers", (edges[:-1] + edges[1:]) / 2)
        else:
            self.points_head = nn.Sequential(
                nn.Linear(hidden_size, value_hidden),
                nn.ReLU(),
                nn.Linear(value_hidden, 1),
                nn.Tanh(),
            )

        # Ownership-Head (72 Ausgaben, ego-perspektivisch) -- bewusst ZULETZT
        # deklariert, gleiches Muster wie `MosaicNet`. Konjunktions-Erweiterung
        # ebenfalls identisch: +CONJUNCTION_TARGETS hinten angehaengt, nur bei
        # gesetztem Flag (siehe `MosaicNet`-Kommentar fuer die Begruendung).
        self.conjunction_head = bool(conjunction_head)
        self.ownership_head = nn.Sequential(
            nn.Linear(hidden_size, 128),
            nn.ReLU(),
            nn.Linear(128, OWNERSHIP_TARGETS + (CONJUNCTION_TARGETS if conjunction_head else 0)),
        )

        # opp_points_head (Task #28) -- BYTE-IDENTISCHE Architektur/Begruendung
        # zu `MosaicNet` (siehe dortiger Kommentar), additiv/standardmaessig AUS.
        self.has_opp_points_head = bool(opp_points_head)
        if self.has_opp_points_head:
            self.opp_points_head = nn.Sequential(
                nn.Linear(hidden_size, value_hidden),
                nn.ReLU(),
                nn.Linear(value_hidden, 1),
                nn.Tanh(),
            )
        # endgame_head (PREREG_plate_intervention.md, Schema 18): exaktes
        # R5-Zonen-Ziel (Minimax-Wurzelwert), additiv/standardmaessig AUS --
        # gleiches "zuletzt deklariert"-Muster und gleiche Architektur wie
        # opp_points_head. Tanh-Ausgang [-1,1]; das [0,1]-Cache-Ziel wird in
        # train.py per 2x-1 remapped. Reines Trainingssignal (Suche liest
        # den Kopf nicht).
        self.has_endgame_head = bool(endgame_head)
        if self.has_endgame_head:
            self.endgame_head = nn.Sequential(
                nn.Linear(hidden_size, value_hidden),
                nn.ReLU(),
                nn.Linear(value_hidden, 1),
                nn.Tanh(),
            )


    def forward(self, x_planes, x_flat=None):
        if x_flat is None:
            x_flat = torch.zeros(
                x_planes.shape[0], self.input_size, dtype=x_planes.dtype, device=x_planes.device
            )
        c = self.conv(x_planes).flatten(1)
        f = self.flat_branch(x_flat)
        shared = self.fusion(torch.cat([c, f], dim=1))

        pts_out = self.points_head(shared)
        pts_logits = None
        if self.points_dist_bins > 0:
            pts_logits = pts_out
            probs = torch.softmax(pts_logits, dim=-1)
            pts_out = (probs * self.points_bin_centers).sum(dim=-1, keepdim=True)

        # Task #34: identische Logik zu `MosaicNet.forward` -- siehe dortiger
        # Kommentar fuer die vollstaendige Begruendung.
        value_raw = self.value_head(shared)
        value_wdl_logits = None
        if self.value_head_variant == "wdl":
            value_wdl_logits = value_raw
            p_win = torch.softmax(value_wdl_logits, dim=-1)[:, 1:2]
            value_out = 2.0 * p_win - 1.0
        else:
            value_out = value_raw

        # Reihenfolge = ONNX-Ausgabereihenfolge, identisch zu `MosaicNet.forward`.
        out = (
            self.policy_head(shared),
            value_out,
            self.moon_order_head(shared),
            pts_out,
            self.ownership_head(shared),
        )
        if pts_logits is not None:
            out = out + (pts_logits,)
        if value_wdl_logits is not None:
            out = out + (value_wdl_logits,)
        # Task #28: `opp_points` haengt HINTER ALLEM, identisches Muster zu
        # `MosaicNet.forward`.
        if self.has_opp_points_head:
            out = out + (self.opp_points_head(shared),)
        # Schema 18: endgame haengt HINTER opp_points (additiv; Rust liest
        # per NAME bzw. ignoriert unbekannte Outputs -- Indizes 0..3 stabil).
        if self.has_endgame_head:
            out = out + (self.endgame_head(shared),)
        return out


def build_model_from_checkpoint(ckpt: dict, input_size: int | None = None, num_actions: int = NUM_ACTIONS,
                                hidden_override: int | None = None):
    """Baut ein `MosaicNet` ODER `Mosaic2DNet` passend zu `ckpt` (ein bereits
    geladenes `.pth`-Dict) und lädt die Gewichte -- gemeinsame Stelle für
    `export_onnx.py`/`tools/offline_diagnosis.py`/`tools/oracle_metrics.py`,
    die vorher alle denselben `MosaicNet`-Konstruktionscode dupliziert hatten
    (Task #11 Phase 2, M2.1). `encoder` wird aus dem `state_dict` abgeleitet
    (`encoder_from_state_dict`), NICHT aus dem optionalen `ckpt["encoder"]` --
    funktioniert so auch für Checkpoints ohne dieses Feld (rückwirkend).

    Gibt `(model, encoder)` zurück, `encoder` in `{"flat", "2d"}`. Das Modell
    wird NICHT automatisch in `.eval()`-Modus versetzt -- das bleibt beim
    Aufrufer (unterschiedliche Konventionen in den bestehenden Skripten)."""
    state = ckpt["model_state"]
    encoder = encoder_from_state_dict(state)
    hs = hidden_override if hidden_override is not None else ckpt.get("hidden_size", HIDDEN_SIZE)
    bins = points_dist_bins_from_state(state)
    # Task #28: Praesenz des additiven opp_points_head AUS DEM CHECKPOINT
    # ableiten (gleiches Muster wie `bins`/`encoder` oben) -- ein Alt-
    # Checkpoint ohne diese Keys baut das Modell OHNE den Kopf, bleibt also
    # ladbar/exportierbar wie bisher.
    opp_head = opp_points_head_present(state)
    eg_head = endgame_head_present(state)
    # Konjunktions-Erweiterung des Ownership-Kopfs: an der AUSGABEBREITE der
    # letzten Linear-Schicht erkannt (kein eigenes Modul, siehe
    # `conjunction_head_present`). Alt-Checkpoints -> False -> Breite bleibt
    # `OWNERSHIP_TARGETS`, unveraendert ladbar/exportierbar.
    cj_head = conjunction_head_present(state)
    # Task #34: 'tanh' oder 'wdl' AUS DEM CHECKPOINT ableiten (gleiches Muster) --
    # ein Alt-Checkpoint (kein `value_head.2.weight` mit Breite 2) baut den
    # klassischen Tanh-Kopf, bleibt also unveraendert ladbar/exportierbar.
    value_head_variant = value_head_variant_from_state(state)
    if encoder == "2d":
        in_size = input_size if input_size is not None else state["flat_branch.0.weight"].shape[1]
        ph = state["policy_head.0.bias"].shape[0] if "policy_head.2.weight" in state else 0
        # Kanalzahl AUS DEM CHECKPOINT, nicht aus der globalen Konstante
        # (gleiches Muster wie `in_size` eine Zeile darueber und wie
        # `export_onnx.py:185`). Ohne diese Ableitung baute der Lader nach
        # jedem Kanal-Zuwachs ein zu breites Conv und `load_state_dict`
        # scheiterte an `size mismatch for conv.0.weight` -- ein
        # 77-Kanal-Checkpoint waere in Python schlagartig unladbar gewesen,
        # obwohl die Engine ihn ueber `split_planes_flat_batch_src` weiter
        # bitgleich bedient. Gefunden 2026-08-27 beim Schritt 77 -> 79.
        pc = state["conv.0.weight"].shape[1]
        model = Mosaic2DNet(input_size=in_size, num_actions=num_actions, hidden_size=hs,
                            planes_channels=pc,
                            policy_hidden=ph, points_dist_bins=bins, opp_points_head=opp_head,
                            endgame_head=eg_head,
                            conjunction_head=cj_head,
                            value_head_variant=value_head_variant)
    else:
        in_size = input_size if input_size is not None else state["body.0.weight"].shape[1]
        ph = state["policy_head.0.bias"].shape[0] if "policy_head.2.weight" in state else 0
        model = MosaicNet(input_size=in_size, num_actions=num_actions, hidden_size=hs,
                          policy_hidden=ph, points_dist_bins=bins, opp_points_head=opp_head,
                          endgame_head=eg_head,
                          conjunction_head=cj_head,
                          value_head_variant=value_head_variant)
    model.load_state_dict(state, strict=False)
    return model, encoder