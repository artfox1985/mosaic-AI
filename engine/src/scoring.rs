//! Wertungsplatten (Endwertung) — Port von engine/scoring.py.
//!
//! 8 Wertungskriterien; zu Spielbeginn werden 3 (ohne sich ausschließende Paare)
//! gewählt und am Spielende nach der Tiling-Phase der 5. Runde gewertet.

use rand::seq::SliceRandom;
use rand::{Rng, RngExt};

use crate::board::PlayerBoard;
use crate::dome::{DomeSpace, SpaceType};
use crate::tile::TileColor;

// ── Wertungsplatten-Metadaten + Dispatch ────────────────────────────────────────

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ScoringTile {
    pub id: usize,
    pub name: &'static str,
    pub description: &'static str,
    pub emoji: &'static str,
}

impl ScoringTile {
    /// Punkte dieser Wertungsplatte für das Spielerbrett.
    pub fn score(&self, player: &PlayerBoard) -> i32 {
        match self.id {
            0 => score_horizontal_rows(player),
            1 => score_vertical_rows(player),
            2 => score_diagonal_rows(player),
            3 => score_wild_fields(player),
            4 => score_outer_fields(player),
            5 => score_corner_tiles(player),
            6 => score_empty_special_fields(player),
            7 => score_colorful_rows(player),
            _ => 0,
        }
    }
}

/// Alle 8 Wertungsplatten (ID == Index).
pub const ALL_SCORING_TILES: [ScoringTile; 8] = [
    ScoringTile { id: 0, name: "Horizontale Reihen", description: "3 Pkt je vollständige horizontale Reihe (6 Fliesen)", emoji: "↔️" },
    ScoringTile { id: 1, name: "Vertikale Reihen", description: "7 Pkt je vollständige vertikale Reihe (6 Fliesen)", emoji: "↕️" },
    ScoringTile { id: 2, name: "Diagonale Reihen", description: "10 Pkt je vollständige Diagonale (max. 2×)", emoji: "↗️" },
    ScoringTile { id: 3, name: "Mehrfarbige Felder", description: "2 Pkt je Wildcard-Feld wenn ALLE belegt", emoji: "🌈" },
    ScoringTile { id: 4, name: "Äußere Felder", description: "1 Pkt je Fliese auf dem Rand der Kuppel", emoji: "⬜" },
    ScoringTile { id: 5, name: "Eckplatten", description: "3/8 Pkt je Eckkuppelplatte (obere/untere)", emoji: "🔲" },
    ScoringTile { id: 6, name: "Spezialfelder", description: "−3 Pkt je leeres Spezialfliesenfeld", emoji: "⭐" },
    ScoringTile { id: 7, name: "Farbenreiche Reihen", description: "4 Pkt je Reihe mit ≥5 verschiedenen Farben", emoji: "🎨" },
];

/// Wertungsplatte anhand der ID.
pub fn scoring_tile_by_id(id: usize) -> Option<&'static ScoringTile> {
    ALL_SCORING_TILES.iter().find(|t| t.id == id)
}

// ── Ausschluss-Paare ────────────────────────────────────────────────────────────

/// Sich gegenseitig ausschließende Wertungsplatten-Paare (höchstens eine je Paar).
pub const MUTUALLY_EXCLUSIVE_PAIRS: [(usize, usize); 4] = [
    (0, 7), // Horizontale Reihen ⟷ Farbenreiche Reihen
    (6, 3), // Spezialfelder      ⟷ Mehrfarbige Felder
    (4, 1), // Äußere Felder      ⟷ Vertikale Reihen
    (2, 5), // Diagonale Reihen   ⟷ Eckplatten
];

/// Partner-ID der ausschließenden Platte, falls vorhanden.
pub fn exclusion_partner(tile_id: usize) -> Option<usize> {
    for &(a, b) in &MUTUALLY_EXCLUSIVE_PAIRS {
        if tile_id == a {
            return Some(b);
        }
        if tile_id == b {
            return Some(a);
        }
    }
    None
}

