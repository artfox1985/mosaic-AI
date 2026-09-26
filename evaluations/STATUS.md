# Mosaic-AI – Status & Fahrplan

**Dieses Dokument traegt NUR Aktuelles und Offenes.** Neufassung vom 2026-09-19
(Generationswechsel v30 -> v31, Skill Schritt 6); der vollstaendige Stand davor liegt in
`../archive/history.md`, Kapitel **"Vollstaendiger STATUS-Stand vom 2026-09-19 (vor der
Neufassung zum Generationswechsel v30 -> v31)"**, der **"Generationsbericht v30 (2026-09-18
bis 2026-09-19)"** als Kapitel davor, die Generationsberichte v24 bis v29 weiter oben.

**Pflegeregel:** wer einen Befund erzeugt, traegt ihn im selben Zug hier nach und prueft, ob
ein anderer Abschnitt dadurch falsch wird. Wer einen Strang abschliesst, schiebt die
Herleitung ins Archiv und laesst hier eine Zeile mit Verweis stehen. Wer ein Ergebnis
registriert, greppt nach seinen KONSUMENTEN (CLAUDE.md, Rueckwaerts-Pruefung).

**Dauerhaftes Prozesswissen steht NICHT hier**, sondern in `../docs/`: `generation_loop.md`,
`promotion_checklist.md`, `generation_naming.md`, `working_rules.md`, `pitfalls.md`,
`measured_runtimes.md`, `architecture_reference.md`, `engine_manual.md`.

---

## 1. WAS GERADE LAEUFT

**STAND 2026-09-26 -- v33-Erzeugung fertig, Pflichtpruefungen und Vortests stehen an; die Kette wartet auf
Nutzer-Freigabe.** Der vollstaendige STATUS vor diesem Wechsel steht woertlich in
`../archive/history.md`, dazu der Generationsbericht v32.

**FERTIG: die v33-Erzeugung** (`bash tools/night_v33_generate.sh`), Exit 0 am 2026-09-26
04:23:55. Dateien gezaehlt: `policy` 400, `value-tempc-nohull` 400, `value-excursion` 401; letzte
Klasse 4.000 Partien in 13.753,9 s (3,43 s je Partie, threads 11, laut Aufgabenausgabe und Manifest).
**Pflichtpruefungen GRUEN** (`PREREG_v33_window.md` par.9): Manifest-Diff, Wiedervorlage, Tor 2a
`sp_voll` 0,966 gegen 0,977 (haelt, erstmals leicht fallend). **Vielfaltssonde: +1,1 Prozent**,
der Knopf bringt im temperierten Schwarm praktisch keine Vielfalt (`PREREG_geometric_envelope.md`
par.14e). **Bewerter-Vortests Stufe 1 gefahren** (`PREREG_evaluator_pretests.md` par.8a): E1
gleich gut, Arm kommt wegen der Kosten; E2 besteht (+0,00213 Brier); E3 tot; der Kopf schlaegt im
Mittelspiel den linearen Leser.

**v33-Kette FERTIG 13:33.** Training v33-b01 61 min, Tor 1 **420:380 = 52,50 Prozent, Block-z +1,41**:
das Kriterium "gepoolt >= 52,5" ist GENAU AUF DER KANTE erfuellt, statistisch nicht gesichert
(`PREREG_v33_window.md` par.10). **Promotion: Nutzer-Entscheid**, Vorschlag erst nach dem b02-A/B.

**NEBENLAST-VERSTOSS 2026-09-26 (Koordinator, sofort gemeldet):** waehrend des b02-A/B (seit
14:17, Seed 20261651 ab 15:32) liefen ab etwa 15:47 drei Python-Auswertungen ueber 30-150
Korpusdateien (je rund 1 min; Spalten je Index, Startplatten-Auszaehlung) plus Kurzaufrufe
(Index-Generator, Datei-Edits). Irrtum: das A/B wurde fuer GPU-Training gehalten. Betroffen ist
**Seed 20261651, grob Block 5-15**; Seed 20261650 war vorher fertig. **ERLEDIGT:** exklusive
Wiederholung von Seed 20261651, Block 1-17 (das ganze Lastfenster) auf Blockebene IDENTISCH, dann
abgebrochen; der Seed gilt. Statt des Rests laeuft auf Nutzer-Hinweis ein **Entscheidungsseed
20261652** (fester Umfang, `PREREG_v33_window.md` par.6a Nachtrag), danach b03.

**LAEUFT: b02-Arm** (`tools/night_v33_b02.sh`, im selben Hintergrundauftrag wie die Kette):
Training, dann A/B gegen b01 (2 Seeds a 200 Paare). Nichts anderes starten, kein Build, kein Commit.
Danach **b03** (`PREREG_v33_window.md` par.6b, Nutzer 2026-09-26): 4.000 Schwarm-Partien MEHR vom
Generator v32-b01, Fenster je nach b02-Ergebnis, A/B gegen b01, rund 9,5 h; Klasse **`value-wegc`**
(Sockel-Einstellung, value-only; der Ausflug wird gezielt abzweigend umgebaut). Dann Vortest gezieltes Abzweigen (`PREREG_targeted_branching.md`)
und die Wheel-Runde (Stufe 2 der Bewerter-Vortests, Review-Fixes, Spiegelknopf `PREREG_tie_mirror.md`).

