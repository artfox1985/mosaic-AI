#!/usr/bin/env bash
# v35-Kette fuer die Arme v35-b09 und v35-b10 (EINE Datei): nach dem Ende von
# tools/night_v35_b02_chain.sh UND tools/night_v35_arms_chain.sh zuerst b09 (Policy-Volumen: 4.000
# neue Policy-Partien @400 als eigene Klasse, Fenster 1.600, 800 Traeger), dann b10 (b02-Fenster
# unveraendert, alle 1.200 Dateien als Policy-Traeger, keine Erzeugung). Je Arm Offline-Vorabmessung
# gegen b02 auf dem byte-gleichen Val-Satz und Tor 1 gegen den Generator v34-b01 (Seed 2 nur ueber
# der Schwelle, Stufenregel wie die Arm-Kette).
# Registrierungen (verbindlich): evaluations/PREREG_v35_window.md
#   par.12  b02-Fenster (Dateiliste, Traeger-Manifest 400, Val 120, Seed 20260965, Rezept, Tor 1)
#   par.17  b09: Klasse policy-s400-vol (models/v35_b09.recipe.json, Seed-Basis 20263500, 4.000 Partien),
#           Fenster data/window_v35_b09.txt = b02 + 400 neue, Traeger 800 = 100+100+200+400,
#           MOSAIC_VAL_POOL auf die fuenf b02-Klassen, val_frac 120/1.600, Val-Satz byte-gleich b02,
#           Manifest-Diff erlaubt name, cache_file, file_list, val_frac, val_pool
#   par.18  b10: Traeger-Manifest = alle 1.200 Dateien von data/window_v35_b02.txt, Fenster, Pool und
#           val_frac wie b02, keine Bloecke, neuer Merge unter neuem Schluessel (Traegermenge im
#           Schluessel, engine/py/corpus_dataset.py:648-649), Manifest-Diff erlaubt name, cache_file
# Vorlagen: tools/night_v35_b02_chain.sh (Umgebung, Split, Merge, Stempel, Training, Tor 1),
# tools/night_v35_arms_chain.sh (Warten, Vorpruefung, Subshell je Arm, Schwelle fuer Seed 2,
# Zusammenfassung), tools/v35_b02_generate.sh (Rezept-/Wheel-Pruefung, Smoke mit Manifest-Abnahme).
#
# JE ARM in einer SUBSHELL: ein STOPP (exit) beendet nur den Arm, die Kette geht weiter.
# Die Trainings-Umgebung wird IN der Subshell gesetzt, bei b09 erst NACH der Erzeugung:
# self_play.py schreibt alle MOSAIC_* des Elternprozesses ins Manifest (selfplay_manifest.py:129),
# die Smoke-Abnahme verlangt dort genau die drei Rezept-Variablen.
#
# MOSAIC_DATA_EXCLUDE bleibt in BEIDEN Armen byte-gleich b02 (night_v35_b02_chain.sh:106). Das
# Pinning gegen die neue Klasse (par.17: "^selfplay_v34-b01-policy-s400-vol_" fuer laufende und
# folgende Ketten) traegt hier die explizite Dateiliste: train.py nimmt mit --file-list nur die
# gelisteten Dateien (train.py:1448-1462), window_train_split.py ebenso. Ein Zusatz in der Regex
# braeche bei b10 die Vorgabe "mosaic_env byte-gleich b02 bis auf das Traeger-Manifest".
#
# KOSTEN (HERLEITUNG aus docs/measured_runtimes.md Z. 538-548, nicht gemessen):
#   b09: Erzeugung 4.000 x 6,21 s = 24.840 s, rund 6,9 h exklusiv (kein Cache-Waechter daneben; mit
#        Waechter waren es 6,92 s, Z. 548), Smoke rund 1-2 min, Bloecke 400 x 0,79 s rund 5 min (Z. 542;
#        die 1.200 b02-Bloecke werden uebersprungen), Merge rund 4 min (165 s fuer 1.080 Dateien, Z. 543,
#        linear auf 1.480), Training rund 2.930 s (2.198 s bei 2,03 M Zustaenden, Z. 544, linear auf rund
#        2,7 M laut par.17), Offline rund 1 min (83,5 s fuer 3 Checkpoints, Z. 546), Tor 1 Seed 1
#        400 x 13,6 s = 5.440 s rund 1,5 h (exklusiv, Z. 545). Zusammen rund 9,4 h mit einem Seed.
#   b10: Manifest Sekunden, Split plus Merge rund 3 min (Z. 543), Training rund 37 min (Z. 544),
#        Offline rund 1 min, Tor 1 Seed 1 rund 1,5 h. Zusammen rund 2,2 h mit einem Seed.
#   Je Arm ueber der Schwelle +1,5 h fuer Seed 2 (+1,5 h fuer einen dritten Seed nach Stufenregel).
#
# START: im Terminal-Tab mit Git-Bash, als DATEI:  bash tools/night_v35_b09_b10_chain.sh
# KEINE PIPE dahinter, keine eigene Umleitung (weit ueber der 2-h-Grenze der Hintergrundaufgaben).
# Darf vor dem Ende der Vorgaenger gestartet werden: sie wartet, bis kein Prozess mit
# night_v35_b02_chain oder night_v35_arms_chain in der Kommandozeile mehr laeuft (Deckel 40 h).
#
# WIEDERAUFNAHME (2026-10-07, nach einem Rechner-Neustart mitten in der b09-Erzeugung):
#   RESUME=1 bash tools/night_v35_b09_b10_chain.sh
# Die Kette darf dann nach einem Abbruch an JEDER Stelle von vorn gestartet werden und faehrt nur die
# fehlenden Schritte:
#   - Fruehpruefung: statt "Klassendateien liegen schon -> Abbruch" wird gezaehlt; genau 400 Dateien
#     selfplay_v34-b01-policy-s400-vol_*.pkl -> Smoke und Erzeugung entfallen, sonst Abbruch mit Zaehlstand.
#   - b10 entfaellt, wenn models/alphazero_v35-b10_brierbest.onnx und zwei Artefakte
#     gating_v35-b10_vs_v34-b01_s<Seed>.json liegen ("b10 fertig, uebersprungen").
#   - run_b09: "liegt schon -> STOPP" wird "liegt schon -> wiederverwenden, Konsistenz pruefen"
#     (Fenster 1.600 = b02 + neue Klasse, Traeger-Manifest 800, Split-Listen mit Val byte-gleich b02,
#     Monolith mit passendem Stempel, Offline-Artefakt). Training: liegt _resume.pth -> train.py --resume;
#     liegt der finale Stand mit laufzeit im Manifest -> uebersprungen; sonst Reste -> STOPP.
#   - gate(): ein Seed mit fertigem Artefakt entfaellt; ein Zwischenstand <out>.partial.json wird von
#     paired_gating.py --resume fortgesetzt (--resume steht auch im Standardmodus im Aufruf: ohne
#     Zwischenstand laeuft das Gating normal).
# Ohne RESUME (oder RESUME=0) gilt das bisherige Verhalten mit allen STOPP-Pruefungen.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

ART=evaluations/artifacts
SEED=20260965                                                # alle Arme einer Generation (par.12)
GEN=v34-b01                                                  # Generator = amtierender Champion
GEN_MODEL=models/alphazero_v34-b01_brierbest.onnx            # Tor-1-Gegner und Generator der Erzeugung
LOAD=v34-b01_brierbest
N_VAL=120
SPEC=models/v34-b01_brierbest.spec.json                      # Tor 1 BEIDSEITS (par.12 wie par.11)
B02=v35-b02
B02_CARRIER=policy_carrier_manifest_v35_b02.json
B02_WIN=data/window_v35_b02                                  # b02-Fensterdateien, NICHT neu ziehen
B02_VAL_POOL='^selfplay_v34-b01-'
B09_RECIPE=models/v35_b09.recipe.json
B09_CLASS=policy-s400-vol
B09_SEED_BASE=20263500
B09_SMOKE_DIR=data/probe_v35b09_smoke
# b09: Pool = die fuenf b02-Klassen; die neue Klasse trifft NICHT (nach "policy" muss "_" folgen).
B09_VAL_POOL='^selfplay_v34-b01-(policy|policy-s400|policy-dice-v2-r1-s400|value-deviate-s400|value-excursion-s400)_'
B02_EXCLUDE='selfplay_v29-b11-probe_|selfplay_depth|selfplay_s4states|selfplay_tor2a|selfplay_probe-|selfplay_x35|selfplay_x35e2'
RESUME_MODE="${RESUME:-0}"                                   # Wiederaufnahme-Modus, siehe Kopf
case "$RESUME_MODE" in
  0|1) ;;
  *) echo "ABBRUCH: RESUME='$RESUME_MODE' -- erlaubt sind 0 und 1"; exit 1 ;;
esac
[ "$RESUME_MODE" = "1" ] && echo "########## RESUME=1: Wiederaufnahme-Modus (liegende Schritte werden geprueft und wiederverwendet)"
SUMMARY_FILE=$(mktemp)
STEPS_FILE=$(mktemp)

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

