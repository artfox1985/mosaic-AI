#!/usr/bin/env bash
# Bau-Fenster fuer Weg B (PREREG_start_position_seeding.md par.9f) UND die glatte
# Temperatur-Form 2 (PREREG_v25_window.md par.14d). Ein gemeinsamer Build, weil beide
# dieselben Dateien beruehren. Aus tools/hull_form_build_window.sh abgeleitet.
# Aufruf (Projektordner, Hintergrund, ohne Pipe, NUR bei freier CPU):
#     bash tools/wegb_temp2_build_window.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

echo "== 0) Python-DLL in den PATH (sonst STATUS_DLL_NOT_FOUND) $(date +%H:%M:%S)"
. tools/hooks/python_dll_path.sh 2>/dev/null && mosaic_prepend_python_dll_path 2>/dev/null || {
  PYDIR="${MOSAIC_PYTHON_DIR:-}"; [ -z "$PYDIR" ] && PYDIR="$(python -c 'import sys; print(sys.base_prefix)' 2>/dev/null)"
  command -v cygpath >/dev/null 2>&1 && PYDIR="$(cygpath -u "$PYDIR" 2>/dev/null || printf '%s' "$PYDIR")"
  ls "$PYDIR"/python3*.dll >/dev/null 2>&1 && export PATH="$PYDIR:$PATH"; }

echo "== 1) cargo test --release --lib $(date +%H:%M:%S)"
( cd engine && cargo test --release --lib ); rc=$?
echo "   cargo test Exit $rc ($(date +%H:%M:%S))"
[ "$rc" = "0" ] || { echo "STOPP: cargo test rot -- kein Wheel, kein Anker. Koordinator entscheidet."; exit 41; }

# Der pre-push-Hook kompiliert AUCH examples/ und benches/. Wer das erst beim Push merkt,
# hat den Fehler eine Stunde spaeter (CLAUDE.md "Push scheitert am pre-push-Hook").
echo "== 2) cargo test --release --no-run (examples und benches mitkompilieren) $(date +%H:%M:%S)"
( cd engine && cargo test --release --no-run ); rc=$?
echo "   Exit $rc ($(date +%H:%M:%S))"
[ "$rc" = "0" ] || { echo "STOPP: examples/benches brechen -- Aufrufer nachziehen."; exit 42; }

echo "== 3) Wheel bauen $(date +%H:%M:%S)"
( cd engine && python -m maturin build --release ); rc=$?
echo "   maturin Exit $rc ($(date +%H:%M:%S))"
[ "$rc" = "0" ] || { echo "STOPP: maturin rot."; exit 43; }

WHEEL=$(ls -t engine/target/wheels/*.whl 2>/dev/null | head -1)
echo "== 4) Wheel installieren: $WHEEL $(date +%H:%M:%S)"
python -m pip install --force-reinstall --no-deps "$WHEEL"; rc=$?
echo "   pip Exit $rc ($(date +%H:%M:%S))"
[ "$rc" = "0" ] || { echo "STOPP: Install rot (laeuft ein server.py?)."; exit 44; }

echo "== 5) Anker-DRIFT (aktuelles Wheel gegen das Artefakt) $(date +%H:%M:%S)"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv1_anchor \
  --out evaluations/artifacts/anchor_drift_20260907_wegb_temp2.json
echo "   Drift Exit $? ($(date +%H:%M:%S))"

echo "== 6) Anker-KONSERVIERUNG (Wheel des Artefakts) $(date +%H:%M:%S)"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv1_anchor --venv \
  --out evaluations/artifacts/anchor_conservation_20260907_wegb_temp2.json
echo "   Konservierung Exit $? ($(date +%H:%M:%S))"

echo "== 7) Rauchprobe glatte Temperatur (20 Partien, --action-temp 2) $(date +%H:%M:%S)"
python -X utf8 -u self_play.py --mode network --model models/alphazero_v24-b06_brierbest.onnx \
  --spec models/v24-b06_brierbest.spec.json --games 20 --sims 100 --version smoke-temp2 \
  --threads 11 --chunk 10 --per-file 10 --seed 20260951 --action-temp 2
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 8) Rauchprobe Weg B (20 Partien, Ausflug sicher) $(date +%H:%M:%S)"
python -X utf8 -u self_play.py --mode network --model models/alphazero_v24-b06_brierbest.onnx \
  --spec models/v24-b06_brierbest.spec.json --games 20 --sims 100 --version smoke-wegb \
  --threads 11 --chunk 10 --per-file 10 --seed 20260952 --excursion-prob 1.0
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== BAU-FENSTER FERTIG $(date +%H:%M:%S)"
