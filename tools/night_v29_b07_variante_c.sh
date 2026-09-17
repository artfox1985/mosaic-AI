#!/usr/bin/env bash
# Variante C, Arm v29-b07: Encoder-Seite der Tiling-Sicht, INPUT_SIZE 794 -> 884
# (PREREG_round_transition_search_sampling.md par.18; Bau 18.3, Kosten 18.4, Lesart 18.5,
# Kompilat-Stand 18.5 "Kompilat und Abnahme", diese Kette 18.6).
#
# VORAUSSETZUNGEN, die der KOORDINATOR VOR dem Start von Hand herstellt:
#   (a) `config.py` Zeile 49 auf `INPUT_SIZE = 884` gesetzt. Die Kette setzt sie NICHT selbst:
#       an dieser einen Zeile haengt die Scharfschaltung beider Python-Wege
#       (`neural_net.py:639` und der Fenster-Cache-Schluessel). Fehlt sie, bricht Stufe 0 ab.
#   (b) Kein anderer Lauf aktiv. Die Kette wartet zwar (`warte_frei`), aber `pip install`
#       scheitert, solange ein Python-Prozess das `.pyd` haelt (Training mit FROM_RUST=1,
#       paired_gating) -- deshalb steht das Warten VOR der Installation.
#   (c) Reihenfolge-Entscheid des Koordinators (STATUS Abschnitt 1, 2026-09-17 08:20):
#       Installation, INPUT_SIZE 884, Anker, Paritaetssonde, Kostentor und alles danach
#       laufen erst NACH Tor 1 von b08.
#
# NEBENLAST: jede Stufe ausser dem Training ist ein CPU-Auftrag und wartet auf eine freie CPU.
# Das Training (GPU) darf neben EINEM CPU-Auftrag laufen (docs/working_rules.md); Tor 1 wartet
# wieder. Keine Pipe und keine Umleitung hinter den langen Laeufen (CLAUDE.md).
#
# STOPP-PUNKTE (Nutzer-Entscheid, nichts reparieren): Anker-Drift oder -Konservierung ROT,
# Laengenfehler in der Paritaetssonde, gerissenes Kostentor.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
export MOSAIC_IGNORE_POLICY_TARGET_VALID=1
export MOSAIC_VAL_POOL='^selfplay_v28-'
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v29.json
# Planes-Semantik einheitlich FRISCH gerechnet (rust_data_layer par.9a/9b).
export MOSAIC_FEATURES_FROM_RUST=1
unset MOSAIC_MOON_TARGET_SOURCE
ART=evaluations/artifacts
SEED=20260941
WHEEL=engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl
ANKER=models/frozen_heuristics/hv4_anchor
CHAMP=models/alphazero_v28-b02_brierbest.onnx
SPEC=models/frozen_champions/v28-b02/spec.json
B03=models/alphazero_v29-b03_brierbest.onnx
# Referenz des Kostentors: der "aus"-Arm des rt-leaf-Kostentors, gleiche Form (20 Paare,
# 10 Threads, --log-games, Champion-Modell, Spec = Champion-Spec plus abgeschalteter Knopf).
KOSTEN_REF=evaluations/artifacts/rt_leaf_kosten_ohne_s20261151.json

echo "########## VARIANTE-C-KETTE (v29-b07) START $(date +%F' '%H:%M:%S)"

echo ""
echo "== 0) Vorbedingungen $(date +%H:%M:%S)"
grep -q "^INPUT_SIZE = 884" config.py || {
  echo "ABBRUCH: config.py traegt kein 'INPUT_SIZE = 884'. Der Koordinator setzt Zeile 49"
  echo "         VOR dem Start von Hand (par.18.3 Punkt 5); ohne sie bleibt der Python-Weg"
  echo "         auf 794 und die Paritaetssonde meldet nur die Zwischenstellung."
  exit 1
}
grep -q "FEATURE_FORMULA_VERSION" config.py || { echo "ABBRUCH: FEATURE_FORMULA_VERSION fehlt in config.py"; exit 2; }
[ -f "$WHEEL" ] || { echo "ABBRUCH: Wheel $WHEEL fehlt (maturin build vom 2026-09-17 10:14)"; exit 1; }
for f in "$CHAMP" "$SPEC" "$B03" data/window_v29.txt "data/$MOSAIC_CARRIER_MANIFEST" "$KOSTEN_REF"; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
[ -d "$ANKER" ] || { echo "ABBRUCH: Anker-Artefakt $ANKER fehlt"; exit 1; }
echo "   config.py: $(grep -n '^INPUT_SIZE' config.py | cut -c1-60)"
ls -l "$WHEEL"

