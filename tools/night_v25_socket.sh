#!/usr/bin/env bash
# v25, Klasse 1: die 4.000 TRAEGER-Partien (policy-aktiv).
# Befehl woertlich aus PREREG_v25_window.md par.19 Nr. 1.
# Nutzer-Freigabe 2026-09-07: "am Ende der Durchfuehrung des self play skills kannst die
# 4000 sockel Partien selbstaendig starten."
#
# Rezept: Umschaltpunkt 1 (durchgehend greedy) plus Weg C (eine Abweichung je Partie, Stelle
# aus der gemessenen Verteilung). Wurzelrauschen AN (Default). Generator v24-b07.
# Erwartete Dauer rund 4,2 h (hergeleitet aus 3,77 s je Partie, nicht auf dieser Groesse
# gemessen). Die echte Dauer schreibt der Lauf selbst ins Manifest.
#
# WICHTIG fuer die spaetere Trainingsstufe: die hier entstehenden Dateien heissen
# selfplay_v24-b07-policy_* -- der Val-Pool-Regex aus par.6 wandert entsprechend von
# ^selfplay_v24-b06- auf ^selfplay_v24-b07-, und MOSAIC_DATA_EXCLUDE ist beim Training
# zu pinnen (feedback_window_pinning_during_generation).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
echo "== v25 Sockel: 4.000 Traeger-Partien $(date +%H:%M:%S)"
python -X utf8 -u self_play.py --mode network \
  --model models/alphazero_v24-b07_brierbest.onnx \
  --spec models/v24-b07_brierbest.spec.json \
  --games 4000 --sims 100 --version v24-b07-policy \
  --threads 11 --chunk 10 --per-file 10 --seed 20260907 \
  --tau-argmax-from-move 1 --deviate-prob 1.0
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== SOCKEL FERTIG $(date +%H:%M:%S)"
