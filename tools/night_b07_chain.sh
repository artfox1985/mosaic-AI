#!/usr/bin/env bash
# Nachtprogramm 2026-09-02/03 N1: v23-b07 nach dem Relabel -- Manifest, Bloecke, Split, Monolith, Training.
# Aufruf (aus dem Projektordner, NACHDEM data/relabeled_v23_deep/ 200 Dateien traegt und
# evaluations/artifacts/relabel_net_relabeled_v23_deep.json geschrieben ist):
#     bash tools/night_b07_chain.sh
# Hintergrund, ohne Pipe, ohne Umleitung (CLAUDE.md "Lange Laeufe NIE in eine Pipe").
# Herleitung jedes Schritts: PREREG_reanalyze_label_depth.md par.A4, PREREG_cache_build_time.md par.12.
set -euo pipefail
cd "$(dirname "$0")/.."
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v23_deep.json MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_VAL_POOL='^selfplay_v22-b05'
export PYTHONIOENCODING=utf-8
TMP="evaluations/artifacts"

echo "== 0) Deep-Dateien nach data/ kopieren (eigener Praefix, kollisionsfrei)"
n_src=$(ls data/relabeled_v23_deep/selfplay_v22-b05deep-policy_*.pkl | wc -l)
[ "$n_src" -eq 200 ] || { echo "erwartet 200 Deep-Dateien, gefunden $n_src"; exit 2; }
cp -n data/relabeled_v23_deep/selfplay_v22-b05deep-policy_*.pkl data/
echo "in data/: $(ls data/selfplay_v22-b05deep-policy_*.pkl | wc -l)"

echo "== 1) Traeger-Manifest (180 hv2 + 200 deep)"
python -X utf8 tools/generate_carrier_manifest.py --from-list data/window_v23_hv2.txt --n-files 180 --seed 20260921 --include-glob "selfplay_v22-b05deep-policy_*.pkl" --out policy_carrier_manifest_v23_deep.json
python - <<'EOF'
import json
d=json.load(open('data/policy_carrier_manifest_v23_deep.json',encoding='utf-8'))
f=d['policy_carrier_files']; hv2=[x for x in f if x.startswith('selfplay_hv2')]; deep=[x for x in f if 'b05deep' in x]
ref=[l.strip() for l in open('data/carriers_v23_hv2.txt',encoding='utf-8') if l.strip() and not l.startswith('#')]
print('Manifest:', len(f), 'Eintraege; hv2', len(hv2), 'deep', len(deep), '; hv2 == v23-Traeger:', sorted(hv2)==sorted(ref))
assert len(f)==380 and sorted(hv2)==sorted(ref)
EOF

echo "== 2) Bloecke fuer das Deep-Fenster unter der Trainings-Umgebung (nur fehlende)"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d --value-target-variant nortv --workers 6 --file-list data/window_v23_deep.txt

echo "== 3) Trainingsanteil und Schluessel"
python -X utf8 tools/window_train_split.py --file-list data/window_v23_deep.txt --val-frac 0.05 --val-pool '^selfplay_v22-b05' --encoder 2d --value-target-variant nortv --train-list-out data/window_v23_deep_train.txt --val-list-out data/window_v23_deep_val.txt > "$TMP/split.txt"; cat "$TMP/split.txt"
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$TMP/split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "kein Schluessel"; exit 3; }
echo "KEY=$KEY"

echo "== 4) Monolith fuer den Trainingsanteil"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d --value-target-variant nortv --workers 6 --file-list data/window_v23_deep_train.txt --merge-out "data/.cache_${KEY}.h5"
ls -la "data/.cache_${KEY}.h5"

echo "== 5) Training v23-b07 (b01-Rezept, Warmstart v22-b05)"
python -X utf8 -u train.py --name v23-b07 --load v22-b05 --file-list data/window_v23_deep.txt --encoder 2d --value-target-variant nortv --value-head wdl --ownership-head-2d --ownership-weight 1.0 --endgame-head --opp-points-head --moon-loss-weight 0 --select-by-brier --val-frac 0.05 --epochs 12 --lr 5e-5 --lr-schedule cosine --lr-t-max 12 --seed 20260828
