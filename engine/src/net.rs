//! ONNX-Netz-Inferenz via tract-onnx (Network-Modus, Phase B).
//!
//! Lädt ein nach ONNX exportiertes MosaicNet (`export_onnx.py`) und liefert
//! `(policy_logits[NUM_ACTIONS], value[1], moon_logits[5], points[1])`.
//! `value` treibt bei `ACTIVE_LEAF=Net` (Stufe 2, Standard) tatsächlich die
//! PUCT-Suche (`net_mcts.rs::make_node`, `value_to_win_prob`) -- KORRIGIERT
//! ggü. frühem Kommentarstand hier, der noch von der Vor-Value-Head-
//! Rückholung stammte (siehe stage2_investigation.md für die Historie).
//! `points` bleibt reines Trainings-Zusatzsignal, wird in der Suche nirgends
//! gelesen. Frühere `dome_slot`/`dome_rotation`-Faktorisierungsköpfe (Baustein
//! A) sind mit Baustein B (zweistufiger Kuppel-Suchknoten, `game.rs`
//! `ChooseDomeSlot`/`ChooseDomeRotation`) entfallen -- die Slot/Rotations-Wahl
//! bekommt jetzt jeweils eigene Policy-IDs statt einer Prior-Faktorisierung.
//! Reines Rust — keine libtorch/onnxruntime-Abhängigkeit. `eval()` bleibt
//! Batch=1 (eine Stellung pro Forward). Paket 1 (Inferenz-Batching,
//! 2026-07-22) ergänzt `eval_pair()` mit einem eigenen, fest auf Batch=2
//! optimierten Plan -- für die Mover-/geflippte-Perspektive-Doppelauswertung
//! an jedem Suchblatt (`net_mcts.rs::make_node`/`net_leaf_eval`), damit dafür
//! EIN ONNX-Graph-Durchlauf statt zwei sequenzieller Batch=1-Aufrufe bezahlt
//! wird. Fixer Batch=2-Shape statt symbolischer Achse: `eval_pair` braucht
//! immer GENAU 2 Positionen, ein fester Shape lässt tract dieselben
//! Optimierungen (Constant-Folding etc.) wie beim Batch=1-Plan durchführen --
//! eine symbolische Batch-Achse böte hier keinen Vorteil (Batch ist nie etwas
//! anderes als 2), risikiert aber, dass manche Op-Typen (batchabhängige
//! Reshape/Broadcast-Zielformen) schlechter optimiert werden.

use tract_onnx::prelude::*;

type Model = SimplePlan<TypedFact, Box<dyn TypedOp>, Graph<TypedFact, Box<dyn TypedOp>>>;

/// Geladenes, optimiertes Netz (thread-safe → über rayon teilbar).
pub struct Net {
    model: Model,
    /// Zweiter Plan, Batch fix = 2 (Paket 1, siehe Modul-Kommentar).
    model_pair: Model,
    input_size: usize,
}

impl Net {
    /// Lädt ein ONNX-Netz; `input_size` muss zur Feature-Länge passen
    /// (siehe `features::INPUT_SIZE` — dort übergeben, nicht hier hardcoden).
    /// Baut aus derselben geparsten Graph-Struktur ZWEI unabhängig optimierte
    /// Pläne (Batch=1 für `eval`, Batch=2 für `eval_pair`) -- ein `.clone()`
    /// vor dem jeweiligen `with_input_fact`/`into_optimized`, kein zweites
    /// Parsen der Datei von der Platte nötig.
    pub fn load(path: &str, input_size: usize) -> TractResult<Net> {
        let base = tract_onnx::onnx().model_for_path(path)?;
        let model = base
            .clone()
            .with_input_fact(0, f32::fact([1, input_size]).into())?
            .into_optimized()?
            .into_runnable()?;
        let model_pair = base
            .with_input_fact(0, f32::fact([2, input_size]).into())?
            .into_optimized()?
            .into_runnable()?;
        Ok(Net { model, model_pair, input_size })
    }

    /// Forward-Pass für eine Stellung. Gibt (policy_logits, value, moon_logits,
    /// points) -- ONNX-Ausgabereihenfolge aus `export_onnx.py`.
    pub fn eval(
        &self,
        feats: &[f32],
    ) -> TractResult<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)> {
        let input: Tensor =
            tract_ndarray::Array2::from_shape_vec((1, self.input_size), feats.to_vec())?.into();
        let out = self.model.run(tvec!(input.into()))?;
        let policy: Vec<f32> = out[0].to_array_view::<f32>()?.iter().copied().collect();
        let value: Vec<f32> = out[1].to_array_view::<f32>()?.iter().copied().collect();
        let moon: Vec<f32> = out[2].to_array_view::<f32>()?.iter().copied().collect();
        let points: Vec<f32> = out[3].to_array_view::<f32>()?.iter().copied().collect();
        Ok((policy, value, moon, points))
    }

    /// Forward-Pass für ZWEI unabhängige Stellungen in einem Batch=2-Aufruf
    /// (Paket 1, Inferenz-Batching) -- elementweise äquivalent zu
    /// `eval(feats_a)` + `eval(feats_b)` (siehe Paritätstest
    /// `eval_pair_matches_two_single_evals` unten), aber EIN ONNX-Graph-
    /// Durchlauf statt zwei. Zeile 0 = `feats_a`, Zeile 1 = `feats_b`;
    /// Rückgabe entsprechend `(ergebnis_a, ergebnis_b)`, jeweils in derselben
    /// `(policy_logits, value, moon_logits, points)`-Reihenfolge wie `eval`.
    pub fn eval_pair(
        &self,
        feats_a: &[f32],
        feats_b: &[f32],
    ) -> TractResult<(
        (Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>),
        (Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>),
    )> {
        let mut buf = Vec::with_capacity(2 * self.input_size);
        buf.extend_from_slice(feats_a);
        buf.extend_from_slice(feats_b);
        let input: Tensor = tract_ndarray::Array2::from_shape_vec((2, self.input_size), buf)?.into();
        let out = self.model_pair.run(tvec!(input.into()))?;
        let policy: Vec<f32> = out[0].to_array_view::<f32>()?.iter().copied().collect();
        let value: Vec<f32> = out[1].to_array_view::<f32>()?.iter().copied().collect();
        let moon: Vec<f32> = out[2].to_array_view::<f32>()?.iter().copied().collect();
        let points: Vec<f32> = out[3].to_array_view::<f32>()?.iter().copied().collect();
        let (policy_a, policy_b) = split_batch2(policy);
        let (value_a, value_b) = split_batch2(value);
        let (moon_a, moon_b) = split_batch2(moon);
        let (points_a, points_b) = split_batch2(points);
        Ok(((policy_a, value_a, moon_a, points_a), (policy_b, value_b, moon_b, points_b)))
    }
}

