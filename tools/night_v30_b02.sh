#!/usr/bin/env bash
# v30-b02: der ZWEITE Arm der Generation v30 -- Warmstart von v29-b09 auf DEMSELBEN Fenster,
# sonst Rezept-gleich zu v30-b01. Nutzer-Entscheid 2026-09-19: "ja mach mir einen zweiten arm"
# (PREREG_v30_window.md par.8 Punkt 2, STATUS Abschnitt 6 Punkt 3).
#
# WAS DER ARM TRENNT: v30-b01 buendelt Material, Kaltstart, 888 Eingaenge und 414 Aktionen in
# EINEM Arm (par.4). b02 aendert davon GENAU EINEN Faktor -- den Start. Fenster, Monolith, Seed,
# Val-Pool, Rezept und Tor-1-Seeds sind identisch; was zwischen b01 und b02 verschieden misst,
# ist der Kaltstart.
#
# DIESELBEN TOR-1-SEEDS wie b01 (20261300 / 20261301) und derselbe Gegner (Champion v29-b09):
# nur so sind die beiden Arme gegeneinander lesbar, ohne eine dritte Arena zu fahren.
#
# PARALLELITAET: das Training darf neben der laufenden b01-Arena fahren (GPU plus EIN
# CPU-Auftrag, docs/working_rules.md "Auslastung"; ein Training zieht rund EINEN Kern, gemessen
# cpu_s/wanduhr_s 0,92-0,98). Die ARENA von b02 darf das NICHT -- zwei CPU-Messungen
# gegeneinander bleiben verboten. Deshalb wartet Schritt 2 auf eine freie Maschine.
# ACHTUNG: die Trainings-Laufzeit ist damit GEBREMST und im Bericht so zu markieren.
#
# KEINE PIPE, keine eigene Umleitung; als DATEI starten (feedback_chain_waits_on_its_own_wrapper).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

ART=evaluations/artifacts
SEED=20260945                                          # Generationsseed, gleich wie b01
KEY=ec851c536ffd                                       # Fenster-Schluessel des Trainingsanteils (b01-Lauf)
CACHE="data/.cache_${KEY}.h5"
CHAMP=models/alphazero_v29-b09_brierbest.onnx
SPEC=models/frozen_champions/v29-b09/spec.json

export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v29-'
export MOSAIC_FEATURES_FROM_RUST=1
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v30.json
export MOSAIC_DATA_EXCLUDE='selfplay_v29-b11-probe_,selfplay_depth,selfplay_s4states,selfplay_tor2a'
unset MOSAIC_MOON_TARGET_SOURCE

[ -f "$CACHE" ] || { echo "ABBRUCH: Monolith $CACHE fehlt"; exit 1; }
[ -f data/window_v30.txt ] || { echo "ABBRUCH: data/window_v30.txt fehlt"; exit 1; }
[ -f "$CHAMP" ] || { echo "ABBRUCH: $CHAMP fehlt"; exit 1; }
[ -f models/alphazero_v29-b09_brierbest.pth ] || { echo "ABBRUCH: Warmstart-Checkpoint fehlt"; exit 1; }
python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; sys.exit(0 if k==sys.argv[2] else 16)" "$CACHE" "$KEY" \
  || { echo "ABBRUCH: Monolith-Stempel passt nicht zu $KEY"; exit 16; }
echo "== v30-b02, Monolith $CACHE (Stempel geprueft), Champion-Spec $SPEC"

cpu_frei() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { (\$_.CommandLine -match '[s]elf_play\.py|[p]aired_gating\.py|[f]rozen_referee_match\.py|[b]uild_cache|[w]indow_train_split|[o]ffline_diagnosis|[d]ead_unit_probe|[m]aturin' -and \$_.Name -match 'python') -or \$_.Name -match '^(cargo|rustc)' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}

echo ""
echo "== 1) Training v30-b02 -- WARMSTART von v29-b09, sonst b01-Rezept $(date +%F' '%H:%M:%S)"
echo "   (laeuft bewusst neben der b01-Arena: GPU plus EIN CPU-Auftrag; Laufzeit ist GEBREMST)"
python -X utf8 -u train.py --name v30-b02 \
  --load v29-b09_brierbest \
  --file-list data/window_v30.txt --cache-file "$CACHE" \
  --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac 0.05 --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 0.0 \
  --moon-loss-weight 0.0 --opp-points-head \
  --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed $SEED
echo "   Training Exit $? ($(date +%H:%M:%S))"

if [ -f models/alphazero_v30-b02_brierbest.onnx ]; then
  A=models/alphazero_v30-b02_brierbest.onnx
elif [ -f models/alphazero_v30-b02.onnx ]; then
  A=models/alphazero_v30-b02.onnx
else
  echo "ABBRUCH: kein v30-b02-ONNX exportiert"; exit 2
fi

echo ""
echo "########## v30-b02 WARTET auf eine freie Maschine (Arena ist EXKLUSIV) $(date +%F' '%H:%M:%S)"
while :; do
  cpu_frei && { echo "   Maschine frei ($(date +%H:%M:%S))"; break; }
  echo "   belegt ($(date +%H:%M:%S))"; sleep 120
done
sleep 20

echo ""
echo "== 2) Tor 1: v30-b02 gegen den Champion v29-b09, DIESELBEN Seeds wie b01 $(date +%F' '%H:%M:%S)"
echo "   Modell A: $A"
for S in 20261300 20261301; do
  OUT="$ART/gating_v30-b02_vs_v29-b09_s${S}.json"
  echo ""
  echo "===== Seed $S $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$A" --spec-a "$SPEC" --model-b "$CHAMP" --spec-b "$SPEC" \
    --name-a v30-b02 --name-b v29-b09 \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$S" --threads 10 --log-games --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
  echo "-- Tor 2b: Spaltensonde"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  echo "-- Plattenpunkte je Kriterium (Blockgroesse 5)"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_v30-b02_vs_v29-b09_s${S}.json"
done

echo ""
echo "########## v30-b02 FERTIG $(date +%F' '%H:%M:%S)"
