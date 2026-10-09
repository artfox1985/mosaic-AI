#!/usr/bin/env bash
# v35-Kette fuer den Arm v35-b19: Wertziel mit Trajektorien-Bootstrap k = 1 (Bauform b03, par.13) auf dem
# b16-Fenster (b09-Fenster, 1.600 Dateien, ALLE 1.600 als Policy-Traeger, par.20). Keine Erzeugung, kein
# Smoke. Neu sind: 400 Bloecke unter dem Arm-Marker (die b02-Dateien liegen dort seit b03), Split-Protokoll,
# Merge unter neuem Fenster-Schluessel, Training, Vorfilter offline gegen b16 und Schnellblick gegen b16
# (feste Laenge 2 x 50 Paare). Die volle Breite startet die Kette NICHT selbst.
# Registrierungen (verbindlich): evaluations/PREREG_v35_window.md
#   par.21  b19 (Arm-Definition; beim Bau dieser Kette lag par.21 noch NICHT in der Datei, die Kette folgt
#           dem Koordinator-Auftrag vom 2026-10-09 -- vor dem Start gegen par.21 abgleichen)
#   par.13  Knopf MOSAIC_BOOTSTRAP_SOURCE=trajectory, MOSAIC_BOOTSTRAP_HORIZON_ROUNDS=1, Marker
#           +bootstraptraj_h1_v1 in BEIDEN Cache-Schluesseln (b03)
#   par.20  b16: Fenster data/window_v35_b09.txt, Traeger-Manifest policy_carrier_manifest_v35_b16.json
#           (1.600), Split wie b09 (Val byte-gleich b02, Train 1.480), Training byte-gleich b02/b09
#   par.19.0 Schnellblick-Protokoll (Vorfilter Punkt 2, feste Laenge Punkt 3, Lesart Punkt 4), hier mit
#           b16 als Referenz und Gegner statt b02
# Vorlagen: tools/night_v35_b16_chain.sh (BYTE-GLEICH uebernommen: step_begin/step_end 82-91,
# export_train_env 154-164, train_arm 213-222, Fensterlisten-Pruefung 1a 394-417, Split 1d 463-491,
# Merge/RESUME 1e 496-506, Training/RESUME 1f 512-545, Warteschleife 121-129, Arm-Subshell 592-597);
# tools/night_v35_b11_b15_chain.sh (Blockbau 298-299, Schluessel-Abnahme im frischen Prozess 317-361,
# Arm-Variablen im Manifest-Diff 431-439, quicklook 186-223, Vorfilter 463-482, Lesart 498-522).
# ANGEPASST: Schluessel-Abnahme (Marker statt "kein Bootstrap", Vergleich ohne Arm-Variablen gegen den
# b16-Schluessel, Traegermenge wie b16), Manifest-Diff gegen b16 mit Wertpruefung der zwei Arm-Variablen,
# Vorfilter-Referenz b16 mit der b02-Umgebung der b16-Offline-Messung.
#
# KOSTEN (HERLEITUNG, nicht gemessen): Bloecke 400 Dateien rund 7 min (par.19.0 Punkt 5: 1.200 rund 20 min),
# Merge rund 6 min (b16 325 s, par.20b), Training rund 35 min (b16 2.086,8 s), Vorfilter unter 1 min (b16
# Offline 48 s fuer zwei Referenzen), Schnellblick 200 Partien x rund 18 s = rund 1 h (b16 Tor 1 17,74 /
# 18,23 s je Partie); zusammen rund 1,9 h.
#
# START: im Terminal-Tab mit Git-Bash, als DATEI:  bash tools/night_v35_b19_chain.sh
# KEINE PIPE dahinter, keine eigene Umleitung (ueber der 2-h-Grenze der Hintergrundaufgaben).
# Darf vor dem Ende der Vorgaenger gestartet werden: sie wartet, bis kein Prozess mit night_v35_<...>_chain
# (ausser dieser Kette selbst), tree_reuse_arena_chain oder quicklook_b18_chain in der Kommandozeile mehr
# laeuft (Deckel 40 h), danach auf eine freie Maschine (tools/lib/cpu_free.sh).
#
# WIEDERAUFNAHME:  RESUME=1 bash tools/night_v35_b19_chain.sh
# Liegende Schritte werden geprueft und wiederverwendet (Bloecke: liegende uebersprungen, Split-Listen mit
# Protokoll, Monolith mit passendem Stempel, Training: _resume.pth -> train.py --resume, finaler Stand mit
# laufzeit -> uebersprungen, Vorfilter-Artefakt, Schnellblick-Artefakte je Seed; ein Zwischenstand
# <out>.partial.json wird von paired_gating.py --resume fortgesetzt). Ohne RESUME (oder RESUME=0) bricht
# jede liegende b19-Datei die Kette ab (STOPP, nichts wird ueberschrieben).
#
# Exit des Arms: 0 = Schnellblick gelaufen, 34 = Vorfilter (b19 offline schlechter als b16, abgeschlossen,
# kein Schnellblick), sonst STOPP mit dem genannten Code.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

