# Mosaic-AI – Status & Fahrplan

**Dieses Dokument traegt NUR Aktuelles und Offenes.** Neufassung vom
2026-08-31 (Nutzer-Auftrag); der vollstaendige Stand davor liegt in
`../archive/history.md`, Kapitel **"Vollstaendiger STATUS-Stand vom
2026-08-31 (vor der Neufassung)"** -- dort steht jede Herleitung, die hier
nur noch als Verweis vorkommt, inklusive der kompletten v22-Chronologie
(Faecher-Durchgang, Schlachtplan v22->v23, Nachtprogramme, abgeloeste
Tor-Fassungen).

**Pflegeregel:** wer einen Befund erzeugt, traegt ihn im selben Zug hier nach
und prueft, ob ein anderer Abschnitt dadurch falsch wird. Wer einen Strang
abschliesst, schiebt die Herleitung ins Archiv und laesst hier eine Zeile mit
Verweis stehen.

**Zahlen ohne Datum stammen aus dem Stand vom 2026-08-30 und sind in dieser
Neufassung nicht neu nachgemessen worden.**

**Dauerhaftes Prozesswissen steht NICHT hier**, sondern kanonisch in
`../docs/`: `generation_loop.md` (die Schleife und ihre Tore),
`promotion_checklist.md`, `generation_naming.md`, `working_rules.md`,
`pitfalls.md`, `measured_runtimes.md`, `architecture_reference.md`. Wer an
diesen Inhalten etwas aendert, aendert es DORT.

---

## 1. WAS GERADE LAEUFT (Stand 2026-09-03, 14:30 -- Sitzung mosaic-ai-6d, Tagprogramm nach der Uebergabe von 09:00)

**LAEUFT: Kette D `night_chain_0903d.sh`** (Start 2026-09-04 11:38, CPU
exklusiv): K3-P-Arena Replikation Kontrolle / C 1,0 / C 2,0 (Seed 20261009,
2 x 80), argmax C 2,0 plus Huellen-Sonde, dann K3-P im Erzeugungs-
Betriebspunkt @100 (Pilot-Rezept, 400 Partien, Seed 20260910, Tag
`pilot24k3p`) mit Symmetrie-Sonde und Huellen-Sonde gegen den Piloten.
Ende gegen 15:30. Kette C (K3-R/K3-O) ist durch: 8.9a.

**Kette B (2026-09-03 21:25 bis 2026-09-04 07:02) ist durch.** Ergebnisse
je Hebel, alle am `v23-b01_brierbest`, Bezug b01 (argmax 0,515 Spalten,
Huelle H_end 0,659):

| Hebel | Siege (160 Paare) | Spalten argmax / Arena | Huelle argmax / Arena | Verdikt |
| --- | --- | --- | --- | --- |
| K1 c = 0,2 (Margen-Utility) | 104:56 dann 83:77; gegen v21 77:83 (b01: 88:72) | 0,36 / -0,08 | -- | ENTSCHIEDEN: kein Rezept, keine Kante (par.15-17) |
| K3 S/T/S+T (Raster) | 80:80 ... 81:79 | 0,51-0,53 / 0 | 0 / 0 | ENTSCHIEDEN: falscher Hebel (par.9) |
| 8.6 Value im Tiling | 82:78 / 84:76 / 80:80 | 0,49 / 0 | 0 / 0 | Nullbefund (8.6a) |
| Huellen-Bauer (Vorzug) | gegen hv1 68:92 statt 131:29 | 0,275 / -- | 0,677 / +0,07 | unbrauchbar als Uebersteuerung (8.7a) |
| **K3-P projiziert C 0,2 / 0,5 / 1,0** | **88 / 92 / 95 : 80** (p 0,38 / 0,21 / 0,11) | 0,455 / 0,480 / **0,555** und Arena +0,06 / +0,11 / +0,10 | H_end 0,665 / 0,687 / **0,703**; Arena +0,00 / **+0,08 / +0,10** (t 3,5 / 6,2) | **REPLIZIERT (8.7c): C 1,0 gepoolt 191:129 auf 320 Paaren, p = 0,014, Seeds deckungsgleich; Huelle Arena +0,16 im zweiten Seed. K3 traegt; C 2,0 schwaecher (88:72)** |
| K3-R Erreichbarkeit C 0,5 / 1,0 | 82 / 91 : 80 | 0,49 / **0,39** und Arena -0,11 / -0,14 | H_end 0,674 / 0,683; Arena +0,04 / +0,07 | hebt Huelle, kostet Spalten (8.9a) |
| K3-O Ownership C 0,5 / 1,0 | 86 / 87 : 80 | 0,475 / 0,470 | H_end 0,660 / 0,665 | kaum Huelle, kostet Punkte 43,9 (8.9a) |
| Material-Pilot v24 | -- | Value-Klasse 0,726, 50 % Seiten mit voller Spalte (v23 35 %) | -- | Tor 0 fuer b01 @100 vorab belegt (v24 par.7) |

**Nutzer-Entscheid 2026-09-04, 13:20: v24 bekommt KEINE weiteren Arme.**
v24 traegt Generator b01 @100, Knopf-Kandidat K3-P (Kette D entscheidet),
Arme b02/b03 (Seeding-Kuratierung, `start_position_seeding` par.7) und die
Huellen-Wiedervorlage (`geometric_envelope` par.8.9b). Die uebrigen offenen
Preregs (Stand: 16 OFFEN, 81 ENTSCHIEDEN, 8 UEBERHOLT) werden bei Bedarf in
v25 und folgenden Generationen bearbeitet; **Ziel des Nutzers: die offenen
Preregs im Lauf der naechsten Generationen auf rund 7 abarbeiten** -- neue
Preregs nur gegen geschlossene alte, Arme je Generation so waehlen, dass sie
Offenes ENTSCHEIDEN.

**Fuer die v24-Erzeugung heisst das (Nutzer-Entscheid):** Generator bleibt
b01 @100; offen ist, ob K3-P (C 1,0, projiziert) als Rezept-Knopf in die
Erzeugung geht -- dafuer fehlen die Replikation der Siege und die Frage, ob
der Effekt bei 100 Sims (Erzeugung) so gross ist wie bei 400 (Instrument).

