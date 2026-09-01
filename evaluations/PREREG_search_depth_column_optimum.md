<!-- STATUS: OFFEN | Frage: Gibt es fuer den Spaltenbau ein Optimum mittlerer Suchtiefe -- und kostet es Spielstaerke? | Beleg: JA und JA (b05-Kurve par.2i: Plateau 25-100 ~0,6 gegen 0,34 ab 250), aber ein TAUSCH: @25 verliert 11:29 (signifikant), @100 33:47 (p = 0,14, Tendenz, par.2j2). Faktor ist die TIEFE, nicht die Breite (par.2k; m=25-Praemisse in par.2c berichtigt, Clamp ist 16). Stufe 4 Teil A auf 200 distinkten Zustaenden wiederholt (par.6b): Verwerfung 0,825 @400 gegen 0,490 @100, 70:3 diskordant, p = 1,4e-17. **OFFEN: Teil B** (Spalten-Etikett, zweiter Trace-Durchgang). -->

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
MUSS (`PREREG_v22_window.md` par.5, Zeilen 153-154; Verweis am 2026-09-01 berichtigt, par.4 dort handelt vom Vorzug):** "ein ueberwiegend aus
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

**BERICHTIGT 2026-09-01, am Code geprueft:** die Formel ist
`clamp(round(sims/16), 4, GUMBEL_TOP_M)` mit `GUMBEL_TOP_M = 16`
(`net_mcts.rs:2097`, `gumbel_top_m_for_budget` `net_mcts.rs:2135-2141`).
Der 400er-Punkt hat also **m=16, nicht 25**, und die Sims je Wurzelkind sind
NICHT konstant: 400/16 = 25, 100/6 = 16,7, 50/4 = 12,5, 25/4 = 6,25,
10/4 = 2,5. Die folgende "vorab entschiedene" Ausschlussbegruendung steht
damit auf einer falschen Praemisse; sie wird nicht geloescht, sondern als
falsch markiert. Das Verdikt von par.2k (Tiefe, nicht Breite) traegt
trotzdem, weil die Schluesselzelle (400, m=6) gegen (400, m=16) misst und
dort keine Bewegung zeigt; die Spalte "m=25" der 2x2-Tabellen unten heisst
in der 400er-Zeile real "m=16 (Default)", und die Zelle (100, m=25) ist ein
Override UEBER die Code-Obergrenze, die 2x2 also nicht symmetrisch.

~~Vorab entschieden ist eines: das VERHAELTNIS scheidet als Erklaerung
aus, weil die Formel Sims-je-Wurzelkind ueber alle Messpunkte bei ~16
konstant haelt (100/6, 400/25, 50/3) -- eine Groesse, die nicht
variiert, kann keinen Gipfel erzeugen.~~ (falsche Praemisse, siehe oben)

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

## par.2i STUFEN 2/2b/2d/2f GEFAHREN 2026-08-30: die Kurve, und was von ihr traegt

**Vollstaendige Kurve (value-only, argmax, Seed 20260902, je 200
Partien, Stack-Draw EIN):**

| Sims | volle Spalten | +- | Punkte |
| --- | --- | --- | --- |
| 10 | 0,4531 | 0,014 | 41,49 |
| 25 | 0,5650 | 0,029 | 43,99 |
| 50 | 0,4825 | 0,041 | 42,08 |
| 75 | 0,4750 | 0,037 | 41,75 |
| 100 | 0,6225 | 0,035 | 46,06 |
| 150 | 0,4425 | 0,042 | 41,01 |
| 250 | 0,3325 | 0,021 | 39,99 |
| 400 | 0,3375 | 0,026 | 38,37 |

