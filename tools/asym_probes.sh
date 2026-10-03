#!/usr/bin/env bash
# Sonden S1-S4 des asymmetrischen Self-Plays (evaluations/PREREG_asymmetric_selfplay.md par.5), Laeufe.
# Je Klasse aus models/v35_probes.recipe.json 100 Partien nach data/probe_asym, nacheinander, exklusiv
# (S1 liest die Wanduhr je Partie aus dem Manifest). Die Auswertung (S1-S4) laeuft danach getrennt.
# Ein roter Waechter oder Exit != 0 stoppt die Kette.
#
# KEINE PIPE, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
RECIPE=models/v35_probes.recipe.json
[ -f "$RECIPE" ] || { echo "ABBRUCH: $RECIPE fehlt"; exit 1; }
if ls data/probe_asym 2>/dev/null | grep -q "^selfplay_"; then echo "ABBRUCH: data/probe_asym ist nicht leer"; exit 4; fi
mkdir -p data/probe_asym
. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
wait_for_free_cpu "Asym-Sonden"
for CLASS in policy policy-dice policy-aggr-l0 policy-aggr-l05 policy-aggr-l1 policy-aggr-l2; do
  echo ""
  echo "===== Klasse $CLASS, 100 Partien $(date +%F' '%H:%M:%S)"
  MOSAIC_DATA_DIR=data/probe_asym python -X utf8 -u self_play.py --recipe "$RECIPE" --class "$CLASS"
  RC=$?
  echo "   $CLASS Exit $RC ($(date +%H:%M:%S)), Dateien: $(ls data/probe_asym | grep -c "^selfplay_probe-v35-${CLASS}_")"
  [ $RC -eq 0 ] || { echo "STOPP: Klasse $CLASS mit Exit $RC"; exit 10; }
done
echo ""
echo "########## Asym-Sonden Laeufe FERTIG $(date +%F' '%H:%M:%S)"
