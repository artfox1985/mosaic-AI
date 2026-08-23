# Projekt-Richtlinien für Claude

## REGEL 0: Geprüft oder markiert. Kein Drittes. (Nutzer-Anweisung 2026-08-11)

Jede Sachaussage über Code, Regeln, Zahlen oder Messungen ist entweder

- **geprüft in dieser Sitzung**, mit genannter Prüfstelle (`datei:zeile`,
  Handbuch-Abschnitt, Log-Zeile), oder
- **ausdrücklich als ungeprüft / Annahme / Herleitung markiert.**

Eine unmarkierte Behauptung ist ein Regelbruch. Diese Regel entstand nach sieben
Flüchtigkeitsfehlern an einem Tag, die jeweils ein einziger Grep verhindert
hätte — einer davon hätte zu einer "Reparatur" am Elo-Anker geführt.

Die vier Auslöser, an denen es jedes Mal schiefging:

1. **Verhalten von Code**: erst lesen, dann sagen. Nicht aus dem Gedächtnis,
   nicht aus `STATUS.md`, nicht aus einer Vorregistrierung.
2. **Agenten-Befunde sind Behauptungen**, keine Fakten. Die tragende Zahl selbst
   nachprüfen, bevor sie weitergegeben oder verrechnet wird.
3. **Spielregeln**: in `docs/engine_manual.md` oder in den Code schauen, nie
   ableiten.
4. **Zahlen**: eine ungeprüfte Zahl geht in keine Rechnung. Eine Rechnung, die
   "ungefähr passt", ist kein Beleg, sondern ein Zufall.

Zusatz: **Plan und Zustand nie in derselben Zeitform** — "würde addieren" für
Geplantes, "addiert" nur für Gebautes-und-Aktives.

## Token-Optimierung & Kommunikations-Regeln

- **Kein Boilerplate** Wiederhole niemals den gesamten Dateikontent. Gib nur den geänderten Funktionsblock oder die spezifischen Zeilen aus.
- **Diff-Format** Verwende bei komplexeren Änderungen ein prägnantes Format (z.B. In Datei X, ändere Zeile Y zu Z).
- **Direktes Schreiben** Wenn du eine Datei bearbeitest, schreibe die Änderung direkt in die Datei. Verzichte auf die Anzeige des vollständigen Codes im Chat.
- **Kontext-Fokus** Antworte direkt auf die Aufgabe. Erkläre nur kurz die Logik, wenn es für das Verständnis der Änderung notwendig ist.

## Gedankenstrich-Regel (Nutzer-Anweisung 2026-08-21, gelockert am selben Tag)

- Der Geviertstrich (U+2014, "langer" Gedankenstrich) ist im CHAT
  weiterhin erlaubt, in DOKUMENTEN und Repo-Dateien (README, STATUS,
  Preregs, docs/, Kommentare) nicht mehr.
- Der Halbgeviertstrich (U+2013, "–") ist ueberall OK (Nutzer-Lockerung
  2026-08-21; so umgesetzt in docs/engine_manual.md).
- Ersatz fuer U+2014 je nach Kontext: Halbgeviertstrich, Komma,
  Doppelpunkt, Semikolon oder Klammern. Zahlenbereiche bekommen den
  einfachen Bindestrich (z.B. 10-273).
- Bestand wird bei Gelegenheit mit-migriert (README ist am 2026-08-21
  bereinigt), keine Grossaktion ueber alle Altdateien.

## Diagramm-Format: SVG (Nutzer-Anweisung 2026-08-21)

- Diagramme werden als **SVG** erstellt, nicht als PNG.
- PNG-Exporte stoesst der Nutzer bei Bedarf selbst an; nicht ungefragt
  mitgenerieren.

## Prereg-Statuskopf und Index (Nutzer-Anweisung 2026-08-23)

- Jede `evaluations/PREREG_*.md` traegt in Zeile 1 den parsebaren
  Status-Kopf (`<!-- STATUS: ... -->`); `evaluations/PREREG_INDEX.md`
  wird daraus GENERIERT (tools/generate_prereg_index.py). Der
  Tabellenteil des Index wird NIE von Hand editiert.
- **Wer ein Ergebnis oder Verdikt in einer Prereg registriert, zieht
  IM SELBEN ZUG den Zeile-1-Kopf nach** (gleiche Pflegeregel wie bei
  STATUS.md). Diese Regel entstand, nachdem ein Audit am 2026-08-23
  vier Preregs fand, deren Koepfe noch "OFFEN / nichts gebaut" sagten,
  waehrend der Dateikoerper laengst das registrierte Ergebnis trug.
- **Sobald sich ein Prereg-Kopf aendert: sofort
  `python tools/generate_prereg_index.py` laufen lassen** – nicht erst
  auf den pre-commit-Hook warten (der prueft nur, blockt aber erst
  beim Commit). Gilt auch fuer Agenten-Auftraege: die Regel gehoert in
  jeden Prompt, der Prereg-Registrierungen schreibt.

