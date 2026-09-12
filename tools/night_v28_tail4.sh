#!/usr/bin/env bash
# Nach tools/night_v28_tail3.sh (dessen Leiter-Teil am v21-Selbsttest und dessen hv2-Gegenprobe an
# einem Pfadfehler scheiterten, beide behoben 12:15): Leiter (zweite Fassung, v21 aus wave3g),
# dann hv2-Gegenprobe der Startkuppel-Sonde. Exklusiv, nach dem K3-D/Jokerfeld-Instrument.
# Aufruf: bash tools/night_v28_tail4.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
echo "== TAIL4 START $(date +%F' '%H:%M:%S)"
bash tools/night_ladder_rungs2.sh;  RC=$?; echo "== LEITER Exit $RC"
bash tools/night_start_dome_hv2.sh; RC=$?; echo "== hv2-GEGENPROBE Exit $RC"
echo "== TAIL4 FERTIG $(date +%F' '%H:%M:%S)"
