#!/usr/bin/env bash
# v30-Kette: Tor 0 / Tor 2a, Traeger-Manifest, G-2-Auswahl, Fenster, Bloecke, Monolith,
# Training v30-b01 KALT, Tor 1 gegen den Champion v29-b09, Spaltensonde, Plattenpunkte.
# Muster: tools/night_v29_chain.sh (Ablauf) und tools/night_v29_b08_head_pair.sh (Schluessel,
# Stempel-Pruefung, Tor-1-Block). Zuschnitt und Lesart: evaluations/PREREG_v30_window.md.
#
# NICHT STARTEN ohne Anweisung (Regel seit 2026-09-03). Voraussetzungen, alle VOR dem Start:
#   - Erzeugung durch tools/night_v30_generate.sh gelaufen (Generator v29-b11, STATUS Punkt 23)
#   - Wheel mit input_size 888 / num_actions 414 / Vertragshash 6ef829e564c58bd5 installiert
#   - /mosaic-generation-turnover gelaufen (Einfrieren v29-b09, restic-Beleg, STATUS-Neufassung)
#
# SEED der Auswahlen UND des Trainings: 20260945 (par.1; v29 nahm 20260941, Vierer-Schritt aus
#   docs/generation_loop.md).
# VAL-POOL: '^selfplay_v29-' (die neue Generation stellt den Validierungsanteil; die Dateien
#   heissen nach dem GENERATOR v29-b11).
# G-2-POSTEN: die AUSFLUG-Haelfte von v27-b01 (par.1a -- dieselbe Regel wie v28 und v29).
# ROTATION: v26-b01 faellt mit v30 aus dem Fenster (Loeschung nur mit Freigabe, par.8 Punkt 3).
#
# KALTSTART: kein --load. Das ist der Nutzer-Entscheid vom 2026-09-17 (STATUS Abschnitt 4,
#   PREREG_round_transition_search_sampling.md 18.11). Wer ihn versehentlich setzt, misst eine
#   andere Wette. Rueckfall 1 (Afterburner) und Rueckfall 2 (Warmstart von v29-b09) stehen in
#   PREREG_v30_window.md par.3 Punkt 5 und laufen NICHT automatisch.
#
# WARTEBEDINGUNG, gehaertet (drei Vorfaelle: 2026-09-09, 2026-09-13, und die Ketten-Wrapper-Falle
#   aus feedback_chain_waits_on_its_own_wrapper): der laufzeit-Block im Manifest der Ausflug-Klasse
#   (den schreibt self_play.py erst am Ende) UND eine KLARE 0 aus der Prozessabfrage. Eine leere
#   oder unklare Antwort gilt als BELEGT. Der escapte Punkt im Muster und `$_.Name -match 'python'`
#   verhindern den Selbsttreffer ueber die eigene Kommandozeile.
#
# KEINE PIPE hinter langen Laeufen, keine eigene Umleitung (CLAUDE.md "Lange Laeufe NIE in eine
#   Pipe"): mit run_in_background OHNE Pipe starten, dann sieht der Nutzer den Fortschritt.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

ART=evaluations/artifacts
SEED=20260945
GEN=v29-b11                                                  # Generator, Namensstamm der Klassen
G2_SWARM_PATTERN="selfplay_v27-b01-value-excursion_*.pkl"    # par.1a
G1=v28-b02                                                   # G-1
G2=v27-b01                                                   # G-2
CHAMP=models/alphazero_v29-b09_brierbest.onnx                # Tor-1-Gegner (Champion, STATUS Punkt 18)
REF_MANIFEST=data/manifest_v28-b02-policy_20260913_120816.json   # Manifest-Diff-Referenz (par.3 Punkt 3)

# --- Umgebung der ganzen Kette (par.6) -----------------------------------------------------
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v29-'
export MOSAIC_FEATURES_FROM_RUST=1
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v30.json
# Fenster-Pinning (feedback_window_pinning_during_generation): Messdateien duerfen nie still
# mitlaufen. Die Kette arbeitet zusaetzlich durchgaengig mit expliziten Dateilisten.
export MOSAIC_DATA_EXCLUDE='selfplay_v29-b11-probe_,selfplay_depth,selfplay_s4states,selfplay_tor2a'
unset MOSAIC_MOON_TARGET_SOURCE

