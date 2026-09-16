#!/usr/bin/env bash
# Fortschrittsanzeige fuer die verwaiste b04-Kette (2026-09-16).
#
# WARUM ES IHN GIBT: der Wrapper der Kette wurde per TaskStop beendet (er hatte
# seinen eigenen Skripttext in der Kommandozeile und blockierte damit zwei
# Sitzungen, docs/pitfalls.md). Das Skript selbst laeuft verwaist weiter und
# arbeitet korrekt, hat aber keine Harness-Ausgabe mehr. Dieser Beobachter
# stellt sie ueber die ARTEFAKTE wieder her.
#
# ER WIRD ALS DATEI GESTARTET (`bash tools/watch_v29_b04.sh`), NIE per
# Heredoc-und-Start: die Kette laeuft noch mit der ungehaerteten Wartebedingung,
# die auf Prozess-Kommandozeilen greppt -- ein Wrapper mit diesem Text darin
# wuerde sie erneut blockieren.
#
# Reine Beobachtung: ein `ls` je 120 s, keine nennenswerte Last.
set -uo pipefail
cd "$(dirname "$0")/.."
LETZTER=""
while :; do
  SCHRITT="wartet"
  AKTIV=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.Name -match 'python' } | Select-Object -First 1 -ExpandProperty CommandLine)" 2>/dev/null | tr -d '\r')
  case "$AKTIV" in
    *build_cache*merge-out*) SCHRITT="2/4 Monolith" ;;
    *build_cache*)           SCHRITT="1/4 Bloecke" ;;
    *window_train_split*)    SCHRITT="2/4 Split" ;;
    *tr""ain.py*)            SCHRITT="3/4 Training" ;;
    *paired_ga""ting*)       SCHRITT="4/4 Tor 1" ;;
    *offline_diag*)          SCHRITT="(fremd: Netz-Gesundheit)" ;;
    "")                      SCHRITT="Maschine frei / Kette wartet" ;;
    *)                       SCHRITT="anderer Python-Lauf" ;;
  esac
  ART=""
  [ -f evaluations/artifacts/v29_b04_split.txt ] && ART="$ART split"
  [ -f models/alphazero_v29-b04_brierbest.onnx ] && ART="$ART modell"
  for f in evaluations/artifacts/tor1_v29-b04_vs_b03_s*.json; do
    [ -f "$f" ] && ART="$ART $(basename "$f" .json | sed 's/.*_s/tor1_s/')"
  done
  ZEILE="$SCHRITT |${ART:- noch keine Artefakte}"
  if [ "$ZEILE" != "$LETZTER" ]; then
    echo "$(date +%H:%M:%S)  $ZEILE"
    LETZTER="$ZEILE"
  else
    echo "$(date +%H:%M:%S)  ... unveraendert"
  fi
  # Ende: Kette durch, wenn beide Tor-1-Artefakte liegen
  n=$(ls evaluations/artifacts/tor1_v29-b04_vs_b03_s*.json 2>/dev/null | wc -l)
  [ "$n" -ge 2 ] && { echo "$(date +%H:%M:%S)  BEIDE TOR-1-ARTEFAKTE DA -- Kette durch"; break; }
  sleep 120
done