ART=evaluations/artifacts
SEED=20260965                                                # alle Arme einer Generation (par.12)
GEN=v34-b01                                                  # Generator des Fensters (Klassen-Praefix)
LOAD=v34-b01_brierbest                                       # Warmstart wie b02/b09/b16
N_VAL=120
SPEC=models/v34-b01_brierbest.spec.json                      # Schnellblick BEIDSEITS (par.19.0 Punkt 3)
ARM=v35-b19
ARM_MARKER="+bootstraptraj_h1_v1"                            # par.13, file_cache_key.py / corpus_dataset.py
B02_CARRIER=policy_carrier_manifest_v35_b02.json
B02_WIN=data/window_v35_b02                                  # b02-Val-Liste, NICHT neu ziehen
B02_VAL_POOL='^selfplay_v34-b01-'
B02_REF_MANIFEST=models/manifest_train_v35-b02_20261005_195355.json   # Vorfilter: b02-Umgebung/-Traegermaske
B09_CLASS=policy-s400-vol
B09_WIN=data/window_v35_b09                                  # Fensterliste von b09/b16, WIEDERVERWENDET
B09_SPLIT=$ART/v35_b09_split.txt
B03_SPLIT=$ART/v35_b03_split.txt
B16=v35-b16
B16_CARRIER=policy_carrier_manifest_v35_b16.json             # Traeger-Manifest von b16, WIEDERVERWENDET
B16_REF_MANIFEST=models/manifest_train_v35-b16_20261009_041044.json   # Manifest-Diff-Referenz
B16_SPLIT=$ART/v35_b16_split.txt                             # traegt den b16-Fenster-Schluessel
B16_PTH=models/alphazero_v35-b16_brierbest.pth               # Vorfilter-Referenz
OPP_MODEL=models/alphazero_v35-b16_brierbest.onnx            # Schnellblick-Gegner
# Pool = die fuenf b02-Klassen; die neue Klasse trifft NICHT (nach "policy" muss "_" folgen), wie b09/b16.
B09_VAL_POOL='^selfplay_v34-b01-(policy|policy-s400|policy-dice-v2-r1-s400|value-deviate-s400|value-excursion-s400)_'
B02_EXCLUDE='selfplay_v29-b11-probe_|selfplay_depth|selfplay_s4states|selfplay_tor2a|selfplay_probe-|selfplay_x35|selfplay_x35e2'
QUICK_SEEDS="20261700 20261701"
QUICK_PAIRS=50
# Alle Bootstrap-Knoepfe (file_cache_key.py _bootstrap_source_config) plus MOSAIC_TD_LAMBDA, wie
# night_v35_b11_b15_chain.sh:82; global AUS, nur die Arm-Subshell setzt die zwei b19-Variablen.
ALL_ARM_VARS="MOSAIC_BOOTSTRAP_SOURCE MOSAIC_BOOTSTRAP_HORIZON_ROUNDS MOSAIC_BOOTSTRAP_MARGIN_SCALE MOSAIC_BOOTSTRAP_TRAJ_LAMBDA MOSAIC_BOOTSTRAP_TRAJ_OPPONENT MOSAIC_BOOTSTRAP_TRAJ_MIX MOSAIC_BOOTSTRAP_TRAJ_CONF_SCALE MOSAIC_TD_LAMBDA"
# Vorgaenger: jede night_v35_<...>_chain AUSSER dieser (negativer Lookahead, sonst wartet die Kette auf sich
# selbst), die Tree-Reuse-Arena und der b18-Schnellblick. Klammer-Trick wie tools/lib/cpu_free.sh, Punkt 1.
PRED_PATTERN='[n]ight_v35_(?!b19_)[A-Za-z0-9_]*_chain|[t]ree_reuse_arena_chain|[q]uicklook_b18_chain'
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
for f in "$OPP_MODEL" "$B16_PTH" "models/alphazero_${LOAD}.pth" "$SPEC" "data/$B02_CARRIER" "data/$B16_CARRIER" \
         "${B02_WIN}_val.txt" "${B09_WIN}.txt" "${B09_WIN}.valfrac" "${B09_WIN}_train.txt" \
         "$B09_SPLIT" "$B03_SPLIT" "$B16_SPLIT" "$ART/v35_b02_split.txt" "$B02_REF_MANIFEST" "$B16_REF_MANIFEST" \
         engine/py/trajectory_bootstrap.py tools/brier_best_checkpoint.py tools/checkpoint_val_eval.py \
         tools/gating_block_z.py tools/paired_gating.py tools/window_train_split.py \
         tools/build_cache_incremental.py tools/probes/arena_column_probe.py tools/plate_points_from_arena.py; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
grep -q -- '"--fixed-length"' tools/paired_gating.py \
  || { echo "ABBRUCH: tools/paired_gating.py kennt --fixed-length nicht"; exit 1; }
