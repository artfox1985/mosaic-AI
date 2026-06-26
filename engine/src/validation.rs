//! Zugvalidierung + Generierung gültiger Züge — Port von engine/validation.py.

use crate::factory::Factory;
use crate::moves::{Move, PlaceAction, TakeAction, TakeSource};
use crate::state::GameState;
use crate::tile::TileColor;

/// Reihen-Indizes für Platzierung: 0..5 plus -1 (Strafleiste).
const ROW_INDICES: [i32; 7] = [0, 1, 2, 3, 4, 5, -1];

pub fn validate_move(state: &GameState, m: &Move) -> Option<String> {
    if let Some(e) = validate_take(state, &m.take) {
        return Some(e);
    }
    validate_place(state, m.take.color, m.place.row_index)
}

fn get_small_factory<'a>(state: &'a GameState, factory_id: usize) -> Option<&'a Factory> {
    state.factories.iter().find(|f| f.factory_id == factory_id)
}

fn validate_take(state: &GameState, take: &TakeAction) -> Option<String> {
    match take.source {
        TakeSource::SmallFactorySun => validate_small_sun(state, take),
        TakeSource::SmallFactoryMoon => validate_small_moon(state, take),
        TakeSource::LargeFactorySun => validate_large_sun(state, take),
        TakeSource::LargeFactoryMoon => validate_large_moon(state, take),
    }
}

fn validate_small_sun(state: &GameState, take: &TakeAction) -> Option<String> {
    let fid = take.factory_id?;
    let f = match get_small_factory(state, fid) {
        Some(f) => f,
        None => return Some(format!("Fabrik {fid} nicht gefunden.")),
    };
    if f.sun_is_empty() {
        return Some(format!("Fabrik {fid}: Sun-Seite ist leer."));
    }
    if !f.sun_colors().contains(&take.color) {
        return Some(format!(
            "Fabrik {fid}: Farbe {} nicht auf Sun-Seite.",
            take.color.value()
        ));
    }
    // moon_order muss genau die übrigen Steine enthalten (als Multiset).
    let mut remaining: Vec<TileColor> =
        f.sun_tiles.iter().copied().filter(|&t| t != take.color).collect();
    let mut order = take.moon_order.clone();
    remaining.sort_by_key(|c| c.value());
    order.sort_by_key(|c| c.value());
    if order != remaining {
        return Some("moon_order stimmt nicht mit übrigen Steinen überein.".into());
    }
    None
}

fn validate_small_moon(state: &GameState, take: &TakeAction) -> Option<String> {
    let fid = match take.factory_id {
        Some(id) => id,
        None => return None, // Aktion C wird über validate_moon_take geprüft
    };
    let f = match get_small_factory(state, fid) {
        Some(f) => f,
        None => return Some(format!("Fabrik {fid} nicht gefunden.")),
    };
    if f.moon_is_empty() {
        return Some(format!("Fabrik {fid}: Moon-Seite ist leer."));
    }
    if !f.moon_top_colors().contains(&take.color) {
        return Some(format!(
            "Fabrik {fid}: Farbe {} liegt nicht oben auf Moon-Stapeln.",
            take.color.value()
        ));
    }
    None
}

fn validate_large_sun(state: &GameState, take: &TakeAction) -> Option<String> {
    let lf = &state.large_factory;
    if lf.sun_is_empty() {
        return Some("Große Fabrik: Sun-Seite ist leer.".into());
    }
    if !lf.sun_colors().contains(&take.color) {
        return Some(format!(
            "Große Fabrik: Farbe {} nicht auf Sun-Seite.",
            take.color.value()
        ));
    }
    None
}

fn validate_large_moon(state: &GameState, take: &TakeAction) -> Option<String> {
    let lf = &state.large_factory;
    if lf.moon_is_empty() {
        return Some("Große Fabrik: Moon-Pool ist leer.".into());
    }
    if !lf.moon_colors().contains(&take.color) {
        return Some(format!(
            "Große Fabrik: Farbe {} nicht im Moon-Pool.",
            take.color.value()
        ));
    }
    None
}

/// Place-Validierung: Strafleiste (-1) immer erlaubt; Musterreihe nicht voll,
/// keine fremde Farbe.
pub fn validate_place(state: &GameState, color: TileColor, row_index: i32) -> Option<String> {
    if row_index == -1 {
        return None;
    }
    if !(0..=5).contains(&row_index) {
        return Some(format!("Ungültiger row_index: {row_index}"));
    }
    let player = &state.players[state.current_player];
    let row = &player.pattern_lines[row_index as usize];
    if row.is_complete() {
        return Some(format!("Musterreihe {} ist bereits voll.", row_index + 1));
    }
    match row.color {
        Some(c) if c != color => Some(format!(
            "Musterreihe {} enthält bereits {} — {} passt nicht.",
            row_index + 1,
            c.value(),
            color.value()
        )),
        _ => None,
    }
}

/// Alle oben verfügbaren Mond-Farben (über kleine Fabriken + große Fabrik).
fn available_moon_colors(state: &GameState) -> Vec<TileColor> {
    let mut v: Vec<TileColor> = Vec::new();
    for f in &state.factories {
        for c in f.moon_top_colors() {
            if !v.contains(&c) {
                v.push(c);
            }
        }
    }
    for c in state.large_factory.moon_colors() {
        if !v.contains(&c) {
            v.push(c);
        }
    }
    v
}

/// Validiert die Sonderaktion C (globaler Mond-Zug).
pub fn validate_moon_take(state: &GameState, m: &Move) -> Option<String> {
    let color = m.take.color;
    if !available_moon_colors(state).contains(&color) {
        return Some(format!(
            "Aktion C ungültig: Keine {}-Fliesen liegen oben auf den Mondbereichen.",
            color.value()
        ));
    }
    validate_place(state, color, m.place.row_index)
}

/// Generiert alle gültigen Stein-Züge für den aktiven Spieler.
pub fn generate_valid_moves(state: &GameState) -> Vec<Move> {
    let mut moves: Vec<Move> = Vec::new();

    // Kleine Fabriken (Sun)
    for f in &state.factories {
        for color in f.sun_colors() {
            let remaining: Vec<TileColor> =
                f.sun_tiles.iter().copied().filter(|&t| t != color).collect();
            let take = TakeAction {
                source: TakeSource::SmallFactorySun,
                color,
                factory_id: Some(f.factory_id),
                moon_order: remaining,
            };
            for &ri in &ROW_INDICES {
                if validate_place(state, color, ri).is_none() {
                    moves.push(Move {
                        take: take.clone(),
                        place: PlaceAction { row_index: ri },
                    });
                }
            }
        }
    }

    // Große Fabrik (Sun)
    for color in state.large_factory.sun_colors() {
        let take = TakeAction {
            source: TakeSource::LargeFactorySun,
            color,
            factory_id: None,
            moon_order: Vec::new(),
        };
        for &ri in &ROW_INDICES {
            if validate_place(state, color, ri).is_none() {
                moves.push(Move {
                    take: take.clone(),
                    place: PlaceAction { row_index: ri },
                });
            }
        }
    }

    // Aktion C: globaler Mond-Zug (factory_id = None)
    for color in available_moon_colors(state) {
        for &ri in &ROW_INDICES {
            let m = Move {
                take: TakeAction {
                    source: TakeSource::SmallFactoryMoon,
                    color,
                    factory_id: None,
                    moon_order: Vec::new(),
                },
                place: PlaceAction { row_index: ri },
            };
            if validate_moon_take(state, &m).is_none() {
                moves.push(m);
            }
        }
    }

    moves
}
