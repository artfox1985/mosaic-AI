#!/usr/bin/env bash
# ERSETZT 2026-09-26 durch tools/night_v33_b03_b04.sh (b03 und b04 parallel, par.6c). Nicht mehr
# starten; bleibt nur, bis der Nachfolger gelaufen ist.
# v33-b03: 4.000 Schwarm-Partien MEHR vom aktuellen Generator (Klasse value-wegc), dann A/B
# gegen v33-b01. Vorregistriert in evaluations/PREREG_v33_window.md par.6b (2026-09-26, VOR dem
# b02-Ergebnis und VOR jedem b03-Lauf).
#
# Aufruf mit der BASIS, die das b02-Ergebnis nach par.6b festlegt:
#     bash tools/night_v33_b03.sh <basis> <gegner>
#       b01 b01   # b02 z <= -1,96: aelterer Schwarm traegt
#       b02 b02   # b02 z >= +1,96: b03 muss gegen b02 spielen (Nachtrag par.6b)
#       b02 b01   # dazwischen
# Basis-Fenster: data/window_v33.txt (b01) bzw. data/window_v33_b02.txt (b02); die neuen
# Dateien werden HINTEN angehaengt, die Reihenfolge der alten bleibt (die Val-Ziehung haengt daran).
#
# Val-Menge: dieselbe wie bei b01. Die neuen Dateien heissen selfplay_v32-b01-value-wegc_* und
# passten auf den bisherigen Pool '^selfplay_v32-'; der Pool schliesst sie deshalb AUSDRUECKLICH
# aus, und --val-frac wird wie bei b02 aus der tatsaechlichen Fenstergroesse gerechnet. Das
# Skript bricht ab, wenn die Val-Menge nicht byte-gleich der von b01 ist.
#
# A/B mit festem Umfang 2 x 200 Paare: die SPRT-Schranken liegen so weit aussen, dass sie bei
# 200 Paaren nicht erreichbar sind (b02 Seed 1 war bei alpha=beta=0,001 nach 145 Paaren
# gestoppt, registriert waren 200).
#
# KEINE PIPE hinter langen Laeufen, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

BASE="${1:-}"
OPP="${2:-}"
case "$BASE" in
  b01) BASE_LIST=data/window_v33.txt ;;
  b02) BASE_LIST=data/window_v33_b02.txt ;;
  *) echo "ABBRUCH: Basis fehlt -- Aufruf 'bash tools/night_v33_b03.sh <b01|b02> <b01|b02>' (par.6b)"; exit 1 ;;
esac
case "$OPP" in
  b01|b02) ;;
  *) echo "ABBRUCH: Gegner fehlt -- zweites Argument b01|b02 (par.6b Nachtrag)"; exit 1 ;;
esac

ART=evaluations/artifacts
SEED=20260957
GEN=v32-b01
LOAD=v32-b01_brierbest
ARM=v33-b03
REF="v33-${OPP}"      # Gegner im A/B (par.6b Nachtrag)
REF_TRAIN=v33-b01   # Rezept-Referenz fuer den Manifest-Diff, unabhaengig vom Gegner
SPEC=models/v33_gating.spec.json
GEN_MODEL=models/alphazero_v32-b01_brierbest.onnx
GEN_SPEC=models/v32_generation.spec.json
CLASS="${GEN}-value-wegc"
GEN_SEED=20260945

for f in "$BASE_LIST" data/window_v33_val.txt "$SPEC" "$GEN_MODEL" "$GEN_SPEC" "models/alphazero_${LOAD}.pth"; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
if [ -f "models/alphazero_${REF}_brierbest.onnx" ]; then B="models/alphazero_${REF}_brierbest.onnx"
elif [ -f "models/alphazero_${REF}.onnx" ]; then B="models/alphazero_${REF}.onnx"
else echo "ABBRUCH: kein Modell $REF"; exit 1; fi

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
wait_for_free_cpu "v33-b03 Erzeugung"

echo "== v33-b03, Basis $BASE ($BASE_LIST), Gegner $REF   Start $(date +%F' '%H:%M:%S)"
echo ""
echo "== 1) Erzeugung $CLASS: 4.000 Partien, Sockel-Einstellung, value-only (par.6b) $(date +%F' '%H:%M:%S)"
N_BEFORE=$(ls data/ | grep -c "^selfplay_${CLASS}_" || true)
if [ "$N_BEFORE" -gt 0 ]; then
  echo "   $N_BEFORE Dateien $CLASS liegen schon -- Erzeugung UEBERSPRUNGEN (Fortsetzung eines Abbruchs?"
  echo "   Dann den Rest per Chunk-Seed nachziehen, nicht neu starten)."
