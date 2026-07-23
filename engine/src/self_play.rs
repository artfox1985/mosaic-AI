//! Self-Play-Datengenerierung in Rust — Port von `self_play.py` (MCTS-Modus).
//!
//! Spielt komplette Partien auf der Rust-Engine (Drafting per MCTS, Tiling per
//! exaktem DFS-Solver) und liefert je Zug einen Trainings-Record im **selben**
//! Format wie `self_play.py` (state = `serialize_state`-kompatibles JSON,
//! `policy`/`valid_actions` im **agent_env-Schema**, `moon_order_target`,
//! `scores`, `winner`, `player`, `game_id`). Ein schlankes Python-`self_play.py`
//! pickled die Records — `train.py` und das Pickle-Format bleiben unverändert.
//!
//! Wichtig: `policy`/`valid_actions` folgen dem agent_env-Schema
//! (`factory_index`, `display_index`, `color`, `row`, `pattern_row`, …), weil
//! `agents/neural_net.py::action_to_id` genau diese Keys liest — NICHT dem
//! `serialize::action_to_dict`-Schema (`factory_id`, `tile_id`).

use std::fs::{File, OpenOptions};
use std::io::{BufWriter, Write};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, Mutex};

use rand::rngs::StdRng;
use rand::seq::{IndexedRandom, SliceRandom};
use rand::{Rng, RngExt, SeedableRng};
use rayon::prelude::*;
use serde_json::{json, Map, Value};

use crate::dome::SpaceType;
use crate::features::{action_to_id, state_to_features_direct};
use crate::game::{
    apply_start_placement, determine_winner, drafting_actions, execute_draw_from_stack, Game,
    TilingMove,
};
use crate::mcts::{dynamic_sims, player_total, root_child_stats, search_drafting_action};
use crate::net::Net;
use crate::net_mcts::{net_effective_sims, net_root_child_stats, net_search_drafting_action};
use crate::moves::{Action, DrawFromStackMove, Move, PlaceAction, TakeAction, TakeSource};
use crate::round_end::{
    apply_bonus_chips_with, can_complete_row_with_chips, generate_tiling_actions,
    row_has_open_matching_slot,
};
use crate::scoring::{sample_valid_scoring_ids, wertung_progress};
use crate::serialize::state_to_json;
use crate::state::{GameState, Phase};
use crate::tile::TileColor;
use crate::tiling_solver::{best_first_step_exact, solve_round_final_score, TilingStep};

/// Standard-UCT-Konstante der Self-Play-Suche (= `py.rs::AI_C`).
pub const SELF_PLAY_C: f64 = 0.3;

/// Temperatur für die AUFGEZEICHNETE Policy-Target (scharf → Destillation der
/// Heuristik-Wahl). Entkoppelt von der Play-Temperatur (die fürs Sampeln der
/// gespielten Aktion sorgt und die Zustandsvielfalt erhält). Niedriger = schärfer.
pub const TARGET_TEMP: f64 = 0.15;

/// Boden-Wallclock für den Hänger-Schutz, unabhängig von der Sim-Zahl — sehr
/// niedrige Sims (Tests, kleine Debug-Läufe) sollen trotzdem nie unter dieses
/// Minimum fallen.
const MIN_GAME_TIMEOUT_SECS: u64 = 30;

/// Hänger-Schutz-Wallclock für reine Heuristik-Partien (`play_one_game`,
/// `play_arena_game`), SKALIERT mit der tatsächlich verwendeten Sim-Zahl statt
/// eines fixen Werts — ein fixer Wert (früher 30s, kalibriert auf niedrige
/// Sim-Zahlen, "normal 1-4s") reißt bei jeder künftigen Erhöhung der Sims
/// wieder: bei 400 Sims plus den seit diesem Zyklus zusätzlichen
/// Blattbewertungskosten (Wertungsplatten-/Unplaceable-Penalty-Projektion pro
/// Knoten) wurden Partien vereinzelt vor Rundenende abgebrochen, scores/winner
/// sind dann kein echtes Endergebnis. Faktor 0.3s/Sim kalibriert so, dass bei
/// 400 Sims wie zuletzt 120s Puffer herauskommen.
fn heuristic_game_timeout_secs(sims: u32) -> u64 {
    ((sims as u64 * 3) / 10).max(MIN_GAME_TIMEOUT_SECS)
}

/// Hänger-Schutz-Wallclock für netzbeteiligte Partien (`play_net_game`,
/// `play_net_vs_net_game`, `play_net_self_play_game`) — jede Simulation
/// braucht eine ONNX-Inferenz, das ist deutlich langsamer als reine
/// Heuristik-Suche, daher ein höherer Faktor pro Sim als bei
/// `heuristic_game_timeout_secs`. SKALIERT mit der Sim-Zahl aus demselben
/// Grund: bei 30s fix wurden Self-Play-Partien bei 400 Sims systematisch vor
/// Rundenende (Runde 3-4 von 5) abgeschnitten — die aufgezeichneten
/// scores/winner solcher Partien sind dann KEIN echtes Endergebnis
/// (Wertungsplatten werden nur bei Phase::End angewendet), was das gesamte
/// Punkte-Marge-Value-Target korrumpiert. Faktor 0.45s/Sim kalibriert so, dass
/// bei 400 Sims wie zuletzt 180s Puffer herauskommen.
fn net_game_timeout_secs(sims: u32) -> u64 {
    ((sims as u64 * 9) / 20).max(MIN_GAME_TIMEOUT_SECS)
}

// ── Fortschritts-Tracking: Einzelspiel-Flush + Heartbeat (Task #71) ─────────
// Wurzel-Problem (siehe self_play.py-Modulkommentar zum Chunk-Hänger-
// Supervisor): ein Chunk lief bisher komplett in EINEM Rust-Aufruf, der ALLE
// `n_games` Partien rayon-parallel spielt und erst am Ende (`.collect()`)
// irgendetwas zurückgibt -- ein harter Kill (Timeout) verwirft deshalb bis zu
// `chunk`-1 bereits fertige Partien, und der Supervisor kann "langsam unter
// Last" nicht von "tot" unterscheiden (beides sieht von außen gleich aus:
// keine Rückgabe). Fix, minimal-invasiv (Dateiformat der finalen .pkl bleibt
// UNVERÄNDERT): optional (beide Pfade `None` = Verhalten exakt wie vorher)
// schreibt JEDES fertige Spiel sofort eine Zeile in eine JSONL-Zwischendatei
// (`progress_path`), UND ein Hintergrund-Thread aktualisiert periodisch eine
// kleine Herzschlag-Datei (`heartbeat_path`) mit Zug-/Spielzählern -- der
// Python-Supervisor beobachtet deren mtime statt eines starren
// Chunk-Gesamttimeouts.

/// Öffnet (falls `progress_path` gesetzt) die JSONL-Zwischendatei im
/// Append-Modus. `None` (kein Pfad) hält das Verhalten identisch zu vorher
/// (kein Fortschritts-Tracking, z.B. Diagnose-/Arena-Aufrufe).
fn open_progress_file(progress_path: Option<&str>) -> Option<Arc<Mutex<BufWriter<File>>>> {
    progress_path.map(|p| {
        let f = OpenOptions::new()
            .create(true)
            .append(true)
            .open(p)
            .unwrap_or_else(|e| panic!("Fortschritts-Datei '{p}' konnte nicht geoeffnet werden: {e}"));
        Arc::new(Mutex::new(BufWriter::new(f)))
    })
}

/// Schreibt EIN fertiges Spiel (dessen Step-Records) als eine JSONL-Zeile --
/// Thread-sicher (Mutex, mehrere rayon-Worker schreiben gleichzeitig
/// unterschiedliche Spiele fertig) und geflusht (minimiert das Zeitfenster
/// für eine unvollständige Zeile bei einem harten Kill mitten im Schreiben).
/// Best-effort: ein Schreibfehler (volle Platte etc.) darf den Self-Play-Lauf
/// selbst nicht abbrechen, nur diesen einen Fortschritts-Eintrag verlieren.
fn append_game_progress(file: &Option<Arc<Mutex<BufWriter<File>>>>, steps: &[Value]) {
    if let Some(f) = file {
        if let Ok(line) = serde_json::to_string(steps) {
            if let Ok(mut guard) = f.lock() {
                let _ = writeln!(guard, "{line}");
                let _ = guard.flush();
            }
        }
    }
}

/// Startet (falls `heartbeat_path` gesetzt) einen Hintergrund-Thread, der
/// alle 2s den aktuellen Zug-/Spielzähler in eine kleine JSON-Datei schreibt
/// -- der Supervisor (self_play.py) killt einen Chunk nur noch, wenn deren
/// mtime für eine Weile stillsteht (unterscheidet "läuft noch, nur langsam
/// unter Last" von "hängt/ist tot"), statt bei jedem trägen, aber lebenden
/// Chunk vorschnell abzubrechen. `move_counter` wird aus den per-Zug-Schleifen
/// in `play_one_game`/`play_net_self_play_game` inkrementiert (feinere
/// Granularität als nur "Spiel fertig" -- ein einzelnes Spiel kann bei hohen
/// Sim-Zahlen selbst deutlich länger als die 120s-Herzschlag-Toleranz
/// brauchen). Rückgabe: Stop-Flag + Thread-Handle, MUSS nach dem parallelen
/// Batch über `stop_heartbeat_reporter` aufgeräumt werden.
fn start_heartbeat_reporter(
    heartbeat_path: Option<String>,
    move_counter: Arc<AtomicU64>,
    games_counter: Arc<AtomicU64>,
) -> (Arc<AtomicBool>, Option<std::thread::JoinHandle<()>>) {
    let stop = Arc::new(AtomicBool::new(false));
    let handle = heartbeat_path.map(|hp| {
        let stop2 = Arc::clone(&stop);
        std::thread::spawn(move || {
            let write_once = |last: &mut (u64, u64)| {
                let cur = (move_counter.load(Ordering::Relaxed), games_counter.load(Ordering::Relaxed));
                if cur != *last {
                    let body = format!("{{\"moves_done\":{},\"games_done\":{}}}", cur.0, cur.1);
                    let _ = std::fs::write(&hp, body);
                    *last = cur;
                }
            };
            let mut last = (u64::MAX, u64::MAX); // erzwingt einen initialen Schreibvorgang
            loop {
                write_once(&mut last);
                if stop2.load(Ordering::Relaxed) {
                    break;
                }
                std::thread::sleep(std::time::Duration::from_secs(2));
            }
            // Letzter Schreibvorgang nach dem Stop-Signal -- der finale Stand
            // (z.B. "alle Spiele fertig") muss sichtbar sein, auch wenn der
            // Supervisor genau in diesem Moment liest.
            write_once(&mut last);
        })
    });
    (stop, handle)
}

/// Signalisiert dem Heartbeat-Thread das Ende des Batches und wartet auf
/// dessen (kurzen) letzten Schreibvorgang -- verhindert einen verwaisten
/// Thread, wenn derselbe Prozess mehrere Self-Play-Aufrufe nacheinander macht.
fn stop_heartbeat_reporter(stop: Arc<AtomicBool>, handle: Option<std::thread::JoinHandle<()>>) {
    stop.store(true, Ordering::Relaxed);
    if let Some(h) = handle {
        let _ = h.join();
    }
}

// ── agent_env-Action-Serializer ──────────────────────────────────────────────

/// `factory_index` einer Stein-Aktion (Port der Logik aus
/// `agents/agent_env.py::_drafting_actions`): 0–3 = kleine Fabriken,
/// 4 = große Fabrik (Sun), 5 = globaler Mond (Aktion C, `factory_id=None`).
fn factory_index(state: &GameState, t: &TakeAction) -> i64 {
    match t.source {
        TakeSource::LargeFactorySun => 4,
        TakeSource::SmallFactoryMoon | TakeSource::LargeFactoryMoon => match t.factory_id {
            Some(fid) => factory_pos(state, fid),
            None => 5,
        },
        TakeSource::SmallFactorySun => match t.factory_id {
            Some(fid) => factory_pos(state, fid),
            None => 0,
        },
    }
}

fn factory_pos(state: &GameState, fid: usize) -> i64 {
    state
        .factories
        .iter()
        .position(|f| f.factory_id == fid)
        .map(|i| i as i64)
        .unwrap_or(0)
}

/// Mappt eine Engine-`Action` auf das agent_env-Dict (Schlüssel, die
/// `action_to_id` liest).
pub(crate) fn action_to_env_dict(state: &GameState, a: &Action) -> Value {
    match a {
        Action::Stone(m) => json!({
            "type": "stone",
            "factory_index": factory_index(state, &m.take),
            "color": m.take.color.value(),
            "row": m.place.row_index,
            // Nur Debug-/Introspektions-Info — action_to_id liest dieses Feld
            // NICHT (Moon-Order-Varianten teilen sich bewusst dieselbe ID; die
            // Suche kombiniert ihre Priors separat, siehe net_mcts.rs).
            "moon_order": m.take.moon_order.iter().map(|c| c.value()).collect::<Vec<_>>(),
        }),
        Action::ChooseDomeSlot(m) => {
            let d_idx = state
                .dome_display
                .iter()
                .position(|t| t.tile_id == m.dome_tile_id)
                .unwrap_or(0);
            json!({
                "type": "choose_dome_slot",
                "display_index": d_idx,
                "slot_row": m.slot_row,
                "slot_col": m.slot_col,
            })
        }
        Action::DrawStackPeek => json!({ "type": "dome_stack_peek" }),
        Action::ChooseDrawStackSlot(m) => {
            // Position von `chosen_id` in der deduplizierten Pending-Liste --
            // exakt dieselbe Dedup-Reihenfolge wie `generate_draw_stack_moves`
            // (game.rs), damit `pending_index` konsistent zur Kandidaten-
            // generierung ist. `chosen_id` selbst fliesst NICHT in die ID ein
            // (wie bisher) -- `pending_index` ist nur eine grobe, beschraenkte
            // Ersatzdimension dafuer (siehe action_to_id/choose_draw_stack_slot).
            let mut ids: Vec<usize> =
                state.pending_stack_draw.iter().map(|t| t.tile_id).collect();
            ids.sort_unstable();
            ids.dedup();
            let pending_index = ids.iter().position(|&id| id == m.chosen_id).unwrap_or(0);
            json!({
                "type": "choose_draw_stack_slot",
                "slot_row": m.slot_row,
                "slot_col": m.slot_col,
                "pending_index": pending_index,
            })
        }
        Action::ChooseDomeRotation(rot) => json!({ "type": "choose_dome_rotation", "rotation": rot }),
        Action::BonusChip(m) => json!({
            "type": "bonus_chip",
            "factory_index": factory_pos(state, m.factory_id),
        }),
        Action::Pass => json!({ "type": "pass" }),
    }
}

/// Direkter `Action → ID`-Match ohne JSON-Umweg (Performance, externer
/// Hinweis Abschnitt D, 2026-07-20) -- identische Logik zu
/// `features::action_to_id(&action_to_env_dict(state, a))`, nur ohne den
/// serde_json-Objektbau + String-Matching im heißesten Suchpfad
/// (`net_mcts::build_untried_actions`, pro legaler Aktion pro Knoten
/// aufgerufen). NUR für Drafting-Phase-Aktionen (alle `Action`-Varianten
/// decken das ab) -- Tiling-Phase-IDs (`end_tiling`/`tiling`/`use_chips` in
/// `action_to_id`) werden hier nicht gebraucht, `build_untried_actions`
/// läuft nur auf Drafting-Knoten. Parität mit dem JSON-Pfad wird per Test
/// abgesichert (`action_to_id_direct_matches_json_path_across_random_games`).
pub(crate) fn action_to_id_direct(state: &GameState, a: &Action) -> usize {
    match a {
        Action::Pass => 0,
        Action::Stone(m) => {
            let c_id: i64 = match m.take.color {
                TileColor::Blau => 0,
                TileColor::Gelb => 1,
                TileColor::Rot => 2,
                TileColor::Schwarz => 3,
                TileColor::Tuerkis => 4,
                TileColor::Wild => -1,
            }
            .max(0);
            let r_id = m.place.row_index as i64 + 1;
            let f_idx = factory_index(state, &m.take);
            (10 + c_id * 48 + r_id * 6 + f_idx).clamp(0, 273) as usize
        }
        Action::ChooseDomeSlot(m) => {
            let d_idx =
                state.dome_display.iter().position(|t| t.tile_id == m.dome_tile_id).unwrap_or(0);
            328 + d_idx * 9 + m.slot_row * 3 + m.slot_col
        }
        Action::ChooseDrawStackSlot(m) => {
            let mut ids: Vec<usize> = state.pending_stack_draw.iter().map(|t| t.tile_id).collect();
            ids.sort_unstable();
            ids.dedup();
            let pending_index = ids.iter().position(|&id| id == m.chosen_id).unwrap_or(0);
            let p_idx = pending_index.min((crate::features::MAX_PENDING_STACK_TILES - 1) as usize);
            355 + p_idx * 9 + m.slot_row * 3 + m.slot_col
        }
        Action::ChooseDomeRotation(rot) => 391 + ((*rot / 90) as usize).min(3),
        Action::BonusChip(m) => (401 + factory_pos(state, m.factory_id)) as usize,
        Action::DrawStackPeek => 405,
    }
}

// ── Policy-Extraktion (Port von SelfPlayMixin.search_and_get_policy) ──────────

/// Gewichtete Policy aus der Wurzelkind-Statistik:
/// `visits^(1/temp) * max(q,1e-6)^2`, normalisiert. Liefert die gewählte Aktion
/// (per Gewichten gesampelt) und die Policy-Einträge (agent_env-Schema).
fn drafting_policy<R: Rng + ?Sized>(
    state: &GameState,
    actions: &[Action],
    base_sims: u32,
    c: f64,
    play_temp: f64,
    rng: &mut R,
) -> (Action, Vec<Value>) {
    let sims = dynamic_sims(base_sims, actions.len());
    let stats = root_child_stats(state, sims, c, rng); // Vec<(Action, visits, q)>

    if stats.is_empty() {
        let a = actions.choose(rng).cloned().unwrap_or(Action::Pass);
        let entry = json!({ "action": action_to_env_dict(state, &a), "prob": 1.0 });
        return (a, vec![entry]);
    }

    // Gewichte für eine Temperatur: visits^(1/temp)·q², mit reinem-Visits-Fallback.
    let weights_for = |t: f64| -> (Vec<f64>, f64) {
        let inv = 1.0 / t.max(1e-6);
        let mut w: Vec<f64> = stats
            .iter()
            .map(|(_, v, q)| (*v as f64).powf(inv) * q.max(1e-6).powi(2))
            .collect();
        let mut s: f64 = w.iter().sum();
        if !(s > 0.0) {
            w = stats.iter().map(|(_, v, _)| (*v as f64).powf(inv)).collect();
            s = w.iter().sum();
        }
        (w, s)
    };

    // TARGET (aufgezeichnet): scharf via TARGET_TEMP → Destillation der besten
    // Heuristik-Züge, damit das Netz eine lernbar-scharfe Policy bekommt.
    let (tw, ts) = weights_for(TARGET_TEMP);
    let policy: Vec<Value> = if ts > 0.0 {
        stats
            .iter()
            .zip(tw.iter())
            .map(|((a, _, _), w)| json!({ "action": action_to_env_dict(state, a), "prob": w / ts }))
            .collect()
    } else {
        vec![json!({ "action": action_to_env_dict(state, &stats[0].0), "prob": 1.0 })]
    };

    // PLAY: moderate Temperatur → gespielte Aktion sampeln (Zustandsvielfalt).
    let (pw, ps) = weights_for(play_temp);
    let idx = if ps > 0.0 { weighted_index(&pw, ps, rng) } else { 0 };
    (stats[idx].0.clone(), policy)
}

/// Sampelt einen Index proportional zu `weights` (Summe = `total`).
fn weighted_index<R: Rng + ?Sized>(weights: &[f64], total: f64, rng: &mut R) -> usize {
    let mut r = rng.random_range(0.0..total.max(f64::MIN_POSITIVE));
    for (i, w) in weights.iter().enumerate() {
        r -= w;
        if r <= 0.0 {
            return i;
        }
    }
    weights.len().saturating_sub(1)
}

// ── Stapel-Zieh-Aufloesung (Aktion A: weiterziehen oder aufhoeren?) ─────────
//
// Regelwerk (Nutzer-Fund): beim Ziehen zeigt die RUECKSEITE nur den TYP der
// Platte (Special vs. Wild, siehe DomeTile::is_special_type) -- die
// Vorderseite (Farbanordnung) sieht man erst, wenn man beschliesst
// aufzuhoeren. Das ist ein echter sequenzieller Stopp-Prozess: Platte
// ziehen (−1 Pkt), Typ pruefen, weiterziehen-oder-aufhoeren entscheiden,
// wiederholen. Erst beim Aufhoeren werden alle gezogenen Platten
// aufgedeckt und eine gewaehlt.
//
// Deshalb ist `Action::DrawStackPeek` jetzt eine ECHTE Engine-Aktion (siehe
// game.rs) statt eines vorab berechneten `num_drawn` -- diese Funktion
// fuehrt den kompletten Vorgang aus (mehrere echte apply_drafting-Aufrufe),
// per Ein-Schritt-Erwartungswert-Vergleich: "aufhoeren" nutzt die exakte
// Bewertung der bereits gezogenen (Front bekannt), "weiterziehen" nur den
// TYP-Durchschnitt ueber den echten Rest-Stapel (Menge bekannt via
// dome_pool_mask-Feature, Reihenfolge nicht -- kein Vorgriff auf konkrete
// Farben ungezogener Karten, sonst waere das kein fairer Spielzug mehr).
// Kein Rollout/Resampling noetig: die Restbestands-TYP-Verteilung ist exakt
// bekannt, nur die Reihenfolge nicht -- der Durchschnitt ueber den echten
// Rest-Pool IST bereits der korrekte Erwartungswert.
//
// Fuer die Heuristik-MCTS (Stufe 1) wird das bewusst NICHT nachgebaut (siehe
// mcts.rs::move_priority) -- nur der Netz-Pfad nutzt diese Funktion.

