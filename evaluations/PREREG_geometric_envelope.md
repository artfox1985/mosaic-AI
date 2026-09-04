<!-- STATUS: OFFEN | Frage: Hilft ein GEOMETRISCHES Gelaender -- die Dreiecks-Einhuellende, frueh stark und gegenlaeufig zum Value-Kopf abklingend --, wenn es in SUCHE und TILING eingreift statt nur Netz-Eingabe zu sein? | Beleg: JA in der Bauform par.8.7 (K3-P, Potential auf dem PROJIZIERTEN Brett, C 1,0): gepoolt 191:129 auf 320 Paaren (p = 0,014, beide Seeds gleich), Spalten +0,09 Arena / 0,555 argmax (b01 0,515), Huelle +0,10 bis +0,16 Arena, Punkte +3. Raster-Form (par.8.2/8.3, par.9), Value im Tiling (8.6a), Erreichbarkeit/Ownership (8.9a) und Huellen-Bauer (8.8) tragen nicht. Offen: Betriebspunkt @100 und Champion-Kante; Wiedervorlage v24 par.8.9b. -->

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

## par.5a STUFE 0 OPERATIONALISIERT, VOR dem Lauf (2026-09-02, 22:55)

Anlass: Nutzer 2026-09-02, *"von der einhuellenden erwart ich mir einiges"*;
mit par.3f (Form A tot) ist Stufe 0 der naechste Schritt und netzfrei bis auf
Vorwaertspaesse.

**Werkzeug:** `tools/probes/envelope_head_discrimination_probe.py`.
Zustaende `frozen_eval_set_v3.pkl` (b01-Aera, 360 je Runde), Netze als ONNX:
`v23-b01_brierbest` (spaltenfaehig), `v22-b05` (Vorgaenger), `v18_2d`
(plattenblind, Referenz). Je Zustand und Brett: Belegung aus `dome_grid`,
Huellen-Orientierung bestpassend (HULL_LEFT r+c<=5 oder HULL_RIGHT r>=c,
kleinere Abweichung; leeres Brett: Vereinigung beider), Ownership-Kopf
(36 Werte je Seite, Sigmoid). **Messgroesse:** AUC von P(belegt) unter den
OFFENEN Zellen, innen gegen aussen, je Runde gemittelt ueber die Bretter;
Block-SE ueber die Quelldateien der frozen-Records; dazu die Mittelwerte
innen/aussen.

**Lesart, vorab festgelegt (Praezisierung von par.5 "hoch"):**
- AUC >= 0,75 in Runde 1 UND 2 beim spaltenfaehigen b01: der Kopf kennt die
  Geometrie bereits -- Baustein (b) (Huellen-Ebenen als Eingabe) ist
  gegenstandslos, der Strang geht direkt zu (c), dem rundenabklingenden
  Gelaender in Suche und Tiling (par.3b/3d), und zur Formwahl B/C.
- AUC <= 0,60 in Runde 1-2: die Geometrie fehlt dem Kopf, (b) bleibt Stufe 1.
- dazwischen: teilweise; (b) und (c) bleiben beide auf dem Plan, Reihenfolge
  nach par.3d (iv).
- Kontrolle: liegt v18_2d (plattenblind) in derselben Hoehe wie b01, misst
  die AUC nur Brettgeometrie (offene Zellen liegen bei fruehen Brettern fast
  alle innen oder aussen), nicht Gelerntes -- dann ist die Groesse als
  Stufe-0-Mass untauglich und wird als solche registriert.

## par.5b STUFE 0 GEMESSEN, ERSTFASSUNG MIT FALSCHER ZWEITER HUELLE (2026-09-03, 00:41; berichtigt in par.5c)

**Diese Tabelle ist ueberholt:** sie wurde mit `HULL_RIGHT = r >= c` gerechnet
(Reihen-Spiegelung), die Quelle definiert `r <= c` (Spalten-Spiegelung);
Nutzer-Frage "unterscheidet es linke und rechte Huelle?" hat es aufgedeckt.
Mit der falschen Huelle war die Vereinigung beider Orientierungen fast das
ganze Brett, weshalb in Runde 1 nur 190 Bretter zaehlbar waren. Gueltig ist
par.5c. Der Text bleibt als Erstfassung stehen.

### Erstfassung (falsche zweite Huelle)

`evaluations/artifacts/envelope_head_discrimination.json` (48 s, frozen_v3,
1.800 Zustaende; 539 Bretter je Netz ohne beide Klassen, meist leere oder
volle Bretter, ausgelassen):

| Runde | Bretter | b01 AUC (Block-SE) | b05 AUC | v18_2d AUC (plattenblind) | b01 P(belegt) innen / aussen |
| --- | --- | --- | --- | --- | --- |
| 1 | 190 | **0,728** (0,016) | 0,746 | 0,607 (0,027) | 0,66 / 0,42 |
| 2 | 711 | **0,850** (0,008) | 0,853 | 0,526 | 0,66 / 0,35 |
| 3 | 720 | 0,775 (0,009) | 0,769 | 0,571 | 0,54 / 0,29 |
| 4 | 720 | 0,771 (0,006) | 0,757 | 0,562 | 0,40 / 0,17 |
| 5 | 720 | 0,713 (0,007) | 0,709 | 0,549 | 0,24 / 0,09 |

**Kontrolle bestanden:** das plattenblinde v18_2d liegt bei 0,53-0,61 mit
P(belegt) rund 0,50 auf beiden Seiten -- sein Ownership-Kopf ist
uninformativ, die AUC misst also Gelerntes, nicht Brettgeometrie.

**Verdikt nach par.5a:** Runde 2 liegt mit 0,850 klar ueber 0,75, Runde 1 mit
0,728 knapp darunter (Block-SE 0,016, also nicht signifikant unter der
Schwelle, aber auch nicht darueber). Formal "dazwischen": (b) und (c)
bleiben auf dem Plan. Inhaltlich ist das Bild eindeutig genug, um die
Reihenfolge zu setzen: **der Kopf kennt die Huelle** -- er gibt Zellen
innerhalb der Dreiecks-Huelle ab Runde 2 rund die doppelte
Belegungswahrscheinlichkeit wie Zellen ausserhalb, und zwar bei b05 genauso
wie bei b01 (das Wissen kam mit der Spalten-Linie, nicht erst mit v23).
Damit ist Baustein (b) (Huellen-Ebenen als Eingabe) der schwaechere Hebel:
was fehlt, ist nicht die Geometrie, sondern dass sie in Suche und Tiling
ZAEHLT -- also Baustein (c), das rundenabklingende Gelaender, mit Formwahl
B oder C aus par.3f. (b) bleibt registriert fuer den Fall, dass (c) an
Runde 1 scheitert, wo die Trennung am schwaechsten ist.

**Naechster Schritt (Stufe 2 vorgezogen vor Stufe 1):** Registrierung des
Gelaenders als Potentialform mit Stuetzstellen nach par.3d (ii), Formwahl B
oder C, Paritaets-Gate, dann Arena. Das ist ein Bau und braucht eine eigene
Registrierung vor dem ersten Handgriff.

## par.5c STUFE 0 MIT BERICHTIGTER HUELLE: der Kopf kennt die Huelle schon in Runde 1 (2026-09-03, 01:00)

`evaluations/artifacts/envelope_head_discrimination_v2.json`; zweite Huelle
`r <= c` (heuristic_v2.rs `triangle_deviation`, Stand 65b48af^, Zeilen
507-508), Orientierung je Brett bestpassend, dazu die AUC je Orientierung.

| Runde | Bretter | b01 AUC (Block-SE) | b05 | v18_2d | Orientierung (links / rechts / gleich / leer) | b01 AUC links / rechts |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 472 | **0,899** (0,009) | 0,910 | 0,522 | 29 / 1 / 50 / 640 | 0,886 / (n=1) |
| 2 | 711 | **0,851** (0,007) | 0,852 | 0,523 | 369 / 27 / 324 / 0 | 0,858 / 0,699 |
| 3 | 720 | 0,795 (0,009) | 0,786 | 0,557 | 552 / 66 / 102 | 0,804 / 0,789 |
| 4 | 720 | 0,796 (0,005) | 0,781 | 0,541 | 578 / 77 / 65 | 0,805 / 0,791 |
| 5 | 720 | 0,732 (0,006) | 0,724 | 0,527 | 563 / 125 / 32 | 0,735 / 0,733 |

**Verdikt nach par.5a, jetzt eindeutig:** AUC 0,90 in Runde 1 und 0,85 in
Runde 2, beide ueber 0,75, Kontrolle plattenblind bei 0,52. **Der
Ownership-Kopf kennt die Huelle von der ersten Runde an**, bei b05 wie bei
b01. Auch die rechte Huelle: sobald ein Brett sie erkennbar macht (ab Runde
3, 66 bis 125 Bretter), trennt der Kopf dort genauso (0,79 gegen 0,80); in
Runde 2 mit 27 Brettern schwaecher (0,70). Rechts-orientierte Bretter sind
in dieser Aera selten (17 Prozent in Runde 5): die Handheuristik der
Startkuppel und die Linie bauen ueberwiegend links.

