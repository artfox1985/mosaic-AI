"""Gepaarter A/B fuer Task #78 (v12c Value-Shrinkage-Toggle, 2026-07-23):
`VALUE_SHRINK_ENABLED=false` (Ist-Zustand, Arm OFF) vs. `=true` mit den
frisch rekalibrierten `VALUE_SHRINK_PER_ROUND`-Gewichten (Arm ON).

## Warum kein Worktree/Zweit-venv (anders als `paired_arena_ismcts.py`/
`paired_arena_round5.py`)

`VALUE_SHRINK_ENABLED` ist eine Compile-Zeit-Konstante -- Shrink-ON und -OFF
koennen nie im selben Prozess gegeneinander spielen. Anders als bei den
ISMCTS-/round5-A/Bs muessen die beiden Arme hier aber NICHT gleichzeitig
laufen (kein Zeitdruck durch einen parallel laufenden Self-Play-Batch) --
deshalb genuegt ein EINZIGES venv, sequenziell nacheinander bespielt: erst
Arm OFF (aktueller Wheel-Stand), dann Quellcode-Flip + Rebuild, dann Arm ON,
im selben venv. Jeder Arm ist ein eigener Skript-Aufruf (frischer Python-
Prozess je Arm-Lauf), damit garantiert das WHEEL zum Zeitpunkt des Aufrufs
geladen wird, das gerade `pip install --force-reinstall` erzeugt hat (ein
bereits laufender Python-Prozess wuerde das alte Wheel im Speicher behalten).

## Design

Champion `v12b_lr_best` (Brett 0, `net_vs_net_arena_match`) gegen
Referenzgegner `v12_best` (Brett 1) -- naher, sensitiver Gegner (Elo 1051 vs.
943), beide @400 Sims, deterministische Arena. IDENTISCHE Seeds `S` in beiden
Armen (`net_vs_net_arena_match`s interne Pro-Spiel-Seed-Ableitung ist
deterministisch aus `seed + i*const`, siehe `paired_arena_shrink_arm_worker.py`-
Docstring) -- Spielindex `i` hat in Arm OFF und Arm ON dieselben
Startbedingungen. Ausgewertet wird PAARWEISE: Spiel `i` in Arm OFF vs. Spiel
`i` in Arm ON, `winner==0` = Champion gewinnt.

  - `b` = Champion gewinnt in ON, verliert in OFF (Beleg FUER den Shrink-Toggle)
  - `c` = Champion gewinnt in OFF, verliert in ON (Beleg GEGEN den Toggle)
  - Konkordant (beide gleich) traegt nicht zum Vorzeichentest bei.

Exakter zweiseitiger McNemar-Test auf (b, c) (gleiche Formel wie
`paired_arena_ismcts.py`/`paired_arena_round5.py`/`paired_gating.py`).

Evidenzregel (Auftrag, fest vereinbart): NUR bei p<0.05 UND Vorteil fuer ON
bleibt der Toggle an. 100 Spiele je Arm (200 gesamt) als Erstmessung, KEIN
sequenzielles Nachziehen -- fixed-n, kein SPRT (reine Sensitivitaetsmessung,
keine Champion-Gating-Entscheidung).

## Nutzung

    # Arm OFF (nach Rekalibrierungs-Commit, aktueller Wheel-Stand):
    python tools/paired_arena_shrink_ab.py --run-arm off --seed <S> --n-games 100

    # ... dann VALUE_SHRINK_ENABLED=true setzen, cargo test --release, Wheel neu bauen ...

    # Arm ON (identischer Seed):
    python tools/paired_arena_shrink_ab.py --run-arm on --seed <S> --n-games 100

    # Zusammenfuehren + Statistik:
    python tools/paired_arena_shrink_ab.py --combine
"""
import sys
import os
import json
import time
import argparse
import subprocess
from pathlib import Path
from math import comb

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
WORKER_SCRIPT = Path(__file__).resolve().parent / "paired_arena_shrink_arm_worker.py"
EVAL_DIR = BASE_DIR / "evaluations"

