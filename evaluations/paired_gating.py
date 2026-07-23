"""Gepaartes Netz-vs-Netz-Gating als STANDARD-Werkzeug fuer Kandidaten-
Vergleiche (Task #76, Phase A, 2026-07-23).

## Warum ein eigenes Skript (statt `arena.py::run_net_vs_net` weiterzunutzen)

`arena.py::run_net_vs_net` spielt Kandidat A vs. Kandidat B direkt gegeneinander
und entscheidet per SPRT -- schnell, aber NICHT gepaart: Startspieler/Brett
alternieren zwar ueber viele Spiele (i % 2), aber JE EINZELNES Spiel hat ein
Kandidat zufaellig das potenziell staerkere/schwaechere Brett (falls es einen
strukturellen Brett-/Zugreihenfolge-Bias gibt) UND es gibt keine Varianz-
reduktion durch geteilte Startbedingungen zwischen Vergleichs-Laeufen.
Dieses Skript ergaenzt (ersetzt NICHT) `run_net_vs_net` fuer die eigentliche
GATING-Entscheidung (loest ein neuer Kandidat den amtierenden Champion ab?):
gepaarte Spiel-PAARE mit identischem Seed und getauschten Brettern, dazu ein
exakter, nicht-parametrischer Signifikanztest.

## Design

Verifiziert (siehe `self_play.rs::run_net_vs_net_arena` bzw. der neue Rust-
Test `self_play::tests::run_net_vs_net_arena_seeds_deterministically_like_
run_net_arena_match`): `net_vs_net_arena_match`s interne Pro-Spiel-Seed-
Ableitung ist GENAUSO deterministisch aus `seed + i * const` wie
`net_arena_match`/`arena_match` -- zwei Aufrufe mit identischem `seed` und
`n_games` liefern daher fuer Spielindex `i` exakt dieselben Startbedingungen
(Wertungsplatten-Auswahl, Startspieler-Index), unabhaengig davon, welche
Modelle auf welchem Brett stehen.

Ein **Paar** = EIN Seed, ZWEI Spiele:
  - Orientierung 1: Kandidat A auf Brett 0, Kandidat B auf Brett 1.
  - Orientierung 2: Kandidat B auf Brett 0, Kandidat A auf Brett 1 (SELBER Seed).

Die Rust-API liefert kein eingebautes "ein Aufruf, Brett-Tausch pro Spielpaar"
-- deshalb zwei separate `net_vs_net_arena_match`-Aufrufe mit vertauschten
Modellpfaden (und vertauschten sims/c_puct, damit der jeweilige Kandidat
weiterhin seine EIGENEN Suchparameter behaelt) bei GLEICHEM `seed`. Damit
bekommt jeder Kandidat innerhalb eines Paares GENAU EIN Spiel auf Brett 0 und
EINS auf Brett 1 -- ein etwaiger Brett-/Zugreihenfolge-Bias faellt PRO PAAR
heraus, nicht erst im Erwartungswert ueber viele Paare.

## Statistik: Paar-Vorzeichentest (b/c-Notation wie in den bestehenden Skripten)

Wichtig — dies ist bewusst KEIN "diskordante Paare"-McNemar im strengen
Lehrbuch-Sinn (das wuerde die informativsten Faelle -- "A gewinnt beide
Spiele des Paares", also der klare Strke-Unterschied -- als "konkordant"
ignorieren und haette dadurch KEINE Power, echte Kandidatenunterschiede zu
erkennen). Stattdessen wird jedes Paar in genau eine von drei Kategorien
eingeteilt:
  - `b` : A gewinnt BEIDE Spiele des Paares (2:0) -- Beleg fuer A.
  - `c` : B gewinnt BEIDE Spiele des Paares (0:2) -- Beleg fuer B.
  - `split` : 1:1 -- unentschieden, traegt NICHT zum Signifikanztest bei
    (analog zu einem "Draw" bei einem klassischen Vorzeichentest), zeigt aber
    typischerweise gerade die Brett-/Reihenfolge-sensiblen Grenzfaelle.
`mcnemar_exact_p(b, c)` (dieselbe Formel wie in
`paired_arena_speedbundle.py`/`paired_arena_ismcts.py`, hier als exakter
Vorzeichentest auf den EINDEUTIGEN Paaren wiederverwendet) testet
H0: P(A gewinnt Paar | Paar ist eindeutig) = 0.5.

Zusaetzlich: gepaarte Differenz `d_i = (A-Siege im Paar) - (B-Siege im Paar)
in {-2, 0, +2}` je Paar, daraus Mittelwert + 95%-Normalapprox.-KI (`paired_ci`)
-- das ist die im Auftrag geforderte "CI der gepaarten Differenz".

Bloecke a 25 Paare (= 50 Spiele), kumulativer Test nach JEDEM vollstaendigen
Block (kein Zwischen-Block-Peeking), Stopp bei p<0.05 ODER 150 Paaren
(= 300 Spiele) -- gleiche Eckwerte wie die bestehenden gepaarten A/Bs.

## Nutzung

    python evaluations/paired_gating.py --model-a models/alphazero_v12_best.onnx \\
        --model-b models/alphazero_v10_best.onnx --name-a v12_best --name-b v10_best \\
        --sims 400

Schreibt `evaluations/paired_gating_result_<name_a>_vs_<name_b>.json`
(inkl. Block-Logs) und druckt am Ende eine fertige `elo_tracker.py add`-
Kommandozeile.

WICHTIG (Phase A, 2026-07-23): dieses Skript ist reine Code-Lieferung.
Es wird NICHT fuer eine echte Gating-Entscheidung ausgefuehrt, solange der
aktuelle netcq2-Self-Play-Batch das installierte Wheel nutzt -- nur ein
Winz-Parameter-Plumbing-Smoke (n=2, sims=20, v10_best gegen sich selbst) ist
in Phase A erlaubt (siehe `evaluations/STATUS.md`, Abschnitt "Gepaartes
Gating als Standard").
"""
import sys
import os
import json
import time
import random
import argparse
from pathlib import Path
from math import comb

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

