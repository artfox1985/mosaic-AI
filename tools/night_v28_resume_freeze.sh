#!/usr/bin/env bash
# Fortsetzung der v28-Master-Kette nach dem Abbruch in Stufe C (2026-09-12, 06:18: der
# Schreiblauf der Paritaets-Fixture scheiterte an einer gesperrten Objektdatei in
# engine/target, os error 32). Stufen A und B sind durch und registriert.
#   C  Einfrieren v28-b02 (erneut, idempotent bis zum Artefakt-Anlegen)
#   D  Messblock (Ueberraschungs-Kante, C2)
#   E  Einhuellende A1/A2
#   F  dritter Seed der Nachbar-Kante + Startkuppel Stufe 0
# Aufruf: bash tools/night_v28_resume_freeze.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
echo "== RESUME START $(date +%F' '%H:%M:%S)"
bash tools/night_v28_freeze.sh;       RC=$?; echo "== C Freeze Exit $RC";      [ $RC -eq 0 ] || { echo "RESUME STOPP nach C"; exit 3; }
bash tools/night_v28_measure.sh;      RC=$?; echo "== D Messblock Exit $RC"
bash tools/night_envelope_bridge.sh v28-b02; RC=$?; echo "== E A1/A2 Exit $RC"
bash tools/night_v28_third_seed.sh;   RC=$?; echo "== F dritter Seed + Stufe 0 Exit $RC"
echo "== RESUME FERTIG $(date +%F' '%H:%M:%S)"
