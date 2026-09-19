#!/usr/bin/env bash
# Promotions-Kanten fuer den Kandidaten v30-b02 (docs/promotion_checklist.md Punkte 3 und 4).
# Muster: tools/night_champion_edges_v29.sh; Aufrufform Feld fuer Feld von dort uebernommen.
#
# WARUM NUR ZWEI KANTEN: die Gating-Kante (Punkt 2) ist schon gefahren -- v30-b02 gegen den
# Champion v29-b09, zwei Seeds a 200 Paare, 443:297 = 59,86 Prozent, Block-z +5,36
# (PREREG_v30_window.md par.9). Offen sind Anker und Champion-2.
#
# ANKER-KANTE MIT n=50 statt 150 (Nutzer-Entscheid 2026-09-19, docs/promotion_checklist.md
# Punkt 3): bei einer erwarteten Quote um 85 Prozent traegt die Kante wenig Information, ihr
# Zweck ist die Bindung an den Fixpunkt. Kleineres FESTES n statt Fruehstopp -- frozen_referee_match
# kennt kein SPRT, und ein Stopp wuerde den Punktschaetzer nach oben ziehen (elo_tracker.py Z.117-120).
#
# CHAMPION-2 IST v28-b02, NICHT v27-b01: Champion-2 ist der Vorvorgaenger des Kandidaten. Fuer
# v30-b02 ist Champion-1 = v29-b09 und Champion-2 = v28-b02 (STATUS Abschnitt 2).
#
# SEEDS: Anker-Basis 20261800 (50 fortlaufende Seeds, ausserhalb der b09-Spanne 20261700-20261849),
# Champion-2-Basis 20261900 (150 fortlaufend, ausserhalb 20261251-20261400 der v29-Kanten).
#
# KEIN REGISTER-SCHREIBEN AUS DER KETTE: --no-promote-winner gibt es hier nicht (frozen_referee_match
# promoviert nichts); die elo_tracker-Zeilen traegt der Koordinator nach Pruefung der Zahlen ein.
# Der Promotions-Entscheid selbst bleibt Nutzer-Entscheid.
#
# KOSTEN (gemessen, docs/measured_runtimes.md): Anker 150 Partien 1.246-1.281 s -> bei n=50 rund
# 420 s; Champion-2 150 Partien 2.340-2.388 s. Zusammen rund 46 min.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

ART=evaluations/artifacts
CAND=v30-b02
MODEL=models/alphazero_v30-b02_brierbest.onnx
CHAMP_SPEC=models/frozen_champions/v29-b09/spec.json
ANCHOR_DIR=models/frozen_heuristics/hv4_anchor
CHAMP2_DIR=models/frozen_champions/v28-b02

for f in "$MODEL" "$CHAMP_SPEC"; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
for d in "$ANCHOR_DIR" "$CHAMP2_DIR"; do
  [ -d "$d" ] || { echo "ABBRUCH: $d fehlt"; exit 1; }
done

cpu_frei() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { (\$_.CommandLine -match '[s]elf_play\.py|[t]rain\.py|[p]aired_gating\.py|[f]rozen_referee_match\.py|[b]uild_cache|[m]aturin' -and \$_.Name -match 'python') -or \$_.Name -match '^(cargo|rustc)' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}
echo "########## PROMOTIONS-KANTEN $CAND $(date +%F' '%H:%M:%S)"
while :; do
  cpu_frei && { echo "   Maschine frei ($(date +%H:%M:%S))"; break; }
  echo "   belegt ($(date +%H:%M:%S))"; sleep 120
done

echo ""
echo "===== b) ANKER-KANTE $CAND gegen hv4_anchor, n=50, Seed-Basis 20261800 $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/frozen_referee_match.py \
  --artifact-dir "$ANCHOR_DIR" \
  --model-a "$MODEL" --spec-a "$CHAMP_SPEC" \
  --sims-a 400 --c-puct-a 1.5 \
  --sims-worker 150 --c-puct-worker 0.3 \
  --n-games 50 --seed-base 20261800 --workers 6 \
  --force-cross-era \
  --out "$ART/anchor_edge_${CAND}_vs_hv4_anchor.json"
echo "   Anker-Kante Exit $? ($(date +%H:%M:%S))"

echo ""
echo "===== c) CHAMPION-2-KANTE $CAND gegen Artefakt v28-b02, Seed-Basis 20261900 $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/frozen_referee_match.py \
  --artifact-dir "$CHAMP2_DIR" \
  --model-a "$MODEL" --spec-a "$CHAMP_SPEC" \
  --sims-a 400 --c-puct-a 1.5 \
  --sims-worker 400 --c-puct-worker 1.5 \
  --n-games 150 --seed-base 20261900 --workers 6 \
  --force-cross-era \
  --out "$ART/champion2_${CAND}_vs_v28-b02_s20261900.json"
echo "   Champion-2-Kante Exit $? ($(date +%H:%M:%S))"

echo ""
echo "########## KANTEN FERTIG $(date +%F' '%H:%M:%S)"
echo "   Naechster Schritt (Koordinator, nach Pruefung der Zahlen): elo_tracker-Zeilen eintragen,"
echo "   dann docs/promotion_checklist.md Punkte 1, 5 und 7 -- der Promotions-Entscheid ist Nutzer-Sache."
