#!/usr/bin/env bash
# Fahrplan 36a, Arm v29-b06 (PREREG_minimal_strength_core.md par.10/10.1): der MINIMALKERN.
#
# REZEPT: b03 mit allen Hilfs-Losses aus -- --moon-loss-weight 0, --ownership-weight 0, OHNE
# --endgame-head, OHNE --opp-points-head; sonst identisch (Fenster window_v29, Warmstart
# v28-b02_brierbest, Seed 20260941, 12 Epochen, 794, --select-by-brier, --fast-loader).
# Die Vorpruefung par.10.1 hat gezeigt: moon und points werden positional gelesen und bleiben
# als Ausgaenge (nur der Loss faellt); opp_points und endgame duerfen wirklich entfallen.
#
# DATEN: dieselbe Fensterliste wie b03, Ziel-Quelle label (MOSAIC_MOON_TARGET_SOURCE UNGESETZT),
# also b03s Fenster-Schluessel -- dessen Monolith ist am 2026-09-16 ueberschrieben worden und
# wird hier NEU gebaut (Bloecke unter dem 794er-Schluessel liegen). Adressiert wird der Monolith
# per --cache-file (Lehre b04: nie ueber den Namen hoffen). Den Val-Cache (label/794,
# .cache_eaa464b44cf7.h5) findet train.py ueber den Namen; der Namenspfad prueft seit heute den
# eingepraegten Schluessel.
#
# NEBENLAST: Split und Monolith-Bau sind CPU-Auftraege -- sie warten, bis kein cargo/maturin/
# train.py/Cache-Bau mehr laeuft (eine Arena daneben waere ein zweiter CPU-Auftrag: ebenfalls
# warten). Das TRAINING (GPU) darf neben EINEM CPU-Auftrag laufen; Tor 1 (CPU) wartet wieder
# auf eine freie Maschine.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v28-'
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v29.json
# Merkmalsbauer EXPLIZIT (2026-09-17, PREREG_rust_data_layer.md par.9a/par.9b):
# der Schalter steht seit heute in BEIDEN Cache-Schluesseln, also entscheidet er
# ueber die Adresse der Bloecke und des Monolithen. Innerhalb von v29 stand er
# uneinheitlich (b02/b03 setzten ihn, diese Kette nicht) -- jede Kette setzt ihn
# ab jetzt ausdruecklich auf 1, damit kein Arm die Semantik dessen erbt, der den
# Block zuerst gebaut hat.
export MOSAIC_FEATURES_FROM_RUST=1
unset MOSAIC_MOON_TARGET_SOURCE
ART=evaluations/artifacts
SEED=20260941

[ -f "data/$MOSAIC_CARRIER_MANIFEST" ] || { echo "ABBRUCH: data/$MOSAIC_CARRIER_MANIFEST fehlt"; exit 1; }
[ -f data/window_v29.txt ] || { echo "ABBRUCH: data/window_v29.txt fehlt"; exit 1; }
[ -f models/alphazero_v29-b03_brierbest.onnx ] || { echo "ABBRUCH: b03-Modell fehlt"; exit 1; }

# Gehaertete Wartebedingung (docs/pitfalls.md): klare 0 = frei, Prozess muss python (oder cargo/
# maturin/rustc) sein; dieses Skript wird als DATEI gestartet.
cpu_frei() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { (\$_.CommandLine -match '[t]rain\.py|[p]aired_gating\.py|[f]rozen_referee_match\.py|[b]uild_cache|[c]ounterfactual_tiling|[o]ffline_diagnosis|[d]ead_unit_probe|[m]aturin' -and \$_.Name -match 'python') -or \$_.Name -match '^(cargo|rustc)' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}
warte_frei() {
  echo "########## b06-KETTE WARTET ($1) $(date +%F' '%H:%M:%S)"
  while :; do
    cpu_frei && { echo "   Maschine frei ($(date +%H:%M:%S))"; break; }
    echo "   belegt ($(date +%H:%M:%S))"; sleep 120
  done
  sleep 20
}

warte_frei "Split und Monolith"
echo ""
echo "== 1) Trainingsanteil, Schluessel (label/794) $(date +%H:%M:%S)"
python -X utf8 tools/window_train_split.py --file-list data/window_v29.txt --val-frac 0.05 \
  --val-pool '^selfplay_v28-' --encoder 2d --value-target-variant nortv \
  --train-list-out data/window_v29_b06_train.txt --val-list-out data/window_v29_b06_val.txt \
  > "$ART/v29_b06_split.txt"
