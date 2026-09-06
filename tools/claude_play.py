# -*- coding: utf-8 -*-
"""Spiel-Interface Claude gegen Netz (PREREG_claude_play_interface.md, Nutzer-Auftrag 2026-09-06).

Jeder Zug ist ein eigener Prozess: der Zustand wird bei jedem Aufruf aus dem Partie-Log
(Server-Format, `static/log/game_*.log`) per `tools/analyze_game_log.Replayer` rekonstruiert,
damit jede Partie mit den vorhandenen Sonden auswertbar bleibt (par.3.1). Claude sieht genau
das, was `serialize.rs` liefert und das Netz kodiert (par.3.2), nicht mehr. Tiling legt Claude
selbst (Nutzer 2026-09-06 12:50: "tiling spielst selber").

Aufrufe (Projektordner; Netz-Zuege sind CPU-Auftraege -> NICHT neben einer Arena oder Sonde):
    python -X utf8 tools/claude_play.py new --game g01 --seed 20260906 --first-player 0
    python -X utf8 tools/claude_play.py show --game g01
    python -X utf8 tools/claude_play.py move --game g01 "s 2 rot 3"
    python -X utf8 tools/claude_play.py note --game g01 "R2: Netz laesst Reihe 6 liegen (Zeile 41)"

Zugnotation (par.3.3), Farben blau gelb rot schwarz tuerkis (auch B G R S T):
    s <quelle> <farbe> <reihe|floor> [mond:<farbe,...>]   Stein; Quelle = 1-4 (Sonnenseite der Fabrik),
                                                          m1-m4 (Mondstapel der Fabrik), m (globaler
                                                          Mondzug, Aktion C), gf / gm (grosse
                                                          Fabrik Sonne / Mond); <reihe> 0-5 oder "floor";
                                                          die Anzeige nennt zu jedem legalen Zug die Kurzform
    d <platte> <slot_r> <slot_c> [rot]                    Kuppelplatte aus der Auslage (rot 0/90/180/270)
    peek                                                  verdeckt vom Stapel ziehen (Aktion A, Schritt 1)
    choose <platte> <slot_r> <slot_c> [rot] [zurueck:<id,...>]  gezogene Platte legen
    chip <fabrik>                                         Bonuschip nehmen
    start <platte> <slot_r> <slot_c> [rot]                Startplatte legen (Anfang der Partie)
    pass
    -- Tiling-Phase (Claude am Zug): --
    tile <reihe> <r> <c>        Stein aus Musterreihe <reihe> auf Rasterzelle (r, c) (r = Reihe der Zeile)
    chips <reihe>               Reihe mit Bonuschips vollenden (Engine-Auswahl)
    floor <reihe>               unplatzierbare Reihe raeumen
    done                        Tiling beenden (danach zieht das Netz weiter)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

GAMES_DIR = REPO / "evaluations" / "artifacts" / "claude_play"
COLORS = {"blau": "B", "gelb": "G", "rot": "R", "schwarz": "S", "türkis": "T", "bunt": "*"}
COLOR_IN = {"b": "blau", "blau": "blau", "g": "gelb", "gelb": "gelb", "r": "rot", "rot": "rot",
            "s": "schwarz", "schwarz": "schwarz", "t": "türkis", "tuerkis": "türkis", "türkis": "türkis"}
# Wie server.py `_SPEC_TO_ENV` (server.py:205): Spec-Felder des Gegners als Env-Knoepfe,
# VOR dem Import der Engine gesetzt (OnceLock-Getter lesen nur einmal je Prozess).
SPEC_TO_ENV = {
    "implicit_minimax_alpha": "MOSAIC_IMPLICIT_MINIMAX_A",
    "long_row_init_shaping_w": "MOSAIC_LONG_ROW_INIT_W",
    "score_utility_c": "MOSAIC_SCORE_UTILITY_C",
    "score_utility_b": "MOSAIC_SCORE_UTILITY_B",
    "envelope_search_c": "MOSAIC_ENVELOPE_SEARCH_C",
    "envelope_tiling_w": "MOSAIC_ENVELOPE_TILING_W",
    "envelope_tiling_value_w": "MOSAIC_ENVELOPE_TILING_VALUE_W",
    "envelope_projection_mode": "MOSAIC_ENVELOPE_PROJECTED",
    "envelope_profile": "MOSAIC_ENVELOPE_PROFILE",
    "envelope_flush_w": "MOSAIC_ENVELOPE_FLUSH_W",
}


# ---------------------------------------------------------------- Partie-Verzeichnis
def game_dir(name: str) -> Path:
    return GAMES_DIR / name


def load_manifest(name: str) -> dict:
    return json.loads((game_dir(name) / "manifest.json").read_text(encoding="utf-8"))


def save_manifest(name: str, m: dict) -> None:
    (game_dir(name) / "manifest.json").write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def apply_spec_env(spec_path: Path) -> None:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    for field, env in SPEC_TO_ENV.items():
        if field in spec:
            v = spec[field]
            os.environ[env] = ",".join(str(x) for x in v) if isinstance(v, list) else str(v)


def resolve_model(name: str) -> Path:
    for c in (REPO / "models" / f"alphazero_{name}.onnx", REPO / "models" / "frozen_champions" / name / "model.onnx"):
        if c.exists():
            return c
    raise SystemExit(f"Modell '{name}' nicht gefunden (models/alphazero_{name}.onnx, models/frozen_champions/{name}/model.onnx)")


# ---------------------------------------------------------------- Engine laden / Zustand aufbauen
def engine(m: dict):
    apply_spec_env(REPO / m["spec"])
    import mosaic_rust as mr  # noqa: WPS433 (nach dem Env-Setzen)
    return mr


def rebuild_game(name: str, m: dict):
    """PyGame aus dem Log rekonstruieren (Replayer), Netz laden, (g, log_len) zurueckgeben."""
    mr = engine(m)
    import analyze_game_log as agl
    log_path = game_dir(name) / "game.log"
    rep, _lines, li, div = agl.run(log_path, model_path=None, sims=1, c_puct=0.3, do_oracle=False, limit=None)
    if div:
        raise SystemExit(f"Replay-Divergenz in {log_path.name}: {div}")
    g = rep.g
    # Ein Pass schreibt keine Log-Zeile (game.rs Action::Pass, py.rs:786); der Replayer
    # rekonstruiert ihn aus dem Spielerwechsel der NAECHSTEN Aktion -- als LETZTE Aktion
    # geht er verloren. Darum merkt sich das Manifest den letzten Pass und spielt ihn nach.
    tp = m.get("trailing_pass")
    if tp is not None and json.loads(g.state_json()).get("phase") == "drafting" and g.current_player() == tp:
        g.apply_pass()
    if m["opponent"] != "heuristic":
        g.load_net(str(REPO / m["model_path"]))
    return mr, g


def append_log(name: str, g, since: int) -> int:
    new = g.log_since(since)
    if new:
        with open(game_dir(name) / "game.log", "a", encoding="utf-8", newline="\n") as fh:
            for e in new:
                fh.write(f"{e}\n")
    return g.log_len()


# ---------------------------------------------------------------- Netz-Zuege bis Claude dran ist
def drive_ai(name: str, m: dict, g, since: int, out: list[str]) -> int:
    ai = m["ai_player"]
    for _ in range(400):
        st = json.loads(g.state_json())
        phase = st.get("phase")
        if phase == "end":
            if not m.get("end_scored"):
                res = json.loads(g.end_scoring_json())
                m["end_scored"] = True
                m["result"] = {"scores": list(g.scores()), "end_scoring": res.get("end_scoring")}
                save_manifest(name, m)
                out.append(f"SPIELENDE: Punkte {g.scores()} (Claude = Spieler {m['me']})")
            return append_log(name, g, since)
        pend = [v for v in st.get("valid_moves", []) if v.get("type") == "start_tile_pending"]
        if pend:
            if pend[0]["player"] == ai:
                res = json.loads(g.ai_start_tile_json(ai))
                out.append(f"KI: {res.get('description')}")
                continue
            return append_log(name, g, since)
        if phase in ("drafting", "tiling") and g.current_player() == ai:
            if m["opponent"] == "heuristic":
                res = json.loads(g.ai_step_json(m["sims"], True))
            else:
                res = json.loads(g.ai_step_net_json(m["sims"], m["c_puct"], True))
            if not res.get("applied"):
                out.append(f"KI konnte nicht ziehen: {res.get('reason')}")
                return append_log(name, g, since)
            a = res.get("action") or {}
            m["trailing_pass"] = ai if a.get("type") == "pass" else None
            save_manifest(name, m)
            out.append(f"KI: {a.get('description') or json.dumps(a, ensure_ascii=False)[:160]}")
            continue
        return append_log(name, g, since)
    raise SystemExit("drive_ai: Schleifendeckel erreicht")


# ---------------------------------------------------------------- Darstellung
def cell_char(sp: dict | None) -> str:
    if sp is None:
        return "."
    t = sp.get("type")
    if sp.get("filled") is not None:
        return "#" if sp["filled"] == "special" else COLORS.get(sp["filled"], "?").upper()
    if t == "SPECIAL":
        return "#"
    if t == "WILD":
        return "*"
    return COLORS.get(sp.get("color"), "?").lower()


def grid_lines(grid) -> list[str]:
    rows = []
    for r in range(6):
        cells = []
        for c in range(6):
            slot = grid[r // 2][c // 2] if grid and r // 2 < len(grid) and c // 2 < len(grid[r // 2]) else None
            sp = None
            if slot:
                spaces = slot.get("spaces") or []
                idx = (r % 2) * 2 + (c % 2)
                sp = spaces[idx] if idx < len(spaces) else None
            cells.append(cell_char(sp))
        rows.append(f"    z{r} " + " ".join(cells))
    return rows


def tile_str(t: dict) -> str:
    sp = t.get("spaces") or []
    return f"#{t['id']}[{''.join(cell_char(s) for s in sp[:2])}/{''.join(cell_char(s) for s in sp[2:4])}]{'+' + str(t['bonus']) if t.get('bonus') else ''}"


# Farb-Zaehlfelder der Engine (`bag_colors`, `tower_colors`): LISTE von 5 Zaehlern in der
# Reihenfolge TileColor::NORMAL (serialize.rs:309, color_counts), kein Dict.
NORMAL_ORDER = ("blau", "gelb", "rot", "schwarz", "türkis")


def counts_str(counts) -> str:
    if isinstance(counts, dict):
        return " ".join(f"{COLORS.get(k, '?')}{v}" for k, v in counts.items()) or "-"
    if isinstance(counts, list):
        return " ".join(f"{COLORS[c]}{n}" for c, n in zip(NORMAL_ORDER, counts)) or "-"
    return "-"


def colors_str(lst) -> str:
    return "".join(COLORS.get(c, "?") for c in lst) or "-"


def render(st: dict, m: dict, tiles_catalog: dict) -> str:
    me, ai = m["me"], m["ai_player"]
    L = []
    L.append(f"Runde {st.get('round')} | Phase {st.get('phase')} | am Zug: Spieler {st.get('current_player')} ({'CLAUDE' if st.get('current_player') == me else 'KI'})")
    ids = st.get("scoring_tile_ids") or []
    L.append("Wertungsplatten: " + "; ".join(f"{i} {tiles_catalog.get(i, {}).get('name', '?')} ({tiles_catalog.get(i, {}).get('description', '')})" for i in ids))
    L.append(f"Beutel {counts_str(st.get('bag_colors'))} | Turm {counts_str(st.get('tower_colors'))} | Stapel {st.get('dome_stack_count')} (oben: {st.get('dome_stack_top_type')})")
    L.append("Auslage Kuppelplatten: " + "  ".join(tile_str(t) for t in st.get("dome_display", [])) + (f"  | gezogen: {'  '.join(tile_str(t) for t in st.get('pending_stack_draw', []))}" if st.get("pending_stack_draw") else ""))
    for f in st.get("factories", []):
        chip = f.get("bonus_chip")
        chip_s = f" chip:{colors_str(chip['colors'])}" if chip and f.get("chip_revealed") else (" chip:?" if chip else "")
        L.append(f"Fabrik {f['id']}: Sonne {colors_str(f['sun'])} | Mond {' '.join(colors_str(s) for s in f['moon']) or '-'}{chip_s}")
    lf = st.get("large_factory") or {}
    L.append(f"Grosse Fabrik: Sonne {colors_str(lf.get('sun', []))} | Mond {colors_str(lf.get('moon', []))}{' | Startmarker' if lf.get('marker') else ''}")
    for pi, pl in enumerate(st.get("players", [])):
        tag = "CLAUDE" if pi == me else "KI"
        L.append(f"--- Spieler {pi} {tag} ({pl.get('name')}): {pl.get('score')} Punkte, Rundenschaetzer {pl.get('estimated_score')}{' | Startmarker' if pl.get('marker') else ''}")
        rows = []
        for row in pl.get("pattern_lines", []):
            k = len(row.get("tiles") or [])
            rows.append(f"R{row['index']}:{COLORS.get(row.get('color'), '-') if k else '-'}{k}/{row['capacity']}{'(' + str(row['phantom_count']) + 'ph)' if row.get('phantom_count') else ''}")
        L.append("    Musterreihen " + " ".join(rows) + f" | Strafleiste {colors_str(pl.get('floor', []))} | Chips {' '.join(colors_str(c['colors']) for c in pl.get('bonus_chips', [])) or '-'}")
        L.append("    Raster (gross = belegt, klein = Farbe der freien Zelle, * wild, # Spezial, . ohne Platte)")
        L.extend(grid_lines(pl.get("dome_grid") or []))
    return "\n".join(L)


def legal_moves_text(st: dict, m: dict) -> str:
    vm = st.get("valid_moves") or []
    if not vm:
        return ""
    L = ["Legale Zuege:"]
    stones = [v for v in vm if v["type"] == "stone"]
    for v in stones:
        fid = v.get("factory_id")
        # Aktion C (globaler Mondzug): SMALL_FACTORY_MOON ohne Fabrik-Id (moves.rs:39) -> Kurzform "m".
        src = {"SMALL_FACTORY_SUN": f"{fid}", "SMALL_FACTORY_MOON": ("m" if fid is None else f"m{fid}"),
               "LARGE_FACTORY_SUN": "gf", "LARGE_FACTORY_MOON": "gm"}.get(v["source"], v["source"])
        L.append(f"  s {src} {v['color']} {v['row'] if v['row'] >= 0 else 'floor'}" + (f" mond:{','.join(v['moon_order'])}" if v.get("moon_order") else ""))
    domes = {}
    for v in vm:
        if v["type"] == "dome_display":
            domes.setdefault(v["tile_id"], set()).add((v["slot_row"], v["slot_col"]))
    for tid, slots in sorted(domes.items()):
        L.append(f"  d {tid} <slot_r> <slot_c> [rot]  Slots: {sorted(slots)}")
    if any(v["type"] == "dome_stack_peek" for v in vm):
        L.append("  peek")
    chooses = {}
    for v in vm:
        if v["type"] == "dome_stack_choose":
            chooses.setdefault(v["chosen_id"], set()).add((v["slot_row"], v["slot_col"]))
    for tid, slots in sorted(chooses.items()):
        L.append(f"  choose {tid} <slot_r> <slot_c> [rot]  Slots: {sorted(slots)}")
    for v in vm:
        if v["type"] == "bonus_chip":
            L.append(f"  chip {v['factory_id']}")
        if v["type"] == "pass":
            L.append("  pass")
        if v["type"] == "start_tile_pending":
            L.append(f"  start <platte> <slot_r> <slot_c> [rot]   (Spieler {v['player']} legt die Startplatte; Platten der Auslage)")
    return "\n".join(L)


def tiling_text(st: dict, g, m: dict) -> str:
    me = m["me"]
    rows = [r for r in st.get("valid_tiling_rows", []) if r["pi"] == me]
    unpl = [u for u in json.loads(g.unplaceable_json()) if u["player"] == me]
    L = ["Tiling (Claude): volle Reihen " + (", ".join(f"R{r['ri']}" for r in rows) or "keine")
         + (" | unplatzierbar: " + ", ".join(f"R{u['pattern_row']} ({u['color']})" for u in unpl) if unpl else "")]
    L.append("  tile <reihe> <r> <c> | chips <reihe> | floor <reihe> | done")
    return "\n".join(L)


# ---------------------------------------------------------------- Zug anwenden
def parse_color(tok: str) -> str:
    c = COLOR_IN.get(tok.lower())
    if not c:
        raise SystemExit(f"unbekannte Farbe '{tok}'")
    return c


def apply_move(g, m: dict, text: str) -> str:
    me = m["me"]
    parts = text.split()
    if not parts:
        raise SystemExit("leerer Zug")
    cmd = parts[0].lower()
    if cmd == "s":
        src, color, row = parts[1], parse_color(parts[2]), parts[3]
        moon = []
        for extra in parts[4:]:
            if extra.startswith("mond:"):
                moon = [parse_color(x) for x in extra[5:].split(",") if x]
        row_i = -1 if row.lower() == "floor" else int(row)
        s_ = src.lower()
        if s_ == "gf":
            g.apply_stone("LARGE_FACTORY_SUN", color, row_i, None, moon or None)
        elif s_ == "gm":
            g.apply_stone("LARGE_FACTORY_MOON", color, row_i, None, moon or None)
        elif s_.startswith("m"):
            g.apply_stone("SMALL_FACTORY_MOON", color, row_i, (int(s_[1:]) if len(s_) > 1 else None), moon or None)
        else:
            g.apply_stone("SMALL_FACTORY_SUN", color, row_i, int(s_), moon or None)
        return f"Claude: Stein {color} aus {src} nach {'Strafleiste' if row_i < 0 else 'R' + str(row_i)}"
    if cmd == "d":
        tid, r, c = int(parts[1]), int(parts[2]), int(parts[3]); rot = int(parts[4]) if len(parts) > 4 else 0
        g.apply_dome(tid, r, c, rot)
        return f"Claude: Platte {tid} -> Slot ({r},{c}) rot {rot}"
    if cmd == "peek":
        res = g.apply_dome_stack_peek()
        return f"Claude: Stapel gezogen -> {res}"
    if cmd == "choose":
        tid, r, c = int(parts[1]), int(parts[2]), int(parts[3]); rot = 0; back = []
        for extra in parts[4:]:
            if extra.startswith("zurueck:"):
                back = [int(x) for x in extra[8:].split(",") if x]
            else:
                rot = int(extra)
        g.apply_dome_stack_choose(tid, r, c, rot, back or None)
        return f"Claude: gezogene Platte {tid} -> Slot ({r},{c}) rot {rot}"
    if cmd == "chip":
        g.apply_bonus_chip(int(parts[1]))
        return f"Claude: Bonuschip aus Fabrik {parts[1]}"
    if cmd == "start":
        tid, r, c = int(parts[1]), int(parts[2]), int(parts[3]); rot = int(parts[4]) if len(parts) > 4 else 0
        g.apply_start_tile(me, tid, r, c, rot)
        return f"Claude: Startplatte {tid} -> Slot ({r},{c}) rot {rot}"
    if cmd == "pass":
        g.apply_pass()
        return "Claude: passt"
    if cmd == "tile":
        row, r, c = int(parts[1]), int(parts[2]), int(parts[3])
        pts = g.apply_tiling(me, row, r // 2, c // 2, (r % 2) * 2 + (c % 2))
        return f"Claude: Stein aus R{row} auf ({r},{c}), +{pts} Punkte"
    if cmd == "chips":
        g.apply_tiling_chips(me, int(parts[1]))
        return f"Claude: R{parts[1]} mit Chips vollendet"
    if cmd == "floor":
        g.move_row_to_floor(me, int(parts[1]))
        return f"Claude: R{parts[1]} unplatzierbar geraeumt"
    if cmd == "done":
        g.end_tiling(me)
        return "Claude: Tiling beendet"
    raise SystemExit(f"unbekannter Zug '{text}' (Notation im Kopf der Datei)")


# ---------------------------------------------------------------- Befehle
def cmd_new(a) -> int:
    name = a.game
    d = game_dir(name)
    if d.exists():
        raise SystemExit(f"{d} existiert schon")
    me = 0 if a.claude_side == 0 else 1
    ai = 1 - me
    names = ["Claude", "KI"] if me == 0 else ["KI", "Claude"]
    opponent = a.opponent
    spec = a.spec or (f"models/{opponent}.spec.json" if opponent != "heuristic" else "models/k3v_off.spec.json")
    model_path = None if opponent == "heuristic" else str(resolve_model(opponent).relative_to(REPO))
    m = {"game": name, "seed": a.seed, "first_player": a.first_player, "me": me, "ai_player": ai,
         "names": names, "opponent": opponent, "model_path": model_path, "spec": spec,
         "sims": a.sims, "c_puct": 1.5, "prereg": "PREREG_claude_play_interface.md",
         "started": dt.datetime.now().isoformat(timespec="seconds"), "moves_claude": 0}
    mr = engine(m)
    cfg = json.loads(mr.engine_config_json())
    m["engine"] = {"input_size": cfg.get("input_size"), "contract_hash": cfg.get("contract_hash")}
    d.mkdir(parents=True)
    g = mr.PyGame((names[0], names[1]), a.first_player, a.seed)
    if model_path:
        g.load_net(str(REPO / model_path))
    meta = {"timestamp": dt.datetime.now().strftime("%Y%m%d_%H%M%S"), "seed": g.seed(), "players": names,
            "first_player": a.first_player, "ai_enabled": True, "ai_player": ai,
            "ai_model": opponent, "ai_sims": a.sims, "teacher_level": 0, "teacher_sims": None,
            "teacher_coach_sims": None, "claude_play": True}
    with open(d / "game.log", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# MOSAIC GAME LOG\n")
        fh.write(f"# {json.dumps(meta, ensure_ascii=False)}\n")
        fh.write(f"# {'=' * 60}\n")
    m["seed"] = g.seed()
    save_manifest(name, m)
    out: list[str] = []
    drive_ai(name, m, g, 0, out)
    print("\n".join(out))
    return show(name, m, mr, g)


def show(name: str, m: dict, mr, g) -> int:
    st = json.loads(g.state_json())
    catalog = {t["id"]: t for t in json.loads(mr.scoring_tiles_json()).get("tiles", [])}
    print(render(st, m, catalog))
    if st.get("phase") == "drafting" and g.current_player() == m["me"] or any(v.get("type") == "start_tile_pending" for v in st.get("valid_moves", [])):
        print(legal_moves_text(st, m))
    if st.get("phase") == "tiling" and g.current_player() == m["me"]:
        print(tiling_text(st, g, m))
    if st.get("phase") == "end":
        print(f"SPIELENDE. Punkte {g.scores()} (Claude = Spieler {m['me']}); Ergebnis im Manifest.")
    return 0


def cmd_show(a) -> int:
    m = load_manifest(a.game)
    mr, g = rebuild_game(a.game, m)
    return show(a.game, m, mr, g)


def cmd_move(a) -> int:
    m = load_manifest(a.game)
    mr, g = rebuild_game(a.game, m)
    since = g.log_len()
    try:
        out = [apply_move(g, m, a.move)]
    except (ValueError, RuntimeError, IndexError) as e:
        print(f"ZUG ABGEWIESEN ({a.move!r}): {e}")
        print("Die legalen Zuege stehen unter 'show' -- Kurzform genau so uebernehmen (auch mond:...).")
        return 1
    m["moves_claude"] = m.get("moves_claude", 0) + 1
    m["trailing_pass"] = m["me"] if a.move.strip().lower() == "pass" else None
    save_manifest(a.game, m)
    since = append_log(a.game, g, since)
    drive_ai(a.game, m, g, since, out)
    print("\n".join(out))
    print()
    return show(a.game, m, mr, g)


def cmd_note(a) -> int:
    d = game_dir(a.game)
    with open(d / "notes.md", "a", encoding="utf-8", newline="\n") as fh:
        fh.write(f"- {dt.datetime.now().strftime('%H:%M')}: {a.text}\n")
    print("Notiz gespeichert.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new"); n.add_argument("--game", required=True); n.add_argument("--seed", type=int, required=True)
    n.add_argument("--first-player", type=int, default=0, help="wer beginnt (Spielerindex 0/1)")
    n.add_argument("--claude-side", type=int, default=0, help="Claude ist Spieler 0 oder 1")
    n.add_argument("--opponent", default=None, help="Modellname (Default: models/champion.txt) oder 'heuristic'")
    n.add_argument("--spec", default=None, help="Spec-Datei des Gegners (Default models/<opponent>.spec.json)")
    n.add_argument("--sims", type=int, default=400)
    s = sub.add_parser("show"); s.add_argument("--game", required=True)
    mv = sub.add_parser("move"); mv.add_argument("--game", required=True); mv.add_argument("move")
    nt = sub.add_parser("note"); nt.add_argument("--game", required=True); nt.add_argument("text")
    a = ap.parse_args()
    if a.cmd == "new":
        if a.opponent is None:
            a.opponent = (REPO / "models" / "champion.txt").read_text(encoding="utf-8").strip()
        return cmd_new(a)
    if a.cmd == "show":
        return cmd_show(a)
    if a.cmd == "move":
        return cmd_move(a)
    if a.cmd == "note":
        return cmd_note(a)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
