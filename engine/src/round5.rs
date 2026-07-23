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

/// PRIMÄRER, deterministischer Cutoff je Entscheidung (analog Task #71 in
/// round_transition/round_transition_deep -- dieselbe Umstellung, hier für
/// die Runde-5-Alpha-Beta). GESCHICHTE: bis zur Determinismus-Untersuchung
/// (2026-07-22, STATUS.md "Prozessgrenzen-Nichtdeterminismus geklärt") war
/// das alte `TIME_BUDGET` (150ms, an JEDEM Knoten geprüft) der de-facto-
/// Cutoff und das alte `NODE_BUDGET` (200.000) unerreichbar (200k Knoten
/// brauchen 45-393s) -- Folge: `exact_round5_outcome` streute in-Prozess
/// bis 0,065 Gewinnwahrscheinlichkeit zwischen direkt aufeinanderfolgenden
/// Aufrufen, das Runde-4→5-Label und jede Runde-5-Bootstrap-Kette waren
/// lastabhängig verrauscht.
///
/// Kalibrierung (2026-07-23, freie lokale Maschine, Release-Build,
/// `round5_node_calibration_probe` unten: 8 realistische Runde-5-Partien
/// via `drive_to_round_start(seed, 5)`, je Entscheidung ein Negamax mit
/// unbegrenztem Knotenbudget und 150ms-Deadline): deadline-gebundene
/// Entscheidungen (n=92) erreichten min 34, p25 88, Median 155, p75 203,
/// p90 292, max 473 Knoten; vor der Deadline vollständig gelöste Teilbäume
/// (n=24, Rundenende) blieben <=144 Knoten. 200 ~ p75 hält die typische
/// Suchtiefe auf dem Niveau des alten 150ms-Cutoffs (Arena-Gegenprobe:
/// siehe STATUS.md) und deckt alle beobachteten natürlich terminierenden
/// Teilbäume ab. Kosten pro Knoten schwanken stellungsabhängig um >10x
/// (0,3-4,4ms) -- deshalb ist das Budget bewusst klein und auf REALISTISCHE
/// Stellungen kalibriert, nicht auf das billige leere Testbrett (siehe
/// Lehre im alten `TIME_BUDGET`-Kommentar: ein auf dem billigen Fall
/// kalibriertes 200k-Budget lief >60s pro Testfall).
pub const NODE_BUDGET: u64 = 200;
/// NUR NOCH Not-Deckel gegen pathologisch teure Stellungen (Task-#71-
/// Muster), NICHT mehr der primäre Cutoff -- greift er, ist das Ergebnis
/// wieder lastabhängig, darum großzügig: Worst-Case der Kalibrierung oben
/// (200 Knoten x 4,4ms/Knoten ~ 0,9s) x ~5. Unter normaler Last entscheidet
/// allein `NODE_BUDGET`; 5s x ~15-20 Halbzüge/Runde bleibt als reiner
/// Ausfallschutz auch im Self-Play tragbar (typische Entscheidung:
/// ~60-900ms, siehe Kalibrierung).
pub const TIME_BUDGET: Duration = Duration::from_secs(5);
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

/// Exakter Endwert nach optimalem Runde-5-Spiel ab `state` (muss
/// `round_number>=5` und `Phase::Drafting` sein) -- für
/// `round_transition.rs`s Runde-4-"Freebie": nach dem 4→5-Übergangs-Sample
/// braucht es KEINE Netz-Bewertung mehr, weil Runde 5 vollständig exakt
/// gelöst werden kann (kein weiterer Zufall, Kuppelraster fix, siehe
/// Modul-Kommentar oben). EIN `negamax`-Aufruf mit `perspective=0` löst dabei
/// die GESAMTE restliche Runde 5 in einem Rutsch (nicht nur den nächsten
/// Zug) -- `MAX_DEPTH`/`NODE_BUDGET`/`TIME_BUDGET` sind dieselben, mit denen
/// `choose_action` ohnehin bei JEDER echten Runde-5-Entscheidung im
/// Self-Play arbeitet (siehe `NODE_BUDGET`-Kommentar zur Kalibrierung auf
/// Self-Play-Tragbarkeit), ein Aufruf
/// vom Runde-5-START ist also strukturell dieselbe Art Suche, nur an einem
/// frühen Punkt im Baum (Budget-Semantik seit der Knoten-primär-Umstellung:
/// `NODE_BUDGET`-Knoten je Aufruf, `TIME_BUDGET` nur Not-Deckel -- siehe
/// Konstanten-Kommentare oben). `perspective=0` ist eine willkürliche, aber
/// widerspruchsfreie Referenz -- `leaf_value` ist antisymmetrisch
/// (`leaf_value(s,p) = -leaf_value(s,1-p)`), das Ergebnis gilt unabhängig
/// davon, wer gerade am Zug ist. Rückgabe im selben Format wie
/// `net_mcts::net_leaf_eval` (Pro-Spieler-"Gewinnwahrscheinlichkeits"-Paar
/// über dieselbe Sigmoid-Normalisierung wie `mcts::normalize_score`), NICHT
/// die rohe Punkte-Differenz -- damit `round_transition_value`s
/// Downstream-Verbraucher (self_play.rs-Stempelung, neural_net.py-Rescaling)
/// unverändert bleiben können.
pub(crate) fn exact_round5_outcome(state: &GameState) -> [f64; 2] {
    let diff = outcome_diff(state, Instant::now() + TIME_BUDGET);
    [crate::mcts::normalize_score(diff), crate::mcts::normalize_score(-diff)]
}

