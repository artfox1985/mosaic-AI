//! Optionale Instrumentierung fürs Hot-Path-Profiling (siehe `benches/clone_cost.rs`
//! für die Kosten-pro-Klon-Messung und `examples/profile_clones.rs` für die
//! kombinierte Auswertung). Nur mit Feature `clone_profiling` aktiv -- ohne das
//! Feature sind alle `note_*`-Funktionen leere No-Ops (wegoptimiert, kein
//! Einfluss auf den Normalbetrieb). Aufrufstellen bleiben IMMER gleich (kein
//! `#[cfg(...)]` an den Call-Sites nötig), nur die Funktionskörper hier sind
//! bedingt kompiliert.

#[cfg(feature = "clone_profiling")]
use std::sync::atomic::{AtomicU64, AtomicUsize, Ordering};
#[cfg(feature = "clone_profiling")]
use std::time::Instant;

#[cfg(feature = "clone_profiling")]
static GAMESTATE_CLONE_COUNT: AtomicUsize = AtomicUsize::new(0);

/// An jeder `GameState`-Klon-Stelle im Such-Hot-Path aufrufen
/// (`mcts.rs`/`net_mcts.rs`: ein Klon je EXPAND-Schritt).
#[inline(always)]
pub fn note_gamestate_clone() {
    #[cfg(feature = "clone_profiling")]
    GAMESTATE_CLONE_COUNT.fetch_add(1, Ordering::Relaxed);
}

pub fn reset_gamestate_clone_count() {
    #[cfg(feature = "clone_profiling")]
    GAMESTATE_CLONE_COUNT.store(0, Ordering::Relaxed);
}

pub fn gamestate_clone_count() -> usize {
    #[cfg(feature = "clone_profiling")]
    {
        GAMESTATE_CLONE_COUNT.load(Ordering::Relaxed)
    }
    #[cfg(not(feature = "clone_profiling"))]
    {
        0
    }
}

// ── Grobe Zeit-Aufteilung je `make_node`-Aufruf (net_mcts.rs) ────────────────
// Drei Kandidaten fuer die "wo gehen die anderen 99.5% hin"-Frage: JSON+Feature-
// Serialisierung, Netz-Forward-Pass, DFS-Solver (Stage-1-Blattwert).

#[cfg(feature = "clone_profiling")]
static FEATURES_COUNT: AtomicUsize = AtomicUsize::new(0);
#[cfg(feature = "clone_profiling")]
static FEATURES_NANOS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "clone_profiling")]
static NET_EVAL_COUNT: AtomicUsize = AtomicUsize::new(0);
#[cfg(feature = "clone_profiling")]
static NET_EVAL_NANOS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "clone_profiling")]
static DFS_EVAL_COUNT: AtomicUsize = AtomicUsize::new(0);
#[cfg(feature = "clone_profiling")]
static DFS_EVAL_NANOS: AtomicU64 = AtomicU64::new(0);

macro_rules! note_and_read {
    ($note_fn:ident, $count_fn:ident, $ns_fn:ident, $reset_fn:ident, $count_static:ident, $nanos_static:ident) => {
        pub fn $note_fn(_elapsed_ns: u64) {
            #[cfg(feature = "clone_profiling")]
            {
                $count_static.fetch_add(1, Ordering::Relaxed);
                $nanos_static.fetch_add(_elapsed_ns, Ordering::Relaxed);
            }
        }
        pub fn $count_fn() -> usize {
            #[cfg(feature = "clone_profiling")]
            {
                $count_static.load(Ordering::Relaxed)
            }
            #[cfg(not(feature = "clone_profiling"))]
            {
                0
            }
        }
        pub fn $ns_fn() -> u64 {
            #[cfg(feature = "clone_profiling")]
            {
                $nanos_static.load(Ordering::Relaxed)
            }
            #[cfg(not(feature = "clone_profiling"))]
            {
                0
            }
        }
        pub fn $reset_fn() {
            #[cfg(feature = "clone_profiling")]
            {
                $count_static.store(0, Ordering::Relaxed);
                $nanos_static.store(0, Ordering::Relaxed);
            }
        }
    };
}

note_and_read!(note_features_ns, features_count, features_ns, reset_features, FEATURES_COUNT, FEATURES_NANOS);
note_and_read!(note_net_eval_ns, net_eval_count, net_eval_ns, reset_net_eval, NET_EVAL_COUNT, NET_EVAL_NANOS);
note_and_read!(note_dfs_eval_ns, dfs_eval_count, dfs_eval_ns, reset_dfs_eval, DFS_EVAL_COUNT, DFS_EVAL_NANOS);

// ── Task #80: Self-Play-Kostenprofil (Gumbel-Zugsuche vs. rtv- vs.
// Bootstrap-Labels) ─────────────────────────────────────────────────────────
// Gleiches Muster wie oben: drei Zähler+Nanosekunden-Paare, je EIN
// `timed()`-Aufruf pro Kategorie in `self_play.rs::play_net_self_play_game`.
// Nur mit `clone_profiling` aktiv (Mess-Wheel) -- Normalbetrieb unverändert.

#[cfg(feature = "clone_profiling")]
static GUMBEL_MOVE_COUNT: AtomicUsize = AtomicUsize::new(0);
#[cfg(feature = "clone_profiling")]
static GUMBEL_MOVE_NANOS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "clone_profiling")]
static RTV_COUNT: AtomicUsize = AtomicUsize::new(0);
#[cfg(feature = "clone_profiling")]
static RTV_NANOS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "clone_profiling")]
static BOOTSTRAP_COUNT: AtomicUsize = AtomicUsize::new(0);
#[cfg(feature = "clone_profiling")]
static BOOTSTRAP_NANOS: AtomicU64 = AtomicU64::new(0);

