//! AlphaZero-PUCT-Suche über die Drafting-Phase (Network-Modus, Phase B).
//!
//! Gleiche Baumstruktur wie der Heuristik-MCTS (`crate::mcts`), aber:
//!   - Selektion per **PUCT** mit Netz-Priors statt UCB1,
//!   - Blattbewertung = `ACTIVE_LEAF` (siehe unten) -- aktuell Stufe 2
//!     (Netz-Value, mit dem neuen ±1-Sieg/Niederlage-Ziel statt der alten
//!     verrauschten Punktestand-Regression), Stufe 1 (DFS-Solver) bleibt als
//!     abschaltbarer Pfad im Code, wird aber nicht mehr aktiv genutzt (siehe
//!     evaluations/stage2_investigation.md fuer die Historie: die
//!     Disagreement-Studie widerlegte Stufe 2 mit dem ALTEN Value-Ziel,
//!     Stufe 1 ist mit dem exakten DFS-Solver aber strukturell auf
//!     Ein-Runden-Sicht begrenzt -- "spielt man gegen Stufe 1, spielt man
//!     letztlich gegen die Heuristik". Stufe 2 mit einem sauber trainierten
//!     Value-Head ist der einzige Weg zu echter Mehrrunden-Strategie).
//!   - **Dirichlet-Wurzel-Noise** (Self-Play-Exploration).
//! Lazy Expansion nach Prior (höchster zuerst) + Progressive Widening.

use std::collections::HashMap;

use rand::{Rng, RngExt};
use serde_json::{json, Value};

use crate::features::{action_to_id, state_to_features_direct};
use crate::game::{drafting_actions, Game};
use crate::mcts::{label_search_move, SearchMove};
use crate::moves::{Action, TakeSource};
use crate::net::{softmax, Net};
use crate::self_play::action_to_env_dict;
use crate::state::{GameState, Phase};
use crate::tile::TileColor;

/// Aktionsraum-Größe (= `config.NUM_ACTIONS`).
pub(crate) const NUM_ACTIONS: usize = 483;
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
///     aber strukturell auf Ein-Runden-Sicht begrenzt).
///   - `Net`: Netz-Value (Stufe 2 — Mehrrunden-Value-Ziel, jetzt ±1
///     Sieg/Niederlage statt der alten Punktestand-Regression).
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum LeafEval {
    Dfs,
    Net,
}

/// Aktiv genutzte Blattbewertung fuer Self-Play/Arena/Stufe 3 (siehe
/// Modul-Kommentar oben). Stufe 1 (`Dfs`) bleibt als Pfad im Code, wird aber
/// bewusst nicht mehr default-mäßig verwendet -- eine Zeile hier zurück auf
/// `Dfs` reaktiviert sie bei Bedarf wieder, ohne Funktionssignaturen
/// anzufassen.
pub const ACTIVE_LEAF: LeafEval = LeafEval::Net;

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
    /// DFS-Solver-Blattwert am Knotenzustand (je Spieler) — Backprop-Blattwert.
    leaf_value: [f64; 2],
    /// Gesamtzahl legaler Züge VOR Moon-Order-Expansion (= Basis-Aktionen) —
    /// für die "Gültige Aktionen"-Anzeige (Server-Debug-UI), unabhängig davon,
    /// wie viele davon durchs Widening tatsächlich zu Kindern wurden.
    n_actions: usize,
}

impl crate::search_common::SearchNode for Node {
    fn parent(&self) -> Option<usize> { self.parent }
    fn children(&self) -> &[usize] { &self.children }
    fn terminal(&self) -> bool { self.terminal }
}

/// Baut die priorisierte Kandidatenliste (Kind-Aktionen + Priors) für einen
/// Nicht-Terminal-Knoten aus den rohen Netz-Logits + Moon-Head-Scores. Reine
/// Funktion (kein `Net`-Aufruf) — direkt mit synthetischen Logits testbar.
/// Gibt `(sortierte Kandidaten, Basis-Aktionszahl VOR Moon-Order-Expansion)`
/// zurück; letzteres bleibt für den DFS-Solver-Blattwert unverändert.
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

