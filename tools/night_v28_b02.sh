#!/usr/bin/env bash
# v28-b02 = Variante B (elf Kuppelstapel-Merkmale, INPUT_SIZE 755; PREREG_v28_window.md par.8/par.9).
# Voraussetzungen, VOR dem Start von Hand geprueft: Wheel mit INPUT_SIZE 755 installiert,
# Anker-Drift gruen, Paritaetswerkzeug Rust/Python bit-identisch, keine Nebenlast.
# Schritte: Bloecke fuers v28-Fenster unter dem NEUEN Schluessel (INPUT_SIZE ist Teil des
# Schluessels), Split, Monolith (Formen-Waechter), Training v28-b02 (Rezept wie b01,
# Warmstart v27-b01_brierbest, Seed 20260937), dann Tor 1 b02 gegen b01 mit zwei Seeds.
# Jeder Schritt bricht die Kette bei Fehler ab.
# Aufruf: bash tools/night_v28_b02.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
SEED=20260937
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v27-'
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v28.json
export MOSAIC_FEATURES_FROM_RUST=1   # Blockbau ueber den Rust-Bauer (Paritaet vorab belegt)

echo "== 0) INPUT_SIZE im Baum und im Wheel $(date +%H:%M:%S)"
python -X utf8 -c "from config import INPUT_SIZE; import mosaic_rust as m; print('config', INPUT_SIZE); assert INPUT_SIZE == 755; assert hasattr(m, 'state_features_from_json'), 'Wheel ohne Rust-Merkmalsexport'" || { echo "STOPP: Baum/Wheel nicht auf Variante B"; exit 11; }

echo "== 5) Bloecke fuers v28-Fenster unter dem 755er-Schluessel $(date +%H:%M:%S)"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v28.txt
RC=$?; [ "$RC" -eq 0 ] || { echo "STOPP: Blockbau Exit $RC"; exit 12; }

echo "== 6) Trainingsanteil, Schluessel, Monolith $(date +%H:%M:%S)"
python -X utf8 tools/window_train_split.py --file-list data/window_v28.txt --val-frac 0.05 \
  --val-pool '^selfplay_v27-' --encoder 2d --value-target-variant nortv \
  --train-list-out data/window_v28_train.txt --val-list-out data/window_v28_val.txt > "$ART/v28_split_b02.txt"
cat "$ART/v28_split_b02.txt"
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v28_split_b02.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
[ "$KEY" != "2db448af20fe" ] || { echo "STOPP: Schluessel unveraendert (744er) -- INPUT_SIZE nicht im Schluessel?"; exit 16; }
echo "KEY=$KEY"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v28_train.txt \
  --merge-out "data/.cache_${KEY}.h5"
RC=$?; [ "$RC" -eq 0 ] || { echo "STOPP: Monolith-Merge Exit $RC -- kein Training"; exit 14; }
ls -la "data/.cache_${KEY}.h5"

echo "== 7) Training v28-b02 (Variante B, Warmstart v27-b01_brierbest) $(date +%H:%M:%S)"
python -X utf8 -u train.py --name v28-b02 --load v27-b01_brierbest \
  --file-list data/window_v28.txt --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac 0.05 --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 1.0 \
  --endgame-head --opp-points-head --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed $SEED
RC=$?; echo "   Training Exit $RC ($(date +%H:%M:%S))"
[ "$RC" -eq 0 ] || { echo "STOPP: Training Exit $RC"; exit 17; }
[ -f models/alphazero_v28-b02_brierbest.onnx ] || { echo "STOPP: kein ONNX"; exit 18; }

# Tor 1 b02 gegen b01: beide Seiten Champion-Spec, nur das Netz verglichen.
NET_A=models/alphazero_v28-b02_brierbest.onnx
NET_B=models/alphazero_v28-b01_brierbest.onnx
SPEC=models/frozen_champions/v27-b01/spec.json
for S in 38 39; do
  echo "== TOR 1 Seed 202610$S: v28-b02 gegen v28-b01 $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$NET_A" --model-b "$NET_B" \
    --name-a v28-b02 --name-b v28-b01 \
    --spec-a "$SPEC" --spec-b "$SPEC" \
    --sims 400 --block-size 5 --max-pairs 200 --seed "202610$S" --threads 10 \
    --log-games --no-promote-winner --out "$ART/paired_gating_v28-b02_vs_v28-b01_s$S.json"
  echo "   Exit $? ($(date +%H:%M:%S))"
done
echo "== v28-b02 FERTIG $(date +%F' '%H:%M:%S)"
