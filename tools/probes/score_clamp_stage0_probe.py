# -*- coding: utf-8 -*-
"""Stufe 0 zu evaluations/PREREG_score_clamp_incentive.md par.5 (+ par.9).

Misst, wie oft und wie lange ein Spieler auf Punktestand 0 steht, wie viel
Strafe die Null-Klammer dabei schluckt, und wie viele Kuppelstapel-Ziehungen
bei Stand 0 gratis waren. ZWEI Grundmengen, getrennt ausgewiesen:

  (a) Self-Play-Korpus der v27-Erzeugung  data/selfplay_v26-b01-policy_*.pkl
  (b) Mensch-vs-KI-Logs                   static/log/game_*.log

Aufruf (ohne Pipe, ohne Umleitung):

    python -X utf8 -u tools/probes/score_clamp_stage0_probe.py

Optionen: --corpus-glob, --log-glob, --limit-files, --out.

Nur LESEND: laedt Korpusdateien und Logs, spielt nichts nach, baut nichts.

Belegstellen der Regeln, die hier codiert sind (alle in dieser Sitzung
geprueft):
  * Startpunktestand 5                       engine/src/board.rs:301-302
  * Klammer bei 0 und Schattenzaehler        engine/src/board.rs:345-346
  * Kauf zahlt nur, was da ist               engine/src/board.rs:361-363
  * Stapel-Ziehung kostet 1, Zeile mit Stand engine/src/game.rs:174-192
  * Rest geht zurueck IN den Pool (Pool -1)  engine/src/game.rs:277-284
  * Strafzeile nur bei pen < 0               engine/src/game.rs:962-969
  * Endwertung ebenfalls geklammert          engine/src/game.rs:1001
  * Self-Play loest den Stapelzug gesammelt  engine/src/self_play.rs:598-695
    auf: EIN Record je Stapelzug, die
    Einzel-Peeks stehen nur im Log
  * state['log'] ist ein Fenster der letzten serialize.rs:246-250
    30 sichtbaren Zeilen
"""
from __future__ import annotations

import argparse
import glob as globmod
import json
import os
import re
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from corpus_io import load_records  # noqa: E402

START_SCORE = 5

# Log-Zeilenformen (Namen werden je Partie eingesetzt, siehe build_log_patterns).
PEEK_RE = re.compile(
    r"^\U0001F4E6 (?P<name>.+?): (?P<n>\d+)\. Kachel vom Stapel gezogen "
    r"\(Rückseite: \S+\) .1 Pkt → (?P<score>-?\d+) Gesamt$"
)


# ---------------------------------------------------------------- Statistik --

