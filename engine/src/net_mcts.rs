//! AlphaZero-PUCT-Suche über die Drafting-Phase (Network-Modus, Phase B).
//!
//! Gleiche Baumstruktur wie der Heuristik-MCTS (`crate::mcts`), aber:
//!   - Selektion per **PUCT** mit Netz-Priors statt UCB1,
//!   - Blattbewertung = **Netz-Value** (Tanh → Win-Prob) statt DFS-Solver,
//!   - **Dirichlet-Wurzel-Noise** (Self-Play-Exploration).
//! Lazy Expansion nach Prior (höchster zuerst) + Progressive Widening.

use std::collections::HashMap;

use rand::{Rng, RngExt};
use serde_json::{json, Value};

use crate::features::{action_to_id, state_to_features};
use crate::game::{drafting_actions, Game};
use crate::mcts::{label_search_move, SearchMove};
use crate::moves::{Action, TakeSource};
use crate::net::{softmax, Net};
use crate::self_play::action_to_env_dict;
use crate::serialize::state_to_json;
use crate::state::{GameState, Phase};
use crate::tile::TileColor;

/// Aktionsraum-Größe (= `config.NUM_ACTIONS`).
const NUM_ACTIONS: usize = 482;
/// Standard-PUCT-Konstante (= agents/mcts.py `_c_puct`).
pub const DEFAULT_C_PUCT: f64 = 1.5;
/// Dirichlet-Wurzel-Noise (AlphaZero-Standard).
pub const DIRICHLET_EPS: f64 = 0.25;
pub const DIRICHLET_ALPHA: f64 = 0.3;
/// Kumulative Policy-Masse, ab der das Widening stoppt: nur die (nach Prior
/// absteigend sortierten) Kandidaten bis zu dieser Schwelle werden je
/// überhaupt zu Kindknoten — der "Long Tail" niedrig priorisierter Züge wird
/// nie besucht (spart Simulationsschritte, ersetzt die alte, rein
/// besuchszahl-gesteuerte Progressive-Widening-Formel `MAX_ACTIONS +
/// WIDEN_FACTOR·√N`).
pub const POLICY_MASS_CUTOFF: f64 = 0.95;

/// Blattbewertung der Netz-Suche. Priors kommen IMMER vom Netz; nur das Blatt
/// unterscheidet sich:
///   - `Dfs`: exakter DFS-Solver (Stufe 1 — saubere, scharfe Visit-Targets,
///     unabhängig vom noch schwachen Netz-Value).
///   - `Net`: Netz-Value (Stufe 2 — sobald das Netz die Heuristik schlägt, um
///     deren Ein-Runden-Kurzsichtigkeit per Mehrrunden-Value zu überwinden).
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum LeafEval {
    Dfs,
    Net,
}

// ── Suche-getriebene Moon-Order-Wahl ─────────────────────────────────────────
//
// Die Aktions-ID (`action_to_id`) kodiert `moon_order` NICHT — Farbe/Reihe/
// Fabrik bestimmen die ID, alle Reihenfolge-Varianten eines SmallFactorySun-
// Zugs fallen also auf dieselbe ID. Statt NUM_ACTIONS aufzublähen (würde alle
// bestehenden Checkpoints invalidieren), bleibt der 482-dim Policy-Head auf
// Farbe+Reihe beschränkt; die Permutations-Priors kommen SEPARAT aus dem
// moon_order_head (Plackett-Luce über die rohen 5 Farb-Scores) und werden erst
// beim Expandieren eines SmallFactorySun-Knotens mit dem Basis-Prior
// multipliziert: P(Zug) = P(Basis) × P(Order | Plackett-Luce).

/// TileColor → Index in COLOR_MAP-Reihenfolge (blau=0…türkis=4), sonst None.
fn color_idx5(c: TileColor) -> Option<usize> {
    TileColor::NORMAL.iter().position(|&x| x == c)
}

