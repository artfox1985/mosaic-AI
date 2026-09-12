#!/usr/bin/env bash
# Nach der Master-Kette (tools/night_v28_after_reanchor.sh), exklusiv:
#   1  Dritter Seed der Nachbar-Kante v28-b02 gegen v27-b01 als UNVERZERRTER Stichentscheid
#      (v26-Praezedenz 2026-09-09: Seed 20261044 SPRT-Stopp 133:97, Seed 20261046 Deckel 212:188
#      ohne Entscheid; Pool aus Stopp und Deckel waere verzerrt). 200 Paare, Fruehstopp aus
#      (SPRT-Schranken 1e-12), Blockgroesse 5, Logs. PREREG_code_cleanup_closeout.md par.7a.
#   2  Startkuppel Stufe 0, volle Messung (PREREG_start_dome_choice.md par.4/par.8): 60 Partien
#      je Slot, Paarungen 25 und 400 Sims, Slot-Kontrolle aktiv.
# Aufruf: bash tools/night_v28_third_seed.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
SPEC=models/frozen_champions/v27-b01/spec.json
echo "== DRITTER SEED v28-b02 gegen v27-b01, Seed 20261047, Fruehstopp aus $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/paired_gating.py \
  --model-a models/alphazero_v28-b02_brierbest.onnx --model-b models/alphazero_v27-b01_brierbest.onnx \
  --name-a v28-b02 --name-b v27-b01 --spec-a "$SPEC" --spec-b "$SPEC" \
  --sims 400 --block-size 5 --max-pairs 200 --seed 20261047 --threads 10 \
  --sprt-alpha 1e-12 --sprt-beta 1e-12 \
  --log-games --no-promote-winner --out "$ART/paired_gating_v28-b02_vs_v27-b01_s47_segment2.json"
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== STARTKUPPEL STUFE 0, volle Messung $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/probes/start_dome_slot_probe.py --out "$ART/start_dome_slot_probe.json"
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== DRITTER SEED + STUFE 0 FERTIG $(date +%F' '%H:%M:%S)"