NCLS=$(ls data/ | grep -c "^selfplay_${GEN}-${B09_CLASS}_.*\.pkl$")
[ "$NCLS" = "400" ] || { echo "ABBRUCH: data/ traegt ${NCLS} statt 400 Dateien selfplay_${GEN}-${B09_CLASS}_*.pkl"; exit 1; }
NW=$(grep -vc '^#' "${B09_WIN}.txt")
[ "$NW" = "1600" ] || { echo "ABBRUCH: ${B09_WIN}.txt hat $NW statt 1600 Dateien"; exit 1; }
NV=$(grep -vc '^#' "${B02_WIN}_val.txt")
[ "$NV" = "$N_VAL" ] || { echo "ABBRUCH: b02-Val-Liste hat $NV statt $N_VAL Dateien"; exit 1; }
if [ "$RESUME_MODE" != "1" ]; then
  for f in models/alphazero_${ARM}*.pth data/window_v35_b19_train.txt data/window_v35_b19_val.txt \
           "$ART/v35_b19_split.txt" "$ART"/checkpoint_val_eval_${ARM}_vs_*.json "$ART"/quicklook_${ARM}_vs_*.json; do
    [ -e "$f" ] && { echo "ABBRUCH: $f liegt schon -- von Hand pruefen oder RESUME=1"; exit 1; }
  done
fi
echo "Fruehpruefung GRUEN: 400 Dateien ${B09_CLASS}, Fenster ${B09_WIN}.txt 1600, b02-Val 120, Referenzen liegen"

# --- 0) Warten auf das Ende der anderen Ketten (Bauform b16-Kette:121-129) --------------------------
echo "########## v35-b19-KETTE WARTET auf das Ende von night_v35_*_chain (ausser b19), tree_reuse_arena_chain und quicklook_b18_chain $(date +%F' '%H:%M:%S)"
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
split_key() {  # $1 Split-Protokoll -> Fenster-Schluessel des Trainingsanteils
  grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$1" | awk '{print $NF}'
}
B02_KEY=$(split_key "$ART/v35_b02_split.txt"); B03_KEY=$(split_key "$B03_SPLIT")
B09_KEY=$(split_key "$B09_SPLIT"); B16_KEY=$(split_key "$B16_SPLIT")
for v in B02_KEY B03_KEY B09_KEY B16_KEY; do
  [ -n "${!v}" ] || { echo "STOPP: $v nicht lesbar (Split-Protokoll)"; exit 3; }
done
# Der b16-Schluessel muss der des b16-Trainings sein (cache_file im Manifest), sonst prueft 1e gegen Falsches.
python -X utf8 -c "import json,os,sys; c=json.load(open(sys.argv[1],encoding='utf-8'))['cli_args']['cache_file']; sys.exit(0 if os.path.basename(c)=='.cache_'+sys.argv[2]+'.h5' else 3)" "$B16_REF_MANIFEST" "$B16_KEY" \
  || { echo "STOPP: b16-Schluessel $B16_KEY passt nicht zu cache_file in $B16_REF_MANIFEST"; exit 3; }
echo "== v35-b19-KETTE   Start $(date +%F' '%H:%M:%S)"
echo "   Diff-Referenz $B16_REF_MANIFEST; Schluessel b16 $B16_KEY, b09 $B09_KEY, b03 $B03_KEY, b02 $B02_KEY"
echo "   Vorfilter-Referenz $B16_PTH (b02-Val-Satz, Umgebung/Traegermaske aus $B02_REF_MANIFEST); Gegner $OPP_MODEL"

# Bootstrap- und Datenschicht-Knoepfe global AUS (wie b16-Kette:145-146); nur run_b19 setzt die zwei Arm-Variablen.
unset $ALL_ARM_VARS MOSAIC_BOOTSTRAP_COHERENCE

wait_for_free_cpu "v35-b19-Kette"

# --- Gemeinsame Bausteine (laufen in der Subshell des Arms) ------------------------------------------

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

