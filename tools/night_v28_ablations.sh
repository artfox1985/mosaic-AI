#!/usr/bin/env bash
# v28-Ablationen (PREREG_v28_window.md par.8 Schritt 4), beide mit dem Rezept von v28-b02
# (INPUT_SIZE 755, Rust-Bauer), damit gegen b02 genau EIN Faktor bleibt: die Fensterzusammensetzung.
#   b03 = Fenster OHNE die neue Ausflug-Klasse (selfplay_v27-b01-value-excursion_*, 401 Dateien)
#   b04 = Fenster OHNE den G-2-Posten (alle selfplay_v25-b01-*: 400 policy + 145 excursion)
# Je Arm: Fensterliste, Split, Monolith (Formen-Waechter), Training, Tor 1 gegen v28-b02 mit zwei
# Seeds und Logs. Jeder Schritt bricht bei Fehler ab. Bloecke liegen unter dem 755er-Schluessel
# (Kette b02); sie werden nicht neu gebaut, nur der Monolith.
# Aufruf: bash tools/night_v28_ablations.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
SEED=20260937
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v27-'
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v28.json
export MOSAIC_FEATURES_FROM_RUST=1
SPEC=models/frozen_champions/v27-b01/spec.json
REF=models/alphazero_v28-b02_brierbest.onnx

echo "== 0) Voraussetzungen $(date +%H:%M:%S)"
python -X utf8 -c "from config import INPUT_SIZE; import mosaic_rust as m; assert INPUT_SIZE == 755; assert hasattr(m, 'state_features_from_json')" || { echo "STOPP: Baum/Wheel nicht auf Variante B"; exit 11; }
[ -f "$REF" ] || { echo "STOPP: $REF fehlt"; exit 12; }
[ -f data/window_v28.txt ] || { echo "STOPP: data/window_v28.txt fehlt"; exit 12; }

run_arm () {
  ARM=$1; PATTERN=$2; LABEL=$3
  echo "== $ARM) Fensterliste ohne $LABEL $(date +%H:%M:%S)"
  grep -v -E "$PATTERN" data/window_v28.txt > "data/window_v28_${ARM}.txt"
  echo "   $(wc -l < data/window_v28.txt) -> $(wc -l < data/window_v28_${ARM}.txt) Dateien"
  python -X utf8 tools/window_train_split.py --file-list "data/window_v28_${ARM}.txt" --val-frac 0.05 \
    --val-pool '^selfplay_v27-' --encoder 2d --value-target-variant nortv \
    --train-list-out "data/window_v28_${ARM}_train.txt" --val-list-out "data/window_v28_${ARM}_val.txt" > "$ART/v28_split_${ARM}.txt"
  cat "$ART/v28_split_${ARM}.txt"
  KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v28_split_${ARM}.txt" | awk '{print $NF}')
  [ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
  echo "KEY=$KEY"
  python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
    --value-target-variant nortv --workers 6 --file-list "data/window_v28_${ARM}_train.txt" \
    --merge-out "data/.cache_${KEY}.h5"
  RC=$?; [ "$RC" -eq 0 ] || { echo "STOPP: Monolith-Merge Exit $RC"; exit 14; }
  ls -la "data/.cache_${KEY}.h5"
  echo "== $ARM) Training v28-$ARM (Warmstart v27-b01_brierbest) $(date +%H:%M:%S)"
  python -X utf8 -u train.py --name "v28-$ARM" --load v27-b01_brierbest \
    --file-list "data/window_v28_${ARM}.txt" --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
    --val-frac 0.05 --encoder 2d --value-head wdl --value-target-variant nortv \
    --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 1.0 \
    --endgame-head --opp-points-head --destretch-a 0.0051 --destretch-b 1.9269 \
    --select-by-brier --fast-loader --seed $SEED
  RC=$?; echo "   Training Exit $RC ($(date +%H:%M:%S))"
  [ "$RC" -eq 0 ] || { echo "STOPP: Training $ARM Exit $RC"; exit 17; }
  NET="models/alphazero_v28-${ARM}_brierbest.onnx"
  [ -f "$NET" ] || { echo "STOPP: kein ONNX fuer $ARM"; exit 18; }
  for S in $4 $5; do
    echo "== TOR 1 Seed 202610$S: v28-$ARM gegen v28-b02 $(date +%H:%M:%S)"
    python -X utf8 -u tools/paired_gating.py \
      --model-a "$NET" --model-b "$REF" \
      --name-a "v28-$ARM" --name-b v28-b02 \
      --spec-a "$SPEC" --spec-b "$SPEC" \
      --sims 400 --block-size 5 --max-pairs 200 --seed "202610$S" --threads 10 \
      --log-games --no-promote-winner --out "$ART/paired_gating_v28-${ARM}_vs_v28-b02_s$S.json"
    echo "   Exit $? ($(date +%H:%M:%S))"
  done
}

run_arm b03 "^selfplay_v27-b01-value-excursion_" "neue Ausflug-Klasse" 40 41
run_arm b04 "^selfplay_v25-b01-" "G-2-Posten (v25-b01)" 42 43
echo "== v28-ABLATIONEN FERTIG $(date +%F' '%H:%M:%S)"
