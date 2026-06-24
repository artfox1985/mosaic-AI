//! MCTS bis zum Rundenende — Port der Kern-Features aus agents/mcts.py
//! (HeuristicMCTSAgent): Progressive Widening, UCB c = 0.3, sublineares
//! Wachstum, `player_who_acted`-Backprop und Win-Prob-Bewertung.
//!
//! Bewusst einfaches „Shaping": der Wert eines Zustands ist allein
//! `(eigene Punkte + Schätzung) − (gegnerische Punkte + Schätzung)` (siehe
//! [`crate::evaluate`]), per Sigmoid (`diff_to_probs`) in (0, 1) abgebildet.
//!
//! Phasen-Umfang: Der Suchbaum läuft über Drafting UND die Tiling-Phase der
//! laufenden Runde (strikt Reihe für Reihe, inkl. Bonus-Chips), stoppt aber am
//! Rundenende — der Rundenwechsel (RNG/Neubefüllen) wird NICHT betreten.
//! Strafpunkte werden am Rundenende-Blatt nicht angewandt; `estimate_round_score`
//! enthält Boden-/Marker-Strafen bereits.

use rand::seq::SliceRandom;
use rand::{Rng, RngExt};
use serde_json::{json, Value};

use crate::evaluate::estimate_round_score;
use crate::game::{drafting_actions, Game};
use crate::moves::Action;
use crate::round_end::{
    apply_bonus_chips_to_row, can_complete_row_with_chips, execute_full_tiling,
    generate_tiling_actions, row_has_open_matching_slot, TilingAction,
};
use crate::serialize::{action_to_dict, tiling_action_to_dict};
use crate::state::{GameState, Phase};

/// Initialwelle an Aktionen pro Knoten (Progressive Widening).
pub const MAX_ACTIONS: usize = 10;
/// Faktor des sublinearen Wachstums: `allowed = MAX_ACTIONS + WIDEN_FACTOR·√N`.
pub const WIDEN_FACTOR: f64 = 2.5;
/// Standard-Explorationskonstante (wie agents/mcts.py).
pub const DEFAULT_C: f64 = 0.3;

/// Vereinheitlichter Such-Zug über Drafting- und Tiling-Phase.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SearchMove {
    Draft(Action),
    TilePlace(TilingAction),
    TileChips { player: usize, row: usize },
    TileEnd { player: usize },
}

struct Node {
    parent: Option<usize>,
    children: Vec<usize>,
    untried: Vec<SearchMove>,
    /// Für Progressive Widening zurückgehaltene, nach Güte sortierte Aktionen.
    remaining: Vec<SearchMove>,
    action: Option<SearchMove>,
    /// Spieler, der den Zug zu diesem Knoten gemacht hat (Backprop-Perspektive).
    player_who_acted: usize,
    visits: u32,
    value: f64,
    state: GameState,
    terminal: bool,
    /// Anzahl legaler Züge in diesem Zustand (für die aktionsabhängige Sigmoid-scale).
    n_actions: usize,
}

// ── Bewertung ────────────────────────────────────────────────────────────────

fn player_total(state: &GameState, pi: usize) -> f64 {
    state.players[pi].score as f64 + estimate_round_score(&state.players[pi], true) as f64
}

/// Aktionsabhängige Sigmoid-scale (Port von agents/mcts.py `_scale_for_actions`).
fn scale_for_actions(n: usize) -> f64 {
    if n > 50 {
        2.0
    } else if n > 15 {
        5.0
    } else {
        7.0
    }
}

/// Punktedifferenz → Win-Wahrscheinlichkeiten [p0, p1] (Port von `_diff_to_probs`).
fn diff_to_probs(diff: f64, scale: f64) -> [f64; 2] {
    let safe = diff.clamp(-200.0, 200.0);
    let p0 = 1.0 / (1.0 + (-safe / scale).exp());
    [p0, 1.0 - p0]
}

/// Blattbewertung als Per-Spieler-Win-Prob (absolut, nicht perspektivisch).
fn evaluate(state: &GameState, n_actions: usize) -> [f64; 2] {
    let diff = player_total(state, 0) - player_total(state, 1);
    diff_to_probs(diff, scale_for_actions(n_actions))
}

