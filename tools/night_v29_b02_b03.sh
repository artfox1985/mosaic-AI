#!/usr/bin/env bash
# Fahrplan Nr. 16 und Nr. 18: die beiden EINGANGS-Arme auf demselben Fenster wie b01.
#
#   b02  Spezialfeld-Ablation: MOSAIC_SPECIAL_PLANES_OFF=1 setzt die Planes-Kanaele
#        77/78 auf Null (PREREG_special_tile_yield.md Nachtrag 2026-09-11).
#   b03  Sicht-Arm: Encoder-Abschnitt 16, INPUT_SIZE 794
#        (PREREG_stack_top_feature.md par.17, PREREG_v29_window.md par.6c).
#
# EIN FAKTOR JE ARM. Der Trainingsaufruf ist WORT FUER WORT der von b01 aus
# tools/night_v29_chain.sh Schritt 7, nur --name unterscheidet sich; die
# Umgebungsvariablen ebenso. Alles andere waere ein zweiter Faktor und macht den
# Vergleich gegen b01 wertlos (Regel "Lauf-Manifest gegen Referenz").
#
# Beide Arme brauchen EIGENE Bloecke und einen EIGENEN Monolithen: der Schalter
# steckt im Cache-Schluessel, und INPUT_SIZE ebenfalls. Deshalb laeuft je Arm die
# volle Folge Bloecke -> Split -> Monolith -> Training.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
SEED=20260941
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v28-'
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v29.json
export MOSAIC_FEATURES_FROM_RUST=1

[ -f data/window_v29.txt ] || { echo "ABBRUCH: data/window_v29.txt fehlt"; exit 1; }

lauf_arm () {
  local NAME="$1"
  echo ""
  echo "############ $NAME ############ $(date +%F' '%H:%M:%S)"

  echo "== Bloecke fuers Fenster $(date +%H:%M:%S)"
  python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
    --value-target-variant nortv --workers 6 --file-list data/window_v29.txt
  local rc=$?
  echo "   Bloecke Exit $rc ($(date +%H:%M:%S))"
  [ $rc -eq 0 ] || return 1

  echo "== Trainingsanteil und Schluessel $(date +%H:%M:%S)"
  python -X utf8 tools/window_train_split.py --file-list data/window_v29.txt --val-frac 0.05 \
    --val-pool '^selfplay_v28-' --encoder 2d --value-target-variant nortv \
    --train-list-out "data/window_v29_${NAME}_train.txt" \
    --val-list-out "data/window_v29_${NAME}_val.txt" > "$ART/v29_split_${NAME}.txt"
  cat "$ART/v29_split_${NAME}.txt"
  local KEY
  KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v29_split_${NAME}.txt" | awk '{print $NF}')
  [ -n "$KEY" ] || { echo "ABBRUCH: kein Schluessel fuer $NAME"; return 1; }
  echo "   KEY=$KEY"

  echo "== Monolith $(date +%H:%M:%S)"
  python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
    --value-target-variant nortv --workers 6 --file-list "data/window_v29_${NAME}_train.txt" \
    --merge-out "data/.cache_${KEY}.h5"
  rc=$?
  echo "   Monolith Exit $rc ($(date +%H:%M:%S))"
  [ $rc -eq 0 ] || return 1

  echo "== Training $NAME (Warmstart v28-b02_brierbest) $(date +%H:%M:%S)"
  python -X utf8 -u train.py --name "$NAME" --load v28-b02_brierbest \
    --file-list data/window_v29.txt --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
    --val-frac 0.05 --encoder 2d --value-head wdl --value-target-variant nortv \
    --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 1.0 \
    --endgame-head --opp-points-head --destretch-a 0.0051 --destretch-b 1.9269 \
    --select-by-brier --fast-loader --seed $SEED
  rc=$?
  echo "   Training Exit $rc ($(date +%H:%M:%S))"
  return $rc
}

echo "== ARM 1: v29-b02 (Spezialfeld-Kanaele 77/78 AUS)"
export MOSAIC_SPECIAL_PLANES_OFF=1
lauf_arm v29-b02 || echo "   -> b02 GESCHEITERT, weiter mit b03"
unset MOSAIC_SPECIAL_PLANES_OFF

echo ""
echo "== ARM 2: v29-b03 (Sicht-Arm, INPUT_SIZE 794)"
lauf_arm v29-b03 || echo "   -> b03 GESCHEITERT"

echo ""
echo "== b02 UND b03 FERTIG $(date +%F' '%H:%M:%S)"
echo "   Naechster Fahrplanpunkt: Nr. 17 und Nr. 19 -- Tor 1 je Arm GEGEN b01, zwei Seeds."
echo "   ACHTUNG beim Modellnamen: _brierbest entsteht nur, wenn die beste Epoche weder"
echo "   die letzte noch die val_combined-beste ist. VORHER nachsehen, welche Datei da"
echo "   ist (PREREG_v29_window.md par.9), nicht den Namen raten."
