#!/usr/bin/env bash
# v35-Arm-Kette (EINE Datei): nach dem Ende von tools/night_v35_b02_chain.sh die Arme v35-b03, -b05,
# -b06, -b04, -b07, -b08 nacheinander auf dem b02-FENSTER trainieren und je Arm Tor 1 Seed 1 gegen
# den Generator v34-b01 fahren, Seed 2 nur ueber der Schwelle (Stufenform par.13).
# Registrierungen (verbindlich): evaluations/PREREG_v35_window.md
#   par.12  b02-Fenster (Dateiliste, Traeger-Manifest, Val 120, Seed 20260965, Rezept, Tor 1)
#   par.13  b03 k=1, b05 k=2, b06 k=3: MOSAIC_BOOTSTRAP_SOURCE=trajectory, MOSAIC_BOOTSTRAP_HORIZON_ROUNDS=k
#   par.14  b04: MOSAIC_BOOTSTRAP_SOURCE=margin, MOSAIC_BOOTSTRAP_MARGIN_SCALE=20
#   par.15  b07: --value-target-lambda 1.0, KEIN neuer Cache-Schluessel (gleicher Monolith wie b02)
#   par.16  b08: --weight-average ema; Vorab-Test Brier gemittelt gegen Brier-best, sonst kein Tor 1
# Vorlage: tools/night_v35_b02_chain.sh (Umgebung, Split, Merge, Stempel, Training, Manifest-Diff,
# Tor 1) und tools/night_v35_chain.sh.
#
# JE ARM in einer SUBSHELL (nichts leckt in den naechsten Arm): Arm-Variablen, Bloecke (nur bei neuem
# Schluessel), Split mit der b02-Fensterliste und dem b02-val_frac (Listen muessen gleich den b02-Listen
# sein), Schluessel-Pruefungen, Merge, Stempel, Training (Flags byte-gleich b02 bis auf --name und den
# Arm-Unterschied), Manifest-Diff gegen das NEUESTE models/manifest_train_v35-b02_*.json, gegatetes
# Netz, Tor 1 Seed 20261600, Schwelle (Block-z >= 1,96 ODER Siegquote >= 0,525) fuer Seed 20261601,
# Stufenregel 20261602 wie b02. Ein STOPP beendet nur den ARM, die Kette geht zum naechsten.
#
# SCHLUESSEL-REGELN: b03/b05/b06/b04 brauchen einen NEUEN Fenster-Schluessel (Marker im Material,
# engine/py/corpus_dataset.py:787-800; Block-Schluessel engine/py/file_cache_key.py:451-458), der sich
# ohne die Bootstrap-Variablen wieder auf den b02-Schluessel reduziert. b07/b08 muessen GENAU den
# b02-Schluessel treffen: lambda mischt erst im Training (train.py:1694, apply_value_target_lambda),
# window_cache_key hat keinen lambda-Parameter (corpus_dataset.py:459-461). Dort wird NICHT neu gebaut
# und NICHT neu zusammengefuegt (--merge-out wuerde den b02-Monolithen neu schreiben).
#
# KOSTEN (HERLEITUNG, nicht gemessen): je Arm mit neuem Schluessel rund 20 min Bloecke und Merge
# (par.13: 16 + 3 min) + 40 min Training (par.13: 37 min) + 1,5 h Tor 1 Seed 1 (par.12) = rund 2,5 h;
# b07/b08 ohne Bloecke rund 2,2 h. Sechs Arme rund 14,5 h, je Arm ueber der Schwelle +1,5 h fuer
# Seed 2 (+1,5 h fuer einen dritten Seed nach Stufenregel). Laufzeiten stehen je Schritt im Log.
#
# START: im Terminal-Tab mit Git-Bash, als DATEI:  bash tools/night_v35_arms_chain.sh
# KEINE PIPE dahinter, keine eigene Umleitung (weit ueber der 2-h-Grenze der Hintergrundaufgaben).
# Darf vor dem Ende der b02-Kette gestartet werden: sie wartet, bis kein Prozess mit
# night_v35_b02_chain in der Kommandozeile mehr laeuft (Bauform tools/night_v35_swarm.sh:32-40), und
# STOPPT dann, wenn das b02-Trainings-Manifest oder die b02-Fensterdateien fehlen.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

