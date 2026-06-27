//! AlphaZero-PUCT-Suche über die Drafting-Phase (Network-Modus, Phase B).
//!
//! Gleiche Baumstruktur wie der Heuristik-MCTS (`crate::mcts`), aber:
//!   - Selektion per **PUCT** mit Netz-Priors statt UCB1,
//!   - Blattbewertung = **Netz-Value** (Tanh → Win-Prob) statt DFS-Solver,
//!   - **Dirichlet-Wurzel-Noise** (Self-Play-Exploration).
//! Lazy Expansion nach Prior (höchster zuerst) + Progressive Widening.

use rand::{Rng, RngExt};

use crate::features::{action_to_id, state_to_features};
use crate::game::{drafting_actions, Game};
use crate::mcts::{MAX_ACTIONS, WIDEN_FACTOR};
use crate::moves::Action;
use crate::net::{softmax, Net};
use crate::self_play::action_to_env_dict;
use crate::serialize::state_to_json;
use crate::state::{GameState, Phase};

/// Aktionsraum-Größe (= `config.NUM_ACTIONS`).
const NUM_ACTIONS: usize = 482;
/// Standard-PUCT-Konstante (= agents/mcts.py `_c_puct`).
pub const DEFAULT_C_PUCT: f64 = 1.5;
/// Dirichlet-Wurzel-Noise (AlphaZero-Standard).
pub const DIRICHLET_EPS: f64 = 0.25;
pub const DIRICHLET_ALPHA: f64 = 0.3;

struct Node {
    parent: Option<usize>,
    children: Vec<usize>,
    /// Noch nicht expandierte (Aktion, Prior), absteigend nach Prior sortiert.
    untried: Vec<(Action, f32)>,
    action: Option<Action>,
    player_who_acted: usize,
    visits: u32,
    value: f64,
    /// Prior, den der Elternknoten dieser Aktion zugewiesen hat (für PUCT).
    prior: f32,
    state: GameState,
    terminal: bool,
    /// Netz-Value am Knotenzustand (absolute Win-Prob je Spieler) — Backprop-Blattwert.
    leaf_value: [f64; 2],
}

/// Erzeugt einen Knoten: Netz-Forward → Value (Blattwert) + Child-Priors (untried).
fn make_node(
    net: &Net,
    state: GameState,
    parent: Option<usize>,
    action: Option<Action>,
    prior: f32,
    player_who_acted: usize,
) -> Node {
    let terminal = state.phase != Phase::Drafting;
    let feats = state_to_features(&state_to_json(&state, true));
    let (logits, value, _moon) = net
        .eval(&feats)
        .unwrap_or_else(|_| (vec![0.0; NUM_ACTIONS], 0.0, Vec::new()));

    // Value (Tanh, [-1,1]) → Win-Prob aus Sicht des Spielers am Zug.
    let win = ((value + 1.0) / 2.0) as f64;
    let cp = state.current_player;
    let leaf_value = if cp == 0 { [win, 1.0 - win] } else { [1.0 - win, win] };

    let untried = if terminal {
        Vec::new()
    } else {
        // WICHTIG: Maskierte Softmax NUR über die legalen Aktions-Logits — exakt
        // wie das Training (masked log_softmax). Eine Softmax über alle 482 würde
        // die durch den Policy-Weight-Fix unbeschränkten illegalen (Tiling-)Logits
        // einrechnen, die dann die legalen Priors flach drücken (≈uniform → die
        // Suche wird ungeführt).
        let acts0: Vec<(Action, usize)> = drafting_actions(&state)
            .into_iter()
            .map(|a| {
                let id = action_to_id(&action_to_env_dict(&state, &a));
                (a, id)
            })
            .collect();
        let legal_logits: Vec<f32> = acts0
            .iter()
            .map(|(_, id)| logits.get(*id).copied().unwrap_or(f32::NEG_INFINITY))
            .collect();
        let probs = softmax(&legal_logits);
        let mut acts: Vec<(Action, f32)> =
            acts0.into_iter().zip(probs).map(|((a, _), p)| (a, p)).collect();
        acts.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        acts
    };

    Node {
        parent,
        children: Vec::new(),
        untried,
        action,
        player_who_acted,
        visits: 0,
        value: 0.0,
        prior,
        state,
        terminal,
        leaf_value,
    }
}

/// PUCT: bestes Kind = argmax Q + c·P·√N_parent/(1+N_child). Priors über die
/// Kinder normalisiert (wie agents/mcts.py `_best_child`).
fn best_puct(nodes: &[Node], nid: usize, c_puct: f64) -> usize {
    let sqrt_pv = (nodes[nid].visits.max(1) as f64).sqrt();
    let psum: f64 = nodes[nid]
        .children
        .iter()
        .map(|&c| nodes[c].prior as f64)
        .sum::<f64>()
        .max(1e-8);
    let mut best = nodes[nid].children[0];
    let mut best_score = f64::NEG_INFINITY;
    for &cid in &nodes[nid].children {
        let n = nodes[cid].visits as f64;
        let q = if n > 0.0 { nodes[cid].value / n } else { 0.0 };
        let p = nodes[cid].prior as f64 / psum;
        let score = q + c_puct * p * sqrt_pv / (1.0 + n);
        if score > best_score {
            best_score = score;
            best = cid;
        }
    }
    best
}

