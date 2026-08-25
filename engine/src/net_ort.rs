//! Weg B (`evaluations/PREREG_gpu_inference_path.md` §3/§6/§11, Nutzer-Auftrag
//! "fang an" 2026-08-12): optionaler ONNX-Runtime-CUDA-Kanal statt tract,
//! NUR fuer [`crate::net::Net::eval_batch`] und (seit dem Ownership-
//! Verbraucher Teil 1) [`crate::net::Net::eval_batch_ex`], das dieselbe
//! Session ueber dieselbe Extraktion bedient -- gleiche Idee wie der 2026-08-15
//! entfernte Weg A (Torch/IPC, gemessen verworfen, PREREG §9), aber ohne
//! Prozessgrenze: kein Python, kein IPC-Rundlauf, ein Speicherbild. GEDECKT
//! nach Regel 3 (§11: 7,0x-18,5x gegen den tract-CPU-Bezug, vom Nutzer aus
//! `evaluations/ort_cuda_batch_throughput.json` nachgeprueft).
//!
//! `#![cfg(feature = "ort_cuda_probe")]` unten: diese Datei wird nur
//! compiliert, wenn das Feature aktiv ist -- `ort` bleibt eine OPTIONALE
//! Abhaengigkeit (`Cargo.toml`), ein Bau ohne `--features ort_cuda_probe`
//! (also jeder heutige Wheel-Bau) zieht `ort`/die CUDA-DLLs ueberhaupt nicht
//! herein. Die `mod net_ort;`-Deklaration in `lib.rs` ist ebenfalls
//! `#[cfg(feature = "ort_cuda_probe")]`-gated -- doppelt abgesichert, falls
//! diese Zeile hier je entfernt wuerde.
//!
//! ## Rangfolge der zwei Backends (festgelegt hier, verdrahtet in
//! `net.rs::eval_batch`)
//!
//! 1. **ORT-CUDA** (dieses Modul) -- geprueft ZUERST. Wenn `MOSAIC_ORT_CUDA_
//!    ENABLED=1` UND das Feature beim Bauen aktiv war UND die Session fuer
//!    dieses `Net` erfolgreich aufgebaut werden konnte (oder schon aufgebaut
//!    ist), laeuft der Batch hierueber.
//! 2. **tract** (Bestandsverhalten) -- IMMER als letzter Fallback verfuegbar,
//!    NIE abschaltbar. Bei Schritt 1 aus (Default) wird dieses Modul
//!    ueberhaupt nicht betreten -- byte-identisches Bestandsverhalten.
//!
//! (Der fruehere Schritt 2, Weg A / Torch-IPC aus `net_ipc.rs`, ist am
//! 2026-08-15 entfernt worden -- gemessen verworfen, PREREG §9:
//! 0,30x/0,55x gegen synchrones tract.)
//!
//! ## Knopf (Default AUS = Bestandsverhalten)
//!
//! `MOSAIC_ORT_CUDA_ENABLED=1` (siehe [`ort_cuda_enabled`]). Wirkt nur,
//! wenn das Crate mit `--features ort_cuda_probe` gebaut wurde -- sonst ist
//! der Knopf wirkungslos (kein Fehler, der ganze Codepfad existiert nicht).
//!
//! ## Session-Aufbau: EINMAL je `Net`-Instanz, wiederverwendet
//!
//! ONNX Runtime kennt (anders als tracts feste Batch=N-Plaene, siehe
//! `net.rs::EVAL_BATCH_MAX_N`/`model_batch`) eine SYMBOLISCHE Batch-Achse --
//! EINE Session bedient JEDE Batchgroesse, kein Plan je N noetig (das war
//! bereits in `examples/ort_cuda_batch_probe.rs` so: eine Session, alle 13
//! Batch-Punkte 1..512 nacheinander). Der Aufbau selbst (CUDA-Kontext,
//! cuDNN-Algorithmus-Suche) ist NICHT billig -- deshalb [`SESSIONS`], eine
//! nach Zeiger-Identitaet des `Net` schluesselnde Registry, exakt dasselbe
//! Muster wie `net_batcher.rs::REGISTRY`/`ensure_batcher_for` (dortiger
//! Kommentar "Registrierung nach Zeigeridentitaet" gilt hier unveraendert:
//! sicher, WEIL dieselbe `Net`-Instanz -- typischerweise hinter einem
//! `Arc<Net>` -- fuer die gesamte Laufzeit eines Selfplay-/Arena-Laufs lebt).
//!
//! Thread-Sicherheit: der Sammel-Faden des Batchers (`net_batcher.rs`) ist
//! heute der einzige *erwartete* Aufrufer von `eval_batch` bei eingeschalteter
//! Verschraenkung, aber `eval_batch` selbst ist auch direkt (ohne Batcher)
//! von mehreren Suchfaeden aus aufrufbar (`Net: Sync`, per `Arc` geteilt,
//! siehe `net.rs`-Feldkommentar). [`SessionSlot::Ready`] haelt die Session
//! deshalb hinter einem eigenen `Mutex` (ONNX Runtimes `Session::run`
//! verlangt `&mut self` in der `ort`-Rust-API, auch wenn der zugrunde
//! liegende C-Aufruf laut `ort`-Quelltext nebenlaeufigkeitssicher waere --
//! `unsafe impl Send + Sync for Session` in `ort` selbst, aber die
//! Rust-Signatur zwingt trotzdem exklusiven Zugriff). Der AEUSSERE
//! Registry-Mutex wird nur fuer die Kartensuche/den (seltenen) Erstaufbau
//! gehalten, NICHT waehrend `run()` -- verschiedene `Net`-Instanzen blockieren
//! sich damit beim Inferieren nicht gegenseitig, nur gleichzeitige Aufrufe
//! FUER DASSELBE `Net` serialisieren sich am inneren Mutex.
//!
//! ## Fallback
//!
//! Jeder Fehler -- Session-Aufbau (CUDA-Provider nicht registrierbar, Modell
//! nicht ladbar) ODER der Inferenz-Aufruf selbst -- liefert `Err(String)`
//! aus [`eval_batch_via_ort_cuda`], NIE ein Panic. Der Aufrufer
//! (`net.rs::eval_batch`) faengt das ab, loggt einmalig
//! ([`warn_ort_cuda_fallback_once`]) und faellt weiter auf Schritt 2/3
//! zurueck. `error_on_failure()` beim CUDA-Provider (siehe [`build_session`])
//! ist ABSICHTLICH gesetzt: ohne diese Option wuerde `ort` bei einem nicht
//! registrierbaren CUDA-Provider intern STILL auf seinen EIGENEN
//! CPU-Provider zurueckfallen -- das waere ein zweiter, redundanter
//! CPU-Pfad, der sich als "ORT-CUDA" ausgibt, aber keinen GPU-Vorteil liefert
//! und obendrein Zeit kostet. Mit `error_on_failure()` bekommen WIR den
//! Fehler zurueck und entscheiden selbst, dass tract (der validierte,
//! gemessene CPU-Pfad) der richtige Fallback ist, nicht ORTs eigener.
//! Ein einmal als nicht aufbaubar erkannter Session-Slot wird fuer die
//! Prozesslaufzeit NICHT erneut versucht -- bewusste Vereinfachung: kein
//! periodischer Retry, kein Health-Check-Thread.
//!
//! ## Was NICHT Teil dieses Moduls ist
//!
//! - Kein Umbau des Batchers (`net_batcher.rs`) -- er ruft weiterhin nur
//!   `Net::eval_batch` und weiss nichts von ORT.
//! - Keine Aenderung an `EVAL_BATCH_MAX_N` oder der Batch-Groesse-Logik.
//! - Keine DLL-Verpackungs-/Wheel-Loesung. Fuer einen Wheel-Bau mit diesem
//!   Feature muessten die ORT-CUDA-Provider-DLLs UND die Torch-CUDA-12-
//!   Laufzeit-DLLs (siehe `evaluations/PREREG_gpu_inference_path.md` §11) neben
//!   die `.pyd` gelangen -- die Handkopie, die fuer die Kennlinien-Messung
//!   reichte, ist dafuer NICHT die Loesung. Offene Frage, nicht Teil dieses
//!   Schritts.
//! - `InputLayout::Planes` (reiner Rang-4-Einzel-Input) ist NICHT
//!   unterstuetzt -- dieser Layout-Fall stammt nur aus einem Test-Export
//!   (`selftest_2d_encoder.py`/`net_2d_probe.rs`), `export_onnx.py` erzeugt
//!   ihn nie (GEPRUEFT: nur zwei `input_names`-Stellen dort, `["state"]` und
//!   `["planes", "state"]"). Ein produktives Modell trifft diesen Zweig also
//!   nicht; er liefert einen klaren `Err` (-> Fallback), keine Vermutung
//!   ueber einen ungeprueften Eingabenamen.

