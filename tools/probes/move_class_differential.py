# -*- coding: utf-8 -*-
"""
tools/probes/move_class_differential.py -- ZUGKLASSEN-DIFFERENTIAL AUS DEN
CLAUDE-PARTIEN (v29-Begleitprogramm, Fahrplanpunkt 25).

Vorregistrierung: `evaluations/PREREG_claude_play_interface.md` par.10 (Zeilen
788-829) und der AGENTEN-AUFTRAG P3 derselben Datei (Zeilen 910-931). Die
fuenf dort registrierten Punkte sind hier 1:1 umgesetzt; jede Abweichung steht
im Artefakt unter `abweichungen_von_par10` UND in diesem Kopf.

FRAGE (par.10): an welchen Entscheiden weicht Claude vom Netz ab, und gewinnt
danach? Nicht "wie viel zieht Claude", sondern WELCHE ZUGKLASSE dem Netz
fehlt. n ist klein -- die Sonde ist ein Richtungsgeber, kein Verdikt.

KEIN NEUBAU: der ganze Unterbau steht in `tools/analyze_game_log.py`
(Parser, byte-exaktes Replay, Orakel `evaluate_oracle`, `OracleRecord`).
Diese Datei ist die AUSWERTESCHICHT darueber plus der Rauschboden; das
Konsum-Muster fuer `rep.oracle_records` ist von `tools/game_log_report.py`
uebernommen (dort `build_report`, Abschnitte (a)/(b)), das Muster fuer den
Arena-Log-Replay von `tools/probes/arena_column_probe.py:60-94`.

GRUNDMENGE (Punkt 4 der Prereg, "alle Claude-Entscheide der Partien g01-g07"):
  DRIN:  g01 .. g07 -- die sieben echten Partien der Reihe. Gegner laut
         Manifest: g01 v24-b06_k3p10, g02-g05 v27-b01_brierbest,
         g06/g07 v28-b02_brierbest (je `manifest.json` Feld `opponent`).
  RAUS:  g00     -- Rauchtest gegen die HEURISTIK (`manifest.json`:
                    `ai_model` "heuristic", `ai_sims` 20), 12 Logzeilen.
         gsmoke  -- Wegwerf-Rauchtest, 3 Logzeilen.
         gsmoke2 -- Wegwerf-Rauchtest; par.9 der Prereg nennt ihn woertlich
                    "Wegwerf-Partie gsmoke2 (nicht Teil der Reihe)"
                    (PREREG_claude_play_interface.md:781).
  Die Ausschlussliste steht als `EXCLUDED_GAMES` im Code und wird ins
  Artefakt geschrieben -- Auswahl begruendet, nicht geraten.

WELCHE LOGDATEI: par.10 nennt `g*/game.log`. Tatsaechlich traegt nur g01 die
`# {...}`-Kopfzeile und die `#a`-Aktions-IDs in `game.log`; ab g02 liegt das
maschinenlesbare Log in `.engine.log` (game.log ist dort ein reines
Textprotokoll ohne Kopf, und `analyze_game_log.load_log` braucht den Kopf --
analyze_game_log.py:259-260). Das Werkzeug nimmt darum `.engine.log`, wenn es
existiert, sonst `game.log`, und schreibt die benutzte Datei je Partie ins
Artefakt. Abweichung vom Wortlaut von par.10, nicht von seiner Absicht.

WER IST CLAUDE: aus dem Log-KOPF, nicht geraten. `load_log` gibt `header`
zurueck (analyze_game_log.py:225-262); der Kopf traegt `players` und
`ai_player` (Schreibstelle `tools/claude_play.py`, Format wie `server.py`).
Claude ist die NICHT-KI-Seite: `claude_idx = 1 - header["ai_player"]`, und
`header["players"][claude_idx] == "Claude"` wird hart geprueft. Gegenprobe
gegen `manifest.json` Feld `me` (dasselbe Index-Feld), Abweichung ist ein
harter Fehler.

NUR CLAUDES ENTSCHEIDE (Punkt 2): `analyze_game_log` bewertet von sich aus
BEIDE Seiten (`_run_loop` ruft `maybe_oracle` unabhaengig vom Akteur,
analyze_game_log.py:1212/1219/1230/1245). Das waere die doppelte Rechenzeit
fuer eine Haelfte, die niemand auswertet. Dieses Werkzeug legt darum EINEN
Filter um `Replayer.maybe_oracle` (siehe `_install_oracle_filter`): der
Entscheid der Gegenseite wird weiter als `OracleRecord` protokolliert (mit
Grund), aber ohne Netzsuche. `turn_idx` laeuft dabei exakt wie im Original
weiter, damit der zugindex-abgeleitete Seed (`deterministic_seed`) derselbe
bleibt.

DAS WURZELFENSTER (beim Selbsttest 2026-09-14 gemessen, nicht vermutet): die
Suche rangt nur `m = clamp(round(sims/16), 4, 16)` Wurzelkandidaten
(net_mcts.rs:3180-3186). Am ersten Entscheid von g02 stehen 158 legale Zuege
und 16 Kandidaten (@400; @8 Sims waren es 4). Liegt Claudes Zug ausserhalb,
gibt es kein `played_q` und damit KEINE Wurzelwert-Differenz -- die Abweichung
selbst ist trotzdem sicher. Solche Entscheide zaehlen darum als
`ausserhalb_kandidatenfenster` getrennt mit und stehen in keinem Mittelwert.
Volltext samt Ausweg (`--gumbel-top-m`) in `CANDIDATE_WINDOW_NOTE`.

KOSTEN: eine Netzsuche @400 je Claude-Entscheid, das Netz wird je Aufruf neu
geladen (`Net::load_auto` in `net_search_state_json`, engine/src/lib.rs:1053).
par.10 rechnet mit unter 30 min, exklusiv.

AUFRUF (voller Lauf, exklusiv, ohne Pipe und ohne Umleitung):

    python -X utf8 -u tools/probes/move_class_differential.py

Mini-Selbsttest (eine Partie, wenige Sims, harter Deckel auf die Entscheide):

    python -X utf8 -u tools/probes/move_class_differential.py \\
        --games g02 --sims 8 --max-decisions 5 --limit-lines 40 \\
        --no-noise-floor --out <scratch>/selftest.json

Ergebnis: `evaluations/artifacts/move_class_differential_v29.json`
(n / Grundmenge / Einheit, `laufzeit`-Block, `cli_args`, Modell und
Sims/c_puct des Orakels, Top-10-Abweichungsklassen, Rauschboden je Klasse,
je Partie bewertete und nicht bewertete Entscheide mit Grund).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import time
from collections import Counter, defaultdict

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools"))
sys.path.insert(0, str(_ROOT / "tools" / "probes"))

import analyze_game_log as agl  # noqa: E402
from game_log_report import extract_full_score_timeline  # noqa: E402

PREREG = "evaluations/PREREG_claude_play_interface.md par.10 (Fahrplanpunkt 25)"

CLAUDE_PLAY_DIR = _ROOT / "evaluations" / "artifacts" / "claude_play"
DEFAULT_OUT = _ROOT / "evaluations" / "artifacts" / "move_class_differential_v29.json"

# Siehe Modulkopf, Abschnitt GRUNDMENGE. Die Gruende stehen hier, damit sie
# mit ins Artefakt wandern und nicht nur im Chat behauptet werden.
EXCLUDED_GAMES = {
    "g00": "Rauchtest gegen die Heuristik (manifest ai_model 'heuristic', ai_sims 20; 12 Logzeilen)",
    "gsmoke": "Wegwerf-Rauchtest (3 Logzeilen)",
    "gsmoke2": "Wegwerf-Rauchtest; PREREG_claude_play_interface.md:781 nennt ihn 'nicht Teil der Reihe'",
}

REASON_OTHER_SIDE = "nicht Claude -- Gegenseite, per Auftrag nicht bewertet (par.10 Punkt 2)"
REASON_CAP = "Deckel --max-decisions erreicht (Selbsttest)"
# Wortlaut aus `evaluate_oracle` (analyze_game_log.py:352) -- der Fall ist
# hier KEIN Ausfall, sondern ein eigener Befund, siehe CANDIDATE_WINDOW_NOTE.
REASON_OUTSIDE_WINDOW = "gespielte Aktion nicht unter Oracle-Kandidaten identifiziert"

CANDIDATE_WINDOW_NOTE = (
    "Die Netzsuche rangt NICHT alle legalen Zuege, sondern nur das Gumbel-Wurzelfenster: "
    "`m = clamp(round(sims/16), 4, GUMBEL_TOP_M)` mit `GUMBEL_TOP_M = 16` "
    "(engine/src/net_mcts.rs:3180-3186, Konstante :3142) -- bei @400 Sims also 16 Kandidaten, "
    "waehrend eine fruehe Runde-1-Stellung ueber 150 legale Zuege hat (gemessen am ersten "
    "Entscheid von g02: num_actions 158, moves 16). Ohne Wurzelrauschen (unser Fall) sind das "
    "die 16 mit dem hoechsten Prior. Spielt Claude ausserhalb dieses Fensters, meldet "
    "`evaluate_oracle` 'gespielte Aktion nicht unter Oracle-Kandidaten identifiziert' "
    "(analyze_game_log.py:351-353): kein played_q, also KEINE Wurzelwert-Differenz. "
    "Diese Faelle sind trotzdem Abweichungen im Sinn von par.10 Punkt 3 (Claudes Zug ist "
    "sicher nicht der Netzzug) und werden getrennt als `ausserhalb_kandidatenfenster` "
    "ausgewiesen -- sie stehen NICHT in den Nennern der Wurzelwert-Differenzen. "
    "Wer sie mit Q sehen will, oeffnet das Fenster ueber `MOSAIC_GUMBEL_TOP_M` "
    "(net_mcts.rs:3188-3200, hier als --gumbel-top-m); das ist dann ein ANDERES Instrument "
    "als das Arena-Instrument aus par.10 und gehoert in den Manifest-Diff."
)

# Rotation steht nur im Logtext der Kuppelzeile (PATTERNS["DOME_PLACE"],
# analyze_game_log.py:126-129), nicht in den Feldern, die `maybe_oracle`
# bekommt -- fuer die feine Klasse wird sie von dort gelesen.
_ROT_RE = re.compile(r"rot=(?P<rot>\d+)")
_ROW_RE = re.compile(r"^Reihe (?P<row>\d+)$")


# ═══════════════════════════════════════════════════════════════════════════
# Orakel-Filter: nur Claudes Entscheide, optionaler Deckel
# ═══════════════════════════════════════════════════════════════════════════

# Zustand des Filters. Ein Modul-Zustand reicht, weil die Partien streng
# nacheinander laufen (eine Netzsuche je Entscheid, kein Parallelismus hier).
_FILTER = {
    "actor": None,        # nur dieser Spielerindex wird bewertet; None = beide
    "max_decisions": None,
    "done": 0,
    "label": "",
    "fields": {},         # turn_idx -> die `fields` des Entscheids (s. u.)
    "actors": {},         # turn_idx -> Akteur (auch fuer uebersprungene)
}
_ORIG_MAYBE_ORACLE = agl.Replayer.maybe_oracle


def _filtered_maybe_oracle(self, actor, kind, played_desc, fields):
    """Ersatz fuer `Replayer.maybe_oracle` (analyze_game_log.py:764).

    Zwei Aufgaben, beide rein additiv zum Original:

    1. **Mitschreiben der `fields`.** `OracleRecord` traegt sie nicht, die
       Zugklasse haengt aber genau daran (Farbe/Quelle/Ziel bzw. Slot). Sie
       hier abzugreifen ist billiger und ehrlicher, als sie spaeter aus
       `played_desc` zurueckzuparsen.
    2. **Filtern.** Entscheide der Gegenseite (und alles hinter dem
       Selbsttest-Deckel) bekommen einen Record MIT Grund, aber keine
       Netzsuche. `turn_idx` wird wie im Original ZUERST erhoeht, damit
       `deterministic_seed(log_name, turn_idx)` fuer die bewerteten
       Entscheide exakt derselbe bleibt wie ohne Filter.
    """
    want = _FILTER["actor"]
    cap = _FILTER["max_decisions"]
    skip_reason = None
    if want is not None and actor != want:
        skip_reason = REASON_OTHER_SIDE
    elif cap is not None and _FILTER["done"] >= cap:
        skip_reason = REASON_CAP

    if skip_reason is not None:
        self.turn_idx += 1
        rec = agl.OracleRecord(
            turn_idx=self.turn_idx, round_num=self.g.round_number(), actor=actor,
            actor_name=self.players[actor], kind=kind, played_desc=played_desc,
            reason=skip_reason,
        )
        _FILTER["fields"][self.turn_idx] = dict(fields)
        _FILTER["actors"][self.turn_idx] = actor
        self.oracle_records.append(rec)
        return

    _FILTER["done"] += 1
    # Fortschritt VOR der Suche (CLAUDE.md "Lange Laeufe"): eine Zeile, die
    # erst nach der Suche kaeme, sagt nichts ueber die laufende Suche.
    print(f"  {_FILTER['label']}: Entscheid {_FILTER['done']} (Runde {self.g.round_number()}, "
          f"{kind}) -- Suche laeuft ...", flush=True)
    next_turn = self.turn_idx + 1
    _FILTER["fields"][next_turn] = dict(fields)
    _FILTER["actors"][next_turn] = actor
    return _ORIG_MAYBE_ORACLE(self, actor, kind, played_desc, fields)


def _install_oracle_filter() -> None:
    agl.Replayer.maybe_oracle = _filtered_maybe_oracle


def _reset_filter(actor, max_decisions, label) -> None:
    _FILTER.update({"actor": actor, "max_decisions": max_decisions, "done": 0,
                    "label": label, "fields": {}, "actors": {}})


# ═══════════════════════════════════════════════════════════════════════════
# Zugklassen (par.10 Punkt 3: Quelle x Farbe x Reihe bzw. Slot/Rotation)
# ═══════════════════════════════════════════════════════════════════════════

def _source_class(src: str) -> str:
    """Quelle grob: Fabrik / Grossfabrik / Mondpool. Die Konvention der
    Quellen-Etiketten ist die von `played_key`/`move_key`
    (analyze_game_log.py:303-334): "F1".."F4", "GF", "Mondpool"."""
    if src.startswith("F") and src[1:].isdigit():
        return "factory"
    if src == "GF":
        return "large_factory"
    if src == "Mondpool":
        return "moon_pool"
    return f"other:{src}"


def _dest_class(dest: str) -> str:
    m = _ROW_RE.match(dest)
    return f"row{m.group('row')}" if m else "floor_line"


def move_classes(kind: str, fields: dict, played_desc: str) -> tuple[str, str]:
    """(grobe Klasse, feine Klasse) eines Entscheids.

    Grob, damit bei n rund 600 nicht jede Klasse ein Einzelfall ist; fein
    genau so weit, wie par.10 Punkt 3 es verlangt. Die Rotation steht NUR in
    der feinen Kuppel-Klasse und ist dort beschreibend: das Orakel bewertet
    die Rotationsstufe nicht (analyze_game_log-Modulkopf, Task #89).
    """
    if kind == "stone":
        dest = _dest_class(fields.get("dest", ""))
        coarse = "stone_row" if dest.startswith("row") else "stone_floor_line"
        fine = f"stone|{_source_class(fields.get('src', ''))}|{fields.get('color', '?')}|{dest}"
        return coarse, fine
    if kind in ("dome_display", "dome_stack"):
        m = _ROT_RE.search(played_desc or "")
        rot = m.group("rot") if m else "?"
        slot = f"r{fields.get('r', '?')}c{fields.get('c', '?')}"
        return kind, f"{kind}|slot={slot}|rot{rot}"
    if kind == "dome_stack_peek":
        return "dome_stack_peek", "dome_stack_peek"
    if kind == "bonus_chip":
        return "bonus_chip", f"bonus_chip|F{fields.get('fid', '?')}"
    return f"other:{kind}", f"other:{kind}"


# ═══════════════════════════════════════════════════════════════════════════
# Partien finden, Kopf lesen, Ausgang bestimmen
# ═══════════════════════════════════════════════════════════════════════════

def discover_games(only: list[str] | None) -> list[dict]:
    games = []
    for d in sorted(CLAUDE_PLAY_DIR.iterdir()):
        if not d.is_dir():
            continue
        if d.name in EXCLUDED_GAMES:
            continue
        if not re.fullmatch(r"g\d+", d.name):
            continue
        if only and d.name not in only:
            continue
        # `.engine.log` traegt Kopf und `#a`-Aktions-IDs, `game.log` ab g02
        # nicht mehr -- siehe Modulkopf, Abschnitt WELCHE LOGDATEI.
        engine_log, plain_log = d / ".engine.log", d / "game.log"
        log = engine_log if engine_log.exists() else plain_log
        if not log.exists():
            raise SystemExit(f"{d.name}: weder .engine.log noch game.log vorhanden.")
        manifest_path = d / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
        games.append({"id": d.name, "log": log, "manifest": manifest,
                      "log_datei": log.name})
    if only:
        missing = sorted(set(only) - {g["id"] for g in games})
        if missing:
            raise SystemExit(f"Partien nicht gefunden oder ausgeschlossen: {missing}")
    return games


def claude_index(header: dict, manifest: dict, game_id: str) -> int:
    """Claudes Spielerindex -- aus dem Log-KOPF, gegengeprueft am Manifest.

    Pruefstellen: `load_log` liefert den Kopf (analyze_game_log.py:225-262);
    die Felder `players`/`ai_player` schreibt `tools/claude_play.py` beim
    Anlegen der Partie (Format wie `server.py`). Der Kopf von g06 zeigt die
    Vertauschung, gegen die diese Funktion sichert:
    `players: ["KI","Claude"], ai_player: 0` -- wer hier "Claude ist immer 0"
    annimmt, wertet in g06/g07 die falsche Seite aus.
    """
    players = header.get("players")
    ai_player = header.get("ai_player")
    if not isinstance(players, list) or ai_player is None:
        raise SystemExit(f"{game_id}: Log-Kopf ohne `players`/`ai_player` -- Seite nicht bestimmbar.")
    idx = 1 - int(ai_player)
    if players[idx] != "Claude":
        raise SystemExit(f"{game_id}: players[{idx}] ist {players[idx]!r}, nicht 'Claude' "
                         f"(Kopf: players={players}, ai_player={ai_player}).")
    me = manifest.get("me")
    if me is not None and int(me) != idx:
        raise SystemExit(f"{game_id}: Log-Kopf sagt Claude={idx}, manifest.json sagt me={me}.")
    return idx


def outcome_of(game: dict, header: dict, lines: list, claude_idx: int) -> dict:
    """Partieausgang aus CLAUDES Sicht, aus zwei Quellen, beide benannt.

    Primaer der Logtext: `extract_full_score_timeline` (game_log_report.py)
    liest die `FINAL_SCORE`-Zeilen (🏆 ... Endwertung ... Gesamt) direkt aus
    denselben Zeilen, die auch das Replay gesehen hat -- unabhaengig davon,
    wie weit das Replay kam. Gegenprobe: `manifest.json` Feld
    `result.scores` (Index = Spielerindex). Weichen beide ab, steht das im
    Artefakt und der Ausgang gilt als unsicher.
    """
    players = header["players"]
    timeline = extract_full_score_timeline(lines, players)
    final = timeline.get("final") or {}
    log_scores = None
    if all(p in final for p in players):
        log_scores = [final[players[0]]["score"], final[players[1]]["score"]]
    manifest_scores = (game["manifest"].get("result") or {}).get("scores")

    scores = log_scores or manifest_scores
    source = "log FINAL_SCORE" if log_scores else ("manifest result.scores" if manifest_scores else None)
    sources_agree = (log_scores is not None and manifest_scores is not None
                     and list(log_scores) == list(manifest_scores))
    if scores is None:
        return {"ergebnis": None, "quelle": None, "punkte_claude": None, "punkte_gegner": None,
                "margin": None, "log_scores": log_scores, "manifest_scores": manifest_scores,
                "quellen_einig": None}
    own, opp = scores[claude_idx], scores[1 - claude_idx]
    result = "sieg" if own > opp else ("niederlage" if own < opp else "unentschieden")
    return {"ergebnis": result, "quelle": source, "punkte_claude": own, "punkte_gegner": opp,
            "margin": own - opp, "log_scores": log_scores, "manifest_scores": manifest_scores,
            "quellen_einig": sources_agree}


# ═══════════════════════════════════════════════════════════════════════════
# Standard-Kennzahlen (CLAUDE.md 2026-08-23, sechs Stueck)
# ═══════════════════════════════════════════════════════════════════════════

def standard_metrics(rep, game: dict, header: dict, lines: list, claude_idx: int,
                     outcome: dict, targets: Counter) -> dict:
    """Die sechs Pflicht-Kennzahlen, je Seite, aus denselben Partien.

    Reihen-/Spaltenauslastung aus `score_geo` des replayten Zustands (Zaehlweise
    wie `tools/probes/arena_column_probe.py:97-146`: `col_fill`/`row_fill`,
    voll = 6). Strafleiste aus den Logzeilen (`ROUND_STRAFE`-Strafen,
    `OVERFLOW_PENALTY`-Zeilen) plus den Zugzielen. Plattenpunkte je Kriterium
    aus `manifest.json` `result.end_scoring` (Kriterium-ID -> score); der
    Logtext traegt dieselbe Aufschluesselung als `FINAL_DETAIL`-Zeilen.
    Punkte und Margin aus `outcome_of`.

    Was FEHLT und warum (stilles Weglassen waere ein Regelbruch): bricht das
    Replay vorzeitig ab, sind Reihen-/Spaltenzahlen die des ERREICHTEN
    Zustands, nicht der Endstellung -- `replay_vollstaendig` sagt es je Partie.
    """
    try:
        state = json.loads(rep.g.state_json())
    except Exception as e:  # defensiv: Replay-Abbruch darf den Bericht nicht killen
        state = None
        geo_error = str(e)
    else:
        geo_error = None

    def side(pi: int) -> dict:
        geo = ((state or {}).get("players") or [{}, {}])[pi].get("score_geo") or {} if state else {}
        cols = geo.get("col_fill") or []
        rows = geo.get("row_fill") or []
        return {
            "zeilen_voll": sum(1 for x in rows if x >= 6),
            "zeilen_fuellung": rows,
            "zeilen_fuellung_summe": sum(rows) if rows else None,
            "spalten_voll": sum(1 for x in cols if x >= 6),
            "spalten_max_hoehe": max(cols) if cols else None,
            "spalten_ge4": sum(1 for x in cols if x >= 4),
            "spalten_ge3": sum(1 for x in cols if x >= 3),
            "spezialfelder_belegt": (geo.get("special_total") or 0) - (geo.get("special_empty") or 0),
        }

    players = header["players"]
    penalty_per_round: dict = defaultdict(dict)
    overflow_lines = Counter()
    for line in lines:
        cat, m = agl.classify(line.body)
        if cat == "ROUND_STRAFE":
            penalty_per_round[line.round_num][m.group("name")] = int(m.group("pen"))
        elif cat == "OVERFLOW_PENALTY":
            overflow_lines[m.group("name")] += 1

    end_scoring = (game["manifest"].get("result") or {}).get("end_scoring") or {}
    out = {"replay_vollstaendig": geo_error is None and state is not None,
           "geo_fehler": geo_error, "je_seite": {}}
    for pi, name in enumerate(players):
        role = "claude" if pi == claude_idx else "gegner"
        entry = side(pi)
        entry["strafleiste_summe"] = sum(v.get(name, 0) for v in penalty_per_round.values())
        entry["strafleiste_ueberlaeufe"] = overflow_lines.get(name, 0)
        entry["zugziele"] = dict(sorted(targets.get(pi, Counter()).items())) if targets else {}
        # `end_scoring[<spieler>]` bindet Kriterium-ID -> {name, desc, score}
        # UND zusaetzlich den Schluessel "total" -> Zahl (siehe g02/manifest.json);
        # beide Formen zulassen, statt an "total" zu zerschellen.
        entry["plattenpunkte_je_kriterium"] = {
            kid: (d.get("score") if isinstance(d, dict) else d)
            for kid, d in (end_scoring.get(str(pi)) or {}).items()
        }
        entry["punkte"] = outcome["punkte_claude"] if pi == claude_idx else outcome["punkte_gegner"]
        entry["margin"] = (outcome["margin"] if pi == claude_idx
                           else (-outcome["margin"] if outcome["margin"] is not None else None))
        out["je_seite"][role] = {"name": name, **entry}
    return out


# ═══════════════════════════════════════════════════════════════════════════
# Eine Partie auswerten
# ═══════════════════════════════════════════════════════════════════════════

def analyse_log(log_path: pathlib.Path, model_path: str, sims: int, c_puct: float,
                actor: int | None, max_decisions: int | None, limit_lines: int | None,
                label: str) -> tuple:
    """Ein Replay ueber `analyze_game_log.run` plus die abgegriffenen Felder.

    `run` faengt Divergenzen ab und gibt sie zurueck, statt zu werfen
    (analyze_game_log.py:1119-1130) -- eine abgebrochene Partie kostet also
    nur ihren Rest, nicht den Lauf.
    """
    _reset_filter(actor, max_decisions, label)
    rep, lines, li_reached, divergence = agl.run(
        log_path, model_path, sims, c_puct, True, limit_lines
    )
    if getattr(rep, "dump_fh", None) is not None:
        rep.dump_fh.close()
    return rep, lines, li_reached, divergence, dict(_FILTER["fields"]), dict(_FILTER["actors"])


def decisions_from(rep, fields_by_turn: dict, actor: int | None) -> list[dict]:
    """Die Entscheide EINER Seite als flache Dicts -- die Einheit der Sonde."""
    out = []
    for rec in rep.oracle_records:
        if actor is not None and rec.actor != actor:
            continue
        fields = fields_by_turn.get(rec.turn_idx, {})
        coarse, fine = move_classes(rec.kind, fields, rec.played_desc)
        out.append({
            "turn_idx": rec.turn_idx, "runde": rec.round_num, "akteur": rec.actor,
            "akteur_name": rec.actor_name, "kind": rec.kind,
            "klasse_grob": coarse, "klasse_fein": fine,
            "gespielt": (rec.played_desc or "").strip(),
            "bewertet": rec.evaluated, "grund": rec.reason,
            "num_actions": rec.num_actions, "root_value": rec.root_value,
            "played_rank": rec.played_rank, "played_q": rec.played_q,
            "top_q": rec.top_q, "top_desc": rec.top_desc,
            "delta_win_pct": rec.delta_win_pct,
            "abweichung": bool(rec.evaluated and rec.played_rank is not None and rec.played_rank != 1),
            # Gesucht wurde, aber Claudes Zug lag ausserhalb des Gumbel-
            # Wurzelfensters -- Abweichung ohne Q (siehe CANDIDATE_WINDOW_NOTE).
            "ausserhalb_kandidatenfenster": bool(not rec.evaluated and rec.reason == REASON_OUTSIDE_WINDOW),
            "ambiguous_match": rec.ambiguous_match, "state_exact": rec.state_exact,
        })
    return out


# ═══════════════════════════════════════════════════════════════════════════
# Aggregation (par.10 Punkt 4)
# ═══════════════════════════════════════════════════════════════════════════

def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def aggregate_by(decisions: list[dict], key: str) -> dict:
    """Aggregat je Auspraegung von `key`.

    Grundmenge je Klasse sind die Entscheide, an denen das Orakel WIRKLICH
    gesucht hat: bewertete plus die ausserhalb des Wurzelfensters (siehe
    CANDIDATE_WINDOW_NOTE). Die Wurzelwert-Differenzen mitteln NUR ueber die
    bewerteten -- fuer die anderen gibt es kein played_q, und eine Null
    einzusetzen waere eine erfundene Zahl.
    """
    buckets: dict = defaultdict(list)
    for d in decisions:
        if d["bewertet"] or d["ausserhalb_kandidatenfenster"]:
            buckets[d[key]].append(d)
    out = {}
    for k, group in buckets.items():
        evaluated = [d for d in group if d["bewertet"]]
        deviations = [d for d in evaluated if d["abweichung"]]
        outside = [d for d in group if d["ausserhalb_kandidatenfenster"]]
        outcomes = Counter(d["ausgang"] for d in deviations + outside)
        interesting = [d for d in deviations
                       if (d["delta_win_pct"] or 0) > 0 and d["ausgang"] == "sieg"]
        out[k] = {
            "n_gesucht": len(group),
            "n_bewertet": len(evaluated),
            "ausserhalb_kandidatenfenster": len(outside),
            "abweichungen_mit_q": len(deviations),
            "abweichungen_gesamt": len(deviations) + len(outside),
            "abweichungsrate_gesamt": round((len(deviations) + len(outside)) / len(group), 4) if group else None,
            "abweichungsrate_bewertete": round(len(deviations) / len(evaluated), 4) if evaluated else None,
            "delta_win_pct_mittel_abweichungen": _mean([d["delta_win_pct"] for d in deviations]),
            "delta_win_pct_mittel_bewertete": _mean([d["delta_win_pct"] for d in evaluated]),
            "ausgang_der_abweichungen": dict(outcomes),
            "netz_schlechter_claude_gewinnt": len(interesting),
        }
    return dict(sorted(out.items(), key=lambda kv: -kv[1]["abweichungen_gesamt"]))


def build_ranking(by_fine: dict, by_coarse_of_fine: dict, top: int = 10) -> list:
    """Rangliste Haeufigkeit x Ausgang (par.10 Punkt 4)."""
    rows = []
    for fine, st in list(by_fine.items())[:top]:
        rows.append({
            "klasse_fein": fine,
            "klasse_grob": by_coarse_of_fine.get(fine),
            "n_gesucht": st["n_gesucht"],
            "n_bewertet": st["n_bewertet"],
            "abweichungen_gesamt": st["abweichungen_gesamt"],
            "abweichungen_mit_q": st["abweichungen_mit_q"],
            "ausserhalb_kandidatenfenster": st["ausserhalb_kandidatenfenster"],
            "abweichungsrate_gesamt": st["abweichungsrate_gesamt"],
            "delta_win_pct_mittel": st["delta_win_pct_mittel_abweichungen"],
            "ausgang_der_abweichungen": st["ausgang_der_abweichungen"],
            "netz_schlechter_claude_gewinnt": st["netz_schlechter_claude_gewinnt"],
        })
    return rows


# ═══════════════════════════════════════════════════════════════════════════
# Rauschboden (par.10 Punkt 5)
# ═══════════════════════════════════════════════════════════════════════════

NOISE_DEVIATION_NOTE = (
    "par.10 Punkt 5 verlangt die Netz-gegen-Netz-Partie 'unter Wurzelrauschen'. "
    "Einen solchen Einstieg gibt es im Baum NICHT: der Arena-Pfad, der als einziger "
    "die Logzeilen liefert (`log_games`, engine/src/self_play.rs:4003-4009), waehlt "
    "fest ohne Rauschen (`net_search_drafting_action(..., false, ...)`, "
    "engine/src/self_play.rs:3133; NetArenaAgent hat gar kein Rausch-Feld, :3075-3086). "
    "Der Self-Play-Pfad traegt das Rauschen (`add_root_noise`, engine/src/lib.rs:467), "
    "laeuft aber in LoopMode::Records und liefert kein vollstaendiges Partie-Log "
    "(engine/src/self_play.rs:3233-3241). Gefahren wird darum Champion gegen "
    "Champion im Arena-Instrument: gemessen ist damit der Rauschboden des MESSENS "
    "(Determinisierung mit anderem Seed, Sims-Skalierung, Bauer-Vorzug, Spec) und "
    "NICHT der Dirichlet-/Gumbel-Anteil. Eine Engine-Aenderung waere noetig und "
    "wurde per Auftrag nicht vorgenommen."
)


def run_noise_floor(model_path: str, spec_path: str | None, sims: int, c_puct: float,
                    n_games: int, seed: int, threads: int, oracle_sims: int,
                    oracle_c_puct: float, max_decisions: int | None,
                    log_dir: pathlib.Path) -> dict:
    """Netz gegen sich selbst, danach DIESELBE Auswertung.

    Erzeugt wird ueber `mosaic_rust.net_vs_net_arena_match(..., log_games=True)`
    (engine/src/lib.rs:376-389) -- kein zweiter Partie-Treiber. Das Log wird
    wie in `tools/probes/arena_column_probe.py:80-90` mit dem `# {...}`-Kopf
    aus `names`/`first_player`/`game_seed` versehen und dann durch dasselbe
    `analyze_game_log.run` geschickt wie die Claude-Partien.
    """
    import mosaic_rust

    print(f"Rauschboden: {n_games} Partie(n) Champion gegen Champion @{sims}, "
          f"threads={threads} ...", flush=True)
    t0 = time.time()
    raw = mosaic_rust.net_vs_net_arena_match(
        model_path, model_path, sims, sims, n_games, seed, threads, c_puct, c_puct,
        True, None, spec_path, spec_path,
    )
    games = json.loads(raw)
    print(f"  Partien erzeugt in {time.time() - t0:.0f}s", flush=True)

    log_dir.mkdir(parents=True, exist_ok=True)
    all_decisions: list[dict] = []
    per_game = []
    for idx, g in enumerate(games):
        header = {"players": g.get("names") or ["NetzA", "NetzB"],
                  "first_player": g.get("first_player", 0),
                  "seed": g.get("game_seed", 0)}
        path = log_dir / f"noise_{idx:02d}.log"
        path.write_text("# " + json.dumps(header, ensure_ascii=False) + "\n"
                        + "\n".join(g["log"]) + "\n", encoding="utf-8", newline="\n")
        print(f"  [{idx + 1}/{len(games)}] Rauschboden-Partie {path.name}: "
              f"{len(g['log'])} Zeilen, Orakel laeuft ...", flush=True)
        rep, lines, li, div, fields, _actors = analyse_log(
            path, model_path, oracle_sims, oracle_c_puct, None, max_decisions, None,
            f"rausch {idx + 1}/{len(games)}")
        decisions = decisions_from(rep, fields, None)
        for d in decisions:
            d["ausgang"] = "netz_gegen_netz"
        all_decisions.extend(decisions)
        n_evaluated = sum(1 for d in decisions if d["bewertet"])
        per_game.append({
            "datei": str(path.relative_to(_ROOT)).replace(os.sep, "/"),
            "seed": header["seed"], "zeilen": len(lines), "li_erreicht": li,
            "divergenz": div, "entscheide": len(decisions), "bewertet": n_evaluated,
            "nicht_bewertet": dict(Counter(d["grund"] for d in decisions if not d["bewertet"])),
            "scores": g.get("scores"),
        })
        print(f"  [{idx + 1}/{len(games)}] fertig: {n_evaluated}/{len(decisions)} Entscheide bewertet"
              + (f" -- ABBRUCH: {div}" if div else ""), flush=True)

    evaluated = [d for d in all_decisions if d["bewertet"]]
    deviations = [d for d in evaluated if d["abweichung"]]
    outside = [d for d in all_decisions if d["ausserhalb_kandidatenfenster"]]
    searched = len(evaluated) + len(outside)
    return {
        "abweichung_von_par10": NOISE_DEVIATION_NOTE,
        "erzeugt_mit": "mosaic_rust.net_vs_net_arena_match(log_games=True), argmax, ohne Wurzelrauschen",
        "n": len(evaluated), "grundmenge": "Entscheide beider Netz-Seiten der Rauschboden-Partien",
        "einheit": "Entscheide",
        "n_gesucht": searched,
        "ausserhalb_kandidatenfenster": len(outside),
        "abweichungen_mit_q": len(deviations),
        "abweichungen_gesamt": len(deviations) + len(outside),
        "abweichungsrate_gesamt": round((len(deviations) + len(outside)) / searched, 4) if searched else None,
        "abweichungsrate_bewertete": round(len(deviations) / len(evaluated), 4) if evaluated else None,
        "je_klasse_grob": aggregate_by(all_decisions, "klasse_grob"),
        "je_klasse_fein": aggregate_by(all_decisions, "klasse_fein"),
        "je_runde": aggregate_by(all_decisions, "runde"),
        "je_partie": per_game,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Hauptlauf
# ═══════════════════════════════════════════════════════════════════════════

def resolve_champion(model_arg: str | None, spec_arg: str | None) -> tuple[str, str | None, dict]:
    """Amtierender Champion aus `models/champion.txt` plus eingefrorenes
    Artefakt -- geprueft, nicht geraten (STATUS.md Abschnitt 2)."""
    info = {}
    champ_file = _ROOT / "models" / "champion.txt"
    name = champ_file.read_text(encoding="utf-8").strip() if champ_file.exists() else None
    info["champion_txt"] = name
    frozen_dir = _ROOT / "models" / "frozen_champions" / (name.split("_")[0] if name else "")
    if model_arg:
        model = model_arg
    elif (frozen_dir / "model.onnx").exists():
        model = str(frozen_dir / "model.onnx")
    elif name and (_ROOT / "models" / f"alphazero_{name}.onnx").exists():
        model = str(_ROOT / "models" / f"alphazero_{name}.onnx")
    else:
        raise SystemExit("Champion-Modell nicht gefunden -- --model setzen.")
    if spec_arg == "":
        spec = None
    elif spec_arg:
        spec = spec_arg
    elif (frozen_dir / "spec.json").exists():
        spec = str(frozen_dir / "spec.json")
    else:
        spec = None
    info["eingefrorenes_verzeichnis"] = str(frozen_dir.relative_to(_ROOT)).replace(os.sep, "/") \
        if frozen_dir.exists() else None
    return model, spec, info


SPEC_DEVIATION_NOTE = (
    "par.10 Punkt 2 verlangt den Champion 'mit seinem Arena-Instrument (@400, argmax, "
    "ohne Wurzelrauschen, Champion-Spec)'. Drei der vier Merkmale treffen zu: die Sims "
    "sind gesetzt, die Suche laeuft ohne Wurzelrauschen (`net_search_with_tree(..., "
    "false, ...)`, engine/src/lib.rs:1055) und der gespielte Zug wird gegen den "
    "hoechsten mcts_q gerangt (argmax, analyze_game_log.py:348-358). Die CHAMPION-SPEC "
    "kommt NICHT durch: `net_search_state_json` hat kein Spec-Argument "
    "(Signatur engine/src/lib.rs:1022-1028) und benutzt damit `SearchConfig::from_env()` "
    "-- Spec-Argumente gibt es nur an den Arena-/Self-Play-Einstiegen "
    "(`resolve_search_config`, engine/src/lib.rs:304-311). Das Orakel laeuft also mit "
    "der Umgebungs-Konfiguration statt mit der Champion-Spec. Ein Nachruesten waere "
    "eine ENGINE-Aenderung (neuer Parameter an `net_search_state_json`) und wurde per "
    "Auftrag nicht vorgenommen; die Spec der Partien steht daneben im Artefakt."
)


def main() -> int:
    agl.check_prereqs()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--games", default=None,
                    help="Komma-Liste (Default: alle echten Partien g01-g07)")
    ap.add_argument("--model", default=None, help="Orakel-Modell (Default: amtierender Champion)")
    ap.add_argument("--spec", default=None,
                    help="Champion-Spec, NUR fuer die Rauschboden-Partie (das Orakel kann sie "
                         "nicht nehmen, siehe SPEC_DEVIATION_NOTE); \"\" = keine")
    ap.add_argument("--sims", type=int, default=400, help="Orakel-Sims (par.10: 400)")
    ap.add_argument("--c-puct", type=float, default=1.5)
    ap.add_argument("--max-decisions", type=int, default=None,
                    help="Deckel je Partie (Selbsttest) -- danach nur noch Protokoll, keine Suche. "
                         "0 = reiner Replay-Durchlauf ohne jede Netzsuche (prueft in Sekunden, ob "
                         "alle Logs durchlaufen). Hinweis: scheitert eine Chip-Vollendung, wiederholt "
                         "`analyze_game_log.run` den Replay mit gesuchtem Chip-Plan -- der Zaehler "
                         "laeuft dann weiter, der Deckel greift entsprechend frueher.")
    ap.add_argument("--limit-lines", type=int, default=None,
                    help="nur die ersten N Logzeilen je Partie (Selbsttest; reicht `limit` an "
                         "analyze_game_log.run durch)")
    ap.add_argument("--no-noise-floor", action="store_true", help="Gegenprobe auslassen (Selbsttest)")
    ap.add_argument("--noise-games", type=int, default=1,
                    help="Partien der Gegenprobe (par.10: eine Partie gleicher Laenge)")
    ap.add_argument("--noise-seed", type=int, default=20260914)
    ap.add_argument("--threads", type=int, default=1,
                    help="Threads der Rauschboden-Arena (<=1 = sequenziell bei "
                         "net_vs_net_arena_match)")
    ap.add_argument("--gumbel-top-m", type=int, default=0,
                    help="Wurzelfenster der Orakel-Suche aufbohren (MOSAIC_GUMBEL_TOP_M, "
                         "net_mcts.rs:3188-3200). 0 = Bestandsverhalten m=clamp(sims/16,4,16). "
                         "ACHTUNG: das ist dann nicht mehr das Arena-Instrument aus par.10.")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    # VOR dem ersten Suchaufruf setzen: die Engine liest den Wert EINMAL in
    # ein OnceLock (net_mcts.rs:3194-3200), ein spaeteres Setzen waere wirkungslos.
    if args.gumbel_top_m and args.gumbel_top_m > 0:
        os.environ["MOSAIC_GUMBEL_TOP_M"] = str(args.gumbel_top_m)
        print(f"ACHTUNG: Wurzelfenster auf MOSAIC_GUMBEL_TOP_M={args.gumbel_top_m} gesetzt -- "
              f"abweichend vom Arena-Instrument aus par.10.", flush=True)

    t_wall, t_cpu = time.time(), time.process_time()
    model_path, spec_path, champ_info = resolve_champion(args.model, args.spec)
    only = [s.strip() for s in args.games.split(",")] if args.games else None
    games = discover_games(only)
    _install_oracle_filter()

    print(f"Zugklassen-Differential -- {len(games)} Partie(n), Orakel {model_path} "
          f"@{args.sims} Sims, c_puct {args.c_puct}", flush=True)
    print(f"Prereg: {PREREG}", flush=True)

    all_decisions: list[dict] = []
    per_game = []
    for gi, game in enumerate(games, 1):
        print(f"[{gi}/{len(games)}] {game['id']} ({game['log_datei']}) ...", flush=True)
        header, _lines0, _hints = agl.load_log(game["log"])
        cidx = claude_index(header, game["manifest"], game["id"])
        rep, lines, li, div, fields, _actors = analyse_log(
            game["log"], model_path, args.sims, args.c_puct, cidx, args.max_decisions,
            args.limit_lines, f"{game['id']} ({gi}/{len(games)})")
        outcome = outcome_of(game, header, lines, cidx)

        decisions = decisions_from(rep, fields, cidx)
        for d in decisions:
            d["partie"] = game["id"]
            d["ausgang"] = outcome["ergebnis"]
        all_decisions.extend(decisions)

        # Zugziele BEIDER Seiten (Kennzahl 1 und 3) -- die Felder liegen auch
        # fuer die uebersprungenen Entscheide vor, sie kosten keine Suche.
        targets: dict = defaultdict(Counter)
        for rec in rep.oracle_records:
            f = fields.get(rec.turn_idx, {})
            if rec.kind == "stone":
                targets[rec.actor][_dest_class(f.get("dest", ""))] += 1
            else:
                targets[rec.actor][rec.kind] += 1

        n_evaluated = sum(1 for d in decisions if d["bewertet"])
        skipped = Counter(d["grund"] for d in decisions if not d["bewertet"])
        per_game.append({
            "partie": game["id"], "log_datei": game["log_datei"],
            "gegner": game["manifest"].get("opponent"),
            "gegner_spec": game["manifest"].get("spec"),
            "gegner_sims": game["manifest"].get("sims"),
            "claude_index": cidx, "spielernamen": header["players"],
            "seed": header.get("seed"),
            "zeilen": len(lines), "li_erreicht": li, "divergenz": div,
            "entscheide_claude": len(decisions), "bewertet": n_evaluated,
            "ausserhalb_kandidatenfenster": sum(1 for d in decisions if d["ausserhalb_kandidatenfenster"]),
            "nicht_bewertet": len(decisions) - n_evaluated, "nicht_bewertet_gruende": dict(skipped),
            "ausgang": outcome,
            "standard_kennzahlen": standard_metrics(rep, game, header, lines, cidx, outcome, targets),
        })
        print(f"[{gi}/{len(games)}] {game['id']}: {n_evaluated}/{len(decisions)} Claude-Entscheide "
              f"bewertet, {sum(1 for d in decisions if d['abweichung'])} Abweichungen mit Q, "
              f"{sum(1 for d in decisions if d['ausserhalb_kandidatenfenster'])} ausserhalb des "
              f"Wurzelfensters, Ausgang {outcome['ergebnis']}"
              + (f" -- ABBRUCH: {div}" if div else ""), flush=True)

    evaluated = [d for d in all_decisions if d["bewertet"]]
    deviations = [d for d in evaluated if d["abweichung"]]
    outside = [d for d in all_decisions if d["ausserhalb_kandidatenfenster"]]
    searched = len(evaluated) + len(outside)
    by_fine = aggregate_by(all_decisions, "klasse_fein")
    by_coarse = aggregate_by(all_decisions, "klasse_grob")
    fine_to_coarse = {d["klasse_fein"]: d["klasse_grob"] for d in all_decisions}

    interesting = [
        {"partie": d["partie"], "runde": d["runde"], "klasse_fein": d["klasse_fein"],
         "gespielt": d["gespielt"], "delta_win_pct": d["delta_win_pct"],
         "played_rank": d["played_rank"], "num_actions": d["num_actions"],
         "top_desc": d["top_desc"]}
        for d in deviations if (d["delta_win_pct"] or 0) > 0 and d["ausgang"] == "sieg"
    ]
    interesting.sort(key=lambda x: -(x["delta_win_pct"] or 0))

    noise = None
    if not args.no_noise_floor:
        noise = run_noise_floor(
            model_path, spec_path, args.sims, args.c_puct, args.noise_games,
            args.noise_seed, args.threads, args.sims, args.c_puct, args.max_decisions,
            _ROOT / "evaluations" / "artifacts" / "move_class_differential_noise")

    wall, cpu = time.time() - t_wall, time.process_time() - t_cpu
    n_games_total = len(games) + (args.noise_games if noise else 0)
    out = {
        "prereg": PREREG,
        "n": len(evaluated),
        "grundmenge": ("alle Claude-Entscheide der Partien "
                       + ", ".join(g["id"] for g in games)
                       + " (Drafting, Runden 1-4; Runde 5 laeuft ueber den exakten "
                         "Alpha-Beta-Solver und wird nicht netz-orakelt)"),
        "einheit": "Entscheide",
        "n_gesamt_protokolliert": len(all_decisions),
        "n_gesucht": searched,
        "ausserhalb_kandidatenfenster": len(outside),
        "kandidatenfenster": CANDIDATE_WINDOW_NOTE,
        "abweichungen_mit_q": len(deviations),
        "abweichungen_gesamt": len(deviations) + len(outside),
        "abweichungsrate_gesamt": round((len(deviations) + len(outside)) / searched, 4) if searched else None,
        "abweichungsrate_bewertete": round(len(deviations) / len(evaluated), 4) if evaluated else None,
        "delta_win_pct_mittel_abweichungen": _mean([d["delta_win_pct"] for d in deviations]),
        "orakel": {
            "modell": str(pathlib.Path(model_path)).replace(os.sep, "/"),
            "sims": args.sims, "c_puct": args.c_puct,
            "champion": champ_info,
            "spec_der_rauschboden_partie": spec_path,
            "abweichung_von_par10": SPEC_DEVIATION_NOTE,
        },
        "ausgeschlossene_partien": EXCLUDED_GAMES,
        "abweichungen_von_par10": [
            SPEC_DEVIATION_NOTE,
            NOISE_DEVIATION_NOTE,
            "par.10 Punkt 2 nennt auch Startsetzung und Tiling-Schritte als Entscheide. "
            "`analyze_game_log` orakelt NUR Drafting-Entscheide: `maybe_oracle` steigt bei "
            "jeder anderen Phase aus (analyze_game_log.py:770-773), und die Zweige "
            "START_TILE/TILING_PLACE rufen es gar nicht erst auf (:1196-1199, :1249-1258). "
            "Startsetzung und Tiling sind damit nicht Teil der Grundmenge.",
            "par.10 nennt als Klassenmerkmal auch die Kuppel-ROTATION. Sie steht in der "
            "feinen Klasse, ist dort aber beschreibend: das Orakel bewertet die "
            "Rotationsstufe nicht (Serialisierungs-Naeherung der PendingDomeChoice-"
            "Zwischenzustaende, analyze_game_log-Modulkopf).",
            "par.10 nennt `g*/game.log`. Ab g02 traegt nur `.engine.log` den Kopf und die "
            "`#a`-Aktions-IDs; das Werkzeug nimmt sie und schreibt je Partie mit, welche "
            "Datei gelesen wurde.",
            CANDIDATE_WINDOW_NOTE,
        ],
        "je_klasse_grob": by_coarse,
        "je_klasse_fein": by_fine,
        "je_runde": aggregate_by(all_decisions, "runde"),
        "top10_abweichungsklassen": build_ranking(by_fine, fine_to_coarse, 10),
        "netz_schlechter_claude_gewinnt": {
            "n": len(interesting),
            "anteil_der_abweichungen": round(len(interesting) / len(deviations), 4) if deviations else None,
            "faelle": interesting[:50],
            "lesart": "par.10 Punkt 4: wo das Netz Claudes Zug fuer schlechter haelt und "
                      "Claude die Partie gewinnt, sitzt die Luecke.",
        },
        "rauschboden": noise,
        "je_partie": per_game,
        "entscheide": all_decisions,
        "cli_args": {"argv": sys.argv, "parsed": vars(args)},
        "laufzeit": {
            "wanduhr_s": round(wall, 2),
            "cpu_s": round(cpu, 2),
            "threads": args.threads,
            "s_je_partie": round(wall / n_games_total, 2) if n_games_total else None,
            "s_je_entscheid": round(wall / len(evaluated), 3) if evaluated else None,
        },
    }

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── Konsolen-Zusammenfassung ────────────────────────────────────────────
    print("", flush=True)
    print(f"n = {len(evaluated)} bewertete Entscheide (plus {len(outside)} ausserhalb des "
          f"Wurzelfensters, zusammen {searched} gesucht), Grundmenge Claude-Entscheide "
          f"({', '.join(g['id'] for g in games)}), Einheit Entscheide", flush=True)
    print(f"Abweichungen: {len(deviations)} mit Q (played_rank != 1) + {len(outside)} ohne Q "
          f"= {len(deviations) + len(outside)}"
          + (f" = {100 * (len(deviations) + len(outside)) / searched:.1f} % der gesuchten"
             if searched else ""), flush=True)
    print(f"mittlere Wurzelwert-Differenz der Abweichungen mit Q: "
          f"{out['delta_win_pct_mittel_abweichungen']} pp", flush=True)
    print(f"davon 'Netz haelt es fuer schlechter UND Claude gewinnt': {len(interesting)}", flush=True)
    print("", flush=True)
    print("Top-Abweichungsklassen (fein) -- Abweichungen/gesucht, davon ohne Q:", flush=True)
    for r in out["top10_abweichungsklassen"]:
        print(f"  {r['abweichungen_gesamt']:>3}/{r['n_gesucht']:<3} "
              f"({(r['abweichungsrate_gesamt'] or 0) * 100:5.1f} %, "
              f"{r['ausserhalb_kandidatenfenster']} ohne Q)  "
              f"delta {r['delta_win_pct_mittel']}  {r['klasse_fein']}  "
              f"Ausgang {r['ausgang_der_abweichungen']}", flush=True)
    if noise:
        print("", flush=True)
        print(f"Rauschboden (Netz gegen sich selbst, {noise['n_gesucht']} gesuchte Entscheide): "
              f"Abweichungsrate gesamt {noise['abweichungsrate_gesamt']}, "
              f"davon ausserhalb des Fensters {noise['ausserhalb_kandidatenfenster']}", flush=True)
    print("", flush=True)
    print(f"laufzeit: Wanduhr {wall:.1f}s, CPU {cpu:.1f}s, threads {args.threads}", flush=True)
    print(f"Artefakt: {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
