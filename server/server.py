"""
Mosaic-AI — Flask API Server

Endpoints:
  POST /api/new_game          — Neues Spiel starten
  GET  /api/state             — Aktuellen State abrufen
  POST /api/move/stone        — Stein-Zug (Aktion B/C)
  POST /api/move/dome         — Kuppelplatte aus Display (Aktion A)
  POST /api/move/dome_stack   — Kuppelplatte vom Stapel (Aktion A, -1Pkt)
  POST /api/move/bonus_chip   — Bonusplättchen nehmen (Aktion D)
  POST /api/move/start_tile   — Startkachel platzieren (Vorbereitung)
  POST /api/tiling            — Tiling-Aktion (Phase 2)
  POST /api/end_tiling        — Tiling-Phase abschließen

Alle Responses: {"ok": true, "state": {...}} oder {"ok": false, "error": "..."}
"""

import sys
import os
from pathlib import Path

# Stelle sicher dass der Hauptordner im Python-Path ist
BASE_DIR = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, BASE_DIR)

from flask import Flask, request, jsonify, send_from_directory

from engine.setup import GameState, setup_new_game, setup_new_round, NUM_ROUNDS
from engine.serializer import serialize_state
from engine.tile import TileColor
from engine.moves import (
    Move, TakeAction, PlaceAction, TakeSource,
    PlaceDomeTileMove, DrawFromStackMove, TakeBonusChipMove
)
from engine.validation import validate_move, generate_valid_moves
from engine.execution import execute_move
from engine.game import (
    Game, validate_dome_move, execute_dome_move,
    validate_draw_from_stack, execute_draw_from_stack,
    validate_take_bonus_chip, execute_take_bonus_chip,
    generate_tiling_actions, run_tiling_phase,
    check_drafting_complete,
    generate_dome_moves, generate_bonus_chip_moves,
)
from engine.round_end import (
    TilingAction, SpecialTilingAction,
    validate_tiling_action, execute_full_tiling, apply_round_scoring,
    get_pending_tiling_rows, process_unplaceable_rows,
    find_unplaceable_rows,
)

STATIC_DIR = Path(__file__).resolve().parent / 'static'
app = Flask(__name__, static_folder=str(STATIC_DIR))
try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    pass

# ── Global game state ────────────────────────────────────────────────────────
_game = Game()
_state: GameState | None = None


def ok(state: GameState) -> dict:
    return {"ok": True, "state": serialize_state(state)}


def _both_start_placed() -> bool:
    """Beide Spieler müssen ihre Startkachel gelegt haben bevor Phase 1 beginnt."""
    return _state is not None and all(p.start_dome_tile is None for p in _state.players)


def err(msg: str) -> dict:
    return {"ok": False, "error": msg}


def color(v: str) -> TileColor:
    for c in TileColor:
        if c.value == v:
            return c
    raise ValueError(f"Unbekannte Farbe: {v}")


def source(v: str) -> TakeSource:
    return TakeSource[v]


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')


@app.route('/api/new_game', methods=['POST'])
def new_game():
    global _state, _game
    data = request.get_json(silent=True) or {}
    names = data.get('names', ['Spieler 1', 'Spieler 2'])
    seed  = data.get('seed', None)
    _game = Game()
    _state = _game.start(player_names=names, seed=seed)
    return jsonify(ok(_state))


@app.route('/api/state', methods=['GET'])
def get_state():
    if _state is None:
        return jsonify(err("Kein aktives Spiel"))
    return jsonify(ok(_state))


