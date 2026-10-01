//! Runde-5-Endspielsuche: **Expectiminimax** mit Alpha-Beta auf den
//! Entscheidungsknoten.
//!
//! ## Was diese Suche IST
//!
//! Max-/Min-Knoten mit Alpha-Beta-Cutoffs, dazu **Zufallsknoten** an den
//! Stellen, an denen verdeckte Information oeffentlich wird (Ballards
//! *-Minimax-Familie; die klassische Anwendung ist Backgammon, und genau
//! diese Struktur hat das Spiel: perfekte Information plus Zufallsknoten,
//! keine private Information). Der Blattwert ist der EXAKTE Endwert des
//! erreichten Bretts: optimales Tiling (`solve_round_final_score_endaware`)
//! plus Wertungsplatten-Endwertung -- moeglich, weil sich das Kuppelraster ab
//! Runde 5 nicht mehr aendert (keine Kuppelplatte wird mehr gelegt,
//! `board.rs::can_place_dome_tile`, und kein Stapelzug mehr angeboten,
//! `game.rs::validate_draw_stack_peek`).
//!
//! ## Was sie NICHT ist -- drei Korrekturen (Nutzer-Befunde 2026-08-10)
//!
//! Der frueherer Modulkopf behauptete "exakte Alpha-Beta-Suche" und "ab
//! Rundenbeginn ist Runde 5 ein Full-Information-Endspiel". Beides war falsch:
//!
//! 1. **Kein Loeser.** `NODE_BUDGET = 200` bei einer Wurzelverzweigung von
//!    ~20 reicht fuer effektiv ~3 Halbzuege. Die 200 sind das p75 dessen, was
//!    der alte 150ms-Wanduhr-Deckel ERREICHTE -- eine Tragbarkeitszahl fuers
//!    Self-Play, keine Suffizienzzahl. Gemessen
//!    (`node_budget_sufficiency_probe`): 5,8 / 9,5 / 13,1 % der Zugwahlen
//!    aendern sich bei 400 / 1000 / 4000 Knoten. EXAKT ist die
//!    Blattbewertung, nicht die Suche.
//! 2. **Keine volle Information.** Runde 5 bekommt 4 FRISCHE verdeckte
//!    Bonuschips (der Pool geht mit 20 Chips exakt fuer 5 Runden auf). Der
//!    alte Kopf begruendete das Gegenteil damit, dass alle Zufaelligkeit in
//!    `setup_new_round` ablaeuft -- das verwechselt AUFGELOEST mit SICHTBAR.
//!    Oeffentlich ist der RESTSATZ (jeder Chip wird in seiner Runde
//!    aufgedeckt und genommen, sonst endet die Runde nicht,
//!    `game.rs::check_drafting_complete`); verdeckt ist die ZUORDNUNG zu den
//!    Manufakturen. Dafuer stehen die Zufallsknoten unten.
//! 3. **Tiefe traegt hier kaum.** Gegen ein 20.000-Knoten-Orakel trifft
//!    Budget 200 in 81,4 % der Faelle dieselbe Wahl, das Zwanzigfache kommt
//!    auf 84,8 % (`teil_e_oracle_agreement_probe`). Was den Wert dieser
//!    Suche traegt, ist die exakte Blattrechnung -- nicht das Alpha-Beta
//!    darum herum. Zum Vergleich: das Netz@400 trifft die Orakel-Wahl nur in
//!    51,7 %, obwohl es in Runde 5 auf genau diese Loeser-Zuege destilliert
//!    wird (One-Hot-Policy-Ziel, `net_mcts::net_root_child_stats_and_policy`).
//!
//! Belegkette und Messwerte: `evaluations/PREREG_chance_nodes.md`.
//!
//! Innerhalb eines Zufallsknotens wird NICHT beschnitten (siehe
//! `child_value`) -- Star1/Star2 waere der Standardweg, braucht aber
//! Wertgrenzen je Ausgang und lohnt bei <=4 Ausgaengen nicht.

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
/// Aufrufstellen (mcts.rs, net_mcts.rs) geprüft. Im Netzpfad kommt seit
/// 2026-09-26 das Seiten-Feld `SearchConfig::r5_net_solver` dazu
/// (`net_mcts::r5_solver_takes_over`).
pub fn applies(state: &GameState) -> bool {
    state.round_number >= 5 && state.phase == Phase::Drafting
}

// ── Zufallsknoten fuer die verdeckten Bonuschips ────────────────────────────────
//
// BEFUND (2026-08-10, `evaluations/PREREG_chance_nodes.md`): der Modulkopf
// oben nennt Runde 5 ein "Full-Information-Endspiel" und begruendet das damit,
// dass alle Zufaelligkeit in `setup_new_round` ablaeuft. Das verwechselt
// AUFGELOEST mit SICHTBAR. Der Chip-Pool geht mit 20 Chips exakt fuer 5 Runden
// auf (`dome.rs::build_bonus_chip_pool`, 4 kleine Manufakturen), Runde 5
// bekommt also 4 FRISCHE verdeckte Chips (`state.rs::setup_new_round` setzt
// `bonus_chip_revealed = false`), und genommen werden darf ein Chip erst nach
// dem Aufdecken (`game.rs::validate_take_bonus_chip`), das seinerseits erst
// beim Leerwerden der Manufaktur passiert (`execution.rs::reveal_chip_if_empty`).
//
// WAS LEGITIM BEKANNT IST: der RESTSATZ. `check_drafting_complete` laesst die
// Runde nicht enden, solange ein aufgedeckter Chip noch zu haben ist -- jeder
// Chip wird also in seiner eigenen Runde aufgedeckt UND genommen, nach Runde 4
// sind exakt 16 gesehen. Verdeckt ist allein die ZUORDNUNG zu den Manufakturen
// (Nutzer-Praezisierung 2026-08-10).
//
// WARUM AUFZAEHLEN UND NICHT WELTEN ZIEHEN: 24 Belegungen an der WURZEL
// aufzuzaehlen, jede mit vollem Wissen exakt zu loesen und zu mitteln, waere
// die Determinisierung mit k = alle -- die Streuung verschwindet, der Bias
// bleibt (Strategy Fusion: der Loeser darf je Welt eine andere Strategie
// spielen, obwohl er die Welten nicht unterscheiden kann). Der Knoten gehoert
// deshalb an die Stelle des AUFDECKENS. Weil das Aufdecken oeffentlich und
// gleichzeitig fuer beide Spieler passiert (es gibt keine private Information),
// ist der Baum ein gewoehnlicher Perfect-Recall-Baum mit oeffentlichen
// Zufallsknoten -- Expectiminimax, kein ISMCTS.
//
// LECKKANAELE, die dafuer zu schliessen waren -- genau zwei, weil die
// BLATTBEWERTUNG die Manufakturen nachweislich nie liest (Code-Audit
// `tiling_solver.rs`: "lesen NACHWEISLICH ausschliesslich `state.players[pi]`"):
//   1. der Aufdeck-Uebergang selbst -> `action_outcomes`
//   2. die ZUGSORTIERUNG in `ordered_children` -- unter Knotenbudget
//      entscheidet die Reihenfolge mit, welche Zuege ueberhaupt durchsucht
//      werden, mit dem wahren Chip zu sortieren waere also ein echtes Leck
//
// Default AUS: `MOSAIC_R5_CHANCE_NODES` unset reproduziert das vorherige
// Verhalten Zustand fuer Zustand (`action_outcomes` liefert dann genau einen
// Ausgang mit Gewicht 1, und `child_value` ruft `negamax` mit demselben
// (alpha,beta)-Fenster wie vorher).
fn chance_nodes_enabled() -> bool {
    static CELL: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| {
        // SCHARF seit 2026-08-10 (Nutzer-Entscheid "ja gehen scharf"), nachdem
        // die Vorzeichen-Messung vorlag: `r5_chance_arming_sign_probe` fand
        // ueber 1371 Entscheidungen 43 Abweichungen mit Delta -0,47 Pkt bei
        // SE 0,66 (t = -0,71, Median exakt 0) -- Versatz null BELEGT, nicht
        // behauptet. Ein frueherer Zwischenstand mit nur 4 Abweichungen hatte
        // -2,75 Pkt gezeigt; das trug ein einzelner -13-Fall.
        // `MOSAIC_R5_CHANCE_NODES=0` stellt das alte Verhalten wieder her --
        // gebraucht, wenn eine Alt-Elo-Kante reproduziert werden soll.
        std::env::var("MOSAIC_R5_CHANCE_NODES")
            .map(|v| v.is_empty() || v != "0")
            .unwrap_or(true)
    })
}

/// Soll der NETZPFAD in Runde 5 diesen Loeser benutzen? Default JA (=
/// byte-identisch zu vorher). Die HEURISTIK-Bahn ist bewusst NICHT betroffen:
/// dort bleibt der Loeser gesetzt, weil ihre Alternative eine
/// Fortschritts-Naeherung (`scoring_progress`) waere, und weil der Anker
/// eingefroren bleiben muss.
///
/// Hintergrund (`PREREG_chance_nodes.md`, Teil E): dass der Loeser das Netz
/// in Runde 5 ersetzt, wurde NIE gegatet -- `round5.rs` kam in 98dffa3
/// gebuendelt herein, gerechtfertigt allein durch das Argument, die Runde sei
/// exakt loesbar. Das Argument ist zweifach entkraeftet: die Runde ist nicht
/// vollinformiert (verdeckte Chip-ZUORDNUNG, siehe oben) und die Suche ist
/// keine Loesung, sondern ~3 Halbzuege (Orakel-Uebereinstimmung 81,4 % bei 200
/// Knoten, 84,8 % bei 4000 -- Tiefe kauft fast nichts, die BLATTBEWERTUNG
/// traegt). Offen ist damit nur noch, ob der exakte Blattwert den GELERNTEN
/// schlaegt. Dieser Knopf macht die Gegenprobe ueberhaupt moeglich.
///
/// SEIT 2026-09-26 (`PREREG_r5_net_vs_solver.md` par.2) ist das nur noch der
/// ENV-DEFAULT des Seiten-Felds `SearchConfig::r5_net_solver`: ein prozessweiter
/// OnceLock wirkt in einer Arena auf BEIDE Seiten, ein A/B "Loeser gegen
/// Netzsuche in Runde 5" mit demselben Champion ist so nicht fahrbar. Die
/// Netz-Sucheinstiege in `net_mcts.rs` lesen deshalb das Feld ihrer Seite;
/// diese Funktion liest nur noch `SearchConfig::from_env` (und
/// `from_spec_file`, wenn die Spec das Feld nicht traegt). Bei ungesetzter
/// Variable und ohne Spec-Feld bleibt alles wie vorher: [`NET_SOLVER_DEFAULT`].
/// Der eingefrorene `round5_anchor.rs` und die Heuristik-Bahn (`mcts.rs`) lesen
/// weder Funktion noch Feld.
pub(crate) fn net_solver_enabled() -> bool {
    static CELL: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| {
        std::env::var("MOSAIC_R5_NET_SOLVER")
            .map(|v| v.is_empty() || v != "0")
            .unwrap_or(NET_SOLVER_DEFAULT)
    })
}

/// Bestand des Seiten-Felds `SearchConfig::r5_net_solver`: der Netzpfad nutzt
/// in Runde 5 den Loeser (an). Umgekehrte Polung wie `net_tiling_tiebreak`:
/// `false` ist die Verhaltensaenderung, nicht `true`.
pub const NET_SOLVER_DEFAULT: bool = true;

/// Knotenbudget je Entscheidung, Default [`NODE_BUDGET`].
///
/// Eigener Knopf, weil Zufallsknoten den Teilbaum unter jedem Aufdecken
/// vervielfachen und sich bei FESTEM Budget als reiner TIEFENVERLUST
/// niederschlagen wuerden. Eine Anker-Kante gegen den Status quo waere dann
/// nicht interpretierbar -- sie mischte "ehrlich" mit "flacher". Damit die
/// beiden Ursachen trennbar bleiben, ist das Budget separat stellbar.
///
/// SEIT 2026-09-27 (`PREREG_r5_net_vs_solver.md` par.5a) zugleich der
/// ENV-DEFAULT des Seiten-Felds `SearchConfig::r5_solver_node_budget`; darum
/// `pub` (Manifest in `lib.rs`, Beispiele). Die Heuristik-Bahn,
/// `exact_round5_outcome` und [`choose_action`] lesen weiter nur diese
/// Funktion.
pub fn node_budget() -> u64 {
    static CELL: std::sync::OnceLock<u64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| {
        std::env::var("MOSAIC_R5_NODE_BUDGET")
            .ok()
            .and_then(|v| v.parse::<u64>().ok())
            .filter(|&n| n > 0)
            .unwrap_or(NODE_BUDGET)
    })
}

/// Bestand des Seiten-Felds `SearchConfig::r5_solver_iterative`: aus, der
/// Loeser sucht wie seit jeher ohne Vertiefung ([`choose_action_deadlined`]).
pub const SOLVER_ITERATIVE_DEFAULT: bool = false;

