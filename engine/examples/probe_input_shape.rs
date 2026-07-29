//! Beweis-Skript für Task #11 Phase 1 (2D-Encoder-Kompatibilitätsschicht):
//! kann tract-onnx die im ONNX-Graph deklarierte Input-Fact auslesen, BEVOR
//! `with_input_fact(...)` sie überschreibt? Gibt Rang + Dimensionen der
//! deklarierten Input-Fact des ersten Inputs aus.
//!
//! Aufruf: cargo run --example probe_input_shape -- <model.onnx>

use tract_onnx::prelude::*;
use tract_onnx::tract_hir::infer::Factoid;
use tract_onnx::tract_hir::internal::DimLike;

fn main() -> TractResult<()> {
    let mut args = std::env::args().skip(1);
    let model_path = args.next().expect("Arg 1: Pfad zum .onnx-Modell");

    // Rohes InferenceModel VOR jedem with_input_fact-Override -- genau der
    // Zustand, den load_auto() später auswertet, um zwischen dem flachen
    // (Rang 2, [_, N]) und dem 2D-Pfad (Rang 4, [_, C, H, W]) zu unterscheiden.
    let model: InferenceModel = tract_onnx::onnx().model_for_path(&model_path)?;

    println!("Modell: {model_path}");
    println!("Anzahl Inputs: {}", model.inputs.len());

    for (i, outlet) in model.inputs.iter().enumerate() {
        let fact = model.outlet_fact(*outlet)?;
        println!("--- Input {i} ---");
        println!("  outlet: {outlet:?}");
        println!("  fact (Debug): {fact:?}");
        // `shape` ist ein `ShapeFactoid` -- iterierbar über die einzelnen
        // Dimensions-Factoide (jede kann konkret ODER symbolisch/unbekannt sein).
        let rank = fact.shape.rank();
        println!("  rank (roh): {rank:?}");
        if let Some(r) = rank.concretize() {
            println!("  rank (konkret): {r}");
            let mut dims_usize: Vec<Option<usize>> = Vec::new();
            for d in 0..r as usize {
                let dim_factoid = fact.shape.dim(d); // Option<GenericFactoid<TDim>>
                let concretized = dim_factoid.as_ref().and_then(|f| f.concretize()); // Option<TDim>
                let as_usize = concretized.as_ref().and_then(|t| t.to_usize().ok());
                println!("  dim[{d}]: roh={dim_factoid:?} concretized={concretized:?} as_usize={as_usize:?}");
                dims_usize.push(as_usize);
            }
            println!("  => dims_usize: {dims_usize:?}");
        } else {
            println!("  dims: Rang selbst nicht konkret (Debug-Fact oben beachten)");
        }
    }

    Ok(())
}
