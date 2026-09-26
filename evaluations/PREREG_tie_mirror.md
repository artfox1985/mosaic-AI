<!-- STATUS: OFFEN | Frage: Kippt der Spiegelknopf (MOSAIC_TIE_MIRROR_P, je Partie eine Muenze) die Gleichstandsregeln von Huellenwahl und Tiling-Zelle in der Erzeugung zu 50:50, und verschiebt das die vollen Spalten nach rechts, ohne Staerke zu kosten? | Beleg: gebaut 2026-09-26, NICHT kompiliert, nicht gemessen (par.2); Abnahme vorab in par.3, Ergebnisse leer (par.4). -->

# Vorregistrierung: Spiegelknopf fuer die Gleichstandsregeln der Erzeugung

**Angelegt 2026-09-26.** Nutzer-Entscheid: *"Ja bau den spiegelknopf ein. Sollte dann 50:50
Aufteilung sein im self play"*. Der Aufbau ueber die linken Spalten sei nicht falsch, aber die
Spielvarianz ueber die rechten Spalten (c4/c5) gehe verloren.

## par.1 Anlass

**Befund (Koordinator, 2026-09-26):** Self-Play und Arena bauen volle Spalten nur links.
**Quelle:** Ad-hoc-Rechnung des Koordinators, Skript jetzt als
`tools/probes/column_by_index_probe.py` im Baum (100 zufaellige Dateien `selfplay_v32-b01-policy_*`,
Seed 20260926, letzte Records mit `winner`, `score_geo.col_fill[c] >= 6`; Arena aus
`gating_v33-b01_vs_v32-b01_s2026160{0,1}.json` ueber `arena_column_probe._end_state_from_artifact`).
Die Summen treffen die unabhaengig gemessenen Werte (Tor 2a 0,966 auf allen 400 Dateien gegen
0,950 hier; Tor 2b 1,024 / 1,060 exakt). **Ein JSON-Artefakt fehlt noch**; der Lauf wird exklusiv
wiederholt (die erste Rechnung lief neben dem b02-A/B, STATUS). Die Zahlen sind reine
Korpus-Lesungen und von der Nebenlast nicht betroffen.

| Spalte | Sockel v33 (n = 2.000 Seiten) | Arena v33-b01 (n = 800) | Arena v32-b01 (n = 800) |
| --- | --- | --- | --- |
| c0 voll / Fuellung | 0,473 / 5,19 | 0,573 / 5,31 | 0,585 / 5,36 |
| c1 | 0,475 / 5,23 | 0,449 / 5,19 | 0,468 / 5,19 |
| c2 | 0,001 / 2,82 | 0,003 / 3,09 | 0,007 / 3,18 |
| c3 | 0 / 2,24 | 0 / 2,11 | 0 / 2,15 |
| c4 | 0 / 1,32 | 0 / 1,54 | 0 / 1,43 |
| c5 | 0,001 / 0,94 | 0 / 0,85 | 0 / 0,76 |

- **Die Startplatte ist NICHT die Ursache** (150 Dateien, Start per Suche zu 90,5 Prozent in
  Slot-Spalte 0; bei randomisiertem Start in Slot-Spalte 2, n = 83 Seiten, trotzdem c0 0,34 /
  c1 0,43 / c5 0,01 voll).

**Ursache laut Code (gelesen 2026-09-26):** das Brett wird bis auf Gleichstandsregeln
links-rechts-symmetrisch bewertet (`envelope.rs` `Hull::contains`: LINKS `r + c <= 5`, RECHTS
`r <= c`, Spiegelbilder an der senkrechten Achse), aber zwei Gleichstandsregeln entscheiden
deterministisch fuer LINKS:

1. **Huellenwahl** (`envelope.rs`, vor dem Bau `best_hull_in`, `best_hull_frac_in` und die
   Modus-1-Wahl in `envelope_score_row6_in`): bei gleicher Abweichung `Hull::Left` (`<=`).
2. **Tiling-Zelle** (`round_end.rs::generate_tiling_actions` zaehlt die Slots `sc in 0..3`
   aufsteigend; jeder Waehler in `tiling_solver.rs` uebernimmt nur bei strikt besserem Wert bzw.
   nimmt beim Gleichstand den ersten Kandidaten): die linke Zelle gewinnt.

