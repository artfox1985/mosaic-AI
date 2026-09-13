# Sicht-Asymmetrie-Inventur 2026-09-13

Auftrag: vollstaendige Inventur der Sicht-Asymmetrien zwischen Mensch (Server-GUI und
Tisch) und dem, was Netz und Suche bekommen, in BEIDE Richtungen. Nur-Lesen-Audit
(kein Build, kein Lauf).

Referenz, nicht neu entdeckt: `evaluations/PREREG_stack_top_feature.md` par.10 (P.1-P.8),
par.11 (zweite Achse), par.13/par.14 (P.9), `docs/architecture_reference.md` Abschnitt
"Wo der Code Information ABSICHTLICH vernichtet".

Alle Zeilenangaben in dieser Sitzung am Code geprueft (Stand Arbeitsbaum 2026-09-13).
Wo eine Aussage nicht geprueft ist, steht ANNAHME davor.

---

## 1. NEUE Asymmetrien (ab P.10)

| Nr. | Richtung | Was | Pruefstelle(n) | Sieht der Mensch es | Gewicht | Kodierungsvorschlag |
| --- | --- | --- | --- | --- | --- | --- |
| **P.10** | Suche vergisst (par.11-Klasse) | **Die Wurzel-Determinisierung mischt den UNBEKANNTEN PRAEFIX inklusive Index 0 und kann damit den oeffentlich sichtbaren Typ der obersten Stapelplatte veraendern.** `determinize_dome_pool` mischt `dome_tile_pool[..prefix_len]`; die Bloecke liegen am unteren Ende, der Praefix ist das obere Ende, Index 0 ist die oberste Platte. Genau deren Rueckseite ist oeffentlich (P.2, in v24-b04 als Abschnitt 12 gebaut). Der Wurzelknoten wird NACH der Determinisierung gebaut, die Merkmale kommen aus diesem Zustand. | `state.rs:242-243` (`prefix_len`, `[..prefix_len].shuffle`), `net_mcts.rs:1385-1393/1405-1410` (Aufruf), `net_mcts.rs:4938-4943` und `:4586-4590` (determinisieren, dann `make_node`), `make_node` `net_mcts.rs:2503-2514`, `features_for_net` `features.rs:1413`, Merkmal `features.rs:597-599` (JSON) / `:1044-1046` (direkt), Quelle `serialize.rs:357-363` | Ja, am Tisch jederzeit: `docs/engine_manual.md:85` ("the plate backs reveal only the type"); GUI `static/js/app.js` `dome_stack_top_type` (6 Treffer, u.a. `stackTopTypeIcon()`) | jede Suche, in der der Stapel einen unbekannten Praefix > 0 hat, also praktisch jeder Drafting-Zug der Runden 1-4 | keine neuen Eingaenge: Index 0 aus dem Mischen ausnehmen, solange der Typ oeffentlich ist. Korrekte Variante: Praefix so permutieren, dass Position 0 den TYP behaelt (getrennte Permutation der wild- und special-Teilmenge oder Swap-zurueck von Position 0) |
| **P.11** | Mensch > Netz | **Anzahl der gehaltenen Bonuschips fehlt; kodiert wird nur die Farbsumme ueber alle Chips.** Ein Einfarb-Chip liefert einen Zaehler, ein Zweifarb-Chip zwei. `{Blau} + {Rot}` (zwei Chips) und `{Blau,Rot}` (ein Chip) ergeben denselben Vektor. Die Vollendungsregel haengt aber an der ANZAHL: "zwei farbgleiche ODER drei beliebige Chips je fehlender Fliese". | Encoder `features.rs:381-396` (JSON-Pfad) und `:874-887` (Direktpfad); Server gibt `bonus_chips` (`serialize.rs:250`) UND `unused_chip_count` (`serialize.rs:255`) aus, `unused_chip_count` hat 0 Treffer in `features.rs`; Regel `round_end.rs:494-517` (`greedy_chip_indices`, `same.len() >= 2` sonst `pool.len() >= 3`), `round_end.rs:457-478` | Ja: GUI rendert jeden Chip einzeln (`app.js:1265-1275`, `:2302`), dazu Ghosts verbrauchter Chips (`app.js:977-1032`) | jede Runde: 2 Chips je Spieler und Runde sind Pflicht (`board.rs:384`, `BONUS_CHIPS_PER_ROUND`) | additiv, 2 Werte: `bonus_chips.len()/4` je Spieler in Zugreihenfolge. Optional 2 weitere: Anzahl der Zweifarb-Chips /4 |
| **P.12** | Mensch > Netz | **Design-Identitaet der Platten in den bekannten Rueckgabe-Bloecken.** Der Spieler sieht bei JEDER Ziehserie (auch der des Gegners) die Vorderseiten der gezogenen Platten und weiss damit, WELCHE Designs zurueckgelegt wurden; nur die Reihenfolge fremder Bloecke ist ihm verborgen. Kodiert werden je Gruppe nur Laenge und Anzahl special/wild, plus Typ (+1/-1/0) der obersten 4 Positionen des obersten EIGENEN Blocks. | `serialize.rs:103-128` (`dome_pool_view`: `len`, `special`, `wild`, `types` nur bei `own`), `features.rs:116-127` (`DomePoolKnowledge`), `:129-159` (die elf Werte), `:167-196` (JSON) / `:212-245` (direkt); Regelstelle `docs/engine_manual.md:86-90` | Am Tisch ja (Regelstelle oben). In der GUI NICHT: `dome_pool_view` hat 0 Treffer in `app.js` (siehe P.15) | jede Ziehserie; Ziehen ist die Standard-Alternative zur Auslage | 18 Bits "Design liegt in einem mir bekannten Block" (tile_id-Reihenfolge); optional getrennt eigen/fremd, dann 36 Bits |
| **P.13** | Mensch > Netz | **Blockstruktur des Stapels ist auf Summen zusammengezogen:** eigene und fremde Bloecke werden je zu `len`/`special`/`wild` addiert; die TIEFE eines Blocks im Stapel und die Verschachtelung (eigen/fremd/eigen) fallen weg, die Positionstypen gibt es nur fuer den obersten eigenen Block und nur fuer 4 Positionen. | `features.rs:116-127` (`own_len`/`own_special`/`own_wild`, `foreign_*`, `top_types: [f32; DOME_POOL_TOP_TYPES]`), `:146-159`, `:212-245` (`if !own_seen` -> nur der erste eigene Block bekommt Positionstypen) | Am Tisch ja (der Spieler weiss, wo sein Block liegt); GUI nein | seltener als P.12: greift erst ab dem zweiten eigenen Rueckgabe-Block oder bei Bloecken laenger als 4 | Blockliste fester Laenge, z.B. 6 x (ist_eigen, `len`/18, `special`/9, Tiefe/18) = 24 Werte |
| **P.14** | Mensch > Netz | **`tiled_max_row` (Oben-nach-unten-Sperre in der Tiling-Phase) ist weder in `state_to_json` noch im Merkmalsvektor.** Die Anzeige-Serialisierung liest das Feld nur INTERN, um `chippable_tiling_rows` zu filtern; ausgegeben wird es nur in `state_to_json_exact` als `tiled_max_row_exact` (Referee-Transport, kein Netz-Eingang). Welche VOLLEN Reihen gesperrt sind, sieht das Netz damit nicht. | Feld `board.rs:259`; nur intern `serialize.rs:678`; `state_to_json` (`serialize.rs:337-385`) enthaelt es nicht; `state_to_json_exact` `serialize.rs:1328-1329`; `features.rs` liest es nur intern in `chippable_pairs_direct` `:737`; Regel `docs/engine_manual.md:131-134` | Ja: GUI baut daraus die Reihen-Steuerung (`app.js:1060-1087`, `getTilingRowState`, aus `valid_tiling_rows`/`chippable_tiling_rows`) | nur Tiling-Phase; das Netz wird dort als Tiebreak befragt (`self_play.rs:1856-1899`, Aktionstypen `tiling`/`end_tiling`) | 1 Wert je Spieler: `(tiled_max_row + 1)/6` |
| **P.15** | Mensch > Netz | **`first_player_next_round` wird nie kodiert, und `holds_first_player_marker` wird bei JEDER Rundenwertung geloescht.** Nach `score_penalty` und bis zur naechsten Markernahme steht im Merkmalsvektor fuer beide Spieler 0; bei Punktegleichstand entscheidet `first_player_next_round` aber das SPIEL. | Ausgabe `serialize.rs:348`; 0 Treffer fuer `first_player_next_round` in `features.rs`; Loeschung `round_end.rs:438-441`; Sieger-Tiebreak `game.rs:620-635` | Ja: GUI nutzt genau dieses Feld (`app.js:1612`, `:3443`) | selten, aber am Partie-Ende entscheidungsrelevant (WDL-Kopf) | 1 Wert: `first_player_next_round == ego` |
| **P.16** | Netz > Mensch (nur GUI, nicht Tisch) | **`dome_pool_view` wird dem Menschen in der Server-GUI ueberhaupt nicht angezeigt**, waehrend das Netz daraus elf Werte bekommt. Am Tisch hat der Mensch die Information aus dem Gedaechtnis; in der GUI muss er sie selbst mitschreiben. | Server `serialize.rs:379`; Encoder `features.rs:673`; `dome_pool_view` 0 Treffer in `static/js/app.js` | Tisch ja, GUI nein | jede Runde mit Ziehserien | keine Kodierung; GUI-Anzeige (Block-Liste mit eigenen Typen) |
| **P.17** | Netz > Mensch (Rechenvorsprung, KEINE verdeckte Information) | Der Zustand liefert dem Netz fertig gerechnete Groessen, die ein Mensch am Tisch selbst ausrechnen muesste: `estimated_score` ist ein EXAKTER Tiling-Solver ueber die optimale Platzierung, `col_f_max`, `cell_reachable_mask` (Plane 76), `score_geo`, `line_geo`, `chippable_tiling_rows`. Alle sind Funktionen des oeffentlichen Zustands (geprueft: `remaining_colors` zaehlt ausschliesslich Fabriken, Musterreihen, Strafleiste und Kuppel und zieht Phantome ab, NICHT den Beutelinhalt). | `serialize.rs:206-221` (`estimated_score`, `f_max`, `reachable_mask`), `tiling_solver.rs:497-504`, `provocation.rs:588-634` (`remaining_colors`, Doku `:570-587`), Encoder `features.rs:360` / `:566-580` / `:1362-1370` (Plane 76) | `estimated_score` zeigt die GUI (`app.js:1236`); `col_f_max` und `cell_reachable_mask` zeigt sie NICHT (je 0 Treffer) | jede Entscheidung | keine; nur zur Vollstaendigkeit der Inventur. Kein verdecktes Wissen |

