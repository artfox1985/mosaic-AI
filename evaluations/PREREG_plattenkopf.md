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

### Identitaeten auf dem GESAMTEN Korpus verifiziert

`tools/plattenkopf_labels.py check` ueber alle **2.945 Dateien / 29.450
Partien**: **44.068 bestaetigt, 0 abweichend, 0 uebersprungen**
(`logs/plattenkopf_identitaet_voll.log`).

Geprueft wurde je Endbrett und je in der Partie AKTIVER Platte:

    -3 * Summe(c6-Atome) == score_empty_special_fields   (Engine)
     2 * Summe(c3-Atome) == score_wild_fields            (Engine)

44.068 ist plausibel: 29.450 Partien x 2 Spieler = 58.900 Bretter, davon
tragen ~3/4 eine der beiden Platten (6 und 3 sind ein Ausschluss-Paar, es
kann also hoechstens eine aktiv sein).

Damit ist die Rechengrundlage des Kopfes **erschoepfend** belegt, nicht
stichprobenweise -- inklusive Kriterium 3, dessen Identitaet nie das Problem
war (es fehlt die Lernbarkeit, nicht die Korrektheit).

## REVISION 2026-08-10 (abends): der Kopf ist der OWNERSHIP-KOPF, c6 bekommt keinen eigenen

Nutzer-Entscheide dieser Sitzung, in der Reihenfolge, in der sie fielen.

### Prinzip

Der Kopf sagt den **unsicheren** Teil vorher, **bedingt auf den beobachtbaren**
(Existenz, Geometrie, aktive Platten). Auszahlungs-Identitaeten liegen
AUSSERHALB des Kopfes und werden aus Kopfausgaben x ablesbaren Multiplikatoren
rekonstruiert. Zielgroesse je Atom ist `P(Bedingung am Ende erfuellt)` -- wie
der Value-Kopf, nur punktweise adressierbar; bei Kriterium 6 invertiert.

### BEFUND: der Randlayer existiert seit Task #9 -- es ist der Ownership-Kopf

`_ownership_from_dome` (`neural_net.py:875`) erzeugt exakt 36 Binaerlabels
"Feld am Ende belegt" je Spielerbrett, mit Cache-Dataset, Kopf in beiden
Modellklassen und ONNX-Ausgang (72-dim, beide Seiten). Deckung:

| Kriterium | aus Ownership? |
|---|---|
| 4 Randfelder (additiv, +1) | **vollstaendig** -- `Summe P(Feld)` IST der Erwartungswert |
| 6 Spezialfelder (additiv, -3) | **vollstaendig** -- die 9 Specials sind unter den 36, `P(leer) = 1 - P(belegt)` |
| 0/1/2/3/5 | nur der Randlayer, die **Konjunktion fehlt** |
| 7 farbenreiche Reihen | **gar nicht** -- Ownership ist belegt/leer OHNE Farbe |

Folgen:
1. **c6 bekommt KEINEN eigenen Kopf** (Nutzer-Entscheid). Verwendung zur
   Laufzeit: `-3 x Summe(1 - P(belegt))` ueber die Spezialpositionen, gegatet
   auf aktive Platte 6. Die am 2026-08-10 nachts gebaute Modellseite
   (`plate_head`, `PLATE_HEAD_SLOTS=9`) wird dafuer nicht gebraucht.
2. **Eigenstaendig sind nur die Konjunktionen** -- und die sind jetzt gebaut.

`OWNERSHIP_WEIGHT = 0.0` beruht auf `+0,0017`, **5:1 bei n=6**, p=0,2188 --
gemessen am ALTEN Value-Ziel vor der WDL-Aera (`archive/history.md`). Nach den
stehenden Regeln (Fruehstopps <150 Paare nur mit Replikation; Effekte <8pp =
Seed-Rauschen) ist das kein Beleg fuer Wirkungslosigkeit, sondern gar keiner.
Die Reaktivierung ist eine EIGENE Frage mit eigener Vorregistrierung.

### Label-Fehler im bisherigen c6-Ziel (Schuld, noch offen)

`atoms_criterion6` ist UNBEDINGT und wirft "kein Special in diesem Slot" mit
"Special gefuellt" in dieselbe 0. Rechnerischer Beleg: das Mittel der neun
Slot-Grundraten ist 0,442 -- exakt die berichtete c6-Grundrate --, waehrend die
BEDINGTE Rate je Brett 0,833 betraegt; `0,833 x 4,50/9 = 0,417`. Die
Stufe-A-Zahlen (+0,637 / +0,655) trennen deshalb NICHT zwischen
Risikovorhersage und blossem Ablesen der Anwesenheit aus den Brettkanaelen.
**Offen: Stufe A bedingt neu auswerten.**

### c3 wird 9+1 (Nutzer: ein Bit ist holprig)

- 9 Ausgaenge `P(Jokerfeld in Slot i belegt)`, maskiert auf Existenz -- Signal,
  zeigt den Engpass.
- 1 Ausgang `P(alle Jokerfelder belegt)` -- das Auszahlungsereignis.
- Die gemeinsame Zerlegung bleibt Pruefgroesse AUSSERHALB des Kopfes
  (`plattenkopf_labels.py check`, Identitaet 44.068/0 unberuehrt), dazu die
  Konsistenzpruefung `P(alle) x 2 x wild_total` gegen die rekonstruierte Summe.
- Groessenordnung: 1 Bit = ~5.060 Beobachtungen (2.530 Partien x 2 Bretter),
  Slot-Ebene ~22.800. Dieselbe Verduennung wie bei c6: Rauchtest-Grundrate der
  c3-Atome 0,199 gegen Konjunktion 0,420, `0,420 x 4,50/9 = 0,21`.
- Der schwere Ausgang muss EINZELN kalibriert/bewertet werden, sonst geht er im
  Gradienten der neun leichten unter.

### "Es gibt keine toten Koepfe" (Nutzer-Korrektur)

c3 ist eine real gewertete Groesse; gescheitert war die AUFLOESUNG (9
korrelierte Ausgaenge fuer 1 Bit), nicht das Atom. Die Rauchtest-Regel muesste
danach ueber *wie fein* entscheiden statt ueber *ob* -- gestrichen wird nur,
was bei KEINER Aufloesung traegt. **Diese Umstellung der vorregistrierten Regel
ist angestossen, aber NICHT foermlich entschieden.**

### GEBAUT: Konjunktionen im Ownership-Kopf

Nutzer-Auftrag: *"bau in den ownership head die konjunktionen ein"*.

- `_conjunctions_from_dome` (`neural_net.py`): 25 Binaerlabels je Spieler --
  6 Reihen + 6 Spalten + 2 Diagonalen + 4 Eckplatten + 1 Jokerfeld-Konjunktion
  + 6 farbenreiche Reihen. Positionsabbildung `grid[sr*2+si//2][sc*2+si%2]`
  exakt wie `scoring.rs::build_grid`.
- `ownership_head` in BEIDEN Klassen auf `OWNERSHIP_TARGETS +
  CONJUNCTION_TARGETS` (72 -> 122) verbreitert, per Flag `conjunction_head`,
  Default AUS. Erkennung aus dem Checkpoint an der Ausgabebreite
  (`conjunction_head_present`) -- es gibt kein eigenes Modul, an dem man die
  Praesenz ablesen koennte.
