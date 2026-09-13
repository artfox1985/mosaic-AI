#!/usr/bin/env bash
# Wheel 1 der v29-Vorbereitung: Bau plus die Tore nach dem Bau.
#
# Inhalt dieses Wheels (drei Aenderungen, alle vorher im Baum):
#   1. P.10-Suchfix (state.rs::restore_top_plate_type) -- die Wurzel-Determinisierung
#      wuerfelte den oeffentlichen Typ der obersten Stapelplatte neu.
#   2. Record-Feld tiled_max_row (serialize.rs), P.14 aus PREREG_stack_top_feature par.15,
#      inklusive Lesen in player_from_json (der Roundtrip-Guard verlangt es).
#   3. Stapelzug-Knoepfe im Lauf-Manifest (lib.rs::engine_config_json), Nutzer-Anweisung
#      2026-09-13 "dann muss der knopf rein ins manifest".
#
# Die Lib-Tests und --no-run --all-targets sind VOR diesem Skript gruen gelaufen
# (637 von 638; offen nur die Netz-Paritaets-Fixture, die durch 1. und 2. erwartet rot ist
# und in einem eigenen Schritt bewusst neu erzeugt wird).
#
# Aufruf: bash tools/wheel1_gates.sh   (Hintergrundaufgabe, keine Pipe)
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
export PATH="$(python -c 'import sys,os;print(os.path.dirname(sys.executable))'):$PATH"
ART=evaluations/artifacts
WHEEL=engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl

echo "== 1) maturin build $(date +%F' '%H:%M:%S)"
( cd engine && python -m maturin build --release )
RC=$?; echo "   maturin Exit $RC"; [ $RC -eq 0 ] || { echo "STOPP: Wheel-Bau rot"; exit 23; }

echo "== 2) pip install $(date +%H:%M:%S)"
python -m pip install --force-reinstall --no-deps "$WHEEL"
RC=$?; echo "   pip Exit $RC"; [ $RC -eq 0 ] || exit 24
sha256sum "$WHEEL"

echo "== 3) Vertrag und der NEUE Manifest-Eintrag $(date +%H:%M:%S)"
python -X utf8 -c "import mosaic_rust as mr, json; c=json.loads(mr.engine_config_json()); print('contract_hash', c['contract_hash'], 'input_size', c.get('input_size')); print('stack_draw_research', c.get('stack_draw_research'), '| stack_draw_reservation', c.get('stack_draw_reservation'))"
RC=$?; echo "   Vertrag Exit $RC"; [ $RC -eq 0 ] || exit 25

echo "== 4) Anker-DRIFT: faehrt der Anker auf dem LIVE-Wheel noch dieselben Zuege? $(date +%H:%M:%S)"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor \
  --out "$ART/anchor_drift_live_wheel_20260913_wheel1.json"
RC=$?; echo "   Drift Exit $RC ($(date +%H:%M:%S))"
[ $RC -eq 0 ] || { echo "STOPP: Anker-Drift ROT -- Nutzer-Entscheid, KEINE Reparatur"; exit 26; }

echo "== 5) Konventionen $(date +%H:%M:%S)"
python -X utf8 tools/check_conventions.py
echo "   Konventionen Exit $?"

echo "== WHEEL1-TORE FERTIG $(date +%F' '%H:%M:%S)"
