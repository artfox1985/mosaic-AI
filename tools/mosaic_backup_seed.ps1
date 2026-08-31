<#
.SYNOPSIS
    Einmaliger Import des robocopy-Bestands in das restic-Repository.

.DESCRIPTION
    Uebernimmt die Sicherung vom 2026-07-24 (nicht-loeschender Spiegel plus
    datierte models-Zips), damit beim Umstieg keine Historie verloren geht.
    Danach genuegt tools/mosaic_backup.ps1.

    ZWEI QUELLEN, ZWEI BEHANDLUNGEN, IN DIESER REIHENFOLGE:

    1. <BackupRoot>\mirror -- der Basisstand.
       Ein Snapshot des Spiegels, mit derselben Ausschlussliste wie der
       Tageslauf. Der Spiegel enthaelt auch Dateien, die im Arbeitsbaum
       laengst geloescht sind -- genau dafuer lief er ohne /PURGE, und
       genau das soll erhalten bleiben.

    2. <BackupRoot>\models_snapshots\models_JJJJ-MM-TT.zip -- die Historie.
       Jedes Zip wird ENTPACKT und als eigener Snapshot mit dem Datum des
       Archivs eingespielt (--time). Das ist der Kern des sauberen Imports:
       ein Zip ist fuer content-defined chunking undurchdringlich. Zwei
       Archive, die sich in einer Datei unterscheiden, haben ab der ersten
       Abweichung durchgehend andere Bytes und dedupen zu praktisch null.
       Entpackt teilen sich die 14 Staende ihre unveraenderten Netze, und
       sie dedupen zusaetzlich gegen den Spiegel und die spaeteren
       Tageslaeufe.

       Gemessen am 2026-08-30: models/ ist 627 MB. Als Zips liegen dort
       rund 8 GB fast identischer Archive; entpackt sollte das Repo davon
       ungefaehr eine Kopie plus die Zuwaechse behalten. Das Skript druckt
       am Ende beide Groessen, damit die Ersparnis nicht behauptet, sondern
       abgelesen wird.

    WARUM DIESE REIHENFOLGE: fuer die Groesse des Repositories ist sie
    gleichgueltig, weil restic Bloecke ueber ihren Inhalt adressiert -- in
    jeder Reihenfolge entsteht dieselbe Menge. Sie entscheidet aber, was
    nach einem Abbruch schon gesichert ist. Der Spiegel ist der aktuelle
    Stand, die Zips sind Historie; das Wertvollere kommt zuerst. Schlaegt
    der Spiegel-Import fehl, bricht das Skript ab, statt mit der Historie
    weiterzumachen.

    DANACH kommt der Arbeitsbaum selbst, ueber tools/mosaic_backup.ps1.
    Wer ihn frueher will, kann diesen Import zweistufig fahren:
    zuerst -SkipZips (nur Spiegel), dann den Tageslauf, dann diesen Import
    erneut ohne Schalter -- schon eingespielte Zip-Staende werden an ihrem
    Datum erkannt und uebersprungen.

    PFADE IM SNAPSHOT: restic speichert den Pfad, aus dem gesichert wurde.
    Die Zip-Snapshots tragen darum den Arbeitsverzeichnis-Pfad, nicht den
    Projektpfad. Fuer die Deduplizierung ist das ohne Bedeutung -- restic
    adressiert Bloecke ueber ihren Inhalt, nicht ueber ihren Ort. Fuer die
    Wiederherstellung sucht man sie ueber ihre Marke:
        restic snapshots --tag models-snapshot

    DIESES SKRIPT LOESCHT NICHTS AN DER ALTEN SICHERUNG. Die Zips und der
    Spiegel bleiben unangetastet. Erst wenn der Import geprueft ist (das
    Skript nennt am Ende die Pruefbefehle), kann der Altbestand weg -- das
    ist eine Entscheidung, keine Aufraeumarbeit.

