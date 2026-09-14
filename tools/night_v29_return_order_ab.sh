#!/usr/bin/env bash
# Fahrplan Nr. 29: A/B Rueckgabe-Modus 1 gegen 0 (PREREG_dome_return_order.md par.5).
#
# ABWEICHUNG VON par.5, BEWUSST UND REGISTRIERT
# ---------------------------------------------
# par.5 Punkt 1 und der AGENTEN-AUFTRAG schreiben `tools/frozen_referee_match.py`
# vor: Seite A auf der lebenden Engine, Seite B als gefrorenes v28-b02-Artefakt im
# eigenen Worker. Als das registriert wurde (2026-09-13), liefen Live-Wheel und
# Artefakt-Wheel auf DERSELBEN Aera. Das gilt seit dem v29-Wheelwechsel nicht mehr:
#   live     39994362fba145a6, INPUT_SIZE 794
#   Artefakt 39648b95bbba1acf, INPUT_SIZE 755
# Der Referee verweigert dann den Handshake; mit --force-cross-era gemessen waere
# nicht der Knopf, sondern Knopf PLUS Aerawechsel -- also gerade nicht das, wonach
# par.5 fragt ("gleiches Netz, nur der Knopf unterscheidet").
#
# Ersatz mit derselben Absicht: `tools/paired_gating.py` faehrt BEIDE Seiten auf dem
# LIVEN Wheel, mit DEMSELBEN Modell, und unterscheidet sie ausschliesslich ueber die
# Spec. Die beiden Spec-Dateien sind aus der Champion-Spec erzeugt und weichen in
# genau einem Feld voneinander ab (geprueft: `return_order_mode`, 14 Felder je Datei).
# Gepaart mit Seitentausch ist das naeher an par.5s Absicht als der Referee-Weg.
#
# Zweite Abweichung: par.5 will 150 Partien je Seed-Basis und einen Vorzeichentest,
# kein SPRT. paired_gating bricht per SPRT ab. Deshalb sind alpha und beta auf 0,001
# gesetzt -- die Wald-Schranken liegen dann bei rund +-6,9 statt +-2,94 und werden
# praktisch nicht erreicht, der Lauf geht bis zum Deckel von 75 Paaren = 150 Partien.
# Ein SPRT-Abbruch waere trotzdem kein Schaden, sondern ein staerkeres Ergebnis.
#
# Erwartung vorab (par.3 H2, par.8a Befund 1): klein. Der Value-Kopf sieht die
# Reihenfolge nur als TYP-Folge (features.rs:212, oberste vier Positionen des eigenen
# Blocks als +1 Spezial / -1 Joker / 0); Permutationen gleichtypiger Platten sind fuer
# das Netz identisch, Modus 1 faellt dann per Gleichstand auf die Ziehreihenfolge
# zurueck. Die Abweichungsrate ist damit strukturell gedeckelt.
#
# Der Knopf bleibt in JEDEM Fall (par.0/par.1, Nutzer-Praezedenz): Massstab ist
# Vollstaendigkeit, nicht Elo.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
MODELL=models/alphazero_v28-b02_brierbest.onnx
SPEC1=models/return_order_mode1.spec.json
SPEC0=models/return_order_mode0.spec.json

for f in "$MODELL" "$SPEC1" "$SPEC0"; do
  if [ ! -f "$f" ]; then
    echo "ABBRUCH: $f fehlt -- kein stiller Leerlauf."
    exit 1
  fi
done
echo "== Nr. 29 Rueckgabe-Modus A/B START $(date +%F' '%H:%M:%S)"

for SEED in 20261071 20261072; do
  OUT="$ART/return_order_ab_mode1_vs_mode0_s${SEED}.json"
  echo "== Seed $SEED $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$MODELL" --spec-a "$SPEC1" \
    --model-b "$MODELL" --spec-b "$SPEC0" \
    --name-a return_order_mode1 --name-b return_order_mode0 \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 75 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$SEED" --threads 10 --log-games \
    --no-promote-winner --out "$OUT"
  echo "   Gating Exit $? ($(date +%H:%M:%S))"

  echo "== Standard-Kennzahlen, Seed $SEED $(date +%H:%M:%S)"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  echo "   Spalten Exit $?"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_return_order_s${SEED}.json"
  echo "   Platten Exit $? ($(date +%H:%M:%S))"
done

echo "== Nr. 29 FERTIG $(date +%F' '%H:%M:%S)"
echo "   Offen danach: die Diagnostik aus par.5 Punkt 2 (Anteil der Rueckgaben mit"
echo "   abweichender Reihenfolge, Wiederkehr-Rate, Ziehungen in den eigenen Block)"
echo "   aus den Logzeilen [return_order] mode=.. drawn=[..] chosen=[..]."
