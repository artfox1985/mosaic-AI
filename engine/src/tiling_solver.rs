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
    apply_bonus_chips_with, can_complete_row_with_chips, chip_allocations, execute_full_tiling,
    generate_tiling_actions, greedy_chip_alloc, row_has_open_matching_slot, TilingAction,
};
use crate::state::GameState;

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
        .filter(|ta| ta.dome_tile_id.is_none())
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

/// Optimaler finaler Runden-Score für Spieler `pi`: aktueller Score +
/// max. Tiling-Punkte + (fixe) Boden-/Marker-Strafen.
pub fn solve_round_final_score(state: &GameState, pi: usize) -> i32 {
    let p = &state.players[pi];
    let penalty = p.broken_penalty()
        + if p.holds_first_player_marker { FIRST_PLAYER_MARKER_PENALTY } else { 0 };
    p.score + penalty + solve_max_tiling_points(state, pi)
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
    let mut best_val = i32::MIN;
    for step in steps {
        if budget == 0 {
            break; // Budget erschöpft: bisher besten Schritt liefern statt hängen.
        }
        if let Some((next, pts)) = apply_step(state, pi, &step) {
            let val = pts + solve_rec(&next, pi, 1, exact, &mut budget);
            if val > best_val {
                best_val = val;
                best_step = step;
            }
        }
    }
    best_step
}

/// Greedy-Variante (Hot-Path / Tests).
pub fn best_first_step(state: &GameState, pi: usize) -> TilingStep {
    best_first_step_inner(state, pi, false)
}

/// Exakte Variante für den tatsächlich gespielten KI-Tiling-Zug: durchsucht die
/// Chip-Allokationen, damit mehrfarbige Plättchen im Engpass optimal verteilt
/// werden. Wird nur einmal pro Zug aufgerufen → bezahlbar.
pub fn best_first_step_exact(state: &GameState, pi: usize) -> TilingStep {
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
