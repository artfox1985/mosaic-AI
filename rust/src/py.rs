//! PyO3-Bindings: exportiert eine spielbare Engine-Instanz `PyGame` nach Python.
//!
//! Ziel: server.py kann eine komplette Partie direkt auf der Rust-Engine fahren.
//! `state_json()` liefert exakt das Frontend-JSON (Port von engine/serializer.py),
//! die `apply_*`-Methoden spiegeln die server.py-Routen, und die `ai_*`-Methoden
//! treiben die MCTS-KI (Drafting + Tiling + Startkachel, inkl. Debug-Baum).

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use rand::rngs::StdRng;
use rand::SeedableRng;
use serde_json::{json, Value};

use crate::dome::SpaceType;
use crate::game::{apply_start_placement, Game, TilingMove};
use crate::mcts::{search_move_json, search_with_tree, SearchMove};
use crate::moves::{Action, DrawFromStackMove, Move, PlaceAction, PlaceDomeTileMove, TakeAction, TakeBonusChipMove, TakeSource};
use crate::round_end::{apply_bonus_chips_to_row, find_unplaceable_rows, TilingAction};
use crate::scoring::{has_exclusion_conflict, sample_valid_scoring_ids};
use crate::serialize::{serialize_stack_peek, state_to_json};
use crate::state::Phase;
use crate::tile::TileColor;

/// Tiefe/Breite des Debug-Baum-Exports (siehe debug.html-Panel).
const AI_TREE_DEPTH: u32 = 3;
const AI_TREE_TOPK: usize = 8;
/// Standard-UCT-Konstante der KI (= mcts::DEFAULT_C).
const AI_C: f64 = 0.3;

fn parse_color(s: &str) -> PyResult<TileColor> {
    TileColor::from_value(s).ok_or_else(|| PyValueError::new_err(format!("Unbekannte Farbe: {s}")))
}

fn parse_source(s: &str) -> PyResult<TakeSource> {
    match s {
        "SMALL_FACTORY_SUN" => Ok(TakeSource::SmallFactorySun),
        "SMALL_FACTORY_MOON" => Ok(TakeSource::SmallFactoryMoon),
        "LARGE_FACTORY_SUN" => Ok(TakeSource::LargeFactorySun),
        "LARGE_FACTORY_MOON" => Ok(TakeSource::LargeFactoryMoon),
        _ => Err(PyValueError::new_err(format!("Unbekannte Quelle: {s}"))),
    }
}

fn map_err<T>(r: Result<T, String>) -> PyResult<T> {
    r.map_err(PyValueError::new_err)
}

#[pyclass]
pub struct PyGame {
    game: Game,
    rng: StdRng,
    seed: u64,
    first_player: usize,
    scoring_confirmed: bool,
}

#[pymethods]
impl PyGame {
    /// Startet eine neue Partie. `scoring_ids` optional (sonst zufällig konfliktfrei).
    #[new]
    #[pyo3(signature = (names, first_player=0, seed=None, scoring_ids=None))]
    fn new(
        names: (String, String),
        first_player: usize,
        seed: Option<u64>,
        scoring_ids: Option<Vec<usize>>,
    ) -> Self {
        let seed = seed.unwrap_or_else(rand::random);
        let mut rng = StdRng::seed_from_u64(seed);
        let ids = scoring_ids.unwrap_or_else(|| sample_valid_scoring_ids(3, &mut rng));
        let game = Game::start([names.0, names.1], first_player, ids, &mut rng);
        PyGame { game, rng, seed, first_player, scoring_confirmed: false }
    }

    // ── Zustand ───────────────────────────────────────────────────────────────

    /// Vollständiges Frontend-JSON (als String; Python: json.loads).
    fn state_json(&self) -> String {
        state_to_json(&self.game.state, self.scoring_confirmed).to_string()
    }

