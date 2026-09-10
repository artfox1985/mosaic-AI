# -*- coding: utf-8 -*-
"""Wiederholungsziehung in einen BEREITS BEKANNTEN Stapelteil -- gezaehlt
gegen den mitgefuehrten Wissensstand (PREREG_dome_stack_information_sets.md
par.8, Diagnostik; par.15c Folge (2)).

**Die vorregistrierte Groesse.** par.8 zaehlt nicht "Ziehungen je Partie",
sondern die Ziehung in einen Stapelteil hinein, dessen Reihenfolge der
Ziehende bereits KENNT. Vorregistrierte Richtung: diese Zahl faellt mit
Variante A auf nahe null. par.15c hat sie auf EINER Partie gemessen (5
Entscheidungen im Wirkbereich, Erwartung trat nicht ein) und dafuer eine
breitere Grundmenge verlangt -- das ist dieses Werkzeug.

**Was "bekannt" heisst** (engine/src/state.rs:76-90, `KnownPoolBlock`): die
Bloecke beschreiben lueckenlos das SUFFIX von `dome_tile_pool`, aeltester
Block zuerst; das unbekannte Praefix ist alles davor
(`dome_pool_unknown_prefix_len`). Gezogen wird von OBEN, also bei Index 0.
Daraus die Dreiteilung je Ziehung:

* (a) unbekannt -- das Praefix ist noch nicht aufgebraucht,
* (b) EIGENER Block -- Praefix leer und `blocks[0].returner == actor`: der
  Ziehende hat diese Platte selbst zurueckgelegt und kennt sie mit
  Reihenfolge (par.4, "fuer den Ziehenden selbst"),
* (c) FREMDER Block -- Praefix leer und `returner != actor`: der Ziehende
  kennt die MENGE des Blocks, nicht die Reihenfolge darin.

(b) ist die vorregistrierte Groesse.

**Zustand VOR der Ziehung -- die Regel.** `Replayer.maybe_oracle` wird in
`_run_loop` (analyze_game_log.py:1216-1220) fuer jede STACK_PEEK-Zeile
aufgerufen, und zwar NACH `ensure_drafting_actor` (impliziter Pass schon
angewandt, der Ziehende ist am Zug) und VOR `rep.apply(..., "apply_dome_
stack_peek")`. Genau dort steht der gesuchte Zustand. Diese Sonde klinkt
sich per Wrapper um `Replayer.maybe_oracle` ein, statt `_run_loop`
nachzubauen: der Nachbau muesste Chip-Plan-Reparatur, Tiling-Kaskade und
Divergenzbehandlung mitkopieren. Der Wrapper laeuft VOR dem Original und
aendert dessen Verhalten nicht (er ruft es unveraendert auf); mit
`--no-oracle` steigt das Original ohnehin frueh aus.

**Konsistenzpruefung.** Die Zahl und die Serien-Nummern der aufgezeichneten
Ziehungen werden gegen die `📦`-Zeilen des Logs geprueft (Name und laufende
Nummer, in Reihenfolge). Abweichung 0 ist verlangt; abweichende Partien
gehen NICHT in die Kennzahlen und werden ausgewiesen.

Aufruf (einkernig, ohne Pipe):

    python -X utf8 -u tools/probes/dome_stack_known_block_draw_probe.py \\
        --input evaluations/artifacts/dome_stack_ab_v27-b01_live_vs_artifact_s60.json \\
        --label ab_s60
    python -X utf8 -u tools/probes/dome_stack_known_block_draw_probe.py \\
        --input static/log --label human
"""
import argparse
import io
import json
import os
import pathlib
import re
import statistics as st
import sys
import tempfile
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))
sys.path.insert(0, str(_ROOT / "tools"))

PREREG = "evaluations/PREREG_dome_stack_information_sets.md par.8 (Diagnostik), par.15c Folge (2)"

#: Die `📦`-Zeile des Logs: Name des Ziehenden und laufende Nummer in der
#: Serie. Gleiche Form wie `analyze_game_log.LINE_PATTERNS["STACK_PEEK"]`,
#: hier aber ohne Zeilenanfang, weil der Rundenpraefix `[R3] ` davorsteht.
STACK_PEEK_RE = re.compile(r"📦 (?P<name>.+?): (?P<n>\d+)\. Kachel vom Stapel gezogen")
GAME_START_RE = re.compile(r"Spiel gestartet\. (?P<name>.+?) beginnt\.")
START_TILE_RE = re.compile(r"\] (?P<name>.+?): Startkachel ")

