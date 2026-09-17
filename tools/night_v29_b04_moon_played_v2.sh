#!/usr/bin/env bash
# Fahrplan 32b, Arm v29-b04: das Ziel des `moon`-Kopfs kommt aus der SUCHVERTEILUNG
# statt aus dem No-Op-Label (PREREG_moon_stack_order.md par.12.1, Zielquelle B1).
#
# WAS ER MISST: par.12.0 hat am Code belegt, dass `moon_order_target` ein No-Op ist --
# der Rundenloeser liest die Fabriken nicht, das Label ist IMMER die kanonische
# Reihenfolge. b05 hat den Kopf ganz abgeschaltet und war dadurch eher BESSER
# (par.12.6, 427:373, z=1,98). Offen blieb: traegt ein Kopf mit RICHTIGEM Ziel?
# Genau das ist b04.
#
# DIE ZIELQUELLE braucht KEINE neue Erzeugung: bei aktivem Fan-out (der Stand der
# v29-Erzeugung) faechert die Suche die Permutationen als eigene Kandidaten auf,
# jeder `policy`-Eintrag traegt seine `moon_order` MIT Besuchswahrscheinlichkeit.
# Die Korpus-Sonde fand 44,1 Prozent nicht-kanonische Reihenfolgen (Tor war 10).
#
# EIGENER DATENSATZ, zweifach abgesichert: `MOSAIC_MOON_TARGET_SOURCE=played` geht
# in BEIDE Cache-Schluessel ein -- in den BLOCK-Schluessel (file_cache_key.py, weil
# die Bloecke `moon_order_targets` je Datei tragen) UND in den FENSTER-Schluessel
# (corpus_dataset.py, fuer den Monolithen). Nachgeprueft: Block 022277a410ca gegen
# 5c950b9d7c7b, Fenster c696e7cb7bf7 gegen f7aa442a9d67. b03s Bloecke und Monolith
# bleiben unberuehrt.
# ACHTUNG, diese vier Schluessel sind UEBERHOLT: seit dem 2026-09-17 tragen beide
# Schluessel die Merkmals-Formelversion und die Merkmals-Quelle
# (PREREG_rust_data_layer.md par.9b). Die Aussage "eigener Datensatz, zweifach
# abgesichert" gilt weiter, die ZAHLEN nicht -- sie muessten vor einem Neulauf
# neu gerechnet werden.
#
# Die Kette laeuft EXKLUSIV und wartet, bis keine Messung mehr laeuft.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v28-'
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v29.json
export MOSAIC_MOON_TARGET_SOURCE=played
# Merkmalsbauer EXPLIZIT (2026-09-17, PREREG_rust_data_layer.md par.9a/par.9b):
# der Schalter steht seit heute in BEIDEN Cache-Schluesseln (Block und Fenster),
# entscheidet also ueber die Adresse der Bloecke und des Monolithen. Er stand in
# v29 uneinheitlich (b02/b03 setzten ihn, diese Kette nicht); ab jetzt setzt ihn
# JEDE Kette ausdruecklich auf 1, damit kein Arm die Semantik dessen erbt, der
# den Block zuerst gebaut hat (Bloecke werden memoisiert).
export MOSAIC_FEATURES_FROM_RUST=1
ART=evaluations/artifacts
SEED=20260941   # wie b01/b03/b05 -- der Arm soll sich nur im Ziel unterscheiden

[ -f "data/$MOSAIC_CARRIER_MANIFEST" ] || { echo "ABBRUCH: data/$MOSAIC_CARRIER_MANIFEST fehlt"; exit 1; }
[ -f data/window_v29.txt ] || { echo "ABBRUCH: data/window_v29.txt fehlt"; exit 1; }

