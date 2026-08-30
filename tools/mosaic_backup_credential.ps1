<#
.SYNOPSIS
    Legt das restic-Repository-Passwort im Windows Credential Manager ab und
    gibt es auf Anforderung aus (fuer RESTIC_PASSWORD_COMMAND).

.DESCRIPTION
    Dritter Weg neben Passwortdatei und RESTIC_PASSWORD. Der Unterschied:

      RESTIC_PASSWORD        Geheimnis liegt im Klartext in HKCU\Environment
                             und wird an JEDEN Kindprozess vererbt.
      RESTIC_PASSWORD_FILE   Geheimnis liegt im Klartext in einer Datei; die
                             Umgebung verraet nur den Pfad.
      RESTIC_PASSWORD_COMMAND (dieses Skript)
                             Die Umgebung verraet nur einen Aufruf. Das
                             Geheimnis liegt im Credential Manager, den
                             Windows mit DPAPI an Konto und Maschine bindet
                             -- eine kopierte Datei nuetzt einem Angreifer
                             auf einem anderen Rechner nichts.

    Relevant, weil dieses Repo OEFFENTLICH ist und sein Werkzeugkasten
    laufend Manifeste, Logs und JSON-Artefakte schreibt. Was nicht in der
    Umgebung steht, kann kein Skript versehentlich mitprotokollieren.

    Der Zugriff laeuft ueber die Win32-Funktionen CredWriteW/CredReadW/
    CredDeleteW (advapi32.dll). Absichtlich ohne PowerShell-Galerie-Modul:
    eine zusaetzliche Abhaengigkeit fuer drei API-Aufrufe waere schlechter
    Tausch, und ein Backup soll nicht an einem fehlenden Modul scheitern.

.PARAMETER Get
    Gibt das Passwort auf stdout aus, ohne Zeilenumbruch und ohne jede
    weitere Ausgabe. Vorgabemodus -- genau das erwartet restic von
    RESTIC_PASSWORD_COMMAND.

.PARAMETER Set
    Fragt ein Passwort ab (verdeckt) und legt es ab. Fuer den Fall, dass
    schon ein Repository mit bekanntem Passwort existiert.

.PARAMETER Generate
    Erzeugt ein neues Zufallspasswort (32 Byte, Base64), legt es ab und
    zeigt es EINMAL an. Fuer ein noch nicht angelegtes Repository.

.PARAMETER Remove
    Entfernt den Eintrag. Loescht kein Repository -- macht es aber
    unzugaenglich, solange keine Kopie des Passworts existiert.

.PARAMETER Target
    Name des Eintrags im Credential Manager. Vorgabe: mosaic-ai-restic.
    Unter diesem Namen taucht er in der Windows-Anmeldeinformations-
    verwaltung auf.

.EXAMPLE
    # Einmalig einrichten (neues Repository):
    powershell -File tools\mosaic_backup_credential.ps1 -Generate

.EXAMPLE
    # Danach dauerhaft bekannt machen:
    setx RESTIC_PASSWORD_COMMAND "powershell -NoProfile -ExecutionPolicy Bypass -File D:\...\tools\mosaic_backup_credential.ps1"

.NOTES
    GRENZE DIESES VERFAHRENS -- vor dem Einrichten der geplanten Aufgabe
    lesen: DPAPI entschluesselt nur in einer Sitzung, in der die
    Benutzerschluessel geladen sind. Eine geplante Aufgabe mit "Nur
    ausfuehren, wenn der Benutzer angemeldet ist" oder mit hinterlegtem
    Kennwort erfuellt das. Eine Aufgabe mit "Nicht gespeichertes Kennwort
    verwenden" (S4U) erfuellt es NICHT -- dort schlaegt das Auslesen fehl,
    und zwar auch dann, wenn es interaktiv einwandfrei funktioniert.
    In dem Fall ist RESTIC_PASSWORD_FILE der richtige Weg.

    Das Skript wird auch von einem Menschen bedient (-Set fragt verdeckt ab);
    im Vorgabemodus -Get ist es vollstaendig nicht-interaktiv.
#>
[CmdletBinding(DefaultParameterSetName = "Get")]
param(
    [Parameter(ParameterSetName = "Get")][switch]$Get,
    [Parameter(ParameterSetName = "Set")][switch]$Set,
    [Parameter(ParameterSetName = "Generate")][switch]$Generate,
    [Parameter(ParameterSetName = "Remove")][switch]$Remove,
    [string]$Target = "mosaic-ai-restic"
)

$ErrorActionPreference = "Stop"

