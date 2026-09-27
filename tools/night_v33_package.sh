#!/usr/bin/env bash
# Nachtkette des v33-Pakets (2026-09-27), alles auf dem Champion v32-b01 (Nutzer: "derzeit keine
# Promotion"), alle Schritte CPU und damit NACHEINANDER:
#   1) Tor 1 fuer v33-b02 gegen v32-b01          PREREG_v33_window.md par.6e   (~3,4 h)
#   2) E1-Kostentor: je 100 Self-Play-Partien     PREREG_evaluator_pretests.md par.5b (~15 min)
#   3) E1-A/B: Champion mit gegen ohne Einpass    PREREG_evaluator_pretests.md par.5b (~3,4 h)
#   4) R5-A/B: Runde 5 Netz gegen Loeser          PREREG_r5_net_vs_solver.md par.3    (~3,4 h)
# Specs mit genau EINEM Feld Unterschied: models/v33_gating_e1.spec.json
# (single_pass_other_val 1), models/v33_gating_r5net.spec.json (r5_net_solver 0).
#
# KEINE PIPE hinter langen Laeufen, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
CHAMP=models/alphazero_v32-b01_brierbest.onnx
SPEC=models/v33_gating.spec.json
SPEC_E1=models/v33_gating_e1.spec.json
SPEC_R5=models/v33_gating_r5net.spec.json
B02=models/alphazero_v33-b02_brierbest.onnx
GEN_SPEC=models/v32_generation.spec.json
for f in "$CHAMP" "$SPEC" "$SPEC_E1" "$SPEC_R5" "$B02" "$GEN_SPEC"; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
python -X utf8 - "$SPEC" "$SPEC_E1" "$SPEC_R5" <<'PYEOF' || exit 2
import json, sys
base, e1, r5 = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:4])
def diff(a, b): return {k: (a.get(k), b.get(k)) for k in set(a) | set(b) if a.get(k) != b.get(k)}
assert diff(base, e1) == {"single_pass_other_val": (None, 1)}, diff(base, e1)
assert diff(base, r5) == {"r5_net_solver": (None, 0)}, diff(base, r5)
print("   Specs: je genau ein Feld Unterschied -- OK")
PYEOF

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
wait_for_free_cpu "v33-Paket"
echo "== v33-PAKET Start $(date +%F' '%H:%M:%S)"

gate() {  # $1 Modell A, $2 Spec A, $3 Name A, $4 Modell B, $5 Spec B, $6 Name B, $7 Seed, $8 SPRT alpha, $9 Ausgabe
  echo ""
  echo "===== $3 gegen $6, Seed $7 $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$1" --spec-a "$2" --model-b "$4" --spec-b "$5" --name-a "$3" --name-b "$6" \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha "$8" --sprt-beta "$8" \
    --seed "$7" --threads 10 --log-games --no-promote-winner --out "$9"
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$9"
  python -X utf8 -u tools/plate_points_from_arena.py "$9" --block 5 \
    --out "${9%.json}_plate_points.json"
}

# --- 1) Tor 1 fuer b02 (par.6e): gleiche Seeds wie Tor 1 von b01, SPRT wie dort ---------------
echo ""
echo "== 1) Tor 1: v33-b02 gegen v32-b01 (par.6e) $(date +%F' '%H:%M:%S)"
for S in 20261600 20261601; do
  gate "$B02" "$SPEC" v33-b02 "$CHAMP" "$SPEC" v32-b01 "$S" 0.001 "$ART/gating_v33-b02_vs_v32-b01_s${S}.json"
done
N_SIG=$(python -X utf8 tools/gating_block_z.py --json \
  "$ART/gating_v33-b02_vs_v32-b01_s20261600.json" "$ART/gating_v33-b02_vs_v32-b01_s20261601.json" \
  | python -c "import sys,json; d=json.load(sys.stdin); print(sum(r['z'] >= 1.96 for r in d['per_seed']))")
