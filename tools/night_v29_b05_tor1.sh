#!/usr/bin/env bash
# Tor 1 fuer v29-b05 gegen b03 (PREREG_moon_stack_order.md par.12.1).
#
# LESART VORAB: b05 hat den `moon`-Kopf ablatiert (--moon-loss-weight 0). Sein
# Trainingsziel war ein No-Op (par.12.0: das Label ist immer die kanonische
# Reihenfolge, der Rundenloeser liest die Fabriken nicht). Traegt b05, hat
# dieses Rauschziel Policy-Qualitaet gekostet -- und die Task-#38-Behauptung
# "der Kopf hilft" ist erstmals gemessen statt behauptet.
#
# ZWEI SEEDS, 200 Paare, KEIN Frueh-Stopp (alpha=beta=0,001): Elo-Kanten aus
# Frueh-Stopp sind nach oben verzerrt, und dieser Arm soll eine belastbare Zahl
# liefern. Champion-Spec beidseitig, gleiches Wheel.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
A=models/alphazero_v29-b05_brierbest.onnx
B=models/alphazero_v29-b03_brierbest.onnx
SPEC=models/frozen_champions/v28-b02/spec.json

for f in "$A" "$B" "$SPEC"; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done

for SEED in 20261120 20261121; do
  OUT="$ART/tor1_v29-b05_vs_b03_s${SEED}.json"
  echo ""
  echo "===== Tor 1 b05 gegen b03, Seed $SEED $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$A" --spec-a "$SPEC" \
    --model-b "$B" --spec-b "$SPEC" \
    --name-a v29-b05 --name-b v29-b03 \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$SEED" --threads 10 --log-games \
    --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_tor1_b05_s${SEED}.json"
  echo "   Kennzahlen Exit $? ($(date +%H:%M:%S))"
done

echo ""
echo "== Tor 1 FERTIG $(date +%F' '%H:%M:%S)"
echo "   Faellig danach: Verdikt in par.12.1 registrieren, Netz-Gesundheit"
echo "   Punkte 1-2 (PREREG_v29_window.md par.6d), Elo-Kante nur auf Anweisung."
