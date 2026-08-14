//! Erwartungswert-Bewertung des Runden-Übergangs (Chance-Node, Fabrik-Neubefüllung).
//!
//! Der Suchbaum (`mcts.rs`/`net_mcts.rs`) läuft bewusst NUR innerhalb einer
//! Runde -- am Rundenende (Phase wechselt von Drafting zu Tiling) wird der
//! Knoten pseudo-terminal per EINEM statischen Aufruf bewertet, nie
//! weitergesucht. Die Fabrik-Neubefüllung der NÄCHSTEN Runde
//! (`state.rs::setup_new_round`/`fill_factories`) ist damit nirgends als
//! echter Zufallsknoten repräsentiert -- der Blattwert muss implizit über
//! die gesamte Verteilung möglicher künftiger Steinzüge mitteln, was ein
//! sehr hochvarianzes Ziel für den Value-Head ist (siehe
//! `archive/STAGE2_TODO_ARCHIVED.md`: "irreduzibles Rauschen im Trainings-
//! Target" als Erklärung für den Val-R²-Plateau bei 0.2-0.3, aktueller
//! Stand in `evaluations/STATUS.md`).
//!
//! Dieses Modul macht die Fabrik-Neubefüllung explizit: `resolve_to_pre_chance`
//! spult einen Runden-End-Zustand deterministisch (kein RNG-Verbrauch,
//! siehe Modul-Kommentar dort) bis unmittelbar vor den EINEN tatsächlich
//! zufälligen Schritt vor (den zweiten/letzten `EndTiling`-Aufruf), und
//! `sample_round_transition_value` sampelt N mögliche Neubefüllungen davon
//! ab, bewertet jede über eine vom Aufrufer übergebene Funktion und mittelt.
//!
//! **Wichtig -- Fabrik-Blindheit der bestehenden statischen Bewerter:**
//! `crate::mcts::player_total` und `crate::round5::player_total_exact` (die
//! DFS-/Heuristik-Bewerter) lesen `state.factories` NIRGENDS -- direkt nach
//! einem Rundenübergang sind die Musterreihen frisch leer, `player_total`
//! liefert für praktisch JEDE gesampelte Neubefüllung denselben Wert. Nur
//! ein Bewerter, der `state.factories` tatsächlich als Eingabe nutzt (das
//! Netz, siehe `features.rs::state_to_features_direct`), kann zwischen
//! Samples überhaupt unterscheiden. Dieses Modul ist daher NUR mit einem
//! netzbasierten Bewerter sinnvoll (Stufe 2/`net_mcts.rs`) -- eine
//! Verdrahtung mit `player_total` in `mcts.rs` (Stufe 1) wäre reiner
//! Mehraufwand ohne Nutzen, siehe Kommentar bei `mcts.rs::evaluate`.

use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, Instant};

use rand::rngs::StdRng;
use rand::seq::SliceRandom;
use rand::Rng;
#[cfg(test)]
use rand::RngExt;
use rand::SeedableRng;

use crate::game::{Game, TilingMove};
use crate::round_end::apply_bonus_chips_with;
use crate::state::{GameState, Phase};
use crate::tiling_solver::{best_first_step_exact, TilingStep};

/// Primäres Zeitbudget je Aufruf -- wie bei `round5.rs` bewusst wall-clock-
/// basiert statt reinem Sample-Budget: die Kosten pro Sample (Klon + Tiling-
/// Wiederholung + Netz-Forward-Pass des Aufrufers) schwanken mit der
/// Brettkomplexität. NICHT empirisch kalibriert -- `round5.rs` hatte einen
/// ersten Kalibrierungsversuch, der auf einem künstlich billigen Testbrett
/// beruhte und in echten Self-Play-Spielen ~75x zu langsam war (siehe dortiger
/// Modul-Kommentar). Vor einer Aktivierung in der Live-Suche (`net_mcts.rs`)
/// MUSS dieser Wert gegen echte, per Self-Play erreichte Rundenenden neu
/// vermessen werden, nicht gegen ein synthetisches Testbrett.
pub const TIME_BUDGET: Duration = Duration::from_millis(50);
/// Zusätzlicher Deckel für den Fall extrem billiger Samples (Sicherheitsnetz,
/// nicht der primäre Cutoff).
pub const MAX_SAMPLES_HARD_CAP: u32 = 64;

/// Anzahl Samples für die Live-Suche (`net_mcts.rs`, Phase 2 -- noch nicht
/// aktiviert). Klein gehalten, da dieser Pfad potenziell sehr oft (einmal je
/// im Suchbaum erzeugtem Runden-End-Knoten) durchlaufen wird.
pub const N_SAMPLES_SEARCH: u32 = 8;
/// Anzahl Samples für die Trainingsziel-Konstruktion (Self-Play,
/// `self_play.rs::play_net_self_play_game`). Läuft nur ~4x je Partie (einmal
/// je echtem Rundenübergang), daher deutlich großzügigeres Budget möglich.
/// Dieser Sample-COUNT ist bereits der eigentliche (deterministische)
/// Knoten-Deckel -- siehe `TIME_BUDGET_TRAIN`-Kommentar (Task #71).
pub const N_SAMPLES_TRAIN: u32 = 24;
/// Task #71, Determinismus-Fix: NUR NOCH äußerer Not-Deckel, nicht mehr der
/// primäre Cutoff. Kalibrierung (2026-07-22, freie lokale Maschine, 8
/// netzgeführte v10_best-Spiele, sims=400, `CALIB_RTV`-Instrumentierung in
/// `sample_round_transition_value`): der Sample-COUNT (`N_SAMPLES_TRAIN`/
/// `N_SAMPLES_TRAIN_ROUND{1,2,3}` in `round_transition_deep.rs`) wurde in
/// ALLEN 8 Spielen IMMER vollständig erreicht (n==cap, nie degradiert) --
/// die Schleife in `sample_round_transition_value` prüft die Deadline nur
/// VOR jeder Sample-Iteration, nicht währenddessen, daher ist der Sample-
/// Count selbst schon der eigentliche (deterministische) Knoten-Deckel.
/// Dieser Pfad (`round_before` außerhalb 1-4, sollte laut Aufrufer nie
/// erreicht werden) nutzt den billigen `net_leaf_eval`-Bewerter (ein
/// Forward-Pass) -- 5s deckt 24 Samples komfortabel ab, selbst unter Last.
// PREREG_deterministic_labels.md §2 Stufe 2 (2026-08-14): ~10x-Anhebung
// ("Ausnahme-Niveau") nach bestaetigter Not-Deckel-Mechanik in der
// Stufe-1-Messung (siehe round_transition_deep.rs-Nachtrag bei
// TIME_BUDGET_TRAIN_ROUND1). Der Sample-COUNT bleibt der primaere Deckel.
pub const TIME_BUDGET_TRAIN: Duration = Duration::from_secs(50);