cpu_frei() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { (\$_.CommandLine -match '[t]rain\.py|[p]aired_gating\.py|[f]rozen_referee_match\.py|[b]uild_cache|[c]ounterfactual_tiling|[o]ffline_diagnosis|[d]ead_unit_probe|[m]aturin|[w]indow_train_split' -and \$_.Name -match 'python') -or \$_.Name -match '^(cargo|rustc)' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}
warte_frei() {
  echo "########## b07-KETTE WARTET ($1) $(date +%F' '%H:%M:%S)"
  while :; do
    cpu_frei && { echo "   Maschine frei ($(date +%H:%M:%S))"; break; }
    echo "   belegt ($(date +%H:%M:%S))"; sleep 120
  done
  sleep 20
}

warte_frei "Wheel-Installation (pip scheitert, solange ein Prozess das .pyd haelt)"

echo ""
echo "== 1) Wheel installieren und Vertrag pruefen $(date +%F' '%H:%M:%S)"
python -X utf8 -m pip install --force-reinstall --no-deps "$WHEEL"
RC=$?; echo "   pip Exit $RC ($(date +%H:%M:%S))"
[ "$RC" = "0" ] || { echo "STOPP: Wheel-Installation gescheitert"; exit 10; }
python -X utf8 -u - <<'EOF'
import json, sys
import mosaic_rust
name = "tiling_projection_values_from_json"   # engine/src/lib.rs:1787, registriert :2342
ok_export = hasattr(mosaic_rust, name)
cfg = json.loads(mosaic_rust.engine_config_json())   # lib.rs:753, Feld input_size :768
print(f"   Export {name}: {'da' if ok_export else 'FEHLT'}")
print(f"   engine input_size={cfg['input_size']}  num_planes_channels={cfg['num_planes_channels']}")
print(f"   contract_hash={cfg['contract_hash']}  engine_version={cfg['engine_version']}")
if not ok_export:
    print("STOPP: das installierte Wheel kennt den Projektions-Export nicht -- altes Wheel?")
    sys.exit(11)
if int(cfg["input_size"]) != 884:
    print(f"STOPP: Rust meldet input_size {cfg['input_size']}, erwartet 884")
    sys.exit(12)
import config
print(f"   config.INPUT_SIZE={config.INPUT_SIZE} (muss 884 sein, beide Seiten scharf)")
sys.exit(0 if int(config.INPUT_SIZE) == 884 else 12)
EOF
RC=$?; [ "$RC" = "0" ] || { echo "STOPP: Vertragspruefung Exit $RC"; exit "$RC"; }

echo ""
echo "== 2) Anker-Invarianz (Skill mosaic-anchor-invariance) $(date +%F' '%H:%M:%S)"
echo "   2a) DRIFT: spielt der heutige Code hv4 noch wie das Artefakt? (Kosten gemessen 22,2 s)"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir "$ANKER" \
  --out "$ART/anchor_v2_drift_live_wheel_20260917_varC.json"
RC=$?; echo "   Drift Exit $RC ($(date +%H:%M:%S))"
[ "$RC" = "0" ] || { echo "STOPP: Anker-DRIFT ROT -- Nutzer-Entscheid (neues Leitersegment oder Aenderung zurueck), KEINE Reparatur"; exit 20; }
echo "   2b) KONSERVIERUNG: spielt das Artefakt noch wie am Einfriertag? (Kosten gemessen 13,4 s)"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir "$ANKER" --venv \
  --out "$ART/anchor_v2_conservation_20260917_varC.json"
RC=$?; echo "   Konservierung Exit $RC ($(date +%H:%M:%S))"
[ "$RC" = "0" ] || { echo "STOPP: Anker-KONSERVIERUNG ROT -- Umgebungsdrift, Nutzer-Entscheid"; exit 21; }