ART=evaluations/artifacts
SEED=20260965                                                # alle Arme einer Generation (par.12)
GEN=v34-b01                                                  # Generator = amtierender Champion
GEN_MODEL=models/alphazero_v34-b01_brierbest.onnx            # Tor-1-Gegner
LOAD=v34-b01_brierbest
N_VAL=120
SPEC=models/v34-b01_brierbest.spec.json                      # Tor 1 BEIDSEITS (par.12 wie par.11)
CARRIER=policy_carrier_manifest_v35_b02.json
WIN=data/window_v35_b02                                      # b02-Fensterdateien, NICHT neu ziehen
B02=v35-b02
SUMMARY_FILE=$(mktemp)

step_begin() {  # $1 Schrittname
  STEP_NAME="$1"; STEP_T0=$(date +%s)
  echo ""
  echo "== $1   Start $(date +%F' '%H:%M:%S)"
}
step_end() {
  echo "   Ende ${STEP_NAME}: $(date +%F' '%H:%M:%S), $(( $(date +%s) - STEP_T0 )) s Wanduhr"
}

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"

# --- 0) Warten auf das Ende der b02-Kette ----------------------------------------------------------
echo "########## v35-ARM-KETTE WARTET auf das Ende der b02-Kette $(date +%F' '%H:%M:%S)"
tick=0
while :; do
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '[n]ight_v35_b02_chain' }).Count" 2>/dev/null | tr -d '\r[:space:]')
  [ "$n" = "0" ] && break
  tick=$((tick + 1))
  [ $tick -gt 1800 ] && { echo "STOPP: b02-Kette nach 30 h noch nicht fertig"; exit 1; }
  [ $((tick % 10)) -eq 1 ] && echo "   b02-Kette laeuft noch (Antwort '${n}', $(date +%H:%M:%S))"
  sleep 60
done
echo "   b02-Kette beendet ($(date +%H:%M:%S))"

# --- Vorpruefungen (global; ein Fehler hier stoppt die GANZE Kette) --------------------------------
for f in "$GEN_MODEL" "models/alphazero_${LOAD}.pth" "$SPEC" "data/$CARRIER" \
         "${WIN}.txt" "${WIN}_train.txt" "${WIN}_val.txt" "${WIN}.valfrac" "$ART/v35_b02_split.txt" \
         engine/py/trajectory_bootstrap.py tools/brier_best_checkpoint.py tools/checkpoint_val_eval.py \
         tools/gating_block_z.py tools/paired_gating.py; do
  [ -f "$f" ] || { echo "STOPP: $f fehlt (b02-Kette nicht durch?)"; exit 2; }
done
REF_MANIFESTS=(models/manifest_train_${B02}_*.json)
REF_TRAIN_MANIFEST="${REF_MANIFESTS[${#REF_MANIFESTS[@]}-1]}"   # Glob sortiert: das neueste
[ -f "$REF_TRAIN_MANIFEST" ] || { echo "STOPP: kein models/manifest_train_${B02}_*.json -- b02 nicht trainiert"; exit 3; }
python -X utf8 -c "import config,sys; sys.exit(0 if (config.INPUT_SIZE,config.NUM_ACTIONS)==(888,414) else 3)" \
  || { echo "STOPP: config.py traegt nicht INPUT_SIZE 888 / NUM_ACTIONS 414"; exit 3; }
VF=$(tr -d '[:space:]' < "${WIN}.valfrac")
[ -n "$VF" ] || { echo "STOPP: ${WIN}.valfrac leer"; exit 3; }
NV=$(grep -vc '^#' "${WIN}_val.txt")
[ "$NV" = "$N_VAL" ] || { echo "STOPP: b02-Val-Liste hat $NV statt $N_VAL Dateien"; exit 3; }
B02_KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v35_b02_split.txt" | awk '{print $NF}')
[ -n "$B02_KEY" ] || { echo "STOPP: kein b02-Schluessel in $ART/v35_b02_split.txt"; exit 3; }
[ -f "data/.cache_${B02_KEY}.h5" ] || { echo "STOPP: b02-Monolith data/.cache_${B02_KEY}.h5 fehlt (b07/b08 brauchen ihn)"; exit 3; }
echo "== v35-ARM-KETTE   Start $(date +%F' '%H:%M:%S)"
echo "   Referenz-Manifest $REF_TRAIN_MANIFEST, b02-Schluessel $B02_KEY, val_frac $VF"

