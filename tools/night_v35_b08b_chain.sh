#!/usr/bin/env bash
# v35-b08b-Kette (EINE Datei): EMA ueber die Epochen wie b08, gespeichert wird aber der gemittelte Stand
# mit dem besten EIGENEN Val-Brier (train.py --weight-average-select brierbest). Training byte-gleich b02
# bis auf die Mittelungs-Knoepfe, Manifest-Diff gegen b02, Vorab-Test `_avg` gegen `_brierbest`
# desselben Laufs, bei bestandenem Vorab-Test Schnellblick gegen b02 (feste Laenge 2 x 50 Paare).
# Registrierungen (verbindlich): evaluations/PREREG_v35_window.md
#   par.12    b02-Fenster (Dateiliste, Traeger-Manifest 400, Val 120, Seed 20260965, Rezept)
#   par.16    b08: --weight-average ema (decay 0,75 ab Epoche 2), Vorab-Test gepaart ueber Dateien
#   par.16a   b08-Ergebnis: Endstand des Mittels schlechter als Einzelstand -> Folgearm b08b
#   par.16b   b08b: Auswahl am eigenen Brier-Minimum; Vorab-Test bestanden = CI der Brier-Differenz
#             (Referenz `_brierbest` minus `_avg`) NICHT ganz unter 0; dann Schnellblick par.19.0
#   par.19.0  Schnellblick: Gegner b02 (alphazero_v35-b02_brierbest.onnx), paired_gating @400 beidseits,
#             Spec v34-b01_brierbest, Blockgroesse 5, feste Laenge 2 Seeds a 50 Paare (20261700/01),
#             --log-games; Lesart gepoolt >= 55 % ODER Block-z >= +1,5 = "spannend"; sechs Kennzahlen
# Vorlagen: tools/night_v35_arms_chain.sh (b08-Zweig, Schluessel-Abnahme ohne Neubau, Vorab-Test),
# tools/night_v35_b11_b15_chain.sh (RESUME-Modus, train_arm, Manifest-Diff mit mosaic_env, quicklook).
#
# SCHLUESSEL: b08b muss GENAU den b02-Schluessel treffen (Mittelung und Auswahl wirken erst im Training,
# kein Datenschicht-Knopf). Es wird NICHT neu gebaut und NICHT neu zusammengefuegt (--merge-out wuerde
# den b02-Monolithen data/.cache_<b02-Schluessel>.h5 neu schreiben).
#
# KOSTEN (HERLEITUNG aus par.16a und par.19.0 Punkt 5, nicht gemessen): Split und Schluessel-Abnahme
# rund 1 min, Training rund 25 min (b08: 1.461,0 s mit Mittelung, Manifest laufzeit.wanduhr_s), Vorab-
# Test rund 1 min, Schnellblick 200 Partien x rund 17,7 s = rund 1,0 h; zusammen rund 1,5 h. Laufzeiten
# stehen je Schritt im Log und in der Zusammenfassung am Ende.
#
# START: im Terminal-Tab mit Git-Bash, als DATEI:  bash tools/night_v35_b08b_chain.sh
# KEINE PIPE dahinter, keine eigene Umleitung. Wartet zuerst auf das Ende laufender v35-Ketten und der
# Tree-Reuse-Arena-Kette, dann auf eine freie Maschine (tools/lib/cpu_free.sh).
# WIEDERAUFNAHME: RESUME=1 bash tools/night_v35_b08b_chain.sh -- Training: _resume.pth -> --resume,
# finaler Stand mit laufzeit -> uebersprungen; Vorab-Test-Artefakt liegt -> wiederverwendet;
# Schnellblick: fertiges Artefakt -> Seed uebersprungen, <out>.partial.json -> paired_gating.py --resume.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

ART=evaluations/artifacts
ARM=v35-b08b
SEED=20260965                                                # alle Arme einer Generation (par.12)
LOAD=v34-b01_brierbest                                       # Warmstart wie b02
N_VAL=120
SPEC=models/v34-b01_brierbest.spec.json                      # Schnellblick BEIDSEITS (par.19.0 Punkt 3)
CARRIER=policy_carrier_manifest_v35_b02.json
WIN=data/window_v35_b02                                      # b02-Fensterdateien, NICHT neu ziehen
B02=v35-b02
B02_KEY_EXPECTED=8e8096768cf0                                # par.12 (evaluations/artifacts/v35_b02_split.txt)
OPP_MODEL=models/alphazero_v35-b02_brierbest.onnx            # Schnellblick-Gegner (par.19.0 Punkt 1)
QUICK_SEEDS="20261700 20261701"
QUICK_PAIRS=50
# Arm-Unterschied gegen b02 (par.16b): EMA decay 0,75 ab Epoche 2, Auswahl am eigenen Brier-Minimum.
WA_FLAGS=(--weight-average ema --weight-average-decay 0.75 --weight-average-from-epoch 2
          --weight-average-select brierbest)
