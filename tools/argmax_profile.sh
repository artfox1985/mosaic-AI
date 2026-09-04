#!/bin/bash
# argmax-Instrument (Tor 2a, docs/generation_loop.md): 200 Partien @400, Seed 20260931, deterministisch,
# mit MOSAIC_STACK_DRAW_RESEARCH=1 (Konvention seit v23); Env-Knoepfe als Argumente ENV=WERT.
# Aufruf (aus dem Projektordner): bash tools/argmax_profile.sh <tag> <modell.onnx> [ENV=WERT ...]
# Ergebnis: data/selfplay_<tag>_*.pkl, Manifest, evaluations/artifacts/<tag mit _>.json (corpus_sanity_check).
set -euo pipefail
cd "$(dirname "$0")/.."
TAG=$1; MODEL=$2; shift 2
export MOSAIC_STACK_DRAW_RESEARCH=1
for kv in "$@"; do export "$kv"; done
python -X utf8 -u self_play.py --mode network --model "$MODEL" --games 200 --sims 400 --version "$TAG" --threads 11 --chunk 10 --seed 20260931 --per-file 10 --no-root-noise --deterministic
python -X utf8 tools/corpus_sanity_check.py data --pattern "selfplay_${TAG}_*.pkl" --out "evaluations/artifacts/${TAG//-/_}.json"
