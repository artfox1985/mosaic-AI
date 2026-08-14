//! PROBELAUF (PREREG_gpu_inference_path.md §5-Vorbedingung, Auftrag 2026-08-12):
//! testet NUR die Nebenlaeufigkeits-MECHANIK der geplanten Verschraenkung --
//! N Faeden legen Dummy-Anfragen in eine gemeinsame Warteschlange und
//! blockieren auf einem Antwort-Kanal, ein Sammel-Faden holt bis zu
//! `batch_max` davon, tut eine feste Arbeit als GPU-Ersatz, schickt Antworten
//! zurueck. KEINE Suche, KEIN Netz, KEIN IPC, KEINE Aenderung an
//! net_mcts.rs/self_play.rs -- reine Warteschlangen-Mechanik.
//!
//! Fragen (siehe Auftrag):
//!   1. Erreicht der mittlere Batch tatsaechlich ~N?
//!   2. Waechst der Durchsatz mit N wie erwartet, oder bricht er ab einem N ein?
//!   3. Bei welchem N kippt es, falls es kippt?
//!
//! Aufruf: cargo run --release --example interleave_concurrency_probe
//! Schreibt JSON nach evaluations/interleave_concurrency_probe.json (Pfad
//! relativ zum Repo-Root, per --manifest-path-Konvention: cwd = engine/ beim
//! `cargo run`, daher `../evaluations/...`).

use std::sync::mpsc::{self, RecvTimeoutError};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

/// Echte Merkmalsvektor-Groesse. GEPRUEFT: engine/src/features.rs:911-916
/// (`state_to_features_2d_direct` = Planes 76*6*6=2736 + Flat INPUT_SIZE=708
/// (features.rs:18) = 3444).
const FEATURE_LEN: usize = 3444;

/// GPU-Ersatz: feste Arbeit pro Batch, UNABHAENGIG von der tatsaechlichen
/// Batch-Groesse -- laut Auftrag die gemessene GPU-Zeit fuer Batch 256.
/// Diese 3ms selbst sind in DIESER Sitzung NICHT nachgeprueft (ich habe
/// PREREG_gpu_offloading.md nicht geoeffnet) -- als Vorgabe des Auftrags
/// uebernommen, nicht selbst nachgemessen. Als UNGEPRUEFT markiert.
const GPU_SLEEP: Duration = Duration::from_millis(3);

/// EIGENE ENTSCHEIDUNG (nicht vom Auftrag vorgegeben): wie lange der
/// Sammel-Faden auf das NAECHSTE Element wartet, nachdem er mindestens eines
/// hat, bevor er den Batch abschickt ("Zeitueberschreitung, damit es nicht
/// haengt wenn zu wenige warten" -- Auftragstext). 200 Mikrosekunden: klar
/// unter der GPU-Ersatz-Zeit (3ms), damit diese Wartezeit die Batch-Fuellung
/// nicht selbst deckelt, aber lang genug fuer Kanal-Weck-Jitter.
const SLOT_TIMEOUT: Duration = Duration::from_micros(200);

/// EIGENE ENTSCHEIDUNG: Aufwaerm-Iterationen je Faden (Threads hochfahren,
/// eingeschwungener Zustand), NICHT mitgemessen.
const WARMUP_ITERS: u64 = 100;

/// EIGENE ENTSCHEIDUNG: gemessene Iterationen je Faden. Bei N=256 sind das
/// 256*2000 = 512.000 Einzelmessungen, bei N=11 sind es 22.000 -- in beiden
/// Faellen weit ueber dem, was fuer stabile Median/p95-Werte noetig ist.
const MEASURE_ITERS: u64 = 2000;

// `sent_at` wird bewusst NICHT im Request mitgeschickt: der Arbeits-Faden
// haelt sein eigenes `t0` lokal und braucht es nur dort (fuer queue_wait),
// der Sammel-Faden liest die Nutzlast nur zur Alloc-Kosten-Simulation.
struct Request {
    payload: Vec<f32>,
    resp_tx: mpsc::Sender<(Instant, usize, Duration)>,
}

#[derive(Clone, Copy)]
struct Sample {
    round_trip_us: f64,
    queue_wait_us: f64,
    service_us: f64,
    other_us: f64,
}

struct BatchStat {
    size: usize,
}

