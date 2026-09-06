#!/usr/bin/env bash
# Halte-Prozess waehrend einer Claude-Partie (PREREG_claude_play_interface.md): der Dateiname
# passt auf das Wartemuster 'claude_pla[y]' der Knopf-Messkette (night_k3_knobs_champion.sh),
# damit sie nicht zwischen zwei Zuegen (getrennte Prozesse, Luecken > 60 s) anspringt.
# Endet, sobald die Marke evaluations/artifacts/claude_play/.playing fehlt.
# Aufruf (Hintergrund):  bash tools/claude_play_hold.sh
set -u
cd "$(dirname "$0")/.."
MARK="evaluations/artifacts/claude_play/.playing"
mkdir -p "$(dirname "$MARK")"; touch "$MARK"
echo "== Halte fuer Claude-Partie $(date +%H:%M:%S) (Marke $MARK)"
t=0
while [ -f "$MARK" ]; do sleep 30; t=$((t+1)); [ $t -gt 480 ] && { echo "Deckel 4 h, Marke entfernt"; rm -f "$MARK"; exit 9; }; done
echo "== Partie beendet, Halte frei $(date +%H:%M:%S)"
