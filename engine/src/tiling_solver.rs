//! Exakter Brute-Force-Solver (DFS) für die Tiling-Phase.
//!
//! Tiling ist ein Solo-Puzzle pro Spieler mit sehr geringer Tiefe (≤6 Reihen)
//! und — laut Regel: **während des Tilings werden KEINE Kuppelplatten gelegt** —
//! sehr wenig Verzweigung. Daher kein MCTS, sondern eine rekursive Maximierung:
//! finde die Platzierungs-/Chip-Folge, die den Runden-Score des Spielers
//! maximiert. Genutzt (a) als Pseudo-Terminal-Bewertung am Drafting→Tiling-
//! Übergang im MCTS und (b) für den echten Tiling-Zug der KI.
//!
//! Zugmenge: nur Steine auf BEREITS gelegte Kuppel-Spaces (`generate_tiling_actions`
//! erzeugt von sich aus nur solche -- kein separater Filter mehr nötig) +
//! Bonus-Chip-Komplettierung passender Reihen. Reihenfolge oben→unten
//! (Regelwerk S.7) steckt bereits in `validate_tiling_action`/`generate_tiling_actions`.

use crate::board::{PlayerBoard, FIRST_PLAYER_MARKER_PENALTY};
use crate::round_end::{
    apply_bonus_chips_with, can_complete_row_with_chips, chip_allocations, execute_full_tiling,
    generate_tiling_actions, greedy_chip_alloc, row_has_open_matching_slot, TilingAction,
};
use crate::state::GameState;
use crate::tile::TileColor;

/// Defensive Rekursionsgrenze (Branching ist klein; nur als Sicherung).
const MAX_DEPTH: u32 = 30;

/// Globales Knoten-Budget für EINEN Solver-Aufruf. `MAX_DEPTH` begrenzt nur die
/// Tiefe, nicht die Breite — bei `exact=true` verzweigt `legal_steps` bei JEDEM
/// Rekursionsschritt über ALLE Chip-Allokationen (2^n), nicht nur einmal. Bei
/// mehreren gleichzeitig „chippable" Reihen mit vielen Farboptionen kann das
/// kombinatorisch explodieren (beobachtet: Self-Play hing >30min in einem
/// einzelnen `best_first_step_exact`-Aufruf, unerreichbar für den Hänger-Schutz
/// in self_play.rs, der nur ZWISCHEN Zügen prüft). Bei Erschöpfung bricht die
/// Suche ab und liefert das bisher beste Ergebnis — degradiert graceful zu
/// suboptimal statt zu hängen.
///
/// WICHTIG: ein „Knoten" ist hier NICHT billig — `chip_allocations` (Aufruf in
/// `legal_steps`, einmal PRO chippable Reihe PRO Knoten) kann bis zu 2^14
/// Teilmengen prüfen (`CHIP_ALLOC_CAP=14`), inkl. Set-/String-Allokationen je
/// Teilmenge. Ein erster Versuch mit 200_000 war deshalb immer noch viel zu
/// hoch (200_000 Knoten × mehrere teure Chip-Allokations-Aufrufe ≈
/// Milliarden Operationen, erneut >30min gehangen). 2_000 hält den
/// Worst-Case auf niedrige zweistellige Sekunden begrenzt und liegt weit über
/// dem, was normale Partien tatsächlich brauchen (Branching ist laut
/// Doc-Kommentar oben klein).
const NODE_BUDGET: u32 = 2_000;

/// Task #16: Endwertungs-Bewusstsein für die Tiling-ZUGWAHL.
///
/// BEFUND (2026-07-28): `best_first_step_inner` maximiert `pts + solve_rec(..)`,
/// also **reine Sofortpunkte der Runde**. `calculate_end_scoring` bzw.
/// `wertung_progress` kommen im gesamten Modul nicht vor. Da
/// `best_first_step_exact` der Pfad für ALLE echten Platzierungen ist
/// (`self_play.rs:894`, `py.rs:687`, `round_transition.rs:135/323`), wählt die
/// KI ihre Steine, ohne die Wertungsplatten je zu berücksichtigen — auch wenn
/// die darüberliegende Suche sie sehr wohl bewertet.
///
/// Die Heuristik macht es seit jeher anders: `mcts::player_total` =
/// `solve_round_final_score` **+ `wertung_progress`** + Straf-Term. Dieses
/// Shaping überträgt denselben Term auf die Zugwahl des Solvers — deshalb
/// Gewicht 1.0, dieselben Einheiten (Rundenpunkte), dieselbe Ersatzformel.
///
/// BEWUSST NUR auf der ersten Stufe (`best_first_step_inner`), NICHT in
/// `solve_rec`: (a) `solve_rec` ist der Blatt-Bewertungs-Hot-Path des MCTS,
/// dort würde der Term mit `player_total`s eigenem `wertung_progress`
/// DOPPELT zählen; (b) die erste Stufe ist die, die den Zug tatsächlich
/// bestimmt. Der Fortschritts-Delta wird daher nur über den ersten Schritt
/// gemessen, nicht über den ganzen Rollout — Unterschätzung in Kauf genommen,
/// weil `solve_rec` nur den Score liefert, nicht den Endzustand.
///
/// STAND: **AUS -- A/B GEFAHREN UND VERWORFEN (2026-07-29).**
///
/// Gepaarter Arena-A/B, `v18_best`@400 vs `v17_best`@400, 1600 Spiele
/// (2 Blöcke à 400 je Arm, identischer Basis-Seed innerhalb jedes Blocks,
/// `tools/paired_arena_plate_ab.py` + `tools/pool_arena_ab.py`):
///
/// | Block | OFF | ON | b(nur ON) | c(nur OFF) | p |
/// |---|---|---|---|---|---|
/// | 1 (Seed 5150271)  | 226 | 245 | 63 | 44 | 0,0814 |
/// | 2 (Seed 77150271) | 228 | 219 | 50 | 59 | 0,4437 |
/// | gepoolt           | 454 | 464 | 113 | 103 | **0,5404** |
///
/// Block 1 sah mit p=0,0814 nach einem Effekt aus, Block 2 kehrte die Richtung
/// um. Gepoolt ein Münzwurf. Auch der Ø-Score beider Seiten ist inkonsistent
/// (Summe Block 1: 74,0 OFF vs 73,9 ON; gepoolt 73,4 vs 74,1) -- kein Signal.
///
/// LEHRE, die den Aufwand wert war: hätte man nach Block 1 auf p=0,08
/// übernommen, wäre eine wirkungslose Änderung eingebaut UND der Elo-Anker
/// unnötig entwertet worden (der Solver ist gemeinsamer Code, er ändert auch
/// die Heuristik-Spielstärke). Replizieren statt auf ein knappes p zu handeln.
///
/// Der Code bleibt inert erhalten -- der zugrundeliegende BEFUND stimmt ja
/// weiterhin (der Solver ist endwertungsblind, die Heuristik darüber nicht).
/// Er ist nur an dieser Stelle offenbar nicht spielentscheidend.
pub const TILING_SHAPING_ENABLED: bool = false;

/// Gewicht des Fortschritts-Terms. 1.0 = exakt die Gewichtung, mit der
/// `mcts::player_total` denselben Term seit jeher führt.
pub const TILING_SHAPING_WEIGHT: f64 = 1.0;

/// Task #21: exakte Endwertung in der Runde-5-Tiling-Zugwahl.
/// Standard AUS bis gemessen ist, wie oft sie ueberhaupt einen anderen Zug
/// waehlt -- dieselbe Disziplin wie bei TILING_SHAPING_ENABLED.
pub const ROUND5_ENDSCORING_ENABLED: bool = true;

/// Ein Tiling-Schritt im Solver. `Chips` trägt die konkrete Plättchen-Auswahl
/// (Indizes in `bonus_chips`), damit der reale KI-Zug exakt dem Solver-Plan folgt.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TilingStep {
    Place(TilingAction),
    Chips { row: usize, chips: Vec<usize> },
    End,
}

/// Mit Bonusplättchen komplettierbare Reihen, die danach platzierbar sind
/// (Reihenfolge oben→unten via `tiled_max_row` respektiert).
fn chippable_rows(state: &GameState, pi: usize) -> Vec<usize> {
    let player = &state.players[pi];
    if player.bonus_chips.is_empty() {
        return Vec::new();
    }
    let tiled_max = player.tiled_max_row;
    let mut out = Vec::new();
    for (ri, row) in player.pattern_lines.iter().enumerate() {
        if row.tiles.is_empty() || row.is_complete() {
            continue;
        }
        if (ri as i32) < tiled_max {
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
            out.push(ri);
        }
    }
    out
}

/// Legale Solver-Schritte: Steine auf bestehende Platten (kein Display) + Chips.
///
/// `exact` steuert die Plättchen-Allokation:
/// - `false` (Hot-Path, MCTS-Blätter): EINE Greedy-Allokation pro Reihe. Das
///   Verzweigen über ALLE 2^n-Allokationen wäre hier unbezahlbar (E2E 8 s→75 s+).
/// - `true` (nur der echte KI-Zug, einmal pro Tiling-Schritt): alle distinkten
///   Allokationen → exakt optimale Chip-Nutzung im tatsächlich gespielten Zug.
fn legal_steps(state: &GameState, pi: usize, exact: bool) -> Vec<TilingStep> {
    let mut steps: Vec<TilingStep> = generate_tiling_actions(state, pi)
        .into_iter()
        .map(TilingStep::Place)
        .collect();
    for row in chippable_rows(state, pi) {
        if exact {
            for chips in chip_allocations(&state.players[pi], row) {
                steps.push(TilingStep::Chips { row, chips });
            }
        } else if let Some(chips) = greedy_chip_alloc(&state.players[pi], row) {
            steps.push(TilingStep::Chips { row, chips });
        }
    }
    steps
}

/// Wendet einen Schritt auf einen Klon an. Gibt (Folgezustand, Sofortpunkte)
/// zurück. None bei `End` oder fehlgeschlagenem Zug.
fn apply_step(state: &GameState, pi: usize, step: &TilingStep) -> Option<(GameState, i32)> {
    match step {
        TilingStep::Place(ta) => {
            let mut s = state.clone();
            let pts = execute_full_tiling(&mut s, pi, ta).ok()?;
            Some((s, pts))
        }
        TilingStep::Chips { row, chips } => {
            let mut s = state.clone();
            if !apply_bonus_chips_with(&mut s.players[pi], *row, chips) {
                return None;
            }
            Some((s, 0))
        }
        TilingStep::End => None,
    }
}

fn solve_rec(state: &GameState, pi: usize, depth: u32, exact: bool, budget: &mut u32) -> i32 {
    if depth >= MAX_DEPTH || *budget == 0 {
        return 0;
    }
    *budget -= 1;
    let steps = legal_steps(state, pi, exact);
    if steps.is_empty() {
        return 0;
    }
    // Baseline 0 = „hier aufhören". Platzierungen liefern stets ≥1, Chips 0
    // (schalten aber Platzierungen frei) — der maximierende Pfad gewinnt.
    let mut best = 0;
    for step in &steps {
        if *budget == 0 {
            break; // Budget erschöpft: bisher bestes Ergebnis liefern statt hängen.
        }
        if let Some((next, pts)) = apply_step(state, pi, step) {
            let total = pts + solve_rec(&next, pi, depth + 1, exact, budget);
            if total > best {
                best = total;
            }
        }
    }
    best
}

/// Maximal erreichbare Tiling-Punkte (Linien + Spezial-Boni) für Spieler `pi`,
/// ausgehend vom aktuellen Brett (Drafting-Ende). GREEDY-Chips (Hot-Path).
pub fn solve_max_tiling_points(state: &GameState, pi: usize) -> i32 {
    let mut budget = NODE_BUDGET;
    solve_rec(state, pi, 0, false, &mut budget)
}

/// Wie `solve_max_tiling_points`, aber mit exakter Chip-Allokationssuche.
/// Nur für den echten KI-Zug (einmalig) gedacht — NICHT für MCTS-Blätter.
pub fn solve_max_tiling_points_exact(state: &GameState, pi: usize) -> i32 {
    let mut budget = NODE_BUDGET;
    solve_rec(state, pi, 0, true, &mut budget)
}

// ── Task #99: Transpositions-Memoisierung ───────────────────────────────────
//
// NUMMERN-REPARATUR 2026-08-09: dieser Block trug bis dahin die Nummer #33,
// die am 2026-08-04 parallel auch fuer den "Value-/Policy-Loss-Gewicht-Sweep"
// vergeben wurde (archive/history.md:9597) -- zwei unabhaengige Themen, gleiche
// Nummer, weil es damals keine Registratur gab. Umnummeriert wurde DIESE Seite,
// weil die andere Bedeutung an fuenf Stellen in einer Entscheidungs-Erzaehlung
// steht ("#33 IN #34", "vor #33 und #35") und ein Umschreiben den historischen
// Ablauf verfaelschen wuerde; hier waren es drei Stellen in einer Datei.
// #99 statt einer der freien Luecken (40-61 usw.): Luecken koennen im Chat
// vergeben worden sein, ohne Spur in den Dateien -- oberhalb des bisherigen
// Maximums #98 ist eine Neu-Kollision ausgeschlossen.
// Registratur: evaluations/TASK_NUMMERN_REGISTRATUR.md
// HERLEITUNG DES CACHE-SCHLÜSSELS (Auftrag Schritt 1a, Code gelesen 2026-08-04):
// `solve_round_final_score`/`solve_max_tiling_points` (und transitiv `solve_rec`,
// `legal_steps`, `chippable_rows`, `apply_step` -> `execute_full_tiling`,
// `check_special_trigger`, `score_placed_tile`, `count_line`, `apply_bonus_chips_with`)
// lesen NACHWEISLICH ausschließlich `state.players[pi]` -- kein Zugriff auf
// `state.current_player`, `state.factories`, den jeweils ANDEREN Spieler, RNG
// oder sonstige globale Zustände. Die Funktion ist damit rein/deterministisch
// bei festem `PlayerBoard`. Innerhalb von `PlayerBoard` sind laut Code-Audit
// NUR folgende Felder ergebnisrelevant:
//   - `pattern_lines[].tiles`        (volle Reihen, Farbe/Füllstand)
//   - `dome_grid.dome_slots`         (Layout inkl. `space_type` -- Wild
//                                     akzeptiert jede Farbe, Special keine,
//                                     UNABHÄNGIG von `required_color`;
//                                     `required_color`/`placed_color`/
//                                     `placed_special`/`is_locked` steuern
//                                     `accepts`/`is_filled`/Special-Trigger;
//                                     `tile_id` wird defensiv mitgehasht,
//                                     ändert nichts an der Korrektheit)
//   - `bonus_chips[].colors`         (NUR `.colors`, s. `chip_sig`/
//                                     `greedy_chip_indices`/`chip_allocations`
//                                     in round_end.rs -- `chip_id` fließt NIE
//                                     in eine Score-Berechnung ein)
//   - `tiled_max_row`                (`chippable_rows`-Untergrenze)
//   - `score`                        (Basiswert, direkt addiert)
//   - `broken_tiles`                 (`broken_penalty()`)
//   - `holds_first_player_marker`    (Marker-Strafe)
// NICHT gehasht, weil nachweislich nie von diesem Aufrufpfad gelesen:
// `player_id`, `name`, `score_unclamped`, `dome_tiles_placed_this_round`,
// `player_tokens_used`, `start_dome_tile`, `start_tile_pending`,
// `bonus_chips_used_this_round`, `total_floor_penalties`,
// `floor_penalties_per_round`.
//
// `solve_round_final_score_endaware` ruft zusätzlich `calculate_end_scoring`
// an jedem Blatt auf (`scoring::calculate_end_scoring(player, tile_ids)`) --
// deren zweiter Parameter ist `state.scoring_tile_ids`, das deshalb NUR beim
// endaware-Schlüssel zusätzlich einfließt (siehe `TilingKeyEndaware` unten).
//
// KOLLISIONS-SCHUTZ: statt eines rohen u64-Hashs als HashMap-Schlüssel (der
// bei einer Kollision STILL das falsche Ergebnis liefern würde) trägt
// `TilingKey` die vollständigen, geklonten Werte selbst. `HashMap::get`
// vergleicht bei Bucket-Kollisionen per `Eq` -- zwei strukturell
// unterschiedliche Stellungen können daher NIE denselben Cache-Treffer
// erzeugen, unabhängig vom internen Hash. Test:
// `tiling_key_differs_on_result_relevant_field_change` unten.
type SpaceKey = (u8, Option<TileColor>, Option<TileColor>, bool, bool);

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct TilingKey {
    score: i32,
    tiled_max_row: i32,
    holds_first_player_marker: bool,
    broken_tiles: Vec<TileColor>,
    pattern_lines: Vec<Vec<TileColor>>,
    dome_slots: Vec<Option<(usize, Vec<SpaceKey>)>>,
    bonus_chip_colors: Vec<Vec<TileColor>>,
}

