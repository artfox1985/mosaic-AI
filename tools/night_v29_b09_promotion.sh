#!/usr/bin/env bash
# Promotion v29-b09: die noch OFFENEN Punkte der Promotions-Checkliste
# (docs/promotion_checklist.md). Nutzer-Entscheid 2026-09-18, 10:05 ("Weiter mit a und b09",
# PREREG_minimal_strength_core.md 10.15 Punkt 1).
#
# WAS SCHON DURCH IST und deshalb hier FEHLT: die drei Elo-Kanten, Checkliste Punkte 2, 3, 4
# (Gating 423:377, Anker 128:22, Champion-2 90:60; gefahren mit tools/night_champion_edges_v29.sh,
# registriert in PREREG_minimal_strength_core.md 10.13 und evaluations/elo_history.csv).
#
# WAS DIESE KETTE ABARBEITET:
#   Stufe 0  Vorbedingungen und Warteschleife (Lastregel)
#   Stufe 1  Punkt 1  set_champion v29-b09_brierbest (+ Spec-Auffindbarkeit fuer server.py)
#   Stufe 2  Punkt 5b Platt-Fit, Anzeige (frozen_v3) und Trend (frozen_v1); DRUCKT nur
#   Stufe 3  Punkt 5c sigma/Prior-Balance (Gumbel-Skala), Schwelle 3
#   Stufe 4  Punkt 5d Netz-Paritaets-Fixture neu schreiben und frisch gegenpruefen
#   Stufe 5  Punkt 7  eingefrorenes Artefakt models/frozen_champions/v29-b09/
#   Stufe 6  Punkt 6 und 5 (Buchfuehrung): DRUCKT die faelligen Registrierungen fuer den Koordinator
#
# VORLAGE: tools/night_v28_freeze.sh und tools/night_v28_promotion.sh (Promotion v28-b02 am
# 2026-09-12, 03:48-06:45; die beiden Skripte sind im Aufraeumen 3688817b geloescht worden und
# wurden fuer diese Kette aus der Historie gelesen). Die Aufrufe von set_champion, cargo test,
# cp/venv/pip, build_frozen_golden_probe, frozen_referee_match, platt_fit und
# gumbel_scale_calibration sind von dort 1:1 uebernommen, nur mit neuem Namen.
#   EINE bewusste Abweichung: die Wheel-KOPIE im Artefakt traegt den KANONISCHEN Dateinamen
#   mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl (v28: mosaic_rust_knobs_20260912.whl), und die
#   venv wird AUS DIESER KOPIE installiert statt aus engine/target/wheels/. Grund: die Checkliste
#   (Punkt 7) nennt genau das als Bedingung ("pip lehnt umbenannte Wheel-Dateinamen ab: Kopie
#   unter kanonischem Namen installieren"), und engine/target/wheels/ wird beim naechsten Bau
#   ueberschrieben -- das Artefakt haengt dann an nichts mehr.
#
# CHAMPION-SPEC: models/frozen_champions/v29-b09/spec.json ist Feld fuer Feld die Spec des
# amtierenden Champions models/frozen_champions/v28-b02/spec.json. b09 IST mit ihr gemessen
# worden (Gating, Anker, Champion-2; tools/night_champion_edges_v29.sh:96 CHAMP_SPEC, Tor 1
# tools/night_v29_b09_v30_recipe.sh:89 SPEC). Sie wird kopiert, nicht neu geschrieben.
# Damit findet server.py sie auch: _resolve_champion_spec streift _brierbest ab und sucht
# models/frozen_champions/v29-b09/spec.json (server.py:257-266).
#
# NETZBREITE gegen WHEELBREITE, benannt statt verschwiegen: b09 ist 884 Eingaenge / 406 Aktionen
# (models/manifest_train_v29-b09_20260917_200920.json, engine_config.input_size / num_actions),
# das installierte Wheel vom 2026-09-18 09:30 ist 888/414 (config.py:49/57). Der Champion spielt
# darauf mit Rueckfall auf die kanonischen Pfade. Das Manifest traegt deshalb BEIDE Paare
# getrennt, und contract_hash ist der des LEBENDEN Wheels -- das ist der Wert, gegen den
# tools/frozen_referee_match.py:144-155 den Handshake fuehrt, und Artefakt-Wheel = Live-Wheel.
#
# LASTREGEL: Stufe 0 wartet auf freie CPU (gehaerteter Filter, Muster tools/night_k6_w025_ab.sh:27),
# danach laeuft alles streng seriell und exklusiv. Stufe 4 ist ein cargo-Bau und damit Volllast --
# das ist der Grund fuer die Warteschleife, nicht nur die Messungen. MOSAIC_CHAIN_NO_WAIT=1
# ueberspringt die Schleife (nur wenn ein Mensch die Reihenfolge selbst sicherstellt).
#
# KOSTEN (Planung; gemessene Zahlen aus docs/measured_runtimes.md, ANNAHMEN markiert):
#   Stufe 2  Platt v3 12 s + Platt v1 9 s          GEMESSEN (measured_runtimes.md:206, v28-b02)
#   Stufe 3  sigma/Prior 300 Zustaende @400 787 s  GEMESSEN (measured_runtimes.md:206, v28-b02)
#   Stufe 4  Fixture: zwei cargo-Laeufe --release  ANNAHME 10-25 min, davon der Grossteil Bauzeit;
#            in keiner Zeile der Kostentabelle eigens ausgewiesen
#   Stufe 5  venv 24 s / Golden Probe 1.450 s = 24 min / Referee-Selbsttest 2 Partien 78 s
#            GEMESSEN (measured_runtimes.md:211, Einfrieren v28-b02); die Golden Probe ist
#            einkernig @400. Die Checkliste nennt "rund 22 min".
#   SUMME    ANNAHME rund 50-70 min Wanduhr, exklusiv. Der 884er Eingang und das 888er Wheel
#            sind in keiner dieser gemessenen Zahlen enthalten; dass sie die Stufen nicht teurer
#            machen, ist ANNAHME.
#
# NICHTS WIRD REGISTRIERT UND NICHTS AN server.py GEAENDERT: die Kette druckt die Platt-Parameter
# und die einzutragenden _DISPLAY_CAL_A/_B-Zeilen, traegt sie aber NICHT ein, und sie schreibt
# keine Zeile nach STATUS.md, elo_history.csv oder in eine Prereg. Der Koordinator prueft die
# Zahlen nach (Regel 0: Werkzeugbefunde sind Behauptungen, bis die tragende Zahl nachgesehen ist).
#
# Aufruf: bash tools/night_v29_b09_promotion.sh   (Hintergrundaufgabe, KEINE Pipe, KEINE Umleitung)
# Registriert in evaluations/PREREG_minimal_strength_core.md 10.16 (geschrieben 2026-09-18).

