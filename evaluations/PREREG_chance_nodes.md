# Vorregistrierung: Wahrscheinlichkeiten statt Welten (Zufallsknoten)

**Angelegt 2026-08-09, VOR jeder Implementierung.** Nutzer-Frage: *"die
frage ist ob wir nicht mit wahrscheinlichkeiten rechnen sollten anstatt
mit welten"*, plus Nutzer-Auftrag, den Befund zum bekannten
Stapel-Unterbau hier anzuhaengen.

## Die strukturelle Grundlage (verifiziert, nicht angenommen)

**Es gibt keine private Information.** Alle Spielerfelder im Zustand sind
oeffentlich (`dome_grid`, `pattern_lines`, `floor`, `bonus_chips`,
`unused_chip_colors`, `score`, ...), und das Verdeckte steht als
**aggregierte Zaehler**: `bag_colors`, `bag_count`, `tower_colors`,
`dome_pool_mask`, `dome_wild_remaining_frac`. Symmetrisch fuer beide
Spieler.

**Folge: das ist kein Spiel mit imperfekter Information, sondern ein
Spiel mit perfekter Information und ZUFALLSKNOTEN** -- Backgammon, nicht
Poker. Determinisierung und ISMCTS sind Techniken fuer
Informationsmengen, also fuer privates Wissen. Wir haben Werkzeug aus der
falschen Familie gemessen.

Das erklaert die Befundlage in einem Zug:
- k=1/2/4 dreimal H0 -- mehr Stichproben einer Determinisierung loesen
  ein Problem, das nicht existiert.
- `SHUFFLE_STACK_PEEK_IN_SEARCH` war **schaedlich** -- Stichprobenrauschen
  in einen Zufallsknoten statt des Erwartungswerts.
- `ROUND_TRANSITION_SAMPLING` ist die einzige Zufallsknoten-Behandlung im
  Haus und fuer die Suche nie eingeschaltet worden.
- Auf der BEWERTUNGSSEITE rechnen wir schon mit Wahrscheinlichkeiten: die
  Merkmale kodieren das Verdeckte als Zaehler, deshalb war der
  Seed-Rauschboden der Forward-Pass-Groessen strukturell exakt Null.
  Nur die DYNAMIK im Baum determinisiert noch.

---
## TEIL A (Korrektheit, zuerst): der bekannte Unterbau darf nicht gemischt werden

### Befund

`determinize_hidden_information` mischt `state.dome_tile_pool`
vollstaendig. Fuer den UNBEKANNTEN Teil ist das richtig und notwendig:
die Engine haelt die echte Anfangsmischung im Speicher, ohne Neumischen
rechnete die Suche mit **Orakelwissen**. Der Regler erfuellt dort seinen
Zweck.

**Der Defekt ist schmaler**: nach der Nutzer-Regel vom 2026-08-09 sind die
zurueckgelegten Platten UND ihre Reihenfolge oeffentlich (sie gehen
`push`-seitig unter den Stapel, vom Nutzer bestaetigt). Dieser Abschnitt
ist damit BEKANNT -- und wird mitgemischt. Die Suche wirft legitimes
Wissen weg.

### Warum es nicht vernachlaessigbar ist (gemessen)

Der Stapel wird bis Runde 4 **vollstaendig** abgetragen
(frozen_v2, `dome_stack_count`):

| Runde | Median Rest | Max | Anteil <=3 |
|---|---|---|---|
| 1 | 13,0 | 15 | 0% |
| 2 | 8,0 | 9 | 0% |
| 3 | 4,0 | 5 | 12,5% |
| 4 | **0,0** | 1 | 100% |
| 5 | 0,0 | 0 | 100% |

Alles, was in Runde 1-3 nach unten wandert, wird also noch gezogen. Meine
erste Einschaetzung ("taucht in derselben Partie kaum wieder auf") war
falsch, der Nutzer hat korrigiert.

**Entscheidungsrelevanz**: das Netz kennt via `dome_pool_mask` die
IDENTITAETSMENGE, also WAS kommt -- nur nicht WANN. Bei einem Zug, der
1 Punkt kostet, haengt der Wert genau daran: kommt die gewuenschte Platte
als naechste oder erst in drei Ziehungen?

### A1 -- engine-intern, KEIN Vertragsbruch

Zurueckgelegte Platten markieren und beim Determinisieren nur den
unbekannten Abschnitt mischen. Bedingungen:
- Der Encoder bleibt unangetastet (`INPUT_SIZE` unveraendert) -- das Netz
  bekommt die Information NICHT, es geht allein um die Such-Dynamik.
- **Das aendert das Suchverhalten und damit den Paritaets-Hash.** Das ist
  der erste ABSICHTLICHE Bruch seit dem Bau der Golden-Waechter: die
  Referenz wird bewusst neu gelegt und der Grund im Fixture-Kopf
  dokumentiert, damit niemand ihn spaeter "zurueckreparieren" will.
- Arena-Pruefung nach Standardmuster (Knopf mit Default AUS, damit das
  Alt-Verhalten bit-identisch verfuegbar bleibt; gepaart, 2x400).

**Entscheidungsregel A1**: die Korrektur bleibt auch bei H0, wenn kein
SCHADEN nachweisbar ist -- stehende Nutzer-Regel "Korrektheit vor
gemessenem Nutzen". Nur ein signifikanter Schaden, den Rauschen nicht
erklaert, fuehrt zur Ruecknahme.

### A2 -- die Reihenfolge dem NETZ geben: zurueckgestellt

Waere ein Encoder-Eingriff (`INPUT_SIZE`), also ein Vertragsbruch mit
allem, was `DESIGN_conventions_as_checks.md` dafuer verlangt
(FeatureVersion, Manifest, Anker-Neumessung). Nicht Teil dieses Tasks.

---
## TEIL B: Zufallsknoten statt Stichwelt

### Aufzaehlbar vs nicht aufzaehlbar

| Zufallspunkt | Verteilung | Behandlung |
|---|---|---|
| Kuppelstapel-Zug (`dome_stack_peek`) | aus `dome_pool_mask` exakt bekannt, wenige Typen | **aufzaehlbar** -> echter Zufallsknoten mit gewichteter Rueckgabe |
| Chip-Aufdeckung | Identitaet aus dem Restpool, wenige Moeglichkeiten | **aufzaehlbar** |
| Fabrik-Neubefuellung | Multimengen aus dem Beutel | **nicht** aufzaehlbar -> bleibt beim TD-Bootstrap (Korpus-Mittelung) |

Reichweite ist gemessen: der Zieh-Zug ist in **45,4%** der
Netz-Entscheidungen legal, die Chip-Aufdeckung im Median **2 Fliesen**
entfernt. Beide Punkte sind also haeufig, nicht exotisch.

### B1 (GATE): Kosten zuerst

Ein Zufallsknoten mit n Kindern streckt das feste Sim-Budget an genau
diesen Stellen. Zu messen VOR jeder Implementierung: die tatsaechliche
Verzweigung n an Zieh- und Aufdeckungsknoten (aus `dome_pool_mask` bzw.
Chip-Restpool auf dem frozen-Set auszaehlbar, kein Arena-Budget), und
daraus der erwartete Sim-Verbrauch.
- **n im Median <= 3** ⇒ B2 wird gefahren.
- **n im Median > 3** ⇒ zurueckgestellt; ein Knoten, der das Budget
  vervierfacht, konkurriert mit der Tiefe, und Breite-gegen-Tiefe ist bei
  uns dreimal H0 gewesen (m-Formel, 16-vs-8, k-Split).

