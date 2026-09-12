//! Heuristik hv3: die Bewertungsterme des Huellen-Lehrers, auf dem HEUTIGEN Motor.
//!
//! ## Was hv3 ist
//!
//! hv3 = hv2 (frueher `v2huelle`, `mcts::HeuristikVariante::V2Huelle`) auf dem
//! aktuellen Quellstand. Das eingefrorene Artefakt
//! `models/frozen_heuristics/hv2_generator` spielt hv2 auf seinem eigenen Wheel
//! vom 2026-08-26 und bleibt unberuehrt; hv3 ist dasselbe Rezept auf dem
//! heutigen Motor, damit die seitdem gebauten Korrektheits-Fixes darin wirken.
//!
//! **Der Unterschied zu hv2, namentlich:** der Phantom-Abzug A2
//! (`provocation.rs::subtract_phantom_tiles`, Commit 2a0cf4b,
//! `PREREG_code_cleanup_closeout.md` par.3 Punkt 2). Er wirkt NICHT in diesem
//! Modul -- die beiden Terme hier lesen den Restvorrat gar nicht --, sondern
//! ausschliesslich im ROUTING (`plate_builder_v3.rs`, siehe dortige Moduldoku
//! mit den beiden Fundstellen). Dieses Modul ist gegenueber `heuristic_v2.rs`
//! Zeile fuer Zeile dasselbe Verhalten, nur mit englischen Bezeichnern.
//!
//! Wieder aufgenommen aus `engine/src/heuristic_v2.rs` (geloescht mit Commit
//! 65b48af, "B4a: v2 verlaesst den Quellstand"). NICHT mit portiert, weil
//! hv2/V2Huelle sie nie gelesen hat: `row_completion_progress_capped`
//! (nur V2HuelleCap, par.16), `triangle_deviation`/`DREIECK_GEWICHT` und
//! `locked_special_fields` (in 65b48af^ ohne einen einzigen Aufrufer, geprueft
//! per git grep ueber engine/src und tools).
//!
//! ## Die Luecke, die der Fortschrittsterm schliesst
//!
//! `mcts::player_total` besteht aus drei Teilen, und keiner davon kann die
//! Reihenwahl in Richtung langer Musterreihen lenken:
//!
//! | Teil | sieht `pattern_lines`? | Richtung |
//! | --- | --- | --- |
//! | Tiling-Solver-Score | Endstand, nicht Zwischenstand | keine |
//! | `scoring_progress` | **nein**, nur `dome_slots` (`scoring.rs`) | keine |
//! | `projected_unplaceable_penalty` | ja | **gegen** lange Musterreihen |
//!
//! Die Bewertung enthaelt also einen Grund, lange Musterreihen zu meiden, und
//! keinen, sie zu bauen.
//!
//! ## Was der Term NICHT ist
//!
//! Kein Laengen-Bonus. `PREREG_long_row_payoff.md` B1 hat genau das versucht
//! (Stufenfunktion 0 auf 1 auf Musterreihe 5/6) und verloren: die Initiierung
//! stieg hoch signifikant, die Staerke fiel um 14,5 Prozentpunkte, und der
//! Preis stand auf der Strafleiste. Belohnt wird hier **erreichbare
//! Vollendung**, nicht Laenge -- und zwar stetig im Fuellstand, damit der
//! Kredit das FORTFUEHREN lenkt und nicht nur das Anfangen.
//!
//! ## Die vier Bausteine (Nutzer-Entscheid 2026-08-24, alle vier gewaehlt)
//!
//! 1. **Stetig im Fuellstand, SAETTIGEND**: ein hoher Kredit fuer die unteren
//!    Musterreihen, dessen ZUWACHS schnell einbricht, sobald die erste Fliese
//!    liegt. Formel `A(r) * sqrt(fill/capacity)`. Die erste Fassung war KONVEX
//!    (`(fill/capacity)^2`) und ist daran gescheitert: der gemessene Engpass
//!    sitzt im ENTSCHLUSS, eine lange Musterreihe ueberhaupt anzufangen (Netz
//!    11,5 Prozent gegen Heuristik 25,2 Prozent).
//! 2. **Nur wenn erreichbar.** Eine Musterreihe, deren Zielzelle auf der
//!    Kuppel gar nicht mehr legbar ist, bekommt nichts -- geprueft ueber
//!    dieselben Kriterien wie `round_end::row_has_open_matching_slot`.
//! 3. **Gewichtet nach Spalten-Ertrag**: der MARGINALE Zuwachs an der
//!    Spalten-Wertungsplatte, die die Zielzelle bedienen wuerde.
//! 4. **Plattenlokal: Spezialfeld freischalten.** Fuellt die Zielzelle die
//!    dritte regulaere Zelle ihrer Platte, schaltet das den Spezialfeld-Space
//!    frei: eine zusaetzliche Zelle plus Punkte in Hoehe der Rasterreihe, plus
//!    die vermiedene Strafe.
//!
//! ## Skala
//!
//! Der Term liefert PUNKTE, wie die anderen Summanden von `player_total`.
//! Keine eigene Normierung, kein eigener Knopf: er ist Teil der Definition von
//! hv3, nicht ein Regler an hv1.

