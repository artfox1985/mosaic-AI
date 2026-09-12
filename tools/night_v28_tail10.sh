#!/usr/bin/env bash
# Nach tail9 (dessen hv3-Bau an einem Test-Wortlaut scheiterte, behoben 20:25): hv3-Kette, dann
# die Huellen-Diagnose des Such-Starts. Exklusiv. Aufruf: bash tools/night_v28_tail10.sh
set -u
cd "$(dirname "$0")/.."
echo "== TAIL10 START $(date +%F' '%H:%M:%S)"
bash tools/night_hv3_freeze_edges.sh;      RC=$?; echo "== HV3 Exit $RC"
bash tools/night_start_search_hull_off.sh; RC=$?; echo "== HUELLE-DIAGNOSE Exit $RC"
echo "== TAIL10 FERTIG $(date +%F' '%H:%M:%S)"
