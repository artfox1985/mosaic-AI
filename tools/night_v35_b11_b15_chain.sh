#!/usr/bin/env bash
# v35-Kette fuer die Varianten des Trajektorien-Bootstraps v35-b11 bis v35-b15 (EINE Datei): je Arm
# Bloecke und Monolith unter dem neuen Marker auf dem b02-FENSTER, Training byte-gleich b02 bis auf den
# Arm-Unterschied, Manifest-Diff gegen b02, Vorfilter offline gegen b02 und Schnellblick gegen b02
# (feste Laenge 2 x 50 Paare). Die volle Breite startet die Kette NICHT selbst.
# Registrierungen (verbindlich): evaluations/PREREG_v35_window.md
#   par.12    b02-Fenster (Dateiliste, Traeger-Manifest 400, Val 120, Seed 20260965, Rezept)
#   par.19.0  Schnellblick: Gegner b02 (alphazero_v35-b02_brierbest.onnx), Vorfilter (CI der Brier-
#             Differenz b02 minus Arm ganz unter 0 = Arm abgeschlossen), paired_gating @400 beidseits,
#             Spec v34-b01_brierbest, Blockgroesse 5, feste Laenge 2 Seeds a 50 Paare (20261700/01),
#             --log-games, SPRT-Schranken nur mitgeschrieben; Lesart gepoolt >= 55 % ODER Block-z
#             >= +1,5 = "spannend"; sechs Standard-Kennzahlen
#   par.19.1  b11  MOSAIC_BOOTSTRAP_SOURCE=trajectory_lambda, MOSAIC_BOOTSTRAP_TRAJ_LAMBDA=0.5
#   par.19.2  b12  wie b11 plus MOSAIC_BOOTSTRAP_TRAJ_OPPONENT=1
#   par.19.3  b13  MOSAIC_BOOTSTRAP_SOURCE=trajectory, HORIZON 1, MOSAIC_BOOTSTRAP_TRAJ_MIX=0.5
#   par.19.4  b14a trajectory k = 1 plus MOSAIC_TD_LAMBDA=0.7; b14b trajectory k = 1 plus
#             --value-target-lambda 0.5 (Trainingsflag, Schluessel = b03-Schluessel)
#   par.19.5  b15  trajectory k = 1 plus MOSAIC_BOOTSTRAP_TRAJ_CONF_SCALE=s, s aus der Eichung
#             evaluations/artifacts/traj_conf_scale_calibration_v35_b02.json (recommended_scale_s) oder
#             aus B15_CONF_SCALE; b15 laeuft nur, wenn s in der Prereg nachgetragen ist (par.19.5:
#             "die Eichung wird hier nachgetragen, bevor trainiert wird")
# Vorlagen: tools/night_v35_arms_chain.sh (Arm-Bauform, Schluessel-Abnahme, Training, Manifest-Diff),
# tools/night_v35_b09_b10_chain.sh (RESUME-Modus, gate() mit --resume, Offline-Vorabmessung).
#
# JE ARM in einer SUBSHELL (nichts leckt in den naechsten Arm). Reihenfolge b11, b12, b13, b14a, b14b,
# b15 (par.19 "Reihenfolge"). Ein STOPP beendet nur den ARM, die Kette geht zum naechsten.
#
# SCHLUESSEL-REGELN (Marker: engine/py/corpus_dataset.py window_cache_key, Block-Schluessel
# engine/py/file_cache_key.py per_file_cache_key; Abnahme tools/tests/test_trajectory_variant_cache_keys.py):
#   b11 +bootstraptrajlambda_l0.5_v1      b12 +bootstraptrajlambda_l0.5_opp1_v1
#   b13 +bootstraptraj_h1_mix0.5_v1       b14a +bootstraptraj_h1_v1 und +tdlambda0.7_v1
#   b14b +bootstraptraj_h1_v1 (= b03)     b15 +bootstraptraj_h1_conf<s>_v1
# Ohne die Arm-Variablen muss jeder Schluessel auf den b02-Schluessel zurueckfallen. Ein Monolith, der
# unter dem Arm-Schluessel schon liegt (b14b: der von b03), wird nach Stempel-Pruefung wiederverwendet
# und NICHT neu zusammengefuegt.
#
# KOSTEN (HERLEITUNG aus par.19.0 Punkt 5, nicht gemessen): je Arm Bloecke rund 20 min, Merge 3 min,
# Training rund 28 min, Vorfilter 30 s, Schnellblick 200 Partien x rund 17,7 s = rund 1,0 h; zusammen
# rund 1,9 h je Arm, sechs Trainings rund 11,4 h (b14b ohne Bloecke/Merge, falls der b03-Monolith
# liegt). Laufzeiten stehen je Schritt im Log und in der Zusammenfassung.
#
# START: im Terminal-Tab mit Git-Bash, als DATEI:  bash tools/night_v35_b11_b15_chain.sh
# KEINE PIPE dahinter, keine eigene Umleitung (weit ueber der 2-h-Grenze der Hintergrundaufgaben).
# Optional: ARMS="v35-b11 v35-b13" faehrt nur diese Arme (Reihenfolge bleibt die registrierte);
# B15_CONF_SCALE=<s> ueberschreibt die Skala aus dem Eichartefakt.
# WIEDERAUFNAHME: RESUME=1 bash tools/night_v35_b11_b15_chain.sh -- liegende Schritte werden geprueft
# und wiederverwendet (Training: _resume.pth -> --resume, finaler Stand mit laufzeit -> uebersprungen;
# Vorfilter-Artefakt liegt -> wiederverwendet; Schnellblick: fertiges Artefakt -> Seed uebersprungen,
# <out>.partial.json -> paired_gating.py --resume). Ohne RESUME gelten alle STOPP-Pruefungen.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