# --- Trainings-Umgebung = die der b02-Kette (night_v35_b02_chain.sh:99-110) -------------------------
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v34-b01-'
export MOSAIC_FEATURES_FROM_RUST=1
export MOSAIC_CARRIER_MANIFEST=$CARRIER
export MOSAIC_DATA_EXCLUDE='selfplay_v29-b11-probe_|selfplay_depth|selfplay_s4states|selfplay_tor2a|selfplay_probe-|selfplay_x35|selfplay_x35e2'
export MOSAIC_MASK_DICE_PHASE_VALUE=1
unset MOSAIC_MOON_TARGET_SOURCE
# Bootstrap-Knoepfe global AUS; nur die Subshell eines Arms setzt sie (file_cache_key.py:185-255).
unset MOSAIC_BOOTSTRAP_SOURCE MOSAIC_BOOTSTRAP_HORIZON_ROUNDS MOSAIC_BOOTSTRAP_MARGIN_SCALE MOSAIC_BOOTSTRAP_COHERENCE

wait_for_free_cpu "v35-Arm-Kette"

# --- Ein Arm --------------------------------------------------------------------------------------
# $1 Armname (v35-b0X), $2 Art (traj|margin|lambda|ema), $3 Parameter (k | b | lambda | -)
# Laeuft in einer Subshell: exit beendet nur den Arm. Exit 0 = Arm durch (mit Tor 1).
run_arm() {
  ARM="$1"; KIND="$2"; PARAM="$3"; SHORT="${ARM#v35-}"
  LAMBDA=0.7; EXTRA_FLAGS=(); NEWKEY=0; MARKER=""
  unset MOSAIC_BOOTSTRAP_SOURCE MOSAIC_BOOTSTRAP_HORIZON_ROUNDS MOSAIC_BOOTSTRAP_MARGIN_SCALE
  case "$KIND" in
    traj)   export MOSAIC_BOOTSTRAP_SOURCE=trajectory MOSAIC_BOOTSTRAP_HORIZON_ROUNDS="$PARAM"
            NEWKEY=1; MARKER="+bootstraptraj_h${PARAM}_v1" ;;
    margin) export MOSAIC_BOOTSTRAP_SOURCE=margin MOSAIC_BOOTSTRAP_MARGIN_SCALE="$PARAM"
            NEWKEY=1; MARKER="+bootstrapmargin_b${PARAM}_v1" ;;
    lambda) LAMBDA="$PARAM" ;;
    ema)    EXTRA_FLAGS=(--weight-average ema) ;;
    *)      echo "STOPP: unbekannte Arm-Art $KIND"; exit 40 ;;
  esac
  echo ""
  echo "############################## ARM $ARM ($KIND $PARAM)   Start $(date +%F' '%H:%M:%S)"
  echo "   MOSAIC_BOOTSTRAP_SOURCE=${MOSAIC_BOOTSTRAP_SOURCE-<unset>} HORIZON=${MOSAIC_BOOTSTRAP_HORIZON_ROUNDS-<unset>}" \
       "MARGIN_SCALE=${MOSAIC_BOOTSTRAP_MARGIN_SCALE-<unset>} lambda=$LAMBDA extra=${EXTRA_FLAGS[*]-}"

  for f in models/alphazero_${ARM}*.pth; do
    [ -f "$f" ] && { echo "STOPP $ARM: $f liegt schon (train.py wuerde ohnehin abbrechen)"; exit 4; }
  done
  if [ "$KIND" = "ema" ]; then
    # par.16: der Knopf wird parallel gebaut. Ohne ihn wird b08 uebersprungen.
    grep -q -- "--weight-average" train.py \
      || { echo "UEBERSPRUNGEN $ARM: train.py kennt --weight-average (noch) nicht"; exit 30; }
  fi

  local VFILE_TRAIN="data/window_v35_${SHORT}_train.txt" VFILE_VAL="data/window_v35_${SHORT}_val.txt"
  local SPLIT_OUT="$ART/v35_${SHORT}_split.txt"

  if [ "$NEWKEY" = "1" ]; then
    step_begin "$ARM 1) Bloecke fuers b02-Fenster (neuer Block-Schluessel wegen $MARKER)"
    python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
      --value-target-variant nortv --workers 6 --file-list "${WIN}.txt"
    RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
    [ $RC -eq 0 ] || { echo "STOPP $ARM: Blockbau mit Exit $RC"; exit 11; }
    step_end
  fi

  step_begin "$ARM 2) Trainingsanteil (b02-Liste, val_frac $VF), Fenster-Schluessel, Monolith"
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
    || { echo "STOPP $ARM: Val-Liste weicht von der b02-Val-Liste ab"; exit 12; }
  KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$SPLIT_OUT" | awk '{print $NF}')
  [ -n "$KEY" ] || { echo "STOPP $ARM: kein Schluessel"; exit 13; }
  CACHE="data/.cache_${KEY}.h5"
  if [ "$NEWKEY" = "1" ]; then
    [ "$KEY" != "$B02_KEY" ] || { echo "STOPP $ARM: Schluessel $KEY == b02-Schluessel -- Marker wirkt nicht"; exit 13; }
    python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
      --value-target-variant nortv --workers 6 --file-list "$VFILE_TRAIN" \
      --merge-out "$CACHE"
    RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
    [ $RC -eq 0 ] && [ -f "$CACHE" ] || { echo "STOPP $ARM: Monolith fehlt (Exit $RC)"; exit 14; }
  else
    # b07/b08: GLEICHER Schluessel wie b02, kein Neubau, kein Merge.
    [ "$KEY" = "$B02_KEY" ] || { echo "STOPP $ARM: Schluessel $KEY != b02-Schluessel $B02_KEY -- Umgebung weicht ab"; exit 13; }
    [ -f "$CACHE" ] || { echo "STOPP $ARM: b02-Monolith $CACHE fehlt"; exit 14; }
    echo "   Schluessel = b02-Schluessel $KEY, Monolith $CACHE wird wiederverwendet"
  fi
  python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; print('   Stempel:',k); sys.exit(0 if k==sys.argv[2] else 16)" "$CACHE" "$KEY" \
    || { echo "STOPP $ARM: Stempel passt nicht zum Schluessel"; exit 16; }
  # Schluessel-Abnahme: Material mit derselben Funktion wie window_train_split.py
  # (corpus_dataset.window_cache_key, volle Pfade aus config.DATA_DIR) einmal MIT und einmal OHNE die
  # Bootstrap-Variablen. Neuer Schluessel: Marker im Material, ohne Variablen = b02-Schluessel,
  # Monolith-Fingerabdruck traegt die Variablen. Gleicher Schluessel: kein Bootstrap-Marker.
  python -X utf8 - "$KEY" "$CACHE" "$VFILE_TRAIN" "$B02_KEY" "$MARKER" <<'PYEOF'
