#!/usr/bin/env bash
# Nachtprogramm 2026-09-04/05: v24 nach der Erzeugung -- Tor 0, Traeger-Manifest,
# Fensterliste, Bloecke, Split, Monolith, Training v24-b01 und v24-b02.
# Nutzer-Freigabe 2026-09-04, 23:30: "du kannst ruhig schon die trainingsarme
# beginnen. es ist ja alles festgehalten" (PREREG_v24_window.md par.6d, 6e, 8).
# Aufruf (aus dem Projektordner, im Hintergrund, ohne Pipe, ohne Umleitung):
#     bash tools/night_v24_chain.sh
# Die Kette WARTET selbst, bis beide Value-Laeufe (800 Dateien) und der
# Cache-Watcher zu Ende sind; erst dann ist sie der eine CPU-Auftrag.
# Herleitung jedes Schritts: PREREG_v24_window.md par.6c-6e, PREREG_cache_build_time.md par.12,
# Vorlage tools/night_b07_chain.sh (2026-09-03). b03 (Seeding-Schwarm) laeuft NICHT hier
# (Kuratierung braucht erst die Value-Klasse und eine Werkzeug-Aenderung, start_position_seeding par.7).
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART="evaluations/artifacts"

procs() {
  powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.Name -eq 'python.exe' -and \$_.CommandLine -match '$1' }).Count" 2>/dev/null | tr -d '\r'
}

echo "== 0) Warten auf das Ende der Value-Laeufe und des Watchers ($(date +%H:%M:%S))"
tick=0
while true; do
  n=$(ls data/selfplay_v23-b01-value-*.pkl 2>/dev/null | wc -l)
  sp=$(procs 'self_play\.py'); sp=${sp:-0}
  wa=$(procs 'build_cache_incremental'); wa=${wa:-0}
  if [ "$n" -ge 800 ] && [ "$sp" = "0" ] && [ "$wa" = "0" ]; then break; fi
  if [ "$sp" = "0" ] && [ "$n" -lt 800 ]; then echo "STOPP: kein self_play-Prozess, aber nur $n von 800 Value-Dateien ($(date +%H:%M:%S))"; exit 10; fi
  tick=$((tick+1)); if [ $((tick % 10)) -eq 0 ]; then echo "   warte: $n/800 Dateien, self_play=$sp, watcher=$wa ($(date +%H:%M:%S))"; fi
  sleep 60
done
echo "   Value-Laeufe und Watcher beendet: $n Dateien ($(date +%H:%M:%S))"
n_pol=$(ls data/selfplay_v23-b01-policy_*.pkl | wc -l)
[ "$n_pol" -eq 400 ] || { echo "STOPP: erwartet 400 Policy-Dateien, gefunden $n_pol"; exit 11; }

echo "== 1) Tor 0 auf der Value-Klasse (par.6c Punkt 3) plus Fenster-Kennzahl der Policy-Klasse (v25 par.7)"
python -X utf8 -u tools/probes/corpus_column_outcome_symmetry_probe.py --data-dir data --pattern "selfplay_v23-b01-value-*.pkl" --out "$ART/v24_symmetry_value_class.json"
python -X utf8 -u tools/corpus_sanity_check.py data --pattern "selfplay_v23-b01-value-*.pkl" --out "$ART/v24_sanity_value_class.json"
python -X utf8 -u tools/corpus_sanity_check.py data --pattern "selfplay_v23-b01-policy_*.pkl" --out "$ART/v24_sanity_policy_class.json"
python - <<'EOF'
import json
s=json.load(open('evaluations/artifacts/v24_symmetry_value_class.json',encoding='utf-8'))
v=s['verdikt']; print('Symmetrie:', v)
a=json.load(open('evaluations/artifacts/v24_sanity_value_class.json',encoding='utf-8'))['arme'][0]
print('Value-Klasse: Partien', a['partien'], 'Seiten', a['seiten'], 'sides_with_full_column', a['sides_with_full_column'], 'sp_voll', a['sp_voll'], 'punkte', a['punkte'])
p=json.load(open('evaluations/artifacts/v24_sanity_policy_class.json',encoding='utf-8'))['arme'][0]
print('Policy-Klasse: Partien', p['partien'], 'sides_with_full_column', p['sides_with_full_column'], 'sp_voll', p['sp_voll'], 'punkte', p['punkte'])
ok = (v.get('verdikt') == 'TRENNT') and a['partien'] == 8000 and a['sides_with_full_column'] >= 1500
print('TOR 0:', 'GRUEN' if ok else 'GERISSEN -- kein Training, Vorlage')
raise SystemExit(0 if ok else 12)
EOF

