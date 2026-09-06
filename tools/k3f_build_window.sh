#!/usr/bin/env bash
# K3-F-Fenster, Teil 1 (2026-09-06): Spec-Nachzug, cargo test, Wheel bauen -- OHNE Install.
# Reihenfolge laut STATUS Abschnitt 1 Aufgabe 7: die lebenden Specs bekommen das Pflichtfeld
# envelope_flush_w erst, wenn kein Lauf mehr mit einem aelteren Wheel darauf zugreift; das neue
# Wheel wird erst installiert, wenn kein Basis-python es haelt (server.py, Trainings). Teil 2
# (Install, Anker-Drift, Konservierung) faehrt der Koordinator von Hand nach Freigabe.
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/k3f_build_window.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
echo "== 1) Spec-Pflichtfeld envelope_flush_w=0.0 in die lebenden models/*.spec.json $(date +%H:%M:%S)"
python -X utf8 tools/spec_add_field.py envelope_flush_w 0.0; python -X utf8 tools/spec_add_field.py envelope_flush_w 0.0 --check || { echo "STOPP: Spec-Nachzug unvollstaendig"; exit 40; }
echo "== 2) cargo test --release (K3-F, Python-DLL im PATH) $(date +%H:%M:%S)"
# Herleitung wie tools/hooks/pre-push und cpu_queue_after_b02.sh: base_prefix, dann cygpath -u --
# ein Windows-Pfad mit Backslashes im bash-PATH zerfaellt beim Spawn (STATUS_DLL_NOT_FOUND, 10:02).
PYDIR="${MOSAIC_PYTHON_DIR:-}"
[ -z "$PYDIR" ] && PYDIR="$(python -c 'import sys; print(sys.base_prefix)' 2>/dev/null)"
command -v cygpath >/dev/null 2>&1 && PYDIR="$(cygpath -u "$PYDIR" 2>/dev/null || printf '%s' "$PYDIR")"
if ls "$PYDIR"/python3*.dll >/dev/null 2>&1; then export PATH="$PYDIR:$PATH"; echo "   PATH-Prefix: $PYDIR"; else echo "   WARNUNG: keine python3*.dll unter '$PYDIR'"; fi
( cd engine && cargo test --release ); rc=$?
echo "   cargo test Exit $rc ($(date +%H:%M:%S))"
[ "$rc" = "0" ] || { echo "STOPP: cargo test rot -- kein Wheel; Nutzer entscheidet."; exit 41; }
echo "== 3) Wheel bauen (nicht installieren) $(date +%H:%M:%S)"
( cd engine && python -m maturin build --release ); rc=$?
echo "   maturin Exit $rc ($(date +%H:%M:%S))"; ls -la --time-style=+%H:%M engine/target/wheels/ | tail -3
echo "== TEIL 1 FERTIG $(date +%H:%M:%S). Teil 2 (nur ohne laufenden server.py): pip install --force-reinstall --no-deps <wheel>; verify_frozen_heuristic.py Drift und --venv."
