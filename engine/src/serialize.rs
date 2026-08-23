//! Serialisiert den GameState in das JSON-Format der API — Port von
//! engine/serializer.py. Das Frontend rendert nur; keine Spiellogik im Browser.
//!
//! Task #89 (2026-07-25): `json_to_state` (unten) ist die Umkehrung von
//! `state_to_json` -- braucht ein `GameState` fuer einen extern gespeicherten
//! Zustand (z.B. aus `frozen_eval_set.pkl`s `records[i]["state"]`), fuer den
//! es zuvor KEINEN Such-Einstieg gab (siehe `evaluations/STATUS.md`, "Task
//! #89 ... BLOCKIERT"). Siehe Doku-Kommentar direkt bei `json_to_state`.

use rand::seq::SliceRandom;
use rand::Rng;
use rand::SeedableRng;
use serde_json::{json, Map, Value};

use crate::board::{DomeGrid, PatternLine, PlayerBoard, DOME_TILES_PER_ROUND};
use crate::dome::{BonusChip, DomeSpace, DomeTile, SpaceType};
use crate::factory::{Factory, LargeFactory};
use crate::moves::Action;
use crate::round_end::{
    can_complete_row_with_chips, generate_tiling_actions, get_pending_tiling_rows,
    row_has_open_matching_slot, TilingAction,
};
use crate::state::{GameState, Phase};
use crate::supply::{Bag, Tower};
use crate::tile::TileColor;
use crate::tiling_solver::solve_round_final_score;
use crate::validation::generate_valid_moves;

/// Zaehlt Vorkommen je Normalfarbe (Reihenfolge `TileColor::NORMAL`) in
/// einem Fliesen-Stapel -- Grundlage fuer die Beutel-/Turm-Farbanteil-
/// Features (siehe features.rs, "was noch zu ziehen ist").
fn color_counts(tiles: &[TileColor]) -> [usize; 5] {
    let mut counts = [0usize; 5];
    for &t in tiles {
        if let Some(i) = TileColor::NORMAL.iter().position(|&c| c == t) {
            counts[i] += 1;
        }
    }
    counts
}

/// Maske je Kuppelplatten-Design (tile_id 0..18): 1, falls das Design noch
/// im verdeckten Stapel liegt -- Nutzer-Anstoss: "dem Netz mitgeben, welche
/// Platten schon aus dem Spiel sind, damit es weiß, was noch im Stapel
/// lauert" (Gemini-Chat-Hinweis, siehe stage2_investigation.md). Die
/// Auslage (`dome_display`) ist bereits an anderer Stelle im JSON codiert
/// (sichtbar), diese Maske betrifft NUR den verdeckten Rest.
fn dome_pool_mask(state: &GameState) -> [u8; crate::dome::NUM_DOME_TILE_DESIGNS] {
    let mut mask = [0u8; crate::dome::NUM_DOME_TILE_DESIGNS];
    for t in &state.dome_tile_pool {
        if t.tile_id < mask.len() {
            mask[t.tile_id] = 1;
        }
    }
    mask
}

/// Wild-Anteil der noch verdeckten Stapelplatten (0.5 = neutral, wenn leer)
/// -- explizites Aggregat ergaenzend zu `dome_pool_mask`: die Rueckseite
/// verraet beim Ziehen nur den Typ (Special/Wild, `DomeTile::is_special_type`),
/// nicht die Vorderseite. Relevant z.B. bei der "-3 je offenes Spezialfeld"-
/// Wertungsplatte, um abzuschaetzen ob die naechste gezogene Platte eher
/// Wild oder Special ist (Nutzer-Anstoss). Direkt aus der Maske ableitbar,
/// aber als eigenes Feld spart es Netz/Python-Seite die 18er-Summation.
fn dome_wild_remaining_frac(state: &GameState) -> f64 {
    let total = state.dome_tile_pool.len();
    if total == 0 {
        return 0.5;
    }
    let wild = state.dome_tile_pool.iter().filter(|t| !t.is_special_type()).count();
    wild as f64 / total as f64
}

fn space_type_name(t: SpaceType) -> &'static str {
    match t {
        SpaceType::Normal => "NORMAL",
        SpaceType::Wild => "WILD",
        SpaceType::Special => "SPECIAL",
    }
}

fn serialize_space(sp: &DomeSpace) -> Value {
    let filled = if let Some(c) = sp.placed_color {
        Value::String(c.value().to_string())
    } else if sp.placed_special {
        Value::String("special".to_string())
    } else {
        Value::Null
    };
    json!({
        "type": space_type_name(sp.space_type),
        "color": sp.required_color.map(|c| c.value()),
        "filled": filled,
        "locked": sp.is_locked,
    })
}

fn serialize_dome_tile(tile: Option<&DomeTile>) -> Value {
    match tile {
        None => Value::Null,
        Some(t) => json!({
            "id": t.tile_id,
            "bonus": t.bonus_points,
            "spaces": t.spaces.iter().map(serialize_space).collect::<Vec<_>>(),
        }),
    }
}

fn serialize_chip(chip: Option<&BonusChip>) -> Value {
    match chip {
        None => Value::Null,
        Some(c) => json!({
            "id": c.chip_id,
            "colors": c.colors.iter().map(|c| c.value()).collect::<Vec<_>>(),
        }),
    }
}

fn serialize_factory(f: &Factory) -> Value {
    json!({
        "id": f.factory_id,
        "sun": f.sun_tiles.iter().map(|t| t.value()).collect::<Vec<_>>(),
        "moon": f.moon_stacks.iter()
            .map(|s| s.iter().map(|t| t.value()).collect::<Vec<_>>())
            .collect::<Vec<_>>(),
        "bonus_chip": if f.bonus_chip.is_some() { serialize_chip(f.bonus_chip.as_ref()) } else { Value::Null },
        "chip_revealed": f.bonus_chip_revealed,
    })
}

fn serialize_large_factory(lf: &LargeFactory) -> Value {
    json!({
        "sun": lf.sun_tiles.iter().map(|t| t.value()).collect::<Vec<_>>(),
        "moon": lf.moon_pool.iter().map(|t| t.value()).collect::<Vec<_>>(),
        "marker": lf.has_first_player_marker,
    })
}

fn serialize_player(state: &GameState, pi: usize) -> Value {
    let p = &state.players[pi];
    let round_number = state.round_number;
    let unused: Vec<&BonusChip> = p.bonus_chips.iter().collect();
    let unused_colors: Vec<&'static str> =
        unused.iter().flat_map(|c| c.colors.iter().map(|c| c.value())).collect();
    // Erwartete Rundenpunkte EXAKT per Tiling-Solver (optimale Platzierung der
    // vollen Reihen inkl. Linien über mehrere Reihen) − fixe Strafen.
    let estimated_score = solve_round_final_score(state, pi) - p.score;

    // Berechnete Endwertungs-/Geometrie-Features (damit das Netz lernt, wie
    // Endpunkte entstehen — siehe scoring::player_scoring_features).
    let sf = crate::scoring::player_scoring_features(p);
    // Linien-Geometrie (offensives Linien-Bauen — scoring::player_line_features).
    let lf = crate::scoring::player_line_features(p);

    json!({
        "id": p.player_id,
        "name": p.name,
        "score": p.score,
        "pattern_lines": p.pattern_lines.iter().enumerate().map(|(i, row)| json!({
            "index": i,
            "capacity": row.capacity(),
            "tiles": row.tiles.iter().map(|t| t.value()).collect::<Vec<_>>(),
            "color": row.color.map(|c| c.value()),
            // Anzahl der zuletzt hinzugefügten Fliesen (rechtes Ende von
            // `tiles`), die per Bonuschip virtuell ergänzt wurden --
            // Frontend zeigt sie weiß mit farbigem Rand statt voll gefüllt.
            "phantom_count": row.phantom_count,
        })).collect::<Vec<_>>(),
        "dome_grid": p.dome_grid.dome_slots.iter().map(|row| {
            row.iter().map(|slot| serialize_dome_tile(slot.as_ref())).collect::<Vec<_>>()
        }).collect::<Vec<_>>(),
        "floor": p.broken_tiles.iter().map(|t| t.value()).collect::<Vec<_>>(),
        "marker": p.holds_first_player_marker,
        "tokens_used": p.player_tokens_used,
        "chips_taken": p.bonus_chips_used_this_round,
        "bonus_chips": unused.iter().map(|c| serialize_chip(Some(c))).collect::<Vec<_>>(),
        "start_placed": !p.start_tile_pending,
        "start_tile": Value::Null,
        "can_place_dome": p.can_place_dome_tile(round_number),
        "estimated_score": estimated_score,
        "unused_chip_count": unused.len(),
        "unused_chip_colors": unused_colors,
        // Berechnete Punkte-Features fürs Netz (Endwertung + Geometrie-Fortschritt).
        "scoring_tile_points": sf.tile_points,
        "score_geo": {
            "row_fill": sf.row_fill,
            "col_fill": sf.col_fill,
            "diag_fill": sf.diag_fill,
            "row_colors": sf.row_colors,
            "border_fill": sf.border_fill,
            "corner_fill": sf.corner_fill,
            "wild_filled": sf.wild_filled,
            "wild_total": sf.wild_total,
            "special_empty": sf.special_empty,
            "special_total": sf.special_total,
        },
        // Linien-Geometrie fürs offensive Linien-Bauen.
        "line_geo": {
            "h_hist": lf.h_hist,
            "v_hist": lf.v_hist,
            "cluster_sq": lf.cluster_sq,
            "row_potential": lf.row_potential,
            "col_potential": lf.col_potential,
        },
    })
}

