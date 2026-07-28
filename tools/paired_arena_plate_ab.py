"""Gepaarter A/B fuer Task #93 (Wertungsplatten-Shaping-Toggle, 2026-07-25):
`PLATE_SHAPING_ENABLED=false` (Ist-Zustand, Arm OFF) vs. `=true` mit
`PLATE_SHAPING_WEIGHT=0.3` (Arm ON, Startwert analog zum validierten
Floor-Shaping `FLOOR_SHAPING_WEIGHT=0.3`).

## Warum kein Worktree/Zweit-venv (analog `paired_arena_shrink_ab.py`)

`PLATE_SHAPING_ENABLED` ist eine Compile-Zeit-Konstante -- Toggle-ON und
-OFF koennen nie im selben Prozess gegeneinander spielen. Die beiden Arme
muessen aber NICHT gleichzeitig laufen (kein Zeitdruck durch einen parallel
laufenden Self-Play-Batch) -- deshalb genuegt EIN venv, sequenziell
nacheinander bespielt: erst Arm OFF (aktueller Wheel-Stand), dann
Quellcode-Flip + Rebuild, dann Arm ON, im selben venv. Jeder Arm ist ein
eigener Skript-Aufruf (frischer Python-Prozess je Arm-Lauf), damit
garantiert das WHEEL zum Zeitpunkt des Aufrufs geladen wird, das gerade
`pip install --force-reinstall` erzeugt hat.

## Design

Referenz-Champion `v15_best` (Elo 1029, Brett 0, `net_vs_net_arena_match`)
gegen Vor-Referenz `v14b_best` (Elo 961, Brett 1) -- naher, sensitiver
Gegner, beide @400 Sims, deterministische Arena. IDENTISCHE Seeds `S` in
beiden Armen (`net_vs_net_arena_match`s interne Pro-Spiel-Seed-Ableitung ist
deterministisch aus `seed + i*const`) -- Spielindex `i` hat in Arm OFF und
Arm ON dieselben Startbedingungen. Ausgewertet wird PAARWEISE: Spiel `i` in
Arm OFF vs. Spiel `i` in Arm ON, `winner==0` = Champion (v15_best) gewinnt.

  - `b` = Champion gewinnt in ON, verliert in OFF (Beleg FUER den Plate-Toggle)
  - `c` = Champion gewinnt in OFF, verliert in ON (Beleg GEGEN den Toggle)
  - Konkordant (beide gleich) traegt nicht zum Vorzeichentest bei.

Exakter zweiseitiger McNemar-Test auf (b, c) (gleiche Formel wie
`paired_arena_shrink_ab.py`/`paired_arena_ismcts.py`/`paired_gating.py`).

Evidenzregel (Auftrag, fest vereinbart): NUR bei p<0.05 UND Vorteil fuer ON
gilt der Toggle als belegt. 100 Spiele je Arm (200 gesamt) als Erstmessung,
KEIN sequenzielles Nachziehen -- fixed-n, kein SPRT (reine
Sensitivitaetsmessung, keine Champion-Gating-Entscheidung).

## Nutzung

    # Arm OFF (Ist-Zustand, PLATE_SHAPING_ENABLED=false):
    python tools/paired_arena_plate_ab.py --run-arm off --seed <S> --n-games 100

    # ... dann PLATE_SHAPING_ENABLED=true setzen, cargo test --release, Wheel neu bauen ...

    # Arm ON (identischer Seed):
    python tools/paired_arena_plate_ab.py --run-arm on --seed <S> --n-games 100

    # Zusammenfuehren + Statistik:
    python tools/paired_arena_plate_ab.py --combine
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
WORKER_SCRIPT = Path(__file__).resolve().parent / "paired_arena_plate_arm_worker.py"
EVAL_DIR = BASE_DIR / "evaluations"

# Absolute Pfade in den HAUPT-Checkout (models/ ist gitignored, daher kein
# relativer Pfad ueber __file__ allein verlaesslich, falls von einem
# Worktree aus aufgerufen -- siehe Junction-Vorfall 2026-07-24).
# Task #8 (2026-07-28, Nutzer-Anstoss "warum schaust dir nicht die
# aktuellen Champions an?"): Referenz-Paar von v15_best/v14b_best (Task #93,
# beide laengst nicht mehr relevant) auf den AMTIERENDEN Champion v17_best
# vs. Vorgaenger v16_best umgestellt -- testet die tatsaechliche Staerke-
# Frage statt akademischer Vergleichbarkeit mit dem alten Nullergebnis.
MAIN_CHECKOUT = BASE_DIR
# Ueberschreibbar per --model-champion/--model-opponent. Vorgabe: der
# amtierende Champion aus models/champion.txt gegen die Vor-Referenz -- damit
# hier nicht (wie bis 2026-07-28 in arena.py) ein veralteter Name stehenbleibt.
def _champion_default() -> str:
    try:
        n = (MAIN_CHECKOUT / "models" / "champion.txt").read_text(encoding="utf-8").strip()
    except Exception:
        n = "v18_best"
    p = MAIN_CHECKOUT / "models" / f"alphazero_{n}.onnx"
    return str((p if p.exists() else MAIN_CHECKOUT / "models" / "alphazero_v18_best.onnx").resolve())


MODEL_CHAMPION = _champion_default()
MODEL_OPPONENT = str((MAIN_CHECKOUT / "models" / "alphazero_v17_best.onnx").resolve())
SIMS = 400
C_PUCT = 1.5
DEFAULT_N_GAMES = 100
DEFAULT_BLOCK_SIZE = 25
DEFAULT_THREADS = 10
ARM_TIMEOUT_SECS = 3 * 3600


def mcnemar_exact_p(b: int, c: int) -> float:
    """Exakter zweiseitiger McNemar-Test -- identische Formel wie in
    `paired_arena_shrink_ab.py`/`paired_arena_ismcts.py`/`paired_gating.py`."""
    n = b + c
    if n == 0:
        return 1.0
    lo, hi = min(b, c), max(b, c)
    p_le = sum(comb(n, k) for k in range(0, lo + 1)) / (2 ** n)
    p_ge = sum(comb(n, k) for k in range(hi, n + 1)) / (2 ** n)
    return min(1.0, 2 * min(p_le, p_ge))


def run_arm(arm: str, seed: int, n_games: int, block_size: int, threads: int,
            out_prefix: str = "plate") -> dict:
    """Spielt einen Arm (OFF oder ON) in Bloecken, Champion (v15_best) IMMER
    auf Brett 0. Gibt {"games": [...alle Einzelspielergebnisse in Original-
    Reihenfolge...]} zurueck und speichert das Rohergebnis nach
    evaluations/paired_arena_plate_<arm>_raw.json."""
    label = arm.upper()
    all_games: list[dict] = []
    done = 0
    block_idx = 0
    print(f"Arm {label}: Champion={os.path.basename(MODEL_CHAMPION)} (Brett 0) vs. "
          f"Vor-Referenz={os.path.basename(MODEL_OPPONENT)} (Brett 1) @ sims={SIMS}, "
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
    out_path = EVAL_DIR / f"paired_arena_{out_prefix}_{arm}_raw.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    champ_wins = sum(1 for g in all_games if g["winner"] == 0)
    print(f"Arm {label} fertig: Champion {champ_wins}:{n_games - champ_wins} Vor-Referenz "
          f"({n_games} Spiele). Rohergebnis: {out_path}", flush=True)
    return result


def _avg(games: list[dict], key: str, idx: int) -> float:
    vals = [g[key][idx] for g in games if key in g]
    return sum(vals) / len(vals) if vals else float("nan")


def combine(out_prefix: str = "plate") -> dict:
    off_path = EVAL_DIR / f"paired_arena_{out_prefix}_off_raw.json"
    on_path = EVAL_DIR / f"paired_arena_{out_prefix}_on_raw.json"
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
        "avg_score_champion_off": _avg(off_games, "scores", 0),
        "avg_score_opponent_off": _avg(off_games, "scores", 1),
        "avg_score_champion_on": _avg(on_games, "scores", 0),
        "avg_score_opponent_on": _avg(on_games, "scores", 1),
        "avg_floor_champion_off": _avg(off_games, "total_floor", 0),
        "avg_floor_opponent_off": _avg(off_games, "total_floor", 1),
        "avg_floor_champion_on": _avg(on_games, "total_floor", 0),
        "avg_floor_opponent_on": _avg(on_games, "total_floor", 1),
        "decision": "ON (signifikant besser)" if (p < 0.05 and on_wins > off_wins)
                    else "OFF (kein signifikanter Vorteil fuer ON)",
    }

    print("-" * 60)
    print(f"Arm OFF: Champion {off_wins}:{n - off_wins} Vor-Referenz  "
          f"(Score {result['avg_score_champion_off']:.1f} vs. {result['avg_score_opponent_off']:.1f}, "
          f"Floor {result['avg_floor_champion_off']:.1f} vs. {result['avg_floor_opponent_off']:.1f})")
    print(f"Arm ON:  Champion {on_wins}:{n - on_wins} Vor-Referenz  "
          f"(Score {result['avg_score_champion_on']:.1f} vs. {result['avg_score_opponent_on']:.1f}, "
          f"Floor {result['avg_floor_champion_on']:.1f} vs. {result['avg_floor_opponent_on']:.1f})")
    print(f"Diskordante Paare (gleicher Seed, unterschiedliches Ergebnis): "
          f"b(ON-only-win)={b}  c(OFF-only-win)={c}  "
          f"konkordant(beide gewinnen)={concordant_both_win}  konkordant(beide verlieren)={concordant_both_lose}")
    print(f"McNemar exakter p-Wert: {p:.4f}")
    print(f"Evidenzregel-Entscheidung: {result['decision']}")

    out_path = EVAL_DIR / f"paired_arena_{out_prefix}_ab_result.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Ergebnis gespeichert: {out_path}")
    return result


def main() -> None:
    p = argparse.ArgumentParser(description="Task #93 Wertungsplatten-Shaping A/B (OFF vs. ON)")
    p.add_argument("--run-arm", choices=["off", "on"], default=None)
    p.add_argument("--combine", action="store_true")
    p.add_argument("--out-prefix", default="plate",
                    help="Praefix der Ergebnisdateien (paired_arena_<prefix>_{off,on}_raw.json / "
                         "_ab_result.json). Default 'plate' = Bestandsverhalten. Erlaubt, dasselbe "
                         "Werkzeug fuer weitere Compile-Toggle-A/Bs zu nutzen, ohne fruehere "
                         "Ergebnisse zu ueberschreiben (z.B. GUMBEL_TOP_M-Kalibrierung, Task #9).")
    p.add_argument("--model-champion", default=None, help="ONNX Brett 0 (Vorgabe: champion.txt)")
    p.add_argument("--model-opponent", default=None, help="ONNX Brett 1")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--n-games", type=int, default=DEFAULT_N_GAMES)
    p.add_argument("--block-size", type=int, default=DEFAULT_BLOCK_SIZE)
    p.add_argument("--threads", type=int, default=DEFAULT_THREADS)
    args = p.parse_args()

    if args.combine:
        combine(args.out_prefix)
        return
    global MODEL_CHAMPION, MODEL_OPPONENT
    if args.model_champion:
        MODEL_CHAMPION = str(Path(args.model_champion).resolve())
    if args.model_opponent:
        MODEL_OPPONENT = str(Path(args.model_opponent).resolve())
    if args.run_arm is None:
        raise SystemExit("Entweder --run-arm off|on oder --combine angeben.")
    if args.seed is None:
        raise SystemExit("--seed ist fuer --run-arm erforderlich (muss in OFF und ON identisch sein).")
    run_arm(args.run_arm, args.seed, args.n_games, args.block_size, args.threads,
            args.out_prefix)


if __name__ == "__main__":
    main()
