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
//! **Gamma-Pruning für rundenendende Geschwister-Kandidaten** (*-Minimax/
//! Star1-Star2-Familie, Ballard 1983): NUR an der WURZEL von
//! `choose_drafting_action_pruned` (nicht rekursiv in `negamax_progress`s
//! tieferer Vorschau -- das würde die vermiedene Kombinatorik doch
//! wieder einführen). Ein Kandidat, der die Runde beendet, wird NICHT mehr
//! per billiger (faktoren-blinder) `leaf_value_progress` bewertet, sondern
//! per echtem, aber knapp gehaltenem Rundenübergangs-Sampling: erst ein
//! kleines Startsample (`N_MIN_ROUND_END`), dann ein Vergleich gegen den
//! bisher besten Kandidaten -- liegt der Kandidat mehr als `GAMMA_MARGIN`
//! Punkte dahinter, wird er verworfen (kein volles Sample verschwendet),
//! sonst mit `N_FULL_ROUND_END` Samples verfeinert. Kosten bleiben dadurch
//! auf die WENIGEN Entscheidungen begrenzt, die tatsächlich rundenendende
//! Kandidaten haben (typischerweise die letzten 1-3 Züge einer simulierten
//! Runde), nicht auf jede der ~15-20 Entscheidungen/Runde.
//!
//! Skalen-Hinweis: `round_end_eval` liefert eine Gewinnwahrscheinlichkeit
//! ([0,1], wie `net_leaf_eval`/`continue_through_roundX`), `negamax_progress`
//! arbeitet auf der Punkte-Differenz-Skala (wie `round5::negamax`) --
//! `denormalize_score` (Inverse von `mcts::normalize_score`) bringt beide
//! auf dieselbe Skala, damit `best_val`/`alpha` in der Wurzel-Schleife
//! konsistent bleiben, OHNE `negamax_progress`s eigene (unveränderte)
//! Alpha-Beta-Rekursion anzufassen.
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
//! **Kalibrierung (Task #71, 2026-07-22)**: alle Zeit-/Sample-Konstanten
//! unten waren ursprünglich NICHT empirisch kalibriert und dienten als
//! PRIMÄRER Cutoff -- dadurch hing die tatsächlich geleistete Sucharbeit
//! (und damit die Label-Qualität von `bootstrap_value_after_rounds`/
//! `round_transition_value`) von der CPU-Last während der Self-Play-
//! Generierung ab: derselbe Seed konnte je nach Systemlast unterschiedlich
//! viel RNG verbrauchen und einen anderen Wert liefern (Determinismus-Bug).
//! Kalibrierlauf: 8 netzgeführte Partien (`v10_best.onnx`, sims=400) auf
//! einer freien lokalen Maschine, instrumentiert mit temporären
//! `eprintln!`-Zählern in `sample_round_transition_value`,
//! `choose_drafting_action_pruned` und `simulate_one_round`. Befund: der
//! Sample-COUNT (`N_SAMPLES_TRAIN_ROUND{1,2,3}`, `N_MIN_ROUND_END`,
//! `N_FULL_ROUND_END`) und der `guard`-Iterationsdeckel in
//! `simulate_one_round` wurden in ALLEN Messungen vollständig erreicht (nie
//! durch die alte Deadline degradiert) -- diese Counts SIND bereits der
//! deterministische Knoten-Deckel, keine Änderung nötig. EINZIGE Ausnahme:
//! `POLICY_NODE_BUDGET` (20.000) war so großzügig bemessen, dass in der
//! Praxis fast immer `POLICY_TIME_BUDGET_PER_DECISION` (15ms) zuerst griff
//! (gemessener `node_count` bei Rückkehr aus `choose_drafting_action_pruned`:
//! Median 13, p90 91, Maximum 336, n=9189 Aufrufe) -- DAS war die tatsächlich
//! lastabhängige Stelle. Jetzt umgedreht: `POLICY_NODE_BUDGET` (klein, vom
//! MEDIAN abgeleitet, nicht vom Maximum) ist der primäre, deterministische
//! Cutoff; alle Zeitbudgets unten sind auf das 3-5-fache des gemessenen
//! Medians/Maximums aufgerundete Not-Deckel, die unter normaler Last nicht
//! mehr greifen sollen. `EXTRA_GAME_TIMEOUT_SECS` entsprechend nachgezogen.
//!
//! **Restbefund, NICHT durch diesen Fix behoben** (End-zu-Ende-Vergleich
//! zweier separater `self_play.py`-Prozesse, gleicher Seed, `--threads 1`):
//! `bootstrap_value_after_rounds`/`sample_round_transition_for_round`
//! liefern INNERHALB EINES Prozesses (siehe Determinismus-Test unten) exakt
//! reproduzierbare Werte, aber ÜBER ZWEI SEPARATE Prozessstarts hinweg eine
//! winzige Restabweichung (~1e-4..1e-3, selbst mit auf 1h aufgeblähten
//! Zeitbudgets zur Kontrolle -- also NICHT wall-clock-bedingt). Ursache
//! vermutlich `tract-onnx`s Forward-Pass selbst (SIMD-/Speicherlayout-
//! abhängige Gleitkomma-Summationsreihenfolge, z.B. durch ASLR), nicht
//! dieses Modul -- eine bereits VOR Task #71 bestehende Eigenschaft, die
//! erst durch den Wegfall des viel größeren wall-clock-Effekts sichtbar
//! wurde. Größenordnung vernachlässigbar gegenüber dem behobenen Effekt
//! (der bis zu ganze Prozentpunkte verschob), aber eine ECHTE Cross-Prozess-
//! Bit-Exaktheit ist damit NICHT erreicht -- separates Thema, nicht Teil
//! dieses Fixes.
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
/// ganze Simulationskette) -- NUR NOCH äußerer Not-Deckel (Task #71, siehe
/// Modul-Kommentar), der Sample-COUNT selbst ist der primäre, deterministische
/// Cutoff. Kalibrierung (2026-07-22, 8 Partien, siehe Modul-Kommentar):
/// gemessene Gesamtlaufzeit je vollständigem Sample-Satz -- Runde 1 (4
/// Samples, je 3 verschachtelte Zwischenrunden): Median 15,04s, Maximum
/// 16,88s; Runde 2 (8 Samples): Median 23,88s, Maximum 32,12s -- ÜBER dem
/// alten 30s-Budget, d.h. der alte Wert wurde in dieser Messung bereits
/// vereinzelt real ausgeschöpft; Runde 3 (16 Samples): Median 24,71s,
/// Maximum 29,44s -- ebenfalls dicht am alten 30s-Budget (kaum Marge). Neu:
/// grosszügig auf ca. das 3-fache des jeweiligen Medians aufgerundet.
// PREREG_deterministic_labels.md §2 Stufe 2 (2026-08-14): Stufe-1-Messung
// (~50 Partien, normale Last, `scratchpad/not_deckel_feuerraten.py`) fand
// echte, wenn auch kleine Feuerraten (`negamax_progress`: 0,047%/0,030%
// der Knoten-Pruefungen) -- die Mechanik ist damit bestaetigt, auch wenn
// DIESE konkreten Sample-/Kandidaten-Deckel in der Stichprobe nie feuerten.
// Alle Wall-Clock-NOT-DECKEL (nicht die PRIMAEREN deterministischen Budgets
// wie POLICY_NODE_BUDGET/POLICY_DEPTH/N_SAMPLES_TRAIN_ROUND*/N_MIN_/
// N_FULL_ROUND_END/der guard=300 in `simulate_one_round` -- die bleiben
// UNVERAENDERT) werden ~10x angehoben ("Ausnahme-Niveau", Auftrag):
// reine Haenger-Versicherung, der aeussere `run_with_watchdog`-Mechanismus
// (self_play.rs) bleibt zusaetzlich bestehen. Bei normaler bis schwerer
// Last soll der Not-Deckel praktisch NIE mehr vor dem jeweiligen primaeren
// Deckel binden -- das war schon vor dieser Anhebung der Median-/p90-Befund
// (siehe Kalibrierungs-Kommentare oben), nur die p99/Ausreisser-Faelle
// unter Last banden zu frueh.
pub const TIME_BUDGET_TRAIN_ROUND1: Duration = Duration::from_secs(450);
pub const TIME_BUDGET_TRAIN_ROUND2: Duration = Duration::from_secs(750);
pub const TIME_BUDGET_TRAIN_ROUND3: Duration = Duration::from_secs(750);