---

## 2. Status der bekannten P.1 bis P.9 am Code

| Nr. | Thema | Status | Pruefstelle |
| --- | --- | --- | --- |
| P.1 | Typ der drei ausliegenden Kuppelplatten (wild gegen special) | **geschlossen** | `features.rs:600-618` (JSON) / `:1047-1059` (direkt), je Slot `has_special`/`has_wild`; Python-Zwilling `engine/py/neural_net.py:357-378` |
| P.2 | Rueckseite der obersten Stapelplatte | **im Encoder geschlossen, in der SUCHE wieder aufgerissen** | Merkmal `features.rs:597-599` / `:1044-1046`, Quelle `serialize.rs:357-363`; Aufreissen: siehe P.10 (`state.rs:243`) |
| P.3 | Laufende Ziehserie (`pending_stack_draw`) | **offen, nicht gebaut** | Ausgabe `serialize.rs:368`; 0 Treffer fuer `pending_stack_draw` in `features.rs` und `engine/py/neural_net.py`; eingetaktet fuer v29 (`PREREG_stack_top_feature.md` par.13) |
| P.4 | Historie / Log | **bewusst kein Merkposten** (Nutzer-Entscheid 2026-09-05) | `serialize.rs:307-311/381` (30 sichtbare Zeilen), 0 Treffer fuer `"log"` in `features.rs` |
| P.5 | Farben der Strafleisten-Fliesen | **geschlossen** | `features.rs:638-655` (JSON) / Direktpfad Abschnitt 13; Quelle `serialize.rs:246` |
| P.6 | Phantom-Fliesen in Musterreihen | **geschlossen** | `features.rs:656-667`, Quelle `serialize.rs:241`; Python `neural_net.py:404` |
| P.7 | Phasenaufloesung | **offen**; `phase_id` faltet `start_placement`, `drafting` UND `scoring` auf 0, nur `tiling`/`end`/`final` sind getrennt | `features.rs:62-68`, Phasen `state.rs:40-48`, Ausgabe `serialize.rs:340` |
| P.8 | Nur erster Mondstapel je Fabrik, oberste 3 Steine | **geschlossen, kein Randfall** (in dieser Sitzung nachgeprueft) | `factory.rs:42-58` (`take_from_sun` leert die Sonnenseite), `:60-66` (`place_on_moon` legt EINEN Stapel), Mondseite wird beim Rundenwechsel geleert (`game.rs:1486`); Encoder `features.rs:499-517` liest `stacks.first()`, oberste 3 |
| P.9 | Beutel/Turm-Aufteilung je Farbe | **offen, Vorschlag registriert** | Encoder addiert: `features.rs:265-269` (JSON) / `:767-776` (direkt), Python `neural_net.py:124-128`; Zustand getrennt `serialize.rs:370-371`; GUI nur Summen `app.js:1808-1812` |

