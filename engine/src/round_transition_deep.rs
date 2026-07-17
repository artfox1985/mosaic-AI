//! Mehrstufiges Rundenübergangs-Sampling (Runde 1-3), aufbauend auf
//! `round_transition.rs` (EIN Übergang) und `round5::exact_round5_outcome`
//! (Runde-4-Freebie: Runde 5 ist exakt lösbar, kein weiterer Zufall).
//!
//! Für Runde 1-3 bleibt nach einem einzelnen Übergangs-Sample immer noch
//! der komplette Rest des Spiels unmodelliert -- die tiefere Version dieses
//! Rauschproblems. Architektur hier: REKURSIV, NICHT kombinatorisch. Für
//! `round_before == r` simuliert der Evaluator Runde r+1 EINMAL durch
//! (`simulate_one_round`), sampelt den (r+1)→(r+2)-Übergang mit
//! `n_samples = 1` (nicht erneut N-fach -- das hält die Kosten additiv über
//! die Tiefe, nicht multiplikativ), und rekursiert in Runde (r+1)s eigenen
//! Evaluator, bis Runde 4 (Freebie) als Basisfall erreicht ist:
//!
//! ```text
//! Runde 4 (4→5):  round5::exact_round5_outcome (Freebie, unveraendert)
//! Runde 3 (3→4):  simuliere Runde 4, 1×Sample 4→5, → exact_round5_outcome
//! Runde 2 (2→3):  simuliere Runde 3, 1×Sample 3→4, → continue_through_round4
//! Runde 1 (1→2):  simuliere Runde 2, 1×Sample 2→3, → continue_through_round3
//! ```
//!
//! Runde 1 bleibt trotzdem der teuerste Fall (3 verschachtelte
//! Zwischenrunden-Simulationen in der Kette) -- erwartungsgemäß, siehe
//! Nutzer-Vorgabe in der Plan-Datei.
//!
//! **Zwischenrunden-Zugwahl** (`choose_drafting_action_pruned`) nutzt
//! `mcts::player_total` (Fortschritts-Heuristik) + Alpha-Beta, strukturell
//! identisch zu `mcts.rs`s Stufe-1-Suche (dort bewusst auf EINE Runde
//! beschränkt) -- hier nur zusätzlich mit Netz-Policy-Priors vorsortiert,
//! um vor der (teureren) 1-Zug-Vorschau bereits die Kandidatenzahl klein zu
//! halten.
//!
//! **Wichtige Scoping-Entscheidung, beim Implementieren erkannt (nicht
//! Teil des ursprünglichen Plans in dieser Form)**: die "Gamma-Pruning für
//! Geschwister-Kandidaten"-Idee aus der Plan-Datei (mehrere rundenendende
//! Kandidaten je über eine kleine Rundenübergangs-Stichprobe vergleichen,
//! per optimistischem Punkte-Deckel früh abbrechen) würde bedeuten, dass
//! `choose_drafting_action_pruned` bei JEDEM rundenendenden Kandidaten
//! erneut durch `sample_round_transition_value` müsste -- das reintroduziert
//! genau die kombinatorische Verzweigung, die die "1 Kontinuation je
//! äußerem Sample"-Architektur oben bewusst vermeidet. Diese erste Version
//! nutzt deshalb für ALLE Kandidaten (rundenendend oder nicht) denselben
//! günstigen, deterministischen `leaf_value_progress`-Wert -- exakt wie
//! `mcts.rs`s bestehende Stufe-1-Suche es an ihrer eigenen Rundengrenze
//! bereits tut. Eine Chance-Knoten-bewusste Gamma-Pruning-Erweiterung
//! (mehrere rundenendende Kandidaten aktiv gegeneinander per Stichprobe
//! abwägen) ist als expliziter Folge-Schritt zu behandeln, nicht Teil
//! dieser ersten, funktionierenden Version.
//!
//! **Information-Set-Determinisierung für den Kuppelstapel**: kein neuer
//! Mechanismus -- Wiederverwendung des bereits vorhandenen, geprüften
//! Musters aus `self_play.rs::mean_rollout_diff` ("Determinisierung Weg
//! 1"): `dome_tile_pool` wird EINMAL pro simulierter Runde neu gemischt
//! (beim Eintritt in `simulate_one_round`, vor der ersten Drafting-
//! Entscheidung). `bag`/`bonus_chip_pool` werden NICHT hier zusätzlich
//! gemischt -- das übernimmt bereits `sample_round_transition_value` beim
//! Übergang IN die simulierte Runde hinein.
//!
//! **Alle Zeit-/Sample-Konstanten unten sind NICHT empirisch kalibriert**
//! (gleiche Lehre wie `round5.rs`s erste, ~75x zu optimistische
//! Kalibrierung auf einem synthetischen Brett statt echten Self-Play-
//! Zuständen) -- vor breitem Einsatz gegen echte Zustände nachmessen.
//!
//! Nur für den Trainingsziel-Pfad gedacht (`self_play.rs`), NICHT für die
//! Live-Suche (`net_mcts.rs`) -- selbst Runde 3s günstigste Kette wäre dort
//! (Runden-End-Knoten entstehen bei jedem Baum-Ast, nicht nur ~4x/Partie)
//! klar zu teuer. Gleiches Gating-Prinzip wie `ROUND_TRANSITION_SAMPLING`.

