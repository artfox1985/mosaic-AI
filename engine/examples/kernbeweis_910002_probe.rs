//! Gezielte Diagnose-Sonde (PREREG_agent_encapsulation.md par.8e-Folge,
//! Kernbeweis seed 910002, Runde 2, Kachel 4 -> Slot (2,1), Rotations-
//! Divergenz): prueft am EXAKT isolierten Entscheidungspunkt (Zustand per
//! Python/RefereeGame::state_json() eingefroren, siehe
//! isolate_rotation_decision.py) zwei Dinge:
//!  1. Ist der exact-JSON-Rundtrip (state_to_json_exact -> json_to_state_exact
//!     -> state_to_json_exact) an DIESER Stellung wirklich verlustfrei
//!     (JSON-Wert-Gleichheit vor/nach)? Wenn nein: welches Feld weicht ab.
//!  2. Q/Visits/Prior je Rotationskandidat + gewaehlte Aktion, bei
//!     WIEDERHOLTEM Aufruf mit demselben (state, seed) -- Determinismus-
//!     Selbstcheck der Suche auf dem rekonstruierten Zustand.
//!
//! Aufruf: cargo run --release --example kernbeweis_910002_probe -- \
//!   <target_rotation_state.json> <model.onnx>

use mosaic_rust::game::drafting_actions;
use mosaic_rust::net::Net;
use mosaic_rust::net_mcts::{net_effective_sims, net_root_child_stats_and_policy, net_search_drafting_action, SearchConfig};
use mosaic_rust::serialize::{action_to_dict, json_to_state_exact, state_to_json_exact};
use rand::rngs::StdRng;
use rand::SeedableRng;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let capture_path = args.get(1).expect("Arg 1: Pfad zu target_rotation_state.json");
    let model_path = args.get(2).expect("Arg 2: Pfad zum .onnx-Modell");

    let raw = std::fs::read_to_string(capture_path).expect("capture-Datei lesbar");
    let outer: serde_json::Value = serde_json::from_str(&raw).expect("capture JSON parsebar");
    let state_json_str = outer["state_json"].as_str().expect("state_json ist ein String");
    let seed: u64 = outer["seed"].as_u64().expect("seed ist u64");
    println!("geladen: seed={seed}, current_player={}, board_a={}", outer["current_player"], outer["board_a"]);

    let inner: serde_json::Value = serde_json::from_str(state_json_str).expect("state_json innen parsebar");

    // ── TEST 1: Rundtrip-Verlustfreiheit an GENAU dieser Stellung ──
    let mut state1 = json_to_state_exact(&inner).expect("json_to_state_exact");
    let rehydrated = state_to_json_exact(&state1, true);

    if inner == rehydrated {
        println!("TEST1 RUNDTRIP: IDENTISCH (state_to_json_exact(json_to_state_exact(x)) == x)");
    } else {
        println!("TEST1 RUNDTRIP: ABWEICHUNG GEFUNDEN");
        diff_json("$", &inner, &rehydrated);
    }

    // ── TEST 1b: gezielte Gegenprobe -- serialize.rs:823 rekonstruiert
    // `dome_tiles_placed_this_round` NUR aus dem `can_place_dome`-Bool (0 oder
    // DOME_TILES_PER_ROUND), nie als echte Zwischenzahl 1 (dokumentierte
    // Naeherung, serialize.rs:597-606, Kategorie 3). An DIESER Stellung ist
    // `tokens_used=1` (Log: "[Plaettchen 2/2]", der Spieler hat sein erstes
    // Kuppelplaettchen dieser Runde schon gelegt) -- die REKONSTRUIERTE
    // `dome_tiles_placed_this_round` sollte also 1 sein, nicht 0/2. Patch
    // testweise auf den aus `tokens_used` abgeleiteten Wert (identisches
    // Muster zu `self_play::seed_state_fixup`, der GENAU diese Luecke fuer
    // den Seeding-Pfad behebt -- referee.rs/json_to_state_exact rufen ihn
    // NICHT auf) und vergleiche die Suche VOR/NACH dem Patch.
    let cur_player = state1.current_player;
    let true_dome_tiles_placed = state1.players[cur_player].player_tokens_used.min(2);
    println!(
        "\nTEST1b GEGENPROBE: current_player={cur_player} player_tokens_used={} \
         dome_tiles_placed_this_round(rekonstruiert)={} vs. abgeleitet-korrekt={true_dome_tiles_placed}",
        state1.players[cur_player].player_tokens_used,
        state1.players[cur_player].dome_tiles_placed_this_round,
    );

    // ── TEST 2: Determinismus-Selbstcheck der Suche auf dem rekonstruierten Zustand ──
    // NEUE HYPOTHESE (dieser Agent, 2026-08-24): RefereeGame::drafting_decide_and_apply_inprocess
    // nutzt den Netz-Cache der LEBENDEN RefereeGame-Instanz (frueh geladen), waehrend
    // FrozenWorkerEngine::new() (Worker-Pfad) EINE EIGENE, ZWEITE Net::load_auto()-Instanz
    // DESSELBEN .onnx-Files haelt -- zwei UNABHAENGIGE tract-Ladevorgaenge. Lade das Modell
    // hier bewusst ZWEIMAL (net_a, net_b) und vergleiche die Suche auf BEIDEN Instanzen mit
    // identischem (state1, seed) -- prueft, ob zwei unabhaengige Ladevorgaenge DESSELBEN Files
    // bitgleiche Suchergebnisse liefern.
    let net_a = Net::load_auto(model_path).expect("Net::load_auto (Instanz A)");
    let net_b = Net::load_auto(model_path).expect("Net::load_auto (Instanz B)");
    // `long_row_init_shaping_w: 0.0` = Bestandsverhalten (Term aus) --
    // diese Sonde ist ein Byte-Identitaets-Nachweis, ihr Suchverhalten
    // MUSS unveraendert bleiben.
    let search_config = SearchConfig { implicit_minimax_alpha: 0.0, long_row_init_shaping_w: 0.0 };
    let actions = drafting_actions(&state1);
    println!(
        "Kandidaten (Reihenfolge aus drafting_actions, n={}):",
        actions.len()
    );
    for (i, a) in actions.iter().enumerate() {
        println!("  [{i}] {}", action_to_dict(a));
    }
    let effective_sims = net_effective_sims(400, actions.len());
    println!("effective_sims={effective_sims} (base=400, n_actions={})", actions.len());

    for trial in 0..2u32 {
        let use_net = if trial == 0 { &net_a } else { &net_b };
        let mut rng_stats = StdRng::seed_from_u64(seed);
        let (stats, completed_q_policy, root_q, completed_q_raw) =
            net_root_child_stats_and_policy(use_net, &state1, effective_sims, 1.5, false, &mut rng_stats, &search_config);
        let mut rng_choice = StdRng::seed_from_u64(seed);
        let chosen = net_search_drafting_action(use_net, &state1, effective_sims, 1.5, false, &mut rng_choice, &search_config);

        println!("-- trial {trial}, Netz-Instanz {} (frischer StdRng::seed_from_u64({seed}) je Aufruf) --", if trial == 0 { "A" } else { "B (unabhaengig geladen)" });
        println!("  root_q={root_q:?}");
        println!("  gewaehlt (net_search_drafting_action): {}", chosen.map(|a| action_to_dict(&a)).unwrap_or(serde_json::Value::Null));
        println!("  root_child_stats (Action, visits, Q):");
        for (a, visits, q) in &stats {
            println!("    {} visits={visits} q={q:.6}", action_to_dict(a));
        }
        println!("  completed_q_policy (Action, softmax-Politik):");
        for (a, p) in &completed_q_policy {
            println!("    {} p={p:.6}", action_to_dict(a));
        }
        println!("  completed_q_raw (Action, roh):");
        for (a, q) in &completed_q_raw {
            println!("    {} q={q:.6}", action_to_dict(a));
        }
    }

    // ── TEST 3: entscheidende Gegenprobe -- Suche NACH dem Patch aus TEST1b ──
    println!("\n=== TEST 3: Suche NACH Patch dome_tiles_placed_this_round={cur_player}->{true_dome_tiles_placed} ===");
    state1.players[cur_player].dome_tiles_placed_this_round = true_dome_tiles_placed;
    let mut rng_stats2 = StdRng::seed_from_u64(seed);
    let (stats2, _cqp2, root_q2, _cqr2) =
        net_root_child_stats_and_policy(&net_a, &state1, effective_sims, 1.5, false, &mut rng_stats2, &search_config);
    let mut rng_choice2 = StdRng::seed_from_u64(seed);
    let chosen2 = net_search_drafting_action(&net_a, &state1, effective_sims, 1.5, false, &mut rng_choice2, &search_config);
    println!("  root_q={root_q2:?}");
    println!("  gewaehlt NACH Patch: {}", chosen2.map(|a| action_to_dict(&a)).unwrap_or(serde_json::Value::Null));
    println!("  root_child_stats NACH Patch (Action, visits, Q):");
    for (a, visits, q) in &stats2 {
        println!("    {} visits={visits} q={q:.6}", action_to_dict(a));
    }
}

