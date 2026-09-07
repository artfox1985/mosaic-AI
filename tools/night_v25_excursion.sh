#!/usr/bin/env bash
# v25, Klasse 3: die Ausflug-Haelfte des Schwarms (Weg B).
# Befehl woertlich aus PREREG_v25_window.md par.19 Nr. 3.
#
# --games 2000, NICHT 4000: ein Ausflug kommt ZUSAETZLICH zur Hauptpartie, mit eigener
# game_id (Suffix _x1). 2.000 Hauptpartien plus 2.000 Ausfluege sind die 4.000 Identitaeten
# dieser Haelfte.
#
# --tau-argmax-from-move 1 ist eine markierte ABLEITUNG (par.19): ohne den Schalter wuerde
# die Hauptpartie weiter proportional zu den Besuchen sampeln, und das Wertziel waere
# wieder verzerrt -- genau der Defekt, den Weg B beheben soll.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
echo "== v25 Ausflug-Haelfte $(date +%H:%M:%S)"
python -X utf8 -u self_play.py --mode network \
  --model models/alphazero_v24-b07_brierbest.onnx \
  --spec models/v24-b07_brierbest.spec.json \
  --games 2000 --sims 100 --value-only --version v24-b07-value-excursion \
  --threads 11 --chunk 10 --per-file 10 --seed 20260909 \
  --excursion-prob 1.0 --tau-argmax-from-move 1 --no-root-noise
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== AUSFLUG-HAELFTE FERTIG $(date +%H:%M:%S)"
