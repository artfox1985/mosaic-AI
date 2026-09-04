<!-- STATUS: OFFEN | Frage: Wie wird das v25-Trainingsfenster zugeschnitten (stationaere Rotation aus docs/window_generation.svg, G = v24), und wie wird dabei der Spaltenbau gegen schleichendes Verlernen gesichert? | Beleg: Zuschnitt vom Nutzer festgelegt (2026-09-04, 21:50), nichts gebaut: Sockel 4.000 G + 1.350 G-1 + 450 G-2, Schwarm 8.000 G + 8.000 G-1 + 2.650 Sockel-Rest G-1 + 3.550 + 1.450 G-2 (par.1); hv2 als G-2 braucht eine Uebergangsabbildung wie v21 (par.2, Vorschlag); Manifest-Generator braucht eine seedbare Teilauswahl je Klasse (par.3); Spalten-Waechter auf drei Flaechen (par.7). Bedingung: v24 nimmt die Champion-Kante, sonst Generatorwahl-Regel (par.4). -->

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
| Schwarm NEU | G = v24 Self-Play, `--value-only` (6.000 argmax + 2.000 gesampelt) | 8.000 | 800 |
| Schwarm G-1 (komplett) | alle 800 `selfplay_v23-b01-value-*` | 8.000 | 800 |
| Sockel-Rest G-1 (Nicht-Traeger) | die 265 uebrigen `selfplay_v23-b01-policy_*` | 2.650 | 265 |
| Sockel-Rest G-2 (vollstaendig) | hv2, siehe par.2 | 3.550 | 355 |
| Schwarm G-2 (Auffuellung) | hv2, siehe par.2 | 1.450 | 145 |

**Summe 29.450 Partien = 2.945 Dateien** (1.200 G + 1.200 G-1 + 545 hv2),
dieselbe Groesse wie das v24-Fenster (`PREREG_v24_window.md` par.6d: 2.945
Dateien). Traegeranteil 5.800 wie v24. Der hv2-Anteil faellt von 17.450 auf
5.450 Partien; G-3 und aelter (hier: nichts mehr) rotieren vollstaendig aus.

## par.2 hv2 als G-2: Uebergangsabbildung (VORSCHLAG, Nutzer-Entscheid offen)

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
Liste reproduzierbar ist. **Alternative**, falls der Nutzer die Ex-Traeger
lieber ganz ausrotieren will: 45 Traeger plus 500 aus dem bisherigen Schwarm.

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

1. Nutzer-Entscheid zu par.2 (welche 500 maskierten hv2-Dateien).
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
| **Fenster** (Korpus-Eigenschaft, NEU hier) | Seiten mit voller Spalte je Klasse UND ueber das ganze Fenster (Partien-gewichtet) | `tools/corpus_sanity_check.py data --pattern <Klasse>` je Posten aus par.1, dann gewichtete Summe | v24-Fenster: Value-Klasse `selfplay_v23-b01-value-*` (Tor 0 nach der Erzeugung), hv2-Anteil und Policy-Klasse beim Fensterbau messen | das v25-Fenster darf in der Fenster-Kennzahl NICHT unter dem v24-Fenster liegen |

Warum die dritte Flaeche: die beiden Tor-2-Flaechen messen das NETZ; die
Rotation aendert aber, WOVON es lernt. hv2-Material ist spaltenaermer als
das heutige (Value-Klasse v23 35,2 % Seiten mit voller Spalte gegen v24-Pilot
50,4 / 55 %, `PREREG_v24_window.md` par.7 und `geometric_envelope` 8.7d), die
Rotation von hv2 nach G-Material hebt die Fenster-Kennzahl also von selbst --
solange G nicht spaltenaermer spielt als G-1. Faellt die Fenster-Kennzahl
trotz Rotation, hat der Generator verlernt, bevor Tor 2 es an 200 Partien
sieht.

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
