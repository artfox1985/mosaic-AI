//! Zugausführung (Drafting) — Port von engine/execution.py.
//!
//! Setzt voraus, dass der Move bereits validiert wurde. Loggt jeden Zug
//! ausführlich (wie die Python-Engine) — der Spiel-Log wird zum Debuggen
//! gebraucht (Steinzüge, Mond-Stapel, Chip-Aufdeckungen, Marker, Strafleiste).

use crate::factory::Factory;
use crate::moves::{Move, TakeSource};
use crate::state::GameState;
use crate::tile::TileColor;

pub fn execute_move(state: &mut GameState, m: &Move) {
    if m.is_global_moon_take() {
        execute_moon_take(state, m.take.color, m.place.row_index);
        return;
    }

    let (taken, got_marker, pending) = execute_take(state, m);
    if got_marker {
        apply_first_player_marker(state);
    }

    // Aktions-Log VOR dem Place — danach Füllstand in denselben Eintrag patchen,
    // damit etwaige Strafleisten-Warnungen aus execute_place danach erscheinen.
    let pi = state.current_player;
    let name = state.players[pi].name.clone();
    let dest = dest_label(m.place.row_index);
    let src = src_label(m);
    state.log_event(format!(
        "☀️  {name}: {}× {} von {} → {}",
        taken.len(),
        m.take.color.value(),
        src,
        dest
    ));
    let idx = state.log.len() - 1;

    execute_place(state, &taken, m.place.row_index);

    if m.place.row_index >= 0 {
        let row = &state.players[pi].pattern_lines[m.place.row_index as usize];
        let fill = format!(" [{}/{}]", row.tiles.len(), row.capacity());
        state.log[idx].push_str(&fill);
    }

    for line in pending {
        state.log_event(line);
    }
}

fn find_factory_idx(state: &GameState, factory_id: usize) -> usize {
    state
        .factories
        .iter()
        .position(|f| f.factory_id == factory_id)
        .expect("Fabrik nicht gefunden")
}

/// Deckt das Bonusplättchen auf, falls die Fabrik jetzt komplett leer ist.
/// Gibt true zurück, wenn gerade aufgedeckt wurde.
fn reveal_chip_if_empty(state: &mut GameState, fidx: usize) -> bool {
    let f = &mut state.factories[fidx];
    if f.is_fully_empty() && f.bonus_chip.is_some() && !f.bonus_chip_revealed {
        f.bonus_chip_revealed = true;
        return true;
    }
    false
}

/// Formatiert alle Mondstapel einer Fabrik als lesbaren String ([unten → oben]).
fn format_moon_stacks(f: &Factory) -> String {
    if f.moon_stacks.is_empty() {
        return "leer".into();
    }
    let stacks: Vec<String> = f
        .moon_stacks
        .iter()
        .map(|stack| match stack.last() {
            None => "(?)".into(),
            Some(top) if stack.len() > 1 => {
                let rest: Vec<&str> = stack[..stack.len() - 1].iter().map(|c| c.value()).collect();
                format!("({}→{})", rest.join(", "), top.value())
            }
            Some(top) => format!("({})", top.value()),
        })
        .collect();
    stacks.join(" | ")
}

fn dest_label(row_index: i32) -> String {
    if row_index >= 0 {
        format!("Reihe {}", row_index + 1)
    } else {
        "Strafleiste".into()
    }
}

fn src_label(m: &Move) -> String {
    match m.take.factory_id {
        Some(id) => format!("F{id}"),
        None => "GF".into(),
    }
}

/// Führt den Take-Teil aus. Gibt (genommene Steine, Marker, ausstehende Logs)
/// zurück — die Logs (Mond-Stapel, Chip-Aufdeckung) werden nach dem Aktions-Log
/// geschrieben.
fn execute_take(state: &mut GameState, m: &Move) -> (Vec<TileColor>, bool, Vec<String>) {
    let mut pending: Vec<String> = Vec::new();
    match m.take.source {
        TakeSource::SmallFactorySun => {
            let fid = m.take.factory_id.expect("small sun braucht factory_id");
            let fidx = find_factory_idx(state, fid);
            let (taken, remaining) = state.factories[fidx]
                .take_from_sun(m.take.color)
                .expect("validierter Zug");
            if !remaining.is_empty() {
                state.factories[fidx].place_on_moon(m.take.moon_order.clone());
                pending.push(format!(
                    "🌙 F{fid} Mond-Stapel: {}",
                    format_moon_stacks(&state.factories[fidx])
                ));
            }
            if reveal_chip_if_empty(state, fidx) {
                pending.push(format!("🎴 F{fid}: Bonusplättchen aufgedeckt!"));
            }
            (taken, false, pending)
        }
        TakeSource::SmallFactoryMoon => {
            let fid = m.take.factory_id.expect("small moon braucht factory_id");
            let fidx = find_factory_idx(state, fid);
            let taken = state.factories[fidx]
                .take_from_moon(m.take.color)
                .expect("validierter Zug");
            pending.push(format!(
                "🌙 F{fid} Mond-Stapel nach Entnahme: {}",
                format_moon_stacks(&state.factories[fidx])
            ));
            if reveal_chip_if_empty(state, fidx) {
                pending.push(format!("🎴 F{fid}: Bonusplättchen aufgedeckt!"));
            }
            (taken, false, pending)
        }
        TakeSource::LargeFactorySun => {
            let (taken, remaining, marker) = state
                .large_factory
                .take_from_sun(m.take.color)
                .expect("validierter Zug");
            if !remaining.is_empty() {
                state.large_factory.add_to_moon(&remaining);
            }
            (taken, marker, pending)
        }
        TakeSource::LargeFactoryMoon => {
            let (taken, marker) = state
                .large_factory
                .take_from_moon(m.take.color)
                .expect("validierter Zug");
            (taken, marker, pending)
        }
    }
}

