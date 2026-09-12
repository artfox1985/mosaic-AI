#!/usr/bin/env bash
# Einhuellende A1/A2 (PREREG_geometric_envelope.md par.12a Kanal A, par.12c Punkt 3): Such-Variante
# der Orakel-Bruecke auf frozen_v3 (1.800 Zustaende, Orakel @5000), Champion-Netz, vier
# Einstellungen: aus (k3v_off), Bestand (Champion-Spec: K3-P, Huellenform 2, K5), plus K3-D
# (dead_cell_w 1,0), plus Jokerfeld (out_wild_w 1,0). Ein Lauf je Spec, sequenziell, exklusiv.
# Aufruf: bash tools/night_envelope_bridge.sh <champion-name>   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
CH=${1:-v28-b02}
ART=evaluations/artifacts
MODEL="models/alphazero_${CH}_brierbest.onnx"
[ -f "$MODEL" ] || { echo "STOPP: $MODEL fehlt"; exit 12; }
for PAIR in "aus:models/k3v_off.spec.json" "bestand:models/frozen_champions/v27-b01/spec.json" "k3d:models/k3d_on.spec.json" "jokerfeld:models/out_wild_on.spec.json"; do
  TAG=${PAIR%%:*}; SPEC=${PAIR#*:}
  echo "== A1/A2 $CH Einstellung $TAG ($SPEC) $(date +%H:%M:%S)"
  python -X utf8 -u tools/oracle_metrics.py --models \
    --oracle-json evaluations/artifacts/frozen_v3_oracle_labels.json \
    --frozen-set evaluations/frozen_eval_set_v3.pkl \
    --search-sims 400 --search-model "$MODEL" --spec "$SPEC" \
    --out "$ART/search_bridge_frozen_v3_${CH}_${TAG}.json"
  echo "   Exit $? ($(date +%H:%M:%S))"
done
echo "== A1/A2 FERTIG $(date +%F' '%H:%M:%S)"
