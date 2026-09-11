# Code-Review Engine-Kern: Spielregeln, Zustand, Runden, Altsuche

**Datum:** 2026-09-11. **Art:** rein lesend, keine Quelldatei angefasst, kein
Build, kein Messlauf, kein git.

**Bereich:** `engine/src/` – game.rs, state.rs, board.rs, dome.rs, factory.rs,
tile.rs, moves.rs, execution.rs, validation.rs, supply.rs, scoring.rs,
round_end.rs, round5.rs, round_transition.rs, round_transition_deep.rs,
round_transition_resample.rs, mcts.rs, search_common.rs (14.609 Zeilen).

**Gelesene Zeilen (Regel 0, ehrlich).** VOLLSTAENDIG: tile.rs (77), moves.rs
(127), supply.rs (103), search_common.rs (79), board.rs (483), dome.rs (360),
factory.rs (302), validation.rs (238), state.rs (881), game.rs (1691),
execution.rs (497), round_end.rs (924) = 5.762 Zeilen. TEILWEISE: scoring.rs
(1-330, 686-1055 von 2592, plus Funktions-Gliederung), round5.rs (1-730 von
1660), round_transition.rs (1-560 von 890), mcts.rs (1-540 von 1511),
round_transition_deep.rs (1-68, 560-740 von 1239), round_transition_resample.rs
(1-43 plus Gliederung, von 551) = rund 2.500 weitere. Der Rest ist ueber
gezielte Greps abgedeckt (Aufrufer-Suche, Bezeichner-Scan,
unwrap/expect/panic-Scan). Wo eine Aussage nur auf einem Grep beruht, steht das
dabei; Unsicheres ist als "unklar" oder "ungeprueft" markiert.

**Regelquelle:** `docs/engine_manual.md` (gelesen, 205 Zeilen). Kontext:
`docs/architecture_reference.md` (gelesen), `CLAUDE.md`.

---

## 1. Bugs und Korrektheitsrisiken

### 1a. Gegen das Handbuch geprueft und IN ORDNUNG

Damit klar ist, was NICHT beanstandet wird; jede Zeile am Code nachgesehen.
**Endwertung, alle 8 Platten** gegen `engine_manual.md:194-201`:
`scoring.rs:704-782` stimmt Kriterium fuer Kriterium (3 / 7 / 10 max 2 / 2 je
Wildfeld nur bei ALLEN belegt / 1 je Randfeld / 3 obere + 8 untere Eckplatte /
-3 je leeres Spezialfeld / 4 je Zeile mit >= 5 Farben); Spezialfliesen zaehlen
bei Kriterium 8 als keine Farbe (`scoring.rs:826-828`); Ausschlusspaare
`scoring.rs:60-65` und Ziehung `scoring.rs:89-109` = `engine_manual.md:186-188`.
**Spezialfliese** (`:179-181`): Punktwert = Rasterreihe 1-6
(`round_end.rs:361-362`), kein eigener Linienbonus (`round_end.rs:316`), zaehlt
aber als belegte Zelle (`dome.rs:54-58`); Freischaltung exakt "die anderen drei
gefuellt" (`dome.rs:140-158`). **Strafleiste** (`:116-118`, `:165-168`):
-1/-2/-3/-4 (`board.rs:228`), Ueberlauf in den Turm (`board.rs:323-328`,
`execution.rs:345-350`), Klemmung bei 0 (`board.rs:344-347`), Marker -2
(`round_end.rs:431-434`). **Startspielerstein** (`:119-125`, `:59-63`): nur die
erste MOND-Nahme vergibt ihn (`factory.rs:196-208`), die Sonnen-Nahme nicht
(`factory.rs:170-179`), Ausnahme monochrome Notbefuellung (`state.rs:313-324`).
**Punktgleichstand** (`:203-205`): `game.rs:600-616` ueber
`first_player_next_round`, weil `score_penalty` (`round_end.rs:431-434`) das
Flag `holds_first_player_marker` bei jeder Rundenwertung raeumt.
**Kuppelplatten-Ablage** (`:46-48`): nachgefuellt nur nach der
Eroeffnungsplatzierung (`game.rs:582-587`) und in der Rundenvorbereitung
(`game.rs:997-1001`). **Determinisierung des Kuppelstapels**
(`state.rs:223-253`): haelt den RNG-Vertrag bei leeren Bloecken (Test
`state.rs:758-778`).