**Folge fuer den Stufenplan:** Baustein (b) (Huellen-Ebenen als Eingabe) ist
nach der vorab festgelegten Lesart GEGENSTANDSLOS -- dem Netz fehlt nicht
die Geometrie, sondern ihre Bewertung. Der Strang geht direkt zu Baustein
(c), dem rundenabklingenden Gelaender in Suche und Tiling, mit Formwahl B
oder C (par.3f). Stufe 1 entfaellt, Stufe 2 wird die naechste Registrierung.

**Nebenfund mit Reichweite:** die falsche zweite Huelle steckte seit dem
2026-08-29 in `tools/probes/triangle_hull_coverage_probe.py` und damit in
den Stufe-D2-Zahlen der Lehrer-Prereg (kosten-gewichtete Huelle Mensch
0,838, Lehrer 0,600, b04 0,573, b06 0,620) und in `hull_coverage_server_logs`.
Betroffen sind nur Bretter, deren bestpassende Orientierung rechts ist;
Neurechnung fuer Lehrer und Mensch-Logs laeuft, b04r2 und b06 liegen nicht
mehr im Baum (Berichtigung in `PREREG_heuristic_v2_long_rows.md`).


## par.8.6 VORSCHLAG (zu bestaetigen): der Value-Anteil im Tiling wird Form B in Punkteeinheiten (Nutzer 2026-09-03: "die momentane implementierung des value heads im tiling ist schwach")

Heute (par.3f): `Punkte * P(Sieg)` unter den Top-12, faktisch ein
Stichentscheid unter Punktgleichen, weil P(Sieg) unter den Kandidaten nur
0,02 bis 0,07 streut. Das ist Form A, und sie ist tot. par.3d (i) verlangt B
(additiv auf angeglichener Skala) oder C (lexikografisch mit Toleranzband).
Die angeglichene Skala gibt es seit `saturating_score_utility` par.6b ohne
neuen Kopf: die **Margen-Vorhersage in Punkten**,
`M(s) = 50 * atanh(p_own(s)) - 50 * atanh(p_opp(s))` aus Punkte- und
Gegnerpunkte-Kopf (Steigung 0,97 auf Plattenpunkten), ausgewertet am
Endzustand jedes Tiling-Kandidaten -- derselbe Forward-Pass, der heute
P(Sieg) liefert.

**Vorgeschlagene Tiling-Zielfunktion in Runde 1-4 (ersetzt 8.3 und den
Stichentscheid):**

```
score(k) = Punkte(k) + W_TILE * w_e(r) * dH_kosten(k) + W_VAL * w_v(r) * M(k)
w_v(r)   = 1 - w_e(r)                        # gegenlaeufig, par.3c; Profil bleibt
```

- Alle drei Terme in Punkten: Sofortpunkte des Abschlusses, Huellen-Gewinn
  (in Kosteneinheiten, per `W_TILE` in Punkte uebersetzt), vorhergesagte
  Endmarge nach dem Abschluss. `W_VAL = 1` heisst: ein vorhergesagter
  Endpunkt zaehlt wie ein sofortiger; Arme **0,5 / 1,0**.
- Profil unveraendert (Nutzer): `w_e` aus der Verlaesslichkeit des
  Value-Kopfs (par.8.5), `w_v` sein Komplement. In Runde 1 fuehrt die
  Geometrie (w_v 0), in Runde 4 die Vorhersage (w_v 0,67), in Runde 5
  rechnet der Loeser exakt (beide 0).
- Der multiplikative Stichentscheid `NET_TILING_TIEBREAK_ENABLED` wird bei
  `W_VAL > 0` nicht mehr gebraucht und uebersprungen; bei `W_VAL = 0` und
  `W_TILE = 0` bleibt der Bestandspfad bitgleich.
- Knopf `MOSAIC_ENVELOPE_TILING_VALUE_W` (= `W_VAL`), Default 0.
- Was M NICHT kann: Streuung. Das ist derselbe bedingte Folgearm wie bei
  K1 (sigma-Kopf), nicht Voraussetzung.

**Messung:** ein zusaetzlicher Arm **V** (nur `W_VAL`, ohne Huelle) neben S,
T, S+T aus 8.4, plus **T+V** als gemeinsamer Tiling-Arm; dieselben
Instrumente und Verdikte. Damit trennt der Zuschnitt, ob im Tiling die
Geometrie, die Margen-Vorhersage oder beides traegt.

**Vorpruefung, PFLICHT vor dem Bau (Nutzer-Einwand 2026-09-03):** die
Schwaeche der Form A war nicht die Skala allein, sondern die Streuung --
P(Sieg) liegt unter den zwoelf Abschluessen derselben Stellung nur 0,02 bis
0,07 auseinander (par.3f), weil alle zwoelf dieselbe Partie fortsetzen. Ob
die Margen-Vorhersage `M(k)` unter denselben zwoelf Kandidaten um MEHR als
einen Punkt streut, ist ungemessen. Deshalb vorab: `tools/tiling_candidate_
spread.py` um die Marge aus Punkte- und Gegnerpunkte-Kopf erweitern (Ausgaben
3 und 6 des Netzes, Ruecktransformation `50 * atanh`) und auf frozen_v1 und
frozen_v3 mit b01 messen: Median und IQR der Spreizung von `M` unter den
Top-12, und wie oft `Punkte + M` einen anderen Kandidaten waehlt als `Punkte`
allein (echte Kippungen eines Punktvorsprungs, wie in par.3f gezaehlt).
**Lesart vorab:** Median-Spreizung von `M` unter 1 Punkt heisst, Form B in
Punkteeinheiten ist ebenso ein Stichentscheid wie Form A -- dann bleibt fuer
den Value im Tiling nur Form C (lexikografisch mit Toleranzband) oder der
Verzicht, und 8.6 wird nicht gebaut. Spreizung von mehreren Punkten heisst,
der Term kann Punktvorspruenge kippen, und 8.6 geht in den Bau.

**Vorpruefung GEFAHREN (2026-09-03, `tiling_candidate_spread_b01_{v1,v3}_margin.json`,
Werkzeug um `margin_batch` erweitert): BESTANDEN.**

| Satz | Stellungen R2-4 | Spreizung M unter Top-12, Median [IQR] | `Punkte + M` kippt Punktvorsprung | zum Vergleich: P(Sieg)-Spreizung, Kippungen |
| --- | --- | --- | --- | --- |
| frozen_v1 | 142 | **6,8 Punkte** [2,9; 12,0], Max 53 | **22 von 142** (Median 1 Punkt) | 0,048, 1 von 142 |
| frozen_v3 | 192 | **9,9 Punkte** [5,0; 15,7], Max 61 | **25 von 192** (Median 1 Punkt) | 0,065, 4 von 192 |

Die Margen-Vorhersage streut unter denselben zwoelf Abschluessen um 7 bis 10
Punkte, waehrend P(Sieg) um 0,05 streut -- derselbe Forward-Pass, zwei Koepfe,
und nur einer davon unterscheidet die Kandidaten. `Punkte + M` waehlt in 13
bis 15 Prozent der Stellungen einen anderen Abschluss als die Sofortpunkte
allein und kippt dabei Vorspruenge von typischerweise einem Punkt; das ist
die Grössenordnung, in der ein Tiling-Term ueberhaupt wirken kann. Form B in
Punkteeinheiten ist damit KEIN Stichentscheid, sondern ein Entscheider, und
8.6 ist bauwuerdig. (Nebenbefund zur Nutzer-These: der Value-Kopf sieht die
Kandidaten nicht auseinander, der Punkte-Kopf schon -- der Massstab, nicht
das Sehen.)

**Status: ENTSCHIEDEN (Nutzer 2026-09-03, 16:50: "Mach das so").** Gebaut
als Knopf `MOSAIC_ENVELOPE_TILING_VALUE_W` (= `W_VAL`, Default 0, Spec-
Pflichtfeld `envelope_tiling_value_w`), zusaetzlich zu 8.3 (nicht statt):
`score(k) = Punkte + W_TILE * w_e * dH + W_VAL * (1 - w_e) * M(k)`, `M(k)`
aus `self_play::net_tiling_margin_value` (Punkte- und Gegnerpunkte-Kopf am
Endzustand des Kandidaten, `50 * atanh`, ein Vorwaertspass je Kandidat),
Runde 1-4, bei `W_VAL > 0` ohne multiplikativen Stichentscheid. Arme: **V**
(`W_VAL` 0,5 / 1,0, `W_TILE` 0) und **T+V** (`W_TILE` 1,0 mit `W_VAL` 1,0);
Instrumente und Verdikte wie 8.4. Messung nach der K3-Kette (S/T/S+T) und
der K1-Champion-Kante.

## par.8 BAU-ABSATZ K3 fuer v24: das Gelaender in Suche (e) und Tiling (d), Stufe 2 vorgezogen (registriert 2026-09-03, VOR dem Bau)

Kontext: `PREREG_v24_window.md` par.8, Such-Knopf K3; Stufe 0 (par.5c) hat
Baustein (b) erledigt, par.3f die Formfrage (A tot). Dieser Absatz legt
fest, was gebaut wird, bevor ein Handgriff passiert. Zwei Werte sind
Vorschlaege und als Nutzer-Entscheid markiert (par.8.5).

### 8.1 Die Groesse, die das Gelaender liest