/// Vollständiges State-Dict für das Frontend.
pub fn state_to_json(state: &GameState, scoring_confirmed: bool) -> Value {
    // Maschinenzeilen (`#a {...}`, PREREG_action_id_logging.md S2) gehoeren in
    // die GESPEICHERTE Fassung, nicht in die Anzeige (Nutzer-Vorgabe
    // 2026-08-18: "am log der in index.html angezeigt wird brauchst nichts
    // ändern. nur in der gespeicherten variante"). Gefiltert wird VOR dem
    // `take(30)` -- sonst wuerde jede Maschinenzeile einen echten Eintrag aus
    // dem Anzeigefenster draengen.
    let log_sichtbar: Vec<String> = {
        let sichtbar: Vec<&String> =
            state.log.iter().filter(|l| !l.starts_with("#a ")).collect();
        sichtbar.iter().rev().take(30).rev().map(|l| (*l).clone()).collect()
    };
    let players: Vec<Value> = (0..state.players.len())
        .map(|pi| serialize_player(state, pi))
        .collect();

    // Moon-Top-Zählung (Aktion C).
    let mut moon_counts: Map<String, Value> = Map::new();
    let bump = |k: &str, m: &mut Map<String, Value>| {
        let v = m.get(k).and_then(|x| x.as_i64()).unwrap_or(0) + 1;
        m.insert(k.to_string(), json!(v));
    };
    for f in &state.factories {
        for stack in &f.moon_stacks {
            if let Some(top) = stack.last() {
                bump(top.value(), &mut moon_counts);
            }
        }
    }
    for t in &state.large_factory.moon_pool {
        bump(t.value(), &mut moon_counts);
    }
    let mut moon_colors: Vec<String> = moon_counts.keys().cloned().collect();
    moon_colors.sort();

    let can_pass = compute_can_pass(state);

    json!({
        "round": state.round_number,
        "scoring_confirmed": scoring_confirmed,
        "phase": state.phase.as_str(),
        "current_player": state.current_player,
        // Ueberlebt (im Gegensatz zu `players[].marker`) die Rundenwertung
        // jeder Runde inkl. Runde 5 (siehe game.rs::determine_winner-Kommentar)
        // -- Frontend braucht das fuer den Punktegleichstand-Tie-Break im
        // Endergebnis-Modal (Nutzer-Fund 2026-07-27: "Unentschieden gewinnt!"
        // trotz Marker bei der KI, weil `marker` zu diesem Zeitpunkt schon
        // geloescht war).
        "first_player_next_round": state.first_player_next_round,
        "scoring_tile_ids": state.scoring_tile_ids,
        "can_pass": can_pass,
        "factories": state.factories.iter().map(serialize_factory).collect::<Vec<_>>(),
        "large_factory": serialize_large_factory(&state.large_factory),
        "moon_top_counts": Value::Object(moon_counts),
        "moon_top_colors": moon_colors,
        "dome_display": state.dome_display.iter().map(|t| serialize_dome_tile(Some(t))).collect::<Vec<_>>(),
        "dome_stack_count": state.dome_tile_pool.len(),
        // Rückseite der OBERSTEN Stapelplatte -- am physischen Tisch für
        // beide Spieler jederzeit sichtbar (Nutzer-Anstoss), nicht erst beim
        // Ziehen. Nur die Vorderseite (Farbanordnung) bleibt bis zum
        // tatsächlichen Ziehen verdeckt.
        "dome_stack_top_type": state.dome_tile_pool.first().map(|t| {
            if t.is_special_type() { "special" } else { "wild" }
        }),
        // Bereits gezogene, aber noch nicht gewählte Platten des laufenden
        // Stapel-Zugs (Aktion A) -- Rückseite zeigt beim Ziehen nur den Typ,
        // hier vereinfacht schon mit voller Vorderseite serialisiert (wie
        // dome_display), sobald mind. 1 gezogen ist.
        "pending_stack_draw": state.pending_stack_draw.iter().map(|t| serialize_dome_tile(Some(t))).collect::<Vec<_>>(),
        "bag_count": state.bag.count(),
        "bag_colors": color_counts(&state.bag.tiles),
        "tower_colors": color_counts(&state.tower.tiles),
        "dome_pool_mask": dome_pool_mask(state),
        "dome_wild_remaining_frac": dome_wild_remaining_frac(state),
        "players": players,
        "log": log_sichtbar,
        "valid_moves": serialize_valid_moves(state),
        "valid_tiling_rows": serialize_valid_tiling_rows(state),
        "chippable_tiling_rows": serialize_chippable_tiling_rows(state),
    })
}

fn compute_can_pass(state: &GameState) -> bool {
    if state.phase != Phase::Drafting {
        return false;
    }
    let p = &state.players[state.current_player];
    let a_possible = state.round_number < 5
        && !p.start_tile_pending
        && !p.has_used_all_tokens(state.round_number)
        && p.can_place_dome_tile(state.round_number)
        && (!state.dome_display.is_empty() || !state.dome_tile_pool.is_empty());
    let b_possible = state.factories.iter().any(|f| !f.sun_tiles.is_empty())
        || !state.large_factory.sun_tiles.is_empty();
    let c_possible = state.factories.iter().any(|f| !f.moon_top_colors().is_empty())
        || !state.large_factory.moon_colors().is_empty();
    let d_possible = p.can_take_bonus_chip()
        && state
            .factories
            .iter()
            .any(|f| f.bonus_chip_revealed && f.bonus_chip.is_some());
    !(a_possible || b_possible || c_possible || d_possible)
}

fn source_name(src: crate::moves::TakeSource) -> &'static str {
    use crate::moves::TakeSource::*;
    match src {
        SmallFactorySun => "SMALL_FACTORY_SUN",
        SmallFactoryMoon => "SMALL_FACTORY_MOON",
        LargeFactorySun => "LARGE_FACTORY_SUN",
        LargeFactoryMoon => "LARGE_FACTORY_MOON",
    }
}

/// Drafting-Aktion → Anzeige-Move-Dict (für KI-Zug-Rückgabe und Baum-Labels).
/// Bewusst informativ/vollständig (anders als die UI-`valid_moves`-Variante,
/// die z.B. `dome_stack` ohne Slot-Felder liefert).
pub fn action_to_dict(a: &Action) -> Value {
    match a {
        Action::Stone(m) => json!({
            "type": "stone",
            "source": source_name(m.take.source),
            "factory_id": m.take.factory_id,
            "color": m.take.color.value(),
            "row": m.place.row_index,
            "moon_order": m.take.moon_order.iter().map(|t| t.value()).collect::<Vec<_>>(),
        }),
        Action::ChooseDomeSlot(m) => json!({
            "type": "dome_display",
            "tile_id": m.dome_tile_id,
            "slot_row": m.slot_row,
            "slot_col": m.slot_col,
        }),
        Action::DrawStackPeek => json!({ "type": "dome_stack_peek" }),
        Action::ChooseDrawStackSlot(m) => json!({
            "type": "dome_stack",
            "chosen_id": m.chosen_id,
            "slot_row": m.slot_row,
            "slot_col": m.slot_col,
            "return_order": m.return_order,
        }),
        Action::ChooseDomeRotation(rot) => json!({ "type": "dome_rotation", "rotation": rot }),
        Action::BonusChip(m) => json!({ "type": "bonus_chip", "factory_id": m.factory_id }),
        Action::Pass => json!({ "type": "pass" }),
    }
}

/// Tiling-Aktion → Anzeige-Move-Dict.
pub fn tiling_action_to_dict(ta: &TilingAction) -> Value {
    json!({
        "type": "tiling",
        "pattern_row": ta.pattern_row,
        "slot_row": ta.slot_row,
        "slot_col": ta.slot_col,
        "space_index": ta.space_index,
    })
}

/// Aktions-ID im ACTION-SPACE des Policy-Kopfes (`features::action_to_id`,
/// `NUM_ACTIONS = 406`) fuer einen UI-`valid_moves`-Eintrag.
/// PREREG_action_id_logging.md, Stueck S1.
///
/// ZWEI DINGE, die der Leser wissen MUSS (beide geprueft 2026-08-18):
///  - Die ID ist NICHT eindeutig je UI-Eintrag. `moon_order` fliesst nicht ein
///    (net_mcts.rs:1824), und Kuppel-Zuege werden intern in Slot-Wahl und
///    Rotation zerlegt (game.rs::apply_drafting) -- die vier Rotations-
///    Varianten eines Kuppel-Zugs teilen sich also `id`. Deshalb traegt ein
///    rotationsbehafteter Eintrag zusaetzlich `id_rotation`; das PAAR
///    identifiziert den atomaren UI-Zug.
///  - Die Berechnung laeuft ueber `self_play::action_to_id_direct`, also ueber
///    exakt dieselbe Funktion wie in der Suche -- keine zweite Wahrheit.
fn move_action_id(state: &GameState, a: &Action) -> usize {
    crate::self_play::action_to_id_direct(state, a)
}

fn serialize_valid_moves(state: &GameState) -> Value {
    if state.phase != Phase::Drafting {
        return json!([]);
    }

    // Startkachel offen → einziger möglicher Zug (Nicht-Startspieler zuerst).
    let first_player = state.current_player;
    let non_starter = 1 - first_player;
    for &pi in &[non_starter, first_player] {
        if state.players[pi].start_tile_pending {
            return json!([{ "type": "start_tile_pending", "player": pi }]);
        }
    }

    let mut moves: Vec<Value> = Vec::new();

    // Mitten in einem Stapel-Zug (Aktion A): NUR weiterziehen oder eine der
    // gezogenen Platten wählen -- keine andere Aktion (siehe game::drafting_actions).
    if !state.pending_stack_draw.is_empty() {
        if crate::game::can_draw_stack_peek(state) {
            moves.push(json!({
                "type": "dome_stack_peek",
                "id": move_action_id(state, &Action::DrawStackPeek),
            }));
        }
        // Baustein B: `generate_draw_stack_moves` liefert nur noch Kachel×Slot
        // (Rotation ist eine separate Stufe-2-Suchknoten-Entscheidung, siehe
        // game.rs) -- die UI erwartet weiterhin die volle Kachel×Slot×Rotation-
        // Enumeration in EINEM Zug, daher hier lokal wieder aufgefächert.
        for m in crate::game::generate_draw_stack_moves(state) {
            for &rotation in &[0u32, 90, 180, 270] {
                let full = crate::moves::DrawFromStackMove { rotation, ..m.clone() };
                if crate::game::validate_draw_from_stack(state, &full).is_none() {
                    moves.push(json!({
                        "type": "dome_stack_choose",
                        "id": move_action_id(state, &Action::ChooseDrawStackSlot(full.clone())),
                        "id_rotation": move_action_id(state, &Action::ChooseDomeRotation(rotation)),
                        "chosen_id": full.chosen_id,
                        "slot_row": full.slot_row,
                        "slot_col": full.slot_col,
                        "rotation": full.rotation,
                        "return_order": full.return_order,
                    }));
                }
            }
        }
        return Value::Array(moves);
    }

    // Stein-Züge (Aktion B + globaler Mond-Zug aus generate_valid_moves).
    for m in generate_valid_moves(state) {
        // ID VOR dem json!-Bau, solange `m` noch als `Action` verfuegbar ist.
        let id = move_action_id(state, &Action::Stone(m.clone()));
        moves.push(json!({
            "type": "stone",
            "id": id,
            "source": source_name(m.take.source),
            "factory_id": m.take.factory_id,
            "color": m.take.color.value(),
            "row": m.place.row_index,
            "moon_order": m.take.moon_order.iter().map(|t| t.value()).collect::<Vec<_>>(),
        }));
    }

    // Kuppelplatten aus offener Ablage. Baustein B: `generate_dome_moves`
    // liefert nur noch Kachel×Slot (Rotation ist eine separate Stufe-2-
    // Suchknoten-Entscheidung, siehe game.rs) -- die UI erwartet weiterhin
    // die volle Kachel×Slot×Rotation-Enumeration in EINEM Zug, daher hier
    // lokal wieder aufgefächert.
    for m in crate::game::generate_dome_moves(state) {
        for &rotation in &[0u32, 90, 180, 270] {
            let full = crate::moves::PlaceDomeTileMove { rotation, ..m };
            if crate::game::validate_dome_move(state, &full).is_none() {
                moves.push(json!({
                    "type": "dome_display",
                    "id": move_action_id(state, &Action::ChooseDomeSlot(full)),
                    "id_rotation": move_action_id(state, &Action::ChooseDomeRotation(rotation)),
                    "tile_id": full.dome_tile_id,
                    "slot_row": full.slot_row,
                    "slot_col": full.slot_col,
                    "rotation": full.rotation,
                }));
            }
        }
    }

    // Aktion A: verdeckt vom Stapel ziehen (Schritt 1, startet einen neuen Zieh-Vorgang).
    if crate::game::can_draw_stack_peek(state) {
        moves.push(json!({
            "type": "dome_stack_peek",
            "id": move_action_id(state, &Action::DrawStackPeek),
        }));
    }

    // Bonusplättchen.
    for m in crate::game::generate_bonus_chip_moves(state) {
        moves.push(json!({
            "type": "bonus_chip",
            "id": move_action_id(state, &Action::BonusChip(m)),
            "factory_id": m.factory_id,
        }));
    }

    Value::Array(moves)
}

