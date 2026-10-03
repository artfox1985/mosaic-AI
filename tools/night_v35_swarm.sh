#!/usr/bin/env bash
# v35-ERZEUGUNG, ZUERST NUR DER SCHWARM (PREREG_v35_window.md par.6/par.7; Nutzer 2026-10-02: "kannst
# schon alles vorbereiten dass das self play nach der promotion von selbst startet? zumindest die
# schwarm daten"). Startet von selbst, sobald die Promotionskette v34-b01 fertig ist:
#   0. Warten: tools/v34_promotion_chain.sh laeuft nicht mehr UND ihr letzter Schritt hat das
#      Selbsttest-Artefakt geschrieben (sonst STOPP, keine Erzeugung auf halber Promotion).
#   1. Netz-Paritaets-Fixture fuer den neuen Champion (Checkliste 5d; ein Build, darum VOR der
#      Erzeugung). Nicht fatal: die Erzeugung haengt nicht daran, der Befund steht im Log.
#   2. Tages-Snapshot (tools/mosaic_backup.ps1, Marke daily) als Beleg fuer spaetere Loeschungen.
#      Nicht fatal.
#   3. Smoke je Klasse (20 Partien, data/probe_v35smoke), Muster PREREG_v34_window.md par.7a.
#      FATAL: ein roter Smoke stoppt die Kette vor der Erzeugung.
#   4. Erzeugung value-deviate, dann value-excursion, je 4.000 Partien aus models/v35.recipe.json.
# Sockel-Klassen (policy und die asymmetrischen) folgen nach dem Bau, nicht hier.
#
# KEINE PIPE, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
RECIPE=models/v35.recipe.json
SELFTEST=evaluations/artifacts/referee_selftest_v34-b01.json
. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"

for f in "$RECIPE" models/v35_generation.spec.json models/alphazero_v34-b01_brierbest.onnx; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
for c in value-deviate value-excursion; do
  if ls data/ | grep -q "^selfplay_v34-b01-${c}_"; then echo "ABBRUCH: data/ traegt schon $c-Dateien"; exit 4; fi
done

echo "########## v35-Schwarm WARTET auf das Ende der Promotionskette $(date +%F' '%H:%M:%S)"
tick=0
while :; do
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '[v]34_promotion_chain' }).Count" 2>/dev/null | tr -d '\r[:space:]')
  [ "$n" = "0" ] && break
  tick=$((tick + 1))
  [ $tick -gt 720 ] && { echo "STOPP: Promotionskette nach 12 h noch nicht fertig"; exit 5; }
  [ $((tick % 10)) -eq 1 ] && echo "   Promotionskette laeuft noch ($(date +%H:%M:%S))"
  sleep 60
done
[ -f "$SELFTEST" ] || { echo "STOPP: Promotionskette beendet, aber $SELFTEST fehlt -- erst pruefen"; exit 6; }
echo "   Promotionskette fertig, Selbsttest-Artefakt liegt ($(date +%H:%M:%S))"
wait_for_free_cpu "v35-Schwarm"

echo ""
echo "===== 1 Netz-Paritaets-Fixture fuer $(cat models/champion.txt) $(date +%H:%M:%S)"
PYDIR=$(python -c 'import sys,os;print(os.path.dirname(sys.executable))')
( cd engine && PATH="$PYDIR:$PATH" MOSAIC_UPDATE_NET_PARITY_FIXTURE=1 \
    cargo test --release net_parity_hash_matches_champion_fixture -- --nocapture ) \
  && ( cd engine && PATH="$PYDIR:$PATH" cargo test --release net_parity_hash_matches_champion_fixture -- --nocapture ) \
  && echo "   Paritaets-Fixture neu und im frischen Prozess GRUEN" \
  || echo "   WARNUNG: Paritaets-Fixture nicht gruen -- von Hand nachziehen (Checkliste 5d)"

echo ""
echo "===== 2 Tages-Snapshot $(date +%H:%M:%S)"
powershell -NoProfile -ExecutionPolicy Bypass -File tools/mosaic_backup.ps1 \
  && echo "   Snapshot fertig ($(date +%H:%M:%S))" \
  || echo "   WARNUNG: Snapshot nicht gelaufen -- vor jeder Loeschung von Hand nachholen"

echo ""
echo "===== 3 Smoke je Klasse $(date +%H:%M:%S)"
python -X utf8 - "$RECIPE" <<'PYEOF' || { echo "STOPP: Rezept- oder Wheel-Pruefung rot"; exit 3; }
import json, sys
sys.path.insert(0, "tools")
import mosaic_rust
from recipe_config import load_recipe, expected_engine_config
r = load_recipe(sys.argv[1])
d = json.loads(mosaic_rust.engine_config_json())
print(f"   engine_config: input_size {d.get('input_size')} num_actions {d.get('num_actions')} "
      f"contract {d.get('contract_hash')}; Rezept sha256 {r.sha256[:12]}")
if str(d.get("input_size")) != "888" or str(d.get("num_actions")) != "414":
    print("ABBRUCH: Wheel traegt nicht 888/414"); sys.exit(3)
for c in r["classes"]:
    print(f"   {c}: version {r['classes'][c]['version']}, seed {r['classes'][c]['seed']}, "
          f"Waechter {expected_engine_config(r, c)}")
PYEOF
for CLASS in value-deviate value-excursion; do
  MOSAIC_DATA_DIR=data/probe_v35smoke python -X utf8 -u self_play.py --recipe "$RECIPE" --class "$CLASS" \
    --games 20 --version "smoke-v35-$CLASS"
  RC=$?
  echo "   Smoke $CLASS Exit $RC ($(date +%H:%M:%S)), Dateien: $(ls data/probe_v35smoke 2>/dev/null | grep -c "^selfplay_smoke-v35-${CLASS}_")"
  [ $RC -eq 0 ] || { echo "STOPP: Smoke $CLASS rot -- keine Erzeugung"; exit 7; }
done

echo ""
wait_for_free_cpu "v35-Schwarm Erzeugung"
for CLASS in value-deviate value-excursion; do
  echo ""
  echo "== Klasse $CLASS, 4.000 Partien $(date +%F' '%H:%M:%S)"
  python -X utf8 -u self_play.py --recipe "$RECIPE" --class "$CLASS"
  RC=$?
  echo "   $CLASS Exit $RC ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c "^selfplay_v34-b01-${CLASS}_")"
  [ $RC -eq 0 ] || { echo "STOPP: Klasse $CLASS mit Exit $RC"; exit 10; }
done

echo ""
echo "== v35-SCHWARM FERTIG $(date +%F' '%H:%M:%S)"
echo "   Naechster Schritt (PREREG_v35_window.md par.8): Manifest-Diff je Klasse gegen v34, Waechter-"
echo "   Protokoll, Tor 0 je Klasse, tie_mirrored-Anteil, KL-Abnahme am Ausflug, Watchdog-Zeilen."