/// True, wenn zwei IDs aus demselben Ausschluss-Paar gewählt wurden.
pub fn has_exclusion_conflict(tile_ids: &[usize]) -> bool {
    MUTUALLY_EXCLUSIVE_PAIRS
        .iter()
        .any(|&(a, b)| tile_ids.contains(&a) && tile_ids.contains(&b))
}

/// Wählt n Wertungsplatten zufällig, ohne zwei aus demselben Ausschluss-Paar.
/// Aus jedem Paar wird höchstens eine Seite in den Pool genommen.
pub fn sample_valid_scoring_ids<R: Rng + ?Sized>(n: usize, rng: &mut R) -> Vec<usize> {
    let mut pool: Vec<usize> = MUTUALLY_EXCLUSIVE_PAIRS
        .iter()
        .map(|&(a, b)| if rng.random_range(0..2) == 0 { a } else { b })
        .collect();

    // Platten ohne Paar ebenfalls aufnehmen (aktuell sind alle 8 gepaart).
    let paired: Vec<usize> = MUTUALLY_EXCLUSIVE_PAIRS
        .iter()
        .flat_map(|&(a, b)| [a, b])
        .collect();
    for t in ALL_SCORING_TILES.iter() {
        if !paired.contains(&t.id) {
            pool.push(t.id);
        }
    }

    pool.shuffle(rng);
    pool.truncate(n.min(pool.len()));
    pool
}

// ── Endwertung ──────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ScoringDetail {
    pub id: usize,
    pub name: &'static str,
    pub emoji: &'static str,
    pub description: &'static str,
    pub score: i32,
}

#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct EndScoring {
    pub details: Vec<ScoringDetail>,
    pub total: i32,
}

/// Endwertung eines Spielers für die gewählten Wertungsplatten.
pub fn calculate_end_scoring(player: &PlayerBoard, tile_ids: &[usize]) -> EndScoring {
    let mut result = EndScoring::default();
    for &tid in tile_ids {
        let tile = match scoring_tile_by_id(tid) {
            Some(t) => t,
            None => continue,
        };
        let pts = tile.score(player);
        result.details.push(ScoringDetail {
            id: tile.id,
            name: tile.name,
            emoji: tile.emoji,
            description: tile.description,
            score: pts,
        });
        result.total += pts;
    }
    result
}

// ── Einzelne Wertungen ──────────────────────────────────────────────────────────

fn score_horizontal_rows(player: &PlayerBoard) -> i32 {
    let grid = build_grid(player);
    (0..6).filter(|&r| (0..6).all(|c| grid[r][c])).count() as i32 * 3
}

fn score_vertical_rows(player: &PlayerBoard) -> i32 {
    let grid = build_grid(player);
    (0..6).filter(|&c| (0..6).all(|r| grid[r][c])).count() as i32 * 7
}

fn score_diagonal_rows(player: &PlayerBoard) -> i32 {
    let grid = build_grid(player);
    let mut pts = 0;
    if (0..6).all(|i| grid[i][i]) {
        pts += 10;
    }
    if (0..6).all(|i| grid[i][5 - i]) {
        pts += 10;
    }
    pts
}

fn score_wild_fields(player: &PlayerBoard) -> i32 {
    let wild = collect_spaces(player, SpaceType::Wild);
    if wild.is_empty() {
        return 0;
    }
    if wild.iter().all(|sp| sp.is_filled()) {
        2 * wild.len() as i32
    } else {
        0
    }
}

fn score_outer_fields(player: &PlayerBoard) -> i32 {
    let grid = build_grid(player);
    let mut pts = 0;
    for r in 0..6 {
        for c in 0..6 {
            if (r == 0 || r == 5 || c == 0 || c == 5) && grid[r][c] {
                pts += 1;
            }
        }
    }
    pts
}

fn score_corner_tiles(player: &PlayerBoard) -> i32 {
    let mut pts = 0;
    let count_full = |sr: usize, sc: usize| -> bool {
        player.dome_grid.dome_slots[sr][sc]
            .as_ref()
            .map_or(false, |slot| slot.spaces.iter().filter(|sp| sp.is_filled()).count() == 4)
    };
    for &(sr, sc) in &[(0usize, 0usize), (0, 2)] {
        if count_full(sr, sc) {
            pts += 3;
        }
    }
    for &(sr, sc) in &[(2usize, 0usize), (2, 2)] {
        if count_full(sr, sc) {
            pts += 8;
        }
    }
    pts
}

