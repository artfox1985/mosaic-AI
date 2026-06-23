//! Spielsteuerung (Orchestrierung) — Port von engine/game.py.
//!
//! Schritt 4: Dome-/Chip-/Stapel-Züge + Drafting-Orchestrierung bis zum
//! Phasenübergang Drafting→Tiling. Tiling-Ausführung, Scoring, Rundenwechsel
//! und Endwertung folgen in Schritt 5.

use rand::Rng;

use crate::execution::execute_move;
use crate::moves::{
    Action, DrawFromStackMove, PlaceDomeTileMove, TakeBonusChipMove,
};
use crate::round_end::process_unplaceable_rows;
use crate::state::{setup_new_game, GameState, Phase, NUM_PLAYERS, NUM_ROUNDS};
use crate::validation::{generate_valid_moves, validate_move, validate_moon_take};

// ── Dome-Zug ────────────────────────────────────────────────────────────────

pub fn validate_dome_move(state: &GameState, m: &PlaceDomeTileMove) -> Option<String> {
    let player = &state.players[state.current_player];
    if !player.can_place_dome_tile(state.round_number) {
        if state.round_number >= 5 {
            return Some("In Runde 5 werden keine Kuppeln mehr gelegt.".into());
        }
        if player.dome_tiles_placed_this_round >= 2 {
            return Some(format!("{} hat bereits 2 Kuppeln diese Runde gelegt.", player.name));
        }
        return Some("Das 3×3-Raster ist bereits voll.".into());
    }
    if player.has_unplaced_start_tile() {
        return Some("Die Startkuppel muss als erstes (in der Startphase) gelegt werden.".into());
    }
    if !state.dome_display.iter().any(|t| t.tile_id == m.dome_tile_id) {
        return Some(format!("Kuppel {} liegt nicht in der offenen Ablage.", m.dome_tile_id));
    }
    if m.slot_row > 2 || m.slot_col > 2 {
        return Some(format!("Ungültiger Slot ({},{}).", m.slot_row, m.slot_col));
    }
    if state.players[state.current_player].dome_grid.dome_slots[m.slot_row][m.slot_col].is_some() {
        return Some(format!("Slot ({},{}) ist bereits belegt.", m.slot_row, m.slot_col));
    }
    None
}

pub fn execute_dome_move(state: &mut GameState, m: &PlaceDomeTileMove) -> Result<(), String> {
    let idx = state
        .dome_display
        .iter()
        .position(|t| t.tile_id == m.dome_tile_id)
        .ok_or("Kuppel nicht im Display")?;
    let mut tile = state.dome_display.remove(idx);
    tile.apply_rotation(m.rotation)?;
    let pi = state.current_player;
    state.players[pi]
        .dome_grid
        .place_dome_tile(tile, m.slot_row, m.slot_col)?;
    state.players[pi].register_dome_placement()?;
    state.players[pi].use_player_token(state.round_number)?;
    Ok(())
}

pub fn generate_dome_moves(state: &GameState) -> Vec<PlaceDomeTileMove> {
    let player = &state.players[state.current_player];
    if !player.can_place_dome_tile(state.round_number) || player.has_unplaced_start_tile() {
        return Vec::new();
    }
    let empty_slots = player.dome_grid.empty_slots();
    let mut moves = Vec::new();
    for tile in &state.dome_display {
        for &(sr, sc) in &empty_slots {
            for &rot in &[0u32, 90, 180, 270] {
                let m = PlaceDomeTileMove {
                    dome_tile_id: tile.tile_id,
                    slot_row: sr,
                    slot_col: sc,
                    rotation: rot,
                };
                if validate_dome_move(state, &m).is_none() {
                    moves.push(m);
                }
            }
        }
    }
    moves
}

// ── Stapel-Zug (Aktion A) ─────────────────────────────────────────────────────

pub fn validate_draw_from_stack(state: &GameState, m: &DrawFromStackMove) -> Option<String> {
    let player = &state.players[state.current_player];
    if state.round_number >= 5 {
        return Some("In Runde 5 werden keine Kuppelplatten mehr gelegt.".into());
    }
    if player.has_used_all_tokens(state.round_number) {
        return Some(format!("{} hat bereits beide Spielerplättchen genutzt.", player.name));
    }
    if !player.can_place_dome_tile(state.round_number) {
        return Some("Das 3×3-Raster ist bereits voll.".into());
    }
    if state.dome_tile_pool.is_empty() {
        return Some("Kein Stapel mehr vorhanden.".into());
    }
    if m.num_drawn < 1 || m.num_drawn > state.dome_tile_pool.len() {
        return Some(format!("num_drawn muss zwischen 1 und {} liegen.", state.dome_tile_pool.len()));
    }
    let available = state.dome_tile_pool[..m.num_drawn]
        .iter()
        .any(|t| t.tile_id == m.chosen_id);
    if !available {
        return Some(format!("Kachel {} nicht unter den {} gezogenen.", m.chosen_id, m.num_drawn));
    }
    if player.dome_grid.dome_slots[m.slot_row][m.slot_col].is_some() {
        return Some(format!("Slot ({},{}) ist bereits belegt.", m.slot_row, m.slot_col));
    }
    None
}

