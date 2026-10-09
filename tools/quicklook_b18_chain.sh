#!/usr/bin/env bash
# Schnellblick b18 (PREREG_tree_reuse.md par.3d): A = v35-b16_brierbest mit Spec v35-b18 (tree_reuse 1,
# tree_reuse_round5 1) gegen B = v35-b16_brierbest mit der Champion-Spec. Gleiches Netz, Unterschied allein
# der Suchknopf. Protokoll par.19.0 der v35-Prereg: 2 Seeds a 50 Paare @400, feste Laenge, Seeds 20261700/01,
# --log-games, --resume; danach arena_column_probe, plate_points_from_arena, gating_block_z gepoolt und die
# Lesart (spannend: gepoolt >= 55 % oder Block-z >= +1,5 -> volle Breite gegen b16, NUR nach Nutzer-Entscheid).
#
# Start (Terminal-Tab, keine Pipe, ueber die Git-Bash):   bash tools/quicklook_b18_chain.sh
set -u
cd "$(dirname "$0")/.." || exit 1
. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"

ARM=v35-b18
GEN=v35-b16
MODEL=models/alphazero_v35-b16_brierbest.onnx
A_SPEC=models/v35-b18.spec.json
B_SPEC=models/v34-b01_brierbest.spec.json
ART=evaluations/artifacts
SEEDS="20261700 20261701"
T0=$(date +%s)

for f in "$MODEL" "$A_SPEC" "$B_SPEC" tools/paired_gating.py tools/gating_block_z.py \
         tools/probes/arena_column_probe.py tools/plate_points_from_arena.py; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
python -X utf8 -c "import json,sys; s=json.load(open(sys.argv[1])); assert s.get('tree_reuse')==1 and s.get('tree_reuse_round5')==1, s; print('   Spec', sys.argv[1], 'tree_reuse', s['tree_reuse'], 'round5', s['tree_reuse_round5'])" "$A_SPEC" \
  || { echo "ABBRUCH: Spec $A_SPEC traegt nicht tree_reuse 1 / tree_reuse_round5 1"; exit 1; }

echo "########## SCHNELLBLICK $ARM (b16 + Tree Reuse) gegen $GEN   Start $(date +%F' '%H:%M:%S)"
wait_for_free_cpu "Schnellblick b18"

DONE=""
for s in $SEEDS; do
  OUT="$ART/quicklook_${ARM}_vs_${GEN}_s${s}.json"
  if [ -f "$OUT" ]; then
    echo "   $OUT liegt schon -- Seed $s uebersprungen"
  else
    echo ""
    echo "===== Schnellblick $ARM gegen $GEN, Seed $s   Start $(date +%F' '%H:%M:%S)"
    python -X utf8 -u tools/paired_gating.py \
      --model-a "$MODEL" --spec-a "$A_SPEC" --model-b "$MODEL" --spec-b "$B_SPEC" \
      --name-a "$ARM" --name-b "$GEN" \
      --sims-a 400 --sims-b 400 --c-puct 1.5 \
      --block-size 5 --max-pairs 50 --fixed-length --sprt-alpha 0.001 --sprt-beta 0.001 \
      --seed "$s" --threads 10 --log-games --no-promote-winner --out "$OUT" --resume
    echo "   Exit $? ($(date +%H:%M:%S))"
    [ -f "$OUT" ] || { echo "STOPP: kein Artefakt fuer Seed $s"; exit 2; }
  fi
  if [ ! -f "$ART/plate_points_quicklook_${ARM}_vs_${GEN}_s${s}.json" ]; then
    python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
    python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
      --out "$ART/plate_points_quicklook_${ARM}_vs_${GEN}_s${s}.json"
  fi
  DONE="$DONE $OUT"
done
echo ""
echo "== Block-z je Seed und gepoolt"
python -X utf8 tools/gating_block_z.py $DONE
python -X utf8 - $DONE <<'PY'
import json, sys
a = b = 0
for f in sys.argv[1:]:
    d = json.load(open(f, encoding="utf-8")); a += d["a_wins_total"]; b += d["b_wins_total"]
n = a + b
print(f"   gepoolt: {a}:{b} von {n} = {100*a/n:.1f} %")
PY
echo "########## SCHNELLBLICK $ARM FERTIG $(date +%F' '%H:%M:%S), $(( $(date +%s) - T0 )) s Wanduhr"
echo "   Lesart par.19.0 Punkt 4 (spannend: gepoolt >= 55 % oder Block-z >= +1,5) -> Verdikt beim Koordinator; volle Breite NUR nach Nutzer-Entscheid."
