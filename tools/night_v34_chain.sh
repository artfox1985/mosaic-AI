#!/usr/bin/env bash
# v34-Kette, Grundarm v34-b01: Traeger-Manifest, Fenster (b04-Form), Bloecke, Monolith, Training
# WARM vom Generator v33-b01, Tor 1 gegen den Generator, Champion-Kante gegen v32-b01 (berichtet).
# Vorlage: tools/night_v33_chain.sh und der b04-Teil von tools/night_v33_b03_b04.sh (Git-Historie).
# Zuschnitt und Lesart: evaluations/PREREG_v34_window.md par.1 (Zuschnitt), par.2 (Tore), par.6
# (Rezept), par.9 (Erzeugung, Abnahmen, Tor 2a vom Nutzer als Self-Play-Effekt akzeptiert).
#
# WAS SICH GEGEN v33 AENDERT, und nur das:
#   1. Generator `v33-b01` (Klassen policy, value-wegc, value-excursion), G-1 `v32-b01`, G-2 `v31-b01`.
#   2. Fenster b04-Form: ganze v34-Erzeugung plus aus G-1/G-2 NUR die Policy-Traeger (135 + 45).
#   3. Seed 20260961, Val-Pool `^selfplay_v33-b01-`; Val-Menge 147 Dateien wie bei v33
#      (val_frac 147/Fenster), damit par.7a von targeted_branching je Klasse genug Dateien hat.
#   4. Warmstart von `v33-b01_brierbest`; Tor-1-Gegner ist der Generator `v33-b01`.
#   5. Champion-Kante gegen `v32-b01` (docs/generation_loop.md Schritt 7, Falle 1), berichtet.
#   6. Tor 1 und Champion-Kante auf `models/v33_gating.spec.json` BEIDSEITS, wie bei v33 (Runde 5
#      dort per Loeser; die Champion-Spec mit Netz in Runde 5 ist ein offener Nutzer-Entscheid).
#
# DAS TRAININGS-REZEPT IST UNVERAENDERT gegen models/manifest_train_v33-b01_20260926_090647.json.
#
# KEINE PIPE hinter langen Laeufen, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

ART=evaluations/artifacts
SEED=20260961
GEN=v33-b01                                                  # Generator, Namensstamm der neuen Klassen
G1=v32-b01                                                   # G-1 (die v33-Erzeugung)
G2=v31-b01                                                   # G-2 (die v32-Erzeugung)
GEN_MODEL=models/alphazero_v33-b01_brierbest.onnx            # Tor-1-Gegner
CHAMP=v32-b01
CHAMP_MODEL=models/alphazero_v32-b01_brierbest.onnx          # amtierender Champion
ARM=v34-b01
LOAD=v33-b01_brierbest
REF_TRAIN_MANIFEST=models/manifest_train_v33-b01_20260926_090647.json
N_VAL=147

export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v33-b01-'
export MOSAIC_FEATURES_FROM_RUST=1
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v34.json
export MOSAIC_DATA_EXCLUDE='selfplay_v29-b11-probe_,selfplay_depth,selfplay_s4states,selfplay_tor2a'
unset MOSAIC_MOON_TARGET_SOURCE

for f in "$GEN_MODEL" "$CHAMP_MODEL" "models/alphazero_${LOAD}.pth" "$REF_TRAIN_MANIFEST"; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
grep -q "FEATURE_FORMULA_VERSION" config.py || { echo "ABBRUCH: FEATURE_FORMULA_VERSION fehlt in config.py"; exit 2; }
python -X utf8 -c "import config,sys; sys.exit(0 if (config.INPUT_SIZE,config.NUM_ACTIONS)==(888,414) else 3)" \
  || { echo "ABBRUCH: config.py traegt nicht INPUT_SIZE 888 / NUM_ACTIONS 414"; exit 3; }
