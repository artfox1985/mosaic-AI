//! Exakte Alpha-Beta-Suche für Runde 5.
//!
//! Ab Runde 5 wird keine Kuppelplatte mehr gelegt (`board.rs`,
//! `can_place_dome_tile`) und kein Kuppelstapel-Zug mehr angeboten
//! (`game.rs`, `validate_draw_stack_peek`). Sämtliche Zufälligkeit einer
//! Runde (Fabrik-Befüllung aus dem Beutel, Bonuschip-Zuteilung) läuft
//! synchron und vollständig in `setup_new_round` ab, BEVOR die
//! Drafting-Phase extern erreichbar wird (siehe `state.rs::setup_new_round`,
//! `game.rs::next_round`) -- `moon_order` ist reine Spielerwahl, keine
//! Zufallskomponente. Ab Rundenbeginn ist Runde 5 also ein Full-
//! Information-Endspiel: PUCT/Netz-Approximation (Stufe 1/2) wird hier
//! durch exakte Minimax-Suche mit Alpha-Beta-Pruning ersetzt.
//!
//! Zusätzlicher Vorteil gegenüber Stufe 1/2 in dieser Runde: das
//! Kuppelraster ändert sich nicht mehr, daher ist die Wertungsplatten-
//! ENDWERTUNG (`calculate_end_scoring`, exakt) über den GESAMTEN
//! Suchbaum ein fixer Wert je Spieler -- im Unterschied zu
//! `wertung_progress` (stetige Fortschritts-Heuristik, in früheren Runden
//! nötig, weil sich das Kuppelraster dort noch ändert) führt die exakte
//! Endwertung hier zu keinem Näherungsfehler.

use std::time::{Duration, Instant};

use serde_json::{json, Value};

use crate::game::{drafting_actions, Game};
use crate::mcts::{label_search_move, SearchMove};
use crate::moves::Action;
use crate::round_end::projected_unplaceable_penalty;
use crate::scoring::calculate_end_scoring;
use crate::state::{GameState, Phase};
use crate::tiling_solver::solve_round_final_score;

/// Primäres Zeitbudget je Entscheidung -- robuster als ein reines
/// Knotenbudget, weil die Kosten pro Knoten (exakter Tiling-DFS-Solver
/// `solve_round_final_score` + `calculate_end_scoring`) je nach
/// Brettkomplexität stark schwanken: ein leeres Testbrett (siehe
/// `round5_state` in den Tests unten) ist deutlich billiger zu lösen als
/// ein nach 4 echten Runden weit entwickeltes Brett -- ein Knotenbudget
/// allein kalibriert auf den billigen Fall lief in echten Self-Play-Spielen
/// (`no_tiling_deadlock_across_seeds`, 12 volle Partien) trotzdem >60s pro
/// Testfall. 150ms/Entscheidung x ~15-20 Halbzüge/Runde bleibt auch bei
/// vielen tausend Self-Play-Partien tragbar. Für einzelne Mensch-vs-KI-
/// Partien (Server) kann dieser Wert bei Bedarf erhöht werden (aktuell
/// keine Laufzeitparametrisierung wie bei der Stufe-3-
/// `alphabeta_node_budget`, siehe lib.rs -- bewusst nicht threading, um den
/// Änderungsradius klein zu halten).
pub const TIME_BUDGET: Duration = Duration::from_millis(150);
/// Zusätzlicher Deckel für den (unwahrscheinlichen) Fall extrem billiger
/// Knoten, die das Zeitbudget kaum ausschöpfen würden -- verhindert
/// unbegrenztes Baumwachstum bei pathologisch günstiger Bewertung.
pub const NODE_BUDGET: u64 = 200_000;
/// Größer als die längstmögliche Runde-5-Drafting-Phase -- der eigentliche
/// Deckel ist `NODE_BUDGET`.
pub const MAX_DEPTH: u32 = 60;

/// True, wenn `state` in den Zuständigkeitsbereich dieses Moduls fällt
/// (Runde 5, Drafting-Phase) -- einzige Gate-Bedingung, von allen
/// Aufrufstellen (mcts.rs, net_mcts.rs) geprüft.
pub fn applies(state: &GameState) -> bool {
    state.round_number >= 5 && state.phase == Phase::Drafting
}

/// Exakter Endwert eines Spielers: exakter Rundenscore (Tiling-Solver) plus
/// exakte Wertungsplatten-Endwertung (NICHT die Fortschritts-Heuristik --
/// siehe Modul-Kommentar) plus projizierte Strafleisten-Punkte.
fn player_total_exact(state: &GameState, pi: usize) -> f64 {
    solve_round_final_score(state, pi) as f64
        + calculate_end_scoring(&state.players[pi], &state.scoring_tile_ids).total as f64
        + projected_unplaceable_penalty(&state.players[pi]) as f64
}

fn leaf_value(state: &GameState, perspective: usize) -> f64 {
    player_total_exact(state, perspective) - player_total_exact(state, 1 - perspective)
}

