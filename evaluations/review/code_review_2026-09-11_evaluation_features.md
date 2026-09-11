# Code-Review 2026-09-11: Heuristik-Bewertung, Merkmale, Tiling-Loeser

**Datum:** 2026-09-11. **Art:** reines Lese-Review, keine Aenderung, kein Build,
kein Lauf (Trainings-/Arena-Kette laeuft).

**Gelesen** (Pfade relativ zu `engine/src/`): `features.rs` 2405 vollstaendig,
`envelope.rs` 2227 vollstaendig, `column_build.rs` 1-1258 (Produktivteil) plus
Tests ueberflogen, `plate_builder.rs` 1-1332 vollstaendig, `provocation.rs`
1-919 vollstaendig, `shaping.rs` 1044 vollstaendig, `tiling_solver.rs` 1-1700
vollstaendig plus Tests ueberflogen. Quergelesen: `serialize.rs:97-198`,
`factory.rs:55-113`, `round_end.rs:625-640`, `self_play.rs:6100-6125`,
`docs/knobs.md`, `docs/architecture_reference.md`,
`docs/engine_manual.md:95-125`, `knob_registry.rs`.

**Methode "kein Aufrufer":** je Funktionsname gegreppt ueber `engine/src`,
`engine/examples`, `engine/benches`; Treffer in Doc-Kommentaren sind separat
ausgewiesen.

---

## 1. Bugs und Korrektheitsrisiken

### 1.1 Phantom-Fliesen verfaelschen `remaining_colors` (schwerwiegend)

