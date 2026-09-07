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

**Nutzer-Einwand (2026-09-06, 22:49, woertlich): *"das ist eventuell ein allgemeines problem
mit der huelle oder aufgezwungenen knoepfen."*** Was die Kampagne dazu hergibt (Stand der
Preregs, Herleitung markiert): aufgezwungene Such-Knoepfe haben getragen, wo sie ein
Verhalten VERSTAERKEN, das das Netz aus dem Korpus schon kann (K3-P: Spalten in der
Huelle, gepoolt 191:129, Champion-Kante 221:179), und sie haben Punkte oder Siege
gekostet, wo sie ein Verhalten VERLANGEN, das im Korpus fehlt (K3-F: Freiraeumen; K3-R/K3-O:
Erreichbarkeit, par.8.9a; B1 Langreihen-Initiierung: erzwingbar, Vollendung nicht; K1:
Marge ohne Siege). Lesart als Hypothese: ein Such-Knopf ist ein Verstaerker, kein
Lehrer -- Lehren geht nur ueber das Material (Bauformen oben). Das ist genau der Grund,
K3-F in die Erzeugung zu nehmen, und zugleich die Erwartung fuer K5: als Such-Knopf
allein wahrscheinlich Punkte-negativ, als Erzeugungs-Klasse der eigentliche Test. Ob die
Huelle selbst das Problem ist (die Dreiecks-Huelle hat in Zeile 6 nur eine Zelle, par.8.14),
laesst sich an K3-F 0,5 und der Kombination nicht klaeren; das braeuchte eine andere
Huellenform als eigenen Arm.

## par.11 VORLAGE v25-ZUSCHNITT (2026-09-07, 00:55; alle offenen Punkte gebuendelt, ENTSCHEID BEIM NUTZER)

Die Erzeugung startet nur auf Anweisung. Diese Vorlage sammelt, was vorher zu entscheiden
ist, mit Empfehlung je Punkt. Keine stille Wahl: was hier offen bleibt, bleibt offen.

### A. Generator: `v24-b05` (Stand par.4) oder `v24-b06` (amtierender Champion)

| Kriterium | b05 ohne K3-P | b06 mit K3-P |
| --- | --- | --- |
| Tor 1 gegen v23-b01, gleiche Spec | **66:34 + 112:78 SPRT**, zwei Seeds | 117:83 + 202:158 SPRT, zwei Seeds |
| Kante gegen den DAMALIGEN Champion in Spielkonfiguration | 202:218 aus 210 Paaren, gleichauf, kein Beleg | dieselbe Messung wie Tor 1: **319:241, Champion-Kante genommen** |
| Amt | -- | **Champion seit 2026-09-06 18:42, Elo 1309** |
| Tor 2a (Spalten-Bezug des Waechters) | 0,4825 ohne Knopf | 0,4975 mit Knopf |
| Tor 2b Spalten | gehalten (0,650 / 0,557 gegen 0,500 / 0,570) | gleichauf (0,575 / 0,725 gegen 0,650 / 0,625) |

**Empfehlung: b06 mit K3-P.** Grund: der Nutzer-Grundsatz "Self-Plays nur mit dem Champion"
(2026-09-06, 17:05) und der Umstand, dass b05 gegen den Champion nur gleichauf liegt
(202:218) -- der Vorsprung von b05 ist gegen v23-b01 in gleicher Spec gemessen, nicht gegen
das, was heute spielt. Das Material entstuende dann in derselben Konfiguration, in der auch
gespielt wird. Kosten der Umstellung gegenueber par.4: der Waechter-Bezug wird 0,4975 statt
0,4825, der Val-Pool-Regex `^selfplay_v24-b06-`, sonst nichts. **Gegenargument, das der
Nutzer kennen muss:** b05 ist der einzige 744er-Arm mit einem Tor-1-Beleg OHNE Knopf, und
eine knopflose Erzeugung haelt das Material naeher an dem, was ein knopfloses Netz spaeter
sieht. Wer das hoeher gewichtet, bleibt bei par.4.

### B. Value-Klasse: 8.000 argmax / 0 gesampelt, oder 7.000 / 1.000 (par.9, offen seit 2026-09-05)

**Empfehlung: 8.000 / 0.** Die Streuung, die die 1.000 gesampelten liefern sollten, kostet
in der Fenster-Kennzahl rund 2 Punkte (0,536 gegen 0,555, par.9), und der Einwand aus
par.9a bleibt gueltig: die Value-Klasse ist policy-maskiert, die Spalten kommen aus den
Traegern. Wer Streuung will, holt sie billiger ueber Seeds und Wertungsplatten als ueber
gesampelte Zuege. **Der unwichtigste Punkt dieser Vorlage** -- er bewegt eine Kennzahl, die
nach par.9a ohnehin das falsche Mass ist.

### C. Der eigentliche Engpass: die Traeger-Kennzahl faellt auf rund 0,23 (par.9a)

Gemessen v24: **0,356 volle Spalten je Seite ueber die 580 Traeger-Dateien**
(`v24_sanity_carriers.json`), gegen 0,624 ueber das ganze Fenster. Hergeleitet (nicht
gemessen) fuer den v25-Zuschnitt aus par.1: (5.350 x 0,19 + 450 x 0,73) / 5.800 = **0,23**.
Der Waechter par.7 reisst damit auf dem Papier, bevor eine einzige Partie gespielt ist --
weil der Sockel NEU (4.000 Partien, policy-aktiv, gesampelt mit Rauschen) mit 0,19 die
spaltenaermste Klasse ist und die spaltenreichen hv2-Traeger von 180 auf 45 Dateien
ausrotieren.

**Vorschlaege (Nutzer waehlt, mehrere kombinierbar):**
1. **Mehr hv2-Traeger behalten**: 450 -> 900 Partien (90 statt 45 Dateien), Sockel NEU
   entsprechend 3.550. Rechnung: (4.900 x 0,19 + 900 x 0,73) / 5.800 = 0,27. Kostet keine
   Rechenzeit, verlangsamt aber die Rotation des Lehrer-Materials.
2. **Sockel NEU spaltenreicher erzeugen**: weniger Rauschen oder schnellere
   Temperatur-Abklingung; Betriebspunkt vorher messen (eine argmax-Sonde je Kandidat, rund
   10 min). Der einzige Hebel, der die 0,19 selbst angreift.
3. **Einen Teil der argmax-Klasse policy-tragend machen** (Besuchsverteilung @100 als
   scharfes Ziel). Groesster Eingriff, eigener Arm, nicht in diesem Zuschnitt.

**Empfehlung: 1 und 2 vor dem Start, 2 zuerst messen.** Punkt 2 ist die Ursache, Punkt 1 der
Verband. Ohne beides startet die Generation mit einem gerissenen Waechter.

### D. K3-F als Knopf in der ERZEUGUNG (par.10, Nutzer-Idee 2026-09-06, 22:45)

Stand der Messung: alle vier Such-Knopf-Arme am Champion sind negativ
(`geometric_envelope` par.8.11a / 8.14 / 8.14a), K3-F verschiebt aber die Endbretter
messbar in die Nutzer-Form (par.8.15a: Zelle (5,1) zu 0,525 gegen 0,362 der Kontrolle) und
vollendet 0,3 bis 0,8 lange Reihen mehr je Seite.

