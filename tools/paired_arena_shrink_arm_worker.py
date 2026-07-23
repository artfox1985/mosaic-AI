"""Ein-Arm-Worker fuer den Task-#78-Value-Shrinkage-A/B (VALUE_SHRINK_ENABLED
false vs. true, 2026-07-23).

Anders als `paired_arena_arm_worker.py` (Netz vs. Heuristik, `net_arena_match`)
spielt dieser Worker Netz vs. Netz (`net_vs_net_arena_match`): Champion
`v12b_lr_best` (Brett 0) gegen den Referenzgegner `v12_best` (Brett 1), beide
@ derselben Sims-Zahl -- Sensitivitaetsgegner nah genug am Champion, um eine
etwaige Staerkeaenderung durch die rundenabhaengige Value-Shrinkage sichtbar
zu machen.

Wird per `python paired_arena_shrink_arm_worker.py ...` in JEWEILS EINEM
Wheel-Stand aufgerufen -- OFF-Arm = Wheel-Build mit `VALUE_SHRINK_ENABLED=
false` (Ist-Zustand), ON-Arm = Wheel-Build mit `VALUE_SHRINK_ENABLED=true`
(nach Toggle-Flip + Rebuild, GLEICHES venv, sequenziell nacheinander, kein
Worktree noetig, weil die beiden Arme nie gleichzeitig laufen muessen). Der
Orchestrator (nicht dieses Skript) ruft dies zweimal mit IDENTISCHEM `--seed`
und `--n-games` auf, damit `net_vs_net_arena_match`s interne Pro-Spiel-Seed-
Ableitung (identisch zu `net_arena_match`/`arena_match`, siehe
`self_play.rs::run_net_vs_net_arena` + zugehoeriger Determinismus-Test) in
beiden Armen dieselbe Spiel-Sequenz erzeugt -- Voraussetzung fuer die
gepaarte Auswertung (Spielindex i: OFF-Ergebnis vs. ON-Ergebnis).

Champion bleibt in BEIDEN Armen auf Brett 0 (`model_a`) -- es geht hier NICHT
um Modell-A-vs-B-Fairness (dafuer gaebe es das Brett-Tausch-Muster aus
`paired_gating.py`), sondern um die Frage "aendert der Shrink-Toggle, ob der
Champion auf DENSELBEN Startbedingungen gewinnt" -- die Brettzuordnung ist
zwischen den Armen ohnehin konstant, ein Brett-Bias faellt daher aus der
Paarung heraus.

Druckt das rohe JSON auf stdout (ein `[{scores, winner, ...}, ...]`-Array,
`winner==0` bedeutet Champion gewinnt).
"""
import sys
import json
import argparse


def main() -> None:
    p = argparse.ArgumentParser(description="Ein Arm des Task-#78-Value-Shrinkage-A/B (Netz vs. Netz)")
    p.add_argument("--model-champion", required=True, help="Absoluter Pfad zum Champion-ONNX (Brett 0)")
    p.add_argument("--model-opponent", required=True, help="Absoluter Pfad zum Referenzgegner-ONNX (Brett 1)")
    p.add_argument("--sims", type=int, required=True, help="Sims fuer BEIDE Seiten")
    p.add_argument("--n-games", type=int, required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--threads", type=int, default=0)
    p.add_argument("--c-puct", type=float, default=1.5)
    args = p.parse_args()

    import mosaic_rust as mr  # bewusst hier importiert: welches Wheel geladen wird,
                               # entscheidet allein der Python-Interpreter (--python-exe
                               # der aufrufenden Seite), nicht dieses Skript.

    raw = mr.net_vs_net_arena_match(
        args.model_champion, args.model_opponent,
        sims_a=args.sims, sims_b=args.sims, n_games=args.n_games, seed=args.seed,
        num_threads=args.threads, c_puct_a=args.c_puct, c_puct_b=args.c_puct,
    )
    # NUR das rohe JSON auf stdout -- der Orchestrator parsed es 1:1.
    sys.stdout.write(raw)


if __name__ == "__main__":
    main()
