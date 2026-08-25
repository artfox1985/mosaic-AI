<!-- STATUS: ENTSCHIEDEN | Frage: Wie wird das v22-Trainingsfenster zugeschnitten? | Beleg: NEU GEFASST 2026-08-25, der Zuschnitt von 2026-08-08 ist HINFAELLIG -- er war fuer einen NETZ-Erzeuger mit Zwei-Klassen-Rotation ueber drei Generationen gebaut (29.450 Partien), v22 ist ein HEURISTIK-Erzeuger (v2huelle), EINE Klasse, KEIN Altbestand (Nutzer 2026-08-25). Gueltiger Zuschnitt: 24.000 Partien, ~4,18 Mio Zustaende, ~37 GB, ein Lauf mit Seed 20260826, Praefix hv2. Die Rotationsregel ab v22 ist ebenfalls hinfaellig: v22 ist ein Schnitt, keine Rotationsstufe. OFFEN als vorregistrierter Arm INNERHALB dieses Zuschnitts ist allein die TRAEGERFRAGE -- 61,8 Prozent der Draftingzuege mit echter Wahl tragen policy_target_valid=false (v2-Vorzug); ob der Policy-Kopf sie sieht, entscheidet ein gepaartes Trainingspaar auf DEMSELBEN Korpus, Entscheidungsmass vorab festgelegt (par.4). ARM A GEFAHREN 2026-08-25 (par.4a, Flagge geachtet, 5.700 Partien, from-scratch): vom Lehrer kommt NICHTS an -- volle Spalten 0,062 gegen 0,741 im Korpus, Punkte 21,8 gegen 47,0, Strafleiste 9,0 gegen 5,0 -- also CHAMPION-Niveau (0,106), nicht Lehrer-Niveau. BERICHTIGT: die erste Messung lief mit Sampling und Wurzelrauschen und mass damit die EXPLORATION; argmax wie in der Arena gibt 6,7 Punkte und mehr als doppelt so viele volle Spalten. Einschraenkung schwer: from-scratch auf einem Viertel des Korpus, bestes Modell Epoche 4, n=40. Der Befund ist damit KEIN Beleg gegen die Destillation, sondern zeigt, dass der Policy-Kopf unter Arm A nur gut ein Drittel des Draftingmaterials sieht -- ausgeblendet sind ausgerechnet die Vorzugszuege. ARM B GEFAHREN (par.4b): mit identischen Flags gemessen, VIER Kennzahlen in derselben Richtung -- volle Spalten 0,113 gegen 0,062, volle Reihen 0,225 gegen 0,113, Punkte 27,3 gegen 21,8. Keine davon einzeln signifikant (n=40, Intervalle ueberlappen). VORLAEUFIGE ANTWORT: die Maske blockiert den Lehrer, also faellt die Traegerfrage auf IGNORIEREN -- gegen die Empfehlung, die im ersten Zuschnitt stand. Beide Arme bleiben aber weit unter dem Lehrer (0,113 gegen 0,741); ob der Rest Datenmenge ist oder eine Grenze der Destillation, trennt dieser Lauf nicht. Richtungsentscheid, kein Gating. Der Bootstrap-Horizont-Wecker ist erledigt: Horizont 2, PREREG_bootstrap_horizon.md par.9f. par.6 (2026-08-25): WARMSTART vom Sanity-Modell hv2sanity geplant; weil dessen Korpus im vollen Fenster VOLLSTAENDIG drinbleibt (anders als bei bisherigen Warmstarts, wo der Vorgaenger-Korpus ausrotiert), waeren ~21 Prozent des Val-Splits vom Startmodell bereits trainiert und die --select-by-brier-Auswahl verzerrt. Gegenmittel GEBAUT und auf dem echten Codepfad abgenommen: MOSAIC_VAL_POOL schraenkt die Val-Kandidaten per Regex ein und bricht ab, statt still einen kleineren Split zu nehmen. Vorbereiteter Pool: evaluations/artifacts/hv2_val_pool_regex.txt. -->

# Vorregistrierung: v22-Fenster

**Neu gefasst am 2026-08-25**, unmittelbar vor und waehrend der Erzeugung.
Der Zuschnitt von 2026-08-08 steht unten als Altstand und ist NICHT mehr
gueltig; seine Begruendung zum Schwarm-Anteil wird aufgehoben, weil sie
wieder greift, sobald Netz-Self-Play zurueckkehrt.