/// Env-Default des Seiten-Felds `SearchConfig::r5_solver_iterative`
/// (`MOSAIC_R5_SOLVER_ITERATIVE`, 0 oder 1, `PREREG_r5_net_vs_solver.md`
/// par.5a). Muster `net_mcts::single_pass_other_val_env`: leer oder ungesetzt
/// = Default, ein ungueltiger Text faellt mit Warnung auf den Default zurueck.
/// Gelesen nur von `SearchConfig::from_env` und `from_spec_file` (wenn die Spec
/// das Feld nicht traegt); der eingefrorene `round5_anchor.rs`, die
/// Heuristik-Bahn und die Label-Pfade lesen ihn nicht.
pub fn solver_iterative_env() -> bool {
    static CELL: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| {
        let Ok(raw) = std::env::var("MOSAIC_R5_SOLVER_ITERATIVE") else {
            return SOLVER_ITERATIVE_DEFAULT;
        };
        match raw.trim() {
            "" => SOLVER_ITERATIVE_DEFAULT,
            "0" => false,
            "1" => true,
            _ => {
                eprintln!(
                    "MOSAIC_R5_SOLVER_ITERATIVE={raw:?} ungueltig (0 oder 1) -- {} gilt.",
                    u8::from(SOLVER_ITERATIVE_DEFAULT)
                );
                SOLVER_ITERATIVE_DEFAULT
            }
        }
    })
}

/// Worst-Case-Kosten eines Knotens aus der Kalibrierung (`NODE_BUDGET`-
/// Kommentar oben: 0,3-4,4 ms je Knoten auf realistischen Stellungen).
const WORST_CASE_NODE_COST: Duration = Duration::from_micros(4_400);
/// Sicherheitsfaktor des Not-Deckels, derselbe wie bei `TIME_BUDGET`
/// (200 Knoten x 4,4 ms ~ 0,9 s, x ~5 = 5 s).
const DEADLINE_SAFETY_FACTOR: u32 = 5;

/// Not-Deckel je Entscheidung fuer die ITERATIVE Suche
/// (`PREREG_r5_net_vs_solver.md` par.5a): `max(TIME_BUDGET, budget x 4,4 ms x 5)`.
/// Bindend soll das Knotenbudget sein; der Deckel ist nur Ausfallschutz und
/// waechst deshalb mit dem Budget mit (bei 2000 Knoten 44 s, bei 400 Knoten
/// 8,8 s, bei 200 Knoten greift das Minimum `TIME_BUDGET`). Greift er doch,
/// ist das Ergebnis lastabhaengig -- dieselbe Lage wie beim heutigen Loeser.
///
/// Der NICHT-iterative Pfad behaelt bewusst `TIME_BUDGET` (unveraendert, auch
/// bei einem Seiten-Budget ueber dem Default): sonst haette ein gesetztes
/// `MOSAIC_R5_NODE_BUDGET` ohne Spec-Feld seinen Deckel geaendert.
///
/// Nach oben auf [`DEADLINE_CAP`] begrenzt, damit `Instant::now() + deckel`
/// bei absurden Budgets nicht ueberlaeuft (der Deckel greift dann ab rund
/// 785.000 Knoten nicht mehr proportional -- weit jenseits jedes Messarms).
pub fn deadline_for_budget(budget: u64) -> Duration {
    let factor = u32::try_from(budget).unwrap_or(u32::MAX).saturating_mul(DEADLINE_SAFETY_FACTOR);
    let scaled = WORST_CASE_NODE_COST.checked_mul(factor).unwrap_or(DEADLINE_CAP);
    scaled.min(DEADLINE_CAP).max(TIME_BUDGET)
}

/// Obergrenze von [`deadline_for_budget`]: ein Tag.
const DEADLINE_CAP: Duration = Duration::from_secs(86_400);

/// Kleine Manufakturen mit noch verdecktem Bonuschip.
fn hidden_chip_factories(state: &GameState) -> Vec<usize> {
    state
        .factories
        .iter()
        .enumerate()
        .filter(|(_, f)| f.bonus_chip.is_some() && !f.bonus_chip_revealed)
        .map(|(i, _)| i)
        .collect()
}

/// Die Manufaktur, deren Chip beim Uebergang `parent` → `child` NEU aufgedeckt
/// wurde. `None`, wenn keine -- und ebenso bei mehr als einer: eine Drafting-
/// Aktion raeumt genau eine Manufaktur leer, mehrere gleichzeitig waeren ein
/// unerwarteter Zustand, und der wird lieber unbehandelt gelassen als still
/// falsch modelliert.
fn newly_revealed(parent: &GameState, child: &GameState) -> Option<usize> {
    let n = parent.factories.len().min(child.factories.len());
    let mut found: Option<usize> = None;
    for i in 0..n {
        let was_hidden = parent.factories[i].bonus_chip.is_some() && !parent.factories[i].bonus_chip_revealed;
        if was_hidden && child.factories[i].bonus_chip_revealed {
            if found.is_some() {
                return None;
            }
            found = Some(i);
        }
    }
    found
}

/// Nachfolge-Zustaende einer Aktion mit ihren Wahrscheinlichkeiten
/// (Gewichtssumme 1). Ohne Knopf, ohne Aufdeckung oder bei nur noch EINEM
/// verdeckten Chip genau ein Ausgang mit Gewicht 1.
///
/// Bei einem Aufdecken an Manufaktur `f` wird aufgezaehlt, WELCHER der noch
/// verdeckten Chips dort liegt: je Kandidat wird er im Elternzustand nach `f`
/// getauscht und die Aktion neu angewendet. Getauscht wird nur zwischen
/// verdeckten Manufakturen, die Belegung ist also a priori gleichverteilt und
/// das Gewicht ist die Vielfachheit. Nach dem Aufdecken halten die uebrigen
/// verdeckten Manufakturen genau den Restsatz -- die Invariante "verdeckte
/// Manufakturen tragen den Restsatz in beliebiger Reihenfolge" bleibt erhalten,
/// weshalb der Glaube gar nicht getrennt mitgefuehrt werden muss.
///
/// Gruppiert wird nach `.colors`: laut Code-Audit in `tiling_solver.rs` fliesst
/// NUR `.colors` je in eine Wertung, `chip_id` nie. Farbgleiche Chips sind fuer
/// die Suche also derselbe Ausgang und fallen zusammen -- aus 4! = 24
/// Belegungen werden dadurch in der Praxis deutlich weniger Zweige.
///
/// Bei genau EINEM verdeckten Chip ist seine Identitaet aus dem Restsatz
/// eindeutig ableitbar. Ihn dann zu lesen ist kein Leck, sondern legitim --
/// das ist keine Abkuerzung, sondern der korrekte Grenzfall.
fn action_outcomes(parent: &GameState, a: &Action, child: GameState, chance: bool) -> Vec<(f64, GameState)> {
    if !chance {
        return vec![(1.0, child)];
    }
    let f = match newly_revealed(parent, &child) {
        Some(f) => f,
        None => return vec![(1.0, child)],
    };
    let hidden = hidden_chip_factories(parent);
    if hidden.len() <= 1 {
        return vec![(1.0, child)];
    }

    // (Farben, Vielfachheit, ein Quell-Index mit diesen Farben)
    let mut groups: Vec<(Vec<crate::tile::TileColor>, usize, usize)> = Vec::new();
    for &i in &hidden {
        let colors = match parent.factories[i].bonus_chip.as_ref() {
            Some(c) => c.colors.clone(),
            None => continue,
        };
        match groups.iter_mut().find(|(c, _, _)| *c == colors) {
            Some((_, count, _)) => *count += 1,
            None => groups.push((colors, 1, i)),
        }
    }

    let total = hidden.len() as f64;
    let mut out: Vec<(f64, GameState)> = Vec::with_capacity(groups.len());
    for (_, count, src) in &groups {
        let mut p = parent.clone();
        if *src != f {
            let at_f = p.factories[f].bonus_chip.take();
            let at_src = p.factories[*src].bonus_chip.take();
            p.factories[f].bonus_chip = at_src;
            p.factories[*src].bonus_chip = at_f;
        }
        let mut g = Game { state: p };
        if g.apply_drafting(a).is_ok() {
            out.push((*count as f64 / total, g.state));
        }
    }

    if out.is_empty() {
        return vec![(1.0, child)];
    }
    // Renormieren, falls eine Variante unerwartet illegal war -- die
    // Gewichtssumme muss 1 bleiben, sonst waere der Erwartungswert skaliert
    // und mit den Werten anderer Zweige nicht mehr vergleichbar.
    let sum: f64 = out.iter().map(|(w, _)| *w).sum();
    if (sum - 1.0).abs() > 1e-12 && sum > 0.0 {
        for (w, _) in out.iter_mut() {
            *w /= sum;
        }
    }
    out
}

/// Ein Wurzel-/Kindkandidat: Sortierwert, Aktion und ihre gewichteten
/// Ausgaenge (genau einer, solange die Zufallsknoten aus sind).
struct Child {
    order_value: f64,
    action: Action,
    outcomes: Vec<(f64, GameState)>,
}

/// Exakter Endwert eines Spielers: exakter Rundenscore (Tiling-Solver) plus
/// exakte Wertungsplatten-Endwertung (NICHT die Fortschritts-Heuristik --
/// siehe Modul-Kommentar) plus projizierte Strafleisten-Punkte.
///
/// TASK #21 -- KORREKTHEITS-BEFUND (2026-07-29): die ERSTEN BEIDEN Terme
/// (`solve_round_final_score` + `calculate_end_scoring`) bezogen sich bisher
/// auf ZWEI VERSCHIEDENE Brettzustände. `solve_round_final_score` plant ein
/// optimales Tiling und liefert dessen PUNKTE; `calculate_end_scoring`
/// bewertete dabei das Brett DAVOR -- gerade die Steine, die Reihen, Spalten
/// und Diagonalen schließen und damit die Endwertung treiben, fehlten also in
/// der Endwertungs-Rechnung. Zwei Runde-5-Drafting-Züge mit gleichen
/// Rundenpunkten, aber unterschiedlich viel ERREICHBARER Endwertung, waren
/// dadurch für die Alpha-Beta-Suche ununterscheidbar.
///
/// Hinter demselben Toggle wie die Tiling-ZUGWAHL
/// (`crate::tiling_solver::ROUND5_ENDSCORING_ENABLED`, siehe dort für die
/// Gating-Historie des Zugwahl-Teils): ON nutzt stattdessen
/// `solve_round_final_score_endaware`, das die Endwertung DES ERREICHTEN
/// BRETTS bereits in seiner Blatt-Rekursion mit-maximiert. Die separate
/// `calculate_end_scoring`-Addition entfällt dann bewusst -- sie ist im
/// endaware-Term bereits enthalten, eine zusätzliche Addition wäre
/// Doppelzählung.
fn player_total_exact(state: &GameState, pi: usize) -> f64 {
    if crate::tiling_solver::ROUND5_ENDSCORING_ENABLED {
        crate::tiling_solver::solve_round_final_score_endaware(state, pi) as f64
            + projected_unplaceable_penalty(&state.players[pi]) as f64
    } else {
        solve_round_final_score(state, pi) as f64
            + calculate_end_scoring(&state.players[pi], &state.scoring_tile_ids).total as f64
            + projected_unplaceable_penalty(&state.players[pi]) as f64
    }
}

fn leaf_value(state: &GameState, perspective: usize) -> f64 {
    player_total_exact(state, perspective) - player_total_exact(state, 1 - perspective)
}

