<!-- STATUS: OFFEN | Frage: Traegt das v30-Fenster (Generator `v29-b11`, 888/414) einen KALT gestarteten Arm `v30-b01` mindestens auf Champion-Niveau `v29-b09`? | Beleg: Erzeugung laeuft; Klasse 1 (policy) fertig 2026-09-18 20:07, 400 Dateien, 4,746 s je Partie (+20,4 Prozent gegen die v29-Linie, par.9). Tor 0 und **Tor 2a GRUEN**: `sp_voll` 0,90087 gegen 0,84275, n = 8.000 Seiten je Klasse. Wiedervorlage erster Record, Manifest-Diff und Stack-Draw-Kontrolle ebenfalls gruen (par.9). Klassen 2/3, Training und Tor 1 stehen aus. -->

# PREREG v30: Fensterzuschnitt der Generation v30 (v31 offen, Nutzer 2026-09-17)

**Angelegt 2026-09-18** auf Nutzer-Auftrag, waehrend die Abnahme-Kette `tools/night_v30_acceptance_b11.sh`
(Polsterung b09 -> b11, A/B, Record-Stichprobe) auf der Maschine laeuft. **Vorlage ist
`PREREG_v29_window.md`** (Zuschnitt par.1, Erzeugungsbefehle par.5, Arme und Tore par.6,
Netz-Gesundheit par.6d). Bestandszahlen sind am 2026-09-18 in `data/` gezaehlt; alles Weitere ist
als Herleitung oder als ANNAHME markiert.

**Was v30 ist (`project_v30_release_close`, STATUS Abschnitt 6 Punkt 18/20/21):** die
Generation v30 (v31 offen, Nutzer 2026-09-17). v29 hat das Begleitprogramm getragen, v30 bekommt nur noch Rezept-Knoepfe,
keine neuen Bauvorhaben. Nach der v30-Promotion folgen Leiter-Endfassung, Schlussmodell "Tessa",
Code-Abschluss und STATUS-Neufassung.

**Drei Dinge unterscheiden diesen Zyklus von jedem vorherigen** und gehoeren deshalb in Zeile 1
der Lesart:

1. **Der Generator ist kein Trainingsarm.** `v29-b11` ist der Champion `v29-b09` mit auf 414
   gepolstertem Policy-Kopf und auf 888 gepolstertem Flach-Eingang, ohne einen Trainingsschritt
   (`docs/generation_naming.md`, Reservierung 2026-09-18; `PREREG_minimal_strength_core.md` 10.15).
   Die Polsterung ist der einzige Weg, mit dem die neuen Suchknoten (Mond, Rueckgabe, Slot,
   Rotation) ueberhaupt in den v30-Korpus kommen: das Tor liest die Policy-Breite aus dem ONNX,
   ein 406er-Netz spielt die Knoten nie (STATUS Punkt 23).
2. **Das Training startet KALT.** Kein `--load` (STATUS Abschnitt 4, Punkt 20;
   `PREREG_round_transition_search_sampling.md` 18.11). Damit lernen die 90 Projektions-Spalten
   (Abschnitt 17), die 39 Sicht-Spalten (Abschnitt 16) und die 4 Design-Spalten (Abschnitt 18)
   von Anfang an, statt als Null-Polster hinter einem eingespielten Netz zu haengen.
3. **Der Aktionsraum ist gewachsen**, NUM_ACTIONS 406 -> 414 (`config.py` Z.57, geprueft
   2026-09-18): 406-410 `choose_moon_top` je Farbe (`features.rs:2164`), 411-413
   `ChooseReturnFirst` (`features.rs:2169`, `RETURN_ORDER_MAX_PERMUTED = 3`,
   `self_play.rs:647`). Diese acht Knoten tragen im v30-Korpus zum ERSTEN MAL eine
   Besuchsverteilung als Lernziel.

## par.1 ZUSCHNITT (Rotationsregel angewandt; Bestandszahlen geprueft 2026-09-18)

Regel: Zwei-Klassen-Fenster aus Sockel (Policy-Klasse, Traeger) und Schwarm (Value-Klassen),
drei Generationen tief, die vierte rotiert heraus (`project_replay_window_strategy`,
`docs/window_generation.svg` "Rotation (seit v22 selbstaehnlich)", umgesetzt in
`PREREG_v29_window.md` par.1). Dateien heissen nach dem GENERATOR
(`feedback_selfplay_naming_convention`).

G = v30-Erzeugung durch `v29-b11` (par.5), Dateien `selfplay_v29-b11-*`; G-1 = `v28-b02`
(400 / 400 / 401 Dateien, gezaehlt); G-2 = `v27-b01` (400 / 400 / 401, gezaehlt).
**`v26-b01` faellt aus der Rotation** (seine 400 / 400 / 401 Dateien liegen noch im Baum und
werden nicht mehr gelesen; Loeschung erst im Generationswechsel und nur mit pfadgenauer
Freigabe).

Zaehlung am 2026-09-18 (`ls data | grep -c`, Einheit Dateien; ausser diesen neun Klassen liegt
KEINE weitere `selfplay_*`-Klasse in `data/`):

| Klasse | Policy | value-tempc | value-excursion |
| --- | --- | --- | --- |
| `v28-b02` (G-1) | 400 | 400 | 401 |
| `v27-b01` (G-2) | 400 | 400 | 401 |
| `v26-b01` (rotiert heraus) | 400 | 400 | 401 |
| `v29-b11` (neu, noch nicht erzeugt) | 0 | 0 | 0 |

**Sockel (Policy-Klasse, Traeger)**

| Posten | Quelle | Dateien | Partien |
| --- | --- | --- | --- |
| Sockel NEU | v30-Erzeugung, policy-aktiv | 400 (erwartet) | 4.000 |
| aus G-1 | 135 der 400 `selfplay_v28-b02-policy_*` (seed-bestimmt) | 135 | 1.350 |
| aus G-2 | 45 der 400 `selfplay_v27-b01-policy_*` (seed-bestimmt) | 45 | 450 |
| **Summe** | | **580** | **5.800** |

**Schwarm (Value-Klassen, policy-maskiert)**

