#!/usr/bin/env bash
# Tor 1 fuer den Sicht-Arm v29-b03 GEGEN DEN AMTIERENDEN CHAMPION v28-b02, zwei
# Seeds, dann Tor 2b und die Plattenpunkte auf denselben Logs.
#
# WARUM DIESER LAUF (Nutzer 2026-09-14: "ich hab noch keinen champion kandidaten
# aus v29 gesehen"): v29 hat bisher NUR arminterne Kanten. b01 gegen den Champion
# war zweimal H0, b03 hat b01 geschlagen (Seed 1 klar 69:41) und b02 geschlagen --
# aber b03 gegen den Champion ist UNGEMESSEN. Ohne diese Kante hat v29 keinen
# Kandidaten, und der Fahrplanpunkt Nr. 21 (Promotion) hat keine Grundlage.
#
# Dazu der korrigierte Offline-Stand (PREREG_v29_window.md, Nachbewertung
# 2026-09-14): b03s vermeintlicher Brier-Rueckstand war ein kaputter Val-Cache.
# Auf sauberen Daten liegt er mit 0,1796741 gegen 0,1793375 gleichauf mit b01.
# Es gibt also keinen Offline-Grund mehr, der gegen die Kante spricht.
#
# KEINE PROMOTION AUS DIESEM SKRIPT: --no-promote-winner ist gesetzt. Ein
# Champion-Wechsel ist ein eigener Ablauf (/mosaic-champion-promotion,
# docs/promotion_checklist.md) und ein Nutzer-Entscheid.
#
# Flags bewusst identisch zu tools/night_v29_tor1_b03.sh (Blockgroesse 5,
# max-pairs 200, sims 400, c_puct 1.5, Champion-Spec beidseits): nur so ist die
# neue Kante mit den bestehenden v29-Kanten vergleichbar.
#
# MODELLNAMEN NACHGESEHEN, nicht geraten: b03 hat ein `_brierbest`, der Champion
# ebenfalls (`alphazero_v28-b02_brierbest.onnx`, models/champion.txt).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
CHAMP_SPEC=models/frozen_champions/v28-b02/spec.json
NEU=models/alphazero_v29-b03_brierbest.onnx
ALT=models/alphazero_v28-b02_brierbest.onnx

for f in "$NEU" "$ALT" "$CHAMP_SPEC"; do
  if [ ! -f "$f" ]; then
    echo "ABBRUCH: $f fehlt -- kein stiller Leerlauf."
    exit 1
  fi
done
echo "== TOR 1 b03 gegen den Champion START $(date +%F' '%H:%M:%S)"
echo "   Kandidat: $NEU"
echo "   Champion: $ALT"

for SEED in 20261067 20261068; do
  OUT="$ART/paired_gating_v29-b03_vs_v28-b02_s${SEED}.json"
  echo "== TOR 1, Seed $SEED $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$NEU" --spec-a "$CHAMP_SPEC" \
    --model-b "$ALT" --spec-b "$CHAMP_SPEC" \
    --name-a v29-b03 --name-b v28-b02 --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --seed "$SEED" --threads 10 --log-games \
    --no-promote-winner --out "$OUT"
  echo "   Gating Exit $? ($(date +%H:%M:%S))"

  echo "== TOR 2b und Plattenpunkte, Seed $SEED $(date +%H:%M:%S)"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  echo "   Spalten Exit $?"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_v29-b03_vs_v28-b02_s${SEED}.json"
  echo "   Platten Exit $? ($(date +%H:%M:%S))"
done

echo "== TOR 1 b03 gegen Champion FERTIG $(date +%F' '%H:%M:%S)"
echo "   Danach faellig: Verdikt in PREREG_v29_window.md par.9 registrieren,"
echo "   Zeile-1-Kopf und STATUS im selben Zug. Bei zwei Siegen ist der"
echo "   Promotions-Ablauf der naechste Schritt -- NUR auf Nutzer-Entscheid."
echo "   Danach steht Fahrplan Nr. 29 (Rueckgabe-Modus A/B) wieder an."
