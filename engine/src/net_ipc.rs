//! Weg A (`evaluations/PREREG_gpu_inferenzpfad.md` Abschnitt 3): optionaler
//! Shared-Memory-IPC-Kanal von der Rust-Engine zu einem Python-Prozess mit
//! torch/CUDA, als Ersatz-Backend für `net.rs::Net::eval_batch` (NUR diese
//! Funktion -- `eval`/`eval_pair`/`eval_ex`/`eval_pair_ex` bleiben unberührt,
//! siehe dortiger Verdrahtungs-Kommentar).
//!
//! GEDECKT durch `evaluations/gpu_inferenzpfad_ipc_roundtrip.json`
//! (Batch 256, Kanal "shm": 0,2867 ms Median-Rundlauf gegen eine Schwelle von
//! 1,0816 ms -- Faktor 3,77 unter der Schwelle). Diese Messung nutzte
//! `multiprocessing.shared_memory` + `Pipe`-Doorbell zwischen ZWEI
//! Python-Prozessen; der hier gebaute Kanal ist Rust<->Python und kann diese
//! Messung deshalb nicht direkt wiederverwenden, reproduziert aber dieselbe
//! Grundidee (Nutzlast in einer gemeinsamen Speicherabbildung, Signalisierung
//! separat) und bleibt bei der GLEICHEN Batchgroesse (<=16 statt 256, siehe
//! `MAX_BATCH`-Kommentar) klar auf der guenstigen Seite (kleinere Nutzlast,
//! selbe Groessenordnung an Fixkosten).
//!
//! ## Architektur (eigene Entscheidung, nicht vom Auftrag vorgegeben)
//!
//! - **Nutzlast**: eine speicherabgebildete Datei je Richtung
//!   (`request.bin`/`response.bin`, fest dimensioniert), von BEIDEN Seiten
//!   mit `mmap` geoeffnet -- kein `multiprocessing.shared_memory`
//!   (Python-internes Protokoll, dessen Windows-Namensschema hier nicht
//!   nachgebaut wird) und keine Serialisierung der grossen Nutzlast über den
//!   Kontrollkanal (das war genau der teure Zweig der Messung, "socket"
//!   NICHT gedeckt).
//! - **Signalisierung**: ein TCP-Loopback-Socket (Rust = Client, Python =
//!   Server) fuer feste, kleine Kontrollnachrichten (Header). Die Messung hat
//!   den "leer"-Fall (reine Signalisierung ohne Nutzlast-Kopie) fuer BEIDE
//!   Kanaele separat ausgewiesen: Socket 0,0378 ms Median -- weit unter jeder
//!   hier relevanten Schwelle. Ein TCP-Socket statt einer plattformspezifischen
//!   Named-Pipe/`multiprocessing.Pipe`-Nachbildung ist also für die reine
//!   Kontrollnachricht unkritisch und in Rust (`std::net`) ohne weitere
//!   Abhaengigkeit verfuegbar.
//!
//! ## Knopf (Default AUS = Bestandsverhalten)
//!
//! `MOSAIC_TORCH_IPC_ENABLED=1` schaltet den Kanal ein (siehe
//! [`ipc_enabled`]). Bei AUS (Default, kein Wheel-Verhaltensunterschied)
//! ruft `Net::eval_batch` unveraendert nur tract auf -- dieses Modul wird in
//! diesem Fall nicht einmal betreten (der Aufrufer prueft den Knopf VOR dem
//! ersten Zugriff hierher, siehe `net.rs::eval_batch`).
//!
//! ## Fallback
//!
//! Jeder Fehler beim Verbindungsaufbau ODER beim Rundlauf selbst
//! (Zeitüberschreitung, Verbindungsabbruch, unerwartete Antwortgroesse,
//! Fehlerstatus vom Python-Server) fuehrt zu `Err(..)` aus
//! [`eval_batch_via_ipc`] -- NIE zu einem Panic. Der Aufrufer
//! (`net.rs::eval_batch`) faengt das ab, loggt einmalig
//! ([`warn_ipc_fallback_once`]) und rechnet mit tract weiter. Ein
//! einmal als nicht erreichbar erkannter Kanal wird fuer den Rest des
//! Prozesses NICHT erneut versucht (siehe [`channel`]-Dokumentation) --
//! bewusste Vereinfachung, siehe Bericht Punkt 6.