import glob, os, sys
root = os.getcwd()
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, "engine", "py"))
from config import DATA_DIR
import corpus_dataset, h5py
key, cache, train_list, b02_key, marker = sys.argv[1:6]
wanted = [os.path.basename(l.strip()) for l in open(train_list, encoding="utf-8")
          if l.strip() and not l.startswith("#")]
have = {os.path.basename(f): f for f in glob.glob(os.path.join(str(DATA_DIR), "*.pkl"))}
train_files = sorted(have[n] for n in wanted)
def wkey():
    return corpus_dataset.window_cache_key(str(DATA_DIR), train_files, value_target_variant="nortv",
                                           encoder="2d", conjunction_head=False)
names = ("MOSAIC_BOOTSTRAP_SOURCE", "MOSAIC_BOOTSTRAP_HORIZON_ROUNDS", "MOSAIC_BOOTSTRAP_MARGIN_SCALE")
on = wkey()
assert on.key == key, f"Schluessel {on.key} != Schluessel des Monolithen {key}"
assert "+maskdicephasevalue_v1" in on.material, "Wertmaske fehlt im Schluesselmaterial"
fp = h5py.File(cache, "r").attrs.get("mosaic_env_fingerprint", "")
fp = (fp.decode() if isinstance(fp, bytes) else str(fp)).split(";")
assert "MOSAIC_MASK_DICE_PHASE_VALUE=1" in fp, "Monolith-Fingerabdruck ohne Maske"
if marker:
    saved = {n: os.environ.pop(n) for n in names if n in os.environ}
    off = wkey()
    os.environ.update(saved)
    print(f"   Schluessel mit Arm-Variablen {on.key}, ohne {off.key}, b02 {b02_key}")
    assert marker in on.material, f"Marker {marker} fehlt im Schluesselmaterial"
    assert on.material.count("+bootstrap") == 1, "mehr als ein Bootstrap-Marker im Material"
    assert off.key == b02_key, "ohne Arm-Variablen NICHT der b02-Schluessel -- weitere Abweichung"
    for n, v in saved.items():
        assert f"{n}={v}" in fp, f"Monolith-Fingerabdruck ohne {n}={v}"
