#!/usr/bin/env bash
# b03-Training SOFORT nach b05 (2026-09-06, 00:25), damit die GPU nicht bis zum Ende der CPU-Messungen
# steht (Ersatz fuer Schritte 1-3 und 5 der night_v24_after_b05_chain.sh; deren Schritt 4, die b05-Abnahme,
# uebernimmt night_v24_b05_acceptance_wait.sh). Zulaessig, weil GPU-Training neben EINEM CPU-Auftrag
# erlaubt ist (working_rules.md "Auslastung") und der Mini-Fenster-Test selbst ein GPU-Training ist.
#   1) Wheel 744 (mit K3-P2) in die Basis-Installation -- kein Basis-python haelt mehr das alte Wheel
#      (b05-Training beendet 00:20; die b04-Abnahme laeuft in venv_measure744 mit eigener Kopie).
#      Anker-Drift unter DIESEM Wheel (byte-gleiche Datei) war in venv_measure744 GRUEN (21:45).
#   2) Mini-Fenster-Test Zwischenstand/resume/Pause/fast-loader (GPU, 2 min)
#   3) config.INPUT_SIZE 744 -> 714, Training v24-b03 (714er-Arm; --fast-loader nur bei gruenem Test)
#   4) config.INPUT_SIZE zurueck auf 744
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/night_v24_b03_now.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

echo "== 1) Wheel 744 installieren $(date +%H:%M:%S)"
n=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.Name -eq 'python.exe' -and \$_.CommandLine -notmatch 'venv_measure' -and \$_.CommandLine -match 'train\.py|self_play|paired_|argmax|probe' }).Count" 2>/dev/null | tr -d '\r[:space:]')
[ "${n:-1}" = "0" ] || { echo "STOPP: $n Basis-python-Prozess(e) mit Engine-Bezug laufen -- Wheel nicht installieren"; exit 95; }
WHL=$(ls -t engine/target/wheels/mosaic_rust-*.whl | head -1); echo "   Wheel: $WHL ($(stat -c %y "$WHL" | cut -c1-16))"
python -m pip install --force-reinstall --no-deps "$WHL" 2>&1 | grep -v notice; rc=$?
python -X utf8 - <<'EOF'
import json, mosaic_rust as mr
c = json.loads(mr.engine_config_json())
print("   installiert: input_size", c.get("input_size"), "contract_hash", c.get("contract_hash"), "envelope_slot_w", c.get("envelope_slot_w"))
raise SystemExit(0 if c.get("input_size") == 744 and c.get("contract_hash") == "20b442a8164f748d" else 71)
EOF
[ $? = 0 ] || { echo "STOPP: Wheel liefert nicht INPUT_SIZE 744 / Kontrakt 20b442a8164f748d"; exit 71; }

echo "== 2) Mini-Fenster-Test Zwischenstand/resume/Pause/fast-loader (GPU) $(date +%H:%M:%S)"
bash tools/tests/train_resume_pause_test.sh; TEST_RC=$?
FAST=""; [ "$TEST_RC" = "0" ] && FAST="--fast-loader"
echo "   Test Exit $TEST_RC -> b03 laeuft mit: ${FAST:-Standard-Lader}"

echo "== 3) config.INPUT_SIZE 744 -> 714 und Training v24-b03 (714er-Arm) $(date +%H:%M:%S)"
python -X utf8 - <<'EOF'
from pathlib import Path
p = Path("config.py"); s = p.read_text(encoding="utf-8")
old = "INPUT_SIZE = 744        #"
assert old in s, "config.py: INPUT_SIZE-Zeile nicht wie erwartet"
p.write_text(s.replace(old, "INPUT_SIZE = 714        #", 1), encoding="utf-8")
import importlib, config; importlib.reload(config); print("   config.INPUT_SIZE =", config.INPUT_SIZE)
raise SystemExit(0 if config.INPUT_SIZE == 714 else 72)
EOF
[ $? = 0 ] || { echo "STOPP: config-Wechsel fehlgeschlagen"; exit 72; }
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v24.json MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_VAL_POOL='^selfplay_v23-b01-'
python -X utf8 -u train.py --name v24-b03 --load v23-b01_brierbest --file-list data/window_v24_b03.txt --encoder 2d --value-target-variant nortv --value-head wdl --ownership-head-2d --ownership-weight 1.0 --endgame-head --opp-points-head --moon-loss-weight 0 --select-by-brier --val-frac 0.05 --epochs 12 --lr 5e-5 --lr-schedule cosine --lr-t-max 12 --seed 20260828 $FAST; TRC=$?
echo "   b03-Training Exit $TRC ($(date +%H:%M:%S)); bei Abbruch: derselbe Befehl plus --resume MIT config 714"

echo "== 4) config.INPUT_SIZE zurueck auf 744 $(date +%H:%M:%S)"
python -X utf8 - <<'EOF'
from pathlib import Path
p = Path("config.py"); s = p.read_text(encoding="utf-8")
old = "INPUT_SIZE = 714        #"
assert old in s, "config.py: 714er-Zeile nicht gefunden -- von Hand pruefen"
p.write_text(s.replace(old, "INPUT_SIZE = 744        #", 1), encoding="utf-8")
import importlib, config; importlib.reload(config); print("   config.INPUT_SIZE zurueck auf", config.INPUT_SIZE)
EOF
echo "== FERTIG $(date +%H:%M:%S): Test $TEST_RC, b03 $TRC. Abnahme b03 ueber night_v24_b03_acceptance_714.sh (714er-Mess-venv)."