# Gehaertete Wartebedingung, ZWEI Haerten:
#  1. NUR eine klare 0 gilt als frei (leere Antwort = belegt).
#  2. Der Prozess muss PYTHON sein. Grund ist ein 30-Minuten-Stillstand am
#     2026-09-16: dieses Skript wurde per Heredoc geschrieben UND im selben
#     Befehl gestartet, wodurch der Wrapper-bash seinen KOMPLETTEN Text (6.554
#     Zeichen, inklusive der Woerter `train.py` und `paired_gating.py`) in
#     seiner eigenen Kommandozeile trug. Der fruehere Filter (nur `-notmatch
#     pwsh|powershell`) fand ihn und wartete auf sich selbst -- und blockierte
#     ueber `build_cache_incremental` dazu die Kette einer Parallelsitzung.
#     Die `[t]rain`-Klammerschreibweise hilft hier NICHT: sie schuetzt gegen
#     den grep-Prozess selbst, nicht gegen einen Wrapper, der den Suchbegriff
#     als Nutzlast traegt.
# DESHALB AUCH: dieses Skript wird als DATEI gestartet (`bash tools/...sh`),
# nie per Heredoc-und-Start in einem Befehl.
maschine_frei() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '[p]aired_gating\.py|[f]rozen_referee_match\.py|[o]ffline_diagnosis|[t]rain\.py' -and \$_.Name -match 'python' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}
echo "########## b04-KETTE WARTET $(date +%F' '%H:%M:%S)"
while :; do
  maschine_frei && { echo "   Maschine frei ($(date +%H:%M:%S))"; break; }
  echo "   belegt ($(date +%H:%M:%S))"; sleep 120
done
sleep 10

echo ""
echo "== 1) Bloecke unter MOON_TARGET_SOURCE=played $(date +%F' '%H:%M:%S)"
echo "   Umgebung: MOON_TARGET_SOURCE=$MOSAIC_MOON_TARGET_SOURCE CARRIER=$MOSAIC_CARRIER_MANIFEST"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v29.txt
echo "   Exit $? ($(date +%H:%M:%S))"

echo ""
echo "== 2) Trainingsanteil, Schluessel, Monolith $(date +%H:%M:%S)"
python -X utf8 tools/window_train_split.py --file-list data/window_v29.txt --val-frac 0.05 \
  --val-pool '^selfplay_v28-' --encoder 2d --value-target-variant nortv \
  --train-list-out data/window_v29_b04_train.txt --val-list-out data/window_v29_b04_val.txt \
  > "$ART/v29_b04_split.txt"
cat "$ART/v29_b04_split.txt"
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v29_b04_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
echo "KEY=$KEY"
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v29_b04_train.txt \
  --merge-out "data/.cache_${KEY}.h5"
echo "   Exit $? ($(date +%H:%M:%S))"
ls -la "data/.cache_${KEY}.h5"

echo ""
echo "== 3) Training v29-b04 $(date +%F' '%H:%M:%S)"
python -X utf8 -u train.py --name v29-b04 --load v28-b02_brierbest \
  --file-list data/window_v29.txt --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac 0.05 --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 1.0 \
  --endgame-head --opp-points-head --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed $SEED \
  --moon-target-source played
echo "   Training Exit $? ($(date +%H:%M:%S))"

echo ""
echo "== 4) Tor 1 gegen b03, zwei Seeds a 200 Paaren OHNE Frueh-Stopp $(date +%H:%M:%S)"
A=models/alphazero_v29-b04_brierbest.onnx
B=models/alphazero_v29-b03_brierbest.onnx
SPEC=models/frozen_champions/v28-b02/spec.json
if [ -f "$A" ]; then
  for S in 20261130 20261131; do
    OUT="$ART/tor1_v29-b04_vs_b03_s${S}.json"
    echo ""
    echo "===== Seed $S $(date +%H:%M:%S)"
    python -X utf8 -u tools/paired_gating.py \
      --model-a "$A" --spec-a "$SPEC" --model-b "$B" --spec-b "$SPEC" \
      --name-a v29-b04 --name-b v29-b03 \
      --sims-a 400 --sims-b 400 --c-puct 1.5 \
      --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
      --seed "$S" --threads 10 --log-games --no-promote-winner --out "$OUT"
    echo "   Exit $? ($(date +%H:%M:%S))"
    python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
    python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
      --out "$ART/plate_points_tor1_b04_s${S}.json"
  done
else
  echo "UEBERSPRUNGEN: $A fehlt -- Training gescheitert?"
fi

echo ""
echo "########## b04-KETTE FERTIG $(date +%F' '%H:%M:%S)"
echo "   Faellig danach: Manifest-Diff gegen b03 (moon_target_source label -> played,"
echo "   sonst nichts), Verdikt in par.12.1 registrieren, Netz-Gesundheit par.6d."