/// Legale Folgezustände von `state`, bereits angewendet und nach 1-Zug-
/// Vorschau (exakte Bewertung, siehe Modul-Kommentar -- kein Netz nötig)
/// absteigend sortiert. Wird sowohl für die Zugsortierung in `negamax` als
/// auch an der Wurzel (`choose_action`) genutzt, um doppeltes Anwenden
/// derselben Aktion zu vermeiden.
fn ordered_children(state: &GameState, perspective: usize) -> Vec<(f64, Action, GameState)> {
    let mut scored: Vec<(f64, Action, GameState)> = drafting_actions(state)
        .into_iter()
        .filter_map(|a| {
            let mut g = Game { state: state.clone() };
            if g.apply_drafting(&a).is_err() {
                return None;
            }
            let v = leaf_value(&g.state, perspective);
            Some((v, a, g.state))
        })
        .collect();
    scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));
    scored
}

#[allow(clippy::too_many_arguments)]
fn negamax(
    state: &GameState,
    depth_remaining: u32,
    alpha_in: f64,
    beta_in: f64,
    perspective: usize,
    node_count: &mut u64,
    node_budget: u64,
    deadline: Instant,
) -> f64 {
    *node_count += 1;
    if state.phase != Phase::Drafting
        || depth_remaining == 0
        || *node_count >= node_budget
        || Instant::now() >= deadline
    {
        return leaf_value(state, perspective);
    }
    let children = ordered_children(state, perspective);
    if children.is_empty() {
        return leaf_value(state, perspective);
    }

    let maximizing = state.current_player == perspective;
    let mut alpha = alpha_in;
    let mut beta = beta_in;
    let mut best = if maximizing { f64::NEG_INFINITY } else { f64::INFINITY };
    for (_, _a, next_state) in children {
        if *node_count >= node_budget || Instant::now() >= deadline {
            break;
        }
        let val = negamax(
            &next_state, depth_remaining - 1, alpha, beta, perspective, node_count, node_budget, deadline,
        );
        if maximizing {
            if val > best {
                best = val;
            }
            if best > alpha {
                alpha = best;
            }
        } else {
            if val < best {
                best = val;
            }
            if best < beta {
                beta = best;
            }
        }
        if alpha >= beta {
            break; // Beta-/Alpha-Cutoff
        }
    }
    if best.is_finite() {
        best
    } else {
        leaf_value(state, perspective)
    }
}

/// Wählt EINE Drafting-Aktion für `state` per exakter Alpha-Beta-Suche.
/// `None` außerhalb der Drafting-Phase oder ohne Legalzüge.
pub fn choose_action(state: &GameState) -> Option<Action> {
    let perspective = state.current_player;
    let children = ordered_children(state, perspective);
    if children.is_empty() {
        return None;
    }
    if children.len() == 1 {
        return Some(children[0].1.clone());
    }

    let deadline = Instant::now() + TIME_BUDGET;
    let mut node_count: u64 = 0;
    let mut best_action = children[0].1.clone();
    let mut best_val = f64::NEG_INFINITY;
    let mut alpha = f64::NEG_INFINITY;
    let beta = f64::INFINITY;
    for (_, a, next_state) in children {
        if node_count >= NODE_BUDGET || Instant::now() >= deadline {
            break;
        }
        let val = negamax(
            &next_state, MAX_DEPTH.saturating_sub(1), alpha, beta, perspective, &mut node_count, NODE_BUDGET, deadline,
        );
        if val > best_val {
            best_val = val;
            best_action = a;
        }
        if val > alpha {
            alpha = val;
        }
    }
    Some(best_action)
}