fn score_empty_special_fields(player: &PlayerBoard) -> i32 {
    let special = collect_spaces(player, SpaceType::Special);
    let empty = special.iter().filter(|sp| !sp.is_filled()).count() as i32;
    -3 * empty
}

fn score_colorful_rows(player: &PlayerBoard) -> i32 {
    (0..6)
        .filter(|&r| row_unique_colors(player, r) >= 5)
        .count() as i32
        * 4
}

// ── Hilfsfunktionen ─────────────────────────────────────────────────────────────

/// 6×6-Bool-Raster aus der Kuppel (true = Fliese vorhanden).
fn build_grid(player: &PlayerBoard) -> [[bool; 6]; 6] {
    let mut grid = [[false; 6]; 6];
    for sr in 0..3 {
        for sc in 0..3 {
            if let Some(slot) = &player.dome_grid.dome_slots[sr][sc] {
                for (si, sp) in slot.spaces.iter().enumerate() {
                    if sp.is_filled() {
                        grid[sr * 2 + si / 2][sc * 2 + si % 2] = true;
                    }
                }
            }
        }
    }
    grid
}

/// Alle Spaces eines bestimmten Typs über alle gelegten Kacheln.
fn collect_spaces(player: &PlayerBoard, kind: SpaceType) -> Vec<&DomeSpace> {
    let mut spaces = Vec::new();
    for sr in 0..3 {
        for sc in 0..3 {
            if let Some(slot) = &player.dome_grid.dome_slots[sr][sc] {
                spaces.extend(slot.spaces.iter().filter(|sp| sp.space_type == kind));
            }
        }
    }
    spaces
}

/// Anzahl verschiedener Stein-Farben einer horizontalen 6×6-Reihe
/// (Spezialfliesen und Lücken zählen nicht).
fn row_unique_colors(player: &PlayerBoard, row6: usize) -> usize {
    let sr = row6 / 2;
    let si_row = row6 % 2;
    let mut seen: Vec<TileColor> = Vec::new();
    for sc in 0..3 {
        if let Some(slot) = &player.dome_grid.dome_slots[sr][sc] {
            for si_col in 0..2 {
                let sp = &slot.spaces[si_row * 2 + si_col];
                if sp.placed_special {
                    continue;
                }
                if let Some(col) = sp.placed_color {
                    if !seen.contains(&col) {
                        seen.push(col);
                    }
                }
            }
        }
    }
    seen.len()
}

// ── Berechnete Features fürs Netz ───────────────────────────────────────────────

/// Endwertungs- und Geometrie-Features eines Spielerbretts — damit das Netz lernt,
/// WIE (End-)Punkte entstehen, statt sie aus der flachen Brett-Kodierung raten zu
/// müssen. Wird über `serialize_player` ins State-Dict gespiegelt.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ScoringFeatures {
    /// Aktuelle Punkte je der 8 Wertungsplatten (ID == Index).
    pub tile_points: [i32; 8],
    /// Gefüllte Felder je horizontaler 6er-Reihe.
    pub row_fill: [u32; 6],
    /// Gefüllte Felder je vertikaler 6er-Spalte.
    pub col_fill: [u32; 6],
    /// Gefüllte Felder je Diagonale (Haupt-, Nebendiagonale).
    pub diag_fill: [u32; 2],
    /// Verschiedene platzierte Farben je horizontaler Reihe (→ farbenreiche Reihen).
    pub row_colors: [u32; 6],
    /// Gefüllte Felder auf dem 6×6-Rand.
    pub border_fill: u32,
    /// Gefüllte Felder je Eckplatte: (0,0),(0,2),(2,0),(2,2).
    pub corner_fill: [u32; 4],
    pub wild_filled: u32,
    pub wild_total: u32,
    pub special_empty: u32,
    pub special_total: u32,
}

