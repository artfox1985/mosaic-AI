<!-- STATUS: ENTSCHIEDEN | Frage: Wie wird das v22-Trainingsfenster zugeschnitten? | Beleg: ZUSCHNITT ENTSCHIEDEN 2026-08-25 (par.2): 24.000 Partien hv2, EINE Klasse, KEIN Altbestand, ~4,18 Mio Zustaende, ~14,1 GB Cache. Der Rotations-Zuschnitt von 2026-08-08 war fuer einen NETZ-Erzeuger gebaut und ist hinfaellig; v22 ist ein Schnitt, keine Rotationsstufe. OFFEN darin nur die TRAEGERFRAGE (par.4): 61,8 Prozent der Draftingzuege tragen policy_target_valid=false. A/B gefahren (par.4a/4b, from-scratch auf 5.700 Partien, je 40 Partien argmax gemessen): Arm B (Flagge ignoriert) besser in vier Kennzahlen -- volle Spalten 0,113 gegen 0,062, Reihen 0,225 gegen 0,113, Punkte 27,3 gegen 21,8 -- keine davon einzeln signifikant. Richtungsentscheid: IGNORIEREN. ABER beide Arme bleiben auf Champion-Niveau (0,106) statt Lehrer-Niveau (0,741), und par.4e erklaert warum: im Tiling ist nur der VALUE-Kopf aktiv, und der bricht bloss Gleichstaende unter punktegleichen Zuegen in Runde 2-4; Punkte-Kopf und Ownership-Pol waren NIE aktiv, und nur der Ownership-Pol koennte Sofortpunkte gegen Struktur eintauschen -- genau den Tausch verlangt Spaltenbau. Naechste Konfiguration daher Arm B PLUS OWNERSHIP_WEIGHT>0 (par.3b der Lehrer-Prereg). par.4c und par.4d sind ueberholte Zwischendeutungen, par.4e ist der Stand. par.4f SPLIT-TEST GEFAHREN 2026-08-26 und er KEHRT die Vorhersage von par.4c UM: die Huelle im DRAFTING allein, mit V1-Tiling, bringt 0,756 volle Spalten gegen 0,044 der V1-Kontrolle (delta +0,713, t 10,29) -- das ist der von par.4c benannte Nahe-0,7-Fall, also traegt das DRAFTING den Loewenanteil, nicht das Routing. Das Routing ALLEIN (Huelle nur im Tiling, V1-Drafting) bringt exakt NICHTS: 0,113 gegen 0,113, delta 0,000, t 0,00. Gekoppelt sind es 0,975 gegen 0,062 (delta +0,912); die Luecke von +0,199 zur Summe der Einzelteile ist eine WECHSELWIRKUNG -- das Routing zahlt sich nur aus, wenn das Drafting die passenden Steine liefert. Folge fuer die Netz-Seite: die hartverdrahtete V1-Kachelung (self_play.rs:2866/3088/3095/3795/3802) kostet weniger als par.4c annahm, und der Kanal, ueber den das Netz erben kann, ist der Policy-Kopf im Drafting -- der ist offen. par.6: Warmstart-Val-Pool gebaut (MOSAIC_VAL_POOL). -->

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


### par.4c STRUKTURBEFUND (2026-08-25): das Netz KANN den Lehrer nicht erben

Nutzer: *"was mich eher irritiert ist das selbst ohne flag die spalten vom
netz nicht gebaut werden"*. Der Grund ist am Code gefunden und hat mit
Datenmenge nichts zu tun.

