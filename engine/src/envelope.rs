//! Geometrische Einhuellende (K3, `PREREG_geometric_envelope.md` par.8):
//! die Groesse `H(brett)`, die das Gelaender in Suche (par.8.2) und Tiling
//! (par.8.3) liest, plus das Runden-Profil `w_e`.
//!
//! Definitionen exakt wie die Python-Sonde
//! `tools/probes/triangle_hull_coverage_probe.py` (Stand der Berichtigung
//! 2026-09-03): zwei Huellen-Orientierungen, LINKS `r + c <= 5` und RECHTS
//! `r <= c` (Spiegelung an der senkrechten Achse; die Reihen-Spiegelung ist
//! ausdruecklich ausgeschlossen), Zellenkosten `r + 1` (Rasterzeile `r`
//! braucht Musterreihe `r`, also `r + 1` Fliesen), Gesamtkost einer Huelle
//! 56. Die bestpassende Huelle ist die mit der kleineren UNGEWICHTETEN
//! Abweichung (Zellen der Huelle ohne Stein plus Steine ausserhalb), bei
//! Gleichstand LINKS -- genau wie `best_hull` der Sonde (`<=`).
//!
//! `H(brett)` (par.8.1) = kosten-gewichteter Fuellanteil INNERHALB der
//! bestpassenden Huelle (Summe `r + 1` der belegten Huellenzellen / 56) MINUS
//! Summe `r + 1` der belegten Zellen AUSSERHALB / 56. Leeres Brett: 0.
//! Der Paritaetstest unten haelt drei Bretter gegen die Zahlen der Sonde.

use crate::board::PlayerBoard;

/// Gesamtkost einer Huelle: Summe `r + 1` ueber ihre 21 Zellen (beide
/// Orientierungen: 6 + 10 + 12 + 12 + 10 + 6).
pub const HULL_TOTAL_COST: f64 = 56.0;

/// Runden-Profil `w_e(r)` aus der Verlaesslichkeit des Value-Kopfs je Runde
/// (par.8.5, Traeger `v23-b01_brierbest`,
/// `evaluations/artifacts/value_head_reliability_by_round.json`):
/// `w_e(r) = (rho(5) - rho(r)) / (rho(5) - rho(1))` mit rho 0,143 / 0,201 /
/// 0,390 / 0,641 / 0,881 -> 1,00 / 0,92 / 0,67 / 0,33 / 0. Runde 5 ist per
/// Auflage par.4.1 immer 0 (der exakte Loeser bekommt nichts). Die Regel
/// verlangt, das Profil JE TRAEGER neu zu berechnen und per
/// `MOSAIC_ENVELOPE_PROFILE` zu setzen; dieser Default ist die gemessene
/// b01-Kurve, kein Hand-Profil.
pub const ENVELOPE_PROFILE_DEFAULT: [f64; 5] = [1.0, 0.92, 0.67, 0.33, 0.0];

/// Toleranz fuer "gleicher bereinigter Score" im Tiling-Zweig (par.8.3:
/// der Netz-Stichentscheid greift nur noch unter Kandidaten mit gleichem
/// `Punkte + W_TILE * w_e * dH`).
pub const ENVELOPE_TIE_EPS: f64 = 1e-9;

/// Orientierung der bestpassenden Huelle.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Hull {
    /// `r + c <= 5`: volle Zeile 0 und volle Spalte 0.
    Left,
    /// `r <= c`: volle Zeile 0 und volle Spalte 5.
    Right,
}

impl Hull {
    #[inline]
    pub fn contains(self, r: usize, c: usize) -> bool {
        match self {
            Hull::Left => r + c <= 5,
            Hull::Right => r <= c,
        }
    }
}

/// Bedien-Kosten einer Rasterzelle: `r + 1` (regel-hergeleitet, nicht gefittet).
#[inline]
pub fn row_cost(r: usize) -> f64 {
    (r + 1) as f64
}

/// Belegung des 6x6-Kuppelrasters (`[zeile][spalte]`), wie
/// `tiling_solver::belegtes_raster`, nur als 2D-Feld.
pub fn occupancy(board: &PlayerBoard) -> [[bool; 6]; 6] {
    let mut out = [[false; 6]; 6];
    for (r, row) in out.iter_mut().enumerate() {
        for (c, cell) in row.iter_mut().enumerate() {
            *cell = board.dome_grid.get_space(r, c).is_some_and(|sp| sp.is_filled());
        }
    }
    out
}

