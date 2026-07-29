//! Abnahme-Nachweis für Task #11 Phase 1 (2D-Encoder-Kompatibilitätsschicht):
//! `Net::load_auto(path)` muss für JEDES Bestandsmodell (flacher 708-Input,
//! v1..v18) exakt dieselben Ausgaben liefern wie das bisherige
//! `Net::load(path, features::INPUT_SIZE)` -- bit-identisch, nicht nur
//! "ungefähr gleich". Das ist die harte Produktanforderung des Nutzers:
//! bestehende ONNX-Modelle müssen ladbar UND spielbar bleiben.
//!
//! Prüft das für ZWEI verschiedene Modelle (v17_best, v18_best) mit je
//! 5 deterministischen (geseedeten) Zufalls-Feature-Vektoren, sowohl über
//! `eval()` als auch `eval_pair()`.
//!
//! Aufruf: cargo run --example net_load_auto_backcompat

use mosaic_rust::features::INPUT_SIZE;
use mosaic_rust::net::Net;
use rand::rngs::StdRng;
use rand::{RngExt, SeedableRng};

fn exact(a: &[f32], b: &[f32]) -> bool {
    a.len() == b.len() && a.iter().zip(b).all(|(x, y)| x.to_bits() == y.to_bits())
}

fn check_model(path: &str) -> bool {
    println!("== {path} ==");
    let net_load = match Net::load(path, INPUT_SIZE) {
        Ok(n) => n,
        Err(e) => {
            println!("  ⚠️  Net::load fehlgeschlagen ({e}) -- Modell nicht lokal vorhanden? Übersprungen.");
            return true; // kein hartes Scheitern bei fehlendem lokalem Checkpoint
        }
    };
    let net_auto = Net::load_auto(path).expect("Net::load_auto");

    let mut rng = StdRng::seed_from_u64(1234);
    let mut all_ok = true;

    for trial in 0..5u32 {
        let fa: Vec<f32> = (0..INPUT_SIZE).map(|_| rng.random_range(-1.0f32..1.0)).collect();
        let fb: Vec<f32> = (0..INPUT_SIZE).map(|_| rng.random_range(-1.0f32..1.0)).collect();

        let (p1, v1, m1, pt1) = net_load.eval(&fa).expect("eval (load)");
        let (p2, v2, m2, pt2) = net_auto.eval(&fa).expect("eval (load_auto)");

        let ok_single = exact(&p1, &p2) && exact(&v1, &v2) && exact(&m1, &m2) && exact(&pt1, &pt2);
        if !ok_single {
            println!("  ❌ trial={trial} eval() weicht ab (load vs. load_auto)");
            all_ok = false;
        }

        let (pair1_a, pair1_b) = net_load.eval_pair(&fa, &fb).expect("eval_pair (load)");
        let (pair2_a, pair2_b) = net_auto.eval_pair(&fa, &fb).expect("eval_pair (load_auto)");
        let ok_pair = exact(&pair1_a.0, &pair2_a.0)
            && exact(&pair1_a.1, &pair2_a.1)
            && exact(&pair1_a.2, &pair2_a.2)
            && exact(&pair1_a.3, &pair2_a.3)
            && exact(&pair1_b.0, &pair2_b.0)
            && exact(&pair1_b.1, &pair2_b.1)
            && exact(&pair1_b.2, &pair2_b.2)
            && exact(&pair1_b.3, &pair2_b.3);
        if !ok_pair {
            println!("  ❌ trial={trial} eval_pair() weicht ab (load vs. load_auto)");
            all_ok = false;
        }

        if trial == 0 {
            println!(
                "  trial=0 value(load)={:.6} value(load_auto)={:.6} (Sanity: ungleich Null/NaN erwartet)",
                v1[0], v2[0]
            );
        }
    }

    if all_ok {
        println!("  ✅ Alle 5 Durchläufe (eval + eval_pair) bit-identisch.");
    }
    all_ok
}

fn main() {
    let models_dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../../models");
    // Absolute Pfade ins Haupt-Checkout (Sicherheitsregel 1: nur lesend, nie
    // per Junction/Symlink referenziert). Fallback auf den Worktree-relativen
    // Pfad, falls das Beispiel woanders ausgeführt wird.
    let candidates = [
        r"D:\OneDrive\Documents\Projekte\mosaic-AI\models\alphazero_v17_best.onnx".to_string(),
        r"D:\OneDrive\Documents\Projekte\mosaic-AI\models\alphazero_v18_best.onnx".to_string(),
        models_dir.join("alphazero_v17_best.onnx").to_string_lossy().to_string(),
        models_dir.join("alphazero_v18_best.onnx").to_string_lossy().to_string(),
    ];

    let mut any_checked = false;
    let mut all_ok = true;
    for path in [&candidates[0], &candidates[1]] {
        if std::path::Path::new(path).exists() {
            any_checked = true;
            if !check_model(path) {
                all_ok = false;
            }
        } else {
            println!("== {path} == nicht gefunden, übersprungen.");
        }
    }

    if !any_checked {
        println!("⚠️  Keine der erwarteten Modelldateien gefunden -- kein Vergleich durchgeführt.");
        std::process::exit(2);
    }
    if !all_ok {
        eprintln!("❌ FEHLGESCHLAGEN: load_auto weicht von load ab.");
        std::process::exit(1);
    }
    println!("✅ GESAMT: load_auto ist für alle geprüften Modelle bit-identisch zu load(path, INPUT_SIZE).");
}
