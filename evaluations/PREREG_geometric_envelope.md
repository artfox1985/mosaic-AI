<!-- STATUS: OFFEN | Frage: Hilft ein GEOMETRISCHES Gelaender -- die Dreiecks-Einhuellende, frueh stark und gegenlaeufig zum Value-Kopf abklingend --, wenn es in SUCHE und TILING eingreift statt nur Netz-Eingabe zu sein? | Beleg: NICHTS GEBAUT, Zuschnitt registriert (par.3d). **Spreizung gemessen (par.3f, 2026-09-02):** b01 0,048/0,065 gegen v18_2d 0,018, aber die multiplikative Form kippt in 1 von 142 bzw. 4 von 192 Stellungen einen Punktvorsprung -- Form A endgueltig tot, B oder C Pflicht. Naechster Schritt: Stufe 0 (weiss der Kopf es schon?) mit Formwahl B/C. -->

# Vorregistrierung: das geometrische Gelaender (Dreiecks-Einhuellende)

**Angelegt 2026-08-31, Nutzer-Auftrag:** *"mach das geometrische gelaender
als eigenen prereg. das werden wir gut gebrauchen koennen fuer die ersten
runden wo der value head keine ahnung hat."* Loest den Merkposten
"Einhuellende im 2D-Encoder" ab (Nutzer-Frage 2026-08-24, bis heute
unregistriert) und buendelt ihn mit dem Rundenabklingen aus
`PREREG_search_depth_column_optimum.md` par.2m.

## par.1 Die Frage

Der Value-Kopf beziffert den Plattenlohn zu leise (R5-Steigung 0,0886 statt
~1). Alle bisherigen Wege wollten IHN reparieren. Dieser hier fragt anders:
**laesst sich die fruehe Zugwahl geometrisch stuetzen, ohne den defekten
Kanal zu benutzen?** Die Einhuellende ist eine reine Geometrie -- sie
braucht keine Bewertung des Plattenlohns, um zu sagen, welche Zellen einem
erreichbaren Zielbild dienen.

## par.2 Warum FRUEH, und warum abklingend (vier Gruende, jeder belegt)

1. **Frueh entscheidet es sich.** Die Ketten-Diagnose
   (`PREREG_heuristic_v2_long_rows.md` par.3b.8) zeigt, dass Abweichungen
   sich ueber die Vollendungskette multiplizieren (0,6^k); die Versorgung
   wird in Runde 1-2 verspielt, nicht in Runde 5.
2. **Dort ist der Bewerter am schwaechsten.** Der Ownership-Kopf trennt in
   Runde 1 mit AUC **0,698** gegen **0,886** in Runde 5
   (`PREREG_ownership_selector.md` par.9.4).
3. **Spaet braucht es nichts.** Ab Runde 5 rechnet die exakte
   Alpha-Beta-Suche (`round5.rs`). Ein Gelaender dort ist im besten Fall
   wirkungslos und im schlechtesten eine Stoerung des exakten Loesers --
   deshalb ist das Abklingen keine Feinheit, sondern **Pflicht** (par.4).
4. **Es umgeht den defekten Kanal.** Die Huelle ist geometrisch; sie haengt
   nicht an der Groesse, die der Kopf zu leise beziffert.

## par.3 Was die Einhuellende IST -- und die drei getrennten Bausteine

**Sie ist eine MACHBARKEITSHUELLE, keine Brettregel.** Alle 36 Zellen sind
legal bebaubar; das Dreieck `r + c <= 5` (21 Zellen, Zeilen 6/5/4/3/2/1)
beschreibt, was praktisch erreichbar ist: die gemessenen Fuellraten je
Rasterzeile sind 4,88 / 4,70 / 2,88 / 2,23 / 1,71 / 1,31 und haben exakt
dieselbe Neigung (`PREREG_heuristic_v2_long_rows.md` par.3a).

**Es gibt GENAU ZWEI Huellen, gespiegelt ueber die SPALTEN-Achse**
(Nutzer-Berichtigung 2026-08-31): Anker in Spalte 0 oder in Spalte 5. Die
Spiegelung ueber die ZEILEN-Achse ergibt zwar geometrisch ebenfalls
21-Zellen-Dreiecke, aber keine spielbare Huelle -- sie legte die breite Zeile
nach UNTEN, und genau dagegen stehen die Fuellraten: 4,88 oben gegen 1,31
unten. Die Huelle ist nach oben verankert, weil die oberen Musterreihen
zuverlaessig liefern und die unteren nicht. Wer hier vier Orientierungen
zaehlt, zaehlt geometrische Konstruktionen und nicht Optionen des Spielers.