[ -f "$CHAMP" ] || { echo "ABBRUCH: Champion-Modell $CHAMP fehlt"; exit 1; }
[ -f "$REF_MANIFEST" ] || echo "WARNUNG: Referenz-Manifest $REF_MANIFEST fehlt -- Manifest-Diff von Hand"
grep -q "FEATURE_FORMULA_VERSION" config.py || { echo "ABBRUCH: FEATURE_FORMULA_VERSION fehlt in config.py"; exit 2; }
python -X utf8 -c "import config,sys; sys.exit(0 if (config.INPUT_SIZE,config.NUM_ACTIONS)==(888,414) else 3)" \
  || { echo "ABBRUCH: config.py traegt nicht INPUT_SIZE 888 / NUM_ACTIONS 414"; exit 3; }

# Champion-Spec: die eingefrorene b09-Spec, sobald der Generationswechsel sie angelegt hat;
# bis dahin die v28-b02-Spec (inhaltlich seit v25 die v24-b07-Spec, PREREG_v28_window.md par.3).
if [ -f models/frozen_champions/v29-b09/spec.json ]; then
  SPEC=models/frozen_champions/v29-b09/spec.json
else
  SPEC=models/frozen_champions/v28-b02/spec.json
  echo "HINWEIS: models/frozen_champions/v29-b09/spec.json liegt noch nicht -- Tor 1 faehrt $SPEC"
fi
echo "== v30-KETTE, Champion-Spec: $SPEC"

erzeugung_fertig() {
  python -X utf8 - "$GEN" <<'PYEOF'
import glob, io, json, sys
try:
    ps = sorted(glob.glob(f"data/manifest_{sys.argv[1]}-value-excursion_*.json"))
    d = json.load(io.open(ps[-1], encoding="utf-8")) if ps else {}
    print("JA" if "laufzeit" in d else "NEIN")
except Exception:
    print("UNKLAR")
PYEOF
}

keine_erzeugung_laeuft() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '[s]elf_play\.py' -and \$_.Name -match 'python' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  # Leere oder unklare Antwort gilt als BELEGT (gehaertet, drei Vorfaelle).
  [ "$n" = "0" ]
}

cpu_frei() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { (\$_.CommandLine -match '[s]elf_play\.py|[t]rain\.py|[p]aired_gating\.py|[f]rozen_referee_match\.py|[b]uild_cache|[w]indow_train_split|[o]ffline_diagnosis|[d]ead_unit_probe|[m]aturin' -and \$_.Name -match 'python') -or \$_.Name -match '^(cargo|rustc)' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}
warte_frei() {
  echo "########## v30-KETTE WARTET ($1) $(date +%F' '%H:%M:%S)"
  while :; do
    cpu_frei && { echo "   Maschine frei ($(date +%H:%M:%S))"; break; }
    echo "   belegt ($(date +%H:%M:%S))"; sleep 120
  done
  sleep 20
}

echo "== WARTEN auf die Ausflug-Klasse von $GEN $(date +%F' '%H:%M:%S)"
while :; do
  status=$(erzeugung_fertig)
  if [ "$status" = "JA" ] && keine_erzeugung_laeuft; then
    echo "   Erzeugung durch ($(date +%H:%M:%S))"
    break
  fi
  echo "   noch nicht ($(date +%H:%M:%S)): laufzeit=$status"
  sleep 300
done

echo ""
echo "== 0) Cache-Waechter beenden $(date +%H:%M:%S)"
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '[b]uild_cache_incremental' -and \$_.Name -match 'python' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }" 2>/dev/null || true
sleep 10

echo ""
echo "== 0b) Manifest-Diff gegen die Referenz (par.3 Punkt 3) und Stack-Draw-Kontrolle (Punkt 4) $(date +%H:%M:%S)"
python -X utf8 - "$GEN" "$REF_MANIFEST" <<'PYEOF'
import glob, io, json, sys
gen, ref_path = sys.argv[1], sys.argv[2]
ps = sorted(glob.glob(f"data/manifest_{gen}-policy_*.json"))
if not ps:
    print("   STOPP-KANDIDAT: kein Manifest der Policy-Klasse gefunden"); sys.exit(0)
neu = json.load(io.open(ps[-1], encoding="utf-8"))
print(f"   Manifest: {ps[-1]}")
cfg = neu.get("engine_config", {}) or {}
print(f"   engine_config: input_size={cfg.get('input_size')} num_actions={cfg.get('num_actions')} "
      f"contract_hash={cfg.get('contract_hash')} stack_draw_research={cfg.get('stack_draw_research')} "
      f"return_order_mode={cfg.get('return_order_mode')}")