RESUME_MODE="${RESUME:-0}"
case "$RESUME_MODE" in
  0|1) ;;
  *) echo "ABBRUCH: RESUME='$RESUME_MODE' -- erlaubt sind 0 und 1"; exit 1 ;;
esac
[ "$RESUME_MODE" = "1" ] && echo "########## RESUME=1: Wiederaufnahme-Modus (liegende Schritte werden geprueft und wiederverwendet)"
STEPS_FILE=$(mktemp)
T_CHAIN0=$(date +%s)

step_begin() {  # $1 Schrittname
  STEP_NAME="$1"; STEP_T0=$(date +%s)
  echo ""
  echo "== $1   Start $(date +%F' '%H:%M:%S)"
}
step_end() {  # schreibt die Wanduhr auch in die Zusammenfassung (Schritt, Sekunden)
  local dt=$(( $(date +%s) - STEP_T0 ))
  echo "   Ende ${STEP_NAME}: $(date +%F' '%H:%M:%S), ${dt} s Wanduhr"
  printf '%s\t%s\n' "$STEP_NAME" "$dt" >> "$STEPS_FILE"
}
# Zusammenfassung der Wanduhren bei JEDEM Ende (auch STOPP und Vorab-Test ohne Gewinn).
finish() {
  local rc=$?
  echo ""
  echo "########## $ARM-KETTE ENDE $(date +%F' '%H:%M:%S), Exit $rc, $(( $(date +%s) - T_CHAIN0 )) s Wanduhr gesamt"
  echo "Wanduhr je Schritt (Schritt, Sekunden):"
  cat "$STEPS_FILE"
  rm -f "$STEPS_FILE"
}
trap finish EXIT

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"

# --- Fruehe Pruefung VOR dem Warten (Bedienfehler nicht erst nach Stunden merken) ------------------
grep -q -- '"--weight-average-select"' train.py \
  || { echo "ABBRUCH: train.py kennt --weight-average-select nicht (par.16b)"; exit 1; }
grep -q -- '"--fixed-length"' tools/paired_gating.py \
  || { echo "ABBRUCH: tools/paired_gating.py kennt --fixed-length nicht"; exit 1; }

# --- 0) Warten auf das Ende laufender Ketten (Bauform night_v35_b11_b15_chain.sh) -------------------
echo "########## $ARM-KETTE WARTET auf das Ende laufender v35-/Arena-Ketten $(date +%F' '%H:%M:%S)"
tick=0
while :; do
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '[n]ight_v35_b02_chain|[n]ight_v35_arms_chain|[n]ight_v35_b09_b10_chain|[n]ight_v35_b11_b15_chain|[t]ree_reuse_arena_chain' }).Count" 2>/dev/null | tr -d '\r[:space:]')
  [ "$n" = "0" ] && break
  tick=$((tick + 1))
  [ $tick -gt 2400 ] && { echo "STOPP: Vorgaenger-Ketten nach 40 h noch nicht fertig"; exit 1; }
  [ $((tick % 10)) -eq 1 ] && echo "   Vorgaenger-Kette(n) laufen noch (Antwort '${n}', $(date +%H:%M:%S))"
  sleep 60
done
echo "   Vorgaenger-Ketten beendet ($(date +%H:%M:%S))"

# --- Vorpruefungen (ein Fehler hier stoppt die Kette) -----------------------------------------------
for f in "$OPP_MODEL" "models/alphazero_${LOAD}.pth" "$SPEC" "data/$CARRIER" \
         "${WIN}.txt" "${WIN}_train.txt" "${WIN}_val.txt" "${WIN}.valfrac" "$ART/v35_b02_split.txt" \
         tools/brier_best_checkpoint.py tools/checkpoint_val_eval.py tools/gating_block_z.py \
         tools/paired_gating.py tools/window_train_split.py \
         tools/probes/arena_column_probe.py tools/plate_points_from_arena.py; do
  [ -f "$f" ] || { echo "STOPP: $f fehlt"; exit 2; }
