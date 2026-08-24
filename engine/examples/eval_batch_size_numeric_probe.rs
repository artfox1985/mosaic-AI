//! Diagnose-Sonde (PREREG_agent_encapsulation.md par.8e, Koordinator-
//! Hypothese "Restdivergenz ist Numerik, kein Protokollfehler"): prueft
//! DIREKT und BITWEISE, ob dieselbe Merkmalszeile je nach BATCH-GROESSE N
//! (verschiedene vorgebaute tract-Plaene, siehe `net.rs::model_batch`) ein
//! anderes Ergebnis liefert -- unabhaengig vom Verschraenkungs-Sammel-Faden
//! (`net_batcher.rs`, der im `net_vs_net_arena_match`-Pfad strukturell NIE
//! aktiv wird, siehe Bericht), sondern als Test der ROOT-Batch-Mechanik
//! (`net_mcts.rs::batched_expand_root_candidates`, IMMER aktiv, buendelt
//! die Top-m-Gumbel-Wurzelkandidaten in EINEM `eval_batch_ex`-Aufruf).
//!
//! Vier Vergleiche je Zeile `feats[0]`:
//!  1. `net.eval(&feats[0])`            -- dedizierter Batch=1-Plan (`self.model`)
//!  2. `net.eval_batch(&feats[0..1])`   -- Batch-Plan `model_batch[1]`
//!  3. `net.eval_batch(&feats[0..2])`   -- Zeile 0 als Teil von N=2
//!  4. `net.eval_batch(&feats[0..16])`  -- Zeile 0 als Teil von N=16 (GUMBEL_TOP_M)
//!
//! Ausgabe je Vergleich: bitgleich JA/NEIN, max |Delta|, max ULP-Abstand.
//!
//! Aufruf: cargo run --release --example eval_batch_size_numeric_probe -- <model.onnx>

use mosaic_rust::net::Net;
use rand::rngs::StdRng;
use rand::{RngExt, SeedableRng};

fn max_diff(a: &[f32], b: &[f32]) -> (f32, u64) {
    let mut abs = 0.0f32;
    let mut ulp = 0u64;
    assert_eq!(a.len(), b.len(), "Laengen-Mismatch -- Kopf fehlt/leer in einem der beiden Pfade");
    for (x, y) in a.iter().zip(b) {
        abs = abs.max((x - y).abs());
        ulp = ulp.max((x.to_bits() as i64 - y.to_bits() as i64).unsigned_abs());
    }
    (abs, ulp)
}

fn report(tag: &str, a: &[f32], b: &[f32]) -> bool {
    let (abs, ulp) = max_diff(a, b);
    let identical = ulp == 0;
    println!(
        "  {tag:32} bitgleich={} max_abs={abs:e} max_ulp={ulp} n={}",
        if identical { "JA " } else { "NEIN" },
        a.len(),
    );
    identical
}