| Baustein | Stand |
| --- | --- |
| **(a) Huellen-Trimm der Ownership-Loss-Maske** | REGISTRIERT (Lehrer-Prereg, Nachtrag 6) -- nicht Gegenstand dieser Datei |
| **(b) Einhuellende als 2D-Eingabeebene** | Merkposten seit 2026-08-24, hier erstmals registriert |
| **(c) Rundenabklingendes Gelaender** | neu (par.2m des Suchtiefen-Strangs), hier erstmals registriert |
| **(d) Huelle als TILING-Ziel** in den fruehen Runden statt Sofortpunkte | neu (Nutzer 2026-08-31), par.3b |
| **(e) Huelle als Eingriff in die SUCHE** (Prior/Utility auf Platzierungszuege) | neu (Nutzer 2026-08-31), par.3b |

## par.3b DIE HUELLE MUSS IN DIE SUCHE UND INS TILING GREIFEN (Nutzer 2026-08-31)

Nutzer: *"diese muss aktiv in die Suche wie auch das Tiling eingreifen.
Maximieren der Tiling-Punkte in den ersten 2-3 Runden bringt nicht wirklich
was. Die meisten Punkte kommen ab Runde 4."*

**Damit sind es fuenf Bausteine, nicht drei** -- (d) Tiling-Ziel und (e)
Such-Eingriff kommen dazu. Und sie sind nicht optional: eine Huelle, die nur
als Eingabeebene existiert, kann vom Loeser ueberstimmt werden, der danach
platziert.

**Die Mechanik, die sie ueberstimmt, ist benannt und gemessen:**
`best_first_step_inner` waehlt nach reinen SOFORTPUNKTEN
(`tiling_solver.rs:49-56`) und wirft draft-seitige Absicht weg -- derselbe
Befund, den der Split-Test als kleinere Haelfte des Durchbruchs ausgewiesen
hat. Wer die Huelle ins Netz gibt, aber den Loeser weiter auf Sofortpunkte
optimieren laesst, baut zwei Instanzen mit gegenlaeufigem Ziel.

**WANN die Punkte fallen -- gemessen 2026-08-31, und in zwei Anlaeufen
richtig gestellt** (80 Partien / 160 Seiten aus `v22-b05-value-argmax`;
Artefakt `round_point_profile_b05.json`):

Der erste Anlauf hat den Punktestand je Runde gebinnt und kam auf "ab Runde 4
fallen 52,8 Prozent". **Diese Zahl ist zurueckgezogen**: die
Wertungsplatten werden erst NACH Spielende gebucht (`apply_end_scoring`,
game.rs:981, Nutzer-Hinweis), ihre Pauschale steckt also im
Runde-5-Zuwachs. Die Kurve vermischte damit Platzierungspunkte und
Endwertung.

Direkt gemessen, ueber die Summe von `scoring_tile_points` auf den AKTIVEN
`scoring_tile_ids`:

| Groesse | je Seite |
| --- | --- |
| Endstand | 44,23 |
| davon **Endwertung (Platten)** | **4,67 = 10,6 Prozent** |
| davon k1 (Spalten), wenn aktiv | 3,98 (in 58 von 160 Seiten) |

**Das ist die eigentliche Pointe fuer diesen Arm, und sie ist schaerfer als
die Rundenkurve:** die Platten zahlen **einmal, ganz am Ende**. Waehrend der
Runden 1 bis 4 wird von ihrem Wert NICHTS gebucht -- ein Zug-fuer-Zug-
Punktemaximierer sieht das ganze Spiel ueber kein Plattensignal, und fuer
Spalten ist es zusaetzlich eine Stufe (siehe unten). Die 10,6 Prozent decken
sich mit dem Leitstern ("rund 10 Punkte je Partie bleiben liegen").

**Die Regelmechanik erklaert es, und zwar schaerfer als eine glatte Kurve
(Nutzer-Berichtigung 2026-08-31):** k1 der ENGINE ist eine STUFE, kein
Verlauf. `score_vertical_rows` zaehlt die VOLLSTAENDIGEN Spalten und zahlt
7 Punkte je Stueck (scoring.rs:709-712) -- die ersten fuenf Zellen einer
Spalte bringen exakt **null**, die sechste bringt **alle sieben**.