/// Baut den PUCT-Suchbaum. `add_root_noise` aktiviert Dirichlet-Wurzel-Noise.
fn build_net_tree<R: Rng + ?Sized>(
    net: &Net,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    rng: &mut R,
) -> Vec<Node> {
    let mut root_state = state.clone();
    root_state.log.clear();
    let root_player = root_state.current_player;
    let mut nodes = vec![make_node(net, root_state, None, None, 0.0, root_player)];

    // Dirichlet-Noise auf die Wurzel-Priors mischen (Self-Play-Exploration).
    if add_root_noise && !nodes[0].untried.is_empty() {
        let noise = dirichlet(nodes[0].untried.len(), DIRICHLET_ALPHA, rng);
        for (i, entry) in nodes[0].untried.iter_mut().enumerate() {
            entry.1 = ((1.0 - DIRICHLET_EPS) * (entry.1 as f64) + DIRICHLET_EPS * noise[i]) as f32;
        }
        nodes[0]
            .untried
            .sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
    }

    for _ in 0..sims {
        // Selection + (eine) Expansion.
        let mut nid = 0;
        loop {
            if nodes[nid].terminal {
                break;
            }
            let allowed = MAX_ACTIONS + (WIDEN_FACTOR * (nodes[nid].visits as f64).sqrt()) as usize;
            if !nodes[nid].untried.is_empty() && nodes[nid].children.len() < allowed {
                let (act, prior) = nodes[nid].untried.remove(0); // höchster Prior zuerst
                let mover = nodes[nid].state.current_player;
                let mut g = Game { state: nodes[nid].state.clone() };
                if g.apply_drafting(&act).is_ok() {
                    let mut child_state = g.state;
                    child_state.log.clear();
                    let child = make_node(net, child_state, Some(nid), Some(act), prior, mover);
                    let cid = nodes.len();
                    nodes.push(child);
                    nodes[nid].children.push(cid);
                    nid = cid;
                }
                break;
            }
            if nodes[nid].children.is_empty() {
                break;
            }
            nid = best_puct(&nodes, nid, c_puct);
        }

        // Backprop (Netz-Blattwert, player_who_acted-Sicht).
        let value = nodes[nid].leaf_value;
        let mut cur = Some(nid);
        while let Some(i) = cur {
            nodes[i].visits += 1;
            nodes[i].value += value[nodes[i].player_who_acted];
            cur = nodes[i].parent;
        }
    }
    nodes
}

/// Beste Drafting-Aktion per Netz-PUCT (meistbesuchtes Wurzelkind). None außerhalb
/// der Drafting-Phase. `add_root_noise` nur im Self-Play aktivieren.
pub fn net_search_drafting_action<R: Rng + ?Sized>(
    net: &Net,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    rng: &mut R,
) -> Option<Action> {
    if state.phase != Phase::Drafting {
        return None;
    }
    let nodes = build_net_tree(net, state, sims, c_puct, add_root_noise, rng);
    let best = nodes[0].children.iter().copied().max_by_key(|&c| nodes[c].visits)?;
    nodes[best].action.clone()
}

/// Wurzelkind-Statistik `(Action, Besuche, Q)` — für Self-Play-Policy-Targets.
pub fn net_root_child_stats<R: Rng + ?Sized>(
    net: &Net,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    rng: &mut R,
) -> Vec<(Action, u32, f64)> {
    if state.phase != Phase::Drafting {
        return Vec::new();
    }
    let nodes = build_net_tree(net, state, sims, c_puct, add_root_noise, rng);
    nodes[0]
        .children
        .iter()
        .filter_map(|&cid| {
            let node = &nodes[cid];
            let q = if node.visits > 0 { node.value / node.visits as f64 } else { 0.0 };
            node.action.clone().map(|a| (a, node.visits, q))
        })
        .collect()
}

// ── Dirichlet/Gamma-Sampling (ohne rand_distr) ──────────────────────────────────

fn std_normal<R: Rng + ?Sized>(rng: &mut R) -> f64 {
    let u1: f64 = rng.random_range(1e-12..1.0);
    let u2: f64 = rng.random_range(0.0..1.0);
    (-2.0 * u1.ln()).sqrt() * (2.0 * std::f64::consts::PI * u2).cos()
}

/// Gamma(alpha, 1) per Marsaglia-Tsang (mit Boost für alpha < 1).
fn gamma<R: Rng + ?Sized>(alpha: f64, rng: &mut R) -> f64 {
    if alpha < 1.0 {
        let u: f64 = rng.random_range(1e-12..1.0);
        return gamma(alpha + 1.0, rng) * u.powf(1.0 / alpha);
    }
    let d = alpha - 1.0 / 3.0;
    let c = 1.0 / (9.0 * d).sqrt();
    loop {
        let x = std_normal(rng);
        let v = (1.0 + c * x).powi(3);
        if v <= 0.0 {
            continue;
        }
        let u: f64 = rng.random_range(0.0..1.0);
        if u < 1.0 - 0.0331 * x.powi(4) || u.ln() < 0.5 * x * x + d * (1.0 - v + v.ln()) {
            return d * v;
        }
    }
}

fn dirichlet<R: Rng + ?Sized>(n: usize, alpha: f64, rng: &mut R) -> Vec<f64> {
    let g: Vec<f64> = (0..n).map(|_| gamma(alpha, rng)).collect();
    let s: f64 = g.iter().sum::<f64>().max(1e-12);
    g.iter().map(|&x| x / s).collect()
}