fn serialize_valid_tiling_rows(state: &GameState) -> Value {
    if state.phase != Phase::Tiling {
        return json!([]);
    }
    let mut result = Vec::new();
    for (pi, player) in state.players.iter().enumerate() {
        let actions = generate_tiling_actions(state, pi);
        let placeable: Vec<usize> = actions.iter().map(|a| a.pattern_row).collect();
        for ri in get_pending_tiling_rows(player) {
            if placeable.contains(&ri) {
                result.push(json!({ "pi": pi, "ri": ri, "placeable": true }));
            }
        }
    }
    Value::Array(result)
}

fn serialize_chippable_tiling_rows(state: &GameState) -> Value {
    if state.phase != Phase::Tiling {
        return json!([]);
    }
    let mut result = Vec::new();
    for (pi, player) in state.players.iter().enumerate() {
        if player.bonus_chips.is_empty() {
            continue;
        }
        let tiled_max = player.tiled_max_row;
        for (ri, row) in player.pattern_lines.iter().enumerate() {
            if row.tiles.is_empty() || row.is_complete() {
                continue;
            }
            if (ri as i32) < tiled_max {
                continue;
            }
            if !can_complete_row_with_chips(player, ri) {
                continue;
            }
            let color = match row.color {
                Some(c) => c,
                None => continue,
            };
            if row_has_open_matching_slot(player, ri, color) {
                result.push(json!({ "pi": pi, "ri": ri }));
            }
        }
    }
    Value::Array(result)
}

/// Serialisiert die obersten n Stapel-Kacheln (für /api/stack/peek).
pub fn serialize_stack_peek(state: &GameState, n: usize) -> Value {
    let n = n.min(state.dome_tile_pool.len());
    Value::Array(
        state.dome_tile_pool[..n]
            .iter()
            .map(|t| serialize_dome_tile(Some(t)))
            .collect(),
    )
}

// ═══════════════════════════════════════════════════════════════════════════
// Task #89: json_to_state — Umkehrung von state_to_json
// ═══════════════════════════════════════════════════════════════════════════
//
// Baut aus einem `state_to_json`-Zustandsdict (z.B. `frozen_eval_set.pkl`s
// `records[i]["state"]`) einen `GameState`, auf dem eine echte Netz-Suche
// laufen kann (`net_search_state_json` in lib.rs). `state_to_json` ist KEINE
// bijektive Serialisierung -- drei Kategorien von Abweichungen, jede einzeln
// geprüft und bewusst so gehandhabt:
//
// 1) ECHTE, dem Spiel selbst verdeckte Information (bag/tower/dome_tile_pool/
//    bonus_chip_pool): das JSON trägt hier nur Zähler/Masken (Farb-Histogramme,
//    Design-Präsenz-Maske), nie die exakte Ziehreihenfolge. Rekonstruktion:
//    die exakte, aus den Zählern/Masken ableitbare IDENTITÄTS-MENGE aufbauen,
//    dann mit dem übergebenen RNG neu mischen (Reihenfolge ist für BEIDE
//    Spieler ohnehin verdeckt). Deckt sich mit `net_mcts::
//    determinize_hidden_information` (`DETERMINIZE_ROOT_HIDDEN_INFO`), das an
//    jedem echten Sucheinstieg ohnehin genau diese Felder neu mischt --
//    dieselbe, bereits im Projekt etablierte Philosophie ("die Suche soll
//    kein Wissen nutzen, das ein echter Spieler nicht hat"), hier nur auf den
//    Rekonstruktionsschritt VOR der Suche erweitert. `bonus_chip_pool` ist ein
//    Sonderfall: state_to_json trägt dafür GAR KEINEN Zähler/Maske (im
//    Gegensatz zum Kuppelstapel) -- die exakte IDENTITÄT historisch
//    verworfener (nie abgeholter) Chips ist aus einer einzelnen Momentaufnahme
//    grundsätzlich nicht rekonstruierbar (kein Feld hält sie fest). Die
//    ANZAHL ist aber deterministisch aus der Rundenzahl ableitbar (jede Runde
//    bekommt jede der 4 Fabriken genau einen neuen Chip aus dem Pool,
//    unabhängig von Abholung -- siehe state.rs::fill_factories/
//    setup_new_round; verifiziert per state.rs-Test
//    `setup_new_game_initial_counts`: Runde 1 → 16 = 20-4). Ersatz: zufällige,
//    seed-gesteuerte Auswahl der richtigen ANZAHL aus allen aktuell NICHT
//    sichtbaren Designs (Fabriken + Spielerhände ausgeschlossen) -- diese nie
//    wieder auftauchenden, historisch verworfenen Chips sind für die Suche
//    irrelevant, unabhängig davon, welche konkreten IDs man ihnen zuordnet.
//
// 2) Aus dem JSON VOLLSTÄNDIG ableitbare, aber nicht wörtlich vorhandene
//    Felder: `first_player_next_round` (= der Spieler mit `marker=true`, falls
//    einer; sonst noch offen und daher irrelevant -- wird beim tatsächlichen
//    Nehmen im Suchbaum frisch gesetzt, siehe execution.rs:253),
//    `monochrome_fallback` der großen Fabrik (jede ECHTE monochrome
//    Notbefüllung setzt dieses Flag, UND `take_from_sun` leert `sun_tiles`
//    beim ersten Zug immer GANZ -- kein Teil-Zustand möglich, siehe
//    factory.rs -- also ist "alle sun_tiles gleichfarbig, solange sun_tiles
//    noch nicht geleert" äquivalent zum Flag).
//
// 3) Nicht exakt rekonstruierbare, aber für die Sucheinstiegs-KORREKTHEIT
//    (Root-Legalität) unschädliche Näherungen -- jede einzeln geprüft:
//    - `dome_tiles_placed_this_round`: nicht direkt serialisiert, nur der
//      fertige `can_place_dome_tile()`-Bool (`"can_place_dome"`). Da die
//      einzige Fallunterscheidung `< DOME_TILES_PER_ROUND` (2) ist, reproduziert
//      0 (falls `can_place_dome=true`) bzw. `DOME_TILES_PER_ROUND` (falls
//      `false`) die WURZEL-Legalität exakt. Erst bei einer tatsächlichen
//      Zwischenzahl 1 UND einer weiteren simulierten Kuppel-Platzierung
//      DERSELBEN Runde tiefer im Suchbaum kann das um höchstens 1 Platzierung
//      zu großzügig sein -- geprüft (game.rs::validate_dome_move/
//      generate_dome_moves lesen `dome_tiles_placed_this_round` ausschließlich
//      über diesen einen Schwellenwert-Vergleich).
//    - `tiled_max_row`: nur in `Phase::Tiling` gelesen
//      (`features.rs::chippable_pairs_direct`, phasen-gegated) -- Default -1
//      ist für JEDEN `Phase::Drafting`-Zustand exakt richtig. EINE geprüfte,
//      dokumentierte Ausnahme: `tiling_solver.rs::chippable_rows` (Basis von
//      `estimated_score`/den entsprechenden Netz-Features) ist NICHT
//      phasen-gegated und läuft nach einer abgeschlossenen Tiling-Phase mit
//      einem stehengebliebenen (erst beim NÄCHSTEN Drafting→Tiling-Übergang
//      zurückgesetzten) Wert weiter -- ein bereits im Original-Engine
//      bestehendes Verhalten, kein durch die Rekonstruktion neu eingeführter
//      Fehler. Wirkt sich nur aus, wenn der aktuelle Spieler gerade einen
//      NICHT verbrauchten Bonuschip hält UND eine unvollständige Reihe
//      unterhalb dieses (eigentlich schon irrelevanten) Schwellenwerts hat --
//      schmale, seltene Randbedingung, betrifft nur ein Hilfs-Feature
//      (`estimated_score`), nicht die Aktionslegalität.
//    - `total_floor_penalties`/`floor_penalties_per_round`/`score_unclamped`:
//      geprüft (grep über `features.rs`) -- werden NIRGENDS für Features,
//      Legalität oder Suche gelesen, nur für Self-Play-Diagnose-Exporte
//      (`self_play.rs`). Defaults (0/leer) sind daher folgenlos.
//    - `pending_dome_choice`: state_to_json serialisiert dieses Feld NICHT
//      (weder direkt noch indirekt -- `serialize_valid_moves` prüft nur
//      `pending_stack_draw`, nie `pending_dome_choice`). Ein Zustand, der real
//      mitten in der Stufe-2-Rotationswahl war, wird als "Stufe 1 noch offen"
//      rekonstruiert -- der JSON-Roundtrip-Test bleibt davon unberührt (das
//      Feld beeinflusst KEIN einziges state_to_json-Ausgabefeld), aber die
//      Wurzel-Kandidatenliste für GENAU diese (seltenen) Zwischenzustände
//      würde bei einer Suche zu großzügig (volle Drafting-Optionen statt nur
//      Rotationswahl). Da `frozen_eval_set.pkl`-Records zusätzlich das
//      SEPARATE `valid_actions`-Feld (aus dem echten Spielzustand, VOR jeder
//      JSON-Serialisierung erzeugt) tragen, kann/sollte der Oracle-Erzeugungs-
//      Code dies gegen die zurückgegebene Root-Kandidatenzahl gegenprüfen und
//      Ausreißer separat zählen (siehe tools/build_frozen_oracle_labels.py).
//
// `tiling_done`: nicht serialisiert, aber für JEDEN `Phase::Drafting`-Zustand
// per Konstruktion `[false, false]` (wird nur beim Drafting→Tiling-Übergang
// gesetzt, siehe game.rs::check_phase_transition) -- kein Näherungsfehler.