Der quadratische Ausdruck `7*(f/6)^2` steht in `scoring_progress`
(scoring.rs:160-166) und ist ein SHAPING-Term, nicht die Wertung: ein
glatter Fortschritts-Ersatz, dessen Exponent 2 laut Funktionskommentar EINE
fast fertige Linie gegenueber vielen halbfertigen bevorzugt. Er ist zudem der
eingefrorene Elo-Anker-Term und wird nicht angefasst. Wer ihn mit der Regel
verwechselt, unterschaetzt den Effekt: die echte Auszahlung ist nicht
"frueh wenig", sondern **frueh nichts**.

Damit ist die Aussage nicht mehr nur quantitativ, sondern kategorisch: ein
Loeser, der nach Sofortpunkten waehlt, sieht beim Spaltenbau bis zur
Vollendung UEBERHAUPT KEIN Signal. Er kann die Huelle nicht beruecksichtigen,
weil sie in seiner Zielfunktion gar nicht vorkommt -- genau deshalb ist (d)
Pflicht und nicht Kuer.

**Folge fuer das Abklingprofil (par.4.1):** es ist nicht frei waehlbar,
sondern soll der gemessenen Kurve folgen -- Huelle dominiert, solange die
Sofortpunkte klein sind (Runden 1-3), und tritt zurueck, wenn die Wertung
selbst die richtige Richtung vorgibt (ab Runde 4, exakt 0 in Runde 5, wo der
Loeser exakt rechnet).

## par.3a Warum (b) NICHT trivial ist -- und wo der Einwand sitzt

Der naheliegende Einwand: eine Ebene "Dreiecks-Zugehoerigkeit je Zelle" ist
**konstant** und traegt damit keine Information. Er ist fuer den flachen
Zweig richtig und fuer den Conv-Zweig falsch:

* Der **Flach-Zweig** sieht ohnehin absolute Positionen -- dort waere die
  Ebene tatsaechlich redundant.
* Der **Conv-Zweig** ist translations-equivariant. `Mosaic2DNet` faehrt zwei
  3x3-Lagen mit `padding=1` und KEINEN Koordinaten-Kanal (geprueft
  2026-08-31: `NUM_PLANES_CHANNELS = 2*16 + 19 + 25 + 1 + 2`, alles Brett-,
  Spielzustands- und Spezialfeld-Kanaele). Eine geometrische Ebene ist fuer
  ihn ein **absoluter Positions-Prior**, den er aus den vorhandenen Kanaelen
  nicht ohne Weiteres synthetisiert.

**Das ist eine HERLEITUNG, keine Messung** -- und sie ist der Grund, warum
Stufe 0 unten zuerst prueft, ob der Kopf die Huellen-Zugehoerigkeit heute
schon implizit kennt. Faellt das positiv aus, ist (b) erledigt, bevor
irgendetwas gebaut wird.

**Die Orientierung ist der zweite Grund, warum die Ebene nicht konstant
ist:** welche der ZWEI Huellen ein Spieler verfolgt, ist eine WAHL -- und die
faellt frueh, mit den ersten Platzierungen. Zwei Ebenen (Anker Spalte 0,
Anker Spalte 5) plus der Brettzustand sagen damit etwas ueber PASSUNG, nicht
nur ueber Geometrie: welche der beiden Huellen zum bereits gebauten Brett
passt, ist eine Zustandsfrage, keine Konstante.

## par.3c GEGENGLEICHE GEWICHTUNG: Huelle runter, Value-Kopf rauf (Nutzer 2026-08-31)

Nutzer: *"Der Tiling-Solver hat eigentlich den Value-Head als Faktor fuer die
Weitsicht bekommen. Das hat aber bis dato nur wenig durchgeschlagen. Mit der
Einhuellenden, deren Einfluss ueber die Runden abnimmt, und dem Value-Head,
dessen Gewicht dann gegengleich zunimmt, laesst sich das vermutlich sauber
adressieren."*