/// Zeitbudget speziell für die Runde-4→5-Transition (siehe
/// `round5::exact_round5_outcome`, self_play.rs-Aufrufstelle): dort ist
/// JEDER Sample-Aufruf selbst ein voller Alpha-Beta-Solve (statt eines
/// ~0,2ms-Netz-Forward-Passes). Task #71, Determinismus-Fix: NUR NOCH
/// äußerer Not-Deckel (der Sample-COUNT `N_SAMPLES_TRAIN`=24 ist der
/// primäre, deterministische Cutoff -- siehe `TIME_BUDGET_TRAIN`-
/// Kommentar). Historische Kalibrierung des zeit-primären Alt-Stands
/// (2026-07-22, 8 netzgeführte v10_best-Spiele, sims=400): volle
/// 24-Sample-Kette Median 3,83s bei 150ms je Solve → alter Wert 12s.
/// NACHGEZOGEN mit der Knoten-primär-Umstellung von round5.rs
/// (`round5::NODE_BUDGET`=200 statt 150ms-Deadline): ein Solve kostet
/// jetzt stellungsabhängig ~60-900ms (siehe dortige Kalibrierung), Worst
/// Case der Kette also ~24 x 0,9s ~ 21s -- mit dem alten 12s-Deckel wäre
/// die Deadline wieder der bindende, lastabhängige Cutoff geworden und
/// hätte den Determinismus-Gewinn genau hier (dem Runde-4-Label!) wieder
/// zerstört. Neu: ~3x Worst-Case aufgerundet.
pub const TIME_BUDGET_TRAIN_ROUND4: Duration = Duration::from_secs(600);

/// Ein Runden-End-Zustand, deterministisch bis unmittelbar vor den EINEN
/// tatsächlich zufälligen Schritt vorgespult (den `EndTiling`-Aufruf des
/// Spielers, der als zweiter fertig wird -- der DAVOR liegende erste
/// `EndTiling`-Aufruf verbraucht nachweislich kein RNG, siehe
/// `game.rs::end_tiling`: früher Return, sobald `tiling_done[other]` noch
/// `false` ist).
pub struct PreChanceState {
    state: GameState,
    pending_end_tiling_player: usize,
}

impl PreChanceState {
    /// Lesender Zugriff auf den deterministisch vorgespulten Zustand (additiv,
    /// Task `round_transition_resample::autoplay_to_round5_and_resample`: der
    /// PREREG-r4-Pfad braucht genau DIESEN Zustand als Rückgabewert für den
    /// Python-seitigen Konsistenz-Check -- siehe dortige Doku).
    pub fn state(&self) -> &GameState {
        &self.state
    }
}

/// Spult `leaf_state` (Phase muss `Tiling` sein -- ein per `terminal`-Flag
/// erkannter Runden-End-Knoten) deterministisch vor: beide Spieler platzieren
/// per exaktem DFS-Solver (`best_first_step_exact`, dieselbe Politik wie
/// `self_play.rs::resolve_tiling_step`) alle möglichen Steine/Bonuschips,
/// bis nur noch der letzte `EndTiling`-Aufruf fehlt. `None`, falls
/// `leaf_state` nicht in Phase::Tiling ist (defensiv -- sollte durch die
/// `terminal`-Prüfung der Aufrufer nie vorkommen).
pub fn resolve_to_pre_chance(leaf_state: &GameState) -> Option<PreChanceState> {
    if leaf_state.phase != Phase::Tiling {
        return None;
    }
    let mut game = Game { state: leaf_state.clone() };
    // Nachweislich nie konsumiert (siehe PreChanceState-Doc) -- ein fester
    // Seed genügt, hier gibt es keine echte Zufälligkeit zu ziehen.
    let mut unused_rng = StdRng::seed_from_u64(0);
    let mut guard = 0u32;
    loop {
        guard += 1;
        if guard > 500 {
            return None; // Sicherheitsnetz gegen einen unerwarteten Endlos-Fall.
        }
        let pi = game.state.current_player;
        match best_first_step_exact(&game.state, pi) {
            TilingStep::Place(ta) => {
                game.apply_single_tiling(pi, &ta).ok()?;
            }
            TilingStep::Chips { row, chips } => {
                apply_bonus_chips_with(&mut game.state.players[pi], row, &chips);
            }
            TilingStep::End => {
                let other = 1 - pi;
                if game.state.tiling_done[other] {
                    // Das ist der zweite/letzte EndTiling-Aufruf -- hier
                    // aufhören, NICHT anwenden. Der eigentliche Zufalls-
                    // schritt (Fabrik-Neubefüllung) passiert erst darin.
                    return Some(PreChanceState { state: game.state, pending_end_tiling_player: pi });
                }
                game.apply_tiling(&TilingMove::EndTiling { player: pi }, &mut unused_rng).ok()?;
            }
        }
    }
}