@app.route('/api/move/stone', methods=['POST'])
def move_stone():
    """Aktion B oder C: Steine nehmen + auf Musterreihe legen."""
    if _state is None:
        return jsonify(err("Kein aktives Spiel"))
    if not _both_start_placed():
        return jsonify(err("Beide Spieler müssen zuerst ihre Startkachel legen."))
    d = request.get_json()
    try:
        src  = source(d['source'])
        col  = color(d['color'])
        row  = int(d['row'])
        fid  = d.get('factory_id')
        moon = [color(c) for c in d.get('moon_order', [])]

        # Aktion C: factory_id=None + SMALL_FACTORY_MOON
        # → nimm von ALLEN Manufakturen gleichzeitig (inkl. große Manufaktur Moon)
        if src == TakeSource.SMALL_FACTORY_MOON and fid is None:
            return _aktion_c(col, row)

        move = Move(
            take=TakeAction(source=src, color=col,
                            factory_id=fid, moon_order=moon),
            place=PlaceAction(row_index=row),
        )
        err_msg = validate_move(_state, move)
        if err_msg:
            return jsonify({"ok": False, "error": err_msg})

        execute_move(_state, move)
        _state.switch_player()
        _check_drafting_done()
        return jsonify(ok(_state))
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})


def _aktion_c(col: TileColor, row: int):
    """
    Aktion C: nimm alle obersten Fliesen der gewählten Farbe
    vom Moon aller 5 Manufakturen (klein + groß) gleichzeitig.
    """
    p = _state.active_player
    taken = []

    # Kleine Fabriken
    for f in _state.factories:
        if col in f.moon_top_colors():
            taken += f.take_from_moon(col)
            if f.is_fully_empty and f.bonus_chip and not f.bonus_chip_revealed:
                f.bonus_chip_revealed = True
                _state.log_event(f"Fabrik {f.factory_id}: Bonus-Chip aufgedeckt!")

    # Große Manufaktur Moon
    got_marker = False
    if col in _state.large_factory.moon_colors():
        tiles, got_marker = _state.large_factory.take_from_moon(col)
        taken += tiles

    if not taken:
        return jsonify({"ok": False, "error": f"Keine {col.value}-Fliesen oben auf Moon-Seiten"})

    # Startspieler-Marker
    if got_marker:
        p.holds_first_player_marker = True
        _state.first_player_next_round = _state.current_player
        _state.log_event(f"🏁 {p.name}: Startspielerstein genommen (−2 Pkt am Rundenende → aktuell {p.score} Pkt)")

    # Auf Musterreihe legen
    from engine.execution import _execute_place
    _execute_place(_state, taken, col, row)

    _state.log_event(f"🌙 {p.name}: Aktion C — {len(taken)}× {col.value} (Moon alle Manufakturen)")
    _state.switch_player()
    _check_drafting_done()
    return jsonify(ok(_state))


@app.route('/api/move/dome', methods=['POST'])
def move_dome():
    """Aktion A: Kuppelplatte aus Display nehmen und legen."""
    if _state is None:
        return jsonify(err("Kein aktives Spiel"))
    if not _both_start_placed():
        return jsonify(err("Beide Spieler müssen zuerst ihre Startkachel legen."))
    d = request.get_json()
    try:
        move = PlaceDomeTileMove(
            dome_tile_id=int(d['tile_id']),
            slot_row=int(d['slot_row']),
            slot_col=int(d['slot_col']),
            rotation=int(d.get('rotation', 0)),
        )
        err_msg = validate_dome_move(_state, move)
        if err_msg:
            return jsonify({"ok": False, "error": err_msg})
        execute_dome_move(_state, move)
        _state.switch_player()
        _check_drafting_done()
        return jsonify(ok(_state))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route('/api/move/dome_stack', methods=['POST'])
def move_dome_stack():
    """Aktion A (Stapel-Variante): verdeckt ziehen, -1 Pkt pro Karte."""
    if _state is None:
        return jsonify(err("Kein aktives Spiel"))
    if not _both_start_placed():
        return jsonify(err("Beide Spieler müssen zuerst ihre Startkachel legen."))
    d = request.get_json()
    try:
        move = DrawFromStackMove(
            num_drawn=int(d['num_drawn']),
            chosen_id=int(d['chosen_id']),
            slot_row=int(d['slot_row']),
            slot_col=int(d['slot_col']),
            rotation=int(d.get('rotation', 0)),
        )
        err_msg = validate_draw_from_stack(_state, move)
        if err_msg:
            return jsonify({"ok": False, "error": err_msg})
        execute_draw_from_stack(_state, move)
        _state.switch_player()
        _check_drafting_done()
        return jsonify(ok(_state))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route('/api/move/bonus_chip', methods=['POST'])
