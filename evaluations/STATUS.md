# Mosaic-AI – Status & Fahrplan

**Dieses Dokument traegt NUR Aktuelles und Offenes.** Neufassung vom 2026-09-13, 13:10
(Generationswechsel v28 -> v29, Skill Schritt 6); der vollstaendige Stand davor liegt in
`../archive/history.md`, Kapitel **"Vollstaendiger STATUS-Stand vom 2026-09-13 (vor der
Neufassung zum Generationswechsel v28 -> v29)"**, die Generationsberichte v24 bis v28 ebenfalls
dort.

**Pflegeregel:** wer einen Befund erzeugt, traegt ihn im selben Zug hier nach und prueft, ob
ein anderer Abschnitt dadurch falsch wird. Wer einen Strang abschliesst, schiebt die
Herleitung ins Archiv und laesst hier eine Zeile mit Verweis stehen.

**Dauerhaftes Prozesswissen steht NICHT hier**, sondern in `../docs/`: `generation_loop.md`,
`promotion_checklist.md`, `generation_naming.md`, `working_rules.md`, `pitfalls.md`,
`measured_runtimes.md`, `architecture_reference.md`, `engine_manual.md`.

---

## 1. WAS GERADE LAEUFT

**Die v29-Erzeugung, seit 2026-09-13 12:08.** Gestartet vom Nutzer in einem eigenen Fenster,
NICHT ueber die Sitzung (Lehre vom Harness-Stopp 2026-09-05). Skript
`tools/night_v29_generate.sh`, Generator `v28-b02`, drei Klassen nacheinander, alle bei
**100 Sims**, `MOSAIC_STACK_DRAW_RESEARCH=1`, Spec `models/start_by_search_on.spec.json`,
`--start-slot-random-p 0.15`:

| Klasse | Seed | Soll |
| --- | --- | --- |
| `v28-b02-policy` (Sockel, policy-aktiv) | 20260920 | 400 Dateien |
| `v28-b02-value-tempc` (Schwarm, temperiert) | 20260921 | 400 Dateien |
| `v28-b02-value-excursion` (Schwarm, Ausflug) | 20260922 | 401 Dateien |

Erwartet rund 10,8 h (Hochrechnung aus gemessenen Werten; v28 lief 9,92 h). Daneben laeuft der
Cache-Waechter unter der Trainings-Umgebung. **Nichts anderes darf Rechenlast erzeugen** --
kein Build, kein cargo, keine Sonde.

**Danach, in dieser Reihenfolge:**

1. **Tor 0 / Tor 2a je Klasse** (`corpus_sanity_check.py`, 271 s je Klasse gemessen).
2. **Offene Kleinigkeit der Sims-Kurve:** Plattenpunkte je Kriterium fuer die drei
   Teil-A-Laeufe nachfahren (das Kettenskript rief `plate_points_from_arena.py` ohne `--out`
   auf; je unter 5 s auf vorhandenen Logs).
3. **Cache-Bloecke und Monolithe aufraeumen** (`cache_inventory.py --orphans`, dann
   `--print-delete-list`): 4,2 GB in 8 Monolithen, 2,5 GB in rund 5.800 Bloecken. Die Waisen der
   heute geloeschten Korpora (v25-b01, Sims-Messdateien) sind darin. Braucht die Fensterliste
   der neuen Generation, deshalb erst jetzt.
4. **Kette v29 fahren**: `tools/night_v29_chain.sh` ist GESCHRIEBEN (2026-09-13, Syntax
   geprueft) und wartet selbst auf das Ende der Erzeugung -- Manifeste, G-2-Kennzahlen, Fenster
   (Seed 20260941), Bloecke, Monolith, Training v29-b01 mit Warmstart auf `v28-b02_brierbest`.
   Sie enthaelt Tor 0 und Tor 2a bereits als Schritt 1, Punkt 1 oben ist damit abgedeckt.
   **Starten wie die Erzeugung: in einem eigenen Fenster, nicht ueber die Sitzung.**