- Cache: die 25+25 Labels haengen HINTEN an den `ownership`-Vektor,
  Ego-Reihenfolge wie der Randlayer. Cache-Key-Suffix `+conj_v1` NUR bei
  gesetztem Flag. **KEIN `VALUE_SCHEMA_VERSION`-Bump** -- der wuerde den
  v21-Cache ohne Not entwerten; der Suffix verhindert zugleich das stille
  Wiederverwenden eines 72-breiten Alt-Caches (das Ziel waere sonst
  vollstaendig maskiert und der Kopf lernte nichts, ohne Fehlermeldung).
- Kein eigener Verlustterm und kein eigenes Gewicht: die Konjunktionen haengen
  am selben BCE wie der Randlayer (`-1`-Maskierung greift unveraendert),
  gesteuert von `OWNERSHIP_WEIGHT`. Anteil am Gradienten 50 von 122 (~41%).
- `train.py --conjunction-head`; `export_onnx.py` zieht das Flag mit -- ohne das
  haette der Export einen 72-breiten Kopf gebaut und der Shape-Mismatch-Zweig
  haette den Kopf STILL zufaellig initialisiert exportiert.

**Verifiziert** (`tools/conjunction_head_selfcheck.py`, ohne Korpus/GPU):
Flag AUS ist bit-identisch zum Stand davor (state_dict-Formen und Ausgaben
beider Klassen, gleicher Seed); Flag AN ergibt +50 Ausgaben; Erkennung und
`build_model_from_checkpoint`-Rundlauf in beiden Klassen; 9 synthetische
Label-Faelle inkl. der Positionsabbildung.
**Nicht verifiziert:** die Identitaet gegen die Engine-Wertung auf echtem
Korpus -- `data/` liegt nicht im Repo. Vor dem ersten Trainingslauf gehoert
`python tools/plattenkopf_labels.py check` (um die Konjunktionen erweitert)
auf die Maschine mit den Daten.

### Maskierung der NICHT AKTIVEN Wertungsplatten (Nutzer)

*"Der head muss halt die ausgaenge der nicht aktiven wertungsplatten maskieren
im self play oder Arena. Sonst zieht er in die falsche Richtung."* -- gilt und
ist Pflicht fuer Stufe B: im Blattwert darf ein Kriterium, das in dieser Partie
nicht aktiv ist, exakt 0 beitragen.

Gegatet wird der PUNKTWERT, nicht die Vorhersage. Begruendung:
1. Alle 25 Konjunktionen sind reine BRETTFAKTEN ("Reihe 3 vollstaendig") --
   wohldefiniert unabhaengig davon, welche Platten ausliegen. Genau wie das
   Ownership-Ziel, das ebenfalls ohne Kriterien-Maske auskommt.
2. Die aktiven Platten stehen IN DER EINGABE: 8er-One-Hot im Flach-Vektor
   (`features.rs:522`) und als gegatete Plane-Kanaele (`features.rs:862`). Der
   Kopf kann also konditionieren und beide Regime lernen, statt Daten zu
   verlieren.

Damit entfaellt die Ziel-Maskierung auf aktive Kriterien, die fuer den
urspruenglichen Plattenkopf vorgesehen war. **Das ist eine Design-Entscheidung,
keine Messung** -- die alte Regel war mit den Ausschluss-Paaren begruendet
(Train/Inferenz-Fehlanpassung). Pruefbar waere sie durch einen Vergleich
maskiert gegen unmaskiert auf dem kriterienweisen Brier; als offener Punkt
notiert.

### Kuppel-Bonus: Korrektur einer Zuordnung in dieser Datei

Der Stufe-B-Satz oben, `"mit dem reihenabhaengigen Punktwert bei Kriterium 6
(1..6 je Reihe, round_end.rs)"`, ist FALSCH ZUGEORDNET. 1..6 ist der
Kuppel-Bonus fuers FUELLEN (`round_end.rs::check_special_trigger`,
`bonus = pattern_row + 1`) -- ein von den Wertungsplatten UNABHAENGIGER
Mechanismus, der immer greift. Kriterium 6 selbst ist glatt:
`score_empty_special_fields` = `-3 * empty`, ohne Reihenabhaengigkeit.

Ebenfalls festgehalten, weil in dieser Sitzung zunaechst behauptet und dann
widerlegt: der Kuppel-Bonus fehlt NICHT in der Bewertung.
`tiling_solver.rs:174` ruft `execute_full_tiling`, das `check_special_trigger`
ausfuehrt -- innerhalb der Runde ist er exakt gerechnet. Was fehlt, ist
allenfalls die Vorausschau ueber den Solver-Horizont hinaus, und die ist
Aufgabe des Value-Kopfs wie bei allem anderen auch.

Reicht die Netz-Eingabe, um den Bonus zu lernen? Ja, in beiden Zweigen: der
Flach-Vektor fuehrt je Slot 4 Spaces mit `space_type` an FESTEN Positionen
(`features.rs:615`), die Planes schreiben auf die echte 6x6-Geometrie
(`features.rs:809`), und die Position ueberlebt den Conv-Zweig, weil
`conv_flat_size = conv_channels * 6 * 6` flach in die Fusions-Linear geht.
Gelernt werden MUSS der Bonus ohnehin nicht -- er ist eine exakte Funktion
einer ablesbaren Position, genau wie die -3 ein bekannter Multiplikator ist.

### Offen

- Stufe A bedingt neu auswerten (Risiko vs. Anwesenheit trennen).
- Umstellung der Rauchtest-Regel foermlich entscheiden.
- Rauchtest fuer 0/1/2/5/7 -- nie gemessen; c3s Scheitergrund (EINE Konjunktion,
  ein Bit je Partie) trifft sie nicht, sie liegen bei 2 bis 6 Bits je Brett.
  Die Diagonalen mit 2 Bits sind der duennste Fall.
- Interaktion 2 x 6: ein unfuellbares Spezialfeld auf einer Diagonale blockiert
  `diag_fill` (`scoring.rs:167`, quadriert x 10). Analog zur schon notierten
  5 x 6, von keinem Ausschlusspaar abgefangen.
- Stufe B (Verwendung im Blattwert) unveraendert OFFEN, eigene Vorregistrierung.

### AUFGERAEUMT: `plate_head` entfernt (2026-08-10, Nutzer-Auftrag)

Die am 2026-08-10 nachts gebaute Modellseite (`plate_head`,
`PLATE_HEAD_SLOTS = 9`, `plate_head_present`, Signatur-Flag in beiden Klassen,
Lader-Durchreichung, Ausgabe-Anhang) ist **entfernt**. Sie war toter Code: 22
Verweise in `neural_net.py`, und **nichts** setzte das Flag je auf `True` --
die Revision oben hat c6 dem Ownership-Kopf zugeschlagen, bevor der eigene Kopf
je benutzt wurde.

Verifiziert nach der Entfernung: beide Modellklassen liefern wieder 5
Ausgaben im Default, der Champion laedt unveraendert mit 8, und
`conjunction_head_present` funktioniert weiter (die eine Kommentarzeile, die
auf `plate_head_present` verwies, ist mitgezogen). `neural_net.py` schrumpft
von 160,3 auf 158,3 KB.

**Was NICHT entfernt ist**: `tools/plattenkopf_labels.py` (Label-Rechnung samt
Identitaets-Pruefung 44.068/0 und der neuen Existenz-Maske),
`tools/plattenkopf_smoketest.py` und die Messungen. Die Labels sind fuer die
Ownership-Route dieselben, und die Identitaets-Pruefung bleibt die Verbindung
zwischen Atom-Definition und Engine-Wertung.

