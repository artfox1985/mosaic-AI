#!/usr/bin/env bash
# Rauchprobe des Knopfs MOSAIC_ACTION_TEMP (PREREG_v25_window.md par.14/14d): BELEGT, dass
# der Knopf die Engine erreicht -- eine Statuszeile belegt das nicht (par.14e: der Knopf war
# monatelang verdrahtet, gedruckt und wirkungslos).
#
# Aufbau: dieselben 10 Partien, derselbe Seed, dreimal -- Modus 0 (aus), 1 (Staffel),
# 2 (glatt). Erwartung: 0 und 1 unterscheiden sich, 0 und 2 unterscheiden sich, 1 und 2
# unterscheiden sich. Waere ein Knopf wirkungslos, waeren die Korpora identisch.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
NET="models/alphazero_v24-b06_brierbest.onnx"; SPEC="models/v24-b06_brierbest.spec.json"
for m in 0 1 2; do
  echo "== Modus $m $(date +%H:%M:%S)"
  python -X utf8 -u self_play.py --mode network --model "$NET" --spec "$SPEC" \
    --games 10 --sims 100 --version "smoke-at$m" --threads 11 --chunk 10 --per-file 10 \
    --seed 20260953 --action-temp "$m"
  echo "   Exit $? ($(date +%H:%M:%S))"
done
echo "== Vergleich $(date +%H:%M:%S)"
python -X utf8 -u tools/smoke_action_temp_compare.py
echo "== RAUCHPROBE FERTIG $(date +%H:%M:%S)"