**Der Value-Kopf IST verdrahtet, und warum er wenig durchschlaegt, steht im
Code (geprueft 2026-08-31):** `NET_TILING_TIEBREAK_ENABLED = true`
(tiling_solver.rs:857) multipliziert `punkte * value` ueber die
`NET_TILING_TOPK = 12` besten Abschluesse. Der zugehoerige Befund
(`tiling_candidate_spread.json`, v18_best, 142 Stellungen aus den Runden 2-4
mit mehr als einem Kandidaten, 51 Faelle mit Auswahlaenderung): die
Multiplikation hat in **0 von 51 Faellen** einen echten Punktvorsprung
ueberstimmt; die mediane Value-Spreizung unter den Top-12 liegt bei **0,017**
(IQR 0,010 bis 0,028). Der Kommentar im Code sagt es selbst: sie wirkt
"ausschliesslich als Stichentscheid zwischen Abschluessen mit (nahezu)
IDENTISCHEN Punkten".

**Daraus folgt mehr als eine Gewichtsfrage:** ein Faktor, der 0,017 breit
ist, kann einen Punkt nicht kippen -- egal, mit welchem Gewicht man ihn
versieht. Wer den Value-Kopf spaet WIRKLICH entscheiden lassen will, muss die
KOMBINATIONSFORM aendern (additiv auf vergleichbarer Skala oder als
Rangkriterium), nicht nur einen Multiplikator drehen. Das ist der Grund,
warum "mehr Value-Gewicht" bisher nicht durchschlug, und er ist gemessen,
nicht vermutet.

**Der Zuschnitt, den der Nutzer vorschlaegt, passt genau auf die gemessenen
Kurven:**

| Runde | Sofortpunkte | Value-Kopf | Huelle |
| --- | --- | --- | --- |
| 1-2 | klein und strukturell blind (Spalten zahlen erst bei Vollendung, Platten erst am Ende) | am schwaechsten (Spalten-AUC 0,698) | **traegt** |
| 3-4 | wachsend | wird verlaesslich | klingt ab |
| 5 | Endwertung faellt | AUC 0,886 -- aber der exakte Loeser rechnet ohnehin | **null** |

Die beiden Gewichte sind damit nicht zwei unabhaengige Knoepfe, sondern EIN
Regler: die Huelle vertritt die Weitsicht dort, wo der Bewerter sie noch
nicht hat, und tritt ab, sobald er sie hat. Das ist zugleich die
inhaltliche Begruendung fuer das Abklingprofil aus par.4.1 -- es folgt der
Verlaesslichkeitskurve des Kopfes, nicht einer gewaehlten Zahl.

**Was daran zu registrieren bleibt, bevor gebaut wird:** die Kombinationsform
(par.4.2 verlangt Potentialform fuer alles, was ins ZIEL geht -- ein
Auswahlkriterium im Loeser ist etwas anderes und braucht seine eigene
Begruendung), die Stuetzstellen des Profils, und ob der Punkte-Term frueh
ueberhaupt bleiben soll. Alle drei sind eigene Entscheide, keine
Implementierungsdetails.

## par.3d DER REGLER, SAUBER ZUGESCHNITTEN (registriert 2026-08-31)

Auf Nutzer-Auftrag ("dann halt das mal sauber fest") wird aus der Idee ein
entscheidbarer Zuschnitt. Die Auswahl unter den `top_k_tilings`-Kandidaten
bekommt die Form

```
score(kandidat, runde r) = w_p(r) * punkte + w_e(r) * huelle + w_v(r) * value
```

mit der harten Auflage **w_e(5) = 0** (in Runde 5 rechnet `round5.rs`
exakt) und der Leitidee, dass w_e und w_v gegenlaeufig verlaufen.

### (i) Kombinationsform -- der Kern, und er ist NICHT frei

| Form | Stand |
| --- | --- |
| **A: multiplikativ** (`punkte * value`, heutiger Bestand) | **AUSGESCHLOSSEN** fuer eine echte Value-Fuehrung: gemessen 0 von 51 Faellen, in denen sie einen Punktvorsprung ueberstimmt haette (par.3c). Sie bleibt, was sie ist -- ein Stichentscheid unter Punktgleichheit |
| **B: additiv auf ANGEGLICHENER Skala** | der Kandidat. Punkte sind ganzzahlig und je Stellung verschieden gespreizt, `value` liegt in [0,1] mit ~0,017 Spannweite -- ein Gewicht auf rohen Skalen waere Willkuer. Angleichung je Stellung ueber die Spannweite INNERHALB der Kandidatenmenge (beide Groessen auf ihre eigene Spreizung normiert), dann ist w_v interpretierbar |
| **C: lexikografisch mit Toleranzband** | Punkte entscheiden, solange der Vorsprung ueber einer Schwelle liegt; darunter entscheidet Value/Huelle. Einfacher zu begruenden, aber die Schwelle ist ein weiterer freier Parameter |

