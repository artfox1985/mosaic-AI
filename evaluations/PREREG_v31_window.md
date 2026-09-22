<!-- STATUS: ENTSCHIEDEN | Frage: Wie wird das v31-Fenster zugeschnitten, und traegt die erstmals durchgehende Belegung der acht neuen Suchknoten? | Beleg: par.6 -- Erzeugung 14,66 h, Tor 2a HAELT (sp_voll 0,955 gegen 0,901), Fenster 2.947 Dateien, Training `v31-b01` warm in 58 min mit 0 unerwarteten Rezept-Abweichungen. **TOR 1 TRAEGT: 461:339 aus 800 = 57,62 %, Block-z +4,24 auf differenzierten Werten, beide Seeds einzeln signifikant.** Tor 2b erstmals wieder verwendbar, 800/800 ohne Replay. Promotion am 2026-09-20 VOLLZOGEN: `v31-b01` ist Champion (Elo 1458 [1414; 1510], vier Kanten, keine frueh gestoppt). Generator der v32-Erzeugung. -->

# PREREG v31: Fensterzuschnitt der Generation v31

**Angelegt 2026-09-19** auf Nutzer-Auftrag ("registrier das fenster fuer v31"), nachdem v30 seine
Arme gemessen hat. Vorlage ist `PREREG_v30_window.md`; Bestandszahlen sind am 2026-09-19 in `data/`
gezaehlt, alles Weitere ist als Herleitung oder ANNAHME markiert.

**Was diesen Zyklus von v30 unterscheidet, in einem Satz je Punkt:**

1. **Der Generator ist ein echter Trainingsarm.** `v30-b02` hat 888 Eingaenge und 414 Aktionen von
   Haus aus -- die Polsterung, die fuer `v29-b11` noetig war, entfaellt samt ihrer Abnahme.
2. **Die acht neuen Knoten sind erstmals durchgehend belegt.** In v30 trugen rund 40,8 Prozent des
   Fensters Lernziele an ihnen (`PREREG_v30_window.md` par.1b); hier sind es die beiden juengsten
   Generationen, also **rund 81,6 Prozent** (Herleitung aus par.1, nicht am Korpus nachgezaehlt --
   die neuen Dateien gibt es noch nicht).
3. **Die Rueckgabe-Streuung wirkt zum ersten Mal.** Sie war in der v30-Erzeugung strukturell
   wirkungslos (`PREREG_dome_return_order.md` 12.12); der Einbau in den Knoten-Weg ist die
   Vorbedingung dieser Erzeugung (par.8 Punkt 1).

## par.1 ZUSCHNITT (Rotationsregel, Bestand am 2026-09-19 gezaehlt)

G = v31-Erzeugung durch `v30-b02` -- ALLE DREI Klassen sind neu, Sockel wie Schwarm (1.201 Dateien); G-1 = `v29-b11` (die v30-Erzeugung); G-2 = `v28-b02` (die
v29-Erzeugung). **`v27-b01` faellt aus der Rotation** (400/400/401 = 1.201 Dateien, Loeschung nur
mit restic-Beleg und pfadgenauer Freigabe).

| Generation | Klasse | Dateien | Partien | Policy-Ziel |
| --- | --- | --- | --- | --- |
| `v30-b02` (neu) | policy | 400 | 4.000 | **ja** |
| `v30-b02` (neu) | value-tempc | 400 | 4.000 | nein |
| `v30-b02` (neu) | value-excursion | 401 | 4.010 | nein |
| `v29-b11` (G-1) | policy, seed-gezogen | 135 | 1.350 | **ja** |
| `v29-b11` | policy, Rest | 265 | 2.650 | nein |
| `v29-b11` | value-tempc | 400 | 4.000 | nein |
| `v29-b11` | value-excursion | 401 | 4.010 | nein |
| `v28-b02` (G-2) | policy, seed-gezogen | 45 | 450 | **ja** |
| `v28-b02` | policy, Rest | 355 | 3.550 | nein |
| `v28-b02` | value-excursion, seed-gezogen | 145 | 1.450 | nein |
| **Summe** | | **2.947** | **29.460** | **580 Traeger** |

**Die Maskierung ist genau die rechte Spalte** (`engine/py/corpus_dataset.py`): Traegerstatus je
Datei Z.1608, Phase Z.1596 (nur Drafting, Tiling und Start fallen weg), Gueltigkeitsflag Z.1635.
Maskiert wird ausschliesslich das POLICY-Ziel; Value, Punkte, Ownership und root_q bleiben in jedem
Record erhalten.

