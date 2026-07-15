"""
Mosaic-AI — Flask API Server (Rust-Engine)

Alle Spiel- und KI-Logik läuft über die Rust-Engine (`mosaic_rust.PyGame`).
Es gibt keinen Python-Engine-/Agenten-Pfad mehr — `engine/` und `agents/`
werden vom Server nicht mehr importiert.

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
  POST /api/ai/config         — Schwierigkeit setzen
  POST /api/ai/move           — KI führt ihren nächsten Zug aus

Alle Responses: {"ok": true, "state": {...}} oder {"ok": false, "error": "..."}
"""

import sys
import json as _json
import datetime as _dt
from pathlib import Path

# Stelle sicher dass der Hauptordner im Python-Path ist
BASE_DIR = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, BASE_DIR)

from flask import Flask, request, jsonify, send_from_directory
import threading
from config import MODELS_DIR

# Rust-Engine — einzige Engine. Ohne sie kann kein Spiel laufen.
try:
    import mosaic_rust as _mr
except ImportError:
    _mr = None

STATIC_DIR = Path(__file__).resolve().parent / 'static'
app = Flask(__name__, static_folder=str(STATIC_DIR))
try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    pass

# ── MIME-Types fix (besonders Windows) ───────────────────────────────────────
# Auf Windows liest Pythons mimetypes-Modul die Registry, wo .js oft OHNE
# charset=utf-8 registriert ist → Multibyte-Zeichen zerbrechen. Wir erzwingen
# die korrekten Typen unabhängig vom OS.
import mimetypes as _mt
_mt.add_type('text/javascript', '.js')
_mt.add_type('text/css', '.css')
_mt.add_type('application/json', '.json')

@app.after_request
def _ensure_utf8(resp):
    ct = resp.headers.get('Content-Type', '')
    if ('charset' not in ct.lower()) and any(
        ct.startswith(p) for p in
        ('text/', 'application/javascript', 'application/json')
    ):
        resp.headers['Content-Type'] = ct + '; charset=utf-8'
    return resp

# ── Globaler Spielzustand (Rust) ─────────────────────────────────────────────
_rust = None            # mosaic_rust.PyGame oder None
_rust_logged = 0        # bereits in die Logdatei geschriebene Log-Zeilen
_game_log_path: Path | None = None
LOG_DIR = Path(__file__).parent / "static" / "log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ── KI-Konfiguration ─────────────────────────────────────────────────────────
_ai_player   = None        # 0 oder 1 — welcher Spieler ist die KI
_ai_sims     = 300         # MCTS-Basis-Simulationen der Rust-KI
_ai_model    = None        # None = Heuristik; sonst Versionsname (z.B. "v8") -> Netz-Modus
_ai_c_puct   = 1.5         # PUCT-Konstante im Netz-Modus (Standard wie net_mcts.rs)
_last_ai_log = None        # voller Such-Trace des zuletzt gespielten KI-Drafting-Zugs
_ai_lock     = threading.Lock()
_ai_debug_history = []     # Liste aller KI-Zug-Analysen des aktuellen Spiels

# Difficulty Presets — Format: {"model": "<version>", "sims": <int>}
DIFFICULTY_PRESETS = {
    "easy":   None,
    "medium": None,
    "hard":   None,
    "expert": None,
    "_default": {"model": "v2", "sims": 40},
}

def _resolve_difficulty(difficulty: str, model: str = None, sims: int = None) -> dict:
    """Löst Schwierigkeit auf: explizite Parameter > Preset > _default."""
    if model is not None and sims is not None:
        return {"model": model, "sims": sims}
    preset = DIFFICULTY_PRESETS.get(difficulty)
    if preset is not None:
        return preset
    return DIFFICULTY_PRESETS["_default"]


