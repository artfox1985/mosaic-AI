#!/usr/bin/env bash
# v26-Kette: Traeger-Kennzahl, Traeger-Manifest, Fenster, Bloecke, Monolith, Training v26-b01.
# Nach dem Muster von tools/night_v25_chain.sh. Zuschnitt: PREREG_v26_window.md par.1/par.4.
# Nutzer-Auftrag 2026-09-09, 00:55: "training kannst ebenfalls starten. zuschnitt dafuer hast ja."
#
# SEED der Auswahlen: 20260929 (v25 nahm 20260925, v24 20260921). In par.1 registriert.
# VAL-POOL: '^selfplay_v25-' (par.4, der einzige Punkt, den v26 zu entscheiden hatte).
#
# WARTEBEDINGUNG wie in night_v26_swarm.sh: laufzeit-Block im Manifest der Ausflug-Klasse
# UND eine KLARE 0 aus der Prozessabfrage. Alles andere gilt als belegt.
#
# WARUM DER CACHE-WAECHTER HIER BEENDET WIRD: er baut dieselben Datei-Bloecke wie Schritt 5.
# Zwei Prozesse, die denselben Block schreiben, sind ein Rennen um dieselbe .h5 -- billiger
# ist es, den Waechter zu beenden, weil ab hier ohnehin nichts mehr dazukommt.
# SELBSTTREFFER (2026-09-09, hier gefunden): das Suchmuster steht auch in der
# Kommandozeile des FRAGENDEN Prozesses. `-match 'self_play'` lieferte deshalb
# nie 0, sondern 4, und die Wartebedingung ging nie auf -- die Kette stand 35
# Minuten still, obwohl die Erzeugung fertig war. Zwei Sperren dagegen: der
# escapte Punkt (`self_play\.py`; die fragende Kommandozeile traegt den
# Backslash, der Zielprozess nicht) UND der Ausschluss der PowerShell-Prozesse.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
SEED=20260929

sockel_fertig() {
  python - <<'PYEOF'
import glob, io, json
try:
    ps = sorted(glob.glob("data/manifest_v25-b01-value-excursion_*.json"))
    d = json.load(io.open(ps[-1], encoding="utf-8")) if ps else {}
    print("JA" if "laufzeit" in d else "NEIN")
except Exception:
    print("UNKLAR")
PYEOF
}

keine_erzeugung_laeuft() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match 'self_play\.py' -and \$_.Name -notmatch 'pwsh|powershell' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}

echo "== WARTEN auf die Ausflug-Klasse $(date +%F' '%H:%M:%S)"
while :; do
  status=$(sockel_fertig)
  if [ "$status" = "JA" ] && keine_erzeugung_laeuft; then
    echo "   Erzeugung durch ($(date +%H:%M:%S))"
    break
  fi
  echo "   noch nicht ($(date +%H:%M:%S)): laufzeit=$status"
  sleep 300
done

echo "== 0) Cache-Waechter beenden $(date +%H:%M:%S)"
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match 'build_cache_incremental' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }" 2>/dev/null || true
sleep 10

export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v25-'

echo "== 1) Traeger-Kennzahl der Klassen (PREREG_v26_window.md par.3) $(date +%H:%M:%S)"
for k in v24-b07-policy v24-b07-value-tempc v24-b07-value-excursion v25-b01-policy; do
  python -X utf8 -u tools/corpus_sanity_check.py data --pattern "selfplay_${k}_*.pkl" --out "$ART/corpus_sanity_${k}.json"
done

echo "== 2) Traeger-Manifest v26 (580 = 400 neu + 135 G-1 + 45 G-2) $(date +%H:%M:%S)"
python -X utf8 tools/generate_carrier_manifest.py \
  --pattern "selfplay_v23-b01-policy_*.pkl" --n-files 45 --seed $SEED \
  --include-glob "selfplay_v25-b01-policy_*.pkl" \
  --pick "selfplay_v24-b07-policy_*.pkl:135" \
  --out policy_carrier_manifest_v26.json
python - <<'PYEOF'
import json
d = json.load(open('data/policy_carrier_manifest_v26.json', encoding='utf-8'))
f = d['policy_carrier_files']
neu = [x for x in f if x.startswith('selfplay_v25-b01-policy_')]
g1 = [x for x in f if x.startswith('selfplay_v24-b07-policy_')]
g2 = [x for x in f if x.startswith('selfplay_v23-b01-policy_')]
print(f'Manifest: {len(f)} Traeger = {len(neu)} neu + {len(g1)} G-1 + {len(g2)} G-2')
assert (len(f), len(neu), len(g1), len(g2)) == (580, 400, 135, 45), (len(f), len(neu), len(g1), len(g2))
PYEOF
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v26.json