/// Horizont (in Runden) für `bootstrap_value_after_rounds` (Punkt 6,
/// `evaluations/value head tests.txt`) -- wie viele Runden vorausgeschaut
/// wird, bevor per `net_leaf_eval` direkt bewertet wird, statt bis zum
/// echten Spielende zu rekursieren. 2 als erster, ungetesteter Startwert
/// (Kollegen-Vorschlag: "r+1/r+2") -- noch keine Arena-/R²-Validierung,
/// bei Bedarf anpassen.
pub const BOOTSTRAP_HORIZON_ROUNDS: u32 = 2;
// GESCHICHTE (Lehre, nicht mehr aktueller Stand): eine erste Gamma-Pruning-
// Version bewertete rundenendende Kandidaten per VOLLER
// continue_through_roundX-Rekursion statt eines einzelnen Netz-Forward-
// Passes (siehe make_round_end_eval-Kommentar) -- ein Live-Batch lief >2h
// ohne eine einzige Partie fertigzustellen (kombinatorische Explosion durch
// verschachteltes Gamma-Pruning auf jeder Rekursionsebene), musste
// abgebrochen werden. Nach dem Fix (make_round_end_eval nutzt
// net_leaf_eval, EIN Forward-Pass, kein rekursiver Aufruf) NEU GEMESSEN
// (Heuristik-Self-Play + v8c-Labels, end-zu-Ende über
// self_play_games_with_net_labels, 1 Partie, base_sims=40): ~47s/Partie --
// wieder im erwarteten Bereich (vorher ~35s ganz ohne Gamma-Pruning),
// Partie lief vollständig durch (completed=true, Runde 1-4 komplett
// gelabelt, Runde 5 korrekt nicht).

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
pub const EXTRA_GAME_TIMEOUT_SECS: u64 = 600 + 750 + 750 + 450; // Runde4+3+2+1, Worst-Case-Summe -- Stufe-2-Anhebung (~10x) nachgezogen, siehe Nachtrag oben

/// Suchtiefe/-budget der Zwischenrunden-Zugwahl (`choose_drafting_action_pruned`)
/// je Einzelentscheidung -- bewusst deutlich billiger als ein voller
/// Runde-5-Solve (`round5::NODE_BUDGET`=200 Knoten mit teurem Tiling-Solver
/// je Knoten) für NICHT-rundenendende Kandidaten
/// (Fortschritts-Heuristik-Suche, kein Vollsolve).
///
/// Task #71, Determinismus-Fix: `POLICY_NODE_BUDGET` ist jetzt der PRIMÄRE,
/// deterministische Cutoff (vorher 20.000 -- so großzügig, dass laut
/// Kalibrierung fast immer `POLICY_TIME_BUDGET_PER_DECISION` zuerst griff,
/// siehe Modul-Kommentar). Kalibrierung (2026-07-22, 8 Partien, n=9189
/// `choose_drafting_action_pruned`-Aufrufe): `node_count` bei Rückkehr --
/// Median 13, p90 91, Maximum 336. Neu auf ca. 3x Median (nicht Maximum,
/// siehe Nutzer-Vorgabe) gesetzt: 40 -- deckt die typische Entscheidung
/// komfortabel ab, bleibt aber unter dem beobachteten p90/Maximum.
/// `POLICY_TIME_BUDGET_PER_DECISION` ist jetzt NUR NOCH Not-Deckel --
/// grosszügig auf das ~13-fache des alten Werts (15ms) angehoben, damit er
/// unter normaler Last nicht mehr vor dem Knoten-Deckel greift.
/// `POLICY_OVERALL_TIME_BUDGET_PER_DECISION` unten deckt zusätzlich die
/// Gamma-Pruning-Samples ab.
pub const POLICY_DEPTH: u32 = 4;
pub const POLICY_NODE_BUDGET: u64 = 40;
// Stufe-2-Anhebung (~10x, siehe Nachtrag oben) -- DIESER Not-Deckel war der
// in der Stufe-1-Messung tatsaechlich (wenn auch selten) feuernde
// (`negamax_entry`/`negamax_loop`, ueber `heuristic_deadline` unten
// durchgereicht).
pub const POLICY_TIME_BUDGET_PER_DECISION: Duration = Duration::from_millis(2000);
/// Gesamt-Zeitbudget für EINEN `choose_drafting_action_pruned`-Aufruf
/// (alle Geschwister-Kandidaten inkl. Gamma-Pruning-Samples für
/// rundenendende) -- NUR NOCH Not-Deckel (Task #71). Kalibrierung
/// (2026-07-22, dieselben 9189 Aufrufe): Gesamt-Laufzeit je Aufruf --
/// Median 25,9ms, p90 54,3ms, Maximum 2,46s (Ausreißer mit aktivem
/// Gamma-Pruning-Zweig). Neu: grosszügig auf ca. 6x Maximum aufgerundet.
pub const POLICY_OVERALL_TIME_BUDGET_PER_DECISION: Duration = Duration::from_secs(150);

/// Gesamt-Wall-Clock-Sicherheitsnetz für EINE simulierte Runde
/// (~15-20 Entscheidungen, davon typischerweise nur die letzten 1-3 mit
/// rundenendenden -- also Gamma-Pruning-kostenpflichtigen -- Kandidaten).
/// NUR NOCH Not-Deckel (Task #71) -- der primäre, deterministische Cutoff
/// ist der `guard`-Iterationsdeckel (300) in `simulate_one_round` selbst,
/// der laut Kalibrierung (2026-07-22, n=384 simulierte Runden) NIE auch nur
/// annähernd erreicht wurde (gemessen: Median 27, p90 31, Maximum 38
/// Entscheidungen je simulierter Runde -- eine normale Runde hat naturgemäß
/// ~15-40 Halbzüge). Gemessene Gesamtlaufzeit je simulierter Runde: Median
/// 977ms, p90 2,21s, Maximum 4,41s. Neu: ca. 3x Maximum aufgerundet.
pub const ROUND_SIM_TIME_BUDGET: Duration = Duration::from_secs(150);

