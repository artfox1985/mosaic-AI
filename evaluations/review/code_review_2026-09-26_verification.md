# Nachpruefung Code-Review 2026-09-26

- Datum: 2026-09-26
- Review-Stand: `3887069` (laut Auftrag sind `engine/` und `server.py` seitdem unveraendert; Zeilennummern unten sind die des heutigen Arbeitsbaums)
- Methode: **nur lesend geprueft** (Read/Grep/Glob). Kein Build, kein Test, kein Python-Lauf, kein Server; auf der Maschine lief waehrenddessen die v33-Kette (`evaluations/STATUS.md:36-39`).
- Regel 0: jede Aussage hat eine Pruefstelle `datei:zeile` oder ist als [UNGEPRUEFT] / [HERLEITUNG] markiert. Das Review ist eine Behauptung; Urteile unten beziehen sich auf den Code, nicht auf das Review.

**Querschnitt "Panic faengt server.py nicht":** dass eine PyO3-`PanicException` von `BaseException` erbt und darum an `except Exception` vorbeigeht, steht im Baum nur als Behauptung (`server.py:331`, `evaluations/review/code_review_2026-09-11_engine_core.md:81`); die pyo3-Quelle liegt nicht im Projekt. [UNGEPRUEFT an der pyo3-Quelle]. Was danach mit dem Flask-Prozess passiert ("beendet den Prozess", `server.py:331`), ist ebenfalls [UNGEPRUEFT].

## Uebersicht

