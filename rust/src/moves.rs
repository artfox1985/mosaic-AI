//! Zugtypen für die Drafting-Phase — Port von engine/moves.py (Stein-Züge).
//!
//! Dome-/Chip-/Stapel-Züge (PlaceDomeTileMove, DrawFromStackMove, TakeBonusChipMove)
//! folgen in einem späteren Schritt zusammen mit ihrer Ausführung.

use crate::tile::TileColor;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TakeSource {
    SmallFactorySun,
    /// factory_id == None signalisiert Aktion C (globaler Mond-Zug).
    SmallFactoryMoon,
    LargeFactorySun,
    LargeFactoryMoon,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TakeAction {
    pub source: TakeSource,
    pub color: TileColor,
    pub factory_id: Option<usize>, // 1–4; None = große Fabrik bzw. Aktion C
    pub moon_order: Vec<TileColor>, // nur bei SmallFactorySun relevant
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PlaceAction {
    /// 0–5 für Musterreihe, -1 für direkt auf Strafleiste.
    pub row_index: i32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Move {
    pub take: TakeAction,
    pub place: PlaceAction,
}

impl Move {
    pub fn is_global_moon_take(&self) -> bool {
        self.take.source == TakeSource::SmallFactoryMoon && self.take.factory_id.is_none()
    }
}
