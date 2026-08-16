//! Verschraenkung (Weg V, Nutzer-Auftrag 2026-08-12, "dann leg los"):
//! gemeinsame Warteschlange + EIN Sammel-Faden je geladenem Netz, buendelt
//! die Blattanfragen MEHRERER gleichzeitig laufender Suchen (Selfplay-/Arena-
//! Partie-Faeden) zu EINEM [`crate::net::Net::eval_batch`]-Aufruf, statt dass
//! jeder Faden seinen eigenen `eval`/`eval_pair_ex`-Aufruf synchron abwartet.
//!
//! ## Warum kein Zustandsautomat noetig ist
//!
//! Eine einzelne Suche hat zu jedem Zeitpunkt HOECHSTENS EIN offenes Blatt
//! (`net_mcts.rs::drafting_action_priors`/`net_leaf_eval`/`make_node` rufen
//! `Net::eval*` synchron und warten auf das Ergebnis, bevor sie weitermachen)
//! -- ein Partie-Faden, der auf seine Antwort wartet, blockiert also einfach
//! auf einem Kanal, GENAU WIE ER HEUTE SCHON auf den tract-Aufruf selbst
//! "blockiert" (der laeuft synchron im selben Aufrufstack). Diese Datei
//! aendert NICHTS an der Suchlogik selbst, nur DARAN, wer den eigentlichen
//! `eval_batch`-Aufruf tatsaechlich ausfuehrt und mit wessen Zeilen er ihn
//! fuellt.
//!
//! ## Architektur
//!
//! - **Warteschlange**: `std::sync::mpsc`, ein [`Request`] je Merkmalszeile
//!   (NICHT je logischem Aufruf -- `eval_pair_ex`-Aufrufer mit Mover+Gegner-
//!   Perspektive senden ZWEI [`Request`]s, siehe [`Batcher::eval_rows`], die
//!   der Sammel-Faden mit denen ANDERER Aufrufer zusammen buendeln kann).
//! - **Sammel-Faden**: EIN dedizierter `std::thread`, haelt `Arc<Net>` fuer
//!   seine gesamte Lebensdauer (muss `'static` sein, siehe
//!   [`spawn_batcher`]), zieht bis zu `batch_max` Zeilen, ruft
//!   **`Net::eval_batch`** -- damit laeuft der optionale ORT-CUDA-Kanal
//!   (`net_ort.rs`, Backend-Rangfolge in `net.rs::eval_batch`) automatisch
//!   mit, wenn er zusaetzlich eingeschaltet ist. Verteilt die Ergebnisse
//!   zeilenweise an die jeweiligen Antwort-Kanaele zurueck.
//! - **Deadlock-Waechter**: die Fuell-Schleife wartet auf JEDES weitere
//!   Element nur bis [`fill_timeout`] (Default 200µs, siehe dortige
//!   Begruendung) -- kommt in dieser Zeit nichts mehr, wird der bisher
//!   gefuellte (moeglicherweise kleinere) Batch sofort abgeschickt statt auf
//!   `batch_max` zu warten. Exakt dieselbe Technik wie im validierten
//!   Probelauf `engine/examples/interleave_concurrency_probe.rs`
//!   (`SLOT_TIMEOUT`), hier nur mit einer echten `Net::eval_batch`-Zeile statt
//!   `thread::sleep` als Fuellung.
//! - **Registrierung nach Zeigeridentitaet**: `net_mcts.rs`s tiefe
//!   Aufrufstellen (`net_leaf_eval`/`make_node`) bekommen nur `&Net`, keinen
//!   `Arc<Net>` (Signaturaenderung an diesen Stellen war NICHT Teil des
//!   Auftrags -- "kein Umbau der Suche"). Deshalb: `self_play.rs` registriert
//!   den Sammel-Faden EINMAL pro Lauf ueber [`ensure_batcher_for`] (hat dort
//!   den `Arc<Net>`), tiefe Aufrufstellen finden ihn ueber [`lookup`] anhand
//!   der Zeiger-Adresse von `&Net` -- sicher, weil dieselbe `Arc<Net>`-Instanz
//!   fuer die gesamte Laufzeit des Selfplay-/Arena-Laufs lebt (per `Arc::clone`
//!   an jeden Rayon-Task durchgereicht) und `&*arc as *const Net` immer
//!   dieselbe Adresse wie `Arc::as_ptr(&arc)` liefert.
//!
//! ## Knopf (Default AUS = heutiges synchrones Verhalten)
//!
//! `MOSAIC_INTERLEAVE_ENABLED=1` (siehe [`interleave_enabled`]). Bei AUS
//! registriert [`ensure_batcher_for`] nichts (No-Op), [`lookup`] findet daher
//! nirgends einen Batcher, und JEDE Aufrufstelle in `net_mcts.rs` faellt auf
//! ihren bestehenden synchronen `Net::eval*`-Aufruf zurueck -- byte-identisch
//! zum Vor-Verschraenkungs-Verhalten (gleiche Funktionsaufrufe, gleiche
//! Reihenfolge, siehe dortige Kommentare).
//!
//! ## Was NICHT Teil dieser Datei ist
//!
//! Kein Virtual Loss (Weg B, als gating-pflichtig verworfen).
//!
//! Keine Freigabe des Batchers fuer `opp_points`-Aufrufer: seit dem
//! Ownership-Verbraucher Teil 1 traegt der Zeilen-Vertrag zwar SECHS Spalten
//! (inkl. `opp_points`, siehe [`BatchRow`]), aber `net_mcts.rs`s
//! `try_batched_pair_ex` behaelt seinen `points_utility_w()>0`-Waechter
//! UNVERAENDERT -- Task #28 unter eingeschalteter Verschraenkung ist eine
//! eigene, nie gemessene Kombination, und dieser Auftrag aendert daran
//! bewusst nichts. Der Waechter ist damit strenger als noetig, nicht falsch.