TOP_UNKNOWN = "unbekannt"
TOP_OWN = "eigener_block"
TOP_FOREIGN = "fremder_block"
TOP_EMPTY = "pool_leer"


# ═══════════════════════════════════════════════════════════════════════════
# Aufzeichnung: Zustand VOR jeder Stapel-Ziehung
# ═══════════════════════════════════════════════════════════════════════════

def _snapshot_before_draw(game, actor: int) -> dict:
    """Der Zustand VOR einer Stapel-Ziehung, aus `state_json_exact()`.

    `dome_pool_order_exact` steht von oben nach unten (serialize.rs:1170,
    Iteration ueber `state.dome_tile_pool`), `dome_pool_known_blocks_exact`
    beschreibt das Suffix, aeltester Block zuerst (state.rs:76-84). Die
    Oberseite ist damit Index 0 des Pools.
    """
    state = json.loads(game.state_json_exact())
    pool = state.get("dome_pool_order_exact") or []
    blocks = state.get("dome_pool_known_blocks_exact") or []
    known_total = sum(int(b["len"]) for b in blocks)
    unknown_prefix = len(pool) - known_total
    own_block_len = 0
    if not pool:
        top = TOP_EMPTY
    elif unknown_prefix > 0:
        top = TOP_UNKNOWN
    elif blocks:
        first = blocks[0]
        if int(first["returner"]) == actor:
            top = TOP_OWN
            own_block_len = int(first["len"])
        else:
            top = TOP_FOREIGN
    else:
        # Praefix 0 und kein Block: nur moeglich, wenn der Pool leer ist --
        # der Fall ist oben schon abgefangen. Defensiv, nicht still.
        top = TOP_EMPTY
    return {
        "round": int(game.round_number()),
        "actor": actor,
        "current_player": int(state.get("current_player", -1)),
        "series_index": len(state.get("pending_stack_draw") or []) + 1,
        "pool_len": len(pool),
        "unknown_prefix": unknown_prefix,
        "n_blocks": len(blocks),
        "own_block_len": own_block_len,
        "top": top,
        "score_before": int(state["players"][actor]["score"]),
    }


def _install_capture(agl):
    """Wrapper um `Replayer.maybe_oracle`, der bei `dome_stack_peek` den
    Zustand VOR der Ziehung mitschreibt. Die Aufzeichnung haengt an der
    INSTANZ (`rep.stack_draw_records`): `_replay_once` baut je Durchlauf
    einen frischen `Replayer`, und die Chip-Plan-Reparatur faehrt bis zu
    zwei volle Durchlaeufe -- an einer Modul-Liste wuerden sich deren
    Ziehungen aufsummieren."""
    original = agl.Replayer.maybe_oracle
    if getattr(original, "_dome_stack_capture", False):
        return

    def maybe_oracle_capturing(self, actor, kind, played_desc, fields):
        if kind == "dome_stack_peek":
            records = getattr(self, "stack_draw_records", None)
            if records is None:
                records = []
                self.stack_draw_records = records
            rec = _snapshot_before_draw(self.g, actor)
            rec["actor_name"] = self.players[actor]
            records.append(rec)
        return original(self, actor, kind, played_desc, fields)

    maybe_oracle_capturing._dome_stack_capture = True
    agl.Replayer.maybe_oracle = maybe_oracle_capturing


# ═══════════════════════════════════════════════════════════════════════════
# Eingaben: Arena-/Referee-Artefakte und Server-Logs
# ═══════════════════════════════════════════════════════════════════════════

def _names_from_log(log_lines: list, first_player: int):
    """Spielernamen in BRETT-Reihenfolge, aus dem Log abgeleitet.

    Der Referee schreibt die Namen nicht ins Partie-Record (nur `board_a`),
    das Log traegt sie aber doppelt: die Startzeile nennt den Startspieler,
    die beiden `Startkachel`-Zeilen nennen beide Namen. Zusammen mit
    `first_player` ist die Zuordnung eindeutig -- geraten wird nichts.
    """
    first_name = None
    for line in log_lines[:3]:
        m = GAME_START_RE.search(line)
        if m:
            first_name = m.group("name")
            break
    seen = []
    for line in log_lines:
        m = START_TILE_RE.search(line)
        if m and m.group("name") not in seen:
            seen.append(m.group("name"))
        if len(seen) == 2:
            break
    if first_name is None or len(seen) != 2 or first_name not in seen:
        return None
    other = seen[0] if seen[1] == first_name else seen[1]
    names = [None, None]
    names[first_player] = first_name
    names[1 - first_player] = other
    return names


