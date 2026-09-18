# Architektur (Referenz)

**Kanonischer Ort seit 2026-08-28** (aus STATUS.md entflochten, Nutzer-Hinweis:
STATUS ist kein Langzeitgedaechtnis); Herkunft der Inhalte: STATUS-Stand
2026-08-28. Wer aendert, aendert HIER -- STATUS.md verweist nur noch.

**Stand der uebernommenen Beschreibung: 2026-08-25** (so war der Abschnitt in
STATUS ueberschrieben). **Pflegeregel: wer die Architektur aendert, zieht diese
Datei im selben Zug nach** -- und setzt das Stand-Datum neu. Genau daran hat es
gefehlt: die Kanalzahl war beim Uebertrag ueberholt (siehe unten).

## Such- und Engine-Seite (`engine/src/net_mcts.rs`)

- `ACTIVE_LEAF = LeafEval::Net`; Stufe 1 (DFS-Blatt) liegt dormant, Rueckfall
  ist ausgeschlossen (Rundenweitsicht ist harte Anforderung).
- **Leitsatz (Nutzer 2026-09-05): Drafting und Tiling gehen Hand in Hand --
  das Drafting muss zum Teil schon wissen, wie das Tiling agieren wird, um
  Fliesen zu legen und Punkte zu erzeugen.** Stand der Engine dazu: der
  Suchbaum laeuft nur INNERHALB einer Runde; das Blatt am Uebergang Drafting
  -> Tiling ist pseudo-terminal und bekommt EINEN Netzwert auf dem Zustand
  VOR dem Tiling (`ROUND_TRANSITION_SAMPLING = false`, net_mcts.rs:95). Kein
  Stein wird im Baum gelegt; das Tiling erreicht die Suche nur ueber das Netz
  (Eingaben: gebundene Reihen, annehmende Zellen, `solve_round_final_score`
  je Spieler als Punkt-Schaetzer mit greedy Chips, features.rs:690) und ueber
  die K3-P-Projektion fuer die Huelle. Ausnahme Runde 5 (exakter Loeser samt
  Endwertung). Das ist der bekannte Schwachpunkt hinter K3-P (par.9 der
  Einhuellenden-Prereg: H im Draft-Baum konstant) und Gegenstand von
  `PREREG_round_transition_search_sampling.md` (par.7: Aufspaltung in
  deterministisches Tiling im Blatt gegen Neubefuellungs-Sampling).
- Gumbel-Suche aktiv: `GUMBEL_TOP_M = 16`, `GUMBEL_C_SCALE = 1,0`,
  `DEFAULT_C_PUCT = 1,5`, `floor_shaping_weight = 0,3`.
- `VALUE_SHRINK_ENABLED = false`, `ROUND_TRANSITION_SAMPLING = false`,
  `SHUFFLE_STACK_PEEK_IN_SEARCH = false`, `bootstrap_horizon_rounds = 2`.
- **Runde 5 ist Expectiminimax** mit Zufallsknoten an den Chip-Aufdeckstellen;
  `NODE_BUDGET = 200` ist eine Bezahlbarkeits-, keine Hinreichenszahl --
  **kein geloestes Endspiel** (~3 Halbzuege, Orakel-Uebereinstimmung 81,4
  Prozent). Der frueher hier genannte zweite, eingefrorene Loeser
  `round5_anchor.rs` ist mit B4b **entfernt** (2026-08-27); der Anker-Schutz
  liegt seither in einem eingefrorenen Heuristik-Artefakt, aktuell
  `models/frozen_heuristics/hv4_anchor` (Neuverankerung 2026-09-12; das
  vorherige `hv1_anchor` ist seit 2026-09-13 geloescht), und eine
  Anker-Messung laeuft ueber `tools/anchor_arena.py`.
