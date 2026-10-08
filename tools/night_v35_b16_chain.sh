#!/usr/bin/env bash
# v35-Kette fuer den Arm v35-b16 (Policy-Traeger-Hebel gestapelt: b09-Fenster mit ALLEN 1.600 Dateien als
# Policy-Traeger). Keine Erzeugung, kein Smoke, kein Blockbau: die 400 Dateien
# selfplay_v34-b01-policy-s400-vol_*.pkl liegen (b09-Kette), die Bloecke aller 1.600 Fensterdateien
# ebenso (traegeragnostisch). Neu sind nur Traeger-Manifest, Split-Protokoll, Merge unter neuem
# Fenster-Schluessel, Training, zwei Offline-Vorabmessungen und Tor 1 gegen den Generator v34-b01.
# Registrierungen (verbindlich): evaluations/PREREG_v35_window.md
#   par.20  b16: Fenster = b09-Fenster (data/window_v35_b09.txt, 1.600 = b02 1.200 + policy-s400-vol 400),
#           Traeger-Manifest data/policy_carrier_manifest_v35_b16.json = alle 1.600 Fensterdateien
#           (generate_carrier_manifest.py --from-list data/window_v35_b09.txt --n-files 1600), Split wie b09
#           (Val-Pool der fuenf b02-Klassen, val_frac 0,075, Val byte-gleich b02, Train 1.480), Training
#           byte-gleich b02/b09, Manifest-Diff gegen b09 (erlaubt name, cache_file, MOSAIC_CARRIER_MANIFEST),
#           Offline gegen b02 UND b10 (b02-Val-Satz, b02-Traegermaske wie par.18), Tor 1 wie die Reihe,
#           Lesart (a)/(b)/(c) gegen b10 60,9 % und b09 59,1 % (gepoolt, Seeds 20261600/01).
#   par.17  b09 (Fenster, Val-Pool, val_frac), par.18 b10 (Traeger = ganzes Fenster, Offline mit b02-Maske).
# Vorlage: tools/night_v35_b09_b10_chain.sh, Arm run_b09 ohne Erzeugung (Zeilen 400-799). BYTE-GLEICH
# uebernommen (aus der Vorlage eingesetzt, Zeilen dort): step_begin/step_end (95-104), export_train_env
# (170-182), train_arm (232-243), print_offline (297-316), gate und tor1 (318-397). ANGEPASST: Vergleichs-
# Traeger und -Schluessel in check_window_key (dort b02 fest, hier Parameter, b16 prueft gegen b09) und
# Referenz-Manifest in manifest_diff (dort b02 fest, hier Parameter, b16 diffed gegen b09, par.20).
#
# KOSTEN (HERLEITUNG aus par.20 und den b09/b10-Laufzeiten, nicht gemessen): Manifest Sekunden, Merge rund
# 7 min (b09 418 s fuer 1.480 Bloecke), Training rund 40 min (b09 2.355 s mit Nebenlast), Offline 2 x rund
# 0,5 min (b09 27,4 s), Tor 1 2 x rund 2 h (b09 Seed 2 exklusiv 7.238 s); zusammen rund 5 h, dritter Seed
# nach Stufenregel rund 2 h mehr.
#
# START: im Terminal-Tab mit Git-Bash, als DATEI:  bash tools/night_v35_b16_chain.sh
# KEINE PIPE dahinter, keine eigene Umleitung (weit ueber der 2-h-Grenze der Hintergrundaufgaben).
# Darf vor dem Ende der Vorgaenger gestartet werden: sie wartet, bis kein Prozess mit night_v35_<...>_chain
# (ausser dieser Kette selbst) oder tree_reuse_arena_chain in der Kommandozeile mehr laeuft (Deckel 40 h).
# Nutzer-Reihenfolge: b08b, b15 (volle Breite), dann b16. Damit b16 hinter b15 laeuft, muss die b15-Kette
# (tools/night_v35_b15_full_chain.sh) VOR oder gleichzeitig mit dieser gestartet sein: die b15-Kette
# wartet ihrerseits NICHT auf b16 (sonst Verklemmung), diese wartet auf b15.
#
# WIEDERAUFNAHME:  RESUME=1 bash tools/night_v35_b16_chain.sh
# Liegende Schritte werden geprueft und wiederverwendet (Traeger-Manifest, Split-Listen mit Protokoll,
# Monolith mit passendem Stempel, Training: _resume.pth -> train.py --resume, finaler Stand mit laufzeit
# -> uebersprungen, Offline-Artefakte, Gating-Artefakte je Seed; ein Zwischenstand <out>.partial.json
# wird von paired_gating.py --resume fortgesetzt). Ohne RESUME (oder RESUME=0) bricht jede liegende
# b16-Datei die Kette ab (STOPP, nichts wird ueberschrieben).
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
B02_CARRIER=policy_carrier_manifest_v35_b02.json
B02_WIN=data/window_v35_b02                                  # b02-Fenster und -Val-Liste, NICHT neu ziehen
B02_VAL_POOL='^selfplay_v34-b01-'
B02_REF_MANIFEST=models/manifest_train_v35-b02_20261005_195355.json   # par.18 Punkt 2: Traegermaske b02
B02_PTH=models/alphazero_v35-b02_brierbest.pth               # Offline-Referenz 1 (par.20 Punkt 1)
B10_PTH=models/alphazero_v35-b10_brierbest.pth               # Offline-Referenz 2 (par.20 Punkt 1)
B09_CLASS=policy-s400-vol
B09_WIN=data/window_v35_b09                                  # Fensterliste von b09, WIEDERVERWENDET
B09_CARRIER=policy_carrier_manifest_v35_b09.json
B09_REF_MANIFEST=models/manifest_train_v35-b09_20261008_000652.json   # Manifest-Diff-Referenz (par.20)
B09_SPLIT=$ART/v35_b09_split.txt                             # traegt den b09-Fenster-Schluessel
# Pool = die fuenf b02-Klassen; die neue Klasse trifft NICHT (nach "policy" muss "_" folgen), wie b09.
B09_VAL_POOL='^selfplay_v34-b01-(policy|policy-s400|policy-dice-v2-r1-s400|value-deviate-s400|value-excursion-s400)_'
B02_EXCLUDE='selfplay_v29-b11-probe_|selfplay_depth|selfplay_s4states|selfplay_tor2a|selfplay_probe-|selfplay_x35|selfplay_x35e2'
# Vorgaenger: jede night_v35_<...>_chain AUSSER dieser (negativer Lookahead, sonst wartet die Kette auf sich
# selbst) und die Tree-Reuse-Arena. Klammer-Trick wie tools/lib/cpu_free.sh, Punkt 1.
PRED_PATTERN='[n]ight_v35_(?!b16_)[A-Za-z0-9_]*_chain|[t]ree_reuse_arena_chain'
# Registrierte Vergleichswerte (par.20, gepoolt gegen v34-b01, Seeds 20261600/01); die Zusammenfassung
# rechnet sie aus den Artefakten nach und nimmt die nachgerechneten.
REG_B10=0.609
REG_B09=0.591
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