else:
    assert "+bootstrap" not in on.material, "Bootstrap-Marker im Material eines Arms ohne Bootstrap"
    assert not any(n in os.environ for n in names), "Bootstrap-Variable gesetzt"
print("   Schluessel-Abnahme GRUEN")
PYEOF
  [ $? -eq 0 ] || { echo "STOPP $ARM: Schluessel-Abnahme ROT"; exit 19; }
  echo "##### FENSTER $ARM STEHT $(date +%F' '%H:%M:%S) -- Monolith $CACHE"
  step_end

  # ABBRUCH? Fortsetzen mit demselben Aufruf plus --resume (Fingerabdruck-Waechter), von Hand.
  step_begin "$ARM 3) Training -- WARMSTART von $LOAD (Rezept b02, lambda $LAMBDA ${EXTRA_FLAGS[*]-})"
  python -X utf8 -u train.py --name "$ARM" --load "$LOAD" \
    --file-list "${WIN}.txt" --cache-file "$CACHE" \
    --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
    --val-frac "$VF" --encoder 2d --value-head wdl --value-target-variant nortv \
    --value-target-lambda "$LAMBDA" --ownership-head-2d --ownership-weight 0.0 \
    --moon-loss-weight 0.0 --opp-points-head \
    --destretch-a 0.0051 --destretch-b 1.9269 \
    --select-by-brier --fast-loader --seed $SEED ${EXTRA_FLAGS[@]+"${EXTRA_FLAGS[@]}"}
  RC=$?; echo "   Training Exit $RC ($(date +%H:%M:%S))"
  [ $RC -eq 0 ] || { echo "STOPP $ARM: Training mit Exit $RC -- kein Tor 1"; exit 20; }
  step_end

  step_begin "$ARM 4) Manifest-Diff des TRAININGS gegen $REF_TRAIN_MANIFEST"
  python -X utf8 - "$ARM" "$REF_TRAIN_MANIFEST" "$CARRIER" "$KIND" "$PARAM" <<'PYEOF'
import glob, io, json, sys
arm, ref_path, carrier, kind, param = sys.argv[1:6]
ps = sorted(glob.glob(f"models/manifest_train_{arm}_*.json"))
if not ps:
    print("   STOPP: kein Trainings-Manifest gefunden"); sys.exit(17)
m = json.load(io.open(ps[-1], encoding="utf-8"))
neu = m.get("cli_args", {}) or {}
ref = json.load(io.open(ref_path, encoding="utf-8")).get("cli_args", {}) or {}
erwartet = {"name", "cache_file"}
if kind == "lambda":
    erwartet.add("value_target_lambda")
if kind == "ema":
    erwartet.add("weight_average")
unerwartet = []
for k in sorted(set(ref) | set(neu)):
    if k not in ref:
        print(f"   cli_args.{k}: neu, Default -> {arm}={neu.get(k)!r}")
        continue
    if ref.get(k) != neu.get(k):
        mark = "" if k in erwartet else "  <== STOPP"
        if k not in erwartet:
            unerwartet.append(k)
        print(f"   cli_args.{k}: v35-b02={ref.get(k)!r} -> {arm}={neu.get(k)!r}{mark}")
# Der Arm-Unterschied muss auch WIRKLICH im Manifest stehen.
lam = neu.get("value_target_lambda")
want_lam = float(param) if kind == "lambda" else 0.7
if lam is None or abs(float(lam) - want_lam) > 1e-12:
    print(f"   value_target_lambda {lam!r} != {want_lam}  <== STOPP"); unerwartet.append("value_target_lambda(Wert)")
wa = neu.get("weight_average")
if kind == "ema":
    if wa != "ema":
        print(f"   weight_average {wa!r} != 'ema'  <== STOPP"); unerwartet.append("weight_average(Wert)")