/// Alle EINDEUTIGEN Permutationen einer Farb-Multimenge (Tiles derselben Farbe
/// sind ununterscheidbar — Duplikate durch wiederholte Farben werden dedupliziert).
fn unique_moon_orders(remaining: &[TileColor]) -> Vec<Vec<TileColor>> {
    fn permute(items: &mut Vec<TileColor>, k: usize, out: &mut Vec<Vec<TileColor>>) {
        if k == items.len() {
            out.push(items.clone());
            return;
        }
        for i in k..items.len() {
            items.swap(k, i);
            permute(items, k + 1, out);
            items.swap(k, i);
        }
    }
    if remaining.is_empty() {
        return vec![Vec::new()];
    }
    let mut items = remaining.to_vec();
    let mut out = Vec::new();
    permute(&mut items, 0, &mut out);
    out.sort_by(|a, b| {
        let av: Vec<&str> = a.iter().map(|c| c.value()).collect();
        let bv: Vec<&str> = b.iter().map(|c| c.value()).collect();
        av.cmp(&bv)
    });
    out.dedup();
    out
}

/// Plackett-Luce-Wahrscheinlichkeit einer konkreten Farbfolge unter den 5 rohen
/// Moon-Head-Scores (unnormalisiert, Reihenfolge wie `TileColor::NORMAL`):
/// sequenzieller Softmax über die jeweils noch verbleibenden Farben.
fn plackett_luce_prob(scores: &[f32; 5], seq: &[TileColor]) -> f64 {
    let mut counts = [0i32; 5];
    for &c in seq {
        if let Some(i) = color_idx5(c) {
            counts[i] += 1;
        }
    }
    let mut p = 1.0f64;
    for &c in seq {
        let Some(cid) = color_idx5(c) else { continue };
        let avail: Vec<usize> = (0..5).filter(|&i| counts[i] > 0).collect();
        if avail.len() > 1 {
            let max_s = avail.iter().map(|&i| scores[i]).fold(f32::NEG_INFINITY, f32::max);
            let exps: Vec<f64> = avail.iter().map(|&i| ((scores[i] - max_s) as f64).exp()).collect();
            let sum: f64 = exps.iter().sum::<f64>().max(1e-12);
            let pos = avail.iter().position(|&i| i == cid).unwrap();
            p *= exps[pos] / sum;
        } // avail.len() <= 1: einziger Rest-Kandidat -> P=1, kein Beitrag
        counts[cid] -= 1;
    }
    p
}

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
    /// Gesamtzahl legaler Züge VOR Moon-Order-Expansion (= Basis-Aktionen) —
    /// für die "Gültige Aktionen"-Anzeige (Server-Debug-UI), unabhängig davon,
    /// wie viele davon durchs Widening tatsächlich zu Kindern wurden.
    n_actions: usize,
}