note_and_read!(
    note_gumbel_move_ns, gumbel_move_count, gumbel_move_ns, reset_gumbel_move,
    GUMBEL_MOVE_COUNT, GUMBEL_MOVE_NANOS
);
note_and_read!(note_rtv_ns, rtv_count, rtv_ns, reset_rtv, RTV_COUNT, RTV_NANOS);
note_and_read!(
    note_bootstrap_ns, bootstrap_count, bootstrap_ns, reset_bootstrap,
    BOOTSTRAP_COUNT, BOOTSTRAP_NANOS
);

/// Misst `f()` und bucht die Dauer über `note` (z.B. [`note_net_eval_ns`]).
/// No-Op-Timing ohne das Feature (spart die `Instant`-Aufrufe, `f()` läuft
/// trotzdem ganz normal weiter).
#[inline(always)]
pub fn timed<T>(note: fn(u64), f: impl FnOnce() -> T) -> T {
    #[cfg(feature = "clone_profiling")]
    {
        let start = Instant::now();
        let out = f();
        note(start.elapsed().as_nanos() as u64);
        out
    }
    #[cfg(not(feature = "clone_profiling"))]
    {
        let _ = note;
        f()
    }
}

// ── Task #81: Netz-Eval- vs. Spiellogik-Split je Kostenprofil-Kategorie ─────
// Ausgangsfrage (GPU-Umbau, Task #82): welcher Anteil JEDER Task-#80-Kategorie
// (Gumbel-Suche, rtv, Bootstrap) ist Netz-Forward-Pass (wandert auf die GPU)
// vs. reine CPU-Spiellogik (Klonen, Zuggenerierung, Feature-Extraktion, bleibt
// CPU -- setzt die Amdahl-Obergrenze fuer den Batcher)? Ein thread-lokaler
// Kategorie-Marker macht die drei Kategorien fuer JEDEN `Net::eval`/
// `eval_pair`-Aufruf (egal ob direkt in `net_mcts.rs` oder ueber
// `round_transition[_deep].rs`s Alpha-Beta-Zugsortierung erreicht)
// unterscheidbar, ohne jede Aufrufstelle einzeln umbauen zu muessen. Ein
// simpler "aktuelle Kategorie"-Slot wuerde reichen (die drei Kategorien laufen
// je Thread strikt sequenziell, nie verschachtelt) -- ein kleiner Stack ist
// defensiv gegen kuenftige Verschachtelung und kostet ohne das Feature nichts.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Category {
    Gumbel,
    Rtv,
    Bootstrap,
}

#[cfg(feature = "clone_profiling")]
thread_local! {
    static CATEGORY_STACK: std::cell::RefCell<Vec<Category>> = std::cell::RefCell::new(Vec::new());
}

#[cfg(feature = "clone_profiling")]
static GUMBEL_NET_EVAL_NANOS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "clone_profiling")]
static GUMBEL_NET_EVAL_CALLS: AtomicUsize = AtomicUsize::new(0);
#[cfg(feature = "clone_profiling")]
static GUMBEL_NET_EVAL_INSTANCES: AtomicUsize = AtomicUsize::new(0);
#[cfg(feature = "clone_profiling")]
static RTV_NET_EVAL_NANOS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "clone_profiling")]
static RTV_NET_EVAL_CALLS: AtomicUsize = AtomicUsize::new(0);
#[cfg(feature = "clone_profiling")]
static RTV_NET_EVAL_INSTANCES: AtomicUsize = AtomicUsize::new(0);
#[cfg(feature = "clone_profiling")]
static BOOTSTRAP_NET_EVAL_NANOS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "clone_profiling")]
static BOOTSTRAP_NET_EVAL_CALLS: AtomicUsize = AtomicUsize::new(0);
#[cfg(feature = "clone_profiling")]
static BOOTSTRAP_NET_EVAL_INSTANCES: AtomicUsize = AtomicUsize::new(0);

/// Umschliesst `f()` mit dem Kategorie-Marker `_cat` -- alle waehrend `f()`
/// gemessenen `Net::eval`/`eval_pair`-Aufrufe (via [`timed_net_eval`]) werden
/// dieser Kategorie zugerechnet. Aufrufstellen in `self_play.rs` bleiben damit
/// wie bisher (nur eine zusaetzliche Huelle um den bestehenden
/// `timed(note_*_ns, ...)`-Block). Ohne Feature ein reiner Passthrough.
#[inline(always)]
pub fn with_category<T>(_cat: Category, f: impl FnOnce() -> T) -> T {
    #[cfg(feature = "clone_profiling")]
    {
        CATEGORY_STACK.with(|s| s.borrow_mut().push(_cat));
        let out = f();
        CATEGORY_STACK.with(|s| {
            s.borrow_mut().pop();
        });
        out
    }
    #[cfg(not(feature = "clone_profiling"))]
    {
        f()
    }
}

