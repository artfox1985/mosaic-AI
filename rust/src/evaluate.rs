//! Heuristische Punkteabschätzung — Single Source of Truth.
//!
//! Schätzt die erwartbaren Tiling-Punkte voller Musterreihen (inkl. Nachbar-Boni)
//! sowie die voraussichtliche Rundenpunktzahl. Bewusst engine-nah und PyO3-frei,
//! damit **sowohl** der Serializer (`serialize.rs`, Frontend-Anzeige) **als auch**
//! der spätere Rust-MCTS dieselbe Geometrie-Logik nutzen — kein zweiter Abklatsch.
//!
//! Port von engine/serializer.py `_estimate_row_values` / `_estimate_round_score`.

use crate::board::PlayerBoard;

/// Strafleisten-Progression (−1/−2/−3/−4), identisch zu board::BROKEN_PENALTIES.
const FLOOR_PENALTIES: [i32; 4] = [-1, -2, -3, -4];

/// Schätzt pro voller Musterreihe die erwartbaren Tiling-Punkte (inkl. Nachbarn).
/// Gibt `(row_index, punkte)` nur für komplette Reihen mit Farbe zurück.
pub fn estimate_row_values(p: &PlayerBoard) -> Vec<(usize, i32)> {
    let mut grid = [[false; 6]; 6];
    let mut valid_empty: [Vec<usize>; 6] = Default::default();

    for sr in 0..3 {
        for sc in 0..3 {
            if let Some(slot) = &p.dome_grid.dome_slots[sr][sc] {
                let (abs_r, abs_c) = (sr * 2, sc * 2);
                for (si, sp) in slot.spaces.iter().enumerate() {
                    let r = abs_r + si / 2;
                    let c = abs_c + si % 2;
                    if sp.placed_color.is_some() || sp.placed_special {
                        grid[r][c] = true;
                    } else if !sp.is_locked {
                        valid_empty[r].push(c);
                    }
                }
            }
        }
    }

    let mut out = Vec::new();
    for (ri, row) in p.pattern_lines.iter().enumerate() {
        let color = match (row.is_complete(), row.color) {
            (true, Some(c)) => c,
            _ => continue,
        };
        // Nur Spaces zählen, die die Reihenfarbe akzeptieren (Wild = jede Farbe).
        // Ohne passenden, platzierbaren Space ist die Reihe NICHT legbar → 0 Punkte
        // (Reihe gar nicht aufnehmen), statt fälschlich Baseline 1.
        let mut best = 0;
        let mut placeable = false;
        for &c in &valid_empty[ri] {
            let accepts = p.dome_grid.get_space(ri, c).map_or(false, |sp| sp.accepts(color));
            if !accepts {
                continue;
            }
            placeable = true;
            let mut h = 1;
            let mut v = 1;
            let mut i = c as i32 - 1;
            while i >= 0 && grid[ri][i as usize] {
                h += 1;
                i -= 1;
            }
            for i in (c + 1)..6 {
                if grid[ri][i] { h += 1; } else { break; }
            }
            let mut i = ri as i32 - 1;
            while i >= 0 && grid[i as usize][c] {
                v += 1;
                i -= 1;
            }
            for i in (ri + 1)..6 {
                if grid[i][c] { v += 1; } else { break; }
            }
            let mut pts = 0;
            if h > 1 { pts += h; }
            if v > 1 { pts += v; }
            if pts == 0 { pts = 1; } // alleinstehend = 1
            if pts > best { best = pts; }
        }
        if placeable {
            out.push((ri, best));
        }
    }
    out
}

/// Voraussichtliche Rundenpunktzahl: Summe der Reihen-Schätzwerte abzüglich
/// Boden-/Startspieler-Strafen. `include_rows=false` liefert nur die Strafen.
pub fn estimate_round_score(p: &PlayerBoard, include_rows: bool) -> i32 {
    let mut est: i32 = if include_rows {
        estimate_row_values(p).iter().map(|(_, v)| v).sum()
    } else {
        0
    };
    for (i, _) in p.broken_tiles.iter().enumerate() {
        if i < FLOOR_PENALTIES.len() {
            est += FLOOR_PENALTIES[i];
        }
    }
    if p.holds_first_player_marker {
        est -= 2;
    }
    est
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dome::build_dome_tile_pool;
    use crate::tile::TileColor::*;

    #[test]
    fn solo_full_row_estimated_at_one() {
        let mut p = PlayerBoard::new(0, "P");
        // Volle Reihe 0 (cap 1), leeres Raster mit freiem passenden Space.
        let tile = build_dome_tile_pool()[2].clone(); // si1 = Rot
        p.dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        p.pattern_lines[0].add_tiles(&[Rot]);
        let rv = estimate_row_values(&p);
        assert_eq!(rv, vec![(0, 1)]);
    }

    #[test]
    fn full_row_without_matching_space_scores_zero() {
        // Volle blaue Reihe 0, aber der einzige Slot bietet keinen blauen/Wild-
        // Space → Reihe nicht platzierbar → 0 erwartete Punkte (nicht 1).
        let mut p = PlayerBoard::new(0, "P");
        let tile = build_dome_tile_pool()[2].clone(); // [Tuerkis, Rot, Blau, Wild]
        // 6x6 Reihe 0 = obere Spaces si0=Tuerkis, si1=Rot → kein Blau/Wild.
        p.dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        p.pattern_lines[0].add_tiles(&[Blau]);
        assert!(estimate_row_values(&p).is_empty());
        assert_eq!(estimate_round_score(&p, true), 0);
    }

    #[test]
    fn full_row_with_wild_space_is_placeable() {
        // Wild-Space akzeptiert jede Farbe → blaue Reihe wird platzierbar (≥1).
        let mut p = PlayerBoard::new(0, "P");
        let tile = build_dome_tile_pool()[2].clone(); // si3 = Wild bei 6x6 (1,1)
        p.dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        // Reihe 1 (cap 2) → 6x6 Reihe 1 (untere Spaces si2=Blau, si3=Wild).
        p.pattern_lines[1].add_tiles(&[Gelb, Gelb]); // Gelb passt nur auf Wild
        let rv = estimate_row_values(&p);
        assert_eq!(rv, vec![(1, 1)]);
    }

    #[test]
    fn floor_penalty_only_without_rows() {
        let mut p = PlayerBoard::new(0, "P");
        p.add_broken(&[Rot, Rot]); // −1 −2 = −3
        p.holds_first_player_marker = true;
        assert_eq!(estimate_round_score(&p, false), -3 - 2);
    }
}
