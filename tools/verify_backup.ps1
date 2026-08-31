<#
.SYNOPSIS
    Prueft die restic-Sicherung, BEVOR der Altbestand geloescht wird.

.DESCRIPTION
    Fuenf Stufen, aufsteigend nach Aussagekraft. Die Stufen 1 bis 3 laufen in
    Minuten; Stufe 4 stellt jeden models-Stand wieder her, Stufe 5 liest das
    gesamte Repository.

    STUFE 1 -- STRUKTUR. `restic check`: sind alle Snapshots, Baeume und
    Indizes in sich schluessig und vollstaendig referenziert?

    STUFE 2 -- ABDECKUNG. Ein erneutes `backup --dry-run` auf dieselbe
    Quelle. Meldet restic "0 new, 0 changed", deckt der vorhandene Snapshot
    die Quelle vollstaendig ab.

    Das ist der Kniff dieses Skripts: die Vollstaendigkeit wird NICHT mit
    einer nachgebauten Ausschlusslogik nachgerechnet. Eine zweite
    Implementierung von `backup_excludes.txt` waere selbst eine Fehlerquelle
    und wuerde frueher oder spaeter von restics Muster-Semantik abweichen.
    Stattdessen ist restic sein eigener Schiedsrichter -- es vergleicht mit
    genau der Logik, mit der es auch gesichert hat.

    STUFE 3 -- BYTE-GLEICHHEIT. Stichprobe: N Dateien aus dem Repository
    wiederherstellen und ihren SHA-256 gegen die Quelle stellen. Stufe 2
    vergleicht Groesse und Zeitstempel; erst hier wird der Datenpfad selbst
    geprueft.

    STUFE 4 -- ZIP-HISTORIE (`-Zips`). Der eine Teil, den Stufe 2 nicht
    pruefen kann: die models-Snapshots aus dem Import haben keine lebende
    Quelle mehr, ihr Arbeitsverzeichnis ist danach geloescht. Solange die
    Zips noch da sind, ist der Vergleich aber moeglich -- und genau die will
    man ja als erstes wegwerfen.

    Je Zip: den Snapshot mit demselben Datum wiederherstellen, jede
    wiederhergestellte Datei gegen den gleichnamigen Eintrag IM ZIP hashen
    (aus dem Archiv gestreamt, ohne es auszupacken), und danach auflisten,
    was im Zip steht und im Snapshot fehlt.

    Dieses Auflisten ist Absicht: das Skript entscheidet NICHT selbst,
    welche fehlende Datei legitim ausgeschlossen war -- dafuer muesste es
    `backup_excludes.txt` nachbauen, und eine zweite Implementierung waere
    selbst eine Fehlerquelle. Es sortiert nur vor (Pfade unterhalb eines
    `venv` sind der erwartete Fall) und legt alles Uebrige als Beanstandung
    vor.

    STUFE 5 -- TIEFENPRUEFUNG (`-Deep`). `check --read-data` liest jedes
    Pack-Byte und prueft die Hashes. Das ist die einzige Stufe, die einen
    stillen Datenfehler im Repository findet. Langsam, aber vor dem Loeschen
    des Altbestands einmal gerechtfertigt.

.PARAMETER Source
    Zu pruefende Quelle. "project" (Arbeitsbaum), "mirror" (Altbestand-
    Spiegel) oder "both". Vorgabe: both.

.PARAMETER SampleSize
    Anzahl Dateien fuer die Byte-Gleichheits-Stichprobe. 0 schaltet Stufe 3
    ab. Vorgabe: 12.

.PARAMETER Zips
    Stufe 4 mitlaufen lassen: die models-Zips gegen ihre Snapshots pruefen.
    Vor dem Loeschen von models_snapshots\ die entscheidende Stufe.

.PARAMETER ZipSample
    Wie viele Dateien je Zip gehasht werden. 0 = alle (gruendlich, aber es
    laeuft der gesamte Inhalt zweimal durch SHA-256). Vorgabe: 0.

.PARAMETER Deep
    Stufe 5 mitlaufen lassen (`check --read-data`).

