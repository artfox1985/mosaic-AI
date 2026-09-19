# Mosaic-AI – Status & Fahrplan

**Dieses Dokument traegt NUR Aktuelles und Offenes.** Neufassung vom 2026-09-18
(Generationswechsel v29 -> v30, Skill Schritt 6); der vollstaendige Stand davor liegt in
`../archive/history.md`, Kapitel **"Vollstaendiger STATUS-Stand vom 2026-09-18 (vor der
Neufassung)"**, der **"Generationsbericht v29 (2026-09-13 bis 2026-09-18)"** als naechstes
Kapitel dort, die Generationsberichte v24 bis v27 ebenfalls.

**Pflegeregel:** wer einen Befund erzeugt, traegt ihn im selben Zug hier nach und prueft, ob
ein anderer Abschnitt dadurch falsch wird. Wer einen Strang abschliesst, schiebt die
Herleitung ins Archiv und laesst hier eine Zeile mit Verweis stehen. Wer ein Ergebnis
registriert, greppt nach seinen KONSUMENTEN (CLAUDE.md, Rueckwaerts-Pruefung).

**Dauerhaftes Prozesswissen steht NICHT hier**, sondern in `../docs/`: `generation_loop.md`,
`promotion_checklist.md`, `generation_naming.md`, `working_rules.md`, `pitfalls.md`,
`measured_runtimes.md`, `architecture_reference.md`, `engine_manual.md`.

---

## 1. WAS GERADE LAEUFT

**UEBERGABE 2026-09-18, 18:10 (Sitzungswechsel per /mosaic-handover; Anlass: Kontext der alten Sitzung voll,
die v30-Erzeugung laeuft bis in die Nacht).** Generationswechsel v29 -> v30 nach Skill DURCH bis Schritt 7:
Champion v29-b09 promoviert und eingefroren (Abschnitt 2), Generator v29-b11 abgenommen (10.17), Snapshot
`af420224`, Loeschungen nach Freigabe ausgefuehrt und committet (`1d619a0d`), STATUS neu gefasst, Preregs
nachgezogen (4 OFFEN, Abschnitt 5). Push-Stand 0 um 18:10 (der Nutzer hat gepusht). Unkommittiert bei der
Uebergabe: nur die Prereg-Kopf-Schliessungen, `docs/knobs.md`, `docs/pitfalls.md` (werden mit der Uebergabe committet).

### LAEUFT (Stand 18:10, gezaehlt)

1. **Self-Play Sockel `v29-b11-policy`** (verwaist, Wrapper am 14:53 bewusst beendet; python PID 27628, Start
   14:50:04, `--games 4000 --sims 100 --seed 20260930`, Spec `models/v30_generation.spec.json`,
   `MOSAIC_STACK_DRAW_RESEARCH=1`): **227 von 400 Dateien** in `data/selfplay_v29-b11-policy_*.pkl` (je 10 Partien),
   rund 5,3 s je Partie neben dem Waechter, **Ende gegen 20:45**. Manifest
   `data/manifest_v29-b11-policy_20260918_145006.json` (traegt am Ende den laufzeit-Block). Liest: Modell
   `models/alphazero_v29-b11.onnx`, die Spec, das installierte Wheel -- nichts davon anfassen.
2. **Rest-Kette `tools/night_v30_generate_rest.sh`** (bash PID 28120, Umgebung `MOSAIC_V30_GENERATOR=models/alphazero_v29-b11.onnx
   MOSAIC_V30_GEN_NAME=v29-b11`): wartet auf das Ende des Sockels (Prozessfilter `self_play.py`), prueft den ersten
   Sockel-Record (gzip), faehrt dann **Klasse 2 `v29-b11-value-tempc`** (Seed 20260931, 4.000 Partien) und
   **Klasse 3 `v29-b11-value-excursion`** (Seed 20260932); Erwartung je Klasse 3-4 h (v28: 3,2 h ohne Nebenlast),
   **Ende gegen 03:00-05:00**. Ihre Ausgabe steht in der Hintergrundaufgabe der ALTEN Sitzung; die neue Sitzung
   zaehlt Dateien: `ls data | grep -c '^selfplay_v29-b11-value-tempc_'` (Ziel 400) und `...-excursion_` (Ziel 401).
3. **Cache-Waechter** (`tools/build_cache_incremental.py --watch`, PIDs 32460/38800, 3 Worker, Umgebung
   `MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_FEATURES_FROM_RUST=1`): 2.629 Bloecke unter dem 888er-Schluessel
   gebaut, baut jede neue Datei nach; laeuft bis `--leerlauf-abbruch` oder Stopp. Erlaubte Nebenlast neben der
   Erzeugung (Kopf von `tools/night_v30_generate.sh`).

### FORTSCHRITT DER ERZEUGUNG (neue Sitzung, gezaehlt; fortlaufend nachgetragen)

**Sitzung uebernommen 2026-09-18, 18:15.** Prozessliste geprueft (`Get-CimInstance Win32_Process`): alle drei
Prozesse der Uebergabe laufen -- Sockel `self_play.py` PID 27628/31704 (Start 14:50:04), Rest-Kette
`night_v30_generate_rest.sh` PID 28120, Cache-Waechter `build_cache_incremental.py` PID 32460/38800. Beobachter
`tools/watch_v30_generation.sh` (neu, reine `ls`-Abfrage je 120 s, Prozess-Check nur bei Stillstand) laeuft je
Klasse; Abbruchgruende: Ziel erreicht plus laufzeit-Block (0), Stillstand 30 min (10), Prozess weg bei
unvollstaendiger Klasse (11).

**Geprueft an der Rest-Kette** (`tools/night_v30_generate_rest.sh`, Z.72-84): ihre Wiedervorlage liest den ersten
Sockel-Record mit `gzip.open` und faellt nur bei `OSError` auf `open` zurueck -- die Falle vom 2026-09-18
(`docs/pitfalls.md`) ist dort repariert, der Sockel wird von der Pruefung nicht getoetet.

**Bezugswert Tor 2a liegt bereits als Artefakt vor** (`evaluations/artifacts/corpus_sanity_v28-b02-policy.json`,
gelesen 2026-09-18): `sp_voll` 0,84275 (+-0,01670), n = 8.000 Seiten, Grundmenge `selfplay_v28-b02-policy_*`
(400 Dateien = 4.000 Partien), Einheit volle Spalten je Seite. Die Bezugsklasse muss also NICHT neu gefahren
werden; das spart rund 4,5 min Nebenlast neben der Erzeugung.