# --- Win32-Anbindung --------------------------------------------------------
# EntryPoint explizit auf die W-Fassungen: bei CharSet.Unicode ohne
# ExactSpelling haengt .NET sonst ein weiteres "W" an einen bereits auf W
# endenden Namen und findet die Funktion nicht.
if (-not ("MosaicCredMan" -as [type])) {
    Add-Type -Namespace "" -Name "MosaicCredMan" -MemberDefinition @'
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct CREDENTIAL {
        public uint Flags;
        public uint Type;
        public string TargetName;
        public string Comment;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
        public uint CredentialBlobSize;
        public IntPtr CredentialBlob;
        public uint Persist;
        public uint AttributeCount;
        public IntPtr Attributes;
        public string TargetAlias;
        public string UserName;
    }

    [DllImport("advapi32.dll", EntryPoint = "CredWriteW", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern bool CredWrite(ref CREDENTIAL credential, uint flags);

    [DllImport("advapi32.dll", EntryPoint = "CredReadW", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern bool CredRead(string target, uint type, uint flags, out IntPtr credential);

    [DllImport("advapi32.dll", EntryPoint = "CredDeleteW", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern bool CredDelete(string target, uint type, uint flags);

    [DllImport("advapi32.dll", EntryPoint = "CredFree")]
    public static extern void CredFree(IntPtr buffer);
'@
}

$CRED_TYPE_GENERIC = 1
$CRED_PERSIST_LOCAL_MACHINE = 2
$ERROR_NOT_FOUND = 1168

function Write-Credential {
    param([string]$TargetName, [string]$Secret)

    # Der Blob ist fuer Windows undurchsichtig; entscheidend ist, dass Lesen
    # und Schreiben dieselbe Kodierung verwenden. UTF-16LE ist die Konvention
    # unter Windows.
    $bytes = [System.Text.Encoding]::Unicode.GetBytes($Secret)
    $blob = [System.Runtime.InteropServices.Marshal]::AllocHGlobal($bytes.Length)
    try {
        [System.Runtime.InteropServices.Marshal]::Copy($bytes, 0, $blob, $bytes.Length)

        $cred = New-Object MosaicCredMan+CREDENTIAL
        $cred.Type = $CRED_TYPE_GENERIC
        $cred.TargetName = $TargetName
        $cred.Comment = "restic-Repository-Passwort fuer mosaic-AI (tools/mosaic_backup.ps1)"
        $cred.CredentialBlobSize = $bytes.Length
        $cred.CredentialBlob = $blob
        $cred.Persist = $CRED_PERSIST_LOCAL_MACHINE
        $cred.UserName = $env:USERNAME

        if (-not [MosaicCredMan]::CredWrite([ref]$cred, 0)) {
            $code = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()
            throw "CredWrite fehlgeschlagen (Win32-Fehler $code)."
        }
    } finally {
        [System.Runtime.InteropServices.Marshal]::FreeHGlobal($blob)
        [Array]::Clear($bytes, 0, $bytes.Length)
    }
}

function Read-Credential {
    param([string]$TargetName)

    $ptr = [IntPtr]::Zero
    if (-not [MosaicCredMan]::CredRead($TargetName, $CRED_TYPE_GENERIC, 0, [ref]$ptr)) {
        $code = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()
        if ($code -eq $ERROR_NOT_FOUND) {
            throw "Kein Eintrag '$TargetName' im Credential Manager. Einmalig anlegen mit: -Generate (neues Repository) oder -Set (vorhandenes Passwort)."
        }
        throw "CredRead fehlgeschlagen (Win32-Fehler $code). Bei einer geplanten Aufgabe mit 'Nicht gespeichertes Kennwort verwenden' ist das der erwartete Fehler -- siehe .NOTES im Skriptkopf."
    }
    try {
        $cred = [System.Runtime.InteropServices.Marshal]::PtrToStructure($ptr, [type]("MosaicCredMan+CREDENTIAL"))
        if ($cred.CredentialBlobSize -eq 0) { return "" }
        $bytes = New-Object byte[] $cred.CredentialBlobSize
        [System.Runtime.InteropServices.Marshal]::Copy($cred.CredentialBlob, $bytes, 0, $cred.CredentialBlobSize)
        return [System.Text.Encoding]::Unicode.GetString($bytes)
    } finally {
        [MosaicCredMan]::CredFree($ptr)
    }
}

# --- Modi -------------------------------------------------------------------
switch ($PSCmdlet.ParameterSetName) {

    "Generate" {
        $b = New-Object byte[] 32
        [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
        $secret = [Convert]::ToBase64String($b)
        Write-Credential -TargetName $Target -Secret $secret

        Write-Host ""
        Write-Host "Passwort erzeugt und unter '$Target' im Credential Manager abgelegt."
        Write-Host ""
        Write-Host "  $secret"
        Write-Host ""
        Write-Warning "SCHREIB DAS AUF, an einem Ort ausserhalb dieses Rechners. Es wird nicht wieder angezeigt. Geht der Credential-Manager-Eintrag verloren (Profilschaden, Neuinstallation), ist das Repository ohne diese Zeichenkette unwiederbringlich -- restic hat keine Hintertuer."
    }

    "Set" {
        $secure = Read-Host -Prompt "restic-Repository-Passwort" -AsSecureString
        $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        try {
            $secret = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
            if (-not $secret) { throw "Leeres Passwort -- nichts abgelegt." }
            Write-Credential -TargetName $Target -Secret $secret
        } finally {
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
        Write-Host "Passwort unter '$Target' im Credential Manager abgelegt."
    }

    "Remove" {
        if (-not [MosaicCredMan]::CredDelete($Target, $CRED_TYPE_GENERIC, 0)) {
            $code = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()
            if ($code -eq $ERROR_NOT_FOUND) {
                Write-Host "Kein Eintrag '$Target' vorhanden -- nichts zu entfernen."
            } else {
                throw "CredDelete fehlgeschlagen (Win32-Fehler $code)."
            }
        } else {
            Write-Host "Eintrag '$Target' entfernt. Das Repository bleibt bestehen, ist ohne Passwortkopie aber nicht mehr zugaenglich."
        }
    }

    default {
        # Get: AUSSCHLIESSLICH das Passwort auf stdout, ohne Zeilenumbruch.
        # restic ruft diesen Befehl direkt auf (keine Shell dazwischen) und
        # nimmt seine Ausgabe als Passwort -- jede zusaetzliche Zeile, auch
        # eine Fortschrittsmeldung, waere Teil des Geheimnisses.
        [Console]::Out.Write((Read-Credential -TargetName $Target))
    }
}
