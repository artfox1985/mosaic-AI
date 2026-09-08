#!/usr/bin/env bash
# Cache-Bloecke fuer die 400 fertigen v25-SOCKEL-Dateien, waehrend die Ausflug-Haelfte
# erzeugt wird. Nutzer-Anweisung 2026-09-07 ("aktivier ihn").
#
# NUR die Sockel-Dateien, per --file-list: der Traegerstatus geht in den Dateischluessel
# ein (build_cache_incremental.py, Kopf Z. 27-32). Ohne Traeger-Manifest nimmt das Werkzeug
# an, JEDE Datei sei Policy-Traeger -- fuer die Sockel-Klasse ist das RICHTIG (sie ist
# policy-tragend, alle 4.000 Partien), fuer die alten und die value-only-Dateien FALSCH.
# Deren Bloecke entstehen spaeter, wenn das v25-Traeger-Manifest steht.
#
# Schluesselparameter aus dem letzten Training (manifest_train_v24-b06_20260906_114705):
# encoder 2d, value_target_variant nortv, kein Konjunktionskopf.
# Workers niedrig, weil daneben die Erzeugung mit 11 Threads laeuft.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
# MOSAIC_IGNORE_POLICY_TARGET_VALID gehoert IN DIESES SKRIPT (2026-09-09): die
# Variable steht als `|ignore_ptv_v1` IM Datei-Schluessel
# (engine/py/file_cache_key.py:115-117, gelesen bei Import in neural_net.py:9).
# Ohne sie landen die Bloecke in einem Namensraum, den das Training nie
# adressiert -- gemessen am 2026-09-09: 2.200 solche Bloecke aus der Nacht vom
# 07./08.09. (840 MiB) und 480 aus einem Waechter-Fehlstart. Die v25-Kette
# exportiert sie vor ihrem Blockbau, dieses Skript tat es nicht.
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
LIST=${1:?Dateiliste fehlt}
echo "== Cache-Bau Sockel $(date +%H:%M:%S), $(wc -l < "$LIST") Dateien"
python -X utf8 -u tools/build_cache_incremental.py \
  --file-list "$LIST" --workers 3 --encoder 2d --value-target-variant nortv
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== CACHE-BAU FERTIG $(date +%H:%M:%S)"
