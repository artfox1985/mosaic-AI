#!/usr/bin/env bash
# K5-Arm "eine Spezialfliese in Reihe 6" EINFAKTORIELL gegen die Huellenform
# (PREREG_special_tile_yield.md par.9a; Nutzer 2026-09-07 06:07 "dann bau und miss das
# gemeinsam mit der form. gehoert ja zusammen").
#
# Arm      = Huellenform 2 PLUS K5 (special_row6_w 1,0)   models/hullform2_k5w10.spec.json
# Kontrolle= Huellenform 2 ALLEIN (special_row6_w 0,0)    models/hullform2.spec.json
# Gepruefte Einfaktorialitaet 2026-09-07: die beiden Specs unterscheiden sich in GENAU
# einem Feld (special_row6_w); die Kontrolle unterscheidet sich vom Champion in GENAU
# einem Feld (envelope_hull_form). Ein Arm gegen den CHAMPION wuerde beide Faktoren
# mischen und den bereits ueber zwei Seeds gemessenen Form-Anteil noch einmal bezahlen.
#
# Warum das Instrument ZWEIMAL laeuft: fuer die Huellenform existiert kein
# argmax-Instrument (par.8.15b/c wurde nur ueber die gepaarte Arena gemessen). Der
# Bezugswert 0,4975 gehoert zum CHAMPION, also zum Dreieck. Ein K5-Instrument gegen
# diesen Bezug waere zweifaktoriell. Darum wird die Kontrolle mitgemessen.
#
# Reihenfolge: Arena zuerst (rund 26 min, traegt die Kopfkennzahl Kuppel-Bonus), dann die
# beiden Instrumente (je rund 24 min). Gesamt rund 80 min.
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/night_k5_row6_special.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
NET="models/alphazero_v24-b06_brierbest.onnx"
ARM="models/hullform2_k5w10.spec.json"
CTL="models/hullform2.spec.json"
ART="evaluations/artifacts"

procs() {
  local out
  for _try in 1 2 3; do
    out=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '$1' -and \$_.Name -match 'python|bash|cargo' }).Count" 2>/dev/null | tr -d '\r[:space:]')
    case "$out" in ''|*[!0-9]*) sleep 5 ;; *) echo "$out"; return 0 ;; esac
  done
  echo 999
}

echo "== 0) Warten auf freie CPU $(date +%H:%M:%S); Deckel 2 h"
tick=0
while true; do
  m=$(procs 'paired_gating|paired_arena|self_play\.py|argmax_profile|maturin|cargo '); m=${m:-999}
  [ "$m" = "0" ] && break
  tick=$((tick+1)); [ "$tick" -gt 120 ] && { echo "STOPP: 2 h ohne freie CPU"; exit 65; }
  echo "   warte: CPU-Last=$m ($(date +%H:%M:%S))"
  sleep 60
done
echo "   CPU frei $(date +%H:%M:%S)"

echo "== 1) Gepaarte Arena Arm gegen Kontrolle, Richtung first $(date +%H:%M:%S)"
python -X utf8 -u tools/paired_arena_env_ab.py --env-name MOSAIC_ENVELOPE_SEARCH_C --arms 1.0 --control 1.0 \
  --model "$NET" --model-b "$NET" --spec-a "$ARM" --spec-b "$CTL" \
  --net-sims 400 --n-games 80 --seed 20261014 --log-games --out-prefix "k5w10_b06_vs_hf2_first_s14"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 2) Gepaarte Arena, Richtung second $(date +%H:%M:%S)"
python -X utf8 -u tools/paired_arena_env_ab.py --env-name MOSAIC_ENVELOPE_SEARCH_C --arms 1.0 --control 1.0 \
  --model "$NET" --model-b "$NET" --spec-a "$CTL" --spec-b "$ARM" \
  --net-sims 400 --n-games 80 --seed 20261014 --log-games --out-prefix "k5w10_b06_vs_hf2_second_s14"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 3) Sonden auf die Arena-Artefakte $(date +%H:%M:%S)"
for d in first second; do
  python -X utf8 -u tools/probes/arena_column_probe.py \
    --artifact "$ART/paired_arena_env_k5w10_b06_vs_hf2_${d}_s14.json" \
    --out "$ART/columns_k5w10_b06_vs_hf2_${d}_s14.json"
done
python -X utf8 -u tools/probes/arena_points_probe.py \
  --artifact "$ART/paired_arena_env_k5w10_b06_vs_hf2_first_s14.json" \
           "$ART/paired_arena_env_k5w10_b06_vs_hf2_second_s14.json" \
  --out "$ART/points_k5w10_b06_vs_hf2_s14.json" || echo "   Kuppel-Bonus-Sonde fehlgeschlagen"

echo "== 4) argmax-Instrument KONTROLLE (Huellenform 2 allein) $(date +%H:%M:%S)"
bash tools/argmax_profile.sh "hf2-v24b06" "$NET" \
  MOSAIC_ENVELOPE_PROJECTED=1 MOSAIC_ENVELOPE_SEARCH_C=1.0 MOSAIC_ENVELOPE_HULL_FORM=2 MOSAIC_SPECIAL_ROW6_W=0.0
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 5) argmax-Instrument ARM (Huellenform 2 plus K5) $(date +%H:%M:%S)"
bash tools/argmax_profile.sh "k5w10-v24b06" "$NET" \
  MOSAIC_ENVELOPE_PROJECTED=1 MOSAIC_ENVELOPE_SEARCH_C=1.0 MOSAIC_ENVELOPE_HULL_FORM=2 MOSAIC_SPECIAL_ROW6_W=1.0
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== KETTE FERTIG $(date +%H:%M:%S): Registrierung par.9c durch den Koordinator."
