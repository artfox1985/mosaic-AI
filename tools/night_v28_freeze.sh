#!/usr/bin/env bash
# Promotion v28-b02, schreibende und bauende Schritte NACH den Messungen
# (tools/night_v28_promotion.sh): docs/promotion_checklist.md Schritte 1, 5d und 7.
#   1  set_champion v28-b02_brierbest (Server findet die Spec ueber frozen_champions/v28-b02/spec.json)
#   5d Netz-Paritaets-Fixture neu erzeugen (cargo test, zweimal: schreiben, dann frisch pruefen)
#   7  Eingefrorenes Artefakt models/frozen_champions/v28-b02/: Modell, Spec (unveraendert die
#      Champion-Spec von v27-b01), das Wheel des Knopf-Durchgangs vom 2026-09-12 (alle neuen
#      Knoepfe auf Default, Anker-Drift gruen), venv aus dem Wheel plus numpy/onnxruntime,
#      Golden Probe (rund 22 min einkernig @400), Referee-Selbsttest mit 2 Echtpartien.
# Das manifest.json vervollstaendigt der Koordinator danach aus den Messwerten (Elo, Platt, sigma).
# Aufruf: bash tools/night_v28_freeze.sh   (Hintergrundaufgabe, keine Pipe, exklusiv)
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
NEU=v28-b02
DIR=models/frozen_champions/$NEU
WHEEL_SRC=engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl
WHEEL_NAME=mosaic_rust_knobs_20260912.whl
[ -d "$DIR" ] && { echo "STOPP: $DIR existiert schon"; exit 12; }

echo "== 1) set_champion $(date +%F' '%H:%M:%S)"
python -X utf8 tools/set_champion.py ${NEU}_brierbest
echo "   Exit $?; champion.txt = $(cat models/champion.txt)"

echo "== 5d) Netz-Paritaets-Fixture $(date +%F' '%H:%M:%S)"
PYDIR="$(cygpath -u "$(python -c 'import sys,os;print(os.path.dirname(sys.executable))')")"
export PATH="$PYDIR:$PATH"
( cd engine && MOSAIC_UPDATE_NET_PARITY_FIXTURE=1 cargo test --release net_parity_hash_matches_champion_fixture -- --nocapture )
echo "   Schreiblauf Exit $?"
( cd engine && cargo test --release net_parity_hash_matches_champion_fixture -- --nocapture )
RC=$?; echo "   Pruefaufruf Exit $RC ($(date +%H:%M:%S))"; [ $RC -eq 0 ] || { echo "STOPP: Fixture-Gegenprobe rot"; exit 25; }
head -c 400 engine/tests/fixtures/net_parity_champion.txt; echo

echo "== 7) Artefakt anlegen $(date +%F' '%H:%M:%S)"
mkdir -p "$DIR"
cp models/alphazero_${NEU}_brierbest.onnx "$DIR/model.onnx"
cp models/alphazero_${NEU}_brierbest.pth "$DIR/model.pth"
cp models/frozen_champions/v27-b01/spec.json "$DIR/spec.json"
cp "$WHEEL_SRC" "$DIR/$WHEEL_NAME"
( cd "$DIR" && sha256sum "$WHEEL_NAME" > wheel.sha256 && cat wheel.sha256 )
echo "   live installiert:"; cat "$(python -c 'import importlib.metadata as m;print([p for p in m.files("mosaic_rust") if p.name=="direct_url.json"][0].locate())')" 2>/dev/null; echo

echo "== 7) venv aus dem Wheel $(date +%F' '%H:%M:%S)"
python -m venv "$DIR/venv"
"$DIR/venv/Scripts/python.exe" -m pip install --no-deps "$WHEEL_SRC"
"$DIR/venv/Scripts/python.exe" -m pip install numpy onnxruntime
"$DIR/venv/Scripts/python.exe" -m pip list
"$DIR/venv/Scripts/python.exe" -c "import mosaic_rust; print('venv-Import ok')"
RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"; [ $RC -eq 0 ] || { echo "STOPP: venv-Import rot"; exit 26; }

echo "== 7) Vorab-Manifest (der Referee liest contract_hash und worker_python) $(date +%F' '%H:%M:%S)"
python -X utf8 - "$DIR" "$WHEEL_NAME" <<'PYMAN'
import json, sys, pathlib, datetime
import mosaic_rust as mr
d = pathlib.Path(sys.argv[1]); wheel = sys.argv[2]
cur = json.loads(mr.engine_config_json())
sha = (d / "wheel.sha256").read_text(encoding="utf-8").split()[0]
tm = json.load(open("models/manifest_train_v28-b02_20260911_152432.json", encoding="utf-8"))
man = {
    "champion": "v28-b02", "freeze_date": datetime.date.today().isoformat(),
    "preliminary": "Vorab-Manifest aus tools/night_v28_freeze.sh; Elo, Platt, sigma/Prior, Golden-Probe- und Selbsttest-Felder traegt der Koordinator nach",
    "name_dialect": "hv", "model_file": "model.onnx", "pth_file": "model.pth", "spec_file": "spec.json",
    "model_source": "models/alphazero_v28-b02_brierbest.onnx (Training v28-b02, Variante B mit 755 Merkmalen, 12 Epochen, %.1f s, Warmstart v27-b01_brierbest; Trainings-Manifest models/manifest_train_v28-b02_20260911_152432.json)" % tm["laufzeit"]["wanduhr_s"],
    "spec_source": "models/frozen_champions/v27-b01/spec.json -- UNVERAENDERT uebernommen (Champion-Spec seit v24-b07; alle Tore der v28-Generation liefen damit)",
    "spec_content": json.loads((d / "spec.json").read_text(encoding="utf-8")),
    "input_size": cur.get("input_size"), "contract_hash": cur["contract_hash"],
    "engine_version": cur.get("engine_version", "0.1.0"),
    "wheels": {"champion_behavior_artifact": {"file": wheel, "sha256": sha,
        "source": "engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl, gebaut 2026-09-12 (Knopf-Durchgang: round_estimate, Rueckgabe-Reihenfolge, Startslot, alle auf Default; Anker-Drift gegen hv1_anchor_v2 gruen, tools/night_v28_knob_build.sh)"}},
    "worker_python": {"interpreter_relative": "venv/Scripts/python.exe",
        "interpreter_note": "Relativ zu diesem Verzeichnis. Windows-venv, Python 3.14, angelegt 2026-09-12 per pip install --no-deps aus dem Wheel plus numpy/onnxruntime"},
    "training_manifest": "models/manifest_train_v28-b02_20260911_152432.json",
    "prereg": "evaluations/PREREG_v28_window.md; docs/promotion_checklist.md",
}
(d / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
print("Vorab-Manifest geschrieben, contract_hash", cur["contract_hash"])
PYMAN
echo "   Exit $?"

echo "== 7) Golden Probe $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/build_frozen_golden_probe.py --artifact-dir "$DIR" --seed-base 916001
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 7) Referee-Selbsttest, 2 Echtpartien $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/frozen_referee_match.py --artifact-dir "$DIR" \
  --model-a "$DIR/model.onnx" --spec-a "$DIR/spec.json" --n-games 2 \
  --out evaluations/artifacts/referee_selftest_${NEU}.json
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== FREEZE FERTIG $(date +%F' '%H:%M:%S) -- manifest.json vervollstaendigt der Koordinator."
