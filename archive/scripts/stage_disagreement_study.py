"""Sucht Stufe1/Stufe2-Meinungsverschiedenheiten in Stufe-1-geführten Partien und
prüft per Rollout, ob Stufe 2s abweichende Wahl im Mittel zu einem besseren
Score-Vorsprung führt (Mehrrunden-Vorsicht-Hypothese, siehe stage2_investigation.md).

Nutzung:
  python evaluations/scripts/stage_disagreement_study.py --model alphazero_v2.onnx \
      --games 40 --sims 100 --reps 6 --out evaluations/sweep_repeat_logs/disagreements_v2.json
"""
import sys
import json
import time
import argparse
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import mosaic_rust as _mr

ROOT = Path(__file__).resolve().parents[2]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", type=str, required=True, help="Dateiname in models/ oder voller Pfad")
    p.add_argument("--games", type=int, default=40)
    p.add_argument("--sims", type=int, default=100)
    p.add_argument("--c-puct", dest="c_puct", type=float, default=1.5)
    p.add_argument("--reps", type=int, default=6, help="Rollouts je Zweig (Mittelung ueber Zufall)")
    p.add_argument("--max-per-round", dest="max_per_round", type=int, default=2,
                   help="Max. ausgewertete Faelle je Runde und Spiel (Stichprobe, begrenzt Rollout-Kosten)")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--threads", type=int, default=0)
    p.add_argument("--out", type=str, required=True)
    args = p.parse_args()

    model = args.model
    mp = Path(model)
    if not mp.exists():
        mp = ROOT / "models" / model
    if not mp.exists():
        raise SystemExit(f"Modell nicht gefunden: {model}")

    print(f"Starte Stufe1/Stufe2-Disagreement-Studie: {args.games} Spiele | Modell {mp.name} | "
          f"sims {args.sims} | reps {args.reps} | max/Runde {args.max_per_round} | "
          f"Threads {args.threads or 'alle Kerne'}")
    t0 = time.time()
    raw = _mr.stage_disagreement_study(
        model_path=str(mp), n_games=args.games, base_sims=args.sims, c_puct=args.c_puct,
        n_reps=args.reps, max_per_round=args.max_per_round, seed=args.seed, num_threads=args.threads,
    )
    elapsed = time.time() - t0
    data = json.loads(raw)
    print(f"Fertig in {elapsed:.1f}s. {len(data)} Meinungsverschiedenheiten gefunden.")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"Gespeichert: {out_path}")

    if data:
        n = len(data)
        n_s2_better = sum(1 for d in data if d["stage2_mean_diff"] > d["stage1_mean_diff"])
        n_s1_better = sum(1 for d in data if d["stage1_mean_diff"] > d["stage2_mean_diff"])
        n_tie = n - n_s2_better - n_s1_better
        avg_diff = sum(d["stage2_mean_diff"] - d["stage1_mean_diff"] for d in data) / n
        print(f"Gesamt — Stufe 2 im Rollout besser: {n_s2_better}/{n} | Stufe 1 besser: {n_s1_better}/{n} | "
              f"gleich: {n_tie}/{n} | mittlere Differenz (Stufe2-Stufe1 Score-Vorsprung): {avg_diff:+.2f}")

        by_round = {}
        for d in data:
            by_round.setdefault(d["round"], []).append(d)
        print("Je Runde:")
        for r in sorted(by_round):
            grp = by_round[r]
            m = len(grp)
            s2b = sum(1 for d in grp if d["stage2_mean_diff"] > d["stage1_mean_diff"])
            s1b = sum(1 for d in grp if d["stage1_mean_diff"] > d["stage2_mean_diff"])
            adiff = sum(d["stage2_mean_diff"] - d["stage1_mean_diff"] for d in grp) / m
            print(f"  Runde {r}: n={m} | Stufe2 besser {s2b} | Stufe1 besser {s1b} | Diff {adiff:+.2f}")


if __name__ == "__main__":
    main()
