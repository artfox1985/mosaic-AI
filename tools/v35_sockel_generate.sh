#!/usr/bin/env bash
# v35-SOCKEL, Mischsockel (PREREG_v35_window.md par.10; PREREG_asymmetric_selfplay.md par.8c1; Nutzer 2026-10-04
# 13:20: "den mischsockel kannst schon starten"): Smoke je Klasse (10 Partien nach data/probe_v35sockel_smoke),
# dann policy (1.000 @400, Modus 2) und policy-s100 (1.000 @100, Modus 2) aus models/v35_sockel.recipe.json nach
# data/. Die W-Klasse policy-dice-v2-r1 und der Exploiter folgen gesondert (Sims-Entscheid bzw. Tor par.7c).
#
# KEINE PIPE, keine eigene Umleitung; als DATEI starten (im Terminal-Tab, 2-h-Grenze der Hintergrundaufgaben).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
RECIPE=models/v35_sockel.recipe.json
. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
step() { echo ""; echo "===== $1 $(date +%F' '%H:%M:%S)"; }
fail() { echo "STOPP: $1"; exit "${2:-10}"; }

for f in "$RECIPE" models/v35_generation.spec.json models/alphazero_v34-b01_brierbest.onnx; do
  [ -f "$f" ] || fail "$f fehlt" 1
done
for c in policy policy-s100; do
  if ls data/ | grep -q "^selfplay_v34-b01-${c}_"; then fail "data/ traegt schon ${c}-Dateien" 4; fi
done
wait_for_free_cpu "v35-Sockel"

for c in policy policy-s100; do
  step "Smoke $c, 10 Partien"
  MOSAIC_DATA_DIR=data/probe_v35sockel_smoke python -X utf8 -u self_play.py --recipe "$RECIPE" --class "$c" --games 10 \
    || fail "Smoke $c rot" 11
done
for c in policy policy-s100; do
  step "Erzeugung $c"
  python -X utf8 -u self_play.py --recipe "$RECIPE" --class "$c" || fail "Erzeugung $c rot" 12
done
echo ""
echo "########## v35-Sockel (policy, policy-s100) FERTIG $(date +%F' '%H:%M:%S)"