// ── Zuggenerierung & -ausführung über beide Phasen ───────────────────────────

/// Chippbare Reihen eines Spielers (komplettierbar UND danach platzierbar,
/// Reihenfolge oben→unten respektiert) — analog serialize_chippable_tiling_rows.
fn chippable_rows(state: &GameState, pi: usize) -> Vec<usize> {
    let player = &state.players[pi];
    if player.bonus_chips.is_empty() {
        return Vec::new();
    }
    let tiled_max = player.tiled_max_row;
    let mut out = Vec::new();
    for (ri, row) in player.pattern_lines.iter().enumerate() {
        if row.tiles.is_empty() || row.is_complete() {
            continue;
        }
        if (ri as i32) < tiled_max {
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
            out.push(ri);
        }
    }
    out
}

fn valid_search_moves(state: &GameState) -> Vec<SearchMove> {
    match state.phase {
        Phase::Drafting => drafting_actions(state).into_iter().map(SearchMove::Draft).collect(),
        Phase::Tiling => {
            let cp = state.current_player;
            let places = generate_tiling_actions(state, cp);
            let mut moves: Vec<SearchMove> =
                places.iter().map(|ta| SearchMove::TilePlace(*ta)).collect();
            for ri in chippable_rows(state, cp) {
                moves.push(SearchMove::TileChips { player: cp, row: ri });
            }
            // EndTiling nur, wenn keine Reihe mehr platzierbar ist (Server-Regel).
            if places.is_empty() {
                moves.push(SearchMove::TileEnd { player: cp });
            }
            moves
        }
        _ => Vec::new(),
    }
}

/// Wendet einen Such-Zug auf einen Klon an. Gibt (neuer Zustand, round_over)
/// zurück; `round_over == true` markiert das Rundenende (Knoten wird terminal,
/// KEIN Rundenwechsel). None bei (unerwartet) ungültigem Zug.
fn apply_search_move(state: &GameState, mv: &SearchMove) -> Option<(GameState, bool)> {
    match mv {
        SearchMove::Draft(a) => {
            let mut g = Game { state: state.clone() };
            g.apply_drafting(a).ok()?;
            let mut s = g.state;
            s.log.clear();
            Some((s, false))
        }
        SearchMove::TilePlace(ta) => {
            let mut s = state.clone();
            let cp = s.current_player;
            execute_full_tiling(&mut s, cp, ta).ok()?;
            s.log.clear();
            Some((s, false))
        }
        SearchMove::TileChips { player, row } => {
            let mut s = state.clone();
            if !apply_bonus_chips_to_row(&mut s.players[*player], *row) {
                return None;
            }
            s.log.clear();
            Some((s, false))
        }
        SearchMove::TileEnd { player } => {
            let mut s = state.clone();
            s.tiling_done[*player] = true;
            let other = 1 - *player;
            let round_over = s.tiling_done[other];
            if !round_over {
                s.current_player = other;
            }
            s.log.clear();
            Some((s, round_over))
        }
    }
}

// ── Aktions-Ranking für Widening ─────────────────────────────────────────────

/// Teures 1-Ply-Heuristik-Ranking (nur an der Wurzel): jede Aktion ausführen und
/// nach `total(acting) − total(other)` absteigend sortieren.
fn rank_actions_root(state: &GameState, moves: Vec<SearchMove>) -> Vec<SearchMove> {
    let acting = state.current_player;
    let other = 1 - acting;
    let mut scored: Vec<(f64, SearchMove)> = moves
        .into_iter()
        .map(|m| {
            let score = match apply_search_move(state, &m) {
                Some((child, _)) => player_total(&child, acting) - player_total(&child, other),
                None => f64::NEG_INFINITY,
            };
            (score, m)
        })
        .collect();
    scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));
    scored.into_iter().map(|(_, m)| m).collect()
}

fn move_priority(m: &SearchMove) -> i32 {
    match m {
        SearchMove::TilePlace(_) => 8,
        SearchMove::TileChips { .. } => 7,
        SearchMove::TileEnd { .. } => 0,
        SearchMove::Draft(a) => match a {
            Action::BonusChip(_) => 6,
            Action::Stone(_) => 4,
            Action::Dome(_) => 3,
            Action::DrawStack(_) => 2,
            Action::Pass => 1,
        },
    }
}

