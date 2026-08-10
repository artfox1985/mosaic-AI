import os
import glob
import re
import json
import math
import pickle
import statistics
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset
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
            
        # 6. Kuppelzustand (pro Spieler: 9 Slots × 9 Features = 81 Features × 2 = 162)
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
NUM_PLANES_CHANNELS = 2 * 16 + 19 + 25  # = 76


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
    [C,6,6], C=NUM_PLANES_CHANNELS=76. ADDITIV: `state_to_tensor` bleibt
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

    return torch.cat([board, raw_geom, gated], dim=0)  # [76,6,6]


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
#  in evaluations/PREREG_punktekopf_epsilon.md -- kurz: der Term war im
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
# Schema 18 (2026-08-07, PREREG_platten_intervention.md): additive Felder
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


def _destretch_prob(p: float) -> float:
    """Platt-Streckung einer gestauchten Alt-Kopf-'Wahrscheinlichkeit'."""
    p = min(max(p, 1e-6), 1.0 - 1e-6)
    z = math.log(p / (1.0 - p))
    return 1.0 / (1.0 + math.exp(-(DESTRETCH_A + DESTRETCH_B * z)))


def _is_policy_carrier(basename, carrier_set, carrier_prefixes, bootstrap_native):
    """Entscheidet, ob eine Self-Play-Datei Policy-Ziele traegt (pol_w>0-Vorfrage).

    Schema 17 (v20) hatte hier einen Kurzschluss: JEDE Datei eines
    WDL-Generators (`bootstrap_native`) trug automatisch Policy, egal ob sie
    im Manifest gelistet war -- fuer v20 harmlos (dort SOLLTEN alle
    v19wdl-Sockel-Dateien tragen), fuer v21 falsch (nur ein Teilsatz der
    v19wdl-Dateien soll Traeger sein). `bootstrap_native` bleibt fuer die
    Platt-Entstauchung (siehe Aufrufer, `not bootstrap_native`) unangetastet
    -- diese Funktion regelt NUR die Policy-Traeger-Frage.

    - `carrier_set is None` (kein Manifest gefunden): JEDE Datei traegt
      (Bestandsverhalten, manifest-unabhaengig).
    - `carrier_prefixes is None` (Manifest OHNE das neue Feld = v20-Schema):
      Alt-Verhalten EXAKT erhalten, inkl. `bootstrap_native`-Kurzschluss --
      Rueckwaerts-Kompatibilitaet/bit-identische v20-Caches sind Pflicht.
    - `carrier_prefixes` vorhanden (auch als leere Liste; v21+-Schema): der
      `bootstrap_native`-Kurzschluss wird NICHT mehr benutzt. Traeger ist nur,
      wer im `carrier_set` gelistet ist ODER dessen Basename mit einem der
      Praefixe beginnt (str.startswith -- "selfplay_v20wdl_" matcht NICHT
      "selfplay_v20wdlsw_...", der Unterstrich ist Teil des Praefixes).
    """
    if carrier_set is None:
        return True
    if carrier_prefixes is None:
        return bootstrap_native or basename in carrier_set
    return basename in carrier_set or basename.startswith(tuple(carrier_prefixes))


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

# Schema 18 (PREREG_platten_intervention.md): exakte R5-Zonen-Ziele fuer den
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
# PREREG_v21_fenster.md "~2,6 KB/Zustand"): 8*int16 (16 B) + 8*float16
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