# --- Fruehe Pruefung VOR dem Warten (sonst merkt man einen Bedienfehler erst nach Stunden) ----------
for f in "$GEN_MODEL" "models/alphazero_${LOAD}.pth" "$SPEC" "data/$B02_CARRIER" "data/$B09_CARRIER" \
         "${B02_WIN}.txt" "${B02_WIN}_val.txt" "${B09_WIN}.txt" "${B09_WIN}.valfrac" "${B09_WIN}_train.txt" \
         "$B09_SPLIT" "$B02_REF_MANIFEST" "$B09_REF_MANIFEST" "$B02_PTH" "$B10_PTH" \
         tools/brier_best_checkpoint.py tools/checkpoint_val_eval.py tools/gating_block_z.py \
         tools/paired_gating.py tools/generate_carrier_manifest.py tools/window_train_split.py \
         tools/build_cache_incremental.py tools/probes/arena_column_probe.py tools/plate_points_from_arena.py; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
NCLS=$(ls data/ | grep -c "^selfplay_${GEN}-${B09_CLASS}_.*\.pkl$")
[ "$NCLS" = "400" ] || { echo "ABBRUCH: data/ traegt ${NCLS} statt 400 Dateien selfplay_${GEN}-${B09_CLASS}_*.pkl"; exit 1; }
NW=$(grep -vc '^#' "${B09_WIN}.txt")
[ "$NW" = "1600" ] || { echo "ABBRUCH: ${B09_WIN}.txt hat $NW statt 1600 Dateien"; exit 1; }
NV=$(grep -vc '^#' "${B02_WIN}_val.txt")
[ "$NV" = "$N_VAL" ] || { echo "ABBRUCH: b02-Val-Liste hat $NV statt $N_VAL Dateien"; exit 1; }
if [ "$RESUME_MODE" != "1" ]; then
  for f in models/alphazero_v35-b16*.pth "data/policy_carrier_manifest_v35_b16.json" \
           data/window_v35_b16_train.txt data/window_v35_b16_val.txt "$ART/v35_b16_split.txt" \
           "$ART"/checkpoint_val_eval_v35-b16_vs_*.json "$ART"/gating_v35-b16_vs_*.json; do
    [ -e "$f" ] && { echo "ABBRUCH: $f liegt schon -- von Hand pruefen oder RESUME=1"; exit 1; }
  done
fi
echo "Fruehpruefung GRUEN: 400 Dateien ${B09_CLASS}, Fenster ${B09_WIN}.txt 1600, b02-Val 120, Referenzen liegen"

# --- 0) Warten auf das Ende aller anderen v35-Ketten und der Tree-Reuse-Arena (Bauform b09-Kette:122-133) -
echo "########## v35-b16-KETTE WARTET auf das Ende von night_v35_*_chain (ausser b16) und tree_reuse_arena_chain $(date +%F' '%H:%M:%S)"
tick=0
while :; do
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '$PRED_PATTERN' }).Count" 2>/dev/null | tr -d '\r[:space:]')
  [ "$n" = "0" ] && break
  tick=$((tick + 1))
  [ $tick -gt 2400 ] && { echo "STOPP: Vorgaenger-Ketten nach 40 h noch nicht fertig"; exit 1; }
  [ $((tick % 10)) -eq 1 ] && echo "   Vorgaenger-Kette(n) laufen noch (Antwort '${n}', $(date +%H:%M:%S))"
  sleep 60
