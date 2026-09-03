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

use crate::game::{apply_start_placement, drafting_actions, Game, TilingMove};
use crate::mcts::{dynamic_sims, search_log_header, search_log_text, search_move_json, search_with_tree, SearchMove};
use crate::moves::{Action, DrawFromStackMove, Move, PlaceAction, PlaceDomeTileMove, TakeAction, TakeBonusChipMove, TakeSource};
use crate::net::Net;
use crate::net_mcts::{self, net_search_with_tree};
use crate::round_end::{apply_bonus_chips_to_row, apply_bonus_chips_with, find_unplaceable_rows, TilingAction};
#[cfg(test)]
use crate::round_end::generate_tiling_actions;
use crate::scoring::{has_exclusion_conflict, sample_valid_scoring_ids};
use crate::serialize::{serialize_stack_peek, state_to_json, tiling_action_to_dict};
use crate::tiling_solver::{
    best_first_step_exact_or_valued, best_first_step_exact_or_valued_envelope, solve_round_final_score,
    TilingStep,
};
use crate::state::{GameState, Phase};
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
    /// PREREG_search_rng_split.md: fortlaufender Zaehler ECHTER KI-Such-
    /// Entscheide (`ai_drafting_step`/`ai_drafting_net_step`), NICHT der
    /// reinen Debug-Endpunkte (`debug_rng` oben ist dafuer schon vom
    /// Partie-RNG entkoppelt, siehe dortiger Kommentar). Zusammen mit
    /// `seed` baut jeder echte Such-Zug daraus einen EIGENEN RNG
    /// (`net_mcts::derive_search_seed`) statt `self.rng` zu verbrauchen --
    /// `self.rng` verschiebt sich dann nur noch durch echte
    /// Zustands-Ereignisse (`PyGame::new`, `end_tiling`/`ai_tiling_step`s
    /// `EndTiling`), unabhaengig von `simulations`.
    move_seq: u64,
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
            net: None, net_path: None, move_seq: 0,
        }
    }

    /// Lädt ein ONNX-Netz für den Netz-KI-Modus (einmalig pro Modellpfad — wird
    /// bei gleichem Pfad übersprungen). Server ruft dies bei `/api/new_game`,
    /// wenn ein Modell (statt "heuristic") gewählt wurde.
    fn load_net(&mut self, model_path: String) -> PyResult<()> {
        if self.net_path.as_deref() == Some(model_path.as_str()) {
            return Ok(()); // schon geladen
        }
        // Task #11 Phase 2 (M3.5): `load_auto` statt `load(path, INPUT_SIZE)`
        // -- der Server-Modellwähler (`/api/new_game`) muss auch 2D-Modelle
        // laden können, ohne fest den flachen 708er-Input zu erzwingen.
        // Byte-identisch für Bestandsmodelle (Rang 2 -> InputLayout::Flat).
        let net = Net::load_auto(&model_path)
            .map_err(|e| PyValueError::new_err(format!("Netz konnte nicht geladen werden: {e}")))?;
        self.net = Some(net);
        self.net_path = Some(model_path);
        Ok(())
    }

    /// Roher Netz-Forward-Pass für einen beliebigen Feature-Vektor (Länge
    /// muss `INPUT_SIZE` treffen) -- KEIN Spielzustand-Bezug, nur fürs
    /// Rust-Paritätstesten gegen `export_onnx.py`s `.onnx.ref.txt`
    /// (deterministischer Zufalls-Input+Referenz-Output je Modell-Export).
    /// Gibt `(policy, value, moon, points)` zurück.
    fn net_eval_raw(
        &self,
        feats: Vec<f32>,
    ) -> PyResult<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)> {
        let net = self.net.as_ref().ok_or_else(|| {
            PyValueError::new_err("Kein Netz geladen — load_net() zuvor aufrufen.")
        })?;
        net.eval(&feats).map_err(|e| PyValueError::new_err(format!("Netz-Fehler: {e}")))
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
        let ui = json!({
            "type": "stone",
            "source": source,
            "color": color,
            "row": row,
            "factory_id": factory_id,
            "moon_order": m.take.moon_order.iter().map(|c| c.value()).collect::<Vec<_>>(),
        });
        map_err(self.log_and_apply(&Action::Stone(m), ui))
    }

    /// Bleibt nach aussen ein ATOMARER Zug (Tile+Slot+Rotation in einem Aufruf,
    /// wie server.py es erwartet) -- intern seit Baustein B zwei aufeinander-
    /// folgende `apply_drafting`-Aufrufe (Stufe 1: Slot waehlen, Stufe 2:
    /// Rotation), da die KI-Suche (net_mcts.rs/mcts.rs) diese Zerlegung fuer
    /// den kleineren Verzweigungsfaktor braucht.
    #[pyo3(signature = (tile_id, slot_row, slot_col, rotation=0))]
    fn apply_dome(&mut self, tile_id: usize, slot_row: usize, slot_col: usize, rotation: u32) -> PyResult<()> {
        let m = PlaceDomeTileMove { dome_tile_id: tile_id, slot_row, slot_col, rotation: 0 };
        // EINE `#a`-Zeile fuer den nach aussen atomaren Zug (Slot + Rotation).
        // `id` deckt die Slot-Stufe ab, `id_rotation` die zweite -- die ID
        // allein kann die Rotation nicht tragen (eigene Stufe im Action Space,
        // siehe features.rs::action_to_id/choose_dome_rotation).
        let ui = json!({
            "type": "dome_display",
            "id_rotation": crate::self_play::action_to_id_direct(
                &self.game.state, &Action::ChooseDomeRotation(rotation)),
            "tile_id": tile_id,
            "slot_row": slot_row,
            "slot_col": slot_col,
            "rotation": rotation,
        });
        map_err(self.log_and_apply(&Action::ChooseDomeSlot(m), ui))?;
        map_err(self.game.apply_drafting(&Action::ChooseDomeRotation(rotation)))
    }

    /// Aktion A, Schritt 1: eine weitere verdeckte Kuppelplatte ziehen (−1
    /// Pkt). Gibt den Typ zurück (Rückseite: "special"/"wild"), NICHT die
    /// Vorderseite -- der Zug endet nicht, `apply_dome_stack_choose` oder ein
    /// weiterer `apply_dome_stack_peek` folgt.
    fn apply_dome_stack_peek(&mut self) -> PyResult<String> {
        map_err(self.log_and_apply(&Action::DrawStackPeek, json!({ "type": "dome_stack_peek" })))?;
        let last = self.game.state.pending_stack_draw.last().ok_or_else(|| {
            PyValueError::new_err("Keine Kachel gezogen (interner Fehler).")
        })?;
        Ok(if last.is_special_type() { "special".into() } else { "wild".into() })
    }

    /// `return_order`: Reihenfolge, in der die NICHT gewählten gezogenen
    /// Platten zurück unter den Stapel gelegt werden (Regelwerk: "in
    /// beliebiger Reihenfolge") -- tile_ids, erstes Element zuerst
    /// zurückgelegt. `None`/weggelassen füllt die Ziehreihenfolge (kanonisch,
    /// wie bei der KI) -- bei ≤1 übriger Platte ohnehin die einzig mögliche
    /// Reihenfolge, das Frontend fragt den Menschen nur bei 2+ übrigen.
    #[pyo3(signature = (chosen_id, slot_row, slot_col, rotation=0, return_order=None))]
    fn apply_dome_stack_choose(
        &mut self,
        chosen_id: usize,
        slot_row: usize,
        slot_col: usize,
        rotation: u32,
        return_order: Option<Vec<usize>>,
    ) -> PyResult<()> {
        let return_order = return_order.unwrap_or_else(|| {
            self.game
                .state
                .pending_stack_draw
                .iter()
                .filter(|t| t.tile_id != chosen_id)
                .map(|t| t.tile_id)
                .collect()
        });
        // Bleibt nach aussen atomar -- siehe `apply_dome`-Kommentar.
        let m = DrawFromStackMove { chosen_id, slot_row, slot_col, rotation: 0, return_order };
        let ui = json!({
            "type": "dome_stack_choose",
            "id_rotation": crate::self_play::action_to_id_direct(
                &self.game.state, &Action::ChooseDomeRotation(rotation)),
            "chosen_id": chosen_id,
            "slot_row": slot_row,
            "slot_col": slot_col,
            "rotation": rotation,
            "return_order": m.return_order.clone(),
        });
        map_err(self.log_and_apply(&Action::ChooseDrawStackSlot(m), ui))?;
        map_err(self.game.apply_drafting(&Action::ChooseDomeRotation(rotation)))
    }

    fn apply_bonus_chip(&mut self, factory_id: usize) -> PyResult<()> {
        map_err(self.log_and_apply(
            &Action::BonusChip(TakeBonusChipMove { factory_id }),
            json!({ "type": "bonus_chip", "factory_id": factory_id }),
        ))
    }

    fn apply_pass(&mut self) -> PyResult<()> {
        // BEWUSST OHNE `#a`-Zeile (PREREG_action_id_logging.md S2): `Pass` ist
        // der einzige Drafting-Zug, der NICHTS ins Log schreibt, und der
        // Replay verlaesst sich darauf -- `Replayer.ensure_drafting_actor`
        // (tools/analyze_game_log.py) bricht ab, wenn `apply_pass` die
        // Log-Laenge veraendert. Passes werden dort ohnehin aus dem Spieler-
        // wechsel rekonstruiert, nicht aus dem Log gelesen.
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

    /// Wie `apply_tiling_chips`, aber mit EXPLIZIT vorgegebener Chip-Auswahl
    /// (Indizes in `players[player].bonus_chips`).
    ///
    /// Warum es das braucht (Vorfall 2026-08-29, `docs/pitfalls.md`): die KI
    /// waehlt ihre Allokation exakt (`ai_tiling_step` unten, Solver-Schritt
    /// `TilingStep::Chips` -> `apply_bonus_chips_with`), `apply_tiling_chips`
    /// dagegen waehlt GREEDY (`round_end.rs::greedy_chip_indices`: ohne zwei
    /// farbgleiche die ersten drei der Hand). Die 🎫-Logzeile nennt die
    /// verbrauchten Chips nicht, `tools/analyze_game_log.py` musste geloggte
    /// KI-Vollendungen deshalb greedy nachspielen -- und verbrannte dabei
    /// Chips, die die echte KI behalten hatte, bis Runden spaeter eine real
    /// gespielte Vollendung unmoeglich wurde.
    ///
    /// Verhalten: dieselbe Regelpruefung wie beide Bestandspfade
    /// (`round_end::chips_complete` via `apply_bonus_chips_with`) PLUS die
    /// Top-down-Sperre, die sonst nur `apply_bonus_chips_to_row` durchsetzt
    /// (Engine-Audit U1, `round_end.rs:464`) -- diese Bindung ist damit nie
    /// permissiver als der Menschen-Pfad, sie darf nur waehlen. Logtext
    /// zeichengleich zu `apply_tiling_chips`, damit die Zeilen-Gegenprobe des
    /// Replayers beide Pfade gleich sieht.
    fn apply_tiling_chips_with(
        &mut self,
        player: usize,
        pattern_row: usize,
        chips: Vec<usize>,
    ) -> PyResult<()> {
        if (pattern_row as i32) < self.game.state.players[player].tiled_max_row {
            return Err(PyValueError::new_err(format!(
                "Reihe {} ist top-down gesperrt.",
                pattern_row + 1
            )));
        }
        if !apply_bonus_chips_with(&mut self.game.state.players[player], pattern_row, &chips) {
            return Err(PyValueError::new_err(format!(
                "Reihe {} nicht mit dieser Chip-Auswahl komplettierbar.",
                pattern_row + 1
            )));
        }
        let name = self.game.state.players[player].name.clone();
        self.game
            .state
            .log_event(format!("🎫 {name} komplettiert Reihe {} mit Bonus-Chips!", pattern_row + 1));
        Ok(())
    }

    /// Alle Chip-Auswahlen, die Reihe `pattern_row` komplettieren koennten --
    /// als JSON-Liste von Index-Listen (`round_end::chip_allocations`,
    /// dedupliziert nach Farb-Signatur). Damit bleibt die REGEL in der Engine:
    /// Aufrufer (der Replayer) waehlt nur aus, statt `chips_complete`
    /// nachzubauen. Die Top-down-Sperre wird hier mitgefiltert, damit die
    /// Kandidatenliste nie etwas anbietet, das `apply_tiling_chips_with`
    /// anschliessend ablehnt.
    fn chip_allocations_json(&self, player: usize, pattern_row: usize) -> String {
        let p = &self.game.state.players[player];
        if (pattern_row as i32) < p.tiled_max_row {
            return "[]".to_string();
        }
        let allocs = crate::round_end::chip_allocations(p, pattern_row);
        serde_json::to_string(&allocs).unwrap_or_else(|_| "[]".to_string())
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
    /// je Wurzelkind, ohne einen Zug auszuführen. Task #95: `collect_trace=true`
    /// -- der EINZIGE Aufrufer, der den ROOT-Value-Breakdown (`value_debug`)
    /// UND den granularen Gumbel-Trace (`gumbel_trace`) anfordert (reiner
    /// Analyse-Endpunkt für `/api/ai/debug`, kein Zug wird angewendet, kein
    /// Self-Play-/Arena-Performance-Pfad betroffen).
    #[pyo3(signature = (simulations=200, c_puct=1.5))]
    fn ai_debug_net_json(&self, simulations: u32, c_puct: f64) -> PyResult<String> {
        let net = self.net.as_ref().ok_or_else(|| {
            PyValueError::new_err("Kein Netz geladen — load_net() zuvor aufrufen.")
        })?;
        let sims = net_mcts::net_effective_sims(simulations, drafting_actions(&self.game.state).len());
        let mut rng = self.debug_rng();
        let (_chosen, analysis) =
            net_search_with_tree(net, &self.game.state, sims, c_puct, false, &mut rng, None, true);
        Ok(analysis.to_string())
    }

    /// Analysiert die aktuelle Stellung per MCTS OHNE Zug auszuführen
    /// (für /api/ai/debug). Gibt das debug.html-Analyse-Dict zurück.
    #[pyo3(signature = (simulations=300))]
    fn ai_debug_json(&self, simulations: u32) -> String {
        let n = drafting_actions(&self.game.state).len();
        let sims = dynamic_sims(simulations, n);
        let mut rng = self.debug_rng();
        let (_chosen, analysis) = search_with_tree(
            &self.game.state,
            sims,
            AI_C,
            &mut rng,
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
    fn ai_debug_log(&self, simulations: u32) -> String {
        if self.game.state.phase != Phase::Drafting {
            return "(Zustand nicht in der Drafting-Phase — kein MCTS-Log)".to_string();
        }
        let n = drafting_actions(&self.game.state).len();
        let sims = dynamic_sims(simulations, n);
        let mut rng = self.debug_rng();
        search_log_text(&self.game.state, sims, AI_C, &mut rng)
    }

    /// Platziert die Startkachel der KI per einfacher Farb-Häufigkeits-Heuristik
    /// (gemeinsamer Helfer mit Self-Play/Arena, siehe `self_play::choose_start_placement`).
    /// Gibt das gewählte Move-Dict zurück.
    fn ai_start_tile_json(&mut self, player: usize) -> PyResult<String> {
        let (tile_id, r, c, rot) = crate::self_play::choose_start_placement(&self.game.state, player)
            .ok_or_else(|| PyValueError::new_err("Keine Startkachel platzierbar."))?;
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
    /// PREREG_action_id_logging.md, Stueck S2: schreibt EINE maschinenlesbare
    /// Zeile je angewandter Drafting-Aktion in den Log-Strom -- die
    /// Aktions-ID aus DEMSELBEN Raum, gegen den der Policy-Kopf trainiert
    /// (`features::action_to_id`, `NUM_ACTIONS = 406`), plus die kanonischen
    /// Felder als Rueckfallebene, falls sich der Raum spaeter verschiebt.
    ///
    /// ```text
    /// #a {"id":137,"p":0,"a":{"type":"stone", ...}}
    /// ```
    ///
    /// DREI Eigenschaften, die beim Aendern zu halten sind:
    ///
    ///  1. **Nur der gespeicherte Strom.** Die Zeile geht in `state.log` und
    ///     damit ueber `log_since` in die Datei -- die UI-Ansicht filtert sie
    ///     wieder heraus (`serialize.rs::state_to_json`, Nutzer-Vorgabe
    ///     2026-08-18: "am log der in index.html angezeigt wird brauchst
    ///     nichts ändern").
    ///  2. **VOR dem Anwenden.** `action_to_id_direct` liest Fabrik- und
    ///     Ablage-POSITIONEN, die der Zug selbst verschiebt; und `p` ist der
    ///     Spieler am Zug, nicht der danach.
    ///  3. **Eigenes Praefix, kein bestehender Logtext geaendert.** Die drei
    ///     Leser am Logtext (`analyze_game_log.py`, `plate_points_from_arena.py`,
    ///     `tools/hooks/pre-push`) bleiben unberuehrt -- geprueft am
    ///     2026-08-18 per Injektion in eine echte Partie (par.4-Sperre).
    ///
    /// Kein `log_event`: das wuerde das "[Rn] "-Praefix voranstellen und die
    /// Zeile damit in die Textklassifikation der Leser ziehen.
    fn push_action_id_line(&mut self, id: usize, ui: Value) {
        let p = self.game.state.current_player;
        self.game
            .state
            .log
            .push(format!("#a {}", json!({ "id": id, "p": p, "a": ui })));
    }

    /// `push_action_id_line` + `apply_drafting`, atomar: schlaegt das Anwenden
    /// fehl, verschwindet auch die Zeile wieder (sonst behauptete das Log eine
    /// Aktion, die nie stattgefunden hat).
    fn log_and_apply(&mut self, a: &Action, ui: Value) -> Result<(), String> {
        let id = crate::self_play::action_to_id_direct(&self.game.state, a);
        let mark = self.game.state.log.len();
        self.push_action_id_line(id, ui);
        match self.game.apply_drafting(a) {
            Ok(()) => Ok(()),
            Err(e) => {
                // Nur die EIGENE Zeile zuruecknehmen. Zwischen `mark` und dem
                // Fehler kann bei mehrstufigen Zuegen (Kuppel: Slot, dann
                // Rotation) schon echter Logtext stehen -- ein `truncate(mark)`
                // wuerde den mit loeschen.
                if self.game.state.log.get(mark).is_some_and(|l| l.starts_with("#a ")) {
                    self.game.state.log.remove(mark);
                }
                Err(e)
            }
        }
    }
}

// Interne KI-Schritt-Helfer (kein PyO3-Export).
impl PyGame {
    /// Separate RNG für reine Debug-/Analyse-Endpunkte (`ai_debug_*`): Die
    /// Suche braucht Zufall, darf aber den Spiel-RNG NICHT fortschreiten
    /// lassen — sonst verschiebt ein KI-Debugger-Aufruf während der Partie
    /// unsichtbar den RNG-Zustand, und das Spiel ist ab der nächsten
    /// Beutel-Neumischung (`Bag::refill_from_tower`) nicht mehr aus dem
    /// Spiel-Log reproduzierbar (bricht die Replay-Validierung in
    /// tools/analyze_game_log.py). `StdRng` ist bewusst nicht klonbar,
    /// daher eine frische, vom Partie-Seed abgeleitete Instanz pro Aufruf
    /// (deterministisch: gleiche Stellung → gleiche Analyse).
    fn debug_rng(&self) -> StdRng {
        StdRng::seed_from_u64(self.seed ^ 0xDEB0_6DEB_06DE_B06D)
    }
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
            // PREREG_search_rng_split.md: eigener, aus (seed, move_seq)
            // abgeleiteter RNG statt `self.rng` -- siehe Feld-Kommentar an
            // `PyGame::move_seq`. `self.rng` bleibt dadurch nur noch durch
            // echte Zustands-Ereignisse belegt, unabhaengig von `simulations`.
            self.move_seq += 1;
            let mut search_rng = StdRng::seed_from_u64(net_mcts::derive_search_seed(self.seed, self.move_seq));
            let (chosen, a) = search_with_tree(
                &self.game.state,
                sims,
                AI_C,
                &mut search_rng,
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

        // Heuristik (Stufe 1) braucht die sequenzielle Stapel-Zieh-Aufloesung
        // nicht (Nutzer-Vorgabe) -- einfach die gewaehlte Aktion einmalig
        // anwenden. Bei DrawStackPeek endet der Zug nicht; ein Folgeaufruf
        // dieser Methode (naechster KI-Zug) entscheidet dann ganz normal
        // ueber weiterziehen/waehlen, wie der Rest der Heuristik-Suche auch.
        let action_json = search_move_json(&mv, Some(&self.game.state));
        let SearchMove::Draft(a) = &mv;
        // PREREG_action_id_logging.md S2: die KI-Aktion traegt ihre ID genauso
        // wie die menschliche -- sonst waere nur die halbe Partie exakt
        // replaybar. `action_to_env_dict` liefert die kanonischen Felder, die
        // `action_to_id` konsumiert (Rueckfallebene, par.5).
        // `Pass` bleibt aussen vor -- gleiche Begruendung wie bei `apply_pass`
        // (er erzeugt keine Textzeile, und der Replay rekonstruiert ihn aus dem
        // Spielerwechsel). Ohne diese Ausnahme schriebe die KI eine `#a`-Zeile
        // fuer einen Zug, den der Mensch-Pfad still laesst.
        let mark_len = self.game.state.log.len();
        let geloggt = !matches!(a, Action::Pass);
        if geloggt {
            let id = crate::self_play::action_to_id_direct(&self.game.state, a);
            let ui = crate::self_play::action_to_env_dict(&self.game.state, a);
            self.push_action_id_line(id, ui);
        }
        if let Err(e) = self.game.apply_drafting(a) {
            if geloggt
                && self.game.state.log.get(mark_len).is_some_and(|l| l.starts_with("#a "))
            {
                self.game.state.log.remove(mark_len);
            }
            return Err(PyValueError::new_err(e));
        }

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
    /// Task #95: `collect_trace=true` -- anders als die Massen-Aufrufstellen
    /// (Self-Play/Arena laufen NIE über `net_search_with_tree`, sondern über
    /// `net_search_drafting_action`/`net_root_child_stats*`, siehe dortige
    /// Kommentare) ist dies ein EINZELNER Zug pro menschlichem Klick im
    /// Server (Mensch-vs-KI) -- der zusätzliche Root-Value-Forward-Pass fällt
    /// hier nicht ins Gewicht, macht die Debug-Historie (`/api/ai/debug_history`,
    /// `debug.html`) aber erst nutzbar (sonst wäre `value_debug`/`gumbel_trace`
    /// dort permanent `null`).
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

        let sims = net_mcts::net_effective_sims(simulations, actions.len());
        let mut lines: Vec<String> = Vec::new();
        let logger = if log { Some(&mut lines) } else { None };
        // PREREG_search_rng_split.md: siehe `ai_drafting_step`-Kommentar --
        // eigener RNG statt `self.rng`.
        self.move_seq += 1;
        let mut search_rng = StdRng::seed_from_u64(net_mcts::derive_search_seed(self.seed, self.move_seq));
        let (chosen, analysis) =
            net_search_with_tree(net, &self.game.state, sims, c_puct, false, &mut search_rng, logger, true);
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

        // Stufe 2 (Netz): DrawStackPeek wird ueber apply_chosen_action komplett
        // aufgeloest (mehrere echte Zuege bis Wahl+Platzierung) -- die
        // zurueckgegebene Aktion ist die tatsaechlich final ausgefuehrte
        // (bei DrawStackPeek also das konkrete DrawStack, nicht der Peek).
        // `a` stammt aus `drafting_actions()`, kann bei zweistufigen Zuegen
        // (Kuppel/Stapel-Rotation) aber trotzdem an Stufe 2 scheitern (siehe
        // `apply_chosen_action`-Kommentar) -- NICHT verschlucken: sonst
        // meldet der Server `applied: true` fuer einen nie angewendeten Zug
        // und Engine-/Server-Zustand laufen auseinander.
        // PREREG_action_id_logging.md S2, mit EINER bewussten Luecke: startet
        // die Netz-KI einen Stapel-Zug (`DrawStackPeek`), loest
        // `apply_chosen_action` intern eine ganze FOLGE von Aktionen auf
        // (mehrfach weiterziehen, dann waehlen, dann rotieren, siehe
        // self_play.rs::resolve_and_apply_stack_draw). Die Zwischen-Zustaende
        // sind hier nicht greifbar, und die Funktion liegt im Self-Play-
        // Heisspfad -- sie bekommt deshalb KEINEN Logging-Haken (par.6: "keine
        // Aenderung an Suche, Wertung oder Self-Play"). Fuer diesen Fall bleibt
        // es beim Textweg, den der Replay ohnehin beherrscht (STACK_PEEK/
        // DOME_PLACE); S3 faellt dort automatisch darauf zurueck.
        if !matches!(a, Action::DrawStackPeek | Action::Pass) {
            let id = crate::self_play::action_to_id_direct(&self.game.state, &a);
            let ui = crate::self_play::action_to_env_dict(&self.game.state, &a);
            self.push_action_id_line(id, ui);
        }
        let mark = self.game.state.log.len();
        let resolved = match crate::self_play::apply_chosen_action(&mut self.game, a) {
            Ok(resolved) => resolved,
            Err(e) => {
                // Angekuendigte, aber nie angewandte Aktion wieder entfernen --
                // dieselbe Regel wie in `log_and_apply`. `mark` zeigt hinter die
                // `#a`-Zeile, deshalb `mark - 1`.
                if mark > 0
                    && self.game.state.log.get(mark - 1).is_some_and(|l| l.starts_with("#a "))
                {
                    self.game.state.log.remove(mark - 1);
                }
                return Ok(json!({
                    "applied": false,
                    "phase": self.game.state.phase.as_str(),
                    "reason": format!("apply_chosen_action fehlgeschlagen: {e}"),
                })
                .to_string());
            }
        };
        let action_json = search_move_json(&SearchMove::Draft(resolved), Some(&self.game.state));

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
        //
        // Task #20: ist ein Netz geladen (`self.net`), wird derselbe
        // Stichentscheid wie im Rust-Self-Play-Pfad angewendet (siehe
        // `self_play.rs::resolve_tiling_step`/`net_tiling_tiebreak_value`) --
        // hinter `NET_TILING_TIEBREAK_ENABLED` + Rundenfenster 2-4, sonst
        // exakt `best_first_step_exact`. Ohne geladenes Netz (`self.net ==
        // None`, Heuristik-Debug-Sitzung) unveraendert.
        //
        // Ownership-Verbraucher Teil 2 (`PREREG_ownership_consumer.md` §3):
        // dieselbe Wurzelkarte-EINMAL-je-Zug-Logik wie im Rust-Self-Play-Pfad,
        // ueber dieselbe Funktion -- eine zweite Implementierung koennte
        // auseinanderlaufen, und ein Pol, der nur in einem der beiden
        // Spielpfade wirkt, waere im Gating unsichtbar. Default 0 -> `None`,
        // kein zusaetzlicher Vorwaertspass.
        let step = match self.net.as_ref() {
            Some(net) => {
                let own = crate::self_play::ownership_tiling_marginals(net, &self.game.state, pi);
                let evaluator =
                    |final_state: &GameState| crate::self_play::net_tiling_tiebreak_value(net, final_state, pi);
                // K3 (d): GUI-Sitzung liest die Knoepfe aus der Umgebung (kein
                // Spec-Pfad hier), wie jeder andere Env-Knopf des Spielbetriebs.
                let sc = crate::net_mcts::SearchConfig::from_env();
                best_first_step_exact_or_valued_envelope(
                    &self.game.state, pi, Some(&evaluator), own.as_ref(), sc.envelope_tiling_w, &sc.envelope_profile,
                )
            }
            None => best_first_step_exact_or_valued(&self.game.state, pi, None),
        };

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
                // Logging-Luecke geschlossen (2026-08-07, Watchlist-Messartefakt):
                // der Menschen-Pfad `apply_tiling_chips` (oben, ~Zeile 298) loggt
                // die Reihen-Komplettierung per Bonuschip, dieser KI-Pfad (Solver-
                // Schritt `TilingStep::Chips`) tat es bisher NICHT -- identischer
                // Wortlaut wie dort, damit `analyze_game_log.py`s 🎫-Regex beide
                // Akteure gleich erfasst.
                let name = self.game.state.players[pi].name.clone();
                self.game
                    .state
                    .log_event(format!("🎫 {name} komplettiert Reihe {} mit Bonus-Chips!", row + 1));
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

        assert!(matches!(crate::tiling_solver::best_first_step_exact(&s, 0), TilingStep::End));
        assert!(generate_tiling_actions(&s, 0).is_empty());
    }

    /// Debug-/Analyse-Endpunkte dürfen den Spiel-RNG nicht fortschreiten
    /// lassen: zwei identisch geseedete Partien müssen mit und ohne
    /// zwischengeschaltete `ai_debug_*`-Aufrufe identisch verlaufen —
    /// insbesondere über eine Beutel-Neumischung (`Bag::refill_from_tower`,
    /// mischt mit dem Spiel-RNG) hinweg. Sonst ist die Partie nicht mehr aus
    /// dem Spiel-Log reproduzierbar (Replay-Validierung, analyze_game_log.py).
    #[test]
    fn debug_endpoints_leave_game_rng_untouched() {
        let mk = || PyGame::new(("A".into(), "B".into()), 0, Some(465392), None);
        let mut plain = mk();
        let mut probed = mk();

        // Startkacheln: Nicht-Starter zuerst (Regel, siehe game.rs).
        for p in [1usize, 0] {
            plain.ai_start_tile_json(p).unwrap();
            probed.ai_start_tile_json(p).unwrap();
        }
        assert_eq!(plain.state_json(), probed.state_json());

        let mut refill_seen = false;
        let mut prev_tower = probed.game.state.tower.count();
        for _ in 0..600 {
            if plain.game.is_over() {
                break;
            }
            // Nur in `probed`: Debug-Aufrufe zwischenschalten — wie ein
            // Nutzer, der während der Partie den KI-Debugger öffnet.
            let _ = probed.ai_debug_json(20);
            let _ = probed.ai_debug_log(20);

            let r1 = plain.ai_step_json(20, false).unwrap();
            let r2 = probed.ai_step_json(20, false).unwrap();
            assert_eq!(r1, r2, "KI-Zug weicht nach Debug-Aufrufen ab");
            assert_eq!(
                plain.state_json(),
                probed.state_json(),
                "Zustand weicht nach Debug-Aufrufen ab"
            );

            // Turm schrumpft nur durch `refill_from_tower` → Neumischung erkannt.
            let tower_now = probed.game.state.tower.count();
            if tower_now < prev_tower {
                refill_seen = true;
            }
            prev_tower = tower_now;
        }
        assert!(plain.game.is_over(), "Partie nicht zu Ende gespielt (Schrittlimit)");
        assert!(refill_seen, "keine Beutel-Neumischung im Testspiel — Seed anpassen");
    }

    /// Watchlist-Messartefakt (2026-08-07, evaluations/watchlist_v20_interim_review.md):
    /// der KI-Pfad `ai_tiling_step` (Solver-Schritt `TilingStep::Chips`) loggte
    /// Reihen-Komplettierungen per Bonuschip bisher NICHT, obwohl der Menschen-Pfad
    /// `apply_tiling_chips` (oben) das immer tat -- Log-Analysen unterschaetzten
    /// dadurch die KI-Chip-Nutzung. Kontentions-Aufbau identisch zu
    /// `tiling_solver::tests::greedy_chip_alloc_tradeoff_in_contention`: erzwingt
    /// deterministisch `TilingStep::Chips` als exakt ersten Solver-Schritt.
    #[test]
    fn ai_tiling_step_logs_chip_completion() {
        use crate::dome::{build_dome_tile_pool, BonusChip};
        use crate::tile::TileColor::{Blau, Rot};

        let mut pg = PyGame::new(("P1".into(), "P2".into()), 0, Some(7), None);
        pg.game.state.phase = Phase::Tiling;
        for p in pg.game.state.players.iter_mut() {
            p.start_tile_pending = false;
        }
        // Slot (1,0) = pool[2] [Tuerkis, Rot, Blau, Wild]:
        //   si1 = Rot @ 6x6 (2,1) -> Reihe 3 (idx 2, 1 fehlt).
        //   si2 = Blau @ 6x6 (3,0) -> Reihe 4 (idx 3, 1 fehlt).
        let tile = build_dome_tile_pool()[2].clone();
        pg.game.state.players[0].dome_grid.place_dome_tile(tile, 1, 0).unwrap();
        pg.game.state.players[0].pattern_lines[2].add_tiles(&[Rot, Rot]); // cap 3
        pg.game.state.players[0].pattern_lines[3].add_tiles(&[Blau, Blau, Blau]); // cap 4
        pg.game.state.players[0].bonus_chips = vec![
            BonusChip { chip_id: 0, colors: vec![Blau, Rot] },
            BonusChip { chip_id: 1, colors: vec![Blau, Rot] },
            BonusChip { chip_id: 2, colors: vec![Blau] },
            BonusChip { chip_id: 3, colors: vec![Rot] },
        ];
        pg.game.state.current_player = 0;

        let before = pg.game.state.log.len();
        pg.ai_tiling_step().expect("KI-Tiling-Schritt sollte gelingen");
        let new_lines = &pg.game.state.log[before..];
        assert!(
            new_lines.iter().any(|l| l.contains('🎫') && l.contains("komplettiert Reihe")),
            "KI-Chip-Komplettierung sollte geloggt werden, neue Log-Zeilen: {new_lines:?}"
        );
    }

    /// Der Fall, an dem `tools/analyze_game_log.py` am 2026-08-29 zerbrach
    /// (Vorfall in `docs/pitfalls.md`): greedy waehlt die ERSTEN drei Chips
    /// der Hand (`round_end::greedy_chip_indices`) und verbrennt dabei einen,
    /// den die echte KI behalten hatte. Hier nachgestellt in klein: eine
    /// Reihe, die greedy so bezahlt, dass die ZWEITE Reihe danach nicht mehr
    /// zahlbar ist -- waehrend die explizite Auswahl beide schafft.
    #[test]
    fn explicit_chip_allocation_survives_where_greedy_starves() {
        use crate::dome::BonusChip;
        use crate::tile::TileColor::{Blau, Gelb, Rot, Tuerkis};

        // Hand: 1x blau-Traeger, 2x gelb-Traeger, Rest farbfremd.
        let hand = || {
            vec![
                BonusChip { chip_id: 0, colors: vec![Gelb] },      // gelb-Traeger, steht VORNE
                BonusChip { chip_id: 1, colors: vec![Tuerkis] },
                BonusChip { chip_id: 2, colors: vec![Rot] },
                BonusChip { chip_id: 3, colors: vec![Blau] },      // einziger blau-Traeger
                BonusChip { chip_id: 4, colors: vec![Gelb] },      // zweiter gelb-Traeger
            ]
        };
        // Reihe 2 (idx 1, cap 2): blau, 1 fehlt. Reihe 3 (idx 2, cap 3): gelb, 1 fehlt.
        let setup = |pg: &mut PyGame| {
            pg.game.state.phase = Phase::Tiling;
            let p = &mut pg.game.state.players[0];
            p.start_tile_pending = false;
            p.pattern_lines[1].add_tiles(&[Blau]);
            p.pattern_lines[2].add_tiles(&[Gelb, Gelb]);
            p.bonus_chips = hand();
        };

        // A) Greedy-Pfad: Reihe 2 hat nur EINEN blau-Traeger, zahlt also drei
        //    beliebige -- und nimmt die ersten drei (0,1,2), darunter einen
        //    gelb-Traeger. Danach bleiben 3+4, nur noch EIN gelb-Traeger:
        //    Reihe 3 braucht drei beliebige, es sind aber nur zwei da.
        let mut greedy = PyGame::new(("P1".into(), "P2".into()), 0, Some(7), None);
        setup(&mut greedy);
        // Kein `expect` auf einem `PyErr`: dessen Debug-Ausgabe braucht den
        // Interpreter, den der Rust-Test nicht haelt -- ein Fehlschlag wuerde
        // sonst als STATUS_STACK_BUFFER_OVERRUN statt als Testmeldung enden.
        assert!(greedy.apply_tiling_chips(0, 1).is_ok(), "Reihe 2 ist greedy zahlbar");
        assert_eq!(
            greedy.game.state.players[0].bonus_chips.len(),
            2,
            "greedy sollte drei beliebige Chips verbraucht haben"
        );
        assert!(
            greedy.apply_tiling_chips(0, 2).is_err(),
            "Reihe 3 muss nach dem greedy-Verbrauch unbezahlbar sein -- sonst trifft der Test den Vorfall nicht"
        );

        // B) Explizite Auswahl: Reihe 2 mit 1,2,3 bezahlen (die gelb-Traeger
        //    schonen), dann traegt Reihe 3 ihre zwei farbgleichen 0,4.
        let mut exact = PyGame::new(("P1".into(), "P2".into()), 0, Some(7), None);
        setup(&mut exact);
        let cands: Vec<Vec<usize>> =
            serde_json::from_str(&exact.chip_allocations_json(0, 1)).expect("Kandidaten-JSON");
        assert!(
            cands.iter().any(|c| c.len() == 3),
            "Kandidatenliste sollte die Drei-beliebig-Zahlungen enthalten: {cands:?}"
        );
        assert!(
            exact.apply_tiling_chips_with(0, 1, vec![1, 2, 3]).is_ok(),
            "explizite Auswahl fuer Reihe 2"
        );
        // ACHTUNG, gilt auch fuer jeden Aufrufer: `apply_bonus_chips_with`
        // entfernt die Chips aus dem Vec, die Indizes verschieben sich also.
        // Aus der Resthand [gelb(war 0), gelb(war 4)] sind das jetzt 0 und 1 --
        // Kandidatenlisten muessen unmittelbar vor der Anwendung geholt werden.
        assert!(
            exact.apply_tiling_chips_with(0, 2, vec![0, 1]).is_ok(),
            "zwei gelb-Traeger fuer Reihe 3"
        );
        assert!(
            exact.game.state.players[0].bonus_chips.is_empty(),
            "beide Reihen bezahlt, Hand leer: {:?}",
            exact.game.state.players[0].bonus_chips
        );
        assert_eq!(
            exact.game.state.log.iter().filter(|l| l.contains('🎫')).count(),
            2,
            "beide Vollendungen muessen mit dem Bestands-Wortlaut geloggt sein"
        );
    }

    /// Die neue Bindung darf nie permissiver sein als der Menschen-Pfad:
    /// Top-down-Sperre (Engine-Audit U1) und Regelpruefung gelten weiter.
    #[test]
    fn explicit_chip_allocation_rejects_locked_row_and_bad_selection() {
        use crate::dome::BonusChip;
        use crate::tile::TileColor::{Blau, Rot};

        let mut pg = PyGame::new(("P1".into(), "P2".into()), 0, Some(7), None);
        pg.game.state.phase = Phase::Tiling;
        {
            let p = &mut pg.game.state.players[0];
            p.start_tile_pending = false;
            p.pattern_lines[1].add_tiles(&[Blau]);
            p.bonus_chips = vec![
                BonusChip { chip_id: 0, colors: vec![Blau] },
                BonusChip { chip_id: 1, colors: vec![Blau] },
                BonusChip { chip_id: 2, colors: vec![Rot] },
            ];
        }
        // Zu wenige Chips fuer die Regel (1 Chip zahlt keine Zelle).
        assert!(pg.apply_tiling_chips_with(0, 1, vec![0]).is_err(), "eine Zelle kostet mindestens zwei Chips");
        // Top-down gesperrt: bereits eine spaetere Reihe getilt.
        pg.game.state.players[0].tiled_max_row = 3;
        assert!(pg.apply_tiling_chips_with(0, 1, vec![0, 1]).is_err(), "gesperrte Reihe darf nicht zahlbar sein");
        assert_eq!(pg.chip_allocations_json(0, 1), "[]", "und sie darf keine Kandidaten anbieten");
    }
}
