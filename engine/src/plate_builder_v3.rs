//! Routing der Heuristik-Variante hv3: die Dreiecks-Huelle als Zielzellenkarte.
//!
//! ## Was hier steht
//!
//! Die zweite Haelfte von hv3. `heuristic_v3.rs` traegt die BEWERTUNG, dieses
//! Modul das ROUTING -- also welche Zellen angesteuert werden, im Drafting
//! (Steinzug und Kuppelplatten-Wahl) und im Tiling (Schritt- und Chip-Wahl).
//! Nach `PREREG_provocation.md` ist das die tragende Haelfte: "der Engpass ist
//! die PLATZIERBARKEIT, nicht die Plattenbewertung".
//!
//! Wieder aufgenommen aus `engine/src/plate_builder.rs` (die hv2-Teile dort
//! wurden mit Commit 65b48af entfernt, "B4a: v2 verlaesst den Quellstand").
//! Portiert ist GENAU der Zweig `HeuristikVariante::V2Huelle` = hv2, mit
//! englischen Bezeichnern. NICHT portiert, weil hv2 sie nie gefahren hat: die
//! Punkte-Heatmaps (`points_heatmap`, `expected_points_map`), der Phasenfaktor
//! (`SPALTEN_PHASE`, `MOSAIC_PHASE_*`), der Vollendbarkeits-Filter aus par.12
//! und die Erreichbarkeits-Skalierung aus par.15.
//!
//! **Auch nicht portiert: der `v2_target_cells`-Rueckfall.** Er stand im alten
//! `v2_drafting_preference`/`v2_tiling_preference` hinter `v2_map_for(...)`,
//! war fuer hv2 aber unerreichbar: `v2_map_for` liefert fuer V2Huelle
//! `v2_envelope_target(...)?`, und das kann nur `None` werden, wenn
//! `envelope_orientation_by_cost` -> `target_index_generic` `None` liefert --
//! was genau bei LEERER Kandidatenliste passiert (plate_builder.rs:342-344),
//! waehrend hier immer zwei Kandidaten uebergeben werden. Toter Zweig, deshalb
//! weggelassen statt mitgeschleppt.
//!
//! ## Der Unterschied zu hv2: der Phantom-Abzug A2
//!
//! A2 (`provocation.rs::subtract_phantom_tiles`, Commit 2a0cf4b,
//! `PREREG_code_cleanup_closeout.md` par.3 Punkt 2) zieht die per Bonuschip
//! eingebuchten PHANTOM-Fliesen wieder aus dem Verbrauch ab -- sie sind nie
//! aus Beutel oder Turm gezogen worden, und wer sie mitzaehlt, haelt den
//! Restvorrat der Farbe zu NIEDRIG. Das Artefakt
//! `models/frozen_heuristics/hv2_generator` faehrt ein Wheel vom 2026-08-26
//! und kennt den Abzug nicht; hv3 ist dasselbe Rezept MIT ihm.
//!
//! Der Abzug wirkt an genau zwei Stellen dieses Routings, beide ueber
//! `provocation::remaining_colors`:
//!
//! 1. **Orientierungswahl der Huelle** -- [`hull_orientation_by_cost`] ->
//!    `plate_builder::target_index_generic` (plate_builder.rs:346, Lesestelle
//!    plate_builder.rs:351) -> `cells_cost` ->
//!    `column_build::cell_cost`. Die beiden Randspalten werden
//!    nach Restversorgung verglichen; ein zu niedrig gehaltener Restvorrat
//!    verschiebt diesen Vergleich.
//! 2. **Knappheits-Tie-Break im Drafting** -- [`hull_drafting_preference`],
//!    Sortierschluessel `scarcity`.
//!
//! Die BEWERTUNG (`heuristic_v3.rs`) liest den Restvorrat nicht; dort wirkt A2
//! nicht. Der alte `row_completion_progress_capped` haette ihn gelesen, gehoert
//! aber zu V2HuelleCap (par.16) und damit nicht zu hv2.

use crate::board::PlayerBoard;
use crate::dome::{DomeSpace, SpaceType};
use crate::moves::Action;
use crate::state::GameState;
use crate::tiling_solver::TilingStep;

/// Gewicht je RASTERZELLE. `0.0` heisst "nicht im Ziel". Strukturgleich zu
/// `plate_builder::Zielkarte`, damit die dortigen gewichteten Vorzugs-
/// Funktionen direkt damit gefuettert werden koennen.
type TargetMap = [[f64; 6]; 6];