use std::time::{Duration, Instant};

use rand::seq::SliceRandom;
use rand::Rng;

use crate::game::Game;
use crate::moves::Action;
use crate::net::Net;
use crate::round_transition::{self, PreChanceState};
use crate::state::{GameState, Phase};

// ── Konstanten (NICHT empirisch kalibriert, siehe Modul-Kommentar) ──────────

/// Äußere Sample-Zahl je Rundentiefe -- weniger für Runde 1 (teuer: 3
/// verschachtelte Zwischenrunden-Simulationen pro Sample), mehr für Runde 3
/// (billig: nur 1 Zwischenrunde bis zum Runde-5-Freebie).
pub const N_SAMPLES_TRAIN_ROUND1: u32 = 4;
pub const N_SAMPLES_TRAIN_ROUND2: u32 = 8;
pub const N_SAMPLES_TRAIN_ROUND3: u32 = 16;

/// Gesamt-Zeitbudget je äußerem `sample_round_transition_value`-Aufruf
/// (deckt bis zu `N_SAMPLES_TRAIN_ROUNDx` Samples ab, jedes selbst eine
/// ganze Simulationskette). Grosszügig, aber begrenzt -- degradiert
/// graceful auf weniger Samples, falls überschritten (siehe
/// `round_transition.rs::sample_round_transition_value`).
pub const TIME_BUDGET_TRAIN_ROUND1: Duration = Duration::from_secs(15);
pub const TIME_BUDGET_TRAIN_ROUND2: Duration = Duration::from_secs(15);
pub const TIME_BUDGET_TRAIN_ROUND3: Duration = Duration::from_secs(15);
// Einmalig gegen v8c auf je EINEM echten Runde-2/3/4-Start-Zustand gemessen
// (ein Sample je Tiefe, nicht über mehrere Zustände gemittelt -- also noch
// kein belastbarer Durchschnitt, siehe Modul-Kommentar):
// continue_through_round2 (Runde-1-Evaluator) ~1,13s/Sample,
// continue_through_round3 (Runde-2-Evaluator) ~0,63s/Sample,
// continue_through_round4 (Runde-3-Evaluator) ~0,69s/Sample.
// Ergibt bei den obigen N grob ~4,5s/5,0s/11s je Rundentiefe (~20s/Partie
// zusätzlich) -- deutlich unter den 15s-Budgets, Luft nach oben vorhanden.

/// Zusätzliches Zeitbudget, das `self_play.rs::play_net_self_play_game`s
/// eigener Hänger-Schutz-Timeout (`net_game_timeout_secs`) einrechnen MUSS.
/// Worst-Case-Summe aller vier Rundenübergangs-Budgets (die drei obigen +
/// `round_transition::TIME_BUDGET_TRAIN_ROUND4`, der bestehende Runde-4-
/// Freebie). LIVE BEOBACHTET, nicht nur theoretisch: ein erster End-zu-End-
/// Smoke-Test (60 Sims, `net_game_timeout_secs(60)=30s`) brach ab, BEVOR
/// Runde 5 je erreicht wurde (0 Runde-5-Schritte im Ergebnis trotz
/// vollständigem Runde-1-4-Sampling) -- exakt derselbe Fehlermodus, den
/// `net_game_timeout_secs`s eigener Kommentar für die BAG/Faktoren-
/// Kalibrierung beschreibt ("scores/winner sind dann kein echtes
/// Endergebnis"), jetzt durch dieses Moduls zusätzliche synchrone
/// Sampling-Zeit reproduziert.
pub const EXTRA_GAME_TIMEOUT_SECS: u64 = 5 + 15 + 15 + 15; // Runde4+3+2+1, Worst-Case-Summe