---

## 3. Diff-Tabellen zum Nachpruefen

### 3a. Server gibt aus (`serialize.rs::state_to_json`, Zeilen 337-385) gegen Encoder

| Feld | serialize.rs | features.rs (JSON-Pfad) | Verlust |
| --- | --- | --- | --- |
| `round` | 338 | 253 | keiner |
| `scoring_confirmed` | 339 | nicht gelesen | GUI-Flag |
| `phase` | 340 | 254-255 (`phase_id`, `:62-68`) | P.7 |
| `current_player` | 341 | 351, 567, 635 | keiner (Perspektive) |
| `first_player_next_round` | 348 | **nicht gelesen** | **P.15** |
| `scoring_tile_ids` | 349 | 289-296 | keiner |
| `can_pass` | 350 | nicht gelesen | aus der Zugmaske ableitbar |
| `factories[].sun` | 183 | 301-313 | Farbzaehler statt Liste, verlustfrei |
| `factories[].moon` | 184-186 | 499-517 | nur erster Stapel, oberste 3 (P.8: kein Verlust) |
| `factories[].bonus_chip` / `chip_revealed` | 187-188 | 314-331 | Farben nur bei `revealed` (korrekt) |
| `large_factory.sun` / `.moon` | 194-195 | 335-347, 519-531 | Farbzaehler, verlustfrei |
| `large_factory.marker` | 196 | **nicht gelesen** | ableitbar (kein Spieler haelt ihn), siehe P.15 fuer den Sonderfall nach der Wertung |
| `moon_top_counts` / `moon_top_colors` | 353-354 | nicht gelesen | ableitbar aus `moon` |
| `dome_display` | 355 | 534-554 (Abschnitt 9), 600-618 (Abschnitt 12) | Design bis auf Rotation bestimmt; `bonus` redundant zu special/wild (`dome.rs:124-128`) |
| `dome_stack_count` | 356 | 557 | keiner |
| `dome_stack_top_type` | 361 | 597-599 | im Encoder keiner, in der Suche P.10 |
| `pending_stack_draw` | 368 | **nicht gelesen** | **P.3** |
| `bag_count` | 369 | 257 | keiner |
| `bag_colors`, `tower_colors` | 370-371 | 265-269 (SUMME) | **P.9** |
| `dome_pool_mask` | 372 | 274-277 | keiner (18 Bits) |
| `dome_wild_remaining_frac` | 373 | 282-286 | keiner |
| `dome_pool_view` | 379 | 673 (elf Werte, `:129-159`) | **P.12, P.13** |
| `players` | 380 | siehe 3b | |
| `log` | 381 | **nicht gelesen** | P.4 (Entscheid) |
| `valid_moves`, `valid_tiling_rows` | 382-383 | nicht gelesen | `valid_tiling_rows` haette `tiled_max_row` getragen, **P.14** |
| `chippable_tiling_rows` | 384 | 355, 399-405 | nur Reihen 1..5; Reihe 0 kann nie chippable sein (Kapazitaet 1, `serialize.rs:679-681` filtert `is_complete`), kein Verlust |

