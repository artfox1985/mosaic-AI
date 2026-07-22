//! Mosaic-AI Rust-Kern (Engine + MCTS + Self-Play), via PyO3 nach Python exportiert.
//!
//! Stand: Toolchain-Gerüst. Vorerst nur Smoke-Test-Funktionen; Engine/MCTS/Self-Play
//! folgen schrittweise (siehe Plan: Phase 2–4).

use pyo3::prelude::*;
use serde_json::json;

// Reiner Rust-Kern (PyO3-frei, mit `cargo test` testbar).
pub mod board;
pub mod dome;
pub mod execution;
pub mod factory;
pub mod features;
pub mod game;
pub mod mcts;
pub mod moves;
pub mod net;
pub mod net_mcts;
pub mod profiling;
pub mod py;
pub mod round5;
pub mod round_end;
pub mod round_transition;
pub mod round_transition_deep;
pub mod scoring;
pub mod search_common;
pub mod self_play;
pub mod serialize;
pub mod state;
pub mod supply;
pub mod tiling_solver;
pub mod tile;
pub mod validation;

/// Version des Rust-Kerns (CARGO_PKG_VERSION) — für den Import-Smoke-Test.
#[pyfunction]
fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

/// Trivialer Round-Trip-Test: prüft, dass Python ↔ Rust Argumente/Rückgaben durchreicht.
#[pyfunction]
fn ping(x: i64) -> i64 {
    x + 1
}

/// Self-Play-Datengeneration (MCTS-Modus) komplett in Rust.
///
/// Spielt `n_games` Partien rayon-parallel (GIL freigegeben) und liefert ALLE
/// Step-Records flach als JSON-Array-String zurück (Python: `json.loads`).
/// `num_threads=0` nutzt alle Kerne. Jeder Step folgt dem `self_play.py`-Format.
#[pyfunction]
#[pyo3(signature = (n_games, base_sims=300, c=0.3, seed=None, num_threads=0, prefix="vrust".to_string()))]
fn self_play_games(
    py: Python<'_>,
    n_games: usize,
    base_sims: u32,
    c: f64,
    seed: Option<u64>,
    num_threads: usize,
    prefix: String,
) -> String {
    let seed = seed.unwrap_or_else(rand::random);
    py.detach(move || {
        crate::self_play::run_self_play(n_games, base_sims, c, seed, num_threads, &prefix)
    })
}

/// Wie `self_play_games`, aber zusätzlich mit `round_transition_value`-
/// Labels aus einem geladenen Netz (siehe `self_play::play_one_game`s
/// `net`-Parameter): Spielentscheidungen bleiben VOLLSTÄNDIG heuristisch,
/// nur die vier Rundenübergänge werden zusätzlich per Netz-Chance-Node-
/// Sampling (`round_transition.rs`/`round_transition_deep.rs`) bewertet --
/// lässt den Value-Head vom rauschärmeren Ziel profitieren, ohne dass das
/// Netz je eine Spielentscheidung trifft.
#[pyfunction]
#[pyo3(signature = (model_path, n_games, base_sims=300, c=0.3, seed=None, num_threads=0, prefix="vrust_netlabel".to_string()))]
#[allow(clippy::too_many_arguments)]
fn self_play_games_with_net_labels(
    py: Python<'_>,
    model_path: String,
    n_games: usize,
    base_sims: u32,
    c: f64,
    seed: Option<u64>,
    num_threads: usize,
    prefix: String,
) -> PyResult<String> {
    let seed = seed.unwrap_or_else(rand::random);
    py.detach(move || {
        crate::self_play::run_self_play_with_net_labels(
            &model_path, n_games, base_sims, c, seed, num_threads, &prefix,
        )
    })
    .map_err(pyo3::exceptions::PyValueError::new_err)
}

/// Arena-Match (Heuristik-MCTS vs. Heuristik-MCTS) komplett in Rust.
///
/// Spielt `n_games` Partien rayon-parallel (GIL freigegeben): Brett 0 nutzt
/// `sims_a`, Brett 1 `sims_b`; Startspieler alternierend. Gibt ein geordnetes
/// JSON-Array `[{scores, winner, steps, total_floor, floor_per_round}, …]`
/// zurück (Elo/Statistik rechnet Python). `num_threads=0` = alle Kerne.
#[pyfunction]
#[pyo3(signature = (sims_a, sims_b, n_games, seed=None, num_threads=0, c=0.3))]
fn arena_match(
    py: Python<'_>,
    sims_a: u32,
    sims_b: u32,
    n_games: usize,
    seed: Option<u64>,
    num_threads: usize,
    c: f64,
) -> String {
    let seed = seed.unwrap_or_else(rand::random);
    py.detach(move || crate::self_play::run_arena_match(sims_a, sims_b, n_games, seed, num_threads, c))
}

