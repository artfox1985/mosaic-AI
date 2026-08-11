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

/// Stetiger Ersatz für [`calculate_end_scoring`], gedacht für die MCTS-Blatt-
/// bewertung (NICHT für die echte Endwertung!): die "Alles-oder-nichts"-Platten
/// (0 Horizontale/1 Vertikale/2 Diagonale Reihen, 3 Mehrfarbige Felder,
/// 5 Eckplatten, 7 Farbenreiche Reihen) geben bei Teilfüllung einen quadratisch
/// skalierten Teil-Bonus statt hartem 0 — bei voller Füllung fällt die Formel
/// exakt auf den echten Punktwert von `calculate_end_scoring` zurück (ersetzt
/// diese Funktion also, statt sie zu ergänzen — keine Doppelzählung möglich).
/// Additive Platten (4 Äußere Felder, 6 Spezialfelder) bleiben unverändert
/// linear, die brauchen keinen Fortschritts-Ersatz. Der Exponent 2 bevorzugt
/// EINE fast fertige Linie/Ecke gegenüber vielen halbfertigen (verhindert
/// Verzetteln der Suche über zu viele Baustellen).
pub fn wertung_progress(player: &PlayerBoard, tile_ids: &[usize]) -> f64 {
    let sf = player_scoring_features(player);
    let mut total = 0.0;
    for &id in tile_ids {
        total += match id {
            0 => sf.row_fill.iter().map(|&f| (f as f64 / 6.0).powi(2)).sum::<f64>() * 3.0,
            1 => sf.col_fill.iter().map(|&f| (f as f64 / 6.0).powi(2)).sum::<f64>() * 7.0,
            2 => sf.diag_fill.iter().map(|&f| (f as f64 / 6.0).powi(2)).sum::<f64>() * 10.0,
            3 => (sf.wild_filled as f64 / sf.wild_total.max(1) as f64).powi(2)
                * 2.0
                * sf.wild_total as f64,
            4 => sf.border_fill as f64,
            5 => {
                (sf.corner_fill[0] as f64 / 4.0).powi(2) * 3.0
                    + (sf.corner_fill[1] as f64 / 4.0).powi(2) * 3.0
                    + (sf.corner_fill[2] as f64 / 4.0).powi(2) * 8.0
                    + (sf.corner_fill[3] as f64 / 4.0).powi(2) * 8.0
            }
            6 => -3.0 * sf.special_empty as f64,
            7 => sf.row_colors.iter().map(|&c| (c as f64 / 5.0).powi(2)).sum::<f64>() * 4.0,
            _ => 0.0,
        };
    }
    total
}

/// Parametrisierte Schwester von [`wertung_progress`] -- ABSICHTLICH eine
/// EIGENE Funktion, nicht `wertung_progress` selbst um einen `alpha`-
/// Parameter erweitert. `wertung_progress` haengt an `mcts.rs::player_total`,
/// dem Heuristik-Blattwert, der den Elo-Anker der gesamten Projekt-Historie
/// bildet -- jede Aenderung an dessen Zahlenwert (auch nur eine Verzweigung,
/// die bei `alpha=2.0` bitgleich dasselbe Ergebnis liefern SOLLTE) wuerde die
/// Elo-Historie entwerten, weil sie nicht mehr beweisbar an derselben Formel
/// haengt. Der Anker-Schutz entsteht hier daher durch KONSTRUKTION (zwei
/// getrennte Funktionen, `wertung_progress` unveraendert) statt durch eine
/// Bedingung innerhalb einer gemeinsamen Funktion -- und selbst wenn man eine
/// solche Bedingung wollte: `f.powi(2)` und `f.powf(2.0)` sind NICHT
/// garantiert bitgleich (verschiedene Implementierungen, siehe Rust-Doku zu
/// `powf`/`powi`), ein `if alpha == 2.0 { powi } else { powf }`-Zweig waere
/// also selbst schon eine (wenn auch winzige) Verhaltensaenderung gegenueber
/// dem Bestand.
///
/// Inhaltlich identische Struktur zu `wertung_progress`, aber `.powf(alpha)`
/// statt `.powi(2)` fuer die KONJUNKTIVEN Geometrien (0 Reihen, 1 Spalten,
/// 2 Diagonalen, 3 Mehrfarbige Felder, 5 Eckplatten, 7 Farbenreiche Reihen).
/// `alpha > 1` verstaerkt die Praemie fuer EINE fast vollstaendige Linie/Ecke
/// gegenueber vielen halbfertigen (Buendelung), `alpha = 1` macht die
/// Formel linear in der Fuellung (keine Buendelungs-Praemie mehr), siehe
/// Test `wertung_progress_alpha_rewards_bundling_when_alpha_above_one`.
///
/// Kriterium 4 (`border_fill`) und 6 (`-3 * special_empty`) bleiben LINEAR
/// (kein Exponent) -- das ist keine Wahl, sondern exakt: beide zahlen PRO
/// FELD, nicht pro vollstaendigem Satz, es gibt also gar keine "Teilerfuellung
/// eines Satzes", die ein Exponent ueberhaupt modulieren koennte.
/// KALIBRIERTE Exponenten je Kriterium, GEMESSEN am 2026-08-11 an der
/// Heuristik-Referenz (`plattenkopf_referenzlauf_heuristik`, 200 Partien,
/// `logs/referenz_kalibrierung.log`) -- also an einem Spieler, der die
/// Abschluesse ANSPIELT. Der Champion-Korpus ist als Referenz untauglich, weil
/// dort die Rate sein Defizit misst und nicht die Erreichbarkeit
/// (Nutzer-Einwand: *"der v20wdl-Korpus ist keine gute referenz"*).
///
/// Gemessen `(fill/kap)^2` gegen realisierte Abschlussrate:
///   Eckplatten 0,389 vs 0,286 ->   1,4x  ->  kalibriertes alpha ~ 2,6
///   Reihen     0,328 vs 0,060 ->   5,5x  ->  ~ 5,0
///   Spalten    0,287 vs 0,021 ->  13,5x  ->  ~ 6,3
///   Diagonalen 0,246 vs 0,0013-> 196,5x  ->  ~ 9,5
///
/// Der einheitliche Exponent 2 ueberschaetzt also alle konjunktiven Kriterien,
/// und zwar UNGLEICHMAESSIG ueber einen Faktor 140 -- ausgerechnet die
/// Diagonale (teuerstes und unerreichbarstes Kriterium) am stärksten. Ein
/// gemeinsames Gewicht kann das nicht korrigieren.
///
/// **Fuer eine 6-Zellen-Konjunktion landet der kalibrierte Exponent bei ~6,
/// also beim PRODUKT unabhaengiger Zellen.** Das ist die Wahrscheinlichkeit,
/// nach der die Nutzer-Frage von Anfang an gezielt hat.
///
/// GRENZE, nicht ueberlesen: grob aufgeloest ueber den MITTLEREN Fuellstand,
/// und `E[x^2] != (E[x])^2` -- ein exakter Fit braucht die Einzelbeobachtungen.
/// Ausserdem ist die Rate am ENDZUSTAND gemessen, nicht als
/// `P(vollstaendig | fill, runde)`. Letzteres waere das eigentlich richtige
/// Objekt und wuerde die ganze alpha-Konstruktion ersetzen.
const ALPHA_KALIBRIERT: [f64; 8] = [
    5.0, // 0 Reihen
    6.3, // 1 Spalten
    9.5, // 2 Diagonalen
    6.3, // 3 Jokerfelder -- keine eigene Messung, wie Spalten behandelt (ungeprueft)
    1.0, // 4 Randfelder -- ADDITIV, kein Exponent
    2.6, // 5 Eckplatten
    1.0, // 6 Spezialfelder -- ADDITIV (und hier ohnehin 0, s.u.)
    6.3, // 7 Farbreihen -- keine eigene Messung, wie Spalten behandelt (ungeprueft)
];

/// Rundenabhaengiger Exponent je Kriterium (Nutzer-Vorgabe: *"wir haben gesagt
/// wir verändern alpha über die runden"*, festgehalten in
/// `PREREG_plattenkopf.md`).
///
/// Runde 1 = `alpha_start` (flach, LENKT: der erste Stein einer Bahn ist etwas
/// wert), Runde 5 = kalibrierter Wert (SCHAETZT: nur noch Erreichbares zaehlt).
/// Damit sind Schaetzer und Lenker nicht zwei Entwuerfe, sondern zwei Enden
/// desselben Fahrplans -- die wahre Funktion `P(Linie vollstaendig)` wird mit
/// kuerzerem Horizont steiler.
///
/// Die LINEARE Interpolation ist eine Annahme, keine Messung.
pub fn alpha_fuer_runde(kriterium: usize, round_number: u32, alpha_start: f64) -> f64 {
    let ziel = ALPHA_KALIBRIERT[kriterium.min(7)];
    if ziel <= 1.0 {
        return 1.0; // additive Kriterien: nie ein Exponent
    }
    let t = ((round_number.clamp(1, 5) - 1) as f64) / 4.0;
    alpha_start + (ziel - alpha_start) * t
}