echo "   Stufenregel: Seeds einzeln >= +1,96: ${N_SIG:-?} von 2"
if [ "$N_SIG" = "1" ]; then
  echo "   -> dritter Seed 20261602 (par.2a)"
  gate "$B02" "$SPEC" v33-b02 "$CHAMP" "$SPEC" v32-b01 20261602 0.001 "$ART/gating_v33-b02_vs_v32-b01_s20261602.json"
fi
python -X utf8 tools/gating_block_z.py "$ART"/gating_v33-b02_vs_v32-b01_s2026160*.json

# --- 2) E1-Kostentor (par.5b): gleiche Seeds, gleiche Threads, Sockel-Einstellung -------------
# Mit Knopf ueber die ENV (sie gilt auch fuer die Label-Pfade, par.5b Bau-Stand); die
# Erzeugungs-Spec traegt das Feld nicht, also gilt der Env-Default.
echo ""
echo "== 2) E1-Kostentor: je 100 Partien ohne / mit Einpass-Konsum $(date +%F' '%H:%M:%S)"
mkdir -p data/probe_e1gate
for ARMV in off on; do
  if [ "$ARMV" = on ]; then export MOSAIC_SINGLE_PASS_OTHER_VAL=1; else unset MOSAIC_SINGLE_PASS_OTHER_VAL; fi
  MOSAIC_DATA_DIR=data/probe_e1gate MOSAIC_STACK_DRAW_RESEARCH=1 python -X utf8 -u self_play.py --mode network --model "$CHAMP" \
    --spec "$GEN_SPEC" --games 100 --sims 100 --value-only --version "e1gate-$ARMV" \
    --threads 11 --chunk 10 --per-file 10 --seed 20261699 --return-order-random-p 0.81 \
    --tau-argmax-from-move 1 --deviate-prob 1.0 --start-slot-random-p 0.15
  echo "   e1gate-$ARMV Exit $? ($(date +%H:%M:%S))"
done
unset MOSAIC_SINGLE_PASS_OTHER_VAL
python -X utf8 - <<'PYEOF'
import glob, json
res = {}
for arm in ("off", "on"):
    m = sorted(glob.glob(f"data/probe_e1gate/manifest_e1gate-{arm}_*.json"))[-1]
    d = json.load(open(m, encoding="utf-8"))
    res[arm] = (d.get("laufzeit") or {}).get("s_je_partie"), d.get("engine_config", {}).get("single_pass_other_val")
    print(f"   {arm}: {res[arm][0]} s je Partie, engine_config.single_pass_other_val = {res[arm][1]}")
off, on = res["off"][0], res["on"][0]
if off and on:
    print(f"   Ersparnis: {100 * (1 - on / off):.1f} Prozent -> je 4.000er-Klasse rund {4000 * (off - on) / on:.0f} Partien mehr in derselben Zeit")
PYEOF

# --- 3) E1-A/B (par.5b): Champion mit Knopf gegen ohne, fester Umfang --------------------------
echo ""
echo "== 3) E1-A/B: v32-b01 mit Einpass (A) gegen ohne (B) $(date +%F' '%H:%M:%S)"
for S in 20261690 20261691; do
  gate "$CHAMP" "$SPEC_E1" v32-b01-e1 "$CHAMP" "$SPEC" v32-b01 "$S" 1e-12 "$ART/ab_e1_v32-b01_s${S}.json"
done
python -X utf8 tools/gating_block_z.py "$ART"/ab_e1_v32-b01_s2026169[01].json

# --- 4) R5-A/B (PREREG_r5_net_vs_solver.md par.3): Netz in Runde 5 (A) gegen Loeser (B) ---------
echo ""
echo "== 4) R5-A/B: v32-b01 Netzsuche in Runde 5 (A) gegen Loeser (B) $(date +%F' '%H:%M:%S)"
for S in 20261670 20261671; do
  gate "$CHAMP" "$SPEC_R5" v32-b01-r5net "$CHAMP" "$SPEC" v32-b01 "$S" 1e-12 "$ART/ab_r5net_v32-b01_s${S}.json"
done
python -X utf8 tools/gating_block_z.py "$ART"/ab_r5net_v32-b01_s2026167[01].json

echo ""
echo "########## v33-PAKET FERTIG $(date +%F' '%H:%M:%S)"