**Vor der Wahl steht eine Messung, und sie ist billig:** die 0,017 stammen
von `v18_best`, einem PLATTENBLINDEN Netz
(`evaluations/artifacts/tiling_candidate_spread.json` -- **diese Datei liegt
NICHT im Baum** (Pruefung 2026-09-01; nur das Werkzeug
`tools/tiling_candidate_spread.py` existiert). Die Zahlen 0,017 und "0 von 51"
sind damit im Repo unbelegt; warum sie nicht einfach neu erzeugt werden
koennen, steht in par.3e). Ob ein
spaltenfaehiger Kopf unter denselben Kandidaten breiter streut, ist offen
und mit dem vorhandenen Werkzeug in einem Lauf zu klaeren:
`tools/tiling_candidate_spread.py --model v23-b01_brierbest --k 12`.
**Vorab festgelegte Lesart:** bleibt die Spreizung in derselben
Groessenordnung (unter ~0,05), ist Form A endgueltig tot und B oder C
Pflicht; waechst sie deutlich, koennte schon eine Skalen-Angleichung ohne
Formwechsel reichen.

### (ii) Das Profil -- Stuetzstellen statt Kurvenanpassung

w_e faellt monoton von Runde 1 auf 0 in Runde 5, w_v steigt gegenlaeufig.
Registriert werden STUETZSTELLEN, keine Formel: je Runde ein Wertepaar, das
im Lauf-Manifest steht und damit nachpruefbar ist. Die Form folgt der
gemessenen Verlaesslichkeit des Kopfes (Spalten-AUC 0,698 in R1 gegen 0,886
in R5), nicht einer gewaehlten Funktion -- ein Vorschlag als Ausgangspunkt,
zu bestaetigen oder zu ersetzen:

| Runde | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- |
| w_e | 1,0 | 0,75 | 0,5 | 0,25 | **0** |
| w_v | 0 | 0,25 | 0,5 | 0,75 | 1,0 |

### (iii) Bleibt der Punkte-Term frueh?

