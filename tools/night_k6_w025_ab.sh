#!/usr/bin/env bash
# PREREG_special_tile_yield.md par.13.2 Punkt 3, zweite Dosis: K6 mit special_unlock_w 0,25 gegen aus.
# Anlass (13.7): Dosis 0,5 SCHADET auf Block-Ebene (z -2,57; 180:210, SPRT H0), der Vorzeichentest lag mit
# p 0,053 knapp ueber der 0,05-Schwelle, an der die Hauptkette (night_k6_special_unlock.sh Stufe 5) die
# zweite Dosis gestartet haette. Die Prereg verlangt "0,25 nur, wenn 0,5 schadet" -- Block-Ebene ist das
# Entscheidungsmass (par.5 der Rundenuebergangs-Prereg, hier gleich verwendet), also faellig.
#
# NEBENLAST: wartet auf freie CPU (Tor 1 v29-b09 laeuft bis etwa 0:30), dann exklusiv. Kein Wheel-Bau,
# kein Training: das installierte Wheel (19:37, mit K6) bleibt.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
MODELL=models/alphazero_v28-b02_brierbest.onnx
W025=models/k6_w025.spec.json
OFF=models/k6_off.spec.json
SEED_AB=20261211
OUT_AB="$ART/k6_w025_vs_off_s${SEED_AB}.json"

[ -f "$MODELL" ] || { echo "ABBRUCH: $MODELL fehlt"; exit 1; }
[ -f "$W025" ] && [ -f "$OFF" ] || { echo "ABBRUCH: Spec-Dateien fehlen"; exit 1; }
python -X utf8 -c "import mosaic_rust, json, sys; d=json.loads(mosaic_rust.engine_config_json()); sys.exit(0 if 'special_unlock_w' in d else 2)" \
  || { echo "ABBRUCH: installiertes Wheel kennt special_unlock_w nicht"; exit 2; }

cpu_frei() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { (\$_.CommandLine -match '[t]rain\.py|[p]aired_gating\.py|[f]rozen_referee_match\.py|[b]uild_cache|[c]ounterfactual_tiling|[o]ffline_diagnosis|[d]ead_unit_probe|[m]aturin|[w]indow_train_split|[a]rena_column_probe|[p]late_points_from_arena' -and \$_.Name -match 'python') -or \$_.Name -match '^(cargo|rustc)' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}
warte_frei() {
  echo "########## K6-W025 WARTET ($1) $(date +%F' '%H:%M:%S)"
  while :; do
    cpu_frei && { echo "   Maschine frei ($(date +%H:%M:%S))"; break; }
    echo "   belegt ($(date +%H:%M:%S))"; sleep 120
  done
  sleep 20
}

warte_frei "A/B Dosis 0,25"
echo ""
echo "===== A/B K6 Dosis 0,25 gegen aus, 200 Paare, Seed $SEED_AB $(date +%F' '%H:%M:%S)"
echo "   A = special_unlock_w 0,25 ($W025), B = aus ($OFF)"
python -X utf8 -u tools/paired_gating.py \
  --model-a "$MODELL" --spec-a "$W025" \
  --model-b "$MODELL" --spec-b "$OFF" \
  --name-a k6_w025 --name-b k6_off \
  --sims-a 400 --sims-b 400 --c-puct 1.5 \
  --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
  --seed "$SEED_AB" --threads 10 --log-games --no-promote-winner --out "$OUT_AB"
echo "   Exit $? ($(date +%H:%M:%S))"
python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT_AB"
python -X utf8 -u tools/plate_points_from_arena.py "$OUT_AB" --block 5 \
  --out "$ART/plate_points_k6_w025_s${SEED_AB}.json"
echo ""
echo "########## K6-W025 FERTIG $(date +%F' '%H:%M:%S)"
echo "   Faellig danach: Verdikt 13.2 Punkt 5 fuer beide Dosen, sechs Kennzahlen, Laufzeit nach measured_runtimes."