/// Sampelt `n_samples` mögliche Fortsetzungen ab `pre` (je einmal den
/// finalen `EndTiling`-Aufruf mit frischem RNG aus `rng` -- das ist der
/// einzige Punkt, an dem `setup_new_round`/`fill_factories` tatsächlich
/// gezogen wird), bewertet jede über `evaluator` und mittelt arithmetisch
/// (korrekter Monte-Carlo-Schätzer, da jedes Sample unter der echten
/// Ziehverteilung entsteht -- keine Gewichtung nötig). Bricht bei
/// `deadline` ab und mittelt über die bis dahin erfolgreich gezogenen
/// Samples; liefert `evaluator(&pre.state)` als Fallback, falls kein
/// einziges Sample vor der Deadline fertig wurde.
///
/// `evaluator` bekommt `rng` als expliziten Parameter (statt es selbst per
/// Closure zu capturen) -- `round_transition_deep.rs`s rekursive Evaluatoren
/// (Runde 1-3, mehrstufiges Sampling) brauchen mutablen Zugriff auf
/// DASSELBE `rng` für ihre eigenen verschachtelten
/// `simulate_one_round`/`sample_round_transition_value`-Aufrufe -- ein
/// Closure, das `rng` per Capture hielte, würde sich mit dem `rng: &mut R`-
/// Parameter dieser Funktion selbst überlappend ausleihen (Borrow-Checker-
/// Konflikt). Bestehende, rng-unabhängige Evaluatoren (`net_leaf_eval`,
/// `round5::exact_round5_outcome`) ignorieren den zweiten Parameter einfach
/// (`|s, _rng| ...`).
/// EINE Zufallsziehung des Rundenuebergangs, als Zustand statt als Bewertung.
///
/// Gleicher Kern wie der Schleifenrumpf von [`sample_round_transition_value`]
/// (Beutel + Bonusplaettchen-Pool neu mischen, dann `EndTiling`), liefert aber
/// den resultierenden Drafting-Zustand zurueck, statt ihn sofort zu bewerten.
///
/// Gebraucht fuer die Validierung der netz-gefuehrten Tiling-Auswahl (Task #20):
/// die Kandidaten-Zustaende stehen in der TILING-Phase, wo `net_search_with_tree`
/// strukturell nichts liefert. Erst nach dem Rundenuebergang ist eine
/// Tiefensuche als Referenz moeglich. Wird derselbe `rng`-Seed fuer alle
/// Kandidaten einer Stellung genutzt, ist der Vergleich GEPAART -- der einzige
/// Unterschied bleibt das Brett.
pub fn advance_one_chance<R: Rng + ?Sized>(
    pre: &PreChanceState,
    rng: &mut R,
) -> Option<GameState> {
    let mut game = Game { state: pre.state.clone() };
    game.state.bag.tiles.shuffle(rng);
    game.state.bonus_chip_pool.shuffle(rng);
    game.apply_tiling(&TilingMove::EndTiling { player: pre.pending_end_tiling_player }, rng)
        .ok()?;
    Some(game.state)
}

// ── Stufe 1, PREREG_deterministic_labels.md §2: Not-Deckel-Feuerraten ───────
// Reine Beobachtung (Diagnose, KEIN Verhaltenseingriff), gleiches Muster wie
// `net_batcher.rs::BatcherStats` (`Relaxed` reicht, kein weiterer Zustand
// haengt kausal an diesen Zahlen). Global statt thread-lokal, weil
// Self-Play viele Partien PARALLEL ueber rayon-Worker laufen laesst -- die
// Feuerrate soll ueber den GESAMTEN Lauf aggregiert werden, nicht je Thread.
// Jede "_checks"-Zaehlung ist EIN Erreichen der jeweiligen Pruefstelle, jede
// "_deadline_fires"-Zaehlung ISOLIERT den Anteil, in dem die WALL-CLOCK-
// Deadline die entscheidende (nicht durch einen ohnehin schon erreichten
// deterministischen Deckel wie `node_budget`/`guard`/Sample-COUNT maskierte)
// Ursache war -- exakt die Unterscheidung, die PREREG_deterministic_labels.md
// §1 zwischen "PRIMAERER, deterministischer Cutoff" (Task #71) und
// "Not-Deckel" (dieser Auftrag) trifft.
#[derive(Default)]
pub struct NotDeckelStats {
    /// `sample_round_transition_value` (hier): je Aufruf.
    pub sample_transition_checks: AtomicU64,
    /// Deadline brach die Sample-Schleife VOR `cap` erreichten Samples ab.
    pub sample_transition_deadline_fires: AtomicU64,
    /// Schwerster Fall: KEIN Sample vor der Deadline fertig -- Fallback ist
    /// `evaluator(&pre.state)`, der UNGESAMPELTE Zustand direkt.
    pub sample_transition_zero_result: AtomicU64,
    /// `round_transition_deep.rs::choose_drafting_action_pruned`s
    /// Kandidatenschleife: je durchlaufenem Kandidaten.
    pub drafting_loop_checks: AtomicU64,
    pub drafting_loop_deadline_fires: AtomicU64,
    /// Dieselbe Funktion, Gamma-Pruning: Voll-Sample uebersprungen, weil
    /// `overall_deadline` erreicht war (isoliert von der eigentlichen
    /// `GAMMA_MARGIN`-Pruning-Entscheidung).
    pub gamma_full_checks: AtomicU64,
    pub gamma_full_deadline_fires: AtomicU64,
    /// `negamax_progress`, Eintritts-Pruefung.
    pub negamax_entry_checks: AtomicU64,
    pub negamax_entry_deadline_fires: AtomicU64,
    /// `negamax_progress`, Schleifen-Pruefung je Kind-Kandidat.
    pub negamax_loop_checks: AtomicU64,
    pub negamax_loop_deadline_fires: AtomicU64,
    /// `simulate_one_round`: je Zug-Entscheidung innerhalb der simulierten
    /// Runde. `_guard_fires` ist der deterministische Iterationsdeckel
    /// (300, Kontext-Zahl, KEIN Not-Deckel), separat von der Deadline.
    pub simulate_round_checks: AtomicU64,
    pub simulate_round_deadline_fires: AtomicU64,
    pub simulate_round_guard_fires: AtomicU64,
}

/// Global fuer die Dauer des Prozesses (ein Self-Play-Lauf = ein Prozess,
/// siehe `self_play.py::_worker_run_chunk`) -- `reset()` VOR einer frischen
/// Messung, `snapshot_json()` danach.
pub static NOT_DECKEL_STATS: NotDeckelStats = NotDeckelStats {
    sample_transition_checks: AtomicU64::new(0),
    sample_transition_deadline_fires: AtomicU64::new(0),
    sample_transition_zero_result: AtomicU64::new(0),
    drafting_loop_checks: AtomicU64::new(0),
    drafting_loop_deadline_fires: AtomicU64::new(0),
    gamma_full_checks: AtomicU64::new(0),
    gamma_full_deadline_fires: AtomicU64::new(0),
    negamax_entry_checks: AtomicU64::new(0),
    negamax_entry_deadline_fires: AtomicU64::new(0),
    negamax_loop_checks: AtomicU64::new(0),
    negamax_loop_deadline_fires: AtomicU64::new(0),
    simulate_round_checks: AtomicU64::new(0),
    simulate_round_deadline_fires: AtomicU64::new(0),
    simulate_round_guard_fires: AtomicU64::new(0),
};

