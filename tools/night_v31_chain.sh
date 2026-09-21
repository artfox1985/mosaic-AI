#!/usr/bin/env bash
# v31-Kette: Tor 0 / Tor 2a, Traeger-Manifest, G-2-Auswahl, Fenster, Bloecke, Monolith,
# Training v31-b01 WARM, Tor 1 gegen den Champion v30-b02, Spaltensonde, Plattenpunkte.
# Vorlage: tools/night_v30_chain.sh (in der Historie, Commit 962c079b^). Zuschnitt und
# Lesart: evaluations/PREREG_v31_window.md.
#
# WAS SICH GEGEN v30 AENDERT, und nur das:
#   1. WARMSTART statt Kaltstart: `--load v30-b02_brierbest`. Der Kaltstart ist in v30
#      einfaktoriell widerlegt -- 404:396 kalt gegen 443:297 warm bei gleichem Fenster,
#      Monolith, Seed und Rezept (PREREG_v30_window.md par.9, 9,36 Prozentpunkte).
#   2. Generator `v30-b02`, G-1 `v29-b11`, G-2 `v28-b02`; `v27-b01` ist herausrotiert
#      und geloescht.
#   3. Seed 20260949, Val-Pool `^selfplay_v30-` (Vierer-Schritt, docs/generation_loop.md).
#   4. Tor 2a misst gegen `sp_voll` 0,90087 von `v29-b11` (par.2).
#   5. Tor-1-Seeds 20261400/20261401.
#   6. KEINE Warteschleife auf die Erzeugung: die ist am 2026-09-20 um 11:04 fertig
#      geworden (400/400/401 Dateien). Die Maschinen-Warteschleife bleibt.
#
# DAS RESTLICHE REZEPT IST UNVERAENDERT und stammt nicht aus diesem Skript, sondern aus
#   models/manifest_train_v30-b02_20260919_082507.json (cli_args). Wer es aendert, aendert
#   eine gemessene Groesse -- Regel `feedback_run_manifest_gegen_referenz`.
#
# NICHT STARTEN ohne Anweisung (Regel seit 2026-09-03). Freigabe fuer diesen Lauf:
#   Nutzer 2026-09-20, "starte das training von v31 und das arena spiel gegen den champ".
#
# KEINE PIPE hinter langen Laeufen, keine eigene Umleitung (CLAUDE.md "Lange Laeufe NIE in
#   eine Pipe"): mit run_in_background OHNE Pipe starten, als DATEI, nie per Heredoc
#   schreiben-und-starten (feedback_chain_waits_on_its_own_wrapper).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

ART=evaluations/artifacts
SEED=20260949
GEN=v30-b02                                                  # Generator, Namensstamm der neuen Klassen
G1=v29-b11                                                   # G-1 (die v30-Erzeugung)
G2=v28-b02                                                   # G-2 (die v29-Erzeugung)
G2_SWARM_PATTERN="selfplay_${G2}-value-excursion_*.pkl"      # par.1, Ausflug-Haelfte
CHAMP=models/alphazero_v30-b02_brierbest.onnx                # Tor-1-Gegner = amtierender Champion
REF_MANIFEST=data/manifest_v29-b11-policy_20260918_145006.json   # Manifest-Diff-Referenz
ARM=v31-b01
LOAD=v30-b02_brierbest
TOR2A_REF=0.90087                                            # sp_voll von v29-b11 (par.2)

# --- Umgebung der ganzen Kette (par.3) -----------------------------------------------------
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v30-'
export MOSAIC_FEATURES_FROM_RUST=1
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v31.json
# Fenster-Pinning (feedback_window_pinning_during_generation): Messdateien duerfen nie still
# mitlaufen. Die Kette arbeitet zusaetzlich durchgaengig mit expliziten Dateilisten.
export MOSAIC_DATA_EXCLUDE='selfplay_v29-b11-probe_,selfplay_depth,selfplay_s4states,selfplay_tor2a'
unset MOSAIC_MOON_TARGET_SOURCE

[ -f "$CHAMP" ] || { echo "ABBRUCH: Champion-Modell $CHAMP fehlt"; exit 1; }
[ -f "models/alphazero_${LOAD}.pth" ] || { echo "ABBRUCH: Startgewicht models/alphazero_${LOAD}.pth fehlt"; exit 1; }
[ -f "$REF_MANIFEST" ] || echo "WARNUNG: Referenz-Manifest $REF_MANIFEST fehlt -- Manifest-Diff von Hand"
grep -q "FEATURE_FORMULA_VERSION" config.py || { echo "ABBRUCH: FEATURE_FORMULA_VERSION fehlt in config.py"; exit 2; }
python -X utf8 -c "import config,sys; sys.exit(0 if (config.INPUT_SIZE,config.NUM_ACTIONS)==(888,414) else 3)" \
  || { echo "ABBRUCH: config.py traegt nicht INPUT_SIZE 888 / NUM_ACTIONS 414"; exit 3; }

