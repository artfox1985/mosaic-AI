#!/usr/bin/env bash
# Tor 1 der v28-Generation: v28-b01 gegen v27-b01 (Champion aus dem eingefrorenen
# Artefakt), beide Seiten Champion-Spec, nur das NETZ verglichen, @400, Blockgroesse 5,
# 10 Threads, MIT --log-games (Tor 2b aus denselben Partien), zwei Seeds nacheinander.
# Muster: PREREG_v27_window.md par.9 (Seeds 20261034/35); hier 20261036/37.
# Aufruf: bash tools/night_v28_tor1.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
NET=models/alphazero_v28-b01_brierbest.onnx
CHAMP=models/frozen_champions/v27-b01/model.onnx
SPEC=models/frozen_champions/v27-b01/spec.json
for S in 36 37; do
  echo "== TOR 1 Seed 202610$S: v28-b01 gegen v27-b01 $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$NET" --model-b "$CHAMP" \
    --name-a v28-b01 --name-b v27-b01 \
    --spec-a "$SPEC" --spec-b "$SPEC" \
    --sims 400 --block-size 5 --max-pairs 200 --seed "202610$S" --threads 10 \
    --log-games --no-promote-winner --out "$ART/paired_gating_v28-b01_vs_v27-b01_s$S.json"
  echo "   Exit $? ($(date +%H:%M:%S))"
done
echo "== TOR 1 FERTIG $(date +%F' '%H:%M:%S)"
