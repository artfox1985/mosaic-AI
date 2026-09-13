#!/usr/bin/env bash
# v29-Kette: Traeger-Kennzahl, Traeger-Manifest, Fenster, Bloecke, Monolith, Training v29-b01.
# Nach dem Muster von tools/night_v28_chain.sh. Zuschnitt: PREREG_v29_window.md par.1.
#
# SEED der Auswahlen UND des Trainings: 20260941 (v28 nahm 20260937), par.1 registriert.
# VAL-POOL: '^selfplay_v28-' (die neue Generation stellt den Validierungsanteil).
# G-2-POSTEN: die AUSFLUG-Haelfte von v26-b01 (Nutzer-Entscheid 2026-09-13, par.2 dort:
#   "Nimm fuer die g-2 das selbe was wir auch bei v28 hatten"). Variable G2_SWARM_PATTERN unten.
#
# ROTATION: v25-b01 ist am 2026-09-13 aus der Rotation gefallen und geloescht. Das Fenster
# besteht aus v28-b02 (neu), v27-b01 (G-1) und v26-b01 (G-2).
#
# FENSTER-PINNING: nicht noetig, weil jeder Schritt mit einer EXPLIZITEN Dateiliste arbeitet
# (--file-list). Streudateien koennen also nicht still mitlaufen. Das Pinning per
# MOSAIC_DATA_EXCLUDE bliebe der Weg, wenn je ohne Liste gebaut wird.
#
# WARTEBEDINGUNG, gehaertet: laufzeit-Block im Manifest der Ausflug-Klasse (den schreibt
# self_play.py erst am Ende) UND eine KLARE 0 aus der Prozessabfrage; alles andere gilt als
# belegt. Der escapte Punkt und der Ausschluss der PowerShell-Prozesse verhindern den
# Selbsttreffer vom 2026-09-09 (und den zweiten vom 2026-09-13).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
SEED=20260941
G2_SWARM_PATTERN="selfplay_v26-b01-value-excursion_*.pkl"   # par.2, Nutzer-Entscheid 2026-09-13

erzeugung_fertig() {
  python - <<'PYEOF'
import glob, io, json
try:
    ps = sorted(glob.glob("data/manifest_v28-b02-value-excursion_*.json"))
    d = json.load(io.open(ps[-1], encoding="utf-8")) if ps else {}
    print("JA" if "laufzeit" in d else "NEIN")
except Exception:
    print("UNKLAR")
PYEOF
}

keine_erzeugung_laeuft() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '[s]elf_play\.py' -and \$_.Name -notmatch 'pwsh|powershell' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}

echo "== WARTEN auf die Ausflug-Klasse $(date +%F' '%H:%M:%S)"
while :; do
  status=$(erzeugung_fertig)
  if [ "$status" = "JA" ] && keine_erzeugung_laeuft; then
    echo "   Erzeugung durch ($(date +%H:%M:%S))"
    break
  fi
  echo "   noch nicht ($(date +%H:%M:%S)): laufzeit=$status"
  sleep 300
done

echo "== 0) Cache-Waechter beenden $(date +%H:%M:%S)"
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '[b]uild_cache_incremental' -and \$_.Name -notmatch 'pwsh|powershell' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }" 2>/dev/null || true
sleep 10

export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v28-'

echo "== 1) Traeger-Kennzahl der Klassen (Tor 0) $(date +%H:%M:%S)"
for k in v27-b01-policy v28-b02-policy v28-b02-value-tempc v28-b02-value-excursion; do
  python -X utf8 -u tools/corpus_sanity_check.py data --pattern "selfplay_${k}_*.pkl" --out "$ART/corpus_sanity_${k}.json"
