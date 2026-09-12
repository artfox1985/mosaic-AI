#!/usr/bin/env bash
# Nach tools/night_v28_resume_freeze.sh (2026-09-12, 11:50 fertig): erst die Leiter reparieren
# (Anker-Kanten korrekt + Zwischenstufen), dann der Schwanz (Replay-Sonden, hv2-Gegenprobe,
# K3-D/Jokerfeld am Instrument). Exklusiv.
# Aufruf: bash tools/night_v28_tail2.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
echo "== TAIL2 START $(date +%F' '%H:%M:%S)"
bash tools/night_ladder_rungs.sh; RC=$?; echo "== LEITER Exit $RC"
bash tools/night_v28_tail.sh;     RC=$?; echo "== TAIL Exit $RC"
echo "== TAIL2 FERTIG $(date +%F' '%H:%M:%S)"
