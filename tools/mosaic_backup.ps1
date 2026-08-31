<#
.SYNOPSIS
    Taegliche Sicherung des Mosaic-AI-Projektordners mit restic.

.DESCRIPTION
    Loest die robocopy-Fassung vom 2026-07-24 ab (eingerichtet nach dem
    models/-Loeschvorfall). Was sich aendert und warum:

    1. SNAPSHOTS STATT SPIEGEL. Der alte Spiegel lief bewusst ohne /PURGE --
       eine geloeschte Datei blieb im Backup erhalten. Diese Eigenschaft
       bleibt, aber sie kostet jetzt nichts mehr: jeder Snapshot haelt den
       Stand seines Tages fest, und gleiche Bloecke werden nur einmal
       gespeichert (content-defined chunking).

    2. KEIN ZIP MEHR. Der alte datierte models-Snapshot packte den vollen
       Baum (627 MB, gemessen 2026-08-30) jeden Tag neu; 14 Tage Vorhaltung
       ergaben rund 8 GB fast identischer Archive. Zip zerstoert
       Blockgrenzen, zwei Archive dedupen zu praktisch null. models/ liegt
       jetzt als normale Dateien im Repository -- ein neuer Tag kostet nur
       die neu hinzugekommenen Netze.

    3. AUSSCHLUSSLISTE REPARIERT. Siehe tools/backup_excludes.txt. Das alte
       Muster ".cache*.h5" liess 2.760 MB Trainingscache stehen, darunter
       zwei Dateien mit je 874 MB.

    Der Bestand der alten Sicherung (Spiegel plus datierte models-Zips) ist
    am 2026-08-31 einmalig uebernommen und geprueft worden; das Werkzeug
    dafuer ist danach entfallen, es steht in der Historie. Seitdem genuegt
    dieses Skript allein.

    LOESCHEN PASSIERT NUR AUF ANSAGE. `forget` und `prune` laufen
    ausschliesslich mit dem Schalter -Prune. Ohne ihn waechst das
    Repository, und das ist die richtige Vorgabe: Anlass der ganzen
    Einrichtung war ein Datenverlust, kein Platzmangel. Ein falsch gesetztes
    Aufbewahrungsfenster ist die einzige Stelle, an der dieses Skript den
    Vorfall vom 2026-07-24 wiederholen koennte.

.PARAMETER Prune
    Fuehrt nach der Sicherung `forget` mit der Aufbewahrungsrichtlinie aus
    und gibt Platz frei. LOESCHT alte Snapshots. Ohne den Schalter wird
    nichts entfernt.

.PARAMETER CheckData
    Prueft zusaetzlich die Nutzdaten (`check --read-data`) statt nur der
    Struktur. Liest das gesamte Repository, entsprechend langsam -- als
    gelegentliche Tiefenpruefung gedacht, nicht fuer den Tageslauf.

.PARAMETER NoVss
    Sichert ohne Volume Shadow Copy. Sonst nutzt das Skript VSS
    (--use-fs-snapshot), sofern es erhoeht laeuft: nur so lassen sich
    Dateien sichern, die ein laufendes Training oder ein Messlauf offen
    haelt.

.PARAMETER DryRun
    Zeigt, was gesichert wuerde, ohne zu schreiben. Zum Pruefen der
    Ausschlussliste nach einer Aenderung.

.NOTES
    Umgebungsvariablen und Voraussetzungen: siehe tools/backup_common.ps1.

    ACHTUNG Projektregel "Messungen laufen EXKLUSIV": dieser Lauf erzeugt
    I/O-Last ueber den ganzen Projektordner. Er gehoert nicht parallel zu
    einer Arena, einem Self-Play oder einer Sonde.
