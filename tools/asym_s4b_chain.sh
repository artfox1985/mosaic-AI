#!/usr/bin/env bash
# Stoerer B (PREREG_asymmetric_selfplay.md par.5c) und Wiederholung der W-Laufzeit (par.5b1): Lib-Suite,
# --no-run, Wheel bauen und installieren, Anker-Drift und -Konservierung; dann `policy` und
# `policy-dice-src4` erneut nach data/probe_asym_rep (saubere Wanduhr), dann die S4b-Klassen
# policy-aggr-e01/e02/e04 nach data/probe_asym, dann beide Auswertungen. Jeder rote Schritt stoppt.
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
wait_for_free_cpu "S4b-Kette"

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
  --out "evaluations/artifacts/anchor_v2_drift_live_wheel_${STAMP}_s4b.json" || fail "Anker-Drift ROT" 15
step "Anker-Konservierung"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor --venv \
  --out "evaluations/artifacts/anchor_v2_conservation_${STAMP}_s4b.json" || fail "Anker-Konservierung ROT" 16

run_class() {  # $1 Klasse, $2 Datenordner
  step "Klasse $1 nach $2, 100 Partien"
  if ls "$2" 2>/dev/null | grep -q "^selfplay_probe-v35-$1_"; then fail "$1-Dateien liegen schon in $2" 4; fi
  mkdir -p "$2"
  MOSAIC_DATA_DIR="$2" python -X utf8 -u self_play.py --recipe "$RECIPE" --class "$1" || fail "Klasse $1 rot" 17
}
run_class policy data/probe_asym_rep
run_class policy-dice-src4 data/probe_asym_rep
for C in policy-aggr-e01 policy-aggr-e02 policy-aggr-e04; do run_class "$C" data/probe_asym; done

step "Auswertung W-Wiederholung"
python -X utf8 -u tools/probes/asym_probe_report.py --data-dir data/probe_asym_rep --dice-class policy-dice-src4 \
  --skip-s4 --out evaluations/artifacts/asym_probe_w_src4_rep.json || fail "Auswertung W rot" 18
step "Auswertung S4b"
python -X utf8 -u tools/probes/asym_probe_report.py --skip-s2 --skip-s4 \
  --aggr-classes policy-aggr-e01:0.01,policy-aggr-e02:0.02,policy-aggr-e04:0.04 \
  --out evaluations/artifacts/asym_probe_s4b.json || fail "Auswertung S4b rot" 19
echo ""
echo "########## S4b-Kette FERTIG $(date +%F' '%H:%M:%S)"
