#!/usr/bin/env bash
# Schwanz des v28-Programms nach tools/night_v28_resume_freeze.sh (2026-09-12):
#   G  hv2-Gegenprobe der Startkuppel-Sonde (Weg 3): Rauchtest, dann voller Lauf
#   H  K3-D und Jokerfeld am argmax-Instrument
# Aufruf: bash tools/night_v28_tail.sh   (Hintergrundaufgabe, keine Pipe, exklusiv)
set -u
cd "$(dirname "$0")/.."
echo "== TAIL START $(date +%F' '%H:%M:%S)"
echo "== F2 Replay-Sonden auf dem dritten Seed und der Ueberraschungs-Kante $(date +%H:%M:%S)"
for E in evaluations/artifacts/paired_gating_v28-b02_vs_v27-b01_s47_segment2.json evaluations/artifacts/paired_gating_v24-b05_vs_v24-b04_s45.json; do
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$E"; echo "   Spalten Exit $? ($E)"
  python -X utf8 -u tools/plate_points_from_arena.py "$E"; echo "   Platten Exit $?"
done
bash tools/night_start_dome_hv2.sh;        RC=$?; echo "== G hv2-Gegenprobe Exit $RC"
bash tools/night_k3d_joker_instrument.sh;  RC=$?; echo "== H K3-D/Jokerfeld Exit $RC"
echo "== TAIL FERTIG $(date +%F' '%H:%M:%S)"