done
REF_MANIFESTS=(models/manifest_train_${B02}_*.json)
REF_TRAIN_MANIFEST="${REF_MANIFESTS[${#REF_MANIFESTS[@]}-1]}"   # Glob sortiert: das neueste
[ -f "$REF_TRAIN_MANIFEST" ] || { echo "STOPP: kein models/manifest_train_${B02}_*.json -- b02 nicht trainiert"; exit 3; }
python -X utf8 -c "import config,sys; sys.exit(0 if (config.INPUT_SIZE,config.NUM_ACTIONS)==(888,414) else 3)" \
  || { echo "STOPP: config.py traegt nicht INPUT_SIZE 888 / NUM_ACTIONS 414"; exit 3; }
VF=$(tr -d '[:space:]' < "${WIN}.valfrac")
[ -n "$VF" ] || { echo "STOPP: ${WIN}.valfrac leer"; exit 3; }
NW=$(grep -vc '^#' "${WIN}.txt")
[ "$NW" = "1200" ] || { echo "STOPP: b02-Fensterliste hat $NW statt 1200 Dateien"; exit 3; }
NV=$(grep -vc '^#' "${WIN}_val.txt")
[ "$NV" = "$N_VAL" ] || { echo "STOPP: b02-Val-Liste hat $NV statt $N_VAL Dateien"; exit 3; }
B02_KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v35_b02_split.txt" | awk '{print $NF}')
[ "$B02_KEY" = "$B02_KEY_EXPECTED" ] \
  || { echo "STOPP: b02-Schluessel '$B02_KEY' aus $ART/v35_b02_split.txt != $B02_KEY_EXPECTED"; exit 3; }
CACHE="data/.cache_${B02_KEY}.h5"
[ -f "$CACHE" ] || { echo "STOPP: b02-Monolith $CACHE fehlt"; exit 3; }
B02_BEST_PTH=$(python -X utf8 tools/brier_best_checkpoint.py "$B02" --ext pth)
[ $? -eq 0 ] && [ -n "$B02_BEST_PTH" ] && [ -f "$B02_BEST_PTH" ] \
  || { echo "STOPP: kein Brier-bestes b02-Netz (.pth)"; exit 3; }
if [ "$RESUME_MODE" != "1" ]; then
  for f in models/alphazero_${ARM}*.pth "$ART"/quicklook_${ARM}_vs_${B02}_s*.json \
           "$ART/checkpoint_val_eval_${ARM}_avg_vs_brierbest.json"; do
    [ -f "$f" ] && { echo "STOPP: $f liegt schon (RESUME=1 zum Fortsetzen)"; exit 4; }
  done
fi
echo "== $ARM-KETTE   Start $(date +%F' '%H:%M:%S)"
echo "   Referenz-Manifest $REF_TRAIN_MANIFEST, b02-Schluessel $B02_KEY, val_frac $VF, b02-Netz $B02_BEST_PTH"
echo "   Arm-Unterschied: ${WA_FLAGS[*]}"

# --- Trainings-Umgebung = die der b02-Kette (wie night_v35_b11_b15_chain.sh) ------------------------
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v34-b01-'
export MOSAIC_FEATURES_FROM_RUST=1
export MOSAIC_CARRIER_MANIFEST=$CARRIER
export MOSAIC_DATA_EXCLUDE='selfplay_v29-b11-probe_|selfplay_depth|selfplay_s4states|selfplay_tor2a|selfplay_probe-|selfplay_x35|selfplay_x35e2'
export MOSAIC_MASK_DICE_PHASE_VALUE=1
# b02 lief mit MOSAIC_MOON_TARGET_SOURCE=label (= Default, kein Schluessel-Anteil); gesetzt, damit
# mosaic_env im Manifest-Diff byte-gleich b02 ist.
export MOSAIC_MOON_TARGET_SOURCE=label
# Alle Datenschicht-Knoepfe AUS (b08b ist ein reiner Trainingsarm).
unset MOSAIC_BOOTSTRAP_COHERENCE MOSAIC_BOOTSTRAP_SOURCE MOSAIC_BOOTSTRAP_HORIZON_ROUNDS \
      MOSAIC_BOOTSTRAP_MARGIN_SCALE MOSAIC_BOOTSTRAP_TRAJ_LAMBDA MOSAIC_BOOTSTRAP_TRAJ_OPPONENT \
      MOSAIC_BOOTSTRAP_TRAJ_MIX MOSAIC_BOOTSTRAP_TRAJ_CONF_SCALE MOSAIC_TD_LAMBDA

wait_for_free_cpu "$ARM-Kette"

