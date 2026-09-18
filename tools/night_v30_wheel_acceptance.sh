#!/usr/bin/env bash
# ABNAHME des 414/888-Wheels UND der Generator-Identitaet v29-b10
# (PREREG_minimal_strength_core.md par.10.12; Weg A / R3 in
# PREREG_moon_stack_order.md par.12.6/12.10, R2 / P.16 und return_order_mode in
# PREREG_dome_return_order.md par.12.7/12.8).
#
# WAS HIER ABGENOMMEN WIRD, in dieser Reihenfolge:
#   das Wheel (Vertrag, Anker, Paritaet), dann das ARTEFAKT v29-b10 (Polsterung
#   und Export), dann seine KOSTEN, dann seine STAERKE gegen das ungepolsterte
#   Original, zuletzt die Frage, ob die neuen Knoten im Record ueberhaupt
#   ankommen. Erst danach darf die v30-Erzeugung starten.
#
# GENERATOR-ENTSCHEID (Nutzer 2026-09-18, "ja nimm es so in die kette auf"):
# Generator der v30-Erzeugung wird `v29-b07` (884 Eingaenge, 406er-Policy) mit
# auf 414 GEPOLSTERTEM Policy-Kopf, acht Nullzeilen, ohne Training. Weil das ein
# anderes Artefakt ist als `v29-b07_brierbest`, traegt es einen eigenen Namen:
# `v29-b10` (Regel feedback_measured_identity_gets_own_bxx).
#
# VORAUSSETZUNGEN, die der KOORDINATOR VOR dem Start von Hand herstellt:
#   (a) `config.py`: `INPUT_SIZE = 888` (Zeile 49) und `NUM_ACTIONS = 414`
#       (Zeile 57). Die Kette setzt sie NICHT selbst -- an diesen zwei Zeilen
#       haengt die Scharfschaltung des Python-Wegs und der Cache-Schluessel.
#   (b) Wheel mit Weg A + R3 und R2/P.16 gebaut, also NEUER als
#       `engine/src/net_mcts.rs` (Stufe 0 prueft das mit `-nt`).
#   (c) Kein anderer CPU-Lauf. `pip install` scheitert, solange ein
#       Python-Prozess das `.pyd` haelt -- deshalb steht das Warten VOR der
#       Installation.
#
# NEBENLAST: jede Stufe ist ein CPU-Auftrag und wartet auf eine freie CPU
# (CLAUDE.md "Messungen laufen EXKLUSIV"). Ein GPU-Training daneben ist erlaubt
# (docs/working_rules.md, "Auslastung"); dafuer gibt es MOSAIC_CHAIN_NO_WAIT=1.
# Keine Pipe und keine Umleitung hinter den langen Laeufen.
#
# STOPP-PUNKTE (Nutzer-Entscheid, nichts reparieren): Vertrag falsch,
# Anker-Drift oder -Konservierung ROT, Laengenfehler in der Paritaetssonde,
# Polsterung oder Export gescheitert, Engine meldet nicht policy_width 414,
# gerissenes Kostentor, gerissene A/B-Marge, Wiedervorlage-Probe (a) oder (b) rot.
#
# MESSDATEIEN: Stufe 7 erzeugt `data/selfplay_v29-b10-probe_*.pkl`. Das sind
# MESSDATEIEN und gehoeren beim Bau des v30-Fensters in MOSAIC_DATA_EXCLUDE
# (Regel feedback_window_pinning_during_generation, Anlass b05-Konfundierung) --
# sonst laufen 20 Partien mit Suchtiefe 100 still im Trainingsfenster mit.
#
# Aufruf:  bash tools/night_v30_wheel_acceptance.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

