//! Self-Play-Datengenerierung in Rust — Port von `self_play.py` (MCTS-Modus).
//!
//! Spielt komplette Partien auf der Rust-Engine (Drafting per MCTS, Tiling per
//! exaktem DFS-Solver) und liefert je Zug einen Trainings-Record im **selben**
//! Format wie `self_play.py` (state = `serialize_state`-kompatibles JSON,
//! `policy`/`valid_actions` im **agent_env-Schema**, `moon_order_target`,
//! `scores`, `winner`, `player`, `game_id`). Ein schlankes Python-`self_play.py`
//! pickled die Records — `train.py` und das Pickle-Format bleiben unverändert.
//!
//! Wichtig: `policy`/`valid_actions` folgen dem agent_env-Schema
//! (`factory_index`, `display_index`, `color`, `row`, `pattern_row`, …), weil
//! `agents/neural_net.py::action_to_id` genau diese Keys liest — NICHT dem
//! `serialize::action_to_dict`-Schema (`factory_id`, `tile_id`).

use rand::rngs::StdRng;
use rand::seq::{IndexedRandom, SliceRandom};
use rand::{Rng, RngExt, SeedableRng};
use rayon::prelude::*;
use serde_json::{json, Map, Value};

use crate::dome::SpaceType;
use crate::game::{apply_start_placement, determine_winner, drafting_actions, Game, TilingMove};
use crate::mcts::{dynamic_sims, root_child_stats, search_drafting_action};
use crate::net::Net;
use crate::net_mcts::{net_root_child_stats, net_search_drafting_action, LeafEval};
use crate::moves::{Action, Move, PlaceAction, TakeAction, TakeSource};
use crate::round_end::{
    apply_bonus_chips_with, can_complete_row_with_chips, generate_tiling_actions,
    row_has_open_matching_slot,
};
use crate::scoring::sample_valid_scoring_ids;
use crate::serialize::state_to_json;
use crate::state::{GameState, Phase};
use crate::tile::TileColor;
use crate::tiling_solver::{best_first_step_exact, solve_round_final_score, TilingStep};

/// Standard-UCT-Konstante der Self-Play-Suche (= `py.rs::AI_C`).
pub const SELF_PLAY_C: f64 = 0.3;

/// Temperatur für die AUFGEZEICHNETE Policy-Target (scharf → Destillation der
/// Heuristik-Wahl). Entkoppelt von der Play-Temperatur (die fürs Sampeln der
/// gespielten Aktion sorgt und die Zustandsvielfalt erhält). Niedriger = schärfer.
pub const TARGET_TEMP: f64 = 0.15;

/// Boden-Wallclock für den Hänger-Schutz, unabhängig von der Sim-Zahl — sehr
/// niedrige Sims (Tests, kleine Debug-Läufe) sollen trotzdem nie unter dieses
/// Minimum fallen.
const MIN_GAME_TIMEOUT_SECS: u64 = 30;

/// Hänger-Schutz-Wallclock für reine Heuristik-Partien (`play_one_game`,
/// `play_arena_game`), SKALIERT mit der tatsächlich verwendeten Sim-Zahl statt
/// eines fixen Werts — ein fixer Wert (früher 30s, kalibriert auf niedrige
/// Sim-Zahlen, "normal 1-4s") reißt bei jeder künftigen Erhöhung der Sims
/// wieder: bei 400 Sims plus den seit diesem Zyklus zusätzlichen
/// Blattbewertungskosten (Wertungsplatten-/Unplaceable-Penalty-Projektion pro
/// Knoten) wurden Partien vereinzelt vor Rundenende abgebrochen, scores/winner
/// sind dann kein echtes Endergebnis. Faktor 0.3s/Sim kalibriert so, dass bei
/// 400 Sims wie zuletzt 120s Puffer herauskommen.
fn heuristic_game_timeout_secs(sims: u32) -> u64 {
    ((sims as u64 * 3) / 10).max(MIN_GAME_TIMEOUT_SECS)
}

/// Hänger-Schutz-Wallclock für netzbeteiligte Partien (`play_net_game`,
/// `play_net_vs_net_game`, `play_net_self_play_game`) — jede Simulation
/// braucht eine ONNX-Inferenz, das ist deutlich langsamer als reine
/// Heuristik-Suche, daher ein höherer Faktor pro Sim als bei
/// `heuristic_game_timeout_secs`. SKALIERT mit der Sim-Zahl aus demselben
/// Grund: bei 30s fix wurden Self-Play-Partien bei 400 Sims systematisch vor
/// Rundenende (Runde 3-4 von 5) abgeschnitten — die aufgezeichneten
/// scores/winner solcher Partien sind dann KEIN echtes Endergebnis
/// (Wertungsplatten werden nur bei Phase::End angewendet), was das gesamte
/// Punkte-Marge-Value-Target korrumpiert. Faktor 0.45s/Sim kalibriert so, dass
/// bei 400 Sims wie zuletzt 180s Puffer herauskommen.
fn net_game_timeout_secs(sims: u32) -> u64 {
    ((sims as u64 * 9) / 20).max(MIN_GAME_TIMEOUT_SECS)
}

// ── agent_env-Action-Serializer ──────────────────────────────────────────────

/// `factory_index` einer Stein-Aktion (Port der Logik aus
/// `agents/agent_env.py::_drafting_actions`): 0–3 = kleine Fabriken,
/// 4 = große Fabrik (Sun), 5 = globaler Mond (Aktion C, `factory_id=None`).
fn factory_index(state: &GameState, t: &TakeAction) -> i64 {
    match t.source {
        TakeSource::LargeFactorySun => 4,
        TakeSource::SmallFactoryMoon | TakeSource::LargeFactoryMoon => match t.factory_id {
            Some(fid) => factory_pos(state, fid),
            None => 5,
        },
        TakeSource::SmallFactorySun => match t.factory_id {
            Some(fid) => factory_pos(state, fid),
            None => 0,
        },
    }
}

fn factory_pos(state: &GameState, fid: usize) -> i64 {
    state
        .factories
        .iter()
        .position(|f| f.factory_id == fid)
        .map(|i| i as i64)
        .unwrap_or(0)
}

/// Mappt eine Engine-`Action` auf das agent_env-Dict (Schlüssel, die
/// `action_to_id` liest).
pub(crate) fn action_to_env_dict(state: &GameState, a: &Action) -> Value {
    match a {
        Action::Stone(m) => json!({
            "type": "stone",
            "factory_index": factory_index(state, &m.take),
            "color": m.take.color.value(),
            "row": m.place.row_index,
            // Nur Debug-/Introspektions-Info — action_to_id liest dieses Feld
            // NICHT (Moon-Order-Varianten teilen sich bewusst dieselbe ID; die
            // Suche kombiniert ihre Priors separat, siehe net_mcts.rs).
            "moon_order": m.take.moon_order.iter().map(|c| c.value()).collect::<Vec<_>>(),
        }),
        Action::Dome(m) => {
            let d_idx = state
                .dome_display
                .iter()
                .position(|t| t.tile_id == m.dome_tile_id)
                .unwrap_or(0);
            json!({
                "type": "dome",
                "display_index": d_idx,
                "slot_row": m.slot_row,
                "slot_col": m.slot_col,
                "rotation": m.rotation,
            })
        }
        Action::DrawStack(m) => json!({
            "type": "dome_stack",
            "slot_row": m.slot_row,
            "slot_col": m.slot_col,
            "rotation": m.rotation,
        }),
        Action::BonusChip(m) => json!({
            "type": "bonus_chip",
            "factory_index": factory_pos(state, m.factory_id),
        }),
        Action::Pass => json!({ "type": "pass" }),
    }
}