| # | Urteil | Pruefstelle(n) | wirkt im aktuellen Rezept? | Fix-Skizze | Anker-Invarianz |
| --- | --- | --- | --- | --- | --- |
| 1 | BESTAETIGT (Kern); Folge "Deadlock-Panic" WIDERLEGT | `game.rs:36-60`, `:62-69`, `:203-261`, `:263-313`, `:1061-1083`, `:460-462`, `py.rs:303-320`, `:349-386` | nur GUI/API | Rotation in beiden Validatoren pruefen; in `execute_*` erst rotieren (auf Kopie), dann entnehmen | Pflicht (Engine), erwartet gruen |
| 2 | BESTAETIGT inkl. ◐ | `py.rs:528-543`, `round_end.rs:87-99`, `server.py:1157-1167`, `engine_manual.md:131-142` | nein (GUI ruft es nicht auf) | `check_player_row`, Phase/Seite pruefen, nur `find_unplaceable_rows`, Phantom-Abzug ueber gemeinsame Hilfsfunktion; oder Endpunkt entfernen | Pflicht, gruen |
| 3 | BESTAETIGT inkl. ◐ | `py.rs:570-581`, `scoring.rs:42-49`, `:60-85`, `:129-146` | nur GUI | ids in 0..8, paarweise verschieden, nur vor dem ersten Zug | Pflicht, gruen |
| 4 | BESTAETIGT | `py.rs:100-110`, `state.rs:580-586`, `server.py:672-681` | nur GUI/API | `first_player` pruefen, `new` als `PyResult` | Pflicht, gruen |
| 5 | BESTAETIGT | `validation.rs:66-113`, `:214-230`, `execution.rs:59-81`, `py.rs:44-46`, `engine_manual.md:104-106` | nur GUI/API | Mond-Entnahme nur global zulassen (Teilformen ablehnen) | Pflicht, gruen |
| 6 | BESTAETIGT (Semantik); keine Messkette betroffen | `game.rs:852-854`, `:1258-1263`, `state.rs:15`, `:579`, `py.rs:237`, `:942`, `:1101`, `:1228`, `:1288-1312`, `gui_node_gate_smoke.py:100/126/134` | nein (nur py.rs-Ausgabe, Sonde, Test) | `is_over` = Phase End/Final; `game.rs:1258` auf expliziten Rundentest umstellen | Pflicht, gruen wenn `:1258` erhalten |
| 7 | TEILWEISE (Referee prueft doch) | `game.rs:898-924`, `:1092-1102`, `server.py:1080-1084`, `referee.rs:849`, `:911-967`, `game.rs:1686-1700` | nein (Server und Referee pruefen) | Pass nur, wenn `drafting_actions == [Pass]`; Test `pass_writes_its_own_log_line` anpassen | Pflicht, gruen |
| 8 | BESTAETIGT (Mechanismus); "in keiner Spec" WIDERLEGT | `net_mcts.rs:6227-6297`, `:6113-6123`, `:4102`, `:5483-5488`, `:2058-2066`, `state.rs:294-302`, `models/moon_order_post2.spec.json:21` | nein im Rezept; ja in drei Diagnose-Specs | Folgezustand aus Sicht des ZIEHENDEN determinisieren, nicht aus der des Gegners | Pflicht formal, gruen |
| 9 | BESTAETIGT | `mcts.rs:489-506`, `:251`, `:258-269`, `:562-571`, `self_play.rs:3403-3428`, `net_mcts.rs:1974`, `:2046` | **ja: jede Elo-Kante gegen `hv4_anchor`** | Wurzel-Determinisierung wie im Netzpfad | **erwartet ROT: Nutzer-Entscheid** |
| 10 | BESTAETIGT | `server.py:1479-1491`, `py.rs:604-607`, `serialize.rs:790-799` | nein (kein Aufrufer) | Route und Bindung entfernen | Pflicht (py.rs), gruen |
| 11 | BESTAETIGT, doppelt latent | `net_mcts.rs:3178-3194`, `net_batcher.rs:227-236`, `:3012-3022`, Specs `score_utility_c 0.0` | nein | `opp`-Spalte durchreichen oder `None`, sobald ein Verbraucher sie braucht | gruen |
| 12 | BESTAETIGT | `net_ort.rs:153-212`, `Cargo.toml:44`, `lib.rs:36`, `engine/pyproject.toml:13` | nein (Feature nicht im Wheel) | Schluessel um `onnx_path` erweitern oder `Arc` halten | nein |
| 13 | BESTAETIGT, mit Einordnung | `self_play.rs:3787-3794`, `:4283-4320`, `:6262`, `round_transition.rs:445-515`, `round_transition_deep.rs:452-554`, `:611-674`, `:802-866` | **ja: jede Netz-Self-Play-Partie** (Bootstrap-Pfad), rtv aus | Label-Sampling aus eigenem abgeleiteten Strom | gruen (Arena hat `labels: None`) |
| 14 | BESTAETIGT (Mechanismus); teils Absicht, kein Sichtdefekt | `self_play.rs:4188`, `:6586-6621`, `supply.rs:37-40`, `state.rs:338-350`, `PREREG_start_position_seeding.md:530-538`, `:934-937` | **ja: Klasse `value-excursion`** | optional: verdeckte Bestaende des Abzweig-Klons mit `ex_rng` neu mischen | gruen |
| 15 | BESTAETIGT, harmlos | `net_batcher.rs:272-311`, `:216-224` | nein (Knopf aus) | keiner noetig; dokumentieren | nein |
| 16 | BESTAETIGT (Code), praktisch nie ausgeloest [Code-Kommentar] | `self_play.rs:361-365`, `:5790-5829`, `night_v33_chain.sh:44`, `corpus_dataset.py:1635-1659` | Pfad `:5822` ja, Ausloesung nie beobachtet | EIGENE Record-Flagge + Maske (ptv reicht nicht, IGNORE_PTV=1) | gruen |
| 17 | BESTAETIGT; Referee nicht betroffen | `serialize.rs:1243-1245`, `:1428-1444`, `:1755`, `referee.rs:141/196/226/253`, `features.rs:581`, `self_play.rs:6464` | nein (Seeding aus) | `first_player_next_round` lesen, wenn vorhanden | gruen |
| 18 | BESTAETIGT | `export_onnx.py:109-113`, `:208-213`, `train.py:2691-2710` | **ja: Export am Ende des laufenden Trainings** (nur bei Architektur-Abweichung schaedlich) | Rueckgabe von `load_state_dict` auswerten, bei fehlenden/verworfenen Keys abbrechen | nein |
| 19 | BESTAETIGT | `tools/hooks/pre-push:137-157`, `:161`, `:221-252` | nein (Push-Pfad) | `"`-Zeilen nicht als Logtext werten; `NUR_LOGTEXT` ueber Refs UND-verknuepfen | nein |
| 20 | BESTAETIGT (Herleitung), latent | `tools/elo_tracker.py:396-421`, `:445-493`, `:527-534`, `:151`, `:174` | nein (keine Sweep-Kante im Register) | Konvergenz statt 500 Iterationen; Sweep-Kanten markieren, Breite 0 als "degeneriert" | nein |
| 21 | BESTAETIGT | `server.py:66-72`, `:1879-1888` | GUI | `debug` per Env, CORS auf localhost | nein |
| 22 | BESTAETIGT | `server.py:273-296`, `:111`, `:687-689`, `:649-650` | GUI | Modellnamen gegen Liste, `sims` deckeln, `_ai_lock` benutzen oder loeschen | nein |
| 23 | BESTAETIGT, einer praezisiert | `train.py:2520`, `:2599`, `:2654`, `:2678`, `corpus_io.py:73-85`, `file_cache_key.py:156-222`, `self_play.py:282-283`, `:369-400`, `self_play.rs:6335-6346`, `:6555-6563` | ja (Erzeugung/Training) | atomare Writes, Ueberschreib-Waechter, Inhalt im Schluessel, Panic ehrlich melden | nein |

## Befunde im Einzelnen

### 1. Kuppel-Rotation: Zustand vor Validierung geaendert