### B2: nur der Kuppelstapel-Zug, nicht beides

Erst der Zieh-Zug (groessere Reichweite, triviale Verteilung). Die
Chip-Aufdeckung waere ein zweiter Schritt -- zwei Aenderungen gleichzeitig
machen die Attribution unmoeglich.

**Entscheidungsregel B2**: Arena gepaart 2x400, Knopf mit Default AUS.
Anders als bei A1 ist das KEINE Korrektheitskorrektur, sondern eine
Genauigkeitsverbesserung -- hier gilt die normale Latte (signifikanter
Gewinn oder H0 ⇒ nicht uebernehmen).

## TEIL C (Diagnose, billig): nutzt die KI die Platte-6-Interaktion?

Nutzer-Spielerfahrung 2026-08-09: *"meiner spieler erfahrung nach kommt
das ziehen vom stapel insbesondere bei der wertungsplatte -3 spezialfeld
zum tragen. da kauf ich gerne -1 punkt fuer jokerplatten."*

Mechanik dahinter: Platte 6 bestraft leere Spezialfelder; ein Spezialfeld
wird erst frei, wenn die anderen drei Felder seiner Kuppelplatte gefuellt
sind. Jokerplatten helfen beim Fuellen, also erhoeht eine aktive Platte 6
den Wert des Ziehens -- und rechtfertigt den Punkt Kaufpreis.

**Das Netz hat die noetigen Merkmale**: `dome_stack_top_type` (Rueckseite
der obersten Platte: Special oder Wild) und `dome_wild_remaining_frac`
(Wild-Anteil des Rests), dazu die aktiven Platten als One-hot. Ob es die
Interaktion GELERNT hat, ist nie geprueft worden.

**Messung ohne neues Instrument**: in den Sockel-Self-Play-Records
(Policy aktiv, nicht maskiert) den Anteil der Policy-Masse auf der
`dome_stack_peek`-Aktion auszaehlen -- getrennt danach, ob Kriterium 6 in
`scoring_tile_ids` steht. Nur Zustaende zaehlen, in denen Ziehen legal ist.

- **Ziehquote mit Platte 6 deutlich hoeher** ⇒ die Interaktion ist
  gelernt, die Nutzer-Beobachtung ist im Netz abgebildet, und die
  Plattenschwaeche liegt woanders.
- **Kein Unterschied** ⇒ die KI ignoriert eine Interaktion, die ein
  menschlicher Spieler aktiv ausnutzt. Das ist ein eigenstaendiger
  Befund und ein starkes Argument fuer den Plattenkopf
  (`PREREG_plate_head.md`), weil es zeigt, dass die Platten-Information
  vorhanden ist, aber nicht handlungsleitend wird.

Deskriptiv mitzufuehren: dieselbe Auszaehlung fuer Platte 3
(Mehrfarbige Felder) als Kontrolle -- sie ist die Ausschluss-Partnerin von
Platte 6 und sollte den Effekt NICHT zeigen.

## Reihenfolge

C (Diagnose, Minuten, keine Maschine) -> A1 (Korrektheit, klein) -> B1
(Kostengate, offline, billig) -> B2 nur bei bestandenem Gate. Alles nach dem laufenden Gewichts-Sweep und dem
Plattenkopf, weil beide bereits eingetaktet sind und Engine-Aenderungen
ein freies Fenster fuer Wheel-Installation brauchen.

---
### ERGEBNIS Teil C (2026-08-09): die Interaktion IST gelernt, spezifisch fuer Platte 6

10 Sockel-Dateien `selfplay_v20wdl_*` (Policy aktiv), 4.581 Zustaende mit
legalem Zieh-Zug. Kennzahl: Anteil der Policy-Masse auf
`dome_stack_peek`.

| Aktive Platte | n akt | Mittel akt | >50% akt | Mittel inakt | >50% inakt | Diff |
|---|---|---|---|---|---|---|
| **6 Spezialfelder -3** | 2.057 | **0,2158** | **21,5%** | 0,1364 | 13,2% | **+0,0794** |
| 2 Diagonalen | 1.644 | 0,1881 | 18,4% | 0,1631 | 16,1% | +0,0250 |
| 4 Aeussere Felder | 1.865 | 0,1789 | 17,7% | 0,1674 | 16,3% | +0,0116 |
| 0 Horizontale | 1.701 | 0,1755 | 17,0% | 0,1700 | 16,8% | +0,0055 |

Platte 6 wirkt **3x staerker** als die naechstgroesste und 14x staerker
als die schwaechste. **Die erste Verzweigung der Regel greift: die
Interaktion ist gelernt**, die Nutzer-Beobachtung ist im Netz abgebildet.

**Methoden-Korrektur waehrend der Messung**: mein erster Kontroll-Ansatz
nahm Platte 3 -- die AUSSCHLUSS-PARTNERIN von Platte 6. "3 aktiv" heisst
damit fast dasselbe wie "6 inaktiv", und das Spiegelbild (-0,0817) war
keine unabhaengige Bestaetigung, sondern dieselbe Zahl mit umgekehrtem
Vorzeichen. Ersetzt durch Kontrollen aus ANDEREN Paaren (2/5, 4/1, 0/7).
Dieselbe Ausschluss-Struktur, die schon den Plattenkopf-Entwurf korrigiert
hat.

**Verteilungs-Hinweis**: die Mediane liegen bei ~0,0000-0,0001 -- in den
meisten Stellungen zieht das Netz gar nicht, der Mittelwert wird von einer
Minderheit entschiedener Ziehzuege getragen. Deshalb ist die
">50%"-Spalte die aussagekraeftigere: entschiedene Ziehzuege steigen von
13,2% auf 21,5%.

### Folge fuer den Plattenkopf -- Erwartung daempfen

Die Nutzer-Partie verlor 19 Punkte auf Diagonalen (10:0) und
Spezialfeldern (-3 gegen -12). Fuer den Spezialfeld-Teil ist jetzt belegt:
**das Netz weiss, dass Ziehen bei aktiver Platte 6 wertvoller ist.** Die
Erklaerung "es kennt die Interaktion nicht" ist damit ausgeschlossen. Was
offen bleibt, ist die GROESSE -- ob 21,5% entschiedene Ziehzuege genug
sind -- und das ist aus Policy-Masse allein nicht beantwortbar.

Der Plattenkopf (`PREREG_plate_head.md`) bleibt sinnvoll, aber seine
Begruendung verschiebt sich: nicht "die Platten sind unbekannt", sondern
"die Dosierung und die anderen Kriterien". Fuer die Diagonalen ist Ziehen
ohnehin nicht der Hebel -- dort entscheidet die Platzierung.

## Architektur-Festlegung (Nutzer 2026-08-10)

*"und dann bauen wir langsam die anderen parameter auch auf
wahrscheinlichkeiten um -> sondern ein Spiel mit perfekter Information und
Zufallsknoten. Backgammon ... innerhalb der runde ist der stapel und die
bonuschips nicht bekannt. groesste unsicherheit in runde 1. laesst sich
vermutlich ueber wahrscheinlichkeiten sauber abdecken. und wir koennen den
k wert und den shuffle rausnehmen. beim rundenuebergang dann bootstrap.
runde 5 ist alles bekannt."*

Dreiteilung der Unsicherheit, je ein Werkzeug:

| Ebene | Unsicherheit | Werkzeug | Stand |
|-------|--------------|----------|-------|
| Innerhalb der Runde | Kuppelstapel, Bonuschips | **aufgezaehlter Zufallsknoten** (exakte Erwartung) | ZU BAUEN (Teil B) |
| Rundenuebergang | Fabrik-Befuellung aus dem Beutel | **TD-Bootstrap** | ERLEDIGT |
| Runde 5 | -- (Annahme: keine) | exakte Alpha-Beta | **BEFUND, siehe unten** |

