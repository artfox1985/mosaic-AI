//! Kuppelplättchen (2×2) und Bonusplättchen — Port von engine/dome.py.

use crate::tile::TileColor;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SpaceType {
    Normal,
    Wild,
    Special,
}

/// Einer der 4 Spaces auf einer Kuppelplättchen.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DomeSpace {
    pub space_type: SpaceType,
    pub required_color: Option<TileColor>,
    pub placed_color: Option<TileColor>,
    pub placed_special: bool,
    pub is_locked: bool,
}

impl DomeSpace {
    pub fn normal(color: TileColor) -> Self {
        DomeSpace {
            space_type: SpaceType::Normal,
            required_color: Some(color),
            placed_color: None,
            placed_special: false,
            is_locked: false,
        }
    }

    pub fn wild() -> Self {
        DomeSpace {
            space_type: SpaceType::Wild,
            required_color: None,
            placed_color: None,
            placed_special: false,
            is_locked: false,
        }
    }

    /// Special-Space (weiß), startet gesperrt.
    pub fn special() -> Self {
        DomeSpace {
            space_type: SpaceType::Special,
            required_color: None,
            placed_color: None,
            placed_special: false,
            is_locked: true,
        }
    }

    pub fn is_filled(&self) -> bool {
        match self.space_type {
            SpaceType::Special => self.placed_special,
            _ => self.placed_color.is_some(),
        }
    }

    /// Kann dieser Space einen normalen Stein dieser Farbe aufnehmen?
    pub fn accepts(&self, color: TileColor) -> bool {
        if self.is_filled() || self.is_locked {
            return false;
        }
        match self.space_type {
            SpaceType::Normal => Some(color) == self.required_color,
            SpaceType::Wild => true,
            SpaceType::Special => false,
        }
    }

    /// Kann dieser Space einen weißen Stein aufnehmen?
    pub fn accepts_special(&self) -> bool {
        self.space_type == SpaceType::Special && !self.is_locked && !self.placed_special
    }

    pub fn place_special_tile(&mut self) -> Result<(), String> {
        if !self.accepts_special() {
            return Err("Dieser Space kann keinen weißen Stein aufnehmen.".into());
        }
        self.placed_special = true;
        Ok(())
    }
}

/// Rotation → neue Reihenfolge der Space-Indizes.
/// Layout vor Rotation: [0][1] / [2][3].
pub fn rotation_indices(degrees: u32) -> Option<[usize; 4]> {
    match degrees {
        0 => Some([0, 1, 2, 3]),
        90 => Some([2, 0, 3, 1]),
        180 => Some([3, 2, 1, 0]),
        270 => Some([1, 3, 0, 2]),
        _ => None,
    }
}

/// Eine 2×2 Kuppelplättchen. spaces-Index-Layout: [0][1] / [2][3].
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DomeTile {
    pub tile_id: usize,
    pub spaces: Vec<DomeSpace>, // genau 4
    pub bonus_points: i32,
}

impl DomeTile {
    pub fn new(tile_id: usize, spaces: Vec<DomeSpace>, bonus_points: i32) -> Self {
        assert_eq!(spaces.len(), 4, "Eine Kuppelplättchen hat genau 4 Spaces");
        DomeTile {
            tile_id,
            spaces,
            bonus_points,
        }
    }

    pub fn is_complete(&self) -> bool {
        self.spaces.iter().all(|s| s.is_filled())
    }

    /// Index des SPECIAL-Space, falls vorhanden.
    pub fn special_space_idx(&self) -> Option<usize> {
        self.spaces
            .iter()
            .position(|s| s.space_type == SpaceType::Special)
    }

    /// Schaltet den SPECIAL-Space frei, sobald die anderen 3 gefüllt sind.
    /// Gibt true zurück, wenn gerade freigeschaltet wurde.
    pub fn try_unlock_special(&mut self) -> bool {
        let sp_idx = match self.special_space_idx() {
            Some(i) => i,
            None => return false,
        };
        if !self.spaces[sp_idx].is_locked {
            return false;
        }
        let other_filled = self
            .spaces
            .iter()
            .enumerate()
            .all(|(i, s)| i == sp_idx || s.is_filled());
        if other_filled {
            self.spaces[sp_idx].is_locked = false;
            return true;
        }
        false
    }

    /// Spaces in gedrehter Reihenfolge (ändert die Platte nicht).
    pub fn rotated_spaces(&self, degrees: u32) -> Result<Vec<DomeSpace>, String> {
        let idx = rotation_indices(degrees)
            .ok_or_else(|| format!("Ungültige Rotation: {degrees}. Erlaubt: 0, 90, 180, 270."))?;
        Ok(idx.iter().map(|&i| self.spaces[i].clone()).collect())
    }

    /// Dreht die Platte dauerhaft (nur vor dem Platzieren erlaubt).
    pub fn apply_rotation(&mut self, degrees: u32) -> Result<(), String> {
        if rotation_indices(degrees).is_none() {
            return Err(format!(
                "Ungültige Rotation: {degrees}. Erlaubt: 0, 90, 180, 270."
            ));
        }
        if degrees == 0 {
            return Ok(());
        }
        if self.spaces.iter().any(|s| s.is_filled()) {
            return Err("Eine bereits befüllte Kuppel kann nicht rotiert werden.".into());
        }
        self.spaces = self.rotated_spaces(degrees)?;
        Ok(())
    }

    /// Indizes der Spaces, die diese Farbe aufnehmen können.
    pub fn open_spaces_for(&self, color: TileColor) -> Vec<usize> {
        self.spaces
            .iter()
            .enumerate()
            .filter(|(_, s)| s.accepts(color))
            .map(|(i, _)| i)
            .collect()
    }
}

