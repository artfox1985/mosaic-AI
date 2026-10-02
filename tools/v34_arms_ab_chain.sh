#!/usr/bin/env bash
# v34 nach den Armen (PREREG_v34_window.md par.10a, PREREG_r5_net_vs_solver.md Fortsetzung par.6f),
# alles CPU, eins nach dem anderen:
#   1. Kostentor R5-Sims 100/200/400 am Erzeugungspunkt, EXKLUSIV (wartet auch auf kein train.py),
#      dazu Determinismus-Gegenprobe gegen die Leiter (gleiche Endstaende je Partie).
#   2. Probelauf E4 gegen v34-b01 (5 Paare, 50 Sims): erstes 936er-Netz in paired_gating.
#   3. A/B E2 gegen v34-b01, Seeds 20261684/85 (+20261688 nach Stufenregel).
#   4. A/B E4 gegen v34-b01, Seeds 20261686/87 (+20261689 nach Stufenregel).
#   5. R5-A/B 400 gegen 200 am Erzeugungspunkt, Seeds 20261682/83.
# Aufruf: bash tools/v34_arms_ab_chain.sh [all|cost|arms|r5]   (Default all)
# KEINE PIPE, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
WHAT="${1:-all}"
GEN=models/alphazero_v34-b01_brierbest.onnx
B01=models/alphazero_v34-b01_brierbest.onnx
E2=models/alphazero_v34-b02_best.onnx
E4=models/alphazero_v34-b03_brierbest.onnx
SPEC=models/v33_gating_r5net.spec.json
for f in "$GEN" "$E2" "$E4" "$SPEC" models/v34_gen_r5net_sims{100,200,400}.spec.json; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
for f in "$ART"/ab_v34-b02_vs_v34-b01_s2026168[458].json "$ART"/ab_v34-b03_vs_v34-b01_s2026168[679].json \
         "$ART"/ab_gen-r5net400_vs_gen-r5net200_s2026168[23].json "$ART/r5_cost_gate_v34-b01.json"; do
  [ -f "$f" ] && { echo "ABBRUCH: $f liegt schon"; exit 4; }
done
. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
BUSY='[s]elf_play\.py|[p]aired_gating|[p]aired_arena|[f]rozen_referee|[b]uild_cache|[w]indow_train_split|[a]rgmax_profile'

block_z() {  # Block-z EINES Artefakts auf stdout
  python -X utf8 tools/gating_block_z.py --json "$1" | python -c "import sys,json; print(json.load(sys.stdin)['per_seed'][0]['z'])"
}

if [ "$WHAT" = all ] || [ "$WHAT" = cost ]; then
  BUSY_PATTERN="$BUSY|[t]rain\.py" wait_for_free_cpu "Kostentor R5 (exklusiv)"
  echo "== Kostentor R5-Sims, exklusiv $(date +%F' '%H:%M:%S)"
  mkdir -p data/probe_r5cost
  for N in 100 200 400; do
    echo ""
    echo "===== Kostentor R5-Sims $N $(date +%H:%M:%S)"
    MOSAIC_STACK_DRAW_RESEARCH=1 MOSAIC_SINGLE_PASS_OTHER_VAL=1 MOSAIC_DATA_DIR=data/probe_r5cost \
    python -X utf8 -u self_play.py --mode network --model "$GEN" \
      --spec "models/v34_gen_r5net_sims${N}.spec.json" \
      --games 100 --sims 100 --threads 11 --chunk 10 --per-file 10 --seed 20261698 \
      --version "r5sims-$N" --return-order-random-p 0.81 --tau-argmax-from-move 1 \
      --start-slot-random-p 0.15 --tie-mirror-p 0.5 --label-rng-split --excursion-reshuffle \
      --deviate-prob 1.0
    echo "   r5sims-$N Exit $? ($(date +%H:%M:%S))"
  done
  python -X utf8 -u tools/probes/r5_sims_ladder_paired.py --data-dir data/probe_r5cost \
    --stages 100 200 400 --out "$ART/r5_cost_gate_v34-b01.json"
  python -X utf8 - <<'PYEOF'
import sys
from pathlib import Path
sys.path.insert(0, "tools/probes"); sys.path.insert(0, "tools"); sys.path.insert(0, ".")
from r5_sims_ladder_paired import load_stage, final
for n in (100, 200, 400):
    a, b = load_stage(Path("data/probe_r5sims"), n), load_stage(Path("data/probe_r5cost"), n)
    keys = sorted(set(a) & set(b))
    diff = [k for k in keys if (final(a[k]) or {}).get("scores") != (final(b[k]) or {}).get("scores")]
    print(f"   Determinismus R5-Sims {n}: {len(keys)} Partien gepaart, {len(diff)} mit anderem Endstand", flush=True)
