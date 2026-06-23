//! Mosaic-AI Rust-Kern (Engine + MCTS + Self-Play), via PyO3 nach Python exportiert.
//!
//! Stand: Toolchain-Gerüst. Vorerst nur Smoke-Test-Funktionen; Engine/MCTS/Self-Play
//! folgen schrittweise (siehe Plan: Phase 2–4).

use pyo3::prelude::*;

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

/// Python-Modul `mosaic_rust`.
#[pymodule]
fn mosaic_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(ping, m)?)?;
    Ok(())
}
