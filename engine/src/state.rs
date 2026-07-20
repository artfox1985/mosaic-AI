//! Spielzustand + Setup — Port von engine/setup.py.

use rand::seq::SliceRandom;
use rand::Rng;

use crate::board::PlayerBoard;
use crate::dome::{build_bonus_chip_pool, build_dome_tile_pool, BonusChip, DomeTile};
use crate::factory::{Factory, LargeFactory};
use crate::moves::PendingDomeChoice;
use crate::supply::{Bag, Tower};
use crate::tile::TileColor;

// Spielkonstanten
pub const NUM_PLAYERS: usize = 2;
pub const NUM_ROUNDS: u32 = 5;
pub const NUM_SMALL_FACTORIES: usize = 4;
pub const TILES_PER_SMALL_FACTORY: usize = 4;
pub const TILES_PER_LARGE_FACTORY: usize = 5;
pub const DOME_TILES_EACH: usize = 9;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Phase {
    StartPlacement,
    Drafting,
    Tiling,
    Scoring,
    End,
    Final,
}

impl Phase {
    pub fn as_str(self) -> &'static str {
        match self {
            Phase::StartPlacement => "start_placement",
            Phase::Drafting => "drafting",
            Phase::Tiling => "tiling",
            Phase::Scoring => "scoring",
            Phase::End => "end",
            Phase::Final => "final",
        }
    }
}

/// Vollständiger Spielzustand.
#[derive(Debug, Clone)]
pub struct GameState {
    pub bag: Bag,
    pub tower: Tower,

    pub factories: Vec<Factory>,
    pub large_factory: LargeFactory,

    pub players: Vec<PlayerBoard>,

    pub dome_tile_pool: Vec<DomeTile>, // verdeckter Stapel (F)
    pub dome_display: Vec<DomeTile>,   // 3 offen ausgelegte Kuppeln (G)
    pub bonus_chip_pool: Vec<BonusChip>,
    /// Aktion A (Stapel-Variante), laufender Zieh-Vorgang von `current_player`:
    /// bereits gezogene, aber noch nicht gewählte Platten (Rückseite zeigt
    /// beim Ziehen nur den Typ, siehe DomeTile::is_special_type). Leer, wenn
    /// gerade kein Stapel-Zug läuft. Reset bei `Action::DrawStack` (Wahl
    /// getroffen) und beim Rundenwechsel.
    pub pending_stack_draw: Vec<DomeTile>,

    /// Baustein B (zweistufiger Kuppel-Suchknoten): Stufe-1-Wahl (Kachel+Slot),
    /// die noch auf ihre Stufe-2-Rotation wartet. `None`, solange kein
    /// Kuppel-Zug im Gange ist. Reset bei `Action::ChooseDomeRotation`
    /// (Wahl abgeschlossen) und beim Rundenwechsel.
    pub pending_dome_choice: Option<PendingDomeChoice>,

    pub scoring_tile_ids: Vec<usize>,

    pub round_number: u32,
    pub current_player: usize,
    pub first_player_next_round: usize,

    pub phase: Phase,
    pub log: Vec<String>,
    pub tiling_done: [bool; 2],
}

impl GameState {
    pub fn log_event(&mut self, msg: impl Into<String>) {
        self.log
            .push(format!("[R{}] {}", self.round_number, msg.into()));
    }

    pub fn active_player(&self) -> &PlayerBoard {
        &self.players[self.current_player]
    }
    pub fn switch_player(&mut self) {
        self.current_player = 1 - self.current_player;
    }

    pub fn all_factories_empty(&self) -> bool {
        self.factories.iter().all(|f| f.is_fully_empty()) && self.large_factory.is_empty()
    }
}

// ── Setup-Helfer ─────────────────────────────────────────────────────────────

fn draw_with_refill<R: Rng + ?Sized>(
    n: usize,
    bag: &mut Bag,
    tower: &mut Tower,
    rng: &mut R,
) -> Vec<TileColor> {
    let mut drawn = bag.draw(n);
    if drawn.len() < n && !tower.is_empty() {
        bag.refill_from_tower(tower, rng);
        drawn.extend(bag.draw(n - drawn.len()));
    }
    drawn
}

