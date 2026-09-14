#!/usr/bin/env bash
# Nachtprogramm 2026-09-14, rund 6 h. Alles auf DEMSELBEN Wheel
# (Kontrakt 39994362fba145a6, Mondstapel-Nachsuche und Streu-Knopf abgenommen).
#
# Jeder Schritt laeuft EXKLUSIV und nacheinander -- zwei CPU-Messungen
# gegeneinander sind verboten (CLAUDE.md). Bricht ein Schritt ab, laeuft die
# Kette weiter; die Artefakte der fertigen Schritte bleiben gueltig.
#
# SCHRITT 1  A/B Mondstapel Stufe 3 (moon_stack_order par.9): Nachsuche gegen
#            kanonisch. Beide Seiten dasselbe Modell, Unterschied ist GENAU ein
#            Spec-Feld (geprueft: moon_order_variants 2 gegen 0). Erstmals misst
#            das den Wert der Reihenfolge ALLEIN -- Stufe 1 hatte die
#            Kandidatenkonkurrenz im Wurzelfenster mitgemessen.
#            Kosten: rund 18.350 Zusatz-Sims je Partie (par.9b, n = 12.907
#            Partien), also etwa +57 Prozent gegenueber Nr. 28.
#
# SCHRITT 2  Kostentor K4 (round_estimate_leaf_term par.5 Punkt 3): Wanduhr je
#            Partie MIT gegen OHNE Rundenschaetzer, Schwelle 25 Prozent. Zwei
#            Laeufe mit identischen Specs je Seite, verglichen wird
#            laufzeit.s_je_partie. Reisst das Tor, sind die Arenen darunter
#            trotzdem aussagekraeftig -- sie messen Staerke, nicht Kosten; das
#            Verdikt zieht der Nutzer.
#
# SCHRITT 3  Arena K4 mit C_est = 1,0 gegen aus (par.5 Punkt 5).
# SCHRITT 4  Arena K4 mit C_est = 0,5 gegen aus -- zwei Dosen, wie par.5 Punkt 4
#            es fuer das Instrument verlangt; hier auf der Arena-Schiene.
#
# NICHT in dieser Kette: das argmax-Instrument (par.5 Punkt 4) -- es braucht ein
# Werkzeug, das ich nicht ungeprueft in eine unbeaufsichtigte Nacht stelle.
#
# Blockgroesse 5 ueberall (feedback_block_size_5_all_arena_tools). SPRT weit
# gesetzt (alpha=beta=0,001), damit die Laeufe ihren vollen Umfang fahren statt
# frueh abzubrechen -- Elo-Kanten aus Frueh-Stopp sind nach oben verzerrt.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
MODELL=models/alphazero_v28-b02_brierbest.onnx

for f in "$MODELL" models/moon_order_post2.spec.json models/moon_order_off0.spec.json \
         models/round_est_c10.spec.json models/round_est_c05.spec.json models/round_est_off.spec.json; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done

lauf () {  # name specA specB seed maxpairs
  local NAME="$1" SA="$2" SB="$3" SEED="$4" PAIRS="$5"
  local OUT="$ART/${NAME}_s${SEED}.json"
  echo ""
  echo "===== $NAME (Seed $SEED, $PAIRS Paare) $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$MODELL" --spec-a "$SA" \
    --model-b "$MODELL" --spec-b "$SB" \
    --name-a "${NAME}_a" --name-b "${NAME}_b" \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs "$PAIRS" --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$SEED" --threads 10 --log-games \
    --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_${NAME}_s${SEED}.json"
  echo "   Kennzahlen Exit $? ($(date +%H:%M:%S))"
}

echo "########## NACHTPROGRAMM START $(date +%F' '%H:%M:%S)"

# 1. Mondstapel Stufe 3
lauf moon_order_post_vs_off models/moon_order_post2.spec.json models/moon_order_off0.spec.json 20261091 200

# 2. Kostentor K4: zwei Laeufe, beide Seiten gleich, Wanduhr vergleichen
lauf k4_kosten_mit models/round_est_c10.spec.json models/round_est_c10.spec.json 20261092 20
lauf k4_kosten_ohne models/round_est_off.spec.json models/round_est_off.spec.json 20261093 20

# 3. und 4. Arena K4, zwei Dosen
lauf k4_c10_vs_off models/round_est_c10.spec.json models/round_est_off.spec.json 20261094 80
lauf k4_c05_vs_off models/round_est_c05.spec.json models/round_est_off.spec.json 20261095 80

# 5. NACHGEZOGEN: die duennste Kante der Generation.
#    Das Verdikt "die Spezialfeld-Kanaele 77/78 tragen" (special_tile_yield
#    par.4a, geschlossen 2026-09-14) steht auf zwei Laeufen, deren zweiter --
#    der SIGNIFIKANTE, McNemar p = 0,0386 -- nach 30 Paaren per SPRT abbrach.
#    60 Partien mit Frueh-Stopp, also nach oben verzerrter Siegquote, fuer ein
#    Verdikt, das einen Prereg-Absatz schliesst. Dieser Lauf zieht dieselbe
#    Kante mit 150 Paaren OHNE Frueh-Stopp nach (neuer Seed).
#    ACHTUNG BEIM LESEN: b02 hat die Kanaele AUS, b03 AN. Verliert die
#    a-Seite (b02), bestaetigt das den Befund.
MOD_B02=models/alphazero_v29-b02_brierbest.onnx
MOD_B03=models/alphazero_v29-b03_brierbest.onnx
CHAMP_SPEC=models/frozen_champions/v28-b02/spec.json
if [ -f "$MOD_B02" ] && [ -f "$MOD_B03" ]; then
  OUT="$ART/paired_gating_v29-b02_vs_v29-b03_s20261096.json"
  echo ""
  echo "===== NACHZUG b02 gegen b03, 150 Paare ohne Frueh-Stopp $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py     --model-a "$MOD_B02" --spec-a "$CHAMP_SPEC"     --model-b "$MOD_B03" --spec-b "$CHAMP_SPEC"     --name-a v29-b02 --name-b v29-b03 --sims-a 400 --sims-b 400 --c-puct 1.5     --block-size 5 --max-pairs 150 --sprt-alpha 0.001 --sprt-beta 0.001     --seed 20261096 --threads 10 --log-games     --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5     --out "$ART/plate_points_v29-b02_vs_v29-b03_s20261096.json"
  echo "   Kennzahlen Exit $? ($(date +%H:%M:%S))"
else
  echo "UEBERSPRUNGEN: b02- oder b03-Modell fehlt"
fi

echo ""
echo "########## NACHTPROGRAMM FERTIG $(date +%F' '%H:%M:%S)"
echo "   Faellig danach: Verdikte registrieren (moon_stack_order par.9,"
echo "   round_estimate_leaf_term par.5), Zeile-1-Koepfe und STATUS im selben Zug."
echo "   Kostentor: laufzeit.s_je_partie aus k4_kosten_mit gegen k4_kosten_ohne,"
echo "   Schwelle 25 Prozent."