**Champion `v32-b01_brierbest`** seit 2026-09-25 (`PREREG_v32_window.md` par.11), eingefroren
unter `models/frozen_champions/v32-b01`; Anker-Drift und -Konservierung gruen auf dem
aktuellen Wheel `46b5dfed...`.

**Aufgeraeumt** (Freigabe 2026-09-25, Gruppen A-F; Beleg restic-Snapshot **`373b8404`**,
`verify_backup.ps1` gruen, `-Deep` auf Nutzer-Entscheid nicht gefahren): Korpus `v29-b11`, die
v32-Fenstercaches (ohne Beleg, `*.h5` ist ausgeschlossen), 1.203 verwaiste Bloecke, Modelle ohne
Rolle, Zwischenstaende v31/v32, drei Ketten-Skripte. `data/` 6,2 -> 3,2 GB,
`cache_inventory.py --orphans` leer. **Das Modell `v29-b11` bleibt:** keine restic-Laufmarke.

### FAHRPLAN (eingetaktet 2026-09-25, Nutzer: *"Registrieren das so vor und takte es ein"*)

1. **ERLEDIGT: v33-Erzeugung** (siehe oben), fertig 2026-09-26 04:23:55.
2. **ERLEDIGT: Pflichtpruefungen der Erzeugung** (`PREREG_v33_window.md` par.9): Manifest-Diff je Klasse,
   Wiedervorlage am ersten Record, Tor 0, Tor 2a am Sockel, Vielfaltssonde an Schwarm a.
2a. **ERLEDIGT: Bewerter-Vortests Stufe 1** (`PREREG_evaluator_pretests.md` par.3/par.4; Nutzer 2026-09-25:
    *"Ja Takte deinen Vorschlag so ein"*): offline auf dem Champion, 60 Val-Dateien aus
    `window_v32_val.txt`, kein Build. E1 (Einpass-Konsum statt geflipptem zweiten Pass) wird nur
    gelesen, sein Arm kommt sicher; E2 (Margen-Schwellen) und E3 (Rundenschicht) muessen gegen
    Zufalls-Trunk und die Schwelle 0,0012 Brier bestehen. Laufzeit ungemessen, Block im Artefakt.
    Werkzeug wird vorher geschrieben, laeuft erst nach Punkt 2.
3. **v33-Kette auf Nutzer-Freigabe** (`bash tools/night_v33_chain.sh`). Tor 1 mit der
   **Stufenregel** aus par.2a: ein dritter Seed (20261602, rund +2 h) genau dann, wenn genau einer
   der beiden ersten einzeln Block-z >= +1,96 erreicht. Rechnung `tools/gating_block_z.py`,
   geeicht an v31/v32 (6 von 6 exakt).
3a. **Im Anschluss an die Kette: `bash tools/night_v33_b02.sh`** (Nutzer: *"Dann fahr Im Anschluss
    eine a/b Partie mit weniger Schwarm Anteil"*, `PREREG_v33_window.md` par.6a). Arm `v33-b02` mit
    Fenster ohne den Schwarm aus G-1/G-2, gleiche Val-Menge, dann A/B gegen b01 (2 Seeds a 200
    Paare). Beantwortet, ob aelterer Schwarm traegt. Rund 5 h, HERLEITUNG aus v32.
3b. **Bewerter-Vortests Stufe 2** (`PREREG_evaluator_pretests.md` par.5): EINE Wheel-Runde fuer
    den E1-Laufzeitknopf und einen pyo3-Export fuer E4, Anker-Invarianz, E1-Kostentor (je 100
    Partien) und E1-Arm (Champion mit/ohne Knopf, 2 Seeds a 200 Paare), dann E4-Vortest. Das
    Ergebnis entscheidet, ob die v34-Erzeugung mit Einpass-Konsum faehrt.
3d. **Paket der v33-Generation nach der Wheel-Runde** (Nutzer 2026-09-26: *"Dann haben wir ein
    schoenes Paket fuer diese generation"*): E1-Arm (`PREREG_evaluator_pretests.md` par.5),
    Vortest gezieltes Abzweigen (`PREREG_targeted_branching.md`), **R5 Netz gegen Loeser**
    (`PREREG_r5_net_vs_solver.md`, NEU: A/B desselben Champions, braucht den Schalter
    `r5_net_solver` je Seite aus der Wheel-Runde), Spiegelknopf in der v34-Erzeugung
    (`PREREG_tie_mirror.md`).
3c. **Code-Review vom 2026-09-26 umsetzen** (Nutzer: *"Mach das"*; Review als Claude-Docs-Dokument
    "Code-Review mosaic-AI", 23 Befunde; Nachpruefung lesend nach
    `evaluations/review/code_review_2026-09-26_verification.md`). IN DERSELBEN Wheel-Runde wie 3b,
    damit die Anker-Invarianz nur einmal faellt: (1) "Validierung vor Mutation" #1-5 plus #6
    (`is_over`) mit Tests, (2) #18 Export und #19 pre-push, (3) #8 (Pfad `moon_order_variants: 2`,
    nicht im Rezept, aber in den Diagnose-Specs `models/moon_order_post2|scale0|scale1.spec.json`:
    der Stufe-3-Nullbefund in `PREREG_moon_stack_order.md` ist unter dem Leck gemessen), #10 `/api/stack/peek`, #21 `debug=True`.
    **#9 (Heuristik-MCTS determinisiert nicht): BLEIBT SO** (Nutzer 2026-09-26: *"Zu 9: lass es
    so."*). Der Anker `hv4_anchor` bleibt unveraendert; das Leck ist Teil seiner Definition.
    **#14 EINGETAKTET** (Nutzer 2026-09-26: *"Takte es ein"*): am Abzweig des Ausflugs mit `ex_rng`
    neu mischen, was KEINER der beiden Spieler kennt (Beutelreihenfolge, unbekannter Stapelteil,
    verdeckte Chips); was ein Spieler rechtmaessig weiss (eigener Rueckgabeblock), bleibt stehen.
    Grund: der Ausflug soll eine unabhaengige Stichprobe der Zukunft sein, heute zieht er bis zum
    naechsten Turm-Nachfuellen dieselben Fliesen wie die Hauptpartie. Kein Arm, Korrektheitsfix;
    vor der v34-Erzeugung. Weg C ist nicht betroffen (weicht IN der Hauptpartie ab, kein Zwilling).
    Nachpruefung liegt vor (`code_review_2026-09-26_verification.md`): 21 bestaetigt, #7 teilweise
    (Referee prueft, `referee.rs:911-967`), #6 wirkt nicht auf Self-Play/Arena (dort `Phase::End`).
    **Beruehren Messungen/Korpus:** #9 (alle Anker-Kanten), #13 (Label-Sampling zieht aus dem
    Partie-RNG, `self_play.rs:3785-3789`), #14 (Ausflug teilt die verdeckte Zukunft der
    Hauptpartie), #16 (Rueckfall-One-hot; `MOSAIC_IGNORE_POLICY_TARGET_VALID=1` macht die
    einfache Markierung wirkungslos), #18 (Export im laufenden Training: Ausgabe auf
    Shape-Mismatch pruefen), #23 (Panics im Netz-Self-Play verschwinden als Watchdog-"Deadline",
    `self_play.rs:6335-6346`: stiller Auswahleffekt).