ART=evaluations/artifacts
WHEEL=engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl
ANKER=models/frozen_heuristics/hv4_anchor
SRC=models/alphazero_v29-b07_brierbest.pth
B07=models/alphazero_v29-b07_brierbest.onnx
GEN=v29-b10
B10=models/alphazero_v29-b10.onnx
SPEC=models/v30_generation.spec.json
# Referenz des Kostentors: 12,0 s je Partie -- Tor 1 b07 gegen b03 auf dem
# 884-Wheel, Seed 20261191, 200 Paare, 10 Threads, --log-games, EXKLUSIV
# (docs/measured_runtimes.md Zeile 187: "12,4 / 12,0 s je Partie"). Genommen wird
# der kleinere der beiden Seeds, also die STRENGERE Referenz.
KOSTEN_REF=12.0
KOSTEN_SCHWELLE=25

echo "########## v30-WHEEL-ABNAHME START $(date +%F' '%H:%M:%S)"

cpu_frei() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { (\$_.CommandLine -match '[t]rain\.py|[p]aired_gating\.py|[f]rozen_referee_match\.py|[s]elf_play\.py|[b]uild_cache|[c]ounterfactual_tiling|[o]ffline_diagnosis|[d]ead_unit_probe|[m]aturin|[w]indow_train_split' -and \$_.Name -match 'python') -or \$_.Name -match '^(cargo|rustc)' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}
warte_frei() {
  if [ "${MOSAIC_CHAIN_NO_WAIT:-0}" = "1" ]; then
    echo "   Warteschleife uebersprungen (MOSAIC_CHAIN_NO_WAIT=1, GPU-Training daneben erlaubt) $(date +%H:%M:%S)"
    return 0
  fi
  echo "########## v30-ABNAHME WARTET ($1) $(date +%F' '%H:%M:%S)"
  while :; do
    cpu_frei && { echo "   Maschine frei ($(date +%H:%M:%S))"; break; }
    echo "   belegt ($(date +%H:%M:%S))"; sleep 120
  done
  sleep 20
}

echo ""
echo "== 0) Vorbedingungen $(date +%H:%M:%S)"
grep -q "^INPUT_SIZE = 888" config.py || {
  echo "ABBRUCH: config.py traegt kein 'INPUT_SIZE = 888' (Zeile 49). Der Koordinator setzt sie VOR"
  echo "         dem Start von Hand; ohne sie bleibt der Python-Weg auf 884 und die Polsterung in"
  echo "         Stufe 4 wuerde eine falsche Breite erzeugen."
  exit 1
}
grep -q "^NUM_ACTIONS = 414" config.py || {
  echo "ABBRUCH: config.py traegt kein 'NUM_ACTIONS = 414' (Zeile 57). Ohne sie polstert Stufe 4 den"
  echo "         Policy-Kopf nicht, und die neuen Knoten haetten im Netz keine Ausgabe."
  exit 1
}
[ -f "$WHEEL" ] || { echo "ABBRUCH: Wheel $WHEEL fehlt (maturin build noch offen)"; exit 1; }
[ "$WHEEL" -nt engine/src/net_mcts.rs ] || {
  echo "ABBRUCH: $WHEEL ist NICHT neuer als engine/src/net_mcts.rs -- das Wheel stammt noch von vor"
  echo "         der Weg-A/R3-Aenderung. Erst neu bauen, dann diese Kette starten."
  exit 1
}
for f in "$SRC" "$B07" "$SPEC"; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
[ -d "$ANKER" ] || { echo "ABBRUCH: Anker-Artefakt $ANKER fehlt"; exit 1; }
grep -q '"return_order_mode"' "$SPEC" || {
  echo "ABBRUCH: $SPEC traegt kein return_order_mode -- die Spec des v30-Generators muss es tragen"
  echo "         (PREREG_dome_return_order.md par.12.6, Korrektheitsentscheid)."
  exit 1
}
echo "   config.py: $(grep -n '^INPUT_SIZE' config.py | cut -c1-40)"
echo "   config.py: $(grep -n '^NUM_ACTIONS' config.py | cut -c1-40)"
ls -l "$WHEEL" "$SRC" "$B07"

warte_frei "Wheel-Installation (pip scheitert, solange ein Prozess das .pyd haelt)"

