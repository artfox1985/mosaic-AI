#!/usr/bin/env bash
# Promotions-Kante v34 (PREREG_v34_window.md par.2a, Nutzer 2026-10-01): v34-b01 mit Runde 5 per Netz
# gegen den Champion v32-b01, wie er heute spielt (eingefrorene Spec). Ersetzt Schritt 6-7 von
# tools/night_v34_chain.sh fuer v34. Zwei Seeds a 200 Paare, Stufenregel wie Tor 1.
#
# KEINE PIPE, keine eigene Umleitung; als DATEI starten, exklusiv.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
ARM=v34-b01
A=models/alphazero_v34-b01_brierbest.onnx
SPEC_A=models/v33_gating_r5net.spec.json
CHAMP=v32-b01
B=models/alphazero_v32-b01_brierbest.onnx
SPEC_B=models/frozen_champions/v32-b01/spec.json
for f in "$A" "$SPEC_A" "$B" "$SPEC_B"; do [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }; done
cmp -s "$SPEC_B" models/v32-b01_brierbest.spec.json || echo "HINWEIS: Champion-Spec weicht von models/v32-b01_brierbest.spec.json ab"

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
wait_for_free_cpu "v34-Promotions-Kante"
echo "== v34-Promotions-Kante: $ARM ($SPEC_A) gegen $CHAMP ($SPEC_B) $(date +%F' '%H:%M:%S)"

gate() {  # $1 Seed
  local OUT="$ART/promotion_${ARM}_vs_${CHAMP}_s${1}.json"
  echo ""
  echo "===== Seed $1 $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$A" --spec-a "$SPEC_A" --model-b "$B" --spec-b "$SPEC_B" \
    --name-a "${ARM}-r5net" --name-b "$CHAMP" \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$1" --threads 10 --log-games --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_promotion_${ARM}_vs_${CHAMP}_s${1}.json"
}

for S in 20261600 20261601; do gate "$S"; done
P="$ART/promotion_${ARM}_vs_${CHAMP}_s"
python -X utf8 tools/gating_block_z.py "${P}20261600.json" "${P}20261601.json"
N_SIG=$(python -X utf8 tools/gating_block_z.py --json "${P}20261600.json" "${P}20261601.json" \
  | python -c "import sys,json; d=json.load(sys.stdin); print(sum(r['z'] >= 1.96 for r in d['per_seed']))")
echo "   Seeds einzeln >= +1,96: ${N_SIG:-?} von 2"
if [ "$N_SIG" = "1" ]; then
  echo "   -> Widerspruch: dritter Seed 20261602 (Stufenregel)"
  gate 20261602
  python -X utf8 tools/gating_block_z.py "${P}"2026160[012].json
elif [ -z "$N_SIG" ]; then
  echo "   STOPP: Block-z nicht berechenbar -- Stufenregel von Hand anwenden"
fi
echo "########## v34-Promotions-Kante FERTIG $(date +%F' '%H:%M:%S)"
