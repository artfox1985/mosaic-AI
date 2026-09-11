#!/usr/bin/env bash
# Wiederaufnahme der v28-Kette ab Schritt 6 (2026-09-11, 10:40), nachdem der
# erste Lauf am Monolith-Merge starb: 24 Bloecke trugen 755 Spalten unter einem
# 744er-Schluessel (Waechter-Worker hatten config.py waehrend des Variante-B-Baus
# frisch importiert). Die Bloecke sind neu gebaut (Skript im Scratchpad, Liste
# data/window_v28_rebuild24.txt); der Merge traegt seit heute einen Formen-Waechter
# (tools/build_cache_parallel.py::merge) und die Kette bricht bei einem Merge-Fehler
# ab, statt das Training auf einem halben Monolithen zu starten.
#
# Aufruf: bash tools/night_v28_chain_resume.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
SEED=20260937
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v27-'
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v28.json

echo "== 6) Trainingsanteil, Schluessel, Monolith (Wiederaufnahme) $(date +%H:%M:%S)"
python -X utf8 tools/window_train_split.py --file-list data/window_v28.txt --val-frac 0.05 \
  --val-pool '^selfplay_v27-' --encoder 2d --value-target-variant nortv \
  --train-list-out data/window_v28_train.txt --val-list-out data/window_v28_val.txt > "$ART/v28_split.txt"
cat "$ART/v28_split.txt"
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v28_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
[ "$KEY" = "2db448af20fe" ] || { echo "STOPP: Schluessel $KEY weicht vom ersten Lauf (2db448af20fe) ab"; exit 15; }
echo "KEY=$KEY"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v28_train.txt \
  --merge-out "data/.cache_${KEY}.h5"
RC=$?
[ "$RC" -eq 0 ] || { echo "STOPP: Monolith-Merge Exit $RC -- kein Training"; exit 14; }
ls -la "data/.cache_${KEY}.h5"

echo "== 7) Training v28-b01 (Warmstart v27-b01_brierbest) $(date +%H:%M:%S)"
echo "   Umgebung: CARRIER_MANIFEST=$MOSAIC_CARRIER_MANIFEST VAL_POOL=$MOSAIC_VAL_POOL"
python -X utf8 -u train.py --name v28-b01 --load v27-b01_brierbest \
  --file-list data/window_v28.txt --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac 0.05 --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 1.0 \
  --endgame-head --opp-points-head --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed $SEED
echo "   Training Exit $? ($(date +%H:%M:%S))"
echo "== v28-KETTE FERTIG (Wiederaufnahme) $(date +%F' '%H:%M:%S)"