echo "== 2) Traeger-Manifest 580 (par.6d; --out ist RELATIV zu data/)"
python -X utf8 tools/generate_carrier_manifest.py --from-list data/window_v23_hv2.txt --n-files 180 --seed 20260921 --include-glob "selfplay_v23-b01-policy_*.pkl" --out policy_carrier_manifest_v24.json
python - <<'EOF'
import json
d=json.load(open('data/policy_carrier_manifest_v24.json',encoding='utf-8'))
f=d['policy_carrier_files']; hv2=[x for x in f if x.startswith('selfplay_hv2')]; pol=[x for x in f if x.startswith('selfplay_v23-b01-policy_')]
ref=[l.strip() for l in open('data/carriers_v23_hv2.txt',encoding='utf-8') if l.strip() and not l.startswith('#')]
print('Manifest:', len(f), 'Eintraege; hv2', len(hv2), 'policy', len(pol), '; hv2 == v23-Traeger:', sorted(hv2)==sorted(ref))
assert len(f)==580 and len(pol)==400 and sorted(hv2)==sorted(ref)
EOF

echo "== 3) Fensterliste data/window_v24.txt (1.745 hv2 + 1.200 neu = 2.945)"
python - <<'EOF'
import glob,os
hv2=[l.strip() for l in open('data/window_v23_hv2.txt',encoding='utf-8') if l.strip() and not l.startswith('#')]
new=sorted(os.path.basename(p) for p in glob.glob('data/selfplay_v23-b01-*.pkl'))
assert len(hv2)==1745, len(hv2); assert len(new)==1200, len(new)
pol=[x for x in new if '-policy_' in x]; arg=[x for x in new if '-value-argmax_' in x]; smp=[x for x in new if '-value-sampled_' in x]
assert (len(pol),len(arg),len(smp))==(400,600,200), (len(pol),len(arg),len(smp))
allf=hv2+new
missing=[b for b in allf if not os.path.exists(os.path.join('data',b))]
assert not missing, missing[:5]
with open('data/window_v24.txt','w',encoding='utf-8',newline='\n') as fh:
    fh.write('# v24-Fenster (PREREG_v24_window.md par.6d): window_v23_hv2.txt unveraendert plus alle 1.200 selfplay_v23-b01-*-Dateien\n')
    fh.write('\n'.join(allf)+'\n')
print('window_v24.txt:', len(allf), 'Dateien (policy', len(pol), 'argmax', len(arg), 'sampled', len(smp), ')')
EOF

export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v24.json MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_VAL_POOL='^selfplay_v23-b01-'

echo "== 4) Bloecke fuer das Fenster unter der Trainings-Umgebung (nur fehlende; der Watcher hat die meisten gebaut)"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d --value-target-variant nortv --workers 6 --file-list data/window_v24.txt

echo "== 5) Trainingsanteil, Schluessel, Monolith (cache_build_time par.12)"
python -X utf8 tools/window_train_split.py --file-list data/window_v24.txt --val-frac 0.05 --val-pool '^selfplay_v23-b01-' --encoder 2d --value-target-variant nortv --train-list-out data/window_v24_train.txt --val-list-out data/window_v24_val.txt > "$ART/v24_split.txt"; cat "$ART/v24_split.txt"
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v24_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
echo "KEY=$KEY"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d --value-target-variant nortv --workers 6 --file-list data/window_v24_train.txt --merge-out "data/.cache_${KEY}.h5"
ls -la "data/.cache_${KEY}.h5"

echo "== 6) Training v24-b01 (par.6e, Warmstart v23-b01_brierbest) $(date +%H:%M:%S)"
python -X utf8 -u train.py --name v24-b01 --load v23-b01_brierbest --file-list data/window_v24.txt --encoder 2d --value-target-variant nortv --value-head wdl --ownership-head-2d --ownership-weight 1.0 --endgame-head --opp-points-head --moon-loss-weight 0 --select-by-brier --val-frac 0.05 --epochs 12 --lr 5e-5 --lr-schedule cosine --lr-t-max 12 --seed 20260828

echo "== 7) Training v24-b02 (par.8: einziger Faktor value_target_lambda 0.7; lambda wirkt nach dem Laden, gleicher Monolith) $(date +%H:%M:%S)"
python -X utf8 -u train.py --name v24-b02 --load v23-b01_brierbest --file-list data/window_v24.txt --encoder 2d --value-target-variant nortv --value-head wdl --ownership-head-2d --ownership-weight 1.0 --endgame-head --opp-points-head --moon-loss-weight 0 --select-by-brier --val-frac 0.05 --epochs 12 --lr 5e-5 --lr-schedule cosine --lr-t-max 12 --seed 20260828 --value-target-lambda 0.7

echo "== KETTE FERTIG $(date +%H:%M:%S): v24-b01 und v24-b02 trainiert; Abnahme (Tor 1, 2a, 2b) folgt getrennt."
