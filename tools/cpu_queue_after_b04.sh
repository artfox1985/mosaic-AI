#!/usr/bin/env bash
# CPU-Auftrag nach der b04-Abnahme (Nutzer 2026-09-05: "fahr die sonde im naechsten cpu-freien fenster
# insbesondere mit abgleich der mensch-logs"): Tiling-Geometrie-Sonde (PREREG_geometric_envelope.md par.8.12)
#   1) auf den Server-Logs Mensch gegen KI (static/log/game_*.log, 19 abgeschlossene Partien)
#   2) auf den Netz-Arenen b01 gegen v24-b01 (Tor 2b, 2 x 80 Partien, beide Seiten K3-P C 1,0)
# Wartet, bis keine Abnahme-Kette und keine andere CPU-Messung mehr laeuft. Die Nachtkette nach b05
# wartet ihrerseits auf das Ende dieses Skripts (Muster 'cpu_queue_after_b0').
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/cpu_queue_after_b04.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

procs() {
  local out
  for _try in 1 2 3; do
    out=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '$1' -and \$_.Name -match 'python|bash|cargo' }).Count" 2>/dev/null | tr -d '\r[:space:]')
    case "$out" in ''|*[!0-9]*) sleep 5 ;; *) echo "$out"; return 0 ;; esac
  done
  echo 999
}

echo "== 0) Warten auf das Ende der b04-Abnahme und aller CPU-Messungen ($(date +%H:%M:%S); Deckel 12 h)"
tick=0
while true; do
  m=$(procs 'night_v24_acceptance_chai[n]|b04_acceptance_744ven[v]|self_play\.py|paired_gating|paired_arena|maturin|cargo '); m=${m:-999}
  [ "$m" = "0" ] && break
  tick=$((tick+1)); [ "$tick" -gt 720 ] && { echo "STOPP: 12 h ohne freie CPU"; exit 65; }
  [ $((tick % 30)) -eq 0 ] && echo "   warte: CPU-Messung=$m ($(date +%H:%M:%S))"
  sleep 60
done
echo "   CPU frei $(date +%H:%M:%S)"

echo "== 1) Tiling-Geometrie: Mensch-Logs $(date +%H:%M:%S)"
python -X utf8 -u tools/probes/tiling_geometry_probe.py --server-logs "static/log/game_*.log" --k 32 --out evaluations/artifacts/tiling_geometry_probe_human.json; echo "   Exit $?"
echo "== 2) Tiling-Geometrie: Netz-Arena b01 gegen v24-b01 $(date +%H:%M:%S)"
python -X utf8 -u tools/probes/tiling_geometry_probe.py --artifact evaluations/artifacts/paired_arena_env_v24b01_vs_b01_first_s14.json evaluations/artifacts/paired_arena_env_v24b01_vs_b01_second_s14.json --k 32 --out evaluations/artifacts/tiling_geometry_probe_arena.json; echo "   Exit $?"
echo "== FERTIG $(date +%H:%M:%S): Auswertung par.8.12 durch den Koordinator."
