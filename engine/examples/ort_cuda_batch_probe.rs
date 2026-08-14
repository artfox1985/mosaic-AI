//! Weg-B-Kennlinien-Probe (`evaluations/PREREG_gpu_inference_path.md` §6 Schritt 2,
//! §3 Weg B). Misst Evals/s fuer `ort`-Crate + ONNX-Runtime-CUDA-Provider auf
//! demselben `.onnx`-Modell und denselben Batch-Punkten wie
//! `tools/gpu_batch_throughput.py` (dortige Torch-Messung) -- NUR damit sind
//! beide Kennlinien vergleichbar.
//!
//! WICHTIG (Lehre aus PREREG §9, "Weg A ist gescheitert, weil ich den
//! Byte-Rundlauf statt des GESAMTEN Aufwands je Batch gemessen habe"): dieser
//! Probe misst die VOLLSTAENDIGE Zeit je Batch -- Merkmalspuffer-Bau ->
//! ORT-Eingabetensoren -> `session.run` -> Ausgaben als `Vec<f32>` extrahiert,
//! also GENAU das, was `Net::eval_batch` (`net.rs`) heute mit tract auch tut.
//! `session.run` blockiert bis der CUDA-Stream fertig ist (ONNX Runtime
//! synchronisiert intern vor der Rueckgabe) -- kein separates `synchronize()`
//! wie bei der Torch-Messung noetig, aus demselben Grund aber auch keine
//! Moeglichkeit, das zu unterlaufen.
//!
//! Kein Eingriff in `Net`/den Suchpfad -- reiner Kennlinien-Probe, optionale
//! Abhaengigkeit (`ort_cuda_probe`-Feature, siehe `Cargo.toml`).
//!
//! Wenn der CUDA-Provider nicht registriert werden kann (fehlende
//! CUDA/cuDNN-Laufzeitbibliotheken o.ae.), bricht dieses Programm mit einer
//! Fehlermeldung ab -- es faellt NICHT ersatzweise auf den CPU-Provider
//! zurueck (PREREG §6: "eine ORT-CPU-Kennlinie ist so wertlos wie der
//! Torch-CPU-Lauf bei Weg A war").
//!
//! Aufruf:
//!   cargo run --release --example ort_cuda_batch_probe --features ort_cuda_probe \
//!     -- models/alphazero_v21_2d_brierbest.onnx evaluations/ort_cuda_batch_throughput.json

use std::env;
use std::fs;
use std::time::Instant;

use ort::ep::CUDA;
use ort::session::Session;
use ort::value::Tensor;

/// Planes-Layout (`InputLayout::PlanesPlusFlat`, `net.rs`/`features.rs:18`):
/// 76 Kanaele x 6 x 6 = 2736 Werte, GEPRUEFT gegen `features.rs:911-918`
/// (`state_to_features_2d_direct`) und `export_onnx.py:200-238` (Eingabenamen
/// "planes"/"state").
const C: usize = 76;
const H: usize = 6;
const W: usize = 6;
const FLAT: usize = 708; // features.rs:18 INPUT_SIZE

/// Dieselben Batch-Punkte wie `tools/gpu_batch_throughput.py::BATCHES` --
/// Vergleichbarkeit der beiden Kennlinien ist der ganze Zweck dieser Probe.
const BATCHES: &[usize] = &[1, 2, 4, 8, 11, 16, 22, 32, 44, 64, 128, 256, 512];
/// Dieselbe Messhygiene wie `gpu_batch_throughput.py` (`--reps`/`--warmup`
/// Defaults): Median ueber REPS Wiederholungen nach WARMUP Aufwaermlaeufen.
const REPS: usize = 30;
const WARMUP: usize = 10;

/// Kleiner xorshift64*-PRNG -- kein `rand`-Crate-Feature fuer diese Probe
/// noetig, deterministisch bei festem Seed. Inhalt der Merkmale ist fuer eine
/// Durchsatzmessung irrelevant (wie `torch.randn` im Python-Pendant), nur die
/// Form zaehlt.
struct Xorshift64(u64);
impl Xorshift64 {
    fn next_f32(&mut self) -> f32 {
        let mut x = self.0;
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        self.0 = x;
        // in [-0.5, 0.5), analog torch.randn-Groessenordnung (nicht identisch,
        // aber fuer eine Durchsatzmessung ohne Belang)
        ((x >> 40) as f32 / (1u64 << 24) as f32) - 0.5
    }
}

