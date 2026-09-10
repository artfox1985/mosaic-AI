#!/usr/bin/env bash
# Promotion v27-b01: die MESSENDEN Schritte der Checkliste, nacheinander und exklusiv.
# docs/promotion_checklist.md ist die Liste; hier stehen nur die Laeufe.
# Nutzer-Auftrag 2026-09-10, 13:20: "Kannst dann autark weiterfahren mit dem v27 Programm."
#
# Vorher gelaufen: Tor 1 v27-b01 gegen v26-b01, Seeds 20261034 (SPRT nach 45 Paaren) und
# 20261035 (Replikation bis zum Deckel), beide MIT --log-games. Was hier laeuft:
#   0  Spaltensonde auf beide Tor-1-Artefakte (Tor 2b fuer v27-b01, aus denselben Partien)
#      und Wertungsplatten-Punkte je Kriterium auf s33 (v26 gegen v25) und s34/s35
#   3  Anker-Kante, festes n=150 ohne Fruehstopp
#   4  Champion-2-Kante gegen v25-b01 -- UEBER DAS EINGEFRORENE ARTEFAKT mit dessen Wheel
#   5c sigma/Prior-Balance (Waechter: ueber 3 oeffnet sich die c_visit/c_scale-Familie)
#   5b Anzeige-Kalibrierung, beide Fits (frozen_v3 fuer die ANZEIGE, frozen_v1 Trendmetrik)
# Schritt 1 (set_champion) faellt erst, wenn Tor 1 registriert ist; Schritt 5d (cargo test)
# und Schritt 7 (Artefakt, Golden Probe) folgen danach, weil sie Build bzw. 22 min kosten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
NEU=models/alphazero_v27-b01_brierbest.onnx
SPEC=models/v24-b07_brierbest.spec.json

echo "== 0a) Spaltensonde auf die Tor-1-Artefakte $(date +%F' '%H:%M:%S)"
for K in s34 s35; do
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$ART/paired_gating_v27-b01_vs_v26-b01_${K}.json"
  echo "   Exit $? ($K, $(date +%H:%M:%S))"
done

echo "== 0b) Wertungsplatten-Punkte je Kriterium $(date +%F' '%H:%M:%S)"
for J in paired_gating_v26-b01_vs_v25-b01_s33_logs paired_gating_v27-b01_vs_v26-b01_s34 paired_gating_v27-b01_vs_v26-b01_s35; do
  python -X utf8 -u tools/plate_points_from_arena.py "$ART/$J.json"
  echo "   Exit $? ($J, $(date +%H:%M:%S))"
done

echo "== 3) Anker-Kante, n=150 ohne Fruehstopp $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/anchor_arena.py --model "$NEU" --spec "$SPEC" \
  --net-sims 400 --anchor-sims 150 --n-games 150 --seed-base 900001 --workers 6 \
  --force-cross-era --out "$ART/anchor_arena_v27-b01.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 4) Champion-2-Kante gegen das ARTEFAKT v25-b01 $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/frozen_referee_match.py \
  --artifact-dir models/frozen_champions/v25-b01 \
  --model-a "$NEU" --spec-a "$SPEC" \
  --sims-a 400 --sims-worker 400 --n-games 150 --seed-base 20261050 --workers 6 \
  --out "$ART/champion2_v27-b01_vs_v25-b01.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 5c) sigma/Prior-Balance $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/gumbel_scale_calibration.py --model v27-b01_brierbest \
  --sims 400 --n-states 300 --out "$ART/gumbel_scale_calibration_v27-b01.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 5b) Anzeige-Kalibrierung, Fit auf frozen_v3 $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/platt_fit.py --models models/alphazero_v27-b01_brierbest.pth \
  --eval-set evaluations/frozen_eval_set_v3.pkl --out "$ART/platt_fit_v27-b01_v3.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 5b) Trendmetrik, Fit auf frozen_v1 $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/platt_fit.py --models models/alphazero_v27-b01_brierbest.pth \
  --eval-set evaluations/frozen_eval_set.pkl --out "$ART/platt_fit_v27-b01.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== PROMOTIONS-MESSUNGEN FERTIG $(date +%F' '%H:%M:%S)"
echo "   Offen: Elo-Kanten eintragen, set_champion, 5b in server.py, 5d Paritaets-Fixture"
echo "   (cargo test, BUILD), STATUS/history, eingefrorenes Artefakt (Schritt 7)."
