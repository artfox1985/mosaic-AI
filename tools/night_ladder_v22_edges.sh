#!/usr/bin/env bash
# Sprosse v22-b05 in der Luecke 1000-1157 der Segment-2-Leiter (Nutzer 2026-09-12: "was ist mit
# v22 und v23"). v22-b05 (Segment 1: 1084, verlor 16:34 gegen v21) liegt im Backup nur als ONNX
# (Snapshot f567ad7d, models/restored_v22/alphazero_v22-b05.onnx, 744 Merkmale), kein Artefakt:
# spielt LIVE auf dem heutigen Wheel (Kuerzung auf Modellbreite, wie die Ueberraschungs-Kante) mit
# models/k3v_off.spec.json (Fassung ohne Huelle, wie zur v22-Zeit). Kanten: gegen v21 (Artefakt),
# gegen Anker, gegen hv2; Bloecke zu 50 mit Frueh-Stopp. Cross-Aera, Knoten heisst "v22-b05_live".
# Aufruf: bash tools/night_ladder_v22_edges.sh   (Hintergrundaufgabe, keine Pipe, exklusiv)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
ANCHOR=models/frozen_heuristics/hv1_anchor_v2
HV2=models/frozen_heuristics/hv2_generator
V21=models/frozen_champions/v21_2d_brierbest
M22=models/restored_v22/alphazero_v22-b05.onnx
S22=models/k3v_off.spec.json
HEUR="--sims-worker 150 --c-puct-worker 0.3"
NETW="--sims-worker 400 --c-puct-worker 1.5"
[ -f "$M22" ] || { echo "STOPP: $M22 fehlt"; exit 12; }
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
echo "== V22-SPROSSEN START $(date +%F' '%H:%M:%S)"
edge v22b05_vs_v21    919001 --artifact-dir "$V21" $NETW --model-a "$M22" --spec-a "$S22" --sims-a 400 --c-puct-a 1.5
edge v22b05_vs_anchor 920001 --artifact-dir "$ANCHOR" $HEUR --model-a "$M22" --spec-a "$S22" --sims-a 400 --c-puct-a 1.5
edge v22b05_vs_hv2    921001 --artifact-dir "$HV2" $HEUR --model-a "$M22" --spec-a "$S22" --sims-a 400 --c-puct-a 1.5
echo "== V22-SPROSSEN FERTIG $(date +%F' '%H:%M:%S)"
