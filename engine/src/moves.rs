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

/// Neue Kuppelplatte aus dem offenen Display auf das 3×3-Raster legen.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PlaceDomeTileMove {
    pub dome_tile_id: usize,
    pub slot_row: usize,
    pub slot_col: usize,
    pub rotation: u32, // 0/90/180/270
}

/// Aktion A (Stapel-Variante), Schritt 2 ("aufhören und wählen"): eine der
/// bisher gezogenen Platten (`state.pending_stack_draw`) wählen und
/// platzieren, der Rest wandert zurück unter den Stapel. Setzt mindestens
/// einen vorherigen `Action::DrawStackPeek` diese Runde voraus -- `num_drawn`
/// gibt es nicht mehr als Feld, es ergibt sich implizit aus der Anzahl der
/// Peeks (siehe Action::DrawStackPeek).
///
/// `return_order`: Regelwerk -- "die ggf. übrigen [legst du] in beliebiger
/// Reihenfolge zurück unter den Stapel" (Nutzer-Zitat). Muss exakt die
/// tile_ids der NICHT gewählten gezogenen Platten enthalten (Multiset-Check
/// wie bei `moon_order`), in der gewünschten Reihenfolge: zuerst = wird
/// zuerst zurückgelegt = liegt NÄHER an der Ziehseite (wird eher wieder
/// gezogen), zuletzt = liegt am tiefsten. Bei ≤1 übriger Platte gibt es
/// keine echte Wahl, das Feld muss trotzdem die (triviale) Reihenfolge
/// tragen.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DrawFromStackMove {
    pub chosen_id: usize,
    pub slot_row: usize,
    pub slot_col: usize,
    pub rotation: u32,
    pub return_order: Vec<usize>,
}

/// Aktion D: ein aufgedecktes Bonusplättchen von einer Fabrik nehmen.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TakeBonusChipMove {
    pub factory_id: usize,
}

/// Vereinheitlichter Drafting-Zug (ersetzt das Python-isinstance-Dispatch).
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Action {
    Stone(Move),
    Dome(PlaceDomeTileMove),
    /// Aktion A (Stapel-Variante), Schritt 1: eine weitere verdeckte Platte
    /// ziehen (−1 Pkt), Rückseite zeigt nur den Typ (Wild/Special), nicht
    /// Farben/Anordnung. Beendet den Zug NICHT -- danach muss der Spieler
    /// erneut entscheiden (weiterziehen oder `DrawStack` zum Aufhören).
    DrawStackPeek,
    DrawStack(DrawFromStackMove),
    BonusChip(TakeBonusChipMove),
    Pass,
}