cat "$ART/v29_b06_split.txt"
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v29_b06_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
echo "KEY=$KEY"
cmp -s data/window_v29_b06_train.txt data/window_v29_v29-b03_train.txt && echo "   Trainingsliste byte-gleich mit b03" || echo "   WARNUNG: Trainingsliste weicht von b03 ab"
cmp -s data/window_v29_b06_val.txt data/window_v29_v29-b03_val.txt && echo "   Val-Liste byte-gleich mit b03" || echo "   WARNUNG: Val-Liste weicht von b03 ab"

echo ""
# ZWEITER ANLAUF 2026-09-17 01:35: der erste Bau lag unter data/.cache_${KEY}.h5, trug aber den
# Stempel 4dd9f020b232 (Pfadform data/x.pkl im Zusammenfueger, docs/pitfalls.md) und wurde vom
# --cache-file-Waechter abgelehnt. Der Zusammenfueger stempelt seit 01:30 aus absoluten Pfaden;
# gebaut wird unter NEUEM Namen, die alte Datei bleibt zur Loeschung durch den Nutzer liegen
# (eine Nachpraegung der Attribute wurde vom Auto-Modus verweigert).
CACHE="data/.cache_${KEY}_b06.h5"
echo "== 2) Monolith unter $KEY -> $CACHE $(date +%H:%M:%S)"
if [ -f "$CACHE" ]; then
  echo "   liegt schon: $CACHE"; ls -la "$CACHE"
else
  python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
    --value-target-variant nortv --workers 6 --file-list data/window_v29_b06_train.txt \
    --merge-out "$CACHE"
  echo "   Exit $? ($(date +%H:%M:%S))"
fi
[ -f "$CACHE" ] || { echo "STOPP: Monolith fehlt"; exit 14; }
ls -la "$CACHE"
python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; print('   Stempel:',k); sys.exit(0 if k==sys.argv[2] else 16)" "$CACHE" "$KEY" || { echo "STOPP: Stempel passt nicht zum Schluessel"; exit 16; }

echo ""
echo "== 3) Training v29-b06 $(date +%F' '%H:%M:%S)"
python -X utf8 -u train.py --name v29-b06 --load v28-b02_brierbest \
  --file-list data/window_v29.txt --cache-file "$CACHE" \
  --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac 0.05 --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 0.0 \
  --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed $SEED \
  --moon-loss-weight 0
echo "   Training Exit $? ($(date +%H:%M:%S))"

if [ -f models/alphazero_v29-b06_brierbest.onnx ]; then
  A=models/alphazero_v29-b06_brierbest.onnx
elif [ -f models/alphazero_v29-b06.onnx ]; then
  A=models/alphazero_v29-b06.onnx
  echo "HINWEIS: kein _brierbest -- beste Epoche war die letzte, finales Modell wird genommen"
else
  echo "UEBERSPRUNGEN: kein Modell v29-b06 -- Training gescheitert?"; exit 15
fi
B=models/alphazero_v29-b03_brierbest.onnx
SPEC=models/frozen_champions/v28-b02/spec.json

warte_frei "Tor 1"
echo ""
echo "== 4) Tor 1 b06 gegen b03, zwei Seeds a 200 Paaren, Nichtunterlegenheit 5 Prozentpunkte $(date +%H:%M:%S)"
echo "   Modell A: $A"; ls -l "$A"
for S in 20261140 20261141; do
  OUT="$ART/tor1_v29-b06_vs_b03_s${S}.json"
  echo ""
  echo "===== Seed $S $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$A" --spec-a "$SPEC" --model-b "$B" --spec-b "$SPEC" \
    --name-a v29-b06 --name-b v29-b03 \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$S" --threads 10 --log-games --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_tor1_b06_s${S}.json"
done

echo ""
echo "########## b06-KETTE FERTIG $(date +%F' '%H:%M:%S)"
echo "   Faellig danach: Manifest-Diff gegen b03 (GENAU moon_loss_weight, ownership_weight,"
echo "   endgame_head, opp_points_head, cache_file, Name), Verdikt nach par.10 (gepoolt >= 45,0"
echo "   Prozent, kein Seed signifikant dagegen), sechs Kennzahlen, Netz-Gesundheit par.6d."
