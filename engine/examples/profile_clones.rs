//! Kombiniert die isolierte Klon-Kosten-Messung (`benches/clone_cost.rs`) mit
//! einem echten Suchaufruf (net_mcts, wie im realen Spiel), um den geschätzten
//! Anteil des GameState-Clonings an der Gesamt-Suchzeit zu bestimmen.
//!
//! Ausführen mit: `cargo run --release --example profile_clones --features clone_profiling`
//! (ohne das Feature bleibt der Zähler bei 0 -- Kompilierbarkeit ist aber auch
//! ohne Feature gegeben, da `note_gamestate_clone` dann ein No-Op ist).

use mosaic_rust::dome::build_dome_tile_pool;
use mosaic_rust::net::Net;
use mosaic_rust::net_mcts::{net_search_drafting_action, SearchConfig};
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
    // 2026-09-21 (par.8h Punkt 9): `Net::load` mit fester `INPUT_SIZE` ist der
    // FLACHE Lader; seit dem 2D-Encoder scheitert er an jedem aktuellen Modell
    // mit "Failed analyse for node ... Conv", und flache Modelle liegen keine
    // mehr im Baum. `Net::load_auto` erkennt die Eingabeform am Modell selbst
    // (Architektur-Fixpunkt "2D encoder must be additive": die Input-Shape
    // kommt vom Modell, nicht aus einer Konstante). Ohne diese Zeile war das
    // Werkzeug nicht mehr lauffaehig -- und damit die Frage, zu der es das
    // Instrument ist, nicht beantwortbar.
    let default_model = "../models/frozen_champions/v31-b01/model.onnx".to_string();
    let model_path = std::env::args().nth(1).unwrap_or(default_model);
    let sims: u32 = std::env::args().nth(2).and_then(|s| s.parse().ok()).unwrap_or(2000);

    let net = Net::load_auto(&model_path)
        .unwrap_or_else(|e| panic!("Konnte {model_path} nicht laden: {e}"));
    let state = midgame_state();
    let mut rng = StdRng::seed_from_u64(7);

    mosaic_rust::profiling::reset_all();

    let start = Instant::now();
    let _ = net_search_drafting_action(&net, &state, sims, 1.5, false, &mut rng, &SearchConfig::from_env());
    let elapsed = start.elapsed();
    let total_ns = elapsed.as_nanos() as f64;

    println!("sims={sims} Gesamtzeit={elapsed:?}");

    let clones = mosaic_rust::profiling::gamestate_clone_count();
    // Neu gemessen 2026-09-21 (par.8h Punkt 9): `cargo bench --bench clone_cost`
    // gibt fuer `gamestate_clone_midgame` 4,61 us (Spanne 4,30-4,95). Der alte
    // Wert 6117 lag 33 Prozent darueber -- eine Konstante, die seit einem
    // frueheren Zustand des `GameState` nicht nachgezogen worden war und jede
    // Prozentangabe dieses Werkzeugs nach oben verzerrt hat.
    const NS_PER_CLONE: f64 = 4609.0; // aus benches/clone_cost.rs (gamestate_clone_midgame)
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