/// Suchtiefe/-budget der Zwischenrunden-Zugwahl (`choose_drafting_action_pruned`)
/// je Einzelentscheidung -- bewusst deutlich billiger als `round5::TIME_BUDGET`
/// (150ms): das hier ist eine Fortschritts-Heuristik-Suche für eine
/// SIMULIERTE Zwischenrunde, kein Vollsolve.
pub const POLICY_DEPTH: u32 = 4;
pub const POLICY_NODE_BUDGET: u64 = 20_000;
pub const POLICY_TIME_BUDGET_PER_DECISION: Duration = Duration::from_millis(15);

/// Gesamt-Wall-Clock-Sicherheitsnetz für EINE simulierte Runde
/// (~15-20 Entscheidungen).
pub const ROUND_SIM_TIME_BUDGET: Duration = Duration::from_millis(600);

/// Zeitbudget für den EINEN verschachtelten Chance-Node-Sample-Aufruf
/// (`n_samples = 1`) nach einer simulierten Zwischenrunde.
pub const INNER_SAMPLE_TIME_BUDGET: Duration = Duration::from_millis(300);

// ── Zwischenrunden-Zugwahl ───────────────────────────────────────────────────

/// Wie `round5.rs::leaf_value`, aber mit der Fortschritts-Heuristik
/// (`mcts::player_total`) statt exakter Endwertung -- gültig für JEDE
/// laufende Runde (Kuppelraster nicht eingefroren), nicht nur Runde 5.
fn leaf_value_progress(state: &GameState, perspective: usize) -> f64 {
    crate::mcts::player_total(state, perspective) - crate::mcts::player_total(state, 1 - perspective)
}

/// Wie `round5.rs::ordered_children`, aber die Kandidatenliste kommt aus
/// `priors` (Netz-Policy, bereits `POLICY_MASS_CUTOFF`-gekappt/sortiert via
/// `net_mcts::drafting_action_priors`) statt aus ALLEN Legalzügen -- hält
/// die 1-Zug-Vorschau-Kosten klein, bevor überhaupt evaluiert wird.
fn ordered_children_pruned(
    priors: impl Fn(&GameState) -> Vec<(Action, f32)>,
    state: &GameState,
    perspective: usize,
) -> Vec<(f64, Action, GameState)> {
    let mut scored: Vec<(f64, Action, GameState)> = priors(state)
        .into_iter()
        .filter_map(|(a, _p)| {
            let mut g = Game { state: state.clone() };
            if g.apply_drafting(&a).is_err() {
                return None;
            }
            let v = leaf_value_progress(&g.state, perspective);
            Some((v, a, g.state))
        })
        .collect();
    scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));
    scored
}

/// Wie `round5.rs::negamax` (identische Alpha-Beta-Struktur), aber mit
/// `leaf_value_progress`/`ordered_children_pruned` statt der exakten
/// Runde-5-Varianten. Der bestehende `state.phase != Phase::Drafting`-
/// Stopp fällt bereits GENAU auf das Rundenende -- kein Sonderfall nötig,
/// die Rekursion bleibt strukturell auf EINE Runde beschränkt (wie
/// `mcts.rs`s Stufe-1-Suche).
#[allow(clippy::too_many_arguments)]
fn negamax_progress(
    priors: impl Fn(&GameState) -> Vec<(Action, f32)> + Copy,
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
        return leaf_value_progress(state, perspective);
    }
    let children = ordered_children_pruned(priors, state, perspective);
    if children.is_empty() {
        return leaf_value_progress(state, perspective);
    }
    let maximizing = state.current_player == perspective;
    let mut alpha = alpha_in;
    let mut beta = beta_in;
    let mut best = if maximizing { f64::NEG_INFINITY } else { f64::INFINITY };
    for (_, _a, next_state) in children {
        if *node_count >= node_budget || Instant::now() >= deadline {
            break;
        }
        let val = negamax_progress(
            priors, &next_state, depth_remaining - 1, alpha, beta, perspective, node_count, node_budget, deadline,
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
        leaf_value_progress(state, perspective)
    }
}