### 3b. Spielerfelder (`serialize.rs::serialize_player`, Zeilen 229-296)

| Feld | serialize.rs | features.rs | Verlust |
| --- | --- | --- | --- |
| `id`, `name` | 230-231 | nicht gelesen | irrelevant |
| `score` | 232 | 359 | keiner |
| `pattern_lines.capacity/tiles/color` | 235-237 | 365-372 | Fuellgrad + Farb-One-Hot, verlustfrei (Reihe ist einfarbig) |
| `pattern_lines.phantom_count` | 241 | 656-667 | keiner (P.6) |
| `dome_grid` | 243-245 | 410-444 (9x17) | keiner |
| `floor` | 246 | 376-377 (Anzahl), 638-655 (Farben) | keiner (P.5) |
| `marker` | 247 | 361 | siehe P.15 |
| `tokens_used` | 248 | 378 | keiner |
| `chips_taken` | 249 | 379 | keiner |
| `bonus_chips` | 250 | 381-396 (Farbsummen) | **P.11** |
| `start_placed` | 251 | nicht gelesen | nur Phase `start_placement`; ANNAHME: durch die Zugmaske folgenlos, nicht geprueft |
| `start_tile` | 252 | nicht gelesen | ist immer `Value::Null` (tote Ausgabe; `start_dome_tile` wird nur in `board.rs:264/311` und `serialize.rs:1003/1838` beruehrt) |
| `can_place_dome` | 253 | nicht gelesen | **ableitbar, kein Verlust**: `register_dome_placement` und `use_player_token` werden immer gemeinsam gerufen (`game.rs:72-73`, `:315-316`), also ist `tokens_used` == `dome_tiles_placed_this_round`; Rest der Bedingung ist `round` und Slotbelegung (`board.rs:372-381`), beides kodiert |
| `estimated_score` | 254 | 360 | keiner (P.17) |
| `unused_chip_count` | 255 | **nicht gelesen** | **P.11** |
| `unused_chip_colors` | 256 | nicht gelesen | redundant zu `bonus_chips` |
| `scoring_tile_points` | 258 | 449-453 | keiner |
| `score_geo` | 259-270 | 454-476 | keiner |
| `line_geo` | 272-278 | 480-495 | keiner |
| `cell_reachable_mask` | 292 | **im Rust-Flachvektor gar nicht**; nur `neural_net.py:615-619` liest es, der Rust-2D-Zweig rechnet es neu (`features.rs:1354-1370`) | kein Sichtverlust, aber der Kommentar `serialize.rs:281-285` ("Der JSON-Pfad ... LESEN diese Felder") ist fuer `cell_reachable_mask` falsch: 0 Treffer in `features.rs` |
| `col_f_max` | 295 | 566-580 | **nur fuer den ZIEHENDEN Spieler**, der Gegner fehlt; aus oeffentlichem Zustand rechenbar |

