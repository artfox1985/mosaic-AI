//! ENDE-ZU-ENDE-SELF-PLAY-DURCHSATZ (Auftrag 2026-08-12,
//! `evaluations/PREREG_gpu_inference_path.md` -- v.a. §9 Messplan-Fehler, §13
//! TF32, §18 Nutzer-Entscheid "Batcher fuer Self-Play an, Arena/Gating aus").
//!
//! Ruft `self_play::run_self_play_with_net_labels` DIREKT auf (der Auftrag
//! nennt zusaetzlich `run_self_play` -- das laesst `net: None` fest verdrahtet
//! (self_play.rs, `play`-Closure der `run_self_play`-Funktion) und fuehrt
//! daher NIE einen Netz-Forward-Pass aus; fuer eine GPU-Durchsatzmessung ist
//! nur `run_self_play_with_net_labels` ueberhaupt aussagekraeftig, siehe
//! Bericht Punkt 5).
//!
//! ## GEPRUEFTER BEFUND, BEVOR HIER IRGENDETWAS GEMESSEN WIRD
//!
//! `run_self_play_with_net_labels` (self_play.rs) ruft an KEINER Stelle
//! `net_batcher::ensure_batcher_for` auf (volltextgelesen, self_play.rs
//! Zeilen 1343-1410 -- kein Treffer). Damit registriert sich fuer das intern
//! erzeugte `Arc<Net>` NIE ein Sammel-Faden, und `net_batcher::lookup`
//! (aufgerufen aus `net_mcts::try_batched_single_eval`/`try_batched_pair_ex`,
//! net_mcts.rs:1930-1970) liefert IMMER `None` -- jeder Aufruf faellt auf den
//! synchronen `Net::eval`/`eval_pair_ex`/`eval_ex`-Pfad zurueck.
//!
//! Diese drei Methoden (net.rs:376/406/551) benutzen `self.model`/
//! `self.model_pair` DIREKT -- eigene, dedizierte tract-Plaene, komplett ohne
//! den ORT-CUDA-/Torch-IPC-Haken. Dieser Haken lebt AUSSCHLIESSLICH in
//! `Net::eval_batch` (net.rs:451-510, Haken-Zeilen 469-477). Der einzige
//! Produktions-Aufrufer von `eval_batch` ist der Sammel-Faden selbst
//! (`net_batcher.rs::collector_loop`, Zeile 174) -- und der existiert nur,
//! wenn `ensure_batcher_for` fuer GENAU dieses `Arc<Net>` gelaufen ist.
//!
//! **Folge**: fuer `run_self_play`/`run_self_play_with_net_labels`, WIE SIE
//! HEUTE VERDRAHTET SIND, haben `MOSAIC_INTERLEAVE_ENABLED` UND
//! `MOSAIC_ORT_CUDA_ENABLED` STRUKTURELL keine Wirkung -- unabhaengig vom
//! gemessenen Wert. Arm (a) und Arm (b) fuehren fuer diese beiden Funktionen
//! byte-identischen Code aus.
//!
//! Dieses Programm misst darum DREI Arme, nicht zwei -- der dritte ist eine
//! EIGENE, nicht angeforderte Entscheidung (siehe Bericht Punkt 5),
//! notwendig, um die Frage "haette der Batcher hier ueberhaupt einen Effekt"
//! trotzdem zu beantworten, OHNE `self_play.rs` anzufassen (Auftrag: "nichts
//! umbauen"):
//!
//! - **`a`**: Bestand. Keine Env-Vars gesetzt. `run_self_play_with_net_labels`
//!   direkt.
//! - **`b_literal`**: `MOSAIC_INTERLEAVE_ENABLED=1` + `MOSAIC_ORT_CUDA_ENABLED=1`
//!   gesetzt, ABER `run_self_play_with_net_labels` direkt (wie Auftrag es
//!   verlangt) -- nach obigem Befund erwartbar IDENTISCH zu `a`.
//! - **`b_wired`**: dieselben Env-Vars, aber der Sammel-Faden wird VOR dem
//!   Spiel-Loop per `net_batcher::ensure_batcher_for(&net_arc)` fuer das
//!   SELBST geladene `Arc<Net>` registriert -- danach `play_one_game`
//!   (self_play.rs, `pub fn`) mit EXAKT derselben Seed-/Setup-Logik wie die
//!   `play`-Closure in `run_self_play_with_net_labels` (Zeilen 1366-1396,
//!   hier Zeile fuer Zeile gespiegelt) aufgerufen -- nur mit dem einen
//!   zusaetzlichen Registrierungsschritt. Ausschliesslich `pub`-Bausteine
//!   verwendet (`Net::load_auto`, `play_one_game`, `ensure_batcher_for`,
//!   `sample_valid_scoring_ids`, `set_game_shaping_weight`), keine Datei
//!   im Bestand geaendert.
//!
//! ## Aufruf
//!   cargo build --release --example self_play_throughput_probe --features ort_cuda_probe
//!   <exe> --arm a|b_literal|b_wired --threads N --games N --sims N --seed N \
//!         --model <pfad.onnx> --out <ergebnis.jsonl>
//!
//! `--features ort_cuda_probe` wird nur fuer die LIB gebraucht (schaltet
//! `net_ort.rs`/den ORT-CUDA-Haken in `net.rs::eval_batch` frei) -- diese
//! Probe-Datei selbst importiert `ort` nicht, keine `required-features`-
//! Eintragung in `Cargo.toml` noetig.