## par.1 Warum der alte Zuschnitt hinfaellig ist

Drei Praemissen sind weggefallen, alle drei ohne Zutun dieses Dokuments:

1. **Der Erzeuger ist nicht mehr das Netz.** v22 wird von der Heuristik
   `v2huelle` erzeugt, nicht vom v21-Champion. Grund: der Champion vollendet
   keine Spalten (0,050 je Partie), der Lehrer schon (0,741). Ohne
   Spaltenvollendungen im Korpus hat der Value-Kopf nie gesehen, was eine
   Spalte wert ist.
2. **Es gibt keine zwei Klassen mehr.** `--value-only` existiert nur unter
   `--mode network` (`self_play.py:732`); im Heuristik-Modus ist es nicht
   verfuegbar. Sockel und Schwarm lassen sich also nicht mehr ueber die
   ERZEUGUNG trennen. Das ist kein Verlust: die Traeger-Auswahl geschieht
   ohnehin erst beim Training ueber die Manifeste.
3. **Kein Altbestand** (Nutzer-Entscheid 2026-08-25). Der gesamte Altbestand
   stammt aus plattenblindem Spiel -- genau der Verteilung, die v22 ersetzen
   soll. Damit entfaellt die Rotationsmechanik: **v22 ist ein Schnitt, keine
   Rotationsstufe.** Die "stationaere Rotationsregel ab v22" unten ist
   gegenstandslos.

## par.2 Gueltiger Zuschnitt

| | |
|---|---|
| Erzeuger | Heuristik `v2huelle` + Champion-Labels (`alphazero_v21_2d_brierbest.onnx`) |
| Aufruf | `--mode mcts --heuristik-variante v2huelle --sims 600 --threads 11 --version hv2 --per-file 10` |
| Partien | **24.000**, ein Lauf, Seed 20260826 |
| Bootstrap-Horizont | **2** (`PREREG_bootstrap_horizon.md` par.9f) |
| Blindzieh-Knopf | **AUS** (`PREREG_stack_draw_reservation_rule.md` par.5d) |
| Zustaende | ~4,18 Mio (174,2 Records je Partie, gemessen) |
| Plattenplatz | ~37 GB (308 MB je 200 Partien, gemessen) |
| Altbestand | **keiner** |

**Warum 24.000:** Volumen ist ein gemessener Hebel (Dosis-Befund 6/6 auf beiden
Orakelmetriken, arena-bestaetigt 479:321). Die Obergrenze setzt der
Fenster-Cache: bei ~6 KB je Zustand liegen 4,18 Mio Zustaende bei ~25 GB gegen
32 GB RAM. 30.000 Partien sprengen das.

## par.3 Was der Korpus enthaelt (gemessen, 270 Partien des laufenden Korpus)

| Kennzahl | `v2huelle` | `v1`-Kontrolle |
| --- | --- | --- |
| volle Spalten je Seite | **0,741 ± 0,068** | 0,050 |
| k1-Punkte / Anteil Partien mit Ertrag | **+5,48 / 55,2 %** | +0,35 / 5,1 % |
| Strafleistensteine je Partie und Seite | **5,04** | 10,30 |
| Eigene Punkte | **46,97** | 20,91 |
| distinkte Brettzustaende (je 200 Partien) | **6.164** | 6.008 |

Struktur-Abnahme bestanden: zero-mask 0, policy leak 0,000000, keine NaN/Inf,
0 abgeschnittene Partien, alle Partien erreichen Runde 5.

## par.4 OFFENER ARM: traegt der Vorzug Policy? (vorregistriert, nicht gefahren)

**61,8 Prozent** der Draftingzuege mit echter Wahl sind Vorzugszuege und
tragen `policy_target_valid=false`; `neural_net.py:1858` setzt deren
Policy-Gewicht auf 0. Die Flagge steht JE RECORD -- die Entscheidung ist
deshalb NICHT im Korpus zementiert, sondern ein Trainings-Schalter.

Beide Lesarten sind ernsthaft:

* **Flagge achten**: der Policy-Kopf sieht nur die ~38 Prozent such-getriebenen
  Zuege. Er lernt das Routing nicht, aber auch nicht das Routing OHNE das
  Urteil dahinter.
