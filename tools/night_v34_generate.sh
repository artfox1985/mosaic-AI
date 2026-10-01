#!/usr/bin/env bash
# v34-ERZEUGUNG, alle drei Klassen, je Klasse aus der Rezeptdatei models/v34.recipe.json.
# Generator: v33-b01 (Nutzer 2026-09-27, PREREG_v34_window.md par.5 Punkt 1), eingefroren unter
# models/frozen_champions/v33-b01 (Rolle generator).
#
# Fortschreibung von `tools/night_v33_generate.sh` (Fassung in der Git-Historie). GEAENDERT:
#   1. Flags und Env kommen aus dem REZEPT (`--recipe ... --class ...`); das Manifest traegt Rezept,
#      Overrides, mosaic_env und das Waechter-Protokoll (expect_engine_config je Klasse).
#   2. Dritte Klasse `value-wegc` (Weg C, Huelle an) statt `value-tempc-nohull` (par.5 Punkt 2).
#   3. Paket: Spiegelknopf, getrennte Label-RNG, Ausflug-Neumischung, KL-Abzweig im Ausflug,
#      E1 (Einpass-Konsum) und Runde 5 per Netz (par.3).
# Smoke gruen (par.7a), Kostentor (par.8a): Sockel 2,73 s je Partie, Erzeugung rund 8,8 h (HERLEITUNG).
#
# Nach dem Lauf aus der Aufgabenausgabe zaehlen: `[Watchdog]`-Zeilen je Klasse (obere Schranke fuer
# verworfene Panics plus Deadlines, STATUS "Review-Rest").
#
# KEINE PIPE, keine eigene Umleitung; als DATEI starten. Start NUR auf Nutzer-Freigabe.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
RECIPE=models/v34.recipe.json

[ -f "$RECIPE" ] || { echo "ABBRUCH: $RECIPE fehlt"; exit 1; }
python -X utf8 - "$RECIPE" <<'PYEOF' || exit 3
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
for f in (r["common"]["model"], r["common"]["spec"]):
    open(f, "rb").close()
for c in r["classes"]:
    print(f"   {c}: version {r['classes'][c]['version']}, seed {r['classes'][c]['seed']}, "
          f"Waechter {expected_engine_config(r, c)}")
PYEOF

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
wait_for_free_cpu "v34-Erzeugung"

for CLASS in policy value-wegc value-excursion; do
  echo ""
  echo "== Klasse $CLASS, 4.000 Partien $(date +%F' '%H:%M:%S)"
  python -X utf8 -u self_play.py --recipe "$RECIPE" --class "$CLASS"
  RC=$?
  echo "   $CLASS Exit $RC ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c "^selfplay_v33-b01-${CLASS}_")"
  [ $RC -eq 0 ] || { echo "STOPP: Klasse $CLASS mit Exit $RC"; exit 10; }
done

echo ""
echo "== v34-ERZEUGUNG FERTIG $(date +%F' '%H:%M:%S)"
echo "   Naechster Schritt (PREREG_v34_window.md par.4): Manifest-Diff je Klasse gegen v33, Waechter-"
echo "   Protokoll, Tor 0 je Klasse, Tor 2a am Sockel, tie_mirrored-Anteil, KL-Abnahme am Ausflug,"
echo "   Watchdog-Zeilen zaehlen; dann Traeger-Manifest v34 und Fenster (Kette folgt)."
