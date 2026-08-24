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
//! | `scoring_progress` | **nein**, nur `dome_slots` (`scoring.rs`) | keine: innerhalb einer Runde fuer JEDEN Drafting-Zug gleich |
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
//! 1. **Stetig im Fuellstand, SAETTIGEND** (Nutzer-Vorgabe 2026-08-24, zweite
//!    Fassung): ein hoher Kredit fuer die unteren Reihen, dessen ZUWACHS
//!    schnell einbricht, sobald die erste Fliese liegt. Formel
//!    `A(r) * sqrt(fuellstand/kapazitaet)`.
//!
//!    **Die erste Fassung hatte die entgegengesetzte Form** und ist daran
//!    gescheitert: `(fuellstand/kapazitaet)^2` ist KONVEX, der Anreiz waechst
//!    mit dem Fuellstand und zielt aufs Fortfuehren. Der gemessene Engpass
//!    sitzt aber im ENTSCHLUSS, eine lange Reihe ueberhaupt anzufangen
//!    (Netz 11,5 Prozent gegen Heuristik 25,2 Prozent). Konkav setzt den
//!    Anreiz dorthin und nimmt sich danach zurueck: bei Kapazitaet 6 bringt
//!    die erste Fliese 0,41 des Kredits, die zweite noch 0,17, die letzte
//!    0,09.
//!
//!    **Unterschied zu B1, damit der Fehler sich nicht wiederholt:** B1 war
//!    eine STUFE 0 auf 1, die nach dem Start dauerhaft stehen blieb -- kein
//!    Zug zum Weitermachen, keine Vorsicht, Ergebnis waren angefangene
//!    Ruinen. Die saettigende Form haelt das NIVEAU (die Reihe aufzugeben
//!    kostet den ganzen Kredit) und gibt fuers Weiterfuellen nur wenig --
//!    `projected_unplaceable_penalty` bestraft das Liegenlassen zusaetzlich.
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
/// Wertungsplatten-Id der HORIZONTALEN Reihen (`scoring.rs`, Zweig `0`,
/// 3 Punkte je voller Zeile).
const K0_HORIZONTALE_REIHEN: usize = 0;
const ZEILE_VOLL_PUNKTE: f64 = 3.0;

