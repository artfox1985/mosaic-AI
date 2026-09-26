#!/usr/bin/env bash
# v33-b02: nur der Schwarm des Generators im Fenster, dann A/B gegen v33-b01.
# Vorregistriert in evaluations/PREREG_v33_window.md par.6a (2026-09-25, VOR jedem Lauf).
#
# Laeuft IM ANSCHLUSS an tools/night_v33_chain.sh und setzt deren Ergebnisse voraus:
# data/window_v33.txt, data/window_v33_val.txt, die Bloecke aller Fensterdateien und das
# Modell v33-b01. Der EINE Unterschied zu b01: das Fenster verliert den Schwarm aus G-1
# (v31-b01-value-*) und G-2 (die 145 Ausflug-Dateien von v30-b02); Soll 2.001 Dateien.
# Rezept, Warmstart, Trainings-Seed, Carrier-Manifest und Val-Menge sind GLEICH -- die
# Val-Menge ueber ein --val-frac, das Schritt 1 aus der TATSAECHLICHEN b01-Val-Liste und der
# tatsaechlichen b02-Fenstergroesse rechnet (n_val gleich), und denselben Pool; das Skript bricht
# ab, wenn sie nicht byte-gleich ist.
#
# KEINE PIPE hinter langen Laeufen, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

ART=evaluations/artifacts
SEED=20260957
GEN=v32-b01
G1=v31-b01
G2=v30-b02
LOAD=v32-b01_brierbest
ARM=v33-b02
REF=v33-b01
SPEC=models/v33_gating.spec.json

# --- Umgebung wie in night_v33_chain.sh (gleiche Werte, gleiche Reihenfolge) ------------
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v32-'
export MOSAIC_FEATURES_FROM_RUST=1
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v33.json
export MOSAIC_DATA_EXCLUDE='selfplay_v29-b11-probe_,selfplay_depth,selfplay_s4states,selfplay_tor2a'
unset MOSAIC_MOON_TARGET_SOURCE

for f in data/window_v33.txt data/window_v33_val.txt "$SPEC" "models/alphazero_${LOAD}.pth"; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt -- laeuft die v33-Kette schon durch?"; exit 1; }
done
if [ -f "models/alphazero_${REF}_brierbest.onnx" ]; then B="models/alphazero_${REF}_brierbest.onnx"
elif [ -f "models/alphazero_${REF}.onnx" ]; then B="models/alphazero_${REF}.onnx"
else echo "ABBRUCH: kein Modell $REF"; exit 1; fi

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
wait_for_free_cpu "v33-b02"

echo ""
echo "== 1) Fensterliste data/window_v33_b02.txt aus window_v33.txt $(date +%F' '%H:%M:%S)"
python -X utf8 - "$G1" "$G2" <<'PYEOF'
import sys
g1, g2 = sys.argv[1:3]
src = [l.rstrip("\n") for l in open("data/window_v33.txt", encoding="utf-8")]
head = [l for l in src if l.startswith("#")]
files = [l for l in src if l and not l.startswith("#")]
drop = [f for f in files if f.startswith(f"selfplay_{g1}-value-") or f.startswith(f"selfplay_{g2}-value-")]
keep = [f for f in files if f not in set(drop)]
print(f"   Fenster b01: {len(files)}, entfernt (Schwarm G-1/G-2): {len(drop)}, b02: {len(keep)}")
# Fest ist nur der ENTFERNTE Teil (G-1: tempc 400 + Ausflug 401, G-2: 145 Ausflug); die neue
# Ausflug-Klasse darf wie in der Kette zwischen 395 und 410 liegen, also auch das Fenster.
assert len(drop) == 946, (len(files), len(drop), len(keep))
assert len(keep) == len(files) - 946 and 1996 <= len(keep) <= 2011, (len(files), len(keep))
# Reihenfolge der verbleibenden Dateien bleibt erhalten -- die Val-Ziehung haengt daran.
# val_frac so, dass round(N * val_frac) die n_val von b01 trifft (window_train_split.py Z.78:
# n_val = max(1, round(n * val_frac))); +0,25 haelt round() von der .5-Kante fern.
n_val = sum(1 for l in open("data/window_v33_val.txt", encoding="utf-8") if l.strip() and not l.startswith("#"))
vf = (n_val + 0.25) / len(keep)
assert round(len(keep) * vf) == n_val
open("data/window_v33_b02.valfrac", "w", encoding="utf-8").write(f"{vf:.8f}\n")
print(f"   Val-Dateien b01: {n_val} -> val_frac fuer b02: {vf:.8f}")
with open("data/window_v33_b02.txt", "w", encoding="utf-8", newline="\n") as fh:
    fh.write("# v33-b02 (PREREG_v33_window.md par.6a): window_v33.txt ohne Schwarm aus G-1 und G-2\n")
    fh.write("\n".join(keep) + "\n")
PYEOF
[ $? -eq 0 ] || { echo "STOPP: Fensterliste b02 gescheitert"; exit 10; }
VAL_FRAC=$(tr -d '[:space:]' < data/window_v33_b02.valfrac)
[ -n "$VAL_FRAC" ] || { echo "STOPP: val_frac nicht berechnet"; exit 11; }