def _ranking_topk_pairs(action_ids, qs, k):
    """Waehlt bis zu `k` (Aktions-ID, Q)-Paare aus `zip(action_ids, qs)` --
    bei <=k Paaren werden ALLE unveraendert (Original-Reihenfolge)
    uebernommen, bei >k Paaren die `k` mit der GROESSTEN Abweichung vom
    Median-Q (siehe RANKING_CACHE_FIELDS-Kommentar oben: das sind die
    informativsten Paare fuer den |dq|>Margin-Filter des Ranking-Loss,
    nicht die ersten `k` in Sucheihenfolge). Reine Hilfsfunktion, isoliert
    unit-testbar."""
    n = len(action_ids)
    if n <= k:
        return list(zip(action_ids, qs))
    median_q = statistics.median(qs)
    order = sorted(range(n), key=lambda i: abs(qs[i] - median_q), reverse=True)[:k]
    return [(action_ids[i], qs[i]) for i in order]

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
#                `tools/offline_diagnose.py::load_val_samples`.
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
    """25 Binaerlabels je Spielerbrett -- die KONJUNKTIVEN Wertungskriterien,
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

    return out


def _final_ownership_by_game(game_data) -> dict:
    """game_id -> (own_p0, own_p1, conj_p0, conj_p1) aus dem LETZTEN Record des
    Spiels. Das `dome_grid` aendert sich nach Abschluss der Tiling-Phase nicht
    mehr (Nachweis siehe tools/scoring_tile_impact.py), der letzte Record
    traegt also den finalen Kuppelzustand. Unvollstaendige Spiele -> None
    (Ziel wird dann als -1 markiert und im Loss maskiert).

    Die Konjunktionen (`_conjunctions_from_dome`) kommen aus demselben
    Endbrett und derselben `completed`-Pruefung -- sie werden IMMER berechnet;
    ob sie ins Ziel wandern, entscheidet `MosaicDataset.own_targets`."""
    last_by_gid = {}
    for step in game_data:
        last_by_gid[step["game_id"]] = step
    out = {}
    for gid, last in last_by_gid.items():
        if not last.get("completed"):
            out[gid] = None
            continue
        players = last["state"]["players"]
        out[gid] = (_ownership_from_dome(players[0]["dome_grid"]),
                    _ownership_from_dome(players[1]["dome_grid"]),
                    _conjunctions_from_dome(players[0]["dome_grid"]),
                    _conjunctions_from_dome(players[1]["dome_grid"]))
    return out


# ── Bitpacking planes/masks (RAM-Optimierung v21, 2026-08-07) ──────────────
# PREREG_v21_fenster.md, Abschnitt "RAM-Voraussetzung": das ~4,8-Mio-Zustaende-
# Fenster passt im heutigen Cache-Format (planes uint8 [76,6,6]=2.736 B,
# masks uint8 [406]=406 B) nicht mehr komfortabel in 32 GB RAM. Beide Felder
# sind STRIKT binaer (nur 0/1, siehe state_to_planes/mask-Bau oben) --
# np.packbits/np.unpackbits packt 8 Bits verlustfrei in 1 Byte.
#
# LAYOUT (exakt): pro Sample wird das Feld zuerst C-kontiguos auf 1D
# geflacht (planes [76,6,6] -> [2736], masks ist bereits 1D [406]),
# anschliessend `np.packbits(..., axis=-1)` -- NumPy-Standard-Bitreihenfolge
# 'big': Bit-Index 0 des flachen Arrays landet im HOECHSTWERTIGEN Bit (0x80)
# des ERSTEN Ausgabe-Bytes. planes: 2736 Bit / 8 = exakt 342 Byte (kein
# Padding). masks: 406 Bit / 8 = 50,75 -> 51 Byte (letztes Byte hat 2
# Padding-Nullbits). Entpacken mit `np.unpackbits(..., count=K)` schneidet
# das Padding exakt wieder ab -- `count` ist deshalb Pflichtparameter, kein
# optionales Detail.
def _pack_bits(arr: np.ndarray) -> np.ndarray:
    """Bitpackt ein striktes 0/1-uint8-Array entlang der letzten Achse.
    [..., K] -> [..., ceil(K/8)]. Siehe Kopf-Kommentar fuer das exakte
    Layout (Bitreihenfolge 'big', Padding-Konvention)."""
    return np.packbits(arr, axis=-1)


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
def unpack_planes_batch(packed: torch.Tensor) -> torch.Tensor:
    """Entpackt einen KOMPLETTEN Batch bitgepackter planes IN EINEM
    vektorisierten `np.unpackbits`-Aufruf (gewaehlte Variante b2, siehe
    Benchmark-Kommentar oben) -- NICHT pro Sample. `packed`: [B,342] uint8
    (CPU, NOCH VOR dem `.to(device)`-Move, siehe train.py) -> [B,76,6,6]
    uint8 (0/1), identisch zum unentpackten Bestandsformat vor der
    Bitpacking-Aenderung."""
    n = packed.shape[0]
    flat = np.unpackbits(packed.numpy(), axis=-1, count=NUM_PLANES_CHANNELS * 36)
    return torch.from_numpy(flat.reshape(n, NUM_PLANES_CHANNELS, 6, 6))


def unpack_masks_batch(packed: torch.Tensor) -> torch.Tensor:
    """Analog zu `unpack_planes_batch` fuer masks: [B,51] uint8 (CPU) ->
    [B,NUM_ACTIONS] uint8 (0/1)."""
    flat = np.unpackbits(packed.numpy(), axis=-1, count=NUM_ACTIONS)
    return torch.from_numpy(flat)


def _resolve_planes_h5_path(cache_path_h5: str) -> str:
    """DIAGNOSE-Override (2026-07-31, Task #11 Phase 2, fs_2d_s1-Absturz-
    Untersuchung): wenn `MOSAIC_PLANES_H5_DIR` gesetzt ist, wird der lazy
    Planes-HDF5-Handle (`MosaicDataset._open_planes_h5`) aus DIESEM Ordner
    statt aus `cache_path_h5`s eigentlichem Ordner geoeffnet (gleicher
    Dateiname, nur andere Directory) -- Ausschlusstest, ob ein
    stundenlang offen gehaltener h5py-Handle auf eine OneDrive-synchronisierte
    Datei (`data/` liegt unter OneDrive, siehe Memory
    "OneDrive-Dateiverschwinde-Vorfaelle") die stillen Abstuerze verursacht.
    Standardverhalten (Env-Var NICHT gesetzt) ist UNVERAENDERT: `cache_path_h5`
    selbst. NUR die Planes-Datei ist betroffen -- die uebrigen (Flach-)Felder
    bleiben auf dem regulaeren `data_dir`-Pfad, da nur der 2D-Pfad je
    abgestuerzt ist."""
    override_dir = os.environ.get("MOSAIC_PLANES_H5_DIR")
    if not override_dir:
        return cache_path_h5
    resolved = os.path.join(override_dir, os.path.basename(cache_path_h5))
    print(f"⚠️  DIAGNOSE-Override MOSAIC_PLANES_H5_DIR aktiv: Planes werden aus "
          f"'{resolved}' gelesen statt '{cache_path_h5}'.")
    return resolved


class MosaicDataset(Dataset):
    def __init__(self, data_dir="data", files=None, value_target_variant="default", encoder="flat",
                 conjunction_head=False):
        """`files`: optionale explizite Dateiliste (z.B. ein Train- oder
        Val-Split desselben `data_dir`) -- ohne Angabe werden wie bisher ALLE
        `*.pkl` im Ordner geladen. Der Cache-Key haengt von der tatsaechlich
        uebergebenen Liste ab, Train- und Val-Split bekommen also automatisch
        getrennte HDF5-Caches im selben Ordner.

        `value_target_variant`: siehe VALUE_TARGET_VARIANTS oben (Task #84,
        rtv-Ablation Phase 1) -- steuert, ob/wo der rtv-Override beim
        Target-Bau ignoriert wird. Standard "default" reproduziert exakt das
        Bestandsverhalten.

        `encoder`: Task #11 Phase 2. "flat" (Standard) ist bzgl. `states`/
        `policies`/etc. Bestandsverhalten -- ABER `masks` ist seit der
        Bitpacking-Aenderung (RAM-Optimierung v21, s.u.) NICHT mehr
        byte-identisch zum Vor-v21-Verhalten (Cache-Key/-Inhalt/
        `__getitem__`-Tupel-INHALT aendert sich; die Tupel-FORM/-POSITION
        bleibt gleich). "2d" ergaenzt ein zusaetzliches `planes`-HDF5-Dataset
        ([N,76,6,6], `neural_net.py::state_to_planes`) NEBEN den bestehenden
        Datasets -- der Cache-Key bekommt dafuer den Suffix "+enc2d_v1"
        (siehe docs/design_2d_encoder.md Abschnitt 7), ein Flach-Cache
        derselben Dateiliste bleibt davon unberuehrt (eigener Dateiname).
        Speicherformat uint8 (0/1) statt float32: JEDER der 76 Kanaele ist
        binaer (One-Hot-Belegung + 0/1-Geometriemasken, siehe
        design_2d_encoder.md Abschnitt 3/4).

        BITPACKING (RAM-Optimierung v21, 2026-08-07, PREREG_v21_fenster.md
        "RAM-Voraussetzung"): sowohl `masks` (406 Bit/Sample) als auch
        `planes` (2.736 Bit/Sample, NUR "2d") sind STANDARDMAESSIG bitgepackt
        im Cache (siehe `_pack_bits`-Kommentar oben fuer das exakte Layout;
        406 B -> 51 B bzw. 2.736 B -> 342 B). `__getitem__` liefert dann die
        GEPACKTEN Bytes (kuerzere letzte Dimension) statt der entpackten
        Werte -- das Entpacken passiert bewusst NICHT hier pro Sample,
        sondern EINMAL pro Batch in train.py (`unpack_masks_batch`/
        `unpack_planes_batch`, Benchmark-Begruendung dort), NOCH VOR dem
        Device-Move. `self.bitpacked` (bool, nach dem Laden/Bauen gesetzt)
        zeigt Aufrufern, ob dieser Schritt noetig ist. Escape-Hatch
        `MOSAIC_CACHE_NOPACK=1` erzwingt das alte unkomprimierte Format
        (eigener Cache-Key-Suffix, siehe dort) -- dann liefert `__getitem__`
        weiterhin die vollen [406]/[76,6,6]-Werte wie vor v21 und
        `self.bitpacked` ist False."""
        from config import INPUT_SIZE
        import hashlib, time
        import h5py

        if encoder not in ("flat", "2d"):
            raise ValueError(f"Unbekannter encoder={encoder!r} -- erlaubt: 'flat', '2d'")
        self.encoder = encoder
        # Zielbreite des `ownership`-Vektors: Randlayer, optional erweitert um
        # die konjunktiven Kriterien (siehe `_conjunctions_from_dome`). Ueberall
        # unten statt der nackten Konstante benutzt, damit beide Faelle
        # denselben Codepfad nehmen.
        self.conjunction_head = bool(conjunction_head)
        self.own_targets = OWNERSHIP_TARGETS + (CONJUNCTION_TARGETS if conjunction_head else 0)
        # Planes-Ladeverhalten (Task #11 Phase 2, Historie 2026-07-31):
        # STANDARD ist seit 2026-07-31 wieder komplett ins RAM (`_planes_eager_tensor`,
        # siehe `_maybe_load_planes_eager`) -- ein 30s-Vergleichsmesswert auf dem
        # echten 1,3-Mio-Sample-Cache zeigte lazy Pro-Index-h5py-Zugriffe als
        # ~400.000x langsamer (205ms/Sample vs. 0,5µs/Sample), was drei
        # vermeintliche "stille Abstuerze" beim ersten from-scratch-2D-Sweep
        # tatsaechlich erklaert (kein Crash, sondern ein Prozess, der bei
        # Batch=256 ~52s/Batch fuer reine Planes-I/O gebraucht haette und beim
        # Task-Management beendet wurde) -- KEIN Speicherproblem: die Maschine
        # hat 34,3 GB RAM, ein Planes-Split braucht ~3,6 GB. `MOSAIC_PLANES_LAZY=1`
        # schaltet den lazy Pro-Index-HDF5-Zugriff optional wieder ein --
        # NUR fuer echt knappe RAM-Verhaeltnisse gedacht (siehe
        # `_maybe_load_planes_eager`-Docstring fuer die Kosten-Abwaegung).
        self._planes_h5_path = None
        self._planes_h5_file = None
        self._planes_eager_tensor = None
        self._planes_dataset_name = None  # 'planes' oder 'planes_packed' (RAM-Optimierung v21)
        self.bitpacked = False  # True, sobald masks/planes gepackt geladen/gebaut werden (unten)

        if value_target_variant not in VALUE_TARGET_VARIANTS:
            raise ValueError(
                f"Unbekannte value_target_variant={value_target_variant!r} -- "
                f"erlaubt: {VALUE_TARGET_VARIANTS}"
            )

        # Cache-Datei basierend auf Dateiliste + INPUT_SIZE
        # TD_LAMBDA fehlte hier bisher im Hash (Retrain-Sweep-Audit,
        # 2026-07-22): der TD-Bootstrap-Blend wird in `val`/`points_val`
        # VOR dem Caching eingerechnet (siehe unten), ein Lambda-Sweep haette
        # also stillschweigend den Cache der ersten je Dateiliste gebauten
        # Lambda-Variante wiederverwendet und NICHTS gemessen. Jetzt Teil des
        # Keys, gleiche Stelle wie POLICY_TARGET_SHARPEN_EXPONENT.
        # value_target_variant (Task #84) genau dieselbe Falle: der rtv-
        # Override wird ebenfalls VOR dem Caching eingerechnet -- ohne diesen
        # String im Key wuerden "nortv"/"nortv_r1" stillschweigend den
        # "default"-Cache derselben Dateiliste wiederverwenden.
        files = sorted(files) if files is not None else sorted(glob.glob(os.path.join(data_dir, "*.pkl")))
        # MOSAIC_DATA_EXCLUDE (2026-08-07, Fenster-Pinning): Regex, der
        # Dateien VOR Key-Bildung und Training ausschliesst. Noetig, weil
        # data/ waehrend laufender Generierungen WAECHST (Vorfall: der
        # pi_ctrl_s3-Neustart glob-te frisch gelandete v19wdlann-Dateien
        # mit ein -> Cache-Voll-Neubau + kontaminiertes Kontroll-Fenster).
        # Der gefilterte Datei-Liste steckt via `str(files)` ohnehin im
        # Cache-Key -- gleicher Filter => gleicher Key => Cache-Hit.
        _excl = os.environ.get("MOSAIC_DATA_EXCLUDE")
        if _excl:
            _n0 = len(files)
            files = [f for f in files if not re.search(_excl, os.path.basename(f))]
            print(f"🔒 MOSAIC_DATA_EXCLUDE={_excl!r}: {_n0 - len(files)} von {_n0} Dateien ausgeschlossen.")
        # "+rounds_v1" (Task #15 B, 2026-07-28): der Cache fuehrt jetzt zusaetzlich
        # die Rundennummer je Sample mit (fuer rundenselektive Loss-Gewichtung,
        # z.B. --exclude-round5). Der Marker erzwingt einen einmaligen Rebuild
        # aller Alt-Caches, statt sie stillschweigend ohne das Feld zu laden.
        # "+enc2d_v1" (Task #11 Phase 2): NUR im 2D-Modus angehaengt, siehe
        # `encoder`-Doku oben -- der Flach-Modus-Key bleibt dadurch UNVERAENDERT,
        # bestehende Flach-Caches werden also nicht ungueltig.
        # Schema 17: Policy-Traeger-Manifest (v20-Zwei-Klassen-Fenster).
        # Fehlt die Datei -> None = Bestandsverhalten (alle Dateien tragen
        # Policy). Inhalt geht in den Cache-Key ein (anderer Traeger-Satz =
        # anderer Cache).
        # MOSAIC_CARRIER_MANIFEST (2026-08-08, v21-Uebergabe): Dateiname des
        # Traeger-Manifests, Default = v20-Bestand. Inhalt steckt via
        # policy_carrier_set ohnehin im Cache-Key.
        # `carrier_prefixes` (2026-08-08, v21-Fix): additives, OPTIONALES
        # Manifest-Feld -- Liste von Dateinamen-Praefixen, die (zusaetzlich
        # zum `policy_carrier_set`) als Traeger gelten. Ist das Feld
        # VORHANDEN (auch als leere Liste), schaltet `_is_policy_carrier`
        # den `bootstrap_native`-Kurzschluss ab (siehe Funktionskommentar
        # dort) -- notwendig, weil der Kurzschluss fuer v21 ALLE
        # `selfplay_v19wdl_*`-Dateien zu Traegern macht, obwohl nur ein
        # seed-bestimmter Teilsatz tragen soll. Fehlt das Feld (v20-Manifest,
        # kein Rebuild-Zwang): None -> Alt-Verhalten EXAKT erhalten.
        manifest_path = os.path.join(
            data_dir,
            os.environ.get("MOSAIC_CARRIER_MANIFEST", "policy_carrier_manifest_v20.json"))
        policy_carrier_set = None
        carrier_prefixes = None
        if os.path.exists(manifest_path):
            with open(manifest_path, encoding="utf-8") as mf:
                _manifest = json.load(mf)
                policy_carrier_set = frozenset(_manifest["policy_carrier_files"])
                if "carrier_prefixes" in _manifest:
                    carrier_prefixes = list(_manifest["carrier_prefixes"])

        cache_key_material = (
            str(files) + str(INPUT_SIZE) + str(NUM_ACTIONS) + str(VALUE_SCHEMA_VERSION)
            + str(POLICY_TARGET_SHARPEN_EXPONENT) + str(TD_LAMBDA) + str(value_target_variant)
            + "+rounds_v1+own_v1"
        )
        if policy_carrier_set is not None:
            cache_key_material += "+carriers:" + ",".join(sorted(policy_carrier_set))
        if carrier_prefixes is not None:
            # Eigene Komponente (nicht Teil von "+carriers:"): sonst wuerden
            # zwei Manifeste mit identischem policy_carrier_set aber
            # unterschiedlichen carrier_prefixes denselben Cache treffen
            # (Fenster-Kollision, siehe Auftrag Punkt 3).
            cache_key_material += "+carrier_prefixes:" + ",".join(sorted(carrier_prefixes))
        if encoder == "2d":
            cache_key_material += "+enc2d_v1"
        # Konjunktions-Erweiterung (2026-08-10): die 25 Zusatzlabels je Spieler
        # haengen HINTEN an den `ownership`-Vektor. Eigener Suffix, NUR wenn
        # aktiv -- Muster "+enc2d_v1". Bewusst KEIN VALUE_SCHEMA_VERSION-Bump:
        # die Konjunktionen sind ein optionales Zusatzfeld, ein Bump wuerde den
        # vorhandenen v21-Cache ohne Not entwerten. Der Suffix verhindert
        # zugleich das stille Wiederverwenden eines Alt-Caches, dessen
        # `ownership`-Dataset nur OWNERSHIP_TARGETS breit ist (das Ziel waere
        # dann vollstaendig maskiert und der Kopf lernte nichts -- ohne
        # Fehlermeldung).
        if conjunction_head:
            cache_key_material += "+conj_v1"
        # Bitpacking (RAM-Optimierung v21, PREREG_v21_fenster.md "RAM-
        # Voraussetzung"): planes/masks werden ab jetzt STANDARDMAESSIG
        # bitgepackt gespeichert (siehe `_pack_bits`-Kommentar oben) --
        # eigener Suffix erzwingt einen Rebuild ALLER Alt-Caches (flat UND
        # 2d, masks sind in beiden Modi betroffen), kein stilles
        # Fehlinterpretieren des alten unkomprimierten Formats. Escape-Hatch
        # MOSAIC_CACHE_NOPACK=1 (Muster wie MOSAIC_CACHE_F32) erzwingt exakt
        # das alte Format -- eigener Suffix, damit die beiden Formate nie
        # denselben Cache-Key treffen (falls die Bitpack-Validierung mal
        # durchfaellt und zurueckgeschaltet werden muss).
        cache_nopack = os.environ.get("MOSAIC_CACHE_NOPACK") == "1"
        cache_key_material += "+nopack_v1" if cache_nopack else "+bitpack_v1"
        cache_key = hashlib.md5(cache_key_material.encode()).hexdigest()[:12]
        cache_path_h5 = os.path.join(data_dir, f".cache_{cache_key}.h5")
        cache_path_pt = os.path.join(data_dir, f".cache_{cache_key}.pt")

        if os.path.exists(cache_path_h5):
            # HDF5 Cache laden — deutlich schneller als .pt
            print(f"📦 Lade HDF5-Cache ({len(files)} Dateien)...")
            t0 = time.time()
            with h5py.File(cache_path_h5, 'r') as hf:
                self.states             = torch.from_numpy(hf['states'][:])
                self.policies           = torch.from_numpy(hf['policies'][:])
                self.values             = torch.from_numpy(hf['values'][:])
                # Bitpacking (RAM-Optimierung v21): selbstbeschreibend ueber
                # den Dataset-Namen (nicht ueber den aktuellen Env-Var-Stand)
                # -- `self.bitpacked` steuert unten in `__getitem__`/train.py,
                # ob masks/planes noch gepackt sind (Entpacken passiert dann
                # EINMAL pro Batch, siehe `unpack_masks_batch`/
                # `unpack_planes_batch`). 'masks_packed' vorhanden <=> Cache
                # wurde OHNE MOSAIC_CACHE_NOPACK=1 gebaut.
                self.bitpacked = 'masks_packed' in hf
                if self.bitpacked:
                    self.masks = torch.from_numpy(hf['masks_packed'][:])  # [N,51] uint8, gepackt
                else:
                    self.masks = torch.from_numpy(hf['masks'][:])         # [N,406] uint8, Bestandsformat
                self.moon_order_targets = torch.from_numpy(hf['moon_order_targets'][:])
                if 'policy_weights' in hf:
                    self.policy_weights = torch.from_numpy(hf['policy_weights'][:])
                else:  # alter Cache ohne Gewicht → alle 1.0
                    self.policy_weights = torch.ones(len(self.states), dtype=torch.float32)
                if 'points_forecast' in hf:
                    self.points_forecast = torch.from_numpy(hf['points_forecast'][:])
                else:  # alter Cache ohne Aux-Ziel → 0.0 (wird durch VALUE_SCHEMA_VERSION eh selten erreicht)
                    self.points_forecast = torch.zeros_like(self.values)
                if 'rounds' in hf:
                    self.rounds = torch.from_numpy(hf['rounds'][:])
                else:  # kann durch den Schema-Marker im Cache-Key eigentlich nicht auftreten
                    self.rounds = torch.zeros(len(self.states), dtype=torch.int8)
                if 'ownership' in hf:
                    self.ownership = torch.from_numpy(hf['ownership'][:])
                else:
                    self.ownership = torch.full((len(self.states), self.own_targets), -1, dtype=torch.int8)
                if 'root_q' in hf:
                    self.root_q = torch.from_numpy(hf['root_q'][:])
                    self.root_q_mask = torch.from_numpy(hf['root_q_mask'][:])
                else:
                    # Alt-Cache ohne root_q (siehe ROOT_Q_CACHE_FIELDS-Kommentar
                    # oben) -- Maske komplett 0, identisch zu
                    # value_target_lambda=1.0 (Bestandsverhalten).
                    self.root_q = torch.zeros(len(self.states), dtype=torch.float32)
                    self.root_q_mask = torch.zeros(len(self.states), dtype=torch.float32)
                if 'opp_points_forecast' in hf:
                    self.opp_points_forecast = torch.from_numpy(hf['opp_points_forecast'][:])
                    self.opp_points_mask = torch.from_numpy(hf['opp_points_mask'][:])
                else:
                    # Alt-Cache ohne den Task-#28-Kopf (siehe
                    # OPP_POINTS_CACHE_FIELDS-Kommentar oben) -- Maske
                    # komplett 0, `values`/`points_forecast` bleiben unberuehrt.
                    self.opp_points_forecast = torch.zeros_like(self.values)
                    self.opp_points_mask = torch.zeros(len(self.states), dtype=torch.float32)
                if 'values_wdl' in hf:
                    self.values_wdl = torch.from_numpy(hf['values_wdl'][:])
                    self.wdl_outcome = torch.from_numpy(hf['wdl_outcome'][:])
                else:
                    # Task #34 (WDL_CACHE_FIELDS-Kommentar oben): kann durch
                    # den VALUE_SCHEMA_VERSION=16-Marker im Cache-Key
                    # eigentlich nicht auftreten (jeder Cache mit passendem
                    # Key wurde vom neuen Baucode geschrieben) -- defensiver
                    # Fallback trotzdem, gleiches Muster wie bei `rounds`.
                    # 0.5 = neutral/uninformativ (kein Ziel bekannt),
                    # -1.0 = "Ausgang unbekannt" (identisch zur Ownership-
                    # Konvention), NICHT 0.0 (das waere ein erfundenes
                    # "Niederlage"-Label).
                    self.values_wdl = torch.full_like(self.values, 0.5)
                    self.wdl_outcome = torch.full_like(self.values, -1.0)
                if 'endgame_margin' in hf:
                    self.endgame_margin = torch.from_numpy(hf['endgame_margin'][:])
                    self.endgame_mask = torch.from_numpy(hf['endgame_mask'][:])
                else:
                    # Schema 18 (ENDGAME_CACHE_FIELDS): defensiver Fallback
                    # wie bei values_wdl -- Maske komplett 0, Ziel neutral 0.5.
                    self.endgame_margin = torch.full_like(self.values, 0.5)
                    self.endgame_mask = torch.zeros(len(self.states), dtype=torch.float32)
                if 'ranking_action_ids' in hf:
                    self.ranking_action_ids = torch.from_numpy(hf['ranking_action_ids'][:])
                    self.ranking_child_q    = torch.from_numpy(hf['ranking_child_q'][:])
                    self.ranking_mask       = torch.from_numpy(hf['ranking_mask'][:])
                else:
                    # Schema 19 (RANKING_CACHE_FIELDS): defensiver Fallback,
                    # kann durch den VALUE_SCHEMA_VERSION=19-Marker im
                    # Cache-Key eigentlich nicht auftreten (gleiches Muster
                    # wie bei endgame_margin/values_wdl) -- Maske komplett 0,
                    # IDs -1 (kein belegter Slot), Q 0.0.
                    self.ranking_action_ids = torch.full((len(self.states), RANKING_TOPK), -1, dtype=torch.int16)
                    self.ranking_child_q    = torch.zeros((len(self.states), RANKING_TOPK), dtype=torch.float16)
                    self.ranking_mask       = torch.zeros(len(self.states), dtype=torch.float32)
                if self.encoder == "2d":
                    # Bitpacking (RAM-Optimierung v21): Dataset-Name
                    # selbstbeschreibend, unabhaengig vom `self.bitpacked`-
                    # Wert oben (der ueber `masks_packed` bestimmt wird) --
                    # beide werden zwar immer gemeinsam im selben Bauschritt
                    # geschrieben, die getrennte Pruefung ist defensiv gegen
                    # Cache-Korruption (klarer Fehler statt stillem Fallback).
                    if 'planes_packed' in hf:
                        self._planes_dataset_name = 'planes_packed'
                    elif 'planes' in hf:
                        self._planes_dataset_name = 'planes'
                    else:
                        raise RuntimeError(
                            f"HDF5-Cache {cache_path_h5} hat den '+enc2d_v1'-Key, aber weder "
                            f"'planes' noch 'planes_packed' -- Cache-Korruption? Datei loeschen "
                            f"und neu bauen lassen."
                        )
                    # RAM-Fix: NICHT `hf['planes...'][:]` (voller Einlese-Sog),
                    # nur den Pfad merken -- `_open_planes_h5` oeffnet lazy
                    # einen eigenen, separaten Handle (dieser `with`-Block
                    # schliesst `hf` gleich).
                    self._planes_h5_path = _resolve_planes_h5_path(cache_path_h5)
                else:
                    self._planes_h5_path = None
                    self._planes_dataset_name = None
            print(f"Datensatz geladen: {len(self.states)} Züge. "
                  f"(Features pro Zug: {self.states.shape[1]}) — {time.time()-t0:.1f}s")

        elif os.path.exists(cache_path_pt):
            # Alten .pt Cache laden und nach HDF5 migrieren -- kann fuer
            # encoder="2d" praktisch nie greifen (der "+enc2d_v1"-Key-Suffix
            # existiert erst seit Task #11 Phase 2, ein .pt-Cache mit diesem
            # Key kann also nicht vorliegen), aber defensiv statt eines
            # stillen `planes=None` trotzdem hart pruefen.
            if self.encoder == "2d":
                raise RuntimeError(
                    f"Alter .pt-Cache {cache_path_pt} passt zum '+enc2d_v1'-Key -- das kann "
                    f"eigentlich nicht vorkommen (der Suffix ist neuer als jeder .pt-Cache). "
                    f"Cache-Datei loeschen und neu bauen lassen."
                )
            print(f"📦 Migriere .pt → HDF5 Cache...")
            t0 = time.time()
            bundle = torch.load(cache_path_pt, weights_only=False)
            self.states             = bundle["states"] if isinstance(bundle["states"], torch.Tensor) else torch.stack(bundle["states"])
            self.policies           = bundle["policies"] if isinstance(bundle["policies"], torch.Tensor) else torch.stack(bundle["policies"])
            self.values             = bundle["values"] if isinstance(bundle["values"], torch.Tensor) else torch.stack(bundle["values"])
            self.masks              = bundle["masks"] if isinstance(bundle["masks"], torch.Tensor) else torch.stack(bundle["masks"])
            mot = bundle.get("moon_order_targets")
            if mot is None:
                mot = [torch.full((5,), -1.0) for _ in self.states]
            self.moon_order_targets = mot if isinstance(mot, torch.Tensor) else torch.stack(mot)
            self.policy_weights = torch.ones(len(self.states), dtype=torch.float32)  # Legacy → 1.0
            self.points_forecast = torch.zeros_like(self.values)  # Legacy .pt kennt kein Aux-Ziel
            self.rounds = torch.zeros(len(self.states), dtype=torch.int8)  # Legacy .pt kennt keine Runden
            self.ownership = torch.full((len(self.states), self.own_targets), -1, dtype=torch.int8)
            # Legacy .pt stammt aus einer Aera lange vor root_q (Commit
            # 2718b9a) -- Maske komplett 0, siehe ROOT_Q_CACHE_FIELDS-Kommentar.
            self.root_q = torch.zeros(len(self.states), dtype=torch.float32)
            self.root_q_mask = torch.zeros(len(self.states), dtype=torch.float32)
            # Legacy .pt kennt auch keinen Task-#28-Kopf -- gleiches
            # Fallback-Muster wie root_q oben.
            self.opp_points_forecast = torch.zeros_like(self.values)
            self.opp_points_mask = torch.zeros(len(self.states), dtype=torch.float32)
            # Legacy .pt stammt lange vor Schema 18 -- gleiches Muster.
            self.endgame_margin = torch.full_like(self.values, 0.5)
            self.endgame_mask = torch.zeros(len(self.states), dtype=torch.float32)
            # Legacy .pt stammt lange vor Task #34 -- gleiches Fallback-Muster
            # wie root_q/opp_points oben (siehe WDL_CACHE_FIELDS-Kommentar).
            self.values_wdl = torch.full_like(self.values, 0.5)
            self.wdl_outcome = torch.full_like(self.values, -1.0)
            # Legacy .pt stammt lange vor Schema 19 -- gleiches Fallback-
            # Muster wie endgame_margin oben (siehe RANKING_CACHE_FIELDS-
            # Kommentar): Maske komplett 0, IDs -1, Q 0.0.
            self.ranking_action_ids = torch.full((len(self.states), RANKING_TOPK), -1, dtype=torch.int16)
            self.ranking_child_q    = torch.zeros((len(self.states), RANKING_TOPK), dtype=torch.float16)
            self.ranking_mask       = torch.zeros(len(self.states), dtype=torch.float32)
            # Als HDF5 speichern
            with h5py.File(cache_path_h5, 'w') as hf:
                hf.create_dataset('states',              data=self.states.numpy(),              compression='lzf')
                hf.create_dataset('policies',            data=self.policies.numpy(),            compression='lzf')
                hf.create_dataset('values',               data=self.values.numpy(),              compression='lzf')
                hf.create_dataset('masks',               data=self.masks.numpy(),               compression='lzf')
                hf.create_dataset('moon_order_targets',  data=self.moon_order_targets.numpy(),  compression='lzf')
                hf.create_dataset('policy_weights',      data=self.policy_weights.numpy(),      compression='lzf')
                hf.create_dataset('points_forecast',     data=self.points_forecast.numpy(),     compression='lzf')
                hf.create_dataset('rounds',              data=self.rounds.numpy(),              compression='lzf')
                hf.create_dataset('ownership',           data=self.ownership.numpy(),           compression='lzf')
                hf.create_dataset('root_q',              data=self.root_q.numpy(),              compression='lzf')
                hf.create_dataset('root_q_mask',         data=self.root_q_mask.numpy(),         compression='lzf')
                hf.create_dataset('opp_points_forecast', data=self.opp_points_forecast.numpy(), compression='lzf')
                hf.create_dataset('opp_points_mask',     data=self.opp_points_mask.numpy(),     compression='lzf')
                hf.create_dataset('values_wdl',          data=self.values_wdl.numpy(),          compression='lzf')
                hf.create_dataset('wdl_outcome',         data=self.wdl_outcome.numpy(),         compression='lzf')
                hf.create_dataset('endgame_margin',      data=self.endgame_margin.numpy(),      compression='lzf')
                hf.create_dataset('endgame_mask',        data=self.endgame_mask.numpy(),        compression='lzf')
                hf.create_dataset('ranking_action_ids',  data=self.ranking_action_ids.numpy(),  compression='lzf')
                hf.create_dataset('ranking_child_q',     data=self.ranking_child_q.numpy(),     compression='lzf')
                hf.create_dataset('ranking_mask',        data=self.ranking_mask.numpy(),        compression='lzf')
            os.remove(cache_path_pt)
            self._planes_h5_path = None  # kann hier nur "flat" sein, s.o. Guard
            print(f"Datensatz geladen + migriert: {len(self.states)} Züge. "
                  f"(Features pro Zug: {self.states.shape[1]}) — {time.time()-t0:.1f}s")

        else:
            print(f"Lade Daten aus {len(files)} Dateien...")
            t0 = time.time()
            _CIDX = {'blau':0,'gelb':1,'rot':2,'schwarz':3,'türkis':4}
            states_l, policies_l, values_l, masks_l, moon_l = [], [], [], [], []
            polw_l = []  # Policy-Loss-Gewicht je Sample (1=Drafting, 0=Tiling/Start)
            points_l = []  # Aux-Ziel: Punktestand-Prognose (siehe VALUE_SCHEMA_VERSION oben)
            rounds_l = []  # Rundennummer je Sample (Task #15 B: rundenselektive Loss-Gewichtung)
            own_l = []     # Ownership-Ziel je Sample (Task #9): 72 Binaerlabels, -1 = unbekannt
            root_q_l = []       # λ-Misch-Experiment: roher Root-Suchwert, remapped [-1,1]
            root_q_mask_l = []  # 1.0 = root_q vorhanden (echte Suche geloggt), sonst 0.0
            opp_points_l = []       # Task #28: reine Gegner-Punkteprognose (siehe OPP_POINTS_CACHE_FIELDS)
            opp_points_mask_l = []  # 1.0 = echter Wert (scores/winner vorhanden), sonst 0.0
            endgame_l = []       # Schema 18: exakter R5-Wurzelwert [0,1] (ENDGAME_CACHE_FIELDS)
            endgame_mask_l = []  # 1.0 = R5-Drafting mit root_q, sonst 0.0
            ranking_ids_l = []   # Schema 19: Top-K Geschwister-Aktions-IDs (RANKING_CACHE_FIELDS)
            ranking_q_l = []     # Schema 19: zugehoerige Q-Werte, [0,1], fp16
            ranking_mask_l = []  # Schema 19: 1.0 = Geschwister-Set vorhanden UND pol_w>0
            value_wdl_l = []    # Task #34: Gewinnwahrscheinlichkeit [0,1] (siehe WDL_CACHE_FIELDS)
            wdl_outcome_l = []  # Task #34: roher Spielausgang 0.0/1.0, -1.0 = unbekannt
            # Task #11 Phase 2: Planes-Puffer NUR im 2D-Modus gesammelt (leere
            # Liste bei encoder="flat" -> keine zusaetzliche Rechenzeit/Speicher
            # im Bestandsverhalten). uint8 (0/1) statt float32, siehe
            # `encoder`-Doku oben -- jeder der 76 Kanaele ist binaer.
            planes_l = [] if self.encoder == "2d" else None

            for f in files:
                # Schema 17 (v20-Aera): stammt die Datei von einem
                # WDL-Generator, ist `bootstrap_value` eine NATIVE
                # [0,1]-Gewinnwahrscheinlichkeit; Alt-Generatoren (tanh-Kopf)
                # liefern eine gestauchte Marge, die unten Platt-entstaucht
                # wird (Audit Befund 1 + Erosions-Arm-B-Ergebnis).
                bootstrap_native = os.path.basename(f).startswith(WDL_GENERATOR_PREFIXES)
                # Policy-Traeger-Regel (siehe pol_w-Kommentar unten und
                # `_is_policy_carrier`-Doku oben): ohne Manifest traegt jede
                # Datei Policy (Bestandsverhalten); mit v20-Manifest (kein
                # `carrier_prefixes`-Feld) nur v20wdl*-Dateien und gelistete
                # Alt-Dateien (Alt-Verhalten, Rueckwaerts-kompatibel); mit
                # v21-Manifest (`carrier_prefixes` gesetzt) nur die
                # gelisteten Dateien plus explizite Praefix-Treffer -- der
                # bootstrap_native-Kurzschluss greift dann NICHT mehr.
                file_policy_carrier = _is_policy_carrier(
                    os.path.basename(f), policy_carrier_set, carrier_prefixes, bootstrap_native)
                with open(f, "rb") as file:
                    game_data = pickle.load(file)
                    final_own = _final_ownership_by_game(game_data)
                    for step in game_data:
                        states_l.append(state_to_tensor(step["state"]).numpy())
                        if planes_l is not None:
                            planes_l.append(state_to_planes(step["state"]).numpy().astype(np.uint8))
                        # λ-Misch-Value-Target-Experiment (siehe ROOT_Q_CACHE_FIELDS-
                        # Kommentar oben): root_q ist ein Roh-Feld je Schritt,
                        # UNABHAENGIG davon, ob die Partie abgeschlossen ist (anders
                        # als val/points_val unten) -- daher hier, VOR dem
                        # scores/winner-Zweig, extrahiert. [0,1]-Skala wie rtv,
                        # Remap auf [-1,1] beim Cache-Bau (*2.0-1.0). Fehlt bei
                        # Ein-Aktion-Zuegen und in Dateien ohne dieses Feld
                        # (Commit 2718b9a, v18 aufwaerts) -- dann Maske 0.
                        rq = step.get("root_q")
                        if rq is not None:
                            root_q_l.append(float(rq) * 2.0 - 1.0)
                            root_q_mask_l.append(1.0)
                        else:
                            root_q_l.append(0.0)
                            root_q_mask_l.append(0.0)
                        # Schema 18 (ENDGAME_CACHE_FIELDS): in der R5-Drafting-
                        # Zone ist root_q der EXAKTE Minimax-Wurzelwert
                        # (round5.rs via net_mcts.rs-R5-Zweig, [0,1]-Skala) --
                        # als eigenes Aux-Ziel `endgame_margin` gefuehrt.
                        # Unabhaengig von `completed` gueltig (der AB-Wert
                        # haengt nicht vom Partieausgang ab). Ausserhalb der
                        # Zone bzw. ohne root_q (v16/v17, Ein-Aktion-Zuege):
                        # Maske 0.
                        _st = step["state"]
                        if (rq is not None and _st.get("round") == 5
                                and _st.get("phase") == "drafting"):
                            endgame_l.append([float(rq)])
                            endgame_mask_l.append(1.0)
                        else:
                            endgame_l.append([0.0])
                            endgame_mask_l.append(0.0)
                        # Schema 19 (RANKING_CACHE_FIELDS, Task #35b): additives
                        # `root_child_q`-JSON-Feld -- GLEICHE Reihenfolge/Laenge
                        # wie `step["policy"]` (self_play.rs-Vertrag, siehe
                        # dortigen root_child_q_field-Kommentar). Braucht
                        # mindestens 2 Geschwister, um ueberhaupt ein Paar bilden
                        # zu koennen. Die finale `ranking_mask` haengt ZUSAETZLICH
                        # von `pol_w` ab (Tiling/Start/`policy_target_valid=False`)
                        # -- `pol_w` wird aber erst weiter unten berechnet, daher
                        # hier nur die Rohwerte sammeln (`_rk_ids`/`_rk_q`/
                        # `_rk_avail`) und den Append ZUSAMMEN mit `polw_l.append`
                        # weiter unten nachziehen (gleiche Loop-Iteration,
                        # Reihenfolge der Listen bleibt dadurch synchron).
                        rcq = step.get("root_child_q")
                        _rk_ids = np.full(RANKING_TOPK, -1, dtype=np.int16)
                        _rk_q = np.zeros(RANKING_TOPK, dtype=np.float16)
                        _rk_avail = 0.0
                        if rcq is not None and len(rcq) >= 2:
                            _act_ids = [action_to_id(pe["action"]) for pe in step["policy"]]
                            _pairs = _ranking_topk_pairs(_act_ids, [float(q) for q in rcq], RANKING_TOPK)
                            for _i, (_aid, _q) in enumerate(_pairs):
                                _rk_ids[_i] = _aid
                                _rk_q[_i] = _q
                            _rk_avail = 1.0
                        # Audit-F2 (2026-08-05): Rust stempelt `scores`/`winner`
                        # auch bei TIMEOUT-ABBRUCH bedingungslos (self_play.rs,
                        # dortiger Kommentar verspricht faelschlich einen
                        # Downstream-Filter, der nie existierte -- self_play.py
                        # WARNT nur). Der -1-Sentinel-Zweig unten war damit auf
                        # Rust-Korpora UNERREICHBAR und Abbruch-Zwischenstaende
                        # wurden zu harten Sieg-Labels. `game_completed` sperrt
                        # unten wdl_outcome (Sentinel -1) und opp_points_mask
                        # (0); die weichen val/points-Ziele behalten den
                        # Zwischenstand (dokumentierte Restunsicherheit, kein
                        # erfundenes HARTES Label). Fehlendes Feld = Alt-Korpus
                        # = vertrauenswuerdig; nur explizites False sperrt.
                        # Aktueller 900er-Korpus: 0% betroffen (Stichprobe 90
                        # Dateien) -- Korrektheits-Fix fuer kuenftige
                        # Kampagnen, kein Label-Shift, daher KEIN Schema-Bump.
                        game_completed = step.get("completed", True) is not False
                        if "scores" in step and "winner" in step:
                            p = step["player"]
                            scores_src = step.get("scores_unclamped", step["scores"])
                            own_total = float(scores_src[p])
                            opp_total = float(scores_src[1 - p])
                            # Weiches, symmetrisches Margin-Ziel statt hartem
                            # ±1 (siehe VALUE_SCHEMA_VERSION=13-Kommentar oben)
                            # -- dieselbe own_total/opp_total-Information wie
                            # bisher, nur nicht mehr an den Raendern
                            # gesaettigt/binarisiert.
                            val = math.tanh((own_total - opp_total) / VALUE_SCALE)
                            # Punktestand-Formel bleibt als separates Aux-Ziel
                            # erhalten (bereits inkl. Wertungsplatten).
                            # Schema 20 (Nutzer 2026-08-10): REIN own, kein
                            # Gegner-Anteil mehr. Der 0,1-Term war nur ueber
                            # `opp_aware_points_utility` rueckgewinnbar, und der
                            # Pfad ist hinter `w == 0.0` toter Code.
                            points_val = math.tanh(own_total / VALUE_SCALE)
                            # Task #28 (PREREG_task28_aggression.md, "Minimal-
                            # invasiver Zuschnitt" Punkt 2): eigenstaendiger
                            # Aux-Ziel-Track fuer den additiven
                            # `opp_points_head` -- spiegelt JEDEN Zweig, der
                            # oben in `points_val` den own-seitigen Term
                            # (tanh(own_total/SCALE) -> own_rtv ->
                            # TD-Blend mit own_bootstrap) bildet, 1:1 auf den
                            # opp-Groessen. NUR durch diese Spiegelung gilt
                            # `points_val == own-Term - EPSILON*opp_points_val`
                            # in JEDEM Zweig (Induktion ueber rtv-/Bootstrap-
                            # Override) -- und damit algebraisch exakt
                            # `own_pts (= own-Term) = points_pred +
                            # VALUE_OPP_EPSILON * opp_pred` bei perfekter
                            # Kopf-Vorhersage. opp_points_val ist ausdruecklich
                            # NICHT `val` gespiegelt (dessen Basis ist die
                            # MARGIN (own-opp)/SCALE, nicht own_total allein).
                            opp_points_val = math.tanh(opp_total / VALUE_SCALE)
                            # Audit-F2: Abbruch-Zwischenstand ist kein echter
                            # Endpunktestand -- Maske 0 (Konvention wie im
                            # Legacy-Zweig unten).
                            opp_points_mask = 1.0 if game_completed else 0.0
                            # Rundenübergangs-Ziel (siehe round_transition.rs/
                            # self_play.rs::play_net_self_play_game): über
                            # mehrere Chance-Node-Samples (verschiedene mögliche
                            # Fabrik-Neubefüllungen) gemittelte NETZ-
                            # Gewinnwahrscheinlichkeit ([0,1], nicht Punkte --
                            # daher NICHT in die own_total/opp_total-Formel
                            # oben eingesetzt, sondern direkt auf den
                            # tanh-Wertebereich [-1,1] reskaliert). Nur
                            # vorhanden, wenn dieser Schritt tatsächlich einen
                            # Rundenübergang erreicht hat (nicht Runde 5, keine
                            # abgebrochenen Partien) -- sonst Fallback auf die
                            # obigen Formeln (hartes ±1 bzw. Punktestand).
                            #
                            # Ab Version 12 ersetzt own_rtv sowohl `val` (das
                            # Hauptziel, das net_mcts.rs tatsächlich für PUCT
                            # liest) als auch `points_val` -- own_rtv ist
                            # bereits exakt auf `val`s Skala (2*win_prob-1),
                            # daher direkt übernommen statt über die
                            # own_total/opp_total-Punkteformel geschickt.
                            rtv = step.get("round_transition_value")
                            # Task #84 (rtv-Ablation Phase 1): Variante kann
                            # den Override komplett ("nortv") oder nur fuer
                            # Runde-1-Zustaende ("nortv_r1") unterdruecken --
                            # Rundenzuordnung identisch zu
                            # offline_diagnose.py::load_val_samples
                            # (`step["state"]["round"]`).
                            if rtv is not None and value_target_variant == "nortv":
                                rtv = None
                            elif (rtv is not None and value_target_variant == "nortv_r1"
                                  and int(step["state"].get("round", 0)) == 1):
                                rtv = None
                            if rtv is not None:
                                own_rtv = float(rtv[p]) * 2.0 - 1.0
                                opp_rtv = float(rtv[1 - p]) * 2.0 - 1.0
                                val = own_rtv
                                points_val = own_rtv  # Schema 20: rein own
                                opp_points_val = opp_rtv  # Task #28: spiegelt own_rtv-Override
                            # Punkt 6 (VALUE_SCHEMA_VERSION=15): TD-Bootstrap-
                            # Blend, siehe Kommentar oben -- mischt HINEIN
                            # (ersetzt `val`/`points_val` nicht komplett wie
                            # `rtv`), da der kurze Horizont eine andere,
                            # naehere Groesse schaetzt als das bisherige Ziel.
                            bv = step.get("bootstrap_value")
                            if bv is not None:
                                own_bootstrap = float(bv[p]) * 2.0 - 1.0
                                opp_bootstrap = float(bv[1 - p]) * 2.0 - 1.0
                                points_bootstrap = own_bootstrap  # Schema 20: rein own
                                val = TD_LAMBDA * own_bootstrap + (1.0 - TD_LAMBDA) * val
                                points_val = TD_LAMBDA * points_bootstrap + (1.0 - TD_LAMBDA) * points_val
                                # Task #28: identischer TD-Blend, opp-Seite
                                # (gleiches TD_LAMBDA, gleiche Blend-Formel).
                                opp_points_val = (TD_LAMBDA * opp_bootstrap
                                                  + (1.0 - TD_LAMBDA) * opp_points_val)
                            # Task #34 (VALUE_SCHEMA_VERSION=16, WDL_CACHE_FIELDS):
                            # eigenstaendiges, PARALLELES Ziel -- UNABHAENGIG von
                            # `val`/`rtv` oben (der rtv-Zweig bleibt bewusst
                            # unangetastet, siehe Kopf-Kommentar). Hartes
                            # Sieg/Niederlage-Label plus derselbe TD-Blend-Formel
                            # wie oben, ABER `bv[p]` NICHT auf [-1,1] remappen --
                            # `bootstrap_value` ist bereits eine [0,1]-
                            # Gewinnwahrscheinlichkeit, hier direkt geblendet
                            # (macht den Blend semantisch kohaerent, siehe
                            # STATUS.md "Bonus-Befund").
                            # Audit-F2: nur ECHTE Ausgaenge liefern ein hartes
                            # Label; Abbruch -> Sentinel -1 (wie der Legacy-
                            # Zweig unten) und value_wdl = weiche Projektion
                            # statt eines erfundenen harten Anteils.
                            if game_completed:
                                wdl_outcome_val = 1.0 if int(step["winner"]) == p else 0.0
                                value_wdl = wdl_outcome_val
                                if bv is not None:
                                    # Schema 17: Alt-Generator-Bootstrap wird
                                    # entstaucht, WDL-nativer bleibt roh
                                    # (siehe VALUE_SCHEMA_VERSION-Kommentar).
                                    bvp = float(bv[p])
                                    if not bootstrap_native:
                                        bvp = _destretch_prob(bvp)
                                    value_wdl = TD_LAMBDA * bvp + (1.0 - TD_LAMBDA) * wdl_outcome_val
                                value_wdl = min(1.0, max(0.0, value_wdl))
                            else:
                                wdl_outcome_val = -1.0
                                value_wdl = min(1.0, max(0.0, (val + 1.0) * 0.5))
                        else:
                            val = float(step["value"])
                            points_val = val
                            # Task #28: unvollstaendige Partie (kein scores/
                            # winner) -- gleicher Fallback-PFAD wie points_val
                            # (`points_val = val`), aber hier Maske 0 statt
                            # eines erfundenen Werts (PREREG-Vorgabe: "Maske 0
                            # statt eines erfundenen Werts").
                            opp_points_val = 0.0
                            opp_points_mask = 0.0
                            # Task #34: kein echtes Sieg/Niederlage-Label
                            # vorhanden -- grobe Projektion der alten
                            # tanh-Marge auf [0,1] als bestmoegliche Naeherung
                            # (kein erfundenes hartes Label), `wdl_outcome`
                            # bekommt den "unbekannt"-Sentinel -1.0 (analog zur
                            # Ownership-Konvention).
                            value_wdl = (val + 1.0) * 0.5
                            wdl_outcome_val = -1.0
                        values_l.append([val])
                        points_l.append([points_val])
                        opp_points_l.append([opp_points_val])
                        opp_points_mask_l.append(opp_points_mask)
                        value_wdl_l.append([value_wdl])
                        wdl_outcome_l.append([wdl_outcome_val])

                        t_policy = np.zeros(NUM_ACTIONS, dtype=np.float32)
                        for pe in step["policy"]:
                            t_policy[action_to_id(pe["action"])] += pe["prob"]
                        s = t_policy.sum()
                        if s > 0: t_policy /= s
                        if POLICY_TARGET_SHARPEN_EXPONENT != 1.0:
                            t_policy = np.power(t_policy, POLICY_TARGET_SHARPEN_EXPONENT, dtype=np.float32)
                            s2 = t_policy.sum()
                            if s2 > 0: t_policy /= s2
                        policies_l.append(t_policy)

                        mask = np.zeros(NUM_ACTIONS, dtype=np.float32)
                        moves = step.get("valid_actions") or step["state"].get("valid_moves", [])
                        for move in moves:
                            mask[action_to_id(move)] = 1.0
                        # Selbstkonsistenz: die tatsächlich gespielten Policy-Aktionen
                        # sind per Definition legal — immer in die Maske aufnehmen.
                        # Verhindert Policy-Leaks (Target-Masse auf maskierter Aktion →
                        # explodierender Policy-Loss), falls valid_actions unvollständig ist.
                        for pe in step["policy"]:
                            mask[action_to_id(pe["action"])] = 1.0
                        masks_l.append(mask)

                        moon_target = np.full(5, -1.0, dtype=np.float32)
                        moon_order = step.get("moon_order_target", None)
                        if moon_order:
                            for rank, color_name in enumerate(moon_order):
                                c_idx = _CIDX.get(color_name, -1)
                                if c_idx >= 0:
                                    moon_target[c_idx] = float(rank)
                        moon_l.append(moon_target)

                        # Policy-Loss nur für ECHTE Drafting-Schritte: Tiling/Start-
                        # Steps sind one-hot Solver-/Heuristik-Züge, die das Netz nie
                        # vorhersagen muss (Tiling macht der DFS-Solver). Sie fluten
                        # sonst den Policy-Head mit Tiling-Aktionen → das Netz legt
                        # auch in der Drafting-Phase Masse auf (illegale) Tiling-IDs
                        # und die Drafting-Priors verkommen zu Rauschen.
                        phase = step["state"].get("phase")
                        is_start = any(pe["action"].get("is_start") for pe in step["policy"])
                        pol_w = 1.0 if (phase == "drafting" and not is_start) else 0.0
                        # Schema 17 / v20-Zwei-Klassen-Fenster: liegt ein
                        # Policy-Traeger-Manifest vor, tragen ALT-Dateien nur
                        # dann Policy-Ziele, wenn sie darin gelistet sind --
                        # alle uebrigen Alt-Dateien sind reines Value-Material
                        # (Nutzer-Design 2026-08-06: 1350 v18- + 450
                        # v17-Partien Policy-aktiv). v20wdl*-Dateien regeln
                        # sich selbst ueber `policy_target_valid` (Schwarm).
                        if not file_policy_carrier:
                            pol_w = 0.0
                        # PCR (Task #14): Cheap-Suche-Zuege tragen ein explizites
                        # `policy_target_valid=false` (self_play.rs, Feld nur bei
                        # aktivem PCR vorhanden) -- ihr Visit-Ziel stammt aus einer
                        # verkuerzten Suche und ist als Policy-Ziel unzuverlaessig
                        # (PREREG_pcr.md). Maske 0 wie Tiling/Start-Schritte; das
                        # Value-/Punkte-/root_q-Ziel bleibt unmaskiert. Feld fehlt
                        # (None) in allen Nicht-PCR-Korpora -> dort byte-identisch.
                        if step.get("policy_target_valid") is False:
                            pol_w = 0.0
                        polw_l.append(np.float32(pol_w))
                        # Schema 19 (RANKING_CACHE_FIELDS): finale Maske erst
                        # HIER moeglich -- `pol_w` (inkl. aller obigen
                        # Sonderfaelle: Tiling/Start, Policy-Traeger-Manifest,
                        # PCR) ist jetzt final berechnet. `_rk_avail` kam aus
                        # dem `root_child_q`-Block oben (gleiche Loop-Iteration).
                        ranking_ids_l.append(_rk_ids)
                        ranking_q_l.append(_rk_q)
                        ranking_mask_l.append(np.float32(_rk_avail if pol_w > 0.0 else 0.0))
                        rounds_l.append(np.int8(step["state"].get("round", 0)))
                        # Ego-Perspektive: erst der Spieler am Zug, dann der
                        # Gegner -- dieselbe Reihenfolge wie in state_to_tensor
                        # (`me = players[curr_pi]`, dann `enemy`). Die FUELLUNG
                        # stammt aus dem Endzustand DES SPIELS, gilt also fuer
                        # alle Schritte dieser Partie.
                        fo = final_own.get(step["game_id"])
                        if fo is None:
                            own_l.append(np.full(self.own_targets, -1, dtype=np.int8))
                        else:
                            c = step["state"].get("current_player", 0)
                            first, second = (fo[0], fo[1]) if c == 0 else (fo[1], fo[0])
                            vec = first + second
                            if self.conjunction_head:
                                # Gleiche Ego-Reihenfolge wie oben, HINTEN
                                # angehaengt -> Layout des erweiterten Kopfs:
                                # [0:36] Rand ich, [36:72] Rand Gegner,
                                # [72:97] Konj. ich, [97:122] Konj. Gegner.
                                cj_first, cj_second = (fo[2], fo[3]) if c == 0 else (fo[3], fo[2])
                                vec = vec + cj_first + cj_second
                            own_l.append(np.array(vec, dtype=np.int8))

            # RAM-Fix (2026-07-31): jede *_l-Liste wird SOFORT nach ihrer
            # *_np-Konvertierung freigegeben (statt alle Listen bis nach der
            # letzten Konvertierung inkl. `planes_np` mitzuschleppen) -- senkt
            # die Transientspitze waehrend des Cache-Baus, an der Liste UND
            # fertiges Array je Feld kurzzeitig gleichzeitig im Speicher
            # standen. Bei ~1,3 Mio. Zuegen (voller Korpus) sind `states_l`/
            # `policies_l`/`masks_l`/`planes_l` allein je mehrere GB (Python-
            # Objekt-Overhead pro Listenelement kommt oben drauf) -- ein
            # realer from-scratch-2D-Lauf auf dem vollen Korpus ist mit der
            # alten Reihenfolge (ein Sammel-`del` ganz am Ende) vermutlich an
            # genau dieser Spitze bzw. der anschliessenden Dauerlast
            # gestorben (spurlos, kein Traceback, siehe `_open_planes_h5`).
            # RAM-Optimierung v20 (2026-08-06, Nutzer-Auftrag): das
            # 21k-Partien-Fenster (~3,4 Mio Zustaende) wuerde in float32
            # ~35-40 GB RSS kosten (gemessen: 12,1 KB/Zustand bei 9k Partien,
            # 32 GB Maschine). Kompakte Typen druecken das auf ~6 KB/Zustand:
            # - states/policies -> float16 (Eingaben/Soft-Targets; Quantisierung
            #   ~6e-4 relativ, weit unter Seed-Rauschen; NICHT bit-identisch,
            #   Notausstieg MOSAIC_CACHE_F32=1),
            # - masks -> uint8 (0/1, EXAKT),
            # - planes waren bereits uint8, ownership bereits int8.
            # train.py castet je Batch nach dem Device-Move auf float32.
            _f = np.float32 if os.environ.get("MOSAIC_CACHE_F32") == "1" else np.float16
            states_np    = np.array(states_l,    dtype=_f);         del states_l
            policies_np  = np.array(policies_l,  dtype=_f);         del policies_l
            values_np    = np.array(values_l,    dtype=np.float32); del values_l
            masks_np     = np.array(masks_l,     dtype=np.uint8);   del masks_l
            moon_np      = np.array(moon_l,      dtype=np.float32); del moon_l
            polw_np      = np.array(polw_l,      dtype=np.float32); del polw_l
            points_np    = np.array(points_l,    dtype=np.float32); del points_l
            rounds_np    = np.array(rounds_l,    dtype=np.int8);    del rounds_l
            own_np       = np.array(own_l,       dtype=np.int8);    del own_l
            root_q_np      = np.array(root_q_l,      dtype=np.float32); del root_q_l
            root_q_mask_np = np.array(root_q_mask_l, dtype=np.float32); del root_q_mask_l
            opp_points_np      = np.array(opp_points_l,      dtype=np.float32); del opp_points_l
            opp_points_mask_np = np.array(opp_points_mask_l, dtype=np.float32); del opp_points_mask_l
            value_wdl_np    = np.array(value_wdl_l,    dtype=np.float32); del value_wdl_l
            wdl_outcome_np  = np.array(wdl_outcome_l,  dtype=np.float32); del wdl_outcome_l
            endgame_np      = np.array(endgame_l,      dtype=np.float32); del endgame_l
            endgame_mask_np = np.array(endgame_mask_l, dtype=np.float32); del endgame_mask_l
            ranking_ids_np  = np.array(ranking_ids_l,  dtype=np.int16);   del ranking_ids_l
            ranking_q_np    = np.array(ranking_q_l,    dtype=np.float16); del ranking_q_l
            ranking_mask_np = np.array(ranking_mask_l, dtype=np.float32); del ranking_mask_l
            planes_np    = None
            if planes_l is not None:
                planes_np = np.array(planes_l, dtype=np.uint8)
                del planes_l

            # Bitpacking (RAM-Optimierung v21, PREREG_v21_fenster.md "RAM-
            # Voraussetzung"): masks/planes sind striktes 0/1 -- `_pack_bits`
            # packt verlustfrei auf 1/8 der Byte-Groesse (masks 406->51 B,
            # planes 2736->342 B je Sample, exaktes Layout siehe
            # `_pack_bits`-Kopf-Kommentar oben). `cache_nopack` (bereits Teil
            # des Cache-Keys, s.o.) erzwingt als Notausstieg das alte
            # unkomprimierte Format 1:1. `masks_np`/`planes_np` werden ab hier
            # durch die (ggf. gepackte) Speicherform ERSETZT -- alles danach
            # (HDF5-Schreiben, `self.masks`) bleibt dadurch unabhaengig vom
            # Packmodus unveraendert einfach.
            self.bitpacked = not cache_nopack
            planes_orig_shape = (NUM_PLANES_CHANNELS, 6, 6)
            if self.bitpacked:
                masks_np = _pack_bits(masks_np)  # [N,406] -> [N,51]
                if planes_np is not None:
                    planes_np = _pack_bits(planes_np.reshape(len(planes_np), -1))  # [N,76,6,6] -> [N,342]

            print(f"Datensatz geladen: {len(states_np)} Züge. "
                  f"(Features pro Zug: {states_np.shape[1]}) — {time.time()-t0:.1f}s")
            print(f"💾 Speichere HDF5-Cache...")
            _masks_key = 'masks_packed' if self.bitpacked else 'masks'
            _planes_key = 'planes_packed' if self.bitpacked else 'planes'
            with h5py.File(cache_path_h5, 'w') as hf:
                hf.create_dataset('states',               data=states_np,    compression='lzf')
                hf.create_dataset('policies',             data=policies_np,  compression='lzf')
                hf.create_dataset('values',               data=values_np,    compression='lzf')
                hf.create_dataset(_masks_key,             data=masks_np,     compression='lzf')
                if self.bitpacked:
                    hf[_masks_key].attrs['orig_count'] = NUM_ACTIONS
                hf.create_dataset('moon_order_targets',   data=moon_np,      compression='lzf')
                hf.create_dataset('policy_weights',       data=polw_np,      compression='lzf')
                hf.create_dataset('points_forecast',      data=points_np,    compression='lzf')
                hf.create_dataset('rounds',               data=rounds_np,    compression='lzf')
                hf.create_dataset('ownership',            data=own_np,       compression='lzf')
                hf.create_dataset('root_q',               data=root_q_np,      compression='lzf')
                hf.create_dataset('root_q_mask',          data=root_q_mask_np, compression='lzf')
                hf.create_dataset('opp_points_forecast',  data=opp_points_np,      compression='lzf')
                hf.create_dataset('opp_points_mask',      data=opp_points_mask_np, compression='lzf')
                hf.create_dataset('values_wdl',           data=value_wdl_np,     compression='lzf')
                hf.create_dataset('wdl_outcome',          data=wdl_outcome_np,   compression='lzf')
                hf.create_dataset('endgame_margin',       data=endgame_np,       compression='lzf')
                hf.create_dataset('endgame_mask',         data=endgame_mask_np,  compression='lzf')
                hf.create_dataset('ranking_action_ids',   data=ranking_ids_np,   compression='lzf')
                hf.create_dataset('ranking_child_q',      data=ranking_q_np,     compression='lzf')
                hf.create_dataset('ranking_mask',         data=ranking_mask_np,  compression='lzf')
                if planes_np is not None:
                    hf.create_dataset(_planes_key,        data=planes_np,    compression='lzf')
                    if self.bitpacked:
                        hf[_planes_key].attrs['orig_shape'] = planes_orig_shape
            print(f"✅ Cache gespeichert: {cache_path_h5}")
            # RAM-Fix: `planes_np` (die groesste Einzelstruktur, ~3,6 GB beim
            # vollen Korpus, dank Bitpacking jetzt ~450 MB) wird NACH dem
            # Schreiben verworfen statt als `self.planes` fuer die gesamte
            # Trainingsdauer im RAM zu bleiben -- `_open_planes_h5` liest ab
            # jetzt lazy aus der gerade geschriebenen Datei, identisch zum
            # Cache-Lade-Pfad oben.
            # Hinweis: `_resolve_planes_h5_path` liest hier NUR den Pfad um --
            # die Datei selbst wird weiterhin unter `cache_path_h5` (regulaerer
            # Ort) geschrieben; ein Override muesste die frisch geschriebene
            # Datei zusaetzlich manuell an den Override-Ort kopieren.
            self._planes_dataset_name = _planes_key if planes_np is not None else None
            self._planes_h5_path = _resolve_planes_h5_path(cache_path_h5) if planes_np is not None else None
            del planes_np

            self.states             = torch.from_numpy(states_np)
            self.policies           = torch.from_numpy(policies_np)
            self.values             = torch.from_numpy(values_np)
            self.masks              = torch.from_numpy(masks_np)
            self.moon_order_targets = torch.from_numpy(moon_np)
            self.policy_weights     = torch.from_numpy(polw_np)
            self.points_forecast    = torch.from_numpy(points_np)
            self.rounds             = torch.from_numpy(rounds_np)
            self.ownership          = torch.from_numpy(own_np)
            self.root_q             = torch.from_numpy(root_q_np)
            self.root_q_mask        = torch.from_numpy(root_q_mask_np)
            self.opp_points_forecast = torch.from_numpy(opp_points_np)
            self.opp_points_mask     = torch.from_numpy(opp_points_mask_np)
            self.values_wdl          = torch.from_numpy(value_wdl_np)
            self.wdl_outcome         = torch.from_numpy(wdl_outcome_np)
            self.endgame_margin      = torch.from_numpy(endgame_np)
            self.endgame_mask        = torch.from_numpy(endgame_mask_np)
            self.ranking_action_ids  = torch.from_numpy(ranking_ids_np)
            self.ranking_child_q     = torch.from_numpy(ranking_q_np)
            self.ranking_mask        = torch.from_numpy(ranking_mask_np)
            # `self._planes_h5_path` wurde oben bereits gesetzt (RAM-Fix) --
            # kein `self.planes`-Tensor mehr hier.

        self.input_size = self.states.shape[1] if len(self.states) > 0 else 100
        self.value_target_variant = value_target_variant
        self._maybe_load_planes_eager()

    def _maybe_load_planes_eager(self):
        """Laedt den kompletten Planes-HDF5-Inhalt EINMALIG ins RAM
        (`self._planes_eager_tensor`) -- Task #11 Phase 2, seit 2026-07-31
        STANDARDVERHALTEN (vorher lazy als Standard, siehe Historie unten).

        GEMESSENER GRUND FUER DIE UMKEHR: `hf['planes'][idx]`-Einzelzugriffe
        auf den lzf-komprimierten Cache sind ~400.000x langsamer als ein
        In-RAM-Indexzugriff nach einmaligem Voll-Read (205 ms/Sample lazy vs.
        0,5 µs/Sample in-RAM, gemessen auf dem echten 1,3-Mio-Sample-2D-
        Trainingscache) -- bei Batch=256 macht das ~52 s/Batch allein fuer
        Planes-I/O, ein Epoche-1-Batch-100-Herzschlag waere erst nach ~87 min
        faellig gewesen. Die drei vermeintlichen "stillen Abstuerze" des
        lazy-Pfads (2026-07-31) waren mit hoher Wahrscheinlichkeit KEINE
        Abstuerze, sondern kriechend langsame, technisch weiterlaufende
        Prozesse, die beim Task-Management (Stop/Resume) beendet wurden --
        nicht ein Speicherproblem, das laut System-RAM-Log (34,3 GB, 3,6 GB
        Planes je Split) nie real existiert hat.

        `MOSAIC_PLANES_LAZY=1` schaltet auf den lazy Pro-Index-HDF5-Zugriff
        zurueck -- NUR fuer echt knappe RAM-Verhaeltnisse gedacht (Faktor
        ~400.000x langsamer nachweislich in Kauf zu nehmen, wenn 3,6 GB/Split
        nicht ins RAM passen). Kein Effekt bei encoder="flat" (kein
        `_planes_h5_path`)."""
        if self._planes_h5_path is None:
            return
        if os.environ.get("MOSAIC_PLANES_LAZY") == "1":
            print(f"ℹ️  MOSAIC_PLANES_LAZY=1: Planes bleiben lazy (h5py-Pro-Index-Zugriff) -- "
                  f"NUR fuer knappe RAM-Verhaeltnisse gedacht, ~400.000x langsamer als in-RAM "
                  f"(gemessen 2026-07-31, siehe Docstring).")
            return
        import h5py
        # `self._planes_dataset_name`: 'planes_packed' oder 'planes' (RAM-
        # Optimierung v21, Bitpacking) -- selbstbeschreibend am Cache
        # bestimmt, kein zusaetzlicher Zustand noetig.
        with h5py.File(self._planes_h5_path, "r") as hf:
            arr = hf[self._planes_dataset_name][:]
        self._planes_eager_tensor = torch.from_numpy(arr)
        gb = self._planes_eager_tensor.element_size() * self._planes_eager_tensor.nelement() / 1e9
        print(f"Planes komplett ins RAM geladen ({tuple(self._planes_eager_tensor.shape)}, {gb:.2f} GB"
              f"{', gepackt' if self.bitpacked else ''}).")

    def __len__(self): return len(self.states)

    def apply_value_target_lambda(self, lam: float, wdl: bool = False) -> float:
        """λ-Misch-Value-Target-Experiment (Willemsen et al. 2021, "soft-Z"):
        mischt ein Value-Target IN-PLACE mit dem rohen Root-Suchwert
        `self.root_q` ueberall dort, wo `self.root_q_mask` 1 ist --
        `target = lam*target + (1-lam)*root_q(-Skala je nach Zweig)`.
        Samples ohne root_q (Maske 0, z.B. Ein-Aktion-Zuege oder Dateien ohne
        das Feld) bleiben unveraendert (identisch zu lam=1.0), unabhaengig
        von `lam`.

        KORREKTHEITS-FIX (Koordinator-Befund 2026-08-08): frueher mischte
        diese Methode IMMER `self.values` (tanh-Ziel), auch wenn train.py
        mit `--value-head wdl` gegen `self.values_wdl` trainierte -- die
        Mischung lief damit fuer WDL-Laeufe komplett ins Leere (Metriken
        eines λ<1.0-Laufs waren bit-nah identisch zu λ=1.0). `wdl` waehlt
        jetzt explizit das tatsaechlich trainierte Zielfeld:

        - `wdl=False` (Default/Bestandsverhalten): mischt `self.values`
          (tanh-Ziel, Skala [-1,1]) -- fuer diesen Zweig ist nichts anders
          als vorher, `lam=1.0` laesst `self.values` weiterhin KOMPLETT
          UNVERAENDERT (frueher Return-Pfad, keine Tensor-Operation).
        - `wdl=True`: mischt stattdessen `self.values_wdl` (WDL-Ziel, Skala
          [0,1]). SKALEN-DETAIL: `self.root_q` liegt im Cache remapped auf
          [-1,1] (Cache-Bau: `root_q_l.append(float(rq) * 2.0 - 1.0)`),
          `values_wdl` dagegen auf [0,1] (Gewinnwahrscheinlichkeit). Vor der
          Mischung wird root_q daher zurueckgerechnet: `p_root = (root_q+1)/2`
          -- sonst liefe ein [-1,1]-Rohwert direkt in ein [0,1]-Ziel und das
          Ergebnis koennte aus [0,1] herauslaufen (z.B. root_q=-1 wuerde ohne
          Remap ein Ziel von -1 statt 0 mischen). `self.values` bleibt im
          `wdl=True`-Zweig unangetastet, `self.values_wdl` bleibt im
          `wdl=False`-Zweig unangetastet -- jeder Aufruf ruehrt GENAU eines
          der beiden Zielfelder an.

        λ wirkt hier bewusst VOR/unabhaengig von `--wdl-hard-only`
        (trainiert stattdessen auf dem rohen `wdl_outcome`, siehe train.py)
        und `_destretch_wdl_target` (entstaucht `targets_v_wdl` erst im
        Trainings-Loop) -- diese Methode mischt nur das Cache-Feld, das
        `--wdl-hard-only`/destretch als Eingabe sehen.

        Aufrufer (train.py) ruft dies EINMALIG je Dataset (Train- UND
        Val-Split) direkt NACH dem Laden auf, VOR dem `DataLoader`-Wrap --
        jeder Batch liest danach automatisch aus dem gemischten Zielfeld,
        keine Aenderung an `__getitem__`/der Tupel-Form noetig.

        Rueckgabe: Anteil der Samples mit `root_q_mask==1` (Praesenz-Anteil,
        NICHT abhaengig von `lam`/`wdl`) -- fuer das train.py-Logging (PREREG
        verlangt den Misch-Anteil dokumentiert, auch bei lam=1.0 informativ)."""
        if not (0.0 <= lam <= 1.0):
            raise ValueError(
                f"value_target_lambda={lam!r} ausserhalb [0,1] -- harter Abbruch "
                f"statt stillem Clamp (siehe train.py --load-Footgun-Historie)."
            )
        n = len(self.values)
        if n == 0:
            return 0.0
        frac = float(self.root_q_mask.mean().item())
        if lam < 1.0:
            mask_col = self.root_q_mask.unsqueeze(1).bool()  # [N] -> [N,1], matcht self.values/values_wdl
            root_q_col = self.root_q.unsqueeze(1)
            if wdl:
                # Skalen-Fix: root_q ([-1,1]) zurueck auf [0,1] wie values_wdl.
                p_root_col = (root_q_col + 1.0) / 2.0
                mixed = lam * self.values_wdl + (1.0 - lam) * p_root_col
                # Defensiv geclampt: lam in [0,1] und p_root_col in [0,1] (da
                # root_q in [-1,1]) garantieren eine Konvexkombination in
                # [0,1] nur MATHEMATISCH exakt -- Float-Rundung koennte
                # hauchduenn drueber/drunter landen; klare Grenze statt
                # stillem Downstream-Effekt auf die BCE-Loss (Log(0) o.ae.).
                mixed = mixed.clamp(0.0, 1.0)
                self.values_wdl = torch.where(mask_col, mixed, self.values_wdl)
            else:
                mixed = lam * self.values + (1.0 - lam) * root_q_col
                self.values = torch.where(mask_col, mixed, self.values)
        return frac

    def _open_planes_h5(self):
        """Öffnet lazy einen HDF5-Handle für Pro-Index-Planes-Zugriff -- NUR
        genutzt, wenn `MOSAIC_PLANES_LAZY=1` gesetzt ist (`_maybe_load_planes_eager`);
        Standardpfad ist seit 2026-07-31 `self._planes_eager_tensor` (siehe
        dort für die Begründung: lazy Pro-Index-Zugriff ist gemessen
        ~400.000x langsamer, kein Speichervorteil, der das rechtfertigt --
        3,6 GB/Split passen komfortabel ins RAM). Bleibt im Code für echt
        knappe RAM-Verhältnisse. Nur der Dateipfad steht in
        `self._planes_h5_path`, der offene Handle entsteht PRO PROZESS beim
        ersten Zugriff.

        Vorsicht bei künftigem `DataLoader(..., num_workers>0)` unter
        Windows: ein gepickeltes offenes `h5py.File` ist zwischen Prozessen
        nicht sicher teilbar. `__getstate__`/`__setstate__` unten lassen den
        Handle beim Pickeln (Worker-Start) bewusst aus, jeder Worker öffnet
        sich seinen eigenen -- aktuell nutzt `train.py` `num_workers=0`
        (Default, kein expliziter Wert), daher unkritisch, aber vorbereitet."""
        if self._planes_h5_file is None:
            import h5py
            self._planes_h5_file = h5py.File(self._planes_h5_path, "r")
        return self._planes_h5_file

    def _get_planes_tensor(self, idx):
        # RAM-Optimierung v20: uint8 bleibt bis NACH dem Device-Move erhalten
        # (train.py castet batchweise) -- spart 4x Collate-/Transfer-Volumen
        # gegenueber dem frueheren Per-Sample-`.float()`.
        # RAM-Optimierung v21 (Bitpacking): ist `self.bitpacked` True, liefert
        # dies ein FLACHES [342]-Byte-Sample statt [76,6,6] -- das Entpacken
        # passiert NICHT hier (pro Sample), sondern EINMAL pro Batch in
        # train.py (`unpack_planes_batch`, siehe Benchmark-Kommentar dort).
        if self._planes_eager_tensor is not None:
            return self._planes_eager_tensor[idx]
        hf = self._open_planes_h5()
        arr = hf[self._planes_dataset_name][idx]  # EIN Sample -- kein Voll-Array-Read
        return torch.from_numpy(arr)

    def __getstate__(self):
        """Siehe `_open_planes_h5` -- der offene h5py-Handle darf nicht mit-
        gepickelt werden, nur der Pfad überlebt."""
        state = self.__dict__.copy()
        state["_planes_h5_file"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    def __getitem__(self, idx):
        base = (self.states[idx], self.policies[idx], self.values[idx], self.masks[idx],
                self.moon_order_targets[idx], self.policy_weights[idx], self.points_forecast[idx],
                self.rounds[idx], self.ownership[idx],
                # Task #28 (PREREG_task28_aggression.md): additiv ANS ENDE
                # angehaengt -- Aufrufer, die dieses 9-Tupel noch kennen (z.B.
                # `tools/diagnosis.py`s `*_`-Catch-all), bleiben unberuehrt,
                # solange sie nicht die letzten 2 Elemente per Index erwarten.
                self.opp_points_forecast[idx], self.opp_points_mask[idx],
                # Task #34: erneut additiv ANS ENDE angehaengt (gleiches
                # Muster) -- `values_wdl` (TD-geblendetes WDL-Trainingsziel)
                # + `wdl_outcome` (roher, ungeblendeter Ausgang fuer den
                # arm-uebergreifend vergleichbaren Brier-Score, siehe train.py).
                self.values_wdl[idx], self.wdl_outcome[idx],
                # Schema 18 (PREREG_platten_intervention.md): additiv ANS
                # ENDE, gleiches Muster -- exakter R5-Wurzelwert + Maske.
                self.endgame_margin[idx], self.endgame_mask[idx],
                # Schema 19 (Task #35b, RANKING_CACHE_FIELDS): additiv ANS
                # ENDE, gleiches Muster -- Top-K Geschwister-Aktions-IDs +
                # Q-Werte + Verfuegbarkeits-/pol_w-Maske fuer den paarweisen
                # Policy-Ranking-Loss in train.py (`--ranking-loss-weight`).
                self.ranking_action_ids[idx], self.ranking_child_q[idx], self.ranking_mask[idx])
        # Task #11 Phase 2: bei encoder="2d" wird `planes` ALS ERSTES Element
        # vorangestellt -- `encoder="flat"` (Standard) behaelt exakt die
        # bisherige Tupel-FORM/-POSITION fuer Aufrufer, die den `encoder`-
        # Parameter nicht kennen. Der masks-INHALT (Element 4, `base[3]`) ist
        # seit RAM-Optimierung v21 aber ggf. bitgepackt (siehe `bitpacked`-
        # Doku im Klassen-Docstring) -- Konsumenten muessen `self.bitpacked`
        # pruefen, statt sich auf die Elementform zu verlassen.
        if self.encoder == "2d":
            return (self._get_planes_tensor(idx),) + base
        return base


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
        # endgame_head (PREREG_platten_intervention.md, Schema 18): exaktes
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
        # endgame_head (PREREG_platten_intervention.md, Schema 18): exaktes
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
    `export_onnx.py`/`tools/offline_diagnose.py`/`tools/oracle_metrics.py`,
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
        model = Mosaic2DNet(input_size=in_size, num_actions=num_actions, hidden_size=hs,
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