echo ""
echo "== 3) Paritaetssonde Rust gegen Python $(date +%F' '%H:%M:%S)"
echo "   Erwartung (par.18.6 und rust_data_layer par.9a): Flachvektor 884 Werte in BEIDEN"
echo "   Grundmengen gleich; in der Grundmenge 'corpus' bleibt der bekannte Kanal-76-Befund"
echo "   (Planes, Erreichbarkeit je Zelle, 2 von 300 Zustaenden, A2-Phantom-Fix) offen."
python -X utf8 -u tools/probes/feature_parity_rust_python.py
echo "   Sonde Exit $? ($(date +%H:%M:%S))"
python -X utf8 -u - <<'EOF'
import json, sys
p = "evaluations/artifacts/feature_parity_rust_python.json"
d = json.load(open(p, encoding="utf-8"))
shape_fehler = []
for r in d["populations"]:
    for key in ("flat", "planes"):
        fd = r[key].get("first_difference")
        print(f"   {r['population']}/{key}: n_equal {r[key]['n_equal']} von {r['n_states']}"
              + (f"  erste Abweichung {json.dumps(fd, ensure_ascii=False)}" if fd else ""))
        if fd and fd.get("kind") == "shape":
            shape_fehler.append(f"{r['population']}/{key}: {fd['python']} gegen {fd['rust']}")
print(f"   gate_passed={d['gate_passed']}  Artefakt {p}")
if shape_fehler:
    print("STOPP: LAENGENFEHLER -- " + "; ".join(shape_fehler))
    print("       Das ist kein Merkmalsbefund, sondern eine Zwischenstellung zwischen Wheel")
    print("       und config.INPUT_SIZE (par.18.6, Reihenfolge-Falle).")
    sys.exit(30)
print("   Kein Laengenfehler. Wertabweichungen werden BERICHTET, stoppen die Kette nicht.")
EOF
RC=$?; [ "$RC" = "0" ] || exit "$RC"

warte_frei "Kostentor"
echo ""
echo "== 4) Kostentor par.18.4: was kostet der Loeser im Encoder? $(date +%F' '%H:%M:%S)"
echo "   Form: Champion gegen sich selbst, Champion-Spec BEIDSEITS, 2 x 20 Paare = 80 Partien."
echo "   Gemessen wird allein die Wanduhr je Partie; die Siegquote ist hier bedeutungslos."
for S in 20261180 20261181; do
  OUT="$ART/variante_c_kosten_s${S}.json"
  echo ""
  echo "===== Kostenlauf Seed $S $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$CHAMP" --spec-a "$SPEC" --model-b "$CHAMP" --spec-b "$SPEC" \
    --name-a varc_kosten_a --name-b varc_kosten_b \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 20 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$S" --threads 10 --log-games --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
done
python -X utf8 -u - <<'EOF'
import json, sys
def sjp(p):
    return json.load(open(p, encoding="utf-8"))["laufzeit"]["s_je_partie"]