for f in "models/alphazero_${ARM}.pth" "models/alphazero_${ARM}_best.pth" "models/alphazero_${ARM}_brierbest.pth"; do
  [ -f "$f" ] && { echo "ABBRUCH: $f liegt schon (train.py wuerde ohnehin abbrechen)"; exit 4; }
done

SPEC=models/v33_gating.spec.json
[ -f "$SPEC" ] || { echo "ABBRUCH: Tor-1-Spec $SPEC fehlt"; exit 4; }
echo "== v34-KETTE ($ARM), Tor-1-Spec: $SPEC   Start $(date +%F' '%H:%M:%S)"

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
wait_for_free_cpu "v34-Kette"

echo ""
echo "== 1) Traeger-Manifest v34 (580 = 400 neu + 135 G-1 + 45 G-2) $(date +%H:%M:%S)"
python -X utf8 tools/generate_carrier_manifest.py \
  --pattern "selfplay_${G2}-policy_*.pkl" --n-files 45 --seed $SEED \
  --include-glob "selfplay_${GEN}-policy_*.pkl" \
  --pick "selfplay_${G1}-policy_*.pkl:135" \
  --out "$MOSAIC_CARRIER_MANIFEST"
python -X utf8 - "$MOSAIC_CARRIER_MANIFEST" "$GEN" "$G1" "$G2" <<'PYEOF'
import json, sys
name, gen, g1, g2 = sys.argv[1:5]
f = json.load(open(f"data/{name}", encoding="utf-8"))["policy_carrier_files"]
neu = [x for x in f if x.startswith(f"selfplay_{gen}-policy_")]
a = [x for x in f if x.startswith(f"selfplay_{g1}-policy_")]
b = [x for x in f if x.startswith(f"selfplay_{g2}-policy_")]
print(f"Manifest: {len(f)} Traeger = {len(neu)} neu + {len(a)} G-1 + {len(b)} G-2")
assert (len(f), len(neu), len(a), len(b)) == (580, 400, 135, 45), (len(f), len(neu), len(a), len(b))
PYEOF
[ $? -eq 0 ] || { echo "STOPP: Traeger-Manifest traegt nicht 580/400/135/45"; exit 10; }

echo ""
echo "== 2) Fensterliste data/window_v34.txt (b04-Form) $(date +%H:%M:%S)"
python -X utf8 - "$GEN" "$G1" "$G2" "$MOSAIC_CARRIER_MANIFEST" "$N_VAL" <<'PYEOF'
import glob, json, os, sys
gen, g1, g2, manifest, n_val = sys.argv[1:6]
def klasse(stamm):
    return sorted(os.path.basename(p) for p in glob.glob(f"data/selfplay_{stamm}_*.pkl"))
neu = {k: klasse(f"{gen}-{k}") for k in ("policy", "value-wegc", "value-excursion")}
carriers = json.load(open(f"data/{manifest}", encoding="utf-8"))["policy_carrier_files"]
old = sorted(c for c in carriers if c.startswith((f"selfplay_{g1}-", f"selfplay_{g2}-")))
print("neu je Klasse:", {k: len(v) for k, v in neu.items()}, "alte Traeger:", len(old))
assert all(len(v) == 400 for v in neu.values()), {k: len(v) for k, v in neu.items()}
assert len(old) == 180, len(old)
allf = neu["policy"] + neu["value-wegc"] + neu["value-excursion"] + old
assert all(os.path.exists(os.path.join("data", b)) for b in allf), "Datei fehlt"
assert len(allf) == len(set(allf)), "Doppelte im Fenster"
# Kein Nicht-Traeger aus G-1/G-2 (par.1: "Die Kette bricht ab, wenn das Fenster Nicht-Traeger enthaelt")
bad = [b for b in allf if b.startswith((f"selfplay_{g1}-", f"selfplay_{g2}-")) and b not in set(carriers)]
assert not bad, bad[:5]
with open("data/window_v34.txt", "w", encoding="utf-8", newline="\n") as fh:
    fh.write(f"# v34-Fenster (PREREG_v34_window.md par.1, b04-Form): 1.200 neu (Generator {gen}) + "
             f"{len(old)} alte Policy-Traeger aus {g1}/{g2}\n")
    fh.write("\n".join(allf) + "\n")
