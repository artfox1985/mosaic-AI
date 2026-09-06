#!/usr/bin/env bash
# Messung 3-V (PREREG_search_path_remeasurements.md, registriert 2026-09-07 01:20; Nutzer:
# "das self play zerstoert die spalten schon frueh"): drei gepaarte Sockel-Chargen desselben
# Generators, die sich NUR im Temperatur-Regler unterscheiden, danach Spalten und
# Zustandsvielfalt je Charge. Kein Training, kein Engine-Eingriff.
# Aufruf (Projektordner, Hintergrund, ohne Pipe, NUR bei freier CPU):
#   bash tools/temperature_material_compare.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
NET="models/alphazero_v24-b06_brierbest.onnx"; SPEC="models/v24-b06_brierbest.spec.json"
ART="evaluations/artifacts"; SEED=20260931; GAMES=200
# Sockel-Konfiguration der v24-Erzeugung: @100, MIT Wurzelrauschen, gesampelt, policy-aktiv.
run() {  # $1 Tag, $2 tau-argmax-from-move
  echo "== Charge $1 (tau-argmax-from-move $2) $(date +%H:%M:%S)"
  python -X utf8 -u self_play.py --mode network --model "$NET" --spec "$SPEC" \
    --games "$GAMES" --sims 100 --version "$1" --threads 11 --chunk 10 --per-file 10 \
    --seed "$SEED" --tau-argmax-from-move "$2"
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 tools/corpus_sanity_check.py data --pattern "selfplay_$1_*.pkl" --out "$ART/sanity_$1.json"
}
run tempA-tau0  0
run tempB-tau12 12
run tempC-tau30 30
echo "== Zustandsvielfalt (alle drei Chargen gegen A) $(date +%H:%M:%S)"
python -X utf8 -u tools/probes/corpus_state_diversity_probe.py \
  "data::selfplay_tempA-tau0_*.pkl" "data::selfplay_tempB-tau12_*.pkl" "data::selfplay_tempC-tau30_*.pkl" \
  --n "$GAMES" --out "$ART/state_diversity_temperature.json"
echo "== FERTIG $(date +%H:%M:%S). Registrierung: Messung 3-V durch den Koordinator."
