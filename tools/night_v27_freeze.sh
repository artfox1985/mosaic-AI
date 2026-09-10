#!/usr/bin/env bash
# Promotion v27-b01, schreibende und bauende Schritte NACH den Messungen
# (tools/night_v27_promotion.sh): docs/promotion_checklist.md Schritte 1, 5d und 7.
# Nutzer-Auftrag 2026-09-10, 13:20: "Kannst dann autark weiterfahren mit dem v27 Programm."
#
#   1  set_champion v27-b01_brierbest
#   5d Netz-Paritaets-Fixture neu erzeugen (cargo test, zweimal: schreiben, dann frisch pruefen)
#   7  Eingefrorenes Artefakt models/frozen_champions/v27-b01/: Modell, Spec, Wheel (das am
#      2026-09-10 gebaute, Rueckgabe-Logzeile ohne IDs; sha256 c0aa6fdc...), venv aus dem
#      Wheel plus numpy/onnxruntime (Paketstand des v26-Artefakts), Golden Probe
#      (rund 17-22 min einkernig @400), Referee-Selbsttest mit 2 Echtpartien.
# Das manifest.json schreibt der Koordinator danach aus den Messwerten (Elo, Platt, sigma).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
NEU=v27-b01
DIR=models/frozen_champions/$NEU
WHEEL_SRC=engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl
WHEEL_NAME=mosaic_rust_stackreturn_20260910.whl

echo "== 1) set_champion $(date +%F' '%H:%M:%S)"
python -X utf8 tools/set_champion.py ${NEU}_brierbest
echo "   Exit $?; champion.txt = $(cat models/champion.txt)"

echo "== 5d) Netz-Paritaets-Fixture $(date +%F' '%H:%M:%S)"
# cygpath ist Pflicht: ein Windows-Pfad mit Doppelpunkt zerlegt PATH in der Git-Bash
# (Vorfall 2026-09-10, 14:52: Testbinary Exit 127, weil die Python-DLL nicht gefunden wurde).
PYDIR="$(cygpath -u "$(python -c 'import sys,os;print(os.path.dirname(sys.executable))')")"
export PATH="$PYDIR:$PATH"
( cd engine && MOSAIC_UPDATE_NET_PARITY_FIXTURE=1 cargo test --release net_parity_hash_matches_champion_fixture -- --nocapture )
echo "   Schreiblauf Exit $?"
( cd engine && cargo test --release net_parity_hash_matches_champion_fixture -- --nocapture )
echo "   Pruefaufruf Exit $? ($(date +%H:%M:%S))"
head -c 400 engine/tests/fixtures/net_parity_champion.txt; echo

echo "== 7) Artefakt anlegen $(date +%F' '%H:%M:%S)"
mkdir -p "$DIR"
cp models/alphazero_${NEU}_brierbest.onnx "$DIR/model.onnx"
cp models/alphazero_${NEU}_brierbest.pth "$DIR/model.pth"
cp models/v24-b07_brierbest.spec.json "$DIR/spec.json"
cp "$WHEEL_SRC" "$DIR/$WHEEL_NAME"
( cd "$DIR" && sha256sum "$WHEEL_NAME" > wheel.sha256 && cat wheel.sha256 )
echo "   live installiert:"; cat "$(python -c 'import importlib.metadata as m;print([p for p in m.files("mosaic_rust") if p.name=="direct_url.json"][0].locate())')" 2>/dev/null; echo

echo "== 7) venv aus dem Wheel $(date +%F' '%H:%M:%S)"
python -m venv "$DIR/venv"
"$DIR/venv/Scripts/python.exe" -m pip install --no-deps "$WHEEL_SRC"
"$DIR/venv/Scripts/python.exe" -m pip install numpy onnxruntime
"$DIR/venv/Scripts/python.exe" -m pip list
"$DIR/venv/Scripts/python.exe" -c "import mosaic_rust; print('venv-Import ok')"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 7) Vorab-Manifest (der Referee liest contract_hash und worker_python) $(date +%F' '%H:%M:%S)"
python -X utf8 - "$DIR" "$WHEEL_NAME" <<'PYMAN'
import json, sys, io, pathlib, datetime
import mosaic_rust as mr
d = pathlib.Path(sys.argv[1]); wheel = sys.argv[2]
cur = json.loads(mr.engine_config_json())
sha = (d / "wheel.sha256").read_text(encoding="utf-8").split()[0]
man = {
    "champion": "v27-b01", "freeze_date": datetime.date.today().isoformat(),
    "preliminary": "Vorab-Manifest aus tools/night_v27_freeze.sh; Elo, Platt, sigma/Prior, Golden-Probe- und Selbsttest-Felder traegt der Koordinator nach",
    "name_dialect": "hv", "model_file": "model.onnx", "pth_file": "model.pth", "spec_file": "spec.json",
    "model_source": "models/alphazero_v27-b01_brierbest.onnx (Training v27-b01, 12 Epochen, 5.116,7 s, Warmstart v26-b01_brierbest, brierbest Epoche 3)",
    "spec_source": "models/v24-b07_brierbest.spec.json -- UNVERAENDERT uebernommen (Einfrieren bis v27-b01, PREREG_v25_window.md par.18)",
    "spec_content": json.loads((d / "spec.json").read_text(encoding="utf-8")),
    "input_size": cur.get("input_size"), "contract_hash": cur["contract_hash"],
    "engine_version": cur.get("engine_version", mr.__version__ if hasattr(mr, "__version__") else "0.1.0"),
    "wheels": {"champion_behavior_artifact": {"file": wheel, "sha256": sha,
        "source": "engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl, gebaut 2026-09-10 (Rueckgabe-Logzeile ohne Kachel-IDs, Nutzer-Entscheid 2026-09-10; Anker-Drift gruen, 1.763 Schritte identisch). NICHT identisch mit dem Wheel der Artefakte v25-b01/v26-b01 (ea69b2e5...), Zugverhalten laut Anker-Drift unveraendert"}},
    "worker_python": {"interpreter_relative": "venv/Scripts/python.exe",
        "interpreter_note": "Relativ zu diesem Verzeichnis. Windows-venv, Python 3.14, angelegt 2026-09-10 per pip install --no-deps aus dem Wheel plus numpy/onnxruntime"},
    "prereg": "evaluations/PREREG_v27_window.md; docs/promotion_checklist.md",
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
echo "== FREEZE FERTIG $(date +%F' '%H:%M:%S) -- manifest.json schreibt der Koordinator."
