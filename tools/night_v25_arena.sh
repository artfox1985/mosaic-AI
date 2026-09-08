#!/usr/bin/env bash
# Tor 1 fuer v25-b01: gepaartes Gating gegen den amtierenden Champion v24-b07.
# Nutzer-Auftrag 2026-09-08: "dann kurzer arena zwischenstand gegen den champ und
# gegebenenfalls promotion."
#
# BEIDE Seiten fahren die Champion-Spec: die Spec ist seit par.18 fuer v25 bis v27
# geschlossen, es wird nur das NETZ verglichen.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
SPEC=models/v24-b07_brierbest.spec.json
echo "== Tor 1: v25-b01 gegen v24-b07 $(date +%H:%M:%S)"
python -X utf8 -u tools/paired_gating.py \
  --model-a models/alphazero_v25-b01_brierbest.onnx \
  --model-b models/alphazero_v24-b07_brierbest.onnx \
  --name-a v25-b01 --name-b v24-b07 \
  --spec-a "$SPEC" --spec-b "$SPEC" \
  --sims 400 --block-size 5 --max-pairs 200 --seed 20261021 --threads 10 \
  --no-promote-winner \
  --out evaluations/artifacts/paired_gating_v25-b01_vs_v24-b07_s21.json
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== ARENA FERTIG $(date +%H:%M:%S)"
