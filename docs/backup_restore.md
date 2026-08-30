# Sicherung und Wiederherstellung (restic)

**Kanonischer Ort seit 2026-08-31.** Entstanden beim Umstieg von der
robocopy-Fassung auf restic (Commit 76b8e25 und Folgende). Wer hier etwas
aendert, aendert HIER; STATUS.md traegt hoechstens einen Verweis. Grund:
Wiederherstellungswissen wird selten gebraucht und genau dann dringend --
in STATUS.md wuerde es zwischen zwei Kuerzungen verrotten.

Keine absoluten Pfade in dieser Datei (oeffentliches Repo). Es gilt:

- `<Projektordner>` -- die Arbeitskopie von mosaic-AI.
- `<Sicherungswurzel>` -- das Ziel, das `tools/backup_common.ps1` aufloest:
  `MOSAIC_BACKUP_DIR`, sonst der Ordner `Backups\mosaic-AI` im OneDrive des
  angemeldeten Nutzers. **Das restic-Repository liegt DIREKT dort**, nicht
  in einem Unterordner (Nutzer-Entscheid 2026-08-31).

## Was im Repository liegt -- und was nicht

Gesichert wird der ganze Projektordner, auch das Getrackte. Die getrackten
Dateien sind 56 MB von 6.722 MB (0,84 %, gemessen 2026-08-30); sie
wegzulassen spart nichts und kostet im Ernstfall die uncommitteten Staende.
`.git` kostet 63 MB und traegt jeden getrackten Stand jedes Commits.

**Nicht** im Backup, weil regenerierbar (`tools/backup_excludes.txt`):
`engine/target`, `dist`, `build`, `__pycache__`, alle `*.h5`
(Trainingscaches, 5.331 MB), `logs`, `scratchpad` und die `venv/` in den
eingefrorenen Artefakten. Die `.whl` DARIN bleiben gesichert -- sie sind der
Traeger des Verhaltens, das venv entsteht daraus neu.

Wer eine dieser Dateien vermisst, sucht vergeblich: sie wird gebaut, nicht
wiederhergestellt.

## Voraussetzungen fuer den Zugriff von Hand

Die Skripte loesen Repository, Passwort und restic-Pfad selbst auf. Auf der
Kommandozeile hat man das nicht -- beides einmalig setzen:

```
setx RESTIC_REPOSITORY "<Sicherungswurzel>"
```

`restic` ist unter Umstaenden nicht unter diesem Namen aufrufbar: das
winget-Portable-Paket legt die Datei unter ihrem Release-Namen ab
(`restic_<version>_windows_amd64.exe`), und der Alias in `WinGet\Links`
fehlte am 2026-08-31. `winget install restic.restic --force` legt ihn neu
an; sonst hilft eine Funktion im PowerShell-Profil, die auf die Exe zeigt.

Das Passwort kommt aus `RESTIC_PASSWORD_COMMAND` (Windows Credential
Manager, `tools/mosaic_backup_credential.ps1`) und gilt fuer
Handaufrufe genauso -- restic liest die Variable selbst.

## Drei Snapshot-Familien, drei Pfade

Beim Import wurden zwei Altquellen uebernommen, dazu kommt der Tageslauf.
Sie unterscheiden sich im gespeicherten PFAD, darum tragen sie Marken:

| Marke | Pfad im Snapshot | Inhalt |
|---|---|---|
| `daily` | `<Projektordner>` | Arbeitsbaum, je Tageslauf |
| `legacy-mirror` | `<Sicherungswurzel>\mirror` | Altbestand, **inkl. im Arbeitsbaum geloeschter Dateien** |
| `models-snapshot` | Arbeitsverzeichnis des Imports | `models/`-Stand je Zip-Datum |

**`latest` ist dadurch mehrdeutig.** Es waehlt den juengsten Snapshot ueber
alle Familien -- ohne Filter erwischt man womoeglich einen
models-Snapshot statt des Arbeitsbaums. Immer `--tag daily` mitgeben oder
eine Snapshot-ID nennen.

Fuer die Deduplizierung sind die verschiedenen Pfade ohne Bedeutung: restic
adressiert Bloecke ueber ihren Inhalt, nicht ueber ihren Ort. Sie sind nur
fuer das Wiederfinden relevant.

## Die vier Handgriffe

**1. Wo steckt die Datei ueberhaupt?**

```
restic find --tag daily "arena_trends.csv"
```

Nimmt auch Muster (`"alphazero_v22-b05*"`) und einen Zeitraum
(`--oldest` / `--newest`).

**2. Was war an dem Tag drin?**

```
restic snapshots
restic ls --long <snapshot-id> "<Projektordner>\evaluations"
```

Aus der Ausgabe die EXAKTE Schreibweise des Pfades entnehmen und fuer die
naechsten Schritte kopieren -- restic hat ihn so gespeichert, wie er beim
Sichern aussah.

**3. Eine einzelne Datei ansehen, ohne etwas anzufassen**

```
restic dump <snapshot-id> "<Projektordner>\evaluations\STATUS.md" > STATUS_alt.md
```

Ein ganzer Ordner geht als Archiv: `restic dump -a zip <snapshot-id>
"<ordner>" > alt.zip`.

**4. Ordner wiederherstellen**

```
restic restore <snapshot-id> --target <leeres-Zielverzeichnis> --include "<Projektordner>\models"
```

Vorher trocken ansehen, was kaeme:

```
restic restore <snapshot-id> --target <leeres-Zielverzeichnis> --dry-run --verbose=2
```

`--include` und `--exclude` schliessen sich gegenseitig aus. Bei langen
Pfaden hilft die Unterordner-Schreibweise
`<snapshot-id>:<pfad>` -- dann sind `--include`-Angaben relativ dazu.