fn fill_large_factory<R: Rng + ?Sized>(
    large_factory: &mut LargeFactory,
    bag: &mut Bag,
    tower: &mut Tower,
    rng: &mut R,
) {
    // R3 (Regelbuch S.10): können Beutel+Turm zusammen keine 2 verschiedenen
    // Farben mehr liefern, würde der Redraw-Loop unten endlos laufen. Dann
    // wird die monochrome Befüllung akzeptiert und markiert -- die Sonnen-
    // Nahme vergibt in diesem Fall die Startspielerfliese (siehe
    // `LargeFactory::take_from_sun`), weil der Mondbereich leer bleibt.
    let mut available: Vec<TileColor> = Vec::new();
    for &t in bag.tiles.iter().chain(tower.tiles.iter()) {
        if !available.contains(&t) {
            available.push(t);
            if available.len() >= 2 {
                break;
            }
        }
    }
    if available.len() < 2 {
        large_factory.sun_tiles = draw_with_refill(TILES_PER_LARGE_FACTORY, bag, tower, rng);
        large_factory.monochrome_fallback = true;
        if large_factory.sun_tiles.is_empty() {
            // Gar keine Fliesen mehr im Spiel-Vorrat: der Marker wäre über
            // keinen Zug mehr nehmbar (weder Sonne noch Mond) und würde
            // `is_empty()` dauerhaft blockieren -- defensiv entfernen,
            // `first_player_next_round` bleibt beim bisherigen Halter.
            large_factory.has_first_player_marker = false;
        }
        return;
    }
    loop {
        let tiles = draw_with_refill(TILES_PER_LARGE_FACTORY, bag, tower, rng);
        // mindestens 2 verschiedene Farben?
        let mut distinct: Vec<_> = Vec::new();
        for &t in &tiles {
            if !distinct.contains(&t) {
                distinct.push(t);
            }
        }
        if distinct.len() >= 2 {
            large_factory.sun_tiles = tiles;
            return;
        }
        // Alle gleiche Farbe → zurück in den Beutel, neu mischen.
        bag.tiles.extend(tiles);
        bag.tiles.shuffle(rng);
    }
}

fn fill_factories<R: Rng + ?Sized>(
    factories: &mut [Factory],
    large_factory: &mut LargeFactory,
    bag: &mut Bag,
    tower: &mut Tower,
    rng: &mut R,
    mut bonus_pool: Option<&mut Vec<BonusChip>>,
) {
    for factory in factories.iter_mut() {
        factory.sun_tiles.clear();
        factory.moon_stacks.clear();
        factory.bonus_chip_revealed = false;
        factory.sun_tiles = draw_with_refill(TILES_PER_SMALL_FACTORY, bag, tower, rng);
        if let Some(pool) = bonus_pool.as_deref_mut() {
            factory.bonus_chip = pool.pop();
        }
        // R4 (Regelbuch S.10): bleibt eine kleine Manufaktur bei der
        // Rundenvorbereitung ohne Fliesen (Beutel+Turm erschöpft), wird ihr
        // Bonusplättchen sofort aufgedeckt -- sonst würde
        // `reveal_chip_if_empty` nie feuern und die Fabrik gälte nie als
        // abgeräumt (Deadlock in check_drafting_complete).
        if factory.is_fully_empty() {
            factory.bonus_chip_revealed = true;
        }
    }
    fill_large_factory(large_factory, bag, tower, rng);
}

// ── Öffentliche Setup-Funktionen ─────────────────────────────────────────────

/// Erstellt einen vollständig initialisierten Spielzustand für eine neue Partie.
pub fn setup_new_game<R: Rng + ?Sized>(
    player_names: [String; NUM_PLAYERS],
    first_player: usize,
    rng: &mut R,
) -> GameState {
    let mut bag = Bag::full(rng);
    let mut tower = Tower::default();

    let mut players: Vec<PlayerBoard> = player_names
        .into_iter()
        .enumerate()
        .map(|(i, name)| PlayerBoard::new(i, name))
        .collect();

    // Fabriken + je 1 verdeckter Bonus-Chip aus dem gemischten Pool.
    let mut bonus_pool = build_bonus_chip_pool();
    bonus_pool.shuffle(rng);
    let mut factories: Vec<Factory> = (0..NUM_SMALL_FACTORIES)
        .map(|i| Factory::new(i + 1))
        .collect();
    for factory in factories.iter_mut() {
        factory.bonus_chip = bonus_pool.pop();
    }
    let mut large_factory = LargeFactory::default();
    // Chips bereits zugewiesen → fill ohne Pool (None), damit sie nicht überschrieben werden.
    fill_factories(&mut factories, &mut large_factory, &mut bag, &mut tower, rng, None);

    // Kuppelplatten mischen: 3 offen (G), Rest verdeckt (F).
    let mut all_dome = build_dome_tile_pool();
    all_dome.shuffle(rng);
    for p in players.iter_mut() {
        p.start_tile_pending = true;
    }
    let dome_display: Vec<DomeTile> = all_dome.drain(..3.min(all_dome.len())).collect();
    let dome_tile_pool = all_dome; // verbleibende 15

    let mut state = GameState {
        bag,
        tower,
        factories,
        large_factory,
        players,
        dome_tile_pool,
        dome_display,
        bonus_chip_pool: bonus_pool,
        pending_stack_draw: Vec::new(),
        pending_dome_choice: None,
        scoring_tile_ids: Vec::new(),
        round_number: 1,
        current_player: first_player,
        first_player_next_round: first_player,
        phase: Phase::Drafting,
        log: Vec::new(),
        tiling_done: [false, false],
    };
    let starter = state.players[first_player].name.clone();
    state.log_event(format!("Spiel gestartet. {starter} beginnt."));
    state
}