/// Netz-Value (Tanh, ±1) → Win-Prob [0,1] fuer die perspektivische Blattwert-
/// Skala von `leaf_value` (muss zu `crate::mcts::evaluate`s [0,1]-Skala passen,
/// damit PUCTs Q-Mittelung konsistent bleibt).
fn value_to_win_prob(value: &[f32]) -> f64 {
    let v = value.first().copied().unwrap_or(0.0) as f64;
    (v + 1.0) / 2.0
}

/// Erzeugt einen Knoten: Netz-Forward → Child-Priors (untried) + Blattwert
/// (per `ACTIVE_LEAF`: DFS-Solver oder Netz-Value).
fn make_node(
    net: &Net,
    state: GameState,
    parent: Option<usize>,
    action: Option<Action>,
    prior: f32,
    player_who_acted: usize,
) -> Node {
    let terminal = state.phase != Phase::Drafting;
    let feats =
        crate::profiling::timed(crate::profiling::note_features_ns, || state_to_features_direct(&state));
    // `points` ist reines Trainings-Zusatzsignal (siehe net.rs), hier nie
    // gebraucht. `value` wird nur bei ACTIVE_LEAF=Net gelesen.
    let (logits, value, moon, _points) = crate::profiling::timed(crate::profiling::note_net_eval_ns, || {
        net.eval(&feats).unwrap_or_else(|_| (vec![0.0; NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new()))
    });

    let mut moon_scores = [0f32; 5];
    for (i, s) in moon.iter().take(5).enumerate() {
        moon_scores[i] = *s;
    }
    let (untried, n_actions) =
        if terminal { (Vec::new(), 0) } else { build_untried_actions(&state, &logits, &moon_scores) };

    // Blattwert: unabhängige Pro-Spieler-Werte. Das Netz liefert einen
    // EGO-perspektivischen Wert (die Input-Features hängen von
    // `state.current_player` ab, siehe features.rs/state_to_tensor) — für
    // den jeweils ANDEREN Spieler braucht es deshalb einen zweiten
    // Forward-Pass mit geflipptem `current_player`, nicht einfach `1-wert`.
    let leaf_value = match ACTIVE_LEAF {
        LeafEval::Net => {
            let mover_val = value_to_win_prob(&value);
            crate::profiling::note_gamestate_clone();
            let mut flipped = state.clone();
            flipped.current_player = 1 - state.current_player;
            let other_feats = state_to_features_direct(&flipped);
            let other_val = net
                .eval(&other_feats)
                .map(|(_, v, _, _)| value_to_win_prob(&v))
                .unwrap_or(0.5);
            if state.current_player == 0 { [mover_val, other_val] } else { [other_val, mover_val] }
        }
        LeafEval::Dfs => crate::profiling::timed(crate::profiling::note_dfs_eval_ns, || {
            crate::mcts::evaluate(&state, n_actions)
        }),
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

/// Kurzlabel eines Knotens fürs Log (Aktionsbeschreibung bzw. „Wurzel"). Mit
/// Eltern-Zustand (VOR dem Zug) für Steinanzahl/Füllstand/Strafleisten-Hinweis.
fn log_label(nodes: &[Node], nid: usize) -> String {
    match &nodes[nid].action {
        None => "Wurzel".to_string(),
        Some(a) => {
            let parent_state = nodes[nid].parent.map(|p| &nodes[p].state);
            label_search_move(&SearchMove::Draft(a.clone()), parent_state).1
        }
    }
}

/// Expandiert das höchstpriorisierte unversuchte Kind von `nid` (falls
/// vorhanden) und backpropagiert dessen Blattwert bis zur Wurzel — exakt der
/// EXPAND/EVAL/BACKPROP-Schritt einer normalen Simulation, nur außerhalb der
/// Sim-Zählschleife aufrufbar. Für die Nachlauf-Schließung offener Enden
/// (siehe unten): kein Effekt, falls `nid` bereits terminal ist oder keine
/// unversuchten Aktionen mehr hat.
fn expand_and_backprop(
    nodes: &mut Vec<Node>,
    net: &Net,
    nid: usize,
    names: &[&str; 2],
    log: &mut Option<&mut Vec<String>>,
) {
    if nodes[nid].untried.is_empty() {
        return;
    }
    let (act, prior) = nodes[nid].untried.remove(0);
    let mover = nodes[nid].state.current_player;
    crate::profiling::note_gamestate_clone();
    let mut g = Game { state: nodes[nid].state.clone() };
    if g.apply_drafting(&act).is_err() {
        return;
    }
    let mut child_state = g.state;
    child_state.log.clear();
    let terminal = child_state.phase != Phase::Drafting;
    let child = make_node(net, child_state, Some(nid), Some(act.clone()), prior, mover);
    let cid = nodes.len();
    nodes.push(child);
    nodes[nid].children.push(cid);
    if let Some(l) = log.as_deref_mut() {
        l.push(format!(
            "  EXPAND #{nid} +[{}] → #{cid} (Zug: {}, prior={:.1}%{})",
            label_search_move(&SearchMove::Draft(act), Some(&nodes[nid].state)).1,
            names[mover],
            prior * 100.0,
            if terminal { ", terminal" } else { "" }
        ));
    }

    let value = nodes[cid].leaf_value;
    if let Some(l) = log.as_deref_mut() {
        l.push(format!(
            "  EVAL   #{cid} ({}) win[{}]={:.3} win[{}]={:.3}",
            if ACTIVE_LEAF == LeafEval::Net { "Netz-Value" } else { "DFS-Solver" },
            names[0], value[0], names[1], value[1]
        ));
    }

    let mut bp = String::from("  BACKPROP");
    let mut cur = Some(cid);
    while let Some(i) = cur {
        nodes[i].visits += 1;
        let delta = value[nodes[i].player_who_acted];
        nodes[i].value += delta;
        if log.is_some() {
            bp.push_str(&format!(" #{i}+={delta:.3}({})", names[nodes[i].player_who_acted]));
        }
        cur = nodes[i].parent;
    }
    if let Some(l) = log.as_deref_mut() {
        l.push(bp);
    }
}

/// Baut den PUCT-Suchbaum. `add_root_noise` aktiviert Dirichlet-Wurzel-Noise.
/// Mit `log = Some(..)` wird jede Simulation (Selection/Expansion/Eval/Backprop)
/// als Text protokolliert (für den Server-Debug-Log, analog `mcts::build_tree`).
fn build_net_tree<R: Rng + ?Sized>(
    net: &Net,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    rng: &mut R,
    mut log: Option<&mut Vec<String>>,
) -> Vec<Node> {
    let names = [state.players[0].name.as_str(), state.players[1].name.as_str()];
    let mut root_state = state.clone();
    root_state.log.clear();
    let root_player = root_state.current_player;
    let mut nodes = vec![make_node(net, root_state, None, None, 0.0, root_player)];

    macro_rules! logln {
        ($($arg:tt)*) => { if let Some(l) = log.as_deref_mut() { l.push(format!($($arg)*)); } };
    }

    // Dirichlet-Noise auf die Wurzel-Priors mischen (Self-Play-Exploration).
    if add_root_noise && !nodes[0].untried.is_empty() {
        let noise = dirichlet(nodes[0].untried.len(), DIRICHLET_ALPHA, rng);
        for (i, entry) in nodes[0].untried.iter_mut().enumerate() {
            entry.1 = ((1.0 - DIRICHLET_EPS) * (entry.1 as f64) + DIRICHLET_EPS * noise[i]) as f32;
        }
        nodes[0]
            .untried
            .sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        logln!("  ROOT-NOISE gemischt (Dirichlet alpha={DIRICHLET_ALPHA}, eps={DIRICHLET_EPS})");
    }

    for sim in 0..sims {
        logln!("=== Sim {}/{} ===", sim + 1, sims);

        // Selection + (eine) Expansion.
        let mut nid = 0;
        loop {
            // Erzwungener Gegnerzug (Tiefe 0/1, siehe search_common::force_reply_target):
            // ein Knoten breitert erst weiter, wenn sein zuletzt erzeugtes Kind
            // selbst mindestens einen eigenen Kindknoten hat (= Antwort simuliert).
            if let Some(target) = crate::search_common::force_reply_target(&nodes, nid) {
                logln!("  FORCE-REPLY #{nid} → #{target}: Antwort erzwungen vor weiterem Breitern");
                nid = target;
                continue;
            }
            if nodes[nid].terminal {
                logln!("  SELECT #{nid} [{}] terminal", log_label(&nodes, nid));
                break;
            }
            // Kein besuchszahl-abhängiges Wachstum mehr: `untried` ist bereits beim
            // Erzeugen des Knotens auf den POLICY_MASS_CUTOFF-Präfix gekappt (siehe
            // `build_untried_actions`) — jeder verbleibende Kandidat darf irgendwann
            // Kind werden, der Long Tail wurde schon vorher verworfen.
            if !nodes[nid].untried.is_empty() {
                let (act, prior) = nodes[nid].untried.remove(0); // höchster Prior zuerst
                let mover = nodes[nid].state.current_player;
                crate::profiling::note_gamestate_clone();
                let mut g = Game { state: nodes[nid].state.clone() };
                if g.apply_drafting(&act).is_ok() {
                    let mut child_state = g.state;
                    child_state.log.clear();
                    let terminal = child_state.phase != Phase::Drafting;
                    let child = make_node(net, child_state, Some(nid), Some(act.clone()), prior, mover);
                    let cid = nodes.len();
                    nodes.push(child);
                    nodes[nid].children.push(cid);
                    logln!(
                        "  EXPAND #{nid} +[{}] → #{cid} (Zug: {}, prior={:.1}%{})",
                        label_search_move(&SearchMove::Draft(act), Some(&nodes[nid].state)).1,
                        names[mover],
                        prior * 100.0,
                        if terminal { ", terminal" } else { "" }
                    );
                    nid = cid;
                }
                break;
            }
            if nodes[nid].children.is_empty() {
                break;
            }
            let cid = best_puct(&nodes, nid, c_puct);
            if log.is_some() {
                let sqrt_pv = (nodes[nid].visits.max(1) as f64).sqrt();
                let psum: f64 = nodes[nid]
                    .children
                    .iter()
                    .map(|&c| nodes[c].prior as f64)
                    .sum::<f64>()
                    .max(1e-8);
                let n = nodes[cid].visits as f64;
                let q = if n > 0.0 { nodes[cid].value / n } else { 0.0 };
                let p = nodes[cid].prior as f64 / psum;
                let u = c_puct * p * sqrt_pv / (1.0 + n);
                logln!(
                    "  SELECT #{nid} → #{cid} [{}] (Zug: {}) N={} P={:.3} Q={:.3} U={:.3} → {:.3}",
                    log_label(&nodes, cid), names[nodes[cid].player_who_acted],
                    nodes[cid].visits, p, q, u, q + u
                );
            }
            nid = cid;
        }

        // Eval: Blattwert wurde schon bei Knoten-Erzeugung berechnet (make_node).
        let value = nodes[nid].leaf_value;
        logln!(
            "  EVAL   #{nid} ({}) win[{}]={:.3} win[{}]={:.3}",
            if ACTIVE_LEAF == LeafEval::Net { "Netz-Value" } else { "DFS-Solver" },
            names[0], value[0], names[1], value[1]
        );

        // Backprop (Netz-Blattwert, player_who_acted-Sicht).
        let mut bp = String::from("  BACKPROP");
        let mut cur = Some(nid);
        while let Some(i) = cur {
            nodes[i].visits += 1;
            let delta = value[nodes[i].player_who_acted];
            nodes[i].value += delta;
            if log.is_some() {
                bp.push_str(&format!(" #{i}+={delta:.3}({})", names[nodes[i].player_who_acted]));
            }
            cur = nodes[i].parent;
        }
        logln!("{bp}");
    }

    // Nachlauf: Force-Reply oben (Tiefe 0/1) greift nur, wenn PUCT den Knoten
    // je wieder besucht — Wurzelkinder mit sehr niedrigem Prior werden von
    // PUCT nie erneut selektiert und ihr einziges erzwungenes Kind (Tiefe 2)
    // bleibt dauerhaft ohne eigene Antwort (siehe search_common::nachlauf_targets).
    for target in crate::search_common::nachlauf_targets(&nodes) {
        logln!("  NACHLAUF → #{target}: offenes Ende nachträglich geschlossen");
        expand_and_backprop(&mut nodes, net, target, &names, &mut log);
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
    // Runde 5: informationsfreies Endspiel, siehe round5.rs -- exakte
    // Alpha-Beta-Wahl statt Netz-PUCT (kein Netz noetig, kein
    // Naeherungsfehler in der Wertungsplatten-Endwertung).
    if crate::round5::applies(state) {
        return crate::round5::choose_action(state);
    }
    let nodes = build_net_tree(net, state, sims, c_puct, add_root_noise, rng, None);
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
    // Runde 5: siehe net_search_drafting_action. Einzelner Eintrag mit
    // Gewicht 1.0 (statt leer) macht `net_drafting_policy`s Zufalls-
    // Fallback (bei leerer Stats-Liste) nicht faelschlich fuer die
    // Aktionswahl zustaendig.
    if crate::round5::applies(state) {
        return crate::round5::choose_action(state)
            .into_iter()
            .map(|a| (a, 1, 1.0))
            .collect();
    }
    let nodes = build_net_tree(net, state, sims, c_puct, add_root_noise, rng, None);
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
/// Mit `log = Some(..)` wird zusätzlich ein Sim-für-Sim-Trace protokolliert
/// (für den Server-Debug-Log-Button, analog zur Heuristik).
pub fn net_search_with_tree<R: Rng + ?Sized>(
    net: &Net,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    rng: &mut R,
    log: Option<&mut Vec<String>>,
) -> (Option<Action>, Value) {
    if state.phase != Phase::Drafting {
        return (None, Value::Null);
    }
    if crate::round5::applies(state) {
        return crate::round5::choose_action_with_analysis(state);
    }
    let nodes = build_net_tree(net, state, sims, c_puct, add_root_noise, rng, log);
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

/// Tiefe des Teilbaums unter `nid` (0 = Blatt) — Pendant zu `mcts::subtree_depth`,
/// beide delegieren an `search_common::subtree_depth`.
fn subtree_depth(nodes: &[Node], nid: usize) -> u32 {
    crate::search_common::subtree_depth(nodes, nid)
}

/// Kopfzeilen für ein Netz-PUCT-Log aus State + Analyse (für den geloggten
/// KI-Zug) — Pendant zu `mcts::search_log_header`. Der eigentliche Sim-für-
/// Sim-Trace kommt separat aus `build_net_tree`s `log`-Parameter.
pub fn net_search_log_header(state: &GameState, analysis: &Value) -> String {
    let sims = analysis["simulations"].as_u64().unwrap_or(0);
    let na = analysis["num_actions"].as_u64().unwrap_or(0);
    let considered = analysis["num_actions_considered"].as_u64().unwrap_or(0);
    let chosen = analysis["moves"]
        .as_array()
        .and_then(|ms| ms.iter().find(|m| m["chosen"] == json!(true)))
        .and_then(|m| m["description"].as_str())
        .unwrap_or("?");
    format!(
        "Netz-PUCT-Debug-Log (KI-Zug)\nSimulationen={sims}  Aktionen={considered}/{na} durchsucht (Policy-Masse-Cutoff)  Wurzelspieler={}\nSpieler: P0={}  P1={}\nGewaehlter Zug: {chosen}\n{}\n",
        state.players[state.current_player].name,
        state.players[0].name,
        state.players[1].name,
        "=".repeat(60),
    )
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