if str(cfg.get("stack_draw_research")) not in ("1", "True", "true"):
    print("   ACHTUNG: stack_draw_research NICHT gesetzt -- der Korpus traegt keine Slot-Datensaetze "
          "(PREREG_v30_window.md par.3 Punkt 4). NUTZER-VORLAGE.")
try:
    ref = json.load(io.open(ref_path, encoding="utf-8"))
except Exception as e:
    print(f"   Referenz nicht lesbar ({e}) -- Diff von Hand"); sys.exit(0)
erwartet = {"model", "version", "spec", "seed", "name", "run_timestamp", "input_size",
            "num_actions", "contract_hash", "engine_version", "git_commit", "git_dirty"}
a, b = ref.get("cli_args", {}) or {}, neu.get("cli_args", {}) or {}
diff = sorted(set(a) | set(b))
unerwartet = [k for k in diff if a.get(k) != b.get(k) and k not in erwartet]
for k in diff:
    if a.get(k) != b.get(k):
        mark = "  <== PRUEFEN" if k in unerwartet else ""
        print(f"   cli_args.{k}: Referenz={a.get(k)!r} -> neu={b.get(k)!r}{mark}")
print(f"   Unerwartete Abweichungen: {len(unerwartet)} -- jede davon ist ein STOPP (par.3 Punkt 3)")
PYEOF

echo ""
echo "== 1) Tor 0 je Klasse, Tor 2a ex post gegen v28-b02 $(date +%H:%M:%S)"
for k in ${G1}-policy ${GEN}-policy ${GEN}-value-tempc ${GEN}-value-excursion; do
  python -X utf8 -u tools/corpus_sanity_check.py data --pattern "selfplay_${k}_*.pkl" \
    --out "$ART/corpus_sanity_${k}.json"
done
# Tor 2a (docs/generation_loop.md): der Generator darf als Punktschaetzer nicht unter den
# Vorgaenger fallen. Beide Seiten sind bei 100 Sims erzeugt, also dieselbe Betriebsart
# (PREREG_search_depth_column_optimum.md par.8e). Vorlage, kein Abbruch.
python -X utf8 - "$G1" "$GEN" <<'PYEOF'
import io, json, sys
g1, gen = sys.argv[1], sys.argv[2]
v = {}
for k in (f"{g1}-policy", f"{gen}-policy"):
    d = json.load(io.open(f"evaluations/artifacts/corpus_sanity_{k}.json", encoding="utf-8"))["arme"][0]
    v[k] = (d["sp_voll"], d["sp_voll_ci"], d["seiten"])
a, b = v[f"{g1}-policy"], v[f"{gen}-policy"]
print(f"TOR 2a ex post: {gen} als Generator {b[0]:.3f} (+-{b[1]:.3f}, {b[2]} Seiten) "
      f"gegen {g1} {a[0]:.3f} (+-{a[1]:.3f}) -> {'HAELT' if b[0] >= a[0] else 'GERISSEN (Nutzer-Vorlage)'}")
PYEOF

echo ""
echo "== 2) Traeger-Manifest v30 (580 = 400 neu + 135 G-1 + 45 G-2) $(date +%H:%M:%S)"
python -X utf8 tools/generate_carrier_manifest.py \
  --pattern "selfplay_${G2}-policy_*.pkl" --n-files 45 --seed $SEED \
  --include-glob "selfplay_${GEN}-policy_*.pkl" \
  --pick "selfplay_${G1}-policy_*.pkl:135" \
  --out "$MOSAIC_CARRIER_MANIFEST"
python -X utf8 - "$MOSAIC_CARRIER_MANIFEST" "$GEN" "$G1" "$G2" <<'PYEOF'
import json, sys
name, gen, g1, g2 = sys.argv[1:5]
d = json.load(open(f"data/{name}", encoding="utf-8"))
f = d["policy_carrier_files"]
neu = [x for x in f if x.startswith(f"selfplay_{gen}-policy_")]
a = [x for x in f if x.startswith(f"selfplay_{g1}-policy_")]
b = [x for x in f if x.startswith(f"selfplay_{g2}-policy_")]
print(f"Manifest: {len(f)} Traeger = {len(neu)} neu + {len(a)} G-1 + {len(b)} G-2")
assert (len(f), len(neu), len(a), len(b)) == (580, 400, 135, 45), (len(f), len(neu), len(a), len(b))
PYEOF