**Vorschlag (Bauform B aus par.10): 1.200 der 4.000 Sockel-NEU-Partien mit
`envelope_flush_w` 1,0**, also 30 % des neuen Sockels und rund 20 % aller Traeger --
dieselbe Groessenordnung wie der hv2-Traeger-Anteil in v24 (1.800 von 5.800, 31 %), der die
Traeger-Kennzahl nachweislich getragen hat. Ersetzen statt ergaenzen, damit die Traegerzahl
5.800 bleibt und keine Rechenzeit dazukommt. Dosis 1,0 statt 0,5, weil bei 0,5 die
Reihen-Wirkung in der Arena schon kaum mehr sichtbar war (par.8.14). Eigener Dateiname nach
Generator und Knopf, Manifest-Kennzeichnung, Fenster-Pinning. **Vor dem Training messbar:**
lange Reihen vollendet und Traeger-Kennzahl je Klasse -- sieht das Material anders aus als
der Rest, hat der Knopf gewirkt; sieht es gleich aus, ist der Arm tot, bevor er trainiert
wird. **Untergrenze:** unter rund 500 Partien (unter 10 % der Traeger) ist nicht zu
erwarten, dass es das Netz erreicht (Herleitung aus dem hv2-Anteil, nicht gemessen).

### E. Huellenform in der Erzeugung (par.8.15 Teil B, Messung steht aus)

Haengt am Arm-Ergebnis. Traegt Form 2 in der Suche, gehoert sie in die Generator-Spec, und
K3-F bekaeme in der Erzeugungs-Klasse die neue Form dazu (mit zwei Huellenzellen in Zeile 6
hat die Freiraeum-Regel ein zweites Ziel und muss seltener "NEIN" sagen). Traegt sie nicht,
bleibt es bei D auf dem Dreieck. **Kein Entscheid noetig, bis der Arm gefahren ist.**

### Was NICHT offen ist (damit es nicht neu verhandelt wird)

Zuschnitt und Groesse des Fensters (par.1: 29.450 Partien, 2.945 Dateien), die
hv2-Uebergangsabbildung (par.2), Val-Pool-Regex und Startgewicht (par.6), die Form des
Waechters (par.7). Die Erzeugung startet NUR auf Nutzer-Anweisung.

## par.12 WAS MESSUNG 3-V AM ZUSCHNITT AENDERT (2026-09-07, 02:45; Nutzer-Frage "hat das nun einen einfluss auf unseren fenster zuschnitt?")

**Kurz: an der ZUSAMMENSETZUNG nichts, am BETRIEBSPUNKT der Erzeugung alles -- und damit
faellt Punkt C der Vorlage (par.11) ersatzlos weg.**

Gemessen (`PREREG_search_path_remeasurements.md`, Messung 3-V): die Sockel-Konfiguration
(@100, Wurzelrauschen an, policy-aktiv) baut mit dem Bestandsverhalten 0,1950 volle Spalten
je Seite, mit argmax ab Halbzug 12 dagegen **0,4225** -- bei praktisch unveraenderter
Zustandsvielfalt. Betroffen ist ausschliesslich der SOCKEL: der Schwarm faehrt seit v23
ohnehin `--deterministic --no-root-noise` (par.6 der v24-Prereg, Zeile
`selfplay_v22-b05-value-argmax`), ist also schon argmax und mit 0,748 die spaltenreichste
Klasse.

**Traeger-Kennzahl, neu gerechnet** (Zusammensetzung unveraendert: 4.000 Sockel NEU +
1.350 G-1-Sockel + 450 hv2-Traeger = 5.800):

| | volle Spalten je Seite |
| --- | --- |
| v24 GEMESSEN (`v24_sanity_carriers.json`) | 0,356 |
| v25 mit Bestands-Sockel (die Sorge aus par.11 C) | 0,232 |
| **v25 mit argmax-Sockel (Messung 3-V, Charge B)** | **0,392** |

Statt eines Absturzes auf 0,23 also ein Anstieg ueber den v24-Wert. Der Spalten-Waechter
par.7 ist damit nicht mehr in Gefahr, und die drei Hebel aus par.11 C (mehr hv2-Traeger,
Betriebspunkt messen, nichts tun) sind gegenstandslos -- der Betriebspunkt WAR der Hebel.
Fenster-Kennzahl: der Sockel-Fix allein hebt sie um rund 0,032 (4.000 von 29.450 Partien),
Bezug v24 0,624.

**Was sich NICHT aendert:** Groesse und Klassenaufteilung des Fensters (par.1: 29.450
Partien, 2.945 Dateien), die hv2-Uebergangsabbildung (par.2), Val-Pool-Regex und
Startgewicht (par.6), die Form des Waechters (par.7). Der Zuschnitt bleibt, wie er ist.

**Was sich aendert oder neu zu entscheiden ist:**
1. **Punkt C der Vorlage entfaellt.** Ersatzlos, nicht "anders beantwortet".
2. **Punkt B (Value-Klasse 8.000/0 gegen 7.000/1.000) wird klarer:** die 1.000 gesampelten
   waeren nach diesem Befund die EINZIGE verrauschte Klasse des Fensters und traegen laut
   Messung keine zusaetzliche Vielfalt. Empfehlung 8.000/0 steht damit staerker.
3. **NEU: der Erzeugungs-Betriebspunkt gehoert in den Zuschnitt.** Bisher stand er nirgends
   als Parameter des Fensters, sondern implizit im Rezept. Vorschlag: `--tau-argmax-from-move`
   als Pflichtfeld des v25-Rezepts, Wert aus der Kurve (heute: 12 schlaegt 30 um 0,12
   Spalten; ein Punkt bei 1 ist noch nicht gemessen).
4. **NEU, offen: der hv2-Anteil koennte schneller ausrotieren.** hv2 war im Fenster der
   Spalten-Lieferant (0,73 gegen 0,19 des Sockels). Baut der Sockel selbst 0,42, ist dieses
   Argument schwaecher. Das beruehrt par.2 (Uebergangsabbildung) und ist NICHT entschieden --
   es ist ein Kandidat fuer den naechsten Zuschnitt, nicht fuer diesen.

**Ungeprueft, ausdruecklich:** ob ein aus diesem Material trainiertes Netz staerker spielt
oder in der ARENA mehr Spalten baut. Die Kennzahlen oben sind Material-Kennzahlen. Der
Schritt zur Arena kostet ein Training plus Gating und ist der naechste Entscheid.

## par.13 KONKRETE ZUSAMMENSETZUNG MIT DEN DREI SELF-PLAY-WEGEN (2026-09-07, 02:50; Nutzer: "dann gib mir nun eine konkrete fenster zusammensetzung mit den verschiedenen self play wegen (A, B, C)")