SPEC=models/frozen_champions/v30-b02/spec.json
[ -f "$SPEC" ] || { echo "ABBRUCH: Champion-Spec $SPEC fehlt"; exit 4; }
echo "== v31-KETTE, Champion-Spec: $SPEC"

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
warte_frei() { wait_for_free_cpu "$1"; }

echo ""
echo "== 0) Cache-Waechter beenden, falls einer laeuft $(date +%H:%M:%S)"
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '[b]uild_cache_incremental' -and \$_.Name -match 'python' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }" 2>/dev/null || true
sleep 10

echo ""
echo "== 0b) Manifest-Diff gegen die Referenz und Stack-Draw-Kontrolle $(date +%H:%M:%S)"
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
      f"contract_hash={cfg.get('contract_hash')} stack_draw_research={cfg.get('stack_draw_research')}")
if str(cfg.get("stack_draw_research")) not in ("1", "True", "true"):
    print("   ACHTUNG: stack_draw_research NICHT gesetzt -- der Korpus traegt keine Slot-Datensaetze. NUTZER-VORLAGE.")
# Die Rueckgabe-Streuung steht NUR in cli_args: engine_config meldet hier den Env-Default
# (bekannter Manifest-Defekt, STATUS Abschnitt 6). Der wirksame Wert ist das CLI-Flag.
print(f"   cli_args.return_order_random_p = {(neu.get('cli_args') or {}).get('return_order_random_p')!r} (Soll 0.81)")
try:
    ref = json.load(io.open(ref_path, encoding="utf-8"))
except Exception as e:
    print(f"   Referenz nicht lesbar ({e}) -- Diff von Hand"); sys.exit(0)
erwartet = {"model", "version", "spec", "seed", "name", "run_timestamp", "input_size",
            "num_actions", "contract_hash", "engine_version", "git_commit", "git_dirty",
            "return_order_random_p"}
a, b = ref.get("cli_args", {}) or {}, neu.get("cli_args", {}) or {}
diff = sorted(set(a) | set(b))
unerwartet = [k for k in diff if a.get(k) != b.get(k) and k not in erwartet]
for k in diff:
    if a.get(k) != b.get(k):
        mark = "  <== PRUEFEN" if k in unerwartet else ""
        print(f"   cli_args.{k}: Referenz={a.get(k)!r} -> neu={b.get(k)!r}{mark}")
print(f"   Unerwartete Abweichungen: {len(unerwartet)} -- jede davon ist ein STOPP")
PYEOF

echo ""
echo "== 0c) Wiedervorlage: traegt der Korpus die Rueckgabe-Streuung? $(date +%H:%M:%S)"
python -X utf8 - <<'PYEOF'
import glob, sys
sys.path.insert(0, ".")
from corpus_io import load_records
fs = sorted(glob.glob("data/selfplay_v30-b02-policy_*.pkl"))[:20]
partien, gestreut = set(), set()
for f in fs:
    for r in load_records(f):
        g = r.get("game_id")
        partien.add(g)
        for s in (r.get("steps") or [r]):
            if s.get("return_order_randomized") is True:
                gestreut.add(g)
n = len(partien)
print(f"   {len(fs)} Dateien, {n} Partien, davon mit gestreuter Rueckgabe: {len(gestreut)} "
      f"= {100.0*len(gestreut)/max(n,1):.1f} %   (Ziel 15 %, Obergrenze 17,75 %)")
PYEOF

echo ""
echo "== 1) Tor 0 je Klasse, Tor 2a gegen $G1 $(date +%H:%M:%S)"
for k in ${G1}-policy ${GEN}-policy ${GEN}-value-tempc ${GEN}-value-excursion; do
  python -X utf8 -u tools/corpus_sanity_check.py data --pattern "selfplay_${k}_*.pkl" \
    --out "$ART/corpus_sanity_${k}.json"
done
python -X utf8 - "$G1" "$GEN" "$TOR2A_REF" <<'PYEOF'
import io, json, sys
g1, gen, ref = sys.argv[1], sys.argv[2], float(sys.argv[3])
v = {}
for k in (f"{g1}-policy", f"{gen}-policy"):
    d = json.load(io.open(f"evaluations/artifacts/corpus_sanity_{k}.json", encoding="utf-8"))["arme"][0]
    v[k] = (d["sp_voll"], d["sp_voll_ci"], d["seiten"])
a, b = v[f"{g1}-policy"], v[f"{gen}-policy"]
print(f"TOR 2a: {gen} als Generator {b[0]:.5f} (+-{b[1]:.5f}, {b[2]} Seiten) "
      f"gegen {g1} {a[0]:.5f} (+-{a[1]:.5f}) -> {'HAELT' if b[0] >= a[0] else 'GERISSEN (Nutzer-Vorlage)'}")