impl NotDeckelStats {
    /// Setzt ALLE Zaehler auf 0 -- fuer eine frische, unkontaminierte Messung
    /// (z.B. nach dem Wheel-Import, vor dem eigentlichen Probe-Lauf).
    pub fn reset(&self) {
        self.sample_transition_checks.store(0, Ordering::Relaxed);
        self.sample_transition_deadline_fires.store(0, Ordering::Relaxed);
        self.sample_transition_zero_result.store(0, Ordering::Relaxed);
        self.drafting_loop_checks.store(0, Ordering::Relaxed);
        self.drafting_loop_deadline_fires.store(0, Ordering::Relaxed);
        self.gamma_full_checks.store(0, Ordering::Relaxed);
        self.gamma_full_deadline_fires.store(0, Ordering::Relaxed);
        self.negamax_entry_checks.store(0, Ordering::Relaxed);
        self.negamax_entry_deadline_fires.store(0, Ordering::Relaxed);
        self.negamax_loop_checks.store(0, Ordering::Relaxed);
        self.negamax_loop_deadline_fires.store(0, Ordering::Relaxed);
        self.simulate_round_checks.store(0, Ordering::Relaxed);
        self.simulate_round_deadline_fires.store(0, Ordering::Relaxed);
        self.simulate_round_guard_fires.store(0, Ordering::Relaxed);
    }

    /// JSON-Schnappschuss (Muster `batcher_diagnostics`) -- Rohzahlen, Raten
    /// rechnet die Python-Seite (vermeidet Div-durch-0-Sonderfaelle hier).
    pub fn snapshot_json(&self) -> serde_json::Value {
        use serde_json::json;
        let g = |c: &AtomicU64| c.load(Ordering::Relaxed);
        json!({
            "sample_transition_checks": g(&self.sample_transition_checks),
            "sample_transition_deadline_fires": g(&self.sample_transition_deadline_fires),
            "sample_transition_zero_result": g(&self.sample_transition_zero_result),
            "drafting_loop_checks": g(&self.drafting_loop_checks),
            "drafting_loop_deadline_fires": g(&self.drafting_loop_deadline_fires),
            "gamma_full_checks": g(&self.gamma_full_checks),
            "gamma_full_deadline_fires": g(&self.gamma_full_deadline_fires),
            "negamax_entry_checks": g(&self.negamax_entry_checks),
            "negamax_entry_deadline_fires": g(&self.negamax_entry_deadline_fires),
            "negamax_loop_checks": g(&self.negamax_loop_checks),
            "negamax_loop_deadline_fires": g(&self.negamax_loop_deadline_fires),
            "simulate_round_checks": g(&self.simulate_round_checks),
            "simulate_round_deadline_fires": g(&self.simulate_round_deadline_fires),
            "simulate_round_guard_fires": g(&self.simulate_round_guard_fires),
        })
    }
}

pub fn sample_round_transition_value<R: Rng + ?Sized>(
    pre: &PreChanceState,
    n_samples: u32,
    mut evaluator: impl FnMut(&GameState, &mut R) -> [f64; 2],
    rng: &mut R,
    deadline: Instant,
) -> [f64; 2] {
    NOT_DECKEL_STATS.sample_transition_checks.fetch_add(1, Ordering::Relaxed);
    let cap = n_samples.min(MAX_SAMPLES_HARD_CAP);
    let mut sum = [0.0f64; 2];
    let mut n = 0u32;
    // PREREG_deterministic_labels.md §2 Stufe 2 ("ehrliche Deckel"): wenn
    // die Deadline VOR `cap` erreichten Samples feuert, wird das Ergebnis
    // NICHT aus dem load-abhaengigen Teil-Mittel gebildet (dessen genaue
    // Zusammensetzung -- wie viele Samples es noch VOR der Deadline schafften
    // -- selbst vom Ausfuehrungstempo abhinge, exakt die zu vermeidende
    // Maschinenabhaengigkeit) -- stattdessen faellt die Funktion GENAUSO auf
    // `evaluator(&pre.state, rng)` zurueck wie im (schon bestehenden)
    // `n == 0`-Fall unten. Ergebnis: entweder das VOLLE `cap`-Mittel (Deadline
    // nie erreicht) oder der EINE, immer gleiche Kurz-Pfad -- nie ein
    // Zwischending, dessen Wert vom Tempo abhaengt.
    let mut deadline_fired = false;
    for _ in 0..cap {
        if Instant::now() >= deadline {
            NOT_DECKEL_STATS.sample_transition_deadline_fires.fetch_add(1, Ordering::Relaxed);
            deadline_fired = true;
            break;
        }
        let mut game = Game { state: pre.state.clone() };
        // `Bag::draw`/`bonus_chip_pool.pop()` ziehen nur vom Anfang/Ende der
        // (jeweils nur EINMAL beim Spielstart gemischten) Vecs -- ohne
        // Neumischen wuerde jedes Sample aus einem Klon desselben, bereits
        // feststehenden Beutels/Plaettchen-Pools exakt dieselbe Reihenfolge
        // ziehen (mit ~65 Steinen im Beutel wird `draw_with_refill` in
        // `fill_factories` auch so gut wie nie den Turm-Refill-Pfad
        // erreichen, der selbst neu mischt). Nutzer-Anstoss: Bonusplaettchen
        // sind GENAUSO ein Zufallsfaktor am Rundenende wie der Beutel --
        // `fill_factories` weist per `bonus_chip_pool.pop()` je Fabrik
        // verdeckt eins zu (`bonus_chip_revealed` bleibt bis zum Leerwerden
        // der Fabrik false), also muss der Pool genauso wie der Beutel neu
        // gemischt werden, sonst zieht jedes Sample dieselbe Zuteilung.
        // Gleiches Muster wie das bestehende Stufe-3-Rollout
        // (`self_play.rs::mean_rollout_diff`, "Determinisierung Weg 1"): das
        // noch UNBEKANNTE wird je Sample frisch ausgewuerfelt, die sichtbare
        // Information (Fabriken/Boards zu diesem Zeitpunkt) bleibt gleich.
        game.state.bag.tiles.shuffle(rng);
        game.state.bonus_chip_pool.shuffle(rng);
        let applied = game
            .apply_tiling(&TilingMove::EndTiling { player: pre.pending_end_tiling_player }, rng)
            .is_ok();
        if !applied {
            continue;
        }
        let v = evaluator(&game.state, rng);
        sum[0] += v[0];
        sum[1] += v[1];
        n += 1;
    }
    if n == 0 || deadline_fired {
        if n == 0 {
            NOT_DECKEL_STATS.sample_transition_zero_result.fetch_add(1, Ordering::Relaxed);
        }
        return evaluator(&pre.state, rng);
    }
    [sum[0] / n as f64, sum[1] / n as f64]
}

