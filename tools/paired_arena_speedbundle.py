"""Gepaarter A/B: ALT (Commit b0c6a9c, Stand VOR dem Stufe-2-Speed-Bündel)
vs. NEU (Haupt-Wheel: #63 Inferenz-Batching + #68 Gumbel-Tiefe-≥1-mctx-Treue
+ #70 R6-Peek-Kosten-Fix).

Phase 2a (2026-07-22) bereitet dies NUR vor -- startbereit, ABSICHTLICH NICHT
gestartet. Phase 2b führt es nach separatem Nutzer-Go aus (parallel laufen
noch 3 Trainings eines anderen Agenten, die train.py nutzen -- dieses Skript
selbst rührt train.py nicht an, kann aber CPU mit den Trainings teilen müssen).

## Design (identisch zum Floor-Shaping-Ablationsmuster, siehe
`evaluations/STATUS.md`, Abschnitt "Floor-Shaping-Signifikanzanalyse
W=0.3 vs. W=0.0"):

- Gepaarte Arena: identische Spiel-Seeds in beiden Armen (`net_arena_match`s
  interne Seed-Ableitung ist deterministisch je Spielindex, siehe
  `paired_arena_arm_worker.py`-Docstring).
- Blöcke à 25 Paare, nach JEDEM vollständigen Block ein kumulativer EXAKTER
  McNemar-Test (kein Zwischen-Block-Abbruch -- vermeidet Interim-Peeking,
  siehe die Sequenzielle-Ehrlichkeit-Diskussion in STATUS.md).
- Stopp bei p<0.05 ODER 150 Paaren.
- Arm ALT = isolierter Git-Worktree `../mosaic-speedbundle-old` (Commit
  b0c6a9c) + eigenes venv (`.venv-old`) -- NICHT `../mosaic-floorablation`
  wiederverwenden, das ist ein ANDERER Ablations-Stand (Nutzer-Auflage).
  Arm NEU = Haupt-Wheel, läuft im selben venv wie DIESES Orchestrator-Skript
  (`sys.executable`) -- also von der Haupt-Repo-Umgebung aus starten, nicht
  aus dem ALT-Worktree/venv heraus.

## Bedingungen

v10_best @ NET_SIMS=400 (flach, DECOUPLE_NET_SIMS_FROM_ACTIONS=true) vs.
Heuristik @ HEUR_SIMS=200 (Basiswert, weiterhin intern `dynamic_sims`-
skaliert wie in `tools/arena.py`s bisherigem HEUR_SIMS=150 -- NUR der Basiswert
ist per Nutzer-Korrektur auf 200 angehoben, neuer Kader-Standard,
`project_..._elo_kader`-Memory: Heuristik@200-Anker + Champion@400 +
prev-Champion@400). Dieser A/B-Lauf IST damit zugleich der ERSTE
Heuristik@200-Referenzpunkt (bisherige Session-Baselines liefen alle mit
HEUR_SIMS=150) -- beim Interpretieren der absoluten Netz-Siegquote
berücksichtigen, nicht direkt mit den alten 22-49%-Referenzen aus
STATUS.md vergleichen (andere Heuristik-Stärke).

## WICHTIGER METHODIK-VORBEHALT

Die Floor-Shaping-Ablation war ein reiner Leaf-Value-Diff OHNE Einfluss auf
den RNG-Verbrauch der Suche -- identische Seeds erzeugten dort über die
GANZE Partie identische Spielverläufe (Beutel-/Fabrikzufall), nur die
Bewertung unterschied sich. #68 (Gumbel-Tiefe-≥1) ändert dagegen, WANN/WIE
OFT die Suche während eines Zugs auf denselben `rng`-Strom zugreift
(Dirichlet-/Gumbel-Ziehungen, Stapel-Peek-Shuffle, Verdeckte-Info-
Determinisierung) -- Suche und tatsächlicher Spielfortschritt (Beutel-/
Fabrik-Zufall) teilen sich in `self_play.rs`/`net_mcts.rs` denselben `rng`.
Gleiche Seeds erzeugen dadurch AB DEM ERSTEN Suchdivergenzpunkt nicht mehr
zwingend identische Spielverläufe zwischen ALT und NEU. Die Paarung ist also
eine Näherung (gleiche STARTBEDINGUNGEN je Index, nicht zwingend identische
Spielverläufe über die ganze Partie) -- für die McNemar-Varianzreduktion
weiterhin sinnvoll (beide Arme sehen zumindest denselben initialen
Spielaufbau/dieselbe Scoring-Tile-Auswahl), aber kein exakter
Ceteris-paribus-Vergleich mehr wie bei der Floor-Ablation. Bei der
Phase-2b-Interpretation berücksichtigen.

## Nutzung (Phase 2b, NICHT jetzt)

    python tools/paired_arena_speedbundle.py

Voraussetzung: `../mosaic-speedbundle-old/.venv-old` existiert und hat das
ALT-Wheel installiert (siehe Phase-2a-Statusbericht) UND dieses Skript wird
mit dem HAUPT-venv-Python gestartet (NEU-Wheel muss `import mosaic_rust`
liefern).
"""
import sys
import json
import time
import subprocess
from pathlib import Path
from math import comb