// ── Policy-Extraktion (Port von SelfPlayMixin.search_and_get_policy) ──────────

/// Gewichtete Policy aus der Wurzelkind-Statistik:
/// `visits^(1/temp) * max(q,1e-6)^2`, normalisiert. Liefert die gewählte Aktion
/// (per Gewichten gesampelt) und die Policy-Einträge (agent_env-Schema).
fn drafting_policy<R: Rng + ?Sized>(
    state: &GameState,
    actions: &[Action],
    base_sims: u32,
    c: f64,
    play_temp: f64,
    rng: &mut R,
) -> (Action, Vec<Value>) {
    let sims = dynamic_sims(base_sims, actions.len());
    let stats = root_child_stats(state, sims, c, rng); // Vec<(Action, visits, q)>

    if stats.is_empty() {
        let a = actions.choose(rng).cloned().unwrap_or(Action::Pass);
        let entry = json!({ "action": action_to_env_dict(state, &a), "prob": 1.0 });
        return (a, vec![entry]);
    }

    // Gewichte für eine Temperatur: visits^(1/temp)·q², mit reinem-Visits-Fallback.
    let weights_for = |t: f64| -> (Vec<f64>, f64) {
        let inv = 1.0 / t.max(1e-6);
        let mut w: Vec<f64> = stats
            .iter()
            .map(|(_, v, q)| (*v as f64).powf(inv) * q.max(1e-6).powi(2))
            .collect();
        let mut s: f64 = w.iter().sum();
        if !(s > 0.0) {
            w = stats.iter().map(|(_, v, _)| (*v as f64).powf(inv)).collect();
            s = w.iter().sum();
        }
        (w, s)
    };

    // TARGET (aufgezeichnet): scharf via TARGET_TEMP → Destillation der besten
    // Heuristik-Züge, damit das Netz eine lernbar-scharfe Policy bekommt.
    let (tw, ts) = weights_for(TARGET_TEMP);
    let policy: Vec<Value> = if ts > 0.0 {
        stats
            .iter()
            .zip(tw.iter())
            .map(|((a, _, _), w)| json!({ "action": action_to_env_dict(state, a), "prob": w / ts }))
            .collect()
    } else {
        vec![json!({ "action": action_to_env_dict(state, &stats[0].0), "prob": 1.0 })]
    };

    // PLAY: moderate Temperatur → gespielte Aktion sampeln (Zustandsvielfalt).
    let (pw, ps) = weights_for(play_temp);
    let idx = if ps > 0.0 { weighted_index(&pw, ps, rng) } else { 0 };
    (stats[idx].0.clone(), policy)
}

/// Sampelt einen Index proportional zu `weights` (Summe = `total`).
fn weighted_index<R: Rng + ?Sized>(weights: &[f64], total: f64, rng: &mut R) -> usize {
    let mut r = rng.random_range(0.0..total.max(f64::MIN_POSITIVE));
    for (i, w) in weights.iter().enumerate() {
        r -= w;
        if r <= 0.0 {
            return i;
        }
    }
    weights.len().saturating_sub(1)
}

// ── Moon-Order-Target (Port von self_play.py:194-240) ─────────────────────────

/// Beste Mondreihenfolge der RESTLICHEN Sun-Steine für einen Stein-Zug aus einer
/// kleinen Fabrik (factory_index 0–3). Permutiert die verbleibenden Steine
/// (max. 6 Stichproben), bewertet je Reihenfolge per `solve_round_final_score`
/// und gibt die beste als Farb-Liste zurück. `None` außerhalb des Anwendungsfalls.
fn moon_order_target<R: Rng + ?Sized>(
    state: &GameState,
    a: &Action,
    pi: usize,
    rng: &mut R,
) -> Option<Vec<String>> {
    let m = match a {
        Action::Stone(m) => m,
        _ => return None,
    };
    if m.take.source != TakeSource::SmallFactorySun {
        return None;
    }
    let fid = m.take.factory_id?;
    let factory = state.factories.iter().find(|f| f.factory_id == fid)?;
    let color = m.take.color;
    let remaining: Vec<TileColor> = factory
        .sun_tiles
        .iter()
        .copied()
        .filter(|&t| t != color)
        .collect();
    if remaining.is_empty() {
        return None;
    }

    let mut perms = permutations(&remaining);
    if perms.len() > 6 {
        perms.shuffle(rng);
        perms.truncate(6);
    }

    let row = m.place.row_index;
    let mut best_score = i32::MIN;
    let mut best: Option<Vec<TileColor>> = None;
    for perm in perms {
        let mv = Move {
            take: TakeAction {
                source: TakeSource::SmallFactorySun,
                color,
                factory_id: Some(fid),
                moon_order: perm.clone(),
            },
            place: PlaceAction { row_index: row },
        };
        let mut g = Game { state: state.clone() };
        if g.apply_drafting(&Action::Stone(mv)).is_ok() {
            let score = solve_round_final_score(&g.state, pi);
            if score > best_score {
                best_score = score;
                best = Some(perm);
            }
        }
    }
    best.map(|p| p.iter().map(|t| t.value().to_string()).collect())
}

/// Alle Permutationen (rekursiv; nur für sehr kurze Slices genutzt, ≤ 3 Elemente).
fn permutations<T: Clone>(items: &[T]) -> Vec<Vec<T>> {
    if items.len() <= 1 {
        return vec![items.to_vec()];
    }
    let mut out = Vec::new();
    for i in 0..items.len() {
        let mut rest = items.to_vec();
        let head = rest.remove(i);
        for mut p in permutations(&rest) {
            p.insert(0, head.clone());
            out.push(p);
        }
    }
    out
}

// ── Startkachel-Heuristik (Port von py.rs::ai_start_tile_json) ────────────────

fn color_index(c: TileColor) -> Option<usize> {
    TileColor::NORMAL.iter().position(|&x| x == c)
}