`H(brett)` = kosten-gewichteter Huellen-Fuellanteil in [0, 1]: Summe der
Zeilengewichte `r + 1` ueber die belegten Zellen INNERHALB der bestpassenden
Huelle, geteilt durch 56 (Gesamtkost einer Huelle), MINUS Summe der
Zeilengewichte der belegten Zellen AUSSERHALB, geteilt durch 56. Beide
Orientierungen (`r + c <= 5` und `r <= c`, par.5c-Berichtigung), die mit der
kleineren Abweichung zaehlt; leeres Brett: `H = 0`. Das ist die Leitkennzahl
der Einhuellenden (Lehrer-Prereg par.3b.14: Lehrer 0,68, Mensch 0,86), in
der Engine neu als `envelope.rs` mit denselben Definitionen wie die
Python-Sonde und einem Paritaetstest gegen deren Zahlen auf drei Brettern.

### 8.2 (e) Such-Eingriff: Potential am Blattwert, zero-sum, abklingend

Bauform wie die bestehenden Blatt-Additive (`floor_shaping`,
`long_row_init_shaping_w`, net_mcts.rs:1885-1920): eine reine
Zustandsfunktion, die am netzbewerteten Blatt addiert wird, Nullsumme
zwischen den Spielern, geklammert auf [0, 1], bei Gewicht 0 vollstaendig
uebersprungen (byte-identisch).

```
phi(s)   = w_e(runde(s)) * (H(brett_0) - H(brett_1))          # aus Sicht Spieler 0
shift    = C_HULL * tanh(phi(s))
value_0 += shift ; value_1 -= shift ; beide clamp(0, 1)
```

- Profil `w_e` nach par.3d (ii), als Stuetzstellen im Manifest:
  R1 1,0 / R2 0,75 / R3 0,5 / R4 0,25 / **R5 0** (Pflicht-Auflage par.4.1:
  der exakte Loeser bekommt nichts).
- Potentialform (Pflicht-Auflage par.4.2): `phi` haengt nur vom Zustand ab,
  nicht vom Zug; die Differenz zur Wurzel ist das, was die Suche sieht. Das
  ist die Form, in der dieses Projekt seine Shaping-Terme baut; dass sie in
  einer SUCHE nicht dieselbe Politik-Erhaltung garantiert wie PBRS auf
  Returns, ist eine Herleitung und wird als Vorbehalt registriert -- deshalb
  entscheidet die Arena, nicht die Theorie.
- Knopf `MOSAIC_ENVELOPE_SEARCH_C` (= `C_HULL`), Default **0.0 = aus**;
  Profil `MOSAIC_ENVELOPE_PROFILE` als fuenf Kommazahlen, Default
  `1,0.75,0.5,0.25,0`. Beide in `SearchConfig::from_env`, Knopf-Registratur,
  `engine_config` des Manifests.
- Arme: `C_HULL` **0,1 / 0,2** (Groessenordnung des Floor-Terms 0,3 und der
  K1-Zuschlaege; eine volle Huellen-Differenz bewegt den Blattwert dann um
  hoechstens 0,1 bzw. 0,2).

### 8.3 (d) Tiling-Eingriff: Huellen-Gewinn neben den Sofortpunkten

Ort: `best_first_step_exact_or_valued` (tiling_solver.rs:1388-1400), als
neuer Zweig vor dem Netz-Stichentscheid, Runden 1-4, Bauform wie Task #100
(`best_first_step_plate_valued`: Punkte plus gewichtete Zusatzgroesse, dann
Argmax):

```
score(kandidat) = punkte(kandidat) + W_TILE * w_e(runde) * dH_kosten(kandidat)
dH_kosten       = Summe (r+1) der NEU gefuellten Zellen innerhalb der Huelle
                  - Summe (r+1) der NEU gefuellten Zellen ausserhalb
```

- `dH_kosten` ist in Zellenkosten-Einheiten (eine Zelle der Zeile 6 kostet 6,
  der Zeile 1 kostet 1); `W_TILE` uebersetzt Kosten in Punkte-Aequivalente.
- Knopf `MOSAIC_ENVELOPE_TILING_W` (= `W_TILE`), Default **0.0 = aus**
  (dann Bestandspfad, byte-identisch); Arme **0,5 / 1,0** Punkte je
  Kosteneinheit.
- **Reihenfolge gegenueber dem Netz-Stichentscheid (Nutzer-Hinweis
  2026-09-03):** heute waehlt `NET_TILING_TIEBREAK_ENABLED` in Runde 2-4 unter
  den Top-12 nach `Punkte * P(Sieg)` (Modus 0) bzw. `P(Sieg)` (Modus 1), und
  par.3f hat gemessen, dass das nur ein Stichentscheid unter punktgleichen
  Abschluessen ist. Mit K3 gilt: **zuerst** der huellen-bereinigte Score
  `Punkte + W_TILE * w_e * dH_kosten` (Argmax), **danach** der bestehende
  Stichentscheid nur noch unter Kandidaten mit gleichem bereinigtem Score
  (Modus 0 wird zu `score * P(Sieg)`, Modus 1 bleibt `P(Sieg)`). Der Value-
  Stichentscheid rueckt damit hinter die Geometrie, nicht davor; da der
  Huellen-Term echte Gleichstaende seltener macht, bekommt er weniger zu
  entscheiden -- gewollt, weil er nach par.3f ohnehin nie einen
  Punktvorsprung kippt. Bei `W_TILE = 0` und in Runde 5 ist der Pfad
  bitgleich zum Bestand.
- Der Punkte-Term bleibt in allen Runden (par.3d iii, Default); der
  schaerfere Arm `w_p(R1..R2) = 0` ist ein eigener Arm K3-P0 und wird nur
  gefahren, wenn (d) mit Punkten traegt.

### 8.4 Messung und Verdikt (vorab, par.6)

Drei Arme gegen denselben Traeger ohne Gelaender (`v23-b01_brierbest`, spaeter
das beste v24-Netz): **S** (nur Suche, `C_HULL` 0,1 und 0,2), **T** (nur
Tiling, `W_TILE` 0,5 und 1,0), **S+T** (0,1 mit 1,0). Je Arm:

1. **Primaer:** volle Spalten je Partie und Seite am argmax-Instrument
   @400, 200 Partien, Seed 20260931, gepaart gegen die Kontrolle (Block-SE,
   Bezug b01 0,5150). Das ist Tor 2.
2. **Staerke:** gepaarte Arena, dasselbe Netz mit gegen ohne Gelaender
   (`paired_arena_env_ab --env-name MOSAIC_ENVELOPE_SEARCH_C ...`), 2 x 80,
   Blockgroesse 5, `--log-games`, n >= 150 Paare oder Replikation. Das ist
   der Tausch-Waechter aus der Suchtiefe (mehr Spalten, weniger Siege).
3. **Mechanismus:** kosten-gewichtete Huellen-Abdeckung aus den Logs
   (berichtigte Sonde). Steigen Spalten ohne Huelle, wirkt etwas anderes.
4. Sechs Standard-Kennzahlen, `laufzeit`-Block, Paritaets-Gate vorab: alle
   Knoepfe 0 muessen Golden-Selbsttest und Anker-Invarianz bitgleich lassen.

| Befund | Verdikt |
| --- | --- |
| Spalten signifikant ueber Kontrolle UND Siege nicht signifikant darunter, Huelle steigt | K3 traegt; Kandidat fuer das v24-Erzeugungsrezept (Generator baut spaltenreicher) UND fuer den Spielbetrieb, getrennt zu entscheiden |
| Spalten steigen, Siege fallen signifikant | Tausch, wie bei der Suchtiefe; registrieren, nicht uebernehmen; Profil-Frage (schnelleres Abklingen) als Folgearm |
| Spalten unbewegt | par.7: die geometrische Umgehung traegt den fruehen Engpass nicht, es bleibt die Betrags-Schiene (K1) |
| S traegt, T nicht (oder umgekehrt) | der tragende Baustein geht allein weiter; der andere wird geschlossen |

Kosten: Bau rund 3 bis 4 h (Modul `envelope.rs`, zwei Knoepfe, Profil,
Tests, Wheel, Anker); je Arm rund 25 min argmax plus 30 min Arena;
fuenf Arme rund 5 h CPU.

### 8.5 Offen vor dem ersten Handgriff (Nutzer-Entscheid)

1. ~~**Gewichte**~~ **ENTSCHIEDEN (Nutzer 2026-09-03): `C_HULL` 0,1 / 0,2 und
   `W_TILE` 0,5 / 1,0 bleiben.**
