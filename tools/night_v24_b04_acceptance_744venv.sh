#!/usr/bin/env bash
# Abnahme des 744er-Arms v24-b04 VOR der Installation des 744er-Wheels (2026-09-05, 22:05):
# laeuft in der Mess-venv `venv_measure744/` mit dem frisch gebauten Wheel (engine/target/wheels,
# 21:01, Kontrakt 20b442a8164f748d, K3-P2 enthalten, Default aus). So kann die CPU messen, waehrend
# b05 auf der GPU trainiert und das alte Wheel haelt. Anker-Drift unter diesem Wheel: GRUEN (22:02,
# frozen_verify_hv1_anchor.json). `python` im PATH zeigt auf die venv, die Abnahme-Kette laeuft unveraendert.
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/night_v24_b04_acceptance_744venv.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
VENV="venv_measure744/Scripts"
[ -x "$VENV/python.exe" ] || { echo "STOPP: $VENV/python.exe fehlt"; exit 90; }
export PATH="$(pwd)/$VENV:$PATH"
python -X utf8 - <<'EOF'
import json, sys, mosaic_rust as mr
c = json.loads(mr.engine_config_json())
print(f"   Mess-venv: {sys.executable} | input_size {c.get('input_size')} | contract {c.get('contract_hash')}")
raise SystemExit(0 if c.get("input_size") == 744 and c.get("contract_hash") == "20b442a8164f748d" else 91)
EOF
[ $? = 0 ] || { echo "STOPP: Mess-venv liefert nicht das 744er-Wheel"; exit 91; }
echo "== Abnahme b04 unter dem 744er-Wheel (Tor 2a/1 ohne und mit Knopf, Tor 2b) $(date +%H:%M:%S)"
bash tools/night_v24_acceptance_chain.sh b04; rc=$?
echo "   Abnahme b04 Exit $rc ($(date +%H:%M:%S))"
python -X utf8 -u tools/probes/arena_points_probe.py --artifact evaluations/artifacts/paired_arena_env_v24b04_vs_b01_first_s14.json evaluations/artifacts/paired_arena_env_v24b04_vs_b01_second_s14.json --out evaluations/artifacts/points_v24b04_vs_b01_s14.json || echo "   Kuppel-Bonus-Sonde b04 fehlgeschlagen"
echo "== FERTIG $(date +%H:%M:%S)"