done
echo "   Vorgaenger-Ketten beendet ($(date +%H:%M:%S))"

# --- Vorpruefungen (global; ein Fehler hier stoppt die Kette) ---------------------------------------
python -X utf8 -c "import config,sys; sys.exit(0 if (config.INPUT_SIZE,config.NUM_ACTIONS)==(888,414) else 3)" \
  || { echo "STOPP: config.py traegt nicht INPUT_SIZE 888 / NUM_ACTIONS 414"; exit 3; }
B09_KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$B09_SPLIT" | awk '{print $NF}')
[ -n "$B09_KEY" ] || { echo "STOPP: kein b09-Schluessel in $B09_SPLIT"; exit 3; }
B02_KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v35_b02_split.txt" | awk '{print $NF}')
[ -n "$B02_KEY" ] || { echo "STOPP: kein b02-Schluessel in $ART/v35_b02_split.txt"; exit 3; }
echo "== v35-b16-KETTE   Start $(date +%F' '%H:%M:%S)"
echo "   Diff-Referenz $B09_REF_MANIFEST, b09-Schluessel $B09_KEY, b02-Schluessel $B02_KEY"
echo "   Offline-Referenzen $B02_PTH und $B10_PTH, Traegermaske aus $B02_REF_MANIFEST"

# Bootstrap-Knoepfe global AUS (wie night_v35_b09_b10_chain.sh:164); b02/b09 liefen ohne sie. Dazu die
# Datenschicht-Knoepfe der Arme b11-b15 (par.19), falls eine Shell sie noch traegt.
unset MOSAIC_BOOTSTRAP_SOURCE MOSAIC_BOOTSTRAP_HORIZON_ROUNDS MOSAIC_BOOTSTRAP_MARGIN_SCALE MOSAIC_BOOTSTRAP_COHERENCE
unset MOSAIC_TD_LAMBDA MOSAIC_BOOTSTRAP_TRAJ_LAMBDA MOSAIC_BOOTSTRAP_TRAJ_OPPONENT MOSAIC_BOOTSTRAP_TRAJ_MIX MOSAIC_BOOTSTRAP_TRAJ_CONF_SCALE

wait_for_free_cpu "v35-b16-Kette"

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

# Stempel und Schluessel-Abnahme des Monolithen (Bauform b09-Kette:184-230; dort ist der Vergleichs-
# Traeger fest b02, hier Parameter). $1 Schluessel, $2 Monolith, $3 Trainingsliste, $4 Traegerzahl soll,
# $5 Vergleichs-Traeger-Manifest, $6 Vergleichs-Schluessel: dieselbe Trainingsliste unter $5 muss $6
# ergeben (einziger Unterschied = Traegermenge).
check_window_key() {
  python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; print('   Stempel:',k); sys.exit(0 if k==sys.argv[2] else 16)" "$2" "$1" \
    || { echo "STOPP $ARM: Stempel passt nicht zum Schluessel"; return 16; }
  python -X utf8 - "$1" "$2" "$3" "$4" "$MOSAIC_CARRIER_MANIFEST" "$5" "$6" <<'PYEOF'
import glob, json, os, sys
root = os.getcwd()
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, "engine", "py"))
from config import DATA_DIR
import corpus_dataset, h5py
key, cache, train_list, n_carriers, carrier, ref_carrier, ref_key = sys.argv[1:8]
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
saved = os.environ["MOSAIC_CARRIER_MANIFEST"]
os.environ["MOSAIC_CARRIER_MANIFEST"] = ref_carrier
off = wkey()
os.environ["MOSAIC_CARRIER_MANIFEST"] = saved
print(f"   dieselbe Liste mit {ref_carrier}: {off.key}, Vergleichs-Schluessel {ref_key}")
assert off.key == ref_key, f"mit {ref_carrier} NICHT der Vergleichs-Schluessel -- weitere Abweichung"
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