use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, AtomicUsize, Ordering};
use std::sync::mpsc::{self, RecvTimeoutError, Sender};
use std::sync::{Arc, Mutex, OnceLock};
use std::time::Duration;

use crate::net::Net;

/// Eine Merkmalszeile + Antwortkanal. `resp_tx` bekommt GENAU EINE Antwort
/// (Ok = `(policy,value,moon,points,opp_points,ownership)`-Zeile, Err =
/// Fehlertext).
///
/// Ownership-Verbraucher Teil 1 (`PREREG_ownership_consumer.md` §5 Punkt 6):
/// der Vertrag ist von 4 auf 6 Spalten erweitert, weil sonst JEDES ueber den
/// Sammel-Faden ausgewertete Blatt seine Ownership-Karte verloeren wuerde --
/// der Verbraucher saehe dann bei eingeschalteter Verschraenkung still einen
/// leeren Kopf und schoebe nichts, waehrend er es ohne Verschraenkung taete.
/// Genau diese Art stiller Pfadabhaengigkeit soll die Verdrahtung vermeiden.
type BatchRow = (Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>, Vec<f32>);

struct Request {
    feats: Vec<f32>,
    resp_tx: Sender<Result<BatchRow, String>>,
}

/// Lauflaufende Zaehler fuer die Durchsatz-/Batch-Messung (Abnahme Punkt 3,
/// "berichte den TATSAECHLICH erreichten mittleren Batch"). `Relaxed` reicht
/// -- reine Beobachtungsgroessen, kein weiterer Zustand haengt kausal daran.
#[derive(Default)]
pub struct BatcherStats {
    pub batches: AtomicU64,
    pub rows: AtomicU64,
    pub max_batch_seen: AtomicUsize,
}

impl BatcherStats {
    /// Mittlerer Batch = Zeilen/Batches ueber die gesamte Laufzeit des
    /// Sammel-Fadens (nicht nur ein Fenster) -- fuer die Abnahme-Messung
    /// wird der Batcher je Testlauf frisch erzeugt, daher ist "gesamte
    /// Laufzeit" dort "genau dieser Testlauf".
    pub fn mean_batch(&self) -> f64 {
        let batches = self.batches.load(Ordering::Relaxed);
        if batches == 0 {
            return 0.0;
        }
        self.rows.load(Ordering::Relaxed) as f64 / batches as f64
    }
}