print(f"   Gegenprobe zur registrierten Zahl aus par.2: {ref:.5f} gegen gemessene {a[0]:.5f} "
      f"{'(gleich)' if abs(ref-a[0]) < 5e-5 else '(ABWEICHUNG -- pruefen)'}")
PYEOF

echo ""
echo "== 2) Traeger-Manifest v31 (580 = 400 neu + 135 G-1 + 45 G-2) $(date +%H:%M:%S)"
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
echo "== 3) Schwarm G-2: 145 aus $G2_SWARM_PATTERN $(date +%H:%M:%S)"
python -X utf8 tools/generate_carrier_manifest.py \
  --pattern "$G2_SWARM_PATTERN" --n-files 145 --seed $SEED \
  --list-out data/v28_swarm_pick_v31.txt --out v28_swarm_pick_v31_manifest.json
echo "   gewaehlt: $(grep -vc '^#' data/v28_swarm_pick_v31.txt) (Soll 145)"

echo ""
echo "== 4) Fensterliste data/window_v31.txt $(date +%H:%M:%S)"
python -X utf8 - "$GEN" "$G1" "$G2" <<'PYEOF'
import glob, os, sys
gen, g1, g2 = sys.argv[1:4]
def klasse(stamm):
    return sorted(os.path.basename(p) for p in glob.glob(f"data/selfplay_{stamm}_*.pkl"))
neu_pol, neu_tmp, neu_exc = klasse(f"{gen}-policy"), klasse(f"{gen}-value-tempc"), klasse(f"{gen}-value-excursion")
g1_pol, g1_tmp, g1_exc = klasse(f"{g1}-policy"), klasse(f"{g1}-value-tempc"), klasse(f"{g1}-value-excursion")
g2_pol = klasse(f"{g2}-policy")
g2_val = [l.strip() for l in open("data/v28_swarm_pick_v31.txt", encoding="utf-8")
          if l.strip() and not l.startswith("#")]
zahlen = (len(neu_pol), len(neu_tmp), len(neu_exc), len(g1_pol), len(g1_tmp),
          len(g1_exc), len(g2_pol), len(g2_val))
print("Klassen:", zahlen)
assert (len(neu_pol), len(neu_tmp)) == (400, 400), zahlen
assert 395 <= len(neu_exc) <= 410, zahlen
assert (len(g1_pol), len(g1_tmp)) == (400, 400), zahlen
assert 395 <= len(g1_exc) <= 410, zahlen
assert (len(g2_pol), len(g2_val)) == (400, 145), zahlen
allf = neu_pol + neu_tmp + neu_exc + g1_pol + g1_tmp + g1_exc + g2_pol + g2_val
fehlt = [b for b in allf if not os.path.exists(os.path.join("data", b))]
assert not fehlt, fehlt[:5]
assert len(allf) == len(set(allf)), "Doppelte im Fenster"
with open("data/window_v31.txt", "w", encoding="utf-8", newline="\n") as fh:
    fh.write(f"# v31-Fenster (PREREG_v31_window.md par.1): 400 Sockel + 400 temperiert + "
             f"{len(neu_exc)} Ausflug (neu, Generator {gen}) + 400 G-1-policy + "
             f"{len(g1_tmp)+len(g1_exc)} G-1-value + 400 G-2-policy + 145 G-2-value (Ausflug)\n")
    fh.write("\n".join(allf) + "\n")
print(f"window_v31.txt: {len(allf)} Dateien (Soll 2.947)")
PYEOF

warte_frei "Bloecke, Split, Monolith"
echo ""
echo "== 5) Bloecke fuers Fenster UNTER der Trainings-Umgebung (888, Formel-Version) $(date +%F' '%H:%M:%S)"
T0=$(date +%s)
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v31.txt
echo "   Exit $? ($(date +%H:%M:%S)); Bloecke: $(( $(date +%s) - T0 )) s Wanduhr"

echo ""
echo "== 6) Trainingsanteil, Fenster-Schluessel, Monolith $(date +%H:%M:%S)"
python -X utf8 tools/window_train_split.py --file-list data/window_v31.txt --val-frac 0.05 \
  --val-pool "$MOSAIC_VAL_POOL" --encoder 2d --value-target-variant nortv \
  --train-list-out data/window_v31_train.txt --val-list-out data/window_v31_val.txt \
  > "$ART/v31_split.txt"
cat "$ART/v31_split.txt"
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v31_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
echo "KEY=$KEY"
CACHE="data/.cache_${KEY}.h5"
T0=$(date +%s)
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v31_train.txt \
  --merge-out "$CACHE"
