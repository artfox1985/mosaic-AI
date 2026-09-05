#!/usr/bin/env bash
# HALTE-PROZESS fuer die Reihenfolge der Nacht-Abnahmen (2026-09-06, 00:58).
# Problem: tools/night_v24_b03_acceptance_714.sh (laeuft seit 2026-09-05 20:58) wartet auf
#   'night_v24_after_b05_chain|night_v24_acceptance_chain|cpu_queue_after_b02|self_play|paired_gating|paired_arena|maturin|cargo '
# und kennt weder cpu_queue_after_b04.sh, die Tiling-Geometrie-Sonde noch den b05-Wartelauf.
# Sobald das b03-Modell liegt und die b04-Kette endet, wuerde es NEBEN der Sonde oder VOR b05 starten
# (zwei CPU-Messungen gegeneinander). Ein laufendes Skript wird nicht editiert, der Prozess nicht beendet;
# stattdessen haelt DIESER Prozess (sein Dateiname passt auf 'night_v24_after_b05_chain') den alten
# Wartelauf fest, bis Sonde und b05-Abnahme durch sind. Kein anderes Warteskript passt auf diesen Namen
# (geprueft: b05-Wartelauf, cpu_queue_after_b04, night_v24_acceptance_chain).
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/night_v24_after_b05_chain_hold.sh
set -uo pipefail
cd "$(dirname "$0")/.."
procs() {
  local out
  for _try in 1 2 3; do
    out=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '$1' -and \$_.Name -match 'python|bash|cargo' }).Count" 2>/dev/null | tr -d '\r[:space:]')
    case "$out" in ''|*[!0-9]*) sleep 5 ;; *) echo "$out"; return 0 ;; esac
  done
  echo 999
}
echo "== HALTE b03-Abnahme, bis Sonde und b05-Abnahme durch sind ($(date +%H:%M:%S); Deckel 30 h)"
tick=0
while true; do
  m=$(procs 'night_v24_b05_acceptance_wai[t]|cpu_queue_after_b0[0-9]|tiling_geometry_prob[e]|b04_acceptance_744ven[v]|night_v24_acceptance_chai[n]'); m=${m:-999}
  [ "$m" = "0" ] && break
  tick=$((tick+1)); [ "$tick" -gt 1800 ] && { echo "STOPP: 30 h"; exit 70; }
  [ $((tick % 30)) -eq 0 ] && echo "   halte: offene Laeufe=$m ($(date +%H:%M:%S))"
  sleep 60
done
echo "== FREIGABE $(date +%H:%M:%S): Sonde und b05-Abnahme beendet, b03-Abnahme darf starten"
