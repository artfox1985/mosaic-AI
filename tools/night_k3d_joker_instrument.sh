#!/usr/bin/env bash
# K3-D und Jokerfeld-Regel am argmax-Instrument (Nutzer 2026-09-12: "takte 1 und 2 nach der
# hv2-Gegenprobe ein"; PREREG_geometric_envelope.md par.13 Nachtrag). Beide Knoepfe hatten bis
# dahin keine Arena-Messung, nur die Orakel-Bruecke gegen ein huellenblindes Orakel.
# Instrument wie C2 (tools/night_v28_measure.sh): v28-b02, 200 Partien @400, Seed 20260931,
# deterministisch, ohne Wurzelrauschen, MOSAIC_STACK_DRAW_RESEARCH=1, corpus_sanity_check.
# Bezug ist der vorhandene Lauf c2-v28b02-on (Champion-Spec, gleicher Seed, Artefakt
# evaluations/artifacts/c2_v28b02_on.json). Zielgroessen: Jokerfeld -> Punkte Kriterium k3
# ("Mehrfarbige Felder", scoring.rs id 3) und volle Spalten als Waechter; K3-D -> volle Spalten
# und Teilspalten >= 3. Exklusiv, nacheinander.
# Aufruf: bash tools/night_k3d_joker_instrument.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
export MOSAIC_STACK_DRAW_RESEARCH=1
ART=evaluations/artifacts
for PAIR in "jokerfeld:models/out_wild_on.spec.json" "k3d:models/k3d_on.spec.json"; do
  TAG=${PAIR%%:*}; SPEC=${PAIR#*:}
  RUN="c2-v28b02-${TAG}"
  echo "== argmax-Instrument $RUN (Spec $SPEC) $(date +%F' '%H:%M:%S)"
  python -X utf8 -u self_play.py --mode network --model models/alphazero_v28-b02_brierbest.onnx \
    --spec "$SPEC" --games 200 --sims 400 --version "$RUN" --threads 11 --chunk 10 \
    --seed 20260931 --per-file 10 --no-root-noise --deterministic
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 tools/corpus_sanity_check.py data --pattern "selfplay_${RUN}_*.pkl" --out "$ART/${RUN//-/_}.json"
  echo "   sanity Exit $? ($(date +%H:%M:%S))"
done
echo "== K3-D/JOKERFELD-INSTRUMENT FERTIG $(date +%F' '%H:%M:%S)"