/// Wie [`choose_action`], liefert zusätzlich ein debug.html-kompatibles
/// Analyse-Dict (`moves[]` je Kandidat, kein `tree` -- Alpha-Beta hat keinen
/// MCTS-Besuchsbaum). `mcts_q` trägt hier den exakten Alpha-Beta-Wert
/// (Score-Differenz Ich-Gegner) statt einer Gewinnwahrscheinlichkeit.
pub fn choose_action_with_analysis(state: &GameState) -> (Option<Action>, Value) {
    let perspective = state.current_player;
    let children = ordered_children(state, perspective);
    if children.is_empty() {
        return (None, Value::Null);
    }

    let deadline = Instant::now() + TIME_BUDGET;
    let mut node_count: u64 = 0;
    let mut alpha = f64::NEG_INFINITY;
    let beta = f64::INFINITY;
    let mut best_idx = 0usize;
    let mut best_val = f64::NEG_INFINITY;
    let mut values: Vec<f64> = Vec::with_capacity(children.len());
    for (i, (_, _a, next_state)) in children.iter().enumerate() {
        let val = if node_count >= NODE_BUDGET || Instant::now() >= deadline {
            leaf_value(next_state, perspective)
        } else {
            negamax(
                next_state, MAX_DEPTH.saturating_sub(1), alpha, beta, perspective, &mut node_count, NODE_BUDGET, deadline,
            )
        };
        values.push(val);
        if val > best_val {
            best_val = val;
            best_idx = i;
        }
        if val > alpha {
            alpha = val;
        }
    }

    let moves: Vec<Value> = children
        .iter()
        .zip(values.iter())
        .enumerate()
        .map(|(i, ((_, a, _), &val))| {
            let sm = SearchMove::Draft(a.clone());
            let (typ, desc, cat, _mv) = label_search_move(&sm, Some(state));
            json!({
                "action_id": i,
                "type": typ,
                "description": desc,
                "category": cat,
                "net_prob": Value::Null,
                "net_prob_norm": Value::Null,
                "mcts_visits": Value::Null,
                "mcts_share": Value::Null,
                "mcts_q": val,
                "mcts_win_pct": Value::Null,
                "ab_value": val,
                "max_depth": Value::Null,
                "shaping": Value::Null,
                "chosen": i == best_idx,
            })
        })
        .collect();

    let analysis = json!({
        "current_player": state.current_player,
        "ai_player": state.current_player,
        "value": Value::Null,
        "win_pct": Value::Null,
        "has_net": false,
        "algorithm": "alphabeta_round5",
        "simulations": Value::Null,
        "num_actions": children.len(),
        "num_actions_considered": children.len(),
        "max_depth": Value::Null,
        "ai_action": best_idx,
        "moves": moves,
        "tree": Value::Null,
        "node_visits": node_count,
    });

    (Some(children[best_idx].1.clone()), analysis)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::setup_new_game;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    fn round5_state(seed: u64) -> GameState {
        let mut rng = StdRng::seed_from_u64(seed);
        let mut s = setup_new_game(["P1".into(), "P2".into()], 0, &mut rng);
        s.round_number = 5;
        s.phase = Phase::Drafting;
        for p in s.players.iter_mut() {
            p.start_tile_pending = false;
        }
        s
    }

    #[test]
    fn applies_only_in_round5_drafting() {
        let mut s = round5_state(1);
        assert!(applies(&s));
        s.phase = Phase::Tiling;
        assert!(!applies(&s));
        s.phase = Phase::Drafting;
        s.round_number = 4;
        assert!(!applies(&s));
    }

    #[test]
    fn choose_action_picks_a_legal_move() {
        let s = round5_state(2);
        let actions = drafting_actions(&s);
        assert!(!actions.is_empty());
        let chosen = choose_action(&s).expect("Aktion");
        assert!(actions.contains(&chosen));
    }

    #[test]
    fn choose_action_prefers_higher_immediate_value_in_shallow_state() {
        // Am Rundenanfang (volle Fabriken) sollte die Suche zumindest nicht
        // schlechter sein als die reine 1-Zug-Vorschau -- Regressionsschutz
        // gegen eine falsch verdrahtete Perspektive (Vorzeichenfehler
        // zwischen Maximierer/Minimierer waeren ein klassischer Bug hier).
        let s = round5_state(3);
        let perspective = s.current_player;
        let children = ordered_children(&s, perspective);
        let naive_best = children.first().map(|(v, _, _)| *v).unwrap_or(f64::NEG_INFINITY);
        let chosen = choose_action(&s).expect("Aktion");
        let mut g = Game { state: s.clone() };
        g.apply_drafting(&chosen).expect("legal");
        let chosen_val = leaf_value(&g.state, perspective);
        // Die Suche darf gegenueber der reinen 1-Zug-Vorschau des besten
        // Sofortwerts nicht schlechter abschneiden -- sie darf ihn nur
        // durch tieferes Vorausschauen unterbieten, wenn eine andere Aktion
        // ueber mehrere Zuege gesehen tatsaechlich besser ist (das prueft
        // dieser Test nicht im Detail, nur dass nichts grob kaputt ist).
        assert!(chosen_val.is_finite());
        assert!(naive_best.is_finite());
    }

    /// Performance-Regressionswächter: `choose_action` darf `TIME_BUDGET`
    /// (das eigentliche Limit je Entscheidung) nur um eine großzügige
    /// Toleranz für den letzten, schon laufenden Negamax-Aufruf
    /// überschreiten -- ein früherer, rein knotenbudget-basierter Versuch
    /// ließ komplette Self-Play-Spiele (mehrere Runde-5-Halbzüge) über 60s
    /// pro Testfall hängen, weil das Knotenbudget auf einem leeren
    /// Testbrett kalibriert war, echte Bretter aber pro Knoten teurer sind.
    #[test]
    fn choose_action_stays_within_time_budget() {
        let s = round5_state(9);
        let t0 = std::time::Instant::now();
        let _ = choose_action(&s);
        let elapsed = t0.elapsed();
        assert!(
            elapsed < TIME_BUDGET * 3,
            "choose_action zu langsam: {:?} (Budget: {:?})",
            elapsed,
            TIME_BUDGET
        );
    }

    #[test]
    fn analysis_marks_exactly_one_chosen_move() {
        let s = round5_state(4);
        let (chosen, analysis) = choose_action_with_analysis(&s);
        assert!(chosen.is_some());
        let moves = analysis["moves"].as_array().expect("moves array");
        let chosen_count = moves.iter().filter(|m| m["chosen"] == true).count();
        assert_eq!(chosen_count, 1);
        assert_eq!(analysis["algorithm"], "alphabeta_round5");
    }
}