# Manifest-Diff gegen ein Referenz-Manifest (Bauform b09-Kette:245-295; dort fest b02, hier Parameter).
# $1 Referenz-Manifest, $2 Referenz-Name (nur Ausgabe), $3 erlaubte cli_args (Komma), $4 erlaubte
# mosaic_env-Abweichungen (Komma), $5 erwartete file_list, $6 erwarteter Val-Pool.
manifest_diff() {
  python -X utf8 - "$ARM" "$1" "$2" "$MOSAIC_CARRIER_MANIFEST" "$3" "$4" "$5" "$6" <<'PYEOF'
import glob, io, json, sys
arm, ref_path, ref_name, carrier, allowed_cli, allowed_env, want_list, want_pool = sys.argv[1:9]
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
        print(f"   cli_args.{k}: {ref_name}={ref.get(k)!r} -> {arm}={neu.get(k)!r}{mark}")
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
        print(f"   mosaic_env.{k}: {ref_name}={renv.get(k)!r} -> {arm}={env.get(k)!r}{mark}")
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

# --- ARM v35-b16 (par.20) --------------------------------------------------------------------------
run_b16() {
  ARM=v35-b16
  local CARRIER=policy_carrier_manifest_v35_b16.json
  local WIN=$B09_WIN                     # Fensterliste von b09 (par.20 "Split wie b09"; Manifest-Diff erlaubt kein file_list)
  local SPLIT_TRAIN=data/window_v35_b16_train.txt SPLIT_VAL=data/window_v35_b16_val.txt
  local SPLIT_OUT="$ART/v35_b16_split.txt"
  echo ""
  echo "############################## ARM $ARM (Policy-Traeger gestapelt, par.20)   Start $(date +%F' '%H:%M:%S)"
  # Trainings-Umgebung: b02/b09-Umgebung, Traeger-Manifest b16, Val-Pool der fuenf b02-Klassen (wie b09).
  export_train_env "$CARRIER" "$B09_VAL_POOL"
  wait_for_free_cpu "$ARM Fenster"

  step_begin "$ARM 1a) Fensterliste ${WIN}.txt pruefen (b09-Fenster, wiederverwendet: b02 1.200 + $B09_CLASS 400)"
  # Gleiche Pruefung wie RESUME-Zweig der b09-Kette (Z. 557-586), nur ohne Nachziehen von .valfrac.
  python -X utf8 - "$GEN" "$B09_CLASS" "$B02_WIN" "$WIN" "$N_VAL" <<'PYEOF'
import glob, os, re, sys
gen, cls, b02_win, win, n_val = sys.argv[1:6]
rd = lambda p: [l.strip() for l in open(p, encoding="utf-8") if l.strip() and not l.startswith("#")]
b02 = rd(f"{b02_win}.txt")
new = sorted(os.path.basename(p) for p in glob.glob(f"data/selfplay_{gen}-{cls}_*.pkl"))
assert len(b02) == 1200 and len(new) == 400, ("b02-Fenster / neue Klasse", len(b02), len(new))
have = rd(f"{win}.txt")
# Bauvorschrift der b09-Kette: b02-Fenster in Listenreihenfolge, dann die neue Klasse sortiert.
assert have == b02 + new, (f"Fensterliste weicht ab: {len(have)} Eintraege, erwartet 1600 "
                           f"= b02 + neue Klasse in Bau-Reihenfolge")
assert len(set(have)) == 1600, "Doppelte im Fenster"
assert all(os.path.exists(os.path.join("data", b)) for b in have), "Datei fehlt"
assert all(b.startswith(f"selfplay_{gen}-") for b in have), "Fensterdatei ausserhalb selfplay_<GEN>-* (Traeger-Pattern)"
excl = os.environ.get("MOSAIC_DATA_EXCLUDE", "")
assert not [b for b in have if excl and re.search(excl, b)], "Fensterdatei kollidiert mit MOSAIC_DATA_EXCLUDE"
pool = os.environ["MOSAIC_VAL_POOL"]
assert {b for b in have if re.search(pool, b)} == set(b02), "Val-Pool trifft nicht genau das b02-Fenster"
vf = f"{int(n_val) / len(have):.8f}"
got = open(f"{win}.valfrac", encoding="utf-8").read().strip()
assert got == vf, f"{win}.valfrac traegt {got}, erwartet {vf}"
print(f"   {win}.txt: 1600 Dateien = b02 1.200 + {cls} 400 (Reihenfolge der b09-Kette), Val-Pool trifft genau b02, "
      f"val_frac {vf} -- GRUEN")
PYEOF
  [ $? -eq 0 ] || { echo "STOPP $ARM: Fensterliste ${WIN}.txt passt nicht"; exit 13; }
  VF=$(tr -d '[:space:]' < "${WIN}.valfrac")
  step_end

  step_begin "$ARM 1b) Bloecke: alle 1.600 liegen (traegeragnostisch), sonst STOPP"
  # Dieselbe Pfadfunktion wie die Bauschleife (build_cache_incremental._block_path, Z. 111-124) mit der
  # Arm-Umgebung; ein fehlender Block hiesse geaenderter Datei-Schluessel (Marker, Rezept), kein Nachbau.
  python -X utf8 - "${WIN}.txt" <<'PYEOF'
import os, sys
sys.path.insert(0, "tools")
from build_cache_incremental import _block_path
kw = dict(encoder="2d", value_target_variant="nortv", conjunction_head=False)
names = [l.strip() for l in open(sys.argv[1], encoding="utf-8") if l.strip() and not l.startswith("#")]
miss = [n for n in names if not os.path.exists(_block_path("data", n, kw))]
print(f"   {len(names)} Dateien: {len(names) - len(miss)} Bloecke liegen, {len(miss)} zu bauen"
      + (f", z.B. {miss[:3]}" if miss else ""))
sys.exit(0 if not miss and len(names) == 1600 else 1)
PYEOF
  [ $? -eq 0 ] || { echo "STOPP $ARM: nicht alle 1.600 Bloecke liegen (par.20: kein Blockbau) -- von Hand pruefen"; exit 14; }
  step_end

  step_begin "$ARM 1c) Traeger-Manifest data/$CARRIER = alle 1.600 Dateien von ${WIN}.txt"
  if [ "$RESUME_MODE" = "1" ] && [ -f "data/$CARRIER" ]; then
    echo "   RESUME: data/$CARRIER liegt schon -- wiederverwenden, Konsistenz unten"
  else
    # Bauform b10 (b09-Kette:815-829): --from-list schraenkt auf das Fenster ein, --n-files = Fenstergroesse
    # nimmt jede Datei (Stratumgroesse 1, generate_carrier_manifest.py:55-66).
    python -X utf8 tools/generate_carrier_manifest.py \
      --pattern "selfplay_${GEN}-*.pkl" --from-list "${WIN}.txt" --n-files 1600 --seed $SEED \
      --out "$CARRIER"
    [ $? -eq 0 ] || { echo "STOPP $ARM: generate_carrier_manifest.py gescheitert"; exit 10; }
  fi
  python -X utf8 - "$CARRIER" "${WIN}.txt" "$B09_CARRIER" <<'PYEOF'
import json, sys
name, win, b09name = sys.argv[1:4]
f = json.load(open(f"data/{name}", encoding="utf-8"))["policy_carrier_files"]
w = [l.strip() for l in open(win, encoding="utf-8") if l.strip() and not l.startswith("#")]
b09 = set(json.load(open(f"data/{b09name}", encoding="utf-8"))["policy_carrier_files"])
print(f"   Manifest: {len(f)} Traeger, Fenster {len(w)} Dateien, davon b09-Traeger {len(b09 & set(f))} von {len(b09)}")
assert len(f) == 1600 and len(set(f)) == 1600 and set(f) == set(w), "Manifest != die 1.600 Fensterdateien"
assert b09 <= set(f), "b09-Traeger nicht vollstaendig enthalten"
PYEOF
  [ $? -eq 0 ] || { echo "STOPP $ARM: Traeger-Manifest traegt nicht genau die 1.600 Fensterdateien"; exit 10; }
  step_end

  step_begin "$ARM 1d) Split (val_frac $VF, Val-Pool der fuenf b02-Klassen), Listen gegen b02/b09"
  if [ "$RESUME_MODE" = "1" ] && [ -f "$SPLIT_TRAIN" ] && [ -f "$SPLIT_VAL" ] \
     && grep -q "Fenster-Schluessel des Trainingsanteils: [0-9a-f]" "$SPLIT_OUT" 2>/dev/null; then
    echo "   RESUME: $SPLIT_TRAIN, $SPLIT_VAL und $SPLIT_OUT liegen schon -- wiederverwenden, Konsistenz unten"
    RC=0
  else
    python -X utf8 tools/window_train_split.py --file-list "${WIN}.txt" --val-frac "$VF" \
      --val-pool "$MOSAIC_VAL_POOL" --encoder 2d --value-target-variant nortv \
      --train-list-out "$SPLIT_TRAIN" --val-list-out "$SPLIT_VAL" \
      > "$SPLIT_OUT"
    RC=$?
  fi
  cat "$SPLIT_OUT"
  [ $RC -eq 0 ] || { echo "STOPP $ARM: window_train_split.py mit Exit $RC"; exit 12; }
  NV=$(grep -vc '^#' "$SPLIT_VAL")
  [ "$NV" = "$N_VAL" ] || { echo "STOPP $ARM: Val-Menge hat $NV statt $N_VAL Dateien"; exit 12; }
  diff -q <(grep -v '^#' "$SPLIT_VAL") <(grep -v '^#' "${B02_WIN}_val.txt") >/dev/null \
    || { echo "STOPP $ARM: Val-Liste weicht von der b02-Val-Liste ab"; exit 12; }
  diff -q <(grep -v '^#' "$SPLIT_TRAIN") <(grep -v '^#' "${B09_WIN}_train.txt") >/dev/null \
    || { echo "STOPP $ARM: Trainingsliste weicht von der b09-Trainingsliste ab"; exit 12; }
  NT=$(grep -vc '^#' "$SPLIT_TRAIN")
  [ "$NT" = "1480" ] || { echo "STOPP $ARM: Trainingsanteil hat $NT statt 1480 Dateien"; exit 12; }
  echo "   Val-Liste byte-gleich ${B02_WIN}_val.txt, Trainingsliste byte-gleich ${B09_WIN}_train.txt (1.480; ohne Kommentarzeilen)"
  KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$SPLIT_OUT" | awk '{print $NF}')
  [ -n "$KEY" ] || { echo "STOPP $ARM: kein Schluessel"; exit 13; }
  [ "$KEY" != "$B09_KEY" ] || { echo "STOPP $ARM: Schluessel $KEY == b09-Schluessel -- Traegermenge wirkt nicht"; exit 13; }
  [ "$KEY" != "$B02_KEY" ] || { echo "STOPP $ARM: Schluessel $KEY == b02-Schluessel"; exit 13; }
  CACHE="data/.cache_${KEY}.h5"
  step_end

  step_begin "$ARM 1e) Monolith unter dem neuen Schluessel $KEY (Merge aus den liegenden Bloecken)"
  # RESUME: Stempel zuletzt geschrieben (build_cache_parallel.py:203-205), liegt er passend, war der Merge
  # durch (Bauform b09-Kette:709-726). check_window_key laeuft in beiden Faellen.
  RC=1
  if [ "$RESUME_MODE" = "1" ] && [ -f "$CACHE" ] && python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs.get('mosaic_cache_key'); k=k.decode() if isinstance(k,bytes) else k; sys.exit(0 if k==sys.argv[2] else 1)" "$CACHE" "$KEY" 2>/dev/null; then
    echo "   RESUME: $CACHE liegt schon mit Stempel $KEY -- Merge uebersprungen"
    RC=0
  else
    python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
      --value-target-variant nortv --workers 6 --file-list "$SPLIT_TRAIN" \
      --merge-out "$CACHE"
    RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
  fi
  [ $RC -eq 0 ] && [ -f "$CACHE" ] || { echo "STOPP $ARM: Monolith fehlt (Exit $RC)"; exit 14; }
  check_window_key "$KEY" "$CACHE" "$SPLIT_TRAIN" 1600 "$B09_CARRIER" "$B09_KEY" || exit $?
  echo "##### FENSTER $ARM STEHT $(date +%F' '%H:%M:%S) -- Monolith $CACHE"
  step_end

  # ABBRUCH? Die ganze Kette mit RESUME=1 neu starten (dann entscheidet der Zustand unten).
  step_begin "$ARM 1f) Training -- WARMSTART von $LOAD (Rezept b02/b09)"
  if [ "$RESUME_MODE" = "1" ]; then
    # Bauform b09-Kette:731-765 (train.py: Zwischenstand je Epoche _resume.pth, am Ende laufzeit ins Manifest).
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
  fi
  echo "   Training Exit $RC ($(date +%H:%M:%S))"
  [ $RC -eq 0 ] || { echo "STOPP $ARM: Training mit Exit $RC -- kein Tor 1"; exit 20; }
  step_end

  step_begin "$ARM 1g) Manifest-Diff gegen $B09_REF_MANIFEST (par.20: erlaubt name, cache_file, MOSAIC_CARRIER_MANIFEST)"
  manifest_diff "$B09_REF_MANIFEST" "v35-b09" "name,cache_file" "MOSAIC_CARRIER_MANIFEST" \
    "${WIN}.txt" "$B09_VAL_POOL"
  RC=$?
  [ $RC -eq 0 ] || { echo "STOPP $ARM: Manifest-Diff/mosaic_env mit Exit $RC -- KEIN Tor 1"; exit 17; }
  step_end

  step_begin "$ARM 1h) Offline-Vorabmessung par.20 Punkt 1 (b02 und b10 gegen b16, b02-Val-Satz, b02-Traegermaske)"
  local BEST_PTH REF REF_PTH PRE_OUT
  BEST_PTH=$(python -X utf8 tools/brier_best_checkpoint.py "$ARM" --ext pth)
  if [ -n "$BEST_PTH" ] && [ -f "$BEST_PTH" ]; then
    for REF in b02 b10; do
      case $REF in b02) REF_PTH=$B02_PTH ;; b10) REF_PTH=$B10_PTH ;; esac
      PRE_OUT="$ART/checkpoint_val_eval_${ARM}_vs_${REF}.json"
      echo "   -- Referenz $REF ($REF_PTH) minus $ARM ($BEST_PTH)"
      if [ "$RESUME_MODE" = "1" ] && [ -f "$PRE_OUT" ]; then
        echo "   RESUME: $PRE_OUT liegt schon -- uebersprungen"
      else
        # --train-manifest b02 (par.18 Punkt 2): das Werkzeug setzt die MOSAIC_*-Umgebung aus dem Manifest und
        # bricht bei einer GESETZTEN abweichenden Variable ab (checkpoint_val_eval.py:202-235). Die Arm-Umgebung
        # traegt Traeger-Manifest b16 und Val-Pool b09; beide werden fuer den Aufruf auf b02 gesetzt (b10-Kette:
        # nur das Traeger-Manifest, dort war der Pool schon der von b02).
        MOSAIC_CARRIER_MANIFEST="$B02_CARRIER" MOSAIC_VAL_POOL="$B02_VAL_POOL" python -X utf8 -u tools/checkpoint_val_eval.py \
          --checkpoints "$REF_PTH" "$BEST_PTH" \
          --val-list "${B02_WIN}_val.txt" --train-manifest "$B02_REF_MANIFEST" --out "$PRE_OUT"
        RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
      fi
      [ -f "$PRE_OUT" ] && print_offline "$PRE_OUT" || echo "   HINWEIS: kein Artefakt $PRE_OUT (kein Stopp)"
    done
  else
    echo "   HINWEIS: kein Brier-bestes $ARM-Netz (.pth) -- Offline-Vorabmessung entfaellt (kein Stopp)"
  fi
  step_end

  # Gegatet wird das Brier-beste Netz nach der Regel von train.py, aus dem Manifest gelesen
  # (brier_best_checkpoint.py: _brierbest, wenn es getrennt liegt, sonst _best oder der finale Stand).
  A=$(python -X utf8 tools/brier_best_checkpoint.py "$ARM" --ext onnx)
  [ $? -eq 0 ] && [ -n "$A" ] && [ -f "$A" ] || { echo "STOPP $ARM: brier_best_checkpoint.py findet kein Netz"; exit 15; }
  echo "##### TRAINING $ARM DURCH $(date +%F' '%H:%M:%S) -- gegatet wird $A"
  tor1 || exit $?
  echo "############################## ARM $ARM FERTIG $(date +%F' '%H:%M:%S)"
  exit 0
}