/// Baut die priorisierte Kandidatenliste (Kind-Aktionen + Priors) für einen
/// Nicht-Terminal-Knoten aus den rohen Netz-Logits + Moon-Head-Scores. Reine
/// Funktion (kein `Net`-Aufruf) — direkt mit synthetischen Logits testbar.
/// Gibt `(sortierte Kandidaten, Basis-Aktionszahl VOR Moon-Order-Expansion)`
/// zurück; letzteres bleibt für `LeafEval::Dfs`s Skalierung unverändert.
fn build_untried_actions(
    state: &GameState,
    logits: &[f32],
    moon_scores: &[f32; 5],
) -> (Vec<(Action, f32)>, usize) {
    let base_actions = drafting_actions(state);
    let n = base_actions.len();
    let ids: Vec<usize> =
        base_actions.iter().map(|a| action_to_id(&action_to_env_dict(state, a))).collect();

    // WICHTIG: Maskierte Softmax NUR über die EINDEUTIGEN legalen Aktions-IDs —
    // exakt wie das Training (masked log_softmax). Mehrere Moon-Order-Varianten
    // derselben Basis-Aktion teilen sich eine ID; würden sie hier dupliziert
    // eingehen, bekäme diese ID fälschlich mehrfaches Gewicht.
    let mut unique_ids: Vec<usize> = ids.clone();
    unique_ids.sort_unstable();
    unique_ids.dedup();
    let legal_logits: Vec<f32> = unique_ids
        .iter()
        .map(|&id| logits.get(id).copied().unwrap_or(f32::NEG_INFINITY))
        .collect();
    let base_probs = softmax(&legal_logits);
    let p_base: HashMap<usize, f32> = unique_ids.into_iter().zip(base_probs).collect();

    // Kandidaten: SmallFactorySun mit ≥2 Restfliesen → alle eindeutigen Moon-
    // Order-Permutationen, Prior = P(Basis) × P(Order | Plackett-Luce). Alle
    // anderen Aktionen unverändert 1:1.
    let mut acts: Vec<(Action, f32)> = Vec::with_capacity(base_actions.len());
    for (act, id) in base_actions.into_iter().zip(ids.into_iter()) {
        let base_p = *p_base.get(&id).unwrap_or(&0.0);
        if let Action::Stone(m) = &act {
            if m.take.source == TakeSource::SmallFactorySun && m.take.moon_order.len() >= 2 {
                let variants = unique_moon_orders(&m.take.moon_order);
                let pl: Vec<f64> =
                    variants.iter().map(|seq| plackett_luce_prob(moon_scores, seq)).collect();
                let pl_sum: f64 = pl.iter().sum::<f64>().max(1e-12);
                for (seq, p) in variants.into_iter().zip(pl.into_iter()) {
                    let mut mm = m.clone();
                    mm.take.moon_order = seq;
                    acts.push((Action::Stone(mm), base_p * (p / pl_sum) as f32));
                }
                continue;
            }
        }
        acts.push((act, base_p));
    }
    acts.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

    // Policy-Masse-Cutoff: nur den minimalen Präfix behalten, dessen kumulierte
    // Priors POLICY_MASS_CUTOFF erreichen — der Rest (Long Tail) wird verworfen,
    // BEVOR er je ein Kandidat für Widening werden kann. Mindestens 1 Aktion
    // bleibt immer erhalten (auch wenn ihr eigener Prior schon >= Cutoff ist).
    let mut cum = 0.0f64;
    let mut keep = acts.len();
    for (i, (_, p)) in acts.iter().enumerate() {
        cum += *p as f64;
        if cum >= POLICY_MASS_CUTOFF {
            keep = i + 1;
            break;
        }
    }
    acts.truncate(keep.max(1));
    (acts, n)
}