### Was das Tagprogramm 2026-09-03 bis 14:30 ergeben hat (Chronik: `night_run_20260902.md`, ab 09:08)

1. **Reanalyze-Relabel durch** (09:36): 200 Dateien, 205.854 von 210.529
   Steinzug-Records mit b01 @400 nachgelabelt, 11,0 h Wanduhr
   (`reanalyze_label_depth` par.A4).
2. **`v23-b07` trainiert und ABGENOMMEN** (par.A5, ENTSCHIEDEN): Arena 75:85
   gegen b01 (p = 0,55, Margin -1,4), argmax-Spalten 0,445 gegen 0,515,
   Arena-Spalten -0,08/-0,14, Orakel 4/4 knapp vorn, Value-Kopf unbewegt.
   Tiefes Nachlabeln bringt keine Staerke und kostet Spalten (par.4a, mild).
   **b01 bleibt Generator fuer v24.** Manifest-Diff gegen b01 exakt die vier
   erwarteten Felder. Die 400 Value-Kopien sind aus `data/` entfernt (STATUS
   Punkt 7 der Uebergabe); die 200 Deep-Kopien `selfplay_v22-b05deep-policy_*`
   liegen noch in `data/` (Original in `data/relabeled_v23_deep/`).
3. **K1 gebaut und erstgemessen** (`saturating_score_utility` par.15, Commits
   8ffb2e4/d5e687c): Anker-Drift GRUEN, Netz-Pfad bei c = 0 Record fuer Record
   identisch. Arena am b01 (160 Paare je Arm, Knopf-Seite gegen dasselbe Netz
   ohne Knopf): **c = 0,2 gewinnt 104:56 (p = 0,006, Margin +4,9)**, c = 0,1
   und 0,3 Nullbefunde -- aber Spalten darunter (Arena -0,13, argmax 0,36
   gegen 0,52). **Replikation (Seed 20261003): 83:77, p = 0,82; gepoolt
   187:133, p = 0,03, Seeds uneins (z 1,8); Margin in jedem Lauf +2 bis +5.**
   Verdikt par.16, ENTSCHIEDEN: Marge wird zu Punkten, nicht stabil zu
   Siegen, Spalten darunter -- K1 geht NICHT ins v24-Rezept, Skalenwechsel
   par.4b entfaellt. Champion-Kante mit c = 0,2 fuer den Spielbetrieb waere
   ein eigener Nutzer-Entscheid.
4. **K3 gebaut** (`geometric_envelope` par.8.2/8.3, Commit e69aec3): Modul
   `envelope.rs`, drei Knoepfe, Tiling-Zweig vor dem Stichentscheid, W_TILE je
   Seite. Anker-Drift und Netz-Pfad-Paritaet bei allen Knoepfen 0 GRUEN.
   **Noch nicht gemessen.** par.8.6 wartet auf den Nutzer.
5. Werkzeuge: `tools/probes/env_ab_swap_eval.py` (gepoolte Knopf-Seiten-
   Auswertung mit Brett-Tausch), `arena_column_probe.py` liefert jetzt die
   sechs Standard-Kennzahlen und die Huellen-Deckung H je Seite;
   `generator_repro_probe.py` repariert; `night_b07_chain.sh` und v24-Rezept
   par.6d: `generate_carrier_manifest.py --out` ist relativ zu `data/`.

### Reihenfolge fuer den Rest des Tages (Nutzer-Freigabe 2026-09-03: alles ausser der v24-Erzeugung)

1. ~~Watcher, Relabel-Kennzahlen~~ ERLEDIGT 09:36.
2. ~~b07-Kette, Manifest-Diff~~ ERLEDIGT 09:52.
3. ~~K1 bauen, messen, replizieren~~ ERLEDIGT (par.15/16, ENTSCHIEDEN).
   argmax-Profile fuer c = 0,1 und 0,3 entfallen (Nullbefunde, Verdikt
   steht).
4. ~~b07 abnehmen~~ ERLEDIGT (par.A5).
5. **K3 messen** nach par.8.4: Arena LAEUFT (siehe oben); danach argmax je
   Arm (`argmax_profile.sh`, rund 28 min je Arm, Seed 20260931, Tags
   `tor2a-k3s01`, `tor2a-k3s02`, `tor2a-k3t05`, `tor2a-k3t10`, `tor2a-k3st`),
   Spaltensonde auf den Arena-Logs, Registrierung als par.9 samt Kopf.
   par.8.6 nur nach Nutzer-Bestaetigung.
6. **v24-Material-Pilot** (`night_run_20260902.md` N2) in einem freien
   CPU-Fenster; registrieren in `PREREG_v24_window.md` par.7.
7. ~~Aufraeumen~~ `archive_pre_v24` am 2026-09-03 16:40 auf Nutzer-Freigabe
   GELOESCHT (1,7 GB; fuenf Stichproben vorher per `restic find` im Snapshot
   e77c2d7c bestaetigt -- Pfade dort unter `data/`), Fundorte in
   `v23_reachability_recheck` par.7, `frozen_v3_eval_set` par.7-Tabelle und
   `reanalyze_label_depth` par.A4 nachgezogen. Die 200 Deep-Kopien
   `selfplay_v22-b05deep-policy_*` in `data/` bleiben (nicht angekuendigt).
8. **NICHT:** die v24-Erzeugung (`PREREG_v24_window.md` par.6) -- nur auf
   Nutzer-Anweisung.

### Stand der v24-Vorbereitung (vollstaendig registriert)

`PREREG_v24_window.md` par.6 (Rezept) und par.8 (Arme b01/b02/b03, Knoepfe
K1/K3; K2 gegenstandslos), `generation_loop.md` (Gleichstandsregel),
`start_position_seeding` par.7 (b03-Kuratierung), `saturating_score_utility`
par.14 (K1 baureif), `geometric_envelope` par.8 (K3 baureif, 8.6 offen).
Index: 18 OFFEN, 79 ENTSCHIEDEN, 8 UEBERHOLT. Chronik der letzten Naechte:
`night_run_20260901.md`, `night_run_20260902.md`.