2. ~~**Profil** bestaetigen~~ **ENTSCHIEDEN (Nutzer 2026-09-03): "ich wuerd
   das profil abhaengig machen vom value head."** Also keine Hand-
   Stuetzstellen, sondern eine Regel, die aus der gemessenen
   Verlaesslichkeit des Value-Kopfs je Runde folgt:

   ```
   rho(r)  = Spearman(Value-Kopf, tatsaechliche Endmarge) in Runde r,
             Spieler am Zug, auf frozen_v3 (360 Zustaende je Runde)
   w_e(r)  = (rho(5) - rho(r)) / (rho(5) - rho(1))      # R1 = 1, R5 = 0
   ```

   Gemessen am Traeger `v23-b01_brierbest`
   (`evaluations/artifacts/value_head_reliability_by_round.json`, kein
   Orakel, Bezug ist der echte Ausgang der gespielten Partie):

   | Runde | rho (Value vs Endmarge) | w_e |
   | --- | --- | --- |
   | 1 | 0,143 | **1,00** |
   | 2 | 0,201 | **0,92** |
   | 3 | 0,390 | **0,67** |
   | 4 | 0,641 | **0,33** |
   | 5 | 0,881 | **0** (Auflage par.4.1) |

   Der Kopf traegt frueh fast nichts (0,14 in Runde 1), ab Runde 4 viel
   (0,64) und in Runde 5 fast alles (0,88); das Gelaender tritt genau
   gegenlaeufig zurueck. b05 hat dieselbe Kurve (0,17 / 0,17 / 0,37 / 0,65 /
   0,84), die Form ist also eine Eigenschaft der Linie, nicht eines
   Checkpoints. **Regel:** das Profil wird JE TRAEGER aus dieser Messung neu
   berechnet (ein Lauf, unter einer Minute), steht als fuenf Zahlen in
   `MOSAIC_ENVELOPE_PROFILE` und damit im Manifest; ein Hand-Profil ist kein
   Default mehr. **Vorbehalt, registriert:** die niedrige Korrelation in
   Runde 1-2 misst teils echte Spielunsicherheit, nicht nur Kopfschwaeche;
   fuer den Zweck des Gelaenders (dort fuehren, wo der Kopf nicht traegt) ist
   das dieselbe Sache.

   Damit ist K3 vollstaendig baureif; kein Punkt dieses Absatzes ist mehr
   offen.

## par.8.7 K3-P: das Potential auf dem PROJIZIERTEN Brett (Nutzer 2026-09-03, 21:00: "die Huelle wird kommen ... hast du noch nicht den richtigen Hebel gefunden")

**Warum (e) nichts bewegt hat (strukturell, am Code geprueft) -- und was
das NICHT heisst:** Das Drafting legt fest, was dem Tiling zur Verfuegung
steht (Nutzer 2026-09-03); dort wird die Huelle entschieden. `H(brett)` in
par.8.1 liest aber nur die BELEGTEN Zellen des Kuppelrasters
(`envelope::occupancy`, `DomeSpace::is_filled`). Zellen werden nur in der Tiling-Phase gefuellt
(`DomeGrid::place_tile`, aufgerufen aus dem Tiling); waehrend des Draftings
wandern Steine in die MUSTERREIHEN, das Raster bleibt gleich. Ein Suchbaum
ueber Draft-Zuege sieht also an allen Blaettern dasselbe `H0 - H1` (bis auf
Blaetter jenseits des Rundenendes), das Potential ist im Baum konstant und
die Selektion sieht nichts davon -- gemessen in par.9: S 0,1 in allen 160
Partien mit demselben Sieger wie die Kontrolle. Das ist kein Nullbefund der
Huelle, sondern der falsche Hebel (dieselbe Lehre wie B1 bei den langen
Reihen: Initiierung erzwingbar, Vollendung nicht -- hier: das Raster ist
das Ergebnis, die Musterreihen sind die Entscheidung).

**Der Hebel:** dieselbe Groesse auf dem projizierten Brett. Musterreihe `r`
mit Farbe `c` und `k` von `r + 1` Steinen landet beim Tiling in Rasterzeile
`r`, in einer Zelle, die `c` annimmt (`DomeSpace::accepts`: Normal mit
`required_color == c` oder Wild, leer, nicht gesperrt). Projektion:

```
occ_proj(r, c') = 1                             fuer belegte Zellen
                = (k / (r + 1)) / n             fuer jede der n annehmenden Zellen der Reihe r
                                                (Musterreihe r nicht leer, Farbe c, n >= 1)
H_proj          = H nach par.8.1 ueber occ_proj (gebrochene Belegung: Abweichung
                  Summe |Huelle - occ|, Anteile Summe occ * (r + 1) / 56)
```

Ein Draft-Zug, der eine Reihe innerhalb der Huelle beginnt oder fuellt,
hebt `H_proj` sofort um `(k/(r+1)) * (r+1)/56 = k/56` je Stein (bei n = 1);
ausserhalb senkt er es. Das Potential aendert sich also mit JEDEM Draft-Zug,
und die Differenz zur Wurzel ist genau der Beitrag des Zugs zur Huelle.

**Bau:** `envelope::projected_occupancy`/`envelope_score_projected`, Schalter
`MOSAIC_ENVELOPE_PROJECTED=1` (prozessweit, OnceLock; unkritisch fuer den
Spiegelmatch, weil der Term je Seite ueber `envelope_search_c` aus der
SearchConfig gegated ist -- die Kontrollseite mit `c = 0` sieht ihn nie),
der Such-Term (e) rechnet dann `H_proj` statt `H`. Der Tiling-Term (d)
bleibt auf dem Raster (dort ist die Projektion ohnehin realisiert).
Default 0 = Bestand (byte-identisch), Paritaets-Gate wie par.8.4.

**Arme (vorab):** `C_HULL` **0,2 / 0,5 / 1,0** mit `MOSAIC_ENVELOPE_PROJECTED=1`,
Profil unveraendert. Groessenordnung: ein Stein bewegt `H_proj` um 1/56 =
0,018, eine ganze Reihe 5 um 0,09; bei `C = 0,5` ergibt eine Reihe innerhalb
gegen ausserhalb der Huelle rund 0,09 Blattwert -- die Groesse einer
Spalte im K1-Term. Instrumente und Verdikte wie par.8.4; primaer das
argmax-Spaltenprofil (b01 0,515), dazu Huellen-Deckung H und Runden-1/2-
Stabilitaet (Nutzer-Ziel: "die ersten Runden stabiler") als H am Ende von
Runde 2 aus den Arena-Logs.

## par.8.8 K3-B: die Huelle als Vorzugsschicht, inklusive Kuppelplatten (Nutzer 2026-09-03, 21:15: "Werden die Kuppelplatten entsprechend gelegt, um die Huelle zu unterstuetzen?")

