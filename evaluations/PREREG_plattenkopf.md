# Vorregistrierung: PLATTENKOPF (per-Kriterium-Endwertungs-Kopf)

**Angelegt 2026-08-09, VOR jeder Implementierung.** Nutzer-Entscheid:
*"vielleicht machen wir einfach einen extra kopf für die
plattenbewertung"* + *"ja registrier es vor. er sollte mit dem points
head eigentlich gut zusammenarbeiten. wie wir es in die blattbewertung
dann einbauen gilt es noch anzusehen."*

Der Kopf ERSETZT den zuvor diskutierten handgebauten
Wahrscheinlichkeits-Term fuer Platte 6
(`PREREG_punktekopf_platten.md`, Abschnitt "KANDIDAT"). Begruendung:
dieselbe Groesse wird gelernt statt geschaetzt, und ein Kopf erfasst
Abhaengigkeiten, die eine Haeufigkeitstabelle ueber zwei
Bedingungsgroessen nicht erfassen kann. Der handgebaute Term bleibt nur
als Rueckfallebene notiert.

## Anlass

Nutzer-Partie `game_20260809_115404_seed704874`: Grundpunkte 51:51,
Endwertung 18 gegen -2 (69:49). Verloren auf Diagonalen (10:0) und
leeren Spezialfeldern (-3 gegen -12). Der heutige Messstand zeigt: das
Netz ist NICHT plattenblind (Prior reagiert bis 0,46 Bit, Zugwahl kippt
in 29,0% der Faelle, beide Punkte-Koepfe tragen Platten-Information),
aber es gibt keinen Nachweis fuer STRATEGISCHES Ansteuern ueber Runden.
Die Plattenwirkung kommt bisher als NIVEAU-Verschiebung an, und die
kuerzt sich im Ranking weg -- der Grund, aus dem der gebaute
`PLATE_SHAPING`-Hebel folgenlos blieb (+2,4pp, n.s.).

## Design

**Ausgabe: 16 Werte** -- die 8 Wertungskriterien fuer den EIGENEN
Spieler und dieselben 8 fuer den GEGNER. Die Gegnerhaelfte ist
ausdruecklich Teil des Auftrags (Nutzer: Platten des Gegners verhindern
bzw. die -3-Platte erzwingen) und kostet fast nichts, weil das Label
symmetrisch vorliegt.

**Labels: gratis und exakt.** Aus einem Endbrett sind ALLE acht
Kriterien berechenbar -- `scoring.rs::player_scoring_features` liefert
genau die noetigen Groessen (`row_fill`, `col_fill`, `diag_fill`,
`border_fill`, `corner_fill`, `wild_filled`/`wild_total`,
`special_empty`), und die `score_*`-Funktionen bilden daraus die Punkte.
Kein neues Self-Play noetig; die vorhandenen Partien reichen.
**Zu pruefen bei der Implementierung** (nicht vorab behauptet): dass der
letzte gespeicherte Zustand je Partie der Endstand NACH dem Tiling ist,
sonst muss der Label-Zeitpunkt entsprechend gewaehlt werden.