5. **Portable Build** (aus der Uebergabe vom 02:50, beim Neufassen zunaechst verloren
   gegangen): `python tools/build_release.py` nach
   `evaluations/review/portable_build_audit_2026-09-13.md` Abschnitt C. Die Spec ist auf
   v28-b02 umgestellt (Commit 3c81d0b). **Nur bei freier CPU** -- also NICHT neben der
   Erzeugung und nicht neben der Kette. Zip-Name und Weitergabe entscheidet der Nutzer.
6. **Zwei Bauten, die VOR ihrem jeweiligen Trainingsarm stehen** (Fahrplan Nr. 5 und Nr. 15),
   beide brauchen eine freie Maschine und ihre Tore:
   - **Wheel 2 fuer den Sicht-Arm v29-b03**: Encoder-Abschnitt 16 mit P.3, P.7, P.9 und
     P.11 bis P.15, Rust beide Pfade plus Python-Zwilling, `config.INPUT_SIZE` auf **794**
     (entschieden 2026-09-13, `PREREG_stack_top_feature.md` par.16), Sichtgleichheits- und
     Regressionstest, Fixture, Anker-Drift. Rund 2 h (ANNAHME).
   - **Ablations-Schalter `MOSAIC_SPECIAL_PLANES_OFF` fuer v29-b02** plus Tore
     (`PREREG_special_tile_yield.md`, Fahrplan Nr. 15).
7. Danach nach Fahrplan `evaluations/v29_program_agent_plan.md` (41 Punkte).

**FENSTER-PINNING nicht vergessen:** Streudateien, die waehrend der Erzeugung entstehen,
gehoeren beim Fensterbau in `MOSAIC_DATA_EXCLUDE`.

## 2. CHAMPION UND LEITER

**Champion laut `models/champion.txt`: `v28-b02_brierbest`** (Promotion 2026-09-12),
**Elo 1394 [1350, 1445]** aus 1.860 Partien im LEITERSEGMENT 2 (40 Kanten, Anker `hv4_anchor`
fix 1000, Block-Bootstrap). Generator der v29-Erzeugung ist dasselbe Netz.

Der Wert stieg am 2026-09-13 von 1353 auf 1394, weil drei neue Sims-Knoten unter dem
400er-Knoten einhaengen -- **kein neuer Staerkebefund**, sondern eine Folge der dichteren
Vernetzung. Neue Knoten: `v28-b02@100` 1298, `@200` 1289, `@600` 1389. Die Treppe
Anker -> hv4@600 -> v22@25 -> v22@100 -> v22@400 traegt.

**Eingefrorene Artefakte (nach dem Aufraeumen):** `frozen_champions/v28-b02` (amtierend,
Generator) und `v27-b01` (Vorgaenger, Champion-2-Kante); `frozen_heuristics/hv4_anchor`
(aktiver Anker), `hv2_generator` und `hv3_generator` (Sprossen, hv3 ist die Anfaenger-Stufe);
`models/restored_v22` (traegt den Leiterknoten v22-b05).

## 3. LAUFZEITEN (gemessen, Planungsgroessen; Details in `docs/measured_runtimes.md`)

| Aufbau | Dauer |
| --- | --- |
| Erzeugung 3 x 4.000 Partien @100, threads 11 (v27 / v28) | 10,25 h / 9,92 h |
| Argmax-Self-Play 200 Partien, threads 11, @100 / @400 / @600 | 791 s / 1.493 s / 2.113 s |
| Gepaarte Arena 75 Paare @100 gegen @400, threads 10, mit Logs | 1.121 s (7,5 s je Partie) |
| Gepaarte Arena 100 Paare @100 gegen @25 | 601 s (3,0 s je Partie) |
| Kette Schritte 1-6 (Kennzahlen, Manifeste, Fenster, Monolith) | rund 31 min |
| Training 12 Epochen, Fenster 2.947 Dateien | 5.117 s = 1,4 h |
| Gepaartes Gating 200 Paare @400, 10 Threads, mit `--log-games` | 86-91 min |
| Anker-Kante n=150 / Champion-2-Kante n=150 | rund 22 min / 43 min |
| Voller Build: Lib-Tests, no-run, Wheel, Install, Anker | rund 6 min |
| Anker-Drift / Konservierung | 15 s / 15 s |
| Tagesschnappschuss restic plus check | 6 s |

