#!/usr/bin/env bash
# Build nach dem Umbau von Weg B und Weg C auf eine Ziehungsregel
# (PREREG_start_position_seeding.md par.9h/9i). Aus tools/wegb_temp2_build_window.sh.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
echo "== 0) Python-DLL in den PATH $(date +%H:%M:%S)"
. tools/hooks/python_dll_path.sh 2>/dev/null && mosaic_prepend_python_dll_path 2>/dev/null || true
echo "== 1) cargo test --release --lib $(date +%H:%M:%S)"
( cd engine && cargo test --release --lib ); rc=$?
echo "   Exit $rc ($(date +%H:%M:%S))"
[ "$rc" = "0" ] || { echo "STOPP: cargo test rot."; exit 41; }
echo "== 2) cargo test --release --no-run (examples und benches) $(date +%H:%M:%S)"
( cd engine && cargo test --release --no-run ); rc=$?
echo "   Exit $rc ($(date +%H:%M:%S))"
[ "$rc" = "0" ] || { echo "STOPP: examples/benches brechen."; exit 42; }
echo "== 3) Wheel bauen und installieren $(date +%H:%M:%S)"
( cd engine && python -m maturin build --release ); rc=$?
[ "$rc" = "0" ] || { echo "STOPP: maturin rot."; exit 43; }
WHEEL=$(ls -t engine/target/wheels/*.whl | head -1)
python -m pip install --force-reinstall --no-deps "$WHEEL"; rc=$?
echo "   Install Exit $rc ($(date +%H:%M:%S))"
[ "$rc" = "0" ] || { echo "STOPP: Install rot."; exit 44; }
echo "== 4) Anker-Drift $(date +%H:%M:%S)"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv1_anchor \
  --out evaluations/artifacts/anchor_drift_20260907_wegbc.json
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== 5) Anker-Konservierung $(date +%H:%M:%S)"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv1_anchor --venv \
  --out evaluations/artifacts/anchor_conservation_20260907_wegbc.json
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== 6) Rauchprobe Weg B: 20 Partien, Ausflug sicher $(date +%H:%M:%S)"
python -X utf8 -u self_play.py --mode network --model models/alphazero_v24-b07_brierbest.onnx \
  --spec models/v24-b07_brierbest.spec.json --games 20 --sims 100 --version smoke-wegb2 \
  --threads 11 --chunk 10 --per-file 10 --seed 20260961 --excursion-prob 1.0 \
  --tau-argmax-from-move 1 --no-root-noise
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== 7) Rauchprobe Weg C: 20 Partien, Abweichung sicher $(date +%H:%M:%S)"
python -X utf8 -u self_play.py --mode network --model models/alphazero_v24-b07_brierbest.onnx \
  --spec models/v24-b07_brierbest.spec.json --games 20 --sims 100 --version smoke-wegc2 \
  --threads 11 --chunk 10 --per-file 10 --seed 20260962 --deviate-prob 1.0 --tau-argmax-from-move 1
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== BAU-FENSTER FERTIG $(date +%H:%M:%S)"
