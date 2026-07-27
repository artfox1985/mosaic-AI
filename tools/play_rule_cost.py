# -*- coding: utf-8 -*-
"""Task #13: Was kostet die Play-Regel (visit-proportionales Sampling auf einem
Sequential-Halving-Baum)? -- Messung, 2026-07-28.

## Frage

`self_play.rs::net_drafting_policy` waehlt die tatsaechlich gespielte Aktion
proportional zu den ROHEN Besuchszahlen der Wurzelkandidaten. Bei Sequential
Halving sind Besuche aber ein Artefakt des Fahrplans, kein Qualitaetssignal:
jeder Kandidat behaelt seine Phase-1-Sims dauerhaft, auch wenn er sich als
schlecht erwiesen hat. Rechnerisch (sims=400, TOP_M=16) landen 12% der
Spielwahrscheinlichkeit auf in Phase 1 verworfenen Kandidaten.

Dieses Skript misst den EFFEKT davon empirisch, statt dem Modell zu trauen:
wieviel Qualitaet (completed-Q) wirft die Play-Regel pro Zug weg?

## Methode

Fuer N echte Board-Zustaende aus dem Self-Play-Korpus wird EINE Suche
gefahren (`net_search_state_json`). Deren `moves[]` liefert je Wurzelkandidat
`mcts_visits` UND `mcts_q`. Daraus lassen sich MEHRERE Play-Regeln offline
aus DENSELBEN Suchdaten vergleichen -- kein erneutes Suchen noetig:

  - `visits`      : Ist-Zustand (proportional zu rohen Besuchen)
  - `argmax`      : immer der beste Kandidat (= Arena-Verhalten, kein Rauschen)
  - `survivors`   : proportional zu Besuchen, aber nur unter den Kandidaten
                    mit ueberdurchschnittlich vielen Besuchen (= die, die
                    mindestens eine Halbierungsrunde ueberlebt haben)
  - `q_softmax_T` : Softmax auf completed-Q statt auf Besuche (qualitaets-
                    gewichtet, Temperatur T)

Kennzahl je Regel: **erwarteter Q-Verlust je Zug** = Σ p_i · (Q_best − Q_i),
plus die Wahrscheinlichkeit, einen deutlich schlechteren Zug zu spielen.

`mcts_q` ist eine Gewinnwahrscheinlichkeit in [0,1] (siehe
`net_mcts.rs::value_to_win_prob`) -- ein Q-Verlust von 0,05 bedeutet also
5 Prozentpunkte Gewinnwahrscheinlichkeit, verschenkt in EINEM Zug.

## Nutzung

    python tools/play_rule_cost.py --model models/alphazero_v17_best.onnx \
        --n-states 30 --sims 400
"""
from __future__ import annotations

import argparse
import glob
import json
import pickle
import random
import statistics as stats
from pathlib import Path

import mosaic_rust

BASE_DIR = Path(__file__).resolve().parent.parent


def load_states(data_glob: str, n_states: int, seed: int) -> list[dict]:
    """Zieht zufaellige DRAFTING-Zustaende aus dem Korpus (nur Drafting: nur
    dort greift die Play-Regel; Tiling laeuft ueber den DFS-Solver)."""
    rng = random.Random(seed)
    files = sorted(glob.glob(data_glob))
    rng.shuffle(files)
    out: list[dict] = []
    for fp in files:
        with open(fp, "rb") as f:
            recs = pickle.load(f)
        cand = [r for r in recs if r["state"].get("phase") == "drafting"
                and not any(pe["action"].get("is_start") for pe in r["policy"])]
        rng.shuffle(cand)
        for r in cand:
            out.append(r["state"])
            if len(out) >= n_states:
                return out
    return out


# ── Play-Regeln: jede bildet (visits, qs) auf eine Wahrscheinlichkeitsverteilung ab ──

def rule_visits(visits, qs):
    tot = sum(visits)
    return [v / tot for v in visits] if tot else [1 / len(visits)] * len(visits)


def rule_argmax(visits, qs):
    best = max(range(len(qs)), key=lambda i: (visits[i], qs[i]))
    return [1.0 if i == best else 0.0 for i in range(len(qs))]


def rule_survivors(visits, qs):
    """Nur Kandidaten mit ueberdurchschnittlich vielen Besuchen -- die, die
    mindestens eine Halbierung ueberlebt haben. Der Mittelwert trennt die
    Phase-1-Ausgeschiedenen (die ihre Minimal-Sims behalten) sauber ab."""
    avg = sum(visits) / len(visits)
    keep = [v if v > avg else 0.0 for v in visits]
    tot = sum(keep)
    return [k / tot for k in keep] if tot else rule_visits(visits, qs)