/// **HANDGESETZT** (Nutzer-Vorgabe 2026-08-24: "das ist die Heuristik, da
/// muessen wir handcraften"). Kredit-Hoehe je Musterreihe, Index 0..5 fuer
/// Musterreihe 1..6, in PUNKTEN.
///
/// Kurze Reihen bekommen nichts: sie werden ohnehin praktisch jede Runde
/// abgeschlossen (Rasterreihe 1 und 2 liegen bei rund 5 von 5 moeglichen
/// Abschluessen). Der Kredit steigt nach unten, weil dort die Luecke sitzt:
/// gemessen 1,13 und 0,74 Abschluesse je Partie in Reihe 5 und 6, gegen
/// 2,50 und 2,20 bei einem Spieler, der das Spiel beherrscht.
///
/// Die Zahlen sind eine SETZUNG, keine Ableitung -- und das ist Absicht.
/// Eine aus dem heutigen Self-Play abgeleitete Groesse wuerde die Schwaeche
/// festschreiben, die sie beheben soll (dieselbe Regel, an der schon
/// `MARGIN_SCALE` und `FLOOR_SHAPING_SCALE` haengen). Groessenordnung: eine
/// zusaetzliche Vollendung in Reihe 6 traegt eine Spalte (7 Punkte bei
/// aktivem k1) plus Platzierungspunkte, 5 Punkte Kredit sind also die
/// gleiche Groessenordnung wie der Ertrag und nicht ein Vielfaches davon.
const REIHEN_KREDIT: [f64; 6] = [0.0, 0.0, 0.0, 1.0, 3.0, 5.0];
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
/// (`column_fill`), dort gegen die Engine verifiziert.
fn column_fill(player: &PlayerBoard) -> [u32; 6] {
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
fn column_points(fuellung: u32) -> f64 {
    (fuellung as f64 / SPALTE_ZELLEN).powi(2) * SPALTE_VOLL_PUNKTE
}

/// Was das Belegen GENAU DIESES Feldes zusaetzlich einbraechte, in Punkten.
///
/// Zwei Posten, beide nur wenn die zugehoerige Wertungsplatte aktiv ist:
/// der marginale Spalten-Zuwachs und die Freischaltung eines Spezialfeldes.
fn cell_yield(
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
        // schon in `scoring_progress` und darf hier nicht doppelt zaehlen.
        ertrag += column_points(jetzt + 1) - column_points(jetzt);
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
/// Wert der BESTEN Spalte und der besten oberen Zeile -- **unabhaengig davon,
/// ob die zugehoerige Wertungsplatte aktiv ist**.
///
/// Anlass (gemessen 2026-08-24): v2 baut 0,562 volle Spalten je Partie, wenn
/// k1 aktiv ist, aber nur 0,229 wenn nicht. Der Grund ist strukturell --
/// `scoring_progress` kreditiert Spaltenfuellung ausschliesslich bei aktivem
/// k1 (`scoring.rs`, Zweig `1`), und k1 liegt nur in rund 40 Prozent der
/// Partien an. In den uebrigen 60 Prozent arbeitet die Suche also GEGEN das
/// Routing statt mit ihm.
///
/// Fuer v2 ist das L (eine Spalte plus eine obere Zeile) das ZIEL, nicht die
/// Wertungsplatte. Der Term macht es deshalb auch dann wertvoll, wenn es
/// nichts einbringt -- das ist der bewusst in Kauf genommene Punktepreis
/// (Nutzer-Entscheid 2026-08-24: "solange er Spalten baut ... ist es ok").
///
/// **Keine Doppelzaehlung:** ist die Platte aktiv, kreditiert
/// `scoring_progress` sie bereits, und dieser Term liefert fuer sie 0. Er
/// springt nur ein, wo der Bestand schweigt.
///
/// **MAX statt Summe:** `scoring_progress` summiert ueber alle sechs Spalten
/// und belohnt damit Breite. Eine volle Spalte braucht aber Fokus -- die
/// 21-Zellen-Identitaet haengt am Minimum ueber die Rasterzeilen, nicht an
/// der Summe. Das Maximum lenkt auf die Spalte, die ohnehin am weitesten ist.
///
/// Billig gehalten: reines Auszaehlen der 36 Zellen, kein Kandidaten-Kosten-
/// vergleich. Der Term laeuft an JEDEM Suchblatt.
pub fn plate_independent_l_value(player: &PlayerBoard, tile_ids: &[usize]) -> f64 {
    let mut spalten = [0u32; 6];
    let mut zeilen = [0u32; 6];
    for (tr, reihe) in player.dome_grid.dome_slots.iter().enumerate() {
        for (tc, slot) in reihe.iter().enumerate() {
            let Some(slot) = slot else { continue };
            for (si, sp) in slot.spaces.iter().enumerate() {
                if sp.is_filled() {
                    spalten[2 * tc + si % 2] += 1;
                    zeilen[2 * tr + si / 2] += 1;
                }
            }
        }
    }
    let mut wert = 0.0;
    if !tile_ids.contains(&K1_VERTIKALE_REIHEN) {
        let beste = spalten.iter().copied().max().unwrap_or(0);
        wert += column_points(beste);
    }
    if !tile_ids.contains(&K0_HORIZONTALE_REIHEN) {
        // Nur die obersten zwei Rasterzeilen: weiter unten ist eine volle
        // Zeile nicht erreichbar (Musterreihe schliesst hoechstens einmal je
        // Runde ab, fuenf Steine fuer sechs Zellen), siehe
        // `plate_builder::ZEILEN_ZIEL_MAX`.
        let beste = zeilen[..2].iter().copied().max().unwrap_or(0);
        wert += (beste as f64 / SPALTE_ZELLEN).powi(2) * ZEILE_VOLL_PUNKTE;
    }
    wert
}

pub fn row_completion_progress(player: &PlayerBoard, tile_ids: &[usize]) -> f64 {
    let fuellung = column_fill(player);
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
                let e = cell_yield(player, tile_ids, &fuellung, tr, tc, si);
                if e > bester {
                    bester = e;
                }
            }
        }
        if !erreichbar {
            continue; // Baustein 2: unerreichbare Reihe bekommt nichts
        }
        // Baustein 1: SAETTIGEND. Der Kredit steht fast vollstaendig schon
        // nach der ersten Fliese, der Zuwachs bricht danach ein.
        let saettigung = (fuell as f64 / kapazitaet as f64).sqrt();
        // Der handgesetzte Reihen-Kredit ist der tragende Posten; der
        // Feld-Ertrag (Spalte, Spezialfeld) kommt additiv obendrauf, weil er
        // stellungsabhaengig ist und in der ersten Fassung als ALLEINIGER
        // Traeger zu klein war (0,97 bis 1,75 Punkte, und nur bei aktivem k1).
        summe += saettigung * (REIHEN_KREDIT[r] + bester);
    }
    summe
}

