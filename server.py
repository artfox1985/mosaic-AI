"""
Mosaic-AI — Flask API Server (Clean Architecture)

Endpoints:
  POST /api/new_game          — Neues Spiel starten
  GET  /api/state             — Aktuellen State abrufen
  POST /api/move/stone        — Stein-Zug (Aktion B/C)
  POST /api/move/dome         — Kuppelplatte aus Ablage (Aktion A)
  POST /api/move/dome_stack   — Kuppelplatte vom Stapel (Aktion A, -1Pkt)
  POST /api/move/bonus_chip   — Bonusplättchen nehmen (Aktion D)
  POST /api/move/start_tile   — Startkachel platzieren (Vorbereitung)
  POST /api/tiling            — Tiling-Aktion (Phase 2)
  POST /api/end_tiling        — Tiling-Phase abschließen
  GET  /api/ai/config         — KI-Konfiguration abrufen
  POST /api/ai/config         — Schwierigkeit setzen (easy/medium/hard/expert)
  POST /api/ai/move           — KI führt ihren nächsten Zug aus
  GET  /api/ai/suggest        — Mentor Mode: Top-3 KI-Züge mit Win-Wahrscheinlichkeit

Alle Responses: {"ok": true, "state": {...}} oder {"ok": false, "error": "..."}
"""

import sys
import os
import json as _json
import datetime as _dt
from pathlib import Path

# Stelle sicher dass der Hauptordner im Python-Path ist
BASE_DIR = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, BASE_DIR)

from flask import Flask, request, jsonify, send_from_directory
import threading

from engine.setup import GameState, setup_new_game, setup_new_round, NUM_ROUNDS
from engine.serializer import serialize_state
from engine.tile import TileColor
from engine.moves import (
    Move, TakeAction, PlaceAction, TakeSource,
    PlaceDomeTileMove, DrawFromStackMove, TakeBonusChipMove
)
from engine.game import Game, generate_tiling_actions
from engine.round_end import TilingAction

STATIC_DIR = Path(__file__).resolve().parent / 'static'
app = Flask(__name__, static_folder=str(STATIC_DIR))
try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    pass

# ── MIME-Types fix (besonders Windows) ───────────────────────────────────────
# Auf Windows liest Pythons mimetypes-Modul die Registry, wo .js oft OHNE
# charset=utf-8 registriert ist. Dann rät der Browser die Kodierung falsch und
# Multibyte-Zeichen (z.B. — oder Umlaute) zerbrechen → "unescaped line break".
# Wir erzwingen die korrekten Typen unabhängig vom OS.
import mimetypes as _mt
_mt.add_type('text/javascript', '.js')
_mt.add_type('text/css', '.css')
_mt.add_type('application/json', '.json')

@app.after_request
def _ensure_utf8(resp):
    ct = resp.headers.get('Content-Type', '')
    # Bei Text-/JS-/CSS-/JSON-Antworten charset=utf-8 garantieren
    if ('charset' not in ct.lower()) and any(
        ct.startswith(p) for p in
        ('text/', 'application/javascript', 'application/json')
    ):
        resp.headers['Content-Type'] = ct + '; charset=utf-8'
    return resp

# ── Global game state ────────────────────────────────────────────────────────
_game = Game()
_game_log_path: Path | None = None   # Pfad zur aktuellen Log-Datei
LOG_DIR = Path(__file__).parent / "static" / "log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ── KI-Konfiguration ─────────────────────────────────────────────────────────
_ai_agent    = None        # AlphaZeroAgent oder HeuristicMCTSAgent
_ai_player   = None        # 0 oder 1 — welcher Spieler ist die KI
_ai_sims     = 300         # MCTS-Simulationen der Rust-KI (rust-Pfad)
_last_ai_log = None        # voller Such-Trace des zuletzt gespielten KI-Drafting-Zugs
_ai_lock     = threading.Lock()
_ai_debug_history = []     # Liste aller KI-Zug-Analysen des aktuellen Spiels

# Difficulty Presets — werden befüllt wenn genug Modell-Generationen vorhanden sind.
# Aktuell: direkt model_version + sims übergeben über /api/ai/config
# Format: {"model": "<version>", "sims": <int>}
DIFFICULTY_PRESETS = {
    "easy":   None,   # TODO: z.B. {"model": "v1", "sims": 10}
    "medium": None,   # TODO: z.B. {"model": "v2", "sims": 20}
    "hard":   None,   # TODO: z.B. {"model": "v3", "sims": 50}
    "expert": None,   # TODO: z.B. {"model": "v5", "sims": 100}
    # Fallback wenn kein Preset: neuestes verfügbares Modell mit 40 Sims
    "_default": {"model": "v2", "sims": 40},
}

def _resolve_difficulty(difficulty: str, model: str = None, sims: int = None) -> dict:
    """
    Löst Schwierigkeit auf. Priorität:
    1. Explizite model/sims Parameter
    2. Preset wenn vorhanden
    3. _default Preset
    """
    if model is not None and sims is not None:
        return {"model": model, "sims": sims}
    preset = DIFFICULTY_PRESETS.get(difficulty)
    if preset is not None:
        return preset
    return DIFFICULTY_PRESETS["_default"]

def _init_ai(model_version: str, sims: int) -> None:
    """Initialisiert den KI-Agenten (lazy — nur wenn Modell vorhanden).

    Spezialfall: model_version == 'heuristic' wählt gezielt den
    HeuristicMCTSAgent (reines MCTS ohne Netz) — zum Prüfen der Heuristik.
    """
    global _ai_agent

    # Gezielte Heuristik-Auswahl (kein Netz, nur MCTS + Greedy-Rollouts)
    if str(model_version).lower() in ("heuristic", "heuristik", "mcts"):
        from agents.mcts import HeuristicMCTSAgent
        _ai_agent = HeuristicMCTSAgent(simulations=sims, rollout_depth=1,
                                       dynamic_sims="play")
        _ai_agent.set_env(_wrap_env())
        return

    try:
        from agents.alphazero import AlphaZeroAgent
        from config import INPUT_SIZE
        _ai_agent = AlphaZeroAgent(
            model_version=model_version,
            input_size=INPUT_SIZE,
            simulations=sims,
            dynamic_sims="play",   # Stärke: früh (viele Optionen) mehr Suche
        )
        _ai_agent.set_env(_wrap_env())
    except FileNotFoundError:
        # Modell nicht vorhanden → Fallback auf MCTS
        from agents.mcts import HeuristicMCTSAgent
        _ai_agent = HeuristicMCTSAgent(simulations=sims, rollout_depth=1,
                                       dynamic_sims="play")
        _ai_agent.set_env(_wrap_env())