def _resolve_model_path(model: str | None) -> Path | None:
    """`model` ("v8", "heuristic", None, ...) -> ONNX-Pfad oder None (= Heuristik).
    Akzeptiert auch einen bereits vollständigen Pfad/Dateinamen."""
    if not model or model.strip().lower() in ("", "heuristic", "heuristik"):
        return None
    m = model.strip()
    candidates = [Path(m), MODELS_DIR / m, MODELS_DIR / f"alphazero_{m}.onnx"]
    for c in candidates:
        if c.exists() and c.suffix == ".onnx":
            return c
    return None


# ── Rust-Helfer ──────────────────────────────────────────────────────────────
def _rust_active() -> bool:
    return _rust is not None

def _rust_state() -> dict:
    return _json.loads(_rust.state_json())

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

def ok() -> dict:
    return {"ok": True, "state": _rust_state()}

def err(msg: str) -> dict:
    return {"ok": False, "error": msg}

def _flush_game_log() -> None:
    _rust_flush_log()

def _both_start_placed() -> bool:
    return _rust is not None and _rust.both_start_placed()

def _require_game():
    """Gibt eine Fehler-Response zurück, wenn kein Spiel aktiv ist, sonst None."""
    if not _rust_active():
        return jsonify(err("Kein aktives Spiel"))
    return None


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')


@app.route('/debug')
def debug_page():
    return send_from_directory(STATIC_DIR, 'debug.html')


@app.route('/api/new_game', methods=['POST'])
def new_game():
    global _rust, _rust_logged, _ai_sims, _ai_player, _ai_model, _ai_debug_history, _game_log_path
    _ai_debug_history = []
    data = request.get_json(silent=True) or {}
    names      = data.get('names', ['Spieler 1', 'Spieler 2'])
    seed       = data.get('seed', None)
    ai_enabled = data.get('ai_enabled', False)
    difficulty = data.get('difficulty', 'medium')
    ai_side    = data.get('ai_side', 1)   # 0 = KI ist P1, 1 = KI ist P2

    import random as _random
    fp_raw = data.get('first_player', None)
    first_player = _random.randint(0, 1) if fp_raw is None else int(fp_raw)
    if seed is None:
        seed = _random.randint(0, 999999)

    if _mr is None:
        return jsonify(err("Rust-Engine (mosaic_rust) ist nicht installiert. "
                           "Bitte im engine/-Verzeichnis `maturin build --release` ausführen "
                           "und das Wheel installieren."))
    _rust = _mr.PyGame((names[0], names[1]), first_player=first_player, seed=seed)
    _rust_logged = 0
    seed = _rust.seed()

    model_warning = None
    if ai_enabled:
        preset = _resolve_difficulty(difficulty, data.get('model'), data.get('sims'))
        _ai_player = int(ai_side)
        _ai_sims   = int(preset.get('sims') or 100)
        requested_model = preset.get('model')
        model_path = _resolve_model_path(requested_model)
        if model_path is not None:
            try:
                _rust.load_net(str(model_path))
                _ai_model = requested_model
            except Exception as e:
                model_warning = f"Netz '{requested_model}' konnte nicht geladen werden ({e}) — spiele gegen Heuristik."
                _ai_model = None
        else:
            if requested_model and requested_model.strip().lower() not in ("", "heuristic", "heuristik"):
                model_warning = f"Modell '{requested_model}' nicht gefunden (models/alphazero_{requested_model}.onnx) — spiele gegen Heuristik."
            _ai_model = None
    else:
        _ai_player = None
        _ai_model = None

    # Log-Datei für dieses Spiel erstellen
    timestamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    _game_log_path = LOG_DIR / f"game_{timestamp}_seed{seed}.log"
    with open(_game_log_path, 'w', encoding='utf-8') as lf:
        meta = {
            "timestamp":    timestamp,
            "seed":         seed,
            "players":      names,
            "first_player": first_player,
            "ai_enabled":   ai_enabled,
            "ai_player":    _ai_player,
            "ai_model":     _ai_model or "heuristic",
            "ai_sims":      _ai_sims if ai_enabled else None,
        }
        lf.write("# MOSAIC GAME LOG\n")
        lf.write(f"# {_json.dumps(meta, ensure_ascii=False)}\n")
        lf.write(f"# {'='*60}\n")

    response = ok()
    response['ai_enabled']  = ai_enabled
    response['ai_player']   = _ai_player
    response['ai_model']    = _ai_model or "heuristic"
    if model_warning:
        response['warning'] = model_warning
    response['log_file']    = _game_log_path.name
    response['seed']        = seed
    return jsonify(response)