**Antwort auf die Frage: bisher NEIN.** K3 (par.8.2/8.3) und K3-P (par.8.7)
lassen die Kuppelplatten-Wahl unberuehrt; sie wirkt nur mittelbar (eine
Platte in der Huelle schafft annehmende Zielzellen, die H_proj heben). Die
Maschinerie fuer eine direkte Lenkung gibt es aber seit dem Plattenbauer
(`plate_builder.rs`, Nutzer-Vorgabe 2026-08-24: "die notwendigen/
vorteilhaften kuppelplatten sollten dann ebenfalls dementsprechend gelegt
werden"): `dome_preference_for_cells_weighted` bewertet Slot und Rotation
einer Platte danach, welche ihrer vier Zellen in der Zielmenge liegen, wie
die Zielkarte sie gewichtet und ob die geforderte Farbe zur Farbe der
zugehoerigen Musterreihe passt (`column_build::cell_value`, Jackpot bei
Uebereinstimmung). Dasselbe fuer Draft (`preference_move_for_cells_weighted`)
und Tiling (`tiling_preference_for_cells_weighted`).

**Bau: `MOSAIC_PLATTENBAU=8` = Huellen-Bauer.** Zielmenge = die 21 Zellen der
bestpassenden Dreiecks-Huelle (Orientierung per Kostenvergleich der beiden
Kandidaten wie bei jedem Bauer, `target_index_generic`, Seed-Streuung bei
Gleichstand), Zielkarte = Zellenkosten `r + 1` (par.8.1: Zeile 5 zaehlt
sechsfach). Alle drei Vorzuege ueber die generische Zellen-Mechanik, kein
neuer Code in den Bewertungen. Wie jeder Bauer ist das eine
UEBERSTEUERUNG des Netzzugs, wo der Bauer einen Vorschlag hat (Runde 1-4),
kein Blattwert-Term -- das ist bewusst die Bauform des hv2-Lehrers, dessen
Huelle 0,68 Deckung erreicht (Lehrer-Prereg par.3b.14).

**Messung (vorab):** prozessweiter Knopf, also NICHT Netz-gegen-Netz im
selben Prozess (Spiegel). Instrumente: (1) argmax-Profil @400, 200 Partien,
Seed 20260931 (b01 0,515 volle Spalten, H am Ende rund 0,49 in der Arena):
volle Spalten, Huellen-Deckung H am Ende und **nach Runde 2** (Nutzer-Ziel:
stabile fruehe Runden), Punkte; (2) Staerke gegen `Heuristik_hv1_anchor`@150
per `net_arena_match` (die Heuristik-Seite kennt den Bauer nicht) mit und
ohne Bauer, gleiche Seeds, 2 x 80, Blockgroesse 5; (3) als Generator-Frage:
liefert der Bauer ein Korpus, das dem Netz die Huelle beibringt -- das ist
die Frage von v24 (Arm b02/b03 der v24-Prereg), nicht dieser Messung.
Verdikt wie par.8.4; zusaetzlich: steigt H nach Runde 2 signifikant ohne
Punktverlust, ist der Bauer der Kandidat fuer die v24-Erzeugung
("stabilere erste Runden"), auch wenn die Spalten unbewegt bleiben.

Reihenfolge: K3-P (par.8.7) und K3-B (par.8.8) werden nach der Nachtkette
gebaut (Wheel-Wechsel waehrend laufender Laeufe ist nicht moeglich) und in
EINEM Bau mit Paritaets-Gate abgenommen; dann Messung beider.

## par.9 GEMESSEN (2026-09-03): K3 in der Bauform par.8.2/8.3 bewegt nichts -- falscher Hebel, nicht falsches Ziel

**Aufbau:** wie par.8.4, am `v23-b01_brierbest` gegen dasselbe Netz mit Spec
"alle Knoepfe 0" (`k1_off.spec.json`), Brett-Tausch per zweitem Lauf, Seed
20261002, 6 Arme x 2 x 80, Blockgroesse 5, `MOSAIC_STACK_DRAW_RESEARCH=1`,
Profil = b01-Kurve (par.8.5). Artefakte `paired_arena_env_k3_b01_{first,second}_s02.json`
(5.523 + rund 5.500 s exklusiv), `k3_b01_swap_eval_s02.json`,
`columns_k3_b01_{first,second}_s02.json`, `tor2a_k3{s01,s02,t05,t10,st}_v23b01.json`
(je rund 1.510 s). Abbruch-Vorfall der zweiten Richtung (Spec-Datei
waehrend des Laufs geaendert): Chronik 17:32, Neustart identisch.

| Arm | Siege Knopf : Basislinie (160 Paare) | diskordant | Margin (Block-SE) | Spalten Arena, Knopf minus Kontrolle (Block-SE) | H Arena (SE) | argmax volle Spalten (b01 0,515) |
| --- | --- | --- | --- | --- | --- | --- |
| S 0,1 | 80 : 80 | **0 / 0** | -0,07 (0,32) | +0,019 (0,019) | +0,005 (0,003) | 0,510 |
| S 0,2 | 78 : 82 | 0 / 2 | -0,29 (0,43) | +0,019 (0,014) | +0,010 (0,003) | 0,525 |
| T 0,5 | 78 : 82 | 5 / 7 | -0,38 (0,85) | -0,031 (0,029) | -0,002 (0,008) | 0,517 |
| T 1,0 | 81 : 79 | 8 / 7 | -0,32 (0,98) | -0,019 (0,032) | 0,000 (0,010) | 0,512 |
| S+T | 81 : 79 | 8 / 7 | -0,67 (1,17) | -0,019 (0,032) | +0,003 (0,011) | 0,505 |

**Verdikt (par.8.4, Zeile 3): Spalten unbewegt, Siege unbewegt, Huelle
unbewegt.** Der Such-Eingriff (e) aendert bei C_HULL 0,1 in KEINER der 160
Partien den Sieger und bei 0,2 in zweien; der Grund ist strukturell (par.8.7):
das Raster fuellt sich nur im Tiling, im Draft-Suchbaum ist H konstant, das
Potential faellt in der Differenz zur Wurzel weg. **Berichtigung (Nutzer
2026-09-03, 21:40): daraus folgt NICHT, dass die Huelle im Drafting
wirkungslos waere -- das Gegenteil gilt: im Drafting wird festgelegt, was
dem Tiling zur Verfuegung steht (welche Farbe in welcher Musterreihe, also
welche Rasterzelle ueberhaupt erreichbar wird). Wirkungslos war der
MESSFUEHLER, der nur das Raster las und die Draft-Entscheidung deshalb nicht
sah. Der Hebel gehoert ins Drafting: par.8.7 projiziert die Musterreihen in
H, par.8.8 setzt den Draft-Vorzug direkt auf die Huellenzellen.** Der Tiling-Eingriff (d)
kippt 12-15 von 160 Partien ohne Richtung, weil er nur unter Fast-
Gleichstaenden der Sofortpunkte entscheidet. **Das ist KEIN Verdikt ueber die
Huelle** (Nutzer 2026-09-03: "die Huelle wird kommen ... noch nicht den
richtigen Hebel gefunden"), sondern ueber diese zwei Hebel; die Fortsetzung
sind par.8.7 (Potential auf dem projizierten Brett) und par.8.8 (Huellen-
Bauer mit Kuppel-Vorzug). par.7 ("geometrische Umgehung traegt den fruehen
Engpass nicht") bleibt damit OFFEN, nicht bestaetigt.

### 8.7a ERSTE ZAHLEN K3-P (2026-09-03, 23:25; argmax @400, 200 Partien, Seed 20260931; Staerke folgt)

| Arm | volle Spalten (b01 0,515) | Punkte | Huelle H_end kosten-gew. | Halbzeit H | aussen je Seite | neu in Huelle R1 / R2 | stabil ab R1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Kontrolle (K3 S 0,1 = b01-identisch) | 0,510 | 46,3 | 0,659 | 0,389 | 2,92 | 0,978 / 0,905 | 0,92 |
| K3-P C 0,2 | 0,455 | 46,3 | 0,665 | 0,413 | 2,65 | 0,991 / 0,936 | 0,94 |
| K3-P C 0,5 | 0,480 | 47,7 | 0,687 | 0,432 | 2,38 | 0,987 / 0,965 | 0,94 |
| **K3-P C 1,0** | **0,555** | **47,7** | **0,703** | **0,444** | **2,15** | 0,999 / 0,984 | 0,95 |
| Huellen-Bauer (par.8.8) | 0,275 | 40,4 | 0,677 | 0,398 | 2,27 | 0,940 / 0,873 | 0,54 |

Artefakte `tor2a_k3p{02,05,10}_v23b01.json`, `tor2a_k3b_v23b01.json`,
`triangle_hull_coverage_tor2a-*.json`. Lesart vorlaeufig: das projizierte
Potential bewegt die Huelle monoton mit C (Ende +0,044, Halbzeit +0,055,
Runde-2-Neusteine in der Huelle 0,905 -> 0,984) und kostet weder Spalten noch
Punkte; das ist der erste Hebel dieser Prereg, der in die gewuenschte
Richtung wirkt. Der Huellen-Bauer (8.8) als Uebersteuerung hebt die Huelle
ebenfalls, zerstoert aber Spalten, Punkte und Staerke (gegen hv1@150 von
131:29 auf 68:92) -- als Ersatz des Netzzugs zu grob; die Kuppelplatten-
Lenkung gehoert als Bewertung in die Suche (siehe Erreichbarkeit, 8.9).
Verdikt nach der K3-P-Arena (Kette B Schritt 8).

## par.8.9 K3-R: Erreichbarkeit als dritte Projektion (Nutzer 2026-09-03, 23:30: "und macht Erreichbarkeit nicht ebenfalls Sinn?")

**Ja, und sie ist die Groesse, die das Drafting wirklich entscheidet.** Drei
Projektionen desselben H stehen nebeneinander:

| Projektion | liest | misst | Stand |
| --- | --- | --- | --- |
| Raster (par.8.1/8.2) | belegte Zellen | was schon liegt | im Draft-Suchbaum konstant, wirkungslos (par.9) |
| Musterreihen (par.8.7, K3-P) | belegte + anteilig gebundene Zellen | was das gesammelte Material werden wird | bewegt die Huelle monoton (8.7a) |
| Ownership-Kopf (K3-O, geplant) | 36 gelernte Feldwahrscheinlichkeiten | was das Netz bei seinem Spiel legen WIRD (Eintreten) | Kopf kennt die Huelle ab Runde 1 (par.5c, AUC 0,90) |
| **Erreichbarkeit (K3-R)** | belegte + gebundene + noch VOLLENDBARE Zellen | was dem Tiling noch offensteht | berechnetes Praedikat vorhanden (`column_build::cell_is_completable`, `plate_builder::achievable_column_fill`, "Erreichbarkeit als Mass statt als Tor") |

**Bekannte Befunde zur Erreichbarkeit als Ziel:** `reachability_target`
(ENTSCHIEDEN 2026-08-20): der Ownership-Kopf mit Vollendbarkeits-Ziel statt
Endbrett trug nicht (k1 +0,23, Block-t 1,11). `v23_reachability_recheck`
(ENTSCHIEDEN 2026-09-01): der v23-Kopf kartiert 14,6 Prozent der laut
Praedikat vollendbaren Zellen tot, und nur 7 Prozent davon werden doch
gefuellt -- der Kopf ist strenger als das Praedikat und hat recht. Also: als
TRAININGSZIEL war Erreichbarkeit kein Gewinn; als POTENTIAL im Blattwert ist
sie ungemessen, und dort sitzt der Unterschied zum Eintreten: ein Potential
auf "Eintreten" belohnt, was das Netz ohnehin tut; ein Potential auf
"Erreichbarkeit" belohnt, die Huelle OFFEN zu halten -- keine Farbe in
Zeile r zu binden, die dort keine Huellenzelle bedient, und Kuppelplatten so
zu legen, dass Huellenzellen die noch verfuegbaren Farben annehmen. **Das ist
die Bewertungs-Form der Kuppelplatten-Lenkung** (par.8.8 hat sie als
Uebersteuerung versucht und die Staerke zerstoert).

**Bau (vorab):** `occ_reach(r, c)` = 1 belegt; `k/(r+1)/n` gebunden (wie
8.7); fuer leere Huellenzellen ohne gebundene Reihe `w_r`, wenn
`cell_is_completable(player, r, c, verbleibend)` (Kuppelplatte liegt, Farbe
noch im Vorrat, Musterreihe frei oder farbgleich), sonst 0; Zellen ausserhalb
der Huelle nur belegt/gebunden (Erreichbarkeit ausserhalb ist kein Verlust).
`w_r` = 0,25 (eine offene Option zaehlt ein Viertel eines Steins; **ENTSCHIEDEN,
Nutzer 2026-09-03, 23:40: "passt"**; Knopf `MOSAIC_ENVELOPE_REACH_W`). Orientierung:
je Huelle eigene Belegung, H mit fester Orientierung, Maximum der beiden
(die beste noch offene Huelle). GEBAUT 2026-09-03 (`envelope_score_reach`,
`envelope_score_ownership`, `search_shift_state`, Modus 0..3), Bau-Abnahme
und Messung nach Kette B. Schalter `MOSAIC_ENVELOPE_PROJECTED=2`, Arme C 0,5 / 1,0.
Instrumente wie 8.7a plus "tote Huelle Runde 3/4" aus der Sonde
(`tote_huelle_r4_gewichtet_mittel`: heute 0,013).

**K3-O** (Ownership-Projektion, `MOSAIC_ENVELOPE_PROJECTED=3`): `occ_own` =
sigmoid der 36 Ego-Logits, dieselbe H-Rechnung; misst, ob das Netz seine
eigene Vorhersage in die Huelle lenken kann. Beide nach der K3-P-Arena.

### 8.6a GEMESSEN (2026-09-04, 07:00): der Value-Anteil im Tiling bewegt nichts

Aufbau wie 8.4 am `v23-b01_brierbest` gegen Spec aus, Seed 20261005, Arme V
0,5 / V 1,0 / T+V (W_TILE 1,0 + W_VAL 1,0), 2 x 80, Blockgroesse 5; argmax
@400 Seed 20260931. Artefakte `paired_arena_env_k3v_b01_{first,second}_s05.json`,
`k3v_b01_swap_eval_s05.json`, `columns_k3v_b01_*_s05.json`,
`tor2a_k3v{05,10}_v23b01.json`, `tor2a_k3tv_v23b01.json`.

| Arm | Siege Knopf : Basislinie | diskordant, p | Margin (Block-SE) | Spalten Arena (SE) | H Arena (SE) | argmax Spalten (b01 0,515) | Punkte argmax |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V 0,5 | 82 : 78 | 6 / 4, 0,75 | -0,42 (0,56) | -0,019 (0,014) | +0,001 (0,007) | 0,4925 | 46,5 |
| V 1,0 | 84 : 76 | 8 / 4, 0,39 | +0,19 (0,66) | -0,006 (0,017) | -0,001 (0,007) | 0,485 | 46,6 |
| T+V | 80 : 80 | 9 / 9, 1,00 | -0,52 (0,76) | 0,000 (0,024) | +0,021 (0,010) | 0,4975 | 47,0 |

**Verdikt:** Nullbefund in allen Groessen; der Term kippt 10-18 von 160
Partien ohne Richtung. Die Vorpruefung (Spreizung 7-10 Punkte) hat gezeigt,
dass die Marge die Kandidaten UNTERSCHEIDET -- die Wahl nach ihr fuehrt aber
zu keinem anderen Ergebnis als die Sofortpunkte. Im Tiling ist zu wenig zu
entscheiden (par.3f: Fast-Gleichstaende), und der Entscheid liegt im Draft.
8.6 bleibt gebaut (Default 0) und geht nicht ins Rezept.

### 8.7b K3-P ARENA (2026-09-04, 04:12-07:00; Seed 20261007, 3 Arme x 2 x 80, Blockgroesse 5, gegen Spec aus)

| Arm | Siege Knopf : Basislinie (160 Paare) | diskordant, McNemar p | Block-Diff Siege (SE, t) | Punkte Knopf (Kontrolle 48,3) | Margin (Block-SE) | Spalten Arena, Knopf minus Kontrolle (SE) | H Arena (SE) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C 0,2 | 88 : 72 | 36 / 28, 0,38 | +0,050 (0,047; 1,07) | 48,6 | +1,51 (1,97) | +0,062 (0,068) | +0,002 (0,019) |
| C 0,5 | 92 : 68 | 44 / 32, 0,21 | +0,075 (0,054; 1,40) | 51,6 | +3,35 (2,33) | +0,111 (0,066) | **+0,077 (0,022)** |
| C 1,0 | 95 : 65 | 45 / 30, 0,11 | +0,094 (0,057; 1,65) | 50,1 | +3,23 (2,04) | +0,102 (0,060) | **+0,102 (0,017)** |

Artefakte `paired_arena_env_k3p_b01_{first,second}_s07.json`,
`k3p_b01_swap_eval_s07.json`, `columns_k3p_b01_{first,second}_s07.json`.

**Lesart (vorlaeufig, gegen 8.4):** alle drei Groessen zeigen in dieselbe
Richtung und wachsen mit C: Siege +8 / +12 / +15 von 160 (einzeln nicht
signifikant, monoton), Margin +1,5 / +3,4 / +3,2, Spalten in der Arena
+0,06 / +0,11 / +0,10 (t 0,9-1,7), Huelle in der Arena +0,08 / +0,10 bei
C 0,5 / 1,0 (t 3,5 und 6,2) -- zusammen mit 8.7a (argmax: Huelle +0,044,
Spalten 0,555, Punkte +0,9 bei C 1,0). Das ist der erste Hebel dieser Prereg,
bei dem Huelle, Spalten, Punkte und Siege gemeinsam steigen. Fuer Zeile 1
der Tabelle fehlt die Signifikanz bei den Siegen: naechster Schritt
Replikation C 1,0 mit eigenem Seed und ein Arm C 2,0 (Monotonie ausreizen),
dazu K3-R/K3-O (Kette C). Kein Tausch: nichts faellt.

### 8.9a GEMESSEN (2026-09-04, 07:05-11:38, Kette C): Erreichbarkeit und Ownership heben die Huelle, kosten aber Spalten oder Punkte -- K3-P bleibt der beste Hebel

Wheel mit K3-R/K3-O (518 Tests gruen), Anker-Drift GRUEN
(`anchor_drift_20260904_k3ro.json`), Netz-Pfad-Paritaet REPRODUZIERT
(`k3ro_net_path_parity_repro.json`). argmax @400, 200 Partien, Seed 20260931
(je rund 1.600 s); Arena Seed 20261008, 4 Arme x 2 x 80 gegen Spec aus
(`paired_arena_env_k3ro_b01_{first,second}_s08.json`, `k3ro_b01_swap_eval_s08.json`,
`columns_k3ro_b01_*_s08.json`); Huellen-Sonden `triangle_hull_coverage_tor2a-k3{r,o}{05,10}-v23b01.json`.

| Arm | Spalten argmax (b01 0,515) | Punkte argmax (46,5) | H_end (0,659) | Halbzeit H (0,389) | aussen (2,92) | Siege (160 Paare) | Margin (SE) | Spalten Arena (SE) | H Arena (SE) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K3-R C 0,5 (w_r 0,25) | 0,492 | 45,5 | 0,674 | 0,416 | 2,48 | 82 : 78 | -0,01 (1,70) | -0,108 (0,107) | +0,038 (0,022) |
| K3-R C 1,0 | **0,393** | 45,0 | 0,683 | 0,434 | 2,19 | 91 : 69 (p 0,25) | +0,02 (2,05) | **-0,138 (0,092)** | +0,072 (0,020) |
| K3-O C 0,5 | 0,475 | **43,9** | 0,660 | 0,400 | 2,68 | 86 : 74 | +1,91 (2,31) | -0,042 (0,094) | +0,022 (0,023) |
| K3-O C 1,0 | 0,470 | **43,9** | 0,665 | 0,413 | 2,56 | 87 : 73 | +1,54 (2,61) | +0,041 (0,104) | +0,037 (0,020) |
| zum Vergleich K3-P C 1,0 (8.7a/b) | **0,555** | **47,7** | **0,703** | **0,444** | **2,15** | 95 : 65 (p 0,11) | +3,23 (2,04) | +0,102 (0,060) | +0,102 (0,017) |

**Lesart:** Die Erreichbarkeits-Projektion hebt die Huelle (Arena +0,07 bei
C 1,0, t 3,6) und die Siege leicht (91:69), kauft das aber mit Spalten
(argmax 0,393, Arena -0,14): das Potential belohnt OFFENE Huellenzellen und
haelt damit Optionen offen, statt sie zu einer Spalte zu verdichten -- das
Gegenteil dessen, was der Engpass "Vollendung" braucht. Die Ownership-
Projektion bewegt die Huelle kaum (+0,001 bis +0,006 am Ende) und kostet
Punkte (43,9): sie belohnt, was das Netz ohnehin erwartet (Eintreten), und
das ist wenig. **K3-P (gebundenes Material projiziert) bleibt der einzige
Hebel, bei dem Huelle, Spalten, Punkte und Siege gemeinsam steigen.**
K3-R und K3-O bleiben gebaut (Modus 2/3, Default 0), gehen nicht weiter.
Naechster Schritt: Kette D (Replikation K3-P C 1,0, Arm C 2,0,
Betriebspunkt @100).

### 8.9b WIEDERVORLAGE v24 (Nutzer 2026-09-04, 13:05: "das Erreichbarkeits-Potential ist noch nicht so implementiert, dass es einen sauberen Effekt generiert -- wird erst mit v24 schlagend")

**Der Konstruktionsfehler von K3-R, am Code abgelesen** (`envelope_score_reach`:
eine leere, vollendbare Huellenzelle bekommt `w_r` NUR, solange
`occ[r][c] == 0`; sobald die Reihe `r` gebunden ist, zaehlt die Zelle
`k/(r+1)/n` und verliert das `w_r`): der ERSTE Stein in Reihe `r` (n = 1)
aendert das Potential um `1/(r+1) - w_r`, bei `w_r = 0,25` also
+0,75 / +0,25 / +0,08 / **0 / -0,05 / -0,08** fuer die Reihen 0..5. Das
Potential BESTRAFT das Beginnen der langen Reihen 4 und 5 innerhalb der
Huelle -- genau der Zellen, die Spalten vollenden. Das erklaert, warum K3-R
die Huelle hebt (Optionen bleiben offen) und die Spalten senkt (argmax 0,393,
Arena -0,14). Erreichbarkeit als eigenstaendige Belohnung honoriert
Optionalitaet; der Engpass "Vollendung" braucht das Gegenteil.

**Was Erreichbarkeit stattdessen leisten kann (drei Bausteine, fuer v24):**

1. **Als Modulator des gebundenen Materials, nicht als Belohnung leerer
   Zellen (K3-P2).** Belohnt wird weiter nur Material, das gebunden ist
   (K3-P). Erreichbarkeit entscheidet, WO es zaehlt: eine gebundene Reihe
   `r`, deren Huellenzellen noch keine Kuppelplatte tragen, zaehlt auf den
   leeren Huellenzellen der Zeile mit `w_slot` (Vorschlag 0,5 -- die
   passende Platte kann noch kommen), statt wie heute 0 (keine annehmende
   Zelle). Damit wird das Beginnen einer Huellenreihe VOR der Platte
   belohnt, und das Legen einer passenden Platte hebt das Potential sofort
   von `w_slot` auf 1 (die Bewertungs-Form der Kuppelplatten-Lenkung, ohne
   Uebersteuerung). Kein Term fuer leere Reihen.
2. **Tote Huellenzellen als Abzug (K3-D).** Eine Huellenzelle, die durch
   eine Platte mit falscher Farbe oder durch den Restvorrat unerfuellbar
   wird (`cell_is_completable == false`), zaehlt `-w_dead * (r+1)/56`.
   Bestraft nur Zerstoerung, belohnt keine Optionalitaet. Heute selten
   (tote Huelle Runde 4 kosten-gewichtet 0,013 bei b01), also klein --
   aber genau der Fall, den eine falsch gelegte Kuppelplatte erzeugt.
3. **Runden-Profil fuer die Erreichbarkeit umkehren.** Offene Optionen
   sind in Runde 1-2 wertvoll und ab Runde 4 wertlos (nichts kommt mehr
   nach); die Vollendung ist es umgekehrt. Falls 1 nicht reicht: `w_slot`
   mit `w_e(r)` abklingen lassen, waehrend der K3-P-Anteil bleibt.

**Warum erst v24:** K3-P (C 1,0) ist der Rezept-Kandidat fuer die
v24-Erzeugung; die Bausteine 1-3 aendern das, was im v24-Korpus steht, und
werden deshalb als v24-ARME registriert (par.8 der v24-Prereg), gemessen
am v24-Netz mit dem v24-Material -- nicht mehr am b01. Bau je Baustein unter
einer Stunde (dieselbe Projektions-Mechanik, Modus 4 und 5), Messung wie
8.7a/8.7b. Nichts davon wird vor dem v24-Start gebaut.

### 8.7c K3-P REPLIKATION C 1,0 (2026-09-04, 11:39-13:15, Kette D; Seed 20261009, Kontrolle / C 1,0 / C 2,0, 2 x 80, Blockgroesse 5, gegen Spec aus)

| Arm | Siege Knopf : Basislinie (160 Paare) | diskordant, p | Block-Diff Siege (SE, t) | Punkte Knopf (45,3) | Margin (SE) | Spalten Arena (SE) | H Arena (SE) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C 1,0 | **96 : 64** | 46 / 30, 0,085 | +0,100 (0,051; 1,97) | 49,4 | +3,74 (2,16) | +0,088 (0,077) | **+0,162 (0,018)** |
| C 2,0 | 88 : 72 | 45 / 37, 0,44 | +0,050 (0,059; 0,85) | 48,4 | +3,38 (2,21) | +0,022 (0,073) | +0,179 (0,015) |

**C 1,0 gepoolt ueber beide Seeds (20261007 + 20261009, 320 Paare): 191 : 129
gegen 160 : 160, diskordant 91 / 60, McNemar p = 0,014, Block-Differenz
+0,097 je Partie (SE 0,038, t 2,54, 64 Bloecke), Margin +3,48 (SE 1,48);
die beiden Seeds sind deckungsgleich (+0,094 und +0,100, z = -0,08).**
Artefakte `paired_arena_env_k3p_b01_{first,second}_s09.json`,
`k3p_b01_swap_eval_s09.json`, `columns_k3p_b01_*_s09.json`.

**Verdikt nach par.8.4, Zeile 1, ERFUELLT fuer K3-P C 1,0:** Siege signifikant
vorn (p = 0,014 auf 320 Paaren, beide Seeds gleich), Spalten NICHT unter der
Kontrolle (Arena +0,10 und +0,09, argmax 0,555 gegen 0,515), Huelle steigt
(Arena +0,10 und +0,16, argmax 0,703 gegen 0,659), Punkte +2 bis +4.
**K3 traegt -- in der Bauform "Potential auf dem projizierten Brett",
C_HULL 1,0, Profil aus dem Value-Kopf.** Kandidat fuer das v24-
Erzeugungsrezept UND fuer den Spielbetrieb (getrennt zu entscheiden, par.8.4);
C 2,0 ist bei den Siegen schwaecher (88:72) bei noch hoeherer Huelle -- die
Monotonie endet zwischen 1,0 und 2,0, C 1,0 bleibt der Arm. Offen vor dem
Rezept: der Betriebspunkt @100 (Kette D Schritt 3) und die Champion-Kante
(Spielbetrieb).

### 8.7d C 2,0 am Instrument und K3-P im ERZEUGUNGS-Betriebspunkt @100 (2026-09-04, 13:15-14:06, Kette D)

| Messung | ohne Knopf | K3-P C 1,0 | K3-P C 2,0 |
| --- | --- | --- | --- |
| argmax @400, 200 Partien, Seed 20260931: volle Spalten | 0,515 | 0,555 | **0,635** (+-0,068; Seiten mit voller Spalte 203 von 400) |
| dito Punkte / volle Reihen | 46,8 / 0,148 | 47,7 / 0,193 | 49,7 / 0,205 |
| dito Huelle H_end / Halbzeit / aussen | 0,659 / 0,389 / 2,92 | 0,703 / 0,444 / 2,15 | 0,731 / 0,463 / 1,83 |
| **Erzeugungs-Betriebspunkt @100** (Pilot-Rezept par.6b, 400 Partien value-argmax, Seed 20260910): volle Spalten | **0,726** (Pilot, v24 par.7) | **0,775** (+-0,055) | -- |
| dito Seiten mit voller Spalte | 403 von 800 (50 %) | **440 von 800 (55 %)** | -- |
| dito Punkte / volle Reihen / Strafleiste | 49,7 / 0,094 / 5,40 | 51,0 / 0,143 / 5,61 | -- |
| dito Huelle H_end / Halbzeit / aussen / neu in Huelle R2 / stabil ab R1 | 0,685 / 0,413 / 2,82 / 0,907 / 0,91 | **0,718 / 0,456 / 2,36 / 0,974 / 0,95** | -- |
| dito Symmetrie-Trennung (Sieger minus Verlierer, Block-Mittel, SE) | +0,512 (0,047) | +0,455 (0,044) | -- |

Artefakte `tor2a_k3p20_v23b01.json`, `triangle_hull_coverage_tor2a-k3p20-v23b01.json`,
`pilot24k3p_sanity_value_argmax.json`, `pilot24k3p_symmetry_value_argmax.json`,
`triangle_hull_coverage_pilot24{,k3p}-value-argmax.json`; Laufzeiten 1.636 s
(argmax) und 1.309 s (400 Partien @100, 3,27 s je Partie, threads 11).

**Lesart:** Am Instrument steigen Spalten und Huelle mit C weiter (C 2,0:
0,635 Spalten, Huelle 0,731), in der Arena sind die Siege bei C 2,0 aber
schwaecher als bei C 1,0 (8.7c) -- fuer den SPIELBETRIEB ist C 1,0 der Arm,
fuer den GENERATOR koennte C 2,0 das spaltenreichere Material liefern; das
ist eine v24-Frage (par.8.9b-Liste), nicht mehr diese Messung. **Im
Erzeugungs-Betriebspunkt @100 haelt der Effekt:** +0,05 Spalten je Seite,
+5 Prozentpunkte Seiten mit voller Spalte, +1,3 Punkte, Huelle +0,033 am
Ende und +0,043 zur Halbzeit, Runde-2-Steine in der Huelle 0,907 -> 0,974,
Orientierung stabil ab Runde 1 0,91 -> 0,95 (Nutzer-Ziel "stabile erste
Runden"). Die Symmetrie-Trennung sinkt leicht (0,51 -> 0,46, innerhalb einer
SE), weil BEIDE Seiten mehr bauen; Tor 0 (Trennung > 0, Seiten mit voller
Spalte > 35 %) bleibt weit erfuellt. **K3-P C 1,0 ist damit
Rezept-Kandidat fuer die v24-Erzeugung** (`PREREG_v24_window.md` par.6a,
Zeile "Knoepfe": `MOSAIC_ENVELOPE_PROJECTED=1`, `MOSAIC_ENVELOPE_SEARCH_C=1.0`
in der Umgebung der Value-Laeufe; ob auch die Sockel-Klasse, ist Nutzer-
Entscheid). Champion-Kante fuer den Spielbetrieb laeuft.

## par.10 CHAMPION-KANTE mit K3-P (Nutzer-Wunsch 2026-09-04, 13:30; gefahren 14:06-14:14)

`tools/paired_gating.py`, `v23-b01_brierbest` mit `MOSAIC_ENVELOPE_PROJECTED=1
MOSAIC_ENVELOPE_SEARCH_C=1.0` (Profil b01-Kurve) gegen `v21_2d_brierbest` mit
Spec "alle Knoepfe 0" (`k3v_off.spec.json`), @400/@400, Blockgroesse 5, SPRT
H1 p = 0,65, Deckel 200 Paare, **Seed 20261004 = Seed der Bezugskante ohne
Knopf** (`saturating_score_utility` par.17: 214:186 nach 200 Paaren).
Artefakt `paired_gating_result_v23-b01_k3p10_vs_v21_2d_brierbest.json`.

| Kante | Ergebnis | Paare | SPRT | Vorzeichentest p | gepaarte Differenz, 95%-KI |
| --- | --- | --- | --- | --- | --- |
| **b01 + K3-P C 1,0 gegen v21** | **38 : 12** | 25 (Fruehstopp, LLR +3,22 > +2,94) | **signifikant besser** | 0,0023 | +1,04 [+0,53, +1,55] |
| b01 ohne Knopf, dieselben ersten 25 Paare | 30 : 20 | 25 | -- | -- | -- |
| b01 ohne Knopf, volle Kante | 214 : 186 | 200 | kein Entscheid | 0,20 | +0,14 [-0,06, +0,34] |
| zum Vergleich b01 + K1 (par.17 dort) | 77 : 83 | 80 | H0 | 0,77 | -0,08 |

Laufzeit 492 s (9,8 s je Partie, threads 10, exklusiv). Informative Paare:
A gewinnt beide 15, B beide 2, geteilt 8.

**Lesart:** die erste Kante, die den Champion SCHLAEGT statt auf Augenhoehe
zu stehen -- allerdings ein Fruehstopp nach 25 Paaren; `promotion_checklist.md`
Punkt 2 verlangt bei Fruehstopp unter 150 Paaren eine Replikations-Zeile
mit eigenem Seed (laeuft: Seed 20261010, Artefakt `..._s10.json`). Erst
danach ist die Kante ein Beleg. **Vor einer Promotion** braeuchte es
ausserdem: den Projektions-Modus als Feld der `SearchConfig`/Spec-Datei
(heute prozessweiter Env-Knopf `MOSAIC_ENVELOPE_PROJECTED`; ein Champion ist
Modell PLUS Spec, und eine Spec muss das Suchverhalten VOLLSTAENDIG
festlegen), die Anker-Kante mit festem n = 150 und die uebrigen Punkte der
Checkliste. Nutzer-Entscheid.

### 10a REPLIKATION der Champion-Kante (2026-09-04, 14:16-15:23, Seed 20261010, Deckel 200 Paare)

| Kante | Ergebnis | Paare | SPRT | Vorzeichentest p | gepaarte Differenz, 95%-KI | Punkte A / B |
| --- | --- | --- | --- | --- | --- | --- |
| b01 + K3-P C 1,0 gegen v21, Seed 20261010 | **221 : 179** (55,3 %) | 200 (Deckel) | kein Entscheid (LLR +1,36) | 0,055 | +0,21 [+0,01, +0,41] | 50,0 / 47,4 |
| dieselbe Kante, Seed 20261004 (par.10) | 38 : 12 | 25 (Fruehstopp) | signifikant | 0,002 | +1,04 | 57,8 / 48,1 |
| **gepoolt, beide Seeds** | **259 : 191 (57,6 %)** | 225 | -- | **0,003** (informativ 80 / 46) | -- | -- |
| Bezug: b01 ohne Knopf gegen v21, Seed 20261004 | 214 : 186 (53,5 %) | 200 | kein Entscheid | 0,20 | +0,14 [-0,06, +0,34] | 50,5 / 47,5 |

Artefakt `paired_gating_result_v23-b01_k3p10_vs_v21_2d_brierbest_s10.json`
(4.150 s, 10,4 s je Partie, threads 10, exklusiv).

**Verdikt:** Der 38:12-Start war eine gluecklich gezogene Stichprobe; mit
eigenem Seed liegt die Kante bei 55 Prozent, das KI der gepaarten Differenz
schliesst die Null knapp aus, und gepoolt ueber 225 Paare ist der Vorsprung
gegen den Champion signifikant (p = 0,003) -- Champion-Strenge (n >= 150
Paare) erfuellt. Gegenueber b01 ohne Knopf (53,5 %) ist der Zuwachs klein
(rund 2 bis 4 Prozentpunkte) und auf dieser Basis nicht getrennt belegbar;
belegt ist: b01 + K3-P schlaegt v21, b01 allein steht auf Augenhoehe.
Fuer das v24-REZEPT reicht das (`PREREG_v24_window.md` par.6b': der Knopf
verbessert das Material und kostet keine Staerke); fuer eine PROMOTION
(Spielbetrieb) bleibt der Nutzer-Entscheid samt Checkliste und dem
Projektions-Modus als Spec-Feld.

## par.11 PROMOTION: `v23-b01_k3p10` ist Champion (Nutzer 2026-09-04, 19:20; abgearbeitet nach `docs/promotion_checklist.md`)

| Schritt | Ergebnis |
| --- | --- |
| Bau | Projektions-Modus als Spec-Pflichtfeld `envelope_projection_mode` (519 Tests gruen, Commit 0e87ddd); Server uebersetzt die Champion-Spec in Env-Knoepfe; Anker-Drift GRUEN, Netz-Pfad-Paritaet REPRODUZIERT (`anchor_drift_20260904_promotion.json`, `promotion_net_path_parity_repro.json`) |
| 1 set_champion | `models/champion.txt`: v21_2d_brierbest -> **v23-b01_k3p10**; Modell = Kopie von b01_brierbest, Spec Modus 1 / C 1,0 / Profil b01-Kurve |
| 2 Gating-Kanten | 38:12 (Seed 20261004, SPRT nach 25 Paaren) und Replikation 221:179 (Seed 20261010, 200 Paare) gegen v21, beide in `elo_history.csv` |
| 3 Anker-Kante | **128:22 gegen Heuristik_hv1_anchor@150** (n=150 fest, Seed-Basis 900001, Cross-Aera; `anchor_arena_v23-b01_k3p10.json`); b01 ohne Knopf: 127:23 |
| 4 Champion-2-Kante | **32:8 gegen v22-b05** (SPRT nach 20 Paaren, p 0,0005, Seed 20261011; `paired_gating_result_v23-b01_k3p10_vs_v22-b05.json`). Abweichung: v20_2d_opp_brierbest liegt nicht im Baum, v22-b05 ist der Elo-Knoten mit zwei Kanten zu b01 |
| Elo | **1292 [1253, 1335]**, alle Knoten mit dem Anker verbunden; v21 1232, b01 ohne Knopf 1263 |
| 5b Anzeige-Kalibrierung | frozen_v3 (Anzeige-Fit): A -0,1080, B 0,5587; frozen_v1 (Trend): B 0,6092, A +0,2678 (`platt_fit_v23-b01_k3p10_frozenv{1,3}.json`); in `server.py` eingetragen |
| 5c sigma/Prior-Balance | Gesamt **2,92** (Schwelle 3 nicht ueberschritten, c_visit/c_scale-Familie bleibt zu); je Runde 2,57 / 2,83 / 3,88 / 2,99 (`gumbel_scale_calibration_v23-b01_k3p10.json`) |
| 5d Paritaets-Fixture | neu erzeugt, Hash `a274e3ad68f4ad91`, im frischen Prozess gruen |
| Artefakt | `models/frozen_champions/v23-b01_k3p10/` mit model.onnx/.pth, spec.json, Wheel `mosaic_rust_k3p_20260904.whl`; Golden Probe (Tool `build_frozen_golden_probe.py`, Seed-Basis 916001) und manifest.json folgen |
| 6 Docs | STATUS Abschnitt 4, `archive/history.md`, diese Prereg, Chronik |

**Einordnung:** der erste Champion-Wechsel seit v21 (2026-08-20) und der
erste, der nicht aus einem neuen Netz, sondern aus einem SUCH-Knopf am
bestehenden Generator-Netz kommt. `v23-b01_brierbest` selbst blieb auf
Augenhoehe mit v21 (214:186); der Knopf hebt es auf 259:191 gepoolt. Fuer
Erzeugung (v24 par.6b') und Spielbetrieb gilt dieselbe Konfiguration.