def _wrap_env():
    """Erstellt ein MosaicEnv das den aktuellen _game State spiegelt."""
    from agents.agent_env import MosaicEnv
    env = MosaicEnv()
    env._game = _game
    env.state  = _game.state
    return env

def ok() -> dict:
    # Rust-Engine aktiv? Dann State aus der PyGame-Instanz.
    if _rust is not None:
        return {"ok": True, "state": _json.loads(_rust.state_json())}
    # Holt sich den State immer frisch aus der Game-Instanz
    return {"ok": True, "state": serialize_state(_game.state)}


def _flush_game_log() -> None:
    """Schreibt neue state.log Einträge in die Log-Datei."""
    global _game_log_path
    if _rust is not None:
        _rust_flush_log()
        return
    if _game_log_path is None or _game is None or _game.state is None:
        return
    if not hasattr(_game.state, '_logged_count'):
        _game.state._logged_count = 0
    new_entries = _game.state.log[_game.state._logged_count:]
    if new_entries:
        try:
            with open(_game_log_path, 'a', encoding='utf-8') as lf:
                for entry in new_entries:
                    lf.write(f"{entry}\n")
            _game.state._logged_count = len(_game.state.log)
        except Exception:
            pass


def err(msg: str) -> dict:
    return {"ok": False, "error": msg}

def _both_start_placed() -> bool:
    if _rust is not None:
        return _rust.both_start_placed()
    if _game.state is None: return False
    return all(p.start_dome_tile is None for p in _game.state.players)

def color(v: str) -> TileColor:
    for c in TileColor:
        if c.value == v:
            return c
    raise ValueError(f"Unbekannte Farbe: {v}")

def source(v: str) -> TakeSource:
    return TakeSource[v]


# ── Rust-Engine-Pfad (Mensch-vs-Mensch, Branch rust-engine) ──────────────────
# Wenn ein Spiel mit engine="rust" gestartet wird, hält _rust eine
# mosaic_rust.PyGame-Instanz und die Routen verzweigen darauf. Der bestehende
# Python-Flow (_game) bleibt unverändert.
try:
    import mosaic_rust as _mr
except ImportError:
    _mr = None

_rust = None        # mosaic_rust.PyGame oder None
_rust_logged = 0    # bereits in die Logdatei geschriebene Log-Zeilen

def _rust_active() -> bool:
    return _rust is not None

def _rust_state() -> dict:
    return _json.loads(_rust.state_json())

def _rust_ok(extra: dict | None = None):
    r = {"ok": True, "state": _rust_state()}
    if extra:
        r.update(extra)
    return jsonify(r)

def _rust_flush_log() -> None:
    global _rust_logged
    if _game_log_path is None or _rust is None:
        return
    new = _rust.log_since(_rust_logged)
    if new:
        try:
            with open(_game_log_path, 'a', encoding='utf-8') as lf:
                for e in new:
                    lf.write(f"{e}\n")
            _rust_logged = _rust.log_len()
        except Exception:
            pass


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')


@app.route('/debug')
def debug_page():
    return send_from_directory(STATIC_DIR, 'debug.html')


@app.route('/api/new_game', methods=['POST'])
def new_game():
    global _game, _ai_agent, _ai_player
    global _ai_debug_history
    _ai_debug_history = []   # Historie für neues Spiel zurücksetzen
    data = request.get_json(silent=True) or {}
    names      = data.get('names', ['Spieler 1', 'Spieler 2'])
    seed       = data.get('seed', None)
    ai_enabled = data.get('ai_enabled', False)
    difficulty = data.get('difficulty', 'medium')
    ai_side    = data.get('ai_side', 1)   # 0 = KI ist P1, 1 = KI ist P2

    import random as _random
    fp_raw = data.get('first_player', None)
    first_player = _random.randint(0, 1) if fp_raw is None else int(fp_raw)
    # Seed immer explizit setzen für Reproduzierbarkeit
    if seed is None:
        seed = _random.randint(0, 999999)

    global _rust, _rust_logged, _ai_sims

    # In diesem Branch ist Rust die einzige Engine. KI (optional) läuft als
    # Rust-MCTS direkt auf der PyGame-Instanz — kein Python-Agent.
    if _mr is None:
        return jsonify(err("Rust-Engine (mosaic_rust) ist nicht installiert. "
                           "Bitte im rust/-Verzeichnis `pip install .` ausführen."))
    _rust = _mr.PyGame((names[0], names[1]), first_player=first_player, seed=seed)
    _rust_logged = 0
    _game = Game()        # Platzhalter; ungenutzt
    _ai_agent  = None     # rust-Pfad nutzt keinen Python-Agenten
    seed = _rust.seed()

    if ai_enabled:
        preset = _resolve_difficulty(difficulty, data.get('model'), data.get('sims'))
        _ai_player = int(ai_side)
        # Basis-Sims kommt aus dem Start-Modal; dynamic_sims skaliert davon hoch.
        _ai_sims   = int(preset.get('sims') or 100)
    else:
        _ai_player = None

    # Log-Datei für dieses Spiel erstellen
    global _game_log_path
    timestamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    actual_seed = getattr(_game.state, '_seed', seed)
    _game_log_path = LOG_DIR / f"game_{timestamp}_seed{actual_seed}.log"
    with open(_game_log_path, 'w', encoding='utf-8') as lf:
        meta = {
            "timestamp":    timestamp,
            "seed":         actual_seed,
            "players":      names,
            "first_player": first_player,
            "ai_enabled":   ai_enabled,
            "ai_player":    _ai_player,
            "ai_model":     data.get('model', None),
            "ai_sims":      data.get('sims', None),
        }
        lf.write(f"# MOSAIC GAME LOG\n")
        lf.write(f"# {_json.dumps(meta, ensure_ascii=False)}\n")
        lf.write(f"# {'='*60}\n")

    response = ok()
    response['ai_enabled']  = ai_enabled
    response['ai_player']   = _ai_player
    response['log_file']    = _game_log_path.name
    response['seed']        = actual_seed
    return jsonify(response)


@app.route('/api/state', methods=['GET'])
def get_state():
    if _rust_active():
        return jsonify(ok())
    if _game.state is None:
        return jsonify(err("Kein aktives Spiel"))
    return jsonify(ok())


@app.route('/api/move/stone', methods=['POST'])
def move_stone():
    if _rust_active():
        if not _both_start_placed(): return jsonify(err("Startkacheln fehlen."))
        d = request.get_json()
        try:
            raw = d.get('factory_id')
            fid = int(raw) if raw is not None else None
            _rust.apply_stone(d['source'], d['color'], int(d['row']),
                              fid, list(d.get('moon_order', [])))
            _flush_game_log()
            return jsonify(ok())
        except Exception as e:
            return jsonify(err(str(e)))
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
        _flush_game_log()
        return jsonify(ok())
    except ValueError as e:
        return jsonify(err(str(e)))