else
  MOSAIC_STACK_DRAW_RESEARCH=1 python -X utf8 -u self_play.py --mode network --model "$GEN_MODEL" \
    --spec "$GEN_SPEC" --games 4000 --sims 100 --value-only --version "$CLASS" \
    --threads 11 --chunk 10 --per-file 10 --seed $GEN_SEED --return-order-random-p 0.81 \
    --tau-argmax-from-move 1 --deviate-prob 1.0 --start-slot-random-p 0.15
  echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c "^selfplay_${CLASS}_")"
fi
N_NEW=$(ls data/ | grep -c "^selfplay_${CLASS}_" || true)
[ "$N_NEW" -ge 395 ] || { echo "STOPP: nur $N_NEW Dateien $CLASS (Soll ~400)"; exit 2; }
python -X utf8 -u tools/corpus_sanity_check.py data --pattern "selfplay_${CLASS}_*.pkl" \
  --out "$ART/corpus_sanity_${CLASS}.json"

# --- Umgebung wie in night_v33_chain.sh / night_v33_b02.sh, bis auf den Val-Pool ---------
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v32-b01-(policy|value-tempc-nohull|value-excursion)_'
export MOSAIC_FEATURES_FROM_RUST=1
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v33.json
export MOSAIC_DATA_EXCLUDE='selfplay_v29-b11-probe_,selfplay_depth,selfplay_s4states,selfplay_tor2a'
unset MOSAIC_MOON_TARGET_SOURCE

echo ""
echo "== 2) Fensterliste data/window_v33_b03.txt = $BASE_LIST + $CLASS $(date +%H:%M:%S)"
python -X utf8 - "$BASE_LIST" "$CLASS" <<'PYEOF'
import os, sys
base_list, cls = sys.argv[1:3]
src = [l.rstrip("\n") for l in open(base_list, encoding="utf-8")]
files = [l for l in src if l and not l.startswith("#")]
new = sorted(f for f in os.listdir("data") if f.startswith(f"selfplay_{cls}_") and f.endswith(".pkl"))
assert not (set(new) & set(files)), "neue Klasse steht schon im Basis-Fenster"
keep = files + new
print(f"   Basis: {len(files)} Dateien, neu {cls}: {len(new)}, b03: {len(keep)}")
n_val = sum(1 for l in open("data/window_v33_val.txt", encoding="utf-8") if l.strip() and not l.startswith("#"))
vf = (n_val + 0.25) / len(keep)
assert round(len(keep) * vf) == n_val
open("data/window_v33_b03.valfrac", "w", encoding="utf-8").write(f"{vf:.8f}\n")
print(f"   Val-Dateien b01: {n_val} -> val_frac fuer b03: {vf:.8f}")
with open("data/window_v33_b03.txt", "w", encoding="utf-8", newline="\n") as fh:
    fh.write(f"# v33-b03 (PREREG_v33_window.md par.6b): {base_list} + {len(new)} Dateien {cls}\n")
    fh.write("\n".join(keep) + "\n")
PYEOF
[ $? -eq 0 ] || { echo "STOPP: Fensterliste b03 gescheitert"; exit 10; }
VAL_FRAC=$(tr -d '[:space:]' < data/window_v33_b03.valfrac)
[ -n "$VAL_FRAC" ] || { echo "STOPP: val_frac nicht berechnet"; exit 11; }

wait_for_free_cpu "v33-b03 Bloecke"
echo ""
echo "== 3) Bloecke der neuen Dateien (nur fehlende werden gebaut) $(date +%H:%M:%S)"
T0=$(date +%s)
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v33_b03.txt
echo "   Exit $? ($(date +%H:%M:%S)); Bloecke: $(( $(date +%s) - T0 )) s Wanduhr"

echo ""
echo "== 4) Aufteilung (val_frac $VAL_FRAC), Val-Menge MUSS gleich der von b01 sein $(date +%H:%M:%S)"
python -X utf8 tools/window_train_split.py --file-list data/window_v33_b03.txt --val-frac "$VAL_FRAC" \
  --val-pool "$MOSAIC_VAL_POOL" --encoder 2d --value-target-variant nortv \
  --train-list-out data/window_v33_b03_train.txt --val-list-out data/window_v33_b03_val.txt \
  > "$ART/v33_b03_split.txt"
cat "$ART/v33_b03_split.txt"
if ! cmp -s <(grep -v '^#' data/window_v33_val.txt | sort) <(grep -v '^#' data/window_v33_b03_val.txt | sort); then
  echo "STOPP: die Val-Menge von b03 weicht von der von b01 ab -- der Brier waere nicht vergleichbar"
  exit 12