fn tiling_key(player: &PlayerBoard) -> TilingKey {
    let dome_slots = player
        .dome_grid
        .dome_slots
        .iter()
        .flatten()
        .map(|slot| {
            slot.as_ref().map(|t| {
                let spaces: Vec<SpaceKey> = t
                    .spaces
                    .iter()
                    .map(|sp| {
                        (sp.space_type as u8, sp.required_color, sp.placed_color, sp.placed_special, sp.is_locked)
                    })
                    .collect();
                (t.tile_id, spaces)
            })
        })
        .collect();
    TilingKey {
        score: player.score,
        tiled_max_row: player.tiled_max_row,
        holds_first_player_marker: player.holds_first_player_marker,
        broken_tiles: player.broken_tiles.clone(),
        pattern_lines: player.pattern_lines.iter().map(|l| l.tiles.clone()).collect(),
        dome_slots,
        bonus_chip_colors: player.bonus_chips.iter().map(|c| c.colors.clone()).collect(),
    }
}

/// Schlüssel für die endwertungsbewusste Variante -- `TilingKey` plus die
/// aktiven Wertungsplatten-IDs (siehe Herleitung oben).
type TilingKeyEndaware = (TilingKey, Vec<usize>);

fn tiling_key_endaware(player: &PlayerBoard, scoring_tile_ids: &[usize]) -> TilingKeyEndaware {
    (tiling_key(player), scoring_tile_ids.to_vec())
}

/// Obergrenze je Thread-lokalem Cache. GRÖSSENDECKEL statt Rundengrenze:
/// eine Rundengrenzen-Leerung müsste an JEDER Stelle, die einen Runden-
/// übergang auslöst (self_play.rs, net_mcts.rs, round_transition*.rs),
/// einen zusätzlichen Reset-Aufruf einführen -- invasiv und leicht zu
/// vergessen. Ein Größendeckel bleibt vollständig innerhalb dieses Moduls.
/// Korrektheit ist von der Wahl der Zahl UNABHÄNGIG (bitgleiches Ergebnis
/// bei Treffer, Neuberechnung bei `clear()`) -- 20_000 Einträge sind groß
/// genug, um die Transpositionen INNERHALB einer Suche (ein Zug: einige
/// hundert bis wenige tausend Solver-Aufrufe, siehe `NODE_BUDGET`) fast
/// immer im Cache zu halten, aber klein genug, um den Speicher pro der 11
/// Self-Play-Threads (Task-#99-Kontext, vormals #33) begrenzt zu halten.
const CACHE_CAP: usize = 20_000;

thread_local! {
    static PLAIN_CACHE: std::cell::RefCell<std::collections::HashMap<TilingKey, i32>> =
        std::cell::RefCell::new(std::collections::HashMap::new());
    static ENDAWARE_CACHE: std::cell::RefCell<std::collections::HashMap<TilingKeyEndaware, i32>> =
        std::cell::RefCell::new(std::collections::HashMap::new());
    static PLAIN_STATS: std::cell::RefCell<std::collections::HashMap<TilingKey, u32>> =
        std::cell::RefCell::new(std::collections::HashMap::new());
    static ENDAWARE_STATS: std::cell::RefCell<std::collections::HashMap<TilingKeyEndaware, u32>> =
        std::cell::RefCell::new(std::collections::HashMap::new());
    /// Test-Override, siehe `stats_enabled`/`cache_enabled` -- thread-lokal,
    /// deshalb ohne Race gegen andere `cargo test`-Threads, die dieselbe
    /// `OnceLock`-gecachte Env-Var evtl. schon (als AUS) gelesen haben.
    static STATS_OVERRIDE: std::cell::Cell<Option<bool>> = std::cell::Cell::new(None);
    static CACHE_OVERRIDE: std::cell::Cell<Option<bool>> = std::cell::Cell::new(None);
}

/// `MOSAIC_TILING_CACHE_STATS=1`: zählt nur, wie oft derselbe Schlüssel
/// wiederkehrt (Schritt 2 des Auftrags) -- KEIN Cache, keine Ergebnis-
/// Veränderung, praktisch kostenlos wenn aus (ein `bool`-Vergleich,
/// `OnceLock` liest die Env-Var nur beim ersten Aufruf je Prozess).
fn stats_enabled_env() -> bool {
    static ENABLED: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *ENABLED.get_or_init(|| std::env::var("MOSAIC_TILING_CACHE_STATS").map(|v| v == "1").unwrap_or(false))
}

/// Echte Memoisierung. **Standard AN** (Nutzer-Entscheid 2026-08-05, nachdem
/// der A/B gelaufen war); `MOSAIC_TILING_CACHE=0` schaltet ab.
fn cache_enabled_env() -> bool {
    static ENABLED: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    // Standard AN seit 2026-08-05 (Nutzer-Entscheid): der gemessene A/B auf
    // ruhiger Maschine ergab -20,1% Self-Play-Wandzeit (276,7s -> 221,0s ueber
    // 30 Partien) bei BITGLEICHEN Ergebnissen (Bit-Identitaets-Test ueber 400+
    // Vergleiche, kalt und warm). `MOSAIC_TILING_CACHE=0` schaltet ihn ab --
    // fuer A/Bs, Debugging oder falls der Speicherbedarf je Thread stoert.
    *ENABLED.get_or_init(|| std::env::var("MOSAIC_TILING_CACHE").map(|v| v != "0").unwrap_or(true))
}

fn stats_enabled() -> bool {
    STATS_OVERRIDE.with(|c| c.get()).unwrap_or_else(stats_enabled_env)
}

fn cache_enabled() -> bool {
    CACHE_OVERRIDE.with(|c| c.get()).unwrap_or_else(cache_enabled_env)
}

fn compute_plain(state: &GameState, pi: usize) -> i32 {
    let p = &state.players[pi];
    let penalty =
        p.broken_penalty() + if p.holds_first_player_marker { FIRST_PLAYER_MARKER_PENALTY } else { 0 };
    p.score + penalty + solve_max_tiling_points(state, pi)
}

fn cached_plain(state: &GameState, pi: usize) -> i32 {
    if !stats_enabled() && !cache_enabled() {
        return compute_plain(state, pi);
    }
    let key = tiling_key(&state.players[pi]);
    if stats_enabled() {
        PLAIN_STATS.with(|s| *s.borrow_mut().entry(key.clone()).or_insert(0) += 1);
    }
    if cache_enabled() {
        if let Some(v) = PLAIN_CACHE.with(|c| c.borrow().get(&key).copied()) {
            return v;
        }
        let v = compute_plain(state, pi);
        PLAIN_CACHE.with(|c| {
            let mut c = c.borrow_mut();
            if c.len() >= CACHE_CAP {
                c.clear();
            }
            c.insert(key, v);
        });
        return v;
    }
    compute_plain(state, pi)
}

fn compute_endaware(state: &GameState, pi: usize) -> i32 {
    let p = &state.players[pi];
    let penalty =
        p.broken_penalty() + if p.holds_first_player_marker { FIRST_PLAYER_MARKER_PENALTY } else { 0 };
    let mut budget = NODE_BUDGET;
    p.score + penalty + solve_rec_endaware(state, pi, 0, &mut budget)
}

fn cached_endaware(state: &GameState, pi: usize) -> i32 {
    if !stats_enabled() && !cache_enabled() {
        return compute_endaware(state, pi);
    }
    let key = tiling_key_endaware(&state.players[pi], &state.scoring_tile_ids);
    if stats_enabled() {
        ENDAWARE_STATS.with(|s| *s.borrow_mut().entry(key.clone()).or_insert(0) += 1);
    }
    if cache_enabled() {
        if let Some(v) = ENDAWARE_CACHE.with(|c| c.borrow().get(&key).copied()) {
            return v;
        }
        let v = compute_endaware(state, pi);
        ENDAWARE_CACHE.with(|c| {
            let mut c = c.borrow_mut();
            if c.len() >= CACHE_CAP {
                c.clear();
            }
            c.insert(key, v);
        });
        return v;
    }
    compute_endaware(state, pi)
}

#[cfg(test)]
pub(crate) fn set_stats_override_for_test(v: Option<bool>) {
    STATS_OVERRIDE.with(|c| c.set(v));
}
#[cfg(test)]
pub(crate) fn set_cache_override_for_test(v: Option<bool>) {
    CACHE_OVERRIDE.with(|c| c.set(v));
}
#[cfg(test)]
pub(crate) fn clear_tiling_caches_for_test() {
    PLAIN_CACHE.with(|c| c.borrow_mut().clear());
    ENDAWARE_CACHE.with(|c| c.borrow_mut().clear());
    PLAIN_STATS.with(|c| c.borrow_mut().clear());
    ENDAWARE_STATS.with(|c| c.borrow_mut().clear());
}
/// (Gesamtaufrufe, distinkte Schlüssel, max. Wiederholungen eines Schlüssels).
#[cfg(test)]
pub(crate) fn plain_stats_summary_for_test() -> (u64, usize, u32) {
    PLAIN_STATS.with(|s| {
        let s = s.borrow();
        let total: u64 = s.values().map(|&v| v as u64).sum();
        (total, s.len(), s.values().copied().max().unwrap_or(0))
    })
}
#[cfg(test)]
pub(crate) fn endaware_stats_summary_for_test() -> (u64, usize, u32) {
    ENDAWARE_STATS.with(|s| {
        let s = s.borrow();
        let total: u64 = s.values().map(|&v| v as u64).sum();
        (total, s.len(), s.values().copied().max().unwrap_or(0))
    })
}

/// Optimaler finaler Runden-Score für Spieler `pi`: aktueller Score +
/// max. Tiling-Punkte + (fixe) Boden-/Marker-Strafen.
pub fn solve_round_final_score(state: &GameState, pi: usize) -> i32 {
    // Task #32 (`profiling.rs`-Modulkopf "Task #32"): Haupteinstiegspunkt der
    // "tiling_solver"-Kategorie -- die interne Rekursion (`solve_rec`) bleibt
    // uninstrumentiert (siehe dortige Regel "keine Rekursion einzeln zaehlen").
    crate::profiling::selfplay_profile::timed(crate::profiling::selfplay_profile::SelfplayCat::TilingSolver, || {
        cached_plain(state, pi)
    })
}

/// Blatt-Rekursion für [`solve_round_final_score_endaware`]: wie `solve_rec`,
/// aber an jedem BLATT (keine legalen Schritte mehr, Tiefen-/Budget-Deckel
/// erreicht) wird zusätzlich `calculate_end_scoring` des dort erreichten
/// Bretts aufaddiert, und die SUMME aus Platzierungspunkten + Endwertung wird
/// maximiert statt nur die Punkte. Die "hier aufhören"-Baseline (siehe
/// `solve_rec`-Kommentar: Stoppen ist immer eine erlaubte Alternative) ist
/// hier folgerichtig nicht mehr 0, sondern die Endwertung des Bretts VOR
/// diesem Schritt -- Stoppen ist ja selbst ein gültiges Blatt.
///
/// EIGENE Rekursion statt Wiederverwendung von `solve_rec`: `solve_rec` ist
/// der Blatt-Bewertungs-Hot-Path der Runden 1-4 (MCTS, `solve_max_tiling_points`)
/// und bleibt unangetastet. GREEDY-Chip-Politik (`exact=false`, wie der
/// Hot-Path) und dasselbe `NODE_BUDGET`-Muster, weil diese Funktion an JEDEM
/// Alpha-Beta-Blatt in Runde 5 läuft (`round5::player_total_exact`, hinter
/// `ROUND5_ENDSCORING_ENABLED`) -- eine exakte Chip-Allokationssuche wäre dort
/// unbezahlbar teuer.
fn solve_rec_endaware(state: &GameState, pi: usize, depth: u32, budget: &mut u32) -> i32 {
    let end_here =
        crate::scoring::calculate_end_scoring(&state.players[pi], &state.scoring_tile_ids).total;
    if depth >= MAX_DEPTH || *budget == 0 {
        return end_here;
    }
    *budget -= 1;
    let steps = legal_steps(state, pi, false);
    if steps.is_empty() {
        return end_here;
    }
    // Baseline = Endwertung DIESES Bretts ("hier aufhören", siehe Doc oben).
    let mut best = end_here;
    for step in &steps {
        if *budget == 0 {
            break; // Budget erschöpft: bisher bestes Ergebnis liefern statt hängen.
        }
        if let Some((next, pts)) = apply_step(state, pi, step) {
            let total = pts + solve_rec_endaware(&next, pi, depth + 1, budget);
            if total > best {
                best = total;
            }
        }
    }
    best
}

/// Task #21: wie [`solve_round_final_score`], aber die Rekursion wertet am
/// BLATT zusätzlich `calculate_end_scoring` des dort erreichten Bretts aus und
/// maximiert die SUMME (Rundenpunkte + Endwertung) statt allein die Punkte.
///
/// Nur für Runde 5 sinnvoll -- dort ist `calculate_end_scoring` exakt (kein
/// Näherungsfehler, das Kuppelraster ändert sich nicht mehr, siehe
/// `round5.rs`-Modul-Kommentar). Aufgerufen von `round5::player_total_exact`
/// hinter `ROUND5_ENDSCORING_ENABLED` -- dort ersetzt sie die bisherige Summe
/// `solve_round_final_score(..) + calculate_end_scoring(Brett DAVOR, ..)`,
/// die sich auf zwei VERSCHIEDENE Brettzustände bezog (siehe Doc dort).
pub fn solve_round_final_score_endaware(state: &GameState, pi: usize) -> i32 {
    // Task #32: zweiter Haupteinstiegspunkt der "tiling_solver"-Kategorie --
    // wird an JEDEM `round5.rs`-Alpha-Beta-Blatt aufgerufen (siehe
    // `profiling.rs`-Modulkopf); die daraus resultierende Verschachtelung mit
    // `round5_alphabeta` wird dort ueber `tiling_solver_inside_round5_ns`
    // getrennt ausgewiesen, kein Sonderfall hier noetig.
    crate::profiling::selfplay_profile::timed(crate::profiling::selfplay_profile::SelfplayCat::TilingSolver, || {
        cached_endaware(state, pi)
    })
}