# --- Fruehe Pruefung VOR dem Warten (sonst merkt man einen Bedienfehler erst nach bis zu 40 h) -----
for f in "$B09_RECIPE" models/v35_generation.spec.json; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
if [ "$RESUME_MODE" = "1" ]; then
  NCLS=$(ls data/ | grep -c "^selfplay_${GEN}-${B09_CLASS}_.*\.pkl$")
  if [ "$NCLS" != "400" ]; then
    echo "ABBRUCH (RESUME=1): data/ traegt ${NCLS} statt 400 Dateien selfplay_${GEN}-${B09_CLASS}_*.pkl -- Erzeugung erst vervollstaendigen"; exit 1
  fi
  echo "RESUME=1: 400 Dateien selfplay_${GEN}-${B09_CLASS}_*.pkl liegen -- Smoke und Erzeugung von b09 entfallen"
elif ls data/ | grep -q "^selfplay_${GEN}-${B09_CLASS}_\|^manifest_${GEN}-${B09_CLASS}_"; then
  echo "ABBRUCH: data/ traegt schon Dateien der Klasse ${B09_CLASS} -- von Hand pruefen"; exit 1
fi

# --- 0) Warten auf das Ende der b02-Kette UND der Arm-Kette (Bauform night_v35_arms_chain.sh:65-76) -
echo "########## v35-b09/b10-KETTE WARTET auf das Ende von night_v35_b02_chain und night_v35_arms_chain $(date +%F' '%H:%M:%S)"
tick=0
while :; do
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '[n]ight_v35_b02_chain|[n]ight_v35_arms_chain' }).Count" 2>/dev/null | tr -d '\r[:space:]')
  [ "$n" = "0" ] && break
  tick=$((tick + 1))
  [ $tick -gt 2400 ] && { echo "STOPP: Vorgaenger-Ketten nach 40 h noch nicht fertig"; exit 1; }
  [ $((tick % 10)) -eq 1 ] && echo "   Vorgaenger-Kette(n) laufen noch (Antwort '${n}', $(date +%H:%M:%S))"
  sleep 60
done
echo "   Vorgaenger-Ketten beendet ($(date +%H:%M:%S))"

# --- Vorpruefungen (global; ein Fehler hier stoppt die GANZE Kette) --------------------------------
for f in "$GEN_MODEL" "models/alphazero_${LOAD}.pth" "$SPEC" "data/$B02_CARRIER" \
         "${B02_WIN}.txt" "${B02_WIN}_train.txt" "${B02_WIN}_val.txt" "${B02_WIN}.valfrac" \
         "$ART/v35_b02_split.txt" "$B09_RECIPE" models/v35_generation.spec.json \
         tools/brier_best_checkpoint.py tools/checkpoint_val_eval.py tools/gating_block_z.py \
         tools/paired_gating.py tools/generate_carrier_manifest.py tools/window_train_split.py \
         tools/build_cache_incremental.py; do
  [ -f "$f" ] || { echo "STOPP: $f fehlt (b02-Kette nicht durch?)"; exit 2; }
done
REF_MANIFESTS=(models/manifest_train_${B02}_*.json)
REF_TRAIN_MANIFEST="${REF_MANIFESTS[${#REF_MANIFESTS[@]}-1]}"   # Glob sortiert: das neueste
[ -f "$REF_TRAIN_MANIFEST" ] || { echo "STOPP: kein models/manifest_train_${B02}_*.json -- b02 nicht trainiert"; exit 3; }
python -X utf8 -c "import config,sys; sys.exit(0 if (config.INPUT_SIZE,config.NUM_ACTIONS)==(888,414) else 3)" \
  || { echo "STOPP: config.py traegt nicht INPUT_SIZE 888 / NUM_ACTIONS 414"; exit 3; }
B02_VF=$(tr -d '[:space:]' < "${B02_WIN}.valfrac")
[ -n "$B02_VF" ] || { echo "STOPP: ${B02_WIN}.valfrac leer"; exit 3; }
NW=$(grep -vc '^#' "${B02_WIN}.txt")
[ "$NW" = "1200" ] || { echo "STOPP: b02-Fensterliste hat $NW statt 1200 Dateien"; exit 3; }
NV=$(grep -vc '^#' "${B02_WIN}_val.txt")
[ "$NV" = "$N_VAL" ] || { echo "STOPP: b02-Val-Liste hat $NV statt $N_VAL Dateien"; exit 3; }
B02_KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v35_b02_split.txt" | awk '{print $NF}')
[ -n "$B02_KEY" ] || { echo "STOPP: kein b02-Schluessel in $ART/v35_b02_split.txt"; exit 3; }
B02_BEST_PTH=$(python -X utf8 tools/brier_best_checkpoint.py "$B02" --ext pth)
[ $? -eq 0 ] && [ -n "$B02_BEST_PTH" ] && [ -f "$B02_BEST_PTH" ] \
  || { echo "STOPP: kein Brier-bestes b02-Netz (.pth) -- Offline-Vorabmessung unmoeglich"; exit 3; }
echo "== v35-b09/b10-KETTE   Start $(date +%F' '%H:%M:%S)"
echo "   Referenz-Manifest $REF_TRAIN_MANIFEST, b02-Schluessel $B02_KEY, b02-val_frac $B02_VF, b02-Netz $B02_BEST_PTH"

# Bootstrap-Knoepfe global AUS (wie night_v35_arms_chain.sh:109); b02 lief ohne sie.
unset MOSAIC_BOOTSTRAP_SOURCE MOSAIC_BOOTSTRAP_HORIZON_ROUNDS MOSAIC_BOOTSTRAP_MARGIN_SCALE MOSAIC_BOOTSTRAP_COHERENCE

wait_for_free_cpu "v35-b09/b10-Kette"

# --- Gemeinsame Bausteine (laufen in der Subshell des Arms; ARM, A, CARRIER usw. dort gesetzt) ----

# Trainings-Umgebung = die der b02-Kette (night_v35_b02_chain.sh:99-110); nur Traeger-Manifest und
# Val-Pool sind Arm-Parameter. $1 Traeger-Manifest, $2 Val-Pool-Regex.
export_train_env() {
  export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
  export MOSAIC_VAL_POOL="$2"
  export MOSAIC_FEATURES_FROM_RUST=1
  export MOSAIC_CARRIER_MANIFEST="$1"
  # MOSAIC_DATA_EXCLUDE ist ein REGEX auf den Basename (corpus_dataset.py:521-525, train.py:1419).
  export MOSAIC_DATA_EXCLUDE="$B02_EXCLUDE"
  export MOSAIC_MASK_DICE_PHASE_VALUE=1
  unset MOSAIC_MOON_TARGET_SOURCE
  echo "   Trainings-Umgebung: MOSAIC_CARRIER_MANIFEST=$MOSAIC_CARRIER_MANIFEST MOSAIC_VAL_POOL=$MOSAIC_VAL_POOL"
}

# Stempel und Schluessel-Abnahme des Monolithen. $1 Schluessel, $2 Monolith, $3 Trainingsliste,
# $4 Traegerzahl soll, $5 b02-Schluessel ("" = kein Gegencheck ohne Traegerwechsel).
check_window_key() {
  python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; print('   Stempel:',k); sys.exit(0 if k==sys.argv[2] else 16)" "$2" "$1" \
    || { echo "STOPP $ARM: Stempel passt nicht zum Schluessel"; return 16; }
  # Material mit derselben Funktion wie window_train_split.py (corpus_dataset.window_cache_key, volle
  # Pfade aus config.DATA_DIR): Wertmaske im Material, kein Bootstrap-Marker, Traegermenge = Manifest,
  # Fingerabdruck traegt Maske und Traeger-Manifest. Mit $5: dieselbe Trainingsliste unter dem
  # b02-Traeger-Manifest muss den b02-Schluessel ergeben (einziger Unterschied = Traegermenge).
  python -X utf8 - "$1" "$2" "$3" "$4" "$MOSAIC_CARRIER_MANIFEST" "$B02_CARRIER" "$5" <<'PYEOF'
import glob, json, os, sys
root = os.getcwd()
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, "engine", "py"))
from config import DATA_DIR
import corpus_dataset, h5py
key, cache, train_list, n_carriers, carrier, b02_carrier, b02_key = sys.argv[1:8]
wanted = [os.path.basename(l.strip()) for l in open(train_list, encoding="utf-8")
          if l.strip() and not l.startswith("#")]
have = {os.path.basename(f): f for f in glob.glob(os.path.join(str(DATA_DIR), "*.pkl"))}
train_files = sorted(have[n] for n in wanted)
def wkey():
    return corpus_dataset.window_cache_key(str(DATA_DIR), train_files, value_target_variant="nortv",
                                           encoder="2d", conjunction_head=False)