# Stempel und Schluessel-Abnahme des Monolithen (Bauform b11-b15-Kette:313-361 mit der Traegermengen-
# Pruefung der b16-Kette:192-199). Schluessel je in einem FRISCHEN Prozess (Bauform b11-b15: Import-
# Zeitpunkt-Knoepfe saehe ein In-Prozess-Umschalten nicht). $1 Schluessel, $2 Monolith, $3 Trainingsliste,
# $4 Traegerzahl soll, $5 Arm-Marker, $6 Arm-Umgebung als JSON, $7 Vergleichs-Schluessel ohne Arm-Variablen.
check_window_key() {
  python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; print('   Stempel:',k); sys.exit(0 if k==sys.argv[2] else 16)" "$2" "$1" \
    || { echo "STOPP $ARM: Stempel passt nicht zum Schluessel"; return 16; }
  python -X utf8 - "$1" "$2" "$3" "$4" "$MOSAIC_CARRIER_MANIFEST" "$5" "$6" "$7" <<'PYEOF'
import json, os, subprocess, sys
import h5py
key, cache, train_list, n_carriers, carrier, marker, arm_env_json, ref_key = sys.argv[1:9]
arm_env = json.loads(arm_env_json)
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
print("KEYJSON " + json.dumps({"key": k.key, "material": k.material,
                               "carriers": sorted(k.policy_carrier_set or ())}))
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
assert marker in on["material"], f"Marker {marker} fehlt im Schluesselmaterial"
assert on["material"].count("+bootstrap") == 1, "nicht genau ein Bootstrap-Marker im Material"
want = set(json.load(open(os.path.join("data", carrier), encoding="utf-8"))["policy_carrier_files"])
got = set(on["carriers"])
print(f"   Traegermenge im Schluessel: {len(got)} (soll {n_carriers}), gleich Manifest: {got == want}")
assert got == want and len(got) == int(n_carriers), "Traegermenge im Schluessel != Manifest"
off_env = {k: v for k, v in os.environ.items() if k not in arm_env}
off = window_key(off_env)
print(f"   Schluessel mit Arm-Variablen {on['key']}, ohne {off['key']}, Vergleich (b16) {ref_key}")
assert off["key"] == ref_key, "ohne Arm-Variablen NICHT der b16-Schluessel -- weitere Abweichung"
assert "+bootstrap" not in off["material"], "Bootstrap-Marker auch ohne Arm-Variablen im Material"
fp = h5py.File(cache, "r").attrs.get("mosaic_env_fingerprint", "")
fp = (fp.decode() if isinstance(fp, bytes) else str(fp)).split(";")
assert "MOSAIC_MASK_DICE_PHASE_VALUE=1" in fp, "Monolith-Fingerabdruck ohne Maske"
assert f"MOSAIC_CARRIER_MANIFEST={carrier}" in fp, "Monolith-Fingerabdruck ohne das Traeger-Manifest des Arms"
for n, v in arm_env.items():
    assert f"{n}={v}" in fp, f"Monolith-Fingerabdruck ohne {n}={v}"
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

# Manifest-Diff gegen ein Referenz-Manifest (Bauform b16-Kette:227-275), dazu die Wertpruefung der Arm-
# Variablen und von TD_LAMBDA (Bauform b11-b15-Kette:431-439). $1 Referenz-Manifest, $2 Referenz-Name,
# $3 erlaubte cli_args (Komma), $4 erlaubte mosaic_env-Abweichungen (Komma), $5 erwartete file_list,
# $6 erwarteter Val-Pool, $7 Arm-Umgebung als JSON (Sollwerte).
manifest_diff() {
  python -X utf8 - "$ARM" "$1" "$2" "$MOSAIC_CARRIER_MANIFEST" "$3" "$4" "$5" "$6" "$7" <<'PYEOF'
import glob, io, json, sys
arm, ref_path, ref_name, carrier, allowed_cli, allowed_env, want_list, want_pool, arm_env_json = sys.argv[1:10]
arm_env = json.loads(arm_env_json)
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
          ("MOSAIC_VAL_POOL", want_pool)] + sorted(arm_env.items())
for k, v in checks:
    if env.get(k) != v:
        print(f"   mosaic_env.{k}={env.get(k)!r} != {v!r}  <== STOPP"); env_bad.append(k + "(Wert)")
td = (m.get("python_constants") or {}).get("TD_LAMBDA")
want_td = float(arm_env.get("MOSAIC_TD_LAMBDA", "0.5"))
td_ok = td is not None and abs(float(td) - want_td) < 1e-12
print(f"   python_constants.TD_LAMBDA: {td!r} (erwartet {want_td}){'' if td_ok else '  <== STOPP'}")
if not td_ok:
    env_bad.append("TD_LAMBDA(Wert)")
print(f"   mosaic_env: {len(env_bad)} unerwartete Abweichungen (erlaubt {sorted(env_ok)}, Sollwerte {arm_env})")
sys.exit(17 if bad else (18 if env_bad else 0))
PYEOF
}

# Schnellblick EINES Seeds (Bauform b11-b15-Kette:186-223, Gegner b16). Rueckgabe != 0 nur ohne Artefakt.
quicklook() {  # $1 Seed
  local OUT="$ART/quicklook_${ARM}_vs_${B16}_s${1}.json"
  local G0
  G0=$(date +%s)
  if [ -f "$OUT" ]; then
    if [ "$RESUME_MODE" = "1" ]; then
      echo "   RESUME: $OUT liegt schon -- Seed $1 uebersprungen"
      if [ ! -f "$ART/plate_points_quicklook_${ARM}_vs_${B16}_s${1}.json" ]; then
        echo "   Auswertungen zu Seed $1 fehlen -- werden nachgezogen"
        python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
        python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
          --out "$ART/plate_points_quicklook_${ARM}_vs_${B16}_s${1}.json"
      fi
      return 0
    fi
    echo "   STOPP $ARM: $OUT liegt schon -- wird nicht ueberschrieben"; return 1
  fi
  echo ""
  echo "===== Schnellblick $ARM gegen $B16, Seed $1   Start $(date +%F' '%H:%M:%S)"
  [ -f "${OUT}.partial.json" ] && echo "   Zwischenstand ${OUT}.partial.json liegt -- paired_gating.py --resume setzt dort fort"
  # --fixed-length: genau $QUICK_PAIRS Paare, SPRT nur mitgeschrieben (paired_gating.py, 2026-10-08).
  # --resume setzt einen liegenden Zwischenstand fort; ohne ihn laeuft der Lauf normal.
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$A" --spec-a "$SPEC" --model-b "$OPP_MODEL" --spec-b "$SPEC" \
    --name-a "$ARM" --name-b "$B16" \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs $QUICK_PAIRS --fixed-length --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$1" --threads 10 --log-games --no-promote-winner --out "$OUT" --resume
  local RCG=$?
  echo "   Exit $RCG ($(date +%H:%M:%S))"
  # Sechs Standard-Kennzahlen (CLAUDE.md): Spalten/Reihen/Strafleiste aus den Partie-Logs,
  # Punkte je Wertungsplatte; eigene Punkte und Margin stehen im Artefakt.
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_quicklook_${ARM}_vs_${B16}_s${1}.json"
  echo "   Ende Seed $1: $(date +%F' '%H:%M:%S), $(( $(date +%s) - G0 )) s Wanduhr"
  [ $RCG -eq 0 ] && [ -f "$OUT" ]
}

