#!/usr/bin/env bash
# Fahrplan Nr. 13 und 14: Tor 1 fuer v29-b01 gegen den Champion, ZWEI Seeds, dann Tor 2b
# und die Plattenpunkte auf denselben Logs.
#
# ERSATZ fuer tools/night_v29_tor1_b01.sh (2026-09-14, 03:05). Jenes Skript wartete auf
# `models/alphazero_v29-b01_brierbest.onnx` -- eine Datei, die NIE entsteht:
#
#   `train.py` Z.2624-2626 schreibt den `_brierbest`-Checkpoint NUR, wenn die
#   Brier-beste Epoche weder die letzte noch die val_combined-beste ist ("sonst
#   waere er ein Duplikat"). Im Training v29-b01 war die beste Epoche die ZWOELFTE
#   und damit die letzte (`value_val_brier` 0,17934, Manifest
#   `manifest_train_v29-b01_20260914_012808.json`, epoch_history). Das FINALE Modell
#   IST also das value-optimale.
#
# Deshalb `alphazero_v29-b01.onnx` statt `..._brierbest.onnx`. Das ist kein anderer
# Zuschnitt, sondern derselbe: die Prereg (par.6 Punkt 7, Z.609) meint den
# value-optimalen Stand und nennt ihn nur unter dem Namen, den er sonst traegt.
#
# KEINE Warteschleife: die Kette ist um 03:00:59 fertig geworden, die Maschine ist frei.
#
# SEEDS 20261061 und 20261062 wie im Vorgaengerskript; in par.9 zu registrieren, sobald
# das Ergebnis steht. KEIN dritter Seed, wenn beide positiv sind und kein Nullentscheid
# vorliegt (Regel v27, par.6).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
CHAMP_SPEC=models/frozen_champions/v28-b02/spec.json
NEU=models/alphazero_v29-b01.onnx
ALT=models/alphazero_v28-b02_brierbest.onnx

for f in "$NEU" "$ALT" "$CHAMP_SPEC"; do
  if [ ! -f "$f" ]; then
    echo "ABBRUCH: $f fehlt -- kein stiller Leerlauf."
    exit 1
  fi
done
echo "== TOR 1 START $(date +%F' '%H:%M:%S)"
echo "   Kandidat: $NEU (value-optimal, Epoche 12 = letzte)"
echo "   Champion: $ALT"

for SEED in 20261061 20261062; do
  OUT="$ART/paired_gating_v29-b01_vs_v28-b02_s${SEED}.json"
  echo "== TOR 1, Seed $SEED $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$NEU" --spec-a "$CHAMP_SPEC" \
    --model-b "$ALT" --spec-b "$CHAMP_SPEC" \
    --name-a v29-b01 --name-b v28-b02 --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --seed "$SEED" --threads 10 --log-games \
    --no-promote-winner --out "$OUT"
  echo "   Gating Exit $? ($(date +%H:%M:%S))"

  echo "== TOR 2b und Plattenpunkte, Seed $SEED $(date +%H:%M:%S)"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  echo "   Spalten Exit $?"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_v29-b01_vs_v28-b02_s${SEED}.json"
  echo "   Platten Exit $? ($(date +%H:%M:%S))"
done

echo "== TOR 1 FERTIG $(date +%F' '%H:%M:%S)"
echo "   Naechster Fahrplanpunkt: Nr. 15/16 (Wheel fuer Abschnitt 16 plus Ablations-Tore,"
echo "   dann Bloecke unter dem 794er-Schluessel und die Trainings b02/b03)."
echo "   Register-Zeilen und par.9-Eintrag macht der Koordinator; der DRITTE Seed ist ein"
echo "   Entscheid, kein Automatismus (Regel v27, par.6)."
