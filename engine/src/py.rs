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
use crate::game::{apply_start_placement, drafting_actions, Game, TilingMove};
use crate::mcts::{dynamic_sims, search_log_header, search_log_text, search_move_json, search_with_tree, SearchMove};
use crate::moves::{Action, DrawFromStackMove, Move, PlaceAction, PlaceDomeTileMove, TakeAction, TakeBonusChipMove, TakeSource};
use crate::net::Net;
use crate::net_mcts::{self, net_search_with_tree};
use crate::round_end::{apply_bonus_chips_to_row, apply_bonus_chips_with, find_unplaceable_rows, generate_tiling_actions, TilingAction};
use crate::scoring::{has_exclusion_conflict, sample_valid_scoring_ids};
use crate::serialize::{serialize_stack_peek, state_to_json, tiling_action_to_dict};
use crate::tiling_solver::{best_first_step_exact, solve_round_final_score, TilingStep};
use crate::state::Phase;
use crate::tile::TileColor;

/// Debug-Baum-Export: nur die Wurzel (debug.html zeigt keine Kind-Dropdowns mehr).
const AI_TREE_DEPTH: u32 = 0;
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
    /// Geladenes Netz für den Netz-KI-Modus (Server "Gegen KI spielen" mit
    /// Modell-Version statt "heuristic"). `None` = Heuristik-Modus (Standard).
    net: Option<Net>,
    /// Pfad des zuletzt geladenen Netzes — verhindert Neu-Laden bei jedem Zug.
    net_path: Option<String>,
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
        PyGame {
            game, rng, seed, first_player, scoring_confirmed: false,
            net: None, net_path: None,
        }
    }

    /// Lädt ein ONNX-Netz für den Netz-KI-Modus (einmalig pro Modellpfad — wird
    /// bei gleichem Pfad übersprungen). Server ruft dies bei `/api/new_game`,
    /// wenn ein Modell (statt "heuristic") gewählt wurde.
    fn load_net(&mut self, model_path: String) -> PyResult<()> {
        if self.net_path.as_deref() == Some(model_path.as_str()) {
            return Ok(()); // schon geladen
        }
        let net = Net::load(&model_path, crate::features::INPUT_SIZE)
            .map_err(|e| PyValueError::new_err(format!("Netz konnte nicht geladen werden: {e}")))?;
        self.net = Some(net);
        self.net_path = Some(model_path);
        Ok(())
    }

    /// Deaktiviert den Netz-Modus (zurück auf Heuristik), ohne das geladene
    /// Netz zu verwerfen (erneutes `load_net` mit demselben Pfad bleibt billig).
    fn clear_net(&mut self) {
        self.net = None;
        self.net_path = None;
    }

    // ── Zustand ───────────────────────────────────────────────────────────────

    /// Vollständiges Frontend-JSON (als String; Python: json.loads).
    fn state_json(&self) -> String {
        state_to_json(&self.game.state, self.scoring_confirmed).to_string()
    }

    /// NN-Feature-Vektor (Länge = `features::INPUT_SIZE`; Port von
    /// `state_to_tensor`) — für die Phase-B-Paritätsprüfung gegen Python.
    fn features(&self) -> Vec<f32> {
        crate::features::state_to_features(&state_to_json(&self.game.state, self.scoring_confirmed))
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

    fn apply_tiling(
        &mut self,
        player: usize,
        pattern_row: usize,
        slot_row: usize,
        slot_col: usize,
        space_index: usize,
    ) -> PyResult<i32> {
        if self.game.state.phase != Phase::Tiling {
            return Err(PyValueError::new_err("Nicht in der Tiling-Phase."));
        }
        let action = TilingAction { pattern_row, slot_row, slot_col, space_index };
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

    /// Führt EINEN KI-Zug für den aktuellen Spieler aus und gibt
    /// `{applied, phase, action, done, debug}` als JSON zurück. Drafting → MCTS
    /// (mit Debug-Baum); Tiling → exakter DFS-Solver (schlankes Debug, kein Baum).
    /// Server ruft dies nur, wenn die KI am Zug ist.
    #[pyo3(signature = (simulations=300, log=false))]
    fn ai_step_json(&mut self, simulations: u32, log: bool) -> PyResult<String> {
        match self.game.state.phase {
            Phase::Tiling => self.ai_tiling_step(),
            Phase::Drafting => self.ai_drafting_step(simulations, log),
            other => Ok(json!({
                "applied": false,
                "phase": other.as_str(),
                "reason": "keine KI-Aktion (terminale Phase?)",
            })
            .to_string()),
        }
    }

    /// Wie `ai_step_json`, aber mit dem geladenen Netz (`load_net` zuvor
    /// aufrufen) statt der Heuristik. Tiling bleibt der exakte DFS-Solver
    /// (netzunabhängig, wie im Self-Play/Arena). Blattbewertung ist immer der
    /// exakte DFS-Solver (kein Value-Head mehr). Fehler, falls kein Netz
    /// geladen ist.
    #[pyo3(signature = (simulations=200, c_puct=1.5, log=false))]
    fn ai_step_net_json(&mut self, simulations: u32, c_puct: f64, log: bool) -> PyResult<String> {
        match self.game.state.phase {
            Phase::Tiling => self.ai_tiling_step(),
            Phase::Drafting => self.ai_drafting_net_step(simulations, c_puct, log),
            other => Ok(json!({
                "applied": false,
                "phase": other.as_str(),
                "reason": "keine KI-Aktion (terminale Phase?)",
            })
            .to_string()),
        }
    }

    /// Wie `ai_debug_json`, aber mit dem geladenen Netz: Analyse-Dict mit
    /// echten Netz-Priors (`net_prob`/`net_prob_norm`) UND PUCT-Such-Stats
    /// je Wurzelkind, ohne einen Zug auszuführen.
    #[pyo3(signature = (simulations=200, c_puct=1.5))]
    fn ai_debug_net_json(&mut self, simulations: u32, c_puct: f64) -> PyResult<String> {
        let net = self.net.as_ref().ok_or_else(|| {
            PyValueError::new_err("Kein Netz geladen — load_net() zuvor aufrufen.")
        })?;
        let sims = dynamic_sims(simulations, drafting_actions(&self.game.state).len());
        let (_chosen, analysis) =
            net_search_with_tree(net, &self.game.state, sims, c_puct, false, &mut self.rng, None);
        Ok(analysis.to_string())
    }

    /// Analysiert die aktuelle Stellung per MCTS OHNE Zug auszuführen
    /// (für /api/ai/debug). Gibt das debug.html-Analyse-Dict zurück.
    #[pyo3(signature = (simulations=300))]
    fn ai_debug_json(&mut self, simulations: u32) -> String {
        let n = drafting_actions(&self.game.state).len();
        let sims = dynamic_sims(simulations, n);
        let (_chosen, analysis) = search_with_tree(
            &self.game.state,
            sims,
            AI_C,
            &mut self.rng,
            AI_TREE_DEPTH,
            AI_TREE_TOPK,
            None,
        );
        analysis.to_string()
    }

    /// Vollständiger MCTS-Schleifen-Trace (Selection/Expansion/Bewertung/Backprop
    /// je Simulation) als Text — für /api/ai/debug_log. Volle dynamische Sim-Zahl
    /// (`simulations` = Basis). Wendet KEINEN Zug an; nur in der Drafting-Phase.
    #[pyo3(signature = (simulations=300))]
    fn ai_debug_log(&mut self, simulations: u32) -> String {
        if self.game.state.phase != Phase::Drafting {
            return "(Zustand nicht in der Drafting-Phase — kein MCTS-Log)".to_string();
        }
        let n = drafting_actions(&self.game.state).len();
        let sims = dynamic_sims(simulations, n);
        search_log_text(&self.game.state, sims, AI_C, &mut self.rng)
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

// Interne KI-Schritt-Helfer (kein PyO3-Export).
impl PyGame {
    /// Drafting-Zug per MCTS (mit Debug-Baum). `log=true` schneidet den exakten
    /// Such-Trace mit und hängt ihn als `log_text` an.
    fn ai_drafting_step(&mut self, simulations: u32, log: bool) -> PyResult<String> {
        let actions = drafting_actions(&self.game.state);
        if actions.is_empty() {
            return Ok(json!({
                "applied": false,
                "phase": self.game.state.phase.as_str(),
                "reason": "keine Drafting-Aktion",
            })
            .to_string());
        }

        let mut lines: Vec<String> = Vec::new();
        let mv: SearchMove;
        let analysis: Value;
        if actions.len() == 1 {
            // Nur eine legale Aktion → direkt wählen, keine Simulationen
            // (eine erzwungene Wahl muss nicht durchgerechnet werden).
            mv = SearchMove::Draft(actions.into_iter().next().unwrap());
            let mj = search_move_json(&mv, Some(&self.game.state)); // { type, description, category, move }
            if log {
                lines.push("Nur eine legale Drafting-Aktion — direkt gewaehlt (0 Simulationen).".to_string());
            }
            analysis = json!({
                "simulations": 0,
                "num_actions": 1,
                "max_depth": 0,
                "single_action": true,
                "moves": [ {
                    "description": mj["description"],
                    "category": mj["category"],
                    "action_id": mj["type"],
                    "mcts_share": 1.0,
                    "mcts_visits": 0,
                    "mcts_win_pct": null,
                    "max_depth": 0,
                    "chosen": true,
                } ],
            });
        } else {
            let sims = dynamic_sims(simulations, actions.len());
            let logger = if log { Some(&mut lines) } else { None };
            let (chosen, a) = search_with_tree(
                &self.game.state,
                sims,
                AI_C,
                &mut self.rng,
                AI_TREE_DEPTH,
                AI_TREE_TOPK,
                logger,
            );
            match chosen {
                Some(m) => {
                    mv = m;
                    analysis = a;
                }
                None => {
                    return Ok(json!({
                        "applied": false,
                        "phase": self.game.state.phase.as_str(),
                        "reason": "keine Drafting-Aktion",
                    })
                    .to_string());
                }
            }
        }
        // Log-Text VOR dem Anwenden bauen (Kopf nutzt den Pre-Move-Zustand).
        let log_text = if log {
            let mut t = search_log_header(&self.game.state, &analysis);
            for l in &lines {
                t.push_str(l);
                t.push('\n');
            }
            Some(t)
        } else {
            None
        };

        let SearchMove::Draft(a) = &mv;
        // Stapel-Zieh-Menge/-Kachel sind nicht Teil der Policy-ID (siehe
        // resolve_chosen_action) -- erst hier, direkt vor dem Anwenden,
        // aufloesen, und Anzeige-JSON/Log NACH der Aufloesung bauen, damit sie
        // zum tatsaechlich ausgefuehrten Zug passen.
        let resolved = crate::self_play::resolve_chosen_action(&self.game.state, a.clone(), &mut self.rng);
        let resolved_mv = SearchMove::Draft(resolved.clone());
        let action_json = search_move_json(&resolved_mv, Some(&self.game.state));
        map_err(self.game.apply_drafting(&resolved))?;

        let mut obj = serde_json::Map::new();
        obj.insert("applied".into(), json!(true));
        obj.insert("phase".into(), json!(self.game.state.phase.as_str()));
        obj.insert("action".into(), action_json);
        obj.insert("done".into(), json!(self.game.is_over()));
        obj.insert("debug".into(), analysis);
        if let Some(t) = log_text {
            obj.insert("log_text".into(), json!(t));
        }
        Ok(Value::Object(obj).to_string())
    }

    /// Drafting-Zug per Netz-PUCT (mit Priors+Such-Stats-Analyse). Erfordert
    /// zuvor `load_net()`. `log=true` hängt einen vollen Sim-für-Sim-Trace an
    /// (Selection/Expansion/Eval/Backprop je Simulation, analog zur Heuristik).
    fn ai_drafting_net_step(&mut self, simulations: u32, c_puct: f64, log: bool) -> PyResult<String> {
        let net = self.net.as_ref().ok_or_else(|| {
            PyValueError::new_err("Kein Netz geladen — load_net() zuvor aufrufen.")
        })?;
        let actions = drafting_actions(&self.game.state);
        if actions.is_empty() {
            return Ok(json!({
                "applied": false,
                "phase": self.game.state.phase.as_str(),
                "reason": "keine Drafting-Aktion",
            })
            .to_string());
        }

        let sims = dynamic_sims(simulations, actions.len());
        let mut lines: Vec<String> = Vec::new();
        let logger = if log { Some(&mut lines) } else { None };
        let (chosen, analysis) =
            net_search_with_tree(net, &self.game.state, sims, c_puct, false, &mut self.rng, logger);
        let a = match chosen {
            Some(a) => a,
            None => {
                return Ok(json!({
                    "applied": false,
                    "phase": self.game.state.phase.as_str(),
                    "reason": "keine Drafting-Aktion",
                })
                .to_string());
            }
        };

        // Log-Text VOR dem Anwenden bauen (Kopf nutzt den Pre-Move-Zustand).
        let log_text = if log {
            let mut t = net_mcts::net_search_log_header(&self.game.state, &analysis);
            for l in &lines {
                t.push_str(l);
                t.push('\n');
            }
            Some(t)
        } else {
            None
        };

        let resolved = crate::self_play::resolve_chosen_action(&self.game.state, a, &mut self.rng);
        let action_json = search_move_json(&SearchMove::Draft(resolved.clone()), Some(&self.game.state));
        map_err(self.game.apply_drafting(&resolved))?;

        let mut obj = serde_json::Map::new();
        obj.insert("applied".into(), json!(true));
        obj.insert("phase".into(), json!(self.game.state.phase.as_str()));
        obj.insert("action".into(), action_json);
        obj.insert("done".into(), json!(self.game.is_over()));
        obj.insert("debug".into(), analysis);
        if let Some(t) = log_text {
            obj.insert("log_text".into(), json!(t));
        }
        Ok(Value::Object(obj).to_string())
    }

    /// Tiling-Zug per exaktem DFS-Solver. Wendet den optimalen nächsten Schritt
    /// an; liefert ein schlankes Debug-Dict (kein MCTS-Baum).
    fn ai_tiling_step(&mut self) -> PyResult<String> {
        let pi = self.game.state.current_player;
        let optimal = solve_round_final_score(&self.game.state, pi);
        // Exakte Chip-Allokationssuche für den ECHTEN Zug (einmal pro Schritt).
        // Waehrend des Tilings werden keine neuen Kuppelplatten gelegt (Regel) --
        // liefert der Solver `End`, ist die Tiling-Phase fuer diesen Spieler
        // wirklich zu Ende (offene volle Reihen ohne Slot bleiben liegen).
        let step = best_first_step_exact(&self.game.state, pi);

        let (typ, desc, cat, mv): (&str, String, &str, Value) = match step {
            TilingStep::Place(ta) => {
                map_err(self.game.apply_single_tiling(pi, &ta))?;
                (
                    "tiling",
                    format!("Tiling R{} → Slot({},{}) Sp{}", ta.pattern_row + 1, ta.slot_row, ta.slot_col, ta.space_index),
                    "tiling",
                    tiling_action_to_dict(&ta),
                )
            }
            TilingStep::Chips { row, chips } => {
                // Exakt die vom Solver gewählte Plättchen-Allokation anwenden.
                if !apply_bonus_chips_with(&mut self.game.state.players[pi], row, &chips) {
                    return Err(PyValueError::new_err("KI: Chip-Komplettierung fehlgeschlagen."));
                }
                ("use_chips", format!("Chips R{}", row + 1), "chip", json!({ "type": "use_chips", "pattern_row": row }))
            }
            TilingStep::End => {
                map_err(self.game.apply_tiling(&TilingMove::EndTiling { player: pi }, &mut self.rng))?;
                ("end_tiling", "Tiling beenden".to_string(), "pass", json!({ "type": "end_tiling" }))
            }
        };

        // Schlankes, debug.html-kompatibles Debug-Dict (kein Baum).
        let debug = json!({
            "current_player": pi,
            "ai_player": pi,
            "value": Value::Null,
            "win_pct": Value::Null,
            "has_net": false,
            "simulations": 0,
            "num_actions": 1,
            "max_depth": 0,
            "ai_action": 0,
            "solver": "dfs",
            "dfs_optimal_score": optimal,
            "moves": [json!({
                "action_id": 0,
                "type": typ,
                "description": desc.clone(),
                "category": cat,
                "net_prob": Value::Null,
                "net_prob_norm": Value::Null,
                "mcts_visits": 0,
                "mcts_share": 1.0,
                "mcts_q": Value::Null,
                "mcts_win_pct": Value::Null,
                "max_depth": 0,
                "shaping": optimal as f64,
                "chosen": true,
            })],
            "tree": Value::Null,
        });

        Ok(json!({
            "applied": true,
            "phase": self.game.state.phase.as_str(),
            "action": json!({ "type": typ, "description": desc, "category": cat, "move": mv }),
            "done": self.game.is_over(),
            "debug": debug,
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::setup_new_game;
    use crate::tile::TileColor::Rot;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    /// Während des Tilings werden keine neuen Kuppelplatten gelegt (Regel): eine
    /// volle Pattern-Reihe ohne bereits belegten passenden Slot bleibt liegen --
    /// weder der Solver noch `generate_tiling_actions` bieten dafür eine Aktion
    /// an. Das ist kein Deadlock (die Reihe wartet auf eine künftige
    /// Drafting-Platzierung oder landet irgendwann auf der Strafleiste), kein
    /// künstliches Nachziehen einer neuen Platte mehr nötig.
    #[test]
    fn no_tiling_action_for_row_without_templated_slot() {
        let mut rng = StdRng::seed_from_u64(99);
        let mut s = setup_new_game(["P1".into(), "P2".into()], 0, &mut rng);
        for p in s.players.iter_mut() {
            p.start_tile_pending = false;
        }
        // Reihe 0 (cap 1) voll mit Rot, Kuppel-Grid leer → keine Aktion möglich.
        s.players[0].pattern_lines[0].add_tiles(&[Rot]);

        assert!(matches!(best_first_step_exact(&s, 0), TilingStep::End));
        assert!(generate_tiling_actions(&s, 0).is_empty());
    }
}
