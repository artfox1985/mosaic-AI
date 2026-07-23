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

pub fn reset_all() {
    reset_gamestate_clone_count();
    reset_features();
    reset_net_eval();
    reset_dfs_eval();
    reset_gumbel_move();
    reset_rtv();
    reset_bootstrap();
}