#[cfg(feature = "clone_profiling")]
fn note_net_eval_category(elapsed_ns: u64, batch_size: usize) {
    let cat = CATEGORY_STACK.with(|s| s.borrow().last().copied());
    match cat {
        Some(Category::Gumbel) => {
            GUMBEL_NET_EVAL_NANOS.fetch_add(elapsed_ns, Ordering::Relaxed);
            GUMBEL_NET_EVAL_CALLS.fetch_add(1, Ordering::Relaxed);
            GUMBEL_NET_EVAL_INSTANCES.fetch_add(batch_size, Ordering::Relaxed);
        }
        Some(Category::Rtv) => {
            RTV_NET_EVAL_NANOS.fetch_add(elapsed_ns, Ordering::Relaxed);
            RTV_NET_EVAL_CALLS.fetch_add(1, Ordering::Relaxed);
            RTV_NET_EVAL_INSTANCES.fetch_add(batch_size, Ordering::Relaxed);
        }
        Some(Category::Bootstrap) => {
            BOOTSTRAP_NET_EVAL_NANOS.fetch_add(elapsed_ns, Ordering::Relaxed);
            BOOTSTRAP_NET_EVAL_CALLS.fetch_add(1, Ordering::Relaxed);
            BOOTSTRAP_NET_EVAL_INSTANCES.fetch_add(batch_size, Ordering::Relaxed);
        }
        None => {
            // Ausserhalb jeder Task-#80-Kategorie (z.B. `profiling_snapshot`-
            // unabhaengige Testaufrufe) -- bewusst nicht gezaehlt, der globale
            // `net_eval_ns/count` (oben) bleibt davon unberuehrt korrekt.
        }
    }
}

/// Wie `timed(note_net_eval_ns, f)`, misst zusaetzlich `batch_size` (Anzahl
/// Forward-Pass-Instanzen in diesem Aufruf -- 1 fuer `Net::eval`, 2 fuer
/// `Net::eval_pair`s gebuendelten Mover+Gegner-Pass) und bucht sie in die
/// aktuell aktive [`Category`] (siehe [`with_category`]). Ersetzt an den
/// Netz-Eval-Aufrufstellen `timed(note_net_eval_ns, ...)` 1:1 -- der globale
/// Zaehler (`net_eval_count`/`net_eval_ns`) bleibt unveraendert mitgezaehlt.
#[inline(always)]
pub fn timed_net_eval<T>(_batch_size: usize, f: impl FnOnce() -> T) -> T {
    #[cfg(feature = "clone_profiling")]
    {
        let start = Instant::now();
        let out = f();
        let elapsed = start.elapsed().as_nanos() as u64;
        note_net_eval_ns(elapsed);
        note_net_eval_category(elapsed, _batch_size);
        out
    }
    #[cfg(not(feature = "clone_profiling"))]
    {
        f()
    }
}

macro_rules! category_eval_getters {
    ($ns_fn:ident, $calls_fn:ident, $instances_fn:ident, $reset_fn:ident, $nanos_static:ident, $calls_static:ident, $instances_static:ident) => {
        pub fn $ns_fn() -> u64 {
            #[cfg(feature = "clone_profiling")]
            {
                $nanos_static.load(Ordering::Relaxed)
            }
            #[cfg(not(feature = "clone_profiling"))]
            {
                0
            }
        }
        pub fn $calls_fn() -> usize {
            #[cfg(feature = "clone_profiling")]
            {
                $calls_static.load(Ordering::Relaxed)
            }
            #[cfg(not(feature = "clone_profiling"))]
            {
                0
            }
        }
        pub fn $instances_fn() -> usize {
            #[cfg(feature = "clone_profiling")]
            {
                $instances_static.load(Ordering::Relaxed)
            }
            #[cfg(not(feature = "clone_profiling"))]
            {
                0
            }
        }
        pub fn $reset_fn() {
            #[cfg(feature = "clone_profiling")]
            {
                $nanos_static.store(0, Ordering::Relaxed);
                $calls_static.store(0, Ordering::Relaxed);
                $instances_static.store(0, Ordering::Relaxed);
            }
        }
    };
}

category_eval_getters!(
    gumbel_net_eval_ns, gumbel_net_eval_calls, gumbel_net_eval_instances, reset_gumbel_net_eval,
    GUMBEL_NET_EVAL_NANOS, GUMBEL_NET_EVAL_CALLS, GUMBEL_NET_EVAL_INSTANCES
);
category_eval_getters!(
    rtv_net_eval_ns, rtv_net_eval_calls, rtv_net_eval_instances, reset_rtv_net_eval,
    RTV_NET_EVAL_NANOS, RTV_NET_EVAL_CALLS, RTV_NET_EVAL_INSTANCES
);
category_eval_getters!(
    bootstrap_net_eval_ns, bootstrap_net_eval_calls, bootstrap_net_eval_instances, reset_bootstrap_net_eval,
    BOOTSTRAP_NET_EVAL_NANOS, BOOTSTRAP_NET_EVAL_CALLS, BOOTSTRAP_NET_EVAL_INSTANCES
);

pub fn reset_all() {
    reset_gamestate_clone_count();
    reset_features();
    reset_net_eval();
    reset_dfs_eval();
    reset_gumbel_move();
    reset_rtv();
    reset_bootstrap();
    reset_gumbel_net_eval();
    reset_rtv_net_eval();
    reset_bootstrap_net_eval();
}

