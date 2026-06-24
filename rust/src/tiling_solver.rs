//! Exakter Brute-Force-Solver (DFS) für die Tiling-Phase.
//!
//! Tiling ist ein Solo-Puzzle pro Spieler mit sehr geringer Tiefe (≤6 Reihen)
//! und — laut Regel: **während des Tilings werden KEINE Kuppelplatten gelegt** —
//! sehr wenig Verzweigung. Daher kein MCTS, sondern eine rekursive Maximierung:
//! finde die Platzierungs-/Chip-Folge, die den Runden-Score des Spielers
//! maximiert. Genutzt (a) als Pseudo-Terminal-Bewertung am Drafting→Tiling-
//! Übergang im MCTS und (b) für den echten Tiling-Zug der KI.
//!
//! Zugmenge: nur Steine auf BEREITS gelegte Kuppel-Spaces (Filter
//! `dome_tile_id.is_none()` auf `generate_tiling_actions`) + Bonus-Chip-
//! Komplettierung passender Reihen. Reihenfolge oben→unten (Regelwerk S.7)
//! steckt bereits in `validate_tiling_action`/`generate_tiling_actions`.

use crate::board::FIRST_PLAYER_MARKER_PENALTY;
use crate::round_end::{
    apply_bonus_chips_to_row, can_complete_row_with_chips, execute_full_tiling,
    generate_tiling_actions, row_has_open_matching_slot, TilingAction,
};
use crate::state::GameState;

/// Defensive Rekursionsgrenze (Branching ist klein; nur als Sicherung).
const MAX_DEPTH: u32 = 30;

/// Ein Tiling-Schritt im Solver.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TilingStep {
    Place(TilingAction),
    Chips { row: usize },
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
fn legal_steps(state: &GameState, pi: usize) -> Vec<TilingStep> {
    let mut steps: Vec<TilingStep> = generate_tiling_actions(state, pi)
        .into_iter()
        .filter(|ta| ta.dome_tile_id.is_none())
        .map(TilingStep::Place)
        .collect();
    for row in chippable_rows(state, pi) {
        steps.push(TilingStep::Chips { row });
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
        TilingStep::Chips { row } => {
            let mut s = state.clone();
            if !apply_bonus_chips_to_row(&mut s.players[pi], *row) {
                return None;
            }
            Some((s, 0))
        }
        TilingStep::End => None,
    }
}

fn solve_rec(state: &GameState, pi: usize, depth: u32) -> i32 {
    if depth >= MAX_DEPTH {
        return 0;
    }
    let steps = legal_steps(state, pi);
    if steps.is_empty() {
        return 0;
    }
    // Baseline 0 = „hier aufhören". Platzierungen liefern stets ≥1, Chips 0
    // (schalten aber Platzierungen frei) — der maximierende Pfad gewinnt.
    let mut best = 0;
    for step in &steps {
        if let Some((next, pts)) = apply_step(state, pi, step) {
            let total = pts + solve_rec(&next, pi, depth + 1);
            if total > best {
                best = total;
            }
        }
    }
    best
}

/// Maximal erreichbare Tiling-Punkte (Linien + Spezial-Boni) für Spieler `pi`,
/// ausgehend vom aktuellen Brett (Drafting-Ende).
pub fn solve_max_tiling_points(state: &GameState, pi: usize) -> i32 {
    solve_rec(state, pi, 0)
}

/// Optimaler finaler Runden-Score für Spieler `pi`: aktueller Score +
/// max. Tiling-Punkte + (fixe) Boden-/Marker-Strafen.
pub fn solve_round_final_score(state: &GameState, pi: usize) -> i32 {
    let p = &state.players[pi];
    let penalty = p.broken_penalty()
        + if p.holds_first_player_marker { FIRST_PLAYER_MARKER_PENALTY } else { 0 };
    p.score + penalty + solve_max_tiling_points(state, pi)
}

/// Optimaler nächster Tiling-Schritt für Spieler `pi` (für den echten KI-Zug).
/// `End`, wenn nichts mehr platzierbar/komplettierbar ist.
pub fn best_first_step(state: &GameState, pi: usize) -> TilingStep {
    let steps = legal_steps(state, pi);
    if steps.is_empty() {
        return TilingStep::End;
    }
    let mut best_step = TilingStep::End;
    let mut best_val = i32::MIN;
    for step in steps {
        if let Some((next, pts)) = apply_step(state, pi, &step) {
            let val = pts + solve_max_tiling_points(&next, pi);
            if val > best_val {
                best_val = val;
                best_step = step;
            }
        }
    }
    best_step
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::board::PlayerBoard;
    use crate::dome::build_dome_tile_pool;
    use crate::state::{setup_new_game, Phase};
    use crate::tile::TileColor::*;
    use rand::rngs::StdRng;
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
                TilingStep::Chips { row } => {
                    apply_bonus_chips_to_row(&mut s.players[pi], row);
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
        assert!(matches!(first, TilingStep::Chips { row: 2 } | TilingStep::Place(_)));
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
}