use std::io::{Read, Write};
use std::net::TcpStream;
use std::path::PathBuf;
use std::sync::{Mutex, OnceLock};
use std::time::Duration;

use memmap2::MmapMut;

// ── Feste Kopf-Breiten, gleiche Quelle wie
// `evaluations/gpu_inferenzpfad_ipc_roundtrip.json::feature_size.response`
// (net.rs:286-289 `eval()`: out[0..3] = policy,value,moon,points -- exakt
// die 4, die `eval_batch` liest). ABSICHTLICH lokal dupliziert statt aus
// `net_mcts::NUM_ACTIONS` importiert -- gleiches Schichtungs-Argument wie
// `net::EVAL_BATCH_MAX_N` (net_mcts.rs haengt von net.rs/net_ipc.rs ab,
// nicht umgekehrt). Aendert sich die Architektur (anderes NUM_ACTIONS, ein
// zusaetzlicher Pflicht-Kopf), muss dieser Kanal explizit nachgezogen werden
// -- kein impliziter, stiller Fallback auf eine falsche Breite.
const POLICY_WIDTH: usize = 406;
const VALUE_WIDTH: usize = 1;
const MOON_WIDTH: usize = 5;
const POINTS_WIDTH: usize = 1;
const RESP_WIDTH: usize = POLICY_WIDTH + VALUE_WIDTH + MOON_WIDTH + POINTS_WIDTH; // 413

/// Obergrenze der Batchgroesse fuer diesen Kanal. EIGENE ENTSCHEIDUNG: an
/// `net::EVAL_BATCH_MAX_N` (16) ausgerichtet, NICHT an der in der Messung
/// verwendeten 256 -- dieser Kanal ist das Ersatz-Backend fuer
/// `Net::eval_batch`, das schon heute bei 16 deckelt (Gumbel-Wurzel-
/// Kandidatenzahl, siehe dortiger Kommentar). Eine Verschraenkungs-Mechanik,
/// die grössere Batches erzeugen wuerde, ist §5 der Vorregistrierung zufolge
/// NICHT Teil dieses Auftrags. Kleinere Batches als die gemessenen 256 machen
/// die Messung nicht ungueltig (die Kopierkosten skalieren mit der
/// Nutzlastgroesse nach unten, die Fixkosten -- Doorbell/Header -- bleiben
/// gleich) -- das ist eine HERLEITUNG, keine eigene Messung fuer N<=16.
const MAX_BATCH: usize = 16;

/// Obergrenze der Merkmalslaenge je Position (Elemente, nicht Bytes). Aus dem
/// CODE: `features.rs:911-916` (`state_to_features_2d_direct`) = Planes
/// (76*6*6=2736) + Flat (708) = 3444 -- der heutige groesste Layout-Fall
/// (`InputLayout::PlanesPlusFlat`). Der flache Alt-Pfad (708) und der reine
/// Planes-Pfad (2736) passen beide darunter. Wie bei `RESP_WIDTH`: eine
/// zukuenftige Architektur mit groesserer Eingabe muss diese Konstante
/// bewusst anheben, kein stiller Puffer-Ueberlauf.
const MAX_INPUT_LEN: usize = 3444;

const REQUEST_BUF_BYTES: usize = MAX_BATCH * MAX_INPUT_LEN * 4;
const RESPONSE_BUF_BYTES: usize = MAX_BATCH * RESP_WIDTH * 4;

