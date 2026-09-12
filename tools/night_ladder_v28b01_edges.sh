#!/usr/bin/env bash
# Zwei Kanten fuer v28-b01, das im Segment 2 nur an der gesaettigten Anker-Kante haengt
# (Nutzer 2026-09-12, 17:50: "v26 und v21"): v28-b01 (lebendes Modell, Champion-Spec) gegen die
# Artefakte v26-b01 und v21_2d_brierbest, Bloecke zu 50 mit Frueh-Stopp (Binomial p < 0,05),
# spaetestens 150. Exklusiv, nach dem Such-Start-A/B.
# Aufruf: bash tools/night_ladder_v28b01_edges.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
V26=models/frozen_champions/v26-b01
V21=models/frozen_champions/v21_2d_brierbest
SPEC=models/frozen_champions/v27-b01/spec.json
NETW="--sims-worker 400 --c-puct-worker 1.5"
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
echo "== V28-B01-KANTEN START $(date +%F' '%H:%M:%S)"
edge v28b01_vs_v26 922001 --artifact-dir "$V26" $NETW --model-a models/alphazero_v28-b01_brierbest.onnx --spec-a "$SPEC" --sims-a 400 --c-puct-a 1.5
edge v28b01_vs_v21 923001 --artifact-dir "$V21" $NETW --model-a models/alphazero_v28-b01_brierbest.onnx --spec-a "$SPEC" --sims-a 400 --c-puct-a 1.5
echo "== V28-B01-KANTEN FERTIG $(date +%F' '%H:%M:%S)"
