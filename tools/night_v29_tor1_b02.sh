#!/usr/bin/env bash
# Fahrplan Nr. 17: Tor 1 fuer die Spezialfeld-Ablation v29-b02 GEGEN b03, zwei Seeds,
# dann Tor 2b und die Plattenpunkte auf denselben Logs.
#
# BEZUGSPUNKT IST b03, NICHT b01 (Nutzer-Entscheid 2026-09-14: "die 794 kommen
# sowieso"). Beide Arme tragen INPUT_SIZE 794; der einzige Unterschied ist
# MOSAIC_SPECIAL_PLANES_OFF, also die Planes-Kanaele 77 und 78. Damit ist der
# Vergleich sauber einfaktoriell und misst genau das, wofuer die Ablation gebaut
# wurde (PREREG_special_tile_yield.md Nachtrag 2026-09-11, PREREG_v29_window.md par.9).
#
# Gegen b01 waere er zweifaktoriell (Schalter UND Sichtwerte) -- deshalb nicht.
#
# LESART: b02 hat die Kanaele AUS. Gewinnt b02, tragen die Spezialfeld-Kanaele NICHT
# (die Ablation waere dann eine Verbesserung); verliert er, tragen sie.
#
# MODELLNAMEN NACHGESEHEN, nicht geraten (par.9): beide Arme haben ein `_brierbest`.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
CHAMP_SPEC=models/frozen_champions/v28-b02/spec.json
NEU=models/alphazero_v29-b02_brierbest.onnx
ALT=models/alphazero_v29-b03_brierbest.onnx

for f in "$NEU" "$ALT" "$CHAMP_SPEC"; do
  if [ ! -f "$f" ]; then
    echo "ABBRUCH: $f fehlt -- kein stiller Leerlauf."
    exit 1
  fi
done
echo "== TOR 1 b02 gegen b03 START $(date +%F' '%H:%M:%S)"
echo "   Kandidat: $NEU"
echo "   Bezug:    $ALT"

for SEED in 20261065 20261066; do
  OUT="$ART/paired_gating_v29-b02_vs_v29-b03_s${SEED}.json"
  echo "== TOR 1, Seed $SEED $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$NEU" --spec-a "$CHAMP_SPEC" \
    --model-b "$ALT" --spec-b "$CHAMP_SPEC" \
    --name-a v29-b02 --name-b v29-b03 --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --seed "$SEED" --threads 10 --log-games \
    --no-promote-winner --out "$OUT"
  echo "   Gating Exit $? ($(date +%H:%M:%S))"

  echo "== TOR 2b und Plattenpunkte, Seed $SEED $(date +%H:%M:%S)"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  echo "   Spalten Exit $?"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_v29-b02_vs_v29-b03_s${SEED}.json"
  echo "   Platten Exit $? ($(date +%H:%M:%S))"
done

echo "== TOR 1 b03 FERTIG $(date +%F' '%H:%M:%S)"
echo "   Offen bleibt Nr. 17 (b02): sein Bezugspunkt ist ein Nutzer-Entscheid, weil b02"
echo "   zweifaktoriell gegen b01 steht (par.9). Gegen b03 waere er einfaktoriell."
