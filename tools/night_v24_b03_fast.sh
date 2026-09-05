#!/usr/bin/env bash
# Training v24-b03 (714er-Arm) mit --fast-loader (2026-09-06, 00:30). Ersetzt Schritt 3-4 von
# night_v24_b03_now.sh: dort lief der Mini-Fenster-Test ROT allein wegen des Pause-Testfalls D1
# (Stopp-Datei kam nach 20 s, der Lauf war da schon fertig); die Faelle B (resume), D (Gewichte) und
# E (fast-loader) waren bitgleich zu A (max|dW| 0,0), E mit 9,2 s gegen 18,0 s Wanduhr. Der Standard-
# Lauf wurde beim Datenaufbau beendet (kein Zwischenstand vorhanden) und hier mit --fast-loader neu
# gestartet; config.INPUT_SIZE steht bereits auf 714 (Schritt 3 der alten Kette).
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/night_v24_b03_fast.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
python -X utf8 -c "import config, sys; print('   config.INPUT_SIZE =', config.INPUT_SIZE); sys.exit(0 if config.INPUT_SIZE == 714 else 72)" || { echo "STOPP: config.INPUT_SIZE ist nicht 714"; exit 72; }
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v24.json MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_VAL_POOL='^selfplay_v23-b01-'
echo "== Training v24-b03 (714, --fast-loader) $(date +%H:%M:%S)"
python -X utf8 -u train.py --name v24-b03 --load v23-b01_brierbest --file-list data/window_v24_b03.txt --encoder 2d --value-target-variant nortv --value-head wdl --ownership-head-2d --ownership-weight 1.0 --endgame-head --opp-points-head --moon-loss-weight 0 --select-by-brier --val-frac 0.05 --epochs 12 --lr 5e-5 --lr-schedule cosine --lr-t-max 12 --seed 20260828 --fast-loader; TRC=$?
echo "   b03-Training Exit $TRC ($(date +%H:%M:%S)); bei Abbruch: derselbe Befehl plus --resume MIT config 714"
echo "== config.INPUT_SIZE zurueck auf 744 $(date +%H:%M:%S)"
python -X utf8 - <<'EOF'
from pathlib import Path
p = Path("config.py"); s = p.read_text(encoding="utf-8")
old = "INPUT_SIZE = 714        #"
assert old in s, "config.py: 714er-Zeile nicht gefunden -- von Hand pruefen"
p.write_text(s.replace(old, "INPUT_SIZE = 744        #", 1), encoding="utf-8")
import importlib, config; importlib.reload(config); print("   config.INPUT_SIZE zurueck auf", config.INPUT_SIZE)
EOF
echo "== FERTIG $(date +%H:%M:%S): b03 $TRC. Abnahme b03 ueber night_v24_b03_acceptance_714.sh (714er-Mess-venv)."