/// Treibt Drafting per naiver `actions[0]`-Politik bis zum nächsten
/// Tiling-Leaf (oder Spielende). Ausgelagert aus `drive_to_first_round_end`,
/// damit `drive_to_round_start` (unten) dieselbe Politik auch für
/// Zwischenrunden wiederverwenden kann.
#[cfg(test)]
fn drive_drafting_to_leaf_naive(mut state: GameState) -> GameState {
    let mut guard = 0u32;
    while state.phase == Phase::Drafting {
        guard += 1;
        assert!(guard < 2000, "Drafting endet nicht");
        let actions = crate::game::drafting_actions(&state);
        if actions.is_empty() {
            break;
        }
        let mut game = Game { state };
        game.apply_drafting(&actions[0]).expect("valider Zug");
        state = game.state;
    }
    state
}

/// Baut eine Partie direkt über die Engine nach (bewusst KEIN synthetisches
/// leeres Testbrett, siehe Modul-Kommentar/`round5.rs`-Lehre: ein auf einem
/// künstlichen Brett kalibrierter Test sagt nichts über echte
/// Spielkomplexität aus) und stoppt beim ersten echten Rundenende, damit
/// wir einen typisierten `GameState` bekommen. `pub(crate)` (nicht in
/// `mod tests` verschachtelt), damit `round_transition_deep.rs`s Tests
/// (andere Modul, braucht echte Zustände statt synthetischer Bretter,
/// siehe dortiger Modul-Kommentar) das wiederverwenden können.
#[cfg(test)]
pub(crate) fn drive_to_first_round_end(seed: u64) -> GameState {
    use crate::scoring::sample_valid_scoring_ids;
    use crate::state::setup_new_game;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    let mut rng = StdRng::seed_from_u64(seed);
    let ids = sample_valid_scoring_ids(3, &mut rng);
    let mut state = setup_new_game(["P1".into(), "P2".into()], 0, &mut rng);
    state.scoring_tile_ids = ids;
    for p in state.players.iter_mut() {
        p.start_tile_pending = false;
    }
    drive_drafting_to_leaf_naive(state)
}

/// Treibt eine Partie über `drive_to_first_round_end` hinaus bis zum
/// Drafting-START von `target_round` (>= 2) -- wiederverwendet
/// `resolve_to_pre_chance` für den deterministischen Vorlauf UND (mit einem
/// ECHTEN, verbrauchenden `rng`, nicht dem verbrauchsfreien Trick aus
/// `resolve_to_pre_chance` selbst) den tatsächlichen `EndTiling`-
/// Zufallsschritt, um wirklich in der nächsten Runde anzukommen. Für
/// `round_transition_deep.rs`s Tests (`simulate_one_round`/
/// `continue_through_round{2,3,4}` brauchen echte Runde-2/3/4-Start-
/// Zustände, kein synthetisches Brett).
#[cfg(test)]
pub(crate) fn drive_to_round_start(seed: u64, target_round: u32) -> GameState {
    use rand::rngs::StdRng;
    use rand::seq::SliceRandom;
    use rand::SeedableRng;

    let mut rng = StdRng::seed_from_u64(seed.wrapping_add(0xD00D));
    let mut state = drive_to_first_round_end(seed);
    let mut guard = 0u32;
    while !(state.round_number == target_round && state.phase == Phase::Drafting) {
        guard += 1;
        assert!(guard < 10, "drive_to_round_start: zu viele Runden ohne Ziel");
        assert_eq!(state.phase, Phase::Tiling, "erwarteter Tiling-Leaf vor Rundenübergang");
        let pre = resolve_to_pre_chance(&state).expect("aufloesbar");
        let mut game = Game { state: pre.state.clone() };
        game.state.bag.tiles.shuffle(&mut rng);
        game.state.bonus_chip_pool.shuffle(&mut rng);
        game.apply_tiling(&TilingMove::EndTiling { player: pre.pending_end_tiling_player }, &mut rng)
            .expect("EndTiling sollte gelingen");
        state = game.state;
        if !(state.round_number == target_round && state.phase == Phase::Drafting) {
            state = drive_drafting_to_leaf_naive(state);
        }
    }
    state
}

/// Wie [`drive_to_round_start`], aber bis zum Tiling-LEAF von `target_round`
/// (statt bis zum Drafting-START der FOLGENDEN Runde) -- für Tests, die einen
/// echten "letzter R-N-Record"-Zustand brauchen (Phase::Tiling, VOR dem
/// letzten Rundenübergang, analog zu `drive_to_first_round_end`s
/// Runde-1-Variante). Gebraucht von `round_transition_resample.rs`s
/// Vorwärts-Pfad (`autoplay_to_round5_and_resample`), dessen Eingabe laut
/// PREREG_r4_value_calibration.md genau so ein Zustand ist ("letzter
/// R4-Record ... Regel: phase=='tiling'").
#[cfg(test)]
pub(crate) fn drive_to_round_tiling_leaf(seed: u64, target_round: u32) -> GameState {
    drive_drafting_to_leaf_naive(drive_to_round_start(seed, target_round))
}

/// Spielt eine Partie bis zum ENDE durch und liefert den Endzustand (beide
/// Bretter final) -- dritter Treiber neben [`drive_to_round_start`] und
/// [`drive_to_round_tiling_leaf`], gebraucht von der Plattenkopf-Validierung in
/// `scoring.rs` (Identitaeten und Grundraten gelten auf dem ENDBRETT).
///
/// Drafting laeuft naiv (`drive_drafting_to_leaf_naive`) wie in den anderen
/// Treibern -- fuer die IDENTITAETEN irrelevant, weil sie fuer jedes Brett
/// gelten; fuer GRUNDRATEN ein Vorbehalt, der an der Auswertung vermerkt ist.
#[cfg(test)]
pub(crate) fn drive_to_game_end(seed: u64) -> Option<GameState> {
    use rand::rngs::StdRng;
    use rand::seq::SliceRandom;
    use rand::SeedableRng;

    let mut rng = StdRng::seed_from_u64(seed.wrapping_add(0xE11D));
    let leaf = drive_to_round_tiling_leaf(seed, 5);
    let pre = resolve_to_pre_chance(&leaf)?;
    let mut game = Game { state: pre.state.clone() };
    game.state.bag.tiles.shuffle(&mut rng);
    game.state.bonus_chip_pool.shuffle(&mut rng);
    game.apply_tiling(&TilingMove::EndTiling { player: pre.pending_end_tiling_player }, &mut rng)
        .ok()?;
    Some(game.state)
}

