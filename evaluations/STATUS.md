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

**Generationswechsel v29 -> v30 im Gang** (`/mosaic-generation-turnover`). v29 ist
abgeschlossen: Champion `v29-b09` promoviert und eingefroren (2026-09-18, 14:32,
`PREREG_minimal_strength_core.md` 10.18), Generator `v29-b11` abgenommen (10.17). Der
Generationsbericht steht im Archiv.

**Stand des Ablaufs (2026-09-18, 14:50):** Schritt 1 Einfrieren DURCH (Promotion b09). Schritt 2 daily-Snapshot
**`af420224`** (14:35, 6.154 Dateien, `verify_backup.ps1` gruen); `restic find --snapshot af420224`: die 28
Ketten-Skripte der Loeschliste 28 von 28, `selfplay_v26-b01-*` 1.201 von 1.201, `manifest_v26-b01-*` 3 von 3;
Bloecke und Monolithe (`*.h5`) sind planmaessig NICHT in der Sicherung (`docs/backup_restore.md`, rekonstruierbar).
Schritte 3-5 DURCH (Nutzer 2026-09-18, 15:0x: "Loeschfreigabe erteilt"; Ausfuehrung 15:05-15:10): 28 Ketten-Skripte per
`git rm` (restic af420224: 28 von 28); 60 Modelldateien ohne Rolle (685 MB; Klassen wie vorgelegt, die Zahl 54 war
ein Ueberschlag; je Arm `run:`-Snapshot im Repo); Korpus `selfplay_v26-b01-*` 1.201 Dateien plus 3 Manifeste
(1,14 GB; restic 1.201 von 1.201 und 3 von 3); alle 10 Monolithe (6,13 GB) und alle 20.446 Alt-Bloecke (9,19 GB)
plus 382 vom Waechter schon gebaute v26-Bloecke (Waisen), `*.h5` planmaessig nicht in der Sicherung
(rekonstruierbar). `cache_inventory.py --orphans`: 0 Bloecke, 0 Waisen. Verbleibend: 12 Modelldateien
(Champion b09, Generator b11, Vorgaenger v28-b02, b07, v27-b01, engine_test), 2.427 Korpusdateien (v28-b02,
v27-b01, v29-b11 wachsend). Cache-Waechter 15:12 neu gestartet (baut die 888er-Bloecke fuer alle Fensterdateien).
Skill-Vorlage auf `night_v30_chain.sh` umgestellt. Die Loeschungen sind noch NICHT committet (kein Commit neben
dem laufenden Self-Play; Commit heute Abend oder morgen frueh). Schritt 6 (diese Neufassung) DURCH. Schritt 7: Prozessliste vor dem Start geprueft, Erzeugung startet mit
`MOSAIC_V30_GENERATOR=models/alphazero_v29-b11.onnx MOSAIC_V30_GEN_NAME=v29-b11 bash tools/night_v30_generate.sh`,
daneben der Cache-Waechter (Kopf der Kette). **ERZEUGUNG GESTARTET 2026-09-18, 14:50:04** (Sockel `v29-b11-policy`, 4.000 Partien @100, Manifest
`data/manifest_v29-b11-policy_20260918_145006.json`; Wheel-Vertrag 888/414 geprueft). **Vorfall 14:53:** die Kette
haette nach 10 Minuten den ersten Record mit `pickle.load` auf einer gzip-Datei geprueft (derselbe Fehler wie in der
Abnahme-Kette) und das Self-Play bei Exit ungleich 0 getoetet; der Ketten-Wrapper (bash) wurde deshalb beendet,
das Self-Play (python, PID 27628) laeuft verwaist weiter und schreibt nach `data/`. `tools/night_v30_generate.sh`
ist repariert (gzip), und `tools/night_v30_generate_rest.sh` wartet auf das Ende des Sockels, prueft den ersten
Record (gzip) und faehrt Klassen 2 und 3 (Seeds 20260931/32). Cache-Waechter (3 Worker, 888-Schluessel) daneben.
Commit `3d2550a7` vor dem Start (Push-Stand 18).

**Wiedervorlage am ersten Record der v30-Erzeugung GRUEN (2026-09-18, 14:54; `data/selfplay_v29-b11-policy_20260918_1450_g10.pkl`,
1.952 Records aus 10 Partien, gzip-gelesen, IDs ueber `neural_net.action_to_id`):** P.12 `designs` 577 Records,
P.16 `designs_ordered` 577 Records (nur wo ein eigener Block liegt), Mondknoten 406-410 in `valid_actions` 478 / in
`policy` 424, Rueckgabeknoten 411-413 11 / 11, Rotation 640 / 640, Slot 8.132. Der v30-Korpus traegt die neuen
Merkmale und Knoten mit Lernziel; nichts faellt nach v31.

### Als naechstes, in dieser Reihenfolge

1. **Rest des Generationswechsels:** restic-Tagesschnappschuss mit Beleg, obsolete
   Ketten-Skripte, tote Self-Plays/Bloecke/Monolithe und Modelle -- alles nur mit
   `restic find`-Beleg und pfadgenauer Nutzer-Freigabe (Abschnitt 6).