#![cfg(feature = "ort_cuda_probe")]

use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

use ort::ep::CUDA;
use ort::session::{Session, SessionInputValue};
use ort::value::Tensor;

use crate::net::{split_batch_n, split_batch_n_or_empty_rows, split_planes_flat_batch_src, InputLayout, Net};

/// Liest eine `MOSAIC_*`-Bool-Env-Var einmalig -- lokal dupliziert statt
/// importiert (gleiches Muster wie `net_mcts.rs`/`tiling_solver.rs`: Module
/// sollen unabhaengig voneinander bleiben, kein Kreuz-Import zwischen den
/// Backend-Kanaelen).
fn read_bool_env_once(cell: &'static OnceLock<bool>, name: &str, default: bool) -> bool {
    *cell.get_or_init(|| match std::env::var(name) {
        Ok(v) => v != "0" && !v.trim().is_empty(),
        Err(_) => default,
    })
}

static ORT_CUDA_ENABLED: OnceLock<bool> = OnceLock::new();

/// `MOSAIC_ORT_CUDA_ENABLED=1` (oder jeder nicht-"0"/nicht-leere Wert)
/// schaltet den Weg-B-Kanal ein. Default AUS -- siehe Modul-Kommentar.
pub(crate) fn ort_cuda_enabled() -> bool {
    read_bool_env_once(&ORT_CUDA_ENABLED, "MOSAIC_ORT_CUDA_ENABLED", false)
}