pub fn execute_draw_from_stack(state: &mut GameState, m: &DrawFromStackMove) -> Result<(), String> {
    let pi = state.current_player;
    state.players[pi].apply_score(-(m.num_drawn as i32));
    let drawn: Vec<_> = state.dome_tile_pool.drain(..m.num_drawn).collect();
    let mut chosen = None;
    for t in drawn {
        if t.tile_id == m.chosen_id && chosen.is_none() {
            chosen = Some(t);
        } else {
            state.dome_tile_pool.push(t); // Rest zurück unter den Stapel
        }
    }
    let mut chosen = chosen.ok_or("gewählte Kachel nicht gezogen")?;
    chosen.apply_rotation(m.rotation)?;
    state.players[pi]
        .dome_grid
        .place_dome_tile(chosen, m.slot_row, m.slot_col)?;
    state.players[pi].register_dome_placement()?;
    state.players[pi].use_player_token(state.round_number)?;
    Ok(())
}

// ── Bonus-Chip (Aktion D) ─────────────────────────────────────────────────────

pub fn validate_take_bonus_chip(state: &GameState, m: &TakeBonusChipMove) -> Option<String> {
    let player = &state.players[state.current_player];
    if !player.can_take_bonus_chip() {
        return Some(format!("{} hat bereits 2 Bonusplättchen diese Runde genommen.", player.name));
    }
    match state.factories.iter().find(|f| f.factory_id == m.factory_id) {
        None => Some(format!("Fabrik {} nicht gefunden.", m.factory_id)),
        Some(f) if !f.bonus_chip_revealed || f.bonus_chip.is_none() => {
            Some(format!("Kein aufgedecktes Bonusplättchen auf Fabrik {}.", m.factory_id))
        }
        Some(_) => None,
    }
}

pub fn execute_take_bonus_chip(state: &mut GameState, m: &TakeBonusChipMove) -> Result<(), String> {
    let fidx = state
        .factories
        .iter()
        .position(|f| f.factory_id == m.factory_id)
        .ok_or("Fabrik nicht gefunden")?;
    let chip = state.factories[fidx].bonus_chip.take().ok_or("kein Chip")?;
    state.factories[fidx].bonus_chip_revealed = false;
    let pi = state.current_player;
    state.players[pi].take_bonus_chip(chip)?;
    Ok(())
}

/// Repräsentative Stapel-Züge (Aktion A): günstigste Variante (num_drawn=1,
/// oberste Stapelkachel) in jeden freien Slot, Rotation 0. Die vollständige
/// num_drawn/Rotations-Auswahl trifft später der Agent.
pub fn generate_draw_stack_moves(state: &GameState) -> Vec<DrawFromStackMove> {
    let player = &state.players[state.current_player];
    if state.round_number >= 5
        || player.has_used_all_tokens(state.round_number)
        || !player.can_place_dome_tile(state.round_number)
        || state.dome_tile_pool.is_empty()
    {
        return Vec::new();
    }
    let chosen_id = state.dome_tile_pool[0].tile_id;
    player
        .dome_grid
        .empty_slots()
        .into_iter()
        .map(|(sr, sc)| DrawFromStackMove {
            num_drawn: 1,
            chosen_id,
            slot_row: sr,
            slot_col: sc,
            rotation: 0,
        })
        .collect()
}

pub fn generate_bonus_chip_moves(state: &GameState) -> Vec<TakeBonusChipMove> {
    let player = &state.players[state.current_player];
    if !player.can_take_bonus_chip() {
        return Vec::new();
    }
    state
        .factories
        .iter()
        .filter(|f| f.bonus_chip_revealed && f.bonus_chip.is_some())
        .map(|f| TakeBonusChipMove { factory_id: f.factory_id })
        .collect()
}

// ── Drafting-Abschluss ────────────────────────────────────────────────────────