/// Beste erreichbare Bewertung einer (schon gezogenen) Platte über alle
/// freien Slots × Rotationen: Wertungsplatten-Fortschritt + eigene
/// Bonuspunkte (werden später beim Füllen des Spezialfelds real ausgezahlt)
/// + Wild-Spaces (akzeptieren jede Farbe → Flexibilität, unabhängig davon
/// welche Farbe der Spieler noch braucht). OHNE Punktkosten -- die werden
/// separat als Gesamtzahl gezogener Karten geführt, nicht pro Kandidat.
/// Gibt (Score, slot_row, slot_col, rotation) zurück.
fn best_eval_for_tile(state: &GameState, tile: &crate::dome::DomeTile) -> (f64, usize, usize, u32) {
    let pi = state.current_player;
    let mut best = (f64::NEG_INFINITY, 0usize, 0usize, 0u32);
    for (sr, sc) in state.players[pi].dome_grid.empty_slots() {
        for &rotation in &[0u32, 90, 180, 270] {
            let mut g = Game { state: state.clone() };
            g.state.pending_stack_draw = vec![tile.clone()];
            // Nur diese eine Platte ist "gezogen" -- kein Rest, return_order
            // bleibt leer (triviale einzige gueltige Reihenfolge).
            let mv = DrawFromStackMove {
                chosen_id: tile.tile_id,
                slot_row: sr,
                slot_col: sc,
                rotation,
                return_order: Vec::new(),
            };
            if execute_draw_from_stack(&mut g.state, &mv).is_ok() {
                let progress = wertung_progress(&g.state.players[pi], &g.state.scoring_tile_ids);
                let placed = g.state.players[pi].dome_grid.dome_slots[sr][sc].as_ref();
                let bonus = placed.map_or(0, |t| t.bonus_points) as f64;
                let wild_count = placed.map_or(0, |t| {
                    t.spaces.iter().filter(|s| s.space_type == SpaceType::Wild).count()
                }) as f64;
                let score = progress + bonus + wild_count;
                if score > best.0 {
                    best = (score, sr, sc, rotation);
                }
            }
        }
    }
    best
}

/// Durchschnittlicher TYP-Basiswert (Bonus + Wild-Anzahl) über den echten
/// Rest-Stapel -- das ist alles, was die Rückseite vor dem nächsten Zug
/// verrät (keine Farbanordnung).
fn avg_remaining_type_value(state: &GameState) -> f64 {
    if state.dome_tile_pool.is_empty() {
        return f64::NEG_INFINITY;
    }
    let sum: f64 = state
        .dome_tile_pool
        .iter()
        .map(|t| {
            t.bonus_points as f64
                + t.spaces.iter().filter(|s| s.space_type == SpaceType::Wild).count() as f64
        })
        .sum();
    sum / state.dome_tile_pool.len() as f64
}

/// Führt einen kompletten Stapel-Zug (Aktion A) aus: mind. 1 Pflichtzug,
/// danach per Ein-Schritt-Erwartungswert-Vergleich weiterziehen oder
/// aufhören, abschließend die beste gezogene Platte in den besten Slot legen.
/// Mehrere echte `apply_drafting`-Aufrufe -- der Zug ist erst danach beendet
/// (switch_player passiert im letzten `DrawStack`-Aufruf).
fn resolve_and_apply_stack_draw(game: &mut Game) -> Action {
    let _ = game.apply_drafting(&Action::DrawStackPeek);
    // Terminierung: `can_draw_stack_peek` wird false, sobald
    // `state.dome_tile_pool` leer ist (`validate_draw_stack_peek`,
    // game.rs) -- jeder Redraw entnimmt per `dome_tile_pool.remove(0)`
    // GENAU eine Platte (execute_draw_stack_peek), der Pool schrumpft also
    // strikt monoton und ist von Haus aus endlich (<= 18 Platten). Die
    // Schleife terminiert daher beweisbar von selbst, auch seit R6 die
    // punktbasierte Budget-Schranke entfernt hat (Regelbuch-Audit
    // 2026-07-21: Weiterziehen darf jetzt beliebig oft wiederholt werden).
    // Deckel unten ist reine Gürtel+Hosenträger-Absicherung (Nacht-Hänger
    // 2026-07-22 hat gezeigt, dass "beweisbar endlich" allein keine
    // ausreichende Grundlage mehr ist, siehe fill_large_factory-Fix in
    // state.rs) -- sollte in der Praxis nie greifen.
    const MAX_STACK_PEEKS: u32 = 20;
    let mut peeks: u32 = 0;
    loop {
        let cost_so_far = game.state.pending_stack_draw.len() as f64;
        let stop_value = game
            .state
            .pending_stack_draw
            .iter()
            .map(|t| best_eval_for_tile(&game.state, t).0)
            .fold(f64::NEG_INFINITY, f64::max)
            - cost_so_far;
        if !crate::game::can_draw_stack_peek(&game.state) || peeks >= MAX_STACK_PEEKS {
            break;
        }
        let continue_estimate = avg_remaining_type_value(&game.state) - (cost_so_far + 1.0);
        if continue_estimate <= stop_value {
            break;
        }
        let _ = game.apply_drafting(&Action::DrawStackPeek);
        peeks += 1;
    }

    let (chosen_id, sr, sc, rotation) = game
        .state
        .pending_stack_draw
        .iter()
        .map(|t| {
            let (score, sr, sc, rot) = best_eval_for_tile(&game.state, t);
            (score, t.tile_id, sr, sc, rot)
        })
        .max_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal))
        .map(|(_, id, sr, sc, rot)| (id, sr, sc, rot))
        .expect("pending_stack_draw darf hier nicht leer sein (mind. 1 Pflichtzug oben)");
    // Reihenfolge der Restplatten ist fuer die KI keine gelernte Policy-
    // Dimension (wie moon_order/num_drawn) -- kanonisch die Ziehreihenfolge,
    // wie beim Suchbaum-Pfad (game.rs::generate_draw_stack_moves).
    let return_order: Vec<usize> = game
        .state
        .pending_stack_draw
        .iter()
        .filter(|t| t.tile_id != chosen_id)
        .map(|t| t.tile_id)
        .collect();
    // Baustein B: zwei echte `apply_drafting`-Aufrufe (Stufe 1 Slot, Stufe 2
    // Rotation) statt eines einzelnen `DrawStack` -- die zurückgegebene
    // Aktion ist die Stufe-1-Wahl (traegt chosen_id/slot_row/slot_col, wie
    // von den Aufrufern/Tests unten gelesen), die Rotation ist zu diesem
    // Zeitpunkt bereits angewendet.
    let mv = DrawFromStackMove { chosen_id, slot_row: sr, slot_col: sc, rotation: 0, return_order };
    let final_action = Action::ChooseDrawStackSlot(mv);
    let _ = game.apply_drafting(&final_action);
    let _ = game.apply_drafting(&Action::ChooseDomeRotation(rotation));
    final_action
}

/// Wendet eine gewählte Drafting-Aktion an. Bei `Action::DrawStackPeek`
/// (Start eines Stapel-Zugs) übernimmt `resolve_and_apply_stack_draw` das
/// komplette Peek-Entscheiden-Wählen-Prozedere (mehrere echte
/// `apply_drafting`-Aufrufe) -- der Aufrufer sieht danach den fertig
/// abgeschlossenen Zustand (Zug beendet). Alle anderen Aktionen einmalig
/// normal angewendet. Gibt die TATSÄCHLICH final ausgeführte Aktion zurück
/// (bei DrawStackPeek also das konkrete `DrawStack`, nicht den Peek selbst)
/// -- für Aufrufer, die den echten Zug anzeigen/loggen müssen. Zentraler
/// Einhängepunkt für jede Stelle, die eine gewählte Drafting-Aktion
/// tatsächlich ausführt.
pub(crate) fn apply_chosen_action(game: &mut Game, a: Action) -> Action {
    match a {
        Action::DrawStackPeek => resolve_and_apply_stack_draw(game),
        other => {
            let _ = game.apply_drafting(&other);
            other
        }
    }
}

// ── Moon-Order-Target (Port von self_play.py:194-240) ─────────────────────────

/// Beste Mondreihenfolge der RESTLICHEN Sun-Steine für einen Stein-Zug aus einer
/// kleinen Fabrik (factory_index 0–3). Permutiert die verbleibenden Steine
/// (max. 6 Stichproben), bewertet je Reihenfolge per `solve_round_final_score`
/// und gibt die beste als Farb-Liste zurück. `None` außerhalb des Anwendungsfalls.
fn moon_order_target<R: Rng + ?Sized>(
    state: &GameState,
    a: &Action,
    pi: usize,
    rng: &mut R,
) -> Option<Vec<String>> {
    let m = match a {
        Action::Stone(m) => m,
        _ => return None,
    };
    if m.take.source != TakeSource::SmallFactorySun {
        return None;
    }
    let fid = m.take.factory_id?;
    let factory = state.factories.iter().find(|f| f.factory_id == fid)?;
    let color = m.take.color;
    let remaining: Vec<TileColor> = factory
        .sun_tiles
        .iter()
        .copied()
        .filter(|&t| t != color)
        .collect();
    if remaining.is_empty() {
        return None;
    }

    let mut perms = permutations(&remaining);
    if perms.len() > 6 {
        perms.shuffle(rng);
        perms.truncate(6);
    }

    let row = m.place.row_index;
    let mut best_score = i32::MIN;
    let mut best: Option<Vec<TileColor>> = None;
    for perm in perms {
        let mv = Move {
            take: TakeAction {
                source: TakeSource::SmallFactorySun,
                color,
                factory_id: Some(fid),
                moon_order: perm.clone(),
            },
            place: PlaceAction { row_index: row },
        };
        let mut g = Game { state: state.clone() };
        if g.apply_drafting(&Action::Stone(mv)).is_ok() {
            let score = solve_round_final_score(&g.state, pi);
            if score > best_score {
                best_score = score;
                best = Some(perm);
            }
        }
    }
    best.map(|p| p.iter().map(|t| t.value().to_string()).collect())
}

/// Alle Permutationen (rekursiv; nur für sehr kurze Slices genutzt, ≤ 3 Elemente).
fn permutations<T: Clone>(items: &[T]) -> Vec<Vec<T>> {
    if items.len() <= 1 {
        return vec![items.to_vec()];
    }
    let mut out = Vec::new();
    for i in 0..items.len() {
        let mut rest = items.to_vec();
        let head = rest.remove(i);
        for mut p in permutations(&rest) {
            p.insert(0, head.clone());
            out.push(p);
        }
    }
    out
}

// Baustein B (zweistufiger Kuppel-Suchknoten): das frühere
// `dome_slot_rotation_target` (Klassifikations-Label für `dome_slot_head`/
// `dome_rotation_head`, Baustein A) ist entfallen -- Kachel+Slot (Stufe 1)
// und Rotation (Stufe 2) sind jetzt eigenständige `drafting_step`-Aufrufe
// (siehe `game.rs::PendingDomeChoice`) und bekommen dadurch automatisch je
// einen EIGENEN Policy-Record aus dem normalen Selfplay-Loop, ohne
// Sonderbehandlung.

// ── Startkachel-Heuristik (Port von py.rs::ai_start_tile_json) ────────────────

fn color_index(c: TileColor) -> Option<usize> {
    TileColor::NORMAL.iter().position(|&x| x == c)
}

/// Zählt Sun-Steine je Normalfarbe über alle Fabriken + große Fabrik.
fn sun_color_counts(state: &GameState) -> [usize; 5] {
    let mut counts = [0usize; 5];
    let mut bump = |c: TileColor| {
        if let Some(i) = color_index(c) {
            counts[i] += 1;
        }
    };
    for f in &state.factories {
        for &t in &f.sun_tiles {
            bump(t);
        }
    }
    for &t in &state.large_factory.sun_tiles {
        bump(t);
    }
    counts
}

/// Heuristik-Wahl der Startkuppel für Spieler `pi` (Farb-Häufigkeit + Eckbonus):
/// liefert `(tile_id, slot_row, slot_col, rotation)`. `None`, wenn kein Display
/// oder kein freier Slot. Gemeinsam genutzt von Self-Play und Arena.
pub(crate) fn choose_start_placement(state: &GameState, pi: usize) -> Option<(usize, usize, usize, u32)> {
    if state.dome_display.is_empty() {
        return None;
    }
    let empties = state.players[pi].dome_grid.empty_slots();
    if empties.is_empty() {
        return None;
    }
    let counts = sun_color_counts(state);
    let mut best: Option<(f64, usize, usize, usize, u32)> = None;
    for tile in &state.dome_display {
        for &(r, c) in &empties {
            let corner = if (r == 0 || r == 2) && (c == 0 || c == 2) { 0.5 } else { 0.0 };
            for &rot in &[0u32, 90, 180, 270] {
                let spaces = match tile.rotated_spaces(rot) {
                    Ok(s) => s,
                    Err(_) => continue,
                };
                let mut score = corner;
                for sp in &spaces {
                    score += match sp.space_type {
                        SpaceType::Normal => sp
                            .required_color
                            .and_then(color_index)
                            .map(|i| counts[i] as f64)
                            .unwrap_or(0.0),
                        SpaceType::Wild => *counts.iter().max().unwrap_or(&0) as f64,
                        SpaceType::Special => 0.0,
                    };
                }
                if best.map_or(true, |(b, ..)| score > b) {
                    best = Some((score, tile.tile_id, r, c, rot));
                }
            }
        }
    }
    best.map(|(_, t, r, c, rot)| (t, r, c, rot))
}

// ── Einzelschritte ────────────────────────────────────────────────────────────

/// Startkuppel-Platzierung (nur Runde 1). Platziert per Farb-/Reihen-Heuristik
/// und nimmt einen one-hot-`dome`-Record auf. Nicht-Startspieler legt zuerst
/// (Engine erzwingt das). `player` = `current_player` (= Startspieler), exakt
/// wie der Python-Loop (current_player wechselt erst nach Start-Placement).
fn start_placement_step<R: Rng + ?Sized>(game: &mut Game, _rng: &mut R) -> Option<Map<String, Value>> {
    let recorded_player = game.state.current_player;
    let first = game.state.current_player;
    let non_starter = 1 - first;
    let pi = if game.state.players[non_starter].start_tile_pending {
        non_starter
    } else if game.state.players[first].start_tile_pending {
        first
    } else {
        return None;
    };

    if game.state.dome_display.is_empty() {
        return None;
    }
    let empties = game.state.players[pi].dome_grid.empty_slots();
    if empties.is_empty() {
        return None;
    }

    // Vollständige Aktionsmenge (agent_env: alle Display × Slots × 4 Rotationen).
    let mut valid_actions = Vec::new();
    for (d_idx, _tile) in game.state.dome_display.iter().enumerate() {
        for &(r, c) in &empties {
            for &rot in &[0u32, 90, 180, 270] {
                valid_actions.push(json!({
                    "type": "dome",
                    "display_index": d_idx,
                    "slot_row": r,
                    "slot_col": c,
                    "rotation": rot,
                    "is_start": true,
                }));
            }
        }
    }

    // Heuristik-Wahl (Farb-Häufigkeit + Eckbonus) — gemeinsamer Helfer.
    let (tile_id, r, c, rot) = choose_start_placement(&game.state, pi)?;
    let d_idx = game
        .state
        .dome_display
        .iter()
        .position(|t| t.tile_id == tile_id)
        .unwrap_or(0);

    let state_json = state_to_json(&game.state, true);
    let chosen_env = json!({
        "type": "dome",
        "display_index": d_idx,
        "slot_row": r,
        "slot_col": c,
        "rotation": rot,
        "is_start": true,
    });

    apply_start_placement(&mut game.state, pi, tile_id, r, c, rot).ok()?;

    let mut m = Map::new();
    m.insert("state".into(), state_json);
    m.insert("policy".into(), json!([{ "action": chosen_env, "prob": 1.0 }]));
    m.insert("valid_actions".into(), Value::Array(valid_actions));
    m.insert("moon_order_target".into(), Value::Null);
    m.insert("player".into(), json!(recorded_player));
    Some(m)
}

/// Drafting-Zug per MCTS-Policy. Nimmt den Record auf und wendet den Zug an.
fn drafting_step<R: Rng + ?Sized>(
    game: &mut Game,
    base_sims: u32,
    c: f64,
    rng: &mut R,
) -> Map<String, Value> {
    let player = game.state.current_player;
    let actions = drafting_actions(&game.state);
    let n = actions.len();

    // Aktionsabhängige Temperatur (Port self_play.py:172).
    let temp = if n > 50 { 0.7 } else if n > 15 { 0.4 } else { 0.15 };

    let valid_actions: Vec<Value> =
        actions.iter().map(|a| action_to_env_dict(&game.state, a)).collect();

    let (chosen, policy) = if n == 1 {
        let a = actions[0].clone();
        let entry = json!({ "action": action_to_env_dict(&game.state, &a), "prob": 1.0 });
        (a, vec![entry])
    } else {
        drafting_policy(&game.state, &actions, base_sims, c, temp, rng)
    };

    let moon_t = moon_order_target(&game.state, &chosen, player, rng);
    let state_json = state_to_json(&game.state, true);

    // Zug anwenden (sollte stets gültig sein — aus drafting_actions stammend).
    let _ = game.apply_drafting(&chosen);

    let mut m = Map::new();
    m.insert("state".into(), state_json);
    m.insert("policy".into(), Value::Array(policy));
    m.insert("valid_actions".into(), Value::Array(valid_actions));
    m.insert(
        "moon_order_target".into(),
        moon_t.map(|v| json!(v)).unwrap_or(Value::Null),
    );
    m.insert("player".into(), json!(player));
    m
}

/// Legale Tiling-Aktionen im agent_env-Schema (für `valid_actions` = Trainings-
/// maske): ALLE platzierbaren Steine (jede pending Reihe) + optionale `use_chips`
/// + `end_tiling`. WICHTIG: NICHT auf die oberste Reihe filtern — der DFS-Solver
/// darf jede pending Reihe wählen (Engine erlaubt freie Reihenfolge, bis eine
/// spätere gelegt wird). Ein Top-Reihen-Filter ließe eine vom Solver gewählte
/// Aktion einer anderen Reihe außerhalb der Maske liegen → Policy-Leak →
/// explodierender Policy-Loss im Training.
fn tiling_env_actions(state: &GameState, pi: usize) -> Vec<Value> {
    let mut actions = Vec::new();
    let tiling_actions = generate_tiling_actions(state, pi);
    let has_placements = !tiling_actions.is_empty();

    for a in &tiling_actions {
        actions.push(json!({
            "type": "tiling",
            "player": pi,
            "pattern_row": a.pattern_row,
            "slot_row": a.slot_row,
            "slot_col": a.slot_col,
            "space_index": a.space_index,
        }));
    }

    // Chip-Komplettierung: der DFS-Solver kann Chips auch bei noch offenen
    // Platzierungen wählen — daher stets als legale Aktion mitführen (Maske).
    let player = &state.players[pi];
    let tiled_max = player.tiled_max_row;
    for (ri, row) in player.pattern_lines.iter().enumerate() {
        if row.is_complete() || (ri as i32) < tiled_max {
            continue;
        }
        if !can_complete_row_with_chips(player, ri) {
            continue;
        }
        let color = match row.color {
            Some(c) => c,
            None => continue,
        };
        if row_has_open_matching_slot(player, ri, color) {
            actions.push(json!({ "type": "use_chips", "player": pi, "pattern_row": ri }));
        }
    }

    // end_tiling nur, wenn keine zwingende Platzierung offen ist (Engine-Regel).
    if !has_placements {
        actions.push(json!({ "type": "end_tiling" }));
    }
    actions
}

/// Optimaler Tiling-Schritt: reiner exakter DFS-Solver. Während des Tilings
/// werden keine neuen Kuppelplatten gelegt (Regel) -- eine volle Musterreihe
/// ohne bereits belegten passenden Slot bleibt liegen (ggf. später per
/// Strafleiste abgerechnet, siehe `process_unplaceable_rows`), statt am
/// Tiling-Ende künstlich eine neue Platte zu installieren. Gemeinsam genutzt
/// von Self-Play und Arena.
fn resolve_tiling_step(state: &GameState, pi: usize) -> TilingStep {
    best_first_step_exact(state, pi)
}

/// Tiling-Zug per exaktem DFS-Solver (one-hot Policy auf den optimalen Schritt).
fn tiling_step<R: Rng + ?Sized>(game: &mut Game, rng: &mut R) -> Map<String, Value> {
    let pi = game.state.current_player;
    let state_json = state_to_json(&game.state, true);
    let valid_actions = tiling_env_actions(&game.state, pi);
    let step = resolve_tiling_step(&game.state, pi);

    let chosen_env: Value = match &step {
        TilingStep::Place(ta) => json!({
            "type": "tiling",
            "player": pi,
            "pattern_row": ta.pattern_row,
            "slot_row": ta.slot_row,
            "slot_col": ta.slot_col,
            "space_index": ta.space_index,
        }),
        TilingStep::Chips { row, .. } => {
            json!({ "type": "use_chips", "player": pi, "pattern_row": row })
        }
        TilingStep::End => json!({ "type": "end_tiling" }),
    };

    match &step {
        TilingStep::Place(ta) => {
            let _ = game.apply_single_tiling(pi, ta);
        }
        TilingStep::Chips { row, chips } => {
            apply_bonus_chips_with(&mut game.state.players[pi], *row, chips);
        }
        TilingStep::End => {
            let _ = game.apply_tiling(&TilingMove::EndTiling { player: pi }, rng);
        }
    }

    let mut m = Map::new();
    m.insert("state".into(), state_json);
    m.insert("policy".into(), json!([{ "action": chosen_env, "prob": 1.0 }]));
    m.insert("valid_actions".into(), Value::Array(valid_actions));
    m.insert("moon_order_target".into(), Value::Null);
    m.insert("player".into(), json!(pi));
    m
}

