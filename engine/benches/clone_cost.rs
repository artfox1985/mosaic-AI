//! Isolierte Kostenmessung von `GameState::clone()` — Grundlage für die Frage,
//! ob das Klonen im MCTS-Hot-Path (ein Klon pro EXPAND, siehe `mcts.rs`/
//! `net_mcts.rs`) einen relevanten Anteil der Suchzeit frisst. Kombiniert mit
//! dem Klon-Zähler (`profiling::CLONE_COUNT`, nur mit Feature `clone_profiling`
//! aktiv) ergibt (ns/Klon) × (Klone je Suchaufruf) den geschätzten Anteil an
//! der Gesamt-Suchzeit.

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use mosaic_rust::dome::build_dome_tile_pool;
use mosaic_rust::state::setup_new_game;
use rand::rngs::StdRng;
use rand::SeedableRng;

/// Repräsentativer Midgame-Zustand: Standard-Setup PLUS je 4 platzierte
/// Kuppelplatten pro Spieler (typisch für Runde 3-4) — sonst würde ein
/// komplett leeres Startbrett die Kosten der verschachtelten
/// `dome_slots: Vec<Vec<Option<DomeTile>>>`-Allokationen unterschätzen.
fn midgame_state() -> mosaic_rust::state::GameState {
    let mut rng = StdRng::seed_from_u64(42);
    let mut state = setup_new_game(["Spieler 1".into(), "KI".into()], 0, &mut rng);
    let pool = build_dome_tile_pool();
    for pi in 0..2 {
        for (i, &(sr, sc)) in [(0usize, 0usize), (0, 1), (1, 0), (1, 1)].iter().enumerate() {
            let tile = pool[(pi * 4 + i) % pool.len()].clone();
            let _ = state.players[pi].dome_grid.place_dome_tile(tile, sr, sc);
        }
    }
    // Log ist im Suchbaum bei jedem neuen Knoten geleert (siehe `child_state.log.clear()`
    // in mcts.rs/net_mcts.rs) -- hier trotzdem ein paar Zeilen, um den ROOT-Klon
    // (einmal pro Suchaufruf, NICHT pro Sim) realistisch abzubilden.
    for i in 0..20 {
        state.log_event(format!("Testzug {i}"));
    }
    state
}

fn bench_clone(c: &mut Criterion) {
    let state = midgame_state();
    c.bench_function("gamestate_clone_midgame", |b| {
        b.iter(|| black_box(state.clone()))
    });

    // Referenzwert: leerer Startzustand (0 platzierte Kuppelplatten, leeres
    // Log) -- Differenz zeigt, wie viel die verschachtelten Vecs ausmachen.
    let mut rng = StdRng::seed_from_u64(42);
    let empty = setup_new_game(["Spieler 1".into(), "KI".into()], 0, &mut rng);
    c.bench_function("gamestate_clone_fresh_start", |b| {
        b.iter(|| black_box(empty.clone()))
    });
}

criterion_group!(benches, bench_clone);
criterion_main!(benches);