/// Sammel-Faden: zieht bis zu `batch_max` Anfragen, schlaeft `GPU_SLEEP` als
/// GPU-Ersatz, schickt an alle im Batch dieselbe (batch_start, batch_len,
/// gemessene service-Dauer) zurueck.
fn collector_loop(
    req_rx: mpsc::Receiver<Request>,
    batch_max: usize,
    total_requests: u64,
    batch_stats: Arc<Mutex<Vec<BatchStat>>>,
) {
    let mut processed: u64 = 0;
    while processed < total_requests {
        // Auf das erste Element eines neuen Batches warten. Timeout nur, um
        // die Schleife am Leben zu halten -- bei processed < total_requests
        // MUSS noch etwas kommen (die Faeden laufen deterministisch feste
        // Iterationszahlen), ein Timeout hier waere ein Bug, kein normaler Fall.
        let first = match req_rx.recv_timeout(Duration::from_secs(5)) {
            Ok(r) => r,
            Err(RecvTimeoutError::Timeout) => {
                eprintln!(
                    "WARNUNG: Sammel-Faden 5s ohne Anfrage bei processed={processed}/{total_requests} -- Deadlock-Verdacht"
                );
                continue;
            }
            Err(RecvTimeoutError::Disconnected) => break,
        };
        let mut batch = Vec::with_capacity(batch_max);
        batch.push(first);
        while batch.len() < batch_max {
            match req_rx.recv_timeout(SLOT_TIMEOUT) {
                Ok(r) => batch.push(r),
                Err(RecvTimeoutError::Timeout) => break,
                Err(RecvTimeoutError::Disconnected) => break,
            }
        }
        let batch_len = batch.len();
        let batch_start = Instant::now();
        thread::sleep(GPU_SLEEP);
        let service_elapsed = batch_start.elapsed();
        for r in &batch {
            // .len() beruehren, damit die Nutzlast nicht als toter Code
            // wegoptimiert werden kann (soll die Alloc/Kopier-Kosten der
            // echten Merkmalserzeugung nachbilden).
            std::hint::black_box(r.payload.len());
            let _ = r.resp_tx.send((batch_start, batch_len, service_elapsed));
        }
        processed += batch_len as u64;
        batch_stats.lock().unwrap().push(BatchStat { size: batch_len });
    }
}

fn worker_loop(
    req_tx: mpsc::Sender<Request>,
    warmup_iters: u64,
    measure_iters: u64,
    samples_out: Arc<Mutex<Vec<Sample>>>,
) {
    let template: Vec<f32> = (0..FEATURE_LEN).map(|i| (i as f32) * 0.001).collect();
    let (resp_tx, resp_rx) = mpsc::channel::<(Instant, usize, Duration)>();

    for _ in 0..warmup_iters {
        let t0 = Instant::now();
        let payload = template.clone();
        req_tx
            .send(Request { payload, resp_tx: resp_tx.clone() })
            .expect("Sammel-Faden sollte laufen (warmup)");
        let _ = resp_rx.recv().expect("Antwort sollte kommen (warmup)");
        let _ = t0;
    }

    let mut local_samples: Vec<Sample> = Vec::with_capacity(measure_iters as usize);
    for _ in 0..measure_iters {
        let t0 = Instant::now();
        let payload = template.clone();
        req_tx
            .send(Request { payload, resp_tx: resp_tx.clone() })
            .expect("Sammel-Faden sollte laufen (measure)");
        let (batch_start, _batch_len, service_dur) =
            resp_rx.recv().expect("Antwort sollte kommen (measure)");
        let t1 = Instant::now();
        let round_trip = t1.saturating_duration_since(t0);
        let queue_wait = batch_start.saturating_duration_since(t0);
        let round_trip_us = round_trip.as_secs_f64() * 1e6;
        let queue_wait_us = queue_wait.as_secs_f64() * 1e6;
        let service_us = service_dur.as_secs_f64() * 1e6;
        let other_us = (round_trip_us - queue_wait_us - service_us).max(0.0);
        local_samples.push(Sample { round_trip_us, queue_wait_us, service_us, other_us });
    }
    samples_out.lock().unwrap().extend(local_samples);
}

fn percentile(sorted: &[f64], p: f64) -> f64 {
    if sorted.is_empty() {
        return 0.0;
    }
    let idx = ((sorted.len() as f64 - 1.0) * p).round() as usize;
    sorted[idx.min(sorted.len() - 1)]
}