2. **v30-ERZEUGUNG** (Freigabe des Nutzers vom 2026-09-17, STATUS-Archiv Punkt 21;
   `PREREG_v30_window.md` par.5). Start als DATEI, nicht per Heredoc:

   ```
   MOSAIC_V30_GENERATOR=models/alphazero_v29-b11.onnx MOSAIC_V30_GEN_NAME=v29-b11 \
     bash tools/night_v30_generate.sh
   ```

   Die Kette prueft selbst `input_size` 888 und `return_order_mode` im Manifest-Export,
   wartet auf eine freie Maschine und faehrt dann die drei Klassen @100 Sims
   (Seeds 20260930 / 20260931 / 20260932, Spec `models/v30_generation.spec.json`,
   `MOSAIC_STACK_DRAW_RESEARCH=1`, `--start-slot-random-p 0.15`).

   **Daneben gehoert der Cache-Waechter** unter der Trainings-Umgebung, sonst entstehen die
   Bloecke erst nach der Erzeugung:

   ```
   MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_FEATURES_FROM_RUST=1 python -X utf8 -u \
     tools/build_cache_incremental.py --data-dir data --encoder 2d --value-target-variant nortv \
     --workers 3 --watch --wartezeit 60 --leerlauf-abbruch 100000
   ```

   **WIEDERVORLAGE nach dem ersten Record** (`feedback_record_field_must_precede_generation`):
   `designs` (P.12), `designs_ordered` (P.16) und die neuen Knoten-IDs 406-413 mit
   `policy`-Eintrag muessen darin stehen. Die Kette prueft `designs_ordered` selbst und STOPPT
   bei Fehlen; die Knoten prueft der Koordinator. Fehlt etwas, fallen die Merkmale eine
   Generation zurueck. Alle Bloecke sind ohnehin neu zu bauen (888 plus Formel-Version im
   Schluessel).

3. **Danach `tools/night_v30_chain.sh`** (geschrieben 2026-09-18, `bash -n` gruen, NICHT
   gestartet, startet nur auf Anweisung): Tor 0 / Tor 2a je Klasse, Traeger-Manifest,
   G-2-Auswahl (Ausflug-Haelfte von `v27-b01`), Fenster `data/window_v30.txt` (Seed 20260945),
   Bloecke, Monolith mit Stempel-Pruefung, **Training `v30-b01` KALT**, Tor 1 gegen den
   Champion `v29-b09` (zwei Seeds), Spaltensonde, Plattenpunkte. Zuschnitt und Lesart:
   `PREREG_v30_window.md`.

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

## 5. PREREG-BESTAND (11 OFFEN laut Index 2026-09-18, Ziel rund 7)

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
   Prozent der Sims, Praezedenz `moon_order_post_search` mit 256 Sims. **Wiedervorlage v31**
   (Nutzer 2026-09-18, 10:05: Kosten fuer v30 hingenommen), auszuloesen, falls die
   Erzeugungs-Stichprobe mehr als rund +15 Prozent zeigt -- sie zeigt heute +25 Prozent
   (10.17), die Wiedervorlage ist also faellig, sobald die volle Erzeugung ihre Zahl liefert.

3. **Zerlegung Kaltstart gegen Warmstart als eigener Arm `v30-b02`**
   (`PREREG_v30_window.md` par.8 Punkt 2): Rueckfall 2 nicht als Rueckfall, sondern als
   zweiter Arm bei sonst gleichem Rezept und Fenster. Kosten rund 1,2 h Training plus
   2 x rund 105 min Tor 1. Ohne diesen Entscheid laesst par.4 genau einen Arm zu.

4. **Vorgehen, wenn Tor 2a reisst** (`PREREG_v30_window.md` par.8 Punkt 5, Hypothese H4):
   nach `docs/generation_loop.md` Vorlage an den Nutzer mit beiden Zahlen, keine stille
   Fortsetzung. Die Alternative waere, den v29-Korpus weiterzufahren und v30 nur als
   Rezept-Umstellung zu trainieren.

5. **Push.** Stand 2026-09-18 (gemessen `git rev-list --count origin/main..main`):
   **17 Commits vor `origin/main`**. Kein Push ohne Anweisung; der Nutzer pusht selbst.

### Aeltere, weiterhin offene Punkte (unveraendert uebernommen)

6. **Manifest meldet Spec-Felder falsch** (geprueft 2026-09-13): `engine_config` zeigt fuer
   `envelope_search_c`, `envelope_projection_mode`, `envelope_hull_form` und `special_row6_w`
   den Env-Default statt des wirksamen Spec-Werts (`lib.rs` Z.801/807/812/815 lesen
   `SearchConfig::from_env()`). **Kein Belegverlust** -- jedes Manifest nennt den Spec-Pfad.
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

- **Kein Push ohne Anweisung.** Ahead-Stand im Chat melden. Stand 2026-09-18: **17 Commits
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
