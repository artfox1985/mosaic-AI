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
