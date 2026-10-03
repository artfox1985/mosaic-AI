#!/usr/bin/env bash
# W mit neuer Quellenregel (PREREG_asymmetric_selfplay.md par.5b): Lib-Suite, --no-run, Wheel bauen und
# installieren, Anker-Drift und -Konservierung, dann die Sonde policy-dice-src4 (100 Partien) und ihre
# Auswertung. Jeder rote Schritt stoppt die Kette.
#
# KEINE PIPE, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
PYDIR="${MOSAIC_PYTHON_DIR:-$(python -c 'import sys,os;print(os.path.dirname(sys.executable))')}"
export PATH="$(cygpath -u "$PYDIR"):$PATH"
STAMP=$(date +%Y%m%d)
step() { echo ""; echo "===== $1 $(date +%F' '%H:%M:%S)"; }
fail() { echo "STOPP: $1"; exit "${2:-10}"; }

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
wait_for_free_cpu "W-src4-Kette"

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
  --out "evaluations/artifacts/anchor_v2_drift_live_wheel_${STAMP}_src4.json" || fail "Anker-Drift ROT" 15
step "Anker-Konservierung"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor --venv \
  --out "evaluations/artifacts/anchor_v2_conservation_${STAMP}_src4.json" || fail "Anker-Konservierung ROT" 16

step "Sonde policy-dice-src4, 100 Partien"
if ls data/probe_asym 2>/dev/null | grep -q "^selfplay_probe-v35-policy-dice-src4_"; then fail "src4-Dateien liegen schon" 4; fi
MOSAIC_DATA_DIR=data/probe_asym python -X utf8 -u self_play.py --recipe models/v35_probes.recipe.json --class policy-dice-src4 \
  || fail "Sonde rot" 17
step "Auswertung"
python -X utf8 -u tools/probes/asym_probe_report.py --dice-class policy-dice-src4 --skip-s4 \
  --out evaluations/artifacts/asym_probe_w_src4.json || fail "Auswertung rot" 18
echo ""
echo "########## W-src4-Kette FERTIG $(date +%F' '%H:%M:%S)"
