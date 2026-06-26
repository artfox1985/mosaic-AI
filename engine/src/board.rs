//! Spielerbrett: Musterreihen, 6×6-Dome-Raster, Strafleiste — Port von engine/board.py.

use crate::dome::{DomeSpace, DomeTile};
use crate::tile::TileColor;

// ── Musterreihe ──────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PatternLine {
    pub row_index: usize,
    pub tiles: Vec<TileColor>,
    pub color: Option<TileColor>,
}

impl PatternLine {
    pub fn new(row_index: usize) -> Self {
        PatternLine {
            row_index,
            tiles: Vec::new(),
            color: None,
        }
    }

    pub fn capacity(&self) -> usize {
        self.row_index + 1
    }
    pub fn is_complete(&self) -> bool {
        self.tiles.len() == self.capacity()
    }
    pub fn is_empty(&self) -> bool {
        self.tiles.is_empty()
    }
    pub fn spaces_left(&self) -> usize {
        self.capacity() - self.tiles.len()
    }

    pub fn can_accept(&self, color: TileColor) -> bool {
        if self.is_complete() {
            return false;
        }
        match self.color {
            Some(c) if c != color => false,
            _ => true,
        }
    }

    /// Fügt so viele Steine wie möglich hinzu; gibt den Überlauf zurück.
    /// Alle Steine müssen dieselbe Farbe haben (Aufrufer-Verantwortung).
    pub fn add_tiles(&mut self, tiles: &[TileColor]) -> Vec<TileColor> {
        if tiles.is_empty() {
            return Vec::new();
        }
        debug_assert!(tiles.iter().all(|&t| t == tiles[0]));
        if self.color.is_none() {
            self.color = Some(tiles[0]);
        }
        let n = self.spaces_left().min(tiles.len());
        self.tiles.extend_from_slice(&tiles[..n]);
        tiles[n..].to_vec()
    }

    /// Rundenende: leert die volle Reihe, gibt die platzierte Farbe zurück.
    pub fn clear(&mut self) -> TileColor {
        debug_assert!(self.is_complete(), "Cannot clear an incomplete pattern line");
        let color = self.color.expect("complete line has a color");
        self.tiles.clear();
        self.color = None;
        color
    }
}

// ── Dome-Raster ──────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DomeGrid {
    /// 3×3, None = noch nicht gelegt.
    pub dome_slots: Vec<Vec<Option<DomeTile>>>,
}

impl Default for DomeGrid {
    fn default() -> Self {
        DomeGrid {
            dome_slots: (0..3).map(|_| vec![None, None, None]).collect(),
        }
    }
}

impl DomeGrid {
    /// 6×6-Zelle → (slot_row, slot_col, space_index). Space-Layout: 0 1 / 2 3.
    pub fn cell_to_dome_space(row6: usize, col6: usize) -> (usize, usize, usize) {
        (row6 / 2, col6 / 2, (row6 % 2) * 2 + (col6 % 2))
    }

    pub fn place_dome_tile(
        &mut self,
        tile: DomeTile,
        slot_row: usize,
        slot_col: usize,
    ) -> Result<(), String> {
        if slot_row >= 3 || slot_col >= 3 {
            return Err(format!("Invalid slot ({slot_row}, {slot_col})"));
        }
        if self.dome_slots[slot_row][slot_col].is_some() {
            return Err(format!("Slot ({slot_row}, {slot_col}) is already occupied"));
        }
        self.dome_slots[slot_row][slot_col] = Some(tile);
        Ok(())
    }

    pub fn occupied_slots(&self) -> Vec<(usize, usize)> {
        let mut v = Vec::new();
        for r in 0..3 {
            for c in 0..3 {
                if self.dome_slots[r][c].is_some() {
                    v.push((r, c));
                }
            }
        }
        v
    }

