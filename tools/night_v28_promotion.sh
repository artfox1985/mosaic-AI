#!/usr/bin/env bash
# Promotion v28-b02 (Nutzer-Entscheid 2026-09-11: b02 = bester Stand; Generator v29), die
# MESSENDEN Schritte nach docs/promotion_checklist.md, Segment 2 der Leiter (hv1_anchor_v2).
# Schon gelaufen (tools/night_reanchor.sh): Schritt 3 Anker-Kante (126:24) und Schritt 2 als
# Nachbar-Kante v28-b02 gegen v27-b01 (Seed 20261044, 200 Paare, Logs). Hier:
#   0  Spaltensonde und Wertungsplatten-Punkte auf der Nachbar-Kante (Tor 2b im Segment 2)
#   4  Champion-2-Kante gegen das EINGEFRORENE Artefakt v26-b01 mit dessen Wheel; Cross-Aera
#      (Kontrakt 20b442a8 gegen 39648b95, Handshake ROT erwartet, --force-cross-era)
#   5c sigma/Prior-Balance (Waechter: ueber 3 oeffnet sich die c_visit/c_scale-Familie)
#   5b Anzeige-Kalibrierung, frozen_v3 (Anzeige) und frozen_v1 (Trend)
# Aufruf: bash tools/night_v28_promotion.sh   (Hintergrundaufgabe, keine Pipe, exklusiv)
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
NEU=models/alphazero_v28-b02_brierbest.onnx
SPEC=models/frozen_champions/v27-b01/spec.json
EDGE=$ART/paired_gating_v28-b02_vs_v27-b01_s44_segment2.json
[ -f "$EDGE" ] || { echo "STOPP: Nachbar-Kante $EDGE fehlt"; exit 12; }

echo "== 0a) Spaltensonde auf die Nachbar-Kante $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$EDGE"
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== 0b) Wertungsplatten-Punkte je Kriterium $(date +%H:%M:%S)"
python -X utf8 -u tools/plate_points_from_arena.py "$EDGE"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 4) Champion-2-Kante gegen das ARTEFAKT v26-b01 (Cross-Aera) $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/frozen_referee_match.py \
  --artifact-dir models/frozen_champions/v26-b01 \
  --model-a "$NEU" --spec-a "$SPEC" \
  --sims-a 400 --sims-worker 400 --n-games 150 --seed-base 20261052 --workers 6 \
  --force-cross-era --out "$ART/champion2_v28-b02_vs_v26-b01.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 5c) sigma/Prior-Balance $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/gumbel_scale_calibration.py --model v28-b02_brierbest \
  --sims 400 --n-states 300 --out "$ART/gumbel_scale_calibration_v28-b02.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 5b) Anzeige-Kalibrierung, Fit auf frozen_v3 $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/platt_fit.py --models models/alphazero_v28-b02_brierbest.pth \
  --eval-set evaluations/frozen_eval_set_v3.pkl --out "$ART/platt_fit_v28-b02_v3.json"
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== 5b) Trendmetrik, Fit auf frozen_v1 $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/platt_fit.py --models models/alphazero_v28-b02_brierbest.pth \
  --eval-set evaluations/frozen_eval_set.pkl --out "$ART/platt_fit_v28-b02.json"
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== PROMOTIONS-MESSUNGEN FERTIG $(date +%F' '%H:%M:%S)"
