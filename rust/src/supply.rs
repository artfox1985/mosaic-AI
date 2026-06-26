//! Beutel, Ablageturm, Special-Vorrat — Port von engine/supply.py.
//!
//! RNG ist injizierbar (statt globalem random wie in Python), damit Self-Play
//! reproduzierbar ist und Parität-Tests deterministische Startzustände bauen können.

use rand::seq::SliceRandom;
use rand::Rng;

use crate::tile::{TileColor, TILES_PER_COLOR};

#[derive(Debug, Clone, Default)]
pub struct Bag {
    pub tiles: Vec<TileColor>,
}

impl Bag {
    /// Voller, gemischter Beutel mit allen 65 Normalsteinen.
    pub fn full<R: Rng + ?Sized>(rng: &mut R) -> Self {
        let mut tiles = Vec::with_capacity(TILES_PER_COLOR * 5);
        for color in TileColor::NORMAL {
            for _ in 0..TILES_PER_COLOR {
                tiles.push(color);
            }
        }
        tiles.shuffle(rng);
        Bag { tiles }
    }

    pub fn count(&self) -> usize {
        self.tiles.len()
    }
    pub fn is_empty(&self) -> bool {
        self.tiles.is_empty()
    }

    /// Zieht bis zu n Steine (kann weniger sein, wenn der Beutel zu leer ist).
    pub fn draw(&mut self, n: usize) -> Vec<TileColor> {
        let k = n.min(self.tiles.len());
        self.tiles.drain(..k).collect()
    }

    /// Füllt den Beutel aus dem Turm auf und mischt. Gibt die Anzahl zurück.
    pub fn refill_from_tower<R: Rng + ?Sized>(&mut self, tower: &mut Tower, rng: &mut R) -> usize {
        let tiles = tower.empty();
        if tiles.is_empty() {
            return 0;
        }
        let n = tiles.len();
        self.tiles.extend(tiles);
        self.tiles.shuffle(rng);
        n
    }
}

#[derive(Debug, Clone, Default)]
pub struct Tower {
    pub tiles: Vec<TileColor>,
}

impl Tower {
    pub fn count(&self) -> usize {
        self.tiles.len()
    }
    pub fn is_empty(&self) -> bool {
        self.tiles.is_empty()
    }
    pub fn add(&mut self, tiles: &[TileColor]) {
        self.tiles.extend_from_slice(tiles);
    }
    /// Entnimmt alle Steine (für Beutel-Auffüllung).
    pub fn empty(&mut self) -> Vec<TileColor> {
        std::mem::take(&mut self.tiles)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    #[test]
    fn full_bag_has_65_and_draws() {
        let mut rng = StdRng::seed_from_u64(1);
        let mut bag = Bag::full(&mut rng);
        assert_eq!(bag.count(), 65);
        let drawn = bag.draw(4);
        assert_eq!(drawn.len(), 4);
        assert_eq!(bag.count(), 61);
    }

    #[test]
    fn refill_pulls_from_tower() {
        let mut rng = StdRng::seed_from_u64(2);
        let mut bag = Bag::default();
        let mut tower = Tower::default();
        tower.add(&[TileColor::Rot, TileColor::Blau, TileColor::Gelb]);
        assert_eq!(bag.refill_from_tower(&mut tower, &mut rng), 3);
        assert_eq!(bag.count(), 3);
        assert!(tower.is_empty());
    }

}