/// Berechnet die [`ScoringFeatures`] eines Bretts (reuse der Wertungs-Helfer).
pub fn player_scoring_features(player: &PlayerBoard) -> ScoringFeatures {
    let grid = build_grid(player);

    let mut tile_points = [0i32; 8];
    for (i, slot) in tile_points.iter_mut().enumerate() {
        *slot = ALL_SCORING_TILES[i].score(player);
    }

    let mut row_fill = [0u32; 6];
    let mut col_fill = [0u32; 6];
    for r in 0..6 {
        for c in 0..6 {
            if grid[r][c] {
                row_fill[r] += 1;
                col_fill[c] += 1;
            }
        }
    }

    let mut diag_fill = [0u32; 2];
    for i in 0..6 {
        if grid[i][i] {
            diag_fill[0] += 1;
        }
        if grid[i][5 - i] {
            diag_fill[1] += 1;
        }
    }

    let mut row_colors = [0u32; 6];
    for (r, slot) in row_colors.iter_mut().enumerate() {
        *slot = row_unique_colors(player, r) as u32;
    }

    let mut border_fill = 0;
    for r in 0..6 {
        for c in 0..6 {
            if (r == 0 || r == 5 || c == 0 || c == 5) && grid[r][c] {
                border_fill += 1;
            }
        }
    }

    let mut corner_fill = [0u32; 4];
    for (k, &(sr, sc)) in [(0usize, 0usize), (0, 2), (2, 0), (2, 2)].iter().enumerate() {
        corner_fill[k] = player.dome_grid.dome_slots[sr][sc]
            .as_ref()
            .map_or(0, |slot| slot.spaces.iter().filter(|sp| sp.is_filled()).count() as u32);
    }

    let wild = collect_spaces(player, SpaceType::Wild);
    let wild_total = wild.len() as u32;
    let wild_filled = wild.iter().filter(|sp| sp.is_filled()).count() as u32;
    let special = collect_spaces(player, SpaceType::Special);
    let special_total = special.len() as u32;
    let special_empty = special.iter().filter(|sp| !sp.is_filled()).count() as u32;

    ScoringFeatures {
        tile_points,
        row_fill,
        col_fill,
        diag_fill,
        row_colors,
        border_fill,
        corner_fill,
        wild_filled,
        wild_total,
        special_empty,
        special_total,
    }
}

// ── Linien-Geometrie-Features (offensives Linien-Bauen) ─────────────────────────

/// Räumliche Linien-Information, damit das flache MLP offensives Cluster-/Linien-
/// Bauen lernen kann (statt zur Strafleiste zu degenerieren). Punkte entstehen aus
/// zusammenhängenden orthogonalen Läufen ([`crate::round_end::score_placed_tile`]);
/// diese Features machen genau diese Struktur explizit.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LineFeatures {
    /// Anzahl horizontaler maximaler Läufe der Länge 2,3,4,5,6.
    pub h_hist: [u32; 5],
    /// Anzahl vertikaler maximaler Läufe der Länge 2,3,4,5,6.
    pub v_hist: [u32; 5],
    /// Σ Lauflänge² über alle h+v-Läufe (Länge ≥ 2) — belohnt lange Linien.
    pub cluster_sq: u32,
    /// Je Reihe: maximaler Linien-Zuwachs, den ein füllbares Feld dort brächte
    /// (= `score_placed_tile`-Wert, wenn dort ein Stein läge).
    pub row_potential: [u32; 6],
    /// Je Spalte: dito.
    pub col_potential: [u32; 6],
}

fn bucket_run(run: u32, hist: &mut [u32; 5], cluster_sq: &mut u32) {
    if run >= 2 {
        hist[(run.min(6) - 2) as usize] += 1;
        *cluster_sq += run * run;
    }
}

/// Länge des zusammenhängenden gefüllten Laufs durch `(r,c)` in Richtung
/// `(dr,dc)` (beide Seiten), inkl. des hypothetisch gefüllten Felds selbst.
fn run_through(filled: &[[bool; 6]; 6], r: usize, c: usize, dr: i32, dc: i32) -> u32 {
    let mut n = 1u32;
    for &sign in &[1i32, -1] {
        let (mut rr, mut cc) = (r as i32 + sign * dr, c as i32 + sign * dc);
        while (0..6).contains(&rr) && (0..6).contains(&cc) && filled[rr as usize][cc as usize] {
            n += 1;
            rr += sign * dr;
            cc += sign * dc;
        }
    }
    n
}

