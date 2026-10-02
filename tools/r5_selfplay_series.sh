#!/usr/bin/env bash
# R5-Reihe fuers SELF-PLAY (PREREG_r5_net_vs_solver.md par.5b, Nutzer 2026-10-01: Sim-Frage nur fuer die
# Erzeugung). Erzeugungspunkt: Generator der naechsten Erzeugung `v34-b01`, Erzeugungs-Spec
# (models/v33_generation.spec.json plus R5-Felder), 100 Sims ausserhalb Runde 5, E1 an.
#
#   Teil 1, Sim-Leiter 2S, Instrument 1 (gepaarte Self-Play-Sonde): je R5-Sim-Stufe 100/200/400/800
#           100 Partien, Seed 20261698 wie das v34-Kostentor; bis Runde 5 identisch, misst NUR Runde 5.
#   Teil 2, Stufe 2E (A/B Kopf an Kopf): iterativer Loeser @400 Knoten gegen Netz mit R5-Sims 400,
#           Seeds 20261676/77 a 200 Paare, Blockgroesse 5, fester Umfang.
#   Teil 3, Stufe 2E-b (A/B): Netz R5-Sims 400 gegen Netz R5-Sims 100, Seeds 20261678/79.
#
# Aufruf: bash tools/r5_selfplay_series.sh [ladder|2e|2eb|all]   (Default all)
# KEINE PIPE, keine eigene Umleitung; als DATEI starten, exklusiv (CPU). Darf neben GPU-Training laufen.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
export MOSAIC_STACK_DRAW_RESEARCH=1 MOSAIC_SINGLE_PASS_OTHER_VAL=1
unset MOSAIC_R5_NET_SOLVER
ART=evaluations/artifacts
GEN=models/alphazero_v34-b01_brierbest.onnx
WHAT="${1:-all}"
[ -f "$GEN" ] || { echo "ABBRUCH: $GEN fehlt"; exit 1; }
python -X utf8 -c "import mosaic_rust,json,sys; c=json.loads(mosaic_rust.engine_config_json()); sys.exit(0 if 'r5_solver_iterative' in c else 3)" \
  || { echo "ABBRUCH: Wheel ohne R5-Felder"; exit 3; }

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
BUSY_PATTERN='[s]elf_play\.py|[p]aired_gating|[p]aired_arena|[f]rozen_referee|[b]uild_cache|[w]indow_train_split|[a]rgmax_profile' \
  wait_for_free_cpu "R5-Reihe Self-Play"
echo "== R5-Reihe Self-Play ($WHAT) $(date +%F' '%H:%M:%S)"

if [ "$WHAT" = all ] || [ "$WHAT" = ladder ]; then
  mkdir -p data/probe_r5sims
  for N in 100 200 400 800; do
    echo ""
    echo "===== Leiter R5-Sims $N $(date +%H:%M:%S)"
    MOSAIC_DATA_DIR=data/probe_r5sims python -X utf8 -u self_play.py --mode network --model "$GEN" \
      --spec "models/v34_gen_r5net_sims${N}.spec.json" \
      --games 100 --sims 100 --threads 11 --chunk 10 --per-file 10 --seed 20261698 \
      --version "r5sims-$N" --return-order-random-p 0.81 --tau-argmax-from-move 1 \
      --start-slot-random-p 0.15 --tie-mirror-p 0.5 --label-rng-split --excursion-reshuffle \
      --deviate-prob 1.0
    echo "   r5sims-$N Exit $? ($(date +%H:%M:%S))"
  done
  python -X utf8 -u tools/probes/r5_sims_ladder_paired.py --data-dir data/probe_r5sims \
    --stages 100 200 400 800 --out "$ART/r5_sims_ladder_v34-b01.json"
fi

ab() {  # $1 Name A, $2 Spec A, $3 Name B, $4 Spec B, $5.. Seeds
  local na="$1" sa="$2" nb="$3" sb="$4"; shift 4
  for S in "$@"; do
    local OUT="$ART/ab_${na}_vs_${nb}_s${S}.json"
    echo ""
    echo "===== $na gegen $nb, Seed $S $(date +%H:%M:%S)"
    python -X utf8 -u tools/paired_gating.py \
      --model-a "$GEN" --spec-a "$sa" --model-b "$GEN" --spec-b "$sb" \
      --name-a "$na" --name-b "$nb" --sims-a 100 --sims-b 100 --c-puct 1.5 \
      --block-size 5 --max-pairs 200 --sprt-alpha 1e-12 --sprt-beta 1e-12 \
      --seed "$S" --threads 10 --log-games --no-promote-winner --out "$OUT"
    echo "   Exit $? ($(date +%H:%M:%S))"
    python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 --out "${OUT%.json}_plate_points.json"
  done
}

if [ "$WHAT" = all ] || [ "$WHAT" = 2e ]; then
  ab gen-r5iter400 models/v34_gen_r5iter400.spec.json gen-r5net400 models/v34_gen_r5net_sims400.spec.json 20261676 20261677
  python -X utf8 tools/gating_block_z.py "$ART"/ab_gen-r5iter400_vs_gen-r5net400_s2026167[67].json
fi
if [ "$WHAT" = all ] || [ "$WHAT" = 2eb ]; then
  ab gen-r5net400 models/v34_gen_r5net_sims400.spec.json gen-r5net100 models/v34_gen_r5net_sims100.spec.json 20261678 20261679
  python -X utf8 tools/gating_block_z.py "$ART"/ab_gen-r5net400_vs_gen-r5net100_s2026167[89].json
fi
echo "########## R5-Reihe Self-Play FERTIG $(date +%F' '%H:%M:%S)"