@app.route('/api/move/dome', methods=['POST'])
def move_dome():
    if _rust_active():
        if not _both_start_placed(): return jsonify(err("Startkacheln fehlen."))
        d = request.get_json()
        try:
            _rust.apply_dome(int(d['tile_id']), int(d['slot_row']),
                             int(d['slot_col']), int(d.get('rotation', 0)))
            _flush_game_log()
            return jsonify(ok())
        except Exception as e:
            return jsonify(err(str(e) or "Zug abgelehnt."))
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
        _flush_game_log()
        return jsonify(ok())
    except ValueError as e:
        return jsonify(err(str(e)))
    except AssertionError:
        return jsonify(err("Ungültige Slot-Position für die Kuppelplatte."))
    except Exception as e:
        return jsonify(err(str(e) or "Zug abgelehnt."))


@app.route('/api/move/dome_stack', methods=['POST'])
def move_dome_stack():
    if _rust_active():
        if not _both_start_placed(): return jsonify(err("Startkacheln fehlen."))
        d = request.get_json()
        try:
            _rust.apply_dome_stack(int(d['num_drawn']), int(d['chosen_id']),
                                   int(d['slot_row']), int(d['slot_col']),
                                   int(d.get('rotation', 0)))
            _flush_game_log()
            return jsonify(ok())
        except Exception as e:
            return jsonify(err(str(e) or "Zug abgelehnt."))
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
        _flush_game_log()
        return jsonify(ok())
    except ValueError as e:
        return jsonify(err(str(e)))
    except AssertionError:
        # DrawFromStackMove.__post_init__ asserted ohne Message (z.B. slot_row
        # außerhalb 0..2). Klare Meldung statt leerem String ans Frontend.
        return jsonify(err("Ungültige Slot-Position für die Kuppelplatte."))


@app.route('/api/move/bonus_chip', methods=['POST'])
def move_bonus_chip():
    if _rust_active():
        if not _both_start_placed(): return jsonify(err("Startkacheln fehlen."))
        d = request.get_json()
        try:
            _rust.apply_bonus_chip(int(d['factory_id']))
            _flush_game_log()
            return jsonify(ok())
        except Exception as e:
            return jsonify(err(str(e)))
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    if not _both_start_placed(): return jsonify(err("Startkacheln fehlen."))

    d = request.get_json()
    try:
        move = TakeBonusChipMove(factory_id=int(d['factory_id']))
        _game.apply(move)
        _flush_game_log()
        return jsonify(ok())
    except ValueError as e:
        return jsonify(err(str(e)))


@app.route('/api/move/start_tile', methods=['POST'])
def move_start_tile():
    if _rust_active():
        d = request.json
        try:
            _rust.apply_start_tile(int(d['player']), int(d['tile_id']),
                                   int(d['slot_row']), int(d['slot_col']),
                                   int(d.get('rotation', 0)))
            _flush_game_log()
            return jsonify(ok())
        except Exception as e:
            return jsonify(err(str(e) or "Zug abgelehnt."))
    try:
        d = request.json
        _game.apply_start_placement(
            player_idx = int(d['player']),
            tile_id    = int(d['tile_id']),
            row        = int(d['slot_row']),
            col        = int(d['slot_col']),
            rot        = int(d.get('rotation', 0)),
        )
        _flush_game_log()
        return jsonify(ok())
    except AssertionError:
        return jsonify(err("Ungültige Slot-Position für die Startkuppelplatte."))
    except Exception as e:
        return jsonify(err(str(e) or "Zug abgelehnt."))


@app.route('/api/tiling', methods=['POST'])
def tiling():
    global AI_ENABLED, _ai_player
    if _rust_active():
        if _rust.phase() != "tiling": return jsonify(err("Nicht in der Tiling-Phase"))
        d = request.get_json()
        try:
            raw_tid = d.get('dome_tile_id')
            tid = int(raw_tid) if raw_tid is not None else None
            _rust.apply_tiling(int(d['player']), int(d['pattern_row']),
                               int(d['slot_row']), int(d['slot_col']),
                               int(d['space_index']), tid, int(d.get('rotation', 0)))
            _flush_game_log()
            return jsonify(ok())
        except Exception as e:
            return jsonify(err(str(e)))
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    if _game.state.phase != "tiling": return jsonify(err("Nicht in der Tiling-Phase"))

    d = request.get_json()
    try:
        pi = int(d['player'])
        # --- SICHERHEIT: Verhindere KI-Zug durch Mensch ---
        # Wenn KI aktiv ist, darf ein Mensch-Request für Tiling 
        # niemals das KI-Flag oder KI-Züge triggern.
        if 'AI_ENABLED' in globals() and AI_ENABLED and pi == _ai_player:
             # Das sollte eigentlich nicht passieren, wenn das Frontend sauber ist
             pass
        action = TilingAction(
            pattern_row=int(d['pattern_row']),
            slot_row=int(d['slot_row']),
            slot_col=int(d['slot_col']),
            space_index=int(d['space_index']),
            dome_tile_id=d.get('dome_tile_id'),
            rotation=int(d.get('rotation', 0)),
        )
        
        _game.apply_single_tiling(pi, action)
        _flush_game_log()
        return jsonify(ok())
    except ValueError as e:
        return jsonify(err(str(e)))


@app.route('/api/tiling/bonus_chips', methods=['POST'])
def tiling_bonus_chips():
    if _rust_active():
        if _rust.phase() != "tiling": return jsonify(err("Nicht in der Tiling-Phase"))
        d = request.get_json()
        try:
            _rust.apply_tiling_chips(int(d['player']), int(d['pattern_row']))
            _flush_game_log()
            return jsonify(ok())
        except Exception as e:
            return jsonify(err(str(e)))
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

        # Reihenfolge-Regel (top-down): Sobald in dieser Tiling-Phase eine
        # SPÄTERE Reihe gelegt wurde, sind FRÜHERE Reihen tabu — keine Chips,
        # keine Abrechnung mehr. tiled_max_row hält die höchste bereits gelegte
        # Reihe fest (-1 = noch keine gelegt).
        tiled_max = getattr(player, "tiled_max_row", -1)
        if row_idx < tiled_max:
            return jsonify(err(
                f"Reihe {row_idx+1} ist gesperrt — es wurde bereits eine "
                f"spätere Reihe gelegt (Tiling läuft von oben nach unten)."
            ))

        # Chip-IDs validieren
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

        # Platzierbarkeit prüfen wenn Reihe nach Chips komplett wäre
        would_complete = (row.spaces_left - len(chip_uses)) <= 0
        if would_complete:
            from engine.game import generate_tiling_actions
            # Temporär auffüllen und prüfen
            row.tiles.extend([row.color] * len(chip_uses))
            actions = generate_tiling_actions(_game.state, pi)
            placeable = any(a.pattern_row == row_idx for a in actions)
            del row.tiles[-len(chip_uses):]  # zurückrollen

            if not placeable:
                return jsonify(err(
                    f"Reihe {row_idx+1} kann nach Chip-Einsatz nicht auf die Kuppel "
                    f"gelegt werden — kein passender Slot verfügbar."
                ))

        # Chips verbrauchen
        for cid in used_chip_ids:
            for i, c in enumerate(player.bonus_chips):
                if c and c.chip_id == cid:
                    player.bonus_chips[i] = None
                    break

        # Fliesen eintragen
        for _ in chip_uses:
            row.tiles.append(row.color)

        _game.state.log_event(
            f"{player.name}: {len(chip_uses)} Chip-Nutzung(en) → "
            f"Reihe {row_idx+1} {'komplett' if row.is_complete else 'teilweise'} gefüllt"
        )
        _flush_game_log()
        return jsonify(ok())
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify(err(str(e)))