**Frisch-Seed-Replikation (Stufe 2f, Seed 20260930):** 25 Sims 0,6600
(Erst 0,5650), 100 Sims 0,6550 (Erst 0,6225) -- **beide Spitzenwerte
replizieren, der Effekt ist hart.** Die Feinstruktur dagegen NICHT: 25
und 100 sind ununterscheidbar (~0,61 gegen ~0,64 bei SE ~0,04), und
die Seed-Streuung eines einzelnen Punktes betraegt bis 0,095 (25er).
**Lesart: PLATEAU von etwa 25 bis 100 (~0,6), Absturz auf ~0,34 ab
250, und eine Untergrenze unterhalb von 25 (10er faellt auf 0,45).**
Die 50/75-Werte sind vor diesem Hintergrund als Streuung nach unten zu
lesen, nicht als Struktur. Mein zwischenzeitliches "klarer Gipfel bei
100" war voreilig; erst der Nutzer-Auflossungsarm (75) und die
Replikation haben das Bild geradegerueckt.

## par.2j STUFE 3 TEIL 1 GEFAHREN: 25 Sims ist ein TAUSCH, kein Gewinn

Gepaarte Arena b05@25 gegen b05@400 (dasselbe Netz, gleiche Seeds,
Stack-Draw EIN, exklusiv gefahren): **11:29, SPRT H0 nach 20 Paaren,
Vorzeichentest p=0,0117, gepaarte Differenz -0,90 [-1,43; -0,37]**
(paired_gating_result_b05@25_vs_b05@400.json).

**Damit greift die vorab registrierte Tausch-Regel:** der
Spaltenzuwachs bei 25 Sims ist mit Spielstaerke bezahlt. Fuer den
SPIELBETRIEB aendert sich nichts, 400 bleibt.

**Der eigentliche Erkenntnisgewinn ist die Trennung zweier Groessen:**
die Spalten-Kurve ist NICHT die Staerke-Kurve. Weniger Suche baut mehr
Spalten UND spielt schlechter -- beides gleichzeitig, ohne Widerspruch:
die Suche korrigiert taktische Fehler des Priors und optimiert
zugleich seinen Spaltenbau weg. Wer kuenftig "mehr Spalten" misst,
darf daraus nicht auf "besser" schliessen (und umgekehrt).

Fuer die KORPUS-Erzeugung bleibt die Frage offen und unbequem: ein
Erzeuger, der 11:29 gegen den Betriebspunkt verliert, ist nicht
selbstverstaendlich besseres Trainingsmaterial -- genau darauf zielt
der registrierte Gegeneinwand aus PREREG_v22_window par.5. Deshalb
lief Teil 2 mit dem Kompromiss-Kandidaten 100 Sims (gleiche
Spaltenrate wie 25, vierfaches Suchbudget); Ergebnis in par.2j2 unten.

## par.2j2 STUFE 3 TEIL 2 GEFAHREN: @100 verliert 33:47, NICHT signifikant (2026-08-30, nachregistriert 2026-09-01)

Dieser Absatz fehlte: das Ergebnis stand nur im Kopf und in par.6.
`evaluations/paired_gating_result_b05at100_vs_b05at400.json` (seit
2026-09-01 eingecheckt): 40 Paare, SPRT-Verdikt H0, **33:47**, McNemar
p = 0,1435, 95%-KI der gepaarten Differenz [-0,744, +0,044] -- das KI
enthaelt die Null. **Base-Seed 20260921**, nicht der in Stufe 3 registrierte
20260920 (den hat der @25-Lauf); der Seedwechsel war nicht registriert und
wird hier nachgetragen. Lesart: Richtung wie beim @25-Arm (11:29, p = 0,0117,
signifikant), aber fuer sich genommen kein Beleg. Wo im Text "@100 verliert
33:47" als Beleg steht, gilt: Tendenz, nicht Befund.

## par.2k STUFE 2c GEFAHREN: es ist die TIEFE, nicht die Breite

Schluesselzelle (400 Sims, `MOSAIC_GUMBEL_TOP_M=6`, sonst identisch,
200 Partien, Seed 20260902): **0,3525 +- 0,0317** (Punkte 39,72,
init>=4 2,12).

| | m=6 | m=25 |
| --- | --- | --- |
| Sims 100 | 0,6225 | (Gegenprobe laeuft) |
| Sims 400 | **0,3525** | 0,3375 |

