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

- **FOKUS-REGEL: gemessen wird auf k1** (vertikale Reihen, 7 Punkte je Spalte).
  Andere Kriterien nur, wenn ein Zuschnitt sie ausdruecklich braucht -- dann
  mit Begruendung. Nutzer-Entscheid 2026-08-18.
- **Prozessweite Knoepfe: KEIN Spiegelmatch.** Wer einen prozessglobalen Knopf
  misst, faehrt je Arm einen EIGENEN Prozess. Ein Spiegelmatch im selben
  Prozess gibt beiden Seiten dieselbe Knopfstellung und misst nichts.
- **Aus "Eingriff X in Richtung Y verliert" folgt NICHT "Y ist falsch"** --
  nur, dass X in diesem Zustand verliert. Es fehlt die Kontrollgruppe: ein
  Agent, der Y KANN. (Herkunft: STATUS-Strukturbefunde, Stand 2026-08-30.)

### Auslastung: GPU und CPU duerfen parallel laufen (Nutzer-Entscheid 2026-08-31)

Nutzer: *"ich will eine auslastung von gpu und cpu und nicht alles seriell
fahren."* Das praezisiert die Exklusivitaets-Regel aus `CLAUDE.md`
("Messungen laufen EXKLUSIV"), es hebt sie nicht auf.

**Was parallel darf:** ein Training auf der GPU und EIN CPU-Auftrag daneben
(Arena, Sonde, Relabeling, Cache-Bau). Die Ressourcen sind verschieden, und
die Sorge der Ursprungsregel -- verstuemmelte Partien -- ist fuer unsere
Arenen gemessen ausgeraeumt: am 2026-08-29 war der lastgebremste Erstlauf
PARTIEGLEICH mit dem sauberen Neustart (nur die `game_id`-Zeitstempel
differierten). Last bremst, sie verfaelscht nicht, solange die Suche
sim-budgetiert und seed-getrieben ist -- und das ist sie ueberall im Baum
(es gibt kein Zeitbudget in der Suche).

**Was weiter EXKLUSIV bleibt:** zwei CPU-Messungen gegeneinander. Ein
Self-Play neben einer Arena, zwei Arenen nebeneinander, eine Sonde neben
einem Self-Play -- das teilt dieselbe Ressource und macht beide Laufzeiten
wertlos, ohne dass ein zweiter Kern frei wuerde.

**Thread-Budget (12 Kerne).** Ein Training zieht rund 6 Kerne fuer die
DataLoader-Worker. Der CPU-Auftrag daneben bekommt deshalb **hoechstens 5
Threads** -- `paired_gating.py` steht per Default auf 10 und muss
heruntergesetzt werden, sonst buchen sich beide gegenseitig ueber.

**Pflicht dabei:** der `laufzeit`-Block eines unter Nebenlast gefahrenen
Laufs ist KEINE Planungsgroesse und wird im Artefakt als *unter Nebenlast*
markiert. Sonst wandern gebremste Zahlen in `measured_runtimes.md` und die
naechste Sitzung plant falsch. Die Gegenprobe bei Zweifeln ist billig: einen
Lauf auf der ruhigen Maschine wiederholen und auf Partiegleichheit pruefen.

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

- **Zwei gleichzeitige Aenderungen brauchen den Kontrollarm auf der
  UNVERAENDERTEN Achse.** Praezedenz: Ownership-Kopf einschalten plus
  Korpuswechsel -- ohne den w0-Kontrollarm auf DEMSELBEN Korpus sind Kopf und
  Korpus konfundiert und der Effekt ist nicht zuordenbar. Das ist die eine
  Bedingung, die nicht wegfallen darf.
- **Solange die serielle Referenz fuer den vollen Cache fehlt (2,58 h), traegt
  der Cache KEINE Champion-Entscheidung.** Belegt ist Bit-Identitaet auf 120
  Dateien, nicht auf den 4,19 Mio Zustaenden.
