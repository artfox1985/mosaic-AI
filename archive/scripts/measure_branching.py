"""Misst reale Verzweigungsbreite (num_actions) je Runde und Gesamtzugzahl,
direkt aus der Engine (Stufe 1, Netz-gefuehrt) -- fuer die Stufe-3-Rollout-
Kalibrierung (top_k/n_reps/sims), siehe evaluations/stage2_investigation.md.
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

N_GAMES = 20
MODEL = "models/alphazero_v2.onnx"

by_round = defaultdict(list)      # round -> [num_actions je Drafting-Entscheidung]
draft_decisions_per_round = defaultdict(list)  # round -> [Anzahl Drafting-Entscheidungen in dieser Runde, je Spiel]
total_steps = []
total_draft_decisions = []

for gi in range(N_GAMES):
    g = mr.PyGame((f"A{gi}", f"B{gi}"), seed=1000 + gi)
    g.load_net(MODEL)
    steps = 0
    draft_count = 0
    round_draft_count = defaultdict(int)
    guard = 0
    # WICHTIG: nicht "while not g.is_over()" -- is_over() prueft nur
    # round_number >= NUM_ROUNDS und wird schon beim EINTRITT in Runde 5 wahr,
    # nicht erst wenn sie gespielt ist (die Produktions-Loops in self_play.rs
    # pruefen deshalb korrekt nur die Phase, nie is_over() als Schleifen-
    # bedingung). Hier genauso: auf die Phase reagieren, bis sie "end"/etwas
    # Unbehandeltes erreicht.
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
            res = json.loads(g.ai_step_net_json(simulations=100, c_puct=1.5, stage=1))
            na = res.get("debug", {}).get("num_actions")
            if na is not None:
                by_round[r].append(na)
            draft_count += 1
            round_draft_count[r] += 1
            steps += 1
        elif phase == "tiling":
            g.ai_step_net_json(simulations=100, c_puct=1.5, stage=1)
            steps += 1
        else:
            break
    for r, c in round_draft_count.items():
        draft_decisions_per_round[r].append(c)
    total_steps.append(steps)
    total_draft_decisions.append(draft_count)
    print(f"Spiel {gi+1}/{N_GAMES}: {steps} Züge gesamt, {draft_count} Drafting-Entscheidungen", flush=True)

print("\n=== Verzweigungsbreite (num_actions) je Runde ===")
for r in sorted(by_round):
    vals = by_round[r]
    print(f"  Runde {r}: n={len(vals)} | Ø={st.mean(vals):.1f} | min={min(vals)} max={max(vals)}")

print("\n=== Drafting-Entscheidungen je Runde (beide Spieler zusammen) ===")
for r in sorted(draft_decisions_per_round):
    vals = draft_decisions_per_round[r]
    print(f"  Runde {r}: Ø={st.mean(vals):.1f} je Spiel")

print(f"\nGesamt-Züge/Spiel: Ø={st.mean(total_steps):.1f} (min {min(total_steps)}, max {max(total_steps)})")
print(f"Gesamt-Drafting-Entscheidungen/Spiel (beide Spieler): Ø={st.mean(total_draft_decisions):.1f}")

# Verbleibende Drafting-Entscheidungen AB Runde r bis Spielende (fuer Rollout-Kosten-Schaetzung)
rounds_sorted = sorted(draft_decisions_per_round)
avg_per_round = {r: st.mean(draft_decisions_per_round[r]) for r in rounds_sorted}
print("\n=== Ø verbleibende Drafting-Entscheidungen AB Runde r (Rollout-Horizont) ===")
for r in rounds_sorted:
    remaining = sum(avg_per_round[rr] for rr in rounds_sorted if rr >= r)
    print(f"  ab Runde {r}: Ø noch {remaining:.1f} Drafting-Entscheidungen bis Spielende")
