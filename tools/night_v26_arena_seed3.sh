#!/usr/bin/env bash
# Tor 1, dritter Seed: der Stichentscheid zwischen 20261030 (210:190, kein SPRT-Entscheid)
# und 20261031 (85:55, SPRT nach 70 Paaren). Vorregistriert in PREREG_v26_window.md par.8,
# BEVOR die Zahl da war. Nutzer-Freigabe 2026-09-09, 15:45: "fahr ihn."
#
# BIS ZUM DECKEL, OHNE FRUEHSTOPP -- und warum ueber alpha/beta statt ueber einen Schalter:
# paired_gating.py hat keinen "--no-early-stop". Die Wald-Schranken sind
# +-ln((1-beta)/alpha); mit 1e-12 liegen sie bei rund +-27,6, und die brauchte eine Serie
# von ueber hundert Siegen am Stueck. Der Lauf geht damit sicher ueber die vollen 200 Paare.
# Das aendert NUR die Stoppregel, keine Partie und keinen Zug; alpha und beta stehen im
# Artefakt, der Eingriff ist also im Ergebnis sichtbar und nicht versteckt.
#
# Entschieden wird danach am Vorzeichentest/McNemar ueber die vollen 200 Paare, nicht am
# SPRT -- genau das ist der Sinn eines verzerrungsfreien dritten Laufs: der erste Seed
# lief bis zum Deckel, der zweite stoppte, WEIL er vorne lag.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
SPEC=models/v24-b07_brierbest.spec.json

echo "== Tor 1, Seed 20261032, bis zum Deckel $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/paired_gating.py \
  --model-a models/alphazero_v26-b01_brierbest.onnx \
  --model-b models/alphazero_v25-b01_brierbest.onnx \
  --name-a v26-b01 --name-b v25-b01 \
  --spec-a "$SPEC" --spec-b "$SPEC" \
  --sims 400 --block-size 5 --max-pairs 200 --seed 20261032 --threads 10 \
  --sprt-alpha 1e-12 --sprt-beta 1e-12 \
  --no-promote-winner \
  --out "$ART/paired_gating_v26-b01_vs_v25-b01_s32.json"
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== SEED 3 FERTIG $(date +%F' '%H:%M:%S)"
echo "   Auswertung: Vorzeichentest/McNemar ueber alle 200 Paare, Bloecke sind die Einheit."
