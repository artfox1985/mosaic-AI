#!/usr/bin/env bash
# Nach den zwei Code-Auftraegen vom 2026-09-12 (Platte/Rotation-Sonde der Startkuppel,
# PREREG_start_dome_choice.md par.9f; Replayer liest die Startsetzung aus dem Log): Bau-Tore,
# Rauchtest und voller Lauf der Sonde, dann die Spaltensonde auf dem Such-Start-A/B (par.9e, dort
# waren 190 von 190 Partien nicht nachspielbar). Exklusiv.
# Aufruf: bash tools/night_tile_probe_replay.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
bash tools/night_startslot_build.sh; RC=$?; echo "== BAU Exit $RC"; [ $RC -eq 0 ] || { echo "STOPP: Bau rot"; exit 21; }
python -X utf8 -m unittest tools/tests/test_action_id_mirror.py; echo "   Spiegeltest Exit $?"
echo "== RAUCHTEST Platte/Rotation-Sonde $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/probes/start_dome_tile_probe.py --limit 4 --pairings 25 --threads 4 --out "$ART/start_dome_tile_probe_smoke.json"
RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"; [ $RC -eq 0 ] || { echo "STOPP: Rauchtest rot"; exit 22; }
echo "== VOLLER LAUF Platte/Rotation-Sonde $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/probes/start_dome_tile_probe.py --out "$ART/start_dome_tile_probe.json"
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== A/B SUCH-START WIEDERHOLT (eigener RNG-Strom der Start-Suche, echte Paarung), Seed 20261049 $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/paired_gating.py   --model-a models/alphazero_v28-b02_brierbest.onnx --model-b models/alphazero_v28-b02_brierbest.onnx   --name-a v28-b02_startsearch --name-b v28-b02   --spec-a models/start_by_search_on.spec.json --spec-b models/frozen_champions/v27-b01/spec.json   --sims 400 --block-size 5 --max-pairs 200 --seed 20261049 --threads 10   --log-games --no-promote-winner --out "$ART/paired_gating_v28-b02_startsearch_vs_v28-b02_s49.json"
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== SPALTENSONDE auf dem neuen A/B (Replay muss jetzt tragen) $(date +%H:%M:%S)"
python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$ART/paired_gating_v28-b02_startsearch_vs_v28-b02_s49.json"
echo "   Spalten Exit $? ($(date +%H:%M:%S))"
python -X utf8 -u tools/plate_points_from_arena.py "$ART/paired_gating_v28-b02_startsearch_vs_v28-b02_s49.json"
echo "   Platten Exit $? ($(date +%H:%M:%S))"
echo "== TILE-PROBE + REPLAY FERTIG $(date +%F' '%H:%M:%S)"