| Posten | Quelle | Dateien | Partien |
| --- | --- | --- | --- |
| Schwarm NEU | v30, temperiert plus Ausfluege | rund 801 (erwartet) | rund 8.000 |
| Schwarm G-1, Haelfte a | alle 400 `selfplay_v28-b02-value-tempc_*` | 400 | 4.000 |
| Schwarm G-1, Haelfte b | alle 401 `selfplay_v28-b02-value-excursion_*` | 401 | 4.010 |
| Sockel-Rest G-1 | die 265 uebrigen `selfplay_v28-b02-policy_*` | 265 | 2.650 |
| Sockel-Rest G-2 | 355 der `selfplay_v27-b01-policy_*` | 355 | 3.550 |
| Schwarm G-2 | 145 der `selfplay_v27-b01-value-excursion_*` (par.1a) | 145 | 1.450 |
| **Summe** | | **rund 2.367** | **rund 23.660** |

**Fenster gesamt rund 2.947 Dateien**, wie v27, v28 und v29. Die Ausflug-Klassen liefern 400 oder
401 Dateien; nicht ausgeglichen. Die Zahl der neuen Dateien ist eine ERWARTUNG (die Erzeugung
laeuft noch nicht); die Kette prueft sie mit denselben Zusicherungen wie `night_v29_chain.sh`
Schritt 4.