BLOCK_SIZE = 25
MAX_PAIRS = 150
ALPHA = 0.05
DEFAULT_SIMS = 400
DEFAULT_C_PUCT = 1.5
DEFAULT_THREADS = 0


def mcnemar_exact_p(b: int, c: int) -> float:
    """Exakter zweiseitiger Vorzeichentest auf den eindeutigen Zellen (b, c)
    -- identische Formel wie in `paired_arena_speedbundle.py`/
    `paired_arena_ismcts.py`: X ~ Binomial(n=b+c, p=0.5),
    p = 2*min(P(X<=min(b,c)), P(X>=max(b,c))), gedeckelt bei 1.0."""
    n = b + c
    if n == 0:
        return 1.0
    lo, hi = min(b, c), max(b, c)
    p_le = sum(comb(n, k) for k in range(0, lo + 1)) / (2 ** n)
    p_ge = sum(comb(n, k) for k in range(hi, n + 1)) / (2 ** n)
    return min(1.0, 2 * min(p_le, p_ge))


def paired_ci(diffs: list[int], z: float = 1.96) -> tuple[float, float, float]:
    """Normalapprox. 95%-KI (Standard z=1.96) fuer den Mittelwert der
    gepaarten Differenzen `d_i in {-2, 0, +2}`. Liefert (mean, lo, hi);
    bei n<2 kollabiert das KI auf den Mittelwert (keine Streuung schaetzbar)."""
    n = len(diffs)
    if n == 0:
        return 0.0, 0.0, 0.0
    mean = sum(diffs) / n
    if n < 2:
        return mean, mean, mean
    var = sum((d - mean) ** 2 for d in diffs) / (n - 1)
    se = (var / n) ** 0.5
    return mean, mean - z * se, mean + z * se


def play_pair_block(mr, model_a: str, model_b: str, sims_a: int, sims_b: int,
                     c_puct_a: float, c_puct_b: float, n: int, seed: int,
                     threads: int) -> tuple[list[dict], list[dict]]:
    """Spielt EINEN Block von `n` gepaarten Seeds -- je Seed zwei Spiele mit
    getauschten Brettern (siehe Modul-Docstring). `g1[i]`/`g2[i]` teilen sich
    denselben abgeleiteten Pro-Spiel-Seed (identisches `seed`+`n_games`,
    Index `i`), nur die Modell-Brett-Zuordnung ist vertauscht."""
    raw1 = mr.net_vs_net_arena_match(
        model_a, model_b, sims_a=sims_a, sims_b=sims_b, n_games=n, seed=seed,
        num_threads=threads, c_puct_a=c_puct_a, c_puct_b=c_puct_b,
    )
    raw2 = mr.net_vs_net_arena_match(
        model_b, model_a, sims_a=sims_b, sims_b=sims_a, n_games=n, seed=seed,
        num_threads=threads, c_puct_a=c_puct_b, c_puct_b=c_puct_a,
    )
    return json.loads(raw1), json.loads(raw2)