@app.route('/api/tiling/unplaceable', methods=['GET'])
def tiling_unplaceable():
    if _rust_active():
        return jsonify({"ok": True, "unplaceable": _json.loads(_rust.unplaceable_json())})
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
    if _rust_active():
        d = request.get_json()
        try:
            _rust.move_row_to_floor(int(d['player']), int(d['pattern_row']))
            _flush_game_log()
            return jsonify(ok())
        except Exception as e:
            return jsonify(err(str(e)))
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
        _flush_game_log()
        return jsonify(ok())
    except Exception as e:
        return jsonify(err(str(e)))


@app.route('/api/end_tiling', methods=['POST'])
def end_tiling():
    if _rust_active():
        # Mit KI beendet der Mensch (= 1-_ai_player) sein Tiling; danach übernimmt
        # die KI via /api/ai/move. Ohne KI: der aktuelle Spieler.
        pi = (1 - _ai_player) if _ai_player is not None else _rust.current_player()
        if _rust.pending_tiling_count(pi):
            return jsonify(err("Du hast noch platzierbare Reihen. Bitte lege sie zuerst an die Kuppel!"))
        try:
            _rust.end_tiling(pi)
            _flush_game_log()
            return jsonify(ok())
        except Exception as e:
            return jsonify(err(str(e)))
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))

    # 1. Sicherheits-Check: Hat der Mensch wirklich alles gelegt?
    human_player = 1 - _ai_player if _ai_player is not None else _game.state.current_player
    if _game.valid_tiling_actions(human_player):
        return jsonify(err("Du hast noch platzierbare Reihen. Bitte lege sie zuerst an die Kuppel!"))

    try:
        # 2. KI-Turbo: Falls die KI aktiv ist, darf sie jetzt vollautomatisch zu Ende tilen!
        if _ai_agent is not None and _ai_player is not None:
            _game.state.current_player = _ai_player
            from agents.agent_env import MosaicEnv
            from engine.serializer import serialize_state
            
            env = MosaicEnv()
            env._game = _game
            env.state = _game.state
            _ai_agent.set_env(env)
            
            while True:
                actions = env.valid_actions()
                if not actions:
                    break
                # Sobald nur noch der "end_tiling" Exit übrig ist, stoppt die Schleife
                if len(actions) == 1 and actions[0].get("type") == "end_tiling":
                    break
                
                # KI wählt ihren nächsten Tiling-Zug und führt ihn aus
                action = _ai_agent.choose(actions, serialize_state(env.state))
                _, _, done, info = env.step(action)
                
                if 'error' in info:
                    print(f"KI Tiling Fehler (Auto-Loop): {info['error']}")
                    break
        
        # 3. Phase offiziell beenden — für BEIDE Spieler.
        # game.apply({"type":"end_tiling"}) setzt nur das Flag für EINEN
        # Spieler (current_player). Wird nur einmal gerufen, bleibt das Flag
        # des anderen Spielers False → game.py wechselt zurück zu ihm und die
        # Phase endet nie → Endlosschleife. Beide haben hier nachweislich
        # keine platzierbaren Reihen mehr (Mensch via Check oben, KI via
        # Auto-Loop), daher ist end_tiling für beide regelkonform.
        if _ai_player is not None:
            # Erst Mensch, dann KI: der zweite Aufruf erreicht [True, True]
            # und löst _execute_end_tiling() in game.py aus.
            for p in (human_player, _ai_player):
                if not _game.valid_tiling_actions(p):
                    _game.apply({"type": "end_tiling", "player": p})
        else:
            _game.apply({"type": "end_tiling"})
        _flush_game_log()
        return jsonify(ok())
        
    except Exception as e:
        return jsonify(err(str(e)))

@app.route('/api/move/pass', methods=['POST'])
def move_pass():
    if _rust_active():
        if not _both_start_placed(): return jsonify(err("Startkacheln fehlen."))
        if _rust.phase() != "drafting": return jsonify(err("Passen nur in Phase 1 möglich."))
        real_moves = [m for m in _rust_state().get("valid_moves", []) if m.get("type") != "pass"]
        if real_moves:
            return jsonify(err("Passen nicht erlaubt — es gibt noch gültige Aktionen."))
        try:
            _rust.apply_pass()
            _flush_game_log()
            return jsonify(ok())
        except Exception as e:
            return jsonify(err(str(e)))
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    if not _both_start_placed(): return jsonify(err("Startkacheln fehlen."))
    if _game.state.phase != "drafting": return jsonify(err("Passen nur in Phase 1 möglich."))

    # Validierung: Darf der Spieler passen?
    real_moves = [m for m in _game.valid_moves() if m.get("type") != "pass"]
    if len(real_moves) > 0:
        return jsonify(err("Passen nicht erlaubt — es gibt noch gültige Aktionen."))

    # --- HIER IST DIE MAGIE ---
    # Wir übergeben das Passen einfach an die Engine. 
    # game.py kümmert sich jetzt um Spielerwechsel, Log-Eintrag und den Phasenwechsel!
    try:
        _game.apply({"type": "pass"})
        _flush_game_log()
        return jsonify(ok())
    except ValueError as e:
        return jsonify(err(str(e)))


@app.route('/api/scoring_tiles', methods=['GET'])
def get_scoring_tiles():
    from engine.scoring import ALL_SCORING_TILES, MUTUALLY_EXCLUSIVE_PAIRS, _exclusion_partner
    return jsonify({
        "ok": True,
        "tiles": [{"id": t.id, "name": t.name, "description": t.description,
                   "emoji": t.emoji, "excludes": _exclusion_partner(t.id)}
                  for t in ALL_SCORING_TILES],
        "exclusive_pairs": [list(p) for p in MUTUALLY_EXCLUSIVE_PAIRS],
    })