pub struct Batcher {
    req_tx: Sender<Request>,
    pub stats: Arc<BatcherStats>,
}

impl Batcher {
    /// Reicht `feats.len()` Merkmalszeilen als EIN logischer Aufruf ein
    /// (z.B. Mover+Gegner-Paar) -- blockiert den aufrufenden Faden, bis ALLE
    /// Zeilen beantwortet sind. Die einzelnen Zeilen koennen vom Sammel-Faden
    /// mit denen ANDERER, GLEICHZEITIGER Aufrufer in DENSELBEN physischen
    /// `eval_batch`-Aufruf gemischt werden -- das ist der ganze Zweck.
    pub fn eval_rows(&self, feats: &[&[f32]]) -> Result<Vec<BatchRow>, String> {
        let mut receivers = Vec::with_capacity(feats.len());
        for f in feats {
            let (resp_tx, resp_rx) = mpsc::channel();
            self.req_tx
                .send(Request { feats: f.to_vec(), resp_tx })
                .map_err(|_| "Sammel-Faden nicht erreichbar (Kanal geschlossen)".to_string())?;
            receivers.push(resp_rx);
        }
        let mut out = Vec::with_capacity(feats.len());
        for rx in receivers {
            let reply = rx.recv().map_err(|_| "keine Antwort vom Sammel-Faden erhalten".to_string())?;
            out.push(reply?);
        }
        Ok(out)
    }
}

/// Sammel-Faden-Schleife: wartet auf die erste Zeile eines neuen Batches
/// (unbefristet -- kein Batch zu fuellen ist kein Fehler, nur Leerlauf
/// zwischen Partien/Suchknoten), sammelt dann bis zu `batch_max` weitere
/// Zeilen mit `fill_timeout` als Deadlock-Waechter je Slot (siehe
/// Modul-Kommentar), ruft EINMAL `net.eval_batch`, verteilt die Ergebnisse
/// zeilenweise zurueck. Endet, wenn alle `Sender` (also alle `Batcher`-Klone,
/// inkl. des in der Registry gehaltenen) verschwunden sind.
fn collector_loop(
    net: Arc<Net>,
    req_rx: mpsc::Receiver<Request>,
    batch_max: usize,
    fill_timeout: Duration,
    stats: Arc<BatcherStats>,
) {
    loop {
        let first = match req_rx.recv() {
            Ok(r) => r,
            Err(_) => return,
        };
        let mut batch = Vec::with_capacity(batch_max);
        batch.push(first);
        while batch.len() < batch_max {
            match req_rx.recv_timeout(fill_timeout) {
                Ok(r) => batch.push(r),
                Err(RecvTimeoutError::Timeout) => break,
                Err(RecvTimeoutError::Disconnected) => break,
            }
        }

        let feats_refs: Vec<&[f32]> = batch.iter().map(|r| r.feats.as_slice()).collect();
        // Genau HIER laeuft (bei eingeschaltetem `MOSAIC_ORT_CUDA_ENABLED`
        // und aktivem `ort_cuda_probe`-Feature) automatisch der ORT-CUDA-
        // Kanal mit -- `net.rs::eval_batch_ex` prueft den Knopf selbst, dieser
        // Aufruf hier weiss nichts davon und muss es auch nicht wissen.
        // `eval_batch_ex` statt `eval_batch` seit dem Ownership-Verbraucher
        // Teil 1: gleicher vorgebauter tract-Plan, gleiche Extraktion der
        // Ausgaben 0..3, zusaetzlich `opp_points`/`ownership` (siehe
        // `BatchRow`-Doku). Der GPU-Pfad bleibt erhalten, weil
        // `eval_batch_ex` denselben ORT-Haken bekommen hat.
        let result = net.eval_batch_ex(&feats_refs);

        let batch_len = batch.len();
        stats.batches.fetch_add(1, Ordering::Relaxed);
        stats.rows.fetch_add(batch_len as u64, Ordering::Relaxed);
        stats.max_batch_seen.fetch_max(batch_len, Ordering::Relaxed);

        match result {
            Ok(rows) => {
                for (req, row) in batch.into_iter().zip(rows.into_iter()) {
                    let _ = req.resp_tx.send(Ok(row));
                }
            }
            Err(e) => {
                let msg = e.to_string();
                for req in batch {
                    let _ = req.resp_tx.send(Err(msg.clone()));
                }
            }
        }
    }
}