on = wkey()
assert on.key == key, f"Schluessel {on.key} != Schluessel des Monolithen {key}"
assert "+maskdicephasevalue_v1" in on.material, "Wertmaske fehlt im Schluesselmaterial"
assert "+bootstrap" not in on.material, "Bootstrap-Marker im Material"
want = set(json.load(open(os.path.join(str(DATA_DIR), carrier), encoding="utf-8"))["policy_carrier_files"])
got = set(on.policy_carrier_set or ())
print(f"   Traegermenge im Schluessel: {len(got)} (soll {n_carriers}), gleich Manifest: {got == want}")
assert got == want and len(got) == int(n_carriers), "Traegermenge im Schluessel != Manifest"
fp = h5py.File(cache, "r").attrs.get("mosaic_env_fingerprint", "")
fp = (fp.decode() if isinstance(fp, bytes) else str(fp)).split(";")
assert "MOSAIC_MASK_DICE_PHASE_VALUE=1" in fp, "Monolith-Fingerabdruck ohne Maske"
assert f"MOSAIC_CARRIER_MANIFEST={carrier}" in fp, "Monolith-Fingerabdruck ohne das Traeger-Manifest des Arms"
if b02_key:
    saved = os.environ["MOSAIC_CARRIER_MANIFEST"]
    os.environ["MOSAIC_CARRIER_MANIFEST"] = b02_carrier
    off = wkey()
    os.environ["MOSAIC_CARRIER_MANIFEST"] = saved
    print(f"   dieselbe Liste mit b02-Traegern: {off.key}, b02-Schluessel {b02_key}")
    assert off.key == b02_key, "mit b02-Traegern NICHT der b02-Schluessel -- weitere Abweichung"
print("   Schluessel-Abnahme GRUEN")
PYEOF
  [ $? -eq 0 ] || { echo "STOPP $ARM: Schluessel-Abnahme ROT"; return 19; }
}

# Training mit den Flags von night_v35_b02_chain.sh:234-241. $1 Fensterliste, $2 Monolith, $3 val_frac,
# ab $4 optionale Zusatzflags (nur RESUME=1: --resume). Ohne $4 ist der Aufruf der bisherige.
train_arm() {
  python -X utf8 -u train.py --name "$ARM" --load "$LOAD" \
    --file-list "$1" --cache-file "$2" \
    --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
    --val-frac "$3" --encoder 2d --value-head wdl --value-target-variant nortv \
    --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 0.0 \
    --moon-loss-weight 0.0 --opp-points-head \
    --destretch-a 0.0051 --destretch-b 1.9269 \
    --select-by-brier --fast-loader --seed $SEED "${@:4}"
}

# Manifest-Diff gegen das neueste b02-Manifest. $1 erlaubte cli_args (Komma), $2 erlaubte
# mosaic_env-Abweichungen (Komma), $3 erwartete file_list, $4 erwarteter Val-Pool.
manifest_diff() {
  python -X utf8 - "$ARM" "$REF_TRAIN_MANIFEST" "$MOSAIC_CARRIER_MANIFEST" "$1" "$2" "$3" "$4" <<'PYEOF'
import glob, io, json, sys
arm, ref_path, carrier, allowed_cli, allowed_env, want_list, want_pool = sys.argv[1:8]
ps = sorted(glob.glob(f"models/manifest_train_{arm}_*.json"))
if not ps:
    print("   STOPP: kein Trainings-Manifest gefunden"); sys.exit(17)
m = json.load(io.open(ps[-1], encoding="utf-8"))
rm = json.load(io.open(ref_path, encoding="utf-8"))
neu, ref = m.get("cli_args", {}) or {}, rm.get("cli_args", {}) or {}
erlaubt = set(x for x in allowed_cli.split(",") if x)
bad = []
for k in sorted(set(ref) | set(neu)):
    if k not in ref:
        print(f"   cli_args.{k}: neu, Default -> {arm}={neu.get(k)!r}")
        continue
    if ref.get(k) != neu.get(k):
        mark = "" if k in erlaubt else "  <== STOPP"
        if k not in erlaubt:
            bad.append(k)
        print(f"   cli_args.{k}: v35-b02={ref.get(k)!r} -> {arm}={neu.get(k)!r}{mark}")
lam = neu.get("value_target_lambda")
if lam is None or abs(float(lam) - 0.7) > 1e-12:
    print(f"   value_target_lambda {lam!r} != 0.7  <== STOPP"); bad.append("value_target_lambda(Wert)")
if neu.get("weight_average") not in (None, "", "none", "off", False):
    print(f"   weight_average {neu.get('weight_average')!r}  <== STOPP"); bad.append("weight_average(Wert)")
if str(neu.get("file_list")).replace("\\", "/") != want_list:
    print(f"   file_list {neu.get('file_list')!r} != {want_list!r}  <== STOPP"); bad.append("file_list(Wert)")
if neu.get("val_pool") != want_pool:
    print(f"   val_pool {neu.get('val_pool')!r} != {want_pool!r}  <== STOPP"); bad.append("val_pool(Wert)")
print(f"   Manifest {ps[-1]}; unerwartete cli-Abweichungen: {len(bad)} (erlaubt sind {sorted(erlaubt)})")
env, renv = m.get("mosaic_env") or {}, rm.get("mosaic_env") or {}
env_ok = set(x for x in allowed_env.split(",") if x)
env_bad = []
for k in sorted(set(env) | set(renv)):
    if env.get(k) != renv.get(k):
        mark = "" if k in env_ok else "  <== STOPP"
        if k not in env_ok:
            env_bad.append(k)
        print(f"   mosaic_env.{k}: v35-b02={renv.get(k)!r} -> {arm}={env.get(k)!r}{mark}")
checks = [("MOSAIC_MASK_DICE_PHASE_VALUE", "1"), ("MOSAIC_CARRIER_MANIFEST", carrier),
          ("MOSAIC_VAL_POOL", want_pool)]
for k, v in checks:
    if env.get(k) != v:
        print(f"   mosaic_env.{k}={env.get(k)!r} != {v!r}  <== STOPP"); env_bad.append(k + "(Wert)")
print(f"   mosaic_env: {len(env_bad)} unerwartete Abweichungen (erlaubt {sorted(env_ok)})")
sys.exit(17 if bad else (18 if env_bad else 0))
PYEOF
}

# Offline-Vorabmessung (par.17/par.18 Punkt 2): Ergebnis ausgeben, KEIN Stopp.
# $1 Artefakt. Referenz = erster Checkpoint = b02, Feld = b02 minus Arm (> 0: Arm kleiner).
print_offline() {
  python -X utf8 - "$1" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
(path, lists), = d["differences_reference_minus_checkpoint"].items()
a = lists["all"]
print(f"   Referenz {d['reference']} minus {path} (Val {d['val_list']['n_files']} Dateien, "
      f"Selbstpruefung {d.get('selfcheck_overall')}):")
print(f"   Policy-CE gepoolt: {a['policy_val_loss_pooled_diff']}, CI95 {a['policy_val_loss_pooled_diff_ci95']}"
      f"  (> 0 = Arm hat die kleinere CE)")
print(f"   Val-Brier:         {a['value_val_brier_diff']}, CI95 {a['value_val_brier_diff_ci95']}")
for c in d.get("checkpoints", []):
    l = (c.get("lists") or {}).get("all") or {}
    print(f"   {c.get('path')}: Brier {l.get('value_val_brier')}, policy_val_loss {l.get('policy_val_loss')}, "
          f"pooled {l.get('policy_val_loss_pooled')}")
PYEOF
  true
}

gate() {  # $1 Seed (Gegner immer $GEN, Praefix gating, wie night_v35_arms_chain.sh:342-364)
  local OUT="$ART/gating_${ARM}_vs_${GEN}_s${1}.json"
  local G0
  G0=$(date +%s)
  if [ -f "$OUT" ]; then
    if [ "$RESUME_MODE" = "1" ]; then
      # paired_gating.py schreibt das Artefakt atomar (tmp + os.replace): liegt es, ist es vollstaendig.
      echo "   RESUME: $OUT liegt schon -- Seed $1 uebersprungen"
      if [ ! -f "$ART/plate_points_${ARM}_vs_${GEN}_s${1}.json" ]; then
        echo "   Auswertungen zu Seed $1 fehlen -- werden nachgezogen"
        python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
        python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
          --out "$ART/plate_points_${ARM}_vs_${GEN}_s${1}.json"
      fi
      return 0
    fi
    echo "   STOPP $ARM: $OUT liegt schon -- wird nicht ueberschrieben"; return 1
  fi
  echo ""
  echo "===== $ARM gegen $GEN, Seed $1   Start $(date +%F' '%H:%M:%S)"
  [ -f "${OUT}.partial.json" ] && echo "   Zwischenstand ${OUT}.partial.json liegt -- paired_gating.py --resume setzt dort fort"
  # --resume (2026-10-07): setzt einen liegenden Zwischenstand <out>.partial.json fort (Konfiguration
  # wird geprueft); ohne Zwischenstand laeuft das Gating normal. Darum auch im Standardmodus gesetzt.
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$A" --spec-a "$SPEC" --model-b "$GEN_MODEL" --spec-b "$SPEC" \
    --name-a "$ARM" --name-b "$GEN" \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$1" --threads 10 --log-games --no-promote-winner --out "$OUT" --resume
  local RCG=$?
  echo "   Exit $RCG ($(date +%H:%M:%S))"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_${ARM}_vs_${GEN}_s${1}.json"
  echo "   Ende Seed $1: $(date +%F' '%H:%M:%S), $(( $(date +%s) - G0 )) s Wanduhr"
  [ $RCG -eq 0 ] && [ -f "$OUT" ]
}

