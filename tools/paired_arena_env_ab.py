# -*- coding: utf-8 -*-
"""tools/paired_arena_env_ab.py -- generischer gepaarter Zwei-Arm-A/B fuer
LAUFZEIT-Env-Knoepfe (PREREG_search_path_remeasurements.md, Amendment
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

# Selbe Parse-Regel wie der Worker -- EIN Import statt eines zweiten,
# potenziell abweichenden Parsers (Orchestrator schneidet die Liste
# blockweise, der Worker parst sie am Ende wieder; beide muessen dieselbe
# Regel anwenden). Der Import loest KEIN mosaic_rust aus (das passiert im
# Worker erst innerhalb von `main()`).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paired_arena_arm_worker import parse_seeds  # noqa: E402


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
            n_games: int, seed: int, block_size: int, threads: int,
            log_games: bool = False, seeds: list[int] | None = None,
            model_b: str | None = None, sims_b: int | None = None,
            spec_a: str | None = None, spec_b: str | None = None) -> list[dict]:
    """`env_name` darf mehrere komma-getrennte Var-Namen tragen; `value`
    dann entsprechend viele komma-getrennte Werte (Aggressions-
    Neukartierung: W und LAMBDA je Arm gemeinsam gesetzt).

    `seeds` (Plattenkopf-Versuch, `PREREG_plate_head.md`, 2026-08-11):
    explizite Pro-Partie-Seed-Liste -- ERSETZT die `block_seed = seed +
    block_idx * 1_000_000`-Ableitung. Mit einer expliziten Liste muss der
    Orchestrator sie BLOCKWEISE aufteilen (statt je Block einen neuen
    Basis-Seed zu bilden), sonst bekaeme der Worker in jedem Block wieder
    `seeds[0:block_size]` (falsch verschoben, keine Kontrolle mehr darueber,
    welche Partie welchen Seed bekommt). `n_games` folgt dann `len(seeds)`
    (mit Warnung, falls `--n-games` abweicht) -- dieselbe "eine Quelle der
    Wahrheit"-Regel wie engine-seitig (`net_arena_match`)."""
    env = os.environ.copy()
    names = [n.strip() for n in env_name.split(",")]
    vals = [v.strip() for v in value.split(",")]
    if len(names) != len(vals):
        raise SystemExit(f"Arm {value!r}: {len(vals)} Werte fuer {len(names)} Env-Vars")
    for n, v in zip(names, vals):
        env[n] = v

    if seeds is not None:
        if n_games != len(seeds):
            print(f"WARNUNG: --n-games {n_games} weicht von --seeds-Laenge "
                  f"{len(seeds)} ab -- die Listenlaenge gewinnt.", flush=True)
        n_games = len(seeds)

    games: list[dict] = []
    done, block_idx = 0, 0
    gegner = (f"{os.path.basename(model_b)}@{sims_b or net_sims}" if model_b
              else f"Heuristik@{heur_sims}(dyn)")
    print(f"Arm {env_name}={value}: {os.path.basename(model)}@{net_sims} vs "
          f"{gegner}, "
          + (f"{len(seeds)} explizite Seeds" if seeds is not None else f"Basis-Seed={seed}")
          + f", n={n_games}", flush=True)
    while done < n_games:
        n = min(block_size, n_games - done)
        cmd = [sys.executable, str(WORKER), "--model", model,
               "--net-sims", str(net_sims), "--heur-sims", str(heur_sims),
               "--n-games", str(n), "--threads", str(threads)]
        if model_b:
            cmd += ["--model-b", model_b]
            if sims_b is not None:
                cmd += ["--sims-b", str(sims_b)]
            # 2026-08-23 (Agenten-Kapselung Welle 1): per-Seite Spec-JSON.
            if spec_a is not None:
                cmd += ["--spec-a", spec_a]
            if spec_b is not None:
                cmd += ["--spec-b", spec_b]
        if seeds is not None:
            # BLOCKWEISE Teilliste, nicht ein neu abgeleiteter Basis-Seed --
            # das ist die delikate Stelle: mit einer expliziten Liste gibt es
            # keine Formel mehr, aus der ein Block-Seed sinnvoll folgen
            # koennte, also muss der Orchestrator die ECHTEN Seeds weitergeben.
            block_seeds = seeds[done:done + n]
            cmd += ["--seeds", ",".join(str(s) for s in block_seeds)]
            block_label = f"Seeds={block_seeds[0]}..{block_seeds[-1]}"
        else:
            block_seed = seed + block_idx * 1_000_000
            cmd += ["--seed", str(block_seed)]
            block_label = f"Seed={block_seed}"
        if log_games:
            # 2026-08-11: Partie-Logs mitfuehren, damit die VERHALTENS-Zahlen
            # (Nahmen-Anteil tiefe Reihen, Freischaltungen, Zellen je Reihe)
            # aus DENSELBEN Partien kommen wie die Siegquote. Ohne das braeuchte
            # die Verhaltensmessung einen zweiten Lauf ueber dieselben Stunden.
            cmd += ["--log-games"]
        t0 = time.time()
        proc = subprocess.run(
            cmd,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=ARM_TIMEOUT_SECS, env=env,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Arm {value} Block {block_idx} ({block_label}) "
                               f"rc={proc.returncode}: {proc.stderr[-2000:]}")
        block = json.loads(proc.stdout)
        games.extend(block)
        done += n
        block_idx += 1
        wins = sum(1 for g in games if g["winner"] == 0)
        print(f"  [{value}] Block {block_idx} ({block_label}, n={n}, "
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
    # 2026-08-16 (Destillations-Messung, PREREG_corpus_distillation.md par.4.2,
    # Nutzer-Einwand "die Gegnerwahl ist selbst eine Variable"): Gegner-Netz
    # statt Heuristik. Reicht nur durch -- die Umschaltung sitzt im Worker
    # (`--model-b` dort), damit es genau EINE Stelle gibt, die entscheidet,
    # welche Arena-Funktion gerufen wird. Ohne den Schalter unveraendert.
    ap.add_argument("--model-b", default=None,
                    help="Gegner-ONNX auf Brett 1 -> Netz-gegen-Netz statt "
                         "Netz-gegen-Heuristik (Brett-Tausch: zweiter Lauf mit "
                         "vertauschten --model/--model-b und eigenem --out-prefix)")
    ap.add_argument("--sims-b", type=int, default=None,
                    help="Sims fuer --model-b (Default: gleich --net-sims)")
    ap.add_argument("--net-sims", type=int, default=400)
    ap.add_argument("--heur-sims", type=int, default=150)
    ap.add_argument("--n-games", type=int, default=200,
                    help="Ignoriert (mit Warnung), wenn --seeds gesetzt ist -- "
                         "dann gilt die Seed-Listenlaenge")
    ap.add_argument("--seed", type=int, default=None,
                    help="Basis-Seed (Pflicht, ausser --seeds ist gesetzt)")
    # 2026-08-11 (Plattenkopf-Versuch, PREREG_plate_head.md): explizite
    # Pro-Partie-Seeds statt der `seed + block_idx*1_000_000`-Ableitung --
    # siehe `run_arm`-Docstring fuer die Blockaufteilungs-Regel. Format wie
    # beim Worker: kommagetrennt ODER Datei-Pfad (eine Zahl je Zeile), z.B.
    # das Ausgabeformat von `tools/seed_selection_plates.py`.
    ap.add_argument("--seeds", type=str, default=None,
                    help="Explizite Pro-Partie-Seeds, kommagetrennt ODER "
                         "Datei-Pfad (eine Zahl je Zeile) -- ersetzt --seed "
                         "UND --n-games")
    ap.add_argument("--block-size", type=int, default=25)
    ap.add_argument("--threads", type=int, default=10)
    ap.add_argument("--out-prefix", required=True)
    # 2026-08-11: Partie-Logs je Arm mitfuehren (reicht `--log-games` an den
    # Worker und damit an `net_arena_match`s `log_games` weiter, Commit
    # 9dfeb16). Default AUS = Bestandsverhalten, Ergebnis-JSON exakt wie bisher.
    ap.add_argument("--log-games", action="store_true",
                    help="Partie-Logs mitschreiben, damit die Verhaltenszahlen "
                         "aus DENSELBEN Partien kommen wie die Siegquote")
    # 2026-08-23 (PREREG_agent_encapsulation.md par.4a): per-Seite
    # SearchConfig-Specs fuer den Netz-gegen-Netz-Modus (--model-b).
    ap.add_argument("--spec-a", type=str, default=None,
                    help="Spec-JSON fuer Brett 0 (nur mit --model-b)")
    ap.add_argument("--spec-b", type=str, default=None,
                    help="Spec-JSON fuer Brett 1 (nur mit --model-b)")
    args = ap.parse_args()

    if args.control not in args.arms:
        raise SystemExit("--control muss in --arms enthalten sein")
    model = args.model or champion_model()

    seeds = parse_seeds(args.seeds) if args.seeds else None
    if seeds is None and args.seed is None:
        raise SystemExit("--seed oder --seeds ist erforderlich")
    n_games = len(seeds) if seeds is not None else args.n_games

    results: dict[str, list[dict]] = {}
    for v in args.arms:
        results[v] = run_arm(args.env_name, v, model, args.net_sims,
                             args.heur_sims, args.n_games, args.seed,
                             args.block_size, args.threads,
                             log_games=args.log_games, seeds=seeds,
                             model_b=args.model_b, sims_b=args.sims_b,
                             spec_a=args.spec_a, spec_b=args.spec_b)

    out = {
        "env_name": args.env_name, "arms": args.arms, "control": args.control,
        "model": model, "model_b": args.model_b,
        "sims_b": args.sims_b if args.model_b else None,
        "spec_a": args.spec_a, "spec_b": args.spec_b,
        "net_sims": args.net_sims, "heur_sims": args.heur_sims,
        "n_games": n_games, "base_seed": args.seed,
        "seeds": seeds,
        "arm_wins": {}, "comparisons": {},
        "games": {v: results[v] for v in args.arms},
    }
    ctrl = results[args.control]
    print("\n=== AUSWERTUNG (gepaart je Spielindex, Netz-Sieg = winner==0) ===")
    for v in args.arms:
        wins = sum(1 for g in results[v] if g["winner"] == 0)
        out["arm_wins"][v] = wins
        print(f"Arm {args.env_name}={v}: Netz {wins}/{n_games}")
    for v in args.arms:
        if v == args.control:
            continue
        b = c = 0
        for i in range(n_games):
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

    out_path = EVAL_DIR / "artifacts" / f"paired_arena_env_{args.out_prefix}.json"
    out_path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nErgebnis: {out_path}")


if __name__ == "__main__":
    main()
