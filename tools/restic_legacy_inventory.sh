#!/usr/bin/env bash
# Bestandsaufnahme des legacy-mirror-Stands im restic-Repo (Nutzer-Auftrag 2026-09-07:
# "wenn dann einzelne dateien daraus. der loewenanteil werden die self plays und die
# modelle sein"). REIN LESEND -- kein forget, kein rewrite, kein prune.
# Aufruf (Projektordner, Hintergrund, ohne Umleitung): bash tools/restic_legacy_inventory.sh
set -uo pipefail
cd "$(dirname "$0")/.."
SNAP=${1:-61579f2e}   # $2 = Tiefe der Verzeichnis-Buckets
export RESTIC_REPOSITORY="${MOSAIC_RESTIC_REPO:-${MOSAIC_BACKUP_DIR:-$OneDrive/Backups/mosaic-AI}}"
export RESTIC_PASSWORD_COMMAND="powershell -NoProfile -File '$(pwd -W 2>/dev/null || pwd)/tools/mosaic_backup_credential.ps1' -Get"
EXE="${MOSAIC_RESTIC_EXE:-}"
if [ -z "$EXE" ]; then
  EXE=$(find "$LOCALAPPDATA/Microsoft/WinGet" -name 'restic*.exe' -type f 2>/dev/null | sort | head -1)
fi
[ -n "$EXE" ] || { echo "STOPP: restic nicht gefunden."; exit 47; }
echo "== Bestandsaufnahme Snapshot $SNAP $(date +%H:%M:%S)"
echo "   Repo: $RESTIC_REPOSITORY"
echo "   restic: $EXE"
"$EXE" ls "$SNAP" --json | python -u tools/restic_snapshot_inventory.py "${2:-2}"
echo "== FERTIG $(date +%H:%M:%S)"