/// Teilt einen zeilenweise (Batch zuerst) flach ausgelesenen Batch=2-Output
/// exakt in der Mitte -- funktioniert für jede Kopfgröße (policy/value/moon/
/// points), solange der Tensor row-major mit Batch als führender Achse ist
/// (Standard-ONNX-Layout, hier immer erfüllt). Leerer Input (Kopf fehlt im
/// Checkpoint, z.B. `points` bei älteren Modellen) → zwei leere Vektoren.
fn split_batch2(flat: Vec<f32>) -> (Vec<f32>, Vec<f32>) {
    let half = flat.len() / 2;
    let mut a = flat;
    let b = a.split_off(half);
    (a, b)
}

/// Softmax über Logits (für Policy-Priors).
pub fn softmax(logits: &[f32]) -> Vec<f32> {
    let m = logits.iter().cloned().fold(f32::NEG_INFINITY, f32::max);
    let exps: Vec<f32> = logits.iter().map(|&x| (x - m).exp()).collect();
    let sum: f32 = exps.iter().sum();
    if sum > 0.0 {
        exps.iter().map(|&e| e / sum).collect()
    } else {
        vec![1.0 / logits.len() as f32; logits.len()]
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::rngs::StdRng;
    use rand::{RngExt, SeedableRng};

    /// Lädt das aktuelle Produktionsmodell für den Batching-Paritätstest
    /// (Paket 1) -- gleiches Skip-statt-Fail-Muster wie
    /// `net_mcts.rs::load_test_net` (`models/` ist per `.gitignore` nicht Teil
    /// des Checkouts, ein frischer Klon hätte sonst einen harten Testfehler
    /// ohne jeden eigenen Fehler).
    fn load_test_net() -> Option<Net> {
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../models/alphazero_v10_best.onnx");
        match Net::load(path.to_str().unwrap(), crate::features::INPUT_SIZE) {
            Ok(n) => Some(n),
            Err(e) => {
                eprintln!("  ⚠️  {path:?} nicht ladbar ({e}) -- Test übersprungen (kein lokaler Checkpoint).");
                None
            }
        }
    }

    /// Paket 1, Kernabsicherung: `eval_pair(a, b)` muss elementweise (Toleranz
    /// 1e-5) exakt dasselbe liefern wie zwei getrennte `eval(a)` + `eval(b)`
    /// -- der Batch=2-Plan darf die Zahlen nicht verändern, nur die Anzahl
    /// der ONNX-Aufrufe reduzieren. Zufällige Feature-Vektoren reichen hier
    /// (reiner Zahlen-Durchlauf durch den Graphen, keine Spielzustands-
    /// Semantik nötig).
    #[test]
    fn eval_pair_matches_two_single_evals() {
        let Some(net) = load_test_net() else { return };
        let mut rng = StdRng::seed_from_u64(7);
        let close = |x: &[f32], y: &[f32]| -> bool {
            x.len() == y.len() && x.iter().zip(y).all(|(u, v)| (u - v).abs() < 1e-5)
        };
        for trial in 0..5u32 {
            let feats_a: Vec<f32> = (0..net.input_size).map(|_| rng.random_range(-1.0f32..1.0)).collect();
            let feats_b: Vec<f32> = (0..net.input_size).map(|_| rng.random_range(-1.0f32..1.0)).collect();
            let (pa, va, ma, pta) = net.eval(&feats_a).expect("eval a");
            let (pb, vb, mb, ptb) = net.eval(&feats_b).expect("eval b");
            let ((pa2, va2, ma2, pta2), (pb2, vb2, mb2, ptb2)) =
                net.eval_pair(&feats_a, &feats_b).expect("eval_pair");

            assert!(close(&pa, &pa2), "Durchlauf {trial}: policy_a weicht ab");
            assert!(close(&va, &va2), "Durchlauf {trial}: value_a weicht ab");
            assert!(close(&ma, &ma2), "Durchlauf {trial}: moon_a weicht ab");
            assert!(close(&pta, &pta2), "Durchlauf {trial}: points_a weicht ab");
            assert!(close(&pb, &pb2), "Durchlauf {trial}: policy_b weicht ab");
            assert!(close(&vb, &vb2), "Durchlauf {trial}: value_b weicht ab");
            assert!(close(&mb, &mb2), "Durchlauf {trial}: moon_b weicht ab");
            assert!(close(&ptb, &ptb2), "Durchlauf {trial}: points_b weicht ab");
        }
    }
}
