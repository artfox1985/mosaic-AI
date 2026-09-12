#!/usr/bin/env bash
# PREREG_search_depth_column_optimum.md par.8e (Nutzer 2026-09-13, 00:3x: "dann also beide. wir bleiben
# am anfang grob. miss nur bei 100 sims, 200, 400 und 600"): Sims-Kurve am Generator v28-b02 in ZWEI Formen.
#   Teil A (Staerke): gepaarte Laeufe Generator@S gegen Generator@400 fuer S = 100, 200, 600, dasselbe
#          ONNX und dieselbe Champion-Spec beidseitig, 75 Paare, Frueh-Stopp AUS (alpha=beta=1e-12),
#          Bloecke zu 5, Logs; danach je Punkt Spaltensonde und Plattenpunkte je Kriterium.
#   Teil B (Korpus): argmax-Instrument wie par.8b (deterministisch, ohne Wurzelrauschen,
#          MOSAIC_STACK_DRAW_RESEARCH=1, Seed 20260931, 200 Partien) bei S = 100, 200, 400, 600.
# Aufruf (Projektordner, Hintergrundaufgabe, keine Pipe, EXKLUSIV): bash tools/night_sims_curve_v28b02.sh
# Die Self-Play-Dateien von Teil B landen in data/ (selfplay_depth<S>-v28b02_*.pkl) und gehoeren VOR dem
# v29-Fensterbau auf die Ausschluss- oder Loeschliste (PREREG_v29_window.md, Fenster-Pinning).
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
NET=models/alphazero_v28-b02_brierbest.onnx        # sha256 1cc296ee..., identisch mit frozen_champions/v28-b02/model.onnx
SPEC=models/frozen_champions/v28-b02/spec.json
[ -f "$NET" ] || { echo "STOPP: $NET fehlt"; exit 12; }
[ -f "$SPEC" ] || { echo "STOPP: $SPEC fehlt"; exit 12; }

paired_point() {  # $1 Sims A, $2 Seed, $3 Artefaktname
  local S=$1 SEED=$2 OUT=$3
  echo "== TEIL A Punkt @$S gegen @400 (paired_gating, Frueh-Stopp AUS, 75 Paare, Seed $SEED) $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py --model-a "$NET" --model-b "$NET" --spec-a "$SPEC" --spec-b "$SPEC" \
    --name-a "v28-b02_s$S" --name-b v28-b02 --sims-a "$S" --sims-b 400 --c-puct 1.5 --block-size 5 \
    --max-pairs 75 --sprt-alpha 1e-12 --sprt-beta 1e-12 --seed "$SEED" --threads 10 --log-games \
    --no-promote-winner --out "$ART/$OUT.json"
  echo "   Exit $? ($(date +%H:%M:%S))"
  echo "== Spaltensonde @$S $(date +%H:%M:%S)"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$ART/$OUT.json"
  echo "   Exit $? ($(date +%H:%M:%S))"
  echo "== Plattenpunkte je Kriterium @$S $(date +%H:%M:%S)"
  python -X utf8 -u tools/plate_points_from_arena.py "$ART/$OUT.json"
  echo "   Exit $? ($(date +%H:%M:%S))"
}
argmax_point() {  # $1 Sims
  local S=$1 TAG="depth${1}-v28b02"
  echo "== TEIL B Punkt @$S (argmax, 200 Partien, Seed 20260931) $(date +%F' '%H:%M:%S)"
  MOSAIC_STACK_DRAW_RESEARCH=1 python -X utf8 -u self_play.py --mode network --model "$NET" --spec "$SPEC" \
    --games 200 --sims "$S" --version "$TAG" --threads 11 --chunk 10 --per-file 10 \
    --seed 20260931 --no-root-noise --deterministic
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 tools/corpus_sanity_check.py data --pattern "selfplay_${TAG}_*.pkl" --out "$ART/depth_curve_${S}_v28b02.json"
  echo "   Sanity Exit $? ($(date +%H:%M:%S))"
}

echo "== SIMS-KURVE v28-b02 START $(date +%F' '%H:%M:%S)"
paired_point 100 20261055 paired_gating_v28-b02_s100_vs_s400_seed55_full
paired_point 200 20261056 paired_gating_v28-b02_s200_vs_s400_seed56_full
paired_point 600 20261057 paired_gating_v28-b02_s600_vs_s400_seed57_full
argmax_point 100
argmax_point 200
argmax_point 400
argmax_point 600
echo "== SIMS-KURVE FERTIG $(date +%F' '%H:%M:%S). Registrierung par.8e durch den Koordinator."
