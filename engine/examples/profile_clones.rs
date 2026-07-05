//! Kombiniert die isolierte Klon-Kosten-Messung (`benches/clone_cost.rs`) mit
//! einem echten Suchaufruf (net_mcts, wie im realen Spiel), um den geschätzten
//! Anteil des GameState-Clonings an der Gesamt-Suchzeit zu bestimmen.
//!
//! Ausführen mit: `cargo run --release --example profile_clones --features clone_profiling`
//! (ohne das Feature bleibt der Zähler bei 0 -- Kompilierbarkeit ist aber auch
//! ohne Feature gegeben, da `note_gamestate_clone` dann ein No-Op ist).

use mosaic_rust::dome::build_dome_tile_pool;
use mosaic_rust::net::Net;
use mosaic_rust::net_mcts::{net_search_drafting_action, LeafEval};
use mosaic_rust::state::setup_new_game;
use rand::rngs::StdRng;
use rand::SeedableRng;
use std::time::Instant;

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
    state
}

fn main() {
    let model_path = std::env::args().nth(1).unwrap_or_else(|| "../models/alphazero_v8.onnx".into());
    let sims: u32 = std::env::args().nth(2).and_then(|s| s.parse().ok()).unwrap_or(2000);

    let net = Net::load(&model_path, mosaic_rust::features::INPUT_SIZE)
        .unwrap_or_else(|e| panic!("Konnte {model_path} nicht laden: {e}"));
    let state = midgame_state();
    let mut rng = StdRng::seed_from_u64(7);

    mosaic_rust::profiling::reset_all();

    let start = Instant::now();
    let _ = net_search_drafting_action(&net, &state, sims, 1.5, false, LeafEval::Dfs, &mut rng);
    let elapsed = start.elapsed();
    let total_ns = elapsed.as_nanos() as f64;

    println!("sims={sims} Gesamtzeit={elapsed:?}");

    let clones = mosaic_rust::profiling::gamestate_clone_count();
    const NS_PER_CLONE: f64 = 6117.0; // aus benches/clone_cost.rs (gamestate_clone_midgame)
    let clone_ns = clones as f64 * NS_PER_CLONE;
    println!(
        "  GameState-Klone:      n={clones:<6} geschaetzt={:.2}ms ({:.1}%)",
        clone_ns / 1e6,
        100.0 * clone_ns / total_ns
    );

    let (fc, fns) = (mosaic_rust::profiling::features_count(), mosaic_rust::profiling::features_ns());
    println!(
        "  Feature-Serialisierung: n={fc:<6} gemessen={:.2}ms ({:.1}%)",
        fns as f64 / 1e6,
        100.0 * fns as f64 / total_ns
    );

    let (nc, nns) = (mosaic_rust::profiling::net_eval_count(), mosaic_rust::profiling::net_eval_ns());
    println!(
        "  Netz-Forward (net.eval): n={nc:<6} gemessen={:.2}ms ({:.1}%)",
        nns as f64 / 1e6,
        100.0 * nns as f64 / total_ns
    );

    let (dc, dns) = (mosaic_rust::profiling::dfs_eval_count(), mosaic_rust::profiling::dfs_eval_ns());
    println!(
        "  DFS-Solver (Stage-1-Blatt): n={dc:<6} gemessen={:.2}ms ({:.1}%)",
        dns as f64 / 1e6,
        100.0 * dns as f64 / total_ns
    );

    #[cfg(not(feature = "clone_profiling"))]
    println!("(Zaehler inaktiv -- mit --features clone_profiling erneut ausführen fuer echte Werte)");
}