fn main() {
    let model_path = std::env::args().nth(1).expect("Arg 1: Pfad zum .onnx-Modell");
    // `load_auto` statt `load(.., INPUT_SIZE)`: 2D-Modelle (u.a. der
    // Kernbeweis-Champion v21_2d_brierbest) haben eine eigene Input-Form,
    // siehe `net_batcher.rs`-Testpraezedenz.
    let net = Net::load_auto(&model_path).expect("Net::load_auto");
    let input_size = net.input_size();

    let mut rng = StdRng::seed_from_u64(910002); // an den Kernbeweis-Seed angelehnt, sonst beliebig
    let mut all_identical = true;

    for trial in 0..5u32 {
        println!("-- trial {trial} --");
        // Zeile 0 ist die zu vergleichende Stellung; Zeilen 1..15 sind
        // ANDERE zufaellige Stellungen, die den Batch nur fuellen (so wie
        // ANDERE Gumbel-Wurzelkandidaten oder andere Partien im Batch den
        // Sammel-Faden fuellen wuerden).
        let feats: Vec<Vec<f32>> =
            (0..16).map(|_| (0..input_size).map(|_| rng.random_range(-1.0f32..1.0)).collect()).collect();

        let single = net.eval(&feats[0]).expect("eval (single plan)");
        let refs1: Vec<&[f32]> = vec![feats[0].as_slice()];
        let batch1 = net.eval_batch(&refs1).expect("eval_batch N=1").remove(0);
        let refs2: Vec<&[f32]> = feats[0..2].iter().map(|v| v.as_slice()).collect();
        let batch2 = net.eval_batch(&refs2).expect("eval_batch N=2").remove(0);
        let refs16: Vec<&[f32]> = feats[0..16].iter().map(|v| v.as_slice()).collect();
        let batch16 = net.eval_batch(&refs16).expect("eval_batch N=16").remove(0);

        for (name, x, y) in [
            ("eval() vs eval_batch(N=1)", &single.0, &batch1.0),
            ("eval() vs eval_batch(N=2)[row0]", &single.0, &batch2.0),
            ("eval() vs eval_batch(N=16)[row0]", &single.0, &batch16.0),
            ("eval_batch(N=1) vs eval_batch(N=2)[row0]", &batch1.0, &batch2.0),
            ("eval_batch(N=1) vs eval_batch(N=16)[row0]", &batch1.0, &batch16.0),
            ("eval_batch(N=2) vs eval_batch(N=16)[row0]", &batch2.0, &batch16.0),
        ] {
            all_identical &= report(&format!("policy: {name}"), x, y);
        }
        for (name, x, y) in [
            ("eval() vs eval_batch(N=1)", &single.1, &batch1.1),
            ("eval() vs eval_batch(N=2)[row0]", &single.1, &batch2.1),
            ("eval() vs eval_batch(N=16)[row0]", &single.1, &batch16.1),
        ] {
            all_identical &= report(&format!("value:  {name}"), x, y);
        }
        for (name, x, y) in [
            ("eval() vs eval_batch(N=1)", &single.2, &batch1.2),
            ("eval() vs eval_batch(N=16)[row0]", &single.2, &batch16.2),
        ] {
            all_identical &= report(&format!("moon:   {name}"), x, y);
        }
        for (name, x, y) in [
            ("eval() vs eval_batch(N=1)", &single.3, &batch1.3),
            ("eval() vs eval_batch(N=16)[row0]", &single.3, &batch16.3),
        ] {
            all_identical &= report(&format!("points: {name}"), x, y);
        }

        // Zusaetzlich `eval_batch_ex` (6-Tupel inkl. opp_points/ownership) --
        // das ist die Funktion, die `batched_expand_root_candidates`
        // TATSAECHLICH aufruft (net_mcts.rs:4273).
        let single_ex = net.eval_batch_ex(&refs1).expect("eval_batch_ex N=1")[0].clone();
        let batch2_ex = net.eval_batch_ex(&refs2).expect("eval_batch_ex N=2")[0].clone();
        let batch16_ex = net.eval_batch_ex(&refs16).expect("eval_batch_ex N=16")[0].clone();
        if !single_ex.4.is_empty() {
            all_identical &= report("opp_points: N=1 vs N=2[row0]", &single_ex.4, &batch2_ex.4);
            all_identical &= report("opp_points: N=1 vs N=16[row0]", &single_ex.4, &batch16_ex.4);
        }
        if !single_ex.5.is_empty() {
            all_identical &= report("ownership: N=1 vs N=2[row0]", &single_ex.5, &batch2_ex.5);
            all_identical &= report("ownership: N=1 vs N=16[row0]", &single_ex.5, &batch16_ex.5);
        }
    }

    println!(
        "\nGESAMT: {}",
        if all_identical {
            "ALLE Vergleiche bitgleich -- Batch-Groesse aendert bei diesem Modell/diesen Zeilen NICHTS."
        } else {
            "MINDESTENS EIN Vergleich weicht ab -- Batch-Groesse aendert das Bitmuster (siehe max_abs/max_ulp oben)."
        }
    );
}