/// Geschwister-Ranking-Diagnose (siehe `self_play::sibling_ranking_diagnostic`
/// fuer die volle Begruendung): Kendall-Tau zwischen trainiertem Netz-Value
/// und exaktem DFS-Solver ueber Geschwister-Nachfolgezustaende, aggregiert
/// nach Runde 1/2. Gibt JSON `{"round_1": {...}, "round_2": {...}}` zurueck.
#[pyfunction]
#[pyo3(signature = (model_path, n_states_per_round=100, max_children=20, walk_sims=80, seed=None))]
fn sibling_ranking_diagnostic(
    py: Python<'_>,
    model_path: String,
    n_states_per_round: usize,
    max_children: usize,
    walk_sims: u32,
    seed: Option<u64>,
) -> PyResult<String> {
    let seed = seed.unwrap_or_else(rand::random);
    py.detach(move || {
        crate::self_play::sibling_ranking_diagnostic(&model_path, n_states_per_round, max_children, walk_sims, seed)
    })
    .map_err(pyo3::exceptions::PyValueError::new_err)
}

/// Bindungs-Check fuer Fund 6 (siehe `self_play::draw_stack_peek_impact_
/// diagnostic`): Peek-Haeufigkeit + Netz-Wertspanne ueber alle moeglichen
/// Plattenidentitaeten, aggregiert nach Runde.
#[pyfunction]
#[pyo3(signature = (model_path, n_games=30, walk_sims=80, seed=None))]
fn draw_stack_peek_impact_diagnostic(
    py: Python<'_>,
    model_path: String,
    n_games: usize,
    walk_sims: u32,
    seed: Option<u64>,
) -> PyResult<String> {
    let seed = seed.unwrap_or_else(rand::random);
    py.detach(move || crate::self_play::draw_stack_peek_impact_diagnostic(&model_path, n_games, walk_sims, seed))
        .map_err(pyo3::exceptions::PyValueError::new_err)
}

/// Noise-Floor-Test für eine beliebige Runde (siehe
/// `self_play::value_noise_floor_diagnostic`, `evaluations/value head
/// tests.txt` Punkt 1): braucht KEIN Netz -- reine Heuristik-Rollout-
/// Varianzzerlegung des Value-Ziels selbst. `target_round` wählt die Runde
/// (Standard 1, auch 2/3 für die Runde-für-Runde-Einordnung sinnvoll).
#[pyfunction]
#[pyo3(signature = (n_states=300, k_rollouts=10, walk_sims=80, rollout_sims=60, target_round=1, seed=None))]
#[allow(clippy::too_many_arguments)]
fn value_noise_floor_diagnostic(
    py: Python<'_>,
    n_states: usize,
    k_rollouts: usize,
    walk_sims: u32,
    rollout_sims: u32,
    target_round: u32,
    seed: Option<u64>,
) -> PyResult<String> {
    let seed = seed.unwrap_or_else(rand::random);
    py.detach(move || {
        crate::self_play::value_noise_floor_diagnostic(
            n_states,
            k_rollouts,
            walk_sims,
            rollout_sims,
            target_round,
            seed,
        )
    })
    .map_err(pyo3::exceptions::PyValueError::new_err)
}

/// Arena-Match Netz vs. Heuristik-MCTS (Netz auf Brett 0). Lädt das ONNX-Netz
/// einmal, spielt `n_games` (Startspieler alternierend) und gibt ein JSON-Array
/// `[{scores:[netz,heur], winner, steps, total_floor, floor_per_round}]` zurück.
#[pyfunction]
#[pyo3(signature = (model_path, net_sims=100, heur_sims=100, n_games=50, seed=None, num_threads=1, c=0.3, c_puct=1.5))]
#[allow(clippy::too_many_arguments)]
fn net_arena_match(
    py: Python<'_>,
    model_path: String,
    net_sims: u32,
    heur_sims: u32,
    n_games: usize,
    seed: Option<u64>,
    num_threads: usize,
    c: f64,
    c_puct: f64,
) -> PyResult<String> {
    let seed = seed.unwrap_or_else(rand::random);
    py.detach(move || {
        crate::self_play::run_net_arena_match(
            &model_path, net_sims, heur_sims, n_games, seed, num_threads, c, c_puct,
        )
    })
    .map_err(pyo3::exceptions::PyValueError::new_err)
}

