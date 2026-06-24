//! PyO3-Bindings: exportiert eine spielbare Engine-Instanz `PyGame` nach Python.
//!
//! Ziel: server.py kann eine komplette Mensch-gegen-Mensch-Partie direkt auf der
//! Rust-Engine fahren. `state_json()` liefert exakt das Frontend-JSON
//! (Port von engine/serializer.py), die `apply_*`-Methoden spiegeln die
//! server.py-Routen. KI-Anbindung folgt später.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use rand::rngs::StdRng;
use rand::SeedableRng;
use serde_json::{json, Value};

use crate::game::{apply_start_placement, Game, TilingMove};
use crate::moves::{Action, DrawFromStackMove, Move, PlaceAction, PlaceDomeTileMove, TakeAction, TakeBonusChipMove, TakeSource};
use crate::round_end::{apply_bonus_chips_to_row, find_unplaceable_rows, TilingAction};
use crate::scoring::{has_exclusion_conflict, sample_valid_scoring_ids};
use crate::serialize::{serialize_stack_peek, state_to_json};
use crate::state::Phase;
use crate::tile::TileColor;

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
}