# --- Arm in einer SUBSHELL: ein STOPP (exit) beendet nur den Arm, die Zusammenfassung laeuft trotzdem ---
T0=$(date +%s)
( run_b16 )
RC=$?
if [ $RC -eq 0 ]; then ST="durch"; else ST="STOPP Exit $RC"; fi
printf '%s\t%s\t%s\n' "v35-b16" "$ST" "$(( $(date +%s) - T0 ))" >> "$SUMMARY_FILE"
echo "== Arm v35-b16: $ST, $(( $(date +%s) - T0 )) s Wanduhr"

# --- Zusammenfassung ------------------------------------------------------------------------------
echo ""
echo "########## v35-b16-KETTE FERTIG $(date +%F' '%H:%M:%S) -- Zusammenfassung"
python -X utf8 - "$SUMMARY_FILE" "$STEPS_FILE" "$ART" "$GEN" "$B02_REF_MANIFEST" "$B09_REF_MANIFEST" "$REG_B10" "$REG_B09" <<'PYEOF'
import glob, json, os, subprocess, sys
sys.path.insert(0, os.path.join(os.getcwd(), "tools"))
from gating_block_z import block_shares, block_z
summary, steps, art, gen, b02_manifest, b09_manifest, reg_b10, reg_b09 = sys.argv[1:9]
reg = {"v35-b10": float(reg_b10), "v35-b09": float(reg_b09)}
step_rows = [l.rstrip("\n").split("\t", 2) for l in open(steps, encoding="utf-8") if l.strip()]
SEEDS2 = ("20261600", "20261601")

