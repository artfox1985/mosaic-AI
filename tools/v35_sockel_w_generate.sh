#!/usr/bin/env bash
# v35-SOCKEL, W-Klasse (PREREG_v35_window.md par.10; PREREG_asymmetric_selfplay.md par.5d3a/b; Nutzer 2026-10-04
# 13:30: Basis 100, Platzsuche 600): wartet auf eine freie Maschine (der Mischsockel laeuft davor), dann Smoke
# (10 Partien nach data/probe_v35sockel_smoke), dann policy-dice-v2-r1 mit 2.000 Partien nach data/.
#
# KEINE PIPE, keine eigene Umleitung; als DATEI starten (Terminal-Tab).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
RECIPE=models/v35_sockel.recipe.json
C=policy-dice-v2-r1
. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
step() { echo ""; echo "===== $1 $(date +%F' '%H:%M:%S)"; }
fail() { echo "STOPP: $1"; exit "${2:-10}"; }

[ -f "$RECIPE" ] || fail "$RECIPE fehlt" 1
if ls data/ | grep -q "^selfplay_v34-b01-${C}_"; then fail "data/ traegt schon ${C}-Dateien" 4; fi
wait_for_free_cpu "v35-Sockel W" 600 || fail "Warten auf freie Maschine abgebrochen (10 h)" 65
step "Smoke $C, 10 Partien"
MOSAIC_DATA_DIR=data/probe_v35sockel_smoke python -X utf8 -u self_play.py --recipe "$RECIPE" --class "$C" --games 10 \
  || fail "Smoke $C rot" 11
step "Erzeugung $C, 2.000 Partien"
python -X utf8 -u self_play.py --recipe "$RECIPE" --class "$C" || fail "Erzeugung $C rot" 12
echo ""
echo "########## v35-Sockel W ($C) FERTIG $(date +%F' '%H:%M:%S)"
