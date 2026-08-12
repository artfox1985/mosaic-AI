//! Einmal-Messung (Verschraenkungs-Auftrag, 2026-08-12): wie teuer ist
//! `Net::load_auto` in Abhaengigkeit von `net::EVAL_BATCH_MAX_N`? Jeder
//! zusaetzliche Wert `n` baut einen EIGENEN, fest optimierten tract-Plan
//! (`net.rs::build_from_layout`s `model_batch`-Schleife) -- das kostet
//! Ladezeit, nicht Inferenzzeit. Misst nur die aktuell im Code stehende
//! `EVAL_BATCH_MAX_N` (Aufrufer muss die Konstante selbst aendern und neu
//! bauen, um mehrere Werte zu vergleichen -- keine Laufzeit-Parametrisierung,
//! `EVAL_BATCH_MAX_N` ist eine compile-time `const`).
//!
//! Aufruf: cargo run --release --example net_load_time_probe -- <onnx-pfad>
use std::time::Instant;

fn main() {
    let path = std::env::args().nth(1).unwrap_or_else(|| {
        "../models/alphazero_v20_2d_opp_brierbest.onnx".to_string()
    });
    println!("EVAL_BATCH_MAX_N = {}", mosaic_rust::net::EVAL_BATCH_MAX_N);
    println!("Modell: {path}");
    let t0 = Instant::now();
    let net = mosaic_rust::net::Net::load_auto(&path).expect("Modell ladbar");
    let elapsed = t0.elapsed();
    println!("Ladezeit (load_auto, inkl. {} eval_batch-Plaene): {:.3}s", mosaic_rust::net::EVAL_BATCH_MAX_N, elapsed.as_secs_f64());

    // Kurzer Rundlauf-Sanity-Check: eval_batch(1) UND eval_batch(MAX_N) muessen
    // funktionieren (Plaene tatsaechlich vorhanden).
    let feats = vec![0f32; net.input_size()];
    let refs = vec![feats.as_slice()];
    net.eval_batch(&refs).expect("eval_batch(1) sollte funktionieren");
    let refs_max: Vec<&[f32]> = (0..mosaic_rust::net::EVAL_BATCH_MAX_N).map(|_| feats.as_slice()).collect();
    let t1 = Instant::now();
    net.eval_batch(&refs_max).expect("eval_batch(MAX_N) sollte funktionieren");
    println!("eval_batch(MAX_N) ein Aufruf: {:.3}ms", t1.elapsed().as_secs_f64() * 1000.0);
}