Offen, und bewusst nicht vorentschieden. Dafuer spricht, dass Sofortpunkte
auch frueh nicht wertlos sind (Strafleisten-Vermeidung haengt daran);
dagegen, dass sie beim Spaltenbau bis zur Vollendung nachweislich NULL
Information tragen und die Huelle genau dort fuehren soll. Ein Arm mit
w_p(1..2) = 0 ist die schaerfste Fassung der Nutzer-These
("Maximieren der Tiling-Punkte in den ersten 2-3 Runden bringt nicht
wirklich was") und waere als eigener Arm zu fahren, nicht als Default.

### (iv) Reihenfolge

1. Spreizungs-Messung auf b01 (oben, ein Lauf, entscheidet (i)).
2. Stufe 0 aus par.5 (weiss der Kopf die Huelle schon?).
3. Erst dann bauen -- Form, Profil und Punkte-Frage sind dann alle drei
   entschieden statt geraten.

## par.4 PFLICHT-AUFLAGEN (ohne sie wird nichts gebaut)

1. **Abklingen bis NULL in Runde 5.** Der exakte Loeser bekommt keinen
   Gelaender-Term. Profil (Vorschlag, in Stufe 2 festzulegen): voll in R1,
   dann monoton fallend, ab R5 exakt 0.
2. **Potentialform, wenn ueberhaupt ein Term ins Ziel geht.** Shaping auf
   Wertungsplatten war in diesem Projekt mehrfach H0, und die Injektionslinie
   gilt als zu Ende gemessen. Neu waere hier ausschliesslich die
   POTENTIALFORM (Ng/Harada/Russell -- die einzige nachweislich
   politik-erhaltende Bauform, `RESEARCH_heuristic_methodology_external`
   4.6). Ein nicht-potentialfoermiger Term ist eine Wiederholung eines
   geschlossenen Wegs und wird nicht registriert.
3. **Additiv im Encoder.** Neue Ebenen haengen HINTEN an
   (`NUM_PLANES_CHANNELS` waechst), binaere vor `NUM_BINARY_PLANES_CHANNELS`,
   wertetragende dahinter. Alt-ONNX muessen spielbar bleiben; Cache-Key,
   Paritaets-Gate und ONNX-Export ziehen im selben Zug nach (Praezedenz:
   77 -> 79 bei den Spezialfeld-Kanaelen, `PREREG_special_tile_yield.md`
   par.4a).
4. **Traeger ist ein spaltenfaehiges Netz.** Alle frueheren
   Huellen-Messungen liefen auf plattenblinden Koepfen. Der Arm faehrt
   fruehestens auf v23.

## par.5 STUFENPLAN mit Toren

**Stufe 0 -- weiss der Kopf es schon? (netzfrei bis auf Vorwaertspaesse,
kein Bau, Stunden).** Auf gespeicherten Zustaenden pruefen, ob sich die
Huellen-Zugehoerigkeit einer Zelle aus den vorhandenen Ownership-/
Value-Ausgaben ABLESEN laesst (Diskriminierung innerhalb/ausserhalb der
Huelle, je Runde getrennt). Vorab festgelegte Lesart: **liegt die
Trennung in Runde 1-2 bereits hoch, ist (b) gegenstandslos** -- dann fehlt
dem Netz nicht die Geometrie, sondern ihre Bewertung, und der Strang faellt
zurueck auf die Betrags-Schiene. Instrumente vorhanden
(`tools/probes/ownership_column_intent.py`, `column_build_prior_mass.py`).

**Stufe 1 -- Eingabeebene (b).** ZWEI binaere Ebenen (Anker Spalte 0, Anker
Spalte 5), additiv. Tor: **Paritaets-Gate zuerst** (Netz ohne die
Ebenen bitgleich), dann Offline-Vergleich auf demselben Fenster; ein
Staerkeurteil faellt erst in Stufe 3.

**Stufe 2 -- rundenabklingendes Gelaender (c).** Potentialform, Profil nach
par.4.1. Getrennt registrieren, sobald Stufe 1 steht -- die Form des
Potentials und das Abklingprofil sind eigene Entscheide.

**Stufe 3 -- Arena.** Value-/Zielaenderungen brauchen Arena-Gating; es gibt
keinen validierten Offline-Praediktor (`docs/working_rules.md`). Gepaart,
Block-Ebene, sechs Standard-Kennzahlen, `laufzeit`-Block.

## par.6 Entscheidungsmass, vorab

**Primaer: volle Spalten je Partie und Seite am argmax-Instrument**, gegen
denselben Traeger ohne Gelaender, gepaart. Das ist die Kampagnen-Groesse und
zugleich Tor 2 der Generationen-Schleife (`docs/generation_loop.md`).

**Sekundaer, als Mechanismus-Nachweis: die kosten-gewichtete
Huellen-Abdeckung.** Sie ist die Leitkennzahl der Einhuellenden
(Lehrer-Prereg par.3b.8): Mensch 0,84, Maschinen 0,54-0,62. Bewegt sich die
Spaltenzahl OHNE diese Groesse, wirkt etwas anderes als das Gelaender.

**Nicht das Entscheidungsmass:** Offline-Value-Masse allein. Die
Orakelmetriken haben Architektur-Staerke in diesem Projekt schon einmal
falsch vorhergesagt.

## par.7 Registriertes Risiko

Der ehrliche Gegenwind steht in par.4.2: Shaping-Terme auf Wertungsplatten
waren mehrfach H0. Wer diesen Arm faehrt, faehrt gegen eine Grundrate. Was
ihn davon unterscheidet, ist zweierlei und nicht mehr -- die Potentialform
(politik-erhaltend statt Ziel-verzerrend) und ein Traeger, der Spalten
ueberhaupt bauen kann. Faellt der Arm negativ aus, ist das der Befund: dann
traegt auch die geometrische Umgehung den fruehen Engpass nicht, und es
bleibt die Betrags-Schiene.

## par.3e Das Spreizungs-Artefakt fehlt, und das Werkzeug kann b01 nicht laden (Pruefung 2026-09-01)

`evaluations/artifacts/tiling_candidate_spread.json` existiert im Baum nicht;
`tools/tiling_candidate_spread.py` existiert. Zwei Gruende, warum die Zahl
nicht einfach nachgemessen wurde:

1. **Der Checkpoint fehlt:** das Werkzeug laedt `models/alphazero_<name>.pth`
   (Zeile 59); `alphazero_v18_best.pth` liegt nicht mehr in `models/`. Die
   Erstmessung (0,017 Spreizung, 0 von 51 gekippt) ist damit im Repo nicht
   reproduzierbar und gilt als UNBELEGTE Erinnerung, nicht als Befund.
2. **Das Werkzeug ist flach:** es baut `MosaicNet` mit `state_to_tensor`
   (Zeilen 51-62), also den Flach-Encoder. `v23-b01_brierbest` ist ein
   `Mosaic2DNet`; die registrierte Messung "Spreizung auf b01" (par.3d iv)
   braucht daher zuerst eine kleine Werkzeug-Anpassung (2D-Encoder laden,
   Eingabeform vom Modell nehmen). Das ist ein Bau, kein Handgriff, und wird
   hier nicht nebenbei erledigt.

Folge fuer par.3d (i): Form A ist NICHT "gemessen ausgeschlossen", sondern
aufgrund einer nicht mehr belegbaren Messung an einem plattenblinden Netz
als unwahrscheinlich eingestuft. Die Entscheidung zwischen A, B und C faellt
erst nach der b01-Messung; bis dahin ist keine Form gesetzt.

## par.3f SPREIZUNG GEMESSEN: b01 streut 2,6- bis 3,6-mal breiter, kippt aber trotzdem fast nie einen Punktvorsprung (2026-09-02, Nachtprogramm N6)

`tools/tiling_candidate_spread.py` (seit 2026-09-01 2D-faehig, Flach-Eingabe
wird wie im Rust-Pfad auf die Modellbreite gekuerzt; seit 2026-09-02 zaehlt
es ECHTE Kippungen eines Punktvorsprungs getrennt von Wechseln unter
punktgleichen Kandidaten), k=12, 400 Stellungen je Satz. Artefakte
`evaluations/artifacts/tiling_candidate_spread_{b01_v1,b01_v3,v18_2d_v1}.json`.

| Netz | Satz | Stellungen mit Auswahl (R2-4) | Value-Spreizung Median [IQR] | Wechsel Punkte x Value | davon echte Kippungen eines Punktvorsprungs |
| --- | --- | --- | --- | --- | --- |
| `v18_2d` (plattenblind, aus dem Backup) | frozen_v1 | 142 | **0,018** [0,011, 0,033] | 51 | **0** |
| `v23-b01_brierbest` | frozen_v1 | 142 | **0,048** [0,023, 0,089] | 48 | **1** (1 Punkt) |
| `v23-b01_brierbest` | frozen_v3 | 192 | **0,065** [0,028, 0,110] | 83 | **4** (Median 1, Max 2 Punkte) |

**Die Erstmessung ist damit rekonstruiert:** die "0,017 Spreizung, 0 von 51"
aus par.3c waren 0,018 und "51 Wechsel, 0 echte Kippungen" an einem
plattenblinden Netz derselben Aera (dort `v18_best`, hier `v18_2d`; der flache
Checkpoint existiert nicht mehr). Die Formulierung "0 von 51 Faellen einen
Punktvorsprung gekippt" war in der Sache richtig, aber die 51 waren Wechsel
zwischen PUNKTGLEICHEN Kandidaten, kein Nenner aus Vorspruengen.

**Verdikt nach der vorab festgelegten Lesart (par.3d i):** die Spreizung des
spaltenfaehigen Kopfs liegt mit 0,05-0,065 an der registrierten Grenze
(~0,05), also in derselben Groessenordnung, nicht "deutlich groesser". Und der
entscheidende Punkt steht in der letzten Spalte: selbst mit dreifacher
Spreizung kippt die multiplikative Form in 1 von 142 bzw. 4 von 192
Stellungen einen Punktvorsprung, und nur um 1-2 Punkte. **Form A ist als
Value-Fuehrung endgueltig tot; B (additiv auf angeglichener Skala) oder C
(lexikografisch mit Toleranzband) ist Pflicht.** Eine reine Skalen-Angleichung
ohne Formwechsel reicht nicht. Nebenbefund: b01 streut auf dem eigenen
Aera-Satz (v3) breiter als auf dem alten (v1), also hat der Satzwechsel
(`frozen_v3`) hier Substanz.
