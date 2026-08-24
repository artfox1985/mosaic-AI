"""
tools/analyze_game_log.py -- wiederverwendbares Werkzeug zur Analyse von
Mensch-vs-KI-Partie-Logs (static/log/game_*.log).

Pipeline (Auftrag "Spiel-Analyse-Werkzeug", 2026-07-25):
  1. Parser:  Log-Datei -> geordnete Liste struktureller Aktionen (Drafting,
      Startkacheln, Tiling, Wertungsplatten-Wahl, Endwertung). Log-Formate
      wurden NICHT geraten, sondern direkt aus den log_event(...)-Aufrufen in
      engine/src/{execution,game,round_end,state,py}.rs abgelesen.
  2. Replay:  mosaic_rust.PyGame + die passenden apply_*-Methoden, Zug für
      Zug. Seit PREREG_action_id_logging.md (2026-08-18) wird ein Stein-Zug
      NICHT mehr aus der Prosa erraten, sondern ueber die AKTIONS-ID
      aufgeloest, die die Engine je Zug mitschreibt:

          #a {"id": 137, "p": 0, "a": {"type": "stone", ...}}

      Das ist dieselbe ID, gegen die der Policy-Kopf trainiert
      (`features.rs::action_to_id`, `NUM_ACTIONS = 406`); sie steht seither
      auch an jedem `valid_moves`-Eintrag. Die Zeile geht NUR in die
      gespeicherte Fassung, nicht in die Anzeige (serialize.rs filtert sie).
      Logs ohne solche Zeilen (alles vor dem 2026-08-18, Arena-Logs, und der
      KI-Stapelzug) laufen unveraendert ueber den alten Textweg.
      Kreuzvalidierung: nach JEDER Aktion wird `g.log_since(checkpoint)`
      (== dieselben log_event-Strings wie im Original-Log, inkl. "[Rn] "-
      Präfix, siehe GameState::log_event) exakt gegen den entsprechenden
      Original-Log-Abschnitt verglichen. Divergenz -> sofortiger Abbruch mit
      genauer Stelle (nicht weiterraten).
  3. Oracle:  an jedem Drafting-Entscheidungspunkt BEIDER Spieler (vor der
      Aktion, sofern Runde < 5 -- Runde 5 läuft über den exakten Alpha-Beta-
      Solver, siehe round5.rs, und wird bewusst NICHT netz-oracle-bewertet)
      ein `mosaic_rust.net_search_state_json`-Aufruf (v16_best, 5000 Sims,
      deterministischer Seed je Zugindex) -- Rang/Δwin% der gespielten Aktion
      im Vergleich zum Oracle-Top-Zug.
  4. Report:  Markdown nach evaluations/game_analysis/game_analysis_<...>.md.

Bekannte, bewusste Einschränkung (Task #89): PendingDomeChoice-Zwischen-
zustände (Kuppel-Rotation NACH Kachel+Slot-Wahl) haben Serialisierungs-
Näherungen -- Kuppelzüge werden daher NUR am Vor-Zustand (Kachel+Slot-Wahl,
Stufe 1) oracle-bewertet, nie an der Rotations-Zwischenstufe. `apply_dome`/
`apply_dome_stack_choose` bleiben nach aussen atomar (Slot+Rotation in einem
Python-Aufruf), daher gibt es hier ohnehin keine echte Zwischen-Entscheidung
auf Python-Seite.

Laufzeit: ~60-90 Drafting-Entscheidungspunkte x ~3-6s (5000 Sims) ~= 5-10 Min.
Mit --no-oracle laeuft nur Parser+Replay (Sekunden) -- nuetzlich zum Testen
und fuer jede zukuenftige Partie, bei der nur die Replay-Korrektheit
interessiert.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import itertools
import json
import re
import sys
import time
import dataclasses
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import mosaic_rust  # noqa: E402

DEFAULT_MODEL = ROOT / "models" / "alphazero_v16_best.onnx"
DEFAULT_SIMS = 5000
DEFAULT_C_PUCT = 1.5


def check_prereqs() -> None:
    """Auftrag: NICHT selbst neu bauen, wenn net_search_state_json im
    installierten Wheel fehlt -- das würde auf einen aelteren Rebuild-Stand
    hindeuten (siehe Vorfall-Notiz zum Rebuild davor)."""
    missing = [name for name in ("PyGame", "net_search_state_json") if not hasattr(mosaic_rust, name)]
    if missing:
        print(
            "ABBRUCH: mosaic_rust fehlt " + ", ".join(missing) + " -- das installierte Wheel "
            "scheint einen aelteren Stand zu haben. Bitte pruefen/neu installieren; dieses "
            "Werkzeug baut NICHT selbst neu.",
            file=sys.stderr,
        )
        sys.exit(1)


class ReplayDivergence(RuntimeError):
    pass


# ═══════════════════════════════════════════════════════════════════════════
# Log-Klassifikation -- Regexe 1:1 aus den log_event(...)-Formatstrings der
# Engine (siehe Modul-Docstring fuer die Fundstellen: execution.rs, game.rs,
# round_end.rs, state.rs, py.rs).
# ═══════════════════════════════════════════════════════════════════════════

PATTERNS: dict[str, re.Pattern] = {
    "GAME_START": re.compile(r"^Spiel gestartet\. (?P<starter>.+?) beginnt\.$"),
    "SCORING_CHOICE": re.compile(r"^Wertungsplatten gewählt: (?P<ids>\[.*\])$"),
    "START_TILE": re.compile(
        r"^(?P<name>.+?): Startkachel (?P<tile>\d+) → \((?P<row>\d+),(?P<col>\d+)\) rot=(?P<rot>\d+)°$"
    ),
    # Das Emoji ist seit der Korrektur vom 2026-08-18 (execution.rs:59) KEIN
    # Formatmerkmal mehr, sondern folgt der QUELLE: eine Teil-Entnahme aus dem
    # Mondbereich (SmallFactoryMoon/LargeFactoryMoon mit factory_id) traegt
    # 🌙 im SCHLICHTEN Format, ohne die (detail)-Klammer der globalen
    # Mond-Entnahme. Deshalb hier beide Emoji zulassen -- der Aktionstyp wird
    # ohnehin nicht mehr daraus abgeleitet (siehe resolve_stone).
    # Alte Logs behalten ihr ☀️ und bleiben unveraendert parsebar.
    "SUN_TAKE": re.compile(
        r"^(?P<emoji>☀️|🌙)\s*(?P<name>.+?): (?P<n>\d+)× (?P<color>\S+) von (?P<src>F\d+|GF) → "
        r"(?P<dest>Reihe \d+|Strafleiste)(?: \[(?P<fill>\d+)/(?P<cap>\d+)\])?"
        r"(?: \(\+(?P<overflow>\d+) Strafleiste\))?$"
    ),
    "MOON_GLOBAL_TAKE": re.compile(
        r"^🌙 (?P<name>.+?): (?P<n>\d+) \((?P<detail>[\d+]+)\)× (?P<color>\S+) von "
        r"(?P<srcs>.+?) → (?P<dest>Reihe \d+|Strafleiste)(?: \[(?P<fill>\d+)/(?P<cap>\d+)\])?"
        r"(?: \(\+(?P<overflow>\d+) Strafleiste\))?$"
    ),
    "CHIP_TAKE": re.compile(
        r"^(?P<name>.+?): Bonusplättchen von Fabrik (?P<fid>\d+) genommen \[(?P<used>\d+)/2 diese Runde\]$"
    ),
    "STACK_PEEK": re.compile(r"^📦 (?P<name>.+?): (?P<n>\d+)\. Kachel vom Stapel gezogen"),
    "DOME_PLACE": re.compile(
        r"^(?P<name>.+?): Kachel (?P<tile>\d+) → Slot \((?P<r>\d+),(?P<c>\d+)\) rot=(?P<rot>\d+)° "
        r"\[Plättchen (?P<tok>\d+)/2\]$"
    ),
    "TILING_PLACE": re.compile(
        r"^(?P<name>.+?): (?P<color>\S+) → Slot \((?P<r>\d+),(?P<c>\d+)\) Space (?P<si>\d+)"
        r"(?P<special> \[Special freigeschaltet!\])?$"
    ),
    "TILING_SCORE": re.compile(
        r"^🎯 (?P<name>.+?): \+(?P<pts>\d+) Pkt \(Reihe (?P<row>\d+) → Kuppel (?P<sr>\d+)/(?P<sc>\d+) - (?P<expl>.+)\)$"
    ),
    "CHIPS_COMPLETE": re.compile(r"^🎫 (?P<name>.+?) komplettiert Reihe (?P<row>\d+)"),
    "ROUND_START": re.compile(r"^Runde (?P<rn>\d+) beginnt\. (?P<starter>.+?) ist Startspieler\.$"),
    "GAME_OVER": re.compile(r"^Das Spiel ist beendet!$"),
    "ROUND_STRAFE": re.compile(r"^(?P<name>.+?): Strafe (?P<pen>-?\d+) Pkt → (?P<score>-?\d+) Gesamt$"),
    "UNPLACEABLE": re.compile(r"^⚠️\s*(?P<name>.+?): Musterreihe"),
    # Watchlist-Fund 2026-08-07: Endwertung kann NEGATIV sein (leere
    # Spezialfelder bei aktiver Platte 7) -- Vorzeichen zulassen.
    "FINAL_SCORE": re.compile(r"^🏆 (?P<name>.+?): Endwertung (?P<total>-?\d+) Pkt → Gesamt: (?P<score>\d+) Pkt$"),
    # Rein informativ (werden nie als naechste primaere Zeile erwartet,
    # sondern immer als Anhang eines vorausgehenden consume_block verbraucht):
    # GUI-Symbol seit 2026-08-06: ❖ statt 🏁 (beide akzeptieren --
    # Alt-Logs bleiben parsebar; Watchlist-Fund 2026-08-07).
    "MARKER": re.compile(r"^[🏁❖]\s*(?P<name>.+?): Startspielerstein genommen"),
    # Arena-Log-Fund 2026-08-11: Quelle engine/src/game.rs::execute_draw_
    # from_stack (~Zeile 284) -- Spieler zieht >=2 Kuppelplatten, legt >=1
    # zurueck. 0 Treffer in den 64 Nutzer-Logs (latent), aber jede Arena-
    # Partie (net_arena_match(log_games=True)) kann sie erzeugen. Geht der
    # DOME_PLACE-Zeile immer unmittelbar voraus (ein log_event-Aufruf) --
    # wie MARKER per SECONDARY_LINE_CATEGORIES uebersprungen.
    "DOME_RETURN_TO_STACK": re.compile(
        r"^↩️\s*(?P<n>\d+) Kuppelplatte\(n\) zurueck unter den Stapel \(Reihenfolge\): (?P<liste>.+)$"
    ),
    "MOON_STACK_INFO": re.compile(r"^🌙 F(?P<fid>\d+) Mond-Stapel(?: nach Entnahme)?: (?P<desc>.+)$"),
    "MOON_POOL_INFO": re.compile(r"^🌙 GF Moon-Pool: (?P<desc>.+)$"),
    "CHIP_REVEAL": re.compile(r"^🎴 F(?P<fid>\d+): Bonusplättchen aufgedeckt!$"),
    "TILING_START": re.compile(r"^Tiling-Phase beginnt\.$"),
    "OVERFLOW_PENALTY": re.compile(r"^⚠️\s*(?P<name>.+?): \d+× auf Strafleiste"),
    "TOWER_OVERFLOW": re.compile(r"^⚠️\s*(?P<name>.+?): \d+ Stein\(e\) → Turm"),
    "SPECIAL_BONUS": re.compile(r"^⭐ (?P<name>.+?): \+(?P<bonus>\d+) Spezial-Punkte"),
    "FINAL_DETAIL": re.compile(r"^\s+\S+ (?P<name2>.+?): (?P<score>\d+) Pkt$"),
}

# Primaere Aktionszeilen: loesen einen (oder mehrere) apply_*-Aufrufe aus.
PRIMARY_CATEGORIES = {
    "GAME_START", "SCORING_CHOICE", "START_TILE", "SUN_TAKE", "MOON_GLOBAL_TAKE",
    "CHIP_TAKE", "STACK_PEEK", "DOME_PLACE", "TILING_PLACE", "CHIPS_COMPLETE",
    "ROUND_START", "GAME_OVER", "ROUND_STRAFE", "UNPLACEABLE", "FINAL_SCORE",
}

ROUND_PREFIX = re.compile(r"^\[R(\d+)\] (.*)$")

# Zeilen, die einer primaeren Aktionszeile IMMER unmittelbar vorausgehen (Teil
# desselben log_event-Aufrufblocks) und daher fuer die Dispatch-Klassifikation
# uebersprungen werden -- die Textvalidierung (siehe apply()/_call_and_check)
# bekommt sie trotzdem zu sehen, da `li` (Blockanfang) unveraendert bleibt.
SECONDARY_LINE_CATEGORIES = {"MARKER", "DOME_RETURN_TO_STACK"}


def classify(text: str):
    for cat, pat in PATTERNS.items():
        m = pat.match(text)
        if m:
            return cat, m
    return None, None


@dataclass
class LogLine:
    round_num: int
    raw: str   # kompletter Original-Text INKLUSIVE "[Rn] "-Praefix
    body: str  # ohne Praefix (fuer die Klassifikation)


# Maschinenlesbare Aktionszeile (PREREG_action_id_logging.md S2), geschrieben
# von py.rs::push_action_id_line. Traegt die Aktions-ID aus DEMSELBEN Raum,
# gegen den der Policy-Kopf trainiert (features::action_to_id), plus die
# kanonischen Felder als Rueckfallebene.
ACTION_HINT_RE = re.compile(r"^#a (\{.*\})$")

SPIELENDE_RE = re.compile(r"^# SPIELENDE: (\[.*\])$")


def load_log(path: Path):
    """Gibt (header_meta, lines, hints) zurueck.

    `hints[i]` = Liste der `#a`-Nutzlasten, die im Original UNMITTELBAR VOR
    Textzeile `i` stehen. Die Engine schreibt sie VOR dem Anwenden, sie
    gehoeren also zu der Aktion, die die folgenden Textzeilen erzeugt hat.
    Fehlen sie (alte Logs, Arena-Logs, KI-Stapelzug -- siehe py.rs), bleibt
    der Eintrag leer und der Replay faellt auf den Textweg zurueck."""
    header_meta = None
    lines: list[LogLine] = []
    hints: dict[int, list[dict]] = {}
    spielende_scores = None
    with open(path, encoding="utf-8") as fh:
        for raw_line in fh:
            raw_line = raw_line.rstrip("\n").rstrip("\r")
            if raw_line.startswith("# {"):
                header_meta = json.loads(raw_line[2:])
                continue
            if raw_line.startswith("#"):
                mh = ACTION_HINT_RE.match(raw_line)
                if mh:
                    try:
                        hints.setdefault(len(lines), []).append(json.loads(mh.group(1)))
                    except json.JSONDecodeError:
                        pass  # defekte Zeile ignorieren, der Textweg traegt weiter
                    continue
                m2 = SPIELENDE_RE.match(raw_line)
                if m2:
                    spielende_scores = ast.literal_eval(m2.group(1))
                continue
            m = ROUND_PREFIX.match(raw_line)
            if not m:
                continue
            lines.append(LogLine(int(m.group(1)), raw_line, m.group(2)))
    if header_meta is None:
        raise ReplayDivergence("Header-JSON-Zeile (# {...}) nicht gefunden.")
    header_meta["_spielende_scores"] = spielende_scores
    return header_meta, lines, hints


# ═══════════════════════════════════════════════════════════════════════════
# Oracle
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class OracleRecord:
    turn_idx: int
    round_num: int
    actor: int
    actor_name: str
    kind: str
    played_desc: str
    evaluated: bool = False
    reason: str = ""
    num_actions: int = 0
    root_value: float | None = None  # Win% des Spielers am Zug (0..1), Oracle-Schaetzung VOR dem Zug
    played_rank: int | None = None
    played_q: float | None = None
    top_q: float | None = None
    top_desc: str | None = None
    delta_win_pct: float | None = None
    ambiguous_match: bool = False


def deterministic_seed(log_name: str, turn_idx: int) -> int:
    h = hashlib.sha256(f"{log_name}:{turn_idx}".encode()).digest()
    return int.from_bytes(h[:8], "big") & 0x7FFFFFFFFFFFFFFF


STONE_DESC_RE = re.compile(
    r"Stein (?P<color>\S+) (?:von|vom) (?P<src>F\d+|GF|Mondpool) → (?P<dest>Reihe \d+|Strafleiste)"
)
DOME_DISPLAY_DESC_RE = re.compile(r"Kuppel #(?P<tile>\d+) → \((?P<r>\d+),(?P<c>\d+)\)")
DOME_STACK_DESC_RE = re.compile(r"Stapel → \((?P<r>\d+),(?P<c>\d+)\)")
BONUS_DESC_RE = re.compile(r"Bonuschip F(?P<fid>\d+)")


def played_key(kind: str, fields: dict):
    if kind == "stone":
        return ("stone", fields["color"], fields["src"], fields["dest"])
    if kind == "dome_display":
        return ("dome_display", str(fields["tile"]), str(fields["r"]), str(fields["c"]))
    if kind == "dome_stack":
        return ("dome_stack", str(fields["r"]), str(fields["c"]))
    if kind == "dome_stack_peek":
        return ("dome_stack_peek",)
    if kind == "bonus_chip":
        return ("bonus_chip", str(fields["fid"]))
    raise ValueError(kind)


def move_key(mv: dict):
    typ = mv.get("type")
    desc = mv.get("description", "")
    if typ == "stone":
        m = STONE_DESC_RE.search(desc)
        return ("stone", m.group("color"), m.group("src"), m.group("dest")) if m else None
    if typ == "choose_dome_slot":
        m = DOME_DISPLAY_DESC_RE.search(desc)
        return ("dome_display", m.group("tile"), m.group("r"), m.group("c")) if m else None
    if typ == "choose_draw_stack_slot":
        m = DOME_STACK_DESC_RE.search(desc)
        return ("dome_stack", m.group("r"), m.group("c")) if m else None
    if typ == "dome_stack_peek":
        return ("dome_stack_peek",)
    if typ == "bonus_chip":
        m = BONUS_DESC_RE.search(desc)
        return ("bonus_chip", m.group("fid")) if m else None
    return None


def evaluate_oracle(state_json: str, model_path: str, sims: int, c_puct: float, seed: int,
                     kind: str, fields: dict) -> dict:
    raw = mosaic_rust.net_search_state_json(state_json, model_path, sims, c_puct, seed)
    result = json.loads(raw)
    moves = result.get("moves", [])
    out = {"num_actions": result.get("num_actions"), "root_value": result.get("root_value")}
    if not moves:
        out["error"] = "keine moves (root nicht drafting?)"
        return out
    target = played_key(kind, fields)
    matches = [mv for mv in moves if move_key(mv) == target]
    ranked = sorted(moves, key=lambda mv: -mv.get("mcts_q", 0.0))
    out["top_q"] = ranked[0].get("mcts_q")
    out["top_desc"] = ranked[0].get("description")
    if not matches:
        out["error"] = "gespielte Aktion nicht unter Oracle-Kandidaten identifiziert"
        return out
    out["ambiguous_match"] = len(matches) > 1
    played_q = max(mv.get("mcts_q", 0.0) for mv in matches)
    out["played_q"] = played_q
    out["played_rank"] = 1 + sum(1 for mv in ranked if mv.get("mcts_q", 0.0) > played_q + 1e-12)
    out["delta_win_pct"] = (ranked[0].get("mcts_q", 0.0) - played_q) * 100.0
    return out


# ═══════════════════════════════════════════════════════════════════════════
# Replay
# ═══════════════════════════════════════════════════════════════════════════

class Replayer:
    """Treibt eine PyGame-Instanz Zug fuer Zug entlang des geparsten Logs.

    `action_log` haelt JEDEN mutierenden Aufruf (inkl. impliziter apply_pass/
    end_tiling-Aufrufe) fest -- das erlaubt, bei mehrdeutigen Kandidaten
    (z.B. moon_order-Permutationen) eine frische Kopie exakt bis zum
    aktuellen Punkt nachzuspielen und dort testweise einen Kandidaten
    anzuwenden, OHNE die echte Instanz zu verunreinigen (kein Undo in Rust
    verfuegbar -- diese Replay-von-vorn-Strategie ist der Ersatz dafuer).
    """

    def __init__(self, header: dict, log_name: str, model_path: str, sims: int, c_puct: float,
                 do_oracle: bool, dump_path: str | None = None):
        # --dump-states: Datei bleibt fuer die Dauer des Replays offen
        self.dump_fh = open(dump_path, "w", encoding="utf-8") if dump_path else None
        self.header = header
        self.players = header["players"]
        self.name_to_idx = {name: i for i, name in enumerate(self.players)}
        self.first_player = header["first_player"]
        self.seed = header["seed"]
        self.log_name = log_name
        self.model_path = model_path
        self.sims = sims
        self.c_puct = c_puct
        self.do_oracle = do_oracle

        # PREREG_action_id_logging.md S3: von `load_log` nachgereicht.
        # `hints[i]` = `#a`-Nutzlasten unmittelbar vor Textzeile i.
        self.hints: dict[int, list[dict]] = {}
        self.emoji_toleriert = 0  # Zeilen, die nur am ☀️/🌙-Praefix abwichen
        self.hint_used = 0      # Zuege, die ueber die ID aufgeloest wurden
        self.hint_missing = 0   # Stein-Zuege ohne Hinweis (Textweg)
        self.action_log: list[tuple[str, tuple, dict]] = []
        self.g = self._fresh_game()
        self.turn_idx = 0
        self.oracle_records: list[OracleRecord] = []
        self.sun_used: dict = {}
        self._reset_sun_used()
        self.round_scores_crosscheck: list[tuple[int, tuple[int, int]]] = []
        self.silent_chip_gaps: list[tuple[int, int, int]] = []  # (round, actor, pattern_row)

    def _reset_sun_used(self):
        self.sun_used = {1: False, 2: False, 3: False, 4: False, "GF": False}

    def _fresh_game(self):
        g = mosaic_rust.PyGame((self.players[0], self.players[1]), self.first_player, self.seed)
        for method, args, kwargs in self.action_log:
            getattr(g, method)(*args, **kwargs)
        return g

    # ── Textvergleich mit EINER benannten, datierten Toleranz ───────────────
    def _lines_equal(self, original: str, replay: str) -> bool:
        """String-Gleichheit -- mit genau einer Ausnahme, und die ist keine
        Aufweichung, sondern eine bekannte Aenderung am Logtext.

        Am 2026-08-18 hat die Emoji-Korrektur (`execution.rs:59`, Commits
        9c92c66/86c1144) das Praefix einer Teil-Entnahme aus dem Mondbereich
        von ☀️ auf 🌙 umgestellt. Alte Logs tragen ☀️, die heutige Engine
        schreibt 🌙 -- der Rest der Zeile ist zeichengleich (nachgemessen an
        `game_20260818_200516_seed585858` Zeile 17). Ohne diese Toleranz ist
        JEDE aeltere Partie mit einer solchen Entnahme dauerhaft unreplaybar,
        obwohl der Zug korrekt aufgeloest wurde.

        Eng gehalten: NUR das Emoji direkt nach dem `[Rn] `-Praefix, und nur
        zwischen diesen beiden Zeichen. Die globale Mond-Entnahme bleibt
        unterscheidbar, weil sie zusaetzlich die `(detail)`-Klammer traegt --
        die Toleranz kann also keine Quellen-Verwechslung durchlassen. Jeder
        Treffer wird gezaehlt und im Report ausgewiesen, nicht verschwiegen."""
        if original == replay:
            return True
        m_o, m_r = ROUND_PREFIX.match(original), ROUND_PREFIX.match(replay)
        if not m_o or not m_r or m_o.group(1) != m_r.group(1):
            return False
        rest_o, rest_r = m_o.group(2), m_r.group(2)
        for a, b in (("☀️ ", "🌙"), ("☀️", "🌙")):
            if rest_o.startswith(a) and rest_r.startswith(b)                     and rest_o[len(a):].lstrip() == rest_r[len(b):].lstrip():
                self.emoji_toleriert += 1
                return True
        return False

    # ── zentrale Anwendung + exakte Textvalidierung ─────────────────────────
    def _call_and_check(self, g, lines: list[LogLine], li: int, method: str, args: tuple, kwargs: dict):
        """Fuehrt den Aufruf auf `g` aus und vergleicht die neu erzeugten
        Log-Zeilen exakt (String-Gleichheit, inkl. "[Rn] "-Praefix) gegen
        `lines[li:]`. Gibt (matched: bool, n, new_lines) zurueck -- die
        Mutation von `g` bleibt in JEDEM Fall bestehen (kein Undo in Rust)."""
        before = g.log_len()
        getattr(g, method)(*args, **kwargs)
        # Die Engine schreibt seit PREREG_action_id_logging.md S2 eigene
        # Maschinenzeilen (`#a {...}`) mit in den Strom. `load_log` haelt sie
        # aus `lines` heraus (sie stehen in `hints`), also muessen sie auch
        # hier raus -- sonst verschiebt sich der Vergleich um genau eine Zeile
        # und JEDER Zug meldet Divergenz.
        new_lines = [l for l in g.log_since(before) if not l.startswith("#a ")]
        n = len(new_lines)
        if li + n > len(lines):
            return False, n, new_lines
        matched = all(self._lines_equal(lines[li + k].raw, new_lines[k]) for k in range(n))
        return matched, n, new_lines

    def apply(self, lines: list[LogLine], li: int, method: str, *args, **kwargs) -> int:
        """Ein EINDEUTIGER Aufruf (kein Kandidaten-Set): anwenden + validieren."""
        matched, n, new_lines = self._call_and_check(self.g, lines, li, method, args, kwargs)
        if not matched:
            expected = [lines[li + k].raw for k in range(min(n, len(lines) - li))] if li < len(lines) else []
            raise ReplayDivergence(
                f"Divergenz bei Original-Zeile {li} (Runde {lines[li].round_num if li < len(lines) else '?'}) "
                f"nach {method}{args}:\n  erwartet: {expected!r}\n  Replay:   {new_lines!r}"
            )
        self.action_log.append((method, args, kwargs))
        return li + n

    def apply_ambiguous(self, lines: list[LogLine], li: int, method: str, candidates: list[tuple]) -> int:
        """Mehrere strukturell gleichwertige Kandidaten (z.B. moon_order-
        Permutationen): auf einer frischen Kopie (exakt bis hierher
        nachgespielt) je Kandidat testen, welcher die Original-Log-Zeilen ab
        `li` exakt reproduziert -- der Gewinner wird auf die echte Instanz
        angewendet."""
        if len(candidates) == 1:
            args, kwargs = candidates[0]
            return self.apply(lines, li, method, *args, **kwargs)
        for args, kwargs in candidates:
            trial = self._fresh_game()
            matched, n, _ = self._call_and_check(trial, lines, li, method, args, kwargs)
            if matched:
                _matched2, n2, _ = self._call_and_check(self.g, lines, li, method, args, kwargs)  # auf Original anwenden
                self.action_log.append((method, args, kwargs))
                return li + n2
        raise ReplayDivergence(
            f"Mehrdeutiger Zug ({method}, {len(candidates)} Kandidaten) bei Original-Zeile {li} "
            f"(Runde {lines[li].round_num}) -- keiner reproduziert den Original-Log exakt."
        )

    # ── Hilfsfunktionen (implizite, unlogged Zwischenzuege) ─────────────────
    def ensure_drafting_actor(self, target: int, li: int = -1):
        guard = 0
        while self.g.phase() == "drafting" and self.g.current_player() != target:
            guard += 1
            if guard > 4:
                raise ReplayDivergence(f"Zeile {li}: ensure_drafting_actor: Spieler {target} nach {guard} Pass-Versuchen nicht erreicht.")
            before = self.g.log_len()
            self.g.apply_pass()
            if self.g.log_len() != before:
                raise ReplayDivergence(f"Zeile {li}: apply_pass() hat unerwartet Log-Zeilen erzeugt.")
            self.action_log.append(("apply_pass", (), {}))

    def end_tiling_cascade(self, lines: list[LogLine], li: int) -> int:
        """Rundenende: beide Spieler beenden ihr Tiling (mind. der letzte
        Aufruf loest execute_end_tiling aus -- Strafen, Rundenwechsel/Ende).

        WICHTIG (empirisch entdeckt): `apply_tiling`/`end_tiling` nehmen den
        Spieler-Index EXPLIZIT entgegen (siehe py.rs) -- Tiling-Zuege sind
        NICHT an `current_player` gebunden (anders als Drafting), Spieler
        koennen ihre volle Reihen in beliebiger Reihenfolge/Verzahnung legen.
        Deshalb hier beide Spieler unconditional in fester Reihenfolge
        beenden, statt `current_player` zu verfolgen."""
        before = self.g.log_len()
        cascade_calls = []
        for player in (0, 1):
            if self.g.phase() != "tiling":
                break
            if self.g.pending_tiling_count(player) != 0:
                raise ReplayDivergence(
                    f"Zeile {li}: Spieler {player} hat beim Rundenende noch offene Tiling-Zuege."
                )
            self.g.end_tiling(player)
            cascade_calls.append(player)
        after = self.g.log_len()
        new_lines = self.g.log_since(before)
        n = len(new_lines)
        if li + n > len(lines) or any(lines[li + k].raw != new_lines[k] for k in range(n)):
            raise ReplayDivergence(
                f"Divergenz in der Rundenende-Kaskade ab Original-Zeile {li} (Runde {lines[li].round_num}):\n"
                f"  erwartet: {[lines[li + k].raw for k in range(min(n, len(lines) - li))]!r}\n"
                f"  Replay:   {new_lines!r}"
            )
        for p in cascade_calls:
            self.action_log.append(("end_tiling", (p,), {}))
        return li + n

    def maybe_silent_chip_complete(self, actor: int, pattern_row: int) -> bool:
        """Entdeckte Logging-Asymmetrie: der MENSCH-Pfad `apply_tiling_chips`
        (py.rs) loggt "🎫 ... komplettiert Reihe N ...", aber der KI-Pfad
        (`ai_tiling_step` -> `TilingStep::Chips` -> `apply_bonus_chips_with`,
        round_end.rs) tut das NICHT -- die KI kann also eine Musterreihe
        per Bonuschip vervollstaendigen, OHNE dass eine Log-Zeile dafuer
        entsteht. Erkennung: Zielreihe der kommenden Tiling-Aktion ist noch
        nicht voll -- dann hier nachholen (die erzeugte "🎫"-Zeile wird
        bewusst NICHT gegen das Original geprueft, da sie dort fehlt; das
        Ereignis wird stattdessen in `silent_chip_gaps` vermerkt und im
        Report transparent gemacht)."""
        st = json.loads(self.g.state_json())
        row = st["players"][actor]["pattern_lines"][pattern_row]
        if row["tiles"] and len(row["tiles"]) == row["capacity"]:
            return False
        self.g.apply_tiling_chips(actor, pattern_row)
        self.action_log.append(("apply_tiling_chips", (actor, pattern_row), {}))
        self.silent_chip_gaps.append((self.g.round_number(), actor, pattern_row))
        return True

    def apply_end_scoring(self, lines: list[LogLine], li: int) -> int:
        before = self.g.log_len()
        self.g.end_scoring_json()
        after = self.g.log_len()
        new_lines = self.g.log_since(before)
        n = len(new_lines)
        if li + n > len(lines) or any(lines[li + k].raw != new_lines[k] for k in range(n)):
            raise ReplayDivergence(
                f"Divergenz bei der Endwertung ab Original-Zeile {li} (Runde {lines[li].round_num}):\n"
                f"  erwartet: {[lines[li + k].raw for k in range(min(n, len(lines) - li))]!r}\n"
                f"  Replay:   {new_lines!r}"
            )
        self.action_log.append(("end_scoring_json", (), {}))
        return li + n

    # ── Oracle-Hook ──────────────────────────────────────────────────────────
    def maybe_oracle(self, actor: int, kind: str, played_desc: str, fields: dict):
        self.turn_idx += 1
        rec = OracleRecord(
            turn_idx=self.turn_idx, round_num=self.g.round_number(), actor=actor,
            actor_name=self.players[actor], kind=kind, played_desc=played_desc,
        )
        if self.g.phase() != "drafting":
            rec.reason = f"Phase '{self.g.phase()}' statt drafting (unerwartet)"
            self.oracle_records.append(rec)
            return
        # --dump-states (2026-08-18, Nutzer-Auftrag "die Partien als
        # AUSGANGSSTELLUNG hernehmen, um Drafting und Tiling zu debuggen"):
        # der Zustand wird VOR allen Frueh-Ausstiegen geschrieben, damit auch
        # Runde 5 und `--no-oracle` einen Pruefstand liefern. Rein additiv --
        # ohne den Schalter aendert sich nichts.
        if self.dump_fh is not None:
            self.dump_fh.write(json.dumps({
                "turn": self.turn_idx, "round": rec.round_num, "kind": kind,
                "player": rec.actor,
                "played": rec.played_desc,
                "fields": fields,
                "state": json.loads(self.g.state_json()),
            }, ensure_ascii=False) + chr(10))
        if rec.round_num >= 5:
            rec.reason = "Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet"
            self.oracle_records.append(rec)
            return
        if not self.do_oracle:
            rec.reason = "--no-oracle"
            self.oracle_records.append(rec)
            return
        state_json = self.g.state_json()
        seed = deterministic_seed(self.log_name, self.turn_idx)
        try:
            out = evaluate_oracle(state_json, self.model_path, self.sims, self.c_puct, seed, kind, fields)
        except Exception as e:  # defensiv, Praezedenz build_frozen_oracle_labels.py
            rec.reason = f"Fehler: {e}"
            self.oracle_records.append(rec)
            return
        rec.num_actions = out.get("num_actions") or 0
        rec.root_value = out.get("root_value")
        if "error" in out:
            rec.reason = out["error"]
        else:
            rec.evaluated = True
            rec.played_rank = out["played_rank"]
            rec.played_q = out["played_q"]
            rec.top_q = out["top_q"]
            rec.top_desc = out["top_desc"]
            rec.delta_win_pct = out["delta_win_pct"]
            rec.ambiguous_match = out.get("ambiguous_match", False)
        self.oracle_records.append(rec)

    # ── Aktions-Hinweis (#a) ─────────────────────────────────────────────────
    def hint_for(self, li: int, typ: str) -> dict | None:
        """Die `#a`-Nutzlast vor Zeile `li`, sofern sie zum erwarteten
        Aktionstyp passt. `None` heisst: kein Hinweis vorhanden (altes Log,
        Arena-Log, KI-Stapelzug) -- der Aufrufer faellt dann auf den Textweg
        zurueck. Ein Hinweis mit ANDEREM Typ wird ebenfalls verworfen, statt
        ihn zu erzwingen: das waere genau die Sorte stiller Ersatzwahl, gegen
        die diese Registrierung angetreten ist."""
        for h in self.hints.get(li, []):
            a = h.get("a") or {}
            if a.get("type") == typ and isinstance(h.get("id"), int):
                return h
        return None

    # ── Stein-Zug: Quelle/Kandidaten aufloesen ──────────────────────────────
    def resolve_stone(self, lines: list[LogLine], li: int, m: re.Match, is_global: bool, actor: int) -> int:
        color = m.group("color")
        dest = m.group("dest")
        row = -1 if dest == "Strafleiste" else int(dest.split(" ")[1]) - 1

        if is_global:
            factory_id = None
            expected = {"SMALL_FACTORY_MOON"}
        else:
            src = m.group("src")
            factory_id = None if src == "GF" else int(src[1:])
            key = "GF" if factory_id is None else factory_id
            if not self.sun_used[key]:
                expected = {"LARGE_FACTORY_SUN"} if factory_id is None else {"SMALL_FACTORY_SUN"}
            else:
                expected = {"LARGE_FACTORY_MOON"} if factory_id is None else {"SMALL_FACTORY_MOON"}

        st = json.loads(self.g.state_json())

        # ── ID-WEG (PREREG_action_id_logging.md S3) ──────────────────────────
        # Liegt ein `#a`-Hinweis vor, wird die aufgezeichnete Aktion ANGEWANDT
        # statt aus der Prosa erraten. Das erledigt genau die drei Ebenen, die
        # am 2026-08-18 gekippt sind (par.1): das Emoji bestimmt den Aktionstyp
        # nicht, "von GF" bestimmt die Quelle nicht, und eine gueltige, aber nie
        # GENERIERTE Aktion (`LargeFactoryMoon`) fehlt in der Kandidatenliste.
        # Die ID kommt aus `valid_moves` (Stueck S1) und ist damit dieselbe
        # Zahl, gegen die der Policy-Kopf trainiert.
        #
        # WICHTIG -- die ID ist NICHT eindeutig: `moon_order` fliesst nicht in
        # sie ein (net_mcts.rs:1824). Der Hinweis traegt die Reihenfolge
        # deshalb in seinen kanonischen Feldern mit; sie wird hier bevorzugt,
        # und wenn sie nicht passt, bleibt die Permutations-Disambiguierung
        # weiter unten als Netz darunter.
        hint = self.hint_for(li, "stone")
        if hint is not None:
            per_id = [mv for mv in st["valid_moves"] if mv.get("id") == hint["id"]]
            if per_id:
                self.hint_used += 1
                ha = hint["a"]
                cand_calls = []
                # Exakte Reihenfolge aus dem Hinweis zuerst, danach die
                # kanonische je Kandidat -- niemals raten, nur ordnen.
                for mv in sorted(per_id, key=lambda m: 0 if m["source"] == ha.get("source") else 1):
                    orders = []
                    if isinstance(ha.get("moon_order"), list):
                        orders.append(list(ha["moon_order"]))
                    if list(mv["moon_order"]) not in orders:
                        orders.append(list(mv["moon_order"]))
                    for o in orders:
                        cand_calls.append(((mv["source"], mv["color"], mv["row"],
                                            mv["factory_id"], o), {}))
                # `sun_used` weiterfuehren -- nur der Textweg liest es, aber
                # ein Log kann beide Wege mischen (Arena-Zeilen ohne Hinweis).
                if cand_calls and cand_calls[0][0][0] in ("SMALL_FACTORY_SUN", "LARGE_FACTORY_SUN"):
                    self.sun_used["GF" if factory_id is None else factory_id] = True
                return self.apply_ambiguous(lines, li, "apply_stone", cand_calls)
            raise ReplayDivergence(
                f"Zeile {li} (Runde {lines[li].round_num}): Aktions-ID {hint['id']} "
                f"aus dem Log ist hier nicht legal. Verfuegbare Stein-IDs: "
                + ", ".join(sorted({str(mv['id']) for mv in st['valid_moves'] if mv['type'] == 'stone'}))
            )
        self.hint_missing += 1
        # ── TEXTWEG (Rueckfall: alte Logs, Arena-Logs, KI-Stapelzug) ─────────

        candidates = [
            mv for mv in st["valid_moves"]
            if mv["type"] == "stone" and mv["color"] == color and mv["row"] == row
            and mv["factory_id"] == factory_id and mv["source"] in expected
        ]
        if not candidates:
            # QUELLEN-TOLERANTER RUECKFALL (2026-08-18): das Log-Emoji ist KEIN
            # verlaesslicher Indikator des Aktionstyps, und "von GF" ist keiner
            # der Quelle. Nachgewiesen an game_20260818_200516_seed585858:
            # dieselbe Lage -- Rest der grossen Fabrik im Mondpool,
            # Startspielerstein vergeben (laut engine_manual.md:118 NUR bei
            # einer Mond-Entnahme) -- steht in Runde 1 (Zeilen 15/20/21) mit
            # SONNE und in Runde 2 (Zeilen 78/79/80) mit MOND im Log. Zudem
            # traegt Aktion C (Mond ueber alle Fabriken + GF-Mondpool) intern
            # `SMALL_FACTORY_MOON` mit `factory_id=None`, passt also nicht zu
            # den LARGE_*-Quellen, die "von GF" erwarten laesst.
            # Deshalb: ueber ALLE Quellen suchen, `expected` nur noch als
            # Sortier-Praeferenz. Farbe, Reihe und factory_id bleiben harte
            # Bedingungen -- die Zuordnung wird also nicht beliebig.
            candidates = sorted(
                (mv for mv in st["valid_moves"]
                 if mv["type"] == "stone" and mv["color"] == color and mv["row"] == row
                 and mv["factory_id"] == factory_id),
                key=lambda mv: 0 if mv["source"] in expected else 1,
            )
        if not candidates:
            # Diagnose statt Raten (2026-08-18): die verfuegbaren Stein-Zuege
            # mitgeben, sonst ist die Divergenz nicht aufzuklaeren.
            verf = [
                f"{mv['source']}/f{mv['factory_id']}/{mv['color']}/r{mv['row']}"
                for mv in st["valid_moves"] if mv["type"] == "stone"
            ]
            raise ReplayDivergence(
                f"Zeile {li} (Runde {lines[li].round_num}): kein passender Stein-Zug: "
                f"color={color} row={row} factory_id={factory_id} is_global={is_global} "
                f"erwartet={expected}  |  verfuegbar ({len(verf)}): " + ", ".join(sorted(set(verf))[:24])
            )

        if candidates[0]["source"] in ("SMALL_FACTORY_SUN", "LARGE_FACTORY_SUN"):
            key = "GF" if factory_id is None else factory_id
            self.sun_used[key] = True

        # `generate_valid_moves` (validation.rs) liefert je (Fabrik,Farbe,Reihe)
        # NUR EINE kanonische moon_order -- validate_move akzeptiert aber JEDE
        # Permutation desselben Multisets (siehe validation.rs::validate_small_sun,
        # Multiset-Vergleich). Das reale Spiel (Server/UI) kann eine ANDERE
        # gueltige Reihenfolge gewaehlt haben -- daher hier alle distinkten
        # Permutationen als Kandidaten generieren und ueber die Original-Log-
        # Zeilen (naechste "Mond-Stapel"-Zeile zeigt die tatsaechliche
        # Reihenfolge) disambiguieren.
        cand_calls = []
        seen_orders: set[tuple] = set()
        for cand in candidates:
            base_order = cand["moon_order"]
            if len(base_order) >= 2:
                perms = set(itertools.permutations(base_order))
            else:
                perms = {tuple(base_order)}
            for perm in perms:
                key2 = (cand["source"], cand["color"], cand["row"], cand["factory_id"], perm)
                if key2 in seen_orders:
                    continue
                seen_orders.add(key2)
                cand_calls.append(((cand["source"], cand["color"], cand["row"], cand["factory_id"], list(perm)), {}))

        # NACHGESTELLTE RETTUNGS-KANDIDATEN (par.8 Punkt 1 der Registrierung).
        # Die Kandidatenliste oben kommt aus `valid_moves`, also aus dem
        # GENERATOR -- und der erzeugt Mond-Entnahmen ausschliesslich in der
        # globalen Form (validation.rs:214). Die TEIL-Entnahmen
        # (`LargeFactoryMoon`, `SmallFactoryMoon` mit factory_id) werden vom
        # Validator aber AKZEPTIERT und sind ueber die API im Menschenspiel
        # entstanden. Genau daran scheitert `game_20260818_200516_seed585858`:
        # der Textweg griff zur globalen Mond-Entnahme, also zu einer ANDEREN
        # Aktion, und das fiel erst drei Zeilen spaeter auf.
        #
        # Warum das gefahrlos ist: `apply_ambiguous` probiert JEDEN Kandidaten
        # auf einer frischen Kopie und verlangt, dass er die Original-Zeilen
        # EXAKT reproduziert. Ein zusaetzlicher Kandidat kann also nie eine
        # falsche Wahl herbeifuehren -- er kann nur einen Fall retten, den der
        # Generator nicht abdeckt. Deshalb steht er HINTEN.
        #
        # Nur fuer das schlichte Format (`is_global == False`), und nur fuer
        # neue Logs unnoetig: dort greift der ID-Weg weiter oben.
        if not is_global:
            teil_quelle = "LARGE_FACTORY_MOON" if factory_id is None else "SMALL_FACTORY_MOON"
            if not any(c[0][0] == teil_quelle and c[0][3] == factory_id for c in cand_calls):
                cand_calls.append(((teil_quelle, color, row, factory_id, []), {}))

        return self.apply_ambiguous(lines, li, "apply_stone", cand_calls)

    # ── Kuppel-Zug ────────────────────────────────────────────────────────────
    def resolve_dome(self, lines: list[LogLine], li: int, tile_id: int, slot_row: int, slot_col: int, rotation: int) -> int:
        st = json.loads(self.g.state_json())
        vm = st["valid_moves"]
        if any(mv["type"] == "dome_stack_choose" and mv["chosen_id"] == tile_id
               and mv["slot_row"] == slot_row and mv["slot_col"] == slot_col and mv["rotation"] == rotation
               for mv in vm):
            return self.apply(lines, li, "apply_dome_stack_choose", tile_id, slot_row, slot_col, rotation)
        if any(mv["type"] == "dome_display" and mv["tile_id"] == tile_id
               and mv["slot_row"] == slot_row and mv["slot_col"] == slot_col and mv["rotation"] == rotation
               for mv in vm):
            return self.apply(lines, li, "apply_dome", tile_id, slot_row, slot_col, rotation)
        raise ReplayDivergence(
            f"Zeile {li} (Runde {lines[li].round_num}): kein passender Kuppel-Zug: "
            f"tile={tile_id} slot=({slot_row},{slot_col}) rot={rotation}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Haupt-Treiber
# ═══════════════════════════════════════════════════════════════════════════

def run(log_path: Path, model_path: Path, sims: int, c_puct: float, do_oracle: bool,
        limit: int | None, dump_states: str | None = None):
    """Gibt (rep, lines, li_reached, divergence_msg_or_None) zurueck -- wirft
    NICHT bei einer ReplayDivergence, sondern faengt sie ab, damit der
    Aufrufer trotzdem einen (Teil-)Report ueber das bis dahin Erreichte
    schreiben kann (Auftrag: "bei Divergenz praezise abbrechen und
    berichten", nicht einfach nur crashen)."""
    header, lines, hints = load_log(log_path)
    rep = Replayer(header, log_path.name, str(model_path), sims, c_puct, do_oracle,
                   dump_path=dump_states)
    rep.hints = hints
    name_to_idx = rep.name_to_idx

    n_lines = len(lines) if limit is None else min(limit, len(lines))
    t_start = time.time()

    try:
        li = _run_loop(rep, lines, name_to_idx, n_lines, do_oracle, t_start)
    except ReplayDivergence as e:
        li_match = re.search(r"Zeile (\d+)", str(e))
        li = int(li_match.group(1)) if li_match else 0
        return rep, lines, li, str(e)
    return rep, lines, li, None


def _run_loop(rep: "Replayer", lines: list[LogLine], name_to_idx: dict, n_lines: int, do_oracle: bool, t_start: float) -> int:
    li = 0
    n_oracle_done = 0
    while li < n_lines:
        # Die 🏁-Marker-Zeile (Startspielerstein) wird VOR der eigentlichen
        # Aktionszeile geloggt (siehe execution.rs::apply_first_player_marker,
        # aufgerufen aus execute_take VOR dem Aktions-Log) -- fuer die
        # Dispatch-Entscheidung ueberspringen, aber `li` selbst bleibt beim
        # Marker (bzw. der ersten Zeile des Blocks), damit consume_block sie
        # als Teil derselben erzeugten Log-Zeilenfolge mitvalidiert.
        li_disp = li
        cat, m = classify(lines[li_disp].body)
        while cat in SECONDARY_LINE_CATEGORIES:
            li_disp += 1
            if li_disp >= n_lines:
                raise ReplayDivergence(f"Zeile {li}: {cat}-Zeile ohne folgende Aktionszeile.")
            cat, m = classify(lines[li_disp].body)
        cur = lines[li_disp]
        if cat is None or cat not in PRIMARY_CATEGORIES:
            raise ReplayDivergence(
                f"Zeile {li_disp} (Runde {cur.round_num}) nicht als primaere Aktionszeile erkannt: {cur.raw!r}"
            )

        if cat == "GAME_START":
            # Die Zeile wurde bereits durch die PyGame-Konstruktion erzeugt --
            # nur validieren, kein neuer Aufruf noetig.
            new_lines = rep.g.log_since(0)
            if len(new_lines) < 1 or lines[0].raw != new_lines[0]:
                raise ReplayDivergence(f"GAME_START stimmt nicht ueberein: {new_lines!r} vs {lines[0].raw!r}")
            li = 1

        elif cat == "SCORING_CHOICE":
            ids = ast.literal_eval(m.group("ids"))
            li = rep.apply(lines, li, "select_scoring", ids)

        elif cat == "START_TILE":
            actor = name_to_idx[m.group("name")]
            li = rep.apply(lines, li, "apply_start_tile", actor, int(m.group("tile")),
                            int(m.group("row")), int(m.group("col")), int(m.group("rot")))

        elif cat in ("SUN_TAKE", "MOON_GLOBAL_TAKE"):
            actor = name_to_idx[m.group("name")]
            rep.ensure_drafting_actor(actor, li)
            is_global = cat == "MOON_GLOBAL_TAKE"
            # Engine-Fix (mcts.rs::label_search_move) disambiguiert factory_id=None
            # jetzt selbst: "Mondpool" fuer Aktion C (is_global), "GF" nur noch fuer
            # echte Grossfabrik-Ziehungen -- played_key() muss dieselbe Konvention
            # nutzen wie move_key()/STONE_DESC_RE, sonst schlaegt der Oracle-Abgleich
            # fuer JEDEN globalen Mondpool-Zug fehl ("nicht unter Kandidaten identifiziert").
            src_label = "Mondpool" if is_global else m.group("src")
            fields = {"color": m.group("color"), "src": src_label, "dest": m.group("dest")}
            rep.maybe_oracle(actor, "stone", cur.body, fields)
            li = rep.resolve_stone(lines, li, m, is_global, actor)
            n_oracle_done += 1

        elif cat == "STACK_PEEK":
            actor = name_to_idx[m.group("name")]
            rep.ensure_drafting_actor(actor, li)
            rep.maybe_oracle(actor, "dome_stack_peek", cur.body, {})
            li = rep.apply(lines, li, "apply_dome_stack_peek")
            n_oracle_done += 1

        elif cat == "DOME_PLACE":
            actor = name_to_idx[m.group("name")]
            rep.ensure_drafting_actor(actor, li)
            st = json.loads(rep.g.state_json())
            is_stack = any(mv["type"] == "dome_stack_choose" for mv in st["valid_moves"])
            kind = "dome_stack" if is_stack else "dome_display"
            fields = {"tile": m.group("tile"), "r": m.group("r"), "c": m.group("c")}
            rep.maybe_oracle(actor, kind, cur.body, fields)
            li = rep.resolve_dome(lines, li, int(m.group("tile")), int(m.group("r")), int(m.group("c")), int(m.group("rot")))
            n_oracle_done += 1

        elif cat == "CHIP_TAKE":
            actor = name_to_idx[m.group("name")]
            rep.ensure_drafting_actor(actor, li)
            rep.maybe_oracle(actor, "bonus_chip", cur.body, {"fid": m.group("fid")})
            li = rep.apply(lines, li, "apply_bonus_chip", int(m.group("fid")))
            n_oracle_done += 1

        elif cat == "TILING_PLACE":
            actor = name_to_idx[m.group("name")]
            nxt = lines[li + 1]
            _, score_m = classify(nxt.body)
            if score_m is None or "row" not in score_m.groupdict():
                raise ReplayDivergence(f"Zeile {li}: erwartete TILING_SCORE-Folgezeile fehlt: {nxt.raw!r}")
            pattern_row = int(score_m.group("row")) - 1
            slot_row, slot_col, space_index = int(m.group("r")), int(m.group("c")), int(m.group("si"))
            rep.maybe_silent_chip_complete(actor, pattern_row)
            li = rep.apply(lines, li, "apply_tiling", actor, pattern_row, slot_row, slot_col, space_index)

        elif cat == "CHIPS_COMPLETE":
            actor = name_to_idx[m.group("name")]
            li = rep.apply(lines, li, "apply_tiling_chips", actor, int(m.group("row")) - 1)

        elif cat in ("ROUND_START", "GAME_OVER", "ROUND_STRAFE", "UNPLACEABLE"):
            rep.round_scores_crosscheck.append((rep.g.round_number(), rep.g.scores()))
            li = rep.end_tiling_cascade(lines, li)
            rep._reset_sun_used()

        elif cat == "FINAL_SCORE":
            li = rep.apply_end_scoring(lines, li)

        else:  # pragma: no cover
            raise ReplayDivergence(f"Unbehandelte Kategorie {cat} bei Zeile {li}: {cur.raw!r}")

        if do_oracle and rep.oracle_records and rep.oracle_records[-1].evaluated:
            elapsed = time.time() - t_start
            print(
                f"  [{n_oracle_done}] Runde {rep.oracle_records[-1].round_num} "
                f"{rep.oracle_records[-1].actor_name}: Rang {rep.oracle_records[-1].played_rank}"
                f"/{rep.oracle_records[-1].num_actions}, "
                f"Δwin%={rep.oracle_records[-1].delta_win_pct:.1f} "
                f"(elapsed={elapsed:.0f}s)",
                flush=True,
            )
        elif li % 20 == 0:
            print(f"  ... Zeile {li}/{n_lines}", flush=True)

    # ALTBESTANDS-KORREKTUR (gefunden 2026-08-18 beim Bau von S3): hier stand
    # `return rep, lines`. Der Aufrufer `run()` legt das Ergebnis aber auf `li`
    # ab und gibt es als `li_reached` weiter -- die "wie weit kam der Replay"-
    # Zahl im Report war auf dem ERFOLGSPFAD also ein Tupel, kein Zeilenindex.
    # Auf dem Divergenzpfad war sie korrekt, deshalb ist es nie aufgefallen.
    return li


def main() -> None:
    # Verzoegerter Import: die Report-Schicht liegt seit 2026-08-18 in einem
    # eigenen Modul und greift ihrerseits auf `classify`/`LogLine`/`ROOT` von
    # hier zurueck. Der Import steht deshalb IN `main()` -- an beiden
    # Modul-Koepfen waere er ein Zyklus (siehe game_log_report.py).
    from game_log_report import build_report

    check_prereqs()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", default=str(ROOT / "static" / "log" / "game_20260725_214038_seed465392.log"))
    ap.add_argument("--model", default=str(DEFAULT_MODEL))
    ap.add_argument("--sims", type=int, default=DEFAULT_SIMS)
    ap.add_argument("--c-puct", type=float, default=DEFAULT_C_PUCT)
    ap.add_argument("--no-oracle", action="store_true", help="nur Parser+Replay, keine Netzsuche (schnell, zum Testen)")
    ap.add_argument("--limit", type=int, default=None, help="nur die ersten N Log-Zeilen verarbeiten (Debug)")
    ap.add_argument("--dump-states", default=None,
                    help="JSONL-Datei mit dem Zustand an JEDEM Entscheidungspunkt "
                         "(Pruefstand fuer Drafting/Tiling-Debugging)")
    ap.add_argument("--oracle-json", default=None,
                    help="JSONL-Datei mit den Oracle-Records (maschinenlesbar; "
                         "Verbraucher: PREREG_human_game_oracle_gap.md par.4)")
    ap.add_argument("--out", default=None, help="Ziel-Markdown-Datei (Default: evaluations/game_analysis/game_analysis_<logname>.md)")
    args = ap.parse_args()

    log_path = Path(args.log)
    out_path = Path(args.out) if args.out else ROOT / "evaluations" / "game_analysis" / f"game_analysis_{log_path.stem.replace('game_', '')}.md"

    print(f"Lade {log_path} ...")
    t0 = time.time()
    rep, lines, li_reached, divergence = run(
        log_path, Path(args.model), args.sims, args.c_puct, not args.no_oracle, args.limit,
        dump_states=args.dump_states
    )
    if getattr(rep, "dump_fh", None) is not None:
        rep.dump_fh.close()
        print(f"  Zustands-Dump: {args.dump_states}")
    if args.oracle_json:
        # Maschinenlesbare Fassung dessen, was der Markdown-Report aus
        # `oracle_records` rendert -- damit die par.4-Klassifikation
        # (PREREG_human_game_oracle_gap.md) nicht den Report parsen muss.
        with open(args.oracle_json, "w", encoding="utf-8") as fh:
            for rec in rep.oracle_records:
                fh.write(json.dumps(dataclasses.asdict(rec), ensure_ascii=False) + "\n")
        print(f"  Oracle-JSONL: {args.oracle_json}")
    elapsed = time.time() - t0
    n_lines_total = len(lines)
    if divergence:
        print(f"\nABBRUCH: {divergence}\n", file=sys.stderr)

    header, _, _ = load_log(log_path)
    report = build_report(header, log_path, rep, divergence, li_reached, n_lines_total, elapsed, lines)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"\nReport geschrieben: {out_path}")
    if divergence:
        sys.exit(1)


if __name__ == "__main__":
    main()
