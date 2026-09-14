#!/usr/bin/env bash
# Fahrplan Nr. 5 (Rest) und Nr. 15 (Tore) in EINEM Wheel.
#
# Encoder-Abschnitt 16 (INPUT_SIZE 755 -> 794) und der Ablations-Schalter
# MOSAIC_SPECIAL_PLANES_OFF liegen beide im Baum; der Schalter ist per Default AUS
# (features.rs::special_planes_off), ein Wheel traegt also beide.
#
# KRITISCH: config.INPUT_SIZE wird im SELBEN Zug wie die Installation auf 794
# gesetzt. file_cache_key.py liest den Wert zur LAUFZEIT -- eine Konfiguration, die
# nicht zum installierten Wheel passt, legt Bloecke unter dem falschen Schluessel ab
# (Unfall vom 2026-09-11).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
PYDIR=$(python -c 'import sys,os;print(os.path.dirname(sys.executable))')
export PATH="$PYDIR:$PATH"
ART=evaluations/artifacts
DATUM=$(date +%Y%m%d)

echo "== 1) cargo test --release --no-run (Beispiele und Benchmarks) $(date +%H:%M:%S)"
cargo test --release --manifest-path engine/Cargo.toml --no-run || { echo "ABBRUCH: no-run rot"; exit 1; }

echo "== 2) Wheel bauen $(date +%H:%M:%S)"
( cd engine && python -m maturin build --release ) || { echo "ABBRUCH: maturin rot"; exit 1; }

WHL=$(ls -1t engine/target/wheels/mosaic_rust-*.whl 2>/dev/null | head -1)
if [ -z "$WHL" ]; then echo "ABBRUCH: kein Wheel gefunden"; exit 1; fi
echo "   Wheel: $WHL"

echo "== 3) Wheel installieren $(date +%H:%M:%S)"
python -m pip install --force-reinstall --no-deps "$WHL" || { echo "ABBRUCH: pip rot"; exit 1; }

echo "== 4) config.INPUT_SIZE auf 794 -- IM SELBEN ZUG $(date +%H:%M:%S)"
python -X utf8 - <<'PYEOF'
import io
p = "config.py"
s = io.open(p, encoding="utf-8").read()
old = "INPUT_SIZE = 755        # state_to_tensor"
new = "INPUT_SIZE = 794        # state_to_tensor"
if old not in s:
    if new in s:
        print("   schon auf 794")
        raise SystemExit(0)
    raise SystemExit("ABBRUCH: INPUT_SIZE-Zeile nicht gefunden")
io.open(p, "w", encoding="utf-8", newline="").write(s.replace(old, new))
print("   config.INPUT_SIZE = 794")
PYEOF
[ $? -eq 0 ] || exit 1

echo "== 5) Vertragshash und Breite gegenpruefen $(date +%H:%M:%S)"
python -X utf8 -c "
import mosaic_rust, json, sys
sys.path.insert(0, '.')
import config
cfg = json.loads(mosaic_rust.engine_config_json())
print('   Wheel-Kontrakt:', cfg.get('contract_hash'), '| Wheel input_size:', cfg.get('input_size'))
print('   config.INPUT_SIZE:', config.INPUT_SIZE)
assert cfg.get('input_size') == config.INPUT_SIZE, 'Wheel und config passen NICHT zusammen'
print('   -> Wheel und config stimmen ueberein')
" || { echo "ABBRUCH: Wheel/config-Abgleich rot"; exit 1; }

echo "== 6) Anker-Drift gegen hv4_anchor $(date +%H:%M:%S)"
python -X utf8 -u tools/verify_frozen_heuristic.py \
  --artifact-dir models/frozen_heuristics/hv4_anchor \
  --out "$ART/anchor_drift_live_wheel_${DATUM}_abschnitt16.json"
echo "   Drift Exit $? ($(date +%H:%M:%S))"

echo "== 7) Paritaet Rust gegen Python-Zwilling $(date +%H:%M:%S)"
python -X utf8 -u tools/probes/feature_parity_rust_python.py
echo "   Paritaet Exit $? ($(date +%H:%M:%S))"

echo "== 8) Konventionen und Knopf-Doku $(date +%H:%M:%S)"
python -X utf8 tools/generate_knob_docs.py
python -X utf8 tools/check_conventions.py

echo "== WHEEL 2 FERTIG $(date +%F' '%H:%M:%S)"
echo "   Naechster Schritt: Bloecke unter dem 794er-Schluessel, dann Training v29-b03;"
echo "   fuer b02 zusaetzlich MOSAIC_SPECIAL_PLANES_OFF=1 (eigener Schluessel)."