### 3c. Zustandsfelder, die `state_to_json` gar nicht ausgibt

| Feld | Ort | Urteil |
| --- | --- | --- |
| `bag.tiles`, `tower.tiles` (Inhalt) | `state.rs:66-67` | richtig verdeckt; der Direktpfad liest sie nur als Farbsumme (`features.rs:767-776`), byte-gleich zum JSON-Pfad |
| `dome_tile_pool` (Reihenfolge) | `state.rs:74` | richtig verdeckt; Encoder liest nur Multimenge (`features.rs:785-799`) und `first()` als Typ (`:1044`) |
| `dome_pool_known_blocks` | `state.rs:86` | seitenabhaengig, geht als `dome_pool_view` gefiltert heraus (`serialize.rs:97-133`); exakt nur ueber `state_to_json_exact` (`architecture_reference.md:129-136`) |
| `bonus_chip_pool` | `state.rs:88` | richtig verdeckt |
| `pending_dome_choice` | `state.rs:100` | nur in `state_to_json_exact` (`serialize.rs:1381-1403`); 0 Treffer in `features.rs`, in `net_mcts.rs` nur zwei Kommentare (`:1456`, `:5554`) |
| `tiled_max_row` | `board.rs:259` | **P.14** |
| `score_unclamped` | `board.rs:254` | reines Trainingsziel, 0 Treffer in `features.rs` |
| `total_floor_penalties`, `floor_penalties_per_round`, `long_rows_*` | `board.rs:270-293` | Beobachtungszaehler, weder GUI noch Netz |