echo ""
echo "== 1) Wheel installieren und Vertrag pruefen $(date +%F' '%H:%M:%S)"
python -X utf8 -m pip install --force-reinstall --no-deps "$WHEEL"
RC=$?; echo "   pip Exit $RC ($(date +%H:%M:%S))"
[ "$RC" = "0" ] || { echo "STOPP: Wheel-Installation gescheitert"; exit 10; }
python -X utf8 -u - <<'EOF'
import json, sys
import mosaic_rust
# engine_config_json: lib.rs:753; Felder input_size :768, contract_hash :770,
# num_actions :771 (in dieser Reihenfolge im json!-Literal).
cfg = json.loads(mosaic_rust.engine_config_json())
print(f"   engine input_size={cfg.get('input_size')}  num_actions={cfg.get('num_actions')}")
print(f"   num_planes_channels={cfg.get('num_planes_channels')}  "
      f"return_order_mode={cfg.get('return_order_mode', 'FEHLT')}")
print(f"   contract_hash={cfg.get('contract_hash')}  engine_version={cfg.get('engine_version')}")
import config
print(f"   config.INPUT_SIZE={config.INPUT_SIZE}  config.NUM_ACTIONS={config.NUM_ACTIONS}")
fehler = []
if str(cfg.get("input_size")) != "888":
    fehler.append(f"input_size {cfg.get('input_size')}, erwartet 888")
if "num_actions" not in cfg:
    fehler.append("engine_config_json hat kein Feld num_actions -- dann traegt allein der "
                  "contract_hash den Vertrag (siehe naechste Zeile)")
elif str(cfg["num_actions"]) != "414":
    fehler.append(f"num_actions {cfg['num_actions']}, erwartet 414")
# Zweite, unabhaengige Aufhaengung: der in lib.rs:2548-2553 festgeschriebene Hash fuer
# 888/414 (Gegenproben im selben Test: 884/406 -> cfd94509f0aab102).
if cfg.get("contract_hash") != "6ef829e564c58bd5":
    fehler.append(f"contract_hash {cfg.get('contract_hash')}, erwartet 6ef829e564c58bd5 "
                  "(Literal lib.rs:2548-2553)")
if "return_order_mode" not in cfg:
    fehler.append("engine_config_json hat kein Feld return_order_mode -- Wheel ohne R3?")
if int(config.INPUT_SIZE) != 888 or int(config.NUM_ACTIONS) != 414:
    fehler.append(f"config-Seite nicht scharf: {config.INPUT_SIZE}/{config.NUM_ACTIONS}")
if fehler:
    print("STOPP: Vertrag stimmt nicht -- " + "; ".join(fehler))
    sys.exit(12)
print("   Vertrag gruen: beide Seiten 888/414, Hash wie festgeschrieben.")
EOF
RC=$?; [ "$RC" = "0" ] || { echo "STOPP: Vertragspruefung Exit $RC"; exit "$RC"; }

echo ""
echo "== 2) Anker-Invarianz (Skill mosaic-anchor-invariance) $(date +%F' '%H:%M:%S)"
echo "   Leitersegment 2, Anker hv4_anchor (CLAUDE.md, Neuverankerung 2026-09-12)."
echo "   2a) DRIFT: spielt der heutige Code hv4 noch wie das Artefakt? (Kosten gemessen 22,2 s)"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir "$ANKER" \
  --out "$ART/anchor_v2_drift_live_wheel_20260918_v30wheel.json"
RC=$?; echo "   Drift Exit $RC ($(date +%H:%M:%S))"
[ "$RC" = "0" ] || { echo "STOPP: Anker-DRIFT ROT -- Nutzer-Entscheid (neues Leitersegment oder Aenderung zurueck), KEINE Reparatur"; exit 20; }
echo "   2b) KONSERVIERUNG: spielt das Artefakt noch wie am Einfriertag? (Kosten gemessen 13,4 s)"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir "$ANKER" --venv \
  --out "$ART/anchor_v2_conservation_20260918_v30wheel.json"
RC=$?; echo "   Konservierung Exit $RC ($(date +%H:%M:%S))"
[ "$RC" = "0" ] || { echo "STOPP: Anker-KONSERVIERUNG ROT -- Umgebungsdrift, Nutzer-Entscheid"; exit 21; }

