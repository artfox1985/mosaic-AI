#!/usr/bin/env bash
# E2-Arm v34-b02 (PREREG_v34_window.md par.3, PREREG_evaluator_pretests.md par.4): Margen-Schwellen am
# WDL-Logit. Gleiches Fenster, gleicher Split, gleicher Seed wie der Grundarm v34-b01
# (tools/night_v34_chain.sh Schritt 1-5); einziger Unterschied: Cache-Feld final_margin
# (MOSAIC_CACHE_FINAL_MARGIN=1, eigener Schluessel, darum eigene Bloecke und Monolith) und
# --margin-thresholds. Das Training laeuft auf der GPU; die Kette meldet "E2-TRAINING STARTET", ab
# dann darf EIN CPU-Auftrag parallel laufen.
#
# KEINE PIPE hinter langen Laeufen, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
SEED=20260961
ARM=v34-b02
LOAD=v33-b01_brierbest
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v33-b01-'
export MOSAIC_FEATURES_FROM_RUST=1
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v34.json
export MOSAIC_DATA_EXCLUDE='selfplay_v29-b11-probe_,selfplay_depth,selfplay_s4states,selfplay_tor2a'
export MOSAIC_CACHE_FINAL_MARGIN=1
unset MOSAIC_MOON_TARGET_SOURCE MOSAIC_SUPPLY_DEMAND_FEATURES

for f in data/window_v34.txt data/window_v34.valfrac data/window_v34_val.txt "models/alphazero_${LOAD}.pth"; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
for f in "models/alphazero_${ARM}.pth" "models/alphazero_${ARM}_best.pth" "models/alphazero_${ARM}_brierbest.pth"; do
  [ -f "$f" ] && { echo "ABBRUCH: $f liegt schon"; exit 4; }
done
VF=$(tr -d '[:space:]' < data/window_v34.valfrac)

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
wait_for_free_cpu "E2-Arm"
echo "== E2-Arm $ARM: Cache mit final_margin $(date +%F' '%H:%M:%S)"

python -X utf8 tools/window_train_split.py --file-list data/window_v34.txt --val-frac "$VF" \
  --val-pool "$MOSAIC_VAL_POOL" --encoder 2d --value-target-variant nortv \
  --train-list-out data/window_v34_e2_train.txt --val-list-out data/window_v34_e2_val.txt \
  > "$ART/v34_e2_split.txt"
cat "$ART/v34_e2_split.txt"
cmp -s <(grep -v '^#' data/window_v34_val.txt | sort) <(grep -v '^#' data/window_v34_e2_val.txt | sort) \
  || { echo "STOPP: Val-Menge weicht vom Grundarm ab"; exit 12; }
echo "   Val-Menge identisch mit v34-b01 ($(grep -vc '^#' data/window_v34_e2_val.txt) Dateien)"
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v34_e2_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
CACHE="data/.cache_${KEY}.h5"
T0=$(date +%s)
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v34_e2_train.txt --merge-out "$CACHE"
echo "   Exit $? ($(date +%H:%M:%S)); Bloecke plus Merge: $(( $(date +%s) - T0 )) s Wanduhr"
[ -f "$CACHE" ] || { echo "STOPP: Monolith fehlt"; exit 14; }
python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; ok=(k==sys.argv[2]) and ('final_margin' in h); print('   Stempel:',k,'final_margin:', 'final_margin' in h); sys.exit(0 if ok else 16)" "$CACHE" "$KEY" \
  || { echo "STOPP: Stempel oder final_margin fehlt"; exit 16; }

echo ""
echo "##### E2-TRAINING STARTET $(date +%F' '%H:%M:%S) -- ab jetzt darf EIN CPU-Auftrag parallel laufen"
python -X utf8 -u train.py --name "$ARM" --load "$LOAD" \
  --file-list data/window_v34.txt --cache-file "$CACHE" \
  --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac "$VF" --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 0.0 \
  --moon-loss-weight 0.0 --opp-points-head \
  --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed $SEED --margin-thresholds
echo "   Training Exit $? ($(date +%H:%M:%S))"
python -X utf8 - "$ARM" <<'PYEOF'
import glob, io, json, sys
arm = sys.argv[1]
a = sorted(glob.glob(f"models/manifest_train_{arm}_*.json")); b = sorted(glob.glob("models/manifest_train_v34-b01_*.json"))
if not a or not b:
    print("   Manifest fehlt -- Diff von Hand"); sys.exit(0)
na = json.load(io.open(a[-1], encoding="utf-8")).get("cli_args", {}) or {}
nb = json.load(io.open(b[-1], encoding="utf-8")).get("cli_args", {}) or {}
erwartet = {"name", "cache_file", "margin_thresholds", "margin_threshold_weight"}
unerw = [k for k in sorted(set(na) | set(nb)) if na.get(k) != nb.get(k) and k not in erwartet]
for k in sorted(set(na) | set(nb)):
    if na.get(k) != nb.get(k):
        print(f"   cli_args.{k}: v34-b01={nb.get(k)!r} -> {arm}={na.get(k)!r}{'' if k in erwartet else '  <== STOPP'}")
print(f"   unerwartete Abweichungen: {len(unerw)} (erwartet hoechstens {sorted(erwartet)})")
PYEOF
echo "########## E2-ARM FERTIG $(date +%F' '%H:%M:%S)"
