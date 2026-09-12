#!/usr/bin/env bash
# Treppe zwischen Anker (1000) und v22-b05@400 festigen (Nutzer 2026-09-13, 00:10: "ja wirf sie an").
# Alle Kanten bis zum Deckel OHNE Frueh-Stopp, damit jeder Treppen-Knoten mindestens zwei Kanten am
# Deckel hat: (1) hv4@600 gegen v22@100 und gegen v22@400 (Referee, 3 Bloecke a 50); (2) die zwei
# frueh gestoppten Netz-Sims-Kanten der Treppe als gepaarte Laeufe mit Frueh-Stopp aus
# (alpha=beta=1e-12, 75 Paare = 150 Partien): v22@25 gegen @100 (neuer Seed) und v22@100 gegen @400.
# Aufruf: bash tools/night_ladder_gap_fill.sh   (Hintergrundaufgabe, keine Pipe, exklusiv)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
ANCHOR=models/frozen_heuristics/hv4_anchor
M22=models/restored_v22/alphazero_v22-b05.onnx
S22=models/k3v_off.spec.json
HEUR600="--sims-worker 600 --c-puct-worker 0.3"
[ -f "$M22" ] || { echo "STOPP: $M22 fehlt"; exit 12; }
edge_full() {
  local TAG=$1; local SEED=$2; shift 2
  local BLOCK=0
  for OFF in 0 50 100; do
    BLOCK=$((BLOCK+1))
    echo "== KANTE $TAG Block $BLOCK (Seed-Basis $((SEED+OFF))) $(date +%F' '%H:%M:%S)"
    python -X utf8 -u tools/frozen_referee_match.py "$@" --n-games 50 --seed-base $((SEED+OFF)) \
      --workers 6 --force-cross-era --out "$ART/rung_${TAG}_b${BLOCK}.json"
    echo "   Exit $? ($(date +%H:%M:%S))"
  done
  python -X utf8 - "$ART" "$TAG" <<'PY'
import json, sys, math, pathlib
art, tag = pathlib.Path(sys.argv[1]), sys.argv[2]
wa = wb = 0
for b in (1, 2, 3):
    d = json.loads((art / f"rung_{tag}_b{b}.json").read_text(encoding="utf-8"))
    wa += d["wins_a"]; wb += d["wins_b"]
n = wa + wb; k = min(wa, wb)
p = min(1.0, 2 * sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n) if n else 1.0
print(f"   gepoolt {tag}: {wa}:{wb} aus {n}, Binomial zweiseitig p={p:.4f} (Deckel, kein Frueh-Stopp)", flush=True)
PY
}
paired_full() {
  local OUT=$1; local SEED=$2; shift 2
  echo "== KANTE $OUT (paired_gating, Frueh-Stopp AUS, 75 Paare) $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py --model-a "$M22" --model-b "$M22" --spec-a "$S22" --spec-b "$S22" \
    "$@" --c-puct 1.5 --block-size 5 --max-pairs 75 --sprt-alpha 1e-12 --sprt-beta 1e-12 \
    --seed "$SEED" --threads 10 --log-games --no-promote-winner --out "$ART/$OUT.json"
  echo "   Exit $? ($(date +%H:%M:%S))"
}
echo "== TREPPE START $(date +%F' '%H:%M:%S)"
edge_full v22b05s100_vs_hv4s600 933001 --artifact-dir "$ANCHOR" $HEUR600 --model-a "$M22" --spec-a "$S22" --sims-a 100 --c-puct-a 1.5
edge_full v22b05s400_vs_hv4s600 934001 --artifact-dir "$ANCHOR" $HEUR600 --model-a "$M22" --spec-a "$S22" --sims-a 400 --c-puct-a 1.5
paired_full paired_gating_v22-b05_s25_vs_s100_seed53_full 20261053 --name-a v22-b05_live_s25 --name-b v22-b05_live_s100 --sims-a 25 --sims-b 100
paired_full paired_gating_v22-b05_s100_vs_s400_seed54_full 20261054 --name-a v22-b05_live_s100 --name-b v22-b05_live --sims-a 100 --sims-b 400
echo "== TREPPE FERTIG $(date +%F' '%H:%M:%S)"