## 4. SPEC UND REZEPT

Champion-Spec `models/frozen_champions/v28-b02/spec.json`: `envelope_projection_mode` 1,
`envelope_search_c` 1,0, `envelope_flush_w` 0,0, `envelope_hull_form` 2, `special_row6_w` 1,0,
`score_utility_b` 20,0, Profil 1/0,92/0,67/0,33/0, `heuristik_variante` hv1.

**Die v29-Erzeugung faehrt `models/start_by_search_on.spec.json`** -- Feld fuer Feld dieselbe
Spec PLUS `start_by_search: 1` (verglichen 2026-09-13). Dazu in der Umgebung
`MOSAIC_STACK_DRAW_RESEARCH=1` und als Flag `--start-slot-random-p 0.15`.

**Engine seit Wheel 1 (2026-09-13):** P.10-Suchfix (die Wurzel-Determinisierung haelt den
oeffentlichen Typ der obersten Stapelplatte fest), Record-Feld `tiled_max_row` (P.14, wird auch
gelesen), Stapelzug-Knoepfe im Lauf-Manifest. Vertragshash `39648b95bbba1acf` unveraendert,
`input_size` 755. Netz-Paritaets-Fixture bewusst neu: `4750ffc6ec094a83`.

## 5. PREREG-BESTAND (11 OFFEN laut Index 2026-09-13, Ziel rund 7)

`python tools/generate_prereg_index.py` haelt `evaluations/PREREG_INDEX.md` aktuell; Stand
119 Dateien = 11 OFFEN + 96 ENTSCHIEDEN + 12 UEBERHOLT. Die elf offenen sind alle aktiv
eingetaktet, keine ist liegengeblieben:

| Prereg | Was noch aussteht |
| --- | --- |
| `v29_window` | der laufende Zyklus selbst |
| `stack_top_feature` | Sicht-Arm v29-b03 (Wheel 2, INPUT_SIZE 794), dazu die zwei Regelbefunde par.16/16a |
| `special_tile_yield` | Ablations-Schalter und Arm v29-b02 |
| `difficulty_levels` | Bau waehrend der Erzeugung, Kanten nach Tor 1 |
| `claude_play_interface` | Partien g08-g10, Zugklassen-Differential |
| `corpus_behaviour_audit` | Werkzeug ungebaut, Korpuslauf danach |
| `moon_stack_order` | Knopf bauen, A/B am Champion |
| `dome_return_order` | A/B Modus 1 gegen 0 ueber den Referee |
| `round_estimate_leaf_term` | Kostentor K4, dann argmax und A/B; Skalenwahl offen |
| `round_transition_search_sampling` | Variante B bauen (rund ein Tag), Sichttor, Kostentor, A/B |
| `code_cleanup_closeout` | Stufen 2 und 3, nach der v30-Promotion |

Die Zahl liegt ueber dem Ziel, weil das v29-Begleitprogramm bewusst breit ist; nach den
Verdikten von `moon_stack_order`, `dome_return_order`, `round_estimate_leaf_term` und
`round_transition_search_sampling` sollten es rund sieben sein.

## 6. OFFENE NUTZER-ENTSCHEIDE