**SEED der seedbestimmten Auswahlen UND des Trainings: 20260945.** Hergeleitet aus der Regel in
`docs/generation_loop.md` ("je Generation ein NEUER Seed ... weiter im Vierer-Schritt, aber
innerhalb einer Generation teilen ALLE Arme denselben Seed"): v25 20260925, v26 20260929, v27
20260933, v28 20260937, v29 20260941 (`PREREG_v29_window.md` par.1) -> v30 20260945.

**Val-Pool `^selfplay_v29-`** (die neue Generation stellt den Validierungsanteil; dieselbe Form
wie v29 mit `^selfplay_v28-`). Das Muster trifft ausschliesslich die neuen Klassen
`selfplay_v29-b11-*`; G-1 und G-2 heissen `selfplay_v28-b02-*` und `selfplay_v27-b01-*`.

### par.1a G-2-Haelfte: die AUSFLUG-Haelfte, wie in v28 und v29

Der G-2-Posten traegt EINE Schwarm-Haelfte. v28 und v29 nahmen beide die Ausflug-Haelfte
(Nutzer-Entscheid 2026-09-13, `PREREG_v29_window.md` par.2: *"Nimm fuer die g-2 das selbe was wir
auch bei v28 hatten. Da brauchen wir nichts aendern."*). v30 fuehrt dieselbe Regel eine Generation
weiter: `G2_SWARM_PATTERN="selfplay_v27-b01-value-excursion_*.pkl"`, 145 Dateien seed-gezogen mit
20260945. Die 401 Quelldateien liegen vollstaendig im Baum (gezaehlt 2026-09-18). Die temperierte
v27-Haelfte rotiert ersatzlos hinaus. **Kein neuer Nutzer-Entscheid noetig**, solange der Nutzer
nichts anderes sagt (par.8 Punkt 1).

### par.1b VERDUENNUNG, vorab beziffert -- was das Fenster ueber die neuen Merkmale sagen KANN

Die v29-Lehre (`PREREG_v29_window.md` par.9, Nutzer 2026-09-14: *"nicht alles vom material ist
tragend fuer die neuen input features"*) gilt hier genauso und wird vorab hingeschrieben, damit
sie nicht nachtraeglich als Ausrede dient. Anteile am Fenster (Herleitung aus par.1, n = rund
2.947 Dateien, Grundmenge `data/window_v30.txt`, Einheit Dateien):

| Generator | Anteil am Fenster | traegt `designs` (P.12) / `designs_ordered` (P.16) | traegt die Knoten 406-413 |
| --- | --- | --- | --- |
| `v29-b11` (neu) | rund 1.201 = **40,8 %** | ja | ja |
| `v28-b02` (G-1) | 1.201 = 40,8 % | nein | nein |
| `v27-b01` (G-2) | 545 = 18,5 % | nein | nein |

**P.12 wird mit v30 zum ersten Mal lebendig.** `PREREG_stack_top_feature.md` par.17
(Nutzer-Entscheid 2026-09-13: *"dann also erst fuer v30. so be it"*): in v29-b03 waren die 18
P.12-Spalten konstant 0, weil der v29-Korpus das Record-Feld `designs` nicht traegt; sie werden
lebendig, sobald ein Korpus mit dem Wheel von Abschnitt 16 erzeugt wird. Das ist genau diese
Erzeugung -- und es ist die letzte, also die einzige Gelegenheit.

**Nur rund 40,8 Prozent des Fensters tragen ueberhaupt Records mit dem geordneten Design-Block
und mit Policy-Zielen an den acht neuen Knoten.** Fuer die Spalten von Abschnitt 18 und fuer den
Policy-Kopf an 406-413 ist das die Grundmenge; die anderen 59,2 Prozent liefern dort Nullen
beziehungsweise kein Ziel. Abschnitt 16 (39 Sicht-Werte) und Abschnitt 17 (90
Projektions-Spalten) rechnen dagegen aus Feldern, die alle drei Generationen tragen
(`PREREG_v29_window.md` par.9: P.3/P.7/P.9/P.11/P.13/P.15 aus Altfeldern; Abschnitt 17 ist eine
Projektion des Tiling-Loesers, kein Record-Feld) -- ANNAHME, am Fenster nicht nachgezaehlt, weil
die neuen Dateien noch nicht existieren; Nachzaehlung gehoert in par.9.

**Folge fuer das Verdikt:** wer v30-b01 gegen den Champion misst, misst die Kaltstart-Wette auf
dem ganzen Eingang, nicht "die neuen Knoten". Die Knoten sind mit 40,8 Prozent Abdeckung in
EINEM Zyklus vorregistriert als unterbelegt; ihre Wirkung ist erst in v31 sauber messbar
(`PREREG_moon_stack_order.md` 12.6, `PREREG_dome_return_order.md` 12.7: "die Wirkung ist erst im
v31-Training messbar"). Ein Nullbefund an dieser Stelle ist KEIN Beleg gegen die Knoten.

## par.2 HYPOTHESEN UND FALSIFIKATOREN (vor jeder Messung)

**H1 -- Kaltstart erreicht mindestens b09-Niveau.** `v30-b01` (kalt, 888, v30-Rezept, v30-Fenster)
haelt im Gating gegen den Champion `v29-b09` mindestens ein Unentschieden und reisst die
5-Prozentpunkte-Marge nicht nach unten.
*Falsifikator:* zwei Seeds a 200 Paare, beide unter 47,5 Prozent auf Block-Ebene -> H1 gefallen,
Rueckfall 1 (Afterburner, par.3 Punkt 5). Praezedenz fuer einen gescheiterten Kaltstart: v14
(Kaltstart-Destillation verlor den Value-Kopf, `project_v14_rebuild`); Praezedenz fuer einen
gelungenen: v23-b06 (`project_prereg_audit_2026-09-01`).

**H2 -- die 90 + 39 + 4 neuen Spalten leben.** Die Spaltennormen von `flat_branch.0.weight` sind
fuer die Projektion (Abschnitt 17), den Sicht-Anbau (Abschnitt 16) und den Design-Block
(Abschnitt 18) nach dem Kaltstart nicht bei 0 und nicht ein Vielfaches der Altspalten.
*Bezugswerte, gemessen am WARMSTART-Arm b07* (`PREREG_round_transition_search_sampling.md` 18.12):
Projektion mittel 0,668 (min 0,290, max 1,035, keine Spalte bei 0), Sicht-Anbau 0,284 (21 von 39
bei 0), Altbestand 3,02.
*Erwartung, ausdruecklich als solche markiert:* im Kaltstart gibt es keine "Altspalten" mit
Vorsprung, die Normen sollten also naeher beieinander liegen als bei b07 -- genau das ist die
Wette aus 18.11. *Falsifikator:* eine der drei Gruppen nahe 0 (dann traegt der Eingang per
Konstruktion nichts) oder mehr als das Doppelte der Basis-Spalten (dann dominiert er).

**H3 -- die neuen Knoten stehen mit `policy` im Korpus.** Im ersten Record der Policy-Klasse
stehen `designs` (P.12), `designs_ordered` (P.16) und Aktions-IDs >= 406 mit `policy`-Eintraegen
(Besuchsverteilung), nicht nur als gespielte Aktion.
*Falsifikator:* fehlt eines davon, STOPP der Erzeugung (par.3 Punkt 2). Das ist die
Wiedervorlage aus `feedback_record_field_must_precede_generation`: faellt sie durch, faellt das
Merkmal eine Generation zurueck -- und v30 ist die letzte.

**H4 -- Tor 2a haelt.** `v29-b11` als Generator liefert mindestens 0,843 volle Spalten je Seite
(Bezug `v28-b02`, `evaluations/artifacts/corpus_sanity_v28-b02-policy.json`, `sp_voll` 0,84275
+-0,0167, n = 8.000 Seiten aus 4.000 Partien; am Artefakt geprueft 2026-09-18).
*Falsifikator:* darunter -> Tor 2a gerissen, Nutzer-Vorlage nach `docs/generation_loop.md`
("keine stille Promotion"). Vorbehalt vorab: b11 ist b09, also ein ANDERES Netz als b02 -- die
Reihe wechselt die Linie nicht, aber sie wechselt den Arm; beide Seiten messen bei 100 Sims,
damit ist die Betriebsart gleich (`PREREG_v29_window.md` par.4 Punkt 5 und der Hinweis in
`night_v29_chain.sh` Schritt 1).

## par.3 TORE UND PFLICHTPRUEFUNGEN

**1. Tor 0 / Tor 2a -- Korpus-Sanity je Klasse.** `tools/corpus_sanity_check.py` ueber alle vier
Klassen (`v28-b02-policy` als Bezug plus die drei neuen), Artefakte
`evaluations/artifacts/corpus_sanity_<klasse>.json`. Tor 2a ex post: `sp_voll` der
Policy-Klasse gegen 0,84275 (H4). **Betriebsart mitpruefen** (Hinweis aus `night_v29_chain.sh`
Schritt 1): beide Seiten sind bei 100 Sims erzeugt, der Vergleich ist damit in derselben
Betriebsart; bei 400 Sims waere ein niedrigerer Wert der Suchtiefen-Effekt und allein kein
gerissenes Tor (`PREREG_search_depth_column_optimum.md` par.8e: am Champion faellt die Kurve
ueber 100/200/400/600 monoton 1,0975 / 0,9575 / 0,8950 / 0,8200).
Berichtet werden je Klasse die sechs Standard-Kennzahlen (CLAUDE.md): Reihenauslastung,
Spaltenauslastung (volle Spalten, hoechste Spalte, Teilspalten >= 3 / >= 4), Strafleiste,
Plattenpunkte je Kriterium, eigene Punkte, Margin. Der Margin ist im Self-Play per Konstruktion
0.

**2. Wiedervorlage am ERSTEN Record** (H3, `feedback_record_field_must_precede_generation`):
`designs`, `designs_ordered`, Aktions-IDs 406-413 mit `policy`-Eintraegen. `designs_ordered`
prueft `tools/night_v30_generate.sh` selbst 10 Minuten nach dem Start und BRICHT AB, wenn es
fehlt; `designs` und die Knoten prueft der Koordinator mit dem Werkzeug des Baus
(Record-Stichprobe aus `tools/night_v30_acceptance_b11.sh` Stufe 7). Reisst eines: STOPP,
Nutzer-Entscheid.

**3. Manifest-Diff gegen die Referenz.** Das Manifest der ersten Klasse gegen
`data/manifest_v28-b02-policy_20260913_120816.json` diffen (`cli_args`, `sims`, Knoepfe, Spec,
`engine_config`). **Erwartete und einzige zulaessige Unterschiede**: Modell, Namensstamm,
Version, Seed, Datum, `spec` (`models/v30_generation.spec.json` statt
`models/start_by_search_on.spec.json`, Unterschied genau `return_order_mode: 1`), `input_size`
884/755 -> 888, `num_actions` 406 -> 414, Vertragshash -> `6ef829e564c58bd5`. **Jede weitere
Abweichung ist ein Stopp** (`feedback_run_manifest_gegen_referenz`: ein fehlendes Flag ist ein
stiller Default).

**4. Stack-Draw-Kontrolle.** `MOSAIC_STACK_DRAW_RESEARCH=1` muss in der Umgebung BEIDER Laeufe
stehen (`PREREG_v29_window.md` par.5, Nutzer-Entscheid 2026-09-13: ohne ihn traegt der Korpus
NULL Datensaetze fuer `choose_draw_stack_slot`, an der v28-Erzeugung nachgezaehlt 0 von 13.145
Records gegen 4,06 Prozent im Kontrollkorpus). `tools/night_v30_generate.sh` exportiert ihn; die
Kontrolle ist der Manifest-Eintrag `stack_draw_research` im `engine_config_json` der ersten
Klasse. **Befund, der dazugehoert** (`PREREG_dome_return_order.md` 12.9): unter dem Research-Knopf
ist `return_order_mode 1` WIRKUNGSLOS, weil der Sammelaufloeser nie laeuft -- die Abdeckung der
Rueckgabe-Reihenfolge kommt in der Erzeugung vom Suchknoten, nicht von der Spec. Das Feld bleibt
in der Spec als Rueckfall fuer 406er-Seiten in Arenen.

**5. Tor 1 -- gepaartes Gating `v30-b01` gegen den Champion `v29-b09`.**
`tools/paired_gating.py`, Modell A `models/alphazero_v30-b01_brierbest.onnx`, Modell B
`models/alphazero_v29-b09_brierbest.onnx`, **beide Seiten Champion-Spec**, 400 Sims,
`--block-size 5`, `--log-games`, **zwei Seeds 20261300 und 20261301 a 200 Paare**, kein
Frueh-Stopp unter 150 Paaren (Champion-Strenge, `docs/generation_loop.md`: ein SPRT-Fruehstopp
unter 150 Paaren ist informativ und kein Tor-Ergebnis).
*Champion-Spec:* `models/frozen_champions/v29-b09/spec.json`, sobald der Generationswechsel sie
angelegt hat; bis dahin `models/frozen_champions/v28-b02/spec.json` (inhaltlich seit v25 die
v24-b07-Spec, `PREREG_v28_window.md` par.3). Die Kette prueft zur Laufzeit, welche vorliegt.
*Marge und Lesart:* Entscheidungsmass ist die Siegdifferenz je Block (`PREREG_v29_window.md`
par.6, 18.12-Form: 80 Bloecke a 10 Partien, z-Wert). Traegt b01 (z >= +1,96 oder gepoolt >= 52,5
Prozent ohne Gegenbefund), ist v30-b01 der Champion-Kandidat und geht in die
Promotions-Checkliste. Bleibt es flach (beide Seeds H0), gilt die Kaltstart-Wette als NICHT
eingeloest, aber nicht als widerlegt -- dann **Rueckfall 1: Afterburner auf dem kalt gestarteten
v30-Netz** (Warmstart vom v30-Checkpoint, DAgger-Muster v22-b05/b06: 600 Zusatzpartien, 6-12
Epochen, 8-11 min, `docs/measured_runtimes.md` Z.52-53). Haelt auch der Afterburner nicht:
**Rueckfall 2, Warmstart von `v29-b09`** auf dem v30-Fenster (STATUS Punkt 20;
`round_transition_search_sampling` 18.11). Geprueft, dass Rueckfall 2 technisch geht: `train.py`
polstert beim Warmstart sowohl `flat_branch.0.weight` (Z.1691-1698, neue Spalten
null-initialisiert) als auch `policy_head.2.weight`/`policy_head.0.weight` (Z.1713-1718, neue
Zeilen null) -- b09 mit 884/406 laedt also in ein 888/414-Netz.

**6. Tor 2b und Plattenpunkte** aus denselben Logs: `tools/probes/arena_column_probe.py`
(volle Spalten je Seite, beide Modelle) und `tools/plate_points_from_arena.py --block 5`
(Punkte je Kriterium). Tor 2b ist als NICHT-FALLEN formuliert (`docs/generation_loop.md`).

**7. Netz-Gesundheit** (H2, Pflichtteil nach `PREREG_v29_window.md` par.6d): (a) Spaltennormen
von `flat_branch.0.weight` je Block (Basis / Abschnitt 16 / Abschnitt 17 / Abschnitt 18) gegen
die b07-Bezugswerte; (b) tote ReLU-Einheiten mit `tools/probes/dead_unit_probe.py --reference`
gegen `v29-b09`, Schwelle "mehr als das Doppelte des Referenz-Anteils ist ROT"; (c) Koepfe
einzeln mit `tools/offline_diagnosis.py` und `tools/oracle_metrics.py` auf demselben Val-Split
(Aufloesungsgrenze `value_r2` rund 0,015); (d) `tools/platt_fit.py` -- Brier darf nicht ueber den
Referenzwert steigen (Praezedenz v14: der Kopf starb, die Arena sah es spaet). **Beim Kaltstart
ist (b) bis (d) besonders wichtig**, weil kein Warmstart die Koepfe stuetzt.

**8. Vor dem Start der Erzeugung** (uebernommen aus `PREREG_v29_window.md` par.4, hier nur, was
noch offen ist): Maschine frei und Prozessliste leer; Wheel mit `input_size` 888 /
`num_actions` 414 / Vertragshash `6ef829e564c58bd5` installiert (Tore 1-4 gruen, Kostentor
gerissen und auf Nutzer-Entscheid hingenommen, `PREREG_minimal_strength_core.md` 10.14/10.15);
A/B `v29-b11` gegen `v29-b09` und Record-Stichprobe durch (`tools/night_v30_acceptance_b11.sh`);
`/mosaic-generation-turnover` gelaufen (Einfrieren `frozen_champions/v29-b09`, restic-Snapshot
mit Beleg, STATUS-Neufassung); **kein Eingriff in importierte Dateien waehrend Waechter oder
Kette** (`config.py`, `engine/py/neural_net.py`, `corpus_dataset.py`, `file_cache_key.py` --
Vorfall 2026-09-11, `feedback_watcher_workers_reimport_config`).

## par.4 ARME

| Arm | Was | Faktor gegen | Seed |
| --- | --- | --- | --- |
| **`v30-b01`** (Pflicht, einziger) | v30-Rezept KALT: b03-Rezept mit `--moon-loss-weight 0`, `--ownership-weight 0`, OHNE `--endgame-head`, `--opp-points-head` bleibt, INPUT_SIZE 888, NUM_ACTIONS 414, KEIN `--load` (par.6) | Champion `v29-b09`: Material des neuen Generators plus Kaltstart plus die acht neuen Knoten -- **nicht einfaktoriell**, und das steht hier VOR der Messung | 20260945 |

**KEINE weiteren Arme ohne eigenen Nutzer-Entscheid.** Das ist die v30+-Regel
(`project_material_only_freeze_v25_v27` in der Fassung fuer die Generation v30 (v31 offen, Nutzer 2026-09-17), STATUS
Abschnitt 6 Punkt 18/20: *"v30 selbst bekommt nur noch Rezept-Knoepfe, keine neuen
Bauvorhaben"*). Ein zweiter Arm braucht eine eigene Registrierung in dieser Datei und einen
Namenseintrag in `docs/generation_naming.md`.

**Warum der Arm nicht einfaktoriell ist und warum das hier akzeptiert wird:** gegen den Champion
b09 aendern sich gleichzeitig (a) das Material (v30-Fenster statt v29-Fenster), (b) der Start
(kalt statt warm), (c) der Eingang (888 statt 884) und (d) der Aktionsraum (414 statt 406). Die
v29-Lehre war, dass so ein Buendel nicht zerlegbar ist (`PREREG_v29_window.md` par.9: *"welcher
der drei Unterschiede den H0 traegt, ist mit diesen Daten nicht trennbar"*). Der Unterschied: v30
buendelt Kaltstart, 888 Eingaenge und 414 Aktionen in EINEM Arm; eine Zerlegung koennte v31 nachholen (v31
ist offen, Nutzer 2026-09-17), sicherer ist sie als eigener Arm jetzt (par.8 Punkt 2).

## par.5 ERZEUGUNG

**Wortgleich die Befehle aus `tools/night_v30_generate.sh`** (dort gebaut 2026-09-17, 22:15;
Muster `PREREG_v29_window.md` par.5). Generator und Namensstamm kommen ueber die Umgebung, Spec
ist `models/v30_generation.spec.json` (= `start_by_search_on.spec.json` plus
`return_order_mode: 1`, am Dateiinhalt geprueft 2026-09-18).

```
MOSAIC_V30_GENERATOR=models/alphazero_v29-b11.onnx MOSAIC_V30_GEN_NAME=v29-b11 \
  bash tools/night_v30_generate.sh
```

Die Kette exportiert `MOSAIC_STACK_DRAW_RESEARCH=1` (par.3 Punkt 4), prueft `input_size` 888 und
`return_order_mode` im Manifest-Export, wartet auf eine freie Maschine und faehrt dann:

```
# 1) Sockel (Traeger), 4.000 Partien -- policy-aktiv
python -X utf8 -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --version "${GEN}-policy" \
  --threads 11 --chunk 10 --per-file 10 --seed 20260930 \
  --tau-argmax-from-move 1 --deviate-prob 1.0 --start-slot-random-p 0.15

# 2) Schwarm a, 4.000 Partien -- value-only, temperiert
python -X utf8 -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --value-only --version "${GEN}-value-tempc" \
  --threads 11 --chunk 10 --per-file 10 --seed 20260931 \
  --action-temp 2 --deviate-prob 1.0 --start-slot-random-p 0.15

# 3) Schwarm b, 4.000 Identitaeten -- value-only, Ausflug
python -X utf8 -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --value-only --version "${GEN}-value-excursion" \
  --threads 11 --chunk 10 --per-file 10 --seed 20260932 \
  --excursion-prob 1.0 --tau-argmax-from-move 1 --no-root-noise --start-slot-random-p 0.15
```

Seeds 20260930 / 20260931 / 20260932 (v29 nahm 20-22). `--start-slot-random-p 0.15` ist seit der
v29-Erzeugung im Rezept (`PREREG_v29_window.md` par.6b, Nutzer-Dosis).

**Daneben gehoert der Cache-Waechter** unter der Trainings-Umgebung (Kopf von
`night_v30_generate.sh`), damit die Bloecke nicht erst nach der Erzeugung entstehen:

```
MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_FEATURES_FROM_RUST=1 python -X utf8 -u \
  tools/build_cache_incremental.py --data-dir data --encoder 2d --value-target-variant nortv \
  --workers 3 --watch --wartezeit 60 --leerlauf-abbruch 100000
```

**Alle Bloecke unter 888 sind NEU zu bauen** -- der Eingang ist von 884 auf 888 gewachsen und die
Formel-Version steht seit dem 2026-09-17 im Cache-Schluessel (`config.py` Z.89
`FEATURE_FORMULA_VERSION = "a2phantom-20260912"`, `PREREG_rust_data_layer.md` par.9b). Alte
Bloecke und Monolithen sind damit ohnehin entwertet.

**Fenster-Pinning** (`feedback_window_pinning_during_generation`): bevor die Fensterliste gebaut
wird, kommen die Messdateien auf die Ausschlussliste. Heute (2026-09-18, gezaehlt) liegt keine
davon in `data/`; die Record-Stichprobe der Abnahme-Kette erzeugt
`data/selfplay_v29-b11-probe_*.pkl` (`night_v30_acceptance_b11.sh` Z.39/355), und
Suchtiefen-Sonden erzeugen `selfplay_depth*`. Beide gehoeren in `MOSAIC_DATA_EXCLUDE`:

```
export MOSAIC_DATA_EXCLUDE='selfplay_v29-b11-probe_,selfplay_depth,selfplay_s4states,selfplay_tor2a'
```

Die Kette `tools/night_v30_chain.sh` arbeitet zusaetzlich durchgaengig mit EXPLIZITEN Dateilisten
(`--file-list`), sodass Streudateien auch ohne Pinning nicht still mitlaufen koennen; das Pinning
ist der Guertel zum Hosentraeger.

## par.6 REZEPT UND KETTE

**Kette: `tools/night_v30_chain.sh`** (gebaut 2026-09-18, `bash -n` gruen, NICHT gestartet).
Schritte: warten auf die fertige Erzeugung -> Cache-Waechter beenden -> Tor 0 / Tor 2a je Klasse
-> Traeger-Manifest `policy_carrier_manifest_v30.json` -> G-2-Auswahl -> Fensterliste
`data/window_v30.txt` -> Bloecke -> Split und Fenster-Schluessel -> Monolith mit Stempel-Pruefung
-> Training `v30-b01` KALT -> Manifest-Diff-Hinweis -> Tor 1 (zwei Seeds) -> Spaltensonde ->
Plattenpunkte.

**Der Trainingsbefehl**, abgeleitet aus `models/manifest_train_v29-b09_20260917_200920.json`
(`cli_args`, am Artefakt gelesen 2026-09-18) durch genau vier Aenderungen: `--load` gestrichen,
`--name v30-b01`, Fensterliste und Cache-Datei auf v30, Seed 20260945. Alles andere ist
byte-fuer-byte das b09-Rezept, und b09 ist das v30-Rezept auf dem v29-Fenster
(`PREREG_minimal_strength_core.md` par.10.7):

```
python -X utf8 -u train.py --name v30-b01 \
  --file-list data/window_v30.txt --cache-file "data/.cache_${KEY}.h5" \
  --epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12 \
  --val-frac 0.05 --encoder 2d --value-head wdl --value-target-variant nortv \
  --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 0.0 \
  --moon-loss-weight 0.0 --opp-points-head \
  --destretch-a 0.0051 --destretch-b 1.9269 \
  --select-by-brier --fast-loader --seed 20260945
```

Dazu die Punkte, an denen dieses Rezept schon einmal Geld gekostet hat:

* **KEIN `--load`.** Das ist der Kaltstart-Entscheid (STATUS Abschnitt 4 / Punkt 20). Wer ihn
  versehentlich setzt, misst eine andere Wette.
* **`--lr-t-max 12` steht ausdruecklich da.** Ohne das Flag haengt `T_max` an `--epochs`
  (`feedback_cosine_tmax_is_epochs_flag`); b09 hatte `lr_t_max: 12` im Manifest, der Wert ist
  also uebernommen, nicht geraten.
* **`--moon-loss-weight 0.0` ist explizit**, obwohl b09 im Manifest ebenfalls `0.0` traegt: der
  Nutzer-Entscheid (STATUS Punkt 12, `moon_stack_order` 12.9) soll im Befehl sichtbar sein und
  nicht von einem Default abhaengen.
* **`--ownership-head-2d` bleibt bei Gewicht 0.** Die AUSGABE bleibt, nur der Loss ist 0
  (`project_ownership_head_closed`, STATUS Abschnitt 4). Der Kopf wegzulassen waere ein anderer
  Arm (das war b06, und der war unterlegen, `minimal_strength_core` 10.3).
* **`--endgame-head` fehlt bewusst** (STATUS Punkt 13a, `minimal_strength_core` 10.6).
* **Diese vier Flags gibt es in `train.py` NICHT** und sie kommen aus der Umgebung:
  `--val-pool`, `--ignore-policy-target-valid`, `--head-warmstart`, `--bootstrap-coherence`
  (Kommentar in `night_v29_chain.sh` Schritt 7). Early-Stop, Epoch-Checkpoint und Snapshot sind
  per Default an. **Abbruch? Derselbe Aufruf plus `--resume`** (Fingerabdruck-Waechter).

**Umgebung der ganzen Kette** (jede einzelne Zeile hat einen Vorfall hinter sich):

| Variable | Wert | Warum |
| --- | --- | --- |
| `MOSAIC_FEATURES_FROM_RUST` | `1` | derselbe Merkmalsbauer in JEDER Kette, `PREREG_rust_data_layer.md` par.9a/9b |
| `MOSAIC_IGNORE_POLICY_TARGET_VALID` | `1` | wie v29; die gestreuten Startsetzungen tragen `policy_target_valid = false` |
| `MOSAIC_VAL_POOL` | `^selfplay_v29-` | par.1 |
| `MOSAIC_CARRIER_MANIFEST` | `policy_carrier_manifest_v30.json` | Traeger-Status ist NICHT Default, `feedback_check_policy_carrier_status` |
| `MOSAIC_DATA_EXCLUDE` | Messdateien, par.5 | `feedback_window_pinning_during_generation` |

**Val-Cache**: `window_train_split.py` liefert den Fenster-Schluessel des TRAININGSANTEILS; der
Monolith entsteht unter `data/.cache_${KEY}.h5` und wird mit
`h5py ... attrs['mosaic_cache_key']` gegen `${KEY}` geprueft (Stempel-Pruefung wie
`tools/night_v29_b08_head_pair.sh` Schritt 2, Exit 16). **Der Fenster-Schluessel deckt Monolith
UND Val-Cache** (`feedback_feature_knob_belongs_in_both_cache_keys`): b03 hat einmal mit
Kanaelen trainiert und ohne validiert, weil nur einer der beiden Schluessel den Knopf trug.

**Pflichtpruefungen der Kette, in Stichworten** (Langfassung par.3): Manifest-Diff gegen
`data/manifest_v28-b02-policy_20260913_120816.json`; Stack-Draw-Kontrolle am
`engine_config_json` der ersten Klasse; Tor 0 / Tor 2a gegen 0,84275; Wiedervorlage erster
Record (`designs`, `designs_ordered`, IDs 406-413 mit `policy`); Tor 1 zwei Seeds a 200 Paare
gegen `v29-b09`; Netz-Gesundheit; sechs Standard-Kennzahlen.

## par.7 KOSTEN (Planungsgroessen; gemessene Zeilen benannt, Rest als ANNAHME markiert)

| Posten | Zeit | Quelle |
| --- | --- | --- |
| Erzeugung 3 x 4.000 Partien @100 | **9,92 h** (v28), **12,8 h** (v29, unter Nebenlast) | `docs/measured_runtimes.md`; `PREREG_v29_window.md` par.9 |
| dito, Aufschlag 888-Encoder | +5 Prozent | **ANNAHME**, Kopf von `night_v30_generate.sh` |
| dito, Aufschlag neue Suchknoten in der ERZEUGUNG | Mond- und Rueckgabeknoten neu; Slot und Rotation liefen schon in v29 einzeln | **UNGEMESSEN**; das Kostentor mass +35 Prozent fuer ARENEN (`minimal_strength_core` 10.14), das ist die Obergrenze, nicht die Erwartung. Die 20-Partien-Stichprobe der Abnahme-Kette liefert die Zahl |
| **Erzeugung gesamt** | **rund 10,5 bis 14 h** | **ANNAHME** aus den drei Zeilen darueber |
| Bloecke fuers Fenster (rund 2.947 Dateien) | **rund 26 min** | `docs/window_generation.svg` ("2.947 Bloecke in 26 min", Rust-Bauer) |
| Monolith (Merge) | rund 9 min | `PREREG_v29_window.md` par.5 |
| Split und Tor 0 / Tor 2a | rund 5 min je Klasse, Tor 2a 271 s | `PREREG_v29_window.md` par.5 |
| **Training `v30-b01` KALT, 12 Epochen** | **8.164 s = 2,27 h** bei 4,72 Mio Samples | `docs/measured_runtimes.md` Z.62 (v23-b06, Monolith-Treffer). Fuer 888 statt 714 Eingaenge und rund 4,5 Mio Samples: **ANNAHME 2,3 bis 2,6 h** |
| Tor 1 Gating je Seed (200 Paare, 400 Sims, Logs) | **4.778 / 4.855 s = 80-81 min** bei 406er-Netzen | `minimal_strength_core` 10.13 (b09-Kanten) |
| dito mit 414er-Netzen | **ANNAHME rund 105-110 min je Seed** (+35 Prozent aus dem Kostentor) | `minimal_strength_core` 10.14 |
| Tor 2b, Plattenpunkte, Netz-Gesundheit | unter 30 min gesamt | `PREREG_v29_window.md` par.5 / par.6d |
| Rueckfall 1 Afterburner | **8-11 min** (600 Zusatzpartien, 6-12 Epochen) | `docs/measured_runtimes.md` Z.52-53 |
| Rueckfall 2 Warmstart von b09 | rund 1,2 h (Warmstart 12 Epochen) | `models/manifest_train_v29-b09_*.json` `laufzeit.wanduhr_s` 4.325 s |

**Summe des kritischen Pfads** (Erzeugung -> Kette -> Training -> Tor 1): **rund 17 bis 21 h**,
ANNAHME. Die Erzeugung dominiert; sie laeuft ohnehin ueber Nacht.

## par.8 OFFENE NUTZER-ENTSCHEIDE

1. **G-2-Haelfte** (par.1a): Vorschlag ist die Ausflug-Haelfte von `v27-b01`, also dieselbe Regel
   wie v28 und v29. Kein Entscheid noetig, wenn der Nutzer nichts anderes sagt -- er steht hier
   nur, weil er in v28 und v29 ausdruecklich getroffen wurde.
2. **Zweiter Arm?** par.4 laesst genau einen zu. Wenn der Nutzer die Zerlegung des Buendels will
   (Kaltstart gegen Warmstart bei sonst gleichem Rezept und Fenster, das waere `v30-b02` =
   Rueckfall 2 als eigener Arm statt als Rueckfall), ist das ein eigener Entscheid, rund 1,2 h
   Training plus 2 x 105 min Tor 1.
3. **Loeschung der `v26-b01`-Klassen** (1.201 Dateien), die mit v30 aus der Rotation fallen: nur
   mit restic-Beleg und pfadgenauer Freigabe, im Generationswechsel
   (`feedback_never_delete_without_confirmation`).
4. **Freigabe des Kettenstarts.** Die Erzeugung ist seit 2026-09-17 freigegeben (STATUS Punkt
   21); `tools/night_v30_chain.sh` ist geschrieben, aber NICHT gestartet und startet nur auf
   Anweisung (Regel seit 2026-09-03).
5. **Was passiert, wenn Tor 2a reisst** (H4): nach `docs/generation_loop.md` Vorlage an den
   Nutzer mit beiden Zahlen, keine stille Fortsetzung. Die
   Alternative waere, den v29-Korpus weiterzufahren und v30 nur als Rezept-Umstellung zu trainieren.

## par.9 ERGEBNISSE

(noch leer -- nichts erzeugt, nichts trainiert, nichts gemessen)

### Klasse 1 `v29-b11-policy` fertig, Tor 0 und Tor 2a (2026-09-18, 20:07 / 20:15): BEIDE GRUEN

**Erzeugung.** 400 Dateien, `laufzeit.wanduhr_s` 18.984,2 s = 5 h 16 min, **4,746 s je Partie**, n = 4.000
Partien, 790.970 Zuege, threads 11 (`data/manifest_v29-b11-policy_20260918_145006.json`). `cpu_s` bleibt leer,
`os.times()` fuehrt auf dieser Plattform keine Kinderzeiten. Nebenlast waehrend des ganzen Laufs: der
Cache-Waechter mit 3 Arbeitern (erlaubt, Kopf von `night_v30_generate.sh`); der Sanity-Check unten lief erst
NACH dem Klassenende und vor dem Start der zweiten Klasse, also nicht in diese Zahl hinein.

**Kosten gegen die Vorgaenger** (Grundmenge je die Policy-Klasse einer vollen Erzeugung, 4.000 Partien @100,
threads 11; Einheit Sekunden je Partie; Zahlen aus den `laufzeit`-Bloecken der Manifeste):
v28-Erzeugung (Generator `v27-b01`) 3,183 -> v29-Erzeugung (Generator `v28-b02`) 3,943 -> **v30-Erzeugung
(Generator `v29-b11`) 4,746**, also **+49,1 Prozent** gegen die v28-Linie und **+20,4 Prozent** gegen die
v29-Linie. Die 20-Partien-Stichprobe hatte +25 Prozent geschaetzt (`minimal_strength_core` 10.17). **Beide
Lesarten liegen ueber der 15-Prozent-Schwelle** aus STATUS Abschnitt 6 Punkt 2; die v31-Wiedervorlage des
Budget-Knopfs ist damit faellig, unabhaengig von der Bezugswahl. ACHTUNG Namensfalle, beim Nachtragen fast
falsch etikettiert: Manifeste heissen nach dem GENERATOR, `manifest_v28-b02-*` ist die v29-Erzeugung
(`docs/measured_runtimes.md`, Abschnitt Generation v30).

**Tor 2a ex post: HAELT.** `sp_voll` **0,90087 (+-0,01700)** fuer `v29-b11-policy` gegen **0,84275 (+-0,01670)**
fuer `v28-b02-policy`, Differenz **+0,05812**; n = 8.000 Seiten je Klasse, Grundmenge die jeweilige
Policy-Klasse, Einheit volle Spalten je Seite. Die Differenz ist groesser als die Summe beider Halbbreiten
(0,0337). Betriebsart geprueft: beide Klassen sind bei 100 Sims erzeugt (der Manifest-Diff zeigt `sims` nicht
als Abweichung), der Vergleich steht also nicht unter dem Suchtiefen-Effekt aus
`PREREG_search_depth_column_optimum.md` par.8e. Artefakt
`evaluations/artifacts/corpus_sanity_v29-b11-policy.json`, Laufzeit 446,4 s einkernig.

**Tor 0, die sechs Standard-Kennzahlen** (CLAUDE.md; je Seite, n = 8.000 Seiten aus 4.000 Partien; Margin ist
im Self-Play per Konstruktion 0):

| Kennzahl | `v28-b02` (v29-Erzeugung) | `v29-b11` (v30-Erzeugung) | Differenz |
| --- | --- | --- | --- |
| 1 Reihen: volle Reihen | 0,1070 | 0,0912 | -0,0158 |
| 1 Reihen: mittlerer Fuellstand von 6 | 2,8971 | 2,9097 | +0,0126 |
| 2 Spalten: volle Spalten | 0,8427 | 0,9009 | +0,0581 |
| 2 Spalten: Teilspalten >= 4 | 2,1665 | 2,1926 | +0,0261 |
| 2 Spalten: Teilspalten >= 3 | 3,1307 | 3,1397 | +0,0090 |
| 2 Spalten: hoechste Spalte von 6 | 5,5375 | 5,5691 | +0,0316 |
| 3 Strafleiste: Steine | 5,5784 | 5,2832 | -0,2951 |
| 5 Eigene Punkte | 48,6617 | 50,2821 | +1,6204 |
| 6 Margin | 0,0000 | 0,0000 | 0,0000 |

| 4 Punkte je Wertungsplatte | `v28-b02` | `v29-b11` | Differenz |
| --- | --- | --- | --- |
| k0 | +0,32 | +0,29 | -0,03 |
| k1 | +6,29 | +6,65 | +0,35 |
| k2 | +0,34 | +0,32 | -0,02 |
| k3 | +3,30 | +3,29 | -0,02 |
| k4 | +10,22 | +10,19 | -0,03 |
| k5 | +7,62 | +8,08 | +0,46 |
| k6 Spezialfelder | -9,54 | -9,39 | +0,15 |
| k7 | +0,19 | +0,17 | -0,02 |

**Lesart, vorsichtig:** der neue Generator baut mehr Spalten, nimmt weniger Strafsteine und holt 1,62 Punkte
je Seite mehr, bei etwas weniger vollen Reihen. Das ist die Richtung der Kampagnenlinie
(`project_long_row_avoidance_is_correct`). Es ist aber KEIN Staerkebeleg: hier spielt der Generator gegen sich
selbst, der Margin ist per Konstruktion 0, und `v29-b11` unterscheidet sich von `v28-b02` um Generation,
Wheel und Aktionsraum zugleich. Die Staerkefrage entscheidet Tor 1.

### Manifest-Diff und Stack-Draw-Kontrolle (2026-09-18, 18:20, par.3 Punkte 3 und 4): GRUEN

Gefahren wurde der Diff-Block aus `tools/night_v30_chain.sh` Schritt 0b, vorgezogen waehrend der Erzeugung
(reines JSON-Lesen, keine nennenswerte Last): `data/manifest_v29-b11-policy_20260918_145006.json` gegen
`data/manifest_v28-b02-policy_20260913_120816.json`.

**`engine_config` wie vorregistriert:** `input_size` 888, `num_actions` 414, `contract_hash`
`6ef829e564c58bd5`, `stack_draw_research` `True` (Punkt 4 erfuellt, der Korpus traegt Slot-Datensaetze).

**`cli_args`-Abweichungen, alle erwartet:** `model` (`v28-b02_brierbest` -> `v29-b11`), `seed`
(20260920 -> 20260930), `spec` (`start_by_search_on` -> `v30_generation`), `version`. Das Werkzeug meldet
EINE unerwartete Abweichung, `return_order_random_p` `None` -> `0.0`; sie ist keine: der Knopf existierte zur
v28-Referenz noch nicht (`None` = Flag unbekannt), `0.0` ist "aus" und zieht laut
`engine/src/self_play.rs::sample_random_return_order` keine Zufallszahl (bitidentisch), und unter
`MOSAIC_STACK_DRAW_RESEARCH=1` erreicht er den Aufloeser ohnehin nicht (`knob_registry.rs` Z.116,
`PREREG_dome_return_order.md` par.12.9). **Kein Stopp.**

**Ein Melde-Defekt mehr als in STATUS Abschnitt 6 Punkt 6 gelistet:** das Manifest zeigt
`return_order_mode 0`, waehrend `models/v30_generation.spec.json` `1` traegt (beides am Dateiinhalt gelesen).
Ursache ist dieselbe wie bei den vier dort genannten Feldern: `engine/src/lib.rs` Z.834 exportiert
`SearchConfig::from_env().return_order_mode`, also den Env-Default statt des wirksamen Spec-Werts.
**Folgenlos fuer diesen Korpus** -- unter dem Research-Knopf ist das Feld wirkungslos (par.3 Punkt 4), und das
Manifest nennt den Spec-Pfad, es geht also kein Beleg verloren. Die Liste in STATUS Abschnitt 6 Punkt 6 ist um
`return_order_mode` ergaenzt.

### Wiedervorlage erster Record (2026-09-18, 14:54): GRUEN

**Wiedervorlage am ersten Record der v30-Erzeugung GRUEN (2026-09-18, 14:54; `data/selfplay_v29-b11-policy_20260918_1450_g10.pkl`,
1.952 Records aus 10 Partien, gzip-gelesen, IDs ueber `neural_net.action_to_id`):** P.12 `designs` 577 Records,
P.16 `designs_ordered` 577 Records (nur wo ein eigener Block liegt), Mondknoten 406-410 in `valid_actions` 478 / in
`policy` 424, Rueckgabeknoten 411-413 11 / 11, Rotation 640 / 640, Slot 8.132. Der v30-Korpus traegt die neuen
Merkmale und Knoten mit Lernziel; nichts faellt nach v31.
