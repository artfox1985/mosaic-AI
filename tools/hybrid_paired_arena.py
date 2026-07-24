"""Task #88 (Hybrid-Suche 2x2, kausaler Kopf-Test) -- gepaarter Arena-Runner
fuer die Hybrid-Suche (Priors von Netz A, Blattwerte von Netz B).

## Warum ein eigenes (kleines) Skript statt `tools/paired_gating.py` direkt

`paired_gating.py` bleibt das Vorbild (Blockstruktur, Brett-Tausch-Paarung,
`mcnemar_exact_p`/`paired_ci` -- BEIDE Funktionen werden hier direkt
importiert, nicht neu geschrieben, siehe CLAUDE.md "vorhandene Funktionen
nutzen"). Zwei Unterschiede rechtfertigen ein eigenes, schlankes Skript:

1. `paired_gating.py` ruft `mr.net_vs_net_arena_match` (EIN Netz pro Brett).
   Die Hybrid-Zellen brauchen `mr.net_vs_net_arena_match_hybrid` (Task #88,
   `engine/src/lib.rs`) mit einem eigenen `hybrid_board`-Parameter fuer den
   Brett-Tausch (siehe dortiger Kommentar) -- eine andere Aufruf-Signatur je
   Orientierung.
2. Hier geht es NICHT um eine Gating-Entscheidung (kein SPRT-Stopp), sondern
   um Effekt-Richtung/-Groessenordnung bei fester Paarzahl (Nutzer-Vorgabe:
   ~50-75 Paare je Hybrid-Zelle, ~50 Paare fuer die Verankerungsmessung).
   Deshalb: fester Deckel, keine sequenzielle Stopp-Regel.

## Design: drei Zellen, EIN Basis-Seed-Strom

Referenzgegner fuer ALLE Zellen: `v10_best` (fest). Kandidaten:
  - `anchor`   : v12_best (Priors+Value) vs. v10_best -- reine Netz-vs-Netz-
                 Verankerung (`net_vs_net_arena_match`, kein Hybrid-Code).
  - `hybrid_pv`: Priors/Moon von v10_best, Blattwert von v12_best (P=v10,V=v12).
  - `hybrid_vp`: Priors/Moon von v12_best, Blattwert von v10_best (P=v12,V=v10).

Alle drei Zellen nutzen DIESELBE Seed-Ableitung (`base_seed + pair_idx`) --
"gleiche Seeds ueber alle Zellen" (Nutzer-Vorgabe). Jedes Paar = zwei Spiele
mit getauschtem Brett (Kandidat auf Brett 0 UND auf Brett 1, selber Seed) --
identisches Prinzip wie `paired_gating.py::play_pair_block`, hier nur ueber
`hybrid_board` statt vertauschten Modellpfaden umgesetzt.

## Nutzung

    python tools/hybrid_paired_arena.py --sims 400 --n-pairs-anchor 50 \\
        --n-pairs-hybrid 60 --threads 10

Schreibt `evaluations/hybrid_arena_<cell>.json` je Zelle.
"""
import sys
import os
import json
import time
import argparse
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paired_gating import mcnemar_exact_p, paired_ci  # noqa: E402  (Wiederverwendung, siehe Docstring)

DEFAULT_SIMS = 400
DEFAULT_C_PUCT = 1.5
DEFAULT_THREADS = 10
BLOCK_SIZE = 25


def play_pair_block_plain(mr, model_a, model_b, sims, c_puct, n, seed, threads):
    """Wie `paired_gating.py::play_pair_block`, hier lokal (dort nicht als
    eigenstaendig importierbare Funktion mit exakt dieser Signatur -- die
    dortige Version haengt an modulglobalen SPRT-Defaults). Reine Netz-vs-
    Netz-Paarung (Verankerungszelle)."""
    raw1 = mr.net_vs_net_arena_match(
        model_a, model_b, sims_a=sims, sims_b=sims, n_games=n, seed=seed,
        num_threads=threads, c_puct_a=c_puct, c_puct_b=c_puct,
    )
    raw2 = mr.net_vs_net_arena_match(
        model_b, model_a, sims_a=sims, sims_b=sims, n_games=n, seed=seed,
        num_threads=threads, c_puct_a=c_puct, c_puct_b=c_puct,
    )
    g1, g2 = json.loads(raw1), json.loads(raw2)
    # Orientierung 1: Kandidat (model_a) auf Brett 0 -> gewinnt bei winner==0.
    # Orientierung 2: Kandidat auf Brett 1 (model_b auf Brett 0) -> winner==1.
    return [g["winner"] == 0 for g in g1], [g["winner"] == 1 for g in g2]