Die drei Wege sind in `PREREG_start_position_seeding.md` par.9b/9c definiert: **A** eine
Linie, erste k Halbzuege gesampelt, dann argmax (Regler im Wheel, gemessen); **B** Ausflug
von einer Stellung, Hauptlinie bleibt sauber (zu bauen, kostet eine Restpartie je Ausflug);
**C** KataGo-Form, ein Zug an zufaelliger Stelle weicht ab, aus breit gezogenen Kandidaten
per einer Netzbewertung gefiltert (zu bauen, kostenlos).

**Grundsatz: EIN Faktor je Arm.** Die Kampagne misst Arme einfaktoriell
(`generation_loop.md`; b03: "einziger Faktor gegen b01 der Zusatz-Schwarm"). A, B und C
gleichzeitig einzubauen waere kein Zuschnitt, sondern ein Gemisch, dessen Wirkung nicht
zuzuordnen ist. Der Vorschlag ist deshalb: **A in die Basis** (weil gemessen und gratis),
**C und B als je EIN Arm daneben**.

### Basis-Zuschnitt v25 (Weg A) -- die Zusammensetzung aus par.1, unveraendert

| Klasse | Quelle | Partien | Erzeugungsregel | volle Spalten je Seite |
| --- | --- | --- | --- | --- |
| **Sockel NEU** (Traeger) | G = v24-Generator, policy-aktiv | 4.000 | `--sims 100`, Wurzelrauschen an, **NEU: `--tau-argmax-from-move 12`** | **0,4225** (g) |
| Sockel G-1 (Traeger) | 135 der 400 `selfplay_v23-b01-policy_*` | 1.350 | Bestand, unveraendert | 0,189 (g) |
| hv2-Traeger (Traeger) | 45 der 180 aus `carriers_v23_hv2.txt` | 450 | Bestand | 0,732 (g) |
| Schwarm NEU | G, `--value-only --deterministic --no-root-noise` | 8.000 | unveraendert (ist bereits argmax) | 0,748 (g) |
| Schwarm G-1 | alle 800 `selfplay_v23-b01-value-*` | 8.000 | Bestand | 0,748 (g) |
| Sockel-Rest G-1 | die 265 uebrigen policy-Dateien | 2.650 | Bestand | 0,189 (g) |
| Sockel-Rest G-2 | hv2 | 3.550 | Bestand | 0,732 (g) |
| Schwarm G-2 | hv2 | 1.450 | Bestand | 0,732 (g) |
| **Summe** | | **29.450** (2.945 Dateien) | neu zu erzeugen: **12.000** | |

**Kennzahlen: Traeger 0,392 | Fenster 0,625.** Bezug v24 gemessen: 0,356 / 0,624. Beide
Waechter-Flaechen liegen damit ueber der Vor-Generation, ohne dass an der Zusammensetzung
etwas geaendert wurde. **Kosten unveraendert** (rund 11,9 h bei threads 11): der
Umschaltpunkt kostet keine Rechenzeit, er aendert nur, wie die Zugwahl aus der ohnehin
gerechneten Besuchsverteilung gezogen wird.

**Der einzige Eingriff gegenueber par.1 ist eine Zeile im Erzeugungsbefehl:**

```
python -u self_play.py --mode network --model <generator>.onnx --spec <spec> \
  --games 4000 --sims 100 --version v25-<gen>-policy --threads 11 --chunk 10 \
  --per-file 10 --seed <seed> --tau-argmax-from-move 12
```

### Arm C -- dieselbe Zusammensetzung, andere Abweichungsregel

**Zusammensetzung Zeile fuer Zeile IDENTISCH zur Basis.** Einziger Unterschied: waehrend der
Erzeugung des **Sockels NEU** weicht in 5 % der Partien an einer exponentiell verteilten
Stelle GENAU EIN Zug ab (3 bis 10 Kandidaten gleichverteilt gezogen, jeder eine
Netzbewertung, der beste gespielt), danach laeuft die Partie normal weiter.

- **Kosten: 0** -- eine Linie, keine Zusatzpartie; die Kandidaten-Bewertung ist ein
  Vorwaertspass, den die Suche ohnehin macht.
- **Bau: rund 40 Zeilen** in `unified_game_loop` plus zwei Flags (par.9c).
- **Erwartete Kennzahlen: wie die Basis** (ein abweichender Zug in 5 % der Partien bewegt
  den Spaltenschnitt nicht messbar) -- **das ist der Punkt**: C zielt nicht auf die
  Kennzahl, sondern auf die ABDECKUNG (Stellungen, die eine volle Suche nie erzeugt).
- **Messgroesse ist deshalb nicht der Spaltenschnitt, sondern die bedingte Vielfalt**
  (`tools/probes/paired_corpus_divergence_probe.py`, gegen die Basis mit gleichem Seed) und
  spaeter Tor 1/2 des trainierten Netzes.

### Arm B -- eine eigene Ausflug-Klasse

Ausfluege von Sockel-Stellungen: je Ausflug k Zuege mit Temperatur, dann argmax bis zum
Ende; die Hauptpartie laeuft unberuehrt weiter. Vorbild ist der Seeding-Schwarm b03
(`PREREG_start_position_seeding.md` par.7), der genau das offline gemacht hat.
**Value-only**, wie b03 -- die Ausfluege tragen keine Policy-Ziele.

Zwei Fassungen, weil das Fenster eine stationaere Groesse hat:

| Fassung | Aenderung | Partien | Traeger | Fenster | neu zu erzeugen |
| --- | --- | --- | --- | --- | --- |
| **B1 zusaetzlich** | +2.000 Ausfluege | 31.450 | 0,392 | 0,623 (a) | 14.000 |
| **B2 im Tausch** | +2.000 Ausfluege, dafuer 2.000 hv2 weniger (1.450 Schwarm G-2 + 550 aus dem Sockel-Rest G-2) | 29.450 | 0,392 | 0,616 (a) | 14.000 |

Spaltenwert der Ausflug-Klasse mit **0,60 ANGENOMMEN** (sie starten aus Sockel-Stellungen
und laufen argmax; gemessen ist nichts) -- beide Fenster-Werte oben sind damit Schaetzungen,
nicht Messungen. **B2 haelt die stationaere Form** und ist deshalb vorzuziehen; B1 waere ein
einmaliger Groessensprung, der die naechste Rotation verschiebt.

**Kosten B: rund +50 min** (2.000 Ausfluege, Restlaenge rund 44 % einer Vollpartie bei
Verzweigung in R2-4, 3,365 s je Vollpartie -- alles aus `measured_runtimes.md`, die
Restlaenge aus par.7). **Bau: par.9**, Zustands-Klon plus Zweig in derselben Closure.

### Reihenfolge und was zuerst zu entscheiden ist

1. **Basis (A) ist entscheidungsreif.** Sie braucht nur den Generator-Entscheid (par.11 A)
   und den Umschaltpunkt. Fuer den Umschaltpunkt fehlt ein Punkt bei k = 1 (rund 10 min),
   weil 12 heute nur gegen 30 und gegen "aus" gemessen ist.
2. **C ist der billigste naechste Bau** und laesst die Zusammensetzung unberuehrt -- er
   kann auch NACH der v25-Erzeugung als eigener Arm kommen, ohne den Zuschnitt zu aendern.
