#!/usr/bin/env bash
# Tor 1 fuer v26-b01: gepaartes Gating gegen den amtierenden Champion v25-b01.
# Nutzer-Auftrag 2026-09-09, 13:40: "fahre fort mit den genannten punkten."
#
# BEIDE Seiten fahren die Champion-Spec: sie ist nach PREREG_v25_window.md par.18 bis
# v27 geschlossen, verglichen wird ausschliesslich das NETZ. Genau dafuer ist die
# Generation gemacht -- v26 aendert nur das Material.
#
# ZWEI SEEDS, nacheinander: die Fruehstopp-Regel (docs/promotion_checklist.md) laesst
# einen SPRT-Entscheid unter 150 Paaren erst nach einer Replikation mit UNABHAENGIGEM
# Seed gelten. v25 nahm 20261020/20261021, v26 nimmt 20261030/20261031.
#
# Blockgroesse 5 ist gesetzt, nicht dem Default ueberlassen ([[feedback_block_size_5_all_arena_tools]]).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
SPEC=models/v24-b07_brierbest.spec.json
A=models/alphazero_v26-b01_brierbest.onnx
B=models/alphazero_v25-b01_brierbest.onnx

for SEED in 20261030 20261031; do
  KURZ=${SEED: -2}
  echo "== Tor 1: v26-b01 gegen v25-b01, Seed $SEED $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$A" --model-b "$B" \
    --name-a v26-b01 --name-b v25-b01 \
    --spec-a "$SPEC" --spec-b "$SPEC" \
    --sims 400 --block-size 5 --max-pairs 200 --seed "$SEED" --threads 10 \
    --no-promote-winner \
    --out "$ART/paired_gating_v26-b01_vs_v25-b01_s${KURZ}.json"
  echo "   Exit $? ($(date +%H:%M:%S))"
done

echo "== TOR 1 FERTIG $(date +%F' '%H:%M:%S)"
echo "   Artefakte: $ART/paired_gating_v26-b01_vs_v25-b01_s30.json, ..._s31.json"
echo "   Auswertung auf BLOCK-Ebene (der Seed faellt je Block), Verdikt nach"
echo "   PREREG_v26_window.md; Elo-Kanten erst bei Promotion."
