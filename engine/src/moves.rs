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

/// Weg A (`PREREG_moon_stack_order.md` par.12.2/par.12.6): anhaengige Wahl
/// der Mondstapel-Reihenfolge nach einem Sonnenzug aus einer KLEINEN Fabrik.
/// Gebaut nach dem Vorbild von [`PendingDomeChoice`] -- der Stein-Zug ist
/// ausgefuehrt, die Reststeine liegen aber noch "in der Hand" des Spielers
/// (NICHT auf dem Mondstapel), bis er ihre Reihenfolge festgelegt hat. Kein
/// `switch_player()` bis zum letzten Teilzug.
///
/// REIHENFOLGE-KONVENTION, am Code belegt: `Factory::place_on_moon`
/// (factory.rs:62-67) legt den Vektor so ab, dass Index 0 UNTEN und der
/// letzte Eintrag OBEN liegt; nur der oberste Stein ist nehmbar
/// (`Factory::moon_top_colors`, factory.rs:74-84). `ChooseMoonTop` waehlt
/// deshalb von OBEN nach unten, und [`PendingMoonOrder::top_down`] sammelt
/// die Wahlen in genau dieser Richtung.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PendingMoonOrder {
    /// `factory_id` (1..4) der kleinen Fabrik, auf deren Mondseite die Steine
    /// gehen. Kein Index -- `find_factory_idx` (execution.rs) loest ihn auf.
    pub factory_id: usize,
    /// Noch NICHT zugeordnete Reststeine (Multimenge). Leer, sobald alles
    /// entschieden ist; bei nur noch EINER Farbe darin ist der Rest bestimmt.
    pub remaining: Vec<TileColor>,
    /// Bereits gewaehlte Steine, OBERSTER ZUERST.
    pub top_down: Vec<TileColor>,
}

impl PendingMoonOrder {
    /// Die endgueltige Reihenfolge fuer `place_on_moon` (Index 0 = unten):
    /// erst der bestimmte Rest (alles dieselbe Farbe), dann die gewaehlten
    /// Steine von unten nach oben.
    pub fn resolved_bottom_up(&self) -> Vec<TileColor> {
        let mut out = self.remaining.clone();
        out.extend(self.top_down.iter().rev().copied());
        out
    }
}

/// R3 (`PREREG_dome_return_order.md` par.12.1/par.12.7): anhaengige Wahl
/// "welche Restplatte kommt zuerst wieder", eingehaengt ZWISCHEN
/// `ChooseDrawStackSlot` und `ChooseDomeRotation`. Der Rest bleibt in
/// Ziehreihenfolge -- entschieden wird allein `return_order[0]`, also die
/// Platte, die von den zurueckgelegten als ERSTE wieder ans Tageslicht kommt
/// (Herleitung im Kommentarblock vor `self_play.rs::RETURN_ORDER_MAX_PERMUTED`).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PendingReturnOrder {
    pub chosen_id: usize,
    pub slot_row: usize,
    pub slot_col: usize,
    /// Nicht gewaehlte gezogene Platten in ZIEHREIHENFOLGE (`tile_id`s).
    pub rest_in_draw_order: Vec<usize>,
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
    /// Weg A Teilzug (`PREREG_moon_stack_order.md` par.12.2 Punkt 2): "diese
    /// Farbe liegt als naechste OBEN" auf dem Mondstapel der Fabrik aus
    /// [`GameState::pending_moon_order`](crate::state::GameState). Bei drei
    /// verschiedenen Farben zwei Entscheide hintereinander (oben, dann Mitte;
    /// der Rest ist bestimmt), bei zwei verschiedenen einer. Dieselbe
    /// ID-Familie fuer alle Stufen, wie die vier Rotations-IDs fuer beide
    /// Kuppelpfade.
    ChooseMoonTop(TileColor),
    /// R3 Teilzug (`PREREG_dome_return_order.md` par.12.1): Position (in der
    /// ZIEHREIHENFOLGE der nicht gewaehlten Platten) derjenigen Platte, die
    /// als erste wieder gezogen wird. Gedeckelt auf
    /// `self_play::RETURN_ORDER_MAX_PERMUTED` Kandidaten.
    ChooseReturnFirst(usize),
    BonusChip(TakeBonusChipMove),
    Pass,
}