`round_end.rs:635-638` schiebt Phantom-Fliesen als ECHTE Eintraege in
`pattern_lines[row].tiles` und zaehlt sie zusaetzlich in `phantom_count`.
`self_play.rs:6111-6117` rechnet sie an seiner Zaehlstelle ausdruecklich wieder
heraus ("sind nie real gezogen worden ... sonst waere die Zahl kurzzeitig
aufgeblaeht").

`provocation::remaining_colors` (provocation.rs:611-616) tut das NICHT: sie
zaehlt `line.tiles` roh, bucht also Phantome als verbraucht. Der Restvorrat
faellt zu niedrig aus. Dasselbe fuer die Gegnerreihen in
`still_reachable_colors` (provocation.rs:679-683).

Konsumentenkette: `column_build::cell_is_completable` (column_build.rs:563-578)
-> Planes-Kanal 76 "Erreichbarkeit" (features.rs:1363-1368),
`envelope::dead_hull_mass_in` (envelope.rs:988-1005, K3-D) und K3-R
(envelope.rs:1151); `plate_builder::achievable_column_fill`
(plate_builder.rs:713-726) -> `col_f_max`, Flachmerkmale 708-713
(features.rs:566-580 / 1027-1036); dazu `column_cost`, `scarcity_surcharge`
und jeder Bauer-Vorzug.

Fehlerrichtung eindeutig: Restvorrat zu klein, also "nicht mehr vollendbar" zu
oft. Kanal 76 meldet 0, `col_f_max` faellt, K3-D zaehlt lebende Zellen als tot.
Haeufigkeit UNGEPRUEFT (kein Lauf erlaubt); jeder Spieler nimmt zwei Chips je
Runde, selten duerfte es nicht sein.

Bemerkenswert: derselbe Sachverhalt steht im Flachvektor RICHTIG. Abschnitt 1
"Beutel+Turm je Farbe" liest `state.bag.tiles`/`state.tower.tiles` direkt
(features.rs:770-781) und enthaelt keine Phantome. Das Netz bekommt zwei
einander widersprechende Vorratssignale.

Klasse "symmetrischer Defekt" nach CLAUDE.md: gleiches Weltmodell fuer beide
Seiten, kuerzt sich in jeder Arena weg.

### 1.2 Mondstapel: das Netz sieht nur den ERSTEN Stapel je Fabrik

`Factory::moon_stacks` ist `Vec<Vec<TileColor>>`; `place_on_moon`
(factory.rs:62-66) legt je Sonnenzug einen NEUEN Stapel an, und nichts im
Rundenwechsel raeumt sie ab (grep `moon` in `round_transition.rs`/`round_end.rs`:
kein Treffer). Ab Runde 2 traegt eine Fabrik mehrere Stapel.

Beide Merkmalsbauer lesen nur `moon_stacks.first()` und davon die obersten drei
Positionen: features.rs:501-513 (JSON) und features.rs:974-984 (direkt). Die
Oberseiten aller weiteren Stapel fehlen dem Netz.

`docs/engine_manual.md:104-106`: Aktion C nimmt "jede oberste Fliese einer Farbe
ueber alle Mondbereiche, eine je Stapel". Die Heuristiken sehen alle Stapel
(`mcts.rs:603`, `provocation.rs:599-603`, `factory.rs:73-83`), das Netz nicht.
Kein Leck, sondern eine Luecke -- die Achse aus `PREREG_stack_top_feature.md`.

### 1.3 Sichtfrage Mondstapel-Tiefe (unklar)

`serialize_factory` (serialize.rs:184-186) gibt den VOLLSTAENDIGEN Stapel an
beide Seiten. Das Handbuch sagt, der nehmende Spieler bestimme die
Stapelreihenfolge und nur die oberste Fliese sei spaeter nehmbar
(engine_manual.md:100-102). Ob die darunterliegenden fuer den Gegner sichtbar
sind, ist aus Code und Handbuch nicht entscheidbar: **unklar**. Falls nein,
waere features.rs:503-511 (Positionen unter der Spitze) ein Sicht-Leck und
gehoerte in die Naht-Liste in `docs/architecture_reference.md`. Nutzer-Frage,
keine Reparatur.

### 1.4 K3-P2: Belegung fuer Huelle A, Bewertung womoeglich mit Huelle B

`envelope_score_projected_slot_in` (envelope.rs:701-708) baut je Orientierung
eine eigene Belegung via `projected_occupancy_slot_in(board, hull, ..)`,
bewertet sie dann aber mit `envelope_score_frac_in(&occ, form)` -- und das
waehlt die Huelle intern neu nach `deviation_frac` (envelope.rs:359-360). Die
Platzhalter-Masse kann so als "ausserhalb", also NEGATIV, gezaehlt werden.

Der K3-F-Zweig macht es anders: `envelope_score_flush_in` (envelope.rs:673-688)
nimmt `envelope_score_frac_for_in(&occ, hull, form)`, also die FESTE
Orientierung. Dieselbe Asymmetrie noch in `envelope_score_mode_with_cells`
Modus 4 (envelope.rs:1165-1177) und im K5-Zweig (envelope.rs:1113-1127).

Die Doku (envelope.rs:690-695) beschreibt das Verhalten korrekt, begruendet es
aber nicht. Ob gewollt: **unklar**.

### 1.5 Doku der Jokerfeld-Regel widerspricht dem Code

envelope.rs:917-934 sagt zweimal, die Regel greife fuer jede Zelle "die zu einer
BEREITS GELEGTEN Kuppelplatte gehoert" (Praedikat `get_space(..).is_some()`) und
`out_wild_w = 1` schalte den Aussen-Abzug "praktisch ganz ab". Der
Funktions-Doc-Kommentar (envelope.rs:1007-1010) sagt dasselbe. Der Code prueft
`space_type == SpaceType::Wild` (envelope.rs:1029-1033); der Inline-Kommentar
direkt darueber (envelope.rs:1020-1026) beschreibt genau das und nennt die
erste Fassung verworfen. `docs/knobs.md:141` steht auf der Seite des Codes.
Zwei ueberholte Doku-Stellen im selben Modul.

### 1.6 Merkmalsbauer indiziert `current_player` ungeprueft

`state_to_features` nimmt `curr_pi` roh aus dem Record und indiziert direkt:
features.rs:351-354 (`players[curr_pi]`, `enemy_pi = 1 - curr_pi`). Bei
`current_player > 1` gibt es usize-Underflow und Index-Panic, obwohl
`players.len() == 2` geprueft ist. Dieselbe Funktion ist an zwei anderen
Stellen defensiv: features.rs:637 klemmt mit `.min(1)`, features.rs:566-572
nimmt `.get(pi)`. Der Direktpfad (features.rs:849-852) ist unkritisch.

### 1.7 Moeglicher Index-Panic bei NaN im Huellen-Tiling-Zweig

`best_first_step_envelope_valued` (tiling_solver.rs:1657-1659, :1678) bildet
`best` per `fold(NEG_INFINITY, f64::max)` und filtert danach `tied`. `f64::max`
uebergeht NaN; waeren ALLE Scores NaN, bliebe `tied` leer und `tied[0]` panikt.
Erreichbar nur ueber ein NaN aus `margin_evaluator` (tiling_solver.rs:1648) --
ob das vorkommen kann: **unklar**. `tied.first()?` waere ein Einzeiler.

### 1.8 Zwei `partial_cmp(..).unwrap()` auf f64

column_build.rs:602 und :1218. Die Kostenformel (`cell_cost`
column_build.rs:277-295, `scarcity_surcharge` :330-336) liefert nur endliche
Werte, ein NaN ist von dort nicht erzeugbar. Es sind die einzigen zwei `unwrap`
im Produktivteil des ganzen Bereichs; `features.rs:1426` ist der einzige
`panic!` und dokumentiert absichtlich.

### 1.9 Geprueft und in Ordnung

- **Huellenkosten 56/62:** `hull_total_cost` (envelope.rs:115-120) per Test
  nachgerechnet (envelope.rs:1498-1535: 21 Zellen / 56, 22 / 62, `Triangle`
  Zelle fuer Zelle identisch zu `contains`).
- **Kuppelstapel-Wissen (Abschnitt 15):** beide Pfade (features.rs:167-206 aus
  `dome_pool_view`, :212-246 aus dem `GameState`) benutzen dieselbe Sichtregel
  wie `serialize::dome_pool_view` (serialize.rs:97-133), inklusive derselben
  unsaturierten `b.len`-Laenge und derselben Saettigung am Poolende. Kein Leck:
  fremde Bloecke nur als Menge, Praefix nur als Laenge.
- **Planes-Kanaele:** alle 79 haben einen Konsumenten;
  `NUM_PLANES_CHANNELS = 79` in features.rs:1136 und
  `engine/py/neural_net.py:517` stimmen ueberein.
- **Tiling-Loeser:** Spezialfeld-Bonus, Nachbarn und Chips laufen ueber
  `execute_full_tiling`/`apply_bonus_chips_with` (tiling_solver.rs:173-189);
  der Cache-Schluessel (tiling_solver.rs:244-337) deckt jedes ergebnisrelevante
  Feld ab und traegt die Werte selbst statt nur einen Hash.

---

## 2. Tote und ueberholte Pfade

**2.1 `envelope.rs`: 37 von 64 oeffentlichen Funktionen ohne externen Treffer.**
Tatsaechlich von aussen AUFGERUFEN werden nur `search_shift_state`
(net_mcts.rs:2348), `envelope_score` (tiling_solver.rs:1636, :1642),
`adjusted_tiling_score_with_value` (:1650), `row_cost` (plate_builder.rs:805),
`profile_weight` und die acht Env-Getter fuer `SearchConfig::from_env`. Vier
weitere Namen (`row_can_serve_hull`, `apply_row6_special_in`,
`dead_hull_mass_in`, `outside_wild_mass_in`) stehen ausserhalb NUR in
Doc-Kommentaren (net_mcts.rs:438/454/463/470). Ursache ist das Paar-Muster `X`
(Dreieck) / `X_in` (mit `HullForm`); die Dreiecks-Variante wird meist nur noch
vom Bitidentitaets-Test benutzt (envelope.rs:1545-1602) und haelt so rund 20
Wrapper am Leben.

**2.2 `tiling_cost_delta` ist tot und dupliziert eine lebende Formel.**
envelope.rs:1379-1381 hat keinen Aufrufer; dieselbe Rechnung
`HULL_TOTAL_COST * (H(nachher) - H(vorher))` steht ausgeschrieben in
tiling_solver.rs:1636-1645.

**2.3 Ausdruecklich unverdrahtet (`#[allow(dead_code)]`)**, alle mit
Verwurf-Messung im Kommentar: `overpresence_preference`
(column_build.rs:789-825, 2/20 statt 15-16/20 Netz-Siege), `active_criterion`
(plate_builder.rs:171-181), `cells_corner` (:744-754), `best_plate_value`
(:605-624, dazu 42 Zeilen Doku ohne Verbraucher), `dome_draft_preference_k6`
(:1160-1200, par.19 falsches Vorzeichen), `set_target_column_seed` /
`column_from_seed` (provocation.rs:124-141, Stufe 2 nie gebaut).

**2.4 Knoepfe, die Verzweigungen offen halten** (alle laut `docs/knobs.md`
ENTSCHIEDEN bzw. Diagnose, Default aus):

| Knopf | Verzweigung |
| --- | --- |
| `MOSAIC_SPALTENBAU` | column_build.rs:107-115, gesamtes Modul |
| `MOSAIC_SPALTENBAU_SICHERHEITSNETZ` | column_build.rs:176-184, :633-651 |
| `MOSAIC_SPALTENBAU_JACKPOT` | column_build.rs:186-194, :888-894 |
| `MOSAIC_SPALTENBAU_SPECIAL` | column_build.rs:223-231, :360-371, :521-529, :749-751 |
| `MOSAIC_PLATTENBAU` | plate_builder.rs:81-126, neun Bauer-Typen |
| `MOSAIC_PROVOKATION_SPALTE` | provocation.rs:47-100, :180-216 |
| `MOSAIC_VORZUG_SPALTE` | provocation.rs:438-450, tiling_solver.rs:1438-1441 |
| `MOSAIC_OPPONENT_DISRUPTION` | provocation.rs:701-737, :891-917 |
| `TILING_SHAPING_ENABLED` | tiling_solver.rs:94, :583-600 |
| `PLATE_SHAPING_ENABLED` | shaping.rs:142, :180-186 |

Zusammen halten sie rund 4.800 Zeilen (`column_build.rs` + `plate_builder.rs` +
`provocation.rs`) am Leben, von denen im Default-Betrieb nur sechs Funktionen
wirklich laufen: `cell_is_completable`, `cell_cost`, `cell_cost_smart`,
`column_cost`, `remaining_colors`, `achievable_column_fill`.

**2.5 Ueberholte Begruendung einer Dopplung.** `read_f64_env_local`
(tiling_solver.rs:1002-1013) begruendet sich damit, `net_mcts::read_f64_env`
sei "dort privat (`fn`, kein `pub`)". net_mcts.rs:216 ist `pub(crate) fn`, und
`envelope.rs` ruft sie an sechs Stellen direkt (envelope.rs:287, 466, 536, 738,
941, 949).

**2.6 Merkmale ohne Konsument.** Die elf Werte aus Abschnitt 15
(features.rs:670-673, Indizes 744-754) sieht der amtierende Champion
`v27-b01_brierbest` nicht: er deklariert 744 (features.rs:1494-1496),
`net::split_planes_flat_batch_src` kuerzt. Gewollt (Arm v28-b02), aber der
einzige Block im Vektor, der aktuell nirgends gelesen wird.

---

## 3. Optimierungspotenzial (am Code belegt)

**3.1 `top_k_tilings`-Dedup ist quadratisch mit String-Vergleichen.**
tiling_solver.rs:781-793: `seen` ist ein `Vec<(Vec<bool>, Vec<String>)>` und
wird je Kandidat linear durchsucht. Bei `MAX_TILING_LEAVES = 400` (:625) sind
das bis zu 80.000 Vergleiche ueber je einen 36er-`Vec<bool>` plus eine
`Vec<String>`; `tiling_outcome_signature` (:646-671) baut die Strings je
Kandidat per `format!("{col:?}")` und sortiert sie. Verhaltensgleich billiger:
Fuellung als `u64`-Bitmaske (36 Bit), Chips als sortierter `Vec<(u8, u8)>`,
`seen` als `HashSet` -- die Signatur entscheidet nur Gleichheit. Aufrufer:
tiling_solver.rs:829, :1293, :1375, :1468, :1629, plate_builder.rs:661,
lib.rs:1741.

**3.2 Mehrfache `top_k_tilings`-Laeufe in EINER Entscheidung.**
`best_first_step_exact_or_valued_envelope` (tiling_solver.rs:1545-1613) ruft
nacheinander `column_build::preference_tiling_step` (:1560, ueber
plate_builder.rs:661 ein eigener Lauf), `preference_tiling_step` (:1563 ->
:1468), `best_first_step_plate_valued` (:1588 -> :1293) und
`best_first_step_envelope_valued` (:1597 -> :1629). Jeder Lauf startet mit
frischem `NODE_BUDGET = 2000` und `legal_steps(.., exact=true)`, also der
teuren Chip-Allokation an JEDEM Knoten (Modul-Doku :148-150: ausdruecklich nur
fuer den echten Zug gedacht). Im Default sind es ein Lauf, mit
`MOSAIC_SPALTENBAU=1` bis zu vier -- relevant genau fuer die Sonden, die
hinterher als "haengt" gemeldet werden.

**3.3 Geometriemasken im Planes-Bauer.** `state_to_planes_direct`
(features.rs:1308-1350) laeuft je Blatt eine 36x13-Maskenschleife fuer rein
zustandsUNabhaengige Geometrie; nur die sechs `gate(..)` haengen am Zustand,
und `gate` ist ein `Vec::contains` in der innersten Schleife (features.rs:1306).
Eine vorberechnete `static`-Maskentabelle plus sechs vorab gelesene Bools waere
ergebnisgleich.

**3.4 `slot_score_generic` sucht linear.** plate_builder.rs:470:
`zellen.contains(&(row, col))` je Slot-Position, in einer Schleife ueber
Kacheln x freie Slots x 4 Rotationen; beim Huellen-Bauer hat `zellen` 21
Eintraege, und `HullBuilder::cells` baut Kandidatenlisten UND `target_map` bei
jedem der drei Vorzuege neu (plate_builder.rs:780-822). Nur bei
`MOSAIC_PLATTENBAU=8` aktiv.

**Nicht optimierbar, festgehalten damit es nicht erneut gesucht wird:** der
teure Posten in `state_to_features_direct` ist `solve_round_final_score`
(features.rs:859), zweimal je Blatt, einmal je Spieler -- notwendig, und der
Cache (tiling_solver.rs:404-427) traegt es.

---

## 4. Struktur und Nachvollziehbarkeit

### 4.1 Deutsche Bezeichner gegen die CLAUDE.md-Regel (seit 2026-08-24)

Funktionsnamen sind fast durchgaengig migriert; im Produktivcode bleiben vier:
`plate_builder::*::zellen` (die Methode aller sieben Bauer),
`shaping::tiling_potenzial` (shaping.rs:534), `tiling_solver::belegtes_raster`
(:1239), `tiling_solver::fork_feld_punkte` (Testteil).

Bei TYPEN, Konstanten und Statics ist der Rueckstand gross (gezaehlt:
Deklarationen mit `struct`/`enum`/`trait`/`type`/`const`/`static`):

| Datei | deutsch / gesamt | Beispiele |
| --- | --- | --- |
| `plate_builder.rs` | 25 / 28 | `Plattenbauer`, `Modus`, `Zielkarte`, `EINHEITSKARTE`, `ZIEL_TOLERANZ`, `Zeilenbauer`, `SpaltenbauerGenerisch`, `Diagonalenbauer`, `Mehrfarbigbauer`, `Randbauer`, `Eckenbauer`, `Spezialbauer`, `Farbenreichbauer` |
| `column_build.rs` | 9 / 15 | `AKTIV_OVERRIDE`, `SICHERHEITSNETZ_OVERRIDE`, `ENGPASS_MAX`, `SPALTEN_TOLERANZ`, `PARTIE_SEED`, `LETZTER_WECHSEL`, `LETZTER_JACKPOT`, `JACKPOT_WERT` |
| `provocation.rs` | 3 / 7 | `Modus`, `MODUS_OVERRIDE`, `AUTO_SPALTE` |
| `tiling_solver.rs` | 3 / 32 | `PLATTEN_WEIGHT_OVERRIDE`, `PLATTEN_FORK_POINTS_MOVE`, `PLATTEN_FORK_PLATTE_MOVE` |
| `envelope.rs`, `features.rs`, `shaping.rs` | 0 | -- |

Lokale Variablen und Parameter (Treffer gegen eine feste deutsche Wortliste,
`//`-Zeilen abgezogen): `column_build.rs` 182, `plate_builder.rs` 118,
`provocation.rs` 70, `tiling_solver.rs` 23, `features.rs` 14, `envelope.rs` 1,
`shaping.rs` ~0. Haeufigste: `zellen` (48), `spalte` (32), `verbleibend` (36),
`kandidat(en)`, `kosten`, `ergebnis`.

### 4.2 Widerspruechliche Doc-Kommentare

| Stelle | Doku sagt | Code sagt |
| --- | --- | --- |
| tiling_solver.rs:100-103 | `ROUND5_ENDSCORING_ENABLED` "Standard AUS bis gemessen ist" | `= true` (:103) |
| tiling_solver.rs:844-858 | `NET_TILING_TIEBREAK_ENABLED` "STAND: AUS bis per Arena bestaetigt" | `= true` (:858) |
| tiling_solver.rs:992-1001 | `read_f64_env` sei in net_mcts privat | net_mcts.rs:216 `pub(crate)` |
| envelope.rs:917-934, :1007-1010 | Jokerfeld-Regel gilt fuer jede gelegte Platte | nur `SpaceType::Wild` (:1029-1033) |
| provocation.rs:459-464 | Auswahlordnung "1. minimaler Ueberlauf auf die Strafleiste" | :524-527 "KEIN Ueberlauf-Kriterium"; die erste Tupelstelle ist die Konstante `0usize` (:540) |
| shaping.rs:458-487 | Doc-Block beginnt bei `MOSAIC_WERTUNG_ROUND_GAIN`, endet an `scoring_floor_weight` | zwei Bloecke verschmolzen; `scoring_round_gain` (:538) hat gar keine Doku |
| plate_builder.rs:994-996 / :1039-1041 | "ALLE noch offenen Wild-Zellen" / "alle noch offenen Zellen am Rand" | :1006-1009 und :1048 pruefen `is_filled` nicht |

Die beiden letzten sind folgenlos (die Konsumenten filtern selbst), stehen aber
im selben Satz wie die Auswahlregel.

### 4.3 Doku-Verweise auf umbenannte Namen (Rest der Migration)

Neun Stellen zeigen ins Leere: column_build.rs:459
(`ziel_spalte_fuer_player`), :655 (`provocation::spalte_aus_seed`), :734
(`tiling_vorzug_fuer_zellen`), :804, :1515, :1716 (`ist_spalte_vollendbar`),
provocation.rs:490 (`verbleibende_farben`), :650 (`ist_spalte_vollendbar`),
shaping.rs:585, :741, :743 (`apply_wertung_shaping_with`,
`wertung_shaping_alpha()` -- beide existieren nicht mehr, :741 ist ein
rustdoc-Intra-Doc-Link). Dazu plate_builder.rs:20: verweist auf
`plattenbauer_regression_test.rs`, die es nicht gibt (`engine/tests/` enthaelt
nur `fixtures/`); die Aequivalenztests liegen im Modul selbst.

### 4.4 Dateigroesse und Nahtbreite

- **`envelope.rs` (2227):** natuerliche Naht zwischen H-Berechnung (1-900, reine
  Geometrie auf `PlayerBoard`) und Knopf-/Modus-Verteilung (900-1424,
  `CellKnobs`, `envelope_score_mode_with_cells`, `mode_scores`,
  `search_shift_state`). Ueber die Naht liefen rund 12 Namen (`occupancy`,
  `row_cost`, `hull_total_cost`, `contains_in`, `best_hull_frac_in`,
  `envelope_score_frac*`, `projected_occupancy*`, `cell_is_completable`).
  Billig, aber die Datei ist Gegenstand eines offenen Arms (K3-D/Jokerfeld,
  eingetaktet 2026-09-11).
- **`tiling_solver.rs` (3147, davon 1447 Tests):** drei Anliegen -- Loeser und
  Cache (1-568), Kandidaten und Auswahl (570-1352), Vorzugs-/Envelope-
  Verdrahtung (1354-1698). Nahtbreite Teil 1 zu Teil 2: fuenf Namen
  (`legal_steps`, `apply_step`, `MAX_DEPTH`, `NODE_BUDGET`, `TilingStep`).
- **`column_build.rs` + `plate_builder.rs` (3511):** der Schnitt mit dem
  groessten Gegenwert -- die sechs im Default lebenden Funktionen (2.4) in ein
  knopffreies Modul ziehen, den Rest als Diagnose kennzeichnen. Nahtbreite acht
  `pub(crate)`-Namen: `cell_cost`, `cell_cost_smart`, `cell_is_completable`,
  `column_is_completable`, `column_cost`, `scarcity_surcharge`,
  `slot_neighbours`, `achievable_column_fill`.

### 4.5 Tests

Nichts Grobes. Zwei Anmerkungen:
`envelope.rs::cell_knobs_are_bit_identical_at_weight_zero` (:2054-2115) ruft
`slot_weight()`/`reach_weight()`, also die Env-Getter -- die
Bitidentitaets-Aussage bleibt gueltig, der Test prueft unter gesetzten
Env-Knoepfen aber etwas anderes, als sein Name nahelegt.
`features.rs::plate_type_sight_is_appended_after_old_vector` (:1620-1641) prueft
mehr als der Name sagt (auch den 744er-Block), korrekt, nur breiter.

Positiv: `features.rs::dome_pool_knowledge_matches_stack_from_both_views`
(:1650-1700) prueft gegen eine DRITTE, im Test selbst ausgerechnete Zaehlung
statt gegen einen der beiden Bauer -- genau die Bauform, die Regel 0 verlangt.

---

## 5. Prioritaeten vor Projektende

**Zu tun:**

| # | Punkt | Stelle | Aufwand | Risiko |
| --- | --- | --- | --- | --- |
| 1 | Phantome in `remaining_colors`/`still_reachable_colors` abziehen, wie `self_play.rs:6115` | provocation.rs:611-616, :679-683 | 0,5 h Fix + 1 h Test | **hoch**: aendert Kanal 76, `col_f_max` und jede Bauer-Entscheidung; Feature-Golden-Hash und Anker-Invarianz werden ROT. Nutzer-Entscheid noetig, ob vor oder nach dem Generationswechsel |
| 2 | Drei Doku-Stellen mit falschem Schaltzustand richtigstellen | tiling_solver.rs:100-103, :844-858, :992-1001 | 0,5 h | keins |
| 3 | Jokerfeld-Doku auf den Code ziehen (nur `SpaceType::Wild`) | envelope.rs:917-934, :1007-1010 | 0,25 h | keins |
| 4 | Mondstapel: alle Stapel kodieren, oder das Weglassen begruenden und in `PREREG_stack_top_feature.md` eintragen | features.rs:501-513, :974-984 | 0,5 h Notiz / 2-3 h Merkmal | mittel: neues Merkmal heisst neue `INPUT_SIZE` und neue Fixture |
| 5 | Sichtfrage Mondstapel-Tiefe an den Nutzer, Ergebnis in `docs/architecture_reference.md` | serialize.rs:184-186 | 0,25 h | keins |
| 6 | K3-P2-Orientierungsfrage klaeren (feste gegen neu gewaehlte Huelle), Ergebnis an envelope.rs:690-695 festhalten | envelope.rs:701-708, :1113-1127, :1165-1177 | 0,5 h + 0,5 h | mittel: offener Arm, nicht der Champion (Default `MOSAIC_ENVELOPE_PROJECTED=0`) |
| 7 | Neun tote Doku-Verweise nachziehen, plus `plattenbauer_regression_test.rs` | siehe 4.3 | 0,5 h | keins |
| 8 | Merged Doc-Block in `shaping.rs` trennen, `scoring_round_gain` eigene Doku geben | shaping.rs:458-487, :538-541 | 0,25 h | keins |

Summe rund 4 h ohne Punkt 1 und 4, rund 9 h mit ihnen.

**Kann bleiben:**

- Deutsche Typ- und Variablennamen in `plate_builder.rs`, `column_build.rs`,
  `provocation.rs` (4.1). Die Regel verlangt Umbenennung bei BERUEHRUNG; diese
  Module werden vor Projektende voraussichtlich nicht mehr angefasst, und rund
  370 Stellen umzubenennen ist Bewegungsrisiko ohne Gegenwert.
- Die 37 aufruferlosen `envelope.rs`-Wrapper (2.1) und `tiling_cost_delta`
  (2.2): Preis der Bitidentitaets-Tests, Schnitt in eine Datei mit offenem Arm.
- Die sechs `#[allow(dead_code)]`-Funktionen (2.3): jede traegt ihre
  Verwurf-Messung im Kommentar, geloescht waere die Messung weg.
- Die zehn Knoepfe aus 2.4: gehoert in den Generationswechsel
  (`/mosaic-generation-turnover`), je Knopf mit Nutzer-Entscheid.
- Die Optimierungen 3.1 bis 3.4: keine liegt im Default-Hot-Path, und jede
  aendert Code, dessen Bitidentitaet gerade die Anker-Invarianz traegt. 3.1
  waere der einzige Kandidat, falls noch einmal eine Sonde mit
  `MOSAIC_SPALTENBAU=1` laufen soll.
- 1.7 und 1.8: nach Lage des Codes nicht erreichbar; 1.7 waere ein Einzeiler,
  falls jemand die Datei ohnehin anfasst.