/// Bereitet eine neue Runde vor (Fabriken neu befüllen, Marker/Tokens zurücksetzen).
pub fn setup_new_round<R: Rng + ?Sized>(state: &mut GameState, rng: &mut R) {
    state.round_number += 1;
    state.phase = Phase::Drafting;
    state.current_player = state.first_player_next_round;
    state.large_factory.reset_for_new_round();

    fill_factories(
        &mut state.factories,
        &mut state.large_factory,
        &mut state.bag,
        &mut state.tower,
        rng,
        Some(&mut state.bonus_chip_pool),
    );

    for p in state.players.iter_mut() {
        p.reset_dome_placements();
        p.holds_first_player_marker = false;
    }
    let starter = state.players[state.current_player].name.clone();
    let rn = state.round_number;
    state.log_event(format!("Runde {rn} beginnt. {starter} ist Startspieler."));
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    fn names() -> [String; 2] {
        ["Spieler 1".into(), "Spieler 2".into()]
    }

    #[test]
    fn setup_new_game_initial_counts() {
        let mut rng = StdRng::seed_from_u64(42);
        let s = setup_new_game(names(), 0, &mut rng);

        assert_eq!(s.factories.len(), 4);
        for f in &s.factories {
            assert_eq!(f.sun_tiles.len(), 4);
            assert!(f.bonus_chip.is_some());
        }
        assert_eq!(s.large_factory.sun_tiles.len(), 5);
        // große Fabrik: mind. 2 verschiedene Farben
        let mut distinct: Vec<_> = Vec::new();
        for &t in &s.large_factory.sun_tiles {
            if !distinct.contains(&t) {
                distinct.push(t);
            }
        }
        assert!(distinct.len() >= 2);

        assert_eq!(s.dome_display.len(), 3);
        assert_eq!(s.dome_tile_pool.len(), 15);
        assert_eq!(s.bonus_chip_pool.len(), 16); // 20 - 4 zugewiesen
        assert!(s.players.iter().all(|p| p.start_tile_pending));
        // Beutel: 65 - (4*4 + 5) = 44
        assert_eq!(s.bag.count(), 44);
        assert_eq!(s.current_player, 0);
        assert_eq!(s.round_number, 1);
    }

    #[test]
    fn new_round_refills_and_advances() {
        let mut rng = StdRng::seed_from_u64(7);
        let mut s = setup_new_game(names(), 0, &mut rng);
        s.first_player_next_round = 1;
        // Fabriken leeren, um echtes Neubefüllen zu sehen
        for f in s.factories.iter_mut() {
            f.sun_tiles.clear();
        }
        setup_new_round(&mut s, &mut rng);
        assert_eq!(s.round_number, 2);
        assert_eq!(s.current_player, 1);
        for f in &s.factories {
            assert_eq!(f.sun_tiles.len(), 4);
        }
        assert_eq!(s.large_factory.sun_tiles.len(), 5);
        assert!(s.large_factory.has_first_player_marker);
    }

    #[test]
    fn fill_large_factory_monochrome_fallback_terminates() {
        // R3 (Vollaudit 2026-07-21): liefern Beutel+Turm keine 2 Farben
        // mehr, wird die monochrome Befüllung akzeptiert (kein Endlos-Loop)
        // und `monochrome_fallback` gesetzt -- die Sonnen-Nahme vergibt
        // dann den Marker.
        let mut rng = StdRng::seed_from_u64(3);
        let mut bag = Bag { tiles: vec![TileColor::Rot; 6] };
        let mut tower = Tower::default();
        let mut lf = LargeFactory::default();
        fill_large_factory(&mut lf, &mut bag, &mut tower, &mut rng);
        assert_eq!(lf.sun_tiles.len(), 5);
        assert!(lf.sun_tiles.iter().all(|&t| t == TileColor::Rot));
        assert!(lf.monochrome_fallback);
        assert!(lf.has_first_player_marker);
        let (taken, rest, marker) = lf.take_from_sun(TileColor::Rot).unwrap();
        assert_eq!(taken.len(), 5);
        assert!(rest.is_empty());
        assert!(marker, "monochromer Fallback: Sonnen-Nahme vergibt den Marker");
        assert!(lf.is_empty());
    }

    #[test]
    fn fill_factories_reveals_chip_on_empty_factory() {
        // R4 (Vollaudit 2026-07-21): bleibt eine kleine Fabrik bei der
        // Rundenvorbereitung ohne Fliesen, wird ihr Chip sofort aufgedeckt.
        let mut rng = StdRng::seed_from_u64(4);
        let mut s = setup_new_game(names(), 0, &mut rng);
        // Beutel+Turm komplett leeren → Neubefüllung bleibt fliesenlos.
        s.bag.tiles.clear();
        s.tower.tiles.clear();
        setup_new_round(&mut s, &mut rng);
        for f in &s.factories {
            assert!(f.is_fully_empty());
            assert!(
                f.bonus_chip_revealed,
                "Chip einer leer gebliebenen Fabrik muss sofort aufgedeckt sein"
            );
        }
        // Große Fabrik: gar keine Fliesen mehr → Fallback greift, Marker
        // wird defensiv entfernt, damit is_empty() erreichbar bleibt.
        assert!(s.large_factory.monochrome_fallback);
        assert!(s.large_factory.is_empty());
    }
}