set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

NEU=v29-b09
DIR=models/frozen_champions/$NEU
VORLAGE=models/frozen_champions/v28-b02
ART=evaluations/artifacts
MODELL_ONNX=models/alphazero_${NEU}_brierbest.onnx
MODELL_PTH=models/alphazero_${NEU}_brierbest.pth
TRAIN_MANIFEST=models/manifest_train_v29-b09_20260917_200920.json
WHEEL_SRC=engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl
WHEEL_NAME=mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl
EVAL_V3=evaluations/frozen_eval_set_v3.pkl
EVAL_V1=evaluations/frozen_eval_set.pkl

echo "########## PROMOTION $NEU $(date +%F' '%H:%M:%S)"

# ---------------------------------------------------------------- Stufe 0
echo ""
echo "===== 0) Vorbedingungen $(date +%F' '%H:%M:%S)"
RC0=0
for f in "$MODELL_ONNX" "$MODELL_PTH" "$TRAIN_MANIFEST" "$WHEEL_SRC" \
         "$VORLAGE/spec.json" "$VORLAGE/manifest.json" "$EVAL_V3" "$EVAL_V1" \
         tools/set_champion.py tools/platt_fit.py tools/gumbel_scale_calibration.py \
         tools/build_frozen_golden_probe.py tools/frozen_referee_match.py; do
  [ -f "$f" ] || { echo "   FEHLT: $f"; RC0=1; }