@app.route('/api/scoring_tiles/select', methods=['POST'])
def select_scoring_tiles():
    if _rust_active():
        d = request.get_json()
        try:
            _rust.select_scoring([int(i) for i in d.get('ids', [])])
            _flush_game_log()
            return jsonify(ok())
        except Exception as e:
            return jsonify(err(str(e)))
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    d = request.get_json()
    ids = d.get('ids', [])
    if len(ids) != 3: return jsonify(err("Genau 3 Wertungsplatten wählen"))
    
    from engine.scoring import ALL_SCORING_TILES, has_exclusion_conflict
    valid_ids = {t.id for t in ALL_SCORING_TILES}
    if not all(i in valid_ids for i in ids): return jsonify(err("Ungültige Wertungsplatten-IDs"))
    if len(set(ids)) != 3: return jsonify(err("Keine Duplikate erlaubt"))
    if has_exclusion_conflict(ids):
        return jsonify(err("Zwei sich ausschließende Wertungsplatten gewählt"))
    
    _game.state.scoring_tile_ids = list(ids)
    _game.state.scoring_confirmed = True   # nicht mehr editierbar
    _game.state.log_event(f"Wertungsplatten gewählt: {ids}")
    return jsonify(ok())


@app.route('/api/end_scoring', methods=['POST'])
def end_scoring():
    if _rust_active():
        if _rust.phase() != "end": return jsonify(err("Spiel noch nicht beendet"))
        try:
            results = _json.loads(_rust.end_scoring_json())
            _flush_game_log()
            return jsonify({"ok": True, "state": _rust_state(), **results})
        except Exception as e:
            return jsonify(err(str(e)))
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    if _game.state.phase != "end": return jsonify(err("Spiel noch nicht beendet"))
    try:
        results = _game._calculate_end_scoring()
        _flush_game_log()
        return jsonify({"ok": True, "state": serialize_state(_game.state), **results})
    except Exception as e:
        return jsonify(err(str(e)))

@app.route('/api/end_game_log', methods=['POST'])
def end_game_log():
    """Schreibt Spielende-Summary ins Log."""
    if _rust_active():
        if _game_log_path:
            _flush_game_log()
            scores = list(_rust.scores())
            try:
                with open(_game_log_path, 'a', encoding='utf-8') as lf:
                    lf.write(f"# {'='*60}\n")
                    lf.write(f"# SPIELENDE: {scores}\n")
                    lf.write(f"# Seed: {_rust.seed()}\n")
            except Exception:
                pass
        return jsonify(ok())
    if _game_log_path and _game.state:
        _flush_game_log()
        scores = [p.score for p in _game.state.players]
        try:
            with open(_game_log_path, 'a', encoding='utf-8') as lf:
                lf.write(f"# {'='*60}\n")
                lf.write(f"# SPIELENDE: {scores}\n")
                lf.write(f"# Seed: {getattr(_game.state, '_seed', '?')}\n")
        except Exception:
            pass
    return jsonify(ok())


@app.route('/api/stack/peek', methods=['POST'])
def stack_peek():
    if _rust_active():
        d = request.get_json()
        try:
            n = int(d.get('num', 1))
            tiles = _json.loads(_rust.peek_stack_json(n))
            if not tiles:
                return jsonify(err("Keine Karten auf dem Stapel"))
            return jsonify({"ok": True, "tiles": tiles})
        except Exception as e:
            return jsonify(err(str(e)))
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


@app.route('/api/ai/config', methods=['GET'])
def ai_config():
    """Gibt aktuelle KI-Konfiguration zurück."""
    if _rust_active():
        return jsonify({
            "ok": True,
            "ai_enabled": _ai_player is not None,
            "ai_player": _ai_player,
            "sims": _ai_sims,
        })
    if _ai_agent is None:
        return jsonify({"ok": True, "ai_enabled": False})
    sims = getattr(_ai_agent, 'simulations', 0)
    return jsonify({
        "ok":         True,
        "ai_enabled": True,
        "ai_player":  _ai_player,
        "sims":       sims,
    })


@app.route('/api/ai/config', methods=['POST'])
def ai_config_set():
    """Setzt Schwierigkeit während des Spiels."""
    global _ai_agent, _ai_sims
    if _rust_active():
        d = request.get_json(silent=True) or {}
        preset = _resolve_difficulty(d.get('difficulty', 'medium'), d.get('model'), d.get('sims'))
        _ai_sims = int(preset.get('sims') or 300)
        return jsonify({"ok": True, "sims": _ai_sims})
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    d = request.get_json(silent=True) or {}
    difficulty = d.get('difficulty', 'medium')
    model_v    = d.get('model', None)
    sims_v     = d.get('sims',  None)
    preset     = _resolve_difficulty(difficulty, model_v, sims_v)
    with _ai_lock:
        _init_ai(preset['model'], preset['sims'])
    return jsonify({"ok": True, "difficulty": difficulty, **preset})


