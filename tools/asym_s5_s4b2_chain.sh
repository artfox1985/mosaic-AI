#!/usr/bin/env bash
# Eroeffnungs-Wuerfel (PREREG_asymmetric_selfplay.md par.5d, Sonde S5) und Stoerer B repariert (par.5c2,
# S4b neu): Lib-Suite, --no-run, Wheel bauen und installieren, Anker-Drift und -Konservierung; dann
# policy-dice-r1, policy-dice-r2, policy-aggrb-e01/e02/e04 (je 100 Partien) nach data/probe_asym und die
# drei Auswertungen. Jeder rote Schritt stoppt.
#
# KEINE PIPE, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
PYDIR="${MOSAIC_PYTHON_DIR:-$(python -c 'import sys,os;print(os.path.dirname(sys.executable))')}"
export PATH="$(cygpath -u "$PYDIR"):$PATH"
STAMP=$(date +%Y%m%d)
RECIPE=models/v35_probes.recipe.json
step() { echo ""; echo "===== $1 $(date +%F' '%H:%M:%S)"; }
fail() { echo "STOPP: $1"; exit "${2:-10}"; }

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
wait_for_free_cpu "S5-S4b2-Kette"

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
  --out "evaluations/artifacts/anchor_v2_drift_live_wheel_${STAMP}_s5.json" || fail "Anker-Drift ROT" 15
step "Anker-Konservierung"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor --venv \
  --out "evaluations/artifacts/anchor_v2_conservation_${STAMP}_s5.json" || fail "Anker-Konservierung ROT" 16

run_class() {  # $1 Klasse
  step "Klasse $1, 100 Partien"
  if ls data/probe_asym 2>/dev/null | grep -q "^selfplay_probe-v35-$1_"; then fail "$1-Dateien liegen schon" 4; fi
  MOSAIC_DATA_DIR=data/probe_asym python -X utf8 -u self_play.py --recipe "$RECIPE" --class "$1" || fail "Klasse $1 rot" 17
}
for C in policy-dice-r1 policy-dice-r2 policy-aggrb-e01 policy-aggrb-e02 policy-aggrb-e04; do run_class "$C"; done

for R in 1 2; do
  step "Auswertung S5 R1-${R}"
  python -X utf8 -u tools/probes/asym_probe_report.py --dice-class "policy-dice-r${R}" --skip-s4 --post-dice-phase \
    --out "evaluations/artifacts/asym_probe_s5_r${R}.json" || fail "Auswertung S5 r${R} rot" 18
done
step "Auswertung S4b neu"
python -X utf8 -u tools/probes/asym_probe_report.py --skip-s2 --skip-s4 \
  --aggr-classes policy-aggrb-e01:0.01,policy-aggrb-e02:0.02,policy-aggrb-e04:0.04 \
  --out evaluations/artifacts/asym_probe_s4b2.json || fail "Auswertung S4b neu rot" 19
echo ""
echo "########## S5-S4b2-Kette FERTIG $(date +%F' '%H:%M:%S)"
