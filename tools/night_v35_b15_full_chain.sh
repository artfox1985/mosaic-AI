#!/usr/bin/env bash
# Volle Breite v35-b15 gegen v35-b02 (PREREG_v35_window.md par.19.5c, Nutzer-Entscheid 2026-10-08 GEGEN die
# Lesart par.19.0; registriert vor dem Lauf). Nur Gating, kein Training.
# A = alphazero_v35-b15_best.onnx (b15 hat KEIN _brierbest: Brier-Minimum Epoche 2 = best_epoch, Auswahl
# per tools/brier_best_checkpoint.py aus manifest_train_v35-b15_20261008_133129.json), B = v35-b02_brierbest,
# Spec v34-b01_brierbest beidseits, @400, Blockgroesse 5, --log-games, --resume, Seeds 20261600/20261601 a
# 200 Paare (SPRT alpha = beta = 0,001 darf frueher stoppen), Stufenregel: dritter Seed 20261602 nur, wenn
# genau EIN Seed einzeln >= +1,96 liegt. Je Seed arena_column_probe und plate_points_from_arena (sechs
# Standard-Kennzahlen), zum Schluss gating_block_z gepoolt und die Lesart nach dem Kriterium von par.12:
# Block-z >= +1,96 oder gepoolt >= 52,5 % ohne Gegenbefund = b15 traegt gegen b02. Die Schnellblick-Seeds
# 20261700/01 gehen NICHT in die Poolung ein (par.19.5c).
# Vorlage: tools/tree_reuse_arena_chain.sh (gate, Stufenregel, Kennzahlen); Warten wie
# tools/night_v35_b09_b10_chain.sh:122-133.
#
# KOSTEN (HERLEITUNG par.19.5c, nicht gemessen): 2 x rund 2 h (18 s je Partie), dritter Seed rund 2 h mehr.
#
# Start (Terminal-Tab, keine Pipe, keine Umleitung):  bash tools/night_v35_b15_full_chain.sh
# Darf vor dem Ende der Vorgaenger gestartet werden: wartet, bis kein Prozess mit night_v35_<...>_chain
# (ausser dieser Kette und der b16-Kette) oder tree_reuse_arena_chain in der Kommandozeile mehr laeuft
# (Deckel 40 h). Die b16-Kette ist ausgenommen, weil SIE auf DIESE wartet (Nutzer-Reihenfolge b08b, b15,
# b16); beide warteten sonst aufeinander.
# Wiederaufnahme: einfach neu starten. Ein liegendes Artefakt eines Seeds wird uebersprungen, ein
# Zwischenstand <out>.partial.json von paired_gating.py --resume fortgesetzt.
set -u
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"

ARM=v35-b15
OPP=v35-b02
A_MODEL=models/alphazero_v35-b15_best.onnx
B_MODEL=models/alphazero_v35-b02_brierbest.onnx
SPEC=models/v34-b01_brierbest.spec.json                      # beidseits (par.19.5c)
ART=evaluations/artifacts
SEEDS="20261600 20261601"
STAGE_SEED=20261602
PRED_PATTERN='[n]ight_v35_(?!b15_full_|b16_)[A-Za-z0-9_]*_chain|[t]ree_reuse_arena_chain'
T_CHAIN0=$(date +%s)

# --- Fruehe Pruefung VOR dem Warten -----------------------------------------------------------------
for f in "$A_MODEL" "$B_MODEL" "$SPEC" tools/paired_gating.py tools/gating_block_z.py \
         tools/brier_best_checkpoint.py tools/probes/arena_column_probe.py tools/plate_points_from_arena.py; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