/// Zeitbudget für den EINEN verschachtelten Chance-Node-Sample-Aufruf
/// (`n_samples = 1`) nach einer simulierten Zwischenrunde. Task #71-Befund:
/// bei `n_samples = 1` prüft `sample_round_transition_value`s Schleife die
/// Deadline nur VOR der (einzigen) Iteration, nie währenddessen -- dieses
/// Budget hatte in der Kalibrierung (2026-07-22, n=416 Aufrufe) daher NIE
/// eine Wirkung (Sample-Count immer exakt 1), obwohl die gemessene
/// tatsächliche Laufzeit der einen (rekursiven) Sample-Auswertung bei
/// Median 160ms, p90 2,19s, Maximum 5,08s lag -- weit über dem alten
/// 300ms-Wert. Der alte Wert war also faktisch wirkungslos, nicht falsch
/// kalibriert. Neu: ehrlicher Not-Deckel, ca. 4x Maximum aufgerundet (rein
/// defensiv -- die eigentliche Begrenzung kommt jetzt aus den
/// Knoten-Deckeln der rekursiven Evaluatoren selbst, s.o.).
pub const INNER_SAMPLE_TIME_BUDGET: Duration = Duration::from_secs(200);

// ── Gamma-Pruning für rundenendende Geschwister-Kandidaten ──────────────────

/// Kleines Startsample für einen rundenendenden Kandidaten -- billig genug,
/// um es für JEDEN solchen Kandidaten zu zahlen, bevor überhaupt entschieden
/// wird, ob sich ein volles Sample lohnt.
pub const N_MIN_ROUND_END: u32 = 2;
/// Volles Sample für einen rundenendenden Kandidaten, der laut Startsample
/// noch konkurrenzfähig ist (siehe `GAMMA_MARGIN`).
pub const N_FULL_ROUND_END: u32 = 6;
/// Marge auf der Punkte-Differenz-Skala (wie `round5.rs`s `player_total`-
/// Werte, NICHT die [0,1]-Gewinnwahrscheinlichkeit) -- ein Kandidat, dessen
/// Startsample-Wert mehr als `GAMMA_MARGIN` unter dem bisher besten liegt,
/// wird ohne volles Sample verworfen.
pub const GAMMA_MARGIN: f64 = 10.0;
/// Zeitbudget für EIN Gamma-Pruning-Sample (Start- oder Vollsample) --
/// deutlich teurer als der Rest der Zwischenrunden-Zugwahl, da hier ein
/// echter (rekursiver) Rundenübergang samplet statt der billigen Heuristik.
/// NUR NOCH Not-Deckel (Task #71) -- der Bewerter hier ist `net_leaf_eval`
/// (EIN Forward-Pass je Sample), der Sample-COUNT (`N_MIN_ROUND_END`/
/// `N_FULL_ROUND_END`) ist bereits der primäre, deterministische Cutoff.
/// Kalibrierung (2026-07-22, n=390 bzw. n=371 Aufrufe): gemessene
/// Laufzeit -- `N_MIN_ROUND_END`=2: Median 0,87ms, Maximum 2,66ms;
/// `N_FULL_ROUND_END`=6: Median 1,96ms, Maximum 4,98ms -- der alte
/// 2s-Wert war bereits ~400x großzügiger als nötig, blieb aber als
/// unbegründet gewählte Zahl stehen. Neu: 500ms (immer noch >100x
/// gemessenes Maximum, aber jetzt als bewusster, dokumentierter Not-Deckel
/// statt einer Zufallszahl).
pub const GAMMA_SAMPLE_TIME_BUDGET: Duration = Duration::from_millis(5000);

// ── Zwischenrunden-Zugwahl ───────────────────────────────────────────────────

/// Wie `round5.rs::leaf_value`, aber mit der Fortschritts-Heuristik
/// (`mcts::player_total`) statt exakter Endwertung -- gültig für JEDE
/// laufende Runde (Kuppelraster nicht eingefroren), nicht nur Runde 5.
fn leaf_value_progress(state: &GameState, perspective: usize) -> f64 {
    crate::mcts::player_total(state, perspective) - crate::mcts::player_total(state, 1 - perspective)
}

/// Inverse von `mcts::normalize_score` -- wandelt eine Gewinnwahrscheinlichkeit
/// ([0,1], wie sie `round_end_eval`/`net_leaf_eval`/`exact_round5_outcome`
/// liefern) zurück auf die Punkte-Differenz-Skala von `leaf_value_progress`/
/// `negamax_progress`, damit Gamma-Pruning-Werte und Fortschritts-Heuristik-
/// Werte in derselben Wurzel-Schleife (`choose_drafting_action_pruned`)
/// vergleichbar bleiben, OHNE `negamax_progress`s eigene Alpha-Beta-Skala
/// anzufassen. `clamp` vermeidet `atanh`-Singularitäten bei p=0/1.
fn denormalize_score(p: f64) -> f64 {
    let clamped = p.clamp(1e-6, 1.0 - 1e-6);
    crate::mcts::VALUE_SCALE * (2.0 * clamped - 1.0).atanh()
}

