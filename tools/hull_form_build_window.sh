#!/usr/bin/env bash
# Huellenform-Fenster (PREREG_geometric_envelope.md par.8.15, 2026-09-06): Teil A Sonde, dann
# cargo test, Spec-Nachzug, Wheel bauen -- OHNE Install. Aus tools/k3f_build_window.sh abgeleitet.
# Teil 2 (Install, Anker-Drift, Konservierung) faehrt der Koordinator, sobald kein server.py laeuft.
# Aufruf (Projektordner, Hintergrund, ohne Pipe, NUR bei freier CPU):  bash tools/hull_form_build_window.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
echo "== 0) Sonde gemessene Huelle (par.8.15 Teil A) $(date +%H:%M:%S)"
python -X utf8 -u tools/probes/measured_hull_probe.py --server-logs "static/log/game_*.log" \
  --artifact "$ART/paired_arena_env_v24b06_vs_b01_first_s14.json" "$ART/paired_arena_env_v24b06_vs_b01_second_s14.json" \
  "$ART/paired_arena_env_k3p2_b06_vs_k3p_first_s14.json" "$ART/paired_arena_env_k3p2_b06_vs_k3p_second_s14.json" \
  "$ART/paired_arena_env_k3f10_b06_vs_k3p_first_s14.json" "$ART/paired_arena_env_k3f10_b06_vs_k3p_second_s14.json" \
  --out "$ART/measured_hull_probe.json"; echo "   Sonde Exit $? ($(date +%H:%M:%S))"
echo "== 1) cargo test --release --lib (Huellenform + Fixture engine_test.onnx; Python-DLL im PATH) $(date +%H:%M:%S)"
. tools/hooks/python_dll_path.sh 2>/dev/null && mosaic_prepend_python_dll_path 2>/dev/null || {
  PYDIR="${MOSAIC_PYTHON_DIR:-}"; [ -z "$PYDIR" ] && PYDIR="$(python -c 'import sys; print(sys.base_prefix)' 2>/dev/null)"
  command -v cygpath >/dev/null 2>&1 && PYDIR="$(cygpath -u "$PYDIR" 2>/dev/null || printf '%s' "$PYDIR")"
  ls "$PYDIR"/python3*.dll >/dev/null 2>&1 && export PATH="$PYDIR:$PATH"; }
( cd engine && cargo test --release --lib ); rc=$?
echo "   cargo test Exit $rc ($(date +%H:%M:%S))"
[ "$rc" = "0" ] || { echo "STOPP: cargo test rot -- kein Spec-Nachzug, kein Wheel; Koordinator/Nutzer entscheidet."; exit 41; }
echo "== 2) Spec-Pflichtfeld envelope_hull_form=1 in die lebenden models/*.spec.json $(date +%H:%M:%S)"
python -X utf8 tools/spec_add_field.py envelope_hull_form 1; python -X utf8 tools/spec_add_field.py envelope_hull_form 1 --check || { echo "STOPP: Spec-Nachzug unvollstaendig"; exit 40; }
echo "== 3) Wheel bauen (nicht installieren) $(date +%H:%M:%S)"
( cd engine && python -m maturin build --release ); rc=$?
echo "   maturin Exit $rc ($(date +%H:%M:%S))"; ls -la --time-style=+%H:%M engine/target/wheels/ | tail -3
echo "== TEIL 1 FERTIG $(date +%H:%M:%S). Teil 2 (nur ohne laufenden server.py): pip install --force-reinstall --no-deps <wheel>; verify_frozen_heuristic.py Drift und --venv."