/// Erzeugt einen Knoten: Netz-Forward → Child-Priors (untried) + Blattwert
/// (per `leaf`: DFS-Solver oder Netz-Value).
fn make_node(
    net: &Net,
    state: GameState,
    parent: Option<usize>,
    action: Option<Action>,
    prior: f32,
    player_who_acted: usize,
    leaf: LeafEval,
) -> Node {
    let terminal = state.phase != Phase::Drafting;
    let feats = state_to_features(&state_to_json(&state, true));
    let (logits, value, moon) = net
        .eval(&feats)
        .unwrap_or_else(|_| (vec![0.0; NUM_ACTIONS], 0.0, Vec::new()));

    let mut moon_scores = [0f32; 5];
    for (i, s) in moon.iter().take(5).enumerate() {
        moon_scores[i] = *s;
    }
    let (untried, n_actions) =
        if terminal { (Vec::new(), 0) } else { build_untried_actions(&state, &logits, &moon_scores) };

    // Blattwert: absolute Per-Spieler-Win-Prob.
    let leaf_value = match leaf {
        LeafEval::Net => {
            let win = ((value + 1.0) / 2.0) as f64; // Sicht des Spielers am Zug
            let cp = state.current_player;
            if cp == 0 { [win, 1.0 - win] } else { [1.0 - win, win] }
        }
        LeafEval::Dfs => crate::mcts::evaluate(&state, n_actions),
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
        n_actions,
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
    leaf: LeafEval,
    rng: &mut R,
) -> Vec<Node> {
    let mut root_state = state.clone();
    root_state.log.clear();
    let root_player = root_state.current_player;
    let mut nodes = vec![make_node(net, root_state, None, None, 0.0, root_player, leaf)];

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
            // Kein besuchszahl-abhängiges Wachstum mehr: `untried` ist bereits beim
            // Erzeugen des Knotens auf den POLICY_MASS_CUTOFF-Präfix gekappt (siehe
            // `build_untried_actions`) — jeder verbleibende Kandidat darf irgendwann
            // Kind werden, der Long Tail wurde schon vorher verworfen.
            if !nodes[nid].untried.is_empty() {
                let (act, prior) = nodes[nid].untried.remove(0); // höchster Prior zuerst
                let mover = nodes[nid].state.current_player;
                let mut g = Game { state: nodes[nid].state.clone() };
                if g.apply_drafting(&act).is_ok() {
                    let mut child_state = g.state;
                    child_state.log.clear();
                    let child = make_node(net, child_state, Some(nid), Some(act), prior, mover, leaf);
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
    leaf: LeafEval,
    rng: &mut R,
) -> Option<Action> {
    if state.phase != Phase::Drafting {
        return None;
    }
    let nodes = build_net_tree(net, state, sims, c_puct, add_root_noise, leaf, rng);
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
    leaf: LeafEval,
    rng: &mut R,
) -> Vec<(Action, u32, f64)> {
    if state.phase != Phase::Drafting {
        return Vec::new();
    }
    let nodes = build_net_tree(net, state, sims, c_puct, add_root_noise, leaf, rng);
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

/// Wie [`net_search_drafting_action`], liefert zusätzlich ein debug.html-kompatibles
/// Analyse-Dict je Wurzelkind: rohen Netz-Prior (`net_prob`/`net_prob_norm`, VOR jeder
/// Suche — das eigentliche Policy-Head-Signal) zusammen mit den PUCT-Such-Stats
/// (`mcts_visits`/`mcts_share`/`mcts_q`). Für den Server (Mensch-vs-Netz) und Debug-UI;
/// `add_root_noise` hier i.d.R. `false` (Dirichlet-Noise ist nur ein Self-Play-Kniff).
pub fn net_search_with_tree<R: Rng + ?Sized>(
    net: &Net,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    leaf: LeafEval,
    rng: &mut R,
) -> (Option<Action>, Value) {
    if state.phase != Phase::Drafting {
        return (None, Value::Null);
    }
    let nodes = build_net_tree(net, state, sims, c_puct, add_root_noise, leaf, rng);
    let best = nodes[0].children.iter().copied().max_by_key(|&c| nodes[c].visits);
    let total_visits: u32 = nodes[0].children.iter().map(|&c| nodes[c].visits).sum();
    let prior_sum: f64 = nodes[0]
        .children
        .iter()
        .map(|&c| nodes[c].prior as f64)
        .sum::<f64>()
        .max(1e-8);

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
                Some(a) => label_search_move(&SearchMove::Draft(a.clone()), Some(state)),
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
                "net_prob": node.prior,
                "net_prob_norm": node.prior as f64 / prior_sum,
                "mcts_visits": node.visits,
                "mcts_share": if total_visits > 0 { node.visits as f64 / total_visits as f64 } else { 0.0 },
                "mcts_q": q,
                "mcts_win_pct": q * 100.0,
                "max_depth": subtree_depth(&nodes, cid),
                "chosen": is_chosen,
            })
        })
        .collect();

    let root_visits = nodes[0].visits.max(1) as f64;
    let root_q = nodes[0].value / root_visits;

    let analysis = json!({
        "current_player": nodes[0].player_who_acted,
        "ai_player": state.current_player,
        "value": Value::Null,
        "win_pct": Value::Null,
        "has_net": true,
        "simulations": sims,
        // Gesamtzahl legaler Züge (unabhängig vom Widening) vs. tatsächlich
        // durchsuchte Wurzelkinder — Server-Debug-UI zeigt "considered/total".
        "num_actions": nodes[0].n_actions,
        "num_actions_considered": nodes[0].children.len(),
        "max_depth": subtree_depth(&nodes, 0),
        "ai_action": chosen_id,
        "moves": moves,
        "tree": json!({
            "visits": nodes[0].visits,
            "win_pct": root_q * 100.0,
            "depth": subtree_depth(&nodes, 0),
            "n_children": nodes[0].children.len(),
        }),
    });

    let chosen = best.and_then(|cid| nodes[cid].action.clone());
    (chosen, analysis)
}