**Verdikt: die Wurzelbreite erklaert den Effekt NICHT.** Bei 400 Sims
liegt der Spaltenwert mit schmaler Wurzel (0,3525) praktisch auf dem
mit breiter (0,3375); die Differenz ist ein halber Standardfehler.
Entlang der Tiefe dagegen springt derselbe Wert bei gleicher Breite
von 0,6225 (100) auf 0,3525 (400). **Der Befund heisst damit ab jetzt
SUCHTIEFE, nicht mehr Suchbudget** -- die par.2c-Auflage ist erfuellt.

**Praktische Folge: es gibt keine Abkuerzung.** Die Hoffnung, mit
voller Tiefe und schmaler Wurzel Staerke UND Spalten zu bekommen, ist
widerlegt; der in par.2j gemessene Handel bleibt bestehen.

**GEGENPROBE (100 Sims, m=25) GEFAHREN: 0,4750 +- 0,031** (Punkte
42,85). Damit ist das 2x2 vollstaendig:

| | m=6 | m=25 |
| --- | --- | --- |
| Sims 100 | 0,6225 | **0,4750** |
| Sims 400 | 0,3525 | 0,3375 |

Beide Zeilen bestaetigen dasselbe: **entlang der TIEFE aendert sich der
Wert stark** (bei m=6: 0,62 -> 0,35; bei m=25: 0,475 -> 0,3375),
**entlang der BREITE nur wenig** (bei 400 Sims gar nicht, bei 100 Sims
0,62 -> 0,475). Die Breite hat also einen kleineren, aber
gleichgerichteten Nebeneffekt -- schmalere Wurzel = mehr Spalten --,
der die Tiefe nicht ersetzt. Der Vorbehalt zur Zelle (100, m=25) gilt
weiter (nur 4 Simulationen je Wurzelkind, Sequential Halving trennt
dort kaum), sie ist deshalb die schwaechste der vier.

**Mechanische Lesart (Herleitung, konsistent mit Phase 0):** die
Gumbel-Wurzelauswahl sortiert Kandidaten nach ihrem Q-Wert. Mehr
Simulationen heissen stabilere Q-Werte und damit mehr Gewicht fuer den
VALUE-Kopf gegenueber dem rohen Prior. Bei wenig Simulationen dominiert
die Policy, die das Spaltenwissen traegt (Prior-Ratio 1,23); bei vielen
dominiert der Value-Kopf, der den Plattenlohn um Faktor ~11 unterbietet
(R5-Steigung 0,0886). **Die Suchtiefe ist damit faktisch ein Regler
zwischen den beiden Koepfen -- und der Betriebspunkt 400 steht auf der
Seite des defekten.** Das ist eine Deutung, kein Beleg; pruefbar waere
sie ueber Stufe 2e (haengt der Effekt am Prior?) und ueber die
Umkehrprobe nach einer erfolgreichen Phase 3 (kippt die Kurve?).

## par.2l STUFE 2e GEFAHREN: der Effekt haengt am PRIOR -- Deutung bestaetigt

v21_2d_brierbest (plattenblind trainiert, Prior-Ratio 0,59 gegen b05s
1,23), value-only argmax, Seed 20260941, je 600 Partien, Knopf EIN:

| Netz | 100 Sims | 250 Sims | Differenz |
| --- | --- | --- | --- |
| b05 (spaltenkundiger Prior) | 0,6225 | 0,3325 | **+0,2900** |
| v21 (plattenblind) | 0,1058 +- 0,0096 | 0,1317 +- 0,0100 | **-0,0258** (t -1,89) |

*Nachtrag 2026-09-01:* die b05-Zeile stammt aus par.2i (Seed 20260902, je
200 Partien, ohne SE in dieser Tabelle), die v21-Zeile aus Seed 20260941 mit
je 600 Partien -- Stufe 2e hatte "gleiche Seeds, je 600 Partien" registriert.
Der Kontrast ist qualitativ eindeutig (Vorzeichen und Groessenordnung), aber
kein Vergleich unter gleichen Bedingungen.

**Bei v21 tritt der Effekt NICHT auf -- er zeigt sogar leicht in die
Gegenrichtung**, und auch die Punkte bleiben unbewegt (47,23 gegen
47,53; bei b05 lagen sie 6 Punkte auseinander). Das ist exakt die
vorab registrierte Falsifikationsbedingung: zeigt v21 denselben
Sprung, ist die Prior-Deutung widerlegt; bleibt er flach, haengt der
Effekt am Prior. **Er bleibt flach.**

