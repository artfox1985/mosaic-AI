#!/usr/bin/env bash
# v35-Kette, Arm v35-b02 (EINE Datei fuer die ganze Nacht): Erzeugung des kompletten Fensters
# @400 Modus 2 (tools/v35_b02_generate.sh), dann Traeger-Manifest, Fenster (fuenf Klassen des
# Generators v34-b01, alle @400 Modus 2), Bloecke, Monolith mit Wertmaske der Wuerfelphase,
# Training WARM von v34-b01_brierbest, Tor 1 gegen den Generator (= amtierender Champion, Tor 1
# IST die Champion-Kante).
# Registrierung (verbindlich): evaluations/PREREG_v35_window.md par.12 (Nutzer 2026-10-04 spaet:
# "b02 voll"; Grundlage par.11b und par.11d). Vorlage: tools/night_v35_chain.sh (v35-b01).
#
# WAS SICH GEGEN v35-b01 AENDERT, und nur das:
#   0. Vorn: wait_for_free_cpu, dann bash tools/v35_b02_generate.sh (STOPP bei Exit != 0). Der
#      Export-Block der Trainings-Umgebung steht DESHALB erst NACH der Erzeugung: self_play.py
#      schreibt alle MOSAIC_* des Elternprozesses ins Manifest (selfplay_manifest.py:129), die
#      Trainings-Variablen stuenden sonst im mosaic_env der Erzeugungs-Manifeste. Zusaetzliche
#      Vorpruefung: genau 100 Dateien selfplay_v34-b01-policy_*.pkl (die vorhandene @400-Haelfte),
#      sonst Abbruch VOR 14 h Erzeugung.
#   1. ARM=v35-b02; Abbruch, wenn models/alphazero_v35-b02*.pth oder
#      data/policy_carrier_manifest_v35_b02.json schon liegen.
#   2. Traeger-Manifest data/policy_carrier_manifest_v35_b02.json: 400 = policy 100 (--pattern,
#      --n-files 100 = alle) + policy-s400 100 + policy-dice-v2-r1-s400 200 (EIN --include-glob
#      "policy-*s400_", vollstaendig; eine Ueberschneidung mit der Stichprobe bricht im Werkzeug ab,
#      tools/generate_carrier_manifest.py:126-129). MOSAIC_CARRIER_MANIFEST entsprechend.
#   3. Fenster: policy 100 (vorhanden), policy-s400 100, policy-dice-v2-r1-s400 200,
#      value-deviate-s400 400, value-excursion-s400 400 = 1.200; die @100-Klassen sind NICHT drin.
#      Dateinamen data/window_v35_b02.txt, _train.txt, _val.txt, .valfrac,
#      evaluations/artifacts/v35_b02_split.txt.
#   4. Manifest-Diff 5b erwartet das Traeger-Manifest v35_b02 in mosaic_env.
# UNVERAENDERT gegen b01: MOSAIC_DATA_EXCLUDE, MOSAIC_VAL_POOL '^selfplay_v34-b01-' (alle
# Fenster-Dateien tragen das Praefix), Wertmaske, Val 120, Seed 20260965 (alle Arme einer
# Generation teilen den Seed, docs/generation_loop.md), LOAD v34-b01_brierbest, REF_TRAIN_MANIFEST,
# Manifest-Diff-Erwartung, Trainings-Rezept, Tor 1 gegen v34-b01 (Spec v34-b01_brierbest beidseits,
# Seeds 20261600/01, Stufenregel 20261602, Praefix gating).
#
# DAS TRAININGS-REZEPT IST UNVERAENDERT gegen models/manifest_train_v34-b01_20261001_183258.json.
#
# KOSTEN (HERLEITUNG, nicht gemessen): Erzeugung rund 14 h = policy-s400 1.000 x 6,21 s (gemessen
# fuer policy @400, par.10a) + W-s400 2.000 x rund 6,3 s + deviate-s400 4.000 x rund 4,9 s +
# excursion-s400 4.000 x rund 3,4 s; fuer W und Schwarm Faktor 1,95 (= 6,21 / 3,18, policy @400
# gegen policy-s100 @100, par.10a) auf die @100-Zeiten aus par.9/par.10a. Danach Fenster,
# Training und Tor 1 wie b01 (rund 4,5 h, par.11 "Kosten"); zusammen rund 19 h.
#
# START: im Terminal-Tab mit Git-Bash, als DATEI:  bash tools/night_v35_b02_chain.sh
# KEINE PIPE dahinter, keine eigene Umleitung (weit ueber der 2-h-Grenze der Hintergrundaufgaben).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