- Ablage-Pfad: `execute_dome_move` entnimmt die Platte (`game.rs:68`) und rotiert erst danach (`:69`). `validate_dome_move` (`game.rs:36-60`) prueft die Rotation nicht; der Kommentar `game.rs:87-92` sagt das selbst. `apply_rotation` lehnt alles ausser 0/90/180/270 ab (`dome.rs:168-173`). Scheitert `:69`, verlaesst `?` in `game.rs:1072` den Dispatcher VOR `pending_dome_choice = None` (`:1082`): Platte weg, Wahl haengt.
- Startsetzung (`game.rs:603-610`): gleiche Reihenfolge, dazu wird die Luecke schon vom Stapel nachgezogen (`:604-609`), bevor `:610` scheitert. Ebenfalls bestaetigt (war schon vom Koordinator gesehen).
- Stapel-Pfad `:313`: schlimmer als die Ablage. `execute_draw_from_stack` leert `pending_stack_draw` per `mem::take` (`:265`), legt den Rest schon unter den Stapel (`:291-311`) und rotiert erst in `:313`. `validate_draw_from_stack` (`:203-261`) prueft die Rotation ebenfalls nicht. Folge bei Fehler: gewaehlte Platte verloren, Ziehstapel leer, `pending_dome_choice = FromDrawStack` haengt.
- Erreichbarkeit: `py.rs:303-320` (`/api/move/dome`, `server.py:963` reicht `rotation` ungeprueft durch) und `py.rs:349-386` (`/api/move/dome_stack_choose`, `server.py:1018-1020`). Interne Pfade erzeugen nur 0/90/180/270 (`game.rs:99`, `:384`), Self-Play/Arena sind also nicht betroffen.
- ◐-Folge: "Endlos-Paesse" BESTAETIGT, "bis Deadlock-Panic" WIDERLEGT. Nach dem Fehler findet `drafting_actions` keine Rotation mehr (Validator scheitert an der fehlenden Platte bzw. am leeren Ziehstapel) und liefert `[Pass]` (`game.rs:781-798`); `apply_drafting` laesst bei offener Wahl nur Rotation oder Pass zu (`:910-916`), Pass wechselt nur den Spieler (`:1092-1102`). Die Panic in `check_drafting_complete` (`:560-561`) wird nie erreicht, weil `current_player_can_move` bei offener Wahl immer `true` meldet (`:460-462`); vorher bricht `:536-537` schon ab, solange Fabriken nicht leer sind. Die Partie haengt also stumm in einer Pass-Schleife.

### 2. `move_row_to_floor`

- `py.rs:528-543`: kein `check_player_row` (den gibt es, `py.rs:428-436`, andere Bindungen nutzen ihn), keine Phasen- oder Seitenpruefung. `players[2]` bzw. `pattern_lines[9]` (6 Reihen, `board.rs:288`) sind Index-Panics. Die Route `server.py:1157-1167` prueft ebenfalls nichts.
- ◐ Phantom: BESTAETIGT. Der Rundenabschluss zieht Phantom-Fliesen ab und setzt den Zaehler zurueck (`round_end.rs:92-99`); `move_row_to_floor` schiebt alle `tiles` auf die Strafleiste und laesst `phantom_count` stehen (`py.rs:530-536`). Phantome entstehen bei Chip-Vervollstaendigung (`round_end.rs:669`).
- Regelbezug: eine freie "Reihe auf die Strafleiste"-Aktion kennt das Handbuch nicht; platzierbare Reihen MUESSEN gelegt werden, unplatzierbare fallen automatisch (`engine_manual.md:131-142`, automatisch in `game.rs:1131-1145`).
- Reichweite: im Frontend ist `tilingMoveToFloor` definiert, aber nirgends aufgerufen (`static/js/app.js:738`, einziger Treffer); Aufrufer ist `tools/claude_play.py:974`.

### 3. `select_scoring`

- `py.rs:570-581` prueft nur Laenge 3 und Ausschlusspaare (`scoring.rs:81-85`). Die Katalog-IDs sind 0 bis 7 (`scoring.rs:42-49`).
- ◐ `[1,1,1]` wertet dreifach: BESTAETIGT, `calculate_end_scoring` iteriert ungefiltert (`scoring.rs:131-145`). Zusatz: unbekannte IDs werden still uebersprungen (`:132-135`), `[8,9,10]` heisst also "keine Endwertung".
- Keine Phasenpruefung: jederzeit aufrufbar, auch mitten in der Partie.

### 4. `first_player`

- `py.rs:100-110` nimmt `first_player: usize` ungeprueft, `Game::start` -> `setup_new_game` indiziert `players[first_player]` (`state.rs:586`) -> Panic im Konstruktor (`new` gibt `Self`, kein `PyResult`). Server: `int(fp_raw)` ungeprueft (`server.py:672-673`). Nebenbefund: `ai_side` ebenfalls ungeprueft (`server.py:688`).

### 5. Teil-Mond-Entnahmen

- `validate_small_moon` mit `factory_id` prueft nur diese eine Fabrik (`validation.rs:66-85`), `validate_large_moon` nur den GF-Pool (`:101-113`). Der Generator erzeugt ausschliesslich die globale Form (`validation.rs:214-230`). Handbuch 4C: "every topmost tile of one chosen colour across the moon areas of all factories at once" (`engine_manual.md:104-106`). Der Kommentar `execution.rs:59-81` benennt die Luecke. Erreichbar ueber `apply_stone` mit `"SMALL_FACTORY_MOON"` + `factory_id` bzw. `"LARGE_FACTORY_MOON"` (`py.rs:44-46`, `:268-294`). Der Referee-Worker kann es nicht, er ist auf `drafting_actions` beschraenkt (`referee.rs:911-967`).

### 6. `is_over()` in ganz Runde 5 wahr

