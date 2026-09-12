#!/usr/bin/env bash
# Nach tools/night_v28_tail7.sh (Such-Start-A/B): v22-b05-Sprossen und die zwei v28-b01-Kanten.
# Exklusiv. Aufruf: bash tools/night_v28_tail8.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
echo "== TAIL8 START $(date +%F' '%H:%M:%S)"
bash tools/night_ladder_v22_edges.sh;    RC=$?; echo "== V22-SPROSSEN Exit $RC"
bash tools/night_ladder_v28b01_edges.sh; RC=$?; echo "== V28-B01-KANTEN Exit $RC"
echo "== TAIL8 FERTIG $(date +%F' '%H:%M:%S)"