.PARAMETER WorkDir
    Arbeitsverzeichnis fuer Wiederherstellungen. Jeder Lauf legt darin ein
    eigenes `run_<zeitstempel>` an und raeumt am Ende NUR dieses wieder weg;
    vorhandene Reste werden gemeldet, nicht angefasst.

.NOTES
    Voraussetzungen und Umgebungsvariablen: siehe tools/backup_common.ps1.
    Wiederherstellungswissen und Betriebsregeln: docs/backup_restore.md.

    ACHTUNG Projektregel "Messungen laufen EXKLUSIV": die Stufen 2 bis 4
    lesen mehrere GB. Nicht parallel zu einer Arena, einem Self-Play oder
    einer Sonde.

    Dieses Skript LOESCHT NICHTS -- weder am Repository noch am Altbestand.
    Es sagt nur, ob geloescht werden DARF.
#>
[CmdletBinding()]
param(
    [ValidateSet("project", "mirror", "both")][string]$Source = "both",
    [int]$SampleSize = 12,
    [switch]$Zips,
    [int]$ZipSample = 0,
    [switch]$Deep,
    [string]$WorkDir
)

$ErrorActionPreference = "Stop"
$startedAt = Get-Date

. (Join-Path $PSScriptRoot "backup_common.ps1")
$ctx = Initialize-BackupContext -ToolsDir $PSScriptRoot -LogPrefix "backup_verify"
if (-not $WorkDir) { $WorkDir = Join-Path $env:TEMP "mosaic_backup_verify" }

# Jeder Lauf bekommt sein EIGENES Unterverzeichnis. Grund: die erste Fassung
# brach ab, wenn $WorkDir Reste enthielt -- ausgerechnet ein Verzeichnis, das
# das Skript selbst anlegt und am Ende selbst wieder loescht. Streng sein ist
# bei einem fremden Ordner richtig, beim eigenen macht es das Werkzeug nur
# kaputt. Geloescht wird am Ende ausschliesslich $runDir; fremde Reste in
# $WorkDir werden gemeldet, nicht angefasst.
$runDir = Join-Path $WorkDir ("run_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
if (Test-Path $WorkDir) {
    $leftovers = @(Get-ChildItem $WorkDir -Force -ErrorAction SilentlyContinue)
    if ($leftovers.Count) {
        Write-Warning "In $WorkDir liegen $($leftovers.Count) Rest(e) aus frueheren Laeufen. Sie werden NICHT angefasst; dieser Lauf arbeitet in $runDir. Bei Bedarf selbst aufraeumen."
    }
}

$failures = New-Object System.Collections.Generic.List[string]
function Add-Failure { param([string]$Text) $failures.Add($Text); Write-BackupLog $ctx "FEHLER: $Text" }

function Unlock-RestoredTree {
    <#
    .SYNOPSIS
        Macht einen frisch wiederhergestellten Baum lesbar.
    .DESCRIPTION
        restic schreibt beim Restore die Rechte der QUELLE mit. Beim Nachbauen
        des Pfades entsteht dabei ein Ordner "C\Users", der die restriktive
        ACL des echten C:\Users erbt -- und dann scheitert schon das
        REKURSIVE AUFLISTEN daran.

        Am 2026-08-31 hat genau das alle zwoelf Zip-Pruefungen als "hat KEINE
        Datei geliefert" ausgewiesen, obwohl restic zuvor rund 970 MiB je
        Durchgang zurueckgeschrieben hatte. Mit -ErrorAction SilentlyContinue
        verschluckt Get-ChildItem den Zugriffsfehler und gibt eine leere
        Liste zurueck -- ununterscheidbar von "nichts da".

        Wirkt nur auf Verzeichnisse, die dieser Lauf selbst angelegt hat.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path $Path)) { return }
    & icacls $Path /reset /T /C /Q *> $null
}