- **Der Stapelzug wird gesammelt aufgeloest**
  (`self_play.rs::resolve_and_apply_stack_draw`, Default-Pfad): die Suche
  bewertet EINEN Peek, danach zieht eine handgeschriebene Schleife weiter und
  waehlt Platte, Slot und Rotation selbst -- Kosten und Ergebnis weichen vom
  Bewerteten ab.
- **`apply_via_chosen_action` ist je Pfad verschieden.** Korpus und
  Netz-Self-Play loesen den Stapelzug NICHT gleich auf; die Tabelle der Pfade
  und die Folgen fuer die Trainingsziele stehen in STATUS, Abschnitt
  "STAPELZUG" (aktueller Strang mit offenem Wecker in
  `PREREG_v23_window.md` par.4).
- **Es gibt DREI In-Process-Pfade**: `play_arena_game` (Heuristik gegen
  Heuristik), `unified_game_loop` (Netz gegen Heuristik, **hier haengt der
  Anker**) und `RefereeGame`. Wer den Referee mit dem Arena-Pfad vergleicht,
  MUSS `set_apply_modes((True, False))` setzen -- sonst bekommt die Heuristik
  das Netz-Verhalten.

## Netz- und Trainingsseite (`config.py`, `engine/py/neural_net.py`)

- **`INPUT_SIZE = 755`** (config.py:38 und engine/src/features.rs:18 -- die
  beiden EINZIGEN Literale; alles andere liest sie oder holt sie aus den
  Checkpoint-Metadaten). Wachstum: 708 -> 714 (+6 `col_f_max`, 2026-08-25)
  -> 744 (+30 Sicht-Arm v24-b04, 2026-09-05) -> 755 (+11 Kuppelstapel-Wissen,
  Abschnitt 15, Variante B, 2026-09-11). **`NUM_ACTIONS = 406`** (config.py:43).
- **`NUM_PLANES_CHANNELS = 79`** (engine/src/features.rs:813, geprueft
  2026-08-28). Der STATUS-Stand vom 2026-08-25 nannte hier noch **77**; die
  beiden Spezialfeld-Kanaele kamen mit Schritt 1a des v22-Schlachtplans dazu
  (`e91cd34`, additiv, Paritaets-Hash haelt). Der aeltere Zuwachs war Kanal 76
  (Erreichbarkeit).
- Die neuen Groessen werden in `serialize::serialize_player` **einmal**
  gerechnet und ins Zustands-JSON geschrieben; der Rust-JSON-Pfad und Python
  LESEN sie, nur `state_to_features_direct` rechnet selbst (bewacht von den
  `direct_matches_json_path_*`-Tests). Kosten als Bitmaske: plus 0,27 Prozent
  je Korpus statt plus 3,80 Prozent als Liste.
- **Altmodelle bleiben bitgleich**: `net::split_planes_flat_batch_src` kuerzt
  den Planes-Block auf die Modellbreite und liest den Flat-Block ab der
  Quell-Grenze; neue Groessen haengen am ENDE ihres Blocks. Am Champion
  belegt (Paritaets-Hash unveraendert), nicht hergeleitet.
- Champion-Encoder ist **2D** (`Mosaic2DNet`); der flache `MosaicNet` bleibt
  Parallel- und Messarm.
- Koepfe: `policy`, `value`, `moon_order`, `points`, `ownership`,
  `opp_points`. `ownership` ist 140 breit, `OWNERSHIP_WEIGHT = 0,0`
  (config.py:79) -- der Champion-Kopf ist **untrainiert**.
- `VALUE_WEIGHT = 0,2`, `POINTS_WEIGHT = 0,5` (config.py:66/67),
  `VALUE_SCALE = 50,0`, `TD_LAMBDA = 0,5`, `VALUE_OPP_EPSILON = 0,0`
  (neural_net.py:807/808/813).
- **Value-Ziel ist margen-BLIND** (`values_wdl`, TD-Blend aus
  Bootstrap-Gewinnwahrscheinlichkeit und hartem Ausgang). Training:
  `--value-head wdl --select-by-brier`.
