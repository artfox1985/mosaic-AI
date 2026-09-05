#!/usr/bin/env bash
# v24-Arm b04 (Sicht-Arm, PREREG_stack_top_feature.md par.10; PREREG_v24_window.md par.8):
# Bloecke fuer das ganze v24-Fenster unter INPUT_SIZE 744 (der Block-Schluessel traegt INPUT_SIZE),
# Split und Monolith, dann Training v24-b04 mit Warmstart aus v23-b01_brierbest (30 neue
# Eingangsspalten null-initialisiert, train.py). Einziger Faktor gegen b01: die 30 Sichtwerte.
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/night_v24_b04_chain.sh
# Voraussetzungen, die die Kette selbst prueft: config.INPUT_SIZE == 744 (Python-Patch angewendet,
# NACH dem Start des b03-Trainings), kein Self-Play- und kein Cache-Bau-Prozess (der Block-Bau ist
# der eine CPU-Auftrag neben dem GPU-Training), Training erst, wenn kein train.py mehr laeuft.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART="evaluations/artifacts"

procs() {
  powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.Name -eq 'python.exe' -and \$_.CommandLine -match '$1' }).Count" 2>/dev/null | tr -d '\r'
}

echo "== 0) Voraussetzungen ($(date +%H:%M:%S))"
python - <<'EOF'
import config, sys
sys.path.insert(0, "engine/py")
print("config.INPUT_SIZE =", config.INPUT_SIZE)
raise SystemExit(0 if config.INPUT_SIZE == 744 else 40)
EOF
tick=0
while true; do
  sp=$(procs 'self_play\.py'); sp=${sp:-0}
  cb=$(procs 'build_cache_incremental'); cb=${cb:-0}
  [ "$sp" = "0" ] && [ "$cb" = "0" ] && break
  tick=$((tick+1)); [ $((tick % 10)) -eq 0 ] && echo "   warte auf freie CPU: self_play=$sp cache=$cb ($(date +%H:%M:%S))"
  sleep 60
done

export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v24.json MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_VAL_POOL='^selfplay_v23-b01-'

echo "== 1) Bloecke fuer das v24-Fenster unter INPUT_SIZE 744 (alle 2.945 neu; Bezug 36 min bei 6 Workern) $(date +%H:%M:%S)"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d --value-target-variant nortv --workers 6 --file-list data/window_v24.txt
python - <<'EOF'
import json
d=json.load(open('evaluations/artifacts/cache_build_incremental.json',encoding='utf-8'))
print('Bloecke neu gebaut:', d['neu_gebaut'], 'von', d['dateien'], '| Laufzeit', d['laufzeit'])
EOF

echo "== 2) Trainingsanteil, Schluessel, Monolith (cache_build_time par.12) $(date +%H:%M:%S)"
python -X utf8 tools/window_train_split.py --file-list data/window_v24.txt --val-frac 0.05 --val-pool '^selfplay_v23-b01-' --encoder 2d --value-target-variant nortv --train-list-out data/window_v24_train.txt --val-list-out data/window_v24_val.txt > "$ART/v24_b04_split.txt"; cat "$ART/v24_b04_split.txt"
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v24_b04_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 41; }
echo "KEY=$KEY (b01 hatte 976b1ef66843; muss sich unterscheiden, weil INPUT_SIZE im Schluessel steckt)"
[ "$KEY" != "976b1ef66843" ] || { echo "STOPP: Schluessel unveraendert -- INPUT_SIZE steckt nicht im Fenster-Schluessel?"; exit 42; }
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d --value-target-variant nortv --workers 6 --file-list data/window_v24_train.txt --merge-out "data/.cache_${KEY}.h5"
ls -la "data/.cache_${KEY}.h5"

echo "== 3) Warten, bis kein train.py mehr laeuft $(date +%H:%M:%S)"
while true; do
  t=$(procs 'train\.py'); t=${t:-0}
  [ "$t" = "0" ] && break
  sleep 120
done

echo "== 4) Training v24-b04 (b01-Rezept, Fenster v24, INPUT_SIZE 744, Warmstart mit null-initialisierten Sichtspalten, 30 Werte) $(date +%H:%M:%S)"
python -X utf8 -u train.py --name v24-b04 --load v23-b01_brierbest --file-list data/window_v24.txt --encoder 2d --value-target-variant nortv --value-head wdl --ownership-head-2d --ownership-weight 1.0 --endgame-head --opp-points-head --moon-loss-weight 0 --select-by-brier --val-frac 0.05 --epochs 12 --lr 5e-5 --lr-schedule cosine --lr-t-max 12 --seed 20260828

echo "== KETTE b04 FERTIG $(date +%H:%M:%S): Abnahme mit tools/night_v24_acceptance_chain.sh b04 (braucht das neue Wheel, Encoder 744)."