def _sides_referee(artifact: dict, game: dict):
    """Seitenzuordnung des Referee-Artefakts: Seite A ist die LIVE-Engine
    (mit Variante A), Seite B das eingefrorene Artefakt (ohne). Seite A
    sitzt auf Brett `board_a` (frozen_referee_match.py:296/402)."""
    board_a = int(game["board_a"])
    live = "live_variante_a"
    frozen = "artefakt_ohne"
    return {board_a: live, 1 - board_a: frozen}


def _sides_paired(game: dict):
    """paired_gating: `side_names` nennt die beiden Seiten, `board0_name`
    sagt, welche davon auf Brett 0 sitzt."""
    side_names = list(game["side_names"])
    board0 = game["board0_name"]
    if board0 == side_names[0]:
        return {0: side_names[0], 1: side_names[1]}
    return {0: side_names[1], 1: side_names[0]}


def _collect_inputs(input_path: pathlib.Path, tmp_dir: pathlib.Path, limit):
    """Gibt (kind, meta, [game_input]) zurueck. Ein `game_input` ist
    {key, path, log_lines, sides}."""
    if input_path.is_dir():
        files = sorted(input_path.glob("*.log"))
        if limit:
            files = files[:limit]
        games = []
        for path in files:
            header = _read_log_header(path)
            ai_player = header.get("ai_player")
            if ai_player is None:
                sides = {0: "unbekannt", 1: "unbekannt"}
            else:
                ai_player = int(ai_player)
                sides = {ai_player: "ki", 1 - ai_player: "mensch"}
            games.append({
                "key": path.name,
                "path": path,
                "log_lines": path.read_text(encoding="utf-8").splitlines(),
                "sides": sides,
            })
        return "logs", {"quelle": str(input_path).replace("\\", "/")}, games

    artifact = json.loads(input_path.read_text(encoding="utf-8"))
    raw_games = artifact.get("games") or []
    if not isinstance(raw_games, list):
        raise SystemExit(f"{input_path}: `games` ist kein Listenfeld (mehrarmige Artefakte "
                         f"sind hier nicht vorgesehen).")
    is_referee = "board_a" in (raw_games[0] if raw_games else {})
    if limit:
        raw_games = raw_games[:limit]
    games = []
    for idx, game in enumerate(raw_games):
        log_lines = list(game["log"])
        first_player = int(game.get("first_player", 0))
        names = game.get("names") or _names_from_log(log_lines, first_player)
        if names is None:
            raise SystemExit(f"{input_path} Partie {idx}: Spielernamen nicht ableitbar.")
        header = {"players": list(names), "first_player": first_player,
                  "seed": game.get("game_seed", game.get("seed", 0))}
        path = tmp_dir / f"game_{idx:05d}.log"
        path.write_text("# " + json.dumps(header, ensure_ascii=False) + "\n"
                        + "\n".join(log_lines) + "\n", encoding="utf-8", newline="\n")
        sides = _sides_referee(artifact, game) if is_referee else _sides_paired(game)
        games.append({"key": f"game_{idx:05d}", "path": path,
                      "log_lines": log_lines, "sides": sides})
    meta = {
        "quelle": str(input_path).replace("\\", "/"),
        "art": "referee" if is_referee else "paired_gating",
        "n_games_artefakt": len(artifact.get("games") or []),
    }
    for key in ("champion", "model_a", "spec_a", "sims_a", "name_a", "name_b",
                "sims_b", "model_b", "seite_a"):
        if key in artifact:
            meta[key] = artifact[key]
    return meta["art"], meta, games


def _read_log_header(path: pathlib.Path) -> dict:
    """Die `# {...}`-Kopfzeile eines Server-Logs (zweite Zeile der Datei)."""
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("# {"):
                return json.loads(line[2:])
            if not line.startswith("#"):
                break
    return {}


# ═══════════════════════════════════════════════════════════════════════════
# Replay einer Partie
# ═══════════════════════════════════════════════════════════════════════════

def _log_draws(log_lines: list) -> list:
    """(Name, Serien-Nummer) je `📦`-Zeile, in Log-Reihenfolge."""
    out = []
    for line in log_lines:
        m = STACK_PEEK_RE.search(line)
        if m:
            out.append((m.group("name"), int(m.group("n"))))
    return out