## GEBAUT: 9 Layout-Ausgaenge schliessen den Multiplikator von Kriterium 3

Nutzer-Auftrag 2026-08-10: *"mach das"*, nach dem Befund, dass Kriterium 3 der
einzige **zustandsabhaengige Punktwert** unter allen acht ist.

### Warum es die einzige Abdeckungsluecke war

| Kriterium | Punktwert | Bestimmt durch |
|-----------|-----------|----------------|
| 0/1/2/7 | +3 / +7 / +10 / +4 | konstant |
| 4 | +1 je Zelle | konstant |
| 5 | 3/3/8/8 | POSITION (feste Ecke) |
| 6 | -3 je Zelle | konstant |
| **3** | **2 x wild_total** | **Brettzustand am ENDE** |

`wild_total` waechst bis Runde 5, weil Platten weiter gelegt werden. Mit dem
AKTUELLEN Wert zu multiplizieren verzerrt frueh nach unten, und die gemessene
Spanne ist 1..8 Jokerfelder je Brett.

### Umsetzung

`CONJUNCTIONS_PER_PLAYER` 25 → **34**, `CONJUNCTION_TARGETS` 50 → **68**,
Kopfbreite 122 → **140**. Indizes **25..33**: `P(Slot s traegt am Ende eine
Jokerplatte)`, slot_row-major wie ueberall. **Das sind KEINE Konjunktionen,
sondern LAYOUT** -- im Code und in der Doku so benannt, damit der Block nicht
falsch gelesen wird.

Damit ist `E[wild_total] = Summe der neun Wahrscheinlichkeiten` -- ein Zaehler
als Summe von Indikatoren, dieselbe Zerlegung, mit der Kriterium 3 ueberhaupt
in die Wahrscheinlichkeitsfassung kam.

- Kein Checkpoint traegt den Konjunktions-Kopf (geprueft: 0 von allen `.pth`
  mit abweichender Breite), die Breitenaenderung bricht also nichts. Erkennung
  bleibt eine einzige Zahl.
- Cache-Key `+conj_v1` → **`+conj_v2`**: ein 122-breiter Alt-Cache darf nicht
  still wiederverwendet werden, sonst waere der Layout-Block vollstaendig
  maskiert und lernte nichts -- ohne Fehlermeldung. Dieselbe Begruendung wie
  beim ersten Suffix.
- Kein `VALUE_SCHEMA_VERSION`-Bump (der Suffix reicht), kein eigener
  Verlustterm. Gradientenanteil 68 von 140 (~49%).
- Selbsttest `tools/conjunction_head_selfcheck.py` um fuenf Faelle erweitert:
  Layout leer, genau ein Slot (Positionsabbildung 1*3+2=5), unbelegt zaehlt
  trotzdem (Layout, nicht Fuellung), Summe = `wild_total`, und zwei Wild-Spaces
  in EINEM Slot zaehlen als eins. Beide Suiten gruen.

### BEZIFFERTER Vorbehalt: das Produkt ueberschaetzt um 8,8 %

Die Auszahlung ist `2 x E[N x 1{C}]`, und `E[N] x P(C)` ist das nur bei
Unabhaengigkeit. Mehr Jokerfelder heisst schwerer, alle zu schliessen -- die
Korrelation ist negativ, das Produkt ueberschaetzt also. Gemessen auf 1.600
Endbrettern:

| Groesse | Wert |
|---------|------|
| `E[N_wild]` | 4,500 |
| `P(alle belegt)` | 0,413 |
| `E[N] x P(C)` (Naeherung) | 1,859 |
| `E[N x 1{C}]` (exakt) | **1,709** |
| Fehler | **+8,8 %**, Kovarianz -0,150 |
| in Punkten (x2) | 3,72 gegen exakt 3,42 |

Also 0,30 Punkte systematische Ueberschaetzung auf ein Kriterium von ~3,4
Punkten. Klein, aber gerichtet -- und jetzt beziffert statt vermutet.

**Die exakte Alternative liegt bereit**: die neun Verbund-Atome von gestern
(`Slot s hat ein belegtes Jokerfeld UND alle sind belegt`) geben
`2 x Summe P` exakt, Identitaet 44.068/0 verifiziert. Sie hatten im Rauchtest
aber keinen Skill (-0,036), weil alle neun an einem globalen Bit haengen.
Deshalb der Weg ueber Layout + Bedingung, mit dem bezifferten Fehler.

## ATOM-PRUEFUNG mit Waechter (2026-08-10): 16 von 34 Zielen sind konstant

Instrument: `tools/atom_skill_check.py` (neu). Labels aus dem AUTORITATIVEN
Bauer `_conjunctions_from_dome`, 150.000 Zustaende aus 1.268 Partien, Schnitt
nach Partie, Fruehstopp, **Waechter** gegen entartete Grundraten
(`min(rate,1-rate) < 1 %`, `Brier(Grundrate) < 1e-4`, `n < 200`).
Log: `logs/atom_skill_check.log`.

### Ergebnis: 11 Atome mit Skill > +0,02, 2 negativ, **16 entartet**

**Entartet (Grundrate praktisch 0 oder 1) -- und es sind die teuren:**

| Atom | Grundrate | Punktwert |
|------|-----------|-----------|
| Reihe 3/4/5/6 vollstaendig | **0,000** | +3 je |
| Diagonale H / N | 0,002 / **0,000** | **+10 je** |
| Ecke (2,0) / (2,2) | 0,002 / 0,004 | **+8 je** |
| farbenreiche Reihe 3/4/5/6 | **0,000** | +4 je |
| Spalte 1/3/5/6 | 0,002-0,006 | **+7 je** |

**Konjunktionen tragen fast kein Signal.** Bester Nicht-Layout-Wert: Ecke
(0,0) mit **+0,102**. Danach Ecke (0,2) +0,032, "alle Jokerfelder" +0,012,
Reihe 2 +0,016; Reihe 1 und farbenreiche Reihe 1 sind NEGATIV (-0,040 /
-0,043).

**Die 9 Layout-Ausgaenge sind das Starkste im Kopf**: +0,278 bis **+0,972**
(Slot 0 0,972, Slot 1 0,878, Slot 2 0,852, dann fallend bis Slot 8 0,278).

### Vorbehalt zum Layout-Signal -- DASSELBE MUSTER ZUM DRITTEN MAL

Ein Skill von 0,97 heisst hier vermutlich: der Kopf schreibt die **schon
sichtbare** Platzierung fort. Ist die Platte gelegt, ist die Antwort bekannt
und im Zustand ablesbar. Das ist zum dritten Mal derselbe Konfundierungstyp:

1. c6 unbedingt -> mischte ANWESENHEIT des Spezialfelds hinein (+0,637 -> nach
   Bedingung +0,400)
2. c6 gepoolt -> aggregierter Skill aus SLOT-IDENTITAET (jeder Slot einzeln war
   negativ)
3. Layout -> schon ENTSCHIEDENE Platzierungen

**Regel daraus**: jedes Ziel, das teilweise schon aus dem sichtbaren Zustand
folgt, blaeht den Skill auf, solange man nicht auf den noch UNENTSCHIEDENEN
Teil bedingt. Fuer das Layout heisst das: nur Slots auswerten, die im
jeweiligen Zustand noch unbelegt sind. **Offen.**