### 1b. Befunde

**B1 – `is_over()` ist waehrend der GANZEN Runde 5 wahr.** `game.rs:700-702`:
`round_number >= NUM_ROUNDS` (= 5) ist ab dem ersten Zug der Runde 5 wahr, nicht
erst nach ihr. Intern harmlos, weil die einzige Engine-Nutzung
(`game.rs:987`) erst nach der Runde-5-Wertung faellt. Nach aussen nicht:
`py.rs:173-175` exportiert die Funktion, `py.rs:815`/`:931`/`:1055` schreiben
sie als Feld `done`, `server.py:1606` reicht `done` ans Frontend durch. Richtig
waere `phase == End || phase == Final`. Ungeprueft, ob das Frontend darauf
reagiert. Folgeschaden im Test: `py.rs:1111-1113` bricht die "Partie bis zum
Ende"-Schleife am Runde-5-START ab, die Abschlusszusicherung `py.rs:1136`
("Partie nicht zu Ende gespielt") ist danach trivial erfuellt; der Test deckt
faktisch nur die Runden 1-4 ab.

**B2 – Panics ueber die Python-Bindung, fehlende Bereichspruefung.** Zwei
Stellen indizieren `dome_slots[row][col]` ohne die Pruefung, die das
Gegenstueck `validate_dome_move` (`game.rs:51-53`) hat: `game.rs:232` in
`validate_draw_from_stack`, erreichbar ueber `py.rs:281-299`
(`apply_dome_stack_choose`), und `server.py:1000-1003` reicht
`int(d['slot_row'])` aus dem Client-JSON ungeprueft weiter; sowie
`game.rs:570`/`:573` in `apply_start_placement`, wo weder `player_idx < 2` noch
`row/col <= 2` geprueft wird, erreichbar ueber `py.rs:330-331`
(`apply_start_tile`), `server.py:1046-1048`. Das ist exakt die Fehlerklasse des
Engine-Audits U2 (`validation.rs:31-39`), dort behoben, hier offen. Ein
PyO3-Panic ist eine `PanicException` und damit keine `Exception`;
`server.py`s `except Exception` faengt ihn nicht. Ungeprueft, ob das im Betrieb
schon ausgeloest wurde.

**B3 – Top-down-Sperre fehlt in `apply_bonus_chips_with`.**
`engine_manual.md:161-162` verlangt die Sperre auch fuer Chips. Durchgesetzt
wird sie nur in `round_end.rs:464` (`apply_bonus_chips_to_row`) und noch einmal
einzeln in `py.rs:397`. Die eigentliche Arbeitsfunktion
`apply_bonus_chips_with` (`round_end.rs:613`) prueft `tiled_max_row` NICHT, hat
aber 18 weitere Aufrufstellen (gegrept): `referee.rs:537`/`:674`,
`round_transition.rs:157`,
`self_play.rs:1344`/`:2921`/`:3355`/`:3884`/`:5397`/`:5670`/`:5807`/`:7283`,
`tiling_solver.rs:182`/`:1759`. Jede verlaesst sich darauf, dass der Aufrufer
gefiltert hat; `py.rs:388-391` sagt das im Kommentar selbst. Ungeprueft, ob eine
dieser Stellen die Sperre real verletzt. Der Guard gehoert in die
Arbeitsfunktion, dann ist die Frage erledigt.

**B4 – `execute_draw_from_stack` validiert nicht selbst.** `game.rs:252` fuehrt
aus, ohne `validate_draw_from_stack` zu rufen; das Gegenstueck
`execute_draw_stack_peek` (`game.rs:175`) tut es. Folge bei einem
unvalidierten Aufruf: `game.rs:280-286` legt nur zurueck, was in `return_order`
steht, alles uebrige bleibt in der lokalen `rest`-Map und faellt aus dem Spiel.
Im Hauptpfad vorher validiert (`game.rs:814`).

**B5 – Mond-Teilentnahmen sind validierbar, aber regelwidrig.** Bereits im Code
dokumentiert und weiter offen: `LargeFactoryMoon` und `SmallFactoryMoon` MIT
`factory_id` sind Teilentnahmen aus dem Mondbereich, den das Regelwerk als EINEN
Pool behandelt (`engine_manual.md:104-107`). Der Generator erzeugt sie nie
(`validation.rs:214-230` liefert nur die globale Form), die Validatoren
akzeptieren sie (`validation.rs:66-85`, `:101-113`). Anlass, Schadensbild und
der konkrete Log-Fall stehen in `execution.rs:29-57`. Erreichbar nur ueber die
API, also in Menschenpartien.