ART=evaluations/artifacts
SEED=20260965
GEN=v34-b01                                                  # Generator = amtierender Champion
GEN_MODEL=models/alphazero_v34-b01_brierbest.onnx            # Tor-1-Gegner
ARM=v35-b02
LOAD=v34-b01_brierbest
REF_TRAIN_MANIFEST=models/manifest_train_v34-b01_20261001_183258.json
N_VAL=120
SPEC=models/v34-b01_brierbest.spec.json                      # Tor 1 BEIDSEITS (par.12 wie par.11)
CARRIER=policy_carrier_manifest_v35_b02.json
WIN=data/window_v35_b02                                      # Stamm der Fenster-Dateien

step_begin() {  # $1 Schrittname
  STEP_NAME="$1"; STEP_T0=$(date +%s)
  echo ""
  echo "== $1   Start $(date +%F' '%H:%M:%S)"
}
step_end() {
  echo "   Ende ${STEP_NAME}: $(date +%F' '%H:%M:%S), $(( $(date +%s) - STEP_T0 )) s Wanduhr"
}

for f in "$GEN_MODEL" "models/alphazero_${LOAD}.pth" "$REF_TRAIN_MANIFEST" tools/v35_b02_generate.sh; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
grep -q "FEATURE_FORMULA_VERSION" config.py || { echo "ABBRUCH: FEATURE_FORMULA_VERSION fehlt in config.py"; exit 2; }
python -X utf8 -c "import config,sys; sys.exit(0 if (config.INPUT_SIZE,config.NUM_ACTIONS)==(888,414) else 3)" \
  || { echo "ABBRUCH: config.py traegt nicht INPUT_SIZE 888 / NUM_ACTIONS 414"; exit 3; }
for f in models/alphazero_${ARM}*.pth; do
  [ -f "$f" ] && { echo "ABBRUCH: $f liegt schon (train.py wuerde ohnehin abbrechen)"; exit 4; }
done
[ -f "$SPEC" ] || { echo "ABBRUCH: Tor-1-Spec $SPEC fehlt"; exit 4; }
if [ -f "data/$CARRIER" ]; then
  echo "ABBRUCH: data/$CARRIER liegt schon -- wird NICHT ueberschrieben."
  echo "         Pruefen, woher es stammt; zum Neubau von Hand beiseitelegen und neu starten."
  exit 5
fi
N_POL=$(ls data/ | grep -c "^selfplay_${GEN}-policy_.*\.pkl$")
[ "$N_POL" = "100" ] || { echo "ABBRUCH: selfplay_${GEN}-policy_*.pkl trifft $N_POL statt 100 Dateien"; exit 6; }
echo "== v35-KETTE ($ARM), Tor-1-Spec: $SPEC   Start $(date +%F' '%H:%M:%S)"

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
wait_for_free_cpu "v35-b02-Kette"

step_begin "0) Erzeugung v35-b02 (tools/v35_b02_generate.sh: Smokes, vier Klassen @400 Modus 2, Abnahmen)"
bash tools/v35_b02_generate.sh
RC=$?
[ $RC -eq 0 ] || { echo "STOPP: Erzeugung mit Exit $RC -- kein Fenster, kein Training"; exit 20; }
step_end