function Remove-RestoredTree {
    <#
    .SYNOPSIS
        Loescht einen Restore-Baum, auch wenn seine Rechte das verhindern.
    .DESCRIPTION
        restic schreibt beim Restore die Rechte der QUELLE mit. Legt es dabei
        einen Ordner wie "C\Users" nach, erbt der dessen restriktive ACL --
        und dann scheitert nicht nur das Setzen des Zeitstempels, sondern
        auch das spaetere Aufraeumen mit "Zugriff verweigert" (am 2026-08-31
        aufgetreten, 969 MB je Durchgang).

        Darum: erst normal versuchen, dann die Rechte zuruecksetzen und
        erneut versuchen. Gelingt es dann immer noch nicht, wird der Pfad
        GENANNT statt still stehen gelassen -- sonst laeuft die Platte voll,
        ohne dass jemand weiss, warum.

        Wirkt ausschliesslich auf Verzeichnisse, die dieser Lauf selbst
        angelegt hat.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path $Path)) { return $true }
    Remove-Item $Path -Recurse -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path $Path)) { return $true }

    & icacls $Path /reset /T /C /Q *> $null
    Remove-Item $Path -Recurse -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path $Path)) { return $true }

    Write-Warning "Konnte $Path nicht raeumen (Rechte). Bitte von Hand entfernen -- die Restore-Baeume sind je rund 1 GB gross."
    return $false
}

Write-BackupLog $ctx "Pruefung startet. Repo=$($ctx.RepoPath) Quelle=$Source Stichprobe=$SampleSize Tief=$Deep"

# --- Welche Quellen, welche Marken -------------------------------------------
$targets = @()
if ($Source -in @("project", "both")) {
    $targets += [pscustomobject]@{ Name = "Arbeitsbaum"; Path = $ctx.SourceDir; Tag = "daily" }
}
if ($Source -in @("mirror", "both")) {
    $mirrorDir = Join-Path $ctx.BackupRoot "mirror"
    if (Test-Path $mirrorDir) {
        $targets += [pscustomobject]@{ Name = "Spiegel"; Path = $mirrorDir; Tag = "legacy-mirror" }
    } else {
        Write-BackupLog $ctx "HINWEIS: kein Spiegel unter $mirrorDir -- Stufe 2 dafuer entfaellt."
    }
}

# --- Stufe 1: Struktur -------------------------------------------------------
Write-BackupLog $ctx "--- Stufe 1: Struktur (check) ---"
$check = Invoke-ResticCapture -Exe $ctx.ResticExe -Arguments @("check")
if ($check.ExitCode -ne 0) {
    Add-Failure "check meldet Exitcode $($check.ExitCode): $($check.Output)"
} else {
    Write-BackupLog $ctx "Struktur in Ordnung."
}

$snapOut = Invoke-ResticCapture -Exe $ctx.ResticExe -Arguments @("snapshots", "--json")
$allSnaps = @()
if ($snapOut.ExitCode -eq 0) {
    try { $allSnaps = ConvertFrom-Json $snapOut.Output } catch { Add-Failure "Snapshot-Liste nicht lesbar." }
}
Write-BackupLog $ctx "Snapshots im Repository: $($allSnaps.Count)"
foreach ($tag in @("daily", "legacy-mirror", "models-snapshot")) {
    $n = @($allSnaps | Where-Object { $_.tags -contains $tag }).Count
    Write-BackupLog $ctx "  Marke $tag : $n"
}

