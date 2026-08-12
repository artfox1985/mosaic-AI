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
pub mod net_batcher;
pub mod net_ipc;
pub mod net_mcts;
// Weg B (PREREG_gpu_inferenzpfad.md §11, `net.rs::eval_batch`-Rangfolge):
// nur compiliert, wenn `ort` als optionale Abhaengigkeit ueber dieses
// Feature aktiv ist (siehe `Cargo.toml`) -- ein Bau ohne das Feature (jeder
// heutige Wheel-Bau) sieht dieses Modul ueberhaupt nicht.
#[cfg(feature = "ort_cuda_probe")]
pub mod net_ort;
pub mod profiling;
pub mod provokation;
pub mod py;
pub mod round5;
pub mod round_end;
pub mod round_transition;
pub mod round_transition_deep;
pub mod round_transition_resample;
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
/// `log_games` (Default `false`, 2026-08-11): haengt je Partie `game_seed`/
/// `first_player`/`names`/`log` an -- `log` ist die vollstaendige
/// `GameState::log`-Zeilenliste (identischer Wortlaut wie die Server-Logs
/// `static/log/game_*.log`, siehe `state.rs::log_event`/`execution.rs`/
/// `game.rs`/`round_end.rs` -- dieselben Funktionen erzeugen beide). Reine
/// Zusatzausgabe (kein neuer Suchpfad, kein RNG-Verbrauch): bei `false`
/// bleibt das Ergebnis wie zuvor.
/// `seeds` (Plattenkopf-Versuch, `PREREG_plattenkopf.md`, 2026-08-11): siehe
/// `self_play::run_net_arena_match`-Dokumentation -- gesetzt, spielt Partie
/// `i` exakt `seeds[i]` (statt der abgeleiteten Formel) und `n_games` folgt
/// der Listenlänge. `None` (Default) = Bestandsverhalten, byte-identisch.
#[pyfunction]
#[pyo3(signature = (model_path, net_sims=100, heur_sims=100, n_games=50, seed=None, num_threads=1, c=0.3, c_puct=1.5, log_games=false, seeds=None))]
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
    log_games: bool,
    seeds: Option<Vec<u64>>,
) -> PyResult<String> {
    let seed = seed.unwrap_or_else(rand::random);
    py.detach(move || {
        crate::self_play::run_net_arena_match(
            &model_path, net_sims, heur_sims, n_games, seed, num_threads, c, c_puct, log_games, seeds,
        )
    })
    .map_err(pyo3::exceptions::PyValueError::new_err)
}

