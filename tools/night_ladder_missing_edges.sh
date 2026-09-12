#!/usr/bin/env bash
# Nachlauf 2026-09-12: die Kanten, die vor dem Worker-Patch (13:37, start_placement mit drei
# Argumenten) gescheitert sind: drei Anker-Kanten (festes n=150) und hv2 gegen Anker (Bloecke mit
# Frueh-Stopp). Exklusiv, nach dem Ende der laufenden Kette.
# Aufruf: bash tools/night_ladder_missing_edges.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
ANCHOR=models/frozen_heuristics/hv1_anchor_v2
HV2=models/frozen_heuristics/hv2_generator
SPEC=models/frozen_champions/v27-b01/spec.json
HEUR="--sims-worker 150 --c-puct-worker 0.3"
echo "== TEIL A: Anker-Kanten korrekt (n=150 fest, Anker @150 c_puct 0,3) $(date +%F' '%H:%M:%S)"
for CAND in v28-b02 v28-b01 v27-b01; do
  echo "== ANKER-KANTE $CAND@400 gegen hv1_anchor_v2@150 $(date +%H:%M:%S)"
  python -X utf8 -u tools/frozen_referee_match.py --artifact-dir "$ANCHOR" \
    --model-a "models/alphazero_${CAND}_brierbest.onnx" --spec-a "$SPEC" --sims-a 400 --c-puct-a 1.5 $HEUR \
    --n-games 150 --seed-base 900001 --workers 6 --out "$ART/anchor_v2_arena_${CAND}_c03.json"
  echo "   Exit $? ($(date +%H:%M:%S))"
done
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
edge hv2_vs_anchor 910001 --artifact-dir "$ANCHOR" $HEUR --artifact-dir-a "$HV2" --sims-a 150 --c-puct-a 0.3
echo "== FEHLENDE KANTEN FERTIG $(date +%F' '%H:%M:%S)"