done
[ -d "$VORLAGE/venv/Lib/site-packages" ] || { echo "   FEHLT: $VORLAGE/venv (Vorlage-venv)"; RC0=1; }
[ -d "$DIR" ] && { echo "   STOPP: $DIR existiert schon -- ein gemessenes Artefakt wird NIE ueberschrieben"; RC0=1; }
[ $RC0 -eq 0 ] || { echo "ABBRUCH Stufe 0 (Exit 10)"; exit 10; }
echo "   alle Vorbedingungen da"
echo "   Vorlage-venv traegt (bestimmt, was Stufe 5 nachinstalliert):"
ls "$VORLAGE/venv/Lib/site-packages" | tr '\n' ' '; echo

cpu_frei() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { (\$_.CommandLine -match '[t]rain\.py|[p]aired_gating\.py|[f]rozen_referee_match\.py|[b]uild_cache|[c]ounterfactual_tiling|[o]ffline_diagnosis|[d]ead_unit_probe|[m]aturin|[w]indow_train_split|[a]rena_column_probe|[p]late_points_from_arena|[s]elf_play|[b]uild_frozen_golden_probe' -and \$_.Name -match 'python') -or \$_.Name -match '^(cargo|rustc)' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}
warte_frei() {
  if [ "${MOSAIC_CHAIN_NO_WAIT:-0}" = "1" ]; then
    echo "########## WARTESCHLEIFE UEBERSPRUNGEN (MOSAIC_CHAIN_NO_WAIT=1) $(date +%F' '%H:%M:%S)"
    return 0
  fi
  echo "########## PROMOTION WARTET ($1) $(date +%F' '%H:%M:%S)"
  while :; do
    cpu_frei && { echo "   Maschine frei ($(date +%H:%M:%S))"; break; }
    echo "   belegt ($(date +%H:%M:%S))"; sleep 120
  done
  sleep 20
}
warte_frei "Promotion v29-b09"

# ---------------------------------------------------------------- Stufe 1
echo ""
echo "===== 1) Checkliste Punkt 1: set_champion $(date +%F' '%H:%M:%S)"
python -X utf8 tools/set_champion.py ${NEU}_brierbest
RC=$?; echo "   Exit $RC"
[ $RC -eq 0 ] || { echo "STOPP: set_champion rot (Exit 11)"; exit 11; }
echo "   models/champion.txt = $(cat models/champion.txt)"
echo "   Spec-Auffindbarkeit fuer server.py (Checkliste Punkt 1, Vorfall v25-b01 bis v27-b01):"
echo "   models/${NEU}_brierbest.spec.json:      $([ -f models/${NEU}_brierbest.spec.json ] && echo da || echo 'fehlt (erwartet)')"
echo "   $DIR/spec.json: $([ -f $DIR/spec.json ] && echo da || echo 'fehlt -- legt Stufe 5 an')"
echo "   HINWEIS: zwischen Stufe 1 und Stufe 5 findet server.py KEINE Spec. Kein Server-Neustart"
echo "            in diesem Fenster; nach Stufe 5 die Konsolenzeile 'Champion-Spec ...' lesen."