// ═══════════════════════════════════════════════════════════════════════════
// Task #32 (`evaluations/STATUS.md` Abschnitt "Task #32", Herleitung
// 2026-08-04): Self-Play-Zeitprofil -- Netz-Zeit ("S", sim-abhängig) vs.
// Nicht-Netz-Zeit ("F", fix) DIREKT gemessen statt aus dem PCR-mild-Sim-
// Verhältnis hochgerechnet (Herleitung: S~42%, F~58%, bisher UNGEPRÜFT).
//
// BEWUSST NICHT an das `clone_profiling`-Feature gekoppelt (anders als der
// Rest dieser Datei oben): dieses Profil soll per Env-Var in einem normalen
// Release-Build einschaltbar sein, ohne Sonder-Kompilierung -- gleiches
// Muster wie `net_mcts.rs`s `MOSAIC_POINTS_UTILITY_W`/`MOSAIC_AGGR_LAMBDA`
// (`OnceLock`-gecachter Einmal-Lese-Zugriff, danach reines `AtomicU64`-Laden,
// kein Reparsen pro Aufruf). Bei `MOSAIC_PROFILE_SELFPLAY` NICHT gesetzt
// (Normalbetrieb): jeder Messpunkt ist ein einzelner `if !enabled { return
// f() }`-Vergleich OHNE `Instant::now()` -- praktisch kostenlos.
//
// KATEGORISIERUNGS-REGEL (hier bewusst dokumentiert, siehe Auftragstext):
// Die fünf Basiskategorien ÜBERLAPPEN -- keine disjunkte Zerlegung der
// Wandzeit:
//   - `NetInference`    : JEDER `Net::eval*`-Aufruf (`eval`, `eval_pair`,
//                         `eval_batch`, `eval_ex`, `eval_pair_ex`,
//                         `eval_batch_ex`) -- instrumentiert DIREKT in den
//                         Methodenkörpern (`net.rs`), nicht an den
//                         Aufrufstellen, damit KEIN Call-Site vergessen
//                         werden kann (Task #80/#81s `timed_net_eval`-Wrapper
//                         deckt zwar die meisten Stellen in `net_mcts.rs`/
//                         `self_play.rs` ab, aber nicht alle -- z.B. `lib.rs`,
//                         `py.rs`, `self_play.rs::negamax_value`s
//                         `eval`-Aufruf).
//   - `Round5Alphabeta` : `round5::choose_action_with_analysis`, GANZER
//                         Funktionskörper (einziger sinnvoller
//                         Haupteinstiegspunkt, alle Aufrufer -- `mcts.rs`,
//                         `net_mcts.rs` -- automatisch mit abgedeckt).
//   - `TilingSolver`    : `tiling_solver::solve_round_final_score` UND
//                         `solve_round_final_score_endaware`, GANZER
//                         Funktionskörper (Haupteinstiegspunkte, KEINE
//                         Rekursion einzeln gezählt -- `solve_rec`/
//                         `solve_rec_endaware` bleiben uninstrumentiert).
//   - `BootstrapValue`  : `round_transition_deep::bootstrap_value_after_rounds`,
//                         GANZER Funktionskörper.
//   - `TotalSelfplay`   : EIN Aufruf von `play_net_self_play_game` (die
//                         Spielschleife je Partie, `self_play.rs::
//                         run_net_self_play`s `play`-Closure).
//
// Codegeprüft (2026-08-04): `round5.rs` ruft NIRGENDS `Net::eval*` auf (reine
// exakte Suche, Modulkommentar "Full-Information-Endspiel") -- ruft aber
// INTERN `tiling_solver::solve_round_final_score_endaware` an JEDEM
// Alpha-Beta-Blatt auf (`round5.rs::player_total_exact`). Umgekehrt ruft
// `bootstrap_value_after_rounds` INTERN `Net::eval*` auf (`net_leaf_eval`/
// `drafting_action_priors` über `simulate_one_round`), aber NIE
// `tiling_solver` (dessen interne Zugsortierung nutzt Netz-Prioren, keine
// Tiling-Lösung). Die Überlappung ist also NICHT symmetrisch -- statt vier
// Zusatzzähler (ein Netz- UND ein Tiling-Zähler je Kontext) genügen drei:
//   - `tiling_solver_inside_round5_ns`   (Teilmenge von `tiling_solver` UND
//                                         von `round5_alphabeta`)
//   - `net_inference_inside_bootstrap_ns`(Teilmenge von `net_inference` UND
//                                         von `bootstrap_value`)
//   - `net_inference_inside_round5_ns`   zusätzlich mitgeführt, obwohl nach
//                                         aktuellem Code IMMER 0 erwartet --
//                                         billiger, ihn defensiv mitzuzählen,
//                                         als das Modul bei der nächsten
//                                         round5.rs-Änderung (die einen
//                                         Netz-Aufruf einführen könnte)
//                                         stillschweigend falsch zu machen.
// (`tiling_solver_inside_bootstrap_ns` fehlt bewusst -- nach obiger Analyse
// gibt es dort keinen Tiling-Aufruf, ein Zähler dafür bliebe für immer 0 und
// würde nur Verwirrung stiften.)
//
// Für die Auswertung folgt daraus:
//   round5_bookkeeping_ns = round5_alphabeta_ns
//                          - tiling_solver_inside_round5_ns
//                          - net_inference_inside_round5_ns
//   bootstrap_nonnet_ns   = bootstrap_value_ns - net_inference_inside_bootstrap_ns
// (beide bereits vorgerechnet in `selfplay_profile::snapshot_json`).
//
// AUSSERHALB von `Round5Alphabeta`/`BootstrapValue` gemessene `NetInference`/
// `TilingSolver`-Zeit (Gumbel-Zugsuche, rtv-Sampling, Stage-1-DFS-Blatt via
// `mcts.rs::player_total` usw.) ist HIER nicht weiter aufgeschlüsselt -- dafür
// existiert bereits die feature-gegatete Task-#80/#81-Aufteilung weiter oben
// in dieser Datei (`Category::{Gumbel,Rtv,Bootstrap}` + `timed_net_eval`),
// mit einem ANDEREN Zweck (Netz- vs. Spiellogik-Split je Gumbel/rtv/
// Bootstrap-Phase für den GPU-Batcher) und eigenem Env-/Feature-Gate.
pub mod selfplay_profile {
    use std::cell::RefCell;
    use std::sync::atomic::{AtomicU64, Ordering};
    use std::sync::OnceLock;
    use std::time::Instant;