### Was die Nacht 2026-09-01/02 ergeben hat (Chronik: `night_run_20260901.md`)

1. **Relabel-Arm b05 auf 240 Paaren: Nullbefund.** 246:234 fuer b05, p = 0,65,
   der dritte Seed dreht um; Spalten 0,676 gegen 0,642, KI schliesst Null ein.
   Weder Gewinn noch Schaden. **b01 bleibt Generator fuer v24**, jetzt per
   Nullbefund statt per nachtraeglicher Gleichstandsregel
   (`reanalyze_label_depth` par.A3).
2. **Kaltstart ist die Ursache, nicht das Lernraten-Rezept.** `v23-b06`
   (Kaltstart mit exakt dem b01-Rezept) baut 0,18 volle Spalten und verliert
   65:95 gegen b01 (p = 0,024). "Spaltenwissen sitzt in der LINIE" ist damit
   einfaktoriell belegt (`capacity_sim_frontier` par.14b).
3. **Stufe 4 komplett.** Teil A auf 200 distinkten Zustaenden (0,825 gegen
   0,490 Verwerfung, 70:3); Teil B: die tiefere Suche verwirft
   spaltenrelevante Vorschlaege im GLEICHEN Anteil wie alle anderen, nur
   doppelt so oft insgesamt -- Spaltenverlust als Nebenwirkung, kein gezieltes
   Verwerfen (`search_depth_column_optimum` par.7, ENTSCHIEDEN).
4. **Spreizung des Value-Kopfs im Tiling gemessen:** b01 0,048/0,065 gegen
   plattenblind 0,018, aber die multiplikative Form kippt in 1 von 142 bzw. 4
   von 192 Stellungen einen Punktvorsprung. Form A tot, B oder C Pflicht
   (`geometric_envelope` par.3f).
5. **Phase 3 auf Block-Ebene bestaetigt** (t 3,25 und -2,87 fuer die beiden
   signifikanten Arme; `r5_value_calibration` par.12), **Reachability
   zifferngleich reproduziert** (par.7 dort).
6. **Hebel 3 der Cache-Prereg abgenommen:** Zusammenfuegen 344 s statt 4,98 h,
   Datenaufbau im Training 31 s. Zwei Bedingungen waren vorher unbekannt
   (Monolith fuer den TRAININGSANTEIL, Block-Bau unter der Trainings-Umgebung;
   `cache_build_time` par.12, Werkzeug `tools/window_train_split.py`).
7. **Blockgroesse 5 ist Default in allen fuenf Arena-Werkzeugen** (Nutzer,
   zweiter Vorfall; `working_rules.md`, `pitfalls.md`).

### Was als Naechstes ansteht

| Was | Kosten | Anmerkung |
| --- | --- | --- |
| ~~Generatorwahl-Regel bei Gleichstand~~ | -- | ENTSCHIEDEN 2026-09-02 (Nutzer): Staerke schliesst aus, Spaltenprofil entscheidet, sonst Amtsinhaber (`docs/generation_loop.md`, "Generatorwahl unter Armen") |
| ~~Reanalyze-Arm `v23-b07`~~ | -- | ABGENOMMEN 2026-09-03 (`reanalyze_label_depth` par.A5): 75:85 gegen b01, Spalten 0,445 gegen 0,515 -- keine Staerke, weniger Spalten; b01 bleibt Generator. Reanalyze geht NICHT ins v24-Rezept |
| **v24-Erzeugung** | 11,9 h bei threads 11 | Rezept vollstaendig in `PREREG_v24_window.md` par.6; Generator `v23-b01_brierbest`. Startet NUR auf Nutzer-Anweisung |
| Vor dem v24-Training: Monolith fuer den Trainingsanteil | rund 45 min | `tools/window_train_split.py` -> `build_cache_incremental.py --merge-out` unter der Trainings-Umgebung (`cache_build_time` par.12) |
| ~~b04-Zweig~~ | -- | GEPARKT 2026-09-02 (Nutzer): das Problem sitzt im Value-Kopf, nicht in Policy, Breite oder Merkmalsform (`capacity_sim_frontier` par.15). Der Fahrplan traegt die These ab jetzt als Arbeitshypothese |
| Merkposten: `--select-by-brier` bei Kaltstarts | -- | b02 und b06 haben `_brierbest` in Epoche 1 mit BESSEREM Brier als b01 bei schwaecherem Spiel; der b05-Val-Pool misst nicht, was in der Arena zaehlt (`capacity_sim_frontier` par.14b) |
| Push | -- | nie ohne Anweisung; Commits der Nacht sind lokal |

## 2. WAS DIE GENERATION v23 ERGEBEN HAT

**Alle vier Tore bestanden -- das v24-Self-Play ist freigegeben**
(`docs/generation_loop.md` Schritt 9). Herleitungen in
`PREREG_v23_window.md` par.2b bis par.2g.

| Tor | Ergebnis |
| --- | --- |
| 0 Korpus traegt das Signal | Symmetrie-Trennung +0,4041 (t 41,26), 5.629 von 16.000 Seiten mit voller Spalte |
| 1 Siege gegen b05 | **119:61** aus zwei unabhaengigen Seeds (Champion-Strenge erfuellt) |
| 2a Spalten im Self-Play | 0,5150 gegen 0,3100, gepaart **+0,2050** (t 4,47) |
| 2b Spalten in der Arena | 0,6456 gegen 0,4304, gepaart **+0,2152** (t 2,61) |

| Elo-Kante | Ergebnis |
| --- | --- |
| gegen **v22-b05** | 119:61 -- signifikant |
| gegen **v21** (Champion) | 219:181, p = 0,084, KI [-0,013, +0,393] -- **nicht belegt besser**, Augenhoehe. **KEINE Promotion**, v21 bleibt Champion |
| gegen **hv1** (Anker) | 127:23 aus 150 (84,7 Prozent), eingetragen (Abschnitt 4) |