elif wa not in (None, "", "none", "off", False):
    print(f"   weight_average {wa!r} in einem Arm ohne Mittelung  <== STOPP"); unerwartet.append("weight_average(Wert)")
print(f"   Manifest {ps[-1]}; unerwartete Abweichungen: {len(unerwartet)} (erlaubt sind {sorted(erwartet)})")
if unerwartet:
    sys.exit(17)
env = m.get("mosaic_env") or {}
names = ("MOSAIC_BOOTSTRAP_SOURCE", "MOSAIC_BOOTSTRAP_HORIZON_ROUNDS", "MOSAIC_BOOTSTRAP_MARGIN_SCALE")
got = {n: env.get(n) for n in names}
want = {"traj": {"MOSAIC_BOOTSTRAP_SOURCE": "trajectory", "MOSAIC_BOOTSTRAP_HORIZON_ROUNDS": param,
                 "MOSAIC_BOOTSTRAP_MARGIN_SCALE": None},
        "margin": {"MOSAIC_BOOTSTRAP_SOURCE": "margin", "MOSAIC_BOOTSTRAP_HORIZON_ROUNDS": None,
                   "MOSAIC_BOOTSTRAP_MARGIN_SCALE": param}}.get(kind, {n: None for n in names})
print(f"   mosaic_env: MOSAIC_MASK_DICE_PHASE_VALUE={env.get('MOSAIC_MASK_DICE_PHASE_VALUE')!r}, "
      f"MOSAIC_CARRIER_MANIFEST={env.get('MOSAIC_CARRIER_MANIFEST')!r}, Bootstrap {got}")
if env.get("MOSAIC_MASK_DICE_PHASE_VALUE") != "1" or env.get("MOSAIC_CARRIER_MANIFEST") != carrier \
   or got != want or env.get("MOSAIC_BOOTSTRAP_COHERENCE") is not None:
    print(f"   erwartet Bootstrap {want}  <== STOPP")
    sys.exit(18)
PYEOF
  RC=$?
  [ $RC -eq 0 ] || { echo "STOPP $ARM: Manifest-Diff/mosaic_env mit Exit $RC -- KEIN Tor 1"; exit 17; }
  step_end

  # Das zu gatende Netz: Brier-erstes Minimum aus dem Manifest (brier_best_checkpoint.py).
  A=$(python -X utf8 tools/brier_best_checkpoint.py "$ARM" --ext onnx)
  [ $? -eq 0 ] && [ -n "$A" ] && [ -f "$A" ] || { echo "STOPP $ARM: brier_best_checkpoint.py findet kein Netz"; exit 15; }

  if [ "$KIND" = "ema" ]; then
    # par.16 Vorab-Test: Brier des gemittelten Stands gegen den Brier-besten Einzelstand, gepaart ueber
    # Dateien. REFERENZ = ERSTER Checkpoint = der Brier-beste; Feld = Referenz minus Checkpoint, also
    # > 0 heisst "gemittelt hat den KLEINEREN Brier". Tor 1 nur, wenn das CI ganz ueber 0 liegt.
    step_begin "$ARM 5) Vorab-Test par.16: Brier gemittelt gegen Brier-best"
    BEST_PTH=$(python -X utf8 tools/brier_best_checkpoint.py "$ARM" --ext pth)
    AVG_PTH="models/alphazero_${ARM}_avg.pth"
    AVG_ONNX="models/alphazero_${ARM}_avg.onnx"
    for f in "$BEST_PTH" "$AVG_PTH" "$AVG_ONNX"; do
      [ -n "$f" ] && [ -f "$f" ] || { echo "STOPP $ARM: '$f' fehlt (Dateiname des gemittelten Stands pruefen)"; exit 31; }
    done
    MS=(models/manifest_train_${ARM}_*.json)
    PRE_OUT="$ART/checkpoint_val_eval_${ARM}_avg_vs_brierbest.json"
    python -X utf8 -u tools/checkpoint_val_eval.py --checkpoints "$BEST_PTH" "$AVG_PTH" \
      --val-list "${WIN}_val.txt" --train-manifest "${MS[${#MS[@]}-1]}" --out "$PRE_OUT"
    RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
    [ $RC -eq 0 ] && [ -f "$PRE_OUT" ] || { echo "STOPP $ARM: checkpoint_val_eval.py gescheitert"; exit 32; }
    python -X utf8 - "$PRE_OUT" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