1. ~~G-2-Haelfte des v29-Fensters~~ **ENTSCHIEDEN 2026-09-13, 13:20** (Nutzer: "Nimm fuer die
   g-2 das selbe was wir auch bei v28 hatten"): die AUSFLUG-Haelfte
   `selfplay_v26-b01-value-excursion_*`, 145 Dateien seed-gezogen mit 20260941. In
   `PREREG_v29_window.md` par.2 registriert und in `tools/night_v29_chain.sh` gesetzt; die 401
   Quelldateien liegen vollstaendig im Baum.

2. **Manifest meldet Spec-Felder falsch** (geprueft 2026-09-13): `engine_config` zeigt fuer
   `envelope_search_c`, `envelope_projection_mode`, `envelope_hull_form` und `special_row6_w`
   den Env-Default statt des wirksamen Spec-Werts, weil `lib.rs` Z.801/807/812/815
   `SearchConfig::from_env()` lesen. **Kein Belegverlust** -- die Spec-Datei hat genau einen
   Commit und ist unveraendert, jedes Manifest nennt ihren Pfad in `cli_args.spec`.
   **Vorschlag: Spec-Inhalt plus sha256 additiv ins Manifest** (`selfplay_manifest.py`), damit
   der Beleg nicht an der Unveraenderlichkeit einer Datei haengt. Nicht waehrend eines Laufs
   bauen: die Chunk-Prozesse importieren frisch.

3. **Sichtluecke bei den gezogenen Stapelplatten -- zwei Kanaele, zwei Reparaturen**
   (`PREREG_stack_top_feature.md` par.16 und par.16a). Die Vorderseiten sind nach Regelauskunft
   erst NACH dem Aufhoeren bekannt. (a) Die Aktionsliste verraet sie ueber die
   designabhaengige Rotationsfilterung (`game.rs` Z.402) -- betrifft die Suche, Reparatur
   beruehrt `NUM_ACTIONS`. (b) `serialize.rs` Z.375-379 serialisiert sie sofort, die Anzeige
   druckt sie (`claude_play.py` Z.721) und die Platzierungs-Vorschau rechnet damit (Z.597/656)
   -- betrifft den menschlichen Spieler, live eingetreten in Partie g07. Umfang und Prioritaet
   sind offen; beruehrt die Gueltigkeit von g02-g07.

4. **Cache-Bloecke und Monolithe** (knapp 7 GB): Waisen-Inventar nach der Erzeugung, Liste
   dann zur Freigabe.

5. **`-Deep`-Lauf der Backup-Verifikation**: `verify_backup.ps1` empfiehlt ihn vor der ersten
   Loeschung; am 2026-09-13 auf Nutzer-Entscheid nicht gefahren.

6. ~~Textverweise auf `hv1_anchor` nachziehen~~ **ERLEDIGT 2026-09-13, 13:35** fuer die
   Stellen, die aktiv fehlleiteten: CLAUDE.md (Anker-Invarianz nennt jetzt `hv4_anchor` als
   Fixpunkt seit der Neuverankerung), `docs/working_rules.md`, `docs/architecture_reference.md`,
   `docs/generation_naming.md`. **Offen und ein echter Befund:** drei Sonden greifen direkt auf
   das geloeschte Artefakt zu und laufen nicht mehr --
   `tools/probes/anchor_referee_parity_probe.py`, `frozen_agent_referee_probe.py`,
   `frozen_worker_protocol_probe.py`. Sie tragen jetzt einen Hinweis statt eines kryptischen
   Abbruchs. Eine Umstellung auf `hv4_anchor` braucht NEUE Erwartungswerte (die hartkodierten
   gelten fuer hv1, z. B. `scores [27, 15], steps 159`), also einen Lauf -- Nutzer-Entscheid, ob
   das lohnt oder ob die drei als historisch entfallen. Verweise, die bewusst die VERGANGENHEIT
   beschreiben (`docs/promotion_checklist.md` Z.34, die Historien-Kommentare in
   `tools/elo_tracker.py`, das Beispiel in `tools/freeze_heuristic.py`), bleiben unveraendert.

7. **Skala des Rundenschaetzers** (`round_estimate_leaf_term`): Vorschlag (a) je Runde,
   (b) 9,25 auf Zuruf. Aus dem v28-Programm uebernommen, unveraendert offen.

8. **Rahmen (ENTSCHIEDEN 2026-09-12, hier als Erinnerung):** v30 wird released und ist der
   Projektabschluss, Schlussmodell heisst **Tessa**. v29 traegt das Begleitprogramm, v30 nur
   noch Rezept-Knoepfe.

## 7. VERBOTE UND STEHENDE REGELN

- **Kein Push ohne Anweisung.** Stand 2026-09-13, 13:10: **30 Commits vor origin/main**, der
  Nutzer pusht selbst.
- **Loeschung nur auf pfadgenaue Freigabe**, mit restic-Beleg je Gruppe.
- **Messungen laufen exklusiv.** GPU und CPU duerfen parallel, zwei CPU-Messungen nie; ein
  Build zaehlt als Last.
- **Nie committen:** `player_profiles.json`, `player_profiles.json.bak`,
  `models/manifest_train_v28-b0*.json`, `evaluations/game_analysis/*`.
- **Dateien laufender Laeufe nicht anfassen** -- auch nicht `self_play.py`,
  `selfplay_manifest.py`, `config.py`, `engine/py/neural_net.py`, `corpus_dataset.py`: die
  Chunk-Prozesse importieren frisch.
- **Regel 0**, Prereg-Kopf im selben Zug wie das Ergebnis, Laufzeiten ins Artefakt, kein
  Geviertstrich in Dateien, Bezeichner englisch.

## 8. BEFUNDE, die eine Nachschau brauchen

- **Nicht-Transitivitaet am Leiterboden:** v22@25 gegen hv4@150 76 %, gegen hv4@600 50 %,
  hv4@600 gegen hv4@150 55 %. Bradley-Terry mittelt das.
- **Replayer-Grenze Chip-Vollendung:** einzelne Partien nicht nachspielbar ("Reihe N nicht mit
  Chips komplettierbar" nach 60 Versuchen); bekannte Grenze.
- **GUI und Arena: gleicher Suchweg, andere Suchtiefe** (geprueft 2026-09-13,
  `PREREG_difficulty_levels.md` par.11). Beide enden in `select_final_root_child`, beide ohne
  Wurzelrauschen, und `server.py` schreibt die Champion-Spec beim Start in die Umgebung, weil
  der GUI-Pfad sie von dort liest. ABER: die Arena misst bei 400 Sims, der Server faehrt 300
  oder je nach Preset 100 -- nach der Sims-Kurve sind das 45:105 im direkten Duell. Das Netz
  in der GUI ist also schwaecher als das im Register. Fuer die Stufenleiter ist der Regler
  damit beziffert. **Latente Sollbruchstelle:** die Arena zieht `builder_drafting_preference`
  der Suche vor, der Serverpfad kennt den Vorzug nicht; folgenlos nur, solange
  `MOSAIC_SPALTENBAU`/`MOSAIC_PLATTENBAU` unbesetzt bleiben.
- **Gating-Artefakte tragen keine Engine-Konfiguration** (`paired_gating.py`): ein Env-Knopf,
  der in einer Arena an war, ist dort nachtraeglich nicht belegbar.
- **`MOSAIC_ENVELOPE_REACH_W` und `_SLOT_W`** haben keine Spec-Entsprechung. Heute inert, weil
  das Rezept Projektionsmodus 1 faehrt; bei Modus 2 oder 4 waeren sie exakt der
  Stack-Draw-Fall.
- **Sims und Spaltenbau:** die Kurve am Champion faellt ueber 100-600 Sims monoton, und zwar
  allein ueber die VOLLENDUNG -- die Teilspalten bleiben gleich
  (`PREREG_search_depth_column_optimum.md` par.8e).
- `player_profiles.json` im Arbeitsbaum veraendert (Server-Seite), nicht committet.