# Windows-Konsolen (cp1252) koennen die Emoji-Ausgaben sonst nicht kodieren
# (Fund Phase 2b: Crash NACH dem letzten Block, direkt vor der finalen JSON-
# Ausgabe -- alle Daten waren zu dem Zeitpunkt bereits berechnet, nur der
# Abschluss-Print schlug fehl). Gleiches Muster wie tools/arena.py bzw. self_play.py.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
OLD_WORKTREE = BASE_DIR.parent / "mosaic-speedbundle-old"
OLD_PYTHON = OLD_WORKTREE / ".venv-old" / "Scripts" / "python.exe"
WORKER_SCRIPT = Path(__file__).resolve().parent / "paired_arena_arm_worker.py"

MODEL_PATH = str((BASE_DIR / "models" / "alphazero_v10_best.onnx").resolve())
NET_SIMS = 400
HEUR_SIMS = 200            # Kader-Standard-Korrektur (Nutzer-Vorgabe, Phase 2a) -- vorher 150
BLOCK_SIZE = 25
MAX_PAIRS = 150
ALPHA = 0.05
# Phase 2b (2026-07-22): Trainings sind fertig, Maschine frei -- Arme laufen
# ohnehin SEQUENZIELL (kein gleichzeitiger Kontent), daher hier hochgesetzt
# (12 physische/logische Kerne verfuegbar, ein paar fuer Orchestrierung/OS
# freigehalten). Bei erneuter paralleler Systemlast vor einem Re-Run wieder
# senken (siehe Modul-Docstring).
THREADS_PER_ARM = 10
ARM_TIMEOUT_SECS = 3 * 3600


def mcnemar_exact_p(b: int, c: int) -> float:
    """Exakter zweiseitiger McNemar-Test auf den Diskordanz-Zellen (b, c),
    ohne scipy (nicht installiert, siehe Umgebungscheck Phase 2a):
    X ~ Binomial(n=b+c, p=0.5), p = 2*min(P(X<=min(b,c)), P(X>=max(b,c))),
    gedeckelt bei 1.0 -- Standardform des exakten Tests (vgl. R
    `mcnemar.test(..., correct=FALSE)`, exakte Variante)."""
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
    """Führt EINEN Arm für einen Seed-Block per Subprozess aus (siehe
    `paired_arena_arm_worker.py`) -- `python_exe` wählt den Wheel-Stand
    (ALT-venv-Python oder `sys.executable` für NEU)."""
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
    """Orchestriert den vollen gepaarten A/B (siehe Modul-Docstring). Bricht
    NACH einem VOLLSTÄNDIGEN Block ab, sobald der kumulative McNemar-Test
    p<alpha erreicht, oder wenn `max_pairs` Paare gespielt sind."""
    import random
    base_seed = base_seed if base_seed is not None else random.randint(0, 10**9)
    new_wins = old_wins = 0
    b = c = 0  # Diskordanz-Zellen: b = NEU schlägt Heuristik, ALT nicht; c umgekehrt
    done = 0
    block_idx = 0
    print(f"Gepaarter A/B ALT(b0c6a9c) vs NEU(Speed-Bündel) -- v10_best @ NET_SIMS={NET_SIMS} "
          f"vs. Heuristik @ HEUR_SIMS={HEUR_SIMS} (erster Heuristik@200-Referenzpunkt), "
          f"Basis-Seed={base_seed}")
    print(f"  ALT-Python: {OLD_PYTHON}")
    print(f"  NEU-Python: {sys.executable}")
    while done < max_pairs:
        n = min(block_size, max_pairs - done)
        seed = base_seed + block_idx * 1_000_000
        new_results = run_arm(sys.executable, seed, n, "NEU")
        old_results = run_arm(str(OLD_PYTHON), seed, n, "ALT")
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
            print(f"  ⏹️  Signifikant bei p<{alpha} nach {done} Paaren.")
            break
    else:
        print(f"  ⏹️  {max_pairs} Paare erreicht ohne Signifikanz (p={mcnemar_exact_p(b, c):.4f}).")
    return {
        "done": done, "new_wins": new_wins, "old_wins": old_wins,
        "b_new_only": b, "c_old_only": c, "p": mcnemar_exact_p(b, c), "base_seed": base_seed,
        "net_sims": NET_SIMS, "heur_sims": HEUR_SIMS, "model": MODEL_PATH,
    }


if __name__ == "__main__":
    if not OLD_PYTHON.exists():
        raise SystemExit(
            f"❌ ALT-venv-Python nicht gefunden: {OLD_PYTHON}\n"
            "   Erst den ALT-Worktree/venv vorbereiten (siehe Phase-2a-Statusbericht) "
            "oder Pfad in diesem Skript anpassen."
        )
    result = run_paired_ab()
    print(json.dumps(result, indent=2))
