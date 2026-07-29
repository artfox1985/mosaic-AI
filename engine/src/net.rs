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
use tract_onnx::tract_hir::infer::Factoid;
use tract_onnx::tract_hir::internal::DimLike;

type Model = SimplePlan<TypedFact, Box<dyn TypedOp>, Graph<TypedFact, Box<dyn TypedOp>>>;
/// Roh geparster (noch nicht Shape-fixierter) Graph, wie ihn `model_for_path`
/// liefert -- Basis für `with_input_fact`, egal ob Flat- oder Planes-Pfad.
type RawModel = InferenceModel;

/// Deklarierte Input-Form eines geladenen Netzes (Task #11 Phase 1,
/// 2D-Encoder-Kompatibilitätsschicht). Wird EINMAL beim Laden aus der ONNX-
/// Datei selbst bestimmt (`detect_layout`, per `probe_input_shape`-Beispiel
/// belegt: tract liefert die deklarierte, nicht-Batch-Dimension konkret,
/// die Batch-Achse bleibt erwartungsgemäß symbolisch) -- NICHT aus
/// `features::INPUT_SIZE` erraten. Rang 2 `[batch, N]` = der bisherige
/// flache Pfad (alle Bestandsmodelle v1..v18, N=708). Rang 4
/// `[batch, C, H, W]` = neuer 2D-Pfad für künftige Modelle mit Conv-Zweig
/// (siehe docs/design_2d_encoder.md). Jeder andere Rang ist ein Fehler --
/// bewusst kein stiller Fallback.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum InputLayout {
    Flat(usize),
    Planes { c: usize, h: usize, w: usize },
}

impl InputLayout {
    /// Gesamtzahl der Eingabe-Floats pro Sample (N bzw. C*H*W) -- die Länge,
    /// die `eval`/`eval_pair` von ihrem `&[f32]`-Argument erwarten.
    fn flat_len(&self) -> usize {
        match *self {
            InputLayout::Flat(n) => n,
            InputLayout::Planes { c, h, w } => c * h * w,
        }
    }

    fn fact_for_batch(&self, batch: usize) -> InferenceFact {
        match *self {
            InputLayout::Flat(n) => f32::fact([batch, n]).into(),
            InputLayout::Planes { c, h, w } => f32::fact([batch, c, h, w]).into(),
        }
    }
}

/// Geladenes, optimiertes Netz (thread-safe → über rayon teilbar).
pub struct Net {
    model: Model,
    /// Zweiter Plan, Batch fix = 2 (Paket 1, siehe Modul-Kommentar).
    model_pair: Model,
    input_size: usize,
    layout: InputLayout,
}

impl Net {
    /// Lädt ein ONNX-Netz; `input_size` muss zur Feature-Länge passen
    /// (siehe `features::INPUT_SIZE` — dort übergeben, nicht hier hardcoden).
    /// Baut aus derselben geparsten Graph-Struktur ZWEI unabhängig optimierte
    /// Pläne (Batch=1 für `eval`, Batch=2 für `eval_pair`) -- ein `.clone()`
    /// vor dem jeweiligen `with_input_fact`/`into_optimized`, kein zweites
    /// Parsen der Datei von der Platte nötig.
    ///
    /// UNVERÄNDERTES Verhalten ggü. vor Task #11 (Phase 1, 2D-Encoder-
    /// Kompatibilitätsschicht): erzwingt weiterhin IMMER Rang 2 `[batch,
    /// input_size]`, unabhängig davon, was die ONNX-Datei selbst deklariert
    /// -- alle 8 bestehenden Aufrufstellen (`lib.rs`, `py.rs`, `self_play.rs`,
    /// `net_mcts.rs`, `round_transition_deep.rs`, Beispiele) bleiben also
    /// byte-identisch unangetastet. Teilt sich die eigentliche Lade-Logik nur
    /// intern mit `load_auto` (`build_from_layout`) -- kein zweiter,
    /// abweichender Codepfad.
    pub fn load(path: &str, input_size: usize) -> TractResult<Net> {
        let base: RawModel = tract_onnx::onnx().model_for_path(path)?;
        Net::build_from_layout(base, InputLayout::Flat(input_size))
    }

    /// Neuer Konstruktor (Task #11 Phase 1): liest die deklarierte Input-Form
    /// AUS DEM MODELL selbst statt sie vom Aufrufer zu verlangen. Rang 2
    /// `[_, N]` -> `InputLayout::Flat(N)` (bestehendes Verhalten, N=708 für
    /// alle Bestandsmodelle -- `Net::load(path, 708)` und `Net::load_auto(path)`
    /// sind für diese Modelle bit-identisch, siehe
    /// `examples/net_load_auto_backcompat.rs`). Rang 4 `[_, C, H, W]` ->
    /// `InputLayout::Planes` (neuer 2D-Pfad). Jeder andere Rang/nicht-konkrete
    /// Nicht-Batch-Dimension ist ein harter Fehler.
    pub fn load_auto(path: &str) -> TractResult<Net> {
        let base: RawModel = tract_onnx::onnx().model_for_path(path)?;
        let layout = detect_layout(&base)?;
        Net::build_from_layout(base, layout)
    }