/// Billiges Ranking für tiefe Knoten: nach Typ-Priorität (innerhalb gleich:
/// zufällig).
fn rank_actions_cheap<R: Rng + ?Sized>(mut moves: Vec<SearchMove>, rng: &mut R) -> Vec<SearchMove> {
    moves.shuffle(rng);
    moves.sort_by(|a, b| move_priority(b).cmp(&move_priority(a)));
    moves
}

// ── Knoten ───────────────────────────────────────────────────────────────────

#[allow(clippy::too_many_arguments)]
fn make_node<R: Rng + ?Sized>(
    state: GameState,
    parent: Option<usize>,
    action: Option<SearchMove>,
    player_who_acted: usize,
    terminal: bool,
    is_root: bool,
    rng: &mut R,
) -> Node {
    let (untried, remaining, n_actions) = if terminal {
        (Vec::new(), Vec::new(), 0)
    } else {
        let moves = valid_search_moves(&state);
        let n = moves.len();
        let mut ordered = if is_root {
            rank_actions_root(&state, moves)
        } else {
            rank_actions_cheap(moves, rng)
        };
        let remaining = if ordered.len() > MAX_ACTIONS {
            ordered.split_off(MAX_ACTIONS)
        } else {
            Vec::new()
        };
        (ordered, remaining, n)
    };
    Node {
        parent,
        children: Vec::new(),
        untried,
        remaining,
        action,
        player_who_acted,
        visits: 0,
        value: 0.0,
        state,
        terminal,
        n_actions,
    }
}

/// UCB1 (c = 0.3): bestes Kind aus Sicht des Knoten-Spielers. Da alle Kinder
/// vom selben Spieler (current_player des Knotens) erzeugt werden und ihr Wert
/// aus `player_who_acted`-Sicht gespeichert ist, wird NICHT negiert.
fn best_uct_child(nodes: &[Node], nid: usize, c: f64) -> usize {
    let ln_parent = (nodes[nid].visits.max(1) as f64).ln();
    let mut best = nodes[nid].children[0];
    let mut best_score = f64::NEG_INFINITY;
    for &cid in &nodes[nid].children {
        let n = nodes[cid].visits as f64;
        let exploit = nodes[cid].value / n;
        let explore = c * (ln_parent / n).sqrt();
        let score = exploit + explore;
        if score > best_score {
            best_score = score;
            best = cid;
        }
    }
    best
}

fn is_terminal_phase(state: &GameState) -> bool {
    matches!(state.phase, Phase::End | Phase::Final)
}

/// Baut den Suchbaum (Wurzel = Index 0). None, wenn `state` weder in der
/// Drafting- noch in der Tiling-Phase ist (KI sucht in beiden Phasen).
fn build_tree<R: Rng + ?Sized>(
    state: &GameState,
    simulations: u32,
    c: f64,
    rng: &mut R,
) -> Option<Vec<Node>> {
    if !matches!(state.phase, Phase::Drafting | Phase::Tiling) {
        return None;
    }

    let mut root_state = state.clone();
    root_state.log.clear();
    let root_player = root_state.current_player;
    let mut nodes: Vec<Node> =
        vec![make_node(root_state, None, None, root_player, false, true, rng)];

    for _ in 0..simulations {
        // 1. Selection (mit Progressive Widening).
        let mut nid = 0;
        loop {
            if nodes[nid].terminal {
                break;
            }
            // Widening: eine reservierte Aktion freischalten, sobald untried leer
            // ist und das sublineare Budget noch Platz lässt.
            if nodes[nid].untried.is_empty() && !nodes[nid].remaining.is_empty() {
                let allowed =
                    MAX_ACTIONS + (WIDEN_FACTOR * (nodes[nid].visits as f64).sqrt()) as usize;
                if nodes[nid].children.len() < allowed {
                    let mv = nodes[nid].remaining.remove(0);
                    nodes[nid].untried.push(mv);
                }
            }
            if !nodes[nid].untried.is_empty() {
                break; // hier expandieren
            }
            if nodes[nid].children.is_empty() {
                break; // (sollte bei nicht-terminal nicht auftreten)
            }
            nid = best_uct_child(&nodes, nid, c);
        }

        // 2. Expansion (eine zufällige unversuchte Aktion).
        if !nodes[nid].terminal && !nodes[nid].untried.is_empty() {
            let idx = rng.random_range(0..nodes[nid].untried.len());
            let mv = nodes[nid].untried.swap_remove(idx);
            let mover = nodes[nid].state.current_player;
            if let Some((child_state, round_over)) = apply_search_move(&nodes[nid].state, &mv) {
                let terminal = round_over || is_terminal_phase(&child_state);
                let child = make_node(child_state, Some(nid), Some(mv), mover, terminal, false, rng);
                let cid = nodes.len();
                nodes.push(child);
                nodes[nid].children.push(cid);
                nid = cid;
            }
        }

        // 3. Blattbewertung (Per-Spieler-Win-Prob).
        let value = evaluate(&nodes[nid].state, nodes[nid].n_actions);

        // 4. Backprop (player_who_acted, ohne Vorzeichenwechsel).
        let mut cur = Some(nid);
        while let Some(i) = cur {
            nodes[i].visits += 1;
            nodes[i].value += value[nodes[i].player_who_acted];
            cur = nodes[i].parent;
        }
    }

    Some(nodes)
}