echo ""
echo "== 3) Schwarm G-2: 145 aus $G2_SWARM_PATTERN (par.1a) $(date +%H:%M:%S)"
python -X utf8 tools/generate_carrier_manifest.py \
  --pattern "$G2_SWARM_PATTERN" --n-files 145 --seed $SEED \
  --list-out data/v27_swarm_pick_v30.txt --out v27_swarm_pick_v30_manifest.json
echo "   gewaehlt: $(grep -vc '^#' data/v27_swarm_pick_v30.txt) (Soll 145)"

echo ""
echo "== 4) Fensterliste data/window_v30.txt $(date +%H:%M:%S)"
python -X utf8 - "$GEN" "$G1" "$G2" <<'PYEOF'
import glob, os, sys
gen, g1, g2 = sys.argv[1:4]
def klasse(stamm):
    return sorted(os.path.basename(p) for p in glob.glob(f"data/selfplay_{stamm}_*.pkl"))
neu_pol, neu_tmp, neu_exc = klasse(f"{gen}-policy"), klasse(f"{gen}-value-tempc"), klasse(f"{gen}-value-excursion")
g1_pol, g1_tmp, g1_exc = klasse(f"{g1}-policy"), klasse(f"{g1}-value-tempc"), klasse(f"{g1}-value-excursion")
g2_pol = klasse(f"{g2}-policy")
g2_val = [l.strip() for l in open("data/v27_swarm_pick_v30.txt", encoding="utf-8")
          if l.strip() and not l.startswith("#")]
zahlen = (len(neu_pol), len(neu_tmp), len(neu_exc), len(g1_pol), len(g1_tmp),
          len(g1_exc), len(g2_pol), len(g2_val))
print("Klassen:", zahlen)
assert (len(neu_pol), len(neu_tmp)) == (400, 400), zahlen
assert 395 <= len(neu_exc) <= 410, zahlen
assert (len(g1_pol), len(g1_tmp)) == (400, 400), zahlen
assert 395 <= len(g1_exc) <= 410, zahlen
assert (len(g2_pol), len(g2_val)) == (400, 145), zahlen  # G-2-Schwarm: Ausflug-Haelfte (par.1a)
allf = neu_pol + neu_tmp + neu_exc + g1_pol + g1_tmp + g1_exc + g2_pol + g2_val
fehlt = [b for b in allf if not os.path.exists(os.path.join("data", b))]
assert not fehlt, fehlt[:5]
assert len(allf) == len(set(allf)), "Doppelte im Fenster"
with open("data/window_v30.txt", "w", encoding="utf-8", newline="\n") as fh:
    fh.write(f"# v30-Fenster (PREREG_v30_window.md par.1): 400 Sockel + 400 temperiert + "
             f"{len(neu_exc)} Ausflug (neu, Generator {gen}) + 400 G-1-policy + "
             f"{len(g1_tmp)+len(g1_exc)} G-1-value + 400 G-2-policy + 145 G-2-value (Ausflug)\n")
    fh.write("\n".join(allf) + "\n")
print(f"window_v30.txt: {len(allf)} Dateien (Soll rund 2.947)")
PYEOF

warte_frei "Bloecke, Split, Monolith"
echo ""
echo "== 5) Bloecke fuers Fenster UNTER der Trainings-Umgebung (888, Formel-Version) $(date +%F' '%H:%M:%S)"
T0=$(date +%s)
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v30.txt
echo "   Exit $? ($(date +%H:%M:%S)); Bloecke: $(( $(date +%s) - T0 )) s Wanduhr"

echo ""
echo "== 6) Trainingsanteil, Fenster-Schluessel, Monolith $(date +%H:%M:%S)"
python -X utf8 tools/window_train_split.py --file-list data/window_v30.txt --val-frac 0.05 \
  --val-pool "$MOSAIC_VAL_POOL" --encoder 2d --value-target-variant nortv \
  --train-list-out data/window_v30_train.txt --val-list-out data/window_v30_val.txt \
  > "$ART/v30_split.txt"
cat "$ART/v30_split.txt"
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v30_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
echo "KEY=$KEY"
CACHE="data/.cache_${KEY}.h5"
T0=$(date +%s)
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v30_train.txt \
  --merge-out "$CACHE"
echo "   Exit $? ($(date +%H:%M:%S)); Merge: $(( $(date +%s) - T0 )) s Wanduhr"
[ -f "$CACHE" ] || { echo "STOPP: Monolith fehlt"; exit 14; }
ls -la "$CACHE"
# Stempel-Pruefung wie tools/night_v29_b08_head_pair.sh Schritt 2: der Monolith muss den
# Fenster-Schluessel des VERBRAUCHERS tragen, sonst trainiert die Kette auf fremdem Material.
python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; print('   Stempel:',k); sys.exit(0 if k==sys.argv[2] else 16)" "$CACHE" "$KEY" \
  || { echo "STOPP: Stempel passt nicht zum Schluessel"; exit 16; }