def move_bonus_chip():
    """Aktion D: Aufgedecktes Bonusplättchen nehmen."""
    if _state is None:
        return jsonify(err("Kein aktives Spiel"))
    if not _both_start_placed():
        return jsonify(err("Beide Spieler müssen zuerst ihre Startkachel legen."))
    d = request.get_json()
    try:
        move = TakeBonusChipMove(factory_id=int(d['factory_id']))
        err_msg = validate_take_bonus_chip(_state, move)
        if err_msg:
            return jsonify({"ok": False, "error": err_msg})
        execute_take_bonus_chip(_state, move)
        _state.switch_player()  # Aktion D: Spielerwechsel
        _check_drafting_done()
        return jsonify(ok(_state))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route('/api/move/start_tile', methods=['POST'])
def move_start_tile():
    """Vorbereitung: Startkachel aus Display wählen und platzieren."""
    if _state is None:
        return jsonify(err("Kein aktives Spiel"))
    d = request.get_json()
    try:
        pi       = int(d['player'])
        tile_id  = int(d['tile_id'])
        slot_row = int(d['slot_row'])
        slot_col = int(d['slot_col'])
        rotation = int(d.get('rotation', 0))
        player   = _state.players[pi]

        if player.start_dome_tile is None:
            return jsonify({"ok": False, "error": "Startkachel bereits gelegt"})
            
        # Spieler wählt zwingend aus dem Display
        from engine.game import _find_in_display
        tile = _find_in_display(_state, tile_id)
        if tile is None:
            return jsonify({"ok": False, "error": f"Kachel {tile_id} nicht im Display"})
            
        # Kachel aus Display entfernen...
        _state.dome_display.remove(tile)
        # ...und Display sofort wieder vom Stapel auffüllen
        if _state.dome_tile_pool:
            _state.dome_display.append(_state.dome_tile_pool.pop(0))

        from engine.dome import ROTATION_MAP
        import copy
        tile = copy.deepcopy(tile)
        tile.apply_rotation(rotation)
        
        # Auf Raster platzieren und Sperre aufheben
        player.dome_grid.place_dome_tile(tile, slot_row, slot_col)
        player.start_dome_tile = None
        
        _state.log_event(
            f"{player.name}: Startkachel {tile_id} (aus Auslage) → "
            f"({slot_row},{slot_col}) rot={rotation}°"
        )
        return jsonify(ok(_state))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route('/api/tiling', methods=['POST'])
def tiling():
    """
    Phase 2: Einen Stein aus einer vollständigen Musterreihe auf die Kuppel legen.
    Löst automatisch Spezialplatten-Trigger und berechnet Punkte.
    """
    if _state is None:
        return jsonify(err("Kein aktives Spiel"))
    if _state.phase != "tiling":
        return jsonify(err("Nicht in der Tiling-Phase"))
    d = request.get_json()
    try:
        pi = int(d['player'])
        action = TilingAction(
            pattern_row=int(d['pattern_row']),
            slot_row=int(d['slot_row']),
            slot_col=int(d['slot_col']),
            space_index=int(d['space_index']),
            dome_tile_id=d.get('dome_tile_id'),
            rotation=int(d.get('rotation', 0)),
        )
        err_msg = validate_tiling_action(_state, pi, action)
        if err_msg:
            return jsonify({"ok": False, "error": err_msg})

        execute_full_tiling(_state, pi, action)

        return jsonify(ok(_state))
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})