### Der grosse Befund liegt nicht beim Kopf

Von den acht Wertungsplatten erreicht der Champion die **teuersten nie**:
Diagonalen (10 Pkt) nie, Spalten (7 Pkt) unter 1 %, untere Ecken (8 Pkt) nie,
Reihen 3-6 nie. Faktisch gespielt werden nur Randfelder (Kriterium 4),
Spezialfeld-Vermeidung (6), die schnellen Reihen 1-2 und die obere linke Ecke.

Das ist eine **Strategie-Luecke, kein Vorhersage-Problem** -- und ein Kopf, der
Konstanten vorhersagt, schliesst sie nicht. Ob die Luecke strukturell ist,
entscheidet die policy-unabhaengige Verfuegbarkeitsrechnung
(`tools/musterreihen_verfuegbarkeit.py`), nicht der Korpus: dessen Grundraten
sind mit genau dem Defekt kontaminiert, den sie messen sollen.

### Konsequenz fuer `OWNERSHIP_WEIGHT > 0`

Beim jetzigen Stand wuerden **16 von 34 Zusatzzielen Konstanten lernen** und
Gradientenanteil verbrauchen. Vor einem Hochdrehen des Gewichts gehoert
entschieden, ob der Kopf auf die tragenden Atome beschnitten wird -- Kandidaten
sind die 9 Layout-Ausgaenge (nach der bedingten Nachpruefung) und Ecke (0,0).

---

## NACHTRAG 2026-08-10: Zwei Referenzlaeufe -- BODEN (Zufall) und MITTELWERT (Heuristik)

Nutzer-Auftrag: den Champion-Korpus gegen einen **policy-freien Boden** und
einen **kompetenten Mittelwert** abgrenzen, um die offene Frage des vorigen
Abschnitts zu entscheiden -- sind die 16 entarteten Atome *strukturell
unerreichbar* oder ein *Strategiedefizit*?

### Instrumente (neu, `#[ignore]`)

| Baustein | Ort |
|----------|-----|
| `ReferenzPolitik` (`Zufall` / `Heuristik(sims)`) | `engine/src/round_transition.rs` |
| `drive_to_game_end_reference(seed, politik)` | `engine/src/round_transition.rs` |
| `plattenkopf_referenzlauf_zufall` (1000 Partien) | `engine/src/scoring.rs` |
| `plattenkopf_referenzlauf_heuristik` (400 Partien, 150 Sims, `DEFAULT_C`) | `engine/src/scoring.rs` |
| `plattenkopf_referenzlauf_zufall_ohne_startplatte` (Kontrolle) | `engine/src/scoring.rs` |

Partienzahl und Sims sind per Umgebungsvariable uebersteuerbar
(`MOSAIC_PLATTENKOPF_GAMES`, `MOSAIC_PLATTENKOPF_SIMS`).
Rohausgabe: `logs/plattenkopf_referenzlaeufe.log` (Laufzeit 4,1 s Zufall,
130,9 s Heuristik).

### Zuerst ein Treiber-Fehler, der die Messung gekippt haette

`drive_to_game_end_random` (und `drive_to_game_end`) setzen ueber
`drive_to_first_round_end` `start_tile_pending = false` und **ueberspringen die
kostenlose Startkuppel-Platzierung**. Nach `docs/engine_manual.md` legt jeder
Spieler 1 Startplatte plus in den Runden 1-4 je genau 2 (Runde 5: keine) = 9
Platten, also alle `MAX_DOME_SLOTS`. Ohne Startplatte bleiben es **8,000/9** --
gemessen, nicht vermutet (Kontroll-Lauf). Ein 2x2-Block des 6x6-Rasters fehlt
dann STRUKTURELL, womit 2 Reihen, 2 Spalten und mindestens eine Diagonale per
Konstruktion unerreichbar sind: genau die Groessen, um die es hier geht.

Der neue Treiber legt die Startplatte mit `self_play::choose_start_placement`
-- derselben fixen Heuristik, die auch der Champion-Korpus benutzt (Self-Play
waehlt die Startplatte NICHT per Netz). Belegt an drei unabhaengigen Groessen,
dass die Plattenverteilung damit deckungsgleich ist:

| Groesse | neuer Treiber (Zufall) | Champion-Log |
|---------|------------------------|--------------|
| belegte Kuppelslots | 9,000/9 | (9 vorausgesetzt) |
| E[Jokerfelder] | 4,500 | 4,496 (Summe Atome 25-33) |
| Layout Slot 0 traegt Joker | 0,821 | 0,788 |

**Nebenfolge:** die Grundraten, die
`plattenkopf_atom_identities_hold_on_real_end_boards` mitausgibt (Jokerfelder je
Brett, Spezialfelder, "alle Jokerfelder belegt"), stehen auf 8-Platten-Brettern
und sind entsprechend verzerrt. Die dort geprueften IDENTITAETEN sind davon
nicht betroffen -- die gelten je Brett algebraisch, unabhaengig von der
Plattenzahl.

### Tabelle: Zufall | Heuristik | Champion

Zufall n = 1000 Partien / 2000 Bretter, Heuristik n = 400 / 800, Champion aus
`logs/atom_skill_check.log` (1268 Partien). Format: `Mittel-Pkt / Anteil != 0`.
Die Champion-Spalte ist aus den Atom-Grundraten ABGELEITET (Rechnung darunter).

| ID | Kriterium | Zufall | Heuristik | Champion | Einordnung |
|----|-----------|--------|-----------|----------|------------|
| 0 | Horizontale Reihen | 0,004 / 0,1 % | 0,994 / 27,1 % | 0,825 / 14,8-27,5 % | gleichauf |
| 1 | Vertikale Reihen | 0,004 / 0,1 % | **0,945 / 13,1 %** | 0,252 / 1,2-3,6 % | **STRATEGIEDEFIZIT** |
| 2 | Diagonale Reihen | 0,000 / 0,0 % | 0,050 / 0,5 % | 0,020 / 0,2 % | strukturell |
| 3 | Mehrfarbige Felder | 1,212 / 16,2 % | 3,632 / 43,0 % | ~3,2 / 38,7 % | gleichauf |
| 4 | Aeussere Felder | 4,766 / 99,7 % | 9,650 / 100 % | -- (nicht im Log) | offen |
| 5 | Eckplatten | 0,442 / 14,4 % | 3,498 / 97,9 % | 3,237 / >= 80,9 % | gleichauf |
| 6 | Spezialfelder | -13,245 / 100 % | -11,029 / 100 % | -- (nicht im Log) | offen |
| 7 | Farbenreiche Reihen | 0,006 / 0,1 % | 0,385 / 9,0 % | 0,244 / 3,6-6,1 % | gleichauf |

Kriterium 6, mittlere Zahl LEERER Spezialfelder je Brett (Auftragspunkt):
**Zufall 4,415 von 4,500 -- Heuristik 3,676 von 4,500**. Die Heuristik raeumt
also 18 % der Spezialfelder ab, der Zufall 2 %.

Kontext (mittlere Brettfuellung): Zufall 8,418/36 Felder, Heuristik 17,515/36.

