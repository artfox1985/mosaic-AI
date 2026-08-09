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
allem, was `DESIGN_konventionen_als_pruefungen.md` dafuer verlangt
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
  (`PREREG_plattenkopf.md`), weil es zeigt, dass die Platten-Information
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

Der Plattenkopf (`PREREG_plattenkopf.md`) bleibt sinnvoll, aber seine
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
Die k=4-Evidenz (`PREREG_ismcts_determinisierungen.md`: rechenneutral
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