3. **B ist der teuerste und der einzige, der ZIELEN kann.** Er lohnt, wenn C zeigt, dass
   zufaellige Abweichung nicht reicht, oder wenn eine Auswahlregel vorliegt (Unsicherheit,
   Spaltenfortschritt).

**Nicht entschieden:** nichts davon. Die Erzeugung startet nur auf Anweisung.

### par.13a DEN G-1-SOCKEL NEU ERZEUGEN (Nutzer 2026-09-07, 02:55: "den sockel aus der vorgeneration koennen wir ebenfalls neu erstellen mit mehr spalten")

**Der Gedanke.** Die gesampelten G-1-Sockel-Partien sind Temperatur-Artefakt-Material
(0,189 volle Spalten, Messung 3-V erklaert warum). Sie werden bisher UEBERNOMMEN, weil sie
schon da sind. Man kann sie stattdessen mit dem neuen Betriebspunkt neu erzeugen.

| Variante | was neu erzeugt wird | Traeger | Fenster | Partien neu | Erzeugung |
| --- | --- | --- | --- | --- | --- |
| Basis (par.13) | 12.000 (Sockel + Schwarm G) | 0,392 | 0,625 | 12.000 | 11,2 h |
| **V1** | dazu die **1.350 G-1-TRAEGER** | **0,447** | 0,636 | 13.350 | 12,5 h |
| **V2** | dazu **alle 4.000 gesampelten G-1-Sockelpartien** (1.350 Traeger + 2.650 Rest) | **0,447** | **0,657** | 16.000 | 15,0 h |

(Bezug v24 gemessen: Traeger 0,356 / Fenster 0,624 / Erzeugung 11,9 h. Der Schwarm G-1
bleibt in allen Varianten Bestand -- er ist bereits argmax und mit 0,748 die
spaltenreichste Klasse; neu zu erzeugen waere dort reine Kostenverschwendung.)

**Mit welchem Generator?** Das ist die eigentliche Frage, und sie entscheidet, ob das noch
eine Rotation ist:
- **Mit dem ALTEN Generator (`v23-b01` mit K3-P), neuem Betriebspunkt:** die
  Generationen-Mischung bleibt erhalten (zwei verschiedene Netze im Fenster), nur das
  Temperatur-Artefakt verschwindet. **Empfohlen.**
- **Mit dem NEUEN Generator:** dann traegt das Fenster nur noch EIN Netz plus hv2. Das ist
  keine Rotation mehr, sondern ein Ein-Generator-Fenster -- eine andere Fenster-Philosophie,
  nicht ein anderer Parameter. Nicht empfohlen, ohne dass jemand geprueft hat, wofuer die
  Mischung ueberhaupt da ist.