/// Wählt EINE Drafting-Aktion für `state` per Fortschritts-Heuristik +
/// Alpha-Beta (siehe Modul-Kommentar für die Gamma-Pruning-Scoping-
/// Entscheidung). `None` außerhalb der Drafting-Phase oder ohne Legalzüge.
/// Eigenständiges Zeitbudget (wie `round5::choose_action`), nicht von
/// einem entfernten Aufrufer durchgereicht.
pub(crate) fn choose_drafting_action_pruned(
    priors: impl Fn(&GameState) -> Vec<(Action, f32)> + Copy,
    state: &GameState,
    depth: u32,
    node_budget: u64,
    time_budget: Duration,
) -> Option<Action> {
    let perspective = state.current_player;
    let children = ordered_children_pruned(priors, state, perspective);
    if children.is_empty() {
        return None;
    }
    if children.len() == 1 {
        return Some(children[0].1.clone());
    }
    let deadline = Instant::now() + time_budget;
    let mut node_count: u64 = 0;
    let mut best_action = children[0].1.clone();
    let mut best_val = f64::NEG_INFINITY;
    let mut alpha = f64::NEG_INFINITY;
    let beta = f64::INFINITY;
    for (_, a, next_state) in children {
        if node_count >= node_budget || Instant::now() >= deadline {
            break;
        }
        let val = negamax_progress(
            priors, &next_state, depth.saturating_sub(1), alpha, beta, perspective, &mut node_count, node_budget,
            deadline,
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

// ── "Simuliere eine Runde" ───────────────────────────────────────────────────

/// Spielt EINE volle Runde durch (Drafting -- `drafting_actions`/
/// `apply_drafting` decken Kuppelstapel-Züge `DrawStackPeek`/`DrawStack`
/// bereits mit ab, kein Sonderfall nötig -- bis Tiling), ausgehend von
/// einem Runde-START-Zustand (Ergebnis eines Chance-Node-Samples), bis zum
/// nächsten Runde-END-Pseudo-Terminal. Löst Tiling per bestehendem
/// `resolve_to_pre_chance` (WIEDERVERWENDET, nicht dupliziert).
///
/// Determinisierung: mischt `state.dome_tile_pool` GENAU EINMAL beim
/// Eintritt, vor der ersten Drafting-Entscheidung -- siehe Modul-Kommentar.
pub(crate) fn simulate_one_round<R: Rng + ?Sized>(
    priors: impl Fn(&GameState) -> Vec<(Action, f32)> + Copy,
    round_start_state: &GameState,
    overall_deadline: Instant,
    rng: &mut R,
) -> Option<PreChanceState> {
    if round_start_state.phase != Phase::Drafting {
        return None;
    }
    let mut game = Game { state: round_start_state.clone() };
    game.state.dome_tile_pool.shuffle(rng);
    let mut guard = 0u32;
    while game.state.phase == Phase::Drafting {
        guard += 1;
        if guard > 300 || Instant::now() >= overall_deadline {
            return None;
        }
        let action = choose_drafting_action_pruned(
            priors,
            &game.state,
            POLICY_DEPTH,
            POLICY_NODE_BUDGET,
            POLICY_TIME_BUDGET_PER_DECISION,
        )?;
        game.apply_drafting(&action).ok()?;
    }
    round_transition::resolve_to_pre_chance(&game.state)
}

// ── Rekursive Evaluatoren ─────────────────────────────────────────────────────

/// Basisfall-nächster Schritt: simuliert Runde 4, sampelt DANN den 4→5-
/// Übergang genau EINMAL, bewertet über den bestehenden Runde-5-Freebie
/// (`round5::exact_round5_outcome`, exakt, kein Netz-Rauschen).
pub(crate) fn continue_through_round4<R: Rng + ?Sized>(
    net: &Net,
    round4_start: &GameState,
    rng: &mut R,
) -> [f64; 2] {
    let overall = Instant::now() + ROUND_SIM_TIME_BUDGET;
    match simulate_one_round(
        |s| crate::net_mcts::drafting_action_priors(net, s),
        round4_start,
        overall,
        rng,
    ) {
        Some(pre5) => {
            let deadline = Instant::now() + INNER_SAMPLE_TIME_BUDGET.max(crate::round5::TIME_BUDGET * 2);
            round_transition::sample_round_transition_value(
                &pre5,
                1,
                |s, _rng| crate::round5::exact_round5_outcome(s),
                rng,
                deadline,
            )
        }
        // Graceful Degrade: Simulation fehlgeschlagen/Zeitbudget gerissen --
        // einzelner Netz-Blattwert statt kompletter Ausfall.
        None => crate::net_mcts::net_leaf_eval(net, round4_start),
    }
}

/// Simuliert Runde 3, sampelt den 3→4-Übergang EINMAL, rekursiert in
/// `continue_through_round4`.
pub(crate) fn continue_through_round3<R: Rng + ?Sized>(
    net: &Net,
    round3_start: &GameState,
    rng: &mut R,
) -> [f64; 2] {
    let overall = Instant::now() + ROUND_SIM_TIME_BUDGET;
    match simulate_one_round(
        |s| crate::net_mcts::drafting_action_priors(net, s),
        round3_start,
        overall,
        rng,
    ) {
        Some(pre4) => {
            let deadline = Instant::now() + INNER_SAMPLE_TIME_BUDGET;
            round_transition::sample_round_transition_value(
                &pre4,
                1,
                |s, rng| continue_through_round4(net, s, rng),
                rng,
                deadline,
            )
        }
        None => crate::net_mcts::net_leaf_eval(net, round3_start),
    }
}

/// Simuliert Runde 2, sampelt den 2→3-Übergang EINMAL, rekursiert in
/// `continue_through_round3`.
pub(crate) fn continue_through_round2<R: Rng + ?Sized>(
    net: &Net,
    round2_start: &GameState,
    rng: &mut R,
) -> [f64; 2] {
    let overall = Instant::now() + ROUND_SIM_TIME_BUDGET;
    match simulate_one_round(
        |s| crate::net_mcts::drafting_action_priors(net, s),
        round2_start,
        overall,
        rng,
    ) {
        Some(pre3) => {
            let deadline = Instant::now() + INNER_SAMPLE_TIME_BUDGET;
            round_transition::sample_round_transition_value(
                &pre3,
                1,
                |s, rng| continue_through_round3(net, s, rng),
                rng,
                deadline,
            )
        }
        None => crate::net_mcts::net_leaf_eval(net, round2_start),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::round_transition::drive_to_round_start;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    /// Synthetische, uniforme Prior-Closure -- kein Netz nötig. Netzabhängige
    /// Teile (`net_mcts::drafting_action_priors`, `continue_through_round{2,3,4}`
    /// mit echtem `&Net`) haben KEINEN Rust-Unit-Test-Präzedenzfall in diesem
    /// Projekt (kein `Net::load` in irgendeinem `#[cfg(test)]`-Block) --
    /// Verifikation dafür über einen Python-Self-Play-Smoke-Lauf mit einem
    /// echten Modell, nicht hier.
    fn uniform_priors(state: &GameState) -> Vec<(Action, f32)> {
        let actions = crate::game::drafting_actions(state);
        let n = actions.len().max(1) as f32;
        actions.into_iter().map(|a| (a, 1.0 / n)).collect()
    }

    #[test]
    fn choose_drafting_action_pruned_picks_a_legal_move() {
        let state = drive_to_round_start(31, 2);
        let actions = crate::game::drafting_actions(&state);
        let chosen = choose_drafting_action_pruned(
            uniform_priors, &state, POLICY_DEPTH, POLICY_NODE_BUDGET, POLICY_TIME_BUDGET_PER_DECISION,
        )
        .expect("Aktion");
        assert!(actions.contains(&chosen));
    }

    /// Performance-Regressionswächter, analog zu
    /// `round5::choose_action_stays_within_time_budget`.
    #[test]
    fn choose_drafting_action_pruned_stays_within_time_budget() {
        let state = drive_to_round_start(32, 2);
        let t0 = Instant::now();
        let _ = choose_drafting_action_pruned(
            uniform_priors, &state, POLICY_DEPTH, POLICY_NODE_BUDGET, POLICY_TIME_BUDGET_PER_DECISION,
        );
        let elapsed = t0.elapsed();
        assert!(
            elapsed < POLICY_TIME_BUDGET_PER_DECISION * 5,
            "choose_drafting_action_pruned zu langsam: {elapsed:?}"
        );
    }

    #[test]
    fn simulate_one_round_reaches_next_round_start() {
        let state = drive_to_round_start(33, 2);
        let mut rng = StdRng::seed_from_u64(1);
        let deadline = Instant::now() + Duration::from_secs(5);
        let pre = simulate_one_round(uniform_priors, &state, deadline, &mut rng)
            .expect("sollte eine PreChanceState liefern");
        // PreChanceState ist opak (private Felder, andere Datei) -- über die
        // öffentliche API prüfen: ein Sample muss anwendbar sein und Runde 3
        // erreichen.
        let mut rng2 = StdRng::seed_from_u64(2);
        let sample_deadline = Instant::now() + Duration::from_secs(5);
        let mut reached_round: Option<u32> = None;
        crate::round_transition::sample_round_transition_value(
            &pre,
            1,
            |s, _rng| {
                reached_round = Some(s.round_number);
                [0.0, 0.0]
            },
            &mut rng2,
            sample_deadline,
        );
        assert_eq!(reached_round, Some(3));
    }

    /// Kuppelstapel-Determinisierung: `simulate_one_round` mischt
    /// `dome_tile_pool` einmal beim Eintritt (siehe Modul-Kommentar). Da
    /// `choose_drafting_action_pruned` bei GLEICHEM Zustand deterministisch
    /// entscheidet (keine eigene Zufallsquelle), ist die Kuppelstapel-
    /// Mischung die EINZIGE Rauschquelle über verschiedene `rng`-Seeds --
    /// die resultierende Restpool-Reihenfolge (unabhängig davon, ob während
    /// der simulierten Runde tatsächlich gezogen wurde) muss divergieren.
    /// Regressionsschutz analog zu
    /// `round_transition::sampling_produces_genuinely_different_factories`.
    #[test]
    fn simulate_one_round_dome_pool_order_diverges_across_seeds() {
        let state = drive_to_round_start(34, 2);
        let mut seen = std::collections::HashSet::new();
        for seed in 0..8u64 {
            let mut rng = StdRng::seed_from_u64(seed);
            let deadline = Instant::now() + Duration::from_secs(5);
            let Some(pre) = simulate_one_round(uniform_priors, &state, deadline, &mut rng) else {
                continue;
            };
            let mut rng2 = StdRng::seed_from_u64(seed + 1000);
            let sample_deadline = Instant::now() + Duration::from_secs(5);
            let mut sig: Vec<usize> = Vec::new();
            crate::round_transition::sample_round_transition_value(
                &pre,
                1,
                |s, _rng| {
                    sig = s.dome_tile_pool.iter().map(|t| t.tile_id).collect();
                    [0.0, 0.0]
                },
                &mut rng2,
                sample_deadline,
            );
            seen.insert(sig);
        }
        assert!(
            seen.len() > 1,
            "8 Seeds sollten nicht alle dieselbe Kuppelstapel-Restreihenfolge \
             ergeben -- deutet auf ein fehlendes/zu spätes dome_tile_pool-Mischen hin"
        );
    }

    /// Wall-Clock-Regressionswächter für `simulate_one_round` gegen einen
    /// echten (nicht synthetischen) Runde-2-Start-Zustand.
    #[test]
    fn simulate_one_round_stays_within_generous_time_budget() {
        let state = drive_to_round_start(35, 2);
        let mut rng = StdRng::seed_from_u64(9);
        let t0 = Instant::now();
        let deadline = t0 + ROUND_SIM_TIME_BUDGET;
        let _ = simulate_one_round(uniform_priors, &state, deadline, &mut rng);
        let elapsed = t0.elapsed();
        assert!(
            elapsed < ROUND_SIM_TIME_BUDGET * 3,
            "simulate_one_round zu langsam: {elapsed:?} (Budget: {ROUND_SIM_TIME_BUDGET:?})"
        );
    }
}