/// Arena-Match Netz A (Brett 0) vs. Netz B (Brett 1). Lädt beide ONNX-Netze,
/// spielt `n_games` (Startspieler alternierend) und gibt ein JSON-Array
/// `[{scores:[A,B], winner, steps, total_floor, floor_per_round}]` zurück.
#[pyfunction]
#[pyo3(signature = (model_a, model_b, sims_a=200, sims_b=200, n_games=50, seed=None, num_threads=1, c_puct_a=1.5, c_puct_b=1.5))]
#[allow(clippy::too_many_arguments)]
fn net_vs_net_arena_match(
    py: Python<'_>,
    model_a: String,
    model_b: String,
    sims_a: u32,
    sims_b: u32,
    n_games: usize,
    seed: Option<u64>,
    num_threads: usize,
    c_puct_a: f64,
    c_puct_b: f64,
) -> PyResult<String> {
    let seed = seed.unwrap_or_else(rand::random);
    py.detach(move || {
        crate::self_play::run_net_vs_net_arena(
            &model_a, &model_b, sims_a, sims_b, n_games, seed, num_threads, c_puct_a, c_puct_b,
        )
    })
    .map_err(pyo3::exceptions::PyValueError::new_err)
}

/// Netzgeführtes Self-Play (AlphaZero-Loop, Stufe 1: DFS-Blatt, saubere
/// Visit-Targets). Gibt alle Step-Records als JSON-Array zurück (Format wie
/// self_play_games). `num_threads=0` = alle Kerne.
#[pyfunction]
#[pyo3(signature = (model_path, n_games, base_sims=400, c_puct=1.5, seed=None, num_threads=0, prefix="netgen".to_string(), add_root_noise=true, deterministic=false))]
#[allow(clippy::too_many_arguments)]
fn net_self_play_games(
    py: Python<'_>,
    model_path: String,
    n_games: usize,
    base_sims: u32,
    c_puct: f64,
    seed: Option<u64>,
    num_threads: usize,
    prefix: String,
    add_root_noise: bool,
    deterministic: bool,
) -> PyResult<String> {
    let seed = seed.unwrap_or_else(rand::random);
    py.detach(move || {
        crate::self_play::run_net_self_play(
            &model_path, n_games, base_sims, c_puct, seed, num_threads, &prefix, add_root_noise, deterministic,
        )
    })
    .map_err(pyo3::exceptions::PyValueError::new_err)
}

/// Arena-Match Stufe 3 (Brett 0, Top-K-Kandidaten + gemittelte Rollouts über
/// den Beutel-Zufall) vs. Stufe 1 (Brett 1, reine Netz-PUCT + DFS-Blatt),
/// dasselbe Netz. Siehe `evaluations/stage2_investigation.md`: Stufe 3
/// braucht keinen Value-Head, mittelt stattdessen explizit über künftige
/// Runden statt sie zu schätzen.
/// Defaults kalibriert aus gemessener Verzweigungsbreite/Zugzahl (siehe
/// evaluations/stage2_investigation.md, Stufe-3-Kalibrierung): top_k=2,
/// n_reps=3, horizon_rounds=2 (statt bis Spielende) haelt die Rollout-Kosten
/// gerade fuer teure Runde-1/2-Entscheidungen in einem praktikablen Rahmen.
/// `stage3_max_round=2`: Stufe 3 nur in Runde 1-2 einsetzen (dort zaehlt die
/// Mehrrunden-Frage am meisten), danach auf reine Stufe 1 zurueckfallen --
/// ein Besuchsanteil-/Q-Wert-basiertes "nur bei knappen Entscheidungen"-
/// Kriterium wurde gemessen und verworfen (bei 20-43 Kandidaten je Runde zu
/// verrauscht, siehe stage3_choose_action). `alphabeta_depth`/
/// `alphabeta_node_budget`: die Rollout-Fortsetzung nutzt jetzt Alpha-Beta-
/// Minimax mit Netz-Policy-Zugsortierung statt der vollen PUCT-Suche (Profiling
/// zeigte 1,8 Mio. Blattauswertungen fuer 2 Spiele, DFS-Solver/Netz/Features
/// je ~1/3 der Zeit -- Referenz domwil.co.uk/posts/azul-ai: Alpha-Beta mit
/// Zugsortierung braucht 42-54x weniger Knoten als reines Minimax, weil
/// unser DFS-Blatt EXAKT ist, nicht verrauscht wie ein Value-Netz).
#[pyfunction]
#[pyo3(signature = (model_path, n_games=50, sims1=200, stage3_shortlist_sims=100, stage3_rollout_sims=50, c_puct=1.5, top_k=2, n_reps=3, horizon_rounds=2, stage3_max_round=2, alphabeta_depth=2, alphabeta_node_budget=100, seed=None, num_threads=0))]
#[allow(clippy::too_many_arguments)]
fn stage3_vs_stage1_arena_match(
    py: Python<'_>,
    model_path: String,
    n_games: usize,
    sims1: u32,
    stage3_shortlist_sims: u32,
    stage3_rollout_sims: u32,
    c_puct: f64,
    top_k: usize,
    n_reps: usize,
    horizon_rounds: u32,
    stage3_max_round: u32,
    alphabeta_depth: u32,
    alphabeta_node_budget: u32,
    seed: Option<u64>,
    num_threads: usize,
) -> PyResult<String> {
    let seed = seed.unwrap_or_else(rand::random);
    py.detach(move || {
        crate::self_play::run_stage3_vs_stage1_arena(
            &model_path, n_games, sims1, stage3_shortlist_sims, stage3_rollout_sims, c_puct, top_k,
            n_reps, horizon_rounds, stage3_max_round, alphabeta_depth, alphabeta_node_budget, seed, num_threads,
        )
    })
    .map_err(pyo3::exceptions::PyValueError::new_err)
}

