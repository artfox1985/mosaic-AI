#!/usr/bin/env bash
# v33-b03 (PREREG_v33_window.md par.6b) und v33-b04 (par.6c) in EINER Kette, GPU und CPU parallel
# (docs/working_rules.md "GPU und CPU duerfen parallel laufen": ein Training plus EIN CPU-Auftrag).
#
#   Phase 1  (CPU, exklusiv)     b04: Fenster, Aufteilung, Monolith
#   Phase 2  (CPU || GPU)        b03-Erzeugung value-wegc (10 Threads)  ||  b04-Training
#   Phase 3  (CPU)               b03: Sanity, Fenster, Bloecke, Aufteilung, Monolith
#   Phase 4  (GPU || CPU)        b03-Training  ||  b04-A/B gegen b02
#   Phase 5  (CPU, exklusiv)     b03-A/B gegen den Gegner aus par.6b
#   Phase 6                      Block-z beider Arme
#
# Aufruf (Basis und Gegner von b03 nach dem b02-Verdikt, par.6b Nachtrag):
#     bash tools/night_v33_b03_b04.sh <basis b01|b02> <gegner b01|b02>
#
# Laufzeiten der Phasen 2 und 4 sind UNTER NEBENLAST (Pflichtmarkierung working_rules) und keine
# Planungsgroessen. Die beiden Trainings laufen im Hintergrund dieses Skripts; ihre Ausgabe geht
# nach logs/<arm>_train.log, damit sie sich nicht mit dem Vordergrundlauf mischt -- Fortschritt
# dort mit `tail logs/v33-b04_train.log` ablesen.
#
# KEINE PIPE hinter langen Laeufen; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
mkdir -p logs

BASE="${1:-}"
OPP="${2:-}"
case "$BASE" in
  b01) BASE_LIST=data/window_v33.txt ;;
  b02) BASE_LIST=data/window_v33_b02.txt ;;
  *) echo "ABBRUCH: Aufruf 'bash tools/night_v33_b03_b04.sh <b01|b02> <b01|b02>' (par.6b)"; exit 1 ;;
esac
case "$OPP" in
  b01|b02) ;;
  *) echo "ABBRUCH: Gegner fehlt -- zweites Argument b01|b02 (par.6b Nachtrag)"; exit 1 ;;
esac

ART=evaluations/artifacts
SEED=20260957
LOAD=v32-b01_brierbest
SPEC=models/v33_gating.spec.json
GEN_MODEL=models/alphazero_v32-b01_brierbest.onnx
GEN_SPEC=models/v32_generation.spec.json
CLASS="v32-b01-value-wegc"
GEN_SEED=20260945
REF_TRAIN=v33-b01
B03_REF="v33-${OPP}"
B04_REF=v33-b02

for f in "$BASE_LIST" data/window_v33_b02.txt data/window_v33_val.txt data/policy_carrier_manifest_v33.json \
         "$SPEC" "$GEN_MODEL" "$GEN_SPEC" "models/alphazero_${LOAD}.pth"; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done

model_of() {  # bevorzugt _brierbest.onnx, sonst .onnx; leer, wenn keins da ist
  if [ -f "models/alphazero_$1_brierbest.onnx" ]; then echo "models/alphazero_$1_brierbest.onnx"
  elif [ -f "models/alphazero_$1.onnx" ]; then echo "models/alphazero_$1.onnx"; fi
}

# Umgebung wie night_v33_chain.sh / night_v33_b02.sh; der Val-Pool ist je Arm gesetzt.
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_FEATURES_FROM_RUST=1
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v33.json
export MOSAIC_DATA_EXCLUDE='selfplay_v29-b11-probe_,selfplay_depth,selfplay_s4states,selfplay_tor2a'
unset MOSAIC_MOON_TARGET_SOURCE
POOL_B04='^selfplay_v32-'
POOL_B03='^selfplay_v32-b01-(policy|value-tempc-nohull|value-excursion)_'