/// Rekursiver strukturierter JSON-Diff -- meldet JEDEN abweichenden Pfad
/// (nicht nur den ersten), damit die genaue Feld-Ursache sichtbar wird.
fn diff_json(path: &str, a: &serde_json::Value, b: &serde_json::Value) {
    use serde_json::Value;
    match (a, b) {
        (Value::Object(ma), Value::Object(mb)) => {
            let mut keys: Vec<&String> = ma.keys().chain(mb.keys()).collect();
            keys.sort();
            keys.dedup();
            for k in keys {
                let av = ma.get(k).unwrap_or(&Value::Null);
                let bv = mb.get(k).unwrap_or(&Value::Null);
                if av != bv {
                    diff_json(&format!("{path}.{k}"), av, bv);
                }
            }
        }
        (Value::Array(aa), Value::Array(ba)) => {
            if aa.len() != ba.len() {
                println!("  DIFF {path}: Array-Laenge {} vs {}", aa.len(), ba.len());
                println!("    A={a}");
                println!("    B={b}");
                return;
            }
            for (i, (av, bv)) in aa.iter().zip(ba.iter()).enumerate() {
                if av != bv {
                    diff_json(&format!("{path}[{i}]"), av, bv);
                }
            }
        }
        _ => {
            if a != b {
                println!("  DIFF {path}: A={a} B={b}");
            }
        }
    }
}