4. **Traegt Tor 1: `/mosaic-champion-promotion`** mit `models/v33_gating.spec.json` als
   Champion-Spec (Startkuppel-Suche an).
5. **v34-Wechsel:** Rezeptfrage VOLUMEN (Abschnitt 6, Punkt 14). Dazu vormerken: das R4-Substrat
   `selfplay_v30-b02-policy_*` rotiert dann heraus -- vorher die 72 Zustaende sichern, sonst endet
   die gepaarte R4/R4b-Reihe.

**Zurueckgezogen am selben Tag** (Nutzer: *"Mehrkosten sind kritisch abzuwaegen ... nichts fahren,
was schon getestet wurde"*): `PREREG_training_seed_arms.md` und `PREREG_value_readout.md`, beide
UEBERHOLT mit der Liste dessen, was schon gemessen ist. Nichts davon ist gelaufen.

**Committet am 2026-09-26 nach der Erzeugung:** par.2a samt Kettenerweiterung, par.6a samt
`tools/night_v33_b02.sh`, `tools/gating_block_z.py`, die zwei zurueckgezogenen Preregs, die
R5-Streichung, `PREREG_evaluator_pretests.md` samt Werkzeug und Recherche-Bericht.

### FREIGABEN UND VERBOTE (woertlich)

* Nutzer 2026-09-25: *"2 und 3 machen, bei 4 nimm a. fuer 1 machst 4000 schwarm spiele ohne
  huellenknopf"*; auf die Einschaetzung zur Klasse: *"ja, trag es ein"* (temperiert ohne Knopf).
* Nutzer 2026-09-25: Loeschfreigabe A-F im Generationswechsel -- ausgefuehrt und verbraucht.
  Jede weitere Loeschung braucht restic-Beleg UND neue pfadgenaue Freigabe.
* **Kein Push ohne Anweisung.** Nie committen: `player_profiles.json`, `player_profiles.json.bak`.
* **Kein Commit waehrend eines Wanduhr-Laufs.** Messungen exklusiv; ein Build zaehlt als Last --
  und ein `grep -rn` ueber `data/` auch.

## 2. CHAMPION UND LEITER

**Champion laut `models/champion.txt`: `v32-b01_brierbest`** (Promotion 2026-09-25), nach aussen
**Tessa** (der Anzeigename steht fest in `static/js/app.js`, er wandert mit jedem Champion mit).
**Elo 1480 [1431; 1529]** aus 1.000 Partien im Leitersegment 2, Anker `hv4_anchor` fix 1000,
Bradley-Terry mit Block-Bootstrap. **Keine seiner vier Kanten ist frueh gestoppt.**

Vier Kanten tragen ihn: Gating gegen `v31-b01` 434:366 ueber zwei Seeds (Block-z +2,37, aber nur
EIN Seed einzeln signifikant: +3,26 gegen +0,10), Anker @150 mit n = 50 auf 43:7, Champion-2 gegen
`v30-b02` 94:56 (binomial p = 0,0024) -- die Champion-2-Kante trifft diesmal die transitive
Erwartung (61,7 hergeleitet, 62,7 gemessen). Herleitung: `PREREG_v32_window.md` par.11.

| Modell | Elo | KI95 | Partien |
| --- | --- | --- | --- |
| **v32-b01@400 (Champion, Tessa)** | **1480** | **[1431; 1529]** | **1.000** |
| v31-b01@400 | 1450 | [1406; 1496] | 1.800 |
| v30-b02@400 | 1411 | [1371; 1453] | 1.890 |
| Heuristik_hv4_anchor@150 (Anker) | 1000 | fix | 1.700 |

Die uebrigen Knoten stehen im Bericht von `tools/elo_tracker.py report`; das Primaerregister ist
`evaluations/elo_history.csv`.

**Engine-Stand:** Paketversion **1.1.0**, Vertragshash `6ef829e564c58bd5`, 888/414. Live ist seit
2026-09-25 das Wheel `46b5dfed...` (GUI-Tor, `PREREG_dome_return_order.md` par.14b); gemessen und
eingefroren wurde `v32-b01` auf `e11ea6d5...`. Beide tragen dieselbe Versionsnummer -- die Version
geht weder in den Hash noch in einen Cache-Schluessel noch in den Handshake ein, und das Artefakt
identifiziert sein Wheel ueber den sha256. Anker-Drift und -Konservierung ueber den Wechsel gruen.

**Eingefrorene Artefakte:** `models/frozen_champions/` traegt genau `v31-b01` und `v32-b01`
(Zwei-Champion-Regel). **`v30-b02` ist am 2026-09-25 geloescht**, Beleg restic-Snapshot
`4137c235` (7 von 7 sicherungswuerdigen Dateien mit gleicher Groesse; das `venv/` ist per
`backup_excludes.txt` ausgenommen und aus dem mitgesicherten Wheel neu baubar). Seine Kanten
stehen unveraendert im Register. **Seit dem 2026-09-23 sind `.onnx`, `.pth` und Wheels der
Artefakte NICHT im Repo** -- getrackt werden Spec, Manifest, Golden Probe und `wheel.sha256`.

## 3. LAUFZEITEN (gemessen, Planungsgroessen; Details in `../docs/measured_runtimes.md`)

| Aufbau | Dauer | Anmerkung |
| --- | --- | --- |
| Erzeugung 3 x 4.000 Partien @100, threads 11, 888/414 | **13,86 h** (v30) | 9,92 h (v28) / 12,8 h (v29); Sockel 18.984 s, temperiert 16.184 s, Ausflug 14.744 s |
| Erzeugungskosten je Partie @100, Policy-Klasse | 3,183 (v28) / 3,943 (v29) / **4,746** (v30) | +20,4 Prozent gegen v29, +49,1 Prozent gegen v28 |
| Blockbau fuers Fenster, Bloecke vom Waechter vorgebaut | 4 s plus **611 s** Merge | v30-Kette |
| Blockbau 2.800 Dateien plus Merge, 6 Worker, 884 | 2.144 s = 35,7 min | +9,2 Prozent gegen 794 |
| Training Warmstart 12 Epochen, 4,89 Mio Samples, 888/414 | **5.573 s = 1,55 h** (gebremst) | v30-b02, lief neben der b01-Arena; exklusiv frueher 57 min |
| Training KALTSTART 12 Epochen, 888/414 | **3.652 s = 1,01 h** | v30-b01; die alte ANNAHME 2,3-2,6 h stammte aus einer anderen Encoder-Aera |
| Tor 1 je Seed, 200 Paare @400, 10 Threads, mit Logs | **5.719 s** exklusiv / 6.940-7.468 s gebremst | 14,3 s je Partie exklusiv, 17,4-18,7 s gebremst |
| Anker-Kante n = 50 | **418,6 s** (v32) / 430 s (v30) | seit 2026-09-19 die Groesse der Promotionsliste; n = 150 war 1.250-1.280 s |
| Champion-2-Kante n = 150 | **2.377,5 s** (v32) / 2.489 s (v30) | 6 Worker |
| Champion-Kanten je Kandidat gesamt | rund 3,5 h | 2 x Gating plus Anker plus Champion-2 |
| Promotion nach Checkliste MIT R4/R4b/R5 (ohne Tor 1) | **rund 2,3 h** (8.289 s, v32) | ohne R4/R4b/R5: 38 min (v29); R4 allein 46 min |
| Netz-Gesundheit komplett (Normen, tote Einheiten, offline, Platt) | rund 30 min | v30 |
| Voller Build: Lib-Tests, `--no-run`, Fixtures, Wheel | rund 5 min | `--no-run` allein 56 s |
| Anker-Drift / Anker-Konservierung | 22,4 s / 16,6 s | je 1.763 Schritte |
| Tagesschnappschuss restic plus check | 6-7 s | |

## 4. SPEC UND REZEPT

**Champion-Spec** `models/frozen_champions/v32-b01/spec.json` (= `models/v32-b01_brierbest.spec.json`,
byte-gleich mit der von `v31-b01`, sha256 `4f5e5969...`). Sie traegt **weder `start_by_search`
noch `return_order_mode`**; die Startkuppel-Suche kommt ab v33 (`PREREG_start_dome_choice.md`
par.12), vorbereitet als `models/v33_gating.spec.json` fuer Tor 1 (Entscheid offen,
`PREREG_v33_window.md` par.6).

**Erzeugungs-Spec** `models/v32_generation.spec.json`, byte-gleich mit der v30/v31-Fassung
(sha256 `4a3f9db3...`, = `start_by_search_on.spec.json` plus `return_order_mode: 1`). **Ab v33
faehrt Schwarm a `models/v32_generation_nohull.spec.json`** -- identisch bis auf
`envelope_search_c: 0.0` (`PREREG_geometric_envelope.md` par.14d).

**Engine-Stand:** INPUT_SIZE **888**, NUM_ACTIONS **414**, Vertragshash `6ef829e564c58bd5`,
Paketversion 1.1.0, live das Wheel `46b5dfed...` (mit dem GUI-Tor; der Self-Play-Pfad ist davon
unberuehrt). Suchknoten: Mond 406-410, Rueckgabe 411-413, Slot und Rotation als eigene Knoten mit
Policy-Ziel. Die Rueckgabe-Streuung sitzt seit 2026-09-19 im KNOTEN-Weg, die Maske dazu in
`engine/py/corpus_dataset.py` als eigene Bedingung auf `return_order_randomized`.

**Das Rezept seit v30, belegt:** Warmstart vom amtierenden Champion, `--moon-loss-weight 0`,
`--ownership-weight 0` mit `--ownership-head-2d`, `--opp-points-head`, 12 Epochen, lr 5e-05 cosine
mit `--lr-t-max 12`, lambda 0,7, `--select-by-brier`, `--fast-loader`. Der Kaltstart ist
widerlegt (v30: 404:396 kalt gegen 443:297 warm, 9,36 Prozentpunkte).

**v33-Fenster** (`PREREG_v33_window.md` par.1): Soll 2.947 Dateien -- neu `v32-b01` (1.201, mit
`value-tempc-nohull`), G-1 `v31-b01` (1.201), G-2 `v30-b02` (400 policy + 145 Ausflug); `v29-b11`
ist herausrotiert und geloescht. Seed 20260957, Val-Pool `^selfplay_v32-`, 580 Traeger.

## 5. PREREG-BESTAND (3 OFFEN laut Index 2026-09-25; Ziel rund 7)

| Prereg | Was noch aussteht |
| --- | --- |
| `v33_window` | NEU 2026-09-25; par.6 entschieden, Erzeugung laeuft seit 2026-09-25 |
| `evaluator_pretests` | NEU 2026-09-25; Stufe 1 nach der Erzeugung, Stufe 2 nach Kette und b02 (Fahrplan 2a/3b) |
| `difficulty_levels` | ganze Leiter auf den letzten Champion vertagt |

Beim Generationswechsel am 2026-09-25 auf ENTSCHIEDEN gezogen bzw. ergaenzt: `v32_window`
(par.11 Promotion), `dome_return_order` (par.14-14b GUI-Tor), `start_dome_choice` (par.12),
`geometric_envelope` (par.14d Schwarm a ohne Knopf); danach `python tools/generate_prereg_index.py`.

## 6. OFFENE NUTZER-ENTSCHEIDE

1. **Ein oder zwei Arme fuer v31** (`PREREG_v31_window.md` par.5 Punkt 2). v30 fuhr kalt und
   warm; der Warmstart gewann mit 9,36 Punkten Abstand, die Kaltstart-Frage ist damit
   beantwortet. Ein zweiter Arm braucht also einen ANDEREN Faktor, sonst reicht einer.

2. **Budget-Knopf fuer die Hilfsknoten** (Slot, Rotation, Rueckgabe, Mond). Die Kosten sind
   hingenommen (Nutzer 2026-09-18: "wenn es was bringt stoert mich der mehraufwand nicht"); offen
   ist allein die WIRKUNG, und v31 ist der erste Zyklus, in dem sie beantwortbar ist: in v30
   waren die Knoten mit 40,8 Prozent Fensterabdeckung vorregistriert unterbelegt, jetzt sind es
   rund 81,6 Prozent. Trennung aus dem Lernstoff: der **Mondknoten** traegt in 11,64 Prozent der
   Sockel-Records ein Policy-Ziel, der **Rueckgabeknoten in 0,18 Prozent**.

3. **Gruppe B des Aufraeumens**, drei Punkte, je eigener Entscheid: der Wrapper
   `resolve_and_apply_stack_draw` (ein Test ruft ihn auf) und die drei Spec-Felder aus
   `KNOWN_FIELDS` (drei rote Tests, Alt-Specs duerfen sie tragen), beide
   `PREREG_code_cleanup_closeout.md` par.8d; dazu die **Kanonisierung der Bonuschip-Farben**
   (par.8e): fuenf zweifarbige Kombinationen liegen je zweimal im Pool, bei zweien ist die
   Reihenfolge zwischen den Zwillingen vertauscht (`dome.rs:250-273`, Quelle
   `docs/bonus_chips_colors.csv`). Wertung und Netz-Eingabe sind davon unberuehrt (Bitmaske bzw.
   Farb-Flags); Arbeit kostet es in `round5.rs:281` (ein Zufallsast zu viel) und
   `tiling_solver.rs:331` (Cache-Fehlgriffe). **Die Chip-Kanonisierung ist in Anzeige UND Engine gebaut** (2026-09-19/20, CHANGELOG
   v1.0-alpha31, `PREREG_code_cleanup_closeout.md` par.8e); offen sind nur die beiden anderen
   Teile, der Wrapper und die drei Spec-Felder.

4. **ERLEDIGT: die Golden Probe des Ankers ist nicht mehr dauerhaft ROT.** Weg (a) ist seit dem
   2026-09-20 gebaut (Commit `a9302ecb`, *"Drift-Pruefer normalisiert Bonuschip-Farben, eng
   begrenzt"*: `_first_divergence` ordnet nur die Felder `colors` und `unused_chip_colors`, nur
   Listen reiner Zeichenketten). Dieser Eintrag stand danach noch fuenf Tage als offen hier; der
   Nutzer hat am 2026-09-25 (a) bestaetigt, und die Anker-Drift ist am selben Tag ueber 1.763
   Schritte gruen.

5. **R5- und R4b-Sonden der Promotionsliste:** fuer `v32-b01` auf Nutzer-Anweisung gefahren
   (*"r5 und r4b mitfahren"*, 2026-09-25), alle GEPAART gegen v31; die Aufrufe stehen jetzt in
   `docs/promotion_checklist.md` Punkt 5. OFFEN bleibt nur, ob sie ab v33 Pflicht sind oder je
   Promotion erfragt werden.

6. **ERLEDIGT 2026-09-25: Push der umgeschriebenen Historie.** GitHub stand auf `165d1243`
   (lokal umgeschrieben `7b128e35`), der Nutzer hat mit Lease darauf gepusht; seither steht
   GitHub auf dem lokalen `main`. Ein bestehender Klon auf einem anderen Rechner muss NEU
   geklont werden -- ein `git pull` dort holte die alte Historie zurueck.

### Aeltere, weiterhin offene Punkte (unveraendert uebernommen)

6. **Brier-Regel:** bei `v30-b02` gerissen (0,26196 gegen 0,25507 auf `frozen_v1`), bei `v31-b01`
   gestreift (0,22919 gegen 0,22804 auf `frozen_v3`). **Bei `v32-b01` haelt sie**: 0,22864 gegen
   0,22919, im selben Lauf gemessen, und v31 reproduziert dabei seinen Wert exakt
   (`PREREG_v32_window.md` par.11). Offen bleibt der Grundsatzpunkt: `frozen_eval_set` stammt aus
   einer aelteren Verteilung.

7. **ERLEDIGT 2026-09-25: das Manifest traegt die Spec.** `engine_config` meldet weiterhin den
   Env-Default (bewusst unveraendert, damit alte und neue Manifeste diffbar bleiben), daneben steht
   jetzt `spec_file` mit Pfad, sha256 und Inhalt (`selfplay_manifest.py`, vier Tests). Anlass zum
   Bau war v33, das zwei Specs faehrt (`PREREG_geometric_envelope.md` par.14d).

8. **Sichtluecke bei den gezogenen Stapelplatten** (`stack_top_feature` par.16/16a): die
   Vorderseiten sind erst NACH dem Aufhoeren bekannt. (a) Die Aktionsliste verraet sie ueber die
   Rotationsfilterung (`game.rs` Z.402) -- betrifft die Suche, Reparatur beruehrt `NUM_ACTIONS`.
   (b) `serialize.rs` Z.375-379 serialisiert sie sofort, die Anzeige druckt sie -- betrifft den
   menschlichen Spieler, eingetreten in Partie g07.

9. **Paritaets-Tor und Alt-Records** (`rust_data_layer` par.9/9a): Kanal 76 weicht auf Records
   von vor dem A2-Fix ab, weil das Tor eine GESPEICHERTE gegen eine frisch gerechnete Groesse
   haelt. Offen: gespeicherte Felder aufgeben oder das Tor auf frische Zustaende beschraenken.

10. **Drei Sonden zeigen auf das geloeschte Artefakt `hv1_anchor`**
    (`anchor_referee_parity_probe.py`, `frozen_agent_referee_probe.py`,
    `frozen_worker_protocol_probe.py`). Umstellung auf `hv4_anchor` braucht neue
    Erwartungswerte, also einen Lauf. Lohnt das, oder entfallen die drei als historisch?

11. **`-Deep`-Lauf der Backup-Verifikation**: `verify_backup.ps1` empfiehlt ihn vor der ersten
    Loeschung; zuletzt am 2026-09-13 auf Nutzer-Entscheid nicht gefahren.

12. **Rahmen:** v30 ist released, das Schlussmodell heisst **Tessa**, und v31 laeuft, "damit die
    ganzen aenderungen wirklich sauber durchschlagen". Ab v30 keine neuen Preregs; Arme nur aus
    den jetzt offenen Preregs, Aufnahme ins Rezept per Nutzer-Entscheid.

13. **Kleinkram:** die Dry-Artefakte `evaluations/artifacts/_dry_*.json` vom Sonden-Bau koennen
    weg (Verzeichnis ist git-ignoriert).

14. **v34-Rezept: mehr Partien je Generation?** Der einzige Hebel aus der Ideenliste vom
    2026-09-25, der schon BELEGT ist: mehr Korpus traegt in Orakel und Arena
    (`PREREG_corpus_dose.md`, 900 gegen 450 Dateien, 479:321, p < 0,0001), und der Value-Kopf
    saettigt nicht (`PREREG_task36_value_saturation.md`, jede Verdopplung rund 0,0012 Brier).
    Beide aus einer aelteren Aera. Preis: je 4.000 Partien rund 4,5 h Erzeugung (v32). Keine
    Testfrage, sondern ein Budget-Entscheid -- gehoert in par.6 der v34-Fenster-Prereg.
    **Eingegrenzt 2026-09-25 (Nutzer: *"Mehr sockel bringt nichts denk ich. Policy ist
    gesaettigt"*), belegt:** Task #36 fand die Policy-Gegenkurve "flach (daten-gesaettigt)"
    (`PREREG_task36_value_saturation.md`). Mehr Volumen also NUR als Schwarm (value-only).
    Offen fuer v34: ob ueberhaupt, und welche Klasse -- der Ausflug liefert unverzerrte Ziele,
    der temperierte Schwarm Breite; die Vielfaltssonde an `value-tempc-nohull` (v33 par.9)
    liefert dazu die erste Zahl.
15. **ENTSCHIEDEN 2026-09-26: Stufenregel gilt fuer v33** (Nutzer: *"Setz es um wie vorgeschlagen"*). Frueher offen: **Stufenregel fuer Tor 1 behalten?** (`PREREG_v33_window.md` par.2a, in der v33-Kette
    eingebaut): ein dritter Seed kostet rund 2 h, nur wenn die ersten zwei sich widersprechen.
    Er aendert ein Verdikt nur in knappen Faellen, weil das Kriterium auch "gepoolt >= 52,5
    Prozent" durchlaesst. VOR dem Start der v33-Kette zu entscheiden.

16. **v34: Schwarm a wieder mit Huellenknopf?** Die Vielfaltssonde zeigt ohne Knopf nur +1,1
    Prozent verschiedene Zustaende (`PREREG_geometric_envelope.md` par.14e); der Zweck, fuer den
    der Knopf dort ausgeschaltet wurde, ist damit kaum erfuellt. Zum v34-Wechsel.

17. **v34: E2-Arm (Margen-Schwellen am WDL-Logit).** Vortest bestanden (+0,00213 Brier an einem
    LINEAREN Leser, `PREREG_evaluator_pretests.md` par.8a); ob er dem Kopf hilft, zeigt nur ein
    Arm. Bau rund ein halber Tag, Arm rund 4,5 h. Zuschnitt in der v34-Fenster-Prereg.

## 7. VERBOTE UND STEHENDE REGELN

- **Kein Push ohne Anweisung.** Ahead-Stand im Chat melden.
- **Loeschung nur auf pfadgenaue Freigabe**, mit restic-Beleg je Gruppe. Frage ist keine
  Anweisung. `.h5`-Dateien sind per `tools/backup_excludes.txt` nicht im Backup, weil
  regenerierbar -- fuer sie gibt es keinen Snapshot-Beleg.
- **Messungen laufen exklusiv.** GPU und CPU duerfen parallel, zwei CPU-Messungen nie; ein Build
  zaehlt als Last. **Kein Commit waehrend eines Wanduhr-Laufs.**
- **Nie committen:** `player_profiles.json`, `player_profiles.json.bak`,
  `models/manifest_train_v28-b0*.json`, `evaluations/game_analysis/*`. Nach `git add -A` die zwei
  Profil-Dateien gezielt mit `git restore --staged` herausnehmen.
- **Dateien laufender Laeufe nicht anfassen** -- auch nicht `self_play.py`,
  `selfplay_manifest.py`, `config.py`, `engine/py/neural_net.py`, `corpus_dataset.py`: die
  Chunk-Prozesse importieren frisch. **Auch eine reine Kommentaraenderung zaehlt** (Verstoss
  2026-09-20 am `corpus_dataset.py` waehrend des Cache-Waechters, folgenlos geblieben): das
  Risiko ist das Schreibfenster, nicht der Inhalt -- ein Worker, der genau dann importiert,
  sieht eine halbe Datei.
- **Knoepfe, die self_play.py kennt, gehen als CLI-Flag hinein**, nicht ueber die Umgebung:
  `self_play.py` setzt die Variable aus seinem eigenen Default neu (Z.236-240).
- **Kettenskripte als DATEI starten** (`bash tools/x.sh`), NIE Heredoc-schreiben-und-starten in
  einem Befehl.
- **Lange Laeufe nie in eine Pipe und ohne eigene Umleitung**, mit Fortschritt (`python -u`,
  `flush=True`).
- **Vor dem Self-Play der naechsten Generation: `/mosaic-generation-turnover`** -- der Ablauf
  gehoert VOR den Start, nicht daneben (Vorfall 2026-09-19).
- **Regel 0**, Prereg-Kopf im selben Zug wie das Ergebnis, Laufzeiten ins Artefakt, sechs
  Standard-Kennzahlen in jedem Messbericht, kein Geviertstrich in Dateien, Bezeichner englisch,
  Inhalte deutsch.
- **Eingefrorene Netze sind NICHT mehr im Repo** (Nutzer-Entscheid 2026-09-23, Umschrieb am
  selben Tag gefahren: 227,5 -> 33,7 MiB). Champions behalten Spec, Manifest und Golden Probe
  und bleiben identifizierbar; ihre `.onnx`/`.pth`/`.whl` und die Heuristiken GANZ liegen nur
  noch im Arbeitsbaum und in restic. Ein frischer Klon hat damit kein lauffaehiges Netz -- der
  Nutzer stellt eines bereit, wenn es gebraucht wird. **Kein `git add -f`** fuer kuenftige
  Champions. Die Elo-Zahlen der Heuristik-Knoten stehen im Register `elo_history.csv`.
  Der Umschrieb hat JEDEN Commit-Hash ersetzt: bestehende Klons sind ungueltig. Der
  Force-Push ist am 2026-09-25 erfolgt. Danach lokal `reflog expire` und `gc --prune=now`:
  **33,89 MiB, 17.472 Objekte, `git fsck` sauber.** Zwischendurch lag das Repo lokal wieder
  bei 227 MiB, weil die Desktop-App `origin` zehn Minuten nach dem Umschrieb im Hintergrund
  geholt hatte (Kopf von `tools/rewrite_drop_frozen_blobs.sh`, Folge 5). `git gc` fragt in
  einem Terminal bei jedem gesperrten Objektverzeichnis "Should I try again?"; aus einer
  nicht-interaktiven Shell (stdin nicht am Terminal) laeuft es ohne Nachfrage durch.
- Keine neuen Netzkoepfe; nicht jeden Arm in die Elo-Leiter.

## 8. BEFUNDE, die eine Nachschau brauchen

- **Arena-Logs tragen keine `#a`-Zeilen**, weil die im PyGame-Pfad geschrieben werden
  (`py.rs:781`). Der Replayer riet dort die Rueckgabe-Reihenfolge kanonisch und divergierte in
  15-18 Prozent der Partien. Repariert ueber den Endzustand im Artefakt (`score_geo`,
  `dome_grid`); Tor 2b ist ab der naechsten Arena wieder verwendbar. Server- und Mensch-Logs
  waren nie betroffen.
- **Nicht-Transitivitaet am Leiterboden:** v22@25 gegen hv4@150 76 %, gegen hv4@600 50 %,
  hv4@600 gegen hv4@150 55 %. Bradley-Terry mittelt das.
- **SPRT stoppt zwischen Nachbar-Generationen nicht** (beide v30-b01-Laeufe `UNDECIDED_CAP_REACHED`),
  bei groesserem Abstand sehr wohl. Beim Gating bleibt der Stopp aktiv und zieht unter 150 Paaren
  eine Replikation nach; nur die Anker-Kante faehrt ohne ihn.
- **GUI und Arena: dasselbe Spiel, dieselbe Tiefe.** Beide enden in `select_final_root_child`,
  ohne Wurzelrauschen, mit Runde-5-Kurzschluss. Die GUI spielt immer bei 400 Sims. Latente
  Sollbruchstelle: die Arena zieht `builder_drafting_preference` der Suche vor, der Serverpfad
  kennt den Vorzug nicht.
- **Gating-Artefakte tragen keine Engine-Konfiguration** (`paired_gating.py`): ein Env-Knopf, der
  in einer Arena an war, ist dort nachtraeglich nicht belegbar.
- **`MOSAIC_ENVELOPE_REACH_W` und `_SLOT_W`** haben keine Spec-Entsprechung. Heute inert, weil
  das Rezept Projektionsmodus 1 faehrt.
- **Sims und Spaltenbau:** die Kurve am Champion faellt ueber 100-600 Sims monoton, allein ueber
  die VOLLENDUNG; die Teilspalten bleiben gleich.
- **Kein zurueckgehaltener Satz der laufenden Aera:** jede Datei in `data/` liegt in mindestens
  einem Fenster, deshalb ist der Trend ueber die Generationen nicht von der Verteilungsnaehe
  trennbar. Der Handgriff waere, vor dem v31-Training eine Scheibe des frischen Self-Plays zu
  reservieren und aus der Fensterliste zu nehmen.
- **Pfadform der Dateiliste im Cache-Schluessel:** Stempel und Verbraucher stimmen ueberein, die
  eigentliche Reparatur (Normalisierung auf Basenames) entwertet jeden Monolithen und ist
  Nutzer-Entscheid an einem Generationswechsel.
- **Python-Werkzeuge nach einem Kontraktwechsel:** `tools/offline_diagnosis.py`,
  `tools/oracle_metrics.py` und `tools/probes/*_gate.py` uebergeben `num_actions` noch explizit
  und laden Alt-Checkpoints darum nicht.
- `player_profiles.json` im Arbeitsbaum veraendert (Server-Seite), nicht committet.
