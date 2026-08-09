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