/// Einmalige Warnung, wenn der Knopf an, aber die Session nicht (mehr)
/// nutzbar ist -- gleiches "einmal loggen"-Muster wie
/// `net_mcts::warn_missing_opp_head_once`.
static WARNED_ORT_CUDA_FALLBACK: OnceLock<()> = OnceLock::new();

pub(crate) fn warn_ort_cuda_fallback_once(reason: &str) {
    WARNED_ORT_CUDA_FALLBACK.get_or_init(|| {
        eprintln!(
            "⚠️  MOSAIC_ORT_CUDA_ENABLED=1 gesetzt, aber der ORT-CUDA-Kanal ist nicht \
             nutzbar ({reason}) -- falle auf tract zurueck (siehe \
             PREREG_gpu_inference_path.md §11). Diese Meldung erscheint \
             nur einmal je Prozess."
        );
    });
}

/// Registrierter Zustand je `Net`-Instanz (Zeiger-Identitaet, siehe
/// Modul-Kommentar). `Unavailable` ist ENDGUELTIG fuer die Prozesslaufzeit --
/// kein Retry (siehe Modul-Kommentar "Fallback").
enum SessionSlot {
    Ready(Mutex<Session>),
    Unavailable,
}

static SESSIONS: OnceLock<Mutex<HashMap<usize, std::sync::Arc<SessionSlot>>>> = OnceLock::new();

fn registry() -> &'static Mutex<HashMap<usize, std::sync::Arc<SessionSlot>>> {
    SESSIONS.get_or_init(|| Mutex::new(HashMap::new()))
}

/// Baut die CUDA-Session fuer `onnx_path`. `error_on_failure()`: siehe
/// Modul-Kommentar "Fallback". Device 0 (einzige unterstuetzte GPU auf der
/// Zielumgebung, kein eigener Knopf -- ausserhalb des Auftrags-Zuschnitts,
/// siehe Bericht Punkt 6). `with_tf32(false)`: siehe Kommentar direkt am
/// Aufruf unten -- TF32 (reduzierte Praezision auf Ampere+) explizit
/// ausgeschaltet, kein eigener Knopf dafuer (Ergebnisgleichheit mit tract
/// ist der Zweck dieses Backends, nicht Durchsatz um den Preis der
/// Praezision).
fn build_session(onnx_path: &str) -> Result<Session, String> {
    // TF32-Verdacht (Nutzer-Auftrag 2026-08-12, vor dem Arena-Lauf geprueft):
    // `with_tf32(false)` -- GEPRUEFT gegen `ort` 2.0.0-rc.12s Dokumentation
    // (`ort-2.0.0-rc.12/src/ep/cuda.rs:276-297`, Provider-Option `use_tf32`):
    // "This option is disabled by default." Explizit auf `false` gesetzt statt
    // sich auf diesen dokumentierten Default zu verlassen -- doppelte
    // Absicherung, und macht den Zustand fuer den folgenden Entscheidungs-
    // gleichheitstest UNZWEIDEUTIG (siehe PREREG_gpu_inference_path.md §13 fuer
    // das Messergebnis: die dortige Tabelle entscheidet, ob TF32 die Ursache
    // war -- nicht diese Zeile allein).
    let cuda_ep = CUDA::default().with_device_id(0).with_tf32(false).build().error_on_failure();
    let session_result: ort::Result<Session> = Session::builder().and_then(|b| {
        b.with_execution_providers([cuda_ep])
            .map_err(|e| -> ort::Error { e.into() })
            .and_then(|mut b| b.commit_from_file(onnx_path))
    });
    session_result.map_err(|e| e.to_string())
}

