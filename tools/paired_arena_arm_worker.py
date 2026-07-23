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


def main() -> None:
    p = argparse.ArgumentParser(description="Ein Arm des gepaarten Speed-Buendel-A/B")
    p.add_argument("--model", required=True, help="Absoluter Pfad zum ONNX-Modell")
    p.add_argument("--net-sims", type=int, required=True)
    p.add_argument("--heur-sims", type=int, required=True)
    p.add_argument("--n-games", type=int, required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--threads", type=int, default=0)
    p.add_argument("--c", type=float, default=0.3)
    p.add_argument("--c-puct", type=float, default=1.5)
    args = p.parse_args()

    import mosaic_rust as mr  # bewusst hier importiert: welches Wheel geladen wird,
                               # entscheidet allein der Python-Interpreter (--python-exe
                               # der aufrufenden Seite), nicht dieses Skript.

    raw = mr.net_arena_match(
        args.model, net_sims=args.net_sims, heur_sims=args.heur_sims,
        n_games=args.n_games, seed=args.seed, num_threads=args.threads,
        c=args.c, c_puct=args.c_puct,
    )
    # NUR das rohe JSON auf stdout -- der Orchestrator parsed es 1:1.
    sys.stdout.write(raw)


if __name__ == "__main__":
    main()
