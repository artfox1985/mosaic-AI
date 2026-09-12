#!/usr/bin/env bash
# v28-Programm, Messblock nach der Neuverankerung (2026-09-12): erst die Ueberraschungs-Kante
# (Schritt 6), dann C2 der Einhuellenden (Schritt 8b, PREREG_geometric_envelope.md par.12a/12c):
# volle Spalten am argmax-Instrument, Knopf AN (Champion-Spec: K3-P, Huellenform 2, K5) gegen
# AUS (models/k3v_off.spec.json), fuer v28-b01 und v28-b02. Instrument wie tools/argmax_profile.sh:
# 200 Partien @400, Seed 20260931, deterministisch, ohne Wurzelrauschen, MOSAIC_STACK_DRAW_RESEARCH=1,
# corpus_sanity_check je Lauf. Exklusiv, nacheinander.
# Aufruf: bash tools/night_v28_measure.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts

bash tools/night_surprise_edge.sh

export MOSAIC_STACK_DRAW_RESEARCH=1
ON=models/frozen_champions/v27-b01/spec.json
OFF=models/k3v_off.spec.json
for ARM in b01 b02; do
  for MODE in on off; do
    if [ "$MODE" = on ]; then SPEC=$ON; else SPEC=$OFF; fi
    TAG="c2-v28${ARM}-${MODE}"
    echo "== C2 argmax-Instrument $TAG (Spec $SPEC) $(date +%H:%M:%S)"
    python -X utf8 -u self_play.py --mode network --model "models/alphazero_v28-${ARM}_brierbest.onnx" \
      --spec "$SPEC" --games 200 --sims 400 --version "$TAG" --threads 11 --chunk 10 \
      --seed 20260931 --per-file 10 --no-root-noise --deterministic
    echo "   Exit $? ($(date +%H:%M:%S))"
    python -X utf8 tools/corpus_sanity_check.py data --pattern "selfplay_${TAG}_*.pkl" --out "$ART/${TAG//-/_}.json"
    echo "   sanity Exit $? ($(date +%H:%M:%S))"
  done
done
echo "== v28-MESSBLOCK FERTIG $(date +%F' '%H:%M:%S)"
