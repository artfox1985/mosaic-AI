---
name: mosaic-handover
description: Eine laufende Sitzung an eine NEUE, eigenstaendige Sitzung uebergeben (Kontextfenster fast voll, Nachtprogramm laeuft weiter, Schichtwechsel). Nutze das, wenn der Nutzer "neue Sitzung", "Uebergabe" oder "Schichtwechsel" sagt oder wenn das eigene Kontextfenster zur Neige geht, waehrend Hintergrundlaeufe noch offen sind. Deckt ab - was VOR der Uebergabe in den Baum muss, wie STATUS Abschnitt 1 als Uebergabe gebaut wird, welcher Mechanismus eine echte neue Sitzung oeffnet (Arbeitsauftrag-Chip, NICHT Subagent), was die alte Sitzung danach noch darf.
---

# Uebergabe an eine neue Sitzung

**Warum ueberhaupt.** Eine neue Sitzung hat NICHTS von dieser: keinen Chat,
kein Scratchpad, keine Hintergrundaufgaben, keine laufenden Wecker. Alles,
was sie braucht, muss im Repo stehen oder in ihrer ersten Nachricht. Am
2026-09-03 ist die Uebergabe zweimal falsch angesetzt worden, bevor sie
sass; die Lehren daraus sind dieser Skill.

**Nutzer-Vorgabe 2026-09-03:** *"du sollst keinen sub agent eroeffnen,
sondern eine neue sitzung. aehnlich wie wenn du einen arbeitsauftrag
triggerst in einem neuen worktree."*

## Der Mechanismus: Arbeitsauftrag-Chip, nicht Subagent

| Mittel | Ergebnis | Taugt? |
| --- | --- | --- |
| `spawn_task` (Chip "Arbeitsauftrag") | echte neue Sitzung, eigener Kontext, eigene Hintergrundaufgaben; der Nutzer startet sie per Klick | **JA, das ist der Weg** |
| `Agent` (Subagent, auch im Hintergrund) | Kind DIESER Sitzung; Berechtigungen, Meldungen und Lebensdauer haengen an ihr | NEIN (am 2026-09-03 gestartet und auf Nutzer-Anweisung gestoppt) |
| `send_message` an eine Peer-Sitzung | erreicht nur eine schon LAUFENDE Sitzung | nur, wenn eine lebt (`ListAgents` zeigt es) |
| Geplante Aufgabe (`create_scheduled_task`) | unbeaufsichtigte Sitzung, keine Nachrichten hinein, Berechtigungen unklar | nicht fuer Laeufe ueber Stunden |