/// Holt den registrierten Slot fuer `net` oder baut ihn (EINMAL, siehe
/// Modul-Kommentar). Haelt den Registry-Mutex ueber den GESAMTEN Erstaufbau
/// -- exakt dasselbe Muster wie `net_batcher::ensure_batcher_for`
/// (`map.entry(key).or_insert_with(...)` unter EINEM Lock), einfacher als
/// ein Doppel-Check-Locking und fuer diesen seltenen Fall (Aufbau passt
/// faktisch einmal je `Net`-Instanz zu Laufbeginn) ausreichend.
fn get_or_build_session(net: &Net) -> std::sync::Arc<SessionSlot> {
    let key = net as *const Net as usize;
    let mut map = registry().lock().unwrap();
    std::sync::Arc::clone(map.entry(key).or_insert_with(|| {
        std::sync::Arc::new(match build_session(net.onnx_path()) {
            Ok(session) => SessionSlot::Ready(Mutex::new(session)),
            Err(e) => {
                warn_ort_cuda_fallback_once(&e);
                SessionSlot::Unavailable
            }
        })
    }))
}

/// Baut die ORT-Eingabetensoren fuer `feats` gemaess `layout` -- Pendant zu
/// `net.rs::Net::build_inputs`, aber fuer `ort`-Tensoren statt tract-Tensoren.
/// Eingabenamen "planes"/"state" GEPRUEFT gegen `export_onnx.py:147,237`
/// (`input_names=["state"]` bzw. `["planes", "state"]`).
fn build_ort_inputs(layout: InputLayout, feats: &[&[f32]]) -> Result<Vec<(&'static str, SessionInputValue<'static>)>, String> {
    let batch = feats.len();
    match layout {
        InputLayout::Flat(n) => {
            let mut buf = Vec::with_capacity(batch * n);
            for f in feats {
                buf.extend_from_slice(f);
            }
            let t = Tensor::<f32>::from_array(([batch, n], buf.into_boxed_slice())).map_err(|e| e.to_string())?;
            Ok(vec![("state", t.into())])
        }
        InputLayout::PlanesPlusFlat { c, h, w, flat } => {
            // Wie in `net::build_inputs`: Quell-Grenze ist die Bauer-Breite,
            // damit Altmodelle einen korrekt ausgerichteten Flat-Block sehen.
            let (planes_buf, flat_buf) = split_planes_flat_batch_src(
                feats, crate::features::NUM_PLANES_VALUES, c * h * w, flat);
            let planes_t = Tensor::<f32>::from_array(([batch, c, h, w], planes_buf.into_boxed_slice()))
                .map_err(|e| e.to_string())?;
            let flat_t = Tensor::<f32>::from_array(([batch, flat], flat_buf.into_boxed_slice()))
                .map_err(|e| e.to_string())?;
            Ok(vec![("planes", planes_t.into()), ("state", flat_t.into())])
        }
        InputLayout::Planes { .. } => {
            // Siehe Modul-Kommentar "Was NICHT Teil dieses Moduls ist" --
            // kein Produktionsmodell trifft diesen Zweig.
            Err("InputLayout::Planes (reiner Rang-4-Einzel-Input) ist im ORT-CUDA-Pfad nicht unterstuetzt -- kein export_onnx.py-Zweig erzeugt ihn".to_string())
        }
    }
}