/// Meistbesuchtes Wurzelkind (Tiebreak: Mittelwert Q).
fn best_root_child(nodes: &[Node]) -> Option<usize> {
    nodes[0].children.iter().copied().max_by(|&a, &b| {
        let qa = nodes[a].value / nodes[a].visits.max(1) as f64;
        let qb = nodes[b].value / nodes[b].visits.max(1) as f64;
        nodes[a]
            .visits
            .cmp(&nodes[b].visits)
            .then(qa.partial_cmp(&qb).unwrap_or(std::cmp::Ordering::Equal))
    })
}

/// Tiefe des Teilbaums unter `nid` (0 = Blatt).
fn subtree_depth(nodes: &[Node], nid: usize) -> u32 {
    let children = &nodes[nid].children;
    if children.is_empty() {
        0
    } else {
        1 + children.iter().map(|&c| subtree_depth(nodes, c)).max().unwrap()
    }
}

/// Typ, Beschreibung, Kategorie (für `.cat-*` in debug.html) und Move-Dict.
fn label_search_move(sm: &SearchMove) -> (&'static str, String, &'static str, Value) {
    match sm {
        SearchMove::Draft(a) => match a {
            Action::Stone(m) => {
                let cat = if m.place.row_index < 0 { "penalty" } else { "row" };
                let dest = if m.place.row_index < 0 {
                    "Strafleiste".to_string()
                } else {
                    format!("Reihe {}", m.place.row_index + 1)
                };
                let src = match m.take.factory_id {
                    Some(id) => format!("F{id}"),
                    None => "GF".to_string(),
                };
                let desc = format!("Stein {} von {src} → {dest}", m.take.color.value());
                ("stone", desc, cat, action_to_dict(a))
            }
            Action::Dome(m) => (
                "dome",
                format!("Kuppel #{} → ({},{}) {}°", m.dome_tile_id, m.slot_row, m.slot_col, m.rotation),
                "dome",
                action_to_dict(a),
            ),
            Action::DrawStack(m) => (
                "dome_stack",
                format!("Stapel → ({},{}) {}°", m.slot_row, m.slot_col, m.rotation),
                "dome",
                action_to_dict(a),
            ),
            Action::BonusChip(m) => (
                "bonus_chip",
                format!("Bonuschip F{}", m.factory_id),
                "chip",
                action_to_dict(a),
            ),
            Action::Pass => ("pass", "Pass".to_string(), "pass", action_to_dict(a)),
        },
        SearchMove::TilePlace(ta) => (
            "tiling",
            format!("Tiling R{} → Slot({},{}) Sp{}", ta.pattern_row + 1, ta.slot_row, ta.slot_col, ta.space_index),
            "tiling",
            tiling_action_to_dict(ta),
        ),
        SearchMove::TileChips { row, .. } => (
            "use_chips",
            format!("Chips R{}", row + 1),
            "chip",
            json!({ "type": "use_chips", "pattern_row": row }),
        ),
        SearchMove::TileEnd { .. } => {
            ("end_tiling", "Tiling beenden".to_string(), "pass", json!({ "type": "end_tiling" }))
        }
    }
}