# --- ARM v35-b19 (par.21) --------------------------------------------------------------------------
run_b19() {
  local WIN=$B09_WIN                     # Fensterliste von b09/b16 (Manifest-Diff erlaubt kein file_list)
  local SPLIT_TRAIN=data/window_v35_b19_train.txt SPLIT_VAL=data/window_v35_b19_val.txt
  local SPLIT_OUT="$ART/v35_b19_split.txt"
  echo ""
  echo "############################## ARM $ARM (Trajektorien-Bootstrap k = 1 auf dem b16-Fenster, par.21)   Start $(date +%F' '%H:%M:%S)"
  # Trainings-Umgebung byte-gleich b16 (Traeger-Manifest b16, Val-Pool der fuenf b02-Klassen) plus die zwei
  # Arm-Variablen (par.13, Bauform b03). Sie gelten fuer Blockbau, Merge, Schluessel-Abnahme und Training.
  export_train_env "$B16_CARRIER" "$B09_VAL_POOL"
  unset $ALL_ARM_VARS
  export MOSAIC_BOOTSTRAP_SOURCE=trajectory MOSAIC_BOOTSTRAP_HORIZON_ROUNDS=1
  local ARM_ENV_JSON
  ARM_ENV_JSON=$(python -X utf8 -c "import json,os,sys; print(json.dumps({n: os.environ[n] for n in sys.argv[1:] if n in os.environ}))" $ALL_ARM_VARS)
  echo "   Arm-Umgebung $ARM_ENV_JSON, Marker $ARM_MARKER"
  wait_for_free_cpu "$ARM Fenster"

  step_begin "$ARM 1a) Fensterliste ${WIN}.txt pruefen (b09/b16-Fenster, wiederverwendet: b02 1.200 + $B09_CLASS 400)"
  # Gleiche Pruefung wie b16-Kette 1a (Z. 394-417).
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

  step_begin "$ARM 1b) Bloecke unter $ARM_MARKER: fehlende bauen (erwartet 400 $B09_CLASS), liegende uebersprungen"
  # Zaehlung mit derselben Pfadfunktion wie die Bauschleife (build_cache_incremental._block_path, Z. 111-124)
  # in der Arm-Umgebung. Die 1.200 b02-Bloecke liegen unter dem Marker seit b03 (par.13a); fehlt einer davon,
  # hiesse das geaenderter Datei-Schluessel (Rezept, Knopf) -- STOPP statt stiller Nachbau.
  count_missing_blocks() {  # $1 Modus: "pre" (vor dem Bau) oder "post" (danach, muss 0 sein)
    python -X utf8 - "${WIN}.txt" "$B09_CLASS" "$1" "$RESUME_MODE" <<'PYEOF'
import os, sys
sys.path.insert(0, "tools")
from build_cache_incremental import _block_path
win, cls, mode, resume = sys.argv[1:5]
kw = dict(encoder="2d", value_target_variant="nortv", conjunction_head=False)
names = [l.strip() for l in open(win, encoding="utf-8") if l.strip() and not l.startswith("#")]
miss = [n for n in names if not os.path.exists(_block_path("data", n, kw))]
other = [n for n in miss if f"-{cls}_" not in n]
print(f"   {len(names)} Dateien: {len(names) - len(miss)} Bloecke liegen, {len(miss)} zu bauen "
      f"(davon {len(miss) - len(other)} {cls}, {len(other)} andere)" + (f", z.B. {miss[:2]}" if miss else ""))
if len(names) != 1600:
    sys.exit(1)
if mode == "post":
    sys.exit(0 if not miss else 1)
if other:
    print("   fehlende Bloecke AUSSERHALB der neuen Klasse (b02-Bloecke unter dem Marker liegen seit b03)  <== STOPP")
    sys.exit(1)
if resume != "1" and len(miss) != 400:
    print(f"   erwartet 400 fehlende Bloecke, gefunden {len(miss)} (RESUME=0)  <== STOPP")
    sys.exit(1)
sys.exit(0)
PYEOF
  }
  count_missing_blocks pre || { echo "STOPP $ARM: Blockbestand unter $ARM_MARKER nicht wie erwartet -- von Hand pruefen"; exit 11; }
  # Bauform b11-b15-Kette:298-299 (ohne --merge-out: nur Bloecke; liegende meldet das Werkzeug als uebersprungen).
  python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
    --value-target-variant nortv --workers 6 --file-list "${WIN}.txt"
  RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
  [ $RC -eq 0 ] || { echo "STOPP $ARM: Blockbau mit Exit $RC"; exit 11; }
  count_missing_blocks post || { echo "STOPP $ARM: nach dem Bau fehlen noch Bloecke"; exit 11; }
  step_end

  step_begin "$ARM 1c) Traeger-Manifest data/$B16_CARRIER = alle 1.600 Dateien von ${WIN}.txt (wiederverwendet)"
  python -X utf8 - "$B16_CARRIER" "${WIN}.txt" <<'PYEOF'
import json, sys
name, win = sys.argv[1:3]
f = json.load(open(f"data/{name}", encoding="utf-8"))["policy_carrier_files"]
w = [l.strip() for l in open(win, encoding="utf-8") if l.strip() and not l.startswith("#")]
print(f"   Manifest {name}: {len(f)} Traeger, Fenster {len(w)} Dateien")
assert len(f) == 1600 and len(set(f)) == 1600 and set(f) == set(w), "Manifest != die 1.600 Fensterdateien"
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
  KEY=$(split_key "$SPLIT_OUT")
  [ -n "$KEY" ] || { echo "STOPP $ARM: kein Schluessel"; exit 13; }
  for ref in "b16:$B16_KEY" "b09:$B09_KEY" "b03:$B03_KEY" "b02:$B02_KEY"; do
    [ "$KEY" != "${ref#*:}" ] || { echo "STOPP $ARM: Schluessel $KEY == ${ref%%:*}-Schluessel -- Marker wirkt nicht"; exit 13; }
  done
  echo "   neuer Fenster-Schluessel $KEY (verschieden von b16 $B16_KEY, b09 $B09_KEY, b03 $B03_KEY, b02 $B02_KEY)"
  CACHE="data/.cache_${KEY}.h5"
  step_end

  step_begin "$ARM 1e) Monolith unter dem neuen Schluessel $KEY (Merge aus den Bloecken unter $ARM_MARKER)"
  # RESUME: Stempel zuletzt geschrieben (build_cache_parallel.py:203-205), liegt er passend, war der Merge
  # durch (Bauform b16-Kette:496-506). check_window_key laeuft in beiden Faellen.
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
  check_window_key "$KEY" "$CACHE" "$SPLIT_TRAIN" 1600 "$ARM_MARKER" "$ARM_ENV_JSON" "$B16_KEY" || exit $?
  echo "##### FENSTER $ARM STEHT $(date +%F' '%H:%M:%S) -- Monolith $CACHE"
  step_end

  # ABBRUCH? Die ganze Kette mit RESUME=1 neu starten (dann entscheidet der Zustand unten).
  step_begin "$ARM 1f) Training -- WARMSTART von $LOAD (Rezept b02/b09/b16)"
  if [ "$RESUME_MODE" = "1" ]; then
    # Bauform b16-Kette:512-545 (train.py: Zwischenstand je Epoche _resume.pth, am Ende laufzeit ins Manifest).
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
  [ $RC -eq 0 ] || { echo "STOPP $ARM: Training mit Exit $RC -- kein Vorfilter, kein Schnellblick"; exit 20; }
  step_end

  step_begin "$ARM 1g) Manifest-Diff gegen $B16_REF_MANIFEST (erlaubt name, cache_file und die zwei Arm-Variablen)"
  manifest_diff "$B16_REF_MANIFEST" "$B16" "name,cache_file" "MOSAIC_BOOTSTRAP_SOURCE,MOSAIC_BOOTSTRAP_HORIZON_ROUNDS" \
    "${WIN}.txt" "$B09_VAL_POOL" "$ARM_ENV_JSON"
  RC=$?
  [ $RC -eq 0 ] || { echo "STOPP $ARM: Manifest-Diff/mosaic_env mit Exit $RC -- kein Vorfilter, kein Schnellblick"; exit 17; }
  step_end

  step_begin "$ARM 1h) Vorfilter (par.19.0 Punkt 2, Referenz b16): b16 gegen $ARM auf dem b02-Val-Satz"
  local BEST_PTH PRE_OUT
  BEST_PTH=$(python -X utf8 tools/brier_best_checkpoint.py "$ARM" --ext pth)
  [ -n "$BEST_PTH" ] && [ -f "$BEST_PTH" ] || { echo "STOPP $ARM: kein Brier-bestes $ARM-Netz (.pth)"; exit 31; }
  PRE_OUT="$ART/checkpoint_val_eval_${ARM}_vs_b16.json"
  if [ "$RESUME_MODE" = "1" ] && [ -f "$PRE_OUT" ]; then
    echo "   RESUME: $PRE_OUT liegt schon -- wiederverwendet"
  else
    # Gleiche Messumgebung wie die b16-Offline-Messung (b16-Kette:569-571): --train-manifest b02, das Werkzeug
    # setzt die MOSAIC_*-Umgebung aus dem Manifest und bricht bei einer GESETZTEN abweichenden Variable ab
    # (checkpoint_val_eval.py resolve_env_and_recipe); Traeger-Manifest und Val-Pool darum auf b02. Die zwei
    # Bootstrap-Variablen stehen nicht im b02-Manifest (dort nur WARNUNG, kein Abbruch); sie werden fuer den
    # Aufruf entfernt, damit b16 und b19 auf denselben Daten wie die b16-Offline-Messung verglichen werden
    # (der Val-Brier rechnet gegen wdl_outcome, par.13).
    env -u MOSAIC_BOOTSTRAP_SOURCE -u MOSAIC_BOOTSTRAP_HORIZON_ROUNDS \
      MOSAIC_CARRIER_MANIFEST="$B02_CARRIER" MOSAIC_VAL_POOL="$B02_VAL_POOL" \
      python -X utf8 -u tools/checkpoint_val_eval.py --checkpoints "$B16_PTH" "$BEST_PTH" \
      --val-list "${B02_WIN}_val.txt" --train-manifest "$B02_REF_MANIFEST" --out "$PRE_OUT"
    RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
    [ $RC -eq 0 ] && [ -f "$PRE_OUT" ] || { echo "STOPP $ARM: checkpoint_val_eval.py gescheitert"; exit 32; }
  fi
  # Referenz = erster Checkpoint = b16; Feld = b16 minus b19. CI ganz UNTER 0: b16 hat den kleineren Brier,
  # b19 ist schlechter -> abgeschlossen ohne Schnellblick.
  python -X utf8 - "$PRE_OUT" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
(path, lists), = d["differences_reference_minus_checkpoint"].items()
a = lists["all"]
ci = a["value_val_brier_diff_ci95"]
print(f"   Referenz {d['reference']} minus {path} (Val {d['val_list']['n_files']} Dateien, "
      f"Selbstpruefung {d.get('selfcheck_overall')}):")
print(f"   Val-Brier b16 minus b19: {a['value_val_brier_diff']}, CI95 {ci}  (< 0 = b19 hat den GROESSEREN Brier)")
print(f"   Policy-CE gepoolt b16 minus b19: {a['policy_val_loss_pooled_diff']}, CI95 {a['policy_val_loss_pooled_diff_ci95']}")
for c in d.get("checkpoints", []):
    l = (c.get("lists") or {}).get("all") or {}
    print(f"   {c.get('path')}: Brier {l.get('value_val_brier')}, policy_val_loss {l.get('policy_val_loss')}, "
          f"pooled {l.get('policy_val_loss_pooled')}")
if ci is None:
    print("   kein CI -- Vorfilter nicht entscheidbar  <== STOPP"); sys.exit(32)
if ci[1] < 0:
    print("   CI GANZ UNTER 0: b19 schlechter -> abgeschlossen, KEIN Schnellblick (par.19.0 Punkt 2)"); sys.exit(34)
print("   CI nicht ganz unter 0 -> Schnellblick")
PYEOF
  RC=$?
  step_end
  [ $RC -eq 34 ] && { echo "ENDE $ARM: Vorfilter -- b19 offline schlechter als b16, kein Schnellblick"; exit 34; }
  [ $RC -eq 0 ] || { echo "STOPP $ARM: Vorfilter mit Exit $RC"; exit 32; }

  # Geblickt wird mit dem Brier-besten Netz nach der Regel von train.py, aus dem Manifest gelesen
  # (brier_best_checkpoint.py: _brierbest, wenn es getrennt liegt, sonst _best oder der finale Stand).
  A=$(python -X utf8 tools/brier_best_checkpoint.py "$ARM" --ext onnx)
  [ $? -eq 0 ] && [ -n "$A" ] && [ -f "$A" ] || { echo "STOPP $ARM: brier_best_checkpoint.py findet kein Netz (.onnx)"; exit 15; }
  echo "##### TRAINING $ARM DURCH $(date +%F' '%H:%M:%S) -- Schnellblick mit $A"

  wait_for_free_cpu "Schnellblick $ARM"
  step_begin "$ARM 2) Schnellblick gegen $B16 (feste Laenge, Seeds $QUICK_SEEDS a $QUICK_PAIRS Paare)"
  for s in $QUICK_SEEDS; do
    quicklook "$s" || { echo "STOPP $ARM: Schnellblick Seed $s ohne Artefakt"; exit 21; }
  done
  step_end

  step_begin "$ARM 3) Lesart par.19.0 Punkt 4 (gepoolt, Gegner b16)"
  set -- $QUICK_SEEDS
  python -X utf8 tools/gating_block_z.py "$ART/quicklook_${ARM}_vs_${B16}_s$1.json" "$ART/quicklook_${ARM}_vs_${B16}_s$2.json"
  step_end
  echo "############################## ARM $ARM FERTIG $(date +%F' '%H:%M:%S)"
  exit 0
}

