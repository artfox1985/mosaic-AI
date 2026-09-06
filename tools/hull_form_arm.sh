#!/usr/bin/env bash
# par.8.15 Teil B: Arm "Huellenform 2" (Dreieck plus zweite Zelle der Zeile 6) gegen die
# Champion-Spec (Form 1) am selben Netz -- gleiche Bauform wie die vier K3-Arme
# (tools/night_k3_knobs_b06.sh): argmax-Instrument @400 gegen Bezug 0,4975 und gepaarte
# Arena 2 x 80 mit Logs, dazu Spalten-, Punkte- und Reihen-Alter-Sonde.
# Aufruf (Projektordner, Hintergrund, ohne Pipe, NUR bei freier CPU):  bash tools/hull_form_arm.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
NET="models/alphazero_v24-b06_brierbest.onnx"; CHAMP="models/v24-b06_brierbest.spec.json"; ART="evaluations/artifacts"
SPEC="models/hullform2.spec.json"; TAG="hull2"
echo "== Arm $TAG: argmax-Instrument @400 $(date +%H:%M:%S)"
bash tools/argmax_profile.sh "k3-${TAG}-v24b06" "$NET" MOSAIC_ENVELOPE_PROJECTED=1 MOSAIC_ENVELOPE_SEARCH_C=1.0 MOSAIC_ENVELOPE_HULL_FORM=2; echo "   Exit $?"
echo "== Arm $TAG: gepaarte Arena Arm-Spec gegen Champion-Spec $(date +%H:%M:%S)"
python -X utf8 -u tools/paired_arena_env_ab.py --env-name MOSAIC_ENVELOPE_SEARCH_C --arms 1.0 --control 1.0 --model "$NET" --model-b "$NET" --spec-a "$SPEC" --spec-b "$CHAMP" --net-sims 400 --n-games 80 --seed 20261014 --log-games --out-prefix "k3${TAG}_b06_vs_k3p_first_s14"
python -X utf8 -u tools/paired_arena_env_ab.py --env-name MOSAIC_ENVELOPE_SEARCH_C --arms 1.0 --control 1.0 --model "$NET" --model-b "$NET" --spec-a "$CHAMP" --spec-b "$SPEC" --net-sims 400 --n-games 80 --seed 20261014 --log-games --out-prefix "k3${TAG}_b06_vs_k3p_second_s14"
for d in first second; do
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$ART/paired_arena_env_k3${TAG}_b06_vs_k3p_${d}_s14.json" --out "$ART/columns_k3${TAG}_b06_vs_k3p_${d}_s14.json"
done
python -X utf8 -u tools/probes/arena_points_probe.py --artifact "$ART/paired_arena_env_k3${TAG}_b06_vs_k3p_first_s14.json" "$ART/paired_arena_env_k3${TAG}_b06_vs_k3p_second_s14.json" --out "$ART/points_k3${TAG}_b06_vs_k3p_s14.json" || echo "   Kuppel-Bonus-Sonde fehlgeschlagen"
echo "== Arm $TAG fertig $(date +%H:%M:%S). Zusaetzlich die Reihen-6-Blockade messen:"
python -X utf8 -u tools/probes/tiling_geometry_probe.py --artifact "$ART/paired_arena_env_k3${TAG}_b06_vs_k3p_first_s14.json" "$ART/paired_arena_env_k3${TAG}_b06_vs_k3p_second_s14.json" --out "$ART/tiling_geometry_hull2_v2.json" || echo "   Reihen-Alter-Sonde fehlgeschlagen"
echo "== FERTIG $(date +%H:%M:%S)"
