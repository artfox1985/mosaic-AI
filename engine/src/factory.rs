//! Kleine Fabriken + große Fabrik (Tischmitte) — Port von engine/factory.py.

use crate::dome::BonusChip;
use crate::tile::TileColor;

/// Eine kleine Fabrik.
#[derive(Debug, Clone)]
pub struct Factory {
    pub factory_id: usize,
    pub sun_tiles: Vec<TileColor>,
    pub moon_stacks: Vec<Vec<TileColor>>,
    pub bonus_chip: Option<BonusChip>,
    pub bonus_chip_revealed: bool,
}

impl Factory {
    pub fn new(factory_id: usize) -> Self {
        Factory {
            factory_id,
            sun_tiles: Vec::new(),
            moon_stacks: Vec::new(),
            bonus_chip: None,
            bonus_chip_revealed: false,
        }
    }

    pub fn sun_is_empty(&self) -> bool {
        self.sun_tiles.is_empty()
    }

    pub fn sun_colors(&self) -> Vec<TileColor> {
        let mut v: Vec<TileColor> = Vec::new();
        for &t in &self.sun_tiles {
            if !v.contains(&t) {
                v.push(t);
            }
        }
        v
    }

    /// Nimmt alle Steine der Farbe von der Sun-Seite. Gibt (genommene, übrige) zurück.
    pub fn take_from_sun(
        &mut self,
        color: TileColor,
    ) -> Result<(Vec<TileColor>, Vec<TileColor>), String> {
        if !self.sun_tiles.contains(&color) {
            return Err(format!(
                "Farbe {} nicht auf Sun-Seite von Fabrik {}.",
                color.value(),
                self.factory_id
            ));
        }
        let taken: Vec<TileColor> = self.sun_tiles.iter().copied().filter(|&t| t == color).collect();
        let remaining: Vec<TileColor> =
            self.sun_tiles.iter().copied().filter(|&t| t != color).collect();
        self.sun_tiles.clear();
        Ok((taken, remaining))
    }

    /// Legt die übrigen Fliesen als EINEN Stapel auf die Moon-Seite
    /// (Index 0 = unten, letzter = oben/sichtbar).
    pub fn place_on_moon(&mut self, ordered_tiles: Vec<TileColor>) {
        if !ordered_tiles.is_empty() {
            self.moon_stacks.push(ordered_tiles);
        }
    }

    pub fn moon_is_empty(&self) -> bool {
        self.moon_stacks.is_empty()
    }

    /// Top-Farben der Moon-Stapel.
    pub fn moon_top_colors(&self) -> Vec<TileColor> {
        let mut v: Vec<TileColor> = Vec::new();
        for stack in &self.moon_stacks {
            if let Some(&top) = stack.last() {
                if !v.contains(&top) {
                    v.push(top);
                }
            }
        }
        v
    }

    /// Nimmt alle TOP-Steine der Farbe von den Moon-Stapeln.
    pub fn take_from_moon(&mut self, color: TileColor) -> Result<Vec<TileColor>, String> {
        if !self.moon_top_colors().contains(&color) {
            return Err(format!(
                "Farbe {} nicht oben auf Moon-Stapeln von Fabrik {}.",
                color.value(),
                self.factory_id
            ));
        }
        let mut taken = Vec::new();
        let mut surviving: Vec<Vec<TileColor>> = Vec::new();
        for mut stack in std::mem::take(&mut self.moon_stacks) {
            if stack.last() == Some(&color) {
                taken.push(stack.pop().unwrap());
                if !stack.is_empty() {
                    surviving.push(stack);
                }
            } else {
                surviving.push(stack);
            }
        }
        self.moon_stacks = surviving;
        Ok(taken)
    }

    pub fn is_fully_empty(&self) -> bool {
        self.sun_is_empty() && self.moon_is_empty()
    }
}