# Training mit den Flags von night_v35_arms_chain.sh (= b02-Rezept) plus WA_FLAGS. Optionale
# Zusatzflags (RESUME=1: --resume) als Argumente.
train_arm() {
  python -X utf8 -u train.py --name "$ARM" --load "$LOAD" \
    --file-list "${WIN}.txt" --cache-file "$CACHE" \
    --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
    --val-frac "$VF" --encoder 2d --value-head wdl --value-target-variant nortv \
    --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 0.0 \
    --moon-loss-weight 0.0 --opp-points-head \
    --destretch-a 0.0051 --destretch-b 1.9269 \
    --select-by-brier --fast-loader --seed $SEED "${WA_FLAGS[@]}" "$@"
}

# Schnellblick EINES Seeds (par.19.0 Punkt 3). Rueckgabe != 0 nur ohne Artefakt.
quicklook() {  # $1 Seed
  local OUT="$ART/quicklook_${ARM}_vs_${B02}_s${1}.json"
  local G0
  G0=$(date +%s)
  if [ -f "$OUT" ]; then
    if [ "$RESUME_MODE" = "1" ]; then
      echo "   RESUME: $OUT liegt schon -- Seed $1 uebersprungen"
      if [ ! -f "$ART/plate_points_quicklook_${ARM}_vs_${B02}_s${1}.json" ]; then
        echo "   Auswertungen zu Seed $1 fehlen -- werden nachgezogen"
        python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
        python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
          --out "$ART/plate_points_quicklook_${ARM}_vs_${B02}_s${1}.json"
      fi
      return 0
    fi
    echo "   STOPP: $OUT liegt schon -- wird nicht ueberschrieben"; return 1
  fi
  echo ""
  echo "===== Schnellblick $ARM gegen $B02, Seed $1   Start $(date +%F' '%H:%M:%S)"
  [ -f "${OUT}.partial.json" ] && echo "   Zwischenstand ${OUT}.partial.json liegt -- paired_gating.py --resume setzt dort fort"
  # --fixed-length: genau $QUICK_PAIRS Paare, SPRT nur mitgeschrieben.
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$A" --spec-a "$SPEC" --model-b "$OPP_MODEL" --spec-b "$SPEC" \
    --name-a "$ARM" --name-b "$B02" \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs $QUICK_PAIRS --fixed-length --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$1" --threads 10 --log-games --no-promote-winner --out "$OUT" --resume
  local RCG=$?
  echo "   Exit $RCG ($(date +%H:%M:%S))"
  # Sechs Standard-Kennzahlen (CLAUDE.md): Spalten/Reihen/Strafleiste aus den Partie-Logs,
  # Punkte je Wertungsplatte; eigene Punkte und Margin stehen im Artefakt (per_pair_scores).
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_quicklook_${ARM}_vs_${B02}_s${1}.json"
  echo "   Ende Seed $1: $(date +%F' '%H:%M:%S), $(( $(date +%s) - G0 )) s Wanduhr"
  [ $RCG -eq 0 ] && [ -f "$OUT" ]
}

# --- 1) Split, Schluessel (= b02), Stempel, Schluessel-Abnahme ---------------------------------------
VFILE_TRAIN="data/window_v35_b08b_train.txt"
VFILE_VAL="data/window_v35_b08b_val.txt"
SPLIT_OUT="$ART/v35_b08b_split.txt"
step_begin "$ARM 1) Trainingsanteil (b02-Liste, val_frac $VF), Schluessel = b02-Schluessel, Monolith"
python -X utf8 tools/window_train_split.py --file-list "${WIN}.txt" --val-frac "$VF" \
  --val-pool "$MOSAIC_VAL_POOL" --encoder 2d --value-target-variant nortv \
  --train-list-out "$VFILE_TRAIN" --val-list-out "$VFILE_VAL" \
  > "$SPLIT_OUT"
RC=$?
cat "$SPLIT_OUT"
[ $RC -eq 0 ] || { echo "STOPP: window_train_split.py mit Exit $RC"; exit 12; }
diff -q <(grep -v '^#' "$VFILE_TRAIN") <(grep -v '^#' "${WIN}_train.txt") >/dev/null \
  || { echo "STOPP: Trainingsliste weicht von der b02-Trainingsliste ab"; exit 12; }
