<!-- STATUS: OFFEN | Frage: Wie wird das v25-Trainingsfenster zugeschnitten (stationaere Rotation aus docs/window_generation.svg, G = v24), und wie wird dabei der Spaltenbau gegen schleichendes Verlernen gesichert? | Beleg: Zuschnitt vom Nutzer festgelegt (2026-09-04, 21:50), nichts gebaut: Sockel 4.000 G + 1.350 G-1 + 450 G-2, Schwarm 8.000 G + 8.000 G-1 + 2.650 Sockel-Rest G-1 + 3.550 + 1.450 G-2 (par.1); hv2-Uebergangsabbildung ENTSCHIEDEN (par.2: 45 Traeger + 135 Ex-Traeger + 365 Schwarm); Manifest-Generator --pick gebaut (par.3); Spalten-Waechter auf drei Flaechen (par.7; v24-Fenster 44,8 % Seiten mit voller Spalte, hv2 ist spaltenreich 0,73, die gesampelten Klassen 0,19). Value-Klasse zu argmax verschoben (Nutzer 2026-09-05, par.9: 8.000/0 oder 7.000/1.000 offen). Generator ENTSCHIEDEN 2026-09-06 11:40: b05 ohne K3-P (par.4), seit 17:05 offen gegen b06 = Champion (Elo 1309, Nutzer: Self-Plays nur vom Champion). par.10 (22:50): Knoepfe in der ERZEUGUNG als Idee -- K3-F (Mechanik wirkt, Suche allein negativ) und Kandidatenliste mit Kriterium, drei Bauformen, nichts entschieden. -->

# Vorregistrierung: das v25-Trainingsfenster