- **`--cache-file` nutzt, wer `--val-frac 0` faehrt** oder ein exakt passendes
  Fenster baut: der Voll-Cache passt per Design nicht auf Laeufe mit Val-Split
  (anderer Fenster-Schluessel, der Waechter lehnt korrekt ab).
- **B1-Vorgabe fuer jeden Nachfolge-Arm**: wer die Initiierung langer Reihen
  hebt, ohne die Vollendungsquote deutlich ueber 0,53 zu bringen, wiederholt
  B1.
- **Kuenftige Einfrierungen legen die `.pth` mit ab** -- als `model.pth` IM
  Artefakt, unversioniert (die globale `*.pth`-Ignore-Regel greift, Schutz ist
  der Backup-Ordner). Die ONNX bleibt getrackt (Byte-Beweisstueck; ein
  Re-Export aus der `.pth` ist nicht byte-stabil). Schwesterregel zu "Ein Wheel
  liegt IM Artefakt" oben.

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

## Geschlossene Wege (nicht neu vorschlagen)

**Kanonischer Ort seit 2026-08-30** (aus STATUS.md herausgeloest -- eine
Verbotsliste im Dokument, das regelmaessig geleert wird, ist die teuerste
Verlustklasse: verschwindet sie, wird der geschlossene Weg noch einmal
gemessen).

- Q-Skalierungs-Option
- jeder Suchparadigmen-Wechsel (zwei externe Recherchen)
- Mehrfach-Determinisierung (`PREREG_ismcts_determinizations.md`: k=4 faellt
  unter zwei Anordnungen signifikant ab)
- Phasenfaktor, Vollendbarkeits-Relaxation im Routing und die zwei
  Punktekarten (`PREREG_heuristic_v2_long_rows.md` par.11-16)
- `PREREG_long_row_payoff.md` B1
- `PREREG_bootstrap_horizon.md` (beide Arme)
- **v2 weiterentwickeln** -- Nutzer-Entscheid 2026-08-26: "v2 ist durch". Es
  ist eingefroren, weil es fertig ist.

## Arbeitskonventionen

- **Der Leitstern ist der Priorisierungstest.** Ziel ist ein staerkerer
  Spieler, gemessen am direkten Duell; der benannte Hebel ist der
  Plattenblick (rund 10 Punkte je Partie bleiben liegen). Bei jeder
  Priorisierung gilt die Frage: was traegt das dazu bei?
- **Registrierpflicht vor jedem Bau.** Was auf der Parkliste steht, wird vor
  dem Bau vorregistriert, nicht danach.
- **Zahlen gehoeren in die Registrierung, nicht ins Werkzeug.** Korpus- und
  Fensterwerkzeuge bekommen Parameter, keine hartkodierten Groessen; der
  konkrete Aufruf wird bei der Kampagne registriert.
- **Vor der Sanierung eines EINGEFRORENEN Artefakts klaeren, ob das
  verify-Tooling die Datei hasht** (Praezedenz: golden_probe-Manifest-Sanierung
  25a632f). Sonst bricht die Abnahme des Artefakts an der eigenen Reparatur.
- **Agenten-Kapselung: je Knopf ein Commit mit Paritaets-Gate.**
- **Messartefakte liegen ungetrackt in `evaluations/artifacts/`**
  (`.gitignore`). Folge: ein frischer Klon hat sie nicht, Preregs zitieren sie
  aber als Beleg. Deterministische Sonden sind wiederholbar (belegt: der
  Wiederholungslauf des Strafleisten-Tors war byte-identisch), alles mit
  Netz-Zufall nicht ohne Weiteres. Zurueckdrehen: `.gitignore`-Zeile entfernen
  und `git add -f evaluations/artifacts`.
- **Der Ahead-Stand wird im CHAT gemeldet, NICHT in STATUS gefuehrt** -- dort
  verrottet er sofort (Nutzer 2026-08-28).
