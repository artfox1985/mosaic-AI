<#
.SYNOPSIS
    Sichert models/ als benannten restic-Snapshot, direkt nach einem Training.

.DESCRIPTION
    Loest die Zip-Archive ab, die train.py bis zum 2026-08-31 nach
    <Sicherungswurzel>\models_snapshots\ geschrieben hat (ein Archiv des
    ganzen models/-Ordners je Trainingslauf, 0,3 bis 1,1 GB).

    WARUM DER ANLASS BLEIBT: der Tageslauf um 12:00 haelt den Stand EINES
    Zeitpunkts fest. Ein Training um 03:50 und ein zweites um 13:22 waeren
    darin nicht getrennt zu sehen -- was dazwischen entstand, ist mittags
    schon ueberschrieben. Der ereignisgesteuerte Snapshot ist also kein
    doppeltes Backup, sondern haelt einen Zustand fest, den der Tageslauf
    strukturell nicht sehen kann. Eingefuehrt nach dem Modellverlust am
    2026-07-24, und das Motiv gilt unveraendert.

    WARUM KEIN ZIP MEHR: ein Archiv ist fuer content-defined chunking
    undurchdringlich. Zwei Zips, die sich in einer Datei unterscheiden,
    haben ab der ersten Abweichung durchgehend andere Bytes und dedupen zu
    praktisch null -- jeder Lauf kostete den vollen Betrag. Als Snapshot
    kostet er nur die tatsaechlich neuen Netze. Gemessen am 2026-08-31 beim
    Import der Altbestaende: 115,4 GiB logisch in 9,7 GiB belegt.

    Die Beschriftung, die frueher im Dateinamen stand, wird zur Marke
    "run:<version>". Wiederfinden:

        restic snapshots --tag models-snapshot
        restic snapshots --tag "run:v22-b05"

.PARAMETER Version
    Name des Trainingslaufs, z.B. "v22-b05". Wird zur Marke "run:<name>".

.PARAMETER Path
    Zu sichernder Ordner. Vorgabe: models/ unterhalb des Projektordners.
    train.py reicht seinen eigenen MODELS_DIR durch, damit dort nicht zwei
    Vorstellungen davon existieren, wo die Modelle liegen.

.NOTES
    Voraussetzungen und Umgebungsvariablen: siehe tools/backup_common.ps1.
    Betrieb und Wiederherstellung: docs/backup_restore.md.

    Bewusst OHNE `check`: das ist Sache des Tageslaufs. Dieses Skript soll
    ein Training nicht laenger aufhalten als noetig.

    Der Aufrufer (train.py) behandelt jeden Fehlschlag als Warnung -- ein
    misslungener Snapshot darf ein fertiges Training nicht entwerten.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Version,
    [string]$Path
)

$ErrorActionPreference = "Stop"
$startedAt = Get-Date

. (Join-Path $PSScriptRoot "backup_common.ps1")
$ctx = Initialize-BackupContext -ToolsDir $PSScriptRoot -LogPrefix "models_snapshot"

if (-not $Path) { $Path = Join-Path $ctx.SourceDir "models" }
if (-not (Test-Path $Path)) {
    throw "Zu sichernder Ordner fehlt: $Path"
}

Write-BackupLog $ctx "Modell-Snapshot fuer '$Version'. Quelle=$Path Repo=$($ctx.RepoPath)"
Confirm-ResticRepo $ctx

$backupArgs = @(
    "backup", $Path,
    "--exclude-file", $ctx.ExcludeFile,
    "--tag", "mosaic-ai",
    "--tag", "models-snapshot",
    "--tag", "run:$Version"
)

& $ctx.ResticExe @backupArgs
$rc = $LASTEXITCODE

$elapsed = (Get-Date) - $startedAt
if ($rc -eq 0 -or $rc -eq 3) {
    Write-BackupLog $ctx ("Modell-Snapshot 'run:{0}' gesichert (Exitcode {1}) nach {2:N0}s." -f $Version, $rc, $elapsed.TotalSeconds)
    exit 0
}

Write-BackupLog $ctx ("FEHLER: Modell-Snapshot 'run:{0}' fehlgeschlagen (Exitcode {1}) nach {2:N0}s." -f $Version, $rc, $elapsed.TotalSeconds)
exit $rc