# --- Arm in einer SUBSHELL: ein STOPP (exit) beendet nur den Arm, die Zusammenfassung laeuft trotzdem ---
T0=$(date +%s)
( run_b19 )
RC=$?
case $RC in
  0)  ST="durch (Schnellblick gelaufen)" ;;
  34) ST="Vorfilter: offline schlechter als b16, kein Schnellblick" ;;
  *)  ST="STOPP Exit $RC" ;;
esac
printf '%s\t%s\t%s\n' "$ARM" "$ST" "$(( $(date +%s) - T0 ))" >> "$SUMMARY_FILE"
echo "== Arm $ARM: $ST, $(( $(date +%s) - T0 )) s Wanduhr"

# --- Zusammenfassung ------------------------------------------------------------------------------
echo ""
echo "########## v35-b19-KETTE FERTIG $(date +%F' '%H:%M:%S) -- Zusammenfassung"
python -X utf8 - "$SUMMARY_FILE" "$STEPS_FILE" "$ART" "$ARM" "$B16" "$B16_REF_MANIFEST" "$QUICK_SEEDS" <<'PYEOF'
import glob, json, os, subprocess, sys
sys.path.insert(0, os.path.join(os.getcwd(), "tools"))
from gating_block_z import block_shares, block_z
summary, steps, art, arm, opp, b16_manifest, seeds = sys.argv[1:8]
step_rows = [l.rstrip("\n").split("\t", 2) for l in open(steps, encoding="utf-8") if l.strip()]

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

