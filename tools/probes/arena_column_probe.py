# -*- coding: utf-8 -*-
"""Volle Spalten in der ARENA -- aus den Partie-Logs rekonstruiert.

Nutzer-Anweisung 2026-08-31: *"Ich brauch keine k1 Punkte. Ich will die
Spalten wissen unabhaengig von den Wertungsplatten."* Beides trifft zu:
k1-Punkte sind nicht die Anzahl (das Kriterium zahlt `7*(f/6)^2`), und sie
existieren ueberhaupt nur in Partien, in denen die k1-Platte gezogen wurde --
im v23-Value-Korpus war sie in 2.925 von 8.000 Seiten aktiv. Als Mass fuer
Spaltenbau ist das doppelt untauglich.

**Der Weg fuehrt ueber den Replayer, nicht ueber einen Engine-Umbau**
(Nutzer-Hinweis: "Du kannst es aus den logs rekonstruieren"). Das
Arena-Ergebnis-JSON traegt mit `--log-games` je Partie die vollen Logzeilen;
`analyze_game_log.Replayer` treibt daraus eine `PyGame`-Instanz Zug fuer Zug
und liefert den Endzustand. Aus dessen `score_geo.col_fill` faellt die Zahl
voller Spalten je Seite -- plattenunabhaengig, weil `col_fill` reine
Brettgeometrie ist.

**Die Einschraenkung, die dazugehoert:** Arena-Logs tragen KEINE
`#a`-Aktions-Hinweise (analyze_game_log.load_log-Doku nennt sie ausdruecklich
als Fall ohne Hints), der Replay laeuft also ueber den TEXT-Pfad. Der ist der
fragilere -- genau dort sass der Greedy-Fehler, der am 2026-08-30 behoben
wurde. Deshalb zaehlt diese Sonde divergierende Partien und weist sie aus,
statt sie still zu ueberspringen: eine Quote, die auf einer stillen Teilmenge
beruht, waere schlimmer als keine Zahl.

Aufruf:
    python -X utf8 -u tools/probes/arena_column_probe.py \\
        --artifact evaluations/artifacts/paired_arena_env_<name>.json
    ... --limit 20      # Smoke auf den ersten Partien
"""
import argparse
import json
import os
import pathlib
import statistics as st
import sys
import tempfile
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))
sys.path.insert(0, str(_ROOT / "tools"))

PREREG = "docs/generation_loop.md, Tor 2b (Spalten in der Arena)"


def _games_of(artifact: dict):
    """Gibt [(arm, [partien])] zurueck -- ein- wie mehrarmige Artefakte."""
    g = artifact.get("games")
    if isinstance(g, list):
        return [("(einarmig)", g)]
    if isinstance(g, dict):
        return [(arm, lst) for arm, lst in g.items() if isinstance(lst, list)]
    return []


def _replay_end_state(game: dict, tmp_dir, idx):
    """Replayt EINE Arena-Partie und gibt den Endzustand als dict zurueck.

    Zwei Dinge, die das Arena-Log vom Server-Log unterscheiden und die diese
    Funktion ausgleicht:

    1. **Die Header-Zeile fehlt.** `load_log` erwartet `# {...}` mit
       `players`/`first_player`/`seed`; im Arena-Artefakt stehen dieselben
       Angaben als Felder `names`/`first_player`/`game_seed` NEBEN dem Log
       (genau dafuer wurden sie 2026-08-11 mit `--log-games` eingefuehrt).
       Sie werden hier vorangestellt, nicht erraten.
    2. **Der Replayer liest aus einer Datei**, also wird das Log dorthin
       geschrieben -- billiger als eine Schnittstellen-Aenderung an einem
       Werkzeug, das im Kernbeweis haengt.

    Gefahren wird ueber `analyze_game_log.run` und nicht ueber `Replayer`
    direkt: dort sitzt die Chip-Plan-Reparatur vom 2026-08-30 (greedy
    verbrennt sonst die falschen Chips), und Divergenzen kommen als Rueckgabe
    statt als Ausnahme.
    """
    import analyze_game_log as agl

    header = {"players": game.get("names") or ["A", "B"],
              "first_player": game.get("first_player", 0),
              "seed": game.get("game_seed", 0)}
    path = pathlib.Path(tmp_dir) / f"game_{idx:05d}.log"
    body = "\n".join(game["log"])
    path.write_text("# " + json.dumps(header, ensure_ascii=False) + "\n" + body + "\n",
                    encoding="utf-8", newline="\n")
    rep, _lines, _li, div = agl.run(path, model_path=None, sims=1, c_puct=0.3,
                                    do_oracle=False, limit=None)
    if div:
        raise RuntimeError(f"ReplayDivergence: {div}")
    # Das PyGame-Objekt heisst `g` (analyze_game_log.py:381).
    return json.loads(rep.g.state_json())