/// Ungewichtete Abweichung: leere Huellenzellen plus Steine ausserhalb
/// (`deviation` der Sonde).
pub fn deviation(occ: &[[bool; 6]; 6], hull: Hull) -> usize {
    let mut d = 0;
    for (r, row) in occ.iter().enumerate() {
        for (c, &filled) in row.iter().enumerate() {
            if hull.contains(r, c) != filled {
                d += 1;
            }
        }
    }
    d
}

/// Bestpassende Huelle: kleinere Abweichung, bei Gleichstand LINKS
/// (`best_hull` der Sonde, `<=`).
pub fn best_hull(occ: &[[bool; 6]; 6]) -> Hull {
    if deviation(occ, Hull::Left) <= deviation(occ, Hull::Right) {
        Hull::Left
    } else {
        Hull::Right
    }
}

/// `(innen, aussen)`: kosten-gewichtete Belegung innerhalb bzw. ausserhalb
/// der Huelle, jeweils geteilt durch [`HULL_TOTAL_COST`]. `innen` ist genau
/// `weighted_fill_share` der Sonde.
pub fn weighted_shares(occ: &[[bool; 6]; 6], hull: Hull) -> (f64, f64) {
    let (mut inside, mut outside) = (0.0, 0.0);
    for (r, row) in occ.iter().enumerate() {
        for (c, &filled) in row.iter().enumerate() {
            if filled {
                if hull.contains(r, c) {
                    inside += row_cost(r);
                } else {
                    outside += row_cost(r);
                }
            }
        }
    }
    (inside / HULL_TOTAL_COST, outside / HULL_TOTAL_COST)
}

/// `H(brett)` nach par.8.1 fuer eine gegebene Belegung.
pub fn envelope_score_of(occ: &[[bool; 6]; 6]) -> f64 {
    let hull = best_hull(occ);
    let (inside, outside) = weighted_shares(occ, hull);
    inside - outside
}

/// `H(brett)` nach par.8.1: Leitkennzahl der Einhuellenden in [-1, 1]
/// (praktisch [0, 1]; Lehrer 0,68, Mensch 0,86 am Partieende).
pub fn envelope_score(board: &PlayerBoard) -> f64 {
    envelope_score_of(&occupancy(board))
}

// ── par.8.7 K3-P: das projizierte Brett ─────────────────────────────────────
// Zellen werden nur im Tiling gefuellt; waehrend des Draftings aendert sich
// das Raster nicht, und das Potential (e) ist im Suchbaum konstant (par.9:
// S 0,1 in allen 160 Partien ohne Wirkung). Die Projektion rechnet die
// Musterreihen anteilig auf ihre Zielzellen um: Musterreihe `r` mit Farbe
// `c` und `k` von `r + 1` Steinen landet in Rasterzeile `r` in einer Zelle,
// die `c` annimmt (`DomeSpace::accepts`); jede der `n` annehmenden Zellen
// bekommt `(k / (r + 1)) / n`.

/// Prozessweiter Schalter `MOSAIC_ENVELOPE_PROJECTED=1`: der Such-Term (e)
/// rechnet `H` auf dem projizierten Brett. Prozessweit ist hier unkritisch
/// (kein Spiegelmatch-Problem), weil der Term je Seite ueber
/// `SearchConfig::envelope_search_c` gegated ist -- die Kontrollseite mit
/// `c = 0` sieht ihn nie. Default aus = Bestand.
pub fn projected_mode() -> bool {
    static CELL: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| std::env::var("MOSAIC_ENVELOPE_PROJECTED").map(|v| v.trim() == "1").unwrap_or(false))
}