# ---------------------------------------------------------------- Stufe 2
echo ""
echo "===== 2) Checkliste Punkt 5b: Platt-Fit (Anzeige-Kalibrierung) $(date +%F' '%H:%M:%S)"
echo "   VERTEILUNGS-CAVEAT (Checkliste 5b, Zusatz 2026-08-28): der ANZEIGE-Fit soll auf"
echo "   zeitgemaessen Zustaenden laufen, der Frozen-v1-Fit bleibt TRENDMETRIK."
echo "   tools/platt_fit.py kennt als Quelle nur --eval-set (tools/platt_fit.py:39). Vorhanden"
echo "   sind frozen_eval_set.pkl (v12-Aera), _v2, _v3 (b01-Aera, 1.800 Zustaende, 360 je Runde;"
echo "   PREREG_frozen_v3_eval_set.md:129). data/holdout/ gibt es NICHT (geprueft 2026-09-18)."
echo "   Es wird deshalb wie bei v28-b02 gefahren: v3 = Anzeige, v1 = Trend. Dass v3 fuer die"
echo "   v29-Aera 'zeitgemaess' ist, ist eine ANNAHME -- ein v29-Zustandssatz existiert nicht."
echo ""
echo "-- 2a) Anzeige-Fit auf frozen_v3 $(date +%H:%M:%S)"
python -X utf8 -u tools/platt_fit.py --models "$MODELL_PTH" \
  --eval-set "$EVAL_V3" --out "$ART/platt_fit_${NEU}_v3.json"
RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
[ $RC -eq 0 ] || { echo "STOPP: Platt-Fit v3 rot (Exit 12)"; exit 12; }
echo ""
echo "-- 2b) Trendmetrik auf frozen_v1 $(date +%H:%M:%S)"
python -X utf8 -u tools/platt_fit.py --models "$MODELL_PTH" \
  --eval-set "$EVAL_V1" --out "$ART/platt_fit_${NEU}.json"
RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
[ $RC -eq 0 ] || { echo "STOPP: Platt-Fit v1 rot (Exit 13)"; exit 13; }
echo ""
echo "-- 2c) A/B und die Zeilen fuer server.py (NUR GEDRUCKT, nichts eingetragen)"
python -X utf8 - "$ART/platt_fit_${NEU}_v3.json" "$ART/platt_fit_${NEU}.json" <<'PYCAL'
import json, sys, pathlib
def lade(p):
    d = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    m = d.get("models") or {}
    if not m:
        return None, d
    k = sorted(m)[0]
    return m[k], d
v3, roh3 = lade(sys.argv[1])
v1, roh1 = lade(sys.argv[2])
def zeig(name, e):
    if e is None:
        print(f"   {name}: keine models-Sektion im Artefakt -- von Hand nachsehen")
        return None
    print(f"   {name}: " + ", ".join(f"{k}={e[k]!r}" for k in sorted(e)))
    return e
e3 = zeig("frozen_v3 (ANZEIGE)", v3)
e1 = zeig("frozen_v1 (TREND)", v1)
if e3:
    A = e3.get("A"); B = e3.get("B")
    print("")
    print("   >>> In server.py eintragen (Checkliste 5b) -- TUT DIESE KETTE NICHT:")
    print(f"   _DISPLAY_CAL_A = {A}")
    print(f"   _DISPLAY_CAL_B = {B}")
    print("   Vergleichswerte v28-b02: A -0.0539 / B 0.6684 / Brier 0.22537 (frozen_v3),")
    print("   Trend frozen_v1 A 0.3840 / B 0.6074 / Brier 0.25217")
    print("   (models/frozen_champions/v28-b02/manifest.json, Feld display_calibration).")
    print("   Lesart: B~1 kalibriert, B>1 unterkonfident, B<1 ueberkonfident (platt_fit.py:11).")
PYCAL
echo "   Exit $?"

# ---------------------------------------------------------------- Stufe 3
echo ""
echo "===== 3) Checkliste Punkt 5c: sigma/Prior-Balance $(date +%F' '%H:%M:%S)"
echo "   ARGUMENTFORM GEPRUEFT: --model nimmt einen NAMEN, keinen Pfad -- das Werkzeug baut"
echo "   models/alphazero_<name>.onnx selbst (tools/gumbel_scale_calibration.py:85 und :98)."
echo "   Der Zustandssatz ist fest verdrahtet (FROZEN_PKL/ORACLE_JSON, Zeilen 65/66), es gibt"
echo "   kein --eval-set."
python -X utf8 -u tools/gumbel_scale_calibration.py --model ${NEU}_brierbest \
  --sims 400 --n-states 300 --out "$ART/gumbel_scale_calibration_${NEU}.json"
RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
[ $RC -eq 0 ] || { echo "STOPP: sigma/Prior rot (Exit 14)"; exit 14; }
python -X utf8 - "$ART/gumbel_scale_calibration_${NEU}.json" <<'PYGUM'
import json, sys, pathlib
d = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
def suche(obj, muster):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if muster in k.lower() and isinstance(v, (int, float)):
                return k, v
            t = suche(v, muster)
            if t:
                return t
    return None
t = suche(d, "ratio")
print("")
print("   KENNZAHL (Verhaeltnis sigma zu Prior, Median):", t[1] if t else "nicht gefunden -- Artefakt von Hand lesen")
print("   REGEL (Checkliste 5c, kein Ermessen): ueberschreitet die GESAMT-Kennzahl 3, oeffnet")
print("   sich die c_visit/c_scale-Familie wieder, und die H0-Befunde der Wurzel-Regler-Familie")
print("   verfallen (in anderem Balance-Regime gemessen).")
print("   Vergleich: v28-b02 2,222 / v27-b01 2,161 / v26-b01 2,270; je Runde bei v28-b02")
print("   1,30 / 2,48 / 3,04 / 3,76 (models/frozen_champions/v28-b02/manifest.json, gumbel_balance).")
if t and t[1] > 3:
    print("   >>> UEBER DER SCHWELLE: Koordinator-Entscheid faellig, nicht still weiterfahren.")
PYGUM
echo "   Exit $?"

# ---------------------------------------------------------------- Stufe 4
echo ""
echo "===== 4) Checkliste Punkt 5d: Netz-Paritaets-Fixture $(date +%F' '%H:%M:%S)"
echo "   Die Fixture folgt models/champion.txt (engine/src/self_play.rs:8848 ff.), also erst"
echo "   NACH Stufe 1. Der Test liegt in der lib (self_play.rs), deshalb --lib."
PYDIR="$(cygpath -u "$(python -c 'import sys,os;print(os.path.dirname(sys.executable))')")"
export PATH="$PYDIR:$PATH"   # sonst STATUS_DLL_NOT_FOUND (CLAUDE.md, Abschnitt pre-push-Hook)
echo "   PATH um $PYDIR ergaenzt"
( cd engine && MOSAIC_UPDATE_NET_PARITY_FIXTURE=1 cargo test --release --lib net_parity_hash_matches_champion_fixture -- --nocapture )
RC=$?; echo "   Schreiblauf Exit $RC ($(date +%H:%M:%S))"
[ $RC -eq 0 ] || { echo "STOPP: Fixture-Schreiblauf rot (Exit 15). Bei os error 32 unter OneDrive: Lauf wiederholen."; exit 15; }
( cd engine && cargo test --release --lib net_parity_hash_matches_champion_fixture -- --nocapture )
RC=$?; echo "   Pruefaufruf (frischer Prozess, ohne Variable) Exit $RC ($(date +%H:%M:%S))"
[ $RC -eq 0 ] || { echo "STOPP: Fixture-Gegenprobe rot (Exit 16)"; exit 16; }
head -c 400 engine/tests/fixtures/net_parity_champion.txt; echo
grep -E "^(champion|hash|erzeugt|engine)" engine/tests/fixtures/net_parity_champion.txt

# ---------------------------------------------------------------- Stufe 5
echo ""
echo "===== 5) Checkliste Punkt 7: eingefrorenes Artefakt $DIR $(date +%F' '%H:%M:%S)"
mkdir -p "$DIR"
cp "$MODELL_ONNX" "$DIR/model.onnx"
cp "$MODELL_PTH" "$DIR/model.pth"
cp "$VORLAGE/spec.json" "$DIR/spec.json"
cp "$WHEEL_SRC" "$DIR/$WHEEL_NAME"
RC=$?; [ $RC -eq 0 ] || { echo "STOPP: Kopieren rot (Exit 17)"; exit 17; }
echo "-- 5a) Spec Feld fuer Feld gegen die Vorlage $(date +%H:%M:%S)"
python -X utf8 - "$DIR/spec.json" "$VORLAGE/spec.json" <<'PYSPEC'
import json, sys, pathlib
a = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
b = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
if a == b:
    print("   IDENTISCH zu", sys.argv[2], f"({len(a)} Felder)")
    sys.exit(0)