@app.route('/api/tiling/bonus_chips', methods=['POST'])
def tiling_bonus_chips():
    """
    Phase 2: Bonusplättchen nutzen um eine unvollständige Musterreihe zu vervollständigen.
    Regelwerk S.8:
    - 2 gleichfarbige Chips = 1 fehlende Fliese ERSETZEN
    - 3 beliebige Chips = 1 fehlende Fliese ERSETZEN
    Muss mindestens 1 echte Fliese in der Reihe geben.
    """
    if _state is None:
        return jsonify(err("Kein aktives Spiel"))
    if _state.phase != "tiling":
        return jsonify(err("Nicht in der Tiling-Phase"))
    d = request.get_json()
    try:
        pi = int(d['player'])
        row_idx = int(d['pattern_row'])
        # chip_uses: Liste von Chip-Nutzungen, jede Nutzung ist:
        #   {"chip_ids": [id1, id2]}  (2 gleichfarbige) oder
        #   {"chip_ids": [id1, id2, id3]}  (3 beliebige)
        chip_uses = d.get('chip_uses', [])

        player = _state.players[pi]
        row = player.pattern_lines[row_idx]

        if not row.tiles:
            return jsonify({"ok": False, "error": "Musterreihe hat keine echten Fliesen"})
        if row.is_complete:
            return jsonify({"ok": False, "error": "Reihe ist bereits voll"})

        # Validierung: Chips existieren und sind nicht verbraucht
        used_chip_ids = set()
        for use in chip_uses:
            ids = use['chip_ids']
            if len(ids) not in (2, 3):
                return jsonify({"ok": False, "error": f"Ungültige Chip-Anzahl: {len(ids)}"})
            for cid in ids:
                if cid in used_chip_ids:
                    return jsonify({"ok": False, "error": f"Chip {cid} doppelt verwendet"})
                # Chip finden
                chip = next((c for c in player.bonus_chips if c and c.chip_id == cid), None)
                if chip is None:
                    return jsonify({"ok": False, "error": f"Chip {cid} nicht gefunden"})
                used_chip_ids.add(cid)

        if len(chip_uses) > row.spaces_left:
            return jsonify({"ok": False, "error": "Mehr Chip-Nutzungen als fehlende Fliesen"})

        # Chips als genutzt markieren (auf None setzen)
        for cid in used_chip_ids:
            for i, c in enumerate(player.bonus_chips):
                if c and c.chip_id == cid:
                    player.bonus_chips[i] = None
                    break

        # Fliesen zur Reihe hinzufügen
        color = row.color
        for _ in chip_uses:
            row.tiles.append(color)

        _state.log_event(
            f"{player.name}: {len(chip_uses)} Chip-Nutzung(en) → "
            f"Reihe {row_idx+1} {'komplett' if row.is_complete else 'teilweise'} gefüllt"
        )
        return jsonify(ok(_state))
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})


@app.route('/api/tiling/unplaceable', methods=['GET'])
def tiling_unplaceable():
    """
    Gibt alle unplatzierbaren Musterreihen zurück.
    Eine Reihe ist unplatzierbar wenn: Dome-Reihe voll (3 Platten) UND
    keine davon hat ein passendes freies Feld für die Reihenfarbe.
    Unplatzierbare Fliesen müssen auf die Strafleiste.
    """
    if _state is None:
        return jsonify(err("Kein aktives Spiel"))
    from engine.round_end import find_unplaceable_rows
    result = []
    for pi, player in enumerate(_state.players):
        unplaceable = find_unplaceable_rows(player)
        for row_idx in unplaceable:
            row = player.pattern_lines[row_idx]
            result.append({
                "player": pi,
                "pattern_row": row_idx,
                "color": row.color.value if row.color else None,
                "count": len(row.tiles),
            })
    return jsonify({"ok": True, "unplaceable": result})


@app.route('/api/tiling/move_to_floor', methods=['POST'])
def tiling_move_to_floor():
    """
    Phase 2: Unplatzierbare Fliesen explizit auf die Strafleiste verschieben.
    """
    if _state is None:
        return jsonify(err("Kein aktives Spiel"))
    d = request.get_json()
    try:
        pi = int(d['player'])
        row_idx = int(d['pattern_row'])
        player = _state.players[pi]
        row = player.pattern_lines[row_idx]

        if not row.tiles:
            return jsonify({"ok": False, "error": "Reihe ist leer"})

        tiles = list(row.tiles)
        row.tiles = []
        row.color = None
        overflow = player.add_broken(tiles)
        _state.tower.add(overflow)
        _state.log_event(
            f"{player.name}: {len(tiles)} unplatzierbare Fliesen → Strafleiste"
        )
        return jsonify(ok(_state))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route('/api/end_tiling', methods=['POST'])