// ── Die Prio-Leiter (Nutzer-Vorgabe 2026-08-24) ─────────────────────────────

/// **HANDGESETZT.** Gewicht je Prioritaetsstufe der Nutzer-Leiter
/// (2026-08-24, erweiterte Fassung), Index 0..4 fuer Prio 3..7:
///
/// 3. **Randspalte fuellen** (Rasterspalte 0 oder 5) -- hoechste Basiswertigkeit.
/// 4. **Zweite Spalte fuellen** (Rasterspalte 1 oder 4), mit Spezialfliese
///    oder Joker auf Rasterzeile 5 (siehe [`hull_cell_value`]).
/// 5. **Wertungsplatten und Ziele sichern**: Spezialfelder freischalten und
///    Joker-Zellen halten. Steht VOR den kurzen Musterreihen, weil beides im
///    Lategame skaliert -- ein leeres Spezialfeld kostet `-3` (`scoring.rs`,
///    Zweig 6) und die Freischaltung bringt zusaetzlich eine Gratis-Zelle plus
///    Punkte in Hoehe der Rasterreihe.
/// 6. **Rasterzeile 0 und 1 fuellen**, soweit es geht.
/// 7. **Nachbarn mitnehmen** aus Rasterzeile 2 und 3 -- reiner Tie-Break.
///
/// Prio 0 (Endspiel), 1 (Strafleiste) und 2 (Gegner-Stoerung) stehen bewusst
/// NICHT in dieser Karte. Sie sind keine Routing-Ziele, sondern Sache der
/// SUCHE, und dort schon entschieden: Runde 5 laeuft als exaktes Endspiel
/// (`round5::applies`, `mcts.rs`), die Strafleiste steckt als
/// `round_end::projected_unplaceable_penalty` in `mcts::player_total`. Sie hier
/// zu duplizieren hiesse, dieselbe Groesse zweimal zu zaehlen.
///
/// Die Zahlen sind eine SETZUNG, keine Ableitung -- dieselbe Regel wie bei
/// `heuristic_v3::ROW_CREDIT`. Gefordert ist nur die strenge Rangfolge.
const PRIORITY_WEIGHT: [f64; 5] = [5.0, 4.0, 3.0, 2.0, 1.0];

/// Prio 7 bei AKTIVER Diagonalen-Wertungsplatte (`scoring.rs`, Zweig 2).
///
/// Nutzer-Vorgabe 2026-08-24: "bei Verwendung der Diagonale wird Prio 7
/// aufgeweicht". Die Nachbarschafts-Mitnahme ist ohnehin nur Tie-Break; wenn
/// eine Diagonale anliegt, sollen die Zuege dorthin nicht von ihr ueberstimmt
/// werden.
const PRIORITY7_SOFTENED: f64 = 0.5;

/// Wertungsplatten-Id der DIAGONALEN (`scoring.rs`, Zweig 2).
const K2_DIAGONALS: usize = 2;

/// Zielkarte je Orientierung: `0` = Randspalte LINKS (Rasterspalte 0, zweite
/// Spalte 1), `1` = Randspalte RECHTS (5 bzw. 4).
///
/// **Warum genau zwei Orientierungen** (Nutzer-Korrektur 2026-08-24): die
/// volle Rasterzeile liegt immer oben. Eine Spiegelung um die Reihen-Achse
/// verlangte eine volle Rasterzeile 5, gespeist ausschliesslich von Musterreihe
/// 6 (0,74-1,31 Abschluesse je Partie) -- strukturell unerreichbar.
///
/// **Rasterzeile 4 und 5 ausserhalb der beiden Spalten bekommen im Grundbild
/// 0.** Dort kostet jede Zelle einen Abschluss von Musterreihe 5 bzw. 6, und
/// die sind in Prio 3/4 besser angelegt. Die Prio-5-Auflage kann sie wieder
/// anheben -- aber nur fuer Zellen, die ein Spezialfeld freischalten, weil
/// deren Ertrag nicht an einem weiteren Abschluss haengt.
fn priority_map(player: &PlayerBoard, tile_ids: &[usize], orientation: usize) -> TargetMap {
    let first_column = if orientation == 0 { 0 } else { 5 };
    let second_column = if orientation == 0 { 1 } else { 4 };
    let neighbour = if tile_ids.contains(&K2_DIAGONALS) {
        PRIORITY7_SOFTENED
    } else {
        PRIORITY_WEIGHT[4]
    };
    let mut k = [[0.0f64; 6]; 6];
    for r in 0..6 {
        for c in 0..6 {
            k[r][c] = if c == first_column {
                PRIORITY_WEIGHT[0]
            } else if c == second_column {
                PRIORITY_WEIGHT[1]
            } else if r <= 1 {
                PRIORITY_WEIGHT[3]
            } else if r <= 3 {
                neighbour
            } else {
                0.0
            };
        }
    }
    priority5_overlay(player, &mut k);
    k
}

