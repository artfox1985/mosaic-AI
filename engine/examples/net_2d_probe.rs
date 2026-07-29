//! Rust<->2D-ONNX-Roundtrip-Beweis (Task #11 Phase 1, Teil C.2): lädt ein
//! UNTRAINIERTES `Mosaic2DNet` (von `selftest_2d_encoder.py` nach
//! `tmp_2d_probe.onnx` exportiert, Rang-4-Single-Input `[batch,76,6,6]`)
//! über `Net::load_auto` und wertet es aus -- beweist, dass die komplette
//! Kette Python-2D-Export -> tract-onnx-Laden (Planes-Layout) ->
//! `Net::eval`/`eval_pair` funktioniert, ganz ohne die Python-Umgebung
//! anzufassen.
//!
//! Aufruf: cargo run --example net_2d_probe -- <tmp_2d_probe.onnx>

use mosaic_rust::net::Net;

fn main() {
    let mut args = std::env::args().skip(1);
    let model_path = args.next().unwrap_or_else(|| "tmp_2d_probe.onnx".to_string());

    let net = Net::load_auto(&model_path).expect("Net::load_auto (2D-Modell)");
    println!("✅ Net::load_auto hat das 2D-ONNX-Modell geladen: {model_path}");

    // Planes-Layout: 76 Kanäle x 6 x 6 = 2736 Floats pro Position (siehe
    // NUM_PLANES_CHANNELS in neural_net.py).
    const C: usize = 76;
    const H: usize = 6;
    const W: usize = 6;
    let feats_a = vec![0.1f32; C * H * W];
    let feats_b = vec![-0.2f32; C * H * W];

    let (policy, value, moon, points) = net.eval(&feats_a).expect("eval (Planes-Layout)");
    println!(
        "eval(): policy.len={} value.len={} moon.len={} points.len={}",
        policy.len(),
        value.len(),
        moon.len(),
        points.len()
    );
    assert_eq!(policy.len(), 406, "policy-Kopf muss NUM_ACTIONS=406 liefern");
    assert_eq!(value.len(), 1, "value-Kopf muss 1 liefern");
    assert_eq!(moon.len(), 5, "moon-Kopf muss 5 liefern");
    assert_eq!(points.len(), 1, "points-Kopf muss 1 liefern");
    println!("  value[0]={:.6}", value[0]);

    let ((pa, va, ma, pta), (pb, vb, mb, ptb)) =
        net.eval_pair(&feats_a, &feats_b).expect("eval_pair (Planes-Layout)");
    assert_eq!(pa.len(), 406);
    assert_eq!(pb.len(), 406);
    assert_eq!(va.len(), 1);
    assert_eq!(vb.len(), 1);
    assert_eq!(ma.len(), 5);
    assert_eq!(mb.len(), 5);
    assert_eq!(pta.len(), 1);
    assert_eq!(ptb.len(), 1);
    println!("eval_pair(): value_a={:.6} value_b={:.6} (unterschiedliche Inputs -> erwartungsgemäß unterschiedliche Werte)", va[0], vb[0]);
    assert!(
        (va[0] - vb[0]).abs() > 1e-9,
        "eval_pair mit unterschiedlichen Inputs sollte unterschiedliche Werte liefern"
    );

    println!("\n✅ GESAMT: Rust<->2D-ONNX-Roundtrip erfolgreich (Net::load_auto + eval + eval_pair, Planes-Layout, 5-Kopf-Modell -> 4 von net.rs gelesene Köpfe).");
}