- `is_over` = `round_number >= NUM_ROUNDS` (`game.rs:852-854`), `NUM_ROUNDS = 5` (`state.rs:15`), Runden 1-basiert (`state.rs:579`). Also wahr ab Beginn von Runde 5.
- **Alle Aufrufer** (Grep `.is_over()` ueber `engine/` und `*.py`):
  - `game.rs:1258`: am RUNDENENDE nach dem Tiling, dort ist die Bedingung RICHTIG (nach Runde 5 -> `Phase::End`, sonst `next_round`). Diese Stelle darf ein Fix nicht mitaendern.
  - `py.rs:237` (Python-Export), `:942`, `:1101`, `:1228` (`"done"`-Feld der KI-Schritte).
  - `py.rs:1288`, `:1312`: Test `debug_endpoints_leave_game_rng_untouched` spielt nur bis Runde-5-Beginn; er bleibt gruen, testet Runde 5 aber nicht.
  - `tools/probes/gui_node_gate_smoke.py:100/126/134`: bricht zu Beginn von Runde 5 ab und meldet `over: true`.
- **Keine Messkette betroffen:** Self-Play und Arena pruefen `game.state.phase == Phase::End` (`self_play.rs:4471`, `:5024`, `:5629`, `:6981`, `:7180`), der Referee ebenso (`referee.rs:986`); `tools/` ruft `is_over` nur in der genannten Sonde (Grep). Das Frontend liest `done` nicht (Grep `\.done` in `static/`: 0 Treffer); `server.py:1602` reicht es nur durch. Eine abgeschnittene Runde 5 in Self-Play, Arena oder Referee gibt es also NICHT.

### 7. Pass ohne Abgleich

- Engine: bestaetigt, `Action::Pass` wird bedingungslos angenommen (`game.rs:1092-1102`), und die Pending-Waechter lassen Pass ausdruecklich durch (`:898-924`).
- Server prueft vorher (`server.py:1080-1084`). **Referee prueft doch:** der Worker-Pfad matcht gegen `drafting_actions` und verweigert Unbekanntes (`referee.rs:911-967`), der In-Process-Pfad waehlt aus `drafting_actions` (`referee.rs:849-861`). Ungeprueft rufen nur `tools/claude_play.py:964` und der Replayer `tools/analyze_game_log.py:617` (dort gewollt).
- Achtung beim Fix: der Test `pass_writes_its_own_log_line` passt in der Eroeffnung von Runde 1, wo Steinzuege legal sind (`game.rs:1686-1700`), und haengt damit am heutigen Verhalten.

### 8. `moon_order_post_search`: Determinisierung aus der falschen Sicht

- Mechanismus BESTAETIGT: der Folgezustand `next` hat den GEGNER am Zug (`net_mcts.rs:6113-6123`) und geht an `build_net_tree` (`:6276-6278`). Mit `USE_GUMBEL_SEARCH = true` (`:4102`) laeuft `build_gumbel_tree`, das an der Wurzel `determinize_hidden_information` ruft (`:5483-5487`), und die nimmt `viewer = state.current_player` (`:2065`). `determinize_dome_pool` laesst Bloecke mit `returner == viewer` ungemischt (`state.rs:300-302`). Aus Sicht des Ziehenden heisst das: die Rueckgabebloecke des Gegners stehen in ECHTER Reihenfolge (Orakel), sein eigener Block wird gemischt (Wissensverlust). Der PUCT-Zweig determinisiert gleich (`:5842-5844`). Verdeckte Chips werden unabhaengig vom Betrachter gemischt (`:2085-2104`), dort kein Leck.
- Tor: nur bei `moon_order_variants == 2` UND `moon_order_search_sims > 0` (`:6154-6167`); Default 1 (`:393`).
- **Korrektur zur Koordinator-Pruefung:** "in keiner Spec gesetzt" stimmt nicht. `models/moon_order_post2.spec.json:21`, `models/moon_order_scale0.spec.json:21`, `models/moon_order_scale1.spec.json:21` tragen `"moon_order_variants": 2`. Das sind Diagnose-Specs der Stufe 3 aus `PREREG_moon_stack_order.md`; das aktuelle Rezept faehrt 1 (Generierungs-Spec ohne Feld, `models/v32_generation.spec.json`; Trainingsmanifest `manifest_train_v33-b01_20260926_090647.json:88`). Folge: der registrierte Stufe-3-Nullbefund (`PREREG_moon_stack_order.md:1`) ist unter diesem Defekt gemessen.
- Die Liste "Wo der Code Information ABSICHTLICH vernichtet" fuehrt die Stelle nicht; ihre Zeile zur Wurzel-Determinisierung (`docs/architecture_reference.md:114`) setzt voraus, dass `current_player` der Suchende ist, und genau das gilt hier nicht.

### 9. Heuristik-MCTS determinisiert nicht