[ -f models/alphazero_v35-b15_brierbest.onnx ] && { echo "ABBRUCH: models/alphazero_v35-b15_brierbest.onnx liegt -- par.19.5c nennt _best, von Hand klaeren"; exit 1; }
SEL=$(python -X utf8 tools/brier_best_checkpoint.py "$ARM" --ext onnx)
[ "$SEL" = "$A_MODEL" ] || { echo "ABBRUCH: brier_best_checkpoint.py waehlt '$SEL' statt $A_MODEL"; exit 1; }
SEL=$(python -X utf8 tools/brier_best_checkpoint.py "$OPP" --ext onnx)
[ "$SEL" = "$B_MODEL" ] || { echo "ABBRUCH: brier_best_checkpoint.py waehlt fuer $OPP '$SEL' statt $B_MODEL"; exit 1; }
echo "Fruehpruefung GRUEN: A $A_MODEL, B $B_MODEL (beide = Brier-beste Wahl aus dem Manifest), Spec $SPEC"

# --- Warten auf die Vorgaenger (Bauform night_v35_b09_b10_chain.sh:122-133) -------------------------
echo "########## v35-b15-VOLLE-BREITE WARTET auf night_v35_*_chain (ausser b15_full/b16) und tree_reuse_arena_chain $(date +%F' '%H:%M:%S)"
tick=0
while :; do
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '$PRED_PATTERN' }).Count" 2>/dev/null | tr -d '\r[:space:]')
  [ "$n" = "0" ] && break
  tick=$((tick + 1))
  [ $tick -gt 2400 ] && { echo "STOPP: Vorgaenger-Ketten nach 40 h noch nicht fertig"; exit 1; }
  [ $((tick % 10)) -eq 1 ] && echo "   Vorgaenger-Kette(n) laufen noch (Antwort '${n}', $(date +%H:%M:%S))"
  sleep 60
done
echo "   Vorgaenger-Ketten beendet ($(date +%H:%M:%S))"

echo "########## VOLLE BREITE $ARM gegen $OPP (par.19.5c)   Start $(date +%F' '%H:%M:%S)"
wait_for_free_cpu "b15 volle Breite"

gate() {  # $1 Seed (Bauform tree_reuse_arena_chain.sh:37-60)
  local OUT="$ART/gating_${ARM}_vs_${OPP}_s${1}.json"
  local G0
  G0=$(date +%s)
  if [ -f "$OUT" ]; then
    echo "   $OUT liegt schon -- Seed $1 uebersprungen (Wiederaufnahme)"
  else
    echo ""
    echo "===== $ARM gegen $OPP, Seed $1   Start $(date +%F' '%H:%M:%S)"
    [ -f "${OUT}.partial.json" ] && echo "   Zwischenstand liegt -- --resume setzt fort"
    python -X utf8 -u tools/paired_gating.py \
      --model-a "$A_MODEL" --spec-a "$SPEC" --model-b "$B_MODEL" --spec-b "$SPEC" \
      --name-a "$ARM" --name-b "$OPP" \
      --sims-a 400 --sims-b 400 --c-puct 1.5 \
      --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
      --seed "$1" --threads 10 --log-games --no-promote-winner --out "$OUT" --resume
    echo "   Exit $? ($(date +%H:%M:%S))"
    [ -f "$OUT" ] || { echo "STOPP: kein Artefakt fuer Seed $1"; return 1; }
  fi
  if [ ! -f "$ART/plate_points_${ARM}_vs_${OPP}_s${1}.json" ]; then
    python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
    python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
      --out "$ART/plate_points_${ARM}_vs_${OPP}_s${1}.json"
  fi
  echo "   Ende Seed $1: $(date +%F' '%H:%M:%S), $(( $(date +%s) - G0 )) s Wanduhr"
  return 0
}

# Block-z eines Artefakts >= +1,96? (Funktion von gating_block_z.py, nicht die Textausgabe)
seed_clears() {
  python -X utf8 - "$1" <<'PYEOF'
import os, sys
sys.path.insert(0, os.path.join(os.getcwd(), "tools"))
from gating_block_z import block_shares, block_z
z = block_z(block_shares(sys.argv[1]))["z"]
sys.exit(0 if z is not None and z >= 1.96 else 1)
PYEOF
}

