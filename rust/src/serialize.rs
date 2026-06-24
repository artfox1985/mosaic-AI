//! Serialisiert den GameState in das JSON-Format der API — Port von
//! engine/serializer.py. Das Frontend rendert nur; keine Spiellogik im Browser.

use serde_json::{json, Map, Value};

use crate::board::PlayerBoard;
use crate::dome::{BonusChip, DomeSpace, DomeTile, SpaceType};
use crate::evaluate::estimate_round_score;
use crate::factory::{Factory, LargeFactory};
use crate::round_end::{
    can_complete_row_with_chips, generate_tiling_actions, get_pending_tiling_rows,
    row_has_open_matching_slot,
};
use crate::state::{GameState, Phase};
use crate::validation::generate_valid_moves;

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

fn serialize_player(p: &PlayerBoard, round_number: u32) -> Value {
    let unused: Vec<&BonusChip> = p.bonus_chips.iter().collect();
    let unused_colors: Vec<&'static str> =
        unused.iter().flat_map(|c| c.colors.iter().map(|c| c.value())).collect();

    json!({
        "id": p.player_id,
        "name": p.name,
        "score": p.score,
        "pattern_lines": p.pattern_lines.iter().enumerate().map(|(i, row)| json!({
            "index": i,
            "capacity": row.capacity(),
            "tiles": row.tiles.iter().map(|t| t.value()).collect::<Vec<_>>(),
            "color": row.color.map(|c| c.value()),
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
        "estimated_score": estimate_round_score(p, true),
        "unused_chip_count": unused.len(),
        "unused_chip_colors": unused_colors,
    })
}

/// Vollständiges State-Dict für das Frontend.
pub fn state_to_json(state: &GameState, scoring_confirmed: bool) -> Value {
    let players: Vec<Value> = state
        .players
        .iter()
        .map(|p| serialize_player(p, state.round_number))
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
        "scoring_tile_ids": state.scoring_tile_ids,
        "can_pass": can_pass,
        "factories": state.factories.iter().map(serialize_factory).collect::<Vec<_>>(),
        "large_factory": serialize_large_factory(&state.large_factory),
        "moon_top_counts": Value::Object(moon_counts),
        "moon_top_colors": moon_colors,
        "dome_display": state.dome_display.iter().map(|t| serialize_dome_tile(Some(t))).collect::<Vec<_>>(),
        "dome_stack_count": state.dome_tile_pool.len(),
        "special_supply": state.special_supply.count(),
        "bag_count": state.bag.count(),
        "players": players,
        "log": state.log.iter().rev().take(30).rev().cloned().collect::<Vec<_>>(),
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

    // Stein-Züge (Aktion B + globaler Mond-Zug aus generate_valid_moves).
    for m in generate_valid_moves(state) {
        moves.push(json!({
            "type": "stone",
            "source": source_name(m.take.source),
            "factory_id": m.take.factory_id,
            "color": m.take.color.value(),
            "row": m.place.row_index,
            "moon_order": m.take.moon_order.iter().map(|t| t.value()).collect::<Vec<_>>(),
        }));
    }

    // Kuppelplatten aus offener Ablage.
    for m in crate::game::generate_dome_moves(state) {
        moves.push(json!({
            "type": "dome_display",
            "tile_id": m.dome_tile_id,
            "slot_row": m.slot_row,
            "slot_col": m.slot_col,
            "rotation": m.rotation,
        }));
    }

    // Aktion A: verdeckt vom Stapel ziehen.
    let p = &state.players[state.current_player];
    if !p.start_tile_pending
        && p.can_place_dome_tile(state.round_number)
        && !state.dome_tile_pool.is_empty()
        && state.round_number < 5
        && !p.has_used_all_tokens(state.round_number)
    {
        moves.push(json!({ "type": "dome_stack" }));
    }

    // Bonusplättchen.
    for m in crate::game::generate_bonus_chip_moves(state) {
        moves.push(json!({ "type": "bonus_chip", "factory_id": m.factory_id }));
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
