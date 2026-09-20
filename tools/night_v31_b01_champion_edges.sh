#!/usr/bin/env bash
# Promotions-Kanten fuer v31-b01: Anker und Champion-2.
# Vorlage: tools/night_v30_b02_champion_edges.sh (Historie, 962c079b^).
# Ablauf und Begruendungen: docs/promotion_checklist.md, Skill /mosaic-champion-promotion.
#
# Die Gating-Kante (Champion-1) ist bereits gemessen und eingetragen: zwei Seeds,
# 461:339 aus 800, Block-z +4,24 (PREREG_v31_window.md par.6).
#
# ANKER-KANTE mit festem n=50 statt Fruehstopp (Nutzer-Entscheid 2026-09-19): bei rund
# 90 Prozent Siegquote ist sie ein Sanity-Check, kein Rangmass. Als Fruehstopp waere sie
# ohnehin Bauarbeit -- frozen_referee_match kennt kein SPRT --, und ein Stopp zoege den
# Punktschaetzer nach oben (elo_tracker.py Z.117-120).
#
# CHAMPION-2 IST v29-b09: der Vorvorgaenger des Kandidaten. Fuer v31-b01 ist
# Champion-1 = v30-b02 und Champion-2 = v29-b09.
#
# CROSS-AERA ist der Normalfall (Nutzer-Entscheid 2026-08-29): die Artefakte bringen ihr
# eigenes Wheel mit, der Kandidat laeuft auf dem aktuellen. --force-cross-era ist deshalb
# gesetzt, der Golden-Selbsttest der Artefakte bleibt die Schranke.
#
# KEIN REGISTER-SCHREIBEN AUS DER KETTE: die elo_tracker-Zeilen traegt der Koordinator
# nach Pruefung der Zahlen ein.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

ART=evaluations/artifacts
CAND=v31-b01
MODEL=models/alphazero_v31-b01_brierbest.onnx
CHAMP_SPEC=models/frozen_champions/v30-b02/spec.json   # die Spec, mit der Tor 1 gemessen wurde
ANCHOR_DIR=models/frozen_heuristics/hv4_anchor
CHAMP2_DIR=models/frozen_champions/v29-b09

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
echo "===== b) ANKER-KANTE $CAND gegen hv4_anchor, n=50, Seed-Basis 20262000 $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/frozen_referee_match.py \
  --artifact-dir "$ANCHOR_DIR" \
  --model-a "$MODEL" --spec-a "$CHAMP_SPEC" \
  --sims-a 400 --c-puct-a 1.5 \
  --sims-worker 150 --c-puct-worker 0.3 \
  --n-games 50 --seed-base 20262000 --workers 6 \
  --force-cross-era \
  --out "$ART/anchor_edge_${CAND}_vs_hv4_anchor.json"
echo "   Anker-Kante Exit $? ($(date +%H:%M:%S))"

echo ""
echo "===== c) CHAMPION-2-KANTE $CAND gegen Artefakt v29-b09, Seed-Basis 20262100 $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/frozen_referee_match.py \
  --artifact-dir "$CHAMP2_DIR" \
  --model-a "$MODEL" --spec-a "$CHAMP_SPEC" \
  --sims-a 400 --c-puct-a 1.5 \
  --sims-worker 400 --c-puct-worker 1.5 \
  --n-games 150 --seed-base 20262100 --workers 6 \
  --force-cross-era \
  --out "$ART/champion2_${CAND}_vs_v29-b09_s20262100.json"
echo "   Champion-2-Kante Exit $? ($(date +%H:%M:%S))"

echo ""
echo "########## KANTEN FERTIG $(date +%F' '%H:%M:%S)"
echo "   Naechster Schritt (Koordinator, nach Pruefung der Zahlen): elo_tracker-Zeilen,"
echo "   dann Punkt 5 der Checkliste (Platt-Kalibrierung, sigma/Prior-Balance,"
echo "   Netz-Paritaets-Fixture), dann Punkt 6 und das eingefrorene Artefakt (Punkt 7)."