/// Wie [`drive_drafting_to_leaf_naive`], aber mit UNIFORM ZUFAELLIGER Zugwahl
/// statt `actions[0]`. Eigener Treiber, weil der naive seine Determiniertheit
/// behalten muss (`drive_to_round_start` und die Kalibrierungstests bauen
/// darauf) -- und weil "erste legale Aktion" KEIN Zufall ist, sondern die
/// Reihenfolge des Aktionsgenerators systematisch bevorzugt.
#[cfg(test)]
fn drive_drafting_to_leaf_random(mut state: GameState, rng: &mut rand::rngs::StdRng) -> GameState {
    let mut guard = 0u32;
    while state.phase == Phase::Drafting {
        guard += 1;
        assert!(guard < 2000, "Drafting endet nicht");
        let actions = crate::game::drafting_actions(&state);
        if actions.is_empty() {
            break;
        }
        // `random_range` kommt aus `RngExt`, nicht aus `Rng` -- das Modul
        // importierte nur `Rng` (mcts.rs importiert beide).
        let idx = rng.random_range(0..actions.len());
        let pick = actions[idx].clone();
        let mut game = Game { state };
        game.apply_drafting(&pick).expect("valider Zug");
        state = game.state;
    }
    state
}

/// Spielt eine Partie mit UNIFORM ZUFAELLIGEM Drafting bis zum Ende durch --
/// der BODEN-Referenzlauf (Nutzer-Auftrag 2026-08-10): was ohne jede Absicht
/// erreicht wird. Gegenstueck zum Champion-Korpus (IST).
#[cfg(test)]
pub(crate) fn drive_to_game_end_random(seed: u64) -> Option<GameState> {
    use rand::rngs::StdRng;
    use rand::seq::SliceRandom;
    use rand::SeedableRng;

    let mut rng = StdRng::seed_from_u64(seed ^ 0x5EED);
    let mut state = drive_to_first_round_end(seed);
    let mut guard = 0u32;
    loop {
        guard += 1;
        if guard > 12 {
            return None;
        }
        let pre = resolve_to_pre_chance(&state)?;
        let mut game = Game { state: pre.state.clone() };
        game.state.bag.tiles.shuffle(&mut rng);
        game.state.bonus_chip_pool.shuffle(&mut rng);
        game.apply_tiling(&TilingMove::EndTiling { player: pre.pending_end_tiling_player }, &mut rng)
            .ok()?;
        state = game.state;
        if state.phase != Phase::Drafting {
            return Some(state);   // Spielende erreicht
        }
        state = drive_drafting_to_leaf_random(state, &mut rng);
    }
}

/// Drafting-Politik der Referenzlaeufe ([`drive_to_game_end_reference`]).
#[cfg(test)]
#[derive(Debug, Clone, Copy)]
pub(crate) enum ReferenzPolitik {
    /// Uniform zufaellige Wahl aus `drafting_actions` -- policy-freier BODEN.
    Zufall,
    /// Heuristik-MCTS (`mcts::search_drafting_action`, kein Netz) mit `sims`
    /// Simulationen und `DEFAULT_C` -- kompetenter MITTELWERT.
    Heuristik(u32),
}

/// Ein Drafting-Zug nach der gewaehlten Politik. Fallback auf `actions[0]`,
/// wenn die Suche nichts liefert -- genau wie der Produktions-Self-Play-Pfad
/// (`self_play.rs`), damit ein Referenzlauf nicht an einem Suchabbruch haengt.
#[cfg(test)]
fn drive_drafting_to_leaf_policy(
    mut state: GameState,
    politik: ReferenzPolitik,
    rng: &mut rand::rngs::StdRng,
) -> GameState {
    let mut guard = 0u32;
    while state.phase == Phase::Drafting {
        guard += 1;
        assert!(guard < 2000, "Drafting endet nicht");
        let actions = crate::game::drafting_actions(&state);
        if actions.is_empty() {
            break;
        }
        let pick = match politik {
            ReferenzPolitik::Zufall => actions[rng.random_range(0..actions.len())].clone(),
            ReferenzPolitik::Heuristik(sims) => {
                crate::mcts::search_drafting_action(&state, sims, crate::mcts::DEFAULT_C, rng)
                    .unwrap_or_else(|| actions[0].clone())
            }
        };
        let mut game = Game { state };
        game.apply_drafting(&pick).expect("valider Zug");
        state = game.state;
    }
    state
}

