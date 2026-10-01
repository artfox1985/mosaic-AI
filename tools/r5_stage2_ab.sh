#!/usr/bin/env bash
# R5 Stufe 2 (PREREG_r5_net_vs_solver.md par.5a/par.5b, Nutzer 2026-10-01): Spiel-Betriebspunkt,
# Champion v32-b01 beidseits, A = iterativer Loeser @400 Knoten in Runde 5
# (models/v33_gating_r5iter400.spec.json), B = Netzsuche in Runde 5 @400 Sims
# (models/v33_gating_r5net.spec.json, die Referenz aus Stufe 1); sonst models/v33_gating.spec.json.
# Seeds 20261672/73 a 200 Paare, Blockgroesse 5, fester Umfang (SPRT 1e-12), --log-games.
# Laeuft parallel zum GPU-Training der v34-Kette (GPU plus EIN CPU-Auftrag, docs/working_rules.md);
# die Kette wartet vor Tor 1 auf diesen Lauf. Laufzeit darum als "neben GPU-Training" markieren.
#
# KEINE PIPE, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
CHAMP=models/alphazero_v32-b01_brierbest.onnx
SPEC_A=models/v33_gating_r5iter400.spec.json
SPEC_B=models/v33_gating_r5net.spec.json
for f in "$CHAMP" "$SPEC_A" "$SPEC_B" models/v33_gating.spec.json; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
python -X utf8 - "$SPEC_A" "$SPEC_B" <<'PYEOF' || exit 2
import json, sys
base = json.load(open("models/v33_gating.spec.json", encoding="utf-8"))
a, b = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:3])
def diff(x, y): return {k: (x.get(k), y.get(k)) for k in set(x) | set(y) if x.get(k) != y.get(k)}
assert diff(base, a) == {"r5_net_solver": (None, 1), "r5_solver_iterative": (None, 1), "r5_solver_node_budget": (None, 400)}, diff(base, a)
assert diff(base, b) == {"r5_net_solver": (None, 0)}, diff(base, b)
print("   Specs: A nur Loeser-Felder, B nur r5_net_solver 0 -- OK")
PYEOF
echo "== R5 Stufe 2: v32-b01 iterativer Loeser @400 (A) gegen Netz @400 (B) $(date +%F' '%H:%M:%S)"
for S in 20261672 20261673; do
  OUT="$ART/ab_r5iter400_v32-b01_s${S}.json"
  echo ""
  echo "===== Seed $S $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$CHAMP" --spec-a "$SPEC_A" --model-b "$CHAMP" --spec-b "$SPEC_B" \
    --name-a v32-b01-r5iter400 --name-b v32-b01-r5net \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha 1e-12 --sprt-beta 1e-12 \
    --seed "$S" --threads 10 --log-games --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "${OUT%.json}_plate_points.json"
done
python -X utf8 tools/gating_block_z.py "$ART"/ab_r5iter400_v32-b01_s2026167[23].json
echo "########## R5 Stufe 2 FERTIG $(date +%F' '%H:%M:%S)"