- Der WDL-Bootstrap ist seit 2026-08-27 **nativ per Default**; entstaucht wird
  nur noch die Blockliste der fuenf tanh-Aera-Praefixe
  (`LEGACY_STRETCHED_PREFIXES`), mit eigener eingefrorener Konstante fuer den
  v20-Traeger-Kurzschluss (`V20_CARRIER_SHORTCUT_PREFIXES`).
- Champion: `models/champion.txt` zeigt auf `v21_2d_brierbest` (geprueft
  2026-08-28).

## Wo der Code Information ABSICHTLICH vernichtet (Naht-Audit 2026-09-09)

**Wozu diese Liste.** Selfplay, Arena, Gating und die Offline-Metriken vergleichen zwei
Agenten IM SELBEN Weltmodell. Ein Fehler im geteilten Modell wirkt auf beide Seiten gleich
und kuerzt sich weg -- er kostet null Elo, bei jeder Partienzahl. **Symmetrische Defekte
sind fuer symmetrische Messung unsichtbar.** Die einzige Gegenwehr ist, die Stellen
aufzuzaehlen, an denen Information absichtlich verschwindet, und jede zwei Fragen
beantworten zu lassen: WESSEN Informationsmenge modelliert sie, und was nimmt sie weg, das
der Spieler rechtmaessig HAT?

Die Liste ist endlich und greppbar: `.shuffle(`, `choose_multiple`, Kuerzungen wie
`net.rs::build_inputs`. Stand 2026-09-09: 24 Mischstellen; dazu seit 2026-09-16 die
Neubefuellung im Suchblatt (Variante B, eigene Zeile unten).