echo "== 3) Schwarm G-2: 145 der 800 v23-b01-value-* (par.1) $(date +%H:%M:%S)"
python -X utf8 tools/generate_carrier_manifest.py \
  --pattern "selfplay_v23-b01-value-*.pkl" --n-files 145 --seed $SEED \
  --list-out data/v23_swarm_pick_v26.txt --out v23_swarm_pick_v26_manifest.json
echo "   gewaehlt: $(grep -vc '^#' data/v23_swarm_pick_v26.txt) (Soll 145)"

echo "== 4) Fensterliste data/window_v26.txt $(date +%H:%M:%S)"
python - <<'PYEOF'
import glob, os
def base(p): return os.path.basename(p)
neu_pol = sorted(base(p) for p in glob.glob('data/selfplay_v25-b01-policy_*.pkl'))
neu_tmp = sorted(base(p) for p in glob.glob('data/selfplay_v25-b01-value-tempc_*.pkl'))
neu_exc = sorted(base(p) for p in glob.glob('data/selfplay_v25-b01-value-excursion_*.pkl'))
g1_pol = sorted(base(p) for p in glob.glob('data/selfplay_v24-b07-policy_*.pkl'))
g1_tmp = sorted(base(p) for p in glob.glob('data/selfplay_v24-b07-value-tempc_*.pkl'))
g1_exc = sorted(base(p) for p in glob.glob('data/selfplay_v24-b07-value-excursion*_*.pkl'))
g2_pol = sorted(base(p) for p in glob.glob('data/selfplay_v23-b01-policy_*.pkl'))
g2_val = [l.strip() for l in open('data/v23_swarm_pick_v26.txt', encoding='utf-8')
          if l.strip() and not l.startswith('#')]
zahlen = (len(neu_pol), len(neu_tmp), len(neu_exc), len(g1_pol), len(g1_tmp),
          len(g1_exc), len(g2_pol), len(g2_val))
print('Klassen:', zahlen)
assert (len(neu_pol), len(neu_tmp)) == (400, 400), zahlen
assert 395 <= len(neu_exc) <= 410, zahlen
assert (len(g1_pol), len(g1_tmp), len(g1_exc)) == (400, 400, 402), zahlen
assert (len(g2_pol), len(g2_val)) == (400, 145), zahlen
allf = neu_pol + neu_tmp + neu_exc + g1_pol + g1_tmp + g1_exc + g2_pol + g2_val
fehlt = [b for b in allf if not os.path.exists(os.path.join('data', b))]
assert not fehlt, fehlt[:5]
assert len(allf) == len(set(allf)), 'Doppelte im Fenster'
with open('data/window_v26.txt', 'w', encoding='utf-8', newline='\n') as fh:
    fh.write('# v26-Fenster (PREREG_v26_window.md par.1): 400 Sockel + 400 temperiert + '
             f'{len(neu_exc)} Ausflug (neu) + 400 G-1-policy + 802 G-1-value + '
             '400 G-2-policy + 145 G-2-value\n')
    fh.write('\n'.join(allf) + '\n')
print(f'window_v26.txt: {len(allf)} Dateien (Soll rund 2.947)')
PYEOF

echo "== 5) Bloecke fuers Fenster UNTER der Trainings-Umgebung $(date +%H:%M:%S)"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v26.txt
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 6) Trainingsanteil, Schluessel, Monolith $(date +%H:%M:%S)"
python -X utf8 tools/window_train_split.py --file-list data/window_v26.txt --val-frac 0.05 \
  --val-pool '^selfplay_v25-' --encoder 2d --value-target-variant nortv \
  --train-list-out data/window_v26_train.txt --val-list-out data/window_v26_val.txt > "$ART/v26_split.txt"
cat "$ART/v26_split.txt"
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v26_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
echo "KEY=$KEY"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v26_train.txt \
  --merge-out "data/.cache_${KEY}.h5"
ls -la "data/.cache_${KEY}.h5"

# Die Flags --val-pool, --ignore-policy-target-valid, --head-warmstart und
# --bootstrap-coherence GIBT ES IN train.py NICHT (geprueft 2026-09-09 gegen die
# argparse-Liste); sie kommen aus der Umgebung. Early-Stop, Epoch-Checkpoint,
# Snapshot und Head-Warmstart sind per Default an. Genau daran ist der Trainingsschritt
# der v25-Kette gescheitert (Exit 2), deshalb hier die Form aus night_v25_train.sh.
echo "== 7) Training v26-b01 (Warmstart v25-b01_brierbest) $(date +%H:%M:%S)"
echo "   Umgebung: CARRIER_MANIFEST=$MOSAIC_CARRIER_MANIFEST VAL_POOL=$MOSAIC_VAL_POOL"
python -X utf8 -u train.py --name v26-b01 --load v25-b01_brierbest \
  --file-list data/window_v26.txt --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac 0.05 --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 1.0 \
  --endgame-head --opp-points-head --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed $SEED
echo "   Training Exit $? ($(date +%H:%M:%S))"
echo "== v26-KETTE FERTIG $(date +%F' '%H:%M:%S)"