echo ""
echo "== 3) Paritaetssonde Rust gegen Python $(date +%F' '%H:%M:%S)"
echo "   Erwartung: Flachvektor 888 Werte in BEIDEN Grundmengen gleich. STOPP nur beim"
echo "   LAENGENfehler (Zwischenstellung zwischen Wheel und config.INPUT_SIZE); Wertabweichungen"
echo "   werden berichtet, nicht bestraft (bekannter Kanal-76-Befund in der Grundmenge 'corpus')."
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
    sys.exit(30)
print("   Kein Laengenfehler.")
EOF
RC=$?; [ "$RC" = "0" ] || exit "$RC"

echo ""
echo "== 4) Generator-Artefakt v29-b10 herstellen (Polsterung, kein Training) $(date +%F' '%H:%M:%S)"
echo "   Policy-Kopf 406 -> 414 (acht Nullzeilen plus Bias), Flach-Eingang 884 -> 888"
echo "   (vier Nullspalten, R2/P.16). Export ueber export_onnx.export, also dieselbe Routine,"
echo "   die train.py fuer jedes _brierbest.onnx aufruft."
python -X utf8 -u tools/pad_policy_head_export.py --src "$SRC" --dst-name "$GEN"
RC=$?; echo "   Polsterung/Export Exit $RC ($(date +%H:%M:%S))"
[ "$RC" = "0" ] || { echo "STOPP: Polsterung oder Export gescheitert"; exit 40; }
[ -f "$B10" ] || { echo "STOPP: $B10 fehlt nach dem Export"; exit 41; }
ls -l "$B10" "${B10}.ref.txt" "models/alphazero_${GEN}.pth"

echo "   Kontrolle: laedt die ENGINE das ONNX, und wie breit ist ihr Policy-Ausgang?"
echo "   ERSATZ-MESSUNG (markiert): es gibt KEINEN pyo3-Export fuer net.rs::policy_width"
echo "   (geprueft: engine/src/py.rs und die wrap_pyfunction-Liste lib.rs:2344-2394 kennen"
echo "   keinen). Gemessen wird deshalb die LAENGE des policy-Vektors von mosaic_rust.onnx_eval"
echo "   (lib.rs:653-661: Net::load_auto plus net.eval) -- dasselbe Modell, dieselbe Ladepfad-"
echo "   Erkennung, und die Laenge IST die Policy-Breite, die die Suche sieht."
python -X utf8 -u - "$B10" <<'EOF'
import json, sys
import mosaic_rust as mr
pfad = sys.argv[1]
cfg = json.loads(mr.engine_config_json())
# Eingabe von onnx_eval ist die KONKATENATION Planes-Werte + Flachvektor
# (net.rs::split_planes_flat_batch_src, Zweig InputLayout::PlanesPlusFlat, net.rs:458-464); Geometrie
# 6x6 (features.rs:1674/1675), Kanalzahl und Flachbreite aus dem Vertrag.
n = int(cfg["num_planes_channels"]) * 6 * 6 + int(cfg["input_size"])
try:
    policy, value, moon, points = mr.onnx_eval(pfad, [0.0] * n)
except Exception as e:
    print(f"STOPP: Engine konnte {pfad} nicht auswerten: {e!r}")
    sys.exit(42)
print(f"   Engine hat geladen. Eingabelaenge {n}, policy_width={len(policy)}, "
      f"value {len(value)}, moon {len(moon)}, points {len(points)}")
if len(policy) != int(cfg["num_actions"]):
    print(f"STOPP: policy_width {len(policy)}, erwartet {cfg['num_actions']} -- der gepolsterte "
          "Kopf ist nicht im ONNX angekommen, oder das Tor der neuen Knoten faellt kanonisch "
          "zurueck (net.rs::policy_width/detect_policy_width).")
    sys.exit(43)
print("   policy_width 414: das Tor der neuen Suchknoten ist offen.")
EOF
RC=$?; [ "$RC" = "0" ] || { echo "STOPP: Engine-Kontrolle Exit $RC"; exit "$RC"; }