diffs = d["differences_reference_minus_checkpoint"]
assert len(diffs) == 1, f"erwartet genau einen Vergleich, gefunden {list(diffs)}"
(path, lists), = diffs.items()
a = lists["all"]
ci = a["value_val_brier_diff_ci95"]
print(f"   Referenz {d['reference']} minus {path}: Brier-Diff {a['value_val_brier_diff']}, CI95 {ci}")
if ci is None or not (ci[0] > 0):
    print("   CI NICHT ganz ueber 0 -> KEIN Tor 1 (par.16)"); sys.exit(33)
print("   CI ganz ueber 0 -> Tor 1 mit dem gemittelten Stand")
PYEOF
    RC=$?
    step_end
    [ $RC -eq 0 ] || { echo "ENDE $ARM: Vorab-Test ohne Gewinn (Exit $RC) -- kein Tor 1"; exit 33; }
    A="$AVG_ONNX"
  fi
  echo "##### TRAINING $ARM DURCH $(date +%F' '%H:%M:%S) -- gegatet wird $A"

  gate() {  # $1 Seed (Gegner immer $GEN, Praefix gating, wie night_v35_b02_chain.sh:298-315)
    local OUT="$ART/gating_${ARM}_vs_${GEN}_s${1}.json"
    local G0
    G0=$(date +%s)
    if [ -f "$OUT" ]; then
      echo "   STOPP $ARM: $OUT liegt schon -- wird nicht ueberschrieben"; return 1
    fi
    echo ""
    echo "===== $ARM gegen $GEN, Seed $1   Start $(date +%F' '%H:%M:%S)"
    python -X utf8 -u tools/paired_gating.py \
      --model-a "$A" --spec-a "$SPEC" --model-b "$GEN_MODEL" --spec-b "$SPEC" \
      --name-a "$ARM" --name-b "$GEN" \
      --sims-a 400 --sims-b 400 --c-puct 1.5 \
      --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
      --seed "$1" --threads 10 --log-games --no-promote-winner --out "$OUT"
    local RCG=$?
    echo "   Exit $RCG ($(date +%H:%M:%S))"
    python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
    python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
      --out "$ART/plate_points_${ARM}_vs_${GEN}_s${1}.json"
    echo "   Ende Seed $1: $(date +%F' '%H:%M:%S), $(( $(date +%s) - G0 )) s Wanduhr"
    [ $RCG -eq 0 ] && [ -f "$OUT" ]
  }

  wait_for_free_cpu "Tor 1 $ARM"
  step_begin "$ARM 6) Tor 1 gegen $GEN, Seed 20261600 (Stufenform par.13)"
  gate 20261600 || { echo "STOPP $ARM: Tor 1 Seed 20261600 ohne Artefakt"; exit 21; }
  # Schwelle fuer Seed 2: Block-z >= +1,96 ODER Siegquote a_wins_total/n_games_total >= 0,525.
  python -X utf8 - "$ART/gating_${ARM}_vs_${GEN}_s20261600.json" <<'PYEOF'
import json, os, sys
sys.path.insert(0, os.path.join(os.getcwd(), "tools"))
from gating_block_z import block_shares, block_z
p = sys.argv[1]
d = json.load(open(p, encoding="utf-8"))
n = d.get("n_games_total") or 0
wr = d["a_wins_total"] / n if n else None
z = block_z(block_shares(p))["z"]
ok = (z is not None and z >= 1.96) or (wr is not None and wr >= 0.525)
print(f"   Seed 20261600: {d['a_wins_total']}:{d.get('b_wins_total')} von {n} Spielen, Siegquote "
      f"{wr if wr is None else round(wr, 4)}, Block-z {z if z is None else round(z, 2)} -> "
      f"{'Seed 2 FAELLIG' if ok else 'unter der Schwelle: ein Seed, nicht entschieden'}")
