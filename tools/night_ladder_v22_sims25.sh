#!/usr/bin/env bash
# Sprosse v22-b05@25 (Nutzer 2026-09-12, 23:40: "Netz@25 -- ja probier das auch mal mit fruehstop";
# Vorschlag aus PREREG_code_cleanup_closeout.md par.7a: ein Knoten, der gegen die Heuristiken bei
# 55-70 Prozent liegt). Kanten: v22-b05@25 gegen hv4 und hv3 (Referee, Bloecke zu 50, Frueh-Stopp
# Binomial p<0,05, Deckel 150) und nach oben gegen v22-b05@100 (paired_gating, SPRT, Deckel 75 Paare).
# Wartet vorab, bis die Kante v28-b02@100 gegen @400 (seed51) ihr Artefakt geschrieben hat.
# Aufruf: bash tools/night_ladder_v22_sims25.sh   (Hintergrundaufgabe, keine Pipe, exklusiv)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
ANCHOR=models/frozen_heuristics/hv4_anchor
HV3=models/frozen_heuristics/hv3_generator
V21=models/frozen_champions/v21_2d_brierbest
M22=models/restored_v22/alphazero_v22-b05.onnx
S22=models/k3v_off.spec.json
HEUR="--sims-worker 150 --c-puct-worker 0.3"
NETW="--sims-worker 400 --c-puct-worker 1.5"
[ -f "$M22" ] || { echo "STOPP: $M22 fehlt"; exit 12; }
[ -d "$HV3" ] || { echo "STOPP: $HV3 fehlt"; exit 12; }
while [ ! -f "$ART/paired_gating_v28-b02_s100_vs_s400_seed51.json" ]; do sleep 20; done
while tasklist 2>/dev/null | grep -qi "cargo.exe"; do sleep 15; done
echo "== Vorlauf frei $(date +%H:%M:%S)"
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
echo "== V22@25-SPROSSEN START $(date +%F' '%H:%M:%S)"
edge v22b05s25_vs_anchor 929001 --artifact-dir "$ANCHOR" $HEUR --model-a "$M22" --spec-a "$S22" --sims-a 25 --c-puct-a 1.5
edge v22b05s25_vs_hv3    930001 --artifact-dir "$HV3"    $HEUR --model-a "$M22" --spec-a "$S22" --sims-a 25 --c-puct-a 1.5
echo "== KANTE v22b05s25_vs_v22b05s100 (paired_gating, SPRT, Deckel 75 Paare) $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/paired_gating.py --model-a "$M22" --model-b "$M22" --spec-a "$S22" --spec-b "$S22" \
  --name-a v22-b05_live_s25 --name-b v22-b05_live_s100 --sims-a 25 --sims-b 100 --c-puct 1.5 \
  --block-size 5 --max-pairs 75 --seed 20261052 --threads 10 --log-games --no-promote-winner \
  --out "$ART/paired_gating_v22-b05_s25_vs_s100_seed52.json"
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== V22@25-SPROSSEN FERTIG $(date +%F' '%H:%M:%S)"