diff -q <(grep -v '^#' "$VFILE_VAL") <(grep -v '^#' "${WIN}_val.txt") >/dev/null \
  || { echo "STOPP: Val-Liste weicht von der b02-Val-Liste ab (Val-Satz muss byte-gleich b02 sein)"; exit 12; }
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$SPLIT_OUT" | awk '{print $NF}')
[ "$KEY" = "$B02_KEY" ] || { echo "STOPP: Schluessel '$KEY' != b02-Schluessel $B02_KEY -- Umgebung weicht ab"; exit 13; }
echo "   Schluessel = b02-Schluessel $KEY, Monolith $CACHE wird wiederverwendet (kein Neubau, kein Merge)"
python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; print('   Stempel:',k); sys.exit(0 if k==sys.argv[2] else 16)" "$CACHE" "$KEY" \
  || { echo "STOPP: Stempel passt nicht zum Schluessel"; exit 16; }
# Material mit derselben Funktion wie window_train_split.py (Muster night_v35_arms_chain.sh, Zweig
# "gleicher Schluessel"): kein Bootstrap-Marker, keine Arm-Variable, Wertmaske im Material und im
# Monolith-Fingerabdruck.
python -X utf8 - "$KEY" "$CACHE" "$VFILE_TRAIN" <<'PYEOF'
import glob, os, sys
root = os.getcwd()
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, "engine", "py"))
from config import DATA_DIR
import corpus_dataset, h5py
key, cache, train_list = sys.argv[1:4]
wanted = [os.path.basename(l.strip()) for l in open(train_list, encoding="utf-8")
          if l.strip() and not l.startswith("#")]
have = {os.path.basename(f): f for f in glob.glob(os.path.join(str(DATA_DIR), "*.pkl"))}
train_files = sorted(have[n] for n in wanted)
on = corpus_dataset.window_cache_key(str(DATA_DIR), train_files, value_target_variant="nortv",
                                     encoder="2d", conjunction_head=False)
assert on.key == key, f"Schluessel {on.key} != Schluessel des Monolithen {key}"
assert "+maskdicephasevalue_v1" in on.material, "Wertmaske fehlt im Schluesselmaterial"
assert "+bootstrap" not in on.material, "Bootstrap-Marker im Material eines Arms ohne Bootstrap"
assert "+tdlambda" not in on.material, "TD-lambda-Marker im Material eines Arms ohne Datenschicht-Knopf"
names = [n for n in os.environ if n.startswith("MOSAIC_BOOTSTRAP_") or n == "MOSAIC_TD_LAMBDA"]
assert not names, f"Datenschicht-Variable gesetzt: {names}"
fp = h5py.File(cache, "r").attrs.get("mosaic_env_fingerprint", "")
fp = (fp.decode() if isinstance(fp, bytes) else str(fp)).split(";")
assert "MOSAIC_MASK_DICE_PHASE_VALUE=1" in fp, "Monolith-Fingerabdruck ohne Maske"
print("   Schluessel-Abnahme GRUEN")
PYEOF
[ $? -eq 0 ] || { echo "STOPP: Schluessel-Abnahme ROT"; exit 19; }
echo "##### FENSTER $ARM STEHT $(date +%F' '%H:%M:%S) -- Monolith $CACHE"
step_end

# --- 2) Training ------------------------------------------------------------------------------------
step_begin "$ARM 2) Training -- WARMSTART von $LOAD (Rezept b02, ${WA_FLAGS[*]})"
if [ "$RESUME_MODE" = "1" ] && [ -f "models/alphazero_${ARM}_resume.pth" ]; then
  echo "   RESUME: models/alphazero_${ARM}_resume.pth liegt -- train.py --resume"
  train_arm --resume
  RC=$?
elif [ "$RESUME_MODE" = "1" ] && [ -f "models/alphazero_${ARM}.pth" ]; then
  python -X utf8 - "$ARM" <<'PYEOF'
import glob, json, sys
ms = sorted(glob.glob(f"models/manifest_train_{sys.argv[1]}_*.json"))
if not ms:
    print("   kein Trainings-Manifest"); sys.exit(1)
lz = json.load(open(ms[-1], encoding="utf-8")).get("laufzeit")
print(f"   {ms[-1]}: laufzeit {lz}")
sys.exit(0 if lz else 1)
PYEOF
  [ $? -eq 0 ] || { echo "STOPP (RESUME): finaler Stand ohne laufzeit im Manifest -- von Hand pruefen"; exit 20; }
  echo "   RESUME: Training $ARM ist durch -- uebersprungen"
  RC=0
else
  for f in models/alphazero_${ARM}*.pth; do
    [ -f "$f" ] && { echo "STOPP: $f liegt ohne Zwischenstand -- von Hand pruefen"; exit 20; }
  done
  train_arm
  RC=$?
fi
echo "   Training Exit $RC ($(date +%H:%M:%S))"
[ $RC -eq 0 ] || { echo "STOPP: Training mit Exit $RC -- kein Vorab-Test"; exit 20; }
step_end