/// Berechnet die [`LineFeatures`] eines Bretts.
pub fn player_line_features(player: &PlayerBoard) -> LineFeatures {
    // 6×6-Raster: gefüllt bzw. füllbar (Slot vorhanden, leer, nicht gesperrt).
    let mut filled = [[false; 6]; 6];
    let mut placeable = [[false; 6]; 6];
    for sr in 0..3 {
        for sc in 0..3 {
            if let Some(slot) = &player.dome_grid.dome_slots[sr][sc] {
                for (si, sp) in slot.spaces.iter().enumerate() {
                    let (r, c) = (sr * 2 + si / 2, sc * 2 + si % 2);
                    if sp.is_filled() {
                        filled[r][c] = true;
                    } else if !sp.is_locked {
                        placeable[r][c] = true;
                    }
                }
            }
        }
    }

    let mut h_hist = [0u32; 5];
    let mut v_hist = [0u32; 5];
    let mut cluster_sq = 0u32;
    for r in 0..6 {
        let mut run = 0u32;
        for c in 0..6 {
            if filled[r][c] {
                run += 1;
            } else {
                bucket_run(run, &mut h_hist, &mut cluster_sq);
                run = 0;
            }
        }
        bucket_run(run, &mut h_hist, &mut cluster_sq);
    }
    for c in 0..6 {
        let mut run = 0u32;
        for r in 0..6 {
            if filled[r][c] {
                run += 1;
            } else {
                bucket_run(run, &mut v_hist, &mut cluster_sq);
                run = 0;
            }
        }
        bucket_run(run, &mut v_hist, &mut cluster_sq);
    }

    let mut row_potential = [0u32; 6];
    let mut col_potential = [0u32; 6];
    for r in 0..6 {
        for c in 0..6 {
            if !placeable[r][c] {
                continue;
            }
            let h = run_through(&filled, r, c, 0, 1);
            let v = run_through(&filled, r, c, 1, 0);
            // Wie score_placed_tile: alleinstehend = 1, sonst Summe der Läufe > 1.
            let gain = if h <= 1 && v <= 1 {
                1
            } else {
                (if h > 1 { h } else { 0 }) + (if v > 1 { v } else { 0 })
            };
            row_potential[r] = row_potential[r].max(gain);
            col_potential[c] = col_potential[c].max(gain);
        }
    }

    LineFeatures { h_hist, v_hist, cluster_sq, row_potential, col_potential }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dome::{build_dome_tile_pool, DomeTile};
    use crate::tile::TileColor::*;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    /// Hilfsbrett: füllt das komplette 6×6-Raster mit Platten und allen Steinen.
    fn fully_filled_board() -> PlayerBoard {
        let mut p = PlayerBoard::new(0, "P");
        let pool = build_dome_tile_pool();
        for sr in 0..3 {
            for sc in 0..3 {
                let mut t: DomeTile = pool[sr * 3 + sc].clone();
                // Alle Spaces befüllen (Special direkt als Special markieren).
                for sp in t.spaces.iter_mut() {
                    match sp.space_type {
                        SpaceType::Special => {
                            sp.is_locked = false;
                            sp.placed_special = true;
                        }
                        SpaceType::Wild => sp.placed_color = Some(Rot),
                        SpaceType::Normal => sp.placed_color = sp.required_color,
                    }
                }
                p.dome_grid.place_dome_tile(t, sr, sc).unwrap();
            }
        }
        p
    }

    #[test]
    fn horizontal_and_vertical_full_board() {
        let p = fully_filled_board();
        // 6 volle horizontale Reihen × 3, 6 volle vertikale × 7.
        assert_eq!(score_horizontal_rows(&p), 18);
        assert_eq!(score_vertical_rows(&p), 42);
        // 2 Diagonalen × 10.
        assert_eq!(score_diagonal_rows(&p), 20);
    }

    #[test]
    fn empty_board_penalizes_specials() {
        let mut p = PlayerBoard::new(0, "P");
        // Eine Platte mit Special, nichts belegt → −3 für das leere Special.
        let tile = build_dome_tile_pool()[0].clone(); // enthält 1 Special
        p.dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        assert_eq!(score_empty_special_fields(&p), -3);
    }

    #[test]
    fn corner_tiles_top_and_bottom() {
        let p = fully_filled_board();
        // 2 obere Ecken × 3 + 2 untere Ecken × 8 = 6 + 16 = 22.
        assert_eq!(score_corner_tiles(&p), 22);
    }

    #[test]
    fn scoring_features_match_tile_scores_full_board() {
        let p = fully_filled_board();
        let sf = player_scoring_features(&p);
        // tile_points müssen exakt den Einzelwertungen entsprechen.
        for i in 0..8 {
            assert_eq!(sf.tile_points[i], ALL_SCORING_TILES[i].score(&p), "tile {i}");
        }
        // Volles Brett: jede Reihe/Spalte/Diagonale komplett gefüllt.
        assert_eq!(sf.row_fill, [6; 6]);
        assert_eq!(sf.col_fill, [6; 6]);
        assert_eq!(sf.diag_fill, [6, 6]);
        assert_eq!(sf.border_fill, 20);
        assert_eq!(sf.corner_fill, [4, 4, 4, 4]);
        // Special-Felder sind alle belegt (placed_special) → keine leeren.
        assert_eq!(sf.special_empty, 0);
        assert!(sf.special_total >= 1);
    }

    #[test]
    fn line_features_full_board() {
        let p = fully_filled_board();
        let lf = player_line_features(&p);
        // Volles Brett: 6 horizontale + 6 vertikale Läufe der Länge 6.
        assert_eq!(lf.h_hist, [0, 0, 0, 0, 6]); // alle len 6
        assert_eq!(lf.v_hist, [0, 0, 0, 0, 6]);
        // Cluster: 12 Läufe × 6² = 432.
        assert_eq!(lf.cluster_sq, 12 * 36);
        // Kein füllbares Feld mehr → Potential 0.
        assert_eq!(lf.row_potential, [0; 6]);
        assert_eq!(lf.col_potential, [0; 6]);
    }

    #[test]
    fn line_features_empty_board() {
        let p = PlayerBoard::new(0, "P");
        let lf = player_line_features(&p);
        assert_eq!(lf.h_hist, [0; 5]);
        assert_eq!(lf.v_hist, [0; 5]);
        assert_eq!(lf.cluster_sq, 0);
        // Kein Slot gelegt → keine füllbaren Felder → Potential 0.
        assert_eq!(lf.row_potential, [0; 6]);
    }

    #[test]
    fn scoring_features_empty_board_is_zero() {
        let p = PlayerBoard::new(0, "P");
        let sf = player_scoring_features(&p);
        assert_eq!(sf.row_fill, [0; 6]);
        assert_eq!(sf.border_fill, 0);
        assert_eq!(sf.corner_fill, [0; 4]);
        // Kein Brett gelegt → keine Wertungspunkte (auch keine Special-Strafe).
        assert_eq!(sf.tile_points, [0; 8]);
    }

    #[test]
    fn end_scoring_sums_selected_tiles() {
        let p = fully_filled_board();
        let res = calculate_end_scoring(&p, &[0, 1, 2]);
        assert_eq!(res.details.len(), 3);
        assert_eq!(res.total, 18 + 42 + 20);
    }

    #[test]
    fn sampling_avoids_exclusion_conflicts() {
        let mut rng = StdRng::seed_from_u64(123);
        for _ in 0..200 {
            let ids = sample_valid_scoring_ids(3, &mut rng);
            assert_eq!(ids.len(), 3);
            assert!(!has_exclusion_conflict(&ids), "Konflikt in {ids:?}");
            // keine Duplikate
            let mut sorted = ids.clone();
            sorted.sort_unstable();
            sorted.dedup();
            assert_eq!(sorted.len(), ids.len());
        }
    }

    #[test]
    fn exclusion_partner_is_symmetric() {
        assert_eq!(exclusion_partner(0), Some(7));
        assert_eq!(exclusion_partner(7), Some(0));
        assert_eq!(exclusion_partner(5), Some(2));
    }
}