**SEED: 20260949** (Vierer-Schritt aus `docs/generation_loop.md`: v29 20260941, v30 20260945).
**Val-Pool `^selfplay_v30-`** -- das Muster trifft ausschliesslich die neuen Klassen.

## par.2 TORE

Wie `PREREG_v30_window.md` par.3, mit zwei Aenderungen: **Tor 2a** misst `sp_voll` der neuen
Policy-Klasse gegen die von `v29-b11` (**0,90087**, gemessen 2026-09-18), nicht mehr gegen v28-b02.
**Tor 2b** ist wieder verwendbar: die Arena schreibt den Endstand seit 2026-09-19 ins Artefakt, das
Replay entfaellt (par.9 der v30-Prereg).

## par.3 ERZEUGUNG

Befehle wie `PREREG_v30_window.md` par.5, mit `MOSAIC_V30_GENERATOR=models/alphazero_v30-b02_brierbest.onnx`
und `MOSAIC_V30_GEN_NAME=v30-b02`, Seeds 20260934 / 20260935 / 20260936 (Fortschreibung der
30/31/32-Reihe). **NEU: `MOSAIC_RETURN_ORDER_RANDOM_P=0.81`** in allen drei Klassen
(`PREREG_dome_return_order.md` 12.12a: Ziel "15 Prozent der Partien mindestens einmal", exakt
gerechnet ueber die Verteilung der Gelegenheiten; Obergrenze 17,75 Prozent bei p = 1).
`MOSAIC_STACK_DRAW_RESEARCH=1` bleibt.

## par.4 KOSTEN (ANNAHME aus v30)

Erzeugung 3 x 4.000 Partien @100: **13,86 h gemessen in v30**, hier dieselbe Groessenordnung; der
Streu-Knopf zieht keine Zusatzsuche, nur eine Zufallszahl je Gelegenheit. Kette danach: Bloecke
(Waechter mitlaufen lassen), Monolith rund 10 min, Training rund 1 h warm bzw. 2,3 h kalt, Tor 1
zwei Seeds a rund 95 min.

## par.5 OFFENE NUTZER-ENTSCHEIDE

1. **ERLEDIGT 2026-09-19:** die Rueckgabe-Streuung war vor der Erzeugung im Wheel
   (`feedback_record_field_must_precede_generation`). Knoten-Weg in `self_play.rs` mit eigenem
   Seed-Unterscheider, Maske in `engine/py/corpus_dataset.py` als eigene Bedingung auf
   `return_order_randomized`, Wheel uebersetzt und installiert. Ein Cache-Schluessel-Zusatz war
   NICHT noetig und wurde nach einem roten Waechter-Test wieder zurueckgenommen.
2. **Arme.** v30 fuhr zwei (kalt und warm), und der Warmstart gewann mit 9,36 Prozentpunkten
   Abstand. Ob v31 wieder zwei Arme bekommt oder nur den Warmstart, ist offen.
3. **Start der Erzeugung** -- wie immer erst auf ausdrueckliche Anweisung.

## par.6 ERGEBNISSE

### Erzeugung gestartet 2026-09-19, 21:55 (zweiter Anlauf)

Kette `tools/night_v31_generate.sh`, Generator `v30-b02`, Seeds 20260934/35/36, Dosis als
**CLI-Flag** `--return-order-random-p 0.81`.

**Der erste Anlauf (20:15 bis 20:47) ist verworfen und geloescht.** Er lief 45 Dateien und 120
Partien weit **ohne eine einzige Streuung**: die Kette exportierte
`MOSAIC_RETURN_ORDER_RANDOM_P=0.81`, aber `self_play.py` Z.236-240 setzt dieselbe Variable aus
seinem eigenen CLI-Wert neu, und dessen Default ist 0.0. Eine Wheel-Abfrage in einem SEPARATEN
Prozess zeigte dabei korrekt 0.81, waehrend die Erzeugung mit 0.0 lief -- die Gegenprobe im
falschen Prozess belegt also nichts. Eintrag in `docs/pitfalls.md`.

**Gegenprobe am neuen Korpus, erste 20 Dateien:** 3 von 20 Partien mit gestreuter Rueckgabe =
**15,0 Prozent** (Ziel 15 Prozent, Obergrenze 17,75). Die Dosis 0,81 trifft damit den
registrierten Zielwert.

