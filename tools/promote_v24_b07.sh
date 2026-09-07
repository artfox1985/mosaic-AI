#!/usr/bin/env bash
# Promotion v24-b07 (docs/promotion_checklist.md, Skill mosaic-champion-promotion).
# Nutzer-Freigabe 2026-09-07: "ja starte die promotion. dann koennen wir v24 endlich
# abschliessen."
#
# b07 traegt die GEWICHTE von b06 und eine andere Spec (Huellenform 2, K5). Daraus folgt
# fuer die Checkliste: alles, was nur vom NETZ abhaengt, ist identisch und wird uebernommen
# statt neu gemessen. Geprueft an der Quelle 2026-09-07:
#   5b Platt  -- tools/platt_fit.py rechnet auf der .pth, b07 hat keine eigene; die
#                Anzeige-Parameter in server.py (_DISPLAY_CAL_A/_B) bleiben unveraendert.
#   5c sigma  -- tools/gumbel_scale_calibration.py kennt KEIN --spec (Zeilen 85-88), ist
#                also spec-unabhaengig; der Wert von b06 gilt weiter.
#   5d Fixture-- folgt models/champion.txt und MUSS neu (Schritt 4 unten).
# Was durch die SUCHE geht, wird neu gemessen: die beiden fehlenden Elo-Kanten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
NET="models/alphazero_v24-b07_brierbest.onnx"; SPEC="models/v24-b07_brierbest.spec.json"
ART="evaluations/artifacts"

procs() {
  local out
  for _try in 1 2 3; do
    out=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '$1' -and \$_.Name -match 'python|bash|cargo' }).Count" 2>/dev/null | tr -d '\r[:space:]')
    case "$out" in ''|*[!0-9]*) sleep 5 ;; *) echo "$out"; return 0 ;; esac
  done
  echo 999
}
echo "== 0) Warten auf freie CPU $(date +%H:%M:%S)"
tick=0
while true; do
  m=$(procs 'paired_gating|paired_arena|self_play\.py|anchor_arena|golden_probe|maturin|cargo '); m=${m:-999}
  [ "$m" = "0" ] && break
  tick=$((tick+1)); [ "$tick" -gt 120 ] && { echo "STOPP: 2 h ohne freie CPU"; exit 65; }
  sleep 60
done
echo "   CPU frei $(date +%H:%M:%S)"

echo "== 1) Schritt 1: Server-Default auf v24-b07 $(date +%H:%M:%S)"
python -X utf8 tools/set_champion.py v24-b07_brierbest; echo "   Exit $?"

echo "== 2) Schritt 3: ANKER-Kante, festes n=150 ohne Fruehstopp $(date +%H:%M:%S)"
python -X utf8 -u tools/anchor_arena.py --model "$NET" --spec "$SPEC" \
  --net-sims 400 --anchor-sims 150 --n-games 150 --workers 6 --force-cross-era \
  --out "$ART/anchor_arena_v24-b07.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 3) Schritt 4: CHAMPION-2-Kante gegen v23-b01_k3p10 @400 $(date +%H:%M:%S)"
python -X utf8 -u tools/paired_gating.py \
  --model-a "$NET" --model-b models/alphazero_v23-b01_brierbest.onnx \
  --name-a v24-b07 --name-b v23-b01_k3p10 \
  --spec-a "$SPEC" --spec-b models/v23-b01_k3p10.spec.json \
  --sims 400 --block-size 5 --max-pairs 200 --seed 20261017 --threads 10 \
  --no-promote-winner --out "$ART/paired_gating_v24-b07_vs_v23-b01_k3p10_s17.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 4) Schritt 5d: Netz-Paritaets-Fixture neu erzeugen $(date +%H:%M:%S)"
. tools/hooks/python_dll_path.sh 2>/dev/null && mosaic_prepend_python_dll_path 2>/dev/null || true
( cd engine && MOSAIC_UPDATE_NET_PARITY_FIXTURE=1 cargo test --release net_parity_hash_matches_champion_fixture -- --nocapture )
echo "   Schreiben Exit $? ($(date +%H:%M:%S))"
echo "== 5) Schritt 5d Gegenprobe: FRISCHER Prozess ohne die Variable $(date +%H:%M:%S)"
( cd engine && cargo test --release net_parity_hash_matches_champion_fixture )
echo "   Gegenprobe Exit $? ($(date +%H:%M:%S))"

echo "== 6) Schritt 7: Golden Probe fuer das eingefrorene Artefakt (rund 22 min) $(date +%H:%M:%S)"
python -X utf8 -u tools/build_frozen_golden_probe.py --artifact-dir models/frozen_champions/v24-b07 --seed-base 916001
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== KETTE FERTIG $(date +%H:%M:%S): Elo-Zeilen, Artefakt-Bau, STATUS und history macht der Koordinator."
