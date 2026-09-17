#!/usr/bin/env bash
# Fahrplan 36e, Arm v29-b08 (PREREG_minimal_strength_core.md par.10.4): ZWEIERPAKET der beiden
# am wenigsten tragenden Koepfe -- ownership-Loss 0 und OHNE endgame-Kopf; opp_points und moon
# bleiben wie bei b03 (Nutzer 2026-09-17: "pack die tendenziell am wenigsten tragenden koepfe in
# ein paket zusammen ... fahr sie gegen b03").
#
# ERSTE KETTE AUF DEM NEUEN CACHE-SCHLUESSEL (rust_data_layer par.9b: Formel-Version im Material,
# MOSAIC_FEATURES_FROM_RUST=1 in jeder Kette): alle Bloecke und der Monolith entstehen neu, die
# Bauzeit wird gemessen (Kettenausgabe plus Artefakt von build_cache_incremental).
#
# NEBENLAST: Split und Blockbau sind CPU-Auftraege und warten auf eine freie CPU (Sonde, Arena,
# cargo/maturin). Das Training (GPU) darf neben EINEM CPU-Auftrag laufen; Tor 1 wartet wieder.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v28-'
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v29.json
# Planes-Semantik einheitlich FRISCH gerechnet (rust_data_layer par.9a/9b, Nutzer 2026-09-17).
export MOSAIC_FEATURES_FROM_RUST=1
unset MOSAIC_MOON_TARGET_SOURCE
ART=evaluations/artifacts
SEED=20260941

[ -f "data/$MOSAIC_CARRIER_MANIFEST" ] || { echo "ABBRUCH: data/$MOSAIC_CARRIER_MANIFEST fehlt"; exit 1; }
[ -f data/window_v29.txt ] || { echo "ABBRUCH: data/window_v29.txt fehlt"; exit 1; }
[ -f models/alphazero_v29-b03_brierbest.onnx ] || { echo "ABBRUCH: b03-Modell fehlt"; exit 1; }
grep -q "FEATURE_FORMULA_VERSION" config.py || { echo "ABBRUCH: Schluessel-Umbau (FEATURE_FORMULA_VERSION in config.py) fehlt noch"; exit 2; }

cpu_frei() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { (\$_.CommandLine -match '[t]rain\.py|[p]aired_gating\.py|[f]rozen_referee_match\.py|[b]uild_cache|[c]ounterfactual_tiling|[o]ffline_diagnosis|[d]ead_unit_probe|[m]aturin|[w]indow_train_split' -and \$_.Name -match 'python') -or \$_.Name -match '^(cargo|rustc)' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}
warte_frei() {
  echo "########## b08-KETTE WARTET ($1) $(date +%F' '%H:%M:%S)"
  while :; do
    cpu_frei && { echo "   Maschine frei ($(date +%H:%M:%S))"; break; }
    echo "   belegt ($(date +%H:%M:%S))"; sleep 120
  done
  sleep 20
}

warte_frei "Split, Bloecke, Monolith"
echo ""
echo "== 1) Trainingsanteil, Schluessel (label/794, Formel-Version, FROM_RUST=1) $(date +%H:%M:%S)"
python -X utf8 tools/window_train_split.py --file-list data/window_v29.txt --val-frac 0.05 \
  --val-pool '^selfplay_v28-' --encoder 2d --value-target-variant nortv \
  --train-list-out data/window_v29_b08_train.txt --val-list-out data/window_v29_b08_val.txt \
  > "$ART/v29_b08_split.txt"
cat "$ART/v29_b08_split.txt"
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v29_b08_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
echo "KEY=$KEY"
cmp -s data/window_v29_b08_train.txt data/window_v29_v29-b03_train.txt && echo "   Trainingsliste byte-gleich mit b03" || echo "   WARNUNG: Trainingsliste weicht von b03 ab"

echo ""
echo "== 2) Bloecke und Monolith unter $KEY $(date +%F' '%H:%M:%S)"
CACHE="data/.cache_${KEY}.h5"
T0=$(date +%s)
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v29_b08_train.txt \
  --merge-out "$CACHE"
echo "   Exit $? ($(date +%H:%M:%S)); Bloecke plus Merge: $(( $(date +%s) - T0 )) s Wanduhr"
[ -f "$CACHE" ] || { echo "STOPP: Monolith fehlt"; exit 14; }
ls -la "$CACHE"
python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; print('   Stempel:',k); sys.exit(0 if k==sys.argv[2] else 16)" "$CACHE" "$KEY" || { echo "STOPP: Stempel passt nicht zum Schluessel"; exit 16; }

echo ""
echo "== 3) Training v29-b08 $(date +%F' '%H:%M:%S)"
python -X utf8 -u train.py --name v29-b08 --load v28-b02_brierbest \
  --file-list data/window_v29.txt --cache-file "$CACHE" \
  --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac 0.05 --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 0.0 \
  --opp-points-head --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed $SEED
echo "   Training Exit $? ($(date +%H:%M:%S))"

if [ -f models/alphazero_v29-b08_brierbest.onnx ]; then
  A=models/alphazero_v29-b08_brierbest.onnx
elif [ -f models/alphazero_v29-b08.onnx ]; then
  A=models/alphazero_v29-b08.onnx
  echo "HINWEIS: kein _brierbest -- beste Epoche war die letzte, finales Modell wird genommen"
else
  echo "UEBERSPRUNGEN: kein Modell v29-b08 -- Training gescheitert?"; exit 15
fi
B=models/alphazero_v29-b03_brierbest.onnx
SPEC=models/frozen_champions/v28-b02/spec.json

warte_frei "Tor 1"
echo ""
echo "== 4) Tor 1 b08 gegen b03, zwei Seeds a 200 Paaren, Nichtunterlegenheit 5 Prozentpunkte $(date +%H:%M:%S)"
echo "   Modell A: $A"; ls -l "$A"
for S in 20261160 20261161; do
  OUT="$ART/tor1_v29-b08_vs_b03_s${S}.json"
  echo ""
  echo "===== Seed $S $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$A" --spec-a "$SPEC" --model-b "$B" --spec-b "$SPEC" \
    --name-a v29-b08 --name-b v29-b03 \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$S" --threads 10 --log-games --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_tor1_b08_s${S}.json"
done

echo ""
echo "########## b08-KETTE FERTIG $(date +%F' '%H:%M:%S)"
echo "   Faellig danach: Manifest-Diff gegen b03 (GENAU ownership_weight, endgame_head, cache_file,"
echo "   Name), Verdikt nach par.10.4, sechs Kennzahlen, Bauzeit nach docs/measured_runtimes.md."
