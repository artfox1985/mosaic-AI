#!/bin/sh
# tools/hooks/python_dll_path.sh -- EINE Herleitung des Verzeichnisses mit der
# python3*.dll, zum Einbinden per `.` (source) in Shell-Skripte, die `cargo`
# aufrufen.
#
#   . "$(git rev-parse --show-toplevel)/tools/hooks/python_dll_path.sh"
#   mosaic_prepend_python_dll_path || true   # gibt 1 zurueck, wenn nicht gefunden
#
# WARUM: ohne die Python-DLL im PATH bricht `cargo test --release` mit
# STATUS_DLL_NOT_FOUND (0xc0000135) ab -- das PyO3-Testbinary laedt sie beim
# Start. Dieselbe Herleitung stand am 2026-09-06 in SECHS Kopien im Baum
# (tools/hooks/pre-push, tools/cpu_queue_after_b02.sh, tools/k3f_build_window.sh,
# tools/run_longrow_teacher_arena.sh, tools/run_lr_init_arena.sh,
# tools/run_v2_teacher_arena.sh). Sie ist hier zusammengezogen, damit die
# naechste Korrektur nicht sechsmal nachgezogen werden muss.
#
# ZWEI Stolperfallen, die beide schon zugeschlagen haben und deshalb hier
# stehen bleiben muessen:
#
# 1. `sys.base_prefix`, NICHT `dirname(sys.executable)`: in einem venv liegt das
#    Interpreter-Exe in venv/Scripts/, die python*.dll aber in der Basis-
#    Installation.
# 2. `cygpath -u`: PATH ist hier ein :-getrennter POSIX-PATH. Ein Windows-Pfad
#    mit Laufwerksbuchstabe zerfaellt darin am Doppelpunkt in zwei unbrauchbare
#    Eintraege, die DLL wird NICHT gefunden, und cargo stirbt mit
#    STATUS_DLL_NOT_FOUND, obwohl das Verzeichnis korrekt ermittelt wurde
#    (aufgetreten am 2026-08-17 im Push). Ein bereits POSIX-formatierter Pfad
#    bleibt von cygpath -u unberuehrt.
#
# Kein absoluter Pfad und kein Nutzername im Skript (CLAUDE.md, Nutzer-Entscheid
# 2026-08-17: das Repo ist oeffentlich) -- erst MOSAIC_PYTHON_DIR, sonst aus dem
# gefundenen python selbst abgeleitet.

# Gibt das Verzeichnis auf stdout aus, oder nichts bei Exit != 0.
mosaic_python_dll_dir() {
    _mosaic_pydir="${MOSAIC_PYTHON_DIR:-}"
    if [ -z "$_mosaic_pydir" ] && command -v python >/dev/null 2>&1; then
        _mosaic_pydir="$(python -c 'import sys; print(sys.base_prefix)' 2>/dev/null)"
    fi
    [ -n "$_mosaic_pydir" ] || return 1
    if command -v cygpath >/dev/null 2>&1; then
        _mosaic_pydir="$(cygpath -u "$_mosaic_pydir" 2>/dev/null || printf '%s' "$_mosaic_pydir")"
    fi
    printf '%s' "$_mosaic_pydir"
}

# Stellt das Verzeichnis dem PATH voran. Exit 0 = DLL gefunden und PATH gesetzt;
# Exit 1 = nicht gefunden, mit Meldung auf stderr (der Aufrufer entscheidet, ob
# das ein Abbruch ist -- ein reiner Python-Lauf braucht die DLL nicht im PATH).
mosaic_prepend_python_dll_path() {
    _mosaic_dir="$(mosaic_python_dll_dir)"
    if [ -z "$_mosaic_dir" ]; then
        echo "python_dll_path: Python-Verzeichnis nicht ermittelbar." >&2
        echo "                 Bei STATUS_DLL_NOT_FOUND: MOSAIC_PYTHON_DIR setzen." >&2
        return 1
    fi
    if ls "$_mosaic_dir"/python3*.dll >/dev/null 2>&1; then
        export PATH="$_mosaic_dir:$PATH"
        return 0
    fi
    echo "python_dll_path: WARNUNG -- in '$_mosaic_dir' liegt keine python3*.dll." >&2
    echo "                 Bei STATUS_DLL_NOT_FOUND: MOSAIC_PYTHON_DIR auf das" >&2
    echo "                 Verzeichnis mit python3.dll/python3XX.dll setzen." >&2
    return 1
}