    pub fn empty_slots(&self) -> Vec<(usize, usize)> {
        let mut v = Vec::new();
        for r in 0..3 {
            for c in 0..3 {
                if self.dome_slots[r][c].is_none() {
                    v.push((r, c));
                }
            }
        }
        v
    }

    pub fn get_space(&self, row6: usize, col6: usize) -> Option<&DomeSpace> {
        let (sr, sc, si) = Self::cell_to_dome_space(row6, col6);
        self.dome_slots[sr][sc].as_ref().map(|d| &d.spaces[si])
    }

    pub fn get_space_mut(&mut self, row6: usize, col6: usize) -> Option<&mut DomeSpace> {
        let (sr, sc, si) = Self::cell_to_dome_space(row6, col6);
        self.dome_slots[sr][sc]
            .as_mut()
            .map(|d| &mut d.spaces[si])
    }

    /// Legt einen normalen Stein auf eine 6×6-Zelle; schaltet ggf. Special frei.
    pub fn place_tile(&mut self, row6: usize, col6: usize, color: TileColor) -> Result<(), String> {
        let (sr, sc, si) = Self::cell_to_dome_space(row6, col6);
        let dome = self.dome_slots[sr][sc]
            .as_mut()
            .ok_or_else(|| format!("No dome tile at ({row6}, {col6})"))?;
        if !dome.spaces[si].accepts(color) {
            return Err(format!(
                "Space at ({row6}, {col6}) does not accept color {}",
                color.value()
            ));
        }
        dome.spaces[si].placed_color = Some(color);
        dome.try_unlock_special();
        Ok(())
    }

    /// Legt einen weißen Stein auf einen offenen SPECIAL-Space; gibt bonus_points zurück.
    pub fn place_special_tile(&mut self, row6: usize, col6: usize) -> Result<i32, String> {
        let (sr, sc, si) = Self::cell_to_dome_space(row6, col6);
        let dome = self.dome_slots[sr][sc]
            .as_mut()
            .ok_or_else(|| format!("No dome tile at ({row6}, {col6})"))?;
        if !dome.spaces[si].accepts_special() {
            return Err(format!("Space at ({row6}, {col6}) is not an open SPECIAL space."));
        }
        dome.spaces[si].place_special_tile()?;
        Ok(dome.bonus_points)
    }

    pub fn valid_placements_for(&self, color: TileColor) -> Vec<(usize, usize)> {
        let mut v = Vec::new();
        for r in 0..6 {
            for c in 0..6 {
                if self.get_space(r, c).map_or(false, |s| s.accepts(color)) {
                    v.push((r, c));
                }
            }
        }
        v
    }

    pub fn valid_special_placements(&self) -> Vec<(usize, usize)> {
        let mut v = Vec::new();
        for r in 0..6 {
            for c in 0..6 {
                if self.get_space(r, c).map_or(false, |s| s.accepts_special()) {
                    v.push((r, c));
                }
            }
        }
        v
    }

    pub fn is_row_complete(&self, row6: usize) -> bool {
        (0..6).all(|c| self.get_space(row6, c).map_or(false, |s| s.is_filled()))
    }

    pub fn is_col_complete(&self, col6: usize) -> bool {
        (0..6).all(|r| self.get_space(r, col6).map_or(false, |s| s.is_filled()))
    }

    pub fn completed_rows(&self) -> Vec<usize> {
        (0..6).filter(|&r| self.is_row_complete(r)).collect()
    }

    pub fn completed_cols(&self) -> Vec<usize> {
        (0..6).filter(|&c| self.is_col_complete(c)).collect()
    }
}

// ── Spielerbrett ─────────────────────────────────────────────────────────────

pub const MAX_BROKEN: usize = 4;
pub const BROKEN_PENALTIES: [i32; 4] = [-1, -2, -3, -4];
pub const DOME_TILES_PER_ROUND: u32 = 2;
pub const MAX_DOME_SLOTS: usize = 9;
pub const TOKENS_PER_ROUND: u32 = 2;
pub const BONUS_CHIPS_PER_ROUND: u32 = 2;
pub const FIRST_PLAYER_MARKER_PENALTY: i32 = -2;

