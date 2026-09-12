#!/usr/bin/env bash
# Nach tools/night_v28_tail3.sh: erst der Bau-Durchgang fuer den Streu-Knopf (Default 0, Tore),
# dann Leiter (zweite Fassung) und hv2-Gegenprobe (tools/night_v28_tail4.sh). Exklusiv.
# Aufruf: bash tools/night_v28_tail5.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
echo "== TAIL5 START $(date +%F' '%H:%M:%S)"
bash tools/night_startslot_build.sh; RC=$?; echo "== KNOPF-BAU Exit $RC"; [ $RC -eq 0 ] || { echo "STOPP: Bau rot -- die Python-Treiber (Referee) rufen neue Engine-Signaturen, Leiter nicht auf altem Wheel"; exit 5; }
bash tools/night_v28_tail4.sh;      RC=$?; echo "== TAIL4 Exit $RC"
echo "== TAIL5 FERTIG $(date +%F' '%H:%M:%S)"
