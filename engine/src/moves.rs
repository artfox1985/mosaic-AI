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

/// Baustein B (zweistufiger Kuppel-Suchknoten, externe Bugfix-Review):
/// speichert die Stufe-1-Wahl (Kachel+Slot), bis die Stufe-2-Wahl (Rotation)
/// eintrifft. `execute_dome_move`/`execute_draw_from_stack` (game.rs) bleiben
/// unveraendert -- nur WANN die volle Move-Struktur zusammengesetzt wird
/// (ueber zwei Spielerentscheidungen statt einer, ohne `switch_player()`
/// zwischen Stufe 1 und 2), aendert sich.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PendingDomeChoice {
    FromDisplay {
        dome_tile_id: usize,
        slot_row: usize,
        slot_col: usize,
    },
    FromDrawStack {
        chosen_id: usize,
        slot_row: usize,
        slot_col: usize,
        return_order: Vec<usize>,
    },
}

/// Vereinheitlichter Drafting-Zug (ersetzt das Python-isinstance-Dispatch).
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Action {
    Stone(Move),
    /// Baustein B Stufe 1: Kachel aus dem offenen Display + Slot waehlen.
    /// `rotation` im enthaltenen Move ist Platzhalter (immer 0, siehe
    /// `PendingDomeChoice`) -- die tatsaechliche Rotation folgt als
    /// eigenstaendige Stufe-2-Entscheidung (`ChooseDomeRotation`).
    ChooseDomeSlot(PlaceDomeTileMove),
    /// Aktion A (Stapel-Variante), Schritt 1: eine weitere verdeckte Platte
    /// ziehen (−1 Pkt), Rückseite zeigt nur den Typ (Wild/Special), nicht
    /// Farben/Anordnung. Beendet den Zug NICHT -- danach muss der Spieler
    /// erneut entscheiden (weiterziehen oder `ChooseDrawStackSlot` zum
    /// Aufhören).
    DrawStackPeek,
    /// Baustein B Stufe 1 (Stapel-Variante): gezogene Kachel + Slot waehlen.
    /// `rotation` Platzhalter (immer 0), analog `ChooseDomeSlot`.
    ChooseDrawStackSlot(DrawFromStackMove),
    /// Baustein B Stufe 2: Rotation fuer die in `GameState::pending_dome_choice`
    /// gespeicherte Stufe-1-Wahl -- EINE gemeinsame Aktion fuer beide Pfade
    /// (Display/Stapel), `pending_dome_choice` sagt welcher gemeint ist.
    ChooseDomeRotation(u32),
    BonusChip(TakeBonusChipMove),
    Pass,
}