### Erzeugung ABGESCHLOSSEN 2026-09-20, 11:04

**400 / 400 / 401 Dateien**, Exit 0, 20:23:47 bis 11:04. Laufzeiten aus den Manifesten, nicht
geschaetzt: Sockel 16.944,3 s (4,236 s je Partie), temperiert 18.399,2 s (4,600), Ausflug
17.434,6 s (4,353); zusammen **52.778,1 s = 14,66 h**, gegen v30 (13,86 h) +5,7 Prozent.
Vollstaendig mit dem Vergleich je ZUG in `docs/measured_runtimes.md`, Abschnitt "Generation v31".

**Offen und ausdruecklich unerklaert:** die Partielaenge ist gegen v30 auf ein Zehntel Zug gleich
(197,7 gegen 197,7 im Sockel), trotzdem ist der Sockel 10,7 Prozent BILLIGER und beide
Schwarm-Klassen 13,7 bzw. 18,4 Prozent TEURER je Zug. Cache-Waechter und `policy_mass_cutoff` sind
als Ursachen geprueft und ausgeschlossen (Herleitung in `measured_runtimes.md`). Entscheiden wuerde
es die Zahl der je Entscheidung expandierten Knoten -- eine Sonde ueber die Records, keine Partie.

### Vorlauf der Kette, 2026-09-20 12:15 (tools/night_v31_chain.sh)

| Pruefung | Ergebnis |
| --- | --- |
| Manifest-Diff gegen `manifest_v29-b11-policy_20260918_145006.json` | **0 unerwartete Abweichungen**; die einzige gemeldete ist `return_order_random_p` 0,0 -> 0,81 |
| Stack-Draw-Kontrolle | `stack_draw_research` gesetzt, Slot-Datensaetze im Korpus |
| Wiedervorlage der Streuung am Korpus | **24 von 200 Partien = 12,0 %** (20 Dateien) |
| **Tor 2a** | `sp_voll` **0,955** (+-0,017) fuer `v30-b02` gegen **0,901** (+-0,017) fuer `v29-b11`, Differenz **+0,054** -- **HAELT** |

**Zur Dosis:** 12,0 Prozent gegen das Ziel 15 Prozent. Auf n = 200 Partien betraegt eine
Standardabweichung 2,5 Prozentpunkte, der Abstand also 1,2 sd -- kein auffaelliger Befund, aber die
BESSERE Schaetzung als die 15,0 Prozent aus 20 Partien vom Vorabend. Die Rate ist
verhaltensabhaengig (`PREREG_dome_return_order.md` 12.12a) und gehoert am vollen Korpus
nachgerechnet, sobald die Maschine frei ist; erst dann ist sie eine tragende Zahl.

**Die Referenzzahl aus par.2 ist am Korpus bestaetigt:** 0,90087 gegen gemessene 0,901.

### Tor 2a im Reihenverlauf

Die Reihe der Generatoren-`sp_voll` lautet damit 0,637 / 0,737 / 0,777 / 0,816 / 0,843 / 0,901 /
**0,955**, die Zuwaechse +0,100 / +0,040 / +0,039 / +0,027 / +0,058 / **+0,054**. Der Zuwachs
bleibt auf dem erhoehten Niveau der Vorgeneration. **Das ist kein Staerkebeleg** -- `sp_voll` ist
eine Korpus-Kennzahl des Generators, kein Duell.

### TOR 1: `v31-b01` gegen den Champion `v30-b02` -- TRAEGT (2026-09-20)

Beide Seiten Champion-Spec, 400 Sims, c_puct 1,5, Blockgroesse 5, Deckel 200 Paare,
alpha = beta = 0,001, 10 Threads, `--log-games`. Training 3.490,4 s = 58 min, warm von
`v30-b02_brierbest`, 5.211.996 Samples; **der automatische Manifest-Diff gegen das
v30-b02-Rezept meldet 0 unerwartete Abweichungen** -- genau `cache_file`, `file_list`, `load`,
`name`, `seed`, `val_pool`.

