#!/usr/bin/env bash
# SCHARF: entfernt die Alt-Korpora aus dem legacy-mirror-Stand und gibt den Platz frei.
# Nutzer-Freigabe 2026-09-07: "raeum auf" -- erteilt NACH dem Trockenlauf und nach dem
# Einwand des Koordinators, dass nur rund 6,6 GiB zu holen sind
# (evaluations/cleanup_proposal_restic_legacy.md, Abschnitt "TROCKENLAUF GEMESSEN").
#
# ENDGUELTIG. Fuer alles, was hier herausfaellt, ist dieser Stand die einzige Kopie.
# BLEIBEN: mirror/models/ (Nutzer: "die wichtigen dinge sind die modelle"),
# mirror/data/holdout/ (Referenzsatz, lebt im Baum), mirror/data/seed_corpus/
# (Seeding-Linie ist NICHT geschlossen).
set -uo pipefail
cd "$(dirname "$0")/.."
SNAP=${1:-61579f2e}
export RESTIC_REPOSITORY="${MOSAIC_RESTIC_REPO:-${MOSAIC_BACKUP_DIR:-$OneDrive/Backups/mosaic-AI}}"
export RESTIC_PASSWORD_COMMAND="powershell -NoProfile -File '$(pwd -W 2>/dev/null || pwd)/tools/mosaic_backup_credential.ps1' -Get"
EXE="${MOSAIC_RESTIC_EXE:-}"
[ -n "$EXE" ] || EXE=$(find "$LOCALAPPDATA/Microsoft/WinGet" -name 'restic*.exe' -type f 2>/dev/null | sort | head -1)
[ -n "$EXE" ] || { echo "STOPP: restic nicht gefunden."; exit 47; }

EXCL=(
  --exclude "**/mirror/data/asym_corpus"
  --exclude "**/mirror/data/ownership_corpus"
  --exclude "**/mirror/data/corpus_probe"
  --exclude "**/mirror/data/archive_v18_ausserhalb_v21fenster_20260809"
  --exclude "**/mirror/data/selfplay_v18_*"
  --exclude "**/mirror/data/selfplay_v19wdl_*"
  --exclude "**/mirror/data/selfplay_v19wdlsw_*"
  --exclude "**/mirror/data/selfplay_v19wdlann_*"
  --exclude "**/mirror/data/selfplay_v20wdl_*"
  --exclude "**/mirror/data/selfplay_v20wdlsw_*"
)

echo "== 0) Stand VORHER $(date +%H:%M:%S)"
"$EXE" stats --mode raw-data
echo "== 1) rewrite --forget: Stand $SNAP ohne die Alt-Korpora $(date +%H:%M:%S)"
"$EXE" rewrite --forget "${EXCL[@]}" "$SNAP"; rc=$?
echo "   rewrite Exit $rc ($(date +%H:%M:%S))"
[ "$rc" = "0" ] || { echo "STOPP: rewrite fehlgeschlagen -- KEIN prune."; exit 48; }

echo "== 2) prune: nicht mehr referenzierte Bloecke freigeben $(date +%H:%M:%S)"
"$EXE" prune; rc=$?
echo "   prune Exit $rc ($(date +%H:%M:%S))"
[ "$rc" = "0" ] || { echo "STOPP: prune fehlgeschlagen -- danach check fahren!"; exit 49; }

echo "== 3) Stand NACHHER $(date +%H:%M:%S)"
"$EXE" stats --mode raw-data
echo "== 4) check: Integritaet nach dem Umschreiben der Pack-Dateien $(date +%H:%M:%S)"
"$EXE" check; rc=$?
echo "   check Exit $rc ($(date +%H:%M:%S))"
echo "== AUFRAEUMEN FERTIG $(date +%H:%M:%S)"
