#!/usr/bin/env bash
# Nach dem Such-Start-A/B: tail8 (v22-b05-Sprossen, v28-b01-Kanten), dann hv3 (Bau-Tore,
# Einfrieren, zwei Heuristik-Kanten). Exklusiv. Aufruf: bash tools/night_v28_tail9.sh
set -u
cd "$(dirname "$0")/.."
echo "== TAIL9 START $(date +%F' '%H:%M:%S)"
bash tools/night_v28_tail8.sh;         RC=$?; echo "== TAIL8 Exit $RC"
bash tools/night_hv3_freeze_edges.sh;  RC=$?; echo "== HV3 Exit $RC"
echo "== TAIL9 FERTIG $(date +%F' '%H:%M:%S)"