fn stats_of(mut v: Vec<f64>) -> (f64, f64, f64, f64) {
    // (mean, median, p95, max)
    if v.is_empty() {
        return (0.0, 0.0, 0.0, 0.0);
    }
    let mean = v.iter().sum::<f64>() / v.len() as f64;
    v.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let median = percentile(&v, 0.5);
    let p95 = percentile(&v, 0.95);
    let max = *v.last().unwrap();
    (mean, median, p95, max)
}

struct RunResult {
    n: usize,
    total_measured_requests: u64,
    num_batches_recorded: usize,
    batch_mean: f64,
    batch_median: f64,
    batch_p05: f64,
    batch_min: usize,
    batch_max_seen: usize,
    round_trip_mean_us: f64,
    round_trip_median_us: f64,
    round_trip_p95_us: f64,
    round_trip_max_us: f64,
    queue_wait_mean_us: f64,
    queue_wait_median_us: f64,
    service_mean_us: f64,
    service_median_us: f64,
    other_mean_us: f64,
    throughput_req_per_s: f64,
    wall_s: f64,
}

fn run_for_n(n: usize) -> RunResult {
    let (req_tx, req_rx) = mpsc::channel::<Request>();
    let total_requests: u64 = n as u64 * (WARMUP_ITERS + MEASURE_ITERS);
    let batch_stats: Arc<Mutex<Vec<BatchStat>>> = Arc::new(Mutex::new(Vec::new()));
    let samples: Arc<Mutex<Vec<Sample>>> = Arc::new(Mutex::new(Vec::new()));

    let batch_stats_c = Arc::clone(&batch_stats);
    let collector = thread::spawn(move || {
        collector_loop(req_rx, n, total_requests, batch_stats_c);
    });

    let start = Instant::now();
    let mut workers = Vec::with_capacity(n);
    for _ in 0..n {
        let tx = req_tx.clone();
        let samples_c = Arc::clone(&samples);
        workers.push(thread::spawn(move || {
            worker_loop(tx, WARMUP_ITERS, MEASURE_ITERS, samples_c);
        }));
    }
    drop(req_tx); // Sammel-Faden soll nicht auf den Original-Sender warten.
    for w in workers {
        w.join().expect("Arbeits-Faden sollte fehlerfrei enden");
    }
    collector.join().expect("Sammel-Faden sollte fehlerfrei enden");
    let wall_s = start.elapsed().as_secs_f64();

    let batch_sizes: Vec<f64> =
        batch_stats.lock().unwrap().iter().map(|b| b.size as f64).collect();
    let batch_min = batch_sizes.iter().cloned().fold(f64::INFINITY, f64::min) as usize;
    let batch_max_seen = batch_sizes.iter().cloned().fold(0.0, f64::max) as usize;
    let (batch_mean, batch_median, _bp95, _bmax) = stats_of(batch_sizes.clone());
    let mut sorted_batches = batch_sizes.clone();
    sorted_batches.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let batch_p05 = percentile(&sorted_batches, 0.05);

    let samples_v = samples.lock().unwrap();
    let rt: Vec<f64> = samples_v.iter().map(|s| s.round_trip_us).collect();
    let qw: Vec<f64> = samples_v.iter().map(|s| s.queue_wait_us).collect();
    let sv: Vec<f64> = samples_v.iter().map(|s| s.service_us).collect();
    let ov: Vec<f64> = samples_v.iter().map(|s| s.other_us).collect();
    let total_measured_requests = samples_v.len() as u64;
    drop(samples_v);

    let (rt_mean, rt_median, rt_p95, rt_max) = stats_of(rt);
    let (qw_mean, qw_median, _qw_p95, _qw_max) = stats_of(qw);
    let (sv_mean, sv_median, _sv_p95, _sv_max) = stats_of(sv);
    let (ov_mean, _ov_median, _ov_p95, _ov_max) = stats_of(ov);

    let throughput_req_per_s = total_measured_requests as f64 / wall_s;

    RunResult {
        n,
        total_measured_requests,
        num_batches_recorded: batch_sizes.len(),
        batch_mean,
        batch_median,
        batch_p05,
        batch_min,
        batch_max_seen,
        round_trip_mean_us: rt_mean,
        round_trip_median_us: rt_median,
        round_trip_p95_us: rt_p95,
        round_trip_max_us: rt_max,
        queue_wait_mean_us: qw_mean,
        queue_wait_median_us: qw_median,
        service_mean_us: sv_mean,
        service_median_us: sv_median,
        other_mean_us: ov_mean,
        throughput_req_per_s,
        wall_s,
    }
}