ART=evaluations/artifacts
SEED=20260965                                                # alle Arme einer Generation (par.12)
LOAD=v34-b01_brierbest                                       # Warmstart wie b02
N_VAL=120
SPEC=models/v34-b01_brierbest.spec.json                      # Schnellblick BEIDSEITS (par.19.0 Punkt 3)
CARRIER=policy_carrier_manifest_v35_b02.json
WIN=data/window_v35_b02                                      # b02-Fensterdateien, NICHT neu ziehen
B02=v35-b02
OPP_MODEL=models/alphazero_v35-b02_brierbest.onnx            # Schnellblick-Gegner (par.19.0 Punkt 1)
QUICK_SEEDS="20261700 20261701"
QUICK_PAIRS=50
CALIBRATION_ARTIFACT=$ART/traj_conf_scale_calibration_v35_b02.json
PREREG=evaluations/PREREG_v35_window.md
ARM_ORDER="v35-b11 v35-b12 v35-b13 v35-b14a v35-b14b v35-b15"
ARMS_SELECTED="${ARMS:-$ARM_ORDER}"
RESUME_MODE="${RESUME:-0}"
case "$RESUME_MODE" in
  0|1) ;;
  *) echo "ABBRUCH: RESUME='$RESUME_MODE' -- erlaubt sind 0 und 1"; exit 1 ;;
esac
for a in $ARMS_SELECTED; do
  case " $ARM_ORDER " in *" $a "*) ;; *) echo "ABBRUCH: ARMS enthaelt unbekannten Arm '$a' (erlaubt: $ARM_ORDER)"; exit 1 ;; esac
done
[ "$RESUME_MODE" = "1" ] && echo "########## RESUME=1: Wiederaufnahme-Modus (liegende Schritte werden geprueft und wiederverwendet)"
SUMMARY_FILE=$(mktemp)
STEPS_FILE=$(mktemp)

# Alle Bootstrap-Knoepfe (file_cache_key.py _bootstrap_source_config) plus MOSAIC_TD_LAMBDA.
ALL_ARM_VARS="MOSAIC_BOOTSTRAP_SOURCE MOSAIC_BOOTSTRAP_HORIZON_ROUNDS MOSAIC_BOOTSTRAP_MARGIN_SCALE MOSAIC_BOOTSTRAP_TRAJ_LAMBDA MOSAIC_BOOTSTRAP_TRAJ_OPPONENT MOSAIC_BOOTSTRAP_TRAJ_MIX MOSAIC_BOOTSTRAP_TRAJ_CONF_SCALE MOSAIC_TD_LAMBDA"

step_begin() {  # $1 Schrittname
  STEP_NAME="$1"; STEP_T0=$(date +%s)
  echo ""
  echo "== $1   Start $(date +%F' '%H:%M:%S)"
}
step_end() {  # schreibt die Wanduhr auch in die Zusammenfassung (Arm, Schritt, Sekunden)
  local dt=$(( $(date +%s) - STEP_T0 ))
  echo "   Ende ${STEP_NAME}: $(date +%F' '%H:%M:%S), ${dt} s Wanduhr"
  printf '%s\t%s\t%s\n' "${ARM:-global}" "$STEP_NAME" "$dt" >> "$STEPS_FILE"
}

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"

# --- Fruehe Pruefung VOR dem Warten (Bedienfehler nicht erst nach Stunden merken) ------------------
grep -q -- '"--fixed-length"' tools/paired_gating.py \
  || { echo "ABBRUCH: tools/paired_gating.py kennt --fixed-length nicht"; exit 1; }
grep -q '"trajectory_lambda"' engine/py/file_cache_key.py \
  || { echo "ABBRUCH: engine/py/file_cache_key.py kennt die Quelle trajectory_lambda nicht"; exit 1; }

# b15: Skala s kanonisch (file_cache_key._canonical_number), damit Umgebung und Marker gleich lauten.
B15_SCALE_RAW="${B15_CONF_SCALE:-}"
if [ -z "$B15_SCALE_RAW" ] && [ -f "$CALIBRATION_ARTIFACT" ]; then
  B15_SCALE_RAW=$(python -X utf8 -c "import json,sys; v=json.load(open(sys.argv[1],encoding='utf-8')).get('recommended_scale_s'); print('' if v is None else v)" "$CALIBRATION_ARTIFACT")
