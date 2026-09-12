#!/usr/bin/env bash
# Ueberraschungs-Kante (PREREG_policy_surprise_weighting.md par.11, v28-Programm Schritt 6):
# v24-b05 (surprise_alpha 0,5) gegen v24-b04 (ohne), gleiches Rezept sonst, beide Modelle aus
# den restic-Snapshots run:v24-b05 (73b5c104) und run:v24-b04 (c6877ec9) nach
# models/restored_v24/ zurueckgeholt (2026-09-12). Beide Seiten models/k3v_off.spec.json
# (Fassung ohne Knopf wie bei den v24-Abnahmen), 200 Paare, Blockgroesse 5, Logs.
# 744er-Modelle unter dem 755er-Wheel (Kuerzung auf Modellbreite, net.rs:421); die neuen
# optionalen Spec-Felder fehlen in k3v_off.spec.json und stehen damit auf 0.
# Aufruf: bash tools/night_surprise_edge.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
SPEC=models/k3v_off.spec.json
A=models/restored_v24/alphazero_v24-b05_brierbest.onnx
B=models/restored_v24/alphazero_v24-b04_brierbest.onnx
[ -f "$A" ] && [ -f "$B" ] || { echo "STOPP: Modelle fehlen"; exit 12; }
echo "== UEBERRASCHUNGS-KANTE v24-b05 gegen v24-b04, Seed 20261045 $(date +%H:%M:%S)"
python -X utf8 -u tools/paired_gating.py \
  --model-a "$A" --model-b "$B" --name-a v24-b05 --name-b v24-b04 \
  --spec-a "$SPEC" --spec-b "$SPEC" \
  --sims 400 --block-size 5 --max-pairs 200 --seed 20261045 --threads 10 \
  --log-games --no-promote-winner --out "$ART/paired_gating_v24-b05_vs_v24-b04_s45.json"
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== UEBERRASCHUNGS-KANTE FERTIG $(date +%F' '%H:%M:%S)"