@app.route('/api/ai/move', methods=['GET', 'POST'])
def ai_move():
    """
    Lässt die KI einen Zug ausführen.
    Wird vom Frontend nach jedem Menschenzug aufgerufen wenn
    _game.state.current_player == _ai_player.
    """
    if _rust_active():
        if _ai_player is None: return jsonify(err("KI-Spieler nicht gesetzt"))
        phase = _rust.phase()
        if phase not in ("drafting", "tiling"):
            return jsonify(err(f"KI kann in Phase '{phase}' nicht ziehen"))
        if _rust.current_player() != _ai_player:
            return jsonify(err("Nicht der Zug der KI" if phase == "drafting"
                               else "Mensch ist noch am Tilen"))
        try:
            # KI-Drafting-Zug immer geloggt ausführen (gleicher Zug; nur Trace
            # zusätzlich) → letzter Trace für den Debugger-Button vorhalten.
            global _last_ai_log
            res = _json.loads(_rust.ai_step_json(_ai_sims, True))
        except Exception as e:
            return jsonify(err(f"KI-Fehler: {e}"))
        if not res.get("applied"):
            return jsonify(err(res.get("reason", "KI konnte nicht ziehen")))
        if res.get("log_text"):
            _last_ai_log = res["log_text"]
        dbg = res.get("debug")
        if isinstance(dbg, dict) and "moves" in dbg:
            dbg["round"]    = _rust.round_number()
            dbg["move_idx"] = len(_ai_debug_history) + 1
            _ai_debug_history.append(dbg)
        _flush_game_log()
        response = ok()
        response["ai_action"] = res.get("action")
        response["done"]      = res.get("done", False)
        response["debug"]     = dbg
        return jsonify(response)

    if _game.state is None:    return jsonify(err("Kein aktives Spiel"))
    if _ai_agent is None:      return jsonify(err("Kein KI-Agent aktiv"))
    if _ai_player is None:     return jsonify(err("KI-Spieler nicht gesetzt"))

    # --- START SYNC DEBUG LOG ---
    #print(f"\n[SYNC-DEBUG] Frontend fordert KI-Zug an!")
    #print(f" -> Engine Phase:   {_game.state.phase}")
    #print(f" -> Engine Player:  {_game.state.current_player} (Sollte KI={_ai_player} sein)")
    #print(f" -> Tokens verbraucht (Spieler 0): {_game.state.players[0].tokens_used}")
    #print(f" -> Tokens verbraucht (Spieler 1): {_game.state.players[1].tokens_used}")
    # --- END SYNC DEBUG LOG ---

    if _game.state.phase not in ("drafting", "tiling"):
        return jsonify(err(f"KI kann in Phase '{_game.state.phase}' nicht ziehen"))

    # Drafting: current_player muss KI sein
    if _game.state.phase == "drafting" and _game.state.current_player != _ai_player:
        return jsonify(err("Nicht der Zug der KI"))

    # Tiling: KI muss noch platzierbare Reihen haben
    if _game.state.phase == "tiling":
        from engine.game import generate_tiling_actions
        #ai_actions = generate_tiling_actions(_game.state, _ai_player)
        #if not ai_actions:
        #    return jsonify(err("KI hat keine Tiling-Züge mehr"))

        # Regel mit KI: Der Mensch tilt ZUERST komplett. Solange der Mensch
        # noch platzierbare Reihen hat, darf die KI nicht tilen.
        human_player = 1 - _ai_player
        human_actions = generate_tiling_actions(_game.state, human_player)
        if human_actions:
            return jsonify(err("Mensch ist noch am Tilen"))
            
        _game.state.current_player = _ai_player

    with _ai_lock:
        try:
            from agents.agent_env import MosaicEnv
            # KI-Env mit aktuellem State synchronisieren
            env = MosaicEnv()
            env._game = _game
            env.state  = _game.state
            _ai_agent.set_env(env)

            actions = env.valid_actions()
            if not actions:
                return jsonify(err("Keine gültigen Aktionen für KI"))

            from engine.serializer import serialize_state
            obs = serialize_state(env.state)

            # Pre-Move-Analyse UND Zugwahl aus DEMSELBEN Baum.
            # So sind angezeigte Visits und gewählter Zug garantiert konsistent.
            # Gilt für AlphaZero (mit Netz) UND Heuristik (nur MCTS).
            debug_info  = None
            best_action = None
            if hasattr(_ai_agent, "_select"):
                try:
                    debug_info, best_action = _compute_debug_analysis(
                        env, actions, mark_best=True)
                except Exception as _de:
                    debug_info = {"error": str(_de)}

            # Aktion bestimmen: bevorzugt aus der Analyse (gleicher Baum),
            # sonst Fallback auf separaten choose-Aufruf.
            if best_action is not None:
                action = best_action
            else:
                action = _ai_agent.choose(actions, obs)

            # Aktion im echten Game ausführen
            _, reward, done, info = env.step(action)

            if 'error' in info:
                return jsonify(err(f"KI-Zug ungültig: {info['error']}"))

            # Metadaten + Historie (chosen wurde schon in der Analyse gesetzt)
            if debug_info and "moves" in debug_info:
                from agents.neural_net import action_to_id
                chosen_id = action_to_id(action) if isinstance(action, dict) else action
                debug_info["round"]     = getattr(_game.state, "round_number", None)
                debug_info["move_idx"]  = len(_ai_debug_history) + 1
                debug_info["ai_action"] = chosen_id
                _ai_debug_history.append(debug_info)

            response = ok()
            response['ai_action'] = action
            response['done']      = done
            response['debug']     = debug_info
            return jsonify(response)

        except Exception as e:
            return jsonify(err(f"KI-Fehler: {str(e)}"))


@app.route('/api/ai/start_tile', methods=['GET', 'POST'])
def ai_start_tile():
    """
    KI legt ihre Startkuppelplatte. Nutzt — wie die normalen Züge — den
    MCTS+Netz-Mechanismus, sodass die KI das gelernte Startkuppel-Wissen
    aus dem Training anwendet (statt der alten evaluate_state-Heuristik).
    Fallback auf evaluate_state nur wenn kein KI-Agent aktiv ist.
    """
    if _rust_active():
        if _ai_player is None: return jsonify(err("KI-Spieler nicht gesetzt"))
        if _rust.both_start_placed():
            return jsonify({"ok": True, "state": _rust_state(), "skipped": True})
        vm = _rust_state().get("valid_moves", [])
        pending = vm[0].get("player") if vm and vm[0].get("type") == "start_tile_pending" else None
        if pending != _ai_player:
            # Noch nicht die KI dran (Nicht-Startspieler zuerst) → warten.
            return jsonify({"ok": True, "state": _rust_state(), "skipped": True})
        try:
            res = _json.loads(_rust.ai_start_tile_json(_ai_player))
        except Exception as e:
            return jsonify(err(str(e)))
        _flush_game_log()
        response = ok()
        response["ai_action"] = res
        return jsonify(response)

    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    if _ai_player is None:  return jsonify(err("KI-Spieler nicht gesetzt"))

    state  = _game.state
    player = state.players[_ai_player]

    # Startkachel bereits gelegt?
    if player.start_dome_tile is None:
        return jsonify({"ok": True, "state": serialize_state(state), "skipped": True})

    if not state.dome_display:
        return jsonify(err("Kein Kuppelplättchen im Display"))

    empty_slots = [(r, c) for r in range(3) for c in range(3)
                   if player.dome_grid.dome_slots[r][c] is None]
    if not empty_slots:
        return jsonify(err("Kein freies Kuppelslot"))

    # --- Netz-Agent: MCTS+Policy (gelerntes Wissen) ---
    # Nur für Agenten MIT Netz (evaluate_raw). Der reine Heuristik-Agent
    # nutzt stattdessen die Farb-Reihen-Heuristik (unten), die ohne Policy
    # bessere Startkuppeln setzt als die blinde MCTS-Suche.
    if _ai_agent is not None and hasattr(_ai_agent, "evaluate_raw") and hasattr(_ai_agent, "_select"):
        prev_phase = state.phase
        try:
            from agents.agent_env import MosaicEnv
            from agents.mcts import MCTSNode

            env = MosaicEnv()
            env._game = _game
            env.state = _game.state
            env._start_first_player = state.current_player
            state.phase = "start_placement"
            _ai_agent.set_env(env)

            actions = [a for a in env._start_placement_actions()
                       if a.get("_placing_player") == _ai_player]
            if not actions:
                raise RuntimeError("Keine Startkuppel-Aktionen für KI")

            pi = _ai_player
            root = MCTSNode(action=None, parent=None, untried_actions=list(actions),
                            player_who_acted=pi)
            root.visits = 1
            if hasattr(_ai_agent, "_compute_dynamic_sims"):
                sim_count = _ai_agent._compute_dynamic_sims(len(actions))
            else:
                sim_count = _ai_agent.simulations
            for _ in range(sim_count):
                sim_env = env.clone()
                node = _ai_agent._select(root, sim_env)
                node = _ai_agent._expand(node, sim_env)
                result = _ai_agent._rollout(sim_env)
                _ai_agent._backpropagate(node, result, pi)

            state.phase = prev_phase  # apply_start_placement macht den echten Übergang

            if root.children:
                best = max(root.children, key=lambda n: n.visits)
                a = best.action
                _game.apply_start_placement(
                    player_idx=_ai_player,
                    tile_id=a["tile_id"],
                    row=a["slot_row"], col=a["slot_col"], rot=a["rotation"],
                )
                return jsonify(ok())
        except Exception:
            try:
                state.phase = prev_phase
            except Exception:
                pass
            # weiter zum Heuristik-Fallback

    # --- Heuristik-Agent oder kein Netz: Farb-Reihen-Heuristik ---
    # Dreht die Kuppel so, dass häufig verfügbare Farben in kurze, leicht
    # füllbare Reihen zeigen (statt blinder evaluate_state-Bewertung).
    try:
        import copy
        from collections import Counter
        from agents.agent_env import MosaicEnv

        # Farb-Verfügbarkeit dieser Runde aus den Fabriken
        color_availability = Counter()
        for f in state.factories:
            for t in f.sun_tiles:
                color_availability[t.name] += 1
            for t in getattr(f, 'moon_tiles', []):
                color_availability[t.name] += 1
        for t in getattr(state.large_factory, 'sun_tiles', []):
            color_availability[t.name] += 1
        for t in getattr(state.large_factory, 'moon_tiles', []):
            color_availability[t.name] += 1

        scorer = MosaicEnv()  # nur für _score_start_placement
        best_score = -float('inf')
        best = (state.dome_display[0].tile_id, empty_slots[0][0], empty_slots[0][1], 0)

        for tile in state.dome_display:
            for (r, c) in empty_slots:
                for rot in [0, 90, 180, 270]:
                    test_game = copy.deepcopy(_game)
                    try:
                        test_game.apply_start_placement(
                            player_idx=_ai_player,
                            tile_id=tile.tile_id,
                            row=r, col=c, rot=rot,
                        )
                        score = scorer._score_start_placement(
                            test_game.state.players[_ai_player],
                            color_availability,
                        )
                        if score > best_score:
                            best_score = score
                            best = (tile.tile_id, r, c, rot)
                    except Exception:
                        continue

        tile_id, row, col, rot = best
        _game.apply_start_placement(
            player_idx=_ai_player,
            tile_id=tile_id,
            row=row, col=col, rot=rot,
        )
        return jsonify(ok())

    except Exception as e:
        return jsonify(err(str(e)))