MODEL_CHAMPION = str((BASE_DIR / "models" / "alphazero_v12b_lr_best.onnx").resolve())
MODEL_OPPONENT = str((BASE_DIR / "models" / "alphazero_v12_best.onnx").resolve())
SIMS = 400
C_PUCT = 1.5
DEFAULT_N_GAMES = 100
DEFAULT_BLOCK_SIZE = 25
DEFAULT_THREADS = 10
ARM_TIMEOUT_SECS = 3 * 3600


def mcnemar_exact_p(b: int, c: int) -> float:
    """Exakter zweiseitiger McNemar-Test -- identische Formel wie in
    `paired_arena_ismcts.py`/`paired_arena_round5.py`/`paired_gating.py`."""
    n = b + c
    if n == 0:
        return 1.0
    lo, hi = min(b, c), max(b, c)
    p_le = sum(comb(n, k) for k in range(0, lo + 1)) / (2 ** n)
    p_ge = sum(comb(n, k) for k in range(hi, n + 1)) / (2 ** n)
    return min(1.0, 2 * min(p_le, p_ge))


def run_arm(arm: str, seed: int, n_games: int, block_size: int, threads: int) -> dict:
    """Spielt einen Arm (OFF oder ON) in Bloecken, Champion IMMER auf Brett 0.
    Gibt {"games": [...alle Einzelspielergebnisse in Original-Reihenfolge...]} zurueck
    und speichert das Rohergebnis nach evaluations/paired_arena_shrink_<arm>_raw.json."""
    label = arm.upper()
    all_games: list[dict] = []
    done = 0
    block_idx = 0
    print(f"Arm {label}: Champion={os.path.basename(MODEL_CHAMPION)} (Brett 0) vs. "
          f"Gegner={os.path.basename(MODEL_OPPONENT)} (Brett 1) @ sims={SIMS}, "
          f"Basis-Seed={seed}, n_games={n_games}, Bloecke a {block_size}", flush=True)
    while done < n_games:
        n = min(block_size, n_games - done)
        block_seed = seed + block_idx * 1_000_000
        t0 = time.time()
        proc = subprocess.run(
            [sys.executable, str(WORKER_SCRIPT),
             "--model-champion", MODEL_CHAMPION, "--model-opponent", MODEL_OPPONENT,
             "--sims", str(SIMS), "--n-games", str(n), "--seed", str(block_seed),
             "--threads", str(threads), "--c-puct", str(C_PUCT)],
            capture_output=True, text=True, timeout=ARM_TIMEOUT_SECS,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Arm {label} Block {block_idx} (Seed={block_seed}, n={n}) "
                                f"fehlgeschlagen (rc={proc.returncode}): {proc.stderr[-2000:]}")
        block_games = json.loads(proc.stdout)
        all_games.extend(block_games)
        dur = time.time() - t0
        wins = sum(1 for g in block_games if g["winner"] == 0)
        done += n
        block_idx += 1
        cum_wins = sum(1 for g in all_games if g["winner"] == 0)
        print(f"  [{label}] Block {block_idx} (Seed={block_seed}, n={n}, {dur:.1f}s, "
              f"{n/dur:.2f} Spiele/s): Block-Champion-Siege {wins}/{n} | "
              f"kumulativ {cum_wins}/{done}", flush=True)

    result = {
        "arm": arm, "base_seed": seed, "n_games": n_games, "block_size": block_size,
        "sims": SIMS, "c_puct": C_PUCT, "model_champion": MODEL_CHAMPION,
        "model_opponent": MODEL_OPPONENT, "games": all_games,
    }
    out_path = EVAL_DIR / f"paired_arena_shrink_{arm}_raw.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    champ_wins = sum(1 for g in all_games if g["winner"] == 0)
    print(f"Arm {label} fertig: Champion {champ_wins}:{n_games - champ_wins} Gegner "
          f"({n_games} Spiele). Rohergebnis: {out_path}", flush=True)
    return result