# Trainings-Umgebung ERST JETZT (Kopf, Punkt 0); Inhalt unveraendert gegen b01 bis auf das
# Traeger-Manifest.
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v34-b01-'
export MOSAIC_FEATURES_FROM_RUST=1
export MOSAIC_CARRIER_MANIFEST=$CARRIER
# MOSAIC_DATA_EXCLUDE ist ein REGEX, angewandt per re.search auf den Basename
# (engine/py/corpus_dataset.py:519-522, tools/build_cache_incremental.py:157-170,
# train.py:1389-1392). Alternation mit | wie b01.
export MOSAIC_DATA_EXCLUDE='selfplay_v29-b11-probe_|selfplay_depth|selfplay_s4states|selfplay_tor2a|selfplay_probe-|selfplay_x35|selfplay_x35e2'
# Wertmaske der Wuerfelphase (par.11, Asym-Prereg par.5d): MUSS vor build_cache_incremental UND
# train.py stehen; beide laufen in dieser Shell und erben den Export.
export MOSAIC_MASK_DICE_PHASE_VALUE=1
unset MOSAIC_MOON_TARGET_SOURCE
# Der Cache-Waechter der Erzeugung ([b]uild_cache im BUSY_PATTERN) muss beendet sein.
wait_for_free_cpu "v35-b02 Fenster"

step_begin "1) Traeger-Manifest v35-b02 (400 = policy 100 + policy-s400 100 + policy-dice-v2-r1-s400 200)"
# --pattern policy_ (Unterstrich) trifft genau die 100 policy-Dateien, --n-files 100 nimmt sie alle;
# --include-glob "policy-*s400_" nimmt policy-s400_ und policy-dice-v2-r1-s400_ vollstaendig (trifft
# weder policy-s100_ noch policy-dice-v2-r1_). Ausgabe nach data/<--out> (--data-dir Default data).
python -X utf8 tools/generate_carrier_manifest.py \
  --pattern "selfplay_${GEN}-policy_*.pkl" --n-files 100 --seed $SEED \
  --include-glob "selfplay_${GEN}-policy-*s400_*.pkl" \
  --out "$MOSAIC_CARRIER_MANIFEST"
[ $? -eq 0 ] || { echo "STOPP: generate_carrier_manifest.py gescheitert"; exit 10; }
python -X utf8 - "$MOSAIC_CARRIER_MANIFEST" "$GEN" <<'PYEOF'
import json, sys
name, gen = sys.argv[1:3]
f = json.load(open(f"data/{name}", encoding="utf-8"))["policy_carrier_files"]
pol = [x for x in f if x.startswith(f"selfplay_{gen}-policy_")]
s400 = [x for x in f if x.startswith(f"selfplay_{gen}-policy-s400_")]
dice = [x for x in f if x.startswith(f"selfplay_{gen}-policy-dice-v2-r1-s400_")]
print(f"Manifest: {len(f)} Traeger = {len(pol)} policy_ + {len(s400)} policy-s400_ + {len(dice)} policy-dice-v2-r1-s400_")
assert (len(f), len(pol), len(s400), len(dice)) == (400, 100, 100, 200), (len(f), len(pol), len(s400), len(dice))
assert len(set(f)) == len(f), "Doppelte im Manifest"
PYEOF
[ $? -eq 0 ] || { echo "STOPP: Traeger-Manifest traegt nicht 400 = 100/100/200"; exit 10; }
step_end

step_begin "2) Fensterliste ${WIN}.txt (fuenf Klassen @400 Modus 2, 1.200 Dateien)"
python -X utf8 - "$GEN" "$N_VAL" "$WIN" <<'PYEOF'
import glob, os, re, sys
gen, n_val, win = sys.argv[1:4]
soll = {"value-deviate-s400": 400, "value-excursion-s400": 400, "policy": 100, "policy-s400": 100,
        "policy-dice-v2-r1-s400": 200}
def klasse(k):
    # "{k}_" mit Unterstrich: "policy_" trifft NICHT "policy-s400_", "value-deviate-s400_" nicht "value-deviate_"
    return sorted(os.path.basename(p) for p in glob.glob(f"data/selfplay_{gen}-{k}_*.pkl"))
