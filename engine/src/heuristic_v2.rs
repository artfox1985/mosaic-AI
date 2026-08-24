//! Heuristik v2: der musterreihen-sichtige Fortschrittsterm.
//!
//! `PREREG_heuristic_v2_long_rows.md`. Nutzer-Vorgabe 2026-08-24: v2 ist ein
//! ZUSAETZLICHER Anker, kein Ersatz. Dieses Modul wird ausschliesslich vom
//! V2-Pfad aufgerufen (`mcts::HeuristikVariante::V2`); der Elo-Anker v1 laeuft
//! byte-identisch weiter.
//!
//! ## Die Luecke, die dieser Term schliesst
//!
//! `mcts::player_total` besteht aus drei Teilen, und keiner davon kann die
//! Reihenwahl in Richtung langer Reihen lenken:
//!
//! | Teil | sieht `pattern_lines`? | Richtung |
//! | --- | --- | --- |
//! | Tiling-Solver-Score | Endstand, nicht Zwischenstand | keine |
//! | `wertung_progress` | **nein**, nur `dome_slots` (`scoring.rs`) | keine: innerhalb einer Runde fuer JEDEN Drafting-Zug gleich |
//! | `projected_unplaceable_penalty` | ja | **gegen** lange Reihen |
//!
//! Die Bewertung enthaelt also einen Grund, lange Musterreihen zu meiden, und
//! keinen, sie zu bauen. Dass weder der Lehrer noch sein Schueler Spalten
//! vollendet (0,098 gegen 0,101 je Partie, gemessen 2026-08-24), ist die
//! direkte Folge.
//!
//! ## Was der Term NICHT ist
//!
//! Kein Laengen-Bonus. `PREREG_long_row_payoff.md` B1 hat genau das versucht
//! (Stufenfunktion 0 auf 1 auf Reihe 5/6) und verloren: die Initiierung stieg
//! hoch signifikant, die Staerke fiel um 14,5 Prozentpunkte, und der Preis
//! stand auf der Strafleiste. Belohnt wird hier **erreichbare Vollendung**,
//! nicht Laenge -- und zwar stetig im Fuellstand, damit der Kredit das
//! FORTFUEHREN lenkt und nicht nur das Anfangen.
//!
//! ## Die vier Bausteine (Nutzer-Entscheid 2026-08-24, alle vier gewaehlt)
//!
//! 1. **Stetig im Fuellstand.** Kredit skaliert mit `(fuellstand/kapazitaet)^2`
//!    -- derselbe Exponent wie im Anker (`wertung_progress`, `.powi(2)`), aus
//!    demselben Grund: er bevorzugt EINE fast fertige Baustelle gegenueber
//!    vielen halbfertigen und verhindert das Verzetteln.
//! 2. **Nur wenn erreichbar.** Eine Reihe, deren Zielfeld auf der Kuppel gar
//!    nicht mehr legbar ist, bekommt nichts -- geprueft ueber dieselben
//!    Kriterien wie `round_end::row_has_open_matching_slot` (offen, nicht
//!    gesperrt, Farbe passt).
//! 3. **Gewichtet nach Spalten-Ertrag.** Nicht "irgendwo eine Fliese mehr",
//!    sondern der MARGINALE Zuwachs an der Spalten-Wertungsplatte, die das
//!    Zielfeld bedienen wuerde. Zielt auf die 21-Zellen-Identitaet: eine volle
//!    Spalte braucht je einen Abschluss JEDER Musterreihe.
//! 4. **Plattenlokal: Spezialfeld freischalten.** Fuellt das Zielfeld die
//!    dritte regulaere Zelle seiner Platte, schaltet das den Spezialfeld-Space
//!    frei: eine zusaetzliche Zelle plus Punkte in Hoehe der Rasterreihe,
//!    plus die vermiedene Strafe. Rund 4 solcher Felder bleiben heute je
//!    Partie ungenutzt -- groesster Einzelposten der Plattenwertung
//!    (-11,94 Punkte gemessen).
//!
//! ## Skala
//!
//! Der Term liefert PUNKTE, wie die anderen Summanden von `player_total`.
//! Keine eigene Normierung, kein eigener Knopf: er ist Teil der Definition
//! von v2, nicht ein Regler an v1. (Lehre aus dem Floor-Shaping-Nenner: eine
//! Skalenkonstante, die niemand begruendet, wird zur Altlast.)

use crate::board::PlayerBoard;
use crate::dome::SpaceType;

