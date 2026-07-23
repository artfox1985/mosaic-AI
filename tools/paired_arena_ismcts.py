"""Gepaarter A/B fuer Task #65 (ISMCTS-Mehrfach-Determinisierung): ALT
(NUM_DETERMINIZATIONS=1, exaktes Alt-Verhalten -- Einzel-Determinisierung
pro Zugsuche) vs. NEU (NUM_DETERMINIZATIONS=3, klassisches ISMCTS -- drei
unabhaengige Welten, Sims-Budget gesplittet, completed-Q-Politik ueber die
Welten gemittelt).

## Design (identisch zum Speed-Buendel-A/B-Muster, siehe
`tools/paired_arena_speedbundle.py`):

- Gepaarte Arena: identische Spiel-Seeds in beiden Armen (`net_arena_match`s
  interne Seed-Ableitung ist deterministisch je Spielindex, siehe
  `paired_arena_arm_worker.py`-Docstring).
- Bloecke à 25 Paare, nach JEDEM vollstaendigen Block ein kumulativer EXAKTER
  McNemar-Test (kein Zwischen-Block-Abbruch).
- Stopp bei p<0.05 ODER 150 Paaren.
- Arm ALT (n=1) = isolierter Git-Worktree `../mosaic-ismcts-n1` (Commit
  8e4b3b9 = b5c59ff + Task-#65-Implementierung mit `NUM_DETERMINIZATIONS`
  lokal auf 1 zurueckgesetzt, uncommitted) + eigenes venv (`.venv-n1`).
  Arm NEU (n=3) = Haupt-Wheel (`NUM_DETERMINIZATIONS=3`, unveraendert aus
  dem Task-#65-Quellcode), laeuft im selben venv wie DIESES
  Orchestrator-Skript (`sys.executable`).

## Bedingungen

v10_best @ NET_SIMS=400 (flach, DECOUPLE_NET_SIMS_FROM_ACTIONS=true) vs.
Heuristik @ HEUR_SIMS=200 (Elo-Kader-Standard, siehe
`paired_arena_speedbundle.py`). Bei ALT wird das volle NET_SIMS=400-Budget
auf 1 Welt gefahren (exakt wie vor Task #65); bei NEU auf 3 Welten
gesplittet (134/133/133, siehe `split_sims_across_worlds`).

## WICHTIGER METHODIK-VORBEHALT (RNG-Vorbehalt, wie beim Speed-Buendel-A/B)

Beide Arme teilen sich in `self_play.rs`/`net_mcts.rs` denselben `rng`-Strom
zwischen Suche und tatsächlichem Spielfortschritt (Beutel-/Fabrik-Zufall).
ALT (1 Baum, volles Budget) und NEU (3 Baeume, je 1/3 Budget UND je eine
eigene Wurzel-Determinisierungs-Ziehung) verbrauchen den `rng`-Strom pro Zug
unterschiedlich oft/unterschiedlich -- gleiche Start-Seeds erzeugen daher AB
DEM ERSTEN Suchdivergenzpunkt nicht zwingend identische Spielverlaeufe
zwischen den Armen. Die Paarung ist eine Naeherung (gleiche
STARTBEDINGUNGEN je Index), kein exakter Ceteris-paribus-Vergleich --
McNemar bleibt trotzdem sinnvoll fuer die Varianzreduktion.

## Nutzung

    python tools/paired_arena_ismcts.py

Voraussetzung: `../mosaic-ismcts-n1/.venv-n1` existiert mit dem ALT-Wheel
(NUM_DETERMINIZATIONS=1) installiert, UND dieses Skript wird mit dem
HAUPT-venv-Python gestartet (NEU-Wheel, NUM_DETERMINIZATIONS=3, muss
`import mosaic_rust` liefern).
"""
import sys
import json
import time
import subprocess
from pathlib import Path
from math import comb

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
OLD_WORKTREE = BASE_DIR.parent / "mosaic-ismcts-n1"
OLD_PYTHON = OLD_WORKTREE / ".venv-n1" / "Scripts" / "python.exe"
WORKER_SCRIPT = Path(__file__).resolve().parent / "paired_arena_arm_worker.py"

MODEL_PATH = str((BASE_DIR / "models" / "alphazero_v10_best.onnx").resolve())
NET_SIMS = 400
HEUR_SIMS = 200
BLOCK_SIZE = 25
MAX_PAIRS = 150
ALPHA = 0.05
THREADS_PER_ARM = 10
ARM_TIMEOUT_SECS = 3 * 3600