| Stelle | Was | Urteil |
| --- | --- | --- |
| `net_mcts.rs:987` (via `:3952`) | Wurzel-Determinisierung, ruft seit 2026-09-10 `state::determinize_dome_pool(state, Some(current_player), rng)` statt `dome_tile_pool.shuffle` | **REPARIERT** (par.7 Variante A): modelliert die Informationsmenge des SUCHENDEN (`current_player`, unmittelbar danach als `root_player` gelesen). Weggenommen wird nur noch das unbekannte Praefix plus die Reihenfolge INNERHALB fremder Rueckgabe-Bloecke; der eigene Block bleibt stehen. `PREREG_dome_stack_information_sets.md` |
| `state.rs:243` (`determinize_dome_pool`, unbekannter Praefix) | mischt `dome_tile_pool[..prefix_len]` INKLUSIVE Index 0, der obersten Platte; deren Rueckseite (Typ Wild/Spezial) ist oeffentlich (`serialize.rs:357-363` `dome_stack_top_type`, Merkmal P.2 seit v24-b04) | **OFFENER BEFUND (Sichtinventur 2026-09-13, `PREREG_stack_top_feature.md` par.15 P.10):** nimmt dem Suchenden den sichtbaren Typ der obersten Platte, in jeder Determinisierung neu gewuerfelt. Fix GEBAUT 2026-09-13, 02:35 (`restore_top_plate_type`, Nutzer: "p10 fix kommt jetzt"), Wheel folgt nach dem Messende |
| `round_transition_deep.rs:623` | `simulate_one_round` determinisiert den Stapel beim Eintritt, ebenfalls ueber `determinize_dome_pool`, aber mit `viewer = None` | **TEILWEISE**: Blockgrenzen und Blockmengen bleiben erhalten, die Reihenfolge in JEDEM Block faellt weg. Wessen Unwissen: keines einzelnen Spielers -- die Rollout-Kette liefert `[f64; 2]` fuer BEIDE Spieler und laeuft aus den Label-Pfaden (`self_play.rs:4238/4248/4258`, `:2827/:2835`, `lib.rs:1917`), nicht aus dem Baum eines Wurzelspielers. Konservativ: nimmt niemandem Wissen zu, gibt keinem Orakelwissen |
| `net_mcts.rs:4010`, `:4139`, `:4448` | Neumischen bei `DrawStackPeek` im Baum, seit 2026-09-10 ueber `determinize_dome_pool(.., Some(mover), ..)` | RUHEND (`SHUFFLE_STACK_PEEK_IN_SEARCH = false`, `:904`; gemessen schlechter, 17 % -> 9 % Siege). Der blinde Fleck der Kommentare dort ist berichtigt ("volles Mischen ist exakt richtig" war falsch) |
| `self_play.rs:5140` (`mean_rollout_diff`), `:5973` (`value_noise_floor_diagnostic`) | Diagnose-Rollouts wuerfeln das Verdeckte neu, seit 2026-09-10 ueber `determinize_dome_pool(.., None, ..)` | in Ordnung: Diagnose ohne Wurzelspieler, gleiche Klasse wie `round_transition_deep.rs:623`. Ohne bekannte Bloecke byte-identisch zum fruehreren `shuffle` |
| `net_mcts.rs::search_start_placement` (2026-09-12) | Wurzel-Determinisierung der STARTSETZUNGS-Suche, ueber `determinize_hidden_information_for(state, pi, rng)` -- der Wrapper mit EXPLIZITEM Betrachter | in Ordnung, und die Stelle, an der die Frage "wessen Informationsmenge?" den Code geaendert hat: der Suchende ist hier NICHT `current_player`. Der Nicht-Starter legt zuerst (`game.rs::apply_start_placement`), waehrend `current_player` schon der Startspieler ist -- der Bestands-Wrapper haette aus der Sicht der falschen Seite determinisiert. Weggenommen wird dasselbe wie an der Drafting-Wurzel (unbekanntes Praefix, Reihenfolge in fremden Rueckgabe-Bloecken). Noetig ist sie, weil `apply_start_placement` die Luecke im Display SOFORT vom Stapel nachzieht: ohne sie saehe die Suche die echte verdeckte Nachziehplatte. `PREREG_start_dome_choice.md` par.9c |
| `round_transition.rs::round_transition_leaf_state` (2026-09-16) | Variante B des Rundenuebergangs: am pseudo-terminalen SUCHBLATT der Runden 1-4 wird EINE Fabrik-Neubefuellung gezogen -- `determinize_dome_pool(.., Some(viewer), ..)` fuer den Kuppelstapel, dann `advance_one_chance` (Beutel-Reihenfolge und Bonuschip-Vorrat gemischt, Turm-Nachfuellung ueber `draw_with_refill`). Knopf `MOSAIC_ROUND_TRANSITION_LEAF`, Default AUS | in Ordnung. **Wessen Informationsmenge:** die des SUCHENDEN, und zwar des WURZELSPIELERS (`viewer` kommt aus `RoundTransitionLeafCtx`, gesetzt an der Wurzel der drei Suchtreiber) -- nicht `current_player`, der im Tiling zwischen den Schritten wechselt. Dieselbe Mischregel wie die Wurzel, keine eigene (`PREREG_round_transition_search_sampling.md` par.8/par.9). **Was weggenommen wird:** die Reihenfolge im Beutel, im verdeckten Chip-Vorrat und im unbekannten Teil des Kuppelstapels -- alles echt verdeckt. **Was ausdruecklich NICHT weggenommen wird:** die Zusammensetzung. Die Fuellung kommt aus dem ECHTEN Beutel mit dem Turm daneben, nie aus der Summe und nie aus einem zusammengeworfenen Pool (par.10 BAUVORGABE) -- ein zaehlender Spieler kennt die Aufteilung Beutel/Turm je Farbe exakt (106 von 106 Entscheidungspunkten, `PREREG_stack_top_feature.md` par.14), und bei knappem Beutel sind die ersten Fliesen damit SICHER. Ein zusammengeworfener Pool wuerde genau diese Sicherheit wegwuerfeln. Sichttor dazu GEFAHREN 2026-09-17 (par.17.7 (d)): **GRUEN**, n = 300 Blatt-Zustaende der Runden 3 und 4 mit `bag_count` < 21, 0 Verstoesse in allen drei Kriterien (Quelle, exakte Bilanz, sichere Beutel-Steine), Instrument `tools/probes/round_transition_leaf_sight_gate.py`; im Kleinen geprueft von `leaf_fill_takes_only_tiles_from_bag_and_tower` |
| `features.rs::tiling_projection_from_json` (2026-09-17) | KEINE neue Mischregel, aber eine neue AUFRUFSTELLE einer bestehenden: der JSON-Pfad des Encoders rekonstruiert den Zustand ueber `serialize::json_to_state` mit festem Seed 0, und der mischt dabei Beutel, Turm, Kuppelstapel und Chip-Vorrat neu (Variante C, Abschnitt 17, `PREREG_round_transition_search_sampling.md` par.18) | in Ordnung, und der Grund ist, dass NICHTS davon gelesen wird: die Tiling-Projektion haengt allein an `state.players[pi]` (Feld-Herleitung im Kommentarblock ueber `tiling_solver::TilingKey`). Weggenommen wird dem Merkmal also nichts, das ein Spieler hat; die gemischten Bestaende gehen in keinen der 90 Werte ein. Bewacht wird das empirisch von `direct_matches_json_path_*`: der Direktpfad (ECHTER Zustand, nichts gemischt) und der JSON-Pfad muessen Wert fuer Wert gleich sein -- eine Abhaengigkeit von der gewuerfelten Reihenfolge wuerde dort auffallen. Dieselbe Route fahren `lib.rs::state_planes_from_json` und `lib.rs::scoring_shaping_e_json` seit laengerem |
| `net_mcts.rs:1003` | verdeckte Bonuschips | in Ordnung -- und **das Vorbild**: aufgedeckte Fabrik-Chips bleiben ausdruecklich unangetastet |
| `round_transition.rs` (8x), `round_transition_resample.rs:193`, `self_play.rs:5093` | Beutel und verdeckter Chip-Vorrat | in Ordnung: Reihenfolge ist echt verdeckt, die Multimenge bleibt erhalten |
| `scoring.rs:106` | Auswahl der Wertungsplatten | Spielaufbau, keine Informationsfrage |
| `mcts.rs:235`, `self_play.rs:803` | Zugreihenfolge, Permutationen | Gleichstandsaufloesung, keine Informationsfrage |
| `features.rs::action_to_id` (Zweig `"dome" \| "choose_dome_slot"`) | ID-BUENDELUNG statt Mischen: die vier Rotationen derselben (Platte, Slot) fallen auf EINE ID; ihre Besuchsmasse addiert sich (`t_policy[id] += prob`, `corpus_dataset.py:1314`) | **absichtlich**, weil die Rotation seit Baustein B eine eigene Stufe-2-Entscheidung mit eigener ID-Familie ist (`choose_dome_rotation`, 391-394): der Kopf lernt sie getrennt, nicht als Kreuzprodukt. Weggenommen wird nichts, das ein Spieler HAT -- es ist eine Aufteilung des Aktionsraums, keine Modellierung von Unwissen. Kehrseite: an der Startsetzung (`is_start`) gibt es die Stufe 2 nicht, dort verliert das Ziel die Rotation wirklich |
| `self_play.rs:226-235` (`action_to_env_dict`, Zweig `Stone`) | `moon_order` fliesst NICHT in die ID ein: Mondvarianten desselben Sonnenzugs teilen sich eine ID | **absichtlich**, und seit 2026-09-18 nur noch der RUECKFALL: die Suche kombiniert die Priors dieser Varianten separat (`net_mcts.rs` `build_untried_actions`), der Policy-Kopf traegt die Farbreihenfolge als EIGENEN Kopf (`moon`). Eine ID je PERMUTATION wuerde `NUM_ACTIONS` sprengen, ohne dass der Kopf die Trennung lernen koennte -- eine ID je TEILENTSCHEIDUNG dagegen nicht, und genau das ist Weg A (Zeile unten): fuenf Farb-IDs, mehrfach hintereinander benutzt. Fuer eine Seite mit 414er-Policy ist die Buendelung damit aufgehoben; fuer ein 406er-Netz und die Heuristik bleibt sie |
| `game.rs` (Weg A, `pending_moon_order`; R3, `pending_return_order`), 2026-09-18 | KEINE Mischung und keine Buendelung, sondern ihre UMKEHRUNG: die Mondstapel-Reihenfolge und der Kopf der Rueckgabe-Reihenfolge werden zu eigenen Entscheidungsknoten mit eigenen Aktions-IDs (`choose_moon_top` 406-410, `choose_return_first` 411-413, `NUM_ACTIONS` 406 -> 414) | **absichtlich, und hier eingetragen, weil die Regel unten das fuer JEDE Aenderung am Aktionsraum verlangt.** *Wessen Informationsmenge:* die des ziehenden Spielers, und zwar unveraendert -- der Knoten waehlt ausschliesslich unter Dingen, die er ohnehin in der Hand hat (die Reststeine seines eigenen Sonnenzugs; die von ihm selbst gezogenen, aufgedeckten Kuppelplatten). *Was weggenommen wird:* nichts. Der Gegner sieht vom Mondstapel weiterhin nur die oberste Farbe (`factory.rs` `moon_top_colors`) und vom Rueckgabeblock weiterhin nur Menge und Blockgrenze (`state.rs` `determinize_dome_pool`) -- der Knoten aendert an keiner dieser beiden Sichten etwas. *Tor:* `GameState::extended_action_nodes[spieler]`, gesetzt nur in `self_play::unified_game_loop` fuer eine Seite, deren Netz mindestens `NUM_ACTIONS` Policy-Ausgaenge hat. `PREREG_moon_stack_order.md` par.12.6, `PREREG_dome_return_order.md` par.12.7 |
| `serialize.rs::dome_pool_view` (Feld `designs`) | SORTIERUNG als Informationsvernichtung: die Design-Nummern des EIGENEN Rueckgabeblocks stehen als sortierte Multimenge im Record, die Reihenfolge fiel weg | **seit 2026-09-18 additiv aufgehoben** (R2/P.16): daneben steht `designs_ordered` in Stapelreihenfolge, und der Encoder liest daraus Abschnitt 18 (vier Werte, `INPUT_SIZE` 884 -> 888). Die Sortierung war eine Annahme ueber die SICHT ("der Spieler haelt die Reihenfolge im zurueckgelegten Block nicht auseinander"), und sie war falsch: er hat die Reihenfolge selbst GEWAEHLT, und `determinize_dome_pool` laesst sie ihm auch in der Suche. Fremde Bloecke bleiben unberuehrt `null` -- dort ist schon die MENGE der Designs nie gesehen worden. `PREREG_dome_return_order.md` par.12.6 |