use crate::board::PlayerBoard;

/// Wertungsplatten-Id der VERTIKALEN Linien ("k1"). Ihre Punktformel im Anker
/// ist `(fill/6)^2 * 7` je Spalte (`scoring.rs`, Zweig `1`); der marginale
/// Zuwachs unten benutzt exakt dieselbe Formel, damit hv3 und die Endwertung
/// nicht auseinanderlaufen.
const K1_VERTICAL_LINES: usize = 1;
/// Wertungsplatten-Id der HORIZONTALEN Linien (`scoring.rs`, Zweig `0`,
/// 3 Punkte je voller Rasterzeile).
const K0_HORIZONTAL_LINES: usize = 0;
const FULL_GRID_ROW_POINTS: f64 = 3.0;

/// **HANDGESETZT** (Nutzer-Vorgabe 2026-08-24: "das ist die Heuristik, da
/// muessen wir handcraften"). Kredit-Hoehe je Musterreihe, Index 0..5 fuer
/// Musterreihe 1..6, in PUNKTEN.
///
/// Kurze Musterreihen bekommen nichts: sie werden ohnehin praktisch jede Runde
/// abgeschlossen. Der Kredit steigt nach unten, weil dort die Luecke sitzt:
/// gemessen 1,13 und 0,74 Abschluesse je Partie in Musterreihe 5 und 6, gegen
/// 2,50 und 2,20 bei einem Spieler, der das Spiel beherrscht.
///
/// Die Zahlen sind eine SETZUNG, keine Ableitung -- und das ist Absicht. Eine
/// aus dem heutigen Self-Play abgeleitete Groesse wuerde die Schwaeche
/// festschreiben, die sie beheben soll (dieselbe Regel, an der schon
/// `MARGIN_SCALE` und `FLOOR_SHAPING_SCALE` haengen).
const ROW_CREDIT: [f64; 6] = [0.0, 0.0, 0.0, 1.0, 3.0, 5.0];
/// Wertungsplatten-Id der SPEZIALFELDER. Kostet `-3` je leerem Feld
/// (`scoring.rs`, Zweig `6`).
const K7_SPECIAL_SPACES: usize = 6;
const FULL_COLUMN_POINTS: f64 = 7.0;
const COLUMN_CELLS: f64 = 6.0;
const EMPTY_SPECIAL_PENALTY: f64 = 3.0;

/// Aktuelle Fuellung jeder der sechs Rasterspalten.
///
/// Zuordnung: Slot `(tr, tc)`, Space `si` -> Rasterspalte `2*tc + si%2`.
/// Dieselbe Abbildung wie in `tools/probes/column_build_structural_probe.py`
/// (`column_fill`), dort gegen die Engine verifiziert.
fn column_fill(player: &PlayerBoard) -> [u32; 6] {
    let mut fill = [0u32; 6];
    for grid_row in player.dome_grid.dome_slots.iter() {
        for (tc, slot) in grid_row.iter().enumerate() {
            let Some(slot) = slot else { continue };
            for (si, sp) in slot.spaces.iter().enumerate() {
                if sp.is_filled() {
                    fill[2 * tc + si % 2] += 1;
                }
            }
        }
    }
    fill
}

