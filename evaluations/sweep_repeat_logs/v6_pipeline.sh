#!/bin/bash
# Stufe-2-Bootstrapping-Test: 4000 Self-Play-Spiele mit v2 auf Stufe 2,
# danach v6 trainieren (Warm-Start von v2).
set -e
cd "D:/Archiv/Documents/Projekte/mosaic-AI"

echo "$(date) Starte 4000 Stufe-2-Self-Plays mit v2 (Label v2s2)..."
python self_play.py --mode network --model alphazero_v2.onnx --stage 2 \
  --games 4000 --sims 400 --version v2s2

echo "$(date) Self-Play fertig. Starte Training v6 (Warm-Start v2)..."
python train.py --name v6 --epochs 100 --load v2

echo "$(date) FERTIG."
