#!/usr/bin/env bash
# Fahrplan 32b, Arm v29-b05: Ablation des `moon`-Kopfs (PREREG_moon_stack_order.md par.12.1).
#
# WARUM DIESER ARM ZUERST: er braucht KEINEN Bau. `--moon-loss-weight` existiert
# (train.py:575), und das Gewicht ist kein Daten-Schluessel -- b05 laeuft auf
# demselben 794er-Monolithen wie b03. b04 (Ziel aus der gespielten Reihenfolge)
# braucht dagegen Datenpfad, eigenen Fenster-Schluessel und einen neuen Monolith.
#
# WAS ER MISST: par.12.0 hat am Code belegt, dass das heutige Trainingsziel des
# Kopfs ein No-Op ist -- der Rundenloeser liest die Fabriken nicht, das Label ist
# IMMER die kanonische Reihenfolge. Der Kopf hat also mit Gewicht 1,0 auf eine
# Konstante trainiert. b05 nimmt ihm dieses Ziel ganz weg. Traegt b05, hat das
# Rauschziel Policy-Qualitaet gekostet, und die Task-#38-Behauptung ("der Kopf
# hilft") ist erstmals gemessen statt behauptet.
#
# REZEPT = b03 (Manifest models/manifest_train_v29-b03_20260914_111513.json),
# geaendert ist GENAU ein Flag: --moon-loss-weight 0.
# Die Flags --val-pool, --ignore-policy-target-valid und --bootstrap-coherence
# GIBT ES IN train.py NICHT; sie kommen aus der Umgebung (wie in der v29-Kette).
# Early-Stop, Epoch-Checkpoint, Snapshot und Head-Warmstart sind Default an.
# Abbruch? Derselbe Aufruf plus --resume.
#
# GPU-LAUF: daneben darf EIN CPU-Auftrag laufen (CLAUDE.md), nicht mehr.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
export MOSAIC_VAL_POOL='^selfplay_v28-'
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
# PFLICHT, und beim ersten Versuch am 2026-09-15 VERGESSEN: ohne diese Variable
# findet `corpus_dataset` kein Traeger-Manifest, und dann traegt JEDE Datei
# Policy (corpus_dataset.py:142 "carrier_set is None -> JEDE Datei traegt").
# b03 hatte 580 Traeger-Dateien, der erste b05-Versuch 2947 -- also das
# Fuenffache an Policy-Signal. Der Arm waere damit zweifaktoriell gewesen und
# haette nicht den moon-Kopf gemessen, sondern die Traegermenge.
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v29.json
SEED=20260941   # derselbe Seed wie b01/b03 -- der Arm soll sich nur im Ziel unterscheiden

for f in data/window_v29.txt models/alphazero_v28-b02_brierbest.onnx; do
  [ -e "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done

echo "== v29-b05 (moon-Kopf ablatiert) START $(date +%F' '%H:%M:%S)"
echo "   Umgebung: CARRIER_MANIFEST=$MOSAIC_CARRIER_MANIFEST VAL_POOL=$MOSAIC_VAL_POOL IGNORE_PTV=$MOSAIC_IGNORE_POLICY_TARGET_VALID"
# Der Name wird gegen data_dir aufgeloest (corpus_dataset.py:401), liegt also
# unter data/ -- hier genauso pruefen, sonst schlaegt die Pruefung falsch an.
[ -f "data/$MOSAIC_CARRIER_MANIFEST" ] || { echo "ABBRUCH: data/$MOSAIC_CARRIER_MANIFEST fehlt"; exit 1; }
python -X utf8 -u train.py --name v29-b05 --load v28-b02_brierbest \
  --file-list data/window_v29.txt --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac 0.05 --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 1.0 \
  --endgame-head --opp-points-head --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed $SEED \
  --moon-loss-weight 0
echo "   Training Exit $? ($(date +%H:%M:%S))"

echo "== FERTIG $(date +%F' '%H:%M:%S)"
echo "   Faellig danach: Manifest-Diff gegen b03 (genau ein Feld: moon_loss_weight),"
echo "   dann Tor 1 gegen b03 mit ZWEI Seeds a 200 Paaren OHNE Frueh-Stopp, dazu"
echo "   Netz-Gesundheit Punkte 1-2 (PREREG_v29_window.md par.6d)."
