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


---

## 7. ABNAHME VERFEHLT (2026-08-12) — und zwar weil die Beschneidung ZU STARK ist

Sechs Zellen, je Ziel-Spalte einzeln, 20 k1-Seeds, ohne Injektion.

| Ziel-Spalte | vertikal | Abschlüsse/20 | Endstand | Strafleiste |
| ----------: | -------: | ------------: | -------: | ----------: |
| 0 | 1,05 | 3 | **6,25** | **23,00** |
| 1 | 1,40 | 4 | 8,30 | 22,65 |
| 2 | 1,05 | 3 | 7,45 | 22,85 |
| 3 | 1,05 | 3 | 11,15 | 21,05 |
| 4 | 1,05 | 3 | 15,30 | 16,85 |
| 5 | 0,70 | 2 | 7,60 | 22,60 |
| **Bezug ohne Provokation** | **1,05** | **3** | **47,80** | **9,35** |

Ziel war >= 7,00. Höchstwert 1,40, also verfehlt um Faktor 5.

### Die Diagnose ist NICHT "zu schwach"

Mein Messskript hat "die Beschneidung ist zu schwach" ausgegeben. **Das ist
falsch**, und die Zahlen sagen das Gegenteil: der Endstand bricht von 47,80 auf
6-15 ein, die Strafleiste steigt von 9,35 auf **bis zu 23**. Das Netz nimmt
permanent Fliesen, die es nicht platzieren kann — weil ihm alles andere verboten
ist. Die Beschneidung ist **zu stark**, nicht zu schwach.

Die Spaltenabschlüsse selbst bewegen sich dabei kaum (3 statt 3, einmal 4). Die
Beschneidung erzwingt also die Absicht, ohne das Ziel zu erreichen, und zerstört
das Spiel dabei.

### Der Konstruktionsfehler, und er ist derselbe wie vorher

Ich habe die Beschneidung auf **alle sechs Musterreihen** und die **ganze Partie**
gelegt. Ein Mensch, der eine Spalte baut, legt nicht fünf Runden lang sechs Reihen
auf je eine Farbe fest — er bindet sich **opportunistisch**, wenn die passende
Farbe erscheint, und spielt sonst normal. Meine Fassung erzwingt die Absicht so
total, dass kein Spiel übrig bleibt.

Zweitens kann eine Beschneidung das **Erscheinen** der Fliesen nicht erzwingen.
Die Deckenprobe (`PREREG_platzierungsseite.md` §14) hat gezeigt, dass volle
Verfügbarkeit allein nicht hilft; hier zeigt sich die andere Seite: eine Bindung
an eine Farbe, die nicht kommt, kostet Strafpunkte statt Fortschritt.

### Was daraus folgt — die naheliegende Verfeinerung, NICHT gemessen

Drei Lockerungen, jede einzeln prüfbar:

1. **Weniger Reihen binden.** Nur die billigen (Musterreihe 0-3 kosten 1+2+3+4 = 10
   Fliesen) statt aller sechs; die teuren bleiben frei. Die fehlenden Zellen
   müssten dann aus Spezialfeldern kommen — und die füllen Zellen ohne Fliese
   (`dome.rs:54-59`).
2. **Nur binden, wenn ein Alternativzug existiert.** Die Beschneidung greift nur,
   solange ein Nicht-Bodenzug übrig bleibt. Heute ist der Fallback erst bei
   VOLLSTÄNDIG leerer Menge aktiv, und Bodenzüge zählen als Alternative — genau
   deshalb steigt die Strafleiste auf 23.
3. **Erst ab Runde 2 oder 3 binden.** In Runde 1 steht die Farbverteilung noch
   nicht, eine frühe Bindung ist die teuerste.

**Punkt 2 ist der aussichtsreichste** und erklärt die Zahlen am direktesten: die
Strafleiste ist der Preis dafür, dass Bodenzüge als gültige Alternative gelten und
die Beschneidung deshalb fast nie in ihren Fallback läuft.

### Stufe 2 bleibt gesperrt

Bis eine Fassung >= 7,00 erreicht, geht kein Korpus ins Self-Play. Ein Korpus aus
Partien mit Endstand 8 und Strafleiste 22 wäre schädlicher als keiner — er würde
dem Netz beibringen, dass Spaltenbau mit Zusammenbruch einhergeht.


---

## 8. NEUEINORDNUNG (Nutzer, 2026-08-12): die Provokation ist ein DIAGNOSEINSTRUMENT

*"die provokation an sich ist schon in ordnung damit wir wissen welche
stellschrauben zu drehen sind"*

