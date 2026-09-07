#!/usr/bin/env bash
# PREREG_search_depth_column_optimum.md par.8 (registriert 2026-09-07 02:05, Nutzer-Freigabe):
# drei Punkte der Suchtiefen-Kurve am AKTUELLEN Champion neu messen. Die Bestandskurve
# (par.2i) stammt von v22-b05, drei Generationen alt; der Effekt haengt am Prior (par.2l).
# Konfiguration wie das Tor-2a-Instrument (argmax_profile.sh), nur die Sims variieren.
# Aufruf (Projektordner, Hintergrund, ohne Pipe, NUR bei freier CPU):
#   bash tools/depth_curve_recheck.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
NET="models/alphazero_v24-b06_brierbest.onnx"; SPEC="models/v24-b06_brierbest.spec.json"
ART="evaluations/artifacts"; SEED=20260931
export MOSAIC_STACK_DRAW_RESEARCH=1
run() {  # $1 Sims
  local tag="depth${1}-v24b06"
  echo "== Punkt @$1 Sims $(date +%H:%M:%S)"
  python -X utf8 -u self_play.py --mode network --model "$NET" --spec "$SPEC" \
    --games 200 --sims "$1" --version "$tag" --threads 11 --chunk 10 --per-file 10 \
    --seed "$SEED" --no-root-noise --deterministic
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 tools/corpus_sanity_check.py data --pattern "selfplay_${tag}_*.pkl" --out "$ART/depth_curve_${1}_v24b06.json"
}
run 100
run 250
run 400
echo "== FERTIG $(date +%H:%M:%S). Registrierung par.8 durch den Koordinator."