sys.exit(0 if ok else 1)
PYEOF
  if [ $? -eq 0 ]; then
    gate 20261601 || { echo "STOPP $ARM: Tor 1 Seed 20261601 ohne Artefakt"; exit 22; }
    python -X utf8 tools/gating_block_z.py "$ART/gating_${ARM}_vs_${GEN}_s20261600.json" "$ART/gating_${ARM}_vs_${GEN}_s20261601.json"
    N_SIG=$(python -X utf8 - "$ART/gating_${ARM}_vs_${GEN}_s20261600.json" "$ART/gating_${ARM}_vs_${GEN}_s20261601.json" <<'PYEOF'
import os, sys
sys.path.insert(0, os.path.join(os.getcwd(), "tools"))
from gating_block_z import block_shares, block_z
print(sum(1 for p in sys.argv[1:] if (block_z(block_shares(p))["z"] or 0) >= 1.96))
PYEOF
)
    echo "   Seeds einzeln >= +1,96: ${N_SIG:-?} von 2"
    if [ "$N_SIG" = "1" ]; then
      echo "   -> Widerspruch: dritter Seed 20261602 (Stufenregel, par.13 wie par.11)"
      gate 20261602 || { echo "STOPP $ARM: Tor 1 Seed 20261602 ohne Artefakt"; exit 23; }
      python -X utf8 tools/gating_block_z.py "$ART"/gating_${ARM}_vs_${GEN}_s2026160[012].json
    elif [ -z "$N_SIG" ]; then
      echo "   STOPP: Block-z nicht berechenbar -- Stufenregel von Hand anwenden"
    fi
  fi
  step_end
  echo "############################## ARM $ARM FERTIG $(date +%F' '%H:%M:%S)"
  exit 0
}

# --- Arme in der registrierten Reihenfolge (par.13-16) --------------------------------------------
for spec in "v35-b03 traj 1" "v35-b05 traj 2" "v35-b06 traj 3" "v35-b04 margin 20" \
            "v35-b07 lambda 1.0" "v35-b08 ema -"; do
  set -- $spec
  T0=$(date +%s)
  ( run_arm "$1" "$2" "$3" )
  RC=$?
  case $RC in
    0)  ST="durch" ;;
    30) ST="UEBERSPRUNGEN (Knopf --weight-average fehlt)" ;;
    33) ST="Vorab-Test ohne Gewinn, kein Tor 1" ;;
    *)  ST="STOPP Exit $RC" ;;
  esac
  echo "$1|$ST|$(( $(date +%s) - T0 ))" >> "$SUMMARY_FILE"
  echo "== Arm $1: $ST, $(( $(date +%s) - T0 )) s Wanduhr"
done

# --- Zusammenfassung aller Arme --------------------------------------------------------------------
echo ""
echo "########## v35-ARM-KETTE FERTIG $(date +%F' '%H:%M:%S) -- Zusammenfassung"
python -X utf8 - "$SUMMARY_FILE" "$ART" "$GEN" <<'PYEOF'
import glob, json, os, subprocess, sys
sys.path.insert(0, os.path.join(os.getcwd(), "tools"))
from gating_block_z import block_shares, block_z
summary, art, gen = sys.argv[1:4]
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
    r = subprocess.run([sys.executable, "-X", "utf8", "tools/brier_best_checkpoint.py", arm, "--ext", "onnx"],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode == 0:
        print(f"   Brier-bestes Netz: {r.stdout.strip()}")
    arts = sorted(glob.glob(f"{art}/gating_{arm}_vs_{gen}_s2026160[012].json"))
    for p in arts:
        d = json.load(open(p, encoding="utf-8"))
        n = d.get("n_games_total") or 0
        z = block_z(block_shares(p))["z"]
        wr = f"{d['a_wins_total'] / n:.4f}" if n else "?"
        print(f"   Tor 1 {os.path.basename(p)}: {d['a_wins_total']}:{d.get('b_wins_total')} von {n}, "
              f"Siegquote {wr}, Block-z {'n/a' if z is None else f'{z:+.2f}'}")
    if len(arts) > 1:
        pooled = []
        for p in arts:
            pooled.extend(block_shares(p))
        z = block_z(pooled)["z"]
        print(f"   gepoolt ({len(arts)} Seeds): Block-z {'n/a' if z is None else f'{z:+.2f}'}")
PYEOF
rm -f "$SUMMARY_FILE"
echo ""
echo "   Faellig danach (par.13-16): Verdikt je Arm (Stufenform), Vergleich mit b02 deskriptiv auf"
echo "   denselben Seeds, Epochenkurven (Erosion), Platt-B (b04, b07), Tor 2b aus den Logs, sechs"
echo "   Standard-Kennzahlen je Seite, Laufzeiten in die Prereg; Promotion NUR nach Nutzer-Entscheid."
