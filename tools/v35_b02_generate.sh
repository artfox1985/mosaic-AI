#!/usr/bin/env bash
# v35-b02-ERZEUGUNG (evaluations/PREREG_v35_window.md par.12; Nutzer-Entscheid 2026-10-04 spaet: "b02 voll"):
# das v35-Fenster komplett mit 400 Sims und Stichentscheid Modus 2 neu erzeugen, vier Klassen aus
# models/v35_b02.recipe.json. Vorlagen: tools/v35_sockel_generate.sh, tools/night_v35_swarm.sh.
#   1. Rezept- und Wheel-Pruefung (888/414), Waechter je Klasse drucken.
#   2. Smoke je Klasse: 10 Partien nach data/probe_v35b02_smoke, --version smoke-v35b02-<klasse>,
#      danach Manifest-Abnahme (Sims 400, tau_tiebreak_q 2, r5_net_sims 400, Klassen-Knoepfe).
#      ROT = STOPP vor der Erzeugung.
#   3. Cache-Waechter im Hintergrund (Nutzer: "lass den cache waechter gleich mitlaufen"), Umgebung
#      wie das Training der Kette, damit die Bloecke den Trainings-Schluessel treffen (Begruendung
#      am Startpunkt unten).
#   4. Erzeugung policy-s400, policy-dice-v2-r1-s400, value-deviate-s400, value-excursion-s400,
#      jede mit Exit-Pruefung und Zeitstempel.
#   5. Abnahmen nach par.8 (nur gedruckt, nicht fatal): Tor 0 je Klasse, Spiegelknopf,
#      KL-Abnahme am Ausflug, Vollstaendigkeit (Feld completed) je Klasse.
#   6. Warten, bis der Cache-Waechter von selbst endet (Leerlauf).
# Watchdog-/Deadline-/Haenger-Zeilen stehen nur in der Terminal-Ausgabe dieses Skripts; das
# Skript zaehlt sie nicht (Abnahme par.8 von Hand am Terminal-Rest).
#
# KEINE PIPE, keine eigene Umleitung; als DATEI starten (im Terminal-Tab mit Git-Bash; die Erzeugung
# dauert rund 14 h, weit ueber der 2-h-Grenze der Hintergrundaufgaben). Normalerweise aus
# tools/night_v35_b02_chain.sh aufgerufen.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
RECIPE=models/v35_b02.recipe.json
SMOKE_DIR=data/probe_v35b02_smoke
GEN=v34-b01
GEN_PTH=models/alphazero_v34-b01_brierbest.pth               # Generator fuer die KL-Abnahme (.pth)
CLASSES="policy-s400 policy-dice-v2-r1-s400 value-deviate-s400 value-excursion-s400"
. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
step() { echo ""; echo "===== $1 $(date +%F' '%H:%M:%S)"; }
fail() { echo "STOPP: $1 ($(date +%F' '%H:%M:%S))"; exit "${2:-10}"; }

for f in "$RECIPE" models/v35_generation.spec.json models/alphazero_v34-b01_brierbest.onnx "$GEN_PTH"; do
  [ -f "$f" ] || fail "$f fehlt" 1
done
for c in $CLASSES; do
  # "${c}_" mit Unterstrich: "policy-s400_" trifft nicht die vorhandenen "policy_"/"policy-s100_".
  if ls data/ | grep -q "^selfplay_${GEN}-${c}_"; then fail "data/ traegt schon ${c}-Dateien" 4; fi
  if ls data/ | grep -q "^manifest_${GEN}-${c}_"; then fail "data/ traegt schon ein ${c}-Manifest" 4; fi
done
if [ -d "$SMOKE_DIR" ] && [ -n "$(ls -A "$SMOKE_DIR" 2>/dev/null)" ]; then
  fail "$SMOKE_DIR ist nicht leer -- Reste eines frueheren Smokes von Hand beiseitelegen" 4