    /// Die fünf überlappenden Basiskategorien (siehe Modulkopf-Doku oben).
    #[derive(Clone, Copy, PartialEq, Eq, Debug)]
    pub enum SelfplayCat {
        NetInference,
        Round5Alphabeta,
        TilingSolver,
        BootstrapValue,
        TotalSelfplay,
    }

    /// Kontext für die thread-lokale Verschachtelungs-Erkennung (siehe
    /// `timed_with_enabled`) -- NUR die zwei Kategorien, die dokumentiert
    /// andere Kategorien intern aufrufen, brauchen einen Kontext-Eintrag.
    #[derive(Clone, Copy, PartialEq, Eq, Debug)]
    enum SelfplayContext {
        Round5,
        Bootstrap,
    }

    thread_local! {
        static CONTEXT_STACK: RefCell<Vec<SelfplayContext>> = RefCell::new(Vec::new());
    }

    fn context_contains(ctx: SelfplayContext) -> bool {
        CONTEXT_STACK.with(|s| s.borrow().iter().any(|c| *c == ctx))
    }

    static NET_INFERENCE_NS: AtomicU64 = AtomicU64::new(0);
    static NET_INFERENCE_CALLS: AtomicU64 = AtomicU64::new(0);
    static ROUND5_ALPHABETA_NS: AtomicU64 = AtomicU64::new(0);
    static ROUND5_ALPHABETA_CALLS: AtomicU64 = AtomicU64::new(0);
    static TILING_SOLVER_NS: AtomicU64 = AtomicU64::new(0);
    static TILING_SOLVER_CALLS: AtomicU64 = AtomicU64::new(0);
    static BOOTSTRAP_VALUE_NS: AtomicU64 = AtomicU64::new(0);
    static BOOTSTRAP_VALUE_CALLS: AtomicU64 = AtomicU64::new(0);
    static TOTAL_SELFPLAY_NS: AtomicU64 = AtomicU64::new(0);
    static TOTAL_SELFPLAY_CALLS: AtomicU64 = AtomicU64::new(0);

    // Zusatzzähler für die dokumentierte Überschneidung (siehe Modulkopf).
    static TILING_SOLVER_INSIDE_ROUND5_NS: AtomicU64 = AtomicU64::new(0);
    static NET_INFERENCE_INSIDE_ROUND5_NS: AtomicU64 = AtomicU64::new(0);
    static NET_INFERENCE_INSIDE_BOOTSTRAP_NS: AtomicU64 = AtomicU64::new(0);

    fn add_base_counter(cat: SelfplayCat, elapsed_ns: u64) {
        let (ns, calls): (&'static AtomicU64, &'static AtomicU64) = match cat {
            SelfplayCat::NetInference => (&NET_INFERENCE_NS, &NET_INFERENCE_CALLS),
            SelfplayCat::Round5Alphabeta => (&ROUND5_ALPHABETA_NS, &ROUND5_ALPHABETA_CALLS),
            SelfplayCat::TilingSolver => (&TILING_SOLVER_NS, &TILING_SOLVER_CALLS),
            SelfplayCat::BootstrapValue => (&BOOTSTRAP_VALUE_NS, &BOOTSTRAP_VALUE_CALLS),
            SelfplayCat::TotalSelfplay => (&TOTAL_SELFPLAY_NS, &TOTAL_SELFPLAY_CALLS),
        };
        ns.fetch_add(elapsed_ns, Ordering::Relaxed);
        calls.fetch_add(1, Ordering::Relaxed);
    }

    /// Reines Env-Wert-Parsing (kein Env-Zugriff selbst) -- direkt testbar
    /// ohne den Prozess-weiten `OnceLock`-Cache zu berühren. NUR der exakte
    /// String `"1"` (nach `trim()`) aktiviert das Profil; alles andere
    /// (fehlend, leer, `"0"`, `"true"`, ...) bleibt aus -- bewusst strikt,
    /// analog zu anderen `MOSAIC_*`-Schaltern im Projekt, die lieber
    /// eindeutig aus bleiben als bei einem Tippfehler still ein unerwartetes
    /// Verhalten anzunehmen.
    fn parse_profile_enabled(raw: Option<&str>) -> bool {
        matches!(raw.map(|s| s.trim()), Some("1"))
    }

    static SELFPLAY_PROFILE_ENABLED: OnceLock<bool> = OnceLock::new();

    /// Liest `MOSAIC_PROFILE_SELFPLAY` EINMALIG (Prozessstart-Cache, gleiches
    /// Muster wie `net_mcts.rs::points_utility_w_cell`) -- kein Reparsen pro
    /// Messpunkt.
    pub fn selfplay_profile_enabled() -> bool {
        *SELFPLAY_PROFILE_ENABLED
            .get_or_init(|| parse_profile_enabled(std::env::var("MOSAIC_PROFILE_SELFPLAY").ok().as_deref()))
    }