fi
B15_SCALE=""
if [ -n "$B15_SCALE_RAW" ]; then
  B15_SCALE=$(python -X utf8 -c "import sys; sys.path.insert(0,'engine/py'); from file_cache_key import _canonical_number as c; v=float(sys.argv[1]); assert v > 0; print(c(v))" "$B15_SCALE_RAW") \
    || { echo "ABBRUCH: B15-Skala '$B15_SCALE_RAW' ist keine Zahl > 0"; exit 1; }
fi
echo "   b15-Skala s: ${B15_SCALE:-<keine>} (Quelle: ${B15_CONF_SCALE:+B15_CONF_SCALE}${B15_CONF_SCALE:-$CALIBRATION_ARTIFACT})"

# --- 0) Warten auf das Ende der Vorgaenger-Ketten (Bauform night_v35_b09_b10_chain.sh) ----------------
echo "########## v35-b11..b15-KETTE WARTET auf das Ende der v35-Vorgaengerketten $(date +%F' '%H:%M:%S)"
tick=0
while :; do
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '[n]ight_v35_b02_chain|[n]ight_v35_arms_chain|[n]ight_v35_b09_b10_chain' }).Count" 2>/dev/null | tr -d '\r[:space:]')
  [ "$n" = "0" ] && break
  tick=$((tick + 1))
  [ $tick -gt 2400 ] && { echo "STOPP: Vorgaenger-Ketten nach 40 h noch nicht fertig"; exit 1; }
  [ $((tick % 10)) -eq 1 ] && echo "   Vorgaenger-Kette(n) laufen noch (Antwort '${n}', $(date +%H:%M:%S))"
  sleep 60
done
echo "   Vorgaenger-Ketten beendet ($(date +%H:%M:%S))"

# --- Vorpruefungen (global; ein Fehler hier stoppt die GANZE Kette) --------------------------------
for f in "$OPP_MODEL" "models/alphazero_${LOAD}.pth" "$SPEC" "data/$CARRIER" \
         "${WIN}.txt" "${WIN}_train.txt" "${WIN}_val.txt" "${WIN}.valfrac" "$ART/v35_b02_split.txt" \
         engine/py/trajectory_bootstrap.py tools/brier_best_checkpoint.py tools/checkpoint_val_eval.py \
         tools/gating_block_z.py tools/paired_gating.py tools/window_train_split.py \
         tools/build_cache_incremental.py tools/probes/arena_column_probe.py tools/plate_points_from_arena.py; do
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
[ -n "$B02_KEY" ] || { echo "STOPP: kein b02-Schluessel in $ART/v35_b02_split.txt"; exit 3; }
B02_BEST_PTH=$(python -X utf8 tools/brier_best_checkpoint.py "$B02" --ext pth)
[ $? -eq 0 ] && [ -n "$B02_BEST_PTH" ] && [ -f "$B02_BEST_PTH" ] \
  || { echo "STOPP: kein Brier-bestes b02-Netz (.pth) -- Vorfilter unmoeglich"; exit 3; }
echo "== v35-b11..b15-KETTE   Start $(date +%F' '%H:%M:%S)"
echo "   Arme: $ARMS_SELECTED"
echo "   Referenz-Manifest $REF_TRAIN_MANIFEST, b02-Schluessel $B02_KEY, val_frac $VF, b02-Netz $B02_BEST_PTH"

# --- Trainings-Umgebung = die der b02-Kette (wie night_v35_arms_chain.sh) ---------------------------
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v34-b01-'
export MOSAIC_FEATURES_FROM_RUST=1
export MOSAIC_CARRIER_MANIFEST=$CARRIER
export MOSAIC_DATA_EXCLUDE='selfplay_v29-b11-probe_|selfplay_depth|selfplay_s4states|selfplay_tor2a|selfplay_probe-|selfplay_x35|selfplay_x35e2'
export MOSAIC_MASK_DICE_PHASE_VALUE=1
# b02 lief mit MOSAIC_MOON_TARGET_SOURCE=label (= Default, kein Schluessel-Anteil); gesetzt, damit
# mosaic_env im Manifest-Diff byte-gleich b02 ist.
export MOSAIC_MOON_TARGET_SOURCE=label
unset MOSAIC_BOOTSTRAP_COHERENCE
# Arm-Knoepfe global AUS; nur die Subshell eines Arms setzt sie.
unset $ALL_ARM_VARS

wait_for_free_cpu "v35-b11..b15-Kette"