---

## 4. Zeit-Achse (par.11): traegt der Zustand es, gibt der Encoder es weiter, laesst die Suche es stehen

| Information, die der Spieler aufbaut | Zustand | Encoder | Suche |
| --- | --- | --- | --- |
| Rueckseite der obersten Stapelplatte | ja (`dome_tile_pool[0]`) | ja (`features.rs:597`) | **NEIN, P.10** (`state.rs:243`) |
| Eigene Rueckleg-Reihenfolge | ja (`dome_pool_known_blocks`, `state.rs:86`) | teilweise (oberster eigener Block, 4 Positionen, `features.rs:212-245`) | ja, eigener Block bleibt stehen (`state.rs:248`) |
| Gesehene Vorderseiten fremder Ziehserien | ja (die Platten liegen im Block) | **nein, nur Anzahl special/wild (P.12)** | ja, Multimenge je Block bleibt erhalten (`state.rs:249`) |
| Mitgezaehlter Turm je Farbe | ja (`tower_colors`, `serialize.rs:371`) | **nein, addiert (P.9)** | irrelevant: `bag`/`tower` haben 0 Treffer in `net_mcts.rs`, die Suche spielt den Rundenuebergang nicht |
| Gezogene Chips / Restvorrat | teilweise (`bonus_chip_pool` verdeckt, verbrauchte Chips werden aus `bonus_chips` entfernt, `app.js:977-987`) | nein (nur `chips_taken` je Runde, `features.rs:379`) | verdeckte Chips werden korrekt gemischt, aufgedeckte bleiben (`net_mcts.rs:1412-1431`) |
| Anzahl der gehaltenen Chips | ja (`bonus_chips`) | **nein (P.11)** | ja |
| Startspieler-Historie / wer eroeffnet | ja (`first_player_next_round`) | **nein (P.15)** | ja (Feld bleibt stehen) |
| Reihenfolge der Mondstapel | ja | ja (`features.rs:499-517`) | ja |
| Sperre der Tiling-Reihen | ja (`tiled_max_row`) | **nein (P.14)** | ja |

---

## 5. Verdecktes Wissen der Suche: ausdrueckliche Pruefungen

