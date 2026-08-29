"""
Mosaic-AI — Flask API Server (Rust-Engine)

Alle Spiel- und KI-Logik läuft über die Rust-Engine (`mosaic_rust.PyGame`).
Es gibt keinen Python-Engine-/Agenten-Pfad mehr — `engine/` und `agents/`
werden vom Server nicht mehr importiert.

Endpoints:
  POST /api/new_game          — Neues Spiel starten
  GET  /api/state             — Aktuellen State abrufen
  POST /api/move/stone        — Stein-Zug (Aktion B/C)
  POST /api/move/dome                — Kuppelplatte aus Ablage (Aktion A)
  POST /api/move/dome_stack_peek     — Aktion A Schritt 1: verdeckt ziehen (-1Pkt, endet Zug nicht)
  POST /api/move/dome_stack_choose   — Aktion A Schritt 2: aufhören + Platte wählen (beendet Zug)
  POST /api/move/bonus_chip   — Bonusplättchen nehmen (Aktion D)
  POST /api/move/start_tile   — Startkachel platzieren (Vorbereitung)
  POST /api/tiling            — Tiling-Aktion (Phase 2)
  POST /api/end_tiling        — Tiling-Phase abschließen
  GET  /api/ai/config         — KI-Konfiguration abrufen
  POST /api/ai/config         — Schwierigkeit setzen
  GET  /api/aggression        — Task #28: Aggressivitäts-Regler abrufen (w, lambda_aggr)
  POST /api/aggression        — Task #28: Aggressivitäts-Regler setzen (sofort wirksam)
  POST /api/ai/move           — KI führt ihren nächsten Zug aus

Alle Responses: {"ok": true, "state": {...}} oder {"ok": false, "error": "..."}
"""

import sys
import os
import re as _re
import json as _json
import math as _math
import datetime as _dt
from pathlib import Path

# Stelle sicher dass der Hauptordner im Python-Path ist (nur im normalen
# Skriptbetrieb sinnvoll -- im PyInstaller-Bundle (Task #96) ist __file__
# keine reale Datei auf der Platte und dieser Schritt wird übersprungen).
# server.py liegt in der Repo-Wurzel, also ist `.parent` die Wurzel --
# hier stand `.parent.parent` und schob das ELTERNverzeichnis des Repos in
# den Importpfad (wirkungslos bis leicht schaedlich; die Importe trugen nur,
# weil Python das Skriptverzeichnis ohnehin einbindet). Korrigiert 2026-08-19.
if not getattr(sys, "frozen", False):
    BASE_DIR = str(Path(__file__).resolve().parent)
    sys.path.insert(0, BASE_DIR)

from flask import Flask, request, jsonify, send_from_directory
import threading
from config import MODELS_DIR
import player_profiles as _pp

# Frozen-Modus (PyInstaller onedir, Task #96): static/-Daten liegen neben der
# EXE (sys._MEIPASS), nicht relativ zu __file__ -- Bestandsverhalten (Dev)
# unverändert, da getattr(sys, "frozen", False) dort stets False ist.
if getattr(sys, "frozen", False):
    APP_DIR = Path(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))
else:
    APP_DIR = Path(__file__).resolve().parent

# Rust-Engine — einzige Engine. Ohne sie kann kein Spiel laufen.
try:
    import mosaic_rust as _mr
except ImportError:
    _mr = None

STATIC_DIR = APP_DIR / 'static'
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
LOG_DIR = APP_DIR / "static" / "log"
LOG_DIR.mkdir(parents=True, exist_ok=True)
# Spielerprofile / Elo (Nutzer-Erweiterung 2026-08-02): Logs GEWERTETER
# Partien werden zusaetzlich hierhin KOPIERT (Original bleibt in LOG_DIR
# liegen) -- siehe _archive_rated_game_log().
ELO_LOG_DIR = LOG_DIR / "elo"
ELO_LOG_DIR.mkdir(parents=True, exist_ok=True)

# ── KI-Konfiguration ─────────────────────────────────────────────────────────
_ai_player   = None        # 0 oder 1 — welcher Spieler ist die KI
_ai_sims     = 300         # MCTS-Basis-Simulationen der Rust-KI
_ai_model    = None        # None = Heuristik; sonst Versionsname (z.B. "v8") -> Netz-Modus
_ai_c_puct   = 1.5         # PUCT-Konstante im Netz-Modus (Standard wie net_mcts.rs)
_last_ai_log = None        # voller Such-Trace des zuletzt gespielten KI-Drafting-Zugs
_ai_lock     = threading.Lock()
_ai_debug_history = []     # Liste aller KI-Zug-Analysen des aktuellen Spiels

# ── Spielerprofile / Elo (Nutzer-Feature 2026-08-02) ─────────────────────────
# Aktive Profil-IDs (oder None = Gast/ungewertet) je Spielerindex fuer die
# LAUFENDE Partie -- gesetzt in /api/new_game, konsumiert in /api/end_scoring.
# `_game_rated` verhindert Doppel-Wertung, falls der Client /api/end_scoring
# mehrfach aufruft (z.B. Seiten-Reload nach Spielende). `_hints_used_this_game`
# wird in /api/ai/hint gesetzt (Feld `hints_used` im Historien-Eintrag, siehe
# player_profiles.py::apply_result -- ob deswegen spaeter mal automatisch
# unwertet werden soll, ist eine offene User-Entscheidung, siehe Bericht).
_profile_p0: str | None = None
_profile_p1: str | None = None
_game_rated = False
_hints_used_this_game = False

# Anker-Tabelle (Bradley-Terry-Fit aus evaluations/elo_history.csv) einmal
# beim Serverstart berechnen -- WIEDERVERWENDET tools/elo_tracker.py::fit_all,
# keine eigene Elo-Rechnung (siehe player_profiles.py-Moduldoc).
try:
    _pp.refresh_anchor_table()
except Exception as _e:
    print(f"WARNUNG: Elo-Anker-Tabelle konnte nicht geladen werden ({_e}) -- "
          f"Spielerprofile bleiben ungewertet, bis evaluations/elo_history.csv lesbar ist.")

# ── Lehrer-Modus (Task #97) ──────────────────────────────────────────────────
# 0=aus, 1=Kandidaten (ohne Zahlen), 2=+Bewertungen (Win%), 3=+Coach-Feedback.
_teacher_level      = 0
_teacher_sims       = 800   # Sims für /api/ai/hint
_teacher_coach_sims = 400   # Sims für Coach-Feedback OHNE Cache-Treffer (schneller als ein voller Hint)
_teacher_history    = []    # Liste der teacher_feedback-Einträge dieser Partie (für /api/teacher/summary)
_teacher_cache = {"key": None, "analysis": None}  # (log_len, current_player) -> zuletzt berechnete Analyse

def _champion_onnx_path(name: str) -> Path | None:
    """ONNX-Datei zu einem Versionsnamen (`v21_2d_brierbest`) oder None.

    Zwei Fundorte, in dieser Reihenfolge:

    1. `models/alphazero_<name>.onnx` -- der Bestandsplatz, den Training und
       `tools/set_champion.py` bedienen.
    2. `models/frozen_champions/<name>/model.onnx` -- das EINGEFRORENE
       Artefakt (docs/working_rules.md: ein Verzeichnis je Referenz). Seit
       dem Aufraeumen von `models/` liegt der amtierende Champion nur noch
       dort, und der Server fand ihn nicht mehr.

    Bewusst gehaertet wie `tools/arena.py::_champion_model_path`: kein stiller
    Ersatz durch ein anderes Modell, sondern None -- der Aufrufer entscheidet
    (Server: Warnung + Heuristik statt Absturz).
    """
    for candidate in (MODELS_DIR / f"alphazero_{name}.onnx",
                      MODELS_DIR / "frozen_champions" / name / "model.onnx"):
        if candidate.exists():
            return candidate
    return None