// ── Spiel-Loop ────────────────────────────────────────────────────────────────

/// Spielt EINE komplette Partie und gibt die Trainings-Records zurück.
/// `net`: `None` = ursprüngliches Verhalten (rein heuristische Partie, keine
/// `round_transition_value`-Labels -- alle bestehenden Aufrufstellen
/// unverändert). `Some(net)`: die Partie wird WEITERHIN komplett von der
/// Heuristik entschieden (`drafting_step`/`tiling_step` unverändert), aber
/// zusätzlich werden die Rundenübergänge per `sample_round_transition_for_round`
/// (Netz-Chance-Node-Sampling, siehe `round_transition.rs`/
/// `round_transition_deep.rs`) gelabelt -- lässt den Value-Head über die
/// GESAMTE bestehende Heuristik-Self-Play-Menge hinweg vom rauschärmeren
/// Ziel profitieren, ohne dass das Netz je eine Spielentscheidung trifft
/// (kein Vertrauen in dessen aktuelle Suchqualität nötig).
pub fn play_one_game<R: Rng + ?Sized>(
    base_sims: u32,
    c: f64,
    scoring_ids: Vec<usize>,
    names: [String; 2],
    first_player: usize,
    game_id: &str,
    rng: &mut R,
    net: Option<&Net>,
    move_heartbeat: Option<&AtomicU64>,
) -> Vec<Value> {
    let mut game = Game::start(names, first_player, scoring_ids, rng);
    let mut records: Vec<Map<String, Value>> = Vec::new();
    let mut round_transition_values: std::collections::HashMap<u32, [f64; 2]> = std::collections::HashMap::new();
    // Punkt 6 (`evaluations/value head tests.txt`): TD-Bootstrap-Ziel
    // zusätzlich zum vollen `round_transition_value` (das bis zum echten
    // Spielende rekursiert und damit dieselbe niedrige Runde-1-Decke hat
    // wie das Endergebnis, siehe Noise-Floor-Befund).
    let mut bootstrap_values: std::collections::HashMap<u32, [f64; 2]> = std::collections::HashMap::new();

    let mut guard = 0u32;
    let t_start = std::time::Instant::now();
    // `+ EXTRA_GAME_TIMEOUT_SECS` nur wenn `net` aktiv ist -- dieselbe
    // Bugfix-Logik wie in `play_net_self_play_game` (siehe dortiger
    // Kommentar): ohne den Zuschlag schneidet der Hänger-Schutz Partien vor
    // Rundenende ab, sobald das zusätzliche Sampling nennenswert Zeit kostet.
    let timeout_secs = heuristic_game_timeout_secs(base_sims)
        + if net.is_some() { crate::round_transition_deep::EXTRA_GAME_TIMEOUT_SECS } else { 0 };
    loop {
        guard += 1;
        if let Some(hb) = move_heartbeat {
            hb.fetch_add(1, Ordering::Relaxed);
        }
        if guard > 100_000 || t_start.elapsed().as_secs() >= timeout_secs {
            break; // defensive Endlosschleifen-Sicherung
        }
        match game.state.phase {
            Phase::StartPlacement | Phase::Drafting => {
                if game.state.players.iter().any(|p| p.start_tile_pending) {
                    match start_placement_step(&mut game, rng) {
                        Some(rec) => records.push(rec),
                        None => break,
                    }
                } else if game.state.phase == Phase::Drafting {
                    let round_before = game.state.round_number;
                    records.push(drafting_step(&mut game, base_sims, c, rng));
                    if let Some(net) = net {
                        if game.state.phase == Phase::Tiling && round_before < crate::state::NUM_ROUNDS {
                            // Gleiche Rundenende-vs-Spielende-Unterscheidung wie
                            // in `play_net_self_play_game` (siehe dortiger
                            // Kommentar) -- `round_before < NUM_ROUNDS` filtert
                            // den bedeutungslosen Runde-5-Fall.
                            if let Some(pre) = crate::round_transition::resolve_to_pre_chance(&game.state) {
                                let v = sample_round_transition_for_round(round_before, &pre, net, rng);
                                round_transition_values.insert(round_before, v);
                                let bv = crate::round_transition_deep::bootstrap_value_after_rounds(
                                    &pre,
                                    net,
                                    crate::round_transition_deep::BOOTSTRAP_HORIZON_ROUNDS,
                                    rng,
                                );
                                bootstrap_values.insert(round_before, bv);
                            }
                        }
                    }
                } else {
                    break;
                }
            }
            Phase::Tiling => records.push(tiling_step(&mut game, rng)),
            _ => break, // Scoring/End/Final → Partie vorbei
        }
    }

    // Endwertung anwenden, damit Scores die Wertungsplatten enthalten.
    let completed = game.state.phase == Phase::End;
    if completed {
        let _ = game.apply_end_scoring();
    }
    let scores = [game.state.players[0].score, game.state.players[1].score];
    let scores_unclamped = [
        game.state.players[0].score_unclamped,
        game.state.players[1].score_unclamped,
    ];
    let winner = determine_winner(&game.state);

    records
        .into_iter()
        .map(|mut m| {
            m.insert("game_id".into(), json!(game_id));
            m.insert("scores".into(), json!(scores));
            m.insert("scores_unclamped".into(), json!(scores_unclamped));
            m.insert("winner".into(), json!(winner));
            // Erreicht die Partie regulär Phase::End (nicht durch Haenger-Schutz
            // abgebrochen)? Nur dann sind scores/winner ein echtes Endergebnis
            // (inkl. Wertungsplatten). Downstream (self_play.py) prüft das je Datei.
            m.insert("completed".into(), json!(completed));
            // Nur vorhanden, wenn `net` übergeben wurde UND dieser Schritts
            // Runde tatsächlich einen Übergang erreicht hat -- siehe
            // `play_net_self_play_game`s identisches Stempel-Muster.
            let round = m.get("state").and_then(|s| s.get("round")).and_then(|r| r.as_u64());
            if let Some(v) = round.and_then(|r| round_transition_values.get(&(r as u32))) {
                m.insert("round_transition_value".into(), json!(v));
            }
            if let Some(v) = round.and_then(|r| bootstrap_values.get(&(r as u32))) {
                m.insert("bootstrap_value".into(), json!(v));
            }
            Value::Object(m)
        })
        .collect()
}

/// Spielt `n_games` Partien (rayon-parallel) und gibt ALLE Step-Records flach als
/// JSON-Array-String zurück. Je Spiel ein deterministisch aus `seed` abgeleiteter
/// RNG, zufälliger Startspieler und konfliktfreie Wertungsplatten.
/// `progress_path`/`heartbeat_path` (Task #71, Einzelspiel-Flush + Heartbeat,
/// siehe Modul-Kommentar dort): beide optional, `None` = Verhalten exakt wie
/// vorher (kein Fortschritts-Tracking).
pub fn run_self_play(
    n_games: usize,
    base_sims: u32,
    c: f64,
    seed: u64,
    num_threads: usize,
    prefix: &str,
    progress_path: Option<&str>,
    heartbeat_path: Option<&str>,
) -> String {
    let progress_file = open_progress_file(progress_path);
    let move_counter = Arc::new(AtomicU64::new(0));
    let games_counter = Arc::new(AtomicU64::new(0));
    let (hb_stop, hb_handle) = start_heartbeat_reporter(
        heartbeat_path.map(String::from),
        Arc::clone(&move_counter),
        Arc::clone(&games_counter),
    );

    let play = |i: usize| -> Vec<Value> {
        let mut rng = StdRng::seed_from_u64(seed.wrapping_add((i as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15)));
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let first = rng.random_range(0..2usize);
        let names = ["Spieler 1".to_string(), "Spieler 2".to_string()];
        let gid = format!("{prefix}_g{}", i + 1);
        let steps = play_one_game(base_sims, c, ids, names, first, &gid, &mut rng, None, Some(&move_counter));
        if !steps.is_empty() {
            games_counter.fetch_add(1, Ordering::Relaxed);
            append_game_progress(&progress_file, &steps);
        }
        steps
    };

    // num_threads == 0 → globaler rayon-Pool (alle Kerne); sonst dedizierter Pool.
    let all: Vec<Vec<Value>> = if num_threads == 0 {
        (0..n_games).into_par_iter().map(play).collect()
    } else {
        match rayon::ThreadPoolBuilder::new().num_threads(num_threads).build() {
            Ok(pool) => pool.install(|| (0..n_games).into_par_iter().map(play).collect()),
            Err(_) => (0..n_games).map(play).collect(), // Fallback: seriell
        }
    };
    stop_heartbeat_reporter(hb_stop, hb_handle);

    let flat: Vec<Value> = all.into_iter().flatten().collect();
    serde_json::to_string(&Value::Array(flat)).unwrap_or_else(|_| "[]".to_string())
}

/// Wie `run_self_play`, aber zusätzlich mit `round_transition_value`-Labels
/// aus einem geladenen Netz (siehe `play_one_game`s `net`-Parameter) --
/// Spielentscheidungen bleiben VOLLSTÄNDIG heuristisch, nur die
/// Rundenübergänge werden zusätzlich per Netz-Chance-Node-Sampling bewertet.
/// Lädt das Netz EINMAL (wie `run_net_arena_match`), `Arc`-geteilt über alle
/// Rayon-Threads.
/// `progress_path`/`heartbeat_path`: siehe `run_self_play`-Dokumentation (Task #71).
#[allow(clippy::too_many_arguments)]
pub fn run_self_play_with_net_labels(
    model_path: &str,
    n_games: usize,
    base_sims: u32,
    c: f64,
    seed: u64,
    num_threads: usize,
    prefix: &str,
    progress_path: Option<&str>,
    heartbeat_path: Option<&str>,
) -> Result<String, String> {
    let net = Net::load(model_path, crate::features::INPUT_SIZE).map_err(|e| e.to_string())?;
    let net = std::sync::Arc::new(net);
    let progress_file = open_progress_file(progress_path);
    let move_counter = Arc::new(AtomicU64::new(0));
    let games_counter = Arc::new(AtomicU64::new(0));
    let (hb_stop, hb_handle) = start_heartbeat_reporter(
        heartbeat_path.map(String::from),
        Arc::clone(&move_counter),
        Arc::clone(&games_counter),
    );

    let play = |i: usize| -> Vec<Value> {
        let mut rng = StdRng::seed_from_u64(seed.wrapping_add((i as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15)));
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let first = rng.random_range(0..2usize);
        let names = ["Spieler 1".to_string(), "Spieler 2".to_string()];
        let gid = format!("{prefix}_g{}", i + 1);
        let steps = play_one_game(base_sims, c, ids, names, first, &gid, &mut rng, Some(&net), Some(&move_counter));
        if !steps.is_empty() {
            games_counter.fetch_add(1, Ordering::Relaxed);
            append_game_progress(&progress_file, &steps);
        }
        steps
    };

    let all: Vec<Vec<Value>> = if num_threads == 0 {
        (0..n_games).into_par_iter().map(play).collect()
    } else {
        match rayon::ThreadPoolBuilder::new().num_threads(num_threads).build() {
            Ok(pool) => pool.install(|| (0..n_games).into_par_iter().map(play).collect()),
            Err(_) => (0..n_games).map(play).collect(),
        }
    };
    stop_heartbeat_reporter(hb_stop, hb_handle);

    let flat: Vec<Value> = all.into_iter().flatten().collect();
    Ok(serde_json::to_string(&Value::Array(flat)).unwrap_or_else(|_| "[]".to_string()))
}

// ── Arena (Agent-vs-Agent-Turnier) ───────────────────────────────────────────

/// Spielt EIN Arena-Spiel zwischen zwei Heuristik-MCTS-Konfigurationen.
/// Brett 0 sucht mit `sims[0]` Basis-Simulationen, Brett 1 mit `sims[1]`.
/// Jeder Agent spielt seinen BESTEN Zug (argmax-Visits, keine Temperatur, keine
/// Datenaufzeichnung). Liefert `{scores, winner, steps, total_floor,
/// floor_per_round}`.
fn play_arena_game<R: Rng + ?Sized>(
    sims: [u32; 2],
    c: f64,
    scoring_ids: Vec<usize>,
    names: [String; 2],
    first_player: usize,
    rng: &mut R,
) -> Value {
    let mut game = Game::start(names, first_player, scoring_ids, rng);
    let mut steps = 0u32;
    let mut guard = 0u32;
    let t_start = std::time::Instant::now();
    let timeout_secs = heuristic_game_timeout_secs(sims[0].max(sims[1]));
    loop {
        guard += 1;
        // Hänger-Schutz: Schritt-Limit ODER sims-skalierte Wall-Clock je Partie.
        // Bricht pathologische Nicht-Terminierungen ab (eine teure Netz-Suche pro
        // Schritt würde sonst stundenlang grinden), statt den ganzen Lauf zu blockieren.
        if guard > 100_000 || t_start.elapsed().as_secs() >= timeout_secs {
            break;
        }
        match game.state.phase {
            Phase::StartPlacement | Phase::Drafting => {
                if game.state.players.iter().any(|p| p.start_tile_pending) {
                    let first = game.state.current_player;
                    let non_starter = 1 - first;
                    let pi = if game.state.players[non_starter].start_tile_pending {
                        non_starter
                    } else if game.state.players[first].start_tile_pending {
                        first
                    } else {
                        break;
                    };
                    match choose_start_placement(&game.state, pi) {
                        Some((tid, r, c2, rot)) => {
                            let _ = apply_start_placement(&mut game.state, pi, tid, r, c2, rot);
                        }
                        None => break,
                    }
                    steps += 1;
                } else if game.state.phase == Phase::Drafting {
                    let pi = game.state.current_player;
                    let actions = drafting_actions(&game.state);
                    let chosen = if actions.len() == 1 {
                        actions[0].clone()
                    } else {
                        let s = dynamic_sims(sims[pi], actions.len());
                        search_drafting_action(&game.state, s, c, rng)
                            .unwrap_or_else(|| actions[0].clone())
                    };
                    let _ = game.apply_drafting(&chosen);
                    steps += 1;
                } else {
                    break;
                }
            }
            Phase::Tiling => {
                let pi = game.state.current_player;
                match resolve_tiling_step(&game.state, pi) {
                    TilingStep::Place(ta) => {
                        let _ = game.apply_single_tiling(pi, &ta);
                    }
                    TilingStep::Chips { row, chips } => {
                        apply_bonus_chips_with(&mut game.state.players[pi], row, &chips);
                    }
                    TilingStep::End => {
                        let _ = game.apply_tiling(&TilingMove::EndTiling { player: pi }, rng);
                    }
                }
                steps += 1;
            }
            _ => break,
        }
    }
    if game.state.phase == Phase::End {
        let _ = game.apply_end_scoring();
    }
    let p0 = &game.state.players[0];
    let p1 = &game.state.players[1];
    json!({
        "scores": [p0.score, p1.score],
        "scores_unclamped": [p0.score_unclamped, p1.score_unclamped],
        "winner": determine_winner(&game.state),
        "steps": steps,
        "total_floor": [p0.total_floor_penalties, p1.total_floor_penalties],
        "floor_per_round": [p0.floor_penalties_per_round, p1.floor_penalties_per_round],
    })
}

/// Spielt `n_games` Arena-Partien (rayon-parallel) zwischen zwei MCTS-Konfigs.
/// Brett 0 = Agent A (`sims_a`), Brett 1 = Agent B (`sims_b`). Spiel `i` hat den
/// Startspieler alternierend (`i % 2`), um den Startspieler-Vorteil auszugleichen.
/// Gibt ein geordnetes JSON-Array der Spielergebnisse zurück (Elo rechnet Python).
pub fn run_arena_match(
    sims_a: u32,
    sims_b: u32,
    n_games: usize,
    seed: u64,
    num_threads: usize,
    c: f64,
) -> String {
    let play = |i: usize| -> Value {
        let mut rng =
            StdRng::seed_from_u64(seed.wrapping_add((i as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15)));
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let first = i % 2;
        let names = ["A".to_string(), "B".to_string()];
        play_arena_game([sims_a, sims_b], c, ids, names, first, &mut rng)
    };

    let all: Vec<Value> = if num_threads == 0 {
        (0..n_games).into_par_iter().map(play).collect()
    } else {
        match rayon::ThreadPoolBuilder::new().num_threads(num_threads).build() {
            Ok(pool) => pool.install(|| (0..n_games).into_par_iter().map(play).collect()),
            Err(_) => (0..n_games).map(play).collect(),
        }
    };
    serde_json::to_string(&Value::Array(all)).unwrap_or_else(|_| "[]".to_string())
}

// ── Netz vs. Heuristik (Arena-Messung) ───────────────────────────────────────

/// Spielt EIN Spiel: Brett `net_board` zieht per Netz-PUCT, das andere per
/// Heuristik-MCTS. Tiling/Start für BEIDE per Solver/Heuristik (wie Arena).
#[allow(clippy::too_many_arguments)]
fn play_net_game<R: Rng + ?Sized>(
    net: &Net,
    net_board: usize,
    net_sims: u32,
    heur_sims: u32,
    c: f64,
    c_puct: f64,
    scoring_ids: Vec<usize>,
    names: [String; 2],
    first_player: usize,
    rng: &mut R,
) -> Value {
    let mut game = Game::start(names, first_player, scoring_ids, rng);
    let mut steps = 0u32;
    let mut guard = 0u32;
    let t_start = std::time::Instant::now();
    let timeout_secs = net_game_timeout_secs(net_sims.max(heur_sims));
    loop {
        guard += 1;
        // Hänger-Schutz: Schritt-Limit ODER sims-skalierte Wall-Clock je Partie.
        // Bricht pathologische Nicht-Terminierungen ab (eine teure Netz-Suche pro
        // Schritt würde sonst stundenlang grinden), statt den ganzen Lauf zu blockieren.
        if guard > 100_000 || t_start.elapsed().as_secs() >= timeout_secs {
            break;
        }
        match game.state.phase {
            Phase::StartPlacement | Phase::Drafting => {
                if game.state.players.iter().any(|p| p.start_tile_pending) {
                    let first = game.state.current_player;
                    let non_starter = 1 - first;
                    let pi = if game.state.players[non_starter].start_tile_pending {
                        non_starter
                    } else if game.state.players[first].start_tile_pending {
                        first
                    } else {
                        break;
                    };
                    match choose_start_placement(&game.state, pi) {
                        Some((tid, r, c2, rot)) => {
                            let _ = apply_start_placement(&mut game.state, pi, tid, r, c2, rot);
                        }
                        None => break,
                    }
                    steps += 1;
                } else if game.state.phase == Phase::Drafting {
                    let pi = game.state.current_player;
                    let actions = drafting_actions(&game.state);
                    let chosen = if actions.len() == 1 {
                        actions[0].clone()
                    } else if pi == net_board {
                        let s = net_effective_sims(net_sims, actions.len());
                        net_search_drafting_action(net, &game.state, s, c_puct, false, rng)
                            .unwrap_or_else(|| actions[0].clone())
                    } else {
                        let s = dynamic_sims(heur_sims, actions.len());
                        search_drafting_action(&game.state, s, c, rng)
                            .unwrap_or_else(|| actions[0].clone())
                    };
                    // Sequenzielle Stapel-Zieh-Aufloesung nur fuer den Netz-Spieler
                    // (siehe apply_chosen_action) -- die Heuristik-Seite braucht das
                    // laut Nutzer-Vorgabe nicht, dort reicht die normale Einzelaktion,
                    // Folge-Entscheidungen (weiterziehen/waehlen) kommen automatisch
                    // ueber den naechsten Schleifendurchlauf.
                    if pi == net_board {
                        apply_chosen_action(&mut game, chosen);
                    } else {
                        let _ = game.apply_drafting(&chosen);
                    }
                    steps += 1;
                } else {
                    break;
                }
            }
            Phase::Tiling => {
                let pi = game.state.current_player;
                match resolve_tiling_step(&game.state, pi) {
                    TilingStep::Place(ta) => {
                        let _ = game.apply_single_tiling(pi, &ta);
                    }
                    TilingStep::Chips { row, chips } => {
                        apply_bonus_chips_with(&mut game.state.players[pi], row, &chips);
                    }
                    TilingStep::End => {
                        let _ = game.apply_tiling(&TilingMove::EndTiling { player: pi }, rng);
                    }
                }
                steps += 1;
            }
            _ => break,
        }
    }
    if game.state.phase == Phase::End {
        let _ = game.apply_end_scoring();
    }
    let p0 = &game.state.players[0];
    let p1 = &game.state.players[1];
    json!({
        "scores": [p0.score, p1.score],
        "scores_unclamped": [p0.score_unclamped, p1.score_unclamped],
        "winner": determine_winner(&game.state),
        "steps": steps,
        "net_board": net_board,
        "total_floor": [p0.total_floor_penalties, p1.total_floor_penalties],
        "floor_per_round": [p0.floor_penalties_per_round, p1.floor_penalties_per_round],
    })
}