/// Zählt Sun-Steine je Normalfarbe über alle Fabriken + große Fabrik.
fn sun_color_counts(state: &GameState) -> [usize; 5] {
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

/// Heuristik-Wahl der Startkuppel für Spieler `pi` (Farb-Häufigkeit + Eckbonus):
/// liefert `(tile_id, slot_row, slot_col, rotation)`. `None`, wenn kein Display
/// oder kein freier Slot. Gemeinsam genutzt von Self-Play und Arena.
fn choose_start_placement(state: &GameState, pi: usize) -> Option<(usize, usize, usize, u32)> {
    if state.dome_display.is_empty() {
        return None;
    }
    let empties = state.players[pi].dome_grid.empty_slots();
    if empties.is_empty() {
        return None;
    }
    let counts = sun_color_counts(state);
    let mut best: Option<(f64, usize, usize, usize, u32)> = None;
    for tile in &state.dome_display {
        for &(r, c) in &empties {
            let corner = if (r == 0 || r == 2) && (c == 0 || c == 2) { 0.5 } else { 0.0 };
            for &rot in &[0u32, 90, 180, 270] {
                let spaces = match tile.rotated_spaces(rot) {
                    Ok(s) => s,
                    Err(_) => continue,
                };
                let mut score = corner;
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
    best.map(|(_, t, r, c, rot)| (t, r, c, rot))
}

// ── Einzelschritte ────────────────────────────────────────────────────────────

/// Startkuppel-Platzierung (nur Runde 1). Platziert per Farb-/Reihen-Heuristik
/// und nimmt einen one-hot-`dome`-Record auf. Nicht-Startspieler legt zuerst
/// (Engine erzwingt das). `player` = `current_player` (= Startspieler), exakt
/// wie der Python-Loop (current_player wechselt erst nach Start-Placement).
fn start_placement_step<R: Rng + ?Sized>(game: &mut Game, _rng: &mut R) -> Option<Map<String, Value>> {
    let recorded_player = game.state.current_player;
    let first = game.state.current_player;
    let non_starter = 1 - first;
    let pi = if game.state.players[non_starter].start_tile_pending {
        non_starter
    } else if game.state.players[first].start_tile_pending {
        first
    } else {
        return None;
    };

    if game.state.dome_display.is_empty() {
        return None;
    }
    let empties = game.state.players[pi].dome_grid.empty_slots();
    if empties.is_empty() {
        return None;
    }

    // Vollständige Aktionsmenge (agent_env: alle Display × Slots × 4 Rotationen).
    let mut valid_actions = Vec::new();
    for (d_idx, _tile) in game.state.dome_display.iter().enumerate() {
        for &(r, c) in &empties {
            for &rot in &[0u32, 90, 180, 270] {
                valid_actions.push(json!({
                    "type": "dome",
                    "display_index": d_idx,
                    "slot_row": r,
                    "slot_col": c,
                    "rotation": rot,
                    "is_start": true,
                }));
            }
        }
    }

    // Heuristik-Wahl (Farb-Häufigkeit + Eckbonus) — gemeinsamer Helfer.
    let (tile_id, r, c, rot) = choose_start_placement(&game.state, pi)?;
    let d_idx = game
        .state
        .dome_display
        .iter()
        .position(|t| t.tile_id == tile_id)
        .unwrap_or(0);

    let state_json = state_to_json(&game.state, true);
    let chosen_env = json!({
        "type": "dome",
        "display_index": d_idx,
        "slot_row": r,
        "slot_col": c,
        "rotation": rot,
        "is_start": true,
    });

    apply_start_placement(&mut game.state, pi, tile_id, r, c, rot).ok()?;

    let mut m = Map::new();
    m.insert("state".into(), state_json);
    m.insert("policy".into(), json!([{ "action": chosen_env, "prob": 1.0 }]));
    m.insert("valid_actions".into(), Value::Array(valid_actions));
    m.insert("moon_order_target".into(), Value::Null);
    m.insert("player".into(), json!(recorded_player));
    Some(m)
}

/// Drafting-Zug per MCTS-Policy. Nimmt den Record auf und wendet den Zug an.
fn drafting_step<R: Rng + ?Sized>(
    game: &mut Game,
    base_sims: u32,
    c: f64,
    rng: &mut R,
) -> Map<String, Value> {
    let player = game.state.current_player;
    let actions = drafting_actions(&game.state);
    let n = actions.len();

    // Aktionsabhängige Temperatur (Port self_play.py:172).
    let temp = if n > 50 { 0.7 } else if n > 15 { 0.4 } else { 0.15 };

    let valid_actions: Vec<Value> =
        actions.iter().map(|a| action_to_env_dict(&game.state, a)).collect();

    let (chosen, policy) = if n == 1 {
        let a = actions[0].clone();
        let entry = json!({ "action": action_to_env_dict(&game.state, &a), "prob": 1.0 });
        (a, vec![entry])
    } else {
        drafting_policy(&game.state, &actions, base_sims, c, temp, rng)
    };

    let moon_t = moon_order_target(&game.state, &chosen, player, rng);
    let state_json = state_to_json(&game.state, true);

    // Zug anwenden (sollte stets gültig sein — aus drafting_actions stammend).
    let _ = game.apply_drafting(&chosen);

    let mut m = Map::new();
    m.insert("state".into(), state_json);
    m.insert("policy".into(), Value::Array(policy));
    m.insert("valid_actions".into(), Value::Array(valid_actions));
    m.insert(
        "moon_order_target".into(),
        moon_t.map(|v| json!(v)).unwrap_or(Value::Null),
    );
    m.insert("player".into(), json!(player));
    m
}

/// Legale Tiling-Aktionen im agent_env-Schema (für `valid_actions` = Trainings-
/// maske): ALLE platzierbaren Steine (jede pending Reihe) + optionale `use_chips`
/// + `end_tiling`. WICHTIG: NICHT auf die oberste Reihe filtern — der DFS-Solver
/// darf jede pending Reihe wählen (Engine erlaubt freie Reihenfolge, bis eine
/// spätere gelegt wird). Ein Top-Reihen-Filter ließe eine vom Solver gewählte
/// Aktion einer anderen Reihe außerhalb der Maske liegen → Policy-Leak →
/// explodierender Policy-Loss im Training.
fn tiling_env_actions(state: &GameState, pi: usize) -> Vec<Value> {
    let mut actions = Vec::new();
    let tiling_actions = generate_tiling_actions(state, pi);
    let has_placements = !tiling_actions.is_empty();

    for a in &tiling_actions {
        actions.push(json!({
            "type": "tiling",
            "player": pi,
            "pattern_row": a.pattern_row,
            "slot_row": a.slot_row,
            "slot_col": a.slot_col,
            "space_index": a.space_index,
            "dome_tile_id": a.dome_tile_id,
            "rotation": a.rotation,
        }));
    }

    // Chip-Komplettierung: der DFS-Solver kann Chips auch bei noch offenen
    // Platzierungen wählen — daher stets als legale Aktion mitführen (Maske).
    let player = &state.players[pi];
    let tiled_max = player.tiled_max_row;
    for (ri, row) in player.pattern_lines.iter().enumerate() {
        if row.is_complete() || (ri as i32) < tiled_max {
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
            actions.push(json!({ "type": "use_chips", "player": pi, "pattern_row": ri }));
        }
    }

    // end_tiling nur, wenn keine zwingende Platzierung offen ist (Engine-Regel).
    if !has_placements {
        actions.push(json!({ "type": "end_tiling" }));
    }
    actions
}

/// Beste noch ausstehende Tiling-Platzierung (inkl. Platzierung einer NEUEN
/// Kuppelplatte für eine volle Reihe — die der DFS-Solver bewusst ausblendet).
/// Wahl nach maximalem finalem Runden-Score. Verhindert den Deadlock, wenn der
/// Solver `End` liefert, die Engine das Beenden aber wegen offener Aktionen
/// (`valid_tiling_actions` ≠ ∅) verweigert.
fn best_pending_placement(state: &GameState, pi: usize) -> Option<crate::round_end::TilingAction> {
    let actions = generate_tiling_actions(state, pi);
    let mut best: Option<(i32, crate::round_end::TilingAction)> = None;
    for ta in actions {
        let mut g = Game { state: state.clone() };
        if g.apply_single_tiling(pi, &ta).is_ok() {
            let score = solve_round_final_score(&g.state, pi);
            if best.as_ref().map_or(true, |(b, _)| score > *b) {
                best = Some((score, ta));
            }
        }
    }
    best.map(|(_, ta)| ta)
}

/// Optimaler Tiling-Schritt: DFS-Solver, aber wenn der `End` liefert während die
/// Engine noch offene Tiling-Aktionen sieht (volle Reihe nur per neuer
/// Kuppelplatte legbar), stattdessen die beste solche Platzierung — verhindert
/// den end_tiling-Deadlock. Gemeinsam genutzt von Self-Play und Arena.
fn resolve_tiling_step(state: &GameState, pi: usize) -> TilingStep {
    match best_first_step_exact(state, pi) {
        TilingStep::End => match best_pending_placement(state, pi) {
            Some(ta) => TilingStep::Place(ta),
            None => TilingStep::End,
        },
        other => other,
    }
}

/// Tiling-Zug per exaktem DFS-Solver (one-hot Policy auf den optimalen Schritt).
fn tiling_step<R: Rng + ?Sized>(game: &mut Game, rng: &mut R) -> Map<String, Value> {
    let pi = game.state.current_player;
    let state_json = state_to_json(&game.state, true);
    let valid_actions = tiling_env_actions(&game.state, pi);
    let step = resolve_tiling_step(&game.state, pi);

    let chosen_env: Value = match &step {
        TilingStep::Place(ta) => json!({
            "type": "tiling",
            "player": pi,
            "pattern_row": ta.pattern_row,
            "slot_row": ta.slot_row,
            "slot_col": ta.slot_col,
            "space_index": ta.space_index,
            "dome_tile_id": ta.dome_tile_id,
            "rotation": ta.rotation,
        }),
        TilingStep::Chips { row, .. } => {
            json!({ "type": "use_chips", "player": pi, "pattern_row": row })
        }
        TilingStep::End => json!({ "type": "end_tiling" }),
    };

    match &step {
        TilingStep::Place(ta) => {
            let _ = game.apply_single_tiling(pi, ta);
        }
        TilingStep::Chips { row, chips } => {
            apply_bonus_chips_with(&mut game.state.players[pi], *row, chips);
        }
        TilingStep::End => {
            let _ = game.apply_tiling(&TilingMove::EndTiling { player: pi }, rng);
        }
    }

    let mut m = Map::new();
    m.insert("state".into(), state_json);
    m.insert("policy".into(), json!([{ "action": chosen_env, "prob": 1.0 }]));
    m.insert("valid_actions".into(), Value::Array(valid_actions));
    m.insert("moon_order_target".into(), Value::Null);
    m.insert("player".into(), json!(pi));
    m
}

// ── Spiel-Loop ────────────────────────────────────────────────────────────────

/// Spielt EINE komplette Partie und gibt die Trainings-Records zurück.
pub fn play_one_game<R: Rng + ?Sized>(
    base_sims: u32,
    c: f64,
    scoring_ids: Vec<usize>,
    names: [String; 2],
    first_player: usize,
    game_id: &str,
    rng: &mut R,
) -> Vec<Value> {
    let mut game = Game::start(names, first_player, scoring_ids, rng);
    let mut records: Vec<Map<String, Value>> = Vec::new();

    let mut guard = 0u32;
    let t_start = std::time::Instant::now();
    let timeout_secs = heuristic_game_timeout_secs(base_sims);
    loop {
        guard += 1;
        if guard > 100_000 || t_start.elapsed().as_secs() >= timeout_secs {
            break; // defensive Endlosschleifen-Sicherung
        }
        match game.state.phase {
            Phase::StartPlacement | Phase::Drafting => {
                if game.state.players.iter().any(|p| p.start_tile_pending) {
                    match start_placement_step(&mut game, rng) {
                        Some(rec) => records.push(rec),
                        None => break,
                    }
                } else if game.state.phase == Phase::Drafting {
                    records.push(drafting_step(&mut game, base_sims, c, rng));
                } else {
                    break;
                }
            }
            Phase::Tiling => records.push(tiling_step(&mut game, rng)),
            _ => break, // Scoring/End/Final → Partie vorbei
        }
    }

    // Endwertung anwenden, damit Scores die Wertungsplatten enthalten.
    let completed = game.state.phase == Phase::End;
    if completed {
        let _ = game.apply_end_scoring();
    }
    let scores = [game.state.players[0].score, game.state.players[1].score];
    let winner = determine_winner(&game.state);

    records
        .into_iter()
        .map(|mut m| {
            m.insert("game_id".into(), json!(game_id));
            m.insert("scores".into(), json!(scores));
            m.insert("winner".into(), json!(winner));
            // Erreicht die Partie regulär Phase::End (nicht durch Haenger-Schutz
            // abgebrochen)? Nur dann sind scores/winner ein echtes Endergebnis
            // (inkl. Wertungsplatten). Downstream (self_play.py) prüft das je Datei.
            m.insert("completed".into(), json!(completed));
            Value::Object(m)
        })
        .collect()
}

/// Spielt `n_games` Partien (rayon-parallel) und gibt ALLE Step-Records flach als
/// JSON-Array-String zurück. Je Spiel ein deterministisch aus `seed` abgeleiteter
/// RNG, zufälliger Startspieler und konfliktfreie Wertungsplatten.
pub fn run_self_play(
    n_games: usize,
    base_sims: u32,
    c: f64,
    seed: u64,
    num_threads: usize,
    prefix: &str,
) -> String {
    let play = |i: usize| -> Vec<Value> {
        let mut rng = StdRng::seed_from_u64(seed.wrapping_add((i as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15)));
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let first = rng.random_range(0..2usize);
        let names = ["Spieler 1".to_string(), "Spieler 2".to_string()];
        let gid = format!("{prefix}_g{}", i + 1);
        play_one_game(base_sims, c, ids, names, first, &gid, &mut rng)
    };

    // num_threads == 0 → globaler rayon-Pool (alle Kerne); sonst dedizierter Pool.
    let all: Vec<Vec<Value>> = if num_threads == 0 {
        (0..n_games).into_par_iter().map(play).collect()
    } else {
        match rayon::ThreadPoolBuilder::new().num_threads(num_threads).build() {
            Ok(pool) => pool.install(|| (0..n_games).into_par_iter().map(play).collect()),
            Err(_) => (0..n_games).map(play).collect(), // Fallback: seriell
        }
    };

    let flat: Vec<Value> = all.into_iter().flatten().collect();
    serde_json::to_string(&Value::Array(flat)).unwrap_or_else(|_| "[]".to_string())
}

// ── Arena (Agent-vs-Agent-Turnier) ───────────────────────────────────────────

/// Spielt EIN Arena-Spiel zwischen zwei Heuristik-MCTS-Konfigurationen.
/// Brett 0 sucht mit `sims[0]` Basis-Simulationen, Brett 1 mit `sims[1]`.
/// Jeder Agent spielt seinen BESTEN Zug (argmax-Visits, keine Temperatur, keine
/// Datenaufzeichnung). Liefert `{scores, winner, steps, total_floor,
/// floor_per_round}`.
fn play_arena_game<R: Rng + ?Sized>(
    sims: [u32; 2],
    c: f64,
    scoring_ids: Vec<usize>,
    names: [String; 2],
    first_player: usize,
    rng: &mut R,
) -> Value {
    let mut game = Game::start(names, first_player, scoring_ids, rng);
    let mut steps = 0u32;
    let mut guard = 0u32;
    let t_start = std::time::Instant::now();
    let timeout_secs = heuristic_game_timeout_secs(sims[0].max(sims[1]));
    loop {
        guard += 1;
        // Hänger-Schutz: Schritt-Limit ODER sims-skalierte Wall-Clock je Partie.
        // Bricht pathologische Nicht-Terminierungen ab (eine teure Netz-Suche pro
        // Schritt würde sonst stundenlang grinden), statt den ganzen Lauf zu blockieren.
        if guard > 100_000 || t_start.elapsed().as_secs() >= timeout_secs {
            break;
        }
        match game.state.phase {
            Phase::StartPlacement | Phase::Drafting => {
                if game.state.players.iter().any(|p| p.start_tile_pending) {
                    let first = game.state.current_player;
                    let non_starter = 1 - first;
                    let pi = if game.state.players[non_starter].start_tile_pending {
                        non_starter
                    } else if game.state.players[first].start_tile_pending {
                        first
                    } else {
                        break;
                    };
                    match choose_start_placement(&game.state, pi) {
                        Some((tid, r, c2, rot)) => {
                            let _ = apply_start_placement(&mut game.state, pi, tid, r, c2, rot);
                        }
                        None => break,
                    }
                    steps += 1;
                } else if game.state.phase == Phase::Drafting {
                    let pi = game.state.current_player;
                    let actions = drafting_actions(&game.state);
                    let chosen = if actions.len() == 1 {
                        actions[0].clone()
                    } else {
                        let s = dynamic_sims(sims[pi], actions.len());
                        search_drafting_action(&game.state, s, c, rng)
                            .unwrap_or_else(|| actions[0].clone())
                    };
                    let _ = game.apply_drafting(&chosen);
                    steps += 1;
                } else {
                    break;
                }
            }
            Phase::Tiling => {
                let pi = game.state.current_player;
                match resolve_tiling_step(&game.state, pi) {
                    TilingStep::Place(ta) => {
                        let _ = game.apply_single_tiling(pi, &ta);
                    }
                    TilingStep::Chips { row, chips } => {
                        apply_bonus_chips_with(&mut game.state.players[pi], row, &chips);
                    }
                    TilingStep::End => {
                        let _ = game.apply_tiling(&TilingMove::EndTiling { player: pi }, rng);
                    }
                }
                steps += 1;
            }
            _ => break,
        }
    }
    if game.state.phase == Phase::End {
        let _ = game.apply_end_scoring();
    }
    let p0 = &game.state.players[0];
    let p1 = &game.state.players[1];
    json!({
        "scores": [p0.score, p1.score],
        "winner": determine_winner(&game.state),
        "steps": steps,
        "total_floor": [p0.total_floor_penalties, p1.total_floor_penalties],
        "floor_per_round": [p0.floor_penalties_per_round, p1.floor_penalties_per_round],
    })
}

/// Spielt `n_games` Arena-Partien (rayon-parallel) zwischen zwei MCTS-Konfigs.
/// Brett 0 = Agent A (`sims_a`), Brett 1 = Agent B (`sims_b`). Spiel `i` hat den
/// Startspieler alternierend (`i % 2`), um den Startspieler-Vorteil auszugleichen.
/// Gibt ein geordnetes JSON-Array der Spielergebnisse zurück (Elo rechnet Python).
pub fn run_arena_match(
    sims_a: u32,
    sims_b: u32,
    n_games: usize,
    seed: u64,
    num_threads: usize,
    c: f64,
) -> String {
    let play = |i: usize| -> Value {
        let mut rng =
            StdRng::seed_from_u64(seed.wrapping_add((i as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15)));
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let first = i % 2;
        let names = ["A".to_string(), "B".to_string()];
        play_arena_game([sims_a, sims_b], c, ids, names, first, &mut rng)
    };

    let all: Vec<Value> = if num_threads == 0 {
        (0..n_games).into_par_iter().map(play).collect()
    } else {
        match rayon::ThreadPoolBuilder::new().num_threads(num_threads).build() {
            Ok(pool) => pool.install(|| (0..n_games).into_par_iter().map(play).collect()),
            Err(_) => (0..n_games).map(play).collect(),
        }
    };
    serde_json::to_string(&Value::Array(all)).unwrap_or_else(|_| "[]".to_string())
}

// ── Netz vs. Heuristik (Arena-Messung) ───────────────────────────────────────

/// Spielt EIN Spiel: Brett `net_board` zieht per Netz-PUCT, das andere per
/// Heuristik-MCTS. Tiling/Start für BEIDE per Solver/Heuristik (wie Arena).
#[allow(clippy::too_many_arguments)]
fn play_net_game<R: Rng + ?Sized>(
    net: &Net,
    net_board: usize,
    net_sims: u32,
    heur_sims: u32,
    c: f64,
    c_puct: f64,
    leaf: LeafEval,
    scoring_ids: Vec<usize>,
    names: [String; 2],
    first_player: usize,
    rng: &mut R,
) -> Value {
    let mut game = Game::start(names, first_player, scoring_ids, rng);
    let mut steps = 0u32;
    let mut guard = 0u32;
    let t_start = std::time::Instant::now();
    let timeout_secs = net_game_timeout_secs(net_sims.max(heur_sims));
    loop {
        guard += 1;
        // Hänger-Schutz: Schritt-Limit ODER sims-skalierte Wall-Clock je Partie.
        // Bricht pathologische Nicht-Terminierungen ab (eine teure Netz-Suche pro
        // Schritt würde sonst stundenlang grinden), statt den ganzen Lauf zu blockieren.
        if guard > 100_000 || t_start.elapsed().as_secs() >= timeout_secs {
            break;
        }
        match game.state.phase {
            Phase::StartPlacement | Phase::Drafting => {
                if game.state.players.iter().any(|p| p.start_tile_pending) {
                    let first = game.state.current_player;
                    let non_starter = 1 - first;
                    let pi = if game.state.players[non_starter].start_tile_pending {
                        non_starter
                    } else if game.state.players[first].start_tile_pending {
                        first
                    } else {
                        break;
                    };
                    match choose_start_placement(&game.state, pi) {
                        Some((tid, r, c2, rot)) => {
                            let _ = apply_start_placement(&mut game.state, pi, tid, r, c2, rot);
                        }
                        None => break,
                    }
                    steps += 1;
                } else if game.state.phase == Phase::Drafting {
                    let pi = game.state.current_player;
                    let actions = drafting_actions(&game.state);
                    let chosen = if actions.len() == 1 {
                        actions[0].clone()
                    } else if pi == net_board {
                        let s = dynamic_sims(net_sims, actions.len());
                        net_search_drafting_action(net, &game.state, s, c_puct, false, leaf, rng)
                            .unwrap_or_else(|| actions[0].clone())
                    } else {
                        let s = dynamic_sims(heur_sims, actions.len());
                        search_drafting_action(&game.state, s, c, rng)
                            .unwrap_or_else(|| actions[0].clone())
                    };
                    let _ = game.apply_drafting(&chosen);
                    steps += 1;
                } else {
                    break;
                }
            }
            Phase::Tiling => {
                let pi = game.state.current_player;
                match resolve_tiling_step(&game.state, pi) {
                    TilingStep::Place(ta) => {
                        let _ = game.apply_single_tiling(pi, &ta);
                    }
                    TilingStep::Chips { row, chips } => {
                        apply_bonus_chips_with(&mut game.state.players[pi], row, &chips);
                    }
                    TilingStep::End => {
                        let _ = game.apply_tiling(&TilingMove::EndTiling { player: pi }, rng);
                    }
                }
                steps += 1;
            }
            _ => break,
        }
    }
    if game.state.phase == Phase::End {
        let _ = game.apply_end_scoring();
    }
    let p0 = &game.state.players[0];
    let p1 = &game.state.players[1];
    json!({
        "scores": [p0.score, p1.score],
        "winner": determine_winner(&game.state),
        "steps": steps,
        "net_board": net_board,
        "total_floor": [p0.total_floor_penalties, p1.total_floor_penalties],
        "floor_per_round": [p0.floor_penalties_per_round, p1.floor_penalties_per_round],
    })
}

/// `n_games` Spiele Netz vs. Heuristik (Netz auf Brett 0, Startspieler alternierend).
/// Lädt das ONNX-Netz einmal. Gibt JSON-Array `[{scores:[netz,heur], winner, …}]`.
#[allow(clippy::too_many_arguments)]
pub fn run_net_arena_match(
    model_path: &str,
    net_sims: u32,
    heur_sims: u32,
    n_games: usize,
    seed: u64,
    num_threads: usize,
    c: f64,
    c_puct: f64,
    dfs_leaf: bool,
) -> Result<String, String> {
    let net = Net::load(model_path, crate::features::INPUT_SIZE).map_err(|e| e.to_string())?;
    let net = std::sync::Arc::new(net);
    let leaf = if dfs_leaf { LeafEval::Dfs } else { LeafEval::Net };

    let play = |i: usize| -> Value {
        let mut rng =
            StdRng::seed_from_u64(seed.wrapping_add((i as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15)));
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let first = i % 2;
        let names = ["Netz".to_string(), "Heuristik".to_string()];
        play_net_game(&net, 0, net_sims, heur_sims, c, c_puct, leaf, ids, names, first, &mut rng)
    };

    let all: Vec<Value> = if num_threads <= 1 {
        (0..n_games).map(play).collect()
    } else {
        match rayon::ThreadPoolBuilder::new().num_threads(num_threads).build() {
            Ok(pool) => pool.install(|| (0..n_games).into_par_iter().map(play).collect()),
            Err(_) => (0..n_games).map(play).collect(),
        }
    };
    Ok(serde_json::to_string(&Value::Array(all)).unwrap_or_else(|_| "[]".to_string()))
}

// ── Netz vs. Netz (Generationen-Vergleich) ───────────────────────────────────

/// Spielt EIN Spiel Netz A (Brett 0) vs. Netz B (Brett 1). Beide ziehen per
/// Netz-PUCT mit eigenem Netz/Sims; Tiling/Start für beide per Solver.
#[allow(clippy::too_many_arguments)]
fn play_net_vs_net_game<R: Rng + ?Sized>(
    net_a: &Net,
    net_b: &Net,
    sims_a: u32,
    sims_b: u32,
    c_puct_a: f64,
    c_puct_b: f64,
    leaf: LeafEval,
    scoring_ids: Vec<usize>,
    names: [String; 2],
    first_player: usize,
    rng: &mut R,
) -> Value {
    let mut game = Game::start(names, first_player, scoring_ids, rng);
    let mut steps = 0u32;
    let mut guard = 0u32;
    let t_start = std::time::Instant::now();
    let timeout_secs = net_game_timeout_secs(sims_a.max(sims_b));
    loop {
        guard += 1;
        // Hänger-Schutz: Schritt-Limit ODER sims-skalierte Wall-Clock je Partie.
        // Bricht pathologische Nicht-Terminierungen ab (eine teure Netz-Suche pro
        // Schritt würde sonst stundenlang grinden), statt den ganzen Lauf zu blockieren.
        if guard > 100_000 || t_start.elapsed().as_secs() >= timeout_secs {
            break;
        }
        match game.state.phase {
            Phase::StartPlacement | Phase::Drafting => {
                if game.state.players.iter().any(|p| p.start_tile_pending) {
                    let first = game.state.current_player;
                    let non_starter = 1 - first;
                    let pi = if game.state.players[non_starter].start_tile_pending {
                        non_starter
                    } else if game.state.players[first].start_tile_pending {
                        first
                    } else {
                        break;
                    };
                    match choose_start_placement(&game.state, pi) {
                        Some((tid, r, c2, rot)) => {
                            let _ = apply_start_placement(&mut game.state, pi, tid, r, c2, rot);
                        }
                        None => break,
                    }
                    steps += 1;
                } else if game.state.phase == Phase::Drafting {
                    let pi = game.state.current_player;
                    let actions = drafting_actions(&game.state);
                    let chosen = if actions.len() == 1 {
                        actions[0].clone()
                    } else {
                        let (net, base, cp) = if pi == 0 {
                            (net_a, sims_a, c_puct_a)
                        } else {
                            (net_b, sims_b, c_puct_b)
                        };
                        let s = dynamic_sims(base, actions.len());
                        net_search_drafting_action(net, &game.state, s, cp, false, leaf, rng)
                            .unwrap_or_else(|| actions[0].clone())
                    };
                    let _ = game.apply_drafting(&chosen);
                    steps += 1;
                } else {
                    break;
                }
            }
            Phase::Tiling => {
                let pi = game.state.current_player;
                match resolve_tiling_step(&game.state, pi) {
                    TilingStep::Place(ta) => {
                        let _ = game.apply_single_tiling(pi, &ta);
                    }
                    TilingStep::Chips { row, chips } => {
                        apply_bonus_chips_with(&mut game.state.players[pi], row, &chips);
                    }
                    TilingStep::End => {
                        let _ = game.apply_tiling(&TilingMove::EndTiling { player: pi }, rng);
                    }
                }
                steps += 1;
            }
            _ => break,
        }
    }
    if game.state.phase == Phase::End {
        let _ = game.apply_end_scoring();
    }
    let p0 = &game.state.players[0];
    let p1 = &game.state.players[1];
    json!({
        "scores": [p0.score, p1.score],
        "winner": determine_winner(&game.state),
        "steps": steps,
        "total_floor": [p0.total_floor_penalties, p1.total_floor_penalties],
        "floor_per_round": [p0.floor_penalties_per_round, p1.floor_penalties_per_round],
    })
}

/// `n_games` Spiele Netz A (Brett 0) vs. Netz B (Brett 1), Startspieler
/// alternierend. Lädt beide ONNX-Netze einmal. Gibt JSON-Array
/// `[{scores:[A,B], winner, …}]`. `dfs_leaf` wie sonst (Stufe 1/2).
#[allow(clippy::too_many_arguments)]
pub fn run_net_vs_net_arena(
    model_a: &str,
    model_b: &str,
    sims_a: u32,
    sims_b: u32,
    n_games: usize,
    seed: u64,
    num_threads: usize,
    c_puct_a: f64,
    c_puct_b: f64,
    dfs_leaf: bool,
) -> Result<String, String> {
    let net_a = std::sync::Arc::new(Net::load(model_a, crate::features::INPUT_SIZE).map_err(|e| e.to_string())?);
    let net_b = std::sync::Arc::new(Net::load(model_b, crate::features::INPUT_SIZE).map_err(|e| e.to_string())?);
    let leaf = if dfs_leaf { LeafEval::Dfs } else { LeafEval::Net };

    let play = |i: usize| -> Value {
        let mut rng =
            StdRng::seed_from_u64(seed.wrapping_add((i as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15)));
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let first = i % 2;
        let names = ["NetzA".to_string(), "NetzB".to_string()];
        play_net_vs_net_game(&net_a, &net_b, sims_a, sims_b, c_puct_a, c_puct_b, leaf, ids, names, first, &mut rng)
    };

    let all: Vec<Value> = if num_threads <= 1 {
        (0..n_games).map(play).collect()
    } else {
        match rayon::ThreadPoolBuilder::new().num_threads(num_threads).build() {
            Ok(pool) => pool.install(|| (0..n_games).into_par_iter().map(play).collect()),
            Err(_) => (0..n_games).map(play).collect(),
        }
    };
    Ok(serde_json::to_string(&Value::Array(all)).unwrap_or_else(|_| "[]".to_string()))
}

// ── Netzgeführtes Self-Play (AlphaZero-Loop, Stufe 1/2) ──────────────────────

/// Drafting-Policy aus der Netz-PUCT: Target = ROHE Visit-Verteilung N/ΣN
/// (kein q²/Schärfen — die Schärfe kommt aus der Suchtiefe). Gespielte Aktion ~
/// Visits (τ=1, Exploration; plus Dirichlet-Wurzel-Noise in der Suche).
fn net_drafting_policy<R: Rng + ?Sized>(
    net: &Net,
    state: &GameState,
    actions: &[Action],
    base_sims: u32,
    c_puct: f64,
    leaf: LeafEval,
    rng: &mut R,
) -> (Action, Vec<Value>) {
    let sims = dynamic_sims(base_sims, actions.len());
    let stats = net_root_child_stats(net, state, sims, c_puct, true, leaf, rng); // (Action, visits, q)
    let total: f64 = stats.iter().map(|(_, v, _)| *v as f64).sum();
    if stats.is_empty() || !(total > 0.0) {
        let a = actions.choose(rng).cloned().unwrap_or(Action::Pass);
        return (a.clone(), vec![json!({ "action": action_to_env_dict(state, &a), "prob": 1.0 })]);
    }
    let policy: Vec<Value> = stats
        .iter()
        .map(|(a, v, _)| {
            json!({ "action": action_to_env_dict(state, a), "prob": (*v as f64) / total })
        })
        .collect();
    let weights: Vec<f64> = stats.iter().map(|(_, v, _)| *v as f64).collect();
    let idx = weighted_index(&weights, total, rng);
    (stats[idx].0.clone(), policy)
}

/// Ein netzgeführtes Self-Play-Spiel. Wie `play_one_game`, aber Drafting per
/// Netz-PUCT (Priors vom Netz, Blatt per `leaf`) mit rohen Visit-Targets.
#[allow(clippy::too_many_arguments)]
fn play_net_self_play_game<R: Rng + ?Sized>(
    net: &Net,
    base_sims: u32,
    c_puct: f64,
    leaf: LeafEval,
    scoring_ids: Vec<usize>,
    names: [String; 2],
    first_player: usize,
    game_id: &str,
    rng: &mut R,
) -> Vec<Value> {
    let mut game = Game::start(names, first_player, scoring_ids, rng);
    let mut records: Vec<Map<String, Value>> = Vec::new();
    let mut guard = 0u32;
    let t_start = std::time::Instant::now();
    let timeout_secs = net_game_timeout_secs(base_sims);
    loop {
        guard += 1;
        // Hänger-Schutz: Schritt-Limit ODER sims-skalierte Wall-Clock je Partie.
        // Bricht pathologische Nicht-Terminierungen ab (eine teure Netz-Suche pro
        // Schritt würde sonst stundenlang grinden), statt den ganzen Lauf zu blockieren.
        if guard > 100_000 || t_start.elapsed().as_secs() >= timeout_secs {
            break;
        }
        match game.state.phase {
            Phase::StartPlacement | Phase::Drafting => {
                if game.state.players.iter().any(|p| p.start_tile_pending) {
                    match start_placement_step(&mut game, rng) {
                        Some(rec) => records.push(rec),
                        None => break,
                    }
                } else if game.state.phase == Phase::Drafting {
                    let player = game.state.current_player;
                    let actions = drafting_actions(&game.state);
                    let valid_actions: Vec<Value> =
                        actions.iter().map(|a| action_to_env_dict(&game.state, a)).collect();
                    let (chosen, policy) = if actions.len() == 1 {
                        let a = actions[0].clone();
                        let e = json!({ "action": action_to_env_dict(&game.state, &a), "prob": 1.0 });
                        (a, vec![e])
                    } else {
                        net_drafting_policy(net, &game.state, &actions, base_sims, c_puct, leaf, rng)
                    };
                    let moon_t = moon_order_target(&game.state, &chosen, player, rng);
                    let state_json = state_to_json(&game.state, true);
                    let _ = game.apply_drafting(&chosen);
                    let mut m = Map::new();
                    m.insert("state".into(), state_json);
                    m.insert("policy".into(), Value::Array(policy));
                    m.insert("valid_actions".into(), Value::Array(valid_actions));
                    m.insert(
                        "moon_order_target".into(),
                        moon_t.map(|v| json!(v)).unwrap_or(Value::Null),
                    );
                    m.insert("player".into(), json!(player));
                    records.push(m);
                } else {
                    break;
                }
            }
            Phase::Tiling => records.push(tiling_step(&mut game, rng)),
            _ => break,
        }
    }
    let completed = game.state.phase == Phase::End;
    if completed {
        let _ = game.apply_end_scoring();
    }
    let scores = [game.state.players[0].score, game.state.players[1].score];
    let winner = determine_winner(&game.state);
    records
        .into_iter()
        .map(|mut m| {
            m.insert("game_id".into(), json!(game_id));
            m.insert("scores".into(), json!(scores));
            m.insert("winner".into(), json!(winner));
            m.insert("completed".into(), json!(completed));
            Value::Object(m)
        })
        .collect()
}

/// Netzgeführtes Self-Play: `n_games` Partien (rayon-parallel), Netz vs. sich
/// selbst, rohe Visit-Targets. `dfs_leaf` = Stufe 1 (DFS-Blatt) vs. Stufe 2
/// (Netz-Value). Gibt alle Step-Records flach als JSON-Array zurück.
#[allow(clippy::too_many_arguments)]
pub fn run_net_self_play(
    model_path: &str,
    n_games: usize,
    base_sims: u32,
    c_puct: f64,
    seed: u64,
    num_threads: usize,
    dfs_leaf: bool,
    prefix: &str,
) -> Result<String, String> {
    let net = std::sync::Arc::new(Net::load(model_path, crate::features::INPUT_SIZE).map_err(|e| e.to_string())?);
    let leaf = if dfs_leaf { LeafEval::Dfs } else { LeafEval::Net };

    let play = |i: usize| -> Vec<Value> {
        let mut rng =
            StdRng::seed_from_u64(seed.wrapping_add((i as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15)));
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let first = rng.random_range(0..2usize);
        let names = ["Netz".to_string(), "Netz".to_string()];
        let gid = format!("{prefix}_g{}", i + 1);
        play_net_self_play_game(&net, base_sims, c_puct, leaf, ids, names, first, &gid, &mut rng)
    };

    let all: Vec<Vec<Value>> = if num_threads == 0 {
        (0..n_games).into_par_iter().map(play).collect()
    } else {
        match rayon::ThreadPoolBuilder::new().num_threads(num_threads).build() {
            Ok(pool) => pool.install(|| (0..n_games).into_par_iter().map(play).collect()),
            Err(_) => (0..n_games).map(play).collect(),
        }
    };
    let flat: Vec<Value> = all.into_iter().flatten().collect();
    Ok(serde_json::to_string(&Value::Array(flat)).unwrap_or_else(|_| "[]".to_string()))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn play_one_game_terminates_with_records() {
        let mut rng = StdRng::seed_from_u64(123);
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let recs = play_one_game(
            40,
            SELF_PLAY_C,
            ids,
            ["P0".into(), "P1".into()],
            0,
            "test_g1",
            &mut rng,
        );
        assert!(!recs.is_empty(), "Spiel muss Records erzeugen");
        for r in &recs {
            let o = r.as_object().unwrap();
            for key in ["state", "policy", "valid_actions", "player", "scores", "winner", "game_id"] {
                assert!(o.contains_key(key), "Record fehlt Key {key}");
            }
            // Policy-Wahrscheinlichkeiten summieren ~1.
            let sum: f64 = o["policy"]
                .as_array()
                .unwrap()
                .iter()
                .map(|p| p["prob"].as_f64().unwrap())
                .sum();
            assert!((sum - 1.0).abs() < 1e-6, "Policy-Summe {sum} ≠ 1");
            // Jede Policy-Aktion ist in valid_actions enthalten (Maskenkonsistenz).
            let valid = o["valid_actions"].as_array().unwrap();
            for p in o["policy"].as_array().unwrap() {
                let pa = &p["action"];
                assert!(
                    valid.iter().any(|v| env_action_eq(v, pa)),
                    "Policy-Aktion {pa} nicht in valid_actions"
                );
            }
        }
    }

    /// Vergleicht zwei env-Action-Dicts über die Felder, die `action_to_id` liest.
    fn env_action_eq(a: &Value, b: &Value) -> bool {
        let keys = [
            "type",
            "factory_index",
            "color",
            "row",
            "display_index",
            "slot_row",
            "slot_col",
            "rotation",
            "pattern_row",
        ];
        keys.iter().all(|k| a.get(k) == b.get(k))
    }

    #[test]
    fn run_self_play_returns_valid_json() {
        let out = run_self_play(2, 30, SELF_PLAY_C, 7, 2, "vtest");
        let parsed: Value = serde_json::from_str(&out).unwrap();
        assert!(parsed.as_array().unwrap().len() > 0);
    }

    #[test]
    fn arena_match_produces_results() {
        let out = run_arena_match(40, 60, 4, 99, 2, SELF_PLAY_C);
        let games: Value = serde_json::from_str(&out).unwrap();
        let arr = games.as_array().unwrap();
        assert_eq!(arr.len(), 4);
        for g in arr {
            assert!(g["scores"].as_array().unwrap().len() == 2);
            let w = g["winner"].as_u64().unwrap();
            assert!(w == 0 || w == 1);
            assert!(g["steps"].as_u64().unwrap() > 0);
            assert_eq!(g["floor_per_round"].as_array().unwrap().len(), 2);
        }
    }

    #[test]
    fn no_tiling_deadlock_across_seeds() {
        // Regression: ein Solver-`End` bei offenen (nur per neuer Kuppelplatte
        // legbaren) Reihen führte früher zu einer end_tiling-Endlosschleife
        // (bis zum 100k-Guard). Eine normale Partie hat wenige hundert Steps.
        for seed in 0..12u64 {
            let mut rng = StdRng::seed_from_u64(seed);
            let ids = sample_valid_scoring_ids(3, &mut rng);
            let recs = play_one_game(
                30,
                SELF_PLAY_C,
                ids,
                ["P0".into(), "P1".into()],
                (seed % 2) as usize,
                "seedcheck",
                &mut rng,
            );
            assert!(
                recs.len() < 3000,
                "Seed {seed}: {} Steps — Deadlock-Verdacht (Tiling-End-Schleife)",
                recs.len()
            );
            // Regression Policy-Leak: jede Policy-Aktion MUSS in valid_actions
            // liegen (sonst Target-Masse auf maskierter Aktion → Policy-Loss-
            // Explosion im Training). Traf früher seltene Tiling-Nicht-Top-Reihen.
            for r in &recs {
                let o = r.as_object().unwrap();
                let valid = o["valid_actions"].as_array().unwrap();
                for p in o["policy"].as_array().unwrap() {
                    let pa = &p["action"];
                    assert!(
                        valid.iter().any(|v| env_action_eq(v, pa)),
                        "Seed {seed}: Policy-Aktion {pa} nicht in valid_actions (Leak)"
                    );
                }
            }
        }
    }
}