/// Prio 5 als AUFLAGE auf das Grundbild: hebt Zellen auf `PRIORITY_WEIGHT[2]`,
/// senkt aber nie eine hoehere Stufe.
///
/// Zwei Sorten, beide aus der Nutzer-Vorgabe ("Spezialfliesen und
/// Jokerplatten"; die uebrigen Wertungsplatten sind durch Prio 3/4/6 bereits
/// gedeckt):
///
/// 1. **Freischalt-Zellen**: die noch leeren REGULAEREN Zellen einer Platte,
///    deren Spezialfeld noch gesperrt ist. Sind alle drei belegt, wird das
///    Spezialfeld automatisch belegt und abgerechnet
///    (`round_end::check_special_trigger`). Diese Zellen duerfen auch aus dem
///    Nichts angehoben werden -- der Ertrag haengt nicht an einem weiteren
///    Musterreihen-Abschluss.
/// 2. **Joker-Zellen** (Wild): nur, wo die Karte ohnehin schon > 0 ist. Ein
///    Joker nimmt die Farbbindung, aber die Zelle kostet weiterhin einen
///    Abschluss ihrer Musterreihe -- das rechtfertigt keinen Eintritt in
///    Rasterzeile 4/5 ausserhalb der beiden Spalten.
fn priority5_overlay(player: &PlayerBoard, k: &mut TargetMap) {
    let level = PRIORITY_WEIGHT[2];
    for (tr, grid_row) in player.dome_grid.dome_slots.iter().enumerate() {
        for (tc, slot) in grid_row.iter().enumerate() {
            let Some(slot) = slot else { continue };
            let sp_idx = slot.special_space_idx();
            let special_locked = sp_idx.is_some_and(|i| slot.spaces[i].is_locked);
            for (si, sp) in slot.spaces.iter().enumerate() {
                if sp.is_filled() {
                    continue;
                }
                let (r, c) = (2 * tr + si / 2, 2 * tc + si % 2);
                let unlocks = special_locked && Some(si) != sp_idx;
                let joker = sp.space_type == SpaceType::Wild && k[r][c] > 0.0;
                if (unlocks || joker) && k[r][c] < level {
                    k[r][c] = level;
                }
            }
        }
    }
}

/// Gewichteter Fuellstand der Zielkarte -- das Mass fuer die
/// Orientierungs-Festnagelung ab Runde 3.
///
/// Der Fuellstand ist von sich aus stabil (eine fuehrende Seite behaelt ihren
/// Vorsprung), also braucht es keinen gespeicherten Zustand und es entsteht
/// kein Leck ueber Partiegrenzen.
fn map_fill(player: &PlayerBoard, k: &TargetMap) -> f64 {
    let mut total = 0.0;
    for r in 0..6 {
        for c in 0..6 {
            if k[r][c] > 0.0 && player.dome_grid.get_space(r, c).is_some_and(|sp| sp.is_filled()) {
                total += k[r][c];
            }
        }
    }
    total
}

/// Orientierung der Zielhuelle nach der KOSTENFORMEL.
///
/// Verglichen werden die beiden RANDSPALTEN 0 und 5 -- Prio 3 der Leiter und
/// damit die Spalte, an der die ganze Huelle haengt. Bewusst NICHT die 28
/// Zellen der ganzen Karte: die sind zu grossen Teilen dieselben und
/// unterscheiden die beiden Seiten kaum noch.
///
/// **A2-Wirkstelle 1** (siehe Moduldoku): `target_index_generic` liest
/// `provocation::remaining_colors` (plate_builder.rs:346) und damit seit
/// Commit 2a0cf4b den Phantom-Abzug.
fn hull_orientation_by_cost(state: &GameState, pi: usize) -> Option<usize> {
    let candidates = vec![crate::plate_builder::cells_column(0), crate::plate_builder::cells_column(5)];
    crate::plate_builder::target_index_generic(state, pi, &candidates)
}

