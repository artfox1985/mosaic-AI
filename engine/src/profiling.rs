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
