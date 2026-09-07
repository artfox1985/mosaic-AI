#!/usr/bin/env bash
# TROCKENLAUF fuer das Entruempeln des legacy-mirror-Stands. REIN LESEND:
# kein forget, kein rewrite ohne --dry-run, kein prune.
# Nutzer-Freigabe 2026-09-07: "mach die dry runs, von mir aus koennen diese daten weg.
# die wichtigen dinge sind die modelle."
#
# Beantwortet zwei Fragen, die die nominalen GiB aus der Inventur NICHT beantworten:
#   1) Wie viel Platz haengt ueberhaupt allein an diesem Stand? (stats mit und ohne ihn)
#   2) Treffen die Ausschlussmuster das, was sie treffen sollen? (rewrite --dry-run)
set -uo pipefail
cd "$(dirname "$0")/.."
SNAP=${1:-61579f2e}
export RESTIC_REPOSITORY="${MOSAIC_RESTIC_REPO:-${MOSAIC_BACKUP_DIR:-$OneDrive/Backups/mosaic-AI}}"
export RESTIC_PASSWORD_COMMAND="powershell -NoProfile -File '$(pwd -W 2>/dev/null || pwd)/tools/mosaic_backup_credential.ps1' -Get"
EXE="${MOSAIC_RESTIC_EXE:-}"
[ -n "$EXE" ] || EXE=$(find "$LOCALAPPDATA/Microsoft/WinGet" -name 'restic*.exe' -type f 2>/dev/null | sort | head -1)
[ -n "$EXE" ] || { echo "STOPP: restic nicht gefunden."; exit 47; }

# MODELLE BLEIBEN (Nutzer 2026-09-07). Ebenso holdout (lebt im Baum, Referenzsatz von
# mindestens acht Sonden) und seed_corpus (die Seeding-Linie ist NICHT geschlossen).
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

echo "== 1) Repo-Gesamtgroesse, alle Staende $(date +%H:%M:%S)"
"$EXE" stats --mode raw-data
echo "== 2) Gesamtgroesse OHNE den Stand $SNAP $(date +%H:%M:%S)"
OTHERS=$("$EXE" snapshots --json | python -u -c "
import sys, json
snaps = json.load(sys.stdin)
print(' '.join(s['short_id'] for s in snaps if s['short_id'] != '$SNAP'))
")
# shellcheck disable=SC2086
"$EXE" stats --mode raw-data $OTHERS
echo "   Differenz der beiden Zahlen = was allein an $SNAP haengt."

echo "== 3) rewrite --dry-run mit den Ausschlussmustern $(date +%H:%M:%S)"
"$EXE" rewrite --dry-run "${EXCL[@]}" "$SNAP"
echo "== TROCKENLAUF FERTIG $(date +%H:%M:%S) -- nichts wurde veraendert."