fn make_batch(batch: usize, rng: &mut Xorshift64) -> (Vec<f32>, Vec<f32>) {
    let mut planes = vec![0f32; batch * C * H * W];
    for v in planes.iter_mut() {
        *v = rng.next_f32();
    }
    let mut flat = vec![0f32; batch * FLAT];
    for v in flat.iter_mut() {
        *v = rng.next_f32();
    }
    (planes, flat)
}

fn median(values: &mut [f64]) -> f64 {
    values.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let n = values.len();
    if n % 2 == 1 {
        values[n / 2]
    } else {
        (values[n / 2 - 1] + values[n / 2]) / 2.0
    }
}

fn main() -> ort::Result<()> {
    let mut args = env::args().skip(1);
    let model_path = args
        .next()
        .unwrap_or_else(|| "models/alphazero_v21_2d_brierbest.onnx".to_string());
    let out_path = args
        .next()
        .unwrap_or_else(|| "evaluations/ort_cuda_batch_throughput.json".to_string());

    println!("Modell: {model_path}");
    // VERSIONS-PIN (Cargo.toml-Kommentar): ort 2.0.0-rc.12 buendelt ONNX
    // Runtime 1.24.2 mit einem Windows-"cu12"-Build -- GEPRUEFT gegen
    // `ort-sys` 2.0.0-rc.12s eingebettete `build/download/dist.txt` (aus dem
    // crates.io-Tarball extrahiert). rc.13 (ONNX Runtime 1.28.0) hat den
    // Windows-cu12-Eintrag gestrichen und passt NICHT zu Torchs CUDA-12-DLLs.
    println!("ort-Version (Crate): 2.0.0-rc.12, ONNX Runtime 1.24.2, Windows-Build \"cu12\" (siehe Cargo.toml-Kommentar)");

    // KEIN Fallback auf CPU: `.error_on_failure()` erzwingt einen harten
    // Fehler, wenn der CUDA-Provider nicht registriert werden kann, statt
    // ihn (ort-Standardverhalten) leise auf CPU zurueckfallen zu lassen.
    // Das ist die Stelle, an der PREREGs "wenn nicht eingerichtet werden
    // kann: sag das" gilt.
    //
    // `with_tf32(false)`: TF32-Verdacht (Nutzer-Auftrag 2026-08-12, PREREG §13)
    // GEPRUEFT UND BESTAETIGT als Hauptursache der 500-fach ueberhoehten
    // Policy-Abweichung -- diese Kennlinie misst deshalb den Zustand, den
    // `net_ort.rs` (Produktions-Hook) jetzt auch fest verdrahtet, NICHT den
    // Zustand des allerersten Laufs (§11, TF32 auf ORTs eigenem, dokumentiert
    // "disabled by default"-Wert belassen -- siehe cuda.rs-Fundstelle im
    // Bericht). Die §11-Zahlen bleiben unangetastet in ihrer eigenen JSON.
    let cuda_ep = CUDA::default().with_device_id(0).with_tf32(false).build().error_on_failure();

    let session_result: ort::Result<Session> = Session::builder().and_then(|b| {
        b.with_execution_providers([cuda_ep])
            .map_err(|e| -> ort::Error { e.into() })
            .and_then(|mut b| b.commit_from_file(&model_path))
    });
    let mut session = match session_result {
        Ok(s) => s,
        Err(e) => {
            eprintln!("CUDA-EXECUTION-PROVIDER NICHT EINGERICHTET -- Abbruch, KEIN CPU-Ersatzlauf.");
            eprintln!("Fehler von ort/ONNX-Runtime: {e}");
            std::process::exit(2);
        }
    };

    println!("CUDA-Execution-Provider registriert, Modell geladen.");
    println!(
        "\n{:>6}  {:>14}  {:>12}  {:>10}",
        "Batch", "Evals/s (voll)", "ms/Batch", "us/Eval"
    );

    let mut rng = Xorshift64(0x2026_0812_ABCDEF01);
    let mut results = serde_json::Map::new();

    for &batch in BATCHES {
        let (planes_buf, flat_buf) = make_batch(batch, &mut rng);

        let mut rates_evals_per_s: Vec<f64> = Vec::with_capacity(REPS);
        let mut ms_per_batch: Vec<f64> = Vec::with_capacity(REPS);

        // Aufwaermlaeufe (cuDNN-Algo-Suche/Autotuning, CUDA-Speicherallokator)
        // -- exakt derselbe Zweck wie `warmup` in gpu_batch_throughput.py.
        for _ in 0..WARMUP {
            let _ = run_once(&mut session, &planes_buf, &flat_buf, batch)?;
        }

        for _ in 0..REPS {
            let t0 = Instant::now();
            let _ = run_once(&mut session, &planes_buf, &flat_buf, batch)?;
            let dt = t0.elapsed().as_secs_f64();
            rates_evals_per_s.push(if dt > 0.0 { batch as f64 / dt } else { f64::INFINITY });
            ms_per_batch.push(dt * 1000.0);
        }

        let rate = median(&mut rates_evals_per_s);
        let ms = median(&mut ms_per_batch);
        println!(
            "{:>6}  {:>14.1}  {:>12.4}  {:>10.4}",
            batch,
            rate,
            ms,
            ms * 1000.0 / batch as f64
        );
        results.insert(batch.to_string(), serde_json::json!(rate));
    }

    let out = serde_json::json!({
        "backend": "ort-cuda",
        "ort_version": "2.0.0-rc.12",
        "onnxruntime_version": "1.24.2",
        "onnxruntime_windows_build_tag": "cu12",
        "model": model_path,
        "reps": REPS,
        "warmup": WARMUP,
        "batches": BATCHES,
        "evals_per_s_full_roundtrip": results,
        "note_de": "Volle Zeit je Batch: Merkmalspuffer -> ORT-Eingabetensoren -> session.run -> Vec<f32>-Extraktion. session.run blockiert synchron (kein separates CUDA-synchronize noetig).",
    });
    fs::write(&out_path, serde_json::to_string_pretty(&out).unwrap())
        .expect("Ergebnis-JSON schreiben");
    println!("\nErgebnis: {out_path}");

    Ok(())
}