warte_frei "Kostentor"
echo ""
echo "== 5) Kostentor: was kosten die neuen Suchknoten? $(date +%F' '%H:%M:%S)"
echo "   Form: v29-b10 gegen sich selbst, $SPEC BEIDSEITS, 2 x 20 Paare = 80 Partien,"
echo "   10 Threads, --log-games. Gemessen wird allein die Wanduhr je Partie; die Siegquote"
echo "   ist hier bedeutungslos (zwei identische Spieler ergeben per Konstruktion 50 Prozent)."
echo "   Referenz $KOSTEN_REF s je Partie, Schwelle +$KOSTEN_SCHWELLE Prozent."
echo "   ANNAHME (ungeprueft): die Mondknoten (406-410) und die Rueckgabeknoten (411-413) sind"
echo "   ZUSAETZLICHE Suchen, ein spuerbarer Aufschlag ist also erwartet, nicht ueberraschend."
for S in 20261260 20261261; do
  OUT="$ART/v30_wheel_kosten_s${S}.json"
  echo ""
  echo "===== Kostenlauf Seed $S $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$B10" --spec-a "$SPEC" --model-b "$B10" --spec-b "$SPEC" \
    --name-a v30_kosten_a --name-b v30_kosten_b \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 20 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$S" --threads 10 --log-games --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
done
python -X utf8 -u - <<'EOF'
import json, sys
REF = 12.0          # docs/measured_runtimes.md Zeile 187, Tor 1 b07 Seed 20261191, exklusiv
SCHWELLE = 25.0
def sjp(p):
    return json.load(open(p, encoding="utf-8"))["laufzeit"]["s_je_partie"]
seeds = (20261260, 20261261)
neu = [sjp(f"evaluations/artifacts/v30_wheel_kosten_s{s}.json") for s in seeds]
mittel = sum(neu) / len(neu)
auf = (mittel / REF - 1.0) * 100.0
verdikt = "HAELT" if auf <= SCHWELLE else "GERISSEN"
print(f"KOSTENTOR v30-Wheel: neu {neu[0]:.3f} / {neu[1]:.3f} s je Partie, Mittel {mittel:.3f}")
print(f"   gegen Referenz {REF:.1f} s je Partie: Aufschlag {auf:+.1f} Prozent "
      f"(Schwelle +{SCHWELLE:.0f}) -> {verdikt}")
open("evaluations/artifacts/v30_wheel_kostentor_verdikt.txt", "w", encoding="utf-8").write(
    "prereg=PREREG_minimal_strength_core.md par.10.12\n"
    "form=v29-b10 gegen sich selbst, models/v30_generation.spec.json beidseits, "
    "2 x 20 Paare, 400 Sims, 10 Threads, --log-games, exklusiv\n"
    f"neu_s{seeds[0]}={neu[0]}\nneu_s{seeds[1]}={neu[1]}\nneu_mittel={mittel}\n"
    f"referenz_s_je_partie={REF}\n"
    "referenz_quelle=docs/measured_runtimes.md Zeile 187 (Tor 1 b07 gegen b03 auf dem "
    "884-Wheel, Seed 20261191, 200 Paare, 10 Threads, --log-games, exklusiv)\n"
    f"aufschlag_prozent={auf}\nschwelle_prozent={SCHWELLE}\nverdikt={verdikt}\n")
sys.exit(0 if verdikt == "HAELT" else 3)
EOF
RC=$?
if [ "$RC" != "0" ]; then
  echo "########## KOSTENTOR GERISSEN (Exit $RC) -- A/B und Wiedervorlage-Probe NICHT gestartet."
  echo "   Nutzer-Entscheid. Verdikt: $ART/v30_wheel_kostentor_verdikt.txt"
  exit 3
fi
echo "   Kostentor HAELT ($(date +%H:%M:%S))"