@app.route('/api/state', methods=['GET'])
def get_state():
    if (e := _require_game()) is not None:
        return e
    return jsonify(ok())


@app.route('/api/move/stone', methods=['POST'])
def move_stone():
    if (e := _require_game()) is not None:
        return e
    if not _both_start_placed():
        return jsonify(err("Startkacheln fehlen."))
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


@app.route('/api/move/dome', methods=['POST'])
def move_dome():
    if (e := _require_game()) is not None:
        return e
    if not _both_start_placed():
        return jsonify(err("Startkacheln fehlen."))
    d = request.get_json()
    try:
        _rust.apply_dome(int(d['tile_id']), int(d['slot_row']),
                         int(d['slot_col']), int(d.get('rotation', 0)))
        _flush_game_log()
        return jsonify(ok())
    except Exception as e:
        return jsonify(err(str(e) or "Zug abgelehnt."))


@app.route('/api/move/dome_stack', methods=['POST'])
def move_dome_stack():
    if (e := _require_game()) is not None:
        return e
    if not _both_start_placed():
        return jsonify(err("Startkacheln fehlen."))
    d = request.get_json()
    try:
        _rust.apply_dome_stack(int(d['num_drawn']), int(d['chosen_id']),
                               int(d['slot_row']), int(d['slot_col']),
                               int(d.get('rotation', 0)))
        _flush_game_log()
        return jsonify(ok())
    except Exception as e:
        return jsonify(err(str(e) or "Zug abgelehnt."))


@app.route('/api/move/bonus_chip', methods=['POST'])
def move_bonus_chip():
    if (e := _require_game()) is not None:
        return e
    if not _both_start_placed():
        return jsonify(err("Startkacheln fehlen."))
    d = request.get_json()
    try:
        _rust.apply_bonus_chip(int(d['factory_id']))
        _flush_game_log()
        return jsonify(ok())
    except Exception as e:
        return jsonify(err(str(e)))


@app.route('/api/move/start_tile', methods=['POST'])
def move_start_tile():
    if (e := _require_game()) is not None:
        return e
    d = request.json
    try:
        _rust.apply_start_tile(int(d['player']), int(d['tile_id']),
                               int(d['slot_row']), int(d['slot_col']),
                               int(d.get('rotation', 0)))
        _flush_game_log()
        return jsonify(ok())
    except Exception as e:
        return jsonify(err(str(e) or "Zug abgelehnt."))


@app.route('/api/move/pass', methods=['POST'])
def move_pass():
    if (e := _require_game()) is not None:
        return e
    if not _both_start_placed():
        return jsonify(err("Startkacheln fehlen."))
    if _rust.phase() != "drafting":
        return jsonify(err("Passen nur in Phase 1 möglich."))
    real_moves = [m for m in _rust_state().get("valid_moves", []) if m.get("type") != "pass"]
    if real_moves:
        return jsonify(err("Passen nicht erlaubt — es gibt noch gültige Aktionen."))
    try:
        _rust.apply_pass()
        _flush_game_log()
        return jsonify(ok())
    except Exception as e:
        return jsonify(err(str(e)))


@app.route('/api/tiling', methods=['POST'])
def tiling():
    if (e := _require_game()) is not None:
        return e
    if _rust.phase() != "tiling":
        return jsonify(err("Nicht in der Tiling-Phase"))
    d = request.get_json()
    try:
        _rust.apply_tiling(int(d['player']), int(d['pattern_row']),
                           int(d['slot_row']), int(d['slot_col']),
                           int(d['space_index']))
        _flush_game_log()
        return jsonify(ok())
    except Exception as e:
        return jsonify(err(str(e)))