done
# Tor 2a ex post (docs/generation_loop.md): der Generator v28-b02 darf als Punktschaetzer nicht
# unter den Vorgaenger fallen. Nur Vorlage, kein Abbruch.
# HINWEIS 2026-09-13: beide Seiten sind bei 100 Sims erzeugt, der Vergleich ist also in derselben
# Betriebsart (PREREG_search_depth_column_optimum.md par.8e -- bei 400 waere ein niedrigerer Wert
# der Suchtiefen-Effekt und allein kein gerissenes Tor gewesen).
python - <<'PYCHK'
import json, io
v = {}
for k in ("v27-b01-policy", "v28-b02-policy"):
    d = json.load(io.open(f"evaluations/artifacts/corpus_sanity_{k}.json", encoding="utf-8"))["arme"][0]
    v[k] = (d["sp_voll"], d["sp_voll_ci"], d["seiten"])
a, b = v["v27-b01-policy"], v["v28-b02-policy"]
print(f"TOR 2a ex post: v28-b02 als Generator {b[0]:.3f} (+-{b[1]:.3f}, {b[2]} Seiten) "
      f"gegen v27-b01 {a[0]:.3f} (+-{a[1]:.3f}) -> {'HAELT' if b[0] >= a[0] else 'GERISSEN (Nutzer-Vorlage)'}")
PYCHK

echo "== 2) Traeger-Manifest v29 (580 = 400 neu + 135 G-1 + 45 G-2) $(date +%H:%M:%S)"
python -X utf8 tools/generate_carrier_manifest.py \
  --pattern "selfplay_v26-b01-policy_*.pkl" --n-files 45 --seed $SEED \
  --include-glob "selfplay_v28-b02-policy_*.pkl" \
  --pick "selfplay_v27-b01-policy_*.pkl:135" \
  --out policy_carrier_manifest_v29.json
python - <<'PYEOF'
import json
d = json.load(open('data/policy_carrier_manifest_v29.json', encoding='utf-8'))
f = d['policy_carrier_files']
neu = [x for x in f if x.startswith('selfplay_v28-b02-policy_')]
g1 = [x for x in f if x.startswith('selfplay_v27-b01-policy_')]
g2 = [x for x in f if x.startswith('selfplay_v26-b01-policy_')]
print(f'Manifest: {len(f)} Traeger = {len(neu)} neu + {len(g1)} G-1 + {len(g2)} G-2')
assert (len(f), len(neu), len(g1), len(g2)) == (580, 400, 135, 45), (len(f), len(neu), len(g1), len(g2))
PYEOF
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v29.json

echo "== 3) Schwarm G-2: 145 aus $G2_SWARM_PATTERN (par.2) $(date +%H:%M:%S)"
python -X utf8 tools/generate_carrier_manifest.py \
  --pattern "$G2_SWARM_PATTERN" --n-files 145 --seed $SEED \
  --list-out data/v26_swarm_pick_v29.txt --out v26_swarm_pick_v29_manifest.json
echo "   gewaehlt: $(grep -vc '^#' data/v26_swarm_pick_v29.txt) (Soll 145)"

echo "== 4) Fensterliste data/window_v29.txt $(date +%H:%M:%S)"
python - <<'PYEOF'
import glob, os
def base(p): return os.path.basename(p)
neu_pol = sorted(base(p) for p in glob.glob('data/selfplay_v28-b02-policy_*.pkl'))
neu_tmp = sorted(base(p) for p in glob.glob('data/selfplay_v28-b02-value-tempc_*.pkl'))
neu_exc = sorted(base(p) for p in glob.glob('data/selfplay_v28-b02-value-excursion_*.pkl'))
g1_pol = sorted(base(p) for p in glob.glob('data/selfplay_v27-b01-policy_*.pkl'))
g1_tmp = sorted(base(p) for p in glob.glob('data/selfplay_v27-b01-value-tempc_*.pkl'))
g1_exc = sorted(base(p) for p in glob.glob('data/selfplay_v27-b01-value-excursion_*.pkl'))
g2_pol = sorted(base(p) for p in glob.glob('data/selfplay_v26-b01-policy_*.pkl'))
g2_val = [l.strip() for l in open('data/v26_swarm_pick_v29.txt', encoding='utf-8')
          if l.strip() and not l.startswith('#')]