**Was dieser Audit NICHT sieht** (und wofuer die anderen Kanaele stehen): wo Information
nie ENTSTEHT (fehlende Merkmale -- dafuer `PREREG_stack_top_feature.md`, Sicht-Achse) und
wo sie falsch BEWERTET wird (dafuer `PREREG_score_clamp_incentive.md`). Die zweite Achse
des Sicht-Audits -- was WEISS die Suche und was vergisst sie zwischen zwei Zuegen -- steht
in jener Prereg par.11.

**Der Wissensstand selbst** haengt seit 2026-09-10 im Zustand: `GameState::dome_pool_known_blocks`
(`state.rs`, `KnownPoolBlock { len, returner }`) beschreibt das untere Ende des Stapels
blockweise, aeltester Block zuerst; gepflegt an den vier Pool-Stellen in `game.rs`
(`:183`/`:571`/`:984` Ziehen von oben, `:280`-Schleife Rueckgabe), geprueft von
`state::dome_pool_knowledge_is_consistent`. Ueber die Referee-/Worker-Grenze geht er als
`dome_pool_known_blocks_exact` (`serialize.rs`, `state_to_json_exact`/`json_to_state_exact`,
tolerant gelesen); die gemeinsame Anzeige-Sicht `state_to_json` traegt ihn bewusst NICHT,
weil er seitenabhaengig ist.

