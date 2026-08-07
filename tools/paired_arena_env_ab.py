# -*- coding: utf-8 -*-
"""tools/paired_arena_env_ab.py -- generischer gepaarter Zwei-Arm-A/B fuer
LAUFZEIT-Env-Knoepfe (PREREG_suchpfad_nachmessungen.md, Amendment
2026-08-07).

Instrument (#30-Muster): je Arm ein EIGENER Worker-Prozess mit gesetzter
Env-Var (die Knoepfe sind prozessweit, OnceLock), Champion-Netz vs
Heuristik@150(dyn) via `tools/paired_arena_arm_worker.py`
(`mosaic_rust.net_arena_match`, Netz = Brett 0). Identische Basis-Seeds
ueber alle Arme -> Spielindex i hat ueberall dieselben Startbedingungen;
Auswertung als exakter zweiseitiger McNemar auf den diskordanten Paaren
(Formel identisch zu paired_gating.py). Die Heuristik liest keinen der
Knoepfe -- die Arm-Differenz attribuiert sauber auf die Netz-Seite.

Nutzung (Messung 1, Floor-Sweep):
    python tools/paired_arena_env_ab.py --env-name MOSAIC_FLOOR_SHAPING_W \
        --arms 0.3 0.15 0.6 --control 0.3 --net-sims 400 --n-games 200 \
        --seed 20260807 --out-prefix floorw

Nutzung (Messung 2, m-Formel @150):
    python tools/paired_arena_env_ab.py --env-name MOSAIC_GUMBEL_TOP_M \
        --arms 0 16 --control 0 --net-sims 150 --n-games 200 \
        --seed 20260808 --out-prefix topm150
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from math import comb
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
WORKER = Path(__file__).resolve().parent / "paired_arena_arm_worker.py"
EVAL_DIR = BASE_DIR / "evaluations"
ARM_TIMEOUT_SECS = 6 * 3600


def mcnemar_exact_p(b: int, c: int) -> float:
    """Exakter zweiseitiger McNemar -- identisch zu paired_gating.py."""
    n = b + c
    if n == 0:
        return 1.0
    lo, hi = min(b, c), max(b, c)
    p_le = sum(comb(n, k) for k in range(0, lo + 1)) / (2 ** n)
    p_ge = sum(comb(n, k) for k in range(hi, n + 1)) / (2 ** n)
    return min(1.0, 2 * min(p_le, p_ge))


def champion_model() -> str:
    n = (BASE_DIR / "models" / "champion.txt").read_text(encoding="utf-8").strip()
    p = BASE_DIR / "models" / f"alphazero_{n}.onnx"
    if not p.exists():
        raise SystemExit(f"Champion-ONNX fehlt: {p}")
    return str(p.resolve())


def run_arm(env_name: str, value: str, model: str, net_sims: int, heur_sims: int,
            n_games: int, seed: int, block_size: int, threads: int) -> list[dict]:
    env = os.environ.copy()
    env[env_name] = value
    games: list[dict] = []
    done, block_idx = 0, 0
    print(f"Arm {env_name}={value}: {os.path.basename(model)}@{net_sims} vs "
          f"Heuristik@{heur_sims}(dyn), Basis-Seed={seed}, n={n_games}", flush=True)
    while done < n_games:
        n = min(block_size, n_games - done)
        block_seed = seed + block_idx * 1_000_000
        t0 = time.time()
        proc = subprocess.run(
            [sys.executable, str(WORKER), "--model", model,
             "--net-sims", str(net_sims), "--heur-sims", str(heur_sims),
             "--n-games", str(n), "--seed", str(block_seed),
             "--threads", str(threads)],
            capture_output=True, text=True, timeout=ARM_TIMEOUT_SECS, env=env,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Arm {value} Block {block_idx} (Seed={block_seed}) "
                               f"rc={proc.returncode}: {proc.stderr[-2000:]}")
        block = json.loads(proc.stdout)
        games.extend(block)
        done += n
        block_idx += 1
        wins = sum(1 for g in games if g["winner"] == 0)
        print(f"  [{value}] Block {block_idx} (Seed={block_seed}, n={n}, "
              f"{time.time()-t0:.1f}s): Netz kumulativ {wins}/{done}", flush=True)
    return games


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--env-name", required=True)
    ap.add_argument("--arms", nargs="+", required=True,
                    help="Env-Werte der Arme (erster Lauf = Reihenfolge hier)")
    ap.add_argument("--control", required=True,
                    help="Kontroll-Arm-Wert; jeder andere Arm wird gegen ihn gepaart")
    ap.add_argument("--model", default=None, help="Default: models/champion.txt")
    ap.add_argument("--net-sims", type=int, default=400)
    ap.add_argument("--heur-sims", type=int, default=150)
    ap.add_argument("--n-games", type=int, default=200)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--block-size", type=int, default=25)
    ap.add_argument("--threads", type=int, default=10)
    ap.add_argument("--out-prefix", required=True)
    args = ap.parse_args()

    if args.control not in args.arms:
        raise SystemExit("--control muss in --arms enthalten sein")
    model = args.model or champion_model()

    results: dict[str, list[dict]] = {}
    for v in args.arms:
        results[v] = run_arm(args.env_name, v, model, args.net_sims,
                             args.heur_sims, args.n_games, args.seed,
                             args.block_size, args.threads)

    out = {
        "env_name": args.env_name, "arms": args.arms, "control": args.control,
        "model": model, "net_sims": args.net_sims, "heur_sims": args.heur_sims,
        "n_games": args.n_games, "base_seed": args.seed,
        "arm_wins": {}, "comparisons": {},
        "games": {v: results[v] for v in args.arms},
    }
    ctrl = results[args.control]
    print("\n=== AUSWERTUNG (gepaart je Spielindex, Netz-Sieg = winner==0) ===")
    for v in args.arms:
        wins = sum(1 for g in results[v] if g["winner"] == 0)
        out["arm_wins"][v] = wins
        print(f"Arm {args.env_name}={v}: Netz {wins}/{args.n_games}")
    for v in args.arms:
        if v == args.control:
            continue
        b = c = 0
        for i in range(args.n_games):
            ctrl_won = ctrl[i]["winner"] == 0
            test_won = results[v][i]["winner"] == 0
            if test_won and not ctrl_won:
                b += 1
            elif ctrl_won and not test_won:
                c += 1
        p = mcnemar_exact_p(b, c)
        out["comparisons"][f"{args.control}_vs_{v}"] = {"b_test_only": b,
                                                        "c_control_only": c,
                                                        "p_mcnemar": p}
        print(f"{args.control} vs {v}: diskordant b(test)={b} / c(kontrolle)={c}"
              f"  McNemar p={p:.4f}")

    out_path = EVAL_DIR / f"paired_arena_env_{args.out_prefix}.json"
    out_path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nErgebnis: {out_path}")


if __name__ == "__main__":
    main()