/// `n_games` Spiele Netz vs. Heuristik (Netz auf Brett 0, Startspieler alternierend).
/// Lädt das ONNX-Netz einmal. Gibt JSON-Array `[{scores:[netz,heur], winner, …}]`.
#[allow(clippy::too_many_arguments)]
pub fn run_net_arena_match(
    model_path: &str,
    net_sims: u32,
    heur_sims: u32,
    n_games: usize,
    seed: u64,
    num_threads: usize,
    c: f64,
    c_puct: f64,
) -> Result<String, String> {
    let net = Net::load(model_path, crate::features::INPUT_SIZE).map_err(|e| e.to_string())?;
    let net = std::sync::Arc::new(net);

    let play = |i: usize| -> Value {
        let mut rng =
            StdRng::seed_from_u64(seed.wrapping_add((i as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15)));
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let first = i % 2;
        let names = ["Netz".to_string(), "Heuristik".to_string()];
        play_net_game(&net, 0, net_sims, heur_sims, c, c_puct, ids, names, first, &mut rng)
    };

    let all: Vec<Value> = if num_threads <= 1 {
        (0..n_games).map(play).collect()
    } else {
        match rayon::ThreadPoolBuilder::new().num_threads(num_threads).build() {
            Ok(pool) => pool.install(|| (0..n_games).into_par_iter().map(play).collect()),
            Err(_) => (0..n_games).map(play).collect(),
        }
    };
    Ok(serde_json::to_string(&Value::Array(all)).unwrap_or_else(|_| "[]".to_string()))
}

// ── Netz vs. Netz (Generationen-Vergleich) ───────────────────────────────────

/// Spielt EIN Spiel Netz A (Brett 0) vs. Netz B (Brett 1). Beide ziehen per
/// Netz-PUCT mit eigenem Netz/Sims; Tiling/Start für beide per Solver.
#[allow(clippy::too_many_arguments)]
fn play_net_vs_net_game<R: Rng + ?Sized>(
    net_a: &Net,
    net_b: &Net,
    sims_a: u32,
    sims_b: u32,
    c_puct_a: f64,
    c_puct_b: f64,
    scoring_ids: Vec<usize>,
    names: [String; 2],
    first_player: usize,
    rng: &mut R,
) -> Value {
    let mut game = Game::start(names, first_player, scoring_ids, rng);
    let mut steps = 0u32;
    let mut guard = 0u32;
    let t_start = std::time::Instant::now();
    let timeout_secs = net_game_timeout_secs(sims_a.max(sims_b));
    loop {
        guard += 1;
        // Hänger-Schutz: Schritt-Limit ODER sims-skalierte Wall-Clock je Partie.
        // Bricht pathologische Nicht-Terminierungen ab (eine teure Netz-Suche pro
        // Schritt würde sonst stundenlang grinden), statt den ganzen Lauf zu blockieren.
        if guard > 100_000 || t_start.elapsed().as_secs() >= timeout_secs {
            break;
        }
        match game.state.phase {
            Phase::StartPlacement | Phase::Drafting => {
                if game.state.players.iter().any(|p| p.start_tile_pending) {
                    let first = game.state.current_player;
                    let non_starter = 1 - first;
                    let pi = if game.state.players[non_starter].start_tile_pending {
                        non_starter
                    } else if game.state.players[first].start_tile_pending {
                        first
                    } else {
                        break;
                    };
                    match choose_start_placement(&game.state, pi) {
                        Some((tid, r, c2, rot)) => {
                            let _ = apply_start_placement(&mut game.state, pi, tid, r, c2, rot);
                        }
                        None => break,
                    }
                    steps += 1;
                } else if game.state.phase == Phase::Drafting {
                    let pi = game.state.current_player;
                    let actions = drafting_actions(&game.state);
                    let chosen = if actions.len() == 1 {
                        actions[0].clone()
                    } else {
                        let (net, base, cp) = if pi == 0 {
                            (net_a, sims_a, c_puct_a)
                        } else {
                            (net_b, sims_b, c_puct_b)
                        };
                        let s = net_effective_sims(base, actions.len());
                        net_search_drafting_action(net, &game.state, s, cp, false, rng)
                            .unwrap_or_else(|| actions[0].clone())
                    };
                    apply_chosen_action(&mut game, chosen);
                    steps += 1;
                } else {
                    break;
                }
            }
            Phase::Tiling => {
                let pi = game.state.current_player;
                match resolve_tiling_step(&game.state, pi) {
                    TilingStep::Place(ta) => {
                        let _ = game.apply_single_tiling(pi, &ta);
                    }
                    TilingStep::Chips { row, chips } => {
                        apply_bonus_chips_with(&mut game.state.players[pi], row, &chips);
                    }
                    TilingStep::End => {
                        let _ = game.apply_tiling(&TilingMove::EndTiling { player: pi }, rng);
                    }
                }
                steps += 1;
            }
            _ => break,
        }
    }
    if game.state.phase == Phase::End {
        let _ = game.apply_end_scoring();
    }
    let p0 = &game.state.players[0];
    let p1 = &game.state.players[1];
    json!({
        "scores": [p0.score, p1.score],
        "scores_unclamped": [p0.score_unclamped, p1.score_unclamped],
        "winner": determine_winner(&game.state),
        "steps": steps,
        "total_floor": [p0.total_floor_penalties, p1.total_floor_penalties],
        "floor_per_round": [p0.floor_penalties_per_round, p1.floor_penalties_per_round],
    })
}

/// `n_games` Spiele Netz A (Brett 0) vs. Netz B (Brett 1), Startspieler
/// alternierend. Lädt beide ONNX-Netze einmal. Gibt JSON-Array
/// `[{scores:[A,B], winner, …}]`.
pub fn run_net_vs_net_arena(
    model_a: &str,
    model_b: &str,
    sims_a: u32,
    sims_b: u32,
    n_games: usize,
    seed: u64,
    num_threads: usize,
    c_puct_a: f64,
    c_puct_b: f64,
) -> Result<String, String> {
    let net_a = std::sync::Arc::new(Net::load(model_a, crate::features::INPUT_SIZE).map_err(|e| e.to_string())?);
    let net_b = std::sync::Arc::new(Net::load(model_b, crate::features::INPUT_SIZE).map_err(|e| e.to_string())?);

    let play = |i: usize| -> Value {
        let mut rng =
            StdRng::seed_from_u64(seed.wrapping_add((i as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15)));
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let first = i % 2;
        let names = ["NetzA".to_string(), "NetzB".to_string()];
        play_net_vs_net_game(&net_a, &net_b, sims_a, sims_b, c_puct_a, c_puct_b, ids, names, first, &mut rng)
    };

    let all: Vec<Value> = if num_threads <= 1 {
        (0..n_games).map(play).collect()
    } else {
        match rayon::ThreadPoolBuilder::new().num_threads(num_threads).build() {
            Ok(pool) => pool.install(|| (0..n_games).into_par_iter().map(play).collect()),
            Err(_) => (0..n_games).map(play).collect(),
        }
    };
    Ok(serde_json::to_string(&Value::Array(all)).unwrap_or_else(|_| "[]".to_string()))
}

// ── Netzgeführtes Self-Play (AlphaZero-Loop, Stufe 1/2) ──────────────────────

/// Drafting-Policy aus der Netz-Suche: Trainingsziel = Gumbels completed-Q-
/// Softmax `π'(a) = softmax(ln(prior(a)) + σ(completedQ(a)))` über ALLE
/// Wurzelkandidaten (`net_mcts::net_root_child_stats_and_policy`, ersetzt
/// die vorherige rohe Visit-Verteilung N/ΣN, siehe STATUS.md "Gumbel
/// AlphaZero", Punkt 4 -- unbesuchte Kandidaten tragen jetzt via `v_mix`
/// echte Wahrscheinlichkeitsmasse statt Null). Die tatsächlich GESPIELTE
/// Aktion bleibt bewusst UNVERÄNDERT besuchsbasiert (τ=1, Sampling; plus
/// Dirichlet-Wurzel-Noise im PUCT-Legacy-Pfad) -- AUSSER
/// `deterministic=true`: dann wird wie in der Arena immer der meistbesuchte
/// Zug gespielt. Nur das aufgezeichnete Policy-Ziel ändert sich, nicht die
/// Selbstspiel-Trajektorie/Explorationsvielfalt.
fn net_drafting_policy<R: Rng + ?Sized>(
    net: &Net,
    state: &GameState,
    actions: &[Action],
    base_sims: u32,
    c_puct: f64,
    rng: &mut R,
    add_root_noise: bool,
    deterministic: bool,
) -> (Action, Vec<Value>) {
    let sims = net_effective_sims(base_sims, actions.len());
    let (stats, completed_q_policy) =
        crate::net_mcts::net_root_child_stats_and_policy(net, state, sims, c_puct, add_root_noise, rng);
    let total: f64 = stats.iter().map(|(_, v, _)| *v as f64).sum();
    if stats.is_empty() || !(total > 0.0) {
        let a = actions.choose(rng).cloned().unwrap_or(Action::Pass);
        return (a.clone(), vec![json!({ "action": action_to_env_dict(state, &a), "prob": 1.0 })]);
    }
    let policy: Vec<Value> = completed_q_policy
        .iter()
        .map(|(a, p)| json!({ "action": action_to_env_dict(state, a), "prob": p }))
        .collect();
    let idx = if deterministic {
        // Fund 2 (B2, Vollaudit 2026-07-21): Tie-Break visits, dann Q --
        // gleiches Muster wie net_mcts::best_root_child. Nacktes
        // max_by(visits) ließe bei Gleichstand den LETZTEN Eintrag
        // (= niedrigster Prior) gewinnen.
        stats
            .iter()
            .enumerate()
            .max_by(|(_, (_, v1, q1)), (_, (_, v2, q2))| {
                v1.cmp(v2).then(q1.partial_cmp(q2).unwrap_or(std::cmp::Ordering::Equal))
            })
            .map(|(i, _)| i)
            .unwrap_or(0)
    } else {
        let weights: Vec<f64> = stats.iter().map(|(_, v, _)| *v as f64).collect();
        weighted_index(&weights, total, rng)
    };
    (stats[idx].0.clone(), policy)
}

/// Bewertet den Rundenübergang `round_before -> round_before+1` per
/// mehrstufigem Chance-Node-Sampling (siehe `round_transition.rs`/
/// `round_transition_deep.rs`) -- gemeinsame Logik für `play_net_self_play_game`
/// (Netz entscheidet UND bewertet) und `play_one_game` (Heuristik entscheidet,
/// Netz bewertet NUR die Übergänge zusätzlich, siehe dortiger Aufruf).
/// Runde 4->5: exakter Freebie (`round5::exact_round5_outcome`, kein Netz-
/// Rauschen). Runde 1-3: rekursive `continue_through_round{2,3,4}`-Ketten aus
/// `round_transition_deep.rs`, additive (nicht kombinatorische) Kosten.
fn sample_round_transition_for_round<R: Rng + ?Sized>(
    round_before: u32,
    pre: &crate::round_transition::PreChanceState,
    net: &Net,
    rng: &mut R,
) -> [f64; 2] {
    use crate::round_transition_deep as rtd;
    match round_before {
        r if r == crate::state::NUM_ROUNDS - 1 => {
            let deadline = std::time::Instant::now() + crate::round_transition::TIME_BUDGET_TRAIN_ROUND4;
            crate::round_transition::sample_round_transition_value(
                pre,
                crate::round_transition::N_SAMPLES_TRAIN,
                |s, _rng| crate::round5::exact_round5_outcome(s),
                rng,
                deadline,
            )
        }
        3 => {
            let deadline = std::time::Instant::now() + rtd::TIME_BUDGET_TRAIN_ROUND3;
            crate::round_transition::sample_round_transition_value(
                pre,
                rtd::N_SAMPLES_TRAIN_ROUND3,
                |s, rng| rtd::continue_through_round4(net, s, rng),
                rng,
                deadline,
            )
        }
        2 => {
            let deadline = std::time::Instant::now() + rtd::TIME_BUDGET_TRAIN_ROUND2;
            crate::round_transition::sample_round_transition_value(
                pre,
                rtd::N_SAMPLES_TRAIN_ROUND2,
                |s, rng| rtd::continue_through_round3(net, s, rng),
                rng,
                deadline,
            )
        }
        1 => {
            let deadline = std::time::Instant::now() + rtd::TIME_BUDGET_TRAIN_ROUND1;
            crate::round_transition::sample_round_transition_value(
                pre,
                rtd::N_SAMPLES_TRAIN_ROUND1,
                |s, rng| rtd::continue_through_round2(net, s, rng),
                rng,
                deadline,
            )
        }
        _ => {
            // Verteidigung: sollte durch `round_before < NUM_ROUNDS` (Aufrufer-
            // Bedingung) nie erreicht werden.
            let deadline = std::time::Instant::now() + crate::round_transition::TIME_BUDGET_TRAIN;
            crate::round_transition::sample_round_transition_value(
                pre,
                crate::round_transition::N_SAMPLES_TRAIN,
                |s, _rng| crate::net_mcts::net_leaf_eval(net, s),
                rng,
                deadline,
            )
        }
    }
}

/// Ein netzgeführtes Self-Play-Spiel. Wie `play_one_game`, aber Drafting per
/// Netz-PUCT (Priors vom Netz, Blatt per `leaf`) mit rohen Visit-Targets.
#[allow(clippy::too_many_arguments)]
fn play_net_self_play_game<R: Rng + ?Sized>(
    net: &Net,
    base_sims: u32,
    c_puct: f64,
    scoring_ids: Vec<usize>,
    names: [String; 2],
    first_player: usize,
    game_id: &str,
    rng: &mut R,
    add_root_noise: bool,
    deterministic: bool,
    move_heartbeat: Option<&AtomicU64>,
) -> Vec<Value> {
    let mut game = Game::start(names, first_player, scoring_ids, rng);
    let mut records: Vec<Map<String, Value>> = Vec::new();
    // Rundenübergangs-Trainingsziel (siehe round_transition.rs): je Runde N
    // ein per Chance-Node-Sampling gemitteltes Blattwert-Paar, gespeichert
    // unter der Rundennummer VOR dem Übergang (state.round zu dem Zeitpunkt,
    // wenn die Drafting-Phase endet). Ergänzt `scores`/`winner` additiv, siehe
    // Stamping-Schleife unten -- KEIN Ersatz dafür.
    let mut round_transition_values: std::collections::HashMap<u32, [f64; 2]> = std::collections::HashMap::new();
    // Punkt 6 (`evaluations/value head tests.txt`): TD-Bootstrap-Ziel
    // zusätzlich zum vollen `round_transition_value`, siehe
    // `bootstrap_value_after_rounds`-Doku (round_transition_deep.rs).
    let mut bootstrap_values: std::collections::HashMap<u32, [f64; 2]> = std::collections::HashMap::new();
    let mut guard = 0u32;
    let t_start = std::time::Instant::now();
    // `+ EXTRA_GAME_TIMEOUT_SECS`: BUGFIX, live gefunden. `net_game_timeout_secs`
    // wurde kalibriert, bevor `round_transition_deep` existierte -- ohne diesen
    // Zuschlag schnitt ein erster Smoke-Test (60 Sims, Timeout 30s) die Partie
    // VOR Rundenende 5 ab (0 Runde-5-Schritte trotz vollständigem Runde-1-4-
    // Sampling), exakt der corrupted-scores-Fehlermodus, den
    // `net_game_timeout_secs`s eigener Kommentar beschreibt -- siehe
    // round_transition_deep.rs::EXTRA_GAME_TIMEOUT_SECS.
    let timeout_secs = net_game_timeout_secs(base_sims) + crate::round_transition_deep::EXTRA_GAME_TIMEOUT_SECS;
    loop {
        guard += 1;
        if let Some(hb) = move_heartbeat {
            hb.fetch_add(1, Ordering::Relaxed);
        }
        // Hänger-Schutz: Schritt-Limit ODER sims-skalierte Wall-Clock je Partie.
        // Bricht pathologische Nicht-Terminierungen ab (eine teure Netz-Suche pro
        // Schritt würde sonst stundenlang grinden), statt den ganzen Lauf zu blockieren.
        if guard > 100_000 || t_start.elapsed().as_secs() >= timeout_secs {
            break;
        }
        match game.state.phase {
            Phase::StartPlacement | Phase::Drafting => {
                if game.state.players.iter().any(|p| p.start_tile_pending) {
                    match start_placement_step(&mut game, rng) {
                        Some(rec) => records.push(rec),
                        None => break,
                    }
                } else if game.state.phase == Phase::Drafting {
                    let player = game.state.current_player;
                    let actions = drafting_actions(&game.state);
                    let valid_actions: Vec<Value> =
                        actions.iter().map(|a| action_to_env_dict(&game.state, a)).collect();
                    let (chosen, policy) = if actions.len() == 1 {
                        let a = actions[0].clone();
                        let e = json!({ "action": action_to_env_dict(&game.state, &a), "prob": 1.0 });
                        (a, vec![e])
                    } else {
                        // Task #80: Kostenprofil-Kategorie (a) -- Gumbel-Suche der
                        // tatsaechlich gespielten Zuege. `timed()` ist ohne
                        // `clone_profiling`-Feature ein No-Op (siehe profiling.rs).
                        crate::profiling::timed(crate::profiling::note_gumbel_move_ns, || {
                            net_drafting_policy(net, &game.state, &actions, base_sims, c_puct, rng, add_root_noise, deterministic)
                        })
                    };
                    let moon_t = moon_order_target(&game.state, &chosen, player, rng);
                    let state_json = state_to_json(&game.state, true);
                    let round_before = game.state.round_number;
                    apply_chosen_action(&mut game, chosen);
                    if game.state.phase == Phase::Tiling && round_before < crate::state::NUM_ROUNDS {
                        // Rundenübergang gerade erreicht -- Chance-Node-
                        // Sampling für ein rauschärmeres Trainingsziel (siehe
                        // round_transition.rs). Läuft nur ~4x je Partie
                        // (einmal je echtem Rundenwechsel), Budget daher
                        // grosszügiger als in der (noch inaktiven)
                        // Live-Suche. Defensiv best-effort: schlägt der
                        // Sampling-Versuch fehl (sollte durch die
                        // Phase-Prüfung nicht vorkommen), bleibt einfach
                        // kein Eintrag für diese Runde -- Python-Seite fällt
                        // dann auf die literalen `scores` zurück.
                        //
                        // `round_before < NUM_ROUNDS` (nicht Runde 5) ist
                        // BUGFIX, nicht nur Optimierung: nach Runde 5s
                        // Tiling endet `execute_end_tiling` in `Phase::End`
                        // statt `next_round` aufzurufen (`is_over()` greift)
                        // -- ohne diese Prüfung sampelte
                        // `resolve_to_pre_chance`/`sample_round_transition_value`
                        // hier trotzdem "etwas" (den EndTiling-Übergang ins
                        // Spielende), aber ohne jede echte Zufallskomponente
                        // (kein Refill, `apply_tiling` liefert deterministisch
                        // denselben Endzustand) -- ein bedeutungsloser,
                        // irreführender Wert statt eines Rundenübergangs-
                        // Samples. Live gefunden: `round_transition_value`
                        // tauchte faelschlich auch in Runde-5-Records auf.
                        if let Some(pre) = crate::round_transition::resolve_to_pre_chance(&game.state) {
                            // Task #80: Kostenprofil-Kategorien (b)+(c) -- die teure
                            // rekursive round_transition_value-Simulation (inkl. der
                            // #71-Policy-Node-Budget-Suche in
                            // `choose_drafting_action_pruned`) getrennt von (e) dem
                            // TD-Bootstrap-Ziel gemessen, um die rtv/Bootstrap-
                            // Redundanzfrage kostenseitig zu beantworten.
                            let v = crate::profiling::timed(crate::profiling::note_rtv_ns, || {
                                sample_round_transition_for_round(round_before, &pre, net, rng)
                            });
                            round_transition_values.insert(round_before, v);
                            let bv = crate::profiling::timed(crate::profiling::note_bootstrap_ns, || {
                                crate::round_transition_deep::bootstrap_value_after_rounds(
                                    &pre,
                                    net,
                                    crate::round_transition_deep::BOOTSTRAP_HORIZON_ROUNDS,
                                    rng,
                                )
                            });
                            bootstrap_values.insert(round_before, bv);
                        }
                    }
                    let mut m = Map::new();
                    m.insert("state".into(), state_json);
                    m.insert("policy".into(), Value::Array(policy));
                    m.insert("valid_actions".into(), Value::Array(valid_actions));
                    m.insert(
                        "moon_order_target".into(),
                        moon_t.map(|v| json!(v)).unwrap_or(Value::Null),
                    );
                    m.insert("player".into(), json!(player));
                    records.push(m);
                } else {
                    break;
                }
            }
            Phase::Tiling => records.push(tiling_step(&mut game, rng)),
            _ => break,
        }
    }
    let completed = game.state.phase == Phase::End;
    if completed {
        let _ = game.apply_end_scoring();
    }
    let scores = [game.state.players[0].score, game.state.players[1].score];
    // Fund 7 (B1, Vollaudit 2026-07-21): auch der netzgeführte Pfad muss die
    // ungeklemmten Scores backfillen -- gleiches Muster wie in play_one_game.
    let scores_unclamped = [
        game.state.players[0].score_unclamped,
        game.state.players[1].score_unclamped,
    ];
    let winner = determine_winner(&game.state);
    records
        .into_iter()
        .map(|mut m| {
            m.insert("game_id".into(), json!(game_id));
            m.insert("scores".into(), json!(scores));
            m.insert("scores_unclamped".into(), json!(scores_unclamped));
            m.insert("winner".into(), json!(winner));
            m.insert("completed".into(), json!(completed));
            // Zusätzliches, rauschärmeres Trainingsziel für den Rundenübergang
            // (siehe round_transition.rs) -- additiv, ERSETZT `scores`/`winner`
            // NICHT. Nur vorhanden für Runden, die tatsächlich einen
            // Übergang erreicht haben (nicht Runde 5, keine abgebrochenen
            // Partien) -- Python-Seite muss das Fehlen tolerieren.
            let round = m.get("state").and_then(|s| s.get("round")).and_then(|r| r.as_u64());
            if let Some(v) = round.and_then(|r| round_transition_values.get(&(r as u32))) {
                m.insert("round_transition_value".into(), json!(v));
            }
            if let Some(v) = round.and_then(|r| bootstrap_values.get(&(r as u32))) {
                m.insert("bootstrap_value".into(), json!(v));
            }
            Value::Object(m)
        })
        .collect()
}