def run_paired_gating(model_a: str, model_b: str, name_a: str | None = None,
                       name_b: str | None = None, sims_a: int = DEFAULT_SIMS,
                       sims_b: int = DEFAULT_SIMS, c_puct_a: float = DEFAULT_C_PUCT,
                       c_puct_b: float = DEFAULT_C_PUCT, block_size: int = BLOCK_SIZE,
                       max_pairs: int = MAX_PAIRS, alpha: float = ALPHA,
                       base_seed: int | None = None, threads: int = DEFAULT_THREADS) -> dict:
    """Orchestriert das volle gepaarte Gating (siehe Modul-Docstring). Bricht
    NACH einem VOLLSTAENDIGEN Block ab, sobald der kumulative Paar-
    Vorzeichentest p<alpha erreicht, oder wenn `max_pairs` Paare gespielt
    sind. Importiert `mosaic_rust` HIER (nicht auf Modulebene) -- welches
    Wheel geladen wird, entscheidet allein der aufrufende Python-Interpreter,
    nicht dieses Skript."""
    import mosaic_rust as mr

    name_a = name_a or os.path.basename(model_a)
    name_b = name_b or os.path.basename(model_b)
    base_seed = base_seed if base_seed is not None else random.randint(0, 10 ** 9)

    pair_a_sweeps = pair_b_sweeps = splits = 0
    a_wins_total = b_wins_total = 0
    pair_diffs: list[int] = []
    done_pairs = 0
    block_idx = 0
    block_logs: list[dict] = []

    print(f"Gepaartes Gating (Task #76): {name_a}@{sims_a} (c_puct={c_puct_a}) vs "
          f"{name_b}@{sims_b} (c_puct={c_puct_b}) -- Basis-Seed={base_seed}, "
          f"Bloecke a {block_size} Paare, Stopp bei p<{alpha} oder {max_pairs} Paaren")

    while done_pairs < max_pairs:
        n = min(block_size, max_pairs - done_pairs)
        seed = base_seed + block_idx * 1_000_000
        t0 = time.time()
        g1, g2 = play_pair_block(mr, model_a, model_b, sims_a, sims_b, c_puct_a, c_puct_b,
                                  n, seed, threads)
        dur = time.time() - t0

        for i in range(n):
            a_won_o1 = g1[i]["winner"] == 0  # A auf Brett 0 (Orientierung 1)
            a_won_o2 = g2[i]["winner"] == 1  # A auf Brett 1 (Orientierung 2, B auf Brett 0)
            a_wins_pair = int(a_won_o1) + int(a_won_o2)
            b_wins_pair = 2 - a_wins_pair
            a_wins_total += a_wins_pair
            b_wins_total += b_wins_pair
            pair_diffs.append(a_wins_pair - b_wins_pair)
            if a_wins_pair == 2:
                pair_a_sweeps += 1
            elif b_wins_pair == 2:
                pair_b_sweeps += 1
            else:
                splits += 1

        done_pairs += n
        block_idx += 1
        p = mcnemar_exact_p(pair_a_sweeps, pair_b_sweeps)
        mean_d, ci_lo, ci_hi = paired_ci(pair_diffs)
        block_log = {
            "block": block_idx, "seed": seed, "n_pairs_block": n, "done_pairs": done_pairs,
            "a_wins_total": a_wins_total, "b_wins_total": b_wins_total,
            "pair_a_sweeps_b": pair_a_sweeps, "pair_b_sweeps_c": pair_b_sweeps,
            "pair_splits": splits, "mcnemar_p": p, "mean_pair_diff": mean_d,
            "ci95": [ci_lo, ci_hi], "duration_s": dur,
        }
        block_logs.append(block_log)
        print(f"  Block {block_idx} (Seed={seed}, n={n} Paare, {dur:.1f}s): kumulativ "
              f"{name_a} {a_wins_total}:{b_wins_total} {name_b} | Paare {done_pairs} "
              f"(A-Sweep b={pair_a_sweeps} B-Sweep c={pair_b_sweeps} Split={splits}) | "
              f"McNemar p={p:.4f} | gepaarte Diff {mean_d:+.3f} [{ci_lo:+.3f},{ci_hi:+.3f}]",
              flush=True)

        if p < alpha:
            print(f"  Signifikant bei p<{alpha} nach {done_pairs} Paaren.")
            break
    else:
        print(f"  {max_pairs} Paare erreicht ohne Signifikanz "
              f"(p={mcnemar_exact_p(pair_a_sweeps, pair_b_sweeps):.4f}).")

    final_p = mcnemar_exact_p(pair_a_sweeps, pair_b_sweeps)
    mean_d, ci_lo, ci_hi = paired_ci(pair_diffs)
    n_games_total = done_pairs * 2
    result = {
        "name_a": name_a, "name_b": name_b, "model_a": model_a, "model_b": model_b,
        "sims_a": sims_a, "sims_b": sims_b, "c_puct_a": c_puct_a, "c_puct_b": c_puct_b,
        "done_pairs": done_pairs, "n_games_total": n_games_total,
        "a_wins_total": a_wins_total, "b_wins_total": b_wins_total,
        "pair_a_sweeps_b": pair_a_sweeps, "pair_b_sweeps_c": pair_b_sweeps,
        "pair_splits": splits, "p": final_p, "mean_pair_diff": mean_d, "ci95": [ci_lo, ci_hi],
        "base_seed": base_seed, "blocks": block_logs,
    }

    print("-" * 60)
    print(f"ERGEBNIS: {name_a} {a_wins_total}:{b_wins_total} {name_b} "
          f"(von {n_games_total} Spielen, {done_pairs} Paaren)")
    print(f"  Eindeutige Paare: A-Sweep b={pair_a_sweeps}  B-Sweep c={pair_b_sweeps}  "
          f"Split={splits}")
    print(f"  Exakter Paar-Vorzeichentest p={final_p:.4f}")
    print(f"  Gepaarte Differenz (A-Siege minus B-Siege pro Paar): "
          f"{mean_d:+.3f}  95%-KI [{ci_lo:+.3f}, {ci_hi:+.3f}]")
    print(f"  Hinweis fuers elo_tracker-Protokoll:")
    print(f"    python evaluations/elo_tracker.py add --player-a {name_a} --sims-a {sims_a} "
          f"--player-b {name_b} --sims-b {sims_b} --wins-a {a_wins_total} "
          f"--wins-b {b_wins_total} --n {n_games_total} "
          f"--comment \"Gepaartes Gating (Task #76), p={final_p:.4f}\"")
    return result


