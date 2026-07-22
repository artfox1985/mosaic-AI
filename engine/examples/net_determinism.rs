//! Determinismus-Probe für `Net::eval`/`eval_pair` (tract-onnx) über
//! Instanz- und Prozessgrenzen hinweg (Untersuchung nach Task #71: Self-Play-
//! Läufe mit identischem Seed liefern in SEPARATEN Prozessen leicht
//! abweichende bootstrap_values, obwohl alle Suchbudgets knotenbasiert sind).
//!
//! Drei Prüfungen:
//!  1. Gleiche Net-Instanz, gleicher Input, zweimal eval → bitweise gleich?
//!  2. ZWEI Net::load-Instanzen im SELBEN Prozess, gleicher Input → bitweise
//!     gleich? (Testet, ob die Graph-Optimierung pro Ladevorgang
//!     nichtdeterministisch ist, z.B. HashMap-Iterationsreihenfolge.)
//!  3. Bitmuster aller Outputs in eine Datei schreiben → zwei separate
//!     Prozessläufe diffen (testet ASLR-/prozessglobale Effekte).
//!
//! Aufruf: cargo run --release --example net_determinism -- <model.onnx> <out.txt>

use mosaic_rust::features::INPUT_SIZE;
use mosaic_rust::net::Net;
use rand::rngs::StdRng;
use rand::{RngExt, SeedableRng};
use std::io::Write;

fn bits_line(tag: &str, xs: &[f32]) -> String {
    let hex: Vec<String> = xs.iter().map(|x| format!("{:08x}", x.to_bits())).collect();
    format!("{tag} {}", hex.join(" "))
}

fn max_diff(a: &[f32], b: &[f32]) -> (f32, u32) {
    // (max |a-b|, max ULP-Abstand)
    let mut abs = 0.0f32;
    let mut ulp = 0u32;
    for (x, y) in a.iter().zip(b) {
        abs = abs.max((x - y).abs());
        ulp = ulp.max((x.to_bits() as i64 - y.to_bits() as i64).unsigned_abs() as u32);
    }
    (abs, ulp)
}

fn main() {
    let mut args = std::env::args().skip(1);
    let model_path = args.next().expect("Arg 1: Pfad zum .onnx-Modell");
    let out_path = args.next().expect("Arg 2: Output-Datei");

    let net1 = Net::load(&model_path, INPUT_SIZE).expect("Net::load (1)");
    let net2 = Net::load(&model_path, INPUT_SIZE).expect("Net::load (2)");

    let mut rng = StdRng::seed_from_u64(42);
    let mut out = std::fs::File::create(&out_path).expect("Output-Datei anlegen");

    for trial in 0..8u32 {
        let fa: Vec<f32> = (0..INPUT_SIZE).map(|_| rng.random_range(-1.0f32..1.0)).collect();
        let fb: Vec<f32> = (0..INPUT_SIZE).map(|_| rng.random_range(-1.0f32..1.0)).collect();

        let r1 = net1.eval(&fa).expect("eval net1");
        let r1b = net1.eval(&fa).expect("eval net1 wiederholt");
        let r2 = net2.eval(&fa).expect("eval net2");
        let pair1 = net1.eval_pair(&fa, &fb).expect("eval_pair net1");
        let pair2 = net2.eval_pair(&fa, &fb).expect("eval_pair net2");

        // Prüfung 1: Wiederholung auf derselben Instanz.
        for (name, x, y) in [
            ("policy", &r1.0, &r1b.0),
            ("value", &r1.1, &r1b.1),
            ("moon", &r1.2, &r1b.2),
            ("points", &r1.3, &r1b.3),
        ] {
            let (abs, ulp) = max_diff(x, y);
            if ulp != 0 {
                println!("REPEAT-DIFF trial={trial} head={name} max_abs={abs:e} max_ulp={ulp}");
            }
        }

        // Prüfung 2: Zweite Instanz im selben Prozess.
        for (name, x, y) in [
            ("policy", &r1.0, &r2.0),
            ("value", &r1.1, &r2.1),
            ("moon", &r1.2, &r2.2),
            ("points", &r1.3, &r2.3),
        ] {
            let (abs, ulp) = max_diff(x, y);
            if ulp != 0 {
                println!("INSTANCE-DIFF trial={trial} head={name} max_abs={abs:e} max_ulp={ulp}");
            }
        }
        // eval_pair zwischen den Instanzen.
        for (name, x, y) in [
            ("pair_policy_a", &pair1.0 .0, &pair2.0 .0),
            ("pair_value_a", &pair1.0 .1, &pair2.0 .1),
            ("pair_policy_b", &pair1.1 .0, &pair2.1 .0),
            ("pair_value_b", &pair1.1 .1, &pair2.1 .1),
        ] {
            let (abs, ulp) = max_diff(x, y);
            if ulp != 0 {
                println!("INSTANCE-DIFF trial={trial} head={name} max_abs={abs:e} max_ulp={ulp}");
            }
        }

        // Prüfung 3: Bitmuster für Cross-Prozess-Diff (nur net1).
        writeln!(out, "{}", bits_line(&format!("t{trial} policy"), &r1.0)).unwrap();
        writeln!(out, "{}", bits_line(&format!("t{trial} value"), &r1.1)).unwrap();
        writeln!(out, "{}", bits_line(&format!("t{trial} moon"), &r1.2)).unwrap();
        writeln!(out, "{}", bits_line(&format!("t{trial} points"), &r1.3)).unwrap();
        writeln!(out, "{}", bits_line(&format!("t{trial} pair_value_a"), &pair1.0 .1)).unwrap();
        writeln!(out, "{}", bits_line(&format!("t{trial} pair_value_b"), &pair1.1 .1)).unwrap();
        writeln!(out, "{}", bits_line(&format!("t{trial} pair_policy_a"), &pair1.0 .0)).unwrap();
    }
    println!("OK: Bitmuster nach {out_path} geschrieben.");
}
