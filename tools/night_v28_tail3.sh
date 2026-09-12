#!/usr/bin/env bash
# Ersatz fuer tools/night_v28_tail2.sh (gestoppt 12:05, weil v24-b07 als Artefakt aus dem Backup
# kam): Leiter (zweite Fassung) dann Schwanz. Exklusiv.
# Aufruf: bash tools/night_v28_tail3.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
echo "== TAIL3 START $(date +%F' '%H:%M:%S)"
bash tools/night_ladder_rungs2.sh; RC=$?; echo "== LEITER Exit $RC"
bash tools/night_v28_tail.sh;      RC=$?; echo "== TAIL Exit $RC"
echo "== TAIL3 FERTIG $(date +%F' '%H:%M:%S)"