fi
echo "   Val-Menge identisch mit b01 ($(grep -vc '^#' data/window_v33_b03_val.txt) Dateien)"
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v33_b03_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
CACHE="data/.cache_${KEY}.h5"

echo ""
echo "== 5) Monolith $(date +%H:%M:%S)"
T0=$(date +%s)
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v33_b03_train.txt \
  --merge-out "$CACHE"
echo "   Exit $? ($(date +%H:%M:%S)); Merge: $(( $(date +%s) - T0 )) s Wanduhr"
[ -f "$CACHE" ] || { echo "STOPP: Monolith fehlt"; exit 14; }
python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; print('   Stempel:',k); sys.exit(0 if k==sys.argv[2] else 16)" "$CACHE" "$KEY" \
  || { echo "STOPP: Stempel passt nicht zum Schluessel"; exit 16; }

# Rezept GLEICH b01 (night_v33_chain.sh Schritt 7) bis auf --name, --file-list, --cache-file,
# --val-frac und den Val-Pool (Umgebung). ABBRUCH? Fortsetzen mit demselben Aufruf plus --resume.
echo ""
echo "== 6) Training $ARM -- WARMSTART von $LOAD $(date +%F' '%H:%M:%S)"
python -X utf8 -u train.py --name "$ARM" --load "$LOAD" \
  --file-list data/window_v33_b03.txt --cache-file "$CACHE" \
  --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac "$VAL_FRAC" --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 0.0 \
  --moon-loss-weight 0.0 --opp-points-head \
  --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed $SEED
echo "   Training Exit $? ($(date +%H:%M:%S))"

echo ""
echo "== 6b) Manifest-Diff des Trainings gegen v33-b01 $(date +%H:%M:%S)"
python -X utf8 - "$ARM" "$REF_TRAIN" <<'PYEOF'
import glob, io, json, sys
arm, ref = sys.argv[1:3]
a = sorted(glob.glob(f"models/manifest_train_{arm}_*.json")); b = sorted(glob.glob(f"models/manifest_train_{ref}_*.json"))
if not a or not b:
    print("   Manifest fehlt -- Diff von Hand"); sys.exit(0)
na = json.load(io.open(a[-1], encoding="utf-8")).get("cli_args", {}) or {}
nb = json.load(io.open(b[-1], encoding="utf-8")).get("cli_args", {}) or {}
erwartet = {"name", "file_list", "cache_file", "val_frac", "val_pool"}
unerw = [k for k in sorted(set(na) | set(nb)) if na.get(k) != nb.get(k) and k not in erwartet]
for k in sorted(set(na) | set(nb)):
    if na.get(k) != nb.get(k):
        print(f"   cli_args.{k}: {ref}={nb.get(k)!r} -> {arm}={na.get(k)!r}{'' if k in erwartet else '  <== STOPP'}")
print(f"   Unerwartete Abweichungen: {len(unerw)} (erwartet hoechstens {sorted(erwartet)})")
PYEOF

if [ -f "models/alphazero_${ARM}_brierbest.onnx" ]; then A="models/alphazero_${ARM}_brierbest.onnx"
elif [ -f "models/alphazero_${ARM}.onnx" ]; then A="models/alphazero_${ARM}.onnx"
else echo "UEBERSPRUNGEN: kein Modell $ARM -- Training gescheitert?"; exit 15; fi

wait_for_free_cpu "A/B b03 gegen b01"
echo ""
echo "== 7) A/B $ARM gegen $REF, zwei Seeds a 200 Paaren, FESTER Umfang (par.6b) $(date +%F' '%H:%M:%S)"
echo "   A: $A   B: $B   Spec beidseits: $SPEC"
for S in 20261660 20261661; do
  OUT="$ART/ab_${ARM}_vs_${REF}_s${S}.json"
  echo ""
  echo "===== Seed $S $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$A" --spec-a "$SPEC" --model-b "$B" --spec-b "$SPEC" \
    --name-a "$ARM" --name-b "$REF" \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha 1e-12 --sprt-beta 1e-12 \
    --seed "$S" --threads 10 --log-games --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_${ARM}_vs_${REF}_s${S}.json"
done

echo ""
echo "== 8) Leseregel par.6b: Block-z ueber beide Seeds (A = b03) $(date +%H:%M:%S)"
python -X utf8 tools/gating_block_z.py "$ART"/ab_${ARM}_vs_${REF}_s2026166[01].json
echo ""
echo "########## v33-b03 FERTIG $(date +%F' '%H:%M:%S)"
echo "   z >= +1,96: mehr frischer Schwarm traegt (v34 bekommt die Klasse) | dazwischen: Volumen"
echo "   ist kein Hebel mehr, naechster Kandidat gezieltes Abzweigen | z <= -1,96: Diagnose."
