#!/usr/bin/env bash
# v28-Programm, Master-Kette nach der Neuverankerung (2026-09-12, autonom nach Nutzer-Freigabe
# "ja, fahr das so" / "lass sie in v28"): nacheinander, exklusiv, jede Stufe mit Abbruch-Tor.
#   A  Knopf-Bau (Wheel mit allen neuen Knoepfen, Tore: Tests, Fixture, Anker-Drift)
#   B  Promotions-Messungen v28-b02 (Champion-2-Kante, sigma/Prior, Platt)
#   C  Einfrieren v28-b02 (set_champion, Fixture, Artefakt, Golden Probe, Selbsttest)
#   D  Messblock (Ueberraschungs-Kante, C2 der Einhuellenden)
#   E  Einhuellende A1/A2 (Orakel-Bruecke, vier Einstellungen)
# Aufruf: bash tools/night_v28_after_reanchor.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
echo "== MASTER START $(date +%F' '%H:%M:%S)"
bash tools/night_v28_knob_build.sh;   RC=$?; echo "== A Knopf-Bau Exit $RC";   [ $RC -eq 0 ] || { echo "MASTER STOPP nach A"; exit 1; }
bash tools/night_v28_promotion.sh;    RC=$?; echo "== B Promotion Exit $RC";   [ $RC -eq 0 ] || { echo "MASTER STOPP nach B"; exit 2; }
bash tools/night_v28_freeze.sh;       RC=$?; echo "== C Freeze Exit $RC";      [ $RC -eq 0 ] || { echo "MASTER STOPP nach C"; exit 3; }
bash tools/night_v28_measure.sh;      RC=$?; echo "== D Messblock Exit $RC"
bash tools/night_envelope_bridge.sh v28-b02; RC=$?; echo "== E A1/A2 Exit $RC"
echo "== MASTER FERTIG $(date +%F' '%H:%M:%S)"