def _replay_game(agl, game_input: dict) -> dict:
    """Replayt EINE Partie und gibt {records, divergence, mismatch} zurueck.

    Die Zeilen-Fortschrittsausgabe des Replayers (`_run_loop`, alle 20
    Zeilen) wird eingefangen: bei 700+ Partien waeren das fuenfstellig viele
    Zeilen, die den eigenen Fortschrittszaehler unlesbar machen. Sie wird
    NUR bei Divergenz mit ausgegeben, dann traegt sie die Chip-Plan- und
    Abbruchmeldungen."""
    buffer = io.StringIO()
    stdout = sys.stdout
    sys.stdout = buffer
    try:
        rep, _lines, _li, div = agl.run(game_input["path"], model_path=None, sims=1,
                                        c_puct=0.3, do_oracle=False, limit=None)
    finally:
        sys.stdout = stdout
    records = list(getattr(rep, "stack_draw_records", []))
    if div:
        tail = [ln for ln in buffer.getvalue().splitlines() if "Zeile " not in ln][-5:]
        return {"records": [], "divergence": f"{div} | {' / '.join(tail)}" if tail else div,
                "mismatch": None, "return_order_from_hint": 0}
    expected = _log_draws(game_input["log_lines"])
    got = [(r["actor_name"], r["series_index"]) for r in records]
    mismatch = None
    if got != expected:
        mismatch = (f"Replay {len(got)} Ziehungen, Log {len(expected)}; "
                    f"erste Abweichung: {_first_diff(got, expected)}")
    for rec in records:
        rec["side"] = game_input["sides"].get(rec["actor"], "unbekannt")
        rec["actor_mismatch"] = rec["current_player"] != rec["actor"]
    return {"records": records, "divergence": None, "mismatch": mismatch,
            "return_order_from_hint": int(getattr(rep, "return_order_from_hint", 0))}


def _first_diff(got: list, expected: list):
    for i in range(max(len(got), len(expected))):
        a = got[i] if i < len(got) else None
        b = expected[i] if i < len(expected) else None
        if a != b:
            return {"index": i, "replay": a, "log": b}
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Kennzahlen
# ═══════════════════════════════════════════════════════════════════════════

def _side_metrics(per_game: list, side: str) -> dict:
    """Kennzahlen EINER Seite. Grundmenge und Einheit stehen je Feld im
    Namen: `*_je_partie` zaehlt ueber Partien, `anteil_*` ueber Ziehungen."""
    draws_per_game = []
    series_per_game = []
    own_per_game = []
    total = {TOP_UNKNOWN: 0, TOP_OWN: 0, TOP_FOREIGN: 0, TOP_EMPTY: 0}
    own_at_zero = 0
    draws_at_zero = 0
    series_lengths = []
    by_round = {}
    for records in per_game:
        mine = [r for r in records if r["side"] == side]
        draws_per_game.append(len(mine))
        n_series = sum(1 for r in mine if r["series_index"] == 1)
        series_per_game.append(n_series)
        own = 0
        for r in mine:
            total[r["top"]] += 1
            slot = by_round.setdefault(str(r["round"]),
                                       {"ziehungen": 0, TOP_UNKNOWN: 0, TOP_OWN: 0,
                                        TOP_FOREIGN: 0, TOP_EMPTY: 0})
            slot["ziehungen"] += 1
            slot[r["top"]] += 1
            if r["top"] == TOP_OWN:
                own += 1
                if r["score_before"] == 0:
                    own_at_zero += 1
            if r["score_before"] == 0:
                draws_at_zero += 1
        own_per_game.append(own)
        # Serienlaengen: die Nummer VOR jedem Serienstart schliesst die
        # vorige Serie ab; die letzte schliesst das Partieende.
        run = 0
        for r in mine:
            if r["series_index"] == 1 and run:
                series_lengths.append(run)
                run = 0
            run += 1
        if run:
            series_lengths.append(run)
    n_draws = sum(draws_per_game)
    n_games = len(per_game)
    return {
        # Partie-weise Reihen: die Referee-Artefakte sind ungepaart je Partie,
        # aber die BEIDEN SEITEN spielen dieselbe Partie -- der Vergleich
        # (b)-live gegen (b)-artefakt ist also je Partie gepaart und laesst
        # sich nur mit diesen Reihen nachrechnen.
        "je_partie_ziehungen": draws_per_game,
        "je_partie_eigener_block": own_per_game,
        # Runden-Aufschluesselung: in R1 kann es per Konstruktion keinen
        # eigenen Block geben (noch keine Rueckgabe), in R2 gehoert der
        # ganze Stapel meist EINEM Block -- par.15c, "Lesart".
        "nach_runde": dict(sorted(by_round.items(), key=lambda kv: int(kv[0]))),
        "n_partien": n_games,
        "n_ziehungen": n_draws,
        "ziehungen_je_partie_mittel": (n_draws / n_games) if n_games else 0.0,
        "ziehungen_je_partie_median": st.median(draws_per_game) if draws_per_game else 0.0,
        "anteil_unbekannt": (total[TOP_UNKNOWN] / n_draws) if n_draws else 0.0,
        "anteil_eigener_block": (total[TOP_OWN] / n_draws) if n_draws else 0.0,
        "anteil_fremder_block": (total[TOP_FOREIGN] / n_draws) if n_draws else 0.0,
        "n_unbekannt": total[TOP_UNKNOWN],
        "n_eigener_block": total[TOP_OWN],
        "n_fremder_block": total[TOP_FOREIGN],
        "n_pool_leer": total[TOP_EMPTY],
        "eigener_block_je_partie_mittel": (sum(own_per_game) / n_games) if n_games else 0.0,
        "anteil_partien_mit_eigenem_block": (
            sum(1 for x in own_per_game if x >= 1) / n_games) if n_games else 0.0,
        "n_eigener_block_bei_stand_0": own_at_zero,
        "n_ziehungen_bei_stand_0": draws_at_zero,
        "stapelzuege_je_partie_mittel": (sum(series_per_game) / n_games) if n_games else 0.0,
        "serienlaenge_mittel": (sum(series_lengths) / len(series_lengths)) if series_lengths else 0.0,
        "serienlaenge_max": max(series_lengths) if series_lengths else 0,
    }


