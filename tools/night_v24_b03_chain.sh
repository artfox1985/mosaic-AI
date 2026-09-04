#!/usr/bin/env bash
# Nachtprogramm 2026-09-05: v24-Arm b03 (Seeding-Schwarm), PREREG_start_position_seeding.md par.7,
# PREREG_v24_window.md par.8. Nutzer-Freigabe 2026-09-04, 23:30 fuer die Trainingsarme.
# Aufruf (Projektordner, Hintergrund, ohne Pipe, ohne Umleitung):  bash tools/night_v24_b03_chain.sh
# Taktung gegen tools/night_v24_chain.sh (Kette A):
#   - wartet, bis das Training v24-b01 LAEUFT (dann ist Kette A durch Tor 0, Manifest, Fensterliste,
#     Bloecke und Monolith, und die CPU ist frei) -> Kuratierung + Seeding-Schwarm = der eine CPU-Auftrag
#   - Bloecke und Monolith fuer das b03-Fenster laufen, waehrend b02 auf der GPU trainiert
#   - Training v24-b03 erst, wenn kein train.py mehr laeuft (b02 fertig)
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART="evaluations/artifacts"

procs() {
  powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.Name -eq 'python.exe' -and \$_.CommandLine -match '$1' }).Count" 2>/dev/null | tr -d '\r'
}

echo "== 0) Warten, bis das Training v24-b01 laeuft ($(date +%H:%M:%S); Deckel 24 h)"
tick=0
while true; do
  t=$(procs 'train\.py --name v24-b01'); t=${t:-0}
  [ "$t" != "0" ] && break
  tick=$((tick+1)); [ "$tick" -gt 1440 ] && { echo "STOPP: nach 24 h kein v24-b01-Training gesehen (Kette A an einem Tor gestoppt?)"; exit 20; }
  [ $((tick % 30)) -eq 0 ] && echo "   warte auf v24-b01-Training ($(date +%H:%M:%S))"
  sleep 60
done
echo "   v24-b01 trainiert -- CPU frei ($(date +%H:%M:%S))"
n_arg=$(ls data/selfplay_v23-b01-value-argmax_*.pkl | wc -l)
[ "$n_arg" -eq 600 ] || { echo "STOPP: erwartet 600 argmax-Dateien, gefunden $n_arg"; exit 21; }

echo "== 1) Kuratierung (par.7: Spieler am Zug, R2-4, Fortschritt 3-5, 1.500 Stellungen, Seed 20260912, --verify 500)"
python -X utf8 -u tools/seed_position_curation.py --mode am-zug --korpus-glob "data/selfplay_v23-b01-value-argmax_*.pkl" --verify 500 --run --target 1500 --seed 20260912 --out-set data/seed_positions/seed_positions_v2.jsonl --out-report "$ART/seed_positions_curation_report_v2.json"
n_pos=$(grep -c '"state"' data/seed_positions/seed_positions_v2.jsonl)
[ "$n_pos" -eq 1500 ] || { echo "STOPP: erwartet 1.500 Stellungen, gefunden $n_pos"; exit 22; }

echo "== 2) Seeding-Schwarm: 1.500 Stellungen x k = 4 = 6.000 Partien, value-only @100, gesampelt (par.7; Knopf wie 6b', Nachtrag par.7) $(date +%H:%M:%S)"
export MOSAIC_STACK_DRAW_RESEARCH=1 MOSAIC_ENVELOPE_PROJECTED=1 MOSAIC_ENVELOPE_SEARCH_C=1.0
python -u self_play.py --mode network --model models/alphazero_v23-b01_brierbest.onnx --games 6000 --sims 100 --value-only --seed-positions data/seed_positions/seed_positions_v2.jsonl --version v23-b01-seedvalue --threads 11 --chunk 10 --seed 20260913 --per-file 10
unset MOSAIC_STACK_DRAW_RESEARCH MOSAIC_ENVELOPE_PROJECTED MOSAIC_ENVELOPE_SEARCH_C
n_seed=$(ls data/selfplay_v23-b01-seedvalue_*.pkl | wc -l)
[ "$n_seed" -eq 600 ] || { echo "STOPP: erwartet 600 Seeding-Dateien, gefunden $n_seed"; exit 23; }

echo "== 3) Fensterliste b03 = window_v24.txt + 600 Seeding-Dateien"
python - <<'EOF'
import glob,os
base=[l.strip() for l in open('data/window_v24.txt',encoding='utf-8') if l.strip() and not l.startswith('#')]
seed=sorted(os.path.basename(p) for p in glob.glob('data/selfplay_v23-b01-seedvalue_*.pkl'))
assert len(base)==2945 and len(seed)==600, (len(base),len(seed))
with open('data/window_v24_b03.txt','w',encoding='utf-8',newline='\n') as fh:
    fh.write('# v24-Fenster b03 (start_position_seeding par.7): window_v24.txt plus 600 selfplay_v23-b01-seedvalue-Dateien\n')
    fh.write('\n'.join(base+seed)+'\n')
print('window_v24_b03.txt:', len(base)+len(seed), 'Dateien')
EOF

export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v24.json MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_VAL_POOL='^selfplay_v23-b01-'

echo "== 4) Bloecke (nur die 600 neuen) und Monolith fuer den b03-Trainingsanteil (par.12) $(date +%H:%M:%S)"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d --value-target-variant nortv --workers 6 --file-list data/window_v24_b03.txt
python -X utf8 tools/window_train_split.py --file-list data/window_v24_b03.txt --val-frac 0.05 --val-pool '^selfplay_v23-b01-' --encoder 2d --value-target-variant nortv --train-list-out data/window_v24_b03_train.txt --val-list-out data/window_v24_b03_val.txt > "$ART/v24_b03_split.txt"; cat "$ART/v24_b03_split.txt"
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v24_b03_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 24; }
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d --value-target-variant nortv --workers 6 --file-list data/window_v24_b03_train.txt --merge-out "data/.cache_${KEY}.h5"
ls -la "data/.cache_${KEY}.h5"

echo "== 5) Warten, bis kein train.py mehr laeuft (b01/b02 fertig) $(date +%H:%M:%S)"
while true; do
  t=$(procs 'train\.py'); t=${t:-0}
  [ "$t" = "0" ] && break
  sleep 120
done

echo "== 6) Training v24-b03 (b01-Rezept, Fenster b03) $(date +%H:%M:%S)"
python -X utf8 -u train.py --name v24-b03 --load v23-b01_brierbest --file-list data/window_v24_b03.txt --encoder 2d --value-target-variant nortv --value-head wdl --ownership-head-2d --ownership-weight 1.0 --endgame-head --opp-points-head --moon-loss-weight 0 --select-by-brier --val-frac 0.05 --epochs 12 --lr 5e-5 --lr-schedule cosine --lr-t-max 12 --seed 20260828

echo "== KETTE b03 FERTIG $(date +%H:%M:%S)"