- BESTAETIGT: `build_tree` klont den echten Zustand (`mcts.rs:501-506`), `determiniz` kommt in `mcts.rs` nicht vor (einziges `shuffle` ist Zugreihenfolge, `:323`). Expansion ueber `apply_drafting` auf dem echten Zustand (`:258-269`, `:562-571`), Kandidaten aus `drafting_actions` (`:251`), also inklusive `DrawStackPeek`, wenn legal.
- ◐ Stapel: BESTAETIGT als Mechanismus. Ein Peek im Baum zieht die echte oberste Platte; `net_mcts.rs:5909-5920` beschreibt genau diesen Vorgang als Orakel-Problem. Im Netzpfad ist das In-Baum-Mischen aus (`SHUFFLE_STACK_PEEK_IN_SEARCH = false`, `:1974`), dort ist aber schon die Wurzel determinisiert (`DETERMINIZE_ROOT_HIDDEN_INFO = true`, `:2046`). Die Heuristik hat keins von beiden: asymmetrisch.
- ◐ Chips: dass eine im Baum geleerte Fabrik den ECHTEN verdeckten Chip aufdeckt, folgt aus `reveal_chip_if_empty` auf dem echten Zustand (`execution.rs:145-149`). Ob die Heuristik-Bewertung die Chip-Farben dann auch nutzt, ist [UNGEPRUEFT].
- Reichweite: jede Heuristik-Seite in der Arena geht ueber `heuristic_arena_choose_action` -> `mcts::search_drafting_action_with_variant` (`self_play.rs:3403-3428`), also auch der Elo-Anker `hv4_anchor`. Eine Reparatur bewegt den Anker (STATUS vermerkt das schon als Nutzer-Entscheid, `evaluations/STATUS.md:80`).

### 10. `/api/stack/peek`

- BESTAETIGT: kein Guard (`server.py:1479-1491`), gibt die obersten n verdeckten Platten mit Vorderseite aus (`serialize.rs:790-799` ueber `py.rs:604-607`). Aufrufer: keiner in `static/` (dort nur `/move/dome_stack_peek`, `app.js:2777`), keiner in `tools/` (Grep).

### 11. `try_batched_pair_ex` verwirft `opp_points`

- BESTAETIGT: `net_mcts.rs:3191-3193` gibt `Vec::new()` statt `_oppa` zurueck. Doppelt latent: (a) nur unter `MOSAIC_INTERLEAVE_ENABLED` (Default aus, `net_batcher.rs:227-236`), in keiner Kette/Spec gesetzt (Grep: nur Doku, Preregs, `engine/examples/self_play_throughput_probe.rs`); (b) K1 braucht `score_utility_c != 0` (`net_mcts.rs:3013-3015`), beide aktuellen Specs tragen 0.0 (`models/v32_generation.spec.json:13`, `models/v33_gating.spec.json:4`); Denial-Tiebreak Default aus (`knob_registry.rs:90`). Ob der Sammel-Faden die sechste Spalte tatsaechlich fuellt (Kommentar `:3161-3162` gegen `:3171-3176`), ist [UNGEPRUEFT].

### 12. ORT-Session-Registry

- BESTAETIGT, und anders gelagert als #15: der Schluessel ist der rohe `Net`-Zeiger (`net_ort.rs:201`), die Registry haelt KEINE Referenz auf das `Net`. Wird ein `Net` freigegeben und ein anderes an derselben Adresse angelegt, bekaeme es die Session des alten Modells [HERLEITUNG]. Nur mit Feature `ort_cuda_probe` (`Cargo.toml:44`, `lib.rs:36`); der Wheel-Bau setzt es nicht (`engine/pyproject.toml:13`).

### 13. Label-Sampling mit Wanduhr und Partie-RNG

- **Welcher RNG:** der Partie-RNG. `unified_game_loop` bekommt `rng` und dokumentiert ihn als zustaendig fuer "`Game::start`, `EndTiling`-Refill, Label-Sampling" (`self_play.rs:3787-3794`); die Label-Aufrufe nutzen genau diesen (`:4294`, `:4298`, `:4308`, `:4316`).
- **Aktiv im Rezept:** ja. `labels` ist im Netz-Self-Play immer gesetzt (`self_play.rs:6262`). `record_rtv` ist aus (kein `--rtv` in `tools/night_v33_generate.sh:66-85`, Default `self_play.py:889`), aber der Bootstrap laeuft "unabhaengig davon immer mit" (`self_play.rs:4286-4319`) und ist Teil des nortv-Ziels. Arena und Gating setzen `labels: None` (`self_play.rs:5221`, `:5363`).
- **Mechanismus:** `bootstrap_value_after_rounds` (`round_transition_deep.rs:802-866`) laeuft ueber `sample_round_transition_value` (Deadline-Pruefung `round_transition.rs:467-472`) und `simulate_one_round` (`round_transition_deep.rs:658-660`), darin `choose_drafting_action_pruned` mit Gesamt-Deadline (`:499-508`) und Gamma-Samples mit eigener Deadline (`GAMMA_SAMPLE_TIME_BUDGET` 5 s, `:283`, `:589`). Die "ehrlichen Deckel" machen den WERT bei Feuern deterministisch (`round_transition.rs:456-465`, `round_transition_deep.rs:477-485`), aber nicht die ANZAHL der gezogenen Zufallszahlen: bricht eine Schleife ab, hat sie weniger gezogen. Danach treibt derselbe RNG den `EndTiling`-Refill der naechsten Runde. Unter Nebenlast kann die Partie also ab Runde 2 eine andere werden [HERLEITUNG]. Dazu: die Negamax-Deadline (2 s, `:221`, `:376-383`) aendert bei Feuern den Wert und damit ggf. die Rollout-Zugwahl, ohne Fallback [HERLEITUNG].
- `PREREG_search_rng_split.md` trennt den SUCHstrom ab; den Label-Strom behandelt es nicht (Grep dort: keine Label-/Deadline-Treffer ausser Kontextzeilen).
- **Einordnung:** die Deckel sind grosszuegig (150 s, 200 s, 5 s, 2 s; `round_transition_deep.rs:221-254`, `:283`), und `PREREG_deterministic_labels.md:1` meldet "Stress-Abnahme byte-identisch bestanden, 0 Not-Deckel-Feuerungen". Real ist das Risiko nur bei starker Drosselung; die v33-Erzeugung lief exklusiv. Beweisen laesst sich die Reproduzierbarkeit eines bestimmten Laufs nur ueber `NOT_DECKEL_STATS` (`round_transition.rs:384-443`), ob die Erzeugung sie protokolliert, ist [UNGEPRUEFT].