warte_frei "A/B gepolstert gegen ungepolstert"
echo ""
echo "== 6) A/B: gepolstert (v29-b10) gegen ungepolstert (v29-b07_brierbest) $(date +%F' '%H:%M:%S)"
echo "   A = $B10, B = $B07, Spec $SPEC BEIDSEITS, 400 Sims, 200 Paare, Blockgroesse 5,"
echo "   SPRT alpha=beta=0,001 (also kein praktischer Frueh-Stopp), Seed 20261270."
echo "   LESART: die acht Nullzeilen sind nach dem maskierten log_softmax gleichverteilte,"
echo "   nicht bevorzugte Masse -- fuer die 406 alten Aktionen ist b10 exakt b07. Erwartet ist"
echo "   deshalb Gleichstand. HAELT b10 die 5-Prozentpunkte-Marge (>= 45,0 Prozent Siege),"
echo "   ist er der Generator. REISST sie, STOPP und Nutzer-Entscheid -- dann traegt der"
echo "   gepolsterte Kopf etwas weg, was vorher nicht gemessen war."
AB="$ART/ab_v29-b10_vs_b07_s20261270.json"
python -X utf8 -u tools/paired_gating.py \
  --model-a "$B10" --spec-a "$SPEC" --model-b "$B07" --spec-b "$SPEC" \
  --name-a v29-b10 --name-b v29-b07 \
  --sims-a 400 --sims-b 400 --c-puct 1.5 \
  --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
  --seed 20261270 --threads 10 --log-games --no-promote-winner --out "$AB"
echo "   Exit $? ($(date +%H:%M:%S))"

echo ""
echo "== 6b) Standard-Kennzahlen: Spalten und Plattenpunkte je Kriterium $(date +%H:%M:%S)"
python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$AB"
python -X utf8 -u tools/plate_points_from_arena.py "$AB" --block 5 \
  --out "$ART/plate_points_ab_v29-b10_s20261270.json"

python -X utf8 -u - "$AB" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
a, b, n = d["a_wins_total"], d["b_wins_total"], d["n_games_total"]
quote = 100.0 * a / n if n else 0.0
print(f"   A/B v29-b10 gegen v29-b07: {a} : {b} von {n} Partien = {quote:.1f} Prozent "
      f"(Bloecke {len(d.get('blocks') or [])}, McNemar p {d.get('report_mcnemar_p')})")
print(f"   Punkte: A {d.get('avg_score_a')} gegen B {d.get('avg_score_b')}, "
      f"Strafleiste A {d.get('avg_floor_a')} gegen B {d.get('avg_floor_b')}")
print(f"   laufzeit: {json.dumps(d.get('laufzeit'), ensure_ascii=False)}")
if quote < 45.0:
    print(f"STOPP: Marge GERISSEN ({quote:.1f} Prozent < 45,0). Nutzer-Entscheid -- der gepolsterte")
    print("       Kopf ist als Generator nicht abgenommen; die Erzeugung bleibt ungestartet.")
    sys.exit(60)
print(f"   Marge HAELT ({quote:.1f} Prozent >= 45,0): v29-b10 ist der Generator.")
EOF
RC=$?; [ "$RC" = "0" ] || exit "$RC"

warte_frei "Wiedervorlage-Probe (Self-Play-Stichprobe)"
echo ""
echo "== 7) Wiedervorlage-Probe: kommen die neuen Knoten im RECORD an? $(date +%F' '%H:%M:%S)"
echo "   20 Partien mit dem Generator, sonst genau die Argumente der Sockel-Klasse aus"
echo "   tools/night_v30_generate.sh (Zeilen 76-79). MOSAIC_STACK_DRAW_RESEARCH=1 wird NUR"
echo "   hier gesetzt (wie in night_v30_generate.sh:32) -- die Arena-Stufen oben sollen mit"
echo "   der Referenz vergleichbar bleiben."
MOSAIC_STACK_DRAW_RESEARCH=1 python -X utf8 -u self_play.py --mode network --model "$B10" \
  --spec "$SPEC" --games 20 --sims 100 --version "${GEN}-probe" \
  --threads 11 --chunk 10 --per-file 10 --seed 20260929 \
  --tau-argmax-from-move 1 --deviate-prob 1.0 --start-slot-random-p 0.15
