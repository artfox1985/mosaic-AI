#!/usr/bin/env bash
# v21-Sprossen der Elo-Leiter (Nachlauf zu tools/night_ladder_rungs2.sh, 2026-09-12): der
# Selbsttest dort scheiterte an den zwei Echtpartien, weil der Referee die v21-Spec (ein Feld) fuer
# eine IN-PROCESS-Seite strikt parst; der Golden-Selbsttest mit dem Worker des Einfriertags war
# 10/10 gruen. In den Kanten spielt v21 nur als Artefakt-Worker, dort wird die Spec nicht vom
# lebenden Wheel gelesen. Drei Kanten in Bloecken zu 50 mit Frueh-Stopp (wie rungs2).
# Aufruf: bash tools/night_ladder_v21_edges.sh   (Hintergrundaufgabe, keine Pipe, exklusiv)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
ANCHOR=models/frozen_heuristics/hv1_anchor_v2
HV2=models/frozen_heuristics/hv2_generator
V21=models/frozen_champions/v21_2d_brierbest
V24=models/frozen_champions/v24-b07
HEUR="--sims-worker 150 --c-puct-worker 0.3"
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
echo "== V21-SPROSSEN START $(date +%F' '%H:%M:%S)"
edge v21_vs_hv2      911001 --artifact-dir "$HV2" $HEUR --artifact-dir-a "$V21" --sims-a 400 --c-puct-a 1.5
edge v24_vs_v21      912001 --artifact-dir "$V21" $NETW --artifact-dir-a "$V24" --sims-a 400 --c-puct-a 1.5
edge v21_vs_anchor   916001 --artifact-dir "$ANCHOR" $HEUR --artifact-dir-a "$V21" --sims-a 400 --c-puct-a 1.5
echo "== V21-SPROSSEN FERTIG $(date +%F' '%H:%M:%S)"