/// Verbindungsversuch-Zeitlimit. Kein Env-Knopf (schmaler Auftrags-Zuschnitt)
/// -- ein nicht erreichbarer Python-Prozess soll schnell als solcher erkannt
/// werden, nicht eine ganze Suche verzoegern.
const CONNECT_TIMEOUT: Duration = Duration::from_millis(200);

/// Liest eine `MOSAIC_*`-Bool-Env-Var einmalig -- gleiches Muster wie
/// `net_mcts::root_child_q_logging_enabled_env`/`tiling_solver::cache_enabled_env`
/// (lokal dupliziert, `net_ipc.rs` darf nicht von `net_mcts.rs` abhaengen).
fn read_bool_env_once(cell: &'static OnceLock<bool>, name: &str, default: bool) -> bool {
    *cell.get_or_init(|| match std::env::var(name) {
        Ok(v) => v != "0" && !v.trim().is_empty(),
        Err(_) => default,
    })
}

static IPC_ENABLED: OnceLock<bool> = OnceLock::new();

/// `MOSAIC_TORCH_IPC_ENABLED=1` (oder jeder nicht-"0"/nicht-leere Wert)
/// schaltet den Weg-A-Kanal ein. Default AUS -- siehe Modul-Kommentar.
pub(crate) fn ipc_enabled() -> bool {
    read_bool_env_once(&IPC_ENABLED, "MOSAIC_TORCH_IPC_ENABLED", false)
}

static IPC_PORT: OnceLock<u16> = OnceLock::new();

/// TCP-Loopback-Port fuer die Kontrollnachrichten. `MOSAIC_TORCH_IPC_PORT`,
/// Default 8848 (willkuerlich, aber fest -- muss mit dem `--port`-Argument
/// von `tools/torch_ipc_server.py` uebereinstimmen).
fn ipc_port() -> u16 {
    *IPC_PORT.get_or_init(|| {
        std::env::var("MOSAIC_TORCH_IPC_PORT")
            .ok()
            .and_then(|s| s.trim().parse::<u16>().ok())
            .unwrap_or(8848)
    })
}

static IPC_SHM_DIR: OnceLock<PathBuf> = OnceLock::new();

/// Verzeichnis der beiden speicherabgebildeten Dateien. `MOSAIC_TORCH_IPC_SHM_DIR`,
/// Default `%TEMP%/mosaic_torch_ipc` -- muss mit `--shm-dir` von
/// `tools/torch_ipc_server.py` uebereinstimmen.
fn ipc_shm_dir() -> &'static PathBuf {
    IPC_SHM_DIR.get_or_init(|| {
        std::env::var("MOSAIC_TORCH_IPC_SHM_DIR")
            .map(PathBuf::from)
            .unwrap_or_else(|_| std::env::temp_dir().join("mosaic_torch_ipc"))
    })
}

/// Einmalige Warnung, wenn der IPC-Kanal eingeschaltet, aber nicht (mehr)
/// nutzbar ist -- gleiches "einmal loggen"-Muster wie
/// `net_mcts::warn_missing_opp_head_once`.
static WARNED_IPC_FALLBACK: OnceLock<()> = OnceLock::new();

pub(crate) fn warn_ipc_fallback_once(reason: &str) {
    WARNED_IPC_FALLBACK.get_or_init(|| {
        eprintln!(
            "⚠️  MOSAIC_TORCH_IPC_ENABLED=1 gesetzt, aber der Torch-IPC-Kanal ist nicht \
             nutzbar ({reason}) -- falle auf tract zurueck (siehe PREREG_gpu_inferenzpfad.md). \
             Diese Meldung erscheint nur einmal je Prozess."
        );
    });
}

/// Persistenter Kanal-Zustand: einmal aufgebaut, ueber alle Aufrufe dieses
/// Prozesses wiederverwendet (keine Re-Verbindung je Batch). `Unavailable`
/// ist ENDGUELTIG fuer die Prozesslaufzeit (siehe Modul-Kommentar Punkt
/// "Fallback") -- eine bewusste Vereinfachung: kein periodischer Retry, kein
/// Health-Check-Thread. Wird der Python-Server NACH dem ersten
/// fehlgeschlagenen Verbindungsversuch gestartet, sieht dieser Rust-Prozess
/// ihn erst nach einem Neustart.
enum ChannelState {
    Connected { stream: TcpStream, request: MmapMut, response: MmapMut },
    Unavailable,
}

