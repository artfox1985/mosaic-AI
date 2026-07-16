//! ONNX-Netz-Inferenz via tract-onnx (Network-Modus, Phase B).
//!
//! Lädt ein nach ONNX exportiertes MosaicNet (`export_onnx.py`) und liefert
//! `(policy_logits[NUM_ACTIONS], value[1], moon_logits[5], points[1])`.
//! `value`/`points` sind reine Trainings-Zusatzsignale (siehe
//! stage2_investigation.md: Stufe 2/Netz-Value-Blatt in der SUCHE bleibt
//! tot) -- Stufe 1/3 nutzen weiterhin nur Policy + den exakten DFS-Solver,
//! lesen die beiden Werte also nirgends aus. Reines Rust — keine
//! libtorch/onnxruntime-Abhängigkeit. Batch fix = 1 (eine Stellung pro
//! Forward).

use tract_onnx::prelude::*;

type Model = SimplePlan<TypedFact, Box<dyn TypedOp>, Graph<TypedFact, Box<dyn TypedOp>>>;

/// Geladenes, optimiertes Netz (thread-safe → über rayon teilbar).
pub struct Net {
    model: Model,
    input_size: usize,
}

impl Net {
    /// Lädt ein ONNX-Netz; `input_size` muss zur Feature-Länge passen
    /// (siehe `features::INPUT_SIZE` — dort übergeben, nicht hier hardcoden).
    pub fn load(path: &str, input_size: usize) -> TractResult<Net> {
        let model = tract_onnx::onnx()
            .model_for_path(path)?
            .with_input_fact(0, f32::fact([1, input_size]).into())?
            .into_optimized()?
            .into_runnable()?;
        Ok(Net { model, input_size })
    }

    /// Forward-Pass für eine Stellung. Gibt (policy_logits, value, moon_logits,
    /// points) -- ONNX-Ausgabereihenfolge aus `export_onnx.py`.
    pub fn eval(&self, feats: &[f32]) -> TractResult<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)> {
        let input: Tensor =
            tract_ndarray::Array2::from_shape_vec((1, self.input_size), feats.to_vec())?.into();
        let out = self.model.run(tvec!(input.into()))?;
        let policy: Vec<f32> = out[0].to_array_view::<f32>()?.iter().copied().collect();
        let value: Vec<f32> = out[1].to_array_view::<f32>()?.iter().copied().collect();
        let moon: Vec<f32> = out[2].to_array_view::<f32>()?.iter().copied().collect();
        let points: Vec<f32> = out[3].to_array_view::<f32>()?.iter().copied().collect();
        Ok((policy, value, moon, points))
    }
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