def _load_champion_model(fallback: str = "v16_best") -> str:
    """Liest den amtierenden Champion aus `models/champion.txt` (EINE Zeile,
    Versionsname wie `v17_best`) -- einzige Quelle der Wahrheit fuer den
    Server-Default, von `tools/set_champion.py` nach jedem entscheidenden
    Gating aktualisiert (siehe Nutzer-Anstoss 2026-07-27: "sobald neuer
    Champ da ist, sofort in das Server-Game ruebernehmen"). Fehlt die Datei
    (frischer Checkout ohne `models/`-Snapshot) oder ist sie leer, faellt
    dies auf `fallback` zurueck -- rein additiv, kein Hard-Error beim
    Serverstart."""
    try:
        name = (MODELS_DIR / "champion.txt").read_text(encoding="utf-8").strip()
        name = name or fallback
    except OSError:
        name = fallback
    # Audit-V2 (2026-08-05): Existenz des ONNX pruefen und LAUT warnen --
    # vorher konnte der Server bei fehlender Datei (OneDrive-Verlust)
    # kommentarlos mit einem falschen/fehlenden Modell starten. Bewusst
    # weiterhin kein Hard-Error beim Serverstart (GUI soll hochkommen),
    # aber die Warnung macht den Zustand sichtbar.
    if _champion_onnx_path(name) is None:
        print(f"⚠️  WARNUNG: Champion-ONNX zu '{name}' fehlt -- weder "
              f"alphazero_{name}.onnx noch frozen_champions/{name}/model.onnx "
              f"in {MODELS_DIR}. Modell-Laden wird fehlschlagen "
              f"(champion.txt pruefen, OneDrive-Verlust?).")
    return name

_CHAMPION_MODEL = _load_champion_model()