static CHANNEL: OnceLock<Mutex<Option<ChannelState>>> = OnceLock::new();

fn open_or_create_mmap(path: &std::path::Path, size: usize) -> std::io::Result<MmapMut> {
    let file = std::fs::OpenOptions::new().read(true).write(true).create(true).open(path)?;
    file.set_len(size as u64)?;
    // Sicherheit: `set_len` verkuerzt eine evtl. laenger vorgefundene Datei
    // NICHT automatisch auf `size` zurueck bei manchen Dateisystemen -- doch
    // `set_len` in std setzt exakt die angegebene Laenge (kuerzt oder
    // verlaengert), also ist die Datei danach IMMER exakt `size` Bytes.
    unsafe { MmapMut::map_mut(&file) }
}

fn connect() -> Result<ChannelState, String> {
    let dir = ipc_shm_dir();
    std::fs::create_dir_all(dir).map_err(|e| format!("SHM-Verzeichnis {dir:?} nicht anlegbar: {e}"))?;
    let request = open_or_create_mmap(&dir.join("request.bin"), REQUEST_BUF_BYTES)
        .map_err(|e| format!("request.bin nicht abbildbar: {e}"))?;
    let response = open_or_create_mmap(&dir.join("response.bin"), RESPONSE_BUF_BYTES)
        .map_err(|e| format!("response.bin nicht abbildbar: {e}"))?;
    let addr = format!("127.0.0.1:{}", ipc_port());
    let sock_addr = addr
        .parse()
        .map_err(|e| format!("Adresse {addr:?} ungueltig: {e}"))?;
    let stream = TcpStream::connect_timeout(&sock_addr, CONNECT_TIMEOUT)
        .map_err(|e| format!("Verbindung zu {addr} fehlgeschlagen: {e}"))?;
    stream.set_nodelay(true).ok();
    stream
        .set_read_timeout(Some(Duration::from_secs(30)))
        .map_err(|e| format!("Lese-Timeout nicht setzbar: {e}"))?;
    Ok(ChannelState::Connected { stream, request, response })
}

/// f32-Slice LE-byteweise in einen Byte-Puffer schreiben -- explizit statt
/// eines rohen Speicher-Reinterpretierens, damit die Byte-Reihenfolge
/// dokumentiert (und nicht bloss "wie auch immer die Zielplattform es tut")
/// ist. `dst.len()` muss `>= 4*src.len()` sein (Aufrufer-Vertrag, hier per
/// `debug_assert!` abgesichert, kein Produktions-Overhead in Release).
fn write_f32_le(dst: &mut [u8], src: &[f32]) {
    debug_assert!(dst.len() >= src.len() * 4);
    for (chunk, v) in dst.chunks_exact_mut(4).zip(src.iter()) {
        chunk.copy_from_slice(&v.to_le_bytes());
    }
}

/// Gegenstueck zu [`write_f32_le`]: liest `n` f32-Werte LE aus `src`.
fn read_f32_le(src: &[u8], n: usize) -> Vec<f32> {
    debug_assert!(src.len() >= n * 4);
    src.chunks_exact(4).take(n).map(|c| f32::from_le_bytes([c[0], c[1], c[2], c[3]])).collect()
}

fn write_u32_le(dst: &mut Vec<u8>, v: u32) {
    dst.extend_from_slice(&v.to_le_bytes());
}

fn read_u32_le(src: &[u8]) -> u32 {
    u32::from_le_bytes([src[0], src[1], src[2], src[3]])
}