/// Punktwert der Spalten-Platte bei gegebener Fuellung, exakt nach der
/// Anker-Formel.
fn column_points(fill: u32) -> f64 {
    (fill as f64 / COLUMN_CELLS).powi(2) * FULL_COLUMN_POINTS
}

/// Was das Belegen GENAU DIESER Zelle zusaetzlich einbraechte, in Punkten.
///
/// Zwei Posten, beide nur wenn die zugehoerige Wertungsplatte aktiv ist:
/// der marginale Spalten-Zuwachs und die Freischaltung eines Spezialfeldes.
fn cell_gain(
    player: &PlayerBoard,
    tile_ids: &[usize],
    fill: &[u32; 6],
    tr: usize,
    tc: usize,
    si: usize,
) -> f64 {
    let mut gain = 0.0;

    if tile_ids.contains(&K1_VERTICAL_LINES) {
        let column = 2 * tc + si % 2;
        let now = fill[column];
        // Marginal, nicht absolut: der bereits erreichte Fuellstand steht
        // schon in `scoring_progress` und darf hier nicht doppelt zaehlen.
        gain += column_points(now + 1) - column_points(now);
    }

    // Plattenlokal: waere diese Zelle die letzte fehlende REGULAERE Zelle,
    // schaltet sie den Spezialfeld-Space frei (`dome.rs::try_unlock_special`:
    // alle anderen Spaces ausser dem Special muessen gefuellt sein).
    let Some(slot) = player.dome_grid.dome_slots[tr][tc].as_ref() else {
        return gain;
    };
    let Some(sp_idx) = slot.special_space_idx() else {
        return gain;
    };
    if !slot.spaces[sp_idx].is_locked {
        return gain; // schon frei, kein zusaetzlicher Ertrag
    }
    let still_open = slot
        .spaces
        .iter()
        .enumerate()
        .filter(|(i, s)| *i != sp_idx && *i != si && !s.is_filled())
        .count();
    if still_open > 0 {
        return gain; // diese Zelle schaltet noch nichts frei
    }
    // Die Spezialfliese zahlt Punkte in Hoehe ihrer RASTERREIHE (1..6):
    // Rasterreihe = 2*tr + si/2, 0-indexiert, also +1 fuer den Punktwert.
    gain += (2 * tr + sp_idx / 2) as f64 + 1.0;
    if tile_ids.contains(&K7_SPECIAL_SPACES) {
        gain += EMPTY_SPECIAL_PENALTY; // vermiedene Strafe
    }
    gain
}