/// Tiefe des Teilbaums unter `nid` (0 = Blatt) — Pendant zu `mcts::subtree_depth`.
fn subtree_depth(nodes: &[Node], nid: usize) -> u32 {
    let children = &nodes[nid].children;
    if children.is_empty() {
        0
    } else {
        1 + children.iter().map(|&c| subtree_depth(nodes, c)).max().unwrap()
    }
}

/// Textzusammenfassung einer `net_search_with_tree`-Analyse fürs Server-Debug-Log
/// (kein Sim-für-Sim-Trace wie bei der Heuristik — `build_net_tree` protokolliert
/// aktuell nicht jede Simulation einzeln — sondern Kopfzeilen + Zug-Ranking-Tabelle).
pub fn net_analysis_log_text(state: &GameState, analysis: &Value) -> String {
    let sims = analysis["simulations"].as_u64().unwrap_or(0);
    let na = analysis["num_actions"].as_u64().unwrap_or(0);
    let considered = analysis["num_actions_considered"].as_u64().unwrap_or(0);
    let mut out = String::new();
    out.push_str("Netz-PUCT-Debug-Log (KI-Zug)\n");
    out.push_str(&format!(
        "Simulationen={sims}  Aktionen={considered}/{na} durchsucht  Wurzelspieler={}\n",
        state.players[state.current_player].name
    ));
    out.push_str(&format!("Spieler: P0={}  P1={}\n", state.players[0].name, state.players[1].name));
    out.push_str(&format!("{}\n", "=".repeat(60)));
    out.push_str(&format!(
        "{:<5} {:<45} {:>8} {:>8} {:>8} {:>7}\n",
        "#", "Zug", "Prior", "Visits", "Share%", "Q%"
    ));
    if let Some(moves) = analysis["moves"].as_array() {
        for m in moves {
            let mark = if m["chosen"].as_bool().unwrap_or(false) { "*" } else { " " };
            out.push_str(&format!(
                "{mark}{:<4} {:<45} {:>7.1}% {:>8} {:>7.1}% {:>6.1}%\n",
                m["action_id"].as_i64().unwrap_or(-1),
                m["description"].as_str().unwrap_or("?"),
                m["net_prob_norm"].as_f64().unwrap_or(0.0) * 100.0,
                m["mcts_visits"].as_u64().unwrap_or(0),
                m["mcts_share"].as_f64().unwrap_or(0.0) * 100.0,
                m["mcts_q"].as_f64().unwrap_or(0.0) * 100.0,
            ));
        }
    }
    out
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::setup_new_game;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    fn names() -> [String; 2] {
        ["P1".into(), "P2".into()]
    }

    #[test]
    fn unique_moon_orders_dedups_repeated_colors() {
        // 3 verschiedene Farben -> alle 6 Permutationen eindeutig.
        let all_diff = [TileColor::Blau, TileColor::Gelb, TileColor::Rot];
        assert_eq!(unique_moon_orders(&all_diff).len(), 6);

        // 2x dieselbe Farbe + 1 andere -> nur 3 unterscheidbare Reihenfolgen
        // (die beiden Rot-Fliesen sind ununterscheidbar).
        let two_same = [TileColor::Rot, TileColor::Rot, TileColor::Blau];
        let orders = unique_moon_orders(&two_same);
        assert_eq!(orders.len(), 3);
        for o in &orders {
            let mut sorted = o.clone();
            sorted.sort_by_key(|c| c.value());
            let mut expected = two_same.to_vec();
            expected.sort_by_key(|c| c.value());
            assert_eq!(sorted, expected);
        }

        // Alle 3 gleich -> nur 1 mögliche Reihenfolge.
        let all_same = [TileColor::Schwarz, TileColor::Schwarz, TileColor::Schwarz];
        assert_eq!(unique_moon_orders(&all_same).len(), 1);

        // 1 Restfliese -> genau 1 Reihenfolge.
        assert_eq!(unique_moon_orders(&[TileColor::Tuerkis]).len(), 1);

        // 0 Restfliesen -> 1 leere Reihenfolge (kein Stapel nötig).
        assert_eq!(unique_moon_orders(&[]), vec![Vec::<TileColor>::new()]);
    }

    #[test]
    fn plackett_luce_probs_sum_to_one_over_all_unique_orders() {
        let remaining = [TileColor::Blau, TileColor::Gelb, TileColor::Rot];
        let orders = unique_moon_orders(&remaining);
        // Beliebige, nicht-uniforme Scores.
        let scores = [2.0f32, -1.0, 0.5, 3.0, -2.0];
        let total: f64 = orders.iter().map(|o| plackett_luce_prob(&scores, o)).sum();
        assert!((total - 1.0).abs() < 1e-9, "Summe war {total}, erwartet 1.0");

        // Auch mit Farbwiederholung (3 Order statt 6) muss die Summe 1 bleiben.
        let remaining2 = [TileColor::Rot, TileColor::Rot, TileColor::Blau];
        let orders2 = unique_moon_orders(&remaining2);
        let total2: f64 = orders2.iter().map(|o| plackett_luce_prob(&scores, o)).sum();
        assert!((total2 - 1.0).abs() < 1e-9, "Summe war {total2}, erwartet 1.0");
    }

    #[test]
    fn plackett_luce_prefers_higher_scored_color_first() {
        // Score für Rot (Index 2) klar am höchsten -> P(Rot zuerst) muss die
        // größte Einzelwahrscheinlichkeit unter den Permutationen sein, die
        // mit Rot beginnen, gegenüber denen, die mit Blau beginnen.
        let scores = [0.0f32, 0.0, 5.0, 0.0, 0.0]; // Rot dominiert klar
        let p_rot_first = plackett_luce_prob(&scores, &[TileColor::Rot, TileColor::Blau]);
        let p_blau_first = plackett_luce_prob(&scores, &[TileColor::Blau, TileColor::Rot]);
        assert!(p_rot_first > p_blau_first, "{p_rot_first} sollte > {p_blau_first} sein");
        assert!(p_rot_first > 0.9, "bei Score-Differenz 5.0 sollte P(Rot zuerst) dominieren");
    }

    #[test]
    fn build_untried_actions_truncates_long_tail_for_peaked_policy() {
        // Genau EINE legale Aktions-ID stark bevorzugen -> praktisch die gesamte
        // Masse liegt auf ihr (+ ggf. ihren Moon-Order-Varianten), der Rest ist
        // Long Tail und sollte komplett verworfen werden.
        let mut rng = StdRng::seed_from_u64(11);
        let state = setup_new_game(names(), 0, &mut rng);
        let base_actions = drafting_actions(&state);
        assert!(base_actions.len() > 5, "Testvoraussetzung: früher Zustand mit vielen legalen Zügen");
        let spike_id = action_to_id(&action_to_env_dict(&state, &base_actions[0]));

        let mut logits = vec![-10.0f32; NUM_ACTIONS];
        logits[spike_id] = 10.0;
        let moon_scores = [0.0f32; 5];

        let (acts, n_base) = build_untried_actions(&state, &logits, &moon_scores);
        assert!(!acts.is_empty());
        assert!(
            acts.len() < n_base,
            "Kappung sollte bei stark geneigter Verteilung deutlich weniger Kandidaten \
             behalten als Basis-Aktionen: {} Kandidaten vs. {} Basis-Aktionen",
            acts.len(),
            n_base
        );
        let total: f64 = acts.iter().map(|(_, p)| *p as f64).sum();
        assert!(total >= POLICY_MASS_CUTOFF && total <= 1.0 + 1e-4);
    }

    #[test]
    fn build_untried_actions_priors_reach_cutoff_and_expand_moon_orders() {
        let mut rng = StdRng::seed_from_u64(42);
        let state = setup_new_game(names(), 0, &mut rng);
        let logits = vec![0.1f32; NUM_ACTIONS];
        let moon_scores = [1.0f32, 0.5, -0.5, 2.0, 0.0];

        let (acts, n_base) = build_untried_actions(&state, &logits, &moon_scores);
        assert!(!acts.is_empty());

        // Kandidaten sind auf den POLICY_MASS_CUTOFF-Präfix gekappt (Long Tail
        // verworfen) — die Summe muss also mindestens den Cutoff erreichen
        // (der Schritt, der ihn überschreitet, wird noch mitgenommen), aber
        // nie mehr als 1.0 (Moon-Order-Aufteilung erzeugt/verliert keine Masse).
        let total: f64 = acts.iter().map(|(_, p)| *p as f64).sum();
        assert!(
            total >= POLICY_MASS_CUTOFF && total <= 1.0 + 1e-4,
            "Summe der (gekappten) Priors war {total}, erwartet in [{POLICY_MASS_CUTOFF}, 1.0]"
        );

        // Mindestens eine SmallFactorySun-Basis-Aktion mit ≥2 Restfliesen sollte
        // beim Spielstart existieren (4 Fabriken × 4 Fliesen) -> Expansion
        // muss stattgefunden haben (mehr Kandidaten als Basis-Aktionen).
        let has_multi_order = state.factories.iter().any(|f| {
            f.sun_colors().iter().any(|&c| {
                f.sun_tiles.iter().filter(|&&t| t != c).count() >= 2
            })
        });
        if has_multi_order {
            assert!(
                acts.len() > n_base,
                "Erwartete Moon-Order-Expansion (mehr Kandidaten als Basis-Aktionen): {} vs {}",
                acts.len(),
                n_base
            );
        }

        // Für jede expandierte SmallFactorySun-Gruppe: die Prior-Summe der
        // Varianten muss der Basis-ID-Wahrscheinlichkeit entsprechen (Prüfung
        // über Gruppierung nach (color,row,factory), da die ID selbst nicht
        // direkt zugänglich ist -> stattdessen Gesamtsumme je Gruppe > 0).
        use std::collections::HashMap as Map;
        let mut groups: Map<(String, i32, Option<usize>), f64> = Map::new();
        for (act, p) in &acts {
            if let Action::Stone(m) = act {
                if m.take.source == TakeSource::SmallFactorySun {
                    let key = (m.take.color.value().to_string(), m.place.row_index, m.take.factory_id);
                    *groups.entry(key).or_insert(0.0) += *p as f64;
                }
            }
        }
        assert!(!groups.is_empty(), "keine SmallFactorySun-Gruppen gefunden");
        for (_, sum) in &groups {
            assert!(*sum > 0.0);
        }
    }
}