/// Forward-Pass fuer `feats.len()` Positionen ueber den Torch/CUDA-IPC-Kanal
/// (Weg A) -- Ersatz-Backend fuer `net.rs::Net::eval_batch`, GLEICHER
/// Rueckgabe-Vertrag ((policy, value, moon, points) je Zeile, gleiche
/// Reihenfolge wie die Eingabe). Erfordert `1 <= feats.len() <= MAX_BATCH`
/// und dass alle Zeilen dieselbe Laenge haben (`<= MAX_INPUT_LEN`) -- sonst
/// `Err` (kein Panic, kein stiller Fallback auf eine falsche Groesse).
///
/// NIE ein Panic: jeder Fehlerfall (Verbindungsaufbau, I/O, Protokoll,
/// Server-Fehlerstatus) wird als `Err(String)` an den Aufrufer
/// zurueckgegeben, der (in `net.rs::eval_batch`) auf tract zurueckfaellt.
pub(crate) fn eval_batch_via_ipc(
    feats: &[&[f32]],
) -> Result<Vec<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)>, String> {
    let n = feats.len();
    if n == 0 || n > MAX_BATCH {
        return Err(format!("Batchgroesse {n} ausserhalb 1..={MAX_BATCH}"));
    }
    let input_len = feats[0].len();
    if input_len == 0 || input_len > MAX_INPUT_LEN {
        return Err(format!("Merkmalslaenge {input_len} ausserhalb 1..={MAX_INPUT_LEN}"));
    }
    if feats.iter().any(|f| f.len() != input_len) {
        return Err("uneinheitliche Merkmalslaenge im Batch".to_string());
    }

    let cell = CHANNEL.get_or_init(|| Mutex::new(None));
    let mut guard = cell.lock().map_err(|_| "Kanal-Mutex vergiftet".to_string())?;

    if guard.is_none() {
        match connect() {
            Ok(state) => *guard = Some(state),
            Err(e) => {
                *guard = Some(ChannelState::Unavailable);
                return Err(e);
            }
        }
    }

    let (stream, request, response) = match guard.as_mut() {
        Some(ChannelState::Connected { stream, request, response }) => (stream, request, response),
        Some(ChannelState::Unavailable) => return Err("Kanal zuvor als nicht erreichbar markiert".to_string()),
        None => unreachable!("guard wurde oben befuellt"),
    };

    let result = run_roundtrip(stream, request, response, feats, n, input_len);
    if result.is_err() {
        // Rundlauf-Fehler NACH erfolgreichem Connect (z.B. Server waehrend
        // der Laufzeit abgestuerzt) -- Kanal ebenfalls endgueltig als nicht
        // erreichbar markieren (siehe Modul-Kommentar), statt bei jedem
        // weiteren Aufruf erneut die (jetzt tote) Verbindung zu versuchen.
        *guard = Some(ChannelState::Unavailable);
    }
    result
}

