#!/usr/bin/env bash
# v30-ERZEUGUNG, REST (Klassen 2 und 3): der Sockel laeuft seit 14:50:04 verwaist weiter (Wrapper 14:53 beendet,
# weil seine Wiedervorlage-Pruefung pickle.load auf gzip rief und das Self-Play getoetet haette); diese Kette wartet
# auf sein Ende, prueft den ersten Sockel-Record (gzip) und faehrt die beiden Schwarm-Klassen.
# Ursprung: die drei Klassen nacheinander (Muster tools/night_v29_generate.sh, Befehle aus
# PREREG_v29_window.md par.5; Seeds 20260930/31/32). FREIGABE des Nutzers 2026-09-17: "du hast auch die
# freigabe mit den self plays fuer v30 loszulegen" (STATUS Abschnitt 6 Punkt 21).
#
# VORAUSSETZUNGEN (Punkt 21, alle VOR dem ersten Self-Play, sonst fallen die Merkmale nach v31):
#   (1) Wheel mit Weg A + R3 (NUM_ACTIONS 414) und R2/P.16 (INPUT_SIZE 888) installiert und abgenommen
#       (Anker-Drift/-Konservierung, Paritaets-Fixture des Champions, Kostentor) -- die Kette prueft nur
#       `input_size` 888 und `return_order_mode` im Manifest-Export.
#   (2) Champion-Entscheid (STATUS Punkt 18): der Generator kommt ueber die Umgebung herein --
#       MOSAIC_V30_GENERATOR = ONNX-Pfad, MOSAIC_V30_GEN_NAME = Namensstamm der Dateien
#       (Konvention: Dateien heissen nach dem GENERATOR, z.B. v29-b07 -> selfplay_v29-b07-policy_*).
#   (3) Generationswechsel nach /mosaic-generation-turnover (Einfrieren, restic, STATUS-Neufassung).
#
# SPEC: models/v30_generation.spec.json = start_by_search_on.spec.json PLUS return_order_mode 1
# (PREREG_dome_return_order.md par.12.6, Korrektheitsentscheid). MOSAIC_STACK_DRAW_RESEARCH=1 wie v29.
#
# WIEDERVORLAGE nach den ersten Dateien (Punkt 21): P.12 `designs`, P.16 `designs_ordered`, Mond- und
# Rueckgabe-Knoten muessen im Record stehen. Die Kette prueft `designs_ordered` selbst und STOPPT die
# Erzeugung, wenn das Feld fehlt; die Knoten prueft der Koordinator mit dem Werkzeug des Baus.
#
# DANEBEN GEHOERT DER CACHE-WAECHTER unter der Trainings-Umgebung (v29-Kopf), Schluessel-Knoepfe:
#   MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_FEATURES_FROM_RUST=1 python -X utf8 -u \
#     tools/build_cache_incremental.py --data-dir data --encoder 2d --value-target-variant nortv \
#     --workers 3 --watch --wartezeit 60 --leerlauf-abbruch 100000
#
# ERWARTETE DAUER (v28 gemessen 9,92 h fuer 3 x 4.000 @100; 888-Encoder rund +5 Prozent, ANNAHME): rund 10,5 h.
# Aufruf: MOSAIC_V30_GENERATOR=models/... MOSAIC_V30_GEN_NAME=v29-bXX bash tools/night_v30_generate.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
export MOSAIC_STACK_DRAW_RESEARCH=1
MODEL="${MOSAIC_V30_GENERATOR:?ABBRUCH: MOSAIC_V30_GENERATOR (ONNX-Pfad des Generators) fehlt -- Champion-Entscheid Punkt 18}"
GEN="${MOSAIC_V30_GEN_NAME:?ABBRUCH: MOSAIC_V30_GEN_NAME (Namensstamm, z.B. v29-b07) fehlt}"
SPEC=models/v30_generation.spec.json

