#!/usr/bin/env bash
# v32-ERZEUGUNG, alle drei Klassen. Generator: der amtierende Champion v31-b01.
#
# Nutzer-Entscheid 2026-09-22: *"du faehrst v32"* und *"du faehrst die Einstellungen wie v31"*.
# Dieses Skript ist darum die Fortschreibung von `tools/night_v31_generate.sh` (am 2026-09-22
# im Generationswechsel geloescht, Fassung in der Git-Historie unter HEAD~2). GEAENDERT sind
# genau drei Dinge, und nichts sonst:
#
#   1. GENERATOR  `v30-b02` -> `v31-b01`  (Champion seit 2026-09-20)
#   2. SEEDS      20260934/35/36 -> 20260938/39/40  (Vierer-Schritt je Generation,
#                 `docs/generation_loop.md`; v30 fuhr 20260930/31/32)
#   3. SPEC-NAME  `v30_generation.spec.json` -> `v31_generation.spec.json`
#                 (byte-identischer Inhalt, sha256 4a3f9db3..., nur nach dem GENERATOR benannt,
#                 damit das Lauf-Manifest selbsterklaerend ist)
#
# UNVERAENDERT, ausdruecklich: `--return-order-random-p 0.81`. Beim Schreiben stand hier ein
# Vorbehalt, die Gelegenheitsrate sei von 17,75 auf 28,0 Prozent gestiegen. Das war ein
# Zaehlfehler: die beiden Zahlen meinen verschiedene Kriterien (>= 3 gegen >= 2 Restplatten).
# Mit EINER Zaehlweise an beiden Korpora nachgemessen liegt die Rate bei 22,5 gegen 23,5
# Prozent, die Streurate bei 12,0 gegen 14,0 -- Ziel war 15. Die Dosis ist richtig
# eingestellt (`PREREG_dome_return_order.md` par.13, Berichtigung 2026-09-23).
#
# KEINE PIPE, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
export MOSAIC_STACK_DRAW_RESEARCH=1

MODEL=models/alphazero_v31-b01_brierbest.onnx
SPEC=models/v31_generation.spec.json
GEN=v31-b01

[ -f "$MODEL" ] || { echo "ABBRUCH: $MODEL fehlt"; exit 1; }
[ -f "$SPEC" ] || { echo "ABBRUCH: $SPEC fehlt"; exit 1; }
grep -q "return_order_randomized" engine/py/corpus_dataset.py \
  || { echo "ABBRUCH: die Policy-Maske fuer gestreute Zuege fehlt in corpus_dataset.py"; exit 2; }
python -X utf8 - <<'PYEOF' || exit 3
import json, sys, mosaic_rust
d = json.loads(mosaic_rust.engine_config_json())
p = d.get("return_order_random_p")
print(f"   engine_config: input_size {d.get('input_size')} num_actions {d.get('num_actions')} "
      f"contract {d.get('contract_hash')} engine {d.get('engine_version')} "
      f"stack_draw_research {d.get('stack_draw_research')} return_order_random_p {p}")
if str(d.get("input_size")) != "888" or str(d.get("num_actions")) != "414":
    print("ABBRUCH: Wheel traegt nicht 888/414"); sys.exit(3)
# NICHT auf return_order_random_p pruefen: hier laeuft ein eigener Prozess OHNE
# self_play.py, der Wert waere also nur der Env-Stand und sagt nichts ueber den Lauf.
# Die Dosis steht als CLI-Flag an jedem der drei Aufrufe unten.
PYEOF

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
wait_for_free_cpu "v32-Erzeugung"

echo ""
echo "== 1) Sockel (Traeger), 4.000 Partien -- policy-aktiv $(date +%F' '%H:%M:%S)"
python -X utf8 -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --version "${GEN}-policy" \
  --threads 11 --chunk 10 --per-file 10 --seed 20260938 --return-order-random-p 0.81 \
  --tau-argmax-from-move 1 --deviate-prob 1.0 --start-slot-random-p 0.15
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c "^selfplay_${GEN}-policy_")"

echo ""
echo "== 2) Schwarm a, 4.000 Partien -- value-only, temperiert $(date +%F' '%H:%M:%S)"
python -X utf8 -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --value-only --version "${GEN}-value-tempc" \
  --threads 11 --chunk 10 --per-file 10 --seed 20260939 --return-order-random-p 0.81 \
  --action-temp 2 --deviate-prob 1.0 --start-slot-random-p 0.15
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c "^selfplay_${GEN}-value-tempc_")"

echo ""
echo "== 3) Schwarm b, 4.000 Identitaeten -- value-only, Ausflug $(date +%F' '%H:%M:%S)"
python -X utf8 -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --value-only --version "${GEN}-value-excursion" \
  --threads 11 --chunk 10 --per-file 10 --seed 20260940 --return-order-random-p 0.81 \
  --excursion-prob 1.0 --tau-argmax-from-move 1 --no-root-noise --start-slot-random-p 0.15
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c "^selfplay_${GEN}-value-excursion_")"

echo ""
echo "== v32-ERZEUGUNG FERTIG $(date +%F' '%H:%M:%S)"
echo "   Naechster Schritt: Wiedervorlage am ersten Record (traegt er return_order_randomized?),"
echo "   Tor 0 / Tor 2a je Klasse, dann Fenster und Kette nach PREREG_v32_window.md."