Champion-Ableitung aus den Atom-Grundraten: Kriterium 0 = 3 x Summe(Reihen),
1 = 7 x Summe(Spalten), 2 = 10 x Summe(Diagonalen), 5 = 3 x (E00+E02) +
8 x (E20+E22), 7 = 4 x Summe(farbenreiche Reihen). Der Anteil != 0 ist aus
Marginalraten nur eingrenzbar (max(einzeln) <= Anteil <= Summe), deshalb als
Spanne. Kriterium 3 ist NICHT exakt ableitbar (der Punktwert `2 x wild_total`
ist zustandsabhaengig); ~3,2 unterstellt `E[wild_total | alle belegt] ~ 4,2`
wie im Heuristik-Arm gemessen. Kriterien 4 und 6 haben im Log **keine**
Entsprechung -- sie sind additiv und werden vom 36-Feld-`ownership`-Layer
abgedeckt, nicht von den 34 Konjunktionen.

### Atom-Ebene: welches der 16 entarteten Atome ist was

Wilson-95-%-Intervalle konservativ auf der PARTIE-Zahl (400 bzw. 1268), nicht
auf der Brettzahl -- die beiden Bretter einer Partie teilen Versorgung und
Denial und sind nicht unabhaengig (`feedback_arena_block_correlation`).

| Atom | Zufall | Heuristik | Champion | Befund |
|------|--------|-----------|----------|--------|
| Reihe 3/4/5/6 vollst. | 0,000 | 0,001 / 0,001 / 0,000 / 0,000 | 0,000 | **strukturell** |
| Diagonale H / N | 0,000 / 0,000 | 0,003 / 0,003 | 0,002 / 0,000 | **strukturell** |
| farbenreiche Reihe 3-6 | 0,000 | 0,001 / 0,000 / 0,000 / 0,000 | 0,000 | **strukturell** |
| Ecke (2,2) | 0,000 | 0,004 | 0,004 | **strukturell** |
| Ecke (2,0) | 0,001 | 0,013 [0,006-0,030] | 0,002 [0,001-0,006] | Hinweis auf Defizit, klein |
| Spalte 1 | 0,001 | 0,035 | 0,004 | **Strategiedefizit** |
| Spalte 2 | 0,000 | 0,046 | 0,010 | **Strategiedefizit** |
| Spalte 3 | 0,000 | 0,029 | 0,006 | **Strategiedefizit** |
| Spalte 4 | 0,000 | 0,009 | 0,012 | gleichauf |
| Spalte 5 | 0,000 | 0,014 | 0,002 | Hinweis auf Defizit |
| Spalte 6 | 0,000 | 0,003 | 0,002 | gleichauf |
| Summe Spalten | 0,002 | **0,136 [0,106-0,173]** | **0,036 [0,027-0,048]** | **3,8x, Intervalle disjunkt** |

Nicht-entartete Atome zur Kalibrierung: Reihe 1 Heuristik 0,189
[0,154-0,230] gegen Champion 0,127 [0,110-0,146] (Heuristik leicht besser);
Reihe 2 0,140 gegen 0,148 (gleich); "alle Jokerfelder belegt" 0,430
[0,382-0,479] gegen 0,387 [0,361-0,414] (ueberlappend); Ecke (0,0) 0,866
[0,829-0,896] gegen 0,809 [0,786-0,830]; Ecke (0,2) 0,256 gegen 0,254 (gleich).
Anders gesagt: eine 150-Sim-Heuristik ohne Netz erreicht auf JEDEM dieser
Konjunktions-Atome mindestens das Champion-Niveau.

### Warum Reihen strukturell sind, Spalten aber nicht -- der Mechanismus

Am Code geprueft, nicht vermutet (`round_end.rs::generate_tiling_actions`
Zeile 598: `dome_row = row_idx / 2; space_row = row_idx % 2`, und
`execute_tiling_action` Zeile 218: `row.tiles.clear()`):

1. Musterreihe *r* speist **genau** Kuppel-Rasterzeile *r* (1:1, keine
   Nachbarzeile).
2. Je Tiling-Phase wandert aus einer fertigen Musterreihe **genau 1 Stein** auf
   die Kuppel, die Reihe wird geleert. Ueber 5 Runden also **hoechstens 5
   Steine je Rasterzeile** aus dem Tiling.
3. Eine Rasterzeile hat 6 Felder. Der 6. kann nur ein **Spezialfeld** sein (das
   wird automatisch belegt, sobald die anderen 3 Felder seiner Platte voll sind,
   `engine_manual.md` Abschnitt 5). Auch Jokerfelder verbrauchen einen Transfer.

Daraus folgt die Asymmetrie:

* **Zeile *r* vollstaendig** = Musterreihe *r* muss in **jeder** der 5 Runden
  geschlossen werden. Laut `tools/musterreihen_verfuegbarkeit.py` braucht
  Musterreihe 3 ~1,4 Runden je Abschluss, Reihe 6 ~2,9 -- fuenf Abschluesse
  brauchen ~7 bzw. ~14,5 Runden von 5. **Unmoeglich.** Nur die Reihen 1-2
  (~0,5 / ~1,0 Runden je Abschluss) liegen im Budget, und genau die sind die
  einzigen mit positiver Grundrate, in ALLEN drei Armen.
* **Spalte *c* vollstaendig** = **jede** der 6 Musterreihen muss **einmal** in
  Spalte *c* liefern. Das liegt im Budget (jede Reihe ist mindestens einmal
  schliessbar). Spalten sind also erreichbar -- und die Heuristik erreicht sie
  auch, auf 13,1 % der Bretter gegen maximal 3,6 % beim Champion.
* **Diagonale** verlangt zusaetzlich, dass jeder dieser 6 Transfers eine
  bestimmte, mit der Zeile wandernde Spalte trifft. Beide Referenzen bei 0,3 %.

### Was NICHT belegt ist

1. **Kriterium 4 (Aeussere Felder) und 6 (Spezialfelder) haben keine
   Champion-Spalte.** Sie stehen nicht im Atom-Log (additiv, im
   `ownership`-Layer). Der Zufall/Heuristik-Vergleich steht, der Abstand zum
   Champion ist offen. Waere ueber den Korpus nachzurechnen -- nicht Teil dieses
   Auftrags.
2. **Die Heuristik ist selbst schwach.** 150 Sims, kein Netz, statische
   Blattbewertung; in der Elo-Kaderaufstellung ist Heuristik@200 der ANKER am
   unteren Ende. Sie ist eine untere Schranke fuer "was ein kompetenter Spieler
   erreicht", kein Deckel. Wo sie den Champion schlaegt, ist das Defizit
   deshalb eher UNTERschaetzt; wo beide bei 0 liegen, bleibt die Moeglichkeit,
   dass ein dritter, ganz anderer Spielstil es doch erreicht -- die
   Struktur-Einordnung stuetzt sich daher auf den Mechanismus oben, nicht auf
   die Nullrate allein.
3. **Stichprobengroesse.** Heuristik 400 Partien / 800 Bretter, Zufall 1000 /
   2000. Fuer Atome mit Rate < 1 % traegt das nicht: Ecke (2,0) beruht auf ~10
   Ereignissen, die Diagonalen auf 2-3. Diese Zeilen sind als "beide ~0"
   belastbar, nicht als Rangordnung. Fuer die Spalten-Aussage (13,1 % gegen
   <= 3,6 %, disjunkte Intervalle) traegt sie.
