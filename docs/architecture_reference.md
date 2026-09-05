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
- Gumbel-Suche aktiv: `GUMBEL_TOP_M = 16`, `GUMBEL_C_SCALE = 1,0`,
  `DEFAULT_C_PUCT = 1,5`, `floor_shaping_weight = 0,3`.
- `VALUE_SHRINK_ENABLED = false`, `ROUND_TRANSITION_SAMPLING = false`,
  `SHUFFLE_STACK_PEEK_IN_SEARCH = false`, `bootstrap_horizon_rounds = 2`.
- **Runde 5 ist Expectiminimax** mit Zufallsknoten an den Chip-Aufdeckstellen;
  `NODE_BUDGET = 200` ist eine Bezahlbarkeits-, keine Hinreichenszahl --
  **kein geloestes Endspiel** (~3 Halbzuege, Orakel-Uebereinstimmung 81,4
  Prozent). Der frueher hier genannte zweite, eingefrorene Loeser
  `round5_anchor.rs` ist mit B4b **entfernt** (2026-08-27); der Anker-Schutz
  liegt seither im Artefakt `models/frozen_heuristics/hv1_anchor`, und eine
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

- **`INPUT_SIZE = 714`** (config.py:38; seit 2026-08-25 plus 6 `col_f_max`),
  **`NUM_ACTIONS = 406`** (config.py:43).
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

- **Sichtgleichheit Spieler/Netz** (`PREREG_stack_top_feature.md`, UEBERHOLT):
  die offen liegende Rueckseite der obersten Kuppelstapel-Platte sieht der
  Spieler am Tisch, das Netz nicht (par.3 dort). Stufe 0 waere ein
  Sicht-Inventar in beide Richtungen (par.5), Stufe 1 ein ADDITIVER
  Input-Zuschnitt (par.6: neue Kanaele ans Ende, Alt-ONNX bleiben spielbar,
  Input-Shape kommt vom Modell). Kein Staerkeziel; Anlass war eine
  Nutzer-Frage nach der GUI-Aenderung am Stapel-Dialog (Commit 94b9090).
- **Additiver Input-Mechanismus als Baustein** (dieselbe Prereg par.6, von
  `PREREG_uvfa_plate_regime.md` als Abhaengigkeit genannt): jede
  Regime- oder Sicht-Konditionierung des Netzes braucht ihn zuerst.

