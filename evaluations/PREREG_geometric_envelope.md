<!-- STATUS: OFFEN | Frage: Hilft ein GEOMETRISCHES Gelaender -- die Dreiecks-Einhuellende, frueh stark und ueber die Runden abklingend -- dort, wo der Value-Kopf am wenigsten weiss (Runde 1-2)? | Beleg: NICHTS GEBAUT, angelegt 2026-08-31 auf Nutzer-Auftrag. Motiv: Spalten-AUC 0,698 in R1 gegen 0,886 in R5, Abweichungen multiplizieren sich (0,6^k), und ab R5 rechnet round5.rs exakt -- das Gelaender UMGEHT den gedaempften Plattenlohn-Kanal, statt ihn zu reparieren. Drei Bausteine (par.3), Pflicht-Auflagen inkl. Potentialform (par.4), Stufenplan mit Toren (par.5). -->

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
dieselbe Neigung (`PREREG_heuristic_v2_long_rows.md` par.3a). Es gibt **vier
Orientierungen** (je 21 Zellen, je eine volle Zeile plus eine volle Spalte an
ihrer Ecke); praktisch bedienbar sind oben-links und oben-rechts, also
Spalte 0 und Spalte 5 als Anker.

| Baustein | Stand |
| --- | --- |
| **(a) Huellen-Trimm der Ownership-Loss-Maske** | REGISTRIERT (Lehrer-Prereg, Nachtrag 6) -- nicht Gegenstand dieser Datei |
| **(b) Einhuellende als 2D-Eingabeebene** | Merkposten seit 2026-08-24, hier erstmals registriert |
| **(c) Rundenabklingendes Gelaender** | neu (par.2m des Suchtiefen-Strangs), hier erstmals registriert |

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
ist:** welche der vier Huellen ein Spieler verfolgt, ist eine WAHL. Vier
Ebenen (oder zwei fuer die bedienbaren) plus der Brettzustand sagen etwas
ueber Passung, nicht nur ueber Geometrie.

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

**Stufe 1 -- Eingabeebene (b).** Zwei bis vier binaere Ebenen
(Orientierungen), additiv. Tor: **Paritaets-Gate zuerst** (Netz ohne die
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