**Frage des Nutzers 18:35 ("kannst den validation cache auch schon parallel fahren?") -- geprueft, Antwort NEIN,
aber der teure Teil LAEUFT bereits parallel:**

* **Die Datei-Bloecke sind fensterunabhaengig und liegen vollstaendig.** `per_file_cache_key` kennt bewusst KEINE
  Dateiliste und keinen Split (`tools/build_cache_incremental.py` Z.111-124, `corpus_dataset.py` Z.381-383).
  Gezaehlt 18:34: **2.664 Bloecke zu 2.664 Korpusdateien** in `data/`, also aufgeschlossen; 41 neue Bloecke in den
  letzten 30 min, das ist das Tempo der Erzeugung. Stichprobe unter dem AKTUELLEN Schluessel (888, Formel
  `a2phantom-20260912`, 2d, nortv) neu gerechnet: **150 von 150 Bloecken liegen** (je 30 aus `v27-b01-policy`,
  `v27-b01-value-excursion`, `v28-b02-policy`, `v28-b02-value-tempc`, `v29-b11-policy`). Schritt 5 der Kette
  (Blockbau) faellt damit weitgehend weg.
* **Monolith und Val-Cache haengen dagegen an der VOLLSTAENDIGEN Dateiliste.** `window_cache_key(data_dir, files,
  ...)` hasht die Liste (`corpus_dataset.py` Z.366-385); der Val-Split zieht ausserdem aus dem Pool
  `^selfplay_v29-` (`train.py` Z.1401-1440), und zwei der drei Klassen dieses Pools existieren noch nicht. Ein
  jetzt gebauter Cache traegt einen anderen Schluessel und waere wertlos. Nach der Erzeugung bleiben Split
  (Minuten) und Monolith-Merge aus liegenden Bloecken (gemessen 827 s, Abschnitt 3).
* **Nebenbefund, VORLAGE an den Nutzer:** die Kette merged nur den TRAININGSANTEIL (`night_v30_chain.sh` Z.253-257,
  `--merge-out "$CACHE"`). Der Val-Anteil (rund 147 Dateien) wird von `train.py` als eigenes `MosaicDataset` ohne
  `cache_file` gebaut und dabei NEU kodiert, obwohl seine Bloecke liegen. Ein zusaetzlicher Merge des
  Val-Anteils unter seinen eigenen Fenster-Schluessel waere ein Sekunden-Schritt; die Ersparnis ist UNGEMESSEN.

| Zeit | policy (Ziel 400) | value-tempc (Ziel 400) | value-excursion (Ziel 401) |
| --- | --- | --- | --- |
| 18:14 | 232 | 0 | 0 |
| 20:07 | **400 FERTIG** (18.984,2 s, 4,746 s je Partie) | 0 | 0 |
| 00:41 | 400 | **400 FERTIG** (16.183,5 s, 4,046 s je Partie) | 0, Klasse 3 laeuft an |
| 04:46 | 400 | 400 | **401 FERTIG** (14.744,0 s, 3,680 s je Identitaet) |

**ERZEUGUNG KOMPLETT 2026-09-19, 04:46.** 1.201 Dateien, zusammen **49.911,7 s = 13,86 h** (14:50 bis 04:46, durchgehend mit Cache-Waechter daneben); gegen v28 +39,7 Prozent, Planungsannahme 10,5-14 h am oberen Rand getroffen. Alle drei `laufzeit`-Bloecke stehen in ihren Manifesten und in `../docs/measured_runtimes.md` (Abschnitt Generation v30). Die Kette `night_v30_chain.sh` laeuft seit 2026-09-18 23:17 und uebernimmt selbsttaetig.

**Tor 0 der beiden Value-Klassen faehrt die KETTE selbst** (`night_v30_chain.sh` Schritt 1, alle vier
Klassen); ein zweiter Lauf von Hand waere doppelte Nebenlast ohne Erkenntnisgewinn -- Tor 2a ist nur auf
der Policy-Klasse definiert und seit 20:15 gruen.

**Klasse 1 durch, beide Tore gruen** (Belege und alle sechs Kennzahlen in `PREREG_v30_window.md` par.9):
Tor 2a `sp_voll` **0,90087 (+-0,01700)** gegen den Bezug **0,84275 (+-0,01670)**, n = 8.000 Seiten je Klasse,
Einheit volle Spalten je Seite, beide bei 100 Sims erzeugt. Der Generator baut mehr Spalten, nimmt weniger
Strafsteine (-0,295) und holt +1,62 Punkte je Seite; volle Reihen gehen leicht zurueck (-0,0158). Kein
Staerkebeleg (Self-Play, Margin per Konstruktion 0) -- das entscheidet Tor 1.

**Kosten der Erzeugung, gemessen** (Grundmenge Policy-Klasse einer vollen Erzeugung, 4.000 Partien @100,
threads 11, Einheit s je Partie): v28-Erzeugung 3,183 -> v29-Erzeugung 3,943 -> **v30-Erzeugung 4,746**.
Das sind **+49,1 Prozent** gegen die v28-Linie und **+20,4 Prozent** gegen die v29-Linie; die Stichprobe hatte
+25 Prozent geschaetzt. **Beide Lesarten reissen die 15-Prozent-Schwelle aus Abschnitt 6 Punkt 2** -- die
v31-Wiedervorlage des Budget-Knopfs ist faellig, die Bezugswahl aendert daran nichts. Eingetragen in
`../docs/measured_runtimes.md` (neuer Abschnitt "Generation v30") samt Warnung vor der Namensfalle:
Manifeste heissen nach dem GENERATOR, `manifest_v28-b02-*` ist die v29-Erzeugung.

### ERSTE AUFGABE DER NEUEN SITZUNG, in dieser Reihenfolge

1. **WATCHER auf die Erzeugung**, nichts sonst mit Rechenlast: Bedingung "400 policy-Dateien UND laufzeit-Block im
   Manifest", dann "400 tempc", dann "401 excursion UND Rest-Kette-Prozess weg". Stillstand = keine neue Datei in
   30 min bei laufendem Prozess -> Nutzer informieren, nicht eingreifen. Zwischenstaende hier in Abschnitt 1
   nachtragen (Dateizahl, Uhrzeit).