mins, n_ep = history_minima(b16_manifest)
print(f"\nReferenz {opp} ({os.path.basename(b16_manifest)}): " + ", ".join(
    f"{k} Minimum {v:.5f} in Epoche {ep}" for k, (v, ep) in mins.items()))
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
    print("   (policy_val_loss b19 und b16: gleiche Traegermaske b16 und gleicher Val-Satz, vergleichbar;"
          " value_val_loss NICHT, b19 mischt ein anderes Ziel, par.13a)")
    lz = json.load(open(ms[-1], encoding="utf-8")).get("laufzeit") or {}
    print(f"   Training: {lz.get('wanduhr_s')} s Wanduhr, {lz.get('samples')} Samples (b16: 2.832.807, par.20a)")
r = subprocess.run([sys.executable, "-X", "utf8", "tools/brier_best_checkpoint.py", arm, "--ext", "onnx"],
                   capture_output=True, text=True, encoding="utf-8")
if r.returncode == 0:
    print(f"   Brier-bestes Netz: {r.stdout.strip()}")
off = f"{art}/checkpoint_val_eval_{arm}_vs_b16.json"
if os.path.exists(off):
    d = json.load(open(off, encoding="utf-8"))
    for path, lists in d["differences_reference_minus_checkpoint"].items():
        a = lists["all"]
        print(f"   Offline b16 minus b19: Brier {a['value_val_brier_diff']} CI95 {a['value_val_brier_diff_ci95']}; "
              f"Policy-CE gepoolt {a['policy_val_loss_pooled_diff']} CI95 {a['policy_val_loss_pooled_diff_ci95']}"
              f"  (> 0 = b19 besser)")
