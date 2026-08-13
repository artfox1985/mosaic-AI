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

## Workflow-Präferenzen

- Bevor du große Refactorings durchführst, skizziere kurz den Plan (1-2 Sätze).
- Führe Änderungen schrittweise durch (Atomic CommitsEdits).
- Für Commits gilt: Kurzbeschreibung im Titel, dann in der Beschreibung das warum. Das was steckt im diff der Dateien.
- Wenn Unklarheiten bei den Spielregeln bestehen, frage kurz nach, anstatt Annahmen zu treffen.
- Schau in vorhandene scripts ob dort bereits relevante funktionen vorhanden sind bevor du was neues baust (zb arena.py war schon da, aber du hast dir selbst noch eine gebaut)