/// Zusätzliche Sicherheitsmarge (über `net_game_timeout_secs +
/// EXTRA_GAME_TIMEOUT_SECS` hinaus) für den präemptiven Thread-Watchdog
/// unten -- gibt dem KOOPERATIVEN Timeout in `play_net_self_play_game`
/// (dessen eigener `guard`/`t_start.elapsed()`-Check) immer zuerst die
/// Chance, sauber mit einem `completed: false`-Teilresultat zurückzukehren
/// (besser als ein komplett leeres Ergebnis).
const WATCHDOG_MARGIN_SECS: u64 = 60;

/// Führt `f` mit einer HARTEN Wallclock-Deadline aus, präemptiv statt
/// kooperativ: `f` läuft in einem eigenen OS-Thread; überschreitet es
/// `deadline`, wartet der Aufrufer NICHT weiter -- er bekommt `None` und
/// macht sofort mit dem nächsten Spiel weiter.
///
/// Hintergrund (Root-Cause-Fix 2026-07-22, siehe `fill_large_factory` in
/// state.rs): `play_net_self_play_game`s eigener Hänger-Schutz
/// (`guard`/`t_start.elapsed()` in dessen Zug-Schleife) ist rein
/// KOOPERATIV -- er wird nur ZWISCHEN zwei Zügen geprüft. Hängt ein
/// EINZELNER Zug in einer tiefer liegenden, unbegrenzten Schleife (wie es
/// bei `fill_large_factory` der Fall war, aufgerufen aus
/// `setup_new_round`/`next_round` beim Rundenübergang, oder ebenso aus
/// `round_transition_deep::bootstrap_value_after_rounds`s Sampling), kommt
/// die Zug-Schleife nie wieder zu ihrer eigenen Deadline-Prüfung zurück --
/// der kooperative Timeout greift dann nicht, exakt der beobachtete Hänger
/// (1 nativer Thread spinnt auf 100%, alle anderen rayon-Worker idle,
/// Python-Hauptthread parkt in `WaitOnAddress` auf das `.collect()` der
/// gesamten Partie-Menge). Dieser Watchdog ist die einzige WIRKLICH
/// präemptive Absicherung: er schützt auch gegen künftige, heute noch
/// unbekannte unbegrenzte Schleifen tief im Aufrufbaum, ohne dass jede
/// einzelne Funktion selbst einen Deadline-Parameter durchreichen muss.
///
/// Trade-off: der gespawnte Thread wird NICHT abgebrochen (Rust/OS-Threads
/// sind nicht sicher von außen killbar) -- er läuft verwaist weiter, bis er
/// selbst terminiert oder der Prozess endet, und bindet bis dahin einen
/// CPU-Kern. Das ist bewusst hingenommen: besser 1 verwaister Kern als der
/// gesamte Chunk/Batch, der laut Beobachtung sonst komplett blockiert.
fn run_with_watchdog<F, T>(deadline: std::time::Duration, f: F) -> Option<T>
where
    F: FnOnce() -> T + Send + 'static,
    T: Send + 'static,
{
    let (tx, rx) = std::sync::mpsc::channel();
    std::thread::spawn(move || {
        let result = f();
        let _ = tx.send(result);
    });
    rx.recv_timeout(deadline).ok()
}

/// Netzgeführtes Self-Play: `n_games` Partien (rayon-parallel), Netz vs. sich
/// selbst, rohe Visit-Targets. Gibt alle Step-Records flach als JSON-Array
/// zurück. `progress_path`/`heartbeat_path`: siehe `run_self_play`-
/// Dokumentation (Task #71) -- dies ist der Pfad des v12-Batches
/// (`--mode network`), daher hier die primäre Zielfunktion für den Fix.
#[allow(clippy::too_many_arguments)]
pub fn run_net_self_play(
    model_path: &str,
    n_games: usize,
    base_sims: u32,
    c_puct: f64,
    seed: u64,
    num_threads: usize,
    prefix: &str,
    add_root_noise: bool,
    deterministic: bool,
    progress_path: Option<&str>,
    heartbeat_path: Option<&str>,
) -> Result<String, String> {
    let net = std::sync::Arc::new(Net::load(model_path, crate::features::INPUT_SIZE).map_err(|e| e.to_string())?);
    let progress_file = open_progress_file(progress_path);
    let move_counter = Arc::new(AtomicU64::new(0));
    let games_counter = Arc::new(AtomicU64::new(0));
    let (hb_stop, hb_handle) = start_heartbeat_reporter(
        heartbeat_path.map(String::from),
        Arc::clone(&move_counter),
        Arc::clone(&games_counter),
    );

    // Perspektiven-/OOD-Audit (siehe net_mcts.rs-Modulkommentar zu
    // `PERSPECTIVE_DIVERGENCE_STATS`) -- vor diesem Self-Play-Lauf
    // zuruecksetzen, damit der angehaengte Snapshot NUR diesen Lauf abbildet.
    crate::net_mcts::perspective_divergence_reset();

    // Präemptiver Per-Spiel-Watchdog (siehe `run_with_watchdog`-Doku): der
    // interne kooperative Timeout von `play_net_self_play_game` bekommt per
    // `WATCHDOG_MARGIN_SECS` immer zuerst die Chance, sauber abzubrechen --
    // erst wenn das nicht einmal das schafft (Hänger tief in einem
    // EINZELNEN Zug, siehe Kommentar oben), greift dieser harte Deckel.
    let watchdog_deadline = std::time::Duration::from_secs(
        net_game_timeout_secs(base_sims) + crate::round_transition_deep::EXTRA_GAME_TIMEOUT_SECS + WATCHDOG_MARGIN_SECS,
    );
    let play = |i: usize| -> Vec<Value> {
        let mut rng =
            StdRng::seed_from_u64(seed.wrapping_add((i as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15)));
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let first = rng.random_range(0..2usize);
        let names = ["Netz".to_string(), "Netz".to_string()];
        let gid = format!("{prefix}_g{}", i + 1);
        let net = std::sync::Arc::clone(&net);
        let gid_thread = gid.clone();
        let move_counter_thread = Arc::clone(&move_counter);
        let result = run_with_watchdog(watchdog_deadline, move || {
            play_net_self_play_game(
                &net, base_sims, c_puct, ids, names, first, &gid_thread, &mut rng, add_root_noise, deterministic,
                Some(&move_counter_thread),
            )
        });
        let steps = match result {
            Some(v) => v,
            None => {
                eprintln!(
                    "⚠️  [Watchdog] Spiel {gid} ueberschritt die harte {watchdog_deadline:?}-Deadline -- \
                     als unvollstaendig verworfen (verwaister Thread laeuft im Hintergrund weiter)."
                );
                Vec::new()
            }
        };
        // Nur GENUTZTE Spiele (nicht der leere Watchdog-Abbruch-Fall) zaehlen
        // fuers Fortschritts-Tracking -- ein leeres Ergebnis traegt nichts
        // zur Ziel-Spielezahl bei (`_group_by_game` in self_play.py ueberspringt
        // es ohnehin, siehe dortige Gruppierung anhand von `game_id`-Steps).
        if !steps.is_empty() {
            games_counter.fetch_add(1, Ordering::Relaxed);
            append_game_progress(&progress_file, &steps);
        }
        steps
    };

    let all: Vec<Vec<Value>> = if num_threads == 0 {
        (0..n_games).into_par_iter().map(play).collect()
    } else {
        match rayon::ThreadPoolBuilder::new().num_threads(num_threads).build() {
            Ok(pool) => pool.install(|| (0..n_games).into_par_iter().map(play).collect()),
            Err(_) => (0..n_games).map(play).collect(),
        }
    };
    stop_heartbeat_reporter(hb_stop, hb_handle);
    let mut flat: Vec<Value> = all.into_iter().flatten().collect();
    // Audit-Objekt anhaengen -- gleiches Muster wie `stage3_diagnostics`
    // weiter unten (arena.py/self_play.py lesen es separat aus, kein
    // Einfluss auf die Trainingsdaten-Auswertung).
    flat.push(json!({
        "perspective_divergence_diagnostics": true,
        "by_round": crate::net_mcts::perspective_divergence_snapshot(),
    }));
    Ok(serde_json::to_string(&Value::Array(flat)).unwrap_or_else(|_| "[]".to_string()))
}

// ── Alpha-Beta-Minimax als guenstige Rollout-Fortsetzungspolitik ────────────
// Hintergrund (siehe evaluations/stage2_investigation.md, Stufe-3-Kalibrierung):
// Profiling zeigte 1,8 Mio. Blattauswertungen fuer nur 2 Spiele -- Feature-
// Extraktion, Netz-Forward-Pass und DFS-Solver je etwa gleich teuer (~31-35%),
// keiner davon dominant. Der PUCT-Sims-Ansatz braucht so viele Auswertungen,
// weil er fuer VERRAUSCHTE Blattwerte gebaut ist (viele Simulationen, um
// Rauschen wegzumitteln) -- unser DFS-Blatt ist aber EXAKT. Referenz
// (domwil.co.uk/posts/azul-ai): ein echtes Azul-KI-Projekt nutzt gar keine
// MCTS, sondern Alpha-Beta-Minimax mit Zugsortierung + einer guenstigen
// statischen "Score, wenn die Runde JETZT endet"-Bewertung (identisch zu
// unserem `player_total`/DFS-Solver) -- 42-54x weniger besuchte Knoten als
// reines Minimax. Hier als guenstigere Fortsetzungspolitik NUR fuer Stufe-3-
// Rollouts prototypisiert (NICHT fuer Stufe 1 selbst, das bleibt PUCT).

/// Bewertet `state` aus Sicht von `perspective` (dessen Score minus Gegner-
/// Score) per Alpha-Beta-Minimax mit Netz-Policy-Zugsortierung (ein
/// Forward-Pass je Knoten fuer die Reihenfolge, kein Sims-Budget). Bricht ab
/// bei Rundenende (Phase != Drafting), erschoepfter `depth_remaining` ODER
/// erschoepftem `node_budget` -- an all diesen Punkten liefert `player_total`
/// (derselbe DFS-Solver-Score wie Stufe 1s Blattwert, nur ggf. VOR dem
/// echten Rundenende ausgewertet: "wieviele Punkte, wenn die Runde jetzt
/// endet") die Bewertung.
#[allow(clippy::too_many_arguments)]
fn negamax_value(
    net: &Net,
    state: &GameState,
    depth_remaining: u32,
    alpha_in: f64,
    beta_in: f64,
    perspective: usize,
    node_count: &mut u32,
    node_budget: u32,
) -> f64 {
    *node_count += 1;
    ALPHABETA_NODE_VISITS.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    if state.phase != Phase::Drafting || depth_remaining == 0 || *node_count >= node_budget {
        return crate::profiling::timed(crate::profiling::note_dfs_eval_ns, || {
            player_total(state, perspective) - player_total(state, 1 - perspective)
        });
    }
    let actions = drafting_actions(state);
    if actions.is_empty() {
        return crate::profiling::timed(crate::profiling::note_dfs_eval_ns, || {
            player_total(state, perspective) - player_total(state, 1 - perspective)
        });
    }
    let feats = crate::profiling::timed(crate::profiling::note_features_ns, || state_to_features_direct(state));
    let (logits, _value, _m, _points) =
        crate::profiling::timed(crate::profiling::note_net_eval_ns, || {
            net.eval(&feats).unwrap_or_else(|_| {
                (vec![0.0; crate::net_mcts::NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new())
            })
        });
    let mut scored: Vec<(f32, Action)> = actions
        .into_iter()
        .map(|a| {
            let id = action_to_id(&action_to_env_dict(state, &a));
            (logits.get(id).copied().unwrap_or(f32::NEG_INFINITY), a)
        })
        .collect();
    scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));

    let maximizing = state.current_player == perspective;
    let mut alpha = alpha_in;
    let mut beta = beta_in;
    let mut best = if maximizing { f64::NEG_INFINITY } else { f64::INFINITY };
    for (_, a) in scored {
        if *node_count >= node_budget {
            break;
        }
        let mut g = Game { state: state.clone() };
        if g.apply_drafting(&a).is_err() {
            continue;
        }
        let val = negamax_value(
            net, &g.state, depth_remaining - 1, alpha, beta, perspective, node_count, node_budget,
        );
        if maximizing {
            if val > best {
                best = val;
            }
            if best > alpha {
                alpha = best;
            }
        } else {
            if val < best {
                best = val;
            }
            if best < beta {
                beta = best;
            }
        }
        if alpha >= beta {
            break; // Beta-/Alpha-Cutoff
        }
    }
    if best.is_finite() {
        best
    } else {
        player_total(state, perspective) - player_total(state, 1 - perspective)
    }
}

/// Waehlt EINE Drafting-Aktion per Alpha-Beta-Minimax (siehe `negamax_value`)
/// -- guenstige Ersatz-Fortsetzungspolitik fuer Stufe-3-Rollouts statt der
/// vollen PUCT-Suche. `depth` begrenzt die Suchtiefe (Plies), `node_budget`
/// ist ein zusaetzliches Sicherheitsnetz gegen pathologische Explosion.
fn alphabeta_choose_action(
    net: &Net,
    state: &GameState,
    actions: &[Action],
    depth: u32,
    node_budget: u32,
) -> Action {
    if actions.len() <= 1 {
        return actions.first().cloned().unwrap_or(Action::Pass);
    }
    ALPHABETA_CALLS.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    let perspective = state.current_player;
    let feats = crate::profiling::timed(crate::profiling::note_features_ns, || state_to_features_direct(state));
    let (logits, _value, _m, _points) =
        crate::profiling::timed(crate::profiling::note_net_eval_ns, || {
            net.eval(&feats).unwrap_or_else(|_| {
                (vec![0.0; crate::net_mcts::NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new())
            })
        });
    let mut scored: Vec<(f32, Action)> = actions
        .iter()
        .map(|a| {
            let id = action_to_id(&action_to_env_dict(state, a));
            (logits.get(id).copied().unwrap_or(f32::NEG_INFINITY), a.clone())
        })
        .collect();
    scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));

    let mut node_count = 0u32;
    let mut best_action = scored[0].1.clone();
    let mut best_val = f64::NEG_INFINITY;
    let mut alpha = f64::NEG_INFINITY;
    let beta = f64::INFINITY;
    for (_, a) in scored {
        if node_count >= node_budget {
            break;
        }
        let mut g = Game { state: state.clone() };
        if g.apply_drafting(&a).is_err() {
            continue;
        }
        let val = negamax_value(
            net, &g.state, depth.saturating_sub(1), alpha, beta, perspective, &mut node_count, node_budget,
        );
        if val > best_val {
            best_val = val;
            best_action = a;
        }
        if val > alpha {
            alpha = val;
        }
    }
    best_action
}

/// Wendet `first_action` auf eine Kopie von `state` an und spielt danach
/// `n_reps`-mal (je frischer RNG-Ziehung ab diesem Punkt) per Stufe-1-Politik
/// (DFS-Blatt, deterministisch — Champion-Spielstil) bis Spielende fort.
/// Gibt den mittleren Score-Vorsprung (`player` minus Gegner) zurück.
/// `horizon_rounds`: `None` = wie bisher bis Spielende (Disagreement-Studie).
/// `Some(h)` bricht ab, sobald `h` Runden ab der aktuellen gespielt wurden,
/// und wertet den bis dahin ECHT erzielten Score-Vorsprung aus (keine
/// Schätzung -- nur ohne die Wertungsplatten-Endbonuspunkte, die erst am
/// echten Spielende dazukommen). Kappt die Rollout-Kosten drastisch fuer
/// fruehe Runden (siehe stage2_investigation.md, Stufe-3-Kalibrierung: ab
/// Runde 1 muessten sonst im Schnitt alle ~109 restlichen Zuege des GANZEN
/// Spiels durchgespielt werden, mit horizon_rounds=2 nur noch die aktuelle
/// plus eine weitere Runde).
/// `alphabeta`: `None` = Fortsetzung per Stufe-1-PUCT (`net_drafting_policy`,
/// wie bisher). `Some((depth, node_budget))` nutzt stattdessen die guenstigere
/// Alpha-Beta-Minimax-Fortsetzung (`alphabeta_choose_action`) -- Prototyp fuer
/// Stufe-3-Rollouts, siehe Kommentar vor `negamax_value`.
#[allow(clippy::too_many_arguments)]
fn mean_rollout_diff<R: Rng + ?Sized>(
    net: &Net,
    state: &GameState,
    first_action: &Action,
    base_sims: u32,
    c_puct: f64,
    n_reps: usize,
    player: usize,
    horizon_rounds: Option<u32>,
    alphabeta: Option<(u32, u32)>,
    rng: &mut R,
) -> f64 {
    let start_round = state.round_number;
    let mut total = 0.0;
    for _ in 0..n_reps {
        let mut g = Game { state: state.clone() };
        // Determinisierung (Weg 1, siehe evaluations/stage2_investigation.md,
        // Nutzer-Anstoss): das noch UNBEKANNTE -- Beutel-Restbestand und
        // verdeckter Kuppelstapel -- wird je Wiederholung frisch ausgewuerfelt.
        // OHNE das wuerden ALLE Wiederholungen exakt dieselbe, schon
        // feststehende Reihenfolge durchspielen (`draw_with_refill` mischt den
        // Beutel nur bei Unterversorgung neu, der Kuppelstapel wird nur EINMAL
        // beim Spielstart gemischt) -- verifiziert per Test
        // `rollout_repetitions_actually_diverge_in_bag_and_dome_order`, der
        // ohne diesen Fix fehlschlaegt (identischer Beutel/Stapel ueber alle
        // Wiederholungen). Die sichtbare Information (Fabriken, Spielerbretter,
        // Kuppel-Auslage) bleibt unveraendert -- nur das wirklich Verdeckte
        // wird neu resampelt.
        g.state.bag.tiles.shuffle(rng);
        g.state.dome_tile_pool.shuffle(rng);
        let _ = g.apply_drafting(first_action);
        let mut guard = 0u32;
        loop {
            guard += 1;
            if guard > 2000 {
                break;
            }
            if let Some(h) = horizon_rounds {
                if g.state.phase == Phase::Drafting && g.state.round_number >= start_round + h {
                    break;
                }
            }
            match g.state.phase {
                Phase::StartPlacement | Phase::Drafting => {
                    if g.state.players.iter().any(|p| p.start_tile_pending) {
                        if start_placement_step(&mut g, rng).is_none() {
                            break;
                        }
                    } else if g.state.phase == Phase::Drafting {
                        let actions = drafting_actions(&g.state);
                        if actions.is_empty() {
                            break;
                        }
                        let a = if actions.len() == 1 {
                            actions[0].clone()
                        } else if let Some((depth, node_budget)) = alphabeta {
                            alphabeta_choose_action(net, &g.state, &actions, depth, node_budget)
                        } else {
                            let (a, _) = net_drafting_policy(
                                net, &g.state, &actions, base_sims, c_puct, rng, false, true,
                            );
                            a
                        };
                        apply_chosen_action(&mut g, a);
                    } else {
                        break;
                    }
                }
                Phase::Tiling => {
                    tiling_step(&mut g, rng);
                }
                _ => break,
            }
        }
        if g.state.phase == Phase::End {
            let _ = g.apply_end_scoring();
        }
        let opp = 1 - player;
        total += (g.state.players[player].score - g.state.players[opp].score) as f64;
    }
    total / n_reps.max(1) as f64
}

// ── Stufe 3: explizite Zufallsmittelung über Rundengrenzen (Rollouts) ───────
// Begründung siehe `evaluations/stage2_investigation.md`: AlphaZero (Schach/
// Go) hat keine Zufallsknoten im Suchbaum, weil dort kein Zufall zwischen
// Zügen liegt. Backgammon/Scrabble-Programme lösen das nicht durch ein
// größeres Wertenetz, sondern durch explizite Mittelung über den Zufall
// (Rollouts). Stufe 1 hatte (wie Stufe 2, mittlerweile entfernt) null
// Zufallsknoten -- der Suchbaum endet exakt an der Rundengrenze
// (`terminal = phase != Drafting`) und überließ den kompletten Rest
// (Beutel-Nachschub künftiger Runden) frueher dem Wertenetz. Stufe 3 ersetzt
// diese Schätzung durch echte Simulation: die vielversprechendsten
// Kandidatenzüge (Top-K nach Netz-Suche) werden je `n_reps`-mal mit
// unabhängigem Zufall (Beutel-Nachschub) bis Spielende fortgesetzt
// (Stufe-1-Politik als Fortsetzung), der beste mittlere Score-Vorsprung
// gewinnt. Braucht keinen Value-Head (reine Policy+DFS-Simulation), ist aber
// pro Zug deutlich teurer.