def fmt(x):
    return "?" if x is None else f"{x:.2f}"

def history_minima(path):
    hist = json.load(open(path, encoding="utf-8")).get("epoch_history") or []
    out = {}
    for key in ("value_val_brier", "policy_val_loss"):
        vals = [(e.get(key), e.get("epoch", i + 1)) for i, e in enumerate(hist) if e.get(key) is not None]
        if vals:
            out[key] = min(vals, key=lambda t: t[0])
    return out, len(hist)

def gating(arm, seeds):
    """Gepoolte Siegquote (Summe a_wins / Summe n_games) und Block-z ueber die vorhandenen Seeds."""
    paths = [p for p in (f"{art}/gating_{arm}_vs_{gen}_s{s}.json" for s in seeds) if os.path.exists(p)]
    a = n = 0
    blocks = []
    for p in paths:
        d = json.load(open(p, encoding="utf-8"))
        a += d["a_wins_total"]; n += d.get("n_games_total") or 0
        blocks.extend(block_shares(p))
    z = block_z(blocks)["z"] if blocks else None
    return paths, a, n, (a / n if n else None), z

for name, path in (("v35-b02", b02_manifest), ("v35-b09", b09_manifest)):
    mins, _ = history_minima(path)
    print(f"\nReferenz {name} ({os.path.basename(path)}): " + ", ".join(
        f"{k} Minimum {v:.5f} in Epoche {ep}" for k, (v, ep) in mins.items()))