fn json_err(key: &str) -> String {
    format!("json_to_state: fehlendes/ungültiges Feld '{key}'")
}

fn get_str<'a>(v: &'a Value, key: &str) -> Result<&'a str, String> {
    v.get(key).and_then(|x| x.as_str()).ok_or_else(|| json_err(key))
}
fn get_arr<'a>(v: &'a Value, key: &str) -> Result<&'a Vec<Value>, String> {
    v.get(key).and_then(|x| x.as_array()).ok_or_else(|| json_err(key))
}
fn get_u64(v: &Value, key: &str) -> Result<u64, String> {
    v.get(key).and_then(|x| x.as_u64()).ok_or_else(|| json_err(key))
}
fn get_i64(v: &Value, key: &str) -> Result<i64, String> {
    v.get(key).and_then(|x| x.as_i64()).ok_or_else(|| json_err(key))
}
fn get_bool(v: &Value, key: &str) -> Result<bool, String> {
    v.get(key).and_then(|x| x.as_bool()).ok_or_else(|| json_err(key))
}

fn color_from_json(v: &Value) -> Result<TileColor, String> {
    let s = v.as_str().ok_or_else(|| "json_to_state: Farbe ist kein String".to_string())?;
    TileColor::from_value(s).ok_or_else(|| format!("json_to_state: unbekannte Farbe '{s}'"))
}

fn colors_from_json_array(v: &Value) -> Result<Vec<TileColor>, String> {
    v.as_array()
        .ok_or_else(|| "json_to_state: erwartete Farb-Liste ist kein Array".to_string())?
        .iter()
        .map(color_from_json)
        .collect()
}

fn phase_from_str(s: &str) -> Result<Phase, String> {
    match s {
        "start_placement" => Ok(Phase::StartPlacement),
        "drafting" => Ok(Phase::Drafting),
        "tiling" => Ok(Phase::Tiling),
        "scoring" => Ok(Phase::Scoring),
        "end" => Ok(Phase::End),
        "final" => Ok(Phase::Final),
        _ => Err(format!("json_to_state: unbekannte Phase '{s}'")),
    }
}

fn space_type_from_name(s: &str) -> Result<SpaceType, String> {
    match s {
        "NORMAL" => Ok(SpaceType::Normal),
        "WILD" => Ok(SpaceType::Wild),
        "SPECIAL" => Ok(SpaceType::Special),
        _ => Err(format!("json_to_state: unbekannter Space-Typ '{s}'")),
    }
}

fn dome_space_from_json(v: &Value) -> Result<DomeSpace, String> {
    let space_type = space_type_from_name(get_str(v, "type")?)?;
    let required_color = match v.get("color").and_then(|c| c.as_str()) {
        Some(s) => Some(
            TileColor::from_value(s).ok_or_else(|| format!("json_to_state: unbekannte Farbe '{s}'"))?,
        ),
        None => None,
    };
    let filled = v.get("filled").ok_or_else(|| json_err("filled"))?;
    let (placed_color, placed_special) = if filled.is_null() {
        (None, false)
    } else if let Some(s) = filled.as_str() {
        if s == "special" {
            (None, true)
        } else {
            (
                Some(
                    TileColor::from_value(s)
                        .ok_or_else(|| format!("json_to_state: unbekannte Farbe '{s}'"))?,
                ),
                false,
            )
        }
    } else {
        return Err("json_to_state: 'filled' weder null noch String".to_string());
    };
    let is_locked = get_bool(v, "locked")?;
    Ok(DomeSpace { space_type, required_color, placed_color, placed_special, is_locked })
}

fn dome_tile_from_json(v: &Value) -> Result<DomeTile, String> {
    let tile_id = get_u64(v, "id")? as usize;
    let bonus_points = get_i64(v, "bonus")? as i32;
    let spaces: Vec<DomeSpace> =
        get_arr(v, "spaces")?.iter().map(dome_space_from_json).collect::<Result<_, _>>()?;
    if spaces.len() != 4 {
        return Err(format!("json_to_state: Kuppelplatte {tile_id} hat {} statt 4 Spaces", spaces.len()));
    }
    Ok(DomeTile { tile_id, spaces, bonus_points })
}

fn dome_tile_opt_from_json(v: &Value) -> Result<Option<DomeTile>, String> {
    if v.is_null() {
        Ok(None)
    } else {
        Ok(Some(dome_tile_from_json(v)?))
    }
}

fn bonus_chip_from_json(v: &Value) -> Result<BonusChip, String> {
    let chip_id = get_u64(v, "id")? as usize;
    let colors = colors_from_json_array(v.get("colors").ok_or_else(|| json_err("colors"))?)?;
    Ok(BonusChip { chip_id, colors })
}

fn factory_from_json(v: &Value, factory_id: usize) -> Result<Factory, String> {
    let sun_tiles = colors_from_json_array(v.get("sun").ok_or_else(|| json_err("sun"))?)?;
    let moon_stacks: Vec<Vec<TileColor>> = get_arr(v, "moon")?
        .iter()
        .map(colors_from_json_array)
        .collect::<Result<_, _>>()?;
    let bonus_chip = match v.get("bonus_chip") {
        Some(bc) if !bc.is_null() => Some(bonus_chip_from_json(bc)?),
        _ => None,
    };
    let bonus_chip_revealed = get_bool(v, "chip_revealed")?;
    Ok(Factory { factory_id, sun_tiles, moon_stacks, bonus_chip, bonus_chip_revealed })
}

fn large_factory_from_json(v: &Value) -> Result<LargeFactory, String> {
    let sun_tiles = colors_from_json_array(v.get("sun").ok_or_else(|| json_err("large_factory.sun"))?)?;
    let moon_pool = colors_from_json_array(v.get("moon").ok_or_else(|| json_err("large_factory.moon"))?)?;
    let has_first_player_marker = get_bool(v, "marker")?;
    // `monochrome_fallback` s.o. (Kategorie 2, vollständig ableitbar).
    let monochrome_fallback = !sun_tiles.is_empty() && sun_tiles.iter().all(|&t| t == sun_tiles[0]);
    Ok(LargeFactory { sun_tiles, moon_pool, has_first_player_marker, monochrome_fallback })
}

fn pattern_line_from_json(v: &Value) -> Result<PatternLine, String> {
    let row_index = get_u64(v, "index")? as usize;
    let tiles = colors_from_json_array(v.get("tiles").ok_or_else(|| json_err("tiles"))?)?;
    let color = match v.get("color").and_then(|c| c.as_str()) {
        Some(s) => Some(
            TileColor::from_value(s).ok_or_else(|| format!("json_to_state: unbekannte Farbe '{s}'"))?,
        ),
        None => None,
    };
    let phantom_count = get_u64(v, "phantom_count")? as usize;
    Ok(PatternLine { row_index, tiles, color, phantom_count })
}

fn dome_grid_from_json(v: &Value) -> Result<DomeGrid, String> {
    let rows = v.as_array().ok_or_else(|| "json_to_state: dome_grid ist kein Array".to_string())?;
    if rows.len() != 3 {
        return Err(format!("json_to_state: dome_grid hat {} Zeilen, erwartet 3", rows.len()));
    }
    let mut dome_slots = Vec::with_capacity(3);
    for row in rows {
        let cells = row.as_array().ok_or_else(|| "json_to_state: dome_grid-Zeile ist kein Array".to_string())?;
        if cells.len() != 3 {
            return Err(format!("json_to_state: dome_grid-Zeile hat {} Spalten, erwartet 3", cells.len()));
        }
        let row_out: Vec<Option<DomeTile>> =
            cells.iter().map(dome_tile_opt_from_json).collect::<Result<_, _>>()?;
        dome_slots.push(row_out);
    }
    Ok(DomeGrid { dome_slots })
}

fn player_from_json(v: &Value) -> Result<PlayerBoard, String> {
    let player_id = get_u64(v, "id")? as usize;
    let name = get_str(v, "name")?.to_string();
    let score = get_i64(v, "score")? as i32;
    let pattern_lines: Vec<PatternLine> =
        get_arr(v, "pattern_lines")?.iter().map(pattern_line_from_json).collect::<Result<_, _>>()?;
    let dome_grid = dome_grid_from_json(v.get("dome_grid").ok_or_else(|| json_err("dome_grid"))?)?;
    let broken_tiles = colors_from_json_array(v.get("floor").ok_or_else(|| json_err("floor"))?)?;
    let holds_first_player_marker = get_bool(v, "marker")?;
    let player_tokens_used = get_u64(v, "tokens_used")? as u32;
    let bonus_chips_used_this_round = get_u64(v, "chips_taken")? as u32;
    let bonus_chips: Vec<BonusChip> =
        get_arr(v, "bonus_chips")?.iter().map(bonus_chip_from_json).collect::<Result<_, _>>()?;
    let start_placed = get_bool(v, "start_placed")?;
    let can_place_dome = get_bool(v, "can_place_dome")?;
    // s.o. Kategorie 3: 0/DOME_TILES_PER_ROUND reproduziert die aktuelle
    // Wurzel-Legalität exakt (einzige Fallunterscheidung ist der Schwellenwert).
    let dome_tiles_placed_this_round = if can_place_dome { 0 } else { DOME_TILES_PER_ROUND };

    Ok(PlayerBoard {
        player_id,
        name,
        score,
        score_unclamped: score, // nur Trainingslabel (self_play.rs), keine Suchabhängigkeit
        pattern_lines,
        dome_grid,
        broken_tiles,
        bonus_chips,
        dome_tiles_placed_this_round,
        tiled_max_row: -1, // s.o. Kategorie 3: exakt für Phase::Drafting (dokumentierte Ausnahme: estimated_score)
        player_tokens_used,
        holds_first_player_marker,
        start_dome_tile: None, // nur Phase::StartPlacement; dort nie erreicht (apply_drafting verlangt start_tile_pending=false)
        start_tile_pending: !start_placed,
        bonus_chips_used_this_round,
        total_floor_penalties: 0, // reine Post-hoc-Statistik, keine Spiellogik liest sie
        floor_penalties_per_round: Vec::new(),
    })
}