/// Vollständiger Pool von 18 Kuppelplättchen (engine/dome.py, dome_colors.csv).
pub fn build_dome_tile_pool() -> Vec<DomeTile> {
    use TileColor::*;
    let n = DomeSpace::normal;
    let w = DomeSpace::wild;
    let s = DomeSpace::special;

    // (spaces, bonus_points); Reihenfolge: oben-links, oben-rechts, unten-links, unten-rechts
    let defs: Vec<(Vec<DomeSpace>, i32)> = vec![
        (vec![n(Gelb), n(Schwarz), n(Tuerkis), s()], 3),
        (vec![w(), n(Blau), n(Tuerkis), n(Schwarz)], 0),
        (vec![n(Tuerkis), n(Rot), n(Blau), w()], 0),
        (vec![n(Schwarz), n(Gelb), n(Rot), w()], 0),
        (vec![n(Schwarz), s(), n(Tuerkis), n(Rot)], 3),
        (vec![n(Tuerkis), n(Gelb), w(), n(Schwarz)], 0),
        (vec![s(), n(Schwarz), n(Rot), n(Blau)], 3),
        (vec![n(Gelb), n(Blau), n(Schwarz), s()], 3),
        (vec![n(Tuerkis), n(Rot), n(Blau), s()], 3),
        (vec![n(Gelb), n(Rot), w(), n(Blau)], 0),
        (vec![n(Gelb), s(), n(Schwarz), n(Rot)], 3),
        (vec![n(Tuerkis), n(Schwarz), n(Rot), w()], 0),
        (vec![n(Blau), n(Schwarz), s(), n(Tuerkis)], 3),
        (vec![n(Rot), n(Tuerkis), n(Gelb), w()], 0),
        (vec![n(Tuerkis), n(Blau), w(), n(Gelb)], 0),
        (vec![s(), n(Tuerkis), n(Gelb), n(Blau)], 3),
        (vec![n(Rot), w(), n(Blau), n(Schwarz)], 0),
        (vec![s(), n(Gelb), n(Blau), n(Rot)], 3),
    ];

    defs.into_iter()
        .enumerate()
        .map(|(i, (spaces, bp))| DomeTile::new(i, spaces, bp))
        .collect()
}

/// Bonusplättchen (1–2 Farben).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BonusChip {
    pub chip_id: usize,
    pub colors: Vec<TileColor>,
}

/// Alle 20 Bonusplättchen (engine/dome.py, bonus_chips_colors.csv).
pub fn build_bonus_chip_pool() -> Vec<BonusChip> {
    use TileColor::*;
    let defs: Vec<Vec<TileColor>> = vec![
        vec![Blau],
        vec![Tuerkis],
        vec![Tuerkis, Gelb],
        vec![Blau, Rot],
        vec![Rot],
        vec![Rot, Tuerkis],
        vec![Schwarz, Blau],
        vec![Gelb, Schwarz],
        vec![Blau],
        vec![Rot],
        vec![Blau, Rot],
        vec![Schwarz],
        vec![Schwarz, Gelb],
        vec![Schwarz],
        vec![Rot, Tuerkis],
        vec![Blau, Schwarz],
        vec![Gelb],
        vec![Tuerkis, Gelb],
        vec![Tuerkis],
        vec![Gelb],
    ];
    defs.into_iter()
        .enumerate()
        .map(|(i, colors)| BonusChip { chip_id: i, colors })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::tile::TileColor::*;

    #[test]
    fn pools_have_expected_sizes() {
        let pool = build_dome_tile_pool();
        assert_eq!(pool.len(), 18);
        assert!(pool.iter().all(|t| t.spaces.len() == 4));
        // tile_ids 0..18 fortlaufend
        for (i, t) in pool.iter().enumerate() {
            assert_eq!(t.tile_id, i);
        }
        assert_eq!(build_bonus_chip_pool().len(), 20);
    }

    #[test]
    fn space_accepts_logic() {
        let normal = DomeSpace::normal(Rot);
        assert!(normal.accepts(Rot));
        assert!(!normal.accepts(Blau));
        assert!(DomeSpace::wild().accepts(Schwarz));
        // Special akzeptiert keinen normalen Stein, locked
        let sp = DomeSpace::special();
        assert!(!sp.accepts(Rot));
        assert!(!sp.accepts_special()); // weil is_locked
    }

    #[test]
    fn rotation_preserves_set_and_layout() {
        // 180° zweimal == original
        let mut t = DomeTile::new(
            0,
            vec![
                DomeSpace::normal(Blau),
                DomeSpace::normal(Gelb),
                DomeSpace::normal(Rot),
                DomeSpace::normal(Schwarz),
            ],
            0,
        );
        let orig = t.spaces.clone();
        t.apply_rotation(180).unwrap();
        assert_eq!(t.spaces[0].required_color, Some(Schwarz));
        t.apply_rotation(180).unwrap();
        assert_eq!(t.spaces, orig);
    }

    #[test]
    fn special_unlocks_when_others_filled() {
        // Platte mit 1 Special + 3 Normal; fülle die 3 Normal → Special unlockt.
        let mut t = build_dome_tile_pool()[0].clone(); // [Gelb, Schwarz, Tuerkis, Special]
        let sp_idx = t.special_space_idx().unwrap();
        for i in 0..4 {
            if i != sp_idx {
                let col = t.spaces[i].required_color.unwrap();
                t.spaces[i].placed_color = Some(col);
            }
        }
        assert!(t.try_unlock_special());
        assert!(t.spaces[sp_idx].accepts_special());
        // zweiter Aufruf liefert false (schon entsperrt)
        assert!(!t.try_unlock_special());
    }
}
