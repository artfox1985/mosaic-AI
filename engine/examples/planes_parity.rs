//! Task #11 Phase 2, M1.3: Rust<->Python-Paritätstest für
//! `features::state_to_planes_direct` gegen `neural_net.py::state_to_planes`.
//! Liest eine JSON-Datei mit einer LISTE von State-Dicts (`state_to_json`-
//! Format, z.B. aus `evaluations/frozen_eval_set.pkl` extrahiert), berechnet
//! je Zustand den `[NUM_PLANES_CHANNELS,6,6]`-Planes-Puffer (C-Major, wie `net.rs` ihn
//! erwartet) und schreibt ihn als EINE Zeile Leerzeichen-getrennter Floats
//! (feste Präzision) pro Zustand nach stdout -- die Python-Seite vergleicht
//! das Zeile für Zeile gegen `state_to_planes(state).flatten()`.
//!
//! Kein Wheel-Install nötig (Sicherheitsregel 1): reiner `cargo run
//! --release --example`-Aufruf gegen die bereits gebaute Rust-Lib.
//!
//! Aufruf: cargo run --release --example planes_parity -- <states.json>

use mosaic_rust::features::{state_to_planes_direct, NUM_PLANES_CHANNELS};
use mosaic_rust::serialize::json_to_state;
use rand::rngs::StdRng;
use rand::SeedableRng;
use serde_json::Value;
use std::fs;

fn main() {
    let mut args = std::env::args().skip(1);
    let path = args.next().expect("Arg 1: Pfad zur JSON-Datei mit einer Liste von State-Dicts");
    let content = fs::read_to_string(&path).expect("Datei lesbar");
    let states: Vec<Value> = serde_json::from_str(&content).expect("gueltiges JSON (Liste von State-Dicts)");

    // Fester Seed: die RNG treibt in `json_to_state` NUR das Neumischen des
    // verdeckten Kuppelstapel-Restbestands (Kategorie 1, echte verdeckte
    // Information) -- `state_to_planes`/`state_to_planes_direct` lesen davon
    // nichts (nur `dome_grid` + `scoring_tile_ids`), die Wahl ist für den
    // Paritätstest also irrelevant.
    let mut rng = StdRng::seed_from_u64(0);

    eprintln!("planes_parity: {} Zustaende aus {}", states.len(), path);
    for (i, v) in states.iter().enumerate() {
        let state = json_to_state(v, &mut rng)
            .unwrap_or_else(|e| panic!("json_to_state fehlgeschlagen bei Zustand {i}: {e}"));
        let planes = state_to_planes_direct(&state);
        // Aus der KONSTANTE, nicht als Literal: der Block waechst additiv
        // (76 -> 77 -> 79), und ein Literal hier war nach dem 77er-Schritt
        // still falsch -- die Beispiel-Binary haette beim naechsten Lauf
        // gepanickt, ohne dass die Suite es je gemerkt haette.
        assert_eq!(
            planes.len(),
            NUM_PLANES_CHANNELS * 6 * 6,
            "Zustand {i}: falsche Planes-Laenge"
        );
        let line: Vec<String> = planes.iter().map(|x| format!("{x:.8}")).collect();
        println!("{}", line.join(" "));
    }
    eprintln!("planes_parity: fertig ({} Zeilen auf stdout).", states.len());
}