vf = int(n_val) / len(allf)
open("data/window_v34.valfrac", "w", encoding="utf-8").write(f"{vf:.8f}\n")
print(f"window_v34.txt: {len(allf)} Dateien; val_frac {vf:.8f} fuer {n_val} Val-Dateien")
PYEOF
[ $? -eq 0 ] || { echo "STOPP: Fensterbau gescheitert"; exit 11; }
VF=$(tr -d '[:space:]' < data/window_v34.valfrac)

echo ""
echo "== 3) Bloecke fuers Fenster $(date +%F' '%H:%M:%S)"
T0=$(date +%s)
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v34.txt
echo "   Exit $? ($(date +%H:%M:%S)); Bloecke: $(( $(date +%s) - T0 )) s Wanduhr"

echo ""
echo "== 4) Trainingsanteil, Fenster-Schluessel, Monolith $(date +%H:%M:%S)"
python -X utf8 tools/window_train_split.py --file-list data/window_v34.txt --val-frac "$VF" \
  --val-pool "$MOSAIC_VAL_POOL" --encoder 2d --value-target-variant nortv \
  --train-list-out data/window_v34_train.txt --val-list-out data/window_v34_val.txt \
  > "$ART/v34_split.txt"
cat "$ART/v34_split.txt"
NV=$(grep -vc '^#' data/window_v34_val.txt)
[ "$NV" = "$N_VAL" ] || { echo "STOPP: Val-Menge hat $NV statt $N_VAL Dateien"; exit 12; }
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v34_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
CACHE="data/.cache_${KEY}.h5"
T0=$(date +%s)
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v34_train.txt \
  --merge-out "$CACHE"
echo "   Exit $? ($(date +%H:%M:%S)); Merge: $(( $(date +%s) - T0 )) s Wanduhr"
[ -f "$CACHE" ] || { echo "STOPP: Monolith fehlt"; exit 14; }
python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; print('   Stempel:',k); sys.exit(0 if k==sys.argv[2] else 16)" "$CACHE" "$KEY" \
  || { echo "STOPP: Stempel passt nicht zum Schluessel"; exit 16; }
echo "##### FENSTER STEHT $(date +%F' '%H:%M:%S) -- Monolith $CACHE"

# ABBRUCH? Fortsetzen mit demselben Aufruf plus --resume (Fingerabdruck-Waechter).
echo ""
echo "== 5) Training $ARM -- WARMSTART von $LOAD $(date +%F' '%H:%M:%S)"
python -X utf8 -u train.py --name "$ARM" --load "$LOAD" \
  --file-list data/window_v34.txt --cache-file "$CACHE" \
  --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac "$VF" --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 0.0 \
  --moon-loss-weight 0.0 --opp-points-head \
  --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed $SEED
echo "   Training Exit $? ($(date +%H:%M:%S))"

echo ""
echo "== 5b) Manifest-Diff des TRAININGS gegen das v33-b01-Rezept $(date +%H:%M:%S)"
python -X utf8 - "$ARM" "$REF_TRAIN_MANIFEST" <<'PYEOF'
import glob, io, json, sys
arm, ref_path = sys.argv[1], sys.argv[2]
ps = sorted(glob.glob(f"models/manifest_train_{arm}_*.json"))
if not ps:
    print("   kein Trainings-Manifest gefunden -- Diff von Hand"); sys.exit(0)
neu = json.load(io.open(ps[-1], encoding="utf-8")).get("cli_args", {}) or {}
ref = json.load(io.open(ref_path, encoding="utf-8")).get("cli_args", {}) or {}
erwartet = {"load", "name", "file_list", "cache_file", "seed", "val_pool", "val_frac"}
unerwartet = []
for k in sorted(set(ref) | set(neu)):
    if ref.get(k) != neu.get(k):
        mark = "" if k in erwartet else "  <== STOPP"
        if k not in erwartet:
            unerwartet.append(k)
        print(f"   cli_args.{k}: v33-b01={ref.get(k)!r} -> {arm}={neu.get(k)!r}{mark}")