def mcnemar_exact_p(b: int, c: int) -> float:
    """Exakter zweiseitiger McNemar-Test auf den Diskordanz-Zellen (b, c),
    ohne scipy: X ~ Binomial(n=b+c, p=0.5), p = 2*min(P(X<=min(b,c)),
    P(X>=max(b,c))), gedeckelt bei 1.0."""
    n = b + c
    if n == 0:
        return 1.0
    lo, hi = min(b, c), max(b, c)
    p_le = sum(comb(n, k) for k in range(0, lo + 1)) / (2 ** n)
    p_ge = sum(comb(n, k) for k in range(hi, n + 1)) / (2 ** n)
    return min(1.0, 2 * min(p_le, p_ge))


def run_arm(python_exe: str, seed: int, n_games: int, label: str,
            net_sims: int = NET_SIMS, heur_sims: int = HEUR_SIMS,
            threads: int = THREADS_PER_ARM) -> list[dict]:
    t0 = time.time()
    proc = subprocess.run(
        [python_exe, str(WORKER_SCRIPT),
         "--model", MODEL_PATH, "--net-sims", str(net_sims), "--heur-sims", str(heur_sims),
         "--n-games", str(n_games), "--seed", str(seed), "--threads", str(threads)],
        capture_output=True, text=True, timeout=ARM_TIMEOUT_SECS,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Arm {label} (Seed {seed}, n={n_games}) fehlgeschlagen "
                            f"(rc={proc.returncode}): {proc.stderr[-2000:]}")
    dur = time.time() - t0
    print(f"  [{label}] Block Seed={seed} n={n_games} fertig in {dur:.1f}s ({n_games/dur:.2f} Spiele/s)",
          flush=True)
    return json.loads(proc.stdout)


def run_paired_ab(max_pairs: int = MAX_PAIRS, block_size: int = BLOCK_SIZE,
                   alpha: float = ALPHA, base_seed: int | None = None) -> dict:
    import random
    base_seed = base_seed if base_seed is not None else random.randint(0, 10**9)
    new_wins = old_wins = 0
    b = c = 0  # Diskordanz-Zellen: b = NEU(n=3) schlaegt Heuristik, ALT(n=1) nicht; c umgekehrt
    done = 0
    block_idx = 0
    print(f"Gepaarter A/B ALT(NUM_DETERMINIZATIONS=1) vs NEU(NUM_DETERMINIZATIONS=3) -- "
          f"v10_best @ NET_SIMS={NET_SIMS} vs. Heuristik @ HEUR_SIMS={HEUR_SIMS}, Basis-Seed={base_seed}")
    print(f"  ALT-Python (n=1): {OLD_PYTHON}")
    print(f"  NEU-Python (n=3): {sys.executable}")
    while done < max_pairs:
        n = min(block_size, max_pairs - done)
        seed = base_seed + block_idx * 1_000_000
        new_results = run_arm(sys.executable, seed, n, "NEU(n=3)")
        old_results = run_arm(str(OLD_PYTHON), seed, n, "ALT(n=1)")
        for i in range(n):
            new_won = new_results[i]["winner"] == 0
            old_won = old_results[i]["winner"] == 0
            new_wins += int(new_won)
            old_wins += int(old_won)
            if new_won and not old_won:
                b += 1
            elif old_won and not new_won:
                c += 1
        done += n
        block_idx += 1
        p = mcnemar_exact_p(b, c)
        print(f"  Kumulativ nach {done} Paaren: NEU(n=3) {new_wins}:{old_wins} ALT(n=1) | "
              f"diskordant b={b} c={c} | McNemar p={p:.4f}", flush=True)
        if p < alpha:
            print(f"  Signifikant bei p<{alpha} nach {done} Paaren.")
            break
    else:
        print(f"  {max_pairs} Paare erreicht ohne Signifikanz (p={mcnemar_exact_p(b, c):.4f}).")
    return {
        "done": done, "new_wins": new_wins, "old_wins": old_wins,
        "b_new_only": b, "c_old_only": c, "p": mcnemar_exact_p(b, c), "base_seed": base_seed,
        "net_sims": NET_SIMS, "heur_sims": HEUR_SIMS, "model": MODEL_PATH,
    }


if __name__ == "__main__":
    if not OLD_PYTHON.exists():
        raise SystemExit(
            f"ALT-venv-Python nicht gefunden: {OLD_PYTHON}\n"
            "   Erst den ALT-Worktree/venv vorbereiten oder Pfad in diesem Skript anpassen."
        )
    result = run_paired_ab()
    print(json.dumps(result, indent=2))
    out_path = BASE_DIR / "evaluations" / "paired_arena_ismcts_result.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Ergebnis gespeichert: {out_path}")
