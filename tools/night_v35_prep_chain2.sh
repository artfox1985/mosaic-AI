#!/usr/bin/env bash
# v35-Vorbereitung, Kette 2 (PREREG_asymmetric_selfplay.md par.7b und par.8b, REGISTRIERT vor dem Lauf):
#   1. policy-m2       (G gegen G, Stichentscheid Modus 2 beide Seiten, 200 Partien @100),
#   2. policy-vs-v32   (G gegen v32-b01 als Zweitnetz, Records beider Seiten, 200 Partien @100),
#   3. policy-s400-m2  (G gegen G @400, Modus 2 beide Seiten, 100 Partien),
# alle nach data/probe_asym (Rezept models/v35_probes2.recipe.json, Seed 20261720); dann drei Auswertungen:
#   evaluations/artifacts/probe_vs_v32_kl.json    KL der G-Seite (net_label primary) gegen policy-m2,
#   evaluations/artifacts/probe_vs_v32_sides.json Seiten (sonderseite = v32-b01, G = v34-b01),
#   evaluations/artifacts/probe_s400_m2_kl.json   KL und Kennzahlen policy-s400-m2 gegen policy-m2,
#                                                 dritte Spalte policy-s400 (par.8a).
# OHNE Build, Wheel und Anker: das installierte Wheel ist das Exploiter-Wheel (Anker gruen, par.7 Chronik).
# Jeder rote Schritt stoppt.
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
wait_for_free_cpu "v35-Vorbereitung Kette 2"

# Vorbedingungen: die drei Klassen liegen noch nicht; Gegner-Netz und Bezug policy-s400 liegen.
for C in policy-m2 policy-vs-v32 policy-s400-m2; do
  if ls data/probe_asym/selfplay_probe-v35-${C}_*.pkl >/dev/null 2>&1; then fail "${C}-Dateien liegen schon" 4; fi
done
[ -f models/alphazero_v32-b01_brierbest.onnx ] || fail "Gegner-Netz models/alphazero_v32-b01_brierbest.onnx fehlt" 3
ls data/probe_asym/selfplay_probe-v35-policy-s400_*.pkl >/dev/null 2>&1 || fail "Bezug policy-s400 fehlt in data/probe_asym" 3

for C in policy-m2 policy-vs-v32 policy-s400-m2; do
  step "Klasse $C"
  MOSAIC_DATA_DIR=data/probe_asym python -X utf8 -u self_play.py --recipe "$RECIPE" --class "$C" \
    || fail "Klasse $C rot" 20
done

step "Auswertung par.7b: KL der G-Seite von policy-vs-v32 gegen policy-m2"
python -X utf8 -u tools/probes/asym_probe_report.py --kl-class policy-vs-v32 --kl-baseline policy-m2 \
  --kl-side-field net_label --kl-side-value primary \
  --out evaluations/artifacts/probe_vs_v32_kl.json || fail "Auswertung KL vs-v32 rot" 21

step "Auswertung par.7b: Seiten von policy-vs-v32 (sonderseite = v32-b01)"
python -X utf8 -u tools/probes/asym_probe_report.py --side-class policy-vs-v32 --side-field opponent_side \
  --side-names "v32-b01 (Zweitnetz),v34-b01 (G)" \
  --out evaluations/artifacts/probe_vs_v32_sides.json || fail "Auswertung Seiten vs-v32 rot" 22

step "Auswertung par.8b: policy-s400-m2 gegen policy-m2, dritte Spalte policy-s400"
python -X utf8 -u tools/probes/asym_probe_report.py --kl-class policy-s400-m2 --kl-baseline policy-m2 \
  --kl-extra-class policy-s400 \
  --out evaluations/artifacts/probe_s400_m2_kl.json || fail "Auswertung s400-m2 rot" 23

echo ""
echo "########## v35-Vorbereitung Kette 2 FERTIG $(date +%F' '%H:%M:%S)"
