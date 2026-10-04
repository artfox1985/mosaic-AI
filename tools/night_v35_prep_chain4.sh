#!/usr/bin/env bash
# v35-Vorbereitung, Kette 4 (PREREG_asymmetric_selfplay.md par.8c, REGISTRIERT vor dem Lauf): Nachmessung Punkte und
# Spalten @400. Klasse policy-s400-m2-b (300 Partien @400, Modus 2, Seed 20261730) nach data/probe_asym, dann die
# gepoolte Auswertung @400 (policy-s400-m2 + policy-s400-m2-b) gegen @100 (policy-m2 + policy-m2-400g) nach
# evaluations/artifacts/probe_s400_points_check.json (Kennzahlen und Lesart aus tools/probes/sims_points_check.py,
# Median-KL ueber tools/probes/asym_probe_report.py).
# OHNE Build, Wheel und Anker: das installierte Wheel ist das aktuelle. Jeder rote Schritt stoppt.
#
# KEINE PIPE hinter einem Lauf, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
PYDIR="${MOSAIC_PYTHON_DIR:-$(python -c 'import sys,os;print(os.path.dirname(sys.executable))')}"
export PATH="$(cygpath -u "$PYDIR"):$PATH"
RECIPE=models/v35_probes2.recipe.json
step() { echo ""; echo "===== $1 $(date +%F' '%H:%M:%S)"; }
fail() { echo "STOPP: $1"; exit "${2:-10}"; }

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
wait_for_free_cpu "v35-Vorbereitung Kette 4"

# Vorbedingungen: die neue Klasse liegt noch nicht, die vier Bezugsklassen liegen.
if ls data/probe_asym/selfplay_probe-v35-policy-s400-m2-b_*.pkl >/dev/null 2>&1; then
  fail "policy-s400-m2-b-Dateien liegen schon" 4
fi
for C in policy-s400-m2 policy-m2 policy-m2-400g; do
  ls data/probe_asym/selfplay_probe-v35-${C}_*.pkl >/dev/null 2>&1 || fail "Bezugsklasse ${C} fehlt in data/probe_asym" 3
done

step "Klasse policy-s400-m2-b, 300 Partien @400"
MOSAIC_DATA_DIR=data/probe_asym python -X utf8 -u self_play.py --recipe "$RECIPE" --class policy-s400-m2-b \
  || fail "Klasse policy-s400-m2-b rot" 20

step "Auswertung par.8c: @400 gegen @100, gepoolt"
python -X utf8 -u tools/probes/asym_probe_report.py \
  --group-a policy-s400-m2,policy-s400-m2-b --group-b policy-m2,policy-m2-400g \
  --out evaluations/artifacts/probe_s400_points_check.json || fail "Auswertung par.8c rot" 21

echo ""
echo "########## v35-Vorbereitung Kette 4 FERTIG $(date +%F' '%H:%M:%S)"
