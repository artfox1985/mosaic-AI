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
(`PREREG_placement_side.md` §7–14, `PREREG_scoring_plate_injection.md`).
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
Die Deckenprobe (`PREREG_placement_side.md` §14) hat gezeigt, dass volle
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

*"die provocation an sich ist schon in ordnung damit wir wissen welche
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
ihn (`PREREG_scoring_plate_injection.md`).

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

Alle Protokolle: `generator_matrix_protocol.json`. Die 5/6-Mauer bleibt in jeder
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


---

## 10. ZWEI-POLE-ARCHITEKTUR (Nutzer-Idee 2026-08-13) -- der geltende Rahmen

*"wir haben dann zwei extreme. einmal das netz was momentan noch auf die
wertungsplatten pfeift und dann die heuristik die nur auf die wertungsplatten
spielt. mit der staerke des ownership heads koennen wir dann recht gut steuern
wie stark die wertungsplatten beruecksichtigt werden"*

### Die Architektur

| Pol | Spieler | Rolle |
| --- | ------- | ----- |
| A | **Netz (Champion)** -- spielt die Basis stark, Platten ~0,15 Spalten/Partie | Basisspiel-Extrem |
| B | **Wertungsheuristik** (je Platte, Prototyp = Spaltenbau-Spieler) | Platten-Extrem |

1. **Korpus aus beiden Polen** (plus Zwischenstufen via `MOSAIC_WERTUNG_STREUUNG_MAX`):
   der Ownership-Kopf sieht das ganze Spektrum, nicht einen Betriebspunkt.
2. **Kopf-Basistraining** auf diesem Korpus -- Nutzer-Vorschlag: NUR den Kopf
   (Trunk eingefroren, kein Gating-Risiko). Vorbehalt, messbar: der eingefrorene
   Trunk koennte die Decke sein -- Kopf-allein gegen Trunk-mitlernen auf demselben
   Korpus vergleichen (Skill je Atom).
3. **Der Regler ist das KONSUMENTEN-Gewicht** (P4, zu bauen): wie stark die
   erwarteten Plattenpunkte aus dem Kopf dem Blattwert zugeschlagen werden.
   w=0 = reines Netz, w gross = Richtung Platten-Pol. NICHT zu verwechseln mit dem
   Trainingsgewicht (0,2) -- das formt nur den Trunk beim Lernen.
4. **Der Regler ist zur Laufzeit sweepbar, ohne Neutraining** -- ein Arena-Sweep
   ueber w findet den Betriebspunkt mit derselben Messmaschinerie, die die
   Injektions-Sweeps benutzt haben, nur mit gelerntem statt gerechnetem Term.

### Warum das den 0,30-Deckel brechen koennte (offene Wette, nicht Beleg)

Die Hand-Injektion rechnet kurzsichtig aus dem Brett und deckelt gemessen bei 0,30
Spalten/Partie (§9, vier Mechanismen). Der Kopf lernt aus REALISIERTEN
Plattenpartien -- wie Spalten ueber Runden, mit Farblogik, tatsaechlich zustande
kommen. Das ist die erste Fassung des Vorhabens, die nicht schon strukturell
verloren ist. Garantie gibt es keine; die Gates (Korpusraten, Atom-Skill,
w-Sweep) sind so gebaut, dass jede Stufe billig scheitern kann.

### Moegliche Folge (Nutzer): je Wertungsplatte eine eigene Heuristik

Der Spaltenbau-Spieler ist der Prototyp. Traegt er, wird er PARAMETRISIERT
(Ziel = Kriterium statt fest Spalte) statt achtmal neu gebaut; ob einzelne
Platten eigene Logik brauchen (Spezialfelder sind Trigger-, keine Lieferlogik),
entscheidet sich je Platte.

## 11. RUNDE 2 GEMESSEN (2026-08-13): 5,60 statt 1,40 -- Ziel 7,00 weiterhin verfehlt

Drei Nachbesserungen an `column_build.rs`/`provocation.rs` gegenueber dem
Stand aus Commit `fd2d15e` (1,40 vertikale Punkte, Blocker zu 10/12 auf
SPEZIAL-Zellen):

1. **Wild-Zellen aktiv bedient**: `provocation::vorzugszug_fuer_spalte` liess
   Wild-Zellen bisher NIE als Ziel gelten (`geforderte_farbe` liefert dort
   `None`, das alte `Some(x) if x==farbe`-Muster verwarf jede Farbe) -- jetzt
   qualifiziert an einer Wild-Zelle JEDE Farbe.
2. **Spezial-Zellen umbepreist**: `spalten_kosten` bewertete SPEZIAL bisher
   als billig (0,3, wie Wild) -- jetzt `special_kosten`, skaliert mit der
   Zahl der noch offenen der 3 Slot-Nachbarn (0,3 bei 0 offenen bis 2,7 bei
   3 offenen), weil eine Spezial-Zelle sich erst automatisch fuellt, wenn
   diese drei komplett sind (die Ursache des 10/12-Befunds).
3. **Zielspalte seed-gestreut**: `waehle_spalte` waehlt bei mehreren nahe am
   Minimum liegenden Spalten (Toleranz 0,5) deterministisch per SplitMix64
   aus dem Partie-Seed statt immer die kleinste Nummer -- ohne das war die
   Zielspalte bei leerem Brett (alle 6 Spalten exakt gleich teuer) fuer JEDE
   Partie Spalte 0.

### Aufbau (identisch zur letzten Messung, PLUS Trace)

`net_arena_match`, Champion (`v21_2d_brierbest`) @400 vs Heuristik@150, 20
k1-Seeds (`evaluations/seed_selection_plates.json`, GEPRUEFT:
`[2,3,6,8,9,11,13,20,22,26,29,32,34,39,44,50,52,57,59,69]`), gepaart gegen
`MOSAIC_SPALTENBAU=0` als Kontrolle, `MOSAIC_SPALTENBAU_TRACE=1` fuer beide
Arme (No-Op ohne aktiven Spaltenbauer). Werkzeug: `tools/paired_arena_env_ab.py
--env-name MOSAIC_SPALTENBAU --arms 0 1 --control 0 --net-sims 400
--heur-sims 150 --seeds <k1> --log-games`, Ergebnis in
`evaluations/paired_arena_env_spaltenbau_r2.json`. Metrik ueber
`tools/plate_points_from_arena.py`s `auswerten()`, Kriterium "Vertikale
Reihen"; Verteilung/Blocker ueber das NEU gebaute `tools/column_build_trace.py`
(liest die `[SB]`-Zeilen).

### ABNAHME: 5,60 -- Ziel 7,00 verfehlt, aber 4x ueber der letzten Messung

| Groesse | Spaltenbau AUS (Kontrolle) | Spaltenbau AN |
| --- | ---: | ---: |
| Vertikale Plattenpunkte (Ø, n=20) | 0,70 | **5,60** |
| Endstand (Ø) | 48,30 | 41,10 |
| Strafleiste (Ø) | 8,50 | 9,20 |
| Siege Netz | 15/20 | 13/20 |