def quantile_nearest_rank(values, q):
    """Oberes Quantil nach nearest-rank (kein Interpolieren)."""
    if not values:
        return None
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, int(-(-len(ordered) * q // 1)) - 1))
    return ordered[idx]


def stat_block(values, grundmenge, einheit):
    """Kennzahlenblock mit n, GRUNDMENGE und EINHEIT (Regel 0, Zusatz 2)."""
    vals = list(values)
    return {
        "n": len(vals),
        "grundmenge": grundmenge,
        "einheit": einheit,
        "median": statistics.median(vals) if vals else None,
        "mittel": (sum(vals) / len(vals)) if vals else None,
        "p90": quantile_nearest_rank(vals, 0.90),
        "max": max(vals) if vals else None,
        "anteil_groesser_null": (sum(1 for v in vals if v > 0) / len(vals)) if vals else None,
    }


def wilson_interval(hits, n, z=1.96):
    """95-%-Wilson-Intervall; bei n=30 ist die Spanne die eigentliche Aussage."""
    if n == 0:
        return (None, None)
    p = hits / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return ((centre - half) / denom, (centre + half) / denom)


def share_block(flags, grundmenge):
    vals = list(flags)
    hits = sum(1 for v in vals if v)
    low, high = wilson_interval(hits, len(vals))
    return {
        "n": len(vals),
        "grundmenge": grundmenge,
        "einheit": "Anteil der Partien",
        "treffer": hits,
        "anteil": (hits / len(vals)) if vals else None,
        "wilson95_unten": low,
        "wilson95_oben": high,
    }


def conditional_block(values, grundmenge, einheit):
    """Dieselbe Groesse, aber nur ueber die Partien, in denen sie > 0 ist."""
    sub = [v for v in values if v > 0]
    block = stat_block(sub, grundmenge + " mit Wert > 0", einheit)
    block["anteil_der_grundmenge"] = (len(sub) / len(list(values))) if values else None
    return block


# ------------------------------------------------------------------ Korpus --

class CorpusGame:
    """Sammelt die Kennzahlen einer Self-Play-Partie ueber ihre Records."""

    def __init__(self, game_id):
        self.game_id = game_id
        self.records = 0
        self.halfmoves = [0, 0]
        self.zero_before = [0, 0]      # Stand VOR dem Halbzug == 0
        self.zero_after = [0, 0]       # Stand NACH dem Halbzug == 0
        self.after_undefined = [0, 0]  # kein Folge-Record in derselben Runde
        self.peeks = [0, 0]
        self.free_peeks = [0, 0]
        self.stack_turns = [0, 0]
        self.stack_turns_at_zero = [0, 0]
        self.log_recon = []
        self.log_gaps = 0
        self.peek_line_mismatch = 0
        self.prev = None               # (player, score_vor, runde)
        self.scores = None
        self.scores_unclamped = None
        self.completed = None
        self.rounds_seen = set()


def merge_log_window(recon, window):
    """Haengt ein 30-Zeilen-Fenster an die Rekonstruktion an.

    Sucht die LAENGSTE Ueberlappung zwischen dem Ende der Rekonstruktion und
    dem Anfang des Fensters. Gibt (neue_zeilen, luecke) zurueck; `luecke` ist
    True, wenn keine Ueberlappung gefunden wurde, obwohl die Rekonstruktion
    nicht leer ist (dann sind Zeilen aus dem Fenster gefallen und die
    Zuordnung ist nicht sicher).
    """
    if not recon:
        recon.extend(window)
        return list(window), False
    max_k = min(len(recon), len(window))
    for k in range(max_k, 0, -1):
        if recon[-k:] == window[:k]:
            new = list(window[k:])
            recon.extend(new)
            return new, False
    recon.extend(window)
    return list(window), True


def attribute_peeks(game, player, score_before, new_lines):
    """Zaehlt die Stapel-Ziehungen, die der vorige Record ausgeloest hat.

    Regel fuer die ZIEHUNGSERKENNUNG im Korpus (dokumentiert im Bericht):
    ein Self-Play-Record traegt den gesammelt aufgeloesten Stapelzug als EINE
    Entscheidung (self_play.rs:598-695), die einzelnen Peeks stehen nur als
    Logzeilen im Zustands-Log des FOLGENDEN Records. Jede solche Zeile nennt
    ihre laufende Nummer im Zug und den Stand danach; der Stand davor kommt
    aus dem Record selbst. Frei ist eine Ziehung genau dann, wenn der Stand
    davor 0 war (apply_paid_cost, board.rs:361-363).
    """
    score = score_before
    in_turn = False
    for line in new_lines:
        m = PEEK_RE.match(strip_round_prefix(line))
        if not m:
            continue
        n = int(m.group("n"))
        if n == 1 or not in_turn:
            in_turn = True
            game.stack_turns[player] += 1
            if score == 0:
                game.stack_turns_at_zero[player] += 1
        game.peeks[player] += 1
        if score == 0:
            game.free_peeks[player] += 1
        score = max(0, score - 1)
        if score != int(m.group("score")):
            game.peek_line_mismatch += 1
            score = int(m.group("score"))


ROUND_PREFIX_RE = re.compile(r"^\[R\d+\] (.*)$")


def strip_round_prefix(line):
    m = ROUND_PREFIX_RE.match(line)
    return m.group(1) if m else line


def feed_corpus_record(game, rec):
    st = rec["state"]
    player = rec["player"]
    scores = [p["score"] for p in st["players"]]
    rnd = st["round"]
    game.records += 1
    game.rounds_seen.add(rnd)

    new_lines, gap = merge_log_window(game.log_recon, st.get("log") or [])
    if gap:
        game.log_gaps += 1
    if game.prev is not None and not gap:
        attribute_peeks(game, game.prev[0], game.prev[1], new_lines)

    if game.prev is not None:
        prev_player, _, prev_round = game.prev
        if prev_round == rnd:
            if scores[prev_player] == 0:
                game.zero_after[prev_player] += 1
        else:
            game.after_undefined[prev_player] += 1

    game.halfmoves[player] += 1
    if scores[player] == 0:
        game.zero_before[player] += 1

    game.prev = (player, scores[player], rnd)
    game.scores = rec.get("scores")
    game.scores_unclamped = rec.get("scores_unclamped")
    game.completed = rec.get("completed")


def finish_corpus_game(game):
    if game.prev is not None:
        game.after_undefined[game.prev[0]] += 1


def analyze_corpus(paths):
    games = {}
    order = []
    t0 = time.time()
    for i, path in enumerate(paths, 1):
        recs = load_records(path)
        for rec in recs:
            gid = rec["game_id"]
            g = games.get(gid)
            if g is None:
                g = CorpusGame(gid)
                games[gid] = g
                order.append(gid)
            feed_corpus_record(g, rec)
        if i % 10 == 0 or i == len(paths):
            print(f"  Korpus: {i}/{len(paths)} Dateien, {len(games)} Partien, "
                  f"{time.time() - t0:.0f}s", flush=True)
    for g in games.values():
        finish_corpus_game(g)
    return [games[gid] for gid in order]


# -------------------------------------------------------------- Mensch-Logs --

class LogGame:
    def __init__(self, path, header):
        self.path = path
        self.header = header
        self.names = header["players"]
        self.ai_player = header.get("ai_player")
        self.score = [START_SCORE, START_SCORE]
        self.swallowed = [0, 0]
        self.halfmoves = [[], []]      # (stand_vor, stand_nach) je Halbzug
        self.peeks = [0, 0]
        self.free_peeks = [0, 0]
        self.stack_turns = [0, 0]
        self.stack_turns_at_zero = [0, 0]
        self.peek_lines = [0, 0]
        self.anchor_mismatch = 0
        self.final_seen = [False, False]
        self.pending = None            # (player, stand_vor)
        self.stack_turn_open = [False, False]

    @property
    def completed(self):
        return all(self.final_seen)


def build_log_patterns(names):
    """Regexe je Partie, mit den beiden echten Spielernamen bestueckt."""
    alternation = "|".join(re.escape(n) for n in names)
    n = f"(?P<name>{alternation})"
    return {
        "peek": re.compile(
            rf"^\U0001F4E6 {n}: (?P<num>\d+)\. Kachel vom Stapel gezogen "
            rf"\(Rückseite: \S+\) .1 Pkt → (?P<score>-?\d+) Gesamt$"),
        "tiling_points": re.compile(rf"^\U0001F3AF {n}: \+(?P<pts>\d+) Pkt "),
        "special_points": re.compile(rf"^⭐ {n}: \+(?P<pts>\d+) Spezial-Punkte"),
        "floor_penalty": re.compile(
            rf"^{n}: Strafe (?P<pen>-?\d+) Pkt → (?P<score>-?\d+) Gesamt$"),
        "final_scoring": re.compile(
            rf"^\U0001F3C6 {n}: Endwertung (?P<total>-?\d+) Pkt → Gesamt: (?P<score>\d+) Pkt$"),
        "stone_take": re.compile(rf"^(?:☀️|\U0001F319)\s*{n}: \d+"),
        "chip_take": re.compile(rf"^{n}: Bonusplättchen von Fabrik "),
        "dome_place": re.compile(rf"^{n}: Kachel \d+ → Slot "),
        "start_tile": re.compile(rf"^{n}: Startkachel "),
        "tiling_place": re.compile(rf"^{n}: \S+ → Slot \(\d+,\d+\) Space "),
        "pass": re.compile(rf"^⏭️\s*{n}: passt$"),
        "chips_complete": re.compile(rf"^[\U0001F3AB\U0001F3B4] {n} komplettiert Reihe "),
    }


HALFMOVE_KEYS = ("stone_take", "chip_take", "dome_place", "start_tile",
                 "tiling_place", "pass", "chips_complete")


def close_halfmove(g):
    if g.pending is not None:
        player, before = g.pending
        g.halfmoves[player].append((before, g.score[player]))
        g.pending = None


def open_halfmove(g, player):
    close_halfmove(g)
    g.pending = (player, g.score[player])


def analyze_human_log(path):
    with open(path, "r", encoding="utf-8") as fh:
        raw_lines = fh.read().splitlines()
    header = None
    for line in raw_lines[:5]:
        if line.startswith("# {"):
            header = json.loads(line[2:])
            break
    if header is None:
        return None
    g = LogGame(path, header)
    pat = build_log_patterns(g.names)
    idx = {name: i for i, name in enumerate(g.names)}

    for raw in raw_lines:
        if raw.startswith("#"):
            continue
        body = strip_round_prefix(raw)
        if not body:
            continue

        m = pat["peek"].match(body)
        if m:
            p = idx[m.group("name")]
            before = g.score[p]
            if int(m.group("num")) == 1 or not g.stack_turn_open[p]:
                open_halfmove(g, p)
                g.stack_turn_open[p] = True
                g.stack_turns[p] += 1
                if before == 0:
                    g.stack_turns_at_zero[p] += 1
            g.peeks[p] += 1
            if before == 0:
                g.free_peeks[p] += 1
            g.score[p] = max(0, before - 1)
            if g.score[p] != int(m.group("score")):
                g.anchor_mismatch += 1
                g.score[p] = int(m.group("score"))
            continue

        m = pat["tiling_points"].match(body)
        if m:
            g.score[idx[m.group("name")]] += int(m.group("pts"))
            continue

        m = pat["special_points"].match(body)
        if m:
            g.score[idx[m.group("name")]] += int(m.group("pts"))
            continue

        m = pat["floor_penalty"].match(body)
        if m:
            close_halfmove(g)
            p = idx[m.group("name")]
            raw_score = g.score[p] + int(m.group("pen"))
            if raw_score < 0:
                g.swallowed[p] += -raw_score
            g.score[p] = max(0, raw_score)
            if g.score[p] != int(m.group("score")):
                g.anchor_mismatch += 1
                g.score[p] = int(m.group("score"))
            continue

        m = pat["final_scoring"].match(body)
        if m:
            close_halfmove(g)
            p = idx[m.group("name")]
            raw_score = g.score[p] + int(m.group("total"))
            if raw_score < 0:
                g.swallowed[p] += -raw_score
            g.score[p] = max(0, raw_score)
            g.final_seen[p] = True
            if g.score[p] != int(m.group("score")):
                g.anchor_mismatch += 1
                g.score[p] = int(m.group("score"))
            continue

        if body.startswith("Runde ") or body == "Das Spiel ist beendet!" \
                or body == "Tiling-Phase beginnt.":
            close_halfmove(g)
            continue

        hit = False
        for key in HALFMOVE_KEYS:
            m = pat[key].match(body)
            if m:
                p = idx[m.group("name")]
                # Die Kuppel-Platzierung, die einen Stapelzug abschliesst,
                # eroeffnet KEINEN neuen Halbzug -- der Zug zaehlt einmal
                # (so wie der Korpus ihn als EINEN Record fuehrt).
                if key == "dome_place" and g.stack_turn_open[p]:
                    g.stack_turn_open[p] = False
                else:
                    open_halfmove(g, p)
                hit = True
                break
        if hit:
            continue
    close_halfmove(g)
    return g


# ------------------------------------------------------------ Auswertungen --

def summarize_corpus(games, side_names):
    complete = [g for g in games if g.completed is not False]
    out = {
        "n_partien": len(games),
        "n_partien_completed_true": sum(1 for g in games if g.completed is True),
        "n_partien_ausflug_x1": sum(1 for g in games if g.game_id.endswith("_x1")),
        "log_luecken_partien": sum(1 for g in games if g.log_gaps),
        "log_luecken_summe": sum(g.log_gaps for g in games),
        "peek_zeilen_widerspruch": sum(g.peek_line_mismatch for g in games),
        "halbzuege_je_partie_beide": stat_block(
            [sum(g.halfmoves) for g in complete],
            "Partien des Self-Play-Korpus", "Records (Halbzuege beider Spieler)"),
        "seiten": {},
    }
    for s, name in enumerate(side_names):
        side = {
            "k1_anteil_partien_mit_halbzug_bei_0_nach": share_block(
                [g.zero_after[s] > 0 for g in complete], "Partien des Self-Play-Korpus"),
            "k1_anteil_partien_mit_halbzug_bei_0_vor": share_block(
                [g.zero_before[s] > 0 for g in complete], "Partien des Self-Play-Korpus"),
            "k2_halbzuege_bei_0_je_partie_nach": stat_block(
                [g.zero_after[s] for g in complete],
                "Partien des Self-Play-Korpus", "Halbzuege dieser Seite je Partie"),
            "k2_halbzuege_bei_0_je_partie_vor": stat_block(
                [g.zero_before[s] for g in complete],
                "Partien des Self-Play-Korpus", "Halbzuege dieser Seite je Partie"),
            "halbzuege_gesamt_je_partie": stat_block(
                [g.halfmoves[s] for g in complete],
                "Partien des Self-Play-Korpus", "Halbzuege dieser Seite je Partie"),
            "k3_geschluckte_strafe": stat_block(
                [g.scores[s] - g.scores_unclamped[s] for g in complete
                 if g.scores and g.scores_unclamped],
                "Partien des Self-Play-Korpus", "Punkte je Partie"),
            "k2_halbzuege_bei_0_bedingt": conditional_block(
                [g.zero_after[s] for g in complete],
                "Partien des Self-Play-Korpus", "Halbzuege dieser Seite je Partie"),
            "k3_geschluckte_strafe_bedingt": conditional_block(
                [g.scores[s] - g.scores_unclamped[s] for g in complete
                 if g.scores and g.scores_unclamped],
                "Partien des Self-Play-Korpus", "Punkte je Partie"),
            "k4_gratis_ziehungen_bedingt": conditional_block(
                [g.free_peeks[s] for g in complete],
                "Partien des Self-Play-Korpus", "Ziehungen je Partie"),
            "k4_stapelzuege_bei_0_je_partie": stat_block(
                [g.stack_turns_at_zero[s] for g in complete],
                "Partien des Self-Play-Korpus", "Stapelzuege je Partie"),
            "k4_gratis_ziehungen_je_partie": stat_block(
                [g.free_peeks[s] for g in complete],
                "Partien des Self-Play-Korpus", "Ziehungen je Partie"),
            "stapelzuege_gesamt_je_partie": stat_block(
                [g.stack_turns[s] for g in complete],
                "Partien des Self-Play-Korpus", "Stapelzuege je Partie"),
            "ziehungen_gesamt_je_partie": stat_block(
                [g.peeks[s] for g in complete],
                "Partien des Self-Play-Korpus", "Ziehungen je Partie"),
            "halbzuege_ohne_nachfolger": sum(g.after_undefined[s] for g in complete),
        }
        out["seiten"][name] = side
    out["k2_halbzuege_bei_0_je_partie_beide_seiten"] = stat_block(
        [g.zero_after[0] + g.zero_after[1] for g in complete],
        "Partien des Self-Play-Korpus", "Halbzuege beider Spieler je Partie")
    return out


def summarize_logs(games, side_names):
    complete = [g for g in games if g.completed]
    out = {
        "n_logdateien": len(games),
        "n_partien_vollstaendig": len(complete),
        "unvollstaendig": [os.path.basename(g.path) for g in games if not g.completed],
        "anker_widersprueche": sum(g.anchor_mismatch for g in games),
        "halbzuege_je_partie_beide": stat_block(
            [len(g.halfmoves[0]) + len(g.halfmoves[1]) for g in complete],
            "Mensch-vs-KI-Partien", "Halbzuege beider Spieler je Partie"),
        "seiten": {},
    }
    for s, name in enumerate(side_names):
        zero_after = [sum(1 for (_, a) in g.halfmoves[s] if a == 0) for g in complete]
        zero_before = [sum(1 for (b, _) in g.halfmoves[s] if b == 0) for g in complete]
        out["seiten"][name] = {
            "k1_anteil_partien_mit_halbzug_bei_0_nach": share_block(
                [z > 0 for z in zero_after], "Mensch-vs-KI-Partien"),
            "k1_anteil_partien_mit_halbzug_bei_0_vor": share_block(
                [z > 0 for z in zero_before], "Mensch-vs-KI-Partien"),
            "k2_halbzuege_bei_0_je_partie_nach": stat_block(
                zero_after, "Mensch-vs-KI-Partien", "Halbzuege dieser Seite je Partie"),
            "k2_halbzuege_bei_0_je_partie_vor": stat_block(
                zero_before, "Mensch-vs-KI-Partien", "Halbzuege dieser Seite je Partie"),
            "halbzuege_gesamt_je_partie": stat_block(
                [len(g.halfmoves[s]) for g in complete],
                "Mensch-vs-KI-Partien", "Halbzuege dieser Seite je Partie"),
            "k3_geschluckte_strafe": stat_block(
                [g.swallowed[s] for g in complete],
                "Mensch-vs-KI-Partien", "Punkte je Partie"),
            "k2_halbzuege_bei_0_bedingt": conditional_block(
                zero_after, "Mensch-vs-KI-Partien", "Halbzuege dieser Seite je Partie"),
            "k3_geschluckte_strafe_bedingt": conditional_block(
                [g.swallowed[s] for g in complete],
                "Mensch-vs-KI-Partien", "Punkte je Partie"),
            "k4_gratis_ziehungen_bedingt": conditional_block(
                [g.free_peeks[s] for g in complete],
                "Mensch-vs-KI-Partien", "Ziehungen je Partie"),
            "k4_stapelzuege_bei_0_je_partie": stat_block(
                [g.stack_turns_at_zero[s] for g in complete],
                "Mensch-vs-KI-Partien", "Stapelzuege je Partie"),
            "k4_gratis_ziehungen_je_partie": stat_block(
                [g.free_peeks[s] for g in complete],
                "Mensch-vs-KI-Partien", "Ziehungen je Partie"),
            "stapelzuege_gesamt_je_partie": stat_block(
                [g.stack_turns[s] for g in complete],
                "Mensch-vs-KI-Partien", "Stapelzuege je Partie"),
            "ziehungen_gesamt_je_partie": stat_block(
                [g.peeks[s] for g in complete],
                "Mensch-vs-KI-Partien", "Ziehungen je Partie"),
        }
    out["k2_halbzuege_bei_0_je_partie_beide_seiten"] = stat_block(
        [sum(1 for s in (0, 1) for (_, a) in g.halfmoves[s] if a == 0) for g in complete],
        "Mensch-vs-KI-Partien", "Halbzuege beider Spieler je Partie")
    out["endstaende"] = [
        {"datei": os.path.basename(g.path), "score": g.score,
         "geschluckt": g.swallowed, "gratis_ziehungen": g.free_peeks}
        for g in complete
    ]
    return out


def verdict(summary, side_names):
    """Vorregistrierte Schwelle par.5: (1) < 5 % UND (3) Median < 3 Punkte."""
    per_side = {}
    for name in side_names:
        side = summary["seiten"][name]
        k1 = side["k1_anteil_partien_mit_halbzug_bei_0_nach"]["anteil"]
        k3 = side["k3_geschluckte_strafe"]["median"]
        per_side[name] = {
            "k1_anteil": k1,
            "k3_median": k3,
            "k1_unter_5_prozent": (k1 is not None and k1 < 0.05),
            "k3_median_unter_3": (k3 is not None and k3 < 3),
        }
    beide = all(v["k1_unter_5_prozent"] and v["k3_median_unter_3"] for v in per_side.values())
    return {
        "je_seite": per_side,
        "schwelle_unterschritten_alle_seiten": beide,
        "lesart": "UEBERHOLT nur, wenn BEIDE Grundmengen unterschreiten (par.9 Punkt 1).",
    }


# ------------------------------------------------------------------- Main ----

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus-glob", default="data/selfplay_v26-b01-policy_*.pkl")
    ap.add_argument("--log-glob", default="static/log/game_*.log")
    ap.add_argument("--limit-files", type=int, default=None)
    ap.add_argument("--out", default="evaluations/artifacts/score_clamp_stage0.json")
    args = ap.parse_args()

    wall_start = time.time()
    cpu_start = time.process_time()

    corpus_paths = sorted(globmod.glob(str(ROOT / args.corpus_glob)))
    if args.limit_files:
        corpus_paths = corpus_paths[:args.limit_files]
    log_paths = sorted(globmod.glob(str(ROOT / args.log_glob)))
    print(f"Korpusdateien: {len(corpus_paths)} | Logdateien: {len(log_paths)}", flush=True)

    corpus_games = analyze_corpus(corpus_paths)
    print(f"Korpus fertig: {len(corpus_games)} Partien", flush=True)

    log_games = []
    for i, p in enumerate(log_paths, 1):
        g = analyze_human_log(p)
        if g is not None:
            log_games.append(g)
        print(f"  Log {i}/{len(log_paths)}: {os.path.basename(p)}", flush=True)

    corpus_summary = summarize_corpus(corpus_games, ["spieler_0", "spieler_1"])
    # Mensch-Logs: Index 0 ist in allen Kopfzeilen der Mensch, Index 1 die KI
    # (ai_player == 1); wird unten geprueft.
    ai_players = sorted({g.ai_player for g in log_games})
    log_summary = summarize_logs(log_games, ["mensch", "netz_ki"])
    log_summary["ai_player_indizes_im_kopf"] = ai_players

    result = {
        "prereg": "evaluations/PREREG_score_clamp_incentive.md par.5 (Berichtigungen par.9)",
        "erzeugt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "aufruf": "python -X utf8 -u tools/probes/score_clamp_stage0_probe.py",
        "regeln": {
            "startpunktestand": START_SCORE,
            "halbzug_korpus": "ein Self-Play-Record (Drafting + Tiling); ein "
                              "gesammelt aufgeloester Stapelzug ist EIN Record "
                              "(self_play.rs:598-695)",
            "halbzug_log": "eine geloggte Aktionszeile; ein Stapelzug (n "
                           "Ziehungszeilen + zugehoerige Kuppel-Platzierung) "
                           "zaehlt als EIN Halbzug",
            "ziehungserkennung_korpus": "Ziehungszeilen (Emoji-Paket) aus dem "
                                        "Zustands-Log des FOLGENDEN Records, dem "
                                        "Akteur des vorigen Records zugeordnet; "
                                        "Stand davor aus dem Record, Stand danach "
                                        "aus der Zeile gegengeprueft",
            "ziehungserkennung_log": "Ziehungszeile mit Stand davor == 0",
            "geschluckte_strafe_korpus": "scores[s] - scores_unclamped[s], einmal je Partie",
            "geschluckte_strafe_log": "Summe der Klammer-Ereignisse aus Strafzeilen "
                                      "und Endwertungszeile",
        },
        "korpus": corpus_summary,
        "mensch_logs": log_summary,
        "verdikt": {
            "korpus": verdict(corpus_summary, ["spieler_0", "spieler_1"]),
            "mensch_logs": verdict(log_summary, ["mensch", "netz_ki"]),
        },
    }

    n_games = corpus_summary["n_partien"] + log_summary["n_partien_vollstaendig"]
    wall = time.time() - wall_start
    cpu = time.process_time() - cpu_start
    result["laufzeit"] = {
        "wanduhr_s": round(wall, 1),
        "cpu_s": round(cpu, 1),
        "threads": 1,
        "s_je_partie": round(wall / n_games, 4) if n_games else None,
    }

    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print(f"Artefakt: {out_path}", flush=True)
    print(json.dumps(result["verdikt"], ensure_ascii=False, indent=2), flush=True)
    print(json.dumps(result["laufzeit"], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