def _compute_debug_analysis(env, actions, mark_best=False):
    """
    Gemeinsame Debug-Analyse für /api/ai/debug und /api/ai/move.
    Baut EINEN MCTS-Baum auf (führt KEINEN Zug aus) und kombiniert
    rohe Netz-Policy + MCTS-Visits + Value pro gültiger Aktion.

    Gibt (analysis_dict, best_action_dict) zurück. Die best_action stammt
    aus DEMSELBEN Baum (max Visits) — so sind Anzeige und echte Wahl konsistent.
    Wenn mark_best=True wird der beste Zug direkt als 'chosen' markiert.
    """
    from agents.mcts import MCTSNode
    from agents.neural_net import action_to_id
    from engine.serializer import serialize_state
    from utils.action_describe import describe_action_id, action_category

    has_net = hasattr(_ai_agent, "evaluate_raw")

    # 1. Rohe Netz-Auswertung (nur falls Netz vorhanden)
    obs = serialize_state(env.state)
    raw = _ai_agent.evaluate_raw(obs, actions=actions) if has_net else None

    # 2. EINEN MCTS-Baum aufbauen (Visits), ohne Zug auszuführen
    pi = env.current_player()
    root = MCTSNode(action=None, parent=None, untried_actions=None,
                    player_who_acted=pi)
    root.visits = 1
    # Dieselbe (ggf. dynamische) Sim-Zahl wie die echte Zugwahl verwenden,
    # damit Anzeige und gewählter Zug konsistent bleiben.
    if hasattr(_ai_agent, "_compute_dynamic_sims"):
        sim_count = _ai_agent._compute_dynamic_sims(len(actions))
    else:
        sim_count = _ai_agent.simulations
    for _ in range(sim_count):
        sim_env = env.clone()
        node = _ai_agent._select(root, sim_env)
        node = _ai_agent._expand(node, sim_env)
        result = _ai_agent._rollout(sim_env)
        _ai_agent._backpropagate(node, result, pi)
        
    def get_max_depth(n):
        if not n.children:
            return 0
        return 1 + max(get_max_depth(c) for c in n.children)
    
    tree_depth = get_max_depth(root)

    # Beste Aktion aus DIESEM Baum: höchste Visits (identische Logik wie _mcts_search)
    best_action = None
    best_id     = None
    if root.children:
        best_child  = max(root.children, key=lambda n: n.visits)
        best_action = best_child.action
        best_id     = action_to_id(best_action)

    total_visits = sum(c.visits for c in root.children) or 1
    visits_by_id = {}
    q_by_id      = {}
    depth_by_id  = {}
    for c in root.children:
        aid = action_to_id(c.action)
        visits_by_id[aid] = c.visits
        q_by_id[aid]      = (c.value / c.visits) if c.visits > 0 else 0.0
        depth_by_id[aid]  = get_max_depth(c) + 1

    # Shaping-Reward pro Aktion: was gibt env.step() für diesen einen Zug?
    # (Score-Differenz + Potential-Differenz aus shaping.py)
    # Zeigt direkt, warum die Heuristik/das Shaping einen Zug gut/schlecht findet.
    shaping_by_id = {}
    for a in actions:
        aid = action_to_id(a)
        if aid in shaping_by_id:
            continue
        try:
            test_env = env.clone()
            _, r, _, _ = test_env.step(a)
            shaping_by_id[aid] = round(float(r), 3)
        except Exception:
            shaping_by_id[aid] = None

    moves = []
    if has_net:
        # Netz vorhanden: über alle gültigen Aktionen iterieren (mit Policy)
        for e in raw["per_action"]:
            aid = action_to_id(e["action"])
            visits = visits_by_id.get(aid, 0)
            q      = q_by_id.get(aid, None)
            d      = depth_by_id.get(aid, 0)
            moves.append({
                "action_id":      aid,
                "description":    describe_action_id(aid),
                "category":       action_category(aid),
                "net_prob":       round(e["prob"], 4),
                "net_prob_norm":  round(e["prob_renormalized"], 4),
                "mcts_visits":    visits,
                "mcts_share":     round(visits / total_visits, 4),
                "mcts_q":         round(q, 4) if q is not None else None,
                "mcts_win_pct":   round((q + 1) / 2 * 100, 1) if q is not None else None,
                "max_depth":      d,
                "shaping":        shaping_by_id.get(aid),
                "chosen":         (mark_best and aid == best_id),
            })
    else:
        # Kein Netz (Heuristik): nur die MCTS-besuchten Aktionen anzeigen,
        # Netz-Felder bleiben None (Frontend blendet sie aus).
        for c in root.children:
            aid    = action_to_id(c.action)
            visits = c.visits
            q      = q_by_id.get(aid, None)
            d      = depth_by_id.get(aid, 0)
            moves.append({
                "action_id":      aid,
                "description":    describe_action_id(aid),
                "category":       action_category(aid),
                "net_prob":       None,
                "net_prob_norm":  None,
                "mcts_visits":    visits,
                "mcts_share":     round(visits / total_visits, 4),
                "mcts_q":         round(q, 4) if q is not None else None,
                "mcts_win_pct":   round((q + 1) / 2 * 100, 1) if q is not None else None,
                "max_depth":      d,
                "shaping":        shaping_by_id.get(aid),
                "chosen":         (mark_best and aid == best_id),
            })
    moves.sort(key=lambda m: m["mcts_visits"], reverse=True)

    analysis = {
        "current_player": pi,
        "ai_player":      _ai_player,
        "value":          round(raw["value"], 4) if has_net else None,
        "win_prob":       round(raw["win_prob"], 4) if has_net else None,
        "win_pct":        round(raw["win_prob"] * 100, 1) if has_net else None,
        "has_net":        has_net,
        "simulations":    sim_count,
        "num_actions":    len(actions),
        "max_depth":      tree_depth,
        "moves":          moves,
    }
    return analysis, best_action