# Difficulty Presets — Format: {"model": "<version>", "sims": <int>}
DIFFICULTY_PRESETS = {
    # medium/hard/expert/_default zeigen alle auf denselben amtierenden
    # Champion (nur die Sim-Zahl unterscheidet die Staerke) -- der Name
    # kommt dynamisch aus `models/champion.txt`, s.o. `_load_champion_model`.
    "easy":   {"model": "heuristic",     "sims": 60},
    "medium": {"model": _CHAMPION_MODEL, "sims": 60},
    "hard":   {"model": _CHAMPION_MODEL, "sims": 150},
    "expert": {"model": _CHAMPION_MODEL, "sims": 400},
    "_default": {"model": _CHAMPION_MODEL, "sims": 400},
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
    Akzeptiert auch einen bereits vollständigen Pfad/Dateinamen.

    Versionsnamen loest `_champion_onnx_path` auf (Bestandsplatz zuerst,
    dann das gefrorene Artefakt)."""
    if not model or model.strip().lower() in ("", "heuristic", "heuristik"):
        return None
    m = model.strip()
    # Direkte Pfad-/Dateinamen-Angabe hat Vorrang (Bestandsverhalten).
    for c in (Path(m), MODELS_DIR / m):
        if c.suffix == ".onnx" and c.exists():
            return c
    return _champion_onnx_path(m)


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


# ── Lehrer-Modus: Beschreibungs-Parsing + Analyse-Cache ─────────────────────
# Die Regexe UND die move_key/played_key-Logik sind bewusst aus
# tools/analyze_game_log.py dupliziert (dort battle-tested für exakt dasselbe
# Problem: eine gespielte Aktion gegen die von ai_debug_*_json gelabelten
# Kandidaten abgleichen), NICHT importiert -- tools/ wird nicht ins
# PyInstaller-Bundle gepackt (siehe mosaic_release.spec), server.py muss
# eigenständig lauffähig bleiben.
_T_STONE_DESC_RE = _re.compile(
    r"Stein (?P<color>\S+) (?:von|vom) (?P<src>F\d+|GF|Mondpool) → (?P<dest>Reihe \d+|Strafleiste)"
)
_T_DOME_DISPLAY_DESC_RE = _re.compile(r"Kuppel #(?P<tile>\d+) → \((?P<r>\d+),(?P<c>\d+)\)")
_T_DOME_STACK_DESC_RE = _re.compile(r"Stapel → \((?P<r>\d+),(?P<c>\d+)\)")
_T_BONUS_DESC_RE = _re.compile(r"Bonuschip F(?P<fid>\d+)")


def _teacher_move_key(typ: str, desc: str):
    """Vergleichsschlüssel EINES Kandidaten aus moves[] (Analyse-Dict) --
    Pendant zu analyze_game_log.py::move_key."""
    if typ == "stone":
        m = _T_STONE_DESC_RE.search(desc or "")
        return ("stone", m.group("color"), m.group("src"), m.group("dest")) if m else None
    if typ == "choose_dome_slot":
        m = _T_DOME_DISPLAY_DESC_RE.search(desc or "")
        return ("dome_display", m.group("tile"), m.group("r"), m.group("c")) if m else None
    if typ == "choose_draw_stack_slot":
        m = _T_DOME_STACK_DESC_RE.search(desc or "")
        return ("dome_stack", m.group("r"), m.group("c")) if m else None
    if typ == "dome_stack_peek":
        return ("dome_stack_peek",)
    if typ == "bonus_chip":
        m = _T_BONUS_DESC_RE.search(desc or "")
        return ("bonus_chip", m.group("fid")) if m else None
    return None


def _teacher_played_key(kind: str, **f):
    """Vergleichsschlüssel der TATSÄCHLICH gespielten Aktion, direkt aus den
    Request-Parametern gebaut (kein Text-Parsing nötig, wir haben die
    strukturierten Felder bereits) -- Pendant zu analyze_game_log.py::played_key.
    Gibt exakt dieselbe Tupel-Form wie `_teacher_move_key` zurück, damit beide
    vergleichbar sind."""
    if kind == "stone":
        # Punkt 9-Nachtrag (engine-seitige Disambiguierung in
        # mcts.rs::label_search_move, siehe Kommentar unten): factory_id=None
        # ist zweideutig (echte Grossfabrik-Ziehung ODER globaler Mondpool-Zug,
        # Aktion C) -- der `source`-Rohwert aus der Request (identisch zu
        # `serialize::source_name`, z.B. "SMALL_FACTORY_MOON") loest das auf.
        # `source` ist optional (Rueckwaertskompatibilitaet mit Aufrufern, die
        # ihn nicht mitgeben) -- fehlt er, wird wie bisher auf "GF" geraten.
        if f["factory_id"] is not None:
            src = f"F{f['factory_id']}"
        elif f.get("source") == "SMALL_FACTORY_MOON":
            src = "Mondpool"
        else:
            src = "GF"
        dest = "Strafleiste" if f["row"] < 0 else f"Reihe {f['row'] + 1}"
        return ("stone", f["color"], src, dest)
    if kind == "dome_display":
        return ("dome_display", str(f["tile_id"]), str(f["slot_row"]), str(f["slot_col"]))
    if kind == "dome_stack":
        return ("dome_stack", str(f["slot_row"]), str(f["slot_col"]))
    if kind == "dome_stack_peek":
        return ("dome_stack_peek",)
    if kind == "bonus_chip":
        return ("bonus_chip", str(f["factory_id"]))
    raise ValueError(kind)


TEACHER_HINT_TOP_N = 3  # Nutzer-Feedback: max. 3 Kandidaten (vorher 5), alle Stufen.


# Punkt 9 (Nutzer-Feedback 2026-08-02, Live-Spiel-Log game_20260802_151513_seed631890),
# NACHTRAG (Folgeauftrag am selben Tag): `label_search_move` (engine/src/mcts.rs)
# baute die Anzeige-Beschreibung eines Stein-Zugs bisher als
# "...Stein {color} von {src} → {dest}" mit
#     src = match m.take.factory_id { Some(id) => "F{id}", None => "GF" }
# -- das war NUR fuer echte Grossfabrik-Ziehungen (TakeSource::LargeFactorySun/
# -Moon) korrekt. Aktion C (geteilter Mondpool, TakeSource::SmallFactoryMoon mit
# factory_id=None -- der EINZIGE andere Fall, der ebenfalls factory_id=None hat,
# siehe engine/src/moves.rs::is_global_moon_take) wurde von derselben Match-Arm
# faelschlich GENAUSO als "GF" gelabelt. Der reale Spiel-LOG war davon nie
# betroffen (execute_moon_take in execution.rs listet die beitragenden Fabriken
# einzeln auf) -- nur dieser Lehrer-Tipp-/Coach-Text.
#
# FIX AN DER QUELLE: `label_search_move` disambiguiert jetzt selbst (emittiert
# "Mondpool" statt "GF" fuer Aktion C, inkl. korrekter Praeposition "vom").
# Die frueher hier lebende Nachbearbeitung (`_fix_moon_pool_label`, Text-Regex
# + Live-State-Abfrage) ist dadurch ueberfluessig geworden und wurde entfernt.
# `_T_STONE_DESC_RE` akzeptiert "Mondpool" als dritten `src`-Wert (neben
# F\d+/GF); `_teacher_played_key` loest die verbleibende Ambiguitaet der
# GESPIELTEN Aktion (dort liegt kein Text vor) ueber das rohe `source`-Feld
# der Request auf (siehe dort).
def _teacher_describe_move(mv: dict) -> str:
    """Anzeige-Beschreibung EINES Analyse-Kandidaten für Lehrer-Ausgaben (Hint-
    Kandidaten UND Coach-`bester_zug_description`). Hängt bei Kuppel-Zügen
    (choose_dome_slot/choose_draw_stack_slot) die Rotation an, FALLS die Suche
    dafür eine Rotationswahl gefunden hat (`best_rotation`-Kind-Knoten-Feld,
    siehe engine/src/net_mcts.rs bzw. mcts.rs -- `null`, wenn der Suchbaum an
    dieser Stelle nie bis zur Rotationsstufe vertieft wurde, z.B. bei kleinem
    Sim-Budget). Die ROHE `description` (ohne Rotation) bleibt unverändert für
    das Matching in `_teacher_move_key`."""
    desc = mv.get("description") or ""
    if mv.get("type") in ("choose_dome_slot", "choose_draw_stack_slot"):
        br = mv.get("best_rotation")
        if isinstance(br, dict) and br.get("rotation") is not None:
            desc = f"{desc}, {int(br['rotation'])}°"
    return desc


def _teacher_action_params(typ: str, desc: str) -> dict | None:
    """Strukturierte Parameter EINES Kandidaten für die Brett-Markierung im
    Frontend (Quell-Fabrik/Farbe/Zielreihe bzw. Kuppel-Slot). Funktioniert
    identisch für Heuristik- UND Netz-Pfad (beide liefern `description` im
    selben Format), anders als das rohe `action`-Feld aus moves[] (nur im
    Netz-Pfad befüllt, siehe net_mcts.rs::action_to_env_dict)."""
    if typ == "stone":
        m = _T_STONE_DESC_RE.search(desc or "")
        if not m:
            return None
        dest = m.group("dest")
        row = -1 if dest == "Strafleiste" else int(dest.split(" ")[1]) - 1
        src = m.group("src")
        factory_id = int(src[1:]) if src not in ("GF", "Mondpool") else None
        # `source` ist die disambiguierte Roh-Quelle ("GF"/"Mondpool"/"F3") --
        # rein additiv, loest die vorher auf factory_id=None kollabierte
        # GF/Mondpool-Ambiguitaet fuer Konsumenten (z.B. Brett-Highlight im
        # Frontend) explizit auf, ohne bestehende `factory_id`-Semantik zu
        # aendern (die bleibt fuer beide Faelle None, wie schon immer).
        return {"color": m.group("color"), "factory_id": factory_id, "row": row, "source": src}
    if typ == "choose_dome_slot":
        m = _T_DOME_DISPLAY_DESC_RE.search(desc or "")
        if not m:
            return None
        return {"tile_id": int(m.group("tile")), "slot_row": int(m.group("r")), "slot_col": int(m.group("c"))}
    if typ == "choose_draw_stack_slot":
        m = _T_DOME_STACK_DESC_RE.search(desc or "")
        if not m:
            return None
        return {"slot_row": int(m.group("r")), "slot_col": int(m.group("c"))}
    if typ == "dome_stack_peek":
        return {}
    if typ == "bonus_chip":
        m = _T_BONUS_DESC_RE.search(desc or "")
        if not m:
            return None
        return {"factory_id": int(m.group("fid"))}
    return None


def _teacher_compute_analysis(sims: int) -> dict | None:
    """Analyse der AKTUELLEN Stellung aus Sicht des current_player (Mensch
    ODER KI, `ai_debug_net_json` ist bereits Ego-perspektivisch) -- identische
    Semantik wie /api/ai/debug, nur mit eigener Sim-Zahl für den Lehrer-Modus.
    Nutzt das GELADENE Netz (= der KI-Gegner dieser Partie). Ist keines
    geladen (Heuristik-Gegner), fällt es pragmatisch auf die Heuristik-Analyse
    zurück (`ai_debug_json`) -- ein Lehrer-Hinweis ist auch mit gröberer
    Heuristik-Schätzung besser als gar keiner; der Aufrufer markiert diesen
    Fall über `_ai_model is None` im Response (`note`-Feld)."""
    if _rust is None:
        return None
    try:
        if _ai_model is not None:
            return _calibrate_display_win_prob(
                _json.loads(_rust.ai_debug_net_json(sims, _ai_c_puct)))
        return _json.loads(_rust.ai_debug_json(sims))
    except Exception:
        return None


def _teacher_cached_or_fresh_analysis(sims: int) -> dict | None:
    """Cache-Schlüssel = (log_len, current_player) -- log_len steigt bei JEDER
    zustandsändernden Aktion (siehe _rust_flush_log/Replay-Validierung in
    tools/analyze_game_log.py), ist also ein zuverlässiger "Zustands-Zähler"
    ohne eigene Zusatz-Buchhaltung. Ein vorheriger /api/ai/hint-Abruf
    DERSELBEN Stellung wird hier wiederverwendet (eliminiert die Coach-
    Latenz beim nachfolgenden Zug); sonst wird frisch mit `sims` gerechnet."""
    global _teacher_cache
    if _rust is None:
        return None
    key = (_rust.log_len(), _rust.current_player())
    if _teacher_cache.get("key") == key and _teacher_cache.get("analysis") is not None:
        return _teacher_cache["analysis"]
    analysis = _teacher_compute_analysis(sims)
    if analysis is not None:
        _teacher_cache = {"key": key, "analysis": analysis}
    return analysis


def _teacher_pre_move_snapshot() -> dict | None:
    """Vor einem menschlichen Drafting-Zug (nur Stufe 3 = Coach): liefert die
    (evtl. gecachte) Analyse des VOR-Zustands, oder None, wenn Coach nicht
    aktiv/anwendbar ist. Bei teacher_level != 3 wird sofort None
    zurückgegeben -- KEIN zusätzlicher MCTS-Aufruf, KEINE Zusatzlatenz für
    Stufe 0/1/2."""
    try:
        if _teacher_level != 3 or _ai_player is None or _rust is None:
            return None
        if _rust.phase() != "drafting" or _rust.current_player() == _ai_player:
            return None
        return _teacher_cached_or_fresh_analysis(_teacher_coach_sims)
    except Exception:
        return None


def _teacher_feedback_from_snapshot(analysis: dict | None, kind: str, played_key) -> dict | None:
    """Vergleicht die gespielte Aktion (`played_key`) gegen die VOR-Zustands-
    Analyse `analysis` (aus `_teacher_pre_move_snapshot`, VOR dem Zug geholt).
    Bei Kuppel-Zweistufigkeit wird -- wie in tools/analyze_game_log.py -- NUR
    die erste Stufe (Kachel/Stapel + Slot) bewertet, nie die Rotationswahl
    danach (die ist ohnehin kein eigener Analyse-Kandidat). Hängt bei Erfolg
    einen Eintrag an `_teacher_history` (für /api/teacher/summary) und gibt
    das Response-Feld {rang, delta_win_pp, bester_zug_description} zurück,
    oder None (kein Match / keine Analyse verfügbar -> kein teacher_feedback
    im Response, aber der Zug selbst bleibt unberührt)."""
    if not analysis or played_key is None:
        return None
    moves = analysis.get("moves") or []
    if not moves:
        return None
    matches = [m for m in moves if _teacher_move_key(m.get("type"), m.get("description", "")) == played_key]
    if not matches:
        return None
    ranked = sorted(moves, key=lambda m: -(m.get("mcts_q") or 0.0))
    top_q = ranked[0].get("mcts_q") or 0.0
    top_desc = _teacher_describe_move(ranked[0])
    played_q = max((m.get("mcts_q") or 0.0) for m in matches)
    rang = 1 + sum(1 for m in moves if (m.get("mcts_q") or 0.0) > played_q + 1e-12)
    delta = round((top_q - played_q) * 100.0, 1)
    _teacher_history.append({
        "round": _rust.round_number() if _rust is not None else None,
        "kind": kind, "rang": rang, "delta_win_pp": delta, "top_desc": top_desc,
    })
    return {"rang": rang, "delta_win_pp": delta, "bester_zug_description": top_desc}


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
    global _teacher_level, _teacher_sims, _teacher_coach_sims, _teacher_history, _teacher_cache
    global _profile_p0, _profile_p1, _game_rated, _hints_used_this_game
    _ai_debug_history = []
    data = request.get_json(silent=True) or {}
    names      = data.get('names', ['Spieler 1', 'Spieler 2'])
    seed       = data.get('seed', None)
    ai_enabled = data.get('ai_enabled', False)
    difficulty = data.get('difficulty', 'medium')
    ai_side    = data.get('ai_side', 1)   # 0 = KI ist P1, 1 = KI ist P2

    # Spielerprofile (Nutzer-Feature 2026-08-02): ungueltige/leere IDs werden
    # stillschweigend als Gast (None, ungewertet) behandelt -- kein Hard-Error,
    # das Spiel soll auch ohne Profil-Auswahl ganz normal starten.
    def _resolve_profile_id(raw):
        pid = (raw or "").strip() if isinstance(raw, str) else None
        return pid if pid and _pp.get_profile(pid) is not None else None

    _profile_p0 = _resolve_profile_id(data.get('profile_p0'))
    _profile_p1 = _resolve_profile_id(data.get('profile_p1'))
    _game_rated = False
    _hints_used_this_game = False

    # Lehrer-Modus (Task #97): 0=aus (Default -- Bestandsverhalten unverändert),
    # 1=Kandidaten, 2=+Bewertungen, 3=+Coach-Feedback. Pro Partie zurückgesetzt.
    try:
        teacher_level = int(data.get('teacher_level', 0) or 0)
    except (TypeError, ValueError):
        teacher_level = 0
    if teacher_level not in (0, 1, 2, 3):
        teacher_level = 0
    _teacher_level      = teacher_level
    _teacher_sims       = int(data.get('teacher_sims', 800) or 800)
    _teacher_coach_sims = int(data.get('teacher_coach_sims', 400) or 400)
    _teacher_history    = []
    _teacher_cache      = {"key": None, "analysis": None}

    # Spielerprofile / Elo (User-Entscheid 2026-08-02): Coach-Stufe 3 gibt
    # AUTOMATISCH nach jedem Zug eine KI-Zugempfehlung (_teacher_feedback_
    # from_snapshot in den Move-Handlern, "bester_zug_description") -- das
    # ist eine KI-Hilfe genau wie der manuelle Tipp-Button (/api/ai/hint,
    # setzt dasselbe Flag), nur eben automatisch statt auf Klick. Die Partie
    # gilt daher schon ab Spielstart als "mit KI-Hilfe" -- NICHT erst, wenn
    # tatsaechlich mal ein Feedback-Match gefunden wird (waere unnoetig
    # unklar: die Stufe wurde bewusst gewaehlt). Stufe 1/2 geben NUR auf
    # Klick Hinweise (derselbe /api/ai/hint-Kanal) -- kein automatischer
    # Trigger hier. Das reine Debug-Panel (/debug, ai_debug_json/ai_suggest)
    # zaehlt bewusst NICHT: es zeigt Bewertungen/Analyse, aber liefert keine
    # Zugempfehlung im normalen Spielfluss und ist nur ueber die separate
    # Debug-Seite erreichbar, nicht Teil der Partie-UI.
    if teacher_level == 3 and ai_enabled:
        _hints_used_this_game = True

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
                model_warning = f"Netz '{requested_model}' konnte nicht geladen werden ({e}) - spiele gegen Heuristik."
                _ai_model = None
        else:
            if requested_model and requested_model.strip().lower() not in ("", "heuristic", "heuristik"):
                model_warning = (f"Modell '{requested_model}' nicht gefunden "
                                 f"(weder models/alphazero_{requested_model}.onnx noch "
                                 f"models/frozen_champions/{requested_model}/model.onnx) "
                                 f"- spiele gegen Heuristik.")
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
            "teacher_level":      _teacher_level,
            "teacher_sims":       _teacher_sims if _teacher_level else None,
            "teacher_coach_sims": _teacher_coach_sims if _teacher_level == 3 else None,
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
    response['teacher_level']      = _teacher_level
    response['teacher_sims']       = _teacher_sims
    response['teacher_coach_sims'] = _teacher_coach_sims

    # Spielerprofile: aufgeloeste Profil-Daten (fuer sofortige Rating-Anzeige
    # im Frontend ohne Extra-Request) + KI-Elo-Anker (falls gegen KI gespielt
    # wird) -- Schaetzwerte (is_estimate=True) markiert das Frontend mit "~".
    response['profile_p0'] = _pp.get_profile(_profile_p0) if _profile_p0 else None
    response['profile_p1'] = _pp.get_profile(_profile_p1) if _profile_p1 else None
    # Coach-Stufe 3 macht die Partie schon ab Start ungewertet (s.o.) --
    # Frontend zeigt das persistente "ungewertet"-Badge dann sofort, ohne
    # auf einen Tipp-Klick zu warten.
    response['hints_used'] = _hints_used_this_game
    if ai_enabled:
        ai_identity = _ai_model or "Heuristik"
        ai_elo, ai_is_estimate, ai_node = _pp.estimate_ai_anchor(ai_identity, _ai_sims)
        response['ai_rating'] = {
            "node": ai_node or f"{ai_identity}@{_ai_sims}",
            "elo": round(ai_elo, 1) if ai_elo is not None else None,
            "is_estimate": ai_is_estimate,
        }
    return jsonify(response)


@app.route('/api/state', methods=['GET'])
def get_state():
    if (e := _require_game()) is not None:
        return e
    return jsonify(ok())


@app.route('/api/champion', methods=['GET'])
def get_champion():
    """Amtierender Champion (`models/champion.txt`, siehe `_load_champion_model`)
    -- Frontend nutzt das, um das Modell-Feld im Neues-Spiel-Modal beim Oeffnen
    automatisch auf den aktuellen Stand zu setzen (Nutzer-Anstoss 2026-07-27:
    "ich dachte hier wird dann immer der aktuelle Champ verwendet"), statt
    einen Versionsnamen im HTML hart zu kodieren, der bei jedem Champion-
    Wechsel veraltet."""
    return jsonify({"ok": True, "model": _CHAMPION_MODEL})


@app.route('/api/profiles', methods=['GET'])
def list_profiles():
    """Alle lokalen Spielerprofile (id/name/rating/games_rated), alphabetisch
    -- fuer die Profil-Auswahl im Neues-Spiel-Modal."""
    return jsonify({"ok": True, "profiles": _pp.list_profiles()})


@app.route('/api/profiles', methods=['POST'])
def create_profile():
    """Legt ein neues Spielerprofil an (Start-Rating 1000)."""
    data = request.get_json(silent=True) or {}
    try:
        profile = _pp.create_profile(data.get('name', ''))
        return jsonify({"ok": True, "profile": profile})
    except ValueError as e:
        return jsonify(err(str(e)))


@app.route('/api/log_info', methods=['GET'])
def log_info():
    """Dateiname des Spiel-Logs der laufenden Partie (für den Download-Button im Frontend)."""
    if _game_log_path is None:
        return jsonify(err("Noch kein Spiel-Log vorhanden."))
    return jsonify({
        "ok": True,
        "log_file": _game_log_path.name,
        "url": f"/static/log/{_game_log_path.name}",
    })


def _stack_draw_lock():
    """Nutzer-Feedback 2026-08-07: Aktion A (Stapel-Zug) ist EIN
    durchgaengiger Zug. Laufen bereits Ziehungen (pending_stack_draw),
    sind andere Drafting-Aktionen ungueltig -- die Engine GENERIERT sie
    korrekt nicht mehr (game.rs::drafting_actions), aber die Move-
    Endpoints wandten Zuege bisher ohne diese Pruefung an (gleiche
    Fehlerklasse wie Audit-U1: Apply-Ebene ohne Sperre). Hier die
    apply-seitige Verteidigungslinie."""
    try:
        st = _json.loads(_rust.state_json())
        if st.get('pending_stack_draw'):
            return jsonify(err("Stapel-Zug läuft - bitte erst eine gezogene Platte wählen und legen."))
    except Exception:
        pass
    return None


@app.route('/api/move/stone', methods=['POST'])
def move_stone():
    if (e := _require_game()) is not None:
        return e
    if (e := _stack_draw_lock()) is not None:
        return e
    if not _both_start_placed():
        return jsonify(err("Startkacheln fehlen."))
    d = request.get_json()
    try:
        raw = d.get('factory_id')
        fid = int(raw) if raw is not None else None
        row = int(d['row'])
        pre_analysis = _teacher_pre_move_snapshot()
        _rust.apply_stone(d['source'], d['color'], row,
                          fid, list(d.get('moon_order', [])))
        _flush_game_log()
        resp = ok()
        fb = _teacher_feedback_from_snapshot(
            pre_analysis, "stone",
            _teacher_played_key("stone", color=d['color'], factory_id=fid, row=row, source=d.get('source')))
        if fb:
            resp["teacher_feedback"] = fb
        return jsonify(resp)
    except Exception as e:
        return jsonify(err(str(e)))


@app.route('/api/move/dome', methods=['POST'])
def move_dome():
    if (e := _require_game()) is not None:
        return e
    if (e := _stack_draw_lock()) is not None:
        return e
    if not _both_start_placed():
        return jsonify(err("Startkacheln fehlen."))
    d = request.get_json()
    try:
        tile_id, slot_row, slot_col = int(d['tile_id']), int(d['slot_row']), int(d['slot_col'])
        pre_analysis = _teacher_pre_move_snapshot()
        _rust.apply_dome(tile_id, slot_row, slot_col, int(d.get('rotation', 0)))
        _flush_game_log()
        resp = ok()
        fb = _teacher_feedback_from_snapshot(
            pre_analysis, "dome_display",
            _teacher_played_key("dome_display", tile_id=tile_id, slot_row=slot_row, slot_col=slot_col))
        if fb:
            resp["teacher_feedback"] = fb
        return jsonify(resp)
    except Exception as e:
        return jsonify(err(str(e) or "Zug abgelehnt."))


@app.route('/api/move/dome_stack_peek', methods=['POST'])
def move_dome_stack_peek():
    """Aktion A, Schritt 1: eine weitere verdeckte Kuppelplatte ziehen (-1 Pkt).
    Beendet den Zug NICHT -- Rückseite zeigt nur den Typ (special/wild), die
    Vorderseite kommt erst mit move_dome_stack_choose. Gibt den gezogenen Typ
    zurück, damit das Frontend "Special!"/"Wild." anzeigen kann."""
    if (e := _require_game()) is not None:
        return e
    if not _both_start_placed():
        return jsonify(err("Startkacheln fehlen."))
    try:
        pre_analysis = _teacher_pre_move_snapshot()
        typ = _rust.apply_dome_stack_peek()
        _flush_game_log()
        res = ok()
        res['type'] = typ
        fb = _teacher_feedback_from_snapshot(pre_analysis, "dome_stack_peek", _teacher_played_key("dome_stack_peek"))
        if fb:
            res["teacher_feedback"] = fb
        return jsonify(res)
    except Exception as e:
        return jsonify(err(str(e) or "Zug abgelehnt."))


@app.route('/api/move/dome_stack_choose', methods=['POST'])
def move_dome_stack_choose():
    """Aktion A, Schritt 2: das Ziehen beenden -- eine der bisher gezogenen
    Platten (state.pending_stack_draw) wählen und platzieren, Rest zurück
    unter den Stapel. Beendet den Zug."""
    if (e := _require_game()) is not None:
        return e
    if not _both_start_placed():
        return jsonify(err("Startkacheln fehlen."))
    d = request.get_json()
    try:
        return_order = d.get('return_order')
        if return_order is not None:
            return_order = [int(x) for x in return_order]
        slot_row, slot_col = int(d['slot_row']), int(d['slot_col'])
        pre_analysis = _teacher_pre_move_snapshot()
        _rust.apply_dome_stack_choose(int(d['chosen_id']),
                                      slot_row, slot_col,
                                      int(d.get('rotation', 0)), return_order)
        _flush_game_log()
        resp = ok()
        fb = _teacher_feedback_from_snapshot(
            pre_analysis, "dome_stack", _teacher_played_key("dome_stack", slot_row=slot_row, slot_col=slot_col))
        if fb:
            resp["teacher_feedback"] = fb
        return jsonify(resp)
    except Exception as e:
        return jsonify(err(str(e) or "Zug abgelehnt."))


@app.route('/api/move/bonus_chip', methods=['POST'])
def move_bonus_chip():
    if (e := _require_game()) is not None:
        return e
    if (e := _stack_draw_lock()) is not None:
        return e
    if not _both_start_placed():
        return jsonify(err("Startkacheln fehlen."))
    d = request.get_json()
    try:
        factory_id = int(d['factory_id'])
        pre_analysis = _teacher_pre_move_snapshot()
        _rust.apply_bonus_chip(factory_id)
        _flush_game_log()
        resp = ok()
        fb = _teacher_feedback_from_snapshot(
            pre_analysis, "bonus_chip", _teacher_played_key("bonus_chip", factory_id=factory_id))
        if fb:
            resp["teacher_feedback"] = fb
        return jsonify(resp)
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
        return jsonify(err("Passen nicht erlaubt - es gibt noch gültige Aktionen."))
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


def _archive_rated_game_log() -> str | None:
    """Kopiert das Log der GERADE beendeten (gewerteten) Partie nach
    ELO_LOG_DIR (static/log/elo/) -- Nutzer-Erweiterung 2026-08-02. Original
    bleibt UNVERAENDERT in LOG_DIR liegen (kein `move`/`rename`): der
    Log-Writer haelt nie eine offene Dateihandle zwischen Requests (jeder
    `_flush_game_log()`-Aufruf oeffnet/schreibt/schliesst synchron innerhalb
    EINES Requests, siehe dortige `with open(..., 'a') as lf:`-Musters) --
    zum Zeitpunkt dieses Aufrufs (innerhalb von /api/end_scoring, NACH dem
    dortigen `_flush_game_log()`) ist die Datei also immer vollstaendig
    geschrieben und geschlossen, ein direktes Kopieren ist sicher. Trotzdem
    bewusst KOPIEREN statt VERSCHIEBEN (nicht `move`): (a) der Client ruft
    `/api/end_game_log` (haengt die SPIELENDE-Zusammenfassung an) typischerweise
    VOR `/api/end_scoring` auf, aber ungesichert per Race (beides sind
    unabhaengige Fetches) -- ein `move` hier koennte der ANHAENGENDEN
    end_game_log-Schreibung die Datei unter den Fuessen wegziehen und einen
    FileNotFoundError ausloesen; (b) der bestehende Download-Button
    ("📄 Log") zeigt weiterhin auf LOG_DIR und soll nach der Wertung nicht
    kaputtgehen. Gibt den Dateinamen im Archiv zurueck, oder None bei Fehler
    (dann faellt der Historien-Eintrag auf den Original-Dateinamen in
    LOG_DIR zurueck -- nie ein Hard-Error, Wertung selbst bleibt unberuehrt)."""
    if _game_log_path is None or not _game_log_path.exists():
        return None
    try:
        import shutil as _shutil
        dest = ELO_LOG_DIR / _game_log_path.name
        _shutil.copy2(_game_log_path, dest)
        return dest.name
    except OSError as e:
        print(f"WARNUNG: Log-Archivierung fuer gewertete Partie fehlgeschlagen ({e}) -- "
              f"Original bleibt in {LOG_DIR}, nur die Elo-Historie referenziert den Original-Pfad.")
        return None


def _mirror_determine_winner(state: dict) -> int:
    """Python-Nachbildung von engine/src/game.rs::determine_winner (REIN
    LESEND aus state_json, keine Engine-Aenderung) -- Punktegleichstand wird
    exakt wie dort per `first_player_next_round` aufgeloest (siehe
    game.rs-Kommentar: `holds_first_player_marker` ist zu diesem Zeitpunkt
    immer false, score_penalty loescht es bei jeder Rundenwertung)."""
    s0 = state["players"][0]["score"]
    s1 = state["players"][1]["score"]
    if s0 > s1:
        return 0
    if s1 > s0:
        return 1
    return state["first_player_next_round"]


def _apply_elo_for_finished_game(state: dict) -> dict:
    """Spielerprofile-Feature (2026-08-02): wertet die GERADE beendete
    Partie fuer alle ausgewaehlten Profile per Standard-Elo (KI-Ratings sind
    fixe Anker, siehe player_profiles.py). Wird vom Aufrufer GENAU EINMAL
    pro Partie aufgerufen (Idempotenz-Schutz per `_game_rated`-Flag) -- ein
    spaeterer Reload/erneuter /api/end_scoring-Aufruf darf nicht nochmal
    werten. Gibt {"0": entry|None, "1": entry|None, "note": str|None}
    zurueck, vom Frontend fuer die Endwertungs-Anzeige genutzt.

    User-Entscheid 2026-08-02: sobald IRGENDWO in der Partie KI-Hilfe genutzt
    wurde (`_hints_used_this_game` -- manueller Tipp ODER automatisches
    Coach-Feedback Stufe 3, siehe new_game()/ai_hint()), wird sie fuer ALLE
    beteiligten Profile ungewertet (`_pp.record_unrated` statt
    `_pp.apply_result`) -- Rating bleibt unveraendert, aber ein Historien-
    Eintrag mit `rated:false` wird trotzdem geschrieben (Transparenz: "das
    hast du gespielt", keine Wertungsgrundlage).

    Abgebrochene Spiele (kein /api/end_scoring erreicht) werten sich von
    selbst nie -- es gibt bewusst keinen expliziten Abbruch-Zustand."""
    winner = _mirror_determine_winner(state)
    # Unentschieden ist nach aktuellem Regelwerk NIE erreichbar (siehe
    # determine_winner-Tie-Break oben) -- Pfad bleibt fuer kuenftige
    # Regelaenderungen (Design-Vorgabe #4).
    result_p0 = 1.0 if winner == 0 else 0.0
    result_p1 = 1.0 - result_p0
    rated = not _hints_used_this_game

    # Seed + Log-Referenz (Nutzer-Erweiterung 2026-08-02): NUR gewertete
    # Partien werden nach ELO_LOG_DIR kopiert (Original bleibt zusaetzlich in
    # LOG_DIR) -- ungewertete Partien (Tipps genutzt) referenzieren weiterhin
    # den Original-Dateinamen in LOG_DIR, siehe player_profiles.py-Doku. Die
    # Archivierung passiert LAZY (memoized Closure) und hoechstens einmal je
    # Partie -- NICHT schon hier oben, sonst wuerden auch Gast-Spiele ohne
    # jedes ausgewaehlte Profil unnoetig archiviert (erst `_record()` weiss,
    # ob ueberhaupt ein Profil tatsaechlich gewertet wird).
    seed = _rust.seed() if _rust is not None else None
    _orig_log_name = _game_log_path.name if _game_log_path is not None else None
    _archive_cache = {"done": False, "name": _orig_log_name}

    def _log_ref():
        if rated and not _archive_cache["done"]:
            _archive_cache["name"] = _archive_rated_game_log() or _orig_log_name
            _archive_cache["done"] = True
        return _archive_cache["name"]

    out = {"0": None, "1": None, "note": None}

    def _record(pid, opponent_label, opponent_rating, opponent_is_estimate, result):
        # Vorfall 2026-08-02: pro-Profil abgesichert, damit ein fehlendes/
        # nicht mehr auffindbares Profil (Datei zwischenzeitlich geleert/
        # ersetzt) NICHT die Wertung der ANDEREN Seite mitreisst (Mensch-vs-
        # Mensch) und v.a. NICHT die gesamte /api/end_scoring-Antwort zum
        # Fehler macht (siehe End-Route: dort sitzt zusaetzlich ein globaler
        # Schutz als zweite Verteidigungslinie fuer alles andere).
        try:
            if rated:
                return _pp.apply_result(pid, opponent_label, opponent_rating,
                                         opponent_is_estimate, result, False,
                                         seed=seed, log=_log_ref())
            return _pp.record_unrated(pid, opponent_label, opponent_rating,
                                       opponent_is_estimate, result,
                                       seed=seed, log=_orig_log_name)
        except KeyError:
            print(f"WARNUNG: Elo-Update fuer Profil-ID '{pid}' uebersprungen -- "
                  f"Profil nicht gefunden (Datei evtl. zwischenzeitlich geleert/ersetzt).")
            out["note"] = out["note"] or "Rating nicht gespeichert: Profil nicht gefunden."
            return None
        except Exception as e:
            print(f"WARNUNG: Elo-Update fuer Profil-ID '{pid}' fehlgeschlagen "
                  f"({type(e).__name__}: {e}).")
            out["note"] = out["note"] or f"Rating nicht gespeichert: {e}"
            return None

    if _ai_player is not None:
        # Mensch gegen KI: nur die menschliche Seite kann ein Profil haben,
        # die KI ist der fixe Anker (wird selbst nie aktualisiert).
        human_pi = 1 - _ai_player
        human_profile_id = _profile_p0 if human_pi == 0 else _profile_p1
        if human_profile_id is None:
            out["note"] = "Kein Profil ausgewählt - Spiel ungewertet."
            return out
        ai_identity = _ai_model or "Heuristik"
        ai_elo, ai_is_estimate, ai_node = _pp.estimate_ai_anchor(ai_identity, _ai_sims)
        # Elo-Betrugsschutz (Nutzer 2026-08-06): GEWERTET wird nur gegen
        # Konfigurationen mit DIREKTER Arena-Kante (is_estimate=False).
        # Vorher wertete auch der Sims-Tier-SCHAETZWERT -- damit liess sich
        # Elo farmen (z.B. Champion@60 schlagen, Anker aber nahe der
        # @400-Staerke geschaetzt). Historien-Eintrag wird trotzdem
        # geschrieben (rated:false, Transparenz wie beim Tipp-Fall).
        if rated and ai_is_estimate:
            out["note"] = (f"{ai_identity}@{_ai_sims} hat keinen direkten Arena-Anker "
                           f"(nur Schätzwert) - Spiel ungewertet. Gewertete Spiele nur "
                           f"gegen verankerte Konfigurationen (z.B. @400).")
            rated = False
        if ai_elo is None and rated:
            # Kein Anker bekannt: nur bei GEWERTETEN Spielen ein Problem
            # (ohne Anker keine Elo-Rechnung moeglich) -- bei ungewerteten
            # Spielen (Tipps genutzt) wird trotzdem ein Historien-Eintrag
            # geschrieben, auch ohne bekannten Gegner-Wert (opponent_rating=None).
            out["note"] = f"Kein Elo-Anker für {ai_identity}@{_ai_sims} bekannt - Spiel ungewertet."
            return out
        result = result_p0 if human_pi == 0 else result_p1
        entry = _record(human_profile_id, ai_node or f"{ai_identity}@{_ai_sims}",
                         ai_elo, ai_is_estimate, result)
        out[str(human_pi)] = entry
        return out

    # Mensch gegen Mensch: nur werten, wenn BEIDE Seiten ein (unterschiedliches)
    # Profil ausgewählt haben — ohne Gegner-Rating gibt es keinen Anker für
    # eine Elo-Aktualisierung (Design-Vorgabe #3). Bei genutzten Tipps
    # (rated=False) gilt dieselbe Grundvoraussetzung: ohne Gegner-Profil kein
    # sinnvoller Historien-Eintrag.
    if not _profile_p0 or not _profile_p1:
        out["note"] = "Werten nur, wenn beide Spieler ein Profil ausgewählt haben."
        return out
    if _profile_p0 == _profile_p1:
        out["note"] = "Beide Seiten haben dasselbe Profil ausgewählt - ungewertet."
        return out
    p0 = _pp.get_profile(_profile_p0)
    p1 = _pp.get_profile(_profile_p1)
    if p0 is None or p1 is None:
        out["note"] = "Profil nicht gefunden - ungewertet."
        return out
    # Beide Ratings VOR dem Update einfrieren (symmetrisches Matchup) --
    # Standard-Elo-Konvention für gegenseitige Updates, sonst würde die
    # Reihenfolge der Aufrufe das Ergebnis leicht verzerren (nur relevant,
    # wenn rated=True -- bei record_unrated aendert sich ohnehin nichts).
    rating_p0_before = p0["rating"]
    rating_p1_before = p1["rating"]
    out["0"] = _record(_profile_p0, p1["name"], rating_p1_before, False, result_p0)
    out["1"] = _record(_profile_p1, p0["name"], rating_p0_before, False, result_p1)
    return out


@app.route('/api/end_scoring', methods=['POST'])
def end_scoring():
    global _game_rated
    if (e := _require_game()) is not None:
        return e
    if _rust.phase() != "end":
        return jsonify(err("Spiel noch nicht beendet"))
    # Die eigentliche Punktewertung (apply_end_scoring in der Engine) ist
    # STATEFUL und darf nicht an einem spaeteren Profil-/Rating-Fehler
    # scheitern -- eigener try/except NUR dafuer.
    try:
        results = _json.loads(_rust.end_scoring_json())
        _flush_game_log()
    except Exception as e:
        return jsonify(err(str(e)))

    state = _rust_state()
    response = {"ok": True, "state": state, **results}

    # Spielerprofile/Elo: darf die Endwertung NIEMALS zum Scheitern bringen
    # (Vorfall 2026-08-02: eine Profil-Ausnahme hier hat vorher die GESAMTE
    # /api/end_scoring-Antwort als Fehler zurueckgegeben, obwohl die
    # eigentliche Punktewertung oben laengst erfolgreich und bereits
    # state-veraendernd durchgelaufen war -- der Spieler bekam einen Fehler
    # UND keine Endwertung angezeigt, obwohl das Spiel serverseitig fertig
    # war. Deshalb: eigener, komplett isolierter try/except NUR um die
    # Rating-Logik, mit Server-Log-Zeile bei Fehlern; Elo-Wertung GENAU
    # EINMAL pro Partie (Idempotenz-Schutz per `_game_rated`, falls der
    # Client /api/end_scoring mehrfach aufruft, z.B. nach einem Reload).
    if not _game_rated:
        try:
            response["rating_updates"] = _apply_elo_for_finished_game(state)
        except Exception as e:
            print(f"WARNUNG: Elo-Wertung fuer beendete Partie fehlgeschlagen "
                  f"({type(e).__name__}: {e}) -- Endwertung wird trotzdem normal "
                  f"ausgeliefert, Rating-Teil wird uebersprungen.")
            response["rating_updates"] = {
                "0": None, "1": None,
                "note": "Rating nicht gespeichert: Profil nicht gefunden.",
            }
        _game_rated = True

    return jsonify(response)


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
                # Task #97: Lehrer-Kernzahlen als Kommentarzeile (Format-
                # kompatibel -- tools/analyze_game_log.py::load_log()
                # überspringt JEDE Zeile, die mit "#" beginnt und nicht mit
                # "# {" (Header) startet oder auf SPIELENDE_RE matcht, siehe
                # dortige `elif raw_line.startswith("#"): ... continue`).
                if _teacher_level == 3 and _teacher_history:
                    n = len(_teacher_history)
                    avg = sum(h["delta_win_pp"] for h in _teacher_history) / n
                    top1 = sum(1 for h in _teacher_history if h["rang"] == 1)
                    top3 = sum(1 for h in _teacher_history if h["rang"] <= 3)
                    summary = {
                        "count": n, "avg_delta_win_pp": round(avg, 1),
                        "top1_rate": round(top1 / n, 3), "top3_rate": round(top3 / n, 3),
                    }
                    lf.write(f"# TEACHER_SUMMARY: {_json.dumps(summary, ensure_ascii=False)}\n")
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


# ── Task #28 (PREREG_task28_aggression.md): Aggressivitäts-Regler ───────────
# Setzt/liest die beiden Laufzeit-Parameter des Score-/Denial-Utility-Blends
# in der Rust-Engine (`net_mcts::set_aggression_params`/`get_aggression_
# params`, ATOMAR, wirkt SOFORT auf die naechste KI-Suche — kein
# Server-Neustart noetig). Engine-weiter Zustand, NICHT an eine laufende
# Partie gebunden (funktioniert unabhaengig von `_rust`/`PyGame`, direkt
# ueber das `mosaic_rust`-Modul). KEIN Persistieren ueber einen Server-
# Neustart hinweg — danach gelten wieder die `MOSAIC_POINTS_UTILITY_W`/
# `MOSAIC_AGGR_LAMBDA`-Env-Var-Defaults (siehe net_mcts.rs-Doku); ein
# `models/champion.txt`-Analogon fuer den Regler ist bewusst nicht vorgesehen
# (Nutzer-Wunsch: "kein Persistieren noetig").
#
# Die Rust-Bindungen existieren erst NACH dem naechsten Wheel-Build/-Install
# (dieser Server-Code wurde parallel zum Engine-Umbau geschrieben) — beide
# Endpunkte pruefen defensiv per `hasattr`, ob `mosaic_rust` die neuen
# Funktionen schon mitbringt, und antworten sonst mit 503 statt den Server
# mit einem AttributeError abstuerzen zu lassen (Server muss mit einem NOCH
# ALTEN Wheel weiterlaufen).
_AGGRESSION_UNAVAILABLE_MSG = (
    "Aggressivitäts-Regler nicht verfügbar - Wheel-Update nötig "
    "(installiertes mosaic_rust-Wheel kennt set_aggression_params/"
    "get_aggression_params noch nicht, Server-Neustart nach dem Update nötig)."
)


@app.route('/api/aggression', methods=['GET'])
def get_aggression():
    """Aktueller Stand des Reglers (w, lambda_aggr) — Frontend nutzt das, um
    den Slider beim Laden auf den tatsächlichen Serverzustand zu setzen."""
    if _mr is None or not hasattr(_mr, 'get_aggression_params'):
        return jsonify(err(_AGGRESSION_UNAVAILABLE_MSG)), 503
    w, lambda_aggr = _mr.get_aggression_params()
    return jsonify({"ok": True, "w": w, "lambda_aggr": lambda_aggr})


@app.route('/api/aggression', methods=['POST'])
def set_aggression():
    """Setzt den Regler. Body: {"w": float, "lambda_aggr": float} — beide
    optional (Default 0.0 = aus). Wertebereiche werden zusätzlich in der
    Rust-Engine geklemmt (w in [0,1], lambda_aggr in [0,5], siehe
    `net_mcts::set_aggression_params`-Doku); hier nur Typ-/Endlichkeits-
    Prüfung, damit ein kaputter Request eine klare Fehlermeldung statt eines
    500ers liefert."""
    if _mr is None or not hasattr(_mr, 'set_aggression_params'):
        return jsonify(err(_AGGRESSION_UNAVAILABLE_MSG)), 503
    d = request.get_json(silent=True) or {}
    try:
        w = float(d.get('w', 0.0))
        lambda_aggr = float(d.get('lambda_aggr', 0.0))
    except (TypeError, ValueError):
        return jsonify(err("w/lambda_aggr müssen Zahlen sein."))
    if not _math.isfinite(w) or not _math.isfinite(lambda_aggr):
        return jsonify(err("w/lambda_aggr müssen endliche Zahlen sein."))
    _mr.set_aggression_params(w, lambda_aggr)
    actual_w, actual_lambda_aggr = _mr.get_aggression_params()
    return jsonify({"ok": True, "w": actual_w, "lambda_aggr": actual_lambda_aggr})


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


# ── Anzeige-Kalibrierung der Gewinnwahrscheinlichkeit (Weg A, Nutzer 2026-08-09)
# Auftrag: "ehrlichere Gewinnwahrscheinlichkeit" im Spiel. Der Value-Kopf ist
# leicht UEBERKONFIDENT -- gemessener Platt-Fit des amtierenden Champions
# `v21_2d_brierbest` auf dem eingefrorenen Eval-Set (1440 Records, Runden 1-4,
# tools/platt_fit.py -> evaluations/platt_fit_v21.json): B=0,9060, A=-0,0033.
# B<1 heisst: die Ausschlaege sind zu gross. Die Korrektur
#     p_anzeige = sigmoid(A + B * logit(p_roh))
# schrumpft sie auf das gemessene Mass zurueck.
#
# BEWUSST NUR IM ANZEIGEPFAD, NICHT IN DER SUCHE: die Engine hat fuer den
# Suchpfad eigene Knoepfe (MOSAIC_VALUE_CAL_A/B, Task #30) -- die bleiben
# INERT (A=0/B=1), weil Task #30 fuer die Suchseite H0 gemessen hat und eine
# Aenderung dort die Blattwerte und damit die Spielstaerke verschieben wuerde.
# Hier wird ausschliesslich die ANGEZEIGTE Zahl korrigiert; das Rohsignal
# bleibt als `win_prob_raw` erhalten, damit nichts verloren geht.
#
# WICHTIG: A/B sind MODELLSPEZIFISCH. Bei jedem Champion-Wechsel neu messen
# (`python tools/platt_fit.py --models models/alphazero_<neu>.pth`) und hier
# eintragen -- steht als Punkt in der Promotions-Checkliste (STATUS.md).
# Abschalten: MOSAIC_DISPLAY_CAL=0. Ueberschreiben: MOSAIC_DISPLAY_CAL_A/_B.
_DISPLAY_CAL_A = float(os.environ.get("MOSAIC_DISPLAY_CAL_A", "-0.0033"))
_DISPLAY_CAL_B = float(os.environ.get("MOSAIC_DISPLAY_CAL_B", "0.9060"))
_DISPLAY_CAL_ON = os.environ.get("MOSAIC_DISPLAY_CAL", "1") != "0"


def _calibrate_display_win_prob(analysis):
    """Ersetzt `value_debug.win_prob` durch die kalibrierte Wahrscheinlichkeit
    und legt das Rohsignal unter `win_prob_raw` ab. Reine Anzeige-Transformation
    (idempotent-sicher: wenn `win_prob_raw` schon existiert, wird nichts
    nochmals transformiert). Fehlt das Feld oder ist die Kalibrierung aus,
    bleibt `analysis` unveraendert."""
    if not _DISPLAY_CAL_ON or not isinstance(analysis, dict):
        return analysis
    vd = analysis.get("value_debug")
    if not isinstance(vd, dict) or vd.get("win_prob") is None or "win_prob_raw" in vd:
        return analysis
    try:
        p = float(vd["win_prob"])
    except (TypeError, ValueError):
        return analysis
    eps = 1e-6
    p = min(max(p, eps), 1.0 - eps)
    z = _math.log(p / (1.0 - p))
    p_cal = 1.0 / (1.0 + _math.exp(-(_DISPLAY_CAL_A + _DISPLAY_CAL_B * z)))
    vd["win_prob_raw"] = float(vd["win_prob"])
    vd["win_prob"] = p_cal
    vd["win_prob_calibrated"] = True
    vd["win_prob_cal_ab"] = [_DISPLAY_CAL_A, _DISPLAY_CAL_B]
    return analysis


@app.route('/api/ai/debug', methods=['GET'])
def ai_debug():
    """Analyse der AKTUELLEN Stellung (ohne Zug auszuführen), aus der Rust-KI."""
    if (e := _require_game()) is not None:
        return e
    if _ai_model is not None:
        analysis = _calibrate_display_win_prob(
            _json.loads(_rust.ai_debug_net_json(_ai_sims, _ai_c_puct)))
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


# ── Lehrer-Modus (Task #97) ──────────────────────────────────────────────────

@app.route('/api/teacher/config', methods=['GET'])
def teacher_config():
    return jsonify({
        "ok": True,
        "level": _teacher_level,
        "sims": _teacher_sims,
        "coach_sims": _teacher_coach_sims,
    })


@app.route('/api/teacher/config', methods=['POST'])
def teacher_config_set():
    """Setzt Lehrer-Stufe/Sims während des Spiels (analog /api/ai/config)."""
    global _teacher_level, _teacher_sims, _teacher_coach_sims, _teacher_cache
    d = request.get_json(silent=True) or {}
    if 'level' in d:
        try:
            lvl = int(d['level'])
        except (TypeError, ValueError):
            return jsonify(err("teacher_level muss 0-3 sein."))
        if lvl not in (0, 1, 2, 3):
            return jsonify(err("teacher_level muss 0-3 sein."))
        _teacher_level = lvl
    if 'sims' in d:
        _teacher_sims = int(d['sims'])
    if 'coach_sims' in d:
        _teacher_coach_sims = int(d['coach_sims'])
    _teacher_cache = {"key": None, "analysis": None}  # Stufenwechsel -> alte Analyse verwerfen
    return jsonify({"ok": True, "level": _teacher_level, "sims": _teacher_sims, "coach_sims": _teacher_coach_sims})


@app.route('/api/ai/hint', methods=['GET'])
def ai_hint():
    """Lehrer-Tipp (Stufe 1/2/3): Top-3-Kandidaten (Nutzer-Feedback, vorher
    Top-5) der Analyse des AKTUELLEN (menschlichen) Zustands -- nur gültig,
    wenn der Mensch am Zug UND in der Drafting-Phase ist. Nutzt das geladene
    Netz des KI-Gegners (`ai_debug_net_json`); ist keines geladen (Heuristik-
    Gegner), fällt die Analyse pragmatisch auf die Heuristik zurück (`note`-
    Feld im Response weist darauf hin) -- siehe `_teacher_compute_analysis`-
    Doku."""
    global _hints_used_this_game
    if (e := _require_game()) is not None:
        return e
    if _teacher_level == 0:
        return jsonify(err("Lehrer-Modus ist aus."))
    if _ai_player is None:
        return jsonify(err("Tipps gibt es nur im Spiel gegen die KI."))
    if _rust.current_player() == _ai_player:
        return jsonify(err("Nicht dein Zug."))
    if _rust.phase() != "drafting":
        return jsonify(err("Tipps gibt es nur in der Drafting-Phase."))
    # Spielerprofile: Tipp-Nutzung wird im Elo-Historien-Eintrag vermerkt
    # (Feld hints_used, siehe player_profiles.py::apply_result) -- das Spiel
    # zaehlt trotzdem ganz normal (Design-Vorgabe #4: werten, nur vermerken).
    _hints_used_this_game = True
    analysis = _teacher_cached_or_fresh_analysis(_teacher_sims)
    moves = analysis.get("moves") if isinstance(analysis, dict) else None
    if not moves:
        return jsonify(err("Analyse derzeit nicht verfügbar."))

    ranked = sorted(moves, key=lambda m: -(m.get("mcts_q") or 0.0))
    top_n = ranked[:TEACHER_HINT_TOP_N]
    top_win_pct = top_n[0].get("mcts_win_pct") or 0.0
    candidates = []
    for i, mv in enumerate(top_n):
        typ = mv.get("type")
        params = _teacher_action_params(typ, mv.get("description", ""))
        br = mv.get("best_rotation")
        if params is not None and isinstance(br, dict) and br.get("rotation") is not None:
            params["rotation"] = int(br["rotation"])
        cand = {
            "rank":        i + 1,
            "description": _teacher_describe_move(mv),
            "type":        typ,
            "action":      params,
        }
        if _teacher_level >= 2:
            wp = mv.get("mcts_win_pct")
            cand["win_pct"]      = round(wp, 1) if wp is not None else None
            cand["delta_win_pp"] = round(top_win_pct - wp, 1) if wp is not None else None
        candidates.append(cand)

    note = None
    if _ai_model is None:
        note = ("Lehrer-Analyse basiert auf der Heuristik-KI (kein Netz-Gegner geladen) -- "
                "Gewinnschätzungen sind gröber als mit einem geladenen Netz.")
    return jsonify({"ok": True, "level": _teacher_level, "candidates": candidates, "note": note})


@app.route('/api/teacher/summary', methods=['GET'])
def teacher_summary():
    """Endbilanz des Coach-Modus (Stufe 3) der laufenden/letzten Partie."""
    hist = _teacher_history
    n = len(hist)
    if n == 0:
        return jsonify({
            "ok": True, "count": 0, "avg_delta_win_pp": None,
            "top1_rate": None, "top3_rate": None, "worst": [],
        })
    avg = sum(h["delta_win_pp"] for h in hist) / n
    top1 = sum(1 for h in hist if h["rang"] == 1)
    top3 = sum(1 for h in hist if h["rang"] <= 3)
    worst = sorted(hist, key=lambda h: -h["delta_win_pp"])[:3]
    return jsonify({
        "ok": True,
        "count": n,
        "avg_delta_win_pp": round(avg, 1),
        "top1_rate": round(top1 / n, 3),
        "top3_rate": round(top3 / n, 3),
        "worst": [{
            "round": h["round"], "kind": h["kind"], "rang": h["rang"],
            "delta_win_pp": h["delta_win_pp"], "top_desc": h["top_desc"],
        } for h in worst],
    })


if __name__ == '__main__':
    print("Mosaic-AI Server läuft auf http://localhost:5000")
    app.run(debug=True, port=5000)