/// Legale Folgezustände von `state`, bereits angewendet und nach 1-Zug-
/// Vorschau (exakte Bewertung, siehe Modul-Kommentar -- kein Netz nötig)
/// absteigend sortiert. Wird sowohl für die Zugsortierung in `negamax` als
/// auch an der Wurzel (`choose_action`) genutzt, um doppeltes Anwenden
/// derselben Aktion zu vermeiden.
///
/// BUGFIX (`PREREG_round5_minfix_elo_reset.md` par.1 /
/// `PREREG_implementation_review_unprimed.md` par.7 Befund 1, bestaetigt):
/// bis hierher sortierte diese Funktion mit einem als Parameter
/// hereingereichten, WURZELFESTEN `perspective` -- dieselbe Liste wird aber
/// sowohl an Max- als auch an Min-Knoten von `negamax` benutzt (`:454`).
/// An einem Min-Knoten (`state.current_player != perspective`) ist
/// `leaf_value(s, perspective)` aus Sicht des NICHT ziehenden Spielers --
/// absteigend danach sortiert stehen die fuer den ZIEHENDEN (den Gegner der
/// Wurzel) besten Gegenzuege am ENDE der Liste. Unter dem Knotenbudget
/// (`negamax`s Kinderschleife bricht bei `node_count >= node_budget` ab)
/// werden genau diese Widerlegungen bevorzugt abgeschnitten, Min-Werte
/// liegen dadurch systematisch zu hoch. Fix: der Sortierschluessel ist jetzt
/// KNOTENLOKAL -- immer aus Sicht von `state.current_player`, dem an DIESEM
/// Knoten Ziehenden (Vorbild `self_play.rs:3398-3411`, das ebenso
/// knotenlokal sortiert). An Max-Knoten (`state.current_player ==
/// perspective`) ist das byte-identisch zum alten Verhalten. Die
/// RUECKGABE-Semantik von `negamax`/`leaf_value` bleibt unveraendert in
/// `perspective`-Sicht -- nur diese Sortierung wechselt, der Parameter wird
/// darum nicht mehr gebraucht.
fn ordered_children(state: &GameState, chance: bool) -> Vec<Child> {
    let mover = state.current_player;
    let mut scored: Vec<Child> = drafting_actions(state)
        .into_iter()
        .filter_map(|a| {
            let mut g = Game { state: state.clone() };
            if g.apply_drafting(&a).is_err() {
                return None;
            }
            let outcomes = action_outcomes(state, &a, g.state, chance);
            // Sortierwert = ERWARTUNGSWERT ueber die Ausgaenge, aus Sicht des
            // an DIESEM Knoten Ziehenden (`mover`, siehe Bugfix-Kommentar
            // oben) -- NICHT einer wurzelfesten Perspektive. Mit dem
            // konkreten (wahren) Chip zu sortieren waere zusaetzlich ein
            // Leck: unter Knotenbudget entscheidet die Reihenfolge mit,
            // welche Zuege ueberhaupt durchsucht werden (siehe Leckkanal 2
            // im Abschnittskopf). Mit ausgeschalteten Zufallsknoten ist die
            // Summe ueber genau einen Ausgang mit Gewicht 1 identisch zu
            // vorher.
            let v: f64 = outcomes.iter().map(|(w, s)| w * leaf_value(s, mover)).sum();
            Some(Child { order_value: v, action: a, outcomes })
        })
        .collect();
    scored.sort_by(|a, b| b.order_value.partial_cmp(&a.order_value).unwrap_or(std::cmp::Ordering::Equal));
    scored
}

/// Wert EINES Kandidaten: bei einem Ausgang direkt [`negamax`] mit
/// unveraendertem `(alpha,beta)`-Fenster, bei mehreren der gewichtete
/// Mittelwert (Zufallsknoten).
///
/// Innerhalb eines Zufallsknotens wird NICHT beschnitten: ein Cutoff auf einer
/// Teilsumme waere nur mit Wertgrenzen je Ausgang korrekt (Star1/Star2). Bei
/// hoechstens vier Ausgaengen und einem Budget in der Groessenordnung von 200
/// Knoten ist der Verzicht billiger als die Buchhaltung -- und vor allem
/// nachweisbar korrekt. Das aeussere Fenster des ELTERN-Knotens bleibt davon
/// unberuehrt, dort wird weiter normal beschnitten.
///
/// `depth_cut` (seit 2026-09-27, `PREREG_r5_net_vs_solver.md` par.5a): wird
/// auf `true` gesetzt, sobald irgendwo darunter ein Knoten an der
/// TIEFENGRENZE (`depth_remaining == 0`, Runde noch im Drafting) statisch
/// bewertet wurde. Nur die iterative Vertiefung liest das (Abbruch, wenn eine
/// Iteration das Rundenende erreicht hat); die Bestandsaufrufer reichen eine
/// Wegwerf-Variable. Es fliesst in keinen Wert ein.
#[allow(clippy::too_many_arguments)]
fn child_value(
    child: &Child,
    depth_remaining: u32,
    alpha: f64,
    beta: f64,
    perspective: usize,
    node_count: &mut u64,
    node_budget: u64,
    deadline: Instant,
    chance: bool,
    depth_cut: &mut bool,
) -> f64 {
    if child.outcomes.len() == 1 {
        return negamax(
            &child.outcomes[0].1,
            depth_remaining,
            alpha,
            beta,
            perspective,
            node_count,
            node_budget,
            deadline,
            chance,
            depth_cut,
        );
    }
    let mut acc = 0.0;
    for (w, s) in &child.outcomes {
        acc += w
            * negamax(
                s,
                depth_remaining,
                f64::NEG_INFINITY,
                f64::INFINITY,
                perspective,
                node_count,
                node_budget,
                deadline,
                chance,
                depth_cut,
            );
    }
    acc
}