neu = [sjp(f"evaluations/artifacts/variante_c_kosten_s{s}.json") for s in (20261180, 20261181)]
mittel = sum(neu) / len(neu)
# Referenz, gleiche Form (20 Paare, 10 Threads, --log-games, Champion-Modell):
# der "aus"-Arm des rt-leaf-Kostentors vom 2026-09-17 01:35.
ref = sjp("evaluations/artifacts/rt_leaf_kosten_ohne_s20261151.json")
# Zweite Orientierung, ANDERE Form (200 Paare): der "aus"-Arm des A/B, par.17.9.
ref200 = sjp("evaluations/artifacts/rt_leaf_on_vs_off_s20261152.json")
auf = (mittel / ref - 1.0) * 100.0
auf200 = (mittel / ref200 - 1.0) * 100.0
print(f"KOSTENTOR Variante C: neu {neu[0]:.3f} / {neu[1]:.3f} s je Partie, Mittel {mittel:.3f}")
print(f"   gegen Referenz 20 Paare {ref:.3f} s je Partie: Aufschlag {auf:+.1f} Prozent (Schwelle +25)")
print(f"   gegen Referenz 200 Paare {ref200:.3f} s je Partie: Aufschlag {auf200:+.1f} Prozent (nur Orientierung, andere Form)")
open("evaluations/artifacts/variante_c_kostentor_verdikt.txt", "w", encoding="utf-8").write(
    "prereg=PREREG_round_transition_search_sampling.md par.18.4\n"
    "form=Champion gegen sich selbst, Champion-Spec beidseits, 2 x 20 Paare, 10 Threads, --log-games\n"
    f"neu_s20261180={neu[0]}\nneu_s20261181={neu[1]}\nneu_mittel={mittel}\n"
    f"referenz_20paare={ref}\nreferenz_quelle_20paare=rt_leaf_kosten_ohne_s20261151.json\n"
    f"aufschlag_prozent={auf}\n"
    f"referenz_200paare={ref200}\nreferenz_quelle_200paare=rt_leaf_on_vs_off_s20261152.json\n"
    f"aufschlag_prozent_gegen_200paare={auf200}\n"
    f"schwelle_prozent=25\nverdikt={'HAELT' if auf <= 25.0 else 'GERISSEN'}\n")
raise SystemExit(0 if auf <= 25.0 else 3)
EOF
RC=$?
if [ "$RC" != "0" ]; then
  echo "########## KOSTENTOR GERISSEN (Exit $RC) -- Blockbau, Training und Tor 1 NICHT gestartet."
  echo "   Nutzer-Entscheid (par.18.4). Verdikt: $ART/variante_c_kostentor_verdikt.txt"
  exit 3
fi
echo "   Kostentor HAELT ($(date +%H:%M:%S))"

warte_frei "Split, Bloecke, Monolith"
echo ""
echo "== 5) Trainingsanteil und Schluessel (884, Formel-Version, FROM_RUST=1) $(date +%H:%M:%S)"
python -X utf8 tools/window_train_split.py --file-list data/window_v29.txt --val-frac 0.05 \
  --val-pool '^selfplay_v28-' --encoder 2d --value-target-variant nortv \
  --train-list-out data/window_v29_b07_train.txt --val-list-out data/window_v29_b07_val.txt \
  > "$ART/v29_b07_split.txt"
cat "$ART/v29_b07_split.txt"
KEY=$(grep -o "Fenster-Schluessel des Trainingsanteils: [0-9a-f]*" "$ART/v29_b07_split.txt" | awk '{print $NF}')
[ -n "$KEY" ] || { echo "STOPP: kein Schluessel"; exit 13; }
echo "KEY=$KEY"
if [ -f data/window_v29_b08_train.txt ]; then
  cmp -s data/window_v29_b07_train.txt data/window_v29_b08_train.txt \
    && echo "   Trainingsliste byte-gleich mit b08 (und damit mit b03)" \
    || echo "   WARNUNG: Trainingsliste weicht von b08 ab"
fi
[ "$KEY" = "421448d12eb8" ] && {
  echo "STOPP: Schluessel ist der 794er Schluessel von b08 -- die 884 ist nicht im Schluessel"
  echo "       angekommen (file_cache_key.py / corpus_dataset.py lesen config.INPUT_SIZE)."
  exit 17
}

echo ""
echo "== 6) Bloecke und Monolith unter $KEY $(date +%F' '%H:%M:%S)"
CACHE="data/.cache_${KEY}.h5"
T0=$(date +%s)
python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d \
  --value-target-variant nortv --workers 6 --file-list data/window_v29_b07_train.txt \
  --merge-out "$CACHE"
echo "   Exit $? ($(date +%H:%M:%S)); Bloecke plus Merge: $(( $(date +%s) - T0 )) s Wanduhr"
echo "   Bestandszeit zum Vergleich (docs/measured_runtimes.md, 2026-09-17, 794 ohne Projektion):"
echo "   2.800 Dateien, 6 Worker, plus Merge = 1.964 s"
[ -f "$CACHE" ] || { echo "STOPP: Monolith fehlt"; exit 14; }
ls -la "$CACHE"
python -X utf8 -c "import h5py,sys; h=h5py.File(sys.argv[1],'r'); k=h.attrs['mosaic_cache_key']; print('   Stempel:',k); sys.exit(0 if k==sys.argv[2] else 16)" "$CACHE" "$KEY" || { echo "STOPP: Stempel passt nicht zum Schluessel"; exit 16; }