/// Optimaler nächster Tiling-Schritt für Spieler `pi`. `End`, wenn nichts mehr
/// platzierbar/komplettierbar ist. `exact` → exakte Chip-Allokationssuche
/// (nur für den echten Zug verwenden, NICHT pro MCTS-Blatt).
fn best_first_step_inner(state: &GameState, pi: usize, exact: bool) -> TilingStep {
    let steps = legal_steps(state, pi, exact);
    if steps.is_empty() {
        return TilingStep::End;
    }
    let mut budget = NODE_BUDGET;
    let mut best_step = TilingStep::End;
    let mut best_val = f64::NEG_INFINITY;
    // Basis-Fortschritt EINMAL vor der Schleife: der Shaping-Term ist ein
    // Delta gegen den Zustand VOR dem Schritt (siehe TILING_SHAPING_ENABLED).
    let base_progress = if TILING_SHAPING_ENABLED {
        crate::scoring::wertung_progress(&state.players[pi], &state.scoring_tile_ids)
    } else {
        0.0
    };
    for step in steps {
        if budget == 0 {
            break; // Budget erschöpft: bisher besten Schritt liefern statt hängen.
        }
        if let Some((next, pts)) = apply_step(state, pi, &step) {
            let mut val = f64::from(pts + solve_rec(&next, pi, 1, exact, &mut budget));
            if TILING_SHAPING_ENABLED {
                let delta = crate::scoring::wertung_progress(
                    &next.players[pi],
                    &next.scoring_tile_ids,
                ) - base_progress;
                val += TILING_SHAPING_WEIGHT * delta;
            }
            if val > best_val {
                best_val = val;
                best_step = step;
            }
        }
    }
    best_step
}

/// Task #20: bis zu `k` VOLLSTAENDIGE Tiling-Abschluesse mit ihren
/// Folgezustaenden, absteigend nach Rundenpunkten.
///
/// Der bestehende Solver liefert nur EINEN Schritt und nur dessen Score. Fuer
/// eine netz-gefuehrte Auswahl braucht es die fertigen Bretter -- das Netz
/// bewertet den Zustand, aus dem die naechste Runde startet.
///
/// BEWUSST eine eigene Funktion: der Hot-Path (`solve_rec`,
/// `solve_round_final_score`, MCTS-Blattbewertung) bleibt unangetastet.
///
/// Abbruch ueber dasselbe `NODE_BUDGET` wie der Solver plus eine Blatt-Obergrenze
/// -- bei mehreren chippable Reihen kann der Baum sonst explodieren.
/// Entartete Reihenfolgen (dieselben Steine, andere Reihenfolge) fuehren auf
/// dasselbe Brett; dedupliziert wird ueber die Belegungssignatur, sonst
/// erschiene die Value-Spreizung kuenstlich klein.
const MAX_TILING_LEAVES: usize = 400;

/// Kanonische Signatur eines Tiling-ABSCHLUSSES: Kuppelfuellung UND
/// verbleibender Bonuschip-Bestand.
///
/// BEFUND (2026-07-29): die alte Signatur (`dome_fill_signature`, nur die 36
/// Fuellungs-Bools) verschmolz zwei Abschluesse mit identischem Endbrett aber
/// UNTERSCHIEDLICHEM Chip-Rest -- verschiedene `chip_allocations` koennen
/// dieselbe Reihenkomplettierung mit verschiedenen Chips erreichen. Der
/// Abschluss mit weniger verbrauchten Chips wurde dabei verworfen, obwohl
/// uebrige Bonuschips Zukunftskapital fuer spaetere Runden sind (sie wandern
/// mit ins naechste Runden-Setup). Fuer die geplante netz-gefuehrte Auswahl
/// (das Netz bewertet den FOLGEZUSTAND, nicht nur die Rundenpunkte) ist der
/// Chip-Rest ein echter Unterschied zwischen zwei sonst identischen Brettern.
///
/// Jeder Chip wird durch die sortierte Liste seiner Farbnamen kodiert
/// (mehrfarbige Chips tragen 1-2 Farben), die Chip-Liste selbst wird
/// anschliessend sortiert -- die Signatur ist damit unabhaengig von der
/// Reihenfolge im `bonus_chips`-Vec (reine Permutationen desselben Bestands
/// duerfen NICHT als unterschiedlich gelten, sonst waechst die Kandidatenzahl
/// kuenstlich).
fn tiling_outcome_signature(state: &GameState, pi: usize) -> (Vec<bool>, Vec<String>) {
    let mut fill = Vec::with_capacity(36);
    for sr in 0..3 {
        for sc in 0..3 {
            match &state.players[pi].dome_grid.dome_slots[sr][sc] {
                Some(slot) => {
                    for si in 0..4 {
                        fill.push(slot.spaces.get(si).map_or(false, |sp| sp.placed_color.is_some()));
                    }
                }
                None => fill.extend_from_slice(&[false; 4]),
            }
        }
    }
    let mut chips: Vec<String> = state.players[pi]
        .bonus_chips
        .iter()
        .map(|c| {
            let mut colors: Vec<String> = c.colors.iter().map(|col| format!("{col:?}")).collect();
            colors.sort();
            colors.join(",")
        })
        .collect();
    chips.sort();
    (fill, chips)
}

/// Ein vollstaendiger Tiling-Abschluss: Rundenpunkte, der ERSTE Schritt dorthin
/// (das ist der Zug, den der Solver zurueckgeben muss) und das fertige Brett.
pub struct TilingOutcome {
    pub points: i32,
    pub first_step: TilingStep,
    pub final_state: GameState,
}

fn collect_tilings(
    state: &GameState,
    pi: usize,
    acc: i32,
    first: Option<&TilingStep>,
    depth: u32,
    budget: &mut u32,
    out: &mut Vec<TilingOutcome>,
) {
    if *budget == 0 || out.len() >= MAX_TILING_LEAVES || depth >= MAX_DEPTH {
        return;
    }
    let steps = legal_steps(state, pi, true);
    if steps.is_empty() {
        if let Some(f) = first {
            out.push(TilingOutcome {
                points: acc,
                first_step: f.clone(),
                final_state: state.clone(),
            });
        }
        return;
    }
    for step in steps {
        if *budget == 0 || out.len() >= MAX_TILING_LEAVES {
            break;
        }
        *budget -= 1;
        if let Some((next, pts)) = apply_step(state, pi, &step) {
            let f = first.unwrap_or(&step).clone();
            collect_tilings(&next, pi, acc + pts, Some(&f), depth + 1, budget, out);
        }
    }
}

/// Bis zu `k` vollstaendige Abschluesse, absteigend nach Punkten, ohne
/// Duplikate gleicher Endbelegung.
pub fn top_k_tilings(state: &GameState, pi: usize, k: usize) -> Vec<TilingOutcome> {
    let mut out: Vec<TilingOutcome> = Vec::new();
    let mut budget = NODE_BUDGET;
    collect_tilings(state, pi, 0, None, 0, &mut budget, &mut out);
    out.sort_by(|a, b| b.points.cmp(&a.points));
    let mut seen: Vec<(Vec<bool>, Vec<String>)> = Vec::new();
    let mut uniq: Vec<TilingOutcome> = Vec::new();
    for o in out {
        let sig = tiling_outcome_signature(&o.final_state, pi);
        if seen.iter().any(|s| *s == sig) {
            continue;
        }
        seen.push(sig);
        uniq.push(o);
        if uniq.len() >= k {
            break;
        }
    }
    uniq
}

/// Task #21: Tiling-Zugwahl in Runde 5 mit EXAKTER Endwertung.
///
/// In den Runden 1-4 ist die Zukunft offen -- jede Endwertungs-Beruecksichtigung
/// im Tiling ist dort eine Wette auf eine Absicht, die das Netz vielleicht gar
/// nicht hat. Genau daran ist Task #16 gescheitert (1600 Spiele, p=0,5404).
///
/// In Runde 5 endet das Spiel NACH dem Tiling. Die Endwertung des fertigen
/// Bretts ist damit exakt berechenbar -- kein Proxy, keine Unsicherheit, kein
/// Gewicht. Maximiert wird deshalb
///
/// ```text
/// Rundenpunkte(Abschluss) + calculate_end_scoring(Brett NACH dem Abschluss)
/// ```
///
/// statt allein die Rundenpunkte.
///
/// WARUM DAS EIN KORREKTHEITS-FIX IST, kein Tuning: `round5::player_total_exact`
/// rechnet heute `solve_round_final_score` (Punkte des punktemaximalen Tilings)
/// PLUS `calculate_end_scoring` des Bretts DAVOR. Die beiden Terme beziehen sich
/// auf verschiedene Brettzustaende -- gerade die Steine, die Reihen, Spalten und
/// Diagonalen schliessen und damit die Endwertung treiben, fehlen in der
/// Endwertungs-Rechnung. Zwei Drafting-Zuege mit gleichen Rundenpunkten, aber
/// unterschiedlich viel ERREICHBARER Endwertung, sind dadurch fuer die
/// Alpha-Beta-Suche ununterscheidbar.
///
/// Bedingung ist bewusst `round_number >= 5` und NICHT `round5::applies`:
/// letzteres verlangt zusaetzlich `phase == Drafting` und waere im Tiling --
/// also genau hier -- immer falsch.
///
/// Nur im echten Zug: `best_first_step_exact` ruft das, `solve_rec` und die
/// MCTS-Blattbewertung bleiben unberuehrt.
fn best_first_step_round5(state: &GameState, pi: usize) -> Option<TilingStep> {
    let cands = top_k_tilings(state, pi, MAX_TILING_LEAVES);
    let best = cands.into_iter().max_by_key(|o| {
        o.points
            + crate::scoring::calculate_end_scoring(
                &o.final_state.players[pi],
                &o.final_state.scoring_tile_ids,
            )
            .total
    })?;
    Some(best.first_step)
}

/// Task #20: netz-geführter Stichentscheid unter punktgleichen (oder
/// -ähnlichen) Tiling-Abschlüssen.
///
/// STAND: AUS bis per Arena bestätigt -- gleiche Disziplin wie
/// `TILING_SHAPING_ENABLED`/`ROUND5_ENDSCORING_ENABLED` oben.
///
/// BEFUND (`evaluations/tiling_candidate_spread.json`, `v18_best`, k=12,
/// 142 Runde-2-4-Tiling-Stellungen mit >1 Kandidat, 51/51 Faelle mit
/// Auswahlaenderung geprueft): die Multiplikation `punkte * value` hat in
/// KEINEM der 51 Faelle einen echten Punktvorsprung ueberstimmt -- die
/// mediane Value-Spreizung unter den Top-`k`-Kandidaten liegt bei 0,017
/// (IQR [0,010; 0,028]), viel zu klein, um einen vollen Punkt zu kippen
/// (siehe Formel im Modulkommentar von `tools/tiling_candidate_spread.py`).
/// Sie wirkt in der Praxis ausschliesslich als Stichentscheid zwischen
/// Abschluessen mit (nahezu) IDENTISCHEN Punkten -- deshalb hier bewusst als
/// Multiplikation und nicht als additiver Shaping-Term wie bei
/// `TILING_SHAPING_ENABLED` implementiert.
pub const NET_TILING_TIEBREAK_ENABLED: bool = true;

/// `k` fuer `top_k_tilings` beim netz-gefuehrten Stichentscheid -- identisch
/// zur Messung in `tiling_candidate_spread.json` (dort mit `k=12` erhoben),
/// damit der gemessene BEFUND (s.o.) tatsaechlich zum Verhalten passt.
pub const NET_TILING_TOPK: usize = 12;

/// Task #37 (NEU, Nutzer 2026-08-05, siehe `archive/history.md` Abschnitt
/// "Task #37"): Laufzeit-Wahl des Auswahlkriteriums unter den
/// `top_k_tilings`-Kandidaten -- `MOSAIC_TILING_SELECT` ueberschreibt den
/// Default (OnceLock, einmalig pro Prozess gelesen, gleiches Muster wie
/// `MOSAIC_FLOOR_SHAPING_W`/`net_mcts::floor_shaping_weight`). Ganzzahl-
/// Modus statt `f64`, weil es sich um eine ENDLICHE Auswahl von Formeln
/// handelt, nicht um ein stufenloses Gewicht:
///
/// - `0` (Default): Bestandskriterium, siehe `select_best_tiling_candidate`.
/// - `1`: Nutzer-Idee "reines P(Sieg)-Ranking" (History-Option (b) --
///   `punkte` fliesst NICHT mehr ein), siehe dort.
///
/// Ungueltige Werte (nicht 0/1, nicht parsbar) fallen mit einer einmaligen
/// stderr-Warnung auf `0` zurueck -- Laufzeit-Konfiguration darf nie einen
/// Self-Play-Prozess abstuerzen lassen (gleiche Disziplin wie `read_f64_env`
/// in `net_mcts.rs`).
fn tiling_select_mode_env() -> u8 {
    static MODE: std::sync::OnceLock<u8> = std::sync::OnceLock::new();
    *MODE.get_or_init(|| match std::env::var("MOSAIC_TILING_SELECT") {
        Ok(s) => match s.trim().parse::<i64>() {
            Ok(0) => 0,
            Ok(1) => 1,
            Ok(v) => {
                eprintln!(
                    "⚠️  MOSAIC_TILING_SELECT={v} nicht 0 oder 1 -- verwende Default 0 (Bestandskriterium)"
                );
                0
            }
            Err(_) => {
                eprintln!(
                    "⚠️  MOSAIC_TILING_SELECT={s:?} nicht als Zahl lesbar -- verwende Default 0 (Bestandskriterium)"
                );
                0
            }
        },
        Err(_) => 0,
    })
}