2. **Nach jeder fertigen Klasse Tor 0 / Tor 2a** (`tools/corpus_sanity_check.py`, Form und Bezugswerte in
   `PREREG_v30_window.md` par.3; Bezug `sp_voll` 0,843 aus v29, Betriebsart-Hinweis dort). Ergebnis in
   `PREREG_v30_window.md` par.9 (neu anlegen) und hier. Reisst Tor 2a: Vorlage an den Nutzer mit beiden Zahlen,
   keine stille Fortsetzung (par.8 Punkt 5).
3. **Nach dem Ende der Erzeugung** (alle drei Klassen, Waechter fertig, Maschine frei per Prozessliste): dem
   Nutzer den Start von `tools/night_v30_chain.sh` vorlegen (Freigabe des Kettenstarts ist `PREREG_v30_window.md`
   par.8 Punkt 4; die Erzeugung selbst war freigegeben, die Kette noch nicht ausdruecklich). Die Kette baut
   Traeger-Manifest v30, `data/window_v30.txt` (v29-b11 neu, v28-b02, v27-b01; Pinning `MOSAIC_DATA_EXCLUDE` fuer
   `selfplay_v29-b11-probe_*`), Bloecke/Monolith unter 888, **Training v30-b01 KALT** (Rezept par.6, rund 2,3 h),
   Tor 1 gegen `models/alphazero_v29-b09_brierbest.onnx` (Seeds 20261300/20261301, je 200 Paare, rund 3,5 h mit
   den neuen Knoten). Danach: Manifest-Diff, Netz-Gesundheit (Spaltennormen 0..755 / 755..794 / 794..884 /
   884..888 und der 414er-Policy-Kopf), sechs Standard-Kennzahlen, Verdikt nach par.3 (Marge 5 Prozentpunkte gegen
   b09; Rueckfall 1 Afterburner, Rueckfall 2 Warmstart von b09, Abschnitt 4).
4. **Registrieren**: Laufzeiten der Erzeugung aus den drei Manifesten nach `docs/measured_runtimes.md`
   (Planungsgroesse hier Abschnitt 3), Prereg-Kopf `PREREG_v30_window.md` im selben Zug,
   `python tools/generate_prereg_index.py`, dann Commit (nicht pushen).

### FREIGABEN UND VERBOTE (woertlich, unveraendert gueltig)

* Nutzer 2026-09-17: *"du hast auch die freigabe mit den self plays fuer v30 loszulegen"* -- die Erzeugung laeuft;
  der Start der Trainingskette ist NICHT ausdruecklich freigegeben (vorlegen).
* Nutzer 2026-09-18: *"Loeschfreigabe erteilt"* -- ausgefuehrt und verbraucht; jede weitere Loeschung braucht
  restic-Beleg UND neue pfadgenaue Freigabe (Kandidat spaeter: `models/frozen_champions/v27-b01` nach der
  v30-Promotion).
* Kein Push ohne Anweisung. Kein Commit waehrend eines Wanduhr-Messlaufs (Kostentor, Tor 1); neben Self-Play
  und Training ist der Sekunden-Hook hingenommen (Praezedenz 15:16).
* Messungen exklusiv; GPU-Training plus EIN CPU-Auftrag erlaubt; Builds zaehlen als Last. Ketten als DATEI
  starten, gehaertete Warteschleife, keine Pipes hinter langen Laeufen.
* Keine neuen Preregs, keine neuen Netzkoepfe. Arme nur aus offenen Preregs, Aufnahme ins Rezept per
  Nutzer-Entscheid. Nie den Projektordner verlassen. Laufzeiten ins Artefakt; sechs Standard-Kennzahlen.
* Nie committen: `player_profiles.json`, `player_profiles.json.bak`.

### OFFENE NUTZER-ENTSCHEIDE (Fundstellen in Abschnitt 6)

Start der Trainingskette v30 (par.8 Punkt 4); zweiter Arm `v30-b02` zur Zerlegung Kaltstart/Warmstart (par.8
Punkt 2, par.4 laesst einen Arm zu); Budget-Knopf fuer die Hilfsknoten als v31-Wiedervorlage (Kostentor +35
Prozent, 10.14); Vorgehen bei Tor-2a-Riss; Loeschung `frozen_champions/v27-b01` nach der v30-Promotion.

## 2. CHAMPION UND LEITER

**Champion laut `models/champion.txt`: `v29-b09_brierbest`** (Promotion 2026-09-18, 14:32;
Nutzer-Entscheid 10:05 "Weiter mit a und b09"; `minimal_strength_core` 10.15/10.18).
**Elo 1366 [1329; 1408]** aus 1.100 Partien im LEITERSEGMENT 2 (Anker `hv4_anchor` fix 1000,
Block-Bootstrap; Stand 2026-09-18, 09:40). Seine drei Aufhaengungen (10.13):

| Kante | Ergebnis |
| --- | --- |
| Gating gegen `v28-b02` (2 Seeds a 200 Paare, 800 Partien) | 423:377 = 52,9 Prozent |
| Anker `hv4_anchor` @150 (150 Partien ohne Stopp) | 128:22 = 85,3 Prozent |
| Champion-2 gegen `v27-b01` (150 Partien ohne Stopp) | 90:60 = 60,0 Prozent |

Eingefroren unter `models/frozen_champions/v29-b09/` (Wheel 414/888, sha256 `da24f156...`,
Golden-Probe 10/10, Referee-Selbsttest gruen, Handshake `6ef829e564c58bd5`).
Anzeige-Kalibrierung `_DISPLAY_CAL_A/_B` -0,0513 / 0,6488 (frozen_v3, Brier 0,255, in
`server.py` eingetragen), sigma/Prior-Balance Median 1,83 (unter 3 -- die c_visit/c_scale-Familie
bleibt geschlossen), Netz-Paritaets-Fixture `01e627ef5e520619`.

**Vorgaenger und Champion-2-Kante: `v28-b02_brierbest`** (Promotion 2026-09-12),
Elo 1349 [1315; 1385] aus 3.950 Partien.

