//! AlphaZero-PUCT-Suche über die Drafting-Phase (Network-Modus, Phase B).
//!
//! Ähnliche Grundstruktur wie die Heuristik-MCTS (`crate::mcts`), aber
//! bewusst OHNE deren Force-Reply-Garantie/Nachlauf-Schließung (Tiefe 0/1
//! erzwang früher eine simulierte Gegner-Antwort vor weiterem Breitern,
//! plus ein Nachlauf-Pass für Fälle, die PUCT nie erneut besucht hätte) --
//! entfernt als unnötige Komplexität für den Netz-Pfad (Nutzer-Entscheidung).
//! `crate::mcts` behält beides (Stufe 1 bleibt unverändert). Sonst:
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

use rand::seq::SliceRandom;
use rand::{Rng, RngExt};
use serde_json::{json, Value};

#[cfg(test)]
use crate::features::action_to_id;
use crate::game::{drafting_actions, Game};
use crate::mcts::{label_search_move, SearchMove};
use crate::moves::{Action, TakeSource};
use crate::net::{softmax, Net};
use crate::scoring::scoring_progress;
use crate::self_play::action_to_env_dict;
use crate::state::{GameState, Phase};
use crate::tile::TileColor;

/// Aktionsraum-Größe (= `config.NUM_ACTIONS`). Baustein B: 328 (Stone+Tiling)
/// + 27 (choose_dome_slot) + 36 (choose_draw_stack_slot) + 4 (choose_dome_rotation)
/// + 6 (use_chips) + 4 (bonus_chip) + 1 (dome_stack_peek) = 406.
pub(crate) const NUM_ACTIONS: usize = 406;
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

/// Rundenübergang per Chance-Node-Sampling bewerten (`round_transition.rs`)
/// statt eines einzelnen Netz-Blattwerts, nur wirksam bei `ACTIVE_LEAF=Net`.
/// Standardmäßig AUS -- siehe `round_transition.rs`-Modul-Kommentar (Phase 2
/// im Fahrplan, erst nach einer belegten Val-R²-Verbesserung über den
/// Trainingsziel-Pfad aktivieren, siehe `evaluations/STATUS.md`). Eine
/// Zeile hier auf `true` aktiviert die Live-Suche-Integration jederzeit
/// wieder, ohne Funktionssignaturen anzufassen (gleiches Muster wie
/// `ACTIVE_LEAF`).
pub const ROUND_TRANSITION_SAMPLING: bool = false;

/// KataGo-Stil geblendete Utility (siehe `project_v8d_value_head_root_cause`-
/// Memory / `evaluations/STATUS.md`): `value_head`s R² ist stark rundenabhängig
/// (~0.03 in Runde 1, ~0.62 in Runde 5) — die Suche vertraut ihm aber an jedem
/// Blatt gleichermaßen. `points_head`/`points_forecast` (kontinuierliches
/// Punktestand-Ziel, siehe `neural_net.py::VALUE_SCALE`/`VALUE_OPP_EPSILON`)
/// generalisiert historisch durchgehend besser (R²≈0.33-0.44) als `value`.
/// KataGo blendet genau so einen Score-basierten Utility-Term MIT der
/// Sieg-Wahrscheinlichkeit in die tatsächliche, such-treibende Utility (nicht
/// nur als Trainings-Nebenverlust) — siehe
/// github.com/lightvector/KataGo/blob/master/docs/KataGoMethods.md. Gewicht
/// hier bewusst ohne Vorab-Tuning auf 0.5 (gleichgewichtete Mischung) gesetzt;
/// erster Test, mit echten Arena-Ergebnissen gegenkalibrieren (0.0 = alter
/// reiner Value-Leaf-Zustand, 1.0 = reiner Points-Leaf).
///
/// GETESTET (2026-07-19, v9b_domeonly, 150 Sims, SPRT): weder 0.5 (1:14,
/// Score 19.5 vs 49.7, Floor 27.0 vs 10.5) noch 1.0 (0:12, Score 14.2 vs
/// 55.0, Floor 25.4 vs 10.1) schließen die Lücke zum 0.0-Baseline (0:12,
/// Score 13.7-18.2 vs 44.4-46.8, Floor ~20-25) — Floor-Strafe bleibt bei
/// ALLEN drei Werten im selben erhöhten Bereich, unabhängig von der
/// Blattwert-Formel. Auf 0.0 zurückgesetzt (= vorheriger, besser abgesicherter
/// Zustand); Code bleibt verfügbar für spätere Rekalibrierung, siehe
/// `project_v8d_value_head_root_cause`-Memory für die volle Diskussion.
pub const POINTS_UTILITY_WEIGHT: f64 = 0.0;

// ── Task #28 (`evaluations/PREREG_task28_aggression.md`): Score-/Denial-
// Utility -- LAUFZEIT-konfigurierbarer Nachfolger des toten `POINTS_UTILITY_
// WEIGHT`-Blends oben (die Konstante bleibt bewusst stehen, siehe deren
// GETESTET-Historie -- dieser neue Blend ERSETZT sie an der Blend-Stelle
// `blended_leaf_win_prob`, loescht sie aber nicht). Unterschied zum alten
// Blend: nicht nur EIGENE Punkte einmischen (das waere reine "Gier"), sondern
// per separatem `opp_points`-Kopf explizit GEGNER-Punkte abziehen ("Denial"),
// gewichtet mit `lambda_aggr`. Siehe PREREG Abschnitt "Minimal-invasiver
// Zuschnitt" Punkt 4 fuer die volle Herleitung.

/// **0 seit Schema 20 (Nutzer-Entscheid 2026-08-10).** GESCHICHTE: der
/// `points_head` war NICHT rein auf Eigenpunkte trainiert, sondern auf
/// `tanh(own/SCALE) - 0.1*tanh(opp/SCALE)`. Dieser Gegner-Anteil liess sich
/// nur ueber `opp_aware_points_utility` algebraisch herausrechnen
/// (`own_pts = pts_raw + VALUE_OPP_EPSILON*opp_raw`) -- und dieser Pfad liegt
/// hinter dem `w == 0.0`-Kurzschluss in `blended_leaf_win_prob_with`, war also
/// toter Code. Das Ziel ist jetzt rein own, der Term entfaellt.
///
/// Die Konstante bleibt auf 0.0 stehen, statt die Formel umzuschreiben: dann
/// degeneriert die Rueckgewinnung automatisch korrekt zu `own_pts = pts_raw`,
/// UND `engine_config_json` zeigt die Aenderung an (dieselbe Praxis wie
/// `POINTS_UTILITY_WEIGHT = 0.0` darueber). Ein Modell, das VOR Schema 20
/// trainiert wurde, traegt den Anteil weiter im Kopf -- fuer solche Modelle
/// waere 0.1 der richtige Wert, weshalb die Geschichte hier stehenbleibt.
pub(crate) const VALUE_OPP_EPSILON: f64 = 0.0;

/// Laufzeit-Zelle fuer `MOSAIC_POINTS_UTILITY_W` -- `OnceLock` initialisiert
/// EINMALIG aus der Env-Var (Prozessstart-Default, siehe `read_f64_env`),
/// der innere `AtomicU64` (f64-Bitmuster via `to_bits`/`from_bits`) ist
/// danach beliebig oft NEU setzbar -- GUI-Live-Regler (`set_aggression_
/// params`, PyO3-Bindung in `lib.rs`) schreibt hier hinein, OHNE dass die
/// Suche pro Knoten neu parst (`Ordering::Relaxed` reicht: kein weiterer
/// Zustand haengt kausal an diesem Wert, ein kurzzeitig "gemischter" Wert
/// zwischen zwei laufenden Suchen ist unkritisch, siehe `points_utility_w()`).
static POINTS_UTILITY_W: std::sync::OnceLock<std::sync::atomic::AtomicU64> =
    std::sync::OnceLock::new();

/// Laufzeit-Zelle fuer `MOSAIC_AGGR_LAMBDA`, gleiches Muster wie
/// `POINTS_UTILITY_W` oben (siehe `aggr_lambda()`).
static AGGR_LAMBDA: std::sync::OnceLock<std::sync::atomic::AtomicU64> = std::sync::OnceLock::new();

/// Interne Zellen-Getter (initialisieren aus der Env-Var beim ERSTEN Zugriff,
/// liefern danach immer dieselbe `AtomicU64`-Referenz) -- getrennt von den
/// oeffentlichen `points_utility_w()`/`aggr_lambda()`-Lese-Funktionen, damit
/// `set_aggression_params` dieselbe Zelle zum Schreiben greifen kann, ohne
/// den Bit-Umweg ueber eine zweite `OnceLock::get_or_init`-Doku zu noeten.
fn points_utility_w_cell() -> &'static std::sync::atomic::AtomicU64 {
    POINTS_UTILITY_W.get_or_init(|| {
        std::sync::atomic::AtomicU64::new(read_f64_env("MOSAIC_POINTS_UTILITY_W", 0.0).to_bits())
    })
}

fn aggr_lambda_cell() -> &'static std::sync::atomic::AtomicU64 {
    AGGR_LAMBDA.get_or_init(|| {
        std::sync::atomic::AtomicU64::new(read_f64_env("MOSAIC_AGGR_LAMBDA", 0.0).to_bits())
    })
}

/// Markiert, ob die "Modell hat keinen opp_points-Kopf, obwohl w>0"-Warnung
/// bereits einmal geloggt wurde (verhindert Log-Spam ueber tausende
/// PUCT-Blattauswertungen einer einzigen Suche).
static WARNED_NO_OPP_HEAD: std::sync::OnceLock<()> = std::sync::OnceLock::new();

/// Liest eine `MOSAIC_*`-Env-Var einmalig als `f64` -- fehlend/leer -> Default
/// (kein Fehler), nicht parsbar -> Default + EINMALIGE Warnung auf stderr
/// (kein Panic; Laufzeit-Konfiguration darf einen Prozess nie abstuerzen
/// lassen). Selbes Muster wie die bestehenden Python-seitigen `MOSAIC_*`-Env-
/// Var-Leser (z.B. `config.py::MOSAIC_DATA_DIR`, `player_profiles.py::
/// MOSAIC_PROFILES_PATH`) -- hier auf Rusts `std::env::var` uebertragen.
pub(crate) fn read_f64_env(name: &str, default: f64) -> f64 {
    match std::env::var(name) {
        Ok(s) => match s.trim().parse::<f64>() {
            Ok(v) => v,
            Err(_) => {
                eprintln!("⚠️  {name}={s:?} nicht als Zahl lesbar -- verwende Default {default}");
                default
            }
        },
        Err(_) => default,
    }
}

thread_local! {
    /// Test-Override fuer [`root_child_q_logging_enabled`] -- thread-lokal,
    /// gleiches Muster wie `tiling_solver::STATS_OVERRIDE`/`CACHE_OVERRIDE`:
    /// verhindert, dass ein Test die Prozess-weite `OnceLock`-gecachte
    /// Env-Var fuer ALLE parallel laufenden `cargo test`-Threads festlegt
    /// (`std::env::set_var` + `OnceLock::get_or_init` racet sonst gegen
    /// andere Test-Threads, die den Wert evtl. schon gelesen/gecacht haben).
    static ROOT_CHILD_Q_OVERRIDE: std::cell::Cell<Option<bool>> = std::cell::Cell::new(None);
}

/// `MOSAIC_ROOT_CHILD_Q=0` schaltet das Task-#35-Wurzelkind-Q-Logging ab
/// (Default AN, siehe STATUS.md Task #35 "Ranking-Loss auf Geschwister-Q").
/// Begruendung fuer den Default: `root_completed_q_raw`/`average_completed_q_raw`
/// serialisieren nur Werte, die `completed_q_per_candidate` fuer die ohnehin
/// bestehende `policy`-Softmax-Zielverteilung SCHON berechnet -- kein
/// zusaetzlicher Suchaufwand (keine weiteren Sims, kein weiterer Netz-Eval),
/// nur ein zusaetzlicher `Vec`-Clone kleiner `f64`-Listen je Drafting-
/// Entscheid. Abgeschaltet: `self_play.rs` prueft dieses Flag VOR dem
/// `root_child_q`-JSON-Insert (nicht hier in der Suche selbst) -- das
/// Self-Play-JSON ist dann byte-identisch zum Vor-#35-Format.
pub(crate) fn root_child_q_logging_enabled() -> bool {
    ROOT_CHILD_Q_OVERRIDE.with(|c| c.get()).unwrap_or_else(root_child_q_logging_enabled_env)
}

fn root_child_q_logging_enabled_env() -> bool {
    static ENABLED: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    // Gleiches OnceLock-Cache-Muster wie `tiling_solver::cache_enabled_env`.
    *ENABLED.get_or_init(|| std::env::var("MOSAIC_ROOT_CHILD_Q").map(|v| v != "0").unwrap_or(true))
}

#[cfg(test)]
pub(crate) fn set_root_child_q_logging_override_for_test(v: Option<bool>) {
    ROOT_CHILD_Q_OVERRIDE.with(|c| c.set(v));
}

/// Laufzeit-Utility-Blend-Gewicht `w` (Task #28). INITIAL aus
/// `MOSAIC_POINTS_UTILITY_W` gelesen (Prozessstart-Default, gleiches Parsing
/// wie zuvor), danach per [`set_aggression_params`] jederzeit neu setzbar
/// (GUI-Live-Regler) -- `Ordering::Relaxed`-Load, KEIN Neu-Parsen pro
/// Suchknoten. Default `0.0` -> `blended_leaf_win_prob` nimmt den Early-Out
/// (byte-identisches Bestandsverhalten, kein zusaetzlicher Rechenpfad).
pub(crate) fn points_utility_w() -> f64 {
    f64::from_bits(points_utility_w_cell().load(std::sync::atomic::Ordering::Relaxed))
}

/// Laufzeit-Denial-Gewicht `lambda_aggr` (Task #28). INITIAL aus
/// `MOSAIC_AGGR_LAMBDA` gelesen, gleiches Zellen-/Cache-Muster wie
/// `points_utility_w`. Default `0.0` (kein Gegner-Punkte-Abzug).
pub(crate) fn aggr_lambda() -> f64 {
    f64::from_bits(aggr_lambda_cell().load(std::sync::atomic::Ordering::Relaxed))
}

/// GUI-Live-Regler (Task #28, `PREREG_task28_aggression.md` Punkt 4 "Engine
/// (additiv, laufzeit-konfigurierbar)"): setzt `w`/`lambda_aggr` ATOMAR neu
/// (naechste PUCT-Blattauswertung sieht sofort den neuen Wert, kein
/// Prozess-Neustart noetig) -- PyO3-Bindung `set_aggression_params` in
/// `lib.rs` ruft dies direkt auf. Defensiv geklemmt auf die im PREREG
/// gemessenen/als sicher belegten Wertebereiche: `w` in `[0,1]` (gemessener
/// Betriebspunkt `w=0.1`, `w=1.0` waere reiner Punkte-Utility ohne
/// Win-Anteil -- ausserhalb bleibt undefiniertes Terrain), `lambda_aggr` in
/// `[0,5]` (Sweep deckte `{0; 0.5; 1; 2}` ab, `5` laesst Luft nach oben ohne
/// eine voellig unvalidierte Groessenordnung zuzulassen). Nicht-endliche
/// Eingaben (NaN/Inf, z.B. durch einen kaputten GUI-Request) fallen auf
/// `0.0` zurueck -- `f64::clamp` selbst liesse NaN unveraendert durch (siehe
/// dessen Doku), das waere hier keine echte Klemme.
pub(crate) fn set_aggression_params(w: f64, lambda_aggr: f64) {
    let w = if w.is_finite() { w.clamp(0.0, 1.0) } else { 0.0 };
    let lambda_aggr = if lambda_aggr.is_finite() { lambda_aggr.clamp(0.0, 5.0) } else { 0.0 };
    points_utility_w_cell().store(w.to_bits(), std::sync::atomic::Ordering::Relaxed);
    aggr_lambda_cell().store(lambda_aggr.to_bits(), std::sync::atomic::Ordering::Relaxed);
}

/// Gegenstueck zu [`set_aggression_params`] -- liest beide Laufzeit-Werte in
/// einem Aufruf (PyO3-Bindung `get_aggression_params` in `lib.rs`).
pub(crate) fn get_aggression_params() -> (f64, f64) {
    (points_utility_w(), aggr_lambda())
}

/// Einmalige Warnung, wenn `w>0` konfiguriert ist, das geladene Netz aber
/// keinen `opp_points`-Kopf hat -- Legacy-Modelle bleiben dadurch unbeeinflusst
/// (Additiv-Regel), der Nutzer soll aber sehen, dass die Konfiguration
/// wirkungslos ist.
fn warn_missing_opp_head_once() {
    WARNED_NO_OPP_HEAD.get_or_init(|| {
        eprintln!(
            "⚠️  MOSAIC_POINTS_UTILITY_W>0 gesetzt, aber das geladene Netz hat keinen \
             opp_points-Kopf -- verhaelt sich wie w=0 (Legacy-Pfad, siehe \
             PREREG_task28_aggression.md)."
        );
    });
}

/// `warn_missing_opp_head_once`-Pendant fuer den Denial-Tie-Break
/// (PREREG_denial_tiebreak.md): eigene `OnceLock`+Funktion statt der obigen
/// wiederverwendet, weil die Meldung den jeweils betroffenen Env-Knopf beim
/// Namen nennen soll (sonst verwechselbar mit dem Task-#28-Blend, der einen
/// eigenen, unabhaengigen Knopf hat).
static WARNED_NO_OPP_HEAD_DENIAL_TIEBREAK: std::sync::OnceLock<()> = std::sync::OnceLock::new();

fn warn_missing_opp_head_for_denial_tiebreak_once() {
    WARNED_NO_OPP_HEAD_DENIAL_TIEBREAK.get_or_init(|| {
        eprintln!(
            "⚠️  MOSAIC_DENIAL_TIEBREAK_EPS>0 gesetzt, aber das geladene Netz hat keinen \
             opp_points-Kopf -- Denial-Tie-Break bleibt inert (siehe \
             PREREG_denial_tiebreak.md)."
        );
    });
}

// ── Task #30 (`evaluations/STATUS.md` Abschnitt "Task #30"): monotone
// Skalen-Korrektur (Platt-artig) des Value-Kopf-Outputs als Laufzeit-Knopf.
// Motivation: Gumbels σ ist LINEAR in der completed-Q-Perturbation, die
// gemessene 6-9%-Wertstauchung (R5-Kalibrierung, Task #27) wird also 1:1 in
// eine zu schwache Perturbation durchgereicht -- eine monotone Logit-Skalen-
// Korrektur AENDERT DIE ORDNUNG PER DEFINITION NICHT, kann aber die Stauchung
// aufheben. Gleiches OnceLock-Env-Var-Cache-Muster wie Task #28
// (`POINTS_UTILITY_W`/`AGGR_LAMBDA` oben) -- siehe `read_f64_env`-Doku.

/// Laufzeit-Cache fuer `MOSAIC_VALUE_CAL_A` (einmalig gelesen, siehe
/// `value_cal_a()`). Default `0.0` (kein Logit-Shift).
static VALUE_CAL_A: std::sync::OnceLock<f64> = std::sync::OnceLock::new();

/// Laufzeit-Cache fuer `MOSAIC_VALUE_CAL_B` (einmalig gelesen, siehe
/// `value_cal_b()`). Default `1.0` (keine Logit-Streckung).
static VALUE_CAL_B: std::sync::OnceLock<f64> = std::sync::OnceLock::new();

/// Laufzeit-Logit-Shift `A` (Task #30), einmalig aus `MOSAIC_VALUE_CAL_A`
/// gelesen und gecacht (NICHT pro Suchknoten neu geparst). Default `0.0`.
pub(crate) fn value_cal_a() -> f64 {
    *VALUE_CAL_A.get_or_init(|| read_f64_env("MOSAIC_VALUE_CAL_A", 0.0))
}

/// Laufzeit-Logit-Streckung `B` (Task #30), gleiches Cache-Muster wie
/// `value_cal_a`. Default `1.0`.
pub(crate) fn value_cal_b() -> f64 {
    *VALUE_CAL_B.get_or_init(|| read_f64_env("MOSAIC_VALUE_CAL_B", 1.0))
}

// ── PREREG_implicit_minimax_backup.md par.1: Implicit-Minimax-Backup-Knopf
// (Baier/Winands). PREREG_agent_encapsulation.md par.3/par.4 (Welle 1, Pilot):
// dieser Knopf ist der ERSTE, der aus dem prozessglobalen OnceLock-Env-Cache
// in die pro-Seite instanziierte `SearchConfig` migriert wurde -- die
// Selektion (`gumbel_select_child`) liest ab jetzt AUSSCHLIESSLICH das
// Config-Feld, kein OnceLock mehr im Suchpfad.

/// Konfiguration EINER Suchseite (Welle 1 der Agenten-Kapselung). Buendelt
/// Knopfwerte, die frueher prozessglobal galten, aber PRO SEITE
/// unterschiedlich gesetzt werden sollen -- angedockt an die bestehenden
/// Pro-Seite-Objekte (`self_play::NetArenaAgent`/`NetSelfPlayAgent`).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct SearchConfig {
    /// Mischgewicht `alpha` fuer die Selektions-Q-Beimischung des implizit-
    /// minimax-propagierten Werts (PREREG_implicit_minimax_backup.md par.1,
    /// `mix_q_with_implicit_minimax`). Default `0.0` (keine Beimischung).
    pub implicit_minimax_alpha: f64,
    /// Gewicht des Langreihen-INITIIERUNGS-Additivs am Blattwert
    /// (`PREREG_long_row_payoff.md` par.3/B1). Default `0.0` =
    /// byte-identisches Bestandsverhalten.
    ///
    /// Zielt ausdruecklich auf den ERSTEN Stein in Musterreihe 5/6, nicht
    /// auf Fortschritt darin: par.2a hat gemessen, dass das Netz beim
    /// FORTSETZEN nicht auffaellig schlechter ist als der Heuristik-Lehrer
    /// (Verhaeltnis 0,22 auf beiden Zustandsverteilungen), beim BEGINNEN
    /// dagegen um Faktor ~3 (Policy-Masse 11,5 % gegen 25,2 %, flach ueber
    /// R1-4). Deshalb Stufenfunktion 0->1, kein Rampenterm.
    pub long_row_init_shaping_w: f64,
}

impl SearchConfig {
    /// Liest den heutigen Env-Knopf `MOSAIC_IMPLICIT_MINIMAX_A` (dieselbe
    /// Parse-Regel wie der fruehere OnceLock-Getter: `read_f64_env`,
    /// Default `0.0`).
    ///
    /// WICHTIG -- Unterschied zum fruaheren `implicit_minimax_alpha()`-
    /// Getter: dessen OnceLock-Cache war VERHALTENSTEIL, nicht nur
    /// Performance-Optimierung -- einmal initialisiert, blieb der Wert fuer
    /// den Rest des PROZESSES fix, selbst wenn zwei Seiten (Netz-vs-Netz)
    /// unterschiedliche Werte haben sollten -- genau das war Anlass 2 in
    /// PREREG_agent_encapsulation.md par.1 (Knopf nicht Netz-gegen-Netz
    /// messbar). `from_env()` cacht dagegen NICHTS und liest bei JEDEM
    /// Aufruf frisch aus der Umgebung. Das ist unproblematisch, weil diese
    /// Funktion je Partie-Einstieg (Agent-Konstruktion) GENAU EINMAL
    /// aufgerufen wird, nicht pro Suchknoten -- ein `Default`-Trait-Impl,
    /// das intern `from_env()` aufriefe, waere dagegen FALSCH: es wuerde den
    /// Eindruck erwecken, `SearchConfig::default()` sei ein reiner,
    /// env-unabhaengiger Wert.
    pub fn from_env() -> Self {
        Self {
            implicit_minimax_alpha: read_f64_env("MOSAIC_IMPLICIT_MINIMAX_A", 0.0),
            long_row_init_shaping_w: read_f64_env("MOSAIC_LONG_ROW_INIT_W", 0.0),
        }
    }

    /// Laedt eine Spec-Datei (`models/<name>.spec.json`,
    /// PREREG_agent_encapsulation.md par.6a Entscheid 2). Schema Welle 1:
    /// `{"implicit_minimax_alpha": <Zahl>}` -- GENAU dieses eine Feld, PFLICHT
    /// (kein Default-Fallback auf die Umgebung: eine Spec-Datei soll das
    /// Suchverhalten VOLLSTAENDIG und reproduzierbar festlegen). Unbekannte
    /// Felder sind ein HARTER FEHLER (kein stilles Ignorieren -- sonst
    /// maskiert ein Tippfehler eine ganze Messung).
    pub fn from_spec_file(path: &str) -> Result<Self, String> {
        let text = std::fs::read_to_string(path)
            .map_err(|e| format!("Spec-Datei {path} nicht lesbar: {e}"))?;
        let value: Value = serde_json::from_str(&text)
            .map_err(|e| format!("Spec-Datei {path}: ungueltiges JSON: {e}"))?;
        let obj = value
            .as_object()
            .ok_or_else(|| format!("Spec-Datei {path}: JSON-Wurzel muss ein Objekt sein"))?;
        const KNOWN_FIELDS: &[&str] =
            &["implicit_minimax_alpha", "long_row_init_shaping_w", "heuristik_variante"];
        for key in obj.keys() {
            if !KNOWN_FIELDS.contains(&key.as_str()) {
                return Err(format!(
                    "Spec-Datei {path}: unbekanntes Feld '{key}' (bekannt: {KNOWN_FIELDS:?})"
                ));
            }
        }
        let get_required = |name: &str| -> Result<f64, String> {
            obj.get(name)
                .ok_or_else(|| format!("Spec-Datei {path}: Feld '{name}' fehlt"))?
                .as_f64()
                .ok_or_else(|| format!("Spec-Datei {path}: '{name}' ist keine Zahl"))
        };
        // Beide Felder PFLICHT (Welle-1-Regel beibehalten: eine Spec-Datei legt
        // das Suchverhalten VOLLSTAENDIG fest, kein stiller Default). Folge und
        // bewusst so gewollt: eine Spec aus der Welle-1-Aera (nur
        // `implicit_minimax_alpha`) wird von DIESEM Wheel hart abgelehnt. Das
        // ist die richtige Fehlermeldung -- ein eingefrorenes Artefakt gehoert
        // auf seinem EIGENEN, mitgelieferten Wheel gefahren
        // (`models/frozen_champions/<name>/mosaic_rust_*.whl`), nicht auf einem
        // neueren; ein stiller Default wuerde genau diesen Fehler maskieren und
        // die "beweisbar identisch"-Zusage aushebeln.
        let implicit_minimax_alpha = get_required("implicit_minimax_alpha")?;
        let long_row_init_shaping_w = get_required("long_row_init_shaping_w")?;
        // Das Feld bleibt PFLICHT, obwohl es seit 2026-08-26 nur noch einen
        // gueltigen Wert hat: die Specs der eingefrorenen Artefakte tragen es,
        // und ein weggelassenes Pflichtfeld waere ein stiller Vertragsbruch.
        //
        // Der v2-Zweig ist aus dem Quellstand entfernt (B4a). Eine v2-Spec
        // wird deshalb ABGEWIESEN und nicht still als v1 gefahren -- sonst
        // laege genau der Fehler vor, gegen den die Kapselung gebaut ist:
        // ein Agent, der etwas anderes spielt, als seine Spec sagt. Das
        // Artefakt bleibt auf seinem MITGELIEFERTEN Wheel lauffaehig.
        let variante_name = obj
            .get("heuristik_variante")
            .ok_or_else(|| format!("Spec-Datei {path}: Feld 'heuristik_variante' fehlt"))?
            .as_str()
            .ok_or_else(|| {
                format!("Spec-Datei {path}: 'heuristik_variante' ist keine Zeichenkette")
            })?;
        if variante_name != "v1" {
            return Err(format!(
                "Spec-Datei {path}: heuristik_variante '{variante_name}' ist in diesem Build                  nicht mehr spielbar -- nur 'v1'. Der v2-Zweig wurde am 2026-08-26 entfernt                  (PREREG_heuristic_v2_long_rows.md par.19). Das Artefakt laeuft weiter auf                  seinem mitgelieferten Wheel."
            ));
        }
        Ok(Self { implicit_minimax_alpha, long_row_init_shaping_w })
    }
}

/// Clamp-Epsilon fuer die Logit-Transformation -- verhindert `ln(0/1)` bzw.
/// `ln(x/0)` (±∞) an den Raendern des `[0,1]`-Win-Prob-Bereichs.
const VALUE_CAL_EPS: f64 = 1e-6;

/// Reine Kalibrierungs-Formel (Task #30, kein Netz-/Env-Zugriff -- direkt
/// testbar, gleiches Trennungsmuster wie `blended_leaf_win_prob`/`_with`):
/// `p' = sigmoid(a + b*logit(p))`, `p` vorher auf `[EPS, 1-EPS]` geklemmt.
/// MONOTON in `p` fuer jedes `b>0` (Sigmoid und Logit sind beide streng
/// monoton steigend, `a + b*x` ist es fuer `b>0` auch) -- die Suchordnung
/// bleibt also per Konstruktion erhalten, siehe Eigenschafts-Test unten.
///
/// Early-Out bei `(a,b)==(0.0,1.0)` (Default): gibt `p` UNVERAENDERT zurueck,
/// kein Logit-/Sigmoid-Roundtrip -- byte-identisches Bestandsverhalten (kein
/// zusaetzlicher Rechenpfad, keine Rundungsdifferenz durch `ln`/`exp`).
pub(crate) fn calibrate_win_prob_with(p: f64, a: f64, b: f64) -> f64 {
    if a == 0.0 && b == 1.0 {
        return p;
    }
    let clamped = p.clamp(VALUE_CAL_EPS, 1.0 - VALUE_CAL_EPS);
    let logit = (clamped / (1.0 - clamped)).ln();
    let z = a + b * logit;
    1.0 / (1.0 + (-z).exp())
}

/// Laufzeit-Wrapper von [`calibrate_win_prob_with`], liest `A`/`B` aus dem
/// Prozess-weiten `OnceLock`-Cache (`value_cal_a()`/`value_cal_b()`) --
/// gleiches Trennungsmuster wie `blended_leaf_win_prob`/`_with`.
pub(crate) fn calibrate_win_prob(p: f64) -> f64 {
    calibrate_win_prob_with(p, value_cal_a(), value_cal_b())
}

/// Reine Blend-Formel (Task #28, PREREG Punkt 4, kein Netz-/Env-Zugriff --
/// direkt ohne ONNX-Fixture testbar). `pts_raw`/`opp_raw` sind die ROHEN
/// tanh-Outputs (Bereich [-1,1]) der Punkte-/Gegner-Punkte-Koepfe, VOR jeder
/// [0,1]-Skalierung.
///
/// 1. Algebraische Rueckgewinnung (siehe `VALUE_OPP_EPSILON`-Doku oben):
///    `own_pts = pts_raw + VALUE_OPP_EPSILON*opp_raw`.
/// 2. Denial-Abzug + Clamp auf den gueltigen Tanh-Bereich:
///    `combined = clamp(own_pts - lambda_aggr*opp_raw, -1, 1)`.
/// 3. Skalenkonvention identisch zu `value_to_win_prob`/der bestehenden
///    `pts = value_to_win_prob(points)`-Zeile in `blended_leaf_win_prob`
///    (Tanh[-1,1] -> [0,1] via `(v+1)/2`) -- der Punkte-Term muss auf
///    DIESELBE Skala wie `wr` (Win-Wahrscheinlichkeit, [0,1]) gebracht
///    werden, sonst wäre der `(1-w)*wr + w*u_pts`-Blend in
///    `blended_leaf_win_prob` dimensional inkonsistent.
pub(crate) fn opp_aware_points_utility(pts_raw: f64, opp_raw: f64, lambda_aggr: f64) -> f64 {
    let own_pts = pts_raw + VALUE_OPP_EPSILON * opp_raw;
    let combined = (own_pts - lambda_aggr * opp_raw).clamp(-1.0, 1.0);
    (combined + 1.0) * 0.5
}

/// Skala für die Floor-Straf-Korrektur (siehe `floor_shaping_delta`), gleiche
/// Größenordnung wie `VALUE_SCALE` in `neural_net.py` (dort 50.0) — macht die
/// Korrektur direkt vergleichbar mit dem own-minus-opp-Score-Margin, den
/// `value`/`points_forecast` schon als Trainingsziel verwenden.
const FLOOR_SHAPING_SCALE: f64 = 50.0;

/// Gewicht der Floor-Straf-Korrektur relativ zum Netz-Blattwert. Klein
/// gehalten (Nudge, kein Ersatz für den Value-Head).
///
/// DREIFACH RE-VALIDIERT, der Wert 0.3 ist bestätigt und bleibt:
///
/// 1. Erstvalidierung (2026-07-19/20, v9b_domeonly, 150 Sims, n=100, kein
///    Early-Stop): 11:89 Siege, Score 24.5 vs. 44.2, Floor 16.9 vs. 11.2 –
///    deutlich engerer Floor-Abstand als die Baseline (~20-27 vs. ~8-10).
/// 2. Floor-Sweep in der WDL-Ära (`PREREG_search_path_remeasurements.md`,
///    Status ENTSCHIEDEN, Messung 1): W=0,3 153/200 gegen W=0,15 144/200
///    (p=0,31) und gegen W=0,6 (p=0,36) – beides H0, der Wert dazwischen
///    ist gleichgültig.
/// 3. Task A (2026-08-09, Champion v21_2d_brierbest @400 gegen
///    Heuristik@150dyn, Seed 20260825): W=0,3 322/400 gegen W=0,0 277/400
///    (80,5 % gegen 69,3 %, -11,25 pp), gepaarter exakter McNemar
///    p=0,0001 (b=43/c=88); Block-Ebene 13 von 16 Blöcken, Block-SE 0,71,
///    t=3,94. Artefakt
///    `evaluations/paired_arena_env_paired_arena_env_floorw_taskA.json`.
///
/// STRUKTURBEFUND: Floor-Shaping ist ein SCHALTER, kein Regler – ob es an
/// ist, macht ~11 pp Siegquote; welchen Wert es zwischen 0,15 und 0,6
/// trägt, macht nichts. Ein Sweep an dieser Konstante ist damit
/// abgeschlossen; nur ein Abschalten waere eine echte Aenderung – und das
/// kostet belegt Staerke.
pub const FLOOR_SHAPING_WEIGHT: f64 = 0.3;

/// Laufzeit-Wert des Floor-Shaping-Gewichts: `MOSAIC_FLOOR_SHAPING_W`
/// ueberschreibt den Default `FLOOR_SHAPING_WEIGHT` (PREREG_suchpfad_
/// nachmessungen.md, Messung 1 -- Sweep 0,15/0,3/0,6 ohne Neubau).
/// Einmalig beim ersten Zugriff gelesen (OnceLock, #30-Muster); ohne
/// gesetzte Env-Var byte-identisches Bestandsverhalten.
pub fn floor_shaping_weight() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_FLOOR_SHAPING_W", FLOOR_SHAPING_WEIGHT))
}

/// Default der Gegner-Gewichtung fuer das Floor-Shaping (Eskalationsstufe
/// E2, `evaluations/PREREG_aggression_style_measurement.md`) -- `1.0` = der
/// GEGNER-Anteil (`opp`) fliesst genauso stark ein wie der EIGENE Anteil
/// (`own`), exakt das bisherige, arena-verifizierte Verhalten.
pub const FLOOR_SHAPING_OPP_BIAS: f64 = 1.0;

/// Laufzeit-Wert der Floor-Shaping-Gegner-Gewichtung: `MOSAIC_FLOOR_SHAPING_
/// OPP_BIAS` ueberschreibt `FLOOR_SHAPING_OPP_BIAS` (gleiches OnceLock-Muster
/// wie `floor_shaping_weight`). `bias>1` belohnt Zuege, die dem GEGNER
/// Floor-Strafen zuschieben, STAERKER als eigene Floor-Vermeidung (siehe
/// `floor_shaping_delta_ego`-Kommentar fuer die exakte Formel). Ohne
/// gesetzte Env-Var byte-identisches Bestandsverhalten (Default 1.0).
pub fn floor_shaping_opp_bias() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_FLOOR_SHAPING_OPP_BIAS", FLOOR_SHAPING_OPP_BIAS))
}

/// Task #78 (v12c): rundenabhängige Value-Shrinkage Richtung 0.5. Motivation:
/// der Value-Head ist in frühen Runden nachweislich kaum besser als der
/// Mittelwert (Runde-1-Noise-Floor-Deckel ≈0.007, siehe
/// `evaluations/STATUS.md` "Noise-Floor-Test"), wird an JEDEM PUCT-
/// Blattknoten aber gleich stark vertraut wie in Runde 5 (Deckel ≈0.44, klar
/// informativ). Shrinkage dämpft die Blattwert-AUSSCHLÄGE (nicht den
/// Mittelwert) proportional zur erwarteten Zuverlässigkeit je Runde, analog
/// zu einem James-Stein-artigen Schrumpfen des Schätzers Richtung des
/// uninformativen Priors 0.5.
///
/// GEPAARTER A/B-NACHWEIS GEFAHREN (2026-07-23, `tools/paired_arena_shrink_ab.py`,
/// v12b_lr_best@400 vs. v12_best@400, 100 seed-gepaarte Spiele je Arm, gleiche
/// Seeds in beiden Armen): Arm OFF 61:39, Arm ON 50:50 -- ON ist NICHT nur
/// unsignifikant, sondern tendenziell sogar schwächer (Diskordanz b=15 vs.
/// c=26, exakter McNemar p=0.117). Evidenzregel (siehe MEMORY.md/STATUS.md-
/// Präzedenzfälle: reine Performance-Hebel ohne Korrektheits-Charakter
/// brauchen einen signifikanten Beleg, bevor sie standardmäßig aktiv
/// geschaltet werden, siehe z.B. das ISMCTS-Mehrfach-Determinisierungs-
/// Verwerfungsmuster) verlangt p<0.05 UND Vorteil für ON -- keins von beiden
/// erfüllt. Bleibt daher AUS. Details: `evaluations/STATUS.md` Abschnitt
/// "v12c: Value-Shrinkage-Rekalibrierung + A/B (2026-07-23)".
pub const VALUE_SHRINK_ENABLED: bool = false;

/// Rekalibrierung (Task #78, 2026-07-23) `w_r` je Runde (Index 0 = Runde 1
/// ... Index 4 = Runde 5), angewendet als `v_shrunk = 0.5 + w_r·(v - 0.5)`.
/// Ersetzt die Phase-A-Platzhalterwerte (die auf dem separaten Noise-Floor-
/// Rückspiel-Test + geclampter v10/v9b-Modell-R²-Näherung beruhten, siehe
/// Git-Historie dieser Konstante).
///
/// Quelle der Zahlen: `tools/offline_diagnosis.py`-Lauf auf dem AMTIERENDEN
/// Champion `v12b_lr_best` (2026-07-23, `evaluations/STATUS.md` Abschnitt
/// "v12b: LR-Schedule + From-Scratch-Kontrolle"), echter Val-Split
/// (n=32.392 Val-Züge). Für v12b_lr existiert KEIN separater Noise-Floor-
/// Rückspiel-Test (die Drei-Runden-Probe wurde nur einmal, gegen ein
/// anderes Modell/Korpus, gefahren) -- deshalb wird hier direkt das
/// Modell-R² pro Runde als Verlässlichkeits-Näherung verwendet (derselbe
/// Näherungsschritt, den Phase A bereits für Runde 4/5 mangels Deckel-
/// Messwert brauchte, jetzt konsistent auf alle 5 Runden angewendet).
///
/// Herleitung, unverändert zur Phase-A-Formel: `w_r ∝ sqrt(max(0, R²_r))`,
/// normiert auf `w_5 = 1.0` (keine Dämpfung in der letzten Runde). Die
/// frischen R²-Werte sind bereits von sich aus streng monoton steigend
/// (R1 0.0368 < R2 0.1106 < R3 0.1717 < R4 0.2298 < R5 0.5145) -- anders als
/// in Phase A ist HIER kein `max(Deckel_r, Deckel_{r-1})`-Clamping nötig.
/// Werte (vor Normierung, `sqrt`):
///   R1 √0.0368=0.19183, R2 √0.1106=0.33257, R3 √0.1717=0.41437,
///   R4 √0.2298=0.47937, R5 √0.5145=0.71729.
/// Normiert durch R5: `[0.2674, 0.4636, 0.5777, 0.6683, 1.0000]`.
pub const VALUE_SHRINK_PER_ROUND: [f64; 5] = [0.2674, 0.4636, 0.5777, 0.6683, 1.0000];

/// Rundenzahl (1-basiert, wie `state.round_number`) → Schrumpfgewicht `w_r`
/// aus `VALUE_SHRINK_PER_ROUND`. Defensiv geklammert (Runde 0 oder >5 sollte
/// in der Praxis nie vorkommen, klemmt statt zu paniken).
fn value_shrink_weight(round_number: u32) -> f64 {
    let last = VALUE_SHRINK_PER_ROUND.len() - 1;
    let idx = (round_number.saturating_sub(1) as usize).min(last);
    VALUE_SHRINK_PER_ROUND[idx]
}

/// Wendet die rundenabhängige Value-Shrinkage (Task #78) auf BEIDE
/// Blattwert-Perspektiven `[Spieler0, Spieler1]` an. Muss NACH
/// `blended_leaf_win_prob`, aber VOR dem Floor-Shaping-Additiv aufgerufen
/// werden (siehe `make_node`/`net_leaf_eval`) -- das exakte Floor-Signal
/// (`floor_shaping_delta`) ist eine reine State-Funktion und soll NICHT
/// geschrumpft werden, nur der Netz-Rohwert. Bei `VALUE_SHRINK_ENABLED=false`
/// (Standard) exakte Identität -- byte-identisch zum Vor-Task-#78-Verhalten.
fn apply_value_shrink(value: [f64; 2], round_number: u32) -> [f64; 2] {
    if !VALUE_SHRINK_ENABLED {
        return value;
    }
    let w = value_shrink_weight(round_number);
    [0.5 + w * (value[0] - 0.5), 0.5 + w * (value[1] - 0.5)]
}

/// Perspektiven-/OOD-Interventionstest (externer Hinweis, 2026-07-19): der
/// zweite Forward-Pass für `other_val` (künstlich geflipptes
/// `state.current_player`) bewertet einen Zustand, den das Netz im Training
/// NIE sieht — Trainingsdaten (`self_play.rs`) zeichnen Zustände IMMER nur
/// aus der Perspektive des TATSÄCHLICHEN Zugspielers auf, nie eine fremde
/// Ego-Sicht mitten in einem fremden Zug (inkl. pending-Phasen wie
/// Kuppelplatzierung). Dieser zweite Forward-Pass ist also potenziell
/// Out-of-Distribution und könnte inkohärente, nicht nullsummen-konsistente
/// Q-Backups in beide PUCT-Bäume einspeisen — eine Hypothese, die sowohl
/// "gesundes R², aber schadet der Suche" ALS AUCH "Value/Points/Blend
/// versagen alle identisch" erklären würde (gleiche Plumbing in allen drei
/// Fällen). `true` erzwingt stattdessen die günstige, garantiert
/// nullsummen-konsistente Näherung `other_val = 1 - mover_val` (EIN
/// Forward-Pass statt zwei, kein OOD-Risiko, halbiert nebenbei die
/// Inferenzkosten) — direkter, kostenloser Interventionstest.
///
/// GETESTET (2026-07-20, v9b_domeonly, 150 Sims, n=100, KEIN Early-Stop,
/// ISOLIERT ohne Floor-Shaping): 3:97 (3% Siege), Score 15.7 vs. 43.4,
/// Floor 21.3 vs. 11.1 — KEINE Verbesserung, eher schlechter als der
/// 0.0-Baseline-Bereich und deutlich schwächer als Floor-Shaping (11%).
/// Die Perspektiven-/OOD-Hypothese ist damit als ALLEINIGE Erklärung
/// widerlegt (der zweite Forward-Pass ist zumindest nicht der dominante
/// Schadensfaktor) -- auf `false` zurückgesetzt (Original-Verhalten).
pub const MIRROR_OTHER_VAL: bool = false;

/// Kuppelstapel-Determinisierung im Suchbaum (Fund 6, externer Hinweis,
/// 2026-07-20) -- mischt `dome_tile_pool` bei jedem simulierten
/// `DrawStackPeek` neu (siehe Kommentar an der Aufrufstelle in
/// `build_net_tree`), statt die ECHTE, im realen Spiel verdeckte oberste
/// Platte zu lesen.
///
/// GETESTET (2026-07-20, v9b_domeonly + Struktur-Fixes + Floor-Shaping
/// W=0.3, 150 Sims, n=100, KEIN Early-Stop): 9:91 (9% Siege), Score 21.9
/// vs. 43.9, Floor 18.8 vs. 12.1 -- SCHLECHTER als ohne diesen Fix (17%
/// Siege). Theoretisch gut begründet (entfernt Orakel-Wissen), aber die
/// Neumischung erhöht offenbar eher die Varianz der Suche (jeder simulierte
/// Ast sieht eine andere Ziehung) als dass sie echte Verzerrung beseitigt --
/// bei nur 150 Sims/Zug zu teuer. Auf `false` zurückgesetzt (Original-
/// Verhalten); Code bleibt verfügbar.
pub const SHUFFLE_STACK_PEEK_IN_SEARCH: bool = false;

/// Buendelt die ERSTMALIGE Expansion ALLER Top-m-Kandidaten an der Gumbel-
/// Wurzel (Perf-Auftrag, 2026-08-02: die 1,46x-2D-Inferenzkosten druecken)
/// in EINEM `Net::eval_batch`-Aufruf statt `m_prime` einzelner
/// `make_node`-Netz-Evals -- siehe `batched_expand_root_candidates`.
/// Standardmaessig AUS (gleiches Muster wie `USE_GUMBEL_SEARCH`/
/// `MIRROR_OTHER_VAL` etc. -- neue, noch nicht arena-validierte
/// Sucheigenschaft), Arena-A/B folgt VOR einer Aktivierung.
///
/// Numerisch THEORETISCH nicht ganz kostenlos beim Umschalten: die
/// per-Kandidat-Blattwerte selbst sind batch-invariant (Toleranz 1e-5,
/// siehe `net::eval_batch_matches_n_single_evals` -- derselbe
/// Praezedenzfall wie `eval_pair`), und die WURZEL-Aggregate
/// (`nodes[0].value`/`.visits`) KOENNTEN in den letzten Bits abweichen,
/// weil Gleitkomma-Summation nicht assoziativ ist und die Kandidaten-
/// Expansionsreihenfolge sich relativ zu den anschliessenden Tiefen-
/// Besuchen verschiebt (batched: ALLE `m_prime` Kandidaten zuerst, dann
/// deren weitere Besuche; unbatcht: je Kandidat Erstbesuch + weitere
/// Besuche EINGESCHACHTELT, bevor der naechste Kandidat drankommt) --
/// GEMESSEN (2026-08-02, Paritaetstest
/// `batched_root_expansion_matches_sequential_within_tolerance`, gegen
/// `v19_2d_best` UND ein flaches Modell, sims=400/m_prime=16) war das
/// Ergebnis aber tatsaechlich BIT-IDENTISCH (nicht nur innerhalb Toleranz)
/// -- kein beobachtbarer Effekt in der Praxis, die Toleranz im Test bleibt
/// trotzdem als Sicherheitsmarge stehen (kein Anspruch auf Bit-Identitaet
/// ueber alle Hardware-/tract-Versionen hinweg).
/// RNG-Verbrauch bleibt in der Standardkonfiguration UNVERAENDERT (siehe
/// `batched_expand_root_candidates`-Doku): `SHUFFLE_STACK_PEEK_IN_SEARCH`
/// und `ROUND_TRANSITION_SAMPLING` (beide Default `false`) sind die
/// einzigen `rng`-Verbrauchsstellen zwischen Expansion und Tiefenbesuch --
/// bei `SHUFFLE_STACK_PEEK_IN_SEARCH=true` faellt die Aufrufstelle
/// zusaetzlich auf den unbatchten Pfad zurueck (siehe dort), um die
/// RNG-Reihenfolge nicht zu verschieben.
pub const BATCH_ROOT_EXPANSION: bool = false;

/// Wurzel-Determinisierung (Nutzer-Vorschlag, 2026-07-20 -- Ersatz für
/// `SHUFFLE_STACK_PEEK_IN_SEARCH`s In-Tree-Neumischung): statt bei JEDEM
/// simulierten Peek/Chip-Reveal neu zu mischen (nachweislich MEHR
/// Such-Varianz als Bias-Korrektur, siehe dortiger Kommentar -- und für den
/// Kuppelstapel-Fall ohnehin irrelevant, siehe Bindungs-Check: der
/// Value-Head sieht `pending_stack_draw` architektonisch nie), wird hier
/// EINMAL pro Zugsuche (`build_net_tree`s Wurzel-Erzeugung) eine plausible,
/// fixierte "Stichwelt" gezogen -- `dome_tile_pool` UND die noch
/// unaufgedeckten Bonuschips (`bonus_chip_pool` + noch nicht enthüllte
/// Fabrik-Chips) werden einmalig neu gemischt, danach läuft die GESAMTE
/// Suche deterministisch auf dieser einen Welt. Kein zusätzliches
/// In-Tree-Rauschen (jeder Knoten bleibt intern konsistent) -- nur der
/// klassische, weit mildere Determinisierungs-Fehler (die Suche vertraut
/// EINER plausiblen Stichprobe statt der echten, aber unbekannten Welt).
/// Anders als beim Kuppelstapel (bewiesen irrelevant) sieht der Value-Head
/// aufgedeckte Bonuschip-Werte tatsächlich als Feature (`features.rs`,
/// `bonus_chip_revealed`) -- hier könnte Orakel-Wissen also durchaus
/// greifen.
///
/// GETESTET (2026-07-20, v9b_domeonly + Struktur-Fixes + Floor-Shaping
/// W=0.3, 150 Sims, n=100, KEIN Early-Stop): 12:88 (12% Siege), Score 19.2
/// vs. 40.5, Floor 19.2 vs. 13.7 -- KEINE Verbesserung ggü. der Baseline
/// ohne Determinisierung (17%), tendenziell sogar leicht schlechter (wenn
/// auch deutlich milder als der In-Tree-Fix, der von 17%→9% stürzte). Da
/// der Kuppelstapel-Anteil bewiesen irrelevant ist, kann die Ursache nur im
/// Bonuschip-Anteil liegen oder schlicht Stichproben-Rauschen sein (n=100,
/// ~5 Prozentpunkte liegen im selben Band wie andere Wiederholungen dieser
/// Session) -- kein separater Bonuschip-Bindungs-Check bisher gefahren.
///
/// NUTZER-ENTSCHEIDUNG (2026-07-20): TROTZDEM aktiv gelassen. Anders als
/// der In-Tree-Fix (klarer, großer Rückschritt 17%→9%, dort zu Recht
/// verworfen) ist der Effekt hier klein und im Rauschband dieser Session --
/// es geht nicht nur um gemessenen Vorteil, sondern auch um KORREKTHEIT:
/// die Suche soll kein Wissen nutzen, das ein echter Spieler nicht hat.
/// Dies ist der Minimalfix für das Orakel-Wissen-Problem (Fund 6), bewusst
/// als Standardverhalten beibehalten, unabhängig vom (unklaren) Arena-Delta.
pub const DETERMINIZE_ROOT_HIDDEN_INFO: bool = true;

/// Mischt `dome_tile_pool` und alle noch unaufgedeckten Bonuschip-Werte
/// (Fabrik-Chips mit `!bonus_chip_revealed` + `bonus_chip_pool`) einmalig
/// neu -- siehe `DETERMINIZE_ROOT_HIDDEN_INFO`-Kommentar. Bereits
/// AUFGEDECKTE Fabrik-Chips sind öffentliches Wissen und bleiben
/// unangetastet. Gleiches Muster wie `round_transition_deep::
/// simulate_one_round`s Kuppelstapel-Determinisierung, hier auf beide
/// verdeckten Informationsquellen erweitert und auf Wurzel-Ebene (einmal
/// pro Suche) statt pro Runde angewendet.
fn determinize_hidden_information<R: Rng + ?Sized>(state: &mut GameState, rng: &mut R) {
    state.dome_tile_pool.shuffle(rng);

    let orig_pool_len = state.bonus_chip_pool.len();
    let mut hidden_chips: Vec<crate::dome::BonusChip> = state.bonus_chip_pool.drain(..).collect();
    let unrevealed_idxs: Vec<usize> = state
        .factories
        .iter()
        .enumerate()
        .filter(|(_, f)| f.bonus_chip.is_some() && !f.bonus_chip_revealed)
        .map(|(i, _)| i)
        .collect();
    for &idx in &unrevealed_idxs {
        if let Some(chip) = state.factories[idx].bonus_chip.take() {
            hidden_chips.push(chip);
        }
    }
    hidden_chips.shuffle(rng);
    let remaining = hidden_chips.split_off(orig_pool_len.min(hidden_chips.len()));
    state.bonus_chip_pool = hidden_chips;
    for (idx, chip) in unrevealed_idxs.into_iter().zip(remaining.into_iter()) {
        state.factories[idx].bonus_chip = Some(chip);
    }
}

/// Klassisches ISMCTS (Task #65, 2026-07-22): `DETERMINIZE_ROOT_HIDDEN_INFO`
/// zieht bisher EINE Stichweltentscheidung pro Zugsuche -- die Suche
/// optimiert dann gegen genau diese eine mögliche Welt. Mit `> 1` werden
/// stattdessen `NUM_DETERMINIZATIONS` unabhängige Welten gezogen (je ein
/// eigener `build_net_tree`-Aufruf, das Sims-Budget gleichmäßig gesplittet,
/// Rest an die erste Welt, siehe `split_sims_across_worlds`), je Welt ein
/// eigener Baum gebaut, und die completed-Q-Politik an der Wurzel über die
/// Welten GEMITTELT (siehe `average_completed_q_policy`) -- Standard-ISMCTS-
/// Aggregation, statt sich auf eine einzelne Stichprobe zu verlassen.
///
/// `1` = EXAKT das bisherige Verhalten -- an allen drei Suche-Einstiegen
/// (`net_search_drafting_action`/`net_root_child_stats_and_policy`/
/// `net_search_with_tree`) bleibt der `<= 1`-Codepfad unverändert ein
/// einzelner `build_net_tree`-Aufruf + die alte Auswahl-/Extraktionslogik --
/// bewusst NICHT durch die neue Aggregations-Maschinerie geroutet, damit
/// `NUM_DETERMINIZATIONS=1` byte-identisch zum Alt-Verhalten bleibt (siehe
/// Testmodul).
///
/// **Befund zur Wurzel-Kandidatenliste (Aufgabenstellung fragte explizit
/// danach)**: `drafting_actions(state)` (game.rs) hängt an der Wurzel nur
/// von `state.factories` (Existenz/Farbe der Auslage-Fliesen, `bonus_chip.
/// is_some()` -- NICHT von dessen Identität/`bonus_chip_revealed`),
/// `state.dome_display`, `state.pending_dome_choice`/`pending_stack_draw`
/// (Struktur, nicht Inhalt) ab. `determinize_hidden_information` verändert
/// AUSSCHLIESSLICH die REIHENFOLGE von `dome_tile_pool` und die IDENTITÄT
/// (nicht Existenz) unaufgedeckter Bonus-Chips -- keines dieser Felder
/// beeinflusst, welche `Action`-Varianten legal sind. Die Wurzel-
/// Kandidatenliste (und mit ihr `build_untried_actions`s POLICY_MASS_CUTOFF-
/// Präfix, da die Netz-Priors auf denselben, für unaufgedeckte Information
/// maskierten Features beruhen) ist damit weltUNabhängig -- die Aggregation
/// per direktem Aktions-Schlüsselvergleich (`Action: PartialEq`) ist
/// folglich korrekt und braucht keinen Kandidatenlisten-Abgleich über
/// Indizes. Trotzdem defensiv robust implementiert (fehlende Aktion in
/// einer Welt wird einfach übersprungen, kein Panik), falls diese Invariante
/// künftig durch eine Regeländerung verletzt würde.
///
/// **Perspektiven-Divergenz-Logging/Diagnose-Pfade geprüft (kein n-faches
/// Zählen)**: `record_perspective_divergence` akkumuliert pro `make_node`-
/// Aufruf, also pro TATSÄCHLICH bewertetem Baumknoten -- bei N Welten gibt
/// es zwar N separate Bäume, aber JEDER Knoten in JEDEM Baum ist eine echte,
/// eigenständige Netz-Auswertung (kein Knoten wird mehrfach für dieselbe
/// Sim gezählt). Das Gesamt-Sims-Budget bleibt unverändert (nur gesplittet,
/// siehe `split_sims_across_worlds`) -- die Diagnose sammelt also über
/// denselben Gesamt-Simulationsaufwand wie zuvor, nur jetzt über mehrere
/// kleinere Bäume statt einem großen. Kein Fix nötig.
///
/// **GETESTET (2026-07-22, gepaarter A/B, `evaluations/paired_arena_ismcts.py`,
/// v10_best@NET_SIMS=400 vs. Heuristik@HEUR_SIMS=200, Blöcke à 25, kumulativer
/// exakter McNemar): n=3 verliert SIGNIFIKANT gegen n=1 -- Stopp nach 75
/// Paaren bei p=0.00088 (diskordant b=6 [n=3 gewinnt, n=1 nicht] vs. c=25
/// [umgekehrt]). Sieg-Anteil gegen Heuristik: n=3 19/75=25.3% (95%-KI
/// 16.9-36.2%), n=1 38/75=50.7% (95%-KI 39.6-61.7%) -- deutlich, nicht im
/// Rauschband. Wahrscheinlichste Erklärung: das 400er-Sims-Budget auf 3
/// Welten gesplittet (~133/Welt) unterbudgetiert `GUMBEL_TOP_M=16` +
/// Sequential Halving pro Welt stark genug, dass der Suchtiefen-/
/// Differenzierungsverlust den ISMCTS-Aggregationsgewinn (Robustheit gegen
/// EINE ungünstige Determinisierung) bei diesem Sims-Niveau klar überwiegt.
/// Reiner Performance-Hebel (kein Korrektheits-Fix, siehe
/// `DETERMINIZE_ROOT_HIDDEN_INFO`-Präzedenz für den Unterschied) -- hier
/// zählt der Nachweis, nicht die theoretische Eleganz (Floor-Shaping-
/// Präzedenz). Auf `1` zurückgesetzt (= Standard-Einzeldeterminisierung,
/// unverändert seit vor Task #65); der komplette Mehrwelten-/Aggregations-
/// Code bleibt als Toggle verfügbar (z.B. für einen künftigen Test bei
/// höherem Sims-Budget, wo der Unterbudgetierungs-Nachteil kleiner sein
/// könnte).
pub const NUM_DETERMINIZATIONS: usize = 1;

/// Laufzeit-Wert der ISMCTS-Mehrfach-Determinisierung `k`
/// (PREREG_ismcts_determinizations.md) via `MOSAIC_NUM_DETERMINIZATIONS` --
/// ueberschreibt die Konstante [`NUM_DETERMINIZATIONS`] oben (bleibt als
/// Default-Quelle stehen, siehe deren GETESTET-Absatz: `k=1` ist der
/// arena-belegte Standard). Einmalig gelesen (OnceLock, #30-Muster wie
/// `floor_shaping_weight`). ALLE Aufrufstellen, die frueher direkt die
/// Konstante lasen (die drei Sucheinstiege `net_search_drafting_action`/
/// `net_root_child_stats_and_policy`/`net_search_with_tree`, PLUS die
/// Hybrid-Variante `net_search_drafting_action_hybrid` und das Debug-JSON-
/// Feld `net_search_with_tree_from_forest`), lesen jetzt diesen Getter --
/// die `<= 1`-Kurzschluesse an jeder dieser Stellen bleiben ERHALTEN, damit
/// `k=1` weiterhin byte-identisch zum Alt-Verhalten ist (unveraendert
/// derselbe Einzelbaum-Codepfad, nur die Quelle des Vergleichswerts ist neu).
///
/// Werte `<1` (inkl. ungesetzt/nicht parsbar -- `read_f64_env`s Default-
/// Fallback IST die Konstante selbst, `1.0`) werden auf mindestens `1`
/// geklemmt: `k=0` haette eine leere Welten-Liste zur Folge
/// (`build_determinized_forest` erwartet `n>=1`, siehe dortige Doku).
/// Nachkommastellen werden gerundet (z.B. `2.6` -> `3`).
pub fn num_determinizations() -> usize {
    static CELL: std::sync::OnceLock<usize> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| {
        let raw = read_f64_env("MOSAIC_NUM_DETERMINIZATIONS", NUM_DETERMINIZATIONS as f64);
        (raw.round() as i64).max(1) as usize
    })
}

/// Teilt `sims` gleichmäßig auf `n` Welten auf (Rest an die ERSTE Welt).
/// `n` wird an den Aufrufstellen immer `NUM_DETERMINIZATIONS` sein.
fn split_sims_across_worlds(sims: u32, n: usize) -> Vec<u32> {
    let n = (n.max(1)) as u32;
    let base = sims / n;
    let rem = sims % n;
    (0..n).map(|i| if i == 0 { base + rem } else { base }).collect()
}

/// Baut `n` unabhängige Suchbäume ("Wald", ein Baum je Welt) -- `n` nimmt
/// alle Produktions-Aufrufstellen als `NUM_DETERMINIZATIONS` entgegen
/// (NUR für den `> 1`-Pfad gedacht, siehe Konstantenkommentar), als
/// Parameter statt hartkodierter Konstante gehalten, damit das Testmodul
/// direkt verschiedene `n` prüfen kann, ohne die Konstante selbst umbauen
/// zu müssen. `build_net_tree` zieht bei `DETERMINIZE_ROOT_HIDDEN_INFO=true`
/// selbst bei JEDEM Aufruf eine frische Determinisierung (RNG-Strom wird
/// zwischen den Welten einfach weitergereicht) -- kein separates Reseeding
/// nötig, um unterschiedliche Welten zu bekommen.
fn build_determinized_forest<R: Rng + ?Sized>(
    net_policy: &Net,
    net_value: Option<&Net>,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    n: usize,
    rng: &mut R,
    search_config: &SearchConfig,
) -> Vec<Vec<Node>> {
    split_sims_across_worlds(sims, n)
        .into_iter()
        .map(|world_sims| {
            build_net_tree(
                net_policy, net_value, state, world_sims, c_puct, add_root_noise, rng, None, None, search_config,
            )
        })
        .collect()
}

/// Rohe `(Action, Besuche, Q)`-Statistik der Wurzelkinder EINES Baums --
/// extrahiert aus `net_root_child_stats`/`net_root_child_stats_and_policy`s
/// altem `NUM_DETERMINIZATIONS<=1`-Pfad, zusätzlich von
/// `aggregate_root_child_stats` (Mehrwelten-Summierung) je Welt genutzt.
fn root_child_stats_from_nodes(nodes: &[Node]) -> Vec<(Action, u32, f64)> {
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

/// Aggregiert `(Action, Besuche, Q)` über den Determinisierungs-Wald:
/// Besuche werden SUMMIERT (treibt `self_play::net_drafting_policy`s
/// besuchsbasierte Stichprobe unverändert weiter, jetzt über die
/// Welten-SUMME statt einer einzelnen Welt), `Q = Σ(Value)/Σ(Besuche)` über
/// alle Welten, in denen die Aktion tatsächlich zu einem Wurzelkind wurde
/// (kleineres Pro-Welt-Sims-Budget kann dazu führen, dass eine Aktion nicht
/// in JEDER Welt besucht wird -- trägt dann einfach 0 bei). Aktions-
/// Gleichheit als Schlüssel ist korrekt, siehe `NUM_DETERMINIZATIONS`-
/// Kommentar (weltunabhängige Wurzel-Kandidaten).
fn aggregate_root_child_stats(forest: &[Vec<Node>]) -> Vec<(Action, u32, f64)> {
    let mut acc: Vec<(Action, u32, f64)> = Vec::new(); // (action, visits_sum, value_sum)
    for nodes in forest {
        for &cid in &nodes[0].children {
            let node = &nodes[cid];
            let Some(a) = node.action.clone() else { continue };
            match acc.iter_mut().find(|(act, _, _)| *act == a) {
                Some(entry) => {
                    entry.1 += node.visits;
                    entry.2 += node.value;
                }
                None => acc.push((a, node.visits, node.value)),
            }
        }
    }
    acc.into_iter()
        .map(|(a, v, val_sum)| (a, v, if v > 0 { val_sum / v as f64 } else { 0.0 }))
        .collect()
}

/// Mittelt `root_completed_q_policy` (completed-Q-Softmax an der Wurzel, je
/// Welt über `improved_policy(nodes, 0)`) über den Determinisierungs-Wald,
/// Aktions-Schlüssel = die Aktion selbst (siehe `NUM_DETERMINIZATIONS`-
/// Kommentar: Wurzel-Kandidaten sind weltunabhängig, jede Aktion sollte
/// daher in JEDER Welt genau einmal auftauchen). Defensiv trotzdem robust
/// gegen eine in einzelnen Welten fehlende Aktion (Mittelwert nur über die
/// Welten, in denen sie auftaucht, plus Renormalisierung am Ende, falls die
/// Summe dadurch von 1.0 abweicht).
fn average_completed_q_policy(forest: &[Vec<Node>]) -> Vec<(Action, f64)> {
    let per_world: Vec<Vec<(Action, f64)>> =
        forest.iter().map(|nodes| root_completed_q_policy(nodes)).collect();
    let Some(reference) = per_world.first() else { return Vec::new() };
    let mut out: Vec<(Action, f64)> = Vec::with_capacity(reference.len());
    for (act, _) in reference {
        let mut sum = 0.0f64;
        let mut count = 0usize;
        for world in &per_world {
            if let Some(&(_, p)) = world.iter().find(|(a, _)| a == act) {
                sum += p;
                count += 1;
            }
        }
        out.push((act.clone(), if count > 0 { sum / count as f64 } else { 0.0 }));
    }
    let total: f64 = out.iter().map(|(_, p)| p).sum();
    if total > 0.0 {
        for entry in out.iter_mut() {
            entry.1 /= total;
        }
    }
    out
}

/// Exakte, JETZT SCHON feststehende Floor-Straf-Differenz (Spieler0 minus
/// Spieler1) dieser Runde, roh (unskaliert). KEINE Vorhersage — reine
/// State-Funktion (`PlayerBoard::broken_penalty`, board.rs), verfügbar ohne
/// jeden Netz-Forward-Pass. Motivation: `execute_place`/`add_to_penalty`
/// (execution.rs) legen Überlauf-Fliesen zu 100% deterministisch beim
/// Anwenden eines Zugs fest — die resultierende Strafe ist beim Expandieren
/// eines PUCT-Knotens (`apply_drafting` ist da schon gelaufen) bereits exakt
/// bekannt, lange bevor irgendeine Runde endet und offiziell verrechnet wird.
/// Der Value-Head bekommt die rohe Fliesenanzahl zwar als Input-Feature
/// (`features.rs`, `floor_n/4`), muss die NICHTLINEARE, eskalierende
/// Strafskala (`BROKEN_PENALTIES` = -1,-2,-3,-4) aber selbst lernen UND
/// korrekt gegen den unsicheren Rest der Partie abwägen — genau dort ist der
/// Value-Head laut Rundenabhängigkeits-Befund (siehe
/// `project_v8d_value_head_root_cause`-Memory) am schwächsten. Diese
/// Korrektur reicht die exakt bekannte Teilinformation direkt durch, statt
/// darauf zu vertrauen, dass das Netz sie selbst wiederentdeckt.
///
/// Zwei Quellen, BEIDE exakt/deterministisch, BEIDE nötig (Nutzer-Hinweis --
/// Boden entsteht nicht nur beim Drafting-Überlauf): `broken_penalty()`
/// zählt bereits MATERIALISIERTE Strafleisten-Fliesen (Drafting-Überlauf,
/// `execution.rs::add_to_penalty`); `round_end::projected_unplaceable_penalty`
/// preist zusätzlich die beim NÄCHSTEN Drafting→Tiling-Übergang fällige
/// Strafe für schon jetzt erkennbar unplatzierbare Reihen ein
/// (`round_end.rs::process_unplaceable_rows`) — komponiert korrekt mit dem
/// MAX_BROKEN-Deckel der ersten Quelle (siehe dortiger Kommentar: selbst der
/// exakte DFS-Solver preist das NICHT ein). Ohne diese zweite Quelle sieht
/// die Korrektur an einem Rundenende-Knoten oft noch 0 Boden, obwohl er beim
/// tatsächlichen Übergang unausweichlich feststeht.
fn floor_shaping_delta(state: &GameState) -> f64 {
    let (mine, theirs) = floor_penalties(state);
    (mine - theirs) / FLOOR_SHAPING_SCALE
}

/// Rohe (unskalierte) Floor-Strafsumme je Spieler -- Extraktion aus
/// `floor_shaping_delta`, damit `floor_shaping_delta_ego` (Eskalationsstufe
/// E2, Gegner-Bias) dieselben zwei Quellen ohne Doppelpflege wiederverwendet.
fn floor_penalties(state: &GameState) -> (f64, f64) {
    let mine = (state.players[0].broken_penalty()
        + crate::round_end::projected_unplaceable_penalty(&state.players[0])) as f64;
    let theirs = (state.players[1].broken_penalty()
        + crate::round_end::projected_unplaceable_penalty(&state.players[1])) as f64;
    (mine, theirs)
}

// ── Langreihen-Initiierung (PREREG_long_row_payoff.md par.3/B1) ─────────────

/// Skala fuer das Langreihen-Initiierungs-Additiv. **NICHT von
/// `FLOOR_SHAPING_SCALE`/`VALUE_SCALE` uebernommen** -- siehe
/// `PREREG_floor_shaping_scale.md`: dort ist nachgerechnet, dass ein Nenner
/// 50 fuer einen Zaehler mit kleiner Spanne die `tanh` dekorativ macht (der
/// Term bleibt vollstaendig im linearen Zipfel).
///
/// Hier laeuft der Zaehler nur ueber `[-2, +2]` (Differenz der Zahl
/// begonnener langer Reihen). Nenner 10 legt das maximale `tanh`-Argument auf
/// `0,2` und damit den maximalen Blattwert-Shift bei `w = 0,3` auf `0,059` --
/// dieselbe Groessenordnung wie der Floor-Term, der EINZIGE Blattwert-Term
/// mit nachgewiesener Staerkewirkung (11,25 pp, McNemar p=0,0001). Mit
/// Nenner 50 waere der Shift `0,012` gewesen, also fuenfmal schwaecher.
/// Nutzer-Entscheid 2026-08-24.
const LONG_ROW_INIT_SHAPING_SCALE: f64 = 10.0;

/// Musterreihen-Indizes der langen Reihen. Zentral in `board.rs`, damit das
/// Such-Additiv hier und die Arena-Zaehler (`execution.rs`, `round_end.rs`)
/// nicht auseinanderlaufen koennen: sonst koennte der Mitschrieb eine andere
/// Reihenmenge zaehlen als der Knopf bewegt.
use crate::board::LONG_ROW_INDICES;

/// Zahl der BEGONNENEN langen Musterreihen (mindestens eine Fliese), `0..=2`.
/// **Stufenfunktion am Uebergang 0 -> 1, kein Fuellstands-Anteil** -- das ist
/// der ganze Punkt des Terms (par.2a: die Luecke sitzt im Beginnen, nicht im
/// Fortsetzen).
fn long_rows_started(player: &crate::board::PlayerBoard) -> f64 {
    LONG_ROW_INDICES
        .iter()
        .filter(|&&i| !player.pattern_lines[i].tiles.is_empty())
        .count() as f64
}

/// Ego-perspektivische Differenz begonnener langer Reihen, skaliert --
/// dieselbe Bauform wie `floor_shaping_delta_ego` bei `opp_bias = 1.0`
/// (Nullsummen-Additiv, kein systematischer Versatz auf der Blattwertskala).
fn long_row_init_delta(state: &GameState, ego: usize) -> f64 {
    let own = long_rows_started(&state.players[ego]);
    let opp = long_rows_started(&state.players[1 - ego]);
    (own - opp) / LONG_ROW_INIT_SHAPING_SCALE
}

/// Eskalationsstufe E2 (`evaluations/PREREG_aggression_style_measurement.md`,
/// `MOSAIC_FLOOR_SHAPING_OPP_BIAS`): verallgemeinert `floor_shaping_delta`
/// von der festen Spieler0-minus-Spieler1-Differenz auf eine EGO-
/// perspektivische, asymmetrisch gewichtete Fassung:
/// `delta_ego = (own - opp_bias * opp) / FLOOR_SHAPING_SCALE`, wobei `own`
/// die Floor-Strafsumme von `ego` und `opp` die des jeweils ANDEREN Spielers
/// ist. Vorzeichenkonvention wie beim Bestand: `own`/`mine` = weniger
/// negativ = besser fuer `ego` (die eigene Strafe soll klein sein), `opp`
/// wird mit `opp_bias` skaliert, BEVOR es abgezogen wird -- `opp_bias>1`
/// gewichtet eine hohe GEGNER-Strafe staerker als die eigene, `opp_bias=1`
/// ist exakt die alte, symmetrische Definition (own - opp, ungewichtet).
///
/// Bei `opp_bias == 1.0` liefert dies fuer `ego=0` bit-identisch denselben
/// Wert wie `floor_shaping_delta` (Multiplikation mit exakt `1.0` rundet
/// nie, siehe IEEE754) -- die Aufrufstellen verzweigen trotzdem explizit
/// auf den alten Ausdruck, um jeden Zweifel an Bit-Identitaet auszuschliessen
/// (kein Vertrauen auf `tanh`s exakte Ungeradheit ueber Systemgrenzen).
fn floor_shaping_delta_ego(state: &GameState, ego: usize, opp_bias: f64) -> f64 {
    let (mine, theirs) = floor_penalties(state);
    let (own, opp) = if ego == 0 { (mine, theirs) } else { (theirs, mine) };
    (own - opp_bias * opp) / FLOOR_SHAPING_SCALE
}

// ── Wertungsplatten-Shaping (Task #93) ──────────────────────────────────────
// Rekonstruiert 2026-07-27 aus Commit 3b7f36b/344970f (Worktree
// `worktree-plate-shaping`, nach der A/B-Messung aufgeraeumt/geloescht) --
// Nutzer-Anstoss: erneut fuer einen Folgetest (Task #5, Rang-Invarianz-
// Hypothese der Gumbel-Suche) brauchbar machen. Inhaltlich UNVERAENDERT
// gegenueber dem Original, siehe evaluations/STATUS.md Abschnitt
// "Wertungsplatten-Shaping A/B (Task #93, 2026-07-25)" fuer das damalige
// A/B-Ergebnis (p=0.7111, GEGEN Merge -- ENABLED bleibt daher `false`).

/// Skala für das Wertungsplatten-Fortschritts-Additiv, gleiche Größenordnung
/// wie `FLOOR_SHAPING_SCALE`/`VALUE_SCALE` (50.0) -- macht die Korrektur
/// direkt vergleichbar mit dem own-minus-opp-Score-Margin, das `value`/
/// `points_forecast` schon als Trainingsziel verwenden (gleiche Begründung
/// wie bei `FLOOR_SHAPING_SCALE`).
const PLATE_SHAPING_SCALE: f64 = 50.0;

/// Gewicht des Wertungsplatten-Fortschritts-Additivs relativ zum
/// Netz-Blattwert (Task #93, analog `FLOOR_SHAPING_WEIGHT`). Startwert 0.3
/// aus Analogie zum validierten Floor-Shaping übernommen -- war der
/// A/B-Testgegenstand (siehe `PLATE_SHAPING_ENABLED`-Kommentar für das
/// Ergebnis), NICHT weiter rekalibriert (der Toggle blieb aus, eine
/// Fein-Kalibrierung des Gewichts wäre reine Spekulation ohne neuen Beleg).
pub const PLATE_SHAPING_WEIGHT: f64 = 0.3;

/// Toggle für das Wertungsplatten-Shaping (Task #93, Compile-Konstante --
/// Arm OFF/ON per Wheel-Rebuild wie beim Value-Shrinkage-A/B, siehe
/// `VALUE_SHRINK_ENABLED`). `false` (Standard) = byte-identisches
/// Bestandsverhalten, der Additiv-Block in `make_node` wird dann gar nicht
/// erst ausgeführt (siehe `apply_plate_shaping`). Paritätstest:
/// `plate_shaping_disabled_is_exact_identity`.
///
/// GEPAARTER A/B GEFAHREN (2026-07-25, `tools/paired_arena_plate_ab.py`,
/// `v15_best`@400 vs. `v14b_best`@400, 100 seed-gepaarte Spiele je Arm,
/// identischer Basis-Seed 9315 in beiden Armen): Arm OFF 58:42 (Score 35.3
/// vs. 31.0, Floor 14.2 vs. 17.4), Arm ON 61:39 (Score 35.9 vs. 29.2, Floor
/// 13.7 vs. 17.8) -- ON liegt zwar numerisch vorn, aber die Diskordanz
/// (b=16 ON-only-Siege, c=13 OFF-only-Siege) ist klein und nicht signifikant
/// (exakter McNemar p=0.7111). Evidenzregel (siehe MEMORY.md/STATUS.md-
/// Präzedenzfälle, z.B. `VALUE_SHRINK_ENABLED`) verlangt p<0.05 UND Vorteil
/// für ON -- nur Ersteres fehlt hier klar. Bleibt daher AUS. Details:
/// `evaluations/STATUS.md` Abschnitt "Wertungsplatten-Shaping A/B (Task #93,
/// 2026-07-25)".
pub const PLATE_SHAPING_ENABLED: bool = false;

/// Exakte, JETZT SCHON feststehende Wertungsplatten-Fortschritts-Differenz
/// (Spieler0 minus Spieler1) -- reine State-Funktion
/// ([`crate::scoring::scoring_progress`], dieselbe stetige Fortschritts-
/// Heuristik, die die DFS-Blattbewertung in `mcts.rs::player_total` schon
/// lange nutzt), KEIN Netz-Forward-Pass, analog `floor_shaping_delta`.
/// `scoring_progress` selbst fällt bei voller Plattenfüllung exakt auf den
/// echten `calculate_end_scoring`-Punktwert zurück (siehe dortiger
/// Kommentar) -- keine Doppelzählung mit dem tatsächlichen Endwertungs-Score.
fn plate_shaping_delta(state: &GameState) -> f64 {
    let mine = scoring_progress(&state.players[0], &state.scoring_tile_ids);
    let theirs = scoring_progress(&state.players[1], &state.scoring_tile_ids);
    (mine - theirs) / PLATE_SHAPING_SCALE
}

/// Wendet das Wertungsplatten-Shaping-Additiv (Task #93, Experiment
/// "Marginal-Delta" 2026-07-27, Task #8) auf BEIDE Blattwert-Perspektiven
/// `[Spieler0, Spieler1]` an -- muss NACH dem Floor-Shaping-Additiv
/// aufgerufen werden (koexistiert additiv, siehe Aufrufstelle in
/// `make_node`). Bei `PLATE_SHAPING_ENABLED=false` (Standard) exakte
/// Identität -- der Block wird komplett übersprungen, nicht nur numerisch
/// neutralisiert, damit garantiert byte-identisches Bestandsverhalten
/// erhalten bleibt.
///
/// URSPRUENGLICHE Version (Task #93) wandte `tanh` auf den ABSOLUTEN
/// `plate_shaping_delta(state)` an -- A/B-Nullergebnis (p=0.7111). Task #5
/// (Gumbel-Rang-Invarianz-Diagnose) liefert die Erklaerung: alle
/// Geschwister-Kandidaten eines Knotens teilen denselben grossen
/// Baseline-Fortschritt (nur EIN Zug unterscheidet sie), `tanh` an dieser
/// Stelle hat dort eine kleine Ableitung (`tanh'(baseline)` sinkt mit
/// wachsendem |baseline|) -- die tatsaechlich entscheidungsrelevante
/// MARGINALE Differenz zwischen Geschwistern wird dadurch mit `tanh'
/// (baseline)` gedaempft, nicht durch `tanh'(0)=1` wie beabsichtigt.
/// Fix: `tanh` auf die Differenz zum ELTERNKNOTEN anwenden (isoliert den
/// Beitrag GENAU dieses Zugs, eliminiert die gemeinsame Baseline VOR der
/// Nichtlinearitaet statt danach). Bei fehlendem Elternknoten (Wurzel --
/// hat keine Geschwister-Vergleichsbasis) bleibt der Shift 0.
fn apply_plate_shaping(value: [f64; 2], state: &GameState, parent_state: Option<&GameState>) -> [f64; 2] {
    if !PLATE_SHAPING_ENABLED {
        return value;
    }
    let shift = PLATE_SHAPING_WEIGHT * plate_shaping_marginal(state, parent_state).tanh();
    [(value[0] + shift).clamp(0.0, 1.0), (value[1] - shift).clamp(0.0, 1.0)]
}

/// Marginaler Wertungsplatten-Fortschrittsbeitrag GENAU des Zugs, der von
/// `parent_state` zu `state` führte -- isoliert von der gemeinsamen
/// Baseline (siehe `apply_plate_shaping`-Kommentar). `None` (Wurzel, kein
/// Elternknoten) -> 0.0 (kein Shift, keine Geschwister-Vergleichsbasis).
/// Eigene, ungated Funktion (nicht hinter `PLATE_SHAPING_ENABLED`), damit
/// die reine Formel unabhängig vom Toggle testbar ist.
fn plate_shaping_marginal(state: &GameState, parent_state: Option<&GameState>) -> f64 {
    match parent_state {
        Some(ps) => plate_shaping_delta(state) - plate_shaping_delta(ps),
        None => 0.0,
    }
}

// ── Wertungsplatten-EGO-Shaping (Nutzer-Auftrag 2026-08-10) ─────────────────
// Eigenstaendiges, VOM Task-#93-Plattenshaping oben UNABHAENGIGES Additiv --
// nicht zu verwechseln, drei Unterschiede:
//   1. Formel: `scoring_progress_alpha` (parametrisierter Exponent, eigene
//      Funktion in `scoring.rs`) statt `scoring_progress` (fest `alpha=2`,
//      der Heuristik-Anker -- bleibt unangetastet, siehe dortige Doku).
//   2. Perspektive: JE SPIELER ABSOLUT, NICHT ego-only (Nutzer-Korrektur
//      2026-08-11 -- "ego-only" war eine falsche Lesart der urspruenglichen
//      Formulierung: BEIDE Spieler bekommen unabhaengig einen Shift aus
//      ihrem EIGENEN Brett, `value[i] += w*tanh(f(players[i])/scale)` fuer
//      i in {0,1} getrennt -- sonst wuerde die Suche annehmen, der GEGNER
//      ignoriere die Wertungsplatten, exakt die Self-Play-Blindheit nur
//      innerhalb der Suche. "NUR das eigene Brett" heisst NUR: kein
//      Cross-Term zwischen den Spielern (Index i haengt nicht von
//      `players[1-i]` ab) -- NICHT, dass der Gegner-Fortschritt ignoriert
//      wird. KEINE mine-minus-theirs-Differenz wie `plate_shaping_delta`
//      (stehende, unabhaengig begruendete Anforderung: eine Differenzform
//      macht 55:50 schlechter als 30:15, siehe Test `apply_wertung_shaping_
//      with_rejects_difference_form_same_margin_different_level`).
//   3. Absolut statt marginal: kein Eltern-Delta wie `plate_shaping_marginal`
//      (dessen Baseline-Trick loest ein Gumbel-Geschwistervergleichsproblem,
//      das hier nicht Gegenstand des Auftrags war).
//   4. Runtime-Knopf-Muster: zwei einfache `MOSAIC_*`-Env-Vars (Gewicht +
//      Exponent), analog `floor_shaping_weight`/`floor_shaping_opp_bias`
//      (OnceLock<f64>, EINMAL gelesen), statt eines Compile-Konstante-Togges
//      wie `PLATE_SHAPING_ENABLED`.
// Beide Additive sind unabhaengig voneinander AN/AUS-schaltbar und komponieren
// rein additiv, falls beide je aktiviert wuerden (hier: Anwendungsreihenfolge
// NACH dem Plattenshaping oben, siehe Aufrufstellen in `make_node`/
// `net_leaf_eval`).

/// Skala fuer das Wertungsplatten-EGO-Shaping, gleiche Groessenordnung wie
/// `FLOOR_SHAPING_SCALE`/`PLATE_SHAPING_SCALE` (beide 50.0) -- macht die
/// Korrektur direkt vergleichbar mit dem own-minus-opp-Score-Margin, das
/// `value`/`points_forecast` schon als Trainingsziel verwenden (`VALUE_SCALE`
/// in `neural_net.py`, ebenfalls 50.0). Eigene Konstante statt Wiederverwendung
/// von `PLATE_SHAPING_SCALE` -- unabhaengig nachkalibrierbar, ohne das andere
/// (unabhaengige) Additiv zu beeinflussen.
const WERTUNG_SHAPING_SCALE: f64 = 50.0;

/// Default-Gewicht des Wertungsplatten-EGO-Shaping-Additivs -- `0.0` = AUS,
/// exakt Bestandsverhalten (kein Netz-Blattwert je durch dieses Additiv
/// veraendert, solange `MOSAIC_WERTUNG_SHAPING_W` ungesetzt bleibt).
pub const WERTUNG_SHAPING_WEIGHT: f64 = 0.0;

/// Default-Exponent `alpha` fuer `scoring_progress_alpha` -- `2.0` reproduziert
/// exakt den Exponenten, den der Heuristik-Anker (`scoring_progress`,
/// `.powi(2)`) fest verwendet; nur bei `alpha != 2.0` weicht die Formung von
/// der Heuristik ab.
pub const WERTUNG_SHAPING_ALPHA: f64 = 2.0;

/// Laufzeit-Wert von `MOSAIC_WERTUNG_SHAPING_W` -- gleiches OnceLock-Muster
/// wie `floor_shaping_weight` (einmalig gelesen, kein GUI-Live-Regler
/// vorgesehen, anders als `points_utility_w`s `AtomicU64`-Zelle -- dafuer gibt
/// es hier keinen Anwendungsfall). Ohne gesetzte Env-Var byte-identisches
/// Bestandsverhalten (Default `WERTUNG_SHAPING_WEIGHT` = 0.0).
pub fn scoring_shaping_weight() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_WERTUNG_SHAPING_W", WERTUNG_SHAPING_WEIGHT))
}

thread_local! {
    /// Plattengewicht der AKTUELLEN Partie in DIESEM Thread. `None` = der
    /// prozessweite Env-Wert gilt (Bestandsverhalten).
    static PARTIE_GEWICHT: std::cell::Cell<Option<f64>> = const { std::cell::Cell::new(None) };
}

/// Setzt das Wertungsplatten-Gewicht fuer die aktuelle Partie in DIESEM Thread.
///
/// WARUM THREAD-LOKAL und nicht prozessweit (Nutzer-Auftrag 2026-08-11: *"nimm als
/// hinweis fuers self play mit, dass wir je spiel auch das gewicht des
/// wertungsplattenshapings anpassen sollten. dann bekommt der ownership head
/// ordentlich was zu sehen"*): Self-Play spielt mehrere Partien GLEICHZEITIG in
/// Threads. Ein prozessweiter Wert -- wie ihn `MOSAIC_WERTUNG_SHAPING_W` ueber
/// `OnceLock` liefert -- waere fuer alle laufenden Partien derselbe, und die
/// Streuung entstuende gar nicht. Muster uebernommen von `STATS_OVERRIDE` in
/// `tiling_solver.rs`.
///
/// `None` stellt das Bestandsverhalten wieder her. Aufrufer MUSS am Partieende
/// zuruecksetzen, sonst leckt der Wert in die naechste Partie desselben Threads.
pub fn set_game_shaping_weight(w: Option<f64>) {
    PARTIE_GEWICHT.with(|c| c.set(w));
}

/// PREREG_ownership_corpus.md §3 Punkt 6: Fuehrt `f` mit AUSGESETZTER
/// Partie-STREUUNG aus (`PARTIE_GEWICHT` auf DIESEM Thread kurzzeitig
/// `None`) -- fuer Label-Rollouts (`round_transition_deep.rs`s
/// `bootstrap_value_after_rounds`/`continue_through_round{2,3,4}`), NICHT
/// fuer die eigentliche Suche/Zugwahl.
///
/// WARUM: `bootstrap_value`/`round_transition_value` sollen den
/// tatsaechlich erwartbaren Spielausgang moeglichst rauscharm schaetzen.
/// `PARTIE_GEWICHT` ist aber ein je Partie ZUFAELLIG aus dem Partie-Seed
/// abgeleiteter Wert (`game_weight_from_seed`, `MOSAIC_WERTUNG_STREUUNG_MAX`)
/// -- ohne diese Aussetzung wuerde derselbe Zustand im Trainingsziel rein
/// durch den Wuerfelwurf DIESER Partie anders bewertet, ohne jeden Bezug zum
/// echten Ausgang (die Suche/Zugwahl DARF diese Streuung weiterhin sehen --
/// das ist ihr eigentlicher Zweck, siehe `set_game_shaping_weight`-Doku:
/// mehr Vielfalt fuers Self-Play/den Ownership-Kopf; nur die LABEL-Rechnung
/// nicht).
///
/// Der PROZESSWEITE Basiswert (`MOSAIC_WERTUNG_SHAPING_W`, konstant ueber
/// alle Partien, seit laenger bestehend) bleibt bewusst WIRKSAM: faellt
/// `PARTIE_GEWICHT` auf `None` zurueck, liest `scoring_shaping_weights()`
/// wieder den Env-Wert (siehe dortiger Code) -- das ist die bestehende,
/// in `net_leaf_eval`s eigener Doku ausdruecklich gewollte Kopplung
/// ("gilt unveraendert fuer JEDEN net_leaf_eval-Aufrufer ... eingeschlossen"),
/// nicht Gegenstand dieser Frage und hier nicht angetastet.
///
/// RAII statt eines manuellen "danach zuruecksetzen": Rust fuehrt `Drop`
/// beim Stack-Unwinding auch bei einem Panic MITTEN in `f` aus -- ein
/// Fehlschlag tief in der rekursiven Simulation wuerde die Streuung sonst
/// fuer den Rest der Partie auf demselben (wiederverwendeten) Thread
/// verschlucken.
pub(crate) fn with_game_scatter_suspended<T>(f: impl FnOnce() -> T) -> T {
    let prev = PARTIE_GEWICHT.with(|c| c.get());
    struct Restore(Option<f64>);
    impl Drop for Restore {
        fn drop(&mut self) {
            PARTIE_GEWICHT.with(|c| c.set(self.0));
        }
    }
    let _restore = Restore(prev);
    PARTIE_GEWICHT.with(|c| c.set(None));
    f()
}

/// Streubreite fuer das partieweise Gewicht, `MOSAIC_WERTUNG_STREUUNG_MAX`.
/// Default **0,0 = aus**, dann gilt ausschliesslich der prozessweite Env-Wert.
/// Bei `> 0` leitet [`game_weight_from_seed`] je Partie einen Wert in
/// `[0, max]` ab.
pub fn scoring_scatter_max() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_WERTUNG_STREUUNG_MAX", 0.0))
}

/// Deterministische Ableitung des Partiegewichts aus dem Partie-Seed.
///
/// Reproduzierbar (kein Zufall zur Laufzeit -- dieselbe Partie ergibt dasselbe
/// Gewicht), gleichverteilt in `[0, max]`. Die Mischung ist der
/// SplitMix64-Finalizer; er wird gebraucht, weil aufeinanderfolgende Partie-Seeds
/// im Self-Play sich oft nur in den unteren Bits unterscheiden und eine rohe
/// Modulo-Bildung dann eine Treppe statt einer Streuung ergaebe.
pub fn game_weight_from_seed(seed: u64, max: f64) -> f64 {
    let mut z = seed.wrapping_add(0x9E37_79B9_7F4A_7C15);
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^= z >> 31;
    max * ((z % 1_000_000) as f64 / 999_999.0)
}

/// PREREG_search_rng_split.md: Such-RNG von der Partie trennen. Leitet einen
/// EIGENEN, deterministischen Seed fuer EINE Such-/Entscheidungs-Episode aus
/// `(game_seed, move_index)` ab -- Praezedenz `game_weight_from_seed` oben
/// (gleicher SplitMix64-Finalizer), hier zweistufig, weil ZWEI Eingaben statt
/// einer gemischt werden muessen: erst `game_seed` durch den Finalizer, dann
/// `move_index` addiert und NOCHMAL durch den Finalizer -- eine simple
/// Summe/XOR beider Werte waere bei benachbarten `move_index`-Werten
/// (0,1,2,...) nur eine Treppe in den unteren Bits, keine echte Streuung.
///
/// Aufrufer (self_play.rs/py.rs, siehe dortige Kommentare) bauen daraus
/// `StdRng::seed_from_u64(derive_search_seed(...))` und geben DIESE Instanz
/// an die Suche/Entscheidungs-Sampling weiter -- NICHT mehr den echten
/// Partie-RNG. Der Partie-RNG selbst wird dadurch nur noch durch ECHTE
/// Spielzustands-Ereignisse (`Game::start`, `Bag::refill_from_tower` über
/// `apply_tiling`s `EndTiling`) verbraucht, deren Haeufigkeit NICHT von der
/// Suchtiefe (sims) abhaengt -- das ist der Kern des Schnitts (Prereg §2/§5).
pub fn derive_search_seed(game_seed: u64, move_index: u64) -> u64 {
    let mut z = game_seed.wrapping_add(0x9E37_79B9_7F4A_7C15);
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^= z >> 31;
    z = z.wrapping_add(move_index.wrapping_add(0x9E37_79B9_7F4A_7C15));
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^= z >> 31;
    z
}

/// `MOSAIC_WERTUNG_SHAPING_W` als **acht Werte, einer JE KRITERIUM** -- gleiches
/// Format und gleiche Haerte wie `scoring_shaping_alphas` (1 Wert gilt fuer alle;
/// falsche Laenge wird VERWORFEN, nicht teilgelesen).
///
/// WARUM ein Gewicht je Kriterium und nicht nur ein alpha je Kriterium
/// (Nutzer-Aufbau 2026-08-11): der Versuch will *"20 Spiele in denen die
/// vertikalen Wertungsplatten aktiv sind, NUR mit alpha variation der vertikalen
/// platten"*. Dafuer muessen die anderen Kriterien AUS sein, sonst laeuft jede
/// Messung gegen einen Hintergrund aus sieben weiteren Shaping-Termen und der
/// Effekt ist nicht mehr zurechenbar.
///
/// **Und alpha kann das nicht leisten**: ein Kriterium abzuschalten geht ueber den
/// Exponenten nicht -- ein hohes alpha drueckt den Teilfortschritt nur
/// asymptotisch gegen 0, `(1.0)^alpha` bleibt 1. Nur ein Gewicht 0 schaltet
/// wirklich ab. "Nur die Vertikale" heisst damit `0,1,0,0,0,0,0,0`.
pub fn scoring_shaping_weights() -> [f64; 8] {
    // Partieweiser Wert schlaegt den prozessweiten -- siehe
    // `set_game_shaping_weight`.
    if let Some(w) = PARTIE_GEWICHT.with(|c| c.get()) {
        return [w; 8];
    }

    static CELL: std::sync::OnceLock<[f64; 8]> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| {
        let mut out = [WERTUNG_SHAPING_WEIGHT; 8];
        let Ok(raw) = std::env::var("MOSAIC_WERTUNG_SHAPING_W") else { return out };
        let parts: Vec<&str> = raw.split(',').map(|p| p.trim()).filter(|p| !p.is_empty()).collect();
        let vals: Option<Vec<f64>> = parts.iter().map(|p| p.parse::<f64>().ok()).collect();
        match vals.as_deref() {
            Some([one]) => out = [*one; 8],
            Some(v) if v.len() == 8 => out.copy_from_slice(v),
            _ => eprintln!(
                "MOSAIC_WERTUNG_SHAPING_W={raw:?} ignoriert -- erwartet 1 oder 8 Zahlen, Default {WERTUNG_SHAPING_WEIGHT} gilt"
            ),
        }
        out
    })
}

/// Laufzeit-Wert von `MOSAIC_WERTUNG_ALPHA` -- **acht Werte, einer JE KRITERIUM**
/// (Nutzer-Vorgabe 2026-08-11: *"wir wollen ja alpha pro wertungsplatte seperat
/// festlegen"*). Format: kommagetrennt in Kriterien-Reihenfolge 0..7, z.B.
/// `2,6,9,2,2,2.6,2,2`. **Ein einzelner Wert gilt fuer alle** (Rueckwaerts-
/// kompatibilitaet und bequem fuer globale A/Bs). Ungesetzt = alle
/// `WERTUNG_SHAPING_ALPHA` (2.0), also byte-identisches Bestandsverhalten.
///
/// Fehlerhafte oder unvollstaendige Listen fallen HART auf den Default zurueck --
/// kein stilles Teil-Parsen, sonst waere ein Tippfehler ein unbemerkt anderer
/// Versuch (vgl. `train.py --load`-Footgun).
pub fn scoring_shaping_alphas() -> [f64; 8] {
    static CELL: std::sync::OnceLock<[f64; 8]> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| {
        let mut out = [WERTUNG_SHAPING_ALPHA; 8];
        // Die alten Spezialfeld-Knoepfe sind seit der Zusammenfuehrung 2026-08-11
        // WIRKUNGSLOS (ein Gewicht, alphas[6] als Exponent). Ein still
        // wirkungsloser Regler ist gefaehrlicher als ein fehlender: jemand
        // setzt ihn, liest ein H0 und schliesst auf den Term. Deshalb laut.
        for alt_var in ["MOSAIC_UNLOCK_SHAPING_W", "MOSAIC_UNLOCK_BETA"] {
            if std::env::var(alt_var).is_ok() {
                eprintln!(
                    "{alt_var} ist WIRKUNGSLOS (seit 2026-08-11 zusammengefuehrt) --                      nutze MOSAIC_WERTUNG_SHAPING_W fuer das Gewicht und die 7. Stelle                      von MOSAIC_WERTUNG_ALPHA fuer den Spezialfeld-Exponenten."
                );
            }
        }
        let Ok(raw) = std::env::var("MOSAIC_WERTUNG_ALPHA") else { return out };
        let parts: Vec<&str> = raw.split(',').map(|p| p.trim()).filter(|p| !p.is_empty()).collect();
        let vals: Option<Vec<f64>> = parts.iter().map(|p| p.parse::<f64>().ok()).collect();
        match vals.as_deref() {
            Some([one]) => out = [*one; 8],
            Some(v) if v.len() == 8 => out.copy_from_slice(v),
            _ => eprintln!(
                "MOSAIC_WERTUNG_ALPHA={raw:?} ignoriert -- erwartet 1 oder 8 Zahlen, Default {WERTUNG_SHAPING_ALPHA} gilt"
            ),
        }
        out
    })
}

/// Laufzeit-Wert von `MOSAIC_WERTUNG_ROUND_GAIN` -- hebt ALLE Exponenten ueber die
/// Runden an: `alpha_c(r) = alpha_c * (1 + gain * (r-1)/4)`. Default **0,0** = keine
/// Rundenabhaengigkeit. Ersetzt die frueheren, einkompilierten kalibrierten
/// Zielwerte je Kriterium -- die waren nicht begruendbar, weil
/// `Mittel(x^alpha) > Rate` fuer JEDES alpha gilt (siehe `scoring.rs`-Doku).
/// Gewicht fuer den Strafleisten-Gegenterm im Wertungsplatten-Shaping.
/// Default **0,0** = aus, Bestandsverhalten.
///
/// WARUM (Nutzer: *"aber ja probier es aus"*, 2026-08-11): die HEURISTIK benutzt
/// `scoring_progress` nie allein, sondern als Mittelterm von
/// `player_total` (`mcts.rs:80-84`) -- daneben stehen der Tiling-Solver-Score UND
/// `projected_unplaceable_penalty`. Meine Injektion hatte nur den Mittelteil.
///
/// Zwei Gruende, es zu messen statt zu argumentieren:
///  1. GEMESSEN: die Injektion treibt die Strafleiste monoton hoch (+2,42 Pkt bei
///     w=1,0, t=+2,42) -- genau die Buesse, die dieser Term einpreist.
///  2. `projected_unplaceable_penalty` liest `player.pattern_lines`
///     (`round_end.rs:116-120`) und ist damit das EINZIGE verfuegbare Stueck des
///     Shapings, das die Musterreihen sieht. `scoring_progress` liest nur das
///     Kuppelraster und ist deshalb innerhalb einer Runde fuer JEDEN
///     Drafting-Zug gleich -- es kann die Wahl gar nicht lenken, dieser Term
///     kann es.
///
/// Gegenargument, das die Messung entscheiden soll: der Value-Kopf ist auf
/// AUSGAENGE trainiert, Strafpunkte gehen in den Ausgang ein -- er preist sie
/// also schon ein, und der Term koennte doppelt zaehlen.
pub fn scoring_floor_weight() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_WERTUNG_FLOOR_W", 0.0))
}

/// Gewicht fuer den **Tiling-Potenzial**-Term. Default **0,0** = aus.
///
/// HERKUNFT (Nutzer-Entscheid 2026-08-11, nach *"nichts davon"* zu meinen zwei
/// selbst erfundenen Musterreihen-Termen): NICHT nachbauen, sondern den nehmen,
/// den die Heuristik benutzt. `mcts.rs::player_total` besteht aus DREI
/// Summanden, und der erste ist der, der die Musterreihen sieht:
///
/// ```text
/// solve_round_final_score(state, pi)                  <- dieser hier
///   + scoring_progress(..)                            <- MOSAIC_WERTUNG_SHAPING_W
///   + projected_unplaceable_penalty(..)               <- MOSAIC_WERTUNG_FLOOR_W
/// ```
///
/// Warum meine beiden Eigenbauten (`MOSAIC_ENDAWARE_W`/`tiling_vorausschau`,
/// `MOSAIC_MUSTERREIHEN_W`/`crate::scoring::musterreihen_fortschritt`) INZWISCHEN
/// entfernt sind (2026-08-13, PREREG_scoring_plate_injection.md Abschnitt N7):
/// gemessen taten sie nichts. `MOSAIC_ENDAWARE_W` bei w=0,1 gab -0,07 Punkte
/// (t=-0,07), bei w=0,3 -2,16 (t=-1,21) ohne jeden Plattengewinn;
/// `MOSAIC_MUSTERREIHEN_W` bei w=0,1 -0,84 (t=-0,69). Dieser Traeger hier blieb
/// unangetastet -- er ist der aus der Heuristik uebernommene, nicht selbst
/// erfundene Term.
pub fn tiling_weight() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_TILING_W", 0.0))
}

/// Aus den HEUTIGEN Musterreihen erreichbare Platzierungspunkte.
///
/// `solve_round_final_score` liefert *aktueller Punktestand + max. Tiling-Punkte
/// + feste Boden-/Marker-Strafen* (`tiling_solver.rs:398`: `p.score + penalty +
/// solve_max_tiling_points`). Der Punktestand wird ABGEZOGEN -- Nutzer-Entscheid
/// "nur der Tiling-Anteil". Zwei Gruende, und beide zaehlen:
///  1. Er ist fuer alle Geschwisterzuege GLEICH und traegt zur Zugwahl nichts bei.
///  2. Er liegt bei ~50 Punkten und wuerde `tanh(pts/50)` saettigen, womit auch
///     der variable Rest keine Wirkung mehr haette.
///
/// Die Differenz ist keine Erfindung: `tiling_solver.rs:1069` prueft genau sie
/// (`solve_round_final_score(&s,0) - s.players[0].score == 3`). Uebrig bleiben
/// Tiling-Punkte + feste Strafen, beides drafting-abhaengig, und beides in
/// Punkten -- dieselbe Einheit wie die Nachbarterme.
///
/// Ueberschneidung mit `projected_unplaceable_penalty` ist gewollt und spiegelt
/// die Heuristik: `penalty` sind die Strafen der SCHON gebrochenen Fliesen, der
/// andere Term preist die Fliesen in Reihen, die sich nicht mehr platzieren
/// lassen -- der Solver sieht dort nur "0 Punkte", nicht die Busse.
fn tiling_potenzial(state: &GameState, pi: usize) -> f64 {
    (crate::tiling_solver::solve_round_final_score(state, pi) - state.players[pi].score) as f64
}

pub fn scoring_round_gain() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_WERTUNG_ROUND_GAIN", 0.0))
}

/// Baustein 3 (`MOSAIC_WERTUNG_SCALE_PROFILE`, `PREREG_shaping_scale_per_
/// round.md` par.4): `profil_r` je Runde 1..5, gemessen aus dem
/// Punktestand-ANTEIL (nicht dem Punktestand selbst) ueber 22 Arena-Logs
/// (par.1) -- `SCALE_r = WERTUNG_SHAPING_SCALE * profil_r`.
const WERTUNG_SCALE_PROFILE: [f64; 5] = [0.083, 0.172, 0.327, 0.515, 0.825];

/// Laufzeit-Wert von `MOSAIC_WERTUNG_SCALE_PROFILE` -- Default **aus**
/// (ungesetzt, leer oder `"0"`) = flacher Nenner `WERTUNG_SHAPING_SCALE`
/// (50.0) fuer ALLE Runden, byte-identisches Bestandsverhalten. Gesetzt auf
/// `"1"` oder `"an"` = das rundenabhaengige Profil (par.4) gilt fuer den
/// Wertungsplatten-/Spezialfeld-Term in [`apply_scoring_shaping_full`] --
/// NICHT fuer den Strafleisten- oder den Tiling-Term, siehe dortige
/// Begruendung (par.6a).
pub fn scoring_scale_profile_active() -> bool {
    static CELL: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| match std::env::var("MOSAIC_WERTUNG_SCALE_PROFILE") {
        Ok(raw) => {
            let t = raw.trim();
            t == "1" || t.eq_ignore_ascii_case("an")
        }
        Err(_) => false,
    })
}

/// `SCALE_r` fuer Runde `round_number` (1-basiert, geklemmt auf 1..5, gleiche
/// Klemmung wie die bestehende `t`-Berechnung in [`apply_scoring_shaping_full`]).
/// Reine Funktion (kein Env-Zugriff) -- `profile_active` als Parameter, damit
/// Tests das OnceLock nicht umgehen muessen (gleiches Trennungsmuster wie
/// `apply_scoring_shaping_full` selbst).
fn scoring_scale_for_round(round_number: u32, profile_active: bool) -> f64 {
    if !profile_active {
        return WERTUNG_SHAPING_SCALE;
    }
    let idx = (round_number.clamp(1, 5) - 1) as usize;
    WERTUNG_SHAPING_SCALE * WERTUNG_SCALE_PROFILE[idx]
}

/// Reine Formel hinter [`apply_scoring_shaping`], OHNE Env-Var-Zugriff --
/// Gewichte/Exponenten als Parameter statt aus dem OnceLock-Cache gelesen,
/// gleiches Trennungsmuster wie `blended_leaf_win_prob`/`_with` (siehe
/// dortige Doku: ein Test, der den Env-Var-Cache nach dem ersten Zugriff
/// umstellen will, kaeme nie an sein Ziel). Frueher ueber zwei Test-Huellen
/// `apply_wertung_shaping_with`/`_with_alphas` aufgerufen (ausserhalb von
/// Tests nie gebraucht, deshalb entfernt -- Tests rufen diese Funktion jetzt
/// direkt mit `&[w; 8]`/`&[alpha; 8]` und den Gegenterm-Defaults `0.0`).
///
/// Fruehausstieg bei ALLEN Gewichten `== 0.0`: gibt `value` UNVERAENDERT
/// zurueck -- kein `scoring_progress_alpha`-Aufruf, kein `tanh`, keine
/// Rundung, also GARANTIERT numerisch identisch zum Vor-Additiv-Bestand
/// (exakt das Muster, das `blended_leaf_win_prob_with`s bestehender
/// `w == 0.0`-Kurzschluss schon fuer sein eigenes Gewicht vorgibt).
///
/// Skalierung: `scoring_progress_alpha` liefert PUNKTE, `value` sind
/// Gewinnwahrscheinlichkeiten -- Normierung ueber `tanh(punkte /
/// WERTUNG_SHAPING_SCALE)` (siehe dortige Doku), gleiche Konvention wie
/// `floor_shaping_delta`/`plate_shaping_delta`. JEDER Spieler bekommt seinen
/// EIGENEN, unabhaengigen Shift aus seinem EIGENEN Brett (`state.players[i]`)
/// -- keine mine-minus-theirs-Kopplung wie beim Plattenshaping oben, siehe
/// Modul-Kommentar. Ergebnis wird wie die bestehende Floor-/Platten-Additiv-
/// Logik auf `[0,1]` geklemmt.
///
/// Volle Form: Gewicht UND Exponent je Kriterium, plus den absoluten
/// Gegenterm (Strafleiste `floor_w`). Ein Gewicht 0 schaltet das jeweilige
/// Kriterium/Additiv vollstaendig ab -- das ist die Voraussetzung fuer den
/// Nutzer-Versuchsaufbau (je Satz nur EIN Kriterium injiziert).
///
/// Baustein 3 (`scale_profile_active`, `MOSAIC_WERTUNG_SCALE_PROFILE`,
/// `PREREG_shaping_scale_per_round.md` par.4/par.5/par.6a): wirkt NUR auf den
/// Nenner der Wertungsplatten-/Spezialfeld-Terme (die `bei`-Closure unten).
/// Der Strafleisten-Term (`floor_w`) und der Tiling-Term (`tiling_w`) bleiben
/// AUSDRUECKLICH auf dem flachen Nenner `WERTUNG_SHAPING_SCALE`, unabhaengig
/// vom Profil-Knopf -- par.6a Praezisierung (REGEL 0, geprueft, weicht vom
/// Prereg-Wortlaut ab): der DEFAULT von `floor_w` selbst
/// (`scoring_floor_weight()`/`MOSAIC_WERTUNG_FLOOR_W`) ist **0.0**, nicht
/// 0,3 -- der im Prereg zitierte Beleg "`floor_shaping_weight = 0,3`,
/// engine_config" (`lib.rs:631`) meint `FLOOR_SHAPING_WEIGHT`/
/// `floor_shaping_weight()` (`MOSAIC_FLOOR_SHAPING_W`), das GANZ ANDERE Floor-
/// Additiv in `blended_leaf_win_prob`/`floor_shaping_delta` -- eine separate
/// Funktion, die diese Closure gar nicht durchlaeuft. Der `floor_w`-Zweig
/// hier ist also per Default TOT (der fruehe `floor_w == 0.0`-Zweig unten
/// greift ohnehin nicht, weil der ganze Ausdruck schon durch den
/// Gesamt-Fruehausstieg abgefangen wird). Der flache Nenner bleibt trotzdem
/// EXPLIZIT gepinnt -- als Schutz fuer den Fall, dass jemand `MOSAIC_WERTUNG_
/// FLOOR_W` UND das Profil gleichzeitig setzt (nicht-default Kombination),
/// und weil `tiling_w` (`MOSAIC_TILING_W`, ebenfalls Default 0.0) aus
/// Symmetriegruenden analog behandelt wird.
fn apply_scoring_shaping_full(
    value: [f64; 2], state: &GameState, ws: &[f64; 8], alphas: &[f64; 8], round_gain: f64,
    floor_w: f64, tiling_w: f64, scale_profile_active: bool,
) -> [f64; 2] {
    if ws.iter().all(|w| *w == 0.0) && floor_w == 0.0 && tiling_w == 0.0 {
        return value;
    }
    let mut out = value;
    for i in 0..2 {
        // ALLE ACHT Kriterien in EINEM Term, EIN Gewicht (Nutzer-Korrektur
        // 2026-08-11: *"ich dachte das haengt zusammen"*).
        //
        // WARUM es zusammenhaengt: Kriterium 6 (Spezialfelder) IST eine der acht
        // Wertungsplatten. Es steckt aus Doppelzaehlungs-Gruenden nicht in
        // `scoring_progress_per_criterion` (dort liefert es 0), sondern in
        // `unlock_progress_beta` -- weil sein ⭐-Anteil UNGEGATET zahlt
        // (Grundwertung, Rasterreihe 1..6) und nur der -3-Anteil an der aktiven
        // Platte haengt. Vorher hingen die beiden an ZWEI Gewichten, und eine
        // Vorregistrierung von mir hat eines davon auf 0 gesetzt -- damit war
        // "alle Wertungsplatten injizieren" auf sieben verkuerzt.
        //
        // `alphas[6]` ist jetzt auch der Exponent des Freischalt-Terms: dieselbe
        // Bedeutung (wie steil zaehlt Teilfortschritt), nur mit Kapazitaet 3
        // statt 6. Damit deckt die achtstellige alpha-Liste tatsaechlich alle
        // acht Platten -- die Form, die der Versuchsplan "je Platte 20 Partien,
        // nur deren alpha" braucht.
        // Je Kriterium EINZELN gewichtet: `ws[k] == 0` laesst Kriterium k
        // vollstaendig weg. Deshalb je Kriterium ein eigener Aufruf mit
        // einelementiger tile_ids-Liste statt einem Sammelaufruf.
        // `w` muss AUSSEN am tanh bleiben, sonst ist es nicht mehr die
        // Obergrenze der Verschiebung: `tanh(w*P/50)` saettigt gegen 1
        // unabhaengig von w, `w*tanh(P/50)` gegen w. Bei Gewichten je Kriterium
        // gibt es kein einzelnes w -- also das GROESSTE aussen und innen darauf
        // normieren. Gleichmaessiger Fall: reproduziert `w*tanh(SUM pts/50)`
        // exakt. Isolierung (eins auf 1, Rest 0): `1*tanh(pts_k/50)`.
        // SUMME JE TERM, jeder mit EIGENEM Gewicht in EIGENER Schranke:
        //
        //     shift = SUM_term  w_term * tanh(P_term / SCALE)
        //
        // FEHLER, DER DAMIT BEHOBEN IST (2026-08-12, vom Nutzer an
        // bit-identischen Zellen erkannt): vorher gab es EIN gemeinsames
        // `pts` und davor ein `skala = max(alle Gewichte)`, innen normiert auf
        // `ws[k] / max(ws)`. Bei genau EINEM Null-verschiedenen
        // Kriteriumsgewicht `w` kuerzte sich `w` dadurch ZWEIMAL heraus --
        // innen als `w/w = 1`, aussen weil `max(w, floor_w, tiling_w)` bei
        // floor_w=tiling_w=1 immer 1 ergab. `w` war in der isolierten
        // Injektion wirkungslos, und nur `alpha` wirkte.
        //
        // Beide Bausteine waren einzeln begruendet: die Normierung, damit der
        // gleichmaessige Fall `w*tanh(SUM P/50)` exakt reproduziert; das `max`,
        // damit ein allein gesetzter Zusatzknopf nicht wirkungslos ist.
        // Zusammen hoben sie sich auf.
        //
        // Warum das Gewicht AUSSEN am jeweiligen tanh bleibt: `tanh(w*P/50)`
        // saettigt gegen 1 unabhaengig von w, `w*tanh(P/50)` gegen w -- nur die
        // zweite Form macht das Gewicht zur echten Obergrenze der Verschiebung.
        // Je Term ein eigenes tanh statt eines gemeinsamen, damit kein Term die
        // Schranke eines anderen mitbenutzt.
        //
        // NICHT rueckwaertskompatibel zum gleichmaessigen Fall: dort liefert die
        // neue Form `SUM_k w*tanh(P_k/50)` statt `w*tanh(SUM_k P_k/50)`. Gleiche
        // Richtung und Monotonie, andere Zahlen. Die Dosis-Kurve vom 11.08.
        // (w=0,03/0,1/0,3/1,0 gleichmaessig) ist damit unter der ALTEN Formel
        // gemessen und nicht mit neuen Zahlen vergleichbar.
        let t = ((state.round_number.clamp(1, 5) - 1) as f64) / 4.0;
        // Baustein 3: Nenner der Wertungsplatten-/Spezialfeld-Terme, gesteuert
        // von `MOSAIC_WERTUNG_SCALE_PROFILE` -- bei inaktivem Knopf identisch
        // zu `WERTUNG_SHAPING_SCALE` (byte-identisches Bestandsverhalten).
        let scale_r = scoring_scale_for_round(state.round_number, scale_profile_active);
        let bei = |x: f64| (x / scale_r).tanh();
        // Strafleisten-/Tiling-Term bleiben IMMER auf dem flachen Nenner --
        // siehe Funktionskommentar oben (par.6a-Praezisierung).
        let bei_flat = |x: f64| (x / WERTUNG_SHAPING_SCALE).tanh();
        let mut shift = 0.0;

        // Wertungsplatten, je Kriterium einzeln gewichtet und einzeln begrenzt.
        // `ws[k] == 0` laesst Kriterium k vollstaendig weg -- die Voraussetzung
        // fuer den Nutzer-Versuchsaufbau (je Satz nur EIN Kriterium injiziert).
        for &id in state.scoring_tile_ids.iter() {
            let k = (id as usize).min(7);
            if ws[k] == 0.0 {
                continue;
            }
            shift += ws[k] * bei(crate::scoring::scoring_progress_per_criterion(
                &state.players[i], &[id], alphas, state.round_number, round_gain,
            ));
        }
        // Spezialfelder: der Bonus-Anteil zahlt UNGEGATET, also unabhaengig von
        // `scoring_tile_ids` -- er haengt an `ws[6]`, nicht am Liegen der Platte.
        if ws[6] != 0.0 {
            let beta6 = alphas[6] * (1.0 + round_gain * t);
            shift += ws[6] * bei(crate::scoring::unlock_progress_beta(
                &state.players[i], &state.scoring_tile_ids, beta6,
            ));
        }
        // Strafleisten-Gegenterm: NEGATIV (Summe der BROKEN_PENALTIES).
        // Flacher Nenner (`bei_flat`), NICHT `scale_r` -- siehe
        // Funktionskommentar (par.6a).
        if floor_w != 0.0 {
            shift += floor_w * bei_flat(
                crate::round_end::projected_unplaceable_penalty(&state.players[i]) as f64);
        }
        // Tiling-Potenzial: der Musterreihen-Traeger aus der Heuristik.
        // Flacher Nenner, analog zum Strafleisten-Term (siehe oben).
        if tiling_w != 0.0 {
            shift += tiling_w * bei_flat(tiling_potenzial(state, i));
        }
        out[i] = (value[i] + shift).clamp(0.0, 1.0);
    }
    out
}

/// Laufzeit-Wrapper von [`apply_wertung_shaping_with`], liest `w`/`alpha` aus
/// den Prozess-weiten OnceLock-Caches (`scoring_shaping_weight()`/
/// `wertung_shaping_alpha()`) -- gleiches Trennungsmuster wie
/// `blended_leaf_win_prob`/`_with`. Aufrufstellen: `net_leaf_eval` (deckt
/// damit auch alle DESSEN Aufrufer ab -- `round_transition_deep.rs`,
/// `self_play.rs`, den Chance-Node-Zweig in `make_node` selbst) und
/// `make_node`s eigener `LeafEval::Net`-Zweig (der Haupt-Suchpfad, der NICHT
/// ueber `net_leaf_eval` laeuft, siehe dortige Duplizierung der Blend-Logik).
fn apply_scoring_shaping(value: [f64; 2], state: &GameState) -> [f64; 2] {
    apply_scoring_shaping_full(
        value, state, &scoring_shaping_weights(), &scoring_shaping_alphas(), scoring_round_gain(),
        scoring_floor_weight(), tiling_weight(), scoring_scale_profile_active(),
    )
}

// ── Ownership-Verbraucher Teil 1: Drafting/Blattbewertung ───────────────────
// `evaluations/PREREG_ownership_consumer.md` §2/§5/§6, freigegeben durch Tor A
// (`PREREG_ownership_corpus.md` §10). Der ZWEITE Pol neben dem Heuristik-Pol
// (`apply_scoring_shaping` oben): dort misst `scoring_progress_per_criterion`
// den IST-Fortschritt, hier prognostiziert das Netz die VOLLENDUNG. Gleiche
// Shift-Form, gleicher Rechen-Ort, eigener Regler.
//
// NUR die Drafting-Seite. Der Tiling-Verbraucher (§3, marginale Feldwerte im
// Solver) ist AUSDRUECKLICH nicht Teil dieses Schritts.

/// `MOSAIC_OWNERSHIP_W` -- der Zwei-Pole-Regler `w_own`. Default **0,0** =
/// Verbraucher TOT (Fruehausstieg in [`apply_ownership_shaping_full`], kein
/// Sigmoid, kein tanh, keine Rundung -> byte-identisches Bestandsverhalten,
/// Task-#28-Muster, siehe `blended_leaf_win_prob_with`s `w == 0.0`-Kurzschluss).
///
/// Prozessweit einmalig gelesen (`OnceLock`), wie alle Nachbarregler --
/// ein Test, der den Wert nach dem ersten Zugriff umstellen will, kaeme nie an
/// sein Ziel; die Formel ist deshalb ueber
/// [`apply_ownership_shaping_full`] ohne Env-Var direkt pruefbar.
pub fn ownership_weight() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_OWNERSHIP_W", 0.0))
}

/// `MOSAIC_OWNERSHIP_GEW` -- Gewicht JE KRITERIUM `gew_k` innerhalb des
/// Ownership-Pols. Acht Werte in Kriterien-Reihenfolge 0..7, ein einzelner
/// gilt fuer alle; falsche Laenge wird VERWORFEN (mit Meldung), nicht
/// teilgelesen. Format und Haerte exakt wie `MOSAIC_WERTUNG_SHAPING_W`/
/// `MOSAIC_TILING_PLATTEN_GEW`.
///
/// Default **alle 1,0**, NICHT 0,0: `w_own` ist der Hauptschalter (§2), die
/// Kriteriengewichte sind der Isolier-Knopf darueber ("nur die Vertikale" =
/// `0,1,0,0,0,0,0,0`). Waere der Default 0, waere `w_own` allein wirkungslos
/// -- genau die still-wirkungslose Kombination, die bei
/// `MOSAIC_WERTUNG_SHAPING_W` schon einmal eine Messung entwertet hat.
///
/// Stelle 7 ist per Konstruktion wirkungslos: `expected_plate_points` liefert
/// fuer Kriterium 7 immer 0 (Farbinformation steckt nicht im Ownership-Ziel,
/// `neural_net.py:958`).
pub fn ownership_weights() -> [f64; 8] {
    static CELL: std::sync::OnceLock<[f64; 8]> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| {
        let mut out = [1.0f64; 8];
        let Ok(raw) = std::env::var("MOSAIC_OWNERSHIP_GEW") else { return out };
        let parts: Vec<&str> = raw.split(',').map(|p| p.trim()).filter(|p| !p.is_empty()).collect();
        let vals: Option<Vec<f64>> = parts.iter().map(|p| p.parse::<f64>().ok()).collect();
        match vals.as_deref() {
            Some([one]) => out = [*one; 8],
            Some(v) if v.len() == 8 => out.copy_from_slice(v),
            _ => eprintln!(
                "MOSAIC_OWNERSHIP_GEW={raw:?} ignoriert -- erwartet 1 oder 8 Zahlen, Default 1,0 je Kriterium gilt"
            ),
        }
        out
    })
}

/// Baustein 2 (`MOSAIC_OWNERSHIP_SCALE`, `PREREG_reachability_target.md`
/// par.6 / `PREREG_shaping_scale_per_round.md` par.3a): Nenner JE KRITERIUM
/// fuer den Ownership-Pol, ersetzt die feste `WERTUNG_SHAPING_SCALE` (50.0)
/// im `tanh(E_k / scale_k)`-Term. Format und Haerte exakt wie
/// `scoring_shaping_alphas`/`ownership_weights`: 1 oder 8 kommagetrennte
/// Zahlen, falsche Laenge wird VERWORFEN (mit Meldung), nicht teilgelesen.
///
/// Default alle `WERTUNG_SHAPING_SCALE` (50.0) = byte-identisches
/// Bestandsverhalten. Anlass (par.6, gemessen): `tanh(0,082/50)` = 0,0016
/// gegen eine q-Eigenspreizung der Suche von 0,078 -- Faktor ~50 zu leise.
/// Gemessene Nenner fuer Arm S: k0 ~17, k1 ~1, k2 ~0,3 statt einheitlich 50.
pub fn ownership_scale() -> [f64; 8] {
    static CELL: std::sync::OnceLock<[f64; 8]> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| {
        let mut out = [WERTUNG_SHAPING_SCALE; 8];
        let Ok(raw) = std::env::var("MOSAIC_OWNERSHIP_SCALE") else { return out };
        let parts: Vec<&str> = raw.split(',').map(|p| p.trim()).filter(|p| !p.is_empty()).collect();
        let vals: Option<Vec<f64>> = parts.iter().map(|p| p.parse::<f64>().ok()).collect();
        match vals.as_deref() {
            Some([one]) => out = [*one; 8],
            Some(v) if v.len() == 8 => out.copy_from_slice(v),
            _ => eprintln!(
                "MOSAIC_OWNERSHIP_SCALE={raw:?} ignoriert -- erwartet 1 oder 8 Zahlen, Default {WERTUNG_SHAPING_SCALE} je Kriterium gilt"
            ),
        }
        out
    })
}

/// Einmalige Warnung, wenn `w_own > 0` gesetzt ist, das geladene Netz aber
/// keinen brauchbaren Ownership-Kopf liefert -- Stufe 2 des
/// `blended_leaf_win_prob`-Musters (net_mcts.rs, `warn_missing_opp_head_once`):
/// laut scheitern statt still nichts tun. Der Verbraucher verhaelt sich danach
/// wie `w_own = 0`.
fn warn_ownership_head_unusable_once(len: usize) {
    static WARNED: std::sync::OnceLock<()> = std::sync::OnceLock::new();
    WARNED.get_or_init(|| {
        eprintln!(
            "⚠️  MOSAIC_OWNERSHIP_W ist gesetzt, aber der Ownership-Kopf des geladenen Netzes ist \
             unbrauchbar (Laenge {len}, gebraucht werden mindestens {min} Werte = 2 x 36 Felder). \
             Der Ownership-Pol verhaelt sich wie w_own=0. Diese Meldung erscheint nur einmal je Prozess.",
            min = 2 * crate::scoring::OWNERSHIP_FIELDS
        );
    });
}

/// Sigmoid -- der Ownership-Kopf endet auf `nn.Linear` OHNE Aktivierung
/// (`neural_net.py:2390-2394`) und wird mit
/// `binary_cross_entropy_with_logits` trainiert (`train.py:1171-1172`), die
/// Kopf-Ausgaben sind also LOGITS. Die Umrechnung gehoert hierher, nicht in
/// `net.rs` (das reicht Koepfe roh durch).
///
/// `pub(crate)` seit Teil 2 (Tiling): `self_play.rs::ownership_tiling_marginals`
/// dekodiert dieselben Logits fuer die Wurzelkarte des Tiling-Zuges. Eine
/// zweite lokale Kopie waere hier die schlechtere Wahl -- beide Pole muessen
/// dieselbe Umrechnung benutzen, sonst haben sie verschiedene Karten.
pub(crate) fn sigmoid(x: f64) -> f64 {
    1.0 / (1.0 + (-x).exp())
}

/// Reine Formel hinter [`apply_ownership_shaping`], OHNE Env-Var-Zugriff --
/// gleiches Trennungsmuster wie `apply_scoring_shaping_full`/
/// `blended_leaf_win_prob_with` (die OnceLock-Getter sind pro Prozess nur
/// einmal lesbar, ein env-basierter Test kaeme nie an sein Ziel).
///
/// ```text
/// shift_i = w_own * SUM_k gew_k * tanh(E_k(i) / 50)
/// out_i   = clamp(value_i + shift_i, 0, 1)
/// ```
///
/// -- dieselbe Form, dieselbe Skala (`WERTUNG_SHAPING_SCALE`) und dasselbe
/// "Gewicht AUSSEN am tanh" wie der Heuristik-Pol (siehe dortige Begruendung:
/// `tanh(w*P/50)` saettigt gegen 1 unabhaengig von w, `w*tanh(P/50)` gegen w).
///
/// PERSPEKTIVE: `ownership` ist die Karte des MOVER-Passes, ego-perspektivisch
/// -- `[0:36]` gehoert `state.current_player`, `[36:72]` dem anderen Spieler
/// (`neural_net.py:1825-1840`, "erst der Spieler am Zug, dann der Gegner").
/// Jeder Spieler bekommt seinen eigenen, unabhaengigen Shift aus seiner
/// eigenen Haelfte -- keine mine-minus-theirs-Kopplung, exakt wie der
/// Heuristik-Pol.
///
/// DREI STUFEN, Muster von `blended_leaf_win_prob_with`:
///   1. `w_own == 0.0` (Default) -> `value` UNVERAENDERT zurueck. Kein
///      Sigmoid, kein tanh, keine Rundung -> byte-identisch.
///   2. `w_own > 0`, aber der Kopf ist unbrauchbar (fehlt ganz oder ist
///      schmaler als 72) -> einmalige Warnung, dann wie Stufe 1. Deckt den
///      72er- UND den 140er-Kopf ab: gebraucht werden nur die ersten 72
///      Werte, alles dahinter (Konjunktionen) wird hier nicht gelesen.
///   3. `w_own > 0` und Kopf brauchbar -> Shift wie oben.
///
/// WARUM DER 140er-KOPF NICHT DIREKT GELESEN WIRD (bewusste Wahl, siehe
/// Bericht): `expected_plate_points` rechnet das PRODUKT der Feld-Randwahr-
/// scheinlichkeiten, obwohl der Konjunktionsteil des 140er-Kopfs
/// (`neural_net.py::_conjunctions_from_dome`, Index `[72:106]` ich /
/// `[106:140]` Gegner) genau diese Konjunktionen direkt schaetzt und laut
/// dortigem Docstring GENAUER ist ("P(alle 6 Felder) ist nicht das Produkt
/// der Einzelwahrscheinlichkeiten"). Drei Gruende fuer die Produktform:
///   - §2 des Vertrags schreibt sie woertlich vor;
///   - sie ist kopfbreiten-agnostisch, der amtierende Champion
///     (`v21_2d_brierbest`, 72 breit) und die Sweep-Checkpoints (140 breit)
///     nehmen denselben Codepfad -- kein zweiter, nur halb getesteter Zweig;
///   - der Tiling-Verbraucher (§3) braucht ohnehin marginale Feldwerte
///     (`punkte_k * PROD ueber die UEBRIGEN Felder`), die aus einer
///     Konjunktions-Ausgabe gar nicht ableitbar waeren.
/// Die Konjunktions-Ausgaenge sind damit heute UNGENUTZT -- ein moeglicher
/// zweiter Regler-Arm, kein Teil dieses Auftrags.
fn apply_ownership_shaping_full(
    value: [f64; 2],
    state: &GameState,
    ownership: &[f32],
    w_own: f64,
    gew: &[f64; 8],
    use_conj: bool,
    scale: &[f64; 8],
) -> [f64; 2] {
    if w_own == 0.0 {
        return value;
    }
    let need = 2 * crate::scoring::OWNERSHIP_FIELDS;
    if ownership.len() < need {
        warn_ownership_head_unusable_once(ownership.len());
        return value;
    }
    let mut out = value;
    for i in 0..2 {
        // Ego-Haelfte des ZIEHENDEN Spielers ist `[0:36]`, die des anderen
        // `[36:72]` -- siehe Funktionskommentar "PERSPEKTIVE".
        let base = if i == state.current_player { 0 } else { crate::scoring::OWNERSHIP_FIELDS };
        let mut p_own = [0.0f64; crate::scoring::OWNERSHIP_FIELDS];
        for (f, slot) in p_own.iter_mut().enumerate() {
            *slot = sigmoid(ownership[base + f] as f64);
        }
        // FORMUMSCHALTUNG (PREREG_conjunction_terms.md par.4): die konjunktiven
        // Kriterien aus den GELERNTEN Atomen statt aus dem Produkt der
        // Feldwahrscheinlichkeiten. Braucht den 140er-Kopf; bei schmalerem Kopf
        // Rueckfall auf die Produktform MIT Warnung -- still zurueckfallen wuerde
        // heissen, dass ein Knopf beim einen Checkpoint wirkt und beim anderen
        // nicht, und das waere in der Arena von einem Dosiseffekt nicht zu
        // unterscheiden (par.4.3).
        let conj_breite = 2 * (crate::scoring::OWNERSHIP_FIELDS
                               + crate::scoring::CONJUNCTION_ATOMS);
        let e = if use_conj && ownership.len() >= conj_breite {
            let cbase = 2 * crate::scoring::OWNERSHIP_FIELDS
                + if i == state.current_player { 0 } else { crate::scoring::CONJUNCTION_ATOMS };
            let mut p_conj = [0.0f64; crate::scoring::CONJUNCTION_ATOMS];
            for (a, slot) in p_conj.iter_mut().enumerate() {
                *slot = sigmoid(ownership[cbase + a] as f64);
            }
            crate::scoring::expected_plate_points_conj(
                &state.players[i], &p_own, &p_conj, &state.scoring_tile_ids,
            )
        } else {
            if use_conj {
                warn_ownership_conj_unavailable_once(ownership.len());
            }
            crate::scoring::expected_plate_points(
                &state.players[i], &p_own, &state.scoring_tile_ids,
            )
        };
        let mut shift = 0.0;
        for k in 0..8 {
            if gew[k] == 0.0 {
                continue;
            }
            shift += gew[k] * (e[k] / scale[k]).tanh();
        }
        out[i] = (value[i] + w_own * shift).clamp(0.0, 1.0);
    }
    out
}

/// Laufzeit-Wrapper von [`apply_ownership_shaping_full`], liest `w_own`/`gew`/
/// `scale` aus den prozessweiten OnceLock-Caches. Aufrufstellen: `net_leaf_eval`
/// und `node_from_net_outputs`s `LeafEval::Net`-Zweig -- dieselben zwei Stellen
/// wie [`apply_scoring_shaping`], jeweils DIREKT dahinter.
fn apply_ownership_shaping(value: [f64; 2], state: &GameState, ownership: &[f32]) -> [f64; 2] {
    apply_ownership_shaping_full(value, state, ownership, ownership_weight(),
                                 &ownership_weights(), ownership_conj(), &ownership_scale())
}

/// `MOSAIC_OWNERSHIP_CONJ` -- Formumschaltung des Ownership-Verbrauchers.
/// Default **0** = Produktform, byte-identisches Bestandsverhalten. 1 = die
/// konjunktiven Kriterien kommen aus den gelernten Atomen
/// (`scoring::expected_plate_points_conj`).
///
/// Das ist KEINE Dosis, sondern ein Schalter: die Staerke regelt weiterhin
/// `MOSAIC_OWNERSHIP_W`. Getrennt gehalten, damit Form und Dosis in der Arena
/// einzeln messbar bleiben (PREREG_conjunction_terms.md par.6).
pub(crate) fn ownership_conj() -> bool {
    static CELL: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| {
        std::env::var("MOSAIC_OWNERSHIP_CONJ")
            .ok()
            .and_then(|s| s.trim().parse::<f64>().ok())
            .map(|v| v != 0.0)
            .unwrap_or(false)
    })
}

/// Einmalige Warnung, wenn `MOSAIC_OWNERSHIP_CONJ` gesetzt ist, der Kopf aber
/// keinen Konjunktionsteil hat (72 statt 140 breit -- etwa der amtierende
/// Champion). Absichtlich laut: siehe Begruendung an der Aufrufstelle.
fn warn_ownership_conj_unavailable_once(len: usize) {
    static EINMAL: std::sync::Once = std::sync::Once::new();
    EINMAL.call_once(|| {
        eprintln!("[mosaic] WARNUNG: MOSAIC_OWNERSHIP_CONJ ist gesetzt, aber der Ownership-Kopf ist nur {len} breit (noetig: {}). Rueckfall auf die Produktform -- die Formumschaltung ist fuer diesen Checkpoint WIRKUNGSLOS.",
                  2 * (crate::scoring::OWNERSHIP_FIELDS + crate::scoring::CONJUNCTION_ATOMS));
    });
}

// ── Freischalt-Shaping (Nutzer-Auftrag 2026-08-10, Messlage watchlist_v20_
// zwischenlese.md Abschnitt 2) ──────────────────────────────────────────────
// Eigener Knopf, eigene Formel (`unlock_progress_beta`, scoring.rs) --
// UNGEGATET (zahlt unabhaengig von `scoring_tile_ids`, siehe dortiger
// Kommentar), ABSOLUT statt marginal (bewusst KEIN Eltern-Delta wie
// `plate_shaping_marginal` -- eine Differenzform waere potentialbasiert und
// liesse die Zugwahl strukturell unberuehrt, das ist hier explizit NICHT
// gewollt: der Term soll echte Praeferenz fuer Freischalt-Fortschritt in die
// Suche tragen, nicht nur eine neutrale Reparametrisierung sein). Je Spieler
// ABSOLUT wie das Wertungsplatten-Shaping oben (siehe dortiger Kommentar,
// Nutzer-Korrektur 2026-08-11) -- BEIDE Spieler unabhaengig ueber ihr
// EIGENES Brett, kein Cross-Term, keine mine-minus-theirs-Differenz. Gleiche
// Skala (`tanh(x/50.0)`).

/// Default-Gewicht des Freischalt-Shaping-Additivs -- `0.0` = AUS, exakt
/// Bestandsverhalten ohne gesetzte `MOSAIC_UNLOCK_SHAPING_W`.
pub const UNLOCK_SHAPING_WEIGHT: f64 = 0.0;

/// Default-Exponent `beta` fuer `unlock_progress_beta` -- `2.0` (Startwert,
/// analog `WERTUNG_SHAPING_ALPHA`, keine eigene Kalibrierung ueber diesen
/// Default hinaus).
pub const UNLOCK_SHAPING_BETA: f64 = 2.0;

// ── Perspektiven-/OOD-Audit (externer Hinweis, 2026-07-20) ──────────────────
//
// Der Perspektiven-Mirror-Fix (`MIRROR_OTHER_VAL`) wurde arena-getestet und
// hat die Suchstärke NICHT verbessert (siehe dortiger Kommentar) -- die
// Hypothese "zweiter Forward-Pass ist der dominante Schadensfaktor" ist damit
// als ALLEINIGE Erklärung widerlegt. Der zugrunde liegende Verdacht (mover_val
// + other_val nicht nullsummen-konsistent, da `other_val` einen im Training
// nie gesehenen Zustand auswertet) bleibt aber eine berechtigte, noch nicht
// endgültig ausgeschlossene Teilursache -- daher NICHT die Suche selbst
// ändern (das Ergebnis war negativ), sondern permanent als Audit/Sanity-Check
// mitloggen: `|v_mover + v_other - 1|` pro Runde, unconditional (kein
// Feature-Flag, immer aktiv, im Gegensatz zu `profiling.rs`s
// `clone_profiling`-gated Tooling) -- Nutzer-Auftrag, im Self-Play als
// zusätzliche Ausgabewerte sichtbar bleiben. Gleiches Muster wie
// `self_play.rs`s `STAGE3_DECISIONS`-Zähler (Mutex statt Atomics, da hier
// auch Summen/Mittelwerte gebraucht werden, nicht nur Zählungen).
static PERSPECTIVE_DIVERGENCE_STATS: std::sync::OnceLock<std::sync::Mutex<[(u64, f64); 6]>> =
    std::sync::OnceLock::new();

fn perspective_divergence_stats() -> &'static std::sync::Mutex<[(u64, f64); 6]> {
    PERSPECTIVE_DIVERGENCE_STATS.get_or_init(|| std::sync::Mutex::new([(0u64, 0.0f64); 6]))
}

/// `mover_val`/`other_val` sind VOR der Floor-Shaping-Korrektur genau die
/// beiden unabhängigen Netz-Forward-Pass-Ergebnisse -- exakt die Größen, die
/// laut Hinweis nicht nullsummen-konsistent sein könnten. `round` wird auf
/// 1..=5 gekappt (Index 0 bleibt ungenutzt).
fn record_perspective_divergence(round: u32, mover_val: f64, other_val: f64) {
    let idx = (round as usize).clamp(1, 5);
    let div = (mover_val + other_val - 1.0).abs();
    let mut g = perspective_divergence_stats().lock().unwrap();
    g[idx].0 += 1;
    g[idx].1 += div;
}

pub(crate) fn perspective_divergence_reset() {
    let mut g = perspective_divergence_stats().lock().unwrap();
    *g = [(0u64, 0.0f64); 6];
}

/// JSON `{"round_1": {"n": .., "mean_abs_divergence": ..}, ...}` -- ans
/// Self-Play-Ergebnis angehängt, analog `self_play.rs`s
/// `stage3_diagnostics`-Objekt.
pub(crate) fn perspective_divergence_snapshot() -> Value {
    let g = perspective_divergence_stats().lock().unwrap();
    let mut out = serde_json::Map::new();
    for round in 1..=5usize {
        let (n, sum) = g[round];
        let mean = if n > 0 { sum / n as f64 } else { 0.0 };
        out.insert(format!("round_{round}"), json!({ "n": n, "mean_abs_divergence": mean }));
    }
    Value::Object(out)
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
    /// DFS-Solver-Blattwert am Knotenzustand (je Spieler) — Backprop-Blattwert.
    leaf_value: [f64; 2],
    /// Gesamtzahl legaler Züge VOR Moon-Order-Expansion (= Basis-Aktionen) —
    /// für die "Gültige Aktionen"-Anzeige (Server-Debug-UI), unabhängig davon,
    /// wie viele davon durchs Widening tatsächlich zu Kindern wurden.
    n_actions: usize,
    /// PREREG_denial_tiebreak.md (Task E3): roher `points_head`-Output dieses
    /// Knotens (ego-perspektivisch bzgl. `state.current_player`), `None` bei
    /// jedem Netz ohne Punkte-Kopf. War bislang ein reiner Zwischenwert in
    /// `node_from_net_outputs` (nur für `blended_leaf_win_prob` gebraucht,
    /// danach verworfen) -- hier zusätzlich GESPEICHERT, weil der Denial-
    /// Tie-Break denselben, ohnehin schon berechneten Wert für die Wurzel-
    /// kinder braucht (KEIN zusätzlicher Netz-Forward-Pass, siehe
    /// `apply_denial_tiebreak`-Kommentar für die Kostenrechnung).
    points_forecast: Option<f32>,
    /// Wie [`Node::points_forecast`], aber der optionale `opp_points_head`-
    /// Output (Task #28, `net.rs::has_opp_head`) -- ebenfalls ego-
    /// perspektivisch bzgl. `state.current_player` (Gegner-Punkte AUS SICHT
    /// des an DIESEM Knoten ziehenden Spielers, nicht zwingend der Wurzel-
    /// Gegner, siehe `opp_points_forecast_from_root_perspective`).
    opp_points_forecast: Option<f32>,
    /// PREREG_points_head_plates.md (Stufe 2): roher `value_head`-Tanh-
    /// Output dieses Knotens (ego-perspektivisch bzgl. `state.current_player`,
    /// VOR jeder Blend-/Shrink-/Floor-/Plate-Shaping-Korrektur) -- exakt
    /// derselbe Rohwert, der in `node_from_net_outputs` ohnehin für
    /// `blended_leaf_win_prob` berechnet wird, hier zusätzlich GESPEICHERT
    /// statt verworfen (kein zusätzlicher Netz-Forward-Pass), analog zu
    /// [`Node::points_forecast`]/[`Node::opp_points_forecast`] oben. `None`
    /// nur, wenn der Netz-Aufruf selbst keinen Value zurückgab (Fallback-Pfad
    /// bei Eval-Fehler).
    raw_value: Option<f32>,
    /// PREREG_implicit_minimax_backup.md par.1 (Baier/Winands Implicit
    /// Minimax Backups): implizit-minimax-propagierter Wert JE SPIELER
    /// (gleiche Indizierung wie `leaf_value`, NICHT dieselbe Perspektiv-
    /// Konvention wie `value`/`visits` -- siehe `update_im_value_backup`-
    /// Doku). Bei Knotenerzeugung = `leaf_value` (Blatt/Neuexpansion-Fall,
    /// "v_IM = Netz-Value des Knotens"), danach bei jedem Backprop per
    /// Minimax ueber die besuchten Kinder aktualisiert -- IMMER mitgefuehrt,
    /// unabhaengig vom `MOSAIC_IMPLICIT_MINIMAX_A`-Knopf (reine Arithmetik,
    /// kein Netz-/RNG-Zugriff). Erst die Selektion (`gumbel_select_child`)
    /// entscheidet per `alpha`, ob dieser Wert das Ergebnis ueberhaupt
    /// beeinflusst.
    im_value: [f64; 2],
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
    skip_cutoff: bool,
) -> (Vec<(Action, f32)>, usize) {
    let base_actions = drafting_actions(state);
    let n = base_actions.len();
    // Direkter Action→ID-Match statt JSON-Umweg (Performance, externer
    // Hinweis Abschnitt D, 2026-07-20) -- heißester Aufruf in
    // `build_untried_actions` (pro legaler Aktion pro Knoten), siehe
    // `self_play::action_to_id_direct`-Kommentar für die Parität-Absicherung.
    let ids: Vec<usize> = base_actions.iter().map(|a| crate::self_play::action_to_id_direct(state, a)).collect();

    // WICHTIG: Maskierte Softmax NUR über die EINDEUTIGEN legalen Aktions-IDs —
    // exakt wie das Training (masked log_softmax). Mehrere Moon-Order-Varianten
    // derselben Basis-Aktion teilen sich eine ID; würden sie hier dupliziert
    // eingehen, bekäme diese ID fälschlich mehrfaches Gewicht. Seit Baustein B
    // (zweistufiger Kuppel-Suchknoten) ist das die EINZIGE verbleibende
    // ID-Kollabierung -- Kuppel-Slot/Rotation haben jetzt eigene, nicht
    // kollabierte IDs (siehe features.rs::action_to_id), brauchen also keine
    // separate Prior-Faktorisierung mehr.
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
    //
    // `skip_cutoff` (externer Bugfix-Hinweis, Fund 4, 2026-07-20): an der
    // WURZEL ausgesetzt (siehe `make_node`s `parent.is_none()`-Aufruf) --
    // Dirichlet-Root-Noise (`build_net_tree`) wird sonst erst NACH diesem
    // Cutoff auf den bereits verkleinerten Präfix gemischt, wodurch Aktionen
    // jenseits der 95%-Masse im Self-Play NIE exploriert werden können (kein
    // AlphaZero-Standardverhalten: Root-Noise soll JEDER legalen Aktion eine
    // Explorations-Chance geben). Nur an der Wurzel relevant -- der
    // Progressive-Widening-Cap (`MAX_ACTIONS + WIDEN_FACTOR·√N`, siehe
    // `build_net_tree`) verhindert weiterhin, dass der Long Tail tatsächlich
    // durchgehend expandiert wird, auch ohne den harten Cutoff hier.
    if skip_cutoff {
        return (acts, n);
    }
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

/// KataGo-Stil geblendete Blattbewertung: mischt `value_head`s Sieg-Wahr-
/// scheinlichkeit mit `points_head`s Punktestand-Prognose. `points` nutzt
/// dieselbe Tanh→[0,1]-Skalierung wie `value` (andere Zielformel, gleiche
/// Skala) — bei fehlendem `points`-Kopf (z.B. ältere ONNX-Checkpoints ohne
/// den Kopf) fällt dies auf reines `value` zurück, kein Panik/Skip nötig.
///
/// Task #28 (`evaluations/PREREG_task28_aggression.md`, "Minimal-invasiver
/// Zuschnitt" Punkt 4): `opp_points` ist der optionale Gegner-Punkte-Kopf
/// (leer bei jedem Netz ohne `opp_points`-ONNX-Output, siehe
/// `net.rs::eval_ex`/`has_opp_head`). Ablauf, drei Stufen:
///   1. `w = points_utility_w() == 0.0` (Default) -> Early-Out, exakt
///      dieselbe Formel wie VOR diesem Task (`POINTS_UTILITY_WEIGHT` bleibt
///      dabei unangetastet als eigener, stehen gelassener toter Pfad -- der
///      aktuell IMMER 0 beitraegt, `legacy_blended` ist also numerisch
///      identisch zu `wr`). Byte-identisches Bestandsverhalten, KEIN
///      zusaetzlicher Rechenpfad.
///   2. `w>0`, aber `opp_points` leer (Legacy-Modell ohne den Kopf) ->
///      verhaelt sich wie `w=0` (einmalige Warnung statt stillem Ignorieren).
///   3. `w>0` UND `opp_points` vorhanden -> `opp_aware_points_utility`
///      (own-minus-lambda_aggr*opp-Blend, siehe dortige Doku für die
///      Skalenkonvention).
///
/// Task #30: `value_to_win_prob(value)` (die reine Netz-Win-Prob `wr`) läuft
/// zusätzlich durch [`calibrate_win_prob`] -- VOR jeder weiteren Verwendung
/// inkl. dieses Blends, siehe dortige Doku. Der Punkte-Term (`pts`/
/// `opp_aware_points_utility`) bleibt bewusst UNKORRIGIERT (andere Skala/
/// Kopf, eigene Kalibrierung wäre ein separates Experiment).
fn blended_leaf_win_prob(value: &[f32], points: &[f32], opp_points: &[f32]) -> f64 {
    blended_leaf_win_prob_with(
        value, points, opp_points, points_utility_w(), aggr_lambda(), value_cal_a(), value_cal_b(),
    )
}

/// Reiner Entscheidungskern von [`blended_leaf_win_prob`], OHNE Env-Var-
/// Zugriff -- nimmt `w`/`lambda_aggr`/`cal_a`/`cal_b` als Parameter statt sie
/// aus dem Prozess-weiten `OnceLock`-Cache (`points_utility_w()`/
/// `aggr_lambda()`/`value_cal_a()`/`value_cal_b()`) zu lesen. Getrennt, damit
/// die VOLLSTAENDIGE Blend-Entscheidungslogik (Early-Out bei `w=0`,
/// Legacy-Fallback bei fehlendem opp-Kopf, echter Blend, Task-#30-Kalibrierung)
/// OHNE die "einmal pro Prozess gecacht"-Falle direkt testbar ist -- diese
/// Getter sind ABSICHTLICH nur einmal pro Prozess lesbar (siehe deren Doku),
/// ein Test, der den Cache nach dem ersten Aufruf per Env-Var umstellen will,
/// kaeme nie an sein Ziel. Gleiches Trennungsmuster wie `net.rs`s
/// `detect_layout`/`combine_layouts`.
fn blended_leaf_win_prob_with(
    value: &[f32],
    points: &[f32],
    opp_points: &[f32],
    w: f64,
    lambda_aggr: f64,
    cal_a: f64,
    cal_b: f64,
) -> f64 {
    // Task #30: Skalen-Korrektur auf `wr`, VOR jeder weiteren Verwendung --
    // `points`/`opp_points` bleiben unkorrigiert (siehe Funktionskommentar).
    let wr = calibrate_win_prob_with(value_to_win_prob(value), cal_a, cal_b);
    if points.is_empty() {
        return wr;
    }
    let pts = value_to_win_prob(points);
    // Alter (toter) KataGo-Blend -- `POINTS_UTILITY_WEIGHT` ist konstant 0.0
    // (siehe dortiger GETESTET-Kommentar), dieser Ausdruck ist also aktuell
    // IMMER numerisch `wr`. Bewusst weiter berechnet (nicht durch `wr`
    // ersetzt), damit die Konstante an dieser Stelle sichtbar referenziert
    // bleibt, falls sie je rekalibriert wird.
    let legacy_blended = (1.0 - POINTS_UTILITY_WEIGHT) * wr + POINTS_UTILITY_WEIGHT * pts;

    if w == 0.0 {
        return legacy_blended;
    }
    if opp_points.is_empty() {
        warn_missing_opp_head_once();
        return legacy_blended;
    }
    let pts_raw = points.first().copied().unwrap_or(0.0) as f64;
    let opp_raw = opp_points.first().copied().unwrap_or(0.0) as f64;
    let u_pts = opp_aware_points_utility(pts_raw, opp_raw, lambda_aggr);
    (1.0 - w) * wr + w * u_pts
}

/// Verschraenkung (Weg V, `net_batcher.rs`): versucht `feats`s EINZELNE Zeile
/// ueber den fuer `net` registrierten Sammel-Faden auszuwerten (4-Tupel,
/// gleicher Vertrag wie `Net::eval`) statt ueber `Net::eval` direkt. `None`
/// faellt auf den bestehenden synchronen Pfad zurueck (kein registrierter
/// Sammel-Faden fuer dieses Netz -- Knopf aus ODER `ensure_batcher_for` nie
/// aufgerufen -- oder ein Fehler im Rundlauf). Braucht keinen
/// `points_utility_w()`-Wächter wie [`try_batched_pair_ex`] unten: `Net::eval`
/// kennt `opp_points` von vornherein nicht, der Vertrag ist also IMMER
/// deckungsgleich mit dem, was der Sammel-Faden liefert.
fn try_batched_single_eval(
    net: &Net,
    feats: &[f32],
) -> Option<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)> {
    let batcher = crate::net_batcher::lookup(net)?;
    let mut rows = batcher.eval_rows(&[feats]).ok()?;
    // Der Sammel-Faden liefert seit dem Ownership-Verbraucher Teil 1 sechs
    // Spalten; dieser Aufrufer (`drafting_action_priors`) braucht nur den
    // `Net::eval`-4-Tupel-Vertrag und verwirft die beiden Aux-Koepfe --
    // dort gibt es keinen Blattwert, in den ein Shift eingehen koennte.
    let (policy, value, moon, points, _opp, _own) = rows.remove(0);
    Some((policy, value, moon, points))
}

/// Verschraenkung (Weg V, `net_batcher.rs`): versucht `feats_a`/`feats_b`
/// (Mover-/geflippte Perspektive) ueber den fuer `net` registrierten
/// Sammel-Faden auszuwerten (zwei Zeilen desselben logischen Aufrufs, siehe
/// `Batcher::eval_rows`) statt ueber `Net::eval_pair_ex` direkt -- NUR
/// sicher, wenn der `opp_points`-Kopf ohnehin unbeobachtet bleibt
/// (`points_utility_w()==0.0`, Task #28 Default), weil der Sammel-Faden
/// intern `Net::eval_batch` aufruft (4-Tupel, KEIN `opp_points`). Liefert in
/// diesem Fall `opp_points`/`o_opp_points` als LEERE Vecs zurueck -- exakt
/// die etablierte "kein Kopf"-Konvention (`eval_ex`-Doku), mit der
/// `blended_leaf_win_prob` bei `w==0.0` ohnehin nie in Beruehrung kommt
/// (frueher Ausstieg VOR jedem `opp_points`-Zugriff, siehe dortiger Code).
/// `None` (Knopf aus, `w>0`, kein registrierter Sammel-Faden, oder ein
/// Fehler im Rundlauf) faellt auf den bestehenden synchronen Pfad zurueck --
/// der Aufrufer bleibt dadurch UNVERAENDERT lauffaehig, egal was hier passiert.
///
/// Ownership-Verbraucher Teil 1: der Sammel-Faden liefert seit der
/// Verdrahtung SECHS Spalten je Zeile, `ownership` kommt also auch ueber
/// diesen Pfad durch (frueher waere hier still ein leerer Kopf entstanden).
/// `opp_points` wird trotzdem weiterhin als LEER zurueckgegeben und der
/// `points_utility_w()`-Waechter bleibt unangetastet -- siehe
/// `net_batcher.rs`-Modulkommentar "Was NICHT Teil dieser Datei ist".
#[allow(clippy::type_complexity)]
fn try_batched_pair_ex(
    net: &Net,
    feats_a: &[f32],
    feats_b: &[f32],
) -> Option<(
    (Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>),
    (Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>),
)> {
    if points_utility_w() != 0.0 {
        return None;
    }
    let batcher = crate::net_batcher::lookup(net)?;
    let rows = batcher.eval_rows(&[feats_a, feats_b]).ok()?;
    let (pa, va, ma, pta, _oppa, owna) = rows[0].clone();
    let (pb, vb, mb, ptb, _oppb, ownb) = rows[1].clone();
    Some(((pa, va, ma, pta, Vec::new(), owna), (pb, vb, mb, ptb, Vec::new(), ownb)))
}

/// Netz-Blattwert für `state`: unabhängige Pro-Spieler-Werte. Das Netz liefert
/// einen EGO-perspektivischen Wert (die Input-Features hängen von
/// `state.current_player` ab, siehe features.rs/state_to_tensor) — für den
/// jeweils ANDEREN Spieler braucht es deshalb einen zweiten Forward-Pass mit
/// geflipptem `current_player`, nicht einfach `1-wert`. Extrahiert aus
/// `make_node` (dort weiterhin für den `terminal==false`-Pfad genutzt,
/// unverändert), zusätzlich von `round_transition`-Aufrufstellen (Sampling
/// über Runden-Neubefüllungen, siehe `round_transition.rs`) wiederverwendet,
/// da beide denselben Netz-Blattwert brauchen.
pub(crate) fn net_leaf_eval(net: &Net, state: &GameState) -> [f64; 2] {
    let feats = crate::profiling::timed(crate::profiling::note_features_ns, || {
        crate::features::features_for_net(net, state)
    });
    // Paket 1 (Inferenz-Batching, 2026-07-22): bei `MIRROR_OTHER_VAL=false`
    // braucht dieser Aufruf ohnehin ZWEI Forward-Pässe (Mover-/geflippte
    // Perspektive) -- `Net::eval_pair` fasst sie zu einem Batch=2-Aufruf
    // zusammen statt zwei sequenzieller Batch=1-Aufrufe zu bezahlen (Parität
    // siehe `net.rs::eval_pair_matches_two_single_evals`). Bei `true` entfällt
    // der zweite Pass ohnehin (reines `eval`, unverändert).
    // Ownership-Verbraucher Teil 1: die Ownership-Karte des MOVER-Passes
    // deckt BEIDE Spieler ab (`[0:36]` ich, `[36:72]` Gegner, ego-
    // perspektivisch -- `neural_net.py:1825-1840`), der geflippte Pass wird
    // dafuer also nicht gebraucht.
    let (mover_val, other_val, own_map) = if MIRROR_OTHER_VAL {
        // Task #81: Batch=1 (ein einzelner Forward-Pass) -- fuer die Amdahl-
        // Aufteilung des geplanten GPU-Batchers (Task #82).
        // Task #28: `eval_ex` statt `eval` -- liest zusaetzlich den optionalen
        // `opp_points`-Kopf (leerer Vec bei jedem Netz ohne den Kopf, siehe
        // `net.rs::eval_ex`-Doku), sonst BYTE-IDENTISCH (gleiche Extraktion
        // der ersten vier Ausgaben).
        let (_logits, value, _moon, points, opp_points, ownership) =
            crate::profiling::timed_net_eval(1, || {
                net.eval_ex(&feats).unwrap_or_else(|_| {
                    (vec![0.0; NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new())
                })
            });
        let mv = blended_leaf_win_prob(&value, &points, &opp_points);
        (mv, 1.0 - mv, ownership)
    } else {
        crate::profiling::note_gamestate_clone();
        let mut flipped = state.clone();
        flipped.current_player = 1 - state.current_player;
        let other_feats = crate::features::features_for_net(net, &flipped);
        // Task #81: Batch=2 (`eval_pair` buendelt Mover+Gegner-Pass). Task #28:
        // `eval_pair_ex` (siehe Kommentar oben zu `eval_ex`). Weg V
        // (Verschraenkung, `net_batcher.rs`): `try_batched_pair_ex` versucht
        // ZUERST den registrierten Sammel-Faden -- `None` (Knopf aus ist der
        // Default) faellt byte-identisch auf den bisherigen synchronen
        // `eval_pair_ex`-Aufruf zurueck.
        let (
            (_logits, value, _moon, points, opp_points, ownership),
            (_o_logits, o_value, _o_moon, o_points, o_opp_points, _o_ownership),
        ) = match try_batched_pair_ex(net, &feats, &other_feats) {
            Some(pair) => pair,
            None => crate::profiling::timed_net_eval(2, || {
                net.eval_pair_ex(&feats, &other_feats).unwrap_or_else(|_| {
                    (
                        (vec![0.0; NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new()),
                        (Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new()),
                    )
                })
            }),
        };
        (
            blended_leaf_win_prob(&value, &points, &opp_points),
            blended_leaf_win_prob(&o_value, &o_points, &o_opp_points),
            ownership,
        )
    };
    if !MIRROR_OTHER_VAL {
        record_perspective_divergence(state.round_number, mover_val, other_val);
    }
    let raw = if state.current_player == 0 { [mover_val, other_val] } else { [other_val, mover_val] };
    // Task #78 (v12c Shrinkage) -- NACH blended_leaf_win_prob; `net_leaf_eval`
    // kennt weder die Floor- noch die Plattenshaping-Korrektur (die leben nur
    // in `make_node`), also gibt es hier dazu keine "vor/nach"-Reihenfolge zu
    // wahren. Das Wertungsplatten-EGO-Shaping (siehe dortiger Modul-Kommentar)
    // ist bewusst HIER zusaetzlich verdrahtet (nicht nur in `make_node`) --
    // es ist eine reine State-Funktion ohne Baum-/Elternknoten-Bezug, gilt
    // also unveraendert fuer jeden `net_leaf_eval`-Aufrufer (Chance-Node-
    // Sampling in `round_transition_deep.rs`/`self_play.rs` eingeschlossen),
    // NACH der Shrinkage (analog zur Floor-/Platten-Reihenfolge in
    // `make_node`: Shrinkage daempft nur den rohen Netzwert, die danach
    // angewendeten State-Korrekturen bleiben ungedaempft). Freischalt-Shaping
    // (siehe dortiger Modul-Kommentar) NACH dem Wertungsplatten-EGO-Shaping,
    // gleiche Begruendung.
    // `apply_unlock_shaping` NICHT mehr hier: der Spezialfeld-Anteil steckt seit
    // 2026-08-11 IM `apply_scoring_shaping`-Term (ein Gewicht fuer alle acht
    // Kriterien). Ein zweiter Aufruf wuerde ihn doppelt zaehlen.
    //
    // Ownership-Verbraucher Teil 1 (`PREREG_ownership_consumer.md` §2) NACH
    // dem Heuristik-Pol: derselbe Rechen-Ort, dieselbe Shift-Form, aber der
    // ANDERE Pol (Netz-Prognose statt Ist-Fortschritt). Bei
    // `MOSAIC_OWNERSHIP_W` ungesetzt (Default 0,0) exakte Identitaet --
    // `apply_ownership_shaping` steigt VOR jeder Rechnung aus.
    apply_ownership_shaping(
        apply_scoring_shaping(apply_value_shrink(raw, state.round_number), state),
        state,
        &own_map,
    )
}

/// Netz-Policy-Priors für `state`: EIN Forward-Pass, wiederverwendet
/// `build_untried_actions`s bestehende Prior-Sortierung/POLICY_MASS_CUTOFF-
/// Kappung/Moon-Order-Expansion unverändert (dieselbe Logik, die `make_node`
/// für die PUCT-Baumexpansion nutzt). Für `round_transition_deep.rs`s
/// Zwischenrunden-Zugwahl (`choose_drafting_action_pruned`) gedacht — dort
/// wird `priors` als generische Closure erwartet (kein `&Net` direkt), damit
/// Tests eine synthetische Closure ohne ONNX-Fixture übergeben können; dies
/// ist der dünne Produktions-Wrapper dafür. Liefert eine leere Liste bei
/// `terminal`-Zuständen (kein Policy-Kopf-Bedarf außerhalb Drafting).
pub(crate) fn drafting_action_priors(net: &Net, state: &GameState) -> Vec<(Action, f32)> {
    if state.phase != Phase::Drafting {
        return Vec::new();
    }
    let feats = crate::profiling::timed(crate::profiling::note_features_ns, || {
        crate::features::features_for_net(net, state)
    });
    // Task #81: Batch=1. Weg V (Verschraenkung, `net_batcher.rs`):
    // `try_batched_single_eval` versucht ZUERST den registrierten
    // Sammel-Faden -- `None` (Knopf aus ist der Default) faellt
    // byte-identisch auf den bisherigen synchronen `eval`-Aufruf zurueck.
    let (logits, _value, moon, _points) = match try_batched_single_eval(net, &feats) {
        Some(row) => row,
        None => crate::profiling::timed_net_eval(1, || {
            net.eval(&feats).unwrap_or_else(|_| {
                (vec![0.0; NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new())
            })
        }),
    };
    let mut moon_scores = [0f32; 5];
    for (i, s) in moon.iter().take(5).enumerate() {
        moon_scores[i] = *s;
    }
    build_untried_actions(state, &logits, &moon_scores, false).0
}

/// Erzeugt einen Knoten: Netz-Forward → Child-Priors (untried) + Blattwert
/// (per `ACTIVE_LEAF`: DFS-Solver oder Netz-Value).
///
/// Task #88 (Hybrid-Suche, kausaler Kopf-Test): `net_value` erlaubt ein
/// ZWEITES Netz für Blattwerte (Value+Points), waehrend `net_policy` weiter
/// die Priors (Policy-Logits) UND die Moon-Order (`moon`, policy-artig)
/// liefert -- siehe Modul-weite Erklaerung bei `net_search_drafting_action_
/// hybrid`. `net_value = None` (alle bisherigen Aufrufstellen) heisst
/// "gleiches Netz fuer beides" -- intern per `std::ptr::eq`-Kurzschluss
/// GENAU der alte Einzel-Netz-Codepfad (ein `eval`/`eval_pair`-Aufruf liefert
/// Policy UND Value zusammen), damit dieser Fall BYTE-IDENTISCH zum
/// Vor-Task-#88-Verhalten bleibt (Paritätstest siehe Testmodul unten:
/// `hybrid_search_with_equal_nets_matches_plain_search`). Nur wenn
/// `net_value` auf ein ANDERES Netz zeigt, greift der separate Hybrid-Pfad
/// (ein Batch=1-Policy-Pass + ein eigener Value-Pass/-Paar).
fn make_node<R: Rng + ?Sized>(
    net_policy: &Net,
    net_value: Option<&Net>,
    state: GameState,
    parent: Option<usize>,
    parent_state: Option<&GameState>,
    action: Option<Action>,
    prior: f32,
    player_who_acted: usize,
    rng: &mut R,
    search_config: &SearchConfig,
) -> Node {
    let terminal = state.phase != Phase::Drafting;
    // `points` fließt bei ACTIVE_LEAF=Net jetzt in `blended_leaf_win_prob` mit
    // ein (KataGo-Stil Score-Utility, siehe `POINTS_UTILITY_WEIGHT`-Kommentar).
    //
    // Paket 1 (Inferenz-Batching, 2026-07-22): bei ACTIVE_LEAF=Net UND
    // MIRROR_OTHER_VAL=false braucht dieser Knoten ohnehin einen zweiten
    // Forward-Pass für `other_val` (geflippte Perspektive, siehe weiter unten)
    // -- `Net::eval_pair` fasst Mover- und Gegner-Pass zu EINEM Batch=2-
    // ONNX-Aufruf zusammen statt zwei sequenzieller Batch=1-Aufrufe (Parität
    // siehe `net.rs::eval_pair_matches_two_single_evals`). Policy-Logits/
    // Moon-Scores werden nur aus dem Mover-Pass gebraucht -- die geflippte
    // Perspektive dient ausschließlich `other_val`, siehe `other_pass` unten.
    //
    // Task #11 Phase 2 (M3.5): Feature-Erzeugung läuft PRO NETZ
    // (`crate::features::features_for_net`), nicht mehr global VOR der
    // Verzweigung -- im Hybrid-Pfad (`same_net=false`) können `net_policy`
    // und `net_value` unterschiedliche Layouts haben (z.B. ein 2D- und ein
    // flaches Modell im selben Vergleich), ein einzelner geteilter
    // Feature-Puffer wäre für mindestens eines der beiden Netze falsch.
    let need_other_pass = ACTIVE_LEAF == LeafEval::Net && !MIRROR_OTHER_VAL;
    let same_net = net_value.is_none_or(|v| std::ptr::eq(v, net_policy));
    // Task #28: `_ex`-Varianten statt `eval`/`eval_pair` -- lesen zusaetzlich
    // den optionalen `opp_points`-Kopf (leer bei jedem Netz ohne den Kopf),
    // sonst BYTE-IDENTISCH (gleiche Extraktion von logits/value/moon/points).
    // Ownership-Verbraucher Teil 1: `ownership` kommt IMMER aus dem
    // Mover-Pass (deckt beide Spielerhaelften ab, siehe `net_leaf_eval`).
    let (logits, value, moon, points, opp_points, ownership, other_pass) = if same_net {
        // Unveraendert gegenueber vor Task #88 (Paritaets-Codepfad).
        let net = net_policy;
        let feats = crate::profiling::timed(crate::profiling::note_features_ns, || {
            crate::features::features_for_net(net, &state)
        });
        if need_other_pass {
            crate::profiling::note_gamestate_clone();
            let mut flipped = state.clone();
            flipped.current_player = 1 - state.current_player;
            let other_feats = crate::features::features_for_net(net, &flipped);
            // Task #81: Batch=2 (`eval_pair`). Weg V (Verschraenkung,
            // `net_batcher.rs`): `try_batched_pair_ex` versucht ZUERST den
            // registrierten Sammel-Faden -- `None` (Knopf aus ist der
            // Default) faellt byte-identisch auf den bisherigen synchronen
            // `eval_pair_ex`-Aufruf zurueck. Dies ist der DOMINANTE
            // Netz-Aufrufpfad (`same_net=true`, `need_other_pass=true` bei
            // `USE_GUMBEL_SEARCH=true`/`MIRROR_OTHER_VAL=false`, dem heutigen
            // Produktions-Stand) -- die eigentliche Ziel-Stelle der
            // Verschraenkung.
            let (
                (logits, value, moon, points, opp_points, ownership),
                (_o_logits, o_value, _o_moon, o_points, o_opp_points, _o_ownership),
            ) = match try_batched_pair_ex(net, &feats, &other_feats) {
                Some(pair) => pair,
                None => crate::profiling::timed_net_eval(2, || {
                    net.eval_pair_ex(&feats, &other_feats).unwrap_or_else(|_| {
                        (
                            (vec![0.0; NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new()),
                            (Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new()),
                        )
                    })
                }),
            };
            (logits, value, moon, points, opp_points, ownership, Some((o_value, o_points, o_opp_points)))
        } else {
            // Task #81: Batch=1.
            let (logits, value, moon, points, opp_points, ownership) =
                crate::profiling::timed_net_eval(1, || {
                    net.eval_ex(&feats).unwrap_or_else(|_| {
                        (vec![0.0; NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new())
                    })
                });
            (logits, value, moon, points, opp_points, ownership, None)
        }
    } else {
        // Task #88 Hybrid-Pfad: Policy/Moon von `net_policy` (EIN Batch=1-
        // Pass, kein Gegner-Pass noetig -- Priors sind rein EGO-
        // perspektivisch), Value/Points von `net_value` (Mover+Gegner-Pass
        // wie im Nicht-Hybrid-Fall, siehe `net_leaf_eval`-Kommentar).
        // Task #11 Phase 2 (M3.5): jeweils EIGENER, netz-spezifischer
        // Feature-Puffer -- `net_policy` und `net_value` koennen
        // unterschiedliche Layouts haben.
        let net_value = net_value.expect("same_net=false impliziert Some(..)");
        let feats_policy = crate::profiling::timed(crate::profiling::note_features_ns, || {
            crate::features::features_for_net(net_policy, &state)
        });
        let (logits, _p_value, moon, _p_points) = crate::profiling::timed_net_eval(1, || {
            net_policy
                .eval(&feats_policy)
                .unwrap_or_else(|_| (vec![0.0; NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new()))
        });
        if need_other_pass {
            crate::profiling::note_gamestate_clone();
            let mut flipped = state.clone();
            flipped.current_player = 1 - state.current_player;
            let feats_value = crate::features::features_for_net(net_value, &state);
            let other_feats_value = crate::features::features_for_net(net_value, &flipped);
            let (
                (_v_logits, value, _v_moon, points, opp_points, ownership),
                (_o_logits, o_value, _o_moon, o_points, o_opp_points, _o_ownership),
            ) = crate::profiling::timed_net_eval(2, || {
                net_value.eval_pair_ex(&feats_value, &other_feats_value).unwrap_or_else(|_| {
                    (
                        (Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new()),
                        (Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new()),
                    )
                })
            });
            (logits, value, moon, points, opp_points, ownership, Some((o_value, o_points, o_opp_points)))
        } else {
            let feats_value = crate::features::features_for_net(net_value, &state);
            let (_v_logits, value, _v_moon, points, opp_points, ownership) = crate::profiling::timed_net_eval(1, || {
                net_value.eval_ex(&feats_value).unwrap_or_else(|_| {
                    (Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new())
                })
            });
            (logits, value, moon, points, opp_points, ownership, None)
        }
    };

    node_from_net_outputs(
        net_policy, net_value, state, parent, parent_state, action, prior, player_who_acted, terminal,
        logits, value, moon, points, opp_points, ownership, other_pass, rng, search_config,
    )
}

/// Baut einen [`Node`] aus BEREITS BERECHNETEN Netz-Rohausgaben
/// (`logits`/`value`/`moon`/`points`/`other_pass`) -- reine Extraktion aus
/// `make_node` (Perf-Auftrag, 2026-08-02: Gumbel-Wurzel-Kandidaten-
/// Buendelung), KEINE Verhaltensaenderung: `make_node` ruft dies direkt im
/// Anschluss an seinen eigenen (unveraendert EINZELNEN) Netz-Eval-Block auf.
/// Der Sinn der Trennung: fuer eine GEBUENDELTE Wurzel-Kandidaten-Expansion
/// (`batched_expand_root_candidates` unten) werden die Netz-Rohausgaben
/// FUER ALLE KANDIDATEN GEMEINSAM per `Net::eval_batch` berechnet (EIN
/// ONNX-Aufruf statt `m_prime` einzelner) -- die eigentliche Knoten-
/// Konstruktion (Blattwert-Blending, Value-Shrink, Floor-/Plate-Shaping,
/// `build_untried_actions`, ...) bleibt dabei UNVERAENDERT dieselbe Funktion
/// wie im unbatchten Pfad, angewandt auf JEDEN Kandidaten einzeln -- kein
/// Doppelpflege-Risiko zwischen zwei Kopien derselben Logik.
#[allow(clippy::too_many_arguments)]
fn node_from_net_outputs<R: Rng + ?Sized>(
    net_policy: &Net,
    net_value: Option<&Net>,
    state: GameState,
    parent: Option<usize>,
    parent_state: Option<&GameState>,
    action: Option<Action>,
    prior: f32,
    player_who_acted: usize,
    terminal: bool,
    logits: Vec<f32>,
    value: Vec<f32>,
    moon: Vec<f32>,
    points: Vec<f32>,
    // Task #28: optionaler Gegner-Punkte-Kopf, leer bei jedem Netz ohne
    // `opp_points`-Output -- `other_pass`s 3. Tupel-Element ist das
    // Gegenstueck aus der geflippten Perspektive.
    opp_points: Vec<f32>,
    // Ownership-Verbraucher Teil 1: rohe Kopf-LOGITS des Mover-Passes
    // (`[0:36]` ich, `[36:72]` Gegner; 140 breit bei Konjunktions-Netzen,
    // der Verbraucher liest nur die ersten 72). Leer bei jedem Netz ohne den
    // Kopf. Bewusst KEIN Gegenstueck in `other_pass` -- die Karte deckt
    // beide Spielerhaelften schon ab.
    ownership: Vec<f32>,
    other_pass: Option<(Vec<f32>, Vec<f32>, Vec<f32>)>,
    rng: &mut R,
    search_config: &SearchConfig,
) -> Node {
    let mut moon_scores = [0f32; 5];
    for (i, s) in moon.iter().take(5).enumerate() {
        moon_scores[i] = *s;
    }
    // Cutoff ausgesetzt (siehe `build_untried_actions`-Kommentar zu
    // `skip_cutoff`, Fund 4) an der Wurzel (`parent.is_none()`, unabhängig
    // davon, ob Root-Noise gerade aktiv ist) -- UND (Paket 2, mctx-Treue
    // Tiefe-≥1-Auswahl, 2026-07-22) an JEDEM Knoten, wenn `USE_GUMBEL_SEARCH`
    // aktiv ist: die neue `gumbel_select_child`-Auswahlregel entscheidet
    // selbst über children ∪ untried, ohne einen vorab gekappten Long Tail zu
    // brauchen -- der PUCT-Legacy-Pfad (`USE_GUMBEL_SEARCH=false`) bleibt
    // unverändert nur an der Wurzel ausgesetzt (sein eigener Widening-Cap in
    // `build_net_tree` bremst dort weiterhin, wie bisher).
    let skip_cutoff = parent.is_none() || USE_GUMBEL_SEARCH;
    let (untried, n_actions) = if terminal {
        (Vec::new(), 0)
    } else {
        build_untried_actions(&state, &logits, &moon_scores, skip_cutoff)
    };

    // Blattwert: unabhängige Pro-Spieler-Werte. Das Netz liefert einen
    // EGO-perspektivischen Wert (die Input-Features hängen von
    // `state.current_player` ab, siehe features.rs/state_to_tensor) — für
    // den jeweils ANDEREN Spieler braucht es deshalb einen zweiten
    // Forward-Pass mit geflipptem `current_player`, nicht einfach `1-wert`.
    let leaf_value = match ACTIVE_LEAF {
        LeafEval::Net => {
            let mover_val = blended_leaf_win_prob(&value, &points, &opp_points);
            let other_val = if MIRROR_OTHER_VAL {
                1.0 - mover_val
            } else {
                // `other_pass` wurde oben bereits per `eval_pair` MIT dem
                // Mover-Pass zusammen berechnet (Paket 1) -- hier nur noch
                // auslesen, kein zweiter Forward-Pass mehr nötig.
                let (o_value, o_points, o_opp_points) =
                    other_pass.expect("need_other_pass deckt genau diesen Zweig ab");
                blended_leaf_win_prob(&o_value, &o_points, &o_opp_points)
            };
            // Perspektiven-/OOD-Audit (siehe Modul-Kommentar oben) -- nur
            // aussagekräftig, wenn `other_val` ein ECHTER zweiter Forward-Pass
            // ist (bei `MIRROR_OTHER_VAL=true` wäre die Divergenz trivial 0,
            // per Konstruktion, keine echte Information).
            if !MIRROR_OTHER_VAL {
                record_perspective_divergence(state.round_number, mover_val, other_val);
            }
            let mut today_value =
                if state.current_player == 0 { [mover_val, other_val] } else { [other_val, mover_val] };

            // Task #78 (v12c Shrinkage) -- NACH blended_leaf_win_prob (oben),
            // aber VOR dem Floor-Shaping-Additiv (unten): das exakte
            // Floor-Signal ist eine reine State-Funktion und soll NICHT durch
            // die Netz-Unsicherheits-Schrumpfung gedämpft werden, nur der
            // rohe Netz-Blattwert selbst. Bei `VALUE_SHRINK_ENABLED=false`
            // (Standard) exakte Identität.
            today_value = apply_value_shrink(today_value, state.round_number);

            // Exakte Floor-Straf-Korrektur (siehe `floor_shaping_delta`-Kommentar) --
            // reine State-Funktion, kein Netz-Forward-Pass, direkt additiv auf
            // beide Perspektiven (Nullsummen-Charakter wie beim own-opp-Value-Ziel
            // bei `opp_bias=1.0`; siehe `floor_shaping_delta_ego`-Kommentar fuer
            // Eskalationsstufe E2 -- ab `opp_bias!=1.0` KEIN Nullsummen-Additiv
            // mehr, jeder Spieler bekommt seinen eigenen, asymmetrisch
            // gewichteten own-minus-bias*opp-Anteil).
            let opp_bias = floor_shaping_opp_bias();
            let (floor_shift0, floor_shift1) = if opp_bias == 1.0 {
                // Bestand, UNVERAENDERTER Rechenweg (kein zusaetzlicher
                // Rundungsschritt) -- `today_value[1] -= shift` ist bit-identisch
                // zu `today_value[1] += (-shift)` (IEEE754-Negation ist exakt).
                let shift = floor_shaping_weight() * floor_shaping_delta(&state).tanh();
                (shift, -shift)
            } else {
                // E2: pro Spieler eigener own-minus-opp_bias*opp-Anteil, siehe
                // `floor_shaping_delta_ego`.
                let w = floor_shaping_weight();
                let d0 = floor_shaping_delta_ego(&state, 0, opp_bias);
                let d1 = floor_shaping_delta_ego(&state, 1, opp_bias);
                (w * d0.tanh(), w * d1.tanh())
            };
            today_value[0] = (today_value[0] + floor_shift0).clamp(0.0, 1.0);
            today_value[1] = (today_value[1] + floor_shift1).clamp(0.0, 1.0);

            // Langreihen-Initiierungs-Additiv (PREREG_long_row_payoff.md
            // par.3/B1) -- reine State-Funktion wie das Floor-Shaping, direkt
            // danach, gleiche Bauform. Bei `w == 0.0` (Default) wird der Block
            // KOMPLETT uebersprungen: keine zusaetzliche Rechnung, keine
            // Rundungsdifferenz, byte-identisches Bestandsverhalten.
            let lr_w = search_config.long_row_init_shaping_w;
            if lr_w != 0.0 {
                // Nullsummen wie beim Floor-Term bei `opp_bias == 1.0`:
                // `long_row_init_delta(state, 1) == -long_row_init_delta(state, 0)`
                // per Konstruktion, deshalb EIN `tanh` und Negation (IEEE754-
                // Negation ist exakt, kein zweiter Rundungsschritt).
                let shift = lr_w * long_row_init_delta(&state, 0).tanh();
                today_value[0] = (today_value[0] + shift).clamp(0.0, 1.0);
                today_value[1] = (today_value[1] - shift).clamp(0.0, 1.0);
            }

            // Task #93: Wertungsplatten-Fortschritts-Additiv, NACH dem
            // Floor-Shaping-Additiv (koexistiert additiv, siehe
            // `apply_plate_shaping`-Kommentar). Bei `PLATE_SHAPING_ENABLED=false`
            // (Standard) exakte Identität -- der Block wird gar nicht ausgeführt.
            today_value = apply_plate_shaping(today_value, &state, parent_state);

            // Wertungsplatten-EGO-Shaping (Nutzer-Auftrag 2026-08-10, siehe
            // Modul-Kommentar bei `apply_scoring_shaping`) -- NACH dem
            // Task-#93-Plattenshaping (koexistieren additiv, unabhaengig
            // schaltbar). Bei `MOSAIC_WERTUNG_SHAPING_W` ungesetzt (Default
            // 0.0) exakte Identitaet -- der Fruehausstieg in
            // `apply_scoring_shaping_full` ueberspringt jede Rechnung.
            today_value = apply_scoring_shaping(today_value, &state);

            // Ownership-Verbraucher Teil 1 (`PREREG_ownership_consumer.md`
            // §2), NACH dem Heuristik-Pol -- gleiche Reihenfolge wie in
            // `net_leaf_eval`. Bei `MOSAIC_OWNERSHIP_W` ungesetzt (Default
            // 0,0) exakte Identitaet: `apply_ownership_shaping` steigt VOR
            // jeder Rechnung aus (kein Sigmoid, kein tanh, keine Rundung).
            today_value = apply_ownership_shaping(today_value, &state, &ownership);

            // KEIN separates Freischalt-Shaping mehr (2026-08-11): der
            // Spezialfeld-Anteil (Kriterium 6 samt ungegatetem ⭐-Bonus) steckt
            // seit der Zusammenfuehrung IM `apply_scoring_shaping`-Term, mit
            // `alphas[6]` als Exponent und demselben Gewicht. Ein zweiter
            // Aufruf wuerde ihn doppelt zaehlen -- genau die Falle, die vorher
            // schon bei Kriterium 6 in beiden Funktionen bestand.

            // Rundenübergang (Phase wechselt von Drafting weg) per Chance-Node-
            // Sampling statt Einzelwert bewerten -- siehe round_transition.rs
            // fuer die Begruendung (verrauschtes Trainingsziel/Blattwert, da die
            // Fabrik-Neubefuellung sonst nirgends als echter Zufallsknoten
            // repraesentiert ist). Standardmaessig AUS (siehe Konstante unten) --
            // erst nach einer Val-R²-Verbesserung im Trainingsziel-Pfad
            // (self_play.rs::play_net_self_play_game) aktivieren.
            if terminal && ROUND_TRANSITION_SAMPLING {
                match crate::round_transition::resolve_to_pre_chance(&state) {
                    Some(pre) => crate::round_transition::sample_round_transition_value(
                        &pre,
                        crate::round_transition::N_SAMPLES_SEARCH,
                        // Dead Code bei `ROUND_TRANSITION_SAMPLING=false` (Standard) --
                        // faellt fuer eine spaetere Aktivierung konsistent auf den
                        // Value-Net (falls Hybrid) statt Policy-Net zurueck.
                        |s, _rng| net_leaf_eval(net_value.unwrap_or(net_policy), s),
                        rng,
                        std::time::Instant::now() + crate::round_transition::TIME_BUDGET,
                    ),
                    None => today_value, // defensiv, sollte durch das `terminal`-Gating nie vorkommen
                }
            } else {
                today_value
            }
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
        // PREREG_denial_tiebreak.md: dieselben `points`/`opp_points`-Rohwerte,
        // die oben bereits fuer `blended_leaf_win_prob` berechnet wurden --
        // hier zusaetzlich abgelegt statt verworfen (kein Zusatz-Forward-Pass).
        points_forecast: points.first().copied(),
        opp_points_forecast: opp_points.first().copied(),
        // PREREG_points_head_plates.md (Stufe 2): `value` wurde oben bereits
        // für `blended_leaf_win_prob` gelesen (siehe `leaf_value`-Berechnung) --
        // hier zusätzlich abgelegt statt verworfen, exakt dasselbe Muster wie
        // `points_forecast`/`opp_points_forecast` (kein Zusatz-Forward-Pass).
        raw_value: value.first().copied(),
        // PREREG_implicit_minimax_backup.md par.1: Blatt/Neuexpansion-Fall
        // ("v_IM = Netz-Value des Knotens") -- exakt derselbe Wert wie
        // `leaf_value`, spaeter per Backprop von `update_im_value_backup`
        // ueberschrieben, sobald es besuchte Kinder gibt.
        im_value: leaf_value,
    }
}

// ── Gumbel AlphaZero (Danihelka/Guez/Schrittwieser/Silver, ICLR 2022) ───────
//
// Motivation (siehe evaluations/STATUS.md, "Struktureller Durchbruch"-
// Abschnitt): selbst nach den Widening-/Tiebreak-Fixes verteilt PUCT sein
// Sim-Budget bei ~150-195 Kandidaten in Runde 1 extrem duenn. Gumbel-Top-m +
// Sequential Halving konzentriert das Budget gezielt auf wenige Kandidaten
// statt "1 Besuch auf 150". Alle Formeln unten exakt aus der DeepMind-mctx-
// Referenzimplementierung (github.com/google-deepmind/mctx: seq_halving.py,
// qtransforms.py, action_selection.py, policies.py) uebernommen, NICHT nur
// aus der Paper-Prosa rekonstruiert -- siehe Plan-Dokument fuer die volle
// Herleitung/Quellenlage.

/// Gewicht der Q-Komponente relativ zum Log-Prior in Gumbel-Scores (§3 des
/// Plans): `σ(q) = (c_visit + max_N) · c_scale · q`. Paper-Werte (NICHT
/// mctx-Bibliotheks-Default 0.1 fuer c_scale) -- unsere Q sind schon
/// [0,1]-Win-Wahrscheinlichkeiten, keine zusaetzliche Min-Max-Rescale wie
/// bei mctx' unbeschraenkten Atari-Rewards noetig.
const GUMBEL_C_VISIT: f64 = 50.0;
/// GEMESSEN UND BESTAETIGT (2026-07-29, Task #18) -- bleibt 1.0.
///
/// `tools/gumbel_scale_calibration.py` hat ueber 216 frozen-set-Stellungen
/// (v18_best @ 400 Sims, letzte Sequential-Halving-Phase) erhoben, wie schwer
/// `sigma(q)` gegenueber `ln(prior)` wiegt -- beide ueber DIESELBE
/// Kandidatenmenge:
///   delta_q          Median 0,0073   delta_ln(prior)  Median 1,11
///   max_N            Median 96       Verhaeltnis      Median 1,23
///   je Runde: 1,01 / 1,08 / 1,56 / 1,44
/// q und Prior wiegen also praktisch gleich schwer; fuer exakte Gleichheit
/// waere c_scale = 0,81 noetig. Die Begruendung oben traegt damit.
///
/// GEGENPROBE (gepaarter Arena-A/B, v18_best@400 vs v17_best@400, 400 Spiele
/// je Arm, identischer Basis-Seed 31415926), c_scale 1,0 gegen 0,3:
///   Arm 1,0: Champion 210:190 | Score 39,13 vs 37,77 (Summe 76,90) | Floor 13,85/14,97
///   Arm 0,3: Champion 248:152 | Score 35,59 vs 31,32 (Summe 66,91) | Floor 15,61/17,32
///   McNemar p = 0,0057
///
/// Die Siegquote spricht fuer 0,3 -- **uebernommen wurde es trotzdem NICHT**.
/// Bei 0,3 spielen BEIDE Seiten massiv schlechter: zehn Punkte weniger in der
/// Summe (-13 %) und deutlich mehr Bodenstrafen auf beiden Brettern. Ein
/// kleineres c_scale verschiebt Gewicht von der SUCHE zum Policy-Prior; die
/// Suche traegt dann weniger bei. Dass v18 dabei oefter gewinnt, misst nur, dass
/// v17 unter der verschlechterten Suche staerker einbricht (v18 hat den besseren
/// Prior) -- also RELATIVE Robustheit, nicht Staerke.
///
/// LEHRE: bei einer engine-weiten Aenderung, die BEIDE Seiten trifft, ist die
/// Siegquote im Champion-gegen-Vorgaenger-Duell KEIN gueltiges Staerkemass. Der
/// absolute Ø-Score ist hier das entscheidende Signal gewesen.
const GUMBEL_C_SCALE: f64 = 1.0;

/// Anzahl der per Gumbel-Top-m an der Wurzel gezogenen Kandidaten (vor
/// Sequential Halving). Paper-/mctx-Standardwert, aus Go/Schach-Experimenten
/// mit aehnlichem/groesserem Verzweigungsfaktor -- fuer dieses Spiel noch
/// nicht eigens kalibriert (siehe Plan-Dokument, "Offene Risiken").
///
/// Dient seit Task #14 (PCR-Vorbereitung, 2026-08-02) als OBERE Grenze
/// (Ceiling) fuer `gumbel_top_m_for_budget` unten, nicht mehr als der fuer
/// JEDEN Suchaufruf feste Wert -- bleibt als eigene Konstante bestehen, weil
/// `lib.rs::engine_config_json` sie weiterhin als Referenz-/Ceiling-Wert ins
/// Lauf-Manifest schreibt (das tatsaechliche, budgetabhaengige M eines
/// einzelnen Suchaufrufs steht dort NICHT drin, nur die Obergrenze).
pub const GUMBEL_TOP_M: usize = 16;

/// Sim-budget-abhaengige Ober-Grenze fuer die Gumbel-Top-m-Kandidatenzahl
/// (Task #14, PCR-Vorbereitung, 2026-08-02): vorher war `GUMBEL_TOP_M` eine
/// reine Compile-Time-Konstante, gleich fuer JEDEN Suchaufruf, unabhaengig
/// vom tatsaechlichen Sim-Budget dieses Zugs. Mit Playout-Cap-Randomization
/// (KataGo-Vorbild, siehe `self_play.rs`) laufen im selben Prozess klassische
/// Voll-Suchen (400/600 Sims) UND sehr guenstige Cheap-Suchen (z.B. 150 Sims
/// oder weniger). Bei fixem M=16 wuerde eine Cheap-Suche mit z.B. 64 Sims
/// versuchen, 16 Kandidaten ueber `ceil(log2(16))=4` Sequential-Halving-Phasen
/// zu verteilen: 16*4=64 Sim-"Slots" (siehe `remaining_slots` unten) sind dann
/// schon aufgebraucht, nur um JEDEN Kandidaten EINMAL pro Phase zu besuchen --
/// keine Reserve mehr fuer die eigentliche Differenzierung (Sequential
/// Halving braucht MEHRERE Besuche pro Kandidat pro Phase, damit die
/// Q-Schaetzung, nach der die naechste Haelfte eliminiert wird, ueberhaupt
/// aussagekraeftig ist).
///
/// Formel: `m(budget) = clamp(round(budget / 16), 4, GUMBEL_TOP_M)`.
/// - Referenzteiler 16: bei den bisherigen Standard-Budgets ergibt
///   `round(400/16)=25` bzw. `round(600/16)=38`, beide werden vom oberen
///   Clamp auf `GUMBEL_TOP_M=16` gekappt -- IDENTISCHES Verhalten zur alten
///   fixen Konstante bei allen bisher produktiv genutzten Sim-Zahlen (400,
///   600). Regressionstest: `gumbel_top_m_for_budget_unchanged_at_400_and_600_sims`.
/// - Obere Grenze `GUMBEL_TOP_M`: der bisherige Paper-/mctx-Standardwert wird
///   durch die Skalierung nie ueberschritten -- keine unkalibrierte
///   Vergroesserung der Wurzelbreite ueber den bisher genutzten Bereich
///   hinaus.
/// - Untere Grenze 4: unter 4 Kandidaten verliert Sequential Halving an Sinn
///   (mit `ceil(log2(m))`-Phasen braucht selbst `m=2` schon eine
///   Halbierungs-Phase; bei `m=1` degeneriert die Suche zur reinen
///   Tiefensuche eines einzigen Zugs, siehe `candidates.len() <= 1`-Zweig
///   unten) -- 4 haelt auch bei sehr kleinen Cheap-Budgets eine minimale
///   Kandidaten-Diversitaet an der Wurzel.
/// - Dazwischen (z.B. Cheap-Suche mit 150 Sims -> `round(150/16)=9`):
///   proportional zum Budget, damit jeder Halbierungs-"Slot"
///   (`remaining_slots = remaining_phases * current.len()`, s.u.) im Schnitt
///   in einer aehnlichen Groessenordnung Sims pro Kandidat bleibt wie beim
///   bisherigen 400/600-Sims-Betrieb bei M=16.
pub fn gumbel_top_m_for_budget(sims: u32) -> usize {
    if let Some(m) = gumbel_top_m_override() {
        return m;
    }
    let raw = (sims as f64 / 16.0).round() as i64;
    raw.clamp(4, GUMBEL_TOP_M as i64) as usize
}

/// Fester Wurzelbreiten-Override via `MOSAIC_GUMBEL_TOP_M` (PREREG_
/// suchpfad_nachmessungen.md, Messung 2 -- m-Formel vs feste Breite bei
/// niedrigen Sims). `0`/nicht gesetzt/nicht parsbar = `None` = Formel
/// (Bestandsverhalten). Einmalig gelesen (OnceLock, #30-Muster); wirkt
/// auf JEDEN `gumbel_top_m_for_budget`-Aufruf, `m_prime = min(m, n_root)`
/// begrenzt weiterhin auf die legale Zugzahl.
fn gumbel_top_m_override() -> Option<usize> {
    static CELL: std::sync::OnceLock<Option<usize>> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| {
        let m = read_f64_env("MOSAIC_GUMBEL_TOP_M", 0.0);
        if m >= 1.0 { Some(m.round() as usize) } else { None }
    })
}

/// τ-Annealing-Schwelle fuer den SELF-PLAY-Zugwahl-Pfad via
/// `MOSAIC_TAU_ARGMAX_FROM_MOVE` (`evaluations/PREREG_search_path_remeasurements.md`,
/// Messung 3 -- "fruehe Zuege τ=1 (Sampling, Bestandsverhalten), ab einem
/// Schwellen-Zug argmax"). `0`/nicht gesetzt/nicht parsbar = `None` = AUS
/// (Bestandsverhalten: die GANZE Partie wird weiterhin proportional zur
/// Besuchsverteilung gesampelt, siehe `self_play::net_drafting_policy`).
/// Einmalig gelesen (OnceLock, #30-Muster). N>=1: ab dem N-ten Halbzug EINER
/// Partie (1-basiert, beide Spieler zusammen gezaehlt -- siehe
/// `self_play::play_net_self_play_game`s `move_number`-Zaehler) wird statt
/// gesampelt der argmax der bestehenden Besuchsverteilung gespielt
/// (Gleichstand: deterministisch der erste Eintrag, siehe
/// `self_play::argmax_index`). Vorab-Festlegung im PREREG: Schwelle 30 (grob
/// Runde 1+, siehe `evaluations/actions_per_round.md`: ~11 Zuege/Runde/
/// Spieler). Wirkt NUR im Self-Play-Pfad (`self_play::net_drafting_policy`,
/// einziger produktiver Aufrufer ist `run_net_self_play`/
/// `play_net_self_play_game`) -- der Arena-/GUI-Pfad
/// (`net_search_state_json`/`net_search_with_tree` in `lib.rs`) ruft weder
/// diese Funktion noch `net_drafting_policy` auf und bleibt unveraendert.
pub(crate) fn tau_argmax_from_move() -> Option<usize> {
    static CELL: std::sync::OnceLock<Option<usize>> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| {
        let n = read_f64_env("MOSAIC_TAU_ARGMAX_FROM_MOVE", 0.0);
        if n >= 1.0 { Some(n.round() as usize) } else { None }
    })
}

/// ε-Fenster des Denial-Tie-Breaks (PREREG_denial_tiebreak.md, Task E3) via
/// `MOSAIC_DENIAL_TIEBREAK_EPS` -- Default `0.0` = AUS = byte-identisches
/// Bestandsverhalten (`apply_denial_tiebreak`s Fruehausstieg liest diesen
/// Wert). Einmalig gelesen (OnceLock, #30-Muster, siehe `floor_shaping_
/// weight`/`gumbel_top_m_override` oben). ε liegt auf der completed-Q-Skala
/// ([0,1]-Gewinnwahrscheinlichkeit, siehe `completed_q_per_candidate`) --
/// KEINE separate Klemmung noetig, negative/absurd grosse Werte degenerieren
/// von selbst zu "nie ausserhalb des Fensters" bzw. "Fenster leer" in
/// `apply_denial_tiebreak_with`.
fn denial_tiebreak_eps() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_DENIAL_TIEBREAK_EPS", 0.0))
}

/// z-Schwelle des E3b-Unsicherheits-Fensters (PREREG_denial_tiebreak.md,
/// Abschnitt "E3b" -- Nachfolger von E3, siehe dortiges ERGEBNIS) via
/// `MOSAIC_DENIAL_UNCERT_Z` -- Default `0.0` = AUS = byte-identisches
/// Bestandsverhalten (`apply_denial_tiebreak_uncert_with`s Fruehausstieg
/// liest diesen Wert, gleiches Muster wie `denial_tiebreak_eps` oben).
/// Einmalig gelesen (OnceLock, #30-Muster). `z` skaliert den Zwei-Anteils-
/// Standardfehler in `denial_uncert_qualifies` -- KEINE separate Klemmung
/// noetig (negative Werte degenerieren von selbst zu "Fenster nie erfuellt
/// ausser bei exakter Q-Gleichheit").
fn denial_uncert_z() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_DENIAL_UNCERT_Z", 0.0))
}

/// Mindest-Besuchsanteil `f` des E3b-Besuchs-Gates (PREREG_denial_tiebreak.md,
/// Abschnitt "E3b") via `MOSAIC_DENIAL_MIN_VISIT_FRAC` -- Default `0,5`
/// (PREREG-Vorgabe). Nur wirksam, wenn `denial_uncert_z() > 0.0` (siehe
/// dortige Doku); gleiches OnceLock-Cache-Muster wie `denial_uncert_z`.
fn denial_min_visit_frac() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_DENIAL_MIN_VISIT_FRAC", 0.5))
}

/// Schaltet die Suche komplett auf Gumbel-AlphaZero um (Wurzel: Gumbel-Top-m
/// + Sequential Halving statt Dirichlet-Noise + PUCT; Tiefe≥1: neue
/// deterministische Auswahlregel statt `best_puct`; Policy-Ziel: completed-Q-
/// Softmax statt Besuchsanteil). Standardmaessig AUS, bis Phase 3 (Arena-
/// Validierung ohne Neu-Training) ein Ergebnis liefert -- gleiches Muster
/// wie `ACTIVE_LEAF`/`MIRROR_OTHER_VAL`.
pub const USE_GUMBEL_SEARCH: bool = true;

/// Schaltet die dynamic_sims-Entkopplung im Gumbel-Netzpfad frei (externer
/// Befund, 2026-07-20, siehe `net_effective_sims`). Standardmäßig AN
/// (Nutzer-Entscheidung, 2026-07-21) -- Arena-Ablation davor (n=100, Netz
/// fest auf 330 Sims vs. Heuristik unverändert bei 150) ergab 20:80 (20%),
/// innerhalb des Rauschbands der 22-26%-Bestmarke, kein klarer Effekt in
/// diesem einzelnen Test, aber auch keine Verschlechterung -- die
/// theoretische Begründung (Gumbel-Wurzelbreite ist fix, dynamic_sims'
/// Kopplung an die Aktionszahl hat dort keine Grundlage mehr) bleibt
/// unabhängig vom uneindeutigen Arena-Ergebnis gültig.
/// **WICHTIG für alle Aufrufstellen mit `base_sims`** (Server-Mensch-vs-KI,
/// `self_play.py --mode network`, Arena-Konstanten): `dynamic_sims` skalierte
/// einen Wert wie 150 bisher automatisch auf ~185-499 hoch (siehe
/// `evaluations/actions_per_round.md`) -- mit dieser Umstellung ist der
/// übergebene Wert jetzt die TATSÄCHLICHE Sims-Zahl, keine Basis mehr.
/// Bestehende `base_sims`-Werte ggf. entsprechend nach oben anpassen, um
/// dieselbe effektive Suchtiefe zu behalten (z.B. `arena.py`s bisheriges
/// `NET_SIMS=150` ⇒ vergleichbar wäre eher ~300-330 flach).
pub const DECOUPLE_NET_SIMS_FROM_ACTIONS: bool = true;

/// Sims-Skalierung für NETZGEFÜHRTE Suche (Gumbel oder PUCT-Legacy) --
/// externer Befund (2026-07-20): `mcts::dynamic_sims`s Kopplung an die
/// Aktionszahl war für die alte PUCT-Zwangs-Expansion begründet (mehr
/// Kandidaten -> mehr Sims nötig, sonst Breitensuche ohne Differenzierung).
/// Mit Gumbel-Top-m + Sequential Halving ist die Wurzelbreite FIX
/// (`GUMBEL_TOP_M`) -- 195 legale Aktionen kosten nicht mehr Suchaufwand
/// als 44, dieselben Sims werden unabhängig von der Aktionszahl sinnvoll
/// auf `GUMBEL_TOP_M` Kandidaten verteilt. Die Kopplung ist im Gumbel-Pfad
/// daher THEORETISCH eine Fehlallokation (Zusatzbudget an breiten Wurzeln,
/// wo es am wenigsten bringt; Einsparung an engen Stellungen, wo es am
/// meisten hilft) -- EMPIRISCH aber noch nicht bestätigt (siehe
/// `DECOUPLE_NET_SIMS_FROM_ACTIONS`-Kommentar), daher Toggle statt Standard.
/// Bei `USE_GUMBEL_SEARCH=true UND DECOUPLE_NET_SIMS_FROM_ACTIONS=true`:
/// `base_sims` unverändert zurückgeben. Sonst (inkl. PUCT-Legacy-Pfad, wo
/// `dynamic_sims` weiterhin seine ursprüngliche Begründung hat): normales
/// `dynamic_sims`-Verhalten. Betrifft NUR netzgeführte Suche -- die
/// Heuristik-MCTS (`mcts.rs`) behält `dynamic_sims` an ihren eigenen
/// Aufrufstellen unverändert (braucht die Skalierung weiterhin, da sie
/// klassisches PUCT+Widening ohne Gumbel nutzt).
pub fn net_effective_sims(base_sims: u32, num_actions: usize) -> u32 {
    if USE_GUMBEL_SEARCH && DECOUPLE_NET_SIMS_FROM_ACTIONS {
        base_sims
    } else {
        crate::mcts::dynamic_sims(base_sims, num_actions)
    }
}

/// Gumbel(0,1)-Ziehung: `-ln(-ln(U))`, `U ~ Uniform(0,1)` (offenes Intervall,
/// `U=0` waere `ln(0)=-inf`).
fn sample_gumbel<R: Rng + ?Sized>(rng: &mut R) -> f64 {
    let u: f64 = rng.random_range(f64::MIN_POSITIVE..1.0);
    -(-u.ln()).ln()
}

/// `σ(q) = (c_visit + max_N) · c_scale · q` -- siehe Modul-Kommentar.
fn gumbel_sigma(q: f64, max_n: u32) -> f64 {
    (GUMBEL_C_VISIT + max_n as f64) * GUMBEL_C_SCALE * q
}

/// Eigener Netz-/DFS-Blattwert von `nid`, aus der Sicht des an DIESEM Knoten
/// ziehenden Spielers (`state.current_player`) -- NICHT `nodes[nid].value`
/// (das akkumuliert aus der Sicht des Spielers, der in `nid` HINEIN gezogen
/// ist, i.d.R. der GEGNER von `state.current_player`). Für `v_mix` brauchen
/// wir explizit die Perspektive des Spielers, dessen Kinder gerade bewertet
/// werden -- exakt dieselbe Perspektive, in der `nodes[cid].value/visits`
/// für Kinder von `nid` bereits akkumuliert (deren `player_who_acted` ist
/// der Zieher AN `nid`, siehe `make_node`-Aufruf beim Expandieren).
fn node_own_value(nodes: &[Node], nid: usize) -> f64 {
    nodes[nid].leaf_value[nodes[nid].state.current_player]
}

/// `v_mix` (§4 des Plans) -- PRIOR-gewichtet über besuchte Kinder von `nid`
/// (NICHT visit-gewichtet, ein leicht zu verwechselnder Punkt):
/// `v_mix = (v(nid) + N_total · Σ_besucht[π(a)·Q(a)] / Σ_besucht[π(a)]) / (1 + N_total)`.
/// Fällt bei `N_total=0` (noch kein Kind besucht) exakt auf `v(nid)` zurück.
fn v_mix(nodes: &[Node], nid: usize) -> f64 {
    let v_node = node_own_value(nodes, nid);
    let n_total: f64 = nodes[nid].children.iter().map(|&c| nodes[c].visits as f64).sum();
    if n_total <= 0.0 {
        return v_node;
    }
    let mut prior_sum = 0.0f64;
    let mut weighted_q_sum = 0.0f64;
    for &c in &nodes[nid].children {
        if nodes[c].visits == 0 {
            continue;
        }
        let p = (nodes[c].prior as f64).max(1e-9);
        let q = nodes[c].value / nodes[c].visits as f64;
        prior_sum += p;
        weighted_q_sum += p * q;
    }
    if prior_sum <= 0.0 {
        return v_node;
    }
    (v_node + n_total * (weighted_q_sum / prior_sum)) / (1.0 + n_total)
}

/// `(Prior, completed Q)` je Kandidat von `nid`, Reihenfolge: erst
/// `children` (besucht → eigenes Q), dann `untried` (unbesucht → `v_mix`,
/// derselbe Wert für alle unbesuchten Kandidaten desselben Knotens).
fn completed_q_per_candidate(nodes: &[Node], nid: usize) -> Vec<(f64, f64)> {
    let vmix = v_mix(nodes, nid);
    let mut out: Vec<(f64, f64)> =
        Vec::with_capacity(nodes[nid].children.len() + nodes[nid].untried.len());
    for &c in &nodes[nid].children {
        let prior = nodes[c].prior as f64;
        let q = if nodes[c].visits > 0 { nodes[c].value / nodes[c].visits as f64 } else { vmix };
        out.push((prior, q));
    }
    for (_, prior) in &nodes[nid].untried {
        out.push((*prior as f64, vmix));
    }
    out
}

// ── PREREG_implicit_minimax_backup.md par.1: Implicit-Minimax-Backups
// (Baier/Winands) -- additiver Backup-/Selektionspfad, siehe `Node::im_value`-
// Doku fuer die Perspektiv-Konvention.

/// Reine Mischformel `Q = (1-alpha)*Q_MC + alpha*v_IM` (PREREG par.1). Kein
/// Env-/Node-Zugriff -- direkt testbar, gleiches Trennungsmuster wie
/// `calibrate_win_prob_with`. Early-Out bei `alpha==0.0` (Default): gibt
/// `q_mc` UNVERAENDERT zurueck, byte-identisches Bestandsverhalten (keine
/// Rundungsdifferenz durch die Mischrechnung selbst).
pub(crate) fn mix_q_with_implicit_minimax(q_mc: f64, v_im: f64, alpha: f64) -> f64 {
    if alpha == 0.0 {
        return q_mc;
    }
    (1.0 - alpha) * q_mc + alpha * v_im
}

/// Backup-Kern (PREREG par.1): aktualisiert `nodes[nid].im_value` per
/// Minimax ueber die BESUCHTEN Kinder von `nid`, aus der Sicht des an `nid`
/// ziehenden Spielers (`nodes[nid].state.current_player`). Kinder von `nid`
/// teilen sich per Konstruktion GENAU diese Perspektive als ihr eigenes
/// `player_who_acted` (derselbe Grund, aus dem `completed_q_per_candidate`s
/// Kinder-Q-Werte ohne Vorzeichenwechsel vergleichbar sind) -- deshalb reicht
/// ein direkter Index `im_value[mover]` je Kind, KEINE Negation wie bei
/// alternierendem Negamax. Minimax = der Zieher waehlt das fuer sich selbst
/// beste besuchte Kind; DESSEN VOLLER `im_value`-Vektor (beide Spieler) wird
/// uebernommen -- nicht nur die eigene Komponente, denn die Wahl legt fest,
/// welcher Zweig ueberhaupt weitergespielt wird, und damit AUCH den Wert des
/// Gegners. Ohne besuchte Kinder (frischer Blattknoten): unveraendert, bleibt
/// der bei der Knotenerzeugung gesetzte `leaf_value`-Wert stehen ("Blatt/
/// Neuexpansion: v_IM = Netz-Value des Knotens", PREREG par.1). Reine
/// Arithmetik, kein Netz-/RNG-Zugriff -- wird daher IMMER mitgefuehrt,
/// unabhaengig vom `MOSAIC_IMPLICIT_MINIMAX_A`-Knopf (siehe `backprop_path`).
fn update_im_value_backup(nodes: &mut [Node], nid: usize) {
    let mover = nodes[nid].state.current_player;
    let mut best: Option<[f64; 2]> = None;
    let mut best_score = f64::NEG_INFINITY;
    for &c in &nodes[nid].children {
        if nodes[c].visits == 0 {
            continue;
        }
        let score = nodes[c].im_value[mover];
        if score > best_score {
            best_score = score;
            best = Some(nodes[c].im_value);
        }
    }
    if let Some(v) = best {
        nodes[nid].im_value = v;
    }
}

/// Gemeinsamer Backprop-Kern der drei (vormals duplizierten) Backprop-
/// Stellen in `build_gumbel_tree_inner` (`descend_and_backprop` + beide
/// `visit_candidate!`-Zweige): aktualisiert `visits`/`value` (Bestands-
/// verhalten, UNVERAENDERT -- byte-identische Rechenreihenfolge wie vorher)
/// UND -- additiv, PREREG_implicit_minimax_backup.md par.1 -- `im_value`
/// entlang desselben Pfads von `leaf_nid` bis zur Wurzel. `update_im_value_
/// backup` laeuft fuer JEDEN Knoten NACH dessen `visits`/`value`-Update, aber
/// noch INNERHALB derselben Schleifeniteration -- alle Geschwister-Kinder
/// weiter unten im Baum haben ihren `im_value` zu diesem Zeitpunkt bereits
/// aus fruaheren Besuchen (oder eben JETZT, auf demselben Pfad) korrekt
/// gesetzt.
fn backprop_path(nodes: &mut [Node], leaf_nid: usize) {
    let value = nodes[leaf_nid].leaf_value;
    let mut cur = Some(leaf_nid);
    while let Some(i) = cur {
        nodes[i].visits += 1;
        nodes[i].value += value[nodes[i].player_who_acted];
        update_im_value_backup(nodes, i);
        cur = nodes[i].parent;
    }
}

/// Wie [`completed_q_per_candidate`], aber die Q-Komponente besuchter Kinder
/// wird per `alpha` mit `im_value` gemischt (`mix_q_with_implicit_minimax`,
/// PREREG par.1). NUR fuer die Tiefe-≥1-Selektion (`gumbel_select_child`) --
/// bewusst NICHT als Ersatz fuer `completed_q_per_candidate` selbst, dessen
/// bestehende Aufrufstellen (`root_completed_q_policy`/`root_completed_q_raw`
/// -- die nach aussen gegebenen Policy-Targets -- sowie die Wurzel-Tie-
/// Break-Sonden) UNVERAENDERT bleiben (minimal-invasive Designentscheidung,
/// siehe Abnahmebericht: Mischung wirkt nur auf die interne Suchselektion,
/// nie auf trainingsrelevante Ausgaben). Unbesuchte Kandidaten bekommen wie
/// bisher `v_mix` OHNE Mischung -- kein `im_value` vorhanden, da noch nicht
/// expandiert. Bei `alpha==0.0` liefert `mix_q_with_implicit_minimax` fuer
/// jedes besuchte Kind exakt `q_mc` zurueck -- Ergebnis dann zahlengleich zu
/// `completed_q_per_candidate` (siehe Paritaetstest).
fn completed_q_per_candidate_mixed(nodes: &[Node], nid: usize, alpha: f64) -> Vec<(f64, f64)> {
    let vmix = v_mix(nodes, nid);
    let mover = nodes[nid].state.current_player;
    let mut out: Vec<(f64, f64)> =
        Vec::with_capacity(nodes[nid].children.len() + nodes[nid].untried.len());
    for &c in &nodes[nid].children {
        let prior = nodes[c].prior as f64;
        let q = if nodes[c].visits > 0 {
            let q_mc = nodes[c].value / nodes[c].visits as f64;
            mix_q_with_implicit_minimax(q_mc, nodes[c].im_value[mover], alpha)
        } else {
            vmix
        };
        out.push((prior, q));
    }
    for (_, prior) in &nodes[nid].untried {
        out.push((*prior as f64, vmix));
    }
    out
}

/// Softmax über `f64`-Scores (eigene Kopie statt `net::softmax`, das auf
/// `f32` arbeitet -- Gumbel-Score-Summen (Log-Prior + σ(Q)) profitieren von
/// der zusätzlichen Präzision).
fn softmax_f64(scores: &[f64]) -> Vec<f64> {
    let m = scores.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    let exps: Vec<f64> = scores.iter().map(|&x| (x - m).exp()).collect();
    let sum: f64 = exps.iter().sum();
    if sum > 0.0 {
        exps.iter().map(|&e| e / sum).collect()
    } else {
        vec![1.0 / scores.len().max(1) as f64; scores.len()]
    }
}

/// `π'_node(a) = softmax(ln(prior(a)) + σ(completedQ(a)))` über
/// `children ∪ untried` von `nid`, gleiche Reihenfolge wie
/// `completed_q_per_candidate`. `max_N` (für σ) = größte Besuchszahl unter
/// `nid`s Kindern JETZT (wächst über die Suche).
fn improved_policy(nodes: &[Node], nid: usize) -> Vec<f64> {
    let max_n = nodes[nid].children.iter().map(|&c| nodes[c].visits).max().unwrap_or(0);
    let cq = completed_q_per_candidate(nodes, nid);
    let scores: Vec<f64> =
        cq.iter().map(|&(p, q)| p.max(1e-9).ln() + gumbel_sigma(q, max_n)).collect();
    softmax_f64(&scores)
}

/// Wie [`improved_policy`], aber ueber `completed_q_per_candidate_mixed`
/// (PREREG_implicit_minimax_backup.md par.1) statt der ungemischten
/// `completed_q_per_candidate` -- NUR fuer `gumbel_select_child` (Tiefe-≥1-
/// Selektion), siehe dortige Doku fuer die minimal-invasive Scope-
/// Entscheidung. Bei `alpha==0.0` zahlengleich zu `improved_policy` (die
/// Mischformel selbst ist dann ein Early-Out, siehe `mix_q_with_implicit_
/// minimax`).
fn improved_policy_mixed(nodes: &[Node], nid: usize, alpha: f64) -> Vec<f64> {
    let max_n = nodes[nid].children.iter().map(|&c| nodes[c].visits).max().unwrap_or(0);
    let cq = completed_q_per_candidate_mixed(nodes, nid, alpha);
    let scores: Vec<f64> =
        cq.iter().map(|&(p, q)| p.max(1e-9).ln() + gumbel_sigma(q, max_n)).collect();
    softmax_f64(&scores)
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

/// Meistbesuchtes Wurzelkind (Tiebreak: Mittelwert Q, dann Prior) — Pendant
/// zu `mcts::best_root_child`. Externer Bugfix-Hinweis (2026-07-20): ein
/// reines `max_by_key(|c| nodes[c].visits)` ist hier ein echter Bug --
/// Rusts `max_by_key`/`max_by` liefern bei Gleichstand das LETZTE Maximum,
/// Kinder werden aber in ABSTEIGENDER Prior-Reihenfolge expandiert (siehe
/// `build_net_tree`s `untried.remove(0)`), das letzte (gleichstehende) Kind
/// ist also das mit dem NIEDRIGSTEN Prior im behaltenen Set. Besuchsgleich-
/// stand ist in frühen, hochverzweigten Runden wegen der (jetzt engeren,
/// aber nicht eliminierten) Voll-Expansions-Neigung der Normalfall --
/// ohne Tiebreak würde dort systematisch der am schlechtesten bewertete
/// Kandidat gespielt.
fn best_root_child(nodes: &[Node], children: &[usize]) -> Option<usize> {
    children.iter().copied().max_by(|&a, &b| {
        let qa = if nodes[a].visits > 0 { nodes[a].value / nodes[a].visits as f64 } else { 0.0 };
        let qb = if nodes[b].visits > 0 { nodes[b].value / nodes[b].visits as f64 } else { 0.0 };
        nodes[a]
            .visits
            .cmp(&nodes[b].visits)
            .then(qa.partial_cmp(&qb).unwrap_or(std::cmp::Ordering::Equal))
            .then(nodes[a].prior.partial_cmp(&nodes[b].prior).unwrap_or(std::cmp::Ordering::Equal))
    })
}

/// Tiefe-≥1-Auswahl über `children ∪ untried` von `nid` (Gumbel-Pendant zu
/// `best_puct`, §6 des Plans, JETZT mctx-treu ohne PUCT-geerbte Forced-
/// Expansion/Widening-Cap-Sonderbehandlung -- Paket 2 des Speed-Bündels,
/// 2026-07-22): `argmax[π'_node(a) − N(a)/(1+ΣN)]` über ALLE Kandidaten,
/// unbesuchte (untried) zählen mit `N(a)=0`, exakt wie mctx' `action_selection.py`
/// (vorher: nur über `nodes[nid].children`, WELCHE Kandidaten überhaupt als
/// Kind entstehen durften, entschied ein separater Progressive-Widening-Cap
/// -- beides jetzt entfernt, siehe `descend_and_backprop`).
///
/// Rückgabe: Index INNERHALB des Kombi-Vektors (`completed_q_per_candidate`-
/// Reihenfolge: erst `children`, dann `untried`). `< children.len()` heißt
/// bestehendes Kind (`nodes[nid].children[idx]`), sonst unbesuchter Kandidat
/// bei Offset `idx - children.len()` in `nodes[nid].untried` -- der Aufrufer
/// entscheidet anhand dieses Index, ob deszendiert oder on-demand expandiert
/// wird.
///
/// PREREG_implicit_minimax_backup.md par.1: EINZIGE Stelle, an der die
/// Implicit-Minimax-Beimischung wirkt (`MOSAIC_IMPLICIT_MINIMAX_A` ueber
/// `search_config.implicit_minimax_alpha`, PREREG_agent_encapsulation.md
/// par.4 Punkt 4, Pilot-Migration) -- bei `alpha==0.0` (Default) exakt der
/// ungemischte `improved_policy`-Aufruf von vorher, kein zusaetzlicher
/// Rechenpfad (Byte-Identitaet).
fn gumbel_select_child(nodes: &[Node], nid: usize, search_config: &SearchConfig) -> usize {
    let alpha = search_config.implicit_minimax_alpha;
    let policy = if alpha == 0.0 {
        improved_policy(nodes, nid)
    } else {
        improved_policy_mixed(nodes, nid, alpha)
    };
    let n_children = nodes[nid].children.len();
    let sum_n: f64 = nodes[nid].children.iter().map(|&c| nodes[c].visits as f64).sum();
    let mut best = 0usize;
    let mut best_adv = f64::NEG_INFINITY;
    for (i, &p) in policy.iter().enumerate() {
        let n_a = if i < n_children { nodes[nodes[nid].children[i]].visits as f64 } else { 0.0 };
        let adv = p - n_a / (1.0 + sum_n);
        if adv > best_adv {
            best_adv = adv;
            best = i;
        }
    }
    best
}

/// Finale Wurzel-Zugwahl im Gumbel-Modus (§7 des Plans, `gumbel_scale=0` für
/// Arena/Produktion -- keine Ziehung): unter den Wurzelkindern mit
/// `N(a) == max_a N(a)` (den Sequential-Halving-Überlebenden), `argmax[
/// ln(prior(a)) + σ(completedQ(a))]`. Für besuchte Überlebende ist
/// `completedQ` immer das eigene Q (nie `v_mix`, siehe `completed_q`-
/// Kommentar), daher direkt `value/visits` statt der vollen
/// `completed_q_per_candidate`-Maschinerie.
fn gumbel_final_root_action(nodes: &[Node]) -> Option<usize> {
    let children = &nodes[0].children;
    if children.is_empty() {
        return None;
    }
    let max_n = children.iter().map(|&c| nodes[c].visits).max().unwrap_or(0);
    children
        .iter()
        .copied()
        .filter(|&c| nodes[c].visits == max_n)
        .max_by(|&a, &b| {
            let score = |cid: usize| -> f64 {
                let prior = (nodes[cid].prior as f64).max(1e-9);
                let q = if nodes[cid].visits > 0 { nodes[cid].value / nodes[cid].visits as f64 } else { 0.0 };
                prior.ln() + gumbel_sigma(q, max_n)
            };
            score(a).partial_cmp(&score(b)).unwrap_or(std::cmp::Ordering::Equal)
        })
}

// ── PREREG_denial_tiebreak.md (Task E3): Denial-Tie-Break an der Wurzel ────
//
// Unter allen Wurzelkindern, deren completed-Q im ε-Fenster um das der
// `gumbel_final_root_action`-Basisaktion liegt (quasi-gleichwertige Züge),
// spielt die Suche stattdessen den Zug mit der NIEDRIGSTEN prognostizierten
// Gegner-Punktzahl (aus Wurzelspieler-Sicht). ε=0.0 (Default) => sofortiger
// Return der Basisaktion, kein zusätzlicher Vergleich, kein Netz-/RNG-
// Verbrauch -- byte-identisches Bestandsverhalten (gleiches Additiv-Muster
// wie `MOSAIC_FLOOR_SHAPING_W`/`MOSAIC_TAU_ARGMAX_FROM_MOVE`).

static DENIAL_TIEBREAK_FIRED: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static DENIAL_TIEBREAK_TOTAL: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);

/// Zaehlt eine Denial-Tie-Break-Auswertung -- nur erreicht, wenn `ε>0` UND
/// das Netz einen `opp_points`-Kopf hat (siehe `apply_denial_tiebreak_with`s
/// Fruehausstiege; bei `ε=0`/Legacy-Netz bleiben BEIDE Zaehler unveraendert,
/// keine "leere" Buchung). `fired`: true, wenn tatsaechlich eine ANDERE
/// Aktion als die Gumbel-Basisaktion gewaehlt wurde. Billiges Debug-
/// Instrument fuer die PREREG-Messgroesse "Anteil getauschter Zuege" -- zwei
/// `AtomicU64`, `Ordering::Relaxed` (keine kausale Abhaengigkeit anderer
/// Zustandsaenderungen an diesem Zaehler, gleiches Muster wie
/// `profiling.rs`s Zaehler-Paare).
fn note_denial_tiebreak(fired: bool) {
    DENIAL_TIEBREAK_TOTAL.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    if fired {
        DENIAL_TIEBREAK_FIRED.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    }
}

/// Snapshot `(fired, total)` der Denial-Tie-Break-Zaehler -- fuer die
/// Stichproben-Auswertung "wie oft feuert der Tie-Break" aus
/// PREREG_denial_tiebreak.md.
pub fn denial_tiebreak_stats() -> (u64, u64) {
    (
        DENIAL_TIEBREAK_FIRED.load(std::sync::atomic::Ordering::Relaxed),
        DENIAL_TIEBREAK_TOTAL.load(std::sync::atomic::Ordering::Relaxed),
    )
}

/// Setzt beide Denial-Tie-Break-Zaehler zurueck (Test-/Mess-Helfer, gleiches
/// Muster wie `profiling::reset_all`).
pub fn reset_denial_tiebreak_stats() {
    DENIAL_TIEBREAK_FIRED.store(0, std::sync::atomic::Ordering::Relaxed);
    DENIAL_TIEBREAK_TOTAL.store(0, std::sync::atomic::Ordering::Relaxed);
}

/// Perspektiv-Logik des Denial-Tie-Breaks (Implementierungsauftrag Punkt 2):
/// `Node::points_forecast`/`opp_points_forecast` sind IMMER ego-
/// perspektivisch bezüglich `nodes[cid].state.current_player` (siehe
/// `node_from_net_outputs`/Task #28), NICHT zwingend bezüglich des an der
/// WURZEL ziehenden Spielers `root_player` -- die meisten Aktionen wechseln
/// den Zieher (`GameState::switch_player`), manche mehrstufigen Aktionen
/// (z.B. `ChooseDrawStackSlot`, siehe `moves.rs`-Kommentar "über zwei
/// Spielerentscheidungen ... ohne switch_player()") NICHT. Zwei Fälle:
///   - Kind-Zieher == `root_player` (Zug wechselt NICHT): das Kind bewertet
///     mit seinem EIGENEN `points_forecast` weiterhin die Punkte von
///     `root_player` selbst -- der gesuchte GEGNER-Wert steckt in seinem
///     `opp_points_forecast`.
///   - Kind-Zieher == `1 - root_player` (Normalfall, Zug wechselt): das Kind
///     bewertet mit seinem EIGENEN `points_forecast` bereits die Punkte
///     SEINES Ziehers, also des WURZEL-GEGNERS -- direkt verwenden;
///     `opp_points_forecast` wäre hier fälschlich wieder `root_player`s
///     eigene Punkte.
/// `None`, wenn der jeweils benötigte Wert am Kind fehlt (sollte bei
/// vorhandenem `opp_points`-Kopf nicht vorkommen -- Aufrufer-Gating in
/// `apply_denial_tiebreak_with` prüft das netzweit an der Wurzel; hier
/// trotzdem defensiv `Option` statt `unwrap`).
fn opp_points_forecast_from_root_perspective(nodes: &[Node], root_player: usize, cid: usize) -> Option<f64> {
    let child = &nodes[cid];
    let raw = if child.state.current_player == root_player {
        child.opp_points_forecast
    } else {
        child.points_forecast
    };
    raw.map(|v| v as f64)
}

/// Reiner Entscheidungskern des Denial-Tie-Breaks, OHNE Env-Var-Zugriff --
/// nimmt `eps` als Parameter statt ihn aus dem Prozess-weiten `OnceLock`-
/// Cache (`denial_tiebreak_eps()`) zu lesen (gleiches Trennungsmuster wie
/// `blended_leaf_win_prob`/`_with`), damit Tests das Fenster ohne die
/// "einmal pro Prozess gecacht"-Falle direkt durchspielen können.
///
/// Kandidatenmenge: NUR `nodes[0].children` (dieselbe Population, über die
/// bereits `gumbel_final_root_action` entscheidet) -- bewusst NICHT
/// `nodes[0].untried`: unbesuchte Kandidaten haben nie einen eigenen
/// `make_node`-Aufruf gesehen (kein `points_forecast`/`opp_points_forecast`
/// vorhanden) und teilen sich ohnehin alle denselben `v_mix`-Platzhalter
/// statt einer echten completed-Q-Schätzung (siehe `completed_q_per_
/// candidate`) -- kein "quasi-gleichwertiger Zug" im Sinne der PREREG. Ein
/// Einbezug würde IMMER den im PREREG als Fallback erlaubten Zusatz-Batch-
/// Forward erzwingen; da `baseline` (`gumbel_final_root_action`) ohnehin nie
/// aus `untried` kommt, bleibt die Tie-Break-Population konsistent zur
/// Baseline-Auswahl. KOSTEN dieser Funktion: NULL zusätzliche Netz-Forward-
/// Pässe -- jedes Wurzelkind hat seinen `points_forecast`/`opp_points_
/// forecast` bereits bei seiner eigenen `make_node`-Expansion berechnet
/// bekommen (siehe `node_from_net_outputs`), hier nur zusätzlich gelesen
/// statt (wie vorher) nach der Blattwert-Blendung verworfen.
fn apply_denial_tiebreak_with(nodes: &[Node], baseline: usize, eps: f64) -> usize {
    if eps <= 0.0 {
        return baseline;
    }
    if nodes[0].opp_points_forecast.is_none() {
        warn_missing_opp_head_for_denial_tiebreak_once();
        return baseline;
    }
    let children = &nodes[0].children;
    if children.len() <= 1 {
        note_denial_tiebreak(false);
        return baseline;
    }
    let Some(baseline_pos) = children.iter().position(|&c| c == baseline) else {
        // Sollte nie vorkommen (`gumbel_final_root_action` waehlt IMMER aus
        // `nodes[0].children`) -- defensiv trotzdem unveraendert zurueck
        // statt zu paniken.
        return baseline;
    };
    let root_player = nodes[0].state.current_player;
    let cq = completed_q_per_candidate(nodes, 0);
    let best_q = cq[baseline_pos].1;
    let mut chosen_idx = baseline_pos;
    let mut chosen_opp = opp_points_forecast_from_root_perspective(nodes, root_player, baseline);
    for (i, &cid) in children.iter().enumerate() {
        if i == baseline_pos {
            continue;
        }
        if cq[i].1 < best_q - eps {
            continue; // ausserhalb des Aequivalenzfensters
        }
        let Some(opp) = opp_points_forecast_from_root_perspective(nodes, root_player, cid) else {
            continue;
        };
        if chosen_opp.is_none_or(|b| opp < b) {
            chosen_opp = Some(opp);
            chosen_idx = i;
        }
    }
    let chosen = children[chosen_idx];
    note_denial_tiebreak(chosen != baseline);
    chosen
}

// ── PREREG_denial_tiebreak.md, Abschnitt "E3b": Denial-Tie-Break mit
// UNSICHERHEITS-Fenster -- ersetzt E3s rohe ε-Q-Differenz (dort refutiert,
// siehe ERGEBNIS oben: der Suchsieger traegt Auswahl-Bias, Fenster-Nachbarn
// mit wenig Besuchen sind real oft schlechter als ε) durch ein besuchs-
// gewichtetes Aequivalenz-Kriterium. E3 (`MOSAIC_DENIAL_TIEBREAK_EPS`)
// bleibt UNVERAENDERT bestehen (Default AUS) -- E3b ist ein ZWEITER,
// alternativer Mechanismus an derselben Stelle, keine Ablösung im Code.

/// Reines E3b-Qualifikations-Kriterium (PREREG_denial_tiebreak.md, Abschnitt
/// "E3b"), OHNE Env-/Node-Zugriff -- direkt mit synthetischen Werten testbar
/// (gleiches Trennungsmuster wie `apply_denial_tiebreak_with`/`calibrate_
/// win_prob_with`). Kandidat `a` (`n_a` Besuche, completed-Q `q_a`) gilt als
/// gleichwertig zum Sieger `b` (`n_b`, `q_b`), wenn BEIDE Bedingungen halten:
///
/// 1. Besuchs-Gate: `n_a >= min_visit_frac * n_b` -- eliminiert die im
///    Sequential Halving frueh weggehalbierten Kandidaten (vergleichbare
///    Schaetzerqualitaet wie der Sieger).
/// 2. Unsicherheits-Fenster: `q_b - q_a <= z * SE`, mit dem Zwei-Anteils-
///    Standardfehler `SE = sqrt(Q_pool*(1-Q_pool)*(1/n_a+1/n_b))`,
///    `Q_pool = (q_a*n_a + q_b*n_b)/(n_a+n_b)` (defensiv auf `[0,1]`
///    geklemmt -- completed-Q ist eine Gewinnwahrscheinlichkeit und sollte
///    dort ohnehin liegen, der Clamp schuetzt nur vor Gleitkomma-
///    Ausreissern knapp ausserhalb der Grenzen).
///
/// Randfall `n_a<=0.0 || n_b<=0.0` (Division durch 0 in `1/n_a`/`1/n_b`
/// waere undefiniert) ODER `SE<=0.0` (Q_pool exakt auf `0`/`1` geklemmt --
/// bei gueltigen `[0,1]`-Q-Werten impliziert das ohnehin schon `q_a==q_b`,
/// der Test bleibt trotzdem als explizite Absicherung stehen): qualifiziert
/// dann NUR bei exakter Q-Gleichheit (PREREG: "behandle N=0/SE=0 sauber").
///
/// `z<=0.0` ist HIER bewusst NICHT gesondert behandelt (kein Early-Return) --
/// das AUS-Verhalten des Gesamt-Features lebt in `apply_denial_tiebreak_
/// uncert_with`s eigenem Fruehausstieg (byte-identisch + keine Zaehler-
/// Buchung), diese reine Funktion bleibt fuer JEDES `z` (auch `<=0`)
/// mathematisch wohldefiniert und direkt testbar.
pub(crate) fn denial_uncert_qualifies(n_a: f64, q_a: f64, n_b: f64, q_b: f64, z: f64, min_visit_frac: f64) -> bool {
    if n_a < min_visit_frac * n_b {
        return false;
    }
    if n_a <= 0.0 || n_b <= 0.0 {
        return q_a == q_b;
    }
    let q_pool = ((q_a * n_a + q_b * n_b) / (n_a + n_b)).clamp(0.0, 1.0);
    let se_sq = q_pool * (1.0 - q_pool) * (1.0 / n_a + 1.0 / n_b);
    if se_sq <= 0.0 {
        return q_a == q_b;
    }
    q_b - q_a <= z * se_sq.sqrt()
}

/// E3b-Variante von [`apply_denial_tiebreak_with`]: ersetzt dessen rohes
/// ε-Fenster durch `denial_uncert_qualifies` (Besuchs-Gate + Unsicherheits-
/// Fenster um die completed-Q-Differenz zum Sieger). Gleiches Trennungs-
/// muster: reiner Entscheidungskern, `z`/`min_visit_frac` als Parameter statt
/// aus den Env-Var-Caches gelesen. `z<=0.0` -> sofortiger Return der
/// Basisaktion, KEIN Vergleich, KEINE Zaehler-Buchung -- byte-identisches
/// Bestandsverhalten, exakt wie `apply_denial_tiebreak_with`s `eps<=0.0`-
/// Fruehausstieg. Kandidatenmenge/opp-Kopf-Gating/Perspektiven-Logik IDENTISCH
/// zu `apply_denial_tiebreak_with` (siehe dortige Kommentare fuer die
/// Begruendung, insbesondere warum NUR `nodes[0].children`, nicht `untried`,
/// betrachtet wird). Bucht DENSELBEN prozessweiten Debug-Zaehler
/// (`note_denial_tiebreak`/`denial_tiebreak_stats`) wie der E3-Pfad -- die
/// Feuerrate ist laut PREREG Stufe 1 das Entscheidungsinstrument fuer BEIDE
/// Mechanismen, und `apply_denial_tiebreak` stellt (Abbruch bei `eps>0 &&
/// z>0`) sicher, dass zu jedem Zeitpunkt hoechstens EINER der beiden Pfade
/// aktiv ist, ein gemeinsamer Zaehler also nie Ergebnisse zweier Mechanismen
/// vermischt.
fn apply_denial_tiebreak_uncert_with(nodes: &[Node], baseline: usize, z: f64, min_visit_frac: f64) -> usize {
    if z <= 0.0 {
        return baseline;
    }
    if nodes[0].opp_points_forecast.is_none() {
        warn_missing_opp_head_for_denial_tiebreak_once();
        return baseline;
    }
    let children = &nodes[0].children;
    if children.len() <= 1 {
        note_denial_tiebreak(false);
        return baseline;
    }
    let Some(baseline_pos) = children.iter().position(|&c| c == baseline) else {
        // Siehe `apply_denial_tiebreak_with`-Kommentar: sollte nie vorkommen,
        // defensiv trotzdem unveraendert zurueck statt zu paniken.
        return baseline;
    };
    let root_player = nodes[0].state.current_player;
    let cq = completed_q_per_candidate(nodes, 0);
    let n_b = nodes[baseline].visits as f64;
    let q_b = cq[baseline_pos].1;
    let mut chosen_idx = baseline_pos;
    let mut chosen_opp = opp_points_forecast_from_root_perspective(nodes, root_player, baseline);
    for (i, &cid) in children.iter().enumerate() {
        if i == baseline_pos {
            continue;
        }
        let n_a = nodes[cid].visits as f64;
        let q_a = cq[i].1;
        if !denial_uncert_qualifies(n_a, q_a, n_b, q_b, z, min_visit_frac) {
            continue; // ausserhalb des Aequivalenzfensters oder zu wenig Besuche
        }
        let Some(opp) = opp_points_forecast_from_root_perspective(nodes, root_player, cid) else {
            continue;
        };
        if chosen_opp.is_none_or(|b| opp < b) {
            chosen_opp = Some(opp);
            chosen_idx = i;
        }
    }
    let chosen = children[chosen_idx];
    note_denial_tiebreak(chosen != baseline);
    chosen
}

/// Reine Guard-Funktion des E3/E3b-Konfigurationskonflikts (siehe
/// `apply_denial_tiebreak`), OHNE Env-Zugriff -- direkt mit synthetischen
/// `eps`/`z`-Werten testbar (`#[should_panic]`), damit der Panic-Pfad
/// geprueft werden kann, OHNE die echten, prozessweit gecachten
/// `denial_tiebreak_eps()`/`denial_uncert_z()`-OnceLocks anzufassen (die
/// duerfen in `cargo test`s gemeinsamem Testprozess NIE auf einen
/// Nicht-Default-Wert gesetzt werden, sonst wuerden alle anderen, parallel
/// laufenden Denial-Tie-Break-Tests kontaminiert).
fn assert_denial_tiebreak_config_not_conflicting(eps: f64, z: f64) {
    if eps > 0.0 && z > 0.0 {
        panic!(
            "MOSAIC_DENIAL_TIEBREAK_EPS>0 ({eps}) UND MOSAIC_DENIAL_UNCERT_Z>0 ({z}) gleichzeitig \
             gesetzt -- zwei widerspruechliche Denial-Tie-Break-Aequivalenzdefinitionen (E3: rohes \
             Q-Fenster, refutiert; E3b: besuchsgewichtetes Unsicherheitsfenster, siehe \
             evaluations/PREREG_denial_tiebreak.md). Genau einen der beiden Env-Knoepfe setzen, \
             nicht beide."
        );
    }
}

/// Env-gelesener Wrapper von [`apply_denial_tiebreak_with`]/
/// [`apply_denial_tiebreak_uncert_with`] (produktiver Aufrufer:
/// `select_final_root_child`). Liest BEIDE Denial-Tie-Break-Env-Knoepfe (E3
/// `MOSAIC_DENIAL_TIEBREAK_EPS` und E3b `MOSAIC_DENIAL_UNCERT_Z`) und bricht
/// hart ab, wenn beide gleichzeitig `>0` sind (`assert_denial_tiebreak_
/// config_not_conflicting`) -- eine stille Praeferenz fuer einen der beiden
/// Mechanismen wuerde einen Nutzer glauben lassen, er teste E3, obwohl
/// tatsaechlich E3b greift (oder umgekehrt). Sonst: `z>0` -> E3b-Pfad
/// (`apply_denial_tiebreak_uncert_with`), sonst E3-Pfad
/// (`apply_denial_tiebreak_with`, inkl. dessen `eps<=0.0`-Fruehausstieg bei
/// beiden Default-Werten).
fn apply_denial_tiebreak(nodes: &[Node], baseline: usize) -> usize {
    let eps = denial_tiebreak_eps();
    let z = denial_uncert_z();
    assert_denial_tiebreak_config_not_conflicting(eps, z);
    if z > 0.0 {
        apply_denial_tiebreak_uncert_with(nodes, baseline, z, denial_min_visit_frac())
    } else {
        apply_denial_tiebreak_with(nodes, baseline, eps)
    }
}

/// Dispatcht die finale Wurzel-Zugwahl auf `gumbel_final_root_action`
/// (Gumbel-Modus) oder `best_root_child` (PUCT), je nach `USE_GUMBEL_SEARCH`.
/// Der Denial-Tie-Break (`apply_denial_tiebreak`) wirkt NUR im Gumbel-Zweig
/// (PREREG_denial_tiebreak.md: "Wirkt bei der finalen Wurzelzug-Wahl der
/// Netz-Suche (Gumbel-Pfad)") -- der PUCT-Legacy-Zweig bleibt unangetastet.
/// Gemeinsame Stelle für ALLE Aufrufer der finalen Zugwahl (Self-Play über
/// `net_search_drafting_action`/`net_root_child_stats_and_policy`, Arena über
/// `net_search_drafting_action[_hybrid]`, GUI/Debug über
/// `net_search_with_tree[_from_nodes]`) -- eine einzige Änderungsstelle wirkt
/// dadurch überall dort, wo die tatsächlich gespielte Aktion aus dem
/// Suchergebnis bestimmt wird, OHNE `root_q`/`root_child_q`/die aufgezeich-
/// neten Policy-Targets zu berühren (die werden weiterhin unabhängig davon in
/// `net_root_child_stats_and_policy` aus `nodes`/`forest` gebaut, siehe
/// dortige Kommentare) -- exakt dasselbe Trennungsmuster wie beim τ-
/// Annealing (Commit 4c5db0e): reine Zugwahl, kein Trainingsziel-Einfluss.
fn select_final_root_child(nodes: &[Node]) -> Option<usize> {
    if USE_GUMBEL_SEARCH {
        gumbel_final_root_action(nodes).map(|baseline| {
            // PREREG_opponent_disruption_v2.md §5.2: reiner ZAEHLMODUS, VOR
            // dem Tie-Break und ohne Einfluss auf dessen Eingaben oder auf
            // den Rueckgabewert -- die gespielte Aktion bleibt exakt
            // `apply_denial_tiebreak(...)`.
            color_denial_probe(nodes, baseline);
            apply_denial_tiebreak(nodes, baseline)
        })
    } else {
        best_root_child(nodes, &nodes[0].children)
    }
}

// ── PREREG_opponent_disruption_v2.md §5.2: Stoerfenster-Zaehlmodus ─────────
//
// Beantwortet OHNE Verhaltenseingriff die Vorfrage "wie oft tritt ueberhaupt
// ein Stoerfenster auf?": eine Wurzelentscheidung, in der ein nach dem
// E3b-Kriterium gleichwertiger Kandidat dem Gegner mehr von einer AKUT
// gebrauchten Farbe wegnimmt als der Suchsieger, ohne die eigene Strafleiste
// staerker zu fuellen. Der Zaehler laeuft, der Zug bleibt der Zug.
//
// Runde 5 erreicht diese Stelle nie (`round5::applies` kurzschliesst schon in
// `net_search_drafting_action`/`net_root_child_stats_and_policy`, dort kein
// Gumbel-Baum) -- PREREG §9.6 Punkt 2, hier bewusst nicht noch einmal gegatet.

static COLOR_DENIAL_PROBE_TOTAL: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static COLOR_DENIAL_PROBE_FENSTER: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static COLOR_DENIAL_PROBE_STOERBAR: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);

/// `z`-Schwelle des Zaehlmodus, `MOSAIC_COLOR_DENIAL_PROBE_Z` -- Default
/// `0.0` = AUS = kein Zaehlen, keine Kosten. BEWUSST getrennt von
/// `MOSAIC_DENIAL_UNCERT_Z`: dieser Knopf darf den E3b-Tie-Break NICHT
/// aktivieren (der wuerde das Spielverhalten aendern und die
/// Byte-Identitaets-Zusicherung brechen).
fn color_denial_probe_z() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_COLOR_DENIAL_PROBE_Z", 0.0))
}

/// Mindest-Besuchsanteil des Zaehlmodus, `MOSAIC_COLOR_DENIAL_PROBE_MIN_VISIT_FRAC`
/// -- Default `0,5` wie beim E3b-Vorbild (`denial_min_visit_frac`).
fn color_denial_probe_min_visit_frac() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_COLOR_DENIAL_PROBE_MIN_VISIT_FRAC", 0.5))
}

/// Snapshot `(total, fenster, stoerbar)` des Zaehlmodus.
/// `total` = ausgewertete Wurzelentscheidungen (inkl. Ein-Kandidaten-Faelle,
/// gleicher Nenner-Zuschnitt wie `denial_tiebreak_stats`),
/// `fenster` = davon mit >=1 gleichwertigem Nicht-Sieger,
/// `stoerbar` = davon mit >=1 gleichwertigem Kandidaten, der mehr stoert und
/// nicht mehr Strafleiste kostet.
pub fn color_denial_probe_stats() -> (u64, u64, u64) {
    use std::sync::atomic::Ordering::Relaxed;
    (
        COLOR_DENIAL_PROBE_TOTAL.load(Relaxed),
        COLOR_DENIAL_PROBE_FENSTER.load(Relaxed),
        COLOR_DENIAL_PROBE_STOERBAR.load(Relaxed),
    )
}

/// Setzt alle drei Zaehler zurueck (Muster `reset_denial_tiebreak_stats`).
pub fn reset_color_denial_probe_stats() {
    use std::sync::atomic::Ordering::Relaxed;
    COLOR_DENIAL_PROBE_TOTAL.store(0, Relaxed);
    COLOR_DENIAL_PROBE_FENSTER.store(0, Relaxed);
    COLOR_DENIAL_PROBE_STOERBAR.store(0, Relaxed);
}

/// Reiner Zaehlkern OHNE Env-Zugriff (Trennungsmuster wie
/// `apply_denial_tiebreak_with`/`denial_uncert_qualifies`) -- direkt mit
/// synthetischen `Node`-Vektoren testbar.
///
/// KEINE Rueckgabe, KEINE Mutation an `nodes`, kein RNG-Zugriff, kein
/// Netz-Forward: alle Eingaben (Besuche, completed-Q, Wurzelzustand) liegen
/// nach dem Baumbau bereits vor. Kandidatenmenge ausschliesslich
/// `nodes[0].children` -- identisch zu E3/E3b (siehe
/// `apply_denial_tiebreak_with`-Kommentar, warum nicht `untried`).
fn color_denial_probe_with(nodes: &[Node], baseline: usize, z: f64, min_visit_frac: f64) {
    use std::sync::atomic::Ordering::Relaxed;
    if z <= 0.0 {
        return; // AUS: kein Zaehlen, keine Kosten.
    }
    COLOR_DENIAL_PROBE_TOTAL.fetch_add(1, Relaxed);
    let children = &nodes[0].children;
    if children.len() <= 1 {
        return;
    }
    let Some(baseline_pos) = children.iter().position(|&c| c == baseline) else {
        return; // defensiv, wie im Tie-Break: nie beobachtet, nie paniken.
    };
    let root = &nodes[0].state;
    let cq = completed_q_per_candidate(nodes, 0);
    let n_b = nodes[baseline].visits as f64;
    let q_b = cq[baseline_pos].1;
    let bedarf = crate::provocation::opponent_demand_acute(root, root.current_player);
    // Der Basiszug selbst: nur Stein-Zuege tragen eine Farbe/Stueckzahl. Eine
    // Nicht-Stein-Basis (Kuppelwahl o.ae.) bekommt (0,0) -- dann kann jeder
    // stoerende Stein-Kandidat sie schlagen, was sachlich richtig ist.
    let (stoer_b, floor_b) = match nodes[baseline].action.as_ref() {
        Some(Action::Stone(m)) => crate::provocation::disruption_score(root, m, &bedarf),
        _ => (0, 0),
    };
    let mut fenster = false;
    let mut stoerbar = false;
    for (i, &cid) in children.iter().enumerate() {
        if i == baseline_pos {
            continue;
        }
        if !denial_uncert_qualifies(nodes[cid].visits as f64, cq[i].1, n_b, q_b, z, min_visit_frac) {
            continue; // ausserhalb des Aequivalenzfensters oder zu wenig Besuche
        }
        fenster = true;
        let Some(Action::Stone(m)) = nodes[cid].action.as_ref() else { continue };
        let (stoer_a, floor_a) = crate::provocation::disruption_score(root, m, &bedarf);
        if stoer_a > stoer_b && floor_a <= floor_b {
            stoerbar = true;
            break; // eine qualifizierte Alternative genuegt fuer die Rate
        }
    }
    if fenster {
        COLOR_DENIAL_PROBE_FENSTER.fetch_add(1, Relaxed);
    }
    if stoerbar {
        COLOR_DENIAL_PROBE_STOERBAR.fetch_add(1, Relaxed);
    }
}

/// Env-gelesener Wrapper von [`color_denial_probe_with`] (produktiver
/// Aufrufer: `select_final_root_child`).
fn color_denial_probe(nodes: &[Node], baseline: usize) {
    let z = color_denial_probe_z();
    if z <= 0.0 {
        return; // Fruehausstieg VOR jedem weiteren Env-Lesen (Default-Kosten: ein f64-Vergleich).
    }
    color_denial_probe_with(nodes, baseline, z, color_denial_probe_min_visit_frac());
}

// ── Task #95: Debug-Trace (Value-Head-Einschätzung + granularer Gumbel-Trace) ──
//
// Beide unten definierten Strukturen fassen AUSSCHLIESSLICH bereits an anderer
// Stelle berechnete Zwischenwerte zusammen -- kein zusätzlicher Netz-Aufruf im
// Suchpfad selbst (`RootValueDebug` nutzt zwar EINEN eigenen `Net::eval`-aufruf,
// aber NUR wenn explizit angefordert, siehe `compute_root_value_debug`, und
// komplett losgelöst von `nodes`/RNG der eigentlichen Suche). Alle
// Trace-Sammelstellen in `build_gumbel_tree` sind reine Lesezugriffe auf
// bereits vorhandene lokale Werte (kein Effekt auf Auswahl/Backprop/RNG-Strom)
// -- siehe Paritätstest `gumbel_trace_collection_does_not_change_search`.

/// Root-Value-Debug-Breakdown (Anforderung 1, Task #95): rohe Value-/
/// Points-Kopf-Ausgaben + alle Blend-/Shaping-Zwischenschritte für die
/// ROOT-Position, aus Sicht des tatsächlich ziehenden Spielers (Ego). Nur
/// über `compute_root_value_debug` befüllt, ausschließlich vom Debug-Pfad
/// (`ai_debug_net_json`) angefordert.
#[derive(Clone, Debug)]
pub struct RootValueDebug {
    /// Roher `value_head`-Tanh-Output (Ego-Perspektive, VOR jeder Blend-/
    /// Shrink-/Floor-Korrektur).
    pub raw_value: f32,
    /// Roher `points_head`-Output, falls das Netz einen hat (ältere
    /// Checkpoints ohne Punktekopf → `None`).
    pub points_forecast: Option<f32>,
    /// Task #28: roher `opp_points_head`-Output, falls das Netz den neuen
    /// Gegner-Punkte-Kopf hat (`None` bei jedem Netz ohne den Kopf, siehe
    /// `net.rs::has_opp_head`).
    pub opp_points_forecast: Option<f32>,
    /// `value_to_win_prob(raw_value)` -- reine Sieg-Wahrscheinlichkeit ohne
    /// Points-Blend, OHNE Task-#30-Kalibrierung (roher Wert, siehe
    /// `win_prob_calibrated` fuer das Gegenstueck).
    pub win_prob: f64,
    /// Task #30: additives Feld, `calibrate_win_prob(win_prob)` -- der
    /// tatsaechlich in `blended_utility` (und damit in die Suche) einfließende
    /// Wert VOR dem Task-#28-Blend. Bei Default-Parametern (a=0,b=1) identisch
    /// zu `win_prob`.
    pub win_prob_calibrated: f64,
    /// `blended_leaf_win_prob` (KataGo-Blend, MIT Task-#30-Kalibrierung auf
    /// `wr`) NACH der Value-Shrinkage (Task #78, aktuell
    /// `VALUE_SHRINK_ENABLED=false` ⇒ Identität) -- exakt die Größe, die
    /// tatsächlich als Blattwert in die Suche einfließt, NUR noch ohne das
    /// Floor-Shaping-Additiv (separat ausgewiesen).
    pub blended_utility: f64,
    /// Floor-Shaping-Additiv (`FLOOR_SHAPING_WEIGHT · tanh(floor_shaping_delta)`),
    /// bereits auf Ego-Perspektive gedreht (positiv = Vorteil für den
    /// ziehenden Spieler). 0.0, wenn `FLOOR_SHAPING_WEIGHT=0` (Feature aus).
    pub floor_shift: f64,
    /// `(blended_utility + floor_shift)`, geklammert auf [0,1] -- identisch
    /// zum tatsächlichen `leaf_value[ego]` der Wurzel.
    pub final_value: f64,
}

impl RootValueDebug {
    fn to_json(&self) -> Value {
        json!({
            "raw_value": self.raw_value,
            "points_forecast": self.points_forecast,
            "opp_points_forecast": self.opp_points_forecast,
            "win_prob": self.win_prob,
            "win_prob_calibrated": self.win_prob_calibrated,
            "blended_utility": self.blended_utility,
            "floor_shift": self.floor_shift,
            "final_value": self.final_value,
        })
    }
}

/// Rechnet den Netz-Value-/Points-Blattwert für `state` (Ego-Perspektive,
/// EIN Batch=1-Forward-Pass) separat vom Suchpfad aus -- NUR für die
/// Debug-Anzeige (Anforderung 1). Liest/schreibt weder `nodes` noch den
/// RNG-Strom der Suche; `state` muss die bereits (falls
/// `DETERMINIZE_ROOT_HIDDEN_INFO`) determinisierte Wurzelposition sein
/// (`nodes[0].state`) -- KEINE zweite Determinisierung hier.
fn compute_root_value_debug(net_policy: &Net, net_value: Option<&Net>, state: &GameState) -> RootValueDebug {
    let net = net_value.unwrap_or(net_policy);
    let feats = crate::features::features_for_net(net, state);
    // Task #28: `eval_ex` statt `eval` -- liest zusaetzlich den optionalen
    // `opp_points`-Kopf (leerer Vec bei jedem Netz ohne den Kopf).
    let (_logits, value, _moon, points, opp_points, _ownership) = net.eval_ex(&feats).unwrap_or_else(|_| {
        (vec![0.0; NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new())
    });
    let raw_value = value.first().copied().unwrap_or(0.0);
    let win_prob = value_to_win_prob(&value);
    // Task #30: additiv, roher UND korrigierter Wert nebeneinander (siehe
    // `RootValueDebug::win_prob_calibrated`-Doku).
    let win_prob_calibrated = calibrate_win_prob(win_prob);
    let blended_raw = blended_leaf_win_prob(&value, &points, &opp_points);
    let blended_utility = if VALUE_SHRINK_ENABLED {
        0.5 + value_shrink_weight(state.round_number) * (blended_raw - 0.5)
    } else {
        blended_raw
    };
    let points_forecast = points.first().copied();
    let opp_points_forecast = opp_points.first().copied();
    // `floor_shaping_delta` ist absolut Spieler0-minus-Spieler1 -- auf
    // Ego-Perspektive (der an der Wurzel ziehende Spieler) drehen. Bei
    // `opp_bias!=1.0` (Eskalationsstufe E2) darf das NICHT mehr per simplem
    // Vorzeichenwechsel geschehen (own/opp sind dann nicht mehr symmetrisch
    // vertauschbar) -- `floor_shaping_delta_ego` rechnet direkt aus Sicht von
    // `state.current_player`, `opp_bias=1.0` bleibt bit-identisch zum alten
    // Drehungs-Trick (siehe `floor_shaping_delta_ego`-Kommentar).
    let opp_bias = floor_shaping_opp_bias();
    let floor_shift = if opp_bias == 1.0 {
        let floor_raw = floor_shaping_weight() * floor_shaping_delta(state).tanh();
        if state.current_player == 0 { floor_raw } else { -floor_raw }
    } else {
        floor_shaping_weight() * floor_shaping_delta_ego(state, state.current_player, opp_bias).tanh()
    };
    let final_value = (blended_utility + floor_shift).clamp(0.0, 1.0);
    RootValueDebug {
        raw_value,
        points_forecast,
        opp_points_forecast,
        win_prob,
        win_prob_calibrated,
        blended_utility,
        floor_shift,
        final_value,
    }
}

/// Ein Wurzel-Kandidat in der Gumbel-Top-m-Auswahlphase (Anforderung 2b).
#[derive(Clone, Debug)]
pub struct GumbelTraceCandidate {
    pub description: String,
    pub prior: f64,
    pub ln_prior: f64,
    pub gumbel_g: f64,
    pub score: f64,
    pub selected_top_m: bool,
}

impl GumbelTraceCandidate {
    fn to_json(&self) -> Value {
        json!({
            "description": self.description,
            "prior": self.prior,
            "ln_prior": self.ln_prior,
            "gumbel_g": self.gumbel_g,
            "score": self.score,
            "selected_top_m": self.selected_top_m,
        })
    }
}

/// Ein Kandidat innerhalb EINER Sequential-Halving-Phase (Anforderung 2c).
#[derive(Clone, Debug)]
pub struct GumbelPhaseCandidate {
    pub description: String,
    pub visits: u32,
    pub q: f64,
    pub sigma_q: f64,
    pub score: f64,
    pub eliminated: bool,
    /// PREREG_points_head_plates.md (Stufe 2): Netz-Kopf-Ausgaben AM
    /// KINDZUSTAND dieses Kandidaten (`Node::raw_value`/`points_forecast`/
    /// `opp_points_forecast`) -- der Suchlauf hat diesen Knoten an dieser
    /// Stelle bereits mindestens einmal besucht/expandiert (Sequential-
    /// Halving-Invariante: jeder `current`-Kandidat bekommt vor der Rangfolge
    /// mind. 1 Sim), reiner Lesezugriff, kein Zusatz-Netz-Aufruf. `None` nur
    /// bei wiederholt fehlgeschlagener Expansion (`apply_drafting`-Fehler,
    /// siehe `visit_candidate!`-Kommentar) oder fehlendem Kopf am Netz.
    pub raw_value: Option<f32>,
    pub points_forecast: Option<f32>,
    pub opp_points_forecast: Option<f32>,
    /// PREREG_reachability_target.md par.6 ("Ordnung gegen das Praedikat
    /// selbst"): Nachfolgezustand nach Anwenden dieses Kandidatenzugs, als
    /// Frontend-JSON (`state_to_json`, `scoring_confirmed=false` -- in der
    /// Drafting-Phase ohne Wirkung). Rein additiv: kostet nur bei
    /// `collect_trace=true` einen weiteren `state_to_json`-Aufruf je
    /// Kandidat, Self-Play/Arena rufen weiterhin immer mit `trace=None`.
    /// `None` nur bei fehlgeschlagener Expansion (siehe `raw_value`-Kommentar).
    pub successor_state_json: Option<String>,
    /// Ziehender Spieler an diesem Kindzustand (`Node::player_who_acted`) --
    /// noetig, um ein Praedikat egoseitig auf dem Nachfolgezustand
    /// auszuwerten (der Zug kann die Spielerreihenfolge wechseln).
    pub mover: Option<usize>,
}

impl GumbelPhaseCandidate {
    fn to_json(&self) -> Value {
        json!({
            "description": self.description,
            "visits": self.visits,
            "q": self.q,
            "sigma_q": self.sigma_q,
            "score": self.score,
            "eliminated": self.eliminated,
            "raw_value": self.raw_value,
            "points_forecast": self.points_forecast,
            "opp_points_forecast": self.opp_points_forecast,
            "successor_state_json": self.successor_state_json,
            "mover": self.mover,
        })
    }
}

/// Eine Sequential-Halving-Phase (Anforderung 2c).
#[derive(Clone, Debug)]
pub struct GumbelPhase {
    pub phase: u32,
    pub sims_per_survivor: u32,
    pub candidates: Vec<GumbelPhaseCandidate>,
}

impl GumbelPhase {
    fn to_json(&self) -> Value {
        json!({
            "phase": self.phase,
            "sims_per_survivor": self.sims_per_survivor,
            "candidates": self.candidates.iter().map(|c| c.to_json()).collect::<Vec<_>>(),
        })
    }
}

/// Ein Finalist der letzten Max-Visit-Menge (Anforderung 2d).
#[derive(Clone, Debug)]
pub struct GumbelFinalist {
    pub description: String,
    pub visits: u32,
    pub ln_prior: f64,
    pub sigma_q: f64,
    pub score: f64,
    /// PREREG_points_head_plates.md (Stufe 2): wie
    /// `GumbelPhaseCandidate::raw_value`/`points_forecast`/
    /// `opp_points_forecast`, hier für den bereits expandierten
    /// Wurzelkind-Knoten (`nodes[cid]`) dieses Finalisten -- reiner
    /// Lesezugriff, kein Zusatz-Netz-Aufruf.
    pub raw_value: Option<f32>,
    pub points_forecast: Option<f32>,
    pub opp_points_forecast: Option<f32>,
}

impl GumbelFinalist {
    fn to_json(&self) -> Value {
        json!({
            "description": self.description,
            "visits": self.visits,
            "ln_prior": self.ln_prior,
            "sigma_q": self.sigma_q,
            "score": self.score,
            "raw_value": self.raw_value,
            "points_forecast": self.points_forecast,
            "opp_points_forecast": self.opp_points_forecast,
        })
    }
}

/// Granularer Gumbel-Such-Trace (Task #95, Anforderung 2) -- ersetzt den
/// bisherigen Platzhalter-Log-Eintrag „GUMBEL-SUCHE (kein granularer
/// Sim-Trace)" durch eine strukturierte Aufzeichnung von Top-m-Auswahl,
/// jeder Sequential-Halving-Phase und der finalen Wurzel-Zugwahl. Nur
/// befüllt, wenn `collect_trace=true` an `build_gumbel_tree`/`build_net_tree`
/// durchgereicht wird (siehe dortige Parameter) -- Self-Play/Arena rufen
/// IMMER mit `None`, byte-identisch zum Vor-Task-#95-Verhalten (Paritätstest
/// siehe Testmodul).
#[derive(Clone, Debug, Default)]
pub struct GumbelTrace {
    pub determinize_active: bool,
    pub root_value: Option<RootValueDebug>,
    pub top_m: Vec<GumbelTraceCandidate>,
    pub phases: Vec<GumbelPhase>,
    pub finalists: Vec<GumbelFinalist>,
}

impl GumbelTrace {
    pub fn to_json(&self) -> Value {
        json!({
            "determinize_active": self.determinize_active,
            "top_m_selection": self.top_m.iter().map(|c| c.to_json()).collect::<Vec<_>>(),
            "phases": self.phases.iter().map(|p| p.to_json()).collect::<Vec<_>>(),
            "final_selection": self.finalists.iter().map(|f| f.to_json()).collect::<Vec<_>>(),
        })
    }
}

/// Gumbel-AlphaZero-Baumaufbau (siehe Modul-Kommentar "Gumbel AlphaZero" für
/// die volle Herleitung) -- Ersatz für `build_net_tree`, wenn
/// `USE_GUMBEL_SEARCH=true`. Wurzel: Gumbel-Top-m + Sequential Halving statt
/// Dirichlet-Noise + PUCT über den vollen Kandidatensatz. Tiefe≥1 (Paket 2
/// des Speed-Bündels, 2026-07-22): `gumbel_select_child` über
/// `children ∪ untried` OHNE Progressive-Widening-Cap -- die mctx-Auswahlregel
/// selbst entscheidet, ob deszendiert oder ein neuer Kandidat expandiert wird
/// (vorher PUCT-Erbe: fester Widening-Cap erzwang Expansion, bevor überhaupt
/// zwischen Kindern gewählt wurde, siehe `descend_and_backprop`).
/// `add_root_noise = false` (Arena/Produktion) schaltet die Gumbel-Samples ab
/// (alle g(a) = 0.0): Top-m und Halving ranken dann rein nach
/// `ln(prior) + σ(Q̂)` -- deterministisch, äquivalent zu mctx
/// `gumbel_scale=0`. Self-Play ruft mit `true` und behält die echte
/// Gumbel-Exploration (G1, Vollaudit 2026-07-21).
///
/// `trace` (Task #95, Anforderung 2/3): NUR wenn `Some`, wird zusätzlich ein
/// granularer Trace (Top-m-Auswahl, jede Halving-Phase, finale Zugwahl)
/// gesammelt -- ausschließlich additive Lesezugriffe auf ohnehin berechnete
/// Werte, KEINE Änderung an Auswahl/Backprop/RNG-Verbrauch (siehe
/// Paritätstest).
/// Buendelt die ERSTMALIGE Expansion ALLER `candidates.len()` Top-m-
/// Kandidaten an der Gumbel-Wurzel in EINEM `Net::eval_batch`-Aufruf (Perf-
/// Auftrag, 2026-08-02, siehe `BATCH_ROOT_EXPANSION`-Doku) statt
/// `candidates.len()` einzelner `make_node`-Netz-Evals. NUR fuer den
/// `same_net`-Fall gedacht (Aufrufer prueft das) -- diese Funktion selbst
/// geht implizit davon aus, dass EIN Netz (`net_policy`) sowohl Policy- als
/// auch Value-Quelle ist (identisch zu `make_node`s `same_net=true`-Zweig).
///
/// Baut je erfolgreich expandiertem Kandidaten einen [`Node`] (ueber
/// `node_from_net_outputs`, DIESELBE Konstruktionslogik wie der unbatchte
/// Pfad -- kein Doppelpflege-Risiko), haengt ihn an `nodes[0].children` und
/// setzt `candidate_node[ci] = Some(cid)` -- ABSICHTLICH OHNE den
/// Erstbesuch-Backprop (`nodes[cid].visits` bleibt `0`, Frisch-Knoten-
/// Default): der Aufrufer (`build_gumbel_tree`s `visit_candidate!`-Makro)
/// erkennt `visits==0` und holt den Backprop beim naechsten reguraeren
/// Besuch nach -- dadurch bleibt die `budget_used`/`extra`-Buchhaltung der
/// Sequential-Halving-Phasenschleife UNVERAENDERT (jeder Kandidat zaehlt
/// weiterhin genau EINEN Sim fuer seinen Erstbesuch, exakt wie im unbatchten
/// Pfad -- nur WANN der Netz-Eval passiert, nicht WIE VIELE Sims er kostet,
/// aendert sich).
///
/// Fehlgeschlagene `apply_drafting`-Versuche werden wie im unbatchten Pfad
/// stillschweigend uebersprungen (`candidate_node[ci]` bleibt `None`).
///
/// RNG/Determinismus: siehe `BATCH_ROOT_EXPANSION`-Doku -- in der
/// Standardkonfiguration (`SHUFFLE_STACK_PEEK_IN_SEARCH=false`,
/// `ROUND_TRANSITION_SAMPLING=false`) verbraucht `node_from_net_outputs`
/// gar kein `rng`, die Aufrufreihenfolge ist daher irrelevant; der
/// `SHUFFLE_STACK_PEEK_IN_SEARCH=true`-Fall wird an der Aufrufstelle
/// zusaetzlich ausgeschlossen (fällt auf den unbatchten Pfad zurück).
fn batched_expand_root_candidates<R: Rng + ?Sized>(
    net_policy: &Net,
    net_value: Option<&Net>,
    root_state: &GameState,
    candidates: &[(Action, f32, f64)],
    nodes: &mut Vec<Node>,
    candidate_node: &mut [Option<usize>],
    rng: &mut R,
    search_config: &SearchConfig,
) {
    let mover = root_state.current_player;
    let need_other_pass = ACTIVE_LEAF == LeafEval::Net && !MIRROR_OTHER_VAL;

    struct Pending {
        ci: usize,
        action: Action,
        prior: f32,
        child_state: GameState,
        terminal: bool,
    }
    let mut pending: Vec<Pending> = Vec::with_capacity(candidates.len());
    for (ci, (act, prior, _g)) in candidates.iter().enumerate() {
        crate::profiling::note_gamestate_clone();
        let mut g = Game { state: root_state.clone() };
        // Kein `SHUFFLE_STACK_PEEK_IN_SEARCH`-Zweig hier -- die Aufrufstelle
        // schaltet den Batch-Pfad bei aktivem Toggle komplett ab (siehe
        // Funktionskommentar), diese Funktion wird dann nie erreicht.
        if g.apply_drafting(act).is_ok() {
            let mut child_state = g.state;
            child_state.log.clear();
            let terminal = child_state.phase != Phase::Drafting;
            pending.push(Pending { ci, action: act.clone(), prior: *prior, child_state, terminal });
        }
    }
    if pending.is_empty() {
        return;
    }

    let feats: Vec<Vec<f32>> = pending
        .iter()
        .map(|p| {
            crate::profiling::timed(crate::profiling::note_features_ns, || {
                crate::features::features_for_net(net_policy, &p.child_state)
            })
        })
        .collect();
    let feats_refs: Vec<&[f32]> = feats.iter().map(|v| v.as_slice()).collect();
    let n = pending.len();
    // Task #28: `eval_batch_ex` statt `eval_batch` -- liest zusaetzlich den
    // optionalen `opp_points`-Kopf je Zeile (leer bei jedem Netz ohne den
    // Kopf), sonst BYTE-IDENTISCH.
    let outputs = crate::profiling::timed_net_eval(n, || net_policy.eval_batch_ex(&feats_refs)).unwrap_or_else(
        |_| {
            (0..n)
                .map(|_| (vec![0.0; NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new()))
                .collect()
        },
    );

    let other_outputs: Vec<Option<(Vec<f32>, Vec<f32>, Vec<f32>)>> = if need_other_pass {
        let other_feats: Vec<Vec<f32>> = pending
            .iter()
            .map(|p| {
                let mut flipped = p.child_state.clone();
                flipped.current_player = 1 - p.child_state.current_player;
                crate::features::features_for_net(net_policy, &flipped)
            })
            .collect();
        let other_feats_refs: Vec<&[f32]> = other_feats.iter().map(|v| v.as_slice()).collect();
        let other_out = crate::profiling::timed_net_eval(n, || net_policy.eval_batch_ex(&other_feats_refs))
            .unwrap_or_else(|_| {
                (0..n).map(|_| (Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new())).collect()
            });
        other_out
            .into_iter()
            .map(|(_, o_value, _, o_points, o_opp_points, _o_own)| Some((o_value, o_points, o_opp_points)))
            .collect()
    } else {
        (0..n).map(|_| None).collect()
    };

    for (idx, p) in pending.into_iter().enumerate() {
        let (logits, value, moon, points, opp_points, ownership) = outputs[idx].clone();
        let other_pass = other_outputs[idx].clone();
        let child = node_from_net_outputs(
            net_policy, net_value, p.child_state, Some(0), Some(root_state), Some(p.action), p.prior, mover,
            p.terminal, logits, value, moon, points, opp_points, ownership, other_pass, rng,
            search_config,
        );
        let cid = nodes.len();
        nodes.push(child);
        nodes[0].children.push(cid);
        candidate_node[p.ci] = Some(cid);
        // BEWUSST kein Backprop hier -- siehe Funktionskommentar
        // (`visits==0` bleibt der Marker fuer "expandiert, aber Erstbesuch
        // noch nicht gezaehlt", nachgeholt vom `visit_candidate!`-Makro).
    }
}

fn build_gumbel_tree<R: Rng + ?Sized>(
    net_policy: &Net,
    net_value: Option<&Net>,
    state: &GameState,
    sims: u32,
    add_root_noise: bool,
    rng: &mut R,
    trace: Option<&mut GumbelTrace>,
    search_config: &SearchConfig,
) -> Vec<Node> {
    build_gumbel_tree_inner(
        net_policy, net_value, state, sims, add_root_noise, rng, trace, BATCH_ROOT_EXPANSION, search_config,
    )
}

/// Eigentliche Implementierung von [`build_gumbel_tree`], mit
/// `batch_root_expansion` als LAUFZEIT-Parameter statt der globalen
/// `BATCH_ROOT_EXPANSION`-Konstante (Perf-Auftrag, 2026-08-02) -- einziger
/// Zweck: der Paritaetstest
/// `batched_root_expansion_matches_sequential_within_tolerance` kann so
/// BEIDE Pfade (batched/unbatcht) mit IDENTISCHEM Seed direkt gegeneinander
/// vergleichen, ohne die Konstante zur Testlaufzeit umschalten zu muessen
/// (waere bei einem `const` ohnehin nicht moeglich). `build_gumbel_tree`
/// selbst bleibt die STABILE Aufrufstellen-Signatur -- reicht nur
/// `BATCH_ROOT_EXPANSION`s aktuellen (Default `false`) Wert durch.
/// `search_config` (PREREG_agent_encapsulation.md par.4 Punkt 4, Pilot-
/// Migration): einzige Konsument-Stelle ist `gumbel_select_child` ueber
/// `descend_and_backprop`, siehe dort.
fn build_gumbel_tree_inner<R: Rng + ?Sized>(
    net_policy: &Net,
    net_value: Option<&Net>,
    state: &GameState,
    sims: u32,
    add_root_noise: bool,
    rng: &mut R,
    mut trace: Option<&mut GumbelTrace>,
    batch_root_expansion: bool,
    search_config: &SearchConfig,
) -> Vec<Node> {
    let mut root_state = state.clone();
    root_state.log.clear();
    if DETERMINIZE_ROOT_HIDDEN_INFO {
        determinize_hidden_information(&mut root_state, rng);
    }
    let root_player = root_state.current_player;
    let mut nodes =
        vec![make_node(net_policy, net_value, root_state, None, None, None, 0.0, root_player, rng, search_config)];

    if let Some(t) = trace.as_deref_mut() {
        t.determinize_active = DETERMINIZE_ROOT_HIDDEN_INFO;
        t.root_value = Some(compute_root_value_debug(net_policy, net_value, &nodes[0].state));
    }

    // Eine einzelne Tiefe-≥1-Deszension + Backprop, beginnend bei einem
    // bereits existierenden Knoten (typischerweise ein Wurzelkind). Paket 2
    // (2026-07-22): KEIN Progressive-Widening-Cap/Forced-Expansion mehr (PUCT-
    // Erbe, entfernt) -- `gumbel_select_child` wählt bei jedem Schritt über
    // `children ∪ untried`; fällt die Wahl auf einen unbesuchten Kandidaten,
    // wird GENAU DIESER on demand expandiert (statt immer `untried[0]`), sonst
    // wird zum gewählten bestehenden Kind weiter deszendiert. Der PUCT-Legacy-
    // Pfad (`build_net_tree`s eigene Sim-Schleife, `USE_GUMBEL_SEARCH=false`)
    // behält seinen eigenen Widening-Cap unverändert -- diese Funktion wird
    // von dort nie aufgerufen. Kein granularer Sim-Trace (siehe
    // `build_net_tree`-Dispatch-Kommentar).
    fn descend_and_backprop<R: Rng + ?Sized>(
        net_policy: &Net,
        net_value: Option<&Net>,
        nodes: &mut Vec<Node>,
        start_nid: usize,
        rng: &mut R,
        search_config: &SearchConfig,
    ) {
        let mut nid = start_nid;
        let mut expansion_failed = false;
        loop {
            if nodes[nid].terminal {
                break;
            }
            if nodes[nid].children.is_empty() && nodes[nid].untried.is_empty() {
                break; // defensiv: sollte an einem Nicht-Terminal-Knoten nie vorkommen
            }
            let n_children = nodes[nid].children.len();
            let idx = gumbel_select_child(nodes, nid, search_config);
            if idx < n_children {
                nid = nodes[nid].children[idx];
                continue;
            }
            // Auswahl faellt auf einen unbesuchten Kandidaten -- GENAU DIESEN
            // on demand expandieren (kein Zwang mehr auf `untried[0]`).
            let untried_idx = idx - n_children;
            let (act, prior) = nodes[nid].untried.remove(untried_idx);
            let mover = nodes[nid].state.current_player;
            crate::profiling::note_gamestate_clone();
            let mut g = Game { state: nodes[nid].state.clone() };
            if SHUFFLE_STACK_PEEK_IN_SEARCH && act == Action::DrawStackPeek {
                g.state.dome_tile_pool.shuffle(rng);
            }
            if g.apply_drafting(&act).is_ok() {
                let mut child_state = g.state;
                child_state.log.clear();
                let child = make_node(
                    net_policy, net_value, child_state, Some(nid), Some(&nodes[nid].state), Some(act), prior, mover, rng,
                    search_config,
                );
                let cid = nodes.len();
                nodes.push(child);
                nodes[nid].children.push(cid);
                nid = cid;
            } else {
                expansion_failed = true;
            }
            break;
        }
        if expansion_failed {
            return;
        }
        backprop_path(nodes, nid);
    }

    let n_root = nodes[0].untried.len();
    if n_root == 0 {
        return nodes; // Wurzel terminal/keine legalen Züge -- nichts zu tun.
    }

    // Gumbel-Top-m an der Wurzel (§1 des Plans): je Kandidat einen Gumbel-
    // Wert ziehen, Score = g(a) + ln(prior(a)), Top m' behalten. `g(a)`
    // wird für die spätere Halbierungs-Rangfolge (§2) aufbewahrt (NICHT neu
    // gezogen).
    let m_prime = gumbel_top_m_for_budget(sims).min(n_root);
    let mut scored: Vec<(f64, f64, usize)> = nodes[0]
        .untried
        .iter()
        .enumerate()
        .map(|(i, &(_, p))| {
            // g(a) = 0 im deterministischen Modus (siehe Funktionskommentar).
            let g = if add_root_noise { sample_gumbel(rng) } else { 0.0 };
            (g + (p as f64).max(1e-9).ln(), g, i)
        })
        .collect();
    scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));

    // Anforderung 2b: ALLE legalen Wurzelkandidaten (nicht nur die Top-m) mit
    // prior/ln(prior)/Gumbel-g/Score + Top-16-Kennzeichnung -- muss VOR dem
    // Entfernen der gezogenen Einträge aus `nodes[0].untried` passieren
    // (`scored` referenziert deren Indizes).
    if let Some(t) = trace.as_deref_mut() {
        for (rank, &(score, g, idx)) in scored.iter().enumerate() {
            let (act, prior) = &nodes[0].untried[idx];
            let description = label_search_move(&SearchMove::Draft(act.clone()), Some(&nodes[0].state)).1;
            t.top_m.push(GumbelTraceCandidate {
                description,
                prior: *prior as f64,
                ln_prior: (*prior as f64).max(1e-9).ln(),
                gumbel_g: g,
                score,
                selected_top_m: rank < m_prime,
            });
        }
    }

    let mut chosen: Vec<(usize, f64)> = scored.iter().take(m_prime).map(|&(_, g, i)| (i, g)).collect();
    // Absteigend nach urspruenglichem Untried-Index entfernen, damit sich
    // die Indizes der VERBLEIBENDEN (nicht gezogenen) Einträge beim
    // Herausnehmen nicht verschieben.
    chosen.sort_by(|a, b| b.0.cmp(&a.0));
    let candidates: Vec<(Action, f32, f64)> = chosen
        .into_iter()
        .map(|(i, g)| {
            let (act, prior) = nodes[0].untried.remove(i);
            (act, prior, g)
        })
        .collect();
    // `nodes[0].untried` enthält jetzt nur noch die NICHT gezogenen
    // Kandidaten -- bleibt für `improved_policy`/das spätere Policy-Ziel
    // (§5, Phase 4) korrekt als "N(a)=0"-Menge erhalten.

    let mut candidate_node: Vec<Option<usize>> = vec![None; candidates.len()];
    let mut current: Vec<usize> = (0..candidates.len()).collect();

    // Perf-Auftrag (2026-08-02): gebuendelte Erstexpansion ALLER Kandidaten
    // in EINEM Netz-Batch-Aufruf statt `candidates.len()` einzelner Evals,
    // siehe `BATCH_ROOT_EXPANSION`-Doku. NUR wenn (a) der Toggle aktiv ist,
    // (b) mehr als 1 Kandidat da ist (bei genau 1 gibt's nichts zu
    // buendeln, der `candidates.len()<=1`-Zweig unten bleibt unberuehrt),
    // (c) Policy- und Value-Netz IDENTISCH sind (Hybrid-Pfad, Task #88,
    // faellt weiterhin auf den unbatchten Pfad zurueck -- ausserhalb des
    // Scopes dieses Auftrags) und (d) `SHUFFLE_STACK_PEEK_IN_SEARCH` AUS
    // ist (sonst wuerde die geaenderte Kandidaten-Reihenfolge den
    // RNG-Verbrauch verschieben, siehe `BATCH_ROOT_EXPANSION`-Doku).
    let same_net_for_batching = net_value.is_none_or(|v| std::ptr::eq(v, net_policy));
    if batch_root_expansion && candidates.len() > 1 && same_net_for_batching && !SHUFFLE_STACK_PEEK_IN_SEARCH {
        let root_state = nodes[0].state.clone();
        batched_expand_root_candidates(
            net_policy, net_value, &root_state, &candidates, &mut nodes, &mut candidate_node, rng,
            search_config,
        );
    }

    // Expandiert (falls nötig) und simuliert EINEN weiteren Besuch für
    // Kandidat `ci` (Index in `candidates`/`candidate_node`).
    macro_rules! visit_candidate {
        ($ci:expr) => {{
            let ci = $ci;
            match candidate_node[ci] {
                Some(cid) if nodes[cid].visits > 0 => {
                    descend_and_backprop(net_policy, net_value, &mut nodes, cid, rng, search_config)
                }
                Some(cid) => {
                    // Perf-Auftrag (2026-08-02): per `batched_expand_root_candidates`
                    // bereits per Batch-Netz-Eval expandiert (Node existiert,
                    // `leaf_value` bereits berechnet), aber NOCH NICHT als
                    // Besuch gezaehlt (`visits==0`, Frisch-Knoten-Default) --
                    // hier NUR den Erstbesuch-Backprop nachholen, KEIN
                    // zweiter Netz-Eval (identische Backprop-Logik wie im
                    // `None`-Zweig unten, ohne die dortige vorangehende
                    // Netz-/Expansionsarbeit, die schon erledigt ist).
                    backprop_path(&mut nodes, cid);
                }
                None => {
                    let (act, prior, _g) = candidates[ci].clone();
                    let mover = nodes[0].state.current_player;
                    crate::profiling::note_gamestate_clone();
                    let mut g = Game { state: nodes[0].state.clone() };
                    if SHUFFLE_STACK_PEEK_IN_SEARCH && act == Action::DrawStackPeek {
                        g.state.dome_tile_pool.shuffle(rng);
                    }
                    if g.apply_drafting(&act).is_ok() {
                        let mut child_state = g.state;
                        child_state.log.clear();
                        let child = make_node(
                            net_policy, net_value, child_state, Some(0), Some(&nodes[0].state), Some(act), prior, mover, rng,
                            search_config,
                        );
                        let cid = nodes.len();
                        nodes.push(child);
                        nodes[0].children.push(cid);
                        candidate_node[ci] = Some(cid);
                        backprop_path(&mut nodes, cid);
                    }
                    // Fehlgeschlagenes apply_drafting: `candidate_node[ci]`
                    // bleibt `None` -- der Kandidat faellt bei der naechsten
                    // Rangfolge automatisch raus (Q=0-Fallback unten trifft
                    // nie einen ECHTEN Kandidaten, da jeder in `current`
                    // vor der ersten Rangfolge mind. 1 Sim bekommen hat --
                    // ausser bei wiederholtem Fehlschlag, dann bleibt er
                    // einfach auf Q=0 stehen, kein Panik/Sonderfall noetig).
                }
            }
        }};
    }

    if candidates.len() <= 1 {
        for _ in 0..sims {
            visit_candidate!(0);
        }
    } else {
        let m_actual = candidates.len();
        let num_phases = (m_actual as f64).log2().ceil().max(1.0) as u32;
        // G2 (Vollaudit 2026-07-21): das Restbudget wird wie in mctx durch
        // die VERBLEIBENDE Phasenzahl geteilt (Laufvariable, pro Halbierung
        // dekrementiert) -- die frühere Division durch die feste Anfangs-
        // Phasenzahl unterbudgetierte die frühen Phasen und kippte den Rest
        // per Tail-Loop nur auf die Finalisten.
        let mut remaining_phases = num_phases;
        let mut budget_used: u32 = 0;
        let mut phase_num: u32 = 0;
        while current.len() > 1 && budget_used < sims {
            phase_num += 1;
            let remaining_slots = (remaining_phases as usize) * current.len();
            // Invariante "jeder in current bekommt mind. 1 Sim je Phase"
            // (extra >= 1) gilt nur für sims >= m -- bei kleinerem Budget
            // bricht `budget_used >= sims` die Phase vorzeitig ab und
            // unbesuchte Kandidaten bleiben auf dem Q=0-Fallback.
            let extra = (((sims - budget_used) as usize / remaining_slots.max(1)).max(1)) as u32;
            for &ci in &current.clone() {
                for _ in 0..extra {
                    if budget_used >= sims {
                        break;
                    }
                    visit_candidate!(ci);
                    budget_used += 1;
                }
            }
            // Rangfolge: g(a) + ln(prior(a)) + σ(Q̂(a)) -- Q̂ ist der
            // empirische Mittelwert des zugehörigen Wurzelkindes (inzwischen
            // mind. 1x besucht, siehe `extra = max(1, ...)` oben).
            let max_n = current
                .iter()
                .filter_map(|&ci| candidate_node[ci].map(|cid| nodes[cid].visits))
                .max()
                .unwrap_or(0);
            current.sort_by(|&a, &b| {
                let score = |ci: usize| -> f64 {
                    let (_, prior, g) = candidates[ci];
                    let q = match candidate_node[ci] {
                        Some(cid) if nodes[cid].visits > 0 => nodes[cid].value / nodes[cid].visits as f64,
                        _ => 0.0,
                    };
                    g + (prior as f64).max(1e-9).ln() + gumbel_sigma(q, max_n)
                };
                score(b).partial_cmp(&score(a)).unwrap_or(std::cmp::Ordering::Equal)
            });
            let keep = (current.len() / 2).max(2);

            // Anforderung 2c: Trace-Eintrag für DIESE Phase -- `current` ist
            // hier bereits absteigend nach Score sortiert (siehe `sort_by`
            // oben), `rank >= keep` markiert exakt die Kandidaten, die
            // gleich per `truncate` eliminiert werden. Reine Lesezugriffe auf
            // bereits vorhandene Werte, kein Effekt auf `current` selbst.
            if let Some(t) = trace.as_deref_mut() {
                let mut phase_candidates = Vec::with_capacity(current.len());
                for (rank, &ci) in current.iter().enumerate() {
                    let (act, prior, g) = &candidates[ci];
                    let (visits, q) = match candidate_node[ci] {
                        Some(cid) if nodes[cid].visits > 0 => {
                            (nodes[cid].visits, nodes[cid].value / nodes[cid].visits as f64)
                        }
                        Some(cid) => (nodes[cid].visits, 0.0),
                        None => (0, 0.0),
                    };
                    let sigma_q = gumbel_sigma(q, max_n);
                    let score = g + (*prior as f64).max(1e-9).ln() + sigma_q;
                    let description =
                        label_search_move(&SearchMove::Draft(act.clone()), Some(&nodes[0].state)).1;
                    // PREREG_points_head_plates.md (Stufe 2): Netz-Kopf-
                    // Ausgaben am bereits expandierten Kindzustand -- `None`
                    // nur bei wiederholt fehlgeschlagener Expansion (siehe
                    // `GumbelPhaseCandidate::raw_value`-Kommentar).
                    let (raw_value, points_forecast, opp_points_forecast, successor_state_json, mover) =
                        match candidate_node[ci] {
                            Some(cid) => (
                                nodes[cid].raw_value,
                                nodes[cid].points_forecast,
                                nodes[cid].opp_points_forecast,
                                Some(crate::serialize::state_to_json(&nodes[cid].state, false).to_string()),
                                Some(nodes[cid].player_who_acted),
                            ),
                            None => (None, None, None, None, None),
                        };
                    phase_candidates.push(GumbelPhaseCandidate {
                        description,
                        visits,
                        q,
                        sigma_q,
                        score,
                        eliminated: rank >= keep,
                        raw_value,
                        points_forecast,
                        opp_points_forecast,
                        successor_state_json,
                        mover,
                    });
                }
                t.phases.push(GumbelPhase { phase: phase_num, sims_per_survivor: extra, candidates: phase_candidates });
            }

            current.truncate(keep);
            remaining_phases = remaining_phases.saturating_sub(1).max(1);
        }
        // Restbudget (Rundungsreste) auf die verbliebenen Kandidaten verteilen.
        while budget_used < sims {
            for &ci in &current.clone() {
                if budget_used >= sims {
                    break;
                }
                visit_candidate!(ci);
                budget_used += 1;
            }
        }
    }

    // Anforderung 2d: finale Zugwahl -- die Max-Visit-Menge (Sequential-
    // Halving-Überlebende) mit `ln(prior)+σ(Q)` je Finalist, exakt dieselbe
    // Menge/Formel wie `gumbel_final_root_action` (dort erneut, aber
    // unabhängig berechnet -- reiner Lesezugriff auf die fertigen `nodes`,
    // kein Effekt auf das Ergebnis).
    if let Some(t) = trace.as_deref_mut() {
        let children = &nodes[0].children;
        if !children.is_empty() {
            let max_n = children.iter().map(|&c| nodes[c].visits).max().unwrap_or(0);
            for &cid in children {
                if nodes[cid].visits != max_n {
                    continue;
                }
                let description = log_label(&nodes, cid);
                let ln_prior = (nodes[cid].prior as f64).max(1e-9).ln();
                let q = if nodes[cid].visits > 0 { nodes[cid].value / nodes[cid].visits as f64 } else { 0.0 };
                let sigma_q = gumbel_sigma(q, max_n);
                t.finalists.push(GumbelFinalist {
                    description,
                    visits: nodes[cid].visits,
                    ln_prior,
                    sigma_q,
                    score: ln_prior + sigma_q,
                    // PREREG_points_head_plates.md (Stufe 2): reiner
                    // Lesezugriff auf den bereits expandierten Knoten.
                    raw_value: nodes[cid].raw_value,
                    points_forecast: nodes[cid].points_forecast,
                    opp_points_forecast: nodes[cid].opp_points_forecast,
                });
            }
        }
    }

    nodes
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

/// Baut den PUCT-Suchbaum. `add_root_noise` aktiviert Dirichlet-Wurzel-Noise.
/// Mit `log = Some(..)` wird jede Simulation (Selection/Expansion/Eval/Backprop)
/// als Text protokolliert (für den Server-Debug-Log, analog `mcts::build_tree`).
/// Dispatcht komplett auf `build_gumbel_tree`, wenn `USE_GUMBEL_SEARCH` --
/// `log` wird in diesem Fall ignoriert (der textuelle Platzhalter-Eintrag
/// bleibt für Rückwärtskompatibilität, siehe `net_search_log_header`-
/// Konsumenten). `trace` (Task #95, Anforderung 2/3): NUR wenn `Some`, wird
/// zusätzlich der granulare Gumbel-Trace gesammelt (`build_gumbel_tree`) --
/// bei `USE_GUMBEL_SEARCH=false` (PUCT-Legacy-Pfad) bleibt `trace` ungenutzt,
/// PUCT hat keinen strukturierten Trace (nur den bestehenden Text-`log`).
/// ALLE Produktions-Aufrufstellen (Self-Play/Arena) übergeben `None` --
/// byte-identisch zum Vor-Task-#95-Verhalten. `search_config`
/// (PREREG_agent_encapsulation.md par.4 Punkt 4): nur im Gumbel-Pfad
/// wirksam (`gumbel_select_child`) -- der PUCT-Legacy-Pfad unten liest ihn
/// gar nicht, `best_puct` kennt keine Implicit-Minimax-Beimischung.
fn build_net_tree<R: Rng + ?Sized>(
    net_policy: &Net,
    net_value: Option<&Net>,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    rng: &mut R,
    mut log: Option<&mut Vec<String>>,
    trace: Option<&mut GumbelTrace>,
    search_config: &SearchConfig,
) -> Vec<Node> {
    if USE_GUMBEL_SEARCH {
        if let Some(l) = log.as_deref_mut() {
            l.push("  GUMBEL-SUCHE (kein granularer Text-Sim-Trace -- strukturierter Trace siehe `gumbel_trace`-Feld, falls angefordert)".to_string());
        }
        return build_gumbel_tree(net_policy, net_value, state, sims, add_root_noise, rng, trace, search_config);
    }
    let names = [state.players[0].name.as_str(), state.players[1].name.as_str()];
    let mut root_state = state.clone();
    root_state.log.clear();
    if DETERMINIZE_ROOT_HIDDEN_INFO {
        determinize_hidden_information(&mut root_state, rng);
    }
    let root_player = root_state.current_player;
    let mut nodes =
        vec![make_node(net_policy, net_value, root_state, None, None, None, 0.0, root_player, rng, search_config)];

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
        // Fund 5 (externer Hinweis, 2026-07-20): ein fehlgeschlagenes
        // `apply_drafting` verwarf den Kandidaten still und liess `nid` auf
        // dem PARENT stehen -- die anschliessende Eval/Backprop-Sektion
        // backprop'te dann fälschlich noch einmal den Parent-eigenen,
        // bereits bekannten Blattwert (verzerrte Besuchszahlen ohne echten
        // Informationsgewinn). Fix: diese Sim sauber überspringen (kein
        // Eval/Backprop), statt den Parent nochmal zu zählen.
        let mut expansion_failed = false;
        loop {
            if nodes[nid].terminal {
                logln!("  SELECT #{nid} [{}] terminal", log_label(&nodes, nid));
                break;
            }
            // Progressive Widening ÜBER dem POLICY_MASS_CUTOFF-Präfix (externer
            // Bugfix-Hinweis, 2026-07-20): `untried` ist bereits beim Erzeugen des
            // Knotens auf den Cutoff-Präfix gekappt (siehe `build_untried_actions`,
            // schließt den Long Tail dauerhaft aus -- das bleibt), ABER ohne
            // zusätzliche Bremse hier würde ein Knoten mit dutzenden Kandidaten
            // (Runde 1, ~49% Top-1-Masse) seinen KOMPLETTEN Präfix erst voll
            // ausrollen (ein Kind pro Sim), bevor PUCT überhaupt einmal zwischen
            // ihnen differenzieren kann -- bei 150 Sims faktisch Breitensuche mit
            // Tiefe ~1-2 statt echter Suche. Derselbe `MAX_ACTIONS + WIDEN_FACTOR·
            // √N`-Wachstumscap wie `crate::mcts` (Heuristik-Suche) angewendet,
            // NUR auf den bereits gekappten Präfix -- der Long Tail bleibt
            // dauerhaft ausgeschlossen, aber selbst die guten Kandidaten kommen
            // erst nach und nach ins Spiel, sodass PUCT früh differenzieren kann.
            let widen_allowed = crate::mcts::MAX_ACTIONS
                + (crate::mcts::WIDEN_FACTOR * (nodes[nid].visits as f64).sqrt()) as usize;
            if !nodes[nid].untried.is_empty() && nodes[nid].children.len() < widen_allowed {
                let (act, prior) = nodes[nid].untried.remove(0); // höchster Prior zuerst
                let mover = nodes[nid].state.current_player;
                crate::profiling::note_gamestate_clone();
                let mut g = Game { state: nodes[nid].state.clone() };
                // Verdeckte-Information-Fix (externer Hinweis, Fund 6,
                // 2026-07-20): `execute_draw_stack_peek` (aufgerufen via
                // `apply_drafting` bei `DrawStackPeek`) liest sonst
                // `dome_tile_pool.remove(0)` -- die ECHTE, im realen Spiel
                // eigentlich verdeckte oberste Platte. Dieselbe
                // Determinisierung wie `round_transition_deep::
                // simulate_one_round` (mischt den Restpool einmalig beim
                // Runden-Eintritt): hier einmalig VOR jedem simulierten Peek,
                // da genau in diesem Moment eine neue verdeckte Information
                // aufgedeckt würde. `dome_tile_pool` enthält an dieser Stelle
                // ohnehin nur noch die ungezogenen (= wirklich verdeckten)
                // Platten -- volles Mischen ist daher exakt richtig, keine
                // Sonderbehandlung für bereits aufgedeckte Platten nötig.
                if SHUFFLE_STACK_PEEK_IN_SEARCH && act == Action::DrawStackPeek {
                    g.state.dome_tile_pool.shuffle(rng);
                }
                if g.apply_drafting(&act).is_ok() {
                    let mut child_state = g.state;
                    child_state.log.clear();
                    let terminal = child_state.phase != Phase::Drafting;
                    let child = make_node(
                        net_policy,
                        net_value,
                        child_state,
                        Some(nid),
                        Some(&nodes[nid].state),
                        Some(act.clone()),
                        prior,
                        mover,
                        rng,
                        search_config,
                    );
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
                } else {
                    expansion_failed = true;
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

        if expansion_failed {
            logln!("  SKIP   Sim {} (apply_drafting fehlgeschlagen, kein Backprop)", sim + 1);
            continue;
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

    nodes
}

/// Beste Drafting-Aktion per Netz-PUCT (meistbesuchtes Wurzelkind). None außerhalb
/// der Drafting-Phase. `add_root_noise` nur im Self-Play aktivieren.
/// `search_config` (PREREG_agent_encapsulation.md par.3/par.4): pro-Seite-
/// Suchkonfiguration (Welle 1: nur `implicit_minimax_alpha`), vom Aufrufer
/// (typischerweise `self_play::NetArenaAgent`) durchgereicht.
pub fn net_search_drafting_action<R: Rng + ?Sized>(
    net: &Net,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    rng: &mut R,
    search_config: &SearchConfig,
) -> Option<Action> {
    if state.phase != Phase::Drafting {
        return None;
    }
    // Runde 5: exakte Alpha-Beta-Wahl statt Netz-PUCT -- die BLATTBEWERTUNG
    // dort ist exakt (optimales Tiling + Endwertung des erreichten Bretts),
    // was das Netz nur schaetzen kann. Dass das die bessere Wahl IST, war nie
    // gegatet: siehe `round5::net_solver_enabled` fuer den Knopf und
    // `PREREG_chance_nodes.md` Teil E fuer die offene Gegenprobe.
    if crate::round5::applies(state) && crate::round5::net_solver_enabled() {
        return crate::round5::choose_action(state);
    }
    // PREREG_ismcts_determinizations.md: Getter statt Konstante (siehe
    // `num_determinizations`-Doku) -- der `<= 1`-Kurzschluss bleibt exakt
    // erhalten, `k=1` (Default) ist weiterhin byte-identisch.
    let k = num_determinizations();
    if k <= 1 {
        let nodes = build_net_tree(net, None, state, sims, c_puct, add_root_noise, rng, None, None, search_config);
        let best = select_final_root_child(&nodes)?;
        return nodes[best].action.clone();
    }
    // ISMCTS-Mehrfach-Determinisierung (Task #65): finale Zugwahl = argmax
    // der über die Welten GEMITTELTEN completed-Q-Politik (siehe
    // `average_completed_q_policy`-Kommentar), nicht mehr
    // `select_final_root_child` auf einem Einzelbaum -- letzteres hätte
    // keinen sinnvollen "einen" Baum mehr, über den es entscheiden könnte.
    let forest = build_determinized_forest(net, None, state, sims, c_puct, add_root_noise, k, rng, search_config);
    average_completed_q_policy(&forest)
        .into_iter()
        .max_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal))
        .map(|(a, _)| a)
}

/// Task #88 (Hybrid-Suche, kausaler Kopf-Test): wie [`net_search_drafting_action`],
/// aber Priors/Moon-Order kommen von `net_policy`, Blattwert (Value+Points)
/// von `net_value` -- zwei UNTERSCHIEDLICHE Netze, um zu isolieren, ob die
/// Arena-Stärke eines Kandidaten aus dem Policy- oder dem Value-Kopf kommt
/// (siehe `make_node`-Kommentar für die Verdrahtung). `net_policy`/`net_value`
/// DÜRFEN dieselbe Referenz sein -- dann ist das Ergebnis BYTE-IDENTISCH zu
/// `net_search_drafting_action(net_policy, ...)` (Paritätstest siehe
/// Testmodul: `hybrid_search_with_equal_nets_matches_plain_search`). Nur für
/// die diagnostische Arena gedacht (`self_play::run_net_vs_net_arena_hybrid`),
/// KEIN Self-Play-/Trainingspfad.
pub fn net_search_drafting_action_hybrid<R: Rng + ?Sized>(
    net_policy: &Net,
    net_value: &Net,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    rng: &mut R,
    search_config: &SearchConfig,
) -> Option<Action> {
    if state.phase != Phase::Drafting {
        return None;
    }
    if crate::round5::applies(state) && crate::round5::net_solver_enabled() {
        return crate::round5::choose_action(state);
    }
    let k = num_determinizations();
    if k <= 1 {
        let nodes = build_net_tree(
            net_policy, Some(net_value), state, sims, c_puct, add_root_noise, rng, None, None, search_config,
        );
        let best = select_final_root_child(&nodes)?;
        return nodes[best].action.clone();
    }
    let forest = build_determinized_forest(
        net_policy,
        Some(net_value),
        state,
        sims,
        c_puct,
        add_root_noise,
        k,
        rng,
        search_config,
    );
    average_completed_q_policy(&forest)
        .into_iter()
        .max_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal))
        .map(|(a, _)| a)
}

/// Wurzelkind-Statistik `(Action, Besuche, Q)` — für Self-Play-Policy-Targets.
pub fn net_root_child_stats<R: Rng + ?Sized>(
    net: &Net,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    rng: &mut R,
    search_config: &SearchConfig,
) -> Vec<(Action, u32, f64)> {
    if state.phase != Phase::Drafting {
        return Vec::new();
    }
    // Runde 5: siehe net_search_drafting_action. Einzelner Eintrag mit
    // Gewicht 1.0 (statt leer) macht `net_drafting_policy`s Zufalls-
    // Fallback (bei leerer Stats-Liste) nicht faelschlich fuer die
    // Aktionswahl zustaendig.
    if crate::round5::applies(state) && crate::round5::net_solver_enabled() {
        return crate::round5::choose_action(state)
            .into_iter()
            .map(|a| (a, 1, 1.0))
            .collect();
    }
    // Bewusst NICHT auf NUM_DETERMINIZATIONS umgestellt -- diese Funktion
    // dient nur der günstigen Stufe-3-Rollout-Kandidaten-Vorauswahl
    // (`self_play::alphabeta_choose_action`s Shortlisting), nicht einer der
    // drei in Task #65 benannten Haupt-Sucheinstiege (Arena/Self-Play-Ziel/
    // Debug-UI) -- bleibt unverändert Einzelwelt.
    let nodes = build_net_tree(net, None, state, sims, c_puct, add_root_noise, rng, None, None, search_config);
    root_child_stats_from_nodes(&nodes)
}

/// Wie [`net_root_child_stats`], liefert ZUSÄTZLICH Gumbels completed-Q-
/// Policy-Ziel (`improved_policy` an der Wurzel, §4 des Gumbel-Plans) für
/// die Self-Play-Aufzeichnung — EIN Baum-Aufbau statt zwei getrennte
/// (`build_net_tree` ist die teure Suche, hier nicht doppelt bezahlt).
/// Rückgabe: (rohe Stats für Zugwahl/Shortlisting, unverändert), (Aktion,
/// completed-Q-Wahrscheinlichkeit) je Kandidat für den Trainings-Policy-
/// Vektor — deckt `children ∪ untried` ab, d.h. ALLE Wurzelaktionen, nicht
/// nur die tatsächlich durchsuchten (unbesuchte bekommen `v_mix` statt
/// Null-Besuch, siehe `completed_q_per_candidate`). Die tatsächlich
/// GESPIELTE Aktion bleibt weiterhin besuchsbasiert (Sequential-Halving-
/// Ergebnis) — nur das aufgezeichnete Trainingsziel ändert sich, siehe
/// `self_play::net_drafting_policy`.
///
/// DRITTES Rückgabeelement (v19-Vorbereitung, Root-Q-Logging für das
/// geplante Misch-Value-Target-Experiment λ·z+(1−λ)·q_root, Recherche Fund 1):
/// der Wurzel-Q-Wert der Suche selbst, aus Sicht des ziehenden Spielers
/// (`state.current_player`), auf DERSELBEN [0,1]-Gewinnwahrscheinlichkeits-
/// Skala wie `mcts_q`/`win_pct` überall sonst (`value_to_win_prob`,
/// `crate::mcts::normalize_score`) -- also NICHT die [-1,1]-tanh-Skala des
/// späteren `z`-Labels; Python remapt beim Cache-Bau ohnehin `*2-1` (siehe
/// `round_transition_value`-Konvention, `neural_net.py::MosaicDataset`),
/// `root_q` folgt exakt demselben Muster. `None` nur, wenn keine Bewertung
/// zustande kam (kein Kandidat/leere Suche).
///
/// VIERTES Rückgabeelement (Task #35, Ranking-Loss-Vorlauf, siehe
/// STATUS.md "Ranking-Loss auf Geschwister-Q"/Research-Report Idee 7.1):
/// `(Action, completed-Q)` je Wurzelkandidat, EXAKT dieselbe Reihenfolge
/// UND Länge wie das zweite Rückgabeelement (`completed_q_policy`) --
/// beide werden aus demselben Baum/Wald mit derselben `children ∪ untried`-
/// Traversierung gebaut (`root_completed_q_raw`/`root_completed_q_policy`
/// bzw. `average_completed_q_raw`/`average_completed_q_policy`), lassen sich
/// also 1:1 per Index zippen -- kein Aktions-Matching auf Python-Seite
/// nötig. Perspektive/Skala IDENTISCH zu `root_q` (drittes Element):
/// [0,1]-Gewinnwahrscheinlichkeit aus Sicht des an der WURZEL ziehenden
/// Spielers (`state.current_player`) -- besuchte Kandidaten tragen ihr
/// eigenes `value/visits`, unbesuchte `v_mix` (siehe
/// `completed_q_per_candidate`), NICHT die Softmax-transformierte
/// `policy`-Wahrscheinlichkeit. Leerer Vektor, wenn `completed_q_policy`
/// leer ist (keine Suche / Fallback, siehe `self_play::net_drafting_policy`).
pub fn net_root_child_stats_and_policy<R: Rng + ?Sized>(
    net: &Net,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    rng: &mut R,
    search_config: &SearchConfig,
) -> (Vec<(Action, u32, f64)>, Vec<(Action, f64)>, Option<f64>, Vec<(Action, f64)>) {
    if state.phase != Phase::Drafting {
        return (Vec::new(), Vec::new(), None, Vec::new());
    }
    if crate::round5::applies(state) && crate::round5::net_solver_enabled() {
        let stats: Vec<(Action, u32, f64)> =
            crate::round5::choose_action(state).into_iter().map(|a| (a, 1, 1.0)).collect();
        let n = stats.len().max(1);
        let policy: Vec<(Action, f64)> = stats.iter().map(|(a, _, _)| (a.clone(), 1.0 / n as f64)).collect();
        // Runde 5 hat KEINEN MCTS-Baum (Alpha-Beta statt Netz-Suche, siehe
        // oben) -- der exakte Minimax-Wurzelwert kommt separat aus
        // `round5::choose_action_with_analysis`, die BEREITS (round5.rs,
        // nicht hier neu erfunden) exakt dieselbe tanh-Margin-Normierung auf
        // die [0,1]-Gewinnwahrscheinlichkeits-Skala anwendet wie das MCTS-
        // `root_q` unten (`((val/VALUE_SCALE).tanh()+1.0)/2.0`, siehe dortiger
        // Kommentar zu `mcts_q`). BEWUSST NICHT `choose_action`s eigene Suche
        // wiederverwendet: `choose_action` bricht bei Budget-/Zeit-
        // Überschreitung früh ab und lässt spätere Kandidaten UNBEWERTET,
        // während `choose_action_with_analysis` stattdessen auf einen
        // billigen `leaf_value`-Ersatzwert zurückfällt -- ein gemeinsamer Aufruf
        // könnte dadurch eine ANDERE Aktion als Sieger markieren. Die
        // tatsächlich GESPIELTE Aktion bleibt ausschließlich `choose_action`s
        // Ergebnis (oben, unverändert); die Zusatzanalyse dient NUR der
        // Root-Q-Metadatenerzeugung. Kosten: ein zusätzlicher, aber sehr
        // billiger Alpha-Beta-Lauf (NODE_BUDGET=200, keine Netz-Evals) --
        // anders als beim MCTS-Pfad unten NICHT wortwörtlich kostenlos, aber
        // neben der dominanten Netz-Suchkoste vernachlässigbar.
        let root_q = crate::round5::choose_action_with_analysis(state)
            .1
            .get("moves")
            .and_then(|m| m.as_array())
            .and_then(|moves| {
                moves.iter().find(|mv| mv.get("chosen").and_then(Value::as_bool) == Some(true))
            })
            .and_then(|mv| mv.get("mcts_q"))
            .and_then(Value::as_f64);
        // Task #35: Runde 5 hat -- anders als der Gumbel-Baumpfad unten --
        // KEIN echtes Geschwister-Set in `stats`/`policy` (by design nur die
        // EINE alphabeta-optimale Aktion, siehe oben), also auch kein echtes
        // Ranking-Loss-Paar. Trotzdem parallel befüllt (gleiches Kriterium
        // wie `root_q`: additiv, überall vorhanden, wo auch `root_q`
        // vorhanden ist) -- hier ein 1-elementiger Vektor mit demselben Wert
        // wie `root_q`, statt eines fehlenden Felds. Echte Geschwisterpaare
        // für das Training kommen ausschließlich aus Runden 1-4.
        let root_child_q: Vec<(Action, f64)> =
            stats.iter().map(|(a, _, _)| (a.clone(), root_q.unwrap_or(0.5))).collect();
        return (stats, policy, root_q, root_child_q);
    }
    let k = num_determinizations();
    if k <= 1 {
        let nodes =
            build_net_tree(net, None, state, sims, c_puct, add_root_noise, rng, None, None, search_config);
        let root_visits = nodes[0].visits.max(1) as f64;
        let root_q = Some(nodes[0].value / root_visits);
        return (
            root_child_stats_from_nodes(&nodes),
            root_completed_q_policy(&nodes),
            root_q,
            root_completed_q_raw(&nodes),
        );
    }
    // ISMCTS-Mehrfach-Determinisierung: Stats über die Welten-SUMME der
    // Besuche (treibt Self-Plays besuchsbasierte Sampling-Auswahl
    // unverändert weiter, jetzt über den Wald statt einer Welt), Policy-
    // Ziel = über die Welten gemittelte completed-Q-Politik. `root_q`
    // folgt demselben Summen-Muster wie `aggregate_root_child_stats`
    // (Σvalue/Σvisits über die Welten, NICHT das arithmetische Mittel der
    // Pro-Welt-Quotienten).
    let forest =
        build_determinized_forest(net, None, state, sims, c_puct, add_root_noise, k, rng, search_config);
    let (visits_sum, value_sum) = forest.iter().fold((0.0f64, 0.0f64), |(vs, vals), nodes| {
        (vs + nodes[0].visits as f64, vals + nodes[0].value)
    });
    let root_q = if visits_sum > 0.0 { Some(value_sum / visits_sum) } else { None };
    (
        aggregate_root_child_stats(&forest),
        average_completed_q_policy(&forest),
        root_q,
        average_completed_q_raw(&forest),
    )
}

/// Zippt `improved_policy(nodes, 0)` (reine Zahlen, Reihenfolge
/// `children ∪ untried`, siehe `completed_q_per_candidate`) mit den
/// zugehörigen Aktionen der Wurzel — extrahiert aus
/// [`net_root_child_stats_and_policy`] für einen Unit-Test ohne echtes
/// Netz/Suche (siehe Testmodul, hand-gebauter `Node`-Vektor).
fn root_completed_q_policy(nodes: &[Node]) -> Vec<(Action, f64)> {
    let improved = improved_policy(nodes, 0);
    let mut policy: Vec<(Action, f64)> = Vec::with_capacity(improved.len());
    for (i, &cid) in nodes[0].children.iter().enumerate() {
        if let Some(a) = nodes[cid].action.clone() {
            policy.push((a, improved[i]));
        }
    }
    let n_children = nodes[0].children.len();
    for (i, (act, _prior)) in nodes[0].untried.iter().enumerate() {
        policy.push((act.clone(), improved[n_children + i]));
    }
    policy
}

/// Task #35 (Ranking-Loss-Vorlauf, siehe STATUS.md): wie
/// [`root_completed_q_policy`], aber die ROHEN (nicht softmax-
/// transformierten) completed-Q-Werte je Wurzelkandidat --
/// `completed_q_per_candidate(nodes, 0)`s zweite Komponente, dieselbe
/// Groesse, die `improved_policy` intern fuer den Gumbel-Sigma-Score
/// verwendet (besuchtes Kind: eigenes `value/visits`; unbesucht: `v_mix`,
/// siehe dortige Kommentare), hier nur OHNE die anschliessende Softmax.
/// GLEICHE Traversierung/Reihenfolge wie `root_completed_q_policy`
/// (`children` zuerst, dann `untried`, exakt `completed_q_per_candidate`s
/// Reihenfolge) -- beide Funktionen laufen ueber denselben `nodes[0]`, die
/// Ergebnisse lassen sich daher 1:1 per Index zippen (`self_play.rs` baut
/// daraus das gleichnamige additive `root_child_q`-JSON-Feld, parallel zu
/// `policy`). Bewusst NICHT durch Wiederverwendung von `improved_policy`
/// implementiert -- die wuerde den rohen Wert VOR der Softmax gar nicht mehr
/// preisgeben.
fn root_completed_q_raw(nodes: &[Node]) -> Vec<(Action, f64)> {
    let cq = completed_q_per_candidate(nodes, 0);
    let mut out: Vec<(Action, f64)> = Vec::with_capacity(cq.len());
    for (i, &cid) in nodes[0].children.iter().enumerate() {
        if let Some(a) = nodes[cid].action.clone() {
            out.push((a, cq[i].1));
        }
    }
    let n_children = nodes[0].children.len();
    for (i, (act, _prior)) in nodes[0].untried.iter().enumerate() {
        out.push((act.clone(), cq[n_children + i].1));
    }
    out
}

/// Task #35: wie [`average_completed_q_policy`], aber fuer die ROHEN
/// completed-Q-Werte (`root_completed_q_raw` je Welt statt
/// `root_completed_q_policy`) -- arithmetisches Mittel ueber den
/// Determinisierungs-Wald, Aktions-Schluessel wie dort. KEINE Renormierung
/// am Ende: anders als die Softmax-Politik sind rohe Q-Werte keine
/// Wahrscheinlichkeiten, muessen nicht zu 1 summieren.
fn average_completed_q_raw(forest: &[Vec<Node>]) -> Vec<(Action, f64)> {
    let per_world: Vec<Vec<(Action, f64)>> =
        forest.iter().map(|nodes| root_completed_q_raw(nodes)).collect();
    let Some(reference) = per_world.first() else { return Vec::new() };
    let mut out: Vec<(Action, f64)> = Vec::with_capacity(reference.len());
    for (act, _) in reference {
        let mut sum = 0.0f64;
        let mut count = 0usize;
        for world in &per_world {
            if let Some(&(_, q)) = world.iter().find(|(a, _)| a == act) {
                sum += q;
                count += 1;
            }
        }
        out.push((act.clone(), if count > 0 { sum / count as f64 } else { 0.0 }));
    }
    out
}

/// Wie [`net_search_drafting_action`], liefert zusätzlich ein debug.html-kompatibles
/// Analyse-Dict je Wurzelkind: rohen Netz-Prior (`net_prob`/`net_prob_norm`, VOR jeder
/// Suche — das eigentliche Policy-Head-Signal) zusammen mit den PUCT-Such-Stats
/// (`mcts_visits`/`mcts_share`/`mcts_q`). Für den Server (Mensch-vs-Netz) und Debug-UI;
/// `add_root_noise` hier i.d.R. `false` (Dirichlet-Noise ist nur ein Self-Play-Kniff).
/// Mit `log = Some(..)` wird zusätzlich ein Sim-für-Sim-Trace protokolliert
/// (für den Server-Debug-Log-Button, analog zur Heuristik). `collect_trace`
/// (Task #95, Anforderung 1-3): NUR wenn `true`, werden zusätzlich der
/// ROOT-Value-Breakdown (`value_debug`-Feld) und der granulare Gumbel-Trace
/// (`gumbel_trace`-Feld) im Analyse-Dict befüllt -- kostet EINEN zusätzlichen
/// Netz-Forward-Pass (`compute_root_value_debug`) plus ein paar zusätzliche
/// `Vec`-Pushes während des Baumaufbaus, sonst KEINE Änderung an Auswahl/
/// Backprop/RNG-Verbrauch (Paritätstest siehe Testmodul). Alle
/// Produktions-Aufrufstellen (`ai_step_net_json`/`ai_drafting_net_step`)
/// übergeben `false` -- nur `ai_debug_net_json` (reiner Analyse-Endpunkt,
/// kein Zug wird angewendet) übergibt `true`.
pub fn net_search_with_tree<R: Rng + ?Sized>(
    net: &Net,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    rng: &mut R,
    mut log: Option<&mut Vec<String>>,
    collect_trace: bool,
) -> (Option<Action>, Value) {
    if state.phase != Phase::Drafting {
        return (None, Value::Null);
    }
    if crate::round5::applies(state) && crate::round5::net_solver_enabled() {
        return crate::round5::choose_action_with_analysis(state);
    }
    // Debug-UI-/Mensch-vs-Netz-Einstieg (py.rs, kein Arena-/Self-Play-Pfad):
    // AUSSERHALB des Wave-1-Scopes von PREREG_agent_encapsulation.md (keine
    // Pro-Seite-Spec dafuer vorgesehen) -- liest die Suchkonfiguration daher
    // wie bisher aus der Umgebung, jetzt aber ueber `SearchConfig::from_env()`
    // statt dem entfernten OnceLock-Getter (gleiches Ergebnis, kein
    // Verhaltensunterschied).
    let search_config = SearchConfig::from_env();
    let k = num_determinizations();
    if k <= 1 {
        let mut trace = if collect_trace { Some(GumbelTrace::default()) } else { None };
        let nodes = build_net_tree(
            net, None, state, sims, c_puct, add_root_noise, rng, log, trace.as_mut(), &search_config,
        );
        return net_search_with_tree_from_nodes(state, sims, &nodes, trace.as_ref());
    }
    // ISMCTS-Mehrfach-Determinisierung: kein granularer Sim-für-Sim-Trace je
    // Welt (würde N verschachtelte "=== Sim x/y ==="-Folgen ergeben, kaum
    // lesbar) -- ein einzelner Hinweis genügt, gleiches Muster wie
    // `build_net_tree`s Gumbel-Dispatch-Log. Strukturierter Gumbel-Trace
    // (`collect_trace`) ist im Mehrwelten-Pfad NICHT unterstützt (aktuell
    // ohnehin nur ueber `MOSAIC_NUM_DETERMINIZATIONS>1` erreichbar, Default
    // weiterhin `k=1`, siehe `num_determinizations`-Doku).
    if let Some(l) = log.as_deref_mut() {
        l.push(format!("  ISMCTS: {k} Determinisierungen (kein granularer Sim-Trace je Welt)"));
    }
    let forest =
        build_determinized_forest(net, None, state, sims, c_puct, add_root_noise, k, rng, &search_config);
    net_search_with_tree_from_forest(state, sims, &forest)
}

/// `net_search_with_tree`s Debug-Analyse-Dict aus einem EINZELNEN Baum
/// (`NUM_DETERMINIZATIONS <= 1`-Pfad, unverändert gegenüber vor Task #65).
/// `trace` (Task #95): nur `Some`, wenn `collect_trace=true` angefordert --
/// befüllt zusätzlich `value_debug`/`gumbel_trace`/`value`/`win_pct`.
fn net_search_with_tree_from_nodes(
    state: &GameState,
    sims: u32,
    nodes: &[Node],
    trace: Option<&GumbelTrace>,
) -> (Option<Action>, Value) {
    let best = select_final_root_child(nodes);
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
            // Task #89: `action_to_env_dict`-Schema (self_play.rs) -- NICHT
            // dasselbe wie `label_search_move`s `serialize::action_to_dict`
            // (unterschiedliche Feldnamen, z.B. `display_index` vs. `tile_id`)!
            // Nur `action_to_env_dict` passt zu `neural_net.py::action_to_id`
            // und damit zur festen NUM_ACTIONS-Indizierung eines Kandidaten-
            // Netzes (Oracle-Metriken, tools/oracle_metrics.py). Rein additiv,
            // bisherige Konsumenten (Debug-UI) ignorieren das neue Feld.
            let env_action = node.action.as_ref().map(|a| action_to_env_dict(state, a));
            let is_chosen = best == Some(cid);
            if is_chosen {
                chosen_id = Some(i);
            }
            // Task #97 (Lehrer-Modus-Feedback): `ChooseDomeSlot`/`ChooseDrawStackSlot`
            // tragen selbst KEINE Rotation (Platzhalter 0, siehe moves.rs) -- die
            // Rotationswahl ist ein separater `ChooseDomeRotation`-Zug, der als
            // KIND dieses Wurzelkandidaten im Suchbaum steht (game.rs::drafting_actions
            // liefert nach `ChooseDomeSlot`/`ChooseDrawStackSlot` via `pending_dome_choice`
            // ausschließlich `ChooseDomeRotation`-Kandidaten). Rein lesender Zugriff auf
            // bereits vorhandene Baumdaten (`node.children`) -- KEIN Effekt auf Suche/
            // Selektion/Backprop/RNG (nur diese Debug-JSON-Zusammenstellung betroffen).
            let best_rotation = node
                .children
                .iter()
                .filter_map(|&gc| match &nodes[gc].action {
                    Some(Action::ChooseDomeRotation(rot)) => Some((&nodes[gc], *rot)),
                    _ => None,
                })
                .max_by_key(|(gnode, _)| gnode.visits)
                .map(|(gnode, rot)| {
                    let gq = if gnode.visits > 0 { gnode.value / gnode.visits as f64 } else { 0.0 };
                    json!({ "rotation": rot, "visits": gnode.visits, "q": gq, "win_pct": gq * 100.0 })
                });
            json!({
                "action_id": i,
                "type": typ,
                "description": desc,
                "category": cat,
                "action": env_action,
                "net_prob": node.prior,
                "net_prob_norm": node.prior as f64 / prior_sum,
                "mcts_visits": node.visits,
                "mcts_share": if total_visits > 0 { node.visits as f64 / total_visits as f64 } else { 0.0 },
                "mcts_q": q,
                "mcts_win_pct": q * 100.0,
                // Task #95 (Anforderung 1): Netz-Blattwert DIESES Kindzustands,
                // aus Sicht des Spielers, der den Zug gemacht hat (dieselbe
                // Perspektive wie `mcts_q`/`node.value` -- siehe `node_own_value`-
                // Kommentar) -- bereits bei Expansion berechnet (`make_node`),
                // hier nur ausgelesen. Zeigt die Netz-ERSTEINSCHÄTZUNG dieses
                // Zugs, VOR jeder weiteren Suchvertiefung -- Divergenz zu
                // `mcts_q` zeigt, wo die Suche vom Netz abweicht.
                "net_leaf_value": node.leaf_value[node.player_who_acted],
                // PREREG_points_head_plates.md (Stufe 2): rohe Netz-Kopf-
                // Ausgaben AM KINDZUSTAND `node` (dieselbe Ego-Perspektive
                // wie `net_leaf_value` oben) -- `points_forecast`/
                // `opp_points_forecast` waren bereits als `Node`-Felder da
                // (Denial-Tiebreak, Task E3), `raw_value` ist additiv NEU
                // (siehe `Node::raw_value`-Kommentar). Reiner Lesezugriff,
                // kein Zusatz-Netz-Aufruf, `None` bei Netzen ohne den
                // jeweiligen Kopf.
                "net_raw_value": node.raw_value,
                "net_points_forecast": node.points_forecast,
                "net_opp_points_forecast": node.opp_points_forecast,
                "max_depth": subtree_depth(nodes, cid),
                "chosen": is_chosen,
                // Task #97: besuchsstärkste Rotationswahl (Kind-Knoten) für
                // choose_dome_slot/choose_draw_stack_slot -- `null`, falls die Suche
                // diesen Kandidaten nie bis zur Rotationsstufe vertieft hat (kleines
                // Sim-Budget) oder der Kandidat kein Kuppelzug ist.
                "best_rotation": best_rotation,
            })
        })
        .collect();

    let root_visits = nodes[0].visits.max(1) as f64;
    let root_q = nodes[0].value / root_visits;

    // Task #95 (Anforderung 1): Root-Value-Anzeige -- `value`/`win_pct` sind
    // bestehende, vom Frontend (`debug.html`) bereits konsumierte Top-Level-
    // Felder (bisher IMMER `Null` im Netz-Pfad, siehe Git-Historie); mit
    // `value_debug` befüllt (nur wenn `collect_trace=true`) zeigen sie jetzt
    // den tatsächlichen Netz-Rohwert/die Ego-Win-Wahrscheinlichkeit der
    // Wurzel. `gumbel_trace` (Anforderung 2) bleibt `Null`, wenn kein Trace
    // angefordert wurde ODER die Suche nicht im Gumbel-Modus lief (PUCT-
    // Legacy-Pfad sammelt keinen Trace, siehe `build_net_tree`-Kommentar).
    let (value_field, win_pct_field, value_debug_field) = match trace.and_then(|t| t.root_value.as_ref()) {
        Some(vd) => (json!(vd.raw_value), json!(vd.win_prob * 100.0), vd.to_json()),
        None => (Value::Null, Value::Null, Value::Null),
    };
    let gumbel_trace_field = match trace {
        Some(t) if !t.top_m.is_empty() || !t.finalists.is_empty() => t.to_json(),
        _ => Value::Null,
    };

    let analysis = json!({
        "current_player": nodes[0].player_who_acted,
        "ai_player": state.current_player,
        "value": value_field,
        "win_pct": win_pct_field,
        "value_debug": value_debug_field,
        "gumbel_trace": gumbel_trace_field,
        "has_net": true,
        "simulations": sims,
        // Gesamtzahl legaler Züge (unabhängig vom Widening) vs. tatsächlich
        // durchsuchte Wurzelkinder — Server-Debug-UI zeigt "considered/total".
        "num_actions": nodes[0].n_actions,
        "num_actions_considered": nodes[0].children.len(),
        "max_depth": subtree_depth(nodes, 0),
        "ai_action": chosen_id,
        "moves": moves,
        "tree": json!({
            "visits": nodes[0].visits,
            "win_pct": root_q * 100.0,
            "depth": subtree_depth(nodes, 0),
            "n_children": nodes[0].children.len(),
        }),
    });

    let chosen = best.and_then(|cid| nodes[cid].action.clone());
    (chosen, analysis)
}

/// `net_search_with_tree`s Debug-Analyse-Dict aus dem Determinisierungs-Wald
/// (`NUM_DETERMINIZATIONS > 1`). Baut dieselben Felder wie
/// `net_search_with_tree_from_nodes`, aber aus den über die Welten
/// AGGREGIERTEN Größen (`aggregate_root_child_stats`/
/// `average_completed_q_policy`, siehe dortige Kommentare) statt einem
/// Einzelbaum -- "gewählter Zug" folgt derselben Regel wie
/// `net_search_drafting_action` (argmax gemittelte completed-Q-Politik).
/// Strukturelle Felder ohne sinnvolles Mehrwelten-Äquivalent (rohe
/// Netz-Priors VOR jeder Suche, `n_actions`) kommen repräsentativ aus der
/// ERSTEN Welt -- laut Befund im `NUM_DETERMINIZATIONS`-Kommentar sind
/// Wurzel-Kandidaten UND deren Priors (maskierte Features) weltunabhängig,
/// eine einzelne Welt ist hier also keine Näherung, sondern exakt.
fn net_search_with_tree_from_forest(state: &GameState, sims: u32, forest: &[Vec<Node>]) -> (Option<Action>, Value) {
    let stats = aggregate_root_child_stats(forest); // (Action, Σ Besuche, Q)
    let policy = average_completed_q_policy(forest); // (Action, gemittelte completed-Q-Wahrscheinlichkeit)
    let chosen: Option<Action> = policy
        .iter()
        .max_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal))
        .map(|(a, _)| a.clone());

    let total_visits: u32 = stats.iter().map(|(_, v, _)| *v).sum();
    let nodes0: &[Node] = &forest[0];
    let prior_sum: f64 = nodes0[0].children.iter().map(|&c| nodes0[c].prior as f64).sum::<f64>()
        + nodes0[0].untried.iter().map(|(_, p)| *p as f64).sum::<f64>();
    let prior_sum = prior_sum.max(1e-8);
    let prior_of = |a: &Action| -> f32 {
        nodes0[0]
            .children
            .iter()
            .find(|&&c| nodes0[c].action.as_ref() == Some(a))
            .map(|&c| nodes0[c].prior)
            .or_else(|| nodes0[0].untried.iter().find(|(act, _)| act == a).map(|(_, p)| *p))
            .unwrap_or(0.0)
    };
    // Task #95: `net_leaf_value` repräsentativ aus der ERSTEN Welt (siehe
    // Modul-Kommentar oben zu `prior_of`) -- `None`, wenn die Aktion in Welt 0
    // nie zu einem Kind wurde (kleineres Pro-Welt-Sims-Budget, siehe
    // `aggregate_root_child_stats`-Kommentar).
    let leaf_value_of = |a: &Action| -> Option<f64> {
        nodes0[0]
            .children
            .iter()
            .find(|&&c| nodes0[c].action.as_ref() == Some(a))
            .map(|&c| nodes0[c].leaf_value[nodes0[c].player_who_acted])
    };
    // PREREG_points_head_plates.md (Stufe 2): wie `leaf_value_of` -- rohe
    // Netz-Kopf-Ausgaben repräsentativ aus Welt 0, nur zur Schema-Parität mit
    // `net_search_with_tree_from_nodes` ergänzt (siehe `best_rotation_of`-
    // Kommentar, derselbe praktisch-unerreicht-Vorbehalt).
    let raw_value_of = |a: &Action| -> Option<f32> {
        nodes0[0]
            .children
            .iter()
            .find(|&&c| nodes0[c].action.as_ref() == Some(a))
            .and_then(|&c| nodes0[c].raw_value)
    };
    let points_forecast_of = |a: &Action| -> Option<f32> {
        nodes0[0]
            .children
            .iter()
            .find(|&&c| nodes0[c].action.as_ref() == Some(a))
            .and_then(|&c| nodes0[c].points_forecast)
    };
    let opp_points_forecast_of = |a: &Action| -> Option<f32> {
        nodes0[0]
            .children
            .iter()
            .find(|&&c| nodes0[c].action.as_ref() == Some(a))
            .and_then(|&c| nodes0[c].opp_points_forecast)
    };
    // Task #97: wie `leaf_value_of` -- repräsentativ aus Welt 0, besuchsstärkste
    // `ChooseDomeRotation`-KIND unter dem Wurzelkandidaten `a` (siehe ausführlicher
    // Kommentar in `net_search_with_tree_from_nodes`). `None`, wenn `a` in Welt 0
    // nie zu einem Kind wurde ODER dieses Kind nie bis zur Rotationsstufe vertieft
    // wurde. Aktuell praktisch unerreicht (NUM_DETERMINIZATIONS == 1 -> dieser
    // Forest-Pfad wird vom Debug-Endpunkt nicht durchlaufen), nur zur Schema-Parität
    // mit `net_search_with_tree_from_nodes` ergänzt (siehe Modul-Kommentar oben).
    let best_rotation_of = |a: &Action| -> Value {
        nodes0[0]
            .children
            .iter()
            .find(|&&c| nodes0[c].action.as_ref() == Some(a))
            .and_then(|&c| {
                nodes0[c]
                    .children
                    .iter()
                    .filter_map(|&gc| match &nodes0[gc].action {
                        Some(Action::ChooseDomeRotation(rot)) => Some((&nodes0[gc], *rot)),
                        _ => None,
                    })
                    .max_by_key(|(gnode, _)| gnode.visits)
                    .map(|(gnode, rot)| {
                        let gq = if gnode.visits > 0 { gnode.value / gnode.visits as f64 } else { 0.0 };
                        json!({ "rotation": rot, "visits": gnode.visits, "q": gq, "win_pct": gq * 100.0 })
                    })
            })
            .unwrap_or(Value::Null)
    };

    let mut ordered = stats.clone();
    ordered.sort_by(|a, b| b.1.cmp(&a.1));

    let mut chosen_id: Option<usize> = None;
    let moves: Vec<Value> = ordered
        .iter()
        .enumerate()
        .map(|(i, (act, visits, q))| {
            let (typ, desc, cat, _mv) = label_search_move(&SearchMove::Draft(act.clone()), Some(state));
            let is_chosen = chosen.as_ref() == Some(act);
            if is_chosen {
                chosen_id = Some(i);
            }
            let prior = prior_of(act);
            json!({
                "action_id": i,
                "type": typ,
                "description": desc,
                "category": cat,
                "net_prob": prior,
                "net_prob_norm": prior as f64 / prior_sum,
                "mcts_visits": *visits,
                "mcts_share": if total_visits > 0 { *visits as f64 / total_visits as f64 } else { 0.0 },
                "mcts_q": *q,
                "mcts_win_pct": *q * 100.0,
                "net_leaf_value": leaf_value_of(act),
                "net_raw_value": raw_value_of(act),
                "net_points_forecast": points_forecast_of(act),
                "net_opp_points_forecast": opp_points_forecast_of(act),
                "max_depth": Value::Null,
                "chosen": is_chosen,
                "best_rotation": best_rotation_of(act),
            })
        })
        .collect();

    let (visits_sum, value_sum): (u32, f64) = stats
        .iter()
        .fold((0u32, 0.0f64), |(vs, vl), (_, v, q)| (vs + v, vl + q * (*v as f64)));
    let root_q = if visits_sum > 0 { value_sum / visits_sum as f64 } else { 0.0 };
    let max_depth = forest.iter().map(|nodes| subtree_depth(nodes, 0)).max().unwrap_or(0);

    let analysis = json!({
        "current_player": nodes0[0].player_who_acted,
        "ai_player": state.current_player,
        "value": Value::Null,
        "win_pct": Value::Null,
        // Task #95: ROOT-Value-Breakdown/Gumbel-Trace nur im Einzelbaum-Pfad
        // unterstützt (siehe `net_search_with_tree`-Kommentar) -- hier immer
        // `Null`, damit das Analyse-Dict-Schema in beiden Pfaden gleich bleibt.
        "value_debug": Value::Null,
        "gumbel_trace": Value::Null,
        "has_net": true,
        "simulations": sims,
        // PREREG_ismcts_determinizations.md: `forest.len()` statt der
        // Konstante/des Getters -- `build_determinized_forest` erzeugt IMMER
        // genau `forest.len()` Welten (siehe `split_sims_across_worlds`,
        // Laenge = `n.max(1)`), das ist hier die tatsaechlich verwendete
        // Welten-Anzahl, ohne einen weiteren (wenn auch gecachten) Env-Read.
        "determinizations": forest.len(),
        "num_actions": nodes0[0].n_actions,
        "num_actions_considered": stats.len(),
        "max_depth": max_depth,
        "ai_action": chosen_id,
        "moves": moves,
        "tree": json!({
            "visits": visits_sum,
            "win_pct": root_q * 100.0,
            "depth": max_depth,
            "n_children": stats.len(),
        }),
    });

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
    use rand::seq::IndexedRandom;
    use rand::SeedableRng;

    fn names() -> [String; 2] {
        ["P1".into(), "P2".into()]
    }

    /// PREREG_search_rng_split.md §5-Vorlauf: `derive_search_seed` selbst muss
    /// (a) deterministisch sein (gleiche Eingaben -> gleicher Seed) und (b)
    /// unterschiedliche `move_index`-Werte auf unterschiedliche Seeds
    /// streuen (keine Treppe in den unteren Bits, siehe Funktionskommentar).
    #[test]
    fn derive_search_seed_is_deterministic_and_spreads_move_index() {
        assert_eq!(derive_search_seed(42, 0), derive_search_seed(42, 0));
        assert_eq!(derive_search_seed(42, 7), derive_search_seed(42, 7));
        let s0 = derive_search_seed(42, 0);
        let s1 = derive_search_seed(42, 1);
        let s2 = derive_search_seed(42, 2);
        assert_ne!(s0, s1);
        assert_ne!(s1, s2);
        assert_ne!(s0, s2);
        // Verschiedene game_seed bei gleichem move_index ebenfalls verschieden.
        assert_ne!(derive_search_seed(42, 3), derive_search_seed(43, 3));
    }

    /// TEIL E, NETZ-Haelfte (`PREREG_chance_nodes.md`): schlaegt der GELERNTE
    /// Blattwert den EXAKTEN in Runde 5? Dieselbe Skala wie die Loeser-Haelfte
    /// -- Uebereinstimmung mit einer tiefen Referenzsuche (20.000 Knoten), auf
    /// identischen Stellungen, weitergespielt mit der Orakel-Wahl.
    ///
    /// KEINE Arena: der Loeser sitzt in BEIDEN Bahnen, ein Wechsel hebt sonst
    /// beide Seiten und die Siegquote bleibt blind (Symmetrie-Fallstrick, im
    /// PREREG vermerkt).
    ///
    /// Der Netz-Zug wird ueber `build_net_tree` + `select_final_root_child`
    /// geholt -- genau der Rumpf, den `net_search_drafting_action` bei k=1
    /// (Default) ausfuehrt, also der Produktionspfad ohne den Runde-5-
    /// Ruecksprung. Ueber `MOSAIC_R5_NET_SOLVER` waere das nicht testbar
    /// (OnceLock, ein Wert je Prozess).
    #[test]
    #[ignore]
    fn teil_e_net_half_oracle_agreement_probe() {
        use crate::round_transition::drive_to_round_start;
        use rand::rngs::StdRng;
        use rand::SeedableRng;
        use std::time::{Duration, Instant};

        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../models/alphazero_v21_2d_brierbest.onnx");
        let net = Net::load_auto(path.to_str().unwrap()).unwrap_or_else(|e| panic!(
            "{path:?} nicht ladbar ({e}) -- Sonden-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ));
        const ORACLE: u64 = 20_000;
        const SIMS: u32 = 400;
        const C_PUCT: f64 = 1.5;

        let mut rng = StdRng::seed_from_u64(20260810);
        let mut total = 0usize;
        let mut solver_agree = 0usize;
        let mut net_agree = 0usize;
        let mut both_same = 0usize;
        for seed in [101u64, 202, 303, 404, 505, 606, 707, 808] {
            let mut state = drive_to_round_start(seed, 5);
            let mut guard = 0u32;
            while state.phase == Phase::Drafting && guard < 200 {
                guard += 1;
                let oracle = match crate::round5::choose_action_deadlined(
                    &state,
                    false,
                    ORACLE,
                    Instant::now() + Duration::from_secs(120),
                ) {
                    Some(a) => a,
                    None => break,
                };
                let solver = crate::round5::choose_action(&state);
                let nodes = build_net_tree(
                    &net, None, &state, SIMS, C_PUCT, false, &mut rng, None, None, &SearchConfig::from_env(),
                );
                let net_choice = select_final_root_child(&nodes).and_then(|b| nodes[b].action.clone());

                total += 1;
                if solver.as_ref() == Some(&oracle) {
                    solver_agree += 1;
                }
                if net_choice.as_ref() == Some(&oracle) {
                    net_agree += 1;
                }
                if solver.is_some() && solver == net_choice {
                    both_same += 1;
                }

                let mut g = Game { state };
                if g.apply_drafting(&oracle).is_err() {
                    break;
                }
                state = g.state;
            }
        }
        let pc = |x: usize| if total > 0 { 100.0 * x as f64 / total as f64 } else { 0.0 };
        println!("TEIL E NETZ-HAELFTE: Orakel = {ORACLE} Knoten, {total} Entscheidungen");
        println!("  Loeser@200  : {solver_agree}/{total} = {:.1}%", pc(solver_agree));
        println!("  Netz@{SIMS}   : {net_agree}/{total} = {:.1}%", pc(net_agree));
        println!("  beide gleich: {both_same}/{total} = {:.1}%", pc(both_same));
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
    fn env_knoepfe_defaults_sind_bestandsverhalten() {
        // PREREG_search_path_remeasurements: ohne gesetzte Env-Vars muessen
        // beide Laufzeit-Knoepfe exakt die bisherigen Konstanten liefern
        // (Paritaets-Bedingung; die Env-Vars sind in der Testumgebung
        // nicht gesetzt, OnceLock cached den Default).
        assert_eq!(floor_shaping_weight(), FLOOR_SHAPING_WEIGHT);
        // E2 (PREREG_aggression_style_measurement.md, MOSAIC_FLOOR_SHAPING_OPP_BIAS):
        // ungesetzt -> 1.0 -> alle Aufrufstellen nehmen den `opp_bias==1.0`-
        // Zweig, byte-identisch zum Bestand vor E2.
        assert_eq!(floor_shaping_opp_bias(), FLOOR_SHAPING_OPP_BIAS);
        assert_eq!(gumbel_top_m_for_budget(150), 9);
        assert_eq!(gumbel_top_m_for_budget(400), GUMBEL_TOP_M);
        // τ-Annealing (Messung 3, MOSAIC_TAU_ARGMAX_FROM_MOVE): ungesetzt ->
        // None -> self_play::net_drafting_policy nimmt weiterhin IMMER den
        // weighted_index-Sampling-Zweig (kein argmax-Zweig erreichbar).
        assert_eq!(tau_argmax_from_move(), None);
        // Denial-Tie-Break (PREREG_denial_tiebreak.md, MOSAIC_DENIAL_TIEBREAK_EPS):
        // ungesetzt -> 0.0 -> `apply_denial_tiebreak_with`s Fruehausstieg greift
        // IMMER, `select_final_root_child` bleibt exakt `gumbel_final_root_action`.
        assert_eq!(denial_tiebreak_eps(), 0.0);
        // E3b (PREREG_denial_tiebreak.md, Abschnitt "E3b"): beide neuen Knoepfe
        // ungesetzt -> `MOSAIC_DENIAL_UNCERT_Z` liefert 0.0 (AUS, `apply_denial_
        // tiebreak_uncert_with`s Fruehausstieg greift IMMER), `MOSAIC_DENIAL_
        // MIN_VISIT_FRAC` liefert den PREREG-Default 0.5 (nur wirksam, wenn z>0).
        assert_eq!(denial_uncert_z(), 0.0);
        assert_eq!(denial_min_visit_frac(), 0.5);
        // ISMCTS-k (PREREG_ismcts_determinizations.md, MOSAIC_NUM_
        // DETERMINIZATIONS): ungesetzt -> liefert exakt die Konstante
        // `NUM_DETERMINIZATIONS` (heute 1) -- alle vier Sucheinstiege bleiben
        // im `<= 1`-Einzelbaum-Codepfad, byte-identisch zum Bestand.
        assert_eq!(num_determinizations(), NUM_DETERMINIZATIONS);
    }

    #[test]
    fn gumbel_top_m_for_budget_unchanged_at_400_and_600_sims() {
        // Task #14: bei den bisherigen Standard-Suchbudgets (Arena/Self-Play,
        // s. `DECOUPLE_NET_SIMS_FROM_ACTIONS`-Kommentar) MUSS die neue
        // budgetabhaengige Formel exakt dieselbe Wurzelbreite liefern wie die
        // alte fixe Konstante -- sonst waere die Aenderung nicht additiv.
        assert_eq!(gumbel_top_m_for_budget(400), GUMBEL_TOP_M);
        assert_eq!(gumbel_top_m_for_budget(600), GUMBEL_TOP_M);
        // Auch knapp unterhalb/oberhalb bleibt es beim Ceiling (16*16=256 ist
        // die kleinste Sim-Zahl, bei der round(sims/16) ueberhaupt >= 16
        // wird -- alles ab da wird gekappt).
        assert_eq!(gumbel_top_m_for_budget(256), GUMBEL_TOP_M);
        assert_eq!(gumbel_top_m_for_budget(1000), GUMBEL_TOP_M);

        // Untere Clamp-Grenze: sehr kleine (z.B. PCR-Cheap-)Budgets duerfen
        // nie unter 4 Kandidaten fallen.
        assert_eq!(gumbel_top_m_for_budget(1), 4);
        assert_eq!(gumbel_top_m_for_budget(32), 4);

        // Dazwischen: proportional zum Budget (Sequential-Halving-Argument
        // im Funktionskommentar), gerundet.
        assert_eq!(gumbel_top_m_for_budget(150), 9); // round(150/16) = 9.375 -> 9
        assert_eq!(gumbel_top_m_for_budget(64), 4); // round(64/16) = 4 (untere Grenze exakt getroffen)
        assert_eq!(gumbel_top_m_for_budget(128), 8); // round(128/16) = 8
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

        let (acts, n_base) = build_untried_actions(&state, &logits, &moon_scores, false);
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

        let (acts, n_base) = build_untried_actions(&state, &logits, &moon_scores, false);
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

    /// Baut einen frischen Zustand OHNE offene Startplatten-Pflicht (sonst
    /// blockiert `validate_dome_move`/`has_unplaced_start_tile` jede
    /// `Action::ChooseDomeSlot`-Kandidatengenerierung -- siehe game.rs).
    fn state_with_dome_moves_available(seed: u64) -> GameState {
        let mut rng = StdRng::seed_from_u64(seed);
        let mut state = setup_new_game(names(), 0, &mut rng);
        for p in state.players.iter_mut() {
            p.start_tile_pending = false;
        }
        state
    }

    #[test]
    fn build_untried_actions_dome_slot_candidates_get_independent_direct_priors() {
        // Baustein B: ChooseDomeSlot-Kandidaten (Kachel+Slot) haben seit der
        // Zerlegung in game.rs JEWEILS eine eigene, nicht kollabierte Policy-ID
        // (siehe features.rs::action_to_id) -- keine Faktorisierung mehr noetig.
        // Ein geboosteter Logit fuer GENAU EINE ID darf also NUR deren eigenen
        // Prior anheben, keine Geschwister-Kandidaten.
        let state = state_with_dome_moves_available(7);
        let base_actions = drafting_actions(&state);
        let dome_candidates: Vec<&Action> =
            base_actions.iter().filter(|a| matches!(a, Action::ChooseDomeSlot(_))).collect();
        assert!(dome_candidates.len() > 1, "Testvoraussetzung: mehrere ChooseDomeSlot-Kandidaten");

        let target_id = crate::self_play::action_to_id_direct(&state, dome_candidates[0]);
        let mut logits = vec![0.1f32; NUM_ACTIONS];
        logits[target_id] = 5.0;
        let moon_scores = [0f32; 5];

        let (acts, _n) = build_untried_actions(&state, &logits, &moon_scores, false);

        let target_p = acts
            .iter()
            .find(|(a, _)| matches!(a, Action::ChooseDomeSlot(_)) && crate::self_play::action_to_id_direct(&state, a) == target_id)
            .map(|(_, p)| *p)
            .expect("geboostete ID sollte im Kandidatenergebnis auftauchen");
        for (a, p) in &acts {
            if matches!(a, Action::ChooseDomeSlot(_)) && crate::self_play::action_to_id_direct(&state, a) != target_id {
                assert!(
                    target_p > *p,
                    "geboosteter Kandidat sollte strikt hoeheren Prior haben als \
                     ungeboostete Geschwister: {target_p} vs {p}"
                );
            }
        }
    }

    #[test]
    fn build_untried_actions_draw_stack_candidates_carry_positive_mass() {
        // DrawStack-Kandidaten existieren nur waehrend eines laufenden
        // Stapel-Zugs (`pending_stack_draw` nichtleer) -- direkt konstruieren
        // statt durch echtes Ziehen zu spielen (kein bestehender Test-
        // Helfer dafuer, siehe game.rs::generate_draw_stack_moves-Doc).
        let mut state = state_with_dome_moves_available(3);
        let pending: Vec<_> = state.dome_tile_pool.iter().take(2).cloned().collect();
        assert!(pending.len() >= 2, "Testvoraussetzung: genug Platten im verdeckten Stapel");
        state.pending_stack_draw = pending;

        let base_actions = drafting_actions(&state);
        let draw_stack_count =
            base_actions.iter().filter(|a| matches!(a, Action::ChooseDrawStackSlot(_))).count();
        assert!(draw_stack_count > 1, "Testvoraussetzung: mehrere ChooseDrawStackSlot-Kandidaten");

        let logits = vec![0.1f32; NUM_ACTIONS];
        let moon_scores = [0f32; 5];
        let (acts, _n) = build_untried_actions(&state, &logits, &moon_scores, false);

        let draw_stack_sum: f64 = acts
            .iter()
            .filter(|(a, _)| matches!(a, Action::ChooseDrawStackSlot(_)))
            .map(|(_, p)| *p as f64)
            .sum();
        assert!(draw_stack_sum > 0.0, "ChooseDrawStackSlot-Kandidaten sollten positive Prior-Masse tragen");
    }

    // ── Gumbel AlphaZero: Kern-Mathematik (Phase 1) ─────────────────────────

    fn gumbel_test_state(current_player: usize) -> GameState {
        let mut rng = StdRng::seed_from_u64(0);
        let mut s = setup_new_game(names(), 0, &mut rng);
        s.current_player = current_player;
        s
    }

    /// Minimaler Testknoten -- nur die für Gumbel-Mathematik relevanten
    /// Felder (`prior`/`visits`/`value`/`leaf_value`/`state.current_player`)
    /// sind aussagekräftig, der Rest ist Fuellwerk.
    fn gumbel_test_node(prior: f32, visits: u32, value: f64, current_player: usize) -> Node {
        Node {
            parent: None,
            children: Vec::new(),
            untried: Vec::new(),
            action: None,
            player_who_acted: 0,
            visits,
            value,
            prior,
            state: gumbel_test_state(current_player),
            terminal: false,
            leaf_value: [0.0, 0.0],
            n_actions: 0,
            points_forecast: None,
            opp_points_forecast: None,
            raw_value: None,
            // Default deckungsgleich mit `leaf_value` (Blatt-Fall) -- Tests,
            // die `im_value` explizit brauchen, setzen es nach dem Aufruf.
            im_value: [0.0, 0.0],
        }
    }

    #[test]
    fn sample_gumbel_is_reproducible_with_fixed_seed() {
        let mut rng_a = StdRng::seed_from_u64(42);
        let mut rng_b = StdRng::seed_from_u64(42);
        let a: Vec<f64> = (0..20).map(|_| sample_gumbel(&mut rng_a)).collect();
        let b: Vec<f64> = (0..20).map(|_| sample_gumbel(&mut rng_b)).collect();
        assert_eq!(a, b, "gleicher Seed muss dieselbe Gumbel-Folge liefern");
        // Sanity: nicht alle Werte identisch (echte Ziehung, keine Konstante).
        assert!(a.iter().any(|&x| (x - a[0]).abs() > 1e-6));
    }

    #[test]
    fn gumbel_sigma_matches_formula_directly() {
        let q = 0.7;
        let max_n = 30u32;
        let expected = (GUMBEL_C_VISIT + max_n as f64) * GUMBEL_C_SCALE * q;
        assert!((gumbel_sigma(q, max_n) - expected).abs() < 1e-12);
    }

    #[test]
    fn v_mix_falls_back_to_node_own_value_when_no_child_visited() {
        // Wurzel mit eigenem Blattwert 0.42 (Mover-Perspektive, current_player=0),
        // ein Kind, aber NIE besucht (visits=0) -- v_mix muss exakt auf den
        // eigenen Blattwert zurueckfallen (kein NaN, keine Division durch 0).
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.leaf_value = [0.42, 0.58];
        let child = gumbel_test_node(0.5, 0, 0.0, 1);
        let nodes = vec![root, child];
        let mut nodes = nodes;
        nodes[0].children.push(1);
        assert!((v_mix(&nodes, 0) - 0.42).abs() < 1e-12);
    }

    #[test]
    fn v_mix_matches_hand_computed_example_with_two_visited_children() {
        // Wurzel: eigener Blattwert 0.5 (current_player=0). Zwei Kinder:
        // Kind A prior=0.6 visits=4 value_sum=2.4 (Q=0.6), Kind B prior=0.2
        // visits=2 value_sum=1.6 (Q=0.8). N_total = 4+2 = 6.
        // weighted_Q = (0.6*0.6 + 0.2*0.8) / (0.6+0.2) = (0.36+0.16)/0.8 = 0.65
        // v_mix = (0.5 + 6*0.65) / (1+6) = (0.5 + 3.9) / 7 = 0.62857142857...
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.leaf_value = [0.5, 0.5];
        let child_a = gumbel_test_node(0.6, 4, 2.4, 1);
        let child_b = gumbel_test_node(0.2, 2, 1.6, 1);
        let mut nodes = vec![root, child_a, child_b];
        nodes[0].children.push(1);
        nodes[0].children.push(2);
        let expected = (0.5 + 6.0 * 0.65) / 7.0;
        assert!((v_mix(&nodes, 0) - expected).abs() < 1e-9, "v_mix={} expected={}", v_mix(&nodes, 0), expected);
    }

    #[test]
    fn completed_q_uses_own_q_for_visited_and_v_mix_for_unvisited() {
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.leaf_value = [0.5, 0.5];
        let child_a = gumbel_test_node(0.6, 4, 2.4, 1); // Q=0.6, besucht
        let mut nodes = vec![root, child_a];
        nodes[0].children.push(1);
        nodes[0].untried.push((Action::Pass, 0.1));
        nodes[0].untried.push((Action::Pass, 0.05));
        let cq = completed_q_per_candidate(&nodes, 0);
        assert_eq!(cq.len(), 3, "1 Kind + 2 untried");
        assert!((cq[0].1 - 0.6).abs() < 1e-9, "besuchtes Kind behaelt eigenes Q");
        let vmix = v_mix(&nodes, 0);
        assert!((cq[1].1 - vmix).abs() < 1e-12, "unbesucht #1 bekommt v_mix");
        assert!((cq[2].1 - vmix).abs() < 1e-12, "unbesucht #2 bekommt v_mix");
        assert!((cq[1].1 - cq[2].1).abs() < 1e-12, "alle unbesuchten Kandidaten teilen denselben v_mix");
    }

    // ── PREREG_implicit_minimax_backup.md par.1: Implicit-Minimax-Backups ──

    #[test]
    fn mix_q_with_implicit_minimax_is_identity_at_alpha_zero() {
        // Abnahmekriterium: alpha=0.0 muss q_mc BYTE-IDENTISCH zurueckgeben
        // (exakter Vergleich, keine Epsilon-Toleranz).
        assert_eq!(mix_q_with_implicit_minimax(0.37, 0.91, 0.0), 0.37);
        assert_eq!(mix_q_with_implicit_minimax(0.0, 1.0, 0.0), 0.0);
    }

    #[test]
    fn mix_q_with_implicit_minimax_blends_at_nonzero_alpha() {
        // alpha=0.5: Q = 0.5*q_mc + 0.5*v_im -- Hand-Rechnung.
        let got = mix_q_with_implicit_minimax(0.2, 0.8, 0.5);
        assert!((got - 0.5).abs() < 1e-12, "got={got}, erwartet 0.5");
    }

    #[test]
    fn update_im_value_backup_picks_the_movers_best_visited_child_full_vector() {
        // Wurzel zieht Spieler 0 (mover). Zwei besuchte Kinder mit
        // unterschiedlichem im_value[0] -- die Wurzel muss den VOLLEN Vektor
        // des fuer Spieler 0 besseren Kindes uebernehmen (nicht nur die
        // eigene Komponente, siehe `update_im_value_backup`-Doku: der Zug
        // legt beide Spielerwerte fest, nicht nur den des Ziehers).
        let root = gumbel_test_node(0.0, 0, 0.0, 0);
        let mut child_a = gumbel_test_node(0.5, 1, 0.0, 1);
        child_a.im_value = [0.2, 0.8];
        let mut child_b = gumbel_test_node(0.5, 1, 0.0, 1);
        child_b.im_value = [0.9, 0.1];
        let mut nodes = vec![root, child_a, child_b];
        nodes[0].children.push(1);
        nodes[0].children.push(2);
        update_im_value_backup(&mut nodes, 0);
        assert_eq!(nodes[0].im_value, [0.9, 0.1], "Spieler 0 (Zieher an der Wurzel) waehlt Kind B (0.9 > 0.2)");
    }

    #[test]
    fn update_im_value_backup_ignores_unvisited_children() {
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.im_value = [0.5, 0.5];
        let mut child_unvisited = gumbel_test_node(0.5, 0, 0.0, 1); // visits=0
        child_unvisited.im_value = [0.99, 0.01]; // waere fuer Spieler 0 die beste Wahl -- darf NICHT zaehlen
        let mut nodes = vec![root, child_unvisited];
        nodes[0].children.push(1);
        update_im_value_backup(&mut nodes, 0);
        assert_eq!(
            nodes[0].im_value,
            [0.5, 0.5],
            "unbesuchtes Kind darf den Minimax nicht beeinflussen -- Wurzelwert bleibt der Blattwert"
        );
    }

    #[test]
    fn backprop_path_updates_visits_value_and_im_value_together() {
        // End-zu-Ende-Test des additiven Backup-Kerns: EIN Aufruf muss
        // Bestandsverhalten (`visits`/`value`) UND die neue `im_value`-
        // Fortpflanzung entlang desselben Pfads leisten. Bestandskonvention
        // (unveraendert, siehe `backprop_path`): `value` ist der Blattwert
        // DES BESUCHTEN BLATTS (hier: `child`), NICHT der jeweils eigene
        // `leaf_value` jedes Vorfahrenknotens -- root.leaf_value bleibt daher
        // in dieser Rechnung ungenutzt (nur fuer root's EIGENE Knotenerzeugung
        // relevant, hier irrelevant, siehe Kommentar unten).
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0); // player_who_acted default 0
        root.leaf_value = [0.9, 0.1]; // bewusst ANDERS als child, um die Bestandskonvention zu belegen
        root.im_value = [0.9, 0.1];
        let mut child = gumbel_test_node(0.5, 0, 0.0, 1);
        child.player_who_acted = 0; // root's Mover hat diesen Zug gewaehlt
        child.leaf_value = [0.3, 0.7];
        child.im_value = [0.3, 0.7];
        let mut nodes = vec![root, child];
        nodes[0].children.push(1);
        nodes[1].parent = Some(0); // gumbel_test_node setzt parent immer auf None
        backprop_path(&mut nodes, 1);
        assert_eq!(nodes[1].visits, 1);
        assert!((nodes[1].value - 0.3).abs() < 1e-12, "Kind-Backprop: value[player_who_acted=0]=0.3");
        assert_eq!(nodes[1].im_value, [0.3, 0.7], "Blatt ohne eigene Kinder: im_value bleibt der Blattwert");
        assert_eq!(nodes[0].visits, 1);
        assert!(
            (nodes[0].value - 0.3).abs() < 1e-12,
            "Wurzel-Backprop verwendet DES BLATTS leaf_value[player_who_acted=0]=0.3, NICHT root.leaf_value"
        );
        assert_eq!(
            nodes[0].im_value,
            [0.3, 0.7],
            "Wurzel hat genau ein besuchtes Kind -- dessen im_value wird trivial uebernommen"
        );
    }

    #[test]
    fn completed_q_per_candidate_mixed_matches_plain_at_alpha_zero() {
        // Abnahmekriterium 4b (Byte-/Ergebnis-Identitaet bei alpha=0).
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.leaf_value = [0.5, 0.5];
        let mut child_a = gumbel_test_node(0.6, 4, 2.4, 1); // Q_MC=0.6
        child_a.im_value = [0.99, 0.01]; // deutlich abweichend -- darf bei alpha=0 NICHT wirken
        let mut nodes = vec![root, child_a];
        nodes[0].children.push(1);
        nodes[0].untried.push((Action::Pass, 0.1));
        let plain = completed_q_per_candidate(&nodes, 0);
        let mixed = completed_q_per_candidate_mixed(&nodes, 0, 0.0);
        assert_eq!(plain, mixed, "alpha=0.0 muss byte-identisch zur ungemischten Funktion sein");
    }

    #[test]
    fn completed_q_per_candidate_mixed_differs_from_plain_at_nonzero_alpha() {
        // Abnahmekriterium 4a (Wirkungsnachweis): bei alpha=0.5 UND
        // im_value != Q_MC muss sich die gemischte Selektions-Q sichtbar vom
        // reinen Q_MC unterscheiden.
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0); // Wurzel-Mover = Spieler 0
        root.leaf_value = [0.5, 0.5];
        let mut child_a = gumbel_test_node(0.6, 4, 2.4, 1); // Q_MC=0.6
        child_a.im_value = [0.9, 0.1]; // Perspektive Spieler 0 (Wurzel-Mover): 0.9
        let mut nodes = vec![root, child_a];
        nodes[0].children.push(1);
        let plain = completed_q_per_candidate(&nodes, 0);
        let mixed = completed_q_per_candidate_mixed(&nodes, 0, 0.5);
        assert!((plain[0].1 - 0.6).abs() < 1e-12);
        let expected_mixed = 0.5 * 0.6 + 0.5 * 0.9;
        assert!((mixed[0].1 - expected_mixed).abs() < 1e-12, "mixed={} expected={}", mixed[0].1, expected_mixed);
        assert!((mixed[0].1 - plain[0].1).abs() > 1e-9, "Mischung muss die Selektions-Q sichtbar veraendern");
    }

    // ── PREREG_denial_tiebreak.md (Task E3): Perspektiv-Logik ───────────────

    #[test]
    fn opp_points_forecast_uses_own_opp_head_when_child_mover_equals_root_player() {
        // Zug wechselt NICHT (Kind-Zieher == root_player, z.B. ein
        // Mehrschritt-Zug ohne switch_player()): das Kind bewertet mit
        // `points_forecast` weiterhin root_player's EIGENE Punkte -- der
        // Gegner-Wert steckt im Kind-eigenen `opp_points_forecast`.
        let root_player = 0;
        let mut root = gumbel_test_node(0.0, 0, 0.0, root_player);
        root.opp_points_forecast = Some(0.0); // nur fuer den Kopf-Praesenz-Check relevant
        let mut child = gumbel_test_node(0.5, 1, 0.5, root_player); // Kind-Zieher == root_player
        child.points_forecast = Some(0.9); // waere root_player's EIGENE Punkte -- NICHT verwenden
        child.opp_points_forecast = Some(0.3); // root_player's GEGNER -- das gesuchte Ergebnis
        let nodes = vec![root, child];
        let got = opp_points_forecast_from_root_perspective(&nodes, root_player, 1).expect("Wert vorhanden");
        assert!((got - 0.3).abs() < 1e-6, "got={got}, erwartet 0.3 (opp_points_forecast des Kindes)");
    }

    #[test]
    fn opp_points_forecast_uses_own_points_head_when_child_mover_is_the_opponent() {
        // Normalfall: Zug wechselt (Kind-Zieher == 1-root_player). Das Kind
        // bewertet mit seinem EIGENEN `points_forecast` bereits die Punkte
        // SEINES Ziehers, also des Wurzel-GEGNERS -- direkt verwenden.
        let root_player = 0;
        let mut root = gumbel_test_node(0.0, 0, 0.0, root_player);
        root.opp_points_forecast = Some(0.0);
        let mut child = gumbel_test_node(0.5, 1, 0.5, 1 - root_player); // Kind-Zieher == Gegner
        child.points_forecast = Some(0.4); // Gegners EIGENE Punkte -- das gesuchte Ergebnis
        child.opp_points_forecast = Some(0.9); // waere hier faelschlich root_player's EIGENE Punkte
        let nodes = vec![root, child];
        let got = opp_points_forecast_from_root_perspective(&nodes, root_player, 1).expect("Wert vorhanden");
        assert!((got - 0.4).abs() < 1e-6, "got={got}, erwartet 0.4 (points_forecast des Kindes)");
    }

    #[test]
    fn opp_points_forecast_is_none_when_the_needed_head_is_missing_on_the_child() {
        // Zug wechselt (braucht `points_forecast`), aber genau der fehlt am
        // Kind -- KEIN Rueckfall auf `opp_points_forecast` (der waere hier
        // die FALSCHE Perspektive), stattdessen `None`.
        let root_player = 0;
        let root = gumbel_test_node(0.0, 0, 0.0, root_player);
        let mut child = gumbel_test_node(0.5, 1, 0.5, 1 - root_player);
        child.points_forecast = None;
        child.opp_points_forecast = Some(0.7);
        let nodes = vec![root, child];
        assert_eq!(opp_points_forecast_from_root_perspective(&nodes, root_player, 1), None);
    }

    // ── PREREG_denial_tiebreak.md (Task E3): Tie-Break-Kern ─────────────────
    //
    // Alle Kern-Tests bauen dieselbe Zwei-Kind-Wurzel (Normalfall: Kinder
    // wechseln den Zieher, siehe `opp_points_forecast_uses_own_points_head_
    // when_child_mover_is_the_opponent` oben) und variieren nur `eps`/die
    // Kandidaten-Werte -- `apply_denial_tiebreak_with` ist der reine,
    // env-freie Entscheidungskern (siehe dessen Doku), direkt testbar.
    //
    // Gemeinsamer Zaehler-Zugriff (`note_denial_tiebreak`/`denial_tiebreak_
    // stats`) ist prozessweit -- ein Mutex serialisiert wenigstens diese
    // Testgruppe untereinander, gleiches Kompromiss-Muster wie
    // `AGGRESSION_TEST_LOCK` weiter unten.
    static DENIAL_TIEBREAK_TEST_LOCK: std::sync::Mutex<()> = std::sync::Mutex::new(());

    /// Baut Wurzel (current_player=0, opp-Kopf vorhanden) + zwei Kinder
    /// (current_player=1, Normalfall) mit fest verdrahteten `(Q, points_
    /// forecast)`-Paaren -- `nodes[1]`/`nodes[2]` sind Kandidat A/B.
    fn denial_tiebreak_test_nodes(q_a: f64, opp_a: f32, q_b: f64, opp_b: f32) -> Vec<Node> {
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.opp_points_forecast = Some(0.0); // Kopf-Praesenz-Check
        root.children = vec![1, 2];
        let mut child_a = gumbel_test_node(0.5, 10, q_a * 10.0, 1);
        child_a.points_forecast = Some(opp_a);
        let mut child_b = gumbel_test_node(0.5, 10, q_b * 10.0, 1);
        child_b.points_forecast = Some(opp_b);
        vec![root, child_a, child_b]
    }

    #[test]
    fn denial_tiebreak_eps_zero_returns_baseline_unchanged_byte_identical() {
        let _guard = DENIAL_TIEBREAK_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        reset_denial_tiebreak_stats();
        // B waere bei jedem eps>0 der Gewinner (gleiches Q, viel niedrigere
        // Gegner-Punkte) -- bei eps=0.0 MUSS trotzdem exakt `baseline`
        // zurueckkommen (Bestandsverhalten, kein Vergleich stattgefunden).
        let nodes = denial_tiebreak_test_nodes(0.6, 0.5, 0.6, 0.1);
        assert_eq!(apply_denial_tiebreak_with(&nodes, 1, 0.0), 1);
        assert_eq!(denial_tiebreak_stats(), (0, 0), "eps=0.0 darf die Zaehler nicht anfassen");
        reset_denial_tiebreak_stats();
    }

    #[test]
    fn denial_tiebreak_swaps_to_lower_opp_points_inside_the_window() {
        let _guard = DENIAL_TIEBREAK_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        reset_denial_tiebreak_stats();
        // A: Q=0.60 (Basis), Gegner-Punkte 0.5. B: Q=0.58 (innerhalb eps=0.05
        // um 0.60), Gegner-Punkte 0.1 (niedriger) -- B muss gewinnen.
        let nodes = denial_tiebreak_test_nodes(0.6, 0.5, 0.58, 0.1);
        assert_eq!(apply_denial_tiebreak_with(&nodes, 1, 0.05), 2);
        assert_eq!(denial_tiebreak_stats(), (1, 1), "ein Feuern von einer Gesamtauswertung");
        reset_denial_tiebreak_stats();
    }

    #[test]
    fn denial_tiebreak_ignores_candidates_outside_the_window() {
        let _guard = DENIAL_TIEBREAK_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        reset_denial_tiebreak_stats();
        // Wie oben, aber B liegt mit Q=0.50 ausserhalb des eps=0.05-Fensters
        // um 0.60 -- trotz niedrigerer Gegner-Punkte bleibt die Basis A.
        let nodes = denial_tiebreak_test_nodes(0.6, 0.5, 0.50, 0.1);
        assert_eq!(apply_denial_tiebreak_with(&nodes, 1, 0.05), 1);
        assert_eq!(denial_tiebreak_stats(), (0, 1), "kein Feuern, aber EINE Gesamtauswertung");
        reset_denial_tiebreak_stats();
    }

    #[test]
    fn denial_tiebreak_single_child_returns_baseline_unchanged() {
        let _guard = DENIAL_TIEBREAK_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        reset_denial_tiebreak_stats();
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.opp_points_forecast = Some(0.0);
        root.children = vec![1];
        let mut only_child = gumbel_test_node(0.5, 10, 6.0, 1);
        only_child.points_forecast = Some(0.9);
        let nodes = vec![root, only_child];
        assert_eq!(apply_denial_tiebreak_with(&nodes, 1, 0.5), 1, "einziger Kandidat bleibt Basis");
        assert_eq!(denial_tiebreak_stats(), (0, 1));
        reset_denial_tiebreak_stats();
    }

    #[test]
    fn denial_tiebreak_missing_opp_head_is_inert_and_does_not_touch_counters() {
        let _guard = DENIAL_TIEBREAK_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        reset_denial_tiebreak_stats();
        let mut nodes = denial_tiebreak_test_nodes(0.6, 0.5, 0.58, 0.1);
        nodes[0].opp_points_forecast = None; // Legacy-Netz ohne opp_points-Kopf
        assert_eq!(apply_denial_tiebreak_with(&nodes, 1, 0.05), 1, "inert -> Basis unveraendert");
        assert_eq!(denial_tiebreak_stats(), (0, 0), "kein Kopf -> gar keine Auswertung gezaehlt");
        reset_denial_tiebreak_stats();
    }

    // ── PREREG_denial_tiebreak.md, Abschnitt "E3b": reines Qualifikations-
    // kriterium (`denial_uncert_qualifies`) -- Tests (a)-(e) aus dem
    // Implementierungsauftrag, direkt auf der reinen Funktion (kein Node-
    // Fixture noetig, kein Env-/Zaehler-Zugriff).

    #[test]
    fn denial_uncert_qualifies_rejects_candidate_with_too_few_visits() {
        // (a) Besuchs-Gate greift VOR dem Unsicherheits-Fenster: n_a=40 <
        // 0.5*100=50 -- disqualifiziert, OBWOHL q_a==q_b (das Fenster selbst
        // waere trivial erfuellt).
        assert!(!denial_uncert_qualifies(40.0, 0.6, 100.0, 0.6, 1.0, 0.5));
    }

    #[test]
    fn denial_uncert_qualifies_accepts_candidate_inside_the_se_window() {
        // (b) n_a=n_b=100 (Besuchs-Gate erfuellt), q_a=0.55, q_b=0.6, z=1.0:
        // Q_pool=(0.55+0.6)/2=0.575, SE=sqrt(0.575*0.425*(1/100+1/100))
        // =sqrt(0.0048875)=0.069911..., q_b-q_a=0.05 <= 1.0*SE -- qualifiziert.
        assert!(denial_uncert_qualifies(100.0, 0.55, 100.0, 0.6, 1.0, 0.5));
    }

    #[test]
    fn denial_uncert_qualifies_rejects_candidate_outside_the_se_window() {
        // (c) Gleiche Besuchszahlen wie (b), aber q_a=0.4 (deutlich
        // schlechter): Q_pool=0.5, SE=sqrt(0.5*0.5*0.02)=0.070711...,
        // q_b-q_a=0.2 liegt klar ausserhalb -- nicht qualifiziert.
        assert!(!denial_uncert_qualifies(100.0, 0.4, 100.0, 0.6, 1.0, 0.5));
    }

    #[test]
    fn denial_uncert_qualifies_with_z_zero_only_the_winner_itself_qualifies() {
        // (d) z=0.0 kollabiert das Fenster auf `q_b-q_a<=0`: ein schwaecherer
        // Kandidat (q_a<q_b) qualifiziert NIE, nur der Sieger im Vergleich mit
        // sich selbst (q_a==q_b) -- "aus", exakt wie bei E3s eps=0.
        assert!(!denial_uncert_qualifies(100.0, 0.55, 100.0, 0.6, 0.0, 0.5));
        assert!(denial_uncert_qualifies(100.0, 0.6, 100.0, 0.6, 0.0, 0.5));
    }

    #[test]
    fn denial_uncert_qualifies_handles_zero_visits_and_zero_se_edge_cases() {
        // (e) N=0: `1/n_a`/`1/n_b` waere undefiniert -- Randfall-Regel greift
        // (nur EXAKTE Q-Gleichheit qualifiziert). `min_visit_frac=0.0`, damit
        // das Besuchs-Gate selbst hier nicht schon vorher blockiert (n_a=0 >=
        // 0.0*n_b ist immer wahr).
        assert!(
            !denial_uncert_qualifies(0.0, 0.5, 100.0, 0.6, 1.0, 0.0),
            "n_a=0, Q ungleich -> nicht qualifiziert"
        );
        assert!(
            denial_uncert_qualifies(0.0, 0.6, 100.0, 0.6, 1.0, 0.0),
            "n_a=0, Q gleich -> qualifiziert"
        );
        assert!(
            denial_uncert_qualifies(100.0, 0.5, 0.0, 0.5, 1.0, 0.0),
            "n_b=0, Q gleich -> qualifiziert"
        );
        // SE=0 auch ueber den Q_pool-Rand erreichbar (n_a=n_b=100, beide Q=1.0
        // -> Q_pool exakt 1.0 -> SE=0), NICHT ueber N=0 -- andere Ursache,
        // gleiche Randfall-Regel.
        assert!(
            denial_uncert_qualifies(100.0, 1.0, 100.0, 1.0, 1.0, 0.5),
            "Q_pool=1.0 => SE=0, aber Q gleich -> qualifiziert"
        );
    }

    // ── PREREG_denial_tiebreak.md, Abschnitt "E3b": Konfigurations-Konflikt
    // (E3 UND E3b gleichzeitig aktiv) -- reine Guard-Funktion, bewusst OHNE
    // die echten `denial_tiebreak_eps()`/`denial_uncert_z()`-OnceLocks
    // anzufassen (siehe deren Doku-Warnung vor Test-Kontamination).

    #[test]
    #[should_panic(expected = "MOSAIC_DENIAL_TIEBREAK_EPS")]
    fn denial_tiebreak_config_panics_when_both_mechanisms_are_set() {
        assert_denial_tiebreak_config_not_conflicting(0.01, 1.0);
    }

    #[test]
    fn denial_tiebreak_config_allows_either_mechanism_alone_or_neither() {
        assert_denial_tiebreak_config_not_conflicting(0.0, 0.0); // beide aus
        assert_denial_tiebreak_config_not_conflicting(0.01, 0.0); // nur E3
        assert_denial_tiebreak_config_not_conflicting(0.0, 1.0); // nur E3b
        // Kein Panic bis hierher = Testerfolg.
    }

    // ── PREREG_denial_tiebreak.md, Abschnitt "E3b": `apply_denial_tiebreak_
    // uncert_with` End-zu-End auf echten `Node`-Fixtures (Verdrahtung von
    // Besuchs-Gate + SE-Fenster + Perspektiven-Logik + Debug-Zaehler) --
    // gleiches Lock-/Reset-Muster wie die E3-Kern-Tests oben.

    /// Wie `denial_tiebreak_test_nodes`, aber mit KONFIGURIERBAREN
    /// Besuchszahlen je Kandidat (E3b braucht das Besuchs-Gate, E3 nicht --
    /// dort waren die Besuche daher auf einen festen Wert verdrahtet).
    fn denial_tiebreak_uncert_test_nodes(
        q_a: f64,
        n_a: u32,
        opp_a: f32,
        q_b: f64,
        n_b: u32,
        opp_b: f32,
    ) -> Vec<Node> {
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.opp_points_forecast = Some(0.0); // Kopf-Praesenz-Check
        root.children = vec![1, 2];
        let mut child_a = gumbel_test_node(0.5, n_a, q_a * n_a as f64, 1);
        child_a.points_forecast = Some(opp_a);
        let mut child_b = gumbel_test_node(0.5, n_b, q_b * n_b as f64, 1);
        child_b.points_forecast = Some(opp_b);
        vec![root, child_a, child_b]
    }

    #[test]
    fn denial_tiebreak_uncert_z_zero_returns_baseline_unchanged_byte_identical() {
        let _guard = DENIAL_TIEBREAK_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        reset_denial_tiebreak_stats();
        // B waere bei jedem z>0 (weites Fenster, gleiche Besuche) der Gewinner
        // (gleiches Q, viel niedrigere Gegner-Punkte) -- bei z=0.0 MUSS
        // trotzdem exakt `baseline` zurueckkommen, keine Zaehler-Buchung.
        let nodes = denial_tiebreak_uncert_test_nodes(0.6, 100, 0.5, 0.6, 100, 0.1);
        assert_eq!(apply_denial_tiebreak_uncert_with(&nodes, 1, 0.0, 0.5), 1);
        assert_eq!(denial_tiebreak_stats(), (0, 0), "z=0.0 darf die Zaehler nicht anfassen");
        reset_denial_tiebreak_stats();
    }

    #[test]
    fn denial_tiebreak_uncert_swaps_to_lower_opp_points_inside_the_se_window() {
        let _guard = DENIAL_TIEBREAK_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        reset_denial_tiebreak_stats();
        // A (Basis): Q=0.6, N=100, Gegner-Punkte 0.5. B: Q=0.55 (innerhalb des
        // z=1.0-SE-Fensters, siehe `denial_uncert_qualifies_accepts_candidate_
        // inside_the_se_window`), N=100 (Besuchs-Gate erfuellt), Gegner-Punkte
        // 0.1 -- B muss gewinnen.
        let nodes = denial_tiebreak_uncert_test_nodes(0.6, 100, 0.5, 0.55, 100, 0.1);
        assert_eq!(apply_denial_tiebreak_uncert_with(&nodes, 1, 1.0, 0.5), 2);
        assert_eq!(denial_tiebreak_stats(), (1, 1), "ein Feuern von einer Gesamtauswertung");
        reset_denial_tiebreak_stats();
    }

    #[test]
    fn denial_tiebreak_uncert_visit_gate_excludes_low_visit_candidate() {
        let _guard = DENIAL_TIEBREAK_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        reset_denial_tiebreak_stats();
        // B haette (gleiches Q wie A, niedrigere Gegner-Punkte) OHNE
        // Besuchs-Gate gewonnen -- aber N(B)=40 < 0.5*N(A)=50, das Gate
        // blockiert VOR dem SE-Fenster (siehe `denial_uncert_qualifies_
        // rejects_candidate_with_too_few_visits`).
        let nodes = denial_tiebreak_uncert_test_nodes(0.6, 100, 0.5, 0.6, 40, 0.1);
        assert_eq!(apply_denial_tiebreak_uncert_with(&nodes, 1, 1.0, 0.5), 1);
        assert_eq!(denial_tiebreak_stats(), (0, 1), "kein Feuern, aber EINE Gesamtauswertung");
        reset_denial_tiebreak_stats();
    }

    #[test]
    fn denial_tiebreak_uncert_missing_opp_head_is_inert_and_does_not_touch_counters() {
        let _guard = DENIAL_TIEBREAK_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        reset_denial_tiebreak_stats();
        let mut nodes = denial_tiebreak_uncert_test_nodes(0.6, 100, 0.5, 0.55, 100, 0.1);
        nodes[0].opp_points_forecast = None; // Legacy-Netz ohne opp_points-Kopf
        assert_eq!(apply_denial_tiebreak_uncert_with(&nodes, 1, 1.0, 0.5), 1, "inert -> Basis unveraendert");
        assert_eq!(denial_tiebreak_stats(), (0, 0), "kein Kopf -> gar keine Auswertung gezaehlt");
        reset_denial_tiebreak_stats();
    }

    // ── PREREG_opponent_disruption_v2.md §5.2: Stoerfenster-Zaehlmodus ──────
    //
    // Aufbau aller drei Tests: Wurzel mit Spieler 0 am Zug, der GEGNER
    // (Spieler 1) hat eine begonnene Rot-Reihe mit 2 offenen Plaetzen
    // (akuter Bedarf Rot = 2, Blau = 0). Fabrik 1 bietet 2x Rot und 1x Blau.
    // Basiszug nimmt Blau (stoert nicht), Kandidat nimmt Rot (stoert).

    static COLOR_DENIAL_PROBE_TEST_LOCK: std::sync::Mutex<()> = std::sync::Mutex::new(());

    fn probe_stone(state: &GameState, color: crate::tile::TileColor, row: i32) -> Action {
        Action::Stone(crate::moves::Move {
            take: crate::moves::TakeAction {
                source: TakeSource::SmallFactorySun,
                color,
                factory_id: Some(state.factories[0].factory_id),
                moon_order: Vec::new(),
            },
            place: crate::moves::PlaceAction { row_index: row },
        })
    }

    /// Wurzel + zwei Kinder mit identischem Q/Besuch (Fenster qualifiziert
    /// sicher), Basiszug `nodes[1]` = Blau, Kandidat `nodes[2]` = Rot in
    /// Reihe `kandidat_row`.
    fn probe_test_nodes(kandidat_row: i32) -> Vec<Node> {
        use crate::tile::TileColor::{Blau, Rot};
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.state.factories[0].sun_tiles = vec![Rot, Rot, Blau];
        // Gegner (Spieler 1): begonnene Rot-Reihe der Kapazitaet 3 -> 2 offen.
        root.state.players[1].pattern_lines[2].color = Some(Rot);
        root.state.players[1].pattern_lines[2].tiles = vec![Rot];
        let basis_action = probe_stone(&root.state, Blau, 5);
        let kandidat_action = probe_stone(&root.state, Rot, kandidat_row);
        root.children = vec![1, 2];
        let mut basis = gumbel_test_node(0.5, 10, 6.0, 1); // Q = 0.6
        basis.action = Some(basis_action);
        let mut kandidat = gumbel_test_node(0.5, 10, 6.0, 1); // Q = 0.6, gleichwertig
        kandidat.action = Some(kandidat_action);
        vec![root, basis, kandidat]
    }

    #[test]
    fn color_denial_probe_z_zero_counts_nothing() {
        let _guard = COLOR_DENIAL_PROBE_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        reset_color_denial_probe_stats();
        let nodes = probe_test_nodes(5);
        color_denial_probe_with(&nodes, 1, 0.0, 0.5);
        assert_eq!(color_denial_probe_stats(), (0, 0, 0), "z=0 darf keinen Zaehler anfassen");
        reset_color_denial_probe_stats();
    }

    #[test]
    fn color_denial_probe_counts_windows_and_disruptability() {
        let _guard = COLOR_DENIAL_PROBE_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        reset_color_denial_probe_stats();
        // Kandidat legt 2x Rot in Reihe 6 (Kapazitaet 6, leer) -> kein
        // Ueberlauf, Stoerwirkung min(2, Bedarf 2) = 2 > Basis 0.
        let nodes = probe_test_nodes(5);
        color_denial_probe_with(&nodes, 1, 1.0, 0.5);
        assert_eq!(color_denial_probe_stats(), (1, 1, 1), "Fenster offen UND stoerbar");
        reset_color_denial_probe_stats();
    }

    #[test]
    fn color_denial_probe_rejects_disruption_move_that_fills_the_floor_line() {
        let _guard = COLOR_DENIAL_PROBE_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        reset_color_denial_probe_stats();
        // GEGENPROBE zum Test darueber -- einzige Aenderung: Zielreihe 1
        // (Kapazitaet 1) statt 6. Dieselben 2 Rot-Fliesen erzeugen jetzt 1
        // Ueberlauf gegen 0 des Basiszugs; der Ueberlauf-Filter (PREREG §3,
        // korrigiert in §9.6) muss den Kandidaten verwerfen. Das Fenster
        // bleibt offen -- nur `stoerbar` faellt weg.
        let nodes = probe_test_nodes(0);
        color_denial_probe_with(&nodes, 1, 1.0, 0.5);
        assert_eq!(
            color_denial_probe_stats(),
            (1, 1, 0),
            "Ueberlauf-Kandidat darf NICHT als stoerbar zaehlen"
        );
        reset_color_denial_probe_stats();
    }

    #[test]
    fn improved_policy_sums_to_one_and_matches_hand_example() {
        // Wurzel mit einem besuchten Kind (prior=0.5, Q=0.6, visits=3) und
        // zwei unbesuchten Kandidaten (prior=0.3, prior=0.2). max_N=3.
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.leaf_value = [0.4, 0.6];
        let child = gumbel_test_node(0.5, 3, 1.8, 1); // Q = 1.8/3 = 0.6
        let mut nodes = vec![root, child];
        nodes[0].children.push(1);
        nodes[0].untried.push((Action::Pass, 0.3));
        nodes[0].untried.push((Action::Pass, 0.2));

        let policy = improved_policy(&nodes, 0);
        assert_eq!(policy.len(), 3);
        let total: f64 = policy.iter().sum();
        assert!((total - 1.0).abs() < 1e-9, "Policy muss zu 1.0 summieren, ist {total}");

        // Von Hand nachrechnen: max_N=3, vmix = (0.4 + 3*0.6)/(1+3) = 2.2/4 = 0.55
        let vmix_expected = (0.4 + 3.0 * 0.6) / 4.0;
        let score_child = 0.5f64.ln() + gumbel_sigma(0.6, 3);
        let score_u1 = 0.3f64.ln() + gumbel_sigma(vmix_expected, 3);
        let score_u2 = 0.2f64.ln() + gumbel_sigma(vmix_expected, 3);
        let expected = softmax_f64(&[score_child, score_u1, score_u2]);
        for (a, b) in policy.iter().zip(expected.iter()) {
            assert!((a - b).abs() < 1e-6, "policy={policy:?} expected={expected:?}");
        }
    }

    #[test]
    fn gumbel_select_child_can_pick_a_strongly_preferred_unvisited_candidate_over_existing_children() {
        // Paket 2 (mctx-treue Tiefe-≥1-Auswahl, 2026-07-22): anders als die
        // alte Auswahl (nur ueber `nodes[nid].children`, ein separater
        // Widening-Cap entschied, WANN neue Kandidaten ueberhaupt entstehen
        // duerfen) muss die Auswahl jetzt auch einen bislang UNBESUCHTEN
        // Kandidaten (hoher Prior, N=0) waehlen koennen, selbst wenn ein Kind
        // schon 200 Besuche hat -- `N(a)/(1+ΣN)` bestraft den vielbesuchten
        // Kandidaten irgendwann so stark, dass ein hochpriorisierter, nie
        // besuchter Kandidat gewinnt.
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.leaf_value = [0.5, 0.5];
        let child = gumbel_test_node(0.3, 200, 100.0, 1); // Q = 100/200 = 0.5, stark besucht
        let mut nodes = vec![root, child];
        nodes[0].children.push(1);
        nodes[0].untried.push((Action::Pass, 0.65)); // deutlich hoeherer Prior, N=0

        let idx = gumbel_select_child(&nodes, 0, &SearchConfig::from_env());
        assert_eq!(
            idx, 1,
            "Kombi-Index 1 (= der einzige untried-Kandidat, nach 1 Kind) haette gewaehlt werden muessen, war {idx}"
        );
    }

    /// PREREG_agent_encapsulation.md par.4 Punkt 4 (Pilot-Migration): der
    /// KRONZEUGE-Test, der mit dem alten prozessweiten OnceLock unmoeglich
    /// war (siehe Kommentar an `read_f64_env_implicit_minimax_a_default_and_
    /// parsing` oben) -- ZWEI `SearchConfig`-Werte mit unterschiedlichem
    /// `implicit_minimax_alpha` liefern im SELBEN Prozess, auf DEMSELBEN
    /// Knotensatz, unterschiedliche `gumbel_select_child`-Ergebnisse. Baut
    /// eine Situation, in der die Implicit-Minimax-Beimischung tatsaechlich
    /// etwas aendert: ein besuchtes Kind mit hohem `value/visits`, aber
    /// niedrigem `im_value` (die Minimax-Rueckpropagation "weiss" bereits,
    /// dass der Zweig fuer den Zieher schlecht endet) -- bei `alpha=0` zaehlt
    /// nur `value/visits`, bei hohem `alpha` dominiert `im_value`.
    #[test]
    fn search_config_with_different_alpha_in_same_process_yields_different_selection() {
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.leaf_value = [0.5, 0.5];
        // Kind A: hoher MC-Q (0.9), aber niedriger im_value (0.1) -- Minimax
        // hat den Zweig schon als schlecht erkannt.
        let mut child_a = gumbel_test_node(0.5, 10, 9.0, 1); // Q = 9/10 = 0.9
        child_a.im_value = [0.1, 0.9];
        // Kind B: niedriger MC-Q (0.5), aber hoher im_value (0.9).
        let mut child_b = gumbel_test_node(0.5, 10, 5.0, 1); // Q = 5/10 = 0.5
        child_b.im_value = [0.9, 0.1];
        let mut nodes = vec![root, child_a, child_b];
        nodes[0].children.push(1);
        nodes[0].children.push(2);

        let cfg_off = SearchConfig { implicit_minimax_alpha: 0.0, long_row_init_shaping_w: 0.0 };
        let cfg_on = SearchConfig { implicit_minimax_alpha: 1.0, long_row_init_shaping_w: 0.0 };
        let idx_off = gumbel_select_child(&nodes, 0, &cfg_off);
        let idx_on = gumbel_select_child(&nodes, 0, &cfg_on);
        assert_ne!(
            idx_off, idx_on,
            "zwei SearchConfig-Werte im selben Prozess muessen unterschiedliche Selektion ergeben \
             (idx_off={idx_off} idx_on={idx_on}) -- genau das war mit dem alten OnceLock nicht pruefbar"
        );
    }

    // `SearchConfig::from_env()` liest den ECHTEN Produktions-Env-Namen
    // (`MOSAIC_IMPLICIT_MINIMAX_A`, anders als `read_f64_env_*`-Tests, die
    // bewusst synthetische Namen nutzen) UND cacht NICHTS mehr (siehe
    // `SearchConfig::from_env`-Doku) -- ein Mutex serialisiert die beiden
    // folgenden Tests untereinander, gleiches Kompromiss-Muster wie
    // `DENIAL_TIEBREAK_TEST_LOCK`/`AGGRESSION_TEST_LOCK`.
    static SEARCH_CONFIG_ENV_TEST_LOCK: std::sync::Mutex<()> = std::sync::Mutex::new(());

    // ── Langreihen-Initiierungs-Additiv (PREREG_long_row_payoff.md par.3/B1) ──

    /// `long_rows_started` ist eine STUFENFUNKTION: ein Stein zaehlt genauso
    /// wie eine fast volle Reihe. Genau das unterscheidet den Term vom
    /// urspruenglich entworfenen Fortschritts-Term -- par.2a hat gemessen,
    /// dass die Luecke im BEGINNEN sitzt, nicht im Fuellen.
    #[test]
    fn long_rows_started_is_a_step_function_not_a_ramp() {
        use crate::tile::TileColor;
        let mut p = crate::board::PlayerBoard::new(0, "P");
        assert_eq!(long_rows_started(&p), 0.0, "leeres Brett: keine begonnene lange Reihe");

        // EIN Stein in Musterreihe 5 (Index 4).
        p.pattern_lines[4].tiles.push(TileColor::Rot);
        assert_eq!(long_rows_started(&p), 1.0);

        // Dieselbe Reihe fast voll -> UNVERAENDERT 1.0 (kein Rampenanteil).
        for _ in 0..3 {
            p.pattern_lines[4].tiles.push(TileColor::Rot);
        }
        assert_eq!(
            long_rows_started(&p), 1.0,
            "Fuellstand darf den Term NICHT bewegen -- sonst waere es der              verworfene Fortschritts-Term"
        );

        // Zweite lange Reihe (Index 5) begonnen -> 2.0.
        p.pattern_lines[5].tiles.push(TileColor::Blau);
        assert_eq!(long_rows_started(&p), 2.0);

        // Kurze Reihen zaehlen NICHT mit.
        p.pattern_lines[0].tiles.push(TileColor::Gelb);
        p.pattern_lines[2].tiles.push(TileColor::Gelb);
        assert_eq!(long_rows_started(&p), 2.0, "nur Musterreihe 5/6 zaehlen");
    }

    /// Der Term ist NULLSUMMEN: `delta(ego=1) == -delta(ego=0)`. Darauf
    /// stuetzt sich die Anwendungsstelle, die nur EIN `tanh` rechnet und das
    /// Ergebnis negiert (IEEE754-Negation ist exakt).
    #[test]
    fn long_row_init_delta_is_zero_sum_between_egos() {
        use crate::tile::TileColor;
        let mut state = crate::game::Game::start(
            ["A".into(), "B".into()], 0, vec![0, 1, 2], &mut rand::rngs::StdRng::seed_from_u64(7),
        ).state;
        state.players[0].pattern_lines[4].tiles.push(TileColor::Rot);
        state.players[0].pattern_lines[5].tiles.push(TileColor::Rot);
        let d0 = long_row_init_delta(&state, 0);
        let d1 = long_row_init_delta(&state, 1);
        assert_eq!(d0, 2.0 / LONG_ROW_INIT_SHAPING_SCALE);
        assert_eq!(d1, -d0, "Nullsummen-Eigenschaft haelt");
    }

    /// Die Skala ist bewusst 10 und NICHT 50: der maximale Blattwert-Shift
    /// soll dem Floor-Term entsprechen (PREREG_floor_shaping_scale.md par.2).
    /// Bricht dieser Test, wurde die Konstante geaendert, ohne die
    /// Begruendung nachzuziehen.
    #[test]
    fn long_row_init_scale_matches_floor_term_shift_magnitude() {
        let max_arg = 2.0 / LONG_ROW_INIT_SHAPING_SCALE;
        let shift = 0.3 * max_arg.tanh();
        let floor_max_shift = 0.3 * (10.0f64 / FLOOR_SHAPING_SCALE).tanh();
        assert!(
            (shift - floor_max_shift).abs() < 1e-9,
            "max. Shift {shift} soll dem Floor-Term {floor_max_shift} entsprechen"
        );
    }

    /// Abnahme (a): Default-Pfad -- `MOSAIC_IMPLICIT_MINIMAX_A` ungesetzt
    /// ergibt `alpha=0.0`.
    #[test]
    fn search_config_from_env_defaults_to_zero_alpha() {
        let _guard = SEARCH_CONFIG_ENV_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        std::env::remove_var("MOSAIC_IMPLICIT_MINIMAX_A");
        let cfg = SearchConfig::from_env();
        assert_eq!(cfg.implicit_minimax_alpha, 0.0);
    }

    /// `from_env()` liest wirklich frisch (kein Cache) -- gesetzter Knopf
    /// wirkt sofort, im selben Prozess.
    #[test]
    fn search_config_from_env_reads_set_value() {
        let _guard = SEARCH_CONFIG_ENV_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        let name = "MOSAIC_IMPLICIT_MINIMAX_A";
        let prev = std::env::var(name).ok();
        std::env::set_var(name, "0.3");
        let cfg = SearchConfig::from_env();
        assert_eq!(cfg.implicit_minimax_alpha, 0.3);
        match prev {
            Some(v) => std::env::set_var(name, v),
            None => std::env::remove_var(name),
        }
    }

    /// Eine Spec, die eine NICHT MEHR SPIELBARE Variante verlangt, muss hart
    /// scheitern. Das ist dieselbe Zusage wie vorher, nur unter neuer Lage:
    /// bis zum 2026-08-26 hiess sie "die Spec muss ANKOMMEN" (Anlass: ein
    /// Erzeugerlauf, dessen Aufruf `v2huelle` nicht mitnahm, worauf der
    /// Default v1 still einsprang und ein falscher Befund entstand). Seit
    /// B4a gibt es den v2-Zweig nicht mehr -- ein stilles Durchwinken als v1
    /// waere GENAU derselbe Fehler, nur an einer neuen Stelle.
    ///
    /// Das Artefakt selbst bleibt lauffaehig: es bringt sein eigenes Wheel
    /// mit (`models/frozen_heuristics/v2huelle_generator/`).
    #[test]
    fn search_config_from_spec_file_rejects_v2_variante() {
        let dir = std::env::temp_dir();
        let path = dir.join(format!("mosaic_test_spec_v2_{}.json", std::process::id()));
        std::fs::write(&path, r#"{"implicit_minimax_alpha": 0.0, "long_row_init_shaping_w": 0.0, "heuristik_variante": "v2huelle"}"#).unwrap();
        let result = SearchConfig::from_spec_file(path.to_str().unwrap());
        assert!(result.is_err(), "eine v2-Spec darf in diesem Build NICHT still als v1 laufen");
        let msg = result.unwrap_err();
        assert!(msg.contains("nicht mehr spielbar"), "Fehlermeldung muss den Grund nennen: {msg}");
        assert!(msg.contains("mitgelieferten Wheel"), "Fehlermeldung muss den Ausweg nennen: {msg}");
        std::fs::remove_file(&path).ok();
    }

    /// Ein unbekannter Variantenname ist ein harter Fehler, kein Rueckfall
    /// auf v1. Ein stiller Rueckfall saehe wie der gewollte Lauf aus und
    /// waere der Bestandslauf -- genau der Messfehler vom 2026-08-26.
    #[test]
    fn search_config_from_spec_file_rejects_unknown_variante() {
        let dir = std::env::temp_dir();
        let path = dir.join(format!("mosaic_test_spec_badvariante_{}.json", std::process::id()));
        std::fs::write(&path, r#"{"implicit_minimax_alpha": 0.0, "long_row_init_shaping_w": 0.0, "heuristik_variante": "v2huelle_tippfehler"}"#).unwrap();
        let result = SearchConfig::from_spec_file(path.to_str().unwrap());
        assert!(result.is_err(), "unbekannte Variante muss abgewiesen werden");
        assert!(result.unwrap_err().contains("nicht mehr spielbar"));
        std::fs::remove_file(&path).ok();
    }

    /// Ein FEHLENDES Pflichtfeld ist ebenfalls ein Fehler -- eine Spec legt
    /// das Verhalten VOLLSTAENDIG fest (Welle-1-Regel).
    #[test]
    fn search_config_from_spec_file_requires_heuristik_variante() {
        let dir = std::env::temp_dir();
        let path = dir.join(format!("mosaic_test_spec_novariante_{}.json", std::process::id()));
        std::fs::write(&path, r#"{"implicit_minimax_alpha": 0.0, "long_row_init_shaping_w": 0.0}"#).unwrap();
        let result = SearchConfig::from_spec_file(path.to_str().unwrap());
        assert!(result.is_err(), "fehlende heuristik_variante muss abgewiesen werden");
        std::fs::remove_file(&path).ok();
    }

    /// Abnahme (c): unbekanntes Feld ist ein harter Fehler (kein stilles
    /// Ignorieren -- sonst maskiert ein Tippfehler eine ganze Messung).
    #[test]
    fn search_config_from_spec_file_rejects_unknown_field() {
        let dir = std::env::temp_dir();
        let path = dir.join(format!("mosaic_test_spec_unknown_field_{}.json", std::process::id()));
        std::fs::write(&path, r#"{"implicit_minimax_alpha": 0.2, "long_row_init_shaping_w": 0.0, "tpyo_feld": 1.0}"#).unwrap();
        let result = SearchConfig::from_spec_file(path.to_str().unwrap());
        assert!(result.is_err(), "unbekanntes Feld muss einen Fehler ergeben, nicht still ignoriert werden");
        std::fs::remove_file(&path).ok();
    }

    /// Abnahme (c): fehlende Datei ist ein Fehler.
    #[test]
    fn search_config_from_spec_file_rejects_missing_file() {
        let result = SearchConfig::from_spec_file("does_not_exist_mosaic_spec_probe.json");
        assert!(result.is_err(), "fehlende Spec-Datei muss einen Fehler ergeben");
    }

    #[test]
    fn root_completed_q_policy_pairs_each_action_with_its_own_probability() {
        // Wurzel mit einem besuchten Kind (Action::Pass) und zwei unbesuchten
        // Kandidaten (Action::DrawStackPeek, Action::ChooseDomeRotation(1)) --
        // prueft, dass `root_completed_q_policy` dieselben Zahlen wie
        // `improved_policy` liefert UND korrekt der jeweils richtigen Aktion
        // zuordnet (children zuerst, dann untried, wie `completed_q_per_candidate`).
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.leaf_value = [0.4, 0.6];
        let mut child = gumbel_test_node(0.5, 3, 1.8, 1); // Q = 0.6
        child.action = Some(Action::Pass);
        let mut nodes = vec![root, child];
        nodes[0].children.push(1);
        nodes[0].untried.push((Action::DrawStackPeek, 0.3));
        nodes[0].untried.push((Action::ChooseDomeRotation(1), 0.2));

        let numeric = improved_policy(&nodes, 0);
        let paired = root_completed_q_policy(&nodes);
        assert_eq!(paired.len(), 3);

        let total: f64 = paired.iter().map(|(_, p)| p).sum();
        assert!((total - 1.0).abs() < 1e-9, "Policy muss zu 1.0 summieren, ist {total}");

        assert_eq!(paired[0].0, Action::Pass);
        assert!((paired[0].1 - numeric[0]).abs() < 1e-12);
        assert_eq!(paired[1].0, Action::DrawStackPeek);
        assert!((paired[1].1 - numeric[1]).abs() < 1e-12);
        assert_eq!(paired[2].0, Action::ChooseDomeRotation(1));
        assert!((paired[2].1 - numeric[2]).abs() < 1e-12);
    }

    #[test]
    fn root_completed_q_raw_reports_own_q_for_visited_and_vmix_for_unvisited_in_policy_order() {
        // Task #35 (Ranking-Loss-Vorlauf): gleicher Baum wie im
        // `root_completed_q_policy`-Test oben, aber diesmal wird die ROHE
        // completed-Q gegen die Handrechnung geprueft (nicht die Softmax-
        // Politik) -- UND dass die Aktions-Reihenfolge exakt der von
        // `root_completed_q_policy` entspricht (Voraussetzung dafuer, dass
        // sich `policy`- und `root_child_q`-JSON-Felder in self_play.rs rein
        // positionsbasiert zippen lassen).
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.leaf_value = [0.4, 0.6];
        let mut child = gumbel_test_node(0.5, 3, 1.8, 1); // Q = 1.8/3 = 0.6, besucht
        child.action = Some(Action::Pass);
        let mut nodes = vec![root, child];
        nodes[0].children.push(1);
        nodes[0].untried.push((Action::DrawStackPeek, 0.3));
        nodes[0].untried.push((Action::ChooseDomeRotation(1), 0.2));

        let raw = root_completed_q_raw(&nodes);
        let policy = root_completed_q_policy(&nodes);
        assert_eq!(raw.len(), 3);
        assert_eq!(raw.len(), policy.len());
        for i in 0..raw.len() {
            assert_eq!(raw[i].0, policy[i].0, "Aktions-Reihenfolge muss zu root_completed_q_policy passen");
        }

        // Von Hand: besuchtes Kind traegt sein eigenes Q, unbesuchte Kandidaten
        // TEILEN sich denselben v_mix = (v(root) + N_total*mean_visited_q)/(1+N_total)
        // = (0.4 + 3*0.6)/4 = 0.55 (siehe `v_mix`-Kommentar).
        let vmix_expected = (0.4 + 3.0 * 0.6) / 4.0;
        assert_eq!(raw[0].0, Action::Pass);
        assert!((raw[0].1 - 0.6).abs() < 1e-12, "besuchtes Kind sollte eigenes Q=0.6 tragen, war {}", raw[0].1);
        assert_eq!(raw[1].0, Action::DrawStackPeek);
        assert!((raw[1].1 - vmix_expected).abs() < 1e-12);
        assert_eq!(raw[2].0, Action::ChooseDomeRotation(1));
        assert!((raw[2].1 - vmix_expected).abs() < 1e-12);
        // Q-Werte sind KEINE Wahrscheinlichkeiten -- keine Summe-zu-1-Erwartung
        // (anders als `root_completed_q_policy`).
    }

    // ── ISMCTS-Mehrfach-Determinisierung (Task #65) ─────────────────────────

    #[test]
    fn average_completed_q_policy_averages_matching_actions_across_worlds() {
        // Zwei synthetische "Welten" mit identischem Kandidatensatz (Pass
        // besucht, DrawStackPeek/ChooseDomeRotation(1) unbesucht), aber
        // unterschiedlichen Besuchs-/Wertstatistiken -- prueft, dass
        // `average_completed_q_policy` exakt das arithmetische Mittel der
        // Pro-Welt-`root_completed_q_policy`-Ausgaben liefert (Aktions-
        // Schluessel, siehe `NUM_DETERMINIZATIONS`-Kommentar).
        fn make_world(child_visits: u32, child_value: f64, root_leaf: [f64; 2]) -> Vec<Node> {
            let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
            root.leaf_value = root_leaf;
            let mut child = gumbel_test_node(0.5, child_visits, child_value, 1);
            child.action = Some(Action::Pass);
            let mut nodes = vec![root, child];
            nodes[0].children.push(1);
            nodes[0].untried.push((Action::DrawStackPeek, 0.3));
            nodes[0].untried.push((Action::ChooseDomeRotation(1), 0.2));
            nodes
        }

        let world1 = make_world(3, 1.8, [0.4, 0.6]); // Q_pass = 0.6
        let world2 = make_world(5, 2.0, [0.5, 0.5]); // Q_pass = 0.4
        let p1 = root_completed_q_policy(&world1);
        let p2 = root_completed_q_policy(&world2);
        let forest = vec![world1, world2];

        let averaged = average_completed_q_policy(&forest);
        assert_eq!(averaged.len(), 3);
        let total: f64 = averaged.iter().map(|(_, p)| p).sum();
        assert!((total - 1.0).abs() < 1e-9, "gemittelte Politik muss zu 1.0 summieren, ist {total}");

        for i in 0..3 {
            assert_eq!(averaged[i].0, p1[i].0, "Aktions-Reihenfolge sollte der ersten Welt folgen");
            assert_eq!(averaged[i].0, p2[i].0, "beide Welten sollten denselben Kandidatensatz haben");
            let expected = (p1[i].1 + p2[i].1) / 2.0;
            assert!(
                (averaged[i].1 - expected).abs() < 1e-9,
                "Aktion {:?}: gemittelt={} erwartet={}",
                averaged[i].0,
                averaged[i].1,
                expected
            );
        }
    }

    #[test]
    fn average_completed_q_raw_averages_raw_q_without_renormalizing_to_one() {
        // Task #35: gleiche zwei Welten wie im
        // `average_completed_q_policy`-Mittelungstest oben, diesmal auf der
        // ROHEN completed-Q -- prueft (a) arithmetisches Mittel je Aktion,
        // (b) KEINE Renormierung (Summe muss NICHT 1 sein, anders als bei der
        // Softmax-Politik), (c) Aktions-Reihenfolge identisch zu
        // `average_completed_q_policy` (Voraussetzung fuer positionsbasiertes
        // Zippen von `policy`/`root_child_q` im Self-Play-JSON).
        fn make_world(child_visits: u32, child_value: f64, root_leaf: [f64; 2]) -> Vec<Node> {
            let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
            root.leaf_value = root_leaf;
            let mut child = gumbel_test_node(0.5, child_visits, child_value, 1);
            child.action = Some(Action::Pass);
            let mut nodes = vec![root, child];
            nodes[0].children.push(1);
            nodes[0].untried.push((Action::DrawStackPeek, 0.3));
            nodes[0].untried.push((Action::ChooseDomeRotation(1), 0.2));
            nodes
        }

        let world1 = make_world(3, 1.8, [0.4, 0.6]); // Q_pass = 0.6
        let world2 = make_world(5, 2.0, [0.5, 0.5]); // Q_pass = 0.4
        let r1 = root_completed_q_raw(&world1);
        let r2 = root_completed_q_raw(&world2);
        let forest = vec![world1, world2];

        let averaged_raw = average_completed_q_raw(&forest);
        let averaged_policy = average_completed_q_policy(&forest);
        assert_eq!(averaged_raw.len(), 3);
        assert_eq!(averaged_raw.len(), averaged_policy.len());

        for i in 0..3 {
            assert_eq!(averaged_raw[i].0, r1[i].0);
            assert_eq!(averaged_raw[i].0, r2[i].0);
            assert_eq!(
                averaged_raw[i].0, averaged_policy[i].0,
                "root_child_q und policy muessen dieselbe Aktions-Reihenfolge haben (Index-Zip in self_play.rs)"
            );
            let expected = (r1[i].1 + r2[i].1) / 2.0;
            assert!(
                (averaged_raw[i].1 - expected).abs() < 1e-9,
                "Aktion {:?}: gemittelt={} erwartet={}",
                averaged_raw[i].0,
                averaged_raw[i].1,
                expected
            );
        }
        // Von Hand: v_mix1 = (0.4+3*0.6)/4 = 0.55, v_mix2 = (0.5+5*0.4)/6 = 0.41666...
        // gemittelte Summe = 0.5 (Pass) + 2*0.483333.. (die zwei unbesuchten,
        // teilen sich je Welt denselben v_mix) = 1.46666.. -- explizit WEIT
        // weg von 1.0, zum Nachweis, dass hier (anders als bei der
        // Softmax-Politik) keine Renormierung stattfindet.
        let vmix1 = (0.4 + 3.0 * 0.6) / 4.0;
        let vmix2 = (0.5 + 5.0 * 0.4) / 6.0;
        let expected_sum = (0.6 + 0.4) / 2.0 + 2.0 * ((vmix1 + vmix2) / 2.0);
        let sum: f64 = averaged_raw.iter().map(|(_, q)| q).sum();
        let sum_policy: f64 = averaged_policy.iter().map(|(_, p)| p).sum();
        assert!((sum_policy - 1.0).abs() < 1e-9, "Kontrollwert: Softmax-Politik MUSS zu 1 summieren");
        assert!((sum - expected_sum).abs() < 1e-9, "Summe={sum} erwartet={expected_sum}");
        assert!((sum - 1.0).abs() > 0.1, "rohe completed-Q darf (anders als die Politik) nicht auf 1.0 renormiert sein, Summe={sum}");
    }

    #[test]
    fn aggregate_root_child_stats_sums_visits_and_weighted_averages_q_across_worlds() {
        // Zwei Welten, beide besuchen Action::Pass als Wurzelkind mit
        // unterschiedlichen Besuchs-/Wertsummen -- Erwartung: Besuche werden
        // SUMMIERT (treibt Self-Plays besuchsbasierte Stichprobe ueber die
        // Welten-SUMME), Q = Sigma(Value)/Sigma(Besuche) -- NICHT das
        // einfache arithmetische Mittel der Pro-Welt-Q-Werte.
        fn make_world(child_visits: u32, child_value: f64) -> Vec<Node> {
            let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
            root.leaf_value = [0.5, 0.5];
            let mut child = gumbel_test_node(0.5, child_visits, child_value, 1);
            child.action = Some(Action::Pass);
            let mut nodes = vec![root, child];
            nodes[0].children.push(1);
            nodes
        }
        let world1 = make_world(3, 1.8); // Q=0.6
        let world2 = make_world(5, 2.0); // Q=0.4
        let forest = vec![world1, world2];

        let stats = aggregate_root_child_stats(&forest);
        assert_eq!(stats.len(), 1);
        let (act, visits, q) = &stats[0];
        assert_eq!(*act, Action::Pass);
        assert_eq!(*visits, 8, "Besuche muessen SUMMIERT werden (3+5)");
        let expected_q = (1.8 + 2.0) / 8.0;
        assert!(
            (q - expected_q).abs() < 1e-9,
            "Q={q} erwartet={expected_q} (gewichteter Mittelwert, nicht einfacher Mittelwert der Pro-Welt-Qs)"
        );
    }

    #[test]
    fn split_sims_across_worlds_puts_remainder_on_first_world() {
        assert_eq!(split_sims_across_worlds(150, 3), vec![50, 50, 50]);
        assert_eq!(split_sims_across_worlds(151, 3), vec![51, 50, 50]);
        assert_eq!(split_sims_across_worlds(8, 1), vec![8]);
        assert_eq!(split_sims_across_worlds(7, 5), vec![3, 1, 1, 1, 1]);
    }

    /// Laedt das aktuelle Produktions-Modell fuer die beiden folgenden
    /// Perspektiven-/Vorzeichen-Tests (`evaluations/value head tests.txt`,
    /// Punkt 2, "klassische Vorzeichen-Unit-Tests"). Ueberspringt sich
    /// selbst (statt zu failen), falls die Datei lokal fehlt -- `models/`
    /// ist per `.gitignore` nicht Teil des Checkouts, ein frischer Klon
    /// haette also sonst einen harten Testfehler ohne jeden eigenen Fehler.
    /// Teil-2-Sonde zu `evaluations/PREREG_gpu_offloading.md`: **wie viele
    /// Blaetter je Sekunde kann die CPU erzeugen, wenn die Inferenz nichts
    /// mehr kostet?** Diese Zahl setzt den erreichbaren Batch (Little:
    /// Batch = Erzeugungsrate x GPU-Latenz) und war bisher ungemessen --
    /// ohne sie waere die Batchgroesse beim Bau geraten.
    ///
    /// KEIN Eingriff in die Suche. Statt eines Null-Evaluators im Suchpfad
    /// werden zwei getrennt messbare Groessen verrechnet:
    ///   Baumzeit = Gesamtzeit einer Suche - (Zahl der Evals x Zeit je Eval)
    /// Der Umbau eines Suchpfads fuer eine MESSUNG waere das schlechtere
    /// Werkzeug: er koennte still etwas anderes messen als das Original.
    ///
    /// VORBEHALT, der ins Protokoll gehoert: laeuft parallel eine Arena, sind
    /// beide Absolutwerte durch Kernkonkurrenz nach unten verzerrt. Das
    /// VERHAELTNIS Baum/Inferenz ist robuster, weil beide Seiten gleich
    /// betroffen sind. Vor dem Bau auf leerer Maschine wiederholen.
    #[test]
    #[ignore]
    fn teil2_leaf_generation_rate_probe() {
        use std::time::Instant;
        // Eigener Lader: `load_test_net()` zeigt auf `v10_best`, das es nicht
        // mehr gibt (NUM_ACTIONS-Wechsel hat Alt-Checkpoints entwertet). Hier
        // wird der aktuelle Champion gebraucht, weil die Messung seine
        // Eval-Kosten betrifft.
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../models/alphazero_v21_2d_brierbest.onnx");
        let net = Net::load_auto(path.to_str().unwrap()).unwrap_or_else(|e| panic!(
            "{path:?} nicht ladbar ({e}) -- Sonden-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ));
        let mut seed_rng = StdRng::seed_from_u64(7);
        let state = random_drafting_state(7, 12, &mut seed_rng)
            .expect("kein Drafting-Zustand erzeugbar -- Sonden-Aufbau defekt, nicht still ueberspringen");

        // (1) Zeit je Eval, einzeln und als Paar (der Suchpfad nutzt beides).
        // Dispatch PRO NETZ -- der Champion ist 2D und braucht den
        // kombinierten Planes+Flat-Puffer, nicht den 708er-Flachvektor.
        let feats = crate::features::features_for_net(&net, &state);
        for _ in 0..20 {
            let _ = net.eval(&feats);
        }
        let reps = 200;
        let t0 = Instant::now();
        for _ in 0..reps {
            let _ = net.eval(&feats);
        }
        let per_eval_single = t0.elapsed().as_secs_f64() / reps as f64;

        let t0 = Instant::now();
        for _ in 0..reps {
            let _ = net.eval_pair(&feats, &feats);
        }
        let per_eval_pair = t0.elapsed().as_secs_f64() / (2 * reps) as f64;

        // (2) Gesamtzeit einer vollen Suche und ihre Eval-Zahl.
        let sims = 400u32;
        let mut rng = StdRng::seed_from_u64(4242);
        let t0 = Instant::now();
        let nodes = build_net_tree(
            &net, None, &state, sims, 1.5, false, &mut rng, None, None, &SearchConfig::from_env(),
        );
        let total = t0.elapsed().as_secs_f64();
        let n_nodes = nodes.len() as f64;

        let infer = n_nodes * per_eval_single;
        let tree = (total - infer).max(1e-9);
        let leaves_per_s_now = n_nodes / total;
        let leaves_per_s_free = n_nodes / tree;

        println!("TEIL 2 -- Blatt-Erzeugungsrate");
        println!("  Zeit je Eval: einzeln {:.3} ms, im Paar {:.3} ms",
                 per_eval_single * 1e3, per_eval_pair * 1e3);
        println!("  Suche {sims} Sims: {n_nodes:.0} Knoten in {:.3} s", total);
        println!("  davon Inferenz {:.3} s ({:.0} %), Baumarbeit {:.3} s ({:.0} %)",
                 infer, 100.0 * infer / total, tree, 100.0 * tree / total);
        println!("  Blaetter/s HEUTE (1 Thread):            {leaves_per_s_now:>9.0}");
        println!("  Blaetter/s bei KOSTENLOSER Inferenz:    {leaves_per_s_free:>9.0}");
        for threads in [11usize, 12] {
            let demand = leaves_per_s_free * threads as f64;
            println!("  -> {threads} Threads: Nachfrage {demand:>9.0} Evals/s");
        }
        // Little: erreichbarer Batch = Erzeugungsrate x GPU-Latenz.
        // GPU-Latenz bei Batch B = B / Evals_pro_s(B); gemessene Kennlinie:
        // Batch 128 -> 41.959/s (3,05 ms), 512 -> 162.635/s (3,15 ms).
        for (b, rate) in [(128.0, 41_959.0), (512.0, 162_635.0)] {
            let latency = b / rate;
            let inflight = leaves_per_s_free * 11.0 * latency;
            println!("  -> bei Batch {b:.0} (Latenz {:.2} ms): {inflight:.0} Blaetter gleichzeitig unterwegs",
                     latency * 1e3);
        }
    }

    /// Bis 2026-08-15 zeigte dieser Lader auf `alphazero_v10_best.onnx`, das es
    /// seit dem NUM_ACTIONS-Wechsel nicht mehr gibt, und gab bei Abwesenheit
    /// still `None` -- alle neun abhaengigen Tests liefen seither LEER-GRUEN,
    /// ohne je zu pruefen (Architektur-Fahrplan Punkt 2, Inventar 2026-08-15).
    /// Jetzt: amtierender Champion + harter Fehler statt Skip (Nutzer-Regel:
    /// nie leer gruen; Praezedenz `self_play.rs::load_test_net_for_gating`).
    fn load_test_net() -> Net {
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../models/alphazero_v21_2d_brierbest.onnx");
        Net::load_auto(path.to_str().unwrap()).unwrap_or_else(|e| panic!(
            "{path:?} nicht ladbar ({e}) -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ))
    }

    /// Spielt ein paar zufaellige Drafting-Zuege aus `Game::start` heraus
    /// (kein Tiling -- reicht fuer die Value-Head-Perspektiventests unten,
    /// die nur reale, unterschiedliche Drafting-Stellungen brauchen).
    /// Gibt `None`, falls die Drafting-Phase vor Ablauf der Schritte endet.
    fn random_drafting_state<R: Rng + ?Sized>(seed_tag: u64, steps: u32, rng: &mut R) -> Option<GameState> {
        let ids = crate::scoring::sample_valid_scoring_ids(3, rng);
        let mut game = Game::start(
            [format!("A{seed_tag}"), format!("B{seed_tag}")],
            (seed_tag % 2) as usize,
            ids,
            rng,
        );
        // Startkuppel-Platzierung überspringen -- seit dem R5-Gate
        // (Vollaudit 2026-07-21) lehnt apply_drafting sonst alles ab.
        for p in game.state.players.iter_mut() {
            p.start_tile_pending = false;
        }
        for _ in 0..steps {
            if game.state.phase != Phase::Drafting {
                return None;
            }
            let actions = drafting_actions(&game.state);
            if actions.is_empty() {
                return None;
            }
            let a = actions.choose(rng).unwrap().clone();
            let _ = game.apply_drafting(&a);
        }
        (game.state.phase == Phase::Drafting).then_some(game.state)
    }

    /// Laedt ein lokal vorhandenes Modell fuer den `BATCH_ROOT_EXPANSION`-
    /// Paritaetstest unten -- `load_test_net()` (oben) haengt an
    /// `alphazero_v10_best.onnx`, das im aktuellen Modell-Bestand nicht
    /// mehr vorhanden ist (gleicher Befund wie bei den Task-#14-PCR-Tests
    /// in `self_play.rs`/den `eval_batch`-Tests in `net.rs`). Bewusst der
    /// AMTIERENDE 2D-Champion `v19_2d_best` (nicht ein flaches Modell) --
    /// das ist der eigentliche Zielpunkt dieses Perf-Auftrags (die
    /// 1,46x-2D-Inferenzkosten druecken), der Paritaetstest soll also genau
    /// DIESE Architektur (`PlanesPlusFlat`-Layout, ZWEI ONNX-Graph-Inputs)
    /// abdecken, nicht nur den einfacheren flachen Pfad.
    fn load_batching_test_net() -> Net {
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../models/alphazero_v19_2d_best.onnx");
        Net::load_auto(path.to_str().unwrap()).unwrap_or_else(|e| panic!(
            "{path:?} nicht ladbar ({e}) -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ))
    }

    /// Perf-Auftrag (2026-08-02) -- Kernabsicherung fuer `BATCH_ROOT_EXPANSION`:
    /// `build_gumbel_tree_inner` mit `batch_root_expansion=true` muss bei
    /// IDENTISCHEM Seed (a) dieselbe Gesamt-Besuchszahl an der Wurzel
    /// liefern (Sim-Buchhaltung unveraendert, siehe
    /// `batched_expand_root_candidates`-Doku), (b) pro Wurzelkind dieselbe
    /// Besuchszahl (Kontrollfluss/RNG bis zur Kandidatenauswahl ist in
    /// beiden Pfaden identischer Code, siehe Kommentar an der Aufrufstelle)
    /// und (c) dieselben Q-Werte wie der unbatchte Pfad liefern.
    ///
    /// GEMESSENES ERGEBNIS (2026-08-02, gegen `v19_2d_best` UND zusaetzlich
    /// gegen ein flaches Modell `v18_best` von Hand geprueft, sims=400,
    /// m_prime=16): root_q UND alle 16 Wurzelkind-Q-Werte sind
    /// BIT-IDENTISCH (`f64::to_bits()`-Vergleich, nicht nur "innerhalb
    /// Toleranz") zwischen batched und unbatcht -- kein messbarer
    /// Gleitkomma-Summationsreihenfolge-Effekt in der Praxis, obwohl
    /// theoretisch moeglich (siehe `BATCH_ROOT_EXPANSION`-Doku). Die
    /// Toleranz unten (1e-4) bleibt trotzdem als Sicherheitsmarge stehen
    /// (kein Anspruch auf Bit-Identitaet ueber alle Hardware-/tract-
    /// Versionen hinweg, gleiches Vorsichtsprinzip wie
    /// `net::eval_pair_matches_two_single_evals`s 1e-5) -- der eigentliche
    /// Befund (bit-identisch HEUTE) gehoert in den Auftragsbericht, nicht in
    /// eine ueberscharfe Assertion, die auf einer anderen Maschine flackern
    /// koennte.
    #[test]
    fn batched_root_expansion_matches_sequential_within_tolerance() {
        let net = load_batching_test_net();
        let mut state_rng = StdRng::seed_from_u64(2026_08_02);
        let Some(state) = random_drafting_state(1, 0, &mut state_rng) else {
            panic!("random_drafting_state(steps=0) sollte immer den frischen Runde-1-Zustand liefern");
        };

        let sims = 400u32; // Produktions-Standard -- ergibt m_prime=GUMBEL_TOP_M=16, deckt den vollen eval_batch-Bereich ab.
        let mut rng_unbatched = StdRng::seed_from_u64(555_555);
        let nodes_unbatched = build_gumbel_tree_inner(
            &net, None, &state, sims, false, &mut rng_unbatched, None, false, &SearchConfig::from_env(),
        );
        let mut rng_batched = StdRng::seed_from_u64(555_555);
        let nodes_batched = build_gumbel_tree_inner(
            &net, None, &state, sims, false, &mut rng_batched, None, true, &SearchConfig::from_env(),
        );

        assert_eq!(
            nodes_unbatched[0].visits, nodes_batched[0].visits,
            "Gesamtbesuchszahl an der Wurzel muss identisch sein (gleiche Sim-Buchhaltung)"
        );
        let root_q_u = nodes_unbatched[0].value / (nodes_unbatched[0].visits.max(1) as f64);
        let root_q_b = nodes_batched[0].value / (nodes_batched[0].visits.max(1) as f64);
        assert!(
            (root_q_u - root_q_b).abs() < 1e-4,
            "root_q weicht zu stark ab: unbatcht={root_q_u} batched={root_q_b}"
        );

        let stats_u = root_child_stats_from_nodes(&nodes_unbatched);
        let stats_b = root_child_stats_from_nodes(&nodes_batched);
        assert_eq!(stats_u.len(), stats_b.len(), "gleiche Anzahl besuchter Wurzelkinder erwartet");
        // Nach der Aktion selbst abgeglichen (nicht nach Position): die
        // Kandidaten-EXPANSIONSREIHENFOLGE ist identisch (siehe oben), aber
        // `nodes[0].children`s finale Reihenfolge unterscheidet sich
        // zwischen "alle Kandidaten zuerst" (batched) und "je Kandidat
        // interleaved mit seinen Tiefenbesuchen" (unbatcht).
        let map_b: std::collections::HashMap<String, (u32, f64)> =
            stats_b.iter().map(|(a, v, q)| (format!("{a:?}"), (*v, *q))).collect();
        let mut total_visits_u = 0u32;
        let mut total_visits_b_matched = 0u32;
        for (a, v_u, q_u) in &stats_u {
            total_visits_u += v_u;
            let key = format!("{a:?}");
            let (v_b, q_b) = *map_b.get(&key).unwrap_or(&(0, 0.0));
            assert_eq!(*v_u, v_b, "Besuchszahl fuer Aktion {key} weicht ab");
            total_visits_b_matched += v_b;
            if *v_u > 0 {
                assert!(
                    (q_u - q_b).abs() < 1e-4,
                    "Q fuer Aktion {key} weicht zu stark ab: unbatcht={q_u} batched={q_b}"
                );
            }
        }
        assert_eq!(total_visits_u, total_visits_b_matched, "Summe der Kind-Besuche muss uebereinstimmen");
    }

    /// Interleavte Latenz-Nachmessung `BATCH_ROOT_EXPANSION` an/aus (Perf-
    /// Auftrag 2026-08-02, Deliverable 4), direkt ueber
    /// `build_gumbel_tree_inner` (umgeht die Compile-Zeit-Konstante, siehe
    /// deren Doku) statt zweier getrennter Prozesslaeufe mit manuellem
    /// Konstanten-Umschalten -- INTERLEAVED innerhalb DESSELBEN Prozesses
    /// haelt Lastschwankungen (auf dieser Maschine liefen beim ersten Lauf
    /// parallel die PCR-A/B-Kampagnen) beiderseits gleich, macht das
    /// VERHAELTNIS robust (gleiches Messdesign-Prinzip wie
    /// `examples/latency_2d_vs_flat.rs`). Gemessenes Ergebnis (2026-08-02,
    /// `v19_2d_best`, sims=400, n=60, unter erheblicher Fremdlast durch die
    /// PCR-Kampagnen -- absolute Zeiten dadurch stark aufgeblaeht, ~750ms
    /// statt der ~2-4ms einer unbelasteten Maschine, aber das VERHAELTNIS
    /// bleibt aussagekraeftig): `ratio(on/off) ≈ 1.01` -- KEIN messbarer
    /// Geschwindigkeitsgewinn (siehe Auftragsbericht fuer die Einordnung:
    /// die gebuendelten `m_prime<=16` Erstexpansionen sind nur ein kleiner
    /// Bruchteil der insgesamt `sims` Netz-Aufrufe pro Zug).
    /// `#[ignore]`: kein Teil des normalen `cargo test`-Laufs (reine
    /// Zeitmessung, kein Korrektheits-Test -- der ist
    /// `batched_root_expansion_matches_sequential_within_tolerance` oben),
    /// manuell via `cargo test --release batch_root_expansion_latency_bench
    /// -- --ignored --nocapture` startbar, z.B. fuer eine Nachmessung ohne
    /// Fremdlast.
    #[test]
    #[ignore]
    fn batch_root_expansion_latency_bench() {
        let net = load_batching_test_net();
        let mut state_rng = StdRng::seed_from_u64(2026_08_02);
        let Some(state) = random_drafting_state(1, 0, &mut state_rng) else {
            panic!("random_drafting_state(steps=0) sollte immer den frischen Runde-1-Zustand liefern");
        };
        let sims = 400u32;
        const WARMUP: usize = 5;
        const RUNS: usize = 60;

        for i in 0..WARMUP {
            let mut rng = StdRng::seed_from_u64(i as u64);
            let _ = build_gumbel_tree_inner(
                &net, None, &state, sims, false, &mut rng, None, false, &SearchConfig::from_env(),
            );
            let _ = build_gumbel_tree_inner(
                &net, None, &state, sims, false, &mut rng, None, true, &SearchConfig::from_env(),
            );
        }

        let mut times_off = Vec::with_capacity(RUNS);
        let mut times_on = Vec::with_capacity(RUNS);
        for i in 0..RUNS {
            let mut rng_off = StdRng::seed_from_u64(1000 + i as u64);
            let t = std::time::Instant::now();
            let _ = build_gumbel_tree_inner(
                &net, None, &state, sims, false, &mut rng_off, None, false, &SearchConfig::from_env(),
            );
            times_off.push(t.elapsed().as_secs_f64() * 1000.0);

            let mut rng_on = StdRng::seed_from_u64(1000 + i as u64);
            let t = std::time::Instant::now();
            let _ = build_gumbel_tree_inner(
                &net, None, &state, sims, false, &mut rng_on, None, true, &SearchConfig::from_env(),
            );
            times_on.push(t.elapsed().as_secs_f64() * 1000.0);
        }
        let median = |v: &mut Vec<f64>| -> f64 {
            v.sort_by(|a, b| a.partial_cmp(b).unwrap());
            v[v.len() / 2]
        };
        let m_off = median(&mut times_off.clone());
        let m_on = median(&mut times_on.clone());
        eprintln!(
            "BATCH_ROOT_EXPANSION off med={m_off:.3}ms  on med={m_on:.3}ms  ratio(on/off)={:.3}  n={RUNS} sims={sims}",
            m_on / m_off
        );
    }

    #[test]
    fn build_determinized_forest_with_n_equals_1_matches_single_tree_stats_and_policy() {
        // (a) NUM_DETERMINIZATIONS<=1 ist byte-identisch zum Alt-Verhalten --
        // die drei Produktions-Einstiege routen bei <=1 zwar NICHT durch die
        // Forest-/Aggregations-Maschinerie (siehe deren Code, bewusst
        // unveraendert), aber selbst WENN man `build_determinized_forest`
        // mit n=1 aufruft, muss das aggregierte Ergebnis exakt dem direkten
        // `build_net_tree`-Aufruf mit identischem RNG-Seed entsprechen --
        // Sicherheitsnetz, falls ein zukuenftiges Refactoring den
        // <=1-Sonderfall an den Aufrufstellen versehentlich entfernt.
        let net = load_test_net();
        let mut rng_state = StdRng::seed_from_u64(777);
        let state = random_drafting_state(1, 10, &mut rng_state).expect("Testzustand sollte auswertbar sein");

        let mut rng_a = StdRng::seed_from_u64(999);
        let nodes = build_net_tree(
            &net, None, &state, 8, DEFAULT_C_PUCT, false, &mut rng_a, None, None, &SearchConfig::from_env(),
        );
        let direct_stats = root_child_stats_from_nodes(&nodes);
        let direct_policy = root_completed_q_policy(&nodes);

        let mut rng_b = StdRng::seed_from_u64(999);
        let forest = build_determinized_forest(
            &net, None, &state, 8, DEFAULT_C_PUCT, false, 1, &mut rng_b, &SearchConfig::from_env(),
        );
        assert_eq!(forest.len(), 1, "n=1 sollte genau einen Baum liefern");
        let forest_stats = aggregate_root_child_stats(&forest);
        let forest_policy = average_completed_q_policy(&forest);

        assert_eq!(direct_stats.len(), forest_stats.len());
        for ((a1, v1, q1), (a2, v2, q2)) in direct_stats.iter().zip(forest_stats.iter()) {
            assert_eq!(a1, a2, "Aktionsreihenfolge muss uebereinstimmen");
            assert_eq!(v1, v2, "Besuche muessen bei n=1 identisch sein");
            assert!((q1 - q2).abs() < 1e-12, "Q muss bei n=1 identisch sein: {q1} vs {q2}");
        }
        assert_eq!(direct_policy.len(), forest_policy.len());
        for ((a1, p1), (a2, p2)) in direct_policy.iter().zip(forest_policy.iter()) {
            assert_eq!(a1, a2, "Aktionsreihenfolge muss uebereinstimmen");
            assert!((p1 - p2).abs() < 1e-9, "completed-Q-Politik muss bei n=1 identisch sein: {p1} vs {p2}");
        }
    }

    #[test]
    fn build_determinized_forest_draws_three_different_determinizations_at_n_equals_3() {
        // (b) Kernanforderung Task #65: bei n=3 muessen drei GENUIN
        // unterschiedliche Determinisierungen gezogen werden (nicht dieselbe
        // Welt dreimal) -- `dome_tile_pool`-Reihenfolge NACH der Wurzel-
        // Determinisierung ist der direkteste Zeuge dafuer (siehe
        // `determinize_hidden_information`, `DETERMINIZE_ROOT_HIDDEN_INFO`
        // ist Standard `true`). Gleicher RNG-Strom (ein einziges `rng`,
        // wie `build_determinized_forest` es an `build_net_tree` weiterreicht)
        // muss trotzdem drei verschiedene Ziehungen liefern.
        let net = load_test_net();
        let mut rng = StdRng::seed_from_u64(2468);
        let state = random_drafting_state(2, 10, &mut rng).expect("Testzustand sollte auswertbar sein");
        assert!(
            state.dome_tile_pool.len() >= 3,
            "Testvoraussetzung: genug Platten im verdeckten Stapel fuer eine aussagekraeftige Mischung"
        );

        let forest = build_determinized_forest(
            &net, None, &state, 6, DEFAULT_C_PUCT, false, 3, &mut rng, &SearchConfig::from_env(),
        );
        assert_eq!(forest.len(), 3);
        let pools: Vec<Vec<usize>> = forest
            .iter()
            .map(|nodes| nodes[0].state.dome_tile_pool.iter().map(|t| t.tile_id).collect())
            .collect();
        assert_ne!(pools[0], pools[1], "Welt 1 und 2 sollten unterschiedliche dome_tile_pool-Reihenfolgen ziehen");
        assert_ne!(pools[1], pools[2], "Welt 2 und 3 sollten unterschiedliche dome_tile_pool-Reihenfolgen ziehen");
        assert_ne!(pools[0], pools[2], "Welt 1 und 3 sollten unterschiedliche dome_tile_pool-Reihenfolgen ziehen");
    }

    #[test]
    fn hybrid_search_with_equal_nets_matches_plain_search() {
        // Task #88 (Hybrid-Suche, kausaler Kopf-Test) -- WICHTIGSTER Korrekt-
        // heitstest fuer den neuen Hybrid-Codepfad: `net_policy` UND `net_value`
        // als DIESELBE Referenz muss den `same_net`-Kurzschluss in `make_node`
        // greifen lassen (siehe dortiger Kommentar) -- das Ergebnis muss dann
        // BYTE-IDENTISCH zur normalen (Nicht-Hybrid) Suche sein, sonst haette
        // jede kuenftige 2x2-Messung keinen sauberen A=B-Referenzpunkt. Prueft
        // volle Wurzel-Statistik (Besuche, Q), completed-Q-Politik UND die
        // finale Zugwahl, ueber mehrere zufaellige Stellungen und Sims-Budgets.
        let net = load_test_net();
        let mut setup_rng = StdRng::seed_from_u64(4242);
        let mut checked = 0;
        for gi in 0..6u64 {
            let Some(state) = random_drafting_state(gi, 12, &mut setup_rng) else { continue };
            for &sims in &[8u32, 24] {
                let mut rng_plain = StdRng::seed_from_u64(1000 + gi);
                let nodes_plain = build_net_tree(
                    &net, None, &state, sims, DEFAULT_C_PUCT, false, &mut rng_plain, None, None,
                    &SearchConfig::from_env(),
                );
                let stats_plain = root_child_stats_from_nodes(&nodes_plain);
                let policy_plain = root_completed_q_policy(&nodes_plain);
                let action_plain =
                    select_final_root_child(&nodes_plain).and_then(|i| nodes_plain[i].action.clone());

                let mut rng_hybrid = StdRng::seed_from_u64(1000 + gi);
                let nodes_hybrid = build_net_tree(
                    &net,
                    Some(&net),
                    &state,
                    sims,
                    DEFAULT_C_PUCT,
                    false,
                    &mut rng_hybrid,
                    None,
                    None,
                    &SearchConfig::from_env(),
                );
                let stats_hybrid = root_child_stats_from_nodes(&nodes_hybrid);
                let policy_hybrid = root_completed_q_policy(&nodes_hybrid);
                let action_hybrid =
                    select_final_root_child(&nodes_hybrid).and_then(|i| nodes_hybrid[i].action.clone());

                assert_eq!(
                    nodes_plain.len(),
                    nodes_hybrid.len(),
                    "Spiel {gi} sims={sims}: Baumgroesse weicht ab"
                );
                assert_eq!(stats_plain.len(), stats_hybrid.len());
                for ((a1, v1, q1), (a2, v2, q2)) in stats_plain.iter().zip(stats_hybrid.iter()) {
                    assert_eq!(a1, a2, "Spiel {gi} sims={sims}: Aktionsreihenfolge weicht ab");
                    assert_eq!(v1, v2, "Spiel {gi} sims={sims}: Besuche weichen ab (A={a1:?})");
                    assert_eq!(
                        q1, q2,
                        "Spiel {gi} sims={sims}: Q nicht byte-identisch (A={a1:?}): {q1} vs {q2}"
                    );
                }
                assert_eq!(policy_plain.len(), policy_hybrid.len());
                for ((a1, p1), (a2, p2)) in policy_plain.iter().zip(policy_hybrid.iter()) {
                    assert_eq!(a1, a2, "Spiel {gi} sims={sims}: Policy-Aktionsreihenfolge weicht ab");
                    assert_eq!(
                        p1, p2,
                        "Spiel {gi} sims={sims}: completed-Q-Politik nicht byte-identisch (A={a1:?}): {p1} vs {p2}"
                    );
                }
                assert_eq!(action_plain, action_hybrid, "Spiel {gi} sims={sims}: finale Zugwahl weicht ab");
                checked += 1;
            }
        }
        assert!(checked >= 6, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    #[test]
    fn gumbel_trace_collection_does_not_change_search() {
        // Task #95 (Anforderung 3) -- WICHTIGSTER Korrektheitstest fuer den
        // neuen Debug-Trace: `collect_trace=true` (also `trace=Some(..)` an
        // `build_gumbel_tree`) darf die eigentliche Suche NICHT veraendern --
        // gleicher RNG-Seed muss exakt denselben Baum (Groesse, Besuche, Q je
        // Knoten) UND dieselbe finale Zugwahl liefern wie `trace=None`.
        // Gleiches Muster wie `hybrid_search_with_equal_nets_matches_plain_search`
        // (A=B-Referenzpunkt fuer einen additiven Codepfad).
        let net = load_test_net();
        let mut setup_rng = StdRng::seed_from_u64(9595);
        let mut checked = 0;
        for gi in 0..6u64 {
            let Some(state) = random_drafting_state(gi, 12, &mut setup_rng) else { continue };
            for &sims in &[8u32, 24] {
                let mut rng_plain = StdRng::seed_from_u64(2000 + gi);
                let nodes_plain = build_net_tree(
                    &net, None, &state, sims, DEFAULT_C_PUCT, false, &mut rng_plain, None, None,
                    &SearchConfig::from_env(),
                );

                let mut rng_traced = StdRng::seed_from_u64(2000 + gi);
                let mut trace = GumbelTrace::default();
                let nodes_traced = build_net_tree(
                    &net,
                    None,
                    &state,
                    sims,
                    DEFAULT_C_PUCT,
                    false,
                    &mut rng_traced,
                    None,
                    Some(&mut trace),
                    &SearchConfig::from_env(),
                );

                assert_eq!(
                    nodes_plain.len(),
                    nodes_traced.len(),
                    "Spiel {gi} sims={sims}: Baumgroesse weicht ab, obwohl nur Trace-Sammlung aktiviert wurde"
                );
                for (np, nt) in nodes_plain.iter().zip(nodes_traced.iter()) {
                    assert_eq!(np.visits, nt.visits, "Spiel {gi} sims={sims}: Besuchszahl weicht ab");
                    assert_eq!(np.value, nt.value, "Spiel {gi} sims={sims}: akkumulierter Wert weicht ab");
                    assert_eq!(np.action, nt.action, "Spiel {gi} sims={sims}: Knoten-Aktion weicht ab");
                    assert_eq!(np.prior, nt.prior, "Spiel {gi} sims={sims}: Prior weicht ab");
                }
                let action_plain =
                    select_final_root_child(&nodes_plain).and_then(|i| nodes_plain[i].action.clone());
                let action_traced =
                    select_final_root_child(&nodes_traced).and_then(|i| nodes_traced[i].action.clone());
                assert_eq!(action_plain, action_traced, "Spiel {gi} sims={sims}: finale Zugwahl weicht ab");

                // Trace selbst muss sinnvoll befuellt sein (sonst waere der
                // Paritaetstest trivial, weil gar kein Trace-Code lief).
                assert!(!trace.top_m.is_empty(), "Spiel {gi} sims={sims}: Top-m-Trace ist leer");
                assert!(!trace.finalists.is_empty(), "Spiel {gi} sims={sims}: Finalisten-Trace ist leer");
                assert!(trace.root_value.is_some(), "Spiel {gi} sims={sims}: Root-Value-Debug fehlt");

                checked += 1;
            }
        }
        assert!(checked >= 6, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    #[test]
    fn net_leaf_eval_is_invariant_to_which_player_is_flagged_current() {
        // Kernbehauptung des Kollegen-Verdachts (Perspektivfehler): flippt man
        // NUR `current_player` an einem ansonsten identischen Zustand, MUSS
        // `net_leaf_eval` (das intern ohnehin beide Perspektiven per zwei
        // Forward-Pässen auswertet und fest auf [Spieler0, Spieler1] einsortiert)
        // exakt dasselbe Ergebnis liefern -- unabhaengig davon, wer gerade
        // "current_player" ist. Ein Perspektiv-/Plumbing-Bug wuerde diese
        // Invariante brechen.
        let net = load_test_net();
        let mut rng = StdRng::seed_from_u64(2026);
        let mut checked = 0;
        for gi in 0..10u64 {
            let Some(state) = random_drafting_state(gi, 15, &mut rng) else { continue };
            let mut flipped = state.clone();
            flipped.current_player = 1 - flipped.current_player;
            let a = net_leaf_eval(&net, &state);
            let b = net_leaf_eval(&net, &flipped);
            assert!(
                (a[0] - b[0]).abs() < 1e-9 && (a[1] - b[1]).abs() < 1e-9,
                "Spiel {gi}: net_leaf_eval haengt faelschlich von state.current_player ab -- a={a:?} b={b:?}"
            );
            checked += 1;
        }
        assert!(checked >= 5, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    #[test]
    #[ignore = "Schwelle stammt aus der v10-Aera; seit dem Fixture-Wechsel auf den v21-Champion (2026-08-15) erst neu kalibrieren -- lief zuvor still leer-gruen, weil v10_best fehlte"]
    fn net_leaf_eval_sign_mostly_agrees_with_exact_dfs_ground_truth() {
        // "Terminalnahe Zustaende mit bekanntem Sieger" (Kollegen-Vorschlag)
        // verallgemeinert: `mcts::evaluate` ist an JEDEM Drafting-Zustand ein
        // exaktes Ground-Truth-Urteil (Rundenscore + Wertungsplatten-
        // Fortschritt, dieselbe Grundlage wie das Runde-5-Alpha-Beta). Prueft
        // NICHT Genauigkeit (die ist bekanntermassen schwach, siehe Runde-1-R²
        // in STATUS.md) -- nur, ob das Netz MEHRHEITLICH auf der richtigen
        // Seite der 50%-Linie liegt. Ein echter Perspektivfehler wuerde die
        // Uebereinstimmungsrate weit unter 50% druecken (systematische
        // Umkehrung), reines Value-Rauschen bleibt darueber.
        let net = load_test_net();
        let mut rng = StdRng::seed_from_u64(4242);
        let (mut agree, mut total) = (0usize, 0usize);
        for gi in 0..40u64 {
            let Some(state) = random_drafting_state(gi, 25, &mut rng) else { continue };
            let net_vals = net_leaf_eval(&net, &state);
            let dfs_vals = crate::mcts::evaluate(&state, 0);
            // Nur werten, wenn beide Seiten ueberhaupt eine Praeferenz zeigen --
            // bei einem Gleichstand ist "Vorzeichen" nicht definiert.
            if (net_vals[0] - net_vals[1]).abs() < 1e-6 || (dfs_vals[0] - dfs_vals[1]).abs() < 1e-6 {
                continue;
            }
            total += 1;
            if (net_vals[0] > net_vals[1]) == (dfs_vals[0] > dfs_vals[1]) {
                agree += 1;
            }
        }
        assert!(total >= 10, "zu wenige auswertbare Stichproben ({total}) -- Testaufbau pruefen");
        let rate = agree as f64 / total as f64;
        eprintln!("  ℹ️  Vorzeichen-Uebereinstimmung Netz vs. DFS: {:.1}% ({agree}/{total})", rate * 100.0);
        assert!(
            rate > 0.5,
            "Vorzeichen-Uebereinstimmung Netz vs. exaktem DFS nur {:.0}% ({agree}/{total}) -- \
             das ist nicht besser als Zufall und deutet auf einen Perspektivfehler hin, nicht nur \
             auf gewöhnliches Value-Rauschen",
            rate * 100.0
        );
    }

    // ── Task #78 (v12c Value-Shrinkage, Platzhalter-Kalibrierung) ───────────

    #[test]
    fn value_shrink_per_round_table_is_monotone_and_normalized() {
        assert_eq!(VALUE_SHRINK_PER_ROUND.len(), 5);
        for w in VALUE_SHRINK_PER_ROUND.iter() {
            assert!(*w > 0.0 && *w <= 1.0, "Gewicht ausserhalb (0,1]: {w}");
        }
        for pair in VALUE_SHRINK_PER_ROUND.windows(2) {
            assert!(
                pair[1] >= pair[0] - 1e-12,
                "Tabelle muss monoton nicht-fallend sein: {:?}",
                VALUE_SHRINK_PER_ROUND
            );
        }
        assert!(
            (VALUE_SHRINK_PER_ROUND[4] - 1.0).abs() < 1e-9,
            "Runde 5 muss auf 1.0 normiert sein (keine Daempfung in der letzten Runde)"
        );
        assert!(
            VALUE_SHRINK_PER_ROUND[0] < VALUE_SHRINK_PER_ROUND[4],
            "Runde 1 muss strikt kleiner sein als Runde 5"
        );
    }

    #[test]
    fn value_shrink_weight_maps_round_number_and_clamps_out_of_range() {
        assert_eq!(value_shrink_weight(1), VALUE_SHRINK_PER_ROUND[0]);
        assert_eq!(value_shrink_weight(2), VALUE_SHRINK_PER_ROUND[1]);
        assert_eq!(value_shrink_weight(5), VALUE_SHRINK_PER_ROUND[4]);
        // Verteidigung: Runde 0 oder >5 sollte in der Praxis nie vorkommen,
        // klemmt aber statt zu paniken.
        assert_eq!(value_shrink_weight(0), VALUE_SHRINK_PER_ROUND[0]);
        assert_eq!(value_shrink_weight(99), VALUE_SHRINK_PER_ROUND[4]);
    }

    #[test]
    fn apply_value_shrink_matches_current_toggle_state() {
        // Task #78, robust gegen den A/B-Toggle-Flip (2026-07-23): dieser Test
        // muss bei `VALUE_SHRINK_ENABLED=false` UND `=true` gruen bleiben --
        // waehrend des Phase-B-Nachweislaufs wird die Konstante temporaer auf
        // `true` gesetzt (`cargo test --release` muss dabei gruen bleiben,
        // siehe `evaluations/STATUS.md` "v12c"-Abschnitt), danach je nach
        // Ergebnis wieder zurueckgesetzt. Bei AUS: reine Identitaet (byte-
        // identisch zum Vor-Task-#78-Verhalten). Bei AN: Runde 5 bleibt
        // Identitaet (w_5=1.0 per Normierung), fruehere Runden werden
        // sichtbar Richtung 0.5 gezogen.
        let v = [0.9, 0.05];
        if VALUE_SHRINK_ENABLED {
            assert_ne!(apply_value_shrink(v, 1), v, "bei AN muss Runde 1 sichtbar geschrumpft werden");
            let r5 = apply_value_shrink(v, 5);
            assert!(
                (r5[0] - v[0]).abs() < 1e-9 && (r5[1] - v[1]).abs() < 1e-9,
                "Runde 5 bleibt (bis auf Gleitkomma-Rauschen) Identitaet (w_5=1.0): {r5:?} vs {v:?}"
            );
        } else {
            assert_eq!(apply_value_shrink(v, 1), v);
            assert_eq!(apply_value_shrink(v, 5), v);
            assert_eq!(apply_value_shrink([0.0, 1.0], 3), [0.0, 1.0]);
        }
    }

    #[test]
    fn round1_weight_pulls_harder_toward_half_than_round5_weight() {
        // Direkter Formel-Test (unabhaengig vom ENABLED-Toggle): mit Runde-1-
        // Gewicht muss der geschrumpfte Wert naeher an 0.5 liegen als mit
        // Runde-5-Gewicht, fuer denselben Rohwert.
        let w1 = value_shrink_weight(1);
        let w5 = value_shrink_weight(5);
        for v in [0.9, 0.1, 0.99, 0.55] {
            let shrunk1 = 0.5 + w1 * (v - 0.5);
            let shrunk5 = 0.5 + w5 * (v - 0.5);
            assert!(
                (shrunk1 - 0.5).abs() < (shrunk5 - 0.5).abs(),
                "v={v}: Runde 1 (w={w1}, ->{shrunk1}) sollte staerker Richtung 0.5 \
                 gezogen werden als Runde 5 (w={w5}, ->{shrunk5})"
            );
        }
    }

    #[test]
    fn floor_shaping_additive_is_unaffected_by_shrink_when_applied_after_it() {
        // Konstruierter Vergleich (Task #78): reproduziert exakt die
        // Reihenfolge aus `make_node` -- `apply_value_shrink` (echte
        // Produktionsfunktion) laeuft VOR dem Floor-Additiv. Das reine
        // Floor-Signal (hier durch einen repraesentativen `floor_shift`-Wert
        // ersetzt, wie ihn `floor_shaping_delta(&state).tanh() *
        // FLOOR_SHAPING_WEIGHT` liefern wuerde) darf durch den Shrink-Schritt
        // NICHT gedaempft werden, weil es danach unveraendert additiv
        // aufaddiert wird -- Kontrast zur (falschen) umgekehrten Reihenfolge.
        let base = [0.5f64, 0.5f64]; // neutraler Netz-Rohwert vor Floor-Korrektur
        let floor_shift = 0.12;
        let round1_w = value_shrink_weight(1); // staerkster Schrumpf-Fall, Worst-Case

        // Richtige Reihenfolge (wie in make_node): erst schrumpfen (hier
        // manuell mit dem Runde-1-Gewicht erzwungen, unabhaengig vom
        // ENABLED-Toggle, um die Formel selbst zu pruefen), dann Floor addieren.
        let shrunk_base = [0.5 + round1_w * (base[0] - 0.5), 0.5 + round1_w * (base[1] - 0.5)];
        let correct_order = [
            (shrunk_base[0] + floor_shift).clamp(0.0, 1.0),
            (shrunk_base[1] - floor_shift).clamp(0.0, 1.0),
        ];
        assert!(
            (correct_order[0] - shrunk_base[0] - floor_shift).abs() < 1e-9,
            "Floor-Beitrag muss exakt +floor_shift bleiben, unabhaengig vom Schrumpfgewicht"
        );
        assert!(
            (correct_order[1] - shrunk_base[1] + floor_shift).abs() < 1e-9,
            "Floor-Beitrag muss exakt -floor_shift bleiben, unabhaengig vom Schrumpfgewicht"
        );

        // Kontrast: die (falsche) umgekehrte Reihenfolge -- erst Floor
        // addieren, DANACH schrumpfen -- wuerde das exakte Floor-Signal
        // sichtbar daempfen. Zeigt, warum die gewaehlte Reihenfolge wichtig ist.
        let wrong_order_p0 = 0.5 + round1_w * ((base[0] + floor_shift).clamp(0.0, 1.0) - 0.5);
        let wrong_order_contribution = wrong_order_p0 - (0.5 + round1_w * (base[0] - 0.5));
        assert!(
            wrong_order_contribution.abs() < floor_shift - 1e-9,
            "Erwartete Daempfung bei falscher Reihenfolge (Floor vor Shrink) nicht beobachtet -- \
             Testannahme pruefen"
        );
    }

    // ── Floor-Shaping-Opp-Bias (Eskalationsstufe E2, PREREG_aggression_
    // stilmessung.md) ────────────────────────────────────────────────────────

    #[test]
    fn floor_shaping_delta_ego_bias_one_matches_legacy_delta() {
        // `opp_bias=1.0` muss fuer ego=0 exakt (bit-identisch) den alten,
        // symmetrischen `floor_shaping_delta`-Wert liefern -- die Formel
        // own-1.0*opp reduziert sich exakt auf own-opp (Multiplikation mit
        // 1.0 rundet nie).
        let mut rng = StdRng::seed_from_u64(2026);
        let mut checked = 0;
        for gi in 0..8u64 {
            let Some(state) = random_drafting_state(gi, 12, &mut rng) else { continue };
            let legacy = floor_shaping_delta(&state);
            assert_eq!(
                floor_shaping_delta_ego(&state, 0, 1.0),
                legacy,
                "Spiel {gi}: ego=0, opp_bias=1.0 muss bit-identisch zu floor_shaping_delta sein"
            );
            // ego=1 bei bias=1.0 muss exakt der gespiegelte (own/opp vertauschte)
            // Wert sein -- own=theirs, opp=mine, also theirs-mine = -(mine-theirs).
            assert_eq!(
                floor_shaping_delta_ego(&state, 1, 1.0),
                -legacy,
                "Spiel {gi}: ego=1, opp_bias=1.0 muss exakt -floor_shaping_delta sein"
            );
            checked += 1;
        }
        assert!(checked >= 4, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    #[test]
    fn floor_shaping_delta_ego_bias_two_doubles_opp_term() {
        // `opp_bias=2.0`: der GEGNER-Anteil geht doppelt gewichtet ein, der
        // EIGENE Anteil bleibt unveraendert -- direkter Formel-Nachweis
        // gegen die rohen Strafsummen (`floor_penalties` ueber die
        // oeffentlich sichtbare Board-Query, hier via `broken_penalty`/
        // `projected_unplaceable_penalty` nachgebaut, analog
        // `floor_shaping_delta`-Definition).
        let mut rng = StdRng::seed_from_u64(2027);
        let mut checked = 0;
        for gi in 0..8u64 {
            let Some(state) = random_drafting_state(gi, 15, &mut rng) else { continue };
            let mine = (state.players[0].broken_penalty()
                + crate::round_end::projected_unplaceable_penalty(&state.players[0])) as f64;
            let theirs = (state.players[1].broken_penalty()
                + crate::round_end::projected_unplaceable_penalty(&state.players[1])) as f64;
            let expected_ego0 = (mine - 2.0 * theirs) / FLOOR_SHAPING_SCALE;
            let expected_ego1 = (theirs - 2.0 * mine) / FLOOR_SHAPING_SCALE;
            assert!(
                (floor_shaping_delta_ego(&state, 0, 2.0) - expected_ego0).abs() < 1e-12,
                "Spiel {gi}: ego=0, opp_bias=2.0 -- own-2*opp erwartet"
            );
            assert!(
                (floor_shaping_delta_ego(&state, 1, 2.0) - expected_ego1).abs() < 1e-12,
                "Spiel {gi}: ego=1, opp_bias=2.0 -- own-2*opp (vertauscht) erwartet"
            );
            checked += 1;
        }
        assert!(checked >= 4, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    #[test]
    fn floor_shaping_opp_bias_default_is_env_knob_pattern() {
        // Gleiches Muster wie `floor_shaping_weight` -- ohne gesetzte Env-Var
        // liefert der Laufzeit-Knopf exakt die Compile-Konstante.
        assert_eq!(floor_shaping_opp_bias(), FLOOR_SHAPING_OPP_BIAS);
        assert_eq!(FLOOR_SHAPING_OPP_BIAS, 1.0);
    }

    // ── Wertungsplatten-Shaping (Task #93) ──────────────────────────────────

    #[test]
    fn plate_shaping_delta_matches_scoring_progress_difference() {
        // Direkter Formel-Test: `plate_shaping_delta` muss exakt der (skalierten)
        // Differenz der stetigen Wertungsplatten-Fortschritts-Heuristik
        // entsprechen, die `mcts.rs::player_total` schon lange fuer die
        // DFS-Blattbewertung nutzt -- keine eigene Neuimplementierung, reine
        // Wiederverwendung.
        let mut rng = StdRng::seed_from_u64(93);
        let mut checked = 0;
        for gi in 0..8u64 {
            let Some(state) = random_drafting_state(gi, 14, &mut rng) else { continue };
            let expected = (scoring_progress(&state.players[0], &state.scoring_tile_ids)
                - scoring_progress(&state.players[1], &state.scoring_tile_ids))
                / PLATE_SHAPING_SCALE;
            assert!(
                (plate_shaping_delta(&state) - expected).abs() < 1e-12,
                "Spiel {gi}: plate_shaping_delta weicht von der erwarteten Formel ab"
            );
            checked += 1;
        }
        assert!(checked >= 4, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    #[test]
    fn plate_shaping_disabled_is_exact_identity() {
        // Kern-Paritätstest (Task #93): bei `PLATE_SHAPING_ENABLED=false`
        // (Standard) muss `apply_plate_shaping` die Eingabe UNVERÄNDERT
        // zurückgeben -- der Additiv-Block wird komplett übersprungen (siehe
        // Funktionskommentar), nicht nur numerisch neutralisiert. Geprüft über
        // mehrere reale Stellungen (unterschiedliche Plattenfortschritte) UND
        // synthetische Extremwerte, damit auch ein grosses `plate_shaping_delta`
        // bei ENABLED=false garantiert folgenlos bleibt.
        let mut rng = StdRng::seed_from_u64(931);
        let mut checked = 0;
        for gi in 0..8u64 {
            let Some(state) = random_drafting_state(gi, 16, &mut rng) else { continue };
            for v in [[0.5f64, 0.5f64], [0.9, 0.2], [0.0, 1.0], [1.0, 0.0]] {
                let out = apply_plate_shaping(v, &state, None);
                if PLATE_SHAPING_ENABLED {
                    // Falls der Toggle (Mess-Wheel-Arm) aktiv ist, muss das
                    // Ergebnis weiterhin ein gueltiges [0,1]-Paar bleiben.
                    assert!(out[0].is_finite() && (0.0..=1.0).contains(&out[0]));
                    assert!(out[1].is_finite() && (0.0..=1.0).contains(&out[1]));
                } else {
                    assert_eq!(
                        out, v,
                        "Spiel {gi}: PLATE_SHAPING_ENABLED=false muss byte-identisch zur \
                         Eingabe bleiben (v={v:?})"
                    );
                }
            }
            checked += 1;
        }
        assert!(checked >= 4, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    #[test]
    fn plate_shaping_marginal_isolates_parent_baseline() {
        // Marginal-Delta-Fix (Task #8, 2026-07-27): `plate_shaping_marginal`
        // muss GENAU `plate_shaping_delta(state) - plate_shaping_delta(parent)`
        // sein -- unabhaengig davon, wie GROSS die gemeinsame Baseline ist
        // (das war der Kern des Fixes: die alte Version wandte tanh auf den
        // ABSOLUTEN Wert an, wo eine grosse gemeinsame Baseline die kleine
        // Geschwister-Differenz via tanh'(baseline)->0 daempfte). Kein
        // Elternknoten (Wurzel) -> exakt 0.0.
        let mut rng = StdRng::seed_from_u64(834);
        let mut checked = 0;
        for gi in 0..8u64 {
            let Some(parent) = random_drafting_state(gi, 10, &mut rng) else { continue };
            let Some(child) = random_drafting_state(gi + 100, 11, &mut rng) else { continue };
            let expected = plate_shaping_delta(&child) - plate_shaping_delta(&parent);
            assert!(
                (plate_shaping_marginal(&child, Some(&parent)) - expected).abs() < 1e-12,
                "Spiel {gi}: marginal weicht von delta(child)-delta(parent) ab"
            );
            assert_eq!(
                plate_shaping_marginal(&child, None),
                0.0,
                "Spiel {gi}: ohne Elternknoten (Wurzel) muss marginal exakt 0 sein"
            );
            checked += 1;
        }
        assert!(checked >= 4, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    #[test]
    fn plate_shaping_disabled_search_matches_pre_task93_tree() {
        // End-zu-Ende-Parität auf Baum-Ebene: solange `PLATE_SHAPING_ENABLED`
        // (Standard) `false` ist, muss `build_net_tree` exakt dieselben
        // Wurzel-Statistiken/Politik/Zugwahl liefern wie vor Task #93 -- da
        // `apply_plate_shaping` bei ENABLED=false reine Identität ist (siehe
        // `plate_shaping_disabled_is_exact_identity`), reicht hier der
        // Determinismus-Nachweis: zwei Läufe mit identischem Seed müssen
        // uebereinstimmen. Bei aktivem Mess-Wheel-Arm (`ENABLED=true`, temporär
        // fürs A/B) ist dieser Test KEIN Paritätsnachweis mehr -- übersprungen
        // statt fehlzuschlagen, damit `cargo test --release` in BEIDEN
        // Toggle-Zuständen grün bleibt (Konvention wie `apply_value_shrink`s
        // Tests, die ebenfalls beide Zustände vertragen statt nur einen).
        if PLATE_SHAPING_ENABLED {
            eprintln!(
                "  ⚠️  PLATE_SHAPING_ENABLED=true (Mess-Wheel-Arm) -- \
                 Paritätstest übersprungen, kein Paritätsnachweis in diesem Zustand."
            );
            return;
        }
        let net = load_test_net();
        let mut setup_rng = StdRng::seed_from_u64(9300);
        let mut checked = 0;
        for gi in 0..4u64 {
            let Some(state) = random_drafting_state(gi, 12, &mut setup_rng) else { continue };
            let mut rng_a = StdRng::seed_from_u64(2000 + gi);
            let nodes_a = build_net_tree(
                &net, None, &state, 16, DEFAULT_C_PUCT, false, &mut rng_a, None, None, &SearchConfig::from_env(),
            );
            let stats_a = root_child_stats_from_nodes(&nodes_a);
            let policy_a = root_completed_q_policy(&nodes_a);

            let mut rng_b = StdRng::seed_from_u64(2000 + gi);
            let nodes_b = build_net_tree(
                &net, None, &state, 16, DEFAULT_C_PUCT, false, &mut rng_b, None, None, &SearchConfig::from_env(),
            );
            let stats_b = root_child_stats_from_nodes(&nodes_b);
            let policy_b = root_completed_q_policy(&nodes_b);

            assert_eq!(stats_a, stats_b, "Spiel {gi}: Wurzel-Statistiken nicht deterministisch/identisch");
            assert_eq!(policy_a, policy_b, "Spiel {gi}: completed-Q-Politik nicht deterministisch/identisch");
            checked += 1;
        }
        assert!(checked >= 4, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    // ═══════════════════════════════════════════════════════════════════
    // Wertungsplatten-EGO-Shaping (Nutzer-Auftrag 2026-08-10, siehe
    // Modul-Kommentar bei `apply_scoring_shaping` oben) -- eigener Block,
    // getrennt vom Task-#93-Plattenshaping-Block oben (andere Formel/
    // Perspektive/Verdrahtung, siehe dortiger Unterschieds-Kommentar).
    // ═══════════════════════════════════════════════════════════════════

    #[test]
    fn scoring_shaping_defaults_reproduce_existing_behavior() {
        // Grundvoraussetzung fuer JEDEN Neutralitaets-Nachweis unten: die
        // Compile-Konstanten UND die (in dieser Test-Umgebung ungesetzten)
        // Env-Var-Getter muessen exakt den "Additiv aus"-Zustand liefern.
        assert_eq!(WERTUNG_SHAPING_WEIGHT, 0.0);
        assert_eq!(WERTUNG_SHAPING_ALPHA, 2.0);
        assert_eq!(
            scoring_shaping_weight(),
            0.0,
            "Test-Voraussetzung: MOSAIC_WERTUNG_SHAPING_W darf hier nicht gesetzt sein"
        );
        assert_eq!(
            scoring_shaping_alphas(),
            [2.0; 8],
            "Test-Voraussetzung: MOSAIC_WERTUNG_ALPHA darf hier nicht gesetzt sein"
        );
        // Runden-Verstaerkung ist standardmaessig AUS -- sonst waere der
        // Blattwert rundenabhaengig, ohne dass jemand einen Knopf gedreht hat.
        assert_eq!(
            scoring_round_gain(),
            0.0,
            "Test-Voraussetzung: MOSAIC_WERTUNG_ROUND_GAIN darf hier nicht gesetzt sein"
        );
    }

    #[test]
    fn apply_scoring_shaping_with_zero_weight_is_exact_identity() {
        // Kern-Neutralitaetsnachweis auf reiner Formel-Ebene (Ersatz fuer die
        // Python-Paritaetsprobe, die hier nicht laufen darf -- sie prueft das
        // INSTALLIERTE Wheel, Installieren ist waehrend des laufenden
        // Cache-Neubaus/Trainings gesperrt): bei `w=0.0` MUSS `value`
        // unveraendert zurueckkommen -- kein `scoring_progress_alpha`-Aufruf,
        // kein `tanh`, keine Rundung. Ueber mehrere reale Stellungen UND
        // synthetische Extremwerte, gleiches Muster wie
        // `plate_shaping_disabled_is_exact_identity`.
        let mut rng = StdRng::seed_from_u64(8110);
        let mut checked = 0;
        for gi in 0..8u64 {
            let Some(state) = random_drafting_state(gi, 16, &mut rng) else { continue };
            for v in [[0.5f64, 0.5f64], [0.9, 0.2], [0.0, 1.0], [1.0, 0.0]] {
                let out = apply_scoring_shaping_full(v, &state, &[0.0; 8], &[2.0; 8], 0.0, 0.0, 0.0, false);
                assert_eq!(out, v, "Spiel {gi}: w=0.0 muss byte-identisch zur Eingabe bleiben (v={v:?})");
                // Auch bei einem exotischen `alpha` darf `w=0.0` NICHTS
                // veraendern -- der Fruehausstieg greift VOR jedem
                // `alpha`-Gebrauch.
                let out2 = apply_scoring_shaping_full(v, &state, &[0.0; 8], &[7.0; 8], 0.0, 0.0, 0.0, false);
                assert_eq!(out2, v);
            }
            checked += 1;
        }
        assert!(checked >= 4, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    #[test]
    fn scoring_shaping_disabled_by_default_is_exact_identity() {
        // Gleicher Nachweis wie oben, aber ueber den tatsaechlichen
        // Env-Var-lesenden Wrapper `apply_scoring_shaping` (genau die
        // Funktion, die `net_leaf_eval`/`make_node` aufrufen) -- in dieser
        // Test-Umgebung ist `MOSAIC_WERTUNG_SHAPING_W` ungesetzt, also muss
        // dies exakt dem Default-Pfad entsprechen.
        let mut rng = StdRng::seed_from_u64(8111);
        let mut checked = 0;
        for gi in 0..8u64 {
            let Some(state) = random_drafting_state(gi, 16, &mut rng) else { continue };
            for v in [[0.5f64, 0.5f64], [0.9, 0.2], [0.0, 1.0], [1.0, 0.0]] {
                assert_eq!(apply_scoring_shaping(v, &state), v);
            }
            checked += 1;
        }
        assert!(checked >= 4, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    #[test]
    fn net_leaf_eval_matches_pre_scoring_shaping_path_when_weight_is_zero() {
        // Staerkster verfuegbarer Neutralitaets-Nachweis: rekonstruiert den
        // `net_leaf_eval`-Rechenweg exakt bis VOR den neuen
        // `apply_scoring_shaping`-Aufruf (Mover-/Gegner-Forward-Pass +
        // `blended_leaf_win_prob` + `apply_value_shrink`, alles unveraendert)
        // und vergleicht bit-genau gegen den TATSAECHLICHEN
        // `net_leaf_eval`-Output. Gleiches Muster wie
        // `net_leaf_eval_matches_legacy_value_to_win_prob_when_w_is_zero`
        // (Task #28) fuer den `blended_leaf_win_prob`-Blend.
        let net = load_test_net();
        assert_eq!(
            scoring_shaping_weight(),
            0.0,
            "Test-Voraussetzung: MOSAIC_WERTUNG_SHAPING_W darf hier nicht gesetzt sein"
        );

        let mut rng = StdRng::seed_from_u64(8100);
        let mut checked = 0;
        for gi in 0..10u64 {
            let Some(state) = random_drafting_state(gi, 14, &mut rng) else { continue };
            let actual = net_leaf_eval(&net, &state);

            // Alt-Pfad (Stand VOR diesem Additiv): identische Vorstufe, aber
            // OHNE den anschliessenden `apply_scoring_shaping`-Aufruf.
            let feats = crate::features::features_for_net(&net, &state);
            let mut flipped = state.clone();
            flipped.current_player = 1 - state.current_player;
            let other_feats = crate::features::features_for_net(&net, &flipped);
            let (
                (_l, value, _m, points, opp_points, _own),
                (_ol, o_value, _om, o_points, o_opp_points, _o_own),
            ) = net.eval_pair_ex(&feats, &other_feats).expect("eval_pair_ex (Alt-Pfad)");
            let mover_val = blended_leaf_win_prob(&value, &points, &opp_points);
            let other_val = blended_leaf_win_prob(&o_value, &o_points, &o_opp_points);
            let raw = if state.current_player == 0 { [mover_val, other_val] } else { [other_val, mover_val] };
            let expected = apply_value_shrink(raw, state.round_number);

            assert_eq!(actual, expected, "Spiel {gi}: net_leaf_eval weicht bei w=0 vom Alt-Pfad ab");
            checked += 1;
        }
        assert!(checked >= 6, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    #[test]
    fn apply_scoring_shaping_with_is_per_player_absolute_not_ego_only() {
        // Nutzer-Korrektur 2026-08-11: "ego-only" (nur der ziehende Spieler
        // bekommt einen Zuschlag) war eine FALSCHE Lesart der urspruenglichen
        // Vorgabe -- beide Spieler bekommen unabhaengig je einen Zuschlag aus
        // ihrem EIGENEN Brett (`state.players[i]`), sonst wuerde die Suche
        // annehmen, der GEGNER ignoriere die Wertungsplatten (dieselbe
        // Self-Play-Blindheit wie ausserhalb der Suche). Beweist drei
        // Eigenschaften in einem Test:
        //   1. die EXAKTE Formel je Spieler-Index `i`:
        //      `clamp(value[i] + w * tanh(scoring_progress_alpha(players[i],
        //      scoring_tile_ids, alpha) / WERTUNG_SHAPING_SCALE), 0, 1)`.
        //   2. Index 0 haengt AUSSCHLIESSLICH von `players[0]` ab -- ein
        //      Tausch von `players[1]` (Gegnerbrett) darf Index 0 NICHT
        //      veraendern (kein Cross-Term zwischen den Spielern).
        //   3. UMKEHRUNG (das war die vom Nutzer explizit verlangte
        //      Ergaenzung): derselbe Tausch MUSS Index 1 veraendern, sofern
        //      sich `scoring_progress_alpha` fuer `players[1]` tatsaechlich
        //      unterscheidet -- der Gegner-Fortschritt fliesst also SEHR
        //      wohl in den Blattwert ein, nur eben ausschliesslich ueber
        //      SEINEN EIGENEN Index, nicht in Index 0.
        let w = 0.4;
        let alpha = 1.5;
        let mut rng = StdRng::seed_from_u64(5551);
        let mut checked = 0;
        let mut index1_changed = 0;
        for gi in 0..8u64 {
            let Some(state_a) = random_drafting_state(gi, 12, &mut rng) else { continue };
            let Some(state_b) = random_drafting_state(gi + 500, 13, &mut rng) else { continue };
            let mut hybrid = state_a.clone();
            hybrid.players[1] = state_b.players[1].clone();

            for s in [&state_a, &hybrid] {
                let v = [0.5, 0.5];
                let out = apply_scoring_shaping_full(v, s, &[w; 8], &[alpha; 8], 0.0, 0.0, 0.0, false);
                for i in 0..2 {
                    // Seit der Zusammenfuehrung (2026-08-11) traegt der Term ALLE
                    // acht Kriterien: die gegateten sieben plus den
                    // Spezialfeld-Anteil mit `alphas[6]` als Exponent. Die
                    // Erwartung muss beides spiegeln, sonst prueft der Test eine
                    // Formel, die es nicht mehr gibt.
                    let alphas = [alpha; 8];
                    let pts = crate::scoring::scoring_progress_per_criterion(
                        &s.players[i], &s.scoring_tile_ids, &alphas, s.round_number, 0.0,
                    ) + crate::scoring::unlock_progress_beta(
                        &s.players[i], &s.scoring_tile_ids, alpha,
                    );
                    let expected = (v[i] + w * (pts / WERTUNG_SHAPING_SCALE).tanh()).clamp(0.0, 1.0);
                    assert!(
                        (out[i] - expected).abs() < 1e-12,
                        "Spiel {gi}: Index {i} weicht von der Formel ab (out={out:?})"
                    );
                }
            }

            let out_a = apply_scoring_shaping_full([0.5, 0.5], &state_a, &[w; 8], &[alpha; 8], 0.0, 0.0, 0.0, false);
            let out_hybrid = apply_scoring_shaping_full([0.5, 0.5], &hybrid, &[w; 8], &[alpha; 8], 0.0, 0.0, 0.0, false);
            // (2) Index 0 unveraendert -- `players[0]` ist zwischen `state_a`
            // und `hybrid` identisch geblieben.
            assert_eq!(
                out_a[0], out_hybrid[0],
                "Spiel {gi}: Index 0 haengt faelschlich vom GEGNERBRETT ab"
            );
            // (3) Index 1 reagiert -- nur zaehlen/pruefen, wenn die beiden
            // Bretter tatsaechlich unterschiedlichen Fortschritt haben
            // (sonst waere eine Gleichheit kein Gegenbeweis, nur Zufall).
            let ges = |st: &GameState| {
                let a = [alpha; 8];
                crate::scoring::scoring_progress_per_criterion(
                    &st.players[1], &st.scoring_tile_ids, &a, st.round_number, 0.0)
                + crate::scoring::unlock_progress_beta(&st.players[1], &st.scoring_tile_ids, alpha)
            };
            let pts_a1 = ges(&state_a);
            let pts_b1 = ges(&hybrid);
            if (pts_a1 - pts_b1).abs() > 1e-9 {
                assert_ne!(
                    out_a[1], out_hybrid[1],
                    "Spiel {gi}: Index 1 MUSS auf den Brett-Tausch reagieren (per-Spieler-absolut, nicht ego-only)"
                );
                index1_changed += 1;
            }
            checked += 1;
        }
        assert!(checked >= 4, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");

        // Teil 3 DETERMINISTISCH, nicht aus Zufallsstellungen (Aenderung
        // 2026-08-11): seit Kriterium 6 aus `scoring_progress_alpha` heraus ist
        // (es haelt `unlock_progress_beta`, sonst Doppelzaehlung), liefert die
        // Funktion auf FRUEHEN Drafting-Stellungen fuer beide Seiten 0 -- alle
        // konjunktiven Kriterien brauchen Kuppelfuellung, und die gibt es dort
        // noch nicht. Der Zufallsaufbau konnte die Eigenschaft damit nicht mehr
        // belegen (`index1_changed` blieb 0, der Waechter des Tests hat das
        // korrekt gemeldet statt still durchzulaufen). Statt den Waechter
        // aufzuweichen: dieselbe Aussage deterministisch, Muster wie im
        // Nachbartest `..._both_sides_gain_no_antisymmetry`.
        let mut rng2 = StdRng::seed_from_u64(70012);
        let mut det = setup_new_game(names(), 0, &mut rng2);
        det.scoring_tile_ids = vec![4]; // linear, positiv fuer jedes n>0
        det.players[0] = board_with_border_fill(3);
        det.players[1] = board_with_border_fill(2);
        let mut det_swapped = det.clone();
        det_swapped.players[1] = board_with_border_fill(5); // NUR Gegnerbrett anders

        let o1 = apply_scoring_shaping_full([0.5, 0.5], &det, &[w; 8], &[alpha; 8], 0.0, 0.0, 0.0, false);
        let o2 = apply_scoring_shaping_full([0.5, 0.5], &det_swapped, &[w; 8], &[alpha; 8], 0.0, 0.0, 0.0, false);
        assert_eq!(o1[0], o2[0], "Index 0 darf nicht vom Gegnerbrett abhaengen");
        assert_ne!(
            o1[1], o2[1],
            "Index 1 MUSS auf den Gegnerbrett-Tausch reagieren (per-Spieler-absolut, nicht ego-only)"
        );
        assert!(o2[1] > o1[1], "mehr Gegnerfortschritt muss Index 1 ERHOEHEN, nicht senken");
        let _ = index1_changed;
    }

    #[test]
    fn apply_scoring_shaping_with_both_sides_gain_no_antisymmetry() {
        // Waechter gegen eine Rueckkehr zur `apply_plate_shaping`-Form
        // (`[+shift, -shift]`): wenn BEIDE Spieler Wertungsplatten-
        // Fortschritt haben, muessen BEIDE Indizes STEIGEN (nicht einer rauf,
        // der andere runter) -- die Zuschlaege sind unabhaengig und typisch
        // beide positiv, nicht komplementaer. Deterministischer Aufbau (statt
        // zufaellig gesuchter Stellungen, die haeufig nur auf EINER Seite
        // Fortschritt haben) ueber `board_with_border_fill` -- Kriterium 4
        // ist linear, aber positiv fuer JEDES `n>0`, das reicht hier.
        let mut rng = StdRng::seed_from_u64(70011);
        let mut state = setup_new_game(names(), 0, &mut rng);
        state.players[0] = board_with_border_fill(3);
        state.players[1] = board_with_border_fill(2);
        state.scoring_tile_ids = vec![4];

        let p0 = crate::scoring::scoring_progress_alpha(&state.players[0], &state.scoring_tile_ids, 2.0);
        let p1 = crate::scoring::scoring_progress_alpha(&state.players[1], &state.scoring_tile_ids, 2.0);
        assert!(p0 > 0.0 && p1 > 0.0, "Testaufbau: beide Seiten brauchen echten Fortschritt (p0={p0}, p1={p1})");

        let out = apply_scoring_shaping_full([0.5, 0.5], &state, &[0.5; 8], &[2.0; 8], 0.0, 0.0, 0.0, false);
        assert!(out[0] > 0.5, "Index 0 sollte steigen (p0={p0}), war {}", out[0]);
        assert!(out[1] > 0.5, "Index 1 sollte steigen (p1={p1}), war {}", out[1]);
    }

    /// Baut ein `PlayerBoard` mit EXAKT `n` gefuellten Zellen in der 6x6-
    /// Zeile 0 (`n` in 0..=6) -- Zeile 0 ist zur Gaenze Rand (`r==0`), also
    /// liefert Kriterium 4 (`border_fill`, LINEAR/kein Exponent in
    /// `scoring_progress_alpha`) fuer dieses Brett exakt `n` zurueck. Nutzt
    /// bis zu 3 Slots (`sr=0`, `sc=0..2`, je 2 Zellen ueber `si` in
    /// `{0,1}` -- siehe `build_grid`s Index-Mapping).
    fn board_with_border_fill(n: usize) -> crate::board::PlayerBoard {
        let mut p = crate::board::PlayerBoard::new(0, "P");
        let pool = crate::dome::build_dome_tile_pool();
        let mut remaining = n;
        for sc in 0..3usize {
            if remaining == 0 {
                break;
            }
            let mut t = pool[sc].clone();
            for (si, sp) in t.spaces.iter_mut().enumerate() {
                if si / 2 != 0 || remaining == 0 {
                    continue;
                }
                match sp.space_type {
                    crate::dome::SpaceType::Special => {
                        sp.is_locked = false;
                        sp.placed_special = true;
                    }
                    crate::dome::SpaceType::Wild => sp.placed_color = Some(TileColor::Rot),
                    crate::dome::SpaceType::Normal => sp.placed_color = sp.required_color,
                }
                remaining -= 1;
            }
            p.dome_grid.place_dome_tile(t, 0, sc).unwrap();
        }
        assert_eq!(remaining, 0, "Testaufbau: nicht genug Platz fuer n={n} (max. 6)");
        p
    }

    #[test]
    fn apply_scoring_shaping_with_rejects_difference_form_same_margin_different_level() {
        // Waechter gegen die AUSDRUECKLICH VERBOTENE `mine-minus-theirs`-Form
        // (stehende Nutzer-Anforderung: "ohne Differenzrechnung ... sonst ist
        // 55 vs. 50 schlechter als 30 vs. 15"). Kriterium 4 (`border_fill`)
        // ist LINEAR -- ideal, um einen EXAKTEN Vorsprung zu konstruieren:
        // Paar "low" hat Vorsprung 1-0=1, Paar "high" hat Vorsprung 5-4=1 --
        // GLEICHER Vorsprung, aber unterschiedliches Niveau. Eine
        // `mine-minus-theirs`-Formel waere fuer beide Paare IDENTISCH (der
        // Vorsprung ist ja gleich); die tatsaechliche (absolute, je Spieler
        // unabhaengige) Formel muss UNTERSCHIEDLICHE Werte liefern.
        let mut rng = StdRng::seed_from_u64(70012);
        let mut low = setup_new_game(names(), 0, &mut rng);
        low.players[0] = board_with_border_fill(1);
        low.players[1] = board_with_border_fill(0);
        low.scoring_tile_ids = vec![4];

        let mut high = setup_new_game(names(), 0, &mut rng);
        high.players[0] = board_with_border_fill(5);
        high.players[1] = board_with_border_fill(4);
        high.scoring_tile_ids = vec![4];

        // Vorbedingung: gleicher Vorsprung in beiden Paaren.
        let margin_low = crate::scoring::scoring_progress_alpha(&low.players[0], &low.scoring_tile_ids, 2.0)
            - crate::scoring::scoring_progress_alpha(&low.players[1], &low.scoring_tile_ids, 2.0);
        let margin_high = crate::scoring::scoring_progress_alpha(&high.players[0], &high.scoring_tile_ids, 2.0)
            - crate::scoring::scoring_progress_alpha(&high.players[1], &high.scoring_tile_ids, 2.0);
        assert!(
            (margin_low - margin_high).abs() < 1e-9,
            "Testaufbau: Vorsprung sollte in beiden Faellen 1 sein (low={margin_low}, high={margin_high})"
        );

        let out_low = apply_scoring_shaping_full([0.5, 0.5], &low, &[0.5; 8], &[2.0; 8], 0.0, 0.0, 0.0, false);
        let out_high = apply_scoring_shaping_full([0.5, 0.5], &high, &[0.5; 8], &[2.0; 8], 0.0, 0.0, 0.0, false);
        assert!(
            (out_low[0] - out_high[0]).abs() > 1e-6,
            "gleicher Vorsprung, unterschiedliches Niveau MUSS unterschiedliche Werte liefern \
             (Differenzform-Verdacht): low={out_low:?} high={out_high:?}"
        );
    }

    #[test]
    fn apply_scoring_shaping_with_clamps_extreme_shifts_to_unit_interval() {
        // `tanh` allein haelt den Shift schon in `(-w, w)`, aber bei grossem
        // `w` (> 0.5) kann `value[i] + shift` trotzdem ausserhalb `[0,1]`
        // rutschen -- muss wie die bestehende Floor-/Platten-Additiv-Logik
        // geklemmt werden.
        let mut rng = StdRng::seed_from_u64(8112);
        let Some(state) = random_drafting_state(0, 16, &mut rng) else {
            panic!("Testaufbau: random_drafting_state lieferte keinen Zustand");
        };
        let out_hi = apply_scoring_shaping_full([0.95, 0.05], &state, &[5.0; 8], &[2.0; 8], 0.0, 0.0, 0.0, false);
        let out_lo = apply_scoring_shaping_full([0.05, 0.95], &state, &[5.0; 8], &[2.0; 8], 0.0, 0.0, 0.0, false);
        for v in out_hi.iter().chain(out_lo.iter()) {
            assert!((0.0..=1.0).contains(v), "Shift muss auf [0,1] geklemmt sein, war {v}");
        }
    }

    // ── Baustein 3: MOSAIC_WERTUNG_SCALE_PROFILE (PREREG_shaping_scale_per_round.md) ──

    /// Default (Env-Var ungesetzt) muss aus sein.
    #[test]
    fn scoring_scale_profile_active_defaults_to_off() {
        assert!(
            !scoring_scale_profile_active(),
            "MOSAIC_WERTUNG_SCALE_PROFILE muss bei ungesetzter Env-Var aus sein (Bestandsverhalten)"
        );
    }

    /// (a) `scoring_scale_for_round` reproduziert bei inaktivem Profil in
    /// JEDER Runde exakt die alte feste Konstante -- unabhaengig von der
    /// Runde. Alte Konstante hier bewusst als Literal nachgebaut, nicht aus
    /// `WERTUNG_SHAPING_SCALE` gelesen (REGEL 0: der Test darf eine falsche
    /// Aenderung an der Konstante nicht mitfeiern).
    #[test]
    fn scoring_scale_for_round_is_always_the_old_constant_with_inactive_profile() {
        const ALTE_KONSTANTE: f64 = 50.0;
        for r in 1..=5u32 {
            assert_eq!(
                scoring_scale_for_round(r, false),
                ALTE_KONSTANTE,
                "Runde {r}: inaktives Profil muss immer den flachen Nenner 50 liefern"
            );
        }
        // Auch ausserhalb 1..5 (Clamp-Pfad) bei inaktivem Profil unveraendert.
        assert_eq!(scoring_scale_for_round(0, false), ALTE_KONSTANTE);
        assert_eq!(scoring_scale_for_round(9, false), ALTE_KONSTANTE);
    }

    /// (b) Aktives Profil liefert je Runde `50 * profil_r` aus par.4 und
    /// weicht damit von der flachen Konstante ab (ausser evtl. bei
    /// Rundungszufall, hier durch die konkreten par.4-Werte ausgeschlossen).
    #[test]
    fn scoring_scale_for_round_follows_par4_with_active_profile() {
        let erwartet = [4.15, 8.6, 16.35, 25.75, 41.25];
        for (idx, &e) in erwartet.iter().enumerate() {
            let r = (idx + 1) as u32;
            let got = scoring_scale_for_round(r, true);
            assert!(
                (got - e).abs() < 1e-9,
                "Runde {r}: erwartet SCALE_r={e} (par.4), war {got}"
            );
            assert_ne!(got, WERTUNG_SHAPING_SCALE, "Runde {r}: aktives Profil darf nicht auf dem flachen Nenner liegen");
        }
    }

    /// Clamp-Pfad bei aktivem Profil: Runde 0/9 muessen auf Runde 1/5 fallen
    /// (gleiche Klemmung wie die bestehende `t`-Berechnung im Wertungs-Pfad).
    #[test]
    fn scoring_scale_for_round_clamps_outside_1_to_5() {
        assert_eq!(scoring_scale_for_round(0, true), scoring_scale_for_round(1, true));
        assert_eq!(scoring_scale_for_round(9, true), scoring_scale_for_round(5, true));
    }

    /// (a) FORMEL-BELEG: `apply_scoring_shaping_full` mit `scale_profile_active
    /// = false` reproduziert bitgleich die ALTE Formel `tanh(pts/50)` -- exakt
    /// derselbe Aufbau wie der bestehende Formel-Beleg-Test oben, nur mit der
    /// ausdruecklichen Behauptung "Default aendert nichts".
    #[test]
    fn apply_scoring_shaping_full_with_inactive_profile_reproduces_old_formula_bit_exactly() {
        const ALTE_KONSTANTE: f64 = 50.0;
        let mut rng = StdRng::seed_from_u64(20260819200);
        let Some(state) = random_drafting_state(11, 16, &mut rng) else {
            panic!("Testaufbau: random_drafting_state lieferte keinen Zustand");
        };
        let w = 0.4;
        let alpha = 1.5;
        let v = [0.5, 0.5];
        let out = apply_scoring_shaping_full(v, &state, &[w; 8], &[alpha; 8], 0.0, 0.0, 0.0, false);
        for i in 0..2 {
            let alphas = [alpha; 8];
            let pts = crate::scoring::scoring_progress_per_criterion(
                &state.players[i], &state.scoring_tile_ids, &alphas, state.round_number, 0.0,
            ) + crate::scoring::unlock_progress_beta(
                &state.players[i], &state.scoring_tile_ids, alpha,
            );
            let expected = (v[i] + w * (pts / ALTE_KONSTANTE).tanh()).clamp(0.0, 1.0);
            assert!(
                (out[i] - expected).abs() < 1e-12,
                "Index {i}: inaktives Profil muss bitgleich tanh(pts/50) liefern (out={out:?})"
            );
        }
    }

    /// (b) Aktives Profil AENDERT das Ergebnis gegenueber inaktivem Profil,
    /// wenn ein Wertungsplatten-Gewicht > 0 gesetzt ist. DETERMINISTISCHER
    /// Aufbau statt Zufallsstellung (gleiches Muster wie Teil 3 des
    /// Geschwister-Tests oben, `board_with_border_fill` + Kriterium 4 --
    /// linear, garantiert positiv fuer JEDES `n>0`, unabhaengig von der
    /// Runde -- eine Zufallsstellung koennte zufaellig 0 Fortschritt haben
    /// und den Test scheinlos gruen machen).
    #[test]
    fn apply_scoring_shaping_full_with_active_profile_changes_the_result() {
        let mut rng = StdRng::seed_from_u64(70099);
        let mut state = setup_new_game(names(), 0, &mut rng);
        state.round_number = 3;
        state.scoring_tile_ids = vec![4]; // linear, positiv fuer jedes n>0
        state.players[0] = board_with_border_fill(3);
        state.players[1] = board_with_border_fill(2);
        let w = 0.4;
        let alpha = 1.5;
        let v = [0.5, 0.5];
        let out_aus = apply_scoring_shaping_full(v, &state, &[w; 8], &[alpha; 8], 0.0, 0.0, 0.0, false);
        let out_an = apply_scoring_shaping_full(v, &state, &[w; 8], &[alpha; 8], 0.0, 0.0, 0.0, true);
        assert_ne!(
            out_aus, out_an,
            "aktives Profil muss das Ergebnis gegenueber dem flachen Default veraendern (Runde 3, w={w})"
        );
    }

    /// par.6a-Praezisierung, geprueft: der Strafleisten-Term (`floor_w`) und
    /// der Tiling-Term (`tiling_w`) bleiben auf dem FLACHEN Nenner, auch wenn
    /// das Profil aktiv ist -- alle Wertungsplatten-Gewichte hier auf 0, NUR
    /// `floor_w`/`tiling_w` gesetzt, damit der Test ausschliesslich deren
    /// Pfad trifft. ZWEI Belege: (1) profil AN/AUS darf den Output nicht
    /// unterscheiden, (2) der Output bei aktivem Profil muss trotzdem exakt
    /// der FLACHEN Formel entsprechen -- (2) bleibt auch dann aussagekraeftig,
    /// wenn `projected_unplaceable_penalty`/`tiling_potenzial` fuer diese
    /// konkrete Zufallsstellung 0 sein sollten (Praezedenz: `PREREG_shaping_
    /// scale_per_round.md` par.6a Fund 2 -- beide sind in Self-Play-Stichproben
    /// oft 0), weil die Formel unabhaengig vom Wert geprueft wird.
    #[test]
    fn apply_scoring_shaping_full_floor_and_tiling_term_stay_on_flat_denominator_with_active_profile() {
        const ALTE_KONSTANTE: f64 = 50.0;
        let mut rng = StdRng::seed_from_u64(20260819202);
        let Some(mut state) = random_drafting_state(15, 16, &mut rng) else {
            panic!("Testaufbau: random_drafting_state lieferte keinen Zustand");
        };
        state.round_number = 3;
        let v = [0.5, 0.5];
        let floor_w = 0.3;
        let tiling_w = 0.2;
        let out_aus = apply_scoring_shaping_full(v, &state, &[0.0; 8], &[2.0; 8], 0.0, floor_w, tiling_w, false);
        let out_an = apply_scoring_shaping_full(v, &state, &[0.0; 8], &[2.0; 8], 0.0, floor_w, tiling_w, true);
        assert_eq!(
            out_aus, out_an,
            "Strafleisten-/Tiling-Term duerfen sich NICHT aendern, wenn nur das Profil umgeschaltet wird \
             (par.6a: beide bleiben auf dem flachen Nenner)"
        );
        for i in 0..2 {
            let floor_pts = crate::round_end::projected_unplaceable_penalty(&state.players[i]) as f64;
            let tiling_pts = tiling_potenzial(&state, i);
            let expected = (v[i]
                + floor_w * (floor_pts / ALTE_KONSTANTE).tanh()
                + tiling_w * (tiling_pts / ALTE_KONSTANTE).tanh())
            .clamp(0.0, 1.0);
            assert!(
                (out_an[i] - expected).abs() < 1e-12,
                "Index {i}: Strafleisten-/Tiling-Term bei AKTIVEM Profil muessen trotzdem exakt der \
                 flachen Formel tanh(x/50) folgen (out_an={out_an:?})"
            );
        }
    }

    // ═══════════════════════════════════════════════════════════════════
    // Freischalt-Shaping (Nutzer-Auftrag 2026-08-10, `watchlist_v20_
    // zwischenlese.md` Abschnitt 2) -- eigener Block, gleiches Muster wie
    // das Wertungsplatten-EGO-Shaping oben, aber eigener Knopf/eigene Formel
    // (`unlock_progress_beta`, siehe dortiger Modul-Kommentar).
    // ═══════════════════════════════════════════════════════════════════

    #[test]
    fn alte_unlock_knoepfe_sind_zurueckgebaut() {
        // Seit der Zusammenfuehrung 2026-08-11 gibt es NUR NOCH ein Gewicht
        // (`MOSAIC_WERTUNG_SHAPING_W`) und alpha[6] als Spezialfeld-Exponent.
        // Die alten Getter sind entfernt -- ein still wirkungsloser Regler ist
        // gefaehrlicher als ein fehlender, weil jemand ihn setzt, ein H0 liest
        // und auf den Term schliesst. Wer die alten Variablen setzt, bekommt
        // jetzt eine Meldung auf stderr (siehe `scoring_shaping_alphas`).
        //
        // Die Compile-Konstanten bleiben als Dokumentation der Default-Werte.
        assert_eq!(UNLOCK_SHAPING_WEIGHT, 0.0);
        assert_eq!(UNLOCK_SHAPING_BETA, 2.0);
        // Und der zusammengefuehrte Term ist bei Default-Gewicht inert:
        let mut rng = StdRng::seed_from_u64(4711);
        let state = setup_new_game(names(), 0, &mut rng);
        let v = [0.42, 0.58];
        assert_eq!(apply_scoring_shaping(v, &state), v,
                   "bei MOSAIC_WERTUNG_SHAPING_W=0 muss der Blattwert unveraendert bleiben");
    }

    #[test]
    fn merged_shaping_is_exact_identity_by_default() {
        let mut rng = StdRng::seed_from_u64(9111);
        let mut checked = 0;
        for gi in 0..8u64 {
            let Some(state) = random_drafting_state(gi, 16, &mut rng) else { continue };
            for v in [[0.5f64, 0.5f64], [0.9, 0.2], [0.0, 1.0], [1.0, 0.0]] {
                // Nach der Zusammenfuehrung 2026-08-11 gibt es keinen eigenen
                // Unlock-Aufruf mehr -- geprueft wird der EINE Term, der jetzt
                // alle acht Kriterien traegt.
                assert_eq!(apply_scoring_shaping(v, &state), v);
            }
            checked += 1;
        }
        assert!(checked >= 4, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    /// Punkt 5 (Verdrahtung der Partie-Streuung, verschoben nach
    /// `run_net_self_play`): `set_game_shaping_weight`/`partie_gewicht_
    /// aus_seed` haengen an KEINEM env-var-OnceLock (anders als
    /// `scoring_scatter_max()` selbst) -- hier direkt pruefbar, ohne die
    /// uebliche Cache-nach-erstem-Zugriff-Falle.
    #[test]
    fn set_game_shaping_weight_overrides_default_but_only_on_the_setting_thread() {
        // (1) Gesetzt auf DIESEM Thread veraendert apply_scoring_shaping die
        // sonst bei Default (alle acht Gewichte 0) unveraenderte Blattbewertung.
        let mut rng = StdRng::seed_from_u64(55001);
        let mut changed = 0;
        let mut checked = 0;
        for gi in 0..8u64 {
            let Some(state) = random_drafting_state(gi, 16, &mut rng) else { continue };
            if state.scoring_tile_ids.is_empty() {
                continue;
            }
            let v = [0.5, 0.5];
            set_game_shaping_weight(None);
            let baseline = apply_scoring_shaping(v, &state);
            set_game_shaping_weight(Some(0.7));
            let overridden = apply_scoring_shaping(v, &state);
            set_game_shaping_weight(None); // aufraeumen, sonst leckt's in Folgetests auf diesem Thread
            if overridden != baseline {
                changed += 1;
            }
            checked += 1;
        }
        assert!(checked >= 4, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
        assert!(changed >= 1, "PARTIE_GEWICHT-Override veraenderte in keinem Fall die Blattbewertung");

        // (2) Thread-Lokalitaet: gesetzt auf einem ANDEREN (Watchdog-artigen)
        // Thread bleibt der AUFRUFENDE Thread unberuehrt -- exakt die
        // Voraussetzung, unter der `run_net_self_play` die Streuung INNERHALB
        // der `run_with_watchdog`-Closure setzen muss (self_play.rs, dortiger
        // Kommentar), nicht in der aeusseren Rayon-Closure: ein Setzen auf dem
        // falschen Thread waere unbemerkt wirkungslos.
        let mut rng2 = StdRng::seed_from_u64(55002);
        let Some(state2) = random_drafting_state(0, 16, &mut rng2) else {
            panic!("Testaufbau: random_drafting_state lieferte keinen Zustand");
        };
        set_game_shaping_weight(None);
        let before = apply_scoring_shaping([0.5, 0.5], &state2);
        std::thread::spawn(|| {
            set_game_shaping_weight(Some(0.9));
        })
        .join()
        .unwrap();
        let after = apply_scoring_shaping([0.5, 0.5], &state2);
        assert_eq!(
            before, after,
            "PARTIE_GEWICHT eines FREMDEN Threads darf den aufrufenden Thread nicht beeinflussen"
        );
    }

    #[test]
    fn net_leaf_eval_matches_pre_unlock_shaping_path_when_weight_is_zero() {
        // Gleiches Muster wie `net_leaf_eval_matches_pre_wertung_shaping_
        // path_when_weight_is_zero`: rekonstruiert `net_leaf_eval` bis
        // EINSCHLIESSLICH des (bei Default ebenfalls inerten) Wertungsplatten-
        // EGO-Shaping, aber OHNE den neuen `apply_unlock_shaping`-Aufruf, und
        // vergleicht bit-genau gegen den tatsaechlichen Output.
        let net = load_test_net();

        let mut rng = StdRng::seed_from_u64(9100);
        let mut checked = 0;
        for gi in 0..10u64 {
            let Some(state) = random_drafting_state(gi, 14, &mut rng) else { continue };
            let actual = net_leaf_eval(&net, &state);

            let feats = crate::features::features_for_net(&net, &state);
            let mut flipped = state.clone();
            flipped.current_player = 1 - state.current_player;
            let other_feats = crate::features::features_for_net(&net, &flipped);
            let (
                (_l, value, _m, points, opp_points, _own),
                (_ol, o_value, _om, o_points, o_opp_points, _o_own),
            ) = net.eval_pair_ex(&feats, &other_feats).expect("eval_pair_ex (Alt-Pfad)");
            let mover_val = blended_leaf_win_prob(&value, &points, &opp_points);
            let other_val = blended_leaf_win_prob(&o_value, &o_points, &o_opp_points);
            let raw = if state.current_player == 0 { [mover_val, other_val] } else { [other_val, mover_val] };
            let expected = apply_scoring_shaping(apply_value_shrink(raw, state.round_number), &state);

            assert_eq!(actual, expected, "Spiel {gi}: net_leaf_eval weicht bei w=0 vom Alt-Pfad ab");
            checked += 1;
        }
        assert!(checked >= 6, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    // ═══════════════════════════════════════════════════════════════════
    // Task #28 (`evaluations/PREREG_task28_aggression.md`): Score-/Denial-
    // Utility -- Engine-Seite (Utility-Blend, Laufzeit-Parameter, ONNX-
    // Vertrag-Erkennung).
    // ═══════════════════════════════════════════════════════════════════

    /// Laedt `alphazero_v18_best.onnx` -- flaches Legacy-Modell OHNE
    /// `opp_points`-Kopf, lokal vorhanden (anders als `load_test_net()`s
    /// `v10`, siehe dortiger Kommentar). Gleiches Skip-statt-Fail-Muster bei
    /// Abwesenheit (frischer Klon ohne `models/`, `.gitignore`).
    fn load_v18_legacy_test_net() -> Option<Net> {
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../models/alphazero_v18_best.onnx");
        Net::load_auto(path.to_str().unwrap()).ok()
    }

    // ── Byte-Identitaet bei w=0 (Default) gegen den Alt-Pfad ──

    /// `net_leaf_eval` muss bei `w=0` (Default, keine `MOSAIC_POINTS_UTILITY_
    /// W`-Env-Var in dieser Test-Umgebung gesetzt) exakt denselben Blattwert
    /// liefern wie der Alt-Pfad VOR Task #28: reiner `value_to_win_prob`-
    /// Blend ohne jeden Punkte-Anteil (`POINTS_UTILITY_WEIGHT=0` machte
    /// `blended_leaf_win_prob` schon vor diesem Task numerisch identisch zu
    /// `value_to_win_prob`, siehe dortiger GETESTET-Kommentar) -- verglichen
    /// gegen einen direkten `eval_pair`-Aufruf (nicht `eval_pair_ex`), der
    /// ALT-Pfad-Code also unveraendert.
    #[test]
    fn net_leaf_eval_matches_legacy_value_to_win_prob_when_w_is_zero() {
        let Some(net) = load_v18_legacy_test_net() else { return };
        assert!(!net.has_opp_head(), "v18_best hat noch keinen opp_points-Kopf (Vertrag noch nicht exportiert)");
        assert_eq!(points_utility_w(), 0.0, "Test-Voraussetzung: MOSAIC_POINTS_UTILITY_W darf hier nicht gesetzt sein");

        let mut rng = StdRng::seed_from_u64(2801);
        let mut checked = 0;
        for seed_tag in 0..8u64 {
            let Some(state) = random_drafting_state(seed_tag, 6, &mut rng) else { continue };
            let actual = net_leaf_eval(&net, &state);

            // Alt-Pfad: direkter `eval_pair` (kein `_ex`), reines
            // `value_to_win_prob` je Perspektive, keine Punkte-Beteiligung.
            let feats = crate::features::features_for_net(&net, &state);
            let mut flipped = state.clone();
            flipped.current_player = 1 - state.current_player;
            let other_feats = crate::features::features_for_net(&net, &flipped);
            let ((_l, value, _m, _p), (_ol, o_value, _om, _op)) =
                net.eval_pair(&feats, &other_feats).expect("eval_pair (Alt-Pfad)");
            let mover_val = value_to_win_prob(&value);
            let other_val = value_to_win_prob(&o_value);
            let expected =
                if state.current_player == 0 { [mover_val, other_val] } else { [other_val, mover_val] };

            assert!(
                (actual[0] - expected[0]).abs() < 1e-12 && (actual[1] - expected[1]).abs() < 1e-12,
                "Spiel {seed_tag}: net_leaf_eval {actual:?} weicht vom Alt-Pfad {expected:?} ab"
            );
            checked += 1;
        }
        assert!(checked >= 4, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    /// Gleicher Nachweis auf `blended_leaf_win_prob`-Ebene direkt (ohne
    /// Netz/State) -- egal was in `points`/`opp_points` steht, bei `w=0`
    /// muss IMMER `value_to_win_prob(value)` herauskommen (Early-Out, kein
    /// zusaetzlicher Rechenpfad).
    #[test]
    fn blended_leaf_win_prob_with_w_zero_ignores_points_and_opp_entirely() {
        let value = vec![0.3f32];
        let wr = value_to_win_prob(&value);
        assert_eq!(blended_leaf_win_prob_with(&value, &[], &[], 0.0, 0.0, 0.0, 1.0), wr);
        assert_eq!(blended_leaf_win_prob_with(&value, &[0.9], &[], 0.0, 0.0, 0.0, 1.0), wr);
        assert_eq!(blended_leaf_win_prob_with(&value, &[0.9], &[-0.7], 0.0, 5.0, 0.0, 1.0), wr);
        assert_eq!(blended_leaf_win_prob_with(&value, &[0.9], &[-0.7], 0.0, 0.0, 0.0, 1.0), wr);
    }

    /// `w>0`, aber `opp_points` leer (Legacy-Modell ohne den Kopf) -> muss
    /// sich wie `w=0` verhalten (Additiv-Regel, PREREG Punkt 4), NICHT wie
    /// der `w>0`-Blend mit `opp_raw=0`.
    #[test]
    fn blended_leaf_win_prob_with_missing_opp_head_falls_back_to_legacy() {
        let value = vec![0.3f32];
        let points = vec![0.6f32];
        let wr = value_to_win_prob(&value);
        let via_missing_opp = blended_leaf_win_prob_with(&value, &points, &[], 0.5, 1.0, 0.0, 1.0);
        assert_eq!(via_missing_opp, wr, "fehlender opp-Kopf muss exakt den w=0-Legacy-Pfad liefern");
    }

    // ── Reine Blend-Formel (`opp_aware_points_utility`, kein Netz/ONNX) ──

    #[test]
    fn opp_aware_points_utility_clamps_to_valid_tanh_range() {
        // Extreme Eingaben (own+eps*opp weit ausserhalb [-1,1]) muessen auf
        // den gueltigen Tanh-Bereich geklammert werden, BEVOR auf [0,1]
        // reskaliert wird -- sonst koennte `u` selbst ausserhalb [0,1] liegen.
        let u_hi = opp_aware_points_utility(10.0, 10.0, 0.0);
        let u_lo = opp_aware_points_utility(-10.0, -10.0, 0.0);
        assert_eq!(u_hi, 1.0);
        assert_eq!(u_lo, 0.0);
    }

    #[test]
    fn opp_aware_points_utility_zero_inputs_yield_midpoint() {
        assert_eq!(opp_aware_points_utility(0.0, 0.0, 0.0), 0.5);
        assert_eq!(opp_aware_points_utility(0.0, 0.0, 2.0), 0.5);
    }

    #[test]
    fn opp_aware_points_utility_higher_lambda_lowers_utility_for_positive_opp() {
        // Kernanspruch der PREREG ("Denial"): bei POSITIVEM `opp_raw`
        // (Gegner steht gut) muss ein hoeheres `lambda_aggr` die Utility
        // SENKEN (staerkerer Abzug) -- Wirkrichtung des Denial-Hebels.
        let pts_raw = 0.2;
        let opp_raw = 0.5;
        let u_low_lambda = opp_aware_points_utility(pts_raw, opp_raw, 0.0);
        let u_mid_lambda = opp_aware_points_utility(pts_raw, opp_raw, 1.0);
        let u_high_lambda = opp_aware_points_utility(pts_raw, opp_raw, 2.0);
        assert!(u_low_lambda > u_mid_lambda, "u(lambda=0) sollte > u(lambda=1) sein");
        assert!(u_mid_lambda > u_high_lambda, "u(lambda=1) sollte > u(lambda=2) sein");
    }

    #[test]
    fn opp_aware_points_utility_negative_opp_with_lambda_raises_utility() {
        // Symmetrisch: NEGATIVER `opp_raw` (Gegner steht schlecht) + Denial-
        // Abzug (`-lambda_aggr*opp_raw`) muss die Utility ANHEBEN.
        let u_no_lambda = opp_aware_points_utility(0.0, -0.5, 0.0);
        let u_with_lambda = opp_aware_points_utility(0.0, -0.5, 1.0);
        assert!(u_with_lambda > u_no_lambda);
    }

    #[test]
    fn opp_aware_points_utility_matches_hand_calculation() {
        // Schema 20 (VALUE_OPP_EPSILON = 0, Nutzer-Entscheid 2026-08-10):
        // own_pts = 0.4 + 0.0*0.2 = 0.4; combined = 0.4 - 0.5*0.2 = 0.30;
        // u = (0.30+1)*0.5 = 0.65.
        // VORHER (eps=0.1): own_pts 0.42 -> combined 0.32 -> u 0.66. Die
        // Differenz IST die entfernte Verunreinigung -- der Test haelt sie
        // sichtbar, statt sie stillschweigend nachzuziehen.
        let u = opp_aware_points_utility(0.4, 0.2, 0.5);
        assert!((u - 0.65).abs() < 1e-12, "u={u}, erwartet 0.65");
    }

    /// End-zu-Ende der VOLLEN `w>0`+opp-vorhanden-Blend-Formel ueber
    /// `blended_leaf_win_prob_with` (nicht nur den `opp_aware_points_utility`-
    /// Kern) -- deckt zusaetzlich den `(1-w)*wr + w*u_pts`-Aussenblend ab.
    #[test]
    fn blended_leaf_win_prob_with_full_blend_matches_hand_calculation() {
        // wr = value_to_win_prob([0.0]) = 0.5. points=[0.4], opp=[0.2],
        // lambda_aggr=0.5 -> u_pts=0.65 (siehe Test oben, Schema 20). w=0.5 ->
        // 0.5*0.5 + 0.5*0.65 = 0.575. (Vor Schema 20: 0.58.)
        let value = vec![0.0f32];
        let points = vec![0.4f32];
        let opp_points = vec![0.2f32];
        let u = blended_leaf_win_prob_with(&value, &points, &opp_points, 0.5, 0.5, 0.0, 1.0);
        // Toleranz 1e-6 statt 1e-12 -- `value`/`points` sind `f32`-Vektoren
        // (wie reale ONNX-Outputs), die Konvertierung nach `f64` fuer die
        // Blend-Arithmetik ist nicht bit-exakt zur reinen `f64`-Handrechnung.
        assert!((u - 0.575).abs() < 1e-6, "u={u}, erwartet 0.575");
    }

    // ── Env-Var-Parsing (`read_f64_env`) -- eindeutige, synthetische
    // Var-Namen je Test (NICHT die echten `MOSAIC_POINTS_UTILITY_W`/
    // `MOSAIC_AGGR_LAMBDA`, um den Prozess-weiten `OnceLock`-Cache anderer
    // Tests nicht zu beeinflussen UND um Races zwischen parallel laufenden
    // Tests auf demselben Env-Var-Namen auszuschliessen). ──

    #[test]
    fn read_f64_env_missing_var_yields_default() {
        let name = "MOSAIC_TEST_ENV_MISSING_28A";
        std::env::remove_var(name);
        assert_eq!(read_f64_env(name, 0.0), 0.0);
        assert_eq!(read_f64_env(name, 3.5), 3.5);
    }

    #[test]
    fn read_f64_env_valid_value_is_parsed() {
        let name = "MOSAIC_TEST_ENV_VALID_28B";
        std::env::set_var(name, "1.25");
        assert_eq!(read_f64_env(name, 0.0), 1.25);
        std::env::remove_var(name);
    }

    #[test]
    fn read_f64_env_negative_and_whitespace_values_are_parsed() {
        let name = "MOSAIC_TEST_ENV_NEG_28C";
        std::env::set_var(name, "  -2.0  ");
        assert_eq!(read_f64_env(name, 0.0), -2.0);
        std::env::remove_var(name);
    }

    #[test]
    fn read_f64_env_invalid_value_falls_back_to_default_no_panic() {
        let name = "MOSAIC_TEST_ENV_INVALID_28D";
        std::env::set_var(name, "not_a_number");
        // Darf nicht paniken -- Default zurueck, das Testende erreicht zu
        // haben ist bereits Teil des Nachweises.
        assert_eq!(read_f64_env(name, 0.7), 0.7);
        std::env::remove_var(name);
    }

    #[test]
    fn read_f64_env_empty_value_falls_back_to_default_no_panic() {
        let name = "MOSAIC_TEST_ENV_EMPTY_28E";
        std::env::set_var(name, "");
        assert_eq!(read_f64_env(name, 1.1), 1.1);
        std::env::remove_var(name);
    }

    /// Die gecachten Laufzeit-Getter selbst muessen (in dieser Test-Umgebung,
    /// in der die ECHTEN `MOSAIC_*`-Namen nie gesetzt werden) auf ihren
    /// dokumentierten Default `0.0` zurueckfallen.
    #[test]
    fn points_utility_w_and_aggr_lambda_default_to_zero() {
        assert_eq!(points_utility_w(), 0.0);
        assert_eq!(aggr_lambda(), 0.0);
    }

    // ── `set_aggression_params`/`get_aggression_params` (Task #28 GUI-Regler)
    // -- ANDERS als die reine Env-Var-Lese-Tests oben (`read_f64_env_*`,
    // eindeutige SYNTHETISCHE Var-Namen je Test) schreiben diese Tests auf
    // die ECHTEN Prozess-weiten `points_utility_w`/`aggr_lambda`-Zellen --
    // das ist der ganze Punkt des Atomic-Umbaus (Live-Regler). Das ist mit
    // `cargo test`s Standard-Parallelitaet (mehrere Tests im selben
    // Prozess/mehreren Threads) NICHT frei von Interferenz: ein anderer,
    // parallel laufender Test, der `points_utility_w()`/`aggr_lambda()`
    // liest (z.B. `points_utility_w_and_aggr_lambda_default_to_zero` oben
    // oder `net_leaf_eval_matches_legacy_value_to_win_prob_when_w_is_zero`),
    // kann waehrend des Test-Fensters hier einen zwischenzeitlich gesetzten
    // Nicht-Default-Wert sehen. `AGGRESSION_TEST_LOCK` serialisiert
    // wenigstens die Tests IN DIESER GRUPPE untereinander, UND jeder Test
    // stellt den Default (0.0, 0.0) am Ende wieder her (best effort) -- ein
    // vollstaendiger Ausschluss gegenueber ALLEN anderen Tests im Binary
    // waere nur mit globaler Serialisierung (`--test-threads=1`) oder einem
    // Mutex um wirklich jeden Lesezugriff moeglich; beides wuerde ueber
    // dieses additive Feature hinausgehen. Falls dieser Test-Block spaeter
    // sporadisch fehlschlaegt (Flakiness durch echte Parallelitaet), ist das
    // der bekannte Kompromiss, kein neuer Bug.
    static AGGRESSION_TEST_LOCK: std::sync::Mutex<()> = std::sync::Mutex::new(());

    #[test]
    fn set_aggression_params_round_trips_valid_values() {
        let _guard = AGGRESSION_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        set_aggression_params(0.1, 2.0);
        assert_eq!(get_aggression_params(), (0.1, 2.0));
        assert_eq!(points_utility_w(), 0.1);
        assert_eq!(aggr_lambda(), 2.0);
        set_aggression_params(0.0, 0.0);
    }

    #[test]
    fn set_aggression_params_clamps_w_to_zero_one() {
        let _guard = AGGRESSION_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        set_aggression_params(-3.5, 0.0);
        assert_eq!(get_aggression_params(), (0.0, 0.0), "w<0 muss auf 0.0 geklemmt werden");
        set_aggression_params(7.0, 0.0);
        assert_eq!(get_aggression_params(), (1.0, 0.0), "w>1 muss auf 1.0 geklemmt werden");
        set_aggression_params(0.0, 0.0);
    }

    #[test]
    fn set_aggression_params_clamps_lambda_aggr_to_zero_five() {
        let _guard = AGGRESSION_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        set_aggression_params(0.0, -1.0);
        assert_eq!(get_aggression_params(), (0.0, 0.0), "lambda_aggr<0 muss auf 0.0 geklemmt werden");
        set_aggression_params(0.0, 42.0);
        assert_eq!(get_aggression_params(), (0.0, 5.0), "lambda_aggr>5 muss auf 5.0 geklemmt werden");
        set_aggression_params(0.0, 0.0);
    }

    #[test]
    fn set_aggression_params_non_finite_inputs_fall_back_to_zero() {
        let _guard = AGGRESSION_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        // NaN wuerde `f64::clamp` unveraendert durchlassen (siehe dessen
        // Doku) -- `set_aggression_params` muss das explizit abfangen, sonst
        // koennte ein kaputter GUI-Request die Suche mit NaN vergiften.
        set_aggression_params(f64::NAN, f64::INFINITY);
        assert_eq!(get_aggression_params(), (0.0, 0.0));
        set_aggression_params(f64::NEG_INFINITY, f64::NAN);
        assert_eq!(get_aggression_params(), (0.0, 0.0));
    }

    #[test]
    fn set_aggression_params_boundary_values_are_kept_unclamped() {
        let _guard = AGGRESSION_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        // Randwerte selbst (0.0/1.0 fuer w, 0.0/5.0 fuer lambda_aggr) sind
        // gueltig und duerfen NICHT durch die Klemme veraendert werden.
        set_aggression_params(1.0, 5.0);
        assert_eq!(get_aggression_params(), (1.0, 5.0));
        set_aggression_params(0.0, 0.0);
        assert_eq!(get_aggression_params(), (0.0, 0.0));
    }

    // ── Task #30: monotone Value-Skalen-Korrektur (`calibrate_win_prob_with`) ──

    /// Die gecachten Laufzeit-Getter muessen (in dieser Test-Umgebung, in der
    /// `MOSAIC_VALUE_CAL_A`/`MOSAIC_VALUE_CAL_B` nie gesetzt werden) auf ihre
    /// dokumentierten Defaults `0.0`/`1.0` zurueckfallen (Identitaet).
    #[test]
    fn value_cal_a_and_b_default_to_identity() {
        assert_eq!(value_cal_a(), 0.0);
        assert_eq!(value_cal_b(), 1.0);
    }

    /// (a,b)=(0,1) muss fuer JEDES `p` in `(0,1)` exakte Identitaet liefern
    /// (Early-Out, kein Logit-/Sigmoid-Roundtrip -- byte-identisch, nicht nur
    /// "numerisch nah dran").
    #[test]
    fn calibrate_win_prob_with_identity_at_default_params() {
        for p in [0.0001, 0.05, 0.3, 0.5, 0.5000001, 0.7, 0.9999] {
            assert_eq!(
                calibrate_win_prob_with(p, 0.0, 1.0),
                p,
                "p={p}: (a,b)=(0,1) muss EXAKTE Identitaet sein (Early-Out)"
            );
        }
    }

    /// Randfaelle `p=0.0`/`p=1.0` muessen ebenfalls exakt (nicht nur
    /// naeherungsweise) durchgereicht werden -- der Early-Out greift VOR dem
    /// Clamp, ein Clamp-dann-Sigmoid-Pfad wuerde hier `EPS`/`1-EPS` statt
    /// `0.0`/`1.0` liefern.
    #[test]
    fn calibrate_win_prob_with_identity_at_exact_boundaries() {
        assert_eq!(calibrate_win_prob_with(0.0, 0.0, 1.0), 0.0);
        assert_eq!(calibrate_win_prob_with(1.0, 0.0, 1.0), 1.0);
    }

    /// `B>1` muss die Kalibrierung um `p=0.5` "strecken" (schärfer machen):
    /// fuer `p>0.5` ist `p' > p` (Logit>0 wird verstaerkt).
    #[test]
    fn calibrate_win_prob_with_b_greater_than_one_stretches_above_half() {
        let p = 0.6;
        let p_stretched = calibrate_win_prob_with(p, 0.0, 2.0);
        assert!(p_stretched > p, "b=2.0 sollte p=0.6 anheben, war {p_stretched}");
    }

    /// Symmetrisches Gegenstueck unterhalb 0.5: `B>1` senkt `p<0.5` weiter ab.
    #[test]
    fn calibrate_win_prob_with_b_greater_than_one_stretches_below_half() {
        let p = 0.4;
        let p_stretched = calibrate_win_prob_with(p, 0.0, 2.0);
        assert!(p_stretched < p, "b=2.0 sollte p=0.4 senken, war {p_stretched}");
    }

    /// `B<1` (Stauchung Richtung 0.5) ist das Gegenteil: `p=0.6` -> naeher an
    /// 0.5 heran, nicht davon weg.
    #[test]
    fn calibrate_win_prob_with_b_less_than_one_shrinks_toward_half() {
        let p = 0.6;
        let p_shrunk = calibrate_win_prob_with(p, 0.0, 0.5);
        assert!(p_shrunk < p && p_shrunk > 0.5, "b=0.5 sollte p=0.6 Richtung 0.5 stauchen, war {p_shrunk}");
    }

    /// `A` verschiebt den Logit additiv -- bei `b=1.0` muss `A>0` JEDES `p`
    /// anheben (positiver Shift), unabhaengig vom Ausgangswert.
    #[test]
    fn calibrate_win_prob_with_positive_a_shifts_up() {
        for p in [0.1, 0.3, 0.5, 0.7, 0.9] {
            let shifted = calibrate_win_prob_with(p, 1.0, 1.0);
            assert!(shifted > p, "p={p}: a=1.0 sollte anheben, war {shifted}");
        }
    }

    /// Symmetrisches Gegenstueck: `A<0` senkt JEDES `p`.
    #[test]
    fn calibrate_win_prob_with_negative_a_shifts_down() {
        for p in [0.1, 0.3, 0.5, 0.7, 0.9] {
            let shifted = calibrate_win_prob_with(p, -1.0, 1.0);
            assert!(shifted < p, "p={p}: a=-1.0 sollte senken, war {shifted}");
        }
    }

    /// Kern-Eigenschaft (PREREG-Anspruch: "aendert die Ordnung per Definition
    /// NICHT"): fuer `b>0` ist `calibrate_win_prob_with` STRENG MONOTON in `p`
    /// -- Stichproben-Property-Test ueber zufaellig gezogene `(p1,p2,a,b)`-
    /// Quadrupel (deterministischer Seed, reproduzierbar).
    #[test]
    fn calibrate_win_prob_with_preserves_order_for_random_pairs_and_params() {
        let mut rng = StdRng::seed_from_u64(30001);
        let mut checked = 0;
        for _ in 0..500 {
            let p1: f64 = rng.random_range(1e-4..(1.0 - 1e-4));
            let p2: f64 = rng.random_range(1e-4..(1.0 - 1e-4));
            if (p1 - p2).abs() < 1e-9 {
                continue; // gleiche Werte sind kein Ordnungs-Test
            }
            let a: f64 = rng.random_range(-3.0..3.0);
            let b: f64 = rng.random_range(0.05..5.0); // b>0 -- Voraussetzung fuer Monotonie
            let c1 = calibrate_win_prob_with(p1, a, b);
            let c2 = calibrate_win_prob_with(p2, a, b);
            let same_order = (p1 < p2) == (c1 < c2);
            assert!(
                same_order,
                "Ordnung verletzt: p1={p1} p2={p2} a={a} b={b} -> c1={c1} c2={c2}"
            );
            checked += 1;
        }
        assert!(checked >= 400, "zu wenige gueltige Stichproben ({checked}) -- Testaufbau pruefen");
    }

    /// Env-Var-Parsing fuer die beiden neuen Namen -- reine `read_f64_env`-
    /// Weiterverwendung (die generische Parsing-Logik ist bereits oben
    /// getestet), hier nur der Vertrag "richtiger Default-Wert je Var".
    #[test]
    fn read_f64_env_value_cal_a_default_and_parsing() {
        let name = "MOSAIC_TEST_ENV_CAL_A_30A";
        std::env::remove_var(name);
        assert_eq!(read_f64_env(name, 0.0), 0.0);
        std::env::set_var(name, "0.75");
        assert_eq!(read_f64_env(name, 0.0), 0.75);
        std::env::remove_var(name);
    }

    #[test]
    fn read_f64_env_value_cal_b_default_and_parsing() {
        let name = "MOSAIC_TEST_ENV_CAL_B_30B";
        std::env::remove_var(name);
        assert_eq!(read_f64_env(name, 1.0), 1.0);
        std::env::set_var(name, "1.5");
        assert_eq!(read_f64_env(name, 1.0), 1.5);
        std::env::remove_var(name);
    }

    #[test]
    fn read_f64_env_value_cal_invalid_falls_back_to_documented_default() {
        let name_a = "MOSAIC_TEST_ENV_CAL_A_INVALID_30C";
        std::env::set_var(name_a, "nope");
        assert_eq!(read_f64_env(name_a, 0.0), 0.0);
        std::env::remove_var(name_a);

        let name_b = "MOSAIC_TEST_ENV_CAL_B_INVALID_30D";
        std::env::set_var(name_b, "nope");
        assert_eq!(read_f64_env(name_b, 1.0), 1.0);
        std::env::remove_var(name_b);
    }

    /// PREREG_implicit_minimax_backup.md par.1: gleiches Muster wie die
    /// `read_f64_env_value_cal_*`-Tests oben -- reiner `read_f64_env`-
    /// Vertragstest mit synthetischem Namen. HISTORISCHE ANMERKUNG: frueher
    /// stand hier ein Hinweis, dass die prozessweit gecachte OnceLock-
    /// Variante nicht mit wechselnden Werten im selben Testprozess pruefbar
    /// war -- genau DAS war Anlass 2 fuer die Migration nach `SearchConfig`
    /// (PREREG_agent_encapsulation.md par.1/par.4 Punkt 4). Der Kronzeuge
    /// dafuer ist jetzt
    /// `search_config_with_different_alpha_in_same_process_yields_different_selection`
    /// oben (zwei `SearchConfig`-Werte, ein Prozess, unterschiedliche
    /// Selektion). Die reinen Mischformeln selbst bleiben zusaetzlich ueber
    /// `mix_q_with_implicit_minimax`/`completed_q_per_candidate_mixed`
    /// getestet (etabliertes Trennungsmuster von `calibrate_win_prob_with`).
    #[test]
    fn read_f64_env_implicit_minimax_a_default_and_parsing() {
        let name = "MOSAIC_TEST_ENV_IMPLICIT_MINIMAX_A_1";
        std::env::remove_var(name);
        assert_eq!(read_f64_env(name, 0.0), 0.0);
        std::env::set_var(name, "0.2");
        assert_eq!(read_f64_env(name, 0.0), 0.2);
        std::env::remove_var(name);
    }

    // ── Task #30 x Task #28 Interaktion: Korrektur wirkt auf `wr`, NICHT auf
    // `pts`/`opp` ──

    /// Bei `w=0` (Task #28 Blend aus) muss `blended_leaf_win_prob_with` mit
    /// aktiver Kalibrierung (`a,b != 0,1`) exakt `calibrate_win_prob_with(
    /// value_to_win_prob(value), a, b)` liefern -- die Kalibrierung greift
    /// unabhaengig vom Task-#28-Blend-Status.
    #[test]
    fn blended_leaf_win_prob_with_applies_calibration_to_wr_when_w_is_zero() {
        let value = vec![0.3f32];
        let expected = calibrate_win_prob_with(value_to_win_prob(&value), 0.5, 2.0);
        let actual = blended_leaf_win_prob_with(&value, &[], &[], 0.0, 0.0, 0.5, 2.0);
        assert_eq!(actual, expected);
    }

    /// Voller `w>0`+opp-vorhanden-Blend MIT aktiver Kalibrierung: die
    /// Korrektur darf NUR in `wr` einfliessen, `pts`/`u_pts` (also
    /// `opp_aware_points_utility`, das `points`/`opp_points` konsumiert)
    /// bleiben unangetastet -- Nachweis per Handrechnung.
    #[test]
    fn blended_leaf_win_prob_with_calibration_affects_only_wr_not_points_or_opp() {
        let value = vec![0.0f32]; // value_to_win_prob -> 0.5
        let points = vec![0.4f32];
        let opp_points = vec![0.2f32];
        let a = 0.5;
        let b = 1.5;
        // Erwartung: wr_calibrated statt rohem wr=0.5, u_pts unveraendert
        // (0.66, siehe `opp_aware_points_utility_matches_hand_calculation`).
        let wr_calibrated = calibrate_win_prob_with(0.5, a, b);
        let u_pts = opp_aware_points_utility(0.4, 0.2, 0.5);
        let w = 0.5;
        let expected = (1.0 - w) * wr_calibrated + w * u_pts;
        let actual = blended_leaf_win_prob_with(&value, &points, &opp_points, w, 0.5, a, b);
        // Toleranz 1e-6 statt 1e-9 -- `value`/`points`/`opp_points` sind
        // `f32`-Vektoren (wie reale ONNX-Outputs), die Konvertierung nach
        // `f64` fuer die Blend-/Kalibrierungs-Arithmetik ist nicht bit-exakt
        // zur reinen `f64`-Handrechnung (gleiche Begruendung wie beim
        // bestehenden `blended_leaf_win_prob_with_full_blend_matches_hand_
        // calculation`-Test).
        assert!(
            (actual - expected).abs() < 1e-6,
            "actual={actual} expected={expected} (wr_calibrated={wr_calibrated}, u_pts={u_pts})"
        );
        // Gegenprobe: wenn die Korrektur faelschlich AUCH auf u_pts wirken
        // wuerde, kaeme ein anderer Wert heraus -- schliesst das explizit aus.
        let wrong_if_points_were_calibrated =
            (1.0 - w) * wr_calibrated + w * calibrate_win_prob_with(u_pts, a, b);
        assert!(
            (actual - wrong_if_points_were_calibrated).abs() > 1e-6,
            "u_pts darf NICHT kalibriert werden -- actual={actual} sollte von \
             wrong_if_points_were_calibrated={wrong_if_points_were_calibrated} abweichen"
        );
    }

    /// Reiner Formel-Nachweis, dass Default-Kalibrierung (0,1) den bereits
    /// bestehenden `w>0`-Hand-Rechnungs-Test (`blended_leaf_win_prob_with_
    /// full_blend_matches_hand_calculation`) unveraendert reproduziert --
    /// zusaetzliche Absicherung, dass die neuen Parameter am Ende der
    /// Signatur additiv sind (keine Verschiebung bestehender Positional-
    /// Argumente).
    #[test]
    fn blended_leaf_win_prob_with_default_calibration_matches_pre_task30_result() {
        let value = vec![0.0f32];
        let points = vec![0.4f32];
        let opp_points = vec![0.2f32];
        let u = blended_leaf_win_prob_with(&value, &points, &opp_points, 0.5, 0.5, 0.0, 1.0);
        // Schema 20: 0.575 statt 0.58 -- die Aenderung liegt im Epsilon, NICHT
        // in der Task-#30-Kalibrierung, die dieser Test absichert (A=0/B=1
        // bleibt die Identitaet).
        assert!((u - 0.575).abs() < 1e-6, "u={u}, erwartet 0.575 (Kalibrierung A=0/B=1 = Identitaet)");
    }

    // ── Backend-Entscheidungsgleichheits-Helfer (`evaluations/
    // PREREG_gpu_inference_path.md`): urspruenglich fuer die Weg-A-
    // Wirkungsmessung tract<->torch gebaut (Weg A ist 2026-08-15 entfernt,
    // gemessen verworfen -- PREREG §9); weiterverwendet von den Weg-B-
    // (`ort_cuda_*`) und Weg-V-Tests (`interleaved_*`) unten.

    /// Reproduziert `build_gumbel_tree_inner`s Score-/Sortier-Schritt (siehe
    /// dortige Zeilen ~3644-3676: `score(a) = g(a) + ln(prior(a))`, `g(a) ~
    /// Gumbel(0,1)`, absteigend sortiert, Top-`m_prime` behalten) OHNE den
    /// Rest der Baumsuche -- reicht fuer die reine "welche Aktionen landen
    /// in der Top-m-Menge"-Frage. `acts` MUSS bereits in der von
    /// `build_untried_actions` gelieferten Reihenfolge sein (nach Prior
    /// absteigend) -- die Ziehreihenfolge des Gumbel-Rauschens haengt
    /// GENAU DAVON ab (Treue zum Original, siehe Funktionskommentar dort).
    fn gumbel_topm_set<R: Rng + ?Sized>(acts: &[(Action, f32)], m_prime: usize, rng: &mut R) -> Vec<Action> {
        let mut scored: Vec<(f64, usize)> = acts
            .iter()
            .enumerate()
            .map(|(i, &(_, p))| {
                let g = sample_gumbel(rng);
                (g + (p as f64).max(1e-9).ln(), i)
            })
            .collect();
        scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));
        scored.into_iter().take(m_prime).map(|(_, i)| acts[i].0.clone()).collect()
    }

    /// Policy-Logits, maskiert auf die EINDEUTIGEN legalen Aktions-IDs (exakt
    /// dieselbe Maskierung wie `build_untried_actions`s `unique_ids`, siehe
    /// dortiger Kommentar) -- fuer die REINE, rauschfreie Argmax-Frage
    /// (Metrik 1). Gibt die (id, logit)-Paare absteigend nach Logit sortiert
    /// zurueck.
    fn legal_logits_sorted(state: &GameState, logits: &[f32]) -> Vec<(usize, f32)> {
        let base_actions = drafting_actions(state);
        let mut ids: Vec<usize> =
            base_actions.iter().map(|a| crate::self_play::action_to_id_direct(state, a)).collect();
        ids.sort_unstable();
        ids.dedup();
        let mut pairs: Vec<(usize, f32)> =
            ids.iter().map(|&id| (id, logits.get(id).copied().unwrap_or(f32::NEG_INFINITY))).collect();
        pairs.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        pairs
    }

    // ── Weg B (`evaluations/PREREG_gpu_inference_path.md` §11), Nutzer-Auftrag
    // "fang an" 2026-08-12, Schritt 2 -- ausdruecklich verlangt, weil leicht
    // uebersehen: die 0-von-1148 der (2026-08-15 entfernten) Weg-A-Messung
    // (tract<->torch) und die unten folgende (synchron<->verschraenkt, beide
    // tract) decken KEIN weiteres Backend ab. ORT-CUDA ist ein EIGENER
    // Inferenz-Mechanismus (eigener Graph-Optimierer, eigene CUDA-Kernels)
    // und braucht seinen EIGENEN Nachweis. Wiederverwendet dieselben Helfer
    // (`legal_logits_sorted`, `gumbel_topm_set`) wie oben.

    /// Entscheidungsgleichheit tract<->ORT-CUDA: Argmax + Gumbel-Top-m auf
    /// denselben 1148 Zustaenden wie die fruehere Weg-A-Wirkungsmessung,
    /// dasselbe Modell `alphazero_v20_2d_opp_brierbest.onnx`, ZUSAETZLICH
    /// die maximale Rohwert-Abweichung je Kopf.
    ///
    /// KEIN Urteil hier -- nur Zahlen. Weicht die Entscheidung ab: BERICHTEN,
    /// NICHT die Toleranz anpassen (Auftragstext) -- bei ORT ist eine
    /// Abweichung plausibler als bei torch (anderer Graph-Optimierer als
    /// tract UND als PyTorch), also keine Erwartung von exakt 0 vorwegnehmen,
    /// nur ehrlich zaehlen.
    ///
    /// `#[cfg(feature = "ort_cuda_probe")]` + `#[ignore]`: braucht die
    /// optionale `ort`-Abhaengigkeit UND die ORT-CUDA-Provider-/Torch-CUDA-12-
    /// Laufzeit-DLLs neben dem Testbinary (Handkopie, siehe
    /// `evaluations/PREREG_gpu_inference_path.md` §11) -- kein regulaerer
    /// `cargo test`-Lauf erfuellt das automatisch, deshalb zusaetzlich
    /// `#[ignore]` obwohl das Feature schon gate-haelt (das Feature gate haelt
    /// nur das KOMPILIEREN ab, nicht die Laufzeit-DLL-Verfuegbarkeit).
    /// Aufruf: `cargo test --release --lib --features ort_cuda_probe -- --ignored net_mcts::tests::ort_cuda_matches_tract_gumbel_root_selection --nocapture`
    #[cfg(feature = "ort_cuda_probe")]
    #[test]
    #[ignore]
    fn ort_cuda_matches_tract_gumbel_root_selection() {
        use crate::net::Net;

        let states_path = std::env::var("MOSAIC_FROZEN_STATES_JSON").unwrap_or_else(|_| panic!(
            "MOSAIC_FROZEN_STATES_JSON nicht gesetzt -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ));
        let raw = std::fs::read_to_string(&states_path).unwrap_or_else(|e| panic!(
            "{states_path} nicht lesbar ({e}) -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ));
        let records: Vec<Value> = serde_json::from_str(&raw).expect("JSON-Array erwartet");
        assert!(!records.is_empty(), "leere Zustandsliste -- Export fehlgeschlagen?");

        let repo = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("..");
        let onnx_path = repo.join("models/alphazero_v20_2d_opp_brierbest.onnx");
        assert!(
            onnx_path.exists(),
            "{onnx_path:?} fehlt -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        );
        let net = Net::load_auto(onnx_path.to_str().unwrap()).unwrap_or_else(|e| panic!(
            "{onnx_path:?} nicht ladbar ({e}) -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ));

        let m_for_400_sims = gumbel_top_m_for_budget(400);
        println!("gumbel_top_m_for_budget(400) = {m_for_400_sims}");

        let mut n_total = 0usize;
        let mut n_argmax_mismatch = 0usize;
        let mut n_topm_mismatch = 0usize;
        let mut argmax_mismatch_gaps: Vec<(usize, f32, f32)> = Vec::new();
        let mut max_abs = [0f32; 4]; // policy, value, moon, points -- gleiche Reihenfolge wie net.rs::eval_batch

        let chunk_size = crate::net::EVAL_BATCH_MAX_N;
        for chunk in records.chunks(chunk_size) {
            let mut states: Vec<GameState> = Vec::with_capacity(chunk.len());
            let mut record_indices: Vec<usize> = Vec::with_capacity(chunk.len());
            for entry in chunk {
                let record_index = entry["record_index"].as_u64().unwrap() as usize;
                let mut rng = StdRng::seed_from_u64(record_index as u64);
                match crate::serialize::json_to_state(&entry["state"], &mut rng) {
                    Ok(s) => {
                        states.push(s);
                        record_indices.push(record_index);
                    }
                    Err(e) => eprintln!("  ⚠️  record #{record_index}: json_to_state fehlgeschlagen ({e}) -- ausgelassen."),
                }
            }
            if states.is_empty() {
                continue;
            }
            let feats: Vec<Vec<f32>> = states.iter().map(|s| crate::features::features_for_net(&net, s)).collect();
            let refs: Vec<&[f32]> = feats.iter().map(|v| v.as_slice()).collect();

            let tract_out = net.eval_batch(&refs).expect("tract eval_batch");
            let ort_out = crate::net_ort::eval_batch_via_ort_cuda(&net, &refs)
                .expect("ORT-CUDA-Rundlauf (CUDA-Session muss aufbaubar sein -- siehe PREREG §11 fuer die DLL-Handkopie)");
            assert_eq!(tract_out.len(), states.len());
            assert_eq!(ort_out.len(), states.len());

            for i in 0..states.len() {
                let state = &states[i];
                let record_index = record_indices[i];
                let (policy_t, value_t, moon_t, points_t) = &tract_out[i];
                let (policy_o, value_o, moon_o, points_o) = &ort_out[i];

                // ── Max. Rohwert-Abweichung je Kopf ──
                for (idx, (a, b)) in [(policy_t, policy_o), (value_t, value_o), (moon_t, moon_o), (points_t, points_o)]
                    .iter()
                    .enumerate()
                {
                    for (x, y) in a.iter().zip(b.iter()) {
                        let d = (x - y).abs();
                        if d > max_abs[idx] {
                            max_abs[idx] = d;
                        }
                    }
                }

                // ── Metrik 1: Argmax (rauschfrei) ──
                let sorted_t = legal_logits_sorted(state, policy_t);
                let sorted_o = legal_logits_sorted(state, policy_o);
                assert_eq!(sorted_t.len(), sorted_o.len(), "record #{record_index}: unterschiedliche Legal-ID-Menge?!");
                assert!(!sorted_t.is_empty(), "record #{record_index}: keine legalen Aktionen an einer Drafting-Wurzel?!");
                n_total += 1;
                if sorted_t[0].0 != sorted_o[0].0 {
                    n_argmax_mismatch += 1;
                    let gap_t = if sorted_t.len() > 1 { sorted_t[0].1 - sorted_t[1].1 } else { f32::INFINITY };
                    let gap_o = if sorted_o.len() > 1 { sorted_o[0].1 - sorted_o[1].1 } else { f32::INFINITY };
                    argmax_mismatch_gaps.push((record_index, gap_t, gap_o));
                }

                // ── Metrik 2: Gumbel-Top-m-Menge ──
                let mut moon_arr_t = [0f32; 5];
                for (j, s) in moon_t.iter().take(5).enumerate() {
                    moon_arr_t[j] = *s;
                }
                let mut moon_arr_o = [0f32; 5];
                for (j, s) in moon_o.iter().take(5).enumerate() {
                    moon_arr_o[j] = *s;
                }
                let (acts_t, _) = build_untried_actions(state, policy_t, &moon_arr_t, true);
                let (acts_o, _) = build_untried_actions(state, policy_o, &moon_arr_o, true);
                assert_eq!(
                    acts_t.len(),
                    acts_o.len(),
                    "record #{record_index}: unterschiedliche Kandidatenzahl nach Moon-Expansion?!"
                );
                let n_root = acts_t.len();
                let m_prime = m_for_400_sims.min(n_root);

                let seed = 900_000_000u64 + record_index as u64;
                let mut rng_t = StdRng::seed_from_u64(seed);
                let mut rng_o = StdRng::seed_from_u64(seed);
                let set_t = gumbel_topm_set(&acts_t, m_prime, &mut rng_t);
                let set_o = gumbel_topm_set(&acts_o, m_prime, &mut rng_o);
                let sets_match = set_t.len() == set_o.len() && set_t.iter().all(|a| set_o.contains(a));
                if !sets_match {
                    n_topm_mismatch += 1;
                }
            }
        }

        let argmax_rate = n_argmax_mismatch as f64 / n_total as f64;
        let topm_rate = n_topm_mismatch as f64 / n_total as f64;
        println!("\n=== Entscheidungsgleichheit tract<->ORT-CUDA (Weg B) ===");
        println!("Stellungen verarbeitet: {n_total}");
        println!("Argmax-Abweichung:      {n_argmax_mismatch}/{n_total} ({:.4}%)", argmax_rate * 100.0);
        println!("Top-{m_for_400_sims}-Mengen-Abweichung: {n_topm_mismatch}/{n_total} ({:.4}%)", topm_rate * 100.0);
        if argmax_mismatch_gaps.is_empty() {
            println!("Keine Argmax-Abweichungen -- keine Logit-Abstaende zu berichten.");
        } else {
            println!("Logit-Abstaende (Platz1-Platz2) in den Argmax-Abweichungsfaellen (tract | ORT-CUDA):");
            for (idx, gap_t, gap_o) in &argmax_mismatch_gaps {
                println!("  record #{idx}: tract={gap_t:.6}  ort_cuda={gap_o:.6}");
            }
        }
        println!("\nMax. Rohwert-Abweichung je Kopf (tract vs. ORT-CUDA):");
        for (name, m) in ["policy", "value", "moon", "points"].iter().zip(max_abs.iter()) {
            println!("  {name}: {m:.8}");
        }
    }

    /// Wie [`gumbel_topm_set`], aber gibt die VOLLSTAENDIGE (nicht auf
    /// `m_prime` gekuerzte) nach Score absteigend sortierte Liste zurueck --
    /// gleiche RNG-Verbrauchsreihenfolge (dieselbe `.enumerate()`-Iteration
    /// ueber `acts`), also fuer denselben Seed bit-identisch zu den ersten
    /// `m_prime` Eintraegen, die `gumbel_topm_set` liefern wuerde. Gebraucht
    /// fuer die Rang-/Abstands-Diagnose unten (PREREG §14, Nutzer-Auftrag
    /// 2026-08-12): `gumbel_topm_set` selbst gibt nur die MENGE zurueck, keine
    /// Raenge/Scores.
    /// PREREG §15 (Nutzer-Auftrag 2026-08-12, Zuordnungs-Hypothese): Rueckgabe
    /// jetzt `(score, g, idx)` statt `(score, idx)` -- EXAKT dasselbe Tupel-
    /// Layout wie das echte Produktions-`scored` in
    /// `build_gumbel_tree_inner` (net_mcts.rs:3719 `Vec<(f64, f64, usize)>`),
    /// damit sich `g` (der rohe Gumbel-Zug) UND `ln(prior)` (aus `score - g`
    /// rekonstruierbar) je Kandidat einzeln berichten lassen -- fuer die
    /// Frage "bekommen zwei tauschende Kandidaten unterschiedliche
    /// Zufallszahlen" reicht die reine Score-Summe nicht.
    // Diagnose-Helfer der Rangfolge-Messkette (PREREG_gpu_inference_path §15/§16);
    // nur von #[ignore]-/Feature-Tests gerufen, im Normallauf bewusst ungenutzt.
    #[allow(dead_code)]
    fn gumbel_scored_sorted<R: Rng + ?Sized>(acts: &[(Action, f32)], rng: &mut R) -> Vec<(f64, f64, usize)> {
        let mut scored: Vec<(f64, f64, usize)> = acts
            .iter()
            .enumerate()
            .map(|(i, &(_, p))| {
                let g = sample_gumbel(rng);
                (g + (p as f64).max(1e-9).ln(), g, i)
            })
            .collect();
        scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));
        scored
    }

    /// PREREG §14 (Nutzer-Auftrag 2026-08-12): NUR der eine abweichende
    /// Zustand aus §13 (1/1148 bei ausgeschaltetem TF32) -- welcher, an
    /// welcher Rangstelle die Mengen auseinandergehen, der Score-Abstand am
    /// Schnitt in BEIDEN Backends, und zum Vergleich dieselbe Abstandsgroesse
    /// ueber die 1147 NICHT abweichenden Zustaende (Median, 10%-Quantil).
    /// KEINE Deutung hier -- nur die vier angeforderten Zahlen, `println!`.
    ///
    /// `#[cfg(feature = "ort_cuda_probe")]` + `#[ignore]`: gleiche
    /// Voraussetzungen wie `ort_cuda_matches_tract_gumbel_root_selection`
    /// (`ort`-Feature, ORT-CUDA-Provider-/Torch-CUDA-12-DLLs neben dem
    /// Testbinary, `MOSAIC_FROZEN_STATES_JSON`).
    /// Aufruf: `cargo test --release --lib --features ort_cuda_probe -- --ignored net_mcts::tests::ort_cuda_single_deviation_gap_diagnostic --nocapture`
    #[cfg(feature = "ort_cuda_probe")]
    #[test]
    #[ignore]
    fn ort_cuda_single_deviation_gap_diagnostic() {
        use crate::net::Net;

        let states_path = std::env::var("MOSAIC_FROZEN_STATES_JSON").unwrap_or_else(|_| panic!(
            "MOSAIC_FROZEN_STATES_JSON nicht gesetzt -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ));
        let raw = std::fs::read_to_string(&states_path).unwrap_or_else(|e| panic!(
            "{states_path} nicht lesbar ({e}) -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ));
        let records: Vec<Value> = serde_json::from_str(&raw).expect("JSON-Array erwartet");
        assert!(!records.is_empty());

        let repo = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("..");
        let onnx_path = repo.join("models/alphazero_v20_2d_opp_brierbest.onnx");
        assert!(
            onnx_path.exists(),
            "{onnx_path:?} fehlt -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        );
        let net = Net::load_auto(onnx_path.to_str().unwrap()).unwrap_or_else(|e| panic!(
            "{onnx_path:?} nicht ladbar ({e}) -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ));

        let m_for_400_sims = gumbel_top_m_for_budget(400);

        // Je Zustand mit echtem Schnitt (0 < m_prime < n_root): der
        // Rang-m_prime/m_prime+1-Score-Abstand in TRACTS eigener Rangfolge
        // (Referenzgroesse fuer die Populationsverteilung, Punkt 4) UND ob
        // die Top-m_prime-MENGE zwischen den Backends abweicht.
        struct Rec {
            record_index: usize,
            round: u32,
            n_root: usize,
            m_prime: usize,
            gap_tract: f64,
            gap_ort: f64,
            deviates: bool,
        }
        let mut recs: Vec<Rec> = Vec::new();
        let mut n_no_real_cutoff = 0usize;

        let chunk_size = crate::net::EVAL_BATCH_MAX_N;
        for chunk in records.chunks(chunk_size) {
            let mut states: Vec<GameState> = Vec::with_capacity(chunk.len());
            let mut record_indices: Vec<usize> = Vec::with_capacity(chunk.len());
            for entry in chunk {
                let record_index = entry["record_index"].as_u64().unwrap() as usize;
                let mut rng = StdRng::seed_from_u64(record_index as u64);
                match crate::serialize::json_to_state(&entry["state"], &mut rng) {
                    Ok(s) => {
                        states.push(s);
                        record_indices.push(record_index);
                    }
                    Err(e) => eprintln!("  ⚠️  record #{record_index}: json_to_state fehlgeschlagen ({e}) -- ausgelassen."),
                }
            }
            if states.is_empty() {
                continue;
            }
            let feats: Vec<Vec<f32>> = states.iter().map(|s| crate::features::features_for_net(&net, s)).collect();
            let refs: Vec<&[f32]> = feats.iter().map(|v| v.as_slice()).collect();

            let tract_out = net.eval_batch(&refs).expect("tract eval_batch");
            let ort_out = crate::net_ort::eval_batch_via_ort_cuda(&net, &refs)
                .expect("ORT-CUDA-Rundlauf (CUDA-Session muss aufbaubar sein)");

            for i in 0..states.len() {
                let state = &states[i];
                let record_index = record_indices[i];
                let (policy_t, _v_t, moon_t, _pt_t) = &tract_out[i];
                let (policy_o, _v_o, moon_o, _pt_o) = &ort_out[i];

                let mut moon_arr_t = [0f32; 5];
                for (j, s) in moon_t.iter().take(5).enumerate() {
                    moon_arr_t[j] = *s;
                }
                let mut moon_arr_o = [0f32; 5];
                for (j, s) in moon_o.iter().take(5).enumerate() {
                    moon_arr_o[j] = *s;
                }
                let (acts_t, _) = build_untried_actions(state, policy_t, &moon_arr_t, true);
                let (acts_o, _) = build_untried_actions(state, policy_o, &moon_arr_o, true);
                assert_eq!(acts_t.len(), acts_o.len(), "record #{record_index}: unterschiedliche Kandidatenzahl nach Moon-Expansion?!");
                let n_root = acts_t.len();
                let m_prime = m_for_400_sims.min(n_root);
                if m_prime == 0 || m_prime >= n_root {
                    // Kein echter Schnitt moeglich (alle Kandidaten passen
                    // sowieso hinein) -- keine "16./17. Stelle" zu berichten,
                    // ausgelassen fuer die Abstandsmessung.
                    n_no_real_cutoff += 1;
                    continue;
                }

                let seed = 900_000_000u64 + record_index as u64;
                let mut rng_t = StdRng::seed_from_u64(seed);
                let mut rng_o = StdRng::seed_from_u64(seed);
                let sorted_t = gumbel_scored_sorted(&acts_t, &mut rng_t);
                let sorted_o = gumbel_scored_sorted(&acts_o, &mut rng_o);

                let top_t: Vec<Action> = sorted_t[..m_prime].iter().map(|&(_, _, idx)| acts_t[idx].0.clone()).collect();
                let top_o: Vec<Action> = sorted_o[..m_prime].iter().map(|&(_, _, idx)| acts_o[idx].0.clone()).collect();
                let deviates = !(top_t.len() == top_o.len() && top_t.iter().all(|a| top_o.contains(a)));

                let gap_tract = sorted_t[m_prime - 1].0 - sorted_t[m_prime].0;
                let gap_ort = sorted_o[m_prime - 1].0 - sorted_o[m_prime].0;

                if deviates {
                    // ── Punkt 1+2: welcher Zustand, an welcher Rangstelle ──
                    let extra_t: Vec<&Action> = top_t.iter().filter(|a| !top_o.contains(a)).collect();
                    let extra_o: Vec<&Action> = top_o.iter().filter(|a| !top_t.contains(a)).collect();
                    println!("\n=== EINZIGER ABWEICHENDER ZUSTAND ===");
                    println!("record_index: {record_index}");
                    println!("Runde: {}", state.round_number);
                    println!("Kandidaten nach Moon-Expansion (n_root): {n_root}");
                    println!("m_prime (Schnitt bei 400 Sims): {m_prime}");
                    // PREREG §15 (Zuordnungs-Hypothese, Nutzer-Auftrag
                    // 2026-08-12): fuer JEDE tauschende Aktion zusaetzlich (a)
                    // ihre POSITION in `acts_t`/`acts_o` (= der `.enumerate()`-
                    // Index, an dem `net_mcts.rs:3722-3726` den Gumbel-Zug
                    // zieht) und (b) den ROHEN gezogenen Gumbel-Wert `g` (nicht
                    // nur die Score-Summe) -- direkte Antwort auf "gleiche
                    // Aufzaehlungsreihenfolge? gleiche Zufallszahl?".
                    let pos_in = |acts: &[(Action, f32)], target: &Action| -> Option<usize> {
                        acts.iter().position(|(a, _)| a == target)
                    };
                    let rank_score_g = |sorted: &[(f64, f64, usize)], acts: &[(Action, f32)], target: &Action| -> Option<(usize, f64, f64)> {
                        sorted
                            .iter()
                            .position(|&(_, _, idx)| &acts[idx].0 == target)
                            .map(|p| (p + 1, sorted[p].0, sorted[p].1))
                    };
                    println!("Nur in tracts Top-{m_prime} (faellt bei ORT heraus):");
                    for a in &extra_t {
                        let idx_t = pos_in(&acts_t, a);
                        let idx_o = pos_in(&acts_o, a);
                        let (rank_t, score_t, g_t) = rank_score_g(&sorted_t, &acts_t, a).unwrap();
                        let (rank_o, score_o, g_o) = rank_score_g(&sorted_o, &acts_o, a).unwrap();
                        println!("  {a:?}");
                        println!("    Position in acts_t (0-idx): {idx_t:?}   Position in acts_o (0-idx): {idx_o:?}");
                        println!("    tract:    Rang={rank_t} Score={score_t:.6} g={g_t:.6} ln(prior)={:.6}", score_t - g_t);
                        println!("    ORT-CUDA: Rang={rank_o} Score={score_o:.6} g={g_o:.6} ln(prior)={:.6}", score_o - g_o);
                    }
                    println!("Nur in ORT-CUDAs Top-{m_prime} (kommt neu herein):");
                    for a in &extra_o {
                        let idx_t = pos_in(&acts_t, a);
                        let idx_o = pos_in(&acts_o, a);
                        let (rank_t, score_t, g_t) = rank_score_g(&sorted_t, &acts_t, a).unwrap();
                        let (rank_o, score_o, g_o) = rank_score_g(&sorted_o, &acts_o, a).unwrap();
                        println!("  {a:?}");
                        println!("    Position in acts_t (0-idx): {idx_t:?}   Position in acts_o (0-idx): {idx_o:?}");
                        println!("    tract:    Rang={rank_t} Score={score_t:.6} g={g_t:.6} ln(prior)={:.6}", score_t - g_t);
                        println!("    ORT-CUDA: Rang={rank_o} Score={score_o:.6} g={g_o:.6} ln(prior)={:.6}", score_o - g_o);
                    }
                    // ── Punkt 3 (urspruenglicher Auftrag): die gumbel-
                    // perturbierten SCORES der beiden konkurrierenden
                    // Kandidaten an der Schnittstelle (Rang m_prime und
                    // m_prime+1), in BEIDEN Backends, plus deren Abstand. ──
                    println!(
                        "tract:    Rang{m_prime}-Score={:.6}  Rang{}-Score={:.6}  Abstand={:.6}",
                        sorted_t[m_prime - 1].0,
                        m_prime + 1,
                        sorted_t[m_prime].0,
                        gap_tract
                    );
                    println!(
                        "ORT-CUDA: Rang{m_prime}-Score={:.6}  Rang{}-Score={:.6}  Abstand={:.6}",
                        sorted_o[m_prime - 1].0,
                        m_prime + 1,
                        sorted_o[m_prime].0,
                        gap_ort
                    );
                }

                recs.push(Rec { record_index, round: state.round_number, n_root, m_prime, gap_tract, gap_ort, deviates });
            }
        }

        let n_total = recs.len();
        let n_deviating = recs.iter().filter(|r| r.deviates).count();
        println!("\n=== ZUSAMMENFASSUNG ===");
        println!("Zustaende mit echtem Schnitt (0 < m_prime < n_root): {n_total} (ausgelassen ohne echten Schnitt: {n_no_real_cutoff})");
        println!("davon abweichend: {n_deviating}");

        // ── Punkt 4: Verteilung des Rang-m_prime/m_prime+1-Abstands ueber
        // die NICHT abweichenden Zustaende (tracts eigene Rangfolge als
        // durchgehende Referenzgroesse) -- Median und 10%-Quantil. ──
        let mut gaps_non_deviating: Vec<f64> = recs.iter().filter(|r| !r.deviates).map(|r| r.gap_tract).collect();
        gaps_non_deviating.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let quantile = |sorted: &[f64], q: f64| -> f64 {
            if sorted.is_empty() {
                return f64::NAN;
            }
            let pos = q * (sorted.len() - 1) as f64;
            let lo = pos.floor() as usize;
            let hi = pos.ceil() as usize;
            if lo == hi {
                sorted[lo]
            } else {
                sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo as f64)
            }
        };
        let median_non_dev = quantile(&gaps_non_deviating, 0.5);
        let p10_non_dev = quantile(&gaps_non_deviating, 0.1);
        println!(
            "Rang-Schnitt-Abstand (tract) ueber {} NICHT abweichende Zustaende: Median={:.6}  10%-Quantil={:.6}",
            gaps_non_deviating.len(),
            median_non_dev,
            p10_non_dev
        );

        for r in recs.iter().filter(|r| r.deviates) {
            println!(
                "\nAbweichender Zustand record#{}: Runde={} n_root={} m_prime={} gap_tract={:.6} gap_ort={:.6}",
                r.record_index, r.round, r.n_root, r.m_prime, r.gap_tract, r.gap_ort
            );
        }
    }

    /// PREREG §16 (Nutzer-Auftrag 2026-08-12): Verteilungsvergleich statt
    /// Punktvergleich, MIT SELBSTKONTROLLE. §15 zeigte: Punktgleichheit ist
    /// fuer keinen Backend-Wechsel erreichbar (die Gumbel-Zuordnung haengt an
    /// der prior-abhaengigen Aufzaehlungsreihenfolge, eine Stoerung ab ~1e-6
    /// kann benachbarte Kandidaten tauschen). Gumbel-Top-m ist aber ohnehin
    /// eine STOCHASTISCHE Auswahl -- die Frage ist, ob ein Backend-Wechsel
    /// wie ein Seed-Wechsel wirkt (Menge aus derselben Verteilung) oder wie
    /// etwas anderes.
    ///
    /// ## Stichprobe (Auswahl OHNE Rosinen) -- GEAENDERT nach Pilotlauf
    ///
    /// Nur Zustaende mit einem ECHTEN Schnitt (`m_prime < n_root`, wie in §14
    /// definiert) tragen ueberhaupt stochastische Information (bei
    /// `m_prime >= n_root` ist die Top-m-Menge IMMER die volle
    /// Kandidatenmenge, unabhaengig vom Seed) -- ein STRUKTURELLER, nicht
    /// ergebnisabhaengiger Filter (455 von 1148 in dieser Sitzung GEPRUEFT).
    ///
    /// URSPRUENGLICHER Plan: eine Zufallsstichprobe von `N_STATES=60` aus
    /// diesen 455 (fester Seed `SAMPLE_SEED`, `rand::seq::index::sample` ohne
    /// Zuruecklegen) -- am unteren Rand des im Auftrag genannten Rahmens
    /// (50-100). Ein Pilotlauf damit ergab bei ALLEN DREI Vergleichen EXAKT
    /// dieselbe Zahl (0,2100 max / 0,0117 Mittel, `n=7571`) -- kein
    /// Messfehler: bei einer Basisrate von 1/455 (~0,22%, §14) liegt der
    /// Erwartungswert an Treffern bei `N=60` bei nur ~0,13, die Stichprobe
    /// verfehlt das seltene Vertauschungs-Ereignis mit sehr hoher
    /// Wahrscheinlichkeit komplett -- und dann sind alle Kandidatenlisten-
    /// Reihenfolgen ueber alle Arme hinweg identisch (§15), Vergleich 1/2
    /// werden numerisch zur Selbstkontrolle.
    ///
    /// DESHALB (eigene Entscheidung, nicht vorgegeben): die VOLLE Menge der
    /// 455 Real-Schnitt-Zustaende verwendet, KEINE Stichprobe mehr --
    /// deterministisch, keine Stichproben-Glücksfrage, und mit `K=200`/
    /// Zustand immer noch schnell (Pilotlauf bei `N=60`: 3,7s).
    ///
    /// ## K und die Seed-Aufteilung
    ///
    /// `K=200` (wie im Auftrag vorgeschlagen), aber ALLE DREI Vergleiche
    /// nutzen dieselbe Aufloesung: `K/2=100` DISJUNKTE Seeds je Seite (Seeds
    /// 0..99 vs. 100..199 je Zustand) -- nicht `K` gegen `K`. Begruendung:
    /// die Selbstkontrolle (Vergleich 3) braucht zwei disjunkte Stichproben
    /// AUS DERSELBEN Verteilung, um die reine Stichproben-Rauschgrenze BEI
    /// GEGEBENER Seitengroesse zu bestimmen -- fuer einen fairen Vergleich
    /// ("dieselbe Aufloesung", Auftragstext) muessen die Vergleiche 1/2
    /// GENAU DIESELBE Seitengroesse (100) und denselben Aufbau (disjunkte
    /// Seed-Haelften) verwenden, sonst waere die Rauschgrenze fuer eine
    /// andere Aufloesung gemessen als die Vergleiche selbst. Seite A ist in
    /// ALLEN DREI Vergleichen dieselbe Berechnung (tract/synchron, Seeds
    /// 0..99) -- Seite B unterscheidet sich: ORT-CUDA (Vgl. 1), verschraenkt
    /// (Vgl. 2), tract/synchron erneut mit den ANDEREN 100 Seeds (Vgl. 3,
    /// Selbstkontrolle).
    ///
    /// ## Die drei Vergleiche (je Zustand, je Kandidat: Haeufigkeit ueber die
    /// jeweilige 100er-Seed-Haelfte, dann `|Differenz|`, ueber ALLE
    /// Zustand-Kandidat-Paare der Stichprobe zu Max/Mittel aggregiert)
    ///
    /// 1. tract (Seeds 0..99) gegen ORT-CUDA (Seeds 100..199).
    /// 2. synchron/tract (Seeds 0..99) gegen verschraenkt/tract via
    ///    `net_batcher.rs` (Seeds 100..199).
    /// 3. SELBSTKONTROLLE: tract (Seeds 0..99) gegen tract (Seeds 100..199)
    ///    -- DIESELBE Policy-Ausgabe, nur disjunkte Seeds. Reine
    ///    Stichproben-Rauschgrenze, ohne jede Backend-/Pfad-Differenz.
    ///
    /// KEINE Deutung hier, ob innerhalb/ausserhalb der Selbstkontrolle
    /// akzeptabel ist -- nur die drei Masse und die Grenze selbst, `println!`.
    ///
    /// `#[cfg(feature = "ort_cuda_probe")]` + `#[ignore]`: gleiche
    /// Voraussetzungen wie die anderen ORT-CUDA-Tests (Feature, DLLs neben
    /// dem Testbinary, `MOSAIC_FROZEN_STATES_JSON`).
    /// Aufruf: `cargo test --release --lib --features ort_cuda_probe -- --ignored net_mcts::tests::ort_cuda_topm_distribution_vs_selfcontrol --nocapture`
    #[cfg(feature = "ort_cuda_probe")]
    #[test]
    #[ignore]
    fn ort_cuda_topm_distribution_vs_selfcontrol() {
        use crate::net::Net;
        use std::collections::VecDeque;
        use std::sync::{Arc, Mutex};

        let states_path = std::env::var("MOSAIC_FROZEN_STATES_JSON").unwrap_or_else(|_| panic!(
            "MOSAIC_FROZEN_STATES_JSON nicht gesetzt -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ));
        let raw = std::fs::read_to_string(&states_path).unwrap_or_else(|e| panic!(
            "{states_path} nicht lesbar ({e}) -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ));
        let records: Vec<Value> = serde_json::from_str(&raw).expect("JSON-Array erwartet");
        assert!(!records.is_empty());

        let repo = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("..");
        let onnx_path = repo.join("models/alphazero_v20_2d_opp_brierbest.onnx");
        assert!(
            onnx_path.exists(),
            "{onnx_path:?} fehlt -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        );
        let net = Arc::new(Net::load_auto(onnx_path.to_str().unwrap()).unwrap_or_else(|e| panic!(
            "{onnx_path:?} nicht ladbar ({e}) -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        )));

        // EIGENE ENTSCHEIDUNG, NACHTRAEGLICH GEAENDERT (siehe Bericht): ein
        // Pilotlauf mit `N_STATES=60` (Zufallsstichprobe, Seed `SAMPLE_SEED`)
        // ergab bei allen drei Vergleichen EXAKT dieselbe Zahl (0,2100 max /
        // 0,0117 Mittel) -- kein Messfehler, sondern die erwartete Folge der
        // in §14 gemessenen Basisrate: NUR 1 von 455 Zustaenden zeigt je
        // ueberhaupt eine Rang-Vertauschung (~0,22%), der Erwartungswert bei
        // N=60 liegt bei ~0,13 Treffern -- eine Stichprobe verfehlt das
        // seltene Ereignis mit sehr hoher Wahrscheinlichkeit komplett, und
        // dann sind Vergleich 1/2 numerisch nichts anderes als die
        // Selbstkontrolle (dieselben Aktionslisten-Reihenfolgen in allen
        // Armen, siehe §15). Deshalb HIER die VOLLE Menge der 455
        // Real-Schnitt-Zustaende verwendet, NICHT eine Stichprobe daraus --
        // deterministisch, keine Stichproben-Glücksfrage mehr, und mit
        // K=200/Zustand immer noch schnell (Pilotlauf: 3,7s bei N=60, siehe
        // Bericht). `N_STATES=60` bleibt unten als Konstante zur
        // Nachvollziehbarkeit des Pilotlaufs stehen, wird aber NICHT mehr
        // fuer die Stichprobenziehung verwendet (`eligible.len()` bestimmt
        // jetzt die tatsaechliche Menge).
        #[allow(dead_code)]
        const N_STATES_PILOT: usize = 60; // Pilotlauf-Dokumentation, siehe Kommentar oben.
        const K_HALF: usize = 100; // 100 gegen 100 = K=200 gesamt, siehe Funktionskommentar.

        let m_for_400_sims = gumbel_top_m_for_budget(400);

        // ── Schritt 1: tract-Screening ueber ALLE Zustaende -- n_root/m_prime
        // sind backend-unabhaengig (haengen nur am Zustand, siehe §14/§15),
        // ein Backend reicht zur Bestimmung, welche Zustaende einen echten
        // Schnitt haben. ──
        let mut all_states: Vec<GameState> = Vec::with_capacity(records.len());
        let mut all_record_indices: Vec<usize> = Vec::with_capacity(records.len());
        for entry in &records {
            let record_index = entry["record_index"].as_u64().unwrap() as usize;
            let mut rng = StdRng::seed_from_u64(record_index as u64);
            match crate::serialize::json_to_state(&entry["state"], &mut rng) {
                Ok(s) => {
                    all_states.push(s);
                    all_record_indices.push(record_index);
                }
                Err(e) => eprintln!("  ⚠️  record #{record_index}: json_to_state fehlgeschlagen ({e}) -- ausgelassen."),
            }
        }
        let all_feats: Vec<Vec<f32>> =
            all_states.iter().map(|s| crate::features::features_for_net(&net, s)).collect();

        let mut eligible: Vec<usize> = Vec::new();
        let chunk_size = crate::net::EVAL_BATCH_MAX_N;
        let mut offset = 0usize;
        for chunk in all_feats.chunks(chunk_size) {
            let refs: Vec<&[f32]> = chunk.iter().map(|v| v.as_slice()).collect();
            let out = net.eval_batch(&refs).expect("tract-Screening eval_batch");
            for (j, (policy, _v, moon, _pt)) in out.iter().enumerate() {
                let i = offset + j;
                let state = &all_states[i];
                let mut moon_arr = [0f32; 5];
                for (k, s) in moon.iter().take(5).enumerate() {
                    moon_arr[k] = *s;
                }
                let (acts, _) = build_untried_actions(state, policy, &moon_arr, true);
                let n_root = acts.len();
                let m_prime = m_for_400_sims.min(n_root);
                if m_prime < n_root {
                    eligible.push(i);
                }
            }
            offset += chunk.len();
        }
        println!("Zustaende mit echtem Schnitt (Screening): {}/{}", eligible.len(), all_states.len());
        assert!(
            !eligible.is_empty(),
            "keine Zustaende mit echtem Schnitt gefunden -- Stichproben-Aufbau defekt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        );

        // ── Schritt 2: VOLLE eligible Menge (siehe Entscheidung oben, statt
        // einer Zufalls-Teilmenge) -- `sample_all_idx` ist die GESAMTE
        // `eligible`-Menge, sortiert nach Original-Index. ──
        let mut sample_all_idx: Vec<usize> = eligible.clone();
        sample_all_idx.sort_unstable();

        let states: Vec<GameState> = sample_all_idx.iter().map(|&i| all_states[i].clone()).collect();
        let record_indices: Vec<usize> = sample_all_idx.iter().map(|&i| all_record_indices[i]).collect();
        let feats: Vec<Vec<f32>> = sample_all_idx.iter().map(|&i| all_feats[i].clone()).collect();
        println!(
            "Volle Real-Schnitt-Menge (keine Stichprobe mehr, siehe Entscheidung): {} Zustaende (erste 5 record_indices: {:?})",
            states.len(),
            &record_indices[..5.min(record_indices.len())]
        );

        // ── Schritt 3: die vier Arme, NUR fuer die Stichprobe. ──
        // Arm "tract"/"synchron" (Batch=1 je Zustand -- dieselbe Berechnung
        // dient als Seite A in ALLEN DREI Vergleichen, siehe Funktions-
        // Kommentar).
        let mut tract_policy: Vec<Vec<f32>> = Vec::with_capacity(states.len());
        let mut tract_moon: Vec<Vec<f32>> = Vec::with_capacity(states.len());
        for f in &feats {
            let (p, _v, m, _pt) = net.eval_batch(&[f.as_slice()]).expect("eval_batch(1)").remove(0);
            tract_policy.push(p);
            tract_moon.push(m);
        }

        // Arm "ORT-CUDA".
        let refs: Vec<&[f32]> = feats.iter().map(|v| v.as_slice()).collect();
        let ort_out = crate::net_ort::eval_batch_via_ort_cuda(&net, &refs)
            .expect("ORT-CUDA-Rundlauf (CUDA-Session muss aufbaubar sein)");

        // Arm "verschraenkt" (Sammel-Faden, N_THREADS gleichzeitige Aufrufer)
        // -- exakt dasselbe Muster wie
        // `interleaved_matches_synchronous_gumbel_root_selection`.
        std::env::set_var("MOSAIC_INTERLEAVE_ENABLED", "1");
        std::env::set_var("MOSAIC_INTERLEAVE_BATCH_MAX", crate::net::EVAL_BATCH_MAX_N.to_string());
        std::env::set_var("MOSAIC_INTERLEAVE_FILL_TIMEOUT_US", "200");
        crate::net_batcher::ensure_batcher_for(&net);
        let batcher = crate::net_batcher::lookup(&net).expect("Sammel-Faden sollte registriert sein");

        const N_THREADS: usize = 32;
        let idx_queue: Arc<Mutex<VecDeque<usize>>> = Arc::new(Mutex::new((0..states.len()).collect()));
        let inter_results: Arc<Mutex<Vec<Option<(Vec<f32>, Vec<f32>)>>>> =
            Arc::new(Mutex::new(vec![None; states.len()]));
        let feats_arc = Arc::new(feats.clone());
        let mut handles = Vec::new();
        for _ in 0..N_THREADS {
            let idx_queue = Arc::clone(&idx_queue);
            let inter_results = Arc::clone(&inter_results);
            let batcher = Arc::clone(&batcher);
            let feats_arc = Arc::clone(&feats_arc);
            handles.push(std::thread::spawn(move || loop {
                let idx = idx_queue.lock().unwrap().pop_front();
                let Some(idx) = idx else { break };
                let row = batcher.eval_rows(&[feats_arc[idx].as_slice()]).expect("eval_rows");
                let (p, _v, m, _pt, _opp, _own) = row.into_iter().next().unwrap();
                inter_results.lock().unwrap()[idx] = Some((p, m));
            }));
        }
        for h in handles {
            h.join().unwrap();
        }
        let inter_results = Arc::try_unwrap(inter_results).unwrap().into_inner().unwrap();
        println!(
            "Sammel-Faden: {} Batches, {} Zeilen, mittlerer Batch = {:.2}",
            batcher.stats.batches.load(std::sync::atomic::Ordering::Relaxed),
            batcher.stats.rows.load(std::sync::atomic::Ordering::Relaxed),
            batcher.stats.mean_batch()
        );

        // ── Schritt 4: je Zustand die Kandidatenlisten je Arm + m_prime,
        // dann je Vergleich die Haeufigkeitsdifferenz ueber die Stichprobe. ──
        struct DiffAgg {
            max: f64,
            sum: f64,
            n: usize,
        }
        impl DiffAgg {
            fn new() -> Self {
                DiffAgg { max: 0.0, sum: 0.0, n: 0 }
            }
            fn push(&mut self, d: f64) {
                if d > self.max {
                    self.max = d;
                }
                self.sum += d;
                self.n += 1;
            }
            fn mean(&self) -> f64 {
                if self.n == 0 {
                    f64::NAN
                } else {
                    self.sum / self.n as f64
                }
            }
        }

        /// Haeufigkeit je Aktion (in `canon`-Reihenfolge) ueber die Seeds in
        /// `seed_range` (relativ zu `base_seed`, absolute Seeds =
        /// `base_seed + s`).
        fn freqs_over_seeds(
            acts: &[(Action, f32)],
            m_prime: usize,
            canon: &[Action],
            base_seed: u64,
            seed_range: std::ops::Range<u64>,
        ) -> Vec<f64> {
            let k = seed_range.end - seed_range.start;
            let mut counts = vec![0u32; canon.len()];
            for s in seed_range {
                let mut rng = StdRng::seed_from_u64(base_seed + s);
                let set = gumbel_topm_set(acts, m_prime, &mut rng);
                for a in &set {
                    if let Some(pos) = canon.iter().position(|c| c == a) {
                        counts[pos] += 1;
                    }
                }
            }
            counts.into_iter().map(|c| c as f64 / k as f64).collect()
        }

        let mut agg_tract_vs_ort = DiffAgg::new();
        let mut agg_sync_vs_inter = DiffAgg::new();
        let mut agg_selfcontrol = DiffAgg::new();
        // Zusatz-Transparenz: ueber wie viele der Zustaende unterscheidet
        // sich die Kandidatenlisten-REIHENFOLGE (die eigentliche Ursache
        // laut §15) zwischen den Armen UEBERHAUPT, in DIESER Batch-
        // Zusammensetzung (455 Zustaende in EINEM ORT-Aufruf, ~30er-Batches
        // beim Sammel-Faden)? Beantwortet, ob das Aggregat unten
        // "Reihenfolge nie verschieden" widerspiegelt oder "Reihenfolge oft
        // verschieden, aber die Frequenz-Differenz trotzdem klein".
        let mut n_states_order_diff_ort = 0usize;
        let mut n_states_order_diff_inter = 0usize;

        for i in 0..states.len() {
            let state = &states[i];
            let record_index = record_indices[i];

            let mut moon_arr_tract = [0f32; 5];
            for (j, s) in tract_moon[i].iter().take(5).enumerate() {
                moon_arr_tract[j] = *s;
            }
            let (o_policy, _o_v, o_moon, _o_pt) = &ort_out[i];
            let mut moon_arr_ort = [0f32; 5];
            for (j, s) in o_moon.iter().take(5).enumerate() {
                moon_arr_ort[j] = *s;
            }
            let (inter_policy, inter_moon) = inter_results[i].clone().expect("jede Zeile beantwortet");
            let mut moon_arr_inter = [0f32; 5];
            for (j, s) in inter_moon.iter().take(5).enumerate() {
                moon_arr_inter[j] = *s;
            }

            let (acts_tract, _) = build_untried_actions(state, &tract_policy[i], &moon_arr_tract, true);
            let (acts_ort, _) = build_untried_actions(state, o_policy, &moon_arr_ort, true);
            let (acts_inter, _) = build_untried_actions(state, &inter_policy, &moon_arr_inter, true);
            let n_root = acts_tract.len();
            assert_eq!(acts_ort.len(), n_root, "record #{record_index}: ORT-Kandidatenzahl weicht ab?!");
            assert_eq!(acts_inter.len(), n_root, "record #{record_index}: verschraenkte Kandidatenzahl weicht ab?!");
            let m_prime = m_for_400_sims.min(n_root);
            assert!(
                m_prime < n_root,
                "record #{record_index}: Screening sagte echten Schnitt zu, jetzt keiner mehr -- Bug"
            );

            let order_diff_ort: usize = (0..n_root).filter(|&k| acts_tract[k].0 != acts_ort[k].0).count();
            let order_diff_inter: usize = (0..n_root).filter(|&k| acts_tract[k].0 != acts_inter[k].0).count();
            if order_diff_ort > 0 {
                n_states_order_diff_ort += 1;
            }
            if order_diff_inter > 0 {
                n_states_order_diff_inter += 1;
            }
            if record_index == 320 {
                println!(
                    "record#320 (bekannt aus §14/§15): n_root={n_root} order_diff(tract,ort)={order_diff_ort} order_diff(tract,inter)={order_diff_inter} -- in DIESER Batch-Zusammensetzung"
                );
            }
            let canon: Vec<Action> = acts_tract.iter().map(|(a, _)| a.clone()).collect();
            let base_seed = 900_000_000u64 + record_index as u64 * 1_000_000u64;

            let f_tract_a = freqs_over_seeds(&acts_tract, m_prime, &canon, base_seed, 0..K_HALF as u64);
            let f_tract_b =
                freqs_over_seeds(&acts_tract, m_prime, &canon, base_seed, K_HALF as u64..2 * K_HALF as u64);
            let f_ort_b = freqs_over_seeds(&acts_ort, m_prime, &canon, base_seed, K_HALF as u64..2 * K_HALF as u64);
            let f_inter_b =
                freqs_over_seeds(&acts_inter, m_prime, &canon, base_seed, K_HALF as u64..2 * K_HALF as u64);

            for j in 0..canon.len() {
                agg_tract_vs_ort.push((f_tract_a[j] - f_ort_b[j]).abs());
                agg_sync_vs_inter.push((f_tract_a[j] - f_inter_b[j]).abs());
                agg_selfcontrol.push((f_tract_a[j] - f_tract_b[j]).abs());
            }

            // Zusatz-Transparenz (nicht im Auftrag verlangt, aber ohne sie
            // waere der einzige BEKANNTE Einzelfall aus §14/§15 im Aggregat
            // unsichtbar): den EINEN bekannten Vertauschungs-Zustand
            // `record_index=320` NAMENTLICH mit seinen eigenen Werten
            // ausweisen, statt ihn im Pool aus 50000+ Paaren verschwinden zu
            // lassen. KEINE Deutung -- nur die Zahlen fuer genau diese zwei
            // Aktionen.
            if record_index == 320 {
                println!("\n--- Zusatz (nicht aggregiert): bekannter Zustand record_index=320 einzeln ---");
                for j in 0..canon.len() {
                    let d_ort = (f_tract_a[j] - f_ort_b[j]).abs();
                    let d_inter = (f_tract_a[j] - f_inter_b[j]).abs();
                    let d_self = (f_tract_a[j] - f_tract_b[j]).abs();
                    if d_ort > 0.01 || d_inter > 0.01 || d_self > 0.01 {
                        println!(
                            "  {:?}: f_tract_a={:.4} f_tract_b={:.4} f_ort_b={:.4} f_inter_b={:.4}  |diff tract/ort|={:.4} |diff sync/inter|={:.4} |diff selfcontrol|={:.4}",
                            canon[j], f_tract_a[j], f_tract_b[j], f_ort_b[j], f_inter_b[j], d_ort, d_inter, d_self
                        );
                    }
                }
            }
        }

        println!(
            "\nKandidatenlisten-REIHENFOLGE unterschiedlich (tract vs. ORT): {n_states_order_diff_ort}/{} Zustaende",
            states.len()
        );
        println!(
            "Kandidatenlisten-REIHENFOLGE unterschiedlich (tract vs. verschraenkt): {n_states_order_diff_inter}/{} Zustaende",
            states.len()
        );
        println!(
            "\n=== VERTEILUNGSVERGLEICH (N={} Zustaende, K/2={K_HALF} Seeds je Seite) ===",
            states.len()
        );
        println!("{:<38} {:>10} {:>12} {:>8}", "Vergleich", "max|diff|", "mittel|diff|", "n Paare");
        println!(
            "{:<38} {:>10.4} {:>12.4} {:>8}",
            "tract vs. ORT-CUDA", agg_tract_vs_ort.max, agg_tract_vs_ort.mean(), agg_tract_vs_ort.n
        );
        println!(
            "{:<38} {:>10.4} {:>12.4} {:>8}",
            "synchron vs. verschraenkt (tract)", agg_sync_vs_inter.max, agg_sync_vs_inter.mean(), agg_sync_vs_inter.n
        );
        println!(
            "{:<38} {:>10.4} {:>12.4} {:>8}",
            "SELBSTKONTROLLE (tract vs. tract)", agg_selfcontrol.max, agg_selfcontrol.mean(), agg_selfcontrol.n
        );
        println!(
            "\ntract-vs-ORT max innerhalb Selbstkontrolle-max? {} ({:.4} vs. {:.4})",
            agg_tract_vs_ort.max <= agg_selfcontrol.max,
            agg_tract_vs_ort.max,
            agg_selfcontrol.max
        );
        println!(
            "synchron-vs-verschraenkt max innerhalb Selbstkontrolle-max? {} ({:.4} vs. {:.4})",
            agg_sync_vs_inter.max <= agg_selfcontrol.max,
            agg_sync_vs_inter.max,
            agg_selfcontrol.max
        );
        println!(
            "tract-vs-ORT Mittel innerhalb Selbstkontrolle-Mittel? {} ({:.4} vs. {:.4})",
            agg_tract_vs_ort.mean() <= agg_selfcontrol.mean(),
            agg_tract_vs_ort.mean(),
            agg_selfcontrol.mean()
        );
        println!(
            "synchron-vs-verschraenkt Mittel innerhalb Selbstkontrolle-Mittel? {} ({:.4} vs. {:.4})",
            agg_sync_vs_inter.mean() <= agg_selfcontrol.mean(),
            agg_sync_vs_inter.mean(),
            agg_selfcontrol.mean()
        );
    }

    // ── Weg V (Verschraenkung, `net_batcher.rs`), Nutzer-Auftrag 2026-08-12
    // "dann leg los" -- ABNAHME Punkte 2+3. Wiederverwendet die Helfer
    // `legal_logits_sorted`/`gumbel_topm_set` von oben statt sie neu zu bauen.

    /// ABNAHME Punkt 2: ENTSCHEIDUNGSGLEICHHEIT synchron<->verschraenkt, mit
    /// derselben Messkette wie `ort_cuda_matches_tract_gumbel_root_selection`
    /// (Argmax + Gumbel-Top-m auf denselben 1148 Zustaenden), aber "synchron"
    /// (EIN `Net::eval_batch(&[feats])`-Aufruf je Zustand, heutiges Verhalten)
    /// gegen "verschraenkt" (derselbe `eval_batch`-Vertrag, aber ueber den
    /// registrierten Sammel-Faden UND mit `N_THREADS` GLEICHZEITIGEN
    /// Aufrufern, die ihre Zeilen tatsaechlich miteinander mischen koennen).
    /// Gleiches Backend (tract) auf beiden Seiten -- der einzige Unterschied
    /// ist die Batch-KOMPOSITION, nicht die Inferenz-Maschinerie (KEIN
    /// Cross-Framework-Vorbehalt noetig, nur der schon existierende "tract
    /// ist ueber verschiedene Batch-Plaene nicht bitgleich"-Praezedenzfall,
    /// `net.rs:840`).
    ///
    /// Berichtet nebenbei den TATSAECHLICH erreichten mittleren Batch
    /// (`Batcher::stats`) -- ABNAHME Punkt 3s zweite Haelfte, hier OHNE
    /// synthetische Baumarbeit zwischen zwei Anfragen (`N_THREADS` Faeden
    /// senden so schnell wie moeglich hintereinander) -- das ist also der
    /// MECHANISCH ERREICHBARE Batch bei Sattelung, NICHT die realistische
    /// Zahl unter echter Baumarbeit (die liefert
    /// `interleaved_throughput_vs_synchronous` unten).
    ///
    /// `#[ignore]`: braucht das lokale ONNX UND die exportierte JSON-Datei.
    /// KEIN Python/Torch noetig (reiner tract-Vergleich).
    #[test]
    #[ignore]
    fn interleaved_matches_synchronous_gumbel_root_selection() {
        use crate::net::Net;
        use std::collections::VecDeque;
        use std::sync::{Arc, Mutex};

        let states_path = std::env::var("MOSAIC_FROZEN_STATES_JSON").unwrap_or_else(|_| panic!(
            "MOSAIC_FROZEN_STATES_JSON nicht gesetzt -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ));
        let raw = std::fs::read_to_string(&states_path).unwrap_or_else(|e| panic!(
            "{states_path} nicht lesbar ({e}) -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ));
        let records: Vec<Value> = serde_json::from_str(&raw).expect("JSON-Array erwartet");
        assert!(!records.is_empty());

        let repo = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("..");
        let onnx_path = repo.join("models/alphazero_v20_2d_opp_brierbest.onnx");
        assert!(
            onnx_path.exists(),
            "{onnx_path:?} fehlt -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        );
        let net = Arc::new(Net::load_auto(onnx_path.to_str().unwrap()).unwrap_or_else(|e| panic!(
            "{onnx_path:?} nicht ladbar ({e}) -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        )));

        let mut states: Vec<GameState> = Vec::with_capacity(records.len());
        let mut record_indices: Vec<usize> = Vec::with_capacity(records.len());
        for entry in &records {
            let record_index = entry["record_index"].as_u64().unwrap() as usize;
            let mut rng = StdRng::seed_from_u64(record_index as u64);
            match crate::serialize::json_to_state(&entry["state"], &mut rng) {
                Ok(s) => {
                    states.push(s);
                    record_indices.push(record_index);
                }
                Err(e) => eprintln!("  ⚠️  record #{record_index}: json_to_state fehlgeschlagen ({e}) -- ausgelassen."),
            }
        }
        let feats: Vec<Vec<f32>> = states.iter().map(|s| crate::features::features_for_net(&net, s)).collect();

        // ── ARM 1: synchron (heutiges Verhalten, Batch=1 je Zustand) ──
        let mut sync_policy: Vec<Vec<f32>> = Vec::with_capacity(states.len());
        let mut sync_moon: Vec<Vec<f32>> = Vec::with_capacity(states.len());
        for f in &feats {
            let (p, _v, m, _pt) = net.eval_batch(&[f.as_slice()]).expect("eval_batch(1)").remove(0);
            sync_policy.push(p);
            sync_moon.push(m);
        }

        // ── ARM 2: verschraenkt (Sammel-Faden, N_THREADS gleichzeitige Aufrufer) ──
        std::env::set_var("MOSAIC_INTERLEAVE_ENABLED", "1");
        std::env::set_var("MOSAIC_INTERLEAVE_BATCH_MAX", crate::net::EVAL_BATCH_MAX_N.to_string());
        std::env::set_var("MOSAIC_INTERLEAVE_FILL_TIMEOUT_US", "200");
        crate::net_batcher::ensure_batcher_for(&net);
        let batcher = crate::net_batcher::lookup(&net).expect("Sammel-Faden sollte registriert sein");

        const N_THREADS: usize = 32;
        let idx_queue: Arc<Mutex<VecDeque<usize>>> = Arc::new(Mutex::new((0..states.len()).collect()));
        let inter_results: Arc<Mutex<Vec<Option<(Vec<f32>, Vec<f32>)>>>> =
            Arc::new(Mutex::new(vec![None; states.len()]));
        let feats_arc = Arc::new(feats);

        let mut handles = Vec::new();
        for _ in 0..N_THREADS {
            let idx_queue = Arc::clone(&idx_queue);
            let inter_results = Arc::clone(&inter_results);
            let batcher = Arc::clone(&batcher);
            let feats_arc = Arc::clone(&feats_arc);
            handles.push(std::thread::spawn(move || loop {
                let idx = idx_queue.lock().unwrap().pop_front();
                let Some(idx) = idx else { break };
                let row = batcher.eval_rows(&[feats_arc[idx].as_slice()]).expect("eval_rows");
                let (p, _v, m, _pt, _opp, _own) = row.into_iter().next().unwrap();
                inter_results.lock().unwrap()[idx] = Some((p, m));
            }));
        }
        for h in handles {
            h.join().unwrap();
        }
        let inter_results = Arc::try_unwrap(inter_results).unwrap().into_inner().unwrap();

        println!(
            "Sammel-Faden (Saettigung, keine Baumarbeit zwischen Anfragen): {} Batches, {} Zeilen, mittlerer Batch = {:.2}",
            batcher.stats.batches.load(std::sync::atomic::Ordering::Relaxed),
            batcher.stats.rows.load(std::sync::atomic::Ordering::Relaxed),
            batcher.stats.mean_batch()
        );

        // ── Vergleich: Argmax + Gumbel-Top-m, wie im Policy-Tor-Test ──
        let m_for_400_sims = gumbel_top_m_for_budget(400);
        let mut n_total = 0usize;
        let mut n_argmax_mismatch = 0usize;
        let mut n_topm_mismatch = 0usize;

        for i in 0..states.len() {
            let state = &states[i];
            let (inter_policy, inter_moon) = inter_results[i].clone().expect("jede Zeile sollte beantwortet sein");

            let sorted_sync = legal_logits_sorted(state, &sync_policy[i]);
            let sorted_inter = legal_logits_sorted(state, &inter_policy);
            assert_eq!(sorted_sync.len(), sorted_inter.len(), "record #{}: unterschiedliche Legal-ID-Menge?!", record_indices[i]);
            if sorted_sync.is_empty() {
                continue;
            }
            n_total += 1;
            if sorted_sync[0].0 != sorted_inter[0].0 {
                n_argmax_mismatch += 1;
            }

            let mut moon_arr_sync = [0f32; 5];
            for (j, s) in sync_moon[i].iter().take(5).enumerate() {
                moon_arr_sync[j] = *s;
            }
            let mut moon_arr_inter = [0f32; 5];
            for (j, s) in inter_moon.iter().take(5).enumerate() {
                moon_arr_inter[j] = *s;
            }
            let (acts_sync, _) = build_untried_actions(state, &sync_policy[i], &moon_arr_sync, true);
            let (acts_inter, _) = build_untried_actions(state, &inter_policy, &moon_arr_inter, true);
            assert_eq!(acts_sync.len(), acts_inter.len(), "record #{}: unterschiedliche Kandidatenzahl?!", record_indices[i]);
            let n_root = acts_sync.len();
            let m_prime = m_for_400_sims.min(n_root);

            let seed = 900_000_000u64 + record_indices[i] as u64;
            let mut rng_a = StdRng::seed_from_u64(seed);
            let mut rng_b = StdRng::seed_from_u64(seed);
            let set_sync = gumbel_topm_set(&acts_sync, m_prime, &mut rng_a);
            let set_inter = gumbel_topm_set(&acts_inter, m_prime, &mut rng_b);
            let matches = set_sync.len() == set_inter.len() && set_sync.iter().all(|a| set_inter.contains(a));
            if !matches {
                n_topm_mismatch += 1;
            }
        }

        println!("\n=== Entscheidungsgleichheit synchron<->verschraenkt (Weg V) ===");
        println!("Stellungen verarbeitet: {n_total}");
        println!(
            "Argmax-Abweichung:      {n_argmax_mismatch}/{n_total} ({:.4}%)",
            n_argmax_mismatch as f64 / n_total as f64 * 100.0
        );
        println!(
            "Top-{m_for_400_sims}-Mengen-Abweichung: {n_topm_mismatch}/{n_total} ({:.4}%)",
            n_topm_mismatch as f64 / n_total as f64 * 100.0
        );
    }

    /// Realistische "Baumarbeit" zwischen zwei Blattanfragen EINES Fadens --
    /// HERGELEITET (NICHT frisch gemessen fuer dieses Modell/diese Maschine),
    /// aus `evaluations/selfplay_time_profile.json`: Netz-Anteil 61,96% der
    /// Gesamtzeit (4845457676500ns) ueber 1.314.962 Netz-Aufrufe ->
    /// `(1-0.6196)*4845457676500/1314962 ≈ 1.401.723ns ≈ 1,40ms` "Rest" je
    /// Netz-Aufruf (Tiling+Bootstrap+R5+Rest-Kategorien zusammen). Diese
    /// Herleitung selbst ist in dieser Sitzung NICHT nachgemessen worden
    /// (andere Maschine/anderes Modell als hier) -- als Naeherung markiert.
    const SYNTHETIC_TREE_WORK: std::time::Duration = std::time::Duration::from_micros(1402);

    /// Busy-Spin (bewusst KEIN `thread::sleep`) fuer ungefaehr `dur`: reale
    /// Baumarbeit (Tiling-Solver, Board-Updates) ist CPU-gebunden und
    /// konkurriert dadurch mit ANDEREN Faeden um Kerne -- ein `sleep` wuerde
    /// den Kern freigeben und damit die Kernkonkurrenz-Dynamik verfaelschen,
    /// die genau hier nachgebildet werden soll. Kalibrierung ist grob
    /// (Wall-Clock-Polling), fuer den Zweck (Duty-Verhaeltnis nachbilden,
    /// nicht Zyklen zaehlen) ausreichend.
    fn busy_spin(dur: std::time::Duration) {
        let t0 = std::time::Instant::now();
        let mut x: u64 = 0xDEAD_BEEF;
        while t0.elapsed() < dur {
            x = x.wrapping_add(1).wrapping_mul(2654435761);
        }
        std::hint::black_box(x);
    }

    /// ABNAHME Punkt 3: Evals/s verschraenkt gegen synchron, bei einer
    /// realistischen Fadenzahl -- UND der tatsaechlich erreichte mittlere
    /// Batch UNTER ECHTER (synthetischer, aber kalibrierter) Baumarbeit
    /// zwischen den Anfragen (`SYNTHETIC_TREE_WORK`) -- das ist die Zahl, die
    /// `interleave_concurrency_probe.rs` offenlassen musste (dortige Faeden
    /// taten zwischen zwei Anfragen NICHTS, Bestfall fuer die Fuellung).
    ///
    /// ZWEI Arme, gleiche Zustaende/Merkmale, gleiche Fadenzahl (der fruehere
    /// Arm 3, verschraenkt + Torch/CUDA-IPC, ist mit Weg A am 2026-08-15
    /// entfernt worden -- gemessen verworfen, PREREG §9):
    /// 1. **Synchron** (heutiges Verhalten): `Net::eval_batch(&[feats])`
    ///    direkt, kein Sammel-Faden.
    /// 2. **Verschraenkt, tract**: derselbe Aufruf ueber den Sammel-Faden --
    ///    isoliert die Wirkung der Buendel-MECHANIK allein.
    ///
    /// `#[ignore]`: braucht das lokale ONNX-Modell.
    #[test]
    #[ignore]
    fn interleaved_throughput_vs_synchronous() {
        use crate::net::Net;
        use std::sync::Arc;
        use std::time::Instant;

        let repo = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("..");
        let onnx_path = repo.join("models/alphazero_v20_2d_opp_brierbest.onnx");
        assert!(
            onnx_path.exists(),
            "{onnx_path:?} fehlt -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        );
        let net = Arc::new(Net::load_auto(onnx_path.to_str().unwrap()).unwrap_or_else(|e| panic!(
            "{onnx_path:?} nicht ladbar ({e}) -- Test-Voraussetzung fehlt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        )));

        // Ein paar echte Drafting-Zustaende (kein frozen-Set noetig hier --
        // reiner Durchsatz-/Batch-Test, keine Entscheidungs-Analyse).
        let mut rng = StdRng::seed_from_u64(20260812);
        let mut pool: Vec<Vec<f32>> = Vec::new();
        for tag in 0..64u64 {
            if let Some(s) = random_drafting_state(tag, 5 + (tag % 7) as u32, &mut rng) {
                pool.push(crate::features::features_for_net(&net, &s));
            }
        }
        assert!(
            !pool.is_empty(),
            "keine Drafting-Zustaende erzeugbar -- Test-Aufbau defekt, der Test darf nicht leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        );
        let pool = Arc::new(pool);

        const N_THREADS: usize = 11; // heutige Selfplay-Konvention (siehe Bericht).
        const ITERS_PER_THREAD: usize = 60;

        // ── Arm 1: synchron ──
        let t0 = Instant::now();
        let handles: Vec<_> = (0..N_THREADS)
            .map(|tid| {
                let net = Arc::clone(&net);
                let pool = Arc::clone(&pool);
                std::thread::spawn(move || {
                    for it in 0..ITERS_PER_THREAD {
                        let f = &pool[(tid * 7 + it) % pool.len()];
                        let _ = net.eval_batch(&[f.as_slice()]).expect("eval_batch(1)");
                        busy_spin(SYNTHETIC_TREE_WORK);
                    }
                })
            })
            .collect();
        for h in handles {
            h.join().unwrap();
        }
        let sync_elapsed = t0.elapsed();
        let total_evals = (N_THREADS * ITERS_PER_THREAD) as f64;
        let sync_rate = total_evals / sync_elapsed.as_secs_f64();

        // ── Arm 2: verschraenkt, tract ──
        std::env::set_var("MOSAIC_INTERLEAVE_ENABLED", "1");
        std::env::set_var("MOSAIC_INTERLEAVE_BATCH_MAX", crate::net::EVAL_BATCH_MAX_N.to_string());
        std::env::set_var("MOSAIC_INTERLEAVE_FILL_TIMEOUT_US", "200");
        crate::net_batcher::ensure_batcher_for(&net);
        let batcher = crate::net_batcher::lookup(&net).expect("Sammel-Faden sollte registriert sein");
        let batches_before = batcher.stats.batches.load(std::sync::atomic::Ordering::Relaxed);
        let rows_before = batcher.stats.rows.load(std::sync::atomic::Ordering::Relaxed);

        let t1 = Instant::now();
        let handles: Vec<_> = (0..N_THREADS)
            .map(|tid| {
                let batcher = Arc::clone(&batcher);
                let pool = Arc::clone(&pool);
                std::thread::spawn(move || {
                    for it in 0..ITERS_PER_THREAD {
                        let f = &pool[(tid * 7 + it) % pool.len()];
                        let _ = batcher.eval_rows(&[f.as_slice()]).expect("eval_rows");
                        busy_spin(SYNTHETIC_TREE_WORK);
                    }
                })
            })
            .collect();
        for h in handles {
            h.join().unwrap();
        }
        let inter_tract_elapsed = t1.elapsed();
        let inter_tract_rate = total_evals / inter_tract_elapsed.as_secs_f64();
        let batches_delta = batcher.stats.batches.load(std::sync::atomic::Ordering::Relaxed) - batches_before;
        let rows_delta = batcher.stats.rows.load(std::sync::atomic::Ordering::Relaxed) - rows_before;
        let mean_batch_tract = if batches_delta > 0 { rows_delta as f64 / batches_delta as f64 } else { 0.0 };

        println!("\n=== Durchsatz verschraenkt<->synchron (Weg V), N={N_THREADS} Faeden, {ITERS_PER_THREAD} Iters/Faden ===");
        println!("Synchron            : {sync_rate:.1} Evals/s ({sync_elapsed:?})");
        println!(
            "Verschraenkt (tract) : {inter_tract_rate:.1} Evals/s ({inter_tract_elapsed:?}), mittlerer Batch = {mean_batch_tract:.2} ({batches_delta} Batches, {rows_delta} Zeilen)"
        );
    }

    // ═══════════════════════════════════════════════════════════════════
    // Ownership-Verbraucher Teil 1 (`evaluations/PREREG_ownership_consumer.md`
    // §2/§6) -- Tor B (Bestandsschutz) und der Formel-Beleg.
    // ═══════════════════════════════════════════════════════════════════

    /// Synthetische Ownership-LOGITS: `-20` ueberall (sigmoid ~ 2e-9),
    /// `+20` (sigmoid ~ 1) auf den Feldern von Spalte `spalte` in der
    /// EGO-Haelfte `[0:36]`. `-20` als Grundwert statt 0: bei p=0,5 wuerde
    /// jede der uebrigen fuenf Spalten ueber `0,5^6 * 7` einen Untergrund von
    /// zusammen ~0,55 Punkten erzeugen und den Formel-Beleg verwaessern.
    fn synth_ownership_column(breite: usize, spalte: usize) -> Vec<f32> {
        let mut v = vec![-20.0f32; breite];
        for r in 0..6 {
            v[crate::scoring::ownership_index_for_grid(r, spalte)] = 20.0;
        }
        v
    }

    /// TOR B, Teil 1: bei ungesetztem `MOSAIC_OWNERSHIP_W` (Default 0,0) ist
    /// der Verbraucher tot -- `apply_ownership_shaping` gibt den Blattwert
    /// BIT-GENAU unveraendert zurueck, egal was der Kopf sagt und egal, ob er
    /// 72 oder 140 breit ist. Muster von
    /// `merged_shaping_is_exact_identity_by_default`.
    #[test]
    fn ownership_shaping_is_exact_identity_by_default() {
        assert_eq!(
            ownership_weight(),
            0.0,
            "Test-Voraussetzung: MOSAIC_OWNERSHIP_W darf hier nicht gesetzt sein"
        );
        let mut rng = StdRng::seed_from_u64(20260816);
        let mut checked = 0;
        for gi in 0..8u64 {
            let Some(state) = random_drafting_state(gi, 16, &mut rng) else { continue };
            for breite in [0usize, 71, 72, 140] {
                let own = if breite == 0 { Vec::new() } else { synth_ownership_column(breite, 2) };
                for v in [[0.5f64, 0.5f64], [0.9, 0.2], [0.0, 1.0], [1.0, 0.0]] {
                    assert_eq!(
                        apply_ownership_shaping(v, &state, &own),
                        v,
                        "Spiel {gi}, Kopfbreite {breite}: w_own=0 muss exakte Identitaet sein"
                    );
                }
            }
            checked += 1;
        }
        assert!(checked >= 4, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    /// TOR B, Teil 2 (Paritaetsprobe): `net_leaf_eval` liefert bei Default
    /// denselben Wert wie der Pfad OHNE den neuen `apply_ownership_shaping`-
    /// Aufruf -- bit-genau, gegen einen von Hand nachgebauten Alt-Pfad.
    /// Gleiches Muster wie
    /// `net_leaf_eval_matches_pre_unlock_shaping_path_when_weight_is_zero`.
    #[test]
    fn net_leaf_eval_matches_pre_ownership_shaping_path_when_weight_is_zero() {
        assert_eq!(ownership_weight(), 0.0, "Test-Voraussetzung: MOSAIC_OWNERSHIP_W ungesetzt");
        let net = load_test_net();
        assert!(net.has_own_head(), "Test-Voraussetzung: der Champion traegt einen ownership-Output");

        let mut rng = StdRng::seed_from_u64(20260817);
        let mut checked = 0;
        for gi in 0..10u64 {
            let Some(state) = random_drafting_state(gi, 14, &mut rng) else { continue };
            let actual = net_leaf_eval(&net, &state);

            let feats = crate::features::features_for_net(&net, &state);
            let mut flipped = state.clone();
            flipped.current_player = 1 - state.current_player;
            let other_feats = crate::features::features_for_net(&net, &flipped);
            let (
                (_l, value, _m, points, opp_points, own),
                (_ol, o_value, _om, o_points, o_opp_points, _o_own),
            ) = net.eval_pair_ex(&feats, &other_feats).expect("eval_pair_ex (Alt-Pfad)");
            // Der Kopf IST da und wird auch gelesen -- der Test darf nicht
            // deshalb gruen sein, weil gar nichts durchkommt.
            assert_eq!(
                own.len(),
                2 * crate::scoring::OWNERSHIP_FIELDS,
                "Spiel {gi}: ownership kommt nicht (in erwarteter Breite) durch die Inferenzkette"
            );
            let mover_val = blended_leaf_win_prob(&value, &points, &opp_points);
            let other_val = blended_leaf_win_prob(&o_value, &o_points, &o_opp_points);
            let raw = if state.current_player == 0 { [mover_val, other_val] } else { [other_val, mover_val] };
            let expected = apply_scoring_shaping(apply_value_shrink(raw, state.round_number), &state);

            assert_eq!(actual, expected, "Spiel {gi}: net_leaf_eval weicht bei w_own=0 vom Alt-Pfad ab");
            checked += 1;
        }
        assert!(checked >= 6, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    /// Robuste Kopf-Erkennung (Auftragspunkt 2): ein FEHLENDER oder zu
    /// SCHMALER Kopf darf bei `w_own > 0` nicht panisch werden, sondern
    /// verhaelt sich wie Gewicht 0 -- der 72er-Kopf des amtierenden Champions
    /// UND der 140er der Sweep-Checkpoints muessen dagegen BEIDE steuern
    /// koennen (identisch, weil nur die ersten 72 Werte gelesen werden).
    #[test]
    fn ownership_shaping_tolerates_missing_and_too_narrow_head() {
        let mut rng = StdRng::seed_from_u64(20260818);
        let Some(mut state) = random_drafting_state(3, 16, &mut rng) else {
            panic!("Testaufbau: random_drafting_state lieferte keinen Zustand");
        };
        state.scoring_tile_ids = vec![1];
        let v = [0.5f64, 0.5f64];
        let gew = [1.0f64; 8];
        let scale = [WERTUNG_SHAPING_SCALE; 8];

        for zu_schmal in [Vec::new(), vec![0.0f32; 35], vec![0.0f32; 71]] {
            assert_eq!(
                apply_ownership_shaping_full(v, &state, &zu_schmal, 0.5, &gew, false, &scale),
                v,
                "Kopfbreite {} muss sich wie w_own=0 verhalten (kein Panic, kein Teil-Shift)",
                zu_schmal.len()
            );
        }

        let out72 = apply_ownership_shaping_full(v, &state, &synth_ownership_column(72, 2), 0.5, &gew, false, &scale);
        let out140 = apply_ownership_shaping_full(v, &state, &synth_ownership_column(140, 2), 0.5, &gew, false, &scale);
        assert_ne!(out72, v, "ein brauchbarer 72er-Kopf muss den Blattwert bewegen");
        assert_eq!(out72, out140, "72er- und 140er-Kopf muessen denselben Shift liefern (nur [0:72] wird gelesen)");
    }

    /// FORMEL-BELEG (Auftrag: "sonst ist die Formel nur behauptet"): mit
    /// einem KUENSTLICHEN Ownership-Vektor -- eine Spalte sicher, alles
    /// andere sicher leer -- und nur Kriterium 1 gezogen muss der Shift exakt
    /// `w_own * gew_1 * tanh(7 / 50)` sein, und er darf NUR bei dem Spieler
    /// landen, dem die Ego-Haelfte `[0:36]` gehoert.
    #[test]
    fn ownership_shaping_returns_exactly_the_prereg_formula_and_the_right_half() {
        let mut rng = StdRng::seed_from_u64(20260819);
        let Some(mut state) = random_drafting_state(5, 16, &mut rng) else {
            panic!("Testaufbau: random_drafting_state lieferte keinen Zustand");
        };
        // Nur die Vertikale gezogen -- sonst rechnete der Untergrund anderer
        // Kriterien mit und der Beleg waere nicht mehr exakt.
        state.scoring_tile_ids = vec![1];

        let w_own = 0.4f64;
        let gew = [1.0f64; 8];
        let scale = [WERTUNG_SHAPING_SCALE; 8];
        let own = synth_ownership_column(72, 2);
        let v = [0.5f64, 0.5f64];
        let out = apply_ownership_shaping_full(v, &state, &own, w_own, &gew, false, &scale);

        let erwartet_shift = w_own * (7.0f64 / WERTUNG_SHAPING_SCALE).tanh();
        let ego = state.current_player;
        let gegner = 1 - ego;
        assert!(
            (out[ego] - (v[ego] + erwartet_shift)).abs() < 1e-6,
            "Ego-Shift weicht von w_own*tanh(7/50)={erwartet_shift} ab: out={out:?}"
        );
        // Die Gegner-Haelfte `[36:72]` steht auf -20 (sicher leer) -> E_1 = 0
        // -> tanh(0) = 0 -> kein Shift.
        assert!(
            (out[gegner] - v[gegner]).abs() < 1e-9,
            "Gegner-Haelfte war leer, darf keinen Shift bekommen: out={out:?}"
        );

        // Gegenprobe der Perspektive: dieselbe Spalte in die GEGNER-Haelfte
        // gelegt muss den Shift auf den anderen Spieler drehen.
        let mut own_gegner = vec![-20.0f32; 72];
        for r in 0..6 {
            own_gegner[crate::scoring::OWNERSHIP_FIELDS + crate::scoring::ownership_index_for_grid(r, 2)] = 20.0;
        }
        let out2 = apply_ownership_shaping_full(v, &state, &own_gegner, w_own, &gew, false, &scale);
        assert!(
            (out2[gegner] - (v[gegner] + erwartet_shift)).abs() < 1e-6,
            "Gegner-Shift weicht ab: out2={out2:?}"
        );
        assert!((out2[ego] - v[ego]).abs() < 1e-9, "Ego darf jetzt keinen Shift bekommen: out2={out2:?}");

        // Kriteriengewicht 0 schaltet das Kriterium vollstaendig ab.
        let mut gew_aus = [1.0f64; 8];
        gew_aus[1] = 0.0;
        assert_eq!(
            apply_ownership_shaping_full(v, &state, &own, w_own, &gew_aus, false, &scale),
            v,
            "gew_1=0 muss Kriterium 1 vollstaendig abschalten"
        );
    }

    /// Die beiden neuen Knoepfe stehen bei ungesetzter Umgebung auf ihren
    /// dokumentierten Defaults -- `w_own=0` (aus) und `gew` alle 1,0 (der
    /// Hauptschalter ist `w_own`, nicht die Kriteriengewichte).
    #[test]
    fn ownership_knobs_default_to_off_weight_and_unit_criteria() {
        assert_eq!(ownership_weight(), 0.0);
        assert_eq!(ownership_weights(), [1.0; 8]);
    }

    // ── Baustein 2: MOSAIC_OWNERSHIP_SCALE (PREREG_reachability_target.md par.6) ──

    /// (a) Default: `ownership_scale()` liefert je Kriterium die alte feste
    /// Konstante `WERTUNG_SHAPING_SCALE` (50.0) -- byte-identisches
    /// Bestandsverhalten, ungesetzte Env-Var.
    #[test]
    fn ownership_scale_defaults_to_scoring_shaping_scale_per_criterion() {
        assert_eq!(ownership_scale(), [WERTUNG_SHAPING_SCALE; 8]);
    }

    /// (a) Formel-Beleg mit dem Default-Nenner reproduziert exakt dieselbe
    /// alte Formel `tanh(E/50)` wie vor Baustein 2 (alte Konstante hier
    /// explizit nachgebaut, nicht aus `ownership_scale()` gelesen -- sonst
    /// waere der Test gegen sich selbst blind fuer eine falsche Aenderung an
    /// der Konstante).
    #[test]
    fn ownership_shaping_full_with_default_denominator_reproduces_old_formula_bit_exactly() {
        const ALTE_KONSTANTE: f64 = 50.0;
        let mut rng = StdRng::seed_from_u64(20260819100);
        let Some(mut state) = random_drafting_state(7, 16, &mut rng) else {
            panic!("Testaufbau: random_drafting_state lieferte keinen Zustand");
        };
        state.scoring_tile_ids = vec![1];
        let w_own = 0.4f64;
        let gew = [1.0f64; 8];
        let own = synth_ownership_column(72, 2);
        let v = [0.5f64, 0.5f64];

        let scale_default = [ALTE_KONSTANTE; 8];
        let out = apply_ownership_shaping_full(v, &state, &own, w_own, &gew, false, &scale_default);
        // Die alte Formel wird ueber DIESELBE Pipeline nachgebaut (sigmoid ->
        // expected_plate_points -> tanh(e/50) mit der expliziten alten
        // Konstante, NICHT ueber ownership_scale()). Ein analytisches E=7,0
        // taugt hier nicht als Erwartung: der synthetische Kopf liefert
        // sigmoid(+-20) = 1 - 2e-9 je Zelle, das Sechser-Produkt drueckt E um
        // ~9e-8 unter 7,0 -- der erste Wurf dieses Tests scheiterte daran mit
        // einer Abweichung von 3e-9 bei Toleranz 1e-12.
        let ego = state.current_player;
        let mut p_own = [0.0f64; crate::scoring::OWNERSHIP_FIELDS];
        for (f, slot) in p_own.iter_mut().enumerate() {
            // Ego-Haelfte liegt bei [0:36], und `ego == current_player`.
            *slot = sigmoid(own[f] as f64);
        }
        let e = crate::scoring::expected_plate_points(&state.players[ego], &p_own, &state.scoring_tile_ids);
        let erwartet_shift: f64 =
            w_own * (0..8).map(|k| gew[k] * (e[k] / ALTE_KONSTANTE).tanh()).sum::<f64>();
        assert!(
            (out[ego] - (v[ego] + erwartet_shift)).abs() < 1e-15,
            "Default-Nenner muss bitgleich die alte Formel tanh(E/50) reproduzieren: out={out:?}, erwartet={}",
            v[ego] + erwartet_shift
        );
    }

    /// (b) Ein gesetzter (nicht-uniformer) Nenner je Kriterium AENDERT das
    /// Ergebnis gegenueber dem flachen Default -- direkt an der reinen
    /// Funktion geprueft (kein Env-Var/OnceLock-Umweg, siehe Testkommentar
    /// oben bei `apply_scoring_shaping_full`).
    #[test]
    fn ownership_scale_je_kriterium_aendert_den_shift_gegenueber_flachem_default() {
        let mut rng = StdRng::seed_from_u64(20260819101);
        let Some(mut state) = random_drafting_state(9, 16, &mut rng) else {
            panic!("Testaufbau: random_drafting_state lieferte keinen Zustand");
        };
        state.scoring_tile_ids = vec![1];
        let w_own = 0.4f64;
        let gew = [1.0f64; 8];
        let own = synth_ownership_column(72, 2);
        let v = [0.5f64, 0.5f64];

        let scale_flat = [WERTUNG_SHAPING_SCALE; 8];
        let mut scale_k1_eng = [WERTUNG_SHAPING_SCALE; 8];
        scale_k1_eng[1] = 1.0; // par.6: gemessener Nenner fuer k1 ~1 statt 50

        let out_flat = apply_ownership_shaping_full(v, &state, &own, w_own, &gew, false, &scale_flat);
        let out_eng = apply_ownership_shaping_full(v, &state, &own, w_own, &gew, false, &scale_k1_eng);
        assert_ne!(
            out_flat, out_eng,
            "ein engerer Nenner fuer Kriterium 1 muss den Shift gegenueber dem flachen Default veraendern"
        );
    }

}