PYEOF
fi

ab() {  # $1 Name A, $2 Modell A, $3 Seed, $4 Sims, $5 Spec A, $6 Name B, $7 Modell B, $8 Spec B
  local OUT="$ART/ab_$1_vs_$6_s$3.json"
  echo ""
  echo "===== $1 gegen $6, Seed $3 $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$2" --spec-a "$5" --model-b "$7" --spec-b "$8" \
    --name-a "$1" --name-b "$6" --sims-a "$4" --sims-b "$4" --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha 1e-12 --sprt-beta 1e-12 \
    --seed "$3" --threads 10 --log-games --no-promote-winner --out "$OUT"
  local rc=$?
  echo "   Exit $rc ($(date +%H:%M:%S))"
  [ $rc -eq 0 ] || { echo "STOPP: paired_gating Exit $rc"; exit 20; }
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 --out "${OUT%.json}_plate_points.json"
}

arm() {  # $1 Name, $2 Modell, $3 Seed1, $4 Seed2, $5 Seed3
  ab "$1" "$2" "$3" 400 "$SPEC" v34-b01 "$B01" "$SPEC"
  ab "$1" "$2" "$4" 400 "$SPEC" v34-b01 "$B01" "$SPEC"
  local z1 z2
  z1=$(block_z "$ART/ab_$1_vs_v34-b01_s$3.json"); z2=$(block_z "$ART/ab_$1_vs_v34-b01_s$4.json")
  echo "   Block-z je Seed: $3 $z1, $4 $z2"
  if python -X utf8 -c "import sys; a,b=float(sys.argv[1]),float(sys.argv[2]); sys.exit(0 if (a>=1.96)!=(b>=1.96) else 1)" "$z1" "$z2"; then
    echo "   Stufenregel: genau ein Seed >= +1,96 -> dritter Seed $5"
    ab "$1" "$2" "$5" 400 "$SPEC" v34-b01 "$B01" "$SPEC"
  fi
  python -X utf8 tools/gating_block_z.py "$ART"/ab_"$1"_vs_v34-b01_s2026168?.json
}

if [ "$WHAT" = all ] || [ "$WHAT" = arms ]; then
  BUSY_PATTERN="$BUSY" wait_for_free_cpu "A/B der Arme"
  echo "== Probelauf E4 gegen v34-b01 (5 Paare, 50 Sims) $(date +%H:%M:%S)"
  SMOKE="$ART/smoke_v34-b03_paired.json"; rm -f "$SMOKE"
  python -X utf8 -u tools/paired_gating.py --model-a "$E4" --spec-a "$SPEC" --model-b "$B01" --spec-b "$SPEC" \
    --name-a v34-b03 --name-b v34-b01 --sims-a 50 --sims-b 50 --c-puct 1.5 --block-size 5 --max-pairs 5 \
    --sprt-alpha 1e-12 --sprt-beta 1e-12 --seed 1 --threads 10 --no-promote-winner --out "$SMOKE"
  rc=$?
  [ $rc -eq 0 ] || { echo "STOPP: Probelauf E4 Exit $rc"; exit 21; }
  python -X utf8 -c "import json,sys; g=json.load(open(sys.argv[1],encoding='utf-8'))['games']; ok=len(g)==10 and all(x.get('completed') for x in g); print('   Probelauf:',len(g),'Partien, alle completed' if ok else 'NICHT vollstaendig'); sys.exit(0 if ok else 22)" "$SMOKE" \
    || { echo "STOPP: Probelauf unvollstaendig"; exit 22; }
  arm v34-b02 "$E2" 20261684 20261685 20261688
  arm v34-b03 "$E4" 20261686 20261687 20261689
fi

if [ "$WHAT" = all ] || [ "$WHAT" = r5 ]; then
  # Umgebung wie 2E-b (tools/r5_selfplay_series.sh); die Arm-A/Bs oben laufen wie die Promotions-Kante ohne.
  export MOSAIC_STACK_DRAW_RESEARCH=1 MOSAIC_SINGLE_PASS_OTHER_VAL=1
  unset MOSAIC_R5_NET_SOLVER
  ab gen-r5net400 "$GEN" 20261682 100 models/v34_gen_r5net_sims400.spec.json gen-r5net200 "$GEN" models/v34_gen_r5net_sims200.spec.json
  ab gen-r5net400 "$GEN" 20261683 100 models/v34_gen_r5net_sims400.spec.json gen-r5net200 "$GEN" models/v34_gen_r5net_sims200.spec.json
  python -X utf8 tools/gating_block_z.py "$ART"/ab_gen-r5net400_vs_gen-r5net200_s2026168[23].json
fi
echo "########## v34 Arme-Kette FERTIG $(date +%F' '%H:%M:%S)"