echo "   Self-Play Exit $? ($(date +%H:%M:%S))"
echo "   Dateien: $(ls data/ | grep -c "^selfplay_${GEN}-probe_")"

python -X utf8 -u - "$GEN" <<'EOF'
import glob, json, pickle, sys
from pathlib import Path
REPO = Path.cwd()
sys.path.insert(0, str(REPO / "engine" / "py"))
from neural_net import action_to_id, UnknownActionTypeError   # neural_net.py:976 / Waechter

gen = sys.argv[1]
files = sorted(glob.glob(f"data/selfplay_{gen}-probe_*.pkl"))
print(f"   {len(files)} Datei(en): {', '.join(files) or '(keine)'}")
if not files:
    print("STOPP (b): keine Probe-Datei -- das Self-Play hat nichts geschrieben.")
    sys.exit(70)

# Record-Felder (Pruefstellen): der Zustand steht unter "state", das Policy-Ziel
# unter "policy" als Liste von {"action": <Aktions-Dict>, "prob": ...}, die Maske
# unter "valid_actions" als Liste von Aktions-Dicts. Pruefstelle sind die Zeilen
# `m.insert("state"/"policy"/"valid_actions")` in engine/src/self_play.rs (per
# grep; die Datei wird gerade von einem anderen Strang editiert, ein Zeilenanker
# waere heute falsch). Es gibt KEIN Feld namens "policy_target" im Record -- was
# der Auftrag so nennt, ist dieses "policy"; "policy_target_valid" daneben ist
# ein Gueltigkeits-FLAG, nicht das Ziel.
# Die Aktions-ID entsteht erst in Python, aus dem Dict: action_to_id
# (neural_net.py:976; choose_moon_top -> 406-410 bei :1060, choose_return_first
# -> 411-413 bei :1066, Waechter-Ausnahme :972).
# P.16 `designs_ordered` steckt geschachtelt in dome_pool_view.blocks[*]
# (serialize.rs:119/167), deshalb wird es am JSON-Text des Zustands gesucht --
# dieselbe Bauform wie first_record_check in night_v30_generate.sh:68-70.
BEREICHE = [("mond 406-410", 406, 410), ("rueckgabe 411-413", 411, 413),
            ("slot/rotation kuppel 328-354", 328, 354),
            ("slot/rotation stapel 355-390", 355, 390),
            ("rotation 391-394", 391, 394),
            ("stapel-blick 405", 405, 405)]
zaehler = {name: 0 for name, _, _ in BEREICHE}
maske = {name: 0 for name, _, _ in BEREICHE}
records_total = 0
designs_ordered_hits = 0
neue_knoten_records = 0
neue_knoten_leer = 0
unbekannt = set()

def ids_of(entries):
    """IDs aus einer Liste von Policy-Eintraegen ODER von nackten Aktions-Dicts.

    "policy" traegt {"action": {...}, "prob": ...}, "valid_actions" traegt die
    Aktions-Dicts direkt -- beide Formen kommen hier durch dieselbe Schleife."""
    out = []
    for e in entries or []:
        if not isinstance(e, dict):
            continue
        act = e["action"] if isinstance(e.get("action"), dict) else e
        try:
            out.append(action_to_id(act))
        except UnknownActionTypeError as exc:
            unbekannt.add(str(exc)[:60])
    return out

for fp in files:
    with open(fp, "rb") as f:
        recs = pickle.load(f)
    for r in recs:
        records_total += 1
        if not isinstance(r, dict):
            continue
        if "designs_ordered" in json.dumps(r.get("state"), default=str):
            designs_ordered_hits += 1
        pol_ids = ids_of(r.get("policy"))
        val_ids = ids_of(r.get("valid_actions"))
        for name, lo, hi in BEREICHE:
            zaehler[name] += sum(1 for i in pol_ids if lo <= i <= hi)
            maske[name] += sum(1 for i in val_ids if lo <= i <= hi)
        if any(i >= 406 for i in val_ids):
            neue_knoten_records += 1
            if not r.get("policy"):
                neue_knoten_leer += 1