[ -f "$MODEL" ] || { echo "ABBRUCH: $MODEL fehlt"; exit 1; }
[ -f "$SPEC" ] || { echo "ABBRUCH: $SPEC fehlt"; exit 1; }
python -X utf8 - <<'EOF' || exit 2
import json, sys, mosaic_rust
d = json.loads(mosaic_rust.engine_config_json())
ok = str(d.get("input_size")) == "888" and "return_order_mode" in d
print("   engine_config: input_size", d.get("input_size"), "return_order_mode", d.get("return_order_mode"),
      "num_actions", d.get("num_actions", "?"))
if not ok:
    print("ABBRUCH: installiertes Wheel traegt nicht INPUT_SIZE 888 mit return_order_mode -- Punkt 21 (1) offen")
    sys.exit(2)
EOF

busy() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '[s]elf_play\.py|[t]rain\.py|[p]aired_gating|[a]nchor|[f]rozen_referee|[b]uild_cache_parallel|[c]argo|[m]aturin' -and \$_.Name -match 'python' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" != "0" ]
}
echo "== WARTEN auf das Ende des Sockels (self_play) und eine freie Maschine $(date +%F' '%H:%M:%S)"
while busy; do echo "   noch belegt ($(date +%H:%M:%S))"; sleep 300; done
echo "   frei ($(date +%H:%M:%S))"

first_record_check() {
  # Wiedervorlage P.16: das Record-Feld designs_ordered muss am eigenen Block stehen.
  python -X utf8 - "$1" <<'EOF'
import glob, json, pickle, sys
files = sorted(glob.glob(f"data/selfplay_{sys.argv[1]}_*.pkl"))
if not files:
    print("   WIEDERVORLAGE: noch keine Datei"); sys.exit(3)
import gzip
try:
    with gzip.open(files[0], "rb") as f:   # Self-Play-Records liegen gzip-komprimiert (Vorfall 2026-09-18: pickle.load scheitert am gzip-Magic 0x1f)
        recs = pickle.load(f)
except OSError:
    with open(files[0], "rb") as f:
        recs = pickle.load(f)
blob = json.dumps(recs, default=str)
hit = "designs_ordered" in blob
print(f"   WIEDERVORLAGE {files[0]}: designs_ordered {'vorhanden' if hit else 'FEHLT'}")
sys.exit(0 if hit else 4)
EOF
}

echo "== 1b) Wiedervorlage am fertigen Sockel $(date +%F' '%H:%M:%S)"
first_record_check "${GEN}-policy" || { echo "STOPP: Wiedervorlage P.16 rot -- Klassen 2 und 3 werden NICHT gestartet"; exit 4; }
echo "   Sockel-Dateien: $(ls data/ | grep -c "^selfplay_${GEN}-policy_")"

echo "== 2) Schwarm a, 4.000 Partien, value-only, temperiert $(date +%F' '%H:%M:%S)"
python -X utf8 -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --value-only --version "${GEN}-value-tempc" \
  --threads 11 --chunk 10 --per-file 10 --seed 20260931 \
  --action-temp 2 --deviate-prob 1.0 --start-slot-random-p 0.15
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c "^selfplay_${GEN}-value-tempc_")"

echo "== 3) Schwarm b, 4.000 Identitaeten, value-only, Ausflug $(date +%F' '%H:%M:%S)"
python -X utf8 -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --value-only --version "${GEN}-value-excursion" \
  --threads 11 --chunk 10 --per-file 10 --seed 20260932 \
  --excursion-prob 1.0 --tau-argmax-from-move 1 --no-root-noise --start-slot-random-p 0.15
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c "^selfplay_${GEN}-value-excursion_")"

echo "== v30-ERZEUGUNG FERTIG $(date +%F' '%H:%M:%S)"
echo "   Naechster Schritt: Tor 0 / Tor 2a je Klasse (corpus_sanity_check.py), Fenster v30 (Pinning: Messdateien"
echo "   ausschliessen), Bloecke unter 888, Training KALT nach dem v30-Rezept (STATUS Abschnitt 4), Gating."