echo ""
echo "== 2) Aufteilung (val_frac $VAL_FRAC), Val-Menge MUSS gleich der von b01 sein $(date +%H:%M:%S)"
python -X utf8 tools/window_train_split.py --file-list data/window_v33_b02.txt --val-frac "$VAL_FRAC" \
  --val-pool "$MOSAIC_VAL_POOL" --encoder 2d --value-target-variant nortv \
  --train-list-out data/window_v33_b02_train.txt --val-list-out data/window_v33_b02_val.txt \
  > "$ART/v33_b02_split.txt"
cat "$ART/v33_b02_split.txt"
if ! cmp -s <(grep -v '^#' data/window_v33_val.txt | sort) <(grep -v '^#' data/window_v33_b02_val.txt | sort); then
  echo "STOPP: die Val-Menge von b02 weicht von der von b01 ab -- der Brier waere nicht vergleichbar"
  exit 12
fi
echo "   Val-Menge identisch mit b01 ($(grep -vc '^#' data/window_v33_b02_val.txt) Dateien)"
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v33_b02_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
CACHE="data/.cache_${KEY}.h5"

echo ""
echo "== 3) Monolith aus den vorhandenen Bloecken $(date +%H:%M:%S)"
T0=$(date +%s)
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v33_b02_train.txt \
  --merge-out "$CACHE"
echo "   Exit $? ($(date +%H:%M:%S)); Merge: $(( $(date +%s) - T0 )) s Wanduhr"
[ -f "$CACHE" ] || { echo "STOPP: Monolith fehlt"; exit 14; }
python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; print('   Stempel:',k); sys.exit(0 if k==sys.argv[2] else 16)" "$CACHE" "$KEY" \
  || { echo "STOPP: Stempel passt nicht zum Schluessel"; exit 16; }

# Rezept GLEICH b01 (night_v33_chain.sh Schritt 7) bis auf --name, --file-list, --cache-file
# und --val-frac. ABBRUCH? Fortsetzen mit demselben Aufruf plus --resume.
echo ""
echo "== 4) Training $ARM -- WARMSTART von $LOAD $(date +%F' '%H:%M:%S)"
python -X utf8 -u train.py --name "$ARM" --load "$LOAD" \
  --file-list data/window_v33_b02.txt --cache-file "$CACHE" \
  --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac "$VAL_FRAC" --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 0.0 \
  --moon-loss-weight 0.0 --opp-points-head \
  --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed $SEED
echo "   Training Exit $? ($(date +%H:%M:%S))"

echo ""
echo "== 4b) Manifest-Diff des Trainings gegen v33-b01 $(date +%H:%M:%S)"
python -X utf8 - "$ARM" "$REF" <<'PYEOF'
import glob, io, json, sys
arm, ref = sys.argv[1:3]
a = sorted(glob.glob(f"models/manifest_train_{arm}_*.json")); b = sorted(glob.glob(f"models/manifest_train_{ref}_*.json"))
if not a or not b:
    print("   Manifest fehlt -- Diff von Hand"); sys.exit(0)
na = json.load(io.open(a[-1], encoding="utf-8")).get("cli_args", {}) or {}
nb = json.load(io.open(b[-1], encoding="utf-8")).get("cli_args", {}) or {}
erwartet = {"name", "file_list", "cache_file", "val_frac"}
unerw = [k for k in sorted(set(na) | set(nb)) if na.get(k) != nb.get(k) and k not in erwartet]
for k in sorted(set(na) | set(nb)):
    if na.get(k) != nb.get(k):
        print(f"   cli_args.{k}: {ref}={nb.get(k)!r} -> {arm}={na.get(k)!r}{'' if k in erwartet else '  <== STOPP'}")
print(f"   Unerwartete Abweichungen: {len(unerw)} (erwartet genau {sorted(erwartet)})")
PYEOF

if [ -f "models/alphazero_${ARM}_brierbest.onnx" ]; then A="models/alphazero_${ARM}_brierbest.onnx"
elif [ -f "models/alphazero_${ARM}.onnx" ]; then A="models/alphazero_${ARM}.onnx"
else echo "UEBERSPRUNGEN: kein Modell $ARM -- Training gescheitert?"; exit 15; fi

wait_for_free_cpu "A/B b02 gegen b01"
echo ""
echo "== 5) A/B $ARM gegen $REF, zwei Seeds a 200 Paaren (par.6a) $(date +%F' '%H:%M:%S)"
echo "   A: $A   B: $B   Spec beidseits: $SPEC"
for S in 20261650 20261651; do
  OUT="$ART/ab_${ARM}_vs_${REF}_s${S}.json"
  echo ""
  echo "===== Seed $S $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$A" --spec-a "$SPEC" --model-b "$B" --spec-b "$SPEC" \
    --name-a "$ARM" --name-b "$REF" \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$S" --threads 10 --log-games --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_${ARM}_vs_${REF}_s${S}.json"
done

echo ""
echo "== 6) Leseregel par.6a: Block-z ueber beide Seeds (A = b02) $(date +%H:%M:%S)"
python -X utf8 tools/gating_block_z.py "$ART"/ab_${ARM}_vs_${REF}_s2026165[01].json
echo ""
echo "########## v33-b02 FERTIG $(date +%F' '%H:%M:%S)"
echo "   z <= -1,96: aelterer Schwarm traegt | z >= +1,96: er schadet | dazwischen: kein Beitrag,"
echo "   b02 ist das billigere Fenster (Nutzer-Entscheid fuer v34). Dazu Val-Brier beider Arme."