**`cwd` ist der Projektordner, kein Worktree.** `data/`, `models/`, das
installierte Wheel und die Cache-Bloecke liegen nur im Hauptbaum, und
`git worktree add` scheitert hier am git-crypt-Filter (CLAUDE.md "Worktrees &
git-crypt"). Der Chip bietet trotzdem einen Worktree an; die erste Nachricht
sagt deshalb ausdruecklich, dass im Projektordner gearbeitet wird.

## Ablauf

1. **Zustand aufnehmen, nicht aus dem Gedaechtnis.** Hintergrundlaeufe mit
   Stand ZAEHLEN (Dateien im Zielordner, Artefakt vorhanden ja/nein), `git
   status`, `git log -1`, Zahl ungepushter Commits (`git rev-list --count
   origin/main..HEAD`). Diese Zahlen kommen in STATUS und in die erste
   Nachricht.
2. **Sitzungsgebundenes in den Baum.** Alles, was im Scratchpad liegt und
   die naechste Sitzung braucht (Kettenskripte, Auswerteskripte), wandert
   nach `tools/` bzw. `evaluations/` -- OHNE absolute Pfade und Nutzernamen
   (`cd "$(dirname "$0")/.."`, Zwischendateien nach `evaluations/artifacts`).
   Pruefen mit dem Pruefbefehl aus CLAUDE.md "Oeffentliches Repo: keine
   Rechnerstruktur" (muss die neue Datei NICHT listen). Das Scratchpad der
   alten Sitzung ist fuer die neue unerreichbar.
3. **STATUS Abschnitt 1 zur Uebergabe umschreiben** (es ist das EINZIGE
   Uebergabedokument, CLAUDE.md). Aufbau:
   * Kopfzeile mit Datum, Uhrzeit und Anlass.
   * "LAEUFT": jeder offene Hintergrundlauf mit Werkzeug, Start, Stand,
     erwartetem Ende, Zielordner, Artefaktpfad, und was er noch LIEST
     (damit niemand einen Quellordner unter ihm wegzieht).
   * "ERSTE AUFGABE DER NEUEN SITZUNG": nummerierte Punkte in Reihenfolge,
     je Punkt Bauvorlage (Prereg und Absatz), Befehl oder Skript, erwartete
     Kosten, Abnahmekriterium. Was auf einen laufenden Prozess wartet,
     bekommt einen WATCHER-Auftrag (Bedingung ausformuliert: Dateizahl UND
     Artefakt; Stillstandsmeldung).
   * Nutzer-Freigaben und Verbote WOERTLICH (was selbststaendig laufen
     darf, was nur auf Anweisung; kein Push; was geloescht werden darf).
   * Offene Nutzer-Entscheide mit Fundstelle.
   * Uebergabe BERICHTET, delegiert nicht: der eigene laufende Lauf gehoert
     unter "laeuft", nicht unter "zu tun".
4. **Chronik-Eintrag** in der laufenden `night_run_*.md` (Zeitpunkt,
   Anlass, was seit dem letzten Eintrag registriert wurde).
5. **Committen** (nicht pushen). Der Baum muss sauber sein, bevor die neue
   Sitzung startet -- zwei Sitzungen auf einem schmutzigen Baum sind die
   sicherste Art, einen Commit zu verlieren.
6. **Eigene Wecker und Monitore stoppen** (`ScheduleWakeup stop`,
   `TaskStop` fuer Monitore). Sonst ziehen zwei Sitzungen an derselben Kette.
   Hintergrund-LAEUFE (Relabel, Training) laufen weiter; sie gehoeren dem
   Betriebssystem, nicht der Sitzung.
7. **Chip setzen** (`spawn_task`): `cwd` = Projektordner; `title` als
   Imperativ; `prompt` VOLLSTAENDIG selbsttragend, weil die neue Sitzung
   nichts anderes hat: zuerst-lesen-Liste (CLAUDE.md, STATUS Abschnitt 1,
   Chronik), Freigaben und Verbote, die nummerierten Schritte mit
   Fundstellen, Meldewege (Nutzer im Chat informieren, wenn X durch ist),
   Verhalten bei Blockaden (anhalten, sichern, fragen; Anker ROT ist
   Nutzer-Entscheid), offene Nutzer-Entscheide.
8. **Dem Nutzer melden**: Chip liegt bereit, Worktree-Hinweis, was die
   Uebergabe enthaelt, Stand der Laeufe, offene Entscheide.

## Danach: die alte Sitzung fasst nichts mehr an

Sobald der Nutzer den Chip gestartet hat, arbeiten zwei Sitzungen auf einem
Baum. Die alte Sitzung schreibt keine Datei mehr, committet nicht, startet
keine Laeufe und bearbeitet keine Punkte der Uebergabe -- auch nicht, wenn
eine Hintergrund-Benachrichtigung sie weckt. Sie darf lesen, antworten und
auf Anweisung Dinge tun, die den Baum nicht beruehren (Spurdisziplin,
`docs/working_rules.md`; Staffelstab in CLAUDE.md "Messungen laufen
EXKLUSIV"). Wer ausnahmsweise doch schreiben soll, sagt es der anderen
Sitzung vorher an.

## Pruefliste vor dem Chip

- [ ] Stand der Laeufe gezaehlt, nicht geschaetzt
- [ ] Nichts Notwendiges liegt mehr nur im Scratchpad
- [ ] Neue Repo-Dateien ohne Rechnerpfade (Pruefbefehl aus CLAUDE.md, Abschnitt "Oeffentliches Repo")
- [ ] STATUS Abschnitt 1 traegt Laeuft / Reihenfolge / Freigaben / Verbote / offene Entscheide
- [ ] Baum sauber, committet, nicht gepusht; Ahead-Stand gemeldet
- [ ] Eigene Wecker und Monitore gestoppt
- [ ] Chip-Prompt selbsttragend, `cwd` = Projektordner
