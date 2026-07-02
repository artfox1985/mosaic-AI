//! Spielsteuerung (Orchestrierung) — Port von engine/game.py.
//!
//! Schritt 5: Tiling-Phase (Aktionen, Validierung, Ausführung, Scoring),
//! Rundenende-Strafen und Rundenwechsel. Die scoring-tile-Endwertung
//! (engine/scoring.py) folgt als eigenes Modul in Schritt 6.

use rand::Rng;

use crate::execution::execute_move;
use crate::moves::{
    Action, DrawFromStackMove, PlaceDomeTileMove, TakeBonusChipMove,
};
use crate::round_end::{
    apply_bonus_chips_to_row, execute_full_tiling, generate_tiling_actions,
    process_unplaceable_rows, score_penalty, validate_tiling_action, TilingAction,
};
use crate::scoring::{calculate_end_scoring, EndScoring};
use crate::state::{setup_new_game, setup_new_round, GameState, Phase, NUM_PLAYERS, NUM_ROUNDS};
use crate::validation::{generate_valid_moves, validate_move, validate_moon_take};

/// Zug der Tiling-Phase — Port der dict-Move-Typen aus engine/game.py.apply().
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TilingMove {
    /// Einen Stein aus einer vollen Musterreihe auf die Kuppel legen.
    Place(TilingAction),
    /// Eine Reihe mit Bonusplättchen komplettieren (`use_chips`).
    UseChips { player: usize, pattern_row: usize },
    /// Tiling für einen Spieler beenden (`end_tiling`).
    EndTiling { player: usize },
}

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
    let (name, tokens) = {
        let p = &state.players[pi];
        (p.name.clone(), p.player_tokens_used)
    };
    state.log_event(format!(
        "{name}: Kachel {} → Slot ({},{}) rot={}° [Plättchen {tokens}/2]",
        m.dome_tile_id, m.slot_row, m.slot_col, m.rotation
    ));
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
    let (name, score) = {
        let p = &state.players[pi];
        (p.name.clone(), p.score)
    };
    state.log_event(format!(
        "📦 {name}: {}× vom Stapel gezogen −{} Pkt → {score} Gesamt",
        m.num_drawn, m.num_drawn
    ));
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
    let (name, tokens) = {
        let p = &state.players[pi];
        (p.name.clone(), p.player_tokens_used)
    };
    state.log_event(format!(
        "{name}: Kachel {} → Slot ({},{}) rot={}° [Plättchen {tokens}/2]",
        m.chosen_id, m.slot_row, m.slot_col, m.rotation
    ));
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
    let (name, used) = {
        let p = &state.players[pi];
        (p.name.clone(), p.bonus_chips_used_this_round)
    };
    state.log_event(format!(
        "{name}: Bonusplättchen von Fabrik {} genommen [{used}/2 diese Runde]",
        m.factory_id
    ));
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
    let name = state.players[player_idx].name.clone();
    state.log_event(format!("{name}: Startkachel {tile_id} → ({row},{col}) rot={rot}°"));
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

