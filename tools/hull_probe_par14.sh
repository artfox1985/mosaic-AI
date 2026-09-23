#!/usr/bin/env bash
# Huellen-Sonde, vorregistriert in evaluations/PREREG_geometric_envelope.md par.14/14a.
# Frage: wie viel vom Dreieck ist heute der KNOPF, wie viel der eingelernte PRIOR?
#
# Aufbau (par.14, unveraendert): DASSELBE Netz auf beiden Seiten, nur die Spec unterscheidet
# sich -- Einfaktorialitaet beim Anlegen belegt (genau ein abweichendes Feld,
# `envelope_search_c` 1,0 gegen 0,0). Zwei Seeds, Blockgroesse 5, `--log-games`.
#
# Nutzer-Freigabe: 2026-09-22 "Ja plan es ein." Anlass: *"War eigentlich nur ein proxy um das
# Netz in eine moegliche Form zu leiten."* -- faellt die Form ohne Knopf nicht, kann das
# Geruest weg. Der benannte Abnehmer steht in par.14b (geteilter Sockel in v33).
#
# DREI ABLESUNGEN AUS DENSELBEN LOGS, Stand nach der Werkzeugpruefung vom 2026-09-23:
#   1. FORM  -- laeuft mit. `arena_column_probe.py` rechnet `huelle_innen/aussen/H/orientierung`
#      aus `dome_grid` des Artefakts (dort :142 als Bibliotheksimport von
#      triangle_hull_coverage_probe, :147-164). KEIN Zusatzlauf noetig.
#      VORBEHALT, beim Auswerten zu benennen: dieser Weg normiert auf 56 (Gesamtkosten des
#      DREIECKS) und waehlt zwischen den beiden Dreiecks-Orientierungen, waehrend die Spec
#      `envelope_hull_form 2` faehrt (22 Zellen, Gesamtkosten 62). Differenz eine Zelle.
#      Das RUNDEN-Profil ist aus einem Arena-Artefakt NICHT zu gewinnen (rundenweise liegt nur
#      `floor_per_round` vor); dafuer braeuchte es .pkl-Korpora je Spec, andere Bauform.
#   2. STAERKE -- McNemar und Block-z aus `paired_gating`, ohne Anpassung.
#      Block-z auf DIFFERENZIERTEN Blockwerten rechnen: die Felder in `blocks[]` sind KUMULATIV
#      (docs/pitfalls.md).
#   3. GEGNER-REAKTION -- OFFEN, Nutzer-Entscheid (par.14 "Zweiter Nebenbefund").
#      `opponent_disruption_analysis.py` ist auf eine ANDERE Bauform gebaut (zwei Arme gegen
#      denselben festen Gegner, Artefaktformat `games` als Dict mit Armen "0"/"1"). Hier spielen
#      die Arme GEGENEINANDER; "Gegner" waere der jeweils andere Arm. Dieses Skript ruft es
#      darum NICHT auf -- die Plattenpunkte je Seite kommen aus `plate_points_from_arena.py`.
#
# KEINE PIPE, keine eigene Umleitung (CLAUDE.md): mit run_in_background OHNE Pipe starten.
# NICHT STARTEN, solange eine andere Messung laeuft -- die Warteschleife unten prueft das.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

ART=evaluations/artifacts
NET=models/alphazero_v31-b01_brierbest.onnx          # DASSELBE Netz auf beiden Seiten
SPEC_ON=models/frozen_champions/v31-b01/spec.json    # envelope_search_c 1.0
SPEC_OFF=models/hull_off.spec.json                   # envelope_search_c 0.0, sonst gleich
NAME_ON=hull_on
NAME_OFF=hull_off
SEEDS="20261280 20261281"                            # Sonden-Band, bis 20261271 belegt

for f in "$NET" "$SPEC_ON" "$SPEC_OFF"; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done

echo "== EINFAKTORIALITAET: die beiden Specs duerfen sich in GENAU EINEM Feld unterscheiden"
python -X utf8 - "$SPEC_ON" "$SPEC_OFF" <<'PYEOF'
import io, json, sys
a = json.load(io.open(sys.argv[1], encoding="utf-8"))
b = json.load(io.open(sys.argv[2], encoding="utf-8"))
diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
for k in diff:
    print(f"   {k}: an={a.get(k)!r} aus={b.get(k)!r}")
print(f"   abweichende Felder: {len(diff)}")
sys.exit(0 if diff == ["envelope_search_c"] else 7)
PYEOF
[ $? -eq 0 ] || { echo "STOPP: die Specs sind nicht einfaktoriell -- der Lauf misst dann etwas anderes"; exit 7; }

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
wait_for_free_cpu "Huellen-Sonde"

echo ""
echo "########## HUELLEN-SONDE START $(date +%F' '%H:%M:%S)"
echo "   Netz beidseits: $NET"
echo "   A = $NAME_ON ($SPEC_ON)   B = $NAME_OFF ($SPEC_OFF)"

for S in $SEEDS; do
  OUT="$ART/gating_hull_on_vs_off_s${S}.json"
  echo ""
  echo "===== Seed $S $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$NET" --spec-a "$SPEC_ON" --model-b "$NET" --spec-b "$SPEC_OFF" \
    --name-a "$NAME_ON" --name-b "$NAME_OFF" \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$S" --threads 10 --log-games --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
  echo "-- Ablesung 1 (Form, Endbrett) und die Spaltenkennzahlen"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  echo "-- Plattenpunkte je Kriterium und Seite (Blockgroesse 5)"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_hull_on_vs_off_s${S}.json"
done

echo ""
echo "########## HUELLEN-SONDE FERTIG $(date +%F' '%H:%M:%S)"
echo "   Auswertung nach der VORAB festgelegten Lesart (par.14, Tabelle Form x Staerke):"
echo "   - Staerke 'faellt' = signifikanter Verlust bei n >= 150 Paaren ODER in der Replikation"
echo "     (McNemar, Block-z auf DIFFERENZIERTEN Blockwerten)"
echo "   - Form 'faellt' ist KEIN Signifikanztest, sondern ein Richtwert"
echo "   - die sechs Standard-Kennzahlen je Seite und als Differenz (CLAUDE.md)"
echo "   - den 56-gegen-62-Vorbehalt der Formzahlen benennen, nicht still lassen"
echo "   - Ergebnis in par.14 registrieren UND den Zeile-1-Kopf nachziehen, dann"
echo "     python tools/generate_prereg_index.py"