* **Flagge ignorieren**: klassische Verhaltensklonung des Lehrers -- genau das,
  wofuer ein Lehrer-Korpus da ist. Preis: das Ziel ist auf 62 Prozent der
  Zuege eine reine Eins.

**Aufbau:** zwei identische Trainings auf DEMSELBEN Korpus, ein Schalter
Unterschied, gepaarte Seeds (>= 6, Seed-Varianz-Regel).

**Entscheidungsmass, VORAB festgelegt** (Regel: das Mass wird vor dem Lauf
benannt): `prior_mass_on_oracle_top3` und `kendall_tau`. Begruendung fuer
genau diese: sie sind im Regime "gleiche Architektur, verschiedene Daten"
**7/7** Arena-Praediktoren -- und dieses Regime liegt hier exakt vor.
`policy_top3` ist AUSGESCHLOSSEN (zeigte 6/6 auf den VERLIERER),
`value_r2_rounds_1_4` ebenfalls (unterhalb ~0,015 Abstand 0/3).
Bei Gleichstand beider Orakelmetriken entscheidet die gepaarte Arena.

## par.5 Was an die Stelle der Rotationsregel tritt

Nichts -- vorerst mit Absicht. v22 ist ein Schnitt: das Fenster besteht aus
genau einem Korpus. Eine Rotationsregel wird erst wieder gebraucht, wenn es
eine zweite Generation im selben Regime gibt; sie dann aus dem Altstand unten
zu uebernehmen waere falsch, weil der fuer ZWEI Erzeugungsklassen geschrieben
ist, die es im Heuristik-Modus nicht gibt.

---

# ALTSTAND (2026-08-08) -- NICHT GUELTIG

Aufgehoben wegen der Schwarm-Anteils-Begruendung, die wieder greift, sobald
Netz-Self-Play zurueckkehrt. Der Zuschnitt selbst ist durch par.2 ersetzt.

## Fenster (29.450 Partien, 2.945 Dateien -- identische Form wie v21)

| Klasse | Quelle | Partien | Dateien | Sims | Policy |
|---|---|---|---|---|---|
| Sockel NEU | `v21wdl` (Generator = v21-Champion) | 4.000 | 400 | 600 | aktiv |
| Sockel-Traeger Gen-1 | `v20wdl` (Manifest) | 1.350 | 135 | 600 | aktiv |
| Sockel-Traeger Gen-2 | `v19wdl` (Manifest) | 450 | 45 | 600 | aktiv |
| Schwarm NEU | `v21wdlsw` (`--value-only`) | 8.000 | 800 | 150 | maskiert |
| Schwarm Gen-1 | `v20wdlsw` (komplett) | 8.000 | 800 | 150 | maskiert |
| Sockel-Rest Gen-1 | `v20wdl` (Nicht-Traeger) | 2.650 | 265 | 600 | maskiert |
| **Sockel-Rest Gen-2** | `v19wdl` (Nicht-Traeger, VOLLSTAENDIG) | **3.550** | 355 | 600 | maskiert |
| **Schwarm-Rest Gen-2** | `v19wdlsw` (Auffuellung) | **1.450** | 145 | 150 | maskiert |

Policy-Klasse 5.800 | Value-Klasse 23.650 | Summe 29.450.
Vollstaendig ROTIERT AUS: `v18` (und alles Aeltere), sowie 6.550 der
8.000 `v19wdlsw`-Partien.

## Begruendung des juengsten Postens (Nutzer-Entscheid)

Der 5.000er-Posten der aeltesten Stufe wird NICHT aus dem
Gen-2-Schwarm gefuellt, sondern zuerst aus dem Gen-2-SOCKEL-Rest
(3.550 Partien @600, vollstaendig) und nur zum Auffuellen aus dem
Gen-2-Schwarm (1.450 @150). Wirkung auf den Schwarm-Anteil der
Value-Klasse:

| Variante | Schwarm-Anteil der Value-Klasse |
|---|---|
| v21 (Ist) | 16.000 / 23.650 = 68% |
| v22 mit 5.000 Gen-2-Schwarm | 21.000 / 23.650 = 89% |
| **v22 wie gewaehlt** | **17.450 / 23.650 = 74%** |

