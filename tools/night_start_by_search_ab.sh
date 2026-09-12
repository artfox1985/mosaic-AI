#!/usr/bin/env bash
# Such-Start der Startkuppel (PREREG_start_dome_choice.md par.9c, Nutzer 2026-09-12): erst der
# gemeinsame Bau-Durchgang der beiden neuen Knoepfe (MOSAIC_START_SLOT_RANDOM_P, MOSAIC_START_BY_SEARCH;
# Tore: Tests, Fixture UNVERAENDERT, Anker-Drift, Konventionen), dann A/B am Champion v28-b02:
# Spec models/start_by_search_on.spec.json (Champion-Spec plus start_by_search 1) gegen die
# Champion-Spec, 200 Paare, Blockgroesse 5, Logs, Seed 20261048. Messfragen par.9c: (a) wie oft
# weicht die Suche von (0,0) ab (START_TILE-Logzeilen), (b) Punkte/Marge gepaart, (c) Siege.
# Exklusiv, nach tools/night_v28_tail4.sh.
# Aufruf: bash tools/night_start_by_search_ab.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
bash tools/night_startslot_build.sh; RC=$?; echo "== BAU Exit $RC"; [ $RC -eq 0 ] || { echo "STOPP: Bau rot, kein A/B"; exit 21; }
python -X utf8 -c "import json,mosaic_rust as m; print('Kontrakt', json.loads(m.engine_config_json())['contract_hash'])"
echo "== A/B SUCH-START v28-b02 (an gegen aus), Seed 20261048 $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/paired_gating.py \
  --model-a models/alphazero_v28-b02_brierbest.onnx --model-b models/alphazero_v28-b02_brierbest.onnx \
  --name-a v28-b02_startsearch --name-b v28-b02 \
  --spec-a models/start_by_search_on.spec.json --spec-b models/frozen_champions/v27-b01/spec.json \
  --sims 400 --block-size 5 --max-pairs 200 --seed 20261048 --threads 10 \
  --log-games --no-promote-winner --out "$ART/paired_gating_v28-b02_startsearch_vs_v28-b02_s48.json"
echo "   Exit $? ($(date +%H:%M:%S))"
python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$ART/paired_gating_v28-b02_startsearch_vs_v28-b02_s48.json"; echo "   Spalten Exit $?"
python -X utf8 -u tools/plate_points_from_arena.py "$ART/paired_gating_v28-b02_startsearch_vs_v28-b02_s48.json"; echo "   Platten Exit $?"
echo "== SUCH-START A/B FERTIG $(date +%F' '%H:%M:%S)"