neu = {k: klasse(k) for k in soll}
print("je Klasse:", {k: len(v) for k, v in neu.items()})
assert {k: len(v) for k, v in neu.items()} == soll, {k: len(v) for k, v in neu.items()}
allf = [b for k in soll for b in neu[k]]
assert len(allf) == 1200, len(allf)
assert len(allf) == len(set(allf)), "Doppelte im Fenster"
assert all(os.path.exists(os.path.join("data", b)) for b in allf), "Datei fehlt"
bad = [b for b in allf if any(s in b for s in ("probe", "x35", "smoke", "exploiter"))]
assert not bad, ("Sonden-/Probe-Namen im Fenster", bad[:5])
excl = os.environ.get("MOSAIC_DATA_EXCLUDE", "")
hit = [b for b in allf if excl and re.search(excl, b)]
assert not hit, ("Fensterdatei kollidiert mit MOSAIC_DATA_EXCLUDE", hit[:5])
with open(f"{win}.txt", "w", encoding="utf-8", newline="\n") as fh:
    fh.write(f"# v35-b02-Fenster (PREREG_v35_window.md par.12): 1.200 Dateien, alles Generator {gen} @400 Modus 2 "
             "(value-deviate-s400 400, value-excursion-s400 400, policy 100, policy-s400 100, policy-dice-v2-r1-s400 200)\n")
    fh.write("\n".join(allf) + "\n")
vf = int(n_val) / len(allf)
open(f"{win}.valfrac", "w", encoding="utf-8").write(f"{vf:.8f}\n")
print(f"{win}.txt: {len(allf)} Dateien; val_frac {vf:.8f} fuer {n_val} Val-Dateien")
PYEOF
[ $? -eq 0 ] || { echo "STOPP: Fensterbau gescheitert"; exit 11; }
VF=$(tr -d '[:space:]' < "${WIN}.valfrac")
step_end

step_begin "3) Bloecke fuers Fenster"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list "${WIN}.txt"
echo "   Exit $? ($(date +%H:%M:%S))"
step_end

step_begin "4) Trainingsanteil, Fenster-Schluessel, Monolith"
python -X utf8 tools/window_train_split.py --file-list "${WIN}.txt" --val-frac "$VF" \
  --val-pool "$MOSAIC_VAL_POOL" --encoder 2d --value-target-variant nortv \
  --train-list-out "${WIN}_train.txt" --val-list-out "${WIN}_val.txt" \
  > "$ART/v35_b02_split.txt"
cat "$ART/v35_b02_split.txt"
NV=$(grep -vc '^#' "${WIN}_val.txt")
[ "$NV" = "$N_VAL" ] || { echo "STOPP: Val-Menge hat $NV statt $N_VAL Dateien"; exit 12; }
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v35_b02_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
CACHE="data/.cache_${KEY}.h5"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list "${WIN}_train.txt" \
  --merge-out "$CACHE"
echo "   Exit $? ($(date +%H:%M:%S))"
[ -f "$CACHE" ] || { echo "STOPP: Monolith fehlt"; exit 14; }
python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; print('   Stempel:',k); sys.exit(0 if k==sys.argv[2] else 16)" "$CACHE" "$KEY" \
  || { echo "STOPP: Stempel passt nicht zum Schluessel"; exit 16; }
# Masken-Abnahme (par.11, unveraendert): stamp_cache_key_attrs stempelt NICHT das
# Schluesselmaterial, nur Schluessel, Diagnosefelder und den MOSAIC_*-Fingerabdruck
# (engine/py/corpus_dataset.py:812-836). Darum: den Fenster-Schluessel des Trainingsanteils mit
# derselben Funktion wie window_train_split.py (corpus_dataset.window_cache_key, gleiche Argumente,
# volle Pfade aus config.DATA_DIR) einmal MIT und einmal OHNE MOSAIC_MASK_DICE_PHASE_VALUE berechnen.
python -X utf8 - "$KEY" "$CACHE" "$WIN" <<'PYEOF'
import glob, os, sys
root = os.getcwd()
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, "engine", "py"))
from config import DATA_DIR
import corpus_dataset, h5py
key, cache, win = sys.argv[1:4]
wanted = [os.path.basename(l.strip()) for l in open(f"{win}_train.txt", encoding="utf-8")
          if l.strip() and not l.startswith("#")]
have = {os.path.basename(f): f for f in glob.glob(os.path.join(str(DATA_DIR), "*.pkl"))}
train_files = sorted(have[n] for n in wanted)
def wkey():
    return corpus_dataset.window_cache_key(str(DATA_DIR), train_files, value_target_variant="nortv",
                                           encoder="2d", conjunction_head=False)