**Damit steht die Mechanik:** die Suche drueckt weg, was der Prior an
Spaltenwissen anbietet. Wo nichts angeboten wird, kann nichts
weggedrueckt werden. Die Suchtiefe wirkt nur, wo Prior und Value-Kopf
verschiedener Meinung sind.

**Messmethodische Lehre, die dazugehoert:** der 20-Partien-Rauchtest
hatte fuer v21@100 0,275 gezeigt und mich fast zur Aussage verleitet,
die Deutung sei widerlegt. Der volle Lauf liefert 0,1058 -- Faktor 2,6
daneben. Bei n=20 ist der Fehler so gross wie der Effekt; ein
Rauchtest belegt, dass ein Werkzeug LAEUFT, nie was es misst.

## par.2m ANSCHLUSS an die Einhuellenden-Idee (Nutzer 2026-08-30)

Der Befund stuetzt die Bauform "Einhuellende frueh stark, ueber die
Runden abklingend" -- vier unabhaengige Gruende:

1. **Frueh entscheidet es sich:** die Ketten-Diagnose (par.3b.8) zeigt,
   dass sich Abweichungen ueber die Kette multiplizieren (0,6^k); die
   Versorgung wird in R1-2 verspielt, nicht in R5.
2. **Dort ist der Bewerter am schwaechsten:** Ownership-Kopf trennt in
   R1 mit AUC 0,698 gegen 0,886 in R5 (PREREG_ownership_selector par.9.4).
3. **Spaet braucht es nichts:** ab Runde 5 rechnet die exakte
   Alpha-Beta-Suche (round5.rs), dort ist nichts zu lenken.
4. **Die Huelle umgeht den defekten Kanal:** sie ist eine geometrische
   Vorgabe und braucht keine Bewertung des Plattenlohns.

**Registrierungsstand der Idee (geprueft):** der HUELLEN-TRIMM der
Ownership-Loss-Maske ist als Nachtrag 6 der Lehrer-Prereg registriert;
die EINHUELLENDE ALS 2D-EINGABEEBENE steht nur als Merkposten in der
STATUS-Strangtabelle (Nutzer-Frage 2026-08-24, "nicht registriert");
das RUNDENABKLINGEN ist neu. **Vorbehalt:** Shaping-Terme auf
Wertungsplatten waren mehrfach H0 und die Injektionslinie gilt als "zu
Ende gemessen" -- neu waeren hier zwei Dinge, die Potentialform
(Ng/Harada/Russell, die einzige nachweislich politik-erhaltende
Bauform, RESEARCH_heuristic_methodology 4.6) und ein spaltenfaehiges
Netz als Traeger.

## par.2n BERICHTIGUNG der mechanischen Deutung (2026-08-30, nach der kriterienweisen Aufschluesselung)

par.2k begruendet den Suchtiefen-Effekt damit, dass die Suche einem
Value-Kopf folgt, der "den Plattenlohn um Faktor ~11 unterbietet". Die
kriterienweise Zerlegung (PREREG_r5_value_calibration par.10, Auftrag
des Nutzers) zeigt: **so stimmt das nicht.** Die Daempfung ist BREIT
(alle acht Kriterien zwischen 0,00 und 0,29 gegen Soll ~1), und
ausgerechnet **k1 (Spalten) ist am WENIGSTEN gedaempft** -- 0,1747
(t 4,19), im Wechselwirkungstest ueber den uebrigen sieben, im
annahmefreien Paar-Tausch 4->1 sogar 0,1996 bei t 12,08 (v21 dort
0,0152). Der Kopf ist also **plattensensitiv-schwach, nicht
spaltenblind**.

**Was bestehen bleibt:** der Suchtiefen-Effekt selbst (gemessen) und
seine Prior-Abhaengigkeit (v21-Kontrast, par.2l). **Was faellt:** die
Begruendung "die Suche folgt einem Kopf, der Spalten nicht sieht".