fi
wait_for_free_cpu "v35-b02-Erzeugung"

step "1 Rezept- und Wheel-Pruefung"
python -X utf8 - "$RECIPE" <<'PYEOF' || fail "Rezept- oder Wheel-Pruefung rot" 3
import json, sys
sys.path.insert(0, "tools")
import mosaic_rust
from recipe_config import load_recipe, expected_engine_config
r = load_recipe(sys.argv[1])
d = json.loads(mosaic_rust.engine_config_json())
print(f"   engine_config: input_size {d.get('input_size')} num_actions {d.get('num_actions')} "
      f"contract {d.get('contract_hash')}; Rezept sha256 {r.sha256[:12]}")
if str(d.get("input_size")) != "888" or str(d.get("num_actions")) != "414":
    print("ABBRUCH: Wheel traegt nicht 888/414"); sys.exit(3)
for c in r["classes"]:
    print(f"   {c}: version {r['classes'][c]['version']}, seed {r['classes'][c]['seed']}, "
          f"Waechter {expected_engine_config(r, c)}")
PYEOF

step "2 Smoke je Klasse (10 Partien nach $SMOKE_DIR)"
for c in $CLASSES; do
  echo "-- Smoke $c ($(date +%H:%M:%S))"
  MOSAIC_DATA_DIR="$SMOKE_DIR" python -X utf8 -u self_play.py --recipe "$RECIPE" --class "$c" \
    --games 10 --version "smoke-v35b02-$c"
  RC=$?
  echo "   Smoke $c Exit $RC ($(date +%H:%M:%S)), Dateien: $(ls "$SMOKE_DIR" 2>/dev/null | grep -c "^selfplay_smoke-v35b02-${c}_")"
  [ $RC -eq 0 ] || fail "Smoke $c rot -- keine Erzeugung" 11
  # Manifest-Abnahme. Feldorte (gelesen an data/manifest_v34-b01-policy_20261004_131853.json und
  # data/manifest_v34-b01-value-{deviate,excursion}_*.json): Sims in cli_args.sims (engine_config
  # traegt KEINE Sims), r5_net_sims nur in spec_file.content, tau_tiebreak_q/excursion_kl_weight/
  # dome_dice* in engine_config, value-only als cli_args.pcr_full_prob 0.0 (self_play.py:1834-1839),
  # Waechter-Ergebnis in recipe.engine_config_check.deviations.
  python -X utf8 - "$SMOKE_DIR" "$c" <<'PYEOF' || fail "Smoke-Manifest $c rot -- keine Erzeugung" 11
import glob, json, os, sys
smoke_dir, cls = sys.argv[1:3]
ms = sorted(glob.glob(os.path.join(smoke_dir, f"manifest_smoke-v35b02-{cls}_*.json")))
if not ms:
    print(f"   ROT: kein Manifest manifest_smoke-v35b02-{cls}_*.json in {smoke_dir}"); sys.exit(1)