### 14. Ausflug erbt die verdeckte Welt

- Mechanismus BESTAETIGT: der Abzweig ist ein roher Klon (`self_play.rs:4188`), der Ausflug startet daraus mit eigenem `ex_rng` (`:6586-6621`). `Bag::draw` nimmt ohne RNG vom Anfang (`supply.rs:37-40`); erst eine Turm-Nachfuellung mischt mit dem (dann anderen) RNG (`state.rs:338-350`). Beutelfolge bis zur ersten Turm-Nachfuellung, Kuppelstapel und Chip-Vorrat sind also identisch.
- **Absicht oder Defekt?** Beides nicht ganz. Absicht ist der gemeinsame VORLAUF: "gepaartes Gegenstueck mit gemeinsamem Vorlauf" (`PREREG_start_position_seeding.md:934-937`), die Korrelation ist als Einwand benannt ("fuer das TRAINING kein Fehler", `:530-538`). Die gemeinsame verdeckte ZUKUNFT steht dort nicht (Grep "Beutel"/"verdeckt": 0 Treffer). Kein Sichtdefekt: die Spieler sehen die verdeckte Welt nicht (Wurzel-Determinisierung der Suche). Es ist eine statistische Kopplung: Haupt- und Ausflugspartie teilen den Zufall, die Wertziele sind staerker korreliert als der Vorlauf allein erklaert. Fuer die Paardifferenz ist das eine Varianzreduktion ("common random numbers") [HERLEITUNG], fuer den Value-Kopf sind es weniger unabhaengige Stichproben.
- Aktiv: Klasse `value-excursion` (`tools/night_v33_generate.sh:81-85`), dazu G-1/G-2-Ausfluege im Fenster (`tools/night_v33_chain.sh:115-127`).

### 15. Batcher-Registry nie geleert

- BESTAETIGT (`net_batcher.rs:272-301`; Leeren nur unter `cfg(test)`, `:308-311`). Harmlos: der Sammel-Faden haelt einen `Arc`-Klon (`:216-224`, `:290`), das `Net` bleibt also am Leben und seine Adresse kann nicht neu vergeben werden. Kosten: ein Faden plus Modell je registriertem Netz bis Prozessende. Knopf aus.

### 16. Rueckfall schreibt Zufallszug als One-hot

- BESTAETIGT an beiden Stellen: Heuristik-Self-Play (`self_play.rs:361-365`, nicht im Rezept) und Netz-Self-Play (`:5790-5829`, im Rezept). Laut Code-Kommentar nie beobachtet (863 von 863, `:5804-5816`) [Kommentarangabe, UNGEPRUEFT].
- **Wichtig fuer den Fix:** die Kette faehrt `MOSAIC_IGNORE_POLICY_TARGET_VALID=1` (`tools/night_v33_chain.sh:44`). Ein blosses `policy_target_valid=false` waere damit wirkungslos; `corpus_dataset.py:1635-1659` beschreibt genau diese Falle und das Vorbild (eigene Flagge wie bei `return_order_randomized`).

### 17. `json_to_state` ignoriert `first_player_next_round`

- BESTAETIGT (`serialize.rs:1243-1245`, Kommentar `:1428-1444`). Der Referee nutzt `json_to_state_exact` (`referee.rs:141`, `:196`, `:226`, `:253`), der das Feld woertlich liest (`serialize.rs:1755`): Referee-Grenze NICHT betroffen.
- Wo es falsch werden kann: solange niemand die Marke haelt, liefert die Ableitung `current_player` statt des Vorrunden-Halters. Das wird beim Nehmen der Marke ueberschrieben (`execution.rs:348`), ABER bis dahin liest das Netzmerkmal P.15 den falschen Wert: `current_is_first_next` im Direktpfad (`features.rs:581`). Der JSON-Pfad des Encoders liest den Wert dagegen woertlich (`features.rs:508-510`). Randfall `state.rs:397-403` (Marke entfernt ohne Nahme): dort bliebe auch der naechste Startspieler falsch.
- Betroffene Aufrufer: Seeding-Startzustaende (`self_play.rs:6464`, im Rezept aus: kein `--seed-positions`), 14 Diagnose-Einstiege in `lib.rs` (Grep), die Tiling-Projektion (`features.rs:654`, liest das Feld nicht).

