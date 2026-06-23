//! Rundenende — Port von engine/round_end.py.
//!
//! Schritt 4 (Teilport): nur die für den Drafting→Tiling-Übergang nötigen Teile
//! (unplatzierbare Reihen, volle Reihen). Tiling-Ausführung + Scoring folgen.

use crate::board::PlayerBoard;
use crate::supply::Tower;

/// Indizes aller vollen Musterreihen (müssen noch gelegt werden).
pub fn get_pending_tiling_rows(player: &PlayerBoard) -> Vec<usize> {
    player
        .pattern_lines
        .iter()
        .enumerate()
        .filter(|(_, r)| r.is_complete())
        .map(|(i, _)| i)
        .collect()
}

/// Unplatzierbare Reihen am Rundenende: Reihe mit Steinen, deren Dome-Reihe
/// komplett belegt ist und keinen passenden freien Space hat → Strafleiste.
pub fn find_unplaceable_rows(player: &PlayerBoard) -> Vec<usize> {
    let mut unplaceable = Vec::new();
    for (row_idx, row) in player.pattern_lines.iter().enumerate() {
        let color = match row.color {
            Some(c) if !row.tiles.is_empty() => c,
            _ => continue,
        };
        let dome_row = row_idx / 2;
        let space_row = row_idx % 2;
        let valid_si = [space_row * 2, space_row * 2 + 1];
        let slots = &player.dome_grid.dome_slots[dome_row];
        // Noch freie Slots in der Dome-Reihe → Reihe bleibt liegen.
        if slots.iter().any(|s| s.is_none()) {
            continue;
        }
        let has_match = slots.iter().any(|slot| {
            slot.as_ref().map_or(false, |d| {
                valid_si.iter().any(|&si| {
                    let sp = &d.spaces[si];
                    !sp.is_filled() && !sp.is_locked && sp.accepts(color)
                })
            })
        });
        if !has_match {
            unplaceable.push(row_idx);
        }
    }
    unplaceable
}

/// Verschiebt unplatzierbare Fliesen auf die Strafleiste (Überlauf → Turm).
/// Gibt die Anzahl verschobener Fliesen zurück.
pub fn process_unplaceable_rows(player: &mut PlayerBoard, tower: &mut Tower) -> usize {
    let mut total = 0;
    for row_idx in find_unplaceable_rows(player) {
        let tiles: Vec<_> = std::mem::take(&mut player.pattern_lines[row_idx].tiles);
        player.pattern_lines[row_idx].color = None;
        let n = tiles.len();
        let to_tower = player.add_broken(&tiles);
        tower.add(&to_tower);
        total += n;
    }
    total
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dome::build_dome_tile_pool;
    use crate::tile::TileColor::*;

    #[test]
    fn full_row_detected_as_pending() {
        let mut p = PlayerBoard::new(0, "P");
        p.pattern_lines[0].add_tiles(&[Rot]); // cap 1 → voll
        p.pattern_lines[2].add_tiles(&[Blau, Blau]); // cap 3 → nicht voll
        assert_eq!(get_pending_tiling_rows(&p), vec![0]);
    }

    #[test]
    fn unplaceable_when_domerow_full_no_match() {
        let mut p = PlayerBoard::new(0, "P");
        // Reihe 0 (dome_row 0) mit Rot füllen.
        p.pattern_lines[0].add_tiles(&[Rot]);
        // Dome-Reihe 0 komplett mit Platten belegen, die in den oberen Spaces (si 0,1)
        // KEIN Rot akzeptieren. Platte 1 = [w(), Blau, Tuerkis, Schwarz] hat oben
        // WILD(0) → akzeptiert Rot. Nimm stattdessen Platten ohne Rot/Wild oben.
        let pool = build_dome_tile_pool();
        // Platte 12 (idx) = [Tuerkis, Schwarz, Rot, Wild]; oben si0=Tuerkis, si1=Schwarz → kein Rot
        for sc in 0..3 {
            let mut t = pool[11].clone(); // [Tuerkis, Schwarz, Rot, Wild]
            t.tile_id = 100 + sc;
            p.dome_grid.place_dome_tile(t, 0, sc).unwrap();
        }
        // si0/si1 sind Tuerkis/Schwarz → akzeptiert Rot nicht → unplatzierbar
        assert_eq!(find_unplaceable_rows(&p), vec![0]);

        let mut tower = Tower::default();
        let moved = process_unplaceable_rows(&mut p, &mut tower);
        assert_eq!(moved, 1);
        assert_eq!(p.broken_tiles.len(), 1);
        assert!(p.pattern_lines[0].tiles.is_empty());
    }
}