/// Gebrochene Belegung des projizierten Bretts (`[zeile][spalte]` in [0, 1]).
pub fn projected_occupancy(board: &PlayerBoard) -> [[f64; 6]; 6] {
    let occ = occupancy(board);
    let mut out = [[0.0f64; 6]; 6];
    for r in 0..6 {
        for c in 0..6 {
            if occ[r][c] {
                out[r][c] = 1.0;
            }
        }
    }
    for (r, line) in board.pattern_lines.iter().enumerate().take(6) {
        let (Some(color), k) = (line.color, line.tiles.len()) else { continue };
        if k == 0 {
            continue;
        }
        let targets: Vec<usize> = (0..6)
            .filter(|&c| board.dome_grid.get_space(r, c).is_some_and(|sp| sp.accepts(color)))
            .collect();
        if targets.is_empty() {
            continue;
        }
        let share = (k as f64 / (r + 1) as f64) / targets.len() as f64;
        for c in targets {
            out[r][c] += share;
        }
    }
    out
}

/// Ungewichtete Abweichung fuer gebrochene Belegung: Summe |Huelle - occ|.
pub fn deviation_frac(occ: &[[f64; 6]; 6], hull: Hull) -> f64 {
    let mut d = 0.0;
    for (r, row) in occ.iter().enumerate() {
        for (c, &v) in row.iter().enumerate() {
            let h = if hull.contains(r, c) { 1.0 } else { 0.0 };
            d += (h - v).abs();
        }
    }
    d
}

/// `H` nach par.8.1 ueber eine gebrochene Belegung (bestpassende Huelle nach
/// `deviation_frac`, Gleichstand LINKS; Anteile `Summe occ * (r + 1) / 56`).
pub fn envelope_score_frac(occ: &[[f64; 6]; 6]) -> f64 {
    let hull = if deviation_frac(occ, Hull::Left) <= deviation_frac(occ, Hull::Right) {
        Hull::Left
    } else {
        Hull::Right
    };
    let (mut inside, mut outside) = (0.0, 0.0);
    for (r, row) in occ.iter().enumerate() {
        for (c, &v) in row.iter().enumerate() {
            if v > 0.0 {
                if hull.contains(r, c) {
                    inside += v * row_cost(r);
                } else {
                    outside += v * row_cost(r);
                }
            }
        }
    }
    (inside - outside) / HULL_TOTAL_COST
}

/// `H_proj(brett)` (par.8.7): `H` auf dem projizierten Brett. Bei leeren
/// Musterreihen exakt `envelope_score` (gleiche Huelle, gleiche Anteile).
pub fn envelope_score_projected(board: &PlayerBoard) -> f64 {
    envelope_score_frac(&projected_occupancy(board))
}

/// `w_e(runde)` aus dem Profil: Index `runde - 1`, Runde 0 wie Runde 1,
/// Runden >= 5 lesen den letzten Eintrag (per Auflage 0).
pub fn profile_weight(profile: &[f64; 5], round: u32) -> f64 {
    let idx = (round.max(1) as usize - 1).min(4);
    profile[idx]
}

/// Such-Eingriff (e), par.8.2: `phi = w_e(runde) * (H(brett_0) - H(brett_1))`
/// aus Sicht von Spieler 0, `shift = C_HULL * tanh(phi)`. Der Aufrufer
/// addiert `shift` auf Spieler 0 und subtrahiert ihn von Spieler 1
/// (Nullsumme) und klammert beide auf [0, 1]. Reine Zustandsfunktion.
pub fn search_shift(board0: &PlayerBoard, board1: &PlayerBoard, round: u32, c_hull: f64, profile: &[f64; 5]) -> f64 {
    let (h0, h1) = if projected_mode() {
        (envelope_score_projected(board0), envelope_score_projected(board1))
    } else {
        (envelope_score(board0), envelope_score(board1))
    };
    let phi = profile_weight(profile, round) * (h0 - h1);
    c_hull * phi.tanh()
}

/// Tiling-Eingriff (d), par.8.3: `dH_kosten` eines Abschlusses in
/// Zellenkosten-Einheiten = `56 * (H(nachher) - H(vorher))`. Fuer einen
/// Abschluss ohne Orientierungswechsel ist das exakt "Summe `r + 1` der neu
/// gefuellten Zellen innerhalb der Huelle minus Summe ausserhalb"; kippt die
/// bestpassende Huelle durch den Abschluss, zaehlt die Umorientierung mit
/// (gewollt: die Groesse ist die Fuellung der BESTPASSENDEN Huelle).
pub fn tiling_cost_delta(before: &PlayerBoard, after: &PlayerBoard) -> f64 {
    HULL_TOTAL_COST * (envelope_score(after) - envelope_score(before))
}

