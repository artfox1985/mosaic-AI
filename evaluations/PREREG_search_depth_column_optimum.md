<!-- STATUS: OFFEN | Frage: Gibt es fuer den Spaltenbau ein OPTIMUM mittlerer Suchtiefe -- baut b05 bei 150 Sims mehr volle Spalten als bei 400, und kostet das Spielstaerke? | Beleg: ANLASS 2026-08-30, ein Punktpaar aus VERSCHIEDENEN Modi (value-only@150 0,4425 gegen self-play@400 0,3375) plus der Sims-1-Kollaps (0,0075, par.3b.8 Stufe C). Nichts entschieden; Stufe 1 schliesst die Modus-Luecke, die Arena entscheidet Gewinn gegen Tausch. -->

# Vorregistrierung: Suchtiefe und Spaltenbau -- gibt es ein Optimum?

**Angelegt 2026-08-30** auf Nutzer-Auftrag ("wie schliessen wir den
Strang sauber ab"), VOR jeder Messung dieses Strangs.

## par.1 Der Anlass, ehrlich als Punktpaar benannt

Bei der Sims-Probe fuer den v22-b05-Schwarm fiel auf:

| Lauf | Modus | Sims | volle Spalten je Seite | Punkte |
| --- | --- | --- | --- | --- |
| simsprobe150 | value-only, argmax | 150 | **0,4425 +- 0,042** | 41,0 |
| otw22b05w00 | Self-Play, argmax | 400 | 0,3375 | 37,2 |
| par.3b.8 Stufe C | Self-Play, argmax | 1 | 0,0075 | 11,1 |

**Die beiden oberen Zeilen stammen aus VERSCHIEDENEN Modi** -- der
Vergleich traegt nicht. Er ist der Anlass, nicht der Befund. Die
Sims-1-Zeile zeigt aber, dass die Kurve nicht monoton fallend sein
kann: irgendwo zwischen 1 und 400 liegt ein Maximum.

**Warum das interessant ist (Hypothese, ungeprueft):** Phase 0 hat
gemessen, dass die POLICY das Spaltenwissen traegt (Prior-Ratio 1,23,
Draft-Erbe) und der VALUE-Kopf den Plattenlohn mit Steigung 0,0886
unterbietet. Mehr Suche heisst mehr Gewicht fuer den gedaempften
Bewerter gegen den spaltenkundigen Prior. Dann waere die Suchtiefe ein
Regler zwischen beiden -- und der heutige Betriebspunkt (400) laege auf
der falschen Seite des Maximums.

## par.2 Stufenplan mit vorab festgelegten Entscheidungsregeln

**Stufe 1 -- die fehlende Kontrollzelle (Pflicht, ~42 min).**
value-only, argmax, **400 Sims**, 200 Partien, Seed 20260902 (identisch
zur 150er-Probe), Stack-Draw EIN. Damit variiert NUR die Sims-Zahl.
*Regel:* liegt @400 im selben Modus auf oder ueber @150, ist der
Anlass-Effekt ein MODUS-Artefakt -- Strang GESCHLOSSEN, Eintrag in
STATUS, keine weitere Messung.

**Stufe 2 -- die Kurve (nur wenn Stufe 1 den Effekt bestaetigt, ~1 h).**
Dieselbe Anordnung mit 50 / 100 / 250 Sims, je 200 Partien, gleicher
Seed. Ergebnis ist eine Kurve mit lokalisiertem Maximum.
*Regel:* das Maximum wird BERICHTET, nicht sofort uebernommen -- die
Uebernahme entscheidet Stufe 3.

**Stufe 2b -- die UNTERE Flanke (Nutzer-Auftrag 2026-08-30, waehrend
Stufe 2 lief).** Anlass: der 50er-Zwischenstand (0,5179 bei 140
Partien) setzt den Trend monoton fort, waehrend Sims 1 bei 0,0075
liegt -- der Absturz sitzt also zwischen 1 und 50, und ohne ihn kennt
die Kurve nur EINE Flanke. Zusatzarme **25 und 10 Sims**, gleiche
Anordnung und gleicher Seed. *Lesart:* faellt schon 25 deutlich ab,
liegt das Maximum bei ~50; traegt auch 10, ist der Absturz sehr steil
und sitzt knapp ueber 1 -- dann waere die Kurve ueber fast ihre ganze
Breite fallend in den Sims, was die Deutung (Suche ueberstimmt Prior)
stuetzt, aber die Betriebsempfehlung NICHT automatisch nach unten
verschiebt: dafuer entscheidet Stufe 3.

**Zusaetzliche Berichtsgroesse ab Stufe 2 (Nutzer-Hinweis):** volle
Spalten je STUNDE (Rate x Partien je Stunde), weil fuer die
Korpus-Erzeugung die Ereignisse pro Zeit zaehlen, nicht pro Partie.
Gemessene Punkte bisher: 400 Sims 97/h, 150 Sims 300/h, 50 Sims
~565/h (je Seite).

**Registrierter Gegeneinwand, der bei der Uebernahme mitgelesen werden
MUSS (`PREREG_v22_window.md` par.4):** "ein ueberwiegend aus
150-Sim-Partien bestehendes Fenster kalibriert den Value-Kopf auf
schwaechere Trajektorien". Mehr Vollendungen von einem schwaecher
spielenden Erzeuger sind nicht automatisch besseres Material -- genau
deshalb entscheidet die Arena (Stufe 3) und nicht die Spaltenrate.

**Stufe 2c -- FAKTOREN-TRENNUNG Tiefe gegen Breite (registriert
2026-08-30 auf Nutzer-Auftrag, VOR der Messung).** Anlass: mit `--sims`
variiert gekoppelt die Wurzelbreite, weil `MOSAIC_GUMBEL_TOP_M` auf
Default 0 steht und die Formel `m = sims/16` greift (Registratur;
net_mcts.rs:2514) -- der Gipfel bei 100 Sims hat m=6, der 400er-Punkt
m=25. Bis zur Trennung heisst der Befund SUCHBUDGET, nicht Suchtiefe.

Vorab entschieden ist eines: das VERHAELTNIS scheidet als Erklaerung
aus, weil die Formel Sims-je-Wurzelkind ueber alle Messpunkte bei ~16
konstant haelt (100/6, 400/25, 50/3) -- eine Groesse, die nicht
variiert, kann keinen Gipfel erzeugen.

2x2 mit zwei bereits gemessenen Zellen, `MOSAIC_GUMBEL_TOP_M` explizit:

| | m=6 | m=25 |
| --- | --- | --- |
| sims 100 | 0,6225 (gemessen) | NEU |
| sims 400 | NEU | 0,3375 (gemessen) |

*Lesart:* liegt (400, m=6) beim Gipfelwert, war es die BREITE; bleibt
es beim 400er-Niveau, war es die TIEFE. (100, m=25) spiegelt das.
*Benanntes Degenerationsrisiko:* (100, m=25) laesst nur 4 Simulationen
je Wurzelkind -- Sequential Halving trennt dort kaum noch; ein Absturz
dieser Zelle ist deshalb nicht eindeutig der Breite zuzuschreiben.
(400, m=6) mit 66 je Kind ist die aussagekraeftigere Zelle.
Umfang je Zelle 200 Partien, gleiche Seeds, sonst identisch.

**Stufe 2d -- Aufloesung am Gipfel (Nutzer-Auftrag 2026-08-30, VOR dem
v21-Vergleich):** ein Arm bei **75 Sims**, gleiche Anordnung. Grund: der
Gipfel steht zwischen 50 (0,4825) und 150 (0,4425) mit 100 (0,6225) als
einzigem hohen Punkt -- ein einzelner Messpunkt traegt einen Gipfel
nicht. 75 prueft, ob die Flanke links vom Gipfel glatt ansteigt oder ob
der 100er-Wert ein Ausreisser ist. Kosten ~13 min.

**Stufe 2f -- FRISCH-SEED-REPLIKATION des Gipfels (registriert
2026-08-30, VOR den Folgemessungen; bindend).** Mehr Arme loesen die
KURVENFORM besser auf, aber sie schuetzen NICHT vor dem
Selektionsbias: wer aus mehreren verrauschten Punkten den hoechsten
als Gipfel nimmt, ueberschaetzt ihn im Erwartungswert (Winner's Curse;
bei SE ~0,04 je Punkt und einem halben Dutzend Armen ist ein
4-SE-Ausschlag nicht selten). Deshalb gilt: **bevor v21-Vergleich
(2e), Faktoren-Trennung (2c) oder Arena (3) auf einem Gipfelwert
aufsetzen, wird dieser Punkt EINMAL mit frischem Seed wiederholt**
(200 Partien, sonst identisch). Haelt der Wert, traegt er die
Folgemessungen; faellt er auf Plateau-Niveau, war es Rauschen und die
Lesart lautet "Plateau", nicht "Optimum".
**BERICHTIGUNG im selben Zug (Nutzer-Einwand 2026-08-30):** ein
Plateau macht die Folgemessungen NICHT gegenstandslos -- so hatte ich
es zunaechst formuliert, und das war zu eng gedacht. Die tragende
Frage ist "beeinflusst das Suchbudget die Spaltengenerierung, und
haengt das am Prior?", nicht "warum gibt es einen Gipfel". Der TREND
(400: 0,3375 gegen 50-150: ~0,45) ist gemessen und unabhaengig von der
Feinform. Es aendern sich nur die MESSPUNKTE: im Gipfel-Szenario
Gipfel gegen Nachbar, im Plateau-Szenario Plateau-Punkt gegen 400.
Das 2x2 der Faktoren-Trennung ist in beiden Faellen identisch, weil
die Wurzelbreite ueber denselben Bereich mitwandert (m=3-9 im Plateau
gegen m=25 bei 400). Dieselbe Logik wie die
Frisch-Seed-Replikation bei SPRT-Fruehstopps
(docs/promotion_checklist.md Punkt 2).

**Stufe 2e -- NETZ-VERGLEICH v21 (Sims-Zahlen erst NACH Stufe 2d
festlegen, Nutzer-Praezisierung 2026-08-30).** Gefragt ist, ob der
Gipfel eine Eigenschaft der SUCHE ist oder des spaltenkundigen PRIORS,
den nur b05 hat (Prior-Ratio 1,23 gegen 0,59 beim Champion). Gemessen
werden deshalb **der dann bekannte Gipfelpunkt und der Nachbarpunkt
mit dem staerksten Kontrast bei b05** -- nach heutigem Stand 100 gegen
50, aber das haengt am 75er-Arm und wird erst danach eingesetzt. Beide
Arme MIT Stack-Draw-Knopf (Nutzer: dann ist der Vergleich in sich
geschlossen und haengt nicht an der Alt-Referenz, die ohne Knopf lief),
gleiche Seeds, je 600 Partien (Blockfehler ~0,017; noetig, weil v21 auf
0,102-Niveau liegt und ein relativer Effekt dort absolut klein ist).
*Lesart:* zeigt v21 denselben Sprung, ist der Gipfel Such-Mechanik und
die Prior-Deutung widerlegt; bleibt v21 flach, haengt er am Prior --
mit dem Vorbehalt, dass ein Nullbefund auf niedrigem Niveau schwaecher
wiegt als ein positiver.
*Technischer Vorbehalt:* v21 traegt 76 Planes-Kanaele gegen heute 79 --
der Python-Pfad ist daran schon gescheitert (2026-08-30, seither
gekuerzt); fuer den Rust-Self-Play ist ein 20-Partien-Rauchtest VOR dem
Lauf Pflicht.

**Stufe 3 -- der Haertetest (Arena, entscheidet Gewinn gegen Tausch).**
Gepaarte Arena b05@Optimum gegen b05@400, `tools/paired_gating.py
--no-promote-winner` (block-size 5 = Default), Seed 20260920.
*Regeln:*
* kein signifikanter Staerkeverlust => **echter Gewinn**: weniger Suche
  ist billiger UND spaltenreicher; Konsequenz fuer Erzeugung und
  moeglicherweise fuer den Spielbetrieb (eigener Entscheid).
* signifikanter Verlust => **Tausch**, kein Gewinn: der Spaltenzuwachs
  ist mit Spielstaerke bezahlt. Dann gilt er nur dort, wo Spalten das
  Produkt sind (Korpus-Erzeugung fuer die Value-Klasse), NICHT im
  Spielbetrieb -- und das ist ausdruecklich zu trennen.

**Stufe 4 -- Mechanismus (Datenpassage, nur bei bestaetigtem Effekt).**
Auf denselben Korpora: Anteil der Wurzelentscheidungen, in denen die
Suche den Policy-Top-1 VERWIRFT, je Sims-Stufe; dazu das
Q/Prior-Verhaeltnis (`tools/gumbel_scale_calibration.py`, dessen
Schwellenregel aus PREREG_prior_blind_spot ohnehin je Champion faellig
ist). *Erwartung bei zutreffender Hypothese:* der Verwerfungsanteil
steigt mit den Sims, und die verworfenen Zuege sind ueberproportional
spaltenbauend.

## par.2a STUFE 1 GEFAHREN 2026-08-30: Modus-Erklaerung WIDERLEGT, Effekt bleibt (knapp unter Signifikanz)

value-only, argmax, Seed 20260902, je 200 Partien, 10 Bloecke:

| Sims | volle Spalten | Quote | init>=4 | Punkte |
| --- | --- | --- | --- | --- |
| 150 | **0,4425 +- 0,042** | 0,211 | 2,09 | 41,01 |
| 400 | 0,3375 +- 0,026 | 0,170 | 1,98 | 38,37 |

Gepaart ueber die Bloecke: **volle Spalten +0,1050 (se 0,051, t +2,06)**,
Punkte +2,64 (t +1,98) -- beide unter der Schwelle 2,262 (df=9), beide
in dieselbe Richtung.

**Regel-Anwendung:** die Schliessungsbedingung ("@400 liegt auf oder
ueber @150") ist NICHT eingetreten -- der Strang bleibt offen, Stufe 2
laeuft. Der Effekt ist damit nicht signifikant, aber auch nicht
wegerklaert.

**Beifang, der die Anlass-Tabelle repariert:** value-only@400 misst
0,3375 -- identisch mit dem normalen Self-Play@400 (otw22b05w00,
anderer Seed). Der MODUS aendert die Spaltenzahl also nicht, was zur
Mechanik passt (`--value-only` markiert nur Policy-Ziele als ungueltig,
es aendert das Spiel nicht). Damit war der Anlass-Vergleich aus par.1
im Ergebnis doch tragfaehig -- was er NICHT war, ist ein Beleg, und
genau deshalb lief Stufe 1.

## par.2g Zwei Korrekturen aus der Nutzer-Pruefung 2026-08-30 (beide gegen MICH)

**(1) Der Sockel-Wert 400 war willkuerlich.** Er stand unkommentiert im
Zuschnitt D, begruendet nur mit "dort sind die Ziele das Produkt". Der
BESTAND faehrt **600 Sims** fuer den Netz-Sockel
(PREREG_v21_window.md:15, Generator v20-Champion, 4.000 Partien) --
BERICHTIGT 2026-08-30 auf Nutzer-Einwand: ich hatte zusaetzlich
PREREG_v22_window.md:123 zitiert, aber diese Tabellenzeile gehoert zum
am 2026-08-25 VERWORFENEN Entwurf (das v22-Fenster IST der
hv2-Lehrerkorpus, kein Netz-Korpus). Fundstelle gegriffen, ohne ihre
Gueltigkeit zu pruefen -- die Aussage steht damit auf EINEM Beleg
statt auf zweien.
meine Zahl war also weder gemessen noch am Bestand orientiert. Sie ist
aus der Festlegung raus; die Sockel-Sims gehoeren in dieselbe
Arena-Entscheidung wie der Schwarm. Hintergrund, der die Sache
zuspitzt: beim NETZ-Self-Play sind Spielen und Labeln GEKOPPELT (eine
Suche liefert Zug und Policy-Ziel), waehrend der hv2-Korpus sie trennt
(Heuristik spielt, Netz labelt mit 600) -- die Kurve greift also beim
Sockel voll durch, beim hv2-Korpus nicht.

**(2) "600 Sims erklaeren die historische Spaltenarmut" ist FALSCH und
zurueckgenommen** (Nutzer-Einwand: die bisherigen Generationen hatten
keinen Spalten-Lehrer). Die Vermutung war sogar inkonsistent mit der
eigenen These dieses Strangs: wenn der Effekt daher ruehrt, dass die
Suche einen spaltenkundigen PRIOR ueberstimmt, kann er bei v21 und
frueher nicht aufgetreten sein -- dort gab es kein Spaltenwissen zu
ueberstimmen. Die historische Spaltenarmut haengt am fehlenden Lehrer.
Ein 600er-Arm fuer b05 wurde daraufhin VERWORFEN (Nutzer): er wuerde
einen Betriebspunkt vermessen, den niemand mehr erwaegt.

## par.2h FOLGEGEDANKE: Spielen und Labeln entkoppeln (registriert 2026-08-30; Idee, KEINE Machbarkeitsaussage)

**Beobachtung, die den Gedanken ausgeloest hat:** der hv2-Korpus TRENNT
die beiden Rollen -- die Heuristik spielt (spaltenkompetent), das Netz
labelt mit 600 Sims. Das NETZ-Self-Play kann das nicht: dieselbe Suche
waehlt den Zug UND liefert das Policy-Ziel. Genau deshalb greift die
Sims-Kurve dort voll durch.

**Der Gedanke:** sollte sich bestaetigen, dass flache Suche besser
SPIELT (Spalten, Punkte) und tiefe besser LABELT, waere die saubere
Loesung eine Entkopplung -- mit flacher Suche spielen, die besuchten
Zustaende danach mit tieferer Suche nachlabeln. Technisch ist das
"Reanalyze" (MuZero/ReZero-Muster), im Projekt als Phase-3-Kandidat
aus der Research-Durchsicht 2026-08-29 benannt und bis heute
UNREGISTRIERT und ungebaut; das gebaute Relabeling
(relabel_drafts_with_teacher) ersetzt Policy-Ziele durch LEHRER-Zuege
und laesst Value-Felder unberuehrt, ist also etwas anderes.

**Zwei Vorbehalte, die dazugehoeren:**
1. **Machbarkeit ungeprueft.** Ob die Engine gespeicherte Zustaende mit
   einer zweiten, tieferen Suche nachlabeln kann, ohne die Partie neu
   zu spielen, habe ich NICHT nachgesehen.
2. **Die Praemisse "tiefe labelt besser" ist ungeprueft und nicht mehr
   selbstverstaendlich** (praezisiert 2026-08-30 auf Nutzer-Nachfrage;
   die erste Fassung sagte "dieser Strang stellt sie in Frage" und war
   zu stark). Was DIESER Strang misst, ist SPIELqualitaet je Suchbudget
   (volle Spalten, Punkte im gespielten Verlauf) -- nicht LABELqualitaet.
   Der Schluss vom einen aufs andere ist eine HERLEITUNG: folgt die
   Suche einem verzerrten Bewerter, ist ihre Besuchsverteilung, also
   das Label, von demselben Bewerter gepraegt. Die Herleitung hat eine
   Luecke: eine Besuchsverteilung kann taktisch nuetzliche Information
   tragen, auch wenn der Bewerter im PLATTENanteil verzerrt ist -- das
   eine schliesst das andere nicht aus. Der Gedanke haengt damit an
   einer Messung, die es noch nicht gibt (und fuer die es keine
   neutrale Referenz gibt, siehe par.2 Stufe 3).

## par.3 Was dieser Strang NICHT ist

* **Keine Wiederaufnahme der Q-Skalierungs-Familie** (geschlossen). Hier
  wird kein Regler zwischen Q und Prior gedreht, sondern die Sims-Zahl
  variiert -- ein Erzeugungs- und Betriebsparameter.
* **Kein Ersatz fuer Phase 3.** Faende sich ein Optimum, waere das eine
  Umgehung der Betrags-Daempfung, keine Heilung: der Value-Kopf bliebe
  falsch geeicht, man wuerde ihn nur weniger fragen.
* ~~Kein Kriterium fuer den laufenden v22-b05-Schwarm.~~ **BERICHTIGT
  im selben Zug (Nutzer-Entscheid 2026-08-30): die v22-Self-Plays sind
  AUSGESETZT, bis dieser Strang abgeschlossen ist.** Damit ist er kein
  Nebenstrang mehr, sondern der Taktgeber: die Erzeugung startet
  danach mit einem GEMESSENEN Betriebspunkt statt mit einem
  plausiblen. Faellt in Stufe 2/3 ein anderes Optimum als 150, faehrt
  der Schwarm dieses -- die Sims-Wahl ist bis zum Start offen.

## par.4 Erwartungswert, damit die Kosten eingeordnet sind

Stufe 1 kostet 42 Minuten und kann den Strang komplett schliessen --
das ist der billigste denkbare Ausgang. Der teure Ausgang (Stufen 2+3,
zusammen ~3 h) tritt nur ein, wenn der Effekt real ist; dann ist er
auch die Kosten wert, weil er einen Betriebsparameter betrifft, der
JEDEN kuenftigen Lauf und moeglicherweise die Spielstaerke selbst
beruehrt.