/// Zielkarte fuer hv3: die Prio-Leiter in einer der beiden Orientierungen.
///
/// **Die Festnagelung ab Runde 3** war der Bauschritt, der die Partien mit
/// mindestens einer vollen Spalte von 35 auf 50 Prozent gehoben hat. Gleichstand
/// faellt an die Kostenformel; in Runde 1-2 entscheidet sie ohnehin allein.
fn hull_target_map(state: &GameState, pi: usize) -> Option<TargetMap> {
    let player = &state.players[pi];
    let ids = &state.scoring_tile_ids;
    let orientation = if state.round_number >= 3 {
        let f0 = map_fill(player, &priority_map(player, ids, 0));
        let f1 = map_fill(player, &priority_map(player, ids, 1));
        if f0 > f1 {
            0
        } else if f1 > f0 {
            1
        } else {
            hull_orientation_by_cost(state, pi)?
        }
    } else {
        hull_orientation_by_cost(state, pi)?
    };
    Some(priority_map(player, ids, orientation))
}

/// Alle Zellen mit Gewicht > 0, in Rasterreihenfolge.
fn cells_from_map(k: &TargetMap) -> Vec<(usize, usize)> {
    let mut v = Vec::with_capacity(28);
    for r in 0..6 {
        for c in 0..6 {
            if k[r][c] > 0.0 {
                v.push((r, c));
            }
        }
    }
    v
}

/// Zellenwert fuer die Kuppelplatten-Wahl von hv3.
///
/// Einziger Unterschied zum Bestand (`column_build::cell_value`): auf
/// RASTERZEILE 5 schlagen Spezialfeld und Wild jede Normalfarbe
/// (Nutzer-Vorgabe 2026-08-24: "mit Spezialfliese auf Reihe 6. Alternativ ...
/// jokerplatten verwenden").
///
/// Der Grund ist mechanisch und geprueft, nicht aesthetisch: Rasterzeile 5 wird
/// ausschliesslich von Musterreihe 6 gespeist, dem seltensten Abschluss im
/// Spiel. Ein SPEZIALFELD dort kostet gar keinen -- es wird automatisch belegt,
/// sobald die drei anderen Zellen seiner Platte liegen
/// (`round_end::check_special_trigger`). Ein WILD kostet einen Abschluss, nimmt
/// ihm aber die Farbbindung. Der Bestandswert kehrt die Rangfolge um (Wild 3,0
/// ueber Special 2,0), weil er fuer Zellen OHNE diese Knappheit geschrieben ist.
///
/// Werte sind eine SETZUNG. Gefordert ist nur: Special > Wild > jede
/// Normalfarbe, und Normalfarbe hoechstens `JACKPOT_WERT` (4,0).
fn hull_cell_value(player: &PlayerBoard, r: usize, _c: usize, space: &DomeSpace) -> f64 {
    if r == 5 {
        match space.space_type {
            SpaceType::Special => return 6.0,
            SpaceType::Wild => return 5.0,
            SpaceType::Normal => {}
        }
    }
    crate::column_build::cell_value(player, r, space)
}

// ── Prio 0/1/2: die Leiter oberhalb der Zielkarte ───────────────────────────

/// Phasen-Eskalation je Runde 1..4 (Nutzer-Vorgabe 2026-08-24: "Late Game
/// steigen die Gewichte fuer Prio 0, 1 und 2 exponentiell an").
///
/// Runde 5 kommt nicht vor: dort uebernimmt das exakte Endspiel
/// (`round5::applies`, kurzgeschlossen in `mcts.rs`), und dieses Routing laeuft
/// ohnehin nur bis Runde 4. Das IST Prio 0 der Leiter.
const ESCALATION: [f64; 4] = [1.0, 2.0, 4.0, 8.0];