@app.route('/api/tiling/bonus_chips', methods=['POST'])
def tiling_bonus_chips():
    if (e := _require_game()) is not None:
        return e
    if _rust.phase() != "tiling":
        return jsonify(err("Nicht in der Tiling-Phase"))
    d = request.get_json()
    try:
        _rust.apply_tiling_chips(int(d['player']), int(d['pattern_row']))
        _flush_game_log()
        return jsonify(ok())
    except Exception as e:
        return jsonify(err(str(e)))


@app.route('/api/tiling/unplaceable', methods=['GET'])
def tiling_unplaceable():
    if (e := _require_game()) is not None:
        return e
    return jsonify({"ok": True, "unplaceable": _json.loads(_rust.unplaceable_json())})


@app.route('/api/tiling/move_to_floor', methods=['POST'])
def tiling_move_to_floor():
    if (e := _require_game()) is not None:
        return e
    d = request.get_json()
    try:
        _rust.move_row_to_floor(int(d['player']), int(d['pattern_row']))
        _flush_game_log()
        return jsonify(ok())
    except Exception as e:
        return jsonify(err(str(e)))


@app.route('/api/end_tiling', methods=['POST'])
def end_tiling():
    if (e := _require_game()) is not None:
        return e
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


@app.route('/api/scoring_tiles', methods=['GET'])
def get_scoring_tiles():
    """Statischer Wertungsplatten-Katalog für die Auswahl-UI (aus Rust)."""
    if _mr is None:
        return jsonify(err("Rust-Engine (mosaic_rust) ist nicht installiert."))
    data = _json.loads(_mr.scoring_tiles_json())
    data["ok"] = True
    return jsonify(data)


@app.route('/api/scoring_tiles/select', methods=['POST'])
def select_scoring_tiles():
    if (e := _require_game()) is not None:
        return e
    d = request.get_json()
    try:
        _rust.select_scoring([int(i) for i in d.get('ids', [])])
        _flush_game_log()
        return jsonify(ok())
    except Exception as e:
        return jsonify(err(str(e)))


@app.route('/api/end_scoring', methods=['POST'])
def end_scoring():
    if (e := _require_game()) is not None:
        return e
    if _rust.phase() != "end":
        return jsonify(err("Spiel noch nicht beendet"))
    try:
        results = _json.loads(_rust.end_scoring_json())
        _flush_game_log()
        return jsonify({"ok": True, "state": _rust_state(), **results})
    except Exception as e:
        return jsonify(err(str(e)))


@app.route('/api/end_game_log', methods=['POST'])
def end_game_log():
    """Schreibt Spielende-Summary ins Log."""
    if not _rust_active():
        return jsonify(ok())
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


@app.route('/api/stack/peek', methods=['POST'])
def stack_peek():
    if (e := _require_game()) is not None:
        return e
    d = request.get_json()
    try:
        n = int(d.get('num', 1))
        tiles = _json.loads(_rust.peek_stack_json(n))
        if not tiles:
            return jsonify(err("Keine Karten auf dem Stapel"))
        return jsonify({"ok": True, "tiles": tiles})
    except Exception as e:
        return jsonify(err(str(e)))


# ── KI ───────────────────────────────────────────────────────────────────────

@app.route('/api/ai/config', methods=['GET'])
def ai_config():
    """Gibt aktuelle KI-Konfiguration zurück."""
    return jsonify({
        "ok": True,
        "ai_enabled": _ai_player is not None,
        "ai_player": _ai_player,
        "sims": _ai_sims,
        "model": _ai_model or "heuristic",
    })


@app.route('/api/ai/config', methods=['POST'])
def ai_config_set():
    """Setzt Schwierigkeit (Basis-Sims, Modell) während des Spiels."""
    global _ai_sims, _ai_model
    d = request.get_json(silent=True) or {}
    preset = _resolve_difficulty(d.get('difficulty', 'medium'), d.get('model'), d.get('sims'))
    _ai_sims = int(preset.get('sims') or 300)
    if 'model' in d or 'difficulty' in d:
        requested_model = preset.get('model')
        model_path = _resolve_model_path(requested_model)
        if model_path is not None and _rust is not None:
            try:
                _rust.load_net(str(model_path))
                _ai_model = requested_model
            except Exception as e:
                return jsonify(err(f"Netz '{requested_model}' konnte nicht geladen werden: {e}"))
        else:
            _ai_model = None
    return jsonify({"ok": True, "sims": _ai_sims, "model": _ai_model or "heuristic"})