**Zweite Klasse derselben Sorte: die ID-BUENDELUNG** (zwei Zeilen oben, seit 2026-09-12).
Sie mischt nichts, sie legt verschiedene Aktionen auf denselben Platz im Policy-Raum (406,
seit 2026-09-18 414)
-- mit demselben Messverhalten: beide Seiten lesen dieselbe Tabelle, jeder Fehler darin
kuerzt sich in Arena und Gating weg.

**Anlass (2026-09-12), und warum der Waechter dort jetzt steht:** `action_to_id` hatte
keinen Zweig fuer den Aktionstyp `"dome"` (Startsetzung der Kuppelplatte, Record
`type: dome, is_start: true`). Der Rueckfall `_ => 405` legte JEDEN unbekannten Typ auf die
ID des verdeckten Ziehens (`dome_stack_peek`) -- alle bis zu 108 Startkandidaten auf einer
einzigen, und zwar auf der einer fremden, echten Aktion. Unbemerkt seit Wochen, weil
`corpus_dataset.py` Start-Records ohne `start_by_search` mit Policy-Gewicht 0 fuehrt: das
Ziel war falsch, aber gewichtslos. Gefunden hat es kein Messlauf, sondern das Lesen des
Codes. Seitdem: jeder von der Engine erzeugte Typ hat einen EXPLIZITEN Zweig
(`features.rs::KNOWN_ACTION_TYPES`), der Rueckfall ist ein harter Fehler (Test-Build
`panic!`, Release `debug_assert!` plus einmalige Warnung und der Sentinel
`UNKNOWN_ACTION_ID = 2` aus der ungenutzten ID-Luecke, damit eine laufende Partie nicht
stirbt und die Kollision auf keine echte Aktion faellt), und zwei Tests halten die Menge
der Erzeuger gegen die Menge der Zweige: `features.rs::action_to_id_branches_cover_exactly_the_engine_action_types`
(Rust) und `tools/tests/test_action_id_mirror.py` (Python-Spiegel gegen Rust-Quelltext).