/// Die große Fabrik (Tischmitte). Trägt den Startspieler-Marker.
#[derive(Debug, Clone)]
pub struct LargeFactory {
    pub sun_tiles: Vec<TileColor>,
    pub moon_pool: Vec<TileColor>,
    pub has_first_player_marker: bool,
    /// Regelbuch S.10: konnten Beutel+Turm keine 2 verschiedenen Farben mehr
    /// liefern, wird die monochrome Befüllung akzeptiert -- dann (und NUR
    /// dann) vergibt bereits die Sonnen-Nahme die Startspielerfliese, weil
    /// der Mondbereich sonst leer bliebe und der Marker unnehmbar wäre.
    pub monochrome_fallback: bool,
}

impl Default for LargeFactory {
    fn default() -> Self {
        LargeFactory {
            sun_tiles: Vec::new(),
            moon_pool: Vec::new(),
            has_first_player_marker: true,
            monochrome_fallback: false,
        }
    }
}

impl LargeFactory {
    pub fn sun_is_empty(&self) -> bool {
        self.sun_tiles.is_empty()
    }

    pub fn sun_colors(&self) -> Vec<TileColor> {
        let mut v: Vec<TileColor> = Vec::new();
        for &t in &self.sun_tiles {
            if !v.contains(&t) {
                v.push(t);
            }
        }
        v
    }

    /// Nimmt alle Steine einer Farbe von der Sun-Seite.
    /// Gibt (genommene, übrige, hatte_marker) zurück; übrige → Moon-Pool (Aufrufer).
    pub fn take_from_sun(
        &mut self,
        color: TileColor,
    ) -> Result<(Vec<TileColor>, Vec<TileColor>, bool), String> {
        if !self.sun_tiles.contains(&color) {
            return Err(format!(
                "Farbe {} nicht auf Sun-Seite der großen Fabrik.",
                color.value()
            ));
        }
        let taken: Vec<TileColor> = self.sun_tiles.iter().copied().filter(|&t| t == color).collect();
        let remaining: Vec<TileColor> =
            self.sun_tiles.iter().copied().filter(|&t| t != color).collect();
        self.sun_tiles.clear();
        // Regelbuch S.5: NUR die erste Nahme vom MONDbereich vergibt die
        // Startspielerfliese -- die Sonnen-Nahme lässt den Marker liegen.
        // Einzige Ausnahme (Regelbuch S.10): monochrome Notbefüllung, dann
        // bleibt der Mond leer und der Marker geht mit den 5 gleichfarbigen.
        let marker = self.monochrome_fallback && self.has_first_player_marker;
        if marker {
            self.has_first_player_marker = false;
        }
        Ok((taken, remaining, marker))
    }

    pub fn moon_is_empty(&self) -> bool {
        self.moon_pool.is_empty()
    }

    pub fn moon_colors(&self) -> Vec<TileColor> {
        let mut v: Vec<TileColor> = Vec::new();
        for &t in &self.moon_pool {
            if !v.contains(&t) {
                v.push(t);
            }
        }
        v
    }

    /// Nimmt alle Steine einer Farbe aus dem Moon-Pool. Gibt (genommene, hatte_marker).
    pub fn take_from_moon(&mut self, color: TileColor) -> Result<(Vec<TileColor>, bool), String> {
        if !self.moon_pool.contains(&color) {
            return Err(format!(
                "Farbe {} nicht im Moon-Pool der großen Fabrik.",
                color.value()
            ));
        }
        let taken: Vec<TileColor> = self.moon_pool.iter().copied().filter(|&t| t == color).collect();
        self.moon_pool.retain(|&t| t != color);
        let marker = self.has_first_player_marker;
        self.has_first_player_marker = false;
        Ok((taken, marker))
    }

    pub fn add_to_moon(&mut self, tiles: &[TileColor]) {
        self.moon_pool.extend_from_slice(tiles);
    }