/// Gewicht der Strafleisten-Punkte (Prio 1) im linearen Score.
///
/// **SETZUNG.** Kalibrierung, damit die Rangfolge nachvollziehbar bleibt: eine
/// einzelne Straffliese kostet in Runde 1 `0,5` und liegt damit unter jeder
/// Zielstufe ausser dem Nachbar-Tie-Break; in Runde 4 kostet sie `4,0` und
/// schlaegt alles ausser Prio 3 (`5,0`). Genau das beschreibt die Vorgabe:
/// frueh nachrangig, spaet dominant.
const W_FLOOR: f64 = 0.5;

/// Gewicht der Stoerwirkung (Prio 2) im linearen Score.
///
/// **SETZUNG, bewusst am unteren Rand.** `disruption_score` liefert hoechstens
/// so viele Einheiten, wie der Zug Fliesen nimmt (typisch 1-4, selten 6). Bei
/// `0,10` erreicht die Stoerung in Runde 4 hoechstens `0,1*8*6 = 4,8` und bleibt
/// damit knapp unter Prio 3 (`5,0`) -- sie kann den Spaltenbau zuspitzen, aber
/// nicht abraeumen.
///
/// Der Grund fuer die Vorsicht ist gemessen, nicht theoretisch:
/// `PREREG_long_row_payoff.md` B1 hat mit einem zu starken Zusatzanreiz 14,5
/// Prozentpunkte Siegquote gekostet.
const W_DISRUPTION: f64 = 0.10;

/// Schwelle der Schadensbegrenzung in PUNKTEN (Prio 1, Nutzer-Vorgabe
/// 2026-08-24: "Threshold z. B. ab -4 Punkten").
///
/// Ein Kandidat, der so viel oder mehr kostet, wird nicht mehr bevorzugt -- die
/// Entscheidung faellt dann an die Suche zurueck, die die Strafleiste ueber
/// `round_end::projected_unplaceable_penalty` exakt einpreist. Kein hartes
/// Verbot: das Routing ist eine Praeferenz, kein Filter auf der Zugmenge (die
/// Beschneidungs-Bauform ist in `PREREG_provocation.md` par.7/par.9 als
/// spielzerstoerend gemessen).
const FLOOR_THRESHOLD_POINTS: i32 = -4;

/// Punktekosten, die `extra` weitere Fliesen auf der Strafleiste ausloesen.
///
/// Marginal ab dem aktuellen Fuellstand, gedeckelt bei `MAX_BROKEN` -- exakt
/// dieselbe Rechnung wie `round_end::projected_unplaceable_penalty`
/// (`BROKEN_PENALTIES = [-1, -2, -3, -4]`, board.rs:228), damit Routing und
/// Bewertung nicht auseinanderlaufen.
fn floor_points(player: &PlayerBoard, extra: usize) -> i32 {
    let before = player.broken_tiles.len();
    let after = (before + extra).min(crate::board::MAX_BROKEN);
    (before..after).map(|i| crate::board::BROKEN_PENALTIES[i]).sum()
}

/// Bestes Zielgewicht, das ein Zug in Musterreihe `r` mit Farbe `color`
/// bedienen kann -- `0.0`, wenn er keine Zielzelle bedient.
///
/// MAX statt Summe: eine Musterreihe legt je Abschluss genau EINEN Stein,
/// mehrere bedienbare Zellen sind Alternativen und keine Addition (dieselbe
/// Begruendung, aus der `heuristic_v3` das Maximum nimmt).
fn best_target_weight(
    player: &PlayerBoard,
    k: &TargetMap,
    cells: &[(usize, usize)],
    r: usize,
    color: crate::tile::TileColor,
) -> f64 {
    let mut best = 0.0f64;
    for &(tr, tc) in cells {
        if tr != r {
            continue;
        }
        let Some(sp) = player.dome_grid.get_space(tr, tc) else { continue };
        if sp.is_filled() {
            continue;
        }
        let serves = match sp.space_type {
            SpaceType::Wild => true,
            SpaceType::Normal => sp.required_color == Some(color),
            SpaceType::Special => false,
        };
        if serves && k[tr][tc] > best {
            best = k[tr][tc];
        }
    }
    best
}