/// Serialisiert einen Knoten rekursiv (bis `depth_left`, je Knoten `top_k`
/// meistbesuchte Kinder) für das Debug-Baum-Panel.
fn serialize_node(nodes: &[Node], nid: usize, depth_left: u32, top_k: usize) -> Value {
    let node = &nodes[nid];
    let q = if node.visits > 0 { node.value / node.visits as f64 } else { 0.0 };
    let (typ, desc, cat, mv) = match &node.action {
        None => ("root", "Wurzel".to_string(), "pass", Value::Null),
        Some(sm) => label_search_move(sm),
    };
    let children = if depth_left > 0 && !node.children.is_empty() {
        let mut ch = node.children.clone();
        ch.sort_by(|a, b| nodes[*b].visits.cmp(&nodes[*a].visits));
        ch.truncate(top_k);
        ch.iter().map(|&c| serialize_node(nodes, c, depth_left - 1, top_k)).collect::<Vec<_>>()
    } else {
        Vec::new()
    };
    json!({
        "type": typ,
        "description": desc,
        "category": cat,
        "move": mv,
        "visits": node.visits,
        "q": q,
        "win_pct": q * 100.0,
        "depth": subtree_depth(nodes, nid),
        "player_who_acted": node.player_who_acted,
        "n_children": node.children.len(),
        "children": children,
    })
}

/// Anzeige-JSON einer Suchaktion (`{type, description, category, move}`).
pub fn search_move_json(sm: &SearchMove) -> Value {
    let (typ, desc, cat, mv) = label_search_move(sm);
    json!({ "type": typ, "description": desc, "category": cat, "move": mv })
}

/// Beste Aktion (Drafting ODER Tiling) für `state`. None, wenn `state` weder
/// Drafting noch Tiling ist.
pub fn search_action<R: Rng + ?Sized>(
    state: &GameState,
    simulations: u32,
    c: f64,
    rng: &mut R,
) -> Option<SearchMove> {
    let nodes = build_tree(state, simulations, c, rng)?;
    let best = best_root_child(&nodes)?;
    nodes[best].action.clone()
}

/// Wie [`search_action`], liefert zusätzlich ein debug.html-kompatibles
/// Analyse-Dict (Per-Zug-Statistik `moves[]` + serialisierter `tree`).
pub fn search_with_tree<R: Rng + ?Sized>(
    state: &GameState,
    simulations: u32,
    c: f64,
    rng: &mut R,
    max_depth: u32,
    top_k: usize,
) -> (Option<SearchMove>, Value) {
    let nodes = match build_tree(state, simulations, c, rng) {
        Some(n) => n,
        None => return (None, Value::Null),
    };
    let best = best_root_child(&nodes);
    let total_visits: u32 = nodes[0].children.iter().map(|&c| nodes[c].visits).sum();

    let mut child_ids = nodes[0].children.clone();
    child_ids.sort_by(|a, b| nodes[*b].visits.cmp(&nodes[*a].visits));

    let mut chosen_id: Option<usize> = None;
    let moves: Vec<Value> = child_ids
        .iter()
        .enumerate()
        .map(|(i, &cid)| {
            let node = &nodes[cid];
            let q = if node.visits > 0 { node.value / node.visits as f64 } else { 0.0 };
            let (typ, desc, cat, _mv) = match &node.action {
                Some(sm) => label_search_move(sm),
                None => ("?", "?".to_string(), "pass", Value::Null),
            };
            let is_chosen = best == Some(cid);
            if is_chosen {
                chosen_id = Some(i);
            }
            json!({
                "action_id": i,
                "type": typ,
                "description": desc,
                "category": cat,
                "net_prob": Value::Null,
                "net_prob_norm": Value::Null,
                "mcts_visits": node.visits,
                "mcts_share": if total_visits > 0 { node.visits as f64 / total_visits as f64 } else { 0.0 },
                "mcts_q": q,
                "mcts_win_pct": q * 100.0,
                "max_depth": subtree_depth(&nodes, cid),
                "shaping": Value::Null,
                "chosen": is_chosen,
            })
        })
        .collect();

    let analysis = json!({
        "current_player": nodes[0].player_who_acted,
        "ai_player": nodes[0].player_who_acted,
        "value": Value::Null,
        "win_pct": Value::Null,
        "has_net": false,
        "simulations": simulations,
        "num_actions": nodes[0].n_actions,
        "max_depth": subtree_depth(&nodes, 0),
        "ai_action": chosen_id,
        "moves": moves,
        "tree": serialize_node(&nodes, 0, max_depth, top_k),
    });

    let chosen = best.and_then(|cid| nodes[cid].action.clone());
    (chosen, analysis)
}