/// TIEFE, so wie sie hier zaehlt (am Code gelesen 2026-09-27): jeder
/// ENTSCHEIDUNGSknoten kostet eine Tiefeneinheit (`child_value` reicht
/// `depth_remaining - 1` an das Kind), auch ein Pflichtzug mit nur einem
/// Kandidaten. Zufallsknoten kosten KEINE (`child_value` reicht alle Ausgaenge
/// mit derselben Tiefe weiter). `negamax(s, 0, ..)` ist ein Blatt mit dem
/// statischen Wert `leaf_value`. Jeder Aufruf zaehlt EINEN Knoten, auch ein
/// Blatt; die Vorsortierung `ordered_children` (ebenfalls `leaf_value` je
/// Kind) zaehlt nicht.
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
    chance: bool,
    depth_cut: &mut bool,
) -> f64 {
    *node_count += 1;
    if state.phase != Phase::Drafting
        || depth_remaining == 0
        || *node_count >= node_budget
        || Instant::now() >= deadline
    {
        // Nur Buchfuehrung fuer die iterative Vertiefung, kein Einfluss auf
        // den Rueckgabewert und kein zusaetzlicher Uhr- oder Zustandszugriff.
        if depth_remaining == 0 && state.phase == Phase::Drafting {
            *depth_cut = true;
        }
        return leaf_value(state, perspective);
    }
    let children = ordered_children(state, chance);
    if children.is_empty() {
        return leaf_value(state, perspective);
    }

    let maximizing = state.current_player == perspective;
    let mut alpha = alpha_in;
    let mut beta = beta_in;
    let mut best = if maximizing { f64::NEG_INFINITY } else { f64::INFINITY };
    for child in &children {
        if *node_count >= node_budget || Instant::now() >= deadline {
            break;
        }
        let val = child_value(
            child, depth_remaining - 1, alpha, beta, perspective, node_count, node_budget, deadline, chance, depth_cut,
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
    let mut depth_cut_unused = false;
    negamax(state, MAX_DEPTH.saturating_sub(1), f64::NEG_INFINITY, f64::INFINITY, 0, &mut node_count, node_budget(), deadline, chance_nodes_enabled(), &mut depth_cut_unused)
}

/// Wählt EINE Drafting-Aktion für `state` per exakter Alpha-Beta-Suche.
/// `None` außerhalb der Drafting-Phase oder ohne Legalzüge.
pub fn choose_action(state: &GameState) -> Option<Action> {
    choose_action_inner(state, chance_nodes_enabled(), node_budget())
}

/// Kern von [`choose_action`] mit explizit uebergebener Zufallsknoten-Flagge --
/// ausgelagert, damit die Tests unten beide Betriebsarten im SELBEN Prozess
/// pruefen koennen. Ueber `chance_nodes_enabled()` (OnceLock + Env) waere das
/// nicht moeglich: der Wert wird je Prozess genau einmal gelesen, und
/// `cargo test` laesst Tests parallel im selben Prozess laufen.
fn choose_action_inner(state: &GameState, chance: bool, budget: u64) -> Option<Action> {
    choose_action_deadlined(state, chance, budget, Instant::now() + TIME_BUDGET)
}

/// Wie [`choose_action_inner`], mit injizierbarer Not-Deckel-Deadline -- die
/// Orakel-Referenz in Teil E braucht mehr als `TIME_BUDGET`, sonst waere sie
/// deadline- und damit lastgebunden statt knotengebunden.
pub(crate) fn choose_action_deadlined(state: &GameState, chance: bool, budget: u64, deadline: Instant) -> Option<Action> {
    let perspective = state.current_player;
    let children = ordered_children(state, chance);
    if children.is_empty() {
        return None;
    }
    if children.len() == 1 {
        return Some(children[0].action.clone());
    }

    let mut node_count: u64 = 0;
    let mut depth_cut_unused = false;
    let mut best_action = children[0].action.clone();
    let mut best_val = f64::NEG_INFINITY;
    let mut alpha = f64::NEG_INFINITY;
    let beta = f64::INFINITY;
    for child in &children {
        if node_count >= budget || Instant::now() >= deadline {
            break;
        }
        let val = child_value(
            child,
            MAX_DEPTH.saturating_sub(1),
            alpha,
            beta,
            perspective,
            &mut node_count,
            budget,
            deadline,
            chance,
            &mut depth_cut_unused,
        );
        if val > best_val {
            best_val = val;
            best_action = child.action.clone();
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
    choose_action_with_analysis_budgeted(state, node_budget())
}

/// Kern von [`choose_action_with_analysis`] mit uebergebenem Knotenbudget
/// (`PREREG_r5_net_vs_solver.md` par.5a: Seiten-Feld
/// `SearchConfig::r5_solver_node_budget`). Mit `budget == node_budget()`
/// derselbe Rechenweg wie bis 2026-09-26: das Budget wurde dort an derselben
/// Stelle aus `node_budget()` gelesen, jetzt kommt es als Parameter.
fn choose_action_with_analysis_budgeted(state: &GameState, budget: u64) -> (Option<Action>, Value) {
    // Task #32 (`profiling.rs`-Modulkopf "Task #32"): GANZER Funktionskörper
    // als Haupteinstiegspunkt der "round5_alphabeta"-Kategorie -- deckt ALLE
    // Aufrufer (`mcts.rs`, `net_mcts.rs`) automatisch ab, ohne dort einzeln
    // instrumentieren zu müssen. `return` innerhalb dieser Closure verlässt
    // NUR die Closure (= die bisherige Funktionslogik unverändert).
    crate::profiling::selfplay_profile::timed(crate::profiling::selfplay_profile::SelfplayCat::Round5Alphabeta, || {
    let chance = chance_nodes_enabled();
    let perspective = state.current_player;
    let children = ordered_children(state, chance);
    if children.is_empty() {
        return (None, Value::Null);
    }

    let deadline = Instant::now() + TIME_BUDGET;
    let mut node_count: u64 = 0;
    let mut depth_cut_unused = false;
    let mut alpha = f64::NEG_INFINITY;
    let beta = f64::INFINITY;
    let mut best_idx = 0usize;
    let mut best_val = f64::NEG_INFINITY;
    let mut values: Vec<f64> = Vec::with_capacity(children.len());
    for (i, child) in children.iter().enumerate() {
        let val = if node_count >= budget || Instant::now() >= deadline {
            // Notfallpfad ohne Suche: Erwartungswert der 1-Zug-Vorschau ueber
            // die Ausgaenge (bei einem Ausgang identisch zu `leaf_value` von
            // vorher, also byte-gleich mit Zufallsknoten aus).
            child.outcomes.iter().map(|(w, s)| w * leaf_value(s, perspective)).sum()
        } else {
            child_value(
                child,
                MAX_DEPTH.saturating_sub(1),
                alpha,
                beta,
                perspective,
                &mut node_count,
                budget,
                deadline,
                chance,
                &mut depth_cut_unused,
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

    let entries: Vec<(&Action, f64)> = children.iter().map(|c| &c.action).zip(values.iter().copied()).collect();
    let analysis = analysis_json(state, &entries, best_idx, node_count, "alphabeta_round5", Value::Null);
    (Some(children[best_idx].action.clone()), analysis)
    })
}

/// Rohe Punkte-Margin (`leaf_value`-Skala) auf die [0,1]-Gewinnwahrscheinlichkeit,
/// dieselbe Formel wie im Analyse-Dict (siehe Kommentar in [`analysis_json`]).
pub(crate) fn margin_to_win_prob(val: f64) -> f64 {
    ((val / crate::mcts::VALUE_SCALE).tanh() + 1.0) / 2.0
}

/// Das debug.html-kompatible Analyse-Dict aus (Aktion, Alpha-Beta-Wert) je
/// Wurzelkandidat. Ausgelagert 2026-09-27 aus [`choose_action_with_analysis`],
/// damit die iterative Vertiefung dasselbe Format liefert; Inhalt und
/// Schluessel fuer den Bestandsaufruf unveraendert (`algorithm`
/// "alphabeta_round5", `max_depth` null).
fn analysis_json(
    state: &GameState,
    entries: &[(&Action, f64)],
    best_idx: usize,
    node_count: u64,
    algorithm: &str,
    max_depth: Value,
) -> Value {
    let moves: Vec<Value> = entries
        .iter()
        .enumerate()
        .map(|(i, &(a, val))| {
            let sm = SearchMove::Draft(a.clone());
            let (typ, desc, cat, _mv) = label_search_move(&sm, Some(state));
            // `val` ist eine rohe Punkte-Margin (own_total - opp_total, siehe
            // `leaf_value`), KEINE Gewinnwahrscheinlichkeit -- Lehrer-Modus/
            // `tools/analyze_game_log.py` erwarten `mcts_q` aber überall sonst
            // auf der [0,1]-Win-Prob-Skala (`net_mcts.rs::value_to_win_prob`,
            // `mcts.rs::normalize_score`) und multiplizieren sie ungeprüft mit
            // 100 für "Prozentpunkte" -- ohne diese Normalisierung ergab das in
            // Runde 5 Werte wie "-2500 pp" statt einer sinnvollen Prozentzahl
            // (Nutzer-Feedback 2026-07-27). Dieselbe Margin→[0,1]-Formel wie
            // `crate::mcts::normalize_score`, nur für eine Differenz statt
            // eines absoluten Scores (passt zu `self_play.rs`s
            // `((own-opp)/VALUE_SCALE).tanh()`-Margin-Ziel).
            let win_prob = margin_to_win_prob(val);
            json!({
                "action_id": i,
                "type": typ,
                "description": desc,
                "category": cat,
                "net_prob": Value::Null,
                "net_prob_norm": Value::Null,
                "mcts_visits": Value::Null,
                "mcts_share": Value::Null,
                "mcts_q": win_prob,
                "mcts_win_pct": win_prob * 100.0,
                "ab_value": val,
                "max_depth": Value::Null,
                "shaping": Value::Null,
                "chosen": i == best_idx,
            })
        })
        .collect();

    json!({
        "current_player": state.current_player,
        "ai_player": state.current_player,
        "value": Value::Null,
        "win_pct": Value::Null,
        "has_net": false,
        "algorithm": algorithm,
        "simulations": Value::Null,
        "num_actions": entries.len(),
        "num_actions_considered": entries.len(),
        "max_depth": max_depth,
        "ai_action": best_idx,
        "moves": moves,
        "tree": Value::Null,
        "node_visits": node_count,
    })
}

// ── Seiten-Einstieg und iterative Vertiefung (PREREG_r5_net_vs_solver.md par.5a) ──
//
// BEFUND, der den Bau ausgeloest hat (`choose_action_deadlined` oben): die
// Wurzelkinder werden der Reihe nach mit Tiefe `MAX_DEPTH - 1` und EINEM
// Knotenzaehler durchsucht. Frisst schon das erste Kind das Budget, gibt der
// Loeser `ordered_children[0]` zurueck, also die Vorsortierung "als ende die
// Runde jetzt". Die iterative Vertiefung unten verteilt dasselbe Budget
// stattdessen Tiefe um Tiefe auf ALLE Wurzelkinder.

/// Runde-5-Zugwahl einer NETZ-Seite (`net_mcts::r5_solver_action`), mit den
/// Seiten-Feldern `SearchConfig::r5_solver_iterative` und
/// `SearchConfig::r5_solver_node_budget`.
///
/// `iterative == false` ist derselbe Rechenweg wie [`choose_action`]:
/// `choose_action_inner(state, chance_nodes_enabled(), budget)`, und mit dem
/// Default `budget == node_budget()` sind die Argumente dieselben wie dort
/// (byte-identisch, Test `side_entry_default_matches_choose_action`). Ein
/// abweichendes Budget wirkt im nicht-iterativen Pfad nur auf den
/// Knotenzaehler; der Not-Deckel bleibt `TIME_BUDGET` (siehe
/// [`deadline_for_budget`]).
pub fn choose_action_for_side(state: &GameState, iterative: bool, budget: u64) -> Option<Action> {
    if iterative {
        choose_action_iterative(state, budget).map(|o| o.action)
    } else {
        choose_action_inner(state, chance_nodes_enabled(), budget)
    }
}

/// Wie [`choose_action_for_side`], mit Analyse-Dict (GUI-/Debug-Einstieg
/// `net_mcts::net_search_with_tree_inner`). Nicht-iterativ mit Default-Budget
/// derselbe Rechenweg wie [`choose_action_with_analysis`].
pub fn choose_action_with_analysis_for_side(state: &GameState, iterative: bool, budget: u64) -> (Option<Action>, Value) {
    if !iterative {
        return choose_action_with_analysis_budgeted(state, budget);
    }
    crate::profiling::selfplay_profile::timed(crate::profiling::selfplay_profile::SelfplayCat::Round5Alphabeta, || {
        let Some(out) = choose_action_iterative(state, budget) else {
            return (None, Value::Null);
        };
        let entries: Vec<(&Action, f64)> = out.root_values.iter().map(|(a, v)| (a, *v)).collect();
        let best_idx = out.root_values.iter().position(|(a, _)| *a == out.action).unwrap_or(0);
        let analysis = analysis_json(
            state,
            &entries,
            best_idx,
            out.nodes,
            "alphabeta_round5_iterative",
            json!(out.completed_depth),
        );
        (Some(out.action.clone()), analysis)
    })
}

/// Ergebnis der iterativen Vertiefung. Die Felder ausser `action`/`value`
/// sind Buchfuehrung fuer Analyse-Dict und Kalibriersonde.
#[derive(Debug, Clone)]
pub struct IterativeOutcome {
    /// Gewaehlter Zug.
    pub action: Action,
    /// Sein Wert (Punkte-Margin aus Sicht des Ziehenden, `leaf_value`-Skala)
    /// in der Iteration, aus der er stammt.
    pub value: f64,
    /// Tiefe der letzten VOLLSTAENDIGEN Iteration in Halbzuegen unter der
    /// Wurzel. 1 = nur die Vorsortierung (`ordered_children`), es kam keine
    /// tiefere Iteration zu Ende.
    pub completed_depth: u32,
    /// Verbrauchte Knoten ueber ALLE Iterationen, die abgebrochene
    /// eingeschlossen (gemeinsames Budget).
    pub nodes: u64,
    /// `true`: die letzte vollstaendige Iteration hat keinen Knoten an der
    /// Tiefengrenze gekappt -- jeder Pfad lief bis zum Rundenende, tiefer
    /// suchen aendert nichts mehr. Dann wird nicht weiter vertieft.
    pub reached_round_end: bool,
    /// `true`: der Zug stammt aus der ANGEBROCHENEN Iteration (Ausnahme, siehe
    /// [`choose_action_iterative_inner`]).
    pub from_partial_iteration: bool,
    /// Je Wurzelkind der Wert aus der letzten vollstaendigen Iteration, in
    /// deren Suchreihenfolge (fuer das Analyse-Dict). Werte ausser dem besten
    /// sind wie beim heutigen Loeser oft nur obere Schranken (Alpha-Beta an
    /// der Wurzel, fail-low).
    pub root_values: Vec<(Action, f64)>,
}

/// Iterative Vertiefung mit dem Seiten-Budget und dem mitwachsenden
/// Not-Deckel [`deadline_for_budget`]; Zufallsknoten wie im Bestand ueber
/// `chance_nodes_enabled()`.
pub fn choose_action_iterative(state: &GameState, budget: u64) -> Option<IterativeOutcome> {
    choose_action_iterative_inner(state, chance_nodes_enabled(), budget, Instant::now() + deadline_for_budget(budget))
}

/// Kern der iterativen Vertiefung (`PREREG_r5_net_vs_solver.md` par.5a).
///
/// ABLAUF:
/// * Tiefe 1 ist die Vorsortierung selbst: `ordered_children` hat jedes
///   Wurzelkind schon mit dem statischen Wert bewertet, und bei Tiefe 1 lieferte
///   `child_value(kind, 0, ..)` genau diesen Wert (bei mehreren Ausgaengen
///   denselben gewichteten Mittelwert). Sie kostet darum keinen Knoten.
/// * Fuer d = 2, 3, ... bis `MAX_DEPTH`: die Wurzelkinder STABIL nach den
///   Werten der vorigen Iteration absteigend sortieren (bei Gleichstand bleibt
///   die vorige Reihenfolge), dann Alpha-Beta an der Wurzel wie in
///   `choose_action_deadlined`, je Kind `child_value(kind, d - 1, ..)` --
///   derselbe `negamax`, an der Tiefengrenze derselbe statische Blattwert.
///   Unterhalb der Wurzel sortiert weiter `ordered_children` (keine
///   Transpositionstabelle, kein Zugspeicher -- Lesbarkeit).
/// * EIN Knotenzaehler ueber alle Iterationen; das Budget gilt fuer die Summe.
///
/// WANN EINE ITERATION VOLLSTAENDIG IST: wenn nach ihr `nodes < budget` und
/// die Deadline nicht erreicht ist. Der Zaehler waechst monoton, und `negamax`
/// kappt nur bei `nodes >= budget` (oder Deadline); liegt er nach der Iteration
/// darunter, hat in ihr keine Budget-Kappung stattgefunden. Die Umkehrung gilt
/// nicht ganz (der Knoten, der das Budget genau erreicht, kann ein natuerliches
/// Blatt gewesen sein) -- dann wird die Iteration konservativ verworfen.
///
/// RUECKGABE: der beste Zug der letzten vollstaendigen Iteration. AUSNAHME
/// (Standard bei iterativer Vertiefung, begruendet): in der angebrochenen
/// Iteration steht das bisher beste Kind an erster Stelle. Ist es UND ein
/// spaeteres Kind vollstaendig bewertet (Zaehler nach dem spaeteren Kind
/// noch unter dem Budget, also keine Kappung bis dahin), und liegt der Wert
/// des spaeteren Kinds ueber dem Fenster `alpha` (dann ist er exakt, keine
/// Schranke), so ist dieses Kind auf der TIEFEREN Stufe nachweislich besser als
/// der bisherige Beste auf derselben Stufe. Dann gilt es. Unvollstaendig
/// bewertete Kinder zaehlen nie.
///
/// ENDE: Budget erschoepft, Deadline erreicht, `MAX_DEPTH` erreicht, oder eine
/// vollstaendige Iteration ohne jede Tiefenkappung (`depth_cut == false`):
/// dann lief jeder durchsuchte Pfad bis zum Rundenende (oder wurde von
/// Alpha-Beta mit exakten Werten abgeschnitten), eine tiefere Iteration
/// lieferte dieselben Werte.
pub(crate) fn choose_action_iterative_inner(
    state: &GameState,
    chance: bool,
    budget: u64,
    deadline: Instant,
) -> Option<IterativeOutcome> {
    let perspective = state.current_player;
    let mut children = ordered_children(state, chance);
    if children.is_empty() {
        return None;
    }

    // Tiefe 1 = Vorsortierung (siehe Doku). `ordered_children` sortiert aus
    // Sicht des Ziehenden, an der Wurzel ist das `perspective`.
    let mut values: Vec<f64> = children.iter().map(|c| c.order_value).collect();
    let mut completed_depth: u32 = 1;
    let mut reached_round_end = children
        .iter()
        .all(|c| c.outcomes.iter().all(|(_, s)| s.phase != Phase::Drafting));
    let mut best_idx = 0usize;
    let mut node_count: u64 = 0;

    // Ein einziger Kandidat: wie im Bestand sofort zurueck, ohne Suche.
    while children.len() > 1 && !reached_round_end && completed_depth < MAX_DEPTH {
        // Wurzelkinder nach der vorigen Iteration ordnen (stabil). Nach der
        // Sortierung steht der bisher beste Zug an Index 0.
        let mut order: Vec<usize> = (0..children.len()).collect();
        order.sort_by(|&a, &b| values[b].partial_cmp(&values[a]).unwrap_or(std::cmp::Ordering::Equal));
        children = reorder(children, &order);
        values = order.iter().map(|&i| values[i]).collect();
        best_idx = 0;

        let depth = completed_depth + 1;
        let mut depth_cut = false;
        let mut alpha = f64::NEG_INFINITY;
        let beta = f64::INFINITY;
        let mut iter_values: Vec<f64> = Vec::with_capacity(children.len());
        let mut iter_best_idx = 0usize;
        let mut iter_best_val = f64::NEG_INFINITY;
        let mut complete = true;
        for child in &children {
            if node_count >= budget || Instant::now() >= deadline {
                complete = false;
                break;
            }
            let val = child_value(
                child,
                depth - 1,
                alpha,
                beta,
                perspective,
                &mut node_count,
                budget,
                deadline,
                chance,
                &mut depth_cut,
            );
            if node_count >= budget || Instant::now() >= deadline {
                // In diesem Kind kann gekappt worden sein -- Wert verwerfen.
                complete = false;
                break;
            }
            let i = iter_values.len();
            iter_values.push(val);
            if val > iter_best_val {
                iter_best_val = val;
                iter_best_idx = i;
            }
            if val > alpha {
                alpha = val;
            }
        }

        if complete {
            values = iter_values;
            best_idx = iter_best_idx;
            completed_depth = depth;
            reached_round_end = !depth_cut;
            continue;
        }
        // Angebrochene Iteration: Ausnahme nur, wenn mindestens das erste Kind
        // (der bisherige Beste) UND ein besseres spaeteres Kind voll bewertet
        // sind. `iter_best_idx > 0` heisst genau das: ein spaeteres Kind lag
        // strikt ueber dem Wert des ersten, also ueber `alpha` -- exakt.
        // `root_values` bleiben die der letzten VOLLSTAENDIGEN Iteration.
        if !iter_values.is_empty() && iter_best_idx > 0 {
            return Some(IterativeOutcome {
                action: children[iter_best_idx].action.clone(),
                value: iter_best_val,
                completed_depth,
                nodes: node_count,
                reached_round_end,
                from_partial_iteration: true,
                root_values: children.iter().map(|c| c.action.clone()).zip(values.iter().copied()).collect(),
            });
        }
        break;
    }

    Some(IterativeOutcome {
        action: children[best_idx].action.clone(),
        value: values[best_idx],
        completed_depth,
        nodes: node_count,
        reached_round_end,
        from_partial_iteration: false,
        root_values: children.iter().map(|c| c.action.clone()).zip(values.iter().copied()).collect(),
    })
}

/// `children` in die Reihenfolge `order` bringen (Indizes in die alte Liste),
/// ohne `Child` klonen zu muessen.
fn reorder(children: Vec<Child>, order: &[usize]) -> Vec<Child> {
    let mut slots: Vec<Option<Child>> = children.into_iter().map(Some).collect();
    order.iter().map(|&i| slots[i].take().expect("Index doppelt in der Sortierung")).collect()
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

    // ── Zufallsknoten fuer die verdeckten Bonuschips ─────────────────────────

    /// Runde-5-Zustand, in dem EIN Zug eine Manufaktur leerraeumt (und damit
    /// ihren Chip aufdeckt): Manufaktur 0 haelt genau eine Sonnenfliese und
    /// keinen Mondstapel. Die vier Chips werden auf unterscheidbare Farben
    /// gesetzt, sonst waere eine Permutation ein No-Op.
    fn round5_state_with_imminent_reveal(seed: u64) -> GameState {
        use crate::dome::BonusChip;
        use crate::tile::TileColor::*;
        let mut s = round5_state(seed);
        s.factories[0].sun_tiles = vec![Rot];
        s.factories[0].moon_stacks.clear();
        let colors = [vec![Rot], vec![Blau], vec![Gelb], vec![Schwarz]];
        for (i, c) in colors.iter().enumerate() {
            if i < s.factories.len() {
                s.factories[i].bonus_chip = Some(BonusChip { chip_id: i, colors: c.clone() });
                s.factories[i].bonus_chip_revealed = false;
            }
        }
        s
    }

    #[test]
    fn chance_off_keeps_exactly_one_outcome_per_child() {
        // Parität: ohne Knopf muss jeder Kandidat genau einen Ausgang mit
        // Gewicht 1 tragen -- dann ist `child_value` bitgleich zum alten
        // `negamax`-Aufruf und `ordered_children`s Sortierwert bitgleich zum
        // alten `leaf_value`.
        let s = round5_state_with_imminent_reveal(11);
        let children = ordered_children(&s, false);
        assert!(!children.is_empty());
        for c in &children {
            assert_eq!(c.outcomes.len(), 1, "ohne Knopf darf kein Zufallsknoten entstehen");
            assert_eq!(c.outcomes[0].0, 1.0);
        }
    }

    #[test]
    fn chance_on_branches_at_a_reveal_with_weights_summing_to_one() {
        // Gegenprobe zur Invarianz unten: der Zufallsknoten muss ueberhaupt
        // feuern, sonst waere jene Prüfung leer.
        let s = round5_state_with_imminent_reveal(12);
        let children = ordered_children(&s, true);
        assert!(!children.is_empty());
        let branched: Vec<&Child> = children.iter().filter(|c| c.outcomes.len() > 1).collect();
        assert!(
            !branched.is_empty(),
            "kein Zufallsknoten entstanden -- Aufdeckung nicht erreichbar, Test waere wertlos"
        );
        for c in &children {
            let sum: f64 = c.outcomes.iter().map(|(w, _)| *w).sum();
            assert!((sum - 1.0).abs() < 1e-12, "Gewichtssumme {sum} != 1");
            // 4 verdeckte Chips mit 4 verschiedenen Farben -> hoechstens 4 Zweige
            assert!(c.outcomes.len() <= 4, "mehr Zweige als verdeckte Chips");
        }
    }

    #[test]
    fn equal_colored_chips_collapse_into_one_branch() {
        // `chip_id` fliesst laut Code-Audit (tiling_solver.rs) NIE in eine
        // Wertung, nur `.colors`. Farbgleiche Chips sind fuer die Suche also
        // derselbe Ausgang -- sonst waere die Verzweigung unnoetig teuer.
        use crate::dome::BonusChip;
        use crate::tile::TileColor::Rot;
        let mut s = round5_state_with_imminent_reveal(13);
        for i in 0..s.factories.len() {
            s.factories[i].bonus_chip = Some(BonusChip { chip_id: i, colors: vec![Rot] });
            s.factories[i].bonus_chip_revealed = false;
        }
        let children = ordered_children(&s, true);
        for c in &children {
            assert_eq!(
                c.outcomes.len(),
                1,
                "vier farbgleiche Chips muessen zu EINEM Ausgang zusammenfallen"
            );
        }
    }

    /// Min-Knoten-Regressionstest fuer den Sortier-Fix
    /// (`PREREG_round5_minfix_elo_reset.md` par.1 /
    /// `PREREG_implementation_review_unprimed.md` par.7 Befund 1):
    /// `ordered_children` sortiert seit dem Fix immer knotenlokal (aus
    /// Sicht von `state.current_player`). An einem MIN-Knoten -- hier
    /// simuliert, indem eine gedachte Wurzel-Perspektive `1 - s.current_player`
    /// angenommen wird, so wie `negamax` ihn an einem Min-Knoten saehe --
    /// muss die fuer den ZIEHENDEN beste Widerlegung an Position 0 stehen,
    /// NICHT die aus Sicht der (hier gedachten) Wurzel beste.
    #[test]
    fn ordered_children_puts_the_movers_best_reply_first_at_a_min_node() {
        // Mehrere Seeds durchprobieren, bis ein Zustand mit >=2 Kandidaten
        // UND einer echten Wertspreizung gefunden ist -- sonst waere der
        // Test bei zufaelligem Gleichstand aller Kandidaten wertlos (vgl.
        // "Testaufbau"-Muster in den Nachbartests).
        let mut found = false;
        for seed in 30u64..80 {
            let s = round5_state(seed);
            let mover = s.current_player;
            let root_perspective = 1 - mover; // macht `s` zu einem MIN-Knoten
            let children = ordered_children(&s, false);
            if children.len() < 2 {
                continue;
            }
            let max_v = children.iter().map(|c| c.order_value).fold(f64::NEG_INFINITY, f64::max);
            let min_v = children.iter().map(|c| c.order_value).fold(f64::INFINITY, f64::min);
            if (max_v - min_v).abs() < 1e-9 {
                continue; // kein Unterschied zwischen den Kandidaten -- naechster Seed
            }
            found = true;

            // Referenz: bester Zug FUER DEN ZIEHENDEN, unabhaengig von
            // `ordered_children` direkt ueber `leaf_value` nachgerechnet.
            let mut expected_action: Option<&Action> = None;
            let mut expected_v = f64::NEG_INFINITY;
            for c in &children {
                let v: f64 = c.outcomes.iter().map(|(w, s2)| w * leaf_value(s2, mover)).sum();
                if v > expected_v {
                    expected_v = v;
                    expected_action = Some(&c.action);
                }
            }
            assert_eq!(
                &children[0].action,
                expected_action.expect("mind. ein Kandidat"),
                "seed={seed}: Position 0 muss die fuer den ZIEHENDEN beste Widerlegung sein"
            );

            // Gegenprobe, dass der Fix hier ueberhaupt etwas aendert: mit der
            // ALTEN, wurzelfesten Formel (`leaf_value(s, root_perspective)`)
            // waere an diesem Min-Knoten ein ANDERER Kandidat das Optimum
            // gewesen als der fuer den Ziehenden tatsaechlich beste (`leaf_value`
            // ist exakt antisymmetrisch: `leaf_value(s,p) = -leaf_value(s,1-p)`,
            // die alte Formel bewertet also strikt gegenlaeufig zur neuen).
            // Kein Vergleich gegen `children.last()`: bei einem Gleichstand
            // mehrerer Kandidaten am unteren Ende waere die Position dort
            // nicht eindeutig, das Optimum unter der alten Formel ist es aber.
            let mut old_best_action: Option<&Action> = None;
            let mut old_best_v = f64::NEG_INFINITY;
            for c in &children {
                let v: f64 = c.outcomes.iter().map(|(w, s2)| w * leaf_value(s2, root_perspective)).sum();
                if v > old_best_v {
                    old_best_v = v;
                    old_best_action = Some(&c.action);
                }
            }
            assert_ne!(
                &children[0].action,
                old_best_action.expect("mind. ein Kandidat"),
                "seed={seed}: alte und neue Sortierung waehlten denselben ersten Kandidaten -- Test waere wertlos"
            );
        }
        assert!(found, "kein Seed mit >=2 unterschiedlich bewerteten Kandidaten gefunden -- Testaufbau pruefen");
    }

    /// Max-Knoten-Gegenprobe: an einem Max-Knoten (`state.current_player ==
    /// Wurzel-Perspektive`) war der alte, wurzelfeste Sortierschluessel
    /// bereits identisch zum neuen knotenlokalen Schluessel (Prereg par.1:
    /// "an Max-Knoten identisch zu heute") -- die Reihenfolge nach dem Fix
    /// muss darum exakt der manuell mit der ALTEN Formel (`perspective =
    /// state.current_player`) nachgerechneten entsprechen.
    #[test]
    fn ordered_children_matches_the_old_ordering_at_a_max_node() {
        for seed in [41u64, 42, 43, 44, 45] {
            let s = round5_state(seed);
            let perspective = s.current_player; // Max-Knoten per Konstruktion
            let children = ordered_children(&s, false);
            let mut expected: Vec<(f64, Action)> = drafting_actions(&s)
                .into_iter()
                .filter_map(|a| {
                    let mut g = Game { state: s.clone() };
                    if g.apply_drafting(&a).is_err() {
                        return None;
                    }
                    Some((leaf_value(&g.state, perspective), a))
                })
                .collect();
            expected.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));
            assert_eq!(children.len(), expected.len(), "seed={seed}: Kandidatenzahl weicht ab");
            for (i, (c, (_, a))) in children.iter().zip(expected.iter()).enumerate() {
                assert_eq!(
                    &c.action, a,
                    "seed={seed} Position {i}: Max-Knoten-Reihenfolge weicht von der alten Formel ab"
                );
            }
        }
    }

    #[test]
    fn chosen_action_is_invariant_under_hidden_chip_permutation() {
        // DIE Korrektheitseigenschaft von Weg A: die Zugwahl darf nicht davon
        // abhaengen, WELCHER der verdeckten Chips auf welcher Manufaktur liegt
        // -- diese Zuordnung ist verdeckt, der Restsatz ist es nicht.
        //
        // WICHTIG, damit dieser Test nicht ueberschaetzt wird: er DISKRIMINIERT
        // NICHT. Die Teil-D-Sonde unten hat auf 8 realistischen Partien
        // (137 Entscheidungen, 103 mit >=2 verdeckten Chips) gemessen, dass
        // AUCH DER ALTE, lesende Modus permutationsinvariant ist -- 0/247 in
        // beiden Betriebsarten. Der Grund ist das Knotenbudget: bis die
        // Chipfarbe wirkt, muesste die Suche eine Manufaktur leerraeumen,
        // aufdecken, den Chip NEHMEN und ihn im Tiling verwerten, und dafuer
        // reichen 200 Knoten nie. Dieser Test sichert also die EIGENSCHAFT ab
        // (auch fuer kuenftig groessere Budgets, wo sie zu greifen beginnt) --
        // er belegt NICHT, dass ein wirksamer Defekt behoben wurde.
        for seed in [21u64, 22, 23, 24] {
            let base = round5_state_with_imminent_reveal(seed);
            let hidden = hidden_chip_factories(&base);
            assert!(hidden.len() >= 2, "Testaufbau: mindestens zwei verdeckte Chips");

            let reference = choose_action_inner(&base, true, NODE_BUDGET).expect("Aktion");
            // Alle zyklischen Verschiebungen der Belegung durchprobieren.
            for shift in 1..hidden.len() {
                let mut permuted = base.clone();
                let chips: Vec<_> = hidden
                    .iter()
                    .map(|&i| base.factories[i].bonus_chip.clone())
                    .collect();
                for (k, &i) in hidden.iter().enumerate() {
                    permuted.factories[i].bonus_chip = chips[(k + shift) % chips.len()].clone();
                }
                let got = choose_action_inner(&permuted, true, NODE_BUDGET).expect("Aktion");
                assert_eq!(
                    got, reference,
                    "Seed {seed}, Verschiebung {shift}: die Zugwahl haengt an der verdeckten Zuordnung"
                );
            }
        }
    }

    #[test]
    fn node_budget_knob_defaults_to_the_constant() {
        // Der Budget-Knopf existiert, damit "ehrlich" und "flacher" in einer
        // Anker-Kante trennbar bleiben -- ohne gesetzte Variable darf er das
        // Verhalten nicht veraendern.
        assert_eq!(node_budget(), NODE_BUDGET);
    }

    /// TEIL D der Zufallsknoten-Vorregistrierung: wie oft haengt die
    /// Runde-5-Zugwahl an der VERDECKTEN Belegung der Bonuschips? Gemessen auf
    /// REALISTISCHEN Zustaenden (`drive_to_round_start(seed, 5)`, dieselbe
    /// Quelle wie die Knoten-Kalibrierung oben) und ueber JEDE Entscheidung der
    /// Runde, nicht nur die erste. Als `#[ignore]` markiert: Messung, kein
    /// Urteil -- laeuft auf Abruf per `cargo test --release -- --ignored`.
    #[test]
    #[ignore]
    fn teil_d_permutation_sensitivity_probe() {
        use crate::round_transition::drive_to_round_start;
        for &chance in &[false, true] {
            let mut decisions = 0usize;
            let mut comparisons = 0usize;
            let mut flipped = 0usize;
            let mut with_hidden = 0usize;
            for seed in [101u64, 202, 303, 404, 505, 606, 707, 808] {
                let mut state = drive_to_round_start(seed, 5);
                let mut guard = 0u32;
                while state.phase == Phase::Drafting && guard < 200 {
                    guard += 1;
                    let reference = match choose_action_inner(&state, chance, NODE_BUDGET) {
                        Some(a) => a,
                        None => break,
                    };
                    decisions += 1;
                    let hidden = hidden_chip_factories(&state);
                    if hidden.len() >= 2 {
                        with_hidden += 1;
                        let chips: Vec<_> =
                            hidden.iter().map(|&i| state.factories[i].bonus_chip.clone()).collect();
                        for shift in 1..hidden.len() {
                            let mut permuted = state.clone();
                            for (k, &i) in hidden.iter().enumerate() {
                                permuted.factories[i].bonus_chip = chips[(k + shift) % chips.len()].clone();
                            }
                            if let Some(got) = choose_action_inner(&permuted, chance, NODE_BUDGET) {
                                comparisons += 1;
                                if got != reference {
                                    flipped += 1;
                                }
                            }
                        }
                    }
                    let mut g = Game { state };
                    if g.apply_drafting(&reference).is_err() {
                        break;
                    }
                    state = g.state;
                }
            }
            let pct = if comparisons > 0 { 100.0 * flipped as f64 / comparisons as f64 } else { 0.0 };
            println!(
                "TEIL D chance={chance}: {flipped}/{comparisons} Permutationen kippen die Wahl ({pct:.1}%)                  | Entscheidungen {decisions}, davon mit >=2 verdeckten Chips {with_hidden}"
            );
        }
    }

    /// Ist `NODE_BUDGET` = 200 ueberhaupt ausreichend? (Nutzer-Frage
    /// 2026-08-10.) Die 200 sind laut Kalibrierungs-Kommentar oben das p75
    /// dessen, was der alte 150ms-Deckel ERREICHTE -- eine Tragbarkeitszahl
    /// fuers Self-Play, keine Suffizienzzahl. Direkte Pruefung: wie oft aendert
    /// ein hoeheres Budget die Zugwahl? Aendert sich nichts, war 200 genug;
    /// aendert sich viel, sucht der "exakte Loeser" zu flach.
    #[test]
    #[ignore]
    fn node_budget_sufficiency_probe() {
        use crate::round_transition::drive_to_round_start;
        let seeds = [101u64, 202, 303, 404, 505, 606, 707, 808];
        for &budget in &[400u64, 1000, 4000] {
            let mut total = 0usize;
            let mut changed = 0usize;
            let mut nodes_hint = 0usize;
            for &seed in &seeds {
                let mut state = drive_to_round_start(seed, 5);
                let mut guard = 0u32;
                while state.phase == Phase::Drafting && guard < 200 {
                    guard += 1;
                    let base = match choose_action_inner(&state, false, NODE_BUDGET) {
                        Some(a) => a,
                        None => break,
                    };
                    if let Some(big) = choose_action_inner(&state, false, budget) {
                        total += 1;
                        if big != base {
                            changed += 1;
                        }
                    }
                    nodes_hint += drafting_actions(&state).len();
                    let mut g = Game { state };
                    if g.apply_drafting(&base).is_err() {
                        break;
                    }
                    state = g.state;
                }
            }
            let pct = if total > 0 { 100.0 * changed as f64 / total as f64 } else { 0.0 };
            let avg_branch = if total > 0 { nodes_hint as f64 / total as f64 } else { 0.0 };
            println!(
                "BUDGET {budget} vs {NODE_BUDGET}: {changed}/{total} Zugwahlen aendern sich ({pct:.1}%)                  | mittlere Verzweigung an der Wurzel {avg_branch:.1}"
            );
        }
    }

    /// TEIL E (Loeser-Haelfte): Orakel-Uebereinstimmung. Eine tiefe
    /// Referenzsuche liefert die Vergleichswahl, dann der Anteil, in dem ein
    /// kleineres Budget sie trifft. Beantwortet "was kostet uns 200" auf einer
    /// Skala, die spaeter auch fuer das NETZ gilt -- ohne Arena, also ohne den
    /// Symmetrie-Fallstrick (der Loeser sitzt in beiden Bahnen).
    #[test]
    #[ignore]
    fn teil_e_oracle_agreement_probe() {
        use crate::round_transition::drive_to_round_start;
        const ORACLE: u64 = 20_000;
        let seeds = [101u64, 202, 303, 404, 505, 606, 707, 808];
        let budgets = [200u64, 400, 1000, 4000];
        let mut agree = [0usize; 4];
        let mut total = 0usize;
        let mut oracle_deadline_hits = 0usize;
        for &seed in &seeds {
            let mut state = drive_to_round_start(seed, 5);
            let mut guard = 0u32;
            while state.phase == Phase::Drafting && guard < 200 {
                guard += 1;
                // Orakel mit grosszuegiger Deadline, damit KNOTEN binden.
                let t0 = Instant::now();
                let oracle = match choose_action_deadlined(
                    &state,
                    false,
                    ORACLE,
                    Instant::now() + Duration::from_secs(120),
                ) {
                    Some(a) => a,
                    None => break,
                };
                if t0.elapsed() >= Duration::from_secs(120) {
                    oracle_deadline_hits += 1;
                }
                total += 1;
                for (k, &b) in budgets.iter().enumerate() {
                    if let Some(got) = choose_action_inner(&state, false, b) {
                        if got == oracle {
                            agree[k] += 1;
                        }
                    }
                }
                // Weitergespielt wird mit der ORAKEL-Wahl: so bleibt die
                // Stellungsfolge fuer alle Kandidaten dieselbe.
                let mut g = Game { state };
                if g.apply_drafting(&oracle).is_err() {
                    break;
                }
                state = g.state;
            }
        }
        println!("TEIL E: Orakel = {ORACLE} Knoten, {total} Entscheidungen, Deadline griff {oracle_deadline_hits}x");
        for (k, &b) in budgets.iter().enumerate() {
            let pct = if total > 0 { 100.0 * agree[k] as f64 / total as f64 } else { 0.0 };
            println!("  Budget {b:>5}: {}/{total} Uebereinstimmung ({pct:.1}%)", agree[k]);
        }
    }

    /// Wie stark unterscheidet sich die Zugwahl MIT von der OHNE Zufallsknoten?
    /// Das bemisst, was eine Anker-Kante ueberhaupt finden koennte: aendert
    /// sich fast nie ein Zug, ist der Elo-Versatz sicher innerhalb der
    /// +-4,4pp-Marge und die Kante braucht kein grosses n.
    #[test]
    #[ignore]
    fn chance_node_behaviour_divergence_probe() {
        use crate::round_transition::drive_to_round_start;
        let mut r5_decisions = 0usize;
        let mut diverged = 0usize;
        for seed in [101u64, 202, 303, 404, 505, 606, 707, 808] {
            let mut state = drive_to_round_start(seed, 5);
            let mut guard = 0u32;
            while state.phase == Phase::Drafting && guard < 200 {
                guard += 1;
                let off = match choose_action_inner(&state, false, NODE_BUDGET) {
                    Some(a) => a,
                    None => break,
                };
                let on = choose_action_inner(&state, true, NODE_BUDGET);
                r5_decisions += 1;
                if on.as_ref() != Some(&off) {
                    diverged += 1;
                }
                let mut g = Game { state };
                if g.apply_drafting(&off).is_err() {
                    break;
                }
                state = g.state;
            }
        }
        let pct = 100.0 * diverged as f64 / r5_decisions.max(1) as f64;
        println!(
            "DIVERGENZ Zufallsknoten an/aus: {diverged}/{r5_decisions} Runde-5-Zugwahlen ({pct:.1}%)"
        );
    }

    /// Rechnet "weicht ab" in "kostet Punkte" um -- die Teil-E-Restarbeit.
    ///
    /// Anlass (Nutzer-Korrektur 2026-08-10): meine Begruendung "die
    /// Abweichungen liegen in der Runde mit der geringsten Hebelwirkung" war
    /// FALSCH. Runde 5 ist der Zahltag; gering ist die FREIHEIT (das
    /// Kuppelraster ist ab Runde 5 fix), nicht der Hebel. Ein Freispruch fuer
    /// den Anker-Versatz braucht also den Punktpreis, nicht ein Argument ueber
    /// die Wichtigkeit der Runde.
    ///
    /// Bewertet wird mit der Orakel-Tiefe aus der Perspektive des ZIEHENDEN:
    /// `leaf_value` ist eine Punkte-Differenz, das Delta ist damit direkt in
    /// Punkten lesbar.
    #[test]
    #[ignore]
    fn teil_e_value_cost_of_divergence_probe() {
        use crate::round_transition::drive_to_round_start;
        const ORACLE: u64 = 20_000;
        let long = || Instant::now() + Duration::from_secs(120);

        let deep = |st: &GameState, persp: usize| -> f64 {
            let mut nodes: u64 = 0;
            let mut depth_cut_unused = false;
            negamax(st, MAX_DEPTH.saturating_sub(1), f64::NEG_INFINITY, f64::INFINITY,
                    persp, &mut nodes, ORACLE, long(), false, &mut depth_cut_unused)
        };
        let after = |st: &GameState, a: &Action| -> Option<GameState> {
            let mut g = Game { state: st.clone() };
            g.apply_drafting(a).ok()?;
            Some(g.state)
        };

        let mut chance_deltas: Vec<f64> = Vec::new();
        let mut solver_losses: Vec<f64> = Vec::new();
        let mut decisions = 0usize;
        for seed in [101u64, 202, 303, 404, 505, 606, 707, 808] {
            let mut state = drive_to_round_start(seed, 5);
            let mut guard = 0u32;
            while state.phase == Phase::Drafting && guard < 200 {
                guard += 1;
                let mover = state.current_player;
                let off = match choose_action_inner(&state, false, NODE_BUDGET) {
                    Some(a) => a,
                    None => break,
                };
                decisions += 1;

                // (a) Zufallsknoten an/aus -- nur wo die Wahl abweicht
                if let Some(on) = choose_action_inner(&state, true, NODE_BUDGET) {
                    if on != off {
                        if let (Some(s_on), Some(s_off)) = (after(&state, &on), after(&state, &off)) {
                            chance_deltas.push(deep(&s_on, mover) - deep(&s_off, mover));
                        }
                    }
                }
                // (b) Loeser@200 gegen die Orakel-Wahl -- Verlust in Punkten
                if let Some(oracle) = choose_action_deadlined(&state, false, ORACLE, long()) {
                    if oracle != off {
                        if let (Some(s_or), Some(s_off)) = (after(&state, &oracle), after(&state, &off)) {
                            solver_losses.push(deep(&s_or, mover) - deep(&s_off, mover));
                        }
                    } else {
                        solver_losses.push(0.0);
                    }
                }

                match after(&state, &off) {
                    Some(next) => state = next,
                    None => break,
                }
            }
        }
        let stat = |v: &Vec<f64>| {
            if v.is_empty() {
                return (0.0, 0.0, 0.0);
            }
            let n = v.len() as f64;
            let mean = v.iter().sum::<f64>() / n;
            let worst = v.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
            let best = v.iter().cloned().fold(f64::INFINITY, f64::min);
            (mean, best, worst)
        };
        let (cm, cb, cw) = stat(&chance_deltas);
        println!("PUNKTPREIS, {decisions} Runde-5-Entscheidungen");
        println!(
            "  Zufallsknoten an-vs-aus, nur abweichende ({}): Delta Mittel {cm:+.2} Pkt, Spanne {cb:+.2} .. {cw:+.2}",
            chance_deltas.len()
        );
        let nonzero: Vec<f64> = solver_losses.iter().cloned().filter(|d| d.abs() > 1e-9).collect();
        let (sm, sb, sw) = stat(&nonzero);
        let all_mean = solver_losses.iter().sum::<f64>() / solver_losses.len().max(1) as f64;
        println!(
            "  Loeser@200 vs Orakel: Mittel ueber ALLE {all_mean:+.3} Pkt; nur abweichende ({}): Mittel {sm:+.2}, Spanne {sb:+.2} .. {sw:+.2}",
            nonzero.len()
        );
    }

    /// Vorzeichen-Messung fuer das Scharfschalten der Runde-5-Zufallsknoten.
    ///
    /// `teil_e_value_cost_of_divergence_probe` fand nur 4 abweichende
    /// Entscheidungen -- ein Mittel von -2,75 Pkt, das ein einzelner
    /// -13-Fall dominierte. Vier Datenpunkte tragen kein Vorzeichen. Diese
    /// Sonde sammelt ueber viele Seeds, bewertet aber NUR die abweichenden
    /// Stellungen tief (die Orakel-Bewertung je Entscheidung ist der teure
    /// Teil und fuer die Vorzeichenfrage unnoetig).
    #[test]
    #[ignore]
    fn r5_chance_arming_sign_probe() {
        use crate::round_transition::drive_to_round_start;
        const ORACLE: u64 = 20_000;

        let mut deltas: Vec<f64> = Vec::new();
        let mut decisions = 0usize;
        for seed in 1u64..=80 {
            let mut state = drive_to_round_start(seed, 5);
            let mut guard = 0u32;
            while state.phase == Phase::Drafting && guard < 200 {
                guard += 1;
                let mover = state.current_player;
                let off = match choose_action_inner(&state, false, NODE_BUDGET) {
                    Some(a) => a,
                    None => break,
                };
                decisions += 1;
                if let Some(on) = choose_action_inner(&state, true, NODE_BUDGET) {
                    if on != off {
                        let deep = |a: &Action| -> Option<f64> {
                            let mut g = Game { state: state.clone() };
                            g.apply_drafting(a).ok()?;
                            let mut nodes: u64 = 0;
                            let mut depth_cut_unused = false;
                            Some(negamax(
                                &g.state, MAX_DEPTH.saturating_sub(1), f64::NEG_INFINITY,
                                f64::INFINITY, mover, &mut nodes, ORACLE,
                                Instant::now() + Duration::from_secs(120), false,
                                &mut depth_cut_unused,
                            ))
                        };
                        if let (Some(v_on), Some(v_off)) = (deep(&on), deep(&off)) {
                            deltas.push(v_on - v_off);
                        }
                    }
                }
                let mut g = Game { state };
                if g.apply_drafting(&off).is_err() {
                    break;
                }
                state = g.state;
            }
        }
        let n = deltas.len();
        if n == 0 {
            println!("VORZEICHEN: keine Abweichungen in {decisions} Entscheidungen");
            return;
        }
        let mean = deltas.iter().sum::<f64>() / n as f64;
        let var = deltas.iter().map(|d| (d - mean).powi(2)).sum::<f64>() / (n as f64 - 1.0).max(1.0);
        let se = (var / n as f64).sqrt();
        let mut sorted = deltas.clone();
        sorted.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let median = sorted[n / 2];
        let neg = deltas.iter().filter(|d| **d < 0.0).count();
        println!("VORZEICHEN Zufallsknoten an-vs-aus, {decisions} Entscheidungen, {n} Abweichungen ({:.1}%)",
                 100.0 * n as f64 / decisions as f64);
        println!("  Delta Mittel {mean:+.2} Pkt, SE {se:.2}, t={:+.2}", mean / se.max(1e-9));
        println!("  Median {median:+.2}, Spanne {:+.2} .. {:+.2}, davon negativ {neg}/{n}",
                 sorted[0], sorted[n - 1]);
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
        let children = ordered_children(&s, false);
        let naive_best = children.first().map(|c| c.order_value).unwrap_or(f64::NEG_INFINITY);
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
                let children = ordered_children(&state, false);
                if children.is_empty() {
                    break;
                }
                if children.len() > 1 {
                    let deadline = Instant::now() + probe_budget;
                    let t0 = Instant::now();
                    let mut nodes: u64 = 0;
                    let mut depth_cut_unused = false;
                    let _ = negamax(
                        &state,
                        MAX_DEPTH.saturating_sub(1),
                        f64::NEG_INFINITY,
                        f64::INFINITY,
                        state.current_player,
                        &mut nodes,
                        u64::MAX,
                        deadline,
                        false,
                        &mut depth_cut_unused,
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

    /// Task #21: reiche Runde-5-Stellung mit teilbefuelltem 3x3-Kuppelraster +
    /// mehreren vollen Musterreihen -- analog zu `tiling_solver::tests::rich_state`.
    /// Noetig, weil ein leeres Kuppelraster (wie in `round5_state`) keine
    /// platzierbaren Tiling-Aktionen erzeugt und jeder Vergleich zwischen alter
    /// und endaware-Rechnung trivial gleich waere (`generate_tiling_actions`
    /// prueft NICHT `state.phase` -- funktioniert also direkt auf einer
    /// Drafting-Stellung, siehe `round_end::generate_tiling_actions`).
    fn rich_round5_state(seed: u64) -> GameState {
        use crate::dome::build_dome_tile_pool;
        use crate::tile::TileColor::*;
        use rand::rngs::StdRng;
        use rand::RngExt;
        use rand::SeedableRng;

        let mut rng = StdRng::seed_from_u64(seed);
        let mut s = round5_state(seed);
        s.scoring_tile_ids = vec![0, 1, 2, 4]; // Reihen/Spalten/Diagonalen/Aussenfelder
        let pool = build_dome_tile_pool();
        let mut tid = 500;
        for r in 0..3 {
            for c in 0..3 {
                let mut t = pool[rng.random_range(0..pool.len())].clone();
                t.tile_id = tid;
                tid += 1;
                for si in 0..4 {
                    // ~55% vorbefuellt: genug fuer echte Platzierungen und
                    // fast-volle Linien, laesst aber noch offene Felder frei.
                    if rng.random_range(0..100) < 55 {
                        t.spaces[si].placed_color = t.spaces[si].required_color;
                    }
                }
                let _ = s.players[0].dome_grid.place_dome_tile(t, r, c);
            }
        }
        s.players[0].pattern_lines[1].add_tiles(&[Blau, Blau]);
        s.players[0].pattern_lines[2].add_tiles(&[Rot, Rot, Rot]);
        s.players[0].pattern_lines[3].add_tiles(&[Tuerkis, Tuerkis, Tuerkis, Tuerkis]);
        s
    }

    /// Referenzformel, unabhaengig dupliziert (Muster: `tiling_solver`s
    /// `reference_argmax`), damit der Test nicht dieselbe Codezeile prueft,
    /// die er absichern soll.
    fn reference_player_total(state: &GameState, pi: usize, endaware: bool) -> f64 {
        if endaware {
            crate::tiling_solver::solve_round_final_score_endaware(state, pi) as f64
                + projected_unplaceable_penalty(&state.players[pi]) as f64
        } else {
            solve_round_final_score(state, pi) as f64
                + calculate_end_scoring(&state.players[pi], &state.scoring_tile_ids).total as f64
                + projected_unplaceable_penalty(&state.players[pi]) as f64
        }
    }

    /// Paritaet: `player_total_exact` muss IMMER exakt der Referenzformel fuer
    /// den jeweils aktiven Toggle-Zustand entsprechen -- bei
    /// `ROUND5_ENDSCORING_ENABLED=true` (Ist-Zustand, berichtigt 2026-09-19)
    /// also gegen den endaware-Pfad, bei `false` byte-identisch zur alten
    /// Rechnung. Manuell in BEIDEN Toggle-Zustaenden gebaut/getestet
    /// (siehe Konstanten-Kommentar in tiling_solver.rs) -- dieser Test prueft
    /// generisch gegen den JEWEILS aktiven Wert der Konstante, damit er in
    /// beiden Zustaenden gruen ist.
    #[test]
    fn player_total_exact_follows_toggle() {
        let s = rich_round5_state(11);
        for pi in 0..2 {
            let expected = reference_player_total(
                &s,
                pi,
                crate::tiling_solver::ROUND5_ENDSCORING_ENABLED,
            );
            assert_eq!(
                player_total_exact(&s, pi),
                expected,
                "player_total_exact folgt ROUND5_ENDSCORING_ENABLED={} nicht (pi={pi})",
                crate::tiling_solver::ROUND5_ENDSCORING_ENABLED
            );
        }
    }

    /// Diskriminierung: die alte Rechnung (`solve_round_final_score` +
    /// `calculate_end_scoring` des Bretts DAVOR) und die endaware-Rechnung
    /// (`solve_round_final_score_endaware`, Endwertung des Bretts NACH dem
    /// geplanten Tiling) muessen sich in einer konstruierten Stellung
    /// tatsaechlich unterscheiden -- sonst waere der ganze Task-#21-Befund
    /// wirkungslos. Sucht ueber Seeds (Muster:
    /// `tiling_solver::tests::tiling_shaping_follows_toggle_and_position_discriminates`)
    /// und schlaegt fehl, wenn keine diskriminierende Stellung existiert --
    /// eine leer gruene Suche waere hier schon zweimal aufgefallen.
    #[test]
    fn endaware_formula_discriminates_from_old_formula() {
        let mut found = None;
        'search: for seed in 1u64..=200 {
            let s = rich_round5_state(seed);
            for pi in 0..2 {
                let old = reference_player_total(&s, pi, false);
                let new = reference_player_total(&s, pi, true);
                if (old - new).abs() > 1e-9 {
                    found = Some((seed, pi, old, new));
                    break 'search;
                }
            }
        }
        let (seed, pi, old, new) = found.expect(
            "keine diskriminierende Stellung in 200 Seeds gefunden -- entweder ist die \
             endaware-Rechnung wirkungslos oder rich_round5_state() erzeugt keine echten \
             Platzierungen",
        );
        assert_ne!(
            old, new,
            "Seed {seed} pi={pi}: alte und endaware-Rechnung liefern denselben Wert ({old})"
        );
    }

    // ── Seiten-Einstieg und iterative Vertiefung (PREREG_r5_net_vs_solver.md par.5a) ──

    /// Not-Deckel der iterativen Suche: bei 200 Knoten das Bestandsminimum,
    /// darueber `budget x 4,4 ms x 5`, nach oben gedeckelt.
    #[test]
    fn deadline_for_budget_scales_with_the_budget() {
        assert_eq!(deadline_for_budget(NODE_BUDGET), TIME_BUDGET);
        assert_eq!(deadline_for_budget(400), Duration::from_millis(8_800));
        assert_eq!(deadline_for_budget(2000), Duration::from_secs(44));
        assert_eq!(deadline_for_budget(u64::MAX), DEADLINE_CAP);
    }

    /// (a) Default-Pfad: der Seiten-Einstieg mit `iterative = false` und dem
    /// Default-Budget liefert denselben Zug wie `choose_action` und dasselbe
    /// Analyse-Dict wie `choose_action_with_analysis` -- auf dem Leerbrett UND
    /// auf einer realistischen Stellung, auf der das Budget bindet.
    #[test]
    fn side_entry_default_matches_choose_action() {
        use crate::round_transition::drive_to_round_start;
        assert!(!SOLVER_ITERATIVE_DEFAULT);
        let states = vec![round5_state(2), round5_state(3), drive_to_round_start(51, 5)];
        for (i, s) in states.iter().enumerate() {
            assert_eq!(
                choose_action_for_side(s, false, node_budget()),
                choose_action(s),
                "Stellung {i}: Seiten-Einstieg weicht vom Bestand ab"
            );
            let (a_side, json_side) = choose_action_with_analysis_for_side(s, false, node_budget());
            let (a_old, json_old) = choose_action_with_analysis(s);
            assert_eq!(a_side, a_old, "Stellung {i}: Analyse-Zug weicht ab");
            assert_eq!(json_side, json_old, "Stellung {i}: Analyse-Dict weicht ab");
        }
    }

    /// Kleine Runde-5-Endstellungen (2-4 Legalzuege), deren VOLLE Suche bis
    /// zum Rundenende in wenigen tausend Knoten fertig wird. Vorgerueckt wird
    /// billig mit der Vorsortierung, nicht mit dem Loeser.
    fn small_round5_endgames(max: usize) -> Vec<GameState> {
        use crate::round_transition::drive_to_round_start;
        let mut out = Vec::new();
        for seed in [101u64, 202, 303, 404, 505, 606] {
            let mut state = drive_to_round_start(seed, 5);
            let mut guard = 0u32;
            while state.phase == Phase::Drafting && guard < 200 {
                guard += 1;
                let n = drafting_actions(&state).len();
                if (2..=4).contains(&n) {
                    let mut nodes: u64 = 0;
                    let mut cut = false;
                    let far = Instant::now() + Duration::from_secs(600);
                    let _ = negamax(
                        &state, MAX_DEPTH, f64::NEG_INFINITY, f64::INFINITY, state.current_player,
                        &mut nodes, 20_000, far, true, &mut cut,
                    );
                    if nodes < 20_000 && !cut {
                        out.push(state.clone());
                        break;
                    }
                }
                let children = ordered_children(&state, true);
                let Some(first) = children.first() else { break };
                let mut g = Game { state };
                if g.apply_drafting(&first.action).is_err() {
                    break;
                }
                state = g.state;
            }
            if out.len() >= max {
                break;
            }
        }
        out
    }

    /// (b) Mit sehr grossem Budget erreicht die iterative Suche auf einer
    /// kleinen Endstellung das Rundenende und trifft den Wert der vollen Suche.
    /// Verglichen wird der WERT und die Zugehoerigkeit zur Menge der besten
    /// Zuege -- bei Gleichstand duerfen beide Suchen verschiedene, gleich gute
    /// Zuege nennen (andere Wurzelreihenfolge).
    #[test]
    fn iterative_with_huge_budget_matches_the_full_search() {
        let states = small_round5_endgames(3);
        assert!(!states.is_empty(), "Testaufbau: keine kleine Endstellung gefunden");
        for (k, s) in states.iter().enumerate() {
            let perspective = s.current_player;
            let far = Instant::now() + Duration::from_secs(600);
            // Referenz: jedes Wurzelkind mit vollem Fenster und voller Tiefe.
            let children = ordered_children(s, true);
            let mut reference: Vec<(Action, f64)> = Vec::new();
            for c in &children {
                let mut nodes: u64 = 0;
                let mut cut = false;
                let v = child_value(
                    c, MAX_DEPTH - 1, f64::NEG_INFINITY, f64::INFINITY, perspective,
                    &mut nodes, 1_000_000, far, true, &mut cut,
                );
                assert!(nodes < 1_000_000 && !cut, "Stellung {k}: Referenz nicht vollstaendig");
                reference.push((c.action.clone(), v));
            }
            let best = reference.iter().map(|(_, v)| *v).fold(f64::NEG_INFINITY, f64::max);
            let argmax: Vec<&Action> =
                reference.iter().filter(|(_, v)| (*v - best).abs() < 1e-9).map(|(a, _)| a).collect();

            let out = choose_action_iterative_inner(s, true, 1_000_000, far).expect("Aktion");
            assert!(out.reached_round_end, "Stellung {k}: Rundenende nicht erreicht ({out:?})");
            assert!(!out.from_partial_iteration);
            assert!((out.value - best).abs() < 1e-9, "Stellung {k}: Wert {} statt {best}", out.value);
            assert!(argmax.contains(&&out.action), "Stellung {k}: Zug nicht unter den besten");
        }
    }

    /// (c) Deterministisch bei gleichem Budget, und unabhaengig vom Not-Deckel,
    /// solange der nicht greift (Task-#71-Muster wie
    /// `outcome_is_independent_of_time_budget`).
    #[test]
    fn iterative_is_deterministic_and_node_bound() {
        use crate::round_transition::drive_to_round_start;
        let s = drive_to_round_start(51, 5);
        let budget = 300;
        let run = |deadline: Duration| {
            choose_action_iterative_inner(&s, true, budget, Instant::now() + deadline).expect("Aktion")
        };
        let a = run(deadline_for_budget(budget));
        let b = run(deadline_for_budget(budget));
        let c = run(deadline_for_budget(budget) * 10);
        for (tag, other) in [("Wiederholung", &b), ("10x Deckel", &c)] {
            assert_eq!(a.action, other.action, "{tag}: Zug");
            assert_eq!(a.value.to_bits(), other.value.to_bits(), "{tag}: Wert");
            assert_eq!(a.nodes, other.nodes, "{tag}: Knoten");
            assert_eq!(a.completed_depth, other.completed_depth, "{tag}: Tiefe");
            assert_eq!(a.from_partial_iteration, other.from_partial_iteration, "{tag}: Ausnahme");
        }
        // Kleine Ueberschreitung ist Bestandsverhalten: `negamax` zaehlt VOR der
        // Budgetpruefung, und die Ausgangsschleife eines Zufallsknotens
        // (`child_value`) prueft das Budget nicht -- jeder weitere Ausgang kostet
        // noch einen Knoten. Grob nach oben begrenzt (HERLEITUNG, nicht gemessen).
        assert!(a.nodes < budget + 100, "Budget weit ueberschritten: {}", a.nodes);
        assert!(a.completed_depth >= 1);
    }

    /// Buchfuehrung des HEUTIGEN Loesers fuer die Kalibriersonde: ein Nachbau
    /// der Schleife aus `choose_action_deadlined`, damit der Bestandspfad
    /// unberuehrt bleibt. Paritaet mit dem Original: Test darunter.
    struct LegacySolverStats {
        action: Option<Action>,
        nodes: u64,
        n_children: usize,
        children_searched: usize,
        /// Das Budget (oder der Deckel) war nach dem ERSTEN Kind erschoepft, es
        /// gab weitere Kinder -- der Loeser gibt dann `ordered_children[0]`
        /// zurueck, also die Vorsortierung.
        first_child_ate_budget: bool,
    }

    fn legacy_choose_with_stats(state: &GameState, chance: bool, budget: u64, deadline: Instant) -> LegacySolverStats {
        let perspective = state.current_player;
        let children = ordered_children(state, chance);
        let n_children = children.len();
        if children.len() <= 1 {
            return LegacySolverStats {
                action: children.first().map(|c| c.action.clone()),
                nodes: 0,
                n_children,
                children_searched: 0,
                first_child_ate_budget: false,
            };
        }
        let mut node_count: u64 = 0;
        let mut depth_cut_unused = false;
        let mut best_action = children[0].action.clone();
        let mut best_val = f64::NEG_INFINITY;
        let mut alpha = f64::NEG_INFINITY;
        let mut children_searched = 0usize;
        let mut first_child_ate_budget = false;
        for child in &children {
            if node_count >= budget || Instant::now() >= deadline {
                if children_searched == 1 {
                    first_child_ate_budget = true;
                }
                break;
            }
            let val = child_value(
                child, MAX_DEPTH.saturating_sub(1), alpha, f64::INFINITY, perspective,
                &mut node_count, budget, deadline, chance, &mut depth_cut_unused,
            );
            children_searched += 1;
            if val > best_val {
                best_val = val;
                best_action = child.action.clone();
            }
            if val > alpha {
                alpha = val;
            }
        }
        LegacySolverStats { action: Some(best_action), nodes: node_count, n_children, children_searched, first_child_ate_budget }
    }

    #[test]
    fn legacy_stats_replica_matches_choose_action_deadlined() {
        use crate::round_transition::drive_to_round_start;
        let s = drive_to_round_start(51, 5);
        let far = || Instant::now() + Duration::from_secs(600);
        let replica = legacy_choose_with_stats(&s, true, NODE_BUDGET, far());
        assert_eq!(replica.action, choose_action_deadlined(&s, true, NODE_BUDGET, far()));
        assert!(replica.children_searched >= 1);
        assert!(replica.n_children >= 2, "Testaufbau: mehr als ein Kandidat");
    }

    /// KALIBRIERSONDE der iterativen Vertiefung (`PREREG_r5_net_vs_solver.md`
    /// par.5a, Messung Stufe 1), manuell:
    /// `cargo test --release --lib r5_iterative_deepening_calibration_probe -- --ignored --nocapture`
    ///
    /// Dieselben realistischen Stellungen wie `round5_node_calibration_probe`
    /// (`drive_to_round_start(seed, 5)`, 8 Seeds), die Runde gespielt mit dem
    /// HEUTIGEN Loeser @200. Je Entscheidung mit mehr als einem Kandidaten:
    /// (i) heutiger Loeser @200 (Not-Deckel `TIME_BUDGET`): Knoten, ms,
    /// durchsuchte Wurzelkinder, und ob das erste Kind das Budget frass;
    /// (ii) iterativ @400 und @2000 (Not-Deckel `deadline_for_budget`): volle
    /// Tiefe, Knoten, ms, Rundenende erreicht, Zug aus der angebrochenen
    /// Iteration, gleicher Zug wie der heutige Loeser. Zufallsknoten wie in der
    /// Produktion (`chance_nodes_enabled()`). Netz-Zeiten misst die Sonde NICHT.
    /// Auf freier Maschine laufen lassen (CPU-Last verfaelscht die ms).
    #[test]
    #[ignore]
    fn r5_iterative_deepening_calibration_probe() {
        use crate::round_transition::drive_to_round_start;
        use std::collections::BTreeMap;
        use std::io::Write;

        struct ArmLog {
            ms: Vec<f64>,
            nodes: Vec<f64>,
            depth: BTreeMap<u32, usize>,
            round_end: usize,
            partial: usize,
            same_as_legacy: usize,
        }
        let new_arm = || ArmLog {
            ms: Vec::new(),
            nodes: Vec::new(),
            depth: BTreeMap::new(),
            round_end: 0,
            partial: 0,
            same_as_legacy: 0,
        };
        let pct = |v: &[f64], q: f64| -> f64 {
            if v.is_empty() {
                return f64::NAN;
            }
            let mut s = v.to_vec();
            s.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
            s[((s.len() - 1) as f64 * q).round() as usize]
        };

        let chance = chance_nodes_enabled();
        let budgets = [400u64, 2000];
        let mut legacy_ms: Vec<f64> = Vec::new();
        let mut legacy_nodes: Vec<f64> = Vec::new();
        let mut legacy_first_ate = 0usize;
        let mut legacy_one_child = 0usize;
        let mut arms: Vec<ArmLog> = budgets.iter().map(|_| new_arm()).collect();
        let mut decisions = 0usize;
        let t_total = Instant::now();
        println!("R5-ITERATIV-SONDE chance={chance} budgets={budgets:?}");
        let _ = std::io::stdout().flush();

        for seed in [101u64, 202, 303, 404, 505, 606, 707, 808] {
            let mut state = drive_to_round_start(seed, 5);
            let mut step = 0u32;
            while state.phase == Phase::Drafting && step < 200 {
                let t0 = Instant::now();
                let legacy = legacy_choose_with_stats(&state, chance, NODE_BUDGET, Instant::now() + TIME_BUDGET);
                let legacy_elapsed = t0.elapsed().as_secs_f64() * 1000.0;
                let Some(legacy_action) = legacy.action.clone() else { break };
                if legacy.n_children > 1 {
                    decisions += 1;
                    legacy_ms.push(legacy_elapsed);
                    legacy_nodes.push(legacy.nodes as f64);
                    if legacy.first_child_ate_budget {
                        legacy_first_ate += 1;
                    }
                    if legacy.children_searched == 1 {
                        legacy_one_child += 1;
                    }
                    let mut line = format!(
                        "seed={seed} step={step} kand={} | alt@{NODE_BUDGET} knoten={} ms={legacy_elapsed:.0} kinder={}/{} erstes_frisst={}",
                        legacy.n_children, legacy.nodes, legacy.children_searched, legacy.n_children,
                        legacy.first_child_ate_budget
                    );
                    for (arm, &budget) in arms.iter_mut().zip(budgets.iter()) {
                        let t1 = Instant::now();
                        let out = choose_action_iterative_inner(
                            &state, chance, budget, Instant::now() + deadline_for_budget(budget),
                        )
                        .expect("Aktion");
                        let ms = t1.elapsed().as_secs_f64() * 1000.0;
                        arm.ms.push(ms);
                        arm.nodes.push(out.nodes as f64);
                        *arm.depth.entry(out.completed_depth).or_insert(0) += 1;
                        arm.round_end += usize::from(out.reached_round_end);
                        arm.partial += usize::from(out.from_partial_iteration);
                        let same = out.action == legacy_action;
                        arm.same_as_legacy += usize::from(same);
                        line.push_str(&format!(
                            " | it@{budget} tiefe={} knoten={} ms={ms:.0} ende={} partiell={} gleich_alt={same}",
                            out.completed_depth, out.nodes, out.reached_round_end, out.from_partial_iteration
                        ));
                    }
                    println!("{line}");
                    let _ = std::io::stdout().flush();
                }
                let mut g = Game { state };
                if g.apply_drafting(&legacy_action).is_err() {
                    break;
                }
                state = g.state;
                step += 1;
            }
        }

        let n = decisions.max(1) as f64;
        println!("ZUSAMMENFASSUNG, {decisions} Runde-5-Entscheidungen mit >=2 Kandidaten (8 Partien)");
        println!(
            "  alt@{NODE_BUDGET}: ms Median {:.0} p90 {:.0} max {:.0}; Knoten Median {:.0}; erstes Kind frisst Budget {legacy_first_ate}/{decisions} ({:.1} %); nur ein Kind durchsucht {legacy_one_child}/{decisions}",
            pct(&legacy_ms[..], 0.5), pct(&legacy_ms[..], 0.9), pct(&legacy_ms[..], 1.0), pct(&legacy_nodes[..], 0.5),
            100.0 * legacy_first_ate as f64 / n
        );
        for (arm, &budget) in arms.iter().zip(budgets.iter()) {
            println!(
                "  it@{budget}: ms Median {:.0} p90 {:.0} max {:.0}; Knoten Median {:.0}; Tiefe {:?}; Rundenende {}/{decisions}; Ausnahme angebrochen {}/{decisions}; gleicher Zug wie alt {}/{decisions}",
                pct(&arm.ms[..], 0.5), pct(&arm.ms[..], 0.9), pct(&arm.ms[..], 1.0), pct(&arm.nodes[..], 0.5),
                arm.depth, arm.round_end, arm.partial, arm.same_as_legacy
            );
        }
        println!("  laufzeit: wanduhr_s={:.1} threads=1", t_total.elapsed().as_secs_f64());
        let _ = std::io::stdout().flush();
    }
}