**Was fuer den Vorschlag spricht.** Der Zweck des Alt-Bestands ist laut
[[project_replay_window_strategy]] VOLUMEN fuer den datenhungrigen Value-Kopf ("Policy im
Warm-Start-Regime gesaettigt, Value-Kopf log-linear hungrig"), nicht Zeit-Vielfalt. Volumen
laesst sich neu erzeugen; ob es aus 2026-09 oder 2026-08 stammt, ist dem Value-Kopf gleich.
Und die 0,189 sind kein Merkmal jener Generation, sondern ein Messfehler in der Erzeugung,
den wir seit heute Nacht kennen.

**Was dagegen spricht.** (a) V2 kostet 3,8 h mehr Erzeugung, ein Drittel Aufschlag. (b) Der
Vorteil ist im TRAEGER klein (V1 und V2 sind dort identisch, 0,447 -- die 2.650 sind
Value-Material und beruehren die Policy nicht); der Unterschied zwischen V1 und V2 sind
0,021 Fenster-Kennzahl. (c) Ungeprueft ist, ob das Fenster durch mehr Gleichartigkeit
schmaler wird: alle vier Sockel-Klassen kaemen dann aus demselben Betriebspunkt, und die
bedingte Vielfalt ueber die Klassen hinweg ist nie gemessen worden.

**Empfehlung: V1.** Sie holt den ganzen Traeger-Gewinn (0,392 auf 0,447, das ist die Zahl,
an der der Spalten-Waechter haengt) fuer 1,3 h Aufschlag und laesst die Value-Masse
unberuehrt. V2 kauft 0,021 Fenster-Kennzahl fuer weitere 2,5 h -- das ist der schlechtere
Handel, solange nicht gezeigt ist, dass die Fenster-Kennzahl selbst etwas bewirkt.

**Beide Varianten aendern die Klassenaufteilung NICHT** -- nur, ob eine Klasse kopiert oder
neu gefahren wird. Der Waechter par.7 und die Groesse 29.450 bleiben.

## par.14 SOCKEL-ARME v25: das volle Paket (Nutzer 2026-09-07, 03:30: "temp bestand, temp variabel ueber moegliche aktionen, umschaltpunkt, umschaltpunkt + c, temp variabel + c")

**Der Zuschnitt (par.13) bleibt unveraendert.** Variiert wird ausschliesslich, WIE die
4.000 Sockel-NEU-Partien erzeugt werden. Schwarm, G-1 und G-2 sind in allen Armen dieselben
Dateien -- der Schwarm wird EINMAL erzeugt und von allen Armen geteilt.

| Arm | Temperatur-Regime | Weg C | Was der Vergleich isoliert |
| --- | --- | --- | --- |
| **S1** | Bestand (roh proportional zu den Besuchen, T = 1) | aus | Kontrolle |
| **S2** | variabel ueber die Zahl der gueltigen Aktionen | aus | S2 gegen S1: bringt eine milde, aktionsabhaengige Schaerfung dasselbe wie hartes Umschalten? |
| **S3** | Umschaltpunkt (argmax ab Halbzug k) | aus | S3 gegen S1: was das Sampling kostet (Messung 3-V, jetzt bis ins Netz) |
| **S4** | Umschaltpunkt | **an** | S4 gegen S3: was C liefert, wenn die Zugwahl greedy ist |
| **S5** | variabel | **an** | S5 gegen S2: was C liefert, wenn die Zugwahl mild gesampelt bleibt |

Das ist ein 3 x 2-Feld ohne die Zelle "Bestand plus C" -- sie faellt weg, weil der Bestand
in Messung 3-V die schlechteste Spaltenzahl hatte und eine Abweichung je Partie daran
nichts aendert.

### Der fehlende Baustein: variable Temperatur im NETZ-Pfad (S2, S5)

Der Netz-Pfad hat heute keine Temperatur (par.9d): `net_drafting_policy` zieht mit
`weighted_index` aus den ROHEN Besuchszahlen, fest T = 1. Die aktionsabhaengige Formel
existiert nur im HEURISTIK-Pfad (`drafting_policy`, self_play.rs:1656: `n > 50 -> 0,7`,
`n > 15 -> 0,4`, sonst `0,15`, Port von self_play.py:172).

**Zu bauen:** dieselbe Formel im Netz-Pfad, als Knopf mit Default aus (bitidentisch).
Bauform wie `tau_argmax_from_move`: Env plus CLI-Flag, kein Spec-Feld. Der Eingriff ist
eine Zeile in `net_drafting_policy` -- statt `weights = visits` dann
`weights = visits^(1/T(n))`. **Geschaetzt (nicht gemessen): rund 30 Zeilen mit Getter,
Warnung und Test.** Kleiner als Weg C.

**Warum diese Form und nicht KataGos zeitabhaengige Abklingung** (par.9d, T 0,8 -> 0,2 mit
Halbwertszeit = Brettbreite): die aktionsabhaengige Formel ist im Projekt bereits im
Einsatz und hat das hv2-Lehrermaterial erzeugt, das im Fenster mit 0,732 vollen Spalten die
zweitbeste Klasse ist. Sie ist damit die naheliegendere Wahl, und sie trifft denselben
Punkt: nie ganz greedy, aber scharf, wo wenige Zuege zur Wahl stehen.

### Kosten (aus `docs/measured_runtimes.md`, gerechnet)

| Posten | Kosten |
| --- | --- |
| 5 x 4.000 Sockel-Partien (3,365 s je Partie, threads 11) | 18,7 h |
| Schwarm 8.000, EINMAL fuer alle Arme (3,674 s) | 8,2 h |
| **Erzeugung gesamt** | **26,9 h**, auf zwei Maschinen grob **13,4 h** |
| 5 Trainings (GPU, seriell, rund 4.845 s je Lauf) | 6,7 h |
| Tor 2a je Arm (200 Partien @400 argmax) | 1,9 h |
| Tor 1 je Arm (gepaartes Gating, Deckel 200 Paare) | rund 1,2 h je Arm |

**Vorschlag zur Staffelung, damit nicht alle fuenf durch die volle Abnahme muessen:** erst
alle fuenf Sockel erzeugen und die MATERIAL-Kennzahlen vergleichen (volle Spalten,
bedingte Vielfalt, Policy-Entropie -- kostet Minuten, `corpus_sanity_check.py` und
`paired_corpus_divergence_probe.py`), dann alle fuenf trainieren (6,7 h GPU, laeuft neben
der CPU), dann Tor 2a fuer alle fuenf (1,9 h) und Tor 1 nur fuer die drei besten. Das
spart rund 2,5 h Gating, ohne einen Arm ungemessen zu lassen.

**Wichtig zur Lesart der Material-Kennzahlen:** sie entscheiden NICHT, welcher Arm gewinnt
(Messung 3-V hat gezeigt, dass Materialvorteil und Netzstaerke zwei Fragen sind). Sie
dienen nur der Reihenfolge und dem Nachweis, dass die Knoepfe ueberhaupt gewirkt haben.

### Abhaengigkeiten vor dem Start

1. **Weg C muss durch den Build** (par.9e: gebaut, ungetestet) -- cargo test, Wheel,
   Anker-Invarianz.
2. **Der variable-Temperatur-Knopf muss gebaut werden** (S2, S5).
3. **Der Umschaltpunkt k muss festliegen.** Gemessen sind aus, 12 und 30
   (0,195 / 0,4225 / 0,300); der Punkt bei 1 laeuft.
4. **Generator-Entscheid** (par.11 A: b05 oder b06) -- betrifft alle Arme gleich.
5. **Zweite Maschine:** gleiches Wheel, gleicher Kontrakt-Stempel
   (`engine_config_json`), sonst sind die Korpora nicht vergleichbar. Der Stempel gehoert
   in den Lauf-Bericht jeder Charge.

**Nicht entschieden, Start nur auf Anweisung.**

### par.14a GENERATOR ENTSCHIEDEN (Nutzer 2026-09-07, 03:35: "generator wird b06")

**Generator der v25-Erzeugung ist `v24-b06_brierbest`**, der amtierende Champion
(Elo 1309), mit seiner Champion-Spec `models/v24-b06_brierbest.spec.json` -- also MIT
K3-P (Modus 1, C 1,0) und `envelope_hull_form` 1. Damit ist par.11 A entschieden und der
Stand von par.4 (b05 ohne K3-P, Nutzer 2026-09-06 11:40) ueberholt.

**Was daraus folgt:**
- Val-Pool-Regex `^selfplay_v24-b06-` (par.6 Punkt 2: Dateien heissen nach dem Generator).
- Startgewicht des Trainings: `alphazero_v24-b06_brierbest.pth` (par.6 Punkt 3).
- Spalten-Waechter-Bezug (par.7, Generator-Flaeche): **0,4975** (Tor 2a mit Knopf,
  `tor2a_v24b06.json`), nicht 0,4825.
- Das Material entsteht MIT dem Champion-Knopf -- konsistent mit dem Grundsatz
  "Self-Plays nur vom Champion" (Nutzer 2026-09-06, 17:05).

**Ebenfalls entschieden (03:35): S2 und S5 werden gebaut**, also die aktionsabhaengige
Temperatur im Netz-Pfad (par.14). Damit sind alle fuenf Arme baubar.

### par.14b DOSIS UND UMSCHALTPUNKT ENTSCHIEDEN (Nutzer 2026-09-07, 03:38)

- **Umschaltpunkt k = 1** fuer S3 und S4 (belegt: Messung 3-V, vierter Punkt -- die Reihe
  ist monoton, der Randpunkt gewinnt mit 0,5325 gegen 0,4225 bei k=12 und 0,195 im
  Bestand). **Es wird also gar kein Halbzug mehr gesampelt.**
- **Abweichungsrate 1,0** fuer S4 und S5 (`--deviate-prob 1.0`), also eine Abweichung in
  JEDER Partie. Begruendung gegen KataGos 5 %: bei 4.000 Sockel-Partien waeren 5 % nur 200
  Abweichungen, und da im Mittel die halbe Restpartie hinter dem Knick liegt, stammten
  rund 2,5 % des Materials aus der Zeit danach -- unter jeder Aufloesung. Bei Rate 1,0 sind
  es rund 50 %. KataGos Rate ist fuer Millionen Partien gedacht, nicht fuer viertausend.
  **Nebenwirkung, benannt:** die tatsaechliche Rate liegt leicht darunter, weil der
  Vorzugs-Waechter (par.9e der Seeding-Prereg) Abweichungen ueberspringt, wenn der Bauer-
  oder Kuppel-Vorzug greift.

**Was damit ueber die Streuung im Sockel gesagt ist** (Nutzer-Rueckfrage: "sprich wir
machen nun keine gesampelten halbzuege weil uns das wurzelrauschen eh schon etwas zufall
reinhaut?"): ja. Bei k = 1 bleiben drei Quellen -- das Gumbel-Wurzelrauschen der Suche
(`add_root_noise` ist im Sockel AN, wirkt bei JEDER Suche, par.9d der Seeding-Prereg), der
Spiel-Zufall (Auslagen, Platten, Wertungsplatten) und bei S4/S5 die eine Abweichung je
Partie. Zwei Belege, dass das fuer ZUSTANDSVIELFALT reicht: 399 von 400 distinkten
Endbrettern bei k = 12 (Messung 3-V), und die Schwarm-Klasse faehrt seit v23 voellig
rauschfrei (`--deterministic --no-root-noise`) und ist mit 0,748 die spaltenreichste
Klasse des Fensters.

**Was damit NICHT gesagt ist:** dass es fuer den VALUE-Kopf reicht. Alle diese Stellungen
sind on-policy. Genau diese Luecke ist der Grund fuer Weg C, und ob sie sich auswirkt,
zeigt erst S4 gegen S3 nach dem Training.

## par.14c DIE BEFEHLE (Generator b06, Stand 2026-09-07 03:40; NICHT starten, bevor der Build durch ist)

**Vor der ersten Charge auf JEDER Maschine** -- der Kontrakt-Stempel muss ueberall gleich
sein, sonst sind die Korpora nicht vergleichbar und es faellt erst beim Manifest-Vergleich
auf:

```
python -X utf8 -c "import json, mosaic_rust as mr; c=json.loads(mr.engine_config_json()); print(c['input_size'], c['contract_hash'], c['envelope_hull_form'], c['envelope_flush_w'])"
```

Erwartet: `744 20b442a8164f748d 1 0.0`. Weicht etwas ab, laeuft dort ein anderes Wheel.

**Gemeinsam fuer alle Chargen** (Konvention seit v23, im v24-Rezept par.6 dokumentiert):

```
export MOSAIC_STACK_DRAW_RESEARCH=1
```

### Die fuenf Sockel-Arme (je 4.000 Partien, gleicher Seed -- die Startbedingungen sind damit je Spielindex identisch und die Arme gepaart vergleichbar)

```
# S1 -- Bestand (Kontrolle): Zugwahl proportional zu den Besuchen
python -u self_play.py --mode network --model models/alphazero_v24-b06_brierbest.onnx \
  --spec models/v24-b06_brierbest.spec.json --games 4000 --sims 100 \
  --version v24-b06-policy-s1 --threads 11 --chunk 10 --per-file 10 --seed 20260907

# S2 -- variable Temperatur ueber die Zahl der gueltigen Aktionen
python -u self_play.py --mode network --model models/alphazero_v24-b06_brierbest.onnx \
  --spec models/v24-b06_brierbest.spec.json --games 4000 --sims 100 \
  --version v24-b06-policy-s2 --threads 11 --chunk 10 --per-file 10 --seed 20260907 \
  --action-temp 1

# S3 -- Umschaltpunkt 1 (durchgehend greedy)
python -u self_play.py --mode network --model models/alphazero_v24-b06_brierbest.onnx \
  --spec models/v24-b06_brierbest.spec.json --games 4000 --sims 100 \
  --version v24-b06-policy-s3 --threads 11 --chunk 10 --per-file 10 --seed 20260907 \
  --tau-argmax-from-move 1

# S4 -- Umschaltpunkt 1 plus Weg C (eine Abweichung je Partie)
python -u self_play.py --mode network --model models/alphazero_v24-b06_brierbest.onnx \
  --spec models/v24-b06_brierbest.spec.json --games 4000 --sims 100 \
  --version v24-b06-policy-s4 --threads 11 --chunk 10 --per-file 10 --seed 20260907 \
  --tau-argmax-from-move 1 --deviate-prob 1.0

# S5 -- variable Temperatur plus Weg C
python -u self_play.py --mode network --model models/alphazero_v24-b06_brierbest.onnx \
  --spec models/v24-b06_brierbest.spec.json --games 4000 --sims 100 \
  --version v24-b06-policy-s5 --threads 11 --chunk 10 --per-file 10 --seed 20260907 \
  --action-temp 1 --deviate-prob 1.0
```

**Namen:** `v24-b06-policy-sN` -- die Dateien heissen nach dem GENERATOR
([[feedback_selfplay_naming_convention]]), der Arm-Zusatz haengt hinten an. Der Val-Pool-
Regex `^selfplay_v24-b06-` (par.6) trifft alle fuenf.

**Flag-Namen S2/S5 vorbehaltlich des Baus** (`--action-temp`): der Baustein entsteht
gerade; sollte der Bau einen anderen Namen waehlen, steht er im Bericht und hier ist er
nachzuziehen.

### Der Schwarm (EINMAL, von allen Armen geteilt)

```
python -u self_play.py --mode network --model models/alphazero_v24-b06_brierbest.onnx \
  --spec models/v24-b06_brierbest.spec.json --games 8000 --sims 100 --value-only \
  --version v24-b06-value-argmax --threads 11 --chunk 10 --per-file 10 --seed 20260908 \
  --no-root-noise --deterministic
```

**OFFEN, vor diesem Befehl zu entscheiden (par.11 B):** 8.000 argmax und 0 gesampelt, oder
7.000 und 1.000. Der Befehl oben setzt 8.000/0 voraus (die Empfehlung); bei 7.000/1.000
kaeme ein zweiter Lauf mit `--games 1000 --value-only` OHNE `--no-root-noise
--deterministic` dazu.

### Aufteilung auf zwei Maschinen (Vorschlag)

| Maschine | Chargen | Dauer |
| --- | --- | --- |
| A (diese) | Schwarm 8.000, dann S1, S2 | 8,2 + 3,7 + 3,7 = 15,6 h |
| B (zweite) | S3, S4, S5 | 11,2 h |

Der Schwarm gehoert auf die Maschine, die zuerst frei wird -- er blockiert am laengsten und
alle Trainings brauchen ihn. **Die zweite Maschine braucht denselben Commit UND dasselbe
Wheel** (Stempel-Pruefung oben), sonst driften die Korpora.

### Nach jeder Charge

```
python -X utf8 tools/corpus_sanity_check.py data --pattern "selfplay_v24-b06-policy-sN_*.pkl" --out evaluations/artifacts/sanity_v25_sN.json
```

Damit stehen die Material-Kennzahlen (volle Spalten, Punkte, Strafleiste) je Arm fest,
bevor trainiert wird -- die Reihenfolge der Trainings richtet sich danach (par.14).

## par.15 ARBEITSTEILUNG SOCKEL / SCHWARM (Nutzer-Einwand 2026-09-07, 03:40; Koordinator-Aussage berichtigt)

**Was der Koordinator gesagt hatte** (Chat 03:38): der Schwarm laufe ganz ohne Rauschen und
sei trotzdem mit 0,748 die spaltenreichste Klasse -- als Beleg dafuer, dass Streuung
entbehrlich sei.

**Nutzer, woertlich:** *"der schwarm ist eigentlich nur fuer den value head da und es gibt
nur vielfalt aus dem spiel aber nicht aus der eigenen spielvarianz. da wissen wir ja
eigentlich dass nichts gelernt wird. die spalten werden in der policy erzogen, ich wuerd
vermutlich den schwarm mehr auf varianz trimmen und weniger auf spalten. sprich genau
umgekehrt zum sockel. das gute am rotierenden fenster ist, dass dann in den schwarm
maskierte sockel spiele reinkommen die wieder mehr auf spalten und weniger auf varianz
gehen."*

**Der Einwand trifft, die Koordinator-Aussage war schief.** Sie hat die Kennzahl der
falschen Klasse als Beleg genommen: der Schwarm ist policy-maskiert (`--value-only`), sein
Spaltenreichtum ist fuer seine Aufgabe ohne Bedeutung. Was fuer ihn zaehlt, ist die
Abdeckung des Zustandsraums.

**Die Arbeitsteilung, die daraus folgt:**

| Klasse | Aufgabe | Optimieren auf | Warum |
| --- | --- | --- | --- |
| **Sockel** (Traeger, policy-aktiv) | Prior erziehen | **Spalten** | Der Spalteneffekt haengt am PRIOR: flache Suche baut 0,82, tiefe 0,50 (`PREREG_search_depth_column_optimum.md` par.2l/par.8b). Der Prior lernt aus den Traegern. |
| **Schwarm** (policy-maskiert) | Value-Kopf fuettern | **Varianz / Abdeckung** | Der Value-Kopf lernt Zustand -> Ergebnis. Spaltenreiche, aber enge Zustaende helfen ihm nicht; er braucht Breite. |

**Das Rotations-Argument ist der tragende Teil und war bisher nirgends notiert.** Die
Sockel-Partien dieser Generation werden in der naechsten zu maskiertem Value-Material
(par.1: "Sockel-Rest G-1" wandert in den Schwarm). Der Schwarm bekommt seinen
spaltenreichen, varianzarmen Anteil also von selbst aus der Rotation -- er muss nicht dafuer
gebaut werden. Damit ist die Aufgabenteilung nicht nur zulaessig, sondern selbstkorrigierend.

**Der Preis, der gemessen und nicht angenommen gehoert.** Mehr Temperatur im Schwarm heisst
mehr Abdeckung, aber auch verzerrte Wertziele: `z` ist verzerrt, wenn Explorationszuege im
Pfad liegen (Willemsen/Baier/Kaisers, `RESEARCH_alphazero_improvements_2026-08-01.md`
Fund 1). Der Value-Kopf lernt dann, Stellungen unter maessigem Spiel zu bewerten, waehrend
er sie in der Suche unter gutem braucht. **Weg C mildert genau das** (Abweichung, danach
sauber weiterspielen), Temperatur nicht.

**Nutzer-Vorschlag fuer die Erzeugung (2026-09-07, 03:40):**
- **Sockel: Umschaltpunkt 1 + Weg C** -- maximale Zugqualitaet, Streuung nur aus
  Wurzelrauschen und der einen Abweichung.
- **Schwarm: variable Temperatur (0,8 bis 0,2, auf Basis der moeglichen Aktionen je Runde)
  + Weg C** -- maximale Abdeckung, Abweichung zusaetzlich.

**Was dafuer noch fehlt:** der gebaute Knopf faehrt die HEURISTIK-Staffel (0,7 / 0,4 /
0,15), nicht 0,8 bis 0,2. Die Nutzer-Form braucht entweder andere Konstanten oder eine
glatte Interpolation zwischen 0,8 und 0,2 ueber die Aktionszahl. **Beides ist eine Zeile im
bereits gebauten `action_temp_for`** (self_play.rs:424) plus ein zweiter Knopfwert; die
Bauform steht.

**Folge fuer die Armstruktur par.14:** die fuenf Arme variieren bisher NUR den Sockel und
halten den Schwarm fest. Das bleibt richtig, solange man den Sockel-Faktor isolieren will.
Der Schwarm-Vorschlag ist ein EIGENER Faktor und gehoert in einen eigenen Arm --
andernfalls misst man zwei Aenderungen auf einmal. **Vorschlag: erst die fuenf
Sockel-Arme, dann der Schwarm-Arm gegen den Sieger.** Nicht entschieden.

## par.16 SCHWARM-ENTSCHEID: variable Temperatur plus Weg C, alle 8.000 (Nutzer 2026-09-07, 09:03: "#2 ist obsolet in der form. es werden dann 8000 mit temp. variabel + c")

**Entschieden.** Der Schwarm NEU wird nicht mehr argmax-deterministisch erzeugt, sondern
mit der aktionsabhaengigen Temperatur (`--action-temp 1`) und Weg C (`--deviate-prob 1.0`),
alle 8.000 Partien. Damit ist **par.11 B (8.000/0 gegen 7.000/1.000) gegenstandslos** -- die
Frage lautete, wie viel argmax und wie viel gesampelt; jetzt ist die ganze Klasse auf
Abdeckung gestellt. Ebenfalls entschieden: **Messung 3-W wird gestrichen** (Nutzer 09:03,
"#5 kannst streichen"); sie beantwortet dieselbe Frage wie S1 gegen S3 in der Armstruktur.

**Begruendung steht in par.15:** der Schwarm ist policy-maskiert, sein Spaltenreichtum ist
fuer seine Aufgabe bedeutungslos, und die Rotation liefert ihm den spaltenreichen Anteil in
der naechsten Generation von selbst.

### Zwei Folgen, die benannt gehoeren

**1. Die dritte Waechter-Flaeche (par.7, "Fenster") wird bedeutungslos und muss fallen.**
Sie mittelt volle Spalten ueber ALLE Klassen. Solange beide Klassen dasselbe Ziel hatten,
war das eine sinnvolle Sammelgroesse. Jetzt haben sie GEGENSAETZLICHE Ziele -- der Sockel
soll spaltenreich sein, der Schwarm breit -- und ein Mittelwert ueber beide misst nichts
mehr. Gerechnet mit einer Annahme von 0,35 fuer den temperierten Schwarm (Bandbreite aus
Messung 3-V: volle Temperatur 0,195, argmax 0,5325):

| | Traeger-Flaeche | Fenster-Flaeche |
| --- | --- | --- |
| v24 gemessen | 0,356 | 0,624 |
| v25 mit argmax-Schwarm | 0,468 | 0,640 |
| **v25 mit temperiertem Schwarm** | **0,468** (unveraendert) | **0,532** (a) |

Die Traeger-Flaeche steigt weiter deutlich ueber v24; die Fenster-Flaeche faellt -- **und
zwar absichtlich**. Wer sie als Waechter behaelt, wuerde eine gewollte Aenderung als
Verschlechterung melden. **Vorschlag: Flaeche 3 wird von einem TOR zu einer
Diagnosezeile**, je Klasse getrennt ausgewiesen statt gemittelt. Die beiden Tor-Flaechen
(Generator-Instrument, Arena) bleiben unveraendert -- sie messen das NETZ und sind von der
Klassenaufteilung unabhaengig.

**2. Der Schwarm braucht eine eigene Kennzahl.** Wenn Abdeckung sein Ziel ist, misst man
ihn nicht an vollen Spalten, sondern an Vielfalt. Vorhanden und passend:
`tools/probes/corpus_state_diversity_probe.py` (distinkte Belegungsmuster je Runde,
distinkte Endbretter) und `tools/probes/paired_corpus_divergence_probe.py` (bedingte
Vielfalt bei identischen Startbedingungen, gebaut 2026-09-07). **Vorab festgelegt: der
temperierte Schwarm muss in den distinkten Endbrettern je Seite und in den distinkten
Zustaenden je Record mindestens den argmax-Schwarm erreichen** -- sonst hat die Temperatur
Zugqualitaet gekostet, ohne Abdeckung zu kaufen, und der Entscheid waere zurueckzunehmen.

### Offen, weil vom Nutzer nicht entschieden

**Wurzelrauschen im Schwarm.** Der Bestandsbefehl faehrt `--no-root-noise --deterministic`.
`--deterministic` MUSS fallen (es erzwingt argmax und wuerde die Temperatur wirkungslos
machen). Ob auch `--no-root-noise` faellt, ist eine eigene Frage: das Gumbel-Rauschen ist
eine zusaetzliche Streuquelle und passt zum Ziel Abdeckung, kostet aber Zugqualitaet
(gemessen: die Sockel-Konfiguration mit Rauschen erreicht bei k=1 0,5325, das Instrument
ohne Rauschen 0,8200 -- eine Differenz von 0,29). **Empfehlung: Wurzelrauschen AN**, weil
Abdeckung das erklaerte Ziel der Klasse ist und der Spaltenverlust dort nicht zaehlt.

### Der angepasste Schwarm-Befehl (ersetzt den in par.14c)

```
python -u self_play.py --mode network --model models/alphazero_v24-b06_brierbest.onnx \
  --spec models/v24-b06_brierbest.spec.json --games 8000 --sims 100 --value-only \
  --version v24-b06-value-tempc --threads 11 --chunk 10 --per-file 10 --seed 20260908 \
  --action-temp 1 --deviate-prob 1.0
```

Weder `--deterministic` noch `--no-root-noise` (siehe oben). Kosten rund 7,5 h statt 8,2 h.
Der Name traegt jetzt `-value-tempc` statt `-value-argmax`, damit im Fenster-Manifest
sichtbar bleibt, wie die Klasse erzeugt wurde.

### par.16a WURZELRAUSCHEN AN, und der Split-Gedanke (Nutzer 2026-09-07, 09:05)

**Entschieden: Wurzelrauschen im Schwarm AN.** Weder `--deterministic` noch
`--no-root-noise`; der Befehl in par.16 gilt damit unveraendert. Begruendung wie dort:
Abdeckung ist das erklaerte Ziel dieser Klasse, der Spaltenverlust zaehlt in ihr nicht.

**Nutzer, woertlich (09:05):** *"ich ueberleg mir gerade noch einen saubern split damit wir
nicht nur verrauschte daten in der erstellung fuer den value haben. vielleicht bauen wir
50% der spiele eine meiner ideen ein: den weg B sozusagen."*

**Der Gedanke loest den Trade-off, den par.15 benennen musste.** Eine vollstaendig
temperierte Value-Klasse kauft Abdeckung mit verzerrten Zielen: `z` ist verzerrt, wenn
Explorationszuege im Pfad liegen (Willemsen/Baier/Kaisers,
`RESEARCH_alphazero_improvements_2026-08-01.md` Fund 1). **Weg B hat diesen Defekt nicht** --
der Ausflug weicht ab und spielt danach sauber zu Ende, das Ziel ist also der Wert der
abgewichenen Stellung unter GUTEM Spiel. Ein Split liefert damit beides: eine Haelfte
breite, verrauschte Abdeckung, eine Haelfte abweichende Stellungen mit unverzerrten Zielen.

**Und Weg B braucht dafuer KEINEN neuen Engine-Code** (Befund am Code, 2026-09-07): die
Offline-Fassung ist `--seed-positions` (abgenommen mit b03, par.7) plus
`--tau-argmax-from-move`. Eine Partie startet ab einer Stellung, sampelt k Halbzuege und
spielt danach greedy -- genau der zweiphasige Ausflug. Die Startstellungen kommen aus dem
SOCKEL derselben Generation, der ab sofort sauber gespielt ist (k = 1), also aus Stellungen,
die unter gutem Spiel entstanden sind.

**Kosten (gerechnet, Restlaenge 44 % einer Vollpartie aus par.7):**

| Variante | Erzeugung | Records im Schwarm |
| --- | --- | --- |
| 8.000 Vollpartien temperiert | 7,5 h | rund 1.312.000 |
| **4.000 Voll + 4.000 Ausfluege** | **5,4 h** | rund 944.000 (72 %) |

Der Split ist also **billiger**, kostet aber **28 % der Zustaende**, weil ein Ausflug nur
rund 72 Records liefert statt 164. **Das ist die einzige echte Abwaegung dieses
Vorschlags:** der Value-Kopf ist datenhungrig ([[project_corpus_dose_result]]: doppelte
Menge, 6 von 6 auf beiden Orakel-Metriken, Arena-bestaetigt 479:321). Wer die Zustandszahl
halten will, faehrt entweder mehr Ausflug-Partien (5.500 statt 4.000 gleicht es aus, +0,6 h)
oder nimmt die 28 % in Kauf, weil die gewonnenen Stellungen wertvoller sind.

**Abhaengigkeit in der Reihenfolge:** die Ausfluege brauchen Startstellungen aus dem Sockel,
also muss der Sockel VOR dieser Schwarm-Haelfte laufen. Fuer die zweite Maschine heisst das:
sie faehrt zuerst Sockel-Arme, nicht die Schwarm-Haelfte mit Ausfluegen.

**Offen (Nutzer):** (a) das Verhaeltnis -- 50/50 oder mehr Ausfluege, um die Zustandszahl zu
halten; (b) die Kuratierungsregel fuer die Startstellungen (b03 nahm Spieler am Zug,
R2-4, Spaltenfortschritt 3-5, par.7 -- fuer den Value-Kopf koennte eine breitere Regel
besser sein); (c) wie viele Halbzuege der Ausflug sampelt, bevor er greedy wird.

### par.16b SPLIT ENTSCHIEDEN: 50/50 (Nutzer 2026-09-07, 09:16)

Die Value-Klasse (8.000 Partien) wird geteilt:

| Haelfte | Partien | Erzeugung | Was sie liefert |
| --- | --- | --- | --- |
| **V-a** | 4.000 | variable Temperatur (`--action-temp 1`) plus Weg C, Wurzelrauschen AN | breite Abdeckung; Value-Ziele durch die Temperatur verzerrt |
| **V-b** | 4.000 | **greedy** (`--tau-argmax-from-move 1`) plus **Weg B** (Ausfluege, in der Engine) | abweichende Stellungen mit UNVERZERRTEN Zielen |

**Warum V-b greedy und nicht temperiert** (par.9f der Seeding-Prereg): der Ausflug startet
aus der Stellung, in der er entsteht. Waere die Hauptpartie temperiert, startete er aus
einer verrauschten Lage, und die Trennung, wegen der der Split gebaut wird, waere dahin --
man haette zwei Sorten Abweichung in derselben Partie.

**Kosten:** V-a rund 3,7 h; V-b rund 3,7 h Hauptpartien plus rund 1,6 h Ausfluege (44 %
Restlaenge), zusammen rund 9 h statt 7,5 h fuer eine ungeteilte temperierte Klasse. Der
Aufschlag kauft 4.000 Ausflug-Trajektorien mit sauberen Zielen.

**Offen bleibt die Zaehlung** (par.9f): ob ein Ausflug als eigene Partie im Fenster-Manifest
zaehlt oder zu seiner Hauptpartie gehoert. Das entscheidet, ob V-b 4.000 oder 8.000 Zeilen
beitraegt und damit, ob das Fenster seine Groesse von 29.450 Partien haelt.