/// Drafting-Vorzug der Huelle: die ganze Prio-Leiter als LINEARER Score statt
/// als `if`-Kaskade (Nutzer-Vorgabe 2026-08-24, Implementierungs-Hinweis).
///
/// ```text
/// score = Zielgewicht                         (Prio 3-7, `priority_map`)
///       + W_DISRUPTION * Eskalation * Stoerung (Prio 2, `provocation::disruption_score`)
///       + W_FLOOR * Eskalation * Strafpunkte   (Prio 1, <= 0)
/// ```
///
/// Prio 0 steckt in der Abwesenheit: ab Runde 5 liefert diese Funktion nichts
/// und das exakte Endspiel uebernimmt.
///
/// **Nichts davon ist neu gerechnet.** Stoerwirkung und Strafleisten-Zuwachs
/// kommen aus `provocation.rs`, die Strafpunkte-Tabelle aus `board.rs`. Neu ist
/// allein, dass sie hier zusammen gewichtet werden.
///
/// **Bodenzuege bekommen nie einen Vorzug** -- gleiche Regel und gleicher Grund
/// wie in `provocation::preference_move_for_color`: Schadensbegrenzung steht
/// ueber Stoerung.
///
/// **A2-Wirkstelle 2** (siehe Moduldoku): `remaining` speist den
/// Knappheits-Schluessel `scarcity` und traegt seit Commit 2a0cf4b den
/// Phantom-Abzug.
fn hull_drafting_preference(
    state: &GameState,
    k: &TargetMap,
    cells: &[(usize, usize)],
) -> Option<Action> {
    if state.phase != crate::state::Phase::Drafting || state.round_number > 4 {
        return None;
    }
    let pi = state.current_player;
    let player = &state.players[pi];
    let remaining = crate::provocation::remaining_colors(state);
    let demand_acute = crate::provocation::opponent_demand_acute(state, pi);
    let escalation = ESCALATION[(state.round_number as usize).clamp(1, 4) - 1];

    let mut best: Option<(f64, i64, i32, i32, crate::moves::Move)> = None;
    for m in crate::validation::generate_valid_moves(state) {
        let r = m.place.row_index;
        if !(0..=5).contains(&r) {
            continue; // Bodenzug
        }
        let r = r as usize;

        // Prio 1: Schadensbegrenzung. Ueber der Schwelle gar nicht erst
        // bevorzugen -- die Suche preist die Strafleiste exakt ein.
        let floor = floor_points(player, crate::provocation::floor_line_growth(state, pi, &m));
        if floor <= FLOOR_THRESHOLD_POINTS {
            continue;
        }
        // Prio 2: verhinderte Gegner-Fliesen zaehlen wie eigener Gewinn.
        let (disruption, _) = crate::provocation::disruption_score(state, &m, &demand_acute);
        // Prio 3-7: die Zielkarte.
        let target = best_target_weight(player, k, cells, r, m.take.color);
        if target == 0.0 && disruption == 0 {
            continue; // weder offensiv noch defensiv ein Grund
        }

        let score =
            target + W_DISRUPTION * escalation * disruption as f64 + W_FLOOR * escalation * floor as f64;
        // Tie-Break unveraendert zum Bestand: knappste Farbe zuerst, dann die
        // vollste eigene Musterreihe, dann die kleinste (stabil).
        let scarcity = crate::provocation::color_index(m.take.color)
            .map(|i| remaining[i])
            .unwrap_or(i64::MAX);
        let filled = player.pattern_lines[r].tiles.len() as i32;
        // Alle vier Schluessel "groesser ist besser": Score hoch, Farbe knapp
        // (negiert), eigene Musterreihe voll, Index klein (negiert).
        let key = (score, -scarcity, filled, -(r as i32));
        let better = best.as_ref().map_or(true, |(bs, bk, bf, br, _)| key > (*bs, *bk, *bf, *br));
        if better {
            best = Some((key.0, key.1, key.2, key.3, m));
        }
    }
    best.map(|(_, _, _, _, m)| Action::Stone(m))
}

// ── Die beiden Einstiege ────────────────────────────────────────────────────