/// Task #20/#37: reiner Auswahlkern OHNE Env-Zugriff -- nimmt `mode` als
/// Parameter, damit er ohne `OnceLock`-Prozess-Cache/Env-Var-Umgebung direkt
/// mit synthetischen Kandidaten testbar ist. `best_first_step_valued`
/// (unten) ist nur noch ein duenner Wrapper, der `mode` aus
/// `tiling_select_mode_env` liest.
///
/// Beide Modi lesen NUR Werte, die der Solver (`c.points`) bzw. der
/// Aufrufer-Evaluator (`evaluator(&c.final_state)`) ohnehin schon fuer JEDEN
/// Kandidaten berechnen -- **kein zusaetzlicher Netz-Forward** gegenueber dem
/// Vor-Task-#37-Code, in keinem der beiden Modi. Der Evaluator wird weiterhin
/// genau einmal pro Kandidat aufgerufen (Reihenfolge/Anzahl unveraendert).
///
/// - `mode == 0` (Default, **Bestandskriterium, BYTE-IDENTISCH** zum
///   Vor-Task-#37-Code): `wert(Kandidat) = punkte(Kandidat) *
///   P(Sieg|final_state)`. `punkte` = `TilingOutcome::points`, die
///   Rundenpunkte DIESES Tiling-Abschlusses (Solver-Ausgabe, kein Score-
///   Zuwachs-Proxy). `P(Sieg)` = `evaluator(&c.final_state)`, in der
///   Produktion der kalibrierte WDL-Netz-Value-Kopf auf dem Folgezustand
///   NACH dem Abschluss. Entspricht History-Option (a) ("Bestand
///   `punkte * P(Sieg)`", Task #20).
/// - `mode == 1`: **"reines P(Sieg)-Ranking"** (History-Option (b)) --
///   `wert(Kandidat) = P(Sieg|final_state)`, der Punktefaktor entfaellt
///   komplett. Adressiert das im Task-#37-Befund notierte Risiko, dass der
///   kalibrierte WDL-Kopf (im Gegensatz zum alten, gestauchten Margen-Kopf)
///   ~2x weiter spreizt und damit die Punkte-Information im Produkt ZWEIMAL
///   einrechnet (einmal korrekt dosiert via `P(Sieg|Folgezustand)`, einmal
///   als eigener Faktor mit willkuerlichem Wechselkurs).
///
/// **Wichtiger Befund beim Nachlesen des Bestandscodes (dieser Task):** die
/// im urspruenglichen Task-#37-Auftrag als "Nutzer-Idee, abweichend vom
/// Bestand" bezeichnete Formel "punkte × P(Sieg)" IST bereits das
/// Bestandskriterium (Task #20, seit 2026-07-xx aktiv) -- die eigentliche,
/// in `archive/history.md` dokumentierte offene Frage ist Bestand (a) vs.
/// reines P(Sieg)-Ranking (b) [ggf. (c) als spaeterer dritter Arm, hier NICHT
/// umgesetzt]. `mode=0`/`mode=1` bilden deshalb (a) bzw. (b) ab, nicht zwei
/// identische Varianten der Produktformel.
///
/// Beide Modi: bei Wertegleichheit gewinnt deterministisch der ERSTE
/// Kandidat -- `>` statt `>=` in der Vergleichsschleife, kein Zufall, keine
/// zusaetzliche Tiebreak-Logik.
fn select_best_tiling_candidate(
    cands: Vec<TilingOutcome>,
    mode: u8,
    evaluator: &dyn Fn(&GameState) -> f64,
) -> Option<TilingStep> {
    let mut best: Option<(f64, TilingStep)> = None;
    for c in cands {
        let p_win = evaluator(&c.final_state);
        let val = match mode {
            1 => p_win,
            _ => f64::from(c.points) * p_win,
        };
        let better = match &best {
            Some((best_val, _)) => val > *best_val,
            None => true,
        };
        if better {
            best = Some((val, c.first_step));
        }
    }
    best.map(|(_, step)| step)
}

// ── Task #100: plattenbewusste Tiling-Zugwahl in Runden 1-4 ─────────────────
//
// `MOSAIC_TILING_PLATTEN_W` (Default `0.0` = aus). Bei Wert != 0 wird zu den
// Platzierungspunkten eines Tiling-Abschlusses `w * calculate_end_scoring(Brett
// NACH dem vollstaendigen Abschluss, state.scoring_tile_ids).total` addiert,
// und nach dieser SUMME gewaehlt -- siehe `best_first_step_platten_valued`.
//
// UNTERSCHIED zu `NET_TILING_TIEBREAK_ENABLED` (oben): dieser Zweig deckt
// Runde 1 MIT ab (Rundenfenster 1..=4, siehe `best_first_step_exact_or_valued`
// unten). Der bestehende Runde-1-Ausschluss des Netz-Stichentscheids ist gegen
// einen GELERNTEN Proxy begruendet (Value-Head-RMSE, siehe dessen Doku) --
// `calculate_end_scoring` ist dagegen eine BERECHNETE Formel ohne Schaetzfehler,
// dieser Ausschlussgrund entfaellt hier.
//
// NAEHERUNG in Runden 1-4 (bewusst, siehe `best_first_step_platten_valued`):
// das Kuppelraster aendert sich zwischen jetzt und Rundenende noch durch
// spaetere Drafting-Zuege -- `calculate_end_scoring` bewertet dort also ein
// Zwischenbrett, nicht das tatsaechliche Endbrett. Fuer eine Rangfolge unter
// den JETZT verfuegbaren Tiling-Abschluessen reicht die Richtung (welcher
// Abschluss bringt das Brett den aktivierten Wertungsplatten naeher); ein
// Schaetzfehler in der absoluten Hoehe schadet nur, wenn er die Rangfolge
// selbst verzerrt. In Runde 5 ist das Kuppelraster dagegen final -- dort gilt
// stattdessen der EXAKTE Pfad `best_first_step_round5`/`ROUND5_ENDSCORING_ENABLED`
// (Task #21), dieser Zweig bleibt per Rundenfenster aussen vor.

/// Liest `MOSAIC_TILING_PLATTEN_W` einmalig als `f64`. Gleiches Muster wie
/// `net_mcts::read_f64_env` -- hier LOKAL dupliziert statt dessen Sichtbarkeit
/// zu aendern: `read_f64_env` ist dort privat (`fn`, kein `pub`), und
/// `net_mcts.rs` ist laut Auftrag aktiv von parallelen Messjobs betroffen --
/// eine Sichtbarkeitsaenderung an einer im Hot-Path liegenden Datei fuer einen
/// tiling_solver-internen Bedarf haette ein groesseres Risiko (Rebuild/Merge-
/// Konflikt jener Jobs) als eine kleine Dopplung. Fehlend/leer -> Default
/// (kein Fehler), nicht parsbar -> Default + einmalige stderr-Warnung, kein
/// Panic (Laufzeit-Konfiguration darf einen Self-Play-Prozess nie abstuerzen
/// lassen).
fn read_f64_env_local(name: &str, default: f64) -> f64 {
    match std::env::var(name) {
        Ok(s) => match s.trim().parse::<f64>() {
            Ok(v) => v,
            Err(_) => {
                eprintln!("⚠️  {name}={s:?} nicht als Zahl lesbar -- verwende Default {default}");
                default
            }
        },
        Err(_) => default,
    }
}

thread_local! {
    /// Test-Override fuer [`tiling_platten_weight`] -- thread-lokal, gleiches
    /// Muster wie `STATS_OVERRIDE`/`CACHE_OVERRIDE` oben: erlaubt Tests, den
    /// Wert gezielt zu setzen, OHNE die prozessweite `OnceLock`-gecachte
    /// Env-Var fuer alle parallel laufenden `cargo test`-Threads zu bestimmen.
    static PLATTEN_WEIGHT_OVERRIDE: std::cell::Cell<Option<f64>> = std::cell::Cell::new(None);
}

fn tiling_platten_weight_env() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env_local("MOSAIC_TILING_PLATTEN_W", 0.0))
}

/// Laufzeitgewicht `w` fuer [`best_first_step_platten_valued`]. Default `0.0`
/// = aus -- `best_first_step_exact_or_valued` faellt dann exakt auf das
/// Bestandsverhalten zurueck (siehe dort).
fn tiling_platten_weight() -> f64 {
    PLATTEN_WEIGHT_OVERRIDE.with(|c| c.get()).unwrap_or_else(tiling_platten_weight_env)
}

#[cfg(test)]
pub(crate) fn set_platten_weight_override_for_test(v: Option<f64>) {
    PLATTEN_WEIGHT_OVERRIDE.with(|c| c.set(v));
}

/// Task #100: reiner Auswahlkern OHNE Env-Zugriff -- `w` als Parameter, direkt
/// mit konstruierten Stellungen testbar (gleiches Muster wie
/// `select_best_tiling_candidate`s `mode`-Parameter, Task #37).
///
/// Wert je Kandidat:
///
/// ```text
/// punkte(Abschluss) + w * calculate_end_scoring(Brett NACH dem Abschluss, state.scoring_tile_ids).total
/// ```
///
/// ADDITIV, nicht multiplikativ wie beim Netz-Stichentscheid
/// (`select_best_tiling_candidate`, Modus 0: `punkte * P(Sieg)`): der
/// Plattenwert soll Platzierungspunkte UEBERSTIMMEN koennen (Auftrag), eine
/// Multiplikation mit einem moeglicherweise kleinen oder negativen Punktestand
/// waere dafuer strukturell ungeeignet (ein 0-Punkte-Abschluss wuerde JEDEN
/// Plattenwert auf 0 ziehen).
///
/// VOR jeder Top-K-Beschraenkung: `top_k_tilings(.., MAX_TILING_LEAVES)` --
/// `MAX_TILING_LEAVES` ist die tatsaechliche Erschoepfungsgrenze von
/// `collect_tilings` selbst (siehe dessen Doku), nach dem Dedup kann `uniq`
/// dort also NIE mehr als `MAX_TILING_LEAVES` Eintraege haben -- die
/// `uniq.len() >= k`-Bremse in `top_k_tilings` greift folglich nie, und die
/// dortige punkte-sortierte Zwischenreihung bleibt fuer die Auswahl HIER
/// folgenlos: unten steht ein eigener Argmax ueber die Summe, nicht ueber die
/// von `top_k_tilings` bereits nach Punkten sortierte Reihenfolge. Dasselbe
/// "K weiten" nutzt bereits `best_first_step_round5` fuer denselben Zweck.
///
/// Tie-Break bei exaktem Wertegleichstand: der ERSTE Kandidat gewinnt (`>`
/// statt `>=`), deterministisch, kein Zufall -- gleiche Konvention wie
/// `select_best_tiling_candidate`.
fn best_first_step_platten_valued(state: &GameState, pi: usize, w: f64) -> Option<TilingStep> {
    let cands = top_k_tilings(state, pi, MAX_TILING_LEAVES);
    let mut best: Option<(f64, TilingStep)> = None;
    for c in cands {
        let end = crate::scoring::calculate_end_scoring(
            &c.final_state.players[pi],
            &c.final_state.scoring_tile_ids,
        )
        .total;
        let val = f64::from(c.points) + w * f64::from(end);
        let better = match &best {
            Some((best_val, _)) => val > *best_val,
            None => true,
        };
        if better {
            best = Some((val, c.first_step));
        }
    }
    best.map(|(_, step)| step)
}

/// Task #20: waehlt unter den bis zu `NET_TILING_TOPK` vollstaendigen
/// Tiling-Abschluessen den nach `select_best_tiling_candidate`
/// (`MOSAIC_TILING_SELECT`, Default-Modus `0` = Bestand) besten und liefert
/// dessen ERSTEN Schritt (das ist der Zug, den der Aufrufer tatsaechlich
/// ausfuehren muss -- siehe `TilingOutcome::first_step`).
///
/// `evaluator` ist bewusst eine generische Closure statt eines direkten
/// `&Net`-Parameters: dieses Modul hat keinen Rust-Unit-Test-Praezedenzfall
/// fuer `Net::load` in `#[cfg(test)]` (Projektkonvention, siehe Kommentar zu
/// `uniform_priors` in `round_transition_deep.rs`) -- Tests injizieren hier
/// stattdessen einen Fake-Evaluator, die Produktion (self_play.rs/py.rs) eine
/// echte Netz-Closure ueber `net_mcts`/`net.rs`.
///
/// `None`, wenn keine Kandidaten existieren (leeres Tiling, siehe
/// `top_k_tilings`) -- der Aufrufer faellt dann auf `best_first_step_exact`
/// zurueck (identisch zum unveraenderten Pfad).
pub fn best_first_step_valued(
    state: &GameState,
    pi: usize,
    evaluator: &dyn Fn(&GameState) -> f64,
) -> Option<TilingStep> {
    let cands = top_k_tilings(state, pi, NET_TILING_TOPK);
    select_best_tiling_candidate(cands, tiling_select_mode_env(), evaluator)
}

/// Task #20: kompletter Entscheid fuer den echten Tiling-Zug INKLUSIVE der
/// Anwendungsbedingung (Toggle + Rundenfenster) -- die einzige Stelle, die
/// diese Bedingung kennt, damit `self_play.rs::resolve_tiling_step` und
/// `py.rs::ai_tiling_step` sie nicht redundant duplizieren (und nie
/// auseinanderlaufen koennen).
///
/// REIHENFOLGE der Zweige (Task #100 NEU an erster Stelle). Sobald ein Zweig
/// einen Zug liefert, wird sofort `return`et -- kein Doppelweg, die folgenden
/// Zweige entscheiden diesen Zug dann nie mehr:
///
/// 1. `MOSAIC_TILING_PLATTEN_W != 0` UND Runde in `1..=4` ->
///    `best_first_step_platten_valued` (Task #100, additive Endwertungs-Summe,
///    KEIN Netz noetig). Liefert das `Some`, ist der Zug entschieden.
/// 2. Sonst: `NET_TILING_TIEBREAK_ENABLED` UND Runde in `2..=4` UND ein
///    Evaluator vorhanden -> `best_first_step_valued` (Task #20, Netz-
///    Stichentscheid `punkte * P(Sieg)` bzw. `P(Sieg)`).
/// 3. Sonst: `best_first_step_exact` -- deckt Runde >= 5 selbst ab
///    (`ROUND5_ENDSCORING_ENABLED`/`best_first_step_round5`, Task #21) und ist
///    andernfalls die reine Punktemaximierung, byte-identisch zum Vor-
///    Task-#20-Verhalten.
///
/// `evaluator: None` (Heuristik-Spieler, kein Netz geladen) oder Runde
/// ausserhalb [2,4] oder Toggle aus → Zweig 2 entfaellt. Ist zusaetzlich
/// `MOSAIC_TILING_PLATTEN_W` unveraendert `0.0` (Default, siehe
/// `tiling_platten_weight`) oder die Runde ausserhalb [1,4], entfaellt auch
/// Zweig 1 -- dann EXAKT `best_first_step_exact`, byte-identisch zum
/// Vor-Task-#20-Verhalten.
///
/// Runde 1 in Zweig 2 bewusst ausgeschlossen: das Value-Head ist dort blind
/// (RMSE 0,2531 ~ Zielstreuung 0,2538, siehe Projekt-Notizen zu Task #20) --
/// eine Multiplikation mit im Wesentlichen Rauschen waere reiner Schaden.
/// Zweig 1 (Task #100) schliesst Runde 1 dagegen bewusst EIN, siehe dessen
/// Modul-Kommentar oben -- `calculate_end_scoring` ist dort eine berechnete
/// Formel ohne Schaetzfehler, der Ausschlussgrund von Zweig 2 greift nicht.
///
/// Runde >= 5 in Zweig 1 UND Zweig 2 bewusst ausgeschlossen: dort gilt
/// stattdessen Task #21 (`ROUND5_ENDSCORING_ENABLED`/`best_first_step_round5`)
/// -- die dort exakt berechenbare Endwertung (Kuppelraster final, kein
/// Naeherungsfehler mehr) schlaegt sowohl einen gelernten Proxy als auch die
/// in Runden 1-4 nur naeherungsweise gueltige `calculate_end_scoring`
/// strukturell, siehe dessen Doku oben. `best_first_step_exact` deckt diesen
/// Fall bereits selbst ab (eigene `ROUND5_ENDSCORING_ENABLED`-Verzweigung) --
/// hier also nichts zusaetzlich zu tun, nur nicht versehentlich mit einem der
/// beiden Stichentscheide ueberschreiben.
pub fn best_first_step_exact_or_valued(
    state: &GameState,
    pi: usize,
    evaluator: Option<&dyn Fn(&GameState) -> f64>,
) -> TilingStep {
    // Zweig 1 (Task #100): additive Endwertungs-Summe, Runden 1-4, kein Netz
    // noetig. VOR Zweig 2 geprueft -- entscheidet er, wird Zweig 2 fuer diesen
    // Zug gar nicht mehr aufgerufen (kein Doppelweg, siehe Doku oben).
    if (1..=4).contains(&state.round_number) {
        let w = tiling_platten_weight();
        if w != 0.0 {
            if let Some(step) = best_first_step_platten_valued(state, pi, w) {
                return step;
            }
        }
    }
    // Zweig 2 (Task #20): Netz-Stichentscheid, Runden 2-4.
    if NET_TILING_TIEBREAK_ENABLED && (2..=4).contains(&state.round_number) {
        if let Some(eval) = evaluator {
            if let Some(step) = best_first_step_valued(state, pi, eval) {
                return step;
            }
        }
    }
    // Zweig 3: reine Punktemaximierung (deckt Runde >= 5 selbst ab).
    best_first_step_exact(state, pi)
}

