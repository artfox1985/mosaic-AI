# -*- coding: utf-8 -*-
"""Vorzeichen-Sonde fuer `MOSAIC_IMPLICIT_MINIMAX_A`
(PREREG_implicit_minimax_backup.md par.2 Punkt 1), gebaut nach dem
r5_chance-Muster (`r5_chance_arming_sign_probe`,
engine/src/round5.rs bzw. round5_anchor.rs): an-vs-aus auf festen Seeds
messen, WIE VIELE Entscheidungen sich aendern und was das in Punkten
kostet -- bevor eine teure Arena laeuft.

Abweichung vom Rust-Vorbild (dokumentiert, nicht geraten): die Rust-Sonde
vergleicht beide Zustaende INNERHALB EINES Prozesses (Bool-Parameter an
`choose_action_inner`), weil der Runde-5-Loeser keinen Knopf-Zustand
cached. `MOSAIC_IMPLICIT_MINIMAX_A` liegt dagegen hinter einem
`OnceLock` (net_mcts.rs:337, einmal pro Prozess gelesen) -- an-vs-aus
geht deshalb NUR ueber zwei getrennte Prozesse mit Env-Var vor dem
Start, exakt das Instrument aus `tools/paired_arena_env_ab.py`
(Docstring dort: "je Arm ein EIGENER Worker-Prozess mit gesetzter
Env-Var"). Diese Sonde nutzt DENSELBEN Worker
(`tools/paired_arena_arm_worker.py`, `mosaic_rust.net_arena_match` mit
`log_games=True`) und vergleicht dessen `log`-Zeilenliste zwischen den
beiden Armen -- Granularitaet ist deshalb NICHT die einzelne
Zug-Entscheidung, sondern die volle Partie: erste abweichende Log-Zeile
= erste abweichende Entscheidung, Endstand-Differenz = Punktversatz.
Nur das Netz (Brett 0) liest den Knopf; die Heuristik-Gegenseite
(Brett 1, mcts.rs) ist unveraendert -- der Vergleich attribuiert also
sauber auf die Netz-Seite (gleiches Argument wie im
paired_arena_env_ab.py-Docstring).

    python -u tools/probes/implicit_minimax_sign_probe.py
"""
from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASIS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASIS / "tools"))
from paired_arena_env_ab import champion_model  # noqa: E402 -- bestehende Champion-Aufloesung wiederverwenden

WORKER = BASIS / "tools" / "paired_arena_arm_worker.py"
OUT = BASIS / "evaluations" / "implicit_minimax_sign_probe.json"

KNOB = "MOSAIC_IMPLICIT_MINIMAX_A"
ARMS = ["0", "0.2"]  # aus (Bestand) vs. an (Literatur-Empfehlung, par.1)
N_GAMES = 30  # innerhalb der vorgegebenen Spanne 20-40
NET_SIMS = 400  # Vorgabe der Aufgabe; deckt sich mit paired_arena_env_ab.py --net-sims Default
HEUR_SIMS = 150  # paired_arena_env_ab.py-Default -- dieselbe Sonde, die par.2 Punkt 2 spaeter faehrt
THREADS = 10  # paired_arena_env_ab.py-Default (--threads)
SEEDS = list(range(1, N_GAMES + 1))  # feste, fortlaufende Seeds -- gleiches Muster wie r5_chance_arming_sign_probe (1..=80)


def run_arm(model: str, knob_value: str) -> list[dict]:
    """Ein Arm = ein eigener Prozess mit gesetzter Env-Var (OnceLock-Zwang,
    siehe Modulkopf). Ruft denselben Worker wie `paired_arena_env_ab.py`."""
    env = os.environ.copy()
    env[KNOB] = knob_value
    cmd = [
        sys.executable, str(WORKER),
        "--model", model,
        "--net-sims", str(NET_SIMS),
        "--heur-sims", str(HEUR_SIMS),
        "--seeds", ",".join(str(s) for s in SEEDS),
        "--threads", str(THREADS),
        "--log-games",
    ]
    print(f"  Arm {KNOB}={knob_value}: {len(SEEDS)} Partien, {NET_SIMS} Sims Netz / "
          f"{HEUR_SIMS} Sims Heuristik ...", flush=True)
    t0 = time.time()
    proc = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=6 * 3600, env=env,
    )
    dt = time.time() - t0
    if proc.returncode != 0:
        raise RuntimeError(f"Arm {knob_value} rc={proc.returncode}: {proc.stderr[-4000:]}")
    games = json.loads(proc.stdout)
    print(f"    fertig in {dt:.1f}s", flush=True)
    return games


def first_divergence(log_off: list[str], log_on: list[str]) -> int | None:
    """Index der ersten abweichenden Log-Zeile, None wenn identisch."""
    for i, (a, b) in enumerate(zip(log_off, log_on)):
        if a != b:
            return i
    if len(log_off) != len(log_on):
        return min(len(log_off), len(log_on))
    return None


def stats(values: list[float]) -> dict:
    n = len(values)
    if n == 0:
        return {"n": 0, "mean": 0.0, "sd": 0.0, "se": 0.0, "t": 0.0, "median": 0.0, "min": 0.0, "max": 0.0}
    mean = statistics.mean(values)
    sd = statistics.stdev(values) if n > 1 else 0.0
    se = sd / (n ** 0.5) if n > 1 else 0.0
    t = mean / se if se > 1e-12 else 0.0
    return {
        "n": n, "mean": mean, "sd": sd, "se": se, "t": t,
        "median": statistics.median(values), "min": min(values), "max": max(values),
    }