print("   ABWEICHUNG:", {k: (a.get(k), b.get(k)) for k in set(a) | set(b) if a.get(k) != b.get(k)})
sys.exit(1)
PYSPEC
RC=$?; echo "   Exit $RC"
[ $RC -eq 0 ] || { echo "STOPP: Spec weicht von der Vorlage ab (Exit 18)"; exit 18; }
echo "-- 5b) Wheel-sha256 und Live-Beleg $(date +%H:%M:%S)"
( cd "$DIR" && sha256sum "$WHEEL_NAME" > wheel.sha256 && cat wheel.sha256 )
echo "   live installiertes Wheel (direct_url.json):"
python -X utf8 - <<'PYURL'
import json, pathlib
p = None
try:
    import importlib.metadata as m
    p = [f for f in m.files("mosaic_rust") if f.name == "direct_url.json"][0].locate()
except Exception as e:
    print("   importlib.metadata-Weg fehlgeschlagen:", e)
if p is None:
    try:
        import mosaic_rust, os, glob
        sp = pathlib.Path(os.path.dirname(mosaic_rust.__file__)).parent
        tr = glob.glob(str(sp / "mosaic_rust-*.dist-info" / "direct_url.json"))
        p = tr[0] if tr else None
    except Exception as e:
        print("   Fallback ueber mosaic_rust.__file__ fehlgeschlagen:", e)
if p is None:
    print("   KEIN direct_url.json gefunden -- Live-Beleg von Hand fuehren")
else:
    print("   ", p)
    print("   ", pathlib.Path(p).read_text(encoding="utf-8").strip())