# Training mit den Flags von night_v35_arms_chain.sh (= b02-Rezept). $1 value-target-lambda,
# ab $2 optionale Zusatzflags (RESUME=1: --resume).
train_arm() {
  python -X utf8 -u train.py --name "$ARM" --load "$LOAD" \
    --file-list "${WIN}.txt" --cache-file "$CACHE" \
    --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
    --val-frac "$VF" --encoder 2d --value-head wdl --value-target-variant nortv \
    --value-target-lambda "$1" --ownership-head-2d --ownership-weight 0.0 \
    --moon-loss-weight 0.0 --opp-points-head \
    --destretch-a 0.0051 --destretch-b 1.9269 \
    --select-by-brier --fast-loader --seed $SEED "${@:2}"
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
    echo "   STOPP $ARM: $OUT liegt schon -- wird nicht ueberschrieben"; return 1
  fi
  echo ""
  echo "===== Schnellblick $ARM gegen $B02, Seed $1   Start $(date +%F' '%H:%M:%S)"
  [ -f "${OUT}.partial.json" ] && echo "   Zwischenstand ${OUT}.partial.json liegt -- paired_gating.py --resume setzt dort fort"
  # --fixed-length: genau $QUICK_PAIRS Paare, SPRT nur mitgeschrieben (paired_gating.py, 2026-10-08).
  # --resume setzt einen liegenden Zwischenstand fort; ohne ihn laeuft der Lauf normal.
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

# --- Ein Arm --------------------------------------------------------------------------------------
# $1 Armname. Laeuft in einer Subshell: exit beendet nur den Arm.
# Exit 0 = durch (Schnellblick gelaufen), 34 = Vorfilter: Arm schlechter, kein Schnellblick,
# 30 = uebersprungen (b15 ohne nachgetragene Eichung).
run_arm() {
  ARM="$1"; SHORT="${ARM#v35-}"
  local LAMBDA=0.7 MARKERS="" CLI_ALLOWED="name,cache_file"
  unset $ALL_ARM_VARS
  case "$SHORT" in
    b11)  export MOSAIC_BOOTSTRAP_SOURCE=trajectory_lambda MOSAIC_BOOTSTRAP_TRAJ_LAMBDA=0.5
          MARKERS="+bootstraptrajlambda_l0.5_v1" ;;
    b12)  export MOSAIC_BOOTSTRAP_SOURCE=trajectory_lambda MOSAIC_BOOTSTRAP_TRAJ_LAMBDA=0.5 MOSAIC_BOOTSTRAP_TRAJ_OPPONENT=1
          MARKERS="+bootstraptrajlambda_l0.5_opp1_v1" ;;
    b13)  export MOSAIC_BOOTSTRAP_SOURCE=trajectory MOSAIC_BOOTSTRAP_HORIZON_ROUNDS=1 MOSAIC_BOOTSTRAP_TRAJ_MIX=0.5
          MARKERS="+bootstraptraj_h1_mix0.5_v1" ;;
    b14a) export MOSAIC_BOOTSTRAP_SOURCE=trajectory MOSAIC_BOOTSTRAP_HORIZON_ROUNDS=1 MOSAIC_TD_LAMBDA=0.7
          MARKERS="+bootstraptraj_h1_v1,+tdlambda0.7_v1" ;;
    b14b) export MOSAIC_BOOTSTRAP_SOURCE=trajectory MOSAIC_BOOTSTRAP_HORIZON_ROUNDS=1
          LAMBDA=0.5; CLI_ALLOWED="name,cache_file,value_target_lambda"
          MARKERS="+bootstraptraj_h1_v1" ;;
    b15)  if [ -z "$B15_SCALE" ]; then
            echo "UEBERSPRUNGEN $ARM: keine Skala s (weder B15_CONF_SCALE noch $CALIBRATION_ARTIFACT)"; exit 30
          fi
          # Prereg schreibt Dezimalkomma; beide Schreibweisen gelten.
          if ! grep -qF -e "$B15_SCALE" -e "${B15_SCALE/./,}" "$PREREG"; then
            echo "UEBERSPRUNGEN $ARM: Skala s = $B15_SCALE steht nicht in $PREREG -- par.19.5 verlangt die"
            echo "   Eichung in der Prereg, BEVOR trainiert wird. Nachtragen und den Arm mit ARMS=v35-b15 fahren."
            exit 30
          fi
          export MOSAIC_BOOTSTRAP_SOURCE=trajectory MOSAIC_BOOTSTRAP_HORIZON_ROUNDS=1 MOSAIC_BOOTSTRAP_TRAJ_CONF_SCALE="$B15_SCALE"
          MARKERS="+bootstraptraj_h1_conf${B15_SCALE}_v1" ;;
    *)    echo "STOPP: unbekannter Arm $ARM"; exit 40 ;;
  esac
  # Arm-Umgebung als JSON (nur gesetzte Arm-Variablen) fuer Schluessel-Abnahme und Manifest-Diff.
  local ARM_ENV_JSON
  ARM_ENV_JSON=$(python -X utf8 -c "import json,os,sys; print(json.dumps({n: os.environ[n] for n in sys.argv[1:] if n in os.environ}))" $ALL_ARM_VARS)
  echo ""
  echo "############################## ARM $ARM   Start $(date +%F' '%H:%M:%S)"
  echo "   Arm-Umgebung $ARM_ENV_JSON, value-target-lambda $LAMBDA, Marker $MARKERS"

  if [ "$RESUME_MODE" != "1" ]; then
    for f in models/alphazero_${ARM}*.pth "$ART"/quicklook_${ARM}_vs_${B02}_s*.json; do
      [ -f "$f" ] && { echo "STOPP $ARM: $f liegt schon (RESUME=1 zum Fortsetzen)"; exit 4; }
    done
  fi

  local VFILE_TRAIN="data/window_v35_${SHORT}_train.txt" VFILE_VAL="data/window_v35_${SHORT}_val.txt"
  local SPLIT_OUT="$ART/v35_${SHORT}_split.txt"

  step_begin "$ARM 1) Trainingsanteil (b02-Liste, val_frac $VF), Fenster-Schluessel"
  python -X utf8 tools/window_train_split.py --file-list "${WIN}.txt" --val-frac "$VF" \
    --val-pool "$MOSAIC_VAL_POOL" --encoder 2d --value-target-variant nortv \
    --train-list-out "$VFILE_TRAIN" --val-list-out "$VFILE_VAL" \
    > "$SPLIT_OUT"
  RC=$?
  cat "$SPLIT_OUT"
  [ $RC -eq 0 ] || { echo "STOPP $ARM: window_train_split.py mit Exit $RC"; exit 12; }
  diff -q <(grep -v '^#' "$VFILE_TRAIN") <(grep -v '^#' "${WIN}_train.txt") >/dev/null \
    || { echo "STOPP $ARM: Trainingsliste weicht von der b02-Trainingsliste ab"; exit 12; }
  diff -q <(grep -v '^#' "$VFILE_VAL") <(grep -v '^#' "${WIN}_val.txt") >/dev/null \
    || { echo "STOPP $ARM: Val-Liste weicht von der b02-Val-Liste ab (Val-Satz muss byte-gleich b02 sein)"; exit 12; }
  KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$SPLIT_OUT" | awk '{print $NF}')
  [ -n "$KEY" ] || { echo "STOPP $ARM: kein Schluessel"; exit 13; }
  [ "$KEY" != "$B02_KEY" ] || { echo "STOPP $ARM: Schluessel $KEY == b02-Schluessel -- Marker wirkt nicht"; exit 13; }
  CACHE="data/.cache_${KEY}.h5"
  step_end

  if [ -f "$CACHE" ]; then
    # Gleicher Schluessel heisst gleiche Daten (alle Knoepfe stehen im Schluessel); b14b trifft so den
    # b03-Monolithen. Nicht neu zusammenfuegen (--merge-out wuerde ihn neu schreiben).
    echo "   Monolith $CACHE liegt schon -- wird nach Stempel- und Schluessel-Pruefung wiederverwendet"
  else
    step_begin "$ARM 2) Bloecke fuer die 1.200 Fensterdateien (liegende werden uebersprungen)"
    python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
      --value-target-variant nortv --workers 6 --file-list "${WIN}.txt"
    RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
    [ $RC -eq 0 ] || { echo "STOPP $ARM: Blockbau mit Exit $RC"; exit 11; }
    step_end
    step_begin "$ARM 3) Merge des Trainingsanteils unter $KEY"
    python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
      --value-target-variant nortv --workers 6 --file-list "$VFILE_TRAIN" \
      --merge-out "$CACHE"
    RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
    [ $RC -eq 0 ] && [ -f "$CACHE" ] || { echo "STOPP $ARM: Monolith fehlt (Exit $RC)"; exit 14; }
    step_end
  fi

  step_begin "$ARM 4) Stempel und Schluessel-Abnahme"
  python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; print('   Stempel:',k); sys.exit(0 if k==sys.argv[2] else 16)" "$CACHE" "$KEY" \
    || { echo "STOPP $ARM: Stempel passt nicht zum Schluessel"; exit 16; }
  # Material mit derselben Funktion wie window_train_split.py, je in einem FRISCHEN Prozess:
  # MOSAIC_TD_LAMBDA wird beim Import von neural_net gelesen, ein In-Prozess-Umschalten saehe ihn nicht.
  python -X utf8 - "$KEY" "$CACHE" "$VFILE_TRAIN" "$B02_KEY" "$MARKERS" "$ARM_ENV_JSON" <<'PYEOF'
