//! MCTS für die Drafting-Phase — Negamax-UCT mit heuristischer Blattbewertung.
//!
//! Bewusst einfaches „Shaping": der Wert eines Zustands ist allein
//! `(eigene Punkte + Schätzung) − (gegnerische Punkte + Schätzung)` (siehe
//! [`crate::evaluate`]), nach `tanh` in (−1, 1) gestaucht. Kein Random-Rollout —
//! die Schätzung enthält bereits die erwartbaren Tiling-Punkte voller Reihen.
//! Bei genügend Simulationen liefert das vernünftige Drafting-Züge.
//!
//! Aktionsraum = Drafting-Züge ([`crate::game::drafting_actions`]). Knoten
//! außerhalb der Drafting-Phase werden als Blätter behandelt (nicht expandiert).

use rand::{Rng, RngExt};

use crate::evaluate::estimate_round_score;
use crate::game::{drafting_actions, Game};
use crate::moves::Action;
use crate::state::{GameState, Phase};

/// Skaliert die Punktedifferenz vor `tanh` (kleiner = aggressiver gesättigt).
pub const VALUE_SCALE: f64 = 15.0;
/// Standard-Explorationskonstante für UCT.
pub const DEFAULT_C: f64 = 1.4;

struct Node {
    parent: Option<usize>,
    children: Vec<usize>,
    untried: Vec<Action>,
    /// Aktion, die vom Elternknoten hierher führte (None nur an der Wurzel).
    action: Option<Action>,
    visits: u32,
    /// Aufsummierte Bewertung aus Sicht des Spielers, der in `state` am Zug ist.
    value_sum: f64,
    state: GameState,
    terminal: bool,
}

/// Gesamtwert eines Spielers = aktuelle Punkte + Rundenschätzung.
fn player_total(state: &GameState, pi: usize) -> f64 {
    state.players[pi].score as f64 + estimate_round_score(&state.players[pi], true) as f64
}

/// Blattbewertung aus Sicht des Spielers, der in `state` am Zug ist: gestauchte
/// Punktedifferenz zum Gegner in (−1, 1).
fn evaluate(state: &GameState) -> f64 {
    let cur = state.current_player;
    let other = 1 - cur;
    let margin = player_total(state, cur) - player_total(state, other);
    (margin / VALUE_SCALE).tanh()
}

fn make_node(state: GameState, parent: Option<usize>, action: Option<Action>) -> Node {
    let terminal = state.phase != Phase::Drafting;
    let untried = if terminal { Vec::new() } else { drafting_actions(&state) };
    Node {
        parent,
        children: Vec::new(),
        untried,
        action,
        visits: 0,
        value_sum: 0.0,
        state,
        terminal,
    }
}

/// Wendet eine Drafting-Aktion auf eine Kopie des Zustands an.
fn apply_action(state: &GameState, action: &Action) -> Option<GameState> {
    let mut game = Game { state: state.clone() };
    game.apply_drafting(action).ok()?;
    Some(game.state)
}

/// UCT-Auswahl: bestes Kind aus Sicht des Elternknotens (Negamax → Kindwert negieren).
fn best_uct_child(nodes: &[Node], nid: usize, c: f64) -> usize {
    let ln_parent = (nodes[nid].visits as f64).ln();
    let mut best = nodes[nid].children[0];
    let mut best_score = f64::NEG_INFINITY;
    for &cid in &nodes[nid].children {
        let n = nodes[cid].visits as f64;
        let exploit = -(nodes[cid].value_sum / n); // Kind aus Gegnersicht → negieren
        let explore = c * (ln_parent / n).sqrt();
        let score = exploit + explore;
        if score > best_score {
            best_score = score;
            best = cid;
        }
    }
    best
}