def play_pair_block_hybrid(mr, policy_path, value_path, ref_path, sims, c_puct, n, seed, threads):
    """Hybrid-Zelle: Kandidat = Hybrid-Suche (Priors von `policy_path`, Value
    von `value_path`), Referenz = Einzel-Netz `ref_path` (fest v10_best).
    Brett-Tausch per `hybrid_board` (0/1, Task #88 `net_vs_net_arena_match_hybrid`)
    statt vertauschter Modellpfade -- gleiches Paarungsprinzip wie
    `play_pair_block_plain`."""
    raw1 = mr.net_vs_net_arena_match_hybrid(
        hybrid_policy=policy_path, hybrid_value=value_path, plain_model=ref_path,
        hybrid_board=0, sims_hybrid=sims, sims_plain=sims, n_games=n, seed=seed,
        num_threads=threads, c_puct_hybrid=c_puct, c_puct_plain=c_puct,
    )
    raw2 = mr.net_vs_net_arena_match_hybrid(
        hybrid_policy=policy_path, hybrid_value=value_path, plain_model=ref_path,
        hybrid_board=1, sims_hybrid=sims, sims_plain=sims, n_games=n, seed=seed,
        num_threads=threads, c_puct_hybrid=c_puct, c_puct_plain=c_puct,
    )
    g1, g2 = json.loads(raw1), json.loads(raw2)
    # Orientierung 1 (hybrid_board=0): Kandidat auf Brett 0 -> winner==0.
    # Orientierung 2 (hybrid_board=1): Kandidat auf Brett 1 -> winner==1.
    return [g["winner"] == 0 for g in g1], [g["winner"] == 1 for g in g2]


def run_cell(name, play_pair_fn, n_pairs, base_seed, block_size, sims, threads, out_dir):
    """Orchestriert EINE Zelle in Bloecken (Fortschritts-Log, kein SPRT-Stopp
    -- laeuft immer bis `n_pairs` durch). `play_pair_fn(mr, n, seed)` liefert
    (won_o1: list[bool], won_o2: list[bool]) je Block -- Aufrufer bindet die
    Modellpfade per `functools.partial`/Closure vorab."""
    import mosaic_rust as mr

    cand_sweeps = ref_sweeps = splits = 0
    cand_wins_total = ref_wins_total = 0
    pair_diffs = []
    done_pairs = 0
    block_idx = 0
    block_logs = []
    t_cell_start = time.time()

    print(f"=== Zelle '{name}': {n_pairs} Paare, Basis-Seed={base_seed}, "
          f"Bloecke a {block_size} ===", flush=True)

    while done_pairs < n_pairs:
        n = min(block_size, n_pairs - done_pairs)
        # Ein Seed PRO PAAR (nicht pro Block) -- "gleiche Seeds ueber alle
        # Zellen": Paar i nutzt in JEDER Zelle exakt `base_seed + i`.
        # `net_vs_net_arena_match[_hybrid]` leitet je Spielindex `i` intern
        # per `seed.wrapping_add(i * const)` weiter deterministisch ab (siehe
        # `self_play.rs`-Kommentar) -- ein Block ruft daher mit Basis-Seed
        # `base_seed + done_pairs` und `n_games=n` auf, Spielindex 0..n-1
        # entspricht Paar `done_pairs..done_pairs+n-1`.
        seed = base_seed + done_pairs
        t0 = time.time()
        won_o1, won_o2 = play_pair_fn(mr, n, seed)
        dur = time.time() - t0

        for i in range(n):
            cand_wins_pair = int(won_o1[i]) + int(won_o2[i])
            ref_wins_pair = 2 - cand_wins_pair
            cand_wins_total += cand_wins_pair
            ref_wins_total += ref_wins_pair
            pair_diffs.append(cand_wins_pair - ref_wins_pair)
            if cand_wins_pair == 2:
                cand_sweeps += 1
            elif ref_wins_pair == 2:
                ref_sweeps += 1
            else:
                splits += 1

        done_pairs += n
        block_idx += 1
        report_p = mcnemar_exact_p(cand_sweeps, ref_sweeps)
        mean_d, ci_lo, ci_hi = paired_ci(pair_diffs)
        block_log = {
            "block": block_idx, "seed_base": seed, "n_pairs_block": n, "done_pairs": done_pairs,
            "cand_wins_total": cand_wins_total, "ref_wins_total": ref_wins_total,
            "cand_sweeps": cand_sweeps, "ref_sweeps": ref_sweeps, "splits": splits,
            "mcnemar_p": report_p, "mean_pair_diff": mean_d, "ci95": [ci_lo, ci_hi],
            "duration_s": dur,
        }
        block_logs.append(block_log)
        n_games_so_far = done_pairs * 2
        winrate = cand_wins_total / n_games_so_far if n_games_so_far else 0.0
        print(f"  [{name}] Block {block_idx} (n={n} Paare, {dur:.1f}s): kumulativ "
              f"Kandidat {cand_wins_total}:{ref_wins_total} Referenz | Paare {done_pairs} "
              f"(Sweep_Kand={cand_sweeps} Sweep_Ref={ref_sweeps} Split={splits}) | "
              f"Winrate {winrate:.1%} | McNemar p={report_p:.4f} | gepaarte Diff {mean_d:+.3f} "
              f"[{ci_lo:+.3f},{ci_hi:+.3f}]", flush=True)

    n_games_total = done_pairs * 2
    winrate = cand_wins_total / n_games_total if n_games_total else 0.0
    final_p = mcnemar_exact_p(cand_sweeps, ref_sweeps)
    mean_d, ci_lo, ci_hi = paired_ci(pair_diffs)
    result = {
        "cell": name, "done_pairs": done_pairs, "n_games_total": n_games_total,
        "cand_wins_total": cand_wins_total, "ref_wins_total": ref_wins_total,
        "cand_winrate": winrate,
        "cand_sweeps": cand_sweeps, "ref_sweeps": ref_sweeps, "splits": splits,
        "mcnemar_p": final_p, "mean_pair_diff": mean_d, "ci95_pair_diff": [ci_lo, ci_hi],
        "base_seed": base_seed, "sims": sims, "threads": threads,
        "duration_s_total": time.time() - t_cell_start,
        "blocks": block_logs,
    }
    print(f"=== Zelle '{name}' fertig: Kandidat {cand_wins_total}:{ref_wins_total} Referenz "
          f"({winrate:.1%}, {n_games_total} Spiele, {done_pairs} Paare) -- "
          f"{result['duration_s_total']:.0f}s ===", flush=True)

    out_path = out_dir / f"hybrid_arena_{name}.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"  Ergebnis gespeichert: {out_path}", flush=True)
    return result