# Tor 1 in Stufenform wie night_v35_arms_chain.sh:366-404. Rueckgabe != 0 nur ohne Artefakt.
tor1() {
  wait_for_free_cpu "Tor 1 $ARM"
  step_begin "$ARM Tor 1 gegen $GEN, Seed 20261600 (Stufenform)"
  gate 20261600 || { echo "STOPP $ARM: Tor 1 Seed 20261600 ohne Artefakt"; return 21; }
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
    gate 20261601 || { echo "STOPP $ARM: Tor 1 Seed 20261601 ohne Artefakt"; return 22; }
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
      echo "   -> Widerspruch: dritter Seed 20261602 (Stufenregel, par.17/par.18 wie par.11)"
      gate 20261602 || { echo "STOPP $ARM: Tor 1 Seed 20261602 ohne Artefakt"; return 23; }
      python -X utf8 tools/gating_block_z.py "$ART"/gating_${ARM}_vs_${GEN}_s2026160[012].json
    elif [ -z "$N_SIG" ]; then
      echo "   STOPP: Block-z nicht berechenbar -- Stufenregel von Hand anwenden"
    fi
  fi
  step_end
}

# --- ARM v35-b09 (par.17) --------------------------------------------------------------------------
run_b09() {
  ARM=v35-b09
  local CARRIER=policy_carrier_manifest_v35_b09.json
  local WIN=data/window_v35_b09
  local SPLIT_OUT="$ART/v35_b09_split.txt"
  local CARRIER_LIST=data/policy_carrier_list_v35_b02.txt
  echo ""
  echo "############################## ARM $ARM (Policy-Volumen, par.17)   Start $(date +%F' '%H:%M:%S)"
  if [ "$RESUME_MODE" = "1" ]; then
    # RESUME: die "liegt schon -> STOPP"-Pruefungen werden je Schritt zu "wiederverwenden, pruefen"
    # (Fenster 1b, Traeger 1d, Split 1e, Monolith 1f, Training 1g, Offline 1h, Tor 1 je Seed).
    NCLS=$(ls data/ | grep -c "^selfplay_${GEN}-${B09_CLASS}_.*\.pkl$")
    [ "$NCLS" = "400" ] || { echo "STOPP $ARM (RESUME): $NCLS statt 400 Dateien der Klasse ${B09_CLASS}"; exit 4; }
    echo "   RESUME: 400 Dateien der Klasse ${B09_CLASS}; liegende Schritte werden geprueft und wiederverwendet"
  else
    for f in models/alphazero_${ARM}*.pth; do
      [ -f "$f" ] && { echo "STOPP $ARM: $f liegt schon (train.py wuerde ohnehin abbrechen)"; exit 4; }
    done
    for f in "data/$CARRIER" "${WIN}.txt"; do
      [ -f "$f" ] && { echo "STOPP $ARM: $f liegt schon -- wird NICHT ueberschrieben"; exit 4; }
    done
    if ls data/ | grep -q "^selfplay_${GEN}-${B09_CLASS}_\|^manifest_${GEN}-${B09_CLASS}_"; then
      echo "STOPP $ARM: data/ traegt schon Dateien der Klasse ${B09_CLASS}"; exit 4
    fi
    if [ -d "$B09_SMOKE_DIR" ] && [ -n "$(ls -A "$B09_SMOKE_DIR" 2>/dev/null)" ]; then
      echo "STOPP $ARM: $B09_SMOKE_DIR ist nicht leer -- Reste eines frueheren Smokes von Hand beiseitelegen"; exit 4
    fi
  fi
  # Keine MOSAIC_*-Variable ausser denen des Rezepts darf in die Erzeugung lecken (Smoke prueft es).

  step_begin "$ARM 1a) Rezept- und Wheel-Pruefung ($B09_RECIPE)"
  python -X utf8 - "$B09_RECIPE" "$B09_CLASS" "$B09_SEED_BASE" <<'PYEOF'
import json, sys
sys.path.insert(0, "tools")
import mosaic_rust
from recipe_config import load_recipe, expected_engine_config
path, cls, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
r = load_recipe(path)
d = json.loads(mosaic_rust.engine_config_json())
print(f"   engine_config: input_size {d.get('input_size')} num_actions {d.get('num_actions')} "
      f"contract {d.get('contract_hash')}; Rezept sha256 {r.sha256[:12]}")
if str(d.get("input_size")) != "888" or str(d.get("num_actions")) != "414":
    print("ABBRUCH: Wheel traegt nicht 888/414"); sys.exit(3)
assert list(r["classes"]) == [cls], f"Rezept traegt nicht genau die Klasse {cls}: {list(r['classes'])}"
c = r["classes"][cls]
print(f"   {cls}: version {c['version']}, seed {c['seed']}, games {c.get('games')}, "
      f"Waechter {expected_engine_config(r, cls)}")
assert (c["version"], c["seed"], c.get("games")) == (f"v34-b01-{cls}", seed, 4000), "version/seed/games"
# Byte-Gleichheit der Einstellung gegen policy-s400 aus models/v35_b02.recipe.json (nur Lesen).
b02 = load_recipe("models/v35_b02.recipe.json")
ref = dict(b02["classes"]["policy-s400"])
mine = dict(c)
for k in ("description", "version", "seed", "games"):
    ref.pop(k, None); mine.pop(k, None)
assert mine == ref, f"Klasse weicht von policy-s400 ab: {mine} gegen {ref}"
for sect in ("common", "env", "expect_engine_config"):
    assert r[sect] == b02[sect], f"Abschnitt {sect} weicht von models/v35_b02.recipe.json ab"
print("   Einstellung byte-gleich policy-s400 (bis auf version, seed, games), common/env/Waechter gleich")
PYEOF
  [ $? -eq 0 ] || { echo "STOPP $ARM: Rezept- oder Wheel-Pruefung rot"; exit 3; }
  step_end

  # RESUME: Smoke und Erzeugung entfallen (400 Klassendateien oben gezaehlt). Sonst der bisherige Ablauf.
  if [ "$RESUME_MODE" = "1" ]; then
    echo ""
    echo "== $ARM 1a) Smoke und Erzeugung: RESUME, 400 Dateien selfplay_${GEN}-${B09_CLASS}_*.pkl liegen -- uebersprungen"
  else
  step_begin "$ARM 1a) Smoke (10 Partien nach $B09_SMOKE_DIR)"
  MOSAIC_DATA_DIR="$B09_SMOKE_DIR" python -X utf8 -u self_play.py --recipe "$B09_RECIPE" --class "$B09_CLASS" \
    --games 10 --version "smoke-v35b09-$B09_CLASS"
  RC=$?
  echo "   Smoke Exit $RC ($(date +%H:%M:%S)), Dateien: $(ls "$B09_SMOKE_DIR" 2>/dev/null | grep -c "^selfplay_smoke-v35b09-${B09_CLASS}_")"
  [ $RC -eq 0 ] || { echo "STOPP $ARM: Smoke rot -- keine Erzeugung"; exit 11; }
  # Manifest-Abnahme wie tools/v35_b02_generate.sh:73-146 (Klasse policy-s400), plus Laufzeit-Felder.
  python -X utf8 - "$B09_SMOKE_DIR" "$B09_CLASS" "$B09_SEED_BASE" <<'PYEOF'
import glob, json, os, sys
smoke_dir, cls, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
ms = sorted(glob.glob(os.path.join(smoke_dir, f"manifest_smoke-v35b09-{cls}_*.json")))
if not ms:
    print(f"   ROT: kein Manifest manifest_smoke-v35b09-{cls}_*.json in {smoke_dir}"); sys.exit(1)
m = json.load(open(ms[-1], encoding="utf-8"))
cli, ec = m.get("cli_args", {}), m.get("engine_config", {})
spec = (m.get("spec_file") or {}).get("content", {})
rec = m.get("recipe") or {}
env = {k: v for k, v in (m.get("mosaic_env") or {}).items() if k != "MOSAIC_DATA_DIR"}
lz = m.get("laufzeit") or {}
checks = [
    ("cli_args.sims", cli.get("sims"), 400),
    ("cli_args.seed", cli.get("seed"), seed),
    ("engine_config.tau_tiebreak_q", ec.get("tau_tiebreak_q"), 2),
    ("spec_file.content.r5_net_sims", spec.get("r5_net_sims"), 400),
    ("spec_file.content.r5_net_solver", spec.get("r5_net_solver"), 0),
    ("engine_config.r5_net_solver", ec.get("r5_net_solver"), False),
    ("engine_config.tie_mirror_p", ec.get("tie_mirror_p"), 0.5),
    ("engine_config.label_rng_split", ec.get("label_rng_split"), True),
    ("engine_config.excursion_reshuffle", ec.get("excursion_reshuffle"), True),
    ("engine_config.single_pass_other_val", ec.get("single_pass_other_val"), True),
    ("cli_args.model", os.path.basename(str(cli.get("model", "")).replace("\\", "/")),
     "alphazero_v34-b01_brierbest.onnx"),
    ("cli_args.spec", cli.get("spec"), "models/v35_generation.spec.json"),
    ("cli_args.threads", cli.get("threads"), 11),
    ("recipe.class", rec.get("class"), cls),
    ("recipe.engine_config_check.deviations", (rec.get("engine_config_check") or {}).get("deviations"), []),
    ("mosaic_env ohne MOSAIC_DATA_DIR", env,
     {"MOSAIC_STACK_DRAW_RESEARCH": "1", "MOSAIC_SINGLE_PASS_OTHER_VAL": "1", "MOSAIC_R5_NET_SOLVER": "0"}),
    ("laufzeit.partien", lz.get("partien"), 10),
    # Klasse policy-s400 (tools/v35_b02_generate.sh:113-117)
    ("engine_config.excursion_kl_weight", ec.get("excursion_kl_weight"), 0),
    ("engine_config.dome_dice", ec.get("dome_dice"), 0),
    ("cli_args.deviate_prob", cli.get("deviate_prob"), 1.0),
    ("cli_args.excursion_prob", cli.get("excursion_prob"), 0.0),
    ("cli_args.pcr_full_prob", cli.get("pcr_full_prob"), None),
    # Laufzeit-Felder (CLAUDE.md "Laufzeiten messen"); cpu_s darf None sein (Kinderzeiten fehlen
    # unter Windows, manifest_v34-b01-policy-s400_*: cpu_s None mit cpu_s_hinweis), muss aber stehen.
    ("laufzeit hat wanduhr_s/threads/s_je_partie",
     all(lz.get(k) is not None for k in ("wanduhr_s", "threads", "s_je_partie")), True),
    ("laufzeit hat cpu_s", "cpu_s" in lz, True),
]
bad = [(n, got, want) for n, got, want in checks if got != want]
for n, got, want in checks:
    print(f"   {'ok ' if got == want else 'ROT'} {n} = {got!r}" + ("" if got == want else f" (erwartet {want!r})"))
print(f"   Manifest {ms[-1]}: {len(checks) - len(bad)}/{len(checks)} gruen, "
      f"{lz.get('s_je_partie')} s je Partie im Smoke")
sys.exit(1 if bad else 0)
PYEOF
  [ $? -eq 0 ] || { echo "STOPP $ARM: Smoke-Manifest rot -- keine Erzeugung"; exit 11; }
  step_end

  step_begin "$ARM 1a) Erzeugung $B09_CLASS (4.000 Partien @400 Modus 2, Seed-Basis $B09_SEED_BASE)"
  python -X utf8 -u self_play.py --recipe "$B09_RECIPE" --class "$B09_CLASS"
  RC=$?
  NF=$(ls data/ | grep -c "^selfplay_${GEN}-${B09_CLASS}_.*\.pkl$")
  echo "   Erzeugung Exit $RC ($(date +%H:%M:%S)), Dateien: $NF"
  [ $RC -eq 0 ] || { echo "STOPP $ARM: Erzeugung mit Exit $RC"; exit 12; }
  [ "$NF" = "400" ] || { echo "STOPP $ARM: $NF statt 400 Dateien der Klasse $B09_CLASS"; exit 12; }
  python -X utf8 - "$GEN" "$B09_CLASS" "$B09_SEED_BASE" <<'PYEOF'
import glob, json, sys
gen, cls, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
ms = sorted(glob.glob(f"data/manifest_{gen}-{cls}_*.json"))
if not ms:
    print("   HINWEIS: kein Erzeugungs-Manifest gefunden"); sys.exit(0)
m = json.load(open(ms[-1], encoding="utf-8"))
c = m.get("cli_args") or {}
print(f"   Manifest {ms[-1]}: seed {c.get('seed')} (soll {seed}), games {c.get('games')}, "
      f"Abweichungen {((m.get('recipe') or {}).get('engine_config_check') or {}).get('deviations')}, "
      f"laufzeit {m.get('laufzeit')}")
PYEOF
  step_end
  fi   # Ende "kein RESUME": Smoke und Erzeugung

  # Trainings-Umgebung ERST JETZT (Kopf): b02-Umgebung, Traeger-Manifest b09, Val-Pool der fuenf b02-Klassen.
  export_train_env "$CARRIER" "$B09_VAL_POOL"
  wait_for_free_cpu "$ARM Fenster"

  # Fensterliste VOR den Bloecken (Abweichung von der Auftragsreihenfolge): build_cache_incremental.py
  # braucht eine Dateiliste, und so laufen die Bloecke gleich ueber das ganze Fenster.
  step_begin "$ARM 1b) Fensterliste ${WIN}.txt (b02 1.200 + $B09_CLASS 400 = 1.600)"
  if [ "$RESUME_MODE" = "1" ] && [ -f "${WIN}.txt" ]; then
    echo "   RESUME: ${WIN}.txt liegt schon -- wiederverwenden, Konsistenz pruefen"
    python -X utf8 - "$GEN" "$B09_CLASS" "$B02_WIN" "$WIN" "$N_VAL" <<'PYEOF'
import glob, os, re, sys
gen, cls, b02_win, win, n_val = sys.argv[1:6]
rd = lambda p: [l.strip() for l in open(p, encoding="utf-8") if l.strip() and not l.startswith("#")]
b02 = rd(f"{b02_win}.txt")
new = sorted(os.path.basename(p) for p in glob.glob(f"data/selfplay_{gen}-{cls}_*.pkl"))
assert len(b02) == 1200 and len(new) == 400, ("b02-Fenster / neue Klasse", len(b02), len(new))
have = rd(f"{win}.txt")
# Gleiche Bauvorschrift wie der Fensterbau unten: b02-Fenster, dann die neue Klasse sortiert.
assert have == b02 + new, (f"Fensterliste weicht ab: {len(have)} Eintraege, erwartet 1600 "
                           f"= b02 + neue Klasse in Bau-Reihenfolge")
assert len(set(have)) == 1600, "Doppelte im Fenster"
assert all(os.path.exists(os.path.join("data", b)) for b in have), "Datei fehlt"
excl = os.environ.get("MOSAIC_DATA_EXCLUDE", "")
assert not [b for b in have if excl and re.search(excl, b)], "Fensterdatei kollidiert mit MOSAIC_DATA_EXCLUDE"
pool = os.environ["MOSAIC_VAL_POOL"]
assert {b for b in have if re.search(pool, b)} == set(b02), "Val-Pool trifft nicht genau das b02-Fenster"
vf = f"{int(n_val) / len(have):.8f}"
vpath = f"{win}.valfrac"
if os.path.exists(vpath):
    got = open(vpath, encoding="utf-8").read().strip()
    assert got == vf, f"{vpath} traegt {got}, erwartet {vf}"
else:
    open(vpath, "w", encoding="utf-8").write(f"{vf}\n")
    print(f"   {vpath} fehlte -- nachgezogen ({vf})")
print(f"   {win}.txt: 1600 Dateien = b02 1.200 + {cls} 400, Val-Pool trifft genau b02, val_frac {vf} -- GRUEN")
PYEOF
    [ $? -eq 0 ] || { echo "STOPP $ARM (RESUME): liegende Fensterliste ${WIN}.txt passt nicht -- von Hand beiseitelegen"; exit 13; }
  else
  python -X utf8 - "$GEN" "$B09_CLASS" "$B02_WIN" "$WIN" "$N_VAL" <<'PYEOF'
import glob, os, re, sys
gen, cls, b02_win, win, n_val = sys.argv[1:6]
b02 = [l.strip() for l in open(f"{b02_win}.txt", encoding="utf-8") if l.strip() and not l.startswith("#")]
assert len(b02) == 1200 and len(set(b02)) == 1200, ("b02-Fenster", len(b02))
new = sorted(os.path.basename(p) for p in glob.glob(f"data/selfplay_{gen}-{cls}_*.pkl"))
assert len(new) == 400, ("neue Klasse", len(new))
allf = b02 + new
assert len(allf) == 1600 and len(set(allf)) == 1600, "Doppelte im Fenster"
assert all(os.path.exists(os.path.join("data", b)) for b in allf), "Datei fehlt"
excl = os.environ.get("MOSAIC_DATA_EXCLUDE", "")
hit = [b for b in allf if excl and re.search(excl, b)]
assert not hit, ("Fensterdatei kollidiert mit MOSAIC_DATA_EXCLUDE", hit[:5])
pool = os.environ["MOSAIC_VAL_POOL"]
pool_hits = [b for b in allf if re.search(pool, b)]
# Val-Garantie (par.17): der Pool trifft GENAU die 1.200 b02-Dateien und keine neue.
assert set(pool_hits) == set(b02), ("Val-Pool trifft nicht genau das b02-Fenster",
                                    len(pool_hits), [b for b in new if re.search(pool, b)][:3])
with open(f"{win}.txt", "w", encoding="utf-8", newline="\n") as fh:
    fh.write(f"# v35-b09-Fenster (PREREG_v35_window.md par.17): 1.600 Dateien = b02-Fenster 1.200 "
             f"({b02_win}.txt) + {cls} 400, alles Generator {gen} @400 Modus 2\n")
    fh.write("\n".join(allf) + "\n")
vf = int(n_val) / len(allf)
open(f"{win}.valfrac", "w", encoding="utf-8").write(f"{vf:.8f}\n")
print(f"   {win}.txt: {len(allf)} Dateien; Val-Pool trifft {len(pool_hits)}; val_frac {vf:.8f} fuer {n_val} Val-Dateien")
PYEOF
  [ $? -eq 0 ] || { echo "STOPP $ARM: Fensterbau gescheitert"; exit 13; }
  fi   # Ende Fensterliste bauen / (RESUME) pruefen
  VF=$(tr -d '[:space:]' < "${WIN}.valfrac")
  step_end

  step_begin "$ARM 1c) Bloecke fuers b09-Fenster (die 400 neuen; liegende b02-Bloecke werden uebersprungen)"
  python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
    --value-target-variant nortv --workers 6 --file-list "${WIN}.txt"
  RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
  [ $RC -eq 0 ] || { echo "STOPP $ARM: Blockbau mit Exit $RC"; exit 14; }
  step_end

  step_begin "$ARM 1d) Traeger-Manifest data/$CARRIER (b02-Traeger 400 + $B09_CLASS 400 = 800)"
  # b02-Traeger als Liste (Quelle data/$B02_CARRIER), dann generate_carrier_manifest.py:
  # --from-list schraenkt die Kandidaten auf genau diese 400 ein, --n-files 400 nimmt sie alle
  # (je Stratum eine Datei, Stratumgroesse 1); --include-glob nimmt die neue Klasse vollstaendig.
  # RESUME: ein liegendes Manifest wird nicht neu erzeugt; die Konsistenzpruefung unten (800 =
  # 100+100+200+400, b02-Traeger plus neue Klasse) laeuft in beiden Faellen.
  if [ "$RESUME_MODE" = "1" ] && [ -f "data/$CARRIER" ]; then
    echo "   RESUME: data/$CARRIER liegt schon -- wiederverwenden, Konsistenz unten"
  else
  python -X utf8 - "data/$B02_CARRIER" "$CARRIER_LIST" <<'PYEOF'
import json, sys
src, out = sys.argv[1:3]
f = sorted(json.load(open(src, encoding="utf-8"))["policy_carrier_files"])
assert len(f) == 400 and len(set(f)) == 400, ("b02-Traeger", len(f))
with open(out, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(f"# Policy-Traeger von v35-b02 ({src}), Kandidatenliste fuer policy_carrier_manifest_v35_b09.json (par.17)\n")
    fh.write("\n".join(f) + "\n")
print(f"   {out}: {len(f)} b02-Traeger")
PYEOF
  [ $? -eq 0 ] || { echo "STOPP $ARM: b02-Traegerliste nicht lesbar"; exit 15; }
  python -X utf8 tools/generate_carrier_manifest.py \
    --pattern "selfplay_${GEN}-*.pkl" --from-list "$CARRIER_LIST" --n-files 400 --seed $SEED \
    --include-glob "selfplay_${GEN}-${B09_CLASS}_*.pkl" \
    --out "$CARRIER"
  [ $? -eq 0 ] || { echo "STOPP $ARM: generate_carrier_manifest.py gescheitert"; exit 15; }
  fi   # Ende Traeger-Manifest erzeugen / (RESUME) wiederverwenden
  python -X utf8 - "$CARRIER" "$B02_CARRIER" "$GEN" "$B09_CLASS" <<'PYEOF'
import json, sys
name, b02name, gen, cls = sys.argv[1:5]
f = json.load(open(f"data/{name}", encoding="utf-8"))["policy_carrier_files"]
b02 = set(json.load(open(f"data/{b02name}", encoding="utf-8"))["policy_carrier_files"])
pol = [x for x in f if x.startswith(f"selfplay_{gen}-policy_")]
s400 = [x for x in f if x.startswith(f"selfplay_{gen}-policy-s400_")]
dice = [x for x in f if x.startswith(f"selfplay_{gen}-policy-dice-v2-r1-s400_")]
vol = [x for x in f if x.startswith(f"selfplay_{gen}-{cls}_")]
print(f"   Manifest: {len(f)} Traeger = {len(pol)} policy_ + {len(s400)} policy-s400_ + "
      f"{len(dice)} policy-dice-v2-r1-s400_ + {len(vol)} {cls}_")
assert (len(f), len(pol), len(s400), len(dice), len(vol)) == (800, 100, 100, 200, 400)
assert len(set(f)) == len(f), "Doppelte im Manifest"
assert b02 <= set(f) and set(f) - b02 == set(vol), "Manifest != b02-Traeger + neue Klasse"
PYEOF
  [ $? -eq 0 ] || { echo "STOPP $ARM: Traeger-Manifest traegt nicht 800 = 100+100+200+400"; exit 15; }
  step_end

  step_begin "$ARM 1e) Split (val_frac $VF, Val-Pool der fuenf b02-Klassen), Val-Satz gegen b02"
  # RESUME: liegen beide Listen und ein Split-Protokoll MIT Schluessel (window_train_split.py druckt ihn
  # erst nach dem Schreiben der Listen, Z. 96-107), wird der Split wiederverwendet; die Pruefungen
  # unten (Val 120 byte-gleich b02, Trainingsanteil = b02 + neue, Schluessel != b02) laufen immer.
  if [ "$RESUME_MODE" = "1" ] && [ -f "${WIN}_train.txt" ] && [ -f "${WIN}_val.txt" ] \
     && grep -q "Fenster-Schluessel des Trainingsanteils: [0-9a-f]" "$SPLIT_OUT" 2>/dev/null; then
    echo "   RESUME: ${WIN}_train.txt, ${WIN}_val.txt und $SPLIT_OUT liegen schon -- wiederverwenden, Konsistenz unten"
    RC=0
  else
  python -X utf8 tools/window_train_split.py --file-list "${WIN}.txt" --val-frac "$VF" \
    --val-pool "$MOSAIC_VAL_POOL" --encoder 2d --value-target-variant nortv \
    --train-list-out "${WIN}_train.txt" --val-list-out "${WIN}_val.txt" \
    > "$SPLIT_OUT"
  RC=$?
  fi   # Ende Split rechnen / (RESUME) wiederverwenden
  cat "$SPLIT_OUT"
  [ $RC -eq 0 ] || { echo "STOPP $ARM: window_train_split.py mit Exit $RC"; exit 16; }
  NV=$(grep -vc '^#' "${WIN}_val.txt")
  [ "$NV" = "$N_VAL" ] || { echo "STOPP $ARM: Val-Menge hat $NV statt $N_VAL Dateien"; exit 16; }
  diff -q <(grep -v '^#' "${WIN}_val.txt") <(grep -v '^#' "${B02_WIN}_val.txt") >/dev/null \
    || { echo "STOPP $ARM: Val-Liste weicht von der b02-Val-Liste ab"; exit 16; }
  echo "   Val-Liste byte-gleich ${B02_WIN}_val.txt (ohne Kommentarzeilen)"
  # Trainingsanteil = b02-Trainingsanteil + die 400 neuen (folgt aus gleichem Val-Satz; Gegenprobe).
  python -X utf8 - "${WIN}_train.txt" "${B02_WIN}_train.txt" "$GEN" "$B09_CLASS" <<'PYEOF'
import glob, os, sys
mine, b02, gen, cls = sys.argv[1:5]
rd = lambda p: [l.strip() for l in open(p, encoding="utf-8") if l.strip() and not l.startswith("#")]
new = {os.path.basename(p) for p in glob.glob(f"data/selfplay_{gen}-{cls}_*.pkl")}
a, b = rd(mine), rd(b02)
print(f"   Train b09 {len(a)}, Train b02 {len(b)}, neue {len(new)}")
assert set(a) == set(b) | new and len(a) == len(b) + len(new) == 1480, "Trainingsanteil != b02 + neue"
PYEOF
  [ $? -eq 0 ] || { echo "STOPP $ARM: Trainingsanteil ist nicht b02-Trainingsanteil plus die 400 neuen"; exit 16; }
  KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$SPLIT_OUT" | awk '{print $NF}')
  [ -n "$KEY" ] || { echo "STOPP $ARM: kein Schluessel"; exit 16; }
  [ "$KEY" != "$B02_KEY" ] || { echo "STOPP $ARM: Schluessel $KEY == b02-Schluessel"; exit 16; }
  CACHE="data/.cache_${KEY}.h5"
  step_end

  step_begin "$ARM 1f) Monolith unter dem Fenster-Schluessel $KEY"
  # RESUME: der Stempel wird ZULETZT in den Monolithen geschrieben (build_cache_parallel.py:203-205);
  # traegt ein liegender Monolith den Schluessel, war der Merge durch. Sonst (fehlt, ohne Stempel,
  # unlesbar) wird neu gemergt; ein FREMDER Stempel bricht dort ab (Ueberschreib-Schutz, Z. 152-185).
  # check_window_key unten laeuft in beiden Faellen.
  RC=1
  if [ "$RESUME_MODE" = "1" ] && [ -f "$CACHE" ] && python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs.get('mosaic_cache_key'); k=k.decode() if isinstance(k,bytes) else k; sys.exit(0 if k==sys.argv[2] else 1)" "$CACHE" "$KEY" 2>/dev/null; then
    echo "   RESUME: $CACHE liegt schon mit Stempel $KEY -- Merge uebersprungen"
    RC=0
  else
  python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
    --value-target-variant nortv --workers 6 --file-list "${WIN}_train.txt" \
    --merge-out "$CACHE"
  RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
  fi   # Ende Merge / (RESUME) wiederverwenden
  [ $RC -eq 0 ] && [ -f "$CACHE" ] || { echo "STOPP $ARM: Monolith fehlt (Exit $RC)"; exit 14; }
  check_window_key "$KEY" "$CACHE" "${WIN}_train.txt" 800 "" || exit $?
  echo "##### FENSTER $ARM STEHT $(date +%F' '%H:%M:%S) -- Monolith $CACHE"
  step_end

  # ABBRUCH? Fortsetzen mit demselben Aufruf plus --resume (Fingerabdruck-Waechter), von Hand --
  # oder die ganze Kette mit RESUME=1 neu starten (dann entscheidet der Zustand unten).
  step_begin "$ARM 1g) Training -- WARMSTART von $LOAD (Rezept b02)"
  if [ "$RESUME_MODE" = "1" ]; then
    # train.py: Zwischenstand je Epoche models/alphazero_<name>_resume.pth (train.py:1144), am Ende
    # erst ONNX-Export, dann laufzeit ins Manifest, dann Loeschen des Zwischenstands (train.py:3144-3210).
    if [ -f "models/alphazero_${ARM}_resume.pth" ]; then
      echo "   RESUME: models/alphazero_${ARM}_resume.pth liegt -- train.py --resume"
      train_arm "${WIN}.txt" "$CACHE" "$VF" --resume
      RC=$?
    elif [ -f "models/alphazero_${ARM}.pth" ]; then
      python -X utf8 - "$ARM" <<'PYEOF'
import glob, json, sys
ms = sorted(glob.glob(f"models/manifest_train_{sys.argv[1]}_*.json"))
if not ms:
    print("   kein Trainings-Manifest"); sys.exit(1)
lz = json.load(open(ms[-1], encoding="utf-8")).get("laufzeit")
print(f"   {ms[-1]}: laufzeit {lz}")
sys.exit(0 if lz else 1)
PYEOF
      [ $? -eq 0 ] || { echo "STOPP $ARM (RESUME): models/alphazero_${ARM}.pth liegt ohne Zwischenstand, aber das Manifest traegt keine laufzeit -- von Hand pruefen"; exit 20; }
      echo "   RESUME: Training $ARM ist durch (finaler Stand, kein Zwischenstand, laufzeit im Manifest) -- uebersprungen"
      RC=0
    else
      for f in models/alphazero_${ARM}*.pth; do
        [ -f "$f" ] && { echo "STOPP $ARM (RESUME): $f liegt ohne Zwischenstand und ohne finalen Stand -- von Hand pruefen"; exit 20; }
      done
      train_arm "${WIN}.txt" "$CACHE" "$VF"
      RC=$?
    fi
  else
  train_arm "${WIN}.txt" "$CACHE" "$VF"
  RC=$?
  fi   # Ende Training / (RESUME) fortsetzen oder ueberspringen
  echo "   Training Exit $RC ($(date +%H:%M:%S))"
  [ $RC -eq 0 ] || { echo "STOPP $ARM: Training mit Exit $RC -- kein Tor 1"; exit 20; }
  step_end

  step_begin "$ARM 1g) Manifest-Diff gegen $REF_TRAIN_MANIFEST"
  manifest_diff "name,cache_file,file_list,val_frac,val_pool" \
    "MOSAIC_CARRIER_MANIFEST,MOSAIC_VAL_POOL" "${WIN}.txt" "$B09_VAL_POOL"
  RC=$?
  [ $RC -eq 0 ] || { echo "STOPP $ARM: Manifest-Diff/mosaic_env mit Exit $RC -- KEIN Tor 1"; exit 17; }
  step_end

  step_begin "$ARM 1h) Offline-Vorabmessung par.17 Punkt 2 (b02 gegen b09 auf dem b02-Val-Satz)"
  local BEST_PTH MS
  BEST_PTH=$(python -X utf8 tools/brier_best_checkpoint.py "$ARM" --ext pth)
  MS=(models/manifest_train_${ARM}_*.json)
  if [ -n "$BEST_PTH" ] && [ -f "$BEST_PTH" ]; then
    local PRE_OUT="$ART/checkpoint_val_eval_${ARM}_vs_b02.json"
    if [ "$RESUME_MODE" = "1" ] && [ -f "$PRE_OUT" ]; then
      echo "   RESUME: $PRE_OUT liegt schon -- uebersprungen"
    else
    python -X utf8 -u tools/checkpoint_val_eval.py --checkpoints "$B02_BEST_PTH" "$BEST_PTH" \
      --val-list "${WIN}_val.txt" --train-manifest "${MS[${#MS[@]}-1]}" --out "$PRE_OUT"
    RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
    fi   # Ende Offline-Messung / (RESUME) wiederverwenden
    [ -f "$PRE_OUT" ] && print_offline "$PRE_OUT" || echo "   HINWEIS: kein Artefakt $PRE_OUT (kein Stopp)"
  else
    echo "   HINWEIS: kein Brier-bestes $ARM-Netz (.pth) -- Offline-Vorabmessung entfaellt (kein Stopp)"
  fi
  step_end

  A=$(python -X utf8 tools/brier_best_checkpoint.py "$ARM" --ext onnx)
  [ $? -eq 0 ] && [ -n "$A" ] && [ -f "$A" ] || { echo "STOPP $ARM: brier_best_checkpoint.py findet kein Netz"; exit 15; }
  echo "##### TRAINING $ARM DURCH $(date +%F' '%H:%M:%S) -- gegatet wird $A"
  tor1 || exit $?
  echo "############################## ARM $ARM FERTIG $(date +%F' '%H:%M:%S)"
  exit 0
}

# --- ARM v35-b10 (par.18) --------------------------------------------------------------------------
run_b10() {
  ARM=v35-b10
  local CARRIER=policy_carrier_manifest_v35_b10.json
  local VFILE_TRAIN=data/window_v35_b10_train.txt VFILE_VAL=data/window_v35_b10_val.txt
  local SPLIT_OUT="$ART/v35_b10_split.txt"
  echo ""
  echo "############################## ARM $ARM (Schwarm als Policy-Traeger, par.18)   Start $(date +%F' '%H:%M:%S)"
  for f in models/alphazero_${ARM}*.pth; do
    [ -f "$f" ] && { echo "STOPP $ARM: $f liegt schon (train.py wuerde ohnehin abbrechen)"; exit 4; }
  done
  [ -f "data/$CARRIER" ] && { echo "STOPP $ARM: data/$CARRIER liegt schon -- wird NICHT ueberschrieben"; exit 4; }
  export_train_env "$CARRIER" "$B02_VAL_POOL"

  step_begin "$ARM 2a) Traeger-Manifest data/$CARRIER = alle 1.200 Dateien von ${B02_WIN}.txt"
  python -X utf8 tools/generate_carrier_manifest.py \
    --pattern "selfplay_${GEN}-*.pkl" --from-list "${B02_WIN}.txt" --n-files 1200 --seed $SEED \
    --out "$CARRIER"
  [ $? -eq 0 ] || { echo "STOPP $ARM: generate_carrier_manifest.py gescheitert"; exit 10; }
  python -X utf8 - "$CARRIER" "${B02_WIN}.txt" <<'PYEOF'
import json, sys
name, win = sys.argv[1:3]
f = json.load(open(f"data/{name}", encoding="utf-8"))["policy_carrier_files"]
w = [l.strip() for l in open(win, encoding="utf-8") if l.strip() and not l.startswith("#")]
print(f"   Manifest: {len(f)} Traeger, Fenster {len(w)} Dateien")
assert len(f) == 1200 and len(set(f)) == 1200 and set(f) == set(w), "Manifest != die 1.200 Fensterdateien"
PYEOF
  [ $? -eq 0 ] || { echo "STOPP $ARM: Traeger-Manifest traegt nicht genau die 1.200 Fensterdateien"; exit 10; }
  step_end

  step_begin "$ARM 2b) Split (b02-Liste, val_frac $B02_VF, Pool $B02_VAL_POOL), Listen gegen b02"
  python -X utf8 tools/window_train_split.py --file-list "${B02_WIN}.txt" --val-frac "$B02_VF" \
    --val-pool "$MOSAIC_VAL_POOL" --encoder 2d --value-target-variant nortv \
    --train-list-out "$VFILE_TRAIN" --val-list-out "$VFILE_VAL" \
    > "$SPLIT_OUT"
  RC=$?
  cat "$SPLIT_OUT"
  [ $RC -eq 0 ] || { echo "STOPP $ARM: window_train_split.py mit Exit $RC"; exit 12; }
  diff -q <(grep -v '^#' "$VFILE_VAL") <(grep -v '^#' "${B02_WIN}_val.txt") >/dev/null \
    || { echo "STOPP $ARM: Val-Liste weicht von der b02-Val-Liste ab"; exit 12; }
  diff -q <(grep -v '^#' "$VFILE_TRAIN") <(grep -v '^#' "${B02_WIN}_train.txt") >/dev/null \
    || { echo "STOPP $ARM: Trainingsliste weicht von der b02-Trainingsliste ab"; exit 12; }
  echo "   Val- und Trainingsliste byte-gleich b02 (ohne Kommentarzeilen)"
  KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$SPLIT_OUT" | awk '{print $NF}')
  [ -n "$KEY" ] || { echo "STOPP $ARM: kein Schluessel"; exit 13; }
  [ "$KEY" != "$B02_KEY" ] || { echo "STOPP $ARM: Schluessel $KEY == b02-Schluessel -- Traegermenge wirkt nicht"; exit 13; }
  CACHE="data/.cache_${KEY}.h5"
  step_end

  # Keine eigenen Bloecke (traegeragnostisch, Material "|carrier=1", engine/py/file_cache_key.py:381); der
  # Merge-Aufruf baut nur, was fehlt (build_cache_incremental.py:285-290), und das sollte nichts sein.
  step_begin "$ARM 2c) Monolith unter dem neuen Schluessel $KEY (Merge aus den b02-Bloecken)"
  python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
    --value-target-variant nortv --workers 6 --file-list "$VFILE_TRAIN" \
    --merge-out "$CACHE"
  RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
  [ $RC -eq 0 ] && [ -f "$CACHE" ] || { echo "STOPP $ARM: Monolith fehlt (Exit $RC)"; exit 14; }
  check_window_key "$KEY" "$CACHE" "$VFILE_TRAIN" 1200 "$B02_KEY" || exit $?
  echo "##### FENSTER $ARM STEHT $(date +%F' '%H:%M:%S) -- Monolith $CACHE"
  step_end

  # ABBRUCH? Fortsetzen mit demselben Aufruf plus --resume (Fingerabdruck-Waechter), von Hand.
  step_begin "$ARM 2d) Training -- WARMSTART von $LOAD (Rezept b02)"
  train_arm "${B02_WIN}.txt" "$CACHE" "$B02_VF"
  RC=$?; echo "   Training Exit $RC ($(date +%H:%M:%S))"
  [ $RC -eq 0 ] || { echo "STOPP $ARM: Training mit Exit $RC -- kein Tor 1"; exit 20; }
  step_end

  step_begin "$ARM 2d) Manifest-Diff gegen $REF_TRAIN_MANIFEST"
  manifest_diff "name,cache_file" "MOSAIC_CARRIER_MANIFEST" "${B02_WIN}.txt" "$B02_VAL_POOL"
  RC=$?
  [ $RC -eq 0 ] || { echo "STOPP $ARM: Manifest-Diff/mosaic_env mit Exit $RC -- KEIN Tor 1"; exit 17; }
  step_end

  step_begin "$ARM 2e) Offline-Vorabmessung par.18 Punkt 2 (b02 gegen b10, Traegermaske von b02)"
  local BEST_PTH
  BEST_PTH=$(python -X utf8 tools/brier_best_checkpoint.py "$ARM" --ext pth)
  if [ -n "$BEST_PTH" ] && [ -f "$BEST_PTH" ]; then
    local PRE_OUT="$ART/checkpoint_val_eval_${ARM}_vs_b02.json"
    # --train-manifest b02: das Werkzeug setzt die MOSAIC_*-Umgebung aus dem Manifest und bricht bei
    # einer GESETZTEN abweichenden Variable ab (checkpoint_val_eval.py:223-235). Darum laeuft der
    # Aufruf mit dem b02-Traeger-Manifest; der Val-Cache ist dann der des b02-Trainings.
    MOSAIC_CARRIER_MANIFEST="$B02_CARRIER" python -X utf8 -u tools/checkpoint_val_eval.py \
      --checkpoints "$B02_BEST_PTH" "$BEST_PTH" \
      --val-list "${B02_WIN}_val.txt" --train-manifest "$REF_TRAIN_MANIFEST" --out "$PRE_OUT"
    RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
    [ -f "$PRE_OUT" ] && print_offline "$PRE_OUT" || echo "   HINWEIS: kein Artefakt $PRE_OUT (kein Stopp)"
  else
    echo "   HINWEIS: kein Brier-bestes $ARM-Netz (.pth) -- Offline-Vorabmessung entfaellt (kein Stopp)"
  fi
  step_end

  A=$(python -X utf8 tools/brier_best_checkpoint.py "$ARM" --ext onnx)
  [ $? -eq 0 ] && [ -n "$A" ] && [ -f "$A" ] || { echo "STOPP $ARM: brier_best_checkpoint.py findet kein Netz"; exit 15; }
  echo "##### TRAINING $ARM DURCH $(date +%F' '%H:%M:%S) -- gegatet wird $A"
  tor1 || exit $?
  echo "############################## ARM $ARM FERTIG $(date +%F' '%H:%M:%S)"
  exit 0
}

# --- Arme: b10 VOR b09 (Nutzer 2026-10-06 "tausch b09 mit b10"; par.18: b10 nimmt die Frage (c) von par.17
#     ohne 7,7 h Erzeugung vorweg) ----------------------------------------------------------------
for arm in v35-b10 v35-b09; do
  T0=$(date +%s)
  # RESUME: b10 gilt als fertig, wenn das Brier-beste ONNX und zwei fertige Gating-Artefakte liegen
  # (Regex statt Glob: <out>.partial.json und _ABORTED.json zaehlen nicht).
  if [ "$RESUME_MODE" = "1" ] && [ "$arm" = "v35-b10" ]; then
    NG=$(ls "$ART" | grep -cE "^gating_v35-b10_vs_${GEN}_s[0-9]+\.json$")
    if [ -f models/alphazero_v35-b10_brierbest.onnx ] && [ "$NG" -ge 2 ]; then
      echo ""
      echo "== b10 fertig, uebersprungen (models/alphazero_v35-b10_brierbest.onnx und $NG Gating-Artefakte liegen)"
      printf '%s\t%s\t%s\n' "$arm" "uebersprungen (RESUME, fertig)" "0" >> "$SUMMARY_FILE"
      continue
    fi
    echo "   RESUME: b10 nicht vollstaendig (Brier-bestes ONNX oder zwei Gating-Artefakte fehlen; $NG Artefakte) -- run_b10 laeuft im Standardablauf"
  fi
  case $arm in
    v35-b09) ( run_b09 ) ;;
    v35-b10) ( run_b10 ) ;;
  esac
  RC=$?
  if [ $RC -eq 0 ]; then ST="durch"; else ST="STOPP Exit $RC"; fi
  printf '%s\t%s\t%s\n' "$arm" "$ST" "$(( $(date +%s) - T0 ))" >> "$SUMMARY_FILE"
  echo "== Arm $arm: $ST, $(( $(date +%s) - T0 )) s Wanduhr"