/// Diagnose-Zaehler (Trigger-Rate des Rollout-Tiebreaks) fuer die
/// Stufe-3-Kalibrierung -- siehe `run_stage3_vs_stage1_arena`, das sie vor
/// jedem Lauf zuruecksetzt und am Ende ausliest/loggt.
static STAGE3_DECISIONS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static STAGE3_ROLLOUTS_TRIGGERED: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
/// Zaehlt besuchte Knoten (`negamax_value`-Aufrufe) bzw. Top-Level-Aufrufe
/// von `alphabeta_choose_action` -- Kalibrierungshilfe fuer depth/node_budget.
pub(crate) static ALPHABETA_NODE_VISITS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
pub(crate) static ALPHABETA_CALLS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);

/// Wählt EINE Drafting-Aktion per Stufe 3: Top-K-Kandidaten (nach Besuchen
/// einer günstigen Vorab-Suche, DFS-Blatt) werden je `n_reps`-mal per
/// Rollout (begrenzt auf `horizon_rounds` Runden statt Spielende) bewertet,
/// bester mittlerer Score-Vorsprung gewinnt. NUR fuer Runde-1/2-Entscheidungen
/// aufgerufen (siehe `play_stage3_vs_stage1_game`) -- ein Besuchsanteil-/
/// Q-Wert-basiertes "nur bei knappen Entscheidungen"-Kriterium (das
/// TD-Gammon/Maven-Muster) wurde gemessen und verworfen: bei ~20-43
/// Kandidaten je Runde verteilt die guenstige Suche Besuche zu duenn, um
/// "knapp" verlaesslich von "eindeutig" zu unterscheiden (94% aller
/// Entscheidungen lagen selbst unter margin=0.30 noch "knapp" -- kein
/// brauchbares Signal). Die Rundenbegrenzung ist der robustere Kosten-Hebel:
/// billig UND genau dort, wo die Mehrrunden-Frage zaehlt (siehe
/// evaluations/stage2_investigation.md, Stufe-3-Kalibrierung). Fällt auf die
/// einzige Aktion zurück, falls nur eine legal ist.
#[allow(clippy::too_many_arguments)]
fn stage3_choose_action<R: Rng + ?Sized>(
    net: &Net,
    state: &GameState,
    actions: &[Action],
    shortlist_sims: u32,
    rollout_sims: u32,
    c_puct: f64,
    top_k: usize,
    n_reps: usize,
    horizon_rounds: u32,
    alphabeta_depth: u32,
    alphabeta_node_budget: u32,
    rng: &mut R,
) -> Action {
    if actions.len() <= 1 {
        return actions.first().cloned().unwrap_or(Action::Pass);
    }
    // Kandidaten-Vorauswahl: guenstige Suche (wie Stufe 1), Top-K nach Besuchen
    // -- nicht ALLE Legalzuege ausrollen, das waere zu teuer.
    let sims = net_effective_sims(shortlist_sims, actions.len());
    let mut stats = net_root_child_stats(net, state, sims, c_puct, false, rng);
    stats.sort_by(|a, b| b.1.cmp(&a.1)); // absteigend nach Besuchen
    if stats.is_empty() {
        return actions[0].clone();
    }
    STAGE3_DECISIONS.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    STAGE3_ROLLOUTS_TRIGGERED.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    let player = state.current_player;
    let mut best_action = stats[0].0.clone();
    let mut best_score = f64::NEG_INFINITY;
    let alphabeta = Some((alphabeta_depth, alphabeta_node_budget));
    for (a, _visits, _q) in stats.into_iter().take(top_k.max(1)) {
        let mean_diff = mean_rollout_diff(
            net, state, &a, rollout_sims, c_puct, n_reps, player, Some(horizon_rounds), alphabeta, rng,
        );
        if mean_diff > best_score {
            best_score = mean_diff;
            best_action = a;
        }
    }
    best_action
}

/// Ein Spiel Stufe 3 (Brett 0) vs. Stufe 1 (Brett 1), dasselbe Netz. Analog zu
/// `play_net_vs_net_game`, nur dass Brett 0 bis einschliesslich Runde
/// `stage3_max_round` `stage3_choose_action` nutzt (danach faellt es auf
/// reine Stufe 1 zurueck -- Kosten-Hebel, siehe stage3_choose_action).
#[allow(clippy::too_many_arguments)]
fn play_stage3_vs_stage1_game<R: Rng + ?Sized>(
    net: &Net,
    sims1: u32,
    stage3_shortlist_sims: u32,
    stage3_rollout_sims: u32,
    c_puct: f64,
    top_k: usize,
    n_reps: usize,
    horizon_rounds: u32,
    stage3_max_round: u32,
    alphabeta_depth: u32,
    alphabeta_node_budget: u32,
    scoring_ids: Vec<usize>,
    names: [String; 2],
    first_player: usize,
    rng: &mut R,
) -> Value {
    let mut game = Game::start(names, first_player, scoring_ids, rng);
    let mut steps = 0u32;
    let mut guard = 0u32;
    let t_start = std::time::Instant::now();
    // Grosszuegiger fester Timeout statt `net_game_timeout_secs`: Stufe 3
    // macht pro Zug deutlich mehr Arbeit (Top-K x n_reps Rollouts bis
    // Spielende) -- dieselbe Falle wie beim Disagreement-Study-Timeout-Bug.
    let timeout_secs: u64 = 3600;
    loop {
        guard += 1;
        if guard > 100_000 || t_start.elapsed().as_secs() >= timeout_secs {
            break;
        }
        match game.state.phase {
            Phase::StartPlacement | Phase::Drafting => {
                if game.state.players.iter().any(|p| p.start_tile_pending) {
                    let first = game.state.current_player;
                    let non_starter = 1 - first;
                    let pi = if game.state.players[non_starter].start_tile_pending {
                        non_starter
                    } else if game.state.players[first].start_tile_pending {
                        first
                    } else {
                        break;
                    };
                    match choose_start_placement(&game.state, pi) {
                        Some((tid, r, c2, rot)) => {
                            let _ = apply_start_placement(&mut game.state, pi, tid, r, c2, rot);
                        }
                        None => break,
                    }
                    steps += 1;
                } else if game.state.phase == Phase::Drafting {
                    let pi = game.state.current_player;
                    let actions = drafting_actions(&game.state);
                    let chosen = if actions.len() == 1 {
                        actions[0].clone()
                    } else if pi == 0 && game.state.round_number <= stage3_max_round {
                        stage3_choose_action(
                            net, &game.state, &actions, stage3_shortlist_sims, stage3_rollout_sims,
                            c_puct, top_k, n_reps, horizon_rounds, alphabeta_depth, alphabeta_node_budget, rng,
                        )
                    } else {
                        let s = net_effective_sims(sims1, actions.len());
                        net_search_drafting_action(net, &game.state, s, c_puct, false, rng)
                            .unwrap_or_else(|| actions[0].clone())
                    };
                    apply_chosen_action(&mut game, chosen);
                    steps += 1;
                } else {
                    break;
                }
            }
            Phase::Tiling => {
                let pi = game.state.current_player;
                match resolve_tiling_step(&game.state, pi) {
                    TilingStep::Place(ta) => {
                        let _ = game.apply_single_tiling(pi, &ta);
                    }
                    TilingStep::Chips { row, chips } => {
                        apply_bonus_chips_with(&mut game.state.players[pi], row, &chips);
                    }
                    TilingStep::End => {
                        let _ = game.apply_tiling(&TilingMove::EndTiling { player: pi }, rng);
                    }
                }
                steps += 1;
            }
            _ => break,
        }
    }
    if game.state.phase == Phase::End {
        let _ = game.apply_end_scoring();
    }
    let p0 = &game.state.players[0];
    let p1 = &game.state.players[1];
    json!({
        "scores": [p0.score, p1.score],
        "scores_unclamped": [p0.score_unclamped, p1.score_unclamped],
        "winner": determine_winner(&game.state),
        "steps": steps,
        "total_floor": [p0.total_floor_penalties, p1.total_floor_penalties],
        "floor_per_round": [p0.floor_penalties_per_round, p1.floor_penalties_per_round],
    })
}

/// `n_games` Spiele Stufe 3 (Brett 0) vs. Stufe 1 (Brett 1), dasselbe Netz,
/// Startspieler alternierend. Gibt JSON-Array `[{scores:[Stufe3,Stufe1],
/// winner, …}]` (Format wie `run_net_vs_net_arena`, Elo/SPRT rechnet
/// `arena.py`).
#[allow(clippy::too_many_arguments)]
pub fn run_stage3_vs_stage1_arena(
    model_path: &str,
    n_games: usize,
    sims1: u32,
    stage3_shortlist_sims: u32,
    stage3_rollout_sims: u32,
    c_puct: f64,
    top_k: usize,
    n_reps: usize,
    horizon_rounds: u32,
    stage3_max_round: u32,
    alphabeta_depth: u32,
    alphabeta_node_budget: u32,
    seed: u64,
    num_threads: usize,
) -> Result<String, String> {
    let net = std::sync::Arc::new(Net::load(model_path, crate::features::INPUT_SIZE).map_err(|e| e.to_string())?);
    use std::sync::atomic::Ordering;
    STAGE3_DECISIONS.store(0, Ordering::Relaxed);
    STAGE3_ROLLOUTS_TRIGGERED.store(0, Ordering::Relaxed);

    let play = |i: usize| -> Value {
        let mut rng =
            StdRng::seed_from_u64(seed.wrapping_add((i as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15)));
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let first = i % 2;
        let names = ["Stufe3".to_string(), "Stufe1".to_string()];
        play_stage3_vs_stage1_game(
            &net, sims1, stage3_shortlist_sims, stage3_rollout_sims, c_puct, top_k, n_reps,
            horizon_rounds, stage3_max_round, alphabeta_depth, alphabeta_node_budget, ids, names, first, &mut rng,
        )
    };

    let mut all: Vec<Value> = if num_threads <= 1 {
        (0..n_games).map(play).collect()
    } else {
        match rayon::ThreadPoolBuilder::new().num_threads(num_threads).build() {
            Ok(pool) => pool.install(|| (0..n_games).into_par_iter().map(play).collect()),
            Err(_) => (0..n_games).map(play).collect(),
        }
    };
    // Trigger-Rate des Rollout-Tiebreaks als eigenes Diagnose-Objekt anhaengen
    // (Kalibrierungs-Hilfe, siehe evaluations/stage2_investigation.md) --
    // arena.py liest es separat aus, kein Einfluss auf die Spiel-Auswertung.
    let decisions = STAGE3_DECISIONS.load(Ordering::Relaxed);
    let triggered = STAGE3_ROLLOUTS_TRIGGERED.load(Ordering::Relaxed);
    all.push(json!({
        "stage3_diagnostics": true,
        "decisions": decisions,
        "rollouts_triggered": triggered,
        "trigger_rate": if decisions > 0 { triggered as f64 / decisions as f64 } else { 0.0 },
    }));
    Ok(serde_json::to_string(&Value::Array(all)).unwrap_or_else(|_| "[]".to_string()))
}

/// Kendall-Tau (unnormalisiert, Tau-a) zwischen zwei parallelen Werte-Listen
/// -- Anteil konkordanter minus diskordanter Paare, [-1,1]. Bei `n<2` (kein
/// Paar möglich) `0.0` (neutral, nicht "perfekt übereinstimmend").
fn kendall_tau(pairs: &[(f64, f64)]) -> f64 {
    let n = pairs.len();
    if n < 2 {
        return 0.0;
    }
    let mut concordant = 0i64;
    let mut discordant = 0i64;
    for i in 0..n {
        for j in (i + 1)..n {
            let (xa, ya) = pairs[i];
            let (xb, yb) = pairs[j];
            let dx = xa - xb;
            let dy = ya - yb;
            let sign = dx * dy;
            if sign > 0.0 {
                concordant += 1;
            } else if sign < 0.0 {
                discordant += 1;
            }
        }
    }
    let total = (concordant + discordant) as f64;
    if total <= 0.0 {
        0.0
    } else {
        (concordant - discordant) as f64 / total
    }
}

/// Geschwister-Ranking-Diagnose (Nutzer-Auftrag nach externem Kollegen-
/// Vorschlag, 2026-07-20, siehe `evaluations/Bugfixes.txt` Punkt 3): PUCT
/// braucht keine absolute Kalibrierung des Value-Heads, sondern die
/// richtige RANGFOLGE unter den Kindern eines Knotens ("Geschwister") --
/// das ist eine andere, praxisnähere Frage als das bisher gemessene globale
/// Val-R². Läuft die Netz-eigene Suche (`net_search_drafting_action`,
/// dieselbe Zustandsverteilung wie die echte Live-Suche, kein künstlicher
/// Random-Walk) ein Spiel weit, sammelt dabei bis zu `n_states_per_round`
/// Runde-1/2-Drafting-Entscheidungspunkte ein. Für jeden gesammelten
/// Zustand: alle (bzw. bis zu `max_children`, zufällig gezogen falls mehr)
/// legalen Nachfolgezustände sowohl per trainiertem Netz-Value als auch per
/// exaktem DFS-Solver (Ground Truth, `crate::mcts::evaluate` -- absolute
/// Pro-Spieler-Werte, unabhängig davon wer gerade am Zug ist, funktioniert
/// daher unverändert für JEDEN Nachfolgezustand) auswerten, Kendall-Tau
/// zwischen beiden Rangfolgen berechnen. Aggregiert nach Runde als JSON
/// zurückgegeben.
///
/// Netz-Ranking bewusst NICHT über den (im Live-Suche-Blattwert genutzten,
/// separat als nicht hilfreich getesteten, siehe `MIRROR_OTHER_VAL`-
/// Kommentar) Flip-Klon für die Gegner-Perspektive -- stattdessen der
/// native, garantiert In-Distribution Ein-Forward-Pass auf dem tatsächlichen
/// Nachfolgezustand (dessen `current_player` nach dem Zug auf den GEGNER
/// zeigt): Ranking nach `1 - value_to_win_prob(...)` (höher = besser für
/// den ziehenden Spieler) ist ordnungsäquivalent zur Gegner-Sicht, keine
/// zusätzliche Annahme nötig.
pub fn sibling_ranking_diagnostic(
    model_path: &str,
    n_states_per_round: usize,
    max_children: usize,
    walk_sims: u32,
    seed: u64,
) -> Result<String, String> {
    let net = Net::load(model_path, crate::features::INPUT_SIZE).map_err(|e| e.to_string())?;
    let mut rng = StdRng::seed_from_u64(seed);
    let target_rounds = [1u32, 2u32];
    let mut taus: std::collections::HashMap<u32, Vec<f64>> = std::collections::HashMap::new();
    let mut sib_counts: std::collections::HashMap<u32, Vec<usize>> = std::collections::HashMap::new();

    let mut game_idx = 0u64;
    loop {
        let need_more = target_rounds
            .iter()
            .any(|r| taus.get(r).map(|v| v.len()).unwrap_or(0) < n_states_per_round);
        if !need_more || game_idx > 300 {
            break;
        }
        game_idx += 1;

        let names = ["A".to_string(), "B".to_string()];
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let mut rng_game =
            StdRng::seed_from_u64(seed.wrapping_add(game_idx.wrapping_mul(0x9E37_79B9_7F4A_7C15)));
        let mut game = Game::start(names, 0, ids, &mut rng_game);
        let t_start = std::time::Instant::now();
        let mut guard = 0u32;
        while guard < 2000 && t_start.elapsed().as_secs() < 120 {
            guard += 1;
            match game.state.phase {
                Phase::StartPlacement | Phase::Drafting => {
                    if game.state.players.iter().any(|p| p.start_tile_pending) {
                        let first = game.state.current_player;
                        let non_starter = 1 - first;
                        let pi = if game.state.players[non_starter].start_tile_pending {
                            non_starter
                        } else if game.state.players[first].start_tile_pending {
                            first
                        } else {
                            break;
                        };
                        match choose_start_placement(&game.state, pi) {
                            Some((tid, r, c2, rot)) => {
                                let _ = apply_start_placement(&mut game.state, pi, tid, r, c2, rot);
                            }
                            None => break,
                        }
                    } else if game.state.phase == Phase::Drafting {
                        let round = game.state.round_number;
                        let need_this_round = target_rounds.contains(&round)
                            && taus.get(&round).map(|v| v.len()).unwrap_or(0) < n_states_per_round;
                        let actions = drafting_actions(&game.state);
                        if need_this_round && actions.len() > 1 {
                            let mover = game.state.current_player;
                            let sampled: Vec<_> = if actions.len() > max_children {
                                let mut idxs: Vec<usize> = (0..actions.len()).collect();
                                idxs.shuffle(&mut rng);
                                idxs.truncate(max_children);
                                idxs.into_iter().map(|i| actions[i].clone()).collect()
                            } else {
                                actions.clone()
                            };
                            let mut pairs: Vec<(f64, f64)> = Vec::new();
                            for act in &sampled {
                                let mut g2 = Game { state: game.state.clone() };
                                if g2.apply_drafting(act).is_ok() {
                                    let feats = state_to_features_direct(&g2.state);
                                    let net_mover_val = net
                                        .eval(&feats)
                                        .map(|(_, v, _, _)| {
                                            1.0 - (v.first().copied().unwrap_or(0.0) as f64 + 1.0) / 2.0
                                        })
                                        .unwrap_or(0.5);
                                    let dfs_mover_val = crate::mcts::evaluate(&g2.state, 0)[mover];
                                    pairs.push((net_mover_val, dfs_mover_val));
                                }
                            }
                            if pairs.len() >= 2 {
                                let tau = kendall_tau(&pairs);
                                taus.entry(round).or_default().push(tau);
                                sib_counts.entry(round).or_default().push(pairs.len());
                            }
                        }
                        if actions.is_empty() {
                            break;
                        }
                        let s = net_effective_sims(walk_sims, actions.len());
                        match net_search_drafting_action(&net, &game.state, s, 1.5, false, &mut rng_game) {
                            Some(act) => {
                                apply_chosen_action(&mut game, act);
                            }
                            None => break,
                        }
                    } else {
                        break;
                    }
                }
                Phase::Tiling => {
                    let pi = game.state.current_player;
                    match resolve_tiling_step(&game.state, pi) {
                        TilingStep::Place(ta) => {
                            let _ = game.apply_single_tiling(pi, &ta);
                        }
                        TilingStep::Chips { row, chips } => {
                            apply_bonus_chips_with(&mut game.state.players[pi], row, &chips);
                        }
                        TilingStep::End => {
                            let _ = game.apply_tiling(&TilingMove::EndTiling { player: pi }, &mut rng_game);
                        }
                    }
                }
                _ => break,
            }
        }
    }

    let mut result = serde_json::Map::new();
    for &round in &target_rounds {
        let round_taus = taus.get(&round).cloned().unwrap_or_default();
        let n = round_taus.len();
        let mean = if n > 0 { round_taus.iter().sum::<f64>() / n as f64 } else { 0.0 };
        let avg_sib = sib_counts
            .get(&round)
            .map(|v| v.iter().sum::<usize>() as f64 / v.len().max(1) as f64)
            .unwrap_or(0.0);
        result.insert(
            format!("round_{round}"),
            json!({ "n_states": n, "mean_kendall_tau": mean, "avg_siblings": avg_sib }),
        );
    }
    Ok(serde_json::to_string(&Value::Object(result)).unwrap_or_else(|_| "{}".to_string()))
}