**Verlust MASKIERT auf die AKTIVEN Kriterien -- Korrektur nach
Nutzer-Einwand 2026-08-09** (*"aber warum 16? wir spielen nur mit 3
wertungsplatten und manche schließen sich aus"*). Mein erster Entwurf
wollte auf alle acht trainieren; das war falsch, und der Einwand trifft
staerker als er formuliert war:

`scoring.rs::MUTUALLY_EXCLUSIVE_PAIRS` zeigt, dass die acht Kriterien
**vier Ausschluss-Paare** bilden -- (0,7) Horizontale/Farbenreiche
Reihen, (6,3) Spezialfelder/Mehrfarbige Felder, (4,1) Aeussere
Felder/Vertikale Reihen, (2,5) Diagonale Reihen/Eckplatten -- mit
hoechstens einem aktiven je Paar. Bei drei gezogenen Platten liefern
also genau drei der vier Paare je ein Kriterium.

Damit haette "auf alle acht trainieren" zwei echte Nachteile:
1. **Train/Inferenz-Fehlanpassung.** Zu jedem aktiven Kriterium wuerde
   ausgerechnet der Partner mittrainiert, der in DIESER Partie
   strukturell nicht aktiv sein konnte -- auf einem Brett, das gebaut
   wurde, WEIL der Partner nicht gewaehlt war. Maskiert lernt der Kopf
   dagegen genau die Bedingung, unter der er spaeter gelesen wird:
   "sage den Endwert von Kriterium k voraus, GEGEBEN dass k aktiv ist".
2. **Gradienten-Verduennung.** 16 Ausgaben, aber nur ~6 je Zustand
   gelesen. Die Aux-Terme sind ohnehin klein (gemessene Loss-Anteile:
   Policy 90,1%, Value 6,5%), und verduennen wuerde vor allem
   **Kriterium 6** treffen -- genau den Fall aus der Nutzer-Partie, den
   wir am wenigsten verduennen duerfen.

Das Argument "fuenf zusaetzliche Gratis-Lernsignale" aus dem ersten
Entwurf ziehe ich damit zurueck. **16 Ausgabe-Plaetze bleiben** (stabile
per-Kriterium-Semantik ist leichter zu lernen als eine slot-indizierte,
die die Kriteriums-Identitaet erst aus dem One-hot erschliessen muesste),
aber je Zustand tragen nur die **3 eigenen + 3 gegnerischen aktiven**
Plaetze Gradienten. Maskierung ist das etablierte Muster im Projekt
(`opp_points_mask`, `endgame_mask`) -- kein neuer Mechanismus.
Ueber den Korpus hinweg bekommt trotzdem jeder der 16 Plaetze Training,
naemlich aus den Partien, in denen sein Kriterium aktiv war.

Falls Stufe A Unterfitting zeigt, ist "unmaskiert auf alle acht" ein
moeglicher ZWEITER Arm -- aber nicht die Ausgangsvariante.

**Eigener Verlust-Knopf.** Nicht an `POINTS_WEIGHT` haengen (das
multipliziert bereits points/opp_points/endgame -- Task D vermisst
gerade genau diese Gewichtung). Eigener Schalter, Default 0 = Kopf
aus = byte-identisches Bestandsverhalten.

**Aus `val_combined` HERAUSHALTEN**, genau wie der endgame-Kopf. Sonst
ist die Auswahl-Kennzahl nicht mehr mit Champion und Task-D-Armen
vergleichbar (stehende Lehre: die Entscheidungsmetrik vorab festlegen
und nicht durch neue Loss-Terme verschieben).

## Zweistufig -- und Stufe B ist ausdruecklich OFFEN

### Stufe A: reines Aux-Ziel (Repraesentation), entscheidet ueber Stufe B

Der Kopf trainiert mit, greift aber NICHT in die Blattbewertung ein.
Damit kein Doppelzaehlungs-Risiko, kein Arena-Budget, und die Frage
"lernt er das Problem ueberhaupt?" wird getrennt von "hilft er in der
Suche?" beantwortet.

**Entscheidungsmetrik (vorab): Vorhersagequalitaet je Kriterium gegen
eine Konstanten-Basislinie** (Korpus-Mittelwert des jeweiligen
Kriteriums). Gemessen auf dem Val-Split, je Kriterium getrennt, fuer
eigene UND Gegner-Seite.

1. **Regel A1**: Der Kopf gilt als lernend, wenn er die
   Konstanten-Basislinie auf **mindestens 5 der 8 Kriterien** schlaegt
   UND ausdruecklich **auf Kriterium 6 (leere Spezialfelder)** -- das
   ist der Fall aus der Nutzer-Partie und der einzige mit negativem
   Vorzeichen. Kriterium 6 ist damit Pflicht, nicht Kür.
2. **Regel A2**: Schlaegt er die Basislinie auf Kriterium 6 NICHT, ist
   das ein eigenstaendiger Befund ("die Strafe ist aus dem Zustand
   heraus nicht vorhersagbar") und Stufe B entfaellt. Dann waere die
   Rueckfallebene die ausgezaehlte Wahrscheinlichkeit.
3. **Regel A3 (Nebenwirkungs-Wache)**: `val_brier`, `policy_top3` und
   die Orakel-Metriken duerfen gegenueber dem Kontroll-Training nicht
   messbar fallen. Ein Aux-Kopf, der die Hauptkoepfe beschaedigt, wird
   nicht weiterverfolgt, egal wie gut er sein eigenes Ziel lernt
   (Praezedenz #35b: verbessert die nicht-validierte Metrik,
   verschlechtert die validierte -> geschlossen).
4. **Konsistenz-Pruefung (deskriptiv, gratis)**: Der Punkte-Kopf hat
   die Plattensumme bereits in seinem Ziel (`own_total` inkl.
   Wertungsplatten). Die Summe der 8 eigenen Plattenausgaben muss
   daher zur Platten-Komponente von `own_total` passen. Das ist ein
   kostenloser Korrektheitstest der Labels -- und zugleich der Test auf
   REDUNDANZ: sagen beide Koepfe dasselbe, ist der Gewinn nur die
   Zerlegung, nicht neue Information.

### Stufe B: Einbau in die Blattbewertung -- OFFEN, eigene Vorregistrierung

Nutzer: *"wie wir es in die blattbewertung dann einbauen gilt es noch
anzusehen."* Hier wird ABSICHTLICH nichts festgelegt. Notiert sind nur
die Optionen, damit die spaetere Entscheidung nicht bei Null anfaengt:

- Gewichteter Zuschlag analog Floor-Shaping (das mit +11pp
  arena-bestaetigt ist -- Hand-Terme in der Blattbewertung koennen
  also tragen).
- Nur die AKTIVEN Kriterien einrechnen, gewichtet mit ihrem
  Punktwert.
- Differenz eigene minus Gegner-Seite (die Denial-Richtung) statt nur
  eigene.
- Nur in bestimmten Runden (die Plattenwirkung ist in R5 exakt
  geloest, dort waere der Term reine Doppelung).

Bedingungen, die fuer JEDE Variante gelten: `MOSAIC_*`-Knopf mit
Default 0, Paritaets-Hash
`8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423`
haelt, Arena-Entscheid (kein Offline-Verdikt), **Platt-B als Waechter**
gegen Kalibrierungs-Schaden durch Doppelzaehlung, und die HEURISTIK
bleibt unangetastet, damit der Arena-Massstab fix bleibt.

## Terminbedingung (nicht verhandelbar)

Ein neues Cache-Feld erzwingt einen `VALUE_SCHEMA_VERSION`-Bump, und
der Schema-Stand steckt im Cache-Schluessel. **Alle Task-D-Arme teilen
denselben Cache** -- ein Bump vor dem Ende des Sweeps liesse `pw025` auf
einem anderen Korpus trainieren als `vw04`/`vw08` und machte den Sweep
wertlos (dieselbe Fehlerklasse wie der Traegermanifest-Beinahefehler von
heute). Der Plattenkopf startet daher **nach Abschluss von Task D**.

## Kosten

Cache-Neubau nach dem Schema-Bump ~1h (2.945 Dateien), Training ~3,5h
GPU je Arm, Stufe A braucht ein Kontroll-Training NICHT neu (die
Kontrolle ist `v21_2d` bzw. der jeweils aktuelle Stand mit Kopf-Gewicht
0). Stufe B zusaetzlich ~1,5h CPU je Arena-Arm.

---
## REVISION 2026-08-10: WAHRSCHEINLICHKEITEN statt Punktwerte (Nutzer-Entscheid)

*"dann machen wir den plattenkopf mit wahrscheinlichkeiten"*.

### Warum das die staerkere Fassung ist

Der Punktwert-Entwurf war angreifbar, und der Nutzer hat den Angriff selbst
geliefert: Punkte je Kriterium sind ein ZERLEGTER ABLESEKOPF auf etwas,
das die bestehenden Koepfe schon tragen -- ihr Ziel ist der Endpunktestand,
in dem die Kriterien enthalten sind. Dazu kam der Befund vom 2026-08-10,
dass fuer Kriterium 6 auch die REPRAESENTATION vollstaendig ist: die
Brettkanaele fuehren `+14` SPECIAL-Feld, `+15` gesperrt, `+6` belegt --
raeumlich, die Reihe steckt in der Geometrie. Neue Information haette ein
Punktwert-Kopf also nicht gebracht.

**Eine Wahrscheinlichkeit ist dagegen eine andere Groesse als alles, was wir
heute haben**: der Glaube ueber ein zukuenftiges binaeres Ereignis. Genau
das fehlt einer Blattbewertung mitten im Spiel, und genau daran ist der
Stapel-Aufloeser gescheitert -- er verbuchte die 3 Bonuspunkte
BEDINGUNGSLOS, obwohl sie nur anfallen, wenn das Feld am Ende belegt ist.
Mit `P(Feld am Ende leer)` waere der erwartete Beitrag `P · (-3)` statt
einer festen Zahl.

### Zielgroessen (Labels weiter gratis und exakt aus dem Endbrett)

| Kriterium | natuerliche Groesse |
|---|---|
| **6 Spezialfelder** | **P(Feld am Spielende noch leer)**, je der 9 Spezialfelder -- der Fall, um den es die ganze Untersuchung ging |
| 0/1/2/7 Reihen, Spalten, Diagonalen, Farbenreiche | P(Bedingung am Ende erfuellt), je Linie |
| 5 Eckplatten | P(Eckplatte am Ende voll), je Ecke |
| 3 Mehrfarbige Felder | P(alle Wildcard-Felder belegt) |
| 4 Aeussere Felder | **KEINE Wahrscheinlichkeit** -- additive Zaehlung (+1 je Randfliese). Bleibt als erwartete Anzahl, normiert. Ehrlich vermerkt: hier passt die Wahrscheinlichkeits-Fassung nicht, und das wird nicht schoengerechnet. |

Beide Seiten (eigene und Gegner) wie bisher, Verlust weiter **maskiert auf
die aktiven Kriterien** (Korrektur vom 2026-08-09 gilt unveraendert: die
vier Ausschluss-Paare machen unmaskiertes Training zur
Train/Inferenz-Fehlanpassung).

Labels: alles aus dem Endbrett ableitbar, also weiter gratis. Neu ist nur,
dass das Label ein **Indikator** (0/1) statt eines Punktwerts ist -- und
damit ein Wahrscheinlichkeits-Ziel mit Kreuzentropie, wie beim WDL-Kopf.

### Was sich an den Entscheidungsregeln aendert

Stufe A bleibt der Aufbau, aber die Pflicht-Metrik wird eine
**Kalibrierungs**-Metrik statt eines Regressionsmasses: Brier je Kriterium
gegen eine Konstanten-Basislinie (Korpus-Grundrate desselben Kriteriums).
Kriterium 6 bleibt PFLICHT.

Neu und wichtig: **Kalibrierung ist hier die Entscheidungsgroesse, nicht
Trefferquote.** Der Nutzen entsteht nur, wenn `P · Punktwert` ein
brauchbarer Erwartungswert ist -- ein schiefer, aber gut trennender Kopf
waere fuer diesen Zweck wertlos. Platt-Steigung je Kriterium mitfuehren.

Stufe B (Einbau in die Blattbewertung) wird dadurch praeziser
formulierbar als vorher: der Beitrag ist `Summe ueber aktive Kriterien von
P_Kriterium x Punktwert_Kriterium`, mit dem reihenabhaengigen Punktwert
bei Kriterium 6 (1..6 je Reihe, `round_end.rs`) statt einer Konstante.
Bedingungen unveraendert: Knopf Default 0, Paritaets-Hash, Arena-Entscheid,
Platt-B als Waechter, Heuristik unangetastet.

### Praezisierung des Rechtfertigungsgrunds (Nutzer 2026-08-10)

*"das ist dann eine neue info -- bzw. eine konkretere"*. Die zweite
Formulierung ist die richtige, und der Unterschied ist der eigentliche
Grund fuer diesen Kopf:

Die Information ist nicht NEU -- der Ausgang steckt im Value-Ziel, das Netz
weiss implizit etwas darueber, ob die Spezialfelder am Ende leer bleiben.
Sie ist **KONKRET**: punktweise adressierbar und damit mit dem bekannten
Punktwert multiplizierbar. Aus einer Gewinnwahrscheinlichkeit laesst sich
nicht herausrechnen, welcher Anteil auf die -3 eines BESTIMMTEN Feldes
entfaellt; aus `P(Feld leer)` und dem reihenabhaengigen Punktwert schon.

Der Rechtfertigungsgrund lautet damit nicht "das Netz weiss es nicht",
sondern **"das Netz kann es nicht beziffern, wo es gebraucht wird"** --
genau die Luecke, in die der Stapel-Aufloeser mit seiner bedingungslosen 3
gefallen ist. Er brauchte `P x Punktwert` und hatte eine Konstante.

Konsequenz fuer Stufe A: die Konsistenz-Pruefung gegen den Punkte-Kopf
(Punkt 4 oben) bleibt der Redundanz-Test, aber ihr Ausgang ist jetzt
vorhersagbar und NICHT disqualifizierend -- Uebereinstimmung ist zu
erwarten, weil dieselbe Information zugrunde liegt. Disqualifizierend
waere nur, wenn die Zerlegung nicht KALIBRIERT ist, denn ohne
Kalibrierung ist `P x Punktwert` kein Erwartungswert.

## Atom-Zuschnitt je Wertungsplatte (aus dem Code verifiziert, 2026-08-10)

Nutzer-Vorgabe: die Auflösung ist die **adressierbare geometrische
Einheit**, nicht die Platte -- *"wie hoch ist die wahrscheinlichkeit fuer
diagonale 1 / diagonale 2 ... fuer spalte 1, 2, 3 usw. ... fuer slot 1,1;
1,3; 3,1; 3,3"*. Ein Ausgabewert je Atom, Punktwert bekannt und konstant
multipliziert.

| ID | Kriterium | Atom | Anzahl | Punktwert je Atom | Quelle |
|----|-----------|------|--------|-------------------|--------|
| 0 | Horizontale Reihen | Reihe r vollstaendig (6 Fliesen) | 6 | +3 | `score_horizontal_rows` |
| 1 | Vertikale Reihen | Spalte c vollstaendig | 6 | +7 | `score_vertical_rows` |
| 2 | Diagonale Reihen | Diagonale d vollstaendig | 2 | +10 | `score_diagonal_rows` |
| 3 | Mehrfarbige Felder | ALLE Wild-Felder belegt (Konjunktion) | 1 | 2 x wild_total | `scoring.rs:210` |
| 4 | Aeussere Felder | Randfeld (r,c) belegt | 20 | +1 | `scoring.rs:222` |
| 5 | Eckplatten | Eckslot alle 4 Felder belegt | 4 | +3/+3/**+8/+8** | `scoring.rs:235` |
| 6 | Spezialfelder | Spezialfeld am Ende LEER | 9 (je Kuppelslot) | -3 | `scoring.rs:255` |
| 7 | Farbenreiche Reihen | Reihe r hat >=5 Farben | 6 | +4 | `score_colorful_rows` |

**54 Ausgaben je Spieler, 108 gesamt**, maskiert auf die aktiven
Kriterien (typisch 30-40 aktive Atome je Zustand).

Eckslot-Reihenfolge = `corner_fill`: (0,0), (0,2), (2,0), (2,2)
(`scoring.rs:242`) -- die UNTEREN beiden (Slot-Reihe 2) tragen 8 Punkte.

Spezialfelder: **hoechstens ein Special-Space je Kuppelplatte**
(`dome.rs:135` und `round_end.rs:301` suchen per `.position(...)` genau
EINEN) -- damit ist die feste Ausgabezuordnung sauber die 3x3-Slot-Position.

### Korrektur: Kriterium 4 gehoert HINEIN

Der Ausschluss von Kriterium 4 in der Revision oben (*"KEINE
Wahrscheinlichkeit -- additive Zaehlung"*) war ein **Auflösungsfehler**,
keine Eigenschaft der Platte. Pro Randfeld ist es ein Bernoulli mit Wert 1,
und `Sum P(Feld belegt)` IST der Erwartungswert -- exakt, nicht
schoengerechnet. Der Ausschluss war zudem in sich widersprüchlich, weil
Kriterium 6 ebenso additiv ist und dort pro Feld formuliert wurde. **4 ist
mit 20 Atomen aufgenommen.**

### Der echte Ausreisser ist Kriterium 3

Ein einziges Konjunktionsereignis, und sein Punktwert `2 x wild_total` ist
zum Vorhersagezeitpunkt selbst noch **unsicher** -- Wild-Felder kommen mit
spaeter platzierten Kuppelplatten hinzu. `P x Punktwert` hat hier einen
zweiten unbekannten Faktor. OFFEN (Nutzer-Entscheidung): entweder
`P(alle belegt)` mal dem AKTUELLEN `wild_total` (nach unten verzerrt,
solange Platten fehlen), oder ein zweiter Ausgabewert fuer `E[wild_total]`,
oder fuer dieses eine Kriterium eine Regression auf den Erwartungswert
`2 x E[wild_total * 1{alle belegt}]` -- letzteres exakt, aber die einzige
Nicht-Wahrscheinlichkeit im Kopf.

### Interaktion 5 x 6 -- von keinem Ausschluss abgefangen

5 und 6 liegen in VERSCHIEDENEN Paaren ((2,5) und (6,3)), koennen also
**gleichzeitig aktiv** sein. Eine Spezialkuppel im unteren Eckslot ist dann
8 (Ecke) + 5 oder 6 (Spezialfliese reihenabhaengig, `round_end.rs:327`)
+ 3 (vermiedene Strafe) wert -- und das sind genau die Slots, die der Nutzer
laut seiner Taktik meidet ("in reihe 3 der slots will ich keine
spezialkuppeln"). Das ist der dokumentierte Fall, in dem die Taktik sich
umkehren muss, und die erste Stelle, an der der Kopf einen echten
Mehrwert gegenueber der Erfahrungsregel liefern kann. Als deskriptive
Auswertung in Stufe A vorgemerkt.

### Kriterium 3 IST eine Wahrscheinlichkeit -- Regression zurueckgezogen (Nutzer 2026-08-10)

*"sollt ich eigentlich auch mit wahrscheinlichkeiten abbilden koennen. 9
platten mit dem joker gibt es und dann schau ich mir wieviel bei mir liegen,
wieviel platten ich noch bekommen kann und ob ich die jokerfliesen schliessen
kann."*

Richtig, und meine Regressions-Empfehlung ist damit zurueckgezogen. Der
Denkfehler: ein **Zaehler ist eine Summe von Indikatoren**, `E[N] = Sum P(..)`.
Eine Anzahl ist also nie ein Grund, die Wahrscheinlichkeitsfassung zu
verlassen -- sie heisst nur, dass die Atome falsch gewaehlt waren.

**Poolstruktur (verifiziert, `dome.rs:208`)**: 18 Platten mit je 4 Feldern,
davon **9 mit genau einem Spezialfeld** (`s()`, bonus_points=3) und **9 mit
genau einem Jokerfeld** (`w()`, bonus_points=0). Nie beides auf derselben
Platte. Die Nutzer-Angabe "9 platten mit dem joker" steht woertlich im Pool.

Kriterium 3 ist damit der **Spiegel von Kriterium 6**, kein Ausreisser:

| ID | Atom | Anzahl | Wert |
|----|------|--------|------|
| 6 | Slot s traegt am Ende eine Spezialplatte, deren Spezialfeld LEER ist | 9 | -3 |
| 3 | Slot s traegt am Ende eine Jokerplatte, deren Jokerfeld BELEGT ist **UND** alle Jokerfelder des Bretts sind belegt | 9 | +2 |

**Die Summe ist EXAKT der Erwartungswert.** Sei C = "alle Jokerfelder belegt"
und A_s das Atom von Slot s. Tritt C ein, hat jede Jokerplatte ihr Feld
belegt, also `Sum_s A_s = N_wild`; tritt C nicht ein, sind alle A_s null.
Also `Sum_s A_s = N_wild * 1{C}` und `E[Auszahlung] = 2 * Sum_s P(A_s)` --
ohne Multiplikator, ohne `E[wild_total]`, ohne Regression.

Die Konjunktion im Atom ist unbedenklich: sie ist eine binaere Aussage ueber
das Endbrett und ihr Label bleibt gratis und exakt.

**Nebengewinn -- harte Pruefgroesse**: jedes der 9 Atome muss `<= P(C)` sein.
Das ist eine Ungleichung, die in der Kalibrierungspruefung getestet wird,
statt gehofft zu werden. (Verletzung = der Kopf hat die Konjunktion nicht
gelernt, unabhaengig vom Brier.)

**Atomzahl aktualisiert**: 0:6, 1:6, 2:2, **3:9** (statt 1), 4:20, 5:4, 6:9,
7:6 = **62 je Spieler, 124 gesamt**. Kein Kriterium mehr ausserhalb der
Wahrscheinlichkeitsfassung -- die Tabelle oben und die "Ausreisser"-Notiz zu
Kriterium 3 sind damit ueberholt.

## VALIDIERUNG auf echten Endbrettern (2026-08-10) -- ein Kriterium wackelt

Nutzer-Frage: *"hast du das auf ein paar spielsituationen validiert oder
einfach mal blind gebaut?"* -- zu Recht gestellt. Validiert war NICHTS, nur
die Code-STRUKTUR (9 Joker-/9 Spezialplatten, Auszahlungsformeln). Jetzt
geprueft: `scoring.rs::plattenkopf_atom_identities_hold_on_real_end_boards`
(`#[ignore]`), 24 Endbretter aus 12 Partien via neuem Treiber
`round_transition::drive_to_game_end`.

### Was haelt: die Identitaeten

| Behauptung | Ergebnis |
|-----------|----------|
| `-3 * Sum_s A6_s == score_empty_special_fields` | **haelt, 24/24** |
| `2 * Sum_s A3_s == score_wild_fields` | **haelt, 24/24** |
| jedes A3-Atom `<=` Gesamtbedingung C | **haelt, 24/24** |
| 9 Atome je Kriterium (= 9 Kuppelslots) | bestaetigt |

Diese Pruefung ist **spielweise-unabhaengig** -- die Identitaeten gelten fuer
jedes Brett, unabhaengig davon, wie es entstand.

### Was traegt: Kriterium 3

- Grundrate der Bedingung "alle Jokerfelder belegt": **11/24 = 45,8 %**.
  Weit von 0 und 1 -- fast ideal fuer einen Wahrscheinlichkeitskopf.
- Jokerfelder je Brett: Mittel **3,79**, Spanne **2 bis 5**. Der
  Multiplikator schwankt also wirklich. Die Nutzer-Zerlegung in 9 Atome war
  damit nicht nur eleganter als mein `P x aktuelles wild_total`, sondern
  noetig: ein fester Multiplikator haette um bis zu ~1,5 Felder danebengelegen.

### Was NICHT traegt: Kriterium 6 (Grundrate fast degeneriert)

- Spezialfelder je Brett: Mittel **4,21**
- davon LEER: Mittel **4,04** (Spanne 2 bis 6)

Das Atom ist also in **~96 %** der Faelle wahr. Eine fast konstante
Zielgroesse: der Kopf lernt "leer", erreicht einen praechtigen Brier von
~0,04 und unterscheidet nichts. Und das ist ausgerechnet das Kriterium, um
das die ganze Begruendung dieses Kopfes gebaut ist (die -3-Strafe, die
Stapelzug-Taktik des Nutzers, der bedingungslose Bonus im Aufloeser).

**VORBEHALT, der das entscheidet**: diese Partien spielen das Drafting NAIV
(`drive_drafting_to_leaf_naive`). Ein Spezialfeld zu fuellen erfordert
absichtliches Spiel -- genau die Nutzer-Taktik. Die 4,04 sind damit eine
UNTERGRENZE fuers Leerbleiben. Ausserdem sind 24 Bretter wenig (45,8 % hat
ca. +-10pp).

### Konsequenz fuer die Reihenfolge

**Vor dem Bau** gehoert die Grundraten-Messung auf CHAMPION-Partien
(vorhandener Korpus, kein neuer Lauf noetig -- die Endbretter liegen in den
HDF5-Dateien). Entscheidungsregel vorab:

- Grundrate "Spezialfeld leer" unter Champion-Spiel **> 90 %** ⇒ Kriterium 6
  ist als Wahrscheinlichkeit fast wertlos; der Kopf braucht dann entweder
  eine Klassen-Gewichtung, die die seltenen Fuellungen hervorhebt, ODER
  Kriterium 6 wird als Atom gestrichen und der Kopf traegt nur die anderen.
- Grundrate zwischen **60 und 90 %** ⇒ tragfaehig, Kalibrierung mit
  Klassenungleichgewicht auswerten (Brier gegen die Grundrate, nicht gegen
  0,25).
- Unter **60 %** ⇒ unproblematisch, Bau wie vorregistriert.

Ohne diese Messung waere ein Kopf gebaut worden, dessen Pflicht-Kriterium
eine Konstante vorhersagt.

### Die 96 % sind STRUKTURELL, nicht naiv-spiel-bedingt (Nutzer 2026-08-10)

*"das spezialfeld zu fuellen ist auch schwieriger. dafuer muessen die 3
anderen felder der kuppelplatte erst gefuellt werden. die jokerfelder koennen
direkt belegt werden"*

Woertlich im Code bestaetigt:

- `DomeSpace::special()` startet mit `is_locked: true` (`dome.rs:44`).
- `try_unlock_special` (`dome.rs:140`): "Schaltet den SPECIAL-Space frei,
  sobald die anderen 3 gefuellt sind" -- und die anderen drei sind `Normal`
  mit `required_color`, also drei BESTIMMTE Farben auf derselben Platte.
- `accepts_special` verlangt `!is_locked` (`dome.rs:75`), `check_special_trigger`
  feuert erst dann (`round_end.rs:307`).
- Ein Jokerfeld dagegen: `accepts(color) -> true` fuer JEDE Farbe
  (`dome.rs:68`), ohne Vorbedingung.

**Kosten je Feld**: Spezialfeld = 4 Platzierungen mit 3 Farbauflagen,
Jokerfeld = 1 Platzierung ohne Auflage.

**Folge fuer den Vorbehalt oben**: die 4,04-von-4,21-Leerrate ist damit KEIN
Artefakt des naiven Draftings, sondern strukturell. Die Champion-Messung
wird die Zahl senken, nicht aufloesen. Die vorregistrierten Schwellen
bleiben gueltig, aber der erwartete Ausgang ist ">90 %", also der Fall, der
eine Klassen-Gewichtung erzwingt.

**Und das dreht die Aufgabe, statt sie zu erledigen.** Uninformativ ist nur
die GRUNDRATE, nicht das Kriterium: Wert entsteht, wenn der Kopf die
seltenen ~4 % UNTERSCHEIDET, und dort steckt viel Wert, weil eine gefuellte
Spezialfliese reihenabhaengig 1..6 Punkte traegt (`round_end.rs:327`) -- in
den unteren Slots (Musterreihen 5/6) die teuersten UND schwersten zugleich.
Genau die Preisfrage, die der Nutzer beim Slot-Zuschnitt von Hand macht
("in reihe 3 der slots will ich keine spezialkuppeln").

**Auswertung entsprechend anpassen**: Entscheidungsgroesse fuer Kriterium 6
ist nicht der rohe Brier (der wird bei Grundrate 0,96 trivial gut), sondern
der **Brier-Skill-Score gegen die Grundrate** plus die Trennleistung auf der
Minderheitsklasse. Ein Kopf, der konstant 0,96 ausgibt, muss dabei mit
Skill 0 herauskommen -- das ist der Trivialitaets-Wachhund.

**Repraesentation ist ausreichend**: die Brettkanaele tragen `+15 locked`,
`+6 placed_special` und den Fuellstand der Normalfelder, "drei andere
gefuellt" ist daraus ableitbar (`features.rs::write_board_channels_direct`).
Der Kopf kann also lernen, wie weit eine Platte vom Freischalten entfernt
ist -- die eigentlich informative Groesse.

### Unabhaengige Bestaetigung der erwarteten Grundrate -- VOR der Messung notiert

Die oben vorregistrierte Grundraten-Messung fuer Kriterium 6 hat eine
unabhaengige Vorab-Evidenz, die mir beim Aufschreiben nicht praesent war:
`watchlist_v20_zwischenlese.md` (10 Mensch-vs-Champion-Partien, Commit
11dd012) hat genau diese Groesse schon gemessen, unter CHAMPION-Spiel:

| | Mensch | KI (`v20_2d_opp_brierbest@400`) |
|---|--------|--------------------------------|
| Special-Unlock in Runde 2 | **9 / 10** Partien | **0 / 10** |
| Special-Unlock ueberhaupt nie | 1 / 10 | **6 / 10** |

Die KI schaltet in 6 von 10 Partien NIE ein Spezialfeld frei und nie vor
Runde 4. Der erwartete Ausgang der Messung (">90 % leer", also der Fall,
der eine Klassen-Gewichtung erzwingt) ist damit **bestaetigt, bevor sie
laeuft** -- die Messung bleibt trotzdem noetig, weil sie die Rate BEZIFFERT
und je Slot aufloest, was die Watchlist nicht tut.

**Und das dreht das Argument fuer Kriterium 6 ins Positive.** Eine fast
konstante Zielgroesse ist ein Problem fuer den Brier, aber die dahinter
liegende Schwaeche ist der bestbelegte Struktur-Rueckstand der KI gegen
den Nutzer -- ueber die v19- UND v20-Aera hinweg, und exakt der
Dossier-Punkt "Spezial-Kuppeln in die ERSTEN (schnellen) Reihen".
Kriterium 6 zielt also nicht auf ein Randphaenomen.

**Folge fuer die Entscheidungsregel oben**: der ">90 %"-Zweig ist damit der
ERWARTETE, nicht der Ausnahmefall. Er lautet also nicht mehr "Kriterium 6
streichen ODER Klassen-Gewichtung", sondern: **Klassen-Gewichtung, und
Streichen nur, wenn die Trennleistung auf der Minderheitsklasse
nachweislich bei Null liegt** (Brier-Skill-Score <= 0 gegen die Grundrate).
Ein Kriterium wegen Klassenschieflage zu streichen, das die dokumentierte
Hauptschwaeche adressiert, waere der falsche Schluss aus einer richtigen
Metrik-Beobachtung.

## GRUNDRATEN GEMESSEN auf Champion-Partien -- Mittelband, Bau freigegeben (2026-08-10)

Nutzer-Auftrag: *"kannst du auf den bestehenden korpus ein modell mit dem
platten head trainieren und gegen den champ laufen lassen"*. Erste Stufe
davon -- die vorregistrierte Grundraten-Messung -- ist gelaufen.
Instrument: `tools/plattenkopf_labels.py` (neu), 800 Endbretter aus 40
`selfplay_v20wdl_*`-Dateien.

| Groesse | Messwert |
|---------|----------|
| Kriterium 6: Anteil LEERER Spezialfelder je Brett | **83,3 %** |
| Spezialfelder je Brett | 4,50 |
| Kriterium 3: Grundrate "alle Jokerfelder belegt" | **42,0 %** |
| Jokerfelder je Brett | 4,50, Spanne **1 .. 8** |
| Identitaeten gegen `scoring_tile_points` | **94/94 bestaetigt** |

### Verdikt nach der vorab festgelegten Regel

83,3 % liegt im Band **60-90 %** ⇒ **tragfaehig**, Auswertung mit
ungleichgewichts-bewusster Kalibrierung (Brier-Skill-Score gegen die
Grundrate). NICHT der Zwangsfall ">90 %", der eine Klassen-Gewichtung
erzwungen haette.

**Meine Vorhersage war falsch und das ist folgenreich.** Ich hatte ">90 %"
als "erwarteten Ausgang" notiert, gestuetzt auf die naive-Spiel-Messung
(4,04 von 4,21 leer = 96 %) und das Struktur-Argument. Champion-Spiel fuellt
mehr Spezialfelder als naives -- die 96 % waren also zum TEIL doch ein
Spielweise-Artefakt, nicht rein strukturell. Weil die Schwelle vorab stand,
aendert das den Zweig der Entscheidungsregel, nicht bloss eine Fussnote.

Kriterium 3 bestaetigt sich (42,0 % gegen 45,8 % auf den synthetischen
Brettern). Die Spanne **1 bis 8** Jokerfelder ist weiter als die dort
gemessene 2..5 -- ohne die Zerlegung in 9 Atome laege der Multiplikator um
bis zu sieben Felder falsch.

### Label-Beschraenkung des Bestandskorpus (bleibt bestehen)

Der letzte Datensatz einer Partie ist der letzte TILING-SCHRITT, nicht der
Zustand nach Spielende -- exakte Endlabels liegen NICHT vor. Gemessen:
Kriterium 6 ist in 101/120 Brettern schon 6 Datensaetze vor Schluss final,
Kriterium 3 in 109/120; der Restfehler ist klein und unterzaehlt
Fuellungen systematisch. Tragbar fuer die Machbarkeits-/Staerkeprobe,
NICHT fuer einen Champion-Kandidaten -- der braucht eine Generierung, die
die Endlabels stempelt.

### Restliche Abfolge fuer die Probe

1. Kopf in `engine/py/neural_net.py` (18 Ausgaben: 9 Atome je Kriterium 3/6),
   Verlust maskiert auf die in der Partie AKTIVEN Kriterien.
2. Labels in den Cache -> Schema-Bump -> Cache-Neubau (~3h). Der Bump war
   bis zum Abschluss von Task D gesperrt, damit `pw025` nicht auf einem
   anderen Korpus trainiert -- Task D ist seit heute geschlossen, die Sperre
   ist weg.
3. Training (~3,5h GPU), Rezept wie der Champion (warm-start, lr 5e-5,
   cosine, `--value-head wdl --select-by-brier`).
4. **Beide** Auswertungen, weil eine allein nicht interpretierbar ist:
   Arena-Gating vs Champion (~1-1,5h CPU) UND Brier-Skill-Score je Kriterium.
   Ein Nullergebnis in der Arena ohne die Kalibrierung liesse offen, ob der
   Kopf nichts gelernt hat oder es gelernt hat und nicht hilft.

## RAUCHTEST 2026-08-10: c6 traegt, c3 NICHT -- Bauzuschnitt geaendert

Instrument: `tools/plattenkopf_smoketest.py` (neu). Zweck war ausdruecklich,
die Nachtschicht zu schuetzen: sind die Atome aus den vorhandenen Merkmalen
lernbar, BEVOR Schema-Bump, Cache-Neubau (~3 h) und Training (~3,5 h)
bezahlt werden. Kleines MLP direkt auf `state_to_tensor` + `state_to_planes`
(also OHNE gelernten Rumpf -- die schwierigere und damit konservative
Variante), 80.000 Zustaende aus 677 Partien, Schnitt NACH PARTIE,
Fruehstopp auf dem mittleren Val-Skill.

| Kriterium | Grundrate | Brier | Brier(Grundrate) | **Skill** | Wachhund |
|-----------|-----------|-------|------------------|-----------|----------|
| **c6** Spezialfelder | 0,441 | 0,105 | 0,247 | **+0,574** | +0,000 |
| **c3** Jokerfelder | 0,199 | 0,165 | 0,159 | **-0,036** | +0,000 |

c3 verschlechtert sich zudem monoton mit dem Training (Epoche 1 bis 4:
-0,036 / -0,113 / -0,173 / -0,189). Der Trivialitaets-Wachhund liefert beide
Male exakt 0 -- die Metrik ist korrekt geeicht.

### Warum c6 lokal und c3 global ist

c6 ist eine **lokale** Vorhersage: ob ein Slot sein Spezialfeld fuellt, haengt
fast nur am Zustand dieses Slots (sind die anderen drei Felder gefuellt?), und
der steht in den Brettkanaelen. Deshalb tragen die 9 Atome 9-mal Signal.

c3 ist ein **globales Bit**: alle 9 Atome haengen ueber dieselbe Bedingung
"alle Jokerfelder am Ende belegt" zusammen, der Slot-Teil ist ohnehin sichtbar.
Die effektive Stichprobe sind also 542 Partien mal EIN Bit, nicht mal neun.
Das ist zu wenig Signal -- und es entlarvt die Grundraten-Betrachtung von
oben als unzureichend: eine gesunde Grundrate (42 %) sagt nichts darueber, ob
genug UNABHAENGIGE Beobachtungen dahinterstehen.

### Bauzuschnitt (Regel-Anwendung)

Die vorregistrierte Regel lautet "nur EIN Kriterium schlaegt die Grundrate ⇒
das andere gehoert vor dem Bau geklaert". Angewandt:

- **c6 wird gebaut**: 9 Ausgaben, Verlust maskiert auf Partien mit aktiver
  Platte 6.
- **c3 wird NICHT mitgebaut.** Ein toter Block kostet Kapazitaet und
  Gradientenanteil, ohne etwas zu tragen -- genau der Fehler, den der
  Ownership-Kopf schon einmal gemacht hat (inert, Gewicht 0, seit 2026-07-28
  geschlossen).
- **c3 bleibt offen**, nicht verworfen. Denkbare Wiedervorlage: EIN Ausgang
  fuer `P(alle Jokerfelder belegt)` statt neun korrelierter, und erst wenn ein
  groesseres Fenster mehr unabhaengige Partien liefert. Die
  Exaktheits-Identitaet (`2 x Summe der Atome` = Auszahlung) bleibt dabei
  gueltig, sie war nie das Problem.

### Was der Rauchtest gekostet und gespart hat

Gekostet: ~20 Minuten GPU. Gespart: ein Nachtlauf, der einen Kopf mit einem
toten Block trainiert haette -- und dessen Arena-Nullergebnis nicht
interpretierbar gewesen waere ("Kopf lernt nichts" vs "lernt es, hilft
nicht"). Zwei Fehlwege im Test selbst sind protokolliert: Schnitt nach INDEX
statt nach Partie (alle Zustaende einer Partie tragen dasselbe Label, das
Modell lernt die Partie) und fehlender Fruehstopp (der Endstand misst dann
das Ueberlernen statt der Lernbarkeit; c3 sah dadurch mit -0,494 viel
schlechter aus als mit -0,036).

## STUFE A im grossen Zuschnitt (2026-08-10 nachts): c6 bestaetigt, Slot-Gradient entdeckt

400 Dateien, **300.000 Zustaende aus 2.537 Partien**, Schnitt nach Partie
(2.030 / 507), Fruehstopp auf dem mittleren Val-Skill.
Log: `logs/plattenkopf_stufeA.log`.

| Kriterium | Grundrate | Brier | Brier(Grundrate) | **Skill** |
|-----------|-----------|-------|------------------|-----------|
| **c6** | 0,442 | 0,0895 | 0,2466 | **+0,637** |
| c3 | 0,201 | 0,1599 | 0,1604 | **+0,004** |

c6 verbessert sich mit der Stichprobe (+0,574 bei 677 Partien -> **+0,637**
bei 2.537). **c3 bleibt bei null und faellt mit jeder weiteren Epoche**
(+0,004 / -0,123 / -0,185 / -0,232) -- auf zehnfacher Stichprobe bestaetigt:
kein Signal. Der Ausschluss von c3 steht.

### DER BEFUND: monotoner Slot-Gradient -- die Nutzer-Taktik, gemessen

| Slot | Grundrate "am Ende LEER" | Brier | Skill | Platt-Steigung |
|------|--------------------------|-------|-------|----------------|
| 0 (oben links) | **0,062** | 0,0455 | +0,219 | 0,502 |
| 1 | 0,101 | 0,0932 | **-0,022** | 0,436 |
| 2 | 0,229 | 0,0874 | +0,505 | 0,570 |
| 3 | 0,256 | 0,0780 | +0,590 | 0,753 |
| 4 | 0,303 | 0,1021 | +0,516 | 0,627 |
| 5 | 0,494 | 0,1288 | +0,485 | 0,651 |
| 6 | 0,777 | 0,1113 | +0,358 | 0,498 |
| 7 | 0,856 | 0,0786 | +0,364 | 0,806 |
| 8 (unten rechts) | **0,898** | 0,0807 | +0,120 | 0,801 |

**Monoton von oben nach unten**, und die Spannweite ist enorm: ein
Spezialfeld in der UNTEREN Slot-Reihe bleibt in ~84 % der Partien leer, in
der OBEREN nur in ~13 %.

Das ist die Nutzer-Aussage vom 2026-08-10 woertlich bestaetigt: *"die kuppel
hat 3x3 slots. in der reihe 3 der slots (also musterreihe 5 & 6) ist es sehr
schwer/langwierig ueberhaupt eine spezialkuppel abzuschliessen. sprich ich
will in diesen unteren slots keine spezialkuppeln haben."* Der Korpus sagt
dasselbe in Zahlen, und der Mechanismus stand schon fest (`dome.rs:140`:
Freischaltung erst, wenn die anderen drei Felder gefuellt sind -- und die
unteren Musterreihen sind die traegsten).

**Damit ist die Slot-weise Fassung nicht Kosmetik, sondern der Kern.** Ein
Aggregat ueber alle Spezialfelder wuerde diesen Gradienten vollstaendig
verschlucken -- genau der Fehler, den die Heuristik mit ihrem
`-3 * special_empty` macht.

### Kalibrierung: der Kopf ist systematisch UEBERMUETIG

Alle Platt-Steigungen liegen zwischen **0,44 und 0,81**, also unter 1 --
die Logits sind zu extrem. Fuer die Stufe-A-Entscheidung heisst das:
Trennleistung ja, Erwartungswert-Taugllichkeit **erst nach Platt-Korrektur**.
`P x Punktwert` mit den Rohausgaben waere systematisch verzerrt.

Konsequenz fuer Stufe B (Einbau in die Blattbewertung): die Platt-Parameter
je Slot muessen mitgefuehrt werden, analog zur Anzeige-Kalibrierung des
Champions in `server.py` (`_DISPLAY_CAL_A/_B`). Als Pflichtpunkt vorgemerkt.

### Ausnahme, die auffaellt

**Slot 1 hat Skill -0,022** -- der einzige negative. Grundrate 0,101, also
seltenes Ereignis, und der Kopf trifft es nicht. Vor Stufe B zu klaeren, ob
das an der Seltenheit liegt oder an etwas Strukturellem (Slot 1 ist
oben-mitte; kein offensichtlicher Sonderstatus). Kein Ausschlussgrund, aber
eine offene Stelle.

## MODELLSEITE GEBAUT (2026-08-10 nachts) -- Rest der Kette noch offen

`engine/py/neural_net.py`, additiv nach dem `endgame_head`-Muster:

- `PLATE_HEAD_SLOTS = 9` (3x3 Kuppelslots; hoechstens EIN Spezialfeld je
  Platte, `dome.rs:135` / `round_end.rs:301` suchen genau eines).
- Konstruktor-Flag `plate_head=False` in **beiden** Klassen (`MosaicNet`,
  `Mosaic2DNet`); Kopf = `Linear(hidden, value_hidden) -> ReLU ->
  Linear(value_hidden, 9)`, **Logits ohne Sigmoid** (BCEWithLogits im
  Training, Platt-Korrektur nachtraeglich -- die gemessenen Steigungen lagen
  bei 0,44-0,81).
- Ausgabe **ZULETZT** im Tupel angehaengt -- bestehende Leser indexieren
  positionsbasiert und bleiben unberuehrt.
- `plate_head_present(state)` erkennt den Kopf AUS DEM CHECKPOINT,
  `build_model_from_checkpoint` reicht das durch (Muster
  `endgame_head_present`).

**Verifiziert**: beide Klassen liefern ohne Flag unveraendert viele Ausgaben,
mit Flag eine mehr der Form `(N, 9)`; Rundlauf Speichern/Laden erkennt den
Kopf; und der **Champion laedt unveraendert** (`plate_head: False`, 8
Ausgaben wie zuvor).

### Was noch fehlt -- ausdruecklich NICHT gebaut

1. **Labels in den Cache**: `tools/plattenkopf_labels.py` liefert die Atome,
   der Einbau in `MosaicDataset` fehlt.
2. **Cache-Key**: Suffix `+plate_v1` NUR bei gesetztem Flag anhaengen (Muster
   `+enc2d_v1`, Zeile ~1142). **KEIN `VALUE_SCHEMA_VERSION`-Bump** -- der
   wuerde den vorhandenen v21-Cache entwerten, und das ist unnoetig, weil die
   Plattenlabels ein eigenes, optionales Feld sind.
3. **train.py**: Verlustterm mit Maskierung auf Partien mit aktiver Platte 6,
   plus ein `--plate-head`-Flag.
4. **Integrationsprobe**: Mini-Cache auf ~10 Dateien + 1 Epoche, BEVOR der
   volle Lauf startet.

Bewusst in dieser Reihenfolge: Punkt 4 ist der Schutz gegen einen verlorenen
Nachtlauf, und die Modellseite ist der Teil, der isoliert verifizierbar war.

## REPLIKATION auf der v19-Generation: der Slot-Gradient ist Spielstruktur

Gleicher Zuschnitt auf `selfplay_v19wdl*` (400 Dateien, 300.000 Zustaende aus
**2.530 Partien**), also einer ANDEREN Generator-Aera.
Log: `logs/plattenkopf_stufeA_v19.log`.

| Groesse | v20-Korpus | v19-Korpus |
|---------|-----------|-----------|
| c6-Skill | +0,637 | **+0,655** |
| c3-Skill | +0,004 | **-0,008** |
| Platt-Steigungen | 0,44-0,81 | 0,50-0,75 |

### Grundraten je Slot -- praktisch deckungsgleich

| Slot | v20 | v19 |
|------|-----|-----|
| 0 | 0,062 | 0,050 |
| 1 | 0,101 | 0,093 |
| 2 | 0,229 | 0,278 |
| 3 | 0,256 | 0,229 |
| 4 | 0,303 | 0,317 |
| 5 | 0,494 | 0,537 |
| 6 | 0,777 | 0,787 |
| 7 | 0,856 | 0,834 |
| 8 | 0,898 | 0,907 |

**Der Gradient ist damit generationsunabhaengig -- Spielstruktur, nicht
Champion-Verhalten.** Das ist der Beleg, der aus einem Befund eine
belastbare Groesse macht: er folgt aus der Freischaltmechanik
(`dome.rs:140`, drei Felder zuerst) und der Traegheit der unteren
Musterreihen, nicht aus der Spielweise einer Generation.

Innerhalb des Mittelbandes tauschen Slot 2 und 3 die Reihenfolge (0,229/0,256
gegen 0,278/0,229) -- die DREI-REIHEN-Bandung ist stabil, die Feinordnung
innerhalb eines Bandes nicht. Fuer den Kopf unerheblich, er lernt je Slot.

### Offene Stelle GESCHLOSSEN: Slot 1 war Rauschen

Im v20-Lauf hatte Slot 1 als einziger negativen Skill (-0,022) und war als
"vor Stufe B zu klaeren" vermerkt. Im v19-Lauf steht dort **+0,114**. Kein
struktureller Sonderfall, sondern Stichprobenrauschen bei einem seltenen
Ereignis (Grundrate ~0,10). Vermerk erledigt.

### Damit ist Stufe A abgeschlossen

- c6 lernbar und **repliziert** (+0,637 / +0,655).
- c3 ohne Skill und **repliziert** (+0,004 / -0,008) ⇒ bleibt draussen.
- Kalibrierung durchweg uebermuetig (Steigungen < 1) ⇒ Platt-Parameter je
  Slot sind Pflicht fuer Stufe B, nicht optional.
- Der Slot-Gradient ist der inhaltliche Kern und generationsstabil.

## VERDRAHTUNG: Weg 1 entfaellt, das Vorbild heisst `ownership`

Befund 2026-08-10 nachts, entscheidet die offene Frage:

**Der HDF5-Cache fuehrt `game_id` NICHT mit.** Er schreibt 19 Datasets
(`states`, `policies`, `values`, ..., `ranking_mask`, `neural_net.py:1328ff`),
die Partie-Kennung existiert nur WAEHREND des Baus. Eine Seitendatei
(`data/plate_labels_v1.json`) laesst sich beim Training also nicht anbinden --
es fehlt der Schluessel. **Weg 1 entfaellt.**

Der Dump behaelt damit nur noch die Rolle eines **unabhaengigen
Gegenpruef-Artefakts**: die im Cache gerechneten Labels lassen sich dagegen
halten. Das war nicht seine geplante Rolle, und das gehoert so gesagt.

### Das Vorbild ist `ownership` -- exakt dasselbe Muster

`_final_ownership_by_game` (`neural_net.py:890`) baut `game_id -> Labels aus
dem LETZTEN Record` und verteilt sie im Datensatz-Durchlauf
(`neural_net.py:1690`). Genau das brauchen die Plattenlabels. Die
Implementierung ist damit kein Neubau, sondern das Spiegeln eines laufenden
Mechanismus.

### Zwei Details, die das Vorbild offenlegt -- und die mein Rauchtest FALSCH macht

1. **Unvollstaendige Partien.** `_final_ownership_by_game` prueft
   `last.get("completed")` und setzt sonst `None`; im Datensatz wird daraus
   `-1` als Maskierungsmarke, im Loss maskiert. Mein Rauchtest UND der
   Label-Dump nehmen den letzten Datensatz **ungeprueft** -- bei abgebrochenen
   Partien waeren die Labels frei erfunden. Fuer die Lernbarkeitsfrage
   unerheblich (der Anteil ist klein), fuer den Trainingslauf nicht.
2. **Perspektive.** Das Ownership-Ziel ordnet nach `current_player` um, sodass
   "ich" immer zuerst steht (`c = step["state"]["current_player"]`, dann
   `first, second`). Der Plattenkopf MUSS dieselbe Konvention tragen, sonst
   lernt er die Slots des falschen Spielers. Mein Rauchtest hat
   `rec["player"]` benutzt -- vermutlich identisch, aber das gehoert geprueft,
   nicht vermutet.

### Rezept fuer die Implementierung (abgeleitet, nicht erfunden)

1. `_final_plate_c6_by_game(game_data)` nach dem Muster von
   `_final_ownership_by_game`, inklusive `completed`-Pruefung.
2. Im Datensatz-Durchlauf je Record: Labels des Spielers `current_player`
   holen, `-1` bei fehlenden.
3. Zwei Datasets: `plate_c6` (9 int8) und `plate_c6_mask` (1 int8, gesetzt
   wenn Platte 6 in `scoring_tile_ids` UND die Partie `completed` ist).
4. Cache-Key: Suffix `+plate_v1` NUR bei gesetztem Flag (Muster `+enc2d_v1`,
   `neural_net.py:1142`). **KEIN `VALUE_SCHEMA_VERSION`-Bump.**
5. `train.py`: `--plate-head`, BCEWithLogits auf die 9 Logits, maskiert.
6. **Integrationsprobe** auf ~10 Dateien + 1 Epoche, DANN der volle Lauf.

Damit ist die Verdrahtung vollstaendig spezifiziert und an einem
funktionierenden Vorbild belegt -- der Teil, der die Nacht gekostet haette,
wenn man ihn im Nachtlauf entdeckt.

### Nachtrag: die `completed`-Falle greift in diesem Korpus nicht

Gemessen an 600 Partien aus 60 zufaellig gezogenen Dateien: **0 %
unvollstaendig**, und alle letzten Datensaetze stehen in `phase=tiling`.

Folgen:
- Das erzeugte Artefakt `data/plate_labels_v1.json` (29.450 Partien aus 2.945
  Dateien -- exakt die v21-Fenstergroesse, huebscher Konsistenz-Beleg; 3,5 MiB)
  ist **gueltig**, obwohl der Dump die `completed`-Pruefung nicht macht.
- Die Pruefung bleibt in der IMPLEMENTIERUNG trotzdem Pflicht: sie ist
  defensiv, und ein kuenftiger Korpus (abgebrochene Laeufe, Server-Partien)
  kann anders aussehen. Das Vorbild `_final_ownership_by_game` macht sie
  ebenfalls, obwohl sie heute nie greift.
- Dass alle letzten Datensaetze `tiling` sind, bestaetigt den
  Label-Vorbehalt erneut: ein Zustand NACH Spielende wird nirgends
  aufgezeichnet.

Wichtiger Punkt zur Rolle des Artefakts: ein Gegenpruef-Artefakt, das
denselben Fehler wie die zu pruefende Rechnung traegt, pruefte nichts -- es
bestaetigte. Deshalb diese Messung, statt das Artefakt einfach zu benutzen.