@app.route('/api/ai/debug', methods=['GET'])
def ai_debug():
    """
    Debugger-Endpunkt: Analyse der AKTUELLEN Stellung (ohne Zug auszuführen).
    Funktioniert für AlphaZeroAgent (mit Netz-Policy) UND HeuristicMCTSAgent
    (nur MCTS-Visits, ohne Netz-Spalte).
    """
    if _rust_active():
        analysis = _json.loads(_rust.ai_debug_json(_ai_sims))
        if not isinstance(analysis, dict):
            return jsonify({"ok": True, "moves": [], "current_player": _rust.current_player()})
        analysis["ok"] = True
        return jsonify(analysis)
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    if _ai_agent is None:   return jsonify(err("Kein KI-Agent aktiv"))
    if not hasattr(_ai_agent, "_select"):
        return jsonify(err("Debug nur für MCTS-basierte Agenten verfügbar"))

    try:
        from agents.agent_env import MosaicEnv
        env = MosaicEnv()
        env._game = _game
        env.state  = _game.state
        _ai_agent.set_env(env)

        actions = env.valid_actions()
        if not actions:
            return jsonify({"ok": True, "value": None, "win_prob": None,
                            "current_player": env.current_player(), "moves": []})

        result, _best = _compute_debug_analysis(env, actions, mark_best=True)
        result["ok"] = True
        return jsonify(result)

    except Exception as e:
        import traceback
        return jsonify(err(f"Debug-Fehler: {str(e)}\n{traceback.format_exc()}"))


@app.route('/api/ai/debug_history', methods=['GET'])
def ai_debug_history():
    """Gibt die komplette KI-Zug-Analyse-Historie des aktuellen Spiels zurück."""
    return jsonify({"ok": True, "history": _ai_debug_history, "count": len(_ai_debug_history)})


@app.route('/api/ai/last_log', methods=['GET', 'POST'])
def ai_last_log():
    """Schreibt den vollständigen MCTS-Trace des ZULETZT gespielten KI-Drafting-
    Zugs als Textdatei (Wurzelspieler = KI)."""
    if not _last_ai_log:
        return jsonify(err("Noch kein KI-Zug protokolliert."))
    try:
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"mcts_lastmove_{ts}.txt"
        with open(LOG_DIR / fname, 'w', encoding='utf-8') as f:
            f.write(_last_ai_log)
        return jsonify({
            "ok": True,
            "file": fname,
            "url": f"/static/log/{fname}",
            "lines": _last_ai_log.count("\n") + 1,
        })
    except Exception as e:
        return jsonify(err(f"Log-Fehler: {e}"))




@app.route('/api/ai/suggest', methods=['GET'])
def ai_suggest():
    """
    Mentor Mode: gibt Top-3 KI-Züge mit Visit-Counts zurück.
    Nur für AlphaZeroAgent verfügbar.
    """
    if _game.state is None: return jsonify(err("Kein aktives Spiel"))
    if _ai_agent is None:   return jsonify(err("Kein KI-Agent aktiv"))

    try:
        from agents.agent_env import MosaicEnv
        from agents.mcts import MCTSNode
        env = MosaicEnv()
        env._game = _game
        env.state  = _game.state
        _ai_agent.set_env(env)

        actions = env.valid_actions()
        if not actions:
            return jsonify({"ok": True, "suggestions": []})

        # MCTS-Baum aufbauen ohne Zug auszuführen
        pi = env.current_player()
        root = MCTSNode(action=None, parent=None, untried_actions=None,
                        player_who_acted=pi)
        root.visits = 1

        if hasattr(_ai_agent, "_compute_dynamic_sims"):
            sug_sims = _ai_agent._compute_dynamic_sims(len(actions))
        else:
            sug_sims = _ai_agent.simulations
        for _ in range(sug_sims):
            sim_env = env.clone()
            node = _ai_agent._select(root, sim_env)
            node = _ai_agent._expand(node, sim_env)
            result = _ai_agent._rollout(sim_env)
            _ai_agent._backpropagate(node, result, pi)

        # Top-3 nach Visit-Count
        top = sorted(root.children, key=lambda n: n.visits, reverse=True)[:3]
        suggestions = []
        for child in top:
            q = child.value / child.visits if child.visits > 0 else 0.0
            win_pct = round((q + 1) / 2 * 100, 1)
            suggestions.append({
                "action":   child.action,
                "visits":   child.visits,
                "win_pct":  win_pct,
            })

        return jsonify({"ok": True, "suggestions": suggestions})

    except Exception as e:
        return jsonify(err(f"Suggest-Fehler: {str(e)}"))


if __name__ == '__main__':
    print("Mosaic-AI Server läuft auf http://localhost:5000")
    app.run(debug=True, port=5000)