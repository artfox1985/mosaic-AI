#!/usr/bin/env bash
# v33-ERZEUGUNG, alle drei Klassen. Generator: der amtierende Champion v32-b01.
#
# Fortschreibung von `tools/night_v32_generate.sh` (im Generationswechsel am 2026-09-25
# geloescht, Fassung in der Git-Historie). Rezept und Lesart:
# evaluations/PREREG_v33_window.md par.6. GEAENDERT sind genau vier Dinge:
#
#   1. GENERATOR  `v31-b01` -> `v32-b01`  (Champion seit 2026-09-25)
#   2. SEEDS      20260938/39/40 -> 20260942/43/44  (Vierer-Schritt, docs/generation_loop.md)
#   3. SPEC-NAME  `v31_generation.spec.json` -> `v32_generation.spec.json`
#                 (byte-gleicher Inhalt, sha256 4a3f9db3..., nach dem GENERATOR benannt)
#   4. SCHWARM a  laeuft OHNE Huellenknopf, unter eigener Klassen-Endung und eigener Spec:
#                 `value-tempc-nohull`, `models/v32_generation_nohull.spec.json`
#                 (identisch bis auf `envelope_search_c: 0.0`, sha256 ada4238c...).
#                 Nutzer-Entscheid 2026-09-25, PREREG_geometric_envelope.md par.14d:
#                 der Ausflug bleibt huellen-an, weil er die einzige Klasse mit unverzerrten
#                 Value-Zielen ist.
#
# UNVERAENDERT: `--return-order-random-p 0.81` (Dosis belegt, PREREG_dome_return_order.md
# par.13), 3 x 4.000 Partien, 100 Sims, 11 Threads, Klassen-Flags wie v32.
#
# Das Lauf-Manifest traegt seit 2026-09-25 Pfad, sha256 und INHALT der Spec (`spec_file`);
# die huellenfreie Klasse ist also auch hinterher am Manifest erkennbar, nicht nur am Namen.
#
# KEINE PIPE, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
export MOSAIC_STACK_DRAW_RESEARCH=1

MODEL=models/alphazero_v32-b01_brierbest.onnx
SPEC=models/v32_generation.spec.json
SPEC_NOHULL=models/v32_generation_nohull.spec.json
GEN=v32-b01

[ -f "$MODEL" ] || { echo "ABBRUCH: $MODEL fehlt"; exit 1; }
[ -f "$SPEC" ] || { echo "ABBRUCH: $SPEC fehlt"; exit 1; }
[ -f "$SPEC_NOHULL" ] || { echo "ABBRUCH: $SPEC_NOHULL fehlt"; exit 1; }
grep -q "return_order_randomized" engine/py/corpus_dataset.py \
  || { echo "ABBRUCH: die Policy-Maske fuer gestreute Zuege fehlt in corpus_dataset.py"; exit 2; }
grep -q '"spec_file"' selfplay_manifest.py \
  || { echo "ABBRUCH: das Lauf-Manifest schreibt die Spec nicht (spec_file fehlt)"; exit 2; }
python -X utf8 - "$SPEC" "$SPEC_NOHULL" <<'PYEOF' || exit 3
import json, sys, mosaic_rust
d = json.loads(mosaic_rust.engine_config_json())
print(f"   engine_config: input_size {d.get('input_size')} num_actions {d.get('num_actions')} "
      f"contract {d.get('contract_hash')} engine {d.get('engine_version')}")
if str(d.get("input_size")) != "888" or str(d.get("num_actions")) != "414":
    print("ABBRUCH: Wheel traegt nicht 888/414"); sys.exit(3)
# Die beiden Specs duerfen sich in GENAU einem Feld unterscheiden -- sonst waere die
# huellenfreie Klasse nicht einfaktoriell gegen die anderen zu lesen.
a = json.load(open(sys.argv[1], encoding="utf-8"))
b = json.load(open(sys.argv[2], encoding="utf-8"))
diff = {k: (a.get(k), b.get(k)) for k in set(a) | set(b) if a.get(k) != b.get(k)}
print(f"   Spec-Unterschied: {diff}")
if diff != {"envelope_search_c": (1.0, 0.0)}:
    print("ABBRUCH: die Specs unterscheiden sich nicht in genau envelope_search_c 1.0 -> 0.0")
    sys.exit(3)
PYEOF

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
wait_for_free_cpu "v33-Erzeugung"

echo ""
echo "== 1) Sockel (Traeger), 4.000 Partien -- policy-aktiv, MIT Huelle $(date +%F' '%H:%M:%S)"
python -X utf8 -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --version "${GEN}-policy" \
  --threads 11 --chunk 10 --per-file 10 --seed 20260942 --return-order-random-p 0.81 \
  --tau-argmax-from-move 1 --deviate-prob 1.0 --start-slot-random-p 0.15
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c "^selfplay_${GEN}-policy_")"

echo ""
echo "== 2) Schwarm a, 4.000 Partien -- value-only, temperiert, OHNE Huelle $(date +%F' '%H:%M:%S)"
python -X utf8 -u self_play.py --mode network --model "$MODEL" --spec "$SPEC_NOHULL" \
  --games 4000 --sims 100 --value-only --version "${GEN}-value-tempc-nohull" \
  --threads 11 --chunk 10 --per-file 10 --seed 20260943 --return-order-random-p 0.81 \
  --action-temp 2 --deviate-prob 1.0 --start-slot-random-p 0.15
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c "^selfplay_${GEN}-value-tempc-nohull_")"

echo ""
echo "== 3) Schwarm b, 4.000 Identitaeten -- value-only, Ausflug, MIT Huelle $(date +%F' '%H:%M:%S)"
python -X utf8 -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --value-only --version "${GEN}-value-excursion" \
  --threads 11 --chunk 10 --per-file 10 --seed 20260944 --return-order-random-p 0.81 \
  --excursion-prob 1.0 --tau-argmax-from-move 1 --no-root-noise --start-slot-random-p 0.15
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c "^selfplay_${GEN}-value-excursion_")"

echo ""
echo "== v33-ERZEUGUNG FERTIG $(date +%F' '%H:%M:%S)"
echo "   Naechster Schritt: Manifest-Diff je Klasse gegen v32 (erwartet: model, seed, spec,"
echo "   version -- und bei Schwarm a zusaetzlich spec_file.content.envelope_search_c 1.0 -> 0.0),"
echo "   Wiedervorlage am ersten Record, Tor 2a am Sockel, Vielfaltssonde an Schwarm a"
echo "   (PREREG_geometric_envelope.md par.14d), dann Fenster und Kette (night_v33_chain.sh)."
