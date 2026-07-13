#!/bin/bash
echo "$(date) Warte auf 50 v2s2-Dateien (500 Spiele)..."
while [ "$(ls data/selfplay_v2s2_*.pkl 2>/dev/null | wc -l)" -lt 50 ]; do
  sleep 60
done
echo "$(date) 500 Spiele erreicht: $(ls data/selfplay_v2s2_*.pkl | wc -l) Dateien."
