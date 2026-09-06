#!/usr/bin/env bash
# Champion-Kante fuer v24-b05 in SPIELKONFIGURATION (Nutzer 2026-09-06, 11:55: "starte A"):
# b05 OHNE Knopf (k3v_off, so faehrt er als Generator) gegen den amtierenden Champion v23-b01 MIT
# Champion-Spec (K3-P C 1,0). Zwei Seeds unbedingt (Champion-Strenge, promotion_checklist Punkt 2),
# Deckel 200 Paare, keine Promotion. Einziger CPU-Auftrag; daneben darf das GPU-Training b06 laufen.
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/champion_edge_b05.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART="evaluations/artifacts"
for SEED in 20261012 20261013; do
  echo "== Champion-Kante b05 (k3v_off) gegen v23-b01_k3p10 (Champion-Spec), Seed $SEED $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py --model-a models/alphazero_v24-b05_brierbest.onnx --model-b models/alphazero_v23-b01_brierbest.onnx --name-a v24-b05 --name-b v23-b01_k3p10 --spec-a models/k3v_off.spec.json --spec-b models/v23-b01_k3p10.spec.json --sims 400 --max-pairs 200 --seed "$SEED" --no-promote-winner --out "$ART/paired_gating_result_v24-b05nk_vs_v23-b01_k3p10_s${SEED: -2}.json"
  echo "   Exit $? ($(date +%H:%M:%S))"
done
echo "== FERTIG $(date +%H:%M:%S): Registrierung (Elo-Kante v24-b05 gegen v23-b01_k3p10, knobs gemischt) durch den Koordinator."
