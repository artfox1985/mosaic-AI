# -*- coding: utf-8 -*-
"""PREREG_deterministic_labels.md §2 Stufe 1: Feuerraten-Messung der
Not-Deckel in round_transition.rs/round_transition_deep.rs. Reine Diagnose
(kein Verhaltenseingriff) -- ~50 Partien ueber run_net_self_play unter
normaler Last (kein kuenstlicher CPU-Stress, das ist erst Abnahme-Schritt 2).
"""
from __future__ import annotations

import json
import sys

import mosaic_rust as mr

N_GAMES = 50
SIMS = 400
SEED = 20260814
THREADS = 8
MODEL = "models/alphazero_v21_2d_brierbest.onnx"

mr.reset_not_deckel_diagnostics()
print(f"Starte {N_GAMES} Partien (sims={SIMS}, threads={THREADS}, seed={SEED})...", file=sys.stderr)
raw = mr.net_self_play_games(
    model_path=MODEL,
    n_games=N_GAMES,
    base_sims=SIMS,
    c_puct=1.5,
    seed=SEED,
    num_threads=THREADS,
    prefix="not_deckel_probe",
    add_root_noise=True,
    deterministic=False,
    record_rtv=True,  # rtv MIT einschliessen -- genau der Pfad, der auch die kontinue_through_roundX-Kette durchlaeuft
)
records = json.loads(raw)
n_games_seen = len({r["game_id"] for r in records if "game_id" in r})
print(f"{len(records)} Step-Records, {n_games_seen} Partien.", file=sys.stderr)

diag = json.loads(mr.not_deckel_diagnostics_json())
print(json.dumps(diag, indent=2))


def rate(fires_key: str, checks_key: str) -> str:
    fires = diag[fires_key]
    checks = diag[checks_key]
    if checks == 0:
        return f"{fires_key}: 0/0 (nie erreicht)"
    return f"{fires_key}/{checks_key}: {fires}/{checks} = {100.0 * fires / checks:.4f}%"


print("\n--- Feuerraten je Not-Deckel-Stelle ---")
print(rate("sample_transition_deadline_fires", "sample_transition_checks"))
print(f"  davon sample_transition_zero_result (schwerster Fall): {diag['sample_transition_zero_result']}")
print(rate("drafting_loop_deadline_fires", "drafting_loop_checks"))
print(rate("gamma_full_deadline_fires", "gamma_full_checks"))
print(rate("negamax_entry_deadline_fires", "negamax_entry_checks"))
print(rate("negamax_loop_deadline_fires", "negamax_loop_checks"))
print(rate("simulate_round_deadline_fires", "simulate_round_checks"))
print(f"  simulate_round_guard_fires (Kontext, kein Not-Deckel): {diag['simulate_round_guard_fires']}")