**Regel fuer neue Stellen:** wer einen `shuffle`, eine Kuerzung auf verdeckten Bestand oder
eine neue ID-Buendelung einbaut, traegt sie hier ein, mit der Antwort auf die beiden Fragen
oben. Ein `shuffle`, der nicht sagen kann, wessen Unwissen er modelliert, ist ein Bug in
Wartestellung -- und eine Buendelung, die nicht sagen kann, welche Entscheidungen sie
absichtlich zusammenlegt, genauso.

## Konstanten mit Fallstrick

- `bonus_points` in `dome.rs` ist ein **Diskriminator** (Special = 3,
  Wild = 0), KEIN Punktwert -- der echte Spezialfeld-Wert ist die Rasterreihe
  1 bis 6.
- `special_empty` zaehlt nur Spezialfelder auf **bereits gelegten** Platten.
- Die Handbuch-Nummerierung der Wertungsplatten ist um eins gegen die
  Code-Indizes verschoben: Handbuch 7 = Code 6 = Spezialfelder.
- `is_col_complete` / `completed_cols` (board.rs:212/220, geprueft 2026-08-28)
  heissen wie die Spaltenbau-Wahrheit, SIND sie aber nicht -- die lebt laut
  Audit-Befund 19 in `scoring.rs:709-712`. Toter Zweitpfad, Abraeumen steht
  auf der Merkliste (STATUS, Abschnitt 1e).
