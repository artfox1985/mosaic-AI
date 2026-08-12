# Vorregistrierung: Spalten gezielt PROVOZIEREN (Stufe 1 vor dem Self-Play)

**Angelegt 2026-08-12, Nutzer-Korrektur** — auf meine Beschreibung des "Lern-Wegs":
*"das ist kein plan. das ist hoffen. als erstes brauchen wir eine methode gezielt
spiele zu provozieren die stark auf die wertungsplatten gehen. erst wenn wir das
haben können wir sie in die self plays entlassen"*

## 1. Mein Fehler, und er war eine Stufenverwechslung

Ich hatte das partieweise gestreute Injektionsgewicht (`MOSAIC_WERTUNG_STREUUNG_MAX`,
gebaut und getestet) als den Lern-Weg beschrieben. Es ist aber **Stufe 2**. Die
Messungen derselben Nacht sagen, warum das nicht reicht:

| Konfiguration | vertikale Plattenpunkte | Spalten je Partie |
| ------------- | ----------------------: | ----------------: |
| Nullpunkt | 1,05 | 0,15 |
| beste Injektion (w=1 / alpha=1) | 2,10 | 0,30 |
| Heuristik (Referenz) | 1,40 | 0,20 |

**Keine Konfiguration erzeugt Partien, die STARK auf die Wertungsplatten gehen.**
Ein Korpus mit gestreutem Gewicht wäre ein Korpus aus Nuancen desselben seltenen
Ereignisses — der Ownership-Kopf hätte nichts zu sehen. Das Werkzeug streut etwas,
das es noch nicht gibt.

## 2. Die Abnahmezahl, vom Nutzer kalibriert

*"mehr als zwei werden eher nicht zusammen kommen. selbst mit einer pro partie
wäre ich glücklich. dass sind dann 28 punkte allein aus dieser spalte (inkl.
normalen punkten). bei zwei geschlossenen spalten hätten wir dann 56 punkte."*

Damit ist das Ziel erstmals eine belegte Zahl statt einer Schätzung von mir:

| Ziel | vertikale Plattenpunkte | heute |
| ---- | ----------------------: | ----: |
| **eine Spalte je Partie** (Nutzer: "wäre ich glücklich") | **7,00** | 1,05 |
| zwei Spalten je Partie (Nutzer: "solides Ergebnis") | 14,00 | 1,05 |

Die Rechnung dahinter, geprüft: eine geschlossene Spalte bringt **21
Platzierungspunkte plus 7 Plattenpunkte = 28**. Eine Spalte ist also kein
Plattenposten neben dem Spiel, sondern rund ein Fünftel eines guten Endstands
(Bezug: Champion-Endstand ~48–53). Das erklärt auch, warum der Hebel überhaupt
lohnt — und es korrigiert meine frühere Einordnung, die 7 Plattenpunkte gegen 1–3
Platzierungspunkte gestellt hat, ohne die 21 mitzuzählen.

**Vorab festgelegt**: die Provokationsstufe ist bestanden bei **>= 7,00**
vertikalen Plattenpunkten, also einer Spalte je Partie. Alles darunter ist keine
Provokation, sondern wieder eine Nuance. Bei der auf 0,35 gequantelten Metrik
(7 Punkte / 20 Partien) ist das ein Sprung um zwanzig Ereignisse und damit weit
über jedem Rauschen — anders als alle Effekte dieser Nacht.

## 3. Warum es NICHT über die Bewertung gehen kann

Fünf Anläufe über die Blatt- bzw. Platzierungsbewertung sind gescheitert
(`PREREG_platzierungsseite.md` §7–14, `PREREG_injektion_wertungsplatten.md`).
Der gemeinsame Grund: eine Spalte verlangt eine **Farbfestlegung je Musterreihe,
auf eine bestimmte Spalte gerichtet, über mehrere Runden gehalten**. Das ist eine
ABSICHT. Eine Stellungsbewertung kann sie nicht darstellen, und mehr Suchbudget
findet sie auch nicht (16x Budget → −0,35, gemessen).

Belegt dazu: `dome.rs:61-70` — jede normale Kuppelzelle verlangt GENAU EINE Farbe
(`Some(color) == self.required_color`), und eine Musterreihe trägt nur eine Farbe.
Sechs Zellen einer Spalte sind also sechs festgelegte Farben in sechs
Musterreihen.

## 4. Der Eingriff: Beschneidung der AKTIONSMENGE, kein neuer Bewerter

Zu Partiebeginn wird ein **Ziel** festgelegt: eine Spalte `c` und die sechs
Farben, die ihre Zellen fordern (aus `required_color` der sechs Zellen ablesbar,
also ohne Schätzung). Die Suche spielt dann ihr bestes Spiel, aber nur unter
Zügen, die mit diesem Ziel vereinbar sind — eine Musterreihe, die für Zelle
`(r,c)` gebraucht wird, nimmt keine andere Farbe an.

Zwei Eigenschaften, die das von der Injektion unterscheiden:

1. Es erzwingt die Absicht **konstruktiv**, statt sie zu belohnen. Die Suche kann
   nicht wegdriften, also braucht sie die Absicht nicht selbst zu bilden.
2. Es ist **von der Sichtweite unabhängig** — genau die Größe, die als Ursache
   ausgeschlossen wurde.

Die Suche bleibt regelkonform und stark: sie wählt weiter frei, nur aus einer
kleineren Menge. Das ist eine Beschneidung, keine Vorgabe des Zuges.

**Diagnose-Knopf, nicht Spielparameter** (wie `MOSAIC_VOLLE_VERSORGUNG`): Default
aus, und eine so gespielte Partie darf nie in ein Gating geraten. In einen
TRAININGSKORPUS darf sie — die Ownership-Ziele sind die realisierten
Endzustands-Feldlabels und bei jeder Steuerung korrekt.

## 5. Was die Messung entscheidet, und was sie kostet

Eine halbe Stunde auf denselben 20 k1-Seeds, Metrik wie durchgehend.

- **>= 7,00**: die Methode ist da. Dann geht sie mit `MOSAIC_WERTUNG_STREUUNG_MAX`
  ins Self-Play (Stufe 2), und der Korpus enthält Spaltenabschlüsse in einer
  Häufigkeit, an der ein Kopf lernen kann.
- **< 7,00**: auch die Beschneidung ist zu schwach. Dann ist die Erkenntnis für
  eine halbe Stunde gekauft statt für Stunden Self-Play plus Training — und die
  Frage wäre, ob das Ziel im Zwei-Spieler-Spiel gegen einen Gegner, der dieselben
  Fliesen braucht, überhaupt einseitig erzwingbar ist.

## 6. Reihenfolge, ausdrücklich

Stufe 1 (diese Datei) VOR Stufe 2 (Streuung ins Self-Play). Das Werkzeug für
Stufe 2 ist gebaut und bleibt unbenutzt, bis Stufe 1 ihre Zahl hat. Genau diese
Reihenfolge hatte ich verwechselt.