**B6 – `validate_move` prueft Aktion C gar nicht.** `validation.rs:69`: bei
`SmallFactoryMoon` ohne `factory_id` gibt `validate_small_moon` `None` (= kein
Fehler) zurueck und verlaesst sich auf den Dispatch in `game.rs:759-763`. Wer
`validate_move` direkt benutzt, bekommt fuer jede Farbe ein "gueltig", auch
wenn sie nirgends oben liegt. Gleiche Klasse wie B2 und U2.

**B7 – Phantom-Fliesen in der projizierten Strafe.** `round_end.rs:126` summiert
`pattern_lines[ri].tiles.len()` inklusive der per Bonuschip virtuell ergaenzten
Fliesen; die tatsaechliche Ausfuehrung bucht nur `real_n`
(`round_end.rs:98`). Die Projektion ueberschaetzt also die Strafe fuer
chip-gefuellte Reihen. Verbraucher sind Bewerter, keine Regel: `mcts.rs:83` und
`round5.rs:349`/`:353`. `mcts::player_total` ist der Elo-Anker-Pfad
(`architecture_reference.md:151-154`), also nicht ohne Anker-Entscheid anfassen.

**B8 – Behauptete, aber nicht durchgesetzte Invariante.** `state.rs:92-93` und
`:99` sagen, `pending_stack_draw` und `pending_dome_choice` wuerden "beim
Rundenwechsel" zurueckgesetzt. `setup_new_round` (`state.rs:505-527`) und
`Game::next_round` (`game.rs:996`) tun das nicht; die einzigen Resets sind
`game.rs:254` und `game.rs:820`. In der Praxis unerreichbar, weil
`current_player_can_move` (`game.rs:449`) einen offenen Teilzug als "kann
ziehen" wertet und `check_drafting_complete` deshalb nicht abschliesst. Die
Doku behauptet trotzdem mehr, als der Code haelt.

**B9 – Nichtdeterminismus-Kanaele (kein Bug, aber Messgrenze).**
`round5.rs:474`/`:488` brechen bei `Instant::now() >= deadline` ab;
`round_transition_deep.rs:646`/`:658` liefert bei Deadline `None`, worauf
`:709` auf einen anderen Bewerter ausweicht. Beides ist ausdruecklich als
Not-Deckel gebaut und wird gezaehlt (`round_transition.rs:230-324`). Praktische
Folge: "gleiche Seeds, gleiche Zahl" gilt nur unter gleicher Last.

**B10 – Vier Env-Knoepfe, zwei Dialekte, ein stiller Schlucker.**
`state.rs:214-221`, `round5.rs:148-163`, `round5.rs:180-187` lesen
`v.is_empty() || v != "0"`; `state.rs:360-367` liest `"1"`/`"true"`.
`round5.rs:196-205` faellt bei einem Parse-Fehler von `MOSAIC_R5_NODE_BUDGET`
wortlos auf den Default. Beides ist der in `architecture_reference.md:157-169`
beschriebene Bestand, hier fuer meinen Bereich konkretisiert.

---

## 2. Tote und ueberholte Pfade

**T1 – Vier Funktionen in board.rs ohne jeden Aufrufer.** `board.rs:208`
`is_row_complete`, `:212` `is_col_complete`, `:216` `completed_rows`, `:220`
`completed_cols`. Grep ueber `engine/src`, `engine/examples`, `engine/benches`
und `tools`: kein einziger Aufrufer; einziger Treffer ist ein erklaerender
Kommentar in `tools/probes/arena_column_probe.py:102`. Die Spaltenbau-Wahrheit
lebt in `scoring.rs:709-712`. Steht schon auf der Merkliste
(`architecture_reference.md:147-150`).

**T2 – `mcts::search_action` ist produktiv tot.** `mcts.rs:793`. Einziger
Aufrufer ist `tiling_solver.rs:2932`, und das steht in einem
`#[cfg(test)]`-Messtest (`tiling_cache_hit_rate_measurement`,
`tiling_solver.rs:2909`).