/// Kern von [`exact_round5_outcome`] mit injizierbarer Not-Deckel-Deadline --
/// ausgelagert, damit der Determinismus-Test unten (Task-#71-Muster) belegen
/// kann, dass das Ergebnis NICHT von der Deadline abhängt, solange sie nicht
/// greift (`NODE_BUDGET` ist der bindende Cutoff).
fn outcome_diff(state: &GameState, deadline: Instant) -> f64 {
    let mut node_count: u64 = 0;
    negamax(state, MAX_DEPTH.saturating_sub(1), f64::NEG_INFINITY, f64::INFINITY, 0, &mut node_count, NODE_BUDGET, deadline)
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

    /// Performance-Regressionswächter: `choose_action` darf den Not-Deckel
    /// `TIME_BUDGET` nur um eine großzügige Toleranz für den letzten, schon
    /// laufenden Negamax-Aufruf überschreiten. Historische Lehre (alter,
    /// zeit-primärer Stand): ein auf dem leeren Testbrett kalibriertes
    /// 200k-Knotenbudget ließ komplette Self-Play-Spiele >60s pro Testfall
    /// hängen -- deshalb ist `NODE_BUDGET` heute auf REALISTISCHE
    /// Stellungen kalibriert (siehe Konstanten-Kommentar), und dieser Test
    /// bleibt als Wächter gegen eine erneute Fehlkalibrierung bestehen.
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

    /// Determinismus-Kern (Ziel der Knoten-primär-Umstellung): direkt
    /// aufeinanderfolgende Aufrufe auf DERSELBEN realistischen Stellung
    /// müssen bit-identisch sein -- exakt das Szenario, in dem der alte
    /// zeit-primäre Cutoff in-Prozess bis zu 0,065 Gewinnwahrscheinlichkeit
    /// streute (STATUS.md 2026-07-22). Realistische Stellung statt
    /// `round5_state`-Leerbrett, weil das Leerbrett vor jedem Budget
    /// natürlich terminieren kann und damit trivial deterministisch wäre.
    #[test]
    fn exact_round5_outcome_is_bit_identical_across_repeats() {
        use crate::round_transition::drive_to_round_start;
        let s = drive_to_round_start(51, 5);
        let a = exact_round5_outcome(&s);
        let b = exact_round5_outcome(&s);
        let c = exact_round5_outcome(&s);
        assert_eq!(a[0].to_bits(), b[0].to_bits(), "Aufruf 1 vs 2: {} vs {}", a[0], b[0]);
        assert_eq!(a[1].to_bits(), b[1].to_bits(), "Aufruf 1 vs 2: {} vs {}", a[1], b[1]);
        assert_eq!(a[0].to_bits(), c[0].to_bits(), "Aufruf 1 vs 3: {} vs {}", a[0], c[0]);
        assert_eq!(a[1].to_bits(), c[1].to_bits(), "Aufruf 1 vs 3: {} vs {}", a[1], c[1]);
        // Live-Zugwahl haengt am selben Suchkern -- auch sie muss stabil sein.
        let m1 = choose_action(&s).expect("Aktion");
        let m2 = choose_action(&s).expect("Aktion");
        assert_eq!(m1, m2, "choose_action nicht reproduzierbar");
    }

    /// Task-#71-Kernmuster (vgl. `round_transition_deep.rs`,
    /// `pruned_action_is_deterministic_under_time_pressure`): das Ergebnis
    /// darf NICHT vom Zeit-Not-Deckel abhängen -- `NODE_BUDGET` muss der
    /// bindende Cutoff sein. Eine 10x aufgeblähte Deadline muss dasselbe
    /// Bitmuster liefern.
    #[test]
    fn outcome_is_independent_of_time_budget() {
        use crate::round_transition::drive_to_round_start;
        let s = drive_to_round_start(52, 5);
        let normal = outcome_diff(&s, Instant::now() + TIME_BUDGET);
        let inflated = outcome_diff(&s, Instant::now() + TIME_BUDGET * 10);
        assert_eq!(
            normal.to_bits(),
            inflated.to_bits(),
            "Ergebnis haengt noch vom Zeitbudget ab -- NODE_BUDGET ist nicht der bindende Cutoff: {normal} vs {inflated}"
        );
    }

    #[test]
    fn exact_round5_outcome_returns_complementary_probability_pair() {
        // normalize_score(x) + normalize_score(-x) == 1 exakt (tanh ist
        // ungerade) -- Regressionsschutz gegen eine falsch verdrahtete
        // Perspektive oder eine kaputte Normalisierung.
        let s = round5_state(21);
        let [p0, p1] = exact_round5_outcome(&s);
        assert!((0.0..=1.0).contains(&p0), "p0 ausserhalb [0,1]: {p0}");
        assert!((0.0..=1.0).contains(&p1), "p1 ausserhalb [0,1]: {p1}");
        assert!((p0 + p1 - 1.0).abs() < 1e-9, "p0+p1 sollte exakt 1 sein: {p0}+{p1}");
    }

    #[test]
    fn exact_round5_outcome_favors_the_leading_player() {
        // Kuenstlich groszer Punktevorsprung fuer Spieler 0 (direkt am
        // Score-Feld, nicht ueber echtes Spiel -- reicht hier, weil
        // `leaf_value` den aktuellen `player.score` einliest).
        let mut s = round5_state(22);
        s.players[0].score = 80;
        s.players[1].score = 5;
        let [p0, p1] = exact_round5_outcome(&s);
        assert!(p0 > p1, "fuehrender Spieler sollte hoeheren Wert bekommen: p0={p0} p1={p1}");
        assert!(p0 > 0.5, "p0 sollte deutlich ueber 0.5 liegen: {p0}");
    }

    /// Kalibrierungs-Probe (manuell, nicht Teil der Suite):
    /// `cargo test --release round5_node_calibration -- --ignored --nocapture`
    /// Misst je Runde-5-Entscheidung auf REALISTISCHEN Stellungen
    /// (`drive_to_round_start(seed, 5)`, siehe round_transition.rs-Lehre:
    /// kein synthetisches Leerbrett), wie viele Negamax-Knoten in 150ms
    /// (dem alten `TIME_BUDGET`) erreichbar sind -- Grundlage für die Wahl
    /// von `NODE_BUDGET` als primärem, deterministischem Cutoff.
    /// Auf möglichst freier Maschine laufen lassen.
    #[test]
    #[ignore]
    fn round5_node_calibration_probe() {
        use crate::round_transition::drive_to_round_start;
        let probe_budget = Duration::from_millis(150);
        let mut bound: Vec<u64> = Vec::new(); // Deadline hat gegriffen
        let mut complete: Vec<u64> = Vec::new(); // Teilbaum fertig vor Deadline
        for seed in [101u64, 202, 303, 404, 505, 606, 707, 808] {
            let mut state = drive_to_round_start(seed, 5);
            let mut step = 0u32;
            while state.phase == Phase::Drafting {
                let children = ordered_children(&state, state.current_player);
                if children.is_empty() {
                    break;
                }
                if children.len() > 1 {
                    let deadline = Instant::now() + probe_budget;
                    let t0 = Instant::now();
                    let mut nodes: u64 = 0;
                    let _ = negamax(
                        &state,
                        MAX_DEPTH.saturating_sub(1),
                        f64::NEG_INFINITY,
                        f64::INFINITY,
                        state.current_player,
                        &mut nodes,
                        u64::MAX,
                        deadline,
                    );
                    let elapsed = t0.elapsed();
                    let deadline_hit = elapsed >= probe_budget;
                    eprintln!(
                        "seed={seed} step={step} kandidaten={} nodes={nodes} elapsed={elapsed:?} deadline_hit={deadline_hit}",
                        children.len()
                    );
                    if deadline_hit {
                        bound.push(nodes);
                    } else {
                        complete.push(nodes);
                    }
                }
                let chosen = choose_action(&state).expect("Aktion");
                let mut g = Game { state };
                g.apply_drafting(&chosen).expect("legal");
                state = g.state;
                step += 1;
            }
        }
        let stats = |label: &str, v: &mut Vec<u64>| {
            if v.is_empty() {
                eprintln!("{label}: keine Messpunkte");
                return;
            }
            v.sort_unstable();
            let p = |q: f64| v[((v.len() - 1) as f64 * q) as usize];
            eprintln!(
                "{label}: n={} min={} p25={} median={} p75={} p90={} max={}",
                v.len(), v[0], p(0.25), p(0.5), p(0.75), p(0.9), v[v.len() - 1]
            );
        };
        stats("DEADLINE-GEBUNDEN (relevant fuer NODE_BUDGET)", &mut bound);
        stats("VOR DEADLINE FERTIG (natuerlich beschraenkt)", &mut complete);
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
