<!-- STATUS: OFFEN | Frage: Wie wird das v31-Fenster zugeschnitten -- Generator `v30-b02` (888/414, ohne Polsterung), und traegt die erstmals durchgehende Belegung der acht neuen Suchknoten? | Beleg: par.6 Erzeugung FERTIG 2026-09-20 (400/400/401 Dateien, 14,66 h, +5,7 Prozent gegen v30), Manifest-Diff 0 unerwartete Abweichungen, **Tor 2a HAELT** mit sp_voll 0,955 gegen 0,901. Streuung im Korpus 12,0 Prozent auf n = 200 (Ziel 15, nicht auffaellig). Fenster 2.947 Dateien, Training `v31-b01` WARM und Tor 1 gegen Champion `v30-b02` laufen. -->

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

(Training `v31-b01` und Tor 1 gegen den Champion laufen; Verdikt steht aus.)
