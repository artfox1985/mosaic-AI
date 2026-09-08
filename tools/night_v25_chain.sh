#!/usr/bin/env bash
# v25-Kette: Traeger-Manifest, Fenster, Bloecke, Monolith, Training v25-b01.
# Nach dem Muster von tools/night_v24_chain.sh. Zuschnitt: PREREG_v25_window.md par.1/par.2.
# Nutzer-Auftrag 2026-09-08: "du kannst das training von v25_b01 starten sobald verfuegbar."
#
# SEED der Auswahlen: 20260925 (v24 nahm 20260921). Er ist in par.1c registriert.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
SEED=20260925

echo "== 1) Traeger-Manifest v25 (580 Dateien = 400 neu + 135 G-1 + 45 G-2) $(date +%H:%M:%S)"
python -X utf8 tools/generate_carrier_manifest.py \
  --from-list data/carriers_v23_hv2.txt --n-files 45 --seed $SEED \
  --include-glob "selfplay_v24-b07-policy_*.pkl" \
  --pick "selfplay_v23-b01-policy_*.pkl:135" \
  --out policy_carrier_manifest_v25.json
python - <<'EOF'
import json
d = json.load(open('data/policy_carrier_manifest_v25.json', encoding='utf-8'))
f = d['policy_carrier_files']
neu = [x for x in f if x.startswith('selfplay_v24-b07-policy_')]
g1  = [x for x in f if x.startswith('selfplay_v23-b01-policy_')]
g2  = [x for x in f if x.startswith('selfplay_hv2_')]
print(f'Manifest: {len(f)} Traeger = {len(neu)} neu + {len(g1)} G-1 + {len(g2)} G-2')
assert (len(f), len(neu), len(g1), len(g2)) == (580, 400, 135, 45), (len(f), len(neu), len(g1), len(g2))
EOF

echo "== 2) hv2-Auswahl: 365 der 1.565 maskierten (par.2) $(date +%H:%M:%S)"
python - <<'EOF'
# Die 1.565 hv2-Dateien, die NICHT zu den 180 bisherigen Traegern gehoeren.
alle = [l.strip() for l in open('data/window_v23_hv2.txt', encoding='utf-8')
        if l.strip() and not l.startswith('#')]
tr = {l.strip() for l in open('data/carriers_v23_hv2.txt', encoding='utf-8')
      if l.strip() and not l.startswith('#')}
rest = sorted(set(alle) - tr)
assert len(alle) == 1745 and len(tr) == 180 and len(rest) == 1565, (len(alle), len(tr), len(rest))
open('data/hv2_swarm_candidates_v25.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(rest) + '\n')
print(f'{len(rest)} Kandidaten geschrieben')
EOF
python -X utf8 tools/generate_carrier_manifest.py \
  --from-list data/hv2_swarm_candidates_v25.txt --n-files 365 --seed $SEED \
  --list-out data/hv2_swarm_pick_v25.txt --out hv2_swarm_pick_v25_manifest.json
echo "   gewaehlt: $(grep -vc '^#' data/hv2_swarm_pick_v25.txt) (Soll 365)"

echo "== 3) Fensterliste data/window_v25.txt $(date +%H:%M:%S)"
python - <<'EOF'
import glob, os
def base(p): return os.path.basename(p)
neu_pol = sorted(base(p) for p in glob.glob('data/selfplay_v24-b07-policy_*.pkl'))
neu_tmp = sorted(base(p) for p in glob.glob('data/selfplay_v24-b07-value-tempc_*.pkl'))
neu_exc = sorted(base(p) for p in glob.glob('data/selfplay_v24-b07-value-excursion*_*.pkl'))
g1_pol  = sorted(base(p) for p in glob.glob('data/selfplay_v23-b01-policy_*.pkl'))
g1_val  = sorted(base(p) for p in glob.glob('data/selfplay_v23-b01-value-*.pkl'))
tr_hv2  = [l.strip() for l in open('data/carriers_v23_hv2.txt', encoding='utf-8')
           if l.strip() and not l.startswith('#')]
sw_hv2  = [l.strip() for l in open('data/hv2_swarm_pick_v25.txt', encoding='utf-8')
           if l.strip() and not l.startswith('#')]
hv2 = sorted(set(tr_hv2) | set(sw_hv2))   # 180 + 365 = 545
assert (len(neu_pol), len(neu_tmp), len(g1_pol), len(g1_val), len(hv2)) == (400, 400, 400, 800, 545), \
    (len(neu_pol), len(neu_tmp), len(g1_pol), len(g1_val), len(hv2))
assert 400 <= len(neu_exc) <= 405, len(neu_exc)
allf = neu_pol + neu_tmp + neu_exc + g1_pol + g1_val + hv2
fehlt = [b for b in allf if not os.path.exists(os.path.join('data', b))]
assert not fehlt, fehlt[:5]
assert len(allf) == len(set(allf)), 'Doppelte im Fenster'
with open('data/window_v25.txt', 'w', encoding='utf-8', newline='\n') as fh:
    fh.write('# v25-Fenster (PREREG_v25_window.md par.1/par.2): 400 Sockel + 400 temperiert + '
             f'{len(neu_exc)} Ausflug + 400 G-1-policy + 800 G-1-value + 545 hv2\n')
    fh.write('\n'.join(allf) + '\n')
print(f'window_v25.txt: {len(allf)} Dateien')
EOF

export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v25.json
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v24-b07-'

echo "== 4) Bloecke fuers Fenster UNTER der Trainings-Umgebung $(date +%H:%M:%S)"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v25.txt
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 5) Trainingsanteil, Schluessel, Monolith $(date +%H:%M:%S)"
python -X utf8 tools/window_train_split.py --file-list data/window_v25.txt --val-frac 0.05 \
  --val-pool '^selfplay_v24-b07-' --encoder 2d --value-target-variant nortv \
  --train-list-out data/window_v25_train.txt --val-list-out data/window_v25_val.txt > "$ART/v25_split.txt"
cat "$ART/v25_split.txt"
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v25_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
echo "KEY=$KEY"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v25_train.txt \
  --merge-out "data/.cache_${KEY}.h5"
ls -la "data/.cache_${KEY}.h5"

echo "== 6) Training v25-b01 (Warmstart v24-b06_brierbest = die Gewichte von b07) $(date +%H:%M:%S)"
python -X utf8 -u train.py --name v25-b01 --load v24-b06_brierbest \
  --file-list data/window_v25.txt --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac 0.05 --val-pool '^selfplay_v24-b07-' --val-pool-guard pool_set \
  --encoder 2d --value-head wdl --value-target-variant nortv --value-target-lambda 0.7 \
  --ownership-head-2d --ownership-weight 1.0 --endgame-head --opp-points-head \
  --head-warmstart --ignore-policy-target-valid --bootstrap-coherence off \
  --destretch-a 0.0051 --destretch-b 1.9269 --early-stop --select-by-brier \
  --epoch-checkpoint --snapshot --fast-loader --seed 20260925
echo "   Training Exit $? ($(date +%H:%M:%S))"
echo "== v25-KETTE FERTIG $(date +%H:%M:%S)"