## Die eine Regel, die zaehlt

**Immer in ein NEUES, LEERES Zielverzeichnis wiederherstellen, nie ueber den
Arbeitsbaum.** Danach von Hand zurueckkopieren, was wirklich gebraucht wird.

Herkunft: am 2026-07-29 hat ein pauschales `git checkout -- evaluations/`
zwar die 42 verschwundenen Dateien zurueckgeholt, dabei aber zwei legitim
geaenderte, uncommittete Dateien mitgerissen (`elo_history.csv`,
`arena_trends.csv`); zwei Elo-Kanten und zwei Trendzeilen mussten
rekonstruiert werden. Ein Restore ins Live-Verzeichnis macht denselben
Fehler, nur gruendlicher: es kennt den Unterschied zwischen "fehlt" und
"wurde seitdem geaendert" nicht.

## Kein `restic mount` unter Windows

Die naheliegende Erwartung -- das Repository als Laufwerk durchblaettern --
geht nicht. Die Einbindung laeuft ueber FUSE und ist laut Doku auf Linux,
macOS und FreeBSD beschraenkt. Es bleibt bei `find`, `ls`, `dump`,
`restore`.

## Betrieb

`tools/mosaic_backup.ps1` ist der Tageslauf. Schalter:

- `-Prune` -- fuehrt `forget` mit der Aufbewahrungsrichtlinie aus und gibt
  Platz frei. **LOESCHT Snapshots.** Ohne den Schalter wird nichts entfernt,
  und das ist die richtige Vorgabe: Anlass der Einrichtung war ein
  Datenverlust, kein Platzmangel.
- `-CheckData` -- Tiefenpruefung (`check --read-data`), liest das ganze
  Repository. Gelegentlich, nicht taeglich.
- `-NoVss` -- ohne Volume Shadow Copy. Sonst nutzt der Lauf VSS, sofern er
  erhoeht laeuft; nur so kommen Dateien mit, die ein Training oder ein
  Messlauf offen haelt.
- `-DryRun` -- zeigt, was gesichert wuerde. Nach jeder Aenderung an der
  Ausschlussliste.

`tools/mosaic_backup_seed.ps1` war der einmalige Import und wird im
Normalbetrieb nicht mehr gebraucht.

**Der Lauf erzeugt I/O-Last ueber den ganzen Projektordner** und faellt
damit unter die Regel "Messungen laufen EXKLUSIV" (`../CLAUDE.md`): nicht
parallel zu einer Arena, einem Self-Play oder einer Sonde.

## Fallen, die schon zugeschlagen haben (alle 2026-08-31)

- **`setx` wirkt nicht in der laufenden Shell.** Es schreibt in die
  Registry; bereits laufende Prozesse erben die alte Umgebung. Ein Lauf
  brach mit "Kein Repository-Passwort gesetzt" ab, obwohl
  `RESTIC_PASSWORD_COMMAND` korrekt in `HKCU\Environment` stand. Behoben:
  `Sync-EnvFromRegistry` in `tools/backup_common.ps1` holt die Variablen in
  den Prozess. Fuer HANDaufrufe gilt die Falle weiter -- nach einem `setx`
  eine neue Shell oeffnen.
- **restic frisst unquotierte Backslashes in `RESTIC_PASSWORD_COMMAND`.**
  Es zerlegt den Befehl selbst, ohne Shell, und behandelt `\` als
  Escape-Zeichen: aus `-File D:\Pfad\x.ps1` wird `-File "D:"`, restic bricht
  mit "Resolving password failed" ab. Durchgemessen: unquotiert scheitert;
  einfach quotiert, doppelt quotiert und mit Schraegstrichen funktioniert
  es. **Den Skriptpfad in einfache Anfuehrungszeichen setzen.**
- **PowerShell macht aus nativem stderr eine Ausnahme.** Leitet man die
  Fehlerausgabe eines nativen Programms mit `2>&1` in den Erfolgsstrom um,
  verpackt PowerShell jede Zeile in einen ErrorRecord -- unter
  `$ErrorActionPreference = "Stop"` terminierend. Ausgerechnet die
  ERWARTETE Antwort "repository does not exist" hat so den Lauf beendet,
  der das Repository gerade anlegen wollte. `Invoke-ResticCapture` kapselt
  das; `2>$null` ist davon NICHT betroffen (gemessen).
- **DPAPI-Grenze bei geplanten Aufgaben.** Der Credential Manager gibt das
  Passwort nur in einer Sitzung mit geladenen Benutzerschluesseln heraus.
  "Nur ausfuehren, wenn der Benutzer angemeldet ist" und eine Aufgabe mit
  hinterlegtem Kennwort erfuellen das; **"Nicht gespeichertes Kennwort
  verwenden" (S4U) nicht** -- dort schlaegt das Auslesen fehl, auch wenn es
  interaktiv einwandfrei laeuft. In dem Fall ist `RESTIC_PASSWORD_FILE` der
  richtige Weg.

## Wenn das Passwort weg ist

Dann ist das Repository weg. restic hat keine Hintertuer. Der Eintrag im
Credential Manager haengt an Konto und Maschine; Profilschaden oder
Neuinstallation reichen. Deshalb gehoert eine Kopie des Passworts an einen
Ort ausserhalb dieses Rechners.

## Verweise

- `../CLAUDE.md` -- stehende Regeln (Exklusivitaet von Messungen, keine
  Rechnerstruktur in neuen Dateien).
- `pitfalls.md` -- Vorfaelle des Projekts allgemein, u. a. das
  Verschwinden getrackter Dateien am 2026-07-29.
- `tools/backup_excludes.txt` -- die Ausschlussliste mit Begruendungen.