def end_tiling():
    """
    Phase 2 abschliessen:
    1. Automatisch unplatzierbare Reihen auf Strafleiste
    2. Strafen berechnen (Strafleiste + Startspielerstein)
    3. Musterreihen aufräumen (vollständige löschen, unvollständige behalten)
    4. Neue Runde vorbereiten oder Spielende
    """
    if _state is None:
        return jsonify(err("Kein aktives Spiel"))
    try:
        from engine.round_end import (
            score_penalty, process_unplaceable_rows,
            find_unplaceable_rows
        )

        # 1. Prüfen ob noch platzierbare Tiling-Aktionen möglich sind
        # Regelwerk S.7: Unplatzierbare Reihen (keine passende Kuppelplatte) blockieren NICHT
        from engine.round_end import find_unplaceable_rows
        from engine.game import generate_tiling_actions
        for pi, player in enumerate(_state.players):
            for r in player.pattern_lines:
                if not r.is_complete:
                    continue
                ri = player.pattern_lines.index(r)
                # Prüfe ob es mindestens eine gültige Tiling-Aktion gibt
                actions = generate_tiling_actions(_state, pi)
                placeable = [a for a in actions if a.pattern_row == ri]
                if placeable:
                    return jsonify({
                        "ok": False,
                        "error": f"{player.name}: Reihe {ri+1} kann noch gelegt werden."
                    })

        # 2. Unplatzierbare Reihen automatisch auf Strafleiste
        for player in _state.players:
            process_unplaceable_rows(player, _state.tower, _state)

        # 3. Strafen berechnen und anwenden
        for player in _state.players:
            pen = score_penalty(player)
            if pen < 0:
                player.apply_score(pen)
                broken = player.clear_broken()
                _state.tower.add(broken)
                _state.log_event(f"{player.name}: Strafe {pen} Pkt → {player.score} Gesamt")
            else:
                player.clear_broken()

        # 4. Runde beenden oder Spiel beenden
        if _state.round_number >= NUM_ROUNDS:
            _state.phase = "end"
            _state.log_event(
                f"Spiel beendet! "
                f"{_state.players[0].name}: {_state.players[0].score} Pkt | "
                f"{_state.players[1].name}: {_state.players[1].score} Pkt"
            )
        else:
            # Phase 3: Display auf 3 auffüllen
            while len(_state.dome_display) < 3 and _state.dome_tile_pool:
                _state.dome_display.append(_state.dome_tile_pool.pop(0))
            setup_new_round(_state)
            _state.phase = "drafting"
            _state.log_event(f"Runde {_state.round_number} beginnt.")

        return jsonify(ok(_state))
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})


def _can_act(state, pi: int) -> bool:
    """
    Prüft ob der Spieler noch irgendeine der 4 Aktionen ausführen kann.
    Regelwerk S.7: Nur wenn keine Aktion möglich → Passen erlaubt/erzwungen.
    """
    p = state.players[pi]

    # Aktion A: Kuppelplatte nehmen
    # Nur möglich wenn:
    # - Nicht Runde 5
    # - Spielerplättchen noch verfügbar
    # - Noch freie Slots in der Kuppel
    # - Startkachel bereits gelegt (sonst nur Startkachel-Pflicht, kein echter Zug)
    # - Display ODER Stapel nicht leer
    if (state.round_number < 5
            and p.start_dome_tile is None          # Startkachel bereits gelegt
            and not p.has_used_all_tokens(state.round_number)
            and p.can_place_dome_tile(state.round_number)
            and (state.dome_display or state.dome_tile_pool)):
        return True

    # Aktion B: Fliesen von Sonnenbereich irgendeiner Fabrik
    if any(f.sun_tiles for f in state.factories):
        return True
    if state.large_factory.sun_tiles:
        return True

    # Aktion C: Fliesen von Mondbereich
    if any(f.moon_top_colors() for f in state.factories):
        return True
    if state.large_factory.moon_colors():
        return True

    # Aktion D: Aufgedecktes Bonusplättchen nehmen
    # Nur wenn Spieler noch nicht 2 Chips diese Runde genommen hat
    if (p.can_take_bonus_chip()
            and any(f.bonus_chip_revealed and f.bonus_chip is not None
                    for f in state.factories)):
        return True

    return False