# Die Flags --val-pool, --ignore-policy-target-valid, --head-warmstart und --bootstrap-coherence
# GIBT ES IN train.py NICHT; sie kommen aus der Umgebung. Early-Stop, Epoch-Checkpoint und
# Snapshot sind per Default an.
# ABBRUCH? Fortsetzen mit demselben Aufruf plus --resume (Fingerabdruck-Waechter).
echo ""
echo "== 7) Training v30-b01 -- KALTSTART, kein --load (STATUS Abschnitt 4, par.6) $(date +%F' '%H:%M:%S)"
echo "   Umgebung: CARRIER_MANIFEST=$MOSAIC_CARRIER_MANIFEST VAL_POOL=$MOSAIC_VAL_POOL FROM_RUST=$MOSAIC_FEATURES_FROM_RUST"
python -X utf8 -u train.py --name v30-b01 \
  --file-list data/window_v30.txt --cache-file "$CACHE" \
  --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac 0.05 --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 0.0 \
  --moon-loss-weight 0.0 --opp-points-head \
  --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed $SEED
echo "   Training Exit $? ($(date +%H:%M:%S))"

echo ""
echo "== 7b) Manifest-Diff des TRAININGS gegen das v30-Rezept (par.6) $(date +%H:%M:%S)"
echo "   Faellig von Hand: models/manifest_train_v30-b01_*.json cli_args gegen"
echo "   models/manifest_train_v29-b09_20260917_200920.json diffen. Erwartet sind GENAU:"
echo "   load (b09: v28-b02_brierbest -> v30-b01: null), name, file_list, cache_file, seed,"
echo "   val_pool. Jede weitere Abweichung ist ein STOPP (feedback_run_manifest_gegen_referenz)."

if [ -f models/alphazero_v30-b01_brierbest.onnx ]; then
  A=models/alphazero_v30-b01_brierbest.onnx
elif [ -f models/alphazero_v30-b01.onnx ]; then
  A=models/alphazero_v30-b01.onnx
  echo "HINWEIS: kein _brierbest -- beste Epoche war die letzte, finales Modell wird genommen"
else
  echo "UEBERSPRUNGEN: kein Modell v30-b01 -- Training gescheitert?"; exit 15
fi

warte_frei "Tor 1"
echo ""
echo "== 8) Tor 1: v30-b01 gegen den Champion v29-b09, zwei Seeds a 200 Paaren $(date +%F' '%H:%M:%S)"
echo "   Modell A: $A"; ls -l "$A"
echo "   Modell B: $CHAMP   Spec beidseits: $SPEC"
for S in 20261300 20261301; do
  OUT="$ART/gating_v30-b01_vs_v29-b09_s${S}.json"
  echo ""
  echo "===== Seed $S $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$A" --spec-a "$SPEC" --model-b "$CHAMP" --spec-b "$SPEC" \
    --name-a v30-b01 --name-b v29-b09 \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$S" --threads 10 --log-games --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
  echo "-- Tor 2b: Spaltensonde"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  echo "-- Plattenpunkte je Kriterium (Blockgroesse 5)"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_v30-b01_vs_v29-b09_s${S}.json"
done

echo ""
echo "########## v30-KETTE FERTIG $(date +%F' '%H:%M:%S)"
echo "   Faellig danach (PREREG_v30_window.md par.3):"
echo "   - Verdikt auf BLOCK-Ebene (80 Bloecke a 10 Partien, z-Wert), nicht nur gepoolt"
echo "   - sechs Standard-Kennzahlen je Seite und als Differenz (CLAUDE.md)"
echo "   - Netz-Gesundheit: Spaltennormen je Block (Abschnitt 16/17/18), dead_unit_probe"
echo "     --reference v29-b09, offline_diagnosis, oracle_metrics, platt_fit"
echo "   - Bauzeiten nach docs/measured_runtimes.md, laufzeit-Block in jedes Artefakt"
echo "   - bei flachem Tor 1: Rueckfall 1 Afterburner, dann Rueckfall 2 Warmstart von v29-b09"
echo "     (par.3 Punkt 5) -- beide NUR auf Nutzer-Entscheid, nicht automatisch"
