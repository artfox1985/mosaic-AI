#!/usr/bin/env bash
# v28-Programm: Kompilier- und Wheel-Durchgang fuer die neuen, bisher unkompilierten Knoepfe
# (round_estimate K4, Rueckgabe-Reihenfolge, Startslot P0/P1) in EINEM Wheel. Tore, alle mit
# Default 0/ungesetzt: cargo-Lib-Tests (darunter Kontrakt-Hash-Literal und die Netz-Paritaets-
# Fixture des amtierenden Champions, erwartet UNVERAENDERT), Beispiele/Benches (--no-run), dann
# Anker-Drift UND Konservierung gegen hv1_anchor_v2 (CLAUDE.md "Nach jeder Engine-Aenderung").
# Rauchtest der Startslot-Sonde am Ende. Volllast: NUR bei freier Maschine starten.
# Aufruf: bash tools/night_v28_knob_build.sh   (Hintergrundaufgabe, keine Pipe)
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
WHEEL=engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl
# cygpath ist Pflicht (Vorfall 2026-09-10: Windows-Pfad mit Doppelpunkt zerlegt PATH der Git-Bash)
PYDIR="$(cygpath -u "$(python -c 'import sys,os;print(os.path.dirname(sys.executable))')")"
export PATH="$PYDIR:$PATH"

echo "== 1) cargo test --release --lib $(date +%F' '%H:%M:%S)"
( cd engine && cargo test --release --lib )
RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"; [ $RC -eq 0 ] || { echo "STOPP: Lib-Tests rot"; exit 21; }

echo "== 2) cargo test --release --no-run (examples/benches) $(date +%H:%M:%S)"
( cd engine && cargo test --release --no-run )
RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"; [ $RC -eq 0 ] || { echo "STOPP: examples/benches kompilieren nicht"; exit 22; }

echo "== 3) maturin build + pip install $(date +%H:%M:%S)"
( cd engine && python -m maturin build --release )
RC=$?; echo "   maturin Exit $RC"; [ $RC -eq 0 ] || { echo "STOPP: Wheel-Bau rot"; exit 23; }
python -m pip install --force-reinstall --no-deps "$WHEEL"
RC=$?; echo "   pip Exit $RC ($(date +%H:%M:%S))"; [ $RC -eq 0 ] || exit 24
sha256sum "$WHEEL"
python -X utf8 -c "import mosaic_rust as mr, json; c=json.loads(mr.engine_config_json()); print('contract_hash', c['contract_hash'], 'input_size', c.get('input_size'))"

echo "== 4) Anker-Drift (Live-Wheel gegen hv1_anchor_v2) $(date +%H:%M:%S)"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv1_anchor_v2 \
  --out "$ART/anchor_drift_live_wheel_20260912_knobs.json"
RC=$?; echo "   Drift Exit $RC ($(date +%H:%M:%S))"; [ $RC -eq 0 ] || { echo "STOPP: Anker-Drift ROT -- Nutzer-Entscheid, keine Reparatur"; exit 25; }
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv1_anchor_v2 --venv \
  --out "$ART/anchor_conservation_artifact_wheel_20260912_knobs.json"
echo "   Konservierung Exit $? ($(date +%H:%M:%S))"

echo "== 5) Konventionen und Knopf-Doku $(date +%H:%M:%S)"
python -X utf8 tools/generate_knob_docs.py; echo "   knobs.md Exit $?"
python -X utf8 tools/check_conventions.py; echo "   check_conventions Exit $?"

echo "== 6) Rauchtest Startslot-Sonde (4 Partien je Slot, 25 Sims) $(date +%H:%M:%S)"
python -X utf8 -u tools/probes/start_dome_slot_probe.py --limit 4 --pairings 25 --threads 4 \
  --out "$ART/start_dome_slot_probe_smoke.json"
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== KNOPF-BAU FERTIG $(date +%F' '%H:%M:%S)"