/// [`wertung_progress_alpha`] mit RUNDENABHAENGIGEM Exponenten JE KRITERIUM.
/// Das ist die korrigierte Fassung: der einheitliche Exponent 2 ueberschaetzt
/// die konjunktiven Kriterien ungleichmaessig (Faktor 1,4 bis 196,5, s.
/// [`ALPHA_KALIBRIERT`]), und ein gemeinsames Gewicht kann das nicht heilen.
///
/// Bewusst als DUENNE Huelle ueber `wertung_progress_alpha` gebaut, je Kriterium
/// einzeln aufgerufen -- so kann die Formel nicht auseinanderlaufen. Preis:
/// `player_scoring_features` laeuft einmal je aktivem Kriterium statt einmal
/// (bei 3 Platten im Spiel also 3x). Das ist ein Gang ueber 36 Felder gegen
/// einen Netz-Vorwaertslauf im selben Blatt, also vertretbar.
pub fn wertung_progress_runde(
    player: &PlayerBoard,
    tile_ids: &[usize],
    round_number: u32,
    alpha_start: f64,
) -> f64 {
    tile_ids
        .iter()
        .map(|&id| wertung_progress_alpha(player, &[id], alpha_fuer_runde(id, round_number, alpha_start)))
        .sum()
}

pub fn wertung_progress_alpha(player: &PlayerBoard, tile_ids: &[usize], alpha: f64) -> f64 {
    let sf = player_scoring_features(player);
    let mut total = 0.0;
    for &id in tile_ids {
        total += match id {
            0 => sf.row_fill.iter().map(|&f| (f as f64 / 6.0).powf(alpha)).sum::<f64>() * 3.0,
            1 => sf.col_fill.iter().map(|&f| (f as f64 / 6.0).powf(alpha)).sum::<f64>() * 7.0,
            2 => sf.diag_fill.iter().map(|&f| (f as f64 / 6.0).powf(alpha)).sum::<f64>() * 10.0,
            3 => (sf.wild_filled as f64 / sf.wild_total.max(1) as f64).powf(alpha)
                * 2.0
                * sf.wild_total as f64,
            4 => sf.border_fill as f64,
            5 => {
                (sf.corner_fill[0] as f64 / 4.0).powf(alpha) * 3.0
                    + (sf.corner_fill[1] as f64 / 4.0).powf(alpha) * 3.0
                    + (sf.corner_fill[2] as f64 / 4.0).powf(alpha) * 8.0
                    + (sf.corner_fill[3] as f64 / 4.0).powf(alpha) * 8.0
            }
            // Kriterium 6 BEWUSST 0 hier -- es wird von `unlock_progress_beta`
            // gehalten (Nutzer-Spezifikation 2026-08-11: "wenn die
            // wertungsplatte aktiv ist -3 fuer nicht belegte felder ... fuer
            // belegte Spezialfliesen 1..6 in abhaengigkeit der Reihe.
            // Beruecksichtigung von gestuftem Freischaltterm").
            //
            // WARUM NICHT BEIDE: waeren `MOSAIC_WERTUNG_SHAPING_W` und
            // `MOSAIC_UNLOCK_SHAPING_W` gleichzeitig > 0, wuerde der
            // Spezialfeld-Abzug DOPPELT in den Blattwert eingehen -- einmal
            // hier und einmal dort. Der Fehler war eingebaut und ist beim
            // Beantworten der Nutzer-Frage "hast du das fuer alle
            // wertungsplatten beruecksichtigt" aufgefallen.
            //
            // Der ANKER `wertung_progress` (oben, Zeile ~178) behaelt seinen
            // Kriterium-6-Term unveraendert -- er ist eine andere Funktion mit
            // anderem Aufrufer (`mcts.rs:82`, Heuristik) und darf sich nicht
            // bewegen.
            6 => 0.0,
            7 => sf.row_colors.iter().map(|&c| (c as f64 / 5.0).powf(alpha)).sum::<f64>() * 4.0,
            _ => 0.0,
        };
    }
    total
}

