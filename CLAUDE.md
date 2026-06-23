# Projekt-Richtlinien für Claude

## Token-Optimierung & Kommunikations-Regeln

- **Kein Boilerplate** Wiederhole niemals den gesamten Dateikontent. Gib nur den geänderten Funktionsblock oder die spezifischen Zeilen aus.
- **Diff-Format** Verwende bei komplexeren Änderungen ein prägnantes Format (z.B. In Datei X, ändere Zeile Y zu Z).
- **Direktes Schreiben** Wenn du eine Datei bearbeitest, schreibe die Änderung direkt in die Datei. Verzichte auf die Anzeige des vollständigen Codes im Chat.
- **Kontext-Fokus** Antworte direkt auf die Aufgabe. Erkläre nur kurz die Logik, wenn es für das Verständnis der Änderung notwendig ist.

## Entwicklungs-Standards (Brettspiel-Logik)

- **Modularität** Halte Spiellogik, KI-Entscheidungen und Spielzustand strikt getrennt.
- **Zustandsverwaltung** Änderungen am Spielbrett müssen immer validiert werden, bevor sie den Zustand aktualisieren.
- **Fehlerbehandlung** Implementiere defensive Programmierung für alle Benutzer- und KI-Eingaben.
- **KI-Gegner** Priorisiere Lesbarkeit und Wartbarkeit der Heuristiken gegenüber komplexen, schwer debugbaren Optimierungen.

## Workflow-Präferenzen

- Bevor du große Refactorings durchführst, skizziere kurz den Plan (1-2 Sätze).
- Führe Änderungen schrittweise durch (Atomic CommitsEdits).
- Wenn Unklarheiten bei den Spielregeln bestehen, frage kurz nach, anstatt Annahmen zu treffen.