use std::env;
use std::fs::OpenOptions;
use std::io::Write as _;
use std::sync::Arc;
use std::time::Instant;

use mosaic_rust::net::Net;
use mosaic_rust::net_batcher;
use mosaic_rust::scoring::sample_valid_scoring_ids;
use mosaic_rust::self_play::{play_one_game, run_self_play_with_net_labels, SELF_PLAY_C};
use rand::rngs::StdRng;
use rand::{RngExt, SeedableRng};
use rayon::prelude::*;
use serde_json::Value;

struct Args {
    arm: String,
    threads: usize,
    games: usize,
    sims: u32,
    seed: u64,
    model: String,
    out: String,
    record_rtv: bool,
}

fn parse_args() -> Args {
    let mut arm = "a".to_string();
    let mut threads = 11usize;
    let mut games = 20usize;
    let mut sims = 30u32;
    let mut seed = 20260812u64;
    let mut model = "../models/alphazero_v20_2d_opp_brierbest.onnx".to_string();
    let mut out = "../evaluations/self_play_throughput_e2e.jsonl".to_string();
    let mut record_rtv = false;

    let mut it = env::args().skip(1);
    while let Some(flag) = it.next() {
        match flag.as_str() {
            "--arm" => arm = it.next().expect("--arm braucht einen Wert"),
            "--threads" => threads = it.next().unwrap().parse().unwrap(),
            "--games" => games = it.next().unwrap().parse().unwrap(),
            "--sims" => sims = it.next().unwrap().parse().unwrap(),
            "--seed" => seed = it.next().unwrap().parse().unwrap(),
            "--model" => model = it.next().unwrap(),
            "--out" => out = it.next().unwrap(),
            "--record-rtv" => record_rtv = true,
            other => panic!("unbekanntes Argument: {other}"),
        }
    }
    Args { arm, threads, games, sims, seed, model, out, record_rtv }
}

/// Setzt die Env-Vars fuer den gewaehlten Arm -- MUSS vor JEDEM Aufruf in
/// `net_batcher`/`net_ort` (die ihre Env-Reads in `OnceLock` cachen) passieren.
/// Da dieses Programm pro Messpunkt als EIGENER Prozess laeuft (siehe
/// Orchestrierung aussenherum), ist "beim Prozessstart setzen" aequivalent zu
/// "in der Shell setzen", ohne dass irgendein Aufrufer mehrfach im selben
/// Prozess mit unterschiedlichem Zustand laufen muesste.
fn set_arm_env(arm: &str) {
    match arm {
        "a" => {
            // Bestand: nichts setzen. (Falls die Shell selbst schon etwas
            // exportiert hat, wird das hier NICHT zurueckgesetzt -- fuer
            // diese Probe wird davon ausgegangen, dass die Umgebung sauber
            // ist; die Orchestrierung aussenherum startet jeden Lauf ohne
            // die drei MOSAIC_*-Vars.)
        }
        "b_literal" | "b_wired" => {
            env::set_var("MOSAIC_INTERLEAVE_ENABLED", "1");
            env::set_var("MOSAIC_ORT_CUDA_ENABLED", "1");
            // Torch/IPC (Weg A) explizit AUS -- Regel 3 hat ihn schon
            // verworfen (PREREG §9), er soll den ORT-CUDA-Pfad hier nicht
            // verdecken (net.rs::eval_batch prueft ORT-CUDA zwar zuerst,
            // aber sauberer, den zweiten Kanal erst gar nicht scharf zu
            // schalten).
            env::set_var("MOSAIC_TORCH_IPC_ENABLED", "0");
        }
        other => panic!("unbekannter Arm: {other}"),
    }
}

