//! Zugausführung (Drafting) — Port von engine/execution.py.
//!
//! Setzt voraus, dass der Move bereits validiert wurde. State-Mutation steht im
//! Vordergrund; ausführliche Log-Strings der Python-Version werden bewusst knapp
//! gehalten (für die Parität zählt der State, nicht der Log-Text).

use crate::moves::{Move, TakeSource};
use crate::state::GameState;
use crate::tile::TileColor;

pub fn execute_move(state: &mut GameState, m: &Move) {
    if m.is_global_moon_take() {
        execute_moon_take(state, m.take.color, m.place.row_index);
        return;
    }

    let (taken, got_marker) = execute_take(state, m);
    if got_marker {
        apply_first_player_marker(state);
    }
    execute_place(state, &taken, m.place.row_index);
}

fn find_factory_idx(state: &GameState, factory_id: usize) -> usize {
    state
        .factories
        .iter()
        .position(|f| f.factory_id == factory_id)
        .expect("Fabrik nicht gefunden")
}

fn reveal_chip_if_empty(state: &mut GameState, fidx: usize) {
    let f = &mut state.factories[fidx];
    if f.is_fully_empty() && f.bonus_chip.is_some() && !f.bonus_chip_revealed {
        f.bonus_chip_revealed = true;
    }
}

fn execute_take(state: &mut GameState, m: &Move) -> (Vec<TileColor>, bool) {
    match m.take.source {
        TakeSource::SmallFactorySun => {
            let fidx = find_factory_idx(state, m.take.factory_id.expect("small sun braucht factory_id"));
            let (taken, remaining) = state.factories[fidx]
                .take_from_sun(m.take.color)
                .expect("validierter Zug");
            if !remaining.is_empty() {
                // Spieler legt die übrigen Steine in gewählter Reihenfolge auf Moon.
                state.factories[fidx].place_on_moon(m.take.moon_order.clone());
            }
            reveal_chip_if_empty(state, fidx);
            (taken, false)
        }
        TakeSource::SmallFactoryMoon => {
            // factory_id Some = gezielter Moon-Zug einer Fabrik (Aktion C läuft separat).
            let fidx = find_factory_idx(state, m.take.factory_id.expect("small moon braucht factory_id"));
            let taken = state.factories[fidx]
                .take_from_moon(m.take.color)
                .expect("validierter Zug");
            reveal_chip_if_empty(state, fidx);
            (taken, false)
        }
        TakeSource::LargeFactorySun => {
            let (taken, remaining, marker) = state
                .large_factory
                .take_from_sun(m.take.color)
                .expect("validierter Zug");
            if !remaining.is_empty() {
                state.large_factory.add_to_moon(&remaining);
            }
            (taken, marker)
        }
        TakeSource::LargeFactoryMoon => {
            let (taken, marker) = state
                .large_factory
                .take_from_moon(m.take.color)
                .expect("validierter Zug");
            (taken, marker)
        }
    }
}

/// Aktion C: nimmt alle obersten Fliesen der Farbe vom Mondbereich ALLER
/// Manufakturen (klein + groß) gleichzeitig.
fn execute_moon_take(state: &mut GameState, color: TileColor, row_index: i32) {
    let mut taken: Vec<TileColor> = Vec::new();

    let n_factories = state.factories.len();
    for fidx in 0..n_factories {
        if state.factories[fidx].moon_top_colors().contains(&color) {
            if let Ok(tiles) = state.factories[fidx].take_from_moon(color) {
                taken.extend(tiles);
            }
            reveal_chip_if_empty(state, fidx);
        }
    }

    let mut got_marker = false;
    if state.large_factory.moon_colors().contains(&color) {
        if let Ok((tiles, marker)) = state.large_factory.take_from_moon(color) {
            taken.extend(tiles);
            got_marker = marker;
        }
    }

    assert!(!taken.is_empty(), "Aktion C ohne Mond-Fliesen (validiert?)");

    if got_marker {
        apply_first_player_marker(state);
    }
    execute_place(state, &taken, row_index);
}

fn apply_first_player_marker(state: &mut GameState) {
    let pi = state.current_player;
    state.players[pi].holds_first_player_marker = true;
    state.first_player_next_round = pi;
}

fn execute_place(state: &mut GameState, tiles: &[TileColor], row_index: i32) {
    let pi = state.current_player;
    if row_index == -1 {
        add_to_penalty(state, tiles);
        return;
    }
    let overflow = state.players[pi].pattern_lines[row_index as usize].add_tiles(tiles);
    if !overflow.is_empty() {
        add_to_penalty(state, &overflow);
    }
}

fn add_to_penalty(state: &mut GameState, tiles: &[TileColor]) {
    let pi = state.current_player;
    let to_tower = state.players[pi].add_broken(tiles);
    if !to_tower.is_empty() {
        state.tower.add(&to_tower);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::moves::{Move, PlaceAction, TakeAction, TakeSource};
    use crate::state::setup_new_game;
    use crate::validation::{generate_valid_moves, validate_move};
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    fn names() -> [String; 2] {
        ["P1".into(), "P2".into()]
    }

    #[test]
    fn generated_moves_are_all_valid_and_nonempty() {
        let mut rng = StdRng::seed_from_u64(99);
        let s = setup_new_game(names(), 0, &mut rng);
        let moves = generate_valid_moves(&s);
        assert!(!moves.is_empty());
        for m in &moves {
            assert!(validate_move(&s, m).is_none(), "ungültiger Zug generiert: {m:?}");
        }
    }

    #[test]
    fn small_sun_take_fills_row_and_moon() {
        let mut rng = StdRng::seed_from_u64(5);
        let mut s = setup_new_game(names(), 0, &mut rng);
        // Nimm eine konkrete Farbe von Fabrik 1 (sun) auf Reihe 5 (cap 6, nimmt alles auf).
        let f = &s.factories[0];
        let color = f.sun_colors()[0];
        let remaining: Vec<TileColor> =
            f.sun_tiles.iter().copied().filter(|&t| t != color).collect();
        let n_color = f.sun_tiles.iter().filter(|&&t| t == color).count();
        let m = Move {
            take: TakeAction {
                source: TakeSource::SmallFactorySun,
                color,
                factory_id: Some(1),
                moon_order: remaining.clone(),
            },
            place: PlaceAction { row_index: 5 },
        };
        assert!(validate_move(&s, &m).is_none());
        execute_move(&mut s, &m);

        assert!(s.factories[0].sun_is_empty());
        // übrige Steine als Moon-Stapel
        assert_eq!(s.factories[0].moon_is_empty(), remaining.is_empty());
        // Reihe 5 (Index 5) enthält n_color Steine der Farbe
        let row = &s.players[0].pattern_lines[5];
        assert_eq!(row.tiles.len(), n_color);
        assert_eq!(row.color, Some(color));
    }

    #[test]
    fn floor_placement_and_marker_from_large() {
        let mut rng = StdRng::seed_from_u64(11);
        let mut s = setup_new_game(names(), 0, &mut rng);
        let color = s.large_factory.sun_colors()[0];
        let m = Move {
            take: TakeAction {
                source: TakeSource::LargeFactorySun,
                color,
                factory_id: None,
                moon_order: Vec::new(),
            },
            place: PlaceAction { row_index: -1 }, // direkt auf Strafleiste
        };
        execute_move(&mut s, &m);
        assert!(s.players[0].holds_first_player_marker);
        assert_eq!(s.first_player_next_round, 0);
        assert!(!s.players[0].broken_tiles.is_empty());
        // Reste der großen Fabrik im Moon-Pool
        assert!(s.large_factory.sun_is_empty());
    }
}