#[derive(Debug, Clone)]
pub struct PlayerBoard {
    pub player_id: usize,
    pub name: String,
    pub score: i32,
    pub pattern_lines: Vec<PatternLine>,
    pub dome_grid: DomeGrid,
    pub broken_tiles: Vec<TileColor>,
    pub bonus_chips: Vec<crate::dome::BonusChip>,
    pub dome_tiles_placed_this_round: u32,
    pub tiled_max_row: i32,
    pub player_tokens_used: u32,
    pub holds_first_player_marker: bool,
    /// In der Vorbereitung (Phase start_placement) zu legen; zählt nicht als Runden-Zug.
    pub start_dome_tile: Option<DomeTile>,
    /// True, wenn die Startkachel noch aus der Mitte gezogen werden muss
    /// (ersetzt den Python-String-Platzhalter "Muss_noch_gezogen_werden").
    pub start_tile_pending: bool,
    pub bonus_chips_used_this_round: u32,
    pub total_floor_penalties: i32,
    pub floor_penalties_per_round: Vec<i32>,
}

impl PlayerBoard {
    pub fn new(player_id: usize, name: impl Into<String>) -> Self {
        PlayerBoard {
            player_id,
            name: name.into(),
            score: 5,
            pattern_lines: (0..6).map(PatternLine::new).collect(),
            dome_grid: DomeGrid::default(),
            broken_tiles: Vec::new(),
            bonus_chips: Vec::new(),
            dome_tiles_placed_this_round: 0,
            tiled_max_row: -1,
            player_tokens_used: 0,
            holds_first_player_marker: false,
            start_dome_tile: None,
            start_tile_pending: false,
            bonus_chips_used_this_round: 0,
            total_floor_penalties: 0,
            floor_penalties_per_round: Vec::new(),
        }
    }

    /// Legt Steine auf die Strafleiste (max 4); gibt überzählige zurück (→ Turm).
    pub fn add_broken(&mut self, tiles: &[TileColor]) -> Vec<TileColor> {
        let space_left = MAX_BROKEN.saturating_sub(self.broken_tiles.len());
        let n = space_left.min(tiles.len());
        self.broken_tiles.extend_from_slice(&tiles[..n]);
        tiles[n..].to_vec()
    }

    pub fn broken_penalty(&self) -> i32 {
        self.broken_tiles
            .iter()
            .enumerate()
            .map(|(i, _)| BROKEN_PENALTIES[i.min(MAX_BROKEN - 1)])
            .take(MAX_BROKEN)
            .sum()
    }

    pub fn clear_broken(&mut self) -> Vec<TileColor> {
        std::mem::take(&mut self.broken_tiles)
    }

    /// Punkte addieren, nie unter 0.
    pub fn apply_score(&mut self, delta: i32) {
        self.score = (self.score + delta).max(0);
    }

    pub fn has_used_all_tokens(&self, round_number: u32) -> bool {
        if round_number >= 5 {
            return true;
        }
        self.player_tokens_used >= TOKENS_PER_ROUND
    }

    pub fn can_place_dome_tile(&self, round_number: u32) -> bool {
        if round_number >= 5 {
            return false;
        }
        if self.dome_tiles_placed_this_round >= DOME_TILES_PER_ROUND {
            return false;
        }
        self.dome_grid.occupied_slots().len() < MAX_DOME_SLOTS
    }

    pub fn can_take_bonus_chip(&self) -> bool {
        self.bonus_chips_used_this_round < BONUS_CHIPS_PER_ROUND
    }

    pub fn register_dome_placement(&mut self) -> Result<(), String> {
        if self.dome_tiles_placed_this_round >= DOME_TILES_PER_ROUND {
            return Err(format!("{} hat bereits 2 Kacheln diese Runde gelegt.", self.name));
        }
        self.dome_tiles_placed_this_round += 1;
        Ok(())
    }