**Zwei Kandidaten-Erklaerungen, beide UNGEPRUEFT und als Hypothese
markiert:**
1. **Skalenproblem statt Blindheit.** Die Daempfung ist breit, aber
   Spalten sind mit 7 Punkten das TEUERSTE Kriterium: bei Steigung
   0,175 nimmt der Kopf davon 1,2 Punkte wahr statt 7 -- absolut der
   groesste Verlust aller Kriterien, obwohl relativ der kleinste.
   Gegen Kosten anderer Skala (Strafleiste, Sofortpunkte) verliert die
   Spalte damit trotzdem.
2. **Planungsproblem statt Bewertungsproblem** (Nutzer-Lesart, gestuetzt
   von PREREG_placement_side, Schlussabschnitt, "das Material war da, der Plan
   nicht"; die Datei hat kein par.-Schema, Verweis berichtigt 2026-09-01): eine Spalte verlangt eine mehrrundige Farbzusage; tiefere
   Suche findet mehr gleichwertig bewertete Alternativen, die den Plan
   zerlegen, ohne dass eine einzelne Bewertung falsch waere. Dazu passt,
   dass Ordnung (Tau +0,338), k1-Sensitivitaet und Mensch-Orakel alle
   unauffaellig sind.

Beide sind mit vorhandenen Mitteln pruefbar (Stufe 4 dieses Strangs:
verwirft die Suche Policy-Top-1-Zuege, und sind die ueberproportional
spaltenbauend?).

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

## par.5 STUFE 4 KONKRETISIERT -- Zuschnitt vor dem Bau (2026-09-01)

**Warum jetzt:** vier Eingriffe sind gemessen wirkungslos oder schaedlich
(`PREREG_r5_value_calibration` par.12, `PREREG_gumbel_c_scale_arm` par.5):
Value lauter (-0,125), Value leiser (n.s.), Punkte-Blend (n.s.),
Prior/Value-Balance auf Gleichgewicht (n.s.). **Berichtigt 2026-09-01:** nur
der letzte davon ist ein WURZEL-Eingriff (`c_scale`, `net_mcts.rs:2281`);
`VALUE_CAL_B` und `POINTS_UTILITY_W` greifen in `blended_leaf_win_prob`
(`net_mcts.rs:1381`), also baumweit am Blattwert jedes Knotens. Aus "eine
baumweite Blattwert-Transformation bewegt nichts" folgt nicht "die Ursache
liegt tiefer im Baum" -- es folgt nur, dass weder Skala noch Wurzelbalance
den Effekt tragen. Nur die Suchtiefe selbst bewegt den Spaltenbau (b01:
0,7200 bei 100 Sims gegen 0,5150 bei 400; die Kurve dieser Prereg, par.2i,
ist an b05 gemessen: 0,6225 gegen 0,3375). Die Frage dieser Stufe ist damit
die naechstliegende offene, nicht "die einzige verbliebene".

**Instrument, ohne Bau verfuegbar:** `net_search_state_json_trace`
(lib.rs:928) liefert je Wurzelkandidat `prior`, `ln_prior`, `gumbel_g`,
`score`, `selected_top_m`, dazu je Halbierungsphase `q`, `sigma_q`, `visits`,
`raw_value`, `points_forecast`, `opp_points_forecast`, `eliminated` und die
Finalisten mit `successor_state_json`. An 400 Sims verifiziert (2026-09-01).
**Korrektur einer eigenen Fehlmeldung:** bei sehr wenigen Sims kann der Trace
leer bleiben, ich hatte das voreilig als Instrumentenluecke gemeldet -- er ist
vollstaendig.

### Teil A -- Verwerfungsanteil (messbar, kein Bau, kein Entwurfsspielraum)

**Frage:** wie oft weicht die Zugwahl der Suche vom Prior-Top-1 ab, und
steigt der Anteil mit den Sims?

* **Zustaende:** 200 Drafting-Zustaende aus b01-Self-Play bei
  DEFAULT-Knoepfen (`gumbel_c_scale` 1,0), Runden 2-4, ueber Dateien gestreut
  (Lehre aus dem Reachability-Erstlauf: `--je-datei`, sonst keine Block-SE).
* **Je Zustand zweimal**: `sims=100` und `sims=400`, gleicher Seed --
  gepaart, derselbe Zustand.
* **Messgroesse:** Anteil der Zustaende, in denen der Finalist mit den
  meisten `visits` NICHT der Kandidat mit dem hoechsten `prior` ist.
  Block-SE auf Dateiebene.
* **Vorab registrierte Erwartung** (aus der urspruenglichen Stufe-4-Fassung):
  der Anteil STEIGT mit den Sims. Faellt er oder bleibt gleich, ist auch diese
  Erzaehlung falsch -- dann verwirft die tiefere Suche nicht oefter, sondern
  ANDERS.

### Teil B -- ist das Verworfene spaltenrelevant? (braucht eine DEFINITION)

Ein Drafting-Zug fuellt Musterreihen, keine Kuppelzellen -- "spaltenbauend"
ist an der Wurzel nicht direkt ablesbar. Die Definition wird deshalb HIER
festgelegt, vor jeder Messung:

**DEFINITION BERICHTIGT 2026-09-01, an der Regelquelle geprueft (par.6a
unten). Urspruenglich stand hier:** "wenn er eine Musterreihe `r` bedient,
deren Vollendung eine Kuppelzelle in einer Spalte mit Fuellstand >= 4 fuellen
wuerde"** (Fuellstand aus `col_fill` des Zustands, Zeilenzuordnung ueber die
bestehende Spalten-Abbildung `2*tc + si%2`, wie in
`column_build_structural_probe`). Die Schwelle 4 uebernimmt bewusst die
`--min-fill`-Konvention des Bestandswerkzeugs
`ownership_map_completion_sites_probe`, statt eine neue zu erfinden.