/// Bindungs-Check für Fund 6 (Nutzer-Auftrag, 2026-07-20): BEVOR mehr Arbeit
/// in die Kuppelstapel-Determinisierung fließt -- der `SHUFFLE_STACK_PEEK_
/// IN_SEARCH`-Test (17%→9% Siege, siehe net_mcts.rs) deutet schon darauf
/// hin, dass die durch Neumischen eingeführte Varianz größer war als der
/// eigentliche Orakel-Bias. Misst direkt: (a) wie oft `DrawStackPeek` unter
/// den legalen Aktionen ist bzw. von der Netz-Suche tatsächlich GESPIELT
/// wird, (b) an tatsächlich gespielten Peek-Entscheidungen die Wertspanne
/// (max-min) des Netz-Blattwerts über ALLE aktuell im `dome_tile_pool`
/// verbleibenden Platten-Identitäten (statt der einen echten) -- kleine
/// Spanne/seltene Peeks == der Orakel-Bias ist marginal, Fund 6 gehört ans
/// Ende der Liste. Läuft die Netz-eigene Suche ein Spiel weit (realistische
/// Zustandsverteilung, `walk_sims` moderat), aggregiert nach Runde.
pub fn draw_stack_peek_impact_diagnostic(
    model_path: &str,
    n_games: usize,
    walk_sims: u32,
    seed: u64,
) -> Result<String, String> {
    let net = Net::load(model_path, crate::features::INPUT_SIZE).map_err(|e| e.to_string())?;
    let mut rng = StdRng::seed_from_u64(seed);
    let mut total_decisions: std::collections::HashMap<u32, u64> = std::collections::HashMap::new();
    let mut peek_offered: std::collections::HashMap<u32, u64> = std::collections::HashMap::new();
    let mut peek_chosen: std::collections::HashMap<u32, u64> = std::collections::HashMap::new();
    let mut value_spreads: std::collections::HashMap<u32, Vec<f64>> = std::collections::HashMap::new();

    for game_idx in 0..n_games {
        let names = ["A".to_string(), "B".to_string()];
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let mut rng_game = StdRng::seed_from_u64(
            seed.wrapping_add((game_idx as u64 + 1).wrapping_mul(0x9E37_79B9_7F4A_7C15)),
        );
        let mut game = Game::start(names, 0, ids, &mut rng_game);
        let t_start = std::time::Instant::now();
        let mut guard = 0u32;
        while guard < 2000 && t_start.elapsed().as_secs() < 120 {
            guard += 1;
            match game.state.phase {
                Phase::StartPlacement | Phase::Drafting => {
                    if game.state.players.iter().any(|p| p.start_tile_pending) {
                        let first = game.state.current_player;
                        let non_starter = 1 - first;
                        let pi = if game.state.players[non_starter].start_tile_pending {
                            non_starter
                        } else if game.state.players[first].start_tile_pending {
                            first
                        } else {
                            break;
                        };
                        match choose_start_placement(&game.state, pi) {
                            Some((tid, r, c2, rot)) => {
                                let _ = apply_start_placement(&mut game.state, pi, tid, r, c2, rot);
                            }
                            None => break,
                        }
                    } else if game.state.phase == Phase::Drafting {
                        let round = game.state.round_number;
                        let actions = drafting_actions(&game.state);
                        if actions.is_empty() {
                            break;
                        }
                        *total_decisions.entry(round).or_insert(0) += 1;
                        let offers_peek = actions.contains(&Action::DrawStackPeek);
                        if offers_peek {
                            *peek_offered.entry(round).or_insert(0) += 1;
                        }
                        let s = net_effective_sims(walk_sims, actions.len());
                        let chosen = match net_search_drafting_action(&net, &game.state, s, 1.5, false, &mut rng_game)
                        {
                            Some(act) => act,
                            None => break,
                        };
                        if chosen == Action::DrawStackPeek {
                            *peek_chosen.entry(round).or_insert(0) += 1;
                            let pool = game.state.dome_tile_pool.clone();
                            let mover = game.state.current_player;
                            if pool.len() >= 2 {
                                let mut vals: Vec<f64> = Vec::new();
                                for tile in &pool {
                                    let mut hypo = game.state.clone();
                                    hypo.players[mover].apply_score(-1);
                                    hypo.pending_stack_draw.push(tile.clone());
                                    let feats = state_to_features_direct(&hypo);
                                    if let Ok((_, v, _, _)) = net.eval(&feats) {
                                        vals.push((v.first().copied().unwrap_or(0.0) as f64 + 1.0) / 2.0);
                                    }
                                }
                                if vals.len() >= 2 {
                                    let lo = vals.iter().cloned().fold(f64::INFINITY, f64::min);
                                    let hi = vals.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
                                    value_spreads.entry(round).or_default().push(hi - lo);
                                }
                            }
                        }
                        apply_chosen_action(&mut game, chosen);
                    } else {
                        break;
                    }
                }
                Phase::Tiling => {
                    let pi = game.state.current_player;
                    match resolve_tiling_step(&game.state, pi) {
                        TilingStep::Place(ta) => {
                            let _ = game.apply_single_tiling(pi, &ta);
                        }
                        TilingStep::Chips { row, chips } => {
                            apply_bonus_chips_with(&mut game.state.players[pi], row, &chips);
                        }
                        TilingStep::End => {
                            let _ = game.apply_tiling(&TilingMove::EndTiling { player: pi }, &mut rng_game);
                        }
                    }
                }
                _ => break,
            }
        }
    }

    let mut result = serde_json::Map::new();
    for round in 1..=5u32 {
        let total = *total_decisions.get(&round).unwrap_or(&0);
        let offered = *peek_offered.get(&round).unwrap_or(&0);
        let chosen = *peek_chosen.get(&round).unwrap_or(&0);
        let spreads = value_spreads.get(&round).cloned().unwrap_or_default();
        let n_spread = spreads.len();
        let mean_spread = if n_spread > 0 { spreads.iter().sum::<f64>() / n_spread as f64 } else { 0.0 };
        let max_spread = spreads.iter().cloned().fold(0.0f64, f64::max);
        result.insert(
            format!("round_{round}"),
            json!({
                "total_decisions": total,
                "peek_offered": offered,
                "peek_chosen": chosen,
                "peek_chosen_rate": if total > 0 { chosen as f64 / total as f64 } else { 0.0 },
                "n_value_spread_samples": n_spread,
                "mean_value_spread": mean_spread,
                "max_value_spread": max_spread,
            }),
        );
    }
    Ok(serde_json::to_string(&Value::Object(result)).unwrap_or_else(|_| "{}".to_string()))
}