/// Gestufter Freischalt-Fortschritt fuer den Kuppel-Bonus (Nutzer-Auftrag
/// 2026-08-10, Messlage `evaluations/watchlist_v20_zwischenlese.md` Abschnitt
/// 2: Mensch 10,3 Spezialpunkte/Partie gegen KI 1,3 -- ~62 % der gesamten
/// Endpunkte-Luecke). Verifiziert am Code (nicht angenommen), drei Fragen:
///
/// 1. Feldtyp: `SpaceType::Special` (`dome.rs`), eigenes Flag `placed_special`
///    -- getrennt von `SpaceType::Wild`.
/// 2. Freischaltbedingung: `DomeTile::try_unlock_special` -- exakt "alle 3
///    ANDEREN Spaces DESSELBEN Slots gefuellt" (`other_filled`-Check dort,
///    `i == sp_idx || s.is_filled()` fuer alle 4 Indizes). Kein Slot-
///    uebergreifender Bezug.
/// 3. Punktwert -- KORRIGIERT (erster Versuch war falsch, siehe unten):
///    ZWEI unabhaengige Punktquellen, nicht eine.
///
/// ## Zwei unabhaengige Punktquellen (Nutzer-Korrektur 2026-08-11)
///
/// Erster Versuch las `DomeTile::bonus_points` als Punktwert. Falsch: laut
/// Kommentar an derselben Stelle in `dome.rs` ist `bonus_points` NUR der
/// Special(&gt;0)-gegen-Wild(=0)-Diskriminator (`is_special_type`), kein
/// Punkt-Award -- fiel nicht auf, weil alle 9 Special-Platten `bonus_points=3`
/// tragen.
///
/// - **Kuppel-Bonus (GRUNDWERTUNG, live beim Legen des weissen Steins)**:
///   `round_end.rs::check_special_trigger` -- `pattern_row = slot_row*2 +
///   sp_idx/2`, `bonus = pattern_row + 1`, also **1..6 je Rasterreihe**
///   (`docs/engine_manual.md` Abschnitt 5: "bringt sofort Punkte entsprechend
///   der Reihe (1 bis 6)"). Zahlt IMMER, unabhaengig von `scoring_tile_ids`.
///   Das ist die Quelle fuer den `n_s`-Fortschrittsteil unten.
/// - **Wertungsplatte 6 (ENDWERTUNG, `wertung_progress`/`wertung_progress_
///   alpha`)**: FLACH `-3` je leerem Spezialfeld, KEIN Rasterreihen-Bezug
///   (`docs/engine_manual.md`, Platte Nr. 7 der 8 Wertungsplatten: "-3 Pkt.
///   je leer gebliebenem Spezialfeld") -- zahlt NUR, wenn `6` in `tile_ids`
///   liegt. Bleibt UNVERAENDERT flach, siehe Test
///   `unlock_progress_beta_criterion6_addend_is_row_independent`.
///
/// Nebenbefund (separat berichtet, hier NICHT behoben): `board.rs::
/// PlayerBoard::place_special_tile` gibt `dome.bonus_points` (=3) zurueck --
/// inkonsistent zum echten Live-Pfad oben. Hat aber KEINEN Aufrufer im
/// gesamten Crate (kein PyO3-Binding, kein interner Call) -- toter Code,
/// kein aktiver Regelfehler.
///
/// Formel, JE SLOT EINZELN gebucht (nicht ueber das Brett gepoolt -- ein
/// Slot mit 2 von 3 vorbereitenden Feldern ist bei `beta>1` mehr wert als
/// zwei Slots mit je 1, siehe Test `unlock_progress_beta_is_booked_per_slot_
/// not_pooled`): fuer jeden Slot mit einem Special-Space --
///   - `wert_s = (slot_row*2 + sp_idx/2) + 1` (1..6, die Rasterreihe, exakt
///     wie `check_special_trigger`).
///   - bereits gefuellt   -> volle Gutschrift `wert_s`.
///   - sonst              -> `wert_s * (n_s/3)^beta`, `n_s` = Zahl der
///     gefuellten NICHT-Special-Spaces dieses Slots (0..3).
/// UNGEGATET (kein `tile_ids`-Check fuer diesen Teil) -- der Kuppel-Bonus
/// zahlt beim Legen des weissen Steins IMMER, unabhaengig von den am
/// Spielstart gezogenen Wertungsplatten (das ist ein Spielzug-Bonus, keine
/// Wertungsplatte). Kriterium 6 (`-3 * special_empty`, dieselbe Definition
/// wie in `wertung_progress`/`wertung_progress_alpha`) kommt ZUSAETZLICH
/// dazu, aber NUR wenn `6` in `tile_ids` liegt -- das ist die tatsaechliche
/// Wertungsplatte und bleibt an ihre Auswahl gebunden, UND bleibt flach
/// (keine Rasterreihen-Gewichtung -- das ist eine andere Regel als der
/// Bonus-Anteil, siehe oben).
pub fn unlock_progress_beta(player: &PlayerBoard, tile_ids: &[usize], beta: f64) -> f64 {
    let mut total = 0.0;
    for sr in 0..3 {
        for sc in 0..3 {
            let Some(tile) = &player.dome_grid.dome_slots[sr][sc] else { continue };
            let Some(sp_idx) = tile.special_space_idx() else { continue };
            let rasterreihe = sr * 2 + sp_idx / 2; // 0..5, wie check_special_trigger
            let wert = (rasterreihe + 1) as f64; // 1..6
            if tile.spaces[sp_idx].is_filled() {
                total += wert;
            } else {
                let n_s = tile
                    .spaces
                    .iter()
                    .enumerate()
                    .filter(|&(i, sp)| i != sp_idx && sp.is_filled())
                    .count() as f64;
                total += wert * (n_s / 3.0).powf(beta);
            }
        }
    }
    if tile_ids.contains(&6) {
        let sf = player_scoring_features(player);
        total += -3.0 * sf.special_empty as f64;
    }
    total
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
    use crate::board::DomeGrid;
    use crate::dome::{build_dome_tile_pool, DomeTile};
    use crate::tile::TileColor::*;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    // ── Validierung des Plattenkopf-Atomzuschnitts ───────────────────────────
    //
    // `evaluations/PREREG_plattenkopf.md` behauptet zwei Identitaeten auf dem
    // ENDBRETT, aus denen die Wahrscheinlichkeitsfassung ihre Exaktheit zieht.
    // Nutzer-Frage 2026-08-10: "hast du das auf ein paar spielsituationen
    // validiert oder einfach mal blind gebaut?" -- hier wird es geprueft,
    // statt behauptet.
    //
    //   Kriterium 6:  -3 * Sum_s A6_s  ==  score_empty_special_fields
    //                 A6_s = Slot s hat ein Spezialfeld, das LEER ist
    //   Kriterium 3:  +2 * Sum_s A3_s  ==  score_wild_fields
    //                 A3_s = Slot s hat ein BELEGTES Jokerfeld
    //                        UND alle Jokerfelder des Bretts sind belegt

    /// Atome von Kriterium 6 je Kuppelslot (hoechstens ein Spezialfeld je Platte).
    fn atoms_criterion6(player: &PlayerBoard) -> Vec<bool> {
        let mut out = Vec::new();
        for row in player.dome_grid.dome_slots.iter() {
            for slot in row.iter() {
                let hit = slot.as_ref().is_some_and(|t| {
                    t.spaces.iter().any(|sp| sp.space_type == SpaceType::Special && !sp.is_filled())
                });
                out.push(hit);
            }
        }
        out
    }

    /// Atome von Kriterium 3 je Kuppelslot -- die Konjunktion mit der
    /// Gesamtbedingung steckt IM Atom, daher der `all_filled`-Faktor.
    fn atoms_criterion3(player: &PlayerBoard) -> Vec<bool> {
        let wild = collect_spaces(player, SpaceType::Wild);
        let all_filled = !wild.is_empty() && wild.iter().all(|sp| sp.is_filled());
        let mut out = Vec::new();
        for row in player.dome_grid.dome_slots.iter() {
            for slot in row.iter() {
                let hit = all_filled
                    && slot.as_ref().is_some_and(|t| {
                        t.spaces.iter().any(|sp| sp.space_type == SpaceType::Wild && sp.is_filled())
                    });
                out.push(hit);
            }
        }
        out
    }

    #[test]
    #[ignore]
    fn plattenkopf_atom_identities_hold_on_real_end_boards() {
        use crate::round_transition::drive_to_game_end;

        let mut boards = 0usize;
        let mut c_true = 0usize;
        let mut wild_totals = Vec::new();
        let mut special_totals = Vec::new();
        let mut special_empty_counts = Vec::new();
        for seed in [11u64, 22, 33, 44, 55, 66, 77, 88, 99, 111, 222, 333] {
            let end_state = match drive_to_game_end(seed) {
                Some(s) => s,
                None => continue,
            };
            for player in end_state.players.iter() {
                boards += 1;
                // Identitaet Kriterium 6
                let a6 = atoms_criterion6(player);
                let lhs6 = -3 * a6.iter().filter(|&&b| b).count() as i32;
                let rhs6 = score_empty_special_fields(player);
                assert_eq!(lhs6, rhs6, "Seed {seed}: Kriterium-6-Identitaet verletzt");
                assert_eq!(a6.len(), 9, "9 Kuppelslots erwartet");
                // Identitaet Kriterium 3
                let a3 = atoms_criterion3(player);
                let lhs3 = 2 * a3.iter().filter(|&&b| b).count() as i32;
                let rhs3 = score_wild_fields(player);
                assert_eq!(lhs3, rhs3, "Seed {seed}: Kriterium-3-Identitaet verletzt");
                // Ungleichung aus dem PREREG: jedes Atom <= Gesamtbedingung
                let wild = collect_spaces(player, SpaceType::Wild);
                let cond = !wild.is_empty() && wild.iter().all(|sp| sp.is_filled());
                assert!(!a3.iter().any(|&b| b) || cond, "Atom wahr ohne Gesamtbedingung");
                if cond {
                    c_true += 1;
                }
                wild_totals.push(wild.len());
                let sp = collect_spaces(player, SpaceType::Special);
                special_totals.push(sp.len());
                special_empty_counts.push(sp.iter().filter(|s| !s.is_filled()).count());
            }
        }
        assert!(boards >= 8, "zu wenige Endbretter erzeugt ({boards})");
        let mean = |v: &Vec<usize>| v.iter().sum::<usize>() as f64 / v.len().max(1) as f64;
        println!("PLATTENKOPF-VALIDIERUNG: {boards} Endbretter, beide Identitaeten halten");
        println!(
            "  Grundrate 'alle Jokerfelder belegt' (Bedingung von Kriterium 3): {c_true}/{boards} = {:.1}%",
            100.0 * c_true as f64 / boards as f64
        );
        println!(
            "  Jokerfelder je Brett: Mittel {:.2}, min {:?}, max {:?}",
            mean(&wild_totals),
            wild_totals.iter().min(),
            wild_totals.iter().max()
        );
        println!(
            "  Spezialfelder je Brett: Mittel {:.2} | davon LEER: Mittel {:.2}, min {:?}, max {:?}",
            mean(&special_totals),
            mean(&special_empty_counts),
            special_empty_counts.iter().min(),
            special_empty_counts.iter().max()
        );
    }

    // ── 34-Konjunktions-Label-Spezifikation gegen die Engine ─────────────────
    //
    // `engine/py/neural_net.py::_conjunctions_from_dome` (Docstring dort,
    // Stand 2026-08-10) definiert 34 Binaerlabels je Spielerbrett; dieser
    // Test reimplementiert dieselbe Definition HIER IN RUST -- unabhaengig
    // von der Python-Seite, direkt gegen die echten `score_*`-Funktionen
    // dieser Datei -- und prueft auf KONSTRUIERTEN Brettern (nicht auf
    // Selfplay-Endstaenden): `evaluations/PREREG_plattenkopf.md` misst 16 der
    // 34 Labels auf dem Champion-Korpus als praktisch konstant 0 (Diagonalen,
    // Spalte 1, Reihen 5/6, untere Eckplatten) -- eine Pruefung auf echten
    // Partien liefe also gerade dort leer, wo ein Fehler am ehesten
    // unentdeckt bliebe. Konstruierte Bretter garantieren, dass jedes der 34
    // Labels sowohl feuert als auch nicht feuert (Coverage-Assertion am Ende).
    //
    // WICHTIG -- SCOPE, ausdruecklich vermerkt (keine stille Luecke): dieser
    // Test verifiziert die SPEZIFIKATION gegen die Rust-Wertung. Er verifiziert
    // NICHT `_conjunctions_from_dome` selbst -- die Labels laufen in Python auf
    // der Dome-JSON-Struktur, die Wertung hier auf `PlayerBoard`, zwei
    // getrennte Implementierungen ueber eine Sprachgrenze. Die dafuer
    // zustaendige, ERSCHOEPFENDE Pruefung (echte Python-Funktion gegen den
    // echten kompilierten Rust-Kern, ueber `mosaic_rust.end_scoring_from_state_json`
    // -- denselben PyO3-Pfad, den `serialize.rs::end_scoring_from_state`
    // "Space-fuer-Space EXAKT" fuer `dome_grid` dokumentiert) liegt in
    // `tools/conjunction_head_selfcheck.py` (Suite "ENGINE").
    // Nicht `#[ignore]`: braucht keinen Korpus, keine Zufalls-Partie, nur
    // konstruierte Boards -- laeuft in der normalen `cargo test`-Suite.

    /// Baut ein `DomeGrid` aus einem 6x6-Plan: `plan[r][c] = Some((typ, farbe,
    /// special_markiert))`, `None` = unberuehrt (leeres NORMAL-Feld). Nur
    /// beruehrte Slots bekommen eine Platte -- unberuehrte Slots bleiben
    /// `None`, was fuer die Wertung aequivalent zu "Slot vorhanden, aber leer"
    /// ist (`build_grid`/`collect_spaces` pruefen nur `is_filled()`/Typ, nie
    /// Slot-Anwesenheit direkt).
    fn grid_from_plan(plan: &[[Option<(SpaceType, Option<crate::tile::TileColor>, bool)>; 6]; 6]) -> DomeGrid {
        let mut grid = DomeGrid::default();
        for sr in 0..3 {
            for sc in 0..3 {
                let mut spaces = Vec::with_capacity(4);
                let mut touched = false;
                for si in 0..4 {
                    let (r, c) = (sr * 2 + si / 2, sc * 2 + si % 2);
                    let (space_type, color, special) = plan[r][c].unwrap_or((SpaceType::Normal, None, false));
                    if plan[r][c].is_some() {
                        touched = true;
                    }
                    spaces.push(DomeSpace {
                        space_type,
                        required_color: None,
                        placed_color: color,
                        placed_special: special,
                        is_locked: false,
                    });
                }
                if touched {
                    grid.place_dome_tile(DomeTile::new(sr * 3 + sc, spaces, 0), sr, sc).unwrap();
                }
            }
        }
        grid
    }

    fn player_with_grid(grid: DomeGrid) -> PlayerBoard {
        let mut p = PlayerBoard::new(0, "T");
        p.dome_grid = grid;
        p
    }

    /// Die 34 Atome, unabhaengig aus `PlayerBoard::dome_grid` reimplementiert
    /// (siehe Scope-Hinweis oben) -- Index/Reihenfolge exakt wie der Docstring
    /// von `_conjunctions_from_dome`.
    fn conjunction_atoms_spec(player: &PlayerBoard) -> [i32; 34] {
        let mut filled = [[false; 6]; 6];
        let mut colors: [[Option<crate::tile::TileColor>; 6]; 6] = [[None; 6]; 6];
        for sr in 0..3 {
            for sc in 0..3 {
                if let Some(slot) = &player.dome_grid.dome_slots[sr][sc] {
                    for (si, sp) in slot.spaces.iter().enumerate() {
                        let (r, c) = (sr * 2 + si / 2, sc * 2 + si % 2);
                        if sp.is_filled() {
                            filled[r][c] = true;
                            if !sp.placed_special {
                                colors[r][c] = sp.placed_color;
                            }
                        }
                    }
                }
            }
        }

        let mut out = [0i32; 34];
        for r in 0..6 {
            out[r] = (0..6).all(|c| filled[r][c]) as i32;
        }
        for c in 0..6 {
            out[6 + c] = (0..6).all(|r| filled[r][c]) as i32;
        }
        out[12] = (0..6).all(|i| filled[i][i]) as i32;
        out[13] = (0..6).all(|i| filled[i][5 - i]) as i32;
        for (k, &(sr, sc)) in [(0usize, 0usize), (0, 2), (2, 0), (2, 2)].iter().enumerate() {
            let (r0, c0) = (sr * 2, sc * 2);
            out[14 + k] = (0..2).all(|dr| (0..2).all(|dc| filled[r0 + dr][c0 + dc])) as i32;
        }
        let wild = collect_spaces(player, SpaceType::Wild);
        out[18] = (!wild.is_empty() && wild.iter().all(|sp| sp.is_filled())) as i32;
        for r in 0..6 {
            let mut seen: Vec<crate::tile::TileColor> = Vec::new();
            for c in 0..6 {
                if let Some(col) = colors[r][c] {
                    if !seen.contains(&col) {
                        seen.push(col);
                    }
                }
            }
            out[19 + r] = (seen.len() >= 5) as i32;
        }
        for sr in 0..3 {
            for sc in 0..3 {
                let has_wild = player.dome_grid.dome_slots[sr][sc].as_ref().is_some_and(|t| {
                    t.spaces.iter().any(|sp| sp.space_type == SpaceType::Wild)
                });
                out[25 + sr * 3 + sc] = has_wild as i32;
            }
        }
        out
    }

    #[test]
    fn plattenkopf_conjunction_atoms_match_spec() {
        const N: usize = 34;
        let corner_weights = [3, 3, 8, 8];
        let colors5 = [Blau, Gelb, Rot, Schwarz, Tuerkis];
        let mut coverage_true = [false; N];
        let mut coverage_false = [false; N];

        let mut check = |name: &str, grid: DomeGrid| {
            let player = player_with_grid(grid);
            let atoms = conjunction_atoms_spec(&player);
            for (i, &a) in atoms.iter().enumerate() {
                if a == 1 {
                    coverage_true[i] = true;
                } else {
                    coverage_false[i] = true;
                }
            }
            let rows: i32 = atoms[0..6].iter().sum();
            assert_eq!(3 * rows, score_horizontal_rows(&player), "{name}: Reihen");
            let cols: i32 = atoms[6..12].iter().sum();
            assert_eq!(7 * cols, score_vertical_rows(&player), "{name}: Spalten");
            let diags: i32 = atoms[12..14].iter().sum();
            assert_eq!(10 * diags, score_diagonal_rows(&player), "{name}: Diagonalen");
            let corner_sum: i32 = (0..4).map(|k| atoms[14 + k] * corner_weights[k]).sum();
            assert_eq!(corner_sum, score_corner_tiles(&player), "{name}: Eckplatten");
            let colorful: i32 = atoms[19..25].iter().sum();
            assert_eq!(4 * colorful, score_colorful_rows(&player), "{name}: Farbenreiche Reihen");
            let layout_sum: i32 = atoms[25..34].iter().sum();
            if atoms[18] == 1 {
                assert_eq!(score_wild_fields(&player), 2 * layout_sum, "{name}: Jokerfelder (Bedingung wahr)");
            } else {
                assert_eq!(score_wild_fields(&player), 0, "{name}: Jokerfelder (Bedingung falsch)");
            }
        };

        // EMPTY: alles 0.
        check("EMPTY", grid_from_plan(&[[None; 6]; 6]));

        // FULL: gesamtes Raster gefuellt, 3 Felder WILD (Slots (0,0),(1,1),(2,2)
        // -- Layout-Label 25, 29, 33), Farbmuster (r+c)%5 liefert genau 5
        // verschiedene Farben je Reihe.
        let mut plan_full: [[Option<(SpaceType, Option<crate::tile::TileColor>, bool)>; 6]; 6] =
            [[None; 6]; 6];
        for r in 0..6 {
            for c in 0..6 {
                plan_full[r][c] = Some((SpaceType::Normal, Some(colors5[(r + c) % 5]), false));
            }
        }
        for &(r, c) in &[(0usize, 0usize), (2, 2), (4, 4)] {
            let (_, color, _) = plan_full[r][c].unwrap();
            plan_full[r][c] = Some((SpaceType::Wild, color, false));
        }
        check("FULL", grid_from_plan(&plan_full));

        // LAYOUT_OTHER: Jokerfelder in den 6 Slots, die FULL nicht abdeckt.
        let mut plan_layout: [[Option<(SpaceType, Option<crate::tile::TileColor>, bool)>; 6]; 6] =
            [[None; 6]; 6];
        for &(r, c) in &[(0usize, 2usize), (0, 4), (2, 0), (2, 4), (4, 0), (4, 2)] {
            plan_layout[r][c] = Some((SpaceType::Wild, Some(Blau), false));
        }
        check("LAYOUT_OTHER", grid_from_plan(&plan_layout));

        // ROW3: eine volle Reihe, nur 2 Farben (nicht farbenreich).
        let mut plan_row3: [[Option<(SpaceType, Option<crate::tile::TileColor>, bool)>; 6]; 6] =
            [[None; 6]; 6];
        for c in 0..6 {
            plan_row3[3][c] = Some((SpaceType::Normal, Some(if c % 2 == 0 { Blau } else { Gelb }), false));
        }
        check("ROW3", grid_from_plan(&plan_row3));

        // COL5: eine volle Spalte.
        let mut plan_col5: [[Option<(SpaceType, Option<crate::tile::TileColor>, bool)>; 6]; 6] =
            [[None; 6]; 6];
        for r in 0..6 {
            plan_col5[r][5] = Some((SpaceType::Normal, Some(if r % 2 == 0 { Blau } else { Gelb }), false));
        }
        check("COL5", grid_from_plan(&plan_col5));

        // Vier isolierte Eckplatten -- einzeln, damit eine Gewichts-Vertauschung
        // nicht durch die Summenkonstanz {3,3,8,8} der FULL-Pruefung verdeckt wird.
        for &(sr, sc) in &[(0usize, 0usize), (0, 2), (2, 0), (2, 2)] {
            let mut plan: [[Option<(SpaceType, Option<crate::tile::TileColor>, bool)>; 6]; 6] =
                [[None; 6]; 6];
            let (r0, c0) = (sr * 2, sc * 2);
            for dr in 0..2 {
                for dc in 0..2 {
                    plan[r0 + dr][c0 + dc] = Some((SpaceType::Normal, Some(Blau), false));
                }
            }
            check(&format!("CORNER_{sr}{sc}"), grid_from_plan(&plan));
        }

        // Diagonalen einzeln (6x6 ist geradzahlig, keine Ueberschneidung).
        let mut plan_diag_main: [[Option<(SpaceType, Option<crate::tile::TileColor>, bool)>; 6]; 6] =
            [[None; 6]; 6];
        for i in 0..6 {
            plan_diag_main[i][i] = Some((SpaceType::Normal, Some(colors5[i % 5]), false));
        }
        check("DIAG_MAIN", grid_from_plan(&plan_diag_main));

        let mut plan_diag_anti: [[Option<(SpaceType, Option<crate::tile::TileColor>, bool)>; 6]; 6] =
            [[None; 6]; 6];
        for i in 0..6 {
            plan_diag_anti[i][5 - i] = Some((SpaceType::Normal, Some(colors5[i % 5]), false));
        }
        check("DIAG_ANTI", grid_from_plan(&plan_diag_anti));

        // Farbenreich OHNE volle Reihe (5 von 6 Zellen).
        let mut plan_colorful_partial: [[Option<(SpaceType, Option<crate::tile::TileColor>, bool)>; 6]; 6] =
            [[None; 6]; 6];
        for c in 0..5 {
            plan_colorful_partial[2][c] = Some((SpaceType::Normal, Some(colors5[c]), false));
        }
        check("COLORFUL_PARTIAL", grid_from_plan(&plan_colorful_partial));

        // Jokerfelder vorhanden, aber NICHT alle belegt (Bedingung falsch) --
        // und Layout bleibt unabhaengig vom Fuellstand wahr.
        let mut plan_wild_partial: [[Option<(SpaceType, Option<crate::tile::TileColor>, bool)>; 6]; 6] =
            [[None; 6]; 6];
        plan_wild_partial[0][0] = Some((SpaceType::Wild, Some(Blau), false));
        plan_wild_partial[2][3] = Some((SpaceType::Wild, None, false)); // bleibt leer
        check("WILD_PARTIAL", grid_from_plan(&plan_wild_partial));

        let missing: Vec<usize> = (0..N)
            .filter(|&i| !(coverage_true[i] && coverage_false[i]))
            .collect();
        assert!(missing.is_empty(), "Labels ohne beide Zustaende (feuert/feuert nicht): {missing:?}");
    }

    // ── Referenzlaeufe: Boden (Zufall) und Mittelwert (Heuristik) ────────────
    //
    // Nutzer-Auftrag 2026-08-10: `logs/atom_skill_check.log` zeigt 16 von 34
    // Plattenkopf-Zusatzzielen als praktisch konstant auf dem CHAMPION-Korpus
    // (Reihen 3-6 nie vollstaendig, Diagonalen ~0, untere Eckplatten ~0,
    // farbenreiche Reihen 3-6 nie). Offen ist, ob das STRUKTUR ist (auf diesem
    // Brett nicht erreichbar) oder ein STRATEGIEDEFIZIT des Champions. Zwei
    // Referenzlaeufe grenzen das ein:
    //
    //   Zufall    (`drive_to_game_end_random`)     -- policy-freier Boden
    //   Heuristik (`drive_to_game_end_heuristik`)  -- kompetenter Mittelwert
    //
    // Lesart: liegt ein Kriterium AUCH bei der Heuristik ~0, ist die Groesse
    // strukturell (Kombinatorik des Bretts/der Platten), nicht gelernt. Liegt
    // die Heuristik deutlich UEBER dem Champion, ist es ein Strategiedefizit.
    //
    // Beide Tests sind `#[ignore]` (Messungen, keine Zusicherungen) und lesen
    // die Partienzahl aus `MOSAIC_PLATTENKOPF_GAMES` (Heuristik-Sims aus
    // `MOSAIC_PLATTENKOPF_SIMS`), damit ein Probelauf mit kleinem N moeglich
    // ist, ohne den Test anzufassen.

    fn probe_usize(var: &str, default: usize) -> usize {
        std::env::var(var).ok().and_then(|v| v.parse().ok()).unwrap_or(default)
    }

    /// Atom-Grundraten in der Reihenfolge von `_conjunctions_from_dome`
    /// (`engine/py/neural_net.py`) bzw. `logs/atom_skill_check.log` -- damit die
    /// Referenzlauf-Spalten direkt neben die Champion-Spalte gestellt werden
    /// koennen, ohne die Reihenfolge im Kopf umzusortieren.
    fn atom_labels_and_bits(player: &PlayerBoard) -> Vec<(String, bool)> {
        let sf = player_scoring_features(player);
        let mut out: Vec<(String, bool)> = Vec::new();
        for r in 0..6 {
            out.push((format!("Reihe {} vollst.", r + 1), sf.row_fill[r] == 6));
        }
        for c in 0..6 {
            out.push((format!("Spalte {} vollst.", c + 1), sf.col_fill[c] == 6));
        }
        out.push(("Diagonale H".to_string(), sf.diag_fill[0] == 6));
        out.push(("Diagonale N".to_string(), sf.diag_fill[1] == 6));
        for (k, name) in ["Ecke (0,0)", "Ecke (0,2)", "Ecke (2,0)", "Ecke (2,2)"].iter().enumerate() {
            out.push((name.to_string(), sf.corner_fill[k] == 4));
        }
        out.push((
            "ALLE Jokerfelder belegt".to_string(),
            sf.wild_total > 0 && sf.wild_filled == sf.wild_total,
        ));
        for r in 0..6 {
            out.push((format!("Reihe {} >=5 Farben", r + 1), sf.row_colors[r] >= 5));
        }
        for sr in 0..3 {
            for sc in 0..3 {
                let hit = player.dome_grid.dome_slots[sr][sc]
                    .as_ref()
                    .is_some_and(|t| t.spaces.iter().any(|sp| sp.space_type == SpaceType::Wild));
                out.push((format!("Layout: Slot {} traegt Joker", sr * 3 + sc), hit));
            }
        }
        out
    }

    /// Gemeinsamer Bericht beider Referenzlaeufe -- je Kriterium 0..7 Mittelwert
    /// der Punkte und Anteil der Bretter mit Punkten != 0, dazu die 34
    /// Atom-Grundraten fuer den direkten Vergleich mit dem Champion-Log.
    fn report_reference_run(label: &str, games: usize, boards: &[PlayerBoard]) {
        assert!(!boards.is_empty(), "{label}: keine Endbretter erzeugt");
        let n = boards.len() as f64;
        println!("\n=== REFERENZLAUF {label} ===");
        println!("{} Partien -> {} Endbretter", games, boards.len());
        println!("  ID  Kriterium                      Mittel-Pkt   Anteil !=0");
        for tile in ALL_SCORING_TILES.iter() {
            let pts: Vec<i32> = boards.iter().map(|b| tile.score(b)).collect();
            let mean = pts.iter().sum::<i32>() as f64 / n;
            let share = pts.iter().filter(|&&p| p != 0).count() as f64 / n;
            println!(
                "  {:>2}  {:<28} {:>10.3}   {:>8.1}%",
                tile.id,
                tile.name,
                mean,
                100.0 * share
            );
        }
        let feats: Vec<ScoringFeatures> = boards.iter().map(player_scoring_features).collect();
        let mean_u32 = |f: &dyn Fn(&ScoringFeatures) -> u32| -> f64 {
            feats.iter().map(|s| f(s) as f64).sum::<f64>() / n
        };
        println!(
            "  Kriterium 6 extra: LEERE Spezialfelder je Brett Mittel {:.3} (von {:.3} vorhandenen)",
            mean_u32(&|s| s.special_empty),
            mean_u32(&|s| s.special_total)
        );
        // Belegte Kuppelslots: Plausibilitaets-Anker. Waeren am Spielende nicht
        // (nahezu) alle 9 Slots belegt, waere der ganze Vergleich hinfaellig --
        // dann waeren die Nullraten eine Folge fehlender Platten, nicht der
        // Steinverteilung (`neural_net.py::_conjunctions_from_dome` setzt "im
        // Endzustand sind empirisch alle Slots belegt" voraus).
        let slots: f64 = boards
            .iter()
            .map(|b| {
                b.dome_grid
                    .dome_slots
                    .iter()
                    .flat_map(|r| r.iter())
                    .filter(|s| s.is_some())
                    .count() as f64
            })
            .sum::<f64>()
            / n;
        println!(
            "  Kontext: belegte Kuppelslots {:.3}/9 | Jokerfelder {:.3} | Spezialfelder {:.3} | gefuellte Felder {:.3}/36",
            slots,
            mean_u32(&|s| s.wild_total),
            mean_u32(&|s| s.special_total),
            mean_u32(&|s| s.row_fill.iter().sum::<u32>())
        );

        // KALIBRIERUNG des Fortschritts-Proxys (2026-08-11, Nutzer-Auftrag).
        // Frage: ist `(fill/6)^2` -- die Wahrscheinlichkeitsschaetzung in
        // `wertung_progress`/`wertung_progress_alpha` -- gut kalibriert?
        //
        // WARUM NICHT AM CHAMPION-KORPUS: dort liegt die realisierte
        // Abschlussrate bei 0,56 % (Spalten), weil der Champion Spalten nicht
        // ANSPIELT. Der Vergleich messe dann sein Defizit, nicht die Guete der
        // Formel -- Nutzer-Einwand 2026-08-11 ("der v20wdl-Korpus ist keine
        // gute referenz, da er die abschluesse nicht sauber spielt"). Die
        // Heuristik spielt sie an (`wertung_progress` haengt an `mcts.rs:82`),
        // ist also die brauchbare Referenz.
        println!("  -- Kalibrierung (fill/6)^2 gegen realisierte Abschlussrate --");
        let mean_f = |f: &dyn Fn(&ScoringFeatures) -> Vec<u32>, k: f64| -> (f64, f64) {
            let (mut sp, mut sr, mut n2) = (0.0, 0.0, 0.0);
            for s in feats.iter() {
                for v in f(s) {
                    sp += (v as f64 / k).powi(2);
                    sr += if v as f64 >= k { 1.0 } else { 0.0 };
                    n2 += 1.0;
                }
            }
            (sp / n2, sr / n2)
        };
        for (name, get, kap) in [
            ("Reihen", (&|s: &ScoringFeatures| s.row_fill.to_vec()) as &dyn Fn(&ScoringFeatures) -> Vec<u32>, 6.0),
            ("Spalten", &|s: &ScoringFeatures| s.col_fill.to_vec(), 6.0),
            ("Diagonalen", &|s: &ScoringFeatures| s.diag_fill.to_vec(), 6.0),
            ("Eckplatten", &|s: &ScoringFeatures| s.corner_fill.to_vec(), 4.0),
        ] {
            let (proxy, rate) = mean_f(get, kap);
            let faktor = if rate > 1e-9 { proxy / rate } else { f64::INFINITY };
            println!(
                "  {:<12} (fill/kap)^2 Mittel {:.4} | Abschlussrate {:.4} | Faktor {:>8.1}x",
                name, proxy, rate, faktor
            );
        }

        println!("  -- Atom-Grundraten (Reihenfolge wie logs/atom_skill_check.log) --");
        let names: Vec<String> = atom_labels_and_bits(&boards[0]).into_iter().map(|(l, _)| l).collect();
        let mut hits = vec![0usize; names.len()];
        for b in boards.iter() {
            for (i, (_, bit)) in atom_labels_and_bits(b).into_iter().enumerate() {
                if bit {
                    hits[i] += 1;
                }
            }
        }
        for (name, h) in names.iter().zip(hits.iter()) {
            println!("  {:<32} {:.3}", name, *h as f64 / n);
        }
    }

    #[test]
    #[ignore]
    fn plattenkopf_referenzlauf_zufall() {
        use crate::round_transition::{drive_to_game_end_reference, ReferenzPolitik};
        use rayon::prelude::*;

        let games = probe_usize("MOSAIC_PLATTENKOPF_GAMES", 1000);
        let t0 = std::time::Instant::now();
        let boards: Vec<PlayerBoard> = (0..games)
            .into_par_iter()
            .filter_map(|i| drive_to_game_end_reference(1000 + i as u64, ReferenzPolitik::Zufall))
            .flat_map(|st| st.players)
            .collect();
        report_reference_run("ZUFALL (uniformes Drafting, 9 Platten)", games, &boards);
        println!("  Laufzeit {:.1}s", t0.elapsed().as_secs_f64());
    }

    #[test]
    #[ignore]
    fn plattenkopf_referenzlauf_heuristik() {
        use crate::round_transition::{drive_to_game_end_reference, ReferenzPolitik};
        use rayon::prelude::*;

        let games = probe_usize("MOSAIC_PLATTENKOPF_GAMES", 400);
        let sims = probe_usize("MOSAIC_PLATTENKOPF_SIMS", 150) as u32;
        let t0 = std::time::Instant::now();
        let boards: Vec<PlayerBoard> = (0..games)
            .into_par_iter()
            .filter_map(|i| {
                drive_to_game_end_reference(1000 + i as u64, ReferenzPolitik::Heuristik(sims))
            })
            .flat_map(|st| st.players)
            .collect();
        report_reference_run(&format!("HEURISTIK ({sims} Sims, DEFAULT_C)"), games, &boards);
        println!("  Laufzeit {:.1}s", t0.elapsed().as_secs_f64());
    }

    /// Belegt den Grund, warum die Referenzlaeufe einen EIGENEN Treiber
    /// brauchen: `drive_to_game_end_random` ueberspringt die Startkuppel
    /// (`start_tile_pending = false`), es landen nur 8 der 9 Platten auf dem
    /// Brett. Der Bericht zeigt "belegte Kuppelslots 8.000/9" -- damit sind 2
    /// Reihen, 2 Spalten und mindestens eine Diagonale per Konstruktion
    /// unerreichbar, die Nullraten waeren ein Artefakt des Treibers und kein
    /// Befund ueber das Spiel. NUR als Kontrolle gedacht, nicht als Boden.
    #[test]
    #[ignore]
    fn plattenkopf_referenzlauf_zufall_ohne_startplatte() {
        use crate::round_transition::drive_to_game_end_random;
        use rayon::prelude::*;

        let games = probe_usize("MOSAIC_PLATTENKOPF_GAMES", 400);
        let boards: Vec<PlayerBoard> = (0..games)
            .into_par_iter()
            .filter_map(|i| drive_to_game_end_random(1000 + i as u64))
            .flat_map(|st| st.players)
            .collect();
        report_reference_run("KONTROLLE: ZUFALL OHNE Startplatte (8 Platten)", games, &boards);
    }

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
    fn wertung_progress_matches_end_scoring_on_full_board() {
        // Bei voller Fuellung muss die stetige Fortschritts-Formel exakt auf
        // den echten (diskreten) Wertungsplatten-Punktwert zurueckfallen --
        // sonst waere sie keine gueltige Ersatzformel fuer die Suche.
        let p = fully_filled_board();
        for id in [0usize, 1, 2, 3, 4, 5, 6] {
            let exact = calculate_end_scoring(&p, &[id]).total as f64;
            let progress = wertung_progress(&p, &[id]);
            assert!(
                (exact - progress).abs() < 1e-9,
                "Platte {id}: exakt={exact} vs fortschritt={progress}"
            );
        }
    }

    #[test]
    fn wertung_progress_is_zero_on_empty_board() {
        let p = PlayerBoard::new(0, "P");
        assert_eq!(wertung_progress(&p, &[0, 1, 2, 3, 5, 7]), 0.0);
    }

    #[test]
    fn wertung_progress_gives_partial_credit_before_completion() {
        // Kuppelplatte (0,0) ist eine obere Eckplatte (3 Pkt bei voller
        // Fuellung aller 4 Spaces). Hier nur 2 von 4 Spaces gefuellt -- die
        // diskrete Wertung (`calculate_end_scoring`) sieht das noch als 0,
        // der Fortschritts-Term soll aber schon einen Teil-Bonus zwischen
        // 0 und dem vollen Wert liefern.
        let mut p = PlayerBoard::new(0, "P");
        let mut tile = build_dome_tile_pool()[0].clone();
        for sp in tile.spaces.iter_mut().take(2) {
            match sp.space_type {
                SpaceType::Special => sp.placed_special = true,
                SpaceType::Wild => sp.placed_color = Some(Rot),
                SpaceType::Normal => sp.placed_color = sp.required_color,
            }
        }
        p.dome_grid.place_dome_tile(tile, 0, 0).unwrap();

        let exact = calculate_end_scoring(&p, &[5]).total as f64;
        let progress = wertung_progress(&p, &[5]);
        assert_eq!(exact, 0.0, "Eckplatte noch nicht komplett -> diskret 0");
        assert!(progress > 0.0 && progress < 3.0, "Teil-Bonus erwartet, war {progress}");
        // (2/4)^2 * 3 = 0.75
        assert!((progress - 0.75).abs() < 1e-9, "war {progress}");
    }

    #[test]
    fn alpha_fuer_runde_steigt_und_ist_in_runde_1_der_startwert() {
        // Waechter fuer den Rundenfahrplan (2026-08-11). Die uebrigen
        // Shaping-Tests laufen ALLE auf Runde-1-Zustaenden -- dort ist
        // alpha_c(1) == alpha_start, das neue Verhalten waere dort also
        // unsichtbar. Dieser Test prueft genau die Rundenabhaengigkeit.
        let start = 2.0;
        for krit in [0usize, 1, 2, 5] {
            let r1 = alpha_fuer_runde(krit, 1, start);
            let r5 = alpha_fuer_runde(krit, 5, start);
            assert!((r1 - start).abs() < 1e-12,
                    "Kriterium {krit}: Runde 1 muss der Startwert sein, war {r1}");
            assert!(r5 > r1,
                    "Kriterium {krit}: alpha muss ueber die Runden STEIGEN ({r1} -> {r5})");
            assert!((r5 - ALPHA_KALIBRIERT[krit]).abs() < 1e-12,
                    "Kriterium {krit}: Runde 5 muss den kalibrierten Wert treffen");
            // Monotonie ueber alle Runden
            let mut prev = r1;
            for r in 2..=5u32 {
                let a = alpha_fuer_runde(krit, r, start);
                assert!(a >= prev - 1e-12, "Kriterium {krit}: Runde {r} fiel ab");
                prev = a;
            }
        }
        // Die ADDITIVEN Kriterien bekommen NIE einen Exponenten -- 4 (Randfelder,
        // +1 je Feld) und 6 (Spezialfelder, hier ohnehin 0).
        for krit in [4usize, 6] {
            for r in 1..=5u32 {
                assert!((alpha_fuer_runde(krit, r, start) - 1.0).abs() < 1e-12,
                        "Kriterium {krit} ist additiv, alpha muss 1 bleiben (Runde {r})");
            }
        }
        // Die Diagonale ist das steilste Kriterium (196,5x ueberschaetzt bei
        // alpha=2) und muss in Runde 5 ueber der Spalte liegen.
        assert!(alpha_fuer_runde(2, 5, start) > alpha_fuer_runde(1, 5, start),
                "Diagonale muss in Runde 5 steiler sein als die Spalte");
    }

    #[test]
    fn wertung_progress_alpha_matches_wertung_progress_at_alpha_two() {
        // Neutralitaets-Nachweis: `alpha=2.0` muss `wertung_progress` fuer
        // mehrere nichttriviale Bretter reproduzieren (Toleranz 1e-9, NICHT
        // Bit-Gleichheit -- `powf(2.0)` vs `powi(2)` duerfen im letzten Bit
        // abweichen, exakt deshalb ist `wertung_progress_alpha` eine eigene
        // Funktion statt eines Zweigs in `wertung_progress`).
        let boards = [fully_filled_board(), {
            // Teilgefuelltes Brett (wie im Teil-Bonus-Test oben), damit auch
            // die Nicht-0/Nicht-1-Zwischenwerte der konjunktiven Kriterien
            // geprueft werden, nicht nur die Randfaelle leer/voll.
            let mut p = PlayerBoard::new(0, "P");
            let mut tile = build_dome_tile_pool()[0].clone();
            for sp in tile.spaces.iter_mut().take(2) {
                match sp.space_type {
                    SpaceType::Special => sp.placed_special = true,
                    SpaceType::Wild => sp.placed_color = Some(Rot),
                    SpaceType::Normal => sp.placed_color = sp.required_color,
                }
            }
            p.dome_grid.place_dome_tile(tile, 0, 0).unwrap();
            p
        }];
        // KRITERIUM 6 IST AUSGENOMMEN, und zwar ABSICHTLICH (Nutzer-Spezifikation
        // 2026-08-11): den Spezialfeld-Abzug haelt `unlock_progress_beta`, nicht
        // `wertung_progress_alpha` -- sonst zaehlt er doppelt, wenn beide
        // Shaping-Knoepfe gesetzt sind. Der ANKER `wertung_progress` behaelt ihn.
        // Die Divergenz wird unten ausdruecklich GEPRUEFT statt stillschweigend
        // uebergangen.
        const OHNE_K6: [usize; 7] = [0, 1, 2, 3, 4, 5, 7];
        for p in &boards {
            for id in OHNE_K6 {
                let exact = wertung_progress(p, &[id]);
                let via_alpha = wertung_progress_alpha(p, &[id], 2.0);
                assert!(
                    (exact - via_alpha).abs() < 1e-9,
                    "Platte {id}: wertung_progress={exact} vs wertung_progress_alpha(alpha=2.0)={via_alpha}"
                );
            }
            // Und ueber alle Platten gemeinsam (deckt Summierungs-Reihenfolge ab).
            let exact_all = wertung_progress(p, &OHNE_K6);
            let via_alpha_all = wertung_progress_alpha(p, &OHNE_K6, 2.0);
            assert!((exact_all - via_alpha_all).abs() < 1e-9);

            // Die BEABSICHTIGTE Divergenz: die Schwester liefert fuer Kriterium 6
            // immer 0, der Anker liefert -3 je leerem Spezialfeld.
            assert_eq!(
                wertung_progress_alpha(p, &[6], 2.0),
                0.0,
                "Kriterium 6 muss in wertung_progress_alpha 0 sein (haelt unlock_progress_beta)"
            );
            let sf = player_scoring_features(p);
            assert!(
                (wertung_progress(p, &[6]) - (-3.0 * sf.special_empty as f64)).abs() < 1e-9,
                "Anker wertung_progress muss Kriterium 6 unveraendert behalten"
            );
        }
    }

    #[test]
    fn wertung_progress_alpha_rewards_bundling_when_alpha_above_one() {
        // Kriterium 1 (Vertikale Reihen, 7 Pkt/volle Spalte): sechs gefuellte
        // Felder gebuendelt in EINER Spalte muessen bei `alpha>1` mehr wert
        // sein als sechs Felder verteilt als drei-plus-drei auf zwei Spalten
        // -- bei `alpha=1` (linear in der Fuellung) sind beide gleich, das
        // ist die alpha-Schwelle, ab der ueberhaupt eine Buendelungs-Praemie
        // entsteht.
        //
        // Aufbau ueber die 3 Kuppelplaetze der Spalte `sc=0`
        // (dome_slots[0][0]/[1][0]/[2][0]): jeder Slot hat 4 Spaces, Index
        // `si` -> (Zeilen-Offset, Spalten-Offset) = (si/2, si%2) innerhalb
        // des Slots (siehe `build_grid`).
        //   - "gebuendelt": si in {0,2} gefuellt (Spalten-Offset 0) in allen
        //     3 Slots -> volle 6x6-Spalte 0 (col_fill[0]=6, col_fill[1]=0).
        //   - "verteilt": si in {0,1} gefuellt (beide Spalten-Offsets, aber
        //     nur die JEWEILS ERSTE Zeile jedes Slots) in allen 3 Slots ->
        //     Spalte 0 UND Spalte 1 je zur Haelfte gefuellt
        //     (col_fill[0]=3, col_fill[1]=3). Gleiche Gesamtzahl gefuellter
        //     Felder (6) wie beim gebuendelten Brett -- fairer Vergleich.
        fn board_with_slot_spaces(sis: &[usize; 2]) -> PlayerBoard {
            let mut p = PlayerBoard::new(0, "P");
            let pool = build_dome_tile_pool();
            for sr in 0..3usize {
                let mut t = pool[sr * 3].clone(); // sc=0 => Pool-Index sr*3+0
                for (si, sp) in t.spaces.iter_mut().enumerate() {
                    if sis.contains(&si) {
                        match sp.space_type {
                            SpaceType::Special => {
                                sp.is_locked = false;
                                sp.placed_special = true;
                            }
                            SpaceType::Wild => sp.placed_color = Some(Rot),
                            SpaceType::Normal => sp.placed_color = sp.required_color,
                        }
                    }
                }
                p.dome_grid.place_dome_tile(t, sr, 0).unwrap();
            }
            p
        }

        let bundled = board_with_slot_spaces(&[0, 2]);
        let spread = board_with_slot_spaces(&[0, 1]);

        let sf_bundled = player_scoring_features(&bundled);
        let sf_spread = player_scoring_features(&spread);
        assert_eq!(sf_bundled.col_fill, [6, 0, 0, 0, 0, 0], "Vorbedingung gebuendelt");
        assert_eq!(sf_spread.col_fill, [3, 3, 0, 0, 0, 0], "Vorbedingung verteilt");

        // alpha=1: linear in der Fuellung -> beide Anordnungen gleichwertig.
        let bundled_a1 = wertung_progress_alpha(&bundled, &[1], 1.0);
        let spread_a1 = wertung_progress_alpha(&spread, &[1], 1.0);
        assert!((bundled_a1 - spread_a1).abs() < 1e-9, "bei alpha=1 gleichwertig: {bundled_a1} vs {spread_a1}");

        // alpha=2: Buendelung wird praemiert.
        let bundled_a2 = wertung_progress_alpha(&bundled, &[1], 2.0);
        let spread_a2 = wertung_progress_alpha(&spread, &[1], 2.0);
        assert!(
            bundled_a2 > spread_a2,
            "gebuendelt sollte bei alpha=2 mehr wert sein: {bundled_a2} vs {spread_a2}"
        );
        // Exakte Werte zur Gegenprobe: (6/6)^2*7=7 vs 2*(3/6)^2*7=3.5.
        assert!((bundled_a2 - 7.0).abs() < 1e-9);
        assert!((spread_a2 - 3.5).abs() < 1e-9);
    }

    /// Platziert eine SPECIAL-Typ-Platte (`pool_idx` MUSS `is_special_type()`
    /// sein) an Slot `(sr, sc)`: `filled_normal` (0..=3) ihrer NICHT-Special-
    /// Spaces werden befuellt, `fill_special` steuert das Special-Space
    /// selbst (unabhaengig von `filled_normal` -- fuer die Formel-Tests
    /// unten reicht direkte Manipulation, kein Umweg ueber
    /// `try_unlock_special`/echten Spielablauf).
    fn place_special_type_tile_at(
        p: &mut PlayerBoard,
        sr: usize,
        sc: usize,
        pool_idx: usize,
        filled_normal: usize,
        fill_special: bool,
    ) {
        let mut t = build_dome_tile_pool()[pool_idx].clone();
        assert!(t.is_special_type(), "Pool-Index {pool_idx} muss eine Special-Typ-Platte sein");
        let sp_idx = t.special_space_idx().unwrap();
        let mut filled = 0usize;
        for (i, sp) in t.spaces.iter_mut().enumerate() {
            if i == sp_idx {
                if fill_special {
                    sp.is_locked = false;
                    sp.placed_special = true;
                }
                continue;
            }
            if filled < filled_normal {
                match sp.space_type {
                    SpaceType::Wild => sp.placed_color = Some(Rot),
                    SpaceType::Normal => sp.placed_color = sp.required_color,
                    SpaceType::Special => unreachable!("sp_idx deckt das einzige Special-Space ab"),
                }
                filled += 1;
            }
        }
        p.dome_grid.place_dome_tile(t, sr, sc).unwrap();
    }

    #[test]
    fn unlock_progress_beta_is_strictly_increasing_and_convex_when_beta_above_one() {
        // Kernanforderung (Nutzer-Auftrag 2026-08-10): 2 von 3 vorbereitenden
        // Feldern muss MEHR liefern als 1 von 3, und bei `beta>1` muss der
        // Schritt 2->3 schwerer wiegen als 0->1 (Konvexitaet -- das ist genau
        // der Anreiz, den letzten Schritt zur Freischaltung zu gehen statt
        // bei "fast fertig" stehenzubleiben).
        let beta = 2.0;
        let vals: Vec<f64> = (0..=3usize)
            .map(|n| {
                let mut p = PlayerBoard::new(0, "P");
                place_special_type_tile_at(&mut p, 0, 0, 0, n, n == 3);
                unlock_progress_beta(&p, &[], beta)
            })
            .collect();
        for i in 0..3 {
            assert!(
                vals[i + 1] > vals[i],
                "n={} -> n={}: {} -> {} ist nicht steigend",
                i,
                i + 1,
                vals[i],
                vals[i + 1]
            );
        }
        let step_0_1 = vals[1] - vals[0];
        let step_2_3 = vals[3] - vals[2];
        assert!(
            step_2_3 > step_0_1,
            "Schritt 2->3 ({step_2_3}) sollte bei beta=2 schwerer wiegen als 0->1 ({step_0_1})"
        );
        // Randbedingung: bei n=3 muss "schon gefuellt" (volle Gutschrift) und
        // "alle 3 anderen gefuellt, Special selbst noch offen" denselben Wert
        // liefern -- (3/3)^beta == 1, die beiden Zweige der Formel stossen
        // dort stetig aneinander.
        let mut p_unfilled = PlayerBoard::new(0, "P");
        place_special_type_tile_at(&mut p_unfilled, 0, 0, 0, 3, false);
        assert!((unlock_progress_beta(&p_unfilled, &[], beta) - vals[3]).abs() < 1e-12);
        // pool[0] hat sp_idx=3 (Special an Position 3) -> Rasterreihe
        // 0*2 + 3/2 = 1 -> wert = 2 (NICHT `bonus_points`, siehe Funktions-
        // Kommentar/Nutzer-Korrektur 2026-08-11).
        assert!((vals[3] - 2.0).abs() < 1e-9, "Rasterreihe 1 -> wert 2, war {}", vals[3]);

        // Gegenprobe beta=1: linear in der Fuellung -> alle Schritte gleich.
        let vals_lin: Vec<f64> = (0..=3usize)
            .map(|n| {
                let mut p = PlayerBoard::new(0, "P");
                place_special_type_tile_at(&mut p, 0, 0, 0, n, n == 3);
                unlock_progress_beta(&p, &[], 1.0)
            })
            .collect();
        let s01 = vals_lin[1] - vals_lin[0];
        let s12 = vals_lin[2] - vals_lin[1];
        let s23 = vals_lin[3] - vals_lin[2];
        assert!(
            (s01 - s12).abs() < 1e-9 && (s12 - s23).abs() < 1e-9,
            "bei beta=1 sollten alle Schritte gleich schwer sein: {s01} {s12} {s23}"
        );
    }

    #[test]
    fn unlock_progress_beta_is_booked_per_slot_not_pooled() {
        // Zweite Kernanforderung: zwei Slots mit je 1 von 3 gefuellten Feldern
        // muessen bei `beta>1` WENIGER liefern als EIN Slot mit 2 von 3 --
        // sonst waere der Term ueber das Brett gepoolt statt je Slot gebucht.
        // pool[4] (sp_idx=1) und pool[6] (sp_idx=0) liegen BEIDE in der
        // oberen Haelfte ihres Slots (sp_idx/2==0) -- bei slot_row=0 also
        // BEIDE Rasterreihe 0 -> wert=1 fuer beide, damit die Rasterreihen-
        // Gewichtung (siehe Funktionskommentar) den Vergleich nicht
        // verfaelscht.
        let beta = 2.0;
        let mut distributed = PlayerBoard::new(0, "P");
        place_special_type_tile_at(&mut distributed, 0, 0, 4, 1, false);
        place_special_type_tile_at(&mut distributed, 0, 1, 6, 1, false); // pool[6]: ebenfalls Special-Typ, sp_idx=0

        let mut concentrated = PlayerBoard::new(0, "P");
        place_special_type_tile_at(&mut concentrated, 0, 0, 4, 2, false);

        let distributed_val = unlock_progress_beta(&distributed, &[], beta);
        let concentrated_val = unlock_progress_beta(&concentrated, &[], beta);
        assert!(
            concentrated_val > distributed_val,
            "konzentriert ({concentrated_val}) sollte bei beta=2 mehr sein als verteilt ({distributed_val})"
        );
        // Exakte Gegenprobe (wert=1 je Slot): verteilt = 2 * 1*(1/3)^2 = 2/9; konzentriert = 1*(2/3)^2 = 4/9.
        assert!((distributed_val - 2.0 / 9.0).abs() < 1e-9, "war {distributed_val}");
        assert!((concentrated_val - 4.0 / 9.0).abs() < 1e-9, "war {concentrated_val}");

        // Gegenprobe beta=1: linear -> Verteilung ist irrelevant, beide gleich.
        let distributed_lin = unlock_progress_beta(&distributed, &[], 1.0);
        let concentrated_lin = unlock_progress_beta(&concentrated, &[], 1.0);
        assert!((distributed_lin - concentrated_lin).abs() < 1e-9);
    }

    #[test]
    fn unlock_progress_beta_weights_by_grid_row_lower_slots_worth_more() {
        // Nutzer-Korrektur 2026-08-11: der Bonus-Anteil ist NICHT flach
        // (`bonus_points`), sondern nach der Rasterreihe gewichtet (1..6,
        // exakt `round_end.rs::check_special_trigger`) -- hoehere Rasterreihe
        // = mehr Punkte, die UNTERE Slot-Reihe (sr=2, Rasterreihen 4/5,
        // wert 5/6) ist also die WERTVOLLERE, nicht die obere (sr=0,
        // Rasterreihen 0/1, wert 1/2). Gleicher Fuellstand (n=1), gleiche
        // sp_idx-Unterposition (0, "obere Haelfte" des jeweiligen Slots) --
        // NUR `slot_row` unterscheidet sich. Muss den Faktor 5/1 liefern
        // (wert 5 unten vs. wert 1 oben). Sanity-Check-Bezug (Auftrag):
        // gemessen bleibt ein Special in der unteren Slot-Reihe in ~84% der
        // Partien leer, in der oberen nur ~13% -- die KI laesst also
        // tatsaechlich die TEUERSTEN Felder liegen, ein flach gewichteter
        // Term wuerde diese Rangfolge (und damit den Trainingsanreiz) NICHT
        // abbilden.
        let beta = 2.0;
        let mut upper = PlayerBoard::new(0, "P");
        place_special_type_tile_at(&mut upper, 0, 0, 15, 1, false); // pool[15]: sp_idx=0
        let mut lower = PlayerBoard::new(0, "P");
        place_special_type_tile_at(&mut lower, 2, 0, 15, 1, false);

        let val_upper = unlock_progress_beta(&upper, &[], beta);
        let val_lower = unlock_progress_beta(&lower, &[], beta);
        assert!(
            val_lower > val_upper,
            "untere Slot-Reihe (Rasterreihe 4, wert 5) sollte mehr wert sein als obere \
             (Rasterreihe 0, wert 1): {val_lower} vs {val_upper}"
        );
        assert!(
            (val_lower / val_upper - 5.0).abs() < 1e-9,
            "Faktor sollte exakt 5 sein (wert 5 vs wert 1), war {}",
            val_lower / val_upper
        );
        // Exakte Werte: 1*(1/3)^2 vs 5*(1/3)^2.
        assert!((val_upper - (1.0f64 / 3.0).powi(2)).abs() < 1e-9);
        assert!((val_lower - 5.0 * (1.0f64 / 3.0).powi(2)).abs() < 1e-9);
    }

    #[test]
    fn unlock_progress_beta_criterion6_addend_is_row_independent() {
        // Gegenprobe zur Rasterreihen-Gewichtung: die gilt NUR fuer den
        // Bonus-Anteil. Kriterium 6 (Handbuch Nr. 7, Code-Index 6) bleibt
        // FLACH -3 je leerem Spezialfeld, unabhaengig von der Rasterreihe
        // (Nutzer-Korrektur 2026-08-11 -- zwei unabhaengige Regeln, nicht
        // eine). Nachweis: der Zuschlag von Platte 6 ist bei gleichem
        // Fuellstand identisch, ob das leere Spezialfeld in der oberen oder
        // unteren Slot-Reihe liegt (obwohl der Bonus-Anteil selbst dort um
        // Faktor 5 differiert, siehe voriger Test).
        let beta = 2.0;
        let mut upper = PlayerBoard::new(0, "P");
        place_special_type_tile_at(&mut upper, 0, 0, 15, 1, false);
        let mut lower = PlayerBoard::new(0, "P");
        place_special_type_tile_at(&mut lower, 2, 0, 15, 1, false);

        let delta_upper = unlock_progress_beta(&upper, &[6], beta) - unlock_progress_beta(&upper, &[], beta);
        let delta_lower = unlock_progress_beta(&lower, &[6], beta) - unlock_progress_beta(&lower, &[], beta);
        assert!((delta_upper - (-3.0)).abs() < 1e-9, "war {delta_upper}");
        assert!((delta_lower - (-3.0)).abs() < 1e-9, "war {delta_lower}");
        assert!(
            (delta_upper - delta_lower).abs() < 1e-12,
            "Kriterium-6-Zuschlag sollte reihenunabhaengig identisch sein: {delta_upper} vs {delta_lower}"
        );
    }

    #[test]
    fn unlock_progress_beta_pays_regardless_of_scoring_tile_ids() {
        // UNGEGATET: der Kuppel-Bonus-Anteil muss auch OHNE Platte 6 in
        // `tile_ids` zahlen (er ist ein Spielzug-Bonus, keine Wertungsplatte).
        let mut p = PlayerBoard::new(0, "P");
        place_special_type_tile_at(&mut p, 0, 0, 0, 2, false);
        let without_6 = unlock_progress_beta(&p, &[0, 1, 2], 2.0);
        assert!(without_6 > 0.0, "Kuppel-Bonus-Anteil muss unabhaengig von scoring_tile_ids zahlen");
        // Und identisch, ob tile_ids leer ist oder andere (Nicht-6-)Platten enthaelt.
        let empty_ids = unlock_progress_beta(&p, &[], 2.0);
        assert!((without_6 - empty_ids).abs() < 1e-12);

        // Kriterium 6 kommt NUR zusaetzlich dazu, wenn 6 explizit gewaehlt ist
        // -- exakt -3 je leerem Special-Feld (dieselbe Definition wie in
        // `wertung_progress`).
        let mut q = PlayerBoard::new(0, "P");
        place_special_type_tile_at(&mut q, 0, 0, 0, 0, false); // 1 Special-Slot, nichts gefuellt
        let with_6 = unlock_progress_beta(&q, &[6], 2.0);
        let no_6 = unlock_progress_beta(&q, &[], 2.0);
        assert!(
            (with_6 - no_6 - (-3.0)).abs() < 1e-9,
            "Kriterium 6 sollte exakt -3 pro leerem Special zusaetzlich beitragen (with_6={with_6}, no_6={no_6})"
        );
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