echo ""
echo "== 7) Training v29-b07 (Rezept GENAU b03, manifest_train_v29-b03_20260914_111513.json) $(date +%F' '%H:%M:%S)"
echo "   Warmstart 794 -> 884: train.py:1689-1698 fuellt die fehlenden Eingangsspalten von"
echo "   flat_branch.0.weight mit NULL auf (additive Eingabe, Muster v24-b04, 755 -> 794)."
echo "   Das Netz ist im ersten Schritt exakt das alte; die 90 neuen Spalten wirken erst,"
echo "   wenn das Training sie ankoppelt. Die Zeile 'flat_branch.0.weight: Eingangsbreite"
echo "   794 -> 884, 90 neue Spalten null-initialisiert' MUSS in der Ausgabe erscheinen --"
echo "   bleibt sie aus, startet der Flach-Zweig"
echo "   frisch und der Arm waere gegen b03 nicht vergleichbar."
python -X utf8 -u train.py --name v29-b07 --load v28-b02_brierbest \
  --file-list data/window_v29.txt --cache-file "$CACHE" \
  --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac 0.05 --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 1.0 \
  --opp-points-head --endgame-head --moon-loss-weight 1.0 \
  --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed $SEED
echo "   Training Exit $? ($(date +%H:%M:%S))"

if [ -f models/alphazero_v29-b07_brierbest.onnx ]; then
  A=models/alphazero_v29-b07_brierbest.onnx
elif [ -f models/alphazero_v29-b07.onnx ]; then
  A=models/alphazero_v29-b07.onnx
  echo "HINWEIS: kein _brierbest -- beste Epoche war die letzte, finales Modell wird genommen"
else
  echo "UEBERSPRUNGEN: kein Modell v29-b07 -- Training gescheitert?"; exit 15
fi

warte_frei "Tor 1"
echo ""
echo "== 8) Tor 1 b07 gegen b03, zwei Seeds a 200 Paaren, ohne Frueh-Stopp $(date +%H:%M:%S)"
echo "   Modell A: $A"; ls -l "$A"
for S in 20261190 20261191; do
  OUT="$ART/tor1_v29-b07_vs_b03_s${S}.json"
  echo ""
  echo "===== Seed $S $(date +%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$A" --spec-a "$SPEC" --model-b "$B03" --spec-b "$SPEC" \
    --name-a v29-b07 --name-b v29-b03 \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$S" --threads 10 --log-games --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_tor1_b07_s${S}.json"
done

echo ""
echo "########## VARIANTE-C-KETTE FERTIG $(date +%F' '%H:%M:%S)"
echo "   Faellig danach:"
echo "   1. Manifest-Diff b07 gegen b03 (manifest_train_v29-b03_20260914_111513.json): erwartet"
echo "      sind GENAU name, cache_file und die INPUT_SIZE-abhaengigen Felder (input_size 884,"
echo "      Samplezahl/Schluessel des Monolithen). Jedes weitere abweichende Feld ist ein Befund."
echo "   2. Verdikt nach par.18.5: Siege und Punktemarge auf BLOCK-Ebene, dazu die beiden"
echo "      benannten Nutzniesser (volle Spalten je Partie, belegte Spezialfelder je Partie)."
echo "   3. Netz-Gesundheit par.6d des Fensters: leben die 90 neuen Spalten (Spaltennorm > 0)?"
echo "      Norm exakt 0 heisst 'nie gesehen' -- dann ist ein Nullbefund kein Befund ueber C."
echo "   4. Sechs Standard-Kennzahlen (CLAUDE.md) je Seite und als Differenz."
echo "   5. Laufzeiten nach docs/measured_runtimes.md: Blockbau (gegen 1.964 s), Training,"
echo "      Tor 1 je Seed, plus das Kostentor-Verdikt."
echo "   6. Registrierung in PREREG_round_transition_search_sampling.md par.18 und Zeile-1-Kopf,"
echo "      danach python tools/generate_prereg_index.py."