DONE=""
for s in $SEEDS; do gate "$s" || exit 2; DONE="$DONE $ART/gating_${ARM}_vs_${OPP}_s${s}.json"; done
echo ""
echo "== Block-z je Seed und gepoolt"
python -X utf8 tools/gating_block_z.py $DONE
CLEAR=0
for f in $DONE; do seed_clears "$f" && CLEAR=$((CLEAR+1)); done
echo "   Seeds einzeln >= +1,96: $CLEAR von 2"
if [ "$CLEAR" = "1" ]; then
  echo "   Stufenregel: genau ein Seed -> dritter Seed $STAGE_SEED"
  gate "$STAGE_SEED" || exit 2
  DONE="$DONE $ART/gating_${ARM}_vs_${OPP}_s${STAGE_SEED}.json"
  echo ""
  echo "== Block-z je Seed und gepoolt (drei Seeds)"
  python -X utf8 tools/gating_block_z.py $DONE
fi

echo ""
echo "########## VOLLE BREITE $ARM FERTIG $(date +%F' '%H:%M:%S), $(( $(date +%s) - T_CHAIN0 )) s Wanduhr -- Zusammenfassung"
python -X utf8 - $DONE <<'PYEOF'
import json, os, sys
sys.path.insert(0, os.path.join(os.getcwd(), "tools"))
from gating_block_z import block_shares, block_z
def fmt(x):
    return "?" if x is None else f"{x:.2f}"
a = n = 0
blocks = []
for p in sys.argv[1:]:
    d = json.load(open(p, encoding="utf-8"))
    na = d.get("n_games_total") or 0
    z = block_z(block_shares(p))["z"]
    sa, sb = d.get("avg_score_a"), d.get("avg_score_b")
    marg = f"{sa - sb:+.2f}" if sa is not None and sb is not None else "?"
    lz = d.get("laufzeit") or {}
    print(f"   {os.path.basename(p)}: {d['a_wins_total']}:{d.get('b_wins_total')} von {na}, "
          f"Siegquote {d['a_wins_total'] / na if na else float('nan'):.4f}, Block-z {'n/a' if z is None else f'{z:+.2f}'}, "
          f"SPRT {d.get('sprt_verdict')}, Punkte {fmt(sa)} / {fmt(sb)} (Margin {marg}), "
          f"Strafsteine {fmt(d.get('avg_floor_a'))} / {fmt(d.get('avg_floor_b'))}, "
          f"{lz.get('wanduhr_s')} s, {lz.get('s_je_partie')} s je Partie")
    a += d["a_wins_total"]; n += na
    blocks.extend(block_shares(p))
z = block_z(blocks)["z"] if blocks else None
wr = a / n if n else None
print(f"   gepoolt ({len(sys.argv) - 1} Seeds): {a}/{n} = {'n/a' if wr is None else f'{wr:.4f}'}, "
      f"Block-z {'n/a' if z is None else f'{z:+.2f}'} ({len(blocks)} Bloecke)")
print("\nLESART par.19.5c (Kriterium par.12, mechanisch, Verdikt beim Koordinator):")
if wr is None:
    print("   keine Partien -- keine Lesart")
elif (z is not None and z >= 1.96) or wr >= 0.525:
    print("   -> Kriterium ERFUELLT (Block-z >= +1,96 oder gepoolt >= 52,5 %): b15 traegt gegen b02, SOFERN kein"
          " Gegenbefund (Kennzahlen pruefen); erst das begruendet einen Vorzug vor b02 (par.19)")
else:
    print("   -> Kriterium NICHT erfuellt: kein Hebel auch in voller Breite (bestaetigt die Lesart par.19.0)")
print("   Spalten und Plattenpunkte je Seed: arena_columns_gating_v35-b15_vs_v35-b02_*.json und"
      " plate_points_v35-b15_vs_v35-b02_*.json in evaluations/artifacts")
PYEOF
echo ""
echo "   Faellig: Verdikt par.19.5c in PREREG_v35_window.md, sechs Kennzahlen je Seite, Laufzeiten in Prereg und"
echo "   docs/measured_runtimes.md, Kopf Zeile 1 und Index (python tools/generate_prereg_index.py)."