/// Noise-Floor-Test für eine beliebige Runde (`evaluations/value head
/// tests.txt`, Punkt 1 -- externer Kollegen-Vorschlag, "wichtigster Test,
/// weil er den Lösungsraum halbiert"; ursprünglich nur für Runde 1, auf
/// Nutzer-Wunsch 2026-07-21 auf `target_round` verallgemeinert, um
/// Runde 2/3 vergleichbar zu prüfen): wie viel Value-R² ist in
/// `target_round` ÜBERHAUPT erreichbar, selbst wenn ein Head das Ziel
/// perfekt lernen würde? Sampelt `n_states` realistische
/// `target_round`-Entscheidungspunkte per Heuristik-Walk (KEINE Netz-
/// Abhängigkeit -- das Ziel ist eine Eigenschaft des LABELS, nicht eines
/// bestimmten Modells) und spielt je Zustand `k_rollouts`
/// unabhängige Heuristik-Fortsetzungen bis Spielende (Beutel/Kuppelstapel
/// je Wiederholung neu gemischt, gleiches Determinisierungs-Muster wie
/// `mean_rollout_diff`, verifiziert per
/// `rollout_repetitions_actually_diverge_in_bag_and_dome_order`).
///
/// Label = aktuelle Value-Zielformel (VALUE_SCHEMA_VERSION=15, Fund 7):
/// `tanh((own_unclamped - opp_unclamped) / VALUE_SCALE)`, aus der Sicht des
/// Spielers, der am gesampelten Zustand am Zug ist.
///
/// Varianzzerlegung (Einweg-Zufallseffekte-Modell/ANOVA, NICHT die naive
/// Varianz der Rollout-Mittelwerte -- Bias-Fix, 2026-07-20, Nutzer-Anstoss
/// nach dem ersten Lauf dieser Diagnose): die beobachtete Varianz der
/// Rollout-MITTELWERTE über die Zustände schätzt `Var(E[y|s]) +
/// E[Var(y|s)]/k_rollouts`, NICHT `Var(E[y|s])` allein -- jeder Mittelwert
/// ist selbst nur aus `k_rollouts` Stichproben geschätzt, der
/// Standardfehler dieser Schätzung geht sonst fälschlich als erklärbare
/// Signal-Varianz durch. Korrektur: `Var(E[y|s])_korrigiert =
/// Var(Mittelwerte)_beobachtet - E[Var(y|s)]/k_rollouts` (kann durch
/// Stichprobenrauschen leicht negativ ausfallen, wenn der wahre Wert nahe
/// 0 liegt -- für die R²-Berechnung bei 0 gekappt). Maximal erreichbares
/// R² = `Var(E[y|s])_korrigiert / Var(y)`. Deckel ~0.05-0.1: Runde-1-
/// Rauschen ist eine Eigenschaft des Ziels selbst (kein Lern-/Feature-
/// Problem lösbar) -- das Ziel müsste geändert werden (z.B. TD-/
/// Rundenübergangs-Bootstrap-Labels). Deckel 0.3+: echtes, noch nicht
/// ausgeschöpftes Lernpotenzial. Der Korrekturterm skaliert mit
/// `1/k_rollouts` -- NICHT mit `n_states` -- ein größeres `k_rollouts`
/// (statt mehr Zustände) macht die Schätzung präziser.
pub fn value_noise_floor_diagnostic(
    n_states: usize,
    k_rollouts: usize,
    walk_sims: u32,
    rollout_sims: u32,
    target_round: u32,
    seed: u64,
) -> Result<String, String> {
    // Phase 1 (billig, sequenziell): `n_states` `target_round`-
    // Entscheidungspunkte per Heuristik-Walk sammeln -- höchstens 1 je
    // Partie (Diversität über verschiedene Trajektorien statt mehrfach aus
    // derselben, analog `sibling_ranking_diagnostic`).
    let mut rng = StdRng::seed_from_u64(seed);
    let mut sampled_states: Vec<GameState> = Vec::with_capacity(n_states);
    let mut game_idx = 0u64;
    while sampled_states.len() < n_states && game_idx < (n_states as u64) * 6 + 20 {
        game_idx += 1;
        let names = ["A".to_string(), "B".to_string()];
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let mut rng_game =
            StdRng::seed_from_u64(seed.wrapping_add(game_idx.wrapping_mul(0x9E37_79B9_7F4A_7C15)));
        let mut game = Game::start(names, 0, ids, &mut rng_game);
        let t_start = std::time::Instant::now();
        let mut guard = 0u32;
        let mut collected_this_game = false;
        while guard < 500 && t_start.elapsed().as_secs() < 60 {
            guard += 1;
            match game.state.phase {
                Phase::StartPlacement | Phase::Drafting => {
                    if game.state.players.iter().any(|p| p.start_tile_pending) {
                        let first = game.state.current_player;
                        let non_starter = 1 - first;
                        let pi = if game.state.players[non_starter].start_tile_pending {
                            non_starter
                        } else if game.state.players[first].start_tile_pending {
                            first
                        } else {
                            break;
                        };
                        match choose_start_placement(&game.state, pi) {
                            Some((tid, r, c2, rot)) => {
                                let _ = apply_start_placement(&mut game.state, pi, tid, r, c2, rot);
                            }
                            None => break,
                        }
                    } else if game.state.phase == Phase::Drafting {
                        let actions = drafting_actions(&game.state);
                        if actions.is_empty() {
                            break;
                        }
                        if !collected_this_game && game.state.round_number == target_round && actions.len() > 1 {
                            collected_this_game = true;
                            sampled_states.push(game.state.clone());
                            if sampled_states.len() >= n_states {
                                break;
                            }
                        }
                        // Hauptspiel per Heuristik weiterführen (Walk zum
                        // nächsten realistischen Zustand), unabhängig davon
                        // ob dieser Schritt gesampelt wurde.
                        let s = dynamic_sims(walk_sims, actions.len());
                        let a = search_drafting_action(&game.state, s, 1.5, &mut rng)
                            .unwrap_or_else(|| actions[0].clone());
                        let _ = game.apply_drafting(&a);
                    } else {
                        break;
                    }
                }
                Phase::Tiling => {
                    tiling_step(&mut game, &mut rng);
                }
                _ => break,
            }
        }
    }

    // Phase 2 (teuer, RAYON-PARALLEL über die Zustände): je Zustand
    // `k_rollouts` unabhängige Heuristik-Fortsetzungen bis Spielende
    // (Beutel/Kuppelstapel je Wiederholung neu gemischt, gleiches
    // Determinisierungs-Muster wie `mean_rollout_diff`, verifiziert per
    // `rollout_repetitions_actually_diverge_in_bag_and_dome_order`).
    // Deterministisch trotz Parallelität: jeder Zustands-Index bekommt
    // seinen EIGENEN, vom Index abgeleiteten RNG-Strom.
    let results: Vec<(f64, f64)> = sampled_states
        .par_iter()
        .enumerate()
        .filter_map(|(idx, sample_state)| {
            let mut rng = StdRng::seed_from_u64(seed.wrapping_add((idx as u64).wrapping_mul(0xD1B5_4A32_D192_ED03)));
            let player = sample_state.current_player;
            let opp = 1 - player;
            let mut ys: Vec<f64> = Vec::with_capacity(k_rollouts);
            for _ in 0..k_rollouts {
                let mut g2 = Game { state: sample_state.clone() };
                g2.state.bag.tiles.shuffle(&mut rng);
                g2.state.dome_tile_pool.shuffle(&mut rng);
                let mut rguard = 0u32;
                loop {
                    rguard += 1;
                    if rguard > 4000 {
                        break;
                    }
                    match g2.state.phase {
                        Phase::StartPlacement | Phase::Drafting => {
                            if g2.state.players.iter().any(|p| p.start_tile_pending) {
                                if start_placement_step(&mut g2, &mut rng).is_none() {
                                    break;
                                }
                            } else if g2.state.phase == Phase::Drafting {
                                let acts = drafting_actions(&g2.state);
                                if acts.is_empty() {
                                    break;
                                }
                                let a = if acts.len() == 1 {
                                    acts[0].clone()
                                } else {
                                    let s = dynamic_sims(rollout_sims, acts.len());
                                    search_drafting_action(&g2.state, s, 1.5, &mut rng)
                                        .unwrap_or_else(|| acts[0].clone())
                                };
                                let _ = g2.apply_drafting(&a);
                            } else {
                                break;
                            }
                        }
                        Phase::Tiling => {
                            tiling_step(&mut g2, &mut rng);
                        }
                        _ => break,
                    }
                }
                if g2.state.phase == Phase::End {
                    let _ = g2.apply_end_scoring();
                }
                let own = g2.state.players[player].score_unclamped as f64;
                let opp_s = g2.state.players[opp].score_unclamped as f64;
                ys.push(((own - opp_s) / crate::mcts::VALUE_SCALE).tanh());
            }
            if ys.len() < 2 {
                return None;
            }
            let n = ys.len() as f64;
            let mean = ys.iter().sum::<f64>() / n;
            // UNVERZERRTE Stichprobenvarianz (÷(k-1), Bessel-Korrektur) --
            // wird unten fuer die Between-States-Bias-Korrektur gebraucht
            // (siehe Kommentar dort). Mit ÷k allein waere dieser Schaetzer
            // selbst schon leicht nach unten verzerrt.
            let var = ys.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / (n - 1.0);
            Some((mean, var))
        })
        .collect();
    let (state_means, state_vars): (Vec<f64>, Vec<f64>) = results.into_iter().unzip();

    let n = state_means.len();
    if n < 2 {
        return Err(format!("Zu wenige auswertbare Runde-1-Zustände gesammelt ({n}/{n_states})"));
    }
    let grand_mean = state_means.iter().sum::<f64>() / n as f64;
    // Beobachtete Varianz der ROLLOUT-MITTELWERTE ueber die Zustaende --
    // schaetzt NICHT direkt Var(E[y|s]) (den erklaerbaren Anteil), sondern
    // Var(E[y|s]) + E[Var(y|s)]/k, weil jeder Mittelwert selbst nur aus
    // k_rollouts Stichproben geschaetzt ist (Standardfehler der
    // Mittelwertbildung geht mit rein). Ohne Korrektur wuerde dieser
    // "Rausch-Aufschlag" faelschlich als erklaerbare Signal-Varianz
    // gezaehlt -- Bug im ersten Lauf dieser Diagnose (2026-07-20, vom
    // Nutzer angestossen), hier behoben.
    let var_between_raw = state_means.iter().map(|m| (m - grand_mean).powi(2)).sum::<f64>() / (n as f64 - 1.0);
    let var_within_mean = state_vars.iter().sum::<f64>() / n as f64;
    // Bias-Korrektur (Einweg-Zufallseffekte-Modell, analog ANOVA):
    // Var(E[y|s])_korrigiert = Var(Mittelwerte)_beobachtet - E[Var(y|s)]/k.
    // Kann durch Stichprobenrauschen leicht negativ ausfallen, wenn der
    // wahre Wert nahe 0 liegt -- fuer die R²-Berechnung bei 0 gekappt
    // (eine Varianz kann nicht negativ sein), der ungekappte Wert bleibt
    // im JSON sichtbar (wichtig fuer die Einordnung "nahe Null" vs.
    // "eindeutig positiv").
    let var_between_corrected = var_between_raw - var_within_mean / k_rollouts as f64;
    let var_between_corrected_clamped = var_between_corrected.max(0.0);
    let var_total = var_between_corrected_clamped + var_within_mean;
    let max_r2 = if var_total > 1e-12 { var_between_corrected_clamped / var_total } else { f64::NAN };
    // Unkorrigierter Wert (Bug des ersten Laufs) bleibt zum Vergleich im
    // JSON -- NICHT als max_achievable_r2 verwenden, siehe Kommentar oben.
    let var_total_naive = var_between_raw + var_within_mean;
    let max_r2_naive_biased =
        if var_total_naive > 1e-12 { var_between_raw / var_total_naive } else { f64::NAN };

    Ok(json!({
        "target_round": target_round,
        "n_states": n,
        "k_rollouts": k_rollouts,
        "var_between_states_raw_biased": var_between_raw,
        "var_between_states_corrected": var_between_corrected,
        "var_within_state_mean": var_within_mean,
        "max_achievable_r2_naive_biased": max_r2_naive_biased,
        "var_total": var_total,
        "max_achievable_r2": max_r2,
    })
    .to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Zaehlt alle Vorkommen von `color` im GESAMTEN Spielzustand: Beutel,
    /// Turm, alle Fabriken (Sun+Mond), Spielerreihen, Strafleiste, verlegte
    /// Kuppel-Spaces. Grundlage fuer den Bilanz-Sanity-Check unten (Basis fuer
    /// das geplante Beutel-Farbanteil-Feature, siehe stage2_investigation.md).
    fn count_color(state: &GameState, color: crate::tile::TileColor) -> usize {
        let mut n = 0;
        n += state.bag.tiles.iter().filter(|&&c| c == color).count();
        n += state.tower.tiles.iter().filter(|&&c| c == color).count();
        for f in &state.factories {
            n += f.sun_tiles.iter().filter(|&&c| c == color).count();
            for stack in &f.moon_stacks {
                n += stack.iter().filter(|&&c| c == color).count();
            }
        }
        n += state.large_factory.sun_tiles.iter().filter(|&&c| c == color).count();
        n += state.large_factory.moon_pool.iter().filter(|&&c| c == color).count();
        for p in &state.players {
            for pl in &p.pattern_lines {
                // Phantom-Fliesen (per Bonuschip virtuell ergaenzt, siehe
                // PatternLine::phantom_count) sind nie real gezogen worden --
                // ausklammern, sonst waere die Zahl kurzzeitig aufgeblaeht,
                // solange die Reihe noch nicht getilt ist.
                let raw = pl.tiles.iter().filter(|&&c| c == color).count();
                let phantom_here = if pl.color == Some(color) { pl.phantom_count.min(raw) } else { 0 };
                n += raw - phantom_here;
            }
            n += p.broken_tiles.iter().filter(|&&c| c == color).count();
            for row in &p.dome_grid.dome_slots {
                for slot in row.iter().flatten() {
                    for sp in &slot.spaces {
                        if sp.placed_color == Some(color) {
                            n += 1;
                        }
                    }
                }
            }
        }
        n
    }

    /// Sanity-Check (Nutzer-Anstoss, siehe stage2_investigation.md): Beutel +
    /// Turm + alles sichtbar auf dem Spielfeld muss je Farbe IMMER EXAKT der
    /// festen Gesamtzahl (`TILES_PER_COLOR`=13) entsprechen -- die
    /// Gesamtanzahl je Farbe im Spiel aendert sich nie (Nutzer-Bestaetigung).
    /// Frueher nur `>=` geprueft: Bonus-Chip-Komplettierung
    /// (`apply_bonus_chips_with`, round_end.rs) schiebt "Phantom"-Fliesen
    /// direkt in `pattern_lines[row].tiles`, OHNE sie aus Beutel/Turm zu
    /// ziehen -- das ist beabsichtigtes Spieldesign (Chips geben rein
    /// virtuelle Fliesen). Frueher wanderten diese Phantome beim Tiling/bei
    /// unplatzierbaren Reihen faelschlich als "echte" Fliesen in Turm/
    /// Strafleiste (`PatternLine::phantom_count` in `execute_tiling_action`
    /// bzw. `process_unplaceable_rows` beruecksichtigt das jetzt). WICHTIG
    /// fuer das Beutel-Farbanteil-Feature: der Mechanismus fasst NUR
    /// `pattern_lines` an, NIE `bag`/`tower` direkt -- direktes Auslesen von
    /// `state.bag.tiles` bleibt exakt korrekt als "was noch wirklich zu
    /// ziehen ist".
    #[test]
    fn tile_color_accounting_invariant_holds_throughout_random_games() {
        use crate::tile::TILES_PER_COLOR;
        let mut rng = StdRng::seed_from_u64(777);
        for gi in 0..25u64 {
            let ids = sample_valid_scoring_ids(3, &mut rng);
            let mut game = Game::start([format!("A{gi}"), format!("B{gi}")], (gi % 2) as usize, ids, &mut rng);
            let mut guard = 0u32;
            loop {
                guard += 1;
                if guard > 3000 {
                    break;
                }
                match game.state.phase {
                    Phase::StartPlacement | Phase::Drafting => {
                        if game.state.players.iter().any(|p| p.start_tile_pending) {
                            if start_placement_step(&mut game, &mut rng).is_none() {
                                break;
                            }
                        } else if game.state.phase == Phase::Drafting {
                            let actions = drafting_actions(&game.state);
                            if actions.is_empty() {
                                break;
                            }
                            let a = actions.choose(&mut rng).cloned().unwrap_or(Action::Pass);
                            let _ = game.apply_drafting(&a);
                        } else {
                            break;
                        }
                    }
                    Phase::Tiling => {
                        tiling_step(&mut game, &mut rng);
                    }
                    _ => break,
                }
                for &color in &crate::tile::TileColor::NORMAL {
                    let n = count_color(&game.state, color);
                    if n != TILES_PER_COLOR {
                        let bag = game.state.bag.tiles.iter().filter(|&&c| c == color).count();
                        let tower = game.state.tower.tiles.iter().filter(|&&c| c == color).count();
                        let fac_sun: usize = game.state.factories.iter().map(|f| f.sun_tiles.iter().filter(|&&c| c == color).count()).sum();
                        let fac_moon: usize = game.state.factories.iter().map(|f| f.moon_stacks.iter().flatten().filter(|&&c| c == color).count()).sum();
                        let lf_sun = game.state.large_factory.sun_tiles.iter().filter(|&&c| c == color).count();
                        let lf_moon = game.state.large_factory.moon_pool.iter().filter(|&&c| c == color).count();
                        for (pi, p) in game.state.players.iter().enumerate() {
                            let pl: usize = p.pattern_lines.iter().map(|l| l.tiles.iter().filter(|&&c| c == color).count()).sum();
                            let broken = p.broken_tiles.iter().filter(|&&c| c == color).count();
                            let dome: usize = p.dome_grid.dome_slots.iter().flatten().flatten()
                                .map(|t| t.spaces.iter().filter(|sp| sp.placed_color == Some(color)).count()).sum();
                            let phantoms: Vec<(usize, usize, usize)> = p.pattern_lines.iter()
                                .filter(|l| l.phantom_count > 0)
                                .map(|l| (l.row_index, l.phantom_count, l.tiles.len()))
                                .collect();
                            eprintln!("  Spieler {pi}: pattern_lines={pl} broken={broken} dome={dome} phantom(row,cnt,tiles_len)={phantoms:?}");
                        }
                        eprintln!(
                            "  bag={bag} tower={tower} fac_sun={fac_sun} fac_moon={fac_moon} lf_sun={lf_sun} lf_moon={lf_moon}"
                        );
                    }
                    assert!(
                        n == TILES_PER_COLOR,
                        "Spiel {gi}, Schritt {guard}, Phase {:?}: Farbe {color:?} zaehlt {n}, erwartet genau {TILES_PER_COLOR}",
                        game.state.phase,
                    );
                }
            }
        }
    }

    /// Diagnose (Nutzer-Anstoss): koennen zwei Rollout-Wiederholungen ab
    /// DEMSELBEN geklonten Zustand ueberhaupt unterschiedliche Beutel-/
    /// Kuppelstapel-Ziehungen erleben, wenn sie nur mit unabhaengigem RNG
    /// weiterspielen? `draw_with_refill` mischt den Beutel NUR neu, wenn er
    /// nicht genug Fliesen fuer die Anfrage hat (state.rs) -- der
    /// Kuppelstapel wird NUR EINMAL beim Spielstart gemischt (setup_new_game),
    /// nie wieder. Reicht der Vorrat innerhalb des Rollout-Horizonts, wuerden
    /// ALLE Wiederholungen dieselbe schon feststehende Reihenfolge
    /// durchspielen -- keine echte Zufallsmittelung (Weg-1-Determinisierung
    /// waere dann ein No-Op fuer diese beiden Zufallsquellen).
    #[test]
    fn rollout_repetitions_actually_diverge_in_bag_and_dome_order() {
        let mut base_rng = StdRng::seed_from_u64(555);
        let ids = sample_valid_scoring_ids(3, &mut base_rng);
        let names = ["A".to_string(), "B".to_string()];
        let mut base = Game::start(names, 0, ids, &mut base_rng);
        // Bis zum Start von Runde 1 (Startkacheln legen), damit wir eine
        // echte fruehe Runde-1-Drafting-Entscheidung als Ausgangspunkt haben.
        while base.state.players.iter().any(|p| p.start_tile_pending) {
            if start_placement_step(&mut base, &mut base_rng).is_none() {
                break;
            }
        }
        let snapshot = base.state.clone();

        let mut results: Vec<(Vec<crate::tile::TileColor>, Vec<usize>)> = Vec::new();
        for rep_seed in [1001u64, 2002, 3003] {
            let mut rng = StdRng::seed_from_u64(rep_seed);
            let mut g = Game { state: snapshot.clone() };
            // Derselbe Fix wie in mean_rollout_diff: unbekanntes neu auswuerfeln.
            g.state.bag.tiles.shuffle(&mut rng);
            g.state.dome_tile_pool.shuffle(&mut rng);
            let mut guard = 0u32;
            // Bis mindestens EINE Runde weiter (next_round() also mind. 1x
            // durchlaufen) -- entspricht ungefaehr horizon_rounds=2.
            let start_round = g.state.round_number;
            loop {
                guard += 1;
                if guard > 5000 || g.state.round_number > start_round + 1 {
                    break;
                }
                match g.state.phase {
                    Phase::StartPlacement | Phase::Drafting => {
                        if g.state.players.iter().any(|p| p.start_tile_pending) {
                            if start_placement_step(&mut g, &mut rng).is_none() {
                                break;
                            }
                        } else if g.state.phase == Phase::Drafting {
                            let actions = drafting_actions(&g.state);
                            if actions.is_empty() {
                                break;
                            }
                            let a = actions.choose(&mut rng).cloned().unwrap_or(Action::Pass);
                            let _ = g.apply_drafting(&a);
                        } else {
                            break;
                        }
                    }
                    Phase::Tiling => {
                        tiling_step(&mut g, &mut rng);
                    }
                    _ => break,
                }
            }
            let dome_ids: Vec<usize> = g.state.dome_tile_pool.iter().map(|t| t.tile_id).collect();
            results.push((g.state.bag.tiles.clone(), dome_ids));
        }

        let all_bag_identical = results.windows(2).all(|w| w[0].0 == w[1].0);
        let all_dome_identical = results.windows(2).all(|w| w[0].1 == w[1].1);
        for (i, (bag, dome)) in results.iter().enumerate() {
            eprintln!("  Rep {i}: bag_len={} dome_pool_ids={:?}", bag.len(), dome);
        }
        // Mit dem Determinisierungs-Fix (shuffle vor Rollout-Fortsetzung)
        // MUESSEN unabhaengige Wiederholungen unterschiedliche Beutel-/
        // Kuppelstapel-Reihenfolgen sehen -- sonst ist Weg 1 (Mittelung ueber
        // ausgewuerfelte Welten) fuer diese beiden Zufallsquellen ein No-Op.
        assert!(!all_bag_identical, "Beutel-Reihenfolge identisch ueber alle Wiederholungen -- Determinisierung wirkungslos");
        assert!(!all_dome_identical, "Kuppelstapel-Reihenfolge identisch ueber alle Wiederholungen -- Determinisierung wirkungslos");
    }

    /// `resolve_and_apply_stack_draw` muss immer zu einer gueltig platzierten
    /// Kachel fuehren: mindestens 1 Pflichtzug, `pending_stack_draw` danach
    /// wieder leer, Zug beendet (Token verbraucht, Spieler gewechselt).
    #[test]
    fn resolve_and_apply_stack_draw_produces_valid_placement() {
        let mut rng = StdRng::seed_from_u64(42);
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let mut state = crate::state::setup_new_game(["A".into(), "B".into()], 0, &mut rng);
        state.scoring_tile_ids = ids;
        for p in state.players.iter_mut() {
            p.start_tile_pending = false;
        }
        assert!(state.dome_tile_pool.len() > 1, "Test braucht einen Pool mit mehreren Kacheln");
        let mut game = Game { state };

        let final_action = resolve_and_apply_stack_draw(&mut game);
        match final_action {
            Action::ChooseDrawStackSlot(m) => {
                assert!(
                    game.state.players[0].dome_grid.dome_slots[m.slot_row][m.slot_col].is_some(),
                    "gewaehlte Kachel muss im Raster liegen"
                );
            }
            other => panic!("erwartet Action::ChooseDrawStackSlot, bekommen {other:?}"),
        }
        assert!(game.state.pending_stack_draw.is_empty(), "Zieh-Vorgang muss abgeschlossen sein");
        assert_eq!(game.state.players[0].player_tokens_used, 1, "genau 1 Token verbraucht");
        assert_eq!(game.state.current_player, 1, "Zug muss beendet sein (Spielerwechsel)");
    }

    /// Wenn eine Kachel um ein Vielfaches wertvoller ist als alle anderen im
    /// Pool (hier kuenstlich uebertrieben: 4 Wild-Spaces + Bonus, real
    /// erreichen Katalog-Kacheln das nie -- reine Mechanismus-Pruefung), muss
    /// die sequenzielle Aufloesung sie zuverlaessig finden (deterministisch,
    /// kein Zufall mehr -- der Erwartungswert-Vergleich nutzt die exakte
    /// Rest-Pool-Zusammensetzung, kein Resampling noetig).
    #[test]
    fn resolve_and_apply_stack_draw_finds_high_value_tile_when_worthwhile() {
        use crate::dome::{DomeSpace, DomeTile};
        let junk = || DomeTile::new(
            0,
            vec![
                DomeSpace::normal(TileColor::Rot),
                DomeSpace::normal(TileColor::Blau),
                DomeSpace::normal(TileColor::Gelb),
                DomeSpace::normal(TileColor::Schwarz),
            ],
            0,
        );
        let jackpot = DomeTile::new(
            1,
            vec![DomeSpace::wild(), DomeSpace::wild(), DomeSpace::wild(), DomeSpace::wild()],
            3,
        );

        let mut rng = StdRng::seed_from_u64(9000);
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let mut state = crate::state::setup_new_game(["A".into(), "B".into()], 0, &mut rng);
        state.scoring_tile_ids = ids;
        for p in state.players.iter_mut() {
            p.start_tile_pending = false;
        }
        // Jackpot ganz unten im Stapel -- nur per Weiterziehen erreichbar.
        state.dome_tile_pool = vec![junk(), junk(), junk(), jackpot.clone()];
        let mut game = Game { state };

        let final_action = resolve_and_apply_stack_draw(&mut game);
        match final_action {
            Action::ChooseDrawStackSlot(m) => assert_eq!(
                m.chosen_id, jackpot.tile_id,
                "haette die wertvolle Kachel waehlen sollen, es lohnt sich klar weiterzuziehen"
            ),
            other => panic!("erwartet Action::ChooseDrawStackSlot, bekommen {other:?}"),
        }
    }

    #[test]
    fn play_one_game_terminates_with_records() {
        let mut rng = StdRng::seed_from_u64(123);
        let ids = sample_valid_scoring_ids(3, &mut rng);
        let recs = play_one_game(
            40,
            SELF_PLAY_C,
            ids,
            ["P0".into(), "P1".into()],
            0,
            "test_g1",
            &mut rng,
            None,
            None,
        );
        assert!(!recs.is_empty(), "Spiel muss Records erzeugen");
        for r in &recs {
            let o = r.as_object().unwrap();
            for key in ["state", "policy", "valid_actions", "player", "scores", "winner", "game_id"] {
                assert!(o.contains_key(key), "Record fehlt Key {key}");
            }
            // Policy-Wahrscheinlichkeiten summieren ~1.
            let sum: f64 = o["policy"]
                .as_array()
                .unwrap()
                .iter()
                .map(|p| p["prob"].as_f64().unwrap())
                .sum();
            assert!((sum - 1.0).abs() < 1e-6, "Policy-Summe {sum} ≠ 1");
            // Jede Policy-Aktion ist in valid_actions enthalten (Maskenkonsistenz).
            let valid = o["valid_actions"].as_array().unwrap();
            for p in o["policy"].as_array().unwrap() {
                let pa = &p["action"];
                assert!(
                    valid.iter().any(|v| env_action_eq(v, pa)),
                    "Policy-Aktion {pa} nicht in valid_actions"
                );
            }
        }
    }

    /// Vergleicht zwei env-Action-Dicts über die Felder, die `action_to_id` liest.
    fn env_action_eq(a: &Value, b: &Value) -> bool {
        let keys = [
            "type",
            "factory_index",
            "color",
            "row",
            "display_index",
            "slot_row",
            "slot_col",
            "rotation",
            "pattern_row",
        ];
        keys.iter().all(|k| a.get(k) == b.get(k))
    }

    #[test]
    fn run_self_play_returns_valid_json() {
        let out = run_self_play(2, 30, SELF_PLAY_C, 7, 2, "vtest", None, None);
        let parsed: Value = serde_json::from_str(&out).unwrap();
        assert!(parsed.as_array().unwrap().len() > 0);
    }

    /// Task #71, Kern-Regressionsschutz Einzelspiel-Flush + Heartbeat: mit
    /// gesetzten `progress_path`/`heartbeat_path` muss (a) die JSONL-Datei
    /// GENAU eine Zeile je Spiel enthalten (nicht eine Zeile je Chunk), jede
    /// Zeile ein valides JSON-Array mit `game_id`, und (b) die Heartbeat-Datei
    /// existieren und einen positiven `moves_done`-Zähler enthalten.
    #[test]
    fn run_self_play_writes_per_game_progress_and_heartbeat() {
        let dir = std::env::temp_dir().join(format!("mosaic_progress_test_{}", std::process::id()));
        std::fs::create_dir_all(&dir).expect("Temp-Verzeichnis anlegen");
        let progress_path = dir.join("progress.jsonl");
        let heartbeat_path = dir.join("heartbeat.json");
        let _ = std::fs::remove_file(&progress_path);
        let _ = std::fs::remove_file(&heartbeat_path);

        let out = run_self_play(
            3, 30, SELF_PLAY_C, 123, 2, "vtest_progress",
            Some(progress_path.to_str().unwrap()),
            Some(heartbeat_path.to_str().unwrap()),
        );
        let parsed: Value = serde_json::from_str(&out).unwrap();
        assert!(parsed.as_array().unwrap().len() > 0);

        let jsonl = std::fs::read_to_string(&progress_path).expect("Fortschrittsdatei sollte existieren");
        let lines: Vec<&str> = jsonl.lines().filter(|l| !l.trim().is_empty()).collect();
        assert_eq!(lines.len(), 3, "erwartet genau eine JSONL-Zeile je Spiel (3 Spiele)");
        for line in &lines {
            let game: Value = serde_json::from_str(line).expect("jede Zeile muss valides JSON sein");
            let steps = game.as_array().expect("jede Zeile ist ein Array von Step-Records");
            assert!(!steps.is_empty(), "ein Spiel-Eintrag sollte nicht leer sein");
            assert!(steps[0].get("game_id").is_some(), "Step-Records sollten game_id tragen");
        }

        let hb = std::fs::read_to_string(&heartbeat_path).expect("Heartbeat-Datei sollte existieren");
        let hb_json: Value = serde_json::from_str(&hb).expect("Heartbeat-Datei muss valides JSON sein");
        assert!(
            hb_json["moves_done"].as_u64().unwrap_or(0) > 0,
            "Heartbeat sollte einen positiven Zug-Zaehler zeigen: {hb_json}"
        );
        assert_eq!(hb_json["games_done"].as_u64(), Some(3));

        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn arena_match_produces_results() {
        let out = run_arena_match(40, 60, 4, 99, 2, SELF_PLAY_C);
        let games: Value = serde_json::from_str(&out).unwrap();
        let arr = games.as_array().unwrap();
        assert_eq!(arr.len(), 4);
        for g in arr {
            assert!(g["scores"].as_array().unwrap().len() == 2);
            let w = g["winner"].as_u64().unwrap();
            assert!(w == 0 || w == 1);
            assert!(g["steps"].as_u64().unwrap() > 0);
            assert_eq!(g["floor_per_round"].as_array().unwrap().len(), 2);
        }
    }

    #[test]
    fn no_tiling_deadlock_across_seeds() {
        // Regression: ein Solver-`End` bei offenen (nur per neuer Kuppelplatte
        // legbaren) Reihen führte früher zu einer end_tiling-Endlosschleife
        // (bis zum 100k-Guard). Eine normale Partie hat wenige hundert Steps.
        for seed in 0..12u64 {
            let mut rng = StdRng::seed_from_u64(seed);
            let ids = sample_valid_scoring_ids(3, &mut rng);
            let recs = play_one_game(
                30,
                SELF_PLAY_C,
                ids,
                ["P0".into(), "P1".into()],
                (seed % 2) as usize,
                "seedcheck",
                &mut rng,
                None,
                None,
            );
            assert!(
                recs.len() < 3000,
                "Seed {seed}: {} Steps — Deadlock-Verdacht (Tiling-End-Schleife)",
                recs.len()
            );
            // Regression Policy-Leak: jede Policy-Aktion MUSS in valid_actions
            // liegen (sonst Target-Masse auf maskierter Aktion → Policy-Loss-
            // Explosion im Training). Traf früher seltene Tiling-Nicht-Top-Reihen.
            for r in &recs {
                let o = r.as_object().unwrap();
                let valid = o["valid_actions"].as_array().unwrap();
                for p in o["policy"].as_array().unwrap() {
                    let pa = &p["action"];
                    assert!(
                        valid.iter().any(|v| env_action_eq(v, pa)),
                        "Seed {seed}: Policy-Aktion {pa} nicht in valid_actions (Leak)"
                    );
                }
            }
        }
    }

    /// `action_to_id_direct` (Performance-Fix, Abschnitt D) muss für JEDE
    /// gesammelte Drafting-Aktion exakt dieselbe ID liefern wie der
    /// bisherige JSON-Umweg (`action_to_id(&action_to_env_dict(...))`) --
    /// sonst würde der direkte Pfad die Policy-Zielzuordnung stillschweigend
    /// verfälschen (Wiederverwendung des `state_to_features_direct`-
    /// Paritätstest-Musters aus features.rs).
    #[test]
    fn action_to_id_direct_matches_json_path_across_random_games() {
        for seed in 0..8u64 {
            let mut rng = StdRng::seed_from_u64(seed);
            let mut game = Game {
                state: crate::state::setup_new_game(["P1".into(), "P2".into()], 0, &mut rng),
            };
            for p in game.state.players.iter_mut() {
                p.start_tile_pending = false;
            }
            for step in 0..60 {
                if game.state.phase != Phase::Drafting {
                    break;
                }
                let actions = drafting_actions(&game.state);
                if actions.is_empty() {
                    break;
                }
                for a in &actions {
                    let via_json = crate::features::action_to_id(&action_to_env_dict(&game.state, a));
                    let direct = action_to_id_direct(&game.state, a);
                    assert_eq!(
                        direct, via_json,
                        "seed={seed} step={step}: ID weicht ab fuer {a:?} (direct={direct} json={via_json})"
                    );
                }
                let action = actions.choose(&mut rng).unwrap().clone();
                if game.apply_drafting(&action).is_err() {
                    break;
                }
            }
        }
    }

    /// Lädt das lokale Referenz-Checkpoint fürs Gating-Seeding-Verifikat
    /// (Task #76) -- `None`, falls kein Checkpoint vorhanden (z.B. CI ohne
    /// Modell-Artefakte), Test überspringt sich dann selbst statt zu failen
    /// (gleiches Muster wie `net_mcts::load_test_net`).
    fn load_test_net_for_gating() -> Option<Net> {
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../models/alphazero_v10_best.onnx");
        match Net::load(path.to_str().unwrap(), crate::features::INPUT_SIZE) {
            Ok(n) => Some(n),
            Err(e) => {
                eprintln!("  ⚠️  {path:?} nicht ladbar ({e}) -- Test übersprungen (kein lokaler Checkpoint).");
                None
            }
        }
    }

    /// Task #76 (Gepaartes Gating als Standard) -- Verifikat: `run_net_vs_net_arena`
    /// seedet je Spiel GENAUSO deterministisch aus `seed + i·const` wie
    /// `run_net_arena_match`/`run_arena_match` (siehe deren `play`-Closures,
    /// dieselbe Formel `seed.wrapping_add((i as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15))`).
    /// Zwei komplett unabhängige Aufrufe mit demselben Seed UND denselben
    /// Modellen (hier: dasselbe Netz gegen sich selbst) müssen daher
    /// byte-identische Spielfolgen liefern -- Voraussetzung für das
    /// gepaarte McNemar-Gating in `evaluations/paired_gating.py` (identische
    /// Startbedingungen je Seed-Index über mehrere Prozessaufrufe/Arme hinweg).
    #[test]
    fn run_net_vs_net_arena_seeds_deterministically_like_run_net_arena_match() {
        let Some(net) = load_test_net_for_gating() else { return };
        let model_path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../models/alphazero_v10_best.onnx");
        let model_path = model_path.to_str().unwrap();
        drop(net); // nur zum Existenz-Check geladen, run_net_vs_net_arena laedt selbst neu

        let seed = 13_579u64;
        let n_games = 3usize;
        let raw_a = run_net_vs_net_arena(model_path, model_path, 8, 8, n_games, seed, 1, crate::net_mcts::DEFAULT_C_PUCT, crate::net_mcts::DEFAULT_C_PUCT)
            .expect("Arena-Lauf A sollte gelingen (Checkpoint existiert laut Vorab-Check)");
        let raw_b = run_net_vs_net_arena(model_path, model_path, 8, 8, n_games, seed, 1, crate::net_mcts::DEFAULT_C_PUCT, crate::net_mcts::DEFAULT_C_PUCT)
            .expect("Arena-Lauf B sollte gelingen");
        assert_eq!(
            raw_a, raw_b,
            "run_net_vs_net_arena mit identischem Seed+Modellen muss byte-identische \
             Spielfolgen liefern (Determinismus-Voraussetzung fuers gepaarte Gating)"
        );

        // Zusaetzlich: dieselbe Seed-Ableitungs-Formel wie run_net_arena_match
        // (indirekter Beleg -- ein einzelnes Spiel bei n_games=1 mit Seed S
        // muss IDENTISCH zum ersten Spiel eines n_games=3-Laufs mit Basis-Seed
        // S sein, weil beide `i=0` denselben abgeleiteten Seed ergeben).
        let raw_single = run_net_vs_net_arena(model_path, model_path, 8, 8, 1, seed, 1, crate::net_mcts::DEFAULT_C_PUCT, crate::net_mcts::DEFAULT_C_PUCT)
            .expect("Einzelspiel-Lauf sollte gelingen");
        let games_a: Vec<Value> = serde_json::from_str(&raw_a).unwrap();
        let games_single: Vec<Value> = serde_json::from_str(&raw_single).unwrap();
        assert_eq!(
            games_a[0], games_single[0],
            "Spiel i=0 muss unabhaengig von n_games identisch sein (reine Funktion von seed+i)"
        );
    }
}