import json, os, subprocess, sys
import h5py
key, cache, train_list, b02_key, markers, arm_env_json = sys.argv[1:7]
arm_env = json.loads(arm_env_json)
markers = [m for m in markers.split(",") if m]
CHILD = r"""
import glob, json, os, sys
root = os.getcwd()
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, "engine", "py"))
from config import DATA_DIR
import corpus_dataset
wanted = [os.path.basename(l.strip()) for l in open(sys.argv[1], encoding="utf-8")
          if l.strip() and not l.startswith("#")]
have = {os.path.basename(f): f for f in glob.glob(os.path.join(str(DATA_DIR), "*.pkl"))}
files = sorted(have[n] for n in wanted)
k = corpus_dataset.window_cache_key(str(DATA_DIR), files, value_target_variant="nortv",
                                    encoder="2d", conjunction_head=False)
print("KEYJSON " + json.dumps({"key": k.key, "material": k.material}))
"""
def window_key(env):
    r = subprocess.run([sys.executable, "-X", "utf8", "-c", CHILD, train_list], env=env,
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        print(r.stderr); sys.exit(19)
    line = [l for l in r.stdout.splitlines() if l.startswith("KEYJSON ")][-1]
    return json.loads(line[len("KEYJSON "):])
on = window_key(dict(os.environ))
assert on["key"] == key, f"Schluessel {on['key']} != Schluessel des Monolithen {key}"
assert "+maskdicephasevalue_v1" in on["material"], "Wertmaske fehlt im Schluesselmaterial"
for m in markers:
    assert m in on["material"], f"Marker {m} fehlt im Schluesselmaterial"
assert on["material"].count("+bootstrap") == 1, "nicht genau ein Bootstrap-Marker im Material"
off_env = {k: v for k, v in os.environ.items() if k not in arm_env}
off = window_key(off_env)
print(f"   Schluessel mit Arm-Variablen {on['key']}, ohne {off['key']}, b02 {b02_key}")
assert off["key"] == b02_key, "ohne Arm-Variablen NICHT der b02-Schluessel -- weitere Abweichung"
fp = h5py.File(cache, "r").attrs.get("mosaic_env_fingerprint", "")
fp = (fp.decode() if isinstance(fp, bytes) else str(fp)).split(";")
assert "MOSAIC_MASK_DICE_PHASE_VALUE=1" in fp, "Monolith-Fingerabdruck ohne Maske"
for n, v in arm_env.items():
    assert f"{n}={v}" in fp, f"Monolith-Fingerabdruck ohne {n}={v}"
print("   Schluessel-Abnahme GRUEN")
PYEOF
  [ $? -eq 0 ] || { echo "STOPP $ARM: Schluessel-Abnahme ROT"; exit 19; }
  echo "##### FENSTER $ARM STEHT $(date +%F' '%H:%M:%S) -- Monolith $CACHE"
  step_end

  step_begin "$ARM 5) Training -- WARMSTART von $LOAD (Rezept b02, value-target-lambda $LAMBDA)"
  if [ "$RESUME_MODE" = "1" ] && [ -f "models/alphazero_${ARM}_resume.pth" ]; then
    echo "   RESUME: models/alphazero_${ARM}_resume.pth liegt -- train.py --resume"
    train_arm "$LAMBDA" --resume
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
    [ $? -eq 0 ] || { echo "STOPP $ARM (RESUME): finaler Stand ohne laufzeit im Manifest -- von Hand pruefen"; exit 20; }
    echo "   RESUME: Training $ARM ist durch -- uebersprungen"
    RC=0
  else
    for f in models/alphazero_${ARM}*.pth; do
      [ -f "$f" ] && { echo "STOPP $ARM: $f liegt ohne Zwischenstand -- von Hand pruefen"; exit 20; }
    done
    train_arm "$LAMBDA"
    RC=$?
  fi
  echo "   Training Exit $RC ($(date +%H:%M:%S))"
  [ $RC -eq 0 ] || { echo "STOPP $ARM: Training mit Exit $RC -- kein Schnellblick"; exit 20; }
  step_end

  step_begin "$ARM 6) Manifest-Diff des TRAININGS gegen $REF_TRAIN_MANIFEST"
  python -X utf8 - "$ARM" "$REF_TRAIN_MANIFEST" "$CLI_ALLOWED" "$LAMBDA" "$ARM_ENV_JSON" "${WIN}.txt" <<'PYEOF'
import glob, io, json, sys
arm, ref_path, allowed_cli, want_lambda, arm_env_json, want_list = sys.argv[1:7]
arm_env = json.loads(arm_env_json)
ps = sorted(glob.glob(f"models/manifest_train_{arm}_*.json"))
if not ps:
    print("   STOPP: kein Trainings-Manifest gefunden"); sys.exit(17)
m = json.load(io.open(ps[-1], encoding="utf-8"))
rm = json.load(io.open(ref_path, encoding="utf-8"))
new, ref = m.get("cli_args", {}) or {}, rm.get("cli_args", {}) or {}
allowed = set(x for x in allowed_cli.split(",") if x)
bad = []
for k in sorted(set(ref) | set(new)):
    if k not in ref:
        print(f"   cli_args.{k}: neu, Default -> {arm}={new.get(k)!r}")
        continue
    if ref.get(k) != new.get(k):
        mark = "" if k in allowed else "  <== STOPP"
        if k not in allowed:
            bad.append(k)
        print(f"   cli_args.{k}: v35-b02={ref.get(k)!r} -> {arm}={new.get(k)!r}{mark}")
lam = new.get("value_target_lambda")
if lam is None or abs(float(lam) - float(want_lambda)) > 1e-12:
    print(f"   value_target_lambda {lam!r} != {want_lambda}  <== STOPP"); bad.append("value_target_lambda(Wert)")
if str(new.get("file_list")).replace("\\", "/") != want_list:
    print(f"   file_list {new.get('file_list')!r} != {want_list!r}  <== STOPP"); bad.append("file_list(Wert)")
print(f"   Manifest {ps[-1]}; unerwartete cli-Abweichungen: {len(bad)} (erlaubt sind {sorted(allowed)})")
env, renv = m.get("mosaic_env") or {}, rm.get("mosaic_env") or {}
env_bad = []
for k in sorted(set(env) | set(renv)):
    if env.get(k) != renv.get(k):
        ok = k in arm_env and env.get(k) == arm_env[k]
        if not ok:
            env_bad.append(k)
        print(f"   mosaic_env.{k}: v35-b02={renv.get(k)!r} -> {arm}={env.get(k)!r}{'' if ok else '  <== STOPP'}")
for k, v in arm_env.items():
    if env.get(k) != v:
        print(f"   mosaic_env.{k}={env.get(k)!r} != {v!r}  <== STOPP"); env_bad.append(k + "(Wert)")
td = (m.get("python_constants") or {}).get("TD_LAMBDA")
want_td = float(arm_env.get("MOSAIC_TD_LAMBDA", "0.5"))
td_ok = td is not None and abs(float(td) - want_td) < 1e-12
print(f"   python_constants.TD_LAMBDA: {td!r} (erwartet {want_td}){'' if td_ok else '  <== STOPP'}")
if not td_ok:
    env_bad.append("TD_LAMBDA(Wert)")
print(f"   mosaic_env: {len(env_bad)} unerwartete Abweichungen (erlaubt: die Arm-Variablen {sorted(arm_env)})")
sys.exit(17 if bad else (18 if env_bad else 0))
PYEOF
  RC=$?
  [ $RC -eq 0 ] || { echo "STOPP $ARM: Manifest-Diff/mosaic_env mit Exit $RC -- KEIN Schnellblick"; exit 17; }
  step_end

  step_begin "$ARM 7) Vorfilter par.19.0 Punkt 2 (b02 gegen $ARM auf dem b02-Val-Satz)"
  local BEST_PTH MS PRE_OUT
  BEST_PTH=$(python -X utf8 tools/brier_best_checkpoint.py "$ARM" --ext pth)
  [ -n "$BEST_PTH" ] && [ -f "$BEST_PTH" ] || { echo "STOPP $ARM: kein Brier-bestes $ARM-Netz (.pth)"; exit 31; }
  MS=(models/manifest_train_${ARM}_*.json)
  PRE_OUT="$ART/checkpoint_val_eval_${ARM}_vs_b02.json"
  if [ "$RESUME_MODE" = "1" ] && [ -f "$PRE_OUT" ]; then
    echo "   RESUME: $PRE_OUT liegt schon -- wiederverwendet"
  else
    python -X utf8 -u tools/checkpoint_val_eval.py --checkpoints "$B02_BEST_PTH" "$BEST_PTH" \
      --val-list "${WIN}_val.txt" --train-manifest "${MS[${#MS[@]}-1]}" --out "$PRE_OUT"
    RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
    [ $RC -eq 0 ] && [ -f "$PRE_OUT" ] || { echo "STOPP $ARM: checkpoint_val_eval.py gescheitert"; exit 32; }
  fi
  # Referenz = erster Checkpoint = b02; Feld = b02 minus Arm. CI ganz UNTER 0: b02 hat den kleineren
  # Brier, der Arm ist schlechter -> abgeschlossen ohne Schnellblick.
  python -X utf8 - "$PRE_OUT" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
(path, lists), = d["differences_reference_minus_checkpoint"].items()
a = lists["all"]
ci = a["value_val_brier_diff_ci95"]
print(f"   Referenz {d['reference']} minus {path} (Val {d['val_list']['n_files']} Dateien, "
      f"Selbstpruefung {d.get('selfcheck_overall')}):")
print(f"   Val-Brier b02 minus Arm: {a['value_val_brier_diff']}, CI95 {ci}  (< 0 = Arm hat den GROESSEREN Brier)")
print(f"   Policy-CE gepoolt b02 minus Arm: {a['policy_val_loss_pooled_diff']}, CI95 {a['policy_val_loss_pooled_diff_ci95']}")
if ci is None:
    print("   kein CI -- Vorfilter nicht entscheidbar  <== STOPP"); sys.exit(32)
if ci[1] < 0:
    print("   CI GANZ UNTER 0: Arm schlechter -> abgeschlossen, KEIN Schnellblick (par.19.0 Punkt 2)"); sys.exit(34)
print("   CI nicht ganz unter 0 -> Schnellblick")
PYEOF
  RC=$?
  step_end
  [ $RC -eq 34 ] && { echo "ENDE $ARM: Vorfilter -- Arm schlechter als b02, kein Schnellblick"; exit 34; }
  [ $RC -eq 0 ] || { echo "STOPP $ARM: Vorfilter mit Exit $RC"; exit 32; }

  A=$(python -X utf8 tools/brier_best_checkpoint.py "$ARM" --ext onnx)
  [ $? -eq 0 ] && [ -n "$A" ] && [ -f "$A" ] || { echo "STOPP $ARM: brier_best_checkpoint.py findet kein Netz (.onnx)"; exit 15; }
  echo "##### TRAINING $ARM DURCH $(date +%F' '%H:%M:%S) -- Schnellblick mit $A"

  wait_for_free_cpu "Schnellblick $ARM"
  step_begin "$ARM 8) Schnellblick gegen $B02 (feste Laenge, Seeds $QUICK_SEEDS a $QUICK_PAIRS Paare)"
  for s in $QUICK_SEEDS; do
    quicklook "$s" || { echo "STOPP $ARM: Schnellblick Seed $s ohne Artefakt"; exit 21; }
  done
  step_end

  step_begin "$ARM 9) Lesart par.19.0 Punkt 4 (gepoolt)"
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
  exit 0
}