/// Forward-Pass fuer `feats.len()` Positionen ueber ORT-CUDA (Weg B) --
/// Ersatz-Backend fuer `net.rs::Net::eval_batch`, GLEICHER Rueckgabe-Vertrag
/// ((policy, value, moon, points) je Zeile, gleiche Reihenfolge wie die
/// Eingabe, Ausgaben per INDEX 0..3 gelesen -- exakt wie der tract-Pfad in
/// `net.rs::eval_batch`, NICHT per Name, fuer identische Annahmen zwischen
/// beiden Backends).
///
/// NIE ein Panic: jeder Fehlerfall (Session-Aufbau, Tensor-Bau,
/// `session.run`, Ausgaben-Extraktion) wird als `Err(String)` an den
/// Aufrufer zurueckgegeben, der (in `net.rs::eval_batch`) auf tract
/// zurueckfaellt.
pub(crate) fn eval_batch_via_ort_cuda(
    net: &Net,
    feats: &[&[f32]],
) -> Result<Vec<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)>, String> {
    // Duenne Huelle ueber die 6-Tupel-Variante -- die beiden Vertraege sollen
    // sich nicht auseinanderentwickeln koennen. Die zusaetzlichen Extraktionen
    // dort sind bei einem Modell OHNE den jeweiligen Kopf ein reiner
    // `Option`-Test (kein Tensor-Zugriff), bei einem Modell MIT Kopf ein
    // Kopiervorgang aus einem Tensor, den ORT ohnehin schon berechnet hat.
    Ok(eval_batch_ex_via_ort_cuda(net, feats)?
        .into_iter()
        .map(|(p, v, m, pt, _opp, _own)| (p, v, m, pt))
        .collect())
}