**Phase 3 gemessen, NEGATIV (par.11 der R5-Kalibrierung):** die
Betrags-Daempfung ist unveraendert -- b01 0,0859 gegen b05 0,0886 auf
denselben 139 Paaren. Der Korpus heilt sie nicht. b01 wurde also deutlich
staerker und baut 66 Prozent mehr Spalten, OHNE dass der Bewerter repariert
wurde; der Punkte-Kopf trifft dieselbe Groesse mit 0,97. **Der Eingriff ist
damit faellig**, Erfolgstest "kippt die Sims-Kurve?".

**`v23-b02` (Kaltstart):** Early Stop nach Epoche 15/40, **4,22 h** gegen
b01s 5,97 h -- ein Kaltstart kostet mit stehendem Fenster-Cache WENIGER als
ein Warmstart. Sein brierbestes Modell liegt allerdings bei Epoche 1
(par.2g) -- die Checkpoint-Arena hat es trotzdem zum Kandidaten gemacht:
**33:47 fuer `_brierbest`** (SPRT H0, Vorzeichentest p = 0,189, gepaarte
Differenz -0,350 [-0,791, +0,091], Punkte 42,33 gegen 37,53). Nicht
signifikant, aber die vorab registrierte Regel laesst hier den Punktschaetzer
entscheiden (par.2h).

---

## 3. WAS ALS NAECHSTES ZU TUN IST

**Nutzer-Zuschnitt fuer diese Generation (2026-08-31):** relabelter Sockel,
b02, b03, Phase 3 -- dann v24. **Stand 2026-09-01: alle vier erledigt**, es
bleibt v24 (Abschnitt 1, Rezept in `PREREG_v24_window.md` par.6). Nicht in diesem Zyklus: Kuppelplatten-
Verteilung, Arm K, b04-Breite, geometrisches Gelaender (alle registriert).

### 3.1 Relabel-Arm: GEFAHREN (2026-09-01)

`v23-b05` (Policy-Klasse per hv2-Lehrer relabelt, sonst wie b01): Arena auf
240 Paare verlaengert (2026-09-02): **246:234 fuer b05, p = 0,65**, dritter
Seed 75:85; Spalten 0,676 gegen 0,642, KI [-0,06, +0,13]. Weder Gewinn noch
Schaden, b01 bleibt Generator (par.A3). Herleitung `PREREG_reanalyze_label_depth.md` par.A1; die dortige
Zeile-1-Frage (Spielen gegen Labeln bei Suchtiefe) ist damit NICHT gemessen,
gefahren wurde die Lehrer-Variante. Laufzeit 7,42 h, davon 4,98 h einkerniger
Datenaufbau (`cache_build_time` par.11).

### 3.2 Phase 3: GESCHLOSSEN ohne Bau (2026-09-01)

Stufe 0 der Prereg (`PREREG_r5_value_calibration` par.12) hat die Praemisse
GEPRUEFT, bevor etwas gebaut wurde -- und sie faellt:

| Arm (je 200 Partien, argmax, Seed 20260931) | volle Spalten | gegen Kontrolle |
| --- | --- | --- |
| @100 Sims | **0,7200** | +0,205 (t 3,97) |
| @400 Sims (Kontrolle) | 0,5150 | -- |
| @400, `VALUE_CAL_B=2,0` | 0,3900 | -0,125 (t -2,7) |
| @400, `VALUE_CAL_B=0,5` | 0,5325 | +0,018 (n.s.) |
| @400, `POINTS_UTILITY_W=0,1` | 0,4850 | -0,030 (n.s.) |

**Die Delle gibt es auch bei b01** (0,205, vorher nur an b05 gemessen), **aber
keine Einstellung des Value-Kopfs holt sie zurueck.** Verstaerken schadet,
Daempfen tut nichts, Punkte-Beimischung tut nichts. Die Betrags-Daempfung ist
damit ein registrierter Befund OHNE benannten Nutzniesser -- der Eingriff
entfaellt, der Trainingslauf ist gespart. Die Ursachenfrage erbt
`PREREG_search_depth_column_optimum` Stufe 4: sie liegt nicht in der Skalierung
des Blattwerts und nicht in fehlender Punkte-Information, sondern in dem, was die
tiefere Suche mit den Kandidaten TUT.

**Nebenbefund zu einem Nutzer-Einwand:** die vier fruher geschlossenen Wege am
Verbraucher wurden alle auf plattenBLINDEM v21 gemessen. Der billigste davon
(Punkte-Blend) ist hier auf b01 wiederholt worden und traegt auch dort nicht --
fuer die SPALTEN. Fuer die Staerke sagt der Arm nichts, die alte Schliessung war
eine Staerke-Messung.

### 3.2b Die Tiefen-Delle: vier Wurzel-Eingriffe gemessen, alle wirkungslos

| Eingriff (b01, argmax @400, je 200 Partien) | volle Spalten |
| --- | --- |
| Kontrolle | 0,5150 |
| `VALUE_CAL_B = 2,0` | 0,3900 (-0,125, schaedlich) |
| `VALUE_CAL_B = 0,5` | 0,5325 (n.s.) |
| `POINTS_UTILITY_W = 0,1` | 0,4850 (n.s.) |
| `MOSAIC_GUMBEL_C_SCALE = 0,36` | 0,5000 (n.s.) |
| zum Vergleich: 100 statt 400 Sims | **0,7200** |

Weder Betrag noch Balance noch Zusatzinformation am Blattwert bewegen die Delle --
nur die Suchtiefe selbst tut es. **Was bleibt, liegt tiefer im Baum:** was die Suche
in den Fortsetzungen findet und nach oben propagiert (`search_depth_column_optimum`
Stufe 4). Die quantitativ saubere Erklaerung ueber das sigma/Prior-Verhaeltnis (2,81)
ist gepruft und WIDERLEGT -- sie steht in `prior_blind_spot` par.G3 als solche
markiert.

