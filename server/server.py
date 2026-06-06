"""
Mosaic-AI — Flask API Server (Clean Architecture)

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
from engine.game import Game
from engine.round_end import TilingAction

STATIC_DIR = Path(__file__).resolve().parent / 'static'
app = Flask(__name__, static_folder=str(STATIC_DIR))
try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    pass

# ── Global game state ────────────────────────────────────────────────────────
_game = Game()

def ok() -> dict:
    # Holt sich den State immer frisch aus der Game-Instanz
    return {"ok": True, "state": serialize_state(_game.state)}

def err(msg: str) -> dict:
    return {"ok": False, "error": msg}

def _both_start_placed() -> bool:
    if _game.state is None: return False
    return all(p.start_dome_tile is None for p in _game.state.players)

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
    global _game
    data = request.get_json(silent=True) or {}
    names = data.get('names', ['Spieler 1', 'Spieler 2'])
    seed  = data.get('seed', None)
    
    _game = Game()
    _game.start(player_names=names, seed=seed)
    return jsonify(ok())


@app.route('/api/state', methods=['GET'])
def get_state():
    if _game.state is None:
        return jsonify(err("Kein aktives Spiel"))
    return jsonify(ok())


@app.route('/api/move/stone', methods=['POST'])
def move_stone():
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    if not _both_start_placed(): return jsonify(err("Startkacheln fehlen."))
    
    d = request.get_json()
    try:
        # --- ROBUSTE HANDHABUNG VON AKTION C ---
        # Wenn factory_id fehlt oder None ist, ist es ein globaler Mond-Zug.
        raw_factory_id = d.get('factory_id')
        factory_id = int(raw_factory_id) if raw_factory_id is not None else None
        
        move = Move(
            take=TakeAction(
                source=source(d['source']), 
                color=color(d['color']),
                factory_id=factory_id, 
                moon_order=[color(c) for c in d.get('moon_order', [])]
            ),
            place=PlaceAction(row_index=int(d['row'])),
        )
        
        # apply() in deiner game.py muss jetzt den Fall factory_id=None 
        # als Aktion C erkennen (hast du ja bereits implementiert)
        _game.apply(move)
        return jsonify(ok())
    except ValueError as e:
        return jsonify(err(str(e)))


@app.route('/api/move/dome', methods=['POST'])
def move_dome():
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    if not _both_start_placed(): return jsonify(err("Startkacheln fehlen."))
    
    d = request.get_json()
    try:
        move = PlaceDomeTileMove(
            dome_tile_id=int(d['tile_id']),
            slot_row=int(d['slot_row']),
            slot_col=int(d['slot_col']),
            rotation=int(d.get('rotation', 0)),
        )
        _game.apply(move)
        return jsonify(ok())
    except ValueError as e:
        return jsonify(err(str(e)))
    except Exception as e:
        return jsonify(err(str(e)))


@app.route('/api/move/dome_stack', methods=['POST'])
def move_dome_stack():
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    if not _both_start_placed(): return jsonify(err("Startkacheln fehlen."))
    
    d = request.get_json()
    try:
        move = DrawFromStackMove(
            num_drawn=int(d['num_drawn']),
            chosen_id=int(d['chosen_id']),
            slot_row=int(d['slot_row']),
            slot_col=int(d['slot_col']),
            rotation=int(d.get('rotation', 0)),
        )
        _game.apply(move)
        return jsonify(ok())
    except ValueError as e:
        return jsonify(err(str(e)))


@app.route('/api/move/bonus_chip', methods=['POST'])
def move_bonus_chip():
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    if not _both_start_placed(): return jsonify(err("Startkacheln fehlen."))
    
    d = request.get_json()
    try:
        move = TakeBonusChipMove(factory_id=int(d['factory_id']))
        _game.apply(move)
        return jsonify(ok())
    except ValueError as e:
        return jsonify(err(str(e)))


@app.route('/api/move/start_tile', methods=['POST'])
def move_start_tile():
    try:
        d = request.json
        _game.apply_start_placement(
            player_idx = int(d['player']),
            tile_id    = int(d['tile_id']),
            row        = int(d['slot_row']),
            col        = int(d['slot_col']),
            rot        = int(d.get('rotation', 0)),
        )
        return jsonify(ok())
    except Exception as e:
        return jsonify(err(str(e)))


@app.route('/api/tiling', methods=['POST'])
def tiling():
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    if _game.state.phase != "tiling": return jsonify(err("Nicht in der Tiling-Phase"))
    
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
        
        _game.apply_single_tiling(pi, action)
        return jsonify(ok())
    except ValueError as e:
        return jsonify(err(str(e)))


@app.route('/api/tiling/bonus_chips', methods=['POST'])
def tiling_bonus_chips():
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    if _game.state.phase != "tiling": return jsonify(err("Nicht in der Tiling-Phase"))
    d = request.get_json()
    try:
        pi = int(d['player'])
        row_idx = int(d['pattern_row'])
        chip_uses = d.get('chip_uses', [])

        player = _game.state.players[pi]
        row = player.pattern_lines[row_idx]

        if not row.tiles: return jsonify(err("Musterreihe hat keine echten Fliesen"))
        if row.is_complete: return jsonify(err("Reihe ist bereits voll"))

        used_chip_ids = set()
        for use in chip_uses:
            ids = use['chip_ids']
            if len(ids) not in (2, 3): return jsonify(err(f"Ungültige Chip-Anzahl: {len(ids)}"))
            for cid in ids:
                if cid in used_chip_ids: return jsonify(err(f"Chip {cid} doppelt verwendet"))
                chip = next((c for c in player.bonus_chips if c and c.chip_id == cid), None)
                if chip is None: return jsonify(err(f"Chip {cid} nicht gefunden"))
                used_chip_ids.add(cid)

        if len(chip_uses) > row.spaces_left:
            return jsonify(err("Mehr Chip-Nutzungen als fehlende Fliesen"))

        for cid in used_chip_ids:
            for i, c in enumerate(player.bonus_chips):
                if c and c.chip_id == cid:
                    player.bonus_chips[i] = None
                    break

        color = row.color
        for _ in chip_uses:
            row.tiles.append(color)

        _game.state.log_event(
            f"{player.name}: {len(chip_uses)} Chip-Nutzung(en) → "
            f"Reihe {row_idx+1} {'komplett' if row.is_complete else 'teilweise'} gefüllt"
        )
        return jsonify(ok())
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify(err(str(e)))


@app.route('/api/tiling/unplaceable', methods=['GET'])
def tiling_unplaceable():
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    from engine.round_end import find_unplaceable_rows
    result = []
    for pi, player in enumerate(_game.state.players):
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
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    d = request.get_json()
    try:
        pi = int(d['player'])
        row_idx = int(d['pattern_row'])
        player = _game.state.players[pi]
        row = player.pattern_lines[row_idx]

        if not row.tiles: return jsonify(err("Reihe ist leer"))

        tiles = list(row.tiles)
        row.tiles = []
        row.color = None
        overflow = player.add_broken(tiles)
        _game.state.tower.add(overflow)
        _game.state.log_event(
            f"{player.name}: {len(tiles)} unplatzierbare Fliesen → Strafleiste"
        )
        return jsonify(ok())
    except Exception as e:
        return jsonify(err(str(e)))


@app.route('/api/end_tiling', methods=['POST'])
def end_tiling():
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    try:
        _game.apply({"type": "end_tiling"})
        return jsonify(ok())
    except Exception as e:
        return jsonify(err(str(e)))

@app.route('/api/move/pass', methods=['POST'])
def move_pass():
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    if not _both_start_placed(): return jsonify(err("Startkacheln fehlen."))
    if _game.state.phase != "drafting": return jsonify(err("Passen nur in Phase 1 möglich."))

    # Validierung: Darf der Spieler passen?
    if len(_game.valid_moves()) > 0:
        return jsonify(err("Passen nicht erlaubt — es gibt noch gültige Aktionen."))

    # --- HIER IST DIE MAGIE ---
    # Wir übergeben das Passen einfach an die Engine. 
    # game.py kümmert sich jetzt um Spielerwechsel, Log-Eintrag und den Phasenwechsel!
    try:
        _game.apply({"type": "pass"})
        return jsonify(ok())
    except ValueError as e:
        return jsonify(err(str(e)))


@app.route('/api/scoring_tiles', methods=['GET'])
def get_scoring_tiles():
    from engine.scoring import ALL_SCORING_TILES
    return jsonify({
        "ok": True,
        "tiles": [{"id": t.id, "name": t.name, "description": t.description, "emoji": t.emoji}
                  for t in ALL_SCORING_TILES]
    })


@app.route('/api/scoring_tiles/select', methods=['POST'])
def select_scoring_tiles():
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    d = request.get_json()
    ids = d.get('ids', [])
    if len(ids) != 3: return jsonify(err("Genau 3 Wertungsplatten wählen"))
    
    from engine.scoring import ALL_SCORING_TILES
    valid_ids = {t.id for t in ALL_SCORING_TILES}
    if not all(i in valid_ids for i in ids): return jsonify(err("Ungültige Wertungsplatten-IDs"))
    if len(set(ids)) != 3: return jsonify(err("Keine Duplikate erlaubt"))
    
    _game.state.scoring_tile_ids = list(ids)
    _game.state.log_event(f"Wertungsplatten gewählt: {ids}")
    return jsonify(ok())


@app.route('/api/end_scoring', methods=['POST'])
def end_scoring():
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    if _game.state.phase != "end": return jsonify(err("Spiel noch nicht beendet"))
    try:
        results = _game._calculate_end_scoring()
        return jsonify({"ok": True, **results})
    except Exception as e:
        return jsonify(err(str(e)))

@app.route('/api/stack/peek', methods=['POST'])
def stack_peek():
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    d = request.get_json()
    try:
        n = int(d.get('num', 1))
        n = min(n, len(_game.state.dome_tile_pool))
        if n < 1: return jsonify(err("Keine Karten auf dem Stapel"))
        
        from engine.serializer import serialize_dome_tile
        tiles = [serialize_dome_tile(t) for t in _game.state.dome_tile_pool[:n]]
        return jsonify({"ok": True, "tiles": tiles})
    except Exception as e:
        return jsonify(err(str(e)))


if __name__ == '__main__':
    print("Mosaic-AI Server läuft auf http://localhost:5000")
    app.run(debug=True, port=5000)