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
pub mod py;
pub mod round_end;
pub mod scoring;
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

/// Arena-Match Netz vs. Heuristik-MCTS (Netz auf Brett 0). Lädt das ONNX-Netz
/// einmal, spielt `n_games` (Startspieler alternierend) und gibt ein JSON-Array
/// `[{scores:[netz,heur], winner, steps, total_floor, floor_per_round}]` zurück.
#[pyfunction]
#[pyo3(signature = (model_path, net_sims=100, heur_sims=100, n_games=50, seed=None, num_threads=1, c=0.3, c_puct=1.5))]
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

/// ONNX-Inferenz für die Phase-B-Paritätsprüfung: lädt das Netz, wertet den
/// Feature-Vektor aus und gibt `(value, policy_logits)` zurück.
#[pyfunction]
fn onnx_eval(path: String, features: Vec<f32>) -> PyResult<(f32, Vec<f32>)> {
    let net = crate::net::Net::load(&path, features.len())
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let (policy, value, _moon) = net
        .eval(&features)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok((value, policy))
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
    m.add_function(wrap_pyfunction!(arena_match, m)?)?;
    m.add_function(wrap_pyfunction!(scoring_tiles_json, m)?)?;
    m.add_function(wrap_pyfunction!(onnx_eval, m)?)?;
    m.add_function(wrap_pyfunction!(net_arena_match, m)?)?;
    m.add_class::<crate::py::PyGame>()?;
    Ok(())
}