    /// Kernlogik von [`timed`], mit explizitem `enabled`-Parameter statt des
    /// Prozess-weiten Env-Caches -- direkt testbar (siehe `tests` unten),
    /// ohne dass Tests den `MOSAIC_PROFILE_SELFPLAY`-`OnceLock` (der sich nach
    /// dem ersten Zugriff nie mehr ändert) beeinflussen müssten.
    fn timed_with_enabled<T>(enabled: bool, cat: SelfplayCat, f: impl FnOnce() -> T) -> T {
        if !enabled {
            // Kein `Instant::now()` im Aus-Zustand -- siehe Modulkopf-Doku.
            return f();
        }
        let push_ctx = match cat {
            SelfplayCat::Round5Alphabeta => Some(SelfplayContext::Round5),
            SelfplayCat::BootstrapValue => Some(SelfplayContext::Bootstrap),
            _ => None,
        };
        if let Some(ctx) = push_ctx {
            CONTEXT_STACK.with(|s| s.borrow_mut().push(ctx));
        }
        let start = Instant::now();
        let out = f();
        let elapsed_ns = start.elapsed().as_nanos() as u64;
        if push_ctx.is_some() {
            CONTEXT_STACK.with(|s| {
                s.borrow_mut().pop();
            });
        }
        add_base_counter(cat, elapsed_ns);
        match cat {
            SelfplayCat::NetInference => {
                if context_contains(SelfplayContext::Round5) {
                    NET_INFERENCE_INSIDE_ROUND5_NS.fetch_add(elapsed_ns, Ordering::Relaxed);
                }
                if context_contains(SelfplayContext::Bootstrap) {
                    NET_INFERENCE_INSIDE_BOOTSTRAP_NS.fetch_add(elapsed_ns, Ordering::Relaxed);
                }
            }
            SelfplayCat::TilingSolver => {
                if context_contains(SelfplayContext::Round5) {
                    TILING_SOLVER_INSIDE_ROUND5_NS.fetch_add(elapsed_ns, Ordering::Relaxed);
                }
            }
            _ => {}
        }
        out
    }

    /// Misst `f()` und bucht die Dauer in die Basiskategorie `cat` (plus ggf.
    /// die dokumentierten Zusatzzähler, siehe Modulkopf) -- NUR wenn
    /// `MOSAIC_PROFILE_SELFPLAY=1` gesetzt ist, sonst ein reiner Passthrough
    /// ohne Zeitmessung. Einzige Aufrufstellen: die Methodenkörper von
    /// `Net::eval*` (`net.rs`), `round5::choose_action_with_analysis`,
    /// `tiling_solver::solve_round_final_score[_endaware]`,
    /// `round_transition_deep::bootstrap_value_after_rounds` und der
    /// `play_net_self_play_game`-Aufruf in `self_play.rs::run_net_self_play`.
    pub fn timed<T>(cat: SelfplayCat, f: impl FnOnce() -> T) -> T {
        timed_with_enabled(selfplay_profile_enabled(), cat, f)
    }

    pub fn net_inference_ns() -> u64 {
        NET_INFERENCE_NS.load(Ordering::Relaxed)
    }
    pub fn net_inference_calls() -> u64 {
        NET_INFERENCE_CALLS.load(Ordering::Relaxed)
    }
    pub fn round5_alphabeta_ns() -> u64 {
        ROUND5_ALPHABETA_NS.load(Ordering::Relaxed)
    }
    pub fn round5_alphabeta_calls() -> u64 {
        ROUND5_ALPHABETA_CALLS.load(Ordering::Relaxed)
    }
    pub fn tiling_solver_ns() -> u64 {
        TILING_SOLVER_NS.load(Ordering::Relaxed)
    }
    pub fn tiling_solver_calls() -> u64 {
        TILING_SOLVER_CALLS.load(Ordering::Relaxed)
    }
    pub fn bootstrap_value_ns() -> u64 {
        BOOTSTRAP_VALUE_NS.load(Ordering::Relaxed)
    }
    pub fn bootstrap_value_calls() -> u64 {
        BOOTSTRAP_VALUE_CALLS.load(Ordering::Relaxed)
    }
    pub fn total_selfplay_ns() -> u64 {
        TOTAL_SELFPLAY_NS.load(Ordering::Relaxed)
    }
    pub fn total_selfplay_calls() -> u64 {
        TOTAL_SELFPLAY_CALLS.load(Ordering::Relaxed)
    }
    pub fn tiling_solver_inside_round5_ns() -> u64 {
        TILING_SOLVER_INSIDE_ROUND5_NS.load(Ordering::Relaxed)
    }
    pub fn net_inference_inside_round5_ns() -> u64 {
        NET_INFERENCE_INSIDE_ROUND5_NS.load(Ordering::Relaxed)
    }
    pub fn net_inference_inside_bootstrap_ns() -> u64 {
        NET_INFERENCE_INSIDE_BOOTSTRAP_NS.load(Ordering::Relaxed)
    }

    /// Setzt ALLE Task-#32-Zähler zurück (PyO3-Bindung `selfplay_profile_reset`
    /// in `lib.rs`) -- vor einem zu profilierenden Self-Play-Lauf aufrufen.
    pub fn reset() {
        NET_INFERENCE_NS.store(0, Ordering::Relaxed);
        NET_INFERENCE_CALLS.store(0, Ordering::Relaxed);
        ROUND5_ALPHABETA_NS.store(0, Ordering::Relaxed);
        ROUND5_ALPHABETA_CALLS.store(0, Ordering::Relaxed);
        TILING_SOLVER_NS.store(0, Ordering::Relaxed);
        TILING_SOLVER_CALLS.store(0, Ordering::Relaxed);
        BOOTSTRAP_VALUE_NS.store(0, Ordering::Relaxed);
        BOOTSTRAP_VALUE_CALLS.store(0, Ordering::Relaxed);
        TOTAL_SELFPLAY_NS.store(0, Ordering::Relaxed);
        TOTAL_SELFPLAY_CALLS.store(0, Ordering::Relaxed);
        TILING_SOLVER_INSIDE_ROUND5_NS.store(0, Ordering::Relaxed);
        NET_INFERENCE_INSIDE_ROUND5_NS.store(0, Ordering::Relaxed);
        NET_INFERENCE_INSIDE_BOOTSTRAP_NS.store(0, Ordering::Relaxed);
    }