/// Bereinigter Tiling-Score (par.8.3): `punkte + W_TILE * w_e * dH_kosten`.
#[inline]
pub fn adjusted_tiling_score(points: f64, w_tile: f64, w_e: f64, cost_delta: f64) -> f64 {
    points + w_tile * w_e * cost_delta
}

/// par.8.6 (Nutzer-Entscheid 2026-09-03, "Mach das so"): Tiling-Score mit
/// Value-Anteil in PUNKTEN. `margin` ist die vom Netz vorhergesagte Endmarge
/// nach dem Abschluss (`50 * atanh(p_own) - 50 * atanh(p_opp)`, Punkte- und
/// Gegnerpunkte-Kopf am Endzustand des Kandidaten), `w_v = 1 - w_e` das
/// Komplement des Profils: in Runde 1 fuehrt die Geometrie, in Runde 4 die
/// Vorhersage, in Runde 5 rechnet der Loeser exakt. Fehlt die Marge (Netz
/// ohne Koepfe), zaehlt der Term 0.
#[inline]
pub fn adjusted_tiling_score_with_value(
    points: f64, w_tile: f64, w_e: f64, cost_delta: f64, w_val: f64, margin: Option<f64>,
) -> f64 {
    points + w_tile * w_e * cost_delta + w_val * (1.0 - w_e) * margin.unwrap_or(0.0)
}

/// Knoepfe des Tiling-Eingriffs EINER Seite (par.8.3 und par.8.6), aus der
/// `SearchConfig` der Seite kopiert. `OFF` ist der Bestandspfad.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct EnvelopeTilingParams {
    /// `W_TILE` (par.8.3), Punkte je Zellenkosten-Einheit.
    pub w_tile: f64,
    /// `W_VAL` (par.8.6), Punkte je vorhergesagtem Endpunkt.
    pub w_val: f64,
    /// `w_e(Runde 1..5)`.
    pub profile: [f64; 5],
}

impl EnvelopeTilingParams {
    pub const OFF: EnvelopeTilingParams =
        EnvelopeTilingParams { w_tile: 0.0, w_val: 0.0, profile: ENVELOPE_PROFILE_DEFAULT };