/// EIN Batch-Durchlauf, VOLLSTAENDIG: Tensor-Bau aus dem Merkmalspuffer ->
/// `session.run` -> Ausgaben als `Vec<f32>` extrahiert -- exakt das, was
/// `Net::eval_batch` (`net.rs:386-`) mit tract auch tut, nur mit
/// ort/ONNX-Runtime-CUDA statt tract/CPU. KEIN Aufruf misst nur die
/// Kernel-Zeit (PREREG §9: das war der Fehler bei Weg A).
fn run_once(
    session: &mut Session,
    planes_buf: &[f32],
    flat_buf: &[f32],
    batch: usize,
) -> ort::Result<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)> {
    let planes_t = Tensor::<f32>::from_array(([batch, C, H, W], planes_buf.to_vec().into_boxed_slice()))?;
    let flat_t = Tensor::<f32>::from_array(([batch, FLAT], flat_buf.to_vec().into_boxed_slice()))?;

    // Eingabenamen "planes"/"state" -- GEPRUEFT gegen `export_onnx.py:236-238`
    // (`input_names=["planes", "state"]`), Reihenfolge wie `net.rs::build_inputs`
    // (Planes zuerst, Flat zweitens).
    let inputs: Vec<(&str, ort::session::SessionInputValue)> =
        vec![("planes", planes_t.into()), ("state", flat_t.into())];
    let outputs = session.run(inputs)?;

    let policy = outputs["policy"].try_extract_tensor::<f32>()?.1.to_vec();
    let value = outputs["value"].try_extract_tensor::<f32>()?.1.to_vec();
    let moon = outputs["moon"].try_extract_tensor::<f32>()?.1.to_vec();
    let points = outputs["points"].try_extract_tensor::<f32>()?.1.to_vec();

    Ok((policy, value, moon, points))
}