**T3 – Der Legacy-MCTS als solcher lebt.** Gegenteilige Vermutung geprueft und
falsch: `py.rs:15` (`search_with_tree`, `search_log_text`, `search_log_header`,
`search_move_json`), `self_play.rs:32` (`root_child_stats`,
`search_drafting_action`, `player_total`), `round_transition.rs:601`,
`net_mcts.rs:2415` (`evaluate`). `mcts::player_total` (`mcts.rs:80`) traegt
ueber `scoring_progress` den Elo-Anker. Nicht abraeumen.

**T4 – Der Inversions-Pfad in round_transition_resample.rs ist Altlast.**
`invert_round5_fill` (`:64`), `resample_round5_start` (`:168`), die PyO3-Huelle
`resample_round_transition_json` (`lib.rs:1819`, registriert `lib.rs:2052`) und
der nur dafuer existierende Wrapper `state::fill_factories_for_resample`
(`state.rs:542`). Kein Python-Verbraucher (Grep ueber `tools/*.py` und
`server.py`); `tools/r4_value_calibration.py:222` nutzt ausschliesslich
`autoplay_to_round5_and_resample_json`. Der Modulkopf erklaert warum
(`round_transition_resample.rs:32-43`: 87,6 Prozent der echten Runde-5-Starts
haben einen leeren Turm und werden von der Ausschlussregel verworfen).

**T5 – Doppelte Implementierung in mcts.rs.** `expand_and_backprop`
(`mcts.rs:329-392`) wiederholt Expansion, Bewertung und Backprop der
Sim-Schleife (`mcts.rs:472-515`) fast woertlich.

**T6 – round_transition / _deep / _resample sind KEINE Dubletten.**
Aufrufer-Grep: `round_transition.rs` traegt den EINEN Uebergang (benutzt von
`net_mcts.rs`, `self_play.rs`, `round_transition_deep.rs`,
`round_transition_resample.rs`); `round_transition_deep.rs` die rekursive Kette
ueber mehrere Runden (`self_play.rs`, `lib.rs` via
`bootstrap_value_after_rounds`). Nur `_resample` ist teilweise tot, siehe T4;
der Vorwaerts-Pfad `autoplay_to_round5_and_resample` darin lebt.

---

## 3. Optimierungspotenzial (an konkretem Code, ungemessen)

**O1 GameState-Klon je Kind:** `mcts.rs:184`, `round5.rs:391`, dazu
`round5.rs:288` je Zufallsausgang. Besonders auffaellig `ordered_children`
(`round5.rs:386-411`), das JEDEN Kandidaten klont und anwendet, nur um zu
sortieren; bei rund 20 Kandidaten und `NODE_BUDGET = 200` (`round5.rs:88`) ist
das ein spuerbarer Anteil der Gesamtarbeit. Messwerkzeug liegt bereit:
`benches/clone_cost.rs`, `profiling::note_gamestate_clone` (`mcts.rs:183`).
**O2 Vierfache Validierung je Kuppel-Kandidat:**
`dome_slot_rotation_candidates` (`game.rs:91-104`) ruft `validate_dome_move`
viermal je (Kachel, Slot), `generate_dome_moves` (`game.rs:110-130`) fuer jedes
Paar aus Ablage mal freiem Slot, also bis zu 3*9*4 = 108 volle Validierungen je
Zuggenerierung; der Kommentar dort sagt selbst, dass das Ergebnis "aktuell immer
alle 4" ist. Dasselbe in `draw_stack_slot_rotation_candidates`
(`game.rs:366-386`), das je Aufruf zusaetzlich `return_order.to_vec()` kopiert.
**O3 Vec nur fuer eine Laenge:** `can_place_dome_tile` (`board.rs:373-381`) baut
ueber `occupied_slots()` (`board.rs:118-128`) einen Vec, um dessen Laenge zu
vergleichen; laeuft in jeder Zuggenerierung und jeder Validierung.
**O4 Doppelte Legalitaetspruefung im Tiling:** `generate_tiling_actions`
(`round_end.rs:646-684`) filtert erst selbst (`:667`) und ruft danach nochmal
`validate_tiling_action` (`:676`), das die Top-down-Regel ueber alle frueheren
Reihen erneut durchlaeuft (`round_end.rs:174-189`). **O5 Allokation je
Zugkandidat:** `generate_valid_moves` (`validation.rs:177-190`) klont ein
`TakeAction` samt `moon_order`-Vec je (Fabrik, Farbe, Reihe), also bis zu
4*5*7 = 140 Allokationen je Aufruf.

