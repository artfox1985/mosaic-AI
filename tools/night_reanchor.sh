#!/usr/bin/env bash
# Neuverankerung der Elo-Leiter (PREREG_code_cleanup_closeout.md par.7a, Nutzer 2026-09-12):
# drei Anker-Kanten gegen das neue Artefakt hv1_anchor_v2 (festes n=150, Seed-Basis 900001,
# 6 Worker, Kandidat als ONNX plus Champion-Spec auf dem lebenden Wheel) und die
# Nachbar-Kante v28-b02 gegen v27-b01 (200 Paare mit Logs). Exklusiv, keine Nebenlast.
# Aufruf: bash tools/night_reanchor.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
ANCHOR=models/frozen_heuristics/hv1_anchor_v2
SPEC=models/frozen_champions/v27-b01/spec.json
for CAND in v28-b02 v28-b01 v27-b01; do
  echo "== ANKER-KANTE $CAND@400 gegen hv1_anchor_v2@150 $(date +%H:%M:%S)"
  python -X utf8 -u tools/frozen_referee_match.py --artifact-dir "$ANCHOR" \
    --model-a "models/alphazero_${CAND}_brierbest.onnx" --spec-a "$SPEC" --sims-a 400 \
    --n-games 150 --seed-base 900001 --workers 6 \
    --out "$ART/anchor_v2_arena_${CAND}.json"
  echo "   Exit $? ($(date +%H:%M:%S))"
done
echo "== NACHBAR-KANTE v28-b02 gegen v27-b01, Seed 20261044 $(date +%H:%M:%S)"
python -X utf8 -u tools/paired_gating.py \
  --model-a models/alphazero_v28-b02_brierbest.onnx --model-b models/alphazero_v27-b01_brierbest.onnx \
  --name-a v28-b02 --name-b v27-b01 --spec-a "$SPEC" --spec-b "$SPEC" \
  --sims 400 --block-size 5 --max-pairs 200 --seed 20261044 --threads 10 \
  --log-games --no-promote-winner --out "$ART/paired_gating_v28-b02_vs_v27-b01_s44_segment2.json"
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== NEUVERANKERUNG FERTIG $(date +%F' '%H:%M:%S)"