@app.route('/api/pass', methods=['POST'])
def pass_turn():
    """
    Spieler passt seinen Zug.
    Regelwerk S.7: Nur erlaubt wenn keine der Aktionen A/B/C/D möglich ist.
    """
    if _state is None:
        return jsonify(err("Kein aktives Spiel"))
    if _state.phase != "drafting":
        return jsonify(err("Passen nur in Phase 1 möglich"))

    pi = _state.current_player
    p = _state.players[pi]

    # Prüfe ob Passen erlaubt
    if _can_act(_state, pi):
        # Ermittle welche Aktionen noch möglich sind für nützliche Fehlermeldung
        possible = []
        if (not p.has_used_all_tokens(_state.round_number)
                and p.can_place_dome_tile(_state.round_number)
                and (_state.dome_display or _state.dome_tile_pool)):
            possible.append("A (Kuppelplatte)")
        if any(f.sun_tiles for f in _state.factories) or _state.large_factory.sun_tiles:
            possible.append("B (Sonne)")
        moon_colors = set()
        for f in _state.factories:
            moon_colors.update(c.value for c in f.moon_top_colors())
        moon_colors.update(c.value for c in _state.large_factory.moon_colors())
        if moon_colors:
            possible.append(f"C (Mond: {', '.join(sorted(moon_colors))})")
        if (p.can_take_bonus_chip()
                and any(f.bonus_chip_revealed for f in _state.factories)):
            possible.append("D (Bonusplättchen)")
        return jsonify({
            "ok": False,
            "error": f"Passen nicht erlaubt — noch möglich: {'; '.join(possible)}"
        })

    _state.log_event(f"{p.name}: passt (keine Aktion möglich)")
    _state.switch_player()
    _check_drafting_done()
    return jsonify(ok(_state))


def _check_drafting_done():
    """Wechselt Phase wenn alle Fabriken leer und Tokens verbraucht."""
    if check_drafting_complete(_state):
        _state.phase = "tiling"
        process_unplaceable_rows(_state.players[0], _state.tower, _state)
        process_unplaceable_rows(_state.players[1], _state.tower, _state)
        _state.log_event("Tiling-Phase beginnt.")


@app.route('/api/move/pass', methods=['POST'])
def move_pass():
    """
    Passen: Nur erlaubt wenn der Spieler keine der 4 Aktionen ausführen kann.
    Laut Regelwerk S.7: Andernfalls darf nicht gepasst werden.
    """
    if _state is None:
        return jsonify(err("Kein aktives Spiel"))
    if not _both_start_placed():
        return jsonify(err("Beide Spieler müssen zuerst ihre Startkachel legen."))
    if _state.phase != "drafting":
        return jsonify(err("Passen nur in Phase 1 möglich."))

    player = _state.active_player
    # Prüfe ob der Spieler wirklich keine Aktion hat
    can_stone = bool(generate_valid_moves(_state))
    can_dome  = bool(generate_dome_moves(_state)) if not player.has_used_all_tokens(_state.round_number) else False
    can_chip  = bool(generate_bonus_chip_moves(_state))
    # Aktion C: gibt es Moon-Tops?
    moon_tops = set()
    for f in _state.factories:
        moon_tops |= f.moon_top_colors()
    for c in _state.large_factory.moon_colors():
        moon_tops.add(c)
    can_moon_c = bool(moon_tops) and not player.has_used_all_tokens(_state.round_number) == False

    if can_stone or can_dome or can_chip:
        return jsonify({"ok": False,
                        "error": "Passen nicht erlaubt — es gibt noch gültige Aktionen."})

    _state.log_event(f"{player.name} passt.")
    _state.switch_player()
    _check_drafting_done()
    return jsonify(ok(_state))