@app.route('/api/ai/move', methods=['GET', 'POST'])
def ai_move():
    """Lässt die KI (Rust-MCTS) einen Zug ausführen."""
    global _last_ai_log
    if (e := _require_game()) is not None:
        return e
    if _ai_player is None:
        return jsonify(err("KI-Spieler nicht gesetzt"))
    phase = _rust.phase()
    if phase not in ("drafting", "tiling"):
        return jsonify(err(f"KI kann in Phase '{phase}' nicht ziehen"))
    if _rust.current_player() != _ai_player:
        return jsonify(err("Nicht der Zug der KI" if phase == "drafting"
                           else "Mensch ist noch am Tilen"))
    try:
        if _ai_model is not None:
            # Netz-Modus: kein Text-Trace (anders als Heuristik), dafür Priors+PUCT-Stats im debug-Dict.
            res = _json.loads(_rust.ai_step_net_json(_ai_sims, _ai_c_puct, True))
        else:
            # KI-Drafting-Zug immer geloggt ausführen → Trace für den Debugger-Button.
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


@app.route('/api/ai/start_tile', methods=['GET', 'POST'])
def ai_start_tile():
    """KI legt ihre Startkuppelplatte (Rust-Heuristik)."""
    if (e := _require_game()) is not None:
        return e
    if _ai_player is None:
        return jsonify(err("KI-Spieler nicht gesetzt"))
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


@app.route('/api/ai/debug', methods=['GET'])
def ai_debug():
    """Analyse der AKTUELLEN Stellung (ohne Zug auszuführen), aus der Rust-KI."""
    if (e := _require_game()) is not None:
        return e
    if _ai_model is not None:
        analysis = _json.loads(_rust.ai_debug_net_json(_ai_sims, _ai_c_puct))
    else:
        analysis = _json.loads(_rust.ai_debug_json(_ai_sims))
    if not isinstance(analysis, dict):
        return jsonify({"ok": True, "moves": [], "current_player": _rust.current_player()})
    analysis["ok"] = True
    return jsonify(analysis)


@app.route('/api/ai/debug_history', methods=['GET'])
def ai_debug_history():
    """Komplette KI-Zug-Analyse-Historie des aktuellen Spiels."""
    return jsonify({"ok": True, "history": _ai_debug_history, "count": len(_ai_debug_history)})


@app.route('/api/ai/last_log', methods=['GET', 'POST'])
def ai_last_log():
    """Schreibt den vollständigen MCTS-Trace des ZULETZT gespielten KI-Zugs als Textdatei."""
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
    """Mentor Mode: Top-3 KI-Züge nach Visits (aus der Rust-MCTS-Analyse)."""
    if (e := _require_game()) is not None:
        return e
    try:
        if _ai_model is not None:
            analysis = _json.loads(_rust.ai_debug_net_json(_ai_sims, _ai_c_puct))
        else:
            analysis = _json.loads(_rust.ai_debug_json(_ai_sims))
        moves = analysis.get("moves", []) if isinstance(analysis, dict) else []
        top = sorted(moves, key=lambda m: m.get("mcts_visits", 0), reverse=True)[:3]
        suggestions = [{
            "action":  m.get("move"),
            "visits":  m.get("mcts_visits", 0),
            "win_pct": m.get("mcts_win_pct"),
        } for m in top]
        return jsonify({"ok": True, "suggestions": suggestions})
    except Exception as e:
        return jsonify(err(f"Suggest-Fehler: {str(e)}"))


if __name__ == '__main__':
    print("Mosaic-AI Server läuft auf http://localhost:5000")
    app.run(debug=True, port=5000)