# --- Stufe 2: Abdeckung ------------------------------------------------------
Write-BackupLog $ctx "--- Stufe 2: Abdeckung (backup --dry-run gegen dieselbe Quelle) ---"
foreach ($t in $targets) {
    if (-not (Test-Path $t.Path)) {
        Add-Failure "$($t.Name): Quelle fehlt ($($t.Path))"
        continue
    }
    Write-BackupLog $ctx "$($t.Name): pruefe $($t.Path)"
    $dry = Invoke-ResticCapture -Exe $ctx.ResticExe -Arguments @(
        "backup", $t.Path,
        "--exclude-file", $ctx.ExcludeFile,
        "--tag", "mosaic-ai", "--tag", $t.Tag,
        "--dry-run", "--verbose"
    )
    if ($dry.ExitCode -ne 0) {
        Add-Failure "$($t.Name): dry-run Exitcode $($dry.ExitCode): $($dry.Output)"
        continue
    }
    # restic meldet z.B.: "Files:  0 new,  0 changed,  4107 unmodified"
    if ($dry.Output -match "Files:\s+(\d+)\s+new,\s+(\d+)\s+changed,\s+(\d+)\s+unmodified") {
        $new = [int]$Matches[1]; $chg = [int]$Matches[2]; $same = [int]$Matches[3]
        Write-BackupLog $ctx "$($t.Name): $new neu, $chg geaendert, $same unveraendert."
        if ($new -eq 0 -and $chg -eq 0) {
            Write-BackupLog $ctx "$($t.Name): vollstaendig abgedeckt."
        } else {
            # Beim Arbeitsbaum ist das NORMAL, sobald seit dem letzten Lauf
            # gearbeitet wurde. Beim Spiegel nicht: der aendert sich nicht mehr.
            if ($t.Tag -eq "legacy-mirror") {
                Add-Failure "$($t.Name): $new neu / $chg geaendert -- der Altbestand aendert sich nicht mehr, hier darf nichts offen sein."
            } else {
                Write-BackupLog $ctx "$($t.Name): HINWEIS -- Abweichung ist normal, wenn seit dem letzten Tageslauf gearbeitet wurde. Vor dem Loeschen einen frischen Tageslauf fahren."
            }
        }
    } else {
        Add-Failure "$($t.Name): Zusammenfassung von restic nicht auswertbar."
    }
}

# --- Stufe 3: Byte-Gleichheit per Stichprobe ---------------------------------
if ($SampleSize -gt 0) {
    Write-BackupLog $ctx "--- Stufe 3: Byte-Gleichheit ($SampleSize Dateien) ---"
    $sampleDir = Join-Path $runDir "sample"

    $daily = @($allSnaps | Where-Object { $_.tags -contains "daily" } | Sort-Object time)
    if (-not $daily.Count) {
        Add-Failure "Kein Snapshot mit Marke 'daily' -- Stichprobe nicht moeglich."
    } else {
        $snapId = $daily[-1].short_id
        $lsOut = Invoke-ResticCapture -Exe $ctx.ResticExe -Arguments @("ls", $snapId, "--recursive", "--json")

        # 'ls --json' liefert JSON-Lines, kein Array: zeilenweise auswerten.
        $files = @()
        foreach ($line in ($lsOut.Output -split "`r?`n")) {
            if (-not $line.Trim()) { continue }
            try { $o = ConvertFrom-Json $line } catch { continue }
            if ($o.struct_type -eq "node" -and $o.type -eq "file" -and $o.size -gt 0) { $files += $o }
        }
        Write-BackupLog $ctx "Dateien im Snapshot $snapId : $($files.Count)"

        if ($files.Count -lt 1) {
            Add-Failure "Snapshot $snapId enthaelt keine Dateien."
        } else {
            # Gezogen wird ueber den ganzen Baum, damit nicht nur eine Ecke
            # geprueft wird. Deterministisch waere hier falsch: eine feste
            # Auswahl prueft bei jedem Lauf dieselben Bloecke.
            $sample = $files | Get-Random -Count ([Math]::Min($SampleSize, $files.Count))

            $restoreArgs = @("restore", $snapId, "--target", $sampleDir)
            foreach ($f in $sample) { $restoreArgs += @("--include", $f.path) }
            $res = Invoke-ResticCapture -Exe $ctx.ResticExe -Arguments $restoreArgs
            # Erst lesbar machen, dann auflisten -- der nachgebaute Pfad erbt
            # sonst die ACL der Quelle und die Aufzaehlung liefert still nichts.
            Unlock-RestoredTree -Path $sampleDir
            $restoredAny = @(Get-ChildItem $sampleDir -Recurse -File -Force -ErrorAction SilentlyContinue).Count
            if ($res.ExitCode -ne 0 -and $restoredAny -eq 0) {
                Add-Failure "restore der Stichprobe fehlgeschlagen: $($res.Output)"
            } else {
                if ($res.ExitCode -ne 0) {
                    # Wie in Stufe 4: der Exitcode faellt auch bei einem
                    # misslungenen Zeitstempel auf einem Elternordner an. Was
                    # zaehlt, sind die zurueckgeschriebenen Dateien.
                    Write-BackupLog $ctx "  HINWEIS: restore meldet Exitcode $($res.ExitCode), hat aber $restoredAny Datei(en) geliefert. Der Vergleich entscheidet."
                }
                $ok = 0; $bad = 0; $missing = 0
                foreach ($f in $sample) {
                    # restic legt den Pfad unterhalb des Ziels ab; die genaue
                    # Form (Laufwerksbuchstabe) ist plattformabhaengig, darum
                    # ueber das Pfadende suchen statt sie vorherzusagen.
                    $tail = ($f.path -replace '^[A-Za-z]:', '') -replace '/', '\'
                    $hit = Get-ChildItem $sampleDir -Recurse -File -Force -ErrorAction SilentlyContinue |
                           Where-Object { $_.FullName.EndsWith($tail, [System.StringComparison]::OrdinalIgnoreCase) } |
                           Select-Object -First 1
                    if (-not $hit) { $missing++; Add-Failure "nicht wiederhergestellt: $($f.path)"; continue }

                    $srcPath = $f.path
                    if (-not (Test-Path $srcPath)) {
                        # Datei existiert in der Quelle nicht mehr -- genau der
                        # Fall, fuer den die Sicherung da ist. Kein Fehler,
                        # aber auch kein Vergleich moeglich.
                        Write-BackupLog $ctx "  (Quelle fehlt, nur im Backup: $($f.path))"
                        $ok++
                        continue
                    }
                    $hSrc = (Get-FileHash $srcPath -Algorithm SHA256).Hash
                    $hOut = (Get-FileHash $hit.FullName -Algorithm SHA256).Hash
                    if ($hSrc -eq $hOut) { $ok++ } else { $bad++; Add-Failure "SHA-256 weicht ab: $($f.path)" }
                }
                Write-BackupLog $ctx "Stichprobe: $ok gleich, $bad abweichend, $missing fehlend."
            }
        }
    }
    if (Test-Path $sampleDir) { Remove-Item $sampleDir -Recurse -Force }
}

