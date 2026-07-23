"""Gepaarter A/B fuer die round5-Knoten-primaer-Umstellung (Determinismus-Fix,
Nachfolger der Untersuchung "Prozessgrenzen-Nichtdeterminismus geklaert",
2026-07-22): ALT (round5::TIME_BUDGET=150ms als de-facto-Cutoff, Commit
5cb4f56) vs. NEU (round5::NODE_BUDGET=200 primaer, TIME_BUDGET=5s
Not-Deckel, Commit 9312be0).

Die Umstellung betrifft die LIVE-Runde-5-Zugwahl BEIDER Spieler
(`round5::choose_action` wird von mcts.rs UND net_mcts.rs gerufen) --
erwartet wird KEIN Staerkeunterschied (Rechenparitaet: NODE_BUDGET=200 ~
p75 dessen, was 150ms real erreichten), der A/B ist eine GEGENPROBE, dass
der Determinismus-Gewinn nicht mit Spielstaerke bezahlt wird.

## Design (identisch zum ISMCTS-/Speed-Buendel-A/B-Muster, siehe
`evaluations/paired_arena_ismcts.py`):

- Gepaarte Arena: identische Spiel-Seeds in beiden Armen.
- Bloecke a 25 Paare, nach JEDEM vollstaendigen Block ein kumulativer
  EXAKTER McNemar-Test (kein Zwischen-Block-Abbruch).
- Stopp bei p<0.05 ODER 150 Paaren.
- Arm ALT = Worktree `.claude/worktrees/round5-alt` (detached @ 5cb4f56)
  + venv `.venv-r5alt`; Arm NEU = Worktree
  `.claude/worktrees/round5-node-budget` (9312be0) + venv `.venv-r5neu`.
  BEIDE Arme explizit per venv-Pfad (kein sys.executable-Arm), das Skript
  selbst kann mit jedem Python laufen.

## Bedingungen

v10_best @ NET_SIMS=400 (Elo-Kader-Standard) vs. Heuristik @ HEUR_SIMS=200.
RNG-Vorbehalt wie bei den Vorgaenger-A/Bs: gleiche Startbedingungen je
Index, ab dem ersten abweichenden Runde-5-Zug divergieren die Verlaeufe --
Paarung als Varianzreduktion, kein exakter Ceteris-paribus-Vergleich.

## Nutzung

    python evaluations/paired_arena_round5.py
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

BASE_DIR = Path(__file__).resolve().parent.parent  # Worktree round5-node-budget
MAIN_REPO = Path(r"D:\Archiv\Documents\Projekte\mosaic-AI")
OLD_WORKTREE = MAIN_REPO / ".claude" / "worktrees" / "round5-alt"
OLD_PYTHON = OLD_WORKTREE / ".venv-r5alt" / "Scripts" / "python.exe"
NEW_PYTHON = BASE_DIR / ".venv-r5neu" / "Scripts" / "python.exe"
WORKER_SCRIPT = Path(__file__).resolve().parent / "paired_arena_arm_worker.py"

# Modelle liegen nur im Hauptrepo (models/ ist nicht versioniert).
MODEL_PATH = str((MAIN_REPO / "models" / "alphazero_v10_best.onnx").resolve())
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
    b = c = 0  # Diskordanz: b = NEU schlaegt Heuristik, ALT nicht; c umgekehrt
    done = 0
    block_idx = 0
    print(f"Gepaarter A/B ALT(150ms-Wanduhr, 5cb4f56) vs NEU(NODE_BUDGET=200, 9312be0) -- "
          f"v10_best @ NET_SIMS={NET_SIMS} vs. Heuristik @ HEUR_SIMS={HEUR_SIMS}, Basis-Seed={base_seed}")
    print(f"  ALT-Python: {OLD_PYTHON}")
    print(f"  NEU-Python: {NEW_PYTHON}")
    while done < max_pairs:
        n = min(block_size, max_pairs - done)
        seed = base_seed + block_idx * 1_000_000
        new_results = run_arm(str(NEW_PYTHON), seed, n, "NEU(node200)")
        old_results = run_arm(str(OLD_PYTHON), seed, n, "ALT(150ms)")
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
        print(f"  Kumulativ nach {done} Paaren: NEU {new_wins}:{old_wins} ALT | "
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
    for exe, name in [(OLD_PYTHON, "ALT"), (NEW_PYTHON, "NEU")]:
        if not exe.exists():
            raise SystemExit(f"{name}-venv-Python nicht gefunden: {exe}")
    result = run_paired_ab()
    print(json.dumps(result, indent=2))
    out_path = Path(__file__).resolve().parent / "paired_arena_round5_result.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Ergebnis gespeichert: {out_path}")