    /// Gemeinsamer Bauschritt für `load`/`load_auto`: fixiert die Input-Fact
    /// auf Batch=1 (für `model`) bzw. Batch=2 (für `model_pair`) gemäß
    /// `layout`, dann `into_optimized().into_runnable()` -- exakt dieselbe
    /// Operationsfolge, die `load` vor Task #11 direkt (unfaktoriert) ausführte.
    fn build_from_layout(base: RawModel, layout: InputLayout) -> TractResult<Net> {
        let model = base
            .clone()
            .with_input_fact(0, layout.fact_for_batch(1))?
            .into_optimized()?
            .into_runnable()?;
        let model_pair = base
            .with_input_fact(0, layout.fact_for_batch(2))?
            .into_optimized()?
            .into_runnable()?;
        Ok(Net { model, model_pair, input_size: layout.flat_len(), layout })
    }

    /// Baut den Eingabe-Tensor für `batch` Positionen aus einem flach
    /// aneinandergereihten `&[f32]` (Länge `batch * layout.flat_len()`) --
    /// beim Flat-Layout `[batch, N]` (unverändert ggü. vor Task #11), beim
    /// Planes-Layout `[batch, C, H, W]`.
    fn tensor_from_flat(&self, batch: usize, flat: Vec<f32>) -> TractResult<Tensor> {
        match self.layout {
            InputLayout::Flat(n) => Ok(tract_ndarray::Array2::from_shape_vec((batch, n), flat)?.into()),
            InputLayout::Planes { c, h, w } => {
                Ok(tract_ndarray::Array4::from_shape_vec((batch, c, h, w), flat)?.into())
            }
        }
    }

    /// Forward-Pass für eine Stellung. Gibt (policy_logits, value, moon_logits,
    /// points) -- ONNX-Ausgabereihenfolge aus `export_onnx.py`.
    pub fn eval(
        &self,
        feats: &[f32],
    ) -> TractResult<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)> {
        let input: Tensor = self.tensor_from_flat(1, feats.to_vec())?;
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
        let input: Tensor = self.tensor_from_flat(2, buf)?;
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

/// Liest die im ONNX-Graph DEKLARIERTE Input-Fact aus (VOR jedem
/// `with_input_fact`-Override) und bestimmt daraus das `InputLayout`
/// (Task #11 Phase 1). Beweis, dass das überhaupt geht, siehe
/// `examples/probe_input_shape.rs` -- gegen `alphazero_v18_best.onnx`
/// liefert tract für den einzigen Input `batch,708,F32`: Rang konkret (2),
/// Dim 0 symbolisch (`Sym(batch)`, aus `export_onnx.py`s `dynamic_axes`),
/// Dim 1 konkret (`Val(708)`) -- die Batch-Achse ist erwartungsgemäß NIE
/// konkret (sonst könnte `eval_pair` seinen festen Batch=2-Plan nicht bauen),
/// alle übrigen Achsen sind es bei jedem regulär exportierten Modell
/// (`export_onnx.py` exportiert immer mit `torch.zeros(1, in_size)`/
/// `torch.rand(1, in_size)` als Dummy, die Nicht-Batch-Dims sind also
/// niemals symbolisch). Ein Manifest-Feld als Fallback ist NICHT nötig --
/// die deklarierte Fact ist für jedes bisher exportierte Modell sauber lesbar.
fn detect_layout(model: &RawModel) -> TractResult<InputLayout> {
    let outlet = *model
        .inputs
        .first()
        .ok_or_else(|| TractError::msg("ONNX-Modell hat keinen Input"))?;
    let fact = model.outlet_fact(outlet)?;

    let rank = fact
        .shape
        .rank()
        .concretize()
        .ok_or_else(|| TractError::msg("Input-Rang nicht konkret bestimmbar (symbolischer Rang)"))?;

    let dim_usize = |d: usize| -> TractResult<usize> {
        fact.shape
            .dim(d)
            .and_then(|f| f.concretize())
            .ok_or_else(|| TractError::msg(format!("Input-Dimension {d} nicht konkret (symbolisch/unbekannt)")))?
            .to_usize()
            .map_err(|e| TractError::msg(format!("Input-Dimension {d} nicht in usize konvertierbar: {e}")))
    };

    match rank {
        2 => {
            let n = dim_usize(1)?;
            Ok(InputLayout::Flat(n))
        }
        4 => {
            let c = dim_usize(1)?;
            let h = dim_usize(2)?;
            let w = dim_usize(3)?;
            Ok(InputLayout::Planes { c, h, w })
        }
        other => Err(TractError::msg(format!(
            "Unerwarteter Input-Rang {other} (erwartet 2 = Flat[batch,N] oder 4 = Planes[batch,C,H,W])"
        ))),
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
