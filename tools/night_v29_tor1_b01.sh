#!/usr/bin/env bash
# Fahrplan Nr. 13 und 14: Tor 1 fuer v29-b01 gegen den Champion, ZWEI Seeds, dann Tor 2b
# und die Plattenpunkte auf denselben Logs.
#
# ZWECK DIESER KETTE: kein Stillstand (Nutzer 2026-09-13, 22:40: "Ich will dass v29 ohne
# stillstand lt. Fahrplan durchkommt"). Sie wartet auf das Ende von tools/night_v29_chain.sh
# und uebernimmt die Maschine sofort danach.
#
# Befehle woertlich aus PREREG_v29_window.md par.6 Punkt 7 und 8.
# SEEDS: 20261061 und 20261062 -- die Prereg laesst `<SEED>` offen; das Register hat bis
# 20261058 vergeben (Sims-Kurve und Leiter-Kante am 2026-09-13), diese beiden sind die
# naechsten freien. In par.9 zu registrieren, sobald das Ergebnis steht.
#
# REGEL v27, in par.6 registriert: KEIN dritter Seed, wenn beide positiv sind und kein
# Nullentscheid vorliegt. Der dritte Seed ist also eine Entscheidung NACH diesen beiden,
# kein Automatismus -- deshalb faehrt diese Kette genau zwei.
#
# WARTEBEDINGUNG, gehaertet (Filter maskiert, leere Antwort = belegt).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
CHAMP_SPEC=models/frozen_champions/v28-b02/spec.json
NEU=models/alphazero_v29-b01_brierbest.onnx
ALT=models/alphazero_v28-b02_brierbest.onnx

keine_last() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '[s]elf_play\.py|[t]rain\.py|[p]aired_gating|[b]uild_cache_incremental|[m]aturin|[c]argo ' -and \$_.Name -notmatch 'pwsh|powershell' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}

echo "== WARTEN auf v29-b01 und eine freie Maschine $(date +%F' '%H:%M:%S)"
while :; do
  if [ -f "$NEU" ] && keine_last; then
    echo "   b01 liegt, Maschine frei ($(date +%H:%M:%S))"
    break
  fi
  echo "   noch nicht ($(date +%H:%M:%S)): modell=$([ -f "$NEU" ] && echo da || echo fehlt)"
  sleep 300
done

for SEED in 20261061 20261062; do
  OUT="$ART/paired_gating_v29-b01_vs_v28-b02_s${SEED}.json"
  echo "== TOR 1, Seed $SEED $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$NEU" --spec-a "$CHAMP_SPEC" \
    --model-b "$ALT" --spec-b "$CHAMP_SPEC" \
    --name-a v29-b01 --name-b v28-b02 --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --seed "$SEED" --threads 10 --log-games \
    --no-promote-winner --out "$OUT"
  echo "   Gating Exit $? ($(date +%H:%M:%S))"

  echo "== TOR 2b und Plattenpunkte, Seed $SEED $(date +%H:%M:%S)"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  echo "   Spalten Exit $?"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_v29-b01_vs_v28-b02_s${SEED}.json"
  echo "   Platten Exit $? ($(date +%H:%M:%S))"
done

echo "== TOR 1 FERTIG $(date +%F' '%H:%M:%S)"
echo "   Naechster Fahrplanpunkt: Nr. 15 (Ablations-Schalter bauen, Maschine frei) -- dann b02."
echo "   Register-Zeilen und par.9-Eintrag macht der Koordinator; der DRITTE Seed ist ein"
echo "   Entscheid, kein Automatismus (Regel v27, par.6)."
