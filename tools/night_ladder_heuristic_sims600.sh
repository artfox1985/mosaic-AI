#!/usr/bin/env bash
# Sprossen-Kandidat "Heuristik mit mehr Sims" (Nutzer 2026-09-12, 23:52: "dann als mehr sims bei der
# heuristik probieren"; Vorschlag aus PREREG_code_cleanup_closeout.md par.7a: ein Knoten, der gegen die
# Heuristiken bei 55-70 Prozent liegt, nachdem die Netz-Sims-Achse (400/100/25) nur bis 70 Prozent
# kam). Knoten "Heuristik_hv4_anchor@600": das Anker-ARTEFAKT selbst mit 600 statt 150 Sims, c_puct
# 0,3 wie der Anker. Kanten: gegen den Anker @150 (Artefakt gegen dasselbe Artefakt, nur Sims
# verschieden) und nach oben gegen v22-b05@25 (LIVE-ONNX, k3v_off), das schwaechste Netz der Leiter.
# Bloecke zu 50 mit Frueh-Stopp (Binomial zweiseitig p<0,05), Deckel 150.
# Aufruf: bash tools/night_ladder_heuristic_sims600.sh   (Hintergrundaufgabe, keine Pipe, exklusiv)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
ANCHOR=models/frozen_heuristics/hv4_anchor
M22=models/restored_v22/alphazero_v22-b05.onnx
S22=models/k3v_off.spec.json
HEUR150="--sims-worker 150 --c-puct-worker 0.3"
HEUR600="--sims-worker 600 --c-puct-worker 0.3"
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
echo "== HEURISTIK@600-SPROSSEN START $(date +%F' '%H:%M:%S)"
edge hv4s600_vs_anchor    931001 --artifact-dir "$ANCHOR" $HEUR150 --artifact-dir-a "$ANCHOR" --sims-a 600 --c-puct-a 0.3
edge v22b05s25_vs_hv4s600 932001 --artifact-dir "$ANCHOR" $HEUR600 --model-a "$M22" --spec-a "$S22" --sims-a 25 --c-puct-a 1.5
echo "== HEURISTIK@600-SPROSSEN FERTIG $(date +%F' '%H:%M:%S)"
