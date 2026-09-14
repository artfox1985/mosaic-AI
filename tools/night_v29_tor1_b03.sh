#!/usr/bin/env bash
# Fahrplan Nr. 19: Tor 1 fuer den Sicht-Arm v29-b03 GEGEN b01, zwei Seeds, dann Tor 2b
# und die Plattenpunkte auf denselben Logs.
#
# Bezugspunkt ist b01, nicht der Champion: b03 aendert gegenueber b01 genau einen
# Faktor, den Eingang (INPUT_SIZE 794 statt 755, Abschnitt 16). Fenster, Seed und
# Rezept sind identisch.
#
# LESART (PREREG_v29_window.md par.9): von den 39 neuen Werten sind nur 19 ueber das
# ganze Fenster belegt, 2 auf 40,8 Prozent (P.14) und 18 gar nicht (P.12, wirkt erst
# ab v30). Der Arm misst also im Wesentlichen diese 19 -- das gehoert ins Verdikt.
#
# MODELLNAMEN NACHGESEHEN, nicht geraten (par.9): b03 hat ein `_brierbest`, b01 nicht
# (dort war die beste Brier-Epoche die letzte, das finale Modell IST der
# value-optimale Stand).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
CHAMP_SPEC=models/frozen_champions/v28-b02/spec.json
NEU=models/alphazero_v29-b03_brierbest.onnx
ALT=models/alphazero_v29-b01.onnx

for f in "$NEU" "$ALT" "$CHAMP_SPEC"; do
  if [ ! -f "$f" ]; then
    echo "ABBRUCH: $f fehlt -- kein stiller Leerlauf."
    exit 1
  fi
done
echo "== TOR 1 b03 gegen b01 START $(date +%F' '%H:%M:%S)"
echo "   Kandidat: $NEU"
echo "   Bezug:    $ALT"

for SEED in 20261063 20261064; do
  OUT="$ART/paired_gating_v29-b03_vs_v29-b01_s${SEED}.json"
  echo "== TOR 1, Seed $SEED $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$NEU" --spec-a "$CHAMP_SPEC" \
    --model-b "$ALT" --spec-b "$CHAMP_SPEC" \
    --name-a v29-b03 --name-b v29-b01 --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --seed "$SEED" --threads 10 --log-games \
    --no-promote-winner --out "$OUT"
  echo "   Gating Exit $? ($(date +%H:%M:%S))"

  echo "== TOR 2b und Plattenpunkte, Seed $SEED $(date +%H:%M:%S)"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  echo "   Spalten Exit $?"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_v29-b03_vs_v29-b01_s${SEED}.json"
  echo "   Platten Exit $? ($(date +%H:%M:%S))"
done

echo "== TOR 1 b03 FERTIG $(date +%F' '%H:%M:%S)"
echo "   Offen bleibt Nr. 17 (b02): sein Bezugspunkt ist ein Nutzer-Entscheid, weil b02"
echo "   zweifaktoriell gegen b01 steht (par.9). Gegen b03 waere er einfaktoriell."