/// Diagnose (nur mit `--features clone_profiling` aussagekräftig, sonst
/// immer 0): setzt die Zeit-/Zaehler-Statistik aus `profiling.rs` zurueck --
/// vor einem zu profilierenden Testlauf aufrufen (siehe stage2_investigation.md).
#[pyfunction]
fn profiling_reset() {
    crate::profiling::reset_all();
    crate::self_play::ALPHABETA_CALLS.store(0, std::sync::atomic::Ordering::Relaxed);
    crate::self_play::ALPHABETA_NODE_VISITS.store(0, std::sync::atomic::Ordering::Relaxed);
}

/// Liest die aktuelle Zeit-/Zaehler-Statistik aus `profiling.rs`: wie viel
/// Zeit ging in Feature-Extraktion, Netz-Forward-Pass, DFS-Solver-Aufrufe
/// (jeweils Aufrufe + Gesamt-Nanosekunden), plus GameState-Klon-Zaehler.
/// Nur mit `--features clone_profiling` aussagekraeftig.
#[pyfunction]
fn profiling_snapshot() -> String {
    json!({
        "features_count": crate::profiling::features_count(),
        "features_ns": crate::profiling::features_ns(),
        "net_eval_count": crate::profiling::net_eval_count(),
        "net_eval_ns": crate::profiling::net_eval_ns(),
        "dfs_eval_count": crate::profiling::dfs_eval_count(),
        "dfs_eval_ns": crate::profiling::dfs_eval_ns(),
        "gamestate_clone_count": crate::profiling::gamestate_clone_count(),
        "alphabeta_calls": crate::self_play::ALPHABETA_CALLS.load(std::sync::atomic::Ordering::Relaxed),
        "alphabeta_node_visits": crate::self_play::ALPHABETA_NODE_VISITS.load(std::sync::atomic::Ordering::Relaxed),
    })
    .to_string()
}

/// ONNX-Inferenz für die Phase-B-Paritätsprüfung: lädt das Netz, wertet den
/// Feature-Vektor aus und gibt (policy_logits, value, moon_logits, points)
/// zurück -- passend zur Referenzdatei aus `export_onnx.py`.
#[pyfunction]
fn onnx_eval(
    path: String,
    features: Vec<f32>,
) -> PyResult<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)> {
    let net = crate::net::Net::load(&path, features.len())
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    net.eval(&features)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
}