| Frage | Befund | Pruefstelle |
| --- | --- | --- |
| Liest `net_mcts.rs` `bag` oder `tower`? | **nein, 0 Treffer** | grep ueber `engine/src/net_mcts.rs` |
| Liest `features.rs` den Beutel-/Turm-INHALT? | nur als Farbsumme, spiegelbildlich zum JSON-Pfad | `features.rs:767-776` |
| Liest der Encoder die Stapel-REIHENFOLGE? | nein: Multimenge (Maske, Wildanteil) plus oberste Platte als TYP | `features.rs:785-799`, `:1044-1046` |
| Verdeckte Bonuschips? | korrekt: nur `revealed` gibt Farben, unaufgedeckte werden gemischt, aufgedeckte bleiben unangetastet | `features.rs:315-331`, `net_mcts.rs:1412-1431` |
| `pending_dome_choice`? | nirgends als Merkmal, nur Kommentare | 0 Treffer `features.rs`; `net_mcts.rs:1456`, `:5554` |
| Leckt `remaining_colors` (Basis von `col_f_max`, `cell_reachable_mask`) den Beutelinhalt? | **nein**, zaehlt nur oeffentlich Sichtbares und zieht Phantome ab | `provocation.rs:570-587` (Doku), `:588-634` (Rumpf) |
| Determinisiert jeder Sucheinstieg? | `build_net_tree` (`:4938`), `build_gumbel_tree_inner` (`:4586`), `search_start_placement` mit explizitem Betrachter (`architecture_reference.md:115`); `build_determinized_forest` geht ueber `build_net_tree` (`:5561`) | wie angegeben |
| `SHUFFLE_STACK_PEEK_IN_SEARCH` | ruhend (`false`) | `architecture_reference.md:113` |

---

## 6. Was NICHT geprueft werden konnte

1. **Alles Laufzeitgestuetzte.** Auftrag war Nur-Lesen (exklusive Messung auf der Maschine):
   kein `cargo`, kein `python`. Damit ungeprueft: wie oft `prefix_len >= 1` tatsaechlich gilt
   und wie oft die Determinisierung den Typ der obersten Platte KIPPT (P.10). Die Aussage
   "der Praefix enthaelt Index 0" ist aus `state.rs:242-243` plus der Blocklage am unteren
   Ende (`serialize.rs:92-93`, `:100-128`) abgeleitet, nicht gemessen.
2. **Python-Zwilling nur punktuell.** `engine/py/neural_net.py` wurde fuer die Abschnitte 12
   bis 15 und fuer `bag_colors`/`tower_colors`/`cell_reachable_mask` gelesen
   (`:124-128`, `:357-427`, `:615-619`). Fuer die Abschnitte 1 bis 11 verlasse ich mich auf
   die Paritaetstests, die ich nicht ausfuehren durfte: ANNAHME.
3. **Direktpfad gegen JSON-Pfad.** Byte-Gleichheit ist durch
   `direct_matches_json_path_*` bewacht (`features.rs:685-689` Doku); stichprobenartig
   nachgelesen (Abschnitte 1, 5, 12), nicht Zeile fuer Zeile diffed.
4. **`state_to_json_exact`** (Referee-/Worker-Transport) wurde nur daraufhin angesehen,
   ob Felder daraus in den Netz-Eingang gelangen (tun sie nicht). Ein vollstaendiger Diff
   Anzeige gegen Exakt fehlt.
5. **Gewicht von P.14** (Tiling-Sperre): dass das Netz in der Tiling-Phase ueberhaupt
   befragt wird, ist an `self_play.rs:1856-1899` und `NET_TILING_TIEBREAK_ENABLED` belegt;
   WIE oft und mit welchem Anteil an der Entscheidung, ist ungeprueft.
6. **Regelfragen** wurden nur gegen `docs/engine_manual.md` geprueft, nicht gegen das
   Originalregelwerk.
