#!/usr/bin/env bash
# Promotion v26-b01: die MESSENDEN Schritte der Checkliste, nacheinander und exklusiv.
# docs/promotion_checklist.md ist die Liste; hier stehen nur die Laeufe.
# Nutzer-Auftrag 2026-09-09, 18:05: "fahr die promotion."
#
# Schritt 1 (set_champion) und die drei Gating-Kanten sind bereits erledigt.
# Was hier laeuft:
#   3  Anker-Kante, festes n=150 ohne Fruehstopp
#   4  Champion-2-Kante gegen v24-b07 -- UEBER DAS EINGEFRORENE ARTEFAKT, mit dessen
#      eigenem Wheel. Das ist der Methodenfehler, der bei v25-b01 und v24-b07 gemacht
#      wurde (gegen die LEBENDEN Modelldateien gemessen, also heutiger Motor auf beiden
#      Seiten). Er ist hier vermeidbar: das Artefakt liegt vollstaendig vor, und die
#      Wheels unterscheiden sich tatsaechlich (v24-b07: wegb_temp2 vom 07.09.,
#      installiert: wegbc vom 08.09.).
#   5c sigma/Prior-Balance (Waechter: ueber 3 oeffnet sich die c_visit/c_scale-Familie)
#   5b Anzeige-Kalibrierung, beide Fits -- frozen_v3 fuer die ANZEIGE, frozen_v1 nur
#      als Trendmetrik (Verteilungs-Caveat der Checkliste).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
NEU=models/alphazero_v26-b01_brierbest.onnx
SPEC=models/v24-b07_brierbest.spec.json

echo "== 3) Anker-Kante, n=150 ohne Fruehstopp $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/anchor_arena.py --model "$NEU" --spec "$SPEC" \
  --net-sims 400 --anchor-sims 150 --n-games 150 --seed-base 900001 --workers 6 \
  --force-cross-era --out "$ART/anchor_arena_v26-b01.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 4) Champion-2-Kante gegen das ARTEFAKT v24-b07 $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/frozen_referee_match.py \
  --artifact-dir models/frozen_champions/v24-b07 \
  --model-a "$NEU" --spec-a "$SPEC" \
  --sims-a 400 --sims-worker 400 --n-games 150 --seed-base 20261040 --workers 6 \
  --out "$ART/champion2_v26-b01_vs_v24-b07.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 5c) sigma/Prior-Balance $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/gumbel_scale_calibration.py --model v26-b01_brierbest \
  --sims 400 --n-states 300 --out "$ART/gumbel_scale_calibration_v26-b01.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 5b) Anzeige-Kalibrierung, Fit auf frozen_v3 $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/platt_fit.py --models models/alphazero_v26-b01_brierbest.pth \
  --eval-set evaluations/frozen_eval_set_v3.pkl --out "$ART/platt_fit_v26-b01_v3.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 5b) Trendmetrik, Fit auf frozen_v1 $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/platt_fit.py --models models/alphazero_v26-b01_brierbest.pth \
  --eval-set evaluations/frozen_eval_set.pkl --out "$ART/platt_fit_v26-b01.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== PROMOTIONS-MESSUNGEN FERTIG $(date +%F' '%H:%M:%S)"
echo "   Offen bleiben die schreibenden Schritte: Elo-Kanten eintragen, 5b in server.py,"
echo "   5d Netz-Paritaets-Fixture (cargo test, BUILD -- nicht neben eine Messung),"
echo "   STATUS/history, und das eingefrorene Artefakt (Schritt 7)."