m = json.load(open(ms[-1], encoding="utf-8"))
cli, ec = m.get("cli_args", {}), m.get("engine_config", {})
spec = (m.get("spec_file") or {}).get("content", {})
rec = m.get("recipe") or {}
env = {k: v for k, v in (m.get("mosaic_env") or {}).items() if k != "MOSAIC_DATA_DIR"}
lz = m.get("laufzeit") or {}
checks = [
    ("cli_args.sims", cli.get("sims"), 400),
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
    # Ausflug-Klasse: laufzeit.partien zaehlt die 10 Ausfluege mit (excursion_prob 1.0; PREREG_v35_window.md
    # par.9 "Ausfluege mitgezaehlt"), also 20; sonst 10. Erster Lauf 2026-10-05 00:12 stoppte genau hier.
    ("laufzeit.partien", lz.get("partien"), 20 if cls == "value-excursion-s400" else 10),
]
per_class = {
    "policy-s400": [("engine_config.excursion_kl_weight", ec.get("excursion_kl_weight"), 0),
                    ("engine_config.dome_dice", ec.get("dome_dice"), 0),
                    ("cli_args.deviate_prob", cli.get("deviate_prob"), 1.0),
                    ("cli_args.excursion_prob", cli.get("excursion_prob"), 0.0),
                    ("cli_args.pcr_full_prob", cli.get("pcr_full_prob"), None)],
    "policy-dice-v2-r1-s400": [("engine_config.excursion_kl_weight", ec.get("excursion_kl_weight"), 0),
                               ("engine_config.dome_dice", ec.get("dome_dice"), 1),
                               ("engine_config.dome_dice_sims", ec.get("dome_dice_sims"), 600),
                               ("engine_config.dome_dice_last_round", ec.get("dome_dice_last_round"), 1),
                               ("engine_config.dome_dice_place_eps", ec.get("dome_dice_place_eps"), 0.02),
                               ("engine_config.dome_dice_prior_temp", ec.get("dome_dice_prior_temp"), 2.0),
                               ("engine_config.dome_dice_source_rule", ec.get("dome_dice_source_rule"),
                                "prior_tempered_over_display_slots_and_stack_top"),
                               ("cli_args.deviate_prob", cli.get("deviate_prob"), 1.0),
                               ("cli_args.pcr_full_prob", cli.get("pcr_full_prob"), None)],
    "value-deviate-s400": [("engine_config.excursion_kl_weight", ec.get("excursion_kl_weight"), 0),
                           ("cli_args.deviate_prob", cli.get("deviate_prob"), 1.0),
                           ("cli_args.excursion_prob", cli.get("excursion_prob"), 0.0),
                           ("cli_args.pcr_full_prob", cli.get("pcr_full_prob"), 0.0),
                           ("engine_config.dome_dice", ec.get("dome_dice"), 0)],
    "value-excursion-s400": [("engine_config.excursion_kl_weight", ec.get("excursion_kl_weight"), 1),
                             ("cli_args.excursion_prob", cli.get("excursion_prob"), 1.0),
                             ("cli_args.add_root_noise", cli.get("add_root_noise"), False),
                             ("cli_args.pcr_full_prob", cli.get("pcr_full_prob"), 0.0),
                             ("engine_config.dome_dice", ec.get("dome_dice"), 0)],
}
checks += per_class[cls]
bad = [(n, got, want) for n, got, want in checks if got != want]
for n, got, want in checks:
    print(f"   {'ok ' if got == want else 'ROT'} {n} = {got!r}" + ("" if got == want else f" (erwartet {want!r})"))
print(f"   Manifest {ms[-1]}: {len(checks) - len(bad)}/{len(checks)} gruen, "
      f"{lz.get('s_je_partie')} s je Partie im Smoke")
sys.exit(1 if bad else 0)
PYEOF
done

