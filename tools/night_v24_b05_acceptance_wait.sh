#!/usr/bin/env bash
# Abnahme b05 (2026-09-06): wartet, bis die CPU frei ist (b04-Abnahme in venv_measure744, Tiling-Geometrie-
# Sonde, sonstige Messungen) UND das 744er-Wheel in der Basis-Installation liegt (night_v24_b03_now.sh
# Schritt 1), dann night_v24_acceptance_chain.sh b05 plus Kuppel-Bonus-Sonde. Laeuft parallel zum
# b03-Training auf der GPU (ein CPU-Auftrag neben dem GPU-Training).
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/night_v24_b05_acceptance_wait.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART="evaluations/artifacts"

procs() {
  local out
  for _try in 1 2 3; do
    out=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '$1' -and \$_.Name -match 'python|bash|cargo' }).Count" 2>/dev/null | tr -d '\r[:space:]')
    case "$out" in ''|*[!0-9]*) sleep 5 ;; *) echo "$out"; return 0 ;; esac
  done
  echo 999
}

echo "== 0) Warten auf freie CPU und Basis-Wheel 744 ($(date +%H:%M:%S); Deckel 30 h)"
tick=0
while true; do
  m=$(procs 'night_v24_acceptance_chai[n]|b04_acceptance_744ven[v]|cpu_queue_after_b0[0-9]|tiling_geometry_prob[e]|self_play\.py|paired_gating|paired_arena|maturin|cargo '); m=${m:-999}
  w=$(python -X utf8 -c "import json,mosaic_rust as mr;print(json.loads(mr.engine_config_json()).get('input_size'))" 2>/dev/null | tr -d '\r[:space:]')
  if [ "$m" = "0" ] && [ "$w" = "744" ]; then break; fi
  tick=$((tick+1)); [ "$tick" -gt 1800 ] && { echo "STOPP: 30 h ohne Bedingung"; exit 70; }
  [ $((tick % 30)) -eq 0 ] && echo "   warte: CPU-Messung=$m, Basis-Wheel=$w ($(date +%H:%M:%S))"
  sleep 60
done
echo "   Bedingung erfuellt $(date +%H:%M:%S)"
echo "== 1) Abnahme b05 (Bezug b04 UND b01; Kette misst gegen b01) $(date +%H:%M:%S)"
bash tools/night_v24_acceptance_chain.sh b05; rc=$?
echo "   Abnahme b05 Exit $rc ($(date +%H:%M:%S))"
python -X utf8 -u tools/probes/arena_points_probe.py --artifact "$ART/paired_arena_env_v24b05_vs_b01_first_s14.json" "$ART/paired_arena_env_v24b05_vs_b01_second_s14.json" --out "$ART/points_v24b05_vs_b01_s14.json" || echo "   Kuppel-Bonus-Sonde b05 fehlgeschlagen"
echo "== FERTIG $(date +%H:%M:%S)"