* **Messgroesse:** unter den Zustaenden mit Verwerfung -- wie oft ist der
  Prior-Top-1 spaltenrelevant und die Suchwahl nicht? Und umgekehrt? Je
  Sims-Stufe.
* **Was ein Treffer waere:** bei 400 Sims wird ueberproportional oft ein
  spaltenrelevanter Prior-Top-1 zugunsten eines nicht-spaltenrelevanten Zuges
  verworfen, bei 100 Sims nicht.
* **Was es NICHT beantwortet:** ob die Suche damit RECHT hat. Die Tiefe
  gewinnt die Arena (@25 verliert 11:29, @100 verliert 33:47) -- ein
  bestaetigter Befund waere eine Beschreibung des Tauschs, kein Fehlerbeweis.

### Kosten und Reihenfolge

Teil A zuerst: rund 200 Zustaende x 2 Sims-Stufen, geschaetzt 10-20 min
(Trace bei 400 Sims rund 1-2 s je Zustand, einkernig; gemessen 1.020 s).
~~Teil B rechnet auf denselben Traces, kostet also nur Auswertung.~~
(UEBERHOLT durch par.6a: der erste Trace-Durchgang hat die Reihennummer nicht
mitgeschrieben, Teil B braucht einen zweiten Durchgang.) **Faellt Teil A flach
aus, ist Teil B gegenstandslos** -- ohne Verwerfungen gibt es nichts zu
etikettieren.

## par.6 STUFE 4 TEIL A GEMESSEN: die tiefere Suche ueberstimmt den Prior massiv (2026-09-01)

**BERICHTIGUNG 2026-09-01 (Pruefung der Preregs), VOR dem Lesen der Zahlen:**
die "200 Zustaende aus vier Dateien" sind keine 200. Das Artefakt
(`evaluations/artifacts/search_depth_rejection.json`, Muster
`selfplay_paritycheck-*.pkl`) liest zwei Paritaetslaeufe mit identischer
Konfiguration (20 Partien, 400 Sims, Seed 20260931, deterministisch, gleiches
Modell; `data/manifest_paritycheck-alt_*.json` und `-cscale_*.json`).
Nachgerechnet: die ersten 50 Drafting-Zustaende von `alt_g10` sind
zustandsgleich mit denen von `cscale_g10`, ebenso `g20`; ueber alle 200
Eintraege sind **89 verschieden**. Damit sind die vier "Bloecke" zwei
doppelt gezaehlte, die 200 Paare real hoechstens 100, die 74:6 real 37:3,
und p = 5,4e-16 (korrekt gerechnet fuer 80 diskordante Paare) real rund
2e-8 fuer 40. Das Verdikt (0,49 gegen 0,83) ueberlebt; die berichteten
Kennzahlen nicht. **Die Messung wird mit einem distinkten Zustandssatz
wiederholt (par.6b).** Die Zahlen unten bleiben als Erstfassung stehen.