def combine() -> dict:
    off_path = EVAL_DIR / "paired_arena_shrink_off_raw.json"
    on_path = EVAL_DIR / "paired_arena_shrink_on_raw.json"
    off = json.loads(off_path.read_text(encoding="utf-8"))
    on = json.loads(on_path.read_text(encoding="utf-8"))

    if off["base_seed"] != on["base_seed"] or off["n_games"] != on["n_games"]:
        raise SystemExit(
            f"Arm-Rohergebnisse nicht paarungskompatibel: OFF seed={off['base_seed']} "
            f"n={off['n_games']} vs. ON seed={on['base_seed']} n={on['n_games']}"
        )
    n = off["n_games"]
    off_games, on_games = off["games"], on["games"]

    off_wins = on_wins = 0
    b = c = concordant_both_win = concordant_both_lose = 0
    for i in range(n):
        off_won = off_games[i]["winner"] == 0
        on_won = on_games[i]["winner"] == 0
        off_wins += int(off_won)
        on_wins += int(on_won)
        if on_won and not off_won:
            b += 1
        elif off_won and not on_won:
            c += 1
        elif on_won and off_won:
            concordant_both_win += 1
        else:
            concordant_both_lose += 1

    p = mcnemar_exact_p(b, c)
    result = {
        "n_games": n, "base_seed": off["base_seed"],
        "model_champion": off["model_champion"], "model_opponent": off["model_opponent"],
        "sims": off["sims"], "c_puct": off["c_puct"],
        "champion_wins_off": off_wins, "champion_wins_on": on_wins,
        "discordant_b_on_only": b, "discordant_c_off_only": c,
        "concordant_both_win": concordant_both_win, "concordant_both_lose": concordant_both_lose,
        "mcnemar_p": p,
        "decision": "ON (signifikant besser)" if (p < 0.05 and on_wins > off_wins)
                    else "OFF (kein signifikanter Vorteil fuer ON)",
    }

    print("-" * 60)
    print(f"Arm OFF: Champion {off_wins}:{n - off_wins} Gegner")
    print(f"Arm ON:  Champion {on_wins}:{n - on_wins} Gegner")
    print(f"Diskordante Paare (gleicher Seed, unterschiedliches Ergebnis): "
          f"b(ON-only-win)={b}  c(OFF-only-win)={c}  "
          f"konkordant(beide gewinnen)={concordant_both_win}  konkordant(beide verlieren)={concordant_both_lose}")
    print(f"McNemar exakter p-Wert: {p:.4f}")
    print(f"Evidenzregel-Entscheidung: {result['decision']}")

    out_path = EVAL_DIR / "paired_arena_shrink_ab_result.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Ergebnis gespeichert: {out_path}")
    return result


def main() -> None:
    p = argparse.ArgumentParser(description="Task #78 Value-Shrinkage A/B (OFF vs. ON)")
    p.add_argument("--run-arm", choices=["off", "on"], default=None)
    p.add_argument("--combine", action="store_true")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--n-games", type=int, default=DEFAULT_N_GAMES)
    p.add_argument("--block-size", type=int, default=DEFAULT_BLOCK_SIZE)
    p.add_argument("--threads", type=int, default=DEFAULT_THREADS)
    args = p.parse_args()

    if args.combine:
        combine()
        return
    if args.run_arm is None:
        raise SystemExit("Entweder --run-arm off|on oder --combine angeben.")
    if args.seed is None:
        raise SystemExit("--seed ist fuer --run-arm erforderlich (muss in OFF und ON identisch sein).")
    run_arm(args.run_arm, args.seed, args.n_games, args.block_size, args.threads)


if __name__ == "__main__":
    main()