- `scoring_progress` (scoring.rs:160, geprueft 2026-08-28) ist der
  Elo-Anker-Term und haengt NUR an der Heuristik; das Netz hat ihn nie
  bekommen. Nicht anfassen. Die parametrisierte Schwester daneben ist
  ABSICHTLICH eine eigene Funktion (Kommentar scoring.rs:186-194).

## Env-Knoepfe: Fallstricke beim Lesen (aus STATUS herausgeloest 2026-08-30)

- **SECHS Dialekte fuer "ist dieser Bool-Knopf an?"** (shaping.rs:999,
  state.rs:209, tiling_solver.rs:374/386, net_mcts.rs:230): `X=true` schaltet
  je nach Knopf AN oder AUS. Schadensbild: ein A/B-Arm laeuft still als
  Kontrollarm. Geplanter Fix: ein `read_bool_env` neben `read_f64_env`,
  ~18 Stellen.
- **Drei stille Env-Verschlucker** -- `MOSAIC_INTERLEAVE_BATCH_MAX` ausser
  Range (net_batcher.rs:249), `MOSAIC_R5_NODE_BUDGET=0` oder Tippfehler
  (round5.rs:199), `MOSAIC_PLATTENKOPF_GAMES`-Parse (scoring.rs:1508): alle
  fallen wortlos auf den Default. Schadensbild: die Messung glaubt Knopf X und
  faehrt Default. Verwandt mit der Falle "Ein fehlendes Flag meldet sich nicht"
  in `pitfalls.md`, aber anderer Mechanismus (Parse-Fehler statt fehlendem
  Flag).
- **Der Value-Spread-Pfad verkleinert bei eval-Fehlern still den Pool** und
  liefert bei Serialisierungsfehler `"{}"` (self_play.rs:4607/4666).
- **Zwei verschiedene `w`, zwei verschiedene Messungen** (Klarstellung
  2026-08-27): das ROUTING-Gewicht der Huelle auf den Ownership-Marginalen im
  Tiling-Loeser (Verbraucherseite) ist NICHT das Trainings-Loss-Gewicht
  `OWNERSHIP_WEIGHT` / `--ownership-weight`.
- **Das endgame-Ziel ist `root_q` in der R5-Drafting-Zone**
  (corpus_dataset.py:1000-1012), und `root_q` schreibt nur der
  `NetSelfPlayAgent` (self_play.rs:1324). Ein Heuristik-Korpus traegt es
  strukturell nicht, die Maske ist dort komplett 0 -- **kein Bug**. Einmal als
  solcher fehlgedeutet (Endgame-Loss 0,0000 in v22-b01/b02).

## Merkposten ohne Arm (aus geschlossenen Preregs, 2026-09-05)

Hierher wandert, was als Prereg keinen Verbraucher mehr hat, aber nicht
vergessen werden soll. Wer einen Punkt aufnimmt, registriert ihn neu.

- **Sichtgleichheit Spieler/Netz** (`PREREG_stack_top_feature.md`, OFFEN --
  Nutzer 2026-09-05: Sichtgleichheit ist das Ziel, nicht Staerke; der Eintrag
  hier ist nur der Zeiger):
  die offen liegende Rueckseite der obersten Kuppelstapel-Platte sieht der
  Spieler am Tisch, das Netz nicht (par.3 dort). Stufe 0 waere ein
  Sicht-Inventar in beide Richtungen (par.5), Stufe 1 ein ADDITIVER
  Input-Zuschnitt (par.6: neue Kanaele ans Ende, Alt-ONNX bleiben spielbar,
  Input-Shape kommt vom Modell). Kein Staerkeziel; Anlass war eine
  Nutzer-Frage nach der GUI-Aenderung am Stapel-Dialog (Commit 94b9090).
- **Additiver Input-Mechanismus als Baustein** (dieselbe Prereg par.6, von
  `PREREG_uvfa_plate_regime.md` als Abhaengigkeit genannt): jede
  Regime- oder Sicht-Konditionierung des Netzes braucht ihn zuerst.