done

# --- Zusammenfassung je Arm -----------------------------------------------------------------------
echo ""
echo "########## v35-b09/b10-KETTE FERTIG $(date +%F' '%H:%M:%S) -- Zusammenfassung"
python -X utf8 - "$SUMMARY_FILE" "$STEPS_FILE" "$ART" "$GEN" "$REF_TRAIN_MANIFEST" <<'PYEOF'
import glob, json, os, subprocess, sys
sys.path.insert(0, os.path.join(os.getcwd(), "tools"))
from gating_block_z import block_shares, block_z
summary, steps, art, gen, ref_manifest = sys.argv[1:6]
step_rows = [l.rstrip("\n").split("\t", 2) for l in open(steps, encoding="utf-8") if l.strip()]

def history_minima(path):
    hist = json.load(open(path, encoding="utf-8")).get("epoch_history") or []
    out = {}
    for key in ("value_val_brier", "policy_val_loss"):
        vals = [(e.get(key), e.get("epoch", i + 1)) for i, e in enumerate(hist) if e.get(key) is not None]
        if vals:
            out[key] = min(vals, key=lambda t: t[0])
    return out, len(hist)

ref_min, _ = history_minima(ref_manifest)
print(f"\nReferenz v35-b02 ({os.path.basename(ref_manifest)}): " + ", ".join(
    f"{k} Minimum {v:.5f} in Epoche {ep}" for k, (v, ep) in ref_min.items()))