/// Kann der aktive Spieler (so wie state.current_player gesetzt ist) noch ziehen?
fn current_player_can_move(state: &GameState) -> bool {
    let p = &state.players[state.current_player];
    let can_draw = state.round_number < 5
        && !p.has_used_all_tokens(state.round_number)
        && !state.dome_tile_pool.is_empty()
        && p.can_place_dome_tile(state.round_number);
    can_draw
        || !generate_valid_moves(state).is_empty()
        || !generate_dome_moves(state).is_empty()
        || !generate_bonus_chip_moves(state).is_empty()
}

/// Port von round_end.check_drafting_complete. Braucht &mut, um current_player
/// temporär für die Pro-Spieler-Prüfung zu setzen (danach wiederhergestellt).
pub fn check_drafting_complete(state: &mut GameState) -> bool {
    let chips_available = state
        .factories
        .iter()
        .any(|f| f.bonus_chip.is_some() && f.bonus_chip_revealed);
    if chips_available {
        return false;
    }
    let factories_empty = state
        .factories
        .iter()
        .all(|f| f.is_fully_empty() && (f.bonus_chip.is_none() || f.bonus_chip_revealed))
        && state.large_factory.is_empty();
    if !factories_empty {
        return false;
    }
    if state.round_number >= 5 {
        return true;
    }
    let tokens_done = state
        .players
        .iter()
        .all(|p| p.has_used_all_tokens(state.round_number));
    if tokens_done {
        return true;
    }
    // Kann noch irgendein Spieler etwas tun?
    let orig = state.current_player;
    let mut anyone = false;
    for pi in 0..NUM_PLAYERS {
        state.current_player = pi;
        if current_player_can_move(state) {
            anyone = true;
            break;
        }
    }
    state.current_player = orig;
    !anyone
}

// ── Startkuppel-Platzierung ───────────────────────────────────────────────────

pub fn apply_start_placement(
    state: &mut GameState,
    player_idx: usize,
    tile_id: usize,
    row: usize,
    col: usize,
    rot: u32,
) -> Result<(), String> {
    let first_player = state.current_player;
    let non_starter = 1 - first_player;
    if player_idx == first_player && state.players[non_starter].start_tile_pending {
        return Err("Nicht-Startspieler muss zuerst eine Kuppelplatte wählen.".into());
    }
    if !state.players[player_idx].start_tile_pending {
        return Err(format!("Spieler {player_idx} hat keine ausstehende Startkachel."));
    }
    if state.players[player_idx].dome_grid.dome_slots[row][col].is_some() {
        return Err(format!("Slot ({row},{col}) ist nicht frei."));
    }
    let idx = state
        .dome_display
        .iter()
        .position(|t| t.tile_id == tile_id)
        .ok_or_else(|| format!("Kachel {tile_id} nicht im Display."))?;
    let mut tile = state.dome_display.remove(idx);
    if !state.dome_tile_pool.is_empty() {
        // Nachziehen an dieselbe Display-Position, damit übrige Karten ihren Platz behalten.
        let refill = state.dome_tile_pool.remove(0);
        state.dome_display.insert(idx, refill);
    }
    tile.apply_rotation(rot)?;
    state.players[player_idx]
        .dome_grid
        .place_dome_tile(tile, row, col)?;
    state.players[player_idx].start_tile_pending = false;
    Ok(())
}

// ── Sieger ────────────────────────────────────────────────────────────────────

pub fn determine_winner(state: &GameState) -> usize {
    let s0 = state.players[0].score;
    let s1 = state.players[1].score;
    if s0 > s1 {
        0
    } else if s1 > s0 {
        1
    } else if state.players[0].holds_first_player_marker {
        0
    } else {
        1
    }
}

// ── Game-Loop ─────────────────────────────────────────────────────────────────

pub struct Game {
    pub state: GameState,
}

impl Game {
    pub fn start<R: Rng + ?Sized>(
        player_names: [String; NUM_PLAYERS],
        first_player: usize,
        scoring_tile_ids: Vec<usize>,
        rng: &mut R,
    ) -> Self {
        let mut state = setup_new_game(player_names, first_player, rng);
        state.scoring_tile_ids = scoring_tile_ids;
        state.current_player = first_player;
        Game { state }
    }

    pub fn is_over(&self) -> bool {
        self.state.round_number >= NUM_ROUNDS
    }