#>
[CmdletBinding()]
param(
    [switch]$Prune,
    [switch]$CheckData,
    [switch]$NoVss,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$startedAt = Get-Date

. (Join-Path $PSScriptRoot "backup_common.ps1")
$ctx = Initialize-BackupContext -ToolsDir $PSScriptRoot -LogPrefix "backup"

Write-BackupLog $ctx "Start. Quelle=$($ctx.SourceDir) Repo=$($ctx.RepoPath) restic=$($ctx.ResticExe) Passwort=$($ctx.PasswordSource)"
Confirm-ResticRepo $ctx

# --- Sicherung --------------------------------------------------------------
# VSS braucht erhoehte Rechte. Ohne sie scheitert restic an jeder Datei, die
# ein laufendes Training oder ein Messlauf offen haelt -- deshalb wird die
# Erhoehung geprueft und nicht blind angenommen.
$backupArgs = @(
    "backup", $ctx.SourceDir,
    "--exclude-file", $ctx.ExcludeFile,
    "--tag", "mosaic-ai",
    "--tag", "daily",
    "--verbose"
)
if ($DryRun) { $backupArgs += "--dry-run" }
if (-not $NoVss -and (Test-IsElevated)) {
    $backupArgs += "--use-fs-snapshot"
    Write-BackupLog $ctx "Volume Shadow Copy aktiv."
} elseif (-not $NoVss) {
    Write-BackupLog $ctx "HINWEIS: nicht erhoeht gestartet, sichere ohne VSS. Offene Dateien koennen fehlen."
}

# Bewusst OHNE Pipe und ohne Umleitung (Projektregel "Lange Laeufe NIE in eine
# Pipe"): der Fortschritt soll waehrend des Laufs sichtbar bleiben und der
# Exitcode der von restic sein. In die Logdatei geht nur die Zusammenfassung.
& $ctx.ResticExe @backupArgs
$backupRc = $LASTEXITCODE

# restic: 0 = alles gesichert, 3 = fertig, aber einzelne Dateien unlesbar.
if ($backupRc -eq 0) {
    Write-BackupLog $ctx "Sicherung erfolgreich."
} elseif ($backupRc -eq 3) {
    Write-BackupLog $ctx "WARNUNG: Sicherung abgeschlossen, einzelne Dateien waren unlesbar (Exitcode 3)."
} else {
    Write-BackupLog $ctx "FEHLER: Sicherung fehlgeschlagen (Exitcode $backupRc)."
}

# --- Aufbewahrung: nur auf ausdrueckliche Anforderung -----------------------
if ($Prune -and -not $DryRun -and ($backupRc -eq 0 -or $backupRc -eq 3)) {
    Write-BackupLog $ctx "forget/prune angefordert -- alte Snapshots werden ENTFERNT."
    $forgetArgs = @(
        "forget",
        "--tag", "mosaic-ai",
        "--keep-daily", "14",
        "--keep-weekly", "8",
        "--keep-monthly", "24",
        "--keep-yearly", "10",
        "--prune"
    )
    & $ctx.ResticExe @forgetArgs
    if ($LASTEXITCODE -ne 0) { Write-BackupLog $ctx "WARNUNG: forget/prune Exitcode $LASTEXITCODE." }
} elseif ($Prune -and $DryRun) {
    Write-BackupLog $ctx "forget/prune UEBERSPRUNGEN (Trockenlauf)."
} elseif ($Prune) {
    Write-BackupLog $ctx "forget/prune UEBERSPRUNGEN, weil die Sicherung fehlschlug."
} else {
    Write-BackupLog $ctx "Kein forget/prune (Vorgabe). Mit -Prune anfordern."
}

# --- Pruefung ---------------------------------------------------------------
$checkRc = 0
if (-not $DryRun) {
    $checkArgs = @("check")
    if ($CheckData) {
        $checkArgs += "--read-data"
        Write-BackupLog $ctx "Tiefenpruefung: lese das gesamte Repository."
    }
    & $ctx.ResticExe @checkArgs
    $checkRc = $LASTEXITCODE
    if ($checkRc -ne 0) { Write-BackupLog $ctx "WARNUNG: check Exitcode $checkRc -- Repository pruefen." }
}

# --- Abschluss --------------------------------------------------------------
$elapsed = (Get-Date) - $startedAt
if ($Prune) { $pruneLabel = "ja" } else { $pruneLabel = "nein" }
Write-BackupLog $ctx ("Fertig nach {0:N0}s. backup={1} check={2} prune={3}" -f $elapsed.TotalSeconds, $backupRc, $checkRc, $pruneLabel)

if ($backupRc -ne 0 -and $backupRc -ne 3) { exit $backupRc }
exit 0