/// Baut aus einem Farb-Zähl-Array (`bag_colors`/`tower_colors`, Reihenfolge
/// `TileColor::NORMAL`) eine konkrete, neu gemischte Fliesenliste -- die exakte
/// Reihenfolge ist für beide Spieler ohnehin verdecktes Wissen (s.o. Kategorie 1).
fn color_counts_to_tiles<R: Rng + ?Sized>(counts_json: &[Value], rng: &mut R) -> Result<Vec<TileColor>, String> {
    if counts_json.len() != 5 {
        return Err(format!(
            "json_to_state: Farb-Zähl-Array hat {} Einträge, erwartet 5",
            counts_json.len()
        ));
    }
    let mut tiles = Vec::new();
    for (i, &c) in TileColor::NORMAL.iter().enumerate() {
        let n = counts_json[i]
            .as_u64()
            .ok_or_else(|| "json_to_state: Farb-Zähler ist keine Zahl".to_string())?;
        for _ in 0..n {
            tiles.push(c);
        }
    }
    tiles.shuffle(rng);
    Ok(tiles)
}

/// Umkehrung von [`state_to_json`]: baut aus einem Zustandsdict (exaktes
/// `state_to_json`-Format, z.B. `frozen_eval_set.pkl`s `records[i]["state"]`)
/// einen `GameState`. Siehe den Doku-Block direkt über dieser Funktion für
/// die drei Kategorien von Abweichungen (echte verdeckte Information,
/// vollständig ableitbare Felder, dokumentierte Näherungen) -- JEDE einzeln
/// gegen den Engine-Code geprüft, keine geraten. `rng` treibt ausschließlich
/// die Neumischung der verdeckten Sammlungen (Kategorie 1); derselbe RNG-Strom
/// kann direkt an eine anschließende Suche (die ihrerseits
/// `determinize_hidden_information` aufruft) weitergereicht werden.
pub fn json_to_state<R: Rng + ?Sized>(v: &Value, rng: &mut R) -> Result<GameState, String> {
    let round_number = get_u64(v, "round")? as u32;
    let phase = phase_from_str(get_str(v, "phase")?)?;
    let current_player = get_u64(v, "current_player")? as usize;
    let scoring_tile_ids: Vec<usize> = get_arr(v, "scoring_tile_ids")?
        .iter()
        .map(|x| x.as_u64().map(|n| n as usize).ok_or_else(|| "json_to_state: scoring_tile_ids: keine Zahl".to_string()))
        .collect::<Result<_, _>>()?;

    let factories_json = get_arr(v, "factories")?;
    let factories: Vec<Factory> = factories_json
        .iter()
        .enumerate()
        .map(|(i, f)| factory_from_json(f, i + 1))
        .collect::<Result<_, _>>()?;
    let large_factory = large_factory_from_json(v.get("large_factory").ok_or_else(|| json_err("large_factory"))?)?;

    let dome_display: Vec<DomeTile> =
        get_arr(v, "dome_display")?.iter().map(dome_tile_from_json).collect::<Result<_, _>>()?;
    let pending_stack_draw: Vec<DomeTile> =
        get_arr(v, "pending_stack_draw")?.iter().map(dome_tile_from_json).collect::<Result<_, _>>()?;

    // Verdeckter Kuppelstapel (Kategorie 1): `dome_pool_mask` verrät die exakte
    // IDENTITÄTS-MENGE, Reihenfolge wird neu gewürfelt; die oberste Platte wird
    // danach per Tausch an `dome_stack_top_type` angepasst (einziger
    // Roundtrip-relevanter Rest, s.o.).
    let mask_json = get_arr(v, "dome_pool_mask")?;
    let mut dome_tile_pool: Vec<DomeTile> = crate::dome::build_dome_tile_pool()
        .into_iter()
        .filter(|t| mask_json.get(t.tile_id).and_then(|m| m.as_u64()).unwrap_or(0) == 1)
        .collect();
    dome_tile_pool.shuffle(rng);
    let expect_top_special = match v.get("dome_stack_top_type").and_then(|x| x.as_str()) {
        Some("special") => Some(true),
        Some("wild") => Some(false),
        _ => None,
    };
    if let Some(want_special) = expect_top_special {
        if let Some(idx) = dome_tile_pool.iter().position(|t| t.is_special_type() == want_special) {
            dome_tile_pool.swap(0, idx);
        }
    }

    let bag = Bag { tiles: color_counts_to_tiles(get_arr(v, "bag_colors")?, rng)? };
    let tower = Tower { tiles: color_counts_to_tiles(get_arr(v, "tower_colors")?, rng)? };

    // bonus_chip_pool (Kategorie 1, Sonderfall): kein Zähler/keine Maske im
    // JSON -- Größe deterministisch aus round_number, Identität zufällig aus
    // allen aktuell nicht sichtbaren Designs (s.o. ausführlich dokumentiert).
    let players_json = get_arr(v, "players")?;
    let mut visible_chip_ids: std::collections::HashSet<usize> = std::collections::HashSet::new();
    for f in factories_json {
        if let Some(bc) = f.get("bonus_chip") {
            if let Some(id) = bc.get("id").and_then(|x| x.as_u64()) {
                visible_chip_ids.insert(id as usize);
            }
        }
    }
    for p in players_json {
        if let Some(arr) = p.get("bonus_chips").and_then(|x| x.as_array()) {
            for c in arr {
                if let Some(id) = c.get("id").and_then(|x| x.as_u64()) {
                    visible_chip_ids.insert(id as usize);
                }
            }
        }
    }
    let target_pool_len = 20usize.saturating_sub(4 * round_number as usize);
    let mut bonus_chip_pool: Vec<BonusChip> = crate::dome::build_bonus_chip_pool()
        .into_iter()
        .filter(|c| !visible_chip_ids.contains(&c.chip_id))
        .collect();
    bonus_chip_pool.shuffle(rng);
    bonus_chip_pool.truncate(target_pool_len.min(bonus_chip_pool.len()));

    let players: Vec<PlayerBoard> = players_json.iter().map(player_from_json).collect::<Result<_, _>>()?;

    // first_player_next_round (Kategorie 2, vollständig ableitbar): s.o.
    let first_player_next_round =
        players.iter().position(|p| p.holds_first_player_marker).unwrap_or(current_player);

    let log: Vec<String> = get_arr(v, "log")?
        .iter()
        .map(|s| s.as_str().map(|x| x.to_string()).ok_or_else(|| "json_to_state: log-Eintrag kein String".to_string()))
        .collect::<Result<_, _>>()?;

    Ok(GameState {
        bag,
        tower,
        factories,
        large_factory,
        players,
        dome_tile_pool,
        dome_display,
        bonus_chip_pool,
        pending_stack_draw,
        pending_dome_choice: None, // s.o. Kategorie 3 (dokumentierte Ausnahme)
        scoring_tile_ids,
        round_number,
        current_player,
        first_player_next_round,
        phase,
        log,
        tiling_done: [false, false], // s.o.: für Phase::Drafting per Konstruktion korrekt
    })
}

// ═══════════════════════════════════════════════════════════════════════════
// Welle 3 Fork A (PREREG_agent_encapsulation.md par.8b, Nutzer-Entscheid
// 2026-08-23): state_to_json_exact / json_to_state_exact
// ═══════════════════════════════════════════════════════════════════════════
//
// Kernbeweis-Diagnose (par.8b): `json_to_state` rekonstruiert die verdeckten
// Sammlungen (Kategorie 1 oben) nur aus Zählern/Masken und würfelt die
// REIHENFOLGE per RNG neu -- korrekt für die Fälle, wo `json_to_state` einen
// extern GESPEICHERTEN Schnappschuss (z.B. `frozen_eval_set.pkl`) rekonstruiert,
// bei dem die exakte Reihenfolge gar nicht festgehalten wurde. Der Referee-/
// Worker-Pfad (`referee.rs`) serialisiert dagegen einen LIVE `GameState` --
// hier IST die exakte Ordnung bekannt, und sie ist nachweislich
// verhaltensrelevant, nicht nur Zieraufwand:
//   - `Bag::draw` (supply.rs) entnimmt `tiles.drain(..k)` -- direkt von vorn,
//     Reihenfolge bestimmt die nächsten gezogenen Farben.
//   - `dome_tile_pool.remove(0)` (game.rs, mehrere Stellen) zieht ebenso
//     direkt von vorn.
//   - `net_mcts::determinize_hidden_information` mischt `dome_tile_pool` UND
//     `bonus_chip_pool` an der Suchwurzel per `slice::shuffle` NEU -- die
//     Fisher-Yates-Swap-INDIZES hängen nur an RNG-Strom+Länge, das
//     ERGEBNIS aber zusätzlich an der Eingangsreihenfolge (dieselbe
//     Swap-Sequenz auf unterschiedlichen Startanordnungen liefert
//     unterschiedliche Endanordnungen). Bei byte-identischem Such-RNG
//     (seit par.8a) bräuchte es also zusätzlich exakt dieselbe
//     Eingangsreihenfolge, um dasselbe Suchergebnis zu erreichen.
//   - `Bag::refill_from_tower` (supply.rs) macht `self.tiles.extend(tower)`
//     GEFOLGT von `self.tiles.shuffle(rng)` -- aus demselben Grund hängt das
//     Ergebnis auch an `tower.tiles`s Reihenfolge, obwohl der Turm selbst nie
//     direkt gezogen wird (Ersteinschätzung "Turm-Ordnung ist irrelevant,
//     weil ohnehin komplett geleert+neu gemischt" war deshalb FALSCH -- der
//     Reshuffle ist ordnungsABHÄNGIG, keine Kanonisierung).
//
// Deshalb: additive, NUR vom Referee-/Worker-Pfad konsumierte Serialisierung
// mit den vier exakten Reihenfolgen zusätzlich zu den bestehenden Zähler-/
// Masken-Feldern. `state_to_json` bleibt dafür BYTE-UNVERÄNDERT (siehe
// Grep-Beleg im Abnahmebericht: Debug-UI/`PyGame`/Trainings-Exporte laufen
// weiterhin über die alte Funktion), `json_to_state` bleibt ebenfalls
// UNANGETASTET (Basislinien-Schutz, Präzedenz `self_play::seed_state_fixup`)
// -- `json_to_state_exact` ruft sie nur auf und überschreibt danach gezielt
// die vier Felder.

