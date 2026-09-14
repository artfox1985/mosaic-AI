#!/usr/bin/env bash
# DRITTER SEED fuer Tor 1 v29-b03 gegen den amtierenden Champion v28-b02
# (Nutzer-Entscheid 2026-09-14: "Mach den dritten seed").
#
# WARUM: die ersten beiden Seeds widersprechen sich.
#   20261067: 124:86, SPRT v29-b03 signifikant besser (LLR +3,193, McNemar p 0,0163,
#             gepaarte Diff +0,362 [+0,087, +0,636]), b03 plus 3,35 Punkte je Partie
#   20261068:  87:93, SPRT H0 (LLR -3,239, McNemar p 0,7754, Diff -0,067), Punkte gleich
# Dasselbe Muster wie b03 gegen b01 (ein Seed klar, einer neutral). Ein Seed entscheidet
# hier nichts; der dritte soll die Richtung klaeren.
#
# FLAGS BITGLEICH zu tools/night_v29_tor1_b03_vs_champion.sh -- nur der Seed ist neu.
# Nur so ist die Kante mit den ersten beiden poolbar bzw. vergleichbar.
#
# WHEEL: der Lauf MUSS auf demselben Wheel laufen wie die ersten beiden Seeds.
# Geprueft vor dem Start: Kontrakt-Hash 39994362fba145a6, unveraendert seit dem
# 2-Seed-Lauf (seither wurde nichts kompiliert und nichts installiert). Das Bau-Tor
# fuer den Mondstapel-Knopf und die Encoder-Korrektur wartet ausdruecklich, BIS
# dieser Lauf durch ist -- ein Wheel-Wechsel dazwischen macht den dritten Seed
# unvergleichbar.
#
# KEINE PROMOTION: --no-promote-winner. Champion-Wechsel ist ein eigener Ablauf
# (/mosaic-champion-promotion) und ein Nutzer-Entscheid.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
CHAMP_SPEC=models/frozen_champions/v28-b02/spec.json
NEU=models/alphazero_v29-b03_brierbest.onnx
ALT=models/alphazero_v28-b02_brierbest.onnx
SEED=20261069

for f in "$NEU" "$ALT" "$CHAMP_SPEC"; do
  if [ ! -f "$f" ]; then
    echo "ABBRUCH: $f fehlt -- kein stiller Leerlauf."
    exit 1
  fi
done

OUT="$ART/paired_gating_v29-b03_vs_v28-b02_s${SEED}.json"
echo "== TOR 1 b03 gegen Champion, DRITTER SEED $SEED $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/paired_gating.py \
  --model-a "$NEU" --spec-a "$CHAMP_SPEC" \
  --model-b "$ALT" --spec-b "$CHAMP_SPEC" \
  --name-a v29-b03 --name-b v28-b02 --sims-a 400 --sims-b 400 --c-puct 1.5 \
  --block-size 5 --max-pairs 200 --seed "$SEED" --threads 10 --log-games \
  --no-promote-winner --out "$OUT"
echo "   Gating Exit $? ($(date +%H:%M:%S))"

echo "== TOR 2b und Plattenpunkte $(date +%H:%M:%S)"
python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
echo "   Spalten Exit $?"
python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
  --out "$ART/plate_points_v29-b03_vs_v28-b02_s${SEED}.json"
echo "   Platten Exit $? ($(date +%H:%M:%S))"

echo "== DRITTER SEED FERTIG $(date +%F' '%H:%M:%S)"
echo "   Danach: Verdikt ueber alle drei Seeds in PREREG_v29_window.md par.9,"
echo "   Zeile-1-Kopf und STATUS im selben Zug, Elo-Kante eintragen."
echo "   Erst DANACH das Bau-Tor (Mondstapel-Knopf plus Encoder-Korrektur)."