print("   (policy_val_loss von b16 ist mit b02/b09 NICHT vergleichbar: Policy-Gewicht auf allen 120 Val-Dateien,"
      " par.18; vergleichbar ist die Offline-CE auf der b02-Maske unten)")
arm = "v35-b16"
for line in open(summary, encoding="utf-8"):
    a_, status, wall = line.rstrip("\n").split("\t")
    print(f"\n{a_}: {status} ({int(wall) / 3600:.2f} h Wanduhr)")
for a_, name, sec in step_rows:
    print(f"   {int(sec):>7} s  {name}")
ms = sorted(glob.glob(f"models/manifest_train_{arm}_*.json"))
if ms:
    mins, n_ep = history_minima(ms[-1])
    for k, (v, ep) in mins.items():
        print(f"   {k}: Minimum {v:.5f} in Epoche {ep} von {n_ep} ({os.path.basename(ms[-1])})")
    lz = json.load(open(ms[-1], encoding="utf-8")).get("laufzeit") or {}
    print(f"   Training: {lz.get('wanduhr_s')} s Wanduhr, {lz.get('samples')} Samples (b09: 2.832.807, par.17a)")
r = subprocess.run([sys.executable, "-X", "utf8", "tools/brier_best_checkpoint.py", arm, "--ext", "onnx"],
                   capture_output=True, text=True, encoding="utf-8")