/// Startet einen neuen Sammel-Faden fuer `net` und gibt das Client-Handle
/// zurueck. `net` muss `Arc` sein (siehe Modul-Kommentar "Registrierung nach
/// Zeigeridentitaet") -- der Faden haelt diesen Klon fuer seine gesamte
/// Lebensdauer, `'static` per Konstruktion.
fn spawn_batcher(net: Arc<Net>, batch_max: usize, fill_timeout: Duration) -> Arc<Batcher> {
    let (req_tx, req_rx) = mpsc::channel::<Request>();
    let stats = Arc::new(BatcherStats::default());
    let stats_c = Arc::clone(&stats);
    std::thread::Builder::new()
        .name("mosaic-eval-batcher".to_string())
        .spawn(move || collector_loop(net, req_rx, batch_max, fill_timeout, stats_c))
        .expect("Sammel-Faden sollte startbar sein");
    Arc::new(Batcher { req_tx, stats })
}

static INTERLEAVE_ENABLED: OnceLock<bool> = OnceLock::new();

/// `MOSAIC_INTERLEAVE_ENABLED=1` (oder jeder nicht-"0"/nicht-leere Wert)
/// schaltet die Verschraenkung ein. Default AUS -- siehe Modul-Kommentar.
pub(crate) fn interleave_enabled() -> bool {
    *INTERLEAVE_ENABLED.get_or_init(|| match std::env::var("MOSAIC_INTERLEAVE_ENABLED") {
        Ok(v) => v != "0" && !v.trim().is_empty(),
        Err(_) => false,
    })
}

static BATCH_MAX: OnceLock<usize> = OnceLock::new();

/// Obergrenze der Sammel-Faden-Fuellung je physischem `eval_batch`-Aufruf.
/// `MOSAIC_INTERLEAVE_BATCH_MAX`, geklemmt auf `1..=net::EVAL_BATCH_MAX_N`
/// (der Sammel-Faden kann nicht mehr an `eval_batch` uebergeben, als dort
/// Plaene vorgebaut sind) -- Default = `EVAL_BATCH_MAX_N` selbst (volle
/// Kapazitaet nutzen).
fn configured_batch_max() -> usize {
    *BATCH_MAX.get_or_init(|| {
        std::env::var("MOSAIC_INTERLEAVE_BATCH_MAX")
            .ok()
            .and_then(|s| s.trim().parse::<usize>().ok())
            .filter(|&n| n >= 1 && n <= crate::net::EVAL_BATCH_MAX_N)
            .unwrap_or(crate::net::EVAL_BATCH_MAX_N)
    })
}

static FILL_TIMEOUT_US: OnceLock<u64> = OnceLock::new();

/// Deadlock-Waechter-Zeitfenster je zusaetzlichem Slot. `MOSAIC_INTERLEAVE_
/// FILL_TIMEOUT_US`, Default 200µs -- exakt derselbe Wert, den der validierte
/// Probelauf (`interleave_concurrency_probe.rs::SLOT_TIMEOUT`) nutzt: klar
/// unter jeder gemessenen Service-Zeit (Probelauf: ~3,2-4,2ms, siehe
/// `evaluations/interleave_concurrency_probe.json`), damit dieses Fenster
/// die Fuellung nicht selbst deckelt, aber lang genug fuer Kanal-Weck-Jitter.
fn fill_timeout() -> Duration {
    Duration::from_micros(*FILL_TIMEOUT_US.get_or_init(|| {
        std::env::var("MOSAIC_INTERLEAVE_FILL_TIMEOUT_US")
            .ok()
            .and_then(|s| s.trim().parse::<u64>().ok())
            .unwrap_or(200)
    }))
}

static REGISTRY: OnceLock<Mutex<HashMap<usize, Arc<Batcher>>>> = OnceLock::new();