def _full_columns(state: dict, player_index: int) -> int:
    """Volle Spalten einer Seite: col_fill == 6, rein geometrisch.

    Zaehlweise wie `tools/corpus_sanity_check.py` (col_fill >= 6) und wie die
    Wahrheit im Motor (scoring.rs: `sf.col_fill[c] == 6`) -- NICHT ueber
    `completed_cols`/`is_col_complete` in board.rs, die heissen so, sind es
    aber nicht (Codepflege-Audit 2026-08-27, Befund 19).
    """
    geo = (state["players"][player_index].get("score_geo") or {})
    return sum(1 for x in (geo.get("col_fill") or []) if x >= 6)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--artifact", required=True,
                    help="paired_arena_env_*.json mit --log-games gefahren")
    ap.add_argument("--limit", type=int, default=0, help="nur die ersten N Partien je Arm")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    t_wall, t_cpu = time.time(), time.process_time()

    artifact = json.loads(pathlib.Path(args.artifact).read_text(encoding="utf-8"))
    arms = _games_of(artifact)
    if not arms:
        print(f"ROT -- {args.artifact} traegt kein `games`-Feld.", file=sys.stderr)
        return 1

    findings = {"prereg": PREREG, "artefakt": os.path.basename(args.artifact), "arme": {}}
    failures = []

    with tempfile.TemporaryDirectory(prefix="arenacol_") as tmp:
        for arm, games in arms:
            games = [g for g in games if g.get("log")]
            if args.limit:
                games = games[:args.limit]
            if not games:
                print(f"  {arm}: keine Partie mit Log -- uebersprungen (fehlt --log-games?)")
                findings["arme"][arm] = {"partien_mit_log": 0}
                continue

            per_name: dict[str, list[int]] = {}
            per_game: list[dict] = []
            ok = diverged = 0
            errors: list[str] = []
            for i, g in enumerate(games):
                try:
                    state = _replay_end_state(g, tmp, i)
                except Exception as e:                      # noqa: BLE001
                    diverged += 1
                    if len(errors) < 3:
                        errors.append(f"{type(e).__name__}: {str(e)[:140]}")
                    continue
                ok += 1
                names = g.get("names") or ["seite0", "seite1"]
                cols = [_full_columns(state, pi) for pi in (0, 1)]
                for pi in (0, 1):
                    per_name.setdefault(names[pi], []).append(cols[pi])
                # Je Partie mitschreiben: nur so laesst sich spaeter GEPAART
                # rechnen (beide Seiten aus DERSELBEN Partie), statt zwei
                # Mittelwerte mit unabhaengigen SEs zu vergleichen.
                per_game.append({"index": i, "seed": g.get("game_seed"),
                                 "names": names, "volle_spalten": cols})
                if (i + 1) % 25 == 0:
                    print(f"  {arm}: {i + 1}/{len(games)} replayt "
                          f"({time.time() - t_wall:.0f}s)", flush=True)

            arm_out = {"partien_mit_log": len(games), "replayt": ok, "divergiert": diverged,
                       "fehler_beispiele": errors, "seiten": {}, "je_partie": per_game}
            for name, vals in sorted(per_name.items()):
                mean = sum(vals) / len(vals)
                se = (st.stdev(vals) / len(vals) ** 0.5) if len(vals) > 1 else None
                arm_out["seiten"][name] = {"n": len(vals), "volle_spalten": mean,
                                           "se": se, "ci95": (1.96 * se) if se else None}
                print(f"  {arm} | {name:28s} volle Spalten {mean:.4f}"
                      + (f" +- {1.96 * se:.4f}" if se else "") + f"  (n={len(vals)})",
                      flush=True)
            if diverged:
                print(f"  {arm}: ACHTUNG {diverged} von {len(games)} Partien nicht "
                      f"replaybar -- die Quote steht auf {ok} Partien", flush=True)
                if ok == 0:
                    failures.append(f"{arm}: keine Partie replaybar")
            findings["arme"][arm] = arm_out

    findings["verdikt"] = "GRUEN" if not failures else "ROT"
    findings["versagt"] = failures
    findings["laufzeit"] = {"wanduhr_s": round(time.time() - t_wall, 2),
                            "cpu_s": round(time.process_time() - t_cpu, 2),
                            "threads": 1, "s_je_partie": None}
    out = args.out or str(_ROOT / "evaluations" / "artifacts" /
                          f"arena_columns_{pathlib.Path(args.artifact).stem}.json")
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(out).write_text(json.dumps(findings, indent=2, ensure_ascii=False),
                                 encoding="utf-8", newline="\n")
    print(f"\nArtefakt: {out}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
