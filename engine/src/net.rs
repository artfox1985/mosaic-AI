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

/// Bindeglied zu `net_ort.rs` (Weg B) fuer `eval_batch` -- ZWEI Varianten je
/// nach `ort_cuda_probe`-Feature, damit `net.rs` UNBEDINGT `try_eval_batch`
/// aufrufen kann, ohne selbst zu wissen, ob `ort` ueberhaupt im
/// Abhaengigkeitsbaum ist (`ort` bleibt optional, siehe `Cargo.toml`). Bei
/// aktivem Feature: Knopf pruefen, ORT-CUDA versuchen, bei Fehler EINMAL
/// warnen und `None` liefern (Aufrufer faellt weiter auf tract
/// zurueck). Bei fehlendem Feature: `net_ort` existiert nicht einmal als
/// Modul (siehe `lib.rs`), diese Funktion ist dann ein reiner
/// Kompilierzeit-No-Op (wird zu einem `None`-Literal weginlined).
#[cfg(feature = "ort_cuda_probe")]
mod ort_cuda_hook {
    use super::Net;

    pub(super) fn try_eval_batch(
        net: &Net,
        feats: &[&[f32]],
    ) -> Option<Vec<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)>> {
        if !crate::net_ort::ort_cuda_enabled() {
            return None;
        }
        match crate::net_ort::eval_batch_via_ort_cuda(net, feats) {
            Ok(rows) => Some(rows),
            Err(e) => {
                crate::net_ort::warn_ort_cuda_fallback_once(&e);
                None
            }
        }
    }

    /// Ownership-Verbraucher Teil 1: Pendant fuer den 6-Tupel-Vertrag
    /// (`opp_points` + `ownership`), siehe `Net::eval_batch_ex`.
    #[allow(clippy::type_complexity)]
    pub(super) fn try_eval_batch_ex(
        net: &Net,
        feats: &[&[f32]],
    ) -> Option<Vec<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)>> {
        if !crate::net_ort::ort_cuda_enabled() {
            return None;
        }
        match crate::net_ort::eval_batch_ex_via_ort_cuda(net, feats) {
            Ok(rows) => Some(rows),
            Err(e) => {
                crate::net_ort::warn_ort_cuda_fallback_once(&e);
                None
            }
        }
    }
}
#[cfg(not(feature = "ort_cuda_probe"))]
mod ort_cuda_hook {
    use super::Net;

    pub(super) fn try_eval_batch(
        _net: &Net,
        _feats: &[&[f32]],
    ) -> Option<Vec<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)>> {
        None
    }

    #[allow(clippy::type_complexity)]
    pub(super) fn try_eval_batch_ex(
        _net: &Net,
        _feats: &[&[f32]],
    ) -> Option<Vec<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)>> {
        None
    }
}

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

/// Oberste Batchgroesse, fuer die `eval_batch` einen fest optimierten Plan
/// vorhaelt (Perf-Auftrag, 2026-08-02: Gumbel-Wurzel-Kandidaten-Buendelung).
/// URSPRUENGLICH exakt `net_mcts::GUMBEL_TOP_M` (16) gespiegelt, weil das
/// damals der EINZIGE Aufrufer mit N>2 war (`m_prime <= GUMBEL_TOP_M`).
///
/// Angehoben auf **128** (Verschraenkungs-Auftrag "dann leg los",
/// 2026-08-12, `net_batcher.rs`): der Sammel-Faden buendelt jetzt Zeilen
/// VIELER GLEICHZEITIGER Suchen zu einem `eval_batch`-Aufruf, dessen
/// Ober-Grenze nicht mehr an `GUMBEL_TOP_M` haengt, sondern an der
/// tatsaechlich erreichbaren Fadenzahl. Begruendung fuer GENAU 128, nicht
/// mehr, nicht weniger:
/// - `evaluations/interleave_batch_probe.json::verdict` nennt 128 explizit
///   als den Punkt, an dem die (separat zu bewertende) GPU-Gewinnzone
///   beginnt -- der natuerliche Ziel-Deckel fuer DIESEN Kanal.
/// - Ladezeit-Kosten GEMESSEN (nicht geschaetzt), `examples/
///   net_load_time_probe.rs`, Modell `alphazero_v20_2d_opp_brierbest.onnx`:
///   16 Plaene -> 0,293s, 128 Plaene -> 1,927s (+1,634s einmalig beim
///   Laden). Gegen eine Selfplay-Laufzeit von Minuten bis Stunden (siehe
///   `evaluations/selfplay_time_profile.json`: 500,6s fuer nur 30 Partien)
///   ist das vernachlässigbar.
/// - `eval_batch(128)` selbst (EIN Aufruf, tract/CPU): 30,167ms GEMESSEN --
///   skaliert nahezu LINEAR mit der Batchgroesse (128/16=8x Groesse,
///   30,167/3,333=9,05x Zeit) -- CPU-Batching bringt (anders als GPU) keinen
///   Sub-Linear-Gewinn; das rechtfertigt, den Deckel nicht ÜBER die
///   tatsaechlich angepeilte Ziel-Batchgroesse hinaus aufzublasen, nur weil
///   es ginge.
/// - Speicherkosten der zusaetzlichen Plaene NICHT einzeln gemessen
///   (ungeprueft) -- das Modell selbst ist klein (9MB ONNX), und der
///   RAM-Spielraum fuer die parallele Suche ist grosszuegig (`interleave_
///   batch_probe.json`: 16 GiB Deckel fuer bis zu 10782 gleichzeitige
///   Suchbaeume), Indiz fuer geringes Risiko, kein Beleg.
///
/// ABSICHTLICH als eigene lokale Konstante dupliziert statt aus
/// `net_mcts::GUMBEL_TOP_M` importiert (unveraendert bei 16): `net.rs` ist
/// die tiefere Schicht (net_mcts.rs haengt von net.rs/net_batcher.rs ab,
/// nicht umgekehrt), ein Re-Import wuerde diese Schichtung umkehren. Jedes
/// `net_mcts`-`m_prime` bleibt per Konstruktion `<= GUMBEL_TOP_M=16 <=
/// EVAL_BATCH_MAX_N` -- unbetroffen von der Anhebung. `eval_batch`/der
/// Sammel-Faden (`net_batcher.rs::configured_batch_max`) fallen fuer
/// N > `EVAL_BATCH_MAX_N` weiterhin auf einen klaren Fehler zurueck (kein
/// stiller Bug).
pub const EVAL_BATCH_MAX_N: usize = 128;

