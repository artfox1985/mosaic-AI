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
/// `progress_path`/`heartbeat_path` (Task #71, optional): siehe
/// `self_play::run_self_play`-Dokumentation -- Einzelspiel-Flush (JSONL, eine
/// Zeile je fertigem Spiel) + periodischer Zug-/Spiel-Herzschlag für den
/// Chunk-Supervisor in `self_play.py`.
#[pyfunction]
#[pyo3(signature = (n_games, base_sims=300, c=0.3, seed=None, num_threads=0, prefix="vrust".to_string(), progress_path=None, heartbeat_path=None))]
#[allow(clippy::too_many_arguments)]
fn self_play_games(
    py: Python<'_>,
    n_games: usize,
    base_sims: u32,
    c: f64,
    seed: Option<u64>,
    num_threads: usize,
    prefix: String,
    progress_path: Option<String>,
    heartbeat_path: Option<String>,
) -> String {
    let seed = seed.unwrap_or_else(rand::random);
    py.detach(move || {
        crate::self_play::run_self_play(
            n_games, base_sims, c, seed, num_threads, &prefix,
            progress_path.as_deref(), heartbeat_path.as_deref(),
        )
    })
}

/// Wie `self_play_games`, aber zusätzlich mit `round_transition_value`-
/// Labels aus einem geladenen Netz (siehe `self_play::play_one_game`s
/// `net`-Parameter): Spielentscheidungen bleiben VOLLSTÄNDIG heuristisch,
/// nur die vier Rundenübergänge werden zusätzlich per Netz-Chance-Node-
/// Sampling (`round_transition.rs`/`round_transition_deep.rs`) bewertet --
/// lässt den Value-Head vom rauschärmeren Ziel profitieren, ohne dass das
/// Netz je eine Spielentscheidung trifft. `progress_path`/`heartbeat_path`:
/// siehe `self_play_games` (Task #71). `record_rtv` (Task #85, rtv-Ablation
/// Phase 2): Default `false` -- das teure `round_transition_value`-Sampling
/// (~81% der Self-Play-Kosten, Task #80/#81) ist damit standardmässig AUS,
/// per `self_play.py --rtv` reaktivierbar. `bootstrap_value` bleibt davon
/// unberührt.
#[pyfunction]
#[pyo3(signature = (model_path, n_games, base_sims=300, c=0.3, seed=None, num_threads=0, prefix="vrust_netlabel".to_string(), record_rtv=false, progress_path=None, heartbeat_path=None))]
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
    record_rtv: bool,
    progress_path: Option<String>,
    heartbeat_path: Option<String>,
) -> PyResult<String> {
    let seed = seed.unwrap_or_else(rand::random);
    py.detach(move || {
        crate::self_play::run_self_play_with_net_labels(
            &model_path, n_games, base_sims, c, seed, num_threads, &prefix, record_rtv,
            progress_path.as_deref(), heartbeat_path.as_deref(),
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

/// Task #88 (Hybrid-Suche, kausaler Kopf-Test): Arena-Match Hybrid-Netz
/// (Priors/Moon-Order von `hybrid_policy`, Blattwert von `hybrid_value`) vs.
/// Einzel-Netz `plain_model`. `hybrid_board` (0 oder 1) waehlt, auf welchem
/// Brett die Hybrid-Suche steht -- fuer echten Brett-Tausch bei identischem
/// `seed` zwei Aufrufe mit vertauschtem `hybrid_board` UND vertauschten
/// sims/c_puct (Muster wie `tools/paired_gating.py`). `hybrid_policy`/
/// `hybrid_value` DÜRFEN identisch sein (Kontrollzelle, dann byte-identisch
/// zu `net_vs_net_arena_match`, siehe `self_play::run_net_vs_net_arena_hybrid`-
/// Kommentar). Gibt dasselbe JSON-Array-Format wie `net_vs_net_arena_match`
/// zurück (Aufrufer muss `hybrid_board` selbst mitfuehren, um `winner`
/// richtig zuzuordnen). Reines Diagnose-Werkzeug, kein Produktionspfad.
#[pyfunction]
#[pyo3(signature = (hybrid_policy, hybrid_value, plain_model, hybrid_board=0, sims_hybrid=200, sims_plain=200, n_games=50, seed=None, num_threads=1, c_puct_hybrid=1.5, c_puct_plain=1.5))]
#[allow(clippy::too_many_arguments)]
fn net_vs_net_arena_match_hybrid(
    py: Python<'_>,
    hybrid_policy: String,
    hybrid_value: String,
    plain_model: String,
    hybrid_board: usize,
    sims_hybrid: u32,
    sims_plain: u32,
    n_games: usize,
    seed: Option<u64>,
    num_threads: usize,
    c_puct_hybrid: f64,
    c_puct_plain: f64,
) -> PyResult<String> {
    let seed = seed.unwrap_or_else(rand::random);
    py.detach(move || {
        crate::self_play::run_net_vs_net_arena_hybrid(
            &hybrid_policy, &hybrid_value, &plain_model, hybrid_board, sims_hybrid, sims_plain, n_games,
            seed, num_threads, c_puct_hybrid, c_puct_plain,
        )
    })
    .map_err(pyo3::exceptions::PyValueError::new_err)
}

/// Netzgeführtes Self-Play (AlphaZero-Loop, Stufe 1: DFS-Blatt, saubere
/// Visit-Targets). Gibt alle Step-Records als JSON-Array zurück (Format wie
/// self_play_games). `num_threads=0` = alle Kerne. `progress_path`/
/// `heartbeat_path`: siehe `self_play_games` (Task #71) -- dies ist der Pfad
/// des `--mode network`-v12-Batches, daher die primäre Zielfunktion.
/// `record_rtv` (Task #85, rtv-Ablation Phase 2): Default `false` -- das
/// teure `round_transition_value`-Sampling (~81% der Self-Play-Kosten laut
/// Task #80/#81-Profiling) ist damit standardmässig AUS (erwarteter
/// Durchsatzgewinn ~3x), per `self_play.py --rtv` reaktivierbar. Begründet
/// durch die #84/#85-Gating-Evidenz (`evaluations/STATUS.md`): `v13_nortv_best`
/// (Training ohne rtv-Override) schlägt den vorherigen Champion `v12b_lr_best`
/// signifikant (171:129). `bootstrap_value` bleibt unabhängig davon erhalten.
/// `pcr_full_prob`/`pcr_cheap_sims` (Task #14, Playout-Cap-Randomization,
/// 2026-08-02): siehe `self_play.rs::play_net_self_play_game`-Dokumentation.
/// Default `pcr_full_prob=None` = AUS -- byte-identisch zum Vor-PCR-Verhalten
/// (kein neuer RNG-Verbrauch, kein neues JSON-Feld). `pcr_cheap_sims=150`
/// (KataGo-Groessenordnung fuer eine guenstige Suche) wirkt NUR, wenn
/// `pcr_full_prob` gesetzt ist.
#[pyfunction]
#[pyo3(signature = (model_path, n_games, base_sims=400, c_puct=1.5, seed=None, num_threads=0, prefix="netgen".to_string(), add_root_noise=true, deterministic=false, record_rtv=false, progress_path=None, heartbeat_path=None, pcr_full_prob=None, pcr_cheap_sims=150))]
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
    record_rtv: bool,
    progress_path: Option<String>,
    heartbeat_path: Option<String>,
    pcr_full_prob: Option<f64>,
    pcr_cheap_sims: u32,
) -> PyResult<String> {
    let seed = seed.unwrap_or_else(rand::random);
    py.detach(move || {
        crate::self_play::run_net_self_play(
            &model_path, n_games, base_sims, c_puct, seed, num_threads, &prefix, add_root_noise, deterministic,
            record_rtv, progress_path.as_deref(), heartbeat_path.as_deref(), pcr_full_prob, pcr_cheap_sims,
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
        // Task #80: Self-Play-Kostenprofil (Gumbel-Zugsuche vs. rtv- vs.
        // Bootstrap-Labels), siehe `play_net_self_play_game`.
        "gumbel_move_count": crate::profiling::gumbel_move_count(),
        "gumbel_move_ns": crate::profiling::gumbel_move_ns(),
        "rtv_count": crate::profiling::rtv_count(),
        "rtv_ns": crate::profiling::rtv_ns(),
        "bootstrap_count": crate::profiling::bootstrap_count(),
        "bootstrap_ns": crate::profiling::bootstrap_ns(),
        // Task #81: Netz-Eval-Anteil je Kategorie (Amdahl-Split fuer den
        // geplanten GPU-Batcher, Task #82) -- `*_net_eval_ns` ist die in der
        // jeweiligen Kategorie enthaltene Netz-Forward-Pass-Zeit (Teilmenge von
        // z.B. `gumbel_move_ns`), `*_net_eval_calls` die Aufrufzahl,
        // `*_net_eval_instances` Aufrufe x Batchgroesse (1 fuer `Net::eval`, 2
        // fuer `eval_pair`) -- ergibt die Evals/s-Nachfrage an den GPU-Batcher.
        "gumbel_net_eval_ns": crate::profiling::gumbel_net_eval_ns(),
        "gumbel_net_eval_calls": crate::profiling::gumbel_net_eval_calls(),
        "gumbel_net_eval_instances": crate::profiling::gumbel_net_eval_instances(),
        "rtv_net_eval_ns": crate::profiling::rtv_net_eval_ns(),
        "rtv_net_eval_calls": crate::profiling::rtv_net_eval_calls(),
        "rtv_net_eval_instances": crate::profiling::rtv_net_eval_instances(),
        "bootstrap_net_eval_ns": crate::profiling::bootstrap_net_eval_ns(),
        "bootstrap_net_eval_calls": crate::profiling::bootstrap_net_eval_calls(),
        "bootstrap_net_eval_instances": crate::profiling::bootstrap_net_eval_instances(),
    })
    .to_string()
}

/// ONNX-Inferenz für die Phase-B-Paritätsprüfung: lädt das Netz, wertet den
/// Feature-Vektor aus und gibt (policy_logits, value, moon_logits, points)
/// zurück -- passend zur Referenzdatei aus `export_onnx.py`. Task #11 Phase 2
/// (M3.5): `Net::load_auto` statt `Net::load(path, features.len())` -- das
/// erzwungene `InputLayout::Flat(features.len())` brach für Zwei-Input-2D-
/// Modelle bereits beim Laden (Shape-Mismatch mit dem echten Graphen). Für
/// Flach-Modelle byte-identisch (siehe `examples/net_load_auto_backcompat.rs`);
/// für 2D-Modelle erwartet `features` weiterhin EINEN zusammenhängenden
/// Puffer (Planes-Teil gefolgt vom Flat-Teil, siehe `net.rs::Net::build_inputs`).
#[pyfunction]
fn onnx_eval(
    path: String,
    features: Vec<f32>,
) -> PyResult<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)> {
    let net = crate::net::Net::load_auto(&path)
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

/// Task #89 (Oracle-Metriken): Netz-Suche auf einem EXTERN gespeicherten
/// Zustand statt `PyGame::state` -- der bisher fehlende Such-Einstieg (siehe
/// `evaluations/STATUS.md`, "Task #89 ... BLOCKIERT", Commit `373acc1`).
/// `state_json` ist ein `state_to_json`-Zustandsdict, wie es in Self-Play-
/// Records und `evaluations/frozen_eval_set.pkl`s `records[i]["state"]`
/// steht (Python: `json.dumps(record["state"])`). Baut den `GameState` per
/// `serialize::json_to_state` (siehe dortiger Doku-Kommentar für die
/// Rekonstruktions-Details/Näherungen), lädt das Netz und ruft dieselbe
/// Maschinerie wie `PyGame::ai_debug_net_json` (`py.rs`) auf --
/// `net_search_with_tree` mit `add_root_noise=false` (deterministische
/// Analyse, keine Self-Play-Exploration). Gibt dasselbe Analyse-Dict zurück
/// (`moves` = Wurzelkandidaten mit `action_id`/`mcts_visits`/`mcts_q`/
/// `net_prob`(_norm), `ai_action` = Index der besten Aktion in `moves`),
/// ergänzt um ein explizites Top-Level-Feld `root_value` (= Root-Q, gleiche
/// Zahl wie `tree.win_pct/100`, hier nur bequemer benannt). Gibt für
/// Nicht-Drafting-Zustände (z.B. Phase::Tiling) `moves: []`/`ai_action: null`
/// zurück (identisches Verhalten zu `net_search_with_tree` selbst) --
/// Aufrufer sollte vorab auf `state["phase"] == "drafting"` filtern.
/// `seed` steuert sowohl die Rekonstruktions-Neumischung der verdeckten
/// Sammlungen (`json_to_state`) als auch die anschließende
/// `DETERMINIZE_ROOT_HIDDEN_INFO`-Mischung der Suche selbst (derselbe
/// RNG-Strom, analog zum Determinisierungs-Muster in `net_mcts.rs`) -- fest
/// pro Zustand (z.B. hash-abgeleitet) macht die Oracle-Erzeugung
/// reproduzierbar.
#[pyfunction]
#[pyo3(signature = (state_json, model_path, sims=500, c_puct=1.5, seed=None))]
fn net_search_state_json(
    state_json: String,
    model_path: String,
    sims: u32,
    c_puct: f64,
    seed: Option<u64>,
) -> PyResult<String> {
    use pyo3::exceptions::PyValueError;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    let seed = seed.unwrap_or_else(rand::random);
    let mut rng = StdRng::seed_from_u64(seed);

    let parsed: serde_json::Value = serde_json::from_str(&state_json)
        .map_err(|e| PyValueError::new_err(format!("state_json: JSON-Parse-Fehler: {e}")))?;
    let state = crate::serialize::json_to_state(&parsed, &mut rng).map_err(PyValueError::new_err)?;

    let net = crate::net::Net::load_auto(&model_path)
        .map_err(|e| PyValueError::new_err(format!("Netz konnte nicht geladen werden: {e}")))?;

    let (_chosen, analysis) =
        crate::net_mcts::net_search_with_tree(&net, &state, sims, c_puct, false, &mut rng, None, false);

    // Nicht-Drafting-Zustände: `net_search_with_tree` liefert `Value::Null`
    // (kein Baum gebaut) -- durch ein leeres, aber strukturgleiches Dict
    // ersetzen, damit Aufrufer nicht zwischen "null" und "leere moves-Liste"
    // unterscheiden müssen.
    let mut analysis = if analysis.is_null() {
        json!({ "has_net": true, "simulations": sims, "moves": [], "ai_action": serde_json::Value::Null })
    } else {
        analysis
    };
    if let Some(obj) = analysis.as_object_mut() {
        let root_value = obj
            .get("tree")
            .and_then(|t| t.get("win_pct"))
            .and_then(|w| w.as_f64())
            .map(|w| w / 100.0);
        obj.insert("root_value".to_string(), json!(root_value));
        obj.insert("phase".to_string(), json!(state.phase.as_str()));
        obj.insert("round".to_string(), json!(state.round_number));
    }
    Ok(analysis.to_string())
}

/// Wie [`net_search_state_json`], aber mit `collect_trace=true` (Task #95)
/// -- liefert zusätzlich `value_debug` (Root-Value-Breakdown) und
/// `gumbel_trace` (Top-m-Auswahl + jede Sequential-Halving-Phase mit
/// `q`/`sigma_q`/`score`/`eliminated` je Kandidat, siehe `GumbelTrace` in
/// `net_mcts.rs`) im Analyse-Dict. Rein additiv: eigene Funktion statt eines
/// neuen Parameters an `net_search_state_json`, damit bestehende Aufrufer
/// (Task #89, `tools/scoring_tile_sensitivity.py` etc.) unverändert bleiben.
/// Für Task #5 (Gumbel-Rang-Invarianz vs. Wertungsplatten, 2026-07-27): der
/// bisher fehlende Such-Einstieg, der einen strukturierten Gumbel-Trace auf
/// einem BELIEBIGEN extern gespeicherten Zustand erlaubt (bisher nur über
/// `PyGame::ai_debug_net_json` auf dem LIVE-Server-Zustand verfügbar). Kostet
/// wie beim bestehenden `collect_trace=true`-Pfad einen zusätzlichen Netz-
/// Forward-Pass (`compute_root_value_debug`), sonst keine Änderung an
/// Auswahl/Backprop/RNG-Verbrauch (Paritätstest siehe `net_mcts.rs`-
/// Testmodul, `gumbel_trace_collection_does_not_change_search`).
#[pyfunction]
#[pyo3(signature = (state_json, model_path, sims=500, c_puct=1.5, seed=None))]
fn net_search_state_json_trace(
    state_json: String,
    model_path: String,
    sims: u32,
    c_puct: f64,
    seed: Option<u64>,
) -> PyResult<String> {
    use pyo3::exceptions::PyValueError;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    let seed = seed.unwrap_or_else(rand::random);
    let mut rng = StdRng::seed_from_u64(seed);

    let parsed: serde_json::Value = serde_json::from_str(&state_json)
        .map_err(|e| PyValueError::new_err(format!("state_json: JSON-Parse-Fehler: {e}")))?;
    let state = crate::serialize::json_to_state(&parsed, &mut rng).map_err(PyValueError::new_err)?;

    let net = crate::net::Net::load_auto(&model_path)
        .map_err(|e| PyValueError::new_err(format!("Netz konnte nicht geladen werden: {e}")))?;

    let (_chosen, analysis) =
        crate::net_mcts::net_search_with_tree(&net, &state, sims, c_puct, false, &mut rng, None, true);

    let mut analysis = if analysis.is_null() {
        json!({
            "has_net": true, "simulations": sims, "moves": [], "ai_action": serde_json::Value::Null,
            "value_debug": serde_json::Value::Null, "gumbel_trace": serde_json::Value::Null,
        })
    } else {
        analysis
    };
    if let Some(obj) = analysis.as_object_mut() {
        let root_value = obj
            .get("tree")
            .and_then(|t| t.get("win_pct"))
            .and_then(|w| w.as_f64())
            .map(|w| w / 100.0);
        obj.insert("root_value".to_string(), json!(root_value));
        obj.insert("phase".to_string(), json!(state.phase.as_str()));
        obj.insert("round".to_string(), json!(state.round_number));
    }
    Ok(analysis.to_string())
}

/// Wertungsplatten-Endwertung für einen extern gespeicherten Zustand (z.B.
/// ein Self-Play-Record `state`-Feld, `json.dumps(record["state"])`) --
/// reine additive Lesefunktion für die Wertungsplatten-Diagnose (2026-07-26,
/// Nutzer-Verdacht "die KI ignoriert die Wertungsplatten"), berührt keine
/// bestehende Suche/Produktion. Siehe `serialize::end_scoring_from_state`
/// für die exakte Begründung, warum das Ergebnis (anders als z.B.
/// `estimated_score`) für JEDEN validen Zustand EXAKT ist (nicht nur eine
/// Näherung). Gibt `{"player_0": {"details":[{id,name,emoji,desc,score},…],
/// "total": N}, "player_1": {…}}` zurück.
#[pyfunction]
#[pyo3(signature = (state_json, tile_ids, seed=None))]
fn end_scoring_from_state_json(
    state_json: String,
    tile_ids: Vec<usize>,
    seed: Option<u64>,
) -> PyResult<String> {
    use pyo3::exceptions::PyValueError;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    let mut rng = StdRng::seed_from_u64(seed.unwrap_or(0));
    let parsed: serde_json::Value = serde_json::from_str(&state_json)
        .map_err(|e| PyValueError::new_err(format!("state_json: JSON-Parse-Fehler: {e}")))?;
    let result = crate::serialize::end_scoring_from_state(&parsed, &tile_ids, &mut rng)
        .map_err(PyValueError::new_err)?;
    Ok(result.to_string())
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
/// Task #20: bis zu `k` VOLLSTAENDIGE Tiling-Abschluesse eines Zustands, je mit
/// Rundenpunkten und dem resultierenden Zustand als JSON.
///
/// Zweck: die netz-gefuehrte Tiling-Auswahl (Punkte x Value) braucht die
/// FERTIGEN Bretter -- das Netz bewertet den Zustand, aus dem die naechste Runde
/// startet. Der bestehende Solver liefert nur einen Schritt und nur dessen Score.
///
/// Erste Nutzung ist eine MESSUNG: streuen die Value-Werte unter den Kandidaten
/// ueberhaupt genug, damit eine Multiplikation je einen Punktabstand kippt?
/// Ist die Spreizung winzig, erledigt sich das Feature ohne Arena-Lauf.
///
/// `json_to_state` mischt verdeckte Information neu (siehe dessen Doku) -- fuer
/// die Tiling-Phase ohne Belang, dort werden keine verdeckten Bestaende
/// angefasst. Der Seed wird trotzdem durchgereicht, damit Laeufe reproduzierbar
/// bleiben.
#[pyfunction]
#[pyo3(signature = (state_json, player, k=8, seed=None))]
fn tiling_candidates_json(
    state_json: String,
    player: usize,
    k: usize,
    seed: Option<u64>,
) -> PyResult<String> {
    use pyo3::exceptions::PyValueError;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    let mut rng = StdRng::seed_from_u64(seed.unwrap_or(0));
    let parsed: serde_json::Value = serde_json::from_str(&state_json)
        .map_err(|e| PyValueError::new_err(format!("state_json: JSON-Parse-Fehler: {e}")))?;
    let state = crate::serialize::json_to_state(&parsed, &mut rng).map_err(PyValueError::new_err)?;
    if player >= state.players.len() {
        return Err(PyValueError::new_err(format!(
            "player {player} ausserhalb (nur {} Spieler)",
            state.players.len()
        )));
    }

    let cands = crate::tiling_solver::top_k_tilings(&state, player, k);
    let out: Vec<serde_json::Value> = cands
        .into_iter()
        .map(|o| {
            serde_json::json!({
                "points": o.points,
                "end_scoring": crate::scoring::calculate_end_scoring(
                    &o.final_state.players[player],
                    &o.final_state.scoring_tile_ids,
                ).total,
                "state": crate::serialize::state_to_json(&o.final_state, true),
            })
        })
        .collect();
    Ok(serde_json::Value::Array(out).to_string())
}

/// Task #20-Validierung: einen TILING-Zustand ueber den Rundenuebergang in die
/// naechste DRAFTING-Stellung weiterschalten, mit gesetztem Zufalls-Seed.
///
/// Noetig, weil eine Tiefensuche in der Tiling-Phase strukturell nichts liefert
/// -- die Referenz fuer "welcher Tiling-Abschluss ist wirklich besser" laesst
/// sich erst danach erheben. Derselbe Seed fuer alle Kandidaten einer Stellung
/// macht den Vergleich GEPAART: der Nachfuell-Wurf ist dann identisch, der
/// einzige Unterschied ist das Brett.
#[pyfunction]
#[pyo3(signature = (state_json, seed))]
fn advance_after_tiling_json(state_json: String, seed: u64) -> PyResult<String> {
    use pyo3::exceptions::PyValueError;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    let mut rng = StdRng::seed_from_u64(seed);
    let parsed: serde_json::Value = serde_json::from_str(&state_json)
        .map_err(|e| PyValueError::new_err(format!("state_json: JSON-Parse-Fehler: {e}")))?;
    let state = crate::serialize::json_to_state(&parsed, &mut rng).map_err(PyValueError::new_err)?;
    let pre = crate::round_transition::resolve_to_pre_chance(&state)
        .ok_or_else(|| PyValueError::new_err("Zustand ist nicht in Phase::Tiling"))?;
    let next = crate::round_transition::advance_one_chance(&pre, &mut rng)
        .ok_or_else(|| PyValueError::new_err("Rundenuebergang fehlgeschlagen"))?;
    Ok(crate::serialize::state_to_json(&next, true).to_string())
}

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
    m.add_function(wrap_pyfunction!(net_vs_net_arena_match_hybrid, m)?)?;
    m.add_function(wrap_pyfunction!(net_self_play_games, m)?)?;
    m.add_function(wrap_pyfunction!(stage3_vs_stage1_arena_match, m)?)?;
    m.add_function(wrap_pyfunction!(profiling_reset, m)?)?;
    m.add_function(wrap_pyfunction!(profiling_snapshot, m)?)?;
    m.add_function(wrap_pyfunction!(engine_config_json, m)?)?;
    m.add_function(wrap_pyfunction!(net_search_state_json, m)?)?;
    m.add_function(wrap_pyfunction!(net_search_state_json_trace, m)?)?;
    m.add_function(wrap_pyfunction!(tiling_candidates_json, m)?)?;
    m.add_function(wrap_pyfunction!(advance_after_tiling_json, m)?)?;
    m.add_function(wrap_pyfunction!(end_scoring_from_state_json, m)?)?;
    m.add_class::<crate::py::PyGame>()?;
    Ok(())
}