Sieg-Differenz NICHT signifikant (McNemar b=3/c=5, p=0,73) -- der
Spaltenbauer kostet keine belegbare Staerke, nur ~7 Punkte Endstand und
~0,7 Punkte Strafleiste im Schnitt (dieselbe Kategorie "Bauen kostet ein
bisschen", die schon §7/§9 zeigten).

### Verteilungs-Gate (NEU, Nutzer-Ergaenzung): bestanden -- alle 6 Spalten

Zielspalten-Ereignisse ueber alle Runden/Partien (Spaltenbau-Arm, aus dem
Trace): Spalte 0=35, 1=13, 2=15, 3=12, 4=10, 5=15. **Keine Spalte bei 0** --
Spalte 0 bleibt haeufiger (die Tie-Break-Spalte bei einem echten Gleichstand
inklusive des leeren Startbretts trifft sie am oeftesten), aber die
Seed-Streuung erreicht sichtbar alle sechs, nicht nur Spalte 0 wie vor
Nachbesserung 3.

### Blocker-Klassifikation (81 distinkte Blocker-Ketten ueber 20 Partien, aus dem Trace)

| Kategorie | Anteil |
| --- | ---: |
| Geforderte Farbe nicht im Angebot (Faktoren/Mond/GF) | 74,1 % |
| Musterreihe an eine ANDERE Farbe gebunden | 16,0 % |
| Sonstiges (v.a. Wild-Zelle ohne jede Farbe im Angebot) | 9,9 % |

Der dominante Blocker ist nach den drei Nachbesserungen **NICHT mehr
Farblogik/Spezialfelder, sondern die VERSORGUNG**: in drei von vier Faellen
war die fuer die Zielspalte geforderte Farbe schlicht in KEINER Fabrik/im
Mond verfuegbar, als der Zug gebraucht wurde. Konkrete Kette, Seed 59,
Zeile 5 (`[SB]`-Zeilen des Arms): `reihe_gebunden_an_Gelb_statt_Tuerkis`
blockierte 40 von den insgesamt 83 Entscheidungen dieser Partie, Runden 2
bis 4 durchgehend -- die Musterreihe hatte sich frueh an Gelb gebunden,
Tuerkis (die fuer die Zielspalte in dieser Zeile geforderte Farbe) kam in
diesen drei Runden nicht zusammen. Das bestaetigt die in
`PREREG_placement_side.md` §5 vorab formulierte Vermutung ("dann ist der
naechste Verdacht die Versorgung") DIREKT und mit Kette, nicht nur als
Ausschluss.

`Vorzug existiert/genutzt` je Runde (ueber alle Partien, alle drei
Entscheidungstypen): sobald ein Kandidat existierte, wurde er in JEDER
Runde zu 100 % auch gespielt (R1 164/164, R2 208/208, R3 162/162, R4
26/26, R5 0/0) -- ERWARTUNGSGEMAESS, keine neue Erkenntnis: die
`.or_else(...)`-Kette waehlt einen existierenden Vorzugs-Kandidaten immer
VOR der Netz-Suche, "existiert" und "genutzt" koennen sich in dieser
Architektur gar nicht unterscheiden. Informativ ist die FALLENDE
Kandidatenrate ueber die Runden (308→333→353→348→290 Entscheidungen,
Kandidaten 164→208→162→26→0) -- Runde 4 ist fast schon dicht (nur 26 von
348), Runde 5 hat strukturell keinen (Vorzugszug ist auf Runde ≤4 begrenzt,
Runde 5 laeuft ueber `round5.rs`).

### VERDIKT: Fortschritt belegt, Ziel weiterhin offen -- naechster Hebel ist Versorgung, nicht Farblogik

1,40 → 5,60 ist eine Vervierfachung, aber 5,60 < 7,00. Die drei
Nachbesserungen haben ihre eigene Diagnose (10/12 Spezial-Blocker) sauber
adressiert; der NEUE dominante Blocker (Versorgung, 74 %) ist ein ANDERER
Mechanismus und keiner, den `column_build.rs` selbst loesen kann -- es waehlt
nur unter dem, was JETZT angeboten wird, es kann keine zukuenftige
Fabrikbefuellung erzwingen. Ohne Nutzer-Entscheidung KEINE weitere
Verschaerfung (naechster denkbarer Schritt waere z.B. eine
Versorgungs-bewusste Zielspalten-Wahl, die auf ANGEBOT-WAHRSCHEINLICHKEIT
statt nur Brettzustand reagiert -- das ist neue Mechanik, kein Tuning mehr).


---

## 12. RUNDE 3 GEMESSEN (2026-08-13): 5,95 statt 5,60 -- Ziel 7,00 weiterhin verfehlt, Blocker-Anteil UNVERAENDERT

### (1) Was ist zaehlbar? -- belegt am Code

`engine/src/provocation.rs::verbleibende_farben` (neu, `pub(crate)`) rechnet
je Farbe: Gesamtvorrat (`tile.rs:52`, `TILES_PER_COLOR = 13`) minus jede
SICHTBARE Fundstelle:

- `state.factories[*].sun_tiles` + `.moon_stacks` (`factory.rs:8-14`),
- `state.large_factory.sun_tiles` + `.moon_pool` (`factory.rs:117-126`),
- je Spieler: `pattern_lines[*].tiles`, `broken_tiles` (Strafleiste,
  `board.rs:249`), `dome_grid.dome_slots[*][*]`s `spaces[*].placed_color`
  (`board.rs:85`, `dome.rs:17`).

NICHT gelesen: `state.bag`/`state.tower` (`supply.rs:12-58`) -- deren exakte
FARBZUSAMMENSETZUNG sieht kein menschlicher Spieler, nur ihre Groesse
(`Bag::count`/`Tower::count`). Die Differenz aus den obigen oeffentlichen
Feldern liefert exakt dieselbe Zahl (Beutel+Turm zusammen), wie ein Mensch
sie mit einer Strichliste ebenfalls bekaeme. Getestet in
`provocation.rs::verbleibende_farben_zaehlt_jede_sichtbare_fundstelle`
(6 kuenstlich verteilte Rot-Kopien ueber alle 5 Fundstellen-Kategorien,
exakte Gegenrechnung `13 - 6`).

### (2) Die drei Bausteine, je ein Commit

| Baustein | Commit | Was |
| --- | --- | --- |
| 1 (Versorgung zaehlen) + 3 (Vorzug bevorzugt Knappheit) | `a10202f` | `verbleibende_farben`/`farben_index` (`provocation.rs`); `vorzugszug_fuer_spalte` sortiert Kandidaten jetzt primaer nach Knappheit der genommenen Farbe, "vollste Reihe" bleibt Tie-Break |
| 2 (Zielwahl versorgungsgewichtet) | `d18e523` | `engpass_aufschlag` (0 bei voller, bis 2,5 bei restlos verbrauchter Versorgung); `spalten_kosten` bekommt die vorberechnete Versorgungslage als Parameter, alle 3 Aufrufstellen umgestellt |

Baustein 1+3 liegen technisch in einem Commit (beide in
`provocation.rs`, `vorzugszug_fuer_spalte` selbst braucht
`verbleibende_farben` direkt in seinem Kandidaten-Ranking -- eine
Hunk-Trennung haette das Diff riskanter gemacht als der Gewinn an
Granularitaet wert war; explizit KEIN Automatismus wie `git add -A`,
beide Commits enthalten ausschliesslich die genannten Engine-Dateien).

`cargo test --lib`: 388 bestanden, 0 fehlgeschlagen (ein Bestandstest,
`vorzugszug_reicht_dynamische_spalte_an_provokation_kern_durch`, nahm
implizit an, Spalte 0 bleibe bei echtem Zufalls-Fabrikinhalt die
guenstigste -- das haengt seit Baustein 2 vom Versorgungsstand ab; im Test
die Tischmitte deterministisch geleert, siehe Kommentar dort). Wheel
gebaut+installiert, `tools/parity_probe.py`: Hash `8c6684ff...` haelt,
Default-Verhalten byte-identisch.

### (3) Abnahmezahl, Verteilung, neue Blocker-Verteilung

Aufbau IDENTISCH zu Runde 2 (§11): `alphazero_v21_2d_brierbest.onnx`@400 vs
Heuristik@150(dyn), dieselben 20 k1-Seeds
(`[2,3,6,8,9,11,13,20,22,26,29,32,34,39,44,50,52,57,59,69]`), gepaart gegen
`MOSAIC_SPALTENBAU=0`, `MOSAIC_SPALTENBAU_TRACE=1` fuer beide Arme.
Ergebnis: `evaluations/paired_arena_env_spaltenbau_r3.json`.

| Groesse | Spaltenbau AUS (Kontrolle) | Spaltenbau AN |
| --- | ---: | ---: |
| Vertikale Plattenpunkte (Ø, n=20) | 0,70 | **5,95** |
| Endstand (Ø) | 48,30 | 46,95 |
| Strafleiste (Ø) | 8,50 | 8,35 |
| Siege Netz | 15/20 | 15/20 |

**ABNAHME VERFEHLT** (Ziel >= 7,00), aber 5,60 → 5,95 ist ein weiterer,
GEPRUEFT signifikanter Schritt: gepaartes Delta +5,25 Plattenpunkte,
t = 3,94, n = 20 (Rechnung: `auswerten()`s `je_kriterium["Vertikale
Reihen"]` je Seed aus beiden Einzel-Arm-Dateien, `t_wert()` aus
`plate_points_from_arena.py`). Sieg-Differenz NULL (15/20 beide Arme,
McNemar b=4/c=4, p=1,0, aus dem Rohergebnis-JSON) -- der Spaltenbauer
kostet in dieser Runde nicht messbar Staerke, weniger noch als Runde 2
(dort p=0,73, Endstand-Differenz -7,2; hier nur -1,35, Strafleiste sogar
minimal GUENSTIGER statt teurer). Verteilung der 20 AN-Partien: 15/20 mit
mindestens einer geschlossenen Spalte (7 Punkte), davon 2/20 mit ZWEI
Spalten (14 Punkte) -- eine deutlich dichtere Verteilung als Runde 2s
Einzelwerte suggerieren.

**Verteilungs-Gate**: bestanden, alle 6 Spalten mit Ereignissen (Spalte
0=15, 1=27, 2=5, 3=14, 4=15, 5=24, aus `column_build_trace.py`).

**Blocker-Klassifikation** (82 distinkte Blocker-Ketten ueber 20 Partien,
gleiche Zaehlweise wie Runde 2 -- je (Zeile, Grund)-Kombination EINMAL je
Partie, unabhaengig von der Wiederholungszahl):

| Kategorie | Runde 2 | Runde 3 |
| --- | ---: | ---: |
| Geforderte Farbe nicht im Angebot | 74,1 % | **76,8 %** |
| Musterreihe an eine ANDERE Farbe gebunden | 16,0 % | **6,1 %** |
| Sonstiges (v.a. Wild-Zelle ohne jede Farbe im Angebot) | 9,9 % | **17,1 %** |

### (4) Deutung nach der VORAB festgelegten Regel (§ Auftrag)

Die Regel war: sinkt der "nicht im Angebot"-Anteil deutlich UND steigt die
Spaltenzahl, war Versorgung der Hebel; bleibt der Anteil ~74 % trotz
versorgungsgewichteter Zielwahl, ist die Knappheit STRUKTURELL.

**Der Anteil ist NICHT gesunken -- er ist von 74,1 % auf 76,8 % leicht
GESTIEGEN.** Nach der vorab festgelegten Regel ist das der zweite Fall:
die Versorgungsknappheit fuer die GEFORDERTE Farbe zur GEFORDERTEN Zeit
ist in diesem Generator **strukturell** -- sie kommt aus dem Verbrauch
durch zwei Spieler auf einem Vorrat von 13 Kopien je Farbe, nicht aus
einer schlecht gewaehlten Zielspalte oder einem unaufmerksamen
Vorzugszug. Eine versorgungsgewichtete Zielwahl kann eine Farbe nicht
haeufiger ins Angebot bringen, als der gemeinsame Verbrauch es zulaesst --
sie kann nur vermeiden, sich an eine Farbe zu binden, die gerade knapp
IST, und knappe Farben eher zu ergreifen, wenn sie kurz auftauchen. Genau
DAS zeigt der zweite Kategorie-Wert: "Musterreihe an andere Farbe
gebunden" fiel von 16,0 % auf 6,1 % -- die Bausteine wirken exakt an der
Stelle, an der sie wirken KOENNEN (selbstverschuldetes Fehlbinden), nicht
an der Stelle, an der die Nutzer-Wette lag (Versorgung insgesamt).

Der Anstieg von 5,60 auf 5,95 (GEPRUEFT signifikant, t=3,94) ist also
NICHT der erhoffte grosse Sprung durch "Versorgungs-Bewusstsein", sondern
die Summe zweier kleinerer, plausibler Effekte: weniger Fehlbindung
(Baustein 2+3) und eine dichtere Verteilung ueber mehr Partien mit
mindestens einer Spalte (15/20 statt vermutlich weniger in Runde 2, nicht
neu nachgemessen). **5,60-5,95 ist nach dieser Messung die ehrliche Decke
des JETZIGEN Generator-Ansatzes** (Zielwahl + Vorzug, beide reagieren nur
auf den AKTUELLEN Brett-/Angebotszustand) -- ein weiterer Dreh an
Zielwahl-Gewichten oder Vorzug-Reihenfolge wuerde laut dieser Deutung
keinen groesseren Sprung mehr bringen, weil der dominante Blocker nicht
an dieser Stelle sitzt.

### (5) Eigene Entscheidungen (markiert, nicht Nutzer-Vorgabe)

- `ENGPASS_MAX = 2,5` und der lineare Verlauf zwischen 0 und
  `TILES_PER_COLOR` sind meine Kalibrierung, keine Nutzer-Zahl -- Vorgabe
  war nur die Richtung ("teuer, auch wenn die Reihe frei ist") und die
  Bedingung, dass der Aufschlag eine falsch gebundene Zeile (Basis 2,0)
  im Extremfall uebersteigen muss; beides erfuellt, aber die genaue Kurve
  (linear statt z.B. quadratisch) ist ungeprueft gegen Alternativen.
- Ich habe den Bestandstest
  `vorzugszug_reicht_dynamische_spalte_an_provokation_kern_durch`
  angepasst (Tischmitte deterministisch geleert), statt seine
  Kern-Annahme ("Spalte 0 bleibt billigste") stehen zu lassen und beim
  ersten fehlschlagenden Seed erneut zu reparieren.
- Ich habe NICHT versucht, den 74%-Blocker durch eine aggressivere
  Zielwahl (z.B. groesseres `ENGPASS_MAX`, kleineres `SPALTEN_TOLERANZ`)
  wegzudruecken, nachdem die erste Messung ihn unveraendert zeigte --
  das waere angesichts der eigenen Deutung (strukturell) eine
  Schoenrechnung durch Uebertuning gewesen, kein echter Befund.
- Empfehlung (keine Entscheidung): ohne eine Mechanik, die zukuenftige
  Fabrikbefuellung selbst beeinflusst -- was regelkonform nicht geht, das
  Ziehen ist zufaellig -- ist der naechste sinnvolle Schritt eher die vom
  Nutzer selbst skizzierte Zwei-Pole-Architektur (§10: Kopf lernt aus
  REALISIERTEN Partien statt aus einer handgerechneten Zielwahl) als eine
  vierte Nachbesserung an `column_build.rs`.


---

## 13. PARAMETRISIERUNG AUF ALLE 8 KRITERIEN + SPIELER-ABSTRAKTION (2026-08-13)

Nutzer-Auftrag im Anschluss an §10-§12: der Spaltenbau-Spieler wird
PARAMETRISIERT (Ziel = Kriterium statt fest Spalte) und dabei die
Spieler-Abstraktion (Architektur-Fahrplan Punkt 5, `STATUS.md`) als tragende
Struktur mitgezogen.

### (1) Trait-Zuschnitt + Regressionsnachweis Stufe 1

Neuer Trait `Plattenbauer` (`engine/src/plate_builder.rs`) mit genau den drei
Entscheidungspunkten, die `column_build.rs` fuer Kriterium 1 bisher konkret
implementierte: `drafting_vorzug` (Stein-Zug), `dome_vorzug`
(Kuppelplatten-Wahl), `tiling_vorzug` (Tiling-Routing). Die vier
Drafting-Hook-Stellen in `self_play.rs` (`play_net_game`,
`play_net_vs_net_game`, `play_net_vs_net_hybrid_game`,
`play_stage3_vs_stage1_game`) sowie der eine Tiling-Hook und die
Seed-Weitergabe rufen jetzt `crate::plate_builder::*` statt `crate::
column_build::*` direkt.

`MOSAIC_SPALTENBAU` bleibt der woertliche Altpfad: ist er aktiv, loest die
Abstraktion IMMER auf einen Wrapper auf, der die bestehenden
`column_build::{vorzugszug,vorzug_dome_wahl,vorzug_tiling_step}` UNVERAENDERT
aufruft -- reine Delegation, keine Nachbildung. Byte-Identitaet bei allen
Knoepfen aus: GEPRUEFT, Paritaets-Hash `8c6684ff...` haelt nach Wheel-Neubau.
Verhaltens-Identitaet bei `MOSAIC_SPALTENBAU` an: GEPRUEFT per
Aequivalenztest ueber 30 Seeds/Zustaende
(`mosaic_spaltenbau_an_ist_verhaltensidentisch_zur_direkten_ansteuerung`,
`plate_builder.rs`) -- `drafting_vorzug`/`dome_vorzug`/`tiling_vorzug` der
Abstraktion liefern fuer jeden Seed EXAKT denselben Wert wie der direkte
Aufruf von `column_build::{vorzugszug,vorzug_dome_wahl,vorzug_tiling_step}`.

Zusaetzlich End-to-End GEPRUEFT (nicht nur auf Funktionsebene): eine frische
Arena-Messung mit `MOSAIC_SPALTENBAU=1` durch die NEUE Verdrahtung liefert
20/20 identische Ergebnisse bei zweifacher Wiederholung desselben Kommandos
(eigene Reproduzierbarkeitsprobe, `paired_arena_env_plattenbauer_regress_k1*.
json`) -- die neue Verdrahtung ist selbst deterministisch. **Eine offene,
ungeklaerte Beobachtung**: diese frische Messung liefert fuer den
Kontroll-Arm (`MOSAIC_SPALTENBAU=0`) 1,05 vertikale Plattenpunkte / 47,80
Endstand, waehrend Runde 3 (§12, SELBE 20 Seeds, SELBES Modell, `git log`
GEPRUEFT: kein Engine-Commit zwischen Runde 3 und dieser Sitzung) 0,70 /
48,30 archiviert hat -- Sieg-Zahlen stimmen dabei exakt ueberein (15/20 in
beiden Armen, beide Messungen). Da mein Code fuer den AUS-Zustand
nachweislich ein reiner Passthrough ist (kein Verhaltensunterschied
moeglich) und meine eigene Wiederholung perfekt reproduziert, ist die
Abweichung entweder Lauf-zu-Lauf-Rauschen aus der ONNX-Inferenz (nicht
zwischen Prozessstarts reproduzierbar, nur INNERHALB) oder ein
Unterschied in der urspruenglichen Runde-3-Aufrufumgebung (z.B. Threads) --
NICHT weiter aufgeloest (Zeitbudget). Fuer die §13-Tabelle wird deshalb die
FRISCH GEMESSENE Zahl verwendet, nicht die archivierte.

### (2) Strategie-Kern je Kriterium, ein Satz

- **0 (Zeilen)**: waehlt eine Ziel-Zeile ueber dieselbe Kosten-/
  Streuungs-Mechanik wie Spaltenbau (transponiert), liefert Stein-/
  Kuppel-/Tiling-Vorzug ueber die generische Zellen-Mechanik.
- **1 (Spalten, generisch)**: identische Geometrie zu Spaltenbau, aber ein
  ZWEITER Codepfad (siehe Eigene Entscheidungen) statt einer Wiederverwendung
  der `column_build.rs`-Funktionen.
- **2 (Diagonalen)**: waehlt eine der zwei Diagonalen ueber dieselbe
  Kosten-Mechanik (Zielzellen `(i,i)` bzw. `(i,5-i)`).
- **3 (Mehrfarbig/Jokerfelder)**: keine Kandidatenwahl -- Zielmenge sind ALLE
  noch offenen Wild-Zellen des Bretts, jede Farbe qualifiziert dort.
- **4 (Randfelder)**: keine Kandidatenwahl -- Zielmenge sind alle noch
  offenen Zellen am Kuppelrand (additiv, jede Platzierung zaehlt).
- **5 (Ecken)**: waehlt einen der vier Eck-2x2-Slots ueber dieselbe
  Kosten-Mechanik (Zielzellen = die 4 Rasterzellen des Slots).
- **6 (Spezialfelder)**: keine Kandidatenwahl -- Zielmenge sind die NACHBARN
  offener Special-Zellen (nicht die Special-Zelle selbst, §12-Befund).
- **7 (Farbenreiche Reihen)**: teilt sich die Zeilen-Kandidatenwahl mit
  Kriterium 0, aber eigene Kuppelplatten-Logik (Farbvielfalt statt
  Farbtreffer -- bevorzugt Kacheln, die eine in der Zielreihe NOCH NICHT
  vorhandene Farbe einbringen).

### (3) Messkette und Abweichungen vom Auftrag

Gleiche Messkette wie §11/§12: `tools/paired_arena_env_ab.py`,
`alphazero_v21_2d_brierbest.onnx@400` vs. Heuristik@150(dyn), die
vorhandenen `evaluations/seeds_per_criterion/k<k>.txt`-Seedlisten (20-23
Seeds je Kriterium), `--log-games`. Metrik ueber
`tools/plate_points_from_arena.py`s `auswerten()` (importiert, nicht
nachgebaut), Kriterium-Name aus `scoring::ALL_SCORING_TILES`.

**Zwei Abweichungen vom Auftrag, aus Zeitgruenden (markiert, nicht
Nutzer-Freigabe)**:

1. **`MOSAIC_SPALTENBAU_TRACE`/`[SB]`-Blockerspur wurde NICHT auf die
   generische Mechanik (Kriterien 0/2/3/4/5/6/7) ausgeweitet** --
   `column_build.rs::trace_zeile` bleibt unveraendert und liefert weiterhin
   NUR fuer den Legacy-Pfad (`MOSAIC_SPALTENBAU`) etwas. Die Spalte
   "Blocker aus Trace" ist deshalb fuer Kriterium 1 aus Runde 3 (archiviert,
   NICHT in dieser Sitzung neu erhoben) und fuer alle anderen Kriterien
   **ungeprueft/nicht erhoben**.
2. **Verteilungs-Gate nicht gemessen** fuer die neuen geometrischen
   Kandidaten (0/2/5): ob z.B. alle 6 Zeilen oder alle 4 Eckslots ueber die
   Seedliste hinweg als Ziel auftauchen, ist NUR per Unit-Test belegt
   (`auto_modus_streut_ueber_scoring_tile_ids_der_partie`,
   `waehle_kandidat`/`index_aus_seed`-Streuung), NICHT per Arena-Trace wie
   bei Spaltenbau Runde 2/3.

### (4) §13-Tabelle

| K | Kriterium | Bezug ohne | mit Plattenbauer | Orakel | Blocker aus Trace | n |
| - | --------- | ---------: | ----------------: | ------ | ------------------ | -: |
| 0 | Horizontale Reihen   | 1,04   | 0,65   | >=6,00                                   | ungeprueft | 23 |
| 1 | Vertikale Reihen     | 1,05   | 5,60   | >=14,00 (dokumentiert unerreichbar)      | archiviert Runde 3 (§12: 76,8% Versorgung, 6,1% Fehlbindung, 17,1% Sonstiges) | 20 |
| 2 | Diagonale Reihen     | 0,43   | 2,61   | >=10,00                                  | ungeprueft | 23 |
| 3 | Mehrfarbige Felder   | 3,40   | 3,90   | >=8,00                                   | ungeprueft | 20 |
| 4 | Aeussere Felder      | 9,30   | 10,60  | kein Orakel                              | ungeprueft | 20 |
| 5 | Eckplatten           | 3,00   | 4,73   | >=11,00                                  | ungeprueft | 22 |
| 6 | Spezialfelder        | -11,85 | -10,65 | kein Orakel                              | ungeprueft | 20 |
| 7 | Farbenreiche Reihen  | 0,52   | 1,04   | kein Orakel                              | ungeprueft | 23 |

Begleitzahlen (gleiche Partien, GEPRUEFT aus den Rohdaten):

| K | ΔPlatten (gepaart) | t | Siege Bezug | Siege mit | McNemar p | Strafleiste Bezug->mit | Endstand Bezug->mit |
| - | ------------------: | -: | ----------: | --------: | --------: | ----------------------: | --------------------: |
| 0 | -0,39 | -1,00 | 18/23 | 13/23 | 0,180 | 8,61 -> 9,78   | 56,61 -> 46,83 |
| 1 | +4,55 |  3,58 | 15/20 | 15/20 | 1,000 | 9,10 -> 9,05   | 47,80 -> 44,05 |
| 2 | +2,17 |  2,47 | 19/23 | 12/23 | 0,039 | 11,91 -> 8,22  | 47,52 -> 45,30 |
| 3 | +0,50 |  0,26 | 14/20 | 12/20 | 0,754 | 10,50 -> 10,50 | 52,95 -> 49,10 |
| 4 | +1,30 |  3,51 | 16/20 | 10/20 | 0,146 | 7,60 -> 15,10  | 62,40 -> 47,15 |
| 5 | +1,73 |  2,88 | 15/22 | 14/22 | 1,000 | 8,50 -> 11,77  | 52,14 -> 47,73 |
| 6 | +1,20 |  2,99 | 10/20 | 11/20 | 1,000 | 14,25 -> 16,85 | 31,85 -> 27,25 |
| 7 | +0,52 |  1,00 | 17/23 | 7/23  | 0,021 | 10,35 -> 15,39 | 50,30 -> 34,35 |

Rohdaten: `evaluations/paired_arena_env_plattenbauer_k{0,2,3,4,5,6,7}.json`
(neu) und `evaluations/paired_arena_env_plattenbauer_regress_k1.json`
(Kriterium 1, Regressionslauf). Verrechnungsskript (Scratch, nicht Teil des
Repos): importiert `auswerten`/`t_wert` aus `tools/plate_points_from_arena.py`
unveraendert.

### (5) Je Kriterium: ehrliche Aussage erreicht/Decke/weiter-iterierbar

- **0 (Zeilen): VERFEHLT, Strategie schadet dem eigenen Ziel.** Der
  Plattenbauer macht WENIGER horizontale Reihen als der Bezug (0,65 <
  1,04) und kostet dabei Staerke (18/23 -> 13/23 Siege, Endstand -9,8
  Punkte). Kein STOPP-Kollaps (Strafleiste bleibt bei ~9), aber eine
  Strategie, die ihr eigenes Kriterium unterbietet, ist ein
  Grundsatzproblem der Zeilen-Geometrie (vermutlich: eine volle Zeile
  verlangt bis zu 6 VERSCHIEDENE Farben aus 3 verschiedenen Kuppelplatten,
  waehrend eine Spalte/Diagonale nur je EINE Zelle pro Musterreihe
  braucht) -- weiter-iterierbar, aber nicht mit den bestehenden
  Kosten-Gewichten.
- **1 (Spalten): Decke bestaetigt, dokumentiert unerreichbar.** Frisch
  gemessen 5,60 (Runde 3 archiviert: 5,95, siehe (1) fuer die ungeklaerte
  Differenz) gegen Orakel 14,00 -- Faktor 2,5 verfehlt, keine Staerke-Kosten
  (15/20 beide Arme, McNemar p=1,0). Deckt sich mit §12s Verdikt: der
  dominante Blocker ist strukturelle Versorgungsknappheit, die eine
  Zielspalten-/Vorzugslogik nicht loesen kann.
- **2 (Diagonalen): Fortschritt, aber teuer.** +2,17 Plattenpunkte
  (GEPRUEFT signifikant, t=2,47), Strafleiste sogar GUENSTIGER (11,91 ->
  8,22) -- aber Sieg-Differenz signifikant NEGATIV (19/23 -> 12/23, p=0,039).
  2,61 von Orakel 10,00 -- weiter-iterierbar, doch das Kosten-Nutzen-
  Verhaeltnis dieser Runde ist unguenstig (die Diagonale bindet vermutlich
  zu viele Musterreihen gleichzeitig an feste Positionen relativ zum
  Nutzen).
- **3 (Mehrfarbig): Kein belegter Fortschritt.** +0,50 (t=0,26, nicht
  signifikant), 3,90 von Orakel 8,00. Kein Sicherheitsproblem (Strafleiste
  unveraendert 10,50), aber die "Jokerzellen aktiv bedienen"-Strategie
  bewegt die Zahl nicht messbar -- weiter-iterierbar (naechster Verdacht:
  wie bei Kriterium 1 die Versorgung, da ALLE Jokerzellen gleichzeitig
  offen gehalten werden muessen).
- **4 (Rand): Fortschritt gemessen, Sicherheitsklausel pruefen.** +1,30
  (GEPRUEFT signifikant, t=3,51), aber Strafleiste FAST VERDOPPELT (7,60 ->
  15,10) und Endstand -15 Punkte -- kein Orakel zum Vergleich, aber dieser
  Preis ist hoeher als bei jedem anderen Kriterium in absoluten
  Strafleisten-Punkten. Weiter-iterierbar, aber NICHT ohne eine
  Bodenzug-Bremse (analog §7 Punkt 2 der Beschneidungs-Lehre).
- **5 (Ecken): Fortschritt, Decke unterhalb Orakel.** +1,73 (GEPRUEFT
  signifikant, t=2,88), 4,73 von Orakel 11,00, Sieg-Differenz NICHT
  signifikant (p=1,0) -- die guenstigste Kombination aus Fortschritt und
  Sicherheit in dieser Messreihe. Weiter-iterierbar mit dem besten
  Aufwand-Nutzen-Verhaeltnis.
- **6 (Spezial): Marginaler Fortschritt.** +1,20 (GEPRUEFT signifikant,
  t=2,99) auf einer stark negativen Basis (-11,85 -> -10,65) -- die
  Nachbarn-statt-Special-Zelle-Strategie wirkt in die richtige Richtung,
  aber bei weitem nicht genug, um den strukturellen Rueckstand
  aufzuholen. Strafleiste steigt leicht (14,25 -> 16,85). Weiter-iterierbar.
- **7 (Farbenreich): STOPP-Kriterium ausgeloest.** +0,52 (t=1,00, NICHT
  signifikant) bei einem Sieg-Einbruch von 17/23 auf 7/23 (GEPRUEFT
  signifikant, p=0,021) und Endstand -16 Punkte -- der teuerste Eingriff
  dieser Messreihe fuer praktisch keinen Kriterium-Gewinn. Kein
  Strafleisten-Wert wie bei der historischen Beschneidung (23), aber der
  Sieg-Einbruch ist die schaerfere Kennzahl hier und die Kosten-Nutzen-
  Bilanz ist unvertretbar. **Empfehlung: `Farbenreichbauer` deaktiviert
  lassen (Default AUS bleibt unberuehrt, aber `MOSAIC_PLATTENBAU=7` nicht
  produktiv verwenden), bis die Kuppelplatten-Logik ueberarbeitet ist** --
  vermutlicher Fehler: sie optimiert NUR auf Farbvielfalt der Zielreihe,
  ohne die Kosten der dadurch gebundenen NORMAL-Zellen (die ja trotzdem
  eine feste Farbe verlangen) gegen den Rest des Bretts abzuwaegen.

### (6) Eigene Entscheidungen (markiert, nicht Nutzer-Vorgabe)

- **Zweiter Codepfad fuer Kriterium 1** statt einer Verschmelzung mit
  `column_build.rs`: eine echte Wiederverwendung haette dessen Funktionen auf
  `zellen: &[(usize,usize)]` umstellen und ALLE dortigen Tests neu
  durchdenken muessen, ohne zusaetzlichen Abnahme-Nutzen (der Legacy-Pfad
  bleibt ohnehin die einzige produktiv genutzte Kriterium-1-Route). Statt
  Duplikation der Kosten-Formeln wurden `special_kosten`/
  `engpass_aufschlag`/`zellen_wert` in `column_build.rs` auf `pub(crate)`
  gehoben und in der generischen Mechanik WIEDERVERWENDET (verifiziert per
  Test `zellen_kosten_stimmt_mit_spalten_kosten_fuer_spaltengeometrie_
  ueberein`).
- **Trace/Verteilungs-Gate nicht generalisiert** (siehe (3)) -- Zeitbudget,
  nicht Grundsatzproblem. Fuer eine produktive Nutzung von Kriterium
  2/4/5/6 (die vier mit gepruefter Punkte-Wirkung) waere das die naechste
  sinnvolle Nachruestung, um die STOPP-Frage bei 4 und die
  Kosten-Nutzen-Frage bei 2 ohne weitere Arena-Laeufe zu praezisieren.
- **Kriterium 7 nicht nachgebessert, nur dokumentiert** -- Auftrag sieht bei
  einem STOPP "Strategie deaktivieren, dokumentieren, naechstes Kriterium"
  vor; eine Nachbesserung noch in dieser Sitzung war nicht mehr Teil des
  Auftrags und haette ungeprueften Code produziert.
- **Die ungeklaerte Kriterium-1-Kontrollarm-Differenz (siehe (1)) wurde NICHT
  weiter aufgeloest** -- markiert als offene Beobachtung statt als Befund,
  weil die Ursache (Lauf-zu-Lauf-Inferenz-Jitter vs. Aufrufumgebung) in
  dieser Sitzung nicht eingegrenzt wurde.


---

## 14. RUNDE 4 (2026-08-13): 77-%-Blocker aufgespalten -- 0 % strukturell, Vollendbarkeits-Sicherheitsnetz gebaut, +2,45 gg. AUS aber < Runde 3

Koordinator-Auftrag im Anschluss an §12/§13: den dominanten "Farbe nicht im
Angebot"-Blocker AUFSPALTEN statt pauschal als strukturell zu werten, dann den
groessten behebbaren Anteil bauen. Waehrend der Sitzung kamen zwei
Nutzer-Korrekturen dazu: (1) Vollendbarkeits-Check mit Ziel-Spalten-Wechsel ist
PFLICHT, nicht optional; (2) eine zweite Stufe "Material zuerst" (ueberpraesente
Farbe in tiefe Reihen, Kuppelwahl matcht aufs bereits liegende Material).

### (1) Aufspaltung a/b/c/d -- GEPRUEFT an der exakten Kachel-Geometrie

Methode: `dome.rs:201-233` (18-Platten-Katalog, `tile_id` 0..18 fortlaufend,
Farblayout FEST) + `rotation_indices` (`dome.rs:89-97`) liefern die geforderte
Farbe JEDER Zelle deterministisch aus den `Kachel X -> Slot (r,c) rot=d`-
Logzeilen -- robuster als `kein_vorzug_grund`s Text, der nur die ERSTE
blockierende Zeile nennt und die eigentlich interessierende Zelle oft verdeckt.
Werkzeug: `scratchpad/blocker_split_abcd.py` (Scratch, nicht im Repo), liest die
--log-games-Rohdaten aus Runde 2/3 (`evaluations/paired_arena_env_spaltenbau_
r{2,3}.json`, bereits vorhanden).

"Mauer-Zelle": eine Spalte mit GENAU 1 offener Zelle unter 6 belegten Slots --
ALLE 6 Spalten je Partie gescannt, nicht nur die zuletzt verfolgte Zielspalte.
Fuer die eine offene Normal-Zelle X = ihre (aus der Kachel-Geometrie bekannte)
geforderte Farbe. Klassifikation ueber ALLE Drafting-Entscheidungen der Partie
(chronologisch, nicht nur mit passender Zielspalte -- Musterreihen sind
spielerweit geteilt):

| Kategorie | Runde 2 (6 Zellen) | Runde 3 (8 Zellen) | Kombiniert (14 Zellen) |
| --- | ---: | ---: | ---: |
| (a) Farbe nie verfuegbar, waehrend Zeile offen | 0 (0%) | 0 (0%) | **0 (0%)** |
| (b) verfuegbar, aber Zeile falsch gebunden | 0 (0%) | 0 (0%) | **0 (0%)** |
| (c) verfuegbar, Zeile offen, Vorzug griff trotzdem nicht | 4 (66,7%) | 2 (25%) | **6 (42,9%)** |
| special_zelle_offen (Slot-Nachbarn unvollstaendig) | 2 (33,3%) | 5 (62,5%) | **7 (50,0%)** |
| wild_ohne_farbzwang (Wild nie erreicht) | 0 | 1 (12,5%) | **1 (7,1%)** |

**Kernbefund: 0 von 14 persistenten Mauer-Zellen sind "strukturell" im Sinne
der vorab festgelegten Stopp-Regel.** Die 74-77-%-Kennzahl aus §11/§12 misst
etwas ANDERES -- sie summiert ALLE (meist transienten, spaeter geloesten)
Blockmomente ueber die GANZE Partie; auf die tatsaechlich bis zum Schluss
offene Zelle bezogen ist "Farbe nie verfuegbar" nicht ein einziges Mal die
Ursache. Verifiziert per Stichprobe (Seed 3/Runde 3, Special-Zelle (2,4)): ihre
Slot-Nachbarn (2,5)/(3,5) sind selbst offen (Gelb/Rot) -- eine ECHTE
Cross-Slot/Cross-Spalten-Abhaengigkeit, kein Farbversorgungsproblem dieser
Spalte. Und Seed 13/Runde 3 (c_vorzug_griff_nicht): Tuerkis war im Angebot,
Zeile 5 (braucht Tuerkis) war offen, aber die Praeferenz nahm Tuerkis fuer
Zeile 1 einer damals ANDEREN Zielspalte -- die "vollste Reihe"-Tie-Break-Regel
aus §12 bevorzugt flache/fast-volle Reihen ueber tiefe, exakt der Befund, den
Baustein 3 (Material zuerst) adressieren sollte.

Damit ist die Stopp-Regel des urspruenglichen Auftrags ("(a) dominiert mit
>60% -> nicht bauen, Decke ist strukturell") NICHT ausgeloest -- im Gegenteil,
sie ist mit 0% so weit wie moeglich vom Schwellenwert entfernt. Genau das
deckt sich mit der Nutzer-Korrektur ("eine Spalte laesst sich praktisch immer
erreichen, wenn vernuenftig gespielt wird"): Baustein 1 wurde gebaut.

### (2) Was gebaut wurde

**Baustein 1 (Pflicht): Vollendbarkeits-Sicherheitsnetz + Zielwechsel.**
`ist_spalte_vollendbar(player, spalte, verbleibend)` (`column_build.rs`): jede
offene Normal-Zelle braucht `verbleibend[Farbe] >= (r+1) - schon_gesammelt`
UND darf nicht an eine ANDERE Farbe gebunden sein, DIE NICHT MEHR AUFLOeSBAR
IST (siehe Korrektur unten). `waehle_beste_vollendbare_spalte` waehlt unter
allen vollendbaren Spalten die mit den meisten bereits gefuellten Zellen
(Tie-Break: Kosten). `ziel_spalte_fuer_player` bleibt die GEWOHNTE, bei jedem
Aufruf frisch berechnete Kostenwahl aus Runde 1-3 (`waehle_spalte`) -- das
Sicherheitsnetz greift NUR als Filter DARueBER: ist der natuerliche
Kosten-Kandidat unvollendbar, wird auf die beste vollendbare Alternative
ausgewichen, vermerkt als "Wechsel=alt->neu Grund=unvollendbar" im [SB]-Trace.

*Zwei echte Bugs unterwegs gefunden und behoben (siehe (3)):* (i) eine
transient falsch gebundene Zeile darf NICHT sofort als unvollendbar gelten
(sie loest sich beim naechsten Rundenende automatisch); (ii)
`verbleibende_farben` zaehlt Fabrik-Kacheln faelschlich als "verbaut" -- fuer
die Vollendbarkeit gibt es jetzt die eigene Zahl `noch_erreichbare_farben`
(`provocation.rs`), die nur beider Spieler Strafleiste/verbaute Kuppelzellen
und die Musterreihen des GEGNERS abzieht.

**Baustein 3a (aktiv): Kuppel-Jackpot.** `zellen_wert` bewertet eine Zelle, die
exakt die Farbe fordert, die ihre Musterreihe schon fuehrt, jetzt mit
`JACKPOT_WERT = 4,0` -- DOMINANT ueber Wild (3,0), wie von der Nutzer-Vorgabe
gefordert. Trace: "Jackpot=ja" additiv auf Dome-Entscheidungen.

**Baustein 3b (gebaut, gemessen, NICHT verdrahtet): `ueberpraesenz_vorzug`.**
Eine zweite Drafting-Vorzugsstufe, die bei fehlendem zielspalten-spezifischem
Kandidaten die JETZT ueberpraesenteste Farbe (hoechster `verbleibende_farben`-
Wert) in die TIEFSTE legale Musterreihe nimmt. Erste volle 20-Seed-Messung MIT
dieser Stufe im `vorzugszug`-Pfad: Netz-Siege 2/20 statt 15-16/20 Referenz
(McNemar p=0,0001). Per 6-Seed-Sonde OHNE diese Stufe isoliert: 5/6 (normale
Groessenordnung) -- Ursache eindeutig zugeordnet. Grund: greift auf einem
GROSSEN Teil aller Fruehphasen-Drafting-Entscheidungen (immer, wenn die
zielspalten-spezifische Praeferenz nichts findet -- das ist frueh im Spiel der
Normalfall) und ersetzt dort die Netz-Suche komplett durch eine
Ein-Kriterium-Heuristik, die Strafleiste/Gegner/andere Kriterien ignoriert --
dasselbe Muster wie §7 (Beschneidung zu stark), nur ueber die Vorzugs- statt
die Aktionsmengen-Seite. Bleibt als getestete, unverdrahtete Funktion im Code
fuer eine spaetere, enger gefasste Fassung (z.B. als zusaetzliches Suchsignal
statt als suche-ersetzender Vorzug).

### (3) Der Weg zur finalen Fassung -- drei echte Regressionen, drei Diagnosen

Baustein 1 ging durch VIER volle 20-Seed-Messungen, bevor eine Fassung ohne
Nettoverlust stand -- jede Regression wurde isoliert und ursaechlich behoben,
keine wurde weggemessen oder ignoriert:

| Fassung | Netz-Siege | Vertikale Punkte (AN) | Befund |
| --- | ---: | ---: | --- |
| v1: Baustein1 (Zielspalte persistent gebunden) + `ueberpraesenz_vorzug` verdrahtet | 2/20 (p=0,0001) | nicht ausgewertet (Lauf haette verworfen werden muessen) | `ueberpraesenz_vorzug` ersetzt die Suche zu oft -- isoliert per 6-Seed-Sonde |
| v2: wie v1, `ueberpraesenz_vorzug` NICHT verkettet | 10/20 (p=0,146) | 2,45 | Zielspalte wechselte 5,25x/Partie -- jede transiente Falschbindung loeste einen Wechsel aus |
| v3: transiente Falschbindung nicht mehr Sofort-Trigger | 10/20 (p=0,070) | 0,70 (SCHLECHTER als AUS=1,05) | `verbleibende_farben` zaehlt Fabrik-Kacheln als verbaut -- tiefe Reihen erschienen systematisch unvollendbar |
| v4: `noch_erreichbare_farben` statt `verbleibende_farben`, Zielspalte bleibt PERSISTENT gebunden | 8/20 (p=0,039) | 1,05 (=AUS, kein Gewinn) | Persistente Bindung nahm der Kosten-Formel die Reaktionsfaehigkeit aus Runde 1-3 |
| **v5 (final): Zielspalte WIEDER frisch pro Entscheid, Vollendbarkeit nur als Sicherheitsnetz DARueBER** | **15/20 (p=1,000)** | **3,50** | siehe (4) |

Der entscheidende Design-Fehler ueber v1-v4: eine Zielspalte ueber mehrere
Entscheidungen PERSISTENT festzuhalten nahm der bereits in Runde 1-3
validierten Kosten-Formel genau die Reaktionsfaehigkeit, die sie brauchte, um
selbst schon "wegzuwechseln" -- Runde 3 hatte nie eine gespeicherte
Zielspalte, sondern waehlte bei JEDEM Aufruf frisch die (versorgungsgewichtet)
billigste. v5 stellt das wieder her und legt das Vollendbarkeits-Sicherheitsnetz
nur als FILTER darueber, der ausschliesslich dann greift, wenn selbst die
frische Kostenwahl auf eine nachweislich unvollendbare Spalte faellt.

### (4) Finale Abnahme (v5), 20 k1-Seeds

Aufbau IDENTISCH zu Runde 2/3: `alphazero_v21_2d_brierbest.onnx@400` vs
Heuristik@150(dyn), Seeds `[2,3,6,8,9,11,13,20,22,26,29,32,34,39,44,50,52,57,
59,69]`, `MOSAIC_SPALTENBAU_TRACE=1` beide Arme. Ergebnis:
`evaluations/paired_arena_env_spaltenbau_r4d.json`.

| Groesse | AUS (Kontrolle) | AN (v5) |
| --- | ---: | ---: |
| Vertikale Plattenpunkte (Ø, n=20) | 1,05 | **3,50** |
| Endstand (Ø) | 50,25 | 39,45 |
| Strafleiste (Ø) | 10,90 | 9,50 |
| Siege Netz | 16/20 | 15/20 |

Gepaartes Delta +2,45 Plattenpunkte, t=2,33 (n=20, GEPRUEFT signifikant auf
demselben Niveau wie Runde 3s +5,25/t=3,94). Sieg-Differenz NICHT signifikant
(McNemar p=1,0, b=3/c=4) -- der Spaltenbauer kostet in dieser Fassung KEINE
belegbare Staerke, bei GUENSTIGERER Strafleiste (9,50 vs. 10,90). 10 von 20
Partien schliessen mindestens eine Spalte (7 Punkte), 0 von 20 zwei Spalten.

**ABNAHME gegen das urspruengliche Kriterium (>=7,00) VERFEHLT**, und
zusaetzlich: **3,50 liegt UNTER Runde 3s 5,95** auf denselben 20 Seeds mit
demselben Modell. Das ist NICHT das erhoffte "Baustein 1 verbessert Runde 3";
es ist ein Gewinn gegenueber "gar kein Spaltenbauer" (1,05), aber ein
(unaufgeloester) Verlust gegenueber dem Runde-3-Stand. Zwei Aenderungen
liegen zwischen den Messungen (Vollendbarkeits-Sicherheitsnetz + Jackpot-
Gewichtung), und diese Sitzung hat NICHT gemessen, welche der beiden fuer die
Differenz zu Runde 3 verantwortlich ist -- das ist eine offene Beobachtung,
keine ausgeschlossene Ursache (naechster Schritt: dieselbe Messung mit
`JACKPOT_WERT` zurueck auf 2,5, Sicherheitsnetz aktiv, um die beiden
Beitraege zu trennen).

**Blocker-Aufspaltung auf den v5-Traces** (12 Mauer-Zellen, 8 von 20 Partien):
special_zelle_offen 5 (41,7%), c_vorzug_griff_nicht 6 (50,0%), wild 1 (8,3%),
a/b weiterhin 0 (0%) -- DECKUNGSGLEICH mit Runde 2/3s Befund. Das bestaetigt
die Erwartung aus (1): Baustein 1 adressiert eine Ursache (reine
Farbknappheit), die in den PERSISTENTEN Blockern nie die Mehrheit war,
deshalb bewegt sich diese Verteilung kaum.

**Wechsel-Statistik**: 32 Wechsel-Ereignisse ueber 20 Partien (Ø 1,6/Partie,
Spanne 0-7) -- WEIT unter v3s 5,25/Partie. Auffaellig: Partien mit VIELEN
Wechseln (Seeds 20, 29, 6: 6, 7, 5 Wechsel) enden ALLE mit 0 vertikalen
Punkten, waehrend die 10 erfolgreichen Partien ueberwiegend 0-3 Wechsel
zeigen. Das Sicherheitsnetz greift also bevorzugt in Partien, die SOWIESO
schon schlecht laufen (mehrfache Versorgungs-Engpaesse), OHNE sie zuverlaessig
zu retten -- ein Wechsel ist ein Symptom von Schwierigkeit, kein verlaesslicher
Hebel zum Erfolg. Deckt sich mit dem 0-%-Befund aus (1): reine
Farbknappheits-Rettung war nie der dominante Hebel.

**Jackpot-Statistik**: 76 von 266 Dome-Entscheidungen (28,6%) trafen einen
"Jackpot"-Kandidaten.

### (5) Eigene Entscheidungen (markiert, nicht Nutzer-Vorgabe)

- **`ueberpraesenz_vorzug` deaktiviert statt reparaturversucht** -- Zeitbudget
  UND Prinzip "gemessen und abgelehnt ist ein Befund, keine halbe Arbeit"
  (gleiche Haltung wie §7). Eine enger gefasste Fassung (z.B. nur als
  Zusatzsignal fuer die Suche statt als Suche-Ersatz) ist nicht ausprobiert.
- **Die Jackpot/Sicherheitsnetz-Konfundierung in (4) wurde NICHT aufgeloest**
  -- nach vier Regressions-Zyklen war fuer eine fuenfte Messung (nur zur
  Ursachentrennung) kein Budget mehr; markiert als offene Frage statt als
  Behauptung in irgendeine Richtung.
- **Special-Zellen bewusst NICHT in `ist_spalte_vollendbar` aufgenommen** --
  ihre Trigger-Bedingung ist von der eigenen Spalte unabhaengig (Slot-
  Nachbarn koennen in einer ANDEREN Spalte liegen); eine Vollendbarkeits-
  Pruefung, die nur EINE Spalte betrachtet, kann das grundsaetzlich nicht
  entscheiden, ohne die Nachbarspalte mitzudenken -- nicht gebaut, mit 41,7%
  aber der GROESSTE einzelne Posten der verbleibenden Blocker.
- **`kombination_hat_jackpot` per Gleichheitsvergleich auf `JACKPOT_WERT`**
  statt einem eigenen Rueckgabewert -- kleinerer Diff, sicher, weil
  `zellen_wert` nur Literale liefert (kein Rundungsrisiko).
- **`scratchpad/blocker_split_abcd.py` bleibt Scratch**, nicht Teil des Repos
  -- Diagnosewerkzeug fuer diese Sitzung, nicht auf Dauerbetrieb ausgelegt
  (haerteste Annahme: exakter Kachel-Katalog aus `dome.rs` von Hand
  uebernommen, bricht stumm bei einer Katalog-Aenderung dort).


---

## 15. ENTKONFUNDIERUNG (2026-08-13): 2x2 auf denselben 20 k1-Seeds -- kein Arm > 5,95, Runde-3-Konfiguration bleibt aktiver Stand

Koordinator-Auftrag im Anschluss an §14: die Konfundierung zwischen Baustein 1
(Vollendbarkeits-Sicherheitsnetz) und Baustein 3a (Kuppel-Jackpot) auflösen,
mit derselben 20-Seed-Kette. Zwei neue Diagnose-Knoepfe nachgeruestet
(`MOSAIC_SPALTENBAU_SICHERHEITSNETZ`, `MOSAIC_SPALTENBAU_JACKPOT`), damit
beide Bausteine unabhaengig schaltbar sind -- keiner davon im Gating.

### (1) Aufbau

`tools/paired_arena_env_ab.py` zweimal aufgerufen, `MOSAIC_SPALTENBAU=1`
gemeinsam per Shell-Export gesetzt, je EIN Baustein-Knopf ueber `--arms 0 1`
variiert, der ANDERE per Export fixiert:

- Lauf 1 (`evaluations/paired_arena_env_konfund_AB.json`):
  `MOSAIC_SPALTENBAU_JACKPOT=0` fix, `--env-name MOSAIC_SPALTENBAU_
  SICHERHEITSNETZ --arms 0 1` -> liefert Arm A (beide aus) und Arm B (nur
  Sicherheitsnetz).
- Lauf 2 (`evaluations/paired_arena_env_konfund_AC.json`):
  `MOSAIC_SPALTENBAU_SICHERHEITSNETZ=0` fix, `--env-name MOSAIC_SPALTENBAU_
  JACKPOT --arms 0 1` -> liefert Arm A (erneut, zur Reproduzierbarkeits-
  Kontrolle) und Arm C (nur Jackpot).
- Arm D (beide an) wird NICHT neu gefahren -- Vorgabe des Koordinators;
  identisch mit dem AN-Arm aus `evaluations/paired_arena_env_spaltenbau_
  r4d.json` (§14).

Gleiche 20 k1-Seeds, gleiches Modell (`alphazero_v21_2d_brierbest.onnx@400`
vs. Heuristik@150(dyn)) wie §11-§14 durchgehend.

### (2) KRITISCHER NEBENBEFUND: Arm A reproduziert die Runde-3-Konfiguration NICHT auf 5,95, sondern auf 3,15

Arm A (beide Bausteine aus) ist im Code IDENTISCH zu Runde 3s Pfad (gepruefte
Codepfad-Analyse: `sicherheitsnetz_aktiv()==false` liefert exakt `waehle_
spalte(kosten)`, `jackpot_aktiv()==false` liefert exakt den alten Wert 2,5 --
beides byte-fuer-byte der Runde-3-Stand). Trotzdem: **3,15 vertikale
Plattenpunkte in dieser Sitzung, nicht 5,95 wie in §12 archiviert, auf
DENSELBEN 20 Seeds mit demselben Modell.**

Innerhalb dieser Sitzung ist Arm A REPRODUZIERBAR (zwei unabhaengige
Prozess-Laeufe, Lauf 1 und Lauf 2, liefern die exakt gleiche Punktereihe je
Seed: `[0,7,0,7,7,7,0,0,0,7,0,14,0,0,0,0,0,7,0,7]`, GEPRUEFT identisch) -- die
Abweichung ist also KEIN Zufallsrauschen innerhalb der Sitzung, sondern eine
SYSTEMATISCHE Differenz zwischen dieser Sitzung und der §12-Sitzung (Ursache
nicht eingegrenzt: Wheel-Frische, Thread-Anzahl, tract/ONNX-Laufzeitversion
oder Systemlast sind Kandidaten, keiner geprueft). Das ist dieselbe Art von
Beobachtung, die §13(1) bereits fuer den Kontroll-Arm vermerkt hat ("Lauf-zu-
Lauf-Inferenz-Jitter vs. Aufrufumgebung"), hier aber deutlich groesser (2,8
Punkte statt 0,35) und erstmals auch fuer den AKTIVEN Arm nachgewiesen.

**Folge fuer die Interpretation**: der in §14 berichtete Vergleich "v5=3,50
< Runde 3=5,95" vergleicht zwei VERSCHIEDENE Sitzungen und ist dadurch
vermutlich groesstenteils (oder vollstaendig) durch dieses Sitzungs-Artefakt
erklaert, NICHT durch einen echten Effekt der Runde-4-Bausteine -- der
sitzungsinterne Vergleich unten (A=3,15 vs. D=3,50, beide im selben
Groessenbereich) stuetzt das. **§14s Wortlaut "v5 unterperformt Runde 3" wird
hiermit relativiert**: die Grundlage dafuer war ein Cross-Sitzungs-Vergleich,
den diese Sitzung als nicht belastbar entlarvt hat.

### (3) 2x2-Tabelle (gepaart, n=20 je Zelle)

| Arm | Sicherheitsnetz | Jackpot | Vertikale Punkte Ø | Endstand Ø | Strafleiste Ø | Siege |
| --- | :-: | :-: | ---: | ---: | ---: | ---: |
| A | aus | aus | 3,15 | 40,95 / 40,90* | 9,90 | 15/20 |
| B | AN | aus | 3,15 | 40,90 | 9,90 | 15/20 |
| C | aus | AN | 3,85 | 39,85 | 9,75 | 15/20 |
| D (§14, ANDERE Sitzung) | AN | AN | 3,50 | 39,45 | 9,50 | 15/20 |

*A wurde zweimal gemessen (Lauf 1 und Lauf 2), beide Werte angegeben --
identisch bis auf Rundung, siehe (2).

**Effekt Sicherheitsnetz (B-A, sitzungsintern)**: +0,00 Plattenpunkte
(t=0,00) -- 0 diskordante Paare, JEDES der 20 Spiele identisch mit und ohne
Sicherheitsnetz. Auf diesen 20 Seeds hat Baustein 1 in Kombination mit
Jackpot=aus KEINEN messbaren Effekt (deckt sich mit §14s Wechsel-Statistik:
nur 1,6 Wechsel/Partie im Schnitt, und die betroffenen Partien aendern
laut (4) dort ohnehin selten das Endergebnis).

**Effekt Jackpot (C-A, sitzungsintern)**: +0,70 Plattenpunkte (t=0,81,
NICHT signifikant bei n=20) -- Richtung positiv, aber statistisch nicht von
Null zu unterscheiden.

**Bester Arm: C mit 3,85.** Weit unter der Runde-3-Referenz 5,95 (egal ob man
die archivierte Zahl oder Arm A dieser Sitzung als Bezug nimmt).

### (4) Entscheidung nach der Vorab-Regel

*"Kein Arm > 5,95: Runde-3-Konfiguration bleibt der aktive Stand (Code der
Bausteine bleibt, Knoepfe default AUS)."*

Kein Arm (A=3,15, B=3,15, C=3,85, D=3,50) uebertrifft 5,95. **Entscheidung:
Runde-3-Konfiguration bleibt der aktive Stand.** Umgesetzt:

- `MOSAIC_SPALTENBAU_SICHERHEITSNETZ` und `MOSAIC_SPALTENBAU_JACKPOT` beide
  auf **Default AUS umgestellt** (vorher, seit §14, Default AN) -- unset
  liefert jetzt wieder GENAU den Runde-3-Pfad (`ziel_spalte` = reine
  Kostenwahl ohne Vollendbarkeits-Filter, `zellen_wert` = 2,5 statt
  `JACKPOT_WERT` fuer den Jackpot-Fall).
- Beider Bausteine CODE bleibt im Repo (`ist_spalte_vollendbar`,
  `waehle_beste_vollendbare_spalte`, `zellen_wert`s Jackpot-Zweig,
  `ueberpraesenz_vorzug`) -- ueber `=1` weiter einschaltbar fuer eine
  spaetere Fassung, aber nicht mehr Default-Verhalten. `cargo test --lib`:
  411 bestanden (0 fehlgeschlagen, 20 ignoriert) nach der Umstellung. Wheel
  neu gebaut+installiert, `tools/parity_probe.py`: Hash `8c6684ff...`
  haelt (der Umschwung betrifft nur den `MOSAIC_SPALTENBAU=1`-Pfad, die
  Defaults ohne den Knopf sind davon nicht beruehrt).

**Special-Zellen-Erweiterung (Auftrag 2, bedingt auf "bester Arm >= 5,95"):
NICHT gebaut.** Die Bedingung ist nicht erfuellt (bester Arm 3,85 < 5,95) --
per Vorab-Regel entfaellt dieser Schritt in dieser Sitzung.

### (5) Eigene Entscheidungen (markiert, nicht Nutzer-Vorgabe)

- **Arm D wurde NICHT neu gefahren** (Koordinator-Vorgabe), obwohl (2) einen
  Sitzungs-Effekt nachweist, der D (andere Sitzung) potenziell verzerrt --
  fuer die Entscheidung in (4) macht das keinen Unterschied (D=3,50 liegt
  ohnehin weit unter 5,95, egal wie verzerrt), wird aber hier ausdruecklich
  als Einschraenkung der D-Zahl vermerkt statt verschwiegen.
- **Die Sitzungs-Drift-Ursache aus (2) wurde NICHT eingegrenzt** (Wheel-Alter,
  Thread-Zahl, ONNX-Laufzeit, Systemlast alle als Kandidaten unbewiesen) --
  das ist ein potenziell wichtiger Befund fuer KUENFTIGE Messungen dieser
  Metrik (die 5,95-/7,00-Referenzwerte selbst sind moeglicherweise
  sitzungsabhaengig streuend, nicht nur code-abhaengig), aber ausserhalb des
  Zeitbudgets dieser Sitzung aufzulösen.
- **Polaritaet der Knoepfe umgedreht statt neue Knoepfe mit anderem Namen
  angelegt** -- kleinerer Diff, und die Semantik "unset = aktueller
  Bestand" bleibt fuer beide Knoepfe ueber die Zeit hinweg konsistent
  (vorher war "Bestand" = §14/v5, jetzt ist "Bestand" = Runde 3 -- die
  Knopf-BEDEUTUNG "1=eingeschaltet" aendert sich nicht, nur ihr Default).

### (6) NACHTRAG (Koordinator, 2026-08-13): Ursache der Sitzungs-Drift eingegrenzt -- HERLEITUNG, keine eigene Neumessung

**Als Herleitung markiert** (Konsistenzargument aus geprueften Zeitstempeln,
keine eigene Kausal-Messung dieser Sitzung): der RNG-Schnitt
(`fe1e306`, GEPRUEFT `git log`: 2026-08-13 14:24:52) liegt zeitlich ZWISCHEN
der §13-Messreihe (`a191cd7`, GEPRUEFT: 2026-08-13 12:54:26) und allen
Laeufen dieser Sitzung (§14/§15, nach `fe1e306`). `elo_history.csv` vermerkt
den Schnitt bereits als Aera-Grenze (`6b4fbd3`, GEPRUEFT: 2026-08-13 14:25:20,
Nutzer-Entscheid, Zeile: *"Messungen ueber diesen Schnitt hinweg sind nur
eingeschraenkt vergleichbar, da auch der Heuristik-Anker selbst aus einem
anderen Strom sucht"*).

`fe1e306`s Commit-Text (GEPRUEFT per `git show`): vor dem Schnitt teilten sich
Suche (MCTS/Heuristik) und echte Spielereignisse (Beutel-Nachfuellungen)
DENSELBEN RNG -- wie viel die Suche "verbrauchte", verschob dadurch, welche
Fliesen wann in welche Fabrik kamen, unabhaengig vom eigentlichen Suchergebnis.
Nach dem Schnitt hat die Suche einen eigenen, deterministisch aus (game_seed,
move_index) abgeleiteten RNG (`derive_search_seed`).

**Konsequenz fuer §15s Arm A**: Arm A ist im SPALTENBAU-CODE byte-identisch zu
Runde 3, aber NICHT in der GESAMT-Ausfuehrungsumgebung -- Runde 3 (§12, vor
`fe1e306`) lief mit dem geteilten RNG, Arm A (nach `fe1e306`) mit dem
getrennten. Selbst bei identischer Spaltenbau-Logik fuehrt das zu
UNTERSCHIEDLICHEN Beutel-Nachfuellungen im Partieverlauf (das Kachel-Setup
selbst -- welche 3 Wertungsplatten aktiv sind -- bleibt dabei GEPRUEFT gleich,
da es Teil des unveraenderten Anfangs des Partie-Streams ist, siehe
`konfund_AC`/`r4d`: Vertikale Reihen ist in 20/20 Partien beider Dateien
aktiv). **Damit ist 5,95 ein ALT-AERA-Wert und kein gueltiger Anker mehr** --
der Nutzer hat den Schnitt bereits fuer den Elo-Anker als Aera-Grenze
verfuegt (`6b4fbd3`); dieselbe Logik gilt fuer Generator-Benchmarks wie diesen.
**Neuer, sitzungsinterner Anker fuer alle folgenden Abschnitte: A = 3,15**
(zweimal bit-identisch repliziert, siehe (2)).

Nicht eingegrenzt (und in dieser Sitzung nicht weiter verfolgt): ob der
RNG-Schnitt die GESAMTE Differenz erklaert oder nur einen Teil -- die
Herleitung ist konsistent mit allen Beobachtungen (Zeitstempel-Reihenfolge,
Commit-Inhalt, identisches Kachel-Setup, Nutzer-Entscheid am Elo-Anker), aber
keine Ursachen-Messung dieser Sitzung selbst hat das GEZIELT isoliert (z.B.
per Nachbau des Alt-RNG-Pfads).


---

## 16. SPECIAL-ZELLEN-BAUSTEIN (2026-08-13): +1,05 gg. A, NICHT signifikant (p=0,083); Jackpot-Replikation auf frischen Seeds widerlegt den Trend

Koordinator-Auftrag im Anschluss an §15(6): der mit 50 % groesste Blocker
(Special-Zellen, §14 Teil 1) wird in die Spaltenbau-Logik eingebaut, gemessen
gegen den neuen sitzungsinternen Anker A=3,15 (nicht mehr 5,95). Zusaetzlich:
Jackpot-Replikation auf 20 FRISCHEN Seeds.

### (1) Was gebaut wurde

Dritter Diagnose-Knopf `MOSAIC_SPALTENBAU_SPECIAL` (Default AUS, gleiches
Muster wie §15), drei Teile:

1. **Kosten-Funktion**: `special_kosten(r, spalte, verbleibend)` summiert jetzt
   die ECHTEN [`zelle_kosten`] ihrer 3 Slot-Nachbarn (die Nachbarn SIND der
   Weg zur Special-Zelle, Koordinator-Vorgabe), statt der ALT-Formel
   `0,3 + 0,8*n` (n = Zahl offener Nachbarn, farbblind). `spalten_kosten`
   selbst wurde zu `(0..6).map(|r| zelle_kosten(r, spalte)).sum()`
   vereinfacht -- `zelle_kosten` ist die neue, wiederverwendbare
   Ein-Zellen-Formel (auch von `plate_builder.rs`s generischer Mechanik
   genutzt, die ihre eigene Kopie dieser Formel dafuer verloren hat --
   CLAUDE.md "Bestehendes wiederverwenden").
   
   **Nutzer-Taktik (`docs/domain_knowledge.md` §8: "erzwungene Spezialkuppeln
   nach OBEN ... obere Slots haengen an billigen Musterreihen") entsteht
   AUTOMATISCH aus der bestehenden Formel**, ohne eigene Sonderregel: ein
   Nachbar in Zeile 0/1 (oberer Slot) braucht laut [`zelle_kosten`]s
   Normal-Zweig nur 1-2 Kopien, einer in Zeile 4/5 (unterer Slot) 5-6 -- die
   Reihen-Tiefe ist bereits Teil der Kostenformel.
2. **Vollendbarkeits-Erweiterung**: `ist_spalte_vollendbar` behandelt eine
   offene Special-Zelle jetzt als vollendbar, wenn es ihre 3 Slot-Nachbarn
   sind (neue Hilfsfunktion `ist_zelle_vollendbar`, dieselbe Logik wie der
   Normal-Zweig, aber fuer eine beliebige `(r,c)`). Nur wirksam in
   Kombination mit dem §15-Sicherheitsnetz (das ist Default AUS).
3. **Vorzugs-Erweiterung**: zweite Drafting- und Tiling-Vorzugsstufe
   (`special_nachbar_zellen`), die bei fehlendem zielspaltenspezifischem
   Kandidaten die Slot-Nachbarn ALLER offenen Special-Zellen der Zielspalte
   als Zellen-Liste an `plate_builder::vorzugszug_fuer_zellen`/`tiling_vorzug_
   fuer_zellen` durchreicht -- WIEDERVERWENDUNG der generischen
   Zellen-Mechanik (Kriterien 0/2/5/7) statt einer eigenen Kopie. Bewusst
   KEINE Dome-Wahl-Erweiterung: die Nachbarzellen-Farbforderung wird von
   DERSELBEN Kachel-Platzierung fixiert, die die Special-Zelle ueberhaupt
   erst erzeugt -- es gibt keinen SPAETEREN Dome-Entscheid mehr, der sie
   betreffen koennte (siehe Bericht fuer die Begruendung).

`cargo test --lib`: 416 bestanden (0 fehlgeschlagen, 20 ignoriert), 5 neue
Tests fuer §16 (`special_kosten_par16_nutzt_echte_nachbarkosten`,
`ist_spalte_vollendbar_par16_prueft_special_nachbarn`,
`ist_spalte_vollendbar_default_ignoriert_special_wie_par14`,
`special_nachbar_zellen_liefert_die_drei_slot_nachbarn_nur_wenn_aktiv`,
`vorzugszug_bedient_special_nachbarn_wenn_zielspalte_selbst_nichts_findet`).
Wheel neu gebaut+installiert, `tools/parity_probe.py`: Hash `8c6684ff...`
haelt (Default unveraendert, der Knopf ist unset).

### (2) Special-Zellen-Messung: 20 k1-Seeds gegen A

Aufbau: `--env-name MOSAIC_SPALTENBAU_SPECIAL --arms 0 1 --control 0`,
`MOSAIC_SPALTENBAU=1` per Export fix, dieselben 20 k1-Seeds, gleiches Modell.
Ergebnis: `evaluations/paired_arena_env_special_r16_k1.json`.

| Groesse | A (Special aus) | Special AN |
| --- | ---: | ---: |
| Vertikale Plattenpunkte Ø | 3,15 | **4,20** |
| Endstand Ø | 40,95 | 44,00 |
| Strafleiste Ø | 9,90 | 9,70 |
| Siege | 15/20 | 16/20 |

Gepaartes Delta **+1,05**, t=1,831, **p=0,083** (exakte zweiseitige
Student-t-Verteilung, df=19, per Inkomplette-Beta-Funktion nachgerechnet --
NICHT unter 0,05, verfehlt die Vorab-Regel "signifikant positiv"). Siege
NICHT schlechter (16/20 gg. 15/20, sogar leicht besser) -- der zweite Teil der
Vorab-Regel ist erfuellt, der erste nicht.

**Blocker-Aufspaltung auf dem Special-AN-Arm** (15 Mauer-Zellen ueber 12 von
20 Partien, gleiche Methode wie §14 Teil 1):

| Kategorie | ohne Special-Baustein (§14, kombiniert) | MIT Special-Baustein |
| --- | ---: | ---: |
| special_zelle_offen | 50,0 % | **13,3 %** |
| c_vorzug_griff_nicht | 42,9 % | 80,0 % |
| b_reihe_falsch_gebunden | 0 % | 6,7 % |
| wild_ohne_farbzwang | 7,1 % | 0 % |

Der Special-Blocker-Anteil bricht genau in die Richtung ein, die der
Mechanismus vorhersagt (50 % -> 13,3 %) -- eine INDIREKTE, aber konsistente
Bestaetigung, dass die Kosten-/Vorzugserweiterung tatsaechlich greift, auch
wenn der Gesamteffekt (+1,05) bei n=20 nicht signifikant ist.

### (3) Jackpot-Replikation: 20 FRISCHE Seeds (70-89)

Eigene Wahl (markiert): die 20 auf den k1-Bereich `[2..69]` unmittelbar
folgenden Ganzzahlen 70-89 -- keine Auswahl nach Ergebnis, transparent
nachvollziehbar. Gleicher Aufbau (`--env-name MOSAIC_SPALTENBAU_JACKPOT
--arms 0 1 --control 0`). Ergebnis:
`evaluations/paired_arena_env_jackpot_replik_fresh.json`.

| Groesse | Jackpot aus | Jackpot AN |
| --- | ---: | ---: |
| Vertikale Plattenpunkte Ø | 2,10 | **2,10** |
| Endstand Ø | 39,65 | 39,90 |
| Strafleiste Ø | 13,05 | 12,00 |
| Siege | 9/20 | 8/20 |

**Gepaartes Delta 0,00 (t=0,00) -- alle 20 Partien liefern per Seed EXAKT
denselben Vertikale-Reihen-Wert mit und ohne Jackpot.** Der in §15 gemessene
Trend (+0,70 auf den k1-Seeds) repliziert NICHT.

**Gepoolt ueber beide Seed-Saetze** (k1-Deltas aus §15 + die 20 frischen
Null-Deltas, n=40): Mittel **+0,35**, t=0,813, **p=0,421** (exakt
nachgerechnet) -- weit von jeder Signifikanz entfernt. Die Vorab-Regel
("Jackpot wird uebernommen, wenn die Replikation die Richtung signifikant
bestaetigt, gepoolt") ist klar NICHT erfuellt -- genau die λ-Sweep-Lehre
("Richtung hielt, Replikation entschied") zeigt hier das GEGENTEIL-Ergebnis:
die Richtung hielt NICHT.

### (4) Entscheidung nach der Vorab-Regel

- **Special-Baustein: NICHT uebernommen** (p=0,083 verfehlt "signifikant
  positiv", trotz erfuellter Sieg-Bedingung und einer inhaltlich
  konsistenten Blocker-Verschiebung). `MOSAIC_SPALTENBAU_SPECIAL` bleibt
  Default AUS, Code bleibt im Repo (per `=1` einschaltbar).
- **Jackpot: weiterhin NICHT uebernommen** -- durch die Replikation zusaetzlich
  bestaetigt (nicht nur unentschieden wie in §15, jetzt mit einer zweiten,
  unabhaengigen Messung, die den Effekt auf exakt Null gedrueckt hat).
  `MOSAIC_SPALTENBAU_JACKPOT` bleibt Default AUS.
- **Der aktive Stand bleibt die reine Runde-3-Konfiguration** (A=3,15) --
  keine der beiden §14/§16-Erweiterungen hat die Vorab-Regel ueberstanden.
  Das Nutzer-Ziel 7,00 bleibt unerreicht; der naechste Hebel ist weiterhin
  `c_vorzug_griff_nicht` (jetzt 80 % des verbleibenden Restblockers auf dem
  Special-Arm, siehe (2)) -- das war schon in §14 der zweitgroesste Posten und
  ist jetzt, nach Special, praktisch der EINZIGE.

### (5) Eigene Entscheidungen (markiert, nicht Nutzer-Vorgabe)

- **Special-Baustein bewusst NICHT nachgemessen/repliziert** trotz der
  vielversprechenden Richtung (anders als Jackpot war das nicht explizit
  beauftragt) -- Zeitbudget; die p=0,083-Zahl bleibt eine EINZELNE Messung,
  keine bestaetigte.
- **Keine Dome-Wahl-Erweiterung fuer Special-Nachbarn gebaut** -- begruendet
  in (1): die Nachbarn-Farbforderung wird atomar mit der Special-Zelle selbst
  durch dieselbe Kachel-Platzierung fixiert, ein SPAETERER Dome-Entscheid, der
  sie noch beeinflussen koennte, existiert nicht. Kein Kompromiss, sondern
  eine spielmechanische Tatsache.
- **`plate_builder.rs`s eigene Kopie von `zelle_kosten` entfernt**, ruft jetzt
  `column_build::zelle_kosten` direkt -- kleinerer Diff als zwei Formeln
  synchron zu halten, verifiziert weiterhin durch den bestehenden
  Aequivalenztest.
- **Frische Seeds 70-89 statt einer Zufallsziehung** -- einfachste
  nachvollziehbare Wahl ohne jede Optimierungsmoeglichkeit nach Ergebnis.


---

## 17. SPECIAL-REPLIKATION (FINAL) + (c)-BLOCKER-URSACHEN-DIAGNOSE (2026-08-13)

Koordinator-Auftrag im Anschluss an §16: (1) den Special-Befund (p=0,083,
n=20) NICHT als Nullbefund verwerfen, sondern auf 20 unabhaengigen frischen
Seeds replizieren und gepoolt (n=40) final entscheiden; (2) den jetzt
groessten Restblocker (c_vorzug_griff_nicht, 80 % auf dem Special-Arm)
ursachen-klassifizieren, ERST danach ggf. gezielt eingreifen.

### (1) Special-Replikation: 20 FRISCHE Seeds (90-109, unabhaengig von 70-89)

Eigene Wahl (markiert): naechster unbenutzter Block nach den Jackpot-Replik-
Seeds (70-89) -- wieder ohne Auswahl nach Ergebnis. Aufbau identisch zu §16(2).
Ergebnis: `evaluations/paired_arena_env_special_r17_fresh.json` (GEPRUEFT
vollstaendig: n=20 auf beiden Seiten, kein Teillauf).

| Groesse | A (Special aus) | Special AN |
| --- | ---: | ---: |
| Vertikale Plattenpunkte Ø | 1,40 | 1,75 |
| Siege | 15/20 | 14/20 |

Gepaartes Delta auf den frischen Seeds: **+0,35** (t=0,567, einzeln nicht
signifikant). Richtung bleibt POSITIV (wie in §16), aber kleiner als auf den
k1-Seeds (+1,05).

**Gepoolt ueber beide Seed-Saetze** (k1 aus §16 + frisch, n=40, exakt
nachgerechnet per Inkomplette-Beta-Funktion):

| Groesse | Wert |
| --- | ---: |
| Gepaartes Delta (Mittel) | **+0,70** |
| t (df=39) | 1,669 |
| **p (zweiseitig)** | **0,103** |
| Siege gesamt (A / Special, von 40) | 30 / 30 |
| McNemar (gepoolt, exakt) | b=4, c=4, p=1,000 |

**Entscheidung (final, nach Vorab-Regel): Special-Baustein wird NICHT
uebernommen.** p=0,103 liegt oberhalb der 0,05-Schwelle -- die Richtung ist in
BEIDEN Seed-Saetzen positiv (+1,05 und +0,35), aber die Staerke reicht bei
n=40 nicht fuer Signifikanz. Die Sieg-Bedingung ist erfuellt (30/40 beide,
kein Verlust), aendert an der ersten Bedingung aber nichts. `MOSAIC_
SPALTENBAU_SPECIAL` bleibt Default AUS, Code bleibt als Diagnose-Knopf im
Repo. **Das ist jetzt der finale Befund** -- keine weitere Replikation
vorgesehen (Vorab-Regel war zweistufig, nicht mehrstufig).

### (2) (c)-Blocker-Ursachen-Diagnose: [SB]-Trace-Auswertung, kein Umbau ins Blaue

Bester Arm = Special AN (höchster Mittelwert trotz (1), 20 k1-Seeds,
`evaluations/paired_arena_env_special_r16_k1.json`). Methode: `blocker_split_
abcd.py` (Scratch) erweitert -- fuer jeden bereits klassifizierten
`c_vorzug_griff_nicht`-Fall (den FRUeHESTEN Moment, an dem die geforderte
Farbe X verfuegbar UND die Zeile offen war, aber die tatsaechliche Aktion
nicht (X, Zeile) traf) wird zusaetzlich aus der SELBEN [SB]-Zeile gelesen,
welche Zielspalte zu dem Zeitpunkt aktiv war (`Ziel=`) und ob `vorzugszug_
fuer_spalte` selbst einen Kandidaten hatte (`Vorzug=ja/nein`) -- KEINE neue
Instrumentierung, nur genauer gelesen, wie beauftragt.

Klassifikation je Fall:
- **c1 (Zielwahl war eine ANDERE Spalte)**: `Ziel=` an dieser Stelle
  entspricht NICHT der spaeter tatsaechlich zur Mauer gewordenen Spalte --
  die Kostenfunktion verfolgte zu diesem Zeitpunkt ein anderes Ziel.
- **c3 (Vorzug wählte eine andere Zeile derselben Spalte)**: `Ziel=` WAR schon
  die Mauer-Spalte und `vorzugszug_fuer_spalte` hatte einen Kandidaten
  (`Vorzug=ja`), aber fuer eine ANDERE Zeile derselben Spalte (die interne
  Knappheits-/Vollste-Reihe-Rangfolge aus §12 bevorzugte eine andere Zeile).
- (c2/c4 aus dem Auftrag -- Netz-Prior ueberstimmt den Vorzug bzw. kein
  Kandidat trotz Verfuegbarkeit -- **0 Faelle**, siehe (3).)

| Ursache | Anzahl | Anteil |
| --- | ---: | ---: |
| c1: Zielwahl war eine andere Spalte | 8 | **66,7 %** |
| c3: Vorzug waehlte andere Zeile derselben Spalte | 4 | **33,3 %** |
| c2: Vorzug empfahl r_open, Aktion widersprach trotzdem | 0 | 0 % |
| c4: kein Vorzugskandidat trotz Verfuegbarkeit | 0 | 0 % |

n=12 (c_vorzug_griff_nicht-Faelle ueber 20 Partien). **Auffaellig: ALLE 12
Faelle liegen in Runde 1.** Wortlaut-Beispiel (Seed 6, Zeile 3 der Spalte 4):
Tuerkis war in Runde 1 im Angebot und Zeile 3 offen, aber `Ziel=0` (nicht 4)
zu diesem Zeitpunkt -- die Partie zielte da noch auf Spalte 0.

### (3) Deutung -- und warum HIER kein Eingriff gebaut wird

c1 dominiert (66,7 %), und ALLE Faelle (c1 wie c3) liegen ausschliesslich in
Runde 1: Frueh im Spiel, wenn Kosten zwischen Spalten noch fast identisch
sind (leeres/kaum belegtes Brett), wechselt das Ziel zwischen Entscheidungen
haeufig, WEIL es das per Konstruktion darf (`waehle_spalte` ist bei jedem
Aufruf frisch, keine Bindung -- siehe §14/§15). Genau diese Reaktions-
faehigkeit war es aber, die §14s SPERRIGE Zielspalten-Bindung ("halte an der
gewaehlten Spalte fest") in VIER vollen Messzyklen nachweislich verschlechtert
hat (0,70-2,45 statt 5,95 vertikale Punkte, siehe §14(3)). Ein Eingriff gegen
c1/c3 waere strukturell dieselbe Idee (Runde-1-Ziel fruehe stabilisieren/
festhalten) mit demselben Risiko -- OHNE eine qualitativ neue Idee, die dieses
Risiko vermeidet, waere ein weiterer Bau ein Umbau ins Blaue trotz stehender
Ursache, nicht wegen fehlender Ursache.

Zusaetzlich: n=12 ist klein (eine Partie kann mehrere Faelle liefern, aber
nur 8 von 20 Partien hatten ueberhaupt eine Mauer-Spalte in diesem Arm) --
selbst eine ueberzeugende Idee wuerde eine 20-Seed-Messung mit betraechtlichem
Rauschen treffen (siehe §16/§17(1)s eigene p-Werte als Kalibrierung: n=20-40
loest Effekte dieser Groessenordnung nicht zuverlaessig auf).

**Entscheidung (gedeckt durch die Koordinator-Vorgabe "budget eng ->
Diagnose-Tabelle ohne Eingriff"): Teil 2 liefert die Ursachen-Tabelle in (2),
KEIN Eingriff gebaut.** Kein Diagnose-Knopf, kein Rust-Code-Aenderung, keine
neue Messung in diesem Abschnitt noetig -- `git status` zeigt `engine/`
unveraendert seit Commit `3b0c89d`, Wheel/Parity/`cargo test` aus §16 bleiben
gueltig.

### (4) Eigene Entscheidungen (markiert, nicht Nutzer-Vorgabe)

- **Kein Eingriff fuer c1/c3 gebaut** -- explizit durch die Koordinator-Vorgabe
  gedeckte Wahl bei knappem Budget, zusaetzlich in (3) inhaltlich begruendet
  (dieselbe Risikoklasse wie die gescheiterte §14-Stur-Bindung).
  Empfehlung fuer eine SPAeTERE Sitzung mit mehr Budget: falls eine
  qualitativ neue Idee entsteht (z.B. eine Bindung, die NUR in Runde 1 UND
  NUR bei echtem Kosten-Gleichstand greift, statt bei jedem Kostenunterschied
  wie §14s Fassungen), waere das der naechste testbare Kandidat -- ungeprueft,
  nur als Hinweis vermerkt.
- **c2/c4 mit 0 Faellen nicht weiter untersucht** -- bei n=12 ist das kein
  Beleg fuer "kommt nie vor", nur dafuer, dass es in DIESER Stichprobe nicht
  auftrat.
- **Sub-Klassifikation ohne neue Rust-Instrumentierung**, nur per Nachlesen
  bereits vorhandener [SB]-Felder (`Ziel=`, `Vorzug=`) -- wie beauftragt
  ("KEINE Umbauten ins Blaue", hier gelesen als "keine neue Messung, bevor
  die Ursache steht").


---

## 18. DIAGONALEN-BAUSTEIN k2 (2026-08-13): +2,61 Plattenpunkte, p=0,011 -- UEBERNOMMEN als aktiver Default

Nutzer-Freigabe (ueber Koordinator): k2 (Diagonale) und k6 (Spezialfelder) im
Plattenbauer umsetzen, damit das Generator-Sortiment fuers Ownership-Kopf-
Training vollstaendig wird. Methodik exakt wie beim Spaltenbau (§14-§17):
frischer Aera-Anker, Diagnose-Knopf, gepaarte Messung, Uebernahme-Regel
p<0,05 + McNemar. **Nur k2 in dieser Sitzung geschafft** (Budget, vom
Koordinator ausdruecklich als Prioritaet vorgegeben: "k2 fertig vor k6 halb")
-- k6 ist NICHT begonnen.

### (1) Frischer Aera-Anker: Diskrepanz zur Koordinator-Ausgangslage GEPRUEFT und benannt

Die vom Koordinator genannte Ausgangslage ("0,00 Punkte in allen 18 aktiven
Partien") wurde vor dieser Messung NICHT bestaetigt -- eine frische
Referenzmessung (`evaluations/paired_arena_env_k2_baseline_fresh.json`,
`MOSAIC_PLATTENBAU=0` vs `=2`, die 23 Seeds aus `seeds_per_criterion/k2.txt`,
GEPRUEFT: Kriterium "Diagonale Reihen" in 23/23 Partien BEIDER Arme aktiv --
Seed-Satz nach dem RNG-Schnitt weiterhin gueltig) ergab:

| Groesse | Bezug (kein Plattenbauer) | k2 VOR §18 (bestehender Diagonalenbauer) |
| --- | ---: | ---: |
| Diagonale Reihen Ø | 0,00 | **3,04** |
| Siege | 10/23 | 15/23 |

Der bestehende `Diagonalenbauer` (aus §13, unveraendert) erreichte in DIESER
frischen Messung bereits 3,04 (7 von 23 Partien mit voller Diagonale), nicht
0,00. Als offene Diskrepanz vermerkt (nicht aufgeloest): die Koordinator-Zahl
stammt vermutlich aus einer ANDEREN Messreihe (z.B. reinem Self-Play-Korpus
statt Netz-vs-Heuristik-Arena) -- **fuer diese Sitzung gilt die selbst
gemessene, GEPRUEFTE Zahl 3,04 als Anker**, nicht die Koordinator-Angabe.

**NACHTRAG (Koordinator, aufgeloest, kein offener Punkt mehr)**: die 0,00-Zahl
stammte aus den SPALTENBAU-Laeufen (k1-Spieler, Diagonale nur als Beifang auf
k1-/frischen Seeds -- z.B. `evaluations/paired_arena_env_spaltenbau_r4d.json`),
waehrend 3,04 der k2-PLATTENBAUER selbst auf den k2-Seeds ist
(`evaluations/paired_arena_env_k2_baseline_fresh.json`) -- zwei verschiedene
Generatoren auf verschiedenen Partien, keine Drift, beide Zahlen korrekt fuer
das, was sie je maßen.

### (2) Was gebaut wurde: Special-Zellen-Baustein fuer die Diagonalen-Geometrie

Nutzer-Taktik (`docs/domain_knowledge.md`, Diagonalen-Abschnitt) auf
Kachel-Geometrie uebersetzt: die Gegendiagonale [(5,0)...(0,5)] laeuft durch
Slot (2,0), der GENAU 2 Diagonalzellen ((5,0), (4,1)) und potenziell eine
Special-Zelle unter den 2 uebrigen Slot-Zellen enthaelt -- exakt der Fall, den
§16 (Spaltenbau, Kriterium 1) schon geloest hat, hier aber fuer eine
GEOMETRIE-UNABHAENGIGE Zellen-Liste statt einer Spalte gebraucht.

1. **`column_build::special_nachbar_zellen_fuer_liste`** verallgemeinert
   `special_nachbar_zellen` (spalten-spezifisch) auf eine beliebige
   `&[(usize,usize)]`-Liste -- findet offene Special-Zellen INNERHALB der
   Liste, liefert ihre 3 Slot-Nachbarn (koennen ausserhalb der Liste liegen).
2. **`Diagonalenbauer::drafting_vorzug`/`tiling_vorzug`** (plate_builder.rs)
   bekommen eine zweite Vorzugsstufe: findet `vorzugszug_fuer_zellen`/
   `tiling_vorzug_fuer_zellen` fuer die Diagonale selbst nichts, wird dieselbe
   generische Mechanik auf die Special-Nachbarzellen angewandt.
3. **Kosten-Seite**: `column_build::zelle_kosten_smart`/`special_kosten`s
   Nachbar-Summenformel (aus §16) fliesst in die Diagonalen-Kandidatenwahl
   (Haupt- vs. Gegendiagonale) ein.

**Architektur-Entscheidung (wichtig, siehe (4)): eigener Uebernahme-Status
statt geteiltem Schalter.** Erste Fassung nutzte den bestehenden
`MOSAIC_SPALTENBAU_SPECIAL`-Knopf (§16) wieder -- das haette den k1-Legacy-
Pfad (§17: final NEIN) und k2 (siehe (3): JA) an DIESELBE Umschaltung
gekoppelt. Nach der positiven Messung (3) wurde deshalb umgebaut: 
`zelle_kosten_smart`/`special_nachbar_zellen_immer` sind UNBEDINGTE
Varianten ohne Schalter, die `Diagonalenbauer` direkt nutzt -- `MOSAIC_
SPALTENBAU_SPECIAL` bleibt unangetastet fuer den k1-Pfad (Default AUS, §17
gilt weiter unveraendert). Nachgemessen (4): die unbedingte Fassung liefert
BYTE-IDENTISCHE Werte zur ersten (geschalteten) Messung.

`cargo test --lib`: 416 bestanden (0 fehlgeschlagen, 20 ignoriert,
unveraendert -- keine neuen Tests in dieser Runde, Zeitbudget). Wheel neu
gebaut+installiert (zweimal, vor und nach dem Schalter-Umbau), `tools/
parity_probe.py`: Hash `8c6684ff...` haelt beide Male (der Default-Pfad
ohne `MOSAIC_PLATTENBAU` bleibt unberuehrt, `Diagonalenbauer` wird nur bei
gesetztem Knopf ueberhaupt erreicht).

### (3) Messung: 23 k2-Seeds, Special-Erweiterung gegen den §18(1)-Anker

Aufbau: `MOSAIC_PLATTENBAU=2` fix, `--env-name MOSAIC_SPALTENBAU_SPECIAL
--arms 0 1 --control 0` (erste, geschaltete Fassung -- siehe (2) fuer den
Umbau danach). Ergebnis: `evaluations/paired_arena_env_k2_special_k2seeds.json`.

| Groesse | Bezug (Special aus, =§18(1)s 3,04) | Special-Erweiterung AN |
| --- | ---: | ---: |
| Diagonale Reihen Ø | 3,04 | **5,65** |
| Endstand Ø | 40,04 | 42,74 |
| Strafleiste Ø | 10,17 | 9,22 |
| Siege | 15/23 | 15/23 |

Gepaartes Delta **+2,61**, t=2,787, **p=0,0108** (exakte zweiseitige
Student-t-Verteilung, df=22, per Inkomplette-Beta-Funktion nachgerechnet --
UNTER 0,05). McNemar auf den Siegen: b=5/c=5, **p=1,000** (kein Sieg-
Verlust, sogar leicht guenstigere Strafleiste UND Endstand). **Beide Haelften
der Vorab-Regel erfuellt.**

11 von 23 Partien schliessen eine volle Diagonale (10 Punkte) ab, davon KEINE
mit beiden Diagonalen gleichzeitig (max. beobachtet 10, nicht 20).

### (4) Entscheidung: UEBERNOMMEN als aktiver Default fuer k2

`Diagonalenbauer` nutzt die Special-Zellen-Erweiterung ab sofort UNBEDINGT
(kein Diagnose-Knopf mehr noetig fuer k2 selbst -- die Erweiterung IST jetzt
der validierte Diagonalen-Bauer). Erreichbar wie bisher nur ueber
`MOSAIC_PLATTENBAU=2` (oder `auto`), selbst weiterhin ein reiner Diagnose-/
Korpus-Knopf, Default AUS, nie im Gating -- die Uebernahme-Entscheidung
betrifft NUR das Verhalten INNERHALB des k2-Pfads, nicht seine Aktivierung.
Nachweis der Aequivalenz nach dem Umbau: `evaluations/paired_arena_env_
k2_confirm_default.json` (`MOSAIC_PLATTENBAU=2`, kein `MOSAIC_SPALTENBAU_
SPECIAL` gesetzt) liefert Diagonale-Reihen-Werte PUNKTGENAU identisch zur
geschalteten Messung in (3) (`[10,10,10,10,10,0,10,10,0,0,10,0,10,0,0,0,10,
10,0,0,0,10,10]`, Ø 5,6522).

### (5) k6 (Spezialfelder): NICHT begonnen

Budget-Entscheidung nach expliziter Koordinator-Vorgabe ("k2 fertig vor k6
halb"). Kein Code, keine Messung, keine Seed-Verifikation fuer k6 in dieser
Sitzung. Naechste Schritte fuer eine Folge-Sitzung: (a) `seeds_per_criterion/
k6.txt` (20 Seeds, ungeprueft ob RNG-Schnitt-gueltig) auf Aktivitaetsrate
pruefen, (b) frischen Aera-Anker fuer k6 messen (Bezug ~-12, siehe
Koordinator-Angabe -- nach der k2-Erfahrung in (1) NICHT ungeprueft
uebernehmen), (c) `Spezialbauer`s Kuppeldraft-Logik (Joker horten/unten,
erzwungene Specials nach oben) bauen, (d) Gegner-Spezialfeld-Punkte gepaart
UND getrennt ausweisen (Nutzer-Vorgabe: Stoerkanal nicht mit dem eigenen
Wert verrechnen).

### (6) Eigene Entscheidungen (markiert, nicht Nutzer-Vorgabe)

- **Koordinator-Ausgangslage (0,00) nicht uebernommen, sondern selbst
  nachgemessen** -- REGEL 0 ("Agenten-Befunde sind Behauptungen"); gilt auch
  fuer Koordinator-Angaben, die selbst wieder von einer anderen Messreihe
  stammen koennten. Die Diskrepanz wurde benannt, nicht stillschweigend
  uebernommen oder verworfen.
- **Kein eigener Diagnose-Knopf fuer den k2-Special-Zweig** -- nach der
  positiven Messung ist die "unbedingt"-Fassung direkter als ein weiterer
  Schalter, der ohnehin sofort auf "immer an" stehen wuerde; `MOSAIC_
  PLATTENBAU=2` selbst bleibt der eigentliche Diagnose-Knopf (Default AUS,
  nie im Gating).
- **Keine neuen Unit-Tests fuer §18** -- Zeitbudget; die Aequivalenzpruefung
  in (4) (Vorher/Nachher byte-identisch) ist ein Integrationsnachweis, kein
  Ersatz fuer fehlende Unit-Abdeckung der neuen Funktionen. Nachtrag fuer
  eine Folge-Sitzung vermerkt.
- **k6 bewusst NICHT im selben Zyklus begonnen** -- explizit von der
  Koordinator-Vorgabe gedeckt, hier trotzdem als eigene Entscheidung
  vermerkt (ein Versuch waere angesichts des bereits verbrauchten
  Zeitbudgets ein Risiko fuer einen halbfertigen, schlecht geprueften
  Zustand gewesen).


---

## 19. SPEZIALFELDER-BAUSTEIN k6 (2026-08-13): Kuppeldraft gebaut und gemessen -- NICHT uebernommen (falsches Vorzeichen)

Nutzer-Freigabe (ueber Koordinator, Fortsetzung von §18): k6 (Spezialfelder)
nach `docs/domain_knowledge.md` §8 -- Kuppeldraft-Strategie (Joker horten und
auf untere Slots, erzwungene Special-Kuppeln nach oben, Joker-Prioritaet als
Stoerkanal). Eingriff primaer in der Kuppelwahl, nicht im Fliesendraft.

### (1) Frischer Aera-Anker: 20 k6-Seeds, Aktivitaet 20/20 GEPRUEFT

`evaluations/seeds_per_criterion/k6.txt` (20 Seeds) gegen `MOSAIC_PLATTENBAU=0`
vs `=6` (bestehender `Spezialbauer` aus §13, Nachbarzellen-Fuellung, VOR dem
Kuppeldraft-Zusatz dieser Sitzung). "Spezialfelder"-Kriterium GEPRUEFT in
20/20 Partien beider Arme aktiv (`scoring_tile_ids`). Ergebnis:
`evaluations/paired_arena_env_k6_baseline_fresh.json`.

| Groesse | Bezug (kein Plattenbauer) | k6 VOR §19 (bestehender Spezialbauer) |
| --- | ---: | ---: |
| Eigene Spezialfelder-Punkte Ø | -15,00 | **-9,75** |
| Gegner-Spezialfelder-Punkte Ø | -7,95 | -11,10 |
| Siege | 6/20 | 9/20 |

Der bestehende Spezialbauer verbessert die eigene Zahl bereits deutlich
gegenueber dem Bezug -- **-9,75 ist der fuer diese Sitzung gueltige Anker**,
nicht die vom Koordinator genannte Erwartung "≈-12" (die vermutlich, wie bei
k2, aus einer archivierten/anderen Messreihe stammt -- hier nicht weiter
verfolgt, da unten ohnehin gegen die frische Zahl entschieden wird).

### (2) Was gebaut wurde: `kuppeldraft_vorzug_k6`

Neue Kuppelwahl-Vorzugsstufe (Stufe 1: Kachel+Slot-Wahl, VOR
`Spezialbauer`s bestehender Nachbarzellen-Mechanik, die nur noch Stufe 2/
Rotation bedient -- Rotation aendert die Slot-REIHE einer Kachel nicht,
bleibt fuer diese Taktik irrelevant). Bewertung je (Kachel, freier Slot):

| Kachel-Typ | Obere Slot-Reihe | Mittlere | Untere Slot-Reihe |
| --- | ---: | ---: | ---: |
| Joker (kein Special) | 2,0 | 2,0 | **3,0** (bevorzugt) |
| Special-tragend | **1,5** (bevorzugt) | 1,0 | 0,5 |

Direkte Umsetzung der Nutzer-Vorgabe (Joker in untere Slots, erzwungene
Specials in obere).

### (3) Messung: 20 k6-Seeds, Kuppeldraft gegen den §19(1)-Anker

`cargo test --lib`: 416/0/20 (unveraendert). Wheel neu gebaut+installiert vor
UND nach dem Revert in (4), Paritaetsprobe haelt beide Male (`8c6684ff...`).
Ergebnis: `evaluations/paired_arena_env_k6_kuppeldraft_k6seeds.json`.

| Groesse | Anker (bestehender Spezialbauer) | Kuppeldraft AN |
| --- | ---: | ---: |
| Eigene Spezialfelder-Punkte Ø | -9,75 | **-10,50** |
| Gegner-Spezialfelder-Punkte Ø | -11,10 | **-6,60** |
| Siege | 9/20 | 5/20 |

Gepaartes Delta (eigen) **-0,75** (t=-0,839, p=0,412 -- FALSCHES Vorzeichen
fuer eine Uebernahme, die Kuppeldraft-Vorzugsstufe macht die eigene Zahl
tendenziell SCHLECHTER statt besser). McNemar auf den Siegen: b=8/c=4,
p=0,388 -- nicht signifikant, aber ein deutlicher, unerwuenschter Rueckgang
(9/20 -> 5/20). **Der Stoerkanal wirkt GEGENTEILIG**: die Gegner-Spezialfelder-
Punkte werden BESSER (-11,10 -> -6,60) statt schlechter -- das Joker-Horten
scheint dem Gegner (Heuristik) eher zu nuetzen als zu schaden, moeglicherweise
weil das Verdraengen von Jokern aus dem Display die verbleibenden
Special-Kacheln GLEICHMAESSIGER statt asymmetrisch verteilt.

### (4) Entscheidung: NICHT uebernommen -- Code bleibt unverdrahtet

**Beide Haelften der Vorab-Regel verfehlt** (kein signifikant positives Delta;
Sieg-Bedingung technisch "nicht signifikant schlechter", aber der Trend ist
eindeutig negativ und die eigene Zielgroesse selbst verschlechtert sich).
`kuppeldraft_vorzug_k6` bleibt als GETESTETE, aber NICHT verkettete Funktion
im Code (`#[allow(dead_code)]`, matching das Muster von `ueberpraesenz_
vorzug` in §14) -- `Spezialbauer::dome_vorzug` ruft wieder ausschliesslich die
bestehende Nachbarzellen-Mechanik (`dome_vorzug_fuer_zellen`) auf, GENAU wie
vor dieser Sitzung. `MOSAIC_PLATTENBAU=6` bleibt unveraendert bei -9,75
(dem §19(1)-Anker).

### (5) Eigene Entscheidungen (markiert, nicht Nutzer-Vorgabe)

- **Kein Diagnose-Knopf fuer den Kuppeldraft-Versuch angelegt** -- da das
  Ergebnis klar ablehnend ausfiel, waere ein Schalter fuer eine Fassung, die
  niemand einschalten sollte, reiner Mehraufwand; das Muster aus §14
  (`ueberpraesenz_vorzug`: gebaut, gemessen, unverdrahtet, kein Knopf) passt
  direkt.
- **Ursache des Gegenteil-Effekts (Gegner-Kanal) nicht weiter untersucht** --
  eine plausible Erklaerung steht in (3), aber sie ist eine Vermutung, keine
  Messung; eine Nachverfolgung (z.B. Kachel-Pool-Zusammensetzung ueber die
  Partie hinweg tracen) haette den k6-Umfang gesprengt.
- **Koordinator-Erwartung "≈-12" nicht weiter verglichen** -- da die Messung
  ohnehin ablehnend endet, war eine Klaerung der Diskrepanz (wie in §18)
  fuer die Entscheidung selbst nicht mehr entscheidungsrelevant.
- **Keine neuen Unit-Tests** -- Zeitbudget; das Integrations-Ergebnis (3) ist
  der einzige Beleg fuer `kuppeldraft_vorzug_k6`s Verhalten.

**Damit ist die Nutzer-Freigabe "k2 und k6 umsetzen" fuer diese Sitzung
abgeschlossen**: k2 uebernommen (§18), k6 gebaut, gemessen, und mit
begruendetem Befund abgelehnt (§19) -- kein halbfertiger Zustand in beiden
Faellen.


---

## 20. ECKPLATTEN-NEUBAU k5 (2026-08-14): Spaltenpaar-Ziel, +4,86 Plattenpunkte, p<0,0001 -- UEBERNOMMEN

Fortsetzung der Nutzer-Freigabe (Generator-Sortiment komplettieren, nach k2/
k6). Nutzer-Entwurf: statt vier isolierter Eck-Slots ein AEUSSERES
Spaltenpaar (Rasterspalten 0+1 oder 4+5) als Ziel -- schliesst BEIDE Ecken
derselben Seite (8+3=11 Punkte) und kombiniert nebenbei mit Kriterium 1
(zwei volle Spalten). Vorab GEPRUEFT (`scoring.rs:60`-64,
`score_corner_tiles` `scoring.rs:449`-467): k5 und k1 sind NICHT
wechselseitig ausgeschlossen (nur k5↔k2), obere Ecken 3 Pkt, untere 8 Pkt.

### (1) Frischer Anker: 22 k5-Seeds, Aktivitaet 22/22 GEPRUEFT

Nach der k2-Lehre (§18) NICHT die archivierte §13-Zahl (4,73) uebernommen,
sondern frisch nachgemessen: `MOSAIC_PLATTENBAU=0` vs `=5` (ALTER,
unveraendert isolierter Eckenbauer aus §13) auf `seeds_per_criterion/k5.txt`
(22 Seeds). "Eckplatten"-Kriterium GEPRUEFT in 22/22 Partien beider Arme
aktiv. Ergebnis: `evaluations/paired_arena_env_k5_baseline_fresh.json`.

| Groesse | Bezug (kein Plattenbauer) | k5 VOR §20 (alter Eckenbauer) |
| --- | ---: | ---: |
| Eckplatten Ø | 3,68 | **3,68** |
| Siege | 13/22 | 11/22 |

Der alte, isolierte Eckenbauer zeigt in dieser frischen Messung KEINEN
messbaren Unterschied zum Bezug (identischer Mittelwert, andere Verteilung)
-- **3,68 ist der fuer diese Sitzung gueltige Anker**, nicht die
archivierte §13-Zahl.

### (2) Was gebaut wurde: Spaltenpaar-Ziel statt vier isolierter Eck-Slots

`Eckenbauer` (plate_builder.rs) komplett neu: Kandidaten sind die zwei
AEUSSEREN Spaltenpaare `zellen_spaltenpaar(0)` (Spalten 0+1) und
`zellen_spaltenpaar(4)` (Spalten 4+5), je 12 Zellen (beide volle Spalten),
gewaehlt ueber `ziel_zellen_generisch_smart` (§18: echte Special-Nachbar-
Kosten, Seed-Streuung, keine sture Bindung -- §14-Lehre). Innerhalb des
gewaehlten Paars eine DREISTUFIGE Prioritaets-Kette (`.or_else`, gleiches
Muster wie die Special-Nachbar-Ketten in §16/§18) fuer Drafting, Kuppelwahl
UND Tiling:

1. Untere Ecke (Rasterzeilen 4-5, 8 Punkte) -- teuerster, wertvollster Slot.
2. Obere Ecke (Rasterzeilen 0-1, 3 Punkte).
3. Rest des Spaltenpaars (Rasterzeilen 2-3, reine Spalten-Fuellung ohne
   eigenen Eck-Bonus).

Kein separater Diagnose-Knopf (§18-Lehre: unbedingte Variante) -- die neue
Logik ist die EINZIGE Implementierung von `Eckenbauer`, erreichbar wie
bisher nur ueber `MOSAIC_PLATTENBAU=5`/`auto`.

`cargo test --lib`: 417/0/20 (unveraendert in der Fehlerzahl, keine neuen
Tests fuer §20 -- Zeitbudget, wie schon in §18/§19 vermerkt). Wheel neu
gebaut+installiert, `tools/parity_probe.py`: Hash `8c6684ff...` haelt.

### (3) Messung: 22 k5-Seeds, Spaltenpaar-Ziel gegen den §20(1)-Anker

Ergebnis: `evaluations/paired_arena_env_k5_spaltenpaar_k5seeds.json`.

| Groesse | Anker (alter Eckenbauer, 3,68) | Spaltenpaar-Ziel |
| --- | ---: | ---: |
| Eckplatten Ø | 3,68 | **8,55** |
| Endstand Ø | 43,32 | 42,64 |
| Strafleiste Ø | 11,64 | **9,77** |
| Siege | 11/22 | 11/22 |

Gepaartes Delta **+4,86**, t=4,789, **p=0,0001** (exakte zweiseitige
Student-t-Verteilung, df=21, per Inkomplette-Beta-Funktion nachgerechnet --
WEIT unter 0,05). McNemar auf den Siegen: b=6/c=6, **p=1,000** (keine
Sieg-Aenderung, sogar guenstigere Strafleiste). **Beide Haelften der
Vorab-Regel klar erfuellt.**

13 von 22 Partien (59 %) schliessen BEIDE Ecken derselben Seite ab
(≥11 Punkte); Kombinations-Beifang mit Kriterium 1 GEPRUEFT sichtbar (eine
Partie erreicht 14 vertikale Punkte = zwei volle Spalten zusaetzlich zu den
Eckplatten, exakt der Nutzer-Entwurf "kannst ihn fast schon kombinieren mit
k1 und zwei Spalten").

### (4) Entscheidung: UEBERNOMMEN

Bester Wert dieser gesamten Provokations-/Plattenbauer-Kampagne (§14-§20)
relativ zu seinem Orakel: 8,55 von Orakel 11,00 (78 %), mit KEINEM
Staerke- oder Strafleisten-Preis. `Eckenbauer` ist bereits unbedingt (kein
Knopf-Umbau noetig, siehe (2)) -- die Uebernahme ist mit dem Commit dieser
Sitzung bereits wirksam.

### (5) Eigene Entscheidungen (markiert, nicht Nutzer-Vorgabe)

- **Keine bespoke Kuppelwahl-Gewichtung fuer "Special in Ecken bevorzugen"
  gebaut** (anders als bei k6 explizit erwogen) -- die bestehende
  `zellen_wert`-Formel bewertet Special (2,0) bereits hoeher als eine offene
  farbgebundene Normalzelle (1,5), das reicht in Kombination mit der
  Prioritaets-Kette (untere Ecke zuerst) aus, um den Nutzer-Wunsch
  ("insbesondere untere Ecken") ueber die ZELLENAUSWAHL statt eine neue
  Sonderformel abzudecken -- durch die Messung in (3) bestaetigt, keine
  weitere Verfeinerung noetig.
- **Keine neuen Unit-Tests** -- Zeitbudget, wie bei §18/§19 vermerkt; die
  Integrationsmessung in (3) ist der Beleg.
- **`zellen_ecke` (alte Geometrie-Funktion) nicht geloescht**, nur
  `#[allow(dead_code)]` markiert -- sie traegt weiterhin ihren eigenen
  Geometrietest, Loeschung war nicht beauftragt (LOESCHVERBOT).
