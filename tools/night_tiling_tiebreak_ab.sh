#!/usr/bin/env bash
# Fahrplan 36f: A/B des Netz-Stichentscheids im Tiling
# (PREREG_round_transition_search_sampling.md par.16.10, Bau in par.16.11;
# Nutzer 2026-09-17: "tiling stichentscheid als knopf bauen und im A/B messen").
#
# DASSELBE Netz gegen sich selbst, Knopf AN (Bestand, net_tiling_tiebreak: 1)
# gegen AUS (0), 200 Paare, Blockgroesse 5, ohne Frueh-Stopp
# (alpha = beta = 0,001), --log-games. Netz = der amtierende Champion
# v28-b02_brierbest, Spec = die eingefrorene Champion-Spec plus dem einen Feld.
#
# Kein Kostentor: der Knopf SPART Arbeit, wenn er aus ist (bis zu 12
# Vorwaertspaesse je Tiling-Zug entfallen); ein Aufschlag ist strukturell
# ausgeschlossen. Die Laufzeit steht trotzdem im Artefakt (paired_gating.py).
#
# NEBENLAST: dieses Skript ist eine Wanduhr-Messung und laeuft nur, wenn kein
# anderer CPU-Auftrag laeuft (Cache-Bau, Arena, cargo/maturin, Sonden). Ein
# GPU-Training (train.py) daneben ist erlaubt (docs/working_rules.md,
# Auslastung) und wird NICHT abgewartet.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
MODELL=models/alphazero_v28-b02_brierbest.onnx
ON=models/tiebreak_on.spec.json
OFF=models/tiebreak_off.spec.json
SEED=20261170
OUT="$ART/tiebreak_on_vs_off_s${SEED}.json"

# Erste Pruefung: laeuft dieses Wheel ueberhaupt mit dem Knopf? Ohne ihn waeren
# beide Arme derselbe Spieler, und die Spec-Dateien wuerden als "unbekanntes
# Feld" hart abgewiesen -- lieber hier abbrechen als 87 Minuten messen.
grep -q net_tiling_tiebreak engine/src/net_mcts.rs || {
  echo "ABBRUCH: Knopf net_tiling_tiebreak fehlt in engine/src/net_mcts.rs (Quellstand ohne par.16.11)"
  exit 2
}
for f in "$MODELL" "$ON" "$OFF"; do [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }; done

cpu_frei() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { (\$_.CommandLine -match '[t]rain\.py|[p]aired_gating\.py|[f]rozen_referee_match\.py|[b]uild_cache|[c]ounterfactual_tiling|[o]ffline_diagnosis|[d]ead_unit_probe|[m]aturin|[w]indow_train_split' -and \$_.Name -match 'python') -or \$_.Name -match '^(cargo|rustc)' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}
warte_frei() {
  echo "########## TIEBREAK-A/B WARTET ($1) $(date +%F' '%H:%M:%S)"
  while :; do
    cpu_frei && { echo "   Maschine frei ($(date +%H:%M:%S))"; break; }
    echo "   belegt ($(date +%H:%M:%S))"; sleep 120
  done
  sleep 20
}

# MOSAIC_CHAIN_NO_WAIT=1: Start neben einem GPU-Training als der EINE erlaubte CPU-Auftrag (CLAUDE.md,
# Praezisierung 2026-08-31); der Prozessfilter oben wuerde sonst auf train.py warten.
if [ "${MOSAIC_CHAIN_NO_WAIT:-0}" = "1" ]; then echo "   Warteschleife uebersprungen (MOSAIC_CHAIN_NO_WAIT=1, GPU-Training daneben erlaubt) $(date +%H:%M:%S)"; else warte_frei "A/B Stichentscheid an gegen aus"; fi
echo ""
echo "===== A/B Nr. 36f: Champion mit gegen ohne Stichentscheid, 200 Paare, Seed $SEED $(date +%F' '%H:%M:%S)"
echo "   A = an (Bestand, $ON), B = aus ($OFF)"
python -X utf8 -u tools/paired_gating.py \
  --model-a "$MODELL" --spec-a "$ON" \
  --model-b "$MODELL" --spec-b "$OFF" \
  --name-a tiebreak_on --name-b tiebreak_off \
  --sims-a 400 --sims-b 400 --c-puct 1.5 \
  --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
  --seed "$SEED" --threads 10 --log-games --no-promote-winner --out "$OUT"
echo "   Exit $? ($(date +%H:%M:%S))"

echo ""
echo "== Standard-Kennzahlen: Spalten und Plattenpunkte je Kriterium $(date +%H:%M:%S)"
python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
  --out "$ART/plate_points_tiebreak_on_vs_off_s${SEED}.json"

echo ""
echo "########## TIEBREAK-A/B FERTIG $(date +%F' '%H:%M:%S)"
echo "   Faellig danach: Verdikt nach der Lesart in par.16.10 (Block-z auf Siegquote UND"
echo "   Punktemarge), sechs Standard-Kennzahlen, Laufzeit nach docs/measured_runtimes.md,"
echo "   Registrierung in par.16.12 samt Zeile-1-Kopf und Prereg-Index."
