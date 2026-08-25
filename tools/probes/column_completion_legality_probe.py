# -*- coding: utf-8 -*-
"""
Legalitaets-Stufe der Vollendungs-Sonde (Auftrag 2026-08-23,
`evaluations/PREREG_r5_solver_split.md` par.3d letzter Punkt): baut auf
`tools/probes/column_completion_gap_probe.py` auf (0,55 Hoehe-5-Spalten je
Partie bleiben stehen, ~15% Vollendungsquote, ~3,3 Zuege Restfenster) und
beantwortet die dort offen gelassene Frage: war die fehlende Zelle im
Restfenster ueberhaupt LEGAL belegbar?

QUARANTAENE (par.3d, zwingend, EINGEHALTEN): Zustandsrekonstruktion
ausschliesslich ueber den REPLAY-EXAKTEN Pfad
(`PREREG_action_id_logging.md`-Muster, `tools/analyze_game_log.py::Replayer`
-- treibt eine ECHTE `mosaic_rust.PyGame`-Instanz Zug fuer Zug ueber
validierte `apply_*`-Aufrufe, mit exakter Log-Zeilen-Gegenprobe). NIE der
Referee-/Worker-Pfad (`engine/src/referee.rs`, `tools/frozen_*_worker.py`)
-- der traegt laut `PREREG_agent_encapsulation.md` par.8d bis zum gruenen
Kernbeweis keine Messungen (Kernbeweis Stand 2026-08-23: WEITER ROT).

ARENA-JSON-ADAPTER (eigene, hier dokumentierte Konstruktion -- kein Eingriff
in `tools/analyze_game_log.py`): Arena-Partie-Objekte
(`evaluations/paired_arena_*.json`, Feld `games[i]["log"]`) tragen dieselbe
`[Rn] ...`-Zeilenform wie `static/log/game_*.log`-Dateien, aber KEINE
`# {...}`-Kopfzeile und KEINE `#a`-Aktions-ID-Hinweiszeilen (GEPRUEFT
2026-08-23 an `evaluations/paired_arena_env_imm_netvnet.json`: 0 `#`-Zeilen
im `log`-Feld -- bestaetigt `PREREG_action_id_logging.md` par.7.7 "Arena-Logs
... tragen daher keine #a-Zeilen"). `Replayer.__init__` braucht aus einem
Kopf-Dict nur `players`/`first_player`/`seed` (gelesen, `analyze_game_log.py`
Zeilen 364-393) -- diese liegen im Arena-JSON bereits direkt als
`names`/`first_player`/`game_seed`. Der Adapter baut also `header`/`lines`
in exakt der Form, die `load_log()` aus einer Datei bauen wuerde (gleiche
Skip-Regel fuer `#`-Zeilen, gleiches `ROUND_PREFIX`-Matching), OHNE den
Datei-Umweg -- `Replayer`/`_run_loop` selbst bleiben unveraendert importiert,
kein Fork, keine Kopie der Replay-Logik.

GEMESSENE GRENZE DES REPLAY-PFADS (eigener Befund 2026-08-23, VOR dem
Hauptlauf an 30 Partien gegengeprobt): ~20% der Arena-Partien brechen NICHT
mit einer sauberen `ReplayDivergence`, sondern mit einer UNGEFANGENEN
`ValueError("Reihe N nicht mit Chips komplettierbar")` aus
`Replayer.maybe_silent_chip_complete` (analyze_game_log.py:543) ab -- ein
vorbestehender, dokumentierter Luecken-Fall der "stillen Chip-Vervollstaen-
digung" (Kommentar dort: Ursache ist eine Logging-Asymmetrie zwischen
Mensch- und KI-Tiling-Pfad), der beim Bau von `PREREG_action_id_logging.md`
nur an MENSCH-Partien gegengeprobt wurde. Dieses Werkzeug faengt BEIDE
Fehlerarten (nicht nur `ReplayDivergence`), zaehlt sie getrennt aus und
schliesst betroffene Partien aus der Legalitaets-Stichprobe aus -- KEIN
Ausweichen auf einen anderen Rekonstruktionspfad (das waere die Quarantaene-
Verletzung). Die Erfolgsquote wird im Artefakt UND im Bericht ausgewiesen.

LEGALITAETS-PRUEFUNG (je Hoehe-5-Ereignis mit `vollendet=False`, je Zug im
Restfenster): die exakte Zielzelle (slot_row, slot_col, space_index) wird
aus dem ECHTEN `dome_grid`-JSON gelesen (`engine/src/serialize.rs:82-107`,
"Legalitaets-Stufe"-Recherche 2026-08-23 verifiziert). Die dazu passende
`pattern_row` ist durch die Zielzelle EINDEUTIG bestimmt
(`round_end.rs::validate_tiling_action`, `slot_row = pattern_row // 2`,
`space_index`-Paritaet <-> `pattern_row % 2`, siehe Recherche): pro Zielzelle
gibt es GENAU einen Kandidaten, `pattern_row = 2*slot_row + (0 wenn
space_index<2 sonst 1)`. Legalitaet wird NICHT aus dem Regelwerk abgeleitet,
sondern am ECHTEN Motor geprueft: ein Klon des Spielzustands
(`mosaic_rust.PyGame`, neu aus `action_log`-Praefix nachgespielt, wie
`Replayer._fresh_game()`) versucht `apply_tiling(player, pattern_row,
slot_row, slot_col, space_index)` -- Erfolg/Fehler kommt direkt von
`round_end::validate_tiling_action`. Der Klon wird NIE auf die echte
Replay-Instanz zurueckgeschrieben (kein Seiteneffekt auf die Hauptspur).

Blockadegruende werden NUR aus direkt ablesbaren Zustandsfeldern klassifi-
ziert (Musterreihe voll?, Musterreihen-Farbe vs. Zielfeld-Farbe, Zielfeld-
Typ) -- alles darueber hinaus (z.B. eine Reihenfolge-/Prioritaetsregel
zwischen mehreren offenen Reihen) faellt unklassifiziert in
"sonstiger_engine_einwand" mit der rohen Fehlermeldung, STATT geraten zu
werden (Regel 0).

Aufruf:
    python tools/probes/column_completion_legality_probe.py --out evaluations/column_completion_legality_probe.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "probes"))

import mosaic_rust  # noqa: E402

from analyze_game_log import (  # noqa: E402
    Replayer, ReplayDivergence, LogLine, ROUND_PREFIX, _run_loop, check_prereqs,
)
from plate_points_from_arena import game_list  # noqa: E402
from column_completion_gap_probe import (  # noqa: E402
    reconstruct_game_sequence, hoehe5_ereignisse, QUELLEN, K1_TILE_ID,
)

EVAL = ROOT / "evaluations"
OUT_JSON = EVAL / "artifacts" / "column_completion_legality_probe.json"


# ── Arena-JSON -> Replayer-Adapter (siehe Moduldoku) ────────────────────────

def lines_from_arena_log(log: list) -> list:
    lines = []
    for raw in log or []:
        if raw.startswith("#"):
            continue  # keine #a-Hinweise in Arena-Logs (par.7.7), Guard trotzdem vorhanden
        m = ROUND_PREFIX.match(raw)
        if not m:
            continue
        lines.append(LogLine(int(m.group(1)), raw, m.group(2)))
    return lines


def replay_arena_game(sp: dict):
    """Gibt (rep, lines, li_reached, fehlerart, fehlertext) zurueck.
    `fehlerart` in {None, 'divergence', 'exception'} -- siehe Moduldoku zur
    gemessenen ~20%-Ausfallquote durch die vorbestehende
    `maybe_silent_chip_complete`-Luecke (KEIN Ausweichen, nur Zaehlung)."""
    lines = lines_from_arena_log(sp.get("log") or [])
    header = {"players": list(sp["names"]), "first_player": sp["first_player"], "seed": sp["game_seed"]}
    rep = Replayer(header, f"arena_seed{sp.get('game_seed')}", "", 1, 1.5, False)
    rep.hints = {}
    try:
        li = _run_loop(rep, lines, rep.name_to_idx, len(lines), False, time.time())
        if li != len(lines):
            return rep, lines, li, "divergence", f"unvollstaendig: {li}/{len(lines)}"
        return rep, lines, li, None, None
    except ReplayDivergence as e:
        return rep, lines, 0, "divergence", str(e)
    except Exception as e:  # noqa: BLE001 -- siehe Moduldoku: bewusst NICHT nur ReplayDivergence
        return rep, lines, 0, "exception", f"{type(e).__name__}: {e}"


# ── Nachspielen des validierten action_log (fuer echte Zustaende/Klone) ─────

def replay_prefix(players: tuple, first_player: int, seed: int, action_log: list, k: int):
    g = mosaic_rust.PyGame((players[0], players[1]), first_player, seed)
    for method, args, kwargs in action_log[:k]:
        getattr(g, method)(*args, **kwargs)
    return g


def index_tiling_calls(players: tuple, first_player: int, seed: int, action_log: list):
    """EIN Vorwaertslauf durch `action_log` (frische Instanz): sammelt je
    Spieler die geordnete Liste der `apply_tiling`-Aufrufe mit dem
    `action_log`-Index UNMITTELBAR VOR dem jeweiligen Aufruf (der Praefix bis
    dorthin reproduziert exakt den Zustand vor diesem Zug, siehe
    `replay_prefix`). Gibt zusaetzlich den finalen Zustand zurueck."""
    g = mosaic_rust.PyGame((players[0], players[1]), first_player, seed)
    tiling_calls = defaultdict(list)
    for idx, (method, args, kwargs) in enumerate(action_log):
        if method == "apply_tiling":
            tiling_calls[args[0]].append({"global_index_before": idx, "args": args})
        getattr(g, method)(*args, **kwargs)
    final_state = json.loads(g.state_json())
    return tiling_calls, final_state


def state_before_tiling_call(players, first_player, seed, action_log, tiling_calls, player, call_idx, final_state):
    """Zustand (als geparstes JSON) unmittelbar NACH dem `call_idx`-ten
    `apply_tiling`-Aufruf von `player` -- das ist der Zustand VOR dessen
    NAECHSTEM Tiling-Zug (bzw. der finale Zustand, wenn es der letzte war)."""
    calls = tiling_calls[player]
    if call_idx + 1 < len(calls):
        idx_before = calls[call_idx + 1]["global_index_before"]
        g = replay_prefix(players, first_player, seed, action_log, idx_before)
        return json.loads(g.state_json())
    return final_state


# ── Zielzelle einer Hoehe-5-Spalte ───────────────────────────────────────────

def find_empty_cell_in_column(state: dict, player: int, column: int):
    """`column = 2*slot_col + (space_index % 2)`, siehe
    `column_completion_gap_probe.py::fill_level_from_sequence`. Iteriert die
    (bis zu) 6 Zellen dieser Spalte im ECHTEN `dome_grid`-JSON und gibt die
    LEERE zurueck (erwartet genau eine bei Fuellstand 5). `None`, wenn
    keine/mehr als eine leer ist (Konsistenzbruch -- wird vom Aufrufer
    gezaehlt, nicht stillschweigend uebersprungen)."""
    slot_col = column // 2
    parity = column % 2
    dome_grid = state["players"][player]["dome_grid"]
    empties = []
    for slot_row in range(3):
        slot = dome_grid[slot_row][slot_col]
        if slot is None:
            continue
        for space_index in (parity, parity + 2):
            space = slot["spaces"][space_index]
            if space["filled"] is None:
                empties.append((slot_row, slot_col, space_index, space))
    return empties


def pattern_row_for_cell(slot_row: int, space_index: int) -> int:
    return 2 * slot_row + (0 if space_index < 2 else 1)


def classify_blocker(before_state: dict, player: int, pattern_row: int, space: dict, error_msg: str) -> str:
    row = before_state["players"][player]["pattern_lines"][pattern_row]
    row_complete = len(row["tiles"]) == row["capacity"]
    row_color = row["color"]
    space_type = space["type"]
    space_color = space["color"]
    if space_type == "SPECIAL":
        return "zielfeld_ist_spezialfeld_nur_ueber_sibling_slot"
    if not row_complete:
        return "musterreihe_noch_nicht_voll"
    if space_type == "NORMAL" and space_color is not None and row_color != space_color:
        return "keine_passende_farbe_verfuegbar"
    return f"sonstiger_engine_einwand: {error_msg}"


# ── Je Hoehe-5-Ereignis: Legalitaet im Restfenster pruefen ──────────────────

def check_event_legality(players, first_player, seed, action_log, tiling_calls, final_state,
                          player: int, event: dict, sequenz_len: int):
    """`event` = ein Eintrag aus `hoehe5_ereignisse(sequenz[name])` mit
    `vollendet=False`. Gibt ein Ergebnis-Dict zurueck."""
    ev_idx = event["aktionsindex"]
    column = event["spalte"]
    calls = tiling_calls[player]
    if ev_idx >= len(calls):
        return {"status": "index_ausserhalb_tiling_calls", "spalte": column}

    after_state = state_before_tiling_call(players, first_player, seed, action_log, tiling_calls,
                                            player, ev_idx, final_state)
    empties = find_empty_cell_in_column(after_state, player, column)
    if len(empties) != 1:
        return {"status": f"zielzelle_nicht_eindeutig ({len(empties)} leere Zellen)", "spalte": column}
    slot_row, slot_col, space_index, _sp = empties[0]
    pattern_row = pattern_row_for_cell(slot_row, space_index)

    fenster = list(range(ev_idx + 1, len(calls)))
    if not fenster:
        return {"status": "kein_restzug_mehr", "spalte": column, "fenster_groesse": 0}

    legal_at = None
    blocker_first = None
    checked = 0
    for w in fenster:
        idx_before = calls[w]["global_index_before"]
        g_trial = replay_prefix(players, first_player, seed, action_log, idx_before)
        before_state = json.loads(g_trial.state_json())
        space = before_state["players"][player]["dome_grid"][slot_row][slot_col]["spaces"][space_index]
        checked += 1
        try:
            g_trial.apply_tiling(player, pattern_row, slot_row, slot_col, space_index)
            legal_at = w - ev_idx  # Abstand in eigenen Zuegen
            break
        except Exception as e:  # noqa: BLE001 -- Engine-Ablehnung ist das Messsignal
            reason = classify_blocker(before_state, player, pattern_row, space, str(e))
            if blocker_first is None:
                blocker_first = reason

    return {
        "status": "geprueft", "spalte": column, "fenster_groesse": len(fenster),
        "fenster_geprueft": checked, "legal_irgendwann": legal_at is not None,
        "legal_nach_n_eigenen_zuegen": legal_at, "blockadegrund_erster_pruefpunkt": blocker_first,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-games-per-file", type=int, default=90)
    ap.add_argument("--target-events", type=int, default=160,
                     help="frueher Stopp, sobald mind. so viele nicht-vollendete Hoehe-5-Ereignisse geprueft sind")
    ap.add_argument("--out", default=str(OUT_JSON))
    args = ap.parse_args()

    check_prereqs()

    per_game_stats = {"ok": 0, "divergence": 0, "exception": 0}
    exception_examples = []
    divergence_examples = []
    per_side_rows = []  # eine Zeile je (quelle, rolle, k1_aktiv, spieler-in-partie)
    n_events_checked = 0
    t0 = time.time()

    for quelle in QUELLEN:
        stop_all = False
        for dateiname in quelle["dateien"]:
            pfad = EVAL / "artifacts" / dateiname
            if not pfad.exists():
                print(f"FEHLT: {pfad}", file=sys.stderr)
                continue
            arme = quelle.get("arme", [None])
            for arm in arme:
                spiele = game_list(pfad, arm)
                n_take = min(len(spiele), args.max_games_per_file)
                for gi in range(n_take):
                    if n_events_checked >= args.target_events:
                        stop_all = True
                        break
                    sp = spiele[gi]
                    rep, lines, li, fehlerart, fehlertext = replay_arena_game(sp)
                    if fehlerart is not None:
                        per_game_stats[fehlerart] += 1
                        ex = {"quelle": quelle["kuerzel"], "datei": dateiname, "arm": arm,
                              "game_seed": sp.get("game_seed"), "fehler": fehlertext}
                        (divergence_examples if fehlerart == "divergence" else exception_examples).append(ex)
                        if len(exception_examples) > 8:
                            exception_examples[:] = exception_examples[:8]
                        if len(divergence_examples) > 8:
                            divergence_examples[:] = divergence_examples[:8]
                        continue
                    per_game_stats["ok"] += 1

                    namen = sp["names"]
                    rollen = quelle["rollen"](namen)
                    k1_aktiv = K1_TILE_ID in (sp.get("scoring_tile_ids") or [])
                    players_tuple = (namen[0], namen[1])
                    first_player = sp["first_player"]
                    seed = sp["game_seed"]
                    action_log = rep.action_log

                    sequenz_je_spieler = reconstruct_game_sequence(sp.get("log") or [])
                    tiling_calls, final_state = index_tiling_calls(players_tuple, first_player, seed, action_log)

                    for name in namen:
                        rolle = rollen.get(name)
                        if rolle is None:
                            continue
                        player_idx = rep.name_to_idx[name]
                        sequenz = sequenz_je_spieler.get(name, [])
                        if len(sequenz) != len(tiling_calls.get(player_idx, [])):
                            per_side_rows.append({
                                "quelle": quelle["kuerzel"], "rolle": rolle, "k1_aktiv": k1_aktiv,
                                "game_seed": seed, "status": "konsistenzbruch_text_vs_action_log",
                                "n_text": len(sequenz), "n_action_log": len(tiling_calls.get(player_idx, [])),
                                "ereignisse": [],
                            })
                            continue

                        ereignisse_text = hoehe5_ereignisse(sequenz)
                        gap_events = [e for e in ereignisse_text if not e["vollendet"]]
                        geprueft = []
                        for ev in gap_events:
                            if n_events_checked >= args.target_events:
                                break
                            res = check_event_legality(players_tuple, first_player, seed, action_log,
                                                        tiling_calls, final_state, player_idx, ev, len(sequenz))
                            geprueft.append(res)
                            if res["status"] == "geprueft":
                                n_events_checked += 1

                        per_side_rows.append({
                            "quelle": quelle["kuerzel"], "rolle": rolle, "k1_aktiv": k1_aktiv,
                            "game_seed": seed, "status": "ok",
                            "n_hoehe5_ereignisse_gesamt": len(ereignisse_text),
                            "n_gap_events": len(gap_events),
                            "ereignisse": geprueft,
                        })
                    if n_events_checked % 20 == 0:
                        print(f"  ... {n_events_checked}/{args.target_events} Ereignisse geprueft, "
                              f"{sum(per_game_stats.values())} Partien versucht, elapsed={time.time()-t0:.0f}s")
                if stop_all:
                    break
            if stop_all:
                break
        if stop_all:
            break

    n_tried = sum(per_game_stats.values())
    replay_ok_rate = per_game_stats["ok"] / n_tried if n_tried else None
    print(f"\nReplay-Erfolgsquote: {per_game_stats['ok']}/{n_tried} = {replay_ok_rate}")
    print(f"  divergence={per_game_stats['divergence']} exception={per_game_stats['exception']}")

    # ── Aggregation: echte verpasste Quote je (quelle, rolle, k1_aktiv) ─────
    gruppen = defaultdict(list)
    for row in per_side_rows:
        if row["status"] != "ok":
            continue
        gruppen[(row["quelle"], row["rolle"], row["k1_aktiv"])].append(row)

    tabelle = []
    blockade_gesamt = defaultdict(int)
    for (quelle, rolle, k1), rows in sorted(gruppen.items()):
        alle_ev = [e for r in rows for e in r["ereignisse"] if e["status"] == "geprueft"]
        n_ev = len(alle_ev)
        n_legal = sum(1 for e in alle_ev if e["legal_irgendwann"])
        n_echte_verpasst = n_ev - n_legal  # geprueft, NICHT vollendet (per Definition der Eingabe), NICHT legal moeglich
        blockaden = defaultdict(int)
        for e in alle_ev:
            if not e["legal_irgendwann"] and e.get("blockadegrund_erster_pruefpunkt"):
                key = e["blockadegrund_erster_pruefpunkt"]
                if key.startswith("sonstiger_engine_einwand"):
                    key = "sonstiger_engine_einwand"
                blockaden[key] += 1
                blockade_gesamt[key] += 1
        tabelle.append({
            "quelle": quelle, "rolle": rolle, "k1_aktiv": k1,
            "n_partie_seiten": len(rows),
            "n_gap_events_gesamt": sum(r["n_gap_events"] for r in rows),
            "n_ereignisse_geprueft": n_ev,
            "n_legal_moeglich_aber_nicht_gespielt": n_legal,
            "echte_verpasste_quote": (n_legal / n_ev) if n_ev else None,
            "blockadegruende": dict(blockaden),
        })

    ergebnis = {
        "auftrag": "Legalitaets-Stufe der Vollendungs-Sonde (PREREG_r5_solver_split.md par.3d)",
        "quarantaene": "Zustandsrekonstruktion ausschliesslich ueber tools/analyze_game_log.py::Replayer "
                        "(replay-exakter Pfad, PREREG_action_id_logging.md-Muster); Referee-/Worker-Pfad "
                        "nicht verwendet (PREREG_agent_encapsulation.md par.8d: Kernbeweis Stand 2026-08-23 ROT).",
        "replay_erfolgsquote": {
            "n_partien_versucht": n_tried, "n_ok": per_game_stats["ok"],
            "n_divergence": per_game_stats["divergence"], "n_exception": per_game_stats["exception"],
            "rate": replay_ok_rate,
            "exception_ursache": "vorbestehende Luecke in Replayer.maybe_silent_chip_complete "
                                  "(analyze_game_log.py:543) -- 'Reihe N nicht mit Chips komplettierbar', "
                                  "beim Bau von PREREG_action_id_logging.md nur an Mensch-Partien "
                                  "gegengeprobt, siehe Moduldoku dieser Datei.",
            "exception_beispiele": exception_examples, "divergence_beispiele": divergence_examples,
        },
        "n_ereignisse_geprueft_gesamt": n_events_checked,
        "blockadegruende_gesamt": dict(blockade_gesamt),
        "tabelle": tabelle,
        "per_side_rows": per_side_rows,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(ergebnis, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nGeschrieben: {out_path}")

    print(f"\n{'Quelle':<18}{'Rolle':<20}{'k1':<6}{'n_seiten':>9}{'n_gepr':>8}{'n_legal':>8}{'Quote':>8}")
    for row in tabelle:
        q = row["echte_verpasste_quote"]
        q_s = f"{q:.3f}" if q is not None else "n/a"
        print(f"{row['quelle']:<18}{row['rolle']:<20}{str(row['k1_aktiv']):<6}{row['n_partie_seiten']:>9}"
              f"{row['n_ereignisse_geprueft']:>8}{row['n_legal_moeglich_aber_nicht_gespielt']:>8}{q_s:>8}")
    print("\nBlockadegruende gesamt:", dict(blockade_gesamt))


if __name__ == "__main__":
    main()
