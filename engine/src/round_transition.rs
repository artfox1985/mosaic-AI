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

use std::time::{Duration, Instant};

use rand::rngs::StdRng;
use rand::seq::SliceRandom;
use rand::Rng;
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
pub const N_SAMPLES_TRAIN: u32 = 24;
/// Zeitbudget für die Trainingsziel-Konstruktion -- großzügiger als
/// `TIME_BUDGET` (Live-Suche), da dieser Pfad nur ~4x je Partie läuft statt
/// potenziell tausendfach je Suche. NICHT empirisch kalibriert (siehe
/// `TIME_BUDGET`-Kommentar) -- vor breitem Einsatz gegen echte Partien prüfen.
pub const TIME_BUDGET_TRAIN: Duration = Duration::from_millis(800);

/// Zeitbudget speziell für die Runde-4→5-Transition (siehe
/// `round5::exact_round5_outcome`, self_play.rs-Aufrufstelle): dort kostet
/// JEDER Sample-Aufruf selbst bis zu `round5::TIME_BUDGET` (150ms, ein
/// voller Alpha-Beta-Solve statt eines ~0,2ms-Netz-Forward-Passes) --
/// `TIME_BUDGET_TRAIN` (800ms) würde die Sample-Zahl auf ~5 statt der vollen
/// `N_SAMPLES_TRAIN`=24 zusammenstutzen. Grosszügig auf 24×150ms+Puffer
/// bemessen -- läuft nur 1x je Partie (nur dieser eine Übergang), daher
/// vertretbar teurer als die anderen drei.
pub const TIME_BUDGET_TRAIN_ROUND4: Duration = Duration::from_secs(5);

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
pub fn sample_round_transition_value<R: Rng + ?Sized>(
    pre: &PreChanceState,
    n_samples: u32,
    mut evaluator: impl FnMut(&GameState, &mut R) -> [f64; 2],
    rng: &mut R,
    deadline: Instant,
) -> [f64; 2] {
    let cap = n_samples.min(MAX_SAMPLES_HARD_CAP);
    let mut sum = [0.0f64; 2];
    let mut n = 0u32;
    for _ in 0..cap {
        if Instant::now() >= deadline {
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
    if n == 0 {
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
