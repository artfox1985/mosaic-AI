#!/usr/bin/env bash
# Bestandsaufnahme des legacy-mirror-Stands im restic-Repo (Nutzer-Auftrag 2026-09-07:
# "wenn dann einzelne dateien daraus. der loewenanteil werden die self plays und die
# modelle sein"). REIN LESEND -- kein forget, kein rewrite, kein prune.
# Aufruf (Projektordner, Hintergrund, ohne Umleitung): bash tools/restic_legacy_inventory.sh
set -uo pipefail
cd "$(dirname "$0")/.."
SNAP=${1:-61579f2e}   # $2 = Tiefe der Verzeichnis-Buckets
. "$(dirname "$0")/restic_env.sh"
mosaic_restic_env
EXE=$(mosaic_restic_exe)
[ -n "$EXE" ] || { echo "STOPP: restic nicht gefunden."; exit 47; }
echo "== Bestandsaufnahme Snapshot $SNAP $(date +%H:%M:%S)"
echo "   Repo: $RESTIC_REPOSITORY"
echo "   restic: $EXE"
"$EXE" ls "$SNAP" --json | python -u tools/restic_snapshot_inventory.py "${2:-2}"
echo "== FERTIG $(date +%H:%M:%S)"