    pub fn is_empty(&self) -> bool {
        self.sun_is_empty() && self.moon_is_empty() && !self.has_first_player_marker
    }

    pub fn reset_for_new_round(&mut self) {
        self.sun_tiles.clear();
        self.moon_pool.clear();
        self.has_first_player_marker = true;
        self.monochrome_fallback = false;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::tile::TileColor::*;

    #[test]
    fn sun_take_splits_and_remainder() {
        let mut f = Factory::new(1);
        f.sun_tiles = vec![Rot, Rot, Blau, Gelb];
        let (taken, rest) = f.take_from_sun(Rot).unwrap();
        assert_eq!(taken, vec![Rot, Rot]);
        assert_eq!(rest, vec![Blau, Gelb]);
        assert!(f.sun_is_empty());
        f.place_on_moon(rest);
        assert_eq!(f.moon_top_colors(), vec![Gelb]); // letzter = oben
    }

    #[test]
    fn moon_take_top_only() {
        let mut f = Factory::new(1);
        f.moon_stacks = vec![vec![Blau, Rot], vec![Gelb, Rot], vec![Schwarz]];
        let taken = f.take_from_moon(Rot).unwrap();
        assert_eq!(taken.len(), 2); // beide Top-Rot
        // Reste: [Blau], [Gelb], [Schwarz]
        assert_eq!(f.moon_stacks.len(), 3);
        assert!(f.take_from_moon(Rot).is_err()); // kein Rot mehr oben
    }

    #[test]
    fn large_factory_marker_taken_once() {
        // R2 (Vollaudit 2026-07-21): der Marker geht mit der ERSTEN
        // Mond-Nahme, nicht mit der Sonnen-Nahme.
        let mut lf = LargeFactory::default();
        lf.moon_pool = vec![Rot, Blau, Blau];
        let (taken, marker) = lf.take_from_moon(Blau).unwrap();
        assert_eq!(taken.len(), 2);
        assert!(marker);
        assert!(!lf.has_first_player_marker);
        // Zweite Mond-Nahme: Marker ist weg.
        let (taken2, marker2) = lf.take_from_moon(Rot).unwrap();
        assert_eq!(taken2.len(), 1);
        assert!(!marker2);
    }

    #[test]
    fn large_factory_sun_take_leaves_marker() {
        // R2: die Sonnen-Nahme lässt den Marker liegen -- erst die
        // anschließende erste Mond-Nahme holt ihn.
        let mut lf = LargeFactory::default();
        lf.sun_tiles = vec![Rot, Blau, Blau];
        let (taken, rest, marker) = lf.take_from_sun(Blau).unwrap();
        assert_eq!(taken.len(), 2);
        assert_eq!(rest, vec![Rot]);
        assert!(!marker, "Sonnen-Nahme darf den Marker nicht vergeben");
        assert!(lf.has_first_player_marker);
        lf.add_to_moon(&rest);
        let (_, moon_marker) = lf.take_from_moon(Rot).unwrap();
        assert!(moon_marker, "erste Mond-Nahme holt den Marker");
        assert!(!lf.has_first_player_marker);
        assert!(lf.is_empty());
    }

    #[test]
    fn large_factory_monochrome_fallback_gives_marker_on_sun_take() {
        // R3: bei monochromer Notbefüllung (Regelbuch S.10) vergibt
        // ausnahmsweise die Sonnen-Nahme den Marker.
        let mut lf = LargeFactory::default();
        lf.sun_tiles = vec![Rot, Rot, Rot, Rot, Rot];
        lf.monochrome_fallback = true;
        let (taken, rest, marker) = lf.take_from_sun(Rot).unwrap();
        assert_eq!(taken.len(), 5);
        assert!(rest.is_empty());
        assert!(marker, "monochromer Fallback: Sonnen-Nahme vergibt den Marker");
        assert!(!lf.has_first_player_marker);
        assert!(lf.is_empty());
    }
}
