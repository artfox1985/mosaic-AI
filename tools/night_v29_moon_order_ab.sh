#!/usr/bin/env bash
# Fahrplan Nr. 28: A/B Mondstapel-Fan-out an gegen aus
# (PREREG_moon_stack_order.md par.4, Stufe 1).
#
# Beide Seiten dasselbe Modell (amtierender Champion v28-b02) auf demselben Wheel,
# unterschieden durch GENAU ein Spec-Feld (geprueft: 14 Felder je Datei, ein
# Unterschied: `moon_order_variants` 1 gegen 0).
#   1 = Bestand: die Suche faechert die Reihenfolge der Mondsteine nach einem
#       Sonnenzug als Kandidaten auf (net_mcts.rs:2241-2255).
#   0 = nur die kanonische Reihenfolge, wie im Heuristik-Pfad.
#
# par.4 verlangt 200 Paare, Blockgroesse 5, --log-games und die
# Standard-Kennzahlen. Deshalb sind alpha und beta auf 0,001 gesetzt: die
# Wald-Schranken liegen dann bei rund +-6,9 statt +-2,94, und der Lauf geht bis
# zum Deckel statt per SPRT frueh abzubrechen. Derselbe Aufbau wie bei Nr. 29.
#
# LESART VORAB (par.4): "Sieg und Punkte gepaart ueber der Aufloesung -> H1;
# sonst Fan-out bleibt (Vollstaendigkeit, Nutzer-Praezedenz Rueckgabe-Reihenfolge),
# aber die Zielfrage par.5 wird nicht weiterverfolgt." par.5 (Zielwechsel des
# Kopfs) ist ohnehin v30 und nur bei H1 positiv.
#
# ERWARTUNG: klein. Der Fan-out betrifft nur Sonnenzuege aus der kleinen Fabrik
# mit mindestens zwei Mondsteinen; wie oft das vorkommt, ist nicht gemessen --
# die Diagnostik aus par.4 (Anteil der Sonnenzuege mit Rest >= 2, davon Anteil
# mit nicht-kanonischer Wahl) beantwortet genau das aus den Logs.
#
# KEIN KNOPF INS REZEPT aus diesem Skript: --no-promote-winner, und die Aufnahme
# eines Knopfs ist ein Nutzer-Entscheid.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
MODELL=models/alphazero_v28-b02_brierbest.onnx
SPEC_AN=models/moon_order_variants1.spec.json
SPEC_AUS=models/moon_order_variants0.spec.json

for f in "$MODELL" "$SPEC_AN" "$SPEC_AUS"; do
  if [ ! -f "$f" ]; then
    echo "ABBRUCH: $f fehlt -- kein stiller Leerlauf."
    exit 1
  fi
done
echo "== Nr. 28 Mondstapel-Fan-out A/B START $(date +%F' '%H:%M:%S)"

SEED=20261081
OUT="$ART/moon_order_ab_on_vs_off_s${SEED}.json"
python -X utf8 -u tools/paired_gating.py \
  --model-a "$MODELL" --spec-a "$SPEC_AN" \
  --model-b "$MODELL" --spec-b "$SPEC_AUS" \
  --name-a moon_order_on --name-b moon_order_off \
  --sims-a 400 --sims-b 400 --c-puct 1.5 \
  --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
  --seed "$SEED" --threads 10 --log-games \
  --no-promote-winner --out "$OUT"
echo "   Gating Exit $? ($(date +%H:%M:%S))"

echo "== Standard-Kennzahlen $(date +%H:%M:%S)"
python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
echo "   Spalten Exit $?"
python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
  --out "$ART/plate_points_moon_order_s${SEED}.json"
echo "   Platten Exit $? ($(date +%H:%M:%S))"

echo "== Nr. 28 FERTIG $(date +%F' '%H:%M:%S)"
echo "   Danach: Verdikt in PREREG_moon_stack_order.md par.4 registrieren,"
echo "   Zeile-1-Kopf und STATUS im selben Zug, plus die Diagnostik aus par.4"
echo "   (Anteil Sonnenzuege mit Rest >= 2, davon nicht-kanonische Wahl)."
