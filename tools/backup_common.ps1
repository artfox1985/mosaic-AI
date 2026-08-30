<#
.SYNOPSIS
    Gemeinsame Aufloesung von restic-Binary, Repository, Passwort und Log.

.DESCRIPTION
    Wird von tools/mosaic_backup.ps1 (Tageslauf) und
    tools/mosaic_backup_seed.ps1 (einmaliger Import des robocopy-Bestands)
    per Dot-Sourcing eingebunden. Zweck: die Ziel- und Passwortaufloesung
    steht an EINER Stelle. Zwei Kopien waeren genau die Sorte Drift, bei der
    der Import in ein anderes Repository laeuft als der Tageslauf.

    Bewusst PowerShell-5.1-tauglich (kein ?.-Operator, keine
    Ternaeroperatoren): die Aufgabenplanung startet per Vorgabe
    powershell.exe, nicht pwsh.
#>

function Initialize-BackupContext {
    <#
    .SYNOPSIS
        Loest alles auf, was beide Skripte brauchen, und bricht sonst ab.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$ToolsDir,
        [string]$LogPrefix = "backup"
    )

    # --- restic finden ------------------------------------------------------
    # winget schreibt seinen Links-Ordner in die Registry-PATH, aber bereits
    # laufende Prozesse erben die alte Umgebung. Darum hier neu einlesen, sonst
    # scheitert ein Lauf aus einer Shell, die aelter ist als die Installation.
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:PATH = ($machinePath, $userPath | Where-Object { $_ }) -join ";"

    if ($env:MOSAIC_RESTIC_EXE) {
        $resticExe = $env:MOSAIC_RESTIC_EXE
    } else {
        $resticCmd = Get-Command restic -ErrorAction SilentlyContinue
        if ($resticCmd) { $resticExe = $resticCmd.Source } else { $resticExe = $null }
    }

    # Fallback: winget installiert restic als PORTABLE-Paket. Dabei landet die
    # Exe unter Packages\, und in Links\ entsteht ein Alias, dessen Ordner
    # winget in die PATH eintraegt. Beides greift nicht immer -- auf dieser
    # Maschine meldet 'winget list' Version 0.19.1, waehrend 'where.exe restic'
    # leer bleibt. Statt daran zu scheitern, an den bekannten Orten nachsehen.
    if (-not $resticExe -or -not (Test-Path $resticExe)) {
        $searchRoots = @(
            (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet"),
            (Join-Path ${env:ProgramFiles} "WinGet"),
            (Join-Path ${env:ProgramFiles} "restic")
        ) | Where-Object { $_ -and (Test-Path $_) }

        foreach ($root in $searchRoots) {
            # -Filter restic*.exe, weil das Portable-Paket die Datei unter
            # ihrem Release-Namen ablegt (restic_0.19.1_windows_amd64.exe) und
            # nur der Link in Links\ schlicht restic.exe heisst.
            $found = Get-ChildItem $root -Recurse -Filter "restic*.exe" -File -ErrorAction SilentlyContinue |
                     Sort-Object FullName |
                     Select-Object -First 1
            if ($found) {
                $resticExe = $found.FullName
                Write-Warning "restic war nicht im PATH, gefunden unter: $resticExe. Dauerhaft festnageln mit: setx MOSAIC_RESTIC_EXE `"$resticExe`""
                break
            }
        }
    }

    if (-not $resticExe -or -not (Test-Path $resticExe)) {
        throw "restic nicht gefunden -- weder im PATH noch unter den winget-Ablageorten. 'winget install restic.restic' ausfuehren, oder MOSAIC_RESTIC_EXE auf den vollen Pfad zu restic.exe setzen."
    }

    # --- Sicherungswurzel und Repository ------------------------------------
    # backupRoot ist der Ordner der ALTEN robocopy-Sicherung (mirror,
    # models_snapshots, logs). Der Import braucht ihn, der Tageslauf nur fuer
    # das Log.
    if ($env:MOSAIC_BACKUP_DIR) {
        $backupRoot = $env:MOSAIC_BACKUP_DIR
    } elseif ($env:OneDrive) {
        $backupRoot = Join-Path $env:OneDrive "Backups\mosaic-AI"
    } else {
        $backupRoot = $null
    }

    if ($env:MOSAIC_RESTIC_REPO) {
        $repoPath = $env:MOSAIC_RESTIC_REPO
    } elseif ($backupRoot) {
        # Nutzer-Entscheid 2026-08-30: das Repository liegt DIREKT im
        # Sicherungswurzel-Ordner (<OneDrive>\Backups\mosaic-AI), nicht in
        # einem Unterordner.
        #
        # Das geht, weil restics lokales Backend beim Anlegen ausschliesslich
        # prueft, ob dort schon eine 'config' liegt
        # (internal/backend/local/local.go, Create); vorhandenen Fremdinhalt
        # laesst es stehen und legt seine Struktur daneben an. Kollisionen mit
        # dem Altbestand gibt es nicht -- restic belegt config, data, index,
        # keys, locks, snapshots; der Altbestand mirror, models_snapshots,
        # logs.
        #
        # ACHTUNG beim spaeteren Aufraeumen: nach dem Import stehen
        # Altbestand und Repository im SELBEN Ordner. Wer dann mirror\ und
        # models_snapshots\ entfernt, muss die restic-Verzeichnisse stehen
        # lassen -- sie sind ab dann die einzige Kopie.
        $repoPath = $backupRoot
    } else {
        throw "Kein Sicherungsziel: MOSAIC_RESTIC_REPO, MOSAIC_BACKUP_DIR oder OneDrive setzen."
    }

    # Warnung, keine Sperre. Grund: ein Chunk-Repository ist gegen Teilverlust
    # empfindlicher als lose Dateien -- faellt eine Pack-Datei aus, fehlen
    # deren Bloecke in ALLEN Snapshots, auch monatealten. Ausserdem teilen sich
    # Quelle und Sicherung dann dieselbe Fehlerdomaene.
    if ($env:OneDrive -and $repoPath.StartsWith($env:OneDrive, [System.StringComparison]::OrdinalIgnoreCase)) {
        Write-Warning "Repository liegt unter OneDrive ($repoPath). Besser ein externes/lokales Ziel via MOSAIC_RESTIC_REPO. Falls es dort bleibt: Ordner auf 'Immer auf diesem Geraet behalten' stellen -- restic braucht seine Pack-Dateien materialisiert."
    }

    # --- Passwort -----------------------------------------------------------
    # restic akzeptiert drei Wege (Doku, Abschnitt "Environment variables"):
    # RESTIC_PASSWORD_FILE (Pfad), RESTIC_PASSWORD (Klartext) und
    # RESTIC_PASSWORD_COMMAND (Befehl, der es auf stdout druckt). Das Skript
    # laesst alle drei zu und prueft nur, dass ueberhaupt einer gesetzt ist --
    # sonst bliebe restic an einer Passwortabfrage haengen, die im
    # unbeaufsichtigten Lauf niemand beantwortet.
    #
    # EMPFEHLUNG bleibt die Datei. Grund ist nicht die Ablageform an sich --
    # 'setx' schreibt genauso im Klartext nach HKCU\Environment --, sondern
    # die Streuung: eine Umgebungsvariable erbt JEDER Prozess, den man
    # startet. Dieses Repo ist oeffentlich und sein Werkzeugkasten schreibt
    # Manifeste und Artefakte; ein einziger Umgebungs-Abzug in einem Log oder
    # JSON, und das Passwort steht in einem oeffentlichen Commit. Ein Pfad
    # verraet nur einen Pfad.
    if ($env:RESTIC_PASSWORD_FILE) {
        if (-not (Test-Path $env:RESTIC_PASSWORD_FILE)) {
            throw "RESTIC_PASSWORD_FILE zeigt auf eine nicht vorhandene Datei: $($env:RESTIC_PASSWORD_FILE)"
        }
        $passwordSource = "RESTIC_PASSWORD_FILE"
    } elseif ($env:RESTIC_PASSWORD_COMMAND) {
        $passwordSource = "RESTIC_PASSWORD_COMMAND"
    } elseif ($env:RESTIC_PASSWORD) {
        $passwordSource = "RESTIC_PASSWORD"
    } else {
        throw "Kein Repository-Passwort gesetzt. Einen der drei Wege waehlen: RESTIC_PASSWORD_FILE (empfohlen), RESTIC_PASSWORD_COMMAND oder RESTIC_PASSWORD. Das Geheimnis gehoert AUSSERHALB des Projektordners -- das Repo ist oeffentlich."
    }

    $env:RESTIC_REPOSITORY = $repoPath

    # --- Ausschlussliste ----------------------------------------------------
    $excludeFile = Join-Path $ToolsDir "backup_excludes.txt"
    if (-not (Test-Path $excludeFile)) {
        throw "Ausschlussliste fehlt: $excludeFile"
    }

    # --- Log ----------------------------------------------------------------
    # Logs neben den Altbestand. Seit das Repository direkt im
    # Sicherungswurzel-Ordner liegt, waere (Split-Path -Parent $repoPath) eine
    # Ebene zu hoch -- das ist nur noch der Rueckfall fuer ein per
    # MOSAIC_RESTIC_REPO woanders hin gelegtes Repository.
    if ($backupRoot) {
        $logDir = Join-Path $backupRoot "logs"
    } else {
        $logDir = Join-Path (Split-Path -Parent $repoPath) "logs"
    }
    New-Item -ItemType Directory -Force $logDir | Out-Null
    $logFile = Join-Path $logDir ("{0}_{1}.log" -f $LogPrefix, (Get-Date -Format "yyyy-MM-dd"))

    # PasswordSource ist der NAME der Variablen, nie ihr Wert -- die Logdatei
    # liegt in OneDrive.
    return [pscustomobject]@{
        ResticExe      = $resticExe
        RepoPath       = $repoPath
        BackupRoot     = $backupRoot
        SourceDir      = Split-Path -Parent $ToolsDir
        ExcludeFile    = $excludeFile
        LogFile        = $logFile
        PasswordSource = $passwordSource
    }
}

function Write-BackupLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]$Context,
        [Parameter(Mandatory = $true)][string]$Message
    )
    $line = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $Message
    Add-Content -Path $Context.LogFile -Value $line
    # Write-Host statt Write-Output: die Zeile ist Fortschrittsanzeige, kein
    # Rueckgabewert -- sonst landet sie in der Pipeline des Aufrufers.
    Write-Host $line
}

function Confirm-ResticRepo {
    <#
    .SYNOPSIS
        Legt das Repository an, falls noch keines existiert.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)]$Context)

    # 'cat config' ist die billigste Existenzpruefung: liest genau einen
    # Datensatz und sagt zugleich, ob das Passwort passt.
    & $Context.ResticExe cat config *> $null
    if ($LASTEXITCODE -eq 0) { return }

    Write-BackupLog $Context "Kein lesbares Repository unter $($Context.RepoPath) -- lege eines an."
    & $Context.ResticExe init
    if ($LASTEXITCODE -ne 0) {
        throw "restic init fehlgeschlagen (Exitcode $LASTEXITCODE)."
    }
    Write-BackupLog $Context "Repository angelegt (Format v2, Kompression aktiv)."
}

function Test-IsElevated {
    $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object System.Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
}