/// Aktion C: nimmt alle obersten Fliesen der Farbe vom Mondbereich ALLER
/// Manufakturen (klein + groß) gleichzeitig.
fn execute_moon_take(state: &mut GameState, color: TileColor, row_index: i32) {
    let mut taken: Vec<TileColor> = Vec::new();
    let mut sources: Vec<(String, usize)> = Vec::new();
    let mut pending: Vec<String> = Vec::new();

    let n_factories = state.factories.len();
    for fidx in 0..n_factories {
        if state.factories[fidx].moon_top_colors().contains(&color) {
            if let Ok(tiles) = state.factories[fidx].take_from_moon(color) {
                let c = tiles.len();
                taken.extend(tiles);
                if c > 0 {
                    sources.push((format!("F{}", state.factories[fidx].factory_id), c));
                }
            }
            pending.push(format!(
                "🌙 F{} Mond-Stapel: {}",
                state.factories[fidx].factory_id,
                format_moon_stacks(&state.factories[fidx])
            ));
            if reveal_chip_if_empty(state, fidx) {
                pending.push(format!(
                    "🎴 F{}: Bonusplättchen aufgedeckt!",
                    state.factories[fidx].factory_id
                ));
            }
        }
    }

    let mut got_marker = false;
    if state.large_factory.moon_colors().contains(&color) {
        if let Ok((tiles, marker)) = state.large_factory.take_from_moon(color) {
            let c = tiles.len();
            taken.extend(tiles);
            got_marker = marker;
            if c > 0 {
                sources.push(("GF".into(), c));
            }
            let pool = &state.large_factory.moon_pool;
            let pool_display = if pool.is_empty() {
                "leer".into()
            } else {
                format!("({})", pool.iter().map(|c| c.value()).collect::<Vec<_>>().join(", "))
            };
            pending.push(format!("🌙 GF Moon-Pool: {pool_display}"));
        }
    }

    assert!(!taken.is_empty(), "Aktion C ohne Mond-Fliesen (validiert?)");

    if got_marker {
        apply_first_player_marker(state);
    }

    let pi = state.current_player;
    let name = state.players[pi].name.clone();
    let dest = dest_label(row_index);
    let src_detail = sources.iter().map(|(_, c)| c.to_string()).collect::<Vec<_>>().join("+");
    let src_labels = sources.iter().map(|(l, _)| l.clone()).collect::<Vec<_>>().join(", ");
    state.log_event(format!(
        "🌙 {name}: {} ({src_detail})× {} von {src_labels} → {dest}",
        taken.len(),
        color.value()
    ));
    let idx = state.log.len() - 1;

    execute_place(state, &taken, row_index);

    if row_index >= 0 {
        let row = &state.players[pi].pattern_lines[row_index as usize];
        state.log[idx].push_str(&format!(" [{}/{}]", row.tiles.len(), row.capacity()));
    }

    for line in pending {
        state.log_event(line);
    }
}

fn apply_first_player_marker(state: &mut GameState) {
    let pi = state.current_player;
    state.players[pi].holds_first_player_marker = true;
    state.first_player_next_round = pi;
    let (name, score) = {
        let p = &state.players[pi];
        (p.name.clone(), p.score)
    };
    state.log_event(format!(
        "🏁 {name}: Startspielerstein genommen (−2 Pkt am Rundenende → aktuell {score} Pkt)"
    ));
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
    let before = state.players[pi].broken_tiles.len();
    let to_tower = state.players[pi].add_broken(tiles);
    let after = state.players[pi].broken_tiles.len();

    if after > before {
        let pen_vals = [-1, -2, -3, -4];
        let sum: i32 = (before..after).map(|i| pen_vals[i]).sum();
        let name = state.players[pi].name.clone();
        state.log_event(format!(
            "⚠️  {name}: {}× auf Strafleiste (Slots {}–{}, {sum} Pkt Strafe)",
            tiles.len(),
            before + 1,
            after
        ));
    }
    if !to_tower.is_empty() {
        let name = state.players[pi].name.clone();
        let n = to_tower.len();
        state.tower.add(&to_tower);
        state.log_event(format!("⚠️  {name}: {n} Stein(e) → Turm (Strafleiste voll)"));
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
        let log_before = s.log.len();
        execute_move(&mut s, &m);

        assert!(s.factories[0].sun_is_empty());
        assert_eq!(s.factories[0].moon_is_empty(), remaining.is_empty());
        let row = &s.players[0].pattern_lines[5];
        assert_eq!(row.tiles.len(), n_color);
        assert_eq!(row.color, Some(color));
        // Aktions-Log wurde geschrieben (mind. 1 neuer Eintrag, mit Füllstand).
        assert!(s.log.len() > log_before);
        assert!(s.log.iter().any(|l| l.contains("☀️") && l.contains("F1")));
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
            place: PlaceAction { row_index: -1 },
        };
        execute_move(&mut s, &m);
        assert!(s.players[0].holds_first_player_marker);
        assert_eq!(s.first_player_next_round, 0);
        assert!(!s.players[0].broken_tiles.is_empty());
        assert!(s.large_factory.sun_is_empty());
        // Marker- und Strafleisten-Log vorhanden.
        assert!(s.log.iter().any(|l| l.contains("🏁")));
        assert!(s.log.iter().any(|l| l.contains("Strafleiste")));
    }
}