/// Greedy-Variante (Hot-Path / Tests).
pub fn best_first_step(state: &GameState, pi: usize) -> TilingStep {
    best_first_step_inner(state, pi, false)
}

/// Exakte Variante für den tatsächlich gespielten KI-Tiling-Zug: durchsucht die
/// Chip-Allokationen, damit mehrfarbige Plättchen im Engpass optimal verteilt
/// werden. Wird nur einmal pro Zug aufgerufen → bezahlbar.
pub fn best_first_step_exact(state: &GameState, pi: usize) -> TilingStep {
    // Task #21: in Runde 5 ist die Endwertung exakt berechenbar (das Spiel endet
    // nach diesem Tiling) -- dort wird sie mitmaximiert statt ignoriert.
    if ROUND5_ENDSCORING_ENABLED && state.round_number >= 5 {
        if let Some(step) = best_first_step_round5(state, pi) {
            return step;
        }
    }
    best_first_step_inner(state, pi, true)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::board::PlayerBoard;
    use crate::dome::build_dome_tile_pool;
    use crate::state::{setup_new_game, Phase};
    use crate::tile::TileColor::*;
    use rand::rngs::StdRng;
    use rand::RngExt;
    use rand::SeedableRng;

    fn tiling_state(seed: u64) -> GameState {
        let mut rng = StdRng::seed_from_u64(seed);
        let mut s = setup_new_game(["P1".into(), "P2".into()], 0, &mut rng);
        for p in s.players.iter_mut() {
            p.start_tile_pending = false;
        }
        s.phase = Phase::Tiling;
        s
    }

    #[test]
    fn solo_full_row_scores_one() {
        let mut s = tiling_state(7);
        // Slot (0,0) = pool[2] = [Tuerkis, Rot, Blau, Wild]; si1 = Rot.
        let tile = build_dome_tile_pool()[2].clone();
        s.players[0].dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        s.players[0].pattern_lines[0].add_tiles(&[Rot]); // volle Reihe 0
        // Genau ein platzierbarer Stein, alleinstehend → 1 Punkt.
        assert_eq!(solve_max_tiling_points(&s, 0), 1);
        // best_first_step platziert (kein End).
        assert!(matches!(best_first_step(&s, 0), TilingStep::Place(_)));
    }

    #[test]
    fn no_placeable_row_yields_end_and_zero() {
        let s = tiling_state(7); // leeres Brett, keine vollen Reihen
        assert_eq!(solve_max_tiling_points(&s, 0), 0);
        assert_eq!(best_first_step(&s, 0), TilingStep::End);
    }

    #[test]
    fn solver_matches_engine_when_played_out() {
        // Konsistenz: solve_round_final_score == real durchgespielter Score,
        // wenn man best_first_step bis End anwendet.
        let mut s = tiling_state(7);
        let tile = build_dome_tile_pool()[2].clone(); // si1 = Rot
        s.players[0].dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        s.players[0].pattern_lines[0].add_tiles(&[Rot]);
        let predicted = solve_round_final_score(&s, 0);

        // Real durchspielen (greedy nach Solver).
        let pi = 0;
        loop {
            match best_first_step(&s, pi) {
                TilingStep::Place(ta) => {
                    execute_full_tiling(&mut s, pi, &ta).unwrap();
                }
                TilingStep::Chips { row, chips } => {
                    apply_bonus_chips_with(&mut s.players[pi], row, &chips);
                }
                TilingStep::End => break,
            }
        }
        let realized = s.players[pi].score
            + s.players[pi].broken_penalty()
            + if s.players[pi].holds_first_player_marker { FIRST_PLAYER_MARKER_PENALTY } else { 0 };
        assert_eq!(predicted, realized);
    }

    #[test]
    fn counts_cross_row_vertical_line() {
        // Reihenübergreifende Linie: Reihe 1 (Schwarz) → 6x6 (0,1), Reihe 2
        // (Schwarz) → 6x6 (1,1, Wild). Zusammen vertikale Linie → 1 + 2 = 3
        // (NICHT 1 + 1 = 2, wie die per-Reihe-Heuristik schätzen würde).
        let mut s = tiling_state(7);
        let tile = build_dome_tile_pool()[11].clone(); // [Tuerkis, Schwarz, Rot, Wild]
        s.players[0].dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        s.players[0].pattern_lines[0].add_tiles(&[Schwarz]);
        s.players[0].pattern_lines[1].add_tiles(&[Schwarz, Schwarz]);
        assert_eq!(solve_max_tiling_points(&s, 0), 3);
        // Erwartete Rundenpunkte (estimated_score) = Solver-Score − aktueller Score.
        assert_eq!(solve_round_final_score(&s, 0) - s.players[0].score, 3);
    }

    #[test]
    fn uses_chips_to_complete_and_place() {
        use crate::dome::BonusChip;
        let mut s = tiling_state(7);
        // Reihe 2 (cap 3): 1 Rot → 2 fehlen; 4 Rot-Chips → komplettierbar.
        s.players[0].pattern_lines[2].add_tiles(&[Rot]);
        for i in 0..4 {
            s.players[0].bonus_chips.push(BonusChip { chip_id: i, colors: vec![Rot] });
        }
        // Dome-Reihe 1 (Reihe 2 → dome_row 1), Slot mit offenem Rot an si0/si1:
        // pool[2] si1 = Rot.
        let tile = build_dome_tile_pool()[2].clone();
        s.players[0].dome_grid.place_dome_tile(tile, 1, 0).unwrap();
        // Ohne Chips: Reihe 2 nicht voll → 0 Punkte. Mit Chips: komplettieren +
        // platzieren → ≥1 Punkt. Solver muss die Chip-Option nutzen.
        assert!(solve_max_tiling_points(&s, 0) >= 1);
        let first = best_first_step(&s, 0);
        assert!(matches!(first, TilingStep::Chips { row: 2, .. } | TilingStep::Place(_)));
    }

    #[test]
    fn greedy_chip_alloc_tradeoff_in_contention() {
        use crate::dome::BonusChip;
        // Engpass: 2 Doppel-Chips [blau,rot] + [blau] + [rot]. Reihe 3 (Rot,
        // fehlt 1) und Reihe 4 (Blau, fehlt 1) je per 2 farbgleichen Chips
        // komplettierbar. Der DFS nutzt im Hot-Path die GREEDY-Allokation: sie
        // verbrennt beide Doppel-Chips auf die erste Reihe → nur 1 Reihe legbar.
        // (Die exakte Allokationssuche käme auf 3, ist aber an jedem MCTS-Blatt
        // zu teuer — bewusster Tradeoff; `chip_allocations` bleibt dafür da.)
        let mut s = tiling_state(7);
        // Slot (1,0) = pool[2] [Tuerkis, Rot, Blau, Wild]:
        //   si1 = Rot @ 6x6 (2,1) → Reihe 3 (idx 2, valid_si [0,1]).
        //   si2 = Blau @ 6x6 (3,0) → Reihe 4 (idx 3, valid_si [2,3]).
        let tile = build_dome_tile_pool()[2].clone();
        s.players[0].dome_grid.place_dome_tile(tile, 1, 0).unwrap();
        s.players[0].pattern_lines[2].add_tiles(&[Rot, Rot]); // cap 3 → 1 fehlt
        s.players[0].pattern_lines[3].add_tiles(&[Blau, Blau, Blau]); // cap 4 → 1 fehlt
        s.players[0].bonus_chips = vec![
            BonusChip { chip_id: 0, colors: vec![Blau, Rot] },
            BonusChip { chip_id: 1, colors: vec![Blau, Rot] },
            BonusChip { chip_id: 2, colors: vec![Blau] },
            BonusChip { chip_id: 3, colors: vec![Rot] },
        ];
        // Greedy-DFS (Hot-Path): verbrennt beide Doppel-Chips → nur 1 Reihe = 1.
        assert_eq!(solve_max_tiling_points(&s, 0), 1);
        // EXAKT (echter Zug): beide Reihen legbar; Blau aufs Wild-Feld (3,1)
        // bildet mit Rot auf (2,1) eine vertikale Linie → 1 + 2 = 3.
        assert_eq!(solve_max_tiling_points_exact(&s, 0), 3);
        // Der erste exakte Schritt ist ein kontentionsschonender Chip-Schritt.
        assert!(matches!(best_first_step_exact(&s, 0), TilingStep::Chips { .. }));
    }

    #[test]
    fn chip_allocations_offers_distinct_choices() {
        use crate::dome::BonusChip;
        use crate::round_end::chip_allocations;
        let mut p = PlayerBoard::new(0, "P");
        p.pattern_lines[2].add_tiles(&[Rot, Rot]); // Reihe 3, 1 fehlt
        p.bonus_chips = vec![
            BonusChip { chip_id: 0, colors: vec![Blau, Rot] },
            BonusChip { chip_id: 1, colors: vec![Rot] },
            BonusChip { chip_id: 2, colors: vec![Rot] },
        ];
        // 1 fehlend → 2 rot-tragende ODER 3 beliebige. Mehrere distinkte
        // Allokationen (z.B. {0,1}, {1,2}); deduppliziert nach Farb-Signatur.
        let allocs = chip_allocations(&p, 2);
        assert!(allocs.len() >= 2, "mehrere distinkte Allokationen erwartet: {allocs:?}");
        // Jede Allokation komplettiert die Reihe.
        for a in &allocs {
            let mut q = p.clone();
            assert!(apply_bonus_chips_with(&mut q, 2, a));
            assert!(q.pattern_lines[2].is_complete());
        }
    }

    #[test]
    fn solver_counts_special_bonus_and_neighbor() {
        // Verifikation: (1) Special-Bonus = Reihennummer wird vom Solver gezählt,
        // (2) der ausgelöste Special zählt als Nachbar für eine spätere Fliese.
        //
        // Slot A (0,0) = pool[8] [Tuerkis(si0,(0,0)), Rot(si1,(0,1)),
        //   Blau(si2,(1,0)), Special(si3,(1,1))]. si0/si1 aus "Vorrunden" gefüllt.
        // Slot B (1,0) = pool[2] [Tuerkis(si0), Rot(si1,(2,1)), Blau, Wild].
        let mut s = tiling_state(7);
        s.dome_display.clear(); // nur bestehende Slots nutzbar (deterministisch)

        let mut a = build_dome_tile_pool()[8].clone();
        a.spaces[0].placed_color = Some(Tuerkis); // (0,0)
        a.spaces[1].placed_color = Some(Rot); // (0,1)
        s.players[0].dome_grid.place_dome_tile(a, 0, 0).unwrap();

        let mut b = build_dome_tile_pool()[2].clone();
        b.tile_id = 200;
        s.players[0].dome_grid.place_dome_tile(b, 1, 0).unwrap();

        // Reihe 2 (idx 1, cap 2) → Blau auf Slot A si2 (1,0): füllt das 3. Feld
        //   → Special si3 (1,1) löst aus. Reihe 3 (idx 2, cap 3) → Rot auf (2,1).
        s.players[0].pattern_lines[1].add_tiles(&[Blau, Blau]);
        s.players[0].pattern_lines[2].add_tiles(&[Rot, Rot, Rot]);

        // Erwartung:
        //  - Blau@(1,0): vertikale Linie (0,0)+(1,0) = 2. Special-Bonus: Reihe von
        //    si3 = slot_row*2 + 3/2 = 1 → +2. = 4.
        //  - Rot@(2,1): vertikale Linie (0,1)Rot + (1,1)Special + (2,1)Rot = 3
        //    (Special zählt als gefüllter Nachbar). = 3.
        //  Summe = 7. (Ohne Special-Bonus: 5; ohne Nachbar-Effekt: 5.)
        assert_eq!(solve_max_tiling_points(&s, 0), 7);
    }

    /// Referenz-Implementierung der Zugwahl, beide Varianten getrennt
    /// nachgerechnet -- bewusst dupliziert, damit der Test nicht dieselbe
    /// Codezeile prueft, die er absichern soll.
    fn reference_argmax(state: &GameState, pi: usize, shaped: bool) -> TilingStep {
        let steps = legal_steps(state, pi, true);
        if steps.is_empty() {
            return TilingStep::End;
        }
        let mut budget = NODE_BUDGET;
        let mut best_step = TilingStep::End;
        let mut best_val = f64::NEG_INFINITY;
        let base = crate::scoring::wertung_progress(&state.players[pi], &state.scoring_tile_ids);
        for step in steps {
            if budget == 0 {
                break;
            }
            if let Some((next, pts)) = apply_step(state, pi, &step) {
                let mut val = f64::from(pts + solve_rec(&next, pi, 1, true, &mut budget));
                if shaped {
                    val += TILING_SHAPING_WEIGHT
                        * (crate::scoring::wertung_progress(
                            &next.players[pi],
                            &next.scoring_tile_ids,
                        ) - base);
                }
                if val > best_val {
                    best_val = val;
                    best_step = step;
                }
            }
        }
        best_step
    }

    /// Reiche Tiling-Stellung: volles 3x3-Kuppelraster, ein Teil der Felder
    /// vorbefuellt (erzeugt fast-volle Mosaikreihen/-spalten/-diagonalen, wo
    /// `wertung_progress` grosse Deltas liefert), mehrere gefuellte Musterreihen.
    ///
    /// NOETIG, weil `tiling_state()` allein ein LEERES Kuppelraster hat: dort
    /// gibt `generate_tiling_actions` nichts zurueck, jeder Vergleich waere
    /// `End == End` und damit leer gruen.
    fn rich_state(seed: u64) -> GameState {
        let mut rng = StdRng::seed_from_u64(seed);
        let mut s = tiling_state(seed);
        s.dome_display.clear();
        s.scoring_tile_ids = vec![0, 1, 2]; // Reihen(3) / Spalten(7) / Diagonalen(10)
        let pool = build_dome_tile_pool();
        let mut tid = 300;
        for r in 0..3 {
            for c in 0..3 {
                let mut t = pool[rng.random_range(0..pool.len())].clone();
                t.tile_id = tid;
                tid += 1;
                for si in 0..4 {
                    // ~60% vorbefuellt: genug fuer fast-volle Linien, laesst aber
                    // noch freie Felder fuer echte Zugauswahl.
                    if rng.random_range(0..100) < 60 {
                        t.spaces[si].placed_color = t.spaces[si].required_color;
                    }
                }
                let _ = s.players[0].dome_grid.place_dome_tile(t, r, c);
            }
        }
        s.players[0].pattern_lines[1].add_tiles(&[Blau, Blau]);
        s.players[0].pattern_lines[2].add_tiles(&[Rot, Rot, Rot]);
        s.players[0].pattern_lines[3].add_tiles(&[Tuerkis, Tuerkis, Tuerkis, Tuerkis]);
        s
    }

    #[test]
    fn tiling_shaping_follows_toggle_and_position_discriminates() {
        // Erste Stellung suchen, in der Sofortpunkte und Plattenfortschritt
        // AUSEINANDER zeigen -- sonst wuerde der Test das Shaping nicht pruefen.
        let mut found = None;
        for seed in 1u64..=200 {
            let s = rich_state(seed);
            if legal_steps(&s, 0, true).len() < 2 {
                continue;
            }
            let shaped = reference_argmax(&s, 0, true);
            let unshaped = reference_argmax(&s, 0, false);
            if shaped != unshaped {
                found = Some((seed, s, shaped, unshaped));
                break;
            }
        }
        let (seed, s, shaped, unshaped) = found.expect(
            "keine diskriminierende Stellung in 200 Seeds gefunden -- entweder ist der \
             Shaping-Term wirkungslos oder rich_state() erzeugt keine echten Zugauswahlen",
        );

        let expected = if TILING_SHAPING_ENABLED { &shaped } else { &unshaped };
        assert_eq!(
            &best_first_step_exact(&s, 0),
            expected,
            "Seed {seed}: best_first_step_exact folgt TILING_SHAPING_ENABLED={TILING_SHAPING_ENABLED} nicht"
        );
    }

    #[test]
    fn tiling_shaping_off_is_pure_immediate_points() {
        // Paritaet des f64-Refactors: solange der Toggle AUS ist, muss die
        // Zugwahl exakt die alte i32-Sofortpunkte-Maximierung sein.
        if TILING_SHAPING_ENABLED {
            return;
        }
        let mut checked = 0;
        for seed in 1u64..=60 {
            let s = rich_state(seed);
            if legal_steps(&s, 0, true).is_empty() {
                continue;
            }
            checked += 1;
            assert_eq!(
                best_first_step_exact(&s, 0),
                reference_argmax(&s, 0, false),
                "Seed {seed}: OFF weicht von reiner Sofortpunkte-Maximierung ab"
            );
        }
        // Schutz gegen einen leer gruenen Test.
        assert!(checked >= 20, "nur {checked} Stellungen mit Zuegen geprueft");
    }

    /// Formeltest fuer `tiling_outcome_signature` selbst: gleiche Fuellung
    /// (hier: beide leer) + verschiedener Chip-Rest => verschiedene Signatur.
    /// Zusaetzlich: Chip-REIHENFOLGE darf keine Rolle spielen (Permutation
    /// desselben Bestands => gleiche Signatur), sonst waechst die
    /// Kandidatenzahl in `top_k_tilings` kuenstlich durch reine Vec-Ordnung.
    #[test]
    fn tiling_outcome_signature_distinguishes_chip_remainder() {
        use crate::dome::BonusChip;
        let mut a = tiling_state(7);
        let mut b = tiling_state(7);
        a.players[0].bonus_chips = vec![BonusChip { chip_id: 0, colors: vec![Rot] }];
        b.players[0].bonus_chips = vec![
            BonusChip { chip_id: 0, colors: vec![Rot] },
            BonusChip { chip_id: 1, colors: vec![Blau] },
        ];
        let sig_a = tiling_outcome_signature(&a, 0);
        let sig_b = tiling_outcome_signature(&b, 0);
        assert_eq!(sig_a.0, sig_b.0, "Fuellung sollte identisch sein (beide leer)");
        assert_ne!(sig_a.1, sig_b.1, "unterschiedlicher Chip-Rest muss unterschiedliche Signatur ergeben");
        assert_ne!(sig_a, sig_b);

        // Permutation desselben Bestands => gleiche Signatur.
        let mut c = tiling_state(7);
        c.players[0].bonus_chips = vec![
            BonusChip { chip_id: 1, colors: vec![Blau] },
            BonusChip { chip_id: 0, colors: vec![Rot] },
        ];
        assert_eq!(
            tiling_outcome_signature(&b, 0),
            tiling_outcome_signature(&c, 0),
            "reine Chip-Reihenfolge darf die Signatur nicht aendern"
        );
    }

    /// End-zu-End-Beleg ueber `top_k_tilings`: eine echte Stellung, in der
    /// ZWEI Chip-Allokationen dieselbe fehlende Musterreihe komplettieren
    /// (2 farbgleiche Chips ODER 3 beliebige, siehe `chip_allocations`/
    /// `chips_complete` in round_end.rs), danach folgt exakt EIN Platzierungs-
    /// zug und keine weiteren Schritte. Beide Pfade landen auf demselben
    /// Endbrett (identische Fuellung, identische Rundenpunkte), aber mit
    /// unterschiedlichem Chip-Rest (0 vs. 1 uebrig). Vor dem Fix (Signatur nur
    /// ueber die Fuellung) haette die Dedup-Schleife in `top_k_tilings` einen
    /// der beiden verworfen.
    #[test]
    fn top_k_tilings_keeps_both_outcomes_with_different_chip_remainder() {
        use crate::dome::BonusChip;
        let mut s = tiling_state(7);
        // Slot (1,0) = pool[2] [Tuerkis, Rot, Blau, Wild]; si1 = Rot @ 6x6(2,1)
        // -> Reihe 3 (idx 2). Reihe 4 (idx 3) bleibt leer, damit der Blau-Slot
        // (si2) NICHT platzierbar ist -- exakt ein Platzierungszug moeglich.
        let tile = build_dome_tile_pool()[2].clone();
        s.players[0].dome_grid.place_dome_tile(tile, 1, 0).unwrap();
        s.players[0].pattern_lines[2].add_tiles(&[Rot, Rot]); // cap 3, 1 fehlt
        // 2 rot-tragende Chips (s=2, komplettiert allein) + 1 fachfremder Chip,
        // der nur in der "3-beliebige"-Allokation (s=3) mitgenutzt wird.
        s.players[0].bonus_chips = vec![
            BonusChip { chip_id: 0, colors: vec![Rot] },
            BonusChip { chip_id: 1, colors: vec![Rot] },
            BonusChip { chip_id: 2, colors: vec![Blau] },
        ];

        let outcomes = top_k_tilings(&s, 0, 10);
        assert_eq!(
            outcomes.len(),
            2,
            "erwarte genau 2 ueberlebende Abschluesse (0 bzw. 1 Chip uebrig): {:?}",
            outcomes.iter().map(|o| o.final_state.players[0].bonus_chips.len()).collect::<Vec<_>>()
        );
        let mut remainders: Vec<usize> =
            outcomes.iter().map(|o| o.final_state.players[0].bonus_chips.len()).collect();
        remainders.sort_unstable();
        assert_eq!(remainders, vec![0, 1], "Chip-Reste muessen 0 und 1 sein");
        // Beide Abschluesse haben dieselben Rundenpunkte (identisches Endbrett).
        assert_eq!(outcomes[0].points, outcomes[1].points);
        // Und dieselbe Kuppelfuellung (nur der Chip-Rest unterscheidet sie).
        assert_eq!(
            tiling_outcome_signature(&outcomes[0].final_state, 0).0,
            tiling_outcome_signature(&outcomes[1].final_state, 0).0
        );
    }

    #[test]
    fn unused_player_helper() {
        // broken_penalty/Marker fließen ins Finale ein.
        let mut p = PlayerBoard::new(0, "P");
        p.add_broken(&[Rot, Rot]); // -1 -2 = -3
        p.holds_first_player_marker = true;
        let mut s = tiling_state(7);
        s.players[0] = p;
        // Keine vollen Reihen → 0 Tiling-Punkte; Score 5 (Start) - 3 - 2 = 0.
        assert_eq!(solve_round_final_score(&s, 0), 5 - 3 - 2);
    }

    // ── Task #20: netz-gefuehrter Stichentscheid ────────────────────────────

    /// Sucht eine `rich_state`-Stellung in Runde 2 mit mindestens zwei
    /// punktegleichen Top-Abschluessen mit UNTERSCHIEDLICHEM ersten Schritt --
    /// nur dort kann ein Stichentscheid ueberhaupt etwas kippen. Gibt
    /// (Seed, Zustand, Kandidaten) zurueck. Gemeinsam genutzt von mehreren
    /// Tests unten, damit die Suche nicht viermal dupliziert wird.
    fn find_tied_tiling_candidates(max_seed: u64) -> Option<(u64, GameState, Vec<TilingOutcome>)> {
        for seed in 1..=max_seed {
            let mut s = rich_state(seed);
            s.round_number = 2; // Task #20 gilt nur fuer Runden 2-4.
            let cands = top_k_tilings(&s, 0, NET_TILING_TOPK);
            if cands.len() < 2 {
                continue;
            }
            if cands[0].points == cands[1].points && cands[0].first_step != cands[1].first_step {
                return Some((seed, s, cands));
            }
        }
        None
    }

    /// (a) Paritaet: `best_first_step_exact_or_valued` mit `evaluator: None`
    /// (Heuristik-Pfad -- kein Netz geladen) ist byte-identisch zu
    /// `best_first_step_exact`, unabhaengig vom Toggle und von der Runde.
    /// `best_first_step_valued` wird dabei gar nicht erst aufgerufen (das
    /// `if let Some(eval) = evaluator` in `best_first_step_exact_or_valued`
    /// greift nie).
    #[test]
    fn exact_or_valued_without_evaluator_matches_exact() {
        let mut checked = 0;
        for seed in 1u64..=60 {
            for round in [1u32, 2, 3, 4, 5] {
                let mut s = rich_state(seed);
                s.round_number = round;
                if legal_steps(&s, 0, true).is_empty() {
                    continue;
                }
                checked += 1;
                assert_eq!(
                    best_first_step_exact_or_valued(&s, 0, None),
                    best_first_step_exact(&s, 0),
                    "Seed {seed} Runde {round}: evaluator=None weicht von best_first_step_exact ab"
                );
            }
        }
        assert!(checked >= 20, "nur {checked} Stellungen geprueft");
    }

    /// (b) Diskriminierung: unter zwei punktegleichen Top-Abschluessen mit
    /// unterschiedlichem ersten Schritt kippt ein gezielter Fake-Evaluator
    /// (bevorzugt das ZWEITE Endbrett, per Signatur identifiziert, nicht per
    /// Index) die Wahl weg vom neutralen (punktegierigen) Ergebnis. Muss
    /// fehlschlagen statt leer-gruen zu sein, wenn keine diskriminierende
    /// Stellung existiert -- `expect` statt `if let`.
    #[test]
    fn best_first_step_valued_biased_evaluator_flips_tied_choice() {
        let (seed, s, cands) = find_tied_tiling_candidates(300).expect(
            "keine Runde-2-Stellung mit >=2 punktegleichen, unterschiedlichen Top-Abschluessen \
             in 300 Seeds gefunden -- Testkonstruktion ueberpruefen",
        );

        // Neutraler (konstanter) Evaluator: reine Punkte-Reihenfolge, cands[0]
        // gewinnt (top_k_tilings sortiert absteigend, cands[0] kommt zuerst
        // und `>` in der Argmax-Schleife bevorzugt den ZUERST gefundenen bei
        // exaktem Gleichstand).
        let neutral = |_: &GameState| 0.5;
        let neutral_choice = best_first_step_valued(&s, 0, &neutral).expect("Kandidaten vorhanden");
        assert_eq!(
            neutral_choice, cands[0].first_step,
            "Seed {seed}: neutraler Evaluator sollte den Punkte-Sieger waehlen"
        );

        // Diskriminierender Evaluator: bevorzugt gezielt das Endbrett von
        // cands[1] (Signatur-Vergleich, weil der Evaluator nur das GameState
        // sieht, keinen Kandidaten-Index).
        let target_sig = tiling_outcome_signature(&cands[1].final_state, 0);
        let biased = |gs: &GameState| if tiling_outcome_signature(gs, 0) == target_sig { 0.9 } else { 0.1 };
        let biased_choice = best_first_step_valued(&s, 0, &biased).expect("Kandidaten vorhanden");
        assert_eq!(
            biased_choice, cands[1].first_step,
            "Seed {seed}: Evaluator sollte den zweiten (punktegleichen) Abschluss erzwingen"
        );
        assert_ne!(
            biased_choice, neutral_choice,
            "Seed {seed}: Stichentscheid muss die Wahl gegenueber dem neutralen Evaluator tatsaechlich kippen"
        );
    }

    /// (c) Nullkosten-Invariante bei REALISTISCH kleiner Value-Spreizung.
    ///
    /// ACHTUNG: das ist NICHT strukturell garantiert -- `punkte * value` ist
    /// eine echte Multiplikation, ein extremer Evaluator-Ausschlag KANN
    /// Punkte kosten (siehe Testfall b: dort wird das bewusst ausgenutzt).
    /// Bei den GEMESSENEN Value-Spreizungen realer Netze (Median ~0,017,
    /// siehe `NET_TILING_TIEBREAK_ENABLED`-Doku) passiert das laut
    /// `tiling_candidate_spread.json` (51/51 Faelle) nie -- dort korreliert
    /// der Wert eines echten Netzes NICHT systematisch invers mit den
    /// Punkten. Ein Evaluator, der stattdessen streng nach Punkte-RANG
    /// ansteigt (dem sortierten `top_k_tilings`-Index), waere das exakte
    /// Gegenteil -- er wuerde SYSTEMATISCH die punktschwaecheren Kandidaten
    /// bevorzugen und war in einer fruehen Version dieses Tests genau deshalb
    /// rot (Seed 3: 20 statt 21 Punkte). Hier deshalb per Hash der
    /// Endbrett-Signatur (unkorreliert zum Punkte-Rang) auf eine enge Spanne
    /// [0,49; 0,51] (Spreizung 0,02, nahe am gemessenen Median 0,017)
    /// verteilt -- NICHT als Beweis einer strukturellen Garantie, siehe
    /// Testfall (b) fuer den Gegenbeweis mit einem gezielt adversen Evaluator.
    #[test]
    fn best_first_step_valued_small_spread_does_not_cost_points_empirically() {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        let mut checked = 0;
        for seed in 1u64..=150 {
            let mut s = rich_state(seed);
            s.round_number = 2;
            let cands = top_k_tilings(&s, 0, NET_TILING_TOPK);
            if cands.len() < 2 {
                continue;
            }
            checked += 1;
            let max_points = cands.iter().map(|c| c.points).max().unwrap();

            let evaluator = |gs: &GameState| {
                let sig = tiling_outcome_signature(gs, 0);
                let mut hasher = DefaultHasher::new();
                sig.0.hash(&mut hasher);
                sig.1.hash(&mut hasher);
                let h = hasher.finish();
                0.49 + 0.02 * ((h % 1_000_000) as f64 / 999_999.0)
            };

            // Referenz-Implementierung dupliziert (wie `reference_argmax`
            // weiter oben) statt `best_first_step_valued`s eigene Codezeile
            // zu pruefen -- liefert zusaetzlich die Punkte des gewaehlten
            // Kandidaten, die `TilingStep` selbst nicht traegt.
            let mut best: Option<(f64, i32)> = None;
            for c in &cands {
                let val = f64::from(c.points) * evaluator(&c.final_state);
                if best.map_or(true, |(bv, _)| val > bv) {
                    best = Some((val, c.points));
                }
            }
            let (_, chosen_points) = best.expect("Kandidaten vorhanden");
            assert_eq!(
                chosen_points, max_points,
                "Seed {seed}: realistisch kleine Evaluator-Spreizung hat Punkte gekostet"
            );
        }
        assert!(checked >= 10, "nur {checked} Stellungen mit >=2 Kandidaten geprueft");
    }

    /// (d) Rundengrenzen: derselbe stark diskriminierende Evaluator wie in
    /// Test (b), aber auf Runde 1 bzw. 5 angewendet -- `best_first_step_exact_or_valued`
    /// muss dort die ALTE (reine Punkte-)Wahl liefern, unabhaengig vom
    /// Evaluator. Nutzt dieselbe Stellung wie Test (b) (dort in Runde 2
    /// gefunden), nur mit ueberschriebener `round_number` -- die
    /// Kandidatenmenge selbst haengt nicht von `round_number` ab.
    #[test]
    fn exact_or_valued_ignores_evaluator_outside_rounds_2_to_4() {
        let (seed, mut s, cands) = find_tied_tiling_candidates(300).expect(
            "keine Runde-2-Stellung mit >=2 punktegleichen, unterschiedlichen Top-Abschluessen \
             in 300 Seeds gefunden -- Testkonstruktion ueberpruefen",
        );
        let target_sig = tiling_outcome_signature(&cands[1].final_state, 0);
        let biased = |gs: &GameState| if tiling_outcome_signature(gs, 0) == target_sig { 0.9 } else { 0.1 };

        for round in [1u32, 5] {
            s.round_number = round;
            let expected = best_first_step_exact(&s, 0);
            let actual = best_first_step_exact_or_valued(&s, 0, Some(&biased));
            assert_eq!(
                actual, expected,
                "Seed {seed} Runde {round}: Evaluator haette die Wahl gekippt, \
                 ausserhalb Runde 2-4 darf er das nicht"
            );
        }
    }

    // ── Task #37: Laufzeit-Auswahlkriterium (MOSAIC_TILING_SELECT) ──────────

    /// Paritaets-Bedingung (gleiches Muster wie
    /// `net_mcts::tests::env_knoepfe_defaults_sind_bestandsverhalten`): ohne
    /// gesetzte `MOSAIC_TILING_SELECT`-Env-Var MUSS der Laufzeit-Knopf exakt
    /// den Default-Modus `0` liefern (OnceLock cached den ungesetzten Zustand
    /// in der Testumgebung).
    #[test]
    fn env_knoepfe_defaults_sind_bestandsverhalten() {
        assert_eq!(tiling_select_mode_env(), 0);
    }

    /// Auswahlkern, Modus 0 (Bestand): bei synthetischen Kandidaten mit
    /// unterschiedlichen Punkten UND unterschiedlichem P(Sieg) gewinnt das
    /// PRODUKT `punkte * P(Sieg)` -- hier bewusst so konstruiert, dass der
    /// Kandidat mit den WENIGEREN Punkten wegen der hoeheren Siegchance das
    /// hoehere Produkt hat (10*0.9=9.0 > 20*0.4=8.0), um Modus 0 von einer
    /// reinen "hoechste Punkte gewinnen"-Regel zu unterscheiden.
    #[test]
    fn select_best_tiling_candidate_mode0_is_points_times_pwin_product() {
        let s = rich_state(1);
        let base_round = s.round_number;
        let expected_first_step = TilingStep::End;
        let mut s2 = s.clone();
        s2.round_number = s2.round_number.wrapping_add(1).min(5); // anderer "Fingerabdruck" fuer den Fake-Evaluator
        let cands = vec![
            TilingOutcome {
                points: 10,
                first_step: expected_first_step.clone(),
                final_state: s,
            },
            TilingOutcome {
                points: 20,
                first_step: TilingStep::Chips { row: 0, chips: vec![] },
                final_state: s2,
            },
        ];
        let evaluator = |gs: &GameState| if gs.round_number == base_round { 0.9 } else { 0.4 };
        let chosen = select_best_tiling_candidate(cands, 0, &evaluator);
        assert_eq!(
            chosen,
            Some(expected_first_step),
            "Modus 0 muss 10*0.9=9.0 gegen 20*0.4=8.0 gewinnen lassen -- reines Punkte-Ranking waere hier falsch"
        );
    }

    /// Auswahlkern, Modus 1 (reines P(Sieg)-Ranking): identische Kandidaten
    /// wie oben, aber diesmal muss der Punktevorsprung des zweiten Kandidaten
    /// IGNORIERT werden -- Modus 1 waehlt ausschliesslich nach `P(Sieg)`,
    /// unabhaengig von `punkte`.
    #[test]
    fn select_best_tiling_candidate_mode1_ignores_points_pure_pwin_ranking() {
        let s = rich_state(1);
        let base_round = s.round_number;
        let expected_first_step = TilingStep::End;
        let mut s2 = s.clone();
        s2.round_number = s2.round_number.wrapping_add(1).min(5);
        let cands = vec![
            TilingOutcome {
                points: 5, // sogar noch weniger Punkte als im Modus-0-Test
                first_step: expected_first_step.clone(),
                final_state: s,
            },
            TilingOutcome {
                points: 100,
                first_step: TilingStep::Chips { row: 0, chips: vec![] },
                final_state: s2,
            },
        ];
        let evaluator = |gs: &GameState| if gs.round_number == base_round { 0.9 } else { 0.4 };
        let chosen = select_best_tiling_candidate(cands, 1, &evaluator);
        assert_eq!(
            chosen,
            Some(expected_first_step),
            "Modus 1 muss ausschliesslich nach P(Sieg) waehlen (0.9 > 0.4), egal wie gross der Punkteunterschied ist"
        );
    }

    /// Beide Modi: bei exaktem Wertegleichstand gewinnt deterministisch der
    /// ERSTE Kandidat in der uebergebenen Reihenfolge (kein Zufall).
    #[test]
    fn select_best_tiling_candidate_tie_picks_first_candidate_both_modes() {
        let s = rich_state(1);
        let expected_first_step = TilingStep::End;
        let evaluator = |_: &GameState| 0.5; // fuer beide Kandidaten identisch -> exakter Gleichstand in BEIDEN Modi
        for mode in [0u8, 1] {
            let cands = vec![
                TilingOutcome {
                    points: 10,
                    first_step: expected_first_step.clone(),
                    final_state: s.clone(),
                },
                TilingOutcome {
                    points: 10,
                    first_step: TilingStep::Chips { row: 0, chips: vec![] },
                    final_state: s.clone(),
                },
            ];
            let chosen = select_best_tiling_candidate(cands, mode, &evaluator);
            assert_eq!(
                chosen,
                Some(expected_first_step.clone()),
                "Modus {mode}: bei Gleichstand muss der erste Kandidat gewinnen"
            );
        }
    }

    // ── Task #100: plattenbewusste Tiling-Zugwahl (MOSAIC_TILING_PLATTEN_W) ──

    /// Baut einen echten Tiling-FORK fuer Musterreihe 0 (Kapazitaet 1, ein
    /// einzelner Rot-Stein): zwei Ziel-Slots in Dome-Reihe 0 bieten je einen
    /// offenen, Rot-annehmenden Space.
    ///
    /// Slot (0,0): si0 ist das EINZIGE Wildcard-Feld auf dem gesamten Brett,
    /// isoliert (si1/si2/si3 unbelegt -> keine Linie beim Legen,
    /// "alleinstehend" = 1 Punkt via `score_placed_tile`). si1 traegt bewusst
    /// Blau statt Rot: sonst waere si1 (unbelegt, `valid_si=[0,1]` fuer
    /// Musterreihe 0) selbst ein DRITTER gueltiger Rot-Zug und der Fork keine
    /// echte Zwei-Wege-Entscheidung mehr. Legen bei si0 komplettiert
    /// Kriterium 3 ("Mehrfarbige Felder"): 2 * wild_total(=1) = 2
    /// Endwertungspunkte.
    /// Slot (0,2): si0 offen (Rot), si1 VORBEFUELLT (Rot) -> horizontale
    /// 2er-Linie = 2 Punkte via `score_placed_tile`. Kein Wildcard-Feld ->
    /// Kriterium 3 bleibt dort unerfuellt (0).
    ///
    /// `scoring_tile_ids = vec![3]` isoliert den Effekt auf genau dieses eine
    /// Kriterium -- keine der beiden Platzierungen beeinflusst versehentlich
    /// ein anderes (nicht aktives) Kriterium.
    ///
    /// `round` wird nur gesetzt, NICHT in der Geometrie selbst genutzt -- die
    /// Rundenabhaengigkeit lebt ausschliesslich im Aufrufer
    /// (`best_first_step_exact_or_valued`s Rundenfenster).
    fn platten_fork_state(round: u32) -> GameState {
        use crate::dome::{DomeSpace, DomeTile};
        let mut s = tiling_state(7);
        s.round_number = round;
        s.scoring_tile_ids = vec![3];
        s.dome_display.clear();

        let slot_a = DomeTile::new(
            100,
            vec![DomeSpace::wild(), DomeSpace::normal(Blau), DomeSpace::normal(Rot), DomeSpace::normal(Rot)],
            0,
        );
        s.players[0].dome_grid.place_dome_tile(slot_a, 0, 0).unwrap();

        let mut slot_b = DomeTile::new(
            101,
            vec![DomeSpace::normal(Rot), DomeSpace::normal(Rot), DomeSpace::normal(Tuerkis), DomeSpace::normal(Tuerkis)],
            0,
        );
        slot_b.spaces[1].placed_color = Some(Rot);
        s.players[0].dome_grid.place_dome_tile(slot_b, 0, 2).unwrap();

        s.players[0].pattern_lines[0].add_tiles(&[Rot]);
        s
    }

    /// Der punktereichere Zug im Fork (2 Punkte, keine Plattenvollendung).
    const PLATTEN_FORK_POINTS_MOVE: TilingAction =
        TilingAction { pattern_row: 0, slot_row: 0, slot_col: 2, space_index: 0 };
    /// Der plattenvollendende Zug im Fork (1 Punkt, +2 Endwertung bei aktivem Gewicht).
    const PLATTEN_FORK_PLATTE_MOVE: TilingAction =
        TilingAction { pattern_row: 0, slot_row: 0, slot_col: 0, space_index: 0 };

    /// Vorab-Beleg der Handrechnung im Doc-Kommentar von `platten_fork_state`:
    /// die beiden Zuege muessen tatsaechlich 1 bzw. 2 Punkte bringen und sich
    /// im Endwertungs-Delta (0 vs. 2) unterscheiden -- sonst waere der Fork
    /// kein echter Fork fuer die folgenden Tests.
    #[test]
    fn platten_fork_state_matches_hand_computed_points_and_end_scoring() {
        let s = platten_fork_state(2);
        let actions = generate_tiling_actions(&s, 0);
        assert_eq!(actions.len(), 2, "erwarte genau 2 Ziel-Slots als Fork: {actions:?}");

        let cands = top_k_tilings(&s, 0, MAX_TILING_LEAVES);
        assert_eq!(cands.len(), 2, "erwarte genau 2 ueberlebende Tiling-Abschluesse");

        let points_cand = cands
            .iter()
            .find(|c| c.first_step == TilingStep::Place(PLATTEN_FORK_POINTS_MOVE))
            .expect("Punkte-Zug muss unter den Kandidaten sein");
        let platte_cand = cands
            .iter()
            .find(|c| c.first_step == TilingStep::Place(PLATTEN_FORK_PLATTE_MOVE))
            .expect("Platten-Zug muss unter den Kandidaten sein");

        assert_eq!(points_cand.points, 2, "Punkte-Zug sollte 2 Punkte bringen (2 horizontal)");
        assert_eq!(platte_cand.points, 1, "Platten-Zug sollte 1 Punkt bringen (alleinstehend)");

        let end_points = crate::scoring::calculate_end_scoring(
            &points_cand.final_state.players[0],
            &points_cand.final_state.scoring_tile_ids,
        )
        .total;
        let end_platte = crate::scoring::calculate_end_scoring(
            &platte_cand.final_state.players[0],
            &platte_cand.final_state.scoring_tile_ids,
        )
        .total;
        assert_eq!(end_points, 0, "Punkte-Zug darf Kriterium 3 nicht vollenden");
        assert_eq!(end_platte, 2, "Platten-Zug muss Kriterium 3 vollenden (2*wild_total=2*1)");
    }

    /// (1) Default-Neutralitaet: ungesetzter Knopf (`MOSAIC_TILING_PLATTEN_W`
    /// nicht gesetzt, kein Test-Override aktiv) -> Default `0.0` ->
    /// `best_first_step_exact_or_valued` muss in Runden 1-4 exakt
    /// `best_first_step_exact` liefern. Praezedenz:
    /// `exact_or_valued_without_evaluator_matches_exact` oben, hier gezielt auf
    /// den neuen Plattenwert-Zweig zugeschnitten (engeres Rundenfenster 1..=4).
    #[test]
    fn platten_weight_default_off_matches_exact_rounds_1_to_4() {
        assert_eq!(
            tiling_platten_weight(),
            0.0,
            "Testumgebung darf MOSAIC_TILING_PLATTEN_W nicht gesetzt haben"
        );
        let mut checked = 0;
        for seed in 1u64..=60 {
            for round in [1u32, 2, 3, 4] {
                let mut s = rich_state(seed);
                s.round_number = round;
                if legal_steps(&s, 0, true).is_empty() {
                    continue;
                }
                checked += 1;
                assert_eq!(
                    best_first_step_exact_or_valued(&s, 0, None),
                    best_first_step_exact(&s, 0),
                    "Seed {seed} Runde {round}: MOSAIC_TILING_PLATTEN_W=0 (Default) weicht ab"
                );
            }
        }
        assert!(checked >= 20, "nur {checked} Stellungen geprueft");
    }

    /// (2) Der Plattenwert ueberstimmt Platzierungspunkte -- Runden 2-4: bei
    /// `w=0` gewinnt der punktereichere Zug (2 > 1), bei hinreichend grossem
    /// `w=5` (Plattenbonus 2*5=10 uebersteigt den 1-Punkt-Vorsprung) gewinnt
    /// der plattenvollendende Zug.
    #[test]
    fn platten_weight_overrides_points_rounds_2_to_4() {
        for round in [2u32, 3, 4] {
            let s = platten_fork_state(round);

            set_platten_weight_override_for_test(Some(0.0));
            let off = best_first_step_exact_or_valued(&s, 0, None);
            set_platten_weight_override_for_test(None);
            assert_eq!(
                off,
                TilingStep::Place(PLATTEN_FORK_POINTS_MOVE),
                "Runde {round}: w=0 sollte die punktereichere Platzierung waehlen"
            );

            set_platten_weight_override_for_test(Some(5.0));
            let on = best_first_step_exact_or_valued(&s, 0, None);
            set_platten_weight_override_for_test(None);
            assert_eq!(
                on,
                TilingStep::Place(PLATTEN_FORK_PLATTE_MOVE),
                "Runde {round}: w=5 sollte die plattenvollendende Platzierung waehlen"
            );
        }
    }

    /// (3) Runde 1 wirkt: derselbe Nachweis wie oben, aber in Runde 1 -- dort
    /// ist der BESTEHENDE Pfad (`best_first_step_exact` -> `best_first_step_inner`)
    /// plattenblind (kein `NET_TILING_TIEBREAK_ENABLED`-Zweig, der ist auf
    /// Runden 2-4 begrenzt). Der neue Zweig muss trotzdem greifen.
    #[test]
    fn platten_weight_overrides_points_in_round_1() {
        let s = platten_fork_state(1);

        set_platten_weight_override_for_test(Some(0.0));
        let off = best_first_step_exact_or_valued(&s, 0, None);
        set_platten_weight_override_for_test(None);
        assert_eq!(
            off,
            TilingStep::Place(PLATTEN_FORK_POINTS_MOVE),
            "Runde 1, w=0: sollte die punktereichere Platzierung waehlen (Bestandsverhalten)"
        );
        // Gegenprobe: w=0 ist tatsaechlich identisch zum bestehenden, plattenblinden Pfad.
        assert_eq!(off, best_first_step_exact(&s, 0));

        set_platten_weight_override_for_test(Some(5.0));
        let on = best_first_step_exact_or_valued(&s, 0, None);
        set_platten_weight_override_for_test(None);
        assert_eq!(
            on,
            TilingStep::Place(PLATTEN_FORK_PLATTE_MOVE),
            "Runde 1, w=5: der neue Zweig muss die plattenvollendende Platzierung erzwingen, \
             obwohl der bestehende Runde-1-Pfad plattenblind ist"
        );
    }

    /// (4) Runde 5 unangetastet: eigener Fork mit GROESSEREM Punktevorsprung
    /// (4 statt 2) fuer den Punkte-Zug, damit der Test tatsaechlich
    /// diskriminiert: `best_first_step_round5` (Task #21) addiert die
    /// Endwertung selbst schon UNGEWICHTET (effektiv `w=1`) und wuerde bei nur
    /// 1-2 Punkten Vorsprung ohnehin denselben (Platten-)Zug waehlen wie ein
    /// (hypothetisch) faelschlich aktiver Task-#100-Zweig mit `w=5` -- ein
    /// Test, der dann "gleich" bliebe, koennte eine kaputte Rundenfenster-
    /// Bremse nicht von einem Zufallstreffer unterscheiden. Mit 4 Punkten
    /// Vorsprung waehlt `best_first_step_round5` (effektives Gewicht 1:
    /// 4+0=4 > 1+2=3) den PUNKTE-Zug; ein faelschlich aktiver Task-#100-Zweig
    /// mit `w=5` wuerde dagegen den PLATTEN-Zug waehlen (1+5*2=11 > 4+0=4) --
    /// beide Ergebnisse sind unterscheidbar, der Test kann also tatsaechlich
    /// eine kaputte Bremse aufdecken statt nur zufaellig gruen zu sein.
    #[test]
    fn platten_weight_round5_unaffected() {
        use crate::dome::{DomeSpace, DomeTile};
        let mut s = tiling_state(7);
        s.round_number = 5;
        s.scoring_tile_ids = vec![3];
        s.dome_display.clear();

        // si1 traegt Blau statt Rot -- sonst waere si1 (unbelegt, `valid_si=[0,1]`)
        // selbst ein dritter gueltiger Rot-Zug, siehe `platten_fork_state`-Doku.
        let slot_a = DomeTile::new(
            100,
            vec![DomeSpace::wild(), DomeSpace::normal(Blau), DomeSpace::normal(Rot), DomeSpace::normal(Rot)],
            0,
        );
        s.players[0].dome_grid.place_dome_tile(slot_a, 0, 0).unwrap();

        // si0 offen (Rot), si1 UND si2 vorbefuellt (Rot) -> horizontale UND
        // vertikale 2er-Linie = 2+2 = 4 Punkte (statt 2 im kleinen Fork oben).
        let mut slot_b = DomeTile::new(
            102,
            vec![DomeSpace::normal(Rot), DomeSpace::normal(Rot), DomeSpace::normal(Rot), DomeSpace::normal(Tuerkis)],
            0,
        );
        slot_b.spaces[1].placed_color = Some(Rot);
        slot_b.spaces[2].placed_color = Some(Rot);
        s.players[0].dome_grid.place_dome_tile(slot_b, 0, 2).unwrap();

        s.players[0].pattern_lines[0].add_tiles(&[Rot]);

        let baseline = best_first_step_exact_or_valued(&s, 0, None); // Default 0.0, kein Override

        set_platten_weight_override_for_test(Some(5.0));
        let with_weight = best_first_step_exact_or_valued(&s, 0, None);
        set_platten_weight_override_for_test(None);

        assert_eq!(
            with_weight, baseline,
            "Runde 5 darf sich durch MOSAIC_TILING_PLATTEN_W nicht aendern"
        );
        // Gegenprobe, dass der Test wirklich etwas beweist: die Baseline muss
        // der PUNKTE-Zug sein (Runde-5-Endwertung mit Gewicht 1 waehlt ihn,
        // siehe Doc oben) -- sonst waere die Konstruktion kein Diskriminator.
        assert_eq!(
            baseline,
            TilingStep::Place(PLATTEN_FORK_POINTS_MOVE),
            "Testkonstruktion: Runde-5-Baseline sollte der Punkte-Zug sein (Diskriminierungspruefung)"
        );
    }

    // ── Task #99 (vormals #33): Transpositions-Memoisierung ──────────────────

    /// Auftrag Schritt 2: Wiederholungsrate MESSEN, bevor ein echter Cache
    /// gebaut wird. Treibt REALE Produktionscodepfade -- Netz-Feature-Build
    /// inkl. der echten `flipped`-Gegner-Pass-Verdopplung aus
    /// `net_mcts.rs::net_leaf_eval` (`let mut flipped = state.clone();
    /// flipped.current_player = 1 - state.current_player;`), die klassische
    /// Heuristik-MCTS-Baumsuche (`mcts::search_action`) und die Runde-5-
    /// Alpha-Beta-Suche (`round5::choose_action_with_analysis`) -- über eine
    /// vielfältige Menge echter Zustände (mehrere Saaten, Runden 2-5, via
    /// `round_transition::drive_to_round_start`) und zählt per
    /// `PLAIN_STATS`/`ENDAWARE_STATS` (Test-Override statt Env-Var, siehe
    /// `set_stats_override_for_test`-Doku), wie oft derselbe Solver-Schlüssel
    /// wiederkehrt. Kein `assert` auf eine Mindest-Trefferquote -- das
    /// Ergebnis ENTSCHEIDET (siehe Bericht), es wird hier nur reproduzierbar
    /// gemessen und geloggt (`cargo test -- --nocapture`).
    #[test]
    fn tiling_cache_hit_rate_measurement() {
        use rand::rngs::StdRng;
        use rand::SeedableRng;

        clear_tiling_caches_for_test();
        set_stats_override_for_test(Some(true));
        set_cache_override_for_test(Some(false)); // reine Zaehlung, keine Wertveraenderung

        // (a) Netz-Feature-Build inkl. der echten `flipped`-Verdopplung.
        for seed in 1u64..=25 {
            for round in [2u32, 3, 4, 5] {
                let state = crate::round_transition::drive_to_round_start(seed, round);
                let _ = crate::features::state_to_features_direct(&state);
                let mut flipped = state.clone();
                flipped.current_player = 1 - state.current_player;
                let _ = crate::features::state_to_features_direct(&flipped);
            }
        }

        // (b) Klassische Heuristik-MCTS-Baumsuche (`mcts::evaluate` an jedem
        // neuen Knoten -> 2x `player_total` -> 2x `solve_round_final_score`).
        let mut rng = StdRng::seed_from_u64(4242);
        for seed in 1u64..=8 {
            let state = crate::round_transition::drive_to_round_start(seed, 2);
            let _ = crate::mcts::search_action(&state, 150, crate::mcts::DEFAULT_C, &mut rng);
        }

        let (plain_total, plain_distinct, plain_max) = plain_stats_summary_for_test();

        // (c) Runde-5-Alpha-Beta (endaware-Variante: Move-Ordering ruft
        // `leaf_value` -- und damit `player_total_exact` -- an JEDEM
        // Kandidaten-Kind auf, zusätzlich zur eigentlichen Negamax-Rekursion).
        for seed in 1u64..=5 {
            let state = crate::round_transition::drive_to_round_start(seed, 5);
            let _ = crate::round5::choose_action_with_analysis(&state);
        }
        let (end_total, end_distinct, end_max) = endaware_stats_summary_for_test();

        set_stats_override_for_test(None);
        set_cache_override_for_test(None);
        clear_tiling_caches_for_test();

        let plain_hit_rate =
            if plain_total > 0 { 100.0 * (1.0 - plain_distinct as f64 / plain_total as f64) } else { 0.0 };
        let end_hit_rate =
            if end_total > 0 { 100.0 * (1.0 - end_distinct as f64 / end_total as f64) } else { 0.0 };
        eprintln!(
            "[tiling_cache_hit_rate] plain: total={plain_total} distinct={plain_distinct} \
             max_repeat={plain_max} hit_rate={plain_hit_rate:.1}%"
        );
        eprintln!(
            "[tiling_cache_hit_rate] endaware: total={end_total} distinct={end_distinct} \
             max_repeat={end_max} hit_rate={end_hit_rate:.1}%"
        );

        // Reiner Sanity-Check gegen einen leer-aussagekraftlosen Messlauf --
        // KEIN Kriterium fuer die Bau-Entscheidung selbst.
        assert!(plain_total >= 100, "zu wenige Aufrufe gemessen: {plain_total}");
        assert!(end_total >= 20, "zu wenige Endaware-Aufrufe gemessen: {end_total}");
    }

    /// `tiling_key` muss auf JEDES ergebnisrelevante Feld reagieren (siehe
    /// Herleitung im Modulkommentar oben) -- sonst würde eine Memoisierung
    /// STILL falsche Ergebnisse liefern. `space_type` wird separat geprüft,
    /// weil es NICHT über `required_color` mitkodiert ist (Wild hat wie
    /// Special `required_color: None`, aber `accepts()` verhält sich für
    /// beide fundamental unterschiedlich, siehe `dome.rs::DomeSpace::accepts`).
    #[test]
    fn tiling_key_distinguishes_all_result_relevant_fields() {
        use crate::dome::BonusChip;
        use crate::dome::{DomeSpace, DomeTile};

        let base = {
            let mut p = PlayerBoard::new(0, "P");
            p.pattern_lines[0].add_tiles(&[Rot]);
            p
        };
        let base_key = tiling_key(&base);

        let variants: Vec<(&str, PlayerBoard)> = vec![
            ("score", {
                let mut p = base.clone();
                p.score += 3;
                p
            }),
            ("tiled_max_row", {
                let mut p = base.clone();
                p.tiled_max_row = 2;
                p
            }),
            ("holds_first_player_marker", {
                let mut p = base.clone();
                p.holds_first_player_marker = true;
                p
            }),
            ("broken_tiles", {
                let mut p = base.clone();
                p.add_broken(&[Blau]);
                p
            }),
            ("pattern_line_tiles", {
                let mut p = base.clone();
                p.pattern_lines[1].add_tiles(&[Blau, Blau]);
                p
            }),
            ("bonus_chip_colors", {
                let mut p = base.clone();
                p.bonus_chips.push(BonusChip { chip_id: 0, colors: vec![Rot] });
                p
            }),
        ];
        for (label, variant) in &variants {
            assert_ne!(tiling_key(variant), base_key, "Feld '{label}' aendert den Schluessel nicht");
        }

        // Dome-Grid-Layout: identische Fuellung/Farben, aber Wild- statt
        // Special-Space an derselben Position.
        let mut with_wild = base.clone();
        with_wild
            .dome_grid
            .place_dome_tile(
                DomeTile::new(
                    1,
                    vec![DomeSpace::wild(), DomeSpace::normal(Rot), DomeSpace::normal(Blau), DomeSpace::normal(Tuerkis)],
                    0,
                ),
                0,
                0,
            )
            .unwrap();
        let mut with_special = base.clone();
        with_special
            .dome_grid
            .place_dome_tile(
                DomeTile::new(
                    1,
                    vec![DomeSpace::special(), DomeSpace::normal(Rot), DomeSpace::normal(Blau), DomeSpace::normal(Tuerkis)],
                    0,
                ),
                0,
                0,
            )
            .unwrap();
        assert_ne!(
            tiling_key(&with_wild),
            tiling_key(&with_special),
            "space_type (Wild vs. Special) aendert den Schluessel nicht, obwohl `accepts()` unterschiedlich ist"
        );

        // Endaware-Schlüssel: gleiches Brett, unterschiedliche `scoring_tile_ids`.
        let key_a = tiling_key_endaware(&base, &[0, 1, 2]);
        let key_b = tiling_key_endaware(&base, &[0, 1, 3]);
        assert_ne!(key_a, key_b, "unterschiedliche scoring_tile_ids aendern den Endaware-Schluessel nicht");
    }

    /// Auftrag Schritt 4a: Bit-Identitäts-Beweis. Über eine große, vielfältige
    /// Menge echter Zustände (synthetische `rich_state`/`tiling_state`-
    /// Fixtures UND reale `drive_to_round_start`-Partien über die Runden 2-5,
    /// mehrere Spieler) muss `solve_round_final_score`/
    /// `solve_round_final_score_endaware` MIT aktivem Cache (kalt UND warm)
    /// exakt denselben `i32` liefern wie OHNE Cache. Mehrere hundert
    /// Aufrufe, wie im Auftrag verlangt.
    #[test]
    fn tiling_cache_bit_identical_over_diverse_states() {
        clear_tiling_caches_for_test();

        let mut states: Vec<GameState> = Vec::new();
        for seed in 1u64..=40 {
            states.push(rich_state(seed));
        }
        for seed in 1u64..=15 {
            states.push(tiling_state(seed));
        }
        for seed in 1u64..=12 {
            for round in [2u32, 3, 4, 5] {
                states.push(crate::round_transition::drive_to_round_start(seed, round));
            }
        }

        let mut checked = 0u32;
        for s in &states {
            for pi in 0..2usize {
                set_cache_override_for_test(Some(false));
                let uncached_plain = compute_plain(s, pi);
                let uncached_end = compute_endaware(s, pi);

                set_cache_override_for_test(Some(true));
                let cold_plain = cached_plain(s, pi); // Miss: befuellt den Cache
                let warm_plain = cached_plain(s, pi); // Hit: muss denselben Wert liefern
                let cold_end = cached_endaware(s, pi);
                let warm_end = cached_endaware(s, pi);

                assert_eq!(cold_plain, uncached_plain, "plain (kalt) weicht ab");
                assert_eq!(warm_plain, uncached_plain, "plain (warm/Cache-Treffer) weicht ab");
                assert_eq!(cold_end, uncached_end, "endaware (kalt) weicht ab");
                assert_eq!(warm_end, uncached_end, "endaware (warm/Cache-Treffer) weicht ab");
                checked += 2; // plain + endaware
            }
        }
        set_cache_override_for_test(None);
        clear_tiling_caches_for_test();

        assert!(checked >= 400, "zu wenige Vergleiche durchgefuehrt: {checked}");
    }

    /// Auftrag Schritt 4b: Kollisions-Schutz. Zwei Zustände, die sich NUR in
    /// einem ergebnisrelevanten Feld unterscheiden (hier: Startspieler-
    /// Marker), dürfen im Cache NICHT denselben Eintrag treffen -- Zustand B
    /// muss nach Zustand A (bereits im Cache) weiterhin seinen EIGENEN,
    /// korrekten Wert liefern.
    #[test]
    fn tiling_cache_does_not_collide_between_near_identical_states() {
        clear_tiling_caches_for_test();
        set_cache_override_for_test(Some(true));

        let mut s_a = tiling_state(11);
        let tile = build_dome_tile_pool()[2].clone();
        s_a.players[0].dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        s_a.players[0].pattern_lines[0].add_tiles(&[Rot]);

        let mut s_b = s_a.clone();
        s_b.players[0].holds_first_player_marker = true; // einziger Unterschied

        let val_a = cached_plain(&s_a, 0); // befuellt den Cache mit Zustand A
        let val_b_direct = compute_plain(&s_b, 0);
        let val_b_cached = cached_plain(&s_b, 0);

        set_cache_override_for_test(None);
        clear_tiling_caches_for_test();

        assert_ne!(
            val_a, val_b_direct,
            "Testkonstruktion diskriminiert nicht (Marker-Strafe muesste den Wert aendern)"
        );
        assert_eq!(
            val_b_cached, val_b_direct,
            "Cache-Kollision: Zustand B erhielt faelschlich Zustand As gecachten Wert"
        );
    }
}