### 18. ONNX-Export mit stillem Zufallskopf

- BESTAETIGT: Shape-Abweichungen werden verworfen und nur gewarnt, `load_state_dict(strict=False)` wird nicht ausgewertet (`export_onnx.py:109-113`, `:208-213`). Die Referenzdatei fuer die Rust-Paritaet wird aus DEMSELBEN Modell erzeugt (`:159-171`) und faengt es darum nicht. `train.py` exportiert am Trainingsende automatisch (`train.py:2691-2710`), also auch im laufenden v33-Training. Schaden nur bei Architektur-Abweichung; ob der v33-Export eine "Shape-Mismatch"-Zeile druckt, ist [UNGEPRUEFT] (Lauf noch nicht fertig).

### 19. pre-push: Logtext-Erkennung

- BESTAETIGT: jede geaenderte Zeile, die mit `"` beginnt, gilt als Logtext (`tools/hooks/pre-push:150`), z. B. `json!`-Schluessel oder `match`-Arme auf Zeichenketten. Folge nur `cargo build` (`:221-229`). `NUR_LOGTEXT` wird je Ref ueberschrieben (`:151-155`), die letzte Ref mit `engine/src/`-Aenderung gewinnt; die Sicherung `:161` greift nur fuer den Vollpruefungs-Fall.

### 20. Elo-Fit bei Sweep

- BESTAETIGT als Herleitung am Code: bei 10:0 gegen den Anker waechst gamma je Iteration um 1 (`tools/elo_tracker.py:408-415`), nach 500 Iterationen 501, also 1000 + 400 * log10(501) = 2079,9 (`:151`, `:174`, `:421`) [HERLEITUNG, nicht ausgefuehrt]. Der Binomial-Bootstrap zieht bei p = 1 immer 10:0 (`:474-479`), Breite 0, und die Warnung greift nur bei Breite > 600 (`:531`).
- Heute latent: keine Zeile in `evaluations/elo_history.csv` hat 0 Siege einer Seite (Grep; einziger Treffer ist ein Block in `units`, Zeile 50).

### 21. `debug=True` und CORS

- BESTAETIGT (`server.py:1888`, `:68-72`). `app.run` ohne `host` bindet an localhost [UNGEPRUEFT an der Flask-Doku]; CORS ohne Argumente erlaubt alle Origins [UNGEPRUEFT an der flask_cors-Doku], also koennte jede Webseite im Browser des Nutzers die lokale API aufrufen. Der Server kennt einen eingefrorenen Build-Modus (`server.py:55-56`); dort waere `debug=True` besonders unpassend.

### 22. Modellpfade, `sims`, GIL, `_ai_lock`

- BESTAETIGT: beliebiger vorhandener `.onnx`-Pfad (`server.py:292-295`), `sims` aus dem Rumpf ungedeckelt (`:273-276`, `:689`), ebenso `teacher_sims` (`:649-650`). `_ai_lock` definiert (`:111`), sonst kein Treffer. `py.rs` gibt die GIL nirgends frei (Grep `allow_threads|detach`: 0 Treffer), die Suche haelt sie also [HERLEITUNG aus pyo3-Verhalten, UNGEPRUEFT an der Quelle].

### 23. Diverses

- `train.py`: `save_path` aus `--name` (`train.py:2520`) wird ohne Existenz-Waechter und nicht atomar ueberschrieben (`:2599`, ebenso `:2654`, `:2678`); atomar ist nur der Zwischenstand (`:1039-1047`). BESTAETIGT.
- `corpus_io.dump_records`: direktes `open(path, "wb")` (`corpus_io.py:73-85`). BESTAETIGT.
- Cache-Schluessel: nur Basisname plus Konfiguration, kein Inhalt/mtime/Groesse (`engine/py/file_cache_key.py:156-222`). BESTAETIGT.
- Panic im Worker, PRAEZISIERT: im Netz-Self-Play laeuft jede Partie in `run_with_watchdog` in einem eigenen Faden (`self_play.rs:6335-6346`). Panict die Partie, faellt der Sender weg, `recv_timeout` liefert sofort `Err`, und der Aufrufer meldet "[Watchdog] ... ueberschritt die harte Deadline" und verwirft die Partie (`:6555-6563`). Der Chunk laeuft weiter, es gibt KEINEN Neustart. Nur Panics ausserhalb dieser Kapsel (Setup, Netz laden) enden als `PanicException` im Subprozess, an `except Exception` (`self_play.py:282-283`) vorbei; dann bleibt der Herzschlag aus und der Chunk wird mit neuem Seed wiederholt (`self_play.py:385-400`). Beides ist ein Fehlbild: eine Panic heisst im Log "Deadline" bzw. "Herzschlag".

## Wirkt auf Messungen / Korpus