Damit entfallen `MOSAIC_NUM_DETERMINIZATIONS` (k) und
`determinize_hidden_information` (Shuffle) ersatzlos.

### Der eigentliche Gewinn ist Determinismus, nicht Spielstaerke

Ohne Shuffle ist die Netzsuche bei gegebenem Zustand **deterministisch**.
Damit faellt eine Rauschkomponente aus JEDER kuenftigen Arena. Das
Messproblem des Projekts ist Seed-Rauschen (5,75pp bei n=400 fuer
identische Konfiguration, `project_training_seed_variance`) -- dieser
Effekt ist vermutlich groesser als jeder Elo-Gewinn, den k je haette
liefern koennen. Als Hauptbegruendung des Umbaus vorgemerkt, NICHT die
Spielstaerke.

### k=4 ist damit kein Gate mehr

Beide Ausgaenge stuetzen den Umbau: H0 heisst, Welten bringen nichts und
Wahrscheinlichkeiten sind der Ersatz; ein Sieg heisst, die verdeckte
Information IST suchrelevant -- und dann ist die exakte Erwartung ueber die
Verteilung dem Mittel aus 4 Stichproben ueberlegen. Der Lauf wird zu Ende
gefuehrt und als Informativitaets-Messung ausgewertet, nicht als
Entscheidung.

### Verzweigungsbreite (fuer das Kostentor, Teil B)

- Kuppelstapel: `NUM_DOME_TILE_DESIGNS = 18`, aber der STAPEL haelt zu
  Rundenbeginn 13 und leert sich 13 -> 8 -> 4 -> 0 (gemessen). Die
  Verzweigung ist `min(Reststapel, verschiedene Designs)`, gewichtet nach
  Restanzahl; nach einem Zug aendert sich die Verteilung (Ziehen ohne
  Zuruecklegen), die Kinder tragen also verschiedene Posteriors -- exakt,
  aber Buchhaltung.
- Bonuschips: 5 Farben, 20 Chips im Pool -> trivial.
- Runde 1 ist gleichzeitig groesste Unsicherheit UND breiteste
  Verzweigung. Das Kostentor MUSS dort gemessen werden, nicht im Mittel
  ueber alle Runden.

### BEFUND: Runde 5 ist nicht vollstaendig bekannt (Orakel-Leck)

Belegt, nicht vermutet:

1. `build_bonus_chip_pool()` liefert **20** Chips (`dome.rs:243`, im Test
   `pools_have_expected_sizes` auf 20 festgenagelt).
2. 4 kleine Manufakturen. Aufbau verbraucht 4 (`state.rs:262`), die Runden
   2-5 je 4 -> 4 + 16 = **20, exakt aufgehend**. Runde 5 bekommt also 4
   frische Chips, und `setup_new_round` setzt
   `bonus_chip_revealed = false` (`state.rs:222`).
3. `round5::applies` = `round_number >= 5 && phase == Drafting`
   (`round5.rs:75`) -- **keine** Bedingung an die Chips.
4. Der Ruecksprung in die R5-Suche liegt an `net_mcts.rs:3573` und `:3619`
   (ebenso `mcts.rs:742/773/792`) und damit **VOR**
   `determinize_hidden_information` (`net_mcts.rs:2977` / `:3394`).
5. Ein legitimer Spieler darf einen Chip erst nehmen, wenn er aufgedeckt
   ist (`game.rs:315`), und aufgedeckt wird er erst beim Leerwerden der
   Manufaktur (`execution.rs:66`).

Folge: die exakte Alpha-Beta-Suche liest in Runde 5 die **wahren**
Chipfarben und kann steuern, welche Manufaktur sie zuerst leerraeumt, um
den passenden Chip zu bekommen. Die R5-Bahn ist damit die EINZIGE Suchbahn
ohne jede Behandlung verdeckter Information -- die Netzbahn nimmt Welten,
R5 nimmt die Wahrheit.

