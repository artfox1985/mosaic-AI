# -*- coding: utf-8 -*-
"""Warum divergiert der Replayer beim Kuppelzug? Eine Gegenueberstellung.

ANLASS (2026-09-19): `tools/probes/arena_column_probe.py` scheitert auf den
v30-Gating-Logs an 15,5 bzw. 17,8 Prozent der Partien mit
`ReplayDivergence: kein passender Kuppel-Zug: tile=.. slot=(..) rot=..`
(`PREREG_v30_window.md` par.9). Die bekannte Grenze lag bei rund 1 Prozent, und
die replaybare Teilmenge ist nachweislich NICHT repraesentativ (das Vorzeichen
des Punkte-Margins dreht sich), weshalb Tor 2b bis zur Reparatur unbrauchbar
ist.

WAS ES TUT: spielt die Partien eines Gating-Artefakts nach und druckt fuer die
ersten `--max` divergenten Partien, was an der Bruchstelle GESUCHT wurde und
was `valid_moves` dort tatsaechlich ANBIETET. Genau diese Gegenueberstellung
fehlt in der Fehlermeldung der Sonde.

REINE DIAGNOSE: aendert nichts, misst keine Staerke, faellt kein Verdikt.
EXKLUSIV fahren (die Sonde selbst braucht rund 100 s je Seed).

    python -X utf8 -u tools/probes/replay_divergence_diagnosis.py \
        evaluations/artifacts/gating_v30-b01_vs_v29-b09_s20261300.json --max 3
"""
import argparse
import io
import json
import pathlib
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "engine" / "py"))
sys.path.insert(0, str(REPO))


def schreibe_log(game, tmp_dir, idx):
    """Arena-Log in eine Datei, mit vorangestelltem Header.

    Bauform und Begruendung wortgleich aus `tools/probes/arena_column_probe.py`
    (`_replay_end_state`): das Arena-Artefakt traegt `names`, `first_player` und
    `game_seed` NEBEN dem Log, waehrend `load_log` sie als `# {...}`-Kopfzeile
    erwartet.
    """
    header = {"players": game.get("names") or ["A", "B"],
              "first_player": game.get("first_player", 0),
              "seed": game.get("game_seed", 0)}
    path = pathlib.Path(tmp_dir) / ("game_%05d.log" % idx)
    text = "# " + json.dumps(header, ensure_ascii=False) + "\n" + "\n".join(game["log"]) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("artifact", help="Gating-Artefakt mit --log-games")
    ap.add_argument("--max", type=int, default=3, help="wieviele divergente Partien berichten")
    a = ap.parse_args()

    import analyze_game_log as agl

    d = json.load(io.open(a.artifact, encoding="utf-8"))
    games = [g for g in (d.get("games") or []) if g.get("log")]
    print("Artefakt: %s   Partien mit Log: %d" % (a.artifact, len(games)), flush=True)

    berichtet = 0
    divergent = 0
    with tempfile.TemporaryDirectory() as tmp:
        for i, g in enumerate(games):
            path = schreibe_log(g, tmp, i)
            # `run` wirft NICHT, sondern gibt die Divergenz zurueck (Doku dort).
            rep, lines, li, div = agl.run(path, model_path=None, sims=1, c_puct=0.3,
                                          do_oracle=False, limit=None)
            if not div or "kein passender Kuppel-Zug" not in str(div):
                continue
            divergent += 1
            if berichtet >= a.max:
                continue
            berichtet += 1
            print("\n=== Partie %d, Bruch bei Zeile %s: %s" % (i, li, div), flush=True)
            st = json.loads(rep.g.state_json())
            vm = [m for m in st["valid_moves"]
                  if m["type"] in ("dome_stack_choose", "dome_display", "dome_stack_peek")]
            print("   pending_stack_draw: %d Platten" % len(st.get("pending_stack_draw") or []),
                  flush=True)
            print("   angeboten (%d Kuppel-/Peek-Zuege):" % len(vm), flush=True)
            for m in vm[:12]:
                if m["type"] == "dome_stack_peek":
                    print("      dome_stack_peek", flush=True)
                else:
                    print("      %s: tile=%s slot=(%s,%s) rot=%s"
                          % (m["type"], m.get("chosen_id", m.get("tile_id")),
                             m.get("slot_row"), m.get("slot_col"), m.get("rotation")), flush=True)
            if len(vm) > 12:
                print("      ... und %d weitere" % (len(vm) - 12), flush=True)
    print("\nDivergente Partien: %d von %d" % (divergent, len(games)), flush=True)


if __name__ == "__main__":
    main()