    /// Wendet einen Drafting-Zug an (Stein/Kuppel/Stapel/Chip/Pass), wechselt den
    /// Spieler und prüft den Phasenübergang. Tiling-Züge folgen in Schritt 5.
    pub fn apply_drafting(&mut self, action: &Action) -> Result<(), String> {
        if self.state.phase != Phase::Drafting {
            return Err(format!("Zug in Phase '{}' nicht erlaubt.", self.state.phase.as_str()));
        }
        match action {
            Action::Stone(m) => {
                let err = if m.is_global_moon_take() {
                    validate_moon_take(&self.state, m)
                } else {
                    validate_move(&self.state, m)
                };
                if let Some(e) = err {
                    return Err(e);
                }
                execute_move(&mut self.state, m);
                self.state.switch_player();
            }
            Action::Dome(m) => {
                if let Some(e) = validate_dome_move(&self.state, m) {
                    return Err(e);
                }
                execute_dome_move(&mut self.state, m)?;
                self.state.switch_player();
            }
            Action::DrawStack(m) => {
                if let Some(e) = validate_draw_from_stack(&self.state, m) {
                    return Err(e);
                }
                execute_draw_from_stack(&mut self.state, m)?;
                self.state.switch_player();
            }
            Action::BonusChip(m) => {
                if let Some(e) = validate_take_bonus_chip(&self.state, m) {
                    return Err(e);
                }
                execute_take_bonus_chip(&mut self.state, m)?;
                self.state.switch_player();
            }
            Action::Pass => {
                self.state.switch_player();
            }
        }
        self.check_phase_transition();
        Ok(())
    }

    /// Alle gültigen Drafting-Aktionen des aktiven Spielers (ohne Stapel-Zug,
    /// dessen Auswahl agentenseitig erfolgt). Leer → [Pass].
    pub fn valid_drafting_actions(&self) -> Vec<Action> {
        let mut actions: Vec<Action> = Vec::new();
        for m in generate_valid_moves(&self.state) {
            actions.push(Action::Stone(m));
        }
        for m in generate_dome_moves(&self.state) {
            actions.push(Action::Dome(m));
        }
        for m in generate_bonus_chip_moves(&self.state) {
            actions.push(Action::BonusChip(m));
        }
        for m in generate_draw_stack_moves(&self.state) {
            actions.push(Action::DrawStack(m));
        }
        if actions.is_empty() {
            actions.push(Action::Pass);
        }
        actions
    }

    fn check_phase_transition(&mut self) {
        if self.state.phase == Phase::Drafting && check_drafting_complete(&mut self.state) {
            self.state.phase = Phase::Tiling;
            self.state.tiling_done = [false, false];
            for p in self.state.players.iter_mut() {
                p.tiled_max_row = -1;
            }
            // Unplatzierbare Reihen → Strafleiste (für beide Spieler).
            for pi in 0..NUM_PLAYERS {
                let (players, tower) = (&mut self.state.players, &mut self.state.tower);
                process_unplaceable_rows(&mut players[pi], tower);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    fn names() -> [String; 2] {
        ["P1".into(), "P2".into()]
    }

    #[test]
    fn drafting_loop_runs_to_tiling() {
        let mut rng = StdRng::seed_from_u64(123);
        let mut game = Game::start(names(), 0, vec![0, 1, 2], &mut rng);
        // Startkacheln als bereits gelegt markieren (Startphase separat getestet).
        for p in game.state.players.iter_mut() {
            p.start_tile_pending = false;
        }
        let mut steps = 0;
        while game.state.phase == Phase::Drafting && steps < 500 {
            let actions = game.valid_drafting_actions();
            // deterministisch ersten Zug nehmen
            game.apply_drafting(&actions[0]).expect("valider Zug");
            steps += 1;
        }
        assert_eq!(game.state.phase, Phase::Tiling, "Drafting endet in Tiling (steps={steps})");
        assert!(steps < 500, "Drafting terminiert");
    }

    #[test]
    fn start_placement_order_and_effect() {
        let mut rng = StdRng::seed_from_u64(50);
        let mut game = Game::start(names(), 0, vec![0, 1, 2], &mut rng);
        // first_player = 0 → Nicht-Startspieler (1) muss zuerst.
        let tid0 = game.state.dome_display[0].tile_id;
        // Startspieler zuerst → Fehler
        assert!(apply_start_placement(&mut game.state, 0, tid0, 0, 0, 0).is_err());
        // Nicht-Startspieler legt
        let tid = game.state.dome_display[0].tile_id;
        apply_start_placement(&mut game.state, 1, tid, 0, 0, 0).unwrap();
        assert!(!game.state.players[1].start_tile_pending);
        assert!(game.state.players[1].dome_grid.dome_slots[0][0].is_some());
        assert_eq!(game.state.dome_display.len(), 3); // nachgezogen
        // dann Startspieler
        let tid2 = game.state.dome_display[0].tile_id;
        apply_start_placement(&mut game.state, 0, tid2, 0, 0, 0).unwrap();
        assert!(!game.state.players[0].start_tile_pending);
    }
}