/// Der hv3-Zusatzterm: Kredit fuer ERREICHBARE Vollendung angefangener
/// Musterreihen, stetig im Fuellstand.
///
/// Volle Musterreihen bekommen nichts: sie liegen bereits im
/// Tiling-Solver-Score. Leere bekommen nichts: es gibt keinen Fortschritt zu
/// belohnen (und ein Anfangs-Bonus ist genau der Fehler, an dem
/// `PREREG_long_row_payoff.md` B1 gescheitert ist).
pub fn row_completion_progress(player: &PlayerBoard, tile_ids: &[usize]) -> f64 {
    let fill = column_fill(player);
    let mut total = 0.0;

    for (r, line) in player.pattern_lines.iter().enumerate() {
        let filled = line.tiles.len();
        let capacity = r + 1;
        if filled == 0 || filled >= capacity {
            continue;
        }
        let Some(color) = line.color else { continue };

        // Musterreihe r speist Kuppel-Slotreihe r/2, Teilreihe r%2 (Space-
        // Indizes 2*(r%2) und +1) -- dieselbe Zuordnung, die
        // `round_end::validate_tiling_action` erzwingt.
        let tr = r / 2;
        let valid_si = [(r % 2) * 2, (r % 2) * 2 + 1];

        // Bester erreichbarer Zielplatz. Max statt Summe: die Musterreihe
        // belegt genau EINE Zelle, nicht alle in Frage kommenden.
        let mut best_gain = 0.0f64;
        let mut reachable = false;
        for tc in 0..3 {
            let Some(slot) = player.dome_grid.dome_slots[tr][tc].as_ref() else {
                continue;
            };
            for &si in &valid_si {
                let sp = &slot.spaces[si];
                if sp.is_filled() || sp.is_locked || !sp.accepts(color) {
                    continue;
                }
                reachable = true;
                let g = cell_gain(player, tile_ids, &fill, tr, tc, si);
                if g > best_gain {
                    best_gain = g;
                }
            }
        }
        if !reachable {
            continue; // Baustein 2: unerreichbare Musterreihe bekommt nichts
        }
        // Baustein 1: SAETTIGEND. Der Kredit steht fast vollstaendig schon
        // nach der ersten Fliese, der Zuwachs bricht danach ein.
        let saturation = (filled as f64 / capacity as f64).sqrt();
        // Der handgesetzte Kredit ist der tragende Posten; der Zellen-Ertrag
        // (Spalte, Spezialfeld) kommt additiv obendrauf, weil er
        // stellungsabhaengig ist und in der ersten Fassung als ALLEINIGER
        // Traeger zu klein war (0,97 bis 1,75 Punkte, und nur bei aktivem k1).
        total += saturation * (ROW_CREDIT[r] + best_gain);
    }
    total
}

