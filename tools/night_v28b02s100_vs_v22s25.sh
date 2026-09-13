#!/usr/bin/env bash
# Nutzer 2026-09-13, 01:50 (zu v28-b02@100, 30 Partien, Intervall degeneriert): "lasst bitte noch 200x
# spielen gegen v22-b05@25". Zweite Aufhaengung des Knotens v28-b02@100 in der Leiter: gepaart gegen
# v22-b05@25 (k3v_off-Spec), 100 Paare = 200 Partien bis zum Deckel OHNE Frueh-Stopp, Bloecke zu 5, Logs.
# WARTET auf das Ende von tools/night_sims_curve_v28b02.sh (Messungen laufen exklusiv), dann Start.
# Aufruf: bash tools/night_v28b02s100_vs_v22s25.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
echo "== WARTE auf Sims-Kette (depth_curve_600_v28b02.json und kein Kettenprozess) $(date +%F' '%H:%M:%S)"
while true; do
  if [ -f "$ART/depth_curve_600_v28b02.json" ]; then
    n=$(pwsh -NoProfile -NonInteractive -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '[n]ight_sims_curve_v28b02|self_play.py|paired_gating.py' } | Measure-Object).Count" 2>/dev/null | tr -d '\r')
    [ "$n" = "0" ] && break
  fi
  sleep 120
done
echo "== KANTE v28-b02@100 gegen v22-b05@25 (paired_gating, 100 Paare, Frueh-Stopp AUS, Seed 20261058) $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/paired_gating.py \
  --model-a models/alphazero_v28-b02_brierbest.onnx --spec-a models/frozen_champions/v28-b02/spec.json \
  --model-b models/restored_v22/alphazero_v22-b05.onnx --spec-b models/k3v_off.spec.json \
  --name-a v28-b02_s100 --name-b v22-b05_live_s25 --sims-a 100 --sims-b 25 --c-puct 1.5 \
  --block-size 5 --max-pairs 100 --sprt-alpha 1e-12 --sprt-beta 1e-12 --seed 20261058 --threads 10 \
  --log-games --no-promote-winner --out "$ART/paired_gating_v28-b02_s100_vs_v22-b05_s25_seed58_full.json"
echo "   Exit $? ($(date +%H:%M:%S))"
python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$ART/paired_gating_v28-b02_s100_vs_v22-b05_s25_seed58_full.json"
echo "   Spalten Exit $?"
python -X utf8 -u tools/plate_points_from_arena.py "$ART/paired_gating_v28-b02_s100_vs_v22-b05_s25_seed58_full.json"
echo "   Platten Exit $? ($(date +%H:%M:%S))"
echo "== KANTE FERTIG $(date +%F' '%H:%M:%S). Register-Zeile durch den Koordinator."
