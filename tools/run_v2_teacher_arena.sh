#!/usr/bin/env bash
# PREREG_heuristic_v2_long_rows.md par.5.3, Messkette Schritt 3:
# Champion@400 gegen HEURISTIK V2@150, 407 Kampagnen-Seeds, mit Partie-Logs.
#
# Konfiguration gespiegelt von tools/run_longrow_teacher_arena.sh (dem
# v1-Lauf derselben Kette) und damit von paired_arena_env_imm_a02.json --
# dieselben Seeds, dieselben Sims. Nur so ist "v1 als Lehrer" gegen "v2 als
# Lehrer" direkt ablesbar.
#
# KEIN Brettwechsel noetig: run_net_vs_heuristic_v2_arena setzt das Netz immer
# auf Brett 0, der Startspieler alterniert ueber first = i % 2.
#
# NICHT starten, solange etwas anderes CPU zieht.
set -euo pipefail

cd "$(dirname "$0")/.."

# Python-Verzeichnis aus der Umgebung, sonst ableiten -- KEIN fester Pfad
# (oeffentliches Repo). Gleiche Ableitung wie tools/hooks/pre-push.
PYDIR="${MOSAIC_PYTHON_DIR:-}"
if [ -z "$PYDIR" ] && command -v python >/dev/null 2>&1; then
    PYDIR="$(python -c 'import sys; print(sys.base_prefix)' 2>/dev/null)"
fi
if [ -n "$PYDIR" ] && command -v cygpath >/dev/null 2>&1; then
    PYDIR="$(cygpath -u "$PYDIR" 2>/dev/null || printf '%s' "$PYDIR")"
fi
[ -n "$PYDIR" ] && export PATH="$PYDIR:$PATH"

exec python -u tools/probes/v2_teacher_arena.py "$@"