1. **#9, Elo-Leiter:** jede Kante gegen `hv4_anchor` spielt eine Heuristik, die im Baum echte verdeckte Information sieht, gegen Netze, die determinisieren. Asymmetrisch, also NICHT durch die Arena weggekuerzt. Betrifft alle registrierten Anker-Kanten des Segments 2.
2. **#13, Self-Play-Korpora (auch v33, laufendes Training):** Reproduzierbarkeit nur unter der Bedingung, dass kein Label-Deckel feuert. Laut `PREREG_deterministic_labels.md:1` unter Stress 0 Feuerungen; Wertziele selbst deterministisch. Risiko gering, aber im Artefakt nicht belegt.
3. **#14, Klasse `value-excursion` (v33 und G-1/G-2 im Fenster):** Wertziele von Haupt- und Ausflugspartie teilen den Zufall. Fuer jede Messung an diesem Material Blockbildung (Paar = Block), wie `PREREG_start_position_seeding.md:535-536` es fuer den Vorlauf schon verlangt.
4. **#16, Netz-Self-Play-Korpora:** ein ausgeloester Rueckfall ginge wegen `MOSAIC_IGNORE_POLICY_TARGET_VALID=1` als Policy-Ziel ins Training. Praktisch nie ausgeloest [Code-Kommentar].
5. **#18, laufendes Training:** der automatische Export kann bei Architektur-Abweichung ein gueltig aussehendes Modell mit Zufallskopf liefern; Tor 1 wuerde das nur als Schwaeche sehen. Nach dem Training die Export-Ausgabe auf "Shape-Mismatch" pruefen.
6. **#8, Diagnose-Messung:** der Stufe-3-Nullbefund von `PREREG_moon_stack_order.md` lief unter dem Defekt (Specs `moon_order_post2`, `moon_order_scale0/1`).
7. **#23 (Panic -> "Watchdog"):** panicende Partien fallen still aus den Korpora (Auswahleffekt, Groesse [UNGEPRUEFT]; ablesbar an "[Watchdog]"-Zeilen der Erzeugungslogs).
8. **#17:** Seeding-Korpora aus der Vergangenheit und `lib.rs`-Diagnosen koennen Merkmal P.15 vor der Markennahme falsch tragen [HERLEITUNG]; im aktuellen Rezept kein Seeding.
9. Nicht betroffen: #6 (keine Messkette ruft `is_over`), #7 (Referee prueft), #11/#12/#15 (Knoepfe/Feature aus), #20 (kein Sweep im Register).

## Vorschlag: Commit-Schnitt

Randbedingung: kein Build und kein Commit, solange die Kette laeuft (`evaluations/STATUS.md:38`, `:102`). Alle Engine-Commits in EINE Wheel-Runde mit Fahrplan 3b (`STATUS.md:76-79`), damit die Anker-Invarianz nur einmal faellt; #9 getrennt davon.

1. **Engine: Validierung vor Mutation** (`game.rs`, `validation.rs`): #1 (beide Validatoren + Reihenfolge in drei `execute`-Stellen), #5, #7 samt angepasstem Test. Je Befund ein Regressionstest. Anker erwartet gruen.
2. **Engine: py.rs-Bindungen haerten**: #2, #3, #4 und das Entfernen von `peek_stack_json` (#10). Anker erwartet gruen.
3. **Engine: `is_over`-Semantik** (#6) mit `game.rs:1258` auf explizitem Rundentest, py.rs-Test und `gui_node_gate_smoke.py` nachziehen.
4. **Engine: Sichtfehler Diagnosepfad** (#8) plus Eintrag in `docs/architecture_reference.md`.
5. **Engine: `json_to_state` liest `first_player_next_round`** (#17).
6. **Engine + Python: Erzeugungsfragen, VOR der v34-Erzeugung** (Record-Feld vor Erzeugung): #16 (eigene Flagge + Maske in `corpus_dataset.py`), #13 (eigener Label-Strom; aendert Self-Play-Bytes, Golden-Records der Self-Play-Familie neu). #14 nur nach Nutzer-Entscheid.
7. **Engine: #9 Heuristik-Determinisierung** allein, nach Nutzer-Entscheid; ROT erwartet, neues Leitersegment.
8. **Python/Werkzeug, ohne Wheel:** #18 (Export), #19 (pre-push), #20 (Elo-Fit), je ein Commit.
9. **Server:** #21 und #22 zusammen (debug, CORS, Modellliste, `sims`-Deckel, `_ai_lock`).
10. **Betrieb:** #23 (atomare Writes, Ueberschreib-Waechter, Inhalt im Cache-Schluessel, Panic im Watchdog ehrlich melden) in kleinen Einzelcommits; #11, #12, #15 niedrig, gern mit 2.

## Nachtrag 2026-09-27: Befund #5 geschlossen

Nicht umgesetzt (Nutzer: *"Dann weg mit dem schalter"*). Kein legaler Pfad erzeugt die Teil-Mond-Entnahmen;
der Log-Replayer braucht sie fuer alte Menschenpartien (`tools/analyze_game_log.py:1026-1043`).
Training und Messungen sind unberuehrt.