echo "   Exit $? ($(date +%H:%M:%S)); Merge: $(( $(date +%s) - T0 )) s Wanduhr"
[ -f "$CACHE" ] || { echo "STOPP: Monolith fehlt"; exit 14; }
ls -la "$CACHE"
python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; print('   Stempel:',k); sys.exit(0 if k==sys.argv[2] else 16)" "$CACHE" "$KEY" \
  || { echo "STOPP: Stempel passt nicht zum Schluessel"; exit 16; }

# Die Flags --val-pool, --ignore-policy-target-valid, --head-warmstart und --bootstrap-coherence
# GIBT ES IN train.py NICHT; sie kommen aus der Umgebung. Early-Stop, Epoch-Checkpoint und
# Snapshot sind per Default an.
# ABBRUCH? Fortsetzen mit demselben Aufruf plus --resume (Fingerabdruck-Waechter).
echo ""
echo "== 7) Training $ARM -- WARMSTART von $LOAD $(date +%F' '%H:%M:%S)"
echo "   Umgebung: CARRIER_MANIFEST=$MOSAIC_CARRIER_MANIFEST VAL_POOL=$MOSAIC_VAL_POOL FROM_RUST=$MOSAIC_FEATURES_FROM_RUST"
python -X utf8 -u train.py --name "$ARM" --load "$LOAD" \
  --file-list data/window_v31.txt --cache-file "$CACHE" \
  --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac 0.05 --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 0.0 \
  --moon-loss-weight 0.0 --opp-points-head \
  --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed $SEED
echo "   Training Exit $? ($(date +%H:%M:%S))"

echo ""
echo "== 7b) Manifest-Diff des TRAININGS gegen das v30-b02-Rezept $(date +%H:%M:%S)"
python -X utf8 - "$ARM" <<'PYEOF'
import glob, io, json, sys
arm = sys.argv[1]
ps = sorted(glob.glob(f"models/manifest_train_{arm}_*.json"))
if not ps:
    print("   kein Trainings-Manifest gefunden -- Diff von Hand"); sys.exit(0)
neu = json.load(io.open(ps[-1], encoding="utf-8")).get("cli_args", {}) or {}
ref = json.load(io.open("models/manifest_train_v30-b02_20260919_082507.json",
                        encoding="utf-8")).get("cli_args", {}) or {}
erwartet = {"load", "name", "file_list", "cache_file", "seed", "val_pool"}
unerwartet = []
for k in sorted(set(ref) | set(neu)):
    if ref.get(k) != neu.get(k):
        mark = "" if k in erwartet else "  <== STOPP"
        if k not in erwartet:
            unerwartet.append(k)
        print(f"   cli_args.{k}: v30-b02={ref.get(k)!r} -> {arm}={neu.get(k)!r}{mark}")
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

warte_frei "Tor 1"
echo ""
echo "== 8) Tor 1: $ARM gegen den Champion $GEN, zwei Seeds a 200 Paaren $(date +%F' '%H:%M:%S)"
echo "   Modell A: $A"; ls -l "$A"
echo "   Modell B: $CHAMP   Spec beidseits: $SPEC"
for S in 20261400 20261401; do
  OUT="$ART/gating_${ARM}_vs_${GEN}_s${S}.json"
  echo ""
  echo "===== Seed $S $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$A" --spec-a "$SPEC" --model-b "$CHAMP" --spec-b "$SPEC" \
    --name-a "$ARM" --name-b "$GEN" \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$S" --threads 10 --log-games --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
  echo "-- Tor 2b: Spaltensonde (seit 2026-09-19 OHNE Replay, Endzustand im Artefakt)"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  echo "-- Plattenpunkte je Kriterium (Blockgroesse 5)"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_${ARM}_vs_${GEN}_s${S}.json"
done

echo ""
echo "########## v31-KETTE FERTIG $(date +%F' '%H:%M:%S)"
echo "   Faellig danach (PREREG_v31_window.md par.2):"
echo "   - Verdikt auf BLOCK-Ebene (z-Wert auf DIFFERENZIERTEN Blockwerten -- die Felder in"
echo "     blocks[] sind KUMULATIV, docs/pitfalls.md), nicht nur gepoolt"
echo "   - sechs Standard-Kennzahlen je Seite und als Differenz (CLAUDE.md)"
echo "   - Tor 2b ist erstmals wieder verwendbar: die Arena schreibt den Endstand mit"
echo "   - Netz-Gesundheit: Spaltennormen je Block, dead_unit_probe --reference $GEN,"
echo "     offline_diagnosis, oracle_metrics, platt_fit"
echo "   - Laufzeiten nach docs/measured_runtimes.md, laufzeit-Block in jedes Artefakt"
echo "   - Champion-Wechsel NUR nach /mosaic-champion-promotion, nicht nebenher"