## Dateinamen-Konvention (Nutzer-Anweisung 2026-08-13)

- **Neue Dateien und Verzeichnisse werden IMMER englisch benannt** (Code,
  Tools, Docs, Preregs, Messprotokolle). Der Alt-Bestand deutscher Namen
  wird auf Englisch migriert.
- Die Sprachregel für INHALTE bleibt unberührt: README englisch; STATUS,
  Commits, Kommentare, Chat deutsch.

## Entwicklungs-Standards (Brettspiel-Logik)

- **Modularität** Halte Spiellogik, KI-Entscheidungen und Spielzustand strikt getrennt.
- **Zustandsverwaltung** Änderungen am Spielbrett müssen immer validiert werden, bevor sie den Zustand aktualisieren.
- **Fehlerbehandlung** Implementiere defensive Programmierung für alle Benutzer- und KI-Eingaben.
- **KI-Gegner** Priorisiere Lesbarkeit und Wartbarkeit der Heuristiken gegenüber komplexen, schwer debugbaren Optimierungen.

## Worktrees & git-crypt (Stolperfalle)

`git worktree add` scheitert in diesem Repo am git-crypt-Smudge-Filter
(git-crypt findet seinen Schlüssel unter `.git/worktrees/<name>/` nicht).
Workaround — Worktree mit umgangenem Filter anlegen:

```
git -c filter.git-crypt.smudge=cat -c filter.git-crypt.clean=cat -c filter.git-crypt.required=false worktree add <pfad> <branch>
```

Im Worktree enthält `player_profiles.json` dann Ciphertext — für Engine-/
Tool-Arbeit egal, aber die Datei dort NIE bearbeiten oder committen.

## STATUS.md ist das Übergabedokument (Nutzer-Entscheid 2026-08-17)

`evaluations/STATUS.md` ist die **einzige** Quelle für den aktuellen Stand —
kein Artifact, keine Kopie, keine zweite Ansicht. Der Grund ist gemessen und
nicht theoretisch: an einem einzigen Tag haben drei überholte, aber plausible
Quellen Zeit gekostet (ein Code-Kommentar statt der Primärquelle, ein
„GÜLTIG"-Etikett an einer Messung, deren Voraussetzung weggefallen war, und
eine Sonden-Skala, die zu 88 % im Trainingssatz lag).

**Pflege-Regel:** Wer einen Befund erzeugt, trägt ihn im selben Zug in
STATUS.md nach — und prüft dabei, ob ein *anderer* Abschnitt dadurch falsch
wird. Genau das ist zweimal passiert: oben stand noch „beide Wege negativ",
während weiter unten schon der Befund stand, der das widerlegt. Für einen
Menschen ein Schönheitsfehler, für die nächste Sitzung eine Falschaussage.

## Öffentliches Repo: keine Rechnerstruktur (Nutzer-Entscheid 2026-08-17)

Das Repo ist öffentlich. **Neue Dateien enthalten keine absoluten Pfade und
keinen Nutzernamen.** Wo ein maschinenabhängiger Pfad gebraucht wird, kommt er
aus der Umgebung, mit Ableitung als Fallback — Vorbilder im Baum:
`MOSAIC_PYTHON_DIR` (tools/hooks/pre-push, sonst aus `sys.executable`),
`MOSAIC_BACKUP_DIR` (tools/mosaic_backup.ps1, sonst `$env:OneDrive`),
`MOSAIC_MODELS_DIR` (engine/examples, sonst relativ zum Crate).

**Die Historie wird NICHT umgeschrieben.** Ältere Commits enthalten noch
Vorname und einen Python-Installationspfad; ein `filter-repo` plus Force-Push
würde jeden Klon invalidieren, und bei atomaren Commits müsste man gezielt
danach suchen. Nutzer-Abwägung: mehr Kosmetik als Nutzen. Nicht neu vorschlagen.

**Prüfbefehl** vor dem Pushen neuer Dateien:

```
git ls-files -z | xargs -0 grep -lIE "Patrick|OneDrive.(Documents|Backups)"
```

Beim Bereinigen solcher Pfade per Regex: eine Zeichenklasse braucht ZWEI
Backslashes vor dem Schrägstrich (`[\/]`). Mit einem escapt er den
Schrägstrich, trifft nur Vorwärtsschrägstriche und lässt jeden Windows-Pfad
still stehen — dieser Fehler ist am 2026-08-17 zweimal passiert.

## Workflow-Präferenzen

- Bevor du große Refactorings durchführst, skizziere kurz den Plan (1-2 Sätze).
- Führe Änderungen schrittweise durch (Atomic CommitsEdits).
- Für Commits gilt: Kurzbeschreibung im Titel, dann in der Beschreibung das warum. Das was steckt im diff der Dateien.
- Wenn Unklarheiten bei den Spielregeln bestehen, frage kurz nach, anstatt Annahmen zu treffen.
- Schau in vorhandene scripts ob dort bereits relevante funktionen vorhanden sind bevor du was neues baust (zb arena.py war schon da, aber du hast dir selbst noch eine gebaut)