/// Alle gültigen Drafting-Aktionen für den aktiven Spieler eines Zustands.
/// Leer → [Pass]. Single Source of Truth für Game-Loop und MCTS.
pub fn drafting_actions(state: &GameState) -> Vec<Action> {
    let mut actions: Vec<Action> = Vec::new();
    for m in generate_valid_moves(state) {
        actions.push(Action::Stone(m));
    }
    for m in generate_dome_moves(state) {
        actions.push(Action::Dome(m));
    }
    for m in generate_bonus_chip_moves(state) {
        actions.push(Action::BonusChip(m));
    }
    for m in generate_draw_stack_moves(state) {
        actions.push(Action::DrawStack(m));
    }
    if actions.is_empty() {
        actions.push(Action::Pass);
    }
    actions
}

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
        drafting_actions(&self.state)
    }

    fn check_phase_transition(&mut self) {
        if self.state.phase == Phase::Drafting && check_drafting_complete(&mut self.state) {
            self.state.phase = Phase::Tiling;
            self.state.tiling_done = [false, false];
            for p in self.state.players.iter_mut() {
                p.tiled_max_row = -1;
            }
            self.state.log_event("Tiling-Phase beginnt.");
            // Unplatzierbare Reihen → Strafleiste (für beide Spieler).
            for pi in 0..NUM_PLAYERS {
                let (players, tower) = (&mut self.state.players, &mut self.state.tower);
                process_unplaceable_rows(&mut players[pi], tower);
            }
        }
    }

    // ── Tiling-Phase ──────────────────────────────────────────────────────────

    /// Alle gültigen Tiling-Aktionen des Spielers (leer → Spieler kann `EndTiling`).
    pub fn valid_tiling_actions(&self, player_idx: usize) -> Vec<TilingAction> {
        generate_tiling_actions(&self.state, player_idx)
    }

    /// Führt eine einzelne, validierte Tiling-Aktion aus und gibt die Punkte zurück.
    pub fn apply_single_tiling(
        &mut self,
        player_idx: usize,
        action: &TilingAction,
    ) -> Result<i32, String> {
        if let Some(e) = validate_tiling_action(&self.state, player_idx, action) {
            return Err(e);
        }
        execute_full_tiling(&mut self.state, player_idx, action)
    }

    /// Wendet einen Tiling-Phasen-Zug an (Stein legen / Chips nutzen / beenden).
    /// `EndTiling` kann den Rundenwechsel auslösen und braucht daher den RNG.
    pub fn apply_tiling<R: Rng + ?Sized>(
        &mut self,
        mv: &TilingMove,
        rng: &mut R,
    ) -> Result<(), String> {
        if self.state.phase != Phase::Tiling {
            return Err(format!(
                "Tiling-Zug in Phase '{}' nicht erlaubt.",
                self.state.phase.as_str()
            ));
        }
        match mv {
            TilingMove::Place(action) => {
                let pi = self.state.current_player;
                self.apply_single_tiling(pi, action)?;
                Ok(())
            }
            TilingMove::UseChips { player, pattern_row } => {
                if !apply_bonus_chips_to_row(&mut self.state.players[*player], *pattern_row) {
                    return Err(format!("Reihe {} nicht mit Chips komplettierbar.", pattern_row + 1));
                }
                let name = self.state.players[*player].name.clone();
                self.state.log_event(format!(
                    "🎫 {name} komplettiert Reihe {} vollständig mit Bonus-Chips!",
                    pattern_row + 1
                ));
                Ok(())
            }
            TilingMove::EndTiling { player } => self.end_tiling(*player, rng),
        }
    }

    /// Beendet das Tiling für einen Spieler; wechselt zum anderen oder schließt
    /// die Phase ab (Strafen + Rundenwechsel/Spielende).
    fn end_tiling<R: Rng + ?Sized>(&mut self, player: usize, rng: &mut R) -> Result<(), String> {
        if !self.valid_tiling_actions(player).is_empty() {
            return Err(format!("Noch Tiling-Züge offen für Spieler {player}."));
        }
        self.state.tiling_done[player] = true;
        let other = 1 - player;
        if !self.state.tiling_done[other] {
            self.state.current_player = other;
            return Ok(());
        }
        self.state.tiling_done = [false, false];
        self.execute_end_tiling(rng);
        Ok(())
    }

    /// Rundenende-Abschluss: unplatzierbare Reihen, Strafen, dann Rundenwechsel
    /// oder Spielende. Port von engine/game.py `_execute_end_tiling`.
    fn execute_end_tiling<R: Rng + ?Sized>(&mut self, rng: &mut R) {
        for pi in 0..NUM_PLAYERS {
            let (players, tower) = (&mut self.state.players, &mut self.state.tower);
            process_unplaceable_rows(&mut players[pi], tower);
        }

        for pi in 0..NUM_PLAYERS {
            let pen = score_penalty(&mut self.state.players[pi]);
            let broken = self.state.players[pi].clear_broken();
            self.state.tower.add(&broken);
            if pen < 0 {
                self.state.players[pi].apply_score(pen);
                let (name, score) = {
                    let p = &self.state.players[pi];
                    (p.name.clone(), p.score)
                };
                self.state.log_event(format!("{name}: Strafe {pen} Pkt → {score} Gesamt"));
            }
        }

        if self.is_over() {
            self.state.phase = Phase::End;
            self.state.log_event("Das Spiel ist beendet!");
        } else {
            self.next_round(rng);
        }
    }

    /// Bereitet die nächste Runde vor: Display auf 3 auffüllen, dann setup_new_round.
    fn next_round<R: Rng + ?Sized>(&mut self, rng: &mut R) {
        while self.state.dome_display.len() < 3 && !self.state.dome_tile_pool.is_empty() {
            let t = self.state.dome_tile_pool.remove(0);
            self.state.dome_display.push(t);
        }
        setup_new_round(&mut self.state, rng);
        self.state.phase = Phase::Drafting;
    }

    // ── Endwertung ────────────────────────────────────────────────────────────

    /// Wendet die Wertungsplatten-Endwertung an (nach dem Spielende), schreibt
    /// die Punkte gut und setzt die Phase auf `Final`. Gibt die Detailergebnisse
    /// je Spieler zurück. Port von engine/game.py `_calculate_end_scoring`.
    pub fn apply_end_scoring(&mut self) -> Vec<EndScoring> {
        let ids = self.state.scoring_tile_ids.clone();
        let mut results = Vec::with_capacity(NUM_PLAYERS);
        for pi in 0..NUM_PLAYERS {
            let res = calculate_end_scoring(&self.state.players[pi], &ids);
            self.state.players[pi].apply_score(res.total);
            let (name, score) = {
                let p = &self.state.players[pi];
                (p.name.clone(), p.score)
            };
            self.state
                .log_event(format!("🏆 {name}: Endwertung {} Pkt → Gesamt: {score} Pkt", res.total));
            for d in &res.details {
                self.state
                    .log_event(format!("   {} {}: {} Pkt", d.emoji, d.name, d.score));
            }
            results.push(res);
        }
        self.state.phase = Phase::Final;
        results
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
    fn full_round_drafting_through_tiling_to_next_round() {
        let mut rng = StdRng::seed_from_u64(2024);
        let mut game = Game::start(names(), 0, vec![0, 1, 2], &mut rng);
        for p in game.state.players.iter_mut() {
            p.start_tile_pending = false;
        }

        // Drafting bis Tiling.
        let mut steps = 0;
        while game.state.phase == Phase::Drafting && steps < 500 {
            let actions = game.valid_drafting_actions();
            game.apply_drafting(&actions[0]).expect("valider Drafting-Zug");
            steps += 1;
        }
        assert_eq!(game.state.phase, Phase::Tiling);

        // Tiling: jeder Spieler legt alle möglichen Steine, dann EndTiling.
        let round_before = game.state.round_number;
        let mut tsteps = 0;
        while game.state.phase == Phase::Tiling && tsteps < 200 {
            let pi = game.state.current_player;
            let actions = game.valid_tiling_actions(pi);
            let mv = match actions.first() {
                Some(a) => TilingMove::Place(*a),
                None => TilingMove::EndTiling { player: pi },
            };
            game.apply_tiling(&mv, &mut rng).expect("valider Tiling-Zug");
            tsteps += 1;
        }
        assert!(tsteps < 200, "Tiling terminiert");
        // Runde 1 ist nicht das Spielende → neue Runde, Phase wieder Drafting.
        assert_eq!(game.state.phase, Phase::Drafting);
        assert_eq!(game.state.round_number, round_before + 1);
        // Tiling-Flags zurückgesetzt; volle Reihen abgeräumt.
        assert_eq!(game.state.tiling_done, [false, false]);
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