| Seed | Stand | Anteil | **Block-z** | McNemar | SPRT |
| --- | --- | --- | --- | --- | --- |
| 20261400 | 237:163 | 59,25 % | **+3,54** | p = 0,0004 | Deckel, LLR +6,41 |
| 20261401 | 224:176 | 56,00 % | **+2,42** | p = 0,0197 | Deckel, LLR +2,81 |
| **gepoolt** | **461:339** aus 800 | **57,62 %** | **+4,24** | | |

**Der Block-z ist auf DIFFERENZIERTEN Blockwerten gerechnet**, mit Summenprobe gegen
`a_wins_total`/`b_wins_total`: die Felder in `blocks[]` sind kumulativ, und genau daran ist die
Auswertung am 2026-09-19 schon einmal gescheitert (`docs/pitfalls.md`). 80 Bloecke zu 5 Paaren,
Mittel 0,5763, sd 0,1609. Beide Seeds liegen EINZELN ueber der Schwelle 1,96.

**Kein SPRT-Entscheid in beiden Laeufen** (LLR +6,41 und +2,81 gegen die Schranke +6,907): der
Deckel wurde erreicht, die Fixed-n-Auswertung ist nach dem Werkzeugtext ein Notbehelf. Das ist
die dritte Nachbar-Generation in Folge, in der der Frueh-Stopp nicht greift, und stuetzt den
Befund aus `PREREG_v30_window.md` par.9.

### Die sechs Standard-Kennzahlen (je Seite, n = 400 Bretter je Seed)

| Kennzahl | Seed 20261400 A / B | Seed 20261401 A / B |
| --- | --- | --- |
| 1 Reihen (lange Reihen) | 3,13 / 2,96 | 3,08 / 3,03 |
| 2 Spalten: volle Spalten | **1,0300 / 1,0000** (+-0,076) | **1,0425 / 0,9925** (+-0,077) |
| 2 Spalten: Teilspalten >= 4 | 2,43 / 2,27 | 2,37 / 2,29 |
| 3 Strafleiste | 7,13 / 7,56 | 7,36 / 7,01 |
| 5 Eigene Punkte | **60,38 / 56,52** (+-1,6) | **59,03 / 57,57** |
| 6 Margin | **+3,86** [+-1,88] | **+1,47** |

Punkte je Wertungsplatte, Seed 20261400 (Mittel ueber die Bretter mit aktivem Kriterium):
Diagonale 0,54 gegen 0,27; Eckplatten 9,33 gegen 8,58; Horizontale 0,58 gegen 0,25; Vertikale
7,41 gegen 6,45; Aeussere Felder 10,77 gegen 10,29; Spezialfelder -9,48 gegen -9,74. **Gegenlaeufig
in zwei Kriterien:** Farbenreiche Reihen 0,34 gegen 0,42 und Mehrfarbige Felder 3,80 gegen 4,40.

**Was NICHT einheitlich ist, und das gehoert dazu:** die Strafleiste dreht zwischen den Seeds
(-0,43 bzw. +0,35 zulasten des Kandidaten). Der Punktvorsprung ist dagegen in beiden Seeds
positiv und traegt das Verdikt.

### TOR 2b: erstmals seit der Reparatur wieder verwendbar

**800 von 800 Partien ausgewertet, alle direkt aus dem Record, null Divergenzen** -- die Sonde
braucht kein Replay mehr, seit die Arena den Endzustand mitschreibt (`score_geo`, `dome_grid`,
2026-09-19). Zum Vergleich: in v30 divergierten 15,5 und 17,8 Prozent, und die auswertbare
Teilmenge war nachweislich verzerrt. Volle Spalten **+0,030** und **+0,050** zugunsten des
Kandidaten; beide Differenzen liegen unter einer Standardabweichung (+-0,076), sind also je
einzeln nicht signifikant und stuetzen das Tor-1-Ergebnis nur der Richtung nach.

### Verdikt

**`v31-b01` schlaegt den amtierenden Champion `v30-b02`**, 461:339 aus 800 Partien, Block-z
+4,24, in beiden Seeds einzeln signifikant, mit hoeherem Punktestand und mehr vollen Spalten.
Damit ist Tor 1 genommen. **Die Promotion selbst ist ein eigener Ablauf**
(`/mosaic-champion-promotion`: Anker-Kante, Champion-2-Kante, Pflicht-Diagnostiken, Artefakt) und
ein Nutzer-Entscheid -- zumal dieser Champion nach par.5a von `PREREG_code_cleanup_closeout.md`
der Schluss-Champion waere und damit den Anzeigenamen **Tessa** bekaeme.