/// Zaehlt Spiele mit `"completed": true` im flachen Step-Records-Array --
/// Qualitaets-Kennzahl (Haenger-Schutz kann Partien vorzeitig abschneiden),
/// NICHT der Nenner fuer den Durchsatz (der ist `n_games`, siehe `main`s
/// Kommentar an der Durchsatzberechnung).
fn count_completed_games(records_json: &str) -> (usize, usize) {
    let arr: Value = match serde_json::from_str(records_json) {
        Ok(v) => v,
        Err(_) => return (0, 0),
    };
    let mut game_ids = std::collections::HashSet::new();
    let mut completed_ids = std::collections::HashSet::new();
    if let Value::Array(rows) = arr {
        for row in rows {
            if let Some(gid) = row.get("game_id").and_then(|v| v.as_str()) {
                game_ids.insert(gid.to_string());
                if row.get("completed").and_then(|v| v.as_bool()) == Some(true) {
                    completed_ids.insert(gid.to_string());
                }
            }
        }
    }
    (game_ids.len(), completed_ids.len())
}

/// EXAKTE Spiegelung der `play`-Closure aus
/// `self_play::run_self_play_with_net_labels` (self_play.rs Zeilen
/// 1366-1396) -- einzige Abweichung: `net` kommt von AUSSEN (bereits
/// registrierter Batcher) statt intern in derselben Funktion geladen zu
/// werden. `move_heartbeat: None` (kein Fortschritts-Tracking noetig fuer
/// eine Durchsatzmessung).
fn play_one(
    net: &Net,
    base_sims: u32,
    c: f64,
    seed: u64,
    prefix: &str,
    record_rtv: bool,
    i: usize,
) -> Vec<Value> {
    let partie_seed = seed.wrapping_add((i as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15));
    let streuung_max = mosaic_rust::net_mcts::scoring_scatter_max();
    mosaic_rust::net_mcts::set_game_shaping_weight(if streuung_max > 0.0 {
        Some(mosaic_rust::net_mcts::game_weight_from_seed(partie_seed, streuung_max))
    } else {
        None
    });
    let mut rng = StdRng::seed_from_u64(partie_seed);
    let ids = sample_valid_scoring_ids(3, &mut rng);
    let first = rng.random_range(0..2usize);
    let names = ["Spieler 1".to_string(), "Spieler 2".to_string()];
    let gid = format!("{prefix}_g{}", i + 1);
    // V1 = Bestandsverhalten dieser Sonde; `play_one_game` nimmt die
    // Heuristik-Variante seit 2026-08-25 als Parameter (STATUS
    // "v22-Vorbereitung" Punkt 2).
    play_one_game(
        base_sims, c, ids, names, first, &gid, &mut rng, Some(net), record_rtv, None,
        mosaic_rust::mcts::HeuristikVariante::V1, partie_seed,
    )
}

fn main() {
    let args = parse_args();
    set_arm_env(&args.arm);

    let gpu_before = gpu_snapshot();

    match args.arm.as_str() {
        "a" | "b_literal" => {
            let t0 = Instant::now();
            let out = run_self_play_with_net_labels(
                &args.model,
                args.games,
                args.sims,
                SELF_PLAY_C,
                args.seed,
                args.threads,
                &format!("thrpt_{}_{}", args.arm, args.threads),
                args.record_rtv,
                None,
                None,
            )
            .expect("run_self_play_with_net_labels sollte nicht fehlschlagen");
            let dt = t0.elapsed();
            let (n_seen, n_completed) = count_completed_games(&out);
            report(&args, dt, n_seen, n_completed, None, gpu_before, gpu_snapshot());
        }
        "b_wired" => {
            let net = Net::load_auto(&args.model).expect("Modell sollte ladbar sein");
            let net = Arc::new(net);
            // Der eine zusaetzliche Schritt gegenueber der `a`/`b_literal`-
            // Aufrufform: den Sammel-Faden FUER DIESES Arc<Net> registrieren.
            // No-Op, falls MOSAIC_INTERLEAVE_ENABLED nicht gesetzt ist (hier
            // aber gesetzt, siehe `set_arm_env`).
            net_batcher::ensure_batcher_for(&net);

            let prefix = format!("thrpt_{}_{}", args.arm, args.threads);
            let net_ref = &net;
            let prefix_ref = &prefix;
            let play = |i: usize| -> Vec<Value> {
                play_one(net_ref, args.sims, SELF_PLAY_C, args.seed, prefix_ref, args.record_rtv, i)
            };

            let t0 = Instant::now();
            let all: Vec<Vec<Value>> = if args.threads == 0 {
                (0..args.games).into_par_iter().map(play).collect()
            } else {
                rayon::ThreadPoolBuilder::new()
                    .num_threads(args.threads)
                    .build()
                    .expect("Rayon-Pool sollte baubar sein")
                    .install(|| (0..args.games).into_par_iter().map(play).collect())
            };
            let dt = t0.elapsed();

            let flat: Vec<Value> = all.into_iter().flatten().collect();
            let out = serde_json::to_string(&Value::Array(flat)).unwrap_or_else(|_| "[]".to_string());
            let (n_seen, n_completed) = count_completed_games(&out);

            let batch_stats = net_batcher::lookup(&net).map(|b| {
                (
                    b.stats.batches.load(std::sync::atomic::Ordering::Relaxed),
                    b.stats.rows.load(std::sync::atomic::Ordering::Relaxed),
                    b.stats.mean_batch(),
                    b.stats.max_batch_seen.load(std::sync::atomic::Ordering::Relaxed),
                )
            });
            report(&args, dt, n_seen, n_completed, batch_stats, gpu_before, gpu_snapshot());
        }
        other => panic!("unbekannter Arm: {other}"),
    }
}