for line in open(summary, encoding="utf-8"):
    arm, status, wall = line.rstrip("\n").split("\t")
    print(f"\n{arm}: {status} ({int(wall) / 3600:.2f} h Wanduhr)")
    for a, name, sec in step_rows:
        if a == arm:
            print(f"   {int(sec):>7} s  {name}")
    ms = sorted(glob.glob(f"models/manifest_train_{arm}_*.json"))
    if ms:
        mins, n_ep = history_minima(ms[-1])
        for k, (v, ep) in mins.items():
            print(f"   {k}: Minimum {v:.5f} in Epoche {ep} von {n_ep} ({os.path.basename(ms[-1])})")
    r = subprocess.run([sys.executable, "-X", "utf8", "tools/brier_best_checkpoint.py", arm, "--ext", "onnx"],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode == 0:
        print(f"   Brier-bestes Netz: {r.stdout.strip()}")
    off = f"{art}/checkpoint_val_eval_{arm}_vs_b02.json"
    if os.path.exists(off):
        d = json.load(open(off, encoding="utf-8"))
        for path, lists in d["differences_reference_minus_checkpoint"].items():
            a = lists["all"]
            print(f"   Offline b02 minus {arm}: Policy-CE gepoolt {a['policy_val_loss_pooled_diff']} "
                  f"CI95 {a['policy_val_loss_pooled_diff_ci95']}; Brier {a['value_val_brier_diff']} "
                  f"CI95 {a['value_val_brier_diff_ci95']}")
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
rm -f "$SUMMARY_FILE" "$STEPS_FILE"
echo ""
echo "   Faellig danach (par.17/par.18): Verdikt je Arm nach den vorab festgelegten Lesarten (a)/(b)/(c),"
echo "   Epoche und Wert des policy_val_loss-Minimums gegen b02, Tor 2b aus den Logs, sechs"
echo "   Standard-Kennzahlen je Seite, Laufzeiten in die Prereg; MOSAIC_DATA_EXCLUDE folgender Ketten"
echo "   um ^selfplay_v34-b01-policy-s400-vol_ ergaenzen (par.17); Promotion NUR nach Nutzer-Entscheid."