    #[inline]
    pub fn is_off(&self) -> bool {
        self.w_tile == 0.0 && self.w_val == 0.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dome::{DomeSpace, DomeTile, SpaceType};

    /// Brett mit allen neun Kuppelplatten (je vier Wild-Spaces, wie die
    /// Testgitter in `scoring.rs`) und den genannten Zellen belegt.
    fn board_with(cells: &[(usize, usize)]) -> PlayerBoard {
        let mut board = PlayerBoard::new(0, "envelope-test");
        for sr in 0..3 {
            for sc in 0..3 {
                let spaces = (0..4)
                    .map(|_| DomeSpace {
                        space_type: SpaceType::Wild,
                        required_color: None,
                        placed_color: None,
                        placed_special: false,
                        is_locked: false,
                    })
                    .collect();
                board.dome_grid.place_dome_tile(DomeTile::new(sr * 3 + sc, spaces, 0), sr, sc).unwrap();
            }
        }
        for &(r, c) in cells {
            let sp = board.dome_grid.get_space_mut(r, c).expect("Rasterzelle existiert");
            sp.placed_color = Some(crate::tile::TileColor::Rot);
        }
        board
    }

    /// Paritaetstest gegen die Python-Sonde (par.8.1): drei Bretter, Zahlen
    /// am 2026-09-03 mit `triangle_hull_coverage_probe.py` (best_hull,
    /// weighted_fill_share, row_weight, deviation) berechnet.
    ///   A: (0,0)(0,1)(1,0)(2,0)(1,1)(5,5) -> LINKS, innen 9/56, aussen 6/56, devL 17, devR 19
    ///   B: (0,5)(1,5)(0,4)(2,5)(3,5)(4,5)(5,5)(0,0) -> RECHTS, innen 23/56, aussen 0, devL 23, devR 13
    ///   C: volle linke Huelle -> LINKS, H = 1, devL 0, devR 18
    #[test]
    fn envelope_score_matches_python_probe_on_three_boards() {
        let a = occupancy(&board_with(&[(0, 0), (0, 1), (1, 0), (2, 0), (1, 1), (5, 5)]));
        assert_eq!((deviation(&a, Hull::Left), deviation(&a, Hull::Right)), (17, 19));
        assert_eq!(best_hull(&a), Hull::Left);
        let (i, o) = weighted_shares(&a, Hull::Left);
        assert!((i - 9.0 / 56.0).abs() < 1e-12 && (o - 6.0 / 56.0).abs() < 1e-12, "{i} {o}");
        assert!((envelope_score_of(&a) - 0.053571).abs() < 1e-6);

        let b = occupancy(&board_with(&[(0, 5), (1, 5), (0, 4), (2, 5), (3, 5), (4, 5), (5, 5), (0, 0)]));
        assert_eq!((deviation(&b, Hull::Left), deviation(&b, Hull::Right)), (23, 13));
        assert_eq!(best_hull(&b), Hull::Right);
        assert!((envelope_score_of(&b) - 0.410714).abs() < 1e-6, "{}", envelope_score_of(&b));

        let full_left: Vec<(usize, usize)> =
            (0..6).flat_map(|r| (0..6).map(move |c| (r, c))).filter(|&(r, c)| r + c <= 5).collect();
        let c = occupancy(&board_with(&full_left));
        assert_eq!((deviation(&c, Hull::Left), deviation(&c, Hull::Right)), (0, 18));
        assert!((envelope_score_of(&c) - 1.0).abs() < 1e-12);

        assert_eq!(envelope_score(&board_with(&[])), 0.0, "leeres Brett: H = 0");
    }

    #[test]
    fn hull_total_cost_is_56_for_both_orientations() {
        for hull in [Hull::Left, Hull::Right] {
            let sum: f64 = (0..6).flat_map(|r| (0..6).map(move |c| (r, c)))
                .filter(|&(r, c)| hull.contains(r, c)).map(|(r, _)| row_cost(r)).sum();
            assert_eq!(sum, HULL_TOTAL_COST);
        }
    }

    #[test]
    fn profile_weight_reads_round_index_and_pins_round_five_to_last_entry() {
        let p = ENVELOPE_PROFILE_DEFAULT;
        assert_eq!(profile_weight(&p, 1), 1.0);
        assert_eq!(profile_weight(&p, 2), 0.92);
        assert_eq!(profile_weight(&p, 4), 0.33);
        assert_eq!(profile_weight(&p, 5), 0.0);
        assert_eq!(profile_weight(&p, 7), 0.0, "jenseits Runde 5 wie Runde 5");
        assert_eq!(profile_weight(&p, 0), 1.0, "Runde 0 wie Runde 1");
    }

    /// par.8.2: Nullsumme per Konstruktion (der Aufrufer negiert), `c = 0`
    /// ergibt exakt 0, Runde 5 ergibt exakt 0 (Auflage par.4.1), und der
    /// Betrag saettigt bei `c`.
    #[test]
    fn search_shift_is_zero_when_off_or_in_round_five_and_bounded_by_c() {
        let b0 = board_with(&[(0, 0), (0, 1), (1, 0), (2, 0), (1, 1)]);
        let b1 = board_with(&[(5, 5)]);
        assert_eq!(search_shift(&b0, &b1, 2, 0.0, &ENVELOPE_PROFILE_DEFAULT), 0.0);
        assert_eq!(search_shift(&b0, &b1, 5, 0.2, &ENVELOPE_PROFILE_DEFAULT), 0.0);
        let s = search_shift(&b0, &b1, 1, 0.2, &ENVELOPE_PROFILE_DEFAULT);
        assert!(s > 0.0 && s < 0.2, "{s}");
        let mirrored = search_shift(&b1, &b0, 1, 0.2, &ENVELOPE_PROFILE_DEFAULT);
        assert!((s + mirrored).abs() < 1e-12, "Antisymmetrie beim Brett-Tausch");
    }

    /// par.8.3: ohne Orientierungswechsel ist `dH_kosten` genau die Summe der
    /// Zellenkosten neu gefuellter Zellen innerhalb minus ausserhalb.
    #[test]
    fn tiling_cost_delta_equals_new_cell_costs_inside_minus_outside() {
        let before = board_with(&[(0, 0), (0, 1), (1, 0)]);
        let after_inside = board_with(&[(0, 0), (0, 1), (1, 0), (2, 0)]);
        let after_outside = board_with(&[(0, 0), (0, 1), (1, 0), (5, 5)]);
        assert!((tiling_cost_delta(&before, &after_inside) - 3.0).abs() < 1e-9);
        assert!((tiling_cost_delta(&before, &after_outside) + 6.0).abs() < 1e-9);
        assert_eq!(adjusted_tiling_score(4.0, 0.5, 0.92, 3.0), 4.0 + 0.5 * 0.92 * 3.0);
    }

    /// par.8.7: leere Musterreihen -> `H_proj == H`; eine halb volle Reihe 2
    /// (Farbe Rot, genau eine annehmende Zelle in Zeile 2 innerhalb der linken
    /// Huelle) hebt `H_proj` um `(2/3) * 3 / 56`; eine Reihe ausserhalb senkt.
    #[test]
    fn projected_occupancy_maps_pattern_lines_to_accepting_cells_by_fill_share() {
        let mut board = board_with(&[(0, 0), (0, 1)]);
        assert_eq!(envelope_score_projected(&board), envelope_score(&board));
        // Zeile 2: nur (2, 0) nimmt Rot an (Normal-Farbe), alle anderen Blau.
        for c in 0..6 {
            let sp = board.dome_grid.get_space_mut(2, c).unwrap();
            sp.space_type = SpaceType::Normal;
            sp.required_color = Some(if c == 0 { crate::tile::TileColor::Rot } else { crate::tile::TileColor::Blau });
        }
        board.pattern_lines[2].color = Some(crate::tile::TileColor::Rot);
        board.pattern_lines[2].tiles = vec![crate::tile::TileColor::Rot; 2];
        let occ = projected_occupancy(&board);
        assert!((occ[2][0] - 2.0 / 3.0).abs() < 1e-12, "{}", occ[2][0]);
        assert_eq!(occ[2][1], 0.0);
        let expect = envelope_score(&board) + (2.0 / 3.0) * 3.0 / 56.0;
        assert!((envelope_score_projected(&board) - expect).abs() < 1e-12);
        // Zweite Reihe (5, vier von sechs Steinen) mit Zielzelle (5, 1), die in
        // KEINER Huelle liegt (5 + 1 > 5 und 5 > 1): senkt um (4/6) * 6 / 56;
        // die Orientierung bleibt LINKS (beide Abweichungen gleich, Gleichstand).
        for c in 0..6 {
            let sp = board.dome_grid.get_space_mut(5, c).unwrap();
            sp.space_type = SpaceType::Normal;
            sp.required_color = Some(if c == 1 { crate::tile::TileColor::Rot } else { crate::tile::TileColor::Blau });
        }
        board.pattern_lines[5].color = Some(crate::tile::TileColor::Rot);
        board.pattern_lines[5].tiles = vec![crate::tile::TileColor::Rot; 4];
        let expect_out = expect - (4.0 / 6.0) * 6.0 / 56.0;
        assert!((envelope_score_projected(&board) - expect_out).abs() < 1e-12, "{}", envelope_score_projected(&board));
    }

    /// par.8.6: der Value-Term zaehlt mit `w_v = 1 - w_e`; ohne Marge 0; bei
    /// `w_val = 0` exakt der par.8.3-Score.
    #[test]
    fn value_term_uses_profile_complement_and_zero_without_margin() {
        let base = adjusted_tiling_score(4.0, 0.5, 0.92, 3.0);
        assert_eq!(adjusted_tiling_score_with_value(4.0, 0.5, 0.92, 3.0, 0.0, Some(10.0)), base);
        assert_eq!(adjusted_tiling_score_with_value(4.0, 0.5, 0.92, 3.0, 1.0, None), base);
        let with = adjusted_tiling_score_with_value(4.0, 0.5, 0.92, 3.0, 1.0, Some(10.0));
        assert!((with - (base + 0.08 * 10.0)).abs() < 1e-12, "{with}");
        assert!(EnvelopeTilingParams::OFF.is_off());
        assert!(!EnvelopeTilingParams { w_val: 0.5, ..EnvelopeTilingParams::OFF }.is_off());
    }
}