/// Geladenes, optimiertes Netz (thread-safe → über rayon teilbar).
pub struct Net {
    model: Model,
    /// Zweiter Plan, Batch fix = 2 (Paket 1, siehe Modul-Kommentar).
    model_pair: Model,
    /// Zusaetzliche fest optimierte Plaene fuer `eval_batch(N)`,
    /// `N in 1..=EVAL_BATCH_MAX_N`, EAGER beim Laden gebaut (Perf-Auftrag,
    /// 2026-08-02) -- exakt dieselbe Technik wie `model`/`model_pair`
    /// (`with_input_fact` auf einen KONKRETEN Batch-Wert statt einer
    /// symbolischen Achse, dann `into_optimized().into_runnable()`, siehe
    /// Modul-Kommentar oben zur Begruendung "fester Shape statt symbolischer
    /// Achse"). Eager statt lazy-mit-Cache: `Net` muss `Sync` bleiben (wird
    /// per `Arc<Net>` unveraendert ueber rayon-Threads geteilt, siehe
    /// `self_play.rs`) -- ein lazy gefuellter Cache braeuchte interne
    /// Mutation (`Mutex`/`RefCell`), die entweder `Sync` bricht (`RefCell`)
    /// oder `.run()` selbst unter einem Lock serialisieren wuerde (`Mutex`
    /// um den ganzen Eintrag) und damit die rayon-Parallelitaet der
    /// Self-Play-/Arena-Laeufe zunichte machen wuerde -- ein `HashMap`, das
    /// NACH dem Bau nie wieder mutiert wird, ist dagegen trivial `Sync`
    /// (nur `&self`-Lesezugriffe zur Laufzeit).
    model_batch: std::collections::HashMap<usize, Model>,
    input_size: usize,
    layout: InputLayout,
    /// Task #28 (`PREREG_task28_aggression.md`, Engine-Vertrag): `true`, wenn
    /// die geladene ONNX-Datei einen ZUSAETZLICHEN Output namens
    /// `"opp_points"` deklariert (Gegner-Punkte-Kopf, hinter allen
    /// bestehenden Outputs angehaengt) -- per Output-NAME erkannt
    /// (`detect_opp_head`), nicht nur per Output-Anzahl, damit ein spaeterer
    /// weiterer Aux-Kopf diese Erkennung nicht bricht. Einmalig beim Laden
    /// bestimmt (siehe `build_from_layout`), danach nur noch gelesen --
    /// Index des `opp_points`-Outputs im ONNX-Graphen (per Namens-Erkennung
    /// beim Laden, `None` = Legacy-Modell ohne den Kopf). AUDIT-F1
    /// 2026-08-05: `eval_ex`/`eval_pair_ex`/`eval_batch_ex` extrahieren ueber
    /// DIESEN Index -- vorher wurde positionsbasiert `out[4]` gelesen, das
    /// ist aber der `ownership`-Head (opp_points liegt real auf Index 5).
    opp_head_index: Option<usize>,
    /// Ownership-Verbraucher Teil 1 (`PREREG_ownership_consumer.md` §1/§5
    /// Punkt 6): Index des `ownership`-Outputs im ONNX-Graphen, per
    /// Namens-Erkennung beim Laden bestimmt (`detect_own_head`), `None` bei
    /// einem Netz ohne den Kopf. GENAU dasselbe Muster wie
    /// `opp_head_index` -- Name statt Position, damit ein weiterer Aux-Kopf
    /// (points_dist/value_wdl_logits/opp_points haengen alle HINTER
    /// `ownership`, siehe `export_onnx.py:121ff`) die Erkennung nicht bricht.
    ///
    /// KOPFBREITE wird hier BEWUSST NICHT geprueft: der amtierende Champion
    /// `v21_2d_brierbest` traegt einen 72 breiten (untrainierten) Kopf, die
    /// Sweep-Checkpoints einen 140 breiten (72 Feld + 68 Konjunktionen, siehe
    /// `neural_net.py:1836-1848`). Beide muessen ladbar bleiben; ueber die
    /// Brauchbarkeit entscheidet der VERBRAUCHER
    /// (`net_mcts::ownership_leaf_shift`), nicht der Lader.
    own_head_index: Option<usize>,
    /// Dateipfad, unter dem dieses Netz geladen wurde (Weg B, `net_ort.rs`
    /// braucht ihn, um AUSSERHALB von tract eine eigene ORT-CUDA-Session auf
    /// derselben `.onnx`-Datei aufzubauen -- tract selbst haelt den Pfad
    /// nirgends vor, nur den geparsten Graphen). Rein additiv: kein
    /// bestehender Aufrufer liest dieses Feld.
    // Nur der ort_cuda_probe-Pfad liest dieses Feld -- ohne das Feature ist
    // es bewusst tot statt hinter cfg versteckt (Struktur-Layout stabil).
    #[cfg_attr(not(feature = "ort_cuda_probe"), allow(dead_code))]
    onnx_path: String,
}

impl Net {
    /// Task #28: `true`, wenn dieses geladene Netz den optionalen
    /// `opp_points`-Output hat (siehe `opp_head_index`-Feld-Doku).
    pub fn has_opp_head(&self) -> bool {
        self.opp_head_index.is_some()
    }
    /// Ownership-Verbraucher Teil 1: `true`, wenn dieses geladene Netz einen
    /// `ownership`-Output hat (siehe `own_head_index`-Feld-Doku). Sagt NICHTS
    /// ueber Breite oder Guete des Kopfes aus.
    pub fn has_own_head(&self) -> bool {
        self.own_head_index.is_some()
    }

    /// ONNX-Ausgabeindex des `opp_points`- bzw. `ownership`-Kopfes (`None` =
    /// kein solcher Output). `pub(crate)` und NUR fuer `net_ort.rs`: der
    /// ORT-Kanal liest dieselben Ausgaenge aus einem EIGENEN Graphen und
    /// braucht dafuer dieselbe (namensbasiert beim Laden bestimmte)
    /// Index-Auskunft wie der tract-Pfad -- sonst haetten die beiden Backends
    /// unterschiedliche Annahmen, genau der AUDIT-F1-Fehler von 2026-08-05.
    #[cfg_attr(not(feature = "ort_cuda_probe"), allow(dead_code))]
    pub(crate) fn opp_head_index(&self) -> Option<usize> {
        self.opp_head_index
    }
    #[cfg_attr(not(feature = "ort_cuda_probe"), allow(dead_code))]
    pub(crate) fn own_head_index(&self) -> Option<usize> {
        self.own_head_index
    }
    /// Deklariertes Input-Layout dieses geladenen Netzes (Task #11 Phase 2,
    /// M3.5: Engine-Verdrahtung) -- Aufrufer nutzen dies, um pro Netz die
    /// passende Feature-Erzeugung zu waehlen (`features::features_for_net`),
    /// statt fest verdrahtet den flachen 708er-Pfad anzunehmen. `Copy`, also
    /// billig per Wert zurueckgegeben.
    pub fn layout(&self) -> InputLayout {
        self.layout
    }

    /// Gesamtlaenge des `&[f32]`-Merkmalspuffers je Position, den
    /// `eval`/`eval_pair`/`eval_batch` erwarten (= `layout().flat_len()`,
    /// hier nur oeffentlich gemacht -- Aufrufer ausserhalb von `net.rs`
    /// (`net_ort.rs`-/`net_batcher.rs`-Tests) brauchen diese Groesse, ohne
    /// `InputLayout::flat_len` selbst oeffentlich machen zu muessen). Rein
    /// additiv, keine bestehende Aufrufstelle betroffen.
    pub fn input_size(&self) -> usize {
        self.input_size
    }