/// Beste Drafting-Aktion (dünner Wrapper; None außerhalb Drafting bzw. wenn die
/// beste Wurzelaktion kein Drafting-Zug ist).
pub fn search_drafting_action<R: Rng + ?Sized>(
    state: &GameState,
    simulations: u32,
    c: f64,
    rng: &mut R,
) -> Option<Action> {
    match search_action(state, simulations, c, rng)? {
        SearchMove::Draft(a) => Some(a),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dome::build_dome_tile_pool;
    use crate::state::setup_new_game;
    use crate::tile::TileColor::*;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    fn drafting_state(seed: u64) -> GameState {
        let mut rng = StdRng::seed_from_u64(seed);
        let mut s = setup_new_game(["P1".into(), "P2".into()], 0, &mut rng);
        for p in s.players.iter_mut() {
            p.start_tile_pending = false;
        }
        s
    }

    #[test]
    fn returns_a_legal_drafting_action() {
        let s = drafting_state(7);
        let mut rng = StdRng::seed_from_u64(1);
        let action = search_drafting_action(&s, 200, DEFAULT_C, &mut rng).expect("Aktion");
        assert!(drafting_actions(&s).contains(&action), "MCTS-Aktion muss legal sein");
    }

    #[test]
    fn none_outside_drafting() {
        let mut s = drafting_state(7);
        s.phase = Phase::Tiling;
        let mut rng = StdRng::seed_from_u64(3);
        assert!(search_drafting_action(&s, 10, DEFAULT_C, &mut rng).is_none());
    }

    #[test]
    fn progressive_widening_grows_children_beyond_initial_wave() {
        // Frühes Drafting hat weit mehr als MAX_ACTIONS legale Züge.
        let s = drafting_state(7);
        assert!(valid_search_moves(&s).len() > MAX_ACTIONS);
        let mut rng = StdRng::seed_from_u64(2);
        let nodes = build_tree(&s, 300, DEFAULT_C, &mut rng).unwrap();
        // allowed = 10 + 2.5*sqrt(300) ≈ 53 → Wurzel muss > MAX_ACTIONS Kinder haben.
        assert!(
            nodes[0].children.len() > MAX_ACTIONS,
            "Widening sollte mehr als {MAX_ACTIONS} Kinder erzeugen, hat {}",
            nodes[0].children.len()
        );
    }

    #[test]
    fn tiling_state_yields_place_moves() {
        // Reihe 0 (cap 1) mit Rot voll; Slot (0,0) = pool[2] hat si1 = Rot.
        let mut s = drafting_state(7);
        s.phase = Phase::Tiling;
        let tile = build_dome_tile_pool()[2].clone();
        s.players[0].dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        s.players[0].pattern_lines[0].add_tiles(&[Rot]);
        let moves = valid_search_moves(&s);
        assert!(moves.iter().any(|m| matches!(m, SearchMove::TilePlace(_))));
        // Solange platzierbar, KEIN TileEnd.
        assert!(!moves.iter().any(|m| matches!(m, SearchMove::TileEnd { .. })));
    }

    #[test]
    fn tile_end_marks_round_over_when_both_done() {
        // Tiling-Zustand ohne platzierbare Reihen → TileEnd verfügbar.
        let mut s = drafting_state(7);
        s.phase = Phase::Tiling;
        s.tiling_done = [false, true]; // Gegner schon fertig
        let cp = s.current_player; // 0
        s.tiling_done[1 - cp] = true;
        let moves = valid_search_moves(&s);
        let end = moves
            .iter()
            .find(|m| matches!(m, SearchMove::TileEnd { .. }))
            .expect("TileEnd verfügbar");
        let (_st, round_over) = apply_search_move(&s, end).unwrap();
        assert!(round_over, "beide fertig → Rundenende");
    }

    #[test]
    fn chippable_row_yields_chips_move() {
        use crate::dome::BonusChip;
        let mut s = drafting_state(7);
        s.phase = Phase::Tiling;
        // Reihe 2 (cap 3): 1 Rot gelegt → 2 fehlen; 4 Rot-Chips → komplettierbar.
        s.players[0].pattern_lines[2].add_tiles(&[Rot]);
        for i in 0..4 {
            s.players[0].bonus_chips.push(BonusChip { chip_id: i, colors: vec![Rot] });
        }
        // Dome-Reihe 1 (Reihe 2 → dome_row 1) braucht einen Slot mit offenem
        // Rot-Space an valid_si [0,1]. pool[2] = [Tuerkis, Rot, Blau, Wild]: si1 = Rot.
        let tile = build_dome_tile_pool()[2].clone();
        s.players[0].dome_grid.place_dome_tile(tile, 1, 0).unwrap();
        let moves = valid_search_moves(&s);
        assert!(
            moves.iter().any(|m| matches!(m, SearchMove::TileChips { row: 2, .. })),
            "chippbare Reihe 2 sollte ein TileChips erzeugen"
        );
    }

    #[test]
    fn does_not_dump_to_floor_early() {
        let s = drafting_state(11);
        let mut rng = StdRng::seed_from_u64(4);
        let action = search_drafting_action(&s, 400, DEFAULT_C, &mut rng).expect("Aktion");
        if let Action::Stone(m) = &action {
            assert_ne!(m.place.row_index, -1, "MCTS sollte nicht auf die Strafleiste werfen");
        }
    }

    #[test]
    fn search_does_not_advance_round() {
        // Die Suche darf den Rundenwechsel nie betreten (Rundennummer bleibt).
        let s = drafting_state(7);
        let round_before = s.round_number;
        let mut rng = StdRng::seed_from_u64(9);
        let _ = search_drafting_action(&s, 300, DEFAULT_C, &mut rng);
        assert_eq!(s.round_number, round_before);
    }

    #[test]
    fn search_action_works_for_tiling_root() {
        // Tiling-Wurzel mit platzierbarer Reihe → search_action liefert TilePlace.
        let mut s = drafting_state(7);
        s.phase = Phase::Tiling;
        let tile = build_dome_tile_pool()[2].clone(); // si1 = Rot
        s.players[0].dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        s.players[0].pattern_lines[0].add_tiles(&[Rot]);
        let mut rng = StdRng::seed_from_u64(5);
        let mv = search_action(&s, 150, DEFAULT_C, &mut rng).expect("Tiling-Aktion");
        assert!(matches!(mv, SearchMove::TilePlace(_) | SearchMove::TileEnd { .. }));
    }

    #[test]
    fn search_with_tree_produces_valid_tree() {
        let s = drafting_state(7);
        let mut rng = StdRng::seed_from_u64(6);
        let (chosen, analysis) = search_with_tree(&s, 300, DEFAULT_C, &mut rng, 3, 8);
        assert!(chosen.is_some());
        let tree = &analysis["tree"];
        assert!(tree["children"].as_array().unwrap().len() > 0);
        // Wurzelkinder ≤ top_k im Baum.
        assert!(tree["children"].as_array().unwrap().len() <= 8);
        // moves[] vorhanden, Summe der Visits ≈ Simulationen (jede Sim besucht Wurzel).
        let moves = analysis["moves"].as_array().unwrap();
        assert!(!moves.is_empty());
        let sum: u64 = moves.iter().map(|m| m["mcts_visits"].as_u64().unwrap()).sum();
        assert!(sum >= 290 && sum <= 300, "Visit-Summe {sum} ~ 300");
    }
}