assert os.environ.get("MOSAIC_MASK_DICE_PHASE_VALUE") == "1", "Knopf nicht gesetzt"
on = wkey()
os.environ.pop("MOSAIC_MASK_DICE_PHASE_VALUE")
off = wkey()
os.environ["MOSAIC_MASK_DICE_PHASE_VALUE"] = "1"
print(f"   Schluessel mit Maske {on.key}, ohne Maske {off.key}, Monolith {key}")
assert on.key == key, "Schluessel mit Maske != Schluessel des Monolithen"
assert on.key != off.key, "Maske aendert den Fenster-Schluessel nicht"
assert "+maskdicephasevalue_v1" in on.material, "Marker fehlt im Schluesselmaterial"
fp = h5py.File(cache, "r").attrs.get("mosaic_env_fingerprint", "")
fp = fp.decode() if isinstance(fp, bytes) else str(fp)
assert "MOSAIC_MASK_DICE_PHASE_VALUE=1" in fp.split(";"), "Monolith-Fingerabdruck ohne Maske"
print("   Masken-Abnahme GRUEN")
PYEOF
[ $? -eq 0 ] || { echo "STOPP: Masken-Abnahme ROT (Schluessel traegt die Wertmaske nicht)"; exit 19; }
echo "##### FENSTER STEHT $(date +%F' '%H:%M:%S) -- Monolith $CACHE"
step_end

# ABBRUCH? Fortsetzen mit demselben Aufruf plus --resume (Fingerabdruck-Waechter).
step_begin "5) Training $ARM -- WARMSTART von $LOAD"
python -X utf8 -u train.py --name "$ARM" --load "$LOAD" \
  --file-list "${WIN}.txt" --cache-file "$CACHE" \
  --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac "$VF" --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 0.0 \
  --moon-loss-weight 0.0 --opp-points-head \
  --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed $SEED
echo "   Training Exit $? ($(date +%H:%M:%S))"
step_end

step_begin "5b) Manifest-Diff des TRAININGS gegen das v34-b01-Rezept"
python -X utf8 - "$ARM" "$REF_TRAIN_MANIFEST" "$CARRIER" <<'PYEOF'
import glob, io, json, sys
arm, ref_path, carrier = sys.argv[1], sys.argv[2], sys.argv[3]
ps = sorted(glob.glob(f"models/manifest_train_{arm}_*.json"))
if not ps:
    print("   STOPP: kein Trainings-Manifest gefunden"); sys.exit(17)
m = json.load(io.open(ps[-1], encoding="utf-8"))
neu = m.get("cli_args", {}) or {}
ref = json.load(io.open(ref_path, encoding="utf-8")).get("cli_args", {}) or {}
erwartet = {"load", "name", "file_list", "cache_file", "seed", "val_pool", "val_frac"}
unerwartet = []
for k in sorted(set(ref) | set(neu)):
    if k not in ref:
        print(f"   cli_args.{k}: neu, Default -> {arm}={neu.get(k)!r}")
        continue
    if ref.get(k) != neu.get(k):
        mark = "" if k in erwartet else "  <== STOPP"
        if k not in erwartet:
            unerwartet.append(k)
        print(f"   cli_args.{k}: v34-b01={ref.get(k)!r} -> {arm}={neu.get(k)!r}{mark}")
print(f"   Manifest {ps[-1]}; unerwartete Abweichungen: {len(unerwartet)} (erwartet sind genau {sorted(erwartet)})")
if unerwartet:
    sys.exit(17)
env = m.get("mosaic_env") or {}
print(f"   mosaic_env: MOSAIC_MASK_DICE_PHASE_VALUE={env.get('MOSAIC_MASK_DICE_PHASE_VALUE')!r}, "
      f"MOSAIC_CARRIER_MANIFEST={env.get('MOSAIC_CARRIER_MANIFEST')!r}")
if env.get("MOSAIC_MASK_DICE_PHASE_VALUE") != "1" or \
   env.get("MOSAIC_CARRIER_MANIFEST") != carrier:
    sys.exit(18)
PYEOF
RC=$?
[ $RC -eq 17 ] && { echo "STOPP: Manifest-Diff mit unerwarteter Abweichung (oder kein Manifest) -- KEIN Tor 1"; exit 17; }
[ $RC -eq 18 ] && { echo "STOPP: mosaic_env traegt Maske oder Traeger-Manifest v35_b02 nicht -- KEIN Tor 1"; exit 18; }
[ $RC -eq 0 ] || { echo "STOPP: Manifest-Diff mit Exit $RC -- KEIN Tor 1"; exit 17; }
step_end