# --- 3) Manifest-Diff gegen b02 plus Abnahme der Auswahl ---------------------------------------------
# Erlaubte cli-Abweichungen gegen b02: name, weight_average (none -> ema). Neu gegen b02 (Schluessel
# fehlt im b02-Manifest): weight_average_select, Pflichtwert brierbest. weight_average_decay und
# weight_average_from_epoch stehen in b02 mit den Defaults 0.75 / 2 und muessen GLEICH bleiben.
# mosaic_env byte-gleich b02, TD_LAMBDA 0.5, file_list = b02-Fensterliste.
step_begin "$ARM 3) Manifest-Diff des TRAININGS gegen $REF_TRAIN_MANIFEST, Abnahme der Auswahl"
python -X utf8 - "$ARM" "$REF_TRAIN_MANIFEST" "${WIN}.txt" <<'PYEOF'
import glob, io, json, sys
arm, ref_path, want_list = sys.argv[1:4]
ps = sorted(glob.glob(f"models/manifest_train_{arm}_*.json"))
if not ps:
    print("   STOPP: kein Trainings-Manifest gefunden"); sys.exit(17)
m = json.load(io.open(ps[-1], encoding="utf-8"))
rm = json.load(io.open(ref_path, encoding="utf-8"))
new, ref = m.get("cli_args", {}) or {}, rm.get("cli_args", {}) or {}
allowed = {"name", "weight_average"}
must_new = {"weight_average_select": "brierbest"}
bad = []
for k in sorted(set(ref) | set(new)):
    if k not in ref:
        ok = k in must_new and new.get(k) == must_new[k]
        print(f"   cli_args.{k}: neu -> {arm}={new.get(k)!r}{'' if ok else '  <== STOPP'}")
        if not ok:
            bad.append(k)
        continue
    if ref.get(k) != new.get(k):
        mark = "" if k in allowed else "  <== STOPP"
        if k not in allowed:
            bad.append(k)
        print(f"   cli_args.{k}: v35-b02={ref.get(k)!r} -> {arm}={new.get(k)!r}{mark}")
want = {"weight_average": "ema", "weight_average_decay": 0.75, "weight_average_from_epoch": 2,
        "weight_average_select": "brierbest", "value_target_lambda": 0.7, "seed": 20260965}
for k, v in want.items():
    if new.get(k) != v:
        print(f"   cli_args.{k} {new.get(k)!r} != {v!r}  <== STOPP"); bad.append(k + "(Wert)")
if str(new.get("file_list")).replace("\\", "/") != want_list:
    print(f"   file_list {new.get('file_list')!r} != {want_list!r}  <== STOPP"); bad.append("file_list(Wert)")
print(f"   Manifest {ps[-1]}; unerwartete cli-Abweichungen: {len(bad)} (erlaubt: {sorted(allowed)}, "
      f"neu: {must_new})")
env, renv = m.get("mosaic_env") or {}, rm.get("mosaic_env") or {}
env_bad = [k for k in sorted(set(env) | set(renv)) if env.get(k) != renv.get(k)]
for k in env_bad:
    print(f"   mosaic_env.{k}: v35-b02={renv.get(k)!r} -> {arm}={env.get(k)!r}  <== STOPP")
td = (m.get("python_constants") or {}).get("TD_LAMBDA")
if td is None or abs(float(td) - 0.5) > 1e-12:
    print(f"   python_constants.TD_LAMBDA {td!r} != 0.5  <== STOPP"); env_bad.append("TD_LAMBDA(Wert)")
print(f"   mosaic_env: {len(env_bad)} unerwartete Abweichungen (erwartet: byte-gleich b02)")
# Einzelstand-Pfad bitgleich b02 (par.16a-Abnahme): die Val-Brier-Kurve der Einzelstaende muss Wert fuer
# Wert die von b02 sein. Abweichung = Bauform verschiebt den Trainingspfad -> STOPP.
hist, rhist = m.get("epoch_history") or [], rm.get("epoch_history") or []
cur = [e.get("value_val_brier") for e in hist]
refc = [e.get("value_val_brier") for e in rhist]
same_path = cur == refc
print(f"   Einzelstand-Brier je Epoche {'GLEICH' if same_path else 'VERSCHIEDEN'} b02 "
      f"({len(cur)} gegen {len(refc)} Epochen){'' if same_path else '  <== STOPP'}")