fn run_roundtrip(
    stream: &mut TcpStream,
    request: &mut MmapMut,
    response: &mut MmapMut,
    feats: &[&[f32]],
    n: usize,
    input_len: usize,
) -> Result<Vec<(Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>)>, String> {
    // 1) Nutzlast in den Request-Puffer schreiben (Zeile i an Offset i*input_len).
    for (i, row) in feats.iter().enumerate() {
        let off = i * input_len * 4;
        write_f32_le(&mut request[off..off + input_len * 4], row);
    }

    // 2) Kontrollnachricht: batch_n (u32 LE) + input_len (u32 LE) = 8 Bytes.
    let mut header = Vec::with_capacity(8);
    write_u32_le(&mut header, n as u32);
    write_u32_le(&mut header, input_len as u32);
    stream.write_all(&header).map_err(|e| format!("Header-Versand fehlgeschlagen: {e}"))?;

    // 3) Antwort-Header lesen: status(u32) + batch_n_echo(u32) + err_len(u32) = 12 Bytes.
    let mut resp_header = [0u8; 12];
    stream.read_exact(&mut resp_header).map_err(|e| format!("Antwort-Header nicht lesbar: {e}"))?;
    let status = read_u32_le(&resp_header[0..4]);
    let batch_echo = read_u32_le(&resp_header[4..8]);
    let err_len = read_u32_le(&resp_header[8..12]) as usize;

    if status != 0 {
        let mut msg_buf = vec![0u8; err_len];
        stream.read_exact(&mut msg_buf).map_err(|e| format!("Fehlermeldung nicht lesbar: {e}"))?;
        let msg = String::from_utf8_lossy(&msg_buf);
        return Err(format!("Server meldet Status {status}: {msg}"));
    }
    if batch_echo as usize != n {
        return Err(format!("Server-Antwort fuer Batch {batch_echo}, erwartet {n}"));
    }

    // 4) Ergebnisse aus dem Response-Puffer lesen (Zeile i an Offset i*RESP_WIDTH).
    let mut out = Vec::with_capacity(n);
    for i in 0..n {
        let off = i * RESP_WIDTH * 4;
        let row = &response[off..off + RESP_WIDTH * 4];
        let mut cursor = 0usize;
        let policy = read_f32_le(&row[cursor..], POLICY_WIDTH);
        cursor += POLICY_WIDTH * 4;
        let value = read_f32_le(&row[cursor..], VALUE_WIDTH);
        cursor += VALUE_WIDTH * 4;
        let moon = read_f32_le(&row[cursor..], MOON_WIDTH);
        cursor += MOON_WIDTH * 4;
        let points = read_f32_le(&row[cursor..], POINTS_WIDTH);
        out.push((policy, value, moon, points));
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    // ── Reine Wire-Format-Tests, keine Netzwerk-/Dateisystem-Abhaengigkeit ──

    #[test]
    fn write_then_read_f32_le_roundtrips() {
        let src = [1.0f32, -2.5, 0.0, f32::MIN_POSITIVE, -1.0, 3.14159];
        let mut buf = vec![0u8; src.len() * 4];
        write_f32_le(&mut buf, &src);
        let got = read_f32_le(&buf, src.len());
        assert_eq!(got, src);
    }

    #[test]
    fn u32_le_header_roundtrips() {
        let mut buf = Vec::new();
        write_u32_le(&mut buf, 256);
        write_u32_le(&mut buf, 3444);
        assert_eq!(read_u32_le(&buf[0..4]), 256);
        assert_eq!(read_u32_le(&buf[4..8]), 3444);
    }

    #[test]
    fn resp_width_matches_measured_payload_contract() {
        // Fixpunkt gegen `evaluations/gpu_inferenzpfad_ipc_roundtrip.json`
        // ("response.elements_per_position": 413) -- ein Abweichen hier waere
        // ein Vertragsbruch mit der gemessenen/gedeckten Kennzahl.
        assert_eq!(RESP_WIDTH, 413);
        assert_eq!(POLICY_WIDTH + VALUE_WIDTH + MOON_WIDTH + POINTS_WIDTH, 413);
    }

    #[test]
    fn max_input_len_matches_2d_layout_contract() {
        // Fixpunkt gegen dieselbe Messdatei ("request.elements_per_position": 3444)
        // und `features.rs::state_to_features_2d_direct` (Planes 2736 + Flat 708).
        assert_eq!(MAX_INPUT_LEN, 2736 + 708);
    }

    #[test]
    fn ipc_enabled_defaults_to_false_when_unset() {
        // Eigene, synthetische Env-Var statt `MOSAIC_TORCH_IPC_ENABLED` direkt zu
        // setzen -- verhindert, dass dieser Test den Prozess-weiten
        // `OnceLock`-Cache fuer ALLE parallel laufenden `cargo test`-Threads
        // festlegt (gleiches Vorsichts-Muster wie `net_mcts::read_f64_env`-Tests).
        static CELL: OnceLock<bool> = OnceLock::new();
        assert!(!read_bool_env_once(&CELL, "MOSAIC_TORCH_IPC_ENABLED_TEST_UNSET_XYZ", false));
    }

    #[test]
    fn read_bool_env_once_true_for_one_and_empty_string_stays_default() {
        static CELL_TRUE: OnceLock<bool> = OnceLock::new();
        std::env::set_var("MOSAIC_TORCH_IPC_TEST_TRUE_XYZ", "1");
        assert!(read_bool_env_once(&CELL_TRUE, "MOSAIC_TORCH_IPC_TEST_TRUE_XYZ", false));

        static CELL_EMPTY: OnceLock<bool> = OnceLock::new();
        std::env::set_var("MOSAIC_TORCH_IPC_TEST_EMPTY_XYZ", "");
        assert!(!read_bool_env_once(&CELL_EMPTY, "MOSAIC_TORCH_IPC_TEST_EMPTY_XYZ", false));
    }

    #[test]
    fn eval_batch_via_ipc_rejects_batch_size_beyond_max() {
        let feats: Vec<f32> = vec![0.0; 10];
        let refs: Vec<&[f32]> = (0..MAX_BATCH + 1).map(|_| feats.as_slice()).collect();
        assert!(eval_batch_via_ipc(&refs).is_err());
    }

    #[test]
    fn eval_batch_via_ipc_rejects_empty_batch() {
        let refs: Vec<&[f32]> = Vec::new();
        assert!(eval_batch_via_ipc(&refs).is_err());
    }

    #[test]
    fn eval_batch_via_ipc_rejects_uneven_row_lengths() {
        let a = vec![0.0f32; 10];
        let b = vec![0.0f32; 11];
        let refs: Vec<&[f32]> = vec![a.as_slice(), b.as_slice()];
        assert!(eval_batch_via_ipc(&refs).is_err());
    }

    // ── Voller Rundlauf-/Toleranz-Test gegen einen echten Python/torch-Server ──
    // `#[ignore]`: braucht `python`+torch (CUDA optional) auf PATH, ein lokal
    // vorhandenes Checkpoint-Paar (ONNX fuer tract, .pth fuer torch) UND einen
    // freien TCP-Port -- alles Bedingungen, die ein frischer `cargo test`-Lauf
    // (z.B. CI ohne Modelle) nicht garantiert erfuellt, siehe
    // `net.rs::load_test_net`-Skip-Konvention fuer denselben Anlass.
    // Aufruf: `cargo test --lib -- --ignored net_ipc::tests::eval_batch_via_ipc_matches_tract_within_tolerance`
    #[test]
    #[ignore]
    fn eval_batch_via_ipc_matches_tract_within_tolerance() {
        use crate::net::Net;
        use rand::rngs::StdRng;
        use rand::{RngExt, SeedableRng};
        use std::process::{Child, Command};

        struct ChildGuard(Child);
        impl Drop for ChildGuard {
            fn drop(&mut self) {
                let _ = self.0.kill();
                let _ = self.0.wait();
            }
        }

        let repo = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("..");
        let onnx_path = repo.join("models/alphazero_v20_2d_opp_brierbest.onnx");
        let pth_path = repo.join("models/alphazero_v20_2d_opp_brierbest.pth");
        if !onnx_path.exists() || !pth_path.exists() {
            eprintln!("  ⚠️  {onnx_path:?} oder {pth_path:?} fehlt -- Test uebersprungen.");
            return;
        }

        // Eigenen Port/SHM-Ordner fuer diesen Testlauf (kollidiert nicht mit
        // einem evtl. schon laufenden Dauer-Server unter dem Default-Port).
        let port: u16 = 18848;
        let shm_dir = std::env::temp_dir().join("mosaic_torch_ipc_test");
        std::env::set_var("MOSAIC_TORCH_IPC_PORT", port.to_string());
        std::env::set_var("MOSAIC_TORCH_IPC_SHM_DIR", shm_dir.to_str().unwrap());

        let server_script = repo.join("tools/torch_ipc_server.py");
        let mut child = match Command::new("python")
            .arg(&server_script)
            .arg("--model")
            .arg(&pth_path)
            .arg("--port")
            .arg(port.to_string())
            .arg("--shm-dir")
            .arg(&shm_dir)
            .arg("--device")
            .arg("cpu") // CPU: deterministischer, kein Zweitprozess-CUDA-Init-Wettlauf
            .spawn()
        {
            Ok(c) => ChildGuard(c),
            Err(e) => {
                eprintln!("  ⚠️  Python-Server nicht startbar ({e}) -- Test uebersprungen.");
                return;
            }
        };

        // Auf den Server warten (Modell-/CUDA-Ladezeit): Verbindungsversuche
        // bis zu 60s, kurze Pause zwischen den Versuchen.
        let addr: std::net::SocketAddr = format!("127.0.0.1:{port}").parse().unwrap();
        let mut ready = false;
        for _ in 0..300 {
            if std::net::TcpStream::connect_timeout(&addr, Duration::from_millis(200)).is_ok() {
                ready = true;
                break;
            }
            std::thread::sleep(Duration::from_millis(200));
        }
        if !ready {
            eprintln!("  ⚠️  Python-Server nach 60s nicht erreichbar -- Test uebersprungen.");
            let _ = child.0.kill();
            return;
        }

        let net = match Net::load_auto(onnx_path.to_str().unwrap()) {
            Ok(n) => n,
            Err(e) => {
                eprintln!("  ⚠️  ONNX-Modell nicht ladbar ({e}) -- Test uebersprungen.");
                return;
            }
        };

        let mut rng = StdRng::seed_from_u64(2026_08_12);
        let mut max_abs = [0f32; 4]; // policy, value, moon, points
        let names = ["policy", "value", "moon", "points"];
        for batch in [1usize, 2, 5, 16] {
            let feats: Vec<Vec<f32>> = (0..batch)
                .map(|_| (0..net.input_size()).map(|_| rng.random_range(-1.0f32..1.0)).collect())
                .collect();
            let feats_refs: Vec<&[f32]> = feats.iter().map(|v| v.as_slice()).collect();

            let tract_out = net.eval_batch(&feats_refs).expect("tract eval_batch");
            let ipc_out = eval_batch_via_ipc(&feats_refs).expect("IPC-Rundlauf (Server muss laufen)");
            assert_eq!(ipc_out.len(), batch);

            for i in 0..batch {
                let (tp, tv, tm, tpt) = &tract_out[i];
                let (ip, iv, im, ipt) = &ipc_out[i];
                for (a, b) in [(tp, ip), (tv, iv), (tm, im), (tpt, ipt)] {
                    assert_eq!(a.len(), b.len(), "Batch {batch} Zeile {i}: Laengen weichen ab");
                }
                for (idx, (a, b)) in [(tp, ip), (tv, iv), (tm, im), (tpt, ipt)].iter().enumerate() {
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
            println!("PARITAET tract<->torch-IPC, Kopf {name}: max. Abweichung {m:.8}");
        }
        // Toleranz 1e-5 -- Praezedenzfall `net.rs::eval_pair_matches_two_single_evals`/
        // `eval_batch_matches_n_single_evals` (siehe dortiger Kommentar zur
        // Nicht-Bitgleichheit verschiedener tract-Batch-Plaene). HIER zusaetzlich
        // Cross-FRAMEWORK (tract vs. PyTorch/CPU) -- eine strengere Aussage als der
        // Praezedenzfall (der ist tract-vs-tract). Bewusst NICHT vorab verschaerft
        // oder aufgeweicht: das Ergebnis steht im Testbericht, nicht in dieser
        // Assertion-Zahl allein.
        for (name, m) in names.iter().zip(max_abs.iter()) {
            assert!(*m < 1e-5, "Kopf {name}: max. Abweichung {m:.8} >= 1e-5 Toleranz");
        }
    }
}
