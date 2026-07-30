//! Rust<->2D-ONNX-Zwei-Input-Roundtrip-Beweis (Task #11 Phase 2, M1.4): lädt
//! ein UNTRAINIERTES `Mosaic2DNet` (von einem Export-Hilfsskript nach
//! `tmp_2d_probe_two_input.onnx` exportiert, ZWEI Inputs -- `planes`
//! `[batch,76,6,6]` und `state` `[batch,708]`) über `Net::load_auto` und
//! wertet es via `eval`/`eval_pair` aus. Beweist, dass die komplette Kette
//! Python-2D-Zwei-Input-Export -> tract-onnx-Laden
//! (`InputLayout::PlanesPlusFlat`) -> `Net::eval`/`eval_pair` (kombinierter
//! Puffer: Planes-Teil gefolgt vom Flat-Teil, intern gesplittet) funktioniert
//! -- ganz ohne Python-Umgebung zur Laufzeit (Sicherheitsregel 1: kein
//! Wheel-Install nötig).
//!
//! Unterschied zu `net_2d_probe.rs` (Phase 1): jenes deckt den EIN-Input-
//! Rang-4-Pfad ab (`InputLayout::Planes`, nie trainiert), dieses Beispiel den
//! tatsächlich für Phase-2-Training vorgesehenen ZWEI-Input-Pfad
//! (`InputLayout::PlanesPlusFlat`).
//!
//! Aufruf: cargo run --release --example net_2d_probe_two_input -- <tmp_2d_probe_two_input.onnx>

use mosaic_rust::net::Net;

fn main() {
    let mut args = std::env::args().skip(1);
    let model_path = args.next().unwrap_or_else(|| "tmp_2d_probe_two_input.onnx".to_string());

    let net = Net::load_auto(&model_path).expect("Net::load_auto (2D-Zwei-Input-Modell)");
    println!("✅ Net::load_auto hat das Zwei-Input-2D-ONNX-Modell geladen: {model_path}");

    // Kombinierter Puffer: Planes-Teil (76*6*6=2736) gefolgt vom Flat-Teil
    // (708) -- siehe features::state_to_features_2d_direct / net.rs-Doku.
    const C: usize = 76;
    const H: usize = 6;
    const W: usize = 6;
    const FLAT: usize = 708;
    const TOTAL: usize = C * H * W + FLAT;

    let feats_a: Vec<f32> = (0..TOTAL).map(|i| (i as f32 * 0.0001).sin()).collect();
    let feats_b: Vec<f32> = (0..TOTAL).map(|i| (i as f32 * 0.0001 + 3.0).sin()).collect();

    let (policy, value, moon, points) = net.eval(&feats_a).expect("eval (PlanesPlusFlat-Layout)");
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
        net.eval_pair(&feats_a, &feats_b).expect("eval_pair (PlanesPlusFlat-Layout)");
    assert_eq!(pa.len(), 406);
    assert_eq!(pb.len(), 406);
    assert_eq!(va.len(), 1);
    assert_eq!(vb.len(), 1);
    assert_eq!(ma.len(), 5);
    assert_eq!(mb.len(), 5);
    assert_eq!(pta.len(), 1);
    assert_eq!(ptb.len(), 1);
    println!(
        "eval_pair(): value_a={:.6} value_b={:.6} (unterschiedliche Inputs -> erwartungsgemäß unterschiedliche Werte)",
        va[0], vb[0]
    );
    assert!(
        (va[0] - vb[0]).abs() > 1e-9,
        "eval_pair mit unterschiedlichen Inputs sollte unterschiedliche Werte liefern"
    );

    // eval_pair(a,b) muss elementweise eval(a)/eval(b) entsprechen (dieselbe
    // Garantie wie beim Flat-Pfad, siehe net.rs::eval_pair_matches_two_single_evals).
    let (policy_b_single, value_b_single, moon_b_single, points_b_single) =
        net.eval(&feats_b).expect("eval (feats_b, Einzelaufruf)");
    let close = |x: &[f32], y: &[f32]| -> bool {
        x.len() == y.len() && x.iter().zip(y).all(|(u, v)| (u - v).abs() < 1e-5)
    };
    assert!(close(&pa, &policy), "eval_pair-Zeile a muss zu eval(a) passen");
    assert!(close(&pb, &policy_b_single), "eval_pair-Zeile b muss zu eval(b) passen");
    assert!(close(&va, &value), "eval_pair value_a muss zu eval(a) value passen");
    assert!(close(&vb, &value_b_single), "eval_pair value_b muss zu eval(b) value passen");
    assert!(close(&ma, &moon) && close(&mb, &moon_b_single));
    assert!(close(&pta, &points) && close(&ptb, &points_b_single));

    println!(
        "\n✅ GESAMT: Rust<->2D-ONNX-Zwei-Input-Roundtrip erfolgreich (Net::load_auto + eval + eval_pair, \
         PlanesPlusFlat-Layout, eval_pair==zwei Einzelaufrufe, 5-Kopf-Modell -> 4 von net.rs gelesene Köpfe)."
    );
}
