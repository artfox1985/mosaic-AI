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

/// Deklarierte Input-Form eines geladenen Netzes (Task #11 Phase 1+2,
/// 2D-Encoder-Kompatibilitätsschicht). Wird EINMAL beim Laden aus der ONNX-
/// Datei selbst bestimmt (`detect_layout`, per `probe_input_shape`-Beispiel
/// belegt: tract liefert die deklarierte, nicht-Batch-Dimension konkret,
/// die Batch-Achse bleibt erwartungsgemäß symbolisch) -- NICHT aus
/// `features::INPUT_SIZE` erraten. Rang 2 `[batch, N]` = der bisherige
/// flache Pfad (alle Bestandsmodelle v1..v18, N=708). Rang 4
/// `[batch, C, H, W]` = der Ein-Input-2D-Pfad (Phase 1, nie trainiert).
/// ZWEI Inputs (Rang 4 `[batch,C,H,W]` gefolgt von Rang 2 `[batch,F]`) =
/// `PlanesPlusFlat`, der tatsächlich trainierte Phase-2-2D-Pfad
/// (`Mosaic2DNet`, siehe docs/design_2d_encoder.md Abschnitt 8 Phase-2-
/// Entscheidung: Voll-Broadcast auf ein Rang-4-Tensor verworfen, eval_pair
/// brach dabei auf das 6,5-fache ein -- zwei getrennte Inputs bleiben
/// günstig). Jede andere Kombination ist ein Fehler -- bewusst kein
/// stiller Fallback.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum InputLayout {
    Flat(usize),
    Planes { c: usize, h: usize, w: usize },
    /// Zwei ONNX-Graph-Inputs: Input 0 = Planes `[batch,c,h,w]` (Conv-Zweig),
    /// Input 1 = Flat `[batch,flat]` (der bestehende 708er `state_to_tensor`-
    /// Vektor, unveraendert). `eval`/`eval_pair` erwarten weiterhin EINEN
    /// zusammenhaengenden `&[f32]`-Puffer pro Sample -- Konvention: Planes-
    /// Teil (c*h*w Werte) gefolgt vom Flat-Teil (flat Werte), intern beim
    /// Tensor-Bau in zwei ONNX-Inputs gesplittet (siehe `build_inputs`).
    PlanesPlusFlat { c: usize, h: usize, w: usize, flat: usize },
}

impl InputLayout {
    /// Gesamtzahl der Eingabe-Floats pro Sample -- die Länge, die
    /// `eval`/`eval_pair` von ihrem `&[f32]`-Argument je Position erwarten.
    fn flat_len(&self) -> usize {
        match *self {
            InputLayout::Flat(n) => n,
            InputLayout::Planes { c, h, w } => c * h * w,
            InputLayout::PlanesPlusFlat { c, h, w, flat } => c * h * w + flat,
        }
    }