Werkzeug: `tools/probes/search_depth_rejection_probe.py` (neu). 200
Drafting-Zustaende (Runden 2-4) aus b01-Self-Play bei Default-Knoepfen, jeder
Zustand ZWEIMAL getract mit gleichem Seed 20260931. Artefakt:
`evaluations/artifacts/search_depth_rejection.json` (Zeiger nachgetragen).

| Sims | Verwerfungsanteil (Zugwahl != Prior-Top-1) | Block-SE |
| --- | --- | --- |
| 100 | 0,4900 | 0,0173 |
| **400** | **0,8300** | 0,0058 |

**Gepaart, 200 Paare:** beide Stufen verwerfen 92-mal, **nur bei 400 Sims 74-mal,
nur bei 100 Sims 6-mal**. Differenz +0,34 (SE 0,038), McNemar auf den 80
diskordanten Paaren **p = 5,4e-16**.

**Die vorab registrierte Erwartung ist damit bestaetigt, und zwar deutlich:**
der Verwerfungsanteil steigt mit der Suchtiefe. In fuenf von sechs Zustaenden,
in denen sich die beiden Stufen unterscheiden, ist es die TIEFERE, die den
Prior-Vorschlag verwirft.

**Warum das die Delle verortet, ohne sie zu erklaeren:** der Prior traegt das
Spaltenwissen (par.2l: bei plattenblindem Prior tritt der Tiefeneffekt gar
nicht auf). Ein Eingriff an der Wurzelgewichtung (`c_scale`) und drei an der
Skala des Blattwerts sind wirkungslos (`PREREG_gumbel_c_scale_arm` par.5;
Zuordnung berichtigt 2026-09-01, siehe par.5). Hier zeigt sich, dass die
tiefere Suche den Prior haeufiger UEBERSTIMMT -- wo im Baum das entsteht, sagt
Teil A nicht.

**Was es NICHT zeigt:** dass die Suche unrecht hat. Die Tiefe gewinnt die
Arena (@25 verliert 11:29, signifikant; @100 verliert 33:47, p = 0,14, nur
Tendenz, par.2j2). 83 Prozent Verwerfung sind
fuer sich genommen die normale Arbeitsweise einer Suche, die besser sein soll
als ihr Prior.

**Einschraenkung, benannt -- und in der Erstfassung FALSCH benannt:** hier
stand "vier Dateien, vier Bloecke". Real waren es zwei identische Laeufe
(siehe Berichtigung oben). Dazu kommt, was auch fuer die Wiederholung gilt:
alle Zustaende liegen auf Trajektorien der TIEFEN Suche (argmax @400); der
100-Sims-Arm wird auf Stellungen befragt, die er selbst nicht unbedingt
erreicht haette.

**Teil B (Spalten-Etikett) bleibt offen** und braucht eine Zutat, die im
Trace nicht steht: die Abbildung von der bedienten MUSTERREIHE auf die
Kuppelzelle, die ihre Vollendung fuellen wuerde. Die `description` der
Kandidaten nennt die Reihe ("... -> Reihe 6 [5/6]"), die Zielzelle haengt aber
an Farbe und Slot-Belegung. Diese Zuordnung wird an der Quelle geprueft, nicht
geraten -- sonst steht am Ende ein Etikett, das die Frage selbst beantwortet.

## par.6b STUFE 4 TEIL A WIEDERHOLT auf 200 DISTINKTEN Zustaenden: Verdikt haelt (2026-09-01, abends)