fn registry() -> &'static Mutex<HashMap<usize, Arc<Batcher>>> {
    REGISTRY.get_or_init(|| Mutex::new(HashMap::new()))
}

/// Registriert (einmalig je `Net`-Instanz) einen Sammel-Faden fuer
/// `net_arc`, FALLS die Verschraenkung eingeschaltet ist -- No-Op sonst.
/// Aufrufer (`self_play.rs`) kann diese Funktion daher UNBEDINGT aufrufen,
/// ohne den Knopf selbst zu pruefen (Default-aus-Verhalten bleibt dadurch
/// an dieser Stelle ein einzelner Bool-Check, kein zusaetzlicher Zweig).
pub fn ensure_batcher_for(net_arc: &Arc<Net>) {
    if !interleave_enabled() {
        return;
    }
    let key = Arc::as_ptr(net_arc) as usize;
    let mut map = registry().lock().unwrap();
    map.entry(key)
        .or_insert_with(|| spawn_batcher(Arc::clone(net_arc), configured_batch_max(), fill_timeout()));
}

/// Sucht den registrierten Sammel-Faden fuer `net` (Zeigeridentitaet) --
/// `None`, wenn keiner registriert ist (Knopf aus, `ensure_batcher_for` nie
/// aufgerufen, oder ein anderes `Net` als das registrierte). Tiefe
/// Aufrufstellen (`net_mcts.rs`) nutzen dies, um OHNE eigenen `Arc<Net>`
/// festzustellen, ob fuer DIESES Netz gerade verschraenkt ausgewertet wird.
pub fn lookup(net: &Net) -> Option<Arc<Batcher>> {
    let key = net as *const Net as usize;
    registry().lock().unwrap().get(&key).cloned()
}

