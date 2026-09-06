#!/usr/bin/env bash
# Knopf-Messkette am NEUEN Champion v24-b06 (umgestellt 2026-09-06 20:45 nach der Promotion; Bezug Tor 2a mit
# Knopf 0,4975 aus tor2a_v24b06.json). Aus night_k3_knobs_champion.sh abgeleitet (PREREG_geometric_envelope.md par.8.11 K3-P2, par.8.14 K3-F, par.12b
# Rauschboden; Nutzer 2026-09-06 13:15: "miss den rauschboden mit, starte mit dem champion ... vier
# arme sind ok"). Wartet auf freie CPU (b06-Abnahme, Spiel-Interface-Rauchtest), dann:
#   0) Rauschboden par.12b Punkte 1-2: rho je Runde auf frozen_v3 fuer v23-b01 und die v24-Arme
#      (value_head_reliability_probe.py, Block-Bootstrap, Netz-Spannweite)
#   1-4) je Arm K3-P2 (Modus 4), K3-F 1,0 (Modus 1), K3-F 0,5 (Modus 1), beide (Modus 4 + 1,0):
#      argmax-Instrument @400 (200 Partien, Seed 20260931; Bezug Champion + K3-P 0,555) und gepaarte
#      Arena 2 x 80 mit Logs, Arm-Spec gegen Champion-Spec am SELBEN Netz (Spalten aus der Brettgeometrie,
#      Kuppel-Bonus, lange Reihen begonnen/vollendet). Verdikt registriert der Koordinator.
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/night_k3_knobs_champion.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
NET="models/alphazero_v24-b06_brierbest.onnx"; CHAMP="models/v24-b06_brierbest.spec.json"; ART="evaluations/artifacts"
procs() {
  local out
  for _try in 1 2 3; do
    out=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '$1' -and \$_.Name -match 'python|bash|cargo' }).Count" 2>/dev/null | tr -d '\r[:space:]')
    case "$out" in ''|*[!0-9]*) sleep 5 ;; *) echo "$out"; return 0 ;; esac
  done
  echo 999
}
echo "== 0) Warten auf freie CPU $(date +%H:%M:%S); Deckel 12 h"
tick=0
while true; do
  m=$(procs 'night_v24_b06_chai[n]|night_v24_acceptance_chai[n]|champion_edge_b0[5]|paired_gating|paired_arena|self_play\.py|argmax_profile|maturin|cargo '); m=${m:-999}
  [ "$m" = "0" ] && break
  tick=$((tick+1)); [ "$tick" -gt 720 ] && { echo "STOPP: 12 h ohne freie CPU"; exit 65; }
  [ $((tick % 30)) -eq 0 ] && echo "   warte: CPU-Messung=$m ($(date +%H:%M:%S))"
  sleep 60
done
echo "   CPU frei $(date +%H:%M:%S)"
echo "== 1) Rauschboden par.12b Punkte 1-2 (frozen_v3, 7 Netze) $(date +%H:%M:%S)"
python -X utf8 -u tools/probes/value_head_reliability_probe.py --models v23-b01_brierbest v24-b01_brierbest v24-b02_brierbest v24-b03_brierbest v24-b04_brierbest v24-b05_brierbest v24-b06_brierbest --out "$ART/value_head_reliability_par12b.json"; echo "   Exit $? ($(date +%H:%M:%S))"
run_arm() {  # $1 Tag, $2 Spec, $3.. Env-Knoepfe fuer das argmax-Instrument
  local tag=$1 spec=$2; shift 2
  echo "== Arm $tag: argmax-Instrument @400 $(date +%H:%M:%S)"
  bash tools/argmax_profile.sh "k3-${tag}-v24b06" "$NET" "$@"; echo "   Exit $?"
  echo "== Arm $tag: gepaarte Arena Arm-Spec gegen Champion-Spec $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_arena_env_ab.py --env-name MOSAIC_ENVELOPE_SEARCH_C --arms 1.0 --control 1.0 --model "$NET" --model-b "$NET" --spec-a "$spec" --spec-b "$CHAMP" --net-sims 400 --n-games 80 --seed 20261014 --log-games --out-prefix "k3${tag}_b06_vs_k3p_first_s14"
  python -X utf8 -u tools/paired_arena_env_ab.py --env-name MOSAIC_ENVELOPE_SEARCH_C --arms 1.0 --control 1.0 --model "$NET" --model-b "$NET" --spec-a "$CHAMP" --spec-b "$spec" --net-sims 400 --n-games 80 --seed 20261014 --log-games --out-prefix "k3${tag}_b06_vs_k3p_second_s14"
  for d in first second; do
    python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$ART/paired_arena_env_k3${tag}_b06_vs_k3p_${d}_s14.json" --out "$ART/columns_k3${tag}_b06_vs_k3p_${d}_s14.json"
  done
  python -X utf8 -u tools/probes/arena_points_probe.py --artifact "$ART/paired_arena_env_k3${tag}_b06_vs_k3p_first_s14.json" "$ART/paired_arena_env_k3${tag}_b06_vs_k3p_second_s14.json" --out "$ART/points_k3${tag}_b06_vs_k3p_s14.json" || echo "   Kuppel-Bonus-Sonde $tag fehlgeschlagen"
  echo "== Arm $tag fertig $(date +%H:%M:%S)"
}
run_arm p2   models/k3p2_c10.spec.json  MOSAIC_ENVELOPE_PROJECTED=4 MOSAIC_ENVELOPE_SEARCH_C=1.0
run_arm f10  models/k3f_w10.spec.json   MOSAIC_ENVELOPE_PROJECTED=1 MOSAIC_ENVELOPE_SEARCH_C=1.0 MOSAIC_ENVELOPE_FLUSH_W=1.0
run_arm f05  models/k3f_w05.spec.json   MOSAIC_ENVELOPE_PROJECTED=1 MOSAIC_ENVELOPE_SEARCH_C=1.0 MOSAIC_ENVELOPE_FLUSH_W=0.5
run_arm p2f10 models/k3p2f_w10.spec.json MOSAIC_ENVELOPE_PROJECTED=4 MOSAIC_ENVELOPE_SEARCH_C=1.0 MOSAIC_ENVELOPE_FLUSH_W=1.0
echo "== KETTE FERTIG $(date +%H:%M:%S): Registrierung par.8.11 / 8.14 / 12b durch den Koordinator."
