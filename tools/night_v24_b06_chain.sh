#!/usr/bin/env bash
# v24-b06: das b02-Rezept (lambda 0,7) auf der 744er-Sicht (Nutzer 2026-09-06, 11:55: "starte A und B";
# Grund: Self-Plays erzeugt der Champion, ein 744er-Champion-Kandidat mit Knopf-Beleg fehlt). Befehl =
# b04-Kette Schritt 4 (night_v24_b04_chain.sh:62) plus --value-target-lambda 0.7 (einziger Unterschied
# der Manifeste b02/b04) plus --fast-loader (bitgleich, Mini-Fenster-Test E und Volllauf b03). Der 744er-
# Monolith .cache_85a75d76dfab.h5 liegt; config.INPUT_SIZE muss 744 sein. Danach Abnahme wie die anderen
# Arme, aber erst, wenn die Champion-Kante b05 (champion_edge_b05.sh) durch ist (ein CPU-Auftrag).
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/night_v24_b06_chain.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
python -X utf8 -c "import config, sys; print('   config.INPUT_SIZE =', config.INPUT_SIZE); sys.exit(0 if config.INPUT_SIZE == 744 else 72)" || { echo "STOPP: config.INPUT_SIZE ist nicht 744"; exit 72; }
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v24.json MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_VAL_POOL='^selfplay_v23-b01-'
echo "== 1) Training v24-b06 (b02-Rezept lambda 0,7, Sicht 744, --fast-loader) $(date +%H:%M:%S)"
python -X utf8 -u train.py --name v24-b06 --load v23-b01_brierbest --file-list data/window_v24.txt --encoder 2d --value-target-variant nortv --value-head wdl --ownership-head-2d --ownership-weight 1.0 --endgame-head --opp-points-head --moon-loss-weight 0 --select-by-brier --val-frac 0.05 --epochs 12 --lr 5e-5 --lr-schedule cosine --lr-t-max 12 --seed 20260828 --value-target-lambda 0.7 --fast-loader; TRC=$?
echo "   Training Exit $TRC ($(date +%H:%M:%S)); bei Abbruch: derselbe Befehl plus --resume"
[ "$TRC" = "0" ] || { echo "STOPP: Training rot"; exit 73; }
procs() {
  local out
  for _try in 1 2 3; do
    out=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '$1' -and \$_.Name -match 'python|bash|cargo' }).Count" 2>/dev/null | tr -d '\r[:space:]')
    case "$out" in ''|*[!0-9]*) sleep 5 ;; *) echo "$out"; return 0 ;; esac
  done
  echo 999
}
echo "== 2) Warten auf freie CPU (Champion-Kante b05, andere Messungen) $(date +%H:%M:%S)"
tick=0
while true; do
  m=$(procs 'champion_edge_b0[5]|paired_gating|paired_arena|self_play\.py|argmax_profile|maturin|cargo '); m=${m:-999}
  [ "$m" = "0" ] && break
  tick=$((tick+1)); [ "$tick" -gt 720 ] && { echo "STOPP: 12 h ohne freie CPU"; exit 74; }
  [ $((tick % 30)) -eq 0 ] && echo "   warte: CPU-Messung=$m ($(date +%H:%M:%S))"
  sleep 60
done
echo "== 3) Abnahme b06 $(date +%H:%M:%S)"
bash tools/night_v24_acceptance_chain.sh b06; rc=$?
echo "   Abnahme b06 Exit $rc ($(date +%H:%M:%S))"
python -X utf8 -u tools/probes/arena_points_probe.py --artifact evaluations/artifacts/paired_arena_env_v24b06_vs_b01_first_s14.json evaluations/artifacts/paired_arena_env_v24b06_vs_b01_second_s14.json --out evaluations/artifacts/points_v24b06_vs_b01_s14.json || echo "   Kuppel-Bonus-Sonde b06 fehlgeschlagen"
echo "== FERTIG $(date +%H:%M:%S)"