# Fenster -> Aufteilung (Val-Menge MUSS gleich b01 sein) -> Monolith. Setzt CACHE_OUT.
split_and_merge() {  # $1 Arm (z.B. v33-b04), $2 Fensterliste, $3 val_frac, $4 Val-Pool
  local arm="$1" list="$2" vf="$3" pool="$4" tag="${1#v33-}"
  echo "   Aufteilung $arm (val_frac $vf)"
  python -X utf8 tools/window_train_split.py --file-list "$list" --val-frac "$vf" \
    --val-pool "$pool" --encoder 2d --value-target-variant nortv \
    --train-list-out "data/window_v33_${tag}_train.txt" --val-list-out "data/window_v33_${tag}_val.txt" \
    > "$ART/v33_${tag}_split.txt"
  cat "$ART/v33_${tag}_split.txt"
  if ! cmp -s <(grep -v '^#' data/window_v33_val.txt | sort) <(grep -v '^#' "data/window_v33_${tag}_val.txt" | sort); then
    echo "STOPP: die Val-Menge von $arm weicht von der von b01 ab"; return 12
  fi
  echo "   Val-Menge identisch mit b01 ($(grep -vc '^#' "data/window_v33_${tag}_val.txt") Dateien)"
  local key
  key=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v33_${tag}_split.txt" | awk '{print $NF}')
  [ -n "$key" ] || { echo "STOPP: kein Schluessel"; return 13; }
  CACHE_OUT="data/.cache_${key}.h5"
  local t0; t0=$(date +%s)
  python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
    --value-target-variant nortv --workers 6 --file-list "data/window_v33_${tag}_train.txt" \
    --merge-out "$CACHE_OUT"
  echo "   Merge Exit $? ($(date +%H:%M:%S)); $(( $(date +%s) - t0 )) s Wanduhr"
  [ -f "$CACHE_OUT" ] || { echo "STOPP: Monolith fehlt"; return 14; }
  python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; print('   Stempel:',k); sys.exit(0 if k==sys.argv[2] else 16)" "$CACHE_OUT" "$key" \
    || { echo "STOPP: Stempel passt nicht zum Schluessel"; return 16; }
}

# Rezept GLEICH b01 (night_v33_chain.sh Schritt 7) bis auf --name, --file-list, --cache-file,
# --val-frac. ABBRUCH? Fortsetzen mit demselben Aufruf plus --resume.
train_arm() {  # $1 Arm, $2 Fensterliste, $3 Monolith, $4 val_frac, $5 Val-Pool
  MOSAIC_VAL_POOL="$5" python -X utf8 -u train.py --name "$1" --load "$LOAD" \
    --file-list "$2" --cache-file "$3" \
    --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
    --val-frac "$4" --encoder 2d --value-head wdl --value-target-variant nortv \
    --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 0.0 \
    --moon-loss-weight 0.0 --opp-points-head \
    --destretch-a 0.0051 --destretch-b 1.9269 \
    --select-by-brier --fast-loader --seed $SEED
}

manifest_diff() {  # $1 Arm
  python -X utf8 - "$1" "$REF_TRAIN" <<'PYEOF'
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
print(f"   {arm}: unerwartete Abweichungen {len(unerw)} (erwartet hoechstens {sorted(erwartet)})")
PYEOF
}

ab_run() {  # $1 Arm A, $2 Arm B, $3.. Seeds; fester Umfang 200 Paare
  local arm="$1" ref="$2"; shift 2
  local ma mb; ma=$(model_of "$arm"); mb=$(model_of "$ref")
  [ -n "$ma" ] && [ -n "$mb" ] || { echo "UEBERSPRUNGEN: Modell fehlt ($arm: '$ma', $ref: '$mb')"; return 15; }
  echo "   A: $ma   B: $mb   Spec beidseits: $SPEC"
  for S in "$@"; do
    local out="$ART/ab_${arm}_vs_${ref}_s${S}.json"
    echo ""
    echo "===== $arm gegen $ref, Seed $S $(date +%H:%M:%S)"
    python -X utf8 -u tools/paired_gating.py \
      --model-a "$ma" --spec-a "$SPEC" --model-b "$mb" --spec-b "$SPEC" \
      --name-a "$arm" --name-b "$ref" \
      --sims-a 400 --sims-b 400 --c-puct 1.5 \
      --block-size 5 --max-pairs 200 --sprt-alpha 1e-12 --sprt-beta 1e-12 \
      --seed "$S" --threads 10 --log-games --no-promote-winner --out "$out"
    echo "   Exit $? ($(date +%H:%M:%S))"
    python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$out"
    python -X utf8 -u tools/plate_points_from_arena.py "$out" --block 5 \
      --out "$ART/plate_points_${arm}_vs_${ref}_s${S}.json"
  done
}

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
wait_for_free_cpu "v33-b03/b04"
echo "== v33-b03 (Basis $BASE, Gegner $B03_REF) und v33-b04 (Gegner $B04_REF)   Start $(date +%F' '%H:%M:%S)"

