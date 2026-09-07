#!/usr/bin/env bash
# Gating des Spec-Kandidaten (Huellenform 2, wahlweise plus K5) gegen die Champion-Spec,
# am SELBEN Netz. Aufbau und Leseregel: PREREG_geometric_envelope.md par.8.15d.
#
# Aufruf:  bash tools/gate_hull_form_spec.sh <arm.spec.json> <tag> [seed] [kontrolle.spec.json]
#   Huellenform gegen den Champion (Default-Kontrolle):
#     bash tools/gate_hull_form_spec.sh models/hullform2.spec.json hf2 20261015
#   K5 gegen die Huellenform (Nachmessung zu par.9c, Nutzer-Entscheid 2026-09-07):
#     bash tools/gate_hull_form_spec.sh models/hullform2_k5w10.spec.json k5vshf2 20261016 models/hullform2.spec.json
#
# Warum ein DRITTER Seed: 20261014 und 20261013 tragen die beiden Arm-Messungen
# (par.8.15b/c). Ein Gating auf denselben Seeds waere kein unabhaengiger Beleg.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ARM=${1:?Arm-Spec fehlt}; TAG=${2:?Tag fehlt}; SEED=${3:-20261015}
NET="models/alphazero_v24-b06_brierbest.onnx"
CTL=${4:-models/v24-b06_brierbest.spec.json}
ART="evaluations/artifacts"

procs() {
  local out
  for _try in 1 2 3; do
    out=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '$1' -and \$_.Name -match 'python|bash|cargo' }).Count" 2>/dev/null | tr -d '\r[:space:]')
    case "$out" in ''|*[!0-9]*) sleep 5 ;; *) echo "$out"; return 0 ;; esac
  done
  echo 999
}
echo "== Warten auf freie CPU $(date +%H:%M:%S); Deckel 3 h"
tick=0
while true; do
  m=$(procs 'paired_gating|paired_arena|self_play\.py|argmax_profile|maturin|cargo '); m=${m:-999}
  [ "$m" = "0" ] && break
  tick=$((tick+1)); [ "$tick" -gt 180 ] && { echo "STOPP: 3 h ohne freie CPU"; exit 65; }
  [ $((tick % 5)) -eq 0 ] && echo "   warte: CPU-Last=$m ($(date +%H:%M:%S))"
  sleep 60
done
echo "   CPU frei $(date +%H:%M:%S); Arm $ARM gegen Kontrolle $CTL, Seed $SEED"

# Einfaktorialitaet BELEGEN statt behaupten: die beiden Specs duerfen sich in genau einem
# Feld unterscheiden. Ein zweites Feld waere ein zweiter Faktor und die Messung wertlos.
python -X utf8 -c "
import json, sys
a = json.load(open(sys.argv[1], encoding='utf-8')); b = json.load(open(sys.argv[2], encoding='utf-8'))
d = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
print('   Unterschied Arm gegen Kontrolle:', d)
sys.exit(0 if len(d) == 1 else 9)
" "$ARM" "$CTL" || { echo "STOPP: nicht einfaktoriell."; exit 46; }

# Defaults von paired_gating.py sind bereits die Projektwerte: Blockgroesse 5,
# Deckel 200 Paare, sims 400, threads 10, SPRT H1 p=0,65 -- trotzdem explizit gesetzt,
# damit das Manifest sie traegt (Regel "Lauf-Manifest gegen Referenz").
python -X utf8 -u tools/paired_gating.py \
  --model-a "$NET" --model-b "$NET" \
  --name-a "v24-b06_${TAG}_arm" --name-b "v24-b06_${TAG}_ctl" \
  --spec-a "$ARM" --spec-b "$CTL" \
  --sims 400 --block-size 5 --max-pairs 200 --seed "$SEED" --threads 10 \
  --no-promote-winner \
  --out "$ART/paired_gating_${TAG}_s${SEED: -2}.json"
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== GATING FERTIG $(date +%H:%M:%S): Lesart nach par.8.15d -- SPRT-Verdikt, Vorzeichentest UND gepaartes KI, nicht das SPRT allein."
