#!/usr/bin/env bash
# v28-ERZEUGUNG: die drei Klassen, nacheinander, Generator v27-b01.
# Befehle woertlich aus PREREG_v28_window.md par.5 (Seeds 20260917/15/16).
# Vorbereitet 2026-09-10 als Vorlage (v28 ausgesetzt, Nutzer); START NUR AUF AUSDRUECKLICHE FREIGABE.
#
# WARTEBEDINGUNG: gestartet wird erst, wenn KEINE Messung mehr laeuft. Gehaertet wie die
# v26-Ketten -- der escapte Punkt trifft die eigene Kommandozeile nicht, und die
# PowerShell-Prozesse sind ausgeschlossen (Selbsttreffer-Vorfall 2026-09-09: `-match
# 'self_play'` lieferte nie 0, sondern 4, und eine Kette stand 35 Minuten still).
#
# DANEBEN GEHOERT DER CACHE-WAECHTER, und zwar zwingend unter der Trainings-Umgebung:
#   MOSAIC_IGNORE_POLICY_TARGET_VALID=1 python -X utf8 -u tools/build_cache_incremental.py \
#     --data-dir data --encoder 2d --value-target-variant nortv --workers 3 \
#     --watch --wartezeit 60 --leerlauf-abbruch 100000
# Die Variable steht IM Datei-Schluessel; ohne sie landen die Bloecke in einem Namensraum,
# den das Training nie adressiert (2026-09-09: 2.680 tote Bloecke, docs/pitfalls.md).
#
# ERWARTETE DAUER nach den v26-Manifesten (data/manifest_v25-b01-*.json, laufzeit-Block):
# v27 gemessen: 13.769 s + 12.575 s + 10.568 s = 36.912 s, rund 10,3 h (docs/measured_runtimes.md). `--games 4000` gilt AUCH fuer die
# Ausflug-Klasse: der Ausflug hat eine eigene game_id und zaehlt mit (Korrektur aus PREREG_v25_window.md par.19a).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
MODEL=models/alphazero_v27-b01_brierbest.onnx
SPEC=models/v24-b07_brierbest.spec.json

busy() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match 'self_play\.py|train\.py|paired_gating|anchor_arena|frozen_referee' -and \$_.Name -notmatch 'pwsh|powershell' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" != "0" ]   # alles ausser einer klaren 0 gilt als belegt
}

echo "== WARTEN auf eine freie Maschine $(date +%F' '%H:%M:%S)"
while busy; do
  echo "   noch belegt ($(date +%H:%M:%S))"
  sleep 300
done
echo "   frei ($(date +%H:%M:%S))"

echo "== 1) Traeger, 4.000 Partien, policy-aktiv $(date +%F' '%H:%M:%S)"
python -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --version v27-b01-policy \
  --threads 11 --chunk 10 --per-file 10 --seed 20260917 \
  --tau-argmax-from-move 1 --deviate-prob 1.0
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c '^selfplay_v27-b01-policy_')"

echo "== 2) Schwarm a, 4.000 Partien, value-only, temperiert $(date +%F' '%H:%M:%S)"
python -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --value-only --version v27-b01-value-tempc \
  --threads 11 --chunk 10 --per-file 10 --seed 20260918 \
  --action-temp 2 --deviate-prob 1.0
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c '^selfplay_v27-b01-value-tempc_')"

echo "== 3) Schwarm b, 4.000 Identitaeten, value-only, Ausflug $(date +%F' '%H:%M:%S)"
python -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --value-only --version v27-b01-value-excursion \
  --threads 11 --chunk 10 --per-file 10 --seed 20260919 \
  --excursion-prob 1.0 --tau-argmax-from-move 1 --no-root-noise
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c '^selfplay_v27-b01-value-excursion_')"

echo "== v28-ERZEUGUNG FERTIG $(date +%F' '%H:%M:%S)"
for k in policy value-tempc value-excursion; do
  echo "   $k: $(ls data/ | grep -c "^selfplay_v27-b01-${k}_" || true) Dateien"
done
echo "   Weiter mit tools/night_v28_chain.sh (Manifest, Fenster, Bloecke, Monolith, Training)."
