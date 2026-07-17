#!/bin/bash
# Ueberwacht den deterministischen Stufe-2-Selfplay-Lauf: prueft alle 3 Min,
# ob eine neue .pkl-Datei dazugekommen ist. Kein Fortschritt fuer >15 Min ->
# Alarm (Prozess wird NICHT automatisch gekillt, nur gemeldet).
LAST_COUNT=0
STALL_CHECKS=0
while true; do
  sleep 180
  COUNT=$(ls data/selfplay_v2s2det_*.pkl 2>/dev/null | wc -l)
  if [ "$COUNT" -ge 100 ]; then
    echo "FERTIG: $COUNT Dateien (1000 Spiele erreicht)."
    break
  fi
  if [ "$COUNT" -eq "$LAST_COUNT" ]; then
    STALL_CHECKS=$((STALL_CHECKS + 1))
  else
    STALL_CHECKS=0
  fi
  LAST_COUNT=$COUNT
  echo "$(date) Stand: $COUNT Dateien, stall_checks=$STALL_CHECKS"
  if [ "$STALL_CHECKS" -ge 5 ]; then
    echo "STALL-ALARM: seit 15 Min keine neue Datei (Stand $COUNT)."
    break
  fi
done