**LEITER, Stand 2026-09-18 09:40** (Segment 2, `elo_history.csv`; Block-Bootstrap):

| Modell | Elo | KI95 | Spiele | Frueh-Stopp-Kanten |
| --- | --- | --- | --- | --- |
| v29-b03@400 | 1382 | [1342; 1431] | 640 | 3 von 4 (nach oben verzerrt) |
| **v29-b09@400 (Champion)** | **1366** | **[1329; 1408]** | **1.100** | 0 von 4 |
| v29-b07@400 | 1357 | [1318; 1401] | 1.100 | 0 von 4 |
| v28-b02@400 | 1349 | [1315; 1385] | 3.950 | 6 von 17 |
| v27-b01@400 | 1308 | [1272; 1344] | 1.580 | |

Alle Intervalle ueberlappen; die Leiter trennt b07 und b09 nicht. b03 fuehrt nominell, aber
drei seiner vier Kanten sind Frueh-Stopps.

**Generator `v29-b11`** (b09 mit auf 414 gepolstertem Policy-Kopf, ohne Trainingsschritt).
Seine Kante **212:138 gegen v29-b09** ist am 2026-09-18 in `elo_history.csv` eingetragen
(Segment 2, Spec `v30_generation.spec.json`); ein Elo-WERT fuer b11 ist damit noch NICHT
gerechnet -- der Report von 09:40 liegt vor dieser Zeile. Wer ihn braucht, faehrt
`tools/elo_tracker.py report` (Rechenlast, nicht neben einer Messung).

**Eingefrorene Artefakte:** `frozen_champions/v29-b09` (amtierend) und `v28-b02` (Vorgaenger,
Champion-2-Kante); `frozen_heuristics/hv4_anchor` (aktiver Anker), `hv2_generator` und
`hv3_generator` (Sprossen, hv3 ist die Anfaenger-Stufe); `models/restored_v22` (Leiterknoten
v22-b05). `frozen_champions/v27-b01` liegt noch im Baum und ist nach der Zwei-Champion-Regel
Loeschkandidat (Abschnitt 6).

## 3. LAUFZEITEN (gemessen, Planungsgroessen; Details in `../docs/measured_runtimes.md`)

| Aufbau | Dauer | Anmerkung |
| --- | --- | --- |
| Erzeugung 3 x 4.000 Partien @100, threads 11 | 9,92 h (v28) / 12,8 h (v29) | v29 unter Nebenlast; fuer v30 mit 888/414 **ANNAHME 10,5-14 h** |
| Erzeugungskosten je Partie @100 aus der b11-Probe | 3,98 s gegen 3,18 s (v28) = **+25 Prozent** | ANNAHME aus 20 Partien (10.17) |
| Blockbau 2.800 Dateien plus Merge, 6 Worker, INPUT_SIZE 794 | 1.964 s = 32,7 min | erste Kette mit Formel-Version im Schluessel |
| dito unter 884 | 2.144 s = 35,7 min | +9,2 Prozent gegen 794 (18.9) |
| dito unter 888 | **UNGEMESSEN** | ANNAHME: wie 884, der Eingang waechst um 4 Werte |
| Monolith-Merge liegender Bloecke (kein Blockbau) | 827 s | b09-Kette |
| Training Warmstart 12 Epochen, 4,54 Mio Samples | 57 min exklusiv / 72-113 min gebremst | b06 / b09, b08, b07 |
| Training KALTSTART 12 Epochen | **8.164 s = 2,27 h** (v23-b06, 4,72 Mio) | fuer 888 **ANNAHME 2,3-2,6 h** |
| Tor 1 je Seed, 200 Paare @400, 10 Threads, mit Logs | 4.607 s (794) / 4.912-5.090 s (884) | 11,5 bzw. 12,3-12,7 s je Partie, exklusiv |
| dito mit 414er-Netzen | **ANNAHME rund 105-110 min** | +35 Prozent aus dem Kostentor (10.14) |
| Champion-Kanten je Kandidat (Gating 2 Seeds, Anker n=150, Champion-2 n=150) | **rund 3,7 h** | 2 x rund 4.800 s + 1.250-1.280 s + 2.340-2.390 s |
| Kostentor 2 x 20 Paare @400 | rund 22 min | 414/888-Wheel, 09:33-09:55 |
| Promotion nach Checkliste (Punkte 1, 5b-5d, 7 inkl. Golden-Probe 22 min) | **38 min** | 10.18 |
| Voller Build: Lib-Tests, `--no-run`, Fixtures, Wheel | rund 5 min | 146 s + 60 s + 72 s (2026-09-17) |
| Anker-Drift / Anker-Konservierung | 22,4 s / 16,6 s | je 1.763 Schritte |
| Tagesschnappschuss restic plus check | 6-7 s | |

## 4. SPEC UND REZEPT

**Champion-Spec** `models/frozen_champions/v29-b09/spec.json` (= die bisherige Champion-Spec):
`envelope_projection_mode` 1, `envelope_search_c` 1,0, `envelope_flush_w` 0,0,
`envelope_hull_form` 2, `special_row6_w` 1,0, `score_utility_b` 20,0,
Profil 1/0,92/0,67/0,33/0, `heuristik_variante` hv1.

**Erzeugungs-Spec `models/v30_generation.spec.json`** = `start_by_search_on.spec.json` plus
`return_order_mode: 1` (am Dateiinhalt geprueft 2026-09-18). **Befund dazu:**
`return_order_mode 1` ist unter `MOSAIC_STACK_DRAW_RESEARCH=1` WIRKUNGSLOS -- der Aufloeser
laeuft nie; die Abdeckung der Rueckgabe-Reihenfolge kommt in der Erzeugung vom Suchknoten
(`dome_return_order` 12.9). Das Feld bleibt als Rueckfall fuer 406er-Seiten in Arenen.

**Engine-Stand:** INPUT_SIZE **888**, NUM_ACTIONS **414**, Vertragshash `6ef829e564c58bd5`
(Kompilat 2026-09-18 09:21-09:31, 702 Tests gruen, beide Fixtures bewusst neu;
`moon_stack_order` 12.11). Neue Suchknoten: Mond 406-410, Rueckgabe 411-413; Slot und Rotation
entscheidet seit 12.9 die Schleife als eigene Knoten mit Policy-Ziel.

