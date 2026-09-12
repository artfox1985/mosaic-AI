#!/usr/bin/env bash
# Elo-Leiter Segment 2: Anker-Kanten KORREKT wiederholen und Zwischenstufen einziehen (2026-09-12).
# Anlass 1: tools/night_reanchor.sh rief den Referee ohne --sims-worker 150 --c-puct-worker 0.3 auf;
#   der Anker spielte @400/c_puct 1,5 statt der Leiterdefinition @150/0,3 (tools/anchor_arena.py).
#   Die drei Zeilen liegen in archive/elo_history_segment2_anchor_mislabelled.csv.
# Anlass 2 (Nutzer): die Anker-Kanten sind gesaettigt (84-88 %), die Leiter braucht Zwischenstufen.
# Teil A: drei Anker-Kanten, festes n=150 (Leiterdefinition, kein Frueh-Stopp), Seed-Basis 900001.
# Teil B: Zwischenstufen in Bloecken zu 50 mit Frueh-Stopp (zweiseitiger Binomialtest der
#   gepoolten Bloecke p < 0,05; Nutzer: kein Champion-Tor), spaetestens 150: hv2@150 gegen Anker,
#   v24-b07@400 (live, eigene Spec) gegen hv2 und gegen Anker, v26-b01 (Artefakt) gegen hv2 und Anker,
#   v27-b01 und v28-b02 gegen hv2. Heuristik-Seiten immer @150 mit c_puct 0,3, Netze @400 mit 1,5.
# Cross-Aera-Handshakes per --force-cross-era. Exklusiv, nach tools/night_v28_tail.sh.
# Aufruf: bash tools/night_ladder_rungs.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
ANCHOR=models/frozen_heuristics/hv1_anchor_v2
HV2=models/frozen_heuristics/hv2_generator
V26=models/frozen_champions/v26-b01
SPEC=models/frozen_champions/v27-b01/spec.json
SPEC24=models/v24-b07_brierbest.spec.json
HEUR="--sims-worker 150 --c-puct-worker 0.3"

echo "== TEIL A: Anker-Kanten korrekt (n=150 fest, Anker @150 c_puct 0,3) $(date +%F' '%H:%M:%S)"
for CAND in v28-b02 v28-b01 v27-b01; do
  echo "== ANKER-KANTE $CAND@400 gegen hv1_anchor_v2@150 $(date +%H:%M:%S)"
  python -X utf8 -u tools/frozen_referee_match.py --artifact-dir "$ANCHOR" \
    --model-a "models/alphazero_${CAND}_brierbest.onnx" --spec-a "$SPEC" --sims-a 400 --c-puct-a 1.5 $HEUR \
    --n-games 150 --seed-base 900001 --workers 6 --out "$ART/anchor_v2_arena_${CAND}_c03.json"
  echo "   Exit $? ($(date +%H:%M:%S))"
done

# edge <tag> <seed-base> <referee-args...>: Bloecke zu 50 mit Seed-Basis +0/+50/+100, Frueh-Stopp
edge() {
  local TAG=$1; local SEED=$2; shift 2
  local BLOCK=0
  for OFF in 0 50 100; do
    BLOCK=$((BLOCK+1))
    echo "== KANTE $TAG Block $BLOCK (Seed-Basis $((SEED+OFF))) $(date +%F' '%H:%M:%S)"
    python -X utf8 -u tools/frozen_referee_match.py "$@" --n-games 50 --seed-base $((SEED+OFF)) \
      --workers 6 --force-cross-era --out "$ART/rung_${TAG}_b${BLOCK}.json"
    echo "   Exit $? ($(date +%H:%M:%S))"
    python -X utf8 - "$ART" "$TAG" $BLOCK <<'PY'
import json, sys, math, pathlib
art, tag, nb = pathlib.Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])
wa = wb = 0
for b in range(1, nb + 1):
    d = json.loads((art / f"rung_{tag}_b{b}.json").read_text(encoding="utf-8"))
    wa += d["wins_a"]; wb += d["wins_b"]
n = wa + wb
k = min(wa, wb)
p = min(1.0, 2 * sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n) if n else 1.0
print(f"   gepoolt {tag}: {wa}:{wb} aus {n}, Binomial zweiseitig p={p:.4f}", flush=True)
sys.exit(0 if p < 0.05 else 3)
PY
    if [ $? -eq 0 ]; then echo "   Frueh-Stopp nach Block $BLOCK"; break; fi
  done
}

echo "== TEIL B: Zwischenstufen $(date +%F' '%H:%M:%S)"
edge hv2_vs_anchor   910001 --artifact-dir "$ANCHOR" $HEUR --artifact-dir-a "$HV2" --sims-a 150 --c-puct-a 0.3
edge v24b07_vs_hv2   911001 --artifact-dir "$HV2" $HEUR --model-a models/alphazero_v24-b07_brierbest.onnx --spec-a "$SPEC24" --sims-a 400 --c-puct-a 1.5
edge v24b07_vs_anchor 912001 --artifact-dir "$ANCHOR" $HEUR --model-a models/alphazero_v24-b07_brierbest.onnx --spec-a "$SPEC24" --sims-a 400 --c-puct-a 1.5
edge v26_vs_hv2      913001 --artifact-dir "$HV2" $HEUR --artifact-dir-a "$V26" --sims-a 400 --c-puct-a 1.5
edge v26_vs_anchor   914001 --artifact-dir "$ANCHOR" $HEUR --artifact-dir-a "$V26" --sims-a 400 --c-puct-a 1.5
edge v27_vs_hv2      915001 --artifact-dir "$HV2" $HEUR --model-a models/alphazero_v27-b01_brierbest.onnx --spec-a "$SPEC" --sims-a 400 --c-puct-a 1.5
edge v28b02_vs_hv2   916001 --artifact-dir "$HV2" $HEUR --model-a models/alphazero_v28-b02_brierbest.onnx --spec-a "$SPEC" --sims-a 400 --c-puct-a 1.5
echo "== ANKER-KANTEN UND ZWISCHENSTUFEN FERTIG $(date +%F' '%H:%M:%S)"
