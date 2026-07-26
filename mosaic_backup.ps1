# Tägliche Sicherung des Mosaic-AI-Projektordners nach C:\Backups\mosaic-AI
# Eingerichtet 2026-07-24 (nach dem models/-Löschvorfall).
#
# Zwei Ebenen:
# 1. Spiegel (ohne Löschungen!): robocopy OHNE /PURGE bzw. /MIR — Dateien, die
#    auf D: gelöscht werden, bleiben im Backup erhalten. Genau deshalb hätte
#    ein klassischer /MIR-Spiegel beim models/-Vorfall NICHT geholfen.
# 2. Datierte models-Snapshots als Zip (14 Tage Vorhaltung) — die Gewichte
#    sind das einzige, was weder in Git noch regenerierbar ist.
#
# Ausgeschlossen (regenerierbar): engine\target (Rust-Build), __pycache__,
# logs, HDF5-Trainingscaches (.cache*.h5).

$ErrorActionPreference = "Continue"
$src  = "D:\Archiv\Documents\Projekte\mosaic-AI"
$dst  = "C:\Users\Patrick\OneDrive\Backups\mosaic-AI"
$date = Get-Date -Format "yyyy-MM-dd"

New-Item -ItemType Directory -Force "$dst\mirror"          | Out-Null
New-Item -ItemType Directory -Force "$dst\models_snapshots" | Out-Null
New-Item -ItemType Directory -Force "$dst\logs"             | Out-Null

# --- Ebene 1: Nicht-löschender Spiegel ---
robocopy $src "$dst\mirror" /E /XO /R:2 /W:5 `
    /XD "$src\engine\target" "__pycache__" "$src\logs" `
    /XF ".cache*.h5" `
    /NP /LOG:"$dst\logs\backup_$date.log"
$rc = $LASTEXITCODE   # robocopy: 0-7 = Erfolg, >=8 = Fehler

# --- Ebene 2: Datierter models-Snapshot ---
$modelFiles = Get-ChildItem "$src\models" -File -ErrorAction SilentlyContinue
if ($modelFiles) {
    $zip = "$dst\models_snapshots\models_$date.zip"
    if (-not (Test-Path $zip)) {
        Compress-Archive -Path "$src\models\*" -DestinationPath $zip -CompressionLevel Fastest
    }
    # Snapshots älter als 14 Tage entfernen
    Get-ChildItem "$dst\models_snapshots\models_*.zip" |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-14) } |
        Remove-Item -Force
} else {
    Add-Content "$dst\logs\backup_$date.log" "WARNUNG: models/ ist leer - kein Snapshot erzeugt."
}

Add-Content "$dst\logs\backup_$date.log" "Fertig: robocopy-Exitcode $rc, models-Snapshot: $(if ($modelFiles) {'ja'} else {'UEBERSPRUNGEN (leer)'})"
exit 0
