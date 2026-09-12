#!/usr/bin/env bash
# Nach dem (verwaisten) Ende von tools/night_v28_tail5.sh: fehlende Leiter-Kanten, v21-Sprossen,
# dann A/B des Such-Starts. Exklusiv.
# Aufruf: bash tools/night_v28_tail7.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
echo "== TAIL7 START $(date +%F' '%H:%M:%S)"
bash tools/night_ladder_missing_edges.sh; RC=$?; echo "== FEHLENDE KANTEN Exit $RC"
bash tools/night_ladder_v21_edges.sh;     RC=$?; echo "== V21-SPROSSEN Exit $RC"
bash tools/night_start_by_search_ab.sh;   RC=$?; echo "== SUCH-START A/B Exit $RC"
echo "== TAIL7 FERTIG $(date +%F' '%H:%M:%S)"