Damit bleibt der Anteil naeherungsweise stabil statt Richtung 90% zu
laufen. Die Value-ZIELE sind sim-robust (Bootstrap = Forward-Pass am
Rundenuebergang, plus Ausgang) -- der Grund fuer die Wahl ist die
ZUSTANDSVERTEILUNG: ein ueberwiegend aus 150-Sim-Partien bestehendes
Fenster kalibriert den Value-Kopf auf schwaechere Trajektorien, waehrend
der Champion mit 400-600 Sims spielt. Volumen bleibt bei 29.450
(Dosis-Befund: Volumen half 6/6).

## Rotationsregel ab v22 (stationaer, gilt fuer alle Folgegenerationen)

Ab v22 ist die Fensterform selbstaehnlich -- v21 war die letzte
Uebergangsgeneration (v18 war noch kein Zwei-Klassen-Korpus und lieferte
seine 5.000 daher komplett aus Voll-Such-Partien):

- Policy: 4.000 neuer Sockel + 1.350 Gen-1-Sockel (135 Dateien,
  seed-bestimmt) + 450 Gen-2-Sockel (45 Dateien).
- Value: 8.000 neuer Schwarm + 8.000 Gen-1-Schwarm + Gen-1-Sockel-Rest
  (2.650) + Gen-2-Sockel-Rest (3.550) + Gen-2-Schwarm-Auffuellung auf
  23.650 (1.450).
- Gen-3 und aelter rotieren vollstaendig aus; Backup-Bestaende kehren
  nie zurueck.

## Umsetzung

`data/policy_carrier_manifest_v22.json` mit
`carrier_prefixes: ["selfplay_v21wdl_"]` (Unterstrich-Grenze!) plus der
seed-bestimmten Traeger-Liste (135 `v20wdl`- + 45 `v19wdl`-Dateien),
Traeger-Seed hiermit auf **20260901** festgelegt. Fenster-Pin per
`MOSAIC_DATA_EXCLUDE` gegen alles, was NICHT im Fenster ist (v18,
`v19wdlann`, die 6.550 nicht genutzten `v19wdlsw`-Partien, sowie alle
waehrend der Generierung noch wachsenden Tags) -- Regex bei jedem
Trainings-Start NEU aus dem Ist-Bestand ableiten (stehende Regel).

## Vorbehalt: was passiert, wenn das v21-Gating H0 ergibt?

Dann gibt es KEINEN v21-Champion, und der Generator bleibt
`v20_2d_opp_brierbest`. Die Namenskonvention (Dateien nach dem
GENERATOR) wuerde die neuen Partien wieder `v20wdl*` nennen und mit dem
Bestand KOLLIDIEREN. Festlegung fuer diesen Fall: neuer Batch desselben
Generators erhaelt ein Unterscheidungs-Suffix (`v20wdlb` /
`v20wdlbsw`), und die Rotationsregel verschiebt sich um eine
Generation (Gen-1 = v20-Erstbatch, Gen-2 = v19). Das ist eine
Namens-, keine Design-Aenderung.


## par.6 WARMSTART-VORBEREITUNG: der Val-Pool (Nutzer-Entscheid 2026-08-25)

**Plan:** ein Sanity-Modell (`hv2sanity`) auf dem bis dahin erzeugten Teil des
Korpus, und -- wenn es vernuenftig aussieht -- der volle v22-Lauf als
WARMSTART von diesem Modell.

**Das Problem, das dabei entsteht, und es liegt hier anders als bei den
bisherigen Warmstarts.** Sonst rotiert der Korpus des Vorgaengermodells beim
naechsten Fenster groesstenteils AUS. Hier bleibt er vollstaendig DRIN:
`hv2sanity` trainiert auf 513 Dateien, die im vollen Lauf alle wieder dabei
sind. Ein frei gezogener Val-Split enthaelt dann Dateien, die das Startmodell
bereits trainiert hat:

| | |
| --- | --- |
| voller Korpus | 2.400 Dateien |
| Val-Split bei `--val-frac 0.1` | 240 Dateien |
| davon von `hv2sanity` bereits trainiert | ~240 x 513/2400 ~ **51**, also ~21 Prozent |

`--select-by-brier` waehlt den Checkpoint AUF diesem Mass -- die Auswahl waere
systematisch zugunsten spaeter Epochen verzerrt.

