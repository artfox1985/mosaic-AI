#!/usr/bin/env bash
# v35-Vorbereitung, Kette 3 (PREREG_asymmetric_selfplay.md par.5d3, REGISTRIERT vor Bau und Lauf): W, naechste Form.
# Rust ist angefasst (MOSAIC_DOME_DICE_PLACE_EPS, MOSAIC_DOME_DICE_PRIOR_TEMP), darum zuerst Lib-Suite, --no-run,
# Wheel bauen und installieren, Anker-Drift und -Konservierung (Byte-Gleichheit bei Default); dann
#   1. policy-m2-400g     (Bezug, G gegen G, 400 Partien, Modus 2),
#   2. policy-dice-v2-r1  (W mit eps 0,02 und Prior-Temperatur 2, Wuerfelphase bis Runde 1, 400 Partien),
#   3. policy-dice-v2-r2  (dasselbe bis Runde 2),
# alle mit Seed 20261760 und gleicher Chunkung (gepaart je Partie-Index) nach data/probe_asym, Rezept
# models/v35_probes2.recipe.json; dann je W-Klasse die Auswertung nach der Wuerfelphase gegen policy-m2-400g
# nach evaluations/artifacts/asym_probe_dice_v2_r1.json bzw. _r2.json. Punkt (d) der Leseregel (gepaarte
# Abweichung, state_novelty_probe.py) baut ein anderer Agent und ist nicht in dieser Kette.
# Jeder rote Schritt stoppt.
#
# KEINE PIPE hinter einem Lauf, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
PYDIR="${MOSAIC_PYTHON_DIR:-$(python -c 'import sys,os;print(os.path.dirname(sys.executable))')}"
export PATH="$(cygpath -u "$PYDIR"):$PATH"
STAMP=$(date +%Y%m%d)
RECIPE=models/v35_probes2.recipe.json
step() { echo ""; echo "===== $1 $(date +%F' '%H:%M:%S)"; }
fail() { echo "STOPP: $1"; exit "${2:-10}"; }

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
wait_for_free_cpu "v35-Vorbereitung Kette 3"

# Vorbedingung: die drei Klassen liegen noch nicht.
for C in policy-m2-400g policy-dice-v2-r1 policy-dice-v2-r2; do
  if ls data/probe_asym/selfplay_probe-v35-${C}_*.pkl >/dev/null 2>&1; then fail "${C}-Dateien liegen schon" 4; fi
done

step "cargo test --release --lib"
(cd engine && cargo test --release --lib) || fail "Lib-Suite rot" 11
step "cargo test --release --no-run"
(cd engine && cargo test --release --no-run) || fail "--no-run rot" 12
step "Wheel bauen"
(cd engine && python -m maturin build --release) || fail "maturin rot" 13
WHEEL=$(ls -t engine/target/wheels/mosaic_rust-*.whl | head -1)
python -m pip install --force-reinstall --no-deps "$WHEEL" || fail "pip install rot" 14
sha256sum "$WHEEL"
step "Anker-Drift"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor \
  --out "evaluations/artifacts/anchor_v2_drift_live_wheel_${STAMP}_chain3.json" || fail "Anker-Drift ROT" 15
step "Anker-Konservierung"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor --venv \
  --out "evaluations/artifacts/anchor_v2_conservation_${STAMP}_chain3.json" || fail "Anker-Konservierung ROT" 16

for C in policy-m2-400g policy-dice-v2-r1 policy-dice-v2-r2; do
  step "Klasse $C, 400 Partien"
  MOSAIC_DATA_DIR=data/probe_asym python -X utf8 -u self_play.py --recipe "$RECIPE" --class "$C" \
    || fail "Klasse $C rot" 20
done

for R in 1 2; do
  step "Auswertung par.5d3 policy-dice-v2-r${R} gegen policy-m2-400g (nach der Wuerfelphase)"
  python -X utf8 -u tools/probes/asym_probe_report.py --dice-class "policy-dice-v2-r${R}" --skip-s4 --post-dice-phase \
    --kl-baseline policy-m2-400g \
    --out "evaluations/artifacts/asym_probe_dice_v2_r${R}.json" || fail "Auswertung v2-r${R} rot" 21
done

echo ""
echo "########## v35-Vorbereitung Kette 3 FERTIG $(date +%F' '%H:%M:%S)"
