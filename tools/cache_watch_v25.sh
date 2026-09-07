#!/usr/bin/env bash
# Cache-Waechter fuer die v25-Erzeugung: baut den Block JE DATEI, waehrend das Self-Play
# laeuft (PREREG_cache_build_time.md par.6, Hebel 4). Nutzer-Anweisung 2026-09-07.
#
# WARUM: nach dem Korpus kostet der Cache 36 min parallel bzw. 2,58 h seriell auf dem
# kritischen Pfad. Mitlaufend ist er fertig, wenn der Korpus fertig ist.
#
# SCHLUESSELPARAMETER, nicht beliebig: sie gehen in den Dateischluessel ein
# (neural_net.per_file_cache_key). Uebernommen aus dem letzten Training
# models/manifest_train_v24-b06_20260906_114705.json: encoder 2d,
# value_target_variant nortv, conjunction_head False. Ein Block mit anderem
# Schluessel waere fuer das v25-Training wertlos.
#
# WORKERS BEWUSST NIEDRIG: das Self-Play faehrt 11 Threads. Der Default des Werkzeugs
# waere alle Kerne minus zwei und wuerde der Erzeugung die Maschine wegnehmen.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
echo "== Cache-Waechter Start $(date +%H:%M:%S)"
python -X utf8 -u tools/build_cache_incremental.py \
  --watch --workers 3 --wartezeit 60 --leerlauf-abbruch 10 \
  --encoder 2d --value-target-variant nortv
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== Cache-Waechter Ende $(date +%H:%M:%S)"