# ---------------------------------------------------------------------------------------------
echo ""
echo "== 1) b04: Fenster = window_v33_b02 minus die policy-maskierten alten Sockel-Dateien (par.6c) $(date +%H:%M:%S)"
python -X utf8 - <<'PYEOF'
import json, sys
src = [l.rstrip("\n") for l in open("data/window_v33_b02.txt", encoding="utf-8")]
files = [l for l in src if l and not l.startswith("#")]
carriers = set(json.load(open("data/policy_carrier_manifest_v33.json", encoding="utf-8"))["policy_carrier_files"])
old = [f for f in files if f.startswith("selfplay_v31-b01-policy_") or f.startswith("selfplay_v30-b02-policy_")]
drop = [f for f in old if f not in carriers]
kept_old = [f for f in old if f in carriers]
g1 = sum(1 for f in drop if f.startswith("selfplay_v31-b01-")); g2 = len(drop) - g1
print(f"   b02-Fenster {len(files)}, alte Sockel-Dateien {len(old)}, entfernt {len(drop)} (G-1 {g1}, G-2 {g2}), alte Traeger bleiben {len(kept_old)}")
assert (len(drop), g1, g2, len(kept_old)) == (620, 265, 355, 180), (len(drop), g1, g2, len(kept_old))
keep = [f for f in files if f not in set(drop)]
n_val = sum(1 for l in open("data/window_v33_val.txt", encoding="utf-8") if l.strip() and not l.startswith("#"))
vf = (n_val + 0.25) / len(keep)
assert round(len(keep) * vf) == n_val
open("data/window_v33_b04.valfrac", "w", encoding="utf-8").write(f"{vf:.8f}\n")
print(f"   b04: {len(keep)} Dateien, Val-Dateien b01: {n_val} -> val_frac {vf:.8f}")
with open("data/window_v33_b04.txt", "w", encoding="utf-8", newline="\n") as fh:
    fh.write("# v33-b04 (PREREG_v33_window.md par.6c): window_v33_b02 ohne policy-maskierte alte Sockel-Dateien\n")
    fh.write("\n".join(keep) + "\n")
PYEOF
[ $? -eq 0 ] || { echo "STOPP: Fensterliste b04 gescheitert"; exit 20; }
VF_B04=$(tr -d '[:space:]' < data/window_v33_b04.valfrac)
split_and_merge v33-b04 data/window_v33_b04.txt "$VF_B04" "$POOL_B04" || exit $?
CACHE_B04="$CACHE_OUT"

# ---------------------------------------------------------------------------------------------
echo ""
echo "== 2) PARALLEL: b04-Training (GPU, Hintergrund) || b03-Erzeugung (CPU, 10 Threads) $(date +%F' '%H:%M:%S)"
echo "   b04-Training -> logs/v33-b04_train.log (UNTER NEBENLAST)"
( train_arm v33-b04 data/window_v33_b04.txt "$CACHE_B04" "$VF_B04" "$POOL_B04"; echo "   b04-Training Exit $? ($(date +%H:%M:%S))" ) \
  > logs/v33-b04_train.log 2>&1 &
PID_B04=$!