**Neuer Knopf, bleibt:** `MOSAIC_GUMBEL_C_SCALE` (Default 1,0, paritaetsgeprueft an
20 Partien, im Lauf-Manifest sichtbar). Er kostet nichts und macht die naechste
Frage an die Prior/Value-Balance ohne Bau messbar.

### 3.3 Dann v24 -- Zuschnitt STEHT (2026-09-01)

`PREREG_v24_window.md` ist angelegt und der Generator entschieden: **b01**,
weil kein Arm belegt besser ist. Form wie v23, neu besetzt:

| Klasse | Posten | Partien |
| --- | --- | --- |
| Sockel (Policy) | `v23-b01` Self-Play | 4.000 |
| Sockel (Policy) | `hv2`, policy-aktiv | 1.800 |
| Schwarm (Value) | `v23-b01` Self-Play | 8.000 |
| Schwarm (Value) | `hv2`, policy-maskiert | 15.650 |

**Summe 29.450.** Der hv2-Anteil ist identisch mit dem von v23 (1.745 Dateien
a 10 Partien) und wird UNVERAENDERT weiterverwendet -- **es muss kein einziges
Lehrerspiel neu erzeugt werden**, die Traegerauswahl kommt aus
`data/carriers_v23_hv2.txt`. Neu sind allein die 12.000 b01-Partien, mit
`--per-file 10` (`docs/working_rules.md`). Verfahren: `docs/generation_loop.md`.

**Die Daten der Vorgeneration sind archiviert** (Nutzer, 2026-09-01): in
`data/` stehen nur noch die 1.745 hv2-Dateien des Fensters plus ihre Bloecke.
Alles andere liegt im Archiv, samt einer README, die festhaelt, welche
Korpora BELEGE laufender Preregs sind (frozen_v3-Quelle, die vier
Phase-3-Arme, der Tor-2a-Referenzlauf).

### 3.4 Belegungsplan (GPU und CPU parallel)

Regel und Thread-Budget: `../docs/working_rules.md`, Abschnitt "Auslastung".
Ein Training belegt gemessen rund EINEN Kern, der CPU-Auftrag daneben darf
also rund 10 Threads nehmen. Zwei CPU-Messungen gegeneinander bleiben
verboten, und ein unter Nebenlast gefahrener `laufzeit`-Block wird als
solcher markiert.

---

## 4. STAND JETZT

**Champion:** `v21_2d_brierbest`, Elo **1227** [1191, 1269] auf der R5-Fix-Leiter
(`python tools/elo_tracker.py report`, nachgefuehrt 2026-09-01; die Zahl 1226 [1188, 1269]
stand hier aus dem Fit vor den beiden b05-Tor-1-Kanten, der fruehere Wert 1215
aus dem Fit ohne Anker- und Champion-Kante von b01). Kanten ueber die
Fix-Grenze nie mischen. **Staerkster Knoten der Leiter ist inzwischen NICHT der
Champion:** `v23-b01_brierbest` steht bei 1263 -- die KI ueberlappen, die
Promotionsregel haengt an der Champion-Kante, und die war nicht signifikant.

**Bester Stand der Spalten-Linie: `v23-b01_brierbest`** (seit 2026-08-31) --
volle Spalten 0,5150 am argmax-Instrument, 119:61 gegen den Vorgaenger b05,
gegen den Champion 219:181 (nicht signifikant). **Anker-Kante gefochten
(2026-08-31, 22:39): 127:23 aus 150 = 84,7 Prozent** gegen
`Heuristik_hv1_anchor`@150, Cross-Aera, Golden-Selbsttest gruen, Ergebnisse per
Determinismus-Probe freigegeben. **ES GIBT KEIN REMIS** (Nutzer-Hinweis, Regel an
`game.rs:586` geprueft: bei Gleichstand gewinnt, wer den Startspielerstein zuletzt
nahm): der Schiedsrichter meldete drei Partien faelschlich als Remis, alle drei gehen
an b01. `frozen_referee_match.py:380` liest den Tie-Break jetzt aus dem Zustand
(`first_player_next_round`), Gegenprobe auf denselben Seeds bestaetigt es. Die
Rust-Arenen waren nie betroffen. Kennzahlen je Seite: volle Spalten 0,953 gegen
0,027, Punkte 53,97 gegen 36,13, Margin +17,84, Strafpunkte -14,31 gegen -20,17.
Elo als HERLEITUNG: rund +297 ueber dem Anker (aus 84,7 Prozent), und rund +33 ueber
v21 aus der Champion-Kante. Beide Kanten sind seit dem 2026-08-31 in
`elo_history.csv` und die Anker-Kante zusaetzlich in `arena_trends.csv`. Zum
Vergleich, ueber zwei Instrumente hinweg (Paritaet 20/20 belegt): v21 kam am Anker
auf 116 von 150 (77,3 Prozent, Remis dort nicht ausgewiesen).

**EINGETRAGEN am 2026-08-31** in `elo_history.csv` und `arena_trends.csv`.
Beim Eintragen fiel auf, dass der Tracker auf den LITERALEN Namen `Heuristik`
verankerte, waehrend die Checkliste `Heuristik_hv1_anchor` vorschreibt -- die Kante
landete dadurch in einer eigenen, freien Komponente (b01 1148 / Anker 852, Summe
exakt 2000). BEHOBEN, siehe unten; Herleitung in `PREREG_agent_encapsulation.md`
par.13.

**Die Vorbedingung ist inzwischen GEMESSEN (2026-08-31, Nutzer-Vorgabe: nicht
gegeneinander spielen lassen, sondern Zug fuer Zug vergleichen).**
`tools/verify_frozen_heuristic.py` in beiden Modi, hv1-Rezept aus dem Manifest
(10 Partien, 600 Sims, Seed 20260826):

| Modus | Verdikt | verglichen | Wanduhr |
| --- | --- | --- | --- |
| Live-Wheel (Drift) | **GRUEN** | 1.763 Schritte, Feld fuer Feld, keine Abweichung | 22,2 s |
| Artefakt-Wheel (Konservierung) | **GRUEN** | dieselben 1.763 Schritte | 13,4 s |