    /// Fixiert die Input-Fact(s) von `base` auf `batch` gemäß diesem Layout
    /// -- ein `with_input_fact`-Aufruf je ONNX-Graph-Input. Ersetzt das
    /// frühere `fact_for_batch` (Ein-Input-only), gemeinsame Stelle für
    /// `build_from_layout`s Batch=1- und Batch=2-Plan.
    fn apply_input_facts(&self, base: RawModel, batch: usize) -> TractResult<RawModel> {
        match *self {
            InputLayout::Flat(n) => base.with_input_fact(0, f32::fact([batch, n]).into()),
            InputLayout::Planes { c, h, w } => {
                base.with_input_fact(0, f32::fact([batch, c, h, w]).into())
            }
            InputLayout::PlanesPlusFlat { c, h, w, flat } => base
                .with_input_fact(0, f32::fact([batch, c, h, w]).into())?
                .with_input_fact(1, f32::fact([batch, flat]).into()),
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
        let model = layout
            .apply_input_facts(base.clone(), 1)?
            .into_optimized()?
            .into_runnable()?;
        let model_pair = layout
            .apply_input_facts(base, 2)?
            .into_optimized()?
            .into_runnable()?;
        Ok(Net { model, model_pair, input_size: layout.flat_len(), layout })
    }

    /// Baut die ONNX-Eingabe-Tensor(en) für `samples.len()` Positionen --
    /// `samples[i]` ist EIN zusammenhaengender Puffer der Länge
    /// `layout.flat_len()` (Konvention siehe `InputLayout`-Doku). Beim
    /// Flat-/Planes-Layout (unverändert ggü. vor Task #11 Phase 2) EIN
    /// Tensor `[batch, N]` bzw. `[batch, C, H, W]`. Bei `PlanesPlusFlat`
    /// wird jedes Sample intern in Planes-Teil (erste `c*h*w` Werte) und
    /// Flat-Teil (restliche `flat` Werte) gesplittet, dann je Teil
    /// batch-weise zu einem eigenen Tensor zusammengesetzt (ZWEI ONNX-
    /// Graph-Inputs, Reihenfolge Planes zuerst, Flat zweitens -- muss zum
    /// Export in `export_onnx.py`s 2D-Zweig passen).
    fn build_inputs(&self, samples: &[&[f32]]) -> TractResult<TVec<TValue>> {
        let batch = samples.len();
        match self.layout {
            InputLayout::Flat(n) => {
                let mut buf = Vec::with_capacity(batch * n);
                for s in samples {
                    buf.extend_from_slice(s);
                }
                let t: Tensor = tract_ndarray::Array2::from_shape_vec((batch, n), buf)?.into();
                Ok(tvec!(t.into()))
            }
            InputLayout::Planes { c, h, w } => {
                let mut buf = Vec::with_capacity(batch * c * h * w);
                for s in samples {
                    buf.extend_from_slice(s);
                }
                let t: Tensor = tract_ndarray::Array4::from_shape_vec((batch, c, h, w), buf)?.into();
                Ok(tvec!(t.into()))
            }
            InputLayout::PlanesPlusFlat { c, h, w, flat: flat_n } => {
                let planes_len = c * h * w;
                let (planes_buf, flat_buf) = split_planes_flat_batch(samples, planes_len, flat_n);
                let planes_t: Tensor = tract_ndarray::Array4::from_shape_vec((batch, c, h, w), planes_buf)?.into();
                let flat_t: Tensor = tract_ndarray::Array2::from_shape_vec((batch, flat_n), flat_buf)?.into();
                Ok(tvec!(planes_t.into(), flat_t.into()))
            }
        }
    }

    /// Forward-Pass für eine Stellung. Gibt (policy_logits, value, moon_logits,
    /// points) -- ONNX-Ausgabereihenfolge aus `export_onnx.py`.
    pub fn eval(
        &self,
        feats: &[f32],
    ) -> TractResult<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)> {
        let inputs = self.build_inputs(&[feats])?;
        let out = self.model.run(inputs)?;
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
        let inputs = self.build_inputs(&[feats_a, feats_b])?;
        let out = self.model_pair.run(inputs)?;
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
/// Liest Rang + konkrete Nicht-Batch-Dimensionen EINES Inputs (Outlet) aus.
fn concrete_rank(fact: &InferenceFact) -> TractResult<usize> {
    fact.shape
        .rank()
        .concretize()
        .ok_or_else(|| TractError::msg("Input-Rang nicht konkret bestimmbar (symbolischer Rang)"))
        .map(|r| r as usize)
}

fn concrete_dim(fact: &InferenceFact, d: usize) -> TractResult<usize> {
    fact.shape
        .dim(d)
        .and_then(|f| f.concretize())
        .ok_or_else(|| TractError::msg(format!("Input-Dimension {d} nicht konkret (symbolisch/unbekannt)")))?
        .to_usize()
        .map_err(|e| TractError::msg(format!("Input-Dimension {d} nicht in usize konvertierbar: {e}")))
}

/// Rang 2 `[_, N]` -> `Flat(N)`, Rang 4 `[_, C, H, W]` -> `Planes{c,h,w}`.
/// Gemeinsame Auswertung für den Ein-Input-Fall UND je Outlet des
/// Zwei-Input-Falls (Task #11 Phase 2).
fn detect_single_outlet(fact: &InferenceFact) -> TractResult<InputLayout> {
    match concrete_rank(fact)? {
        2 => Ok(InputLayout::Flat(concrete_dim(fact, 1)?)),
        4 => Ok(InputLayout::Planes {
            c: concrete_dim(fact, 1)?,
            h: concrete_dim(fact, 2)?,
            w: concrete_dim(fact, 3)?,
        }),
        other => Err(TractError::msg(format!(
            "Unerwarteter Input-Rang {other} (erwartet 2 = Flat[batch,N] oder 4 = Planes[batch,C,H,W])"
        ))),
    }
}

/// Reine Kombinationslogik (kein tract-Aufruf): leitet aus den je ONNX-Input
/// bereits erkannten Einzel-Layouts das Gesamt-`InputLayout` ab. Von
/// `detect_layout` getrennt, damit die Regel -- EIN Input = Flat/Planes
/// unverändert, ZWEI Inputs NUR in der Reihenfolge Planes(Rang4) dann
/// Flat(Rang2) = `PlanesPlusFlat`, alles andere ein harter Fehler -- ohne
/// echtes ONNX-Modell testbar ist (siehe `tests::combine_layouts_*`).
fn combine_layouts(inputs: &[InputLayout]) -> TractResult<InputLayout> {
    match inputs {
        [] => Err(TractError::msg("ONNX-Modell hat keinen Input")),
        [single] => Ok(*single),
        // Task #11 Phase 2: Zwei-Input-Modell (Mosaic2DNet-Export) -- Input 0
        // MUSS Rang 4 (Planes) sein, Input 1 Rang 2 (Flat), siehe
        // `export_onnx.py`s 2D-Zweig und `InputLayout::PlanesPlusFlat`-Doku.
        [InputLayout::Planes { c, h, w }, InputLayout::Flat(flat)] => {
            Ok(InputLayout::PlanesPlusFlat { c: *c, h: *h, w: *w, flat: *flat })
        }
        [a, b] => Err(TractError::msg(format!(
            "Zwei-Input-Modell mit unerwarteter Kombination (erwartet Input 0 = Planes[batch,C,H,W], \
             Input 1 = Flat[batch,N]): {a:?} / {b:?}"
        ))),
        other => Err(TractError::msg(format!(
            "Unerwartete Anzahl ONNX-Inputs: {} (erwartet 1 = Flat/Planes oder 2 = PlanesPlusFlat)",
            other.len()
        ))),
    }
}

fn detect_layout(model: &RawModel) -> TractResult<InputLayout> {
    let mut layouts = Vec::with_capacity(model.inputs.len());
    for &outlet in &model.inputs {
        let fact = model.outlet_fact(outlet)?;
        layouts.push(detect_single_outlet(fact)?);
    }
    combine_layouts(&layouts)
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

/// Puffer-Split für `InputLayout::PlanesPlusFlat` (Task #11 Phase 2): jedes
/// Sample in `samples` ist EIN zusammenhaengender Puffer `[Planes-Teil
/// (planes_len Werte), Flat-Teil (flat_len Werte)]` -- baut daraus ZWEI
/// batch-weise Puffer (Planes zuerst, dann Flat je Sample angehängt), row-
/// major mit Batch als führender Achse (Standard-ONNX-Layout). Reine
/// Arithmetik ohne tract-Aufruf, daher direkt testbar (`tests::split_planes_flat_*`)
/// -- von `Net::build_inputs` für den eigentlichen Tensor-Bau genutzt.
fn split_planes_flat_batch(samples: &[&[f32]], planes_len: usize, flat_len: usize) -> (Vec<f32>, Vec<f32>) {
    let batch = samples.len();
    let mut planes_buf = Vec::with_capacity(batch * planes_len);
    let mut flat_buf = Vec::with_capacity(batch * flat_len);
    for s in samples {
        planes_buf.extend_from_slice(&s[..planes_len]);
        flat_buf.extend_from_slice(&s[planes_len..planes_len + flat_len]);
    }
    (planes_buf, flat_buf)
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

    // ── Task #11 Phase 2: Layout-Erkennung + Puffer-Split (rein, kein ONNX) ──

    #[test]
    fn flat_len_matches_layout_variant() {
        assert_eq!(InputLayout::Flat(708).flat_len(), 708);
        assert_eq!(InputLayout::Planes { c: 76, h: 6, w: 6 }.flat_len(), 76 * 6 * 6);
        assert_eq!(
            InputLayout::PlanesPlusFlat { c: 76, h: 6, w: 6, flat: 708 }.flat_len(),
            76 * 6 * 6 + 708
        );
    }

    #[test]
    fn combine_layouts_single_input_passes_through() {
        let flat = InputLayout::Flat(708);
        assert_eq!(combine_layouts(&[flat]).unwrap(), flat);
        let planes = InputLayout::Planes { c: 76, h: 6, w: 6 };
        assert_eq!(combine_layouts(&[planes]).unwrap(), planes);
    }

    #[test]
    fn combine_layouts_two_inputs_planes_then_flat_is_planes_plus_flat() {
        let planes = InputLayout::Planes { c: 76, h: 6, w: 6 };
        let flat = InputLayout::Flat(708);
        let combined = combine_layouts(&[planes, flat]).expect("gueltige Kombination");
        assert_eq!(combined, InputLayout::PlanesPlusFlat { c: 76, h: 6, w: 6, flat: 708 });
    }

    #[test]
    fn combine_layouts_two_inputs_wrong_order_is_a_hard_error() {
        // Flat zuerst, Planes zweitens -- NICHT die vereinbarte Konvention
        // (Planes muss Input 0 sein) -- muss fehlschlagen, kein stiller Fallback.
        let flat = InputLayout::Flat(708);
        let planes = InputLayout::Planes { c: 76, h: 6, w: 6 };
        assert!(combine_layouts(&[flat, planes]).is_err());
    }

    #[test]
    fn combine_layouts_two_flat_inputs_is_a_hard_error() {
        assert!(combine_layouts(&[InputLayout::Flat(708), InputLayout::Flat(5)]).is_err());
    }

    #[test]
    fn combine_layouts_zero_or_three_inputs_is_a_hard_error() {
        assert!(combine_layouts(&[]).is_err());
        let flat = InputLayout::Flat(708);
        assert!(combine_layouts(&[flat, flat, flat]).is_err());
    }

    #[test]
    fn split_planes_flat_batch_splits_each_sample_and_concatenates_per_part() {
        // 2 Samples, planes_len=3, flat_len=2 -- je Sample [p0,p1,p2,f0,f1].
        let sample_a: Vec<f32> = vec![1.0, 2.0, 3.0, 100.0, 200.0];
        let sample_b: Vec<f32> = vec![4.0, 5.0, 6.0, 300.0, 400.0];
        let (planes_buf, flat_buf) =
            split_planes_flat_batch(&[&sample_a, &sample_b], 3, 2);
        assert_eq!(planes_buf, vec![1.0, 2.0, 3.0, 4.0, 5.0, 6.0]);
        assert_eq!(flat_buf, vec![100.0, 200.0, 300.0, 400.0]);
    }

    #[test]
    fn split_planes_flat_batch_single_sample_roundtrips() {
        let sample: Vec<f32> = (0..79).map(|i| i as f32).collect(); // 76 planes + 3 flat
        let (planes_buf, flat_buf) = split_planes_flat_batch(&[&sample], 76, 3);
        assert_eq!(planes_buf.len(), 76);
        assert_eq!(flat_buf.len(), 3);
        assert_eq!(planes_buf, sample[..76].to_vec());
        assert_eq!(flat_buf, sample[76..].to_vec());
    }

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