    fn phase(&self) -> &'static str {
        self.game.state.phase.as_str()
    }
    fn current_player(&self) -> usize {
        self.game.state.current_player
    }
    fn round_number(&self) -> u32 {
        self.game.state.round_number
    }
    fn is_over(&self) -> bool {
        self.game.is_over()
    }
    fn seed(&self) -> u64 {
        self.seed
    }
    fn first_player(&self) -> usize {
        self.first_player
    }
    fn scores(&self) -> (i32, i32) {
        (self.game.state.players[0].score, self.game.state.players[1].score)
    }
    fn both_start_placed(&self) -> bool {
        self.game.state.players.iter().all(|p| !p.start_tile_pending)
    }
    /// Anzahl noch platzierbarer Tiling-Aktionen für einen Spieler (Guard für end_tiling).
    fn pending_tiling_count(&self, player: usize) -> usize {
        self.game.valid_tiling_actions(player).len()
    }
    /// Neue Log-Einträge ab Index `from` (für die Logdatei).
    fn log_since(&self, from: usize) -> Vec<String> {
        let log = &self.game.state.log;
        if from >= log.len() {
            Vec::new()
        } else {
            log[from..].to_vec()
        }
    }
    fn log_len(&self) -> usize {
        self.game.state.log.len()
    }

    // ── Drafting-Züge ─────────────────────────────────────────────────────────

    #[pyo3(signature = (source, color, row, factory_id=None, moon_order=None))]
    fn apply_stone(
        &mut self,
        source: &str,
        color: &str,
        row: i32,
        factory_id: Option<usize>,
        moon_order: Option<Vec<String>>,
    ) -> PyResult<()> {
        let src = parse_source(source)?;
        let col = parse_color(color)?;
        let order: Vec<TileColor> = match moon_order {
            Some(v) => v.iter().map(|s| parse_color(s)).collect::<PyResult<_>>()?,
            None => Vec::new(),
        };
        let m = Move {
            take: TakeAction { source: src, color: col, factory_id, moon_order: order },
            place: PlaceAction { row_index: row },
        };
        map_err(self.game.apply_drafting(&Action::Stone(m)))
    }

    #[pyo3(signature = (tile_id, slot_row, slot_col, rotation=0))]
    fn apply_dome(&mut self, tile_id: usize, slot_row: usize, slot_col: usize, rotation: u32) -> PyResult<()> {
        let m = PlaceDomeTileMove { dome_tile_id: tile_id, slot_row, slot_col, rotation };
        map_err(self.game.apply_drafting(&Action::Dome(m)))
    }

    #[pyo3(signature = (num_drawn, chosen_id, slot_row, slot_col, rotation=0))]
    fn apply_dome_stack(&mut self, num_drawn: usize, chosen_id: usize, slot_row: usize, slot_col: usize, rotation: u32) -> PyResult<()> {
        let m = DrawFromStackMove { num_drawn, chosen_id, slot_row, slot_col, rotation };
        map_err(self.game.apply_drafting(&Action::DrawStack(m)))
    }

    fn apply_bonus_chip(&mut self, factory_id: usize) -> PyResult<()> {
        map_err(self.game.apply_drafting(&Action::BonusChip(TakeBonusChipMove { factory_id })))
    }

    fn apply_pass(&mut self) -> PyResult<()> {
        map_err(self.game.apply_drafting(&Action::Pass))
    }

    #[pyo3(signature = (player, tile_id, slot_row, slot_col, rotation=0))]
    fn apply_start_tile(&mut self, player: usize, tile_id: usize, slot_row: usize, slot_col: usize, rotation: u32) -> PyResult<()> {
        map_err(apply_start_placement(&mut self.game.state, player, tile_id, slot_row, slot_col, rotation))
    }

    // ── Tiling-Phase ──────────────────────────────────────────────────────────

    #[pyo3(signature = (player, pattern_row, slot_row, slot_col, space_index, dome_tile_id=None, rotation=0))]
    fn apply_tiling(
        &mut self,
        player: usize,
        pattern_row: usize,
        slot_row: usize,
        slot_col: usize,
        space_index: usize,
        dome_tile_id: Option<usize>,
        rotation: u32,
    ) -> PyResult<i32> {
        if self.game.state.phase != Phase::Tiling {
            return Err(PyValueError::new_err("Nicht in der Tiling-Phase."));
        }
        let action = TilingAction { pattern_row, slot_row, slot_col, space_index, dome_tile_id, rotation };
        map_err(self.game.apply_single_tiling(player, &action))
    }

    /// Reihe in der Tiling-Phase mit Bonusplättchen komplettieren.
    fn apply_tiling_chips(&mut self, player: usize, pattern_row: usize) -> PyResult<()> {
        if !apply_bonus_chips_to_row(&mut self.game.state.players[player], pattern_row) {
            return Err(PyValueError::new_err(format!(
                "Reihe {} nicht mit Chips komplettierbar.",
                pattern_row + 1
            )));
        }
        let name = self.game.state.players[player].name.clone();
        self.game
            .state
            .log_event(format!("🎫 {name} komplettiert Reihe {} mit Bonus-Chips!", pattern_row + 1));
        Ok(())
    }

    /// Unplatzierbare Fliesen einer Reihe auf die Strafleiste schieben.
    fn move_row_to_floor(&mut self, player: usize, pattern_row: usize) -> PyResult<()> {
        let p = &mut self.game.state.players[player];
        let tiles: Vec<_> = std::mem::take(&mut p.pattern_lines[pattern_row].tiles);
        if tiles.is_empty() {
            return Err(PyValueError::new_err("Reihe ist leer"));
        }
        p.pattern_lines[pattern_row].color = None;
        let overflow = p.add_broken(&tiles);
        self.game.state.tower.add(&overflow);
        let name = self.game.state.players[player].name.clone();
        let n = tiles.len();
        self.game
            .state
            .log_event(format!("{name}: {n} unplatzierbare Fliesen → Strafleiste"));
        Ok(())
    }

    /// Beendet das Tiling für einen Spieler (löst ggf. Runden-/Spielende aus).
    fn end_tiling(&mut self, player: usize) -> PyResult<()> {
        let mv = TilingMove::EndTiling { player };
        map_err(self.game.apply_tiling(&mv, &mut self.rng))
    }

    /// Unplatzierbare Reihen beider Spieler (für /api/tiling/unplaceable).
    fn unplaceable_json(&self) -> String {
        let mut out = Vec::new();
        for (pi, player) in self.game.state.players.iter().enumerate() {
            for ri in find_unplaceable_rows(player) {
                let row = &player.pattern_lines[ri];
                out.push(json!({
                    "player": pi,
                    "pattern_row": ri,
                    "color": row.color.map(|c| c.value()),
                    "count": row.tiles.len(),
                }));
            }
        }
        Value::Array(out).to_string()
    }

    // ── Wertungsplatten / Endwertung ──────────────────────────────────────────

    fn select_scoring(&mut self, ids: Vec<usize>) -> PyResult<()> {
        if ids.len() != 3 {
            return Err(PyValueError::new_err("Genau 3 Wertungsplatten wählen."));
        }
        if has_exclusion_conflict(&ids) {
            return Err(PyValueError::new_err("Zwei sich ausschließende Wertungsplatten gewählt."));
        }
        self.game.state.scoring_tile_ids = ids.clone();
        self.scoring_confirmed = true;
        self.game.state.log_event(format!("Wertungsplatten gewählt: {ids:?}"));
        Ok(())
    }

    /// Endwertung anwenden; gibt JSON {"end_scoring": {pi: {...}}} zurück.
    fn end_scoring_json(&mut self) -> PyResult<String> {
        if self.game.state.phase != Phase::End {
            return Err(PyValueError::new_err("Spiel noch nicht beendet."));
        }
        let results = self.game.apply_end_scoring();
        let mut per_player = serde_json::Map::new();
        for (pi, res) in results.iter().enumerate() {
            let mut entry = serde_json::Map::new();
            for d in &res.details {
                entry.insert(
                    d.id.to_string(),
                    json!({ "name": d.name, "emoji": d.emoji, "desc": d.description, "score": d.score }),
                );
            }
            entry.insert("total".to_string(), json!(res.total));
            per_player.insert(pi.to_string(), Value::Object(entry));
        }
        Ok(json!({ "end_scoring": Value::Object(per_player) }).to_string())
    }

    /// Oberste n Stapel-Kacheln (für /api/stack/peek).
    fn peek_stack_json(&self, n: usize) -> String {
        serialize_stack_peek(&self.game.state, n).to_string()
    }

    // ── KI (MCTS) ─────────────────────────────────────────────────────────────

    /// Führt EINEN KI-Zug für den aktuellen Spieler aus (Drafting oder Tiling)
    /// und gibt `{applied, phase, action, done, debug}` als JSON zurück.
    /// `debug` ist debug.html-kompatibel (moves[] + tree). Server ruft dies nur,
    /// wenn die KI am Zug ist.
    #[pyo3(signature = (simulations=300))]
    fn ai_step_json(&mut self, simulations: u32) -> PyResult<String> {
        let (chosen, analysis) = search_with_tree(
            &self.game.state,
            simulations,
            AI_C,
            &mut self.rng,
            AI_TREE_DEPTH,
            AI_TREE_TOPK,
        );
        let mv = match chosen {
            Some(m) => m,
            None => {
                return Ok(json!({
                    "applied": false,
                    "phase": self.game.state.phase.as_str(),
                    "reason": "keine KI-Aktion (terminale Phase?)",
                })
                .to_string())
            }
        };

        let action_json = search_move_json(&mv);
        match &mv {
            SearchMove::Draft(a) => map_err(self.game.apply_drafting(a))?,
            SearchMove::TilePlace(ta) => {
                let pi = self.game.state.current_player;
                map_err(self.game.apply_single_tiling(pi, ta))?;
            }
            SearchMove::TileChips { player, row } => {
                if !apply_bonus_chips_to_row(&mut self.game.state.players[*player], *row) {
                    return Err(PyValueError::new_err("KI: Chip-Komplettierung fehlgeschlagen."));
                }
            }
            SearchMove::TileEnd { player } => {
                let m = TilingMove::EndTiling { player: *player };
                map_err(self.game.apply_tiling(&m, &mut self.rng))?;
            }
        }

        Ok(json!({
            "applied": true,
            "phase": self.game.state.phase.as_str(),
            "action": action_json,
            "done": self.game.is_over(),
            "debug": analysis,
        })
        .to_string())
    }

    /// Analysiert die aktuelle Stellung per MCTS OHNE Zug auszuführen
    /// (für /api/ai/debug). Gibt das debug.html-Analyse-Dict zurück.
    #[pyo3(signature = (simulations=300))]
    fn ai_debug_json(&mut self, simulations: u32) -> String {
        let (_chosen, analysis) = search_with_tree(
            &self.game.state,
            simulations,
            AI_C,
            &mut self.rng,
            AI_TREE_DEPTH,
            AI_TREE_TOPK,
        );
        analysis.to_string()
    }

    /// Platziert die Startkachel der KI per einfacher Farb-Häufigkeits-Heuristik.
    /// Gibt das gewählte Move-Dict zurück.
    fn ai_start_tile_json(&mut self, player: usize) -> PyResult<String> {
        let counts = sun_color_counts(&self.game.state);
        let empties = self.game.state.players[player].dome_grid.empty_slots();
        if empties.is_empty() {
            return Err(PyValueError::new_err("Kein freier Slot für die Startkachel."));
        }

        let mut best: Option<(f64, usize, usize, usize, u32)> = None; // (score, tile_id, r, c, rot)
        for tile in &self.game.state.dome_display {
            for &(r, c) in &empties {
                let corner_bonus = if (r == 0 || r == 2) && (c == 0 || c == 2) { 0.5 } else { 0.0 };
                for &rot in &[0u32, 90, 180, 270] {
                    let spaces = match tile.rotated_spaces(rot) {
                        Ok(s) => s,
                        Err(_) => continue,
                    };
                    let mut score = corner_bonus;
                    for sp in &spaces {
                        score += match sp.space_type {
                            SpaceType::Normal => sp
                                .required_color
                                .and_then(color_index)
                                .map(|i| counts[i] as f64)
                                .unwrap_or(0.0),
                            SpaceType::Wild => *counts.iter().max().unwrap_or(&0) as f64,
                            SpaceType::Special => 0.0,
                        };
                    }
                    if best.map_or(true, |(b, ..)| score > b) {
                        best = Some((score, tile.tile_id, r, c, rot));
                    }
                }
            }
        }

        let (_score, tile_id, r, c, rot) =
            best.ok_or_else(|| PyValueError::new_err("Keine Startkachel platzierbar."))?;
        map_err(apply_start_placement(&mut self.game.state, player, tile_id, r, c, rot))?;
        Ok(json!({
            "type": "dome",
            "tile_id": tile_id,
            "slot_row": r,
            "slot_col": c,
            "rotation": rot,
            "is_start": true,
            "description": format!("Startkachel #{tile_id} → ({r},{c}) {rot}°"),
        })
        .to_string())
    }
}

/// Index einer Normalfarbe in `TileColor::NORMAL` (None für Wild).
fn color_index(c: TileColor) -> Option<usize> {
    TileColor::NORMAL.iter().position(|&x| x == c)
}

/// Zählt die Sun-Steine je Normalfarbe über alle Fabriken + Tischmitte.
fn sun_color_counts(state: &crate::state::GameState) -> [usize; 5] {
    let mut counts = [0usize; 5];
    let mut bump = |c: TileColor| {
        if let Some(i) = color_index(c) {
            counts[i] += 1;
        }
    };
    for f in &state.factories {
        for &t in &f.sun_tiles {
            bump(t);
        }
    }
    for &t in &state.large_factory.sun_tiles {
        bump(t);
    }
    counts
}