---

## 4. Struktur und Nachvollziehbarkeit

**S1 – Deutsche Bezeichner: 13 Deklarationen im ganzen Bereich** (Grep ueber
`fn`/`let`/`const`/`struct`/`enum`). state.rs 2: `volle_versorgung` :360,
`farben` :402. scoring.rs 4: `rasterreihe` :379, `wert` :380, `anzahl` :1451,
`basis_reihen` :1911. round_end.rs 4: `soll_slot_row` :157, `soll_si` :158,
`falsche_teilreihe` :792 (Test), `falsche_slot_reihe` :798 (Test).
execution.rs 1: `war_leer` :313. search_common.rs 1: `nachlauf_targets` :62.
mcts.rs 1: Testname `nachlauf_closed_nodes_have_even_visit_counts` :1191.
Null in game.rs, board.rs, dome.rs, factory.rs, tile.rs, moves.rs,
validation.rs, supply.rs, round5.rs und den drei round_transition-Dateien.
Davon getrennt: `TileColor::{Blau, Gelb, Rot, Schwarz, Tuerkis}`
(`tile.rs:6-12`) sind Spielfachbegriffe, die CLAUDE.md uebersetzt sehen will,
die aber ueber `value()`/`from_value()` (`tile.rs:26-48`) an jedem State-JSON,
jedem Log und am Replayer haengen; Bewertung in Abschnitt 5.

**S2 – Ueberholte oder widerspruechliche Doc-Kommentare.** `state.rs:92-93` und
`:99`: behaupteter Reset beim Rundenwechsel, siehe B8. `round5.rs:459`: die
Funktion heisst `negamax`, ist aber ein Minimax mit ausdruecklicher
`maximizing`-Verzweigung (`:483-508`) und ohne Vorzeichenwechsel; der Modulkopf
(`round5.rs:1-2`) sagt korrekt "Expectiminimax", der Name widerspricht ihm.
`game.rs:846-847`: `valid_drafting_actions` "ohne Stapel-Zug, dessen Auswahl
agentenseitig erfolgt" – `drafting_actions` liefert Stapel-Zuege sehr wohl
(`game.rs:653-664`, `:674-676`). `round_transition.rs:63-66`:
`N_SAMPLES_SEARCH` "noch nicht aktiviert", waehrend `net_mcts.rs` die Konstante
importiert; unklar, ob der Pfad laeuft (`architecture_reference.md:32` nennt
`ROUND_TRANSITION_SAMPLING = false`), der Kommentar sagt jedenfalls mehr, als er
wissen kann.

**S3 – Tests, deren Name mehr verspricht als die Zusicherung haelt.**
`py.rs:1136` (`assert!(plain.game.is_over(), "Partie nicht zu Ende gespielt")`)
ist wegen B1 schon am Runde-5-Start erfuellt; echt geprueft wird nur
`refill_seen`. `board.rs:459-472` `place_tile_and_unlock_special` schliesst mit
`assert!(grid.place_tile(0, 0, Rot).is_err())` unter der Ueberschrift "falsche
Farbe wird abgelehnt" – abgelehnt wird es aber, weil die Zelle schon gefuellt
ist (der Kommentar daneben sagt das selbst); die angekuendigte Farb-Ablehnung
wird nie geprueft. `game.rs:1046`
`stack_peek_at_zero_score_allows_unlimited_draws` zieht viermal, der echte
Deckel (`dome_tile_pool.is_empty()`, `game.rs:168`) wird nie erreicht.

**S4 – Module, die zwei Dinge tun.** `round_transition.rs` traegt das
Uebergangs-Sampling (`:137-391`), sechs `#[cfg(test)]`-Partie-Treiber (`:398`,
`:423`, `:449`, `:484`, `:497`, `:519`, `:543`), die quer von `scoring.rs`,
`round5.rs`, `round_transition_deep.rs` und `tiling_solver.rs` benutzt werden,
und die globale Diagnosestatistik `NotDeckelStats` (`:230-324`), die auch
Zaehler fuer `round_transition_deep.rs` fuehrt. `game.rs` orchestriert UND
validiert/fuehrt die Kuppel- und Stapel-Zuege aus (`:34-441`), waehrend die
Steinzuege dafuer eigene Module haben (`validation.rs`, `execution.rs`); genau
diese Asymmetrie hat B2 und B4 moeglich gemacht.