/// Arena-Match Netz A (Brett 0) vs. Netz B (Brett 1). Lädt beide ONNX-Netze,
/// spielt `n_games` (Startspieler alternierend) und gibt ein JSON-Array
/// `[{scores:[A,B], winner, steps, total_floor, floor_per_round}]` zurück.
/// `log_games` (Default `false`, 2026-08-11): siehe `net_arena_match`-
/// Dokumentation -- identisches Zusatzfeld-Set, derselbe Spielpfad-Typ.
/// `seeds`: siehe `net_arena_match`-Dokumentation, identisches Muster (nutzt
/// denselben Seed-Ableitungspfad wie dort, siehe
/// `self_play::run_net_vs_net_arena`-Dokumentation).
#[pyfunction]
#[pyo3(signature = (model_a, model_b, sims_a=200, sims_b=200, n_games=50, seed=None, num_threads=1, c_puct_a=1.5, c_puct_b=1.5, log_games=false, seeds=None))]
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
    log_games: bool,
    seeds: Option<Vec<u64>>,
) -> PyResult<String> {
    let seed = seed.unwrap_or_else(rand::random);
    py.detach(move || {
        crate::self_play::run_net_vs_net_arena(
            &model_a, &model_b, sims_a, sims_b, n_games, seed, num_threads, c_puct_a, c_puct_b, log_games, seeds,
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

/// Task #32 (`profiling.rs`-Modulkopf "Task #32", `evaluations/STATUS.md`
/// Abschnitt "Task #32"): setzt das env-gegatete Self-Play-Zeitprofil
/// zurück -- vor einem zu profilierenden `net_self_play_games`-Lauf
/// aufrufen (`MOSAIC_PROFILE_SELFPLAY=1` muss gesetzt sein, sonst bleibt
/// ohnehin alles bei 0). UNABHÄNGIG von `profiling_reset`/`reset_all` oben
/// (andere Zähler, anderes Gate -- Env statt `clone_profiling`-Feature).
#[pyfunction]
fn selfplay_profile_reset() {
    crate::profiling::selfplay_profile::reset();
}

/// Liest den aktuellen Self-Play-Zeitprofil-Snapshot (Task #32) als JSON:
/// alle fünf Basiskategorien (`net_inference`, `round5_alphabeta`,
/// `tiling_solver`, `bootstrap_value`, `total_selfplay`) in Nanosekunden +
/// Aufrufzahl + Prozentanteil an `total_selfplay_ns`, PLUS die drei
/// Überschneidungs-Zusatzzähler und die daraus vorgerechneten
/// überschneidungsfreien Restgrößen `round5_bookkeeping_ns`/
/// `bootstrap_nonnet_ns` -- siehe `profiling.rs::selfplay_profile`-
/// Modulkopf-Doku für die vollständige Kategorisierungs-Regel. Bleibt bei
/// `MOSAIC_PROFILE_SELFPLAY` nicht gesetzt komplett bei 0 (`"enabled":
/// false` im Snapshot zeigt das an).
#[pyfunction]
fn selfplay_profile_json() -> String {
    crate::profiling::selfplay_profile::snapshot_json()
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

/// A2 (Laufzeit-Vertragsstempel, `evaluations/DESIGN_konventionen_als_
/// pruefungen.md` Abschnitt "A2"): die kanonische Zeichenkette, aus der
/// [`contract_hash`] gebildet wird. ÖFFENTLICH als eigener Schritt (statt
/// direkt in `contract_hash` verdrahtet), damit ein Rust-Test die Herleitung
/// unabhängig von der Hash-Funktion selbst belegen kann.
///
/// Enthält exakt die Vertragsgrößen, die ein warm gestartetes/geladenes Netz
/// betreffen: `INPUT_SIZE` (`features.rs`), `NUM_PLANES_CHANNELS`
/// (`features.rs`), `NUM_ACTIONS` (`net_mcts.rs`, = Policy-Kopf-Breite) und
/// die ONNX-Kopf-Reihenfolge, WIE `net.rs` SIE INTERPRETIERT -- nicht wie sie
/// in `export_onnx.py` benannt sein könnte: die ersten vier Outputs liest
/// `net.rs` (`eval`/`eval_ex`/`eval_pair`/`eval_batch`, siehe dortige
/// `out[0]..out[3]`-Zeilen) REIN POSITIONELL (Index 0=policy, 1=value,
/// 2=moon, 3=points, Namen werden dabei nicht geprüft), der optionale fünfte
/// Kopf wird dagegen NAMENTLICH gesucht (`"opp_points"`, siehe
/// `net.rs::detect_opp_head`/`output_opp_head_index`). Deshalb hier als feste
/// Liste `["policy","value","moon","points","opp_points"]` nachgebildet --
/// ändert sich diese Interpretation in `net.rs` (andere Positionsreihenfolge,
/// ein weiterer positionell gelesener Kopf, ein anderer Name), MUSS diese
/// Liste mitgeändert werden, sonst zeigt der Hash einen Vertrag an, den
/// `net.rs` tatsächlich nicht mehr einhält.
fn contract_canonical_string() -> String {
    let heads = ["policy", "value", "moon", "points", "opp_points"];
    format!(
        "INPUT_SIZE={};NUM_PLANES_CHANNELS={};NUM_ACTIONS={};HEADS={}",
        crate::features::INPUT_SIZE,
        crate::features::NUM_PLANES_CHANNELS,
        crate::net_mcts::NUM_ACTIONS,
        heads.join(",")
    )
}

/// FNV-1a (64-bit) über einen ASCII/UTF-8-String -- öffentlich dokumentierter
/// Drei-Zeilen-Algorithmus (Offset-Basis + Primzahl, keine Bibliothek nötig),
/// bewusst NICHT `std::collections::hash_map::DefaultHasher` (SipHash):
/// dessen konkreter Algorithmus ist laut Standardbibliotheks-Doku "nicht
/// festgelegt" und darf sich zwischen Rust-Versionen ändern -- unbrauchbar
/// für einen Vertragsstempel, den ein EXTERNES Werkzeug (z.B. ein Python-
/// Skript, das nur die Quellkonstanten liest, ohne die Rust-DLL zu laden)
/// unabhängig nachrechnen soll. FNV-1a ist dagegen in beiden Sprachen mit
/// derselben Konstantenfolge trivial identisch nachbaubar. `pub(crate)`, weil
/// A3 (`features.rs`s Feature-Golden-Hash-Test) denselben Algorithmus
/// wiederverwendet, statt einen zweiten zu bauen (gleiche Begründung: kein
/// bitgenauer/instabiler Hash für einen Golden-Test).
pub(crate) fn fnv1a_64(s: &str) -> u64 {
    const FNV_OFFSET_BASIS: u64 = 0xcbf29ce484222325;
    const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;
    let mut hash = FNV_OFFSET_BASIS;
    for byte in s.as_bytes() {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

/// A2-Vertragsstempel: FNV-1a-64-Hash (siehe [`fnv1a_64`]) über
/// [`contract_canonical_string`], als 16-stelliger Hex-String -- so über
/// `engine_config_json()`s Feld `contract_hash` exponiert. Ein Werkzeug kann
/// damit das INSTALLIERTE Binary fragen, welchen Eingabe-/Kopf-Vertrag es
/// tatsächlich implementiert, statt sich auf einen `grep` über den
/// Quellstand zu verlassen (der ein älteres installiertes Wheel nicht sehen
/// würde -- genau der Ist-Betrieb-Vorfall, der A2 motiviert, siehe
/// Design-Dokument Abschnitt "A2").
pub(crate) fn contract_hash() -> String {
    format!("{:016x}", fnv1a_64(&contract_canonical_string()))
}

/// Snapshot der aktiv wirksamen Rust-Suchkonstanten als JSON -- für
/// `self_play.py`s Lauf-Manifest (#64 Teil 1, Phase 2a, 2026-07-22): ein
/// Self-Play-Lauf soll rückwirkend rekonstruierbar sein (welche Engine-
/// Konfiguration hat DIESE Daten erzeugt), ohne den Rust-Quellcode zum
/// jeweiligen Commit-Stand extra auschecken zu müssen. Reines Auslesen
/// bestehender `pub`/`pub(crate)`-Konstanten aus `net_mcts.rs`/
/// `round_transition.rs`/`round_transition_deep.rs` -- kein Spielzustand
/// nötig, keine neue Suchlogik. A2-Ergänzung (`DESIGN_konventionen_als_
/// pruefungen.md`): `input_size`/`num_planes_channels`/`contract_hash` --
/// alle drei rein additiv (bestehende Schlüssel unverändert), betreffen NUR
/// dieses `engine_config_json()`, nicht `net_search_state_json`/`_trace`
/// (die Paritäts-Probe hasht ausschließlich Letztere, bleibt also unberührt).
#[pyfunction]
fn engine_config_json() -> String {
    use crate::net_mcts::{
        ACTIVE_LEAF, DECOUPLE_NET_SIMS_FROM_ACTIONS, DETERMINIZE_ROOT_HIDDEN_INFO,
        FLOOR_SHAPING_WEIGHT, GUMBEL_TOP_M, LeafEval, MIRROR_OTHER_VAL, NUM_ACTIONS,
        POINTS_UTILITY_WEIGHT, POLICY_MASS_CUTOFF, ROUND_TRANSITION_SAMPLING,
        SHUFFLE_STACK_PEEK_IN_SEARCH, USE_GUMBEL_SEARCH, VALUE_OPP_EPSILON,
        aggr_lambda, points_utility_w, value_cal_a, value_cal_b,
    };
    let active_leaf = match ACTIVE_LEAF {
        LeafEval::Net => "Net",
        LeafEval::Dfs => "Dfs",
    };
    json!({
        "engine_version": env!("CARGO_PKG_VERSION"),
        // A2 (siehe Funktions-Doku oben): Laufzeit-Vertragsstempel.
        "input_size": crate::features::INPUT_SIZE,
        "num_planes_channels": crate::features::NUM_PLANES_CHANNELS,
        "contract_hash": contract_hash(),
        "num_actions": NUM_ACTIONS,
        "active_leaf": active_leaf,
        "use_gumbel_search": USE_GUMBEL_SEARCH,
        "gumbel_top_m": GUMBEL_TOP_M,
        "decouple_net_sims_from_actions": DECOUPLE_NET_SIMS_FROM_ACTIONS,
        "floor_shaping_weight": FLOOR_SHAPING_WEIGHT,
        "points_utility_weight": POINTS_UTILITY_WEIGHT,
        // Task #28 (PREREG_task28_aggression.md): LAUFZEIT-Nachfolger von
        // `points_utility_weight` (siehe dortiger Kommentar) -- INITIAL aus
        // `MOSAIC_POINTS_UTILITY_W`/`MOSAIC_AGGR_LAMBDA` gelesen, danach per
        // `set_aggression_params` (GUI-Regler) jederzeit neu setzbar (Atomic-
        // Zellen, siehe `net_mcts.rs`). Beide 0.0, solange weder Env-Var
        // noch Regler gesetzt wurden (byte-identisches Bestandsverhalten).
        "points_utility_w": points_utility_w(),
        "aggr_lambda": aggr_lambda(),
        "value_opp_epsilon": VALUE_OPP_EPSILON,
        // Task #30 (`evaluations/STATUS.md` Abschnitt "Task #30"): monotone
        // Logit-Skalen-Korrektur des Value-Kopf-Outputs. Aus
        // `MOSAIC_VALUE_CAL_A`/`MOSAIC_VALUE_CAL_B` gelesen, einmalig gecacht.
        // Defaults 0.0/1.0, solange die Env-Vars nicht gesetzt sind
        // (byte-identisches Bestandsverhalten).
        "value_cal_a": value_cal_a(),
        "value_cal_b": value_cal_b(),
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

/// GUI-Aggressivitäts-Regler (Task #28, `PREREG_task28_aggression.md` Punkt 4
/// + `evaluations/STATUS.md` Abschnitt "Task #28 DURCHGEFUEHRT"): setzt die
/// beiden Laufzeit-Parameter des Score-/Denial-Utility-Blends SOFORT neu
/// (nächste PUCT-Blattauswertung sieht den neuen Wert, kein Server-/Prozess-
/// Neustart nötig) — dünner Wrapper um `net_mcts::set_aggression_params`,
/// das die Werte defensiv klemmt (`w` in `[0,1]`, `lambda_aggr` in `[0,5]`,
/// nicht-endliche Eingaben fallen auf `0.0` zurück, siehe dortige Doku).
/// Wirkt nur bei einem geladenen Netz MIT `opp_points`-Kopf — bei einem
/// Legacy-Modell ohne den Kopf verhält sich jeder `w>0` wie `w=0` (Additiv-
/// Regel, einmalige Warnung auf stderr, siehe `net_mcts::blended_leaf_win_
/// prob_with`-Doku). Persistiert NICHT über einen Serverneustart hinweg —
/// nach einem Neustart gelten wieder die `MOSAIC_POINTS_UTILITY_W`/
/// `MOSAIC_AGGR_LAMBDA`-Env-Var-Defaults (Server-seitig dokumentiert in
/// `server.py`).
#[pyfunction]
fn set_aggression_params(w: f64, lambda_aggr: f64) {
    crate::net_mcts::set_aggression_params(w, lambda_aggr);
}

/// Gegenstück zu [`set_aggression_params`]: liest die aktuell aktiven
/// `(w, lambda_aggr)`-Werte (nach Klemmung) — für den GET-Endpunkt der GUI
/// (`server.py::get_aggression`), damit der Regler beim Öffnen der
/// Einstellungen den tatsächlichen Serverzustand anzeigt statt eines
/// hart kodierten Defaults.
#[pyfunction]
fn get_aggression_params() -> (f64, f64) {
    crate::net_mcts::get_aggression_params()
}

/// Liest den Denial-Tie-Break-Debug-Zaehler (`net_mcts::denial_tiebreak_
/// stats`) aus Python -- Stufe-1-Instrument aus
/// `evaluations/PREREG_denial_tiebreak.md` (Abschnitt "E3b", "Feuerrate
/// messen"), ohne Log-Parsing. War bislang NICHT nach Python gebunden
/// (Engine-Task E3b, 2026-08-08) -- der Zaehler existierte schon (E3), aber
/// nur ueber Rust-interne Tests erreichbar. `(fired, total)`: `fired` =
/// Anzahl der Suchentscheidungen, bei denen der Tie-Break tatsaechlich eine
/// ANDERE Aktion als die Gumbel-Basisaktion gewaehlt hat, `total` = Anzahl
/// aller ausgewerteten Entscheidungen. E3 (`MOSAIC_DENIAL_TIEBREAK_EPS`) und
/// E3b (`MOSAIC_DENIAL_UNCERT_Z`) teilen sich denselben prozessweiten
/// Zaehler -- die beiden Mechanismen sind gegenseitig exklusiv (siehe
/// `net_mcts::apply_denial_tiebreak`s Abbruch bei beiden `>0`), ein
/// gemeinsamer Zaehler vermischt also nie Ergebnisse zweier Mechanismen.
#[pyfunction]
fn denial_tiebreak_stats() -> (u64, u64) {
    crate::net_mcts::denial_tiebreak_stats()
}

/// Setzt den Denial-Tie-Break-Debug-Zaehler zurueck -- vor einem zu
/// messenden Lauf aufrufen (Feuerrate-Messung, siehe
/// `evaluations/PREREG_denial_tiebreak.md` Abschnitt "E3b", Stufe 1).
#[pyfunction]
fn reset_denial_tiebreak_stats() {
    crate::net_mcts::reset_denial_tiebreak_stats();
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

/// PREREG_r4_value_calibration.md, Abschnitt "Vorbedingung": invertiert die
/// Fabrik-Neubefüllung eines Runde-5-Startzustands (Übergang 4→5,
/// `state.rs::setup_new_round`/`fill_factories`) und sampelt `n_samples`
/// frische Neubefüllungen DESSELBEN Vor-Befüllungs-Bretts -- Grundlage für
/// die Runde-4-Ende-Ground-Truth (`ab_value` je Sample über `round5.rs`,
/// siehe PREREG-Dokument, Abschnitt "Ground Truth"). Additiv: es gab bisher
/// keinen Python-Einstieg für diese RÜCKWÄRTS-Richtung (nur
/// `advance_after_tiling_json` direkt oberhalb, die VORWÄRTS-Richtung
/// Tiling-Leaf → nächste Runde).
///
/// **BEFUND 2026-08-03 (Koordinator, 9000-Partien-Korpus): 87,6 % der echten
/// Runde-5-Starts haben einen leeren Turm** -- die Ausschlussregel dieser
/// Funktion (Turm-Reshuffle-Grenzfall, siehe
/// `round_transition_resample`-Moduldoku) würde also fast das ganze
/// PREREG-Substrat verwerfen. Diese Funktion bleibt additiv erhalten (für den
/// verbleibenden ~12,4%-Fall weiterhin exakt), der PREREG-r4-Pfad selbst
/// nutzt aber ab jetzt [`autoplay_to_round5_and_resample_json`] weiter unten
/// (Vorwärts-Pfad ab dem echten Runde-4-Zustand, umgeht die Turm-Ambiguität
/// komplett, siehe dortige Doku).
///
/// `r5_start_state_json` muss ein UNBERÜHRTER Runde-5-Start sein (Phase
/// Drafting, `round==5`, alle Fabriken frisch befüllt: 4 kleine × 4
/// Sonnenplättchen + große × 5, kein Mond-Vorrat, Bonuschips unaufgedeckt) --
/// siehe `round_transition_resample::invert_round5_fill` für die exakte
/// Validierung inkl. Turm-Reshuffle-Grenzfall (PREREG "Bekannte
/// Einschränkungen": mehrdeutig invertierbare Zustände geben `Err` statt
/// einer stillen Näherung, s. dortiger Moduldoku-Kommentar). `seed` treibt
/// sowohl die `json_to_state`-Rekonstruktion der (für die Fabrik-Inversion
/// irrelevanten) verdeckten Sammlungen als auch, je Sample-Index
/// deterministisch abgeleitet (`seed + i`), die eigentliche Neubefüllung.
/// Rückgabe: JSON-Array von `n_samples` `state_to_json`-Zustandsdicts
/// (dasselbe Format, das `json_to_state`/`net_search_state_json` wieder
/// einliest).
#[pyfunction]
#[pyo3(signature = (r5_start_state_json, n_samples, seed))]
fn resample_round_transition_json(
    r5_start_state_json: &str,
    n_samples: u32,
    seed: u64,
) -> PyResult<String> {
    use pyo3::exceptions::PyValueError;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    let mut recon_rng = StdRng::seed_from_u64(seed);
    let parsed: serde_json::Value = serde_json::from_str(r5_start_state_json).map_err(|e| {
        PyValueError::new_err(format!("r5_start_state_json: JSON-Parse-Fehler: {e}"))
    })?;
    let state = crate::serialize::json_to_state(&parsed, &mut recon_rng).map_err(PyValueError::new_err)?;

    let samples =
        crate::round_transition_resample::resample_round5_start(&state, n_samples, seed)
            .map_err(PyValueError::new_err)?;

    let out: Vec<serde_json::Value> = samples
        .iter()
        .map(|s| crate::serialize::state_to_json(s, true))
        .collect();
    Ok(serde_json::Value::Array(out).to_string())
}

/// PREREG_r4_value_calibration.md, Vorbedingung -- VORWÄRTS-Ersatz für
/// [`resample_round_transition_json`] (siehe dessen Doku für den
/// 87,6%-Turm-leer-Befund, der die Inversion für das PREREG-Substrat
/// praktisch unbrauchbar macht). Setzt beim echten "letzten R4-Record"
/// (`round==4`, `phase=="tiling"`, PREREG "Positions-Substrat") an, wo
/// Beutel/Turm noch als EXAKTE Multisets bekannt sind (kein
/// Zähler-Rekonstruktions-Verlust) -- keine Inversion, keine
/// Ausschlussregel, der natürliche Beutel-leer→Turm-Reshuffle-Pfad läuft
/// beim Resampling einfach mit.
///
/// Nutzt ausschließlich bestehende Bausteine (`round_transition::
/// resolve_to_pre_chance` + `advance_one_chance`), siehe
/// `round_transition_resample::autoplay_to_round5_and_resample` für die
/// vollständige Doku (RNG-Freiheit des deterministischen Vorlaufs dort
/// explizit geprüft, nicht nur behauptet).
///
/// Rückgabe: EIN JSON-OBJEKT (bewusst kein bloßes Array, um den
/// R4-Ende-Zustand nicht implizit als "Element 0" zu verstecken):
/// ```json
/// {
///   "r4_end_state": <state_to_json des deterministisch erreichten
///                     Runde-4-Ende-Zustands -- round==4, phase=="tiling",
///                     EIN EndTiling-Aufruf steht noch aus; Strafen/
///                     Boden-Abwürfe NOCH NICHT angewendet, siehe
///                     autoplay_to_round5_and_resample-Doku>,
///   "r5_samples": [<state_to_json>, ... n_samples Runde-5-Start-Zustände]
/// }
/// ```
/// `r4_end_state` ist für den Python-seitigen Konsistenz-Check gedacht
/// (PREREG "Konsistenz der beiden Seiten": muss modulo Befüllung zum ersten
/// echten Runde-5-Record der Partie passen).
#[pyfunction]
#[pyo3(signature = (r4_state_json, n_samples, seed))]
fn autoplay_to_round5_and_resample_json(
    r4_state_json: &str,
    n_samples: u32,
    seed: u64,
) -> PyResult<String> {
    use pyo3::exceptions::PyValueError;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    let mut recon_rng = StdRng::seed_from_u64(seed);
    let parsed: serde_json::Value = serde_json::from_str(r4_state_json)
        .map_err(|e| PyValueError::new_err(format!("r4_state_json: JSON-Parse-Fehler: {e}")))?;
    let state = crate::serialize::json_to_state(&parsed, &mut recon_rng).map_err(PyValueError::new_err)?;

    let (r4_end_state, samples) =
        crate::round_transition_resample::autoplay_to_round5_and_resample(&state, n_samples, seed)
            .map_err(PyValueError::new_err)?;

    let out = json!({
        "r4_end_state": crate::serialize::state_to_json(&r4_end_state, true),
        "r5_samples": samples
            .iter()
            .map(|s| crate::serialize::state_to_json(s, true))
            .collect::<Vec<_>>(),
    });
    Ok(out.to_string())
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
    m.add_function(wrap_pyfunction!(set_aggression_params, m)?)?;
    m.add_function(wrap_pyfunction!(get_aggression_params, m)?)?;
    m.add_function(wrap_pyfunction!(denial_tiebreak_stats, m)?)?;
    m.add_function(wrap_pyfunction!(reset_denial_tiebreak_stats, m)?)?;
    m.add_function(wrap_pyfunction!(net_search_state_json, m)?)?;
    m.add_function(wrap_pyfunction!(net_search_state_json_trace, m)?)?;
    m.add_function(wrap_pyfunction!(tiling_candidates_json, m)?)?;
    m.add_function(wrap_pyfunction!(advance_after_tiling_json, m)?)?;
    m.add_function(wrap_pyfunction!(resample_round_transition_json, m)?)?;
    m.add_function(wrap_pyfunction!(autoplay_to_round5_and_resample_json, m)?)?;
    m.add_function(wrap_pyfunction!(end_scoring_from_state_json, m)?)?;
    m.add_function(wrap_pyfunction!(selfplay_profile_reset, m)?)?;
    m.add_function(wrap_pyfunction!(selfplay_profile_json, m)?)?;
    m.add_class::<crate::py::PyGame>()?;
    Ok(())
}

#[cfg(test)]
mod contract_stamp_tests {
    use super::*;

    /// A2-Golden-Waechter (`evaluations/DESIGN_konventionen_als_pruefungen.md`
    /// Abschnitt "A2"): haelt den HEUTIGEN Vertragshash als Literal fest.
    /// Aendert sich `INPUT_SIZE`, `NUM_PLANES_CHANNELS`, `NUM_ACTIONS` ODER
    /// die in `contract_canonical_string` nachgebildete ONNX-Kopf-
    /// Interpretation von `net.rs`, wird dieser Test ROT --
    /// KONSEQUENZ: Bestandschampions (bereits trainierte/gegatete .onnx-
    /// Checkpoints) bekommen dann andere Eingaben/Kopf-Zuordnungen als die,
    /// mit denen sie trainiert/gegatet wurden -- vor einem bewussten Update
    /// dieses Literals pruefen, ob genau das beabsichtigt ist (neue
    /// Modellgeneration) oder ein Versehen (siehe Design-Dokument Abschnitt
    /// "A2" fuer die zwei realen Vorfaelle, die diesen Waechter motivieren).
    #[test]
    fn contract_hash_matches_pinned_literal() {
        assert_eq!(
            contract_hash(),
            "a169ebf0a4451e08",
            "A2-Vertragshash hat sich veraendert -- Bestandschampions bekommen \
             andere Eingaben (siehe Testdoku)"
        );
    }

    /// Gegenprobe-Beleg (nicht Teil der eigentlichen Pruefung, sondern
    /// Dokumentation): der Hash haengt tatsaechlich von den Vertragsgroessen
    /// ab -- ein anderer `NUM_ACTIONS`-Wert aendert die kanonische
    /// Zeichenkette (und damit den Hash) nachweislich.
    #[test]
    fn contract_canonical_string_reflects_current_constants() {
        let s = contract_canonical_string();
        assert!(s.contains(&format!("INPUT_SIZE={}", crate::features::INPUT_SIZE)));
        assert!(s.contains(&format!("NUM_PLANES_CHANNELS={}", crate::features::NUM_PLANES_CHANNELS)));
        assert!(s.contains(&format!("NUM_ACTIONS={}", crate::net_mcts::NUM_ACTIONS)));
        assert!(s.contains("HEADS=policy,value,moon,points,opp_points"));
    }

    /// `engine_config_json()` muss den IDENTISCHEN Hash exponieren, den
    /// [`contract_hash`] direkt liefert -- die JSON-Extraktion ist reines
    /// Auslesen, keine zweite Berechnung.
    #[test]
    fn engine_config_json_exposes_matching_contract_hash() {
        let json_str = engine_config_json();
        let parsed: serde_json::Value = serde_json::from_str(&json_str).expect("gueltiges JSON");
        assert_eq!(parsed["contract_hash"].as_str(), Some(contract_hash().as_str()));
        assert_eq!(parsed["input_size"].as_u64(), Some(crate::features::INPUT_SIZE as u64));
        assert_eq!(
            parsed["num_planes_channels"].as_u64(),
            Some(crate::features::NUM_PLANES_CHANNELS as u64)
        );
    }
}