Der Modulkommentar behauptet das Gegenteil ("Ab Rundenbeginn ist Runde 5
also ein Full-Information-Endspiel") und begruendet es damit, dass alle
Zufaelligkeit in `setup_new_round` ablaeuft. Das verwechselt
**aufgeloest** mit **sichtbar**.

**Groesse ungemessen.** Belegt ist nur die Struktur. Vor einem Eingriff
gehoert eine Messung dazu, wie oft die R5-Wahl von der Chipidentitaet
abhaengt (Teil D, neu). Der Fix ist derselbe Baustein wie Teil B: 4
verdeckte Chips sind ein aufzaehlbarer Zufallsknoten.

Reihenfolge-Empfehlung: Teil D (Groesse des R5-Lecks messen) VOR Teil B,
weil Teil D den Baustein an der kleinsten Verzweigung (<=5 Farben, 4
Manufakturen) testet, bevor er an der breitesten (Stapel, Runde 1)
gebraucht wird.

### KORREKTUR des R5-Befunds (Nutzer 2026-08-10)

*"nein. 16 chips sind bereits in den runden 1-4 genommen worden und
bekannt. somit kann auf die 4 chips zurueckgeschlossen werden die noch in
runde 5 im spiel sind. was nicht bekannt ist, ist die exakte position auf
welcher fabrik sie sind."*

Richtig, und mein "Orakelwissen" war zu breit. Der Restsatz ist
**strukturell garantiert oeffentlich**: `check_drafting_complete`
(`game.rs:499`) laesst die Runde nicht enden, solange ein aufgedeckter Chip
noch verfuegbar ist (`chips_available` -> `return false`), und verlangt
zusaetzlich alle Manufakturen leer bei aufgedecktem Chip. Jeder Chip wird
also in seiner eigenen Runde aufgedeckt UND genommen -> nach Runde 4 sind
exakt 16 gesehen, die 4 restlichen stehen fest. Die Ableitung haengt nicht
am Gedaechtnis, sie folgt aus der Rundenendbedingung.

Das Leck ist damit die **ZUORDNUNG**, nicht die Identitaet: hoechstens
4! = 24 Belegungen, weniger bei farbgleichen Chips (der Pool enthaelt
Duplikate; fuer die Suche zaehlen nur die Farben, nicht `chip_id`).

**Zweiter Defekt, umgekehrtes Vorzeichen:** das Netz kann die Ableitung
NICHT machen. Verbrauchte Chips werden vom Spielerbrett entfernt
(`round_end.rs:576` `bonus_chips.remove(i)`), und die Merkmale kodieren nur
die AKTUELL GEHALTENEN als 5 Farbzaehler (`features.rs:597`). Die Historie
ist weg.

| | Restsatz (welche 4) | Position (welche Fabrik) |
|---|---------------------|--------------------------|
| Mensch | **bekannt**, garantiert | unbekannt |
| Netz (Merkmale) | **unbekannt** | unbekannt |
| R5-Alpha-Beta | bekannt | **bekannt** <- Leck |

Dem Netz fehlt Information, die ein legitimer Spieler hat; der R5-Suche
steht Information zur Verfuegung, die keiner hat. Zwei getrennte Aufgaben:

- **Merkmal (Defizit)**: gesehener/verbrauchter Chipsatz als additives
  Merkmal. Braucht Schema-Bump + Cache-Neubau -> **zusammen mit dem
  Plattenkopf fahren**, dann wird der Neubau einmal bezahlt.
- **Zufallsknoten (Leck)**: R5-Zuordnung als aufgezaehlter Knoten
  (<=24 Belegungen) statt wahrheitsgemaesser Lesung.

### Das tragende Prinzip: Menge oeffentlich, Reihenfolge verdeckt

Beide verdeckten Quellen haben dieselbe Struktur -- die MENGE ist
oeffentlich, die REIHENFOLGE bzw. POSITION ist verdeckt:

- **Kuppelstapel**: `dome_pool_mask` (`serialize.rs:47`) liefert die
  Restmenge EXAKT, weil jedes der 18 Designs genau einmal existiert
  (`mask[tile_id] = 1`, Test `pools_have_expected_sizes`). Mengenteil
  richtig, Reihenfolgeteil gewuerfelt statt gewichtet.
- **Bonuschips**: Mengenteil fehlt im Merkmal, Positionsteil in R5
  gelesen. Beides falsch, in verschiedene Richtungen.

Das ist die Begruendung dafuer, warum der Shuffle (eine
Reihenfolge-Stichprobe) das falsche Werkzeug ist und die Maske (ein
Mengen-Aggregat) das richtige: die Unsicherheit ist eine PERMUTATION ueber
bekannter Menge, und die ist aufzaehlbar.

### KORREKTUR meiner Architektur-Notiz: die STELLE des Knotens entscheidet

Oben steht "aufgezaehlter Zufallsknoten (exakte Erwartung)" ohne Angabe,
WO der Knoten sitzt. Das ist unvollstaendig bis falsch, aufgedeckt durch
die Nutzerfrage *"koennen wir dann ueberhaupt alpha beta solver machen fuer
runde 5?"*:

Zaehlt man die <=24 Belegungen an der **Wurzel** auf, loest jede mit vollem
Wissen exakt und mittelt, dann ist das **kein Fix, sondern die
Determinisierung mit k = alle**. Die Stichprobenstreuung verschwindet, der
**Bias bleibt**: der Loeser darf in jeder Welt eine andere Strategie
spielen, obwohl er die Welten nicht unterscheiden kann (Strategy Fusion,
der bekannte Konstruktionsfehler von PIMC). Vollstaendige Aufzaehlung an
der falschen Stelle ist k->unendlich desselben schiefen Schaetzers.

**Korrekte Konstruktion**: der Zufallsknoten sitzt dort, wo die Information
**aufgedeckt** wird -- beim Leerwerden der Manufaktur (`execution.rs:66`),
und zwar gleichzeitig fuer beide Spieler, weil es keine private Information
gibt. Damit ist Runde 5 ein Baum mit OEFFENTLICHEN Zufallsknoten, also
**Expectiminimax statt Minimax**; Alpha-Beta verallgemeinert sich dorthin
(Star1/Star2-Pruning). Verzweigung <=4 beim ersten Aufdecken, dann <=3, <=2,
1 -- schlimmstenfalls Faktor 24 auf den Teilbaeumen darunter, weniger sobald
zwei Restchips dieselben Farben tragen.

Dasselbe gilt fuer den Kuppelstapel: der Knoten gehoert an den ZUG, der die
Platte aufdeckt, nicht an die Wurzel.

### Drei Wege fuer Runde 5 (Nutzer-Entscheidung offen)

| Weg | exakt | legitim | Kosten |
|-----|-------|---------|--------|
| A: Expectiminimax, Knoten am Aufdecken | ja | ja | bis 24x |
| B: unaufgedeckte Chips marginalisieren (vor dem Loeser verbergen) | **nein** | ja | ~0 |
| C: Status quo (wahre Chips lesen) | ja | **nein** | 0 |

Weg B nimmt dem Modul genau die Eigenschaft, aus der es seine Existenz
begruendet (exaktes Endspiel) -- aber exakt-und-unrechtmaessig ist
schlechter als naeherungsweise-und-ehrlich.

**Reihenfolge**: erst Teil D messen (wie oft haengt die R5-Wahl an der
Belegung). Klein -> Weg B vertretbar. Gross -> die 24x sind gerechtfertigt.
Die k=4-Evidenz (`PREREG_ismcts_determinizations.md`: rechenneutral
monoton fallend, -8,75pp bei k=4) mahnt dabei zum Kostentor: Baum-
Vervielfachung hat sich in diesem Projekt schon einmal nicht bezahlt.

### Der Loeser sitzt in BEIDEN Bahnen -- das Leck ist symmetrisch (Nutzer 2026-08-10)

*"die heuristik hat aber auch den alpha beta solver drinnen oder?"* -- ja.
`round5::choose_action` wird gerufen von `search_action` (`mcts.rs:767`),
`search_with_tree` (`mcts.rs:783`) und `root_child_stats` (`mcts.rs:732`),
also der HEURISTIK-Bahn, ebenso von `net_mcts.rs:3573/:3619`.

**Folge 1 -- keine Verzerrung der bisherigen Messungen.** Anker und Netz
haben dasselbe Orakelwissen in Runde 5. Jede Arena Netz-gegen-Heuristik ist
davon unberuehrt, weil es eine GEMEINSAME Komponente ist. Meine Warnung,
das Schliessen koennte die Champion-Elo druecken, war falsch begruendet.

**Folge 2 -- ein Fix aendert den ANKER.** Heuristik@150/@200 ist das
Elo-Lineal der gesamten Leiter. Eine Korrektur in `round5.rs` macht
Elo-Werte davor und danach unvergleichbar -- dieselbe Klasse wie die
Regelwerk-Fixes (`project_rulebook_audit_fixes`), weswegen domefactB/v10
vor jenem Schnitt liegen.

**Loesung nach der Knopf-Disziplin des Projekts**: `MOSAIC_*`-Knopf mit
Default = heutiges Verhalten. Die alte Leiter bleibt unter Knopf=0
reproduzierbar, die neue Messreihe startet bewusst mit Knopf=1 auf BEIDEN
Seiten. Kein stiller Ankerwechsel. (Arbeitsname `MOSAIC_R5_HIDE_CHIPS`.)

### Teil D wird billiger als geplant

Nicht eine Arena, sondern eine **Uneinigkeitszaehlung**: die von
`round5::choose_action` gewaehlte Aktion unter der WAHREN Belegung gegen die
gewaehlte Aktion unter permutierten Belegungen. Kein Spiel muss zu Ende
gespielt werden. Entscheidungsgroesse = Anteil der R5-Zustaende, in denen
die Wahl kippt.

### NODE_BUDGET dreht das Kostenbild

`round5::NODE_BUDGET = 200` (`round5.rs:59`), `TIME_BUDGET` nur noch
Notdeckel (`:67`). Der "exakte Loeser" ist damit **heute schon bei 200
Knoten abgeschnitten** -- exakt ist die BLATTBEWERTUNG
(`calculate_end_scoring` + Tiling-Solver), nicht die Loesung der Runde.

- Die <=24-fache Verzweigung trifft ein winziges Budget: 4.800 Knoten sind
  neben 400 Netz-Sims mit 2D-Inferenz nichts. Mein Kostenbedenken oben
  ("bis 24x", Warnung aus der k=4-Evidenz) war **ueberzogen** -- die
  k=4-Evidenz betraf volle Netz-Wurzelbaeume, nicht 200-Knoten-Alpha-Beta.
- Mechanistisch ist das Leck wahrscheinlich **klein**: 200 Knoten reichen
  selten tief genug, um eine Manufaktur leerzuraeumen, den Chip
  aufzudecken und ihn zu nehmen. Das ist eine testbare Vorhersage fuer
  Teil D, vorab notiert.

### Anker-Wechsel per Anker-KANTE statt per Knopf (Nutzer 2026-08-10)

*"ich wuerd einfach eine neue heuristik reinmachen, diese dann gegen die
standard heuristik gaten und mit dem elo wert als neuen anker verwenden"*

Besser als mein Knopf-Vorschlag, und aus einem Grund, den ich nicht bedacht
hatte: das **verbindet** die Leitern statt sie zu trennen. Der Knopf haette
die alte Reihe reproduzierbar gehalten, aber keinen UMRECHNUNGSFAKTOR
geliefert -- ein Elo-Wert nach dem Fix waere mit einem davor weiter
unvergleichbar. Die Anker-Kante misst genau diesen Faktor:

    Elo(neuer Anker) = Elo(alter Anker) + gemessene Kante

Der Knopf bleibt als BAUTEIL: er ist die Art, wie die zweite Heuristik ohne
Code-Fork entsteht. Knopf implementiert die Variante, Gating misst die
Kante, der Anker erbt den Versatz. (Etablierte Praxis im Projekt, vgl.
Regel 3 in `PREREG_points_blend_w.md`: "braucht erst eine eigene
Anker-Kante, damit bewertete Partien Elo-regelkonform bleiben".)

#### Vorab: H0 ist hier das ERWUENSCHTE Ergebnis

Eine Brueckenmessung invertiert die Entscheidungsregel. Findet das Gating
keinen Unterschied, heisst das NICHT "unentschieden" -- es heisst, der Anker
laesst sich ohne Sprung austauschen, Versatz null, die Leiter bleibt
buchstaeblich dieselbe. Das ist also keine Ueberlegenheitspruefung, sondern
eine **AEQUIVALENZPRUEFUNG**, und die braucht vorab eine MARGE statt einer
Signifikanzschwelle:

- n=400, Block-SE ~2,2pp -> der Unterschied ist auf ca. **+-4,4pp** (2 SE)
  einklammerbar.
- |Delta| innerhalb der Marge -> "kein Versatz", Anker wird 1:1 getauscht.
- |Delta| ausserhalb -> der gemessene Wert wird als **Versatz verbucht**,
  nicht verworfen.

Ohne diese Vorab-Festlegung wuerde H0 als "nichts gelernt" fehlgelesen --
genau der Fehler, gegen den `feedback_preregister_decision_metric` steht.

#### Zwei Randbedingungen

1. **Die Kante ist simzahl-spezifisch.** Sie muss bei der Simzahl gemessen
   werden, in der der Anker BENUTZT wird: Heuristik@200 in der
   Elo-Kaderung, @150dyn in den Env-A/Bs sind zwei verschiedene Bruecken,
   falls der Effekt simzahlabhaengig ist. Im Zweifel beide messen.
2. **Der neue Anker friert nach dem Gating ein**, wie der alte, dessen
   grobes `-3 * special_empty` bewusst nicht angefasst wird
   (`project_v8d_value_head_root_cause` / Elo-Lineal-Regel). Ein Lineal,
   das sich mitbewegt, ist keines.

Erwarteter Ausgang nach der NODE_BUDGET-Vorhersage oben: Versatz nicht
nachweisbar, Anker tauschbar.

### Spezialfeld-Bug in den neuen Anker buendeln (Nutzer 2026-08-10)

*"bei der aktualisierten heuristik kannst den spezialfeld bug auch gleich
beheben"*

Lokalisiert -- und mit einer Wendung, die Arbeit spart.

**Beide Fundstellen der flachen 3 liegen im Aufloeser**, nicht in der
Suche: `best_eval_for_tile` (`self_play.rs:460`) und
`avg_remaining_type_value` (`self_play.rs:485`) werden AUSSCHLIESSLICH aus
`resolve_and_apply_stack_draw` gerufen (Zeilen 519, 525, 538). Die echte
Wertung ist reihenabhaengig 1..6 (`round_end.rs:327`:
`pattern_row = slot_row*2 + sp_idx/2`, `bonus = pattern_row+1`).

`wertung_progress` ist fuer Kriterium 6 dagegen **exakt**
(`-3.0 * special_empty`, `scoring.rs:178`, deckungsgleich mit
`score_empty_special_fields`) -- dort ist kein Bug.

#### Fix und Forschungsmodus sind ALTERNATIVEN, nicht Ergaenzungen

`MOSAIC_STACK_DRAW_RESEARCH=1` umgeht genau diesen Aufloeser. Traegt der
neue Anker den Forschungsmodus, ist der Spezialfeld-Bug bauartbedingt weg,
weil der Code nicht mehr laeuft (der Kommentar an `self_play.rs:605` sagt
es selbst: die Suche rechnet die Strafpunkte, "statt dass
`best_eval_for_tile` sie per `cost_so_far` von Hand gegenrechnet").

**Und fuer die HEURISTIK ist der Forschungsmodus sofort verfuegbar**: die
Trainingsvoraussetzung (0 von 16.322 Korpus-Datensaetzen enthalten
Zwischenzustaende -> erst Self-Play, dann Training, dann Gating) gilt nur
fuer das NETZ. Eine Heuristik braucht keinen Korpus.

Fuer den Netzpfad bleibt der Aufloeser bis zum Korpus in Betrieb -- dort
behaelt der Fix der flachen 3 seinen Wert. Also machen, aber nicht
erwarten, dass er den neuen Anker beruehrt.

#### Zwei Nebenbefunde

1. **`bonus_points` traegt doppelte Last**: es ist auch der
   Typ-Unterscheider (`is_special_type()` = `bonus_points > 0`,
   `dome.rs:128`). Das Feld darf NICHT auf den reihenabhaengigen Wert
   umgestellt werden -- die Platte kennt ihren Slot nicht, der Wert
   entsteht erst bei der Platzierung. Der Fix rechnet am Platzierungsort
   und laesst das Feld als Typ-Marke stehen.
2. **`PlayerBoard::place_special_tile` (`board.rs:172`) hat keinen
   Aufrufer** -- toter Code, gibt ebenfalls die flache Zahl zurueck. NUR
   NOTIERT, nicht geloescht (Loeschungen brauchen pfadgenaue Freigabe).

#### Preis der Buendelung

Die Anker-Kante misst dann den **Summeneffekt** aus R5-Chips und
Stapelzug-Umstellung. Der Versatz waere hinterher nicht auf die beiden
Ursachen aufteilbar. Fuer einen Anker ist die Zahl genug, die Zerlegung
nicht noetig -- wer sie will, braucht zwei Gatings statt einem.

**Inhalt des neuen Ankers (Vorschlag, Stand jetzt):**
- R5: unaufgedeckte Chips vor dem Loeser verbergen (Weg B) ODER
  Expectiminimax am Aufdecken (Weg A) -- Entscheidung nach Teil D
- Stapelzug: `MOSAIC_STACK_DRAW_RESEARCH=1` (subsumiert den
  Spezialfeld-Bug)
- danach eingefroren

#### KORREKTUR: die Heuristik laeuft nie durch den Aufloeser

Der Abschnitt direkt oben ruht auf einer falschen Praemisse. Belegt:

- Self-Play-/Arena-Schleife: `if pi == net_board { apply_chosen_action(..) }
  else { game.apply_drafting(&chosen) }` (`self_play.rs:1527-1537`) -- der
  Kommentar dort nennt es ausdruecklich "Sequenzielle
  Stapel-Zieh-Aufloesung nur fuer den Netz-Spieler ... die Heuristik-Seite
  braucht das laut Nutzer-Vorgabe nicht".
- Python-Seite: `apply_chosen_action` unter der Ueberschrift "Stufe 2
  (Netz)" (`py.rs:663`).
- Und `self_play.rs:432` sagt es selbst: "nur der Netz-Pfad nutzt diese
  Funktion".

**Folge: in der HEURISTIK gibt es keinen Spezialfeld-Bug.**
`wertung_progress` ist fuer Kriterium 6 exakt, und die reihenabhaengigen
1..6 fallen in der Simulation ueber die echte Spiellogik an. Der neue Anker
schrumpft auf die R5-Chipbehandlung; der oben beschriebene
Attributionsverlust der Buendelung entfaellt.

**Nebenprodukt, wertvoller als der Fix**: die Heuristik IST die
Referenzimplementierung von "Peek ausfuehren und neu suchen" -- sie wendet
die Einzelaktion an und laesst die Folgeentscheidung im naechsten
Schleifendurchlauf entstehen (`self_play.rs:1530-1536`). Genau das ist die
Nutzer-Vorgabe fuer den Netzpfad. Das Design ist erprobt, nicht spekulativ.

**Empfehlung gegen einen Patch der flachen 3 im Netzpfad**: (1) er aendert
die Zugwahl des Champions und braeuchte ein eigenes Gating, um Elo-legal zu
bleiben; (2) das Bauteil ist zur Abloesung vorgesehen
(`MOSAIC_STACK_DRAW_RESEARCH`); (3) der Ersatz laeuft auf der
Heuristikseite bereits. Der direkte Weg ist der Forschungsknopf fuers Netz,
und der braucht nur den Korpus mit Zwischenzustaenden.

## WEG A IMPLEMENTIERT + TEIL D GEMESSEN (2026-08-10)

Nutzer-Entscheidung: *"mach A. ist der saubere weg."*

### Implementierung (`engine/src/round5.rs`, 321 Tests gruen)

- `MOSAIC_R5_CHANCE_NODES` (Default AUS) schaltet die Zufallsknoten.
- `MOSAIC_R5_NODE_BUDGET` (Default `NODE_BUDGET` = 200) trennt "ehrlich"
  von "flacher": Zufallsknoten vervielfachen den Teilbaum unter jedem
  Aufdecken, bei festem Budget waere eine Anker-Kante nicht interpretierbar.
- `action_outcomes` zaehlt am AUFDECKEN auf, nicht an der Wurzel -- Tausch
  des Kandidatenchips nur zwischen VERDECKTEN Manufakturen, Gewicht =
  Vielfachheit. Die Invariante "verdeckte Manufakturen tragen den Restsatz"
  bleibt erhalten, der Glaube braucht keine eigene Buchhaltung.
- Gruppierung nach `.colors` (nie `chip_id`, Code-Audit `tiling_solver.rs`)
  -- farbgleiche Chips fallen zu EINEM Zweig zusammen.
- Bei nur noch EINEM verdeckten Chip ist er aus dem Restsatz eindeutig
  ableitbar; ihn dann zu lesen ist legitim, nicht abgekuerzt.
- Zweiter Leckkanal geschlossen: die ZUGSORTIERUNG sortiert nach dem
  Erwartungswert, nicht nach dem wahren Chip -- unter Knotenbudget
  entscheidet die Reihenfolge mit, welche Zuege ueberhaupt gesucht werden.
- Innerhalb eines Zufallsknotens wird NICHT beschnitten (Cutoff auf
  Teilsummen braeuchte Star1/Star2-Wertgrenzen). Bei <=4 Ausgaengen billiger
  als die Buchhaltung -- und nachweisbar korrekt.
- Flagge als PARAMETER durchgereicht, nicht als Prozess-Global gelesen:
  `chance_nodes_enabled()` ist ein OnceLock, `cargo test` laeuft parallel im
  selben Prozess, beide Betriebsarten waeren sonst nicht testbar.

### TEIL D -- Ergebnis: das Leck ist wirkungslos

`teil_d_permutation_sensitivity_probe` (`#[ignore]`, auf Abruf), 8
realistische Partien via `drive_to_round_start(seed, 5)`, JEDE Entscheidung
der Runde, Belegung der verdeckten Chips zyklisch permutiert:

| Modus | Permutationen, die die Zugwahl kippen | Entscheidungen | davon >=2 verdeckte Chips |
|-------|----------------------------------------|----------------|---------------------------|
| chance=false (Status quo) | **0 / 247** | 137 | 103 |
| chance=true (Weg A) | **0 / 248** | 138 | 104 |

**Die vorab notierte mechanistische Vorhersage trifft zu**: 200 Knoten
reichen nie bis dorthin, wo die Chipfarbe wirkt. Dafuer muesste die Suche
eine Manufaktur leerraeumen, aufdecken, den Chip NEHMEN (eigene Aktion,
`game.rs:315` erlaubt es erst nach dem Aufdecken) und ihn im Tiling
verwerten -- die Blattbewertung sieht Chips nur ueber
`player.bonus_chips`.

Damit ist das Orakel-Leck **strukturell echt und messbar wirkungslos**.

### Zwei Folgerungen, die das aendert

1. **Weg B waere ausreichend gewesen.** Die Verzerrung der
   Eingabemittelung haette nie gegriffen. A ist trotzdem gebaut, kostet
   nichts messbar und ist exakt -- kein Grund zur Umkehr, aber der Grund
   ist jetzt Prinzip, nicht Wirkung.
2. **Die Anker-Kante ist NICHT trivial null.** Die Entscheidungszahl
   unterscheidet sich (137 vs 138), die beiden Modi spielen also nicht
   identisch -- die Mittelung verschiebt Werte und damit gelegentlich das
   Argmax, OHNE dass die verdeckte Belegung eine Rolle spielt. Die
   Aequivalenzpruefung bleibt noetig, ihr Ausgang durfte aber innerhalb der
   +-4,4pp-Marge erwartet werden.

### Ehrlichkeitsnotiz zum Invarianz-Test

`chosen_action_is_invariant_under_hidden_chip_permutation` sichert die
EIGENSCHAFT ab, **diskriminiert aber nicht**: der alte Modus ist ebenso
invariant (0/247). Der Test belegt also nicht, dass ein wirksamer Defekt
behoben wurde -- er schuetzt die Eigenschaft fuer kuenftig groessere
Budgets, wo sie zu greifen beginnt. Als Kommentar im Test festgehalten,
damit er spaeter nicht ueberschaetzt wird.

## BEFUND: NODE_BUDGET = 200 ist nicht ausreichend (Nutzer-Frage 2026-08-10)

*"sind 200 knoten ueberhaupt ausreichend"* -- nein, belegt.

`node_budget_sufficiency_probe` (`#[ignore]`), dieselben 8 realistischen
Partien, je Entscheidung die Zugwahl bei 200 gegen die bei hoeherem Budget:

| Budget | Zugwahlen, die sich gegenueber 200 aendern |
|--------|--------------------------------------------|
| 400 | 8/137 = **5,8 %** |
| 1000 | 13/137 = **9,5 %** |
| 4000 | 18/137 = **13,1 %** |

Mittlere Wurzelverzweigung 19,6. Die Kurve **steigt noch** -- die Suche ist
bei 4000 Knoten nicht konvergiert. Jede achte Entscheidung fiele tiefer
anders aus.

Das war zu erwarten und steht sogar im Kalibrierungs-Kommentar: die 200 sind
das p75 dessen, was der alte 150ms-Wanduhr-Deckel ERREICHTE -- eine
**Tragbarkeitszahl fuers Self-Play, keine Suffizienzzahl**. Bei Verzweigung
~20 reichen 200 Knoten mit Alpha-Beta fuer effektiv ~3 Halbzuege. "Exakt"
ist die BLATTBEWERTUNG (`solve_round_final_score_endaware` +
`calculate_end_scoring`), nicht die Suche. Der Modulkopf ("exakte
Minimax-Suche mit Alpha-Beta-Pruning") ueberverkauft das.

### Damit ist eine nie gestellte Frage offen: Loeser oder Netz?

`round5.rs` kam in **98dffa3** gebuendelt mit der Kuppelstapel-Mechanik und
Server-Fixes herein -- **ohne eigenes Gating**. Gerechtfertigt wurde die
Ersetzung des Netzes in Runde 5 allein durch das Argument, die Runde sei
exakt loesbar. Dieses Argument ist jetzt zweifach entkraeftet: die Runde ist
nicht vollinformiert (Chips, siehe oben), und die Suche ist keine Loesung,
sondern ~3 Halbzuege.

**Eine Arena taugt dafuer NICHT.** Der Loeser sitzt in beiden Bahnen
(`mcts.rs:767/783/732` und `net_mcts.rs:3573/3619`), ein groesseres Budget
hebt also beide Seiten gleichzeitig und die Siegquote bleibt blind --
derselbe Symmetrie-Fallstrick wie beim Chip-Leck. Wer das ohne diese Notiz
als Arena ansetzt, misst garantiert H0 und schliesst falsch.

### Instrument: ORAKEL-UEBEREINSTIMMUNG (Teil E, neu)

Eine sehr tiefe Referenzsuche (Arbeitswert 50.000 Knoten, `TIME_BUDGET`
entsprechend hoch) auf denselben ~137 Entscheidungen, dann der Anteil
uebereinstimmender Zugwahl je Kandidat:

- Loeser@200 (Status quo)
- Loeser@1000 / @4000
- **Netz@400** (braucht einen Knopf, der `round5::applies` fuer den
  Netzpfad ausschaltet -- existiert noch nicht)

Drei Zahlen auf derselben Skala, ohne Arena, ohne Symmetrieproblem. Der
Vergleich Loeser-gegen-Netz fällt als Nebenprodukt ab.

**Bezahlbarkeit**: Commit 6af37ca hat gemessen, dass der Runde-5-Loeser nur
**4,3 %** der Self-Play-Kosten traegt (Task #32, "Hypothese widerlegt").
Budget x5 kostet also insgesamt ~x1,17, x20 ~x1,8 -- fuer eine Entscheidung,
die sich in 9,5 bzw. 13,1 % der Faelle aendert, billig.

### Vorab-Vermutung (damit sie pruefbar ist, nicht hinterher plausibel)

Der Loeser gewinnt, weil seine Blattbewertung optimales Tiling UND
Endwertung des erreichten Bretts EXAKT kennt -- Information, die das Netz nur
schaetzen kann. Dem Netz fehlt nicht Tiefe, sondern diese Exaktheit.
Umgekehrt duerfte der Loeser bei der DRAFTING-Dynamik verlieren, und die
kostet Tiefe; bei ~3 Halbzuegen koennte das Netz dort vorne liegen. Ein
Sieg des Netzes waere also kein Widerspruch, sondern ein Hinweis, dass die
Drafting-Interaktion mehr wiegt als die exakte Endabrechnung.

## TEIL E, Loeser-Haelfte gemessen: Tiefe ist fast wirkungslos

`teil_e_oracle_agreement_probe` (`#[ignore]`), Orakel = 20.000 Knoten mit
120s-Deadline (griff **0x**, also knotengebunden), 145 Entscheidungen aus 8
realistischen Partien, weitergespielt jeweils mit der ORAKEL-Wahl damit die
Stellungsfolge fuer alle Kandidaten identisch bleibt:

| Budget | Uebereinstimmung mit dem Orakel |
|--------|--------------------------------|
| 200 | **81,4 %** (118/145) |
| 400 | 82,8 % (120/145) |
| 1000 | 84,1 % (122/145) |
| 4000 | 84,8 % (123/145) |

### KORREKTUR der Implikation des vorigen Befunds

Die 13,1 % geaenderten Zugwahlen (4000 gegen 200) bleiben richtig, bedeuten
aber NICHT "13 % falsch bei 200". Von den 18 geaenderten Entscheidungen
wandern nur ~5 zum Orakel hin, der Rest wechselt zwischen annaehernd
gleichwertigen Zuegen. **Das Zwanzigfache an Knoten kauft 3,4
Prozentpunkte.** Meine Formulierung "jede achte Entscheidung fiele tiefer
anders aus" war zahlenrichtig und in ihrer Suggestion falsch.

**Die tragende Folgerung**: Tiefe ist in dieser Stellungsklasse fast
wirkungslos, also traegt die BLATTBEWERTUNG die Entscheidung, nicht die
Suche. Das stuetzt die vorab notierte Vermutung -- der Wert des Loesers
liegt in `solve_round_final_score_endaware` + `calculate_end_scoring`, nicht
im Alpha-Beta darum herum.

### Praktische Antwort auf die Budget-Frage: 200 bleibt

Nicht konvergiert, aber das Anheben ist schlechtes Geschaeft: ~x1,8
Gesamtkosten (R5 = 4,3 % des Self-Play, Commit 6af37ca) fuer 3,4 Punkte
Uebereinstimmung. `MOSAIC_R5_NODE_BUDGET` bleibt eingebaut und ungenutzt --
er hat seine Frage beantwortet, statt eine Einstellung zu werden.

### Loeser bleibt fuer die HEURISTIK (Nutzer 2026-08-10)

*"fuer die heuristik der alpha beta solver sicher bleiben schaetz ich mal"*
-- ja, und die Messung liefert den Grund. Die Alternative waere die
heuristische Suche mit `wertung_progress`, einer FORTSCHRITTS-Naeherung. Der
Loeser bringt an derselben Stelle die exakte Rechnung. Sein Vorteil liegt
also genau in dem Teil, der laut Teil E fast alles entscheidet. Zweiter,
unabhaengiger Grund: der Anker muss ohnehin eingefroren bleiben.

**Damit verengt sich die offene Frage auf den NETZPFAD**: dort steht ein
GELERNTER Blattwert gegen den exakten. Nur diese Haelfte von Teil E kann
noch etwas entscheiden, und sie braucht den Knopf, der `round5::applies`
fuer den Netzpfad ausschaltet (existiert noch nicht) plus die
Orakel-Referenz von oben als gemeinsame Skala.

## SCHARFGESCHALTET 2026-08-10 -- und die Suche heisst jetzt anders

Nutzer-Entscheid: *"ja gehen scharf"*, danach *"haben wir jetzt eigentlich
ein derivat von einem alpha beta solver? weil wir haben ja
wahrscheinlichkeiten wegen den bonuschips"*.

**Ja -- die Suche ist jetzt Expectiminimax**, nicht mehr Minimax mit
Alpha-Beta: Max-/Min-Knoten mit Cutoffs plus **Zufallsknoten** an den
Aufdeck-Stellen (Ballards *-Minimax-Familie; klassische Anwendung
Backgammon, und genau diese Struktur hat das Spiel). Der Modulkopf von
`round5.rs` ist entsprechend neu geschrieben -- er behauptete "exakte
Alpha-Beta-Suche" und "Full-Information-Endspiel", und beides ist in dieser
Sitzung widerlegt worden.

### Grundlage des Scharfschaltens

`r5_chance_arming_sign_probe`, 80 Seeds:

| | Wert |
|---|---|
| Entscheidungen | 1371 |
| Abweichungen an-vs-aus | 43 (3,1 %) |
| Delta (Punkte, Sicht des Ziehenden) | **-0,47** |
| SE / t | 0,66 / **-0,71** |
| Median | **+0,00** |
| Spanne, davon negativ | -10 .. +16, 13/43 |

**H0 -- Versatz null, gemessen statt behauptet.** Auflösung ca. +-1,3 Pkt je
abweichender Entscheidung, bei ~0,5 Abweichungen je Partie also ~+-0,02 Pkt
je Partie.

**Wichtig fuer die Protokolltreue**: ein Zwischenstand mit nur 4
Abweichungen zeigte -2,75 Pkt und haette zum gegenteiligen Schluss gefuehrt;
das trug ein einzelner -13-Fall. Ausgeloest wurde die richtige Messung durch
eine Nutzer-Korrektur -- ich hatte den Versatz mit "die Abweichungen liegen
in der Runde mit der geringsten Hebelwirkung" begruenden wollen, und Runde 5
hat die GROESSTE Hebelwirkung (der Zahltag), nur die geringste FREIHEIT (das
Kuppelraster ist fix). Das falsche Argument haette ein richtiges Ergebnis
gestuetzt -- der unangenehmste Fehlertyp.

### Anker-Behandlung

Der Loeser sitzt in BEIDEN Bahnen, das Scharfschalten verschiebt also den
Anker mit. Behandlung:

- **Versatz null**, begruendet aus der Messung oben, NICHT aus einer
  Anker-Kante. Die geplante Aequivalenz-Arena haette den Effekt nicht
  aufloesen koennen (Auflösung +-4,4pp gegen ~0,02 Pkt/Partie) und waere
  eine erschlichene Freigabe gewesen.
- `MOSAIC_R5_CHANCE_NODES=0` stellt das alte Verhalten her -- gebraucht, um
  eine Alt-Elo-Kante zu reproduzieren.
- Die Paritaets-Sonde ist NICHT betroffen: sie hasht Runde-1-bis-3-Zustaende
  (`tools/parity_probe.py`), Runde 5 liegt ausserhalb ihrer Pruefflaeche.
- Elo-Zeilen ab heute tragen die neue Anker-Definition. Die `knobs`-Spalte
  in `elo_history.csv` erfasst nur ENV-Ueberschreibungen, ein Default-Wechsel
  steht also nicht darin -- Datum und dieser Eintrag sind die Grenze.

### Was bewusst NICHT gebaut ist

Star1/Star2-Pruning innerhalb der Zufallsknoten. Braucht Wertgrenzen je
Ausgang; bei <=4 Ausgaengen und 200 Knoten ist der Verzicht billiger als die
Buchhaltung -- und nachweisbar korrekt, waehrend ein falsch begruendeter
Cutoff auf Teilsummen still verzerren wuerde.

## TEIL B1 EINGETAKTET: Ein-Schritt-Erwartung an der Peek-Aktion (Nutzer 2026-08-10)

Nutzer-Auftrag: *"eintakten"*, nach der Klaerung, dass der Stapelzug aus
zwei trennbaren Stuecken besteht.

### Was schon existiert und was fehlt

| Stueck | Stand |
|--------|-------|
| **Kontrollfluss** -- Peek als echter Zug, danach neue Suche | **GEBAUT**: `MOSAIC_STACK_DRAW_RESEARCH` (self_play.rs). Erzeugt zugleich die Korpus-Datensaetze fuer die Unterentscheidungen |
| **Bewertung** -- "lohnt sich ein Peek ueberhaupt" | **FEHLT** = dieser Task |

### Konstruktion

Weil der Peek die Platte UNMITTELBAR aufdeckt und danach frisch gesucht
wird, muss die Suche NICHT ueber den Peek hinausplanen. Sie muss ihn nur
richtig bewerten. Das ist eine **Ein-Schritt-Erwartung an der Expansion**:
statt den einen (determinisierten) Nachzustand zu bewerten, alle moeglichen
bewerten und mit ihren Wahrscheinlichkeiten mitteln.

- Verteilung: gleichverteilt ueber die Restmenge, gruppiert nach Platten-
  DESIGN. Die Menge ist oeffentlich (`dome_pool_mask`, jedes der 18 Designs
  genau einmal), die Oberseite ist Index 0 (`dome_tile_pool.remove(0)`,
  `game.rs:183`), zurueckgelegte Platten haengen per `push` HINTEN an.
- **Teil A1 faellt hier mit ab**: das bekannte Segment am Ende darf nicht in
  die Verteilung eingehen. Das braucht einen Zaehler im Zustand
  ("wie viele Platten am Ende sind oeffentlich bekannt") -- additive
  Zustands-/Serialisierungs-Aenderung, als eigener Schritt gefuehrt. OHNE
  ihn ist die Verteilung konservativ falsch (behandelt Bekanntes als
  unbekannt), also ein tragbarer erster Stand.
- Kosten: |verschiedene Restplatten| Netz-Bewertungen statt einer, an einer
  seltenen Aktion (~3 Peeks je Partie). `Net::eval_pair` existiert fuer
  Batchung.

### Was BEWUSST NICHT gebaut wird

Ein echter Zufallsknoten IM Baum. Der braeuchte eine eigene Knotenart mit
wahrscheinlichkeits-proportionaler Auswahl -- sonst maximiert die Suche
ueber das Glueck statt zu mitteln -- und muesste mit Gumbel und completed-Q
zusammenspielen. Grosse Operation in einer 6.000-Zeilen-Suche, und unter dem
Nutzer-Kontrollfluss NICHT noetig. Die k=4-Evidenz mahnt zusaetzlich: das
Mitteln ueber Stichproben eines unbekannten Zustands hat in diesem Projekt
schon einmal geschadet.

### Entscheidungsregeln (vorab)

1. **Knopf** `MOSAIC_STACK_DRAW_CHANCE`, Default AUS, Paritaets-Sonde muss
   `8c6684ff...` weiter treffen.
2. **Vorzeichen zuerst, Arena spaeter** -- wie bei den R5-Knoten: erst
   messen, in wie vielen Entscheidungen sich die Zugwahl aendert und was das
   in Punkten kostet (Instrument-Muster `r5_chance_arming_sign_probe`). Eine
   Arena, die ~0,02 Pkt/Partie aufloesen soll, ist eine erschlichene
   Freigabe.
3. **Nicht mit dem Kontrollfluss vermischen**: `MOSAIC_STACK_DRAW_RESEARCH`
   und dieser Knopf werden GETRENNT gemessen. Zusammen eingeschaltet waeren
   zwei Aenderungen in einem Gating, und der Netz-Pfad braucht fuer den
   Kontrollfluss ohnehin erst einen Korpus.
4. **Reihenfolge zur Generierung**: der Kontrollfluss-Knopf gehoert in das
   naechste Self-Play (sonst fehlen die Zwischenzustaende eine weitere
   Generation, Nutzer-Hinweis). Die Bewertung kann danach kommen, weil sie
   ohne Trainingsvoraussetzung wirkt.

### Erwartung vorab

Die Priors fuer Slot und Rotation sind ungelernt (0 von 16.322 Datensaetzen
im Bestandskorpus). Gumbel zieht aber m=16 Kandidaten und korrigiert per
completed-Q; bei <=9 Slots x 4 Rotationen ist der Unterraum damit praktisch
abgedeckt. Generation eins sucht dort also ohne Vorsortierung, aber nicht
blind -- ein Zwei-Generationen-Vorlauf, der vorher notiert ist, damit er
hinterher nicht als Fehlschlag gelesen wird.