/// `nvidia-smi`-Schnappschuss vor/nach dem Lauf -- fortlaufendes Mitschneiden
/// waehrend des Laufs macht die AUSSENHERUM-Orchestrierung (Bash, `nvidia-smi
/// -l 1` in eine Log-Datei), nicht dieses Programm selbst (kein zusaetzlicher
/// Kind-Prozess/Thread hier, um die Messung selbst nicht zu stoeren).
fn gpu_snapshot() -> String {
    std::process::Command::new("nvidia-smi")
        .args(["--query-gpu=utilization.gpu,memory.used,power.draw", "--format=csv,noheader"])
        .output()
        .ok()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
        .unwrap_or_else(|| "n/a".to_string())
}

#[allow(clippy::too_many_arguments)]
fn report(
    args: &Args,
    dt: std::time::Duration,
    n_seen: usize,
    n_completed: usize,
    batch_stats: Option<(u64, u64, f64, usize)>,
    gpu_before: String,
    gpu_after: String,
) {
    let secs = dt.as_secs_f64();
    // Durchsatz-Nenner ist `n_games` (angeforderte Partien), NICHT `n_seen`/
    // `n_completed` -- die Wandzeit `dt` deckt bereits ALLE angeforderten
    // Partien ab (Rayon wartet auf jeden Task), unabhaengig davon, ob eine
    // einzelne Partie durch den Haenger-Schutz vorzeitig endet.
    let games_per_hour = args.games as f64 / secs * 3600.0;

    println!(
        "arm={} threads={} games={} sims={} dt_s={:.2} games_per_hour={:.1} seen={} completed={} gpu_vorher=[{}] gpu_nachher=[{}]",
        args.arm, args.threads, args.games, args.sims, secs, games_per_hour, n_seen, n_completed, gpu_before, gpu_after
    );
    match batch_stats {
        Some((batches, rows, mean_batch, max_batch)) => {
            println!(
                "  batcher_stats: batches={batches} rows={rows} mean_batch={mean_batch:.3} max_batch_seen={max_batch}"
            );
        }
        None => println!("  batcher_stats: n/a (kein Sammel-Faden fuer dieses Arc<Net> registriert)"),
    }

    let record = serde_json::json!({
        "arm": args.arm,
        "threads": args.threads,
        "games": args.games,
        "sims": args.sims,
        "seed": args.seed,
        "record_rtv": args.record_rtv,
        "model": args.model,
        "dt_s": secs,
        "games_per_hour": games_per_hour,
        "games_seen": n_seen,
        "games_completed": n_completed,
        "batcher_batches": batch_stats.map(|b| b.0),
        "batcher_rows": batch_stats.map(|b| b.1),
        "batcher_mean_batch": batch_stats.map(|b| b.2),
        "batcher_max_batch_seen": batch_stats.map(|b| b.3),
        "gpu_before": gpu_before,
        "gpu_after": gpu_after,
    });
    if let Some(parent) = std::path::Path::new(&args.out).parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    let mut f = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&args.out)
        .expect("Ausgabedatei sollte schreibbar sein");
    writeln!(f, "{record}").expect("Zeile sollte schreibbar sein");
}