N_BEFORE=$(ls data/ | grep -c "^selfplay_${CLASS}_" || true)
if [ "$N_BEFORE" -gt 0 ]; then
  echo "   $N_BEFORE Dateien $CLASS liegen schon -- Erzeugung UEBERSPRUNGEN (Rest per Chunk-Seed nachziehen)."
else
  MOSAIC_STACK_DRAW_RESEARCH=1 python -X utf8 -u self_play.py --mode network --model "$GEN_MODEL" \
    --spec "$GEN_SPEC" --games 4000 --sims 100 --value-only --version "$CLASS" \
    --threads 10 --chunk 10 --per-file 10 --seed $GEN_SEED --return-order-random-p 0.81 \
    --tau-argmax-from-move 1 --deviate-prob 1.0 --start-slot-random-p 0.15
  echo "   Erzeugung Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c "^selfplay_${CLASS}_") (UNTER NEBENLAST)"
fi
N_NEW=$(ls data/ | grep -c "^selfplay_${CLASS}_" || true)
[ "$N_NEW" -ge 395 ] || { echo "STOPP: nur $N_NEW Dateien $CLASS (Soll ~400); b04-Training laeuft weiter (PID $PID_B04)"; exit 2; }
echo "   warte auf das b04-Training (PID $PID_B04) $(date +%H:%M:%S)"
wait "$PID_B04"
tail -3 logs/v33-b04_train.log
manifest_diff v33-b04

# ---------------------------------------------------------------------------------------------
echo ""
echo "== 3) b03: Sanity, Fenster $BASE_LIST + $CLASS, Bloecke, Aufteilung, Monolith $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/corpus_sanity_check.py data --pattern "selfplay_${CLASS}_*.pkl" \
  --out "$ART/corpus_sanity_${CLASS}.json"
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
VF_B03=$(tr -d '[:space:]' < data/window_v33_b03.valfrac)
T0=$(date +%s)
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v33_b03.txt
echo "   Bloecke Exit $? ($(date +%H:%M:%S)); $(( $(date +%s) - T0 )) s Wanduhr"
split_and_merge v33-b03 data/window_v33_b03.txt "$VF_B03" "$POOL_B03" || exit $?
CACHE_B03="$CACHE_OUT"

# ---------------------------------------------------------------------------------------------
echo ""
echo "== 4) PARALLEL: b03-Training (GPU, Hintergrund) || b04-A/B gegen b02 (CPU) $(date +%F' '%H:%M:%S)"
echo "   b03-Training -> logs/v33-b03_train.log (UNTER NEBENLAST)"
( train_arm v33-b03 data/window_v33_b03.txt "$CACHE_B03" "$VF_B03" "$POOL_B03"; echo "   b03-Training Exit $? ($(date +%H:%M:%S))" ) \
  > logs/v33-b03_train.log 2>&1 &
PID_B03=$!
ab_run v33-b04 "$B04_REF" 20261680 20261681
echo "   warte auf das b03-Training (PID $PID_B03) $(date +%H:%M:%S)"
wait "$PID_B03"
tail -3 logs/v33-b03_train.log
manifest_diff v33-b03

# ---------------------------------------------------------------------------------------------
echo ""
echo "== 5) b03-A/B gegen $B03_REF (exklusiv) $(date +%F' '%H:%M:%S)"
ab_run v33-b03 "$B03_REF" 20261660 20261661

echo ""
echo "== 6) Leseregeln $(date +%H:%M:%S)"
echo "-- b04 gegen b02 (par.6c; A = b04):"
python -X utf8 tools/gating_block_z.py "$ART"/ab_v33-b04_vs_${B04_REF}_s2026168[01].json
echo "-- b03 gegen $B03_REF (par.6b; A = b03):"
python -X utf8 tools/gating_block_z.py "$ART"/ab_v33-b03_vs_${B03_REF}_s2026166[01].json
echo ""
echo "########## v33-b03/b04 FERTIG $(date +%F' '%H:%M:%S)"
echo "   b04 z >= +1,96: altes Value-Material schadet | <= -1,96: es traegt | dazwischen: kein Beitrag"
echo "   b03: Leseregel par.6b je nach Gegner (Nachtrag)"