/// Drafting-Vorzug von hv3 -- UNGEGATET, also ohne `MOSAIC_SPALTENBAU` und ohne
/// `MOSAIC_PLATTENBAU`.
///
/// Beide Bestandsknoepfe sind prozessweit. Fuer eine Partie hv1 GEGEN hv3 sind
/// sie damit unbrauchbar: sie gaelten fuer beide Seiten oder fuer keine. Die
/// Variante ist der einzige Weg, der die Seiten trennt.
///
/// Erst der Stein-Zug, dann die KUPPELPLATTEN-Wahl. Die zweite ist der Grund,
/// warum die gestreute Start-Ecke die vollen Rasterzeilen von 0,400 auf 0,263
/// gedrueckt hat: startet die Kuppel unten, liegt in den oberen Rasterzeilen
/// frueh keine Platte, und genau die sind das Zeilenziel. Nutzer-Vorgabe
/// 2026-08-24: "dann muss man halt Kuppel ziehen fuer die oberen Rasterzeilen".
pub(crate) fn drafting_preference(state: &GameState) -> Option<Action> {
    let k = hull_target_map(state, state.current_player)?;
    let cells = cells_from_map(&k);
    hull_drafting_preference(state, &k, &cells).or_else(|| {
        crate::plate_builder::dome_preference_for_cells_weighted(state, &cells, &k, hull_cell_value)
    })
}

/// Tiling-Routing von hv3 -- ungegatet, siehe [`drafting_preference`].
///
/// Das ist die Haelfte, die ein reiner Bewertungsterm GAR NICHT beruehrt und
/// die laut `PREREG_provocation.md` der eigentliche Engpass ist: ohne sie
/// waehlt `best_first_step_inner` nach reinen Sofortpunkten
/// (`tiling_solver.rs:49-56`) und wirft jede Draft-seitige Absicht wieder weg.
pub(crate) fn tiling_preference(state: &GameState, pi: usize) -> Option<TilingStep> {
    let k = hull_target_map(state, pi)?;
    let cells = cells_from_map(&k);
    chip_preference(state, pi, &cells)
        .or_else(|| crate::plate_builder::tiling_preference_for_cells_weighted(state, pi, &cells, &k))
}