/// NUR fuer Tests/Beispiele: entfernt alle registrierten Sammel-Faeden
/// (schliesst ihre `req_tx`, die Faeden selbst enden dann beim naechsten
/// `req_rx.recv()` mit `Disconnected`). Kein produktiver Aufrufer -- die
/// Registry lebt sonst fuer die gesamte Prozesslaufzeit (ein Selfplay-/
/// Arena-Lauf ist ohnehin ein Einweg-Prozess, siehe PyO3-Aufrufkonvention).
#[cfg(any(test, feature = "clone_profiling"))]
pub fn clear_registry_for_test() {
    registry().lock().unwrap().clear();
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Harter Fehler statt Skip bei fehlendem Modell (seit 2026-08-15): das
    /// alte `Option`-Muster liess die beiden Tests unten bei Abwesenheit
    /// still leer-gruen bestehen (Nutzer-Regel: nie leer gruen; Praezedenz
    /// `self_play.rs::load_test_net_for_gating`).
    fn load_test_net() -> Net {
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../models/alphazero_v20_2d_opp_brierbest.onnx");
        Net::load_auto(path.to_str().unwrap()).unwrap_or_else(|e| panic!(
            "{path:?} nicht ladbar ({e}) -- Test-Voraussetzung fehlt, der Test darf nicht \
             leer-gruen bestehen (Nutzer-Regel: nie leer gruen)."
        ))
    }

    #[test]
    fn interleave_enabled_defaults_to_false_when_unset() {
        // Eigene Testfunktion statt der echten `interleave_enabled()` --
        // sonst wuerde der Prozess-weite `OnceLock`-Cache diesen Test mit
        // allen ANDEREN, evtl. spaeter laufenden Tests im selben Binary
        // kontaminieren (gleiches Vorsichts-Muster wie `net_ort.rs`-Tests).
        static CELL: OnceLock<bool> = OnceLock::new();
        assert!(!*CELL.get_or_init(|| match std::env::var("MOSAIC_INTERLEAVE_ENABLED_TEST_UNSET_XYZ") {
            Ok(v) => v != "0" && !v.trim().is_empty(),
            Err(_) => false,
        }));
    }

    #[test]
    fn lookup_returns_none_when_nothing_registered() {
        let net = load_test_net();
        clear_registry_for_test();
        assert!(lookup(&net).is_none());
    }

    /// Kernabsicherung, OHNE den Prozess-weiten Env-Var-Knopf anzufassen
    /// (der ist `OnceLock`-gecacht, siehe `interleave_enabled`-Doku) --
    /// spawnt den Sammel-Faden HIER DIREKT (nicht ueber `ensure_batcher_for`,
    /// das haengt am Knopf) und prueft, dass mehrere gleichzeitige
    /// `eval_rows`-Aufrufe aus VERSCHIEDENEN Threads (Entscheidungsgleichheit,
    /// NICHT Bit-Gleichheit -- Toleranz 1e-5, gleicher Praezedenzfall wie
    /// `net.rs::eval_batch_matches_n_single_evals`, weil der Sammel-Faden je
    /// nach Ankunfts-Timing NICHT garantiert alle 8 Zeilen in EINEN
    /// physischen `eval_batch(N=8)`-Aufruf buendelt -- tract ist ueber
    /// verschiedene Batch-Plaene hinweg nicht bitgleich, siehe dortiger
    /// Kommentar) dieselben Ergebnisse liefern wie direkte `Net::eval`-Aufrufe.
    #[test]
    fn batcher_eval_rows_matches_direct_eval_batch() {
        let net = load_test_net();
        let net = Arc::new(net);
        let batcher = spawn_batcher(Arc::clone(&net), 8, Duration::from_millis(5));

        let feats: Vec<Vec<f32>> = (0..8)
            .map(|i| vec![(i as f32) * 0.01; net.input_size()])
            .collect();

        let handles: Vec<_> = feats
            .iter()
            .cloned()
            .map(|f| {
                let batcher = Arc::clone(&batcher);
                std::thread::spawn(move || batcher.eval_rows(&[&f]).expect("eval_rows"))
            })
            .collect();
        let mut via_batcher: Vec<BatchRow> =
            handles.into_iter().map(|h| h.join().unwrap().remove(0)).collect();

        let refs: Vec<&[f32]> = feats.iter().map(|v| v.as_slice()).collect();
        let direct = net.eval_batch_ex(&refs).expect("eval_batch_ex direkt");

        // Reihenfolge ist ueber Threads nicht garantiert -- nach dem ersten
        // Policy-Wert sortieren (Merkmale sind bewusst so gebaut, dass sie
        // eindeutig unterscheidbare Ausgaben liefern) macht den Vergleich
        // ordnungsunabhaengig.
        via_batcher.sort_by(|a, b| a.0[0].partial_cmp(&b.0[0]).unwrap());
        let mut direct_sorted = direct;
        direct_sorted.sort_by(|a, b| a.0[0].partial_cmp(&b.0[0]).unwrap());

        let close = |x: &[f32], y: &[f32]| -> bool {
            x.len() == y.len() && x.iter().zip(y).all(|(u, v)| (u - v).abs() < 1e-5)
        };
        assert_eq!(via_batcher.len(), direct_sorted.len());
        for (i, (a, b)) in via_batcher.iter().zip(direct_sorted.iter()).enumerate() {
            assert!(close(&a.0, &b.0), "Zeile {i}: policy weicht > 1e-5 ab");
            assert!(close(&a.1, &b.1), "Zeile {i}: value weicht > 1e-5 ab");
            assert!(close(&a.2, &b.2), "Zeile {i}: moon weicht > 1e-5 ab");
            assert!(close(&a.3, &b.3), "Zeile {i}: points weicht > 1e-5 ab");
            // Ownership-Verbraucher Teil 1: die beiden neuen Spalten muessen
            // ebenfalls durchkommen. `v20_2d_opp_brierbest` traegt BEIDE
            // Koepfe -- ein leerer `ownership`-Vektor waere hier also ein
            // Verdrahtungsfehler, kein "Modell ohne Kopf".
            assert!(close(&a.4, &b.4), "Zeile {i}: opp_points weicht > 1e-5 ab");
            assert!(close(&a.5, &b.5), "Zeile {i}: ownership weicht > 1e-5 ab");
            assert!(!a.5.is_empty(), "Zeile {i}: ownership leer -- Sammel-Faden reicht den Kopf nicht durch");
        }
    }
}