---

## 5. Priorisiert vor Projektende

Sortiert nach Risiko, nicht nach Wichtigkeit: 1-4 sind risikoarm und sofort
machbar, 5-9 brauchen je eine Rueckwaerts-Pruefung, 10 braucht einen Messlauf.

| # | Punkt | Stelle | Aufwand | Risiko |
| --- | --- | --- | --- | --- |
| 1 | B2: Bereichspruefung fuer Slot und Spielerindex nachziehen | game.rs:232, :570, :573 | 0,5 h | niedrig, nur zusaetzliche Err-Zweige, kein legaler Zug aendert sich |
| 2 | B4: `execute_draw_from_stack` mit eigenem Validator absichern wie game.rs:175 | game.rs:252 | 0,25 h | niedrig, vorher pruefen, dass die Aufrufer in net_mcts/self_play schon validieren |
| 3 | T1: die vier aufruferlosen board-Funktionen loeschen | board.rs:208-222 | 0,25 h | sehr niedrig, der Compiler bestaetigt es |
| 4 | T2: `mcts::search_action` entfernen oder auf `#[cfg(test)]` setzen | mcts.rs:793 | 0,25 h | sehr niedrig |
| 5 | B1: `is_over()` auf `phase` umstellen, `done` und den Test nachziehen | game.rs:700, py.rs:174/815/931/1055/1112/1136 | 1 h | MITTEL, `done` geht ins Frontend (server.py:1606), vorher nach Konsumenten greppen |
| 6 | S2: die vier ueberholten Doc-Kommentare richtigstellen, `negamax` umbenennen | state.rs:92/99, game.rs:846, round_transition.rs:63, round5.rs:459 | 0,5 h | null |
| 7 | S1: die 13 deutschen Bezeichner umbenennen | siehe S1 | 0,5 h | null, alle lokal oder crate-privat (`nachlauf_targets` hat einen Aufrufer, mcts.rs:522) |
| 8 | T4: den toten Inversions-Pfad ausbauen | round_transition_resample.rs:64/168, lib.rs:1819/2052, state.rs:542 | 1 h | niedrig, aber `resample_round_transition_json` ist eine oeffentliche PyO3-Funktion, erst ankuendigen |
| 9 | B5/B6: die nie generierten Mond-Teilentnahmen im Validator schliessen, Aktion C auf `validate_moon_take` umleiten | validation.rs:66-113 | 1 h | niedrig fuer Self-Play und Arena (der Generator erzeugt sie nie, also byte-gleich), Replayer-Vertraeglichkeit fuer Altlogs pruefen (tools/analyze_game_log.py) |
| 10 | B3: Top-down-Sperre in `apply_bonus_chips_with` ziehen | round_end.rs:613 | 1 h | MITTEL bis HOCH, kann Zugergebnisse in Solver und Self-Play verschieben. NUR mit Anker-Invarianz-Pruefung (`/mosaic-anchor-invariance`), sonst liegen lassen |

### Kann bleiben

- **`TileColor`-Varianten deutsch** (`tile.rs:6-12`): Nutzen kosmetisch, Risiko
  ist die gesamte Serialisierungs-Paritaet (State-JSON, Logs, Replayer,
  Alt-Korpora).
- **`scoring_progress` und alles daran** (`scoring.rs:160`, `mcts.rs:80-84`):
  Elo-Anker, laut CLAUDE.md gesperrt. B7 faellt darunter; die Ungenauigkeit ist
  real, aber der Anker haengt an genau dieser Zahl.
- **B9, die Wanduhr-Deckel**: bewusst als Not-Deckel gebaut, gezaehlt
  (`round_transition.rs:230-324`), begruendet.
- **B10, die Env-Dialekte**: der geplante `read_bool_env`-Sammelfix
  (`architecture_reference.md:157-162`) betrifft rund 18 Stellen im Baum, davon
  4 hier. Lohnt nur als Gesamtaktion.
- **O1 bis O5**: keine gemessene Not, und das Projekt endet. Optimierung ohne
  vorherige Messung ist hier reines Risiko. Falls doch: O2 und O3 sind die
  billigsten und wirken in jeder Zuggenerierung.
- **T5 und mcts.rs als Ganzes** (T3): traegt den Anker, bleibt.
