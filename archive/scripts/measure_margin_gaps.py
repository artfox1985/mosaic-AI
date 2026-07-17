"""Misst die reale Verteilung des Besuchsanteil-Abstands (Top1-Top2 mcts_share)
je Drafting-Entscheidung -- fuer die Stufe-3-margin-Kalibrierung (siehe
evaluations/stage2_investigation.md). Nur die guenstige Shortlist-Suche, kein
Rollout noetig.
"""
import sys
import json
import statistics as st
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import mosaic_rust as mr

N_GAMES = 8
MODEL = "models/alphazero_v2.onnx"

gaps_by_round = defaultdict(list)
q_gaps_by_round = defaultdict(list)

for gi in range(N_GAMES):
    g = mr.PyGame((f"A{gi}", f"B{gi}"), seed=2000 + gi)
    g.load_net(MODEL)
    guard = 0
    while True:
        guard += 1
        if guard >= 5000:
            break
        phase = g.phase()
        if phase == "start_placement":
            state = json.loads(g.state_json())
            done_any = False
            for pi, p in enumerate(state.get("players", [])):
                if p.get("start_tile_pending"):
                    g.ai_start_tile_json(pi)
                    done_any = True
                    break
            if not done_any:
                break
        elif phase == "drafting":
            r = g.round_number()
            analysis = json.loads(g.ai_debug_net_json(simulations=100, c_puct=1.5, stage=1))
            moves = analysis.get("moves", [])
            shares = sorted((m["mcts_share"] for m in moves), reverse=True)
            if len(shares) >= 2:
                gaps_by_round[r].append(shares[0] - shares[1])
            qs = sorted((m["mcts_q"] for m in moves if m.get("mcts_q") is not None), reverse=True)
            if len(qs) >= 2:
                q_gaps_by_round[r].append(qs[0] - qs[1])
            # Zug wirklich anwenden (wie Stufe 1), damit das Spiel weiterlaeuft.
            res = json.loads(g.ai_step_net_json(simulations=100, c_puct=1.5, stage=1))
            if not res.get("applied"):
                break
        elif phase == "tiling":
            res = json.loads(g.ai_step_net_json(simulations=100, c_puct=1.5, stage=1))
            if not res.get("applied"):
                break
        else:
            break
    print(f"Spiel {gi+1}/{N_GAMES} fertig", flush=True)

print("\n=== Besuchsanteil-Abstand (Top1-Top2) je Runde ===")
all_gaps = []
for r in sorted(gaps_by_round):
    vals = gaps_by_round[r]
    all_gaps.extend(vals)
    vals_sorted = sorted(vals)
    n = len(vals_sorted)
    p25 = vals_sorted[int(n * 0.25)]
    p50 = vals_sorted[int(n * 0.50)]
    p75 = vals_sorted[int(n * 0.75)]
    print(f"  Runde {r}: n={n} | Ø={st.mean(vals):.3f} | p25={p25:.3f} p50={p50:.3f} p75={p75:.3f}")

print("\n=== Anteil Entscheidungen UNTER verschiedenen margin-Schwellen (Besuchsanteil, gesamt) ===")
all_gaps.sort()
n = len(all_gaps)
for margin in [0.02, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30]:
    below = sum(1 for x in all_gaps if x < margin)
    print(f"  margin={margin:.2f}: {below}/{n} ({below/n*100:.1f}%) würden den Rollout auslösen "
          f"(Abstand < margin)")

print("\n=== Q-Wert-Abstand (Top1-Top2, Score-Punkte) je Runde ===")
all_q = []
for r in sorted(q_gaps_by_round):
    vals = q_gaps_by_round[r]
    all_q.extend(vals)
    vals_sorted = sorted(vals)
    n2 = len(vals_sorted)
    p25 = vals_sorted[int(n2 * 0.25)]
    p50 = vals_sorted[int(n2 * 0.50)]
    p75 = vals_sorted[int(n2 * 0.75)]
    print(f"  Runde {r}: n={n2} | Ø={st.mean(vals):.2f} | p25={p25:.2f} p50={p50:.2f} p75={p75:.2f}")

print("\n=== Anteil Entscheidungen UNTER verschiedenen Q-margin-Schwellen (gesamt) ===")
print("(Q lebt in [0,1] -- normalize_score = (tanh(score/50)+1)/2, also winzige Zahlen normal)")
all_q.sort()
n2 = len(all_q)
for margin in [0.002, 0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12]:
    below = sum(1 for x in all_q if x < margin)
    print(f"  Q-margin={margin:.3f}: {below}/{n2} ({below/n2*100:.1f}%) würden den Rollout auslösen "
          f"(Abstand < margin)")