**Gebaut 2026-08-25: `MOSAIC_VAL_POOL`** (train.py, additiv, Default ungesetzt
= bestandsidentisch). Ein Regex schraenkt die KANDIDATEN des Val-Splits ein;
alles, was nicht matcht, geht garantiert in den Trainings-Teil. Trifft der
Regex weniger Dateien als der Split braucht, bricht der Lauf AB statt still
einen kleineren Val-Split zu nehmen -- ein kleinerer Split waere ein anderes
Mass als das registrierte.

**Abgenommen auf dem echten Codepfad** (nicht nur am Regex): Lauf mit
gesetztem Pool meldete "Val-Split aus 71 von 570 Kandidaten gezogen (57
Val-Dateien); die uebrigen 499 gehen garantiert ins Training."

**Vorbereiteter Aufruf fuer den vollen Lauf** (Pool =
`evaluations/artifacts/hv2_val_pool_regex.txt`, das ist genau der
"g > 5700"-Teil, also alles, was `hv2sanity` nie gesehen hat; 1.830 Kandidaten
fuer 240 Val-Dateien):

```
export MOSAIC_VAL_POOL="$(cat evaluations/artifacts/hv2_val_pool_regex.txt)"
python -u train.py --name v22 --load hv2sanity_best --encoder 2d --value-head wdl     --select-by-brier --lr-schedule cosine --epochs <N> --seed <S>
```

Geprueft: keine der `hv2sanity`-Dateien faellt in den Pool, alle Dateien ab
g5710 schon.

**Nicht vergessen:** der Val-Pool gehoert ins Trainings-Manifest, damit er
spaeter nachvollziehbar ist. Ist eingebaut (`"val_pool"` in den CLI-Args).


### par.4a ARM A GEFAHREN (2026-08-25): Flagge geachtet -- der Lehrer kommt nicht an

Unfreiwillig zuerst gefahren, als Sanity-Training auf dem bis dahin erzeugten
Korpusteil (570 Dateien = 5.700 Partien, gepinnt per `MOSAIC_DATA_EXCLUDE`).
From-scratch, 2D, WDL-Kopf, 20 Epochen, Seed 20260825; bestes Modell Epoche 4.
Das Training hat die Flagge GEACHTET, ist also Arm A.

**40 Partien mit `hv2sanity_best`, 400 Sims.**

**BERICHTIGUNG (Nutzer-Einwand 2026-08-25):** die erste Messung lief als
normales Netz-Self-Play, also mit **Sampling und Wurzelrauschen** -- gemessen
war damit das Netz beim EXPLORIEREN, nicht beim Spielen. Die Arena spielt
argmax ohne Rauschen. Wiederholt mit `--deterministic --no-root-noise`
("rauschfreie Trajektorien wie in der Arena", Flag-Hilfetext), gleicher Seed:

| Kennzahl | gesampelt (verworfen) | **argmax (gueltig)** | Lehrer im Korpus | Champion v21 |
| --- | --- | --- | --- | --- |
| volle Spalten | 0,025 | **0,062 ± 0,053** | 0,741 | 0,106 |
| volle Reihen | 0,037 | 0,113 ± 0,078 | 0,128 | – |
| Strafleistensteine | 11,55 | **8,96** | 5,04 | – |
| Eigene Punkte | 15,09 | **21,77** | 46,97 | – |
| k6 Spezialfelder | −12,53 | −12,35 | −9,77 | – |

**Das Sampling hat das Netz um 6,7 Punkte schlechter aussehen lassen und die
vollen Spalten mehr als halbiert.** Wer ein Netz an aufgezeichnetem Self-Play
misst, misst seine Exploration -- die Lehre gilt ueber diesen Arm hinaus.

**Am Schluss aendert das nichts:** 0,062 liegt auf CHAMPION-Niveau (0,106,
Intervalle ueberlappen), nicht auf Lehrer-Niveau. Der Spaltenbau ist nicht
angekommen.

**Nicht ablesbar** ist dagegen, ob die REIHEN angekommen sind: 0,113 liegt
zwischen v1 (0,092) und Lehrer (0,128), bei ±0,078 ist das nicht trennbar.

**Vom Lehrer ist nichts angekommen.** Das Netz spielt sogar schwaecher als der
Champion.

**Was das NICHT belegt**, und die Einschraenkungen wiegen schwer:

* **From-scratch auf 5.700 Partien** ist ein schwacher Spieler -- der Champion
  steht auf Zehntausenden plus langer Warmstart-Kette. Ein Teil des Abstands
  misst Datenmenge, nicht den Lehrer.