Dazu die Referee-Paritaet neu gefahren (`anchor_referee_parity_20260831.json`):
20/20 identisch in beiden Modi, 0 Abweichungen. **Der lebende Code spielt hv1 also
Zug fuer Zug wie das Artefakt** -- die Engine-Aenderungen seit dem Einfrieren haben
den Anker nicht bewegt. Ab jetzt Pflicht nach jeder Engine-Aenderung, als Skill
`mosaic-anchor-invariance` abgelegt.

**Nutzer-Klarstellung dazu:** die In-Process-Heuristik ist eine
ENTWICKLUNGSUMGEBUNG, kein Vergleichswert. Der Fixpunkt gehoert an das Artefakt;
"der Anker ist gedriftet" ist keine moegliche Diagnose, ein rotes Ergebnis hiesse,
der lebende Code hat sich bewegt.

**GESETZT (Nutzer-Anweisung 2026-08-31): der Anker IST das Artefakt.**
`ANCHOR_NAME = "Heuristik_hv1_anchor"` in `tools/elo_tracker.py`, dazu
`ANCHOR_ALIASES = {"Heuristik": ...}` fuer die Zeilen vor der Umbenennung.
`Heuristik_v2huelle` bleibt ein eigener Spieler. Registriert in
`PREREG_agent_encapsulation.md` par.13, Ablauf als Skill
`mosaic-anchor-invariance`, Checkliste nachgezogen.

**Die Leiter danach** (`python tools/elo_tracker.py report`, 11 Zeilen, kein
einziger "NICHT verbunden"-Vermerk mehr; eingetragen sind seither auch die
beiden Tor-1-Gatings gegen b05):

| Modell | Elo | 95%-KI | Partien |
| --- | --- | --- | --- |
| **v23-b01_brierbest@400** | **1263** | [1223, 1311] | 730 |
| v21_2d_brierbest@400 | 1227 | [1191, 1269] | 1407 |
| v20_2d_opp_brierbest@400 | 1194 | [1158, 1235] | 950 |
| v19_2d_best@400 | 1142 | [1103, 1186] | 550 |
| Heuristik_v2huelle@150 | 1137 | [1086, 1190] | 407 |
| v22-b05@400 | 1136 | [1074, 1198] | 230 |
| Heuristik_hv1_anchor@150 | 1000 | fix | 600 |