def _print_table(label: str, metrics: dict) -> None:
    sides = sorted(metrics)
    width = max(len(s) for s in sides) + 2 if sides else 10
    rows = [
        ("Partien (n)", "n_partien", "{:.0f}"),
        ("Ziehungen gesamt", "n_ziehungen", "{:.0f}"),
        ("Ziehungen/Partie (Mittel)", "ziehungen_je_partie_mittel", "{:.3f}"),
        ("Ziehungen/Partie (Median)", "ziehungen_je_partie_median", "{:.1f}"),
        ("Anteil (a) unbekannt", "anteil_unbekannt", "{:.4f}"),
        ("Anteil (b) eigener Block", "anteil_eigener_block", "{:.4f}"),
        ("Anteil (c) fremder Block", "anteil_fremder_block", "{:.4f}"),
        ("(b) absolut", "n_eigener_block", "{:.0f}"),
        ("(b) je Partie (Mittel)", "eigener_block_je_partie_mittel", "{:.4f}"),
        ("Anteil Partien mit (b)>=1", "anteil_partien_mit_eigenem_block", "{:.4f}"),
        ("(b) davon bei Stand 0", "n_eigener_block_bei_stand_0", "{:.0f}"),
        ("Ziehungen bei Stand 0", "n_ziehungen_bei_stand_0", "{:.0f}"),
        ("Stapelzuege/Partie (Mittel)", "stapelzuege_je_partie_mittel", "{:.4f}"),
        ("Serienlaenge (Mittel)", "serienlaenge_mittel", "{:.3f}"),
        ("Serienlaenge (Max)", "serienlaenge_max", "{:.0f}"),
    ]
    print()
    print(f"=== {label} ===", flush=True)
    print("Kennzahl".ljust(30) + "".join(s.ljust(width) for s in sides))
    for title, key, fmt in rows:
        cells = "".join(fmt.format(metrics[s][key]).ljust(width) for s in sides)
        print(title.ljust(30) + cells)
    print("Grundmenge: Partien der Eingabe je Seite; Einheit: Ziehungen "
          "(Kategorie a/b/c) bzw. Partien.", flush=True)


