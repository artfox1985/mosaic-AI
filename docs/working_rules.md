# Geltende Regeln (kompakt)

**Kanonischer Ort seit 2026-08-28** (aus STATUS.md entflochten, Nutzer-Hinweis:
STATUS ist kein Langzeitgedaechtnis); Herkunft der Inhalte: STATUS-Stand
2026-08-28. Wer aendert, aendert HIER -- STATUS.md verweist nur noch.

Langform samt Herleitung: `../archive/history.md`, Kapitel "Vollstaendiger
STATUS-Stand vom 2026-08-25", Abschnitt "GELTENDE REGELN".

**Aufteilung, damit keine dritte Kopie entsteht:** Regeln, die bereits in
`../CLAUDE.md` stehen, sind hier nur EINZEILER mit Verweis -- der Wortlaut
gilt dort. Vollstaendig steht hier, was es nur in STATUS gab. Die
Vorfalls-Herkunft steht in `pitfalls.md`.

## Messen und Auswerten

- **Score-Auswertungen IMMER auf Block-Ebene.** Paar-SEs werden sonst massiv
  unterschaetzt, und Extrembloecke erzeugen Artefakte.
- **Aufloesung schlaegt Sparsamkeit.** Bei n=400 streut dieselbe Konfiguration
  um 5,75 Prozentpunkte; der Seed bewegt die Metrik 4- bis 6-mal staerker als
  jeder Knopf. Keine Spar-Schwelle auf ein blindes Mass bauen.
- **Value-Aenderungen brauchen Arena-Gating** -- es gibt keinen validierten
  Offline-Praediktor.
- **Sechs Standard-Kennzahlen in JEDEM Messbericht**: Reihen-, Spalten- und
  Strafleistenauslastung, Punkte je Wertungsplatte, eigene Punkte, Margin.
  Wortlaut und Werkzeugliste: `CLAUDE.md`, Abschnitt "Standard-Kennzahlen
  jedes Messberichts".
- **Laufzeit ins Artefakt**, nicht nur nach STATUS: `laufzeit`-Block mit
  `wanduhr_s`, `cpu_s`, `threads`, `s_je_partie`. Siehe `CLAUDE.md`,
  Abschnitt "Laufzeiten messen, nicht schaetzen"; Planungsgroessen in
  `measured_runtimes.md`.
- **Lange Laeufe nie in eine Pipe**, keine eigene Umleitung; Fortschritt mit
  `flush` sichtbar machen. Siehe `CLAUDE.md`, Abschnitt "Lange Laeufe NIE in
  eine Pipe".
- **Messungen laufen exklusiv**, ein Build ist Nebenlast. Siehe `CLAUDE.md`,
  gleichnamiger Abschnitt; Vorfall in `pitfalls.md`.
- **Vor der Auswertung das eigene Lauf-Manifest gegen das Referenz-Manifest
  halten** (`cli_args`). Ein fehlendes Flag meldet sich nicht, es ist ein
  Default. Vorfall in `pitfalls.md`.
- **Anker-Messungen laufen ueber `tools/anchor_arena.py`**, nicht ueber die
  In-Process-Heuristik. Seit B4b (`round5_anchor.rs` entfernt) bewegt eine
  Aenderung an `round5.rs` auch den Heuristik-Pfad; der Schutz liegt jetzt im
  Artefakt `models/frozen_heuristics/hv1_anchor`. Herleitung: STATUS,
  Abschnitt "NAECHSTE SCHRITTE / B".

## Training und Korpus

- **Fenster-Pinning: ZWEI Variablen**, nicht eine -- Trainings waehrend
  laufender Generierung immer pinnen (Split-Shift, Cache-Neubau,
  Kontamination).
- **Traeger-Status vor jeder Policy-Aussage pruefen.** Korpora sind per
  Default NICHT policy-traeger.
- **Backup- und Alt-Regel-Korpora kommen NIE wieder ins Training.**
- **Promotions-Checkliste: `promotion_checklist.md`.** Enthaelt u.a. 5b
  Anzeige-Kalibrierung (Platt-Refit je Champion, mit Verteilungs-Caveat) und
  5c sigma/Prior-Balance-Waechter (Kennzahl > 3 oeffnet die c_visit-Familie
  per Regel). **Nachschub bei Gating-Fehlschlag**: Langform im Archiv, hier
  nur der Merkposten, dass beides existiert und gilt.
- **Nie auf plattenblindes Normalspiel eichen.** Kalibrierung und Zielraten
  nicht gegen die Verteilung heutiger Netze, wenn genau deren Verhalten das
  Ziel ist.
- **Ein Wheel liegt IM Artefakt, das es ausfuehrt** (`frozen_heuristics/<name>/`
  oder `frozen_champions/<name>/`), kein Sammelordner. Nutzer-Entscheid
  2026-08-26, Herleitung: STATUS, Abschnitt "C2".
- **Einfrieren, sobald etwas Referenz WIRD** -- Ausloeser ist die
  Rollenuebernahme (Generator, Anker, Gegner), nicht "sieht fertig aus".

## Arbeitsweise

- **Loeschen nur mit expliziter, pfadgenauer Rueckfrage.** Eine Frage ist
  keine Anweisung.
- **Push nie ohne ausdrueckliche Anweisung.** Stand wird als "n Commits
  voraus" gemeldet.
- **Parallele Sitzungen: Spurdisziplin.** Fremde Straenge und Preregs nicht
  abarbeiten; `git add` pfadgenau statt verzeichnisweit (am 2026-08-25 sind
  drei fremde Dateien in einen Commit gerutscht). Staffelstab-Regel fuer
  Messungen: `CLAUDE.md`, Abschnitt "Messungen laufen EXKLUSIV".
- **Prereg-Kopf und Index**: wer ein Ergebnis registriert, zieht den
  Zeile-1-Kopf im selben Zug nach und laesst
  `python tools/generate_prereg_index.py` laufen. Gueltige Status:
  OFFEN / ENTSCHIEDEN / UEBERHOLT. Wortlaut: `CLAUDE.md`, Abschnitt
  "Prereg-Statuskopf und Index".
- **Heuristik-Anker-Parameterpaket: NICHT ANFASSEN** -- es definiert die
  Elo-Leiter.
- **Elo-Betrugsschutz (GUI)**: gewertete Spiele nur gegen verankerte Gegner.
- **Nahtbreite messen, nicht Zeilen zaehlen.** Vor jedem Schnitt auszaehlen,
  wieviele lokale Namen die geplante Naht ueberqueren; zweistellig = falsche
  Naht. Abschnitts-Banner markieren Anfaenge, keine Enden. Herleitung samt
  Messwerten: STATUS, Abschnitt "ARCHITEKTUR: B -> C -> A gefahren".
- **Geprueft oder markiert. Kein Drittes.** REGEL 0, Wortlaut in `CLAUDE.md`
  ganz oben.