/// Ownership-Verbraucher Teil 1 (`PREREG_ownership_consumer.md` §5 Punkt 6):
/// 6-Tupel-Variante von [`eval_batch_via_ort_cuda`], Vertrag identisch zu
/// `net.rs::Net::eval_batch_ex` ((policy, value, moon, points, opp_points,
/// ownership) je Zeile).
///
/// Die beiden Zusatz-Koepfe werden -- anders als die Ausgaben 0..3 -- ueber
/// den beim Laden NAMENSBASIERT bestimmten Index gelesen
/// (`Net::opp_head_index`/`Net::own_head_index`), exakt wie im tract-Pfad.
/// Ein fester Positionsindex waere hier derselbe Fehler wie AUDIT-F1
/// 2026-08-05 (`out[4]` ist `ownership`, nicht `opp_points`). Fehlt der Kopf
/// oder liefert der Graph zu wenige Ausgaben, bleibt die Spalte LEER -- die
/// etablierte "kein Kopf"-Konvention, `split_batch_n_or_empty_rows` haelt
/// dabei die Invariante "genau `n` Zeilen".
#[allow(clippy::type_complexity)]
pub(crate) fn eval_batch_ex_via_ort_cuda(
    net: &Net,
    feats: &[&[f32]],
) -> Result<Vec<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)>, String> {
    let n = feats.len();
    if n == 0 {
        return Err("leerer Batch".to_string());
    }

    let slot = get_or_build_session(net);
    let session_mutex = match &*slot {
        SessionSlot::Unavailable => return Err("Session zuvor als nicht aufbaubar markiert".to_string()),
        SessionSlot::Ready(m) => m,
    };
    let mut session = session_mutex.lock().map_err(|_| "Session-Mutex vergiftet".to_string())?;

    let inputs = build_ort_inputs(net.layout(), feats)?;
    let outputs = session.run(inputs).map_err(|e| e.to_string())?;

    let policy = outputs[0].try_extract_tensor::<f32>().map_err(|e| e.to_string())?.1.to_vec();
    let value = outputs[1].try_extract_tensor::<f32>().map_err(|e| e.to_string())?.1.to_vec();
    let moon = outputs[2].try_extract_tensor::<f32>().map_err(|e| e.to_string())?.1.to_vec();
    let points = outputs[3].try_extract_tensor::<f32>().map_err(|e| e.to_string())?.1.to_vec();
    let aux = |idx: Option<usize>| -> Result<Vec<f32>, String> {
        match idx {
            Some(i) if outputs.len() > i => {
                Ok(outputs[i].try_extract_tensor::<f32>().map_err(|e| e.to_string())?.1.to_vec())
            }
            _ => Ok(Vec::new()),
        }
    };
    let opp_points = aux(net.opp_head_index())?;
    let ownership = aux(net.own_head_index())?;

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
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ort_cuda_enabled_defaults_to_false_when_unset() {
        // Eigene, synthetische Env-Var statt `MOSAIC_ORT_CUDA_ENABLED` direkt
        // zu setzen -- verhindert Kontamination des Prozess-weiten
        // `OnceLock`-Caches fuer parallel laufende `cargo test`-Threads
        // (gleiches Vorsichts-Muster wie `net_batcher.rs`-Tests).
        static CELL: OnceLock<bool> = OnceLock::new();
        assert!(!read_bool_env_once(&CELL, "MOSAIC_ORT_CUDA_ENABLED_TEST_UNSET_XYZ", false));
    }

    #[test]
    fn eval_batch_via_ort_cuda_rejects_empty_batch() {
        // Kein echtes Netz noetig -- der Leer-Batch-Check laeuft VOR jedem
        // Session-Zugriff.
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../models/alphazero_v21_2d_brierbest.onnx");
        let net = Net::load_auto(path.to_str().unwrap()).unwrap_or_else(|e| panic!(
            "{path:?} nicht ladbar ({e}) -- Test-Voraussetzung fehlt, der Test darf nicht              leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ));
        let refs: Vec<&[f32]> = Vec::new();
        assert!(eval_batch_via_ort_cuda(&net, &refs).is_err());
    }

    /// Voller Rundlauf-/Entscheidungsgleichheitstest gegen ein echtes CUDA-
    /// Setup: `#[ignore]`, weil er die ORT-CUDA-Provider-DLLs UND die
    /// Torch-CUDA-12-Laufzeit-DLLs neben dem Testbinary braucht (siehe
    /// `evaluations/PREREG_gpu_inference_path.md` §11) -- kein `cargo test`-
    /// Lauf ohne diese Handkopie erfuellt das. Der eigentliche
    /// Entscheidungsgleichheitsnachweis (Argmax/Gumbel-Top-16 ueber 1148
    /// Zustaende) laeuft separat, siehe Bericht.
    #[test]
    #[ignore]
    fn eval_batch_via_ort_cuda_matches_tract_within_tolerance() {
        use rand::rngs::StdRng;
        use rand::{RngExt, SeedableRng};

        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../models/alphazero_v21_2d_brierbest.onnx");
        let net = Net::load_auto(path.to_str().unwrap()).unwrap_or_else(|e| panic!(
            "{path:?} nicht ladbar ({e}) -- Test-Voraussetzung fehlt, der Test darf nicht              leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ));

        let mut rng = StdRng::seed_from_u64(2026_08_12);
        let mut max_abs = [0f32; 4];
        let names = ["policy", "value", "moon", "points"];
        for batch in [1usize, 2, 5, 16] {
            let feats: Vec<Vec<f32>> = (0..batch)
                .map(|_| (0..net.input_size()).map(|_| rng.random_range(-1.0f32..1.0)).collect())
                .collect();
            let feats_refs: Vec<&[f32]> = feats.iter().map(|v| v.as_slice()).collect();

            let tract_out = net.eval_batch(&feats_refs).expect("tract eval_batch");
            let ort_out = eval_batch_via_ort_cuda(&net, &feats_refs).expect("ORT-CUDA-Rundlauf");
            assert_eq!(ort_out.len(), batch);

            for i in 0..batch {
                let (tp, tv, tm, tpt) = &tract_out[i];
                let (op, ov, om, opt) = &ort_out[i];
                for (idx, (a, b)) in [(tp, op), (tv, ov), (tm, om), (tpt, opt)].iter().enumerate() {
                    for (x, y) in a.iter().zip(b.iter()) {
                        let d = (x - y).abs();
                        if d > max_abs[idx] {
                            max_abs[idx] = d;
                        }
                    }
                }
            }
        }
        for (name, m) in names.iter().zip(max_abs.iter()) {
            println!("PARITAET tract<->ORT-CUDA, Kopf {name}: max. Abweichung {m:.8}");
        }
        for (name, m) in names.iter().zip(max_abs.iter()) {
            assert!(*m < 1e-5, "Kopf {name}: max. Abweichung {m:.8} >= 1e-5 Toleranz");
        }
    }
}