# Auswahl: gespeichert ist das erste Minimum von avg_value_val_brier.
wa = m.get("weight_average") or {}
avg = [(e.get("avg_value_val_brier"), e.get("epoch")) for e in hist if e.get("avg_value_val_brier") is not None]
for b, ep in avg:
    print(f"   Epoche {ep:2d}: Mittel-Brier {b:.5f}")
sel_bad = []
if not avg:
    sel_bad.append("keine avg_value_val_brier")
else:
    best_b, best_ep = avg[0]
    for b, ep in avg[1:]:
        if b < best_b:
            best_b, best_ep = b, ep
    print(f"   erstes Minimum des Mittels: Epoche {best_ep}, {best_b:.5f}; Block: select {wa.get('select')!r}, "
          f"selected_epoch {wa.get('selected_epoch')!r}, selected_avg_value_val_brier "
          f"{wa.get('selected_avg_value_val_brier')!r}, bn_stats {wa.get('bn_stats')!r}, "
          f"Brier nach BN-Neuschaetzung {wa.get('value_val_brier')!r}")
    if wa.get("select") != "brierbest":
        sel_bad.append("select")
    if wa.get("selected_epoch") != best_ep:
        sel_bad.append("selected_epoch")
    if wa.get("selected_avg_value_val_brier") != best_b:
        sel_bad.append("selected_avg_value_val_brier")
    if wa.get("checkpoint") != f"alphazero_{arm}_avg.pth":
        sel_bad.append("checkpoint")
if wa.get("bn_stats") != "recomputed":
    print(f"   WARNUNG: bn_stats {wa.get('bn_stats')!r} (BN-Neuschaetzung gescheitert, Statistik des letzten "
          f"Epochenstands) -- im Bericht nennen")
if sel_bad:
    print(f"   Auswahl-Abnahme ROT: {sel_bad}  <== STOPP")
sys.exit(17 if bad else (18 if env_bad else (24 if not same_path else (25 if sel_bad else 0))))
PYEOF
RC=$?
[ $RC -eq 0 ] || { echo "STOPP: Manifest-Diff/mosaic_env/Pfad/Auswahl mit Exit $RC -- KEIN Vorab-Test"; exit 17; }
step_end

# --- 4) Vorab-Test par.16b: `_brierbest` (Einzelstand) gegen `_avg` desselben Laufs --------------------
# REFERENZ = ERSTER Checkpoint = der Brier-beste Einzelstand (brier_best_checkpoint.py OHNE --include-avg);
# Feld = Referenz minus `_avg`. CI ganz UNTER 0: der Einzelstand hat den kleineren Brier, das Mittel ist
# schlechter -> Arm beendet. Sonst (CI nicht ganz unter 0) bestanden -> Schnellblick.
step_begin "$ARM 4) Vorab-Test par.16b: Brier _brierbest gegen _avg (gepaart ueber ${N_VAL} Val-Dateien)"
BEST_PTH=$(python -X utf8 tools/brier_best_checkpoint.py "$ARM" --ext pth)
AVG_PTH="models/alphazero_${ARM}_avg.pth"
AVG_ONNX="models/alphazero_${ARM}_avg.onnx"
for f in "$BEST_PTH" "$AVG_PTH" "$AVG_ONNX"; do
  [ -n "$f" ] && [ -f "$f" ] || { echo "STOPP: '$f' fehlt"; exit 31; }
done
echo "   Referenz (Einzelstand) $BEST_PTH, gemittelt $AVG_PTH"
MS=(models/manifest_train_${ARM}_*.json)
PRE_OUT="$ART/checkpoint_val_eval_${ARM}_avg_vs_brierbest.json"
if [ "$RESUME_MODE" = "1" ] && [ -f "$PRE_OUT" ]; then
  echo "   RESUME: $PRE_OUT liegt schon -- wiederverwendet"
else
  python -X utf8 -u tools/checkpoint_val_eval.py --checkpoints "$BEST_PTH" "$AVG_PTH" \
    --val-list "${WIN}_val.txt" --train-manifest "${MS[${#MS[@]}-1]}" --out "$PRE_OUT"
  RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
  [ $RC -eq 0 ] && [ -f "$PRE_OUT" ] || { echo "STOPP: checkpoint_val_eval.py gescheitert"; exit 32; }
fi
python -X utf8 - "$PRE_OUT" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
diffs = d["differences_reference_minus_checkpoint"]
assert len(diffs) == 1, f"erwartet genau einen Vergleich, gefunden {list(diffs)}"
(path, lists), = diffs.items()
a = lists["all"]
ci = a["value_val_brier_diff_ci95"]
print(f"   Referenz {d['reference']} minus {path} (Val {d['val_list']['n_files']} Dateien, "
      f"Selbstpruefung {d.get('selfcheck_overall')}):")