PYURL
echo "   Exit $?"
echo "-- 5c) venv aus der Wheel-KOPIE (kanonischer Name) $(date +%H:%M:%S)"
python -m venv "$DIR/venv"
"$DIR/venv/Scripts/python.exe" -m pip install --no-deps "$DIR/$WHEEL_NAME"
# numpy und onnxruntime: die Vorlage-venv traegt beide (geprueft 2026-09-18 an
# models/frozen_champions/v28-b02/venv/Lib/site-packages), der Worker braucht sie fuer ONNX.
"$DIR/venv/Scripts/python.exe" -m pip install numpy onnxruntime
"$DIR/venv/Scripts/python.exe" -m pip list
"$DIR/venv/Scripts/python.exe" -c "import mosaic_rust; print('venv-Import ok')"
RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
[ $RC -eq 0 ] || { echo "STOPP: venv-Import rot (Exit 19)"; exit 19; }
echo "-- 5d) Vorab-Manifest (der Referee liest contract_hash, name_dialect und worker_python) $(date +%H:%M:%S)"
python -X utf8 - "$DIR" "$WHEEL_NAME" "$TRAIN_MANIFEST" <<'PYMAN'
import json, sys, pathlib, datetime
import mosaic_rust as mr
d = pathlib.Path(sys.argv[1]); wheel = sys.argv[2]; tmpath = sys.argv[3]
cur = json.loads(mr.engine_config_json())
sha = (d / "wheel.sha256").read_text(encoding="utf-8").split()[0]
tm = json.load(open(tmpath, encoding="utf-8"))
tec = tm.get("engine_config", {})
man = {
    "champion": "v29-b09",
    "freeze_date": datetime.date.today().isoformat(),
    "preliminary": "Vorab-Manifest aus tools/night_v29_b09_promotion.sh; Elo, Platt, sigma/Prior, "
                   "Golden-Probe- und Selbsttest-Felder traegt der Koordinator nach",
    "name_dialect": "hv",
    "model_file": "model.onnx", "pth_file": "model.pth", "spec_file": "spec.json",
    "model_source": "models/alphazero_v29-b09_brierbest.onnx (Training v29-b09 = v30-Rezept auf dem "
                    "v29-Fenster, %d Epochen, %.1f s, Warmstart %s; Trainings-Manifest %s)"
                    % (tm["cli_args"]["epochs"], tm["laufzeit"]["wanduhr_s"], tm["cli_args"]["load"], tmpath),
    "spec_source": "models/frozen_champions/v28-b02/spec.json -- UNVERAENDERT uebernommen "
                   "(Champion-Spec seit v24-b07; alle Kanten von v29-b09 liefen damit: Tor 1, "
                   "Gating, Anker, Champion-2)",
    "spec_content": json.loads((d / "spec.json").read_text(encoding="utf-8")),
    # Netzbreite (Modell) und Motorbreite (Wheel) sind hier VERSCHIEDEN -- getrennt fuehren.
    "input_size": tec.get("input_size"),
    "num_actions": tec.get("num_actions"),
    "model_contract_hash_at_training": tec.get("contract_hash"),
    "engine_input_size_live": cur.get("input_size"),
    "engine_num_actions_live": cur.get("num_actions"),
    "contract_hash": cur["contract_hash"],
    "engine_version": cur.get("engine_version", "0.1.0"),
    "breiten_note": "Modell 884/406, installiertes Wheel 888/414 (2026-09-18 09:30). Der Champion "
                    "spielt darauf mit Rueckfall auf die kanonischen Pfade; contract_hash ist der "
                    "des LEBENDEN Wheels, weil der Referee-Handshake gegen ihn prueft "
                    "(tools/frozen_referee_match.py:144-155) und Artefakt-Wheel = Live-Wheel ist.",
    "wheels": {"champion_behavior_artifact": {
        "file": wheel, "sha256": sha,
        "source": "engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl, gebaut "
                  "2026-09-18 09:30 (414 Aktionen / 888 Eingaenge; Abnahme Tore 1-4 gruen, "
                  "PREREG_minimal_strength_core.md 10.14). Kopie unter KANONISCHEM Dateinamen, "
                  "damit pip sie direkt installieren kann."}},
    "worker_python": {
        "interpreter_relative": "venv/Scripts/python.exe",
        "interpreter_note": "Relativ zu diesem Verzeichnis. Windows-venv, Python 3.14, angelegt "
                            "2026-09-18 per pip install --no-deps aus der Wheel-Kopie plus "
                            "numpy/onnxruntime"},
    "training_manifest": tmpath,
    "prereg": "evaluations/PREREG_minimal_strength_core.md 10.13/10.15/10.16; "
              "evaluations/PREREG_v29_window.md; docs/promotion_checklist.md",
}
(d / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
print("   Vorab-Manifest geschrieben. contract_hash live", cur["contract_hash"],
      "| Modell", man["input_size"], "/", man["num_actions"],
      "| Motor", man["engine_input_size_live"], "/", man["engine_num_actions_live"])
PYMAN
RC=$?; echo "   Exit $RC"
[ $RC -eq 0 ] || { echo "STOPP: Vorab-Manifest rot (Exit 20)"; exit 20; }
echo "-- 5e) Golden Probe (einkernig @400, gemessen 1.450 s bei v28-b02) $(date +%H:%M:%S)"
python -X utf8 -u tools/build_frozen_golden_probe.py --artifact-dir "$DIR" --seed-base 916001
RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
[ $RC -eq 0 ] || { echo "STOPP: Golden Probe rot (Exit 21)"; exit 21; }
echo "-- 5f) Referee-Selbsttest: Handshake, Golden 10/10, 2 Echtpartien $(date +%H:%M:%S)"
python -X utf8 -u tools/frozen_referee_match.py --artifact-dir "$DIR" \
  --model-a "$DIR/model.onnx" --spec-a "$DIR/spec.json" --n-games 2 \
  --out "$ART/referee_selftest_${NEU}.json"
RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"
[ $RC -eq 0 ] || { echo "STOPP: Referee-Selbsttest rot (Exit 22)"; exit 22; }
echo "   Artefakt-Inhalt:"
ls -la "$DIR"

# ---------------------------------------------------------------- Stufe 6
echo ""
echo "===== 6) Faellige Registrierungen (KOORDINATOR, nicht diese Kette) $(date +%F' '%H:%M:%S)"
cat <<'REG'
   1. server.py: _DISPLAY_CAL_A/_B aus Stufe 2c eintragen (Checkliste 5b). Ohne das zeigt die
      GUI die Gewinnwahrscheinlichkeit mit der Kurve des VORGAENGERS v28-b02.
   2. evaluations/STATUS.md: Champion-Zeile auf v29-b09 (Checkliste Punkt 6). Dabei pruefen,
      ob ein ANDERER Abschnitt dadurch falsch wird (CLAUDE.md, Pflege-Regel).
   3. archive/history.md: Kapitel zum Promotionstag (Checkliste Punkt 6).
   4. evaluations/PREREG_minimal_strength_core.md: Promotions-Absatz als Ergebnis zu 10.15
      Punkt 1, und im SELBEN Zug den Zeile-1-Statuskopf nachziehen, danach
      python tools/generate_prereg_index.py (CLAUDE.md, Prereg-Statuskopf und Index).
   5. models/frozen_champions/v29-b09/manifest.json vervollstaendigen: Feld "preliminary"
      entfernen und elo (Wert, CI, Kanten, Segment 2), display_calibration, gumbel_balance /
      sigma_prior_balance, golden_probe, parity_fixture (Hash aus Stufe 4), referee_selftest,
      live_wheel_check, acceptance, champion_note nachtragen -- Feldnamen 1:1 aus
      models/frozen_champions/v28-b02/manifest.json.
   6. docs/measured_runtimes.md: die gemessenen Dauern dieser Kette als Planungsgroesse.
   7. #29-Buchfuehrung (Checkliste Punkt 5): Offline-Kennzahlen des Siegers zur spaeteren
      Pruefung, ob Offline-Metriken die Arena vorhersagen. ACHTUNG, UNGEKLAERT: eine Datei
      dieses Namens gibt es im Baum NICHT (gegreppt ueber evaluations/ und docs/ am
      2026-09-18; Treffer nur als VERWEIS in docs/promotion_checklist.md:55,
      PREREG_lambda_wdl_arm.md:46, PREREG_t35b_ranking.md:26, PREREG_task_d_weights.md:106).
      Die Frage selbst ist Task #29 und liegt in evaluations/PREREG_value_rank_metric.md
      (Zeile 1: ENTSCHIEDEN, Rangmetrik NICHT validiert). ANNAHME: gemeint ist, die
      Offline-Kennzahlen je Arm dort oder in der Fenster-Prereg festzuhalten. Der Nutzer
      entscheidet, wohin -- stilles Weglassen waere ein Regelbruch.
REG
echo ""
echo "   Gegenprobe Spec-Auffindbarkeit nach Stufe 5:"
python -X utf8 - <<'PYSRV'
# Bildet server.py:257-266 nach: models/<name>.spec.json, sonst
# models/frozen_champions/<name ohne _brierbest/_best>/spec.json.
from pathlib import Path
name = Path("models/champion.txt").read_text(encoding="utf-8").strip()
direct = Path("models") / f"{name}.spec.json"
base = name
for suffix in ("_brierbest", "_best"):
    if base.endswith(suffix):
        base = base[: -len(suffix)]
frozen = Path("models") / "frozen_champions" / base / "spec.json"
treffer = direct if direct.exists() else (frozen if frozen.exists() else None)
print(f"   Champion {name} -> {treffer if treffer else 'KEINE SPEC GEFUNDEN (server.py meldet laut)'}")
PYSRV
echo ""
echo "########## PROMOTION $NEU FERTIG $(date +%F' '%H:%M:%S)"
