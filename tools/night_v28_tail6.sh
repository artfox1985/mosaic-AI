#!/usr/bin/env bash
# Nach tools/night_v28_tail5.sh: v21-Sprossen (Nachlauf), dann A/B des Such-Starts. Exklusiv.
# Aufruf: bash tools/night_v28_tail6.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
echo "== TAIL6 START $(date +%F' '%H:%M:%S)"
bash tools/night_ladder_v21_edges.sh;     RC=$?; echo "== V21-SPROSSEN Exit $RC"
bash tools/night_start_by_search_ab.sh;   RC=$?; echo "== SUCH-START A/B Exit $RC"
echo "== TAIL6 FERTIG $(date +%F' '%H:%M:%S)"