    /// Dateipfad, unter dem dieses Netz geladen wurde (siehe `onnx_path`-
    /// Feld-Doku). `pub(crate)` -- nur `net_ort.rs` braucht das ausserhalb
    /// dieser Datei, kein Grund, es weiter als das nach aussen zu tragen.
    #[cfg_attr(not(feature = "ort_cuda_probe"), allow(dead_code))]
    pub(crate) fn onnx_path(&self) -> &str {
        &self.onnx_path
    }

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
        Net::build_from_layout(base, InputLayout::Flat(input_size), path)
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
        Net::build_from_layout(base, layout, path)
    }

    /// Gemeinsamer Bauschritt für `load`/`load_auto`: fixiert die Input-Fact
    /// auf Batch=1 (für `model`) bzw. Batch=2 (für `model_pair`) gemäß
    /// `layout`, dann `into_optimized().into_runnable()` -- exakt dieselbe
    /// Operationsfolge, die `load` vor Task #11 direkt (unfaktoriert) ausführte.
    /// `path` NEU (Weg B): nur fuer das `onnx_path`-Feld durchgereicht, sonst
    /// unveraendert -- tract selbst braucht den Pfad hier nicht mehr, `base`
    /// ist schon der geparste Graph.
    fn build_from_layout(base: RawModel, layout: InputLayout, path: &str) -> TractResult<Net> {
        // Task #28: NUR am rohen, noch nicht optimierten Graph zuverlaessig
        // lesbar (`into_optimized()` kann Outlet-Reihenfolge/-Labels
        // veraendern) -- analog zu `detect_layout`, das aus demselben Grund
        // ebenfalls vor jedem `apply_input_facts`/`into_optimized` laeuft.
        let opp_head_index = detect_opp_head(&base)?;
        // Ownership-Verbraucher Teil 1: gleiche Stelle, gleiche Begruendung.
        let own_head_index = detect_own_head(&base)?;
        let model = layout
            .apply_input_facts(base.clone(), 1)?
            .into_optimized()?
            .into_runnable()?;
        let model_pair = layout
            .apply_input_facts(base.clone(), 2)?
            .into_optimized()?
            .into_runnable()?;
        // `eval_batch`-Plaene (Perf-Auftrag, 2026-08-02): EAGER fuer
        // `N in 1..=EVAL_BATCH_MAX_N` gebaut, siehe `model_batch`-Feld-
        // Kommentar fuer die Sync-Begruendung. `N=1`/`N=2` dupliziert bewusst
        // `model`/`model_pair` (eigener, unabhaengiger Plan) -- haelt
        // `eval_batch` als eigenstaendigen Pfad einfach/isoliert von
        // `eval`/`eval_pair`, minimal messbarer Mehraufwand beim Laden (siehe
        // `examples/eval_batch_build_cost.rs`), aber NULL Risiko fuer die
        // bestehenden `eval`/`eval_pair`-Pfade (komplett unangetastet).
        let mut model_batch = std::collections::HashMap::with_capacity(EVAL_BATCH_MAX_N);
        for n in 1..EVAL_BATCH_MAX_N {
            let plan = layout.apply_input_facts(base.clone(), n)?.into_optimized()?.into_runnable()?;
            model_batch.insert(n, plan);
        }
        // Letzter Eintrag: `base` selbst (kein weiterer Klon noetig, `base`
        // wird danach nicht mehr gebraucht).
        let plan = layout.apply_input_facts(base, EVAL_BATCH_MAX_N)?.into_optimized()?.into_runnable()?;
        model_batch.insert(EVAL_BATCH_MAX_N, plan);
        Ok(Net {
            model,
            model_pair,
            model_batch,
            input_size: layout.flat_len(),
            layout,
            opp_head_index,
            own_head_index,
            onnx_path: path.to_string(),
        })
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
                    // Auf die MODELLBREITE kuerzen: neue Merkmale haengen
                    // hinten, Altmodelle sehen damit unveraendert ihre ersten
                    // n Werte (Befund 2026-08-25, siehe
                    // `split_planes_flat_batch_src`).
                    buf.extend_from_slice(&s[..n.min(s.len())]);
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
                // Quell-Grenze ist die Breite, die der BAUER liefert -- nicht
                // die des Modells. Sonst verschiebt sich der Flat-Block,
                // sobald der Bauer eine Ebene mehr hat (siehe `..._src`).
                let (planes_buf, flat_buf) = split_planes_flat_batch_src(
                    samples, crate::features::NUM_PLANES_VALUES, planes_len, flat_n);
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
        // Task #32 (`profiling.rs`-Modulkopf "Task #32"): DIREKT im
        // Methodenkoerper statt an den Aufrufstellen instrumentiert, damit
        // JEDER `Net::eval*`-Aufruf erfasst ist, auch solche ausserhalb des
        // Task-#80/#81-`timed_net_eval`-Wrappers (z.B. `lib.rs`, `py.rs`,
        // `self_play.rs::negamax_value`).
        crate::profiling::selfplay_profile::timed(
            crate::profiling::selfplay_profile::SelfplayCat::NetInference,
            || {
                let inputs = self.build_inputs(&[feats])?;
                let out = self.model.run(inputs)?;
                let policy: Vec<f32> = out[0].to_array_view::<f32>()?.iter().copied().collect();
                let value: Vec<f32> = out[1].to_array_view::<f32>()?.iter().copied().collect();
                let moon: Vec<f32> = out[2].to_array_view::<f32>()?.iter().copied().collect();
                let points: Vec<f32> = out[3].to_array_view::<f32>()?.iter().copied().collect();
                Ok((policy, value, moon, points))
            },
        )
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
        // Task #32: siehe `eval`-Kommentar oben.
        crate::profiling::selfplay_profile::timed(
            crate::profiling::selfplay_profile::SelfplayCat::NetInference,
            || {
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
            },
        )
    }

    /// Forward-Pass fuer `feats.len()` UNABHAENGIGE Stellungen in EINEM
    /// Batch=N-Aufruf (Perf-Auftrag, 2026-08-02: Verallgemeinerung von
    /// `eval_pair` auf beliebiges `N` -- gleiche Technik, fest optimierter
    /// Plan statt symbolischer Batch-Achse, siehe `model_batch`-Feld-
    /// Kommentar). Elementweise aequivalent zu `N` sequenziellen
    /// `eval(feats[i])`-Aufrufen (Paritaetstest
    /// `eval_batch_matches_n_single_evals` unten), aber EIN ONNX-Graph-
    /// Durchlauf. Zeile `i` = `feats[i]`, Rueckgabe in derselben Reihenfolge.
    ///
    /// Erfordert `1 <= feats.len() <= EVAL_BATCH_MAX_N` (kein Plan fuer
    /// `N=0` -- ein leerer Batch ist immer ein Aufrufer-Bug, kein
    /// gueltiger Sonderfall; kein Plan fuer `N > EVAL_BATCH_MAX_N`, siehe
    /// dortiger Kommentar) -- sonst ein klarer Fehler statt eines stillen
    /// Fallbacks auf Einzelaufrufe (Aufrufer, die N kennen sollten -- z.B.
    /// `net_mcts`s Gumbel-Wurzel mit `m_prime <= GUMBEL_TOP_M` -- bekommen
    /// so einen sofortigen Fehlschlag statt einer versteckten
    /// Performance-Regression, falls sich die beiden Konstanten je
    /// auseinander bewegen).
    pub fn eval_batch(
        &self,
        feats: &[&[f32]],
    ) -> TractResult<Vec<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)>> {
        // Rangfolge der zwei Backends (festgelegt in `net_ort.rs`-
        // Modulkommentar; Weg A / Torch-IPC ist 2026-08-15 entfernt, gemessen
        // verworfen -- PREREG_gpu_inference_path.md §9: 0,30x/0,55x):
        //   1) Weg B: ORT-CUDA (`net_ort.rs`) -- ZUERST geprueft.
        //   2) tract (Bestandsverhalten) -- IMMER als letzter Fallback.
        // Bei (1) aus (Default) wird `net_ort` ueberhaupt nicht betreten --
        // der Code unten laeuft dann BYTE-IDENTISCH wie vor Weg B.
        // `ort_cuda_hook::try_eval_batch` ist bei fehlendem
        // `ort_cuda_probe`-Feature ein Kompilierzeit-No-Op (siehe dortige
        // Definition unten) -- `ort` bleibt eine optionale Abhaengigkeit,
        // ein Bau ohne das Feature zieht sie nicht herein.
        if let Some(rows) = ort_cuda_hook::try_eval_batch(self, feats) {
            return Ok(rows);
        }
        // Task #32: siehe `eval`-Kommentar oben.
        crate::profiling::selfplay_profile::timed(
            crate::profiling::selfplay_profile::SelfplayCat::NetInference,
            || {
                let n = feats.len();
                let model = self.model_batch.get(&n).ok_or_else(|| {
                    TractError::msg(format!(
                        "eval_batch: kein vorgebauter Plan fuer N={n} (gueltig: 1..={EVAL_BATCH_MAX_N})"
                    ))
                })?;
                let inputs = self.build_inputs(feats)?;
                let out = model.run(inputs)?;
                let policy: Vec<f32> = out[0].to_array_view::<f32>()?.iter().copied().collect();
                let value: Vec<f32> = out[1].to_array_view::<f32>()?.iter().copied().collect();
                let moon: Vec<f32> = out[2].to_array_view::<f32>()?.iter().copied().collect();
                let points: Vec<f32> = out[3].to_array_view::<f32>()?.iter().copied().collect();
                let policy_rows = split_batch_n(policy, n);
                let value_rows = split_batch_n(value, n);
                let moon_rows = split_batch_n(moon, n);
                let points_rows = split_batch_n(points, n);
                Ok((0..n)
                    .map(|i| {
                        (
                            policy_rows[i].clone(),
                            value_rows[i].clone(),
                            moon_rows[i].clone(),
                            points_rows[i].clone(),
                        )
                    })
                    .collect())
            },
        )
    }

    // ── Task #28 (`PREREG_task28_aggression.md`): `opp_points`-erweiterte
    // Varianten. Getrennte Methoden statt `eval`/`eval_pair`/`eval_batch`-
    // Signaturaenderung -- deren 4-Tupel-Rueckgabetyp und ALLE bestehenden
    // Aufrufstellen (net_mcts.rs-Nicht-Blend-Pfade, self_play.rs, py.rs,
    // lib.rs, examples/) bleiben dadurch komplett unangetastet (Additiv-
    // Regel, siehe Modul-Kommentar). Jeweils EIN Forward-Pass liefert
    // ohnehin schon alle ONNX-Outputs -- der 5. Output wird hier nur
    // zusaetzlich ausgelesen, kein zweiter ONNX-Aufruf.

    /// Wie [`Net::eval`], zusaetzlich der optionale `opp_points`-Kopf als 5.
    /// und der optionale `ownership`-Kopf als 6. Rueckgabewert -- jeweils
    /// leerer `Vec`, wenn das Netz den Output nicht hat
    /// (`has_opp_head()`/`has_own_head() == false`) ODER der Graph trotz
    /// erkanntem Kopf unerwartet zu wenige Outputs liefert (defensiv,
    /// sollte durch die Namens-Erkennung beim Laden nie vorkommen).
    ///
    /// Ownership-Verbraucher Teil 1 (`PREREG_ownership_consumer.md`): der 6.
    /// Rueckgabewert ist der ROHE Kopf-Ausgang, also **Logits** (der Kopf
    /// endet auf `nn.Linear` ohne Sigmoid, `neural_net.py:2390-2394`; das
    /// Training nutzt `binary_cross_entropy_with_logits`,
    /// `train.py:1171-1172`). Die Sigmoid-Umrechnung macht der Verbraucher,
    /// nicht diese Schicht -- `net.rs` reicht Koepfe unveraendert durch.
    #[allow(clippy::type_complexity)]
    pub fn eval_ex(
        &self,
        feats: &[f32],
    ) -> TractResult<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)> {
        // Task #32: siehe `eval`-Kommentar oben.
        crate::profiling::selfplay_profile::timed(
            crate::profiling::selfplay_profile::SelfplayCat::NetInference,
            || {
                let inputs = self.build_inputs(&[feats])?;
                let out = self.model.run(inputs)?;
                let policy: Vec<f32> = out[0].to_array_view::<f32>()?.iter().copied().collect();
                let value: Vec<f32> = out[1].to_array_view::<f32>()?.iter().copied().collect();
                let moon: Vec<f32> = out[2].to_array_view::<f32>()?.iter().copied().collect();
                let points: Vec<f32> = out[3].to_array_view::<f32>()?.iter().copied().collect();
                let opp_points: Vec<f32> = match self.opp_head_index {
                    Some(idx) if out.len() > idx => {
                        out[idx].to_array_view::<f32>()?.iter().copied().collect()
                    }
                    _ => Vec::new(),
                };
                let ownership: Vec<f32> = match self.own_head_index {
                    Some(idx) if out.len() > idx => {
                        out[idx].to_array_view::<f32>()?.iter().copied().collect()
                    }
                    _ => Vec::new(),
                };
                Ok((policy, value, moon, points, opp_points, ownership))
            },
        )
    }

    /// Wie [`Net::eval_pair`], zusaetzlich `opp_points` (5. Tupel-Element)
    /// und `ownership` (6.) je Zeile, gleiche Leer-Semantik wie
    /// [`Net::eval_ex`].
    #[allow(clippy::type_complexity)]
    pub fn eval_pair_ex(
        &self,
        feats_a: &[f32],
        feats_b: &[f32],
    ) -> TractResult<(
        (Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>),
        (Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>),
    )> {
        // Task #32: siehe `eval`-Kommentar oben.
        crate::profiling::selfplay_profile::timed(
            crate::profiling::selfplay_profile::SelfplayCat::NetInference,
            || {
                let inputs = self.build_inputs(&[feats_a, feats_b])?;
                let out = self.model_pair.run(inputs)?;
                let policy: Vec<f32> = out[0].to_array_view::<f32>()?.iter().copied().collect();
                let value: Vec<f32> = out[1].to_array_view::<f32>()?.iter().copied().collect();
                let moon: Vec<f32> = out[2].to_array_view::<f32>()?.iter().copied().collect();
                let points: Vec<f32> = out[3].to_array_view::<f32>()?.iter().copied().collect();
                let opp_points: Vec<f32> = match self.opp_head_index {
                    Some(idx) if out.len() > idx => {
                        out[idx].to_array_view::<f32>()?.iter().copied().collect()
                    }
                    _ => Vec::new(),
                };
                let ownership: Vec<f32> = match self.own_head_index {
                    Some(idx) if out.len() > idx => {
                        out[idx].to_array_view::<f32>()?.iter().copied().collect()
                    }
                    _ => Vec::new(),
                };
                let (policy_a, policy_b) = split_batch2(policy);
                let (value_a, value_b) = split_batch2(value);
                let (moon_a, moon_b) = split_batch2(moon);
                let (points_a, points_b) = split_batch2(points);
                let (opp_a, opp_b) = split_batch2(opp_points);
                let (own_a, own_b) = split_batch2(ownership);
                Ok((
                    (policy_a, value_a, moon_a, points_a, opp_a, own_a),
                    (policy_b, value_b, moon_b, points_b, opp_b, own_b),
                ))
            },
        )
    }

    /// Wie [`Net::eval_batch`], zusaetzlich `opp_points` (5. Tupel-Element)
    /// und `ownership` (6.) je Zeile. `split_batch_n` (unveraendert fuer
    /// policy/value/moon/points wiederverwendet) wuerde bei LEEREM
    /// `opp_points`/`ownership` (Modell ohne den Kopf) NICHT `n` leere Zeilen
    /// liefern, sondern eine leere Liste (0/N teilt nicht sauber je Zeile
    /// auf) -- `split_batch_n_or_empty_rows` deckt genau diesen Fall ab,
    /// damit `opp_rows[i]`/`own_rows[i]` fuer JEDES `i in 0..n` definiert
    /// bleibt.
    ///
    /// ORT-CUDA (Weg B): seit dem Ownership-Verbraucher Teil 1 laeuft der
    /// ORT-Kanal AUCH ueber diese Methode (`ort_cuda_hook::try_eval_batch_ex`)
    /// -- noetig, weil der Sammel-Faden (`net_batcher.rs::collector_loop`)
    /// jetzt hier statt bei `eval_batch` einhaengt und seinen GPU-Pfad sonst
    /// verloeren wuerde. Bei ausgeschaltetem Knopf (Default) ODER einem Bau
    /// ohne `--features ort_cuda_probe` (jeder heutige Wheel-Bau) ist der
    /// Aufruf ein No-Op und der tract-Zweig unten laeuft unveraendert.
    #[allow(clippy::type_complexity)]
    pub fn eval_batch_ex(
        &self,
        feats: &[&[f32]],
    ) -> TractResult<Vec<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)>> {
        if let Some(rows) = ort_cuda_hook::try_eval_batch_ex(self, feats) {
            return Ok(rows);
        }
        // Task #32: siehe `eval`-Kommentar oben.
        crate::profiling::selfplay_profile::timed(
            crate::profiling::selfplay_profile::SelfplayCat::NetInference,
            || {
                let n = feats.len();
                let model = self.model_batch.get(&n).ok_or_else(|| {
                    TractError::msg(format!(
                        "eval_batch_ex: kein vorgebauter Plan fuer N={n} (gueltig: 1..={EVAL_BATCH_MAX_N})"
                    ))
                })?;
                let inputs = self.build_inputs(feats)?;
                let out = model.run(inputs)?;
                let policy: Vec<f32> = out[0].to_array_view::<f32>()?.iter().copied().collect();
                let value: Vec<f32> = out[1].to_array_view::<f32>()?.iter().copied().collect();
                let moon: Vec<f32> = out[2].to_array_view::<f32>()?.iter().copied().collect();
                let points: Vec<f32> = out[3].to_array_view::<f32>()?.iter().copied().collect();
                let opp_points: Vec<f32> = match self.opp_head_index {
                    Some(idx) if out.len() > idx => {
                        out[idx].to_array_view::<f32>()?.iter().copied().collect()
                    }
                    _ => Vec::new(),
                };
                let ownership: Vec<f32> = match self.own_head_index {
                    Some(idx) if out.len() > idx => {
                        out[idx].to_array_view::<f32>()?.iter().copied().collect()
                    }
                    _ => Vec::new(),
                };
                let policy_rows = split_batch_n(policy, n);
                let value_rows = split_batch_n(value, n);
                let moon_rows = split_batch_n(moon, n);
                let points_rows = split_batch_n(points, n);
                let opp_rows = split_batch_n_or_empty_rows(opp_points, n);
                let own_rows = split_batch_n_or_empty_rows(ownership, n);
                Ok((0..n)
                    .map(|i| {
                        (
                            policy_rows[i].clone(),
                            value_rows[i].clone(),
                            moon_rows[i].clone(),
                            points_rows[i].clone(),
                            opp_rows[i].clone(),
                            own_rows[i].clone(),
                        )
                    })
                    .collect())
            },
        )
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

/// Reine Namens-Pruefung (Task #28, `PREREG_task28_aggression.md`): der
/// ONNX-Vertrag fuer den kuenftigen Gegner-Punkte-Kopf ist "Modelle MIT dem
/// Kopf haengen GENAU EINEN zusaetzlichen Output namens `opp_points` HINTER
/// allen bestehenden Outputs an" -- Namens- statt Positions-/Anzahl-basiert
/// erkannt, damit ein spaeterer weiterer Aux-Kopf diese Erkennung nicht
/// bricht. Von `detect_opp_head` (die den tract-Graph abfragt) getrennt,
/// damit die eigentliche Entscheidungslogik OHNE ein echtes ONNX-Modell
/// testbar ist -- es existiert noch KEIN exportiertes Netz mit diesem Kopf
/// (Python-Export folgt erst nach diesem Engine-Auftrag, siehe PREREG
/// Abschnitt "Ausfuehrungsplan" Punkt 1 vs. 2) -- gleiches Trennungsmuster
/// wie `combine_layouts`/`detect_layout` oben (siehe `tests::combine_layouts_*`).
/// AUDIT-F1 2026-08-05: liefert den INDEX von `opp_points` statt nur
/// ja/nein. Die Extraktion las vorher positionsbasiert `out[4]` -- das ist
/// laut Export-Vertrag (export_onnx.py) aber der 72-dim `ownership`-Head;
/// `opp_points` haengt HINTER ownership (und ggf. points_dist/
/// value_wdl_logits), bei realen opp-Modellen also Index 5. Der Blend las
/// damit den rohen ownership-Logit von Feld (0,0) als "Gegner-Punkte".
fn output_opp_head_index(names: &[Option<&str>]) -> Option<usize> {
    names.iter().position(|n| *n == Some("opp_points"))
}

/// Liest die ONNX-Output-Namen aus dem ROHEN (noch nicht optimierten) Graph
/// und wertet sie per `output_names_have_opp_head` aus. Muss VOR jedem
/// `apply_input_facts`/`into_optimized()`-Aufruf laufen (siehe
/// `build_from_layout`) -- Optimierung kann Outlet-Reihenfolge/-Labels
/// veraendern, die ONNX-Deklaration selbst ist dagegen immer robust lesbar
/// (analog `detect_layout`s Input-seitiges Pendant).
fn detect_opp_head(model: &RawModel) -> TractResult<Option<usize>> {
    let outlets = model.output_outlets()?;
    let names: Vec<Option<&str>> = outlets.iter().map(|&o| model.outlet_label(o)).collect();
    Ok(output_opp_head_index(&names))
}

/// Ownership-Verbraucher Teil 1 (`PREREG_ownership_consumer.md` §5 Punkt 6):
/// Pendant zu [`output_opp_head_index`] fuer den `ownership`-Ausgang.
/// Namensbasiert aus demselben Grund -- laut `export_onnx.py:121` steht
/// `ownership` heute auf Index 4, aber `points_dist`/`value_wdl_logits`/
/// `opp_points` haengen dahinter und koennen sich verschieben; ein festes
/// `out[4]` waere genau der Fehler, den AUDIT-F1 2026-08-05 fuer
/// `opp_points` schon einmal aufgeraeumt hat (dort wurde der rohe
/// ownership-Logit von Feld (0,0) als "Gegner-Punkte" gelesen).
/// Reine Namens-Pruefung, ohne tract-Graph -> ohne ONNX-Datei testbar.
fn output_own_head_index(names: &[Option<&str>]) -> Option<usize> {
    names.iter().position(|n| *n == Some("ownership"))
}

/// Wie [`detect_opp_head`], fuer `ownership`. Muss aus demselben Grund VOR
/// jedem `apply_input_facts`/`into_optimized()` laufen.
fn detect_own_head(model: &RawModel) -> TractResult<Option<usize>> {
    let outlets = model.output_outlets()?;
    let names: Vec<Option<&str>> = outlets.iter().map(|&o| model.outlet_label(o)).collect();
    Ok(output_own_head_index(&names))
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

/// Verallgemeinerung von `split_batch2` auf `n` Zeilen (Perf-Auftrag,
/// 2026-08-02, `eval_batch`) -- `flat` ist ein row-major `[n, row_width]`-
/// Puffer (Standard-ONNX-Ausgabelayout, Batch als fuehrende Achse), `n`
/// muss `flat.len()` gerade teilen (garantiert: jede der vier Kopf-
/// Ausgaben hat fuer alle `n` Zeilen dieselbe Breite).
// `pub(crate)`: Weg B (`net_ort.rs`) braucht denselben Zeilen-Split fuer
// ORT-Ausgaben wie der tract-Pfad hier -- keine zweite Implementierung, die
// gegen diese hier je auseinanderlaufen koennte.
pub(crate) fn split_batch_n(flat: Vec<f32>, n: usize) -> Vec<Vec<f32>> {
    if n == 0 {
        return Vec::new();
    }
    let row_width = flat.len() / n;
    flat.chunks(row_width.max(1)).map(|c| c.to_vec()).collect()
}

/// Wie `split_batch_n`, aber fuer optionale Koepfe (Task #28 `opp_points`):
/// ein LEERER `flat`-Puffer bedeutet "Kopf fehlt im Modell", nicht "0 Werte
/// pro Zeile" -- `split_batch_n` selbst wuerde dafuer (da `flat.len()/n == 0`
/// UND `flat` leer ist) `chunks(1)` auf einem leeren Slice aufrufen, was 0
/// Chunks statt `n` leerer Zeilen liefert. `eval_batch_ex`s Aufrufer indiziert
/// `opp_rows[i]` aber fuer JEDES `i in 0..n` -- diese Variante haelt die
/// Invariante "genau `n` Zeilen" auch im leeren Fall.
pub(crate) fn split_batch_n_or_empty_rows(flat: Vec<f32>, n: usize) -> Vec<Vec<f32>> {
    if flat.is_empty() {
        return vec![Vec::new(); n];
    }
    split_batch_n(flat, n)
}

/// Puffer-Split für `InputLayout::PlanesPlusFlat` (Task #11 Phase 2): jedes
/// Sample in `samples` ist EIN zusammenhaengender Puffer `[Planes-Teil
/// (planes_len Werte), Flat-Teil (flat_len Werte)]` -- baut daraus ZWEI
/// batch-weise Puffer (Planes zuerst, dann Flat je Sample angehängt), row-
/// major mit Batch als führender Achse (Standard-ONNX-Layout). Reine
/// Arithmetik ohne tract-Aufruf, daher direkt testbar (`tests::split_planes_flat_*`)
/// -- von `Net::build_inputs` für den eigentlichen Tensor-Bau genutzt.
// `pub(crate)`: Weg B (`net_ort.rs::build_ort_inputs`) braucht denselben
// Puffer-Split fuer `InputLayout::PlanesPlusFlat` wie `build_inputs` hier.
pub(crate) fn split_planes_flat_batch(samples: &[&[f32]], planes_len: usize, flat_len: usize) -> (Vec<f32>, Vec<f32>) {
    // Bedeutung UNVERAENDERT: Quell- und Zielbreite des Planes-Blocks sind
    // gleich. Die Kompatibilitaets-Variante ist `..._src` und wird nur dort
    // benutzt, wo ein echter Feature-Puffer auf ein Modell trifft.
    split_planes_flat_batch_src(samples, planes_len, planes_len, flat_len)
}

/// Wie [`split_planes_flat_batch`], aber mit AUSDRUECKLICHER Quell-Laenge des
/// Planes-Blocks -- die Laenge, die der FEATURE-BAUER erzeugt, nicht die, die
/// das Modell erwartet.
///
/// **Warum das getrennt sein muss** (Befund 2026-08-25, vor dem Bau der
/// Erreichbarkeits-Ebenen): die alte Fassung schnitt den Flat-Block mit
/// `s[planes_len .. planes_len + flat_len]` und benutzte damit die
/// MODELL-Laenge als Offset in den Puffer des BAUERS. Solange beide Laengen
/// gleich waren, stimmte das. Sobald der Bauer eine Ebene mehr liefert als
/// ein Altmodell erwartet, verschiebt sich der Flat-Block um genau diese
/// Ebene: die Tensor-FORMEN bleiben gueltig, die WERTE sind falsch. Ein
/// stiller Datenfehler ohne Absturz -- die Sorte, die erst drei Messungen
/// spaeter auffaellt.
///
/// Richtig ist: den Planes-Block ab 0 auf die Modellbreite kuerzen (neue
/// Ebenen haengen hinten), und den Flat-Block ab der QUELL-Grenze lesen und
/// dort ebenfalls kuerzen. Damit bleiben Altmodelle bitgleich, waehrend der
/// Bauer waechst.
pub(crate) fn split_planes_flat_batch_src(
    samples: &[&[f32]],
    src_planes_len: usize,
    planes_len: usize,
    flat_len: usize,
) -> (Vec<f32>, Vec<f32>) {
    let batch = samples.len();
    let mut planes_buf = Vec::with_capacity(batch * planes_len);
    let mut flat_buf = Vec::with_capacity(batch * flat_len);
    for s in samples {
        planes_buf.extend_from_slice(&s[..planes_len]);
        flat_buf.extend_from_slice(&s[src_planes_len..src_planes_len + flat_len]);
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

/// Sucht ein Testmodell und gibt seinen Pfad zurueck, oder `None`, wenn es
/// weder lokal noch als eingefrorenes Artefakt vorliegt. Siehe
/// [`test_model_path`] fuer die harte Variante (Regelfall).
///
/// Suchreihenfolge:
/// 1. `../models/<name>` -- Entwicklungs-Bequemlichkeit: was im Arbeits-
///    bestand liegt, gewinnt.
/// 2. `../models/frozen_champions/<stamm>/model.onnx` -- der Artefakt-Pfad,
///    wobei `<stamm>` aus `<name>` abgeleitet wird: Praefix `alphazero_` und
///    Endung `.onnx` abschneiden. Geprueft am amtierenden Champion:
///    `alphazero_v21_2d_brierbest.onnx` -> `v21_2d_brierbest` ->
///    `../models/frozen_champions/v21_2d_brierbest/model.onnx` (existiert,
///    2026-08-28 im Bestand nachgesehen).
#[cfg(test)]
pub(crate) fn test_model_path_opt(name: &str) -> Option<std::path::PathBuf> {
    let models = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../models");
    let local = models.join(name);
    if local.exists() {
        return Some(local);
    }
    let stem = name.strip_suffix(".onnx").unwrap_or(name);
    let stem = stem.strip_prefix("alphazero_").unwrap_or(stem);
    let artifact = models.join("frozen_champions").join(stem).join("model.onnx");
    artifact.exists().then_some(artifact)
}

/// Pfad zu einem Testmodell -- EINZIGE Stelle, an der Testcode weiss, WO
/// Modelle liegen (vorher: 22 duplizierte `../models/...`-Pfadbauten in sechs
/// Dateien).
///
/// Anlass: das Aufraeumen von `models/` am 2026-08-28. Die alten Champion-
/// Gewichte liegen seither nicht mehr flach in `models/`, sondern nur noch im
/// eingefrorenen Artefakt (`models/frozen_champions/<name>/model.onnx`) --
/// die Tests, die hart auf `../models/alphazero_*.onnx` zeigten, waeren alle
/// gleichzeitig ausgefallen.
///
/// Suchreihenfolge und Namensableitung: siehe [`test_model_path_opt`]. Die
/// Ableitung ist bewusst generisch, damit ein KUENFTIGER Champion keine neue
/// Sonderregel braucht -- wer sein Artefakt nach dem Muster
/// `frozen_champions/<name ohne "alphazero_" und ohne ".onnx">/model.onnx`
/// ablegt, wird automatisch gefunden.
///
/// Fehlt beides, `panic!`t die Funktion (Nutzer-Regel "nie leer gruen": ein
/// Test ohne sein Modell muss LAUT scheitern, nicht still ueberspringen).
/// Wer bewusst ueberspringen will -- etwa fuer ein Alt-Modell ohne Artefakt
/// --, nimmt [`test_model_path_opt`] und dokumentiert das an der Aufrufstelle.
#[cfg(test)]
pub(crate) fn test_model_path(name: &str) -> std::path::PathBuf {
    test_model_path_opt(name).unwrap_or_else(|| {
        let models = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../models");
        let stem = name.strip_suffix(".onnx").unwrap_or(name);
        let stem = stem.strip_prefix("alphazero_").unwrap_or(stem);
        panic!(
            "Testmodell {name:?} liegt WEDER unter {:?} NOCH als eingefrorenes \
             Artefakt unter {:?} -- Test-Voraussetzung fehlt, der Test darf nicht \
             leer-gruen bestehen (Nutzer-Regel: nie leer gruen). Bereitstellen: \
             entweder die Datei nach models/{name} kopieren, oder das Artefakt \
             models/frozen_champions/{stem}/model.onnx anlegen (Ablage eines \
             eingefrorenen Champions), oder den Test bewusst mit --skip abwaehlen.",
            models.join(name),
            models.join("frozen_champions").join(stem).join("model.onnx"),
        )
    })
}

/// Name des AMTIERENDEN Champions aus `models/champion.txt` (ohne
/// `alphazero_`-Praefix, ohne Endung -- genau so, wie `tools/set_champion.py`
/// die Datei schreibt).
///
/// Anlass (Nutzer-Randbedingung 2026-08-28): "es gibt immer nur EINEN
/// Champion, Alt-Champions koennen rausrotieren". Testcode, der einen
/// Modellnamen HART verdrahtet, faellt beim naechsten Aufraeumen von
/// `models/` aus -- genau das ist am 2026-08-28 passiert (Aufraeumen der
/// flachen `models/alphazero_*.onnx`). Wer ein Netz nur als MECHANIK-
/// Traeger braucht (Batcher, Wurzel-Batching, Paritaets-Fixture), nimmt
/// diesen Einstieg und wird damit automatisch mit-rotiert.
///
/// Herkunft der Logik: aus `self_play.rs::tests::load_test_net_for_gating`
/// hierher gehoben (dort seit dem Champion-Pfad-Bugfix), damit die
/// `champion.txt`-Aufloesung EINMAL existiert statt je Modul dupliziert.
///
/// `panic!`t bei fehlender/leerer Datei (Nutzer-Regel "nie leer gruen").
#[cfg(test)]
pub(crate) fn test_champion_name() -> String {
    let champion_txt =
        std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../models/champion.txt");
    let raw = std::fs::read_to_string(&champion_txt).unwrap_or_else(|e| {
        panic!(
            "{champion_txt:?} nicht lesbar ({e}) -- der Test braucht den amtierenden \
             Champion, kein stiller Skip erlaubt (Nutzer-Regel: nie leer gruen)."
        )
    });
    let name = raw.trim().to_string();
    assert!(
        !name.is_empty(),
        "{champion_txt:?} ist leer -- der Test braucht den amtierenden Champion \
         (Nutzer-Regel: nie leer gruen)."
    );
    name
}

/// Pfad zum ONNX des amtierenden Champions -- [`test_champion_name`] plus
/// [`test_model_path`] (findet also sowohl `models/alphazero_<name>.onnx` als
/// auch `models/frozen_champions/<name>/model.onnx`).
#[cfg(test)]
pub(crate) fn test_champion_model_path() -> std::path::PathBuf {
    test_model_path(&format!("alphazero_{}.onnx", test_champion_name()))
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

    /// Lädt den amtierenden Champion für den Batching-Paritätstest (Paket 1).
    /// Bis 2026-08-15 zeigte der Lader auf `alphazero_v10_best.onnx` (existiert
    /// seit dem NUM_ACTIONS-Wechsel nicht mehr) und ÜBERSPRANG bei Abwesenheit
    /// still -- der Test lief seither leer-grün, ohne je zu prüfen. Deshalb
    /// jetzt: existierendes Modell + harter Fehler statt Skip (Nutzer-Regel:
    /// nie leer gruen; Präzedenz `self_play.rs::load_test_net_for_gating`).
    fn load_test_net() -> Net {
        let path = test_model_path("alphazero_v21_2d_brierbest.onnx");
        Net::load_auto(path.to_str().unwrap()).unwrap_or_else(|e| panic!(
            "{path:?} nicht ladbar ({e}) -- Test-Voraussetzung fehlt, der Test darf nicht \
             leer-gruen bestehen (Nutzer-Regel: nie leer gruen). Lokales models/-Checkpoint \
             bereitstellen oder den Test bewusst mit --skip abwaehlen."
        ))
    }

    /// Paket 1, Kernabsicherung: `eval_pair(a, b)` muss elementweise (Toleranz
    /// 1e-5) exakt dasselbe liefern wie zwei getrennte `eval(a)` + `eval(b)`
    /// -- der Batch=2-Plan darf die Zahlen nicht verändern, nur die Anzahl
    /// der ONNX-Aufrufe reduzieren. Zufällige Feature-Vektoren reichen hier
    /// (reiner Zahlen-Durchlauf durch den Graphen, keine Spielzustands-
    /// Semantik nötig).
    #[test]
    fn eval_pair_matches_two_single_evals() {
        let net = load_test_net();
        let mut rng = StdRng::seed_from_u64(7);
        let close = |x: &[f32], y: &[f32]| -> bool {
            x.len() == y.len() && x.iter().zip(y).all(|(u, v)| (u - v).abs() < 1e-5)
        };
        for trial in 0..5u32 {
            let feats_a: Vec<f32> = (0..builder_input_len()).map(|_| rng.random_range(-1.0f32..1.0)).collect();
            let feats_b: Vec<f32> = (0..builder_input_len()).map(|_| rng.random_range(-1.0f32..1.0)).collect();
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

    /// Laedt ein lokal vorhandenes Modell fuer `eval_batch`-Tests. Bis
    /// 2026-08-15 zeigte der Lader auf `alphazero_v18_best.onnx` (inzwischen
    /// ebenfalls aus dem Bestand gefallen) und gab bei Abwesenheit still
    /// `None` -- die drei `eval_batch`-Tests liefen seither leer-gruen.
    /// Jetzt: Champion + harter Fehler statt Skip (Nutzer-Regel: nie leer
    /// gruen).
    /// Vertragliche Eingabelaenge fuer `eval`/`eval_batch`: die Laenge, die
    /// der BAUER liefert, nicht die des Modells. Seit der Bauer breiter sein
    /// darf als ein Altmodell (`split_planes_flat_batch_src`) faellt beides
    /// auseinander -- `net.input_size()` ist die MODELL-Erwartung
    /// (`InputLayout::flat_len`), gefuettert wird aber immer der volle
    /// Bauer-Puffer, den die Schicht dann kuerzt. Tests, die mit
    /// `net.input_size()` synthetisieren, pruefen daher seit 2026-08-25 den
    /// falschen Vertrag (Symptom: `range end index ... out of range`).
    fn builder_input_len() -> usize {
        crate::features::NUM_PLANES_VALUES + crate::features::INPUT_SIZE
    }

    fn load_eval_batch_test_net() -> Net {
        let path = test_model_path("alphazero_v21_2d_brierbest.onnx");
        Net::load_auto(path.to_str().unwrap()).unwrap_or_else(|e| panic!(
            "{path:?} nicht ladbar ({e}) -- Test-Voraussetzung fehlt, der Test darf nicht \
             leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ))
    }

    /// Perf-Auftrag (2026-08-02), Kernabsicherung fuer `eval_batch`: fuer
    /// mehrere `N` muss `eval_batch(feats[0..N])` elementweise (gleiche
    /// Toleranz 1e-5 wie `eval_pair_matches_two_single_evals` oben -- kein
    /// strengerer Anspruch als der bestehende Praezedenzfall, tract liefert
    /// fuer verschiedene Batch-Plaene NICHT garantiert bitgleiche Werte,
    /// siehe dortiger Kommentar) dasselbe liefern wie `N` sequenzielle
    /// `eval()`-Aufrufe. Deckt zusaetzlich `N=1` (Batch=1-eigener Plan,
    /// nicht `self.model` selbst) und `N=EVAL_BATCH_MAX_N` (Randwert) ab.
    #[test]
    fn eval_batch_matches_n_single_evals() {
        let net = load_eval_batch_test_net();
        let mut rng = StdRng::seed_from_u64(11);
        let close = |x: &[f32], y: &[f32]| -> bool {
            x.len() == y.len() && x.iter().zip(y).all(|(u, v)| (u - v).abs() < 1e-5)
        };
        for &n in &[1usize, 2, 3, 5, 9, 16] {
            let feats: Vec<Vec<f32>> = (0..n)
                .map(|_| (0..builder_input_len()).map(|_| rng.random_range(-1.0f32..1.0)).collect())
                .collect();
            let feats_refs: Vec<&[f32]> = feats.iter().map(|v| v.as_slice()).collect();
            let single: Vec<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)> =
                feats.iter().map(|f| net.eval(f).expect("eval")).collect();
            let batched = net.eval_batch(&feats_refs).expect("eval_batch");
            assert_eq!(batched.len(), n, "N={n}: eval_batch muss genau N Ergebnisse liefern");
            for i in 0..n {
                assert!(close(&single[i].0, &batched[i].0), "N={n} Zeile {i}: policy weicht ab");
                assert!(close(&single[i].1, &batched[i].1), "N={n} Zeile {i}: value weicht ab");
                assert!(close(&single[i].2, &batched[i].2), "N={n} Zeile {i}: moon weicht ab");
                assert!(close(&single[i].3, &batched[i].3), "N={n} Zeile {i}: points weicht ab");
            }
        }
    }

    /// `eval_batch` muss fuer nicht vorgebaute Batchgroessen einen klaren
    /// Fehler liefern (kein stiller Fallback, siehe `eval_batch`-Doku).
    #[test]
    fn eval_batch_rejects_batch_size_beyond_max() {
        let net = load_eval_batch_test_net();
        let feats: Vec<f32> = vec![0.0; builder_input_len()];
        let refs: Vec<&[f32]> = (0..EVAL_BATCH_MAX_N + 1).map(|_| feats.as_slice()).collect();
        assert!(net.eval_batch(&refs).is_err(), "N > EVAL_BATCH_MAX_N muss fehlschlagen, nicht still zurueckfallen");
    }

    // ── Task #28 (`PREREG_task28_aggression.md`): `opp_points`-Kopf-Erkennung ──
    // Kein reales Modell mit dem Kopf existiert bislang (Python-Export folgt
    // erst nach diesem Engine-Auftrag) -- die Erkennungslogik ist deshalb rein
    // ueber die Namens-Liste getestet, kein ONNX-Zugriff noetig (analog
    // `combine_layouts_*` oben).

    #[test]
    fn output_opp_head_index_real_export_order_is_five() {
        // REALER Export-Vertrag (export_onnx.py, gegen echtes ONNX
        // verifiziert 2026-08-05): opp_points haengt HINTER ownership.
        // AUDIT-F1: der Vorgaenger-Test liess `ownership` aus der Liste weg
        // und dokumentierte damit genau den Vertrag, den der Export nie
        // erfuellt hat -- die Extraktion las out[4] = ownership (72 Logits)
        // als Gegner-Punkte.
        let names = vec![Some("policy"), Some("value"), Some("moon"), Some("points"),
                         Some("ownership"), Some("opp_points")];
        assert_eq!(output_opp_head_index(&names), Some(5));
    }

    // ── Ownership-Verbraucher Teil 1: `ownership`-Kopf-Erkennung ──
    // Gleiches Muster wie oben: reine Namenslogik, kein ONNX-Zugriff.

    #[test]
    fn output_own_head_index_real_export_order_is_four() {
        // `export_onnx.py:121` (`out_names = [policy, value, moon, points,
        // ownership]`): `ownership` steht auf Index 4, alle spaeteren Koepfe
        // haengen DAHINTER.
        let names = vec![Some("policy"), Some("value"), Some("moon"), Some("points"),
                         Some("ownership"), Some("opp_points")];
        assert_eq!(output_own_head_index(&names), Some(4));
    }

    #[test]
    fn output_own_head_index_absent_and_position_independent() {
        // Alt-Export ohne den Kopf (real: `alphazero_v17_best.onnx`, siehe
        // `eval_ex_matches_eval_on_legacy_model_and_opp_is_empty`).
        let legacy = vec![Some("policy"), Some("value"), Some("moon"), Some("points")];
        assert_eq!(output_own_head_index(&legacy), None);
        assert_eq!(output_own_head_index(&[]), None);
        // Namens- statt positionsbasiert: eine verschobene Reihenfolge findet
        // den Kopf trotzdem (das ist der ganze Zweck der Erkennung).
        let verschoben = vec![Some("policy"), Some("ownership"), Some("value")];
        assert_eq!(output_own_head_index(&verschoben), Some(1));
        // Unbenannte Outlets duerfen nicht faelschlich treffen.
        let unbenannt = vec![None, None, Some("ownership")];
        assert_eq!(output_own_head_index(&unbenannt), Some(2));
    }

    #[test]
    fn output_opp_head_index_with_points_dist_and_wdl_is_last() {
        // Vollausbau (points_dist + value_wdl_logits aktiv): opp_points
        // bleibt laut Export-Doku IMMER der zuletzt angehaengte Output.
        let names = vec![Some("policy"), Some("value"), Some("moon"), Some("points"),
                         Some("ownership"), Some("points_dist"), Some("value_wdl_logits"),
                         Some("opp_points")];
        assert_eq!(output_opp_head_index(&names), Some(7));
    }

    #[test]
    fn output_opp_head_index_absent_on_legacy_model() {
        let names = vec![Some("policy"), Some("value"), Some("moon"), Some("points"),
                         Some("ownership")];
        assert_eq!(output_opp_head_index(&names), None);
    }

    #[test]
    fn output_opp_head_index_ignores_unnamed_or_unlabeled_outlets() {
        // tract liefert `None`, wenn ein Outlet kein explizites Label hat --
        // darf die Suche nicht crashen lassen, nur "nicht gefunden" liefern.
        let names = vec![None, Some("value"), None, Some("points")];
        assert_eq!(output_opp_head_index(&names), None);
    }

    #[test]
    fn output_opp_head_index_is_position_independent() {
        // Namens- statt Positions-basiert: auch wenn `opp_points`
        // (hypothetisch) nicht an letzter Stelle stuende, muss der korrekte
        // Index geliefert werden.
        let names = vec![Some("policy"), Some("opp_points"), Some("value")];
        assert_eq!(output_opp_head_index(&names), Some(1));
    }

    #[test]
    fn output_opp_head_index_empty_list_is_none() {
        assert_eq!(output_opp_head_index(&[]), None);
    }

    // ── Task #28: `split_batch_n_or_empty_rows` (reine Puffer-Arithmetik) ──

    #[test]
    fn split_batch_n_or_empty_rows_empty_input_yields_n_empty_rows() {
        let rows = split_batch_n_or_empty_rows(Vec::new(), 5);
        assert_eq!(rows.len(), 5, "leerer opp-Puffer muss trotzdem N Zeilen liefern");
        assert!(rows.iter().all(|r| r.is_empty()));
    }

    #[test]
    fn split_batch_n_or_empty_rows_nonempty_input_matches_split_batch_n() {
        let flat = vec![1.0f32, 2.0, 3.0, 4.0];
        let expected = split_batch_n(flat.clone(), 2);
        let actual = split_batch_n_or_empty_rows(flat, 2);
        assert_eq!(actual, expected);
    }

    // ── Task #28: `eval_ex` muss auf Legacy-Modellen (kein opp-Kopf) exakt
    // dieselben ersten vier Ausgaben liefern wie `eval` -- byte-identischer
    // Kern, nur ein zusaetzlicher (hier leerer) 5. Wert.

    // ENTFERNT 2026-08-17 (Nutzer-Entscheid): der Test
    // `eval_ex_matches_eval_on_legacy_model_and_opp_is_empty` verlangte ein
    // Modell OHNE `opp_points`- UND OHNE `ownership`-Kopf als Fixture.
    //
    // Warum er weg ist, und zwar aus Ziel- und nicht aus Aufwandsgruenden: er
    // hat zum Ziel dieses Projekts (staerkerer Spieler, Hebel Plattenblick)
    // NICHTS beigetragen. Er versicherte gegen das Laden ausgemusterter
    // Checkpoints -- ein Pfad, den kein Schritt auf dem Weg zu Plattenpunkten
    // beruehrt.
    //
    // Dazu war die Fixture strukturell nicht haltbar: ein grosses,
    // gitignoriertes Gewichtsfile aus der Champion-Linie, in einem Repo, das
    // `models/` regelmaessig aufraeumt. Sie ist ZWEIMAL still verrottet -- erst
    // hing der Test an `v18_best` und lief nach dessen Wegfall wochenlang
    // leer-gruen, dann fehlte `v17_best` und er blockierte den Push.
    //
    // Kein aktuelles Modell kann ihn ersetzen: der Export-Vertrag
    // (`export_onnx.py:121`) haengt den Ownership-Kopf immer an, das gepruefte
    // Szenario ist also nicht mehr erzeugbar. Geprueft 2026-08-17: ALLE
    // verbliebenen Modelle in `models/` liefern `ownership`.
    //
    // Falls die Kopf-Erkennung je wieder abgesichert werden soll, dann mit
    // einer winzigen COMMITTETEN ONNX-Fixture alter Signatur -- nicht mit einem
    // Modell aus der laufenden Linie.
}