**Angelegt 2026-09-04, 21:50**, waehrend die v24-Erzeugung laeuft
(`PREREG_v24_window.md` par.6c'). Nutzer-Vorgabe im Chat, woertlich:

> sockel: 4000 v24 + 1350 v23 b01 k3p10 + 450 hv2
> schwarm: 8000 v24 + 8000 v23 b01 k3p10 + 2650 sockel rest v23 b01 k3p10 + 1450 hv2 + 3550 hv2

und dazu (21:55): *"wichtig ist dass wir wirklich ein augenmerk auf die
spalten haben. es soll nicht schleichend verlernt werden. idealerweise
verbessert es sich schleichend"* (par.7).

Das ist Zeile fuer Zeile die stationaere Rotation aus
`docs/window_generation.svg` (Zwei-Klassen-Design, 29.450 Partien fix,
Nutzer-Entscheid dort) mit **G = v24** (das Netz, das aus dem v24-Fenster
hervorgeht), **G-1 = das heutige v24-Material** (erzeugt von
`v23-b01_brierbest` mit K3-P C 1,0, Dateien `selfplay_v23-b01-*`,
Generator-Namensregel) und **G-2 = hv2**. Nichts davon ist gebaut; diese
Datei haelt die Abbildung fest, damit der Zuschnitt beim v25-Start nicht aus
dem Gedaechtnis entsteht.

## par.1 Der Zuschnitt (Nutzer, 2026-09-04)

**Sockel (Policy-Klasse, 5.800 Partien, Traeger)**

| Posten | Quelle | Partien | Dateien (10 je Datei) |
| --- | --- | --- | --- |
| Sockel NEU | G = v24 Self-Play, policy-aktiv | 4.000 | 400 |
| 1.350 aus G-1 | 135 der 400 `selfplay_v23-b01-policy_*` (Manifest, seed-bestimmt) | 1.350 | 135 |
| 450 aus G-2 | 45 der 180 hv2-Traeger aus `data/carriers_v23_hv2.txt` (Manifest, seed-bestimmt) | 450 | 45 |

**Schwarm (Value-Klasse, 23.650 Partien, policy-maskiert)**

| Posten | Quelle | Partien | Dateien |
| --- | --- | --- | --- |
| Schwarm NEU | G = v24 Self-Play, `--value-only`; **Nutzer-Entscheid 2026-09-05, 12:10: staerker zu argmax verschoben** -- Vorschlag 8.000 argmax + 0 gesampelt (Alternative 7.000 + 1.000, siehe par.9) | 8.000 | 800 |
| Schwarm G-1 (komplett) | alle 800 `selfplay_v23-b01-value-*` | 8.000 | 800 |
| Sockel-Rest G-1 (Nicht-Traeger) | die 265 uebrigen `selfplay_v23-b01-policy_*` | 2.650 | 265 |
| Sockel-Rest G-2 (vollstaendig) | hv2, siehe par.2 | 3.550 | 355 |
| Schwarm G-2 (Auffuellung) | hv2, siehe par.2 | 1.450 | 145 |

**Summe 29.450 Partien = 2.945 Dateien** (1.200 G + 1.200 G-1 + 545 hv2),
dieselbe Groesse wie das v24-Fenster (`PREREG_v24_window.md` par.6d: 2.945
Dateien). Traegeranteil 5.800 wie v24. Der hv2-Anteil faellt von 17.450 auf
5.450 Partien; G-3 und aelter (hier: nichts mehr) rotieren vollstaendig aus.

## par.2 hv2 als G-2: Uebergangsabbildung (ENTSCHIEDEN 2026-09-05, 10:45 -- Nutzer: "nimm deinen vorschlag aus par.2")

Die Diagramm-Zahlen setzen voraus, dass G-2 ein Zwei-Klassen-Korpus mit
4.000-Sockel war: Sockel-Rest G-2 = 4.000 - 450 = 3.550. **hv2 hatte im
v24-Fenster aber nur 1.800 Traeger-Partien** (180 Dateien,
`carriers_v23_hv2.txt`, geprueft: 180 Eintraege) und 15.650 maskierte. Der
Sockel-Rest von hv2 ist also 1.800 - 450 = 1.350, nicht 3.550. Dieselbe Lage
hatte das Diagramm schon einmal ("Uebergangs-Ausnahme v21: die aelteste Stufe
lieferte ihre 5.000 als EINEN Block statt als 3.550 + 1.450").

Vorschlag, der die Summen des Nutzers exakt haelt und die Rollen so weit wie
moeglich abbildet:

| Posten | hv2-Quelle | Dateien | Partien |
| --- | --- | --- | --- |
| 450 aus G-2 (Traeger) | seed-bestimmte 45 der 180 bisherigen Traeger | 45 | 450 |
| Sockel-Rest G-2 | die 135 uebrigen bisherigen Traeger (jetzt maskiert) plus 220 seed-bestimmte aus den 1.565 bisherigen Schwarm-Dateien | 355 | 3.550 |
| Schwarm G-2 | 145 weitere seed-bestimmte aus den bisherigen Schwarm-Dateien | 145 | 1.450 |

Praktisch sind Sockel-Rest G-2 und Schwarm G-2 beide maskiert und beide hv2;
die Trennung ist Buchfuehrung: 45 Traeger plus 500 maskierte hv2-Dateien,
davon 135 ehemalige Traeger und 365 aus dem bisherigen Schwarm. Alle 545 aus
`data/window_v23_hv2.txt` (1.745 Dateien), Auswahl mit festem Seed, damit die
Liste reproduzierbar ist. Die Alternative (45 Traeger plus 500 nur aus dem
bisherigen Schwarm) ist vom Nutzer NICHT gewaehlt worden; es gilt die Tabelle
oben: 45 + 135 + 220 + 145 = 545 hv2-Dateien.

## par.3 Werkzeug-Luecke: seedbare Teilauswahl je Klasse

`tools/generate_carrier_manifest.py` kennt `--from-list --n-files --seed`
(EINE seed-bestimmte Auswahl) und `--include-glob` (ALLE Treffer als
Traeger). Fuer v25 braucht das Manifest zwei seed-bestimmte Teilauswahlen
(135 von 400 G-1-Policy-Dateien, 45 von 180 hv2-Traegern) plus alle 400
G-Policy-Dateien. Bau vor dem v25-Training: eine wiederholbare Option
`--pick "<glob>:<n>"` (seed-bestimmt, sortierte Kandidaten, wie
`--from-list`), Pruefung wie v24 par.6d (Diff der 45 gegen
`carriers_v23_hv2.txt`, Zaehlung je Praefix im Trainingsmanifest:
400 + 135 + 45 = 580 Traeger).

Dazu die Dateiliste `data/window_v25.txt` (2.945 Zeilen) aus denselben
Auswahlen; `train.py --file-list` bricht bei fehlenden Eintraegen hart ab.

**GEBAUT 2026-09-04, 23:50:** `--pick QUELLE:N` (wiederholbar; Glob oder
.txt-Liste; Seed je --pick = `seed + 1000*i`, damit die Hauptauswahl
byte-gleich bleibt; Ueberschneidung mit anderen Auswahlen bricht hart ab;
Herkunft im additiven Manifest-Feld `picks`). Trockenlaeufe: der v24-Aufruf
liefert unveraendert die 180 hv2-Traeger (erste/letzte Datei = Bestandsliste),
die v25-Form (`--from-list carriers_v23_hv2.txt --n-files 45 --pick
"selfplay_v23-b01-policy_*.pkl:135"`) waehlt 45 + 135, eine ueberschneidende
Quelle wird abgewiesen.

## par.4 Bedingung und Generator

Der Zuschnitt gilt, **wenn v24-b01 die Champion-Kante nimmt** (Nutzer:
"wenn v24 den derzeitigen champ besiegt"; Champion ist `v23-b01_k3p10`, Elo
1292). Nimmt er sie nicht, entscheidet die Generatorwahl-Regel
(`docs/generation_loop.md`, "Generatorwahl unter Armen": Staerke schliesst
aus, Spaltenprofil entscheidet, sonst Amtsinhaber). Dann liefert weiter
`v23-b01` mit K3-P das neue Material, und die FORM des Fensters bleibt
dieselbe -- nur heisst G dann nicht v24. Ob die v25-Erzeugung mit K3-P C 1,0
oder mit einem der v24-Arme (`PREREG_geometric_envelope.md` par.8.9b) faehrt,
ist eine eigene Frage der v24-Abnahme, nicht dieses Zuschnitts.

**ENTSCHIEDEN (Nutzer 2026-09-06, 09:40 und 11:40): Generator der v25-Erzeugung
ist `v24-b05` (`models/alphazero_v24-b05_brierbest.onnx`, INPUT_SIZE 744), und
die Erzeugung faehrt OHNE K3-P** (Spec `models/k3v_off.spec.json`, nicht par.6b'
der v24-Prereg). Begruendung aus der Abnahme (`PREREG_v24_window.md` par.9/9c):
"744er bleibt fix" schliesst die 714er-Arme aus; unter den 744er-Armen hat nur
b05 einen Tor-1-Beleg, und nur in der Knopf-losen Fassung (66:34 und 112:78,
zwei Seeds; mit Knopf 219:181 ohne Entscheid), Tor 2b gehalten (98:62,
Spalten 0,650 / 0,557 gegen 0,500 / 0,570). Folgen: das Rezept par.6 der
v24-Prereg gilt mit `--spec models/k3v_off.spec.json` statt der Champion-Spec;
der Spalten-Waechter par.7 bekommt als Generator-Bezug b05 ohne Knopf 0,4825
(Tor 2a, `tor2a_v24b05nk.json`) statt 0,555; Wheel 744 (Kontrakt
20b442a8164f748d, mit K3-P2 und K3-F, beide Default aus). Start der Erzeugung
NUR auf Nutzer-Anweisung.

## par.5 Cache-Kosten: nur der Monolith

Alle G-1- und hv2-Bloecke liegen (Watcher der v24-Erzeugung, 4.849
hv2-Bloecke im Bestand); die G-Bloecke entstehen mitlaufend bei der
v25-Erzeugung (Cache-Prereg par.6). Die Traegermaske wird beim Zusammenfuegen
angewandt (`engine/py/file_cache_key.py`, seit 2026-08-31), kein Block wird
neu gebaut. Kosten: Zusammenfuegen des Trainingsanteils, gemessen am
v23-Fenster 344 s (`PREREG_cache_build_time.md` par.12), unter der
Trainings-Umgebung.

**Berichtigung (2026-09-04, 23:40, am Code geprueft):** die erste Fassung
dieses Absatzes nannte den Satz "Manifest-Inhalt steckt im Cache-Key" in
`docs/window_generation.svg` veraltet. Das war falsch: der FENSTER-Schluessel
(`corpus_dataset.window_cache_key`, engine/py/corpus_dataset.py:324 ff.)
traegt den Manifest-INHALT (`policy_carrier_set`) weiterhin -- ein anderer
Traegersatz ist ein anderer Monolith. Nur der DATEI-Block-Schluessel
(`file_cache_key.per_file_cache_key`) kennt den Traegerstatus seit dem
2026-08-31 nicht mehr. Das Diagramm ist richtig; fuer v25 heisst das: neuer
Traegersatz = neuer Monolith (344 s), Bloecke bleiben.

## par.6 Was noch offen ist

1. ~~Nutzer-Entscheid zu par.2~~ gefallen 2026-09-05 (Vorschlag angenommen).
2. ~~Val-Pool-Regex fuer v25~~ ENTSCHIEDEN 2026-09-05, 18:35 (Nutzer: "par.6
   defaults passen"): analog v24 auf den v24-GENERATOR, also
   `^selfplay_v24-<generator>-` (Dateien heissen nach dem Generator; der
   Name haengt an der Generatorwahl nach den Abnahmen, v24-b01 ist nur der
   Platzhalter).
3. ~~Startgewicht des v25-Trainings~~ ENTSCHIEDEN 2026-09-05, 18:35: der
   Generator-Checkpoint (v24-Regel), also das `_brierbest` des gewaehlten
   v24-Arms.

## par.7 SPALTEN-WAECHTER: nicht schleichend verlernen (Nutzer, 2026-09-04, 21:55)

Die Rotation tauscht je Generation 12.000 Partien aus. Verlernen kaeme nicht
mit einem Knall, sondern ueber zwei bis drei Generationen, jede fuer sich
"innerhalb der Streuung". Darum wird der Spaltenbau auf DREI Flaechen
mitgefuehrt, mit Bezugswert je Generation, und die Reihe ist der Befund, nicht
der einzelne Wert:

| Flaeche | Kennzahl | Instrument | Bezug v24 (Vor-Generation) | Regel |
| --- | --- | --- | --- | --- |
| **Generator** (Self-Play) | volle Spalten je Seite, argmax @400, 200 Partien, Seed 20260931 | Tor 2a der Schleife (`docs/generation_loop.md`), `tools/corpus_sanity_check.py` | b01 0,515; b01 + K3-P 0,555 (`geometric_envelope` 8.7a) | nicht fallen (Punktschaetzer), Tor 2 |
| **Arena** (gegen Vorgaenger) | volle Spalten je Seite aus der Brettgeometrie | Tor 2b, `tools/probes/arena_column_probe.py` | b01-Seite derselben Arena; v23: 0,6456 gegen 0,4304 | nicht fallen, Tor 2 |
| **Fenster** (Korpus-Eigenschaft, NEU hier) | Seiten mit voller Spalte je Klasse UND ueber das ganze Fenster (Partien-gewichtet) | `tools/corpus_sanity_check.py data --pattern <Klasse>` je Posten aus par.1, dann gewichtete Summe | **v24-Fenster gemessen 2026-09-05: 44,7 % / 0,624** (hv2 51,8 % / 0,732; argmax 52,5 % / 0,748; sampled 16,2 % / 0,191; Sockel 16,5 % / 0,189) | das v25-Fenster darf in der Fenster-Kennzahl NICHT unter dem v24-Fenster liegen (Herleitung par.1 mit G = G-1: 37,7 % / 0,517 -- wuerde reissen, siehe Berichtigung unten) |

Warum die dritte Flaeche: die beiden Tor-2-Flaechen messen das NETZ; die
Rotation aendert aber, WOVON es lernt.

**BERICHTIGUNG 12:00 (gemessen, `corpus_sanity_check` ueber alle 1.745
hv2-Dateien, `sanity_hv2_window.json`):** die erste Fassung dieses Absatzes
nannte hv2-Material spaltenaermer als das heutige und stuetzte das auf die
v23-VALUE-Klasse (35,2 %). Das war ein Fehlschluss: jene Klasse war
b05-Material, nicht hv2. **hv2 ist spaltenreich: 0,732 volle Spalten je Seite,
51,8 % Seiten mit voller Spalte (18.091 von 34.900), 46,1 Punkte** -- auf
Augenhoehe mit der v24-argmax-Klasse (0,748 / 52,5 % / 49,8) und weit ueber
den gesampelten Klassen (Sockel 0,189 / 16,5 %, sampled 0,191 / 16,2 %).

Fenster-Kennzahl v24, partiengewichtet: **44,7 % Seiten mit voller Spalte,
0,624 volle Spalten je Seite.** Herleitung fuer v25 nach par.1, wenn das
G-Material die Klassenwerte von G-1 traegt: **37,7 % / 0,517** -- die Rotation
von hv2 (0,73) nach G-Material mit seinen zwei gesampelten Klassen (0,19)
SENKT die Fenster-Kennzahl um 7 Punkte, und die dritte Flaeche dieses par.7
wuerde reissen. Das ist kein Argument gegen die Rotation als solche (hv2 ist
plattenblinder Lehrer-Stoff), aber gegen die Annahme, sie hebe die Spalten
von selbst. Konsequenzen zur Entscheidung (Nutzer): (a) die gesampelten
Klassen sind die Spaltenarmut des Fensters -- Sockel (Policy-Traeger) und
sampled-Schwarm bauen 0,19; (b) die argmax-Klasse traegt die Spalten; eine
Verschiebung der Value-Klasse zu mehr argmax (oder ein Sockel mit weniger
Rauschen) haelt die Kennzahl, ein reiner hv2-Abbau nicht. Faellt die
Fenster-Kennzahl trotz Rotation, hat entweder G verlernt oder der Mix ist
spaltenaermer geworden -- beides sieht diese Flaeche vor Tor 2.

**Die Reihe, die fortgeschrieben wird** (Generator-Flaeche @400, gleiches
Instrument; "schleichend verbessert" heisst: monoton, nicht signifikant je
Schritt): v22-b05 0,4304 (Arena-Seite, v23 par.2d) -> v23-b01 0,515 ->
v23-b01 + K3-P 0,555 -> v24-b01: __ -> v25-b01: __. Jede Generation traegt
hier ihren Wert nach, mit Seed und Partienzahl; ein fehlender Eintrag ist ein
Regelbruch, kein Vergessen.

**Was NICHT hilft und darum nicht gebaut wird:** ein Zwang auf Spalten im
Training (Ownership-Gewicht, Tiling-Uebersteuerung, Huellen-Bauer) -- alle
gemessen ohne Staerke oder mit Zusammenbruch (`ownership_head` geschlossen,
`geometric_envelope` 8.8). Der Hebel bleibt das MATERIAL (par.1) und der
Such-Knopf des Generators (K3-P), der Waechter misst nur.

## par.9 Value-Klasse zu argmax verschoben (Nutzer-Entscheid 12:04: "Wir werden die value klasse staerker zu argmax verschieben")

Anlass: par.7-Berichtigung (hv2 0,73 Spalten je Seite, die gesampelten Klassen
0,19). Fenster-Kennzahl je Variante (Herleitung mit den gemessenen v24-Klassen-
werten, G-Material = G-1-Werte angenommen; Seiten mit voller Spalte /
volle Spalten je Seite):

| Fenster | Seiten mit voller Spalte | volle Spalten je Seite |
| --- | --- | --- |
| v24 gemessen | 44,8 % | 0,624 |
| v25, G-Schwarm 6.000 argmax + 2.000 gesampelt (bisher) | 37,7 % | 0,517 |
| v25, G-Schwarm 7.000 + 1.000 | 38,9 % | 0,536 |
| v25, G-Schwarm 8.000 argmax + 0 gesampelt | 40,1 % | 0,555 |
| dazu Sockel G mit 0,40 statt 0,19 (Annahme, ungeprueft) | 42,0 % | 0,584 |

**Lesart:** die Verschiebung hebt die Kennzahl um bis zu 2,4 Punkte, haelt
aber die Flaeche 3 aus par.7 (nicht unter 44,8 %) NICHT allein, weil die
Rotation 12.000 hv2-Partien mit 0,73 abgibt. Die uebrigen Hebel: (a) der
Sockel (Policy-Klasse, Rauschen noetig fuer die Policy-Ziele) bleibt mit 0,19
die spaltenaermste Klasse -- weniger Rauschen, Generator-Arm C 2,0
(`geometric_envelope` 8.7d: 0,635 am Instrument) oder eine Gewichtung waere
ein eigener Arm. **Nicht mehr Sims** (Nutzer 2026-09-05, 12:15: "hatten wir
schon durch, bringt nur weniger Spalten"; `search_depth_column_optimum`:
25-100 Sims rund 0,6, ab 250 Sims 0,34 volle Spalten); (b) weniger hv2 abbauen (z.B. G-2 nicht auf 5.450, sondern auf
rund 11.000) wuerde die Kennzahl halten, aendert aber die stationaere Form;
(c) das G-Material selbst spaltenreicher (v24-Arme, Knopf-Dosis par.9b der
v24-Prereg).

**Was die 2.000 gesampelten leisten sollten** (`PREREG_heuristic_v2_long_rows.md`
Zeilen 2401-2408): Zustands-Streuung in der Value-Klasse, damit der Value-Kopf
nicht nur argmax-Trajektorien sieht. Argmax-Partien streuen ueber Seeds,
Wertungsplatten und Auslagen weiter, aber enger als gesampelte; das ist der
Preis der Verschiebung. **Offen (Nutzer):** 8.000/0 (maximal, Vorschlag) oder
7.000/1.000 (Streuung teilweise erhalten). Gilt fuer die v25-ERZEUGUNG
(G-Material); das G-1-Material bleibt, wie es liegt.

### par.9a EINWAND DES NUTZERS zur Value-Klasse (2026-09-05, 18:35): "die Spalten kommen aus der Policy"

Nutzer: *"bei v25 value klasse bin ich noch nicht vollkommen ueberzeugt. da
hast gesagt die spalten kommen aus der policy."* Der Einwand trifft die
Herleitung von par.9 an einer Stelle, die dort uebergangen war:

- **Die Frage 8.000/0 gegen 7.000/1.000 betrifft NUR die Value-Klasse**, und
  die ist policy-maskiert (par.1: Schwarm, `--value-only`). Was die POLICY
  lernt, kommt aus den Traegern: Sockel NEU 4.000 (v24, gesampelt mit
  Rauschen), 1.350 aus G-1, 450 hv2-Traeger. Im v24-Material hat genau diese
  Sockel-Klasse 0,19 volle Spalten je Seite (par.7-Tabelle), obwohl sie MIT
  K3-P C 1,0 erzeugt wurde; die spaltenreichen Klassen (argmax 0,75, hv2 0,73)
  sind entweder maskiert oder rotieren aus (hv2-Traeger von 180 auf 45
  Dateien).
- **Was gemessen ist:** flache Suche (Prior-dominiert) baut rund 0,6 volle
  Spalten, tiefe Suche 0,34 -- die Spalten-PRAEFERENZ sitzt im Prior, der
  Value-Kopf daempft sie mit der Tiefe (`search_depth_column_optimum`,
  Merkposten [[project_search_depth_column_tradeoff]]); bei 400 Sims traegt
  der Value-Kopf die STAERKE. Beide Klassen haben also eine Rolle: die
  Value-Klasse dafuer, dass der Kopf spaltenreiche Zustaende richtig
  bewertet (Phase 3, Betrag), die Traeger dafuer, dass der Prior die Spalten
  ueberhaupt vorschlaegt.
- **Folge fuer par.9:** die Fenster-Kennzahl (44,8 % -> 40,1 %) mischt beide
  Klassen und ist deshalb fuer die Policy-Frage das falsche Mass. Der
  Spalten-Waechter par.7 bekommt eine VIERTE Zeile: **Traeger-Kennzahl**
  (Seiten mit voller Spalte und volle Spalten je Seite NUR ueber die
  Traeger-Dateien des Fensters, `corpus_sanity_check.py` ueber die
  Traeger-Liste des Manifests). **Bezug v24 GEMESSEN 21:42 (`v24_sanity_carriers.json`,
  `corpus_sanity_check.py data --file-list data/carriers_v24_manifest.txt`, 580 Dateien =
  5.800 Partien = 11.600 Seiten): volle Spalten 0,356 (+-0,011) je Seite, 3.165 von 11.600
  Seiten mit voller Spalte (27,3 %), Punkte 32,2, Strafleiste 8,3.** Zum Vergleich das ganze
  v24-Fenster 0,624 / 44,7 % und die argmax-Klasse 0,748 / 52,5 %: die Policy lernt aus dem
  spaltenaermsten Drittel des Fensters. Rechnerisch passt der Wert zur Zusammensetzung
  (400 Sockel-Dateien bei 0,19 plus 180 hv2-Traeger bei 0,73 ergeben 0,357).
  **Herleitung (nicht gemessen) fuer den v25-Zuschnitt aus par.1:** Traeger = 4.000 Sockel NEU
  + 1.350 G-1-Sockel + 450 hv2. Bleibt der Sockel NEU beim Erzeugungs-Betriebspunkt des
  v24-Sockels (0,19), faellt die Traeger-Kennzahl auf rund (5.350 x 0,19 + 450 x 0,73) / 5.800
  = **0,23** -- ein Drittel unter v24. Der Waechter ("nicht fallen") wuerde damit schon
  auf dem Papier reissen; das ist der Hebel, nicht die Value-Klasse.
- **Hebel fuer die Policy, zu pruefen statt der 8.000/0-Frage** (Vorschlaege,
  nichts entschieden): (a) den Sockel NEU spaltenreicher erzeugen (weniger
  Rauschen oder hoehere Temperatur-Abklingung, Betriebspunkt messen), (b)
  mehr hv2- oder argmax-Traeger im Sockel als die 450, (c) die argmax-Klasse
  teilweise policy-tragend machen (Besuchsverteilung @100 als Ziel, scharf).
  Jeder Hebel braucht den Traeger-Bezugswert zuerst.

**Stand:** 8.000/0 bleibt OFFEN (Nutzer nicht ueberzeugt); die
Traeger-Kennzahl v24 wird gemessen, sobald die CPU frei ist, dann Vorlage.

## par.10 KNOEPFE IN DER ERZEUGUNG: Idee und Kandidaten (Nutzer 2026-09-06, 22:45)

**Nutzer, woertlich:** *"vielleicht muessen wir den arm dann mit der champ konfiguration
kombinieren"* -> auf die Rueckfrage (der K3-F-Arm IST Champion-Spec plus ein Feld;
Spec-Diff: nur `envelope_flush_w` 0,0 gegen 1,0) die dritte Lesart bestaetigt: *"ja nimm es
also idee fuer das v25 fenster mit. vielleicht haben wir auch gleich andere kandidaten bei
denen es sich auszahlen wuerde sie ins self play zu werfen."*

**Anlass (gemessen, `PREREG_geometric_envelope.md` par.8.14):** K3-F 1,0 am Champion b06
vollendet je Seite 0,3-0,4 lange Reihen mehr und raeumt weniger unplatzierbar (die
Mechanik tut, was sie soll), verliert aber 74:86 und liegt 2,4-2,8 Punkte je Seite unter
der Kontrolle. **These (Herleitung, nicht gemessen):** ein Such-Knopf zwingt der Suche
ein Verhalten auf, dessen Folgezustaende das Netz nie gesehen hat; der Value-Kopf
bewertet sie darum falsch, und der Prior schlaegt die Fortsetzung nicht vor. Steht der
Knopf beim GENERATOR, lernt das Netz die Folgezustaende (Value) und die Zuege (Policy),
und der Preis in Punkten kann verschwinden -- oder er bleibt, dann war es die Mechanik.
Praezedenz in der Kampagne: der Spaltenbau kam aus dem KORPUS (v22: b01 verdreifacht
Spalten ueber das Material, das Trainingsgewicht trug nicht; `PREREG_heuristic_v2_long_rows.md`
par.3b, aus dem Gedaechtnis der Kampagne zitiert, Fundstelle in dieser Sitzung nicht
neu gelesen), nicht aus einem Such-Knopf.

**Kriterium fuer einen Kandidaten (Vorschlag):**
1. Die Mechanik bewegt eine Verhaltensgroesse in den Records nachweisbar (sonst gibt es
   nichts zu lernen);
2. die Kosten in der Suche allein sind Punkte oder Siege, NICHT ein Spaltenverlust ohne
   Gegenwert (Richtungsregel `generation_loop.md`: spalten- UND siegverstaerkend);
3. das Verhalten liegt auf der Kampagnen-Richtung (Plattenblick, Vollendung, Kuppel-Bonus);
4. Welle-1-Bauform: Spec-Pflichtfeld je Seite, bitidentisch bei 0, damit die Erzeugung es
   je Seite und je Klasse setzen kann.

**Kandidaten (Stand am Knopf-Register `docs/knobs.md` und am Prereg-Index, geprueft 22:47):**

| Knopf | Stand | Kriterium 1 (Mechanik) | Kosten in der Suche | Kandidat |
| --- | --- | --- | --- | --- |
| K3-P (Modus 1, C 1,0) | Champion-Knopf seit 2026-09-04; in der v24-Erzeugung auf beiden Seiten (v24 par.6b') | Spalten am Instrument (8.7) | keine (Champion-Kante) | gesetzt; offen ist nur b05 ohne / b06 mit (par.4) |
| **K3-F w_flush 1,0** | 8.14: NEGATIV 74:86 | **ja**: lange Reihen vollendet +0,3-0,4, geraeumt weniger | -2,4/-2,8 Punkte, Spalten leicht | **JA (Nutzer-Idee)**; Dosis 0,5 und Kombination laufen |
| K3-P2 (Modus 4) | 8.11a: NEGATIV 71:89 | nein: Kuppel-Bonus und lange Reihen unveraendert | Siege | nein (Kriterium 1) |
| K3-P2 + K3-F | 8.14a laeuft (Ende rund 00:10) | offen | offen | nach Ergebnis |
| K1 Score-Utility c 0,2 | ENTSCHIEDEN, kein Rezept (`saturating_score_utility` par.15-17) | Marge +2 bis +5 | Siege an der Champion-Kante | schwach: die Marge lernt der Value-Kopf ohnehin aus den Endstaenden; kein neues Verhalten |
| K3 (d) Tiling W_VAL | 8.6a: bewegt nichts | nein | -- | nein |
| K3 (d) Tiling W_TILE | par.8.3 (Stand in dieser Sitzung nicht nachgelesen, UNGEPRUEFT) | -- | -- | offen |
| K4 Rundenschaetzer | nicht gebaut (`round_estimate_leaf_term`) | -- | -- | erst Such-Messung |
| **K5 Reihe-6-Spezialfeld** | nicht gebaut (`special_tile_yield` par.9) | Kuppel-Bonus Netze 3,5-4,3 gegen Mensch 8,9: genau ein nie gesehenes Verhalten | -- | Kandidat NACH der Such-Messung (Bau nach den K3-Armen) |
| Seeding-Schwarm (b03) | `start_position_seeding` par.7; b03 hoechster Kuppel-Bonus 4,2 (v24 par.9c) | ja (Plattenwahl gesaet) | kein Such-Knopf | ist bereits ein Erzeugungs-Hebel; b03 ist 714er |
| LONG_ROW_INIT_W | ENTSCHIEDEN/UEBERHOLT (`long_row_payoff` B1: Initiierung erzwingbar, Vollendung nicht) | Initiierung ja, Vollendung nein | -- | nein |

**Drei Bauformen (Vorschlag, nichts entschieden):**
- **A, Generator-Spec traegt den Knopf auf beiden Seiten** (wie K3-P in v24): einfach,
  alle Klassen tragen ihn. Konflikt: der Nutzer will Self-Plays nur vom Champion
  (17:05), und ein Generator mit K3-F verliert 74:86 gegen die Champion-Spec -- Stufe 1
  der Generatorwahl (Staerke schliesst aus) spraeche dagegen, wenn man den Knopf-
  Generator als eigenen Arm liest.
- **B, Knopf-Klasse:** nur ein Teil des Sockels (Traeger, policy-aktiv, gesampelt) mit
  dem Knopf, der Rest Champion-Spec -- Vorbild Seeding-Schwarm b03. Zum Beispiel 1.000
  der 4.000 Sockel-NEU-Partien; eigener Dateiname nach Generator und Knopf
  (`feedback_selfplay_naming_convention`), Manifest-Kennzeichnung, Fenster-Pinning.
  Messbar je Klasse: Traeger-Kennzahl (par.9a) und lange Reihen vollendet. Der
  Champion bleibt Generator der uebrigen Klassen.
- **C, eine Seite je Partie** (Muster `MOSAIC_ASYM_VORZUG`, Spec je Seite): der Gegner
  sieht das Verhalten, der Value-Kopf lernt beide Seiten, keine zusaetzlichen Partien.
  Halbiert die Dosis im Material.

**Was vorher zu klaeren ist:** (1) Dosis aus der laufenden Kette (K3-F 0,5, Kombination
par.8.14a); (2) Bauform A/B/C und Anteil; (3) der Spalten-Waechter par.7 gilt unveraendert,
Bezug bleibt der Generator ohne Knopf-Klasse; (4) dieser Absatz ist die IDEE -- vor der
Erzeugung bekommt die Knopf-Klasse eine Zeile in der par.1-Tabelle und einen Arm-Namen.
Erzeugung startet NUR auf Nutzer-Anweisung.