/// Snapshot der aktiv wirksamen Rust-Suchkonstanten als JSON -- für
/// `self_play.py`s Lauf-Manifest (#64 Teil 1, Phase 2a, 2026-07-22): ein
/// Self-Play-Lauf soll rückwirkend rekonstruierbar sein (welche Engine-
/// Konfiguration hat DIESE Daten erzeugt), ohne den Rust-Quellcode zum
/// jeweiligen Commit-Stand extra auschecken zu müssen. Reines Auslesen
/// bestehender `pub`/`pub(crate)`-Konstanten aus `net_mcts.rs`/
/// `round_transition.rs`/`round_transition_deep.rs` -- kein Spielzustand
/// nötig, keine neue Suchlogik.
#[pyfunction]
fn engine_config_json() -> String {
    use crate::net_mcts::{
        ACTIVE_LEAF, DECOUPLE_NET_SIMS_FROM_ACTIONS, DETERMINIZE_ROOT_HIDDEN_INFO,
        FLOOR_SHAPING_WEIGHT, GUMBEL_TOP_M, LeafEval, MIRROR_OTHER_VAL, NUM_ACTIONS,
        POINTS_UTILITY_WEIGHT, POLICY_MASS_CUTOFF, ROUND_TRANSITION_SAMPLING,
        SHUFFLE_STACK_PEEK_IN_SEARCH, USE_GUMBEL_SEARCH,
    };
    let active_leaf = match ACTIVE_LEAF {
        LeafEval::Net => "Net",
        LeafEval::Dfs => "Dfs",
    };
    json!({
        "engine_version": env!("CARGO_PKG_VERSION"),
        "num_actions": NUM_ACTIONS,
        "active_leaf": active_leaf,
        "use_gumbel_search": USE_GUMBEL_SEARCH,
        "gumbel_top_m": GUMBEL_TOP_M,
        "decouple_net_sims_from_actions": DECOUPLE_NET_SIMS_FROM_ACTIONS,
        "floor_shaping_weight": FLOOR_SHAPING_WEIGHT,
        "points_utility_weight": POINTS_UTILITY_WEIGHT,
        "mirror_other_val": MIRROR_OTHER_VAL,
        "shuffle_stack_peek_in_search": SHUFFLE_STACK_PEEK_IN_SEARCH,
        "determinize_root_hidden_info": DETERMINIZE_ROOT_HIDDEN_INFO,
        "round_transition_sampling": ROUND_TRANSITION_SAMPLING,
        "policy_mass_cutoff": POLICY_MASS_CUTOFF,
        "round_transition_n_samples_search": crate::round_transition::N_SAMPLES_SEARCH,
        "bootstrap_horizon_rounds": crate::round_transition_deep::BOOTSTRAP_HORIZON_ROUNDS,
    })
    .to_string()
}

/// Statischer Wertungsplatten-Katalog für die Auswahl-UI (Port von
/// `/api/scoring_tiles`): `{tiles:[{id,name,description,emoji,excludes}],
/// exclusive_pairs:[[a,b],…]}`. Braucht keinen Spielzustand.
#[pyfunction]
fn scoring_tiles_json() -> String {
    use crate::scoring::{exclusion_partner, ALL_SCORING_TILES, MUTUALLY_EXCLUSIVE_PAIRS};
    let tiles: Vec<_> = ALL_SCORING_TILES
        .iter()
        .map(|t| {
            json!({
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "emoji": t.emoji,
                "excludes": exclusion_partner(t.id),
            })
        })
        .collect();
    let pairs: Vec<_> = MUTUALLY_EXCLUSIVE_PAIRS.iter().map(|&(a, b)| json!([a, b])).collect();
    json!({ "tiles": tiles, "exclusive_pairs": pairs }).to_string()
}

/// Python-Modul `mosaic_rust`.
#[pymodule]
fn mosaic_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(ping, m)?)?;
    m.add_function(wrap_pyfunction!(self_play_games, m)?)?;
    m.add_function(wrap_pyfunction!(self_play_games_with_net_labels, m)?)?;
    m.add_function(wrap_pyfunction!(arena_match, m)?)?;
    m.add_function(wrap_pyfunction!(scoring_tiles_json, m)?)?;
    m.add_function(wrap_pyfunction!(onnx_eval, m)?)?;
    m.add_function(wrap_pyfunction!(net_arena_match, m)?)?;
    m.add_function(wrap_pyfunction!(sibling_ranking_diagnostic, m)?)?;
    m.add_function(wrap_pyfunction!(draw_stack_peek_impact_diagnostic, m)?)?;
    m.add_function(wrap_pyfunction!(value_noise_floor_diagnostic, m)?)?;
    m.add_function(wrap_pyfunction!(net_vs_net_arena_match, m)?)?;
    m.add_function(wrap_pyfunction!(net_self_play_games, m)?)?;
    m.add_function(wrap_pyfunction!(stage3_vs_stage1_arena_match, m)?)?;
    m.add_function(wrap_pyfunction!(profiling_reset, m)?)?;
    m.add_function(wrap_pyfunction!(profiling_snapshot, m)?)?;
    m.add_function(wrap_pyfunction!(engine_config_json, m)?)?;
    m.add_class::<crate::py::PyGame>()?;
    Ok(())
}