    /// Baut den vollständigen JSON-Snapshot (PyO3-Bindung `selfplay_profile_json`
    /// in `lib.rs`) -- alle Rohzähler in Nanosekunden/Aufrufen PLUS
    /// Prozentwerte relativ zu `total_selfplay_ns` PLUS die zwei
    /// vorgerechneten, überschneidungsfreien Restgrößen (siehe Modulkopf-
    /// Doku: `round5_bookkeeping_ns`, `bootstrap_nonnet_ns`). `enabled`
    /// steht mit im Snapshot, damit ein Aufrufer einen leeren (weil nie
    /// eingeschalteten) Snapshot nicht mit "keine Zeit gemessen" verwechselt.
    pub fn snapshot_json() -> String {
        let total_ns = total_selfplay_ns();
        let pct = |ns: u64| -> f64 {
            if total_ns == 0 {
                0.0
            } else {
                (ns as f64 / total_ns as f64) * 100.0
            }
        };
        let round5_ns = round5_alphabeta_ns();
        let tiling_in_round5 = tiling_solver_inside_round5_ns();
        let net_in_round5 = net_inference_inside_round5_ns();
        let bootstrap_ns = bootstrap_value_ns();
        let net_in_bootstrap = net_inference_inside_bootstrap_ns();
        serde_json::json!({
            "enabled": selfplay_profile_enabled(),
            "note": "Kategorien UEBERLAPPEN (siehe profiling.rs-Modulkopf-Doku \
                      'Task #32'): round5_alphabeta enthaelt tiling_solver_inside_round5_ns \
                      (+ net_inference_inside_round5_ns, erwartet 0), bootstrap_value \
                      enthaelt net_inference_inside_bootstrap_ns. Die *_pct_of_total-Werte \
                      beziehen sich alle auf total_selfplay_ns und summieren sich DESHALB \
                      NICHT auf 100%.",
            "total_selfplay_ns": total_ns,
            "total_selfplay_calls": total_selfplay_calls(),
            "net_inference_ns": net_inference_ns(),
            "net_inference_calls": net_inference_calls(),
            "net_inference_pct_of_total": pct(net_inference_ns()),
            "round5_alphabeta_ns": round5_ns,
            "round5_alphabeta_calls": round5_alphabeta_calls(),
            "round5_alphabeta_pct_of_total": pct(round5_ns),
            "tiling_solver_ns": tiling_solver_ns(),
            "tiling_solver_calls": tiling_solver_calls(),
            "tiling_solver_pct_of_total": pct(tiling_solver_ns()),
            "bootstrap_value_ns": bootstrap_ns,
            "bootstrap_value_calls": bootstrap_value_calls(),
            "bootstrap_value_pct_of_total": pct(bootstrap_ns),
            "tiling_solver_inside_round5_ns": tiling_in_round5,
            "net_inference_inside_round5_ns": net_in_round5,
            "net_inference_inside_bootstrap_ns": net_in_bootstrap,
            "round5_bookkeeping_ns": round5_ns.saturating_sub(tiling_in_round5).saturating_sub(net_in_round5),
            "bootstrap_nonnet_ns": bootstrap_ns.saturating_sub(net_in_bootstrap),
        })
        .to_string()
    }

    #[cfg(test)]
    mod tests {
        use super::*;
        use std::sync::Mutex;
        use std::time::Duration;

        // Alle Tests hier schreiben auf dieselben Prozess-weiten Atomics
        // (bewusst -- das IST der Gegenstand des Tests, anders als z.B.
        // `read_f64_env`s Tests in `net_mcts.rs`, die synthetische Var-Namen
        // je Test verwenden). Ein Mutex serialisiert wenigstens diese
        // Testgruppe untereinander (gleiches Kompromiss-Muster wie
        // `net_mcts.rs::AGGRESSION_TEST_LOCK` -- volle Isolation gegenüber
        // ALLEN anderen `cargo test`-Threads bräuchte `--test-threads=1`).
        static TEST_LOCK: Mutex<()> = Mutex::new(());

        fn busy_wait_at_least_1ms() {
            // `thread::sleep` reicht als Mindest-Verzögerung, damit
            // `elapsed_ns` garantiert > 0 ist (auch auf grob aufgelösten
            // Timern) -- die Tests brauchen keine genaue Dauer, nur "> 0".
            std::thread::sleep(Duration::from_millis(1));
        }

        #[test]
        fn parse_profile_enabled_only_accepts_exact_one() {
            assert!(!parse_profile_enabled(None));
            assert!(!parse_profile_enabled(Some("")));
            assert!(!parse_profile_enabled(Some("0")));
            assert!(!parse_profile_enabled(Some("true")));
            assert!(!parse_profile_enabled(Some("2")));
            assert!(parse_profile_enabled(Some("1")));
            assert!(parse_profile_enabled(Some(" 1 ")), "trim() muss umgebende Whitespace tolerieren");
        }