**v30-TRAININGSREZEPT** (vollstaendig; Befehl in `PREREG_v30_window.md` par.6): b03-Rezept mit

* `--moon-loss-weight 0` (Ausgang bleibt, Loss 0),
* `--ownership-weight 0` mit `--ownership-head-2d` (Ausgabe bleibt, Loss 0),
* OHNE `--endgame-head`, `--opp-points-head` bleibt,
* INPUT_SIZE 888, NUM_ACTIONS 414,
* **KALTSTART: kein `--load`**, Seed 20260945, 12 Epochen, lr 5e-05 cosine mit
  `--lr-t-max 12`, lambda 0,7, `--select-by-brier`, `--fast-loader`.

**Rueckfall 1:** Afterburner auf dem kalt gestarteten v30-Netz (Warmstart vom
v30-Checkpoint, DAgger-Muster v22-b05/b06, 8-11 min). **Rueckfall 2:** Warmstart von
`v29-b09`. Beide laufen NICHT automatisch (`PREREG_v30_window.md` par.3 Punkt 5).

**Belegt ist das Rezept auf dem v29-Fenster:** `v29-b09` faehrt es komplett und haelt gegen
b03 mit 416:384 von 800 (52,0 Prozent, Block-z +1,03; 10.10). Ungedeckt ist allein der
Kaltstart -- das ist die bewusst eingegangene Wette (Nutzer 2026-09-17: "dann gehen wir die
wette fuer v30 und kaltstart ein", 18.11).

## 5. PREREG-BESTAND (5 OFFEN laut Index 2026-09-18, 23:35; Ziel rund 7 weiter unterschritten)

**Nachzug 2026-09-18, 15:25 (Nutzer: "sollten jetzt nicht mehr viele offen sein"):** sieben Koepfe auf ENTSCHIEDEN
gesetzt, weil ihre Fragen mit den Entscheiden vom 17./18.09. beantwortet sind (`minimal_strength_core`,
`round_transition_search_sampling`, `v29_window`, `special_tile_yield`, `moon_stack_order`, `dome_return_order`,
`stack_top_feature`; Wirkungen, die erst im v30-/v31-Training messbar sind, verweisen auf die jeweilige
Fenster-Prereg). **OFFEN sind 5:** `v30_window` (aktiv), `code_cleanup_closeout` (Stufen 2/3 nach v30),
`difficulty_levels` (Leiter auf den Schluss-Champion vertagt), `claude_play_interface` (P1 vertagt)
und **wieder OFFEN seit 2026-09-18, 23:30: `dome_return_order`** -- der Streu-Knopf ist in der
Erzeugung wirkungslos, der Bauplan fuers v31-Self-Play steht in ihrem Abschnitt 12.12
(Nutzer-Auftrag 23:20: *"dann schau dass wir es ins self play fuer v31 bekommen"*). Stand des
Index danach: **121 Dateien = 5 OFFEN + 104 ENTSCHIEDEN + 12 UEBERHOLT**.

`python tools/generate_prereg_index.py` haelt `evaluations/PREREG_INDEX.md` aktuell; Stand
**121 Dateien = 11 OFFEN + 98 ENTSCHIEDEN + 12 UEBERHOLT**.

| Prereg | Was noch aussteht |
| --- | --- |
| `v30_window` | der laufende Zyklus selbst |
| `v29_window` | par.6d Punkt 4 (Value-Kopf-Verlaesslichkeit: rho je Runde und Platt-Brier b03 gegen b01) |
| `minimal_strength_core` | Strang A abgeschlossen (10.6). Offen ist Strang B (Trace `DrawStackPeek` vor jedem Bau, par.3); Strang C ist mit dem Negativbefund zu Variante B gegenstandslos (10.2), Strang D ist Spaetabschluss unter `code_cleanup_closeout` (par.5) |
| `round_transition_search_sampling` | Variante C ist im Rezept, B negativ; Wirkung der Encoder-Seite misst erst v30 |
| `moon_stack_order` | Weg A ist gebaut; seine Wirkung ist erst im v31-Training messbar (12.6) |
| `dome_return_order` | Korpus mit Streuung und die Abnahme des Rueckgabe-Knotens, beides mit der v30-Erzeugung |
| `stack_top_feature` | P.12 wirkt erst ab v30; dazu die zwei Regelbefunde par.16/16a (Abschnitt 6) |
| `special_tile_yield` | K6 geschlossen (13.7/13.8); offen bleibt der Posten selbst |
| `difficulty_levels` | ganze Leiter auf v30 vertagt (par.13) |
| `claude_play_interface` | Partien g08-g10, entschieden als Abschluss mit dem Schlussmodell |
| `code_cleanup_closeout` | Stufen 2 und 3, nach der v30-Promotion |

**Seit der letzten Zaehlung (2026-09-15: 119 Dateien, 9 OFFEN) hat sich nur die Zahl der
Dateien bewegt:** neu sind `minimal_strength_core` (2026-09-16) und `v30_window` (2026-09-18),
geschlossen wurde in diesem Zeitraum keine. Die zwei Schliessungen der Generation liegen
davor: `corpus_behaviour_audit` (2026-09-14) und `round_estimate_leaf_term` (2026-09-15).

**Nachzuziehen (Kopf-Pflege, `/mosaic-prereg`):** zwei Zeile-1-Koepfe beschreiben inzwischen
ueberholte Zustaende -- `round_transition_search_sampling` nennt die Champion-Kanten fuer b07
als offen (gemessen in `minimal_strength_core` 10.11), und `special_tile_yield` sagt, die
K6-Dosis 0,25 "laeuft" (Ergebnis in 13.8). Danach `tools/generate_prereg_index.py`.

## 6. OFFENE NUTZER-ENTSCHEIDE

1. **Loeschfreigaben des Generationswechsels** (jede Gruppe nur mit `restic find`-Beleg und
   pfadgenauer Freigabe, `feedback_never_delete_without_confirmation`). Vier Klassen, Listen
   legt der Koordinator vor:
   * **Ketten-Skripte** in `tools/`, die an v29 gebunden und abgearbeitet sind
     (`night_v29_*`, `night_champion_edges_v29.sh`, `night_v29_b09_promotion.sh`,
     `night_tiling_tiebreak_ab.sh`, `night_k6_*`); generische Werkzeuge bleiben.
   * **Korpora**: die `v26-b01`-Klassen (1.201 Dateien), die mit v30 aus der Rotation fallen
     (`PREREG_v30_window.md` par.8 Punkt 3), dazu Messkorpora und ihre Manifeste.
   * **Bloecke und Monolithe**: alle Alt-Bloecke sind seit der Formel-Version im Schluessel und
     dem Wechsel auf 888 ohnehin nicht mehr adressierbar; `tools/cache_inventory.py --orphans`
     nach der Korpus-Loeschung. h5-Dateien sind vom Backup ausgeschlossen (nachbaubar).
   * **Modelle**: `frozen_champions/v27-b01` faellt unter die Zwei-Champion-Regel
     (`feedback_keep_only_last_two_champion_artifacts`); dazu Arme ohne Rolle
     (`_best`/`_brierbest`/`.pth`/`.onnx` der v29-Arme, die nicht Champion, Generator oder
     Rueckfall sind) und liegen gebliebene `*_resume.pth`/`*.stop`. Nie: Champion,
     Vorgaenger, aktiver Anker, Generator.

2. **Budget-Knopf fuer die Hilfsknoten** (Slot, Rotation, Rueckgabe, Mond) -- z.B. 25-50
   Prozent der Sims, Praezedenz `moon_order_post_search` mit 256 Sims. **ENTSCHIEDEN, aber
   bedingt (Nutzer 2026-09-18, 20:25: "wenn es was bringt stoert mich der mehraufwand
   nicht"):** der gemessene Aufschlag der v30-Erzeugung (+20,4 Prozent gegen die v29-Linie,
   +49,1 Prozent gegen die v28-Linie, `PREREG_v30_window.md` par.9) ist als KOSTEN hingenommen;
   der Knopf wird nicht aus Kostengruenden gezogen. Die Bedingung "wenn es was bringt" ist
   damit die einzige offene Haelfte -- und sie ist in v30 konstruktionsbedingt NICHT sauber
   beantwortbar: die Knoten sind mit 40,8 Prozent Fensterabdeckung vorregistriert als
   unterbelegt, ein Nullbefund ist ausdruecklich KEIN Beleg gegen sie
   (`PREREG_v30_window.md` par.1b, `moon_stack_order` 12.6, `dome_return_order` 12.7).
   **Wiedervorlage bleibt v31**, dann aber als WIRKUNGS-Frage, nicht als Kostenfrage. Was
   heute dazu messbar ist, ist der Lernstoff-Anteil der Knoten im Korpus (Nachzaehlung aus
   par.1b, Ergebnis in par.9). **Gezaehlt am 2026-09-18, 20:35** (n = 78.917 Records aus 40 der
   400 Sockel-Dateien, Einheit Records): der **Mondknoten traegt in 11,64 Prozent** der Records
   ein Policy-Ziel, der **Rueckgabeknoten in 0,18 Prozent** (143 Entscheide in 400 Partien);
   von 9.332 Records mit einer ID >= 406 in der Maske hat NULL ein leeres Ziel. Wer den
   Budget-Knopf in v31 aufmacht, hat damit eine Trennung: fuer den Mondknoten gibt es
   Lernstoff, fuer die Rueckgabe kaum.

3. **Zerlegung Kaltstart gegen Warmstart als eigener Arm `v30-b02`**
   (`PREREG_v30_window.md` par.8 Punkt 2): Rueckfall 2 nicht als Rueckfall, sondern als
   zweiter Arm bei sonst gleichem Rezept und Fenster. Kosten rund 1,2 h Training plus
   2 x rund 105 min Tor 1. Ohne diesen Entscheid laesst par.4 genau einen Arm zu.

3a. **Rueckgabe-Exploration: der gebaute Knopf ist in dieser Erzeugung unwirksam** (Nutzer-Frage
   2026-09-18, 22:00; Belege in `PREREG_v30_window.md` par.9). `MOSAIC_RETURN_ORDER_RANDOM_P`
   sitzt im Stapelzug-Aufloeser, den `MOSAIC_STACK_DRAW_RESEARCH=1` nie betritt
   (`self_play.rs` Z.1387) -- auch p > 0 wuerde nichts aendern. Ersatz gibt es nur in der
   temperierten Klasse ueber `--action-temp 2`; Sockel und Ausflug spielen an den Knoten
   argmax (`--tau-argmax-from-move 1`, Vorrang vor der Temperatur, `self_play.rs` Z.5767).
   Weil die Suche an den Rueckgabeknoten fast unentschieden ist (Median-Anteil der staerksten
   Option 0,572 bei n = 143 Entscheiden), streut die temperierte Klasse dort trotz T = 0,2
   in rund 22 Prozent der Faelle (HERLEITUNG). **Entscheid noetig, falls mehr Streuung
   gewollt ist:** den Knopf wirksam zu machen hiesse `MOSAIC_STACK_DRAW_RESEARCH` aus, und
   damit NULL Slot-Datensaetze -- ein Tausch, kein Fix. Eine Aenderung an der dritten Klasse
   ginge nur ueber Stoppen der laufenden Kette und getrennten Start. **Nutzer 2026-09-18, 22:15:
   "das aktuelle self play kann so weiterlaufen"** -- fuer v30 erledigt. **Offen ist das
   v31-Self-Play**: drei Optionen mit Prueffundstellen in `PREREG_v30_window.md` par.9
   ("Optionen fuer das v31-Self-Play"). Kurz: (1) Streuung in den Knoten-Weg portieren, Bausteine
   liegen, ABER `policy_target_valid` muss dort anders behandelt werden als im Aufloeser, weil im
   Knoten-Weg die Aktion selbst zufaellig ist; (2) tau-argmax an den Hilfsknoten aussetzen --
   trifft auch den Sockel und damit den Policy-Traeger, ohne Not nicht zu empfehlen; (3) nichts
   aendern. Heimat des Entscheids ist die v31-Fenster-Prereg (so schon im Kopf von
   `PREREG_dome_return_order.md` vorgesehen), keine neue Prereg noetig. **ENTSCHIEDEN
   2026-09-18, 23:20 (Nutzer: "dann schau dass wir es ins self play fuer v31 bekommen"):
   Option 1 wird gebaut.** Bauplan mit vier Schritten, Zwaengen und den zwei offenen Dosis-Fragen:
   `PREREG_dome_return_order.md` 12.12. **Noch NICHTS gebaut** -- Erzeugung und v30-Kette laufen,
   ein `cargo`-Build zaehlt als Last; `corpus_dataset.py` darf ausserdem nicht angefasst werden,
   solange Cache-Waechter oder Kette laufen. **Tragender Befund fuer den Bau:**
   `policy_target_valid` taugt NICHT als Maske fuer den gestreuten Entscheid, weil beide Ketten
   `MOSAIC_IGNORE_POLICY_TARGET_VALID=1` fahren (`corpus_dataset.py` Z.1635); zu kopieren ist
   das Muster der gestreuten Startkuppel, das an einer eigenen Bedingung haengt (Z.1593-1595).
   **Dosis, Schwelle, Rundenfenster und Zweck sind NICHT offen** -- alles entschieden in
   `PREREG_dome_return_order.md` par.11b/11c (Nutzer 2026-09-18, 23:45: "diese fragen sind sicher
   nicht offen"). **Aber ihre ZAHL steht auf einer fremden Grundmenge:** die Dosis 0,0146 ist aus
   "11,07 Gelegenheiten je Partie" hergeleitet, und diese 11,07 sind MONDSTAPEL-Dreierstapel aus
   `PREREG_moon_stack_order.md` par.9b, keine Kuppelplatten. Am v30-Korpus gemessen: **0,2225
   Gelegenheiten je Partie** (n = 1.778 Stapelzuege aus 400 Partien), Faktor 50. Mit 0,0146 faellt
   die Muenze in 0,33 statt in 15 Prozent der Partien; fuer das registrierte Ziel waere p = 0,52
   noetig -- **und das war noch die Mittelwert-Rechnung.** Exakt ueber die VERTEILUNG gerechnet
   (n = 400 Partien): nur **17,75 Prozent der Partien haben ueberhaupt eine Gelegenheit**, das ist
   die Obergrenze bei p = 1; p = 0,52 ergaebe 10,29 Prozent. **Nutzer-Entscheid 2026-09-18, 23:55:
   "es bleibt bei den 15%" -> DOSIS 0,81** (`PREREG_dome_return_order.md` 12.12a). Das heisst
   zugleich: in 81 Prozent der Gelegenheiten wird gestreut. Die Rate ist verhaltensabhaengig und
   nach der v31-Erzeugung nachzurechnen.

4. **Vorgehen, wenn Tor 2a reisst** (`PREREG_v30_window.md` par.8 Punkt 5, Hypothese H4):
   nach `docs/generation_loop.md` Vorlage an den Nutzer mit beiden Zahlen, keine stille
   Fortsetzung. Die Alternative waere, den v29-Korpus weiterzufahren und v30 nur als
   Rezept-Umstellung zu trainieren.

5. **Push.** Stand 2026-09-18, 20:20 (gemessen `git rev-list --count origin/main..main`):
   **2 Commits vor `origin/main`** (der Nutzer hat um 18:10 gepusht, Stand danach 0). Kein Push ohne Anweisung; der Nutzer pusht selbst.

### Aeltere, weiterhin offene Punkte (unveraendert uebernommen)

6. **Manifest meldet Spec-Felder falsch** (geprueft 2026-09-13): `engine_config` zeigt fuer
   `envelope_search_c`, `envelope_projection_mode`, `envelope_hull_form`, `special_row6_w`
   und -- neu am 2026-09-18 gefunden -- `return_order_mode` (`lib.rs` Z.834) den Env-Default statt des
   wirksamen Spec-Werts (`lib.rs` Z.801/807/812/815 lesen `SearchConfig::from_env()`). **Kein Belegverlust** -- jedes Manifest nennt den Spec-Pfad.
   Vorschlag: Spec-Inhalt plus sha256 additiv ins Manifest. Nicht waehrend eines Laufs bauen.

7. **Sichtluecke bei den gezogenen Stapelplatten** (`stack_top_feature` par.16/16a): die
   Vorderseiten sind nach Regelauskunft erst NACH dem Aufhoeren bekannt. (a) Die Aktionsliste
   verraet sie ueber die designabhaengige Rotationsfilterung (`game.rs` Z.402) -- betrifft die
   Suche, Reparatur beruehrt `NUM_ACTIONS`. (b) `serialize.rs` Z.375-379 serialisiert sie
   sofort, die Anzeige druckt sie (`claude_play.py` Z.721), die Platzierungs-Vorschau rechnet
   damit -- betrifft den menschlichen Spieler, live eingetreten in Partie g07. Umfang und
   Prioritaet offen; beruehrt die Gueltigkeit von g02-g07.

8. **Paritaets-Tor und Alt-Records** (`rust_data_layer` par.9/par.9a): der Planes-Kanal 76
   weicht auf Records von VOR dem A2-Phantom-Fix (2026-09-12) ab, weil das Tor eine
   GESPEICHERTE gegen eine frisch gerechnete Groesse haelt. Weg (1) (Formel-Version im
   Schluessel) ist gebaut, repariert das Tor aber nicht. Offen ist, was mit dem Tor geschieht:
   gespeicherte Felder aufgeben und ueberall frisch rechnen, oder das Tor auf frische
   Zustaende beschraenken.

9. **Drei Sonden zeigen auf das geloeschte Artefakt `hv1_anchor`**
   (`anchor_referee_parity_probe.py`, `frozen_agent_referee_probe.py`,
   `frozen_worker_protocol_probe.py`). Eine Umstellung auf `hv4_anchor` braucht NEUE
   Erwartungswerte (die hartkodierten gelten fuer hv1, z. B. `scores [27, 15], steps 159`),
   also einen Lauf -- lohnt das, oder entfallen die drei als historisch?

10. **`-Deep`-Lauf der Backup-Verifikation**: `verify_backup.ps1` empfiehlt ihn vor der ersten
    Loeschung; am 2026-09-13 auf Nutzer-Entscheid nicht gefahren.

11. **Rahmen, offen gehalten 2026-09-16:** v30 wird released, Schlussmodell heisst **Tessa** --
    aber "v30 = letzte Generation" ist NICHT mehr fest (Nutzer: "kann gut sein dass noch ein
    v31 kommt damit die ganzen aenderungen wirklich sauber durchschlagen"). Praezisiert:
    **ab v30 keine neuen Preregs**; gefahren wird Staerke ueber Generationen, gegebenenfalls
    mit Armen aus den JETZT offenen Preregs. Vorschlaege mit Wirkung erst in v31 sind nicht aus
    dem Rennen, aber nur mit gemessenem Beleg aus einer bestehenden Prereg.

12. **Kleinkram:** b03s Monolith ist ueberschrieben (Neubau rund 35 min aus den Bloecken,
    faellig erst wenn b03 wieder gebraucht wird); die Dry-Artefakte
    `evaluations/artifacts/_dry_*.json` vom Sonden-Bau koennen weg (Verzeichnis ist
    git-ignoriert).

## 7. VERBOTE UND STEHENDE REGELN

- **Kein Push ohne Anweisung.** Ahead-Stand im Chat melden. Stand 2026-09-18, 20:20: **2 Commits
  vor `origin/main`**, der Nutzer pusht selbst.
- **Loeschung nur auf pfadgenaue Freigabe**, mit restic-Beleg je Gruppe. Frage ist keine
  Anweisung.
- **Messungen laufen exklusiv.** GPU und CPU duerfen parallel, zwei CPU-Messungen nie; ein
  Build zaehlt als Last. **Kein Commit waehrend eines Wanduhr-Laufs.**
- **Nie committen:** `player_profiles.json`, `player_profiles.json.bak`,
  `models/manifest_train_v28-b0*.json`, `evaluations/game_analysis/*`. Nach `git add -A` die
  zwei Profil-Dateien gezielt mit `git restore --staged` herausnehmen.
- **Dateien laufender Laeufe nicht anfassen** -- auch nicht `self_play.py`,
  `selfplay_manifest.py`, `config.py`, `engine/py/neural_net.py`, `corpus_dataset.py`: die
  Chunk-Prozesse importieren frisch.
- **Kettenskripte als DATEI starten** (`bash tools/x.sh`), NIE Heredoc-schreiben-und-starten in
  einem Befehl -- der Wrapper traegt sonst den Skripttext in seiner Kommandozeile, und die
  Wartebedingung findet sich selbst (32 min Stillstand am 2026-09-16; `../docs/pitfalls.md`).
- **Lange Laeufe nie in eine Pipe und ohne eigene Umleitung**, mit Fortschritt (`python -u`,
  `flush=True`).
- **Regel 0**, Prereg-Kopf im selben Zug wie das Ergebnis, Laufzeiten ins Artefakt, sechs
  Standard-Kennzahlen in jedem Messbericht, kein Geviertstrich in Dateien, Bezeichner
  englisch, Inhalte deutsch.
- Keine neuen Netzkoepfe; nicht jeden Arm in die Elo-Leiter.

## 8. BEFUNDE, die eine Nachschau brauchen

- **Nicht-Transitivitaet am Leiterboden:** v22@25 gegen hv4@150 76 %, gegen hv4@600 50 %,
  hv4@600 gegen hv4@150 55 %. Bradley-Terry mittelt das.
- **Replayer-Grenze Chip-Vollendung:** einzelne Partien nicht nachspielbar ("Reihe N nicht mit
  Chips komplettierbar" nach 60 Versuchen); bekannte Grenze, zuletzt 4 von 400 und 1 von 360.
- **GUI und Arena: dasselbe Spiel, dieselbe Tiefe** (geprueft 2026-09-13,
  `PREREG_difficulty_levels.md` par.11). Beide enden in `select_final_root_child`, beide ohne
  Wurzelrauschen, beide mit Runde-5-Kurzschluss; `server.py` schreibt die Champion-Spec beim
  Start in die Umgebung. **Die GUI spielt heute immer bei 400 Sims**, weil die Presets aus ihr
  nicht erreichbar sind -- also genau die Einstellung, bei der die Arena misst.
  **Latente Sollbruchstelle:** die Arena zieht `builder_drafting_preference` der Suche vor, der
  Serverpfad kennt den Vorzug nicht; folgenlos nur, solange `MOSAIC_SPALTENBAU`/
  `MOSAIC_PLATTENBAU` unbesetzt bleiben.
- **Gating-Artefakte tragen keine Engine-Konfiguration** (`paired_gating.py`): ein Env-Knopf,
  der in einer Arena an war, ist dort nachtraeglich nicht belegbar.
- **`MOSAIC_ENVELOPE_REACH_W` und `_SLOT_W`** haben keine Spec-Entsprechung. Heute inert, weil
  das Rezept Projektionsmodus 1 faehrt; bei Modus 2 oder 4 waeren sie exakt der
  Stack-Draw-Fall.
- **Sims und Spaltenbau:** die Kurve am Champion faellt ueber 100-600 Sims monoton, und zwar
  allein ueber die VOLLENDUNG -- die Teilspalten bleiben gleich
  (`PREREG_search_depth_column_optimum.md` par.8e).
- **Kein zurueckgehaltener Satz der LAUFENDEN Aera** (`v29_window` par.6d Punkt 5): jede Datei
  in `data/` liegt in mindestens einem Fenster, deshalb ist der Trend ueber die Generationen
  nicht von der Verteilungsnaehe trennbar. Der Handgriff waere, vor dem v30-Training eine
  Scheibe des frischen Self-Plays zu reservieren und aus der Fensterliste zu nehmen.
- **Pfadform der Dateiliste im Cache-Schluessel** (`../docs/pitfalls.md`): Stempel und
  Verbraucher stimmen seit dem 2026-09-17 ueberein, die eigentliche Reparatur (Normalisierung
  auf Basenames) entwertet jeden Monolithen und ist Nutzer-Entscheid an einem
  Generationswechsel.
- **Python-Werkzeuge nach einem Kontraktwechsel:** `tools/offline_diagnosis.py`,
  `tools/oracle_metrics.py` und `tools/probes/*_gate.py` uebergeben `num_actions` noch
  explizit und laden Alt-Checkpoints darum nicht (`../docs/pitfalls.md`, 2026-09-18).
- `player_profiles.json` im Arbeitsbaum veraendert (Server-Seite), nicht committet.
