<!-- STATUS: OFFEN | Frage: Wie wird das v25-Trainingsfenster zugeschnitten (stationaere Rotation aus docs/window_generation.svg, G = v24), und wie wird dabei der Spaltenbau gegen schleichendes Verlernen gesichert? | Beleg: Zuschnitt vom Nutzer festgelegt (2026-09-04, 21:50), nichts gebaut: Sockel 4.000 G + 1.350 G-1 + 450 G-2, Schwarm 8.000 G + 8.000 G-1 + 2.650 Sockel-Rest G-1 + 3.550 + 1.450 G-2 (par.1); hv2-Uebergangsabbildung ENTSCHIEDEN (par.2: 45 Traeger + 135 Ex-Traeger + 365 Schwarm); Manifest-Generator --pick gebaut (par.3); Spalten-Waechter auf drei Flaechen (par.7; v24-Fenster 44,8 % Seiten mit voller Spalte, hv2 ist spaltenreich 0,73, die gesampelten Klassen 0,19). Value-Klasse zu argmax verschoben (Nutzer 2026-09-05, par.9: 8.000/0 oder 7.000/1.000 offen). Bedingung: v24 nimmt die Champion-Kante, sonst Generatorwahl-Regel (par.4). -->

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
2. Val-Pool-Regex fuer v25 (v24: `^selfplay_v23-b01-`; v25 analog
   `^selfplay_v24-b01-`, Dateien heissen nach dem Generator).
3. Startgewicht des v25-Trainings (v24-Regel: der Generator-Checkpoint).

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