# --- Stufe 4: Zip-Historie ---------------------------------------------------
if ($Zips) {
    Write-BackupLog $ctx "--- Stufe 4: Zip-Historie (models-Zips gegen ihre Snapshots) ---"
    $zipDir = Join-Path $ctx.BackupRoot "models_snapshots"
    if (-not (Test-Path $zipDir)) {
        Write-BackupLog $ctx "HINWEIS: $zipDir existiert nicht -- nichts zu pruefen (vermutlich schon entfernt)."
    } else {
        Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue

        # Je Datum eine LISTE, nicht ein Eintrag: es kann mehrere Snapshots
        # zum selben Tag geben (etwa wenn zwei Zip-Dateien dasselbe Datum im
        # Namen tragen -- OneDrive-Konfliktkopien tun das). Eine Zuordnung
        # 1:1 wuerde solche Faelle still verschlucken, statt sie zu zeigen.
        # Zuordnung bevorzugt ueber die Marke "zip:<dateiname>" -- die ist
        # eindeutig. Der datumsbasierte Weg bleibt als Rueckfall fuer
        # Snapshots aus dem Import vom 2026-08-31, der diese Marke noch nicht
        # gesetzt hat; dort ist er zwangslaeufig ungenau, weil auf ein Datum
        # bis zu vier Zips fallen.
        $byZipName = @{}
        $modelSnaps = @{}
        foreach ($s in ($allSnaps | Where-Object { $_.tags -contains "models-snapshot" })) {
            foreach ($t in $s.tags) {
                if ($t -like "zip:*") { $byZipName[$t.Substring(4)] = $s.short_id }
            }
            $d = ([datetime]$s.time).ToString("yyyy-MM-dd")
            if (-not $modelSnaps.ContainsKey($d)) { $modelSnaps[$d] = @() }
            $modelSnaps[$d] += $s.short_id
        }
        Write-BackupLog $ctx "Snapshots mit zip-Marke: $($byZipName.Count) von $(@($allSnaps | Where-Object { $_.tags -contains 'models-snapshot' }).Count)"
        $zipFiles = @(Get-ChildItem $zipDir -Filter "models_*.zip" -File | Sort-Object Name)
        # $modelSnaps ist nach DATUM gruppiert, seine Count ist also die Zahl
        # der Tage, nicht der Snapshots. Die alte Beschriftung ("models-
        # Snapshots im Repo: 6") hat genau deshalb in die Irre gefuehrt.
        $modelSnapTotal = @($allSnaps | Where-Object { $_.tags -contains "models-snapshot" }).Count
        Write-BackupLog $ctx "Zips: $($zipFiles.Count), models-Snapshots: $modelSnapTotal auf $($modelSnaps.Count) verschiedene Tage"

        $idx = 0
        $usedSnaps = @{}
        foreach ($zf in $zipFiles) {
            $idx++
            # [regex]::Match statt "-notmatch" plus $Matches: $Matches ist eine
            # automatische Variable, deren Aktualisierung bei -notmatch nicht
            # verlaesslich ist. Am 2026-08-31 hat genau das zwei aufeinander
            # folgende Zips auf dasselbe Datum abgebildet.
            $m = [regex]::Match($zf.Name, '(\d{4}-\d{2}-\d{2})')
            if (-not $m.Success) {
                Add-Failure "Zip ohne Datum im Namen: $($zf.Name)"
                continue
            }
            $stamp = $m.Groups[1].Value

            if ($byZipName.ContainsKey($zf.Name)) {
                $snapId = $byZipName[$zf.Name]
                $how = "ueber zip-Marke"
            } elseif ($modelSnaps.ContainsKey($stamp)) {
                # Rueckfall: reihum den naechsten noch nicht verwendeten
                # Snapshot dieses Datums. Bei mehreren Zips pro Tag ist die
                # Paarung damit nur eine VERMUTUNG -- das wird auch so gesagt.
                if (-not $usedSnaps.ContainsKey($stamp)) { $usedSnaps[$stamp] = 0 }
                $candidates = @($modelSnaps[$stamp])
                if ($usedSnaps[$stamp] -ge $candidates.Count) {
                    Add-Failure "[$idx/$($zipFiles.Count)] $($zf.Name): zum Datum $stamp gibt es nur $($candidates.Count) Snapshot(s), aber mehr Zips."
                    continue
                }
                $snapId = $candidates[$usedSnaps[$stamp]]
                $usedSnaps[$stamp]++
                $how = if ($candidates.Count -gt 1) { "ueber Datum, RATEN ($($candidates.Count) Snapshots an diesem Tag)" } else { "ueber Datum" }
            } else {
                Add-Failure "[$idx/$($zipFiles.Count)] $($zf.Name) ($stamp): KEIN Snapshot zu diesem Zip -- nicht importiert."
                continue
            }

            Write-BackupLog $ctx "[$idx/$($zipFiles.Count)] $($zf.Name) gegen Snapshot $snapId ($how) ..."

            # Eigenes Verzeichnis JE ZIP. Grund: restic legt beim Restore den
            # vollen Quellpfad nach (…\zipcheck\C\Users\…), und auf dem
            # nachgebauten "C\Users" scheitert unter Windows sowohl das Setzen
            # des Zeitstempels als auch spaeter das Loeschen (Zugriff
            # verweigert). Mit einem gemeinsamen Verzeichnis blockiert dieser
            # Rest jeden folgenden Durchgang.
            $zipWork = Join-Path $runDir ("zip_{0:d3}" -f $idx)
            New-Item -ItemType Directory -Force $zipWork | Out-Null

            $res = Invoke-ResticCapture -Exe $ctx.ResticExe -Arguments @("restore", $snapId, "--target", $zipWork)
            if ($res.ExitCode -ne 0) {
                # NICHT abbrechen. Der Exitcode ist hier kein gutes Beweismittel:
                # restic meldet "Fatal: There were 1 errors" auch dann, wenn
                # lediglich der Zeitstempel eines nachgebauten Elternordners
                # nicht gesetzt werden konnte, waehrend alle Nutzdaten
                # zurueckgeschrieben wurden. Was zaehlt, ist der Hash-Vergleich
                # weiter unten -- fehlt wirklich etwas, faellt es dort auf.
                Write-BackupLog $ctx "  HINWEIS: restore meldet Exitcode $($res.ExitCode). Wird als Warnung behandelt, der Vergleich entscheidet."
                foreach ($l in ($res.Output -split "`r?`n" | Where-Object { $_ -match 'error|Fatal' } | Select-Object -First 3)) {
                    Write-BackupLog $ctx "    $l"
                }
            }

            $archive = [System.IO.Compression.ZipFile]::OpenRead($zf.FullName)
            try {
                $entries = @{}
                foreach ($e in $archive.Entries) {
                    # Leerer Name = Verzeichniseintrag, hat keinen Inhalt.
                    if (-not $e.Name) { continue }
                    $entries[$e.FullName.Replace('/', '\')] = $e
                }

                # Erst lesbar machen, dann auflisten -- sonst liefert die
                # Aufzaehlung wegen der geerbten ACL still eine leere Liste.
                Unlock-RestoredTree -Path $zipWork
                $restored = @(Get-ChildItem $zipWork -Recurse -File -Force -ErrorAction SilentlyContinue)
                if (-not $restored.Count) {
                    Add-Failure "[$($zf.Name)] Snapshot $snapId hat KEINE Datei geliefert."
                    continue
                }
                $toHash = $restored
                if ($ZipSample -gt 0 -and $restored.Count -gt $ZipSample) {
                    $toHash = @($restored | Get-Random -Count $ZipSample)
                }
                $hashSet = @{}
                foreach ($h in $toHash) { $hashSet[$h.FullName] = $true }

                $seen = @{}
                $equal = 0; $mismatch = 0
                foreach ($rf in $restored) {
                    $full = $rf.FullName
                    # ERSTES "\models\" unterhalb des Ziels, nicht das letzte:
                    # ein verschachtelter Ordner gleichen Namens wuerde den
                    # relativen Pfad sonst falsch abschneiden.
                    $marker = '\models\'
                    $p = $full.IndexOf($marker, $zipWork.Length, [System.StringComparison]::OrdinalIgnoreCase)
                    if ($p -lt 0) {
                        Add-Failure "[$stamp] unerwarteter Pfad im Snapshot: $full"
                        continue
                    }
                    $rel = $full.Substring($p + $marker.Length)
                    $seen[$rel] = $true

                    if (-not $entries.ContainsKey($rel)) {
                        Add-Failure "[$stamp] im Snapshot, aber NICHT im Zip: $rel"
                        continue
                    }
                    if (-not $hashSet.ContainsKey($full)) { continue }

                    # Den Zip-Eintrag streamen statt das Archiv auszupacken.
                    $stream = $entries[$rel].Open()
                    try {
                        $sha = [System.Security.Cryptography.SHA256]::Create()
                        $zipHash = [BitConverter]::ToString($sha.ComputeHash($stream)).Replace("-", "")
                    } finally { $stream.Dispose() }

                    if ($zipHash -eq (Get-FileHash $full -Algorithm SHA256).Hash) { $equal++ }
                    else { $mismatch++; Add-Failure "[$stamp] SHA-256 weicht ab: $rel" }
                }

                # Gegenrichtung. Das Skript entscheidet NICHT selbst, was
                # legitim ausgeschlossen war -- es sortiert nur den erwarteten
                # Fall (venv) vor und legt den Rest zur Ansicht vor.
                $onlyZip = @($entries.Keys | Where-Object { -not $seen.ContainsKey($_) })
                $expected = @($onlyZip | Where-Object { $_ -match '(^|\\)venv\\' })
                $unexpected = @($onlyZip | Where-Object { $_ -notmatch '(^|\\)venv\\' })

                Write-BackupLog $ctx "  $($restored.Count) Dateien im Snapshot, $equal gehasht und gleich, $mismatch abweichend."
                Write-BackupLog $ctx "  nur im Zip: $($onlyZip.Count) (davon $($expected.Count) unterhalb venv\, erwartet)"
                if ($unexpected.Count) {
                    Add-Failure "[$stamp] $($unexpected.Count) Datei(en) nur im Zip und NICHT unter venv\ -- ansehen:"
                    foreach ($u in ($unexpected | Select-Object -First 10)) { Write-BackupLog $ctx "      $u" }
                }
            } finally {
                $archive.Dispose()
            }
            [void](Remove-RestoredTree -Path $zipWork)
        }
    }
} else {
    Write-BackupLog $ctx "Stufe 4 uebersprungen. VOR dem Loeschen von models_snapshots\ mit -Zips fahren -- sonst bleibt der Import dieser Staende unbelegt."
}

# --- Stufe 5: Tiefenpruefung -------------------------------------------------
if ($Deep) {
    Write-BackupLog $ctx "--- Stufe 5: Tiefenpruefung (check --read-data, liest das ganze Repository) ---"
    # BEWUSST OHNE Invoke-ResticCapture. Diese Stufe laeuft ueber Stunden, und
    # eine eingesammelte Ausgabe waere bis zum Ende unsichtbar -- genau das,
    # was die Projektregel "Lange Laeufe NIE in eine Pipe" verbietet. restic
    # druckt hier einen Fortschrittsbalken; der gehoert auf den Schirm.
    # Ausgewertet wird ohnehin nur der Exitcode, der Text stand dann schon da.
    Write-BackupLog $ctx "Fortschritt erscheint direkt von restic; das kann bei diesem Repository Stunden dauern."
    & $ctx.ResticExe check --read-data
    $deepRc = $LASTEXITCODE
    if ($deepRc -ne 0) {
        Add-Failure "check --read-data meldet Exitcode $deepRc (Meldungen stehen oben in der Ausgabe)."
    } else {
        Write-BackupLog $ctx "Alle Pack-Bytes gelesen und geprueft."
    }
} else {
    Write-BackupLog $ctx "Stufe 5 uebersprungen. Vor dem Loeschen des Altbestands einmal mit -Deep fahren."
}

# --- Aufraeumen --------------------------------------------------------------
# Nur das Verzeichnis dieses Laufs. Was sonst in $WorkDir liegt, gehoert dem
# Nutzer und wurde oben lediglich gemeldet.
[void](Remove-RestoredTree -Path $runDir)

# --- Bilanz ------------------------------------------------------------------
Write-BackupLog $ctx "--- Bilanz ---"
foreach ($mode in @("restore-size", "raw-data")) {
    $s = Invoke-ResticCapture -Exe $ctx.ResticExe -Arguments @("stats", "--mode", $mode)
    Write-BackupLog $ctx "stats $mode : $($s.Output -replace "`r?`n", ' | ')"
}

$elapsed = (Get-Date) - $startedAt
Write-BackupLog $ctx ("Fertig nach {0:N0}s." -f $elapsed.TotalSeconds)

if ($failures.Count) {
    Write-BackupLog $ctx "VERDIKT: NICHT freigegeben -- $($failures.Count) Beanstandung(en). Altbestand behalten."
    foreach ($f in $failures) { Write-BackupLog $ctx "  - $f" }
    exit 1
}

Write-BackupLog $ctx "VERDIKT: alle gefahrenen Stufen gruen."
# Die Zip-Mahnung nur, solange es Zips gibt. Sind sie fort, ist entweder
# geprueft worden oder die Gelegenheit ist ohnehin vorbei -- in beiden Faellen
# ist die Zeile nur noch Rauschen, und eine Mahnung, die man wegsehen lernt,
# taugt beim naechsten Mal nichts mehr.
if (-not $Zips -and $ctx.BackupRoot -and (Test-Path (Join-Path $ctx.BackupRoot "models_snapshots"))) {
    Write-BackupLog $ctx "OFFEN: ohne -Zips ist der Import der models-Staende unbelegt. Vor dem Loeschen von models_snapshots\ nachholen -- danach geht es nicht mehr."
}
if (-not $Deep) { Write-BackupLog $ctx "OFFEN: ohne -Deep ist kein stiller Datenfehler ausgeschlossen. Vor dem Loeschen nachholen." }
exit 0
