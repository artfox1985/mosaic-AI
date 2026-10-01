#!/usr/bin/env bash
# Kostentor der v34-Erzeugung (evaluations/PREREG_v34_window.md par.5 Punkt 3, Ergebnis par.8):
# je 100 Partien Sockel-Einstellung (Klasse `policy` aus models/v34.recipe.json, Flag fuer Flag),
# E1 in BEIDEN Armen an; Arm "r5solver" ohne, Arm "r5net" mit MOSAIC_R5_NET_SOLVER=0.
# Ohne --recipe, weil der Rezept-Waechter r5_net_solver false erwartet und den Loeser-Arm
# abbrechen wuerde; beide Arme tragen darum dieselben expliziten Flags, nur die Env unterscheidet
# sich. Muster: tools/night_v33_package.sh Schritt 2 (E1-Kostentor; Fassung in der Git-Historie).
#
# KEINE PIPE, keine eigene Umleitung; als DATEI starten, exklusiv.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
GEN=models/alphazero_v33-b01_brierbest.onnx
SPEC=models/v33_generation.spec.json
OUT=data/probe_v34costgate
for f in "$GEN" "$SPEC"; do [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }; done
mkdir -p "$OUT"
echo "== v34-Kostentor Start $(date +%F' '%H:%M:%S)"
export MOSAIC_STACK_DRAW_RESEARCH=1 MOSAIC_SINGLE_PASS_OTHER_VAL=1
for ARM in r5solver r5net; do
  if [ "$ARM" = r5net ]; then export MOSAIC_R5_NET_SOLVER=0; else unset MOSAIC_R5_NET_SOLVER; fi
  echo "===== $ARM $(date +%H:%M:%S)"
  MOSAIC_DATA_DIR="$OUT" python -X utf8 -u self_play.py --mode network --model "$GEN" --spec "$SPEC" \
    --games 100 --sims 100 --threads 11 --chunk 10 --per-file 10 --seed 20261698 \
    --version "costgate-$ARM" --return-order-random-p 0.81 --tau-argmax-from-move 1 \
    --start-slot-random-p 0.15 --tie-mirror-p 0.5 --label-rng-split --excursion-reshuffle \
    --deviate-prob 1.0
  echo "   costgate-$ARM Exit $? ($(date +%H:%M:%S))"
done
unset MOSAIC_R5_NET_SOLVER
python -X utf8 - "$OUT" <<'PYEOF'
import glob, json, sys
out = sys.argv[1]
res = {}
for arm in ("r5solver", "r5net"):
    m = sorted(glob.glob(f"{out}/manifest_costgate-{arm}_*.json"))[-1]
    d = json.load(open(m, encoding="utf-8"))
    ec = d.get("engine_config", {})
    res[arm] = (d.get("laufzeit") or {}).get("s_je_partie")
    print(f"   {arm}: {res[arm]} s je Partie, laufzeit {d.get('laufzeit')}, "
          f"single_pass_other_val={ec.get('single_pass_other_val')} r5_net_solver={ec.get('r5_net_solver')}")
a, b = res["r5solver"], res["r5net"]
if a and b:
    print(f"   Netz in Runde 5 gegen Loeser: {100 * (b / a - 1):+.1f} Prozent je Partie")
PYEOF
echo "########## v34-Kostentor FERTIG $(date +%F' '%H:%M:%S)"