**Der v2-Durchbruch kommt vom PLATZIERUNGS-Routing** (Lehrer-Prereg: "der
Durchbruch kam durchgehend vom ROUTING, nie von einem Bewertungsterm"), also
vom Tiling. Und dieses Routing ist dem Netz an ZWEI Stellen zugleich
verschlossen:

1. **Beim Spielen.** `play_net_self_play_game` setzt fuer BEIDE Spieler
   `heuristik_variante: HeuristikVariante::V1` (self_play.rs:3795 und 3801).
   Das Tiling des Netzes laeuft damit ueber den V1-Pfad -- exakter DFS-Loeser
   mit Netz-Tiebreak -- und NICHT ueber `v2_tiling_preference`. Dasselbe gilt
   in der Arena (self_play.rs:2821, Netz-Seite ebenfalls V1).
2. **Beim Lernen.** Tiling-Records tragen IMMER `pol_w = 0.0` (maskiert als
   "Tiling/Start-Schritte", unabhaengig von der Traegerflagge). Das Routing
   des Lehrers hinterlaesst im Policy-Ziel also **ueberhaupt keine Spur**.

**Daraus die Vorhersage, die zu den Messungen passt:** das Netz erbt nur die
DRAFT-Haelfte des Lehrers und spielt Tiling wie der Champion. Gemessen: Arm B
0,113 volle Spalten, Champion 0,106, Lehrer 0,741.

**Was das fuer die Traegerfrage bedeutet.** Der A/B-Befund bleibt gueltig --
die Maske kostet messbar, Arm B ist besser als Arm A. Aber die Deckelung
liegt woanders: **auch Arm B kann den Lehrer nicht erreichen, weil ihm der
Mechanismus fehlt, der die Spalten erzeugt.** Mehr Korpus verschiebt das
nicht.

**Der entscheidende Test ist billig und netzfrei** (ungebaut, hier
vorregistriert): die Heuristik mit `v2huelle` im DRAFTING, aber `V1` im
TILING laufen lassen -- der Zuschnitt ist vorhanden, `PlayerLoopConfig`
traegt beide Angaben getrennt. Das spaltet die 0,741 in ihre beiden Haelften.

* **Ergebnis nahe 0,1** ⇒ das Routing traegt den Loewenanteil. Dann ist mehr
  Korpus die falsche Antwort, und die Frage lautet: bekommt die Netz-Seite
  das v2-Tiling, oder lernt der Policy-Kopf Tiling-Ziele (heute maskiert)?
* **Ergebnis nahe 0,7** ⇒ das Drafting traegt es, das Netz muesste es also
  lernen koennen -- dann sind Datenmenge und Trainingsdauer wieder die
  Verdaechtigen.

**Vorher NICHTS bauen.** Beide Folgewege -- Netz-Seite auf v2-Tiling
umstellen oder Tiling-Policy-Ziele freischalten -- sind Eingriffe in den
Elo-Anker bzw. in das Trainingsziel; welcher ueberhaupt lohnt, entscheidet
diese eine Messung.


### par.4d BERICHTIGUNG zu par.4c (Nutzer-Einwand 2026-08-25): es GIBT einen Kanal

Nutzer: *"haben wir dort nicht mit dem value head modifiziert?"* -- die Frage
trifft, und par.4c war zu absolut.

**Richtig bleibt:** die v2-Routing-Huelle (`v2_tiling_preference`) bekommt das
Netz nicht (V1 auf allen Netz-Pfaden), und Tiling-Policy-Ziele sind immer
maskiert.

**Falsch war "doppelt verschlossen".** Es gibt einen dritten Kanal, und er ist
der geplante: **der Ownership-Pol im Tiling-Loeser.** `tiling_net: Some(net)`
reicht dem Loeser `ownership_tiling_marginals` herein, und der Test
`ownership_tiling_overrides_points_rounds_1_to_4` (tiling_solver.rs:2619)
zeigt, dass diese Marginalen die Sofortpunkte-Wahl in den Runden 1-4
**ueberschreiben** -- im Testbeispiel 11 gegen 2. Bei `w_own = 0` gewinnt der
punktereichere Zug (`ownership_tiling_default_off_matches_exact_rounds_1_to_4`).

**Damit ist die Deutung der Arme A und B eine andere:**

Beide liefen mit `OWNERSHIP_WEIGHT = 0`. Ich habe das Netz also **ohne den
einzigen Mechanismus gemessen, mit dem es Spalten ansteuern koennte** -- und
dann festgestellt, dass es keine baut. Der Befund "Arm B erreicht nur
Champion-Niveau" sagt ueber die Destillation entsprechend wenig.

**Der Mechanismus braucht ZWEI Dinge gleichzeitig**, und das ist der Kern:

1. einen Korpus, in dem Spalten tatsaechlich fertig werden -- damit die
   Ownership-Vorhersage auf Spaltenzellen zeigt statt auf das, was
   plattenblindes Spiel erreicht;
2. `OWNERSHIP_WEIGHT > 0` -- damit diese Vorhersage die Platzierung auch
   steuert.

Ich hatte (1) und nicht (2). **Genau (2) ist der registrierte v22-Entscheid**
(`PREREG_heuristic_v2_long_rows.md` par.3b: Kopf EINSCHALTEN, plus
w0-Kontrollarm auf demselben Korpus).

**Konsequenz fuer den naechsten Lauf:** die richtige Konfiguration ist nicht
"Arm B", sondern **Arm B PLUS Ownership-Gewicht ueber null**. Der
w0-Kontrollarm bekommt damit eine zweite Rolle: er trennt nicht nur Kopf von
Korpuswechsel, er ist der Beleg dafuer, ob dieser Kanal ueberhaupt traegt.

**Der Split-Test aus par.4c bleibt trotzdem sinnvoll** -- er sagt, WIEVIEL der
0,741 am Routing haengt und damit, wieviel der Ownership-Kanal ueberhaupt
aufholen muesste. Er ist jetzt aber Vorarbeit statt Entscheidung.


### par.4e ENDSTAND der Kanal-Frage (Nutzer-Korrektur 2026-08-25, dritter Anlauf)

Nutzer: *"irgendwo sollte auch der value head als faktor im tiling sein. der
point head und ownership head waren nur angedacht aber nie aktiv"*. Beides
stimmt. **Dieser Absatz ersetzt die Deutungen in par.4c und par.4d**, die
beide danebenlagen -- par.4c behauptete gar keinen Kanal, par.4d machte den
Ownership-Pol zur Antwort, obwohl er nie an war.

**Am Code geprueft, was im Tiling tatsaechlich wirkt:**

| Kopf | Stand | Wirkung im Tiling |
| --- | --- | --- |
| **Value** | **aktiv** | `net_tiling_tiebreak_value` liest ihn (self_play.rs:1050) und rechnet ihn in eine Gewinnwahrscheinlichkeit; er bricht **Gleichstaende** unter PUNKTEGLEICHEN Zuegen, und nur in **Runde 2-4** |
| Punkte | additiv, Default **0,0** | nie aktiv (self_play.rs:1053ff, "vorher weggeworfen") |
| Ownership | Gewicht **0** | nie aktiv -- **koennte** Punkte ueberschreiben |

Belege fuer die Beschraenkung des Value-Kanals:
`best_first_step_valued_biased_evaluator_flips_tied_choice`
(tiling_solver.rs:2055) arbeitet auf `find_tied_tiling_candidates`, also
punktegleichen Top-Abschluessen; `exact_or_valued_ignores_evaluator_outside_rounds_2_to_4`
(:2157) zeigt, dass er in Runde 1 und 5 komplett ignoriert wird. Der
Ownership-Pol dagegen ueberschreibt die Punktewahl
(`ownership_tiling_overrides_points_rounds_1_to_4`, :2619), steht aber per
Default auf 0 (`ownership_tiling_default_off_matches_exact_rounds_1_to_4`,
:2577).

**Die tragende Aussage, und sie erklaert die Messung besser als alles
vorherige:**

> Der einzige AKTIVE Netz-Kanal ins Tiling kann Gleichstaende brechen, aber
> keine Sofortpunkte gegen Struktur eintauschen. Spaltenbau verlangt genau
> diesen Tausch. Die beiden Koepfe, die ihn koennten, waren nie an.

Das deckt sich mit dem Bestandsbefund zum Loeser: er waehlt nach reinen
Sofortpunkten (`tiling_solver.rs:49-56`) und wirft jede Draft-seitige Absicht
wieder weg -- der Value-Tiebreak aendert daran nichts, er sortiert nur
innerhalb der punktegleichen Spitze.

**Konsequenz, unveraendert gegenueber par.4d:** die naechste sinnvolle
Konfiguration ist Arm B **plus** `OWNERSHIP_WEIGHT > 0`, weil das der einzige
gebaute Kanal ist, der den noetigen Tausch ueberhaupt ausdruecken kann. Neu
ist die Erwartung daran: er wurde **noch nie** unter einem plattenbewussten
Korpus gefahren, und seine bisherige Nullmessung
([[project_ownership_head_closed]], Gewicht 0) ist damit kein Gegenargument,
sondern eine Messung unter der falschen Bedingung.

**Und eine Selbstkritik, die zum Vorgehen gehoert:** diese Frage hat drei
Anlaeufe gebraucht, jeder korrigiert vom Nutzer. Der Fehler war jedes Mal
derselbe -- ich habe aus dem Vorhandensein eines Feldes auf seine Wirksamkeit
geschlossen, statt Default und Reichweite nachzusehen. `tiling_net:
Some(net)` heisst nicht "das Netz steuert das Tiling", sondern "das Netz darf
unter Gleichstaenden mitreden, in drei von fuenf Runden".


### par.4f SPLIT-TEST GEFAHREN (2026-08-26): das DRAFTING traegt es, das Routing allein nichts

par.4c hat den Test vorregistriert und zwei Ausgaenge benannt: *"Ergebnis nahe
0,1 => das Routing traegt den Loewenanteil"*, *"Ergebnis nahe 0,7 => das
Drafting traegt es"*. **Gemessen: 0,756.** Der zweite Fall, und damit das
Gegenteil dessen, was par.4c bis par.4e als Strukturbefund gefuehrt hat.

**Aufbau**, gleicher Seed und gleiche Sims in allen drei Armen, 160 gepaarte
Partien je Arm (80 je Sitz), 150 Sims, Block-Auswertung mit 10 Bloecken:

| Arm | Draft | Tiling | V1-Kontrolle | Testseite | Delta | t |
| --- | --- | --- | --- | --- | --- | --- |
| gekoppelt | v1 : v2huelle | v1 : v2huelle | 0,062 | **0,975** | +0,912 | 13,43 |
| nur Drafting | v1 : v2huelle | v1 : **v1** | 0,044 | **0,756** | +0,713 | 10,29 |
| nur Routing | v1 : **v1** | v1 : v2huelle | 0,113 | **0,113** | **+0,000** | 0,00 |

**Die Zerlegung ist nicht additiv, und das ist der eigentliche Befund.**
0,713 (Drafting) + 0,000 (Routing) = 0,713, gekoppelt sind es aber 0,912. Die
Luecke von **+0,199** ist eine Wechselwirkung: das Routing kann nur einsortieren,
was das Drafting geholt hat. Ohne passende Steine laeuft
`v2_tiling_preference` ins Leere und faellt auf den Bestandspfad durch -- was
die exakte Null im dritten Arm erklaert.

**Was das an par.4c berichtigt.** Dort stand, der v2-Durchbruch komme vom
PLATZIERUNGS-Routing, und dem Netz sei genau dieses Routing verschlossen.
Der erste Teil ist durch diese Messung widerlegt: das Routing allein bewegt
die vollen Spalten nicht. Der zweite Teil bleibt richtig -- die Netz-Seite
kachelt hartverdrahtet V1 (self_play.rs:2866, 3088/3095, 3795/3802, an allen
sechs Stellen nachgelesen) --, aber die Kosten dieser Verdrahtung sind
kleiner als angenommen: sie kostet die Wechselwirkung, nicht den Hauptteil.

**Und was daraus folgt, ohne es hier zu entscheiden:** der Kanal, ueber den
ein Netz den Lehrer erben koennte, ist die DRAFT-Haelfte, und die ist offen --
Draftingzuege tragen Policy-Ziele. Die Tiling-Maskierung (par.4c Punkt 2)
verschliesst die Haelfte, die allein ohnehin nichts traegt. Ob die
Netz-Kachelung trotzdem umgestellt wird, ist damit eine Frage nach den 0,199
Wechselwirkung, nicht mehr nach den 0,7 Hauptteil.

### Was dafuer gebaut werden musste

par.4c sagte, der Zuschnitt sei vorhanden: *"`PlayerLoopConfig` traegt beide
Angaben getrennt"*. Das stimmt fuer die STRUKTUR und nicht fuer den EINSTIEG.
`play_arena_game` nahm EINE Variante und legte sie auf Startsetzung, Drafting
UND Tiling; `run_heuristic_v1_vs_v2_arena` reichte ebenfalls nur eine durch.
Der Split war also nicht fahrbar, sondern musste erst ausdrueckbar gemacht
werden -- dieselbe Falle wie beim Korpus, eine Ebene hoeher: die Struktur
trennt, der Aufrufer koppelt.

Additiv geloest: zweite Variantenachse `tiling_varianten` in
`play_arena_game`, zwei optionale Namen am Einstieg (`None` = wie die
Draft-Seite, also Bestandsverhalten), `--tiling A:B` in
`tools/probes/v2_envelope_arena.py`.

**Drei Gegenproben vor der Messung**, weil ein durchgereichter Wert genau hier
schon einmal nicht angekommen ist:

1. ein unbekannter Tiling-Name muss FEHLSCHLAGEN statt still auf die
   Draft-Variante zurueckzufallen -- sonst saehe ein Bestandslauf wie der
   gewollte Split aus. Meldet `unbekannte Tiling-Variante: gibtsnicht`.
2. der Split-Lauf schreibt seine Achsen ins Artefakt (`tiling_varianten`).
3. der Bestandsaufruf mit zehn Argumenten ergibt weiterhin Tiling = Draft.

**Ein Fund dabei:** im Routing-Arm heissen beide Seiten `v1`, und die
Auswertung schluesselt Bretter nach SPIELERNAMEN. Ohne Unterscheidung legte
`reconstruct_game` zwei Bretter uebereinander. Gefangen hat es der
Katalog-Waechter der Sonde (`Special freigeschaltet, aber Katalog kennt dort
kein Spezialfeld`) -- ohne ihn waere es ein stiller Messfehler gewesen. Der
Spielername traegt die Tiling-Achse jetzt mit, sobald sie abweicht; bei
gleichen Achsen bleibt er Zeichen fuer Zeichen der alte. Gegenprobe: der
Drafting-Arm reproduziert nach der Umbenennung exakt (0,756 / t 10,29).
