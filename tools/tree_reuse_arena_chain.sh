#!/usr/bin/env bash
# Tree-Reuse-Arena (PREREG_tree_reuse.md par.3): A = v34-b01_brierbest mit Spec v35-b17
# (tree_reuse 1, tree_reuse_round5 1) gegen B = v34-b01_brierbest mit der Champion-Spec.
# Gleiches Netz, gleiche Spec sonst: ein Gewinn gehoert dem Knopf allein.
#
# Tor wie Tor 1 der v35-Reihe: Seeds 20261600/20261601 a 200 Paare @400, Blockgroesse 5,
# --log-games, Kriterium Block-z >= +1,96 oder gepoolt >= 52,5 % ohne Gegenbefund; Stufenregel:
# dritter Seed 20261602 nur, wenn genau EIN Seed einzeln >= +1,96 liegt.
# Je Seed danach arena_column_probe und plate_points_from_arena (sechs Standard-Kennzahlen),
# zum Schluss gating_block_z gepoolt. paired_gating.py laeuft mit --resume (Zwischenstand je Block).
#
# Start (Terminal-Tab, keine Pipe):   & "D:\Program Files\Git\bin\bash.exe" tools/tree_reuse_arena_chain.sh
# Ein liegendes Artefakt eines Seeds wird uebersprungen (Wiederaufnahme nach Abbruch).
set -u
cd "$(dirname "$0")/.." || exit 1
. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"

ARM=v35-b17
GEN=v34-b01
A_MODEL=models/alphazero_v34-b01_brierbest.onnx
A_SPEC=models/v35-b17.spec.json
B_MODEL=models/alphazero_v34-b01_brierbest.onnx
B_SPEC=models/v34-b01_brierbest.spec.json
ART=evaluations/artifacts
SEEDS="20261600 20261601"
STAGE_SEED=20261602
T_CHAIN0=$(date +%s)

for f in "$A_MODEL" "$A_SPEC" "$B_SPEC" tools/paired_gating.py tools/gating_block_z.py \
         tools/probes/arena_column_probe.py tools/plate_points_from_arena.py; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
python -X utf8 -c "import json,sys; s=json.load(open(sys.argv[1])); assert s.get('tree_reuse')==1 and s.get('tree_reuse_round5')==1, s; print('   Spec', sys.argv[1], 'tree_reuse', s['tree_reuse'], 'round5', s['tree_reuse_round5'])" "$A_SPEC" \
  || { echo "ABBRUCH: Spec $A_SPEC traegt nicht tree_reuse 1 / tree_reuse_round5 1"; exit 1; }

echo "########## TREE-REUSE-ARENA $ARM gegen $GEN   Start $(date +%F' '%H:%M:%S)"
wait_for_free_cpu "Tree-Reuse-Arena"

gate() {  # $1 Seed
  local OUT="$ART/gating_${ARM}_vs_${GEN}_s${1}.json"
  if [ -f "$OUT" ]; then
    echo "   $OUT liegt schon -- Seed $1 uebersprungen (Wiederaufnahme)"
  else
    echo ""
    echo "===== $ARM gegen $GEN, Seed $1   Start $(date +%F' '%H:%M:%S)"
    [ -f "${OUT}.partial.json" ] && echo "   Zwischenstand liegt -- --resume setzt fort"
    python -X utf8 -u tools/paired_gating.py \
      --model-a "$A_MODEL" --spec-a "$A_SPEC" --model-b "$B_MODEL" --spec-b "$B_SPEC" \
      --name-a "$ARM" --name-b "$GEN" \
      --sims-a 400 --sims-b 400 --c-puct 1.5 \
      --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
      --seed "$1" --threads 10 --log-games --no-promote-winner --out "$OUT" --resume
    echo "   Exit $? ($(date +%H:%M:%S))"
    [ -f "$OUT" ] || { echo "STOPP: kein Artefakt fuer Seed $1"; return 1; }
  fi
  if [ ! -f "$ART/plate_points_${ARM}_vs_${GEN}_s${1}.json" ]; then
    python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
    python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
      --out "$ART/plate_points_${ARM}_vs_${GEN}_s${1}.json"
  fi
  return 0
}

# Block-z eines Artefakts (letzte Zeile von gating_block_z.py: "...: Bloecke N, Mittel m, sd s, z +x.xx")
block_z() { python -X utf8 tools/gating_block_z.py "$1" | tail -1 | sed -E 's/.* z ([+-][0-9.]+).*/\1/'; }

DONE=""
for s in $SEEDS; do gate "$s" || exit 2; DONE="$DONE $ART/gating_${ARM}_vs_${GEN}_s${s}.json"; done
echo ""
echo "== Block-z je Seed und gepoolt"
python -X utf8 tools/gating_block_z.py $DONE
CLEAR=0
for f in $DONE; do z=$(block_z "$f"); python -X utf8 -c "import sys; sys.exit(0 if float(sys.argv[1])>=1.96 else 1)" "$z" && CLEAR=$((CLEAR+1)); done
echo "   Seeds einzeln >= +1,96: $CLEAR von 2"
if [ "$CLEAR" = "1" ]; then
  echo "   Stufenregel: genau ein Seed -> dritter Seed $STAGE_SEED"
  gate "$STAGE_SEED" || exit 2
  DONE="$DONE $ART/gating_${ARM}_vs_${GEN}_s${STAGE_SEED}.json"
  echo ""
  echo "== Block-z je Seed und gepoolt (drei Seeds)"
  python -X utf8 tools/gating_block_z.py $DONE
fi
echo ""
echo "########## TREE-REUSE-ARENA FERTIG $(date +%F' '%H:%M:%S), $(( $(date +%s) - T_CHAIN0 )) s Wanduhr"
echo "   Faellig: Verdikt par.3 in PREREG_tree_reuse.md (Kriterium Block-z >= +1,96 oder gepoolt >= 52,5 %),"
echo "   sechs Kennzahlen je Seite, Laufzeiten (s je Partie je Seite NICHT getrennt erhoben), Kopf Zeile 1, Index."