def main() -> None:
    p = argparse.ArgumentParser(description="Gepaartes Netz-vs-Netz-Gating (Task #76)")
    p.add_argument("--model-a", required=True)
    p.add_argument("--model-b", required=True)
    p.add_argument("--name-a", default=None)
    p.add_argument("--name-b", default=None)
    p.add_argument("--sims", type=int, default=None, help="Setzt sims-a UND sims-b gleich")
    p.add_argument("--sims-a", type=int, default=DEFAULT_SIMS)
    p.add_argument("--sims-b", type=int, default=DEFAULT_SIMS)
    p.add_argument("--c-puct", type=float, default=None, help="Setzt c-puct-a UND c-puct-b gleich")
    p.add_argument("--c-puct-a", type=float, default=DEFAULT_C_PUCT)
    p.add_argument("--c-puct-b", type=float, default=DEFAULT_C_PUCT)
    p.add_argument("--block-size", type=int, default=BLOCK_SIZE)
    p.add_argument("--max-pairs", type=int, default=MAX_PAIRS)
    p.add_argument("--alpha", type=float, default=ALPHA)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--threads", type=int, default=DEFAULT_THREADS)
    p.add_argument("--out", default=None, help="Ziel-JSON-Pfad (Default: evaluations/paired_gating_result_<a>_vs_<b>.json)")
    args = p.parse_args()

    sims_a = args.sims if args.sims is not None else args.sims_a
    sims_b = args.sims if args.sims is not None else args.sims_b
    c_puct_a = args.c_puct if args.c_puct is not None else args.c_puct_a
    c_puct_b = args.c_puct if args.c_puct is not None else args.c_puct_b

    result = run_paired_gating(
        args.model_a, args.model_b, name_a=args.name_a, name_b=args.name_b,
        sims_a=sims_a, sims_b=sims_b, c_puct_a=c_puct_a, c_puct_b=c_puct_b,
        block_size=args.block_size, max_pairs=args.max_pairs, alpha=args.alpha,
        base_seed=args.seed, threads=args.threads,
    )

    out_path = Path(args.out) if args.out else (
        Path(__file__).resolve().parent
        / f"paired_gating_result_{result['name_a']}_vs_{result['name_b']}.json"
    )
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Ergebnis gespeichert: {out_path}")


if __name__ == "__main__":
    main()