/// Spielt eine VOLLSTAENDIGE Partie nach `politik` durch und liefert den
/// Endzustand -- die beiden Referenzlaeufe des Plattenkopf-Auftrags
/// (2026-08-10, Auswertung in `evaluations/PREREG_plate_head.md`).
///
/// WARUM ein eigener Treiber neben [`drive_to_game_end_random`]: jener setzt
/// (ueber `drive_to_first_round_end`) `start_tile_pending = false` und
/// UEBERSPRINGT damit die kostenlose Startkuppel-Platzierung. Nach
/// `docs/engine_manual.md` legt jeder Spieler 1 Startplatte plus in den Runden
/// 1-4 je genau 2 Platten (Runde 5: keine) = 9 Platten, also alle
/// `MAX_DOME_SLOTS`. Ohne Startplatte bleiben es 8 -- ein 2x2-Block des
/// 6x6-Rasters fehlt STRUKTURELL, womit 2 Reihen, 2 Spalten und mindestens
/// eine Diagonale unerreichbar sind. Genau diese Groessen sollen hier gemessen
/// werden; der Treiber muss die Startplatte deshalb legen.
///
/// Die Startplatte waehlt `self_play::choose_start_placement` -- dieselbe fixe
/// Heuristik, die auch der Champion-Korpus benutzt (Self-Play waehlt sie NICHT
/// per Netz, siehe `self_play::start_placement_step`). Damit ist die
/// Startplatten-Verteilung in beiden Referenzlaeufen und im Champion-Korpus
/// identisch und die einzige Differenz ist die DRAFTING-Politik.
#[cfg(test)]
pub(crate) fn drive_to_game_end_reference(seed: u64, politik: ReferenzPolitik) -> Option<GameState> {
    use crate::game::apply_start_placement;
    use crate::scoring::sample_valid_scoring_ids;
    use crate::self_play::choose_start_placement;
    use crate::state::setup_new_game;
    use rand::rngs::StdRng;
    use rand::seq::SliceRandom;
    use rand::SeedableRng;

    // Aufbau-RNG EXAKT wie `drive_to_first_round_end(seed)` (gleicher Seed,
    // gleiche Aufrufreihenfolge) -- damit traegt derselbe `seed` in BEIDEN
    // Referenzlaeufen dieselben Wertungsplatten und dieselbe Startaufstellung,
    // der Vergleich ist gepaart. Zugwahl/Rundenuebergaenge laufen auf einem
    // getrennten RNG.
    let mut setup_rng = StdRng::seed_from_u64(seed);
    let ids = sample_valid_scoring_ids(3, &mut setup_rng);
    let mut state = setup_new_game(["P1".into(), "P2".into()], 0, &mut setup_rng);
    let mut rng = StdRng::seed_from_u64(seed ^ 0xBEEF);
    state.scoring_tile_ids = ids;

    // Startkuppel: Nicht-Startspieler zuerst (die Engine erzwingt die
    // Reihenfolge, siehe `apply_start_placement`).
    let first = state.current_player;
    for pi in [1 - first, first] {
        let (tid, r, c, rot) = choose_start_placement(&state, pi)?;
        apply_start_placement(&mut state, pi, tid, r, c, rot).ok()?;
    }

    state = drive_drafting_to_leaf_policy(state, politik, &mut rng);

    let mut guard = 0u32;
    loop {
        guard += 1;
        if guard > 12 {
            return None;
        }
        let pre = resolve_to_pre_chance(&state)?;
        let mut game = Game { state: pre.state.clone() };
        game.state.bag.tiles.shuffle(&mut rng);
        game.state.bonus_chip_pool.shuffle(&mut rng);
        game.apply_tiling(&TilingMove::EndTiling { player: pre.pending_end_tiling_player }, &mut rng)
            .ok()?;
        state = game.state;
        if state.phase != Phase::Drafting {
            return Some(state); // Spielende erreicht
        }
        state = drive_drafting_to_leaf_policy(state, politik, &mut rng);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::Phase;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    #[test]
    fn resolve_to_pre_chance_stops_before_final_end_tiling() {
        let leaf = drive_to_first_round_end(11);
        assert_eq!(leaf.phase, Phase::Tiling);
        let pre = resolve_to_pre_chance(&leaf).expect("Tiling-Zustand muss aufloesbar sein");
        // Beide Spieler duerfen keine offenen Tiling-Zuege mehr haben --
        // der einzig fehlende Schritt ist der letzte EndTiling.
        for pi in 0..2 {
            let step = best_first_step_exact(&pre.state, pi);
            if pi != pre.pending_end_tiling_player {
                assert!(matches!(step, TilingStep::End), "Spieler {pi} sollte fertig sein");
            }
        }
    }

    #[test]
    fn sampling_produces_genuinely_different_factories() {
        // Ueber die oeffentliche API getestet (nicht die interne Schleife
        // dupliziert) -- ein Evaluator-Closure sammelt die Fabrik-Signatur
        // jedes Samples in ein RefCell<HashSet>. Faengt zwei Fehlerklassen:
        // versehentlicher RNG-Verbrauch in der deterministischen Vorphase
        // UND ein vergessenes Beutel-Neumischen in `sample_round_transition_value`
        // selbst (siehe dortiger Kommentar -- ohne Neumischen zieht jeder Klon
        // des Beutels exakt dieselbe, schon feststehende Reihenfolge).
        let leaf = drive_to_first_round_end(13);
        let pre = resolve_to_pre_chance(&leaf).expect("aufloesbar");
        let mut rng = StdRng::seed_from_u64(99);
        let deadline = Instant::now() + Duration::from_secs(5);
        let seen = std::cell::RefCell::new(std::collections::HashSet::new());
        sample_round_transition_value(
            &pre,
            10,
            |s, _rng| {
                let sig: Vec<String> = s
                    .factories
                    .iter()
                    .flat_map(|f| f.sun_tiles.iter().map(|t| t.value().to_string()))
                    .collect();
                seen.borrow_mut().insert(sig.join(","));
                [0.0, 0.0]
            },
            &mut rng,
            deadline,
        );
        assert!(
            seen.borrow().len() > 1,
            "10 Ziehungen sollten nicht alle identische Fabriken ergeben -- \
             deutet auf versehentlichen RNG-Verbrauch in der deterministischen \
             Vorphase ODER ein fehlendes Beutel-Neumischen je Sample hin"
        );
    }

    #[test]
    fn sampling_produces_genuinely_different_bonus_chips() {
        // Nutzer-Anstoss: Bonusplaettchen sind GENAUSO ein Zufallsfaktor am
        // Rundenende wie der Beutel (`bonus_chip_pool.pop()`, auch nur EINMAL
        // beim Spielstart gemischt) -- eigener Test, analog zur Fabrik-
        // Variante oben, damit ein vergessenes `bonus_chip_pool.shuffle`
        // separat auffaellt statt sich hinter der Beutel-Varianz zu verstecken.
        let leaf = drive_to_first_round_end(13);
        let pre = resolve_to_pre_chance(&leaf).expect("aufloesbar");
        let mut rng = StdRng::seed_from_u64(77);
        let deadline = Instant::now() + Duration::from_secs(5);
        let seen = std::cell::RefCell::new(std::collections::HashSet::new());
        sample_round_transition_value(
            &pre,
            10,
            |s, _rng| {
                let sig: Vec<String> = s
                    .factories
                    .iter()
                    .map(|f| f.bonus_chip.as_ref().map(|c| c.chip_id.to_string()).unwrap_or_default())
                    .collect();
                seen.borrow_mut().insert(sig.join(","));
                [0.0, 0.0]
            },
            &mut rng,
            deadline,
        );
        assert!(
            seen.borrow().len() > 1,
            "10 Ziehungen sollten nicht alle identische Bonusplaettchen-Zuteilung \
             ergeben -- deutet auf ein fehlendes bonus_chip_pool-Neumischen je \
             Sample hin"
        );
    }

    #[test]
    fn averaging_is_plain_arithmetic_mean() {
        let leaf = drive_to_first_round_end(17);
        let pre = resolve_to_pre_chance(&leaf).expect("aufloesbar");
        let mut rng = StdRng::seed_from_u64(5);
        let deadline = Instant::now() + Duration::from_secs(5);
        // Synthetischer Bewerter: liefert je Aufruf einen fortlaufenden Wert,
        // damit der Mittelwert exakt nachrechenbar ist.
        let counter = std::cell::Cell::new(0.0f64);
        let val = sample_round_transition_value(
            &pre,
            4,
            |_s, _rng| {
                let v = counter.get();
                counter.set(v + 1.0);
                [v, v * 2.0]
            },
            &mut rng,
            deadline,
        );
        // 4 Samples liefern 0,1,2,3 bzw. 0,2,4,6 -- Mittelwert 1.5 bzw. 3.0.
        assert!((val[0] - 1.5).abs() < 1e-9);
        assert!((val[1] - 3.0).abs() < 1e-9);
    }

    /// PREREG_deterministic_labels.md §2 Stufe 2 ("ehrliche Deckel"): feuert
    /// die Deadline NACH einigen (aber nicht allen `cap`) erfolgreichen
    /// Samples, darf das Ergebnis NICHT das load-abhaengige Teil-Mittel
    /// dieser wenigen Samples sein (dessen genaue Zusammensetzung vom
    /// Ausfuehrungstempo abhinge) -- es MUSS exakt derselbe Kurz-Pfad-Wert
    /// sein wie im (schon vorher bestehenden) `n == 0`-Fall. Erzwingt echte
    /// Teil-Fertigstellung ueber `thread::sleep` (kein synthetischer
    /// Zaehler-Trick moeglich, da die Deadline selbst wall-clock-basiert
    /// ist) -- grosszuegige Margen (50ms Deadline, 120ms je Sample), um
    /// Flakiness auf einer normal ausgelasteten Test-Maschine auszuschliessen.
    #[test]
    fn deadline_mid_loop_discards_partial_samples_not_just_zero() {
        let leaf = drive_to_first_round_end(29);
        let pre = resolve_to_pre_chance(&leaf).expect("aufloesbar");

        // Referenzwert: derselbe Bewerter, direkt auf `pre.state()` (der
        // Kurz-Pfad-Fallback) angewandt -- KEIN Sampling beteiligt.
        let mut rng_ref = StdRng::seed_from_u64(4242);
        let fallback_val = evaluator_marks_pre_state(pre.state(), &mut rng_ref);
        assert_eq!(fallback_val, [1.0, 1.0], "Testaufbau: Referenzwert unerwartet");

        // Deadline knapp: das erste (langsame) Sample schafft es gerade noch,
        // das zweite nicht mehr -- `n` bleibt zwischen 1 und `cap-1` (nie 0,
        // nie `cap`), genau der bisher UNGETESTETE Zwischenfall.
        let mut rng = StdRng::seed_from_u64(4242);
        let deadline = Instant::now() + Duration::from_millis(50);
        let calls = std::cell::Cell::new(0u32);
        let val = sample_round_transition_value(
            &pre,
            8,
            |s, rng| {
                calls.set(calls.get() + 1);
                std::thread::sleep(Duration::from_millis(120));
                evaluator_marks_pre_state(s, rng)
            },
            &mut rng,
            deadline,
        );
        assert!(
            calls.get() >= 1 && calls.get() < 8,
            "Testaufbau: erwartet einen ECHTEN Teil-Abbruch (1..7 von 8 Samples), \
             bekam {} Aufrufe -- Timing-Margen pruefen",
            calls.get()
        );
        assert_eq!(
            val, fallback_val,
            "Teil-Ergebnis nach {} erfolgreichen Samples war {val:?}, erwartet der \
             Kurz-Pfad-Fallback {fallback_val:?} -- das Ergebnis haengt noch vom \
             Ausfuehrungstempo ab (Stufe-2-Fix nicht wirksam)",
            calls.get()
        );
    }

    /// Hilfsfunktion fuer den Test oben: [1.0, 1.0] auf dem UNVERAENDERTEN
    /// `pre`-Zustand (Fabriken noch nicht neu befuellt), sonst [0.0, 0.0] --
    /// unterscheidet zuverlaessig "direkt auf pre.state() ausgewertet" von
    /// "nach mindestens einem echten Sample (Fabriken neu gemischt/befuellt)
    /// ausgewertet", ohne einen fortlaufenden Zaehler zu brauchen (der bei
    /// EINEM erfolgreichen Sample zufaellig mit dem Fallback-Wert
    /// uebereinstimmen koennte).
    fn evaluator_marks_pre_state<R: Rng + ?Sized>(s: &GameState, _rng: &mut R) -> [f64; 2] {
        let empty_factories = s.factories.iter().all(|f| f.sun_tiles.is_empty());
        if empty_factories {
            [1.0, 1.0]
        } else {
            [0.0, 0.0]
        }
    }

    /// Performance-Regressionswaechter, analog zu
    /// `round5::choose_action_stays_within_time_budget`: darf `TIME_BUDGET`
    /// nur um eine grosszuegige Toleranz ueberschreiten, gemessen an einem
    /// ECHTEN (nicht synthetischen) Rundenende.
    #[test]
    fn sampling_stays_within_time_budget_on_real_state() {
        let leaf = drive_to_first_round_end(23);
        let pre = resolve_to_pre_chance(&leaf).expect("aufloesbar");
        let mut rng = StdRng::seed_from_u64(1);
        let t0 = Instant::now();
        let deadline = t0 + TIME_BUDGET;
        let _ = sample_round_transition_value(&pre, N_SAMPLES_SEARCH, |s, _rng| crate::mcts::evaluate(s, 0), &mut rng, deadline);
        let elapsed = t0.elapsed();
        assert!(
            elapsed < TIME_BUDGET * 3,
            "sample_round_transition_value zu langsam: {:?} (Budget: {:?})",
            elapsed,
            TIME_BUDGET
        );
    }
}
