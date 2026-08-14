"""Ein-Arm-Worker für den gepaarten Speed-Bündel-A/B (Phase 2a/2b,
Task #63/#68/#70-Validierung, 2026-07-22).

Wird per `python paired_arena_arm_worker.py ...` in JEWEILS EINEM
venv/Wheel-Stand aufgerufen (ALT = `../mosaic-speedbundle-old/.venv-old`,
NEU = Haupt-venv) -- reiner dünner CLI-Wrapper um
`mosaic_rust.net_arena_match`, druckt das rohe JSON auf stdout (ein
`[{scores, winner, steps, total_floor, floor_per_round}, ...]`-Array, gleiches
Format wie `tools/arena.py`s `run_net_arena`).

Der Orchestrator (`paired_arena_speedbundle.py`) ruft dies für BEIDE Arme mit
IDENTISCHEM `--seed` auf, damit `net_arena_match`s interne Pro-Spiel-Seed-
Ableitung (siehe `self_play.rs::run_net_arena_match`) in beiden Armen
dieselbe Ausgangs-Sequenz erzeugt -- Voraussetzung für die gepaarte
McNemar-Auswertung (siehe Orchestrator-Docstring für den Methodik-Vorbehalt:
gleiche Startbedingungen je Index, nicht zwingend über die ganze Partie
identische Spielverläufe, weil #68 die RNG-Verbrauchsreihenfolge während der
Suche ändert).
"""
import sys
import json
import argparse
from pathlib import Path

# 2026-08-11: PFLICHT, seit `--log-games` existiert. Das rohe JSON traegt dann
# die Partie-Logs, und die enthalten Pfeile und Emoji ("→", "⭐", "🏆").
# Windows-Default fuer stdout ist cp1252 -> `sys.stdout.write(raw)` stirbt mit
# `UnicodeEncodeError: 'charmap' codec can't encode character '→'`.
# Dritter Vorfall derselben Familie an einem Tag (vgl. Commit 2a6abee: dort war
# die LESE-Seite betroffen, hier ist es die SCHREIB-Seite).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def parse_seeds(value: str) -> list[int]:
    """Explizite Pro-Partie-Seed-Liste fuer `--seeds` (Plattenkopf-Versuch,
    `PREREG_plate_head.md`, 2026-08-11): entweder KOMMAGETRENNT ODER ein Pfad
    zu einer Datei mit einer Zahl je Zeile (Leerzeilen und `#`-Kommentare
    ignoriert -- passend zum `tools/seed_selection_plates.py`-Ausgabeformat).
    Datei-Form gewaehlt fuer den grossen Fall (60 Seeds waeren als ein
    CLI-Argument unhandlich); komma-Form fuer den kleinen Funktionstest.
    `tools/paired_arena_env_ab.py` importiert dieselbe Funktion (kein
    Doppel-Parsing -- Orchestrator und Worker muessen synchron bleiben)."""
    p = Path(value)
    if p.is_file():
        lines = p.read_text(encoding="utf-8").splitlines()
        return [int(ln.strip()) for ln in lines if ln.strip() and not ln.strip().startswith("#")]
    return [int(x.strip()) for x in value.split(",") if x.strip()]


def main() -> None:
    p = argparse.ArgumentParser(description="Ein Arm des gepaarten Speed-Buendel-A/B")
    p.add_argument("--model", required=True, help="Absoluter Pfad zum ONNX-Modell")
    p.add_argument("--net-sims", type=int, required=True)
    p.add_argument("--heur-sims", type=int, required=True)
    # 2026-08-11: nicht mehr required -- bei gesetztem `--seeds` folgt n_games
    # aus der Listenlaenge (siehe `net_arena_match`-Dokumentation), das hier
    # ist dann nur noch informativ. Ohne `--seeds` weiterhin Pflicht (geprueft
    # unten), sonst waere das Bestandsverhalten stillschweigend unterlaufen.
    p.add_argument("--n-games", type=int, default=None)
    p.add_argument("--seed", type=int, default=None,
                   help="Basis-Seed fuer die abgeleitete Formel (ignoriert, wenn --seeds gesetzt ist)")
    p.add_argument("--seeds", type=str, default=None,
                   help="Explizite Pro-Partie-Seeds, kommagetrennt ODER Datei-Pfad "
                        "(eine Zahl je Zeile) -- ersetzt --seed UND --n-games "
                        "(Partie i bekommt seeds[i], n_games = Listenlaenge)")
    p.add_argument("--threads", type=int, default=0)
    p.add_argument("--c", type=float, default=0.3)
    p.add_argument("--c-puct", type=float, default=1.5)
    # 2026-08-11: durchgereicht an `net_arena_match`s `log_games` (Commit
    # 9dfeb16). AUS = Bestandsverhalten, das Ergebnis-JSON ist dann exakt wie
    # vorher. AN = je Partie kommen `game_seed`, `first_player`, `names` und
    # `log` (volle GameState::log-Zeilenliste im Server-Wortlaut) dazu, damit
    # `tools/analyze_game_log.py` die VERHALTENS-Zahlen aus denselben Partien
    # ziehen kann wie die Siegquote. Ohne das liefert ein Sweep nur Siegquoten
    # und die Verhaltensmessung braeuchte einen zweiten Lauf ueber dieselben
    # Stunden (siehe PREREG_scoring_plate_injection.md, Vorbedingung 2).
    p.add_argument("--log-games", action="store_true",
                   help="Partie-Logs im Ergebnis-JSON mitfuehren (Default aus)")
    args = p.parse_args()

    seeds = parse_seeds(args.seeds) if args.seeds else None
    if seeds is None:
        if args.seed is None or args.n_games is None:
            p.error("ohne --seeds sind --seed und --n-games weiterhin Pflicht")
    elif args.n_games is not None and args.n_games != len(seeds):
        print(f"WARNUNG: --n-games {args.n_games} weicht von --seeds-Laenge "
              f"{len(seeds)} ab -- die Listenlaenge gewinnt (siehe "
              f"net_arena_match-Dokumentation).", file=sys.stderr)

    import mosaic_rust as mr  # bewusst hier importiert: welches Wheel geladen wird,
                               # entscheidet allein der Python-Interpreter (--python-exe
                               # der aufrufenden Seite), nicht dieses Skript.

    raw = mr.net_arena_match(
        args.model, net_sims=args.net_sims, heur_sims=args.heur_sims,
        n_games=(args.n_games if args.n_games is not None else 0),
        seed=args.seed, num_threads=args.threads,
        c=args.c, c_puct=args.c_puct, log_games=args.log_games, seeds=seeds,
    )
    # NUR das rohe JSON auf stdout -- der Orchestrator parsed es 1:1.
    sys.stdout.write(raw)


if __name__ == "__main__":
    main()