else:
    print(f"   Offline: kein Artefakt {off}")
paths = [p for p in (f"{art}/quicklook_{arm}_vs_{opp}_s{s}.json" for s in seeds.split()) if os.path.exists(p)]
wins = games = 0
shares = []
for p in paths:
    d = json.load(open(p, encoding="utf-8"))
    n = d.get("n_games_total") or 0
    wins += d["a_wins_total"]; games += n
    sh = block_shares(p)
    shares.extend(sh)
    z1 = block_z(sh)["z"]
    wr = f"{d['a_wins_total'] / n:.4f}" if n else "?"
    sa, sb = d.get("avg_score_a"), d.get("avg_score_b")
    marg = f"{sa - sb:+.2f}" if sa is not None and sb is not None else "?"
    print(f"   Schnellblick {os.path.basename(p)}: {d['a_wins_total']}:{d.get('b_wins_total')} von {n}, Siegquote {wr}, "
          f"Block-z {'n/a' if z1 is None else f'{z1:+.2f}'}, Punkte {fmt(sa)} / {fmt(sb)} (Margin {marg}), "
          f"Strafsteine {fmt(d.get('avg_floor_a'))} / {fmt(d.get('avg_floor_b'))}, "
          f"SPRT-Beruehrung {d.get('sprt_first_crossing')}")
print("   Spalten und Plattenpunkte je Seed: arena_columns_quicklook_* und plate_points_quicklook_*-Artefakte in", art)
print(f"\nLESART par.19.0 Punkt 4 (mechanisch, Verdikt beim Koordinator), Gegner {opp}:")
if not paths or not games:
    print("   kein Schnellblick-Artefakt (Vorfilter oder STOPP) -- keine Lesart")
else:
    wr = wins / games
    z = block_z(shares)["z"] if shares else None
    if len(paths) < 2:
        print("   NUR EIN SEED: Lesart nur vorlaeufig")
    if wr >= 0.55 or (z is not None and z >= 1.5):
        verdict = "SPANNEND -> volle Breite gegen b16 faellig -- startet NICHT automatisch, Nutzer-Entscheid"
    elif wr < 0.45:
        verdict = "abgeschlossen mit Gegenbefund (unter 45 %)"
    else:
        verdict = "abgeschlossen, kein Hebel (45-55 %, Block-z unter +1,5)"
    print(f"   gepoolt ({len(paths)} Seeds): {wins} von {games} = {wr:.4f}, Block-z "
          f"{'n/a' if z is None else f'{z:+.2f}'} ({len(shares)} Bloecke) -> {verdict}")
PYEOF
rm -f "$SUMMARY_FILE" "$STEPS_FILE"
echo ""
echo "   Faellig danach (par.21): Lesart in die Prereg (Kopf Zeile 1 und Index), Vorfilter-Zahlen, sechs"
echo "   Standard-Kennzahlen je Seite (arena_column_probe, plate_points_quicklook), Laufzeiten in Prereg und"
echo "   docs/measured_runtimes.md; volle Breite gegen b16 NUR nach Nutzer-Entscheid."