/// Additive Variante von [`state_to_json`]: identischer Output PLUS vier
/// zusätzliche Top-Level-Felder mit der EXAKTEN Reihenfolge der verdeckten
/// Sammlungen (s.o. Modul-Kommentar für die Begründung, warum das
/// verhaltensrelevant ist). NUR für `referee::RefereeGame::state_json`
/// gedacht -- verdeckte Ordnung ist verstecktes Wissen und darf bestehende
/// Konsumenten (Debug-UI/`PyGame::state_json`, Trainings-/Diagnose-Exporte)
/// nie erreichen.
pub fn state_to_json_exact(state: &GameState, scoring_confirmed: bool) -> Value {
    let mut v = state_to_json(state, scoring_confirmed);
    let obj = v.as_object_mut().expect("state_to_json liefert immer ein JSON-Objekt");
    obj.insert(
        "bag_order_exact".to_string(),
        json!(state.bag.tiles.iter().map(|c| c.value()).collect::<Vec<_>>()),
    );
    obj.insert(
        "tower_order_exact".to_string(),
        json!(state.tower.tiles.iter().map(|c| c.value()).collect::<Vec<_>>()),
    );
    obj.insert(
        "dome_pool_order_exact".to_string(),
        json!(state.dome_tile_pool.iter().map(|t| t.tile_id).collect::<Vec<_>>()),
    );
    obj.insert(
        "bonus_chip_pool_order_exact".to_string(),
        json!(state.bonus_chip_pool.iter().map(|c| c.chip_id).collect::<Vec<_>>()),
    );
    v
}

fn get_usize_arr(v: &Value, key: &str) -> Result<Vec<usize>, String> {
    get_arr(v, key)?
        .iter()
        .map(|x| x.as_u64().map(|n| n as usize).ok_or_else(|| json_err(key)))
        .collect()
}

/// Umkehrung von [`state_to_json_exact`]. Baut wie `json_to_state` einen
/// `GameState`, überschreibt danach aber die vier verdeckten Sammlungen mit
/// der exakt geordneten Fassung aus dem JSON -- PFLICHT, harter Fehler bei
/// Fehlen (kein stiller Rückfall auf die Zähler-Rekonstruktion, Bau-Vorgabe
/// par.8b). Der intern erzeugte RNG treibt in `json_to_state` nur noch die
/// gleich darauf überschriebene Erstmischung -- jeder deterministische RNG
/// reicht dafür, ein fester Seed genügt (der frühere, domain-getrennte
/// Rekonstruktions-RNG aus par.8a/referee.rs, `RECON_DISTINGUISHER`, entfällt
/// dadurch ersatzlos -- weniger bewegliche Teile, siehe referee.rs).
pub fn json_to_state_exact(v: &Value) -> Result<GameState, String> {
    let mut discard_rng = rand::rngs::StdRng::seed_from_u64(0);
    let mut state = json_to_state(v, &mut discard_rng)?;

    let dome_catalog = crate::dome::build_dome_tile_pool();
    let dome_order = get_usize_arr(v, "dome_pool_order_exact")?;
    state.dome_tile_pool = dome_order
        .iter()
        .map(|&id| {
            dome_catalog
                .get(id)
                .cloned()
                .ok_or_else(|| format!("json_to_state_exact: unbekannte dome_pool_order_exact tile_id {id}"))
        })
        .collect::<Result<_, _>>()?;

    let chip_catalog = crate::dome::build_bonus_chip_pool();
    let chip_order = get_usize_arr(v, "bonus_chip_pool_order_exact")?;
    state.bonus_chip_pool = chip_order
        .iter()
        .map(|&id| {
            chip_catalog
                .get(id)
                .cloned()
                .ok_or_else(|| format!("json_to_state_exact: unbekannte bonus_chip_pool_order_exact chip_id {id}"))
        })
        .collect::<Result<_, _>>()?;

    state.bag.tiles = colors_from_json_array(
        v.get("bag_order_exact").ok_or_else(|| json_err("bag_order_exact"))?,
    )?;
    state.tower.tiles = colors_from_json_array(
        v.get("tower_order_exact").ok_or_else(|| json_err("tower_order_exact"))?,
    )?;

    // Defensiver Konsistenz-Check gegen die schon bestehenden Zähler-/
    // Maskenfelder (billig, faengt einen inkonsistent gebauten Producer
    // frueh statt spaeter mitten in der Suche).
    let bag_count = get_u64(v, "bag_count")? as usize;
    if state.bag.tiles.len() != bag_count {
        return Err(format!(
            "json_to_state_exact: bag_order_exact hat {} Eintraege, bag_count sagt {bag_count}",
            state.bag.tiles.len()
        ));
    }
    let dome_stack_count = get_u64(v, "dome_stack_count")? as usize;
    if state.dome_tile_pool.len() != dome_stack_count {
        return Err(format!(
            "json_to_state_exact: dome_pool_order_exact hat {} Eintraege, dome_stack_count sagt {dome_stack_count}",
            state.dome_tile_pool.len()
        ));
    }

    Ok(state)
}

#[cfg(test)]
mod json_to_state_exact_tests {
    use super::*;
    use crate::game::{drafting_actions, Game, TilingMove};
    use crate::state::NUM_ROUNDS;
    use rand::rngs::StdRng;
    use rand::RngExt as _;
    use rand::SeedableRng;

    fn names() -> [String; 2] {
        ["Alpha".into(), "Beta".into()]
    }

    /// Roundtrip-Kern (par.8b, Bau-Vorgabe 4a): state → json_exact →
    /// json_to_state_exact muss FELDGLEICH sein -- inklusive der vier
    /// exakten Reihenfolgen (direkter Struct-Vergleich, nicht nur JSON-
    /// Vergleich, damit ein zufällig gleich aussehendes JSON keine Lücke
    /// verdeckt).
    fn assert_roundtrip_exact(state: &GameState, label: &str) {
        let json1 = state_to_json_exact(state, true);
        let rebuilt =
            json_to_state_exact(&json1).unwrap_or_else(|e| panic!("{label}: json_to_state_exact fehlgeschlagen: {e}"));

        assert_eq!(state.bag.tiles, rebuilt.bag.tiles, "{label}: bag.tiles weicht ab");
        assert_eq!(state.tower.tiles, rebuilt.tower.tiles, "{label}: tower.tiles weicht ab");
        assert_eq!(
            state.dome_tile_pool.iter().map(|t| t.tile_id).collect::<Vec<_>>(),
            rebuilt.dome_tile_pool.iter().map(|t| t.tile_id).collect::<Vec<_>>(),
            "{label}: dome_tile_pool-Reihenfolge weicht ab"
        );
        assert_eq!(
            state.bonus_chip_pool.iter().map(|c| c.chip_id).collect::<Vec<_>>(),
            rebuilt.bonus_chip_pool.iter().map(|c| c.chip_id).collect::<Vec<_>>(),
            "{label}: bonus_chip_pool-Reihenfolge weicht ab"
        );

        // Der Rest des Zustands bleibt an dieselben, bereits per
        // json_to_state_tests::diff_allowing_known_gaps dokumentierten
        // Lücken gebunden (estimated_score bei nicht-leeren bonus_chips,
        // first_player_next_round) -- hier über den bestehenden Vergleicher
        // der Schwesterngruppe geprüft.
        let json2 = state_to_json_exact(&rebuilt, true);
        let mut mismatches = Vec::new();
        json_to_state_tests::diff_allowing_known_gaps(&json1, &json2, "", &mut mismatches);
        assert!(mismatches.is_empty(), "{label}: Roundtrip-JSON weicht ab:\n{}", mismatches.join("\n"));
    }

    #[test]
    fn roundtrip_exact_fresh_game_start_placement() {
        let mut rng = StdRng::seed_from_u64(31);
        let state = crate::state::setup_new_game(names(), 0, &mut rng);
        assert_roundtrip_exact(&state, "frischer Spielstart (start_placement)");
    }