zahlen = (len(neu_pol), len(neu_tmp), len(neu_exc), len(g1_pol), len(g1_tmp),
          len(g1_exc), len(g2_pol), len(g2_val))
print('Klassen:', zahlen)
assert (len(neu_pol), len(neu_tmp)) == (400, 400), zahlen
assert 395 <= len(neu_exc) <= 410, zahlen
assert (len(g1_pol), len(g1_tmp)) == (400, 400), zahlen
assert 395 <= len(g1_exc) <= 410, zahlen
assert (len(g2_pol), len(g2_val)) == (400, 145), zahlen  # G-2-Schwarm: 145 aus der Ausflug-Haelfte (par.2)
allf = neu_pol + neu_tmp + neu_exc + g1_pol + g1_tmp + g1_exc + g2_pol + g2_val
fehlt = [b for b in allf if not os.path.exists(os.path.join('data', b))]
assert not fehlt, fehlt[:5]
assert len(allf) == len(set(allf)), 'Doppelte im Fenster'
with open('data/window_v29.txt', 'w', encoding='utf-8', newline='\n') as fh:
    fh.write('# v29-Fenster (PREREG_v29_window.md par.1): 400 Sockel + 400 temperiert + '
             f'{len(neu_exc)} Ausflug (neu, Generator v28-b02) + 400 G-1-policy + '
             f'{len(g1_tmp)+len(g1_exc)} G-1-value + 400 G-2-policy + 145 G-2-value (Ausflug)\n')
    fh.write('\n'.join(allf) + '\n')
print(f'window_v29.txt: {len(allf)} Dateien (Soll rund 2.947)')
PYEOF

echo "== 5) Bloecke fuers Fenster UNTER der Trainings-Umgebung $(date +%H:%M:%S)"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v29.txt
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 6) Trainingsanteil, Schluessel, Monolith $(date +%H:%M:%S)"
python -X utf8 tools/window_train_split.py --file-list data/window_v29.txt --val-frac 0.05 \
  --val-pool '^selfplay_v28-' --encoder 2d --value-target-variant nortv \
  --train-list-out data/window_v29_train.txt --val-list-out data/window_v29_val.txt > "$ART/v29_split.txt"
cat "$ART/v29_split.txt"
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v29_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
echo "KEY=$KEY"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v29_train.txt \
  --merge-out "data/.cache_${KEY}.h5"
ls -la "data/.cache_${KEY}.h5"

# Die Flags --val-pool, --ignore-policy-target-valid, --head-warmstart und
# --bootstrap-coherence GIBT ES IN train.py NICHT; sie kommen aus der Umgebung.
# Early-Stop, Epoch-Checkpoint, Snapshot und Head-Warmstart sind per Default an.
# Abbruch? Fortsetzen mit demselben Aufruf plus --resume (Fingerabdruck-Waechter).
echo "== 7) Training v29-b01 (Warmstart v28-b02_brierbest) $(date +%H:%M:%S)"
echo "   Umgebung: CARRIER_MANIFEST=$MOSAIC_CARRIER_MANIFEST VAL_POOL=$MOSAIC_VAL_POOL"
python -X utf8 -u train.py --name v29-b01 --load v28-b02_brierbest \
  --file-list data/window_v29.txt --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac 0.05 --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 1.0 \
  --endgame-head --opp-points-head --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed $SEED
echo "   Training Exit $? ($(date +%H:%M:%S))"
echo "== v29-KETTE FERTIG $(date +%F' '%H:%M:%S)"
echo "   v29-b01 ist der Pflichtarm; b02 (Spezialfeld-Ablation) und b03 (Sicht-Arm) folgen"
echo "   auf demselben Fenster mit eigenen Bloecken (PREREG_v29_window.md par.6/par.6c)."