# ═══════════════════════════════════════════════════════════════════════════
# Treiber
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True,
                    help="Arena-/Referee-Artefakt (.json) ODER ein Verzeichnis mit *.log")
    ap.add_argument("--label", required=True, help="Kuerzel fuer den Artefaktnamen")
    ap.add_argument("--limit", type=int, default=None, help="nur die ersten N Partien")
    ap.add_argument("--out-dir", default="evaluations/artifacts")
    args = ap.parse_args()

    import analyze_game_log as agl
    _install_capture(agl)

    t_wall = time.perf_counter()
    t_cpu = time.process_time()
    input_path = (_ROOT / args.input) if not os.path.isabs(args.input) else pathlib.Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Eingabe fehlt: {input_path}")

    with tempfile.TemporaryDirectory(prefix="dome_stack_probe_") as tmp:
        tmp_dir = pathlib.Path(tmp)
        kind, meta, game_inputs = _collect_inputs(input_path, tmp_dir, args.limit)
        n_total = len(game_inputs)
        print(f"[{args.label}] {n_total} Partien, Art '{kind}', Quelle {meta['quelle']}", flush=True)

        per_game = []
        divergent = []
        mismatched = []
        actor_mismatch = 0
        return_order_hints = 0
        sides_seen = set()
        for i, game_input in enumerate(game_inputs, 1):
            try:
                res = _replay_game(agl, game_input)
            except Exception as e:  # defensiv: eine kaputte Partie kippt den Lauf nicht
                divergent.append({"partie": game_input["key"], "grund": f"{type(e).__name__}: {e}"})
                res = None
            if res is None:
                pass
            elif res["divergence"]:
                divergent.append({"partie": game_input["key"], "grund": res["divergence"]})
            elif res["mismatch"]:
                mismatched.append({"partie": game_input["key"], "grund": res["mismatch"]})
            else:
                per_game.append(res["records"])
                return_order_hints += res["return_order_from_hint"]
                actor_mismatch += sum(1 for r in res["records"] if r["actor_mismatch"])
                sides_seen.update(game_input["sides"].values())
            if i % 5 == 0 or i == n_total:
                print(f"  ... {i}/{n_total} Partien "
                      f"(verwertet {len(per_game)}, divergent {len(divergent)}, "
                      f"inkonsistent {len(mismatched)})", flush=True)

    metrics = {side: _side_metrics(per_game, side) for side in sorted(sides_seen)}
    _print_table(args.label, metrics)

    wall = time.perf_counter() - t_wall
    cpu = time.process_time() - t_cpu
    out = {
        "frage": "Wie oft zieht eine Seite in einen Stapelteil, dessen Reihenfolge sie "
                 "bereits kennt (par.8: 'Wiederholungsziehung in einen BEREITS BEKANNTEN "
                 "Stapelteil')?",
        "prereg": PREREG,
        "label": args.label,
        "art": kind,
        "meta": meta,
        "definition": {
            "a_unbekannt": "unbekanntes Praefix noch nicht aufgebraucht "
                           "(dome_pool_unknown_prefix_len > 0)",
            "b_eigener_block": "Praefix leer und blocks[0].returner == Ziehender "
                               "(Reihenfolge bekannt -- die vorregistrierte Groesse)",
            "c_fremder_block": "Praefix leer und blocks[0].returner != Ziehender "
                               "(Menge bekannt, Reihenfolge nicht)",
            "zustand_vor_der_ziehung": "Replayer.maybe_oracle(kind='dome_stack_peek'), "
                                       "aufgerufen in analyze_game_log._run_loop nach "
                                       "ensure_drafting_actor und vor apply_dome_stack_peek",
        },
        "n_partien_eingabe": n_total,
        "n_partien_verwertet": len(per_game),
        "konsistenz": {
            "divergente_partien": len(divergent),
            "inkonsistente_partien": len(mismatched),
            "beispiele_divergenz": divergent[:5],
            "beispiele_inkonsistenz": mismatched[:5],
            "ziehungen_mit_falschem_akteur": actor_mismatch,
            "rueckleg_reihenfolge_aus_hinweis": return_order_hints,
        },
        "kennzahlen": metrics,
        "laufzeit": {
            "wanduhr_s": round(wall, 2),
            "cpu_s": round(cpu, 2),
            "threads": 1,
            "s_je_partie": round(wall / n_total, 4) if n_total else None,
        },
    }
    out_dir = (_ROOT / args.out_dir) if not os.path.isabs(args.out_dir) else pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"dome_stack_known_block_draws_{args.label}.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nArtefakt: {out_path}  "
          f"(Wanduhr {wall:.1f}s, CPU {cpu:.1f}s, {out['laufzeit']['s_je_partie']}s/Partie)",
          flush=True)
    if divergent or mismatched:
        print(f"ACHTUNG: {len(divergent)} divergente und {len(mismatched)} inkonsistente "
              f"Partien NICHT in den Kennzahlen.", flush=True)


if __name__ == "__main__":
    main()