print(f"   Val-Brier Einzelstand minus Mittel: {a['value_val_brier_diff']}, CI95 {ci}  "
      f"(< 0 = Mittel hat den GROESSEREN Brier)")
print(f"   Policy-CE gepoolt Einzelstand minus Mittel: {a['policy_val_loss_pooled_diff']}, "
      f"CI95 {a['policy_val_loss_pooled_diff_ci95']}")
if ci is None:
    print("   kein CI -- Vorab-Test nicht entscheidbar  <== STOPP"); sys.exit(32)
if ci[1] < 0:
    print("   CI GANZ UNTER 0: Mittel schlechter -> Arm beendet, KEIN Schnellblick (par.16b)"); sys.exit(33)
print("   CI nicht ganz unter 0 -> Vorab-Test bestanden, Schnellblick mit dem gemittelten Stand")
PYEOF
RC=$?
step_end
[ $RC -eq 33 ] && { echo "ENDE $ARM: Vorab-Test ohne Gewinn -- kein Schnellblick"; exit 33; }
[ $RC -eq 0 ] || { echo "STOPP: Vorab-Test mit Exit $RC"; exit 32; }
A="$AVG_ONNX"
echo "##### TRAINING $ARM DURCH $(date +%F' '%H:%M:%S) -- Schnellblick mit $A"

# --- 5) Schnellblick gegen b02 ------------------------------------------------------------------------
wait_for_free_cpu "Schnellblick $ARM"
step_begin "$ARM 5) Schnellblick gegen $B02 (feste Laenge, Seeds $QUICK_SEEDS a $QUICK_PAIRS Paare)"
for s in $QUICK_SEEDS; do
  quicklook "$s" || { echo "STOPP: Schnellblick Seed $s ohne Artefakt"; exit 21; }
done
step_end

# --- 6) Lesart par.19.0 Punkt 4 (gepoolt) ---------------------------------------------------------------
step_begin "$ARM 6) Lesart par.19.0 Punkt 4 (gepoolt)"
set -- $QUICK_SEEDS
python -X utf8 tools/gating_block_z.py "$ART/quicklook_${ARM}_vs_${B02}_s$1.json" "$ART/quicklook_${ARM}_vs_${B02}_s$2.json"
python -X utf8 - "$ART/quicklook_${ARM}_vs_${B02}_s$1.json" "$ART/quicklook_${ARM}_vs_${B02}_s$2.json" <<'PYEOF'
import json, os, sys
sys.path.insert(0, os.path.join(os.getcwd(), "tools"))
from gating_block_z import block_shares, block_z
wins = games = 0
shares = []
for p in sys.argv[1:]:
    d = json.load(open(p, encoding="utf-8"))
    wins += d["a_wins_total"]; games += d["n_games_total"]
    shares.extend(block_shares(p))
    print(f"   {os.path.basename(p)}: {d['a_wins_total']}:{d['b_wins_total']} von {d['n_games_total']}, "
          f"Punkte A/B {d.get('avg_score_a')}/{d.get('avg_score_b')}, SPRT-Beruehrung {d.get('sprt_first_crossing')}")
wr = wins / games if games else None
z = block_z(shares)["z"]
if wr is None:
    verdict = "nicht auswertbar"
elif wr >= 0.55 or (z is not None and z >= 1.5):
    verdict = "SPANNEND -> volle Breite gegen b02 faellig (2 x 200 Paare, Seeds 20261600/01) -- startet NICHT automatisch"
elif wr < 0.45:
    verdict = "abgeschlossen mit Gegenbefund (unter 45 %)"
else:
    verdict = "abgeschlossen, kein Hebel (45-55 %, Block-z unter +1,5)"
print(f"   gepoolt: {wins} von {games} = {wr if wr is None else round(wr, 4)}, Block-z "
      f"{'n/a' if z is None else f'{z:+.2f}'} ({len(shares)} Bloecke) -> {verdict}")
PYEOF
step_end
echo "############################## ARM $ARM FERTIG $(date +%F' '%H:%M:%S)"
echo ""
echo "   Faellig danach (par.16b): Ergebnis in die Prereg (Vorab-Test, Schnellblick-Lesart, sechs"
echo "   Standard-Kennzahlen aus den Sonden-Ausgaben oben und plate_points_quicklook_*), Laufzeiten nach"
echo "   docs/measured_runtimes.md; volle Breite NUR nach Koordinator-Entscheid."
exit 0
