#!/usr/bin/env bash
# Sammelstelle fuer die restic-Umgebung. Von tools/restic_*.sh gesourcet.
#
# Warum eine Sammelstelle und nicht drei Kopien: dieselbe Herleitung stand am
# 2026-09-07 in drei Skripten, und der pre-push-Waechter hat sie zu Recht
# dreimal angemeckert. Vorbild ist tools/hooks/python_dll_path.sh -- dieselbe
# Lehre wie bei der Python-DLL (tools/hooks/README.md).
#
# Reihenfolge der Quellen fuer das Repository, wie in tools/backup_common.ps1:
#   1. MOSAIC_RESTIC_REPO   -- voller Pfad, gewinnt immer
#   2. MOSAIC_BACKUP_DIR    -- Sicherungswurzel
#   3. $OneDrive plus MOSAIC_BACKUP_SUBDIR (Default unten)
#
# Das Repo ist oeffentlich (CLAUDE.md 2026-08-17): hier steht KEIN absoluter
# Pfad und kein Nutzername -- alles kommt aus der Umgebung.
: "${MOSAIC_BACKUP_SUBDIR:=Backups/mosaic-AI}"

mosaic_restic_env() {
  local root="${MOSAIC_BACKUP_DIR:-}"
  [ -n "$root" ] || root="${OneDrive:-}/${MOSAIC_BACKUP_SUBDIR}"
  export RESTIC_REPOSITORY="${MOSAIC_RESTIC_REPO:-$root}"
  export RESTIC_PASSWORD_COMMAND="powershell -NoProfile -File '$(git rev-parse --show-toplevel)/tools/mosaic_backup_credential.ps1' -Get"
}

# Findet restic auch dann, wenn winget den PATH-Eintrag nicht gesetzt hat
# (dieselbe Falle wie in tools/backup_common.ps1 beschrieben).
mosaic_restic_exe() {
  if [ -n "${MOSAIC_RESTIC_EXE:-}" ]; then printf '%s' "$MOSAIC_RESTIC_EXE"; return 0; fi
  command -v restic >/dev/null 2>&1 && { command -v restic; return 0; }
  find "${LOCALAPPDATA:-}/Microsoft/WinGet" -name 'restic*.exe' -type f 2>/dev/null | sort | head -1
}