def main() -> None:
    p = argparse.ArgumentParser(description="Task #88: Hybrid-Suche 2x2 gepaarter Arena-Runner")
    p.add_argument("--v10", default=str(BASE_DIR / "models" / "alphazero_v10_best.onnx"))
    p.add_argument("--v12", default=str(BASE_DIR / "models" / "alphazero_v12_best.onnx"))
    p.add_argument("--sims", type=int, default=DEFAULT_SIMS)
    p.add_argument("--c-puct", type=float, default=DEFAULT_C_PUCT)
    p.add_argument("--n-pairs-anchor", type=int, default=50)
    p.add_argument("--n-pairs-hybrid", type=int, default=60)
    p.add_argument("--block-size", type=int, default=BLOCK_SIZE)
    p.add_argument("--threads", type=int, default=DEFAULT_THREADS)
    p.add_argument("--seed", type=int, default=20260724)
    p.add_argument("--cells", default="anchor,hybrid_pv,hybrid_vp",
                    help="Komma-getrennt: welche Zellen laufen sollen")
    p.add_argument("--out-dir", default=str(BASE_DIR / "evaluations"))
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cells = set(c.strip() for c in args.cells.split(","))

    print(f"Task #88 Hybrid-Arena: v10={args.v10}")
    print(f"                       v12={args.v12}")
    print(f"  sims={args.sims} c_puct={args.c_puct} threads={args.threads} "
          f"base_seed={args.seed}", flush=True)

    results = {}

    # WICHTIG: derselbe `args.seed`-Basiswert fuer alle drei Zellen (Vorgabe
    # "gleiche Seeds ueber alle Zellen") -- Paar i nutzt in jeder Zelle
    # denselben abgeleiteten Seed `args.seed + i`.
    if "anchor" in cells:
        def play_anchor(mr, n, seed):
            return play_pair_block_plain(mr, args.v12, args.v10, args.sims, args.c_puct, n, seed, args.threads)
        results["anchor"] = run_cell(
            "anchor_v12_vs_v10", play_anchor, args.n_pairs_anchor, args.seed,
            args.block_size, args.sims, args.threads, out_dir,
        )

    if "hybrid_pv" in cells:
        # P=v10 (Priors/Moon von v10_best), V=v12 (Blattwert von v12_best).
        def play_hybrid_pv(mr, n, seed):
            return play_pair_block_hybrid(
                mr, args.v10, args.v12, args.v10, args.sims, args.c_puct, n, seed, args.threads
            )
        results["hybrid_pv"] = run_cell(
            "hybrid_P-v10_V-v12", play_hybrid_pv, args.n_pairs_hybrid, args.seed,
            args.block_size, args.sims, args.threads, out_dir,
        )

    if "hybrid_vp" in cells:
        # P=v12 (Priors/Moon von v12_best), V=v10 (Blattwert von v10_best).
        def play_hybrid_vp(mr, n, seed):
            return play_pair_block_hybrid(
                mr, args.v12, args.v10, args.v10, args.sims, args.c_puct, n, seed, args.threads
            )
        results["hybrid_vp"] = run_cell(
            "hybrid_P-v12_V-v10", play_hybrid_vp, args.n_pairs_hybrid, args.seed,
            args.block_size, args.sims, args.threads, out_dir,
        )

    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG (2x2-Design, Referenz immer v10_best):")
    for name, r in results.items():
        print(f"  {r['cell']:30s} {r['cand_wins_total']:3d}:{r['ref_wins_total']:<3d} "
              f"({r['cand_winrate']:.1%}, n={r['n_games_total']}) "
              f"McNemar p={r['mcnemar_p']:.4f}")


if __name__ == "__main__":
    main()