@app.route('/api/scoring_tiles', methods=['GET'])
def get_scoring_tiles():
    """Gibt alle 8 verfügbaren Wertungsplatten zurück."""
    from engine.scoring import ALL_SCORING_TILES
    return jsonify({
        "ok": True,
        "tiles": [{"id": t.id, "name": t.name, "description": t.description, "emoji": t.emoji}
                  for t in ALL_SCORING_TILES]
    })


@app.route('/api/scoring_tiles/select', methods=['POST'])
def select_scoring_tiles():
    """Spieler 1 wählt 3 Wertungsplatten für das Spiel."""
    if _state is None:
        return jsonify(err("Kein aktives Spiel"))
    d = request.get_json()
    ids = d.get('ids', [])
    if len(ids) != 3:
        return jsonify({"ok": False, "error": "Genau 3 Wertungsplatten wählen"})
    from engine.scoring import ALL_SCORING_TILES
    valid_ids = {t.id for t in ALL_SCORING_TILES}
    if not all(i in valid_ids for i in ids):
        return jsonify({"ok": False, "error": "Ungültige Wertungsplatten-IDs"})
    if len(set(ids)) != 3:
        return jsonify({"ok": False, "error": "Keine Duplikate erlaubt"})
    _state.scoring_tile_ids = list(ids)
    _state.log_event(f"Wertungsplatten gewählt: {ids}")
    return jsonify(ok(_state))


@app.route('/api/end_scoring', methods=['POST'])
def end_scoring():
    """Berechnet die Endwertung nach Runde 5."""
    if _state is None:
        return jsonify(err("Kein aktives Spiel"))
    if _state.phase != "end":
        return jsonify({"ok": False, "error": "Spiel noch nicht beendet"})
    
    from engine.scoring import calculate_end_scoring, ALL_SCORING_TILES
    
    # --- NEU: Standard-Platten (H/V/D) laden, falls das Modal nie geöffnet wurde ---
    t_ids = getattr(_state, "scoring_tile_ids", [0, 1, 2])
    
    results = {}
    for pi, player in enumerate(_state.players):
        res = calculate_end_scoring(player, t_ids)  # <--- Hier die geladenen Platten nutzen!
        player.apply_score(res["total"])
        # --- DER FIX: Wir machen alle Keys zu Strings, damit jsonify nicht abstürzt ---
        safe_res = {str(k): v for k, v in res.items()}
        results[pi] = safe_res
        
        _state.log_event(
            f"🏆 {player.name}: Endwertung +{res['total']} Pkt → {player.score} Gesamt"
        )
        for tid, detail in res.items():
            if tid == "total":
                continue
            _state.log_event(
                f"   {detail['emoji']} {detail['name']}: {detail['score']:+d} Pkt"
            )
            
    _state.phase = "final"
    # jsonify kommt jetzt perfekt damit klar!
    return jsonify({"ok": True, "state": serialize_state(_state), "results": {
        str(pi): r for pi, r in results.items()
    }})

@app.route('/api/stack/peek', methods=['POST'])  # <--- DIESE ZEILE HAT GEFEHLT!
def stack_peek():
    """
    Zieht n Karten verdeckt vom Stapel und gibt sie zurück (noch nicht platziert).
    Die Karten bleiben im Memory bis der Spieler eine wählt (via /move/dome_stack).
    """
    if _state is None:
        return jsonify(err("Kein aktives Spiel"))
    d = request.get_json()
    try:
        n = int(d.get('num', 1))
        n = min(n, len(_state.dome_tile_pool))
        if n < 1:
            return jsonify({"ok": False, "error": "Keine Karten auf dem Stapel"})
        # Peek: return top n tiles WITHOUT removing them yet
        # Player will confirm via /move/dome_stack which removes them
        from engine.serializer import serialize_dome_tile
        tiles = [serialize_dome_tile(t) for t in _state.dome_tile_pool[:n]]
        return jsonify({"ok": True, "tiles": tiles})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


if __name__ == '__main__':
    print("Mosaic-AI Server läuft auf http://localhost:5000")
    app.run(debug=True, port=5000)