/// Vollendet per Bonuschip die Musterreihe, die eine ZIELZELLE blockiert -- nur
/// wenn diese Zelle sonst leer bliebe UND die Chip-Vollendung sofort
/// platzierbar ist (`row_has_open_matching_slot`). Kein Griff in fremde
/// Musterreihen: eine, die keine Zielzelle bedient, wird nie angefasst,
/// Bonuschips bleiben dafuer erhalten.
///
/// Befund 2026-08-24: trotz Routing null Chip-Vollendungen von Rasterreihe 6 in
/// 80 Partien, und 7,5 Prozent der Partien haben ueberhaupt keinen
/// R6-Abschluss -- ausnahmslos ohne jede volle Spalte. Die generische Suche
/// (`tiling_preference_for_cells_weighted` ueber `top_k_tilings`) SCHLIESST
/// Chip-Schritte technisch ein (`legal_steps` -> `chippable_rows`), findet sie
/// aber nicht zuverlaessig. Ein direkter Vorzug macht die Absicht explizit
/// statt auf den Suchzufall zu hoffen.
///
/// KORREKTUR 2026-08-25 (par.17, gemessen): die frueher hier stehende
/// ERKLAERUNG war falsch. Sie lautete, die Suche finde die Chip-Schritte im
/// DFS-Budget (2000 Knoten) nicht. Gemessen ueber 1671 Aufrufe: das Budget wird
/// NIE erschoepft (0 von 1671) und im Mittel zu 5,4 von 2000 Knoten genutzt.
/// Die Ursache liegt in der Kandidaten-Erzeugung oder in der Bewertung, nicht
/// in der Tiefe; WELCHE von beiden ist offen.
fn chip_preference(state: &GameState, pi: usize, cells: &[(usize, usize)]) -> Option<TilingStep> {
    let player = &state.players[pi];
    if player.bonus_chips.is_empty() {
        return None;
    }
    // `cells` sind RASTER-Koordinaten (r, c) im 6x6-Raster -- dieselbe
    // Konvention wie `column_build::cell_cost`. Musterreihe r speist GENAU
    // Rasterreihe r (`round_end::row_has_open_matching_slot` benutzt dieselbe
    // Zuordnung: `dome_row = r/2, space_row = r%2`), ein Umweg ueber
    // Slot-Koordinaten ist unnoetig -- `get_space` uebernimmt die Umrechnung.
    for &(r, c) in cells {
        let Some(sp) = player.dome_grid.get_space(r, c) else { continue };
        if sp.is_filled() || sp.is_locked {
            continue;
        }
        let line = &player.pattern_lines[r];
        if line.tiles.is_empty() || line.is_complete() {
            continue;
        }
        let Some(color) = line.color else { continue };
        if !sp.accepts(color) {
            continue; // diese Zelle nimmt eine ANDERE Farbe/keine Normalfarbe
        }
        if (r as i32) < player.tiled_max_row {
            continue; // Top-down-Sperre
        }
        if !crate::round_end::can_complete_row_with_chips(player, r) {
            continue;
        }
        if !crate::round_end::row_has_open_matching_slot(player, r, color) {
            continue;
        }
        if let Some(chips) = crate::round_end::greedy_chip_alloc(player, r) {
            return Some(TilingStep::Chips { row: r, chips });
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Die Prio-Leiter, Zelle fuer Zelle (Nutzer-Vorgabe 2026-08-24,
    /// erweiterte Fassung). Ohne diesen Test waere eine vertauschte Stufe nur
    /// in einer Arena sichtbar -- und dort nicht von "das Konzept traegt nicht"
    /// zu unterscheiden.
    ///
    /// Leeres Brett: ohne Kuppelplatten greift die Prio-5-Auflage nicht, der
    /// Test sieht also das reine Grundbild.
    #[test]
    fn priority_map_reflects_the_ladder() {
        let p = crate::board::PlayerBoard::new(0, "P");
        let k = priority_map(&p, &[], 0);
        for r in 0..6 {
            assert_eq!(k[r][0], PRIORITY_WEIGHT[0], "Prio 3: Randspalte 0, Rasterzeile {r}");
            assert_eq!(k[r][1], PRIORITY_WEIGHT[1], "Prio 4: zweite Spalte 1, Rasterzeile {r}");
        }
        for c in 2..6 {
            assert_eq!(k[0][c], PRIORITY_WEIGHT[3], "Prio 6: Rasterzeile 0, Spalte {c}");
            assert_eq!(k[1][c], PRIORITY_WEIGHT[3], "Prio 6: Rasterzeile 1, Spalte {c}");
            assert_eq!(k[2][c], PRIORITY_WEIGHT[4], "Prio 7: Nachbar Rasterzeile 2, Spalte {c}");
            assert_eq!(k[3][c], PRIORITY_WEIGHT[4], "Prio 7: Nachbar Rasterzeile 3, Spalte {c}");
            assert_eq!(k[4][c], 0.0, "Rasterzeile 4, Spalte {c} nicht im Grundbild");
            assert_eq!(k[5][c], 0.0, "Rasterzeile 5, Spalte {c} nicht im Grundbild");
        }
        for i in 0..4 {
            assert!(
                PRIORITY_WEIGHT[i] > PRIORITY_WEIGHT[i + 1],
                "Stufe {i} muss ueber {} liegen",
                i + 1
            );
        }
        assert!(PRIORITY_WEIGHT[4] > 0.0);
        // Prio 5 (Wertungsplatten) steht ueber Prio 6 (kurze Musterreihen).
        assert!(PRIORITY_WEIGHT[2] > PRIORITY_WEIGHT[3]);
    }

    /// "Bei Verwendung der Diagonale wird Prio 7 aufgeweicht."
    #[test]
    fn active_diagonal_softens_the_neighbour_tiebreak() {
        let p = crate::board::PlayerBoard::new(0, "P");
        let without = priority_map(&p, &[], 0);
        let with = priority_map(&p, &[K2_DIAGONALS], 0);
        assert_eq!(without[2][3], PRIORITY_WEIGHT[4]);
        assert_eq!(with[2][3], PRIORITY7_SOFTENED);
        assert!(PRIORITY7_SOFTENED < PRIORITY_WEIGHT[4]);
        // Die uebrigen Stufen bleiben unberuehrt.
        assert_eq!(without[0][0], with[0][0]);
        assert_eq!(without[0][3], with[0][3]);
    }

    /// Die Orientierung spiegelt NUR an der senkrechten Achse: Randspalte
    /// links oder rechts, die vollen Rasterzeilen bleiben oben.
    #[test]
    fn orientation_one_mirrors_the_columns_only() {
        let p = crate::board::PlayerBoard::new(0, "P");
        let right = priority_map(&p, &[], 1);
        for r in 0..6 {
            assert_eq!(right[r][5], PRIORITY_WEIGHT[0]);
            assert_eq!(right[r][4], PRIORITY_WEIGHT[1]);
        }
        assert_eq!(right[0][2], PRIORITY_WEIGHT[3]);
        assert_eq!(right[5][2], 0.0);
    }
}