fn main() {
    let ns: Vec<usize> = vec![11, 32, 64, 128, 256];
    let available_parallelism = thread::available_parallelism().map(|n| n.get()).unwrap_or(0);
    println!(
        "Probelauf Nebenlaeufigkeits-Mechanik -- verfuegbare logische Kerne (std::thread::available_parallelism): {available_parallelism}"
    );
    println!(
        "FEATURE_LEN={FEATURE_LEN} GPU_SLEEP={:?} SLOT_TIMEOUT={:?} WARMUP_ITERS={WARMUP_ITERS} MEASURE_ITERS={MEASURE_ITERS}",
        GPU_SLEEP, SLOT_TIMEOUT
    );
    println!(
        "{:>5} {:>10} {:>10} {:>8} {:>8} {:>12} {:>12} {:>10} {:>10} {:>10} {:>14}",
        "N", "batch_mean", "batch_med", "b_min", "b_max", "rt_med_us", "rt_p95_us", "qw_med_us",
        "svc_med_us", "wall_s", "thpt_req/s"
    );

    let mut results = Vec::new();
    for &n in &ns {
        let r = run_for_n(n);
        println!(
            "{:>5} {:>10.2} {:>10.1} {:>8} {:>8} {:>12.1} {:>12.1} {:>10.1} {:>10.1} {:>10.2} {:>14.1}",
            r.n,
            r.batch_mean,
            r.batch_median,
            r.batch_min,
            r.batch_max_seen,
            r.round_trip_median_us,
            r.round_trip_p95_us,
            r.queue_wait_median_us,
            r.service_median_us,
            r.wall_s,
            r.throughput_req_per_s
        );
        results.push(r);
    }

    // JSON schreiben. cwd bei `cargo run --example` innerhalb von engine/ ist
    // engine/ selbst -> ../evaluations/ zeigt auf den Repo-Root evaluations/.
    let out_path = std::path::Path::new("../evaluations/interleave_concurrency_probe.json");
    let arr: Vec<serde_json::Value> = results
        .iter()
        .map(|r| {
            serde_json::json!({
                "n": r.n,
                "batch_max_setting": r.n,
                "total_measured_requests": r.total_measured_requests,
                "num_batches_recorded": r.num_batches_recorded,
                "batch_size": {
                    "mean": r.batch_mean,
                    "median": r.batch_median,
                    "p05": r.batch_p05,
                    "min": r.batch_min,
                    "max": r.batch_max_seen,
                },
                "round_trip_us": {
                    "mean": r.round_trip_mean_us,
                    "median": r.round_trip_median_us,
                    "p95": r.round_trip_p95_us,
                    "max": r.round_trip_max_us,
                },
                "queue_wait_us": {
                    "mean": r.queue_wait_mean_us,
                    "median": r.queue_wait_median_us,
                },
                "service_us_measured": {
                    "mean": r.service_mean_us,
                    "median": r.service_median_us,
                },
                "other_overhead_us_mean": r.other_mean_us,
                "throughput_req_per_s": r.throughput_req_per_s,
                "wall_s": r.wall_s,
            })
        })
        .collect();

    let out = serde_json::json!({
        "beschreibung": "Probelauf Nebenlaeufigkeits-Mechanik fuer die geplante GPU-Verschraenkung (PREREG_gpu_inference_path.md), OHNE Suche/Netz/IPC -- reine Warteschlangen-Mechanik.",
        "parameter": {
            "feature_len": FEATURE_LEN,
            "gpu_sleep_ms": GPU_SLEEP.as_secs_f64() * 1000.0,
            "gpu_sleep_ungeprueft": true,
            "slot_timeout_us": SLOT_TIMEOUT.as_micros(),
            "warmup_iters_per_thread": WARMUP_ITERS,
            "measure_iters_per_thread": MEASURE_ITERS,
            "available_parallelism_logical_cores": available_parallelism,
        },
        "ns": ns,
        "results": arr,
    });
    let json_str = serde_json::to_string_pretty(&out).expect("JSON-Serialisierung");
    if let Some(parent) = out_path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    std::fs::write(out_path, json_str).expect("JSON-Datei schreiben");
    println!("\nJSON geschrieben nach: {}", out_path.display());
}
