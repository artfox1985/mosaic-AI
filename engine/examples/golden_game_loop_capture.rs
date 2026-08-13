//! Golden-Record-Harness fuer `evaluations/PREREG_unified_game_loop.md` §3.1
//! (Gate-B-Methodik, Vorbild: `sync_only_repeatability_after_rng_split` in
//! `self_play.rs`).
//!
//! Spielt je Spielschleifen-Pfad N feste Seeds ueber die OEFFENTLICHEN
//! `run_*`-Einstiege (dieselben, die py.rs/lib.rs exportieren -- damit sind
//! die duennen Wrapper nach dem Refactor automatisch mitgeprueft) und
//! schreibt die vollstaendige JSON-Ausgabe (Spielverlauf + Trainingsziel-
//! Felder inkl. `bootstrap_value`/`round_transition_value`/Policy-Targets
//! bzw. Arena-Summaries inkl. vollem `log` bei `log_games=true`) als EINE
//! Datei je Pfad nach `<outdir>/<pfad>.json`.
//!
//! Rein additiv: beruehrt keinen Produktionscode. Determinismus-Hinweis:
//! `round_transition_value`/`bootstrap_value` haengen an Wall-Clock-Deadlines
//! (`round_transition{,_deep}.rs`) -- ob sie auf DIESER Maschine bei der
//! gewaehlten Konfiguration stabil sind, stellt der Doppellauf VOR dem
//! Refactor fest (Basislinien-Messung, siehe Prereg-Protokoll).
//!
//! Aufruf:
//!   golden_game_loop_capture <outdir> [--paths p1,p1n,p2,p3,p4]
//!                            [--games N] [--rtv 0|1] [--model PFAD]
//!
//! Pfade:
//!   p1  = play_one_game via run_self_play            (Heuristik pur)
//!   p1n = play_one_game via run_self_play_with_net_labels (Heuristik + Netz-Labels)
//!   p2  = play_net_game via run_net_arena_match      (Netz vs. Heuristik, log_games=true)
//!   p3  = play_net_vs_net_game via run_net_vs_net_arena (Netz vs. Netz, log_games=true)
//!   p4  = play_net_self_play_game via run_net_self_play (Produktions-Self-Play)

use std::io::Write;

const GOLDEN_SEED: u64 = 20260814;
const DEFAULT_MODEL: &str = "../models/alphazero_v21_2d_brierbest.onnx";

fn write_out(outdir: &str, name: &str, payload: &str) {
    let path = std::path::Path::new(outdir).join(format!("{name}.json"));
    let mut f = std::fs::File::create(&path)
        .unwrap_or_else(|e| panic!("kann {path:?} nicht anlegen: {e}"));
    f.write_all(payload.as_bytes())
        .unwrap_or_else(|e| panic!("Schreibfehler {path:?}: {e}"));
    println!("{name}: {} Bytes -> {path:?}", payload.len());
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        eprintln!("Nutzung: golden_game_loop_capture <outdir> [--paths ..] [--games N] [--rtv 0|1] [--model PFAD]");
        std::process::exit(2);
    }
    let outdir = args[1].clone();
    let mut paths = vec!["p1".to_string(), "p1n".to_string(), "p2".to_string(), "p3".to_string(), "p4".to_string()];
    let mut n_games = 8usize;
    let mut rtv = true;
    let mut model = {
        let manifest = env!("CARGO_MANIFEST_DIR");
        std::path::Path::new(manifest).join(DEFAULT_MODEL).to_string_lossy().into_owned()
    };
    let mut i = 2;
    while i + 1 < args.len() + 1 {
        match args.get(i).map(String::as_str) {
            Some("--paths") => {
                paths = args[i + 1].split(',').map(str::to_string).collect();
                i += 2;
            }
            Some("--games") => {
                n_games = args[i + 1].parse().expect("--games braucht eine Zahl");
                i += 2;
            }
            Some("--rtv") => {
                rtv = args[i + 1] != "0";
                i += 2;
            }
            Some("--model") => {
                model = args[i + 1].clone();
                i += 2;
            }
            Some(other) => panic!("unbekanntes Argument {other:?}"),
            None => break,
        }
    }
    std::fs::create_dir_all(&outdir).expect("outdir nicht anlegbar");
    println!(
        "Golden-Capture: seed={GOLDEN_SEED} games={n_games} rtv={rtv} model={model}\npaths={paths:?}"
    );

    use mosaic_rust::net_mcts::DEFAULT_C_PUCT;
    use mosaic_rust::self_play::{
        run_net_arena_match, run_net_self_play, run_net_vs_net_arena, run_self_play,
        run_self_play_with_net_labels, SELF_PLAY_C,
    };

    for p in &paths {
        let t0 = std::time::Instant::now();
        match p.as_str() {
            "p1" => {
                let out = run_self_play(n_games, 32, SELF_PLAY_C, GOLDEN_SEED, 1, "golden_p1", None, None);
                write_out(&outdir, "p1", &out);
            }
            "p1n" => {
                let out = run_self_play_with_net_labels(
                    &model, n_games, 32, SELF_PLAY_C, GOLDEN_SEED, 1, "golden_p1n", rtv, None, None,
                )
                .expect("run_self_play_with_net_labels fehlgeschlagen");
                write_out(&outdir, "p1n", &out);
            }
            "p2" => {
                let out = run_net_arena_match(
                    &model, 24, 24, n_games, GOLDEN_SEED, 1, SELF_PLAY_C, DEFAULT_C_PUCT, true, None,
                )
                .expect("run_net_arena_match fehlgeschlagen");
                write_out(&outdir, "p2", &out);
            }
            "p3" => {
                let out = run_net_vs_net_arena(
                    &model, &model, 24, 24, n_games, GOLDEN_SEED, 1, DEFAULT_C_PUCT, DEFAULT_C_PUCT,
                    true, None,
                )
                .expect("run_net_vs_net_arena fehlgeschlagen");
                write_out(&outdir, "p3", &out);
            }
            "p4" => {
                let out = run_net_self_play(
                    &model, n_games, 60, DEFAULT_C_PUCT, GOLDEN_SEED, 1, "golden_p4", true, false,
                    rtv, None, None, None, 0,
                )
                .expect("run_net_self_play fehlgeschlagen");
                write_out(&outdir, "p4", &out);
            }
            other => panic!("unbekannter Pfad {other:?} (erwartet p1|p1n|p2|p3|p4)"),
        }
        println!("  {p} fertig nach {:?}", t0.elapsed());
    }
}