# 3 CACHE-WAECHTER (Nutzer 2026-10-04: "lass den cache waechter gleich mitlaufen").
# Umgebung = die des Trainings in tools/night_v35_b02_chain.sh, sonst trifft der Block-Schluessel
# nicht: der Block-Schluessel liest MOSAIC_FEATURES_FROM_RUST, MOSAIC_IGNORE_POLICY_TARGET_VALID,
# MOSAIC_MASK_DICE_PHASE_VALUE und MOSAIC_MOON_TARGET_SOURCE (engine/py/file_cache_key.py:39, 68,
# 75-76 ueber neural_net._IGNORE_PTV, 178/336-337), aber NICHT das Traeger-Manifest: das Material
# traegt das Literal "|carrier=1" (file_cache_key.py:271), die Traegermaske kommt erst beim Merge.
# MOSAIC_CARRIER_MANIFEST darf deshalb gesetzt sein, obwohl das Manifest erst in der Kette entsteht:
# fehlt die Datei, liefert _load_manifest (None, None, pfad) und der Waechter druckt nur "KEINS"
# (tools/build_cache_incremental.py:96-107), kein Abbruch; im Datei-Bau gibt corpus_dataset.py:566-578
# hoechstens einen Hinweis aus. Gesetzt bleibt es, damit die Umgebung byte-gleich zur Kette ist.
# NUR DIE NEUEN DATEIEN: --watch nimmt ALLE data/*.pkl ohne Block unter dem aktuellen Schluessel
# (build_cache_incremental.py:182-184, _files ohne --file-list; --file-list ist mit --watch nicht
# kombinierbar, Z. 236-238). Einzige Einschraenkung ist MOSAIC_DATA_EXCLUDE (Regex auf den
# Basename, Z. 182-184). Ohne Zusatz baute der Waechter im ersten Durchgang auch die 2.192
# Altdateien v31-b01/v32-b01/v33-b01 (496 + 496 + 1.200, ls data/ am 2026-10-04; ob dort schon
# Masken-Bloecke liegen, ist UNGEPRUEFT, vermutlich nicht: die b01-Kette baute nur ihr Fenster)
# und die vier @100-Klassen von v34-b01. HERLEITUNG aus docs/measured_runtimes.md Z. 93 (400 Dateien,
# 3 Arbeiter, 18,8 min): rund 1,7 h Nebenbau fuer Dateien, die in keinem b02-Fenster stehen.
# Darum NUR FUER DEN WAECHTER die Exclude-Regex der Kette plus diese Praefixe. Der Block-Schluessel
# liest MOSAIC_DATA_EXCLUDE nicht (grep file_cache_key.py: 0 Treffer), die Bloecke sind also
# dieselben, die die Kette mit ihrer eigenen Regex adressiert. Uebrig bleiben policy_ (100, Bloecke
# aus der b01-Kette, ANNAHME: liegen unter demselben Schluessel und werden uebersprungen) und die
# vier -s400-Klassen.
# Nebenlast: 3 Arbeiter neben der Erzeugung, gemessen ohne Durchsatzverlust (measured_runtimes.md
# Z. 93). Leerlauf: Dateien landen im Abstand von rund 60 s (Dateizeiten von policy_ am 2026-10-04,
# @400), 10 leere Durchgaenge a 60 s beenden den Waechter also erst rund 10 min nach der letzten
# Datei; zwischen zwei Klassen liegt nur der Start der naechsten (unter 2 min).
# Die Variablen stehen in einer Subshell: self_play.py schreibt ALLE MOSAIC_* des Elternprozesses
# ins Manifest (selfplay_manifest.py:129), die Erzeugung darf sie nicht sehen.
step "3 Cache-Waechter im Hintergrund starten"
(
  export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
  export MOSAIC_VAL_POOL='^selfplay_v34-b01-'
  export MOSAIC_FEATURES_FROM_RUST=1
  export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v35_b02.json
  export MOSAIC_DATA_EXCLUDE='selfplay_v29-b11-probe_|selfplay_depth|selfplay_s4states|selfplay_tor2a|selfplay_probe-|selfplay_x35|selfplay_x35e2|^selfplay_v3[123]-b01-|^selfplay_v34-b01-(value-deviate|value-excursion|policy-s100|policy-dice-v2-r1)_'
  export MOSAIC_MASK_DICE_PHASE_VALUE=1
  unset MOSAIC_MOON_TARGET_SOURCE
  exec python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
    --value-target-variant nortv --workers 3 --watch --wartezeit 60 --leerlauf-abbruch 10
) &
WATCH_PID=$!
echo "   Cache-Waechter PID $WATCH_PID ($(date +%H:%M:%S))"

