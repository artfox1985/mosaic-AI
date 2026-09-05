#!/usr/bin/env bash
# v24-Arm b05 (PREREG_policy_surprise_weighting.md par.10; PREREG_v24_window.md par.8):
# Ueberraschungsgewichtung des Policy-Verlusts NUR bei sicherer Suche (alpha 0,5, Top-1 des
# Ziels >= 0,5). Rezept, Fenster, Monolith und INPUT_SIZE wie v24-b04 -- einziger Faktor gegen
# b04: --surprise-alpha 0.5 --surprise-confidence-min 0.5.
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/night_v24_b05_chain.sh
# Wartet, bis das b04-Modell existiert und kein train.py mehr laeuft (GPU frei).
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

procs() {
  powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.Name -eq 'python.exe' -and \$_.CommandLine -match '$1' }).Count" 2>/dev/null | tr -d '\r'
}

echo "== 0) Warten auf models/alphazero_v24-b04_brierbest.onnx und das Ende aller Trainings ($(date +%H:%M:%S); Deckel 30 h)"
tick=0
while true; do
  t=$(procs 'train\.py'); t=${t:-0}
  [ -f models/alphazero_v24-b04_brierbest.onnx ] && [ "$t" = "0" ] && break
  tick=$((tick+1)); [ "$tick" -gt 1800 ] && { echo "STOPP: 30 h ohne b04-Modell"; exit 50; }
  [ $((tick % 30)) -eq 0 ] && echo "   warte: b04=$([ -f models/alphazero_v24-b04_brierbest.onnx ] && echo da || echo fehlt), train.py=$t ($(date +%H:%M:%S))"
  sleep 60
done
python - <<'EOF'
import config
print("config.INPUT_SIZE =", config.INPUT_SIZE)
raise SystemExit(0 if config.INPUT_SIZE == 744 else 51)
EOF

export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v24.json MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_VAL_POOL='^selfplay_v23-b01-'

echo "== 1) Training v24-b05 (b04-Rezept + Ueberraschungsgewichtung mit Sicherheits-Tor) $(date +%H:%M:%S)"
python -X utf8 -u train.py --name v24-b05 --load v23-b01_brierbest --file-list data/window_v24.txt --encoder 2d --value-target-variant nortv --value-head wdl --ownership-head-2d --ownership-weight 1.0 --endgame-head --opp-points-head --moon-loss-weight 0 --select-by-brier --val-frac 0.05 --epochs 12 --lr 5e-5 --lr-schedule cosine --lr-t-max 12 --seed 20260828 --surprise-alpha 0.5 --surprise-confidence-min 0.5

echo "== KETTE b05 FERTIG $(date +%H:%M:%S): Abnahme mit tools/night_v24_acceptance_chain.sh b05 (Bezug b04 UND b01)."