if r.returncode == 0:
    print(f"   Brier-bestes Netz: {r.stdout.strip()}")
for ref in ("b02", "b10"):
    off = f"{art}/checkpoint_val_eval_{arm}_vs_{ref}.json"
    if os.path.exists(off):
        d = json.load(open(off, encoding="utf-8"))
        for path, lists in d["differences_reference_minus_checkpoint"].items():
            a = lists["all"]
            print(f"   Offline {ref} minus b16: Policy-CE gepoolt {a['policy_val_loss_pooled_diff']} "
                  f"CI95 {a['policy_val_loss_pooled_diff_ci95']}; Brier {a['value_val_brier_diff']} "
                  f"CI95 {a['value_val_brier_diff_ci95']}  (> 0 = b16 besser)")
    else:
        print(f"   Offline {ref}: kein Artefakt {off}")
for p in sorted(glob.glob(f"{art}/gating_{arm}_vs_{gen}_s2026160[012].json")):
    d = json.load(open(p, encoding="utf-8"))
    n = d.get("n_games_total") or 0
    z = block_z(block_shares(p))["z"]
    wr = f"{d['a_wins_total'] / n:.4f}" if n else "?"
    sa, sb = d.get("avg_score_a"), d.get("avg_score_b")
    marg = f"{sa - sb:+.2f}" if sa is not None and sb is not None else "?"
    print(f"   Tor 1 {os.path.basename(p)}: {d['a_wins_total']}:{d.get('b_wins_total')} von {n}, Siegquote {wr}, "
          f"Block-z {'n/a' if z is None else f'{z:+.2f}'}, Punkte {fmt(sa)} / {fmt(sb)} (Margin {marg}), "
          f"Strafsteine {fmt(d.get('avg_floor_a'))} / {fmt(d.get('avg_floor_b'))}")
paths, a, n, wr, z = gating(arm, ("20261600", "20261601", "20261602"))
if len(paths) > 1:
    print(f"   gepoolt ({len(paths)} Seeds): {a}/{n} = {wr:.4f}, Block-z {'n/a' if z is None else f'{z:+.2f}'}")
print("   Spalten und Plattenpunkte je Seed: arena_columns_gating_*.json und plate_points_*.json in", art)

# Lesart par.20 auf DENSELBEN Seeds wie die Vergleichswerte (b09/b10 haben nur 20261600/01).
paths, a, n, wr, z = gating(arm, SEEDS2)
seeds_have = [s for s in SEEDS2 if os.path.exists(f"{art}/gating_{arm}_vs_{gen}_s{s}.json")]
print(f"\nLESART par.20 (mechanisch, Verdikt beim Koordinator), Seeds {seeds_have}:")
refs = {}
for other in ("v35-b10", "v35-b09"):
    _, oa, on, owr, oz = gating(other, seeds_have)
    refs[other] = owr
    if seeds_have:
        print(f"   {other} auf denselben Seeds: {oa}/{on} = {'n/a' if owr is None else f'{owr:.4f}'} "
              f"(registriert gepoolt {reg[other]:.3f}), Block-z {'n/a' if oz is None else f'{oz:+.2f}'}")
if not seeds_have or wr is None or None in refs.values():
    print("   kein vollstaendiger Satz Gating-Artefakte (b16 oder Vergleichsarme) -- keine Lesart")
else:
    print(f"   v35-b16: {a}/{n} = {wr:.4f}, Block-z {'n/a' if z is None else f'{z:+.2f}'}")
    if len(seeds_have) < 2:
        print("   NUR EIN SEED (unter der Stufen-Schwelle oder abgebrochen): Lesart nur vorlaeufig")
    top = max(refs.values())
    hits = []
    if wr > top + 0.04:
        hits.append("(a) ueber b10 UND b09 um mehr als rund 4 Punkte (HERLEITUNG par.20): die Hebel addieren sich")
    if 0.57 <= wr <= 0.65:
        hits.append("(b) im Band von b10 (57 bis 65 %): gesaettigt, der zweite Hebel legt nichts auf den ersten")
    if wr < refs["v35-b09"]:
        hits.append("(c) unter b09: die Stapelung schadet (Traegeranteil 100 % verdraengt Wertmaterial)")
    for h in hits or ["keine der drei Lesarten trifft rein (zwischen den Grenzen) -- von Hand einordnen"]:
        print(f"   -> {h}")
    if len(hits) > 1:
        print("   MEHRERE Lesarten treffen (Baender ueberlappen): Grenzfall, direkte Kante b16 gegen b10 nur nach Nutzer-Entscheid")
PYEOF
rm -f "$SUMMARY_FILE" "$STEPS_FILE"
echo ""
echo "   Faellig danach (par.20): Verdikt nach Lesart (a)/(b)/(c), Offline-Zahlen gegen b02 und b10, sechs"
echo "   Standard-Kennzahlen je Seite (arena_column_probe, plate_points), Laufzeiten in Prereg und"
echo "   docs/measured_runtimes.md, Kopf Zeile 1 und Index; Promotion NUR nach Nutzer-Entscheid."