.PARAMETER WorkDir
    Arbeitsverzeichnis zum Entpacken. Braucht so viel freien Platz wie das
    groesste Zip (Richtwert 700 MB); der Inhalt wird nach jedem Archiv
    wieder geleert.

.PARAMETER SkipZips
    models-Zips nicht importieren.

.PARAMETER SkipMirror
    Spiegel nicht importieren.

.PARAMETER Force
    Erlaubt ein bereits vorhandenes, nicht leeres WorkDir. Ohne diesen
    Schalter bricht das Skript dort ab, statt fremden Inhalt zu leeren.

.PARAMETER DryRun
    Zeigt nur, was passieren wuerde. Entpackt nichts und schreibt nicht.

.NOTES
    Voraussetzungen und Umgebungsvariablen: siehe tools/backup_common.ps1.

    Der Lauf ist wiederholbar: bereits importierte Zip-Staende werden an
    ihrem Snapshot-Datum erkannt und uebersprungen. Bricht er in der Mitte
    ab, macht ein zweiter Aufruf dort weiter.

    ACHTUNG Projektregel "Messungen laufen EXKLUSIV": dieser Import liest
    und schreibt mehrere GB. Er gehoert nicht parallel zu einer Arena,
    einem Self-Play oder einer Sonde.
#>
[CmdletBinding()]
param(
    [string]$WorkDir,
    [switch]$SkipZips,
    [switch]$SkipMirror,
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$startedAt = Get-Date

. (Join-Path $PSScriptRoot "backup_common.ps1")
$ctx = Initialize-BackupContext -ToolsDir $PSScriptRoot -LogPrefix "backup_seed"

if (-not $ctx.BackupRoot) {
    throw "MOSAIC_BACKUP_DIR bzw. OneDrive nicht gesetzt -- der Altbestand ist nicht auffindbar."
}
if (-not $WorkDir) { $WorkDir = Join-Path $env:TEMP "mosaic_backup_seed" }

$zipDir = Join-Path $ctx.BackupRoot "models_snapshots"
$mirrorDir = Join-Path $ctx.BackupRoot "mirror"

Write-BackupLog $ctx "Import-Start. Altbestand=$($ctx.BackupRoot) Repo=$($ctx.RepoPath) Passwort=$($ctx.PasswordSource)"
Write-BackupLog $ctx "Arbeitsverzeichnis=$WorkDir DryRun=$DryRun"
Confirm-ResticRepo $ctx

# --- Arbeitsverzeichnis vorbereiten -----------------------------------------
# Absichtlich streng: das Skript leert nur ein Verzeichnis, das es selbst
# angelegt hat oder das ausdruecklich freigegeben wurde. Ein Skript, das
# stillschweigend fremde Ordner leert, ist in diesem Projekt genau die
# Bauform, die den Anlass fuer die ganze Sicherung gegeben hat.
if (Test-Path $WorkDir) {
    $existing = Get-ChildItem $WorkDir -Force -ErrorAction SilentlyContinue
    if ($existing -and -not $Force) {
        throw "WorkDir ist nicht leer: $WorkDir. Mit -Force zulassen oder einen anderen Pfad angeben."
    }
}

# --- Bereits importierte Zip-Staende ermitteln ------------------------------
$alreadyImported = @()
$snapOut = & $ctx.ResticExe snapshots --tag models-snapshot --json 2>$null
if ($LASTEXITCODE -eq 0 -and $snapOut) {
    try {
        # Wiedererkennung am DATEINAMEN, nicht am Datum. Am Datum war sie
        # falsch: am 2026-08-29 liegen vier Zips (Tages-Zip plus v22-b04,
        # -b05, -b06), die sich nur im Namen unterscheiden. Ein datumsbasierter
        # Abgleich haette drei davon fuer "schon da" gehalten.
        $snaps = ConvertFrom-Json ($snapOut -join "`n")
        foreach ($s in $snaps) {
            foreach ($t in $s.tags) {
                if ($t -like "zip:*") { $alreadyImported += $t.Substring(4) }
            }
        }
    } catch {
        Write-BackupLog $ctx "HINWEIS: vorhandene Snapshots nicht lesbar, importiere alle Zips."
    }
}
if ($alreadyImported.Count) {
    Write-BackupLog $ctx "Bereits importierte models-Staende: $($alreadyImported.Count)"
}

# --- 1. Spiegel: der Basisstand ---------------------------------------------
# Nutzer-Entscheid 2026-08-31: der Spiegel zuerst, dann die Historie.
#
# Fuer die GROESSE des Repositories ist die Reihenfolge gleichgueltig -- restic
# adressiert Bloecke ueber ihren Inhalt, es entsteht in jeder Reihenfolge
# dieselbe Menge. Sie entscheidet aber, was nach einem Abbruch schon drin ist,
# und da ist die Rangfolge eindeutig: der Spiegel ist der aktuelle Stand samt
# der Dateien, die im Arbeitsbaum geloescht wurden; die Zips sind Historie.
# Das Wertvollere zuerst.
$mirrorRc = $null
if (-not $SkipMirror) {
    if (-not (Test-Path $mirrorDir)) {
        Write-BackupLog $ctx "HINWEIS: $mirrorDir existiert nicht -- kein Spiegel zu importieren."
    } else {
        Write-BackupLog $ctx "Spiegel einspielen (Basisstand): $mirrorDir"
        $mirrorArgs = @(
            "backup", $mirrorDir,
            "--exclude-file", $ctx.ExcludeFile,
            "--tag", "mosaic-ai",
            "--tag", "legacy-mirror",
            "--verbose"
        )
        if ($DryRun) { $mirrorArgs += "--dry-run" }
        & $ctx.ResticExe @mirrorArgs
        $mirrorRc = $LASTEXITCODE
        if ($mirrorRc -eq 0 -or $mirrorRc -eq 3) {
            Write-BackupLog $ctx "Spiegel eingespielt (Exitcode $mirrorRc)."
        } else {
            Write-BackupLog $ctx "FEHLER: Spiegel-Import fehlgeschlagen (Exitcode $mirrorRc) -- Abbruch vor den Zips."
            throw "restic backup fehlgeschlagen fuer den Spiegel."
        }
    }
}

# --- 2. models-Zips: die Historie -------------------------------------------
$zipImported = 0
$zipSkipped = 0
if (-not $SkipZips) {
    if (-not (Test-Path $zipDir)) {
        Write-BackupLog $ctx "HINWEIS: $zipDir existiert nicht -- keine Zips zu importieren."
    } else {
        Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue

        # Aufsteigend nach Datum, damit die Snapshot-Liste chronologisch liest.
        $zips = Get-ChildItem $zipDir -Filter "models_*.zip" -File |
                Sort-Object Name
        Write-BackupLog $ctx "Gefundene models-Zips: $($zips.Count)"

        $index = 0
        foreach ($zip in $zips) {
            $index++
            # [regex]::Match statt "-notmatch" plus $Matches: die automatische
            # Variable wird bei -notmatch nicht verlaesslich aktualisiert, was
            # am 2026-08-31 zwei aufeinander folgende Dateien auf dasselbe
            # Datum abgebildet hat.
            $m = [regex]::Match($zip.Name, '(\d{4}-\d{2}-\d{2})')
            if (-not $m.Success) {
                Write-BackupLog $ctx "[$index/$($zips.Count)] UEBERSPRUNGEN (kein Datum im Namen): $($zip.Name)"
                $zipSkipped++
                continue
            }
            $stamp = $m.Groups[1].Value
            if ($alreadyImported -contains $zip.Name) {
                Write-BackupLog $ctx "[$index/$($zips.Count)] $($zip.Name) bereits im Repo -- uebersprungen."
                $zipSkipped++
                continue
            }

            $sizeMb = [math]::Round($zip.Length / 1MB, 1)
            Write-BackupLog $ctx "[$index/$($zips.Count)] $($zip.Name) ($sizeMb MB) entpacken..."
            if ($DryRun) {
                Write-BackupLog $ctx "[$index/$($zips.Count)] Trockenlauf: wuerde als Snapshot vom $stamp einspielen."
                $zipImported++
                continue
            }

            $target = Join-Path $WorkDir "models"
            if (Test-Path $target) { Remove-Item $target -Recurse -Force }
            New-Item -ItemType Directory -Force $target | Out-Null

            # ExtractToDirectory statt Expand-Archive: deutlich schneller bei
            # Archiven dieser Groesse und ohne die 2-GB-Grenze aelterer
            # Expand-Archive-Fassungen.
            [System.IO.Compression.ZipFile]::ExtractToDirectory($zip.FullName, $target)

            $backupArgs = @(
                "backup", $target,
                "--exclude-file", $ctx.ExcludeFile,
                # Zeitstempel aus der Datei, nicht "$stamp 12:00:00".
                # ANLASS 2026-08-31: die flache Mittagszeit hat die vier
                # beschrifteten Staende vom 2026-08-29 (v22-b04, -b05, -b06
                # plus Tages-Zip) auf EINEN Zeitpunkt abgebildet und damit
                # ununterscheidbar gemacht.
                "--time", $zip.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss"),
                "--tag", "mosaic-ai",
                "--tag", "models-snapshot",
                "--tag", "from-zip",
                # Der Dateiname ist die einzige Stelle, an der die Beschriftung
                # eines Standes steht ("_1322_v22-b05"). Ohne diese Marke ist
                # sie nach dem Loeschen der Zips unwiederbringlich.
                "--tag", ("zip:" + $zip.Name)
            )
            & $ctx.ResticExe @backupArgs
            $rc = $LASTEXITCODE
            if ($rc -eq 0 -or $rc -eq 3) {
                Write-BackupLog $ctx "[$index/$($zips.Count)] $stamp eingespielt (Exitcode $rc)."
                $zipImported++
            } else {
                Write-BackupLog $ctx "[$index/$($zips.Count)] FEHLER bei $stamp (Exitcode $rc) -- Abbruch."
                throw "restic backup fehlgeschlagen fuer $($zip.Name)."
            }

            Remove-Item $target -Recurse -Force
        }
    }
}

# --- Aufraeumen und Bilanz --------------------------------------------------
if (-not $DryRun -and (Test-Path $WorkDir)) {
    $leftover = Get-ChildItem $WorkDir -Force -ErrorAction SilentlyContinue
    if (-not $leftover) { Remove-Item $WorkDir -Force -ErrorAction SilentlyContinue }
}

Write-BackupLog $ctx "Zips eingespielt=$zipImported uebersprungen=$zipSkipped"

if (-not $DryRun) {
    # Die Ersparnis wird abgelesen, nicht behauptet: restore-size ist die
    # logische Summe aller Snapshots, raw-data das tatsaechlich belegte
    # Volumen nach Deduplizierung und Kompression.
    Write-BackupLog $ctx "--- Logische Groesse aller Snapshots (restore-size) ---"
    & $ctx.ResticExe stats --mode restore-size
    Write-BackupLog $ctx "--- Tatsaechlich belegt (raw-data, dedupliziert + komprimiert) ---"
    & $ctx.ResticExe stats --mode raw-data

    Write-BackupLog $ctx "Strukturpruefung..."
    & $ctx.ResticExe check
    if ($LASTEXITCODE -ne 0) { Write-BackupLog $ctx "WARNUNG: check Exitcode $LASTEXITCODE." }
}

$elapsed = (Get-Date) - $startedAt
Write-BackupLog $ctx ("Import fertig nach {0:N0}s." -f $elapsed.TotalSeconds)
Write-BackupLog $ctx "Pruefen mit:  restic snapshots"
Write-BackupLog $ctx "              restic snapshots --tag models-snapshot"
Write-BackupLog $ctx "              restic find --tag legacy-mirror <dateiname>"
Write-BackupLog $ctx "Der Altbestand (Zips, Spiegel) wurde NICHT angetastet."
exit 0