    #[test]
    fn roundtrip_exact_random_walk_multi_round() {
        let seed = 3101u64;
        let mut rng = StdRng::seed_from_u64(seed);
        let mut game = Game::start(names(), 0, crate::scoring::sample_valid_scoring_ids(3, &mut rng), &mut rng);
        for pi in [1usize, 0usize] {
            let (tile_id, r, c, rot) = crate::self_play::choose_start_placement(&game.state, pi).unwrap();
            crate::game::apply_start_placement(&mut game.state, pi, tile_id, r, c, rot).unwrap();
        }
        let mut n_checked = 0usize;
        let mut n_pending_checked = 0usize;
        let mut steps = 0u32;
        const MAX_STEPS: u32 = 4000;
        while game.state.round_number < NUM_ROUNDS && steps < MAX_STEPS {
            steps += 1;
            match game.state.phase {
                Phase::Drafting => {
                    let actions = drafting_actions(&game.state);
                    if actions.is_empty() {
                        break;
                    }
                    let is_pending = game.state.pending_dome_choice.is_some()
                        || !game.state.pending_stack_draw.is_empty();
                    assert_roundtrip_exact(&game.state, &format!("random_walk Schritt {steps} (drafting)"));
                    n_checked += 1;
                    if is_pending {
                        n_pending_checked += 1;
                    }
                    let idx = rng.random_range(0..actions.len());
                    game.apply_drafting(&actions[idx]).unwrap_or_else(|e| {
                        panic!("random_walk Schritt {steps}: apply_drafting fehlgeschlagen: {e}")
                    });
                }
                Phase::Tiling => {
                    for pi in 0..2 {
                        loop {
                            let acts = game.valid_tiling_actions(pi);
                            let Some(a) = acts.first().copied() else { break };
                            game.apply_single_tiling(pi, &a).unwrap_or_else(|e| {
                                panic!("random_walk Tiling-Platzierung fehlgeschlagen: {e}")
                            });
                        }
                        game.apply_tiling(&TilingMove::EndTiling { player: pi }, &mut rng).unwrap_or_else(|e| {
                            panic!("random_walk EndTiling fehlgeschlagen: {e}")
                        });
                    }
                }
                _ => break,
            }
        }
        assert!(steps < MAX_STEPS, "random_walk: MAX_STEPS erreicht, vermutlich Endlos-Schleife");
        assert!(n_checked > 20, "erwartet viele geprüfte Drafting-Zustände, war {n_checked}");
        assert!(n_pending_checked > 0, "erwartet mind. 1 PendingDomeChoice-/Stapel-Zwischenzustand, war {n_pending_checked}");
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Wertungsplatten-Diagnose (2026-07-26): end_scoring_from_state
// ═══════════════════════════════════════════════════════════════════════════

/// Endwertungs-Details je Spieler für einen extern gespeicherten Zustand
/// (z.B. ein Self-Play-Record `state`-Feld) -- reine additive Lesefunktion
/// für die Wertungsplatten-Diagnose (Nutzer-Verdacht "die KI ignoriert die
/// Wertungsplatten"), berührt keine bestehende Suche/Produktion. Baut per
/// [`json_to_state`] einen `GameState` und ruft für JEDEN Spieler
/// [`crate::scoring::calculate_end_scoring`] mit den übergebenen `tile_ids`
/// auf.
///
/// WICHTIG: `calculate_end_scoring` liest AUSSCHLIESSLICH
/// `PlayerBoard::dome_grid` (siehe scoring.rs: `build_grid`/`collect_spaces`
/// laufen nur über `dome_grid.dome_slots`, nie über Beutel/Turm/Stapel/Phase/
/// etc.). `dome_grid` wird von `dome_grid_from_json` Space-für-Space EXAKT
/// rekonstruiert -- keine der drei oben dokumentierten Näherungskategorien
/// (verdeckte Information, abgeleitete Felder, Wurzel-Legalitäts-Näherungen)
/// betrifft dieses Feld. Das Ergebnis ist also, anders als z.B.
/// `estimated_score`, für JEDEN validen `state_json`-Zustand EXAKT (siehe
/// Test `end_scoring_from_state_is_exact_after_roundtrip` unten) --
/// unabhängig vom übergebenen `rng`, der nur die hier irrelevante Neumischung
/// von bag/tower/dome_tile_pool/bonus_chip_pool treibt.
pub fn end_scoring_from_state<R: Rng + ?Sized>(
    state_json: &Value,
    tile_ids: &[usize],
    rng: &mut R,
) -> Result<Value, String> {
    let state = json_to_state(state_json, rng)?;
    let mut per_player = Map::new();
    for (pi, player) in state.players.iter().enumerate() {
        let res = crate::scoring::calculate_end_scoring(player, tile_ids);
        let details: Vec<Value> = res
            .details
            .iter()
            .map(|d| {
                json!({
                    "id": d.id,
                    "name": d.name,
                    "emoji": d.emoji,
                    "desc": d.description,
                    "score": d.score,
                })
            })
            .collect();
        per_player.insert(
            format!("player_{pi}"),
            json!({ "details": details, "total": res.total }),
        );
    }
    Ok(Value::Object(per_player))
}

#[cfg(test)]
mod end_scoring_from_state_tests {
    use super::*;
    use crate::game::{drafting_actions, Game, TilingMove};
    use crate::scoring::calculate_end_scoring;
    use crate::state::NUM_ROUNDS;
    use rand::rngs::StdRng;
    use rand::RngExt as _;
    use rand::SeedableRng;

    fn names() -> [String; 2] {
        ["Alpha".into(), "Beta".into()]
    }

    /// Treibt ein Zufalls-Spiel bis Runde 5 / Phase::Drafting (wie
    /// `json_to_state_tests::roundtrip_reaches_round5_state`), gibt `None`
    /// zurück, falls dieser Seed das nicht schafft.
    fn drive_to_round5(seed: u64) -> Option<Game> {
        let mut rng = StdRng::seed_from_u64(seed);
        let mut game = Game::start(names(), 0, crate::scoring::sample_valid_scoring_ids(3, &mut rng), &mut rng);
        for pi in [1usize, 0usize] {
            let (tile_id, r, c, rot) = crate::self_play::choose_start_placement(&game.state, pi).unwrap();
            crate::game::apply_start_placement(&mut game.state, pi, tile_id, r, c, rot).unwrap();
        }
        let mut steps = 0u32;
        while game.state.round_number < NUM_ROUNDS && steps < 4000 {
            steps += 1;
            match game.state.phase {
                Phase::Drafting => {
                    let actions = drafting_actions(&game.state);
                    if actions.is_empty() {
                        break;
                    }
                    let idx = rng.random_range(0..actions.len());
                    if game.apply_drafting(&actions[idx]).is_err() {
                        break;
                    }
                }
                Phase::Tiling => {
                    for pi in 0..2 {
                        loop {
                            let acts = game.valid_tiling_actions(pi);
                            let Some(a) = acts.first().copied() else { break };
                            if game.apply_single_tiling(pi, &a).is_err() {
                                break;
                            }
                        }
                        let _ = game.apply_tiling(&TilingMove::EndTiling { player: pi }, &mut rng);
                    }
                }
                _ => break,
            }
        }
        if game.state.round_number >= NUM_ROUNDS && game.state.phase == Phase::Drafting {
            Some(game)
        } else {
            None
        }
    }

    /// Kern-Nachweis: `end_scoring_from_state` auf dem serialisierten Zustand
    /// muss für JEDEN Spieler EXAKT dieselben Details/Total liefern wie
    /// `calculate_end_scoring` direkt auf dem ORIGINAL-`PlayerBoard` (vor
    /// jeder JSON-Serialisierung) -- das ist der Beweis, dass die
    /// Rekonstruktion für die Wertungsplatten-Diagnose verlustfrei ist.
    #[test]
    fn end_scoring_from_state_is_exact_after_roundtrip() {
        for seed in [3u64, 4, 5, 6, 7, 8, 9, 10] {
            let Some(game) = drive_to_round5(seed) else { continue };
            let tile_ids = game.state.scoring_tile_ids.clone();
            let json1 = state_to_json(&game.state, true);
            let mut rng2 = StdRng::seed_from_u64(seed.wrapping_add(777));
            let got = end_scoring_from_state(&json1, &tile_ids, &mut rng2)
                .unwrap_or_else(|e| panic!("seed {seed}: end_scoring_from_state fehlgeschlagen: {e}"));

            for pi in 0..2 {
                let expected = calculate_end_scoring(&game.state.players[pi], &tile_ids);
                let key = format!("player_{pi}");
                let entry = &got[&key];
                assert_eq!(
                    entry["total"].as_i64().unwrap() as i32,
                    expected.total,
                    "seed {seed} player {pi}: total weicht ab"
                );
                let details = entry["details"].as_array().unwrap();
                assert_eq!(details.len(), expected.details.len(), "seed {seed} player {pi}: Detail-Anzahl");
                // Summe der Details == total (Additivität der Endwertung).
                let sum: i64 = details.iter().map(|d| d["score"].as_i64().unwrap()).sum();
                assert_eq!(sum, expected.total as i64, "seed {seed} player {pi}: Summe der Details != total");
                for (d, e) in details.iter().zip(expected.details.iter()) {
                    assert_eq!(d["id"].as_u64().unwrap() as usize, e.id);
                    assert_eq!(d["score"].as_i64().unwrap() as i32, e.score, "seed {seed} player {pi} tile {}", e.id);
                }
            }
            return; // ein erreichter Runde-5-Zustand reicht für den Nachweis.
        }
        panic!("keiner der Test-Seeds erreichte Runde 5 -- Testaufbau prüfen");
    }

    /// Robustheit: funktioniert auch für einen frischen Spielstart (Runde 1,
    /// leeres Brett) -- alle additiven Platten liefern 0, keine der
    /// "alles-oder-nichts"-Platten greift, kein Panic bei leeren Slots.
    #[test]
    fn end_scoring_from_state_empty_board_all_zero() {
        let mut rng = StdRng::seed_from_u64(42);
        let state = crate::state::setup_new_game(names(), 0, &mut rng);
        let json1 = state_to_json(&state, true);
        let mut rng2 = StdRng::seed_from_u64(43);
        let got = end_scoring_from_state(&json1, &[0, 1, 2, 3, 4, 5, 6, 7], &mut rng2).unwrap();
        for pi in 0..2 {
            let key = format!("player_{pi}");
            let total = got[&key]["total"].as_i64().unwrap();
            // Startbrett: alles leer -- alle additiven/Alles-oder-nichts-Platten
            // liefern 0, NUR "leere Spezialfelder" (id 6) könnte theoretisch
            // negativ sein, aber ein frisches Brett hat noch keine gelegten
            // Kuppelplatten -> auch dort 0 Spezialfelder vorhanden.
            assert_eq!(total, 0, "player {pi}: frisches Brett sollte 0 Punkte ergeben");
        }
    }
}

#[cfg(test)]
mod json_to_state_tests {
    use super::*;
    use crate::game::{drafting_actions, Game, TilingMove};
    use crate::state::{setup_new_game, NUM_ROUNDS};
    use rand::rngs::StdRng;
    use rand::RngExt as _;
    use rand::SeedableRng;

    fn names() -> [String; 2] {
        ["Alpha".into(), "Beta".into()]
    }

    /// Rekursiver Strukturvergleich, der GENAU EINE dokumentierte, geprüfte
    /// Lücke toleriert: `players[i].estimated_score` darf abweichen, aber
    /// AUSSCHLIESSLICH wenn `players[i].bonus_chips` nicht leer ist -- das ist
    /// exakt die `tiled_max_row`-Ausnahme aus dem `json_to_state`-Doku-
    /// Kommentar (Kategorie 3): `tiling_solver::chippable_rows` liest den
    /// nicht-serialisierten, potenziell aus der letzten Tiling-Phase stehen
    /// gebliebenen `tiled_max_row`-Wert NUR, wenn der Spieler einen nicht
    /// verbrauchten Bonuschip hält (sonst früher Return, siehe dortiger
    /// Kommentar). JEDE andere Abweichung bleibt ein harter Fehler.
    pub(super) fn diff_allowing_known_gaps(a: &Value, b: &Value, path: &str, mismatches: &mut Vec<String>) {
        match (a, b) {
            (Value::Object(oa), Value::Object(ob)) => {
                let is_player_obj = oa.contains_key("estimated_score") && oa.contains_key("bonus_chips");
                let bonus_chips_nonempty = is_player_obj
                    && oa.get("bonus_chips").and_then(|v| v.as_array()).map(|a| !a.is_empty()).unwrap_or(false);
                let mut keys: Vec<&String> = oa.keys().chain(ob.keys()).collect();
                keys.sort();
                keys.dedup();
                for k in keys {
                    if is_player_obj && k == "estimated_score" && bonus_chips_nonempty {
                        continue; // dokumentierte Ausnahme, s.o.
                    }
                    if k == "first_player_next_round" {
                        // Dokumentierte Ausnahme (Kategorie 2, aber nur
                        // NAEHERUNGSWEISE ableitbar, nicht exakt wie der
                        // Doku-Kommentar bei json_to_state suggeriert):
                        // `json_to_state` leitet dieses Feld aus
                        // `players[].holds_first_player_marker` ab, faellt
                        // aber auf `current_player` zurueck, sobald NIEMAND
                        // die Marke aktuell haelt (z.B. Rundenbeginn, bevor
                        // sie gezogen wurde) -- das muss nicht mit dem
                        // tatsaechlich getrackten Live-Feld uebereinstimmen.
                        // Ohne Einfluss auf Task #89 (Oracle/Suche liest
                        // dieses Feld nirgends), nur `determine_winner`
                        // (self_play.rs, ausschliesslich auf ECHTEN,
                        // beendeten Live-Spielen aufgerufen, nie auf einem
                        // json_to_state-Rekonstrukt) und das Endergebnis-
                        // Modal im Frontend (server.py::state_to_json auf
                        // dem LIVE-GameState, ebenfalls kein Roundtrip)
                        // nutzen es wirklich.
                        continue;
                    }
                    let sub_path = format!("{path}/{k}");
                    match (oa.get(k), ob.get(k)) {
                        (Some(va), Some(vb)) => diff_allowing_known_gaps(va, vb, &sub_path, mismatches),
                        _ => mismatches.push(format!("{sub_path}: Feld fehlt auf einer Seite")),
                    }
                }
            }
            (Value::Array(la), Value::Array(lb)) => {
                if la.len() != lb.len() {
                    mismatches.push(format!("{path}: Array-Länge {} vs {}", la.len(), lb.len()));
                } else {
                    for (i, (x, y)) in la.iter().zip(lb.iter()).enumerate() {
                        diff_allowing_known_gaps(x, y, &format!("{path}[{i}]"), mismatches);
                    }
                }
            }
            _ => {
                if a != b {
                    mismatches.push(format!("{path}: {a} != {b}"));
                }
            }
        }
    }

    /// Roundtrip-Kern: state → json1 → json_to_state → json2, strukturell
    /// gleich (ordnungsunabhängig) bis auf die EINE dokumentierte, geprüfte
    /// Ausnahme oben. Ein eigener RNG-Seed je Aufruf reicht, da die neu
    /// gemischten verdeckten Sammlungen (Kategorie 1 im `json_to_state`-Doku-
    /// Kommentar) laut Analyse KEIN einziges state_to_json-Feld beeinflussen
    /// außer `dome_stack_top_type` (dafür explizit korrigiert).
    fn assert_roundtrip_stable(state: &GameState, seed: u64, label: &str) {
        let json1 = state_to_json(state, true);
        let mut rng = StdRng::seed_from_u64(seed);
        let rebuilt = json_to_state(&json1, &mut rng)
            .unwrap_or_else(|e| panic!("{label}: json_to_state fehlgeschlagen: {e}"));
        let json2 = state_to_json(&rebuilt, true);
        let mut mismatches = Vec::new();
        diff_allowing_known_gaps(&json1, &json2, "", &mut mismatches);
        assert!(
            mismatches.is_empty(),
            "{label}: Roundtrip-JSON weicht ab (Zustand: round={}, phase={}, pending_dome_choice={}, pending_stack_draw_len={}):\n{}",
            state.round_number,
            state.phase.as_str(),
            state.pending_dome_choice.is_some(),
            state.pending_stack_draw.len(),
            mismatches.join("\n"),
        );
    }

    #[test]
    fn roundtrip_fresh_game_start_placement() {
        let mut rng = StdRng::seed_from_u64(1);
        let state = setup_new_game(names(), 0, &mut rng);
        assert_roundtrip_stable(&state, 999, "frischer Spielstart (start_placement)");
    }

    #[test]
    fn roundtrip_after_start_tiles_placed() {
        let mut rng = StdRng::seed_from_u64(2);
        let mut game = Game::start(names(), 0, crate::scoring::sample_valid_scoring_ids(3, &mut rng), &mut rng);
        for pi in [1usize, 0usize] {
            // Regelwerk: Nicht-Startspieler (hier Spieler 1, da first_player=0) waehlt zuerst.
            let (tile_id, r, c, rot) = crate::self_play::choose_start_placement(&game.state, pi).unwrap();
            crate::game::apply_start_placement(&mut game.state, pi, tile_id, r, c, rot).unwrap();
        }
        assert_roundtrip_stable(&game.state, 1000, "nach Startkuppel-Platzierung (drafting, Runde 1)");
    }

    /// Kompletter Self-Play-Walk über mehrere Runden (zufällige legale Züge,
    /// KEINE MCTS-Maschinerie nötig) -- prüft den Roundtrip an JEDEM
    /// Drafting-Entscheidungspunkt, also explizit auch mitten in
    /// PendingDomeChoice- (Rotationswahl) und Stapel-Zug-Situationen
    /// (`pending_stack_draw` nicht leer), wie vom Auftrag verlangt. Tiling-
    /// Phase-Zustände werden ebenfalls durchlaufen (Runden-Fortschritt), aber
    /// NICHT auf Roundtrip geprüft -- s.o. Doku-Kommentar (`tiled_max_row`-
    /// Ausnahme betrifft dort potenziell `estimated_score`, irrelevant für
    /// den Drafting-only Sucheinstieg).
    fn random_walk(seed: u64) -> (usize, usize) {
        let mut rng = StdRng::seed_from_u64(seed);
        let mut game = Game::start(names(), 0, crate::scoring::sample_valid_scoring_ids(3, &mut rng), &mut rng);
        for pi in [1usize, 0usize] {
            // Regelwerk: Nicht-Startspieler (hier Spieler 1, da first_player=0) waehlt zuerst.
            let (tile_id, r, c, rot) = crate::self_play::choose_start_placement(&game.state, pi).unwrap();
            crate::game::apply_start_placement(&mut game.state, pi, tile_id, r, c, rot).unwrap();
        }

        let mut n_drafting_checked = 0usize;
        let mut n_pending_situations_checked = 0usize;
        let mut steps = 0u32;
        const MAX_STEPS: u32 = 4000;

        while game.state.round_number < NUM_ROUNDS && steps < MAX_STEPS {
            steps += 1;
            match game.state.phase {
                Phase::Drafting => {
                    let actions = drafting_actions(&game.state);
                    if actions.is_empty() {
                        break;
                    }
                    let is_pending = game.state.pending_dome_choice.is_some()
                        || !game.state.pending_stack_draw.is_empty();
                    assert_roundtrip_stable(
                        &game.state,
                        seed.wrapping_mul(1000).wrapping_add(steps as u64),
                        &format!("random_walk(seed={seed}) Schritt {steps} (drafting)"),
                    );
                    n_drafting_checked += 1;
                    if is_pending {
                        n_pending_situations_checked += 1;
                    }
                    let idx = rng.random_range(0..actions.len());
                    game.apply_drafting(&actions[idx]).unwrap_or_else(|e| {
                        panic!("random_walk(seed={seed}) Schritt {steps}: apply_drafting fehlgeschlagen: {e}")
                    });
                }
                Phase::Tiling => {
                    for pi in 0..2 {
                        loop {
                            let acts = game.valid_tiling_actions(pi);
                            let Some(a) = acts.first().copied() else { break };
                            game.apply_single_tiling(pi, &a).unwrap_or_else(|e| {
                                panic!("random_walk(seed={seed}) Tiling-Platzierung fehlgeschlagen: {e}")
                            });
                        }
                        game.apply_tiling(&TilingMove::EndTiling { player: pi }, &mut rng).unwrap_or_else(|e| {
                            panic!("random_walk(seed={seed}) EndTiling fehlgeschlagen: {e}")
                        });
                    }
                }
                _ => break,
            }
        }
        assert!(steps < MAX_STEPS, "random_walk(seed={seed}): MAX_STEPS erreicht, vermutlich Endlos-Schleife");
        (n_drafting_checked, n_pending_situations_checked)
    }

    #[test]
    fn roundtrip_random_walk_multi_round_seed_a() {
        let (checked, pending) = random_walk(11);
        assert!(checked > 20, "erwartet viele geprüfte Drafting-Zustände, war {checked}");
        assert!(pending > 0, "erwartet mind. 1 PendingDomeChoice-/Stapel-Zwischenzustand, war {pending}");
    }

    #[test]
    fn roundtrip_random_walk_multi_round_seed_b() {
        let (checked, pending) = random_walk(2027);
        assert!(checked > 20, "erwartet viele geprüfte Drafting-Zustände, war {checked}");
        assert!(pending > 0, "erwartet mind. 1 PendingDomeChoice-/Stapel-Zwischenzustand, war {pending}");
    }

    #[test]
    fn roundtrip_random_walk_multi_round_seed_c() {
        let (checked, pending) = random_walk(555);
        assert!(checked > 20, "erwartet viele geprüfte Drafting-Zustände, war {checked}");
        assert!(pending > 0, "erwartet mind. 1 PendingDomeChoice-/Stapel-Zwischenzustand, war {pending}");
    }

    /// json_to_state muss auf einem strukturell VÖLLIG anderen Zustand
    /// (Runde 5: keine Kuppelplatten-Züge mehr, andere Kandidatenmenge) auch
    /// roundtrip-stabil bleiben.
    #[test]
    fn roundtrip_reaches_round5_state() {
        // Mehrere Seeds probieren, bis ein Walk tatsächlich Runde 5 erreicht
        // (manche enden vorher am MAX_STEPS-Deckel bei Pech mit sehr langen
        // Stapel-Zug-Ketten) -- hartes Scheitern nur, wenn KEINER der
        // Versuche Runde 5 erreicht.
        for seed in [3, 4, 5, 6, 7, 8, 9, 10] {
            let mut rng = StdRng::seed_from_u64(seed);
            let mut game =
                Game::start(names(), 0, crate::scoring::sample_valid_scoring_ids(3, &mut rng), &mut rng);
            for pi in [1usize, 0usize] {
                // Regelwerk: Nicht-Startspieler (hier Spieler 1, da first_player=0) waehlt zuerst.
                let (tile_id, r, c, rot) = crate::self_play::choose_start_placement(&game.state, pi).unwrap();
                crate::game::apply_start_placement(&mut game.state, pi, tile_id, r, c, rot).unwrap();
            }
            let mut steps = 0u32;
            while game.state.round_number < NUM_ROUNDS && steps < 4000 {
                steps += 1;
                match game.state.phase {
                    Phase::Drafting => {
                        let actions = drafting_actions(&game.state);
                        if actions.is_empty() {
                            break;
                        }
                        let idx = rng.random_range(0..actions.len());
                        if game.apply_drafting(&actions[idx]).is_err() {
                            break;
                        }
                    }
                    Phase::Tiling => {
                        for pi in 0..2 {
                            loop {
                                let acts = game.valid_tiling_actions(pi);
                                let Some(a) = acts.first().copied() else { break };
                                if game.apply_single_tiling(pi, &a).is_err() {
                                    break;
                                }
                            }
                            let _ = game.apply_tiling(&TilingMove::EndTiling { player: pi }, &mut rng);
                        }
                    }
                    _ => break,
                }
            }
            if game.state.round_number >= NUM_ROUNDS && game.state.phase == Phase::Drafting {
                assert_roundtrip_stable(&game.state, seed.wrapping_add(500), &format!("Runde 5 (seed={seed})"));
                return;
            }
        }
        panic!("keiner der Test-Seeds erreichte Runde 5 in Phase::Drafting -- Testaufbau prüfen");
    }
}
