#!/usr/bin/env bash
# Tor 1 fuer v29-b04 gegen b03 (PREREG_moon_stack_order.md par.12.1, Fahrplan 32b).
#
# Das Training v29-b04 faehrt der Nutzer selbst in seiner Shell (2026-09-16,
# PID 33436). Diese Kette startet NICHTS davon; sie wartet, bis kein train.py
# mehr laeuft, faehrt dann ZUERST die leichte Abnahme-Sonde fuer die Tore (a)
# und (b) (Sekunden) und danach Tor 1: zwei Seeds a 200 Paaren, Blockgroesse 5,
# KEIN Frueh-Stopp, Champion-Spec beidseitig, mit Logs -- Befehle wie Schritt 4
# in night_v29_b04_moon_played_v2.sh.
#
# MODELLWAHL: `_brierbest.onnx` entsteht NUR, wenn die beste Brier-Epoche nicht
# die letzte ist (v29_program_agent_plan.md Nr. 12; feedback_never_wait_on_a_
# guessed_filename). Fehlt sie, ist das finale Modell der value-optimale Stand
# und wird genommen -- der Name steht im Log und im Artefakt (name-a bleibt
# v29-b04, die Datei wird ausgegeben).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
B=models/alphazero_v29-b03_brierbest.onnx
SPEC=models/frozen_champions/v28-b02/spec.json

# Gehaertete Wartebedingung (docs/pitfalls.md, Ketten-Wrapper): nur eine klare 0
# gilt als frei, und der Prozess muss PYTHON sein. Zusaetzlich zaehlt ein
# laufender Rust-Bau (cargo/rustc) als belegt -- ein Build ist Volllast, und
# Tor 1 ist eine Wanduhr-Messung.
maschine_frei() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { (\$_.CommandLine -match '[t]rain\.py|[p]aired_gating\.py|[f]rozen_referee_match\.py|[o]ffline_diagnosis|[c]ounterfactual_tiling' -and \$_.Name -match 'python') -or \$_.Name -match '^(cargo|rustc)' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}
echo "########## b04-TOR1-KETTE WARTET $(date +%F' '%H:%M:%S)"
while :; do
  maschine_frei && { echo "   Maschine frei ($(date +%H:%M:%S))"; break; }
  echo "   belegt ($(date +%H:%M:%S))"; sleep 120
done
sleep 30

if [ -f models/alphazero_v29-b04_brierbest.onnx ]; then
  A=models/alphazero_v29-b04_brierbest.onnx
elif [ -f models/alphazero_v29-b04.onnx ]; then
  A=models/alphazero_v29-b04.onnx
  echo "HINWEIS: kein _brierbest -- beste Epoche war die letzte, finales Modell wird genommen"
else
  echo "ABBRUCH: kein Modell v29-b04 gefunden -- Training gescheitert?"; exit 1
fi
for f in "$A" "$B" "$SPEC"; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
echo "   Modell A: $A"; ls -l "$A"

echo ""
echo "== 0) Tore (a)/(b): Mondkopf gegen Suchziel, b04 gegen b03 und b05 $(date +%H:%M:%S)"
python -X utf8 -u tools/probes/moon_head_target_probe.py \
  --models v29-b04="$A" v29-b03="$B" v29-b05=models/alphazero_v29-b05_brierbest.onnx \
  --out "$ART/moon_head_target_probe_b04.json"
echo "   Exit $? ($(date +%H:%M:%S))"

for SEED in 20261130 20261131; do
  OUT="$ART/tor1_v29-b04_vs_b03_s${SEED}.json"
  echo ""
  echo "===== Tor 1 b04 gegen b03, Seed $SEED $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$A" --spec-a "$SPEC" \
    --model-b "$B" --spec-b "$SPEC" \
    --name-a v29-b04 --name-b v29-b03 \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$SEED" --threads 10 --log-games \
    --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_tor1_b04_s${SEED}.json"
  echo "   Kennzahlen Exit $? ($(date +%H:%M:%S))"
done

echo ""
echo "########## b04-TOR1-KETTE FERTIG $(date +%F' '%H:%M:%S)"
echo "   Faellig danach: Manifest-Diff gegen b03 (GENAU moon_target_source label -> played"
echo "   plus Name), Verdikt in par.12.1 registrieren, Netz-Gesundheit par.6d Punkte 1-2."