/// Wertungsplatten-Id der VERTIKALEN Reihen ("k1"). Ihre Punktformel im Anker
/// ist `(fuellung/6)^2 * 7` je Spalte (`scoring.rs`, Zweig `1`); der marginale
/// Zuwachs unten benutzt exakt dieselbe Formel, damit v2 und die Endwertung
/// nicht auseinanderlaufen.
const K1_VERTIKALE_REIHEN: usize = 1;
/// Wertungsplatten-Id der SPEZIALFELDER. Kostet `-3` je leerem Feld
/// (`scoring.rs`, Zweig `6`).
const K7_SPEZIALFELDER: usize = 6;
const SPALTE_VOLL_PUNKTE: f64 = 7.0;
const SPALTE_ZELLEN: f64 = 6.0;
const STRAFE_LEERES_SPEZIALFELD: f64 = 3.0;

/// Aktuelle Fuellung jeder der sechs Brett-Spalten.
///
/// Spalten-Zuordnung: Slot `(tr, tc)`, Space `si` -> Spalte `2*tc + si%2`.
/// Dieselbe Abbildung wie in `tools/probes/column_build_structural_probe.py`
/// (`spalten_fuellung`), dort gegen die Engine verifiziert.
fn spalten_fuellung(player: &PlayerBoard) -> [u32; 6] {
    let mut fill = [0u32; 6];
    for (_tr, reihe) in player.dome_grid.dome_slots.iter().enumerate() {
        for (tc, slot) in reihe.iter().enumerate() {
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
fn spalten_punkte(fuellung: u32) -> f64 {
    (fuellung as f64 / SPALTE_ZELLEN).powi(2) * SPALTE_VOLL_PUNKTE
}

/// Was das Belegen GENAU DIESES Feldes zusaetzlich einbraechte, in Punkten.
///
/// Zwei Posten, beide nur wenn die zugehoerige Wertungsplatte aktiv ist:
/// der marginale Spalten-Zuwachs und die Freischaltung eines Spezialfeldes.
fn ertrag_des_feldes(
    player: &PlayerBoard,
    tile_ids: &[usize],
    fuellung: &[u32; 6],
    tr: usize,
    tc: usize,
    si: usize,
) -> f64 {
    let mut ertrag = 0.0;

    if tile_ids.contains(&K1_VERTIKALE_REIHEN) {
        let spalte = 2 * tc + si % 2;
        let jetzt = fuellung[spalte];
        // Marginal, nicht absolut: der bereits erreichte Fuellstand steht
        // schon in `wertung_progress` und darf hier nicht doppelt zaehlen.
        ertrag += spalten_punkte(jetzt + 1) - spalten_punkte(jetzt);
    }

    // Plattenlokal: waere dieses Feld die letzte fehlende REGULAERE Zelle,
    // schaltet es den Spezialfeld-Space frei (`dome.rs::try_unlock_special`:
    // alle anderen Spaces ausser dem Special muessen gefuellt sein).
    let Some(slot) = player.dome_grid.dome_slots[tr][tc].as_ref() else {
        return ertrag;
    };
    let Some(sp_idx) = slot.special_space_idx() else {
        return ertrag;
    };
    if !slot.spaces[sp_idx].is_locked {
        return ertrag; // schon frei, kein zusaetzlicher Ertrag
    }
    let rest_offen = slot
        .spaces
        .iter()
        .enumerate()
        .filter(|(i, s)| *i != sp_idx && *i != si && !s.is_filled())
        .count();
    if rest_offen > 0 {
        return ertrag; // dieses Feld schaltet noch nichts frei
    }
    // Die Spezialfliese zahlt Punkte in Hoehe ihrer RASTERREIHE (1..6):
    // Rasterreihe = 2*tr + si/2, 0-indexiert, also +1 fuer den Punktwert.
    ertrag += (2 * tr + sp_idx / 2) as f64 + 1.0;
    if tile_ids.contains(&K7_SPEZIALFELDER) {
        ertrag += STRAFE_LEERES_SPEZIALFELD; // vermiedene Strafe
    }
    ertrag
}

/// Der v2-Zusatzterm: Kredit fuer ERREICHBARE Vollendung angefangener
/// Musterreihen, stetig im Fuellstand.
///
/// Volle Reihen bekommen nichts: sie liegen bereits im Tiling-Solver-Score.
/// Leere Reihen bekommen nichts: es gibt keinen Fortschritt zu belohnen (und
/// ein Anfangs-Bonus ist genau der Fehler, an dem B1 gescheitert ist).
pub fn row_completion_progress(player: &PlayerBoard, tile_ids: &[usize]) -> f64 {
    let fuellung = spalten_fuellung(player);
    let mut summe = 0.0;

    for (r, reihe) in player.pattern_lines.iter().enumerate() {
        let fuell = reihe.tiles.len();
        let kapazitaet = r + 1;
        if fuell == 0 || fuell >= kapazitaet {
            continue;
        }
        let Some(farbe) = reihe.color else { continue };

        // Musterreihe r speist Kuppel-Reihe r/2, Teilreihe r%2 (Space-Indizes
        // 2*(r%2) und +1) -- dieselbe Zuordnung, die
        // `round_end::validate_tiling_action` erzwingt.
        let tr = r / 2;
        let valid_si = [(r % 2) * 2, (r % 2) * 2 + 1];

        // Bester erreichbarer Zielplatz. Max statt Summe: die Reihe wird
        // genau EINE Zelle belegen, nicht alle in Frage kommenden.
        let mut bester = 0.0f64;
        let mut erreichbar = false;
        for tc in 0..3 {
            let Some(slot) = player.dome_grid.dome_slots[tr][tc].as_ref() else {
                continue;
            };
            for &si in &valid_si {
                let sp = &slot.spaces[si];
                if sp.is_filled() || sp.is_locked || !sp.accepts(farbe) {
                    continue;
                }
                erreichbar = true;
                let e = ertrag_des_feldes(player, tile_ids, &fuellung, tr, tc, si);
                if e > bester {
                    bester = e;
                }
            }
        }
        if !erreichbar {
            continue; // Baustein 2: unerreichbare Reihe bekommt nichts
        }
        // Baustein 1: stetig im Fuellstand, Exponent wie im Anker.
        let fortschritt = (fuell as f64 / kapazitaet as f64).powi(2);
        summe += fortschritt * bester;
    }
    summe
}

/// Nur zur Diagnose: sind ueberhaupt Spezialfeld-Spaces auf dem Brett, die
/// noch gesperrt sind? Wird von keiner Bewertung gelesen.
pub fn gesperrte_spezialfelder(player: &PlayerBoard) -> usize {
    player
        .dome_grid
        .dome_slots
        .iter()
        .flatten()
        .flatten()
        .filter(|slot| {
            slot.spaces
                .iter()
                .any(|s| s.space_type == SpaceType::Special && s.is_locked)
        })
        .count()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dome::build_dome_tile_pool;
    use crate::tile::TileColor::*;

    /// Der Term muss auf einer PLAUSIBLEN Stellung STRIKT POSITIV sein.
    ///
    /// Ohne diesen Test waere ein "v2 bewegt nichts"-Befund nicht von einem
    /// Term zu unterscheiden, der schlicht immer 0 liefert -- also von einem
    /// Bug. Genau dieser Zweifel kam bei der ersten Abnahme auf.
    #[test]
    fn term_ist_positiv_wenn_eine_reihe_erreichbar_angefangen_ist() {
        let mut p = crate::board::PlayerBoard::new(0, "P");
        // Platte 0 = [Gelb, Schwarz, Tuerkis, Special] in Slot (0,0).
        // Musterreihe 1 (Index 0) speist Slot-Reihe 0, Space 0/1.
        let tile = build_dome_tile_pool()[0].clone();
        p.dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        // Musterreihe 2 (Index 1, Kapazitaet 2) mit EINER Fliese anfangen --
        // sie speist Slot-Reihe 0, Space 2/3.
        p.pattern_lines[1].add_tiles(&[Tuerkis]);
        assert_eq!(p.pattern_lines[1].tiles.len(), 1);

        // k1 aktiv, damit der Spalten-Posten ueberhaupt zaehlt.
        let wert = row_completion_progress(&p, &[K1_VERTIKALE_REIHEN]);
        assert!(
            wert > 0.0,
            "Term muss auf einer angefangenen, erreichbaren Reihe positiv sein, war {wert}"
        );
    }

    /// Gegenprobe: eine LEERE Reihe bekommt nichts. Ein Anfangs-Bonus ist
    /// genau der Fehler, an dem `PREREG_long_row_payoff.md` B1 gescheitert
    /// ist -- der Term darf ihn nicht durch die Hintertuer wieder einfuehren.
    #[test]
    fn leere_reihe_bekommt_nichts() {
        let mut p = crate::board::PlayerBoard::new(0, "P");
        let tile = build_dome_tile_pool()[0].clone();
        p.dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        assert_eq!(row_completion_progress(&p, &[K1_VERTIKALE_REIHEN]), 0.0);
    }

    /// Ohne Kuppelplatte gibt es kein erreichbares Zielfeld -- Baustein 2.
    #[test]
    fn unerreichbare_reihe_bekommt_nichts() {
        let mut p = crate::board::PlayerBoard::new(0, "P");
        p.pattern_lines[1].add_tiles(&[Tuerkis]);
        assert_eq!(row_completion_progress(&p, &[K1_VERTIKALE_REIHEN]), 0.0);
    }
}