def main() -> None:
    model = champion_model()
    print(f"Modell: {os.path.basename(model)}")
    print(f"Knopf: {KNOB}, Arme: {ARMS}, n={N_GAMES}, Seeds {SEEDS[0]}..{SEEDS[-1]}")

    t_start = time.time()
    games_by_arm = {arm: run_arm(model, arm) for arm in ARMS}
    total_runtime_s = time.time() - t_start

    off_games = games_by_arm[ARMS[0]]
    on_games = games_by_arm[ARMS[1]]
    assert len(off_games) == len(on_games) == N_GAMES, "Partie-Anzahl muss je Arm gleich sein"

    diverged_flags: list[bool] = []
    first_diff_steps: list[int] = []
    delta_net_all: list[float] = []
    delta_heur_all: list[float] = []
    delta_net_diverged: list[float] = []
    delta_heur_diverged: list[float] = []
    win_flip = 0
    per_game: list[dict] = []

    for i, seed in enumerate(SEEDS):
        g_off, g_on = off_games[i], on_games[i]
        assert g_off["game_seed"] == g_on["game_seed"] == seed, f"Seed-Reihenfolge verrutscht bei Index {i}"
        log_off, log_on = g_off["log"], g_on["log"]
        fd = first_divergence(log_off, log_on)
        diverged = fd is not None
        diverged_flags.append(diverged)

        d_net = g_on["scores"][0] - g_off["scores"][0]
        d_heur = g_on["scores"][1] - g_off["scores"][1]
        delta_net_all.append(d_net)
        delta_heur_all.append(d_heur)

        if diverged:
            first_diff_steps.append(fd)
            delta_net_diverged.append(d_net)
            delta_heur_diverged.append(d_heur)

        flipped = g_off["winner"] != g_on["winner"]
        win_flip += int(flipped)

        per_game.append({
            "seed": seed, "diverged": diverged, "first_diff_log_index": fd,
            "scores_off": g_off["scores"], "scores_on": g_on["scores"],
            "winner_off": g_off["winner"], "winner_on": g_on["winner"], "winner_flipped": flipped,
            "steps_off": g_off["steps"], "steps_on": g_on["steps"],
        })

    n_diverged = sum(diverged_flags)
    wins_net_off = sum(1 for g in off_games if g["winner"] == 0)
    wins_net_on = sum(1 for g in on_games if g["winner"] == 0)

    result = {
        "knob": KNOB, "arms": ARMS, "control_arm": ARMS[0],
        "model": os.path.relpath(model, BASIS).replace("\\", "/"),
        "n_games": N_GAMES, "net_sims": NET_SIMS, "heur_sims": HEUR_SIMS, "threads": THREADS,
        "seeds": SEEDS,
        "runtime_s": total_runtime_s,
        "divergenz": {
            "partien_mit_abweichung": n_diverged,
            "anteil": n_diverged / N_GAMES,
            "erste_abweichung_log_index": stats([float(x) for x in first_diff_steps]),
        },
        "punktversatz_netz_alle_partien": stats(delta_net_all),
        "punktversatz_heuristik_alle_partien": stats(delta_heur_all),
        "punktversatz_netz_nur_abweichende": stats(delta_net_diverged),
        "punktversatz_heuristik_nur_abweichende": stats(delta_heur_diverged),
        "sieg_delta": {
            "netz_siege_aus": wins_net_off, "netz_siege_an": wins_net_on,
            "delta": wins_net_on - wins_net_off, "partien_mit_sieg_wechsel": win_flip,
        },
        "per_game": per_game,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print(f"VORZEICHEN {KNOB} an({ARMS[1]})-vs-aus({ARMS[0]}), {N_GAMES} Partien, "
          f"{n_diverged} mit Abweichung ({100.0 * n_diverged / N_GAMES:.1f}%)")
    dn = result["punktversatz_netz_alle_partien"]
    dh = result["punktversatz_heuristik_alle_partien"]
    print(f"  Punktversatz Netz, ALLE Partien: Mittel {dn['mean']:+.3f} Pkt, SE {dn['se']:.3f}, t={dn['t']:+.2f}")
    print(f"  Punktversatz Heuristik, ALLE Partien: Mittel {dh['mean']:+.3f} Pkt, SE {dh['se']:.3f}, t={dh['t']:+.2f}")
    if n_diverged:
        dnd = result["punktversatz_netz_nur_abweichende"]
        dhd = result["punktversatz_heuristik_nur_abweichende"]
        print(f"  Punktversatz Netz, NUR abweichende ({n_diverged}): Mittel {dnd['mean']:+.3f}, "
              f"Median {dnd['median']:+.3f}, Spanne {dnd['min']:+.2f} .. {dnd['max']:+.2f}")
        print(f"  Punktversatz Heuristik, NUR abweichende ({n_diverged}): Mittel {dhd['mean']:+.3f}, "
              f"Median {dhd['median']:+.3f}, Spanne {dhd['min']:+.2f} .. {dhd['max']:+.2f}")
    print(f"  Sieg-Delta Netz: {wins_net_off}/{N_GAMES} (aus) -> {wins_net_on}/{N_GAMES} (an), "
          f"{win_flip} Partien mit Sieg-Wechsel")
    print(f"  Laufzeit gesamt: {total_runtime_s:.1f}s")
    print(f"Artefakt: {OUT}")


if __name__ == "__main__":
    main()