Praezisierung des Koordinators nach Nutzer-Hinweis (*"Wenn die Kuppelplatten entsprechend
liegen, bleibt dem Tiling nichts anderes uebrig"*): der tragende Hebel ist Regel 1 in der SUCHE,
Regel 2 ist zweitrangig.

## par.2 Bau

**Stand: GEBAUT 2026-09-26, NICHT kompiliert und NICHT getestet** (exklusive Messung auf der
Maschine; der Bau laeuft beim Koordinator). Alle Pruefstellen unten sind Stand dieses Baus.

**Knopf.** `MOSAIC_TIE_MIRROR_P` (float, Default 0.0 = aus), Getter `tie_mirror.rs::tie_mirror_p`
(OnceLock, ausserhalb [0,1] Default mit einmaliger Warnung, Muster
`self_play.rs::start_slot_random_p`). Registriert in `engine/src/knob_registry.rs`
(Status Diagnose), im Lauf-Manifest ueber `lib.rs::engine_config_json` (`tie_mirror_p`).
**Kein Spec-Feld**: der Knopf ist ein reiner Erzeugungsknopf wie `MOSAIC_START_SLOT_RANDOM_P`
(dort ebenfalls "Kein Spec-Feld", `knob_registry.rs`), und die Muenze gehoert der PARTIE, nicht
einer Seite. Das `self_play.py`-Flag (`--tie-mirror-p`, setzt die Variable vor dem ersten Lesen)
steht noch aus: `self_play.py` war waehrend des Baus gesperrt (laufende Prozesse).

**Muenze.** EINE je Partie, `tie_mirror.rs::tie_mirror_coin(p, partie_seed)`:
`derive_search_seed(partie_seed ^ TIE_MIRROR_SEED_DISTINGUISHER, 0)` auf [0,1) abgebildet,
gespiegelt genau dann, wenn der Wert kleiner als p ist. Der Partie-RNG wird nicht verbraucht
(`PREREG_search_rng_split.md`), der Distinguisher ist verschieden von allen sieben im Baum
(gegrept 2026-09-26: sechs benannte `*_SEED_DISTINGUISHER` plus die lokale Konstante in
`self_play.rs::asym_preference_side`). Bei
p = 0 Fruehausstieg ohne Rechnung. Geworfen in `self_play.rs::run_net_self_play` (aeussere
`play`-Closure); der **Ausflug (Weg B) uebernimmt den Wert der Hauptpartie**.

**Schalter.** Thread-lokal (`tie_mirror.rs::set_game_tie_mirror` / `game_tie_mirror`), gesetzt
im Thread der Partie und im Thread des Ausflugs (beide frisch von `run_with_watchdog` gespawnt,
Muster `plate_builder::set_game_seed`). Kein anderer Pfad setzt ihn: Arena, Gating, Referee,
GUI (`py.rs`) und Heuristik-Self-Play bleiben Bestand.

**Was gespiegelt wird (nur in gespiegelten Partien):**

(a) **Huellen-Gleichstand, EINE Stelle:** `envelope.rs::pick_hull` (Gleichstand -> RECHTS statt
LINKS; ohne Gleichstand unveraendert die kleinere Abweichung). Alle Orientierungswahlen laufen
darueber: `best_hull_in`, `best_hull_frac_in` und damit `envelope_score_frac_in`,
`envelope_score_of_in`, die Modus-1-Wahl in `envelope_score_row6_in` und die par.12c-Zweige in
`envelope_score_mode_with_cells`/`ownership_score_with_cells`. Die Maximum-Schleifen
`for hull in [Left, Right]` (K3-R, K3-P2, K3-F) brauchen keinen Eingriff: bei gleichem Wert ist
das Maximum dasselbe.

*Mechanismus (Herleitung aus dem Code, NICHT gemessen):* auf einem exakt spiegelsymmetrischen
Brett geben beide Orientierungen denselben Wert H, dort ist die Regel folgenlos. Sie wirkt auf
Brettern mit GLEICHER Abweichung, deren Haelften verschieden kosten -- und, im Generator
wesentlich, ueber K5 (`special_row6_w` 1,0 in `models/v32_generation.spec.json`, Modus 1): die
Spezialfeld-Gutschrift der Zeile 6 (`apply_row6_special_in`) prueft nur die Huellenzelle der
GEWAEHLTEN Orientierung, (5,0) links bzw. (5,5) rechts. Solange die Abweichung gleich ist (fruehe
Bretter, Steine nur in Rasterzeile 0), bekommt nur eine Spezialplatte unten LINKS die Gutschrift,
und die Suche legt sie dorthin. Gespiegelt gilt dasselbe fuer unten rechts.

(b) **Tiling-Zelle:** `tiling_solver.rs::decision_steps` betrachtet die Platzierungen je
Musterreihe in gespiegelter Rasterspalte (`2 * slot_col + space_index % 2` absteigend,
`mirror_place_order`); Reihenfolge der Musterreihen und Chip-Schritte bleiben. Gelesen in
`best_first_step_inner` (samt `solve_rec_ordered`) und `top_k_tilings` (samt `collect_tilings`).
Damit kippen ALLE Gleichstandsbrueche dieses Wahlpfads ins Spiegelbild: Punkte-Argmax, Netz-
Stichentscheid bei gleichem Wert (`select_best_tiling_candidate`), Huellen-Zweig K3 (d)
(`best_first_step_envelope_valued`, `tied[0]`), Plattenzweig und Runde 5
(`best_first_step_round5`, `max_by_key` nimmt das LETZTE Maximum -- dort war der Bestand also
nicht "links", sondern die spaeteste Kandidatin; gespiegelt ist es deren Spiegelbild). Gespiegelt
heisst hier durchgehend: das exakte Spiegelbild der Bestandsregel, damit die beiden Haelften der
Erzeugung zusammen symmetrisch sind.

**Was ebenfalls mitgespiegelt wird, weil es im selben Thread dieselben Funktionen ruft:** der
Rundenuebergang der Suche (`round_transition.rs::resolve_to_pre_chance` ->
`best_first_step_exact`) und die Label-Rollouts (`round_transition_deep.rs`). Beides modelliert
das eigene Tiling der Partie und bleibt so mit dem echten Zug konsistent.

**Was bewusst NICHT gespiegelt wird:**

- Tiling-Projektion der Netz-Eingabe (`features.rs` -> `tiling_solver::project_max_tiling`,
  `project_rec` mit `>`): das Training rechnet die Eingabe ohne Schalter aus dem Record neu; ein
  gespiegelter Wert beim Spielen waere ein Eingabe-Versatz gegen das Training. Die Projektion
  sagt in gespiegelten Partien bei Gleichstand also weiter die linke Zelle voraus.
- Blatt-Hot-Path `solve_max_tiling_points*`, `solve_rec_endaware`: reine Werte; die Reihenfolge
  zaehlt nur, wenn das Knotenbudget reisst.
- Startsetzung per Handregel (`self_play.rs::choose_start_placement_with_slot`, striktes `>` in
  fester Reihenfolge, Gleichstand oben links): im Generator nicht aktiv (`start_by_search` 1),
  Anker-Code.
- Heuristik-Bauer (`plate_builder.rs`, `column_build.rs`): nur hinter `MOSAIC_PLATTENBAU` /
  `MOSAIC_SPALTENBAU`, Gleichstand dort per Seed-Streuung.

**Record-Feld.** `tie_mirrored: true/false` auf JEDEM Record der Partie (auch Ausflug),
gestempelt in `run_net_self_play` vor dem Fortschritts-Log (`tie_mirror.rs::stamp_tie_mirrored`),
**nur bei p > 0**. Bei p = 0 kein Feld, damit bleiben die Records und die Netz-Paritaets-Fixture
byte-gleich (dieselbe Regel wie `start_slot_randomized`, das nur bei gefallener Muenze
geschrieben wird).

**Tests (Rust, geschrieben, nicht gelaufen):** `tie_mirror.rs` (Muenze: nie bei 0, immer bei 1,
Anteil 0,48 bis 0,52 bei p = 0,5 ueber 10.000 Partie-Seeds, deterministisch, monoton in p;
Record-Feld nur bei p > 0; Waechter setzt zurueck), `envelope.rs::tie_mirror_flips_hull_tie_to_right`
(leeres Brett und Zeile-0-Brett, beide Huellenformen: aus LINKS, an RECHTS),
`tiling_solver.rs::tie_mirror_off_keeps_left_choice_on_tie` / `tie_mirror_on_picks_right_cell_on_tie`
(zwei punktegleiche Zellen, Rasterspalte 1 und 5, fuenf Waehler: aus 1, an 5, Wert unveraendert),
`mirror_place_order_reverses_columns_within_each_pattern_row`.

## par.3 Abnahme (VORAB festgelegt)

1. **Default aus ist byte-identisch** (Tor, vor jeder Erzeugung): Netz-Paritaets-Fixture
   (`engine/tests/fixtures/net_parity_champion.txt`), Golden-Records
   (`examples/golden_game_loop_capture.rs` bzw. die Golden-Tests), Anker-Drift
   (`/mosaic-anchor-invariance`, `hv4_anchor` Zug fuer Zug) -- alle GRUEN mit ungesetztem Knopf.
   Dazu die neuen Rust-Tests aus par.2.
2. **Muenze in der Erzeugung:** bei p = 0,5 liegt der Anteil gespiegelter Partien in der
   naechsten Erzeugung bei 50 +- 3 Prozent (Grundmenge: Hauptpartien des Sockels, Einheit
   "Anteil Partien mit `tie_mirrored: true`"; Ausfluege zaehlen NICHT gesondert, sie erben den
   Wert). Ausserhalb des Fensters ist der Bau falsch, nicht der Zufall (bei n = 2.000 Partien ist
   ein Standardfehler rund 1,1 Prozentpunkte).
3. **Leseregel Spaltenseite (BERICHTET, KEIN TOR):** Anteil voller Spalten RECHTS (c4 + c5) an
   allen vollen Spalten im Sockel der naechsten Generation, per `tools/corpus_sanity_check.py`,
   Feld `sp_voll_je_spalte` (neu seit 2026-09-26), getrennt nach `tie_mirrored` true/false.
   **Ausdruecklich:** 50:50 bei der Gleichstandsrichtung garantiert NICHT 50:50 bei den Spalten.
   Das Netz hat seine Linksvorliebe gelernt (Policy und Value), und die Tiling-Projektion der
   Eingabe bleibt links (par.2); die Verschiebung kann klein sein und erst ueber Generationen
   wachsen. Erwartet ist nur die Richtung: gespiegelte Partien bauen mehr rechts als
   ungespiegelte.
4. **Staerke soll unberuehrt bleiben:** Tor 1 der naechsten Generation ist der Waechter. Faellt
   es, wird der Knopf als Ursache geprueft, bevor irgendetwas anderes am Rezept geaendert wird.

## par.4 Ergebnisse

(leer)