/// Wie `round5.rs::ordered_children`, aber die Kandidatenliste kommt aus
/// `priors` (Netz-Policy, bereits `POLICY_MASS_CUTOFF`-gekappt/sortiert via
/// `net_mcts::drafting_action_priors`) statt aus ALLEN Legalzügen -- hält
/// die 1-Zug-Vorschau-Kosten klein, bevor überhaupt evaluiert wird.
///
/// BUGFIX (`PREREG_round5_minfix_elo_reset.md` par.1 Punkt 2 /
/// `PREREG_implementation_review_unprimed.md` par.7 Befund 1, zweite
/// Fundstelle, bestaetigt): sortierte bis hierher mit einem als Parameter
/// hereingereichten, WURZELFESTEN `perspective` -- dieselbe Liste wird aber
/// von `negamax_progress` (`:369`/`:373`) an Max- UND Min-Knoten benutzt.
/// `leaf_value_progress(s,p) = player_total(s,p) - player_total(s,1-p)` ist
/// wie `round5.rs::leaf_value` exakt antisymmetrisch
/// (`leaf_value_progress(s,p) = -leaf_value_progress(s,1-p)`) -- an einem
/// Min-Knoten (`state.current_player != perspective`) sortierte die alte
/// Formel darum exakt UMGEKEHRT zur Sicht des Ziehenden: dessen beste
/// Widerlegung stand hinten und wurde von der Kinderschleife
/// (`:387-389`, Budget 40) zuerst abgeschnitten. Fix: der Sortierschluessel
/// ist jetzt KNOTENLOKAL -- immer aus Sicht von `state.current_player`
/// (Vorbild `self_play.rs:3398-3411`). An Max-Knoten
/// (`state.current_player == perspective`) ist das byte-identisch zum alten
/// Verhalten. Die RUECKGABE-Semantik von `negamax_progress`/
/// `leaf_value_progress` bleibt unveraendert in `perspective`-Sicht -- nur
/// diese Sortierung wechselt, der Parameter wird darum nicht mehr gebraucht.
fn ordered_children_pruned(
    priors: impl Fn(&GameState) -> Vec<(Action, f32)>,
    state: &GameState,
) -> Vec<(f64, Action, GameState)> {
    let mover = state.current_player;
    let mut scored: Vec<(f64, Action, GameState)> = priors(state)
        .into_iter()
        .filter_map(|(a, _p)| {
            let mut g = Game { state: state.clone() };
            if g.apply_drafting(&a).is_err() {
                return None;
            }
            let v = leaf_value_progress(&g.state, mover);
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
    // PREREG_deterministic_labels.md §2 Stufe 1: Feuerraten-Diagnose, reine
    // Beobachtung. Isoliert die Deadline von den deterministischen
    // Mit-Bedingungen (terminal/Tiefe/node_budget) -- nur wenn die Deadline
    // die ALLEIN entscheidende Ursache war, zaehlt sie als "Not-Deckel"-Feuer.
    {
        use std::sync::atomic::Ordering;
        let terminal = state.phase != Phase::Drafting || depth_remaining == 0;
        let budget_hit = *node_count >= node_budget;
        let deadline_hit = Instant::now() >= deadline;
        crate::round_transition::NOT_DECKEL_STATS.negamax_entry_checks.fetch_add(1, Ordering::Relaxed);
        if deadline_hit && !terminal && !budget_hit {
            crate::round_transition::NOT_DECKEL_STATS
                .negamax_entry_deadline_fires
                .fetch_add(1, Ordering::Relaxed);
        }
        if terminal || budget_hit || deadline_hit {
            return leaf_value_progress(state, perspective);
        }
    }
    let children = ordered_children_pruned(priors, state);
    if children.is_empty() {
        return leaf_value_progress(state, perspective);
    }
    let maximizing = state.current_player == perspective;
    let mut alpha = alpha_in;
    let mut beta = beta_in;
    let mut best = if maximizing { f64::NEG_INFINITY } else { f64::INFINITY };
    for (_, _a, next_state) in children {
        use std::sync::atomic::Ordering;
        let budget_hit = *node_count >= node_budget;
        let deadline_hit = Instant::now() >= deadline;
        crate::round_transition::NOT_DECKEL_STATS.negamax_loop_checks.fetch_add(1, Ordering::Relaxed);
        if deadline_hit && !budget_hit {
            crate::round_transition::NOT_DECKEL_STATS
                .negamax_loop_deadline_fires
                .fetch_add(1, Ordering::Relaxed);
        }
        if budget_hit || deadline_hit {
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
/// Alpha-Beta, mit Gamma-Pruning für rundenendende Kandidaten (siehe
/// Modul-Kommentar). `round_end_eval(state, n_samples, rng)` bewertet einen
/// rundenendenden Kandidatenzustand per `n_samples`-fachem Rundenübergangs-
/// Sampling (Gewinnwahrscheinlichkeits-Skala) -- von `simulate_one_round`s
/// Aufrufern (`continue_through_round{2,3,4}`) über `make_round_end_eval`
/// gebaut; Tests, denen das egal ist, übergeben eine triviale Closure.
/// `None` außerhalb der Drafting-Phase oder ohne Legalzüge.
///
/// ZWEI Zeitbudgets, nicht eines (per Testlauf gefunden, siehe
/// `POLICY_TIME_BUDGET_PER_DECISION`-Kommentar): `heuristic_time_budget`
/// gilt NUR für `negamax_progress`s Fortschritts-Heuristik-Rekursion
/// (nicht-rundenendende Kandidaten) und bleibt klein, `overall_time_budget`
/// deckt den GESAMTEN Aufruf inkl. Gamma-Pruning-Samples ab.
#[allow(clippy::too_many_arguments)]
pub(crate) fn choose_drafting_action_pruned<R: Rng + ?Sized>(
    priors: impl Fn(&GameState) -> Vec<(Action, f32)> + Copy,
    state: &GameState,
    depth: u32,
    node_budget: u64,
    heuristic_time_budget: Duration,
    overall_time_budget: Duration,
    round_end_eval: impl Fn(&GameState, u32, &mut R) -> [f64; 2] + Copy,
    rng: &mut R,
) -> Option<Action> {
    let perspective = state.current_player;
    let children = ordered_children_pruned(priors, state);
    if children.is_empty() {
        return None;
    }
    if children.len() == 1 {
        return Some(children[0].1.clone());
    }
    let overall_deadline = Instant::now() + overall_time_budget;
    // EINMAL berechnet, nicht pro Kandidat (sonst bekäme jeder nicht-
    // rundenendende Kandidat sein EIGENES frisches `heuristic_time_budget`-
    // Fenster statt eines gemeinsam geteilten -- hätte die Gesamtlaufzeit
    // mit der Kandidatenzahl multipliziert statt sie zu deckeln, exakt der
    // Bug, der beim ersten Testlauf auffiel).
    let heuristic_deadline = std::cmp::min(Instant::now() + heuristic_time_budget, overall_deadline);
    // PREREG_deterministic_labels.md §2 Stufe 2 ("ehrliche Deckel"): der
    // erste (Netz-Policy-)Kandidat ist bereits per `ordered_children_pruned`
    // nach der billigen `leaf_value_progress`-Heuristik sortiert -- schnell,
    // ohne eigenes Wall-Clock-Risiko. Feuert `overall_deadline` (nicht
    // `node_budget`) und bricht die Kandidatenschleife vorzeitig ab, faellt
    // die Wahl auf GENAU DIESEN Kandidaten zurueck, statt das load-abhaengige
    // "bislang beste unter den zufaellig noch geschafften Kandidaten"-
    // Ergebnis zu behalten -- derselbe Not-Deckel liefert dann IMMER
    // denselben, schnellen, deterministischen Zug.
    let default_action = children[0].1.clone();
    let mut node_count: u64 = 0;
    let mut best_action = default_action.clone();
    let mut best_val = f64::NEG_INFINITY;
    let mut alpha = f64::NEG_INFINITY;
    let beta = f64::INFINITY;
    let mut deadline_fired = false;
    for (_, a, next_state) in children {
        // PREREG_deterministic_labels.md §2 Stufe 1: Diagnose, siehe
        // `negamax_progress`-Kommentar fuer die Isolations-Begruendung.
        {
            use std::sync::atomic::Ordering;
            let budget_hit = node_count >= node_budget;
            let deadline_hit = Instant::now() >= overall_deadline;
            crate::round_transition::NOT_DECKEL_STATS.drafting_loop_checks.fetch_add(1, Ordering::Relaxed);
            if deadline_hit && !budget_hit {
                crate::round_transition::NOT_DECKEL_STATS
                    .drafting_loop_deadline_fires
                    .fetch_add(1, Ordering::Relaxed);
                deadline_fired = true;
            }
            if budget_hit || deadline_hit {
                break;
            }
        }
        let val = if next_state.phase != Phase::Drafting {
            // Gamma-Pruning: echtes (aber knapp gehaltenes) Rundenübergangs-
            // Sampling statt der billigen, faktoren-blinden Heuristik --
            // siehe Modul-Kommentar. Eigenes Zeitbudget je Sample
            // (`GAMMA_SAMPLE_TIME_BUDGET`, siehe `make_round_end_eval`),
            // zusätzlich durch `overall_deadline` gedeckelt.
            let quick_p = round_end_eval(&next_state, N_MIN_ROUND_END, rng)[perspective];
            let quick = denormalize_score(quick_p);
            let margin_hit = quick < best_val - GAMMA_MARGIN;
            let deadline_hit = Instant::now() >= overall_deadline;
            {
                use std::sync::atomic::Ordering;
                crate::round_transition::NOT_DECKEL_STATS.gamma_full_checks.fetch_add(1, Ordering::Relaxed);
                if deadline_hit && !margin_hit {
                    crate::round_transition::NOT_DECKEL_STATS
                        .gamma_full_deadline_fires
                        .fetch_add(1, Ordering::Relaxed);
                }
            }
            if margin_hit || deadline_hit {
                quick
            } else {
                let full_p = round_end_eval(&next_state, N_FULL_ROUND_END, rng)[perspective];
                denormalize_score(full_p)
            }
        } else {
            negamax_progress(
                priors, &next_state, depth.saturating_sub(1), alpha, beta, perspective, &mut node_count,
                node_budget, heuristic_deadline,
            )
        };
        if val > best_val {
            best_val = val;
            best_action = a;
        }
        if val > alpha {
            alpha = val;
        }
    }
    if deadline_fired {
        return Some(default_action);
    }
    Some(best_action)
}

// ── "Simuliere eine Runde" ───────────────────────────────────────────────────

/// Baut den `round_end_eval`-Callback für `choose_drafting_action_pruned`s
/// Gamma-Pruning: löst den Rundenübergang ab einem rundenendenden
/// Kandidatenzustand deterministisch bis zum Chance-Knoten vor
/// (`resolve_to_pre_chance`, wiederverwendet), sampelt ihn `n`-fach und
/// bewertet jedes Sample per EINEM Netz-Forward-Pass (`net_leaf_eval`,
/// ~0,2ms) -- bewusst NICHT über eine rekursive `continue_through_roundX`-
/// Kontinuation.
///
/// BUGFIX, live beobachtet (2+ Stunden ohne fertigzuwerden, Prozess
/// letztlich abgebrochen): eine frühere Version bewertete hier per voller
/// `continue_through_roundX`-Rekursion -- jeder rundenendende Kandidat, den
/// Gamma-Pruning antrifft, hätte damit eine KOMPLETTE verschachtelte
/// `simulate_one_round` (mit ihrem EIGENEN Gamma-Pruning, bis zu 8
/// Auswertungen je Kandidat) ausgelöst, rekursiv bis Runde 5 -- genau die
/// kombinatorische Explosion, die das "1 Sample je äußerer Ebene"-Design
/// eigentlich vermeiden sollte. Jede Ebene berechnete zudem ihr eigenes
/// Zeitbudget frisch ab `Instant::now()`, unabhängig davon, wie viel vom
/// Budget der aufrufenden Ebene bereits verbraucht war -- nichts deckelte
/// die Gesamtzeit wirklich. Die tiefe, korrekt additive Rekursion bleibt
/// unverändert in `continue_through_round{2,3,4}` selbst (dort EIN Sample,
/// EINE Rekursionsebene tiefer) -- Gamma-Pruning innerhalb einer
/// SIMULIERTEN Runde ist ein separates, bewusst BILLIG gehaltenes Anliegen:
/// eine brauchbare, aber begrenzte Zugwahl treffen, nicht das finale
/// Trainingsziel konstruieren.
///
/// `[0.5, 0.5]`-Fallback, falls der Zustand wider Erwarten nicht auflösbar
/// ist (sollte durch die `phase != Drafting`-Prüfung des Aufrufers nie
/// vorkommen).
fn make_round_end_eval<R: Rng + ?Sized>(net: &Net) -> impl Fn(&GameState, u32, &mut R) -> [f64; 2] + Copy + '_ {
    move |s: &GameState, n: u32, rng: &mut R| match round_transition::resolve_to_pre_chance(s) {
        Some(pre) => {
            let deadline = Instant::now() + GAMMA_SAMPLE_TIME_BUDGET;
            round_transition::sample_round_transition_value(
                &pre,
                n,
                |s2, _rng| crate::net_mcts::net_leaf_eval(net, s2),
                rng,
                deadline,
            )
        }
        None => [0.5, 0.5],
    }
}

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
    round_end_eval: impl Fn(&GameState, u32, &mut R) -> [f64; 2] + Copy,
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
        // PREREG_deterministic_labels.md §2 Stufe 1: Diagnose. `guard`
        // ist der deterministische Iterationsdeckel (Kontext-Zahl, KEIN
        // Not-Deckel) -- separat gezaehlt, damit die Deadline-Feuerrate
        // nicht durch einen (in der Praxis nie erreichten, siehe Modul-
        // Kommentar) Guard-Treffer verwaessert wird.
        {
            use std::sync::atomic::Ordering;
            let guard_hit = guard > 300;
            let deadline_hit = Instant::now() >= overall_deadline;
            crate::round_transition::NOT_DECKEL_STATS.simulate_round_checks.fetch_add(1, Ordering::Relaxed);
            if guard_hit {
                crate::round_transition::NOT_DECKEL_STATS
                    .simulate_round_guard_fires
                    .fetch_add(1, Ordering::Relaxed);
            } else if deadline_hit {
                crate::round_transition::NOT_DECKEL_STATS
                    .simulate_round_deadline_fires
                    .fetch_add(1, Ordering::Relaxed);
            }
        }
        if guard > 300 || Instant::now() >= overall_deadline {
            return None;
        }
        let action = choose_drafting_action_pruned(
            priors,
            &game.state,
            POLICY_DEPTH,
            POLICY_NODE_BUDGET,
            POLICY_TIME_BUDGET_PER_DECISION,
            POLICY_OVERALL_TIME_BUDGET_PER_DECISION,
            round_end_eval,
            rng,
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
    // PREREG_ownership_corpus.md §3 Punkt 6: Label-Rollout, keine
    // Partie-Streuung (siehe `with_game_scatter_suspended`-Doku).
    crate::net_mcts::with_game_scatter_suspended(|| {
    let overall = Instant::now() + ROUND_SIM_TIME_BUDGET;
    match simulate_one_round(
        |s| crate::net_mcts::drafting_action_priors(net, s),
        round4_start,
        make_round_end_eval(net),
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
    })
}

/// Simuliert Runde 3, sampelt den 3→4-Übergang EINMAL, rekursiert in
/// `continue_through_round4`.
pub(crate) fn continue_through_round3<R: Rng + ?Sized>(
    net: &Net,
    round3_start: &GameState,
    rng: &mut R,
) -> [f64; 2] {
    // PREREG_ownership_corpus.md §3 Punkt 6: Label-Rollout, keine
    // Partie-Streuung (siehe `with_game_scatter_suspended`-Doku).
    crate::net_mcts::with_game_scatter_suspended(|| {
    let overall = Instant::now() + ROUND_SIM_TIME_BUDGET;
    match simulate_one_round(
        |s| crate::net_mcts::drafting_action_priors(net, s),
        round3_start,
        make_round_end_eval(net),
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
    })
}

/// Simuliert Runde 2, sampelt den 2→3-Übergang EINMAL, rekursiert in
/// `continue_through_round3`.
pub(crate) fn continue_through_round2<R: Rng + ?Sized>(
    net: &Net,
    round2_start: &GameState,
    rng: &mut R,
) -> [f64; 2] {
    // PREREG_ownership_corpus.md §3 Punkt 6: Label-Rollout, keine
    // Partie-Streuung (siehe `with_game_scatter_suspended`-Doku).
    crate::net_mcts::with_game_scatter_suspended(|| {
    let overall = Instant::now() + ROUND_SIM_TIME_BUDGET;
    match simulate_one_round(
        |s| crate::net_mcts::drafting_action_priors(net, s),
        round2_start,
        make_round_end_eval(net),
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
    })
}

/// TD-Bootstrap-Ziel (`evaluations/value head tests.txt`, Punkt 6): anders
/// als `continue_through_round{2,3,4}` (die bis zum ECHTEN Spielende
/// rekursieren -- dasselbe Ziel wie das Endergebnis selbst, nur an jedem
/// Uebergang variance-reduziert gemittelt) bewertet diese Funktion NUR
/// `horizon_rounds` Runden voraus, dann DIREKT per `net_leaf_eval`.
/// Begruendung: der Noise-Floor-Test (STATUS.md, 2026-07-20/21) zeigt fuer
/// Runde 1 einen praktisch nicht von Null unterscheidbaren Deckel fuers
/// EndergebnisZiel -- das ist eine Eigenschaft der Zielgroesse selbst
/// ("wer gewinnt das GANZE Spiel"), keine Frage der Mittelungstechnik.
/// Die Runde-fuer-Runde-R²-Tabelle zeigt aber einen deutlich hoeheren
/// Deckel fuer NAHE Runden (Runde 4: 0.42, Runde 5: 0.62) -- ein kurzer
/// Bootstrap-Horizont zielt auf genau diese hoehere Decke statt auf die
/// niedrige des vollen Spielausgangs. EIN Sample je Rundenuebergang
/// (keine Mittelung ueber mehrere Neubefuellungen wie bei den
/// `continue_through_roundN`-Funktionen) -- das Ziel ist ein kurzer,
/// billiger Horizont, keine variance-reduzierte Vollsimulation.
/// `horizon_rounds=1`: bewertet direkt den Rundenuebergangs-Zustand
/// (EINE Neubefuellung gezogen, noch kein Zug in der neuen Runde).
/// `horizon_rounds=2`: simuliert zusaetzlich die neue Runde komplett
/// (netzgefuehrt) und bewertet erst am UEBERNAECHSTEN Uebergang. `[0.5,
/// 0.5]`-Fallback, falls die anfaengliche Neubefuellungs-Stichprobe wider
/// Erwarten fehlschlaegt (Zeitbudget/Deadline).
pub(crate) fn bootstrap_value_after_rounds<R: Rng + ?Sized>(
    pre: &PreChanceState,
    net: &Net,
    horizon_rounds: u32,
    rng: &mut R,
) -> [f64; 2] {
    // Task #32 (`profiling.rs`-Modulkopf "Task #32"): Haupteinstiegspunkt der
    // "bootstrap_value"-Kategorie -- ruft INTERN `Net::eval*` auf
    // (`net_leaf_eval`/`drafting_action_priors`), die daraus resultierende
    // Verschachtelung mit "net_inference" wird dort ueber
    // `net_inference_inside_bootstrap_ns` getrennt ausgewiesen.
    crate::profiling::selfplay_profile::timed(crate::profiling::selfplay_profile::SelfplayCat::BootstrapValue, || {
    // PREREG_ownership_corpus.md §3 Punkt 6: Label-Rollout, keine
    // Partie-Streuung (siehe `with_game_scatter_suspended`-Doku).
    crate::net_mcts::with_game_scatter_suspended(|| {
    let mut captured: Option<GameState> = None;
    let deadline0 = Instant::now() + INNER_SAMPLE_TIME_BUDGET;
    round_transition::sample_round_transition_value(
        pre,
        1,
        |s, _rng| {
            captured = Some(s.clone());
            [0.0, 0.0] // Rueckgabewert irrelevant -- nur der Seiteneffekt (captured) zaehlt.
        },
        rng,
        deadline0,
    );
    let Some(mut state) = captured else {
        return [0.5, 0.5];
    };
    for _ in 1..horizon_rounds {
        if state.phase != Phase::Drafting {
            break;
        }
        let overall = Instant::now() + ROUND_SIM_TIME_BUDGET;
        let Some(next_pre) = simulate_one_round(
            |s| crate::net_mcts::drafting_action_priors(net, s),
            &state,
            make_round_end_eval(net),
            overall,
            rng,
        ) else {
            break;
        };
        let mut next_captured: Option<GameState> = None;
        let deadline = Instant::now() + INNER_SAMPLE_TIME_BUDGET;
        round_transition::sample_round_transition_value(
            &next_pre,
            1,
            |s, _rng| {
                next_captured = Some(s.clone());
                [0.0, 0.0]
            },
            rng,
            deadline,
        );
        match next_captured {
            Some(s) => state = s,
            None => break,
        }
    }
    crate::net_mcts::net_leaf_eval(net, &state)
    })
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::round_transition::drive_to_round_start;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    /// `denormalize_score` muss exakt die Inverse von `mcts::normalize_score`
    /// sein -- sonst wären Gamma-Pruning-Werte (Gewinnwahrscheinlichkeits-
    /// Skala) und Fortschritts-Heuristik-Werte (Punkte-Differenz-Skala) in
    /// derselben Wurzel-Schleife nicht mehr vergleichbar.
    #[test]
    fn denormalize_score_is_the_inverse_of_normalize_score() {
        for raw in [-80.0, -12.5, -1.0, 0.0, 1.0, 12.5, 80.0] {
            let p = crate::mcts::normalize_score(raw);
            let back = denormalize_score(p);
            assert!(
                (back - raw).abs() < 1e-6,
                "denormalize_score(normalize_score({raw})) = {back}, erwartet ~{raw}"
            );
        }
    }

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

    /// Triviale `round_end_eval`-Closure für Tests, denen die Qualität der
    /// Gamma-Pruning-Bewertung egal ist (nur `choose_drafting_action_pruned`s/
    /// `simulate_one_round`s Kontrollfluss wird geprüft, nicht die Netz-
    /// Rundenübergangs-Bewertung selbst -- die hat ohnehin keinen Rust-Test-
    /// Präzedenzfall, siehe `uniform_priors`-Kommentar).
    fn trivial_round_end_eval(_s: &GameState, _n: u32, _rng: &mut StdRng) -> [f64; 2] {
        [0.5, 0.5]
    }

    /// Min-Knoten-Regressionstest fuer den Sortier-Fix, zweite Fundstelle
    /// (analog `round5::ordered_children_puts_the_movers_best_reply_first_at_a_min_node`,
    /// `PREREG_round5_minfix_elo_reset.md` par.1 Punkt 2 /
    /// `PREREG_implementation_review_unprimed.md` par.7 Befund 1).
    /// `ordered_children_pruned` sortiert seit dem Fix immer knotenlokal
    /// (aus Sicht von `state.current_player`). An einem MIN-Knoten -- hier
    /// simuliert durch eine gedachte Wurzel-Perspektive
    /// `1 - state.current_player`, so wie `negamax_progress` ihn an einem
    /// Min-Knoten saehe -- muss die fuer den ZIEHENDEN beste Widerlegung an
    /// Position 0 stehen, nicht die aus Sicht der (gedachten) Wurzel beste.
    #[test]
    fn ordered_children_pruned_puts_the_movers_best_reply_first_at_a_min_node() {
        let mut found = false;
        for seed in 60u64..110 {
            let state = drive_to_round_start(seed, 2);
            let mover = state.current_player;
            let root_perspective = 1 - mover;
            let children = ordered_children_pruned(uniform_priors, &state);
            if children.len() < 2 {
                continue;
            }
            let max_v = children.iter().map(|(v, _, _)| *v).fold(f64::NEG_INFINITY, f64::max);
            let min_v = children.iter().map(|(v, _, _)| *v).fold(f64::INFINITY, f64::min);
            if (max_v - min_v).abs() < 1e-9 {
                continue; // kein Unterschied zwischen den Kandidaten -- naechster Seed
            }
            found = true;

            // Referenz: bester Zug FUER DEN ZIEHENDEN, unabhaengig von
            // `ordered_children_pruned` direkt ueber `leaf_value_progress`
            // nachgerechnet.
            let mut expected_action: Option<&Action> = None;
            let mut expected_v = f64::NEG_INFINITY;
            for (_, a, next_state) in &children {
                let v = leaf_value_progress(next_state, mover);
                if v > expected_v {
                    expected_v = v;
                    expected_action = Some(a);
                }
            }
            assert_eq!(
                &children[0].1,
                expected_action.expect("mind. ein Kandidat"),
                "seed={seed}: Position 0 muss die fuer den ZIEHENDEN beste Widerlegung sein"
            );

            // Gegenprobe, dass der Fix hier ueberhaupt etwas aendert: mit der
            // ALTEN, wurzelfesten Formel (`leaf_value_progress(s, root_perspective)`)
            // waere an diesem Min-Knoten ein ANDERER Kandidat das Optimum
            // gewesen als der fuer den Ziehenden tatsaechlich beste
            // (`leaf_value_progress` ist exakt antisymmetrisch, die alte
            // Formel bewertet also strikt gegenlaeufig zur neuen). Kein
            // Vergleich gegen `children.last()`: bei einem Gleichstand
            // mehrerer Kandidaten am unteren Ende waere die Position dort
            // nicht eindeutig, das Optimum unter der alten Formel ist es aber.
            let mut old_best_action: Option<&Action> = None;
            let mut old_best_v = f64::NEG_INFINITY;
            for (_, a, next_state) in &children {
                let v = leaf_value_progress(next_state, root_perspective);
                if v > old_best_v {
                    old_best_v = v;
                    old_best_action = Some(a);
                }
            }
            assert_ne!(
                &children[0].1,
                old_best_action.expect("mind. ein Kandidat"),
                "seed={seed}: alte und neue Sortierung waehlten denselben ersten Kandidaten -- Test waere wertlos"
            );
        }
        assert!(found, "kein Seed mit >=2 unterschiedlich bewerteten Kandidaten gefunden -- Testaufbau pruefen");
    }

    /// Max-Knoten-Gegenprobe: an einem Max-Knoten (`state.current_player ==
    /// Wurzel-Perspektive`) war der alte, wurzelfeste Sortierschluessel
    /// bereits identisch zum neuen knotenlokalen Schluessel -- die
    /// Reihenfolge nach dem Fix muss darum exakt der manuell mit der ALTEN
    /// Formel (`perspective = state.current_player`) nachgerechneten
    /// entsprechen.
    #[test]
    fn ordered_children_pruned_matches_the_old_ordering_at_a_max_node() {
        for seed in [61u64, 62, 63, 64, 65] {
            let state = drive_to_round_start(seed, 2);
            let perspective = state.current_player; // Max-Knoten per Konstruktion
            let children = ordered_children_pruned(uniform_priors, &state);
            let mut expected: Vec<(f64, Action)> = uniform_priors(&state)
                .into_iter()
                .filter_map(|(a, _p)| {
                    let mut g = Game { state: state.clone() };
                    if g.apply_drafting(&a).is_err() {
                        return None;
                    }
                    Some((leaf_value_progress(&g.state, perspective), a))
                })
                .collect();
            expected.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));
            assert_eq!(children.len(), expected.len(), "seed={seed}: Kandidatenzahl weicht ab");
            for (i, ((_, a, _), (_, ea))) in children.iter().zip(expected.iter()).enumerate() {
                assert_eq!(
                    a, ea,
                    "seed={seed} Position {i}: Max-Knoten-Reihenfolge weicht von der alten Formel ab"
                );
            }
        }
    }

    #[test]
    fn choose_drafting_action_pruned_picks_a_legal_move() {
        let state = drive_to_round_start(31, 2);
        let actions = crate::game::drafting_actions(&state);
        let mut rng = StdRng::seed_from_u64(1);
        let chosen = choose_drafting_action_pruned(
            uniform_priors, &state, POLICY_DEPTH, POLICY_NODE_BUDGET, POLICY_TIME_BUDGET_PER_DECISION,
            POLICY_OVERALL_TIME_BUDGET_PER_DECISION, trivial_round_end_eval, &mut rng,
        )
        .expect("Aktion");
        assert!(actions.contains(&chosen));
    }

    /// Performance-Regressionswächter, analog zu
    /// `round5::choose_action_stays_within_time_budget`.
    #[test]
    fn choose_drafting_action_pruned_stays_within_time_budget() {
        let state = drive_to_round_start(32, 2);
        let mut rng = StdRng::seed_from_u64(2);
        let t0 = Instant::now();
        let _ = choose_drafting_action_pruned(
            uniform_priors, &state, POLICY_DEPTH, POLICY_NODE_BUDGET, POLICY_TIME_BUDGET_PER_DECISION,
            POLICY_OVERALL_TIME_BUDGET_PER_DECISION, trivial_round_end_eval, &mut rng,
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
        let pre = simulate_one_round(uniform_priors, &state, trivial_round_end_eval, deadline, &mut rng)
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
            let Some(pre) = simulate_one_round(uniform_priors, &state, trivial_round_end_eval, deadline, &mut rng)
            else {
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
        let _ = simulate_one_round(uniform_priors, &state, trivial_round_end_eval, deadline, &mut rng);
        let elapsed = t0.elapsed();
        assert!(
            elapsed < ROUND_SIM_TIME_BUDGET * 3,
            "simulate_one_round zu langsam: {elapsed:?} (Budget: {ROUND_SIM_TIME_BUDGET:?})"
        );
    }

    /// Task #71, Kern-Regressionsschutz: `POLICY_NODE_BUDGET` muss der
    /// tatsächlich bindende (deterministische) Cutoff sein, nicht mehr die
    /// Zeit -- sonst wäre der ganze Determinismus-Fix wirkungslos. Prüft das
    /// INDIREKT (der Knoten-Zähler selbst ist privat): dieselbe Entscheidung
    /// mit dem regulären `POLICY_TIME_BUDGET_PER_DECISION`/
    /// `POLICY_OVERALL_TIME_BUDGET_PER_DECISION` UND mit künstlich stark
    /// vergrößerten Zeitbudgets (10x) muss exakt dieselbe Aktion liefern --
    /// wenn die Zeit noch der bindende Faktor wäre, dürfte das großzügigere
    /// Budget potenziell tiefer suchen und eine andere Aktion wählen.
    #[test]
    fn choose_drafting_action_pruned_result_is_unaffected_by_extra_time_budget() {
        let state = drive_to_round_start(41, 2);
        let mut rng_a = StdRng::seed_from_u64(4);
        let chosen_normal = choose_drafting_action_pruned(
            uniform_priors, &state, POLICY_DEPTH, POLICY_NODE_BUDGET, POLICY_TIME_BUDGET_PER_DECISION,
            POLICY_OVERALL_TIME_BUDGET_PER_DECISION, trivial_round_end_eval, &mut rng_a,
        );
        let mut rng_b = StdRng::seed_from_u64(4);
        let chosen_generous = choose_drafting_action_pruned(
            uniform_priors, &state, POLICY_DEPTH, POLICY_NODE_BUDGET, POLICY_TIME_BUDGET_PER_DECISION * 10,
            POLICY_OVERALL_TIME_BUDGET_PER_DECISION * 10, trivial_round_end_eval, &mut rng_b,
        );
        assert_eq!(
            chosen_normal, chosen_generous,
            "Ergebnis haengt noch vom Zeitbudget ab -- POLICY_NODE_BUDGET ist nicht der bindende Cutoff"
        );
    }

    /// Task #71, Kern-Regressionsschutz (Determinismus): `bootstrap_value_after_rounds`
    /// muss bei GLEICHEM Seed und GLEICHEM Ausgangszustand zweimal EXAKT
    /// denselben Wert liefern -- vorher (wall-clock-basierte Deadlines als
    /// primärer Cutoff) war das nicht garantiert, weil unter Systemlast
    /// weniger Sucharbeit stattfinden konnte. Braucht ein echtes Netz -- bis
    /// 2026-08-15 zeigte der Pfad auf `alphazero_v10_best.onnx` (existiert
    /// seit dem NUM_ACTIONS-Wechsel nicht mehr) und der Test UEBERSPRANG sich
    /// still: der Kern-Regressionsschutz lief nie. Jetzt: amtierender Champion
    /// + harter Fehler statt Skip (Nutzer-Regel: nie leer gruen).
    #[test]
    fn bootstrap_value_after_rounds_is_deterministic_for_same_seed() {
        let model_path = concat!(env!("CARGO_MANIFEST_DIR"), "/../models/alphazero_v21_2d_brierbest.onnx");
        let net = Net::load_auto(model_path).unwrap_or_else(|e| panic!(
            "{model_path:?} nicht ladbar ({e}) -- Test-Voraussetzung fehlt, der Test darf \
             nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ));
        let leaf = crate::round_transition::drive_to_first_round_end(51);
        let pre = round_transition::resolve_to_pre_chance(&leaf).expect("aufloesbar");

        let mut rng_a = StdRng::seed_from_u64(777);
        let val_a = bootstrap_value_after_rounds(&pre, &net, BOOTSTRAP_HORIZON_ROUNDS, &mut rng_a);
        let mut rng_b = StdRng::seed_from_u64(777);
        let val_b = bootstrap_value_after_rounds(&pre, &net, BOOTSTRAP_HORIZON_ROUNDS, &mut rng_b);

        assert_eq!(
            val_a, val_b,
            "gleicher Seed + gleiche Stellung lieferten unterschiedliche bootstrap_value_after_rounds-Werte \
             ({val_a:?} vs {val_b:?}) -- Determinismus-Fix (Task #71) nicht wirksam"
        );
    }

    /// PREREG_ownership_corpus.md §3 Punkt 6: `bootstrap_value_after_rounds`
    /// (und mit ihr, ueber denselben `net_leaf_eval`-Pfad, `continue_through_
    /// round{2,3,4}`/`round_transition_value`) darf sich NICHT aendern, je
    /// nachdem, ob auf dem aufrufenden Thread eine Partie-Streuung
    /// (`set_game_shaping_weight`, `MOSAIC_WERTUNG_STREUUNG_MAX`) aktiv ist
    /// -- sonst variiert das Trainingsziel rein durch den Partie-Seed-
    /// Wuerfelwurf, ohne Bezug zum Spielausgang (der Befund von Punkt 6:
    /// das Streuungs-Shaping der Suche lief ohne diesen Fix UNGEBREMST in
    /// `net_leaf_eval` und damit in jeden `bootstrap_value`/`round_transition_
    /// value`-Aufrufer, siehe `with_game_scatter_suspended`-Doku in
    /// `net_mcts.rs`). Gleicher Seed, gleiche Ausgangsstellung, EINMAL mit
    /// `Some(1.0)` (maximale Streuung), EINMAL mit `None` (keine) -- muss
    /// bit-identisch sein.
    #[test]
    fn bootstrap_value_after_rounds_ignores_game_scatter() {
        // Fixture-Hinweis wie beim Determinismus-Test oben: bis 2026-08-15
        // v10_best (fehlt) + stiller Skip -- der Test lief nie. Jetzt Champion
        // + harter Fehler (Nutzer-Regel: nie leer gruen).
        let model_path = concat!(env!("CARGO_MANIFEST_DIR"), "/../models/alphazero_v21_2d_brierbest.onnx");
        let net = Net::load_auto(model_path).unwrap_or_else(|e| panic!(
            "{model_path:?} nicht ladbar ({e}) -- Test-Voraussetzung fehlt, der Test darf \
             nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ));
        let leaf = crate::round_transition::drive_to_first_round_end(51);
        let pre = round_transition::resolve_to_pre_chance(&leaf).expect("aufloesbar");
        assert!(
            !leaf.scoring_tile_ids.is_empty(),
            "Testaufbau: Ausgangsstellung ohne Wertungsplatten -- Shaping haette gar keinen Ansatzpunkt"
        );

        crate::net_mcts::set_game_shaping_weight(None);
        let mut rng_off = StdRng::seed_from_u64(4242);
        let val_streuung_aus =
            bootstrap_value_after_rounds(&pre, &net, BOOTSTRAP_HORIZON_ROUNDS, &mut rng_off);

        crate::net_mcts::set_game_shaping_weight(Some(1.0));
        let mut rng_on = StdRng::seed_from_u64(4242);
        let val_streuung_an =
            bootstrap_value_after_rounds(&pre, &net, BOOTSTRAP_HORIZON_ROUNDS, &mut rng_on);
        crate::net_mcts::set_game_shaping_weight(None); // aufraeumen, sonst leckt's in Folgetests

        assert_eq!(
            val_streuung_aus, val_streuung_an,
            "bootstrap_value_after_rounds aenderte sich mit aktiver Partie-Streuung \
             ({val_streuung_aus:?} ohne vs. {val_streuung_an:?} mit) -- Leck aus Punkt 6 nicht behoben"
        );
    }
}