/// Nur zur Diagnose: sind ueberhaupt Spezialfeld-Spaces auf dem Brett, die
/// noch gesperrt sind? Wird von keiner Bewertung gelesen.
pub fn locked_special_fields(player: &PlayerBoard) -> usize {
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
    fn term_is_positive_when_a_reachable_row_is_started() {
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
    fn empty_row_gets_nothing() {
        let mut p = crate::board::PlayerBoard::new(0, "P");
        let tile = build_dome_tile_pool()[0].clone();
        p.dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        assert_eq!(row_completion_progress(&p, &[K1_VERTIKALE_REIHEN]), 0.0);
    }

    /// Ohne Kuppelplatte gibt es kein erreichbares Zielfeld -- Baustein 2.
    #[test]
    fn unreachable_row_gets_nothing() {
        let mut p = crate::board::PlayerBoard::new(0, "P");
        p.pattern_lines[1].add_tiles(&[Tuerkis]);
        assert_eq!(row_completion_progress(&p, &[K1_VERTIKALE_REIHEN]), 0.0);
    }
}

// ── Dreiecks-Abweichung (Nutzer-Formulierung 2026-08-24) ────────────────────

/// Gewicht der Dreiecks-Abweichung in PUNKTEN je Zelle.
///
/// Eine Abweichungs-Einheit ist genau eine Zelle. Gemessen bringt eine
/// Platzierung 2,3 bis 4,3 Punkte (Server-Logs, Mensch wie KI), `1.0` ist
/// also bewusst KONSERVATIV: der Formterm kann eine Platzierung nie
/// ueberstimmen, er bricht nur Gleichstaende in Richtung Form.
pub const DREIECK_GEWICHT: f64 = 1.0;

/// Abweichung des Brettes von der idealen Dreiecksform, als reine
/// Binaermatrix betrachtet (Nutzer-Formulierung 2026-08-24).
///
/// Zahlenwerte und Farben werden ignoriert, nur belegt (1) gegen leer (0):
///
/// * **Erlaubter Bereich** (`r + c <= 5`, 21 Zellen): jedes LEERE Feld ist
///   eine Abweichung.
/// * **Verbotener Bereich** (der Rest, 15 Zellen): jedes BELEGTE Feld ist
///   eine Abweichung.
///
/// Score 0 heisst perfekte Dreiecksform, hoeher heisst weiter weg.
///
/// **Warum diese Form das Ziel ist:** der erlaubte Bereich hat genau 21
/// Zellen -- dieselbe 21, die eine volle Spalte kostet (1+2+3+4+5+6). Die
/// Dreiecksform IST die Spalte-plus-Zeile-Struktur, nur vollstaendig
/// ausformuliert: ihre Kanten sind eine volle Rasterzeile und eine volle
/// Rasterspalte, und alles dazwischen ist zusammenhaengend, zahlt also
/// Platzierungspunkte nach Linienlaenge (`engine_manual.md:143-147`).
///
/// **Was sie loest:** die bisherige Zielzellen-Vereinigung aus Spalte und
/// Zeile war undifferenziert, und die Spalte gewann darin jeden Konflikt --
/// ihre sechs Zellen sind aus sechs verschiedenen Musterreihen bedienbar, die
/// der Zeile nur aus einer. Gemessen kostete jeder Spaltengewinn Zeilen
/// (0,438 auf 0,200 ueber vier Bauschritte). Ein einzelner Skalar ueber das
/// ganze Brett hat diesen Konflikt nicht.
///
/// **Spiegelung nur um die SPALTEN-Achse:** geprueft werden zwei
/// Orientierungen -- volle Spalte links (0) oder rechts (5) --, das Minimum
/// zaehlt. Die volle ZEILE liegt immer oben. Eine Spiegelung um die
/// Reihen-Achse gibt es nicht: sie verlangte eine volle Rasterzeile 5, und
/// die ist strukturell unerreichbar (Musterreihe 6 schliesst 1,3-mal je
/// Partie ab, gebraucht wuerden sechs). Damit bleibt die gestreute
/// Start-Ecke fuer die LINKS/RECHTS-Wahl wirksam, ohne dass eine nie
/// erreichbare Form belohnt wird.
pub fn triangle_deviation(player: &PlayerBoard) -> u32 {
    let mut belegt = [[false; 6]; 6];
    for (tr, reihe) in player.dome_grid.dome_slots.iter().enumerate() {
        for (tc, slot) in reihe.iter().enumerate() {
            let Some(slot) = slot else { continue };
            for (si, sp) in slot.spaces.iter().enumerate() {
                if sp.is_filled() {
                    belegt[2 * tr + si / 2][2 * tc + si % 2] = true;
                }
            }
        }
    }
    // ZWEI Orientierungen, nicht vier (Nutzer-Korrektur 2026-08-24: "es ist
    // nur gespiegelt um die Spalten, aber nicht um die Reihen").
    //
    // Gespiegelt wird an der senkrechten Achse: die volle Spalte kann links
    // (0) oder rechts (5) liegen. Die volle ZEILE liegt immer oben, denn die
    // unteren Orientierungen verlangten eine volle Rasterzeile 5 -- und die
    // wird ausschliesslich von Musterreihe 6 gespeist, die je Partie 1,3-mal
    // abschliesst. Sechs Zellen sind dort strukturell unerreichbar (dieselbe
    // Asymmetrie, die `plate_builder::ZEILEN_ZIEL_MAX` begruendet).
    //
    // Ein Minimum ueber alle vier wuerde ein Brett belohnen, das auf eine
    // NIE erreichbare Form zulaeuft -- der Grund, warum die erste Fassung
    // falsch war.
    let orientierungen: [fn(usize, usize) -> bool; 2] = [
        |r, c| r + c <= 5,       // volle Zeile 0, volle Spalte 0
        |r, c| r + (5 - c) <= 5, // volle Zeile 0, volle Spalte 5
    ];
    orientierungen
        .iter()
        .map(|erlaubt| {
            let mut fehler = 0u32;
            for r in 0..6 {
                for c in 0..6 {
                    if erlaubt(r, c) != belegt[r][c] {
                        fehler += 1;
                    }
                }
            }
            fehler
        })
        .min()
        .unwrap_or(0)
}

#[cfg(test)]
mod dreieck_tests {
    use super::*;
    use crate::dome::build_dome_tile_pool;

    /// Ein LEERES Brett hat genau 21 Abweichungen: alle Zellen des erlaubten
    /// Bereichs sind leer, im verbotenen liegt nichts. Das ist zugleich die
    /// Probe auf die Groesse des erlaubten Bereichs (1+2+3+4+5+6).
    #[test]
    fn empty_board_has_21_deviations() {
        let p = crate::board::PlayerBoard::new(0, "P");
        assert_eq!(triangle_deviation(&p), 21);
    }

    /// Jede belegte Zelle im erlaubten Bereich senkt die Abweichung um genau
    /// 1 -- die Metrik ist in der Binaermatrix linear, wie vorregistriert.
    #[test]
    fn filled_cell_in_allowed_area_lowers_by_one() {
        let mut p = crate::board::PlayerBoard::new(0, "P");
        let tile = build_dome_tile_pool()[0].clone();
        p.dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        let vorher = triangle_deviation(&p);
        // Zelle (0,0) liegt in JEDER Orientierung ausser unten-rechts im
        // erlaubten Bereich; das Minimum ueber die vier faellt also um 1.
        p.dome_grid.place_tile(0, 0, crate::tile::TileColor::Gelb).unwrap();
        assert_eq!(triangle_deviation(&p), vorher - 1);
    }
}