step "4 Erzeugung"
for c in $CLASSES; do
  echo ""
  echo "== Klasse $c   Start $(date +%F' '%H:%M:%S)"
  T0=$(date +%s)
  python -X utf8 -u self_play.py --recipe "$RECIPE" --class "$c"
  RC=$?
  echo "   $c Exit $RC, Ende $(date +%F' '%H:%M:%S), $(( $(date +%s) - T0 )) s Wanduhr, Dateien: $(ls data/ | grep -c "^selfplay_${GEN}-${c}_")"
  if [ $RC -ne 0 ]; then
    echo "   Cache-Waechter PID $WATCH_PID laeuft weiter und endet nach seinem Leerlauf von selbst"
    fail "Klasse $c mit Exit $RC" 12
  fi
done
echo ""
echo "##### ERZEUGUNG v35-b02 FERTIG $(date +%F' '%H:%M:%S)"

# 5 ABNAHMEN nach PREREG_v35_window.md par.8 (Aufrufformen wie par.9/par.10b; nur gedruckt, nicht fatal).
step "5a Tor 0 je Klasse (corpus_sanity_check.py)"
for c in $CLASSES; do
  python -X utf8 -u tools/corpus_sanity_check.py data --pattern "selfplay_${GEN}-${c}_*.pkl" \
    --out "evaluations/artifacts/corpus_sanity_${GEN}-${c}.json"
  echo "   Tor 0 $c Exit $? ($(date +%H:%M:%S))"
done

step "5b Spiegelknopf (tie_mirror_acceptance.py, Fenster 47-53 %)"
python -X utf8 -u tools/probes/tie_mirror_acceptance.py --prefix "$GEN" --classes $CLASSES \
  --out evaluations/artifacts/tie_mirror_acceptance_v35_b02.json
echo "   Spiegelknopf Exit $? ($(date +%H:%M:%S))"

step "5c KL-Abnahme am Ausflug (excursion_kl_acceptance.py)"
# Referenz-Klassen wie par.9 (Schwarm): die beiden value-Klassen; --excursion-class ist seit
# 2026-10-04 im Werkzeug (der Glob war auf value-excursion fest).
python -X utf8 -u tools/probes/excursion_kl_acceptance.py --prefix "$GEN" --model "$GEN_PTH" \
  --classes value-deviate-s400 value-excursion-s400 --excursion-class value-excursion-s400 \
  --out evaluations/artifacts/excursion_kl_acceptance_v35_b02.json
echo "   KL-Abnahme Exit $? ($(date +%H:%M:%S))"

step "5d Vollstaendigkeit je Klasse (Feld completed)"
python -X utf8 - "$GEN" $CLASSES <<'PYEOF'
import glob, os, sys
sys.path.insert(0, os.getcwd())
from corpus_io import load_records
gen, classes = sys.argv[1], sys.argv[2:]
for cls in classes:
    files = sorted(glob.glob(f"data/selfplay_{gen}-{cls}_*.pkl"))
    games, broken, n_rec = set(), set(), 0
    for f in files:
        for r in load_records(f):
            n_rec += 1
            gid = str(r.get("game_id"))
            games.add(gid)
            if r.get("completed", True) is False:
                broken.add(gid)
    main = [g for g in games if not g.endswith("_x1")]
    print(f"   {cls}: {len(files)} Dateien, {len(main)} Hauptpartien ({len(games)} mit Ausfluegen), "
          f"{n_rec} Records, {len(broken)} unvollstaendig (completed False)", flush=True)
PYEOF
echo "   Vollstaendigkeit Exit $? ($(date +%H:%M:%S))"

step "6 Warten auf das Ende des Cache-Waechters (PID $WATCH_PID, Leerlauf 10 x 60 s)"
wait "$WATCH_PID"
echo "   Cache-Waechter Exit $? ($(date +%F' '%H:%M:%S))"

echo ""
echo "########## v35-b02-ERZEUGUNG MIT ABNAHMEN FERTIG $(date +%F' '%H:%M:%S)"
echo "   Von Hand nachzutragen (par.8): Manifest-Diff je Klasse gegen die @100-Vorlage,"
echo "   Watchdog-/Deadline-/Haenger-Zeilen aus der Terminal-Ausgabe, Laufzeiten aus den Manifesten."