* **Bestes Modell Epoche 4** von 20.
* **n=40**, die Intervalle sind breit (±0,034 auf 0,025).

**Was es sehr wohl zeigt:** der Policy-Kopf hat nur gut ein Drittel des
Draftingmaterials gesehen, und ausgeblendet waren ausgerechnet die
Vorzugszuege -- also genau die, die den Spaltenbau AUSMACHEN. Damit ist Arm A
kein neutraler Referenzpunkt, sondern die Bedingung, unter der der Lehrer
strukturell nicht ankommen KANN.

### par.4b ARM B laeuft (2026-08-25): Flagge ignoriert

Gebaut: `MOSAIC_IGNORE_POLICY_TARGET_VALID=1` (neural_net.py). Setzt **genau
diese eine** Maskierung aus; die uebrigen Nullsetzungen (Tiling/Start,
Traeger-Manifest, PCR) bleiben unberuehrt, sonst waere es ein anderer Arm als
der registrierte. Der Schalter steht im **Cache-Schluessel**
(`+ignore_ptv_v1`) -- ohne das haette der zweite Lauf still den Cache des
ersten gezogen, in dem die Gewichte bereits genullt sind, und ein
Nullergebnis geliefert, das nichts bedeutet.

Alles uebrige identisch: gleicher Pin, gleicher Seed, gleiche Epochenzahl,
gleiche Architektur. Ein Flag Unterschied.

**Vorsicht bei der Auswertung:** dieser Vergleich ist wegen der oben genannten
Einschraenkungen ein RICHTUNGSTEST, kein Gating. Er beantwortet "erreicht der
Vorzug die Policy ueberhaupt", nicht "ist Arm B staerker".

### ERGEBNIS ARM B (2026-08-25): die Maske hat den Lehrer blockiert

Gemessen mit IDENTISCHEN Flags wie Arm A -- `--deterministic --no-root-noise`,
Seed 20260901, 40 Partien, 400 Sims. Unterschied zwischen den Armen: ein
Trainings-Flag.

| Kennzahl | Arm A (Flagge geachtet) | **Arm B (ignoriert)** | Lehrer | Champion |
| --- | --- | --- | --- | --- |
| volle Spalten | 0,062 ± 0,053 | **0,113 ± 0,085** | 0,741 | 0,106 |
| volle Reihen | 0,113 ± 0,078 | **0,225 ± 0,110** | 0,128 | – |
| Eigene Punkte | 21,77 ± 3,10 | **27,25 ± 3,31** | 46,97 | – |
| Strafleistensteine | 8,96 | 8,81 | 5,04 | – |

**Vier Kennzahlen, vier mal dieselbe Richtung** -- Spalten fast verdoppelt,
Reihen verdoppelt, +5,5 Punkte. **Einzeln ist keine davon signifikant**, alle
Intervalle ueberlappen bei n=40. Dass vier Groessen gemeinsam wandern, wiegt
mehr als jede einzelne, ist aber kein Ersatz fuer Signifikanz.

**Vorlaeufige Antwort auf die Traegerfrage: die Maske blockiert den Lehrer.**
Das steht gegen die Empfehlung, die im ersten Zuschnitt dieses par.4 stand --
dort war das Markieren als "vorgeschlagene Variante" begruendet mit dem
Argument, ein one-hot-Ziel lehre "das Routing ohne das Urteil dahinter". Die
Messung sagt: ohne das Routing lernt es gar nichts.

**Was weiterhin offen ist.** Beide Arme liegen weit unter dem Lehrer (0,113
gegen 0,741). Arm B erreicht Champion-Niveau, nicht Lehrer-Niveau. Ob der
Abstand an der Datenmenge liegt (5.700 von 24.000 Partien, from-scratch) oder
daran, dass die Destillation den Vorzug grundsaetzlich nicht traegt, trennt
dieser Lauf NICHT.

**Konsequenz fuer den vollen Korpus:** die Entscheidung faellt auf Arm B --
also `MOSAIC_IGNORE_POLICY_TARGET_VALID=1` --, aber als Richtungsentscheid mit
n=40 auf einem Viertelkorpus, nicht als Gating. Wer die Frage endgueltig
beantworten will, braucht beide Arme auf dem vollen Korpus; das kostet nach
heutigem Stand zweimal ~7 h und ist der Grund, warum
`PREREG_cache_build_time.md` existiert.