    pub fn use_player_token(&mut self, round_number: u32) -> Result<(), String> {
        if round_number >= 5 {
            return Err("In Runde 5 werden keine Spielerplättchen genutzt.".into());
        }
        if self.player_tokens_used >= TOKENS_PER_ROUND {
            return Err(format!("{} hat bereits beide Spielerplättchen genutzt.", self.name));
        }
        self.player_tokens_used += 1;
        Ok(())
    }

    pub fn take_bonus_chip(&mut self, chip: crate::dome::BonusChip) -> Result<(), String> {
        if !self.can_take_bonus_chip() {
            return Err(format!(
                "{} hat bereits 2 Bonusplättchen diese Runde genommen.",
                self.name
            ));
        }
        self.bonus_chips.push(chip);
        self.bonus_chips_used_this_round += 1;
        Ok(())
    }

    pub fn has_unplaced_start_tile(&self) -> bool {
        self.start_tile_pending
    }

    pub fn reset_dome_placements(&mut self) {
        self.dome_tiles_placed_this_round = 0;
        self.player_tokens_used = 0;
        self.bonus_chips_used_this_round = 0;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::tile::TileColor::*;

    #[test]
    fn pattern_line_add_and_overflow() {
        let mut pl = PatternLine::new(2); // capacity 3
        let overflow = pl.add_tiles(&[Rot, Rot]);
        assert!(overflow.is_empty());
        assert_eq!(pl.color, Some(Rot));
        assert!(!pl.is_complete());
        let overflow = pl.add_tiles(&[Rot, Rot]); // 1 passt, 1 läuft über
        assert_eq!(overflow, vec![Rot]);
        assert!(pl.is_complete());
        assert_eq!(pl.spaces_left(), 0);
        assert_eq!(pl.clear(), Rot);
        assert!(pl.is_empty());
    }

    #[test]
    fn cell_mapping_matches_layout() {
        assert_eq!(DomeGrid::cell_to_dome_space(0, 0), (0, 0, 0));
        assert_eq!(DomeGrid::cell_to_dome_space(0, 1), (0, 0, 1));
        assert_eq!(DomeGrid::cell_to_dome_space(1, 0), (0, 0, 2));
        assert_eq!(DomeGrid::cell_to_dome_space(1, 1), (0, 0, 3));
        assert_eq!(DomeGrid::cell_to_dome_space(5, 5), (2, 2, 3));
        assert_eq!(DomeGrid::cell_to_dome_space(2, 4), (1, 2, 0));
    }

    #[test]
    fn place_tile_and_unlock_special() {
        // Platte 0 = [Gelb, Schwarz, Tuerkis, Special] in Slot (0,0).
        let mut grid = DomeGrid::default();
        let tile = crate::dome::build_dome_tile_pool()[0].clone();
        grid.place_dome_tile(tile, 0, 0).unwrap();
        // Special ist Space-Index 3 → 6×6-Zelle (1,1). Fülle die 3 Normalen.
        grid.place_tile(0, 0, Gelb).unwrap(); // si 0
        grid.place_tile(0, 1, Schwarz).unwrap(); // si 1
        grid.place_tile(1, 0, Tuerkis).unwrap(); // si 2 → entsperrt Special
        assert!(grid.get_space(1, 1).unwrap().accepts_special());
        // falsche Farbe wird abgelehnt
        assert!(grid.place_tile(0, 0, Rot).is_err()); // schon gefüllt
    }

    #[test]
    fn broken_penalty_escalates_and_caps() {
        let mut p = PlayerBoard::new(0, "P1");
        let overflow = p.add_broken(&[Rot, Rot, Rot, Rot, Rot, Rot]); // nur 4 passen
        assert_eq!(overflow.len(), 2);
        assert_eq!(p.broken_penalty(), -1 - 2 - 3 - 4);
        p.apply_score(-100);
        assert_eq!(p.score, 0); // clamp
    }
}
