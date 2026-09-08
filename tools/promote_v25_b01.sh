#!/usr/bin/env bash
# Promotion v25-b01 (docs/promotion_checklist.md, Skill mosaic-champion-promotion).
# Champion-1 = v24-b07, Champion-2 = v24-b06 (Nutzer 2026-09-08).
#
# Schritt 2 (Gating-Kante) liegt bereits vor und wird nur eingetragen:
#   Seed 20261020  53:27  (SPRT nach 40 Paaren)
#   Seed 20261021 129:91  (SPRT nach 110 Paaren)  -- die geforderte Replikation
#   gepoolt 182:118 = 0,607, p 0,0003, KI [0,551; 0,662]
#
# ANMERKUNG zu Schritt 4: v24-b06 und v24-b07 teilen die GEWICHTE und unterscheiden sich
# nur in der Spec (Huellenform 2, K5). Die Champion-2-Kante misst hier also dasselbe Netz
# unter der alten Spec. Sie ist trotzdem ein eigener Leiterknoten mit eigenen Kanten, und
# der Zweck des Schritts -- die Elo-Schaetzung auf mehr als eine Kante stellen -- ist
# erfuellt.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
NET=models/alphazero_v25-b01_brierbest.onnx
SPEC=models/v24-b07_brierbest.spec.json
ART=evaluations/artifacts

echo "== 1) Server-Default auf v25-b01 $(date +%H:%M:%S)"
python -X utf8 tools/set_champion.py v25-b01_brierbest; echo "   Exit $?"

echo "== 3) ANKER-Kante, festes n=150 ohne Fruehstopp $(date +%H:%M:%S)"
python -X utf8 -u tools/anchor_arena.py --model "$NET" --spec "$SPEC" \
  --net-sims 400 --anchor-sims 150 --n-games 150 --workers 6 --force-cross-era \
  --out "$ART/anchor_arena_v25-b01.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 4) CHAMPION-2-Kante gegen v24-b06 @400 $(date +%H:%M:%S)"
python -X utf8 -u tools/paired_gating.py \
  --model-a "$NET" --model-b models/alphazero_v24-b06_brierbest.onnx \
  --name-a v25-b01 --name-b v24-b06_k3p10 \
  --spec-a "$SPEC" --spec-b models/v24-b06_brierbest.spec.json \
  --sims 400 --block-size 5 --max-pairs 200 --seed 20261022 --threads 10 \
  --no-promote-winner --out "$ART/paired_gating_v25-b01_vs_v24-b06_s22.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 5b) Anzeige-Kalibrierung: Platt-Parameter des NEUEN Champions $(date +%H:%M:%S)"
python -X utf8 -u tools/platt_fit.py --models models/alphazero_v25-b01_brierbest.pth \
  --out "$ART/platt_fit_v25-b01.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 5c) sigma/Prior-Balance $(date +%H:%M:%S)"
python -X utf8 -u tools/gumbel_scale_calibration.py --model v25-b01_brierbest \
  --sims 400 --n-states 300 --out "$ART/gumbel_scale_calibration_v25-b01.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 5d) Netz-Paritaets-Fixture neu $(date +%H:%M:%S)"
. tools/hooks/python_dll_path.sh 2>/dev/null && mosaic_prepend_python_dll_path 2>/dev/null || true
( cd engine && MOSAIC_UPDATE_NET_PARITY_FIXTURE=1 cargo test --release net_parity_hash_matches_champion_fixture -- --nocapture )
echo "   Schreiben Exit $? ($(date +%H:%M:%S))"
( cd engine && cargo test --release net_parity_hash_matches_champion_fixture )
echo "   Gegenprobe Exit $? ($(date +%H:%M:%S))"

echo "== PROMOTION-MESSUNGEN FERTIG $(date +%H:%M:%S): Elo-Zeilen, Artefakt, STATUS macht der Koordinator."