print(f"   Unerwartete Abweichungen: {len(unerwartet)} (erwartet sind genau {sorted(erwartet)})")
PYEOF

if [ -f "models/alphazero_${ARM}_brierbest.onnx" ]; then
  A="models/alphazero_${ARM}_brierbest.onnx"
elif [ -f "models/alphazero_${ARM}.onnx" ]; then
  A="models/alphazero_${ARM}.onnx"
  echo "HINWEIS: kein _brierbest -- beste Epoche war die letzte, finales Modell wird genommen"
else
  echo "UEBERSPRUNGEN: kein Modell $ARM -- Training gescheitert?"; exit 15
fi
echo "##### TRAINING DURCH $(date +%F' '%H:%M:%S) -- Modell $A"

gate() {  # $1 Gegnername, $2 Gegnermodell, $3 Seed, $4 Praefix der Ausgabe
  local OUT="$ART/${4}_${ARM}_vs_${1}_s${3}.json"
  echo ""
  echo "===== $ARM gegen $1, Seed $3 $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$A" --spec-a "$SPEC" --model-b "$2" --spec-b "$SPEC" \
    --name-a "$ARM" --name-b "$1" \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$3" --threads 10 --log-games --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_${ARM}_vs_${1}_s${3}.json"
}

wait_for_free_cpu "Tor 1"
echo ""
echo "== 6) Tor 1: $ARM gegen den Generator $GEN, zwei Seeds a 200 Paaren, Stufenregel $(date +%F' '%H:%M:%S)"
for S in 20261600 20261601; do
  gate "$GEN" "$GEN_MODEL" "$S" gating
done
python -X utf8 tools/gating_block_z.py "$ART/gating_${ARM}_vs_${GEN}_s20261600.json" "$ART/gating_${ARM}_vs_${GEN}_s20261601.json"
N_SIG=$(python -X utf8 tools/gating_block_z.py --json \
  "$ART/gating_${ARM}_vs_${GEN}_s20261600.json" "$ART/gating_${ARM}_vs_${GEN}_s20261601.json" \
  | python -c "import sys,json; d=json.load(sys.stdin); print(sum(r['z'] >= 1.96 for r in d['per_seed']))")
echo "   Seeds einzeln >= +1,96: ${N_SIG:-?} von 2"
if [ "$N_SIG" = "1" ]; then
  echo "   -> Widerspruch: dritter Seed 20261602 (Stufenregel, par.2)"
  gate "$GEN" "$GEN_MODEL" 20261602 gating
  python -X utf8 tools/gating_block_z.py "$ART"/gating_${ARM}_vs_${GEN}_s2026160[012].json
elif [ -z "$N_SIG" ]; then
  echo "   STOPP: Block-z nicht berechenbar -- Stufenregel von Hand anwenden"
fi

echo ""
echo "== 7) Champion-Kante: $ARM gegen den Champion $CHAMP (berichtet, docs/generation_loop.md Schritt 7) $(date +%F' '%H:%M:%S)"
for S in 20261600 20261601; do
  gate "$CHAMP" "$CHAMP_MODEL" "$S" champion
done
python -X utf8 tools/gating_block_z.py "$ART/champion_${ARM}_vs_${CHAMP}_s20261600.json" "$ART/champion_${ARM}_vs_${CHAMP}_s20261601.json"

echo ""
echo "########## v34-KETTE FERTIG $(date +%F' '%H:%M:%S)"
echo "   Faellig danach: Verdikt Tor 1 (par.2), Tor 2b, sechs Standard-Kennzahlen, Elo-Register,"
echo "   Offline-Pruefung par.7a (targeted_branching), Laufzeiten; Promotion NUR nach /mosaic-champion-promotion."