/// Wert der BESTEN Rasterspalte und der besten oberen Rasterzeile --
/// **unabhaengig davon, ob die zugehoerige Wertungsplatte aktiv ist**.
///
/// Anlass (gemessen 2026-08-24): der Huellen-Lehrer baut 0,562 volle Spalten je
/// Partie, wenn k1 aktiv ist, aber nur 0,229 wenn nicht. Der Grund ist
/// strukturell -- `scoring_progress` kreditiert Spaltenfuellung ausschliesslich
/// bei aktivem k1 (`scoring.rs`, Zweig `1`), und k1 liegt nur in rund 40
/// Prozent der Partien an. In den uebrigen 60 Prozent arbeitet die Suche also
/// GEGEN das Routing statt mit ihm.
///
/// Fuer hv3 ist das L (eine Spalte plus eine obere Rasterzeile) das ZIEL, nicht
/// die Wertungsplatte. Der Term macht es deshalb auch dann wertvoll, wenn es
/// nichts einbringt -- das ist der bewusst in Kauf genommene Punktepreis
/// (Nutzer-Entscheid 2026-08-24: "solange er Spalten baut ... ist es ok").
///
/// **Keine Doppelzaehlung:** ist die Platte aktiv, kreditiert
/// `scoring_progress` sie bereits, und dieser Term liefert fuer sie 0. Er
/// springt nur ein, wo der Bestand schweigt.
///
/// **MAX statt Summe:** `scoring_progress` summiert ueber alle sechs Spalten
/// und belohnt damit Breite. Eine volle Spalte braucht aber Fokus -- die
/// 21-Zellen-Identitaet haengt am Minimum ueber die Rasterzeilen, nicht an der
/// Summe.
///
/// Billig gehalten: reines Auszaehlen der 36 Zellen, kein Kandidatenvergleich.
/// Der Term laeuft an JEDEM Suchblatt.
pub fn plate_independent_l_value(player: &PlayerBoard, tile_ids: &[usize]) -> f64 {
    let mut columns = [0u32; 6];
    let mut grid_rows = [0u32; 6];
    for (tr, grid_row) in player.dome_grid.dome_slots.iter().enumerate() {
        for (tc, slot) in grid_row.iter().enumerate() {
            let Some(slot) = slot else { continue };
            for (si, sp) in slot.spaces.iter().enumerate() {
                if sp.is_filled() {
                    columns[2 * tc + si % 2] += 1;
                    grid_rows[2 * tr + si / 2] += 1;
                }
            }
        }
    }
    let mut value = 0.0;
    if !tile_ids.contains(&K1_VERTICAL_LINES) {
        let best = columns.iter().copied().max().unwrap_or(0);
        value += column_points(best);
    }
    if !tile_ids.contains(&K0_HORIZONTAL_LINES) {
        // Nur die obersten zwei Rasterzeilen: weiter unten ist eine volle
        // Rasterzeile nicht erreichbar (eine Musterreihe schliesst hoechstens
        // einmal je Runde ab, fuenf Steine fuer sechs Zellen).
        let best = grid_rows[..2].iter().copied().max().unwrap_or(0);
        value += (best as f64 / COLUMN_CELLS).powi(2) * FULL_GRID_ROW_POINTS;
    }
    value
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dome::build_dome_tile_pool;
    use crate::tile::TileColor::*;

    /// Der Term muss auf einer PLAUSIBLEN Stellung STRIKT POSITIV sein.
    ///
    /// Ohne diesen Test waere ein "hv3 bewegt nichts"-Befund nicht von einem
    /// Term zu unterscheiden, der schlicht immer 0 liefert -- also von einem
    /// Bug. Genau dieser Zweifel kam bei der ersten Abnahme von hv2 auf.
    #[test]
    fn term_is_positive_when_a_reachable_row_is_started() {
        let mut p = crate::board::PlayerBoard::new(0, "P");
        // Platte 0 = [Gelb, Schwarz, Tuerkis, Special] in Slot (0,0).
        // Musterreihe 1 (Index 0) speist Slotreihe 0, Space 0/1.
        let tile = build_dome_tile_pool()[0].clone();
        p.dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        // Musterreihe 2 (Index 1, Kapazitaet 2) mit EINER Fliese anfangen --
        // sie speist Slotreihe 0, Space 2/3.
        p.pattern_lines[1].add_tiles(&[Tuerkis]);
        assert_eq!(p.pattern_lines[1].tiles.len(), 1);

        // k1 aktiv, damit der Spalten-Posten ueberhaupt zaehlt.
        let value = row_completion_progress(&p, &[K1_VERTICAL_LINES]);
        assert!(
            value > 0.0,
            "Term muss auf einer angefangenen, erreichbaren Musterreihe positiv sein, war {value}"
        );
    }

    /// Gegenprobe: eine LEERE Musterreihe bekommt nichts. Ein Anfangs-Bonus ist
    /// genau der Fehler, an dem `PREREG_long_row_payoff.md` B1 gescheitert ist.
    #[test]
    fn empty_row_gets_nothing() {
        let mut p = crate::board::PlayerBoard::new(0, "P");
        let tile = build_dome_tile_pool()[0].clone();
        p.dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        assert_eq!(row_completion_progress(&p, &[K1_VERTICAL_LINES]), 0.0);
    }

    /// Ohne Kuppelplatte gibt es keine erreichbare Zielzelle -- Baustein 2.
    #[test]
    fn unreachable_row_gets_nothing() {
        let mut p = crate::board::PlayerBoard::new(0, "P");
        p.pattern_lines[1].add_tiles(&[Tuerkis]);
        assert_eq!(row_completion_progress(&p, &[K1_VERTICAL_LINES]), 0.0);
    }

    /// Der L-Term springt NUR ein, wo die Wertungsplatte schweigt -- sonst
    /// zaehlte derselbe Fortschritt zweimal.
    #[test]
    fn l_value_is_zero_when_both_plates_are_active() {
        let mut p = crate::board::PlayerBoard::new(0, "P");
        let tile = build_dome_tile_pool()[0].clone();
        p.dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        p.dome_grid.place_tile(0, 0, Gelb).unwrap();
        assert_eq!(
            plate_independent_l_value(&p, &[K0_HORIZONTAL_LINES, K1_VERTICAL_LINES]),
            0.0
        );
        assert!(plate_independent_l_value(&p, &[]) > 0.0);
    }
}