**Zustandssatz neu erzeugt**, weil im Baum kein b01-Korpus bei Default-Knoepfen
mehr lag: 80 Partien `v23-b01_brierbest` argmax @400, `--deterministic
--no-root-noise`, Seed 20260907, `--per-file 10`, `MOSAIC_STACK_DRAW_RESEARCH=1`
(`data/manifest_s4states-v23b01_20260901_222208.json`, Dateien
`selfplay_s4states-v23b01_*.pkl`, 8 Dateien; 1.161 s, 14,5 s je Partie unter
leichter Nebenlast). Die Sonde dedupliziert seit heute ueber einen
Zustands-Hash (auch innerhalb einer Datei: 32 Duplikate uebersprungen) und
schreibt den exakten McNemar-Test ins Artefakt
(`evaluations/artifacts/search_depth_rejection_v2.json`, Seed 20260931,
25 Zustaende je Datei, Runden 2-4, Laufzeit 1.924 s einkernig).

| Sims | Verwerfungsanteil | Block-SE (8 Dateien) |
| --- | --- | --- |
| 100 | 0,4900 | 0,0398 |
| **400** | **0,8250** | 0,0199 |

**Gepaart, 200 distinkte Paare:** beide verwerfen 95-mal, **nur @400 70-mal,
nur @100 3-mal**; Differenz +0,335 (SE 0,036); McNemar exakt auf 73
diskordanten Paaren **p = 1,4e-17**.

**Verdikt unveraendert, jetzt auf sauberer Basis:** die tiefere Suche
verwirft den Prior-Top-1 fast doppelt so oft; in 70 von 73 diskordanten
Faellen ist es die tiefere Stufe. Die Erstfassung (par.6) hatte dieselben
Anteile aus doppelt gezaehlten Zustaenden; ihre Kennzahlen sind durch diese
ersetzt, wo sie zitiert werden (STATUS, Kopf). Der Vorbehalt aus par.6 bleibt:
alle Zustaende liegen auf Trajektorien der tiefen Suche.

**Teil B** (Spalten-Etikett) faehrt auf DIESEM Zustandssatz, mit der
Definition aus par.6a, und braucht den zweiten Trace-Durchgang mit
Reihennummer.

## par.6a DEFINITION VON "SPALTENRELEVANT" BERICHTIGT (2026-09-01)

Die in par.5 vorab festgelegte Definition sprach von der Kuppelzelle, "die
die Vollendung der Musterreihe fuellen wuerde". **Am Regelwerk geprueft
(`docs/engine_manual.md`, Abschnitt "Phase 2: Tiling") ist diese Zelle zum
Drafting-Zeitpunkt NICHT bestimmt:**

* Die ZEILE steht fest -- Musterreihe `r` gehoert zur Kuppelzeile `r` ("all 3
  Kuppelplatten of a row's dome row").
* Die SPALTE nicht: platziert wird, wo die Farbe der Reihe auf eine freie
  passende Zelle einer Kuppelplatte trifft; liegen mehrere passende Zellen
  vor, entscheidet die Tiling-Wahl (eigener Einstieg
  `tiling_choice_state_json`), und ob ueberhaupt platziert wird, haengt an der
  Plattenbelegung der Zeile.

**Berichtigte Definition, weiterhin VOR jeder Messung festgelegt:**

> Ein Zug heisst SPALTENRELEVANT, wenn er eine Musterreihe `r` bedient, deren
> Kuppelzeile `r` mindestens eine offene Zelle in einer Spalte mit Fuellstand
> >= 4 hat.

Also "kann eine fast volle Spalte voranbringen" statt "wird sie
voranbringen". Das ist schwaecher, aber es ist die staerkste Aussage, die der
Zustand zum Zeitpunkt der Zugwahl hergibt -- und sie bleibt aus `col_fill` und
`col_open_cells` des Praedikats berechenbar, ohne Engine-Nachbau.

**Warum das die Frage nicht vorwegnimmt:** die Definition kennt weder Prior
noch Suchwahl. Sie etikettiert Zuege allein aus dem Zustand; welcher Zug
verworfen wurde, entscheidet der Trace.

**Teil B bleibt damit fahrbar**, kostet aber einen zweiten Durchgang: die
Traces von par.6 haben die `description` der Kandidaten gespeichert, nicht die
Zeilennummer -- der naechste Lauf muss sie mitschreiben (Reihe steht im
Klartext der Beschreibung, z.B. "-> Reihe 6 [5/6]").
