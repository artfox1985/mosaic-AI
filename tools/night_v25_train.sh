#!/usr/bin/env bash
# Training v25-b01. Fenster, Traeger-Manifest, Bloecke und Monolith sind fertig
# (tools/night_v25_chain.sh, Schritte 1-5, 2026-09-08 03:33-04:44).
#
# Die Optionen --val-pool, --ignore-policy-target-valid, --head-warmstart und
# --bootstrap-coherence sind KEINE CLI-Flags von train.py -- sie kommen aus der Umgebung
# bzw. aus Defaults; das Trainings-Manifest protokolliert sie nur. Der erste Anlauf ist
# genau daran gescheitert (Exit 2, "unrecognized arguments"), weil ich die
# Manifest-Felder fuer Flags gehalten habe.
# Early-Stop, Epoch-Checkpoint, Snapshot und Head-Warmstart sind per DEFAULT an; es gibt
# nur die Abschalter --no-early-stop, --no-epoch-checkpoint, --no-snapshot,
# --no-head-warmstart. Also nicht setzen.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v25.json
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v24-b07-'
echo "== Training v25-b01 $(date +%H:%M:%S)"
echo "   Umgebung: CARRIER_MANIFEST=$MOSAIC_CARRIER_MANIFEST VAL_POOL=$MOSAIC_VAL_POOL"
python -X utf8 -u train.py --name v25-b01 --load v24-b06_brierbest \
  --file-list data/window_v25.txt --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac 0.05 --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 1.0 \
  --endgame-head --opp-points-head --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed 20260925
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== TRAINING FERTIG $(date +%H:%M:%S)"