/// Führt `simulations` MCTS-Iterationen ab `state` aus und gibt die beste
/// Drafting-Aktion (meistbesuchtes Wurzelkind) zurück. None, wenn der Zustand
/// nicht in der Drafting-Phase ist.
pub fn search_drafting_action<R: Rng + ?Sized>(
    state: &GameState,
    simulations: u32,
    c: f64,
    rng: &mut R,
) -> Option<Action> {
    if state.phase != Phase::Drafting {
        return None;
    }

    // Wurzelzustand ohne (potenziell langen) Log klonen — Knoten sammeln nur
    // ihre eigenen Zug-Logs.
    let mut root_state = state.clone();
    root_state.log.clear();

    let mut nodes: Vec<Node> = vec![make_node(root_state, None, None)];

    for _ in 0..simulations {
        // 1. Selection: bis zu einem expandierbaren oder terminalen Knoten.
        let mut nid = 0;
        loop {
            if nodes[nid].terminal || !nodes[nid].untried.is_empty() {
                break;
            }
            if nodes[nid].children.is_empty() {
                break;
            }
            nid = best_uct_child(&nodes, nid, c);
        }

        // 2. Expansion: eine zufällige unversuchte Aktion ausspielen.
        if !nodes[nid].terminal && !nodes[nid].untried.is_empty() {
            let idx = rng.random_range(0..nodes[nid].untried.len());
            let action = nodes[nid].untried.swap_remove(idx);
            if let Some(child_state) = apply_action(&nodes[nid].state, &action) {
                let child = make_node(child_state, Some(nid), Some(action));
                let cid = nodes.len();
                nodes.push(child);
                nodes[nid].children.push(cid);
                nid = cid;
            }
        }

        // 3. Bewertung des Blatts (aus Sicht seines Spielers am Zug).
        let value = evaluate(&nodes[nid].state);

        // 4. Backprop (Negamax: Vorzeichen pro Ebene wechseln).
        let mut cur = Some(nid);
        let mut val = value;
        while let Some(i) = cur {
            nodes[i].visits += 1;
            nodes[i].value_sum += val;
            val = -val;
            cur = nodes[i].parent;
        }
    }

    // Robuste Wahl: meistbesuchtes Wurzelkind.
    nodes[0]
        .children
        .iter()
        .max_by_key(|&&cid| nodes[cid].visits)
        .and_then(|&cid| nodes[cid].action.clone())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::setup_new_game;
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
        let legal = drafting_actions(&s);
        assert!(legal.contains(&action), "MCTS-Aktion muss legal sein: {action:?}");
    }

    #[test]
    fn root_visits_match_simulations() {
        // Indirekt geprüft über mehrere Sim-Zahlen: mehr Sims → (meist) stabile Wahl.
        let s = drafting_state(7);
        let mut rng = StdRng::seed_from_u64(2);
        let a = search_drafting_action(&s, 50, DEFAULT_C, &mut rng);
        let b = search_drafting_action(&s, 50, DEFAULT_C, &mut rng);
        assert!(a.is_some() && b.is_some());
    }

    #[test]
    fn none_outside_drafting() {
        let mut s = drafting_state(7);
        s.phase = Phase::Tiling;
        let mut rng = StdRng::seed_from_u64(3);
        assert!(search_drafting_action(&s, 10, DEFAULT_C, &mut rng).is_none());
    }

    #[test]
    fn prefers_scoring_over_floor_dump() {
        // Konstruiert: aktiver Spieler kann eine Reihe sinnvoll füllen ODER alles
        // auf die Strafleiste werfen. MCTS sollte nicht die Strafleiste wählen.
        let s = drafting_state(11);
        let mut rng = StdRng::seed_from_u64(4);
        let action = search_drafting_action(&s, 400, DEFAULT_C, &mut rng).expect("Aktion");
        // Direkter Strafleisten-Wurf (row == -1) ist fast nie optimal früh im Spiel.
        if let Action::Stone(m) = &action {
            assert_ne!(m.place.row_index, -1, "MCTS sollte nicht auf die Strafleiste werfen");
        }
    }
}
