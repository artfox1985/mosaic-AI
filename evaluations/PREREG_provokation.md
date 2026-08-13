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

Drei Nachbesserungen an `spaltenbau.rs`/`provokation.rs` gegenueber dem
Stand aus Commit `fd2d15e` (1,40 vertikale Punkte, Blocker zu 10/12 auf
SPEZIAL-Zellen):

1. **Wild-Zellen aktiv bedient**: `provokation::vorzugszug_fuer_spalte` liess
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
k1-Seeds (`evaluations/seed_auswahl_platten.json`, GEPRUEFT:
`[2,3,6,8,9,11,13,20,22,26,29,32,34,39,44,50,52,57,59,69]`), gepaart gegen
`MOSAIC_SPALTENBAU=0` als Kontrolle, `MOSAIC_SPALTENBAU_TRACE=1` fuer beide
Arme (No-Op ohne aktiven Spaltenbauer). Werkzeug: `tools/paired_arena_env_ab.py
--env-name MOSAIC_SPALTENBAU --arms 0 1 --control 0 --net-sims 400
--heur-sims 150 --seeds <k1> --log-games`, Ergebnis in
`evaluations/paired_arena_env_spaltenbau_r2.json`. Metrik ueber
`tools/plattenpunkte_aus_arena.py`s `auswerten()`, Kriterium "Vertikale
Reihen"; Verteilung/Blocker ueber das NEU gebaute `tools/spaltenbau_trace.py`
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
`PREREG_platzierungsseite.md` §5 vorab formulierte Vermutung ("dann ist der
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
Mechanismus und keiner, den `spaltenbau.rs` selbst loesen kann -- es waehlt
nur unter dem, was JETZT angeboten wird, es kann keine zukuenftige
Fabrikbefuellung erzwingen. Ohne Nutzer-Entscheidung KEINE weitere
Verschaerfung (naechster denkbarer Schritt waere z.B. eine
Versorgungs-bewusste Zielspalten-Wahl, die auf ANGEBOT-WAHRSCHEINLICHKEIT
statt nur Brettzustand reagiert -- das ist neue Mechanik, kein Tuning mehr).


---

## 12. RUNDE 3 GEMESSEN (2026-08-13): 5,95 statt 5,60 -- Ziel 7,00 weiterhin verfehlt, Blocker-Anteil UNVERAENDERT

### (1) Was ist zaehlbar? -- belegt am Code

`engine/src/provokation.rs::verbleibende_farben` (neu, `pub(crate)`) rechnet
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
`provokation.rs::verbleibende_farben_zaehlt_jede_sichtbare_fundstelle`
(6 kuenstlich verteilte Rot-Kopien ueber alle 5 Fundstellen-Kategorien,
exakte Gegenrechnung `13 - 6`).

### (2) Die drei Bausteine, je ein Commit

| Baustein | Commit | Was |
| --- | --- | --- |
| 1 (Versorgung zaehlen) + 3 (Vorzug bevorzugt Knappheit) | `a10202f` | `verbleibende_farben`/`farben_index` (`provokation.rs`); `vorzugszug_fuer_spalte` sortiert Kandidaten jetzt primaer nach Knappheit der genommenen Farbe, "vollste Reihe" bleibt Tie-Break |
| 2 (Zielwahl versorgungsgewichtet) | `d18e523` | `engpass_aufschlag` (0 bei voller, bis 2,5 bei restlos verbrauchter Versorgung); `spalten_kosten` bekommt die vorberechnete Versorgungslage als Parameter, alle 3 Aufrufstellen umgestellt |

Baustein 1+3 liegen technisch in einem Commit (beide in
`provokation.rs`, `vorzugszug_fuer_spalte` selbst braucht
`verbleibende_farben` direkt in seinem Kandidaten-Ranking -- eine
Hunk-Trennung haette das Diff riskanter gemacht als der Gewinn an
Granularitaet wert war; explizit KEIN Automatismus wie `git add -A`,
beide Commits enthalten ausschliesslich die genannten Engine-Dateien).

`cargo test --lib`: 388 bestanden, 0 fehlgeschlagen (ein Bestandstest,
`vorzugszug_reicht_dynamische_spalte_an_provokation_kern_durch`, nahm
implizit an, Spalte 0 bleibe bei echtem Zufalls-Fabrikinhalt die
guenstigste -- das haengt seit Baustein 2 vom Versorgungsstand ab; im Test
die Tischmitte deterministisch geleert, siehe Kommentar dort). Wheel
gebaut+installiert, `tools/paritaets_probe.py`: Hash `8c6684ff...` haelt,
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
`plattenpunkte_aus_arena.py`). Sieg-Differenz NULL (15/20 beide Arme,
McNemar b=4/c=4, p=1,0, aus dem Rohergebnis-JSON) -- der Spaltenbauer
kostet in dieser Runde nicht messbar Staerke, weniger noch als Runde 2
(dort p=0,73, Endstand-Differenz -7,2; hier nur -1,35, Strafleiste sogar
minimal GUENSTIGER statt teurer). Verteilung der 20 AN-Partien: 15/20 mit
mindestens einer geschlossenen Spalte (7 Punkte), davon 2/20 mit ZWEI
Spalten (14 Punkte) -- eine deutlich dichtere Verteilung als Runde 2s
Einzelwerte suggerieren.

**Verteilungs-Gate**: bestanden, alle 6 Spalten mit Ereignissen (Spalte
0=15, 1=27, 2=5, 3=14, 4=15, 5=24, aus `spaltenbau_trace.py`).

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
  vierte Nachbesserung an `spaltenbau.rs`.
