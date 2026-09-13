#!/usr/bin/env bash
# Direktstart der Kante v28-b02@100 gegen v22-b05@25 (Nutzer 2026-09-13, 01:50, zum degenerierten
# Intervall des Knotens v28-b02@100: "lasst bitte noch 200x spielen gegen v22-b05@25").
#
# Gleicher Befehl wie in tools/night_v28b02s100_vs_v22s25.sh, aber OHNE dessen Warteschleife.
# Grund (belegt 2026-09-13, 04:18): der Prozessfilter jener Schleife (Z.13) enthaelt
# 'self_play.py|paired_gating.py' UNMASKIERT und trifft damit die CommandLine des eigenen
# pwsh-Aufrufs. Der Zaehler wird deshalb nie 0, und die Kante startet nie -- gemessen: dasselbe
# Muster mit maskierter erster Stelle ergibt 0 Kettenprozesse, das Original 4. CLAUDE.md nennt die
# Falle ausdruecklich ("der Filter darf sich nicht selbst treffen", Muster wie '[n]ight_...').
#
# Die Sims-Kette war um 04:08 durch; die Maschine ist frei bis auf den haengenden Waechter, der
# alle 120 s eine Prozessliste abfragt (1 Kern von 12, Messung faehrt 10 Threads).
#
# Aufruf: bash tools/run_v28b02s100_vs_v22s25.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
OUT="$ART/paired_gating_v28-b02_s100_vs_v22-b05_s25_seed58_full.json"

echo "== KANTE v28-b02@100 gegen v22-b05@25 (paired_gating, 100 Paare, Frueh-Stopp AUS, Seed 20261058) $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/paired_gating.py \
  --model-a models/alphazero_v28-b02_brierbest.onnx --spec-a models/frozen_champions/v28-b02/spec.json \
  --model-b models/restored_v22/alphazero_v22-b05.onnx --spec-b models/k3v_off.spec.json \
  --name-a v28-b02_s100 --name-b v22-b05_live_s25 --sims-a 100 --sims-b 25 --c-puct 1.5 \
  --block-size 5 --max-pairs 100 --sprt-alpha 1e-12 --sprt-beta 1e-12 --seed 20261058 --threads 10 \
  --log-games --no-promote-winner --out "$OUT"
echo "   Exit $? ($(date +%H:%M:%S))"

python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
echo "   Spalten Exit $?"

# --out gegenueber dem Original ERGAENZT: ohne den Schalter druckt das Werkzeug nur auf die
# Konsole, und die Plattenpunkte je Kriterium (Standard-Kennzahl 4) fehlen als Artefakt. Genau
# das ist bei den drei Teil-A-Laeufen der Sims-Kurve passiert.
python -X utf8 -u tools/plate_points_from_arena.py "$OUT" \
  --out "$ART/plate_points_v28b02s100_vs_v22b05s25_seed58.json"
echo "   Platten Exit $? ($(date +%H:%M:%S))"
echo "== KANTE FERTIG $(date +%F' '%H:%M:%S). Register-Zeile durch den Koordinator."
