#!/usr/bin/env bash
# E4-Arm v34-b03 (PREREG_v34_window.md par.3, PREREG_evaluator_pretests.md par.8c): Angebots-Bedarfs-
# Abschnitt im Encoder (engine/src/supply_demand.rs, 48 Werte, Eingabebreite 936). Gleiches Fenster,
# gleicher Split, gleicher Seed wie v34-b01; einziger Unterschied: MOSAIC_SUPPLY_DEMAND_FEATURES=1
# (eigene Bloecke und Monolith, Marker supplydemand_v1). Warmstart von v33-b01 (888): die neuen
# Eingangsspalten starten mit Nullen (train.py).
#   Teil 1 (CPU): Bloecke und Monolith -- wartet auf eine freie CPU, ein laufendes GPU-Training ist erlaubt.
#   Teil 2 (GPU): Training -- wartet, bis kein anderes train.py mehr laeuft (eine GPU).
#
# KEINE PIPE hinter langen Laeufen, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
SEED=20260961
ARM=v34-b03
LOAD=v33-b01_brierbest
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v33-b01-'
export MOSAIC_FEATURES_FROM_RUST=1
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v34.json
export MOSAIC_DATA_EXCLUDE='selfplay_v29-b11-probe_,selfplay_depth,selfplay_s4states,selfplay_tor2a'
export MOSAIC_SUPPLY_DEMAND_FEATURES=1
unset MOSAIC_MOON_TARGET_SOURCE MOSAIC_CACHE_FINAL_MARGIN

for f in data/window_v34.txt data/window_v34.valfrac data/window_v34_val.txt "models/alphazero_${LOAD}.pth"; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
for f in "models/alphazero_${ARM}.pth" "models/alphazero_${ARM}_best.pth" "models/alphazero_${ARM}_brierbest.pth"; do
  [ -f "$f" ] && { echo "ABBRUCH: $f liegt schon"; exit 4; }
done
python -X utf8 -c "import config,sys; print('   config.INPUT_SIZE', config.INPUT_SIZE); sys.exit(0 if config.INPUT_SIZE==936 else 3)" \
  || { echo "ABBRUCH: config.INPUT_SIZE ist nicht 936 trotz Knopf"; exit 3; }
VF=$(tr -d '[:space:]' < data/window_v34.valfrac)

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
BUSY_PATTERN='[s]elf_play\.py|[p]aired_gating|[p]aired_arena|[f]rozen_referee|[b]uild_cache|[w]indow_train_split|[a]rgmax_profile' \
  wait_for_free_cpu "E4-Cache"
echo "== E4-Arm $ARM: Cache mit Angebots-Bedarfs-Abschnitt $(date +%F' '%H:%M:%S)"
python -X utf8 tools/window_train_split.py --file-list data/window_v34.txt --val-frac "$VF" \
  --val-pool "$MOSAIC_VAL_POOL" --encoder 2d --value-target-variant nortv \
  --train-list-out data/window_v34_e4_train.txt --val-list-out data/window_v34_e4_val.txt \
  > "$ART/v34_e4_split.txt"
cat "$ART/v34_e4_split.txt"
cmp -s <(grep -v '^#' data/window_v34_val.txt | sort) <(grep -v '^#' data/window_v34_e4_val.txt | sort) \
  || { echo "STOPP: Val-Menge weicht vom Grundarm ab"; exit 12; }
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v34_e4_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
CACHE="data/.cache_${KEY}.h5"
T0=$(date +%s)
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v34_e4_train.txt --merge-out "$CACHE"
echo "   Exit $? ($(date +%H:%M:%S)); Bloecke plus Merge: $(( $(date +%s) - T0 )) s Wanduhr"
[ -f "$CACHE" ] || { echo "STOPP: Monolith fehlt"; exit 14; }
python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; print('   Stempel:',k); sys.exit(0 if k==sys.argv[2] else 16)" "$CACHE" "$KEY" \
  || { echo "STOPP: Stempel passt nicht"; exit 16; }
echo "##### E4-CACHE FERTIG $(date +%F' '%H:%M:%S) -- CPU frei fuer den naechsten Auftrag"

BUSY_PATTERN='[t]rain\.py' wait_for_free_cpu "E4-Training (GPU frei?)"
echo "##### E4-TRAINING STARTET $(date +%F' '%H:%M:%S)"
python -X utf8 -u train.py --name "$ARM" --load "$LOAD" \
  --file-list data/window_v34.txt --cache-file "$CACHE" \
  --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac "$VF" --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 0.0 \
  --moon-loss-weight 0.0 --opp-points-head \
  --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed $SEED
echo "   Training Exit $? ($(date +%H:%M:%S))"
echo "########## E4-ARM FERTIG $(date +%F' '%H:%M:%S)"
