#!/usr/bin/env bash
# v29-ERZEUGUNG: die drei Klassen nacheinander, Generator v28-b02.
# Befehle aus PREREG_v29_window.md par.5 (Seeds 20260920/21/22).
#
# FREIGABEN des Nutzers 2026-09-13:
#   02:10 Schwarm mit 100 Sims ("du kannst nach abschluss selbstaendig den skill starten
#         fuer die schwarm erzeugung mit 100 sims")
#   11:58 Sockel ebenfalls hier und ebenfalls 100 Sims ("lass den sockel ebenfalls bei dir
#         laufen mit 100 sims") -- die zwischenzeitliche 400er-Wahl ist damit zurueckgezogen.
#   11:15 MOSAIC_STACK_DRAW_RESEARCH=1 ("ja dann schalten wir ihn ein"). Der Knopf hat KEINE
#         Spec-Entsprechung und wird je Prozess einmal per OnceLock gelesen; self_play.py
#         startet jeden Chunk als frischen Prozess, der die Elternumgebung erbt. Seit Wheel 1
#         steht er im Lauf-Manifest (engine_config_json), ist also nachher belegbar --
#         vorher war er es in KEINER Generation (PREREG_chance_nodes.md, Nachtrag 2026-09-13).
#
# SPEC: start_by_search_on.spec.json = Champion-Spec PLUS start_by_search 1 (beide Felder
# verglichen, sonst identisch). Streuung der Startsetzung 0,15 je Spieler (par.6b).
#
# MODELL: die Bestandsdatei, nicht der Artefakt-Pfad -- sha256 1cc296ee... ist identisch mit
# models/frozen_champions/v28-b02/model.onnx (geprueft 2026-09-13), und v28 nahm denselben Weg.
#
# ERWARTETE DAUER (Hochrechnung aus gemessenen Werten, NICHT auf dieser Groesse gemessen):
# Sockel rund 4,4 h, Schwarm zusammen rund 6,4 h, gesamt rund 10,8 h. Vergleich: die
# v28-Erzeugung lief 35.726 s = 9,92 h (docs/measured_runtimes.md).
#
# DANEBEN GEHOERT DER CACHE-WAECHTER, zwingend unter der Trainings-Umgebung:
#   MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_FEATURES_FROM_RUST=1 python -X utf8 -u \
#     tools/build_cache_incremental.py --data-dir data --encoder 2d \
#     --value-target-variant nortv --workers 3 --watch --wartezeit 60 --leerlauf-abbruch 100000
# Die Variablen stehen IM Datei-Schluessel; ohne sie landen die Bloecke in einem Namensraum,
# den das Training nie adressiert (2026-09-09: 2.680 tote Bloecke, docs/pitfalls.md).
#
# Aufruf: bash tools/night_v29_generate.sh   (Hintergrundaufgabe, keine Pipe)
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
export MOSAIC_STACK_DRAW_RESEARCH=1
MODEL=models/alphazero_v28-b02_brierbest.onnx
SPEC=models/start_by_search_on.spec.json

# Wartebedingung, GEHAERTET: der Filter darf sich nicht selbst treffen (jede erste Stelle in
# eine Zeichenklasse), und eine leere Antwort gilt als BELEGT. Beide Fallen sind hier schon
# eingetreten: am 2026-09-09 stand eine Kette 35 Minuten still, und in der Nacht auf den
# 2026-09-13 startete die wartende Leiter-Kante deshalb ueberhaupt nicht.
busy() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '[s]elf_play\.py|[t]rain\.py|[p]aired_gating|[a]nchor_arena|[f]rozen_referee' -and \$_.Name -notmatch 'pwsh|powershell' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" != "0" ]
}

echo "== WARTEN auf eine freie Maschine $(date +%F' '%H:%M:%S)"
while busy; do echo "   noch belegt ($(date +%H:%M:%S))"; sleep 300; done
echo "   frei ($(date +%H:%M:%S))"

echo "== 1) Sockel (Traeger), 4.000 Partien, policy-aktiv $(date +%F' '%H:%M:%S)"
python -X utf8 -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --version v28-b02-policy \
  --threads 11 --chunk 10 --per-file 10 --seed 20260920 \
  --tau-argmax-from-move 1 --deviate-prob 1.0 --start-slot-random-p 0.15
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c '^selfplay_v28-b02-policy_')"

echo "== 2) Schwarm a, 4.000 Partien, value-only, temperiert $(date +%F' '%H:%M:%S)"
python -X utf8 -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --value-only --version v28-b02-value-tempc \
  --threads 11 --chunk 10 --per-file 10 --seed 20260921 \
  --action-temp 2 --deviate-prob 1.0 --start-slot-random-p 0.15
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c '^selfplay_v28-b02-value-tempc_')"

echo "== 3) Schwarm b, 4.000 Identitaeten, value-only, Ausflug $(date +%F' '%H:%M:%S)"
python -X utf8 -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --value-only --version v28-b02-value-excursion \
  --threads 11 --chunk 10 --per-file 10 --seed 20260922 \
  --excursion-prob 1.0 --tau-argmax-from-move 1 --no-root-noise --start-slot-random-p 0.15
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c '^selfplay_v28-b02-value-excursion_')"

echo "== v29-ERZEUGUNG FERTIG $(date +%F' '%H:%M:%S)"
echo "   Naechster Schritt: Tor 0 / Tor 2a je Klasse (corpus_sanity_check.py), dann die Kette."
echo "   FENSTER-PINNING nicht vergessen: die Messdateien der Sims-Kurve"
echo "   (data/selfplay_depth<S>-v28b02_*.pkl) gehoeren beim Fensterbau in MOSAIC_DATA_EXCLUDE."