# Das zu gatende Netz: aus dem Trainings-Manifest bestimmt (Brier-erstes Minimum), nicht aus dem
# Dateinamen geraten (par.11/par.12, Code-Review 2 #1). Werkzeug druckt mit --ext onnx den Pfad auf stdout.
if [ -f tools/brier_best_checkpoint.py ]; then
  A=$(python -X utf8 tools/brier_best_checkpoint.py "$ARM" --ext onnx)
  [ $? -eq 0 ] && [ -n "$A" ] && [ -f "$A" ] || { echo "STOPP: brier_best_checkpoint.py findet kein Netz fuer $ARM"; exit 15; }
elif [ -f "models/alphazero_${ARM}_brierbest.onnx" ]; then
  echo "HINWEIS: tools/brier_best_checkpoint.py fehlt -- Rueckfall auf die v34-Logik"
  A="models/alphazero_${ARM}_brierbest.onnx"
elif [ -f "models/alphazero_${ARM}.onnx" ]; then
  echo "HINWEIS: tools/brier_best_checkpoint.py fehlt, kein _brierbest -- finales Modell wird genommen"
  A="models/alphazero_${ARM}.onnx"
else
  echo "UEBERSPRUNGEN: kein Modell $ARM -- Training gescheitert?"; exit 15
fi
echo "##### TRAINING DURCH $(date +%F' '%H:%M:%S) -- Modell $A"

gate() {  # $1 Gegnername, $2 Gegnermodell, $3 Seed, $4 Praefix der Ausgabe
  local OUT="$ART/${4}_${ARM}_vs_${1}_s${3}.json"
  local G0
  G0=$(date +%s)
  echo ""
  echo "===== $ARM gegen $1, Seed $3   Start $(date +%F' '%H:%M:%S)"
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
  echo "   Ende Seed $3: $(date +%F' '%H:%M:%S), $(( $(date +%s) - G0 )) s Wanduhr"
}

wait_for_free_cpu "Tor 1"
step_begin "6) Tor 1 = Champion-Kante: $ARM gegen den Generator $GEN, zwei Seeds a 200 Paaren, Stufenregel"
for S in 20261600 20261601; do
  gate "$GEN" "$GEN_MODEL" "$S" gating
done
python -X utf8 tools/gating_block_z.py "$ART/gating_${ARM}_vs_${GEN}_s20261600.json" "$ART/gating_${ARM}_vs_${GEN}_s20261601.json"
N_SIG=$(python -X utf8 tools/gating_block_z.py --json \
  "$ART/gating_${ARM}_vs_${GEN}_s20261600.json" "$ART/gating_${ARM}_vs_${GEN}_s20261601.json" \
  | python -c "import sys,json; d=json.load(sys.stdin); print(sum(r['z'] >= 1.96 for r in d['per_seed']))")
echo "   Seeds einzeln >= +1,96: ${N_SIG:-?} von 2"
if [ "$N_SIG" = "1" ]; then
  echo "   -> Widerspruch: dritter Seed 20261602 (Stufenregel, par.12 wie par.11)"
  gate "$GEN" "$GEN_MODEL" 20261602 gating
  python -X utf8 tools/gating_block_z.py "$ART"/gating_${ARM}_vs_${GEN}_s2026160[012].json
elif [ -z "$N_SIG" ]; then
  echo "   STOPP: Block-z nicht berechenbar -- Stufenregel von Hand anwenden"
fi
step_end

echo ""
echo "########## v35-b02-KETTE FERTIG $(date +%F' '%H:%M:%S)"
echo "   Faellig danach (par.12): Abnahme Fenster, Netz-Gesundheit gegen den Warmstart, Verdikt Tor 1"
echo "   (Block-z, Stufenregel), Tor 2a (corpus_sanity der Policy-Klassen gegen 0,826), Tor 2b (volle"
echo "   Spalten je Seite aus den Tor-1-Logs), sechs Standard-Kennzahlen je Seite, Elo-Register,"
echo "   Laufzeiten in die Prereg; Promotion NUR nach Nutzer-Entscheid und /mosaic-champion-promotion."