        #[test]
        fn disabled_flag_leaves_all_counters_at_zero() {
            let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
            reset();
            let out = timed_with_enabled(false, SelfplayCat::TotalSelfplay, || {
                busy_wait_at_least_1ms();
                42
            });
            assert_eq!(out, 42, "f() muss trotzdem ganz normal ausgefuehrt und ihr Ergebnis geliefert werden");
            assert_eq!(total_selfplay_ns(), 0);
            assert_eq!(total_selfplay_calls(), 0);
            reset();
        }

        #[test]
        fn enabled_flag_accumulates_into_the_matching_base_counter() {
            let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
            reset();
            timed_with_enabled(true, SelfplayCat::NetInference, busy_wait_at_least_1ms);
            assert!(net_inference_ns() > 0);
            assert_eq!(net_inference_calls(), 1);
            assert_eq!(round5_alphabeta_ns(), 0, "andere Basiskategorien duerfen unberuehrt bleiben");
            reset();
        }

        #[test]
        fn reset_zeroes_every_counter_including_the_overlap_extras() {
            let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
            reset();
            timed_with_enabled(true, SelfplayCat::Round5Alphabeta, || {
                timed_with_enabled(true, SelfplayCat::TilingSolver, busy_wait_at_least_1ms);
            });
            assert!(round5_alphabeta_ns() > 0);
            assert!(tiling_solver_inside_round5_ns() > 0);
            reset();
            assert_eq!(net_inference_ns(), 0);
            assert_eq!(round5_alphabeta_ns(), 0);
            assert_eq!(tiling_solver_ns(), 0);
            assert_eq!(bootstrap_value_ns(), 0);
            assert_eq!(total_selfplay_ns(), 0);
            assert_eq!(tiling_solver_inside_round5_ns(), 0);
            assert_eq!(net_inference_inside_round5_ns(), 0);
            assert_eq!(net_inference_inside_bootstrap_ns(), 0);
        }

        /// Kern-Nachweis der dokumentierten Kategorisierungs-Regel: ein
        /// `TilingSolver`-Aufruf VERSCHACHTELT innerhalb `Round5Alphabeta`
        /// zählt in BEIDE Basiskategorien UND zusätzlich in
        /// `tiling_solver_inside_round5_ns`.
        #[test]
        fn tiling_solver_nested_in_round5_is_counted_in_both_plus_the_overlap_extra() {
            let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
            reset();
            timed_with_enabled(true, SelfplayCat::Round5Alphabeta, || {
                timed_with_enabled(true, SelfplayCat::TilingSolver, busy_wait_at_least_1ms);
            });
            assert!(round5_alphabeta_ns() > 0, "aeussere Kategorie muss die GESAMTE Spanne zaehlen");
            assert!(tiling_solver_ns() > 0, "innere Basiskategorie bleibt unabhaengig davon vorhanden");
            assert!(
                tiling_solver_inside_round5_ns() > 0,
                "Ueberschneidungs-Zusatzzaehler muss die verschachtelte Zeit sehen"
            );
            assert!(
                tiling_solver_inside_round5_ns() <= round5_alphabeta_ns(),
                "die Teilmenge darf die Gesamtspanne nicht uebersteigen"
            );
            // Die NICHT dokumentierte Kombination (Tiling in Bootstrap) bleibt
            // bei 0 -- kein Zaehler dafuer vorgesehen (siehe Modulkopf).
            assert_eq!(net_inference_inside_bootstrap_ns(), 0);
            reset();
        }

        /// Symmetrischer Nachweis für `BootstrapValue`/`NetInference`.
        #[test]
        fn net_inference_nested_in_bootstrap_is_counted_in_both_plus_the_overlap_extra() {
            let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
            reset();
            timed_with_enabled(true, SelfplayCat::BootstrapValue, || {
                timed_with_enabled(true, SelfplayCat::NetInference, busy_wait_at_least_1ms);
            });
            assert!(bootstrap_value_ns() > 0);
            assert!(net_inference_ns() > 0);
            assert!(net_inference_inside_bootstrap_ns() > 0);
            assert!(net_inference_inside_bootstrap_ns() <= bootstrap_value_ns());
            assert_eq!(
                net_inference_inside_round5_ns(),
                0,
                "Bootstrap-Kontext darf den Round5-Zusatzzaehler nicht beeinflussen"
            );
            reset();
        }

        /// Zwei Basiskategorien-Aufrufe NACHEINANDER (nicht verschachtelt)
        /// duerfen sich nicht gegenseitig in die Ueberschneidungs-Zusatzzaehler
        /// einmischen.
        #[test]
        fn sequential_non_nested_calls_do_not_pollute_overlap_extras() {
            let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
            reset();
            timed_with_enabled(true, SelfplayCat::Round5Alphabeta, busy_wait_at_least_1ms);
            timed_with_enabled(true, SelfplayCat::NetInference, busy_wait_at_least_1ms);
            assert_eq!(
                net_inference_inside_round5_ns(),
                0,
                "Round5 und NetInference liefen NACHEINANDER, nicht verschachtelt"
            );
            reset();
        }

        #[test]
        fn snapshot_json_is_well_formed_and_carries_the_enabled_flag() {
            let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
            reset();
            let raw = snapshot_json();
            let parsed: serde_json::Value = serde_json::from_str(&raw).expect("gueltiges JSON");
            assert!(parsed.get("enabled").is_some());
            assert!(parsed.get("total_selfplay_ns").is_some());
            assert!(parsed.get("round5_bookkeeping_ns").is_some());
            assert!(parsed.get("bootstrap_nonnet_ns").is_some());
        }
    }
}