4. **Der Champion-Korpus ist EXPLORATIVES Self-Play**, mit
   Dirichlet-Wurzel-Noise (`net_mcts.rs::build_net_tree`, `add_root_noise`). Er
   zeigt nicht das beste Spiel des Champions. Ein Teil des Spalten-Abstands kann
   Explorationsrauschen sein. Sauber waere ein Referenzlauf mit
   `add_root_noise = false` -- nicht gemessen.
5. **Die Champion-Grundraten sind ZUSTANDS-, nicht brettgewichtet** (150 000
   Zustaende aus 1268 Partien; das Konjunktions-Label kommt aus dem Endbrett und
   wiederholt sich ueber alle Zustaende einer Partie). Lange Partien wiegen
   schwerer. Die Referenzlaeufe zaehlen je Brett genau einmal.
6. **Die Arme unterscheiden sich nicht NUR in der Politik**: der Champion spielt
   gegen den Champion, die Heuristik gegen die Heuristik. Denial-Druck und damit
   die Versorgung einer gezielt gesammelten Farbe sind nicht dieselben. Ein
   Heuristik-gegen-Champion-Lauf wuerde das trennen -- nicht gemessen.

### Konsequenz

Die Aussage des vorigen Abschnitts ("Strategie-Luecke, kein
Vorhersage-Problem") ist **zu weit gefasst**. Aufgeteilt:

* **Strukturell und damit als Kopf-Ausgang wertlos** (kein Spielstil erreicht
  sie): Reihen 3-6, beide Diagonalen, farbenreiche Reihen 3-6, Ecke (2,2) --
  10 der 16 entarteten Atome. Diese Ziele gehoeren aus dem Kopf entfernt, und
  zwar unabhaengig von jedem `OWNERSHIP_WEIGHT`.
* **Echtes Strategiedefizit**: die **Spalten** (Kriterium 1, 7 Pkt je Spalte).
  Die Heuristik holt hier 3,8x so viel wie der Champion. Das ist der einzige
  Punkt der Liste, an dem ein Eingriff Punkte verspricht -- und er ist kein
  Kopf-Thema, sondern eins der Zielauswahl bzw. der Blattbewertung.
* **Offen**: Ecke (2,0) (8 Pkt, Hinweis auf ein kleines Defizit, n zu klein),
  Kriterien 4 und 6 (keine Champion-Referenz).

## KORREKTUR + ABLEITUNG: die Diagonale ist NICHT strukturell unmoeglich

Nutzer 2026-08-10: *"warum sollte sie strukturell unmoeglich sein. du musst nur
einmal alle musterreihen voll bekommen"* -- richtig, und die
Referenzlauf-Einordnung ist an dieser Stelle falsch. Ich habe sie ungeprueft
uebernommen.

Eine Diagonale sind sechs Zellen `(r,r)`, also **eine je Rasterzeile** -- genau
ein Abschluss jeder Musterreihe, IDENTISCH zur Spalte. Das
Mechanismus-Argument, das fuer Spalten korrekt "im Budget" ergab, gilt fuer die
Diagonale unveraendert. Die Einordnung "strukturell" beruhte allein darauf, dass
BEIDE KIs bei ~0 liegen -- derselbe Fehlschluss, gegen den
`feedback_skill_confound_already_determined` steht, und den der Nutzer selbst
widerlegt (er erreicht Diagonalen "wenn es gut laeuft").

**Fuer die Reihen 3-6 traegt das Argument dagegen unabhaengig**: sie brauchen
FUENF Abschluesse DERSELBEN Musterreihe (Reihe 3: ~1,4 Runden je Abschluss = 7
von 5 Runden). Dort ist "strukturell" korrekt.

### Die Strategie ist ableitbar, nicht bloss beobachtet

**Budget.** Ein Durchgang durch alle sechs Musterreihen kostet 1+2+..+6 = **21**
Steine. Aufnahme je Spieler: 21 Sonnenfliesen/Runde, geteilt, 5 Runden = **52,5**.

| Durchgaenge | Steine | Anteil der Aufnahme | |
|---|---|---|---|
| 1 | 21 | 40 % | passt |
| **2** | **42** | **80 %** | **passt** |
| 3 | 63 | 120 % | passt nicht |

Deckt die Nutzer-Angabe *"das geht sich beim clever spielen auch zweimal aus"*
und erklaert, warum es normalerweise ZWEI sind.

**Wert je Durchgang -- entscheidet die LINIENFORM, nicht der Plattenwert.**
`score_placed_tile` (`round_end.rs:349`) zahlt waagerechte plus senkrechte
Laufweite, je nur wenn > 1:

| | Platzierung | Platte | Summe |
|---|---|---|---|
| **Spalte** | 1+2+3+4+5+6 = **21** | 7 | **28** |
| Diagonale | 6 x 1 = **6** | 10 | **16** |

Die Diagonalzellen sind untereinander **keine orthogonalen Nachbarn** -- jede
bleibt alleinstehend. Bei identischem Musterreihen-Aufwand: 2 Spalten = 56 Pkt,
Spalte + Diagonale = 44, 2 Diagonalen = 32.

**Damit ist die Dossier-Rangfolge des Nutzers hergeleitet** ("vertikal immer
gerne; DIAGONALE zwiegespalten -- widerspricht dem orthogonalen Aufbau";
`archive/history.md`): die Diagonale zahlt den hoechsten Plattenwert und ist die
einzige Linie, die den 93-%-Term NICHT mitnimmt. Die Horizontale kommt aus
Reihe 1 oder 2 fast nebenbei (Kapazitaet 1-2).

### Der Champion-Defekt, praezise

Nicht "bewertet Wertungsplatten falsch", sondern: **er committet sich nie auf
einen Durchgang.** Bei 1,2-3,6 % Spaltenrate schliesst er praktisch nie alle
sechs Musterreihen so, dass sie in EINER Spalte landen -- er verteilt seine ~52
Steine statt zwei Bahnen zu ziehen.

Nutzer-Maszstab gegen Messung, dieselben drei Platten (vertikal/horizontal/diagonal):

| | Nutzer | Heuristik | Champion |
|---|---|---|---|
| Plattenpunkte | **17** (mit Diagonale 27) | 1,99 | **1,10** |

Faktor **15** zum Champion, 8,5 zur Heuristik. Und die Heuristik ist KEIN
unabhaengiger Referenzpunkt: `wertung_progress` enthaelt fuer Kriterium 1
woertlich `(col_fill/6)^2 * 7`, sie wird also ausdruecklich zu Spalten
hingeschoben (Nutzer-Hinweis). Der Befund "Heuristik schlaegt Champion auf jedem
Atom" heisst also: handkodierte Plattenformung schlaegt KEINE Plattenformung.

## BEDINGTE NACHPRUEFUNG des Layout-Signals (2026-08-10): ~90 % war ABLESEN

Der oben als **offen** notierte Vorbehalt ist gemessen. `tools/atom_skill_check.py`
kennt dafuer `--conditional-layout` (Bestandsverhalten bleibt Default) und
wertet die 9 Layout-Ausgaenge nur noch auf Slots aus, die im JEWEILIGEN Zustand
noch keine Platte tragen -- **Grundrate und Brier-Referenz eingeschlossen**,
sonst waere die Referenz falsch. Logs: `logs/atom_skill_check_conditional.log`
(Erstlauf), `logs/atom_skill_check_ownership.log` (Wiederholung mit der
endgueltigen Fassung), `logs/atom_skill_check_masked.log` (bester Versuch).

### Der Konfundierer ist zuerst BELEGT, nicht vermutet

* Eine gelegte Platte wird nie bewegt: 13.219 belegte Slot-Beobachtungen,
  **0 Abweichung** von Platten-Id und WILD-Eigenschaft des Endzustands.
* Der Raumtyp einer gelegten Platte steht in der Eingabe (`state_to_tensor`:
  `TYPE_MAP` mit WILD=0,5; `state_to_planes`: `_SPACE_TYPE_IDX`).

Fuer einen belegten Slot ist das Label damit **trivial ablesbar**. Und weil die
Slots frueh und in fester Reihenfolge belegt werden (Runde 1: 0 Slots, Runde 4:
alle 9), ist der Ablese-Anteil je Slot verschieden gross -- **genau die Achse,
entlang der die unbedingten Skills abfielen**.

### Unbedingt gegen bedingt, beide aus DEMSELBEN Modell

| Slot | Ablese% | Skill unbedingt | n bedingt | Partien | Skill bedingt | 95 %-KI (Partie-Bootstrap) | Delta |
|------|---------|-----------------|-----------|---------|---------------|----------------------------|-------|
| 0 | **98,3 %** | +0,976 | 506 | 253 | **+0,101** | [+0,038; +0,151] | **-0,875** |
| 1 | 87,7 % | +0,879 | 3.687 | 253 | +0,042 | [-0,038; +0,113] | -0,837 |
| 2 | 84,3 % | +0,844 | 4.680 | 253 | +0,069 | [-0,028; +0,153] | -0,774 |
| 3 | 69,2 % | +0,651 | 9.210 | 253 | -0,098 | [-0,176; -0,027] | -0,749 |
| 4 | 59,2 % | +0,542 | 12.198 | 253 | -0,091 | [-0,153; -0,034] | -0,633 |
| 5 | 50,9 % | +0,460 | 14.694 | 253 | -0,078 | [-0,153; -0,011] | -0,539 |
| 6 | 34,2 % | +0,341 | 19.666 | 253 | +0,012 | [-0,067; +0,079] | -0,329 |
| 7 | 36,5 % | +0,266 | 18.982 | 253 | -0,121 | [-0,243; -0,015] | -0,388 |
| 8 | 37,2 % | +0,340 | 18.787 | 253 | -0,006 | [-0,120; +0,084] | -0,346 |

Der Ablese-Anteil erklaert die unbedingte Rangfolge fast vollstaendig: Slot 0
war zu 98,3 % abgelesen und stand mit +0,976 an der Spitze. **Nach der Bedingung
verschwindet die Rangfolge.** Das Konfidenzband kommt aus einem Bootstrap ueber
PARTIEN, nicht ueber Zustaende -- das Label ist je Partie konstant, ein
Zustands-Bootstrap haette die Streuung massiv unterschaetzt (dieselbe Lektion
wie bei der Arena-Block-Korrelation). Effektive Stichprobe: **253 Partien**, egal
ob n = 506 oder n = 19.666.

### Entartung und bester Versuch

**0 von 9** Layout-Atomen entarten unter der Bedingung -- selbst Slot 0 behaelt
n = 506 (> `MIN_OBS` = 200) und eine Grundrate von 0,715. Der Waechter greift
hier also nicht; das Ergebnis ist eine echte Null, keine Messluecke.

Damit die Zahl nicht am Probe haengt, hat `--mask-train-decided` die abgelesenen
Zellen zusaetzlich aus dem TRAININGSverlust genommen -- der Kopf bekommt die
reine Vorhersageaufgabe, ohne Gradientenanteil fuer das Abschreiben:

| Slot | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|------|---|---|---|---|---|---|---|---|---|
| Skill bedingt, Training maskiert | -0,009 | +0,040 | **+0,110** | -0,014 | -0,016 | +0,012 | +0,020 | **+0,117** | +0,067 |

Signifikant positiv sind dabei nur Slot 2 ([+0,050; +0,161]) und Slot 7
([+0,055; +0,174]) -- und Slot 7 war im unmaskierten Lauf -0,121. **Die
Vorzeichen einzelner Slots sind Rauschen** (Muster Trainings-Seed-Varianz), die
belastbare Aussage ist der Betrag.

### Aussage

Vom Layout-Signal bleibt nach der Bedingung **hoechstens +0,12** uebrig, im
Schnitt praktisch **null**; verloren gehen 0,33 bis 0,88 Skill-Punkte je Slot.
Rund **90 % des gemessenen Layout-Skills war Fortschreiben der sichtbaren
Platzierung.** Der Rest liegt in derselben Groessenordnung wie Ecke (0,0)
(+0,124) -- also im Mittelband der uebrigen Atome und **nicht** auf dem Niveau,
das einen eigenen Kopf-Block rechtfertigt. Der Vorbehalt von oben ist damit
**geschlossen, zu Lasten des Layout-Signals**; die 9 Ausgaenge bleiben als
Multiplikator-Abdeckung fuer Kriterium 3 berechtigt, aber sie sind nicht "das
Starkste im Kopf".

Damit ist derselbe Konfundierungstyp zum **vierten** Mal derselbe: Anwesenheit
des Spezialfelds, Slot-Identitaet durch Poolung, entschiedene Platzierung -- und
jetzt (siehe unten) die schon belegte Ownership-Zelle. Die Regel gilt
ausnahmslos: **auf den noch UNENTSCHIEDENEN Teil bedingen, Referenz inbegriffen.**

## OWNERSHIP-ZELLEN GEMESSEN (2026-08-10): 0 von 36 entartet

Anlass ist die Richtung, den Ownership-Kopf in der Blattbewertung zu
MAXIMIEREN. Die Konjunktionen sind dafuer untauglich -- 16 von 34 sind konstant,
"Diagonale vollstaendig" hat Grundrate 0,000, ein Kopf, der "nie" sagt, liefert
keinen Gradienten. Die Idee ist deshalb die konvexe Aggregation der
RANDwahrscheinlichkeiten je Zelle, `(Summe P ueber die Zellen eines Kriteriums /
n)^2 x Punktwert` nach dem Muster `wertung_progress`. Voraussetzung: die
einzelnen Zellen muessen Signal tragen, auch wo die Vollendung nie eintritt.

Instrument: `tools/atom_skill_check.py --target ownership` (bzw. `--target both`,
ein Korpuslauf fuer beide Ziele), Labels aus dem AUTORITATIVEN
`_ownership_from_dome`, gleicher Waechter, gleiche Partie-Trennung,
150.000 Zustaende aus 1.268 Partien, Schnitt 1.015 / 253 Partien.

### Der Konfundierer gilt auch hier -- drei Strata, getrennt ausgewiesen

Auch eine belegte Zelle ist trivial ablesbar: 11.104 belegte Zellen geprueft,
**0** davon im Endzustand nicht belegt. Deshalb trennt die Messung je Zelle und
Zustand:

| Stratum | Bedeutung | Zell-Beobachtungen (Stichprobe) |
|---------|-----------|---------------------------------|
| Zelle belegt | Endlabel trivial 1 -> ABLESEN | 11.104 |
| Platte liegt, Zelle leer | Vorhersage INNERHALB der gelegten Platte | 41.772 |
| Slot ohne Platte | Vorhersage einschliesslich der Plattenwahl | 31.220 |

### BEFUND 1: die Zellen sind nirgends konstant -- auch nicht bei den teuren Kriterien

**0 von 36 Zellen entarten**, auch unter der Bedingung. Genau dort, wo die
Konjunktion tot ist, lebt die Zelle (bedingte Grundraten, Mittel je Geometrie):

| Kriterium | Konjunktion (Grundrate) | Zellen des Kriteriums (bedingte Grundrate) |
|-----------|-------------------------|--------------------------------------------|
| K2 Diagonale H (+10) | **0,000 / 0,002** | **0,428** |
| K2 Diagonale N (+10) | **0,000** | **0,321** |
| K5 Eckslot (2,0) (+8) | 0,002 | **0,102** |
| K5 Eckslot (2,2) (+8) | 0,004 | **0,085** |
| K0 Reihe 5 (+3) | **0,000** | **0,115** |
| K0 Reihe 6 (+3) | **0,000** | **0,081** |
| K1 Spalte 1 (+7) | 0,004 | **0,421** |
| K4 Randzellen (+1) | -- | 0,383 |

Caveat wie oben in der Liste "Was NICHT belegt ist" (Punkt 5): diese Grundraten
sind ZUSTANDS-, nicht brettgewichtet, lange Partien wiegen schwerer. Fuer die
Frage "konstant oder nicht" aendert das nichts -- 0,08 gegen 0,000 ist kein
Gewichtungseffekt --, fuer die exakte Hoehe schon.

Das ist die entscheidende Vorbedingung, und sie **haelt**: die konvexe
Aggregation bekommt ein lebendes, nicht gesaettigtes Ziel und einen echten
Gradienten in genau den Kriterien, in denen die Konjunktion nichts liefert. Die
niedrigste Einzel-Grundrate im ganzen Feld ist 0,072 -- weit ueber der
Entartungsschwelle von 1 %.

### BEFUND 2: das Vorhersage-Signal ist klein, und das PROBE ist die Grenze

Zur Vorsicht gegen die Lesart "das Netz kann es nicht, also traegt die Zelle
nichts" laeuft eine probe-freie Untergrenze mit: eine geglaettete
5-Parameter-Tabelle `P(Label | Runde)`, auf den TRAININGSpartien gefittet,
bedingt ausgewertet. Das MLP hat 1.015 unabhaengige Partien, aber 120.000 fast
identische Zustaende -- es kann partiespezifisch memorieren und dabei unter die
Grundrate fallen. Die Tabelle kann das nicht.

| Mass | Wert |
|------|------|
| Rundentabelle, Schnitt ueber alle 36 Zellen | **+0,025** (positiv bei **36 von 36**) |
| Rundentabelle, bester Wert | +0,072 (Zellen des Eckslots (0,0)) |
| MLP mit maskiertem Training, Schnitt | **-0,027** |
| MLP, bester Einzelwert | +0,202, KI [+0,071; +0,305] (Slot(0,0) F1) |

**Jede** Zelle traegt also Signal ueber ihre eigene Grundrate hinaus -- aber das
MLP-Probe faellt auf den meisten Zellen UNTER die triviale Tabelle. Die
negativen MLP-Zahlen sind darum **keine** Aussage "kein Signal", sondern die
Grenze dieses Probes. Die Groessenordnung des Zell-Signals liegt bei
**+0,02 bis +0,07**, im besten Einzelfall +0,20.

### BEFUND 3: vorhersagbar ist die Vollendung der LIEGENDEN Platte, nicht die Plattenwahl

Mittlere bedingte Skills je Geometrie, getrennt nach den beiden
unentschiedenen Strata (Training maskiert):

| Gruppe | Grundrate | Skill bedingt | Tabelle | leer auf LIEGENDER Platte | Slot ohne Platte |
|--------|-----------|---------------|---------|---------------------------|------------------|
| K4 Randzellen (+1) | 0,383 | -0,018 | +0,023 | **+0,003** | -0,064 |
| K4 Innenzellen | 0,396 | -0,038 | +0,027 | -0,013 | -0,083 |
| K0 Reihe 1 (+3) | 0,750 | +0,037 | +0,036 | **+0,043** | -0,045 |
| K0 Reihe 3 (+3) | 0,397 | -0,037 | +0,033 | +0,006 | -0,114 |
| K0 Reihe 6 (+3) | 0,081 | -0,046 | +0,005 | -0,011 | -0,064 |
| K1 Spalte 2 (+7) | 0,452 | +0,035 | +0,043 | **+0,060** | -0,049 |
| K2 Diagonale H (+10) | 0,428 | +0,010 | +0,034 | **+0,040** | -0,043 |
| K2 Diagonale N (+10) | 0,321 | -0,033 | +0,017 | -0,008 | -0,084 |
| K5 Eckslot (0,0) (+3) | 0,844 | +0,083 | +0,070 | **+0,084** | -0,004 |
| K5 Eckslot (2,0) (+8) | 0,102 | -0,073 | +0,008 | -0,057 | -0,083 |
| K5 Eckslot (2,2) (+8) | 0,085 | -0,033 | +0,006 | +0,017 | -0,057 |

Das Stratum "Slot ohne Platte" ist **durchgaengig negativ** (-0,004 bis -0,114),
das Stratum "leere Zelle auf liegender Platte" traegt das gesamte positive
Signal. Lesart: vorhersagbar ist, ob eine schon gelegte Platte fertig befuellt
wird -- **nicht, welche Platte gewaehlt wird**. Und die teuren unteren Eckslots
sind in beiden Strata signifikant unter der Grundrate (Eckslot (2,0):
-0,068 bis -0,085, Konfidenzband vollstaendig negativ).

### Urteil zur konvexen Aggregation

1. **Die Voraussetzung haelt.** Anders als bei den Konjunktionen ist keine
   einzige Zelle konstant, und die Zellen der teuren Kriterien (Diagonalen 0,43
   / 0,32, untere Eckslots 0,10 / 0,09, Reihen 5-6 0,12 / 0,08) liefern
   lebendige Grundraten. Ein `wertung_progress`-artiger Aggregat hat dort einen
   Gradienten, wo die Konjunktion "nie" sagt. Das ist der belastbare Teil des
   Befunds und spricht **fuer** die Aggregation als Trageform.
2. **Das Signal ist klein, aber echt.** +0,02 bis +0,07 (probe-frei, 36/36
   positiv) statt der 16 toten Ziele. Die Konjunktionen sind fuer ein
   MAXIMIERTES Gewicht der falsche Traeger, die Zellen der richtige.
3. **Unbewiesen bleibt der Nutzen in der Blattbewertung.** Der vorhersagbare
   Anteil sitzt im Stratum "Platte liegt schon", und die Rundentabelle allein
   holt fast alles davon -- ein rein rundenabhaengiger Anteil ordnet
   Geschwisterblaetter derselben Runde ueberhaupt nicht. Ob das Aggregat BRETTER
   unterscheidet, entscheidet dieses Offline-Mass nicht.
4. **Konsequenz.** Vor einem hochgedrehten `OWNERSHIP_WEIGHT` gehoert die
   Aggregation an das Instrument, das im Projekt schon zweimal die richtige
   Antwort gab: Geschwister-Rangfolge / Arena, nicht der Offline-Skill. Die
   bekannte Aufloesungsgrenze der Offline-Masse (~0,015 gegenueber der Arena)
   liegt zu nah an den gemessenen +0,02 bis +0,07, um die Entscheidung zu tragen.