**Beide Kanten sind drin (Nutzer-Anweisung 2026-08-31, "ist ja ein valides
match"): die Champion-Kante 219:181 gegen v21 ist als 9. Zeile eingetragen** --
informativ, kein Promotionsentscheid. Sie zieht b01 von 1297 (Anker-Kante allein)
auf 1266; mit den beiden b05-Kanten dazu steht er bei **1263** ueber 730 Partien.
Anker- und Champion-Kante implizierten einzeln 1297 und rund 1259, der gemeinsame
Fit legt sich dazwischen. Die KI von b01 [1223, 1311] und v21 [1191, 1269]
ueberlappen -- dieselbe Aussage wie die
Champion-Kante selbst: Augenhoehe, nicht belegt besser, keine Promotion.

**Was noch offen BLEIBT:** der Alias faltet die Anker-Kanten vom 2026-08-20 auf ein am 2026-08-26
   eingefrorenes Artefakt. Fuer diese sechs Tage liegt kein Wheel im Baum, die
   Zug-Gleichheit ist dort also NICHT geprueft. Einzige unbelegte Fuge der
   Leiter.

Vorgaenger `v22-b05`: Elo **1136** [1074, 1198] -- und das ist eine ANDERE Zahl als
die 1084, die hier bis zum 2026-08-31 stand. Grund ist nicht eine neue Partie,
sondern die Datenlage: b05 hing bis dahin an einer einzigen fruehgestoppten Kante
(16:34 gegen v21, n=50). Mit den beiden Tor-1-Gatings gegen b01 (52:28 und 67:33)
kommen 180 Partien dazu, das Intervall schrumpft von 228 auf 124 Punkte. Der
hv2-Lehrer liegt mit **1137** jetzt gleichauf statt 40 Punkte darueber.

**Wheel:** 79-Kanal-Build (`e91cd34`), Vertragshash `efd564d87bac2722`,
Paritaets-Hash `8c6684ff...` gemessen unveraendert.

**Was ueber den Value-Kopf gemessen ist:** relativ geheilt, im Betrag
gedaempft -- und die Daempfung ist auf v23-b01 unveraendert (0,0859 gegen
b05s 0,0886, par.11). Geschwister-Tau auf b05 **+0,338** (gegen -0,08/-0,19
der plattenblinden Netze), Mensch-Orakel-Differenz praktisch null. Kriterienweise aufgeloest ist die
Daempfung BREIT, nicht spaltenspezifisch (k1 mit 0,1747 am wenigsten
gedaempft). Daraus die Betrags-Schiene als Phase 3.

**Was ueber den Spaltenbau gemessen ist:** der Korpus wirkt (b01 baut 3x so
viele Spalten wie der Champion), das Ownership-TRAININGSGEWICHT nicht (w0
gleichauf, w2,0 signifikant darunter). Der Engpass ist die VOLLENDUNG spaet,
nicht der Plattenblick. Die Suchtiefe ist ein Regler zwischen Policy
(traegt das Spaltenwissen) und Value-Kopf: Plateau 25-100 Sims bei ~0,6
vollen Spalten gegen 0,34 ab 250 -- aber ein TAUSCH (@25 verliert 11:29,
@100 verliert 33:47 n.s.). Die Erklaerung dafuer ist OFFEN; die Deutung
"der Kopf sieht Spalten nicht" ist durch die kriterienweise Zerlegung
widerlegt.

**Erzeugungs-Knoepfe, gemessen entschieden:** implicit-Minimax alpha 0,0,
Stack-Draw-Kontrollfluss EIN, Bootstrap-Horizont 2, Seed-Positionen AUS
(Quelle plattenblind), Startkuppel Handheuristik, Vollendbarkeits-Filter AUS
(ungebaut). Vollstaendig in `PREREG_v23_window.md` par.4c.
---

## 5. OFFENE ENTSCHEIDUNGEN (Nutzer)

| Punkt | Worum es geht |
| --- | --- |
| **b04: welcher Zweig wird breiter** | Flach-Zweig `hidden_size` 512 ist ohne Bau fahrbar; Conv-Zweig `conv_channels` 48 / `conv_layers` 2 braucht zwei Flags, ein Checkpoint-Feld und eine Ableitung beim Laden -- sonst ist der Checkpoint nicht ladbar (`PREREG_capacity_sim_frontier.md` par.10) |
| ~~frozen_v3: woher die Zustaende~~ ERLEDIGT 2026-09-01 | Weg (b) gefahren: 400 frische Sockel-Partien (24,2 min), Satz und zwei Orakel-Label-Saetze gebaut (`PREREG_frozen_v3_eval_set.md` par.7-9). Quelldateien liegen im restic-Backup (`archive_pre_v24/`) |
| ~~Generatorwahl bei Gleichstand der Arme~~ | ENTSCHIEDEN 2026-09-02: dreistufig, Staerke schliesst aus, Spaltenprofil entscheidet, sonst Amtsinhaber (`docs/generation_loop.md`) |
| ~~Loeschfreigaben~~ ERLEDIGT 2026-09-01 | `data/onpolicy_v22-b05/` und `-b06/` auf Nutzer-Freigabe geloescht (je 31 Dateien, 32 + 34 MB). Vorher geprueft: KEINE Fenster- oder Traegerdatei verweist darauf. Die Preregs `heuristic_v2_long_rows` (DAgger-Runden) und `v23_window` zitieren sie im TEXT -- die Herleitungen bleiben lesbar, die Rohpartien sind weg |
| **Messartefakte tracked?** | `evaluations/artifacts/` ist ungetrackt; Preregs zitieren die JSONs als Beleg, ein frischer Klon hat sie nicht. Zurueckdrehen: `.gitignore`-Zeile raus, `git add -f` |
| **Push** | NIE ohne ausdrueckliche Anweisung; der Ahead-Stand wird im CHAT gemeldet, nicht hier gefuehrt |

---

## 6. OFFENE STRAENGE -- abgeglichen mit dem Prereg-Index (2026-08-31, nachgefuehrt 2026-09-01)

Der Index zaehlt (Stand 2026-09-01 abends, aus dem Generator) **20 OFFEN, 77 ENTSCHIEDEN, 8 UEBERHOLT** (`search_depth_column_optimum` ist wieder OFFEN, `frozen_v3_eval_set` und `v23_reachability_recheck` sind ENTSCHIEDEN)****.
Koepfe, die gegen ihren eigenen Koerper standen, sind an drei Tagen berichtigt
worden: am 2026-08-31 `cache_build_time` und `v23_reachability_recheck`, am
2026-09-01 frueh `policy_surprise_weighting`, `cache_build_time` (Hebel 3
hat einen Nutzniesser) und `r5_solver_split`, am 2026-09-01 abends bei der
Pruefung aller geaenderten Preregs `prior_blind_spot` (Kopf behauptete die
widerlegte Erklaerung), `heuristic_v2_long_rows` (Erzeugung "laeuft"),
`v23_window` (Arm-Frage offen), `search_depth_column_optimum` (jetzt OFFEN,
Stufe 4), `capacity_sim_frontier`, `reanalyze_label_depth`,
`policy_surprise_weighting` (Kennzahlen).

**Am laufenden Strang, mit Platz im Fahrplan:**

| Prereg | Wo es haengt |
| --- | --- |
| ~~`v23_window`~~ | ENTSCHIEDEN: Fenster gebaut, alle Tore und alle Arme gemessen |
| `capacity_sim_frontier` | Warm gegen Kalt einfaktoriell belegt (b06, par.14b: 0,18 Spalten, 65:95); b04 wartet auf den Zweig-Entscheid (Abschnitt 5) |
| ~~`policy_surprise_weighting`~~ | ENTSCHIEDEN 2026-09-01: b03 traegt nicht (Orakel Gleichstand, Arena 75:85) |
| `reanalyze_label_depth` | ENTSCHIEDEN 2026-09-03 (par.A5): Lehrer-Relabel b05 Nullbefund (par.A3), Reanalyze b07 keine Staerke und weniger Spalten -- b01 bleibt Generator; Teil B ohne Verbraucher bei lambda 1,0 |
| ~~`r5_solver_split`~~ | Teil B war Phase 3 -- GESCHLOSSEN ohne Bau (2026-09-01) |
| ~~`v23_reachability_recheck`~~ | ENTSCHIEDEN 2026-09-01: 14,64 Prozent tot-kartiert gegen 13,89 beim Vorgaenger, Stufe 1 wird NICHT eroeffnet; Quelldateien im restic-Backup |
| ~~`search_depth_column_optimum`~~ | ENTSCHIEDEN 2026-09-02: Stufe 4 komplett (par.6b, par.7); Tiefen-Delle beschrieben, nicht behoben |
| `special_tile_yield` | Kanaele 77/78 gebaut, ihre Wirkung nie isoliert |
| `cache_build_time` | Hebel (3) hat seit 2026-09-01 einen Nutzniesser: **4,98 h** einkerniges Zusammenfuegen bei neuer Fenster-Zusammensetzung (par.11). Die vermisste serielle Vollreferenz liegt damit auch vor |
| `frozen_v3_eval_set` | ENTSCHIEDEN und GEBAUT 2026-09-01 (Satz 1.800 Zustaende, Orakel aus b01 und v21, Zirkularitaet belegt, par.7-9). Nachgetragen: die Bruecke gilt nur fuer Runden 1-4; Quelldateien im restic-Backup; Artefakte ohne `laufzeit`-Block |
| `geometric_envelope` | K3 GEBAUT 2026-09-03 (par.8.2/8.3, Anker und Paritaet GRUEN), Messung nach par.8.4 offen; par.8.6 (Value-Anteil im Tiling, Vorpruefung bestanden) wartet auf den Nutzer |

**Registriert, nicht eingetaktet** (jeder Bau braucht vorher eine
Registrierung): `plate_policy_supervision`, `saturating_score_utility`,
`risk_sensitive_leaf_utility`, `uvfa_plate_regime`,
`uncertainty_guided_selfplay`, `start_position_seeding` (Dosis-Folgearm),
`start_dome_choice` (Stufe 0, Wiedervorlage Generation 2),
`round_transition_search_sampling` (Kostentor zuerst),
`stack_draw_reservation_rule` (Default AUS steht),
`stack_top_feature`, `chance_nodes` (Teil B1/A1 geparkt),
`floor_shaping_scale`, `rust_data_layer` (Registrierung, kein Auftrag).

**OHNE PREREG, nur Merkposten -- und darum beim Index-Abgleich durchgefallen
(berichtigt 2026-08-31):** die Neufassung hat Abschnitt 5 aus dem
Prereg-Index gebaut, und damit faellt per Konstruktion alles heraus, was
offen ist, aber keine Prereg hat. Wieder aufgenommen:

* **Einhuellende / geometrisches Gelaender: seit 2026-08-31 REGISTRIERT**
  als `PREREG_geometric_envelope.md` (Nutzer-Auftrag) -- damit ist der
  Merkposten von 2026-08-24 abgeloest. Steht in Abschnitt 5 oben bei den
  Straengen am laufenden Fahrplan.
* **#31 / #38 / #39**: geparkt, Arbeitskreis "Spaeter", Beschreibungen im
  Archiv.

Wer Abschnitt 5 kuenftig aus dem Index erzeugt, traegt diese Liste HIER
nach -- der Index kennt nur, was eine Datei hat.

**Verschoben, nicht verworfen:** Arm K (Bootstrap-Kohaerenz,
`PREREG_heuristic_v2_long_rows.md` par.3b.3/3b.3a) -- gebaut, Default aus,
ausloeserbasiert. Er korrigiert einen VERSATZ, das gemessene Problem ist eine
STEIGUNG; seine drei benannten Nutzniesser sind ungebaut; und er ist der
einzige Arm, der alle Cache-Bloecke entwertet.

---

## 7. MERKLISTE CODEPFLEGE (Audit 2026-08-27, bewusst verschoben)

**Naechstes Build-Fenster** (brauchen cargo, Paritaets-Gate): sechs Dialekte
fuer "ist dieser Bool-Knopf an?" (Befund 4); drei stille Env-Verschlucker
(13-15); Value-Spread-Pfad verkleinert den Pool still (16); toter Zweitpfad
`board.rs:184-220` mit irrefuehrenden Spaltennamen (19).

**Nach dem v23-Training:** ONNX-Paritaetspruefung nie fertiggebaut (18);
Kanalzahl als Hand-Literal im Fenster-Key (5, NICHT vor dem Training);
viermal dasselbe 95%-KI mit Entartungen (20); sieben Eigenaufloesungen von
`champion.txt`, sechs Tool-Stellen offen plus `dist/mosaic_release.spec:46`
packt eine geloeschte ONNX (21); `MosaicDataset.__init__` mit 998 Zeilen
(22); `offline_diagnosis.py` rechnet ein historisches Value-Ziel (6).

Fundstellen im Audit-Bericht; Details im Archiv-Kapitel.

---

## 8. STRUKTURBEFUNDE, die weitergelten

- **Der Champion vollendet keine Spalten**, und der Grund ist Verteilung,
  nicht Versorgung: eine volle Spalte kostet 21 Zellen, das Netz verbraucht
  42,7 und truege gleichverteilt 2,03 Spalten statt 0,10.
- **Die Dreiecksform ist die MACHBARKEITSHUELLE**, keine aesthetische Wahl:
  erlaubt ist `r + c <= 5`, also dieselben 21 Zellen.
- **Eine volle Rasterzeile ist ohne Spezialfliese unmoeglich** -- sie wird nur
  von ihrer Musterreihe gespeist, und die schliesst hoechstens einmal je Runde
  ab. Spalten haben das Problem nicht.
- **Der Durchbruch kam vom DRAFTING, nicht vom Routing** (Split-Test, je 160
  gepaarte Partien): Huelle nur im Drafting 0,756 gegen 0,044 (t 10,29),
  Huelle nur im Routing 0,113 gegen 0,113. Die Luecke zur Summe ist eine
  Wechselwirkung -- das Routing kann nur einsortieren, was das Drafting geholt
  hat.
- **Erste unkontaminierte Referenz:** Mensch-gegen-Netz in `static/log/` --
  der Mensch schliesst 1,80 volle Spalten je Partie gegen 0,10 des Netzes,
  bei GLEICHEN Platzierungspunkten. Der Vorsprung sitzt bei den
  Spezialfliesen; der Mensch tauscht kurze Reihen gegen lange.
- **Chip-Allokation, nicht Chip-Volumen:** Mensch 0,8 Reihe-6-Chip-
  Abschluesse je Partie, v21 0,1. Kosten-gewichtete Huelle Mensch 0,86,
  Lehrer 0,68 (berichtigt 2026-09-03: die zweite Huelle war falsch
  gespiegelt, `heuristic_v2_long_rows` par.3b.14); Netz-Werte 0,54-0,62
  stammen noch aus der falschen Rechnung und sind vermutlich zu niedrig.
- **Blindzieh-Regel:** bei Wertungsplatte 6 laeuft die gebaute Stopp-Regel das
  Punktekonto leer (58-66 Prozent der Serien enden bei 0). Spaltenbau behebt
  das NICHT -- k1 zahlt quadratisch, das Spezialfeld-Defizit kostet linear -3
  je Feld.
- **Eine Herleitung aus dem Code ist eine Hypothese, kein Befund.** Am
  2026-08-25 lagen vier davon im Vorzeichen falsch.