Ich hatte sie nach der verfehlten Abnahme als eigenen Irrweg abgetan ("meine
Erfindung, nicht der Plan"). Das war falsch: ihr Wert liegt nicht darin, Spalten zu
PRODUZIEREN, sondern darin zu zeigen, WAS bricht, wenn man die Absicht erzwingt.
Und sie hat geliefert.

### Was sie zeigt

Erzwingt man die Farbbindung, bricht **nicht** der Spaltenbau -- der bleibt bei 3-4
Abschlüssen wie ohne Provokation. Es bricht die **PLATZIERBARKEIT**:

| Größe | ohne Provokation | mit Provokation |
| ----- | ---------------: | --------------: |
| Strafleiste | 9,35 | **16,85 - 23,00** |
| Endstand | 47,80 | **6,25 - 15,30** |
| Spaltenabschlüsse | 3 | 3 - 4 |

Der Spieler nimmt die richtige Farbe und **kann sie nicht loswerden**.

### Und das ist dieselbe Stellschraube wie das einzige signifikante Ergebnis

`MOSAIC_WERTUNG_FLOOR_W` (der `projected_unplaceable_penalty`-Gegenterm) war der
EINZIGE Eingriff dieser Session mit einem signifikanten Effekt: **+2,77 Punkte
(t=2,21)** und **+1,37 Plattenpunkte (t=2,19)** gepaart gegen dieselbe Dosis ohne
ihn (`PREREG_injektion_wertungsplatten.md`).

**Zwei völlig verschiedene Versuche benennen denselben Engpass**: einer über
Belohnung (der Gegenterm hilft, weil er unplatzierbare Züge bestraft), einer über
Zwang (die Provokation scheitert, weil sie unplatzierbare Züge erzwingt). Der
begrenzende Faktor beim Plattenbau ist die **Platzierbarkeit**, nicht die
Plattenbewertung.

Das ist ein Befund über die Stellschraube, nicht über die Provokation -- und er
war ohne sie nicht zu sehen. Die Injektionsversuche allein zeigten nur, dass die
Strafleiste mit der Dosis steigt (9,35 → 11,77); erst der Zwang macht sichtbar,
dass sie der bindende Engpass IST und nicht eine Nebenwirkung.

### Folge für die Reihenfolge

Die Provokation bleibt als Instrument stehen (Knopf, Default aus). Die
Verfeinerungen aus §7 sind damit keine Rettungsversuche eines gescheiterten
Ansatzes, sondern Varianten eines Messmittels -- und die aussichtsreichste (§7
Punkt 2: nur binden, solange ein Nicht-BODENzug übrig bleibt) ist genau die, die
den identifizierten Engpass adressiert.

**Für Stufe 1 ist sie nicht nötig** -- die Injektion hat ihr Kriterium erfüllt
(Konjunktions-Rate 0,0167 → 0,0500, Faktor 12 über der Totgrenze 0,004, siehe
`STATUS.md` Übergabe-Block). Die Provokation ist das Werkzeug, mit dem man
herausfindet, welche Schraube man in Stufe 2 dreht.


---

## 9. VIER MECHANISMEN, EINE DECKE: 0,30 Spalten je Partie

| Generator | beste Zelle | Endstand | Spiel |
| --- | ---: | ---: | --- |
| Injektion (Belohnung) | 2,10 | 45,30 | intakt |
| Beschneidung (Zwang), beide Fassungen | 1,40 | 8-24 | zerstoert |
| Vorzug Drafting (Praeferenz) | 2,10 | 43-46 | intakt |
| Vorzug Drafting + Tiling-Routing | 2,10 | 39-44 | intakt |

Alle Protokolle: `generator_matrix_protokoll.json`. Die 5/6-Mauer bleibt in jeder
Fassung (9-13 von 20 Partien).

**Blocker-Klassifikation der 6. Zelle** (18 Mauer-Partien): 10x "Reihe lieferte,
Tiling legte anderswo hin", 8x "Reihe kam nie zusammen". ABER: die Klassifikation
prueft nicht, ob die gelieferte FARBE der geforderten entsprach -- eine Reihe voll
Blau kann eine Rot-Zelle nie bedienen, das Tiling weicht dann korrekt aus. Der
Tiling-Vorzug (gebaut, `tiling_solver.rs::vorzug_tiling_step`) konvertierte die
B-Faelle NICHT -- das stuetzt den Verdacht, dass ein Teil davon in Wahrheit
Farb-Faelle sind. **Naechster Diagnoseschritt: die B-Faelle nach gelieferter
gegen geforderter Farbe aufschluesseln.**

**Die offene Grundsatzfrage an den Nutzer**: vier Mechanismen enden bei 0,30 je
Partie mit intaktem Spiel. Das Stufe-1-Kriterium (Labels variieren) war schon bei
der Injektion allein erfuellt (Rate 0,0500 = 12x ueber der Totgrenze). Entweder
(a) den 0,30-Generator akzeptieren und den Korpus-Pilot fahren -- der Kopf braucht
Ereignisse, nicht Perfektion --, oder (b) weiter am Generator arbeiten (Farb-
Diagnose, dann ggf. echter Spaltenbau-Spieler). Der 1,0-Anspruch stammt aus der
Erwartung an das FERTIGE Netz; ob der GENERATOR ihn braucht, ist nicht belegt.
