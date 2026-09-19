#!/usr/bin/env bash
# v31-ERZEUGUNG, alle drei Klassen. Generator: der neue Champion v30-b02.
# Zuschnitt und Lesart: evaluations/PREREG_v31_window.md.
#
# WAS SICH GEGEN v30 AENDERT, und nur das:
#   1. Generator `v30-b02` -- 888/414 von Haus aus, KEINE Polsterung noetig (v29-b11 war
#      der gepolsterte Champion; seine Policy-Zeilen 406-413 waren gemessen NULL).
#   2. `--return-order-random-p 0.81` -- die Rueckgabe-Streuung, seit 2026-09-19 im
#      KNOTEN-Weg statt im verdraengten Aufloeser (PREREG_dome_return_order.md 12.12).
#      Dosis exakt ueber die Verteilung der Gelegenheiten gerechnet (12.12a): Ziel ist
#      "in 15 Prozent der Partien mindestens einmal", Obergrenze waeren 17,75 Prozent.
#      ALS CLI-FLAG, NICHT als Umgebungsvariable (Fehlschlag 2026-09-19, 20:15):
#      `self_play.py` SETZT `MOSAIC_RETURN_ORDER_RANDOM_P` selbst aus dem CLI-Wert
#      (Z.240, Default 0.0) -- ein vorher exportierter Wert wird ueberschrieben, und
#      zwar stillschweigend. Eine Wheel-Abfrage in einem SEPAREN Prozess zeigt dann
#      0.81, waehrend die Erzeugung mit 0.0 laeuft: genau so ist der erste v31-Anlauf
#      45 Dateien weit ohne eine einzige Streuung gekommen.
#   3. Seeds 20260934/35/36 (Fortschreibung der 30/31/32-Reihe aus v30).
#
# VORBEDINGUNG, geprueft vor dem Start: die Maske fuer gestreute Zuege muss im
# Datensatzbau stehen (corpus_dataset.py, eigene Bedingung auf `return_order_randomized`,
# NICHT ueber policy_target_valid -- beide Ketten fahren MOSAIC_IGNORE_POLICY_TARGET_VALID=1).
# Ohne sie lernt der Policy-Kopf den Zufall.
#
# KEINE PIPE, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
export MOSAIC_STACK_DRAW_RESEARCH=1

MODEL=models/alphazero_v30-b02_brierbest.onnx
SPEC=models/v30_generation.spec.json
GEN=v30-b02

[ -f "$MODEL" ] || { echo "ABBRUCH: $MODEL fehlt"; exit 1; }
[ -f "$SPEC" ] || { echo "ABBRUCH: $SPEC fehlt"; exit 1; }
grep -q "return_order_randomized" engine/py/corpus_dataset.py \
  || { echo "ABBRUCH: die Policy-Maske fuer gestreute Zuege fehlt in corpus_dataset.py"; exit 2; }
python -X utf8 - <<'PYEOF' || exit 3
import json, sys, mosaic_rust
d = json.loads(mosaic_rust.engine_config_json())
p = d.get("return_order_random_p")
print(f"   engine_config: input_size {d.get('input_size')} num_actions {d.get('num_actions')} "
      f"contract {d.get('contract_hash')} stack_draw_research {d.get('stack_draw_research')} "
      f"return_order_random_p {p}")
if str(d.get("input_size")) != "888" or str(d.get("num_actions")) != "414":
    print("ABBRUCH: Wheel traegt nicht 888/414"); sys.exit(3)
# NICHT auf return_order_random_p pruefen: hier laeuft ein eigener Prozess OHNE
# self_play.py, der Wert waere also nur der Env-Stand und sagt nichts ueber den Lauf.
# Die Dosis steht als CLI-Flag an jedem der drei Aufrufe unten.
PYEOF

busy() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '[s]elf_play\.py|[t]rain\.py|[p]aired_gating|[f]rozen_referee|[b]uild_cache|[c]argo|[m]aturin' -and \$_.Name -match 'python' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" != "0" ]
}
echo "== WARTEN auf eine freie Maschine $(date +%F' '%H:%M:%S)"
while busy; do echo "   belegt ($(date +%H:%M:%S))"; sleep 120; done
echo "   frei ($(date +%H:%M:%S))"

echo ""
echo "== 1) Sockel (Traeger), 4.000 Partien -- policy-aktiv $(date +%F' '%H:%M:%S)"
python -X utf8 -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --version "${GEN}-policy" \
  --threads 11 --chunk 10 --per-file 10 --seed 20260934 --return-order-random-p 0.81 \
  --tau-argmax-from-move 1 --deviate-prob 1.0 --start-slot-random-p 0.15
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c "^selfplay_${GEN}-policy_")"

echo ""
echo "== 2) Schwarm a, 4.000 Partien -- value-only, temperiert $(date +%F' '%H:%M:%S)"
python -X utf8 -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --value-only --version "${GEN}-value-tempc" \
  --threads 11 --chunk 10 --per-file 10 --seed 20260935 --return-order-random-p 0.81 \
  --action-temp 2 --deviate-prob 1.0 --start-slot-random-p 0.15
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c "^selfplay_${GEN}-value-tempc_")"

echo ""
echo "== 3) Schwarm b, 4.000 Identitaeten -- value-only, Ausflug $(date +%F' '%H:%M:%S)"
python -X utf8 -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --value-only --version "${GEN}-value-excursion" \
  --threads 11 --chunk 10 --per-file 10 --seed 20260936 --return-order-random-p 0.81 \
  --excursion-prob 1.0 --tau-argmax-from-move 1 --no-root-noise --start-slot-random-p 0.15
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c "^selfplay_${GEN}-value-excursion_")"

echo ""
echo "== v31-ERZEUGUNG FERTIG $(date +%F' '%H:%M:%S)"
echo "   Naechster Schritt: Wiedervorlage am ersten Record (traegt er return_order_randomized?),"
echo "   Tor 0 / Tor 2a je Klasse, dann Fenster und Kette nach PREREG_v31_window.md."