print(f"   Records insgesamt: {records_total}")
print(f"   (a) designs_ordered im Zustand: {designs_ordered_hits} Records")
print("   ID-Bereiche (Grundmenge Records dieser Probe, Einheit Vorkommen):")
for name, lo, hi in BEREICHE:
    print(f"       {name:32s} policy {zaehler[name]:6d}   valid_actions {maske[name]:6d}")
print(f"   Records mit einer ID >= 406 in valid_actions: {neue_knoten_records}, "
      f"davon mit LEEREM policy: {neue_knoten_leer}")
if unbekannt:
    print(f"   WARNUNG: unbekannte Aktionstypen gesehen: {sorted(unbekannt)}")

fehler = []
if designs_ordered_hits == 0:
    fehler.append("(a) designs_ordered fehlt in JEDEM Record -- R2/P.16 ist nicht im Record")
neu = zaehler["mond 406-410"] + zaehler["rueckgabe 411-413"] \
    + maske["mond 406-410"] + maske["rueckgabe 411-413"]
if neu == 0:
    fehler.append("(b) keine einzige Aktions-ID >= 406 -- Weg A / R3 erzeugt keine Knoten")
if fehler:
    print("STOPP: " + "; ".join(fehler))
    print("       Die Erzeugung waere nutzlos: das Merkmal fiele eine Generation zurueck")
    print("       (Regel feedback_record_field_must_precede_generation).")
    sys.exit(71)
if neue_knoten_leer:
    print(f"   (c) BEFUND, kein Stopp: {neue_knoten_leer} Records mit neuem Knoten haben ein leeres")
    print("       policy. Das ist zu klaeren (Rueckgabeknoten ohne Policy-Ziel -- Kommentar")
    print("       'kein policy_target am Rueckgabeknoten' in self_play.rs), stoppt die Abnahme")
    print("       aber nicht -- der Value-Anteil bleibt gueltig.")
else:
    print("   (c) kein Record mit neuem Knoten hat ein leeres policy.")
print("   Wiedervorlage-Probe GRUEN.")
EOF
RC=$?; [ "$RC" = "0" ] || { echo "STOPP: Wiedervorlage-Probe Exit $RC"; exit "$RC"; }

echo ""
echo "########## v30-WHEEL-ABNAHME FERTIG $(date +%F' '%H:%M:%S)"
echo "   Freigabe fuer 'MOSAIC_V30_GENERATOR=models/alphazero_v29-b10.onnx"
echo "   MOSAIC_V30_GEN_NAME=v29-b10 bash tools/night_v30_generate.sh' nach Generationswechsel"
echo "   (/mosaic-generation-turnover: Maschine frei, Einfrieren des Generators, daily-Snapshot"
echo "   mit restic-Beleg, STATUS-Neufassung)."
echo ""
echo "   Faellige Registrierungen:"
echo "   1. PREREG_minimal_strength_core.md par.10.12: Kostentor-Verdikt, A/B-Ergebnis auf"
echo "      BLOCK-Ebene, Wiedervorlage-Zaehlung je ID-Bereich; danach Zeile-1-Kopf nachziehen"
echo "      und python tools/generate_prereg_index.py laufen lassen."
echo "   2. PREREG_moon_stack_order.md par.12.6/12.10 (Weg A) und PREREG_dome_return_order.md"
echo "      par.12.7/12.8 (R2/R3): 'Kompilat abgenommen' plus die Zahl aus Stufe 4."
echo "   3. docs/measured_runtimes.md: Kostentor 2 x 20 Paare, A/B 200 Paare, Self-Play-Probe."
echo "   4. docs/generation_naming.md: v29-b10 ist belegt (Eintrag steht, Ergebnis nachtragen)."
echo "   5. evaluations/STATUS.md Abschnitt 6 Punkte 18-22: Generator-Entscheid erledigt,"
echo "      Anker-Kanten des neuen Wheels, offene Elo-Recheck-Frage (Anker-Aera)."
echo "   6. MOSAIC_DATA_EXCLUDE beim Bau des v30-Fensters um selfplay_v29-b10-probe_ erweitern."