# --- Arme in der registrierten Reihenfolge (par.19) -----------------------------------------------
for ARM_NAME in $ARM_ORDER; do
  case " $ARMS_SELECTED " in *" $ARM_NAME "*) ;; *) continue ;; esac
  T0=$(date +%s)
  ( run_arm "$ARM_NAME" )
  RC=$?
  case $RC in
    0)  ST="durch (Schnellblick gelaufen)" ;;
    30) ST="UEBERSPRUNGEN (b15-Eichung fehlt oder nicht in der Prereg)" ;;
    34) ST="Vorfilter: schlechter als b02, kein Schnellblick" ;;
    *)  ST="STOPP Exit $RC" ;;
  esac
  echo "$ARM_NAME|$ST|$(( $(date +%s) - T0 ))" >> "$SUMMARY_FILE"
  echo "== Arm $ARM_NAME: $ST, $(( $(date +%s) - T0 )) s Wanduhr"
done

# --- Zusammenfassung aller Arme --------------------------------------------------------------------
echo ""
echo "########## v35-b11..b15-KETTE FERTIG $(date +%F' '%H:%M:%S) -- Zusammenfassung"
python -X utf8 - "$SUMMARY_FILE" "$ART" "$B02" "$QUICK_SEEDS" <<'PYEOF'
import glob, json, os, subprocess, sys
sys.path.insert(0, os.path.join(os.getcwd(), "tools"))
from gating_block_z import block_shares, block_z
summary, art, b02, seeds = sys.argv[1:5]
for line in open(summary, encoding="utf-8"):
    arm, status, wall = line.rstrip("\n").split("|")
    print(f"\n{arm}: {status} ({int(wall) / 3600:.2f} h Wanduhr)")
    ms = sorted(glob.glob(f"models/manifest_train_{arm}_*.json"))
    if ms:
        hist = json.load(open(ms[-1], encoding="utf-8")).get("epoch_history") or []
        b = [(e.get("value_val_brier"), i + 1) for i, e in enumerate(hist) if e.get("value_val_brier") is not None]
        if b:
            v, ep = min(b, key=lambda t: t[0])
            print(f"   Val-Brier beste Epoche {ep}: {v:.5f} ({os.path.basename(ms[-1])})")
    pre = f"{art}/checkpoint_val_eval_{arm}_vs_b02.json"
    if os.path.exists(pre):
        d = json.load(open(pre, encoding="utf-8"))
        (_, lists), = d["differences_reference_minus_checkpoint"].items()
        a = lists["all"]
        print(f"   Vorfilter Brier b02 minus Arm {a['value_val_brier_diff']}, CI95 {a['value_val_brier_diff_ci95']}")
    arts = [f"{art}/quicklook_{arm}_vs_{b02}_s{s}.json" for s in seeds.split()]
    arts = [p for p in arts if os.path.exists(p)]
    wins = games = 0
    shares = []
    for p in arts:
        d = json.load(open(p, encoding="utf-8"))
        wins += d["a_wins_total"]; games += d["n_games_total"]
        shares.extend(block_shares(p))
        z1 = block_z(block_shares(p))["z"]
        print(f"   {os.path.basename(p)}: {d['a_wins_total']}:{d['b_wins_total']} von {d['n_games_total']}, "
              f"Block-z {'n/a' if z1 is None else f'{z1:+.2f}'}")
    if len(arts) > 1 and games:
        z = block_z(shares)["z"]
        print(f"   gepoolt: {wins / games:.4f} ({wins} von {games}), Block-z {'n/a' if z is None else f'{z:+.2f}'}")
PYEOF
echo ""
echo "Wanduhr je Schritt (Arm, Schritt, Sekunden):"
cat "$STEPS_FILE"
rm -f "$SUMMARY_FILE" "$STEPS_FILE"
echo ""
echo "   Faellig danach (par.19): Lesart je Arm in die Prereg, sechs Standard-Kennzahlen je Seite aus den"
echo "   Sonden-Ausgaben oben und den plate_points_quicklook_*-Artefakten, Laufzeiten nach"
echo "   docs/measured_runtimes.md; ein 'spannender' Arm faehrt die volle Breite gegen b02 (par.19.0"
echo "   Punkt 4) NUR nach Koordinator-Entscheid."