def rule_q_softmax(temp):
    def f(visits, qs):
        m = max(qs)
        ex = [pow(2.718281828459045, (q - m) / temp) for q in qs]
        tot = sum(ex)
        return [e / tot for e in ex]
    return f


RULES = {
    "visits (IST)":      rule_visits,
    "argmax":            rule_argmax,
    "survivors":         rule_survivors,
    "q_softmax T=0.03":  rule_q_softmax(0.03),
    "q_softmax T=0.10":  rule_q_softmax(0.10),
}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default="models/alphazero_v17_best.onnx")
    p.add_argument("--data-glob", default="data/selfplay_v16_*.pkl")
    p.add_argument("--n-states", type=int, default=30)
    p.add_argument("--sims", type=int, default=400)
    p.add_argument("--c-puct", type=float, default=1.5)
    p.add_argument("--seed", type=int, default=1313)
    p.add_argument("--big-loss", type=float, default=0.05,
                   help="Schwelle fuer 'deutlich schlechterer Zug' in Q-Punkten (Default 0.05 = 5pp Gewinn-Wkt.)")
    p.add_argument("--out", default="evaluations/play_rule_cost.json")
    args = p.parse_args()

    model_path = str((BASE_DIR / args.model).resolve()) if not Path(args.model).is_absolute() else args.model
    states = load_states(args.data_glob, args.n_states, args.seed)
    print(f"[play_rule_cost] {len(states)} Drafting-Zustaende, sims={args.sims}, Modell={Path(model_path).name}")

    per_rule_loss: dict[str, list[float]] = {k: [] for k in RULES}
    per_rule_bigloss: dict[str, list[float]] = {k: [] for k in RULES}
    visit_shares: list[list[float]] = []
    n_cands: list[int] = []
    n_used = 0

    for i, st in enumerate(states):
        raw = mosaic_rust.net_search_state_json(
            json.dumps(st), model_path, args.sims, args.c_puct, args.seed + i)
        res = json.loads(raw)
        moves = [m for m in (res.get("moves") or []) if m.get("mcts_visits") is not None]
        if len(moves) < 2:
            continue
        visits = [float(m["mcts_visits"]) for m in moves]
        qs = [float(m["mcts_q"]) for m in moves]
        if sum(visits) <= 0:
            continue
        n_used += 1
        n_cands.append(len(moves))
        q_best = max(qs)
        for name, rule in RULES.items():
            probs = rule(visits, qs)
            per_rule_loss[name].append(sum(pr * (q_best - q) for pr, q in zip(probs, qs)))
            per_rule_bigloss[name].append(
                sum(pr for pr, q in zip(probs, qs) if (q_best - q) > args.big_loss))
        order = sorted(range(len(visits)), key=lambda k: -visits[k])
        tot = sum(visits)
        visit_shares.append([visits[k] / tot for k in order])
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(states)} Zustaende...", flush=True)

    print(f"\nAusgewertet: {n_used} Zustaende, Ø {stats.mean(n_cands):.1f} Wurzelkandidaten\n")
    print(f"{'Play-Regel':20s} {'Ø Q-Verlust/Zug':>16s} {'Median':>9s} "
          f"{'P(Verlust>' + format(args.big_loss, '.2f') + ')':>16s}")
    print("-" * 66)
    result = {"n_states": n_used, "sims": args.sims, "model": Path(model_path).name,
              "big_loss_threshold": args.big_loss, "avg_root_candidates": stats.mean(n_cands),
              "rules": {}}
    for name in RULES:
        ls, bl = per_rule_loss[name], per_rule_bigloss[name]
        result["rules"][name] = {
            "mean_q_loss": stats.mean(ls), "median_q_loss": stats.median(ls),
            "mean_p_big_loss": stats.mean(bl),
        }
        print(f"{name:20s} {stats.mean(ls):16.4f} {stats.median(ls):9.4f} {stats.mean(bl):15.1%}")

    # Wieviel Spielmasse liegt auf den schwaechsten Kandidaten? (Modellabgleich)
    maxlen = max(len(v) for v in visit_shares)
    padded = [v + [0.0] * (maxlen - len(v)) for v in visit_shares]
    avg_share = [stats.mean(col) for col in zip(*padded)]
    print(f"\nØ Spielwahrscheinlichkeit nach Besuchs-Rang (Regel 'visits'):")
    for lo, hi, lbl in ((0, 2, "Rang 1-2"), (2, 4, "Rang 3-4"),
                        (4, 8, "Rang 5-8"), (8, maxlen, f"Rang 9-{maxlen}")):
        if lo < maxlen:
            print(f"  {lbl:14s} {sum(avg_share[lo:hi]):6.1%}")
    result["avg_visit_share_by_rank"] = avg_share

    out = BASE_DIR / args.out
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nErgebnis: {out}")


if __name__ == "__main__":
    main()
