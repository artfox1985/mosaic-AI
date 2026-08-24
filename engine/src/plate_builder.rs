//! Spieler-Abstraktion "Plattenbauer" (Nutzer-Auftrag 2026-08-13,
//! Architektur-Fahrplan Punkt 5 aus `evaluations/STATUS.md`).
//!
//! Ein `Plattenbauer` ist eine Entscheidungsschicht UEBER dem Netz-/
//! Heuristik-Spieler mit genau drei Entscheidungspunkten -- Drafting-Vorzug
//! (Stein-Zug), Kuppelplatten-Wahl-Vorzug, Tiling-Routing-Vorzug --, so wie
//! `column_build.rs` sie fuer EIN Kriterium (Kriterium 1, Vertikale Reihen)
//! bereits konkret implementiert. Diese Datei zieht das Muster als Trait
//! nach und macht es UEBER `MOSAIC_PLATTENBAU=<0..7|auto>` fuer alle 8
//! Wertungskriterien nutzbar (`scoring.rs::ALL_SCORING_TILES`), ohne
//! `column_build.rs` selbst zu aendern.
//!
//! ## Verhaeltnis zum Bestandsknopf `MOSAIC_SPALTENBAU`
//!
//! `MOSAIC_SPALTENBAU` bleibt der WOERTLICHE Altpfad: ist er aktiv, loest
//! [`active_builder`] IMMER auf den Spaltenbauer-Wrapper auf, der die
//! bestehenden `column_build::{preference_move,preference_dome_choice,preference_tiling_step}`
//! UNVERAENDERT aufruft -- Verhaltens-Identitaet ist damit durch reine
//! Delegation garantiert, nicht durch eine Nachbildung (siehe
//! `plattenbauer_regression_test.rs`-Aequivalenztests unten). `MOSAIC_
//! PLATTENBAU=1` (derselbe Kriterium-Index, aber OHNE den Altknopf) nutzt
//! stattdessen die HIER neu gebaute generische Zellen-Mechanik mit
//! Spalten-Geometrie -- ein zweiter Codepfad fuer dasselbe Kriterium, bewusst
//! in Kauf genommen (siehe Bericht, "eigene Entscheidungen"): eine
//! Verschmelzung haette `column_build.rs`s Signaturen aendern und alle dortigen
//! Tests neu durchdenken muessen, ohne zusaetzlichen Nutzen fuer die
//! Abnahme.
//!
//! ## Die generische Zellen-Mechanik
//!
//! Vier der acht Kriterien sind reine GEOMETRIE-Varianten derselben Aufgabe
//! "liefere die richtige Farbe an eine Menge von Zellen, die zusammen
//! gewertet werden": Zeilen (0, Zeilenzellen), Spalten (1, Spaltenzellen,
//! analog `column_build.rs`), Diagonalen (2, zwei Diagonalen), Ecken (5, vier
//! 2x2-Slots). Fuer sie reicht EINE generische Kosten-/Vorzugs-Mechanik
//! ueber eine explizite Zellenliste `&[(row, col)]` -- portiert aus
//! `column_build.rs`s Kosten-/Auswahlformeln (`special_cost`,
//! `scarcity_surcharge`, `cell_value`, Toleranzband + Seed-Streuung), die
//! dafuer sichtbar gemacht wurden (`pub(crate)`). Die drei uebrigen
//! Kriterien -- Mehrfarbig (3, Jokerfelder), Rand (4, additiv-farbfrei),
//! Spezial (6, Slot-Vervollstaendigung) -- brauchen KEINE Kandidatenauswahl
//! (ihr Zielzellen-Satz ist eindeutig aus dem Brett ablesbar, keine
//! Alternative abzuwaegen) und rufen die generische Vorzugs-/Tiling-Mechanik
//! direkt mit diesem festen Satz auf. Farbenreiche Reihen (7) teilt sich die
//! Zeilen-Kandidatenauswahl, bekommt aber eine EIGENE Kuppelplatten-Logik
//! (Farbvielfalt statt Farbtreffer).

use crate::board::PlayerBoard;
use crate::dome::{rotation_indices, DomeSpace, SpaceType};
use crate::moves::{Action, PendingDomeChoice, PlaceDomeTileMove};
use crate::state::GameState;
use crate::tiling_solver::TilingStep;

// ── Der Trait: drei Entscheidungspunkte ─────────────────────────────────────

/// Spieler-Abstraktion ueber den drei Entscheidungspunkten, die
/// `column_build.rs` fuer Kriterium 1 konkret implementiert (Modul-Doku dort).
/// Jede Methode ist ein reiner PRAEFERENZ-Vorschlag (kein Verbot, keine
/// Blattwert-Verschiebung) -- `None` bedeutet "kein Vorschlag, Netz/Heuristik
/// entscheidet frei", genau wie bei `column_build.rs` und `provocation.rs`.
pub(crate) trait Plattenbauer {
    /// Drafting-Vorzug: ein Stein-Zug (`Action::Stone`), der ein Zielfeld
    /// dieses Kriteriums bedient.
    fn drafting_preference(&self, state: &GameState) -> Option<Action>;
    /// Kuppelplatten-Wahl-Vorzug: welche Platte/welcher Slot/welche Rotation
    /// (`Action::ChooseDomeSlot`/`Action::ChooseDomeRotation`).
    fn dome_preference(&self, state: &GameState) -> Option<Action>;
    /// Tiling-Routing-Vorzug: welcher naechste Tiling-Schritt.
    fn tiling_preference(&self, state: &GameState, pi: usize) -> Option<TilingStep>;
}

// ── Aktivierung: MOSAIC_PLATTENBAU=<0..7|auto>, MOSAIC_SPALTENBAU hat Vorrang ──

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum Modus {
    Aus,
    Fest(usize),
    Auto,
}

fn mode_env() -> Modus {
    static CELL: std::sync::OnceLock<Modus> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| match std::env::var("MOSAIC_PLATTENBAU") {
        Err(_) => Modus::Aus,
        Ok(raw) => {
            let v = raw.trim();
            if v.is_empty() {
                Modus::Aus
            } else if v.eq_ignore_ascii_case("auto") {
                Modus::Auto
            } else {
                match v.parse::<usize>() {
                    Ok(k) if k <= 7 => Modus::Fest(k),
                    _ => {
                        eprintln!(
                            "WARNUNG: MOSAIC_PLATTENBAU={raw:?} ungueltig \
                             (erwartet eine Ziffer 0..7 oder \"auto\") -- bleibt AUS."
                        );
                        Modus::Aus
                    }
                }
            }
        }
    })
}

#[cfg(test)]
thread_local! {
    static MODUS_OVERRIDE: std::cell::Cell<Option<Modus>> = const { std::cell::Cell::new(None) };
}

#[cfg(test)]
pub(crate) fn set_mode_override_for_test(m: Option<Modus>) {
    MODUS_OVERRIDE.with(|c| c.set(m));
}

fn mode() -> Modus {
    #[cfg(test)]
    {
        if let Some(m) = MODUS_OVERRIDE.with(|c| c.get()) {
            return m;
        }
    }
    mode_env()
}

thread_local! {
    /// Partie-Seed fuer die generische Kandidatenwahl (Auto-Kriterium +
    /// Kandidaten-Streuung bei Kosten-Gleichstand) -- gleiches Muster wie
    /// `column_build::PARTIE_SEED`. [`set_game_seed`] versorgt BEIDE (siehe
    /// dort), damit self_play.rs nur noch EINE Stelle aufrufen muss.
    static PARTIE_SEED: std::cell::Cell<Option<u64>> = const { std::cell::Cell::new(None) };
}

/// Setzt (oder loescht mit `None`) den Partie-Seed fuer DIESEN Thread -- fuer
/// die generische Mechanik HIER und (Kaskade) fuer `column_build::PARTIE_SEED`,
/// damit self_play.rs an den vier Hook-Stellen nur noch die Abstraktion
/// aufrufen muss, statt zwei Module einzeln zu versorgen. Aufrufer MUSS am
/// Partieende (oder vor der naechsten Partie desselben Threads) mit `None`
/// ueberschreiben (Leck-Warnung wie bei `column_build::set_game_seed`).
pub(crate) fn set_game_seed(seed: Option<u64>) {
    PARTIE_SEED.with(|c| c.set(seed));
    crate::column_build::set_game_seed(seed);
}

/// Deterministische Mischung Seed -> Index `0..n` -- identisches SplitMix64-
/// Muster wie `column_build::index_from_seed`/`provocation::column_from_seed`
/// (Projekt-Konvention: diese kleine Mischfunktion wird je Modul dupliziert
/// statt geteilt, siehe dortige Kommentare).
fn index_from_seed(seed: u64, n: usize) -> usize {
    if n == 0 {
        return 0;
    }
    let mut z = seed.wrapping_add(0x9E37_79B9_7F4A_7C15);
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^= z >> 31;
    (z % n as u64) as usize
}

/// Welches Kriterium (0..7) ist JETZT aktiv, oder `None`. `MOSAIC_SPALTENBAU`
/// hat Vorrang (liefert immer Kriterium 1 ueber den Legacy-Wrapper, siehe
/// [`active_builder`]); sonst entscheidet `MOSAIC_PLATTENBAU`. `Auto` streut
/// ueber `state.scoring_tile_ids` -- die tatsaechlich fuer DIESE Partie
/// gezogenen 3 Platten (`scoring.rs`-Doku: "zu Spielbeginn werden 3 ...
/// gewaehlt"), nicht ueber alle 8 -- ein Kriterium ohne Platte auf dem Tisch
/// waere ein wirkungsloser Vorzug.
// Noch UNVERDRAHTET: gedacht fuer die auto-Zielwahl ueber die aktiven Platten;
// die heutige auto-Streuung waehlt direkt. Bleibt als vorbereiteter Baustein.
#[allow(dead_code)]
fn active_criterion(state: &GameState) -> Option<usize> {
    if crate::column_build::is_active() {
        return Some(1);
    }
    match mode() {
        Modus::Aus => None,
        Modus::Fest(k) => Some(k),
        Modus::Auto => auto_criterion(state),
    }
}

fn auto_criterion(state: &GameState) -> Option<usize> {
    let ids = &state.scoring_tile_ids;
    if ids.is_empty() {
        return None; // defensiv: vor Partie-Setup oder in einem Test ohne Platten.
    }
    match PARTIE_SEED.with(|c| c.get()) {
        None => Some(ids[0]),
        Some(seed) => Some(ids[index_from_seed(seed, ids.len())]),
    }
}

// ── Dispatch: acht zustandslose Bauer + der Legacy-Wrapper ──────────────────

struct SpaltenbauerLegacy;
impl Plattenbauer for SpaltenbauerLegacy {
    fn drafting_preference(&self, state: &GameState) -> Option<Action> {
        crate::column_build::preference_move(state)
    }
    fn dome_preference(&self, state: &GameState) -> Option<Action> {
        crate::column_build::preference_dome_choice(state)
    }
    fn tiling_preference(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        crate::column_build::preference_tiling_step(state, pi)
    }
}

static SPALTENBAUER_LEGACY: SpaltenbauerLegacy = SpaltenbauerLegacy;
static ZEILENBAUER: Zeilenbauer = Zeilenbauer;
static SPALTENBAUER_GENERISCH: SpaltenbauerGenerisch = SpaltenbauerGenerisch;
static DIAGONALENBAUER: Diagonalenbauer = Diagonalenbauer;
static MEHRFARBIGBAUER: Mehrfarbigbauer = Mehrfarbigbauer;
static RANDBAUER: Randbauer = Randbauer;
static ECKENBAUER: Eckenbauer = Eckenbauer;
static SPEZIALBAUER: Spezialbauer = Spezialbauer;
static FARBENREICHBAUER: Farbenreichbauer = Farbenreichbauer;

fn builder_for(kriterium: usize) -> &'static dyn Plattenbauer {
    match kriterium {
        0 => &ZEILENBAUER,
        1 => &SPALTENBAUER_GENERISCH,
        2 => &DIAGONALENBAUER,
        3 => &MEHRFARBIGBAUER,
        4 => &RANDBAUER,
        5 => &ECKENBAUER,
        6 => &SPEZIALBAUER,
        7 => &FARBENREICHBAUER,
        _ => &ZEILENBAUER, // defensiv; active_criterion liefert nie >7.
    }
}

fn active_builder(state: &GameState) -> Option<&'static dyn Plattenbauer> {
    if crate::column_build::is_active() {
        return Some(&SPALTENBAUER_LEGACY);
    }
    match mode() {
        Modus::Aus => None,
        Modus::Fest(k) => Some(builder_for(k)),
        Modus::Auto => auto_criterion(state).map(builder_for),
    }
}

/// Aufrufstellen: die vier Drafting-Hook-Stellen in `self_play.rs`, ersetzt
/// `crate::column_build::preference_move(&game.state)` in der `.or_else(...)`-Kette.
///
/// `PREREG_opponent_disruption.md` §2: NACH dem aktiven Bauer haengt der
/// Stoerungs-Vorzug (`provocation::disruption_preference`) als `.or_else`-Zweig
/// an -- "erst die eigene Vollendung [des aktiven Bauers fuer DIESEN Zug],
/// dann die Stoerung [als Fallback, wenn der aktive Bauer hier nichts
/// vorschlaegt]" (Nutzer-Domaenenwissen, `docs/domain_knowledge.md`
/// "Spielstrategie aus Nutzer-Praxis" Punkt 4). Wirkt eigenstaendig ueber
/// den Knopf `MOSAIC_OPPONENT_DISRUPTION`, unabhaengig davon, ob ueberhaupt
/// ein Bauer (`MOSAIC_PLATTENBAU`/`MOSAIC_SPALTENBAU`) aktiv ist -- bei
/// unbesetztem Knopf liefert `disruption_preference` sofort `None` (Bestandsschutz).
pub(crate) fn drafting_preference(state: &GameState) -> Option<Action> {
    active_builder(state)
        .and_then(|b| b.drafting_preference(state))
        .or_else(|| crate::provocation::disruption_preference(state))
}

/// Aufrufstellen: dieselben vier Hook-Stellen, ersetzt
/// `crate::column_build::preference_dome_choice(&game.state)`.
pub(crate) fn dome_preference(state: &GameState) -> Option<Action> {
    active_builder(state).and_then(|b| b.dome_preference(state))
}

/// Aufrufstelle: der Tiling-Hook in `self_play.rs`, ersetzt
/// `crate::column_build::preference_tiling_step(&game.state, pi)`.
pub(crate) fn tiling_preference(state: &GameState, pi: usize) -> Option<TilingStep> {
    active_builder(state).and_then(|b| b.tiling_preference(state, pi))
}

// ── Generische Zellen-Mechanik (Kriterien 0/1/2/5, Portierung aus column_build.rs) ──

/// Kosten EINER Zelle -- delegiert vollstaendig an `column_build::cell_cost`
/// (§16: dieselbe Formel, jetzt auch fuer die Special-Zellen-Slot-Nachbarn
/// gebraucht, deshalb dort `pub(crate)` und hier keine eigene Kopie mehr,
/// siehe CLAUDE.md "Bestehendes wiederverwenden"). Verifiziert aequivalent
/// per Test unten
/// (`cells_cost_matches_column_cost_for_column_geometry`).
fn cells_cost(player: &PlayerBoard, zellen: &[(usize, usize)], verbleibend: &[i64; 5]) -> f64 {
    zellen.iter().map(|&(r, c)| crate::column_build::cell_cost(player, r, c, verbleibend)).sum()
}

/// Toleranzband, identische Kalibrierung wie `column_build::SPALTEN_TOLERANZ`
/// (dieselbe Kosten-Skala, siehe dortige Begruendung).
const ZIEL_TOLERANZ: f64 = 0.5;

/// Waehlt einen Kandidaten-Index aus `kosten` -- guenstigster, oder bei
/// mehreren nahen (`ZIEL_TOLERANZ`) Kandidaten seed-gestreut, sonst der
/// kleinste Index (stabiler Tie-Break). Generalisierung von
/// `column_build::choose_column` auf beliebig viele Kandidaten.
fn choose_candidate(kosten: &[f64], seed: Option<u64>) -> usize {
    let min_kosten = kosten.iter().cloned().fold(f64::INFINITY, f64::min);
    let kandidaten: Vec<usize> = (0..kosten.len()).filter(|&i| kosten[i] - min_kosten <= ZIEL_TOLERANZ).collect();
    if kandidaten.len() <= 1 {
        return kandidaten.first().copied().unwrap_or(0);
    }
    match seed {
        None => kandidaten[0],
        Some(s) => kandidaten[index_from_seed(s, kandidaten.len())],
    }
}

/// §18 (Diagonalen-Baustein): wie [`target_cells_generic`], aber mit
/// `column_build::cell_cost_smart` statt der geteilten (§16/§17-Schalter-
/// abhaengigen) [`cells_cost`] -- fuer Bauern mit einer EIGENEN,
/// unabhaengig validierten Special-Zellen-Uebernahme (siehe dortige Doku).
fn target_cells_generic_smart(state: &GameState, pi: usize, kandidaten: &[Vec<(usize, usize)>]) -> Option<Vec<(usize, usize)>> {
    if kandidaten.is_empty() {
        return None;
    }
    let player = &state.players[pi];
    let verbleibend = crate::provocation::remaining_colors(state);
    let kosten: Vec<f64> = kandidaten
        .iter()
        .map(|z| z.iter().map(|&(r, c)| crate::column_build::cell_cost_smart(player, r, c, &verbleibend)).sum())
        .collect();
    let seed = PARTIE_SEED.with(|c| c.get());
    let idx = choose_candidate(&kosten, seed);
    Some(kandidaten[idx].clone())
}

/// Loest die aktive Zielzellen-Menge aus einer Kandidatenliste auf --
/// Generalisierung von `column_build::target_column` auf beliebige Geometrien.
fn target_cells_generic(state: &GameState, pi: usize, kandidaten: &[Vec<(usize, usize)>]) -> Option<Vec<(usize, usize)>> {
    let idx = target_index_generic(state, pi, kandidaten)?;
    Some(kandidaten[idx].clone())
}

/// Wie [`target_cells_generic`], liefert aber den INDEX des gewaehlten
/// Kandidaten statt seiner Zellen. Gebraucht von der Orientierungswahl der
/// Dreiecks-Huelle, die aus der Wahl zwischen zwei Randspalten eine
/// Orientierung ableiten muss -- ueber denselben Kostenvergleich und
/// dieselbe Seed-Streuung wie jeder andere Bauer, statt einer zweiten,
/// separat zu pflegenden Regel.
fn target_index_generic(state: &GameState, pi: usize, kandidaten: &[Vec<(usize, usize)>]) -> Option<usize> {
    if kandidaten.is_empty() {
        return None;
    }
    let player = &state.players[pi];
    let verbleibend = crate::provocation::remaining_colors(state);
    let kosten: Vec<f64> = kandidaten.iter().map(|z| cells_cost(player, z, &verbleibend)).collect();
    let seed = PARTIE_SEED.with(|c| c.get());
    Some(choose_candidate(&kosten, seed))
}

/// Drafting-Vorzug ueber einer beliebigen Zielzellen-Menge -- Generalisierung
/// von `provocation::preference_move_for_column`. Fuer eine Reihe `r`, die in
/// `zellen` mit MEHREREN Eintraegen vorkommt (Zeilen-/Ecken-Geometrie), zaehlt
/// "qualifiziert", wenn IRGENDEINE offene Zielzelle dieser Reihe die
/// angebotene Farbe fordert (eine Musterreihe fuehrt ohnehin nur eine Farbe
/// je Zug, welche der mehreren Zielzellen davon profitiert, ist fuer die
/// Zugwahl selbst gleichgueltig).
pub(crate) fn preference_move_for_cells(state: &GameState, zellen: &[(usize, usize)]) -> Option<Action> {
    preference_move_for_cells_weighted(state, zellen, &EINHEITSKARTE)
}

/// Wie [`preference_move_for_cells`], aber mit der Zielkarte als drittem
/// Sortierschluessel.
///
/// Warum genau dort und nicht weiter vorn: Farbknappheit und Reihenfuellstand
/// sind die beiden Schluessel, unter denen die vier gemessenen Bauschritte
/// gelaufen sind -- sie bleiben unberuehrt. Der DRITTE Schluessel war bisher
/// `r` AUFSTEIGEND und bevorzugte damit die oberen Rasterzeilen. Solange die
/// Zielmenge eine einzelne Spalte war, hat das kaum etwas entschieden; mit
/// der Prio-Leiter qualifizieren sich viel mehr Zuege, und ein Gleichstand
/// fiele sonst systematisch nach OBEN -- also gegen Prio 1 und 2.
///
/// Gewertet wird die BESTE Zielzelle, die der Zug in seiner Reihe bedienen
/// kann. Nicht die Summe: eine Musterreihe legt je Abschluss genau EINEN
/// Stein, mehrere bedienbare Zellen sind also Alternativen und keine
/// Addition -- dieselbe Begruendung, aus der `heuristic_v2` das Maximum statt
/// der Summe nimmt.
///
/// Mit [`EINHEITSKARTE`] ist der Rang fuer jede Zelle gleich, der Tie-Break
/// faellt wie bisher auf `r` aufsteigend zurueck: byte-identisch zum Bestand.
pub(crate) fn preference_move_for_cells_weighted(
    state: &GameState,
    zellen: &[(usize, usize)],
    karte: &Zielkarte,
) -> Option<Action> {
    if state.phase != crate::state::Phase::Drafting || state.round_number > 4 {
        return None;
    }
    let player = &state.players[state.current_player];
    let verbleibend = crate::provocation::remaining_colors(state);
    let moves = crate::validation::generate_valid_moves(state);
    let mut best: Option<(i64, i32, i64, i32, crate::moves::Move)> = None;
    for m in moves {
        let r = m.place.row_index;
        if !(0..=5).contains(&r) {
            continue;
        }
        let r = r as usize;
        let mut bestes: Option<f64> = None;
        for &(zr, zc) in zellen {
            if zr != r {
                continue;
            }
            let Some(sp) = player.dome_grid.get_space(zr, zc) else { continue };
            if sp.is_filled() {
                continue;
            }
            let bedient = match sp.space_type {
                SpaceType::Wild => true,
                SpaceType::Normal => sp.required_color == Some(m.take.color),
                SpaceType::Special => false,
            };
            if bedient && bestes.is_none_or(|b| karte[zr][zc] > b) {
                bestes = Some(karte[zr][zc]);
            }
        }
        let Some(bestes) = bestes else { continue };
        let zeile = &player.pattern_lines[r];
        let fuellung = zeile.tiles.len() as i32;
        let knappheit = crate::provocation::color_index(m.take.color).map(|i| verbleibend[i]).unwrap_or(i64::MAX);
        // Hoeheres Gewicht = kleinerer Rang, damit die bestehende
        // "kleiner gewinnt"-Ordnung unveraendert bleibt. Ganzzahlig
        // (Faktor 1000), weil der Schluessel sonst kein `Ord` hat; die
        // gesetzten Gewichte sind ganze Zahlen.
        let rang = -((bestes * 1000.0) as i64);
        let kandidat = (knappheit, -fuellung, rang, r as i32, m);
        let besser = best
            .as_ref()
            .map_or(true, |(k, f, g, rr, _)| (kandidat.0, kandidat.1, kandidat.2, kandidat.3) < (*k, *f, *g, *rr));
        if besser {
            best = Some(kandidat);
        }
    }
    best.map(|(_, _, _, _, m)| Action::Stone(m))
}

/// Score einer (Kachel, Slot, Rotation)-Kombination gegen eine beliebige
/// Zielzellen-Menge -- Generalisierung von `column_build::slot_score`: statt
/// nur die zwei Zellen EINER Spalte je Slot zu pruefen, werden alle vier
/// Platzierungspositionen des Slots gegen die Zielzellen-Mitgliedschaft
/// geprueft. Fuer eine Spalten-Zielzellenliste ist das rechnerisch identisch
/// zu `slot_score` (jeder Slot hat pro Spalten-Offset genau zwei Positionen,
/// exakt die dort gelesenen `idx[cc]`/`idx[cc+2]`).
///
/// `karte` skaliert den Beitrag je ZIELZELLE (Nutzer-Vorgabe 2026-08-24: "die
/// notwendigen/vorteilhaften kuppelplatten sollten dann ebenfalls
/// dementsprechend gelegt werden"). Ohne diesen Faktor waere der Platte eine
/// Zelle in Rasterzeile 0 genauso viel wert wie eine in Rasterzeile 5 -- und
/// gerade die untere ist die knappe. `wert` tauscht die Zellenbewertung aus
/// (Bestand gegen Huelle, siehe [`envelope_cell_value`]).
/// [`EINHEITSKARTE`] plus [`legacy_cell_value`] stellen das
/// Bestandsverhalten her.
fn slot_score_generic(
    player: &PlayerBoard,
    tile: &crate::dome::DomeTile,
    slot_row: usize,
    slot_col: usize,
    rotation: u32,
    zellen: &[(usize, usize)],
    karte: &Zielkarte,
    wert: fn(&PlayerBoard, usize, usize, &DomeSpace) -> f64,
) -> Option<f64> {
    let idx = rotation_indices(rotation)?;
    let mut summe = 0.0;
    let mut beruehrt = false;
    for i in 0..4usize {
        let row = slot_row * 2 + i / 2;
        let col = slot_col * 2 + i % 2;
        if !zellen.contains(&(row, col)) {
            continue;
        }
        beruehrt = true;
        summe += karte[row][col] * wert(player, row, col, &tile.spaces[idx[i]]);
    }
    if beruehrt {
        Some(summe)
    } else {
        None
    }
}

/// Kuppelplatten-Wahl-Vorzug ueber einer beliebigen Zielzellen-Menge --
/// Generalisierung von `column_build::preference_dome_choice`. Anders als dort wird
/// NICHT nach `slot_col` vorgefiltert (eine Zeilen-/Ecken-Zielmenge kann
/// mehrere Slot-Spalten beruehren) -- [`slot_score_generic`]s `beruehrt`-Flag
/// uebernimmt den gleichen Ausschluss implizit (Score 0, dann durch den
/// `>0.0`-Filter unten verworfen).
pub(crate) fn dome_preference_for_cells(state: &GameState, zellen: &[(usize, usize)]) -> Option<Action> {
    dome_preference_for_cells_weighted(state, zellen, &EINHEITSKARTE, legacy_cell_value)
}

/// Wie [`dome_preference_for_cells`], aber mit Zielkarte und austauschbarer
/// Zellenbewertung (siehe [`slot_score_generic`]). Die Bestandsfassung ist
/// der Sonderfall [`EINHEITSKARTE`] plus [`legacy_cell_value`].
pub(crate) fn dome_preference_for_cells_weighted(
    state: &GameState,
    zellen: &[(usize, usize)],
    karte: &Zielkarte,
    wert: fn(&PlayerBoard, usize, usize, &DomeSpace) -> f64,
) -> Option<Action> {
    let player = &state.players[state.current_player];

    if let Some(choice) = &state.pending_dome_choice {
        return match choice {
            PendingDomeChoice::FromDisplay { dome_tile_id, slot_row, slot_col } => {
                let tile = state.dome_display.iter().find(|t| t.tile_id == *dome_tile_id)?;
                let mut best: Option<(f64, u32)> = None;
                for rot in [0u32, 90, 180, 270] {
                    let m = PlaceDomeTileMove {
                        dome_tile_id: *dome_tile_id,
                        slot_row: *slot_row,
                        slot_col: *slot_col,
                        rotation: rot,
                    };
                    if crate::game::validate_dome_move(state, &m).is_some() {
                        continue;
                    }
                    if let Some(score) = slot_score_generic(player, tile, *slot_row, *slot_col, rot, zellen, karte, wert) {
                        if best.map_or(true, |(bs, _)| score > bs) {
                            best = Some((score, rot));
                        }
                    }
                }
                best.filter(|(s, _)| *s > 0.0).map(|(_, rot)| Action::ChooseDomeRotation(rot))
            }
            PendingDomeChoice::FromDrawStack { .. } => None,
        };
    }

    if !state.pending_stack_draw.is_empty() {
        return None;
    }
    if !player.can_place_dome_tile(state.round_number) || player.has_unplaced_start_tile() {
        return None;
    }
    let mut best: Option<(f64, usize, usize, usize)> = None; // (score, tile_id, slot_row, slot_col)
    for tile in &state.dome_display {
        for &(sr, sc) in &player.dome_grid.empty_slots() {
            let mut best_rot_score: Option<f64> = None;
            for rot in [0u32, 90, 180, 270] {
                let m = PlaceDomeTileMove { dome_tile_id: tile.tile_id, slot_row: sr, slot_col: sc, rotation: rot };
                if crate::game::validate_dome_move(state, &m).is_some() {
                    continue;
                }
                if let Some(score) = slot_score_generic(player, tile, sr, sc, rot, zellen, karte, wert) {
                    if best_rot_score.map_or(true, |b| score > b) {
                        best_rot_score = Some(score);
                    }
                }
            }
            if let Some(score) = best_rot_score {
                if best.as_ref().map_or(true, |(bs, _, _, _)| score > *bs) {
                    best = Some((score, tile.tile_id, sr, sc));
                }
            }
        }
    }
    best.filter(|(s, _, _, _)| *s > 0.0).map(|(_, tid, sr, sc)| {
        Action::ChooseDomeSlot(PlaceDomeTileMove { dome_tile_id: tid, slot_row: sr, slot_col: sc, rotation: 0 })
    })
}

/// Tiling-Routing-Vorzug ueber einer beliebigen Zielzellen-Menge --
/// Generalisierung von `column_build::preference_tiling_step_for_column`: zaehlt
/// gefuellte Zielzellen statt gefuellte Zellen EINER Spalte.
pub(crate) fn tiling_preference_for_cells(state: &GameState, pi: usize, zellen: &[(usize, usize)]) -> Option<TilingStep> {
    tiling_preference_for_cells_weighted(state, pi, zellen, &EINHEITSKARTE)
}

/// Wie [`tiling_preference_for_cells`], aber die Zielzellen zaehlen mit ihrem
/// KARTENGEWICHT statt je 1.
///
/// Bei einer Zielmenge aus einer Spalte war jede Zelle gleich viel wert --
/// sie kamen ohnehin aus sechs verschiedenen Musterreihen. Die Prio-Leiter
/// stellt 28 Zellen auf vier Stufen; ohne Gewichtung waere ein Schritt in
/// eine Nachbarzelle der Stufe 4 einem Schritt in die Randspalte
/// gleichgestellt.
///
/// Mit [`EINHEITSKARTE`] ist die Summe die Anzahl (Einsen sind in f64 exakt
/// darstellbar und exakt summierbar), also byte-identisch zum Bestand.
pub(crate) fn tiling_preference_for_cells_weighted(
    state: &GameState,
    pi: usize,
    zellen: &[(usize, usize)],
    karte: &Zielkarte,
) -> Option<TilingStep> {
    if !(1..=4).contains(&state.round_number) {
        return None;
    }
    let ziel_zellen_summe = |s: &GameState| -> f64 {
        zellen
            .iter()
            .filter(|&&(r, c)| s.players[pi].dome_grid.get_space(r, c).map_or(false, |sp| sp.is_filled()))
            .map(|&(r, c)| karte[r][c])
            .sum()
    };
    let vorher = ziel_zellen_summe(state);
    let cands = crate::tiling_solver::top_k_tilings(state, pi, crate::tiling_solver::MAX_TILING_LEAVES);
    let best = cands
        .into_iter()
        .map(|c| {
            let z = ziel_zellen_summe(&c.final_state);
            (z, c.points, c.first_step)
        })
        .max_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal).then(a.1.cmp(&b.1)))?;
    if best.0 > vorher {
        Some(best.2)
    } else {
        None
    }
}

// ── Geometrie-Bausteine ──────────────────────────────────────────────────────

fn cells_row(r: usize) -> Vec<(usize, usize)> {
    (0..6).map(|c| (r, c)).collect()
}

fn cells_column(c: usize) -> Vec<(usize, usize)> {
    (0..6).map(|r| (r, c)).collect()
}

fn cells_main_diagonal() -> Vec<(usize, usize)> {
    (0..6).map(|i| (i, i)).collect()
}

fn cells_anti_diagonal() -> Vec<(usize, usize)> {
    (0..6).map(|i| (i, 5 - i)).collect()
}

// -- Zielhuelle v2: die Prio-Leiter (Nutzer-Vorgabe 2026-08-24) --------------

/// Gewicht je RASTERZELLE. `0.0` heisst "nicht im Ziel".
type Zielkarte = [[f64; 6]; 6];

/// Neutrale Karte fuer alle Aufrufer, die KEINE Zielgewichtung wollen (jeder
/// Bestands-Bauer). Multiplikation mit exakt `1.0` ist in f64 verlustfrei und
/// die Summe exakt darstellbarer Einsen ebenfalls -- die gewichteten
/// Fassungen sind fuer sie byte-identisch zum Bestand.
const EINHEITSKARTE: Zielkarte = [[1.0; 6]; 6];

/// **HANDGESETZT.** Gewicht je Prioritaetsstufe der Nutzer-Leiter
/// (2026-08-24, erweiterte Fassung), Index 0..4 fuer Prio 3..7:
///
/// 3. **Randspalte fuellen** (Rasterspalte 0 oder 5) -- hoechste Basiswertigkeit.
/// 4. **Zweite Spalte fuellen** (Rasterspalte 1 oder 4), mit Spezialfliese
///    oder Joker auf Rasterzeile 5 (siehe [`envelope_cell_value`]).
/// 5. **Wertungsplatten und Ziele sichern**: Spezialfelder freischalten und
///    Joker-Zellen halten. Steht VOR den kurzen Reihen, weil beides im
///    Lategame skaliert -- ein leeres Spezialfeld kostet `-3`
///    (`scoring.rs`, Zweig 6) und die Freischaltung bringt zusaetzlich eine
///    Gratis-Zelle plus Punkte in Hoehe der Rasterreihe.
/// 6. **Rasterzeile 0 und 1 fuellen**, soweit es geht.
/// 7. **Nachbarn mitnehmen** aus Rasterzeile 2 und 3 -- reiner Tie-Break.
///
/// Prio 0 (Endspiel), 1 (Strafleiste) und 2 (Gegner-Stoerung) stehen bewusst
/// NICHT in dieser Karte. Sie sind keine Routing-Ziele, sondern Sache der
/// SUCHE, und dort schon entschieden: Runde 5 laeuft als exaktes Endspiel
/// (`round5_anchor::applies`, `mcts.rs`), die Strafleiste steckt als
/// `round_end::projected_unplaceable_penalty` in `player_total_variante`,
/// und die Gegner-Stoerung ist in `PREREG_opponent_disruption_v2.md` als
/// UEBERHOLT abgelegt (nichts gebaut, kein Knopf). Sie hier zu duplizieren
/// hiesse, dieselbe Groesse zweimal zu zaehlen.
///
/// Die Zahlen sind eine SETZUNG, keine Ableitung -- dieselbe Regel wie bei
/// `heuristic_v2::REIHEN_KREDIT`. Gefordert ist nur die strenge Rangfolge.
const PRIO_GEWICHT: [f64; 5] = [5.0, 4.0, 3.0, 2.0, 1.0];

/// Prio 7 bei AKTIVER Diagonalen-Wertungsplatte (`scoring.rs`, Zweig 2).
///
/// Nutzer-Vorgabe 2026-08-24: "bei Verwendung der Diagonale wird Prio 7
/// aufgeweicht". Die Nachbarschafts-Mitnahme ist ohnehin nur Tie-Break; wenn
/// eine Diagonale anliegt, sollen die Zuege dorthin nicht von ihr
/// ueberstimmt werden.
const PRIO7_AUFGEWEICHT: f64 = 0.5;

/// Wertungsplatten-Id der DIAGONALEN (`scoring.rs`, Zweig 2).
const K2_DIAGONALEN: usize = 2;

/// Zielkarte je Orientierung: `0` = Randspalte LINKS (Rasterspalte 0, zweite
/// Spalte 1), `1` = Randspalte RECHTS (5 bzw. 4).
///
/// **Warum genau zwei Orientierungen** (dieselbe Einschraenkung wie
/// `heuristic_v2::triangle_deviation`, Nutzer-Korrektur 2026-08-24): die
/// volle ZEILE liegt immer oben. Eine Spiegelung um die Reihen-Achse
/// verlangte eine volle Rasterzeile 5, gespeist ausschliesslich von
/// Musterreihe 6 (0,74-1,31 Abschluesse je Partie) -- strukturell
/// unerreichbar.
///
/// **Rasterzeile 4 und 5 ausserhalb der beiden Spalten bekommen im Grundbild
/// 0.** Dort kostet jede Zelle einen Abschluss von Musterreihe 5 bzw. 6, und
/// die sind in Prio 3/4 besser angelegt. Die Prio-5-Auflage kann sie wieder
/// anheben -- aber nur fuer Zellen, die ein Spezialfeld freischalten, weil
/// deren Ertrag nicht an einem weiteren Abschluss haengt.
fn target_map(player: &PlayerBoard, tile_ids: &[usize], orientierung: usize) -> Zielkarte {
    let spalte1 = if orientierung == 0 { 0 } else { 5 };
    let spalte2 = if orientierung == 0 { 1 } else { 4 };
    let nachbar = if tile_ids.contains(&K2_DIAGONALEN) { PRIO7_AUFGEWEICHT } else { PRIO_GEWICHT[4] };
    let mut k = [[0.0f64; 6]; 6];
    for r in 0..6 {
        for c in 0..6 {
            k[r][c] = if c == spalte1 {
                PRIO_GEWICHT[0]
            } else if c == spalte2 {
                PRIO_GEWICHT[1]
            } else if r <= 1 {
                PRIO_GEWICHT[3]
            } else if r <= 3 {
                nachbar
            } else {
                0.0
            };
        }
    }
    prio5_overlay(player, &mut k);
    k
}

/// Prio 5 als AUFLAGE auf das Grundbild: hebt Zellen auf `PRIO_GEWICHT[2]`,
/// senkt aber nie eine hoehere Stufe.
///
/// Zwei Sorten, beide aus der Nutzer-Vorgabe ("Spezialfliesen und
/// Jokerplatten"; die uebrigen Wertungsplatten sind durch Prio 3/4/6 bereits
/// gedeckt):
///
/// 1. **Freischalt-Zellen**: die noch leeren REGULAEREN Zellen einer Platte,
///    deren Spezialfeld noch gesperrt ist. Sind alle drei belegt, wird das
///    Spezialfeld automatisch belegt und abgerechnet
///    (`round_end::check_special_trigger`). Diese Zellen duerfen auch aus
///    dem Nichts angehoben werden -- der Ertrag haengt nicht an einem
///    weiteren Musterreihen-Abschluss.
/// 2. **Joker-Zellen** (Wild): nur, wo die Karte ohnehin schon > 0 ist. Ein
///    Joker nimmt die Farbbindung, aber die Zelle kostet weiterhin einen
///    Abschluss ihrer Musterreihe -- das rechtfertigt keinen Eintritt in
///    Rasterzeile 4/5 ausserhalb der beiden Spalten.
fn prio5_overlay(player: &PlayerBoard, k: &mut Zielkarte) {
    let stufe = PRIO_GEWICHT[2];
    for (tr, reihe) in player.dome_grid.dome_slots.iter().enumerate() {
        for (tc, slot) in reihe.iter().enumerate() {
            let Some(slot) = slot else { continue };
            let sp_idx = slot.special_space_idx();
            let special_gesperrt = sp_idx.is_some_and(|i| slot.spaces[i].is_locked);
            for (si, sp) in slot.spaces.iter().enumerate() {
                if sp.is_filled() {
                    continue;
                }
                let (r, c) = (2 * tr + si / 2, 2 * tc + si % 2);
                let freischalt = special_gesperrt && Some(si) != sp_idx;
                let joker = sp.space_type == SpaceType::Wild && k[r][c] > 0.0;
                if (freischalt || joker) && k[r][c] < stufe {
                    k[r][c] = stufe;
                }
            }
        }
    }
}

// -- Prio 0/1/2: die Leiter oberhalb der Zielkarte ---------------------------

/// Phasen-Eskalation je Runde 1..4 (Nutzer-Vorgabe 2026-08-24: "Late Game
/// steigen die Gewichte fuer Prio 0, 1 und 2 exponentiell an").
///
/// Runde 5 kommt nicht vor: dort uebernimmt das exakte Endspiel
/// (`round5_anchor::applies`, kurzgeschlossen in `mcts.rs`), und dieses
/// Routing laeuft ohnehin nur bis Runde 4. Das IST Prio 0 der Leiter -- sie
/// braucht keine eigene Regel, sondern nur die Uebergabe.
const ESKALATION: [f64; 4] = [1.0, 2.0, 4.0, 8.0];

/// Gewicht der Strafleisten-Punkte (Prio 1) im linearen Score.
///
/// **SETZUNG.** Kalibrierung, damit die Rangfolge nachvollziehbar bleibt:
/// eine einzelne Strafliese kostet in Runde 1 `0,5` und liegt damit unter
/// jeder Zielstufe ausser dem Nachbar-Tie-Break; in Runde 4 kostet sie `4,0`
/// und schlaegt alles ausser Prio 3 (`5,0`). Genau das beschreibt die
/// Vorgabe: frueh nachrangig, spaet dominant.
const W_STRAF: f64 = 0.5;

/// Gewicht der Stoerwirkung (Prio 2) im linearen Score.
///
/// **SETZUNG, bewusst am unteren Rand.** `disruption_score` liefert hoechstens
/// so viele Einheiten, wie der Zug Fliesen nimmt (typisch 1-4, selten 6). Bei
/// `0,10` erreicht die Stoerung in Runde 4 hoechstens `0,1*8*6 = 4,8` und
/// bleibt damit knapp unter Prio 3 (`5,0`) -- sie kann den Spaltenbau
/// zuspitzen, aber nicht abraeumen.
///
/// Der Grund fuer die Vorsicht ist gemessen, nicht theoretisch:
/// `PREREG_long_row_payoff.md` B1 hat mit einem zu starken Zusatzanreiz
/// 14,5 Prozentpunkte Siegquote gekostet, und `PREREG_opponent_disruption_v2`
/// liegt als UEBERHOLT ohne gebauten Baustein. Wer die Dosis erhoehen will,
/// misst sie -- eine Ablation ist eine Zeile (`W_STOER = 0.0`).
const W_STOER: f64 = 0.10;

/// Schwelle der Schadensbegrenzung in PUNKTEN (Prio 1, Nutzer-Vorgabe
/// 2026-08-24: "Threshold z. B. ab -4 Punkten").
///
/// Ein Kandidat, der so viel oder mehr kostet, wird nicht mehr bevorzugt --
/// die Entscheidung faellt dann an die Suche zurueck, die die Strafleiste
/// ueber `round_end::projected_unplaceable_penalty` exakt einpreist. Kein
/// hartes Verbot: das Routing ist eine Praeferenz, kein Filter auf der
/// Zugmenge (die Beschneidungs-Bauform ist in `PREREG_provocation.md` §7/§9
/// als spielzerstoerend gemessen).
const STRAF_SCHWELLE_PUNKTE: i32 = -4;

/// Punktekosten, die `zusatz` weitere Fliesen auf der Strafleiste ausloesen.
///
/// Marginal ab dem aktuellen Fuellstand, gedeckelt bei `MAX_BROKEN` -- exakt
/// dieselbe Rechnung wie `round_end::projected_unplaceable_penalty`
/// (`BROKEN_PENALTIES = [-1, -2, -3, -4]`, board.rs:228), damit Routing und
/// Bewertung nicht auseinanderlaufen.
fn floor_points(player: &PlayerBoard, zusatz: usize) -> i32 {
    let vorher = player.broken_tiles.len();
    let nachher = (vorher + zusatz).min(crate::board::MAX_BROKEN);
    (vorher..nachher).map(|i| crate::board::BROKEN_PENALTIES[i]).sum()
}

/// Bestes Zielgewicht, das ein Zug in Musterreihe `r` mit Farbe `farbe`
/// bedienen kann -- `0.0`, wenn er keine Zielzelle bedient.
///
/// MAX statt Summe: eine Musterreihe legt je Abschluss genau EINEN Stein,
/// mehrere bedienbare Zellen sind Alternativen und keine Addition (dieselbe
/// Begruendung, aus der `heuristic_v2` das Maximum nimmt).
fn best_target_weight(
    player: &PlayerBoard,
    karte: &Zielkarte,
    zellen: &[(usize, usize)],
    r: usize,
    farbe: crate::tile::TileColor,
) -> f64 {
    let mut bestes = 0.0f64;
    for &(zr, zc) in zellen {
        if zr != r {
            continue;
        }
        let Some(sp) = player.dome_grid.get_space(zr, zc) else { continue };
        if sp.is_filled() {
            continue;
        }
        let bedient = match sp.space_type {
            SpaceType::Wild => true,
            SpaceType::Normal => sp.required_color == Some(farbe),
            SpaceType::Special => false,
        };
        if bedient && karte[zr][zc] > bestes {
            bestes = karte[zr][zc];
        }
    }
    bestes
}

/// Drafting-Vorzug der Huellen-Variante: die ganze Prio-Leiter als LINEARER
/// Score statt als `if`-Kaskade (Nutzer-Vorgabe 2026-08-24, Implementierungs-
/// Hinweis).
///
/// ```text
/// score = Zielgewicht                       (Prio 3-7, `target_map`)
///       + W_STOER * Eskalation * Stoerung   (Prio 2, `provocation::disruption_score`)
///       + W_STRAF * Eskalation * Strafpunkte (Prio 1, <= 0)
/// ```
///
/// Prio 0 steckt in der Abwesenheit: ab Runde 5 liefert diese Funktion nichts
/// und das exakte Endspiel uebernimmt.
///
/// **Nichts davon ist neu gerechnet.** Stoerwirkung und Strafleisten-Zuwachs
/// kommen aus `provocation.rs` (dort gegen `PREREG_opponent_disruption_v2`
/// gebaut und dokumentiert), die Strafpunkte-Tabelle aus `board.rs`. Neu ist
/// allein, dass sie hier zusammen gewichtet werden.
///
/// **Bodenzuege bekommen nie einen Vorzug** -- gleiche Regel und gleicher
/// Grund wie in `provocation::preference_move_for_color`: Schadensbegrenzung
/// steht ueber Stoerung.
fn envelope_drafting_preference(
    state: &GameState,
    karte: &Zielkarte,
    zellen: &[(usize, usize)],
) -> Option<Action> {
    if state.phase != crate::state::Phase::Drafting || state.round_number > 4 {
        return None;
    }
    let pi = state.current_player;
    let player = &state.players[pi];
    let verbleibend = crate::provocation::remaining_colors(state);
    let bedarf_akut = crate::provocation::opponent_demand_acute(state, pi);
    let eskal = ESKALATION[(state.round_number as usize).clamp(1, 4) - 1];

    let mut best: Option<(f64, i64, i32, i32, crate::moves::Move)> = None;
    for m in crate::validation::generate_valid_moves(state) {
        let r = m.place.row_index;
        if !(0..=5).contains(&r) {
            continue; // Bodenzug
        }
        let r = r as usize;

        // Prio 1: Schadensbegrenzung. Ueber der Schwelle gar nicht erst
        // bevorzugen -- die Suche preist die Strafleiste exakt ein.
        let strafe = floor_points(player, crate::provocation::floor_line_growth(state, pi, &m));
        if strafe <= STRAF_SCHWELLE_PUNKTE {
            continue;
        }
        // Prio 2: verhinderte Gegner-Fliesen zaehlen wie eigener Gewinn.
        let (stoer, _) = crate::provocation::disruption_score(state, &m, &bedarf_akut);
        // Prio 3-7: die Zielkarte.
        let ziel = best_target_weight(player, karte, zellen, r, m.take.color);
        if ziel == 0.0 && stoer == 0 {
            continue; // weder offensiv noch defensiv ein Grund
        }

        let score = ziel + W_STOER * eskal * stoer as f64 + W_STRAF * eskal * strafe as f64;
        // Tie-Break unveraendert zum Bestand: knappste Farbe zuerst, dann die
        // vollste eigene Reihe, dann die kleinste Reihe (stabil).
        let knappheit =
            crate::provocation::color_index(m.take.color).map(|i| verbleibend[i]).unwrap_or(i64::MAX);
        let fuellung = player.pattern_lines[r].tiles.len() as i32;
        // Alle vier Schluessel "groesser ist besser": Score hoch, Farbe knapp
        // (negiert), eigene Reihe voll, Reihenindex klein (negiert).
        let schluessel = (score, -knappheit, fuellung, -(r as i32));
        let besser = best.as_ref().map_or(true, |(bs, bk, bf, br, _)| schluessel > (*bs, *bk, *bf, *br));
        if besser {
            best = Some((schluessel.0, schluessel.1, schluessel.2, schluessel.3, m));
        }
    }
    best.map(|(_, _, _, _, m)| Action::Stone(m))
}

// -- Punkte-Heatmap (Nutzer-Vorschlag 2026-08-25) ---------------------------

/// Zielkarte aus EXAKTEN Plattenpunkten statt aus handgesetzten Stufen.
///
/// Nutzer-Formulierung: "wir koennen ihn auch als punkte heatmap verwenden.
/// dann ist er weniger starr in die dreiecksform gepresst." Der Anlass ist
/// die Ablation par.8.6: die STRUKTUR haengt an der Zielkarte, nicht an den
/// linearen Zusatztermen -- die Karte ist damit der Hebel, und eine Karte aus
/// gerechneten Punkten braucht keine Formvorgabe.
///
/// Wert je Zelle = **marginaler Zuwachs der Wertungsplatten-Punkte**, exakt
/// gemessen: Zelle probeweise belegen, `scoring::scoring_progress` mit den
/// AKTIVEN Plattenkriterien neu rechnen, Differenz nehmen. Kein
/// nachgebauter Formelsatz je Kriterium -- damit koennen Karte und Endwertung
/// nicht auseinanderlaufen (dieselbe Regel, aus der `heuristic_v2` die
/// Spalten-Formel woertlich uebernimmt).
///
/// Zwei Zuschlaege, die `scoring_progress` allein nicht sieht:
///
/// 1. **Freischaltung**: schaltet die Probebelegung ein Spezialfeld frei,
///    wird es sofort mitbelegt -- so verhaelt sich das Spiel auch
///    (`round_end::check_special_trigger`). Damit enthaelt die Differenz die
///    zusaetzliche Zelle und die vermiedene `-3`-Strafe von selbst.
/// 2. **Spezialfliesen-Bonus** in Hoehe der Rasterreihe (1..6); der ist eine
///    Sofortzahlung beim Tiling und steht in keiner Plattenwertung.
///
/// **Bewusst NICHT enthalten: Platzierungspunkte nach Linienlaenge.** Die
/// sind genau das, was `best_first_step_inner` ohnehin maximiert
/// (`tiling_solver.rs:49-56`). Sie hier mitzuzaehlen hiesse, das Routing auf
/// dasselbe Kriterium zu ziehen, dessen Alleinherrschaft der Anlass fuer v2
/// war.
///
/// **Reichweite statt Abklingkurve.** Eine Zelle, deren Farbe nicht mehr in
/// ausreichender Zahl erreichbar ist, faellt auf 0 -- geprueft mit
/// `column_build::cell_is_completable` gegen `provocation::remaining_colors`.
/// Das ist zugleich die Knappheits-Kopplung, die dem Saettigungsterm in
/// `heuristic_v2` fehlt, und es macht eine Runden-Abklingkurve ueberfluessig:
/// gegen Spielende faellt die Karte von selbst zusammen, weil die Farben
/// ausgehen.
fn points_heatmap(state: &GameState, pi: usize) -> Zielkarte {
    points_map(state, pi, false)
}

/// Karte der ERWARTETEN PUNKTE je Zelle (Nutzer-Praezisierung 2026-08-25:
/// "nicht fuer die wertungsplatten allein ... sondern fuer die erwarteten
/// endpunkte wenn auf dieses feld gelegt wird").
///
/// Wie [`points_heatmap`], PLUS die Platzierungspunkte nach Linienlaenge
/// (`round_end::score_placed_tile`, horizontal und vertikal getrennt gezaehlt)
/// -- also die Rundenpunkte, die der Zug sofort bringt, zusammen mit dem
/// Plattenanteil die erwarteten Endpunkte dieser Zelle.
///
/// **Warum das eine ANDERE Karte ist und nicht nur ein Summand mehr:**
/// `points_heatmap` ist additiv ueber Wertungsplatten und war damit
/// konstruktionsbedingt ein Breiten-Signal (par.9.1 gemessen: Teilspalten
/// >= 3 steigen, volle Spalten fallen). Linienpunkte sind SUPERADDITIV -- die
/// Zelle neben einer langen Linie zahlt mehr als dieselbe Zelle im Freien.
/// Genau das ist ein Fokus-Signal, also die Groesse, deren Fehlen den ersten
/// Versuch hat scheitern lassen.
///
/// **Bekanntes Gegenargument, ausdruecklich in Kauf genommen:** die
/// Linienpunkte sind das Kriterium, das `best_first_step_inner` ohnehin
/// maximiert (`tiling_solver.rs:49-56`), und ihre Alleinherrschaft war der
/// Anlass fuer v2. Hier stehen sie aber NEBEN dem Plattenanteil und wirken auf
/// die Zielzellen-Wahl, nicht auf die Schrittwahl -- ob das reicht, entscheidet
/// die Messung und nicht dieses Argument.
fn expected_points_map(state: &GameState, pi: usize) -> Zielkarte {
    points_map(state, pi, true)
}

fn points_map(state: &GameState, pi: usize, mit_platzierung: bool) -> Zielkarte {
    let player = &state.players[pi];
    let ids = &state.scoring_tile_ids;
    let remaining = crate::provocation::remaining_colors(state);
    let basis = crate::scoring::scoring_progress(player, ids);
    let mut k = [[0.0f64; 6]; 6];

    for r in 0..6 {
        // Top-down-Sperre: unterhalb der bereits getilten Reihe geht nichts
        // mehr (dieselbe Bedingung wie in `v2_chip_preference`).
        if (r as i32) < player.tiled_max_row {
            continue;
        }
        for c in 0..6 {
            let Some(sp) = player.dome_grid.get_space(r, c) else { continue };
            if sp.is_filled() || sp.is_locked || sp.space_type == SpaceType::Special {
                continue; // Spezialfelder werden nicht angesteuert, sie fallen an
            }
            if !crate::column_build::cell_is_completable(player, r, c, &remaining) {
                continue;
            }
            // Welche Farbe wuerde hier liegen? Normal fordert eine bestimmte,
            // Wild nimmt jede -- dort die reichlichste noch verfuegbare.
            let farbe = match sp.space_type {
                SpaceType::Normal => match sp.required_color {
                    Some(f) => f,
                    None => continue,
                },
                SpaceType::Wild => match most_available_color(&remaining) {
                    Some(f) => f,
                    None => continue,
                },
                SpaceType::Special => continue,
            };

            let mut probe = player.clone();
            if probe.dome_grid.place_tile(r, c, farbe).is_err() {
                continue;
            }
            // Freigeschaltetes Spezialfeld sofort mitbelegen und seinen
            // Sofortbonus (= Rasterreihe) aufschlagen.
            let mut bonus = 0.0;
            let (sr, sc) = (r / 2, c / 2);
            if let Some(slot) = probe.dome_grid.dome_slots[sr][sc].as_mut() {
                if let Some(si) = slot.special_space_idx() {
                    if !slot.spaces[si].is_locked && !slot.spaces[si].placed_special {
                        slot.spaces[si].placed_special = true;
                        bonus += (2 * sr + si / 2) as f64 + 1.0;
                    }
                }
            }
            if mit_platzierung {
                // Linienpunkte des gelegten Steins -- gezaehlt auf dem
                // Probe-Brett, also NACH dem Legen, wie im echten Zug.
                let si = 2 * (r % 2) + (c % 2);
                bonus += crate::round_end::score_placed_tile(&probe, sr, sc, si).0 as f64;
            }
            let wert = crate::scoring::scoring_progress(&probe, ids) - basis + bonus;
            if wert > 0.0 {
                k[r][c] = wert;
            }
        }
    }
    k
}

/// Farbe mit dem groessten Restbestand -- die einzige sinnvolle Annahme fuer
/// eine Wild-Zelle, die noch jede Farbe nehmen kann.
fn most_available_color(remaining: &[i64; 5]) -> Option<crate::tile::TileColor> {
    let (idx, &n) = remaining.iter().enumerate().max_by_key(|(_, &n)| n)?;
    if n <= 0 {
        return None;
    }
    // Indexordnung wie `provocation::color_index`: `TileColor::NORMAL`.
    crate::tile::TileColor::NORMAL.get(idx).copied()
}

/// Zielkarte UND passende Zellenbewertung je Variante.
///
/// `None` fuer `V1`/`V2` -- die laufen weiter ueber `v2_target_cells`.
/// Die Zellenbewertung gehoert zur Karte: die Prio-Leiter braucht die
/// Sonderregel fuer Rasterzeile 5 ([`envelope_cell_value`]), die Heatmap
/// nicht, weil sie die Freischaltung schon eingepreist hat.
fn v2_map_for(
    state: &GameState,
    pi: usize,
    variante: crate::mcts::HeuristikVariante,
) -> Option<(Zielkarte, fn(&PlayerBoard, usize, usize, &DomeSpace) -> f64)> {
    match variante {
        crate::mcts::HeuristikVariante::V2Huelle => {
            Some((v2_envelope_target(state, pi)?, envelope_cell_value))
        }
        crate::mcts::HeuristikVariante::V2Heatmap => {
            Some((points_heatmap(state, pi), legacy_cell_value))
        }
        crate::mcts::HeuristikVariante::V2PointMap => {
            Some((expected_points_map(state, pi), legacy_cell_value))
        }
        _ => None,
    }
}

/// Alle Zellen mit Gewicht > 0, in Rasterreihenfolge.
fn cells_from_map(karte: &Zielkarte) -> Vec<(usize, usize)> {
    let mut v = Vec::with_capacity(28);
    for r in 0..6 {
        for c in 0..6 {
            if karte[r][c] > 0.0 {
                v.push((r, c));
            }
        }
    }
    v
}

/// Gewichteter Fuellstand der Zielkarte -- das Mass fuer die
/// Orientierungs-Festnagelung ab Runde 3.
///
/// Dieselbe Bauform wie die Zielspalten-Festnagelung in [`v2_target_cells`]:
/// der Fuellstand ist von sich aus stabil (eine fuehrende Seite behaelt ihren
/// Vorsprung), also braucht es keinen gespeicherten Zustand und es entsteht
/// kein Leck ueber Partiegrenzen.
fn map_fill(player: &PlayerBoard, karte: &Zielkarte) -> f64 {
    let mut summe = 0.0;
    for r in 0..6 {
        for c in 0..6 {
            if karte[r][c] > 0.0 && player.dome_grid.get_space(r, c).is_some_and(|sp| sp.is_filled()) {
                summe += karte[r][c];
            }
        }
    }
    summe
}

/// Zellenwert fuer die PLATTENWAHL, Bestandsfassung: unveraendert
/// `column_build::cell_value`.
fn legacy_cell_value(player: &PlayerBoard, r: usize, _c: usize, space: &DomeSpace) -> f64 {
    crate::column_build::cell_value(player, r, space)
}

/// Zellenwert fuer die Plattenwahl der Huellen-Variante.
///
/// Einziger Unterschied zum Bestand: auf RASTERZEILE 5 schlagen Spezialfeld
/// und Wild jede Normalfarbe (Nutzer-Vorgabe 2026-08-24, Prio 2: "mit
/// Spezialfliese auf Reihe 6. Alternativ ... jokerplatten verwenden").
///
/// Der Grund ist mechanisch und geprueft, nicht aesthetisch: Rasterzeile 5
/// wird ausschliesslich von Musterreihe 6 gespeist, dem seltensten Abschluss
/// im Spiel. Ein SPEZIALFELD dort kostet gar keinen -- es wird automatisch
/// belegt, sobald die drei anderen Zellen seiner Platte liegen
/// (`round_end::check_special_trigger`). Ein WILD kostet einen Abschluss,
/// nimmt ihm aber die Farbbindung. Der Bestandswert kehrt die Rangfolge um
/// (Wild 3,0 ueber Special 2,0), weil er fuer Zellen OHNE diese Knappheit
/// geschrieben ist.
///
/// Werte sind eine SETZUNG. Gefordert ist nur: Special > Wild > jede
/// Normalfarbe, und Normalfarbe hoechstens `JACKPOT_WERT` (4,0).
fn envelope_cell_value(player: &PlayerBoard, r: usize, _c: usize, space: &DomeSpace) -> f64 {
    if r == 5 {
        match space.space_type {
            SpaceType::Special => return 6.0,
            SpaceType::Wild => return 5.0,
            SpaceType::Normal => {}
        }
    }
    crate::column_build::cell_value(player, r, space)
}

/// Die vier Eckslots aus `scoring::score_corner_tiles`: `(0,0)`/`(0,2)` (obere
/// Ecken, 3 Pkt) und `(2,0)`/`(2,2)` (untere Ecken, 8 Pkt) -- Slot-Koordinaten
/// im 3x3-Dome-Raster, je in die 4 Rasterzellen aufgeloest. Seit §20 nicht
/// mehr von `Eckenbauer` selbst genutzt (Spaltenpaar-Ziel ersetzt die
/// isolierten Eck-Slots, siehe dortige Doku) -- bleibt fuer den eigenen
/// Geometrietest stehen.
#[allow(dead_code)]
fn cells_corner(idx: usize) -> Vec<(usize, usize)> {
    let (sr, sc) = [(0usize, 0usize), (0, 2), (2, 0), (2, 2)][idx];
    let mut v = Vec::with_capacity(4);
    for dr in 0..2usize {
        for dc in 0..2usize {
            v.push((sr * 2 + dr, sc * 2 + dc));
        }
    }
    v
}

// ── Kriterium 0: Zeilen (Horizontale Reihen, 3 Pkt) ──────────────────────────

struct Zeilenbauer;
impl Zeilenbauer {
    fn zellen(&self, state: &GameState, pi: usize) -> Option<Vec<(usize, usize)>> {
        let kand: Vec<_> = (0..6).map(cells_row).collect();
        target_cells_generic(state, pi, &kand)
    }
}
impl Plattenbauer for Zeilenbauer {
    fn drafting_preference(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(state, state.current_player)?;
        preference_move_for_cells(state, &z)
    }
    fn dome_preference(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(state, state.current_player)?;
        dome_preference_for_cells(state, &z)
    }
    fn tiling_preference(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        let z = self.zellen(state, pi)?;
        tiling_preference_for_cells(state, pi, &z)
    }
}

// ── Kriterium 1 (generisch, MOSAIC_PLATTENBAU=1 ohne den Altknopf): Spalten ──

struct SpaltenbauerGenerisch;
impl SpaltenbauerGenerisch {
    fn zellen(&self, state: &GameState, pi: usize) -> Option<Vec<(usize, usize)>> {
        let kand: Vec<_> = (0..6).map(cells_column).collect();
        target_cells_generic(state, pi, &kand)
    }
}
impl Plattenbauer for SpaltenbauerGenerisch {
    fn drafting_preference(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(state, state.current_player)?;
        preference_move_for_cells(state, &z)
    }
    fn dome_preference(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(state, state.current_player)?;
        dome_preference_for_cells(state, &z)
    }
    fn tiling_preference(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        let z = self.zellen(state, pi)?;
        tiling_preference_for_cells(state, pi, &z)
    }
}

// ── Kriterium 2: Diagonalen (10 Pkt je volle Diagonale, max 2x) ──────────────

struct Diagonalenbauer;
impl Diagonalenbauer {
    /// §18: nutzt `target_cells_generic_smart` (immer die echten Special-
    /// Nachbar-Kosten, siehe dortige Doku) statt der geteilten, §16/§17-
    /// Schalter-abhaengigen `target_cells_generic` -- die Diagonalen-
    /// Special-Erweiterung ist eine EIGENE, in §18 validierte Entscheidung
    /// (+2,61 Plattenpunkte, t=2,79, p=0,011, kein Sieg-Verlust), unabhaengig
    /// vom k1-Legacy-Befund (§17: final NEIN).
    fn zellen(&self, state: &GameState, pi: usize) -> Option<Vec<(usize, usize)>> {
        let kand = vec![cells_main_diagonal(), cells_anti_diagonal()];
        target_cells_generic_smart(state, pi, &kand)
    }
}
impl Plattenbauer for Diagonalenbauer {
    fn drafting_preference(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(state, state.current_player)?;
        preference_move_for_cells(state, &z).or_else(|| {
            // §18 (Diagonalen-Baustein, Nutzer-Taktik domain_knowledge.md
            // §5): eine offene Special-Zelle in der Diagonalen-Slot-Reihe 3
            // braucht ihre Slot-Nachbarn, die oft NICHT selbst Diagonal-
            // zellen sind. UNBEDINGT (siehe `special_neighbour_cells_always`-
            // Doku) -- §18 hat diese Erweiterung EIGENSTAeNDIG validiert.
            let player = &state.players[state.current_player];
            let nz = crate::column_build::special_neighbour_cells_always(player, &z);
            if nz.is_empty() { None } else { preference_move_for_cells(state, &nz) }
        })
    }
    fn dome_preference(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(state, state.current_player)?;
        dome_preference_for_cells(state, &z)
    }
    fn tiling_preference(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        let z = self.zellen(state, pi)?;
        tiling_preference_for_cells(state, pi, &z).or_else(|| {
            let player = &state.players[pi];
            let nz = crate::column_build::special_neighbour_cells_always(player, &z);
            if nz.is_empty() { None } else { tiling_preference_for_cells(state, pi, &nz) }
        })
    }
}

// ── Kriterium 5: Ecken (2x2-Slots, 3/8 Pkt) ─────────────────────────────────

// §20 (Eckplatten-Neubau, Nutzer-Entwurf "kannst ihn fast schon kombinieren
// k1 und zwei spalten", PREREG_provocation.md §20): statt vier isolierter
// Eck-Slots ein AEUSSERES Spaltenpaar (Rasterspalten 0+1 oder 4+5) als Ziel
// -- das Paar schliesst BEIDE Ecken derselben Seite (8+3=11 Punkte, das
// Nutzer-Orakel fuer k5) und liefert bei aktivem Kriterium 1 zwei volle
// Spalten obendrauf (scoring.rs:60-64: k5 und k1 sind NICHT wechselseitig
// ausgeschlossen, nur k5<->k2). Prioritaet innerhalb des Paars: untere Ecke
// (8 Pkt, Rasterzeilen 4-5) vor oberer (3 Pkt, Zeilen 0-1) vor dem Rest des
// Paars (Zeilen 2-3, reine Spalten-Fuellung ohne Eck-Bonus) -- als
// dreistufige `.or_else`-Kette, gleiches Muster wie die Special-Nachbar-
// Kette in §16/§18.

fn cells_column_pair(c0: usize) -> Vec<(usize, usize)> {
    let mut v = Vec::with_capacity(12);
    for r in 0..6usize {
        v.push((r, c0));
        v.push((r, c0 + 1));
    }
    v
}

fn cells_lower_corner_pair(c0: usize) -> Vec<(usize, usize)> {
    let mut v = Vec::with_capacity(4);
    for r in 4..6usize {
        v.push((r, c0));
        v.push((r, c0 + 1));
    }
    v
}

fn cells_upper_corner_pair(c0: usize) -> Vec<(usize, usize)> {
    let mut v = Vec::with_capacity(4);
    for r in 0..2usize {
        v.push((r, c0));
        v.push((r, c0 + 1));
    }
    v
}

struct Eckenbauer;
impl Eckenbauer {
    /// Waehlt zwischen den beiden AEUSSEREN Spaltenpaaren (0+1 / 4+5) --
    /// `target_cells_generic_smart` (§18) fuer die echte Special-Nachbar-
    /// Kostenrechnung, dieselbe Seed-Streuung/Zielwechsel-Logik wie alle
    /// anderen generischen Bauern (§14-Lehre: keine sture Bindung). Liefert
    /// die KLEINERE der beiden Spaltennummern des gewaehlten Paars.
    fn column0(&self, state: &GameState, pi: usize) -> Option<usize> {
        let kand = vec![cells_column_pair(0), cells_column_pair(4)];
        let z = target_cells_generic_smart(state, pi, &kand)?;
        z.iter().map(|&(_, c)| c).min()
    }
}
impl Plattenbauer for Eckenbauer {
    fn drafting_preference(&self, state: &GameState) -> Option<Action> {
        let c0 = self.column0(state, state.current_player)?;
        preference_move_for_cells(state, &cells_lower_corner_pair(c0))
            .or_else(|| preference_move_for_cells(state, &cells_upper_corner_pair(c0)))
            .or_else(|| preference_move_for_cells(state, &cells_column_pair(c0)))
    }
    fn dome_preference(&self, state: &GameState) -> Option<Action> {
        let c0 = self.column0(state, state.current_player)?;
        dome_preference_for_cells(state, &cells_lower_corner_pair(c0))
            .or_else(|| dome_preference_for_cells(state, &cells_upper_corner_pair(c0)))
            .or_else(|| dome_preference_for_cells(state, &cells_column_pair(c0)))
    }
    fn tiling_preference(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        let c0 = self.column0(state, pi)?;
        tiling_preference_for_cells(state, pi, &cells_lower_corner_pair(c0))
            .or_else(|| tiling_preference_for_cells(state, pi, &cells_upper_corner_pair(c0)))
            .or_else(|| tiling_preference_for_cells(state, pi, &cells_column_pair(c0)))
    }
}

// ── Kriterium 3: Mehrfarbige Felder (Jokerfelder, 2 Pkt je Feld wenn ALLE voll) ──
//
// Kein Kandidatenvergleich noetig -- es gibt nur EINE sinnvolle Zielmenge:
// ALLE noch offenen Wild-Zellen des Bretts (jede Farbe qualifiziert dort
// ohnehin, siehe `preference_move_for_cells`s `SpaceType::Wild => true`).

struct Mehrfarbigbauer;
impl Mehrfarbigbauer {
    fn zellen(&self, player: &PlayerBoard) -> Vec<(usize, usize)> {
        let mut v = Vec::new();
        for sr in 0..3usize {
            for sc in 0..3usize {
                for r in [sr * 2, sr * 2 + 1] {
                    for c in [sc * 2, sc * 2 + 1] {
                        if let Some(sp) = player.dome_grid.get_space(r, c) {
                            if sp.space_type == SpaceType::Wild {
                                v.push((r, c));
                            }
                        }
                    }
                }
            }
        }
        v
    }
}
impl Plattenbauer for Mehrfarbigbauer {
    fn drafting_preference(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(&state.players[state.current_player]);
        preference_move_for_cells(state, &z)
    }
    fn dome_preference(&self, _state: &GameState) -> Option<Action> {
        // Bewusst kein Vorzug: mehr Wild-Zellen sind IMMER neutral-bis-gut
        // (jede Farbe qualifiziert), eine Rotationsentscheidung aendert die
        // Wild-ANZAHL einer Kachel nicht (Rotation permutiert nur Positionen,
        // nicht Typen) -- es gibt hier keine Entscheidung, die dieser
        // Vorzug besser treffen koennte als das Netz selbst.
        None
    }
    fn tiling_preference(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        let z = self.zellen(&state.players[pi]);
        tiling_preference_for_cells(state, pi, &z)
    }
}

// ── Kriterium 4: Randfelder (1 Pkt je gefuellte Randzelle, farbfrei-additiv) ──
//
// Additiv wie Kriterium 3: kein Kandidatenvergleich, Zielmenge = alle noch
// offenen Zellen am Rand (Zeile/Spalte 0 oder 5) mit vorhandenem Slot.

struct Randbauer;
impl Randbauer {
    fn zellen(&self, player: &PlayerBoard) -> Vec<(usize, usize)> {
        let mut v = Vec::new();
        for r in 0..6usize {
            for c in 0..6usize {
                if (r == 0 || r == 5 || c == 0 || c == 5) && player.dome_grid.get_space(r, c).is_some() {
                    v.push((r, c));
                }
            }
        }
        v
    }
}
impl Plattenbauer for Randbauer {
    fn drafting_preference(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(&state.players[state.current_player]);
        preference_move_for_cells(state, &z)
    }
    fn dome_preference(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(&state.players[state.current_player]);
        dome_preference_for_cells(state, &z)
    }
    fn tiling_preference(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        let z = self.zellen(&state.players[pi]);
        tiling_preference_for_cells(state, pi, &z)
    }
}

// ── Kriterium 6: Spezialfelder (-3 Pkt je LEERES Spezialfeld) ───────────────
//
// Special-Zellen nehmen keine Farbe per Stein-Zug entgegen (fuellen sich erst
// automatisch, wenn ihre 3 Slot-Nachbarn komplett sind, `round_end::
// check_special_trigger`) -- Zielmenge sind deshalb die NACHBARN offener
// Special-Zellen, nicht die Special-Zellen selbst (§12-Befund, siehe
// Moduldoku: "der §-Befund aus Runde 1 hilft").

struct Spezialbauer;
impl Spezialbauer {
    fn zellen(&self, player: &PlayerBoard) -> Vec<(usize, usize)> {
        let mut v = Vec::new();
        for sr in 0..3usize {
            for sc in 0..3usize {
                let Some(slot) = &player.dome_grid.dome_slots[sr][sc] else { continue };
                let mut special_offen = false;
                let mut nachbarn: Vec<(usize, usize)> = Vec::new();
                for (si, sp) in slot.spaces.iter().enumerate() {
                    let row = sr * 2 + si / 2;
                    let col = sc * 2 + si % 2;
                    if sp.space_type == SpaceType::Special {
                        if !sp.is_filled() {
                            special_offen = true;
                        }
                    } else if !sp.is_filled() {
                        nachbarn.push((row, col));
                    }
                }
                if special_offen {
                    v.extend(nachbarn);
                }
            }
        }
        v
    }
}
impl Plattenbauer for Spezialbauer {
    fn drafting_preference(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(&state.players[state.current_player]);
        preference_move_for_cells(state, &z)
    }
    fn dome_preference(&self, state: &GameState) -> Option<Action> {
        // §19: `dome_draft_preference_k6` (Joker-Kuppeln auf untere Slots,
        // erzwungene Special-Kuppeln nach oben, domain_knowledge.md §8)
        // wurde GEBAUT UND GEMESSEN, aber NICHT verkettet -- die Messung auf
        // 20 frischen k6-Seeds zeigte eine LEICHT SCHLECHTERE eigene
        // Spezialfeld-Punktzahl (-10,5 statt -9,75, t=-0,84, p=0,41, falsches
        // Vorzeichen fuer eine Uebernahme) UND einen unerwuenschten Gegner-
        // Effekt (Gegner-Spezialfelder wurden BESSER statt schlechter,
        // -6,6 statt -11,1 -- das Gegenteil des beabsichtigten Stoerkanals)
        // UND einen (nicht signifikanten, aber deutlichen) Sieg-Ruecksgang
        // (5/20 statt 9/20). Bleibt als getestete, unverdrahtete Funktion
        // stehen (siehe PREREG_provocation.md §19).
        let z = self.zellen(&state.players[state.current_player]);
        dome_preference_for_cells(state, &z)
    }
    fn tiling_preference(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        let z = self.zellen(&state.players[pi]);
        tiling_preference_for_cells(state, pi, &z)
    }
}

/// §19 (Spezialfelder-Baustein k6, Nutzer-Strategie `docs/domain_knowledge.md`
/// §8, woertlich: *"einerseits viele jokerkuppeln nehmen (und auf die
/// unteren slots legen) und wenn eine spezialkuppel dennoch platziert werden
/// muss, dann die unteren slots vermeiden"*): Kuppeldraft-Vorzug fuer Stufe 1
/// (Kachel+Slot-Wahl, `PendingDomeChoice` noch nicht gesetzt) -- KEIN
/// Fliesendraft-Eingriff, die Strategie lebt laut Nutzer-Vorgabe primaer in
/// der Kuppelwahl. Bewertung je (Kachel, freier Slot)-Kombination:
///
///  - Joker-Kuppel (kein Special, `is_special_type()==false`) in einen
///    UNTEREN Slot (Slot-Reihe 2, Rasterzeilen 4-5): 3,0 -- die teuerste
///    Slot-Reihe wird praeventiv mit einer Kachel besetzt, die NIE ein
///    Spezialfeld-Risiko traegt.
///  - Joker-Kuppel in eine andere Slot-Reihe: 2,0.
///  - Special-Kuppel (unvermeidlich, kein Joker mehr im Display/Slot frei)
///    in einen OBEREN Slot (Slot-Reihe 0, Rasterzeilen 0-1): 1,5 -- der
///    Trigger braucht dort nur 1-2 Kopien je Nachbarzelle (kuerzeste
///    Musterreihen).
///  - Special-Kuppel in die mittlere Slot-Reihe: 1,0.
///  - Special-Kuppel in einen UNTEREN Slot: 0,5 -- die laut Nutzer-Vorgabe
///    ausdruecklich zu VERMEIDENDE Kombination, bleibt aber waehlbar, wenn
///    kein anderer Slot mehr frei ist (Praeferenz, kein Verbot).
///
/// Rotation bleibt bei 0 (Platzhalter wie bei den anderen Bauern) -- Stufe 2
/// entscheidet die tatsaechliche Rotation ueber die bestehende Special-
/// Nachbar-Mechanik (siehe Aufrufstelle).
// Absichtlich NICHT verkettet (siehe `Spezialbauer::dome_preference`-Kommentar):
// gemessen und mit falschem Vorzeichen abgelehnt (§19).
#[allow(dead_code)]
fn dome_draft_preference_k6(state: &GameState) -> Option<Action> {
    let player = &state.players[state.current_player];
    if state.pending_dome_choice.is_some() {
        return None;
    }
    if !state.pending_stack_draw.is_empty() {
        return None;
    }
    if !player.can_place_dome_tile(state.round_number) || player.has_unplaced_start_tile() {
        return None;
    }
    let score_kombination = |tile: &crate::dome::DomeTile, slot_row: usize| -> f64 {
        if tile.is_special_type() {
            match slot_row {
                0 => 1.5,
                1 => 1.0,
                _ => 0.5,
            }
        } else {
            match slot_row {
                2 => 3.0,
                _ => 2.0,
            }
        }
    };
    let mut best: Option<(f64, usize, usize, usize)> = None; // (score, tile_id, slot_row, slot_col)
    for tile in &state.dome_display {
        for &(sr, sc) in &player.dome_grid.empty_slots() {
            let m = PlaceDomeTileMove { dome_tile_id: tile.tile_id, slot_row: sr, slot_col: sc, rotation: 0 };
            if crate::game::validate_dome_move(state, &m).is_some() {
                continue;
            }
            let score = score_kombination(tile, sr);
            if best.as_ref().map_or(true, |(bs, _, _, _)| score > *bs) {
                best = Some((score, tile.tile_id, sr, sc));
            }
        }
    }
    best.map(|(_, tid, sr, sc)| Action::ChooseDomeSlot(PlaceDomeTileMove { dome_tile_id: tid, slot_row: sr, slot_col: sc, rotation: 0 }))
}

// ── Kriterium 7: Farbenreiche Reihen (4 Pkt je Reihe mit >=5 Farben) ─────────
//
// Teilt sich die Zeilen-Kandidatenauswahl mit Kriterium 0 (dieselbe
// Geometrie -- eine Zeile), Drafting-/Tiling-Vorzug sind deshalb IDENTISCH zu
// `Zeilenbauer`. Die Kuppelplatten-Wahl ist eigene Logik: statt "Farbe
// trifft" zaehlt "Farbe ist NEU in der Zielreihe" (Vielfalt statt Treffer).

struct Farbenreichbauer;
impl Farbenreichbauer {
    fn zellen(&self, state: &GameState, pi: usize) -> Option<Vec<(usize, usize)>> {
        let kand: Vec<_> = (0..6).map(cells_row).collect();
        target_cells_generic(state, pi, &kand)
    }

    /// Farben, die in der Zielreihe (aus `zellen`, alle mit gleichem `row`)
    /// schon platziert sind -- gelesen aus `placed_color` der Slot-Zellen.
    fn available_colors(&self, player: &PlayerBoard, row: usize) -> std::collections::HashSet<crate::tile::TileColor> {
        let mut farben = std::collections::HashSet::new();
        for c in 0..6usize {
            if let Some(sp) = player.dome_grid.get_space(row, c) {
                if let Some(col) = sp.placed_color {
                    farben.insert(col);
                }
            }
        }
        farben
    }
}
impl Plattenbauer for Farbenreichbauer {
    fn drafting_preference(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(state, state.current_player)?;
        preference_move_for_cells(state, &z)
    }
    fn dome_preference(&self, state: &GameState) -> Option<Action> {
        let zellen = self.zellen(state, state.current_player)?;
        let row = zellen.first()?.0;
        let player = &state.players[state.current_player];
        let vorhanden = self.available_colors(player, row);

        // Score einer Kombination: Zahl der Positionen in der Zielreihe, die
        // eine noch NICHT vorhandene Farbe einbringen wuerden (Wild zaehlt
        // nicht -- keine feste Farbe, siehe `TileColor`-Doku).
        let score_kombination = |tile: &crate::dome::DomeTile, slot_row: usize, slot_col: usize, rotation: u32| -> Option<f64> {
            let idx = rotation_indices(rotation)?;
            let mut summe = 0.0;
            let mut beruehrt = false;
            for i in 0..4usize {
                let r = slot_row * 2 + i / 2;
                let c = slot_col * 2 + i % 2;
                if r != row || player.dome_grid.get_space(r, c).map_or(false, |s| s.is_filled()) {
                    continue;
                }
                beruehrt = true;
                if let Some(col) = tile.spaces[idx[i]].required_color {
                    if !vorhanden.contains(&col) {
                        summe += 1.0;
                    }
                }
            }
            if beruehrt {
                Some(summe)
            } else {
                None
            }
        };

        if let Some(choice) = &state.pending_dome_choice {
            return match choice {
                PendingDomeChoice::FromDisplay { dome_tile_id, slot_row, slot_col } => {
                    let tile = state.dome_display.iter().find(|t| t.tile_id == *dome_tile_id)?;
                    let mut best: Option<(f64, u32)> = None;
                    for rot in [0u32, 90, 180, 270] {
                        let m = PlaceDomeTileMove {
                            dome_tile_id: *dome_tile_id,
                            slot_row: *slot_row,
                            slot_col: *slot_col,
                            rotation: rot,
                        };
                        if crate::game::validate_dome_move(state, &m).is_some() {
                            continue;
                        }
                        if let Some(score) = score_kombination(tile, *slot_row, *slot_col, rot) {
                            if best.map_or(true, |(bs, _)| score > bs) {
                                best = Some((score, rot));
                            }
                        }
                    }
                    best.filter(|(s, _)| *s > 0.0).map(|(_, rot)| Action::ChooseDomeRotation(rot))
                }
                PendingDomeChoice::FromDrawStack { .. } => None,
            };
        }
        if !state.pending_stack_draw.is_empty() {
            return None;
        }
        if !player.can_place_dome_tile(state.round_number) || player.has_unplaced_start_tile() {
            return None;
        }
        let mut best: Option<(f64, usize, usize, usize)> = None;
        for tile in &state.dome_display {
            for &(sr, sc) in &player.dome_grid.empty_slots() {
                let mut best_rot: Option<f64> = None;
                for rot in [0u32, 90, 180, 270] {
                    let m = PlaceDomeTileMove { dome_tile_id: tile.tile_id, slot_row: sr, slot_col: sc, rotation: rot };
                    if crate::game::validate_dome_move(state, &m).is_some() {
                        continue;
                    }
                    if let Some(score) = score_kombination(tile, sr, sc, rot) {
                        if best_rot.map_or(true, |b| score > b) {
                            best_rot = Some(score);
                        }
                    }
                }
                if let Some(score) = best_rot {
                    if best.as_ref().map_or(true, |(bs, _, _, _)| score > *bs) {
                        best = Some((score, tile.tile_id, sr, sc));
                    }
                }
            }
        }
        best.filter(|(s, _, _, _)| *s > 0.0).map(|(_, tid, sr, sc)| {
            Action::ChooseDomeSlot(PlaceDomeTileMove { dome_tile_id: tid, slot_row: sr, slot_col: sc, rotation: 0 })
        })
    }
    fn tiling_preference(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        let z = self.zellen(state, pi)?;
        tiling_preference_for_cells(state, pi, &z)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dome::{DomeSpace, DomeTile};
    use crate::tile::TileColor::*;
    use rand::SeedableRng;
    use rand::rngs::StdRng;

    fn names() -> [String; 2] {
        ["P1".into(), "P2".into()]
    }

    fn drafting_game(seed: u64) -> crate::game::Game {
        let mut rng = StdRng::seed_from_u64(seed);
        let mut game = crate::game::Game::start(names(), 0, vec![0, 1, 2], &mut rng);
        for p in game.state.players.iter_mut() {
            p.start_tile_pending = false;
        }
        game
    }

    fn normal_tile(id: usize, colors: [crate::tile::TileColor; 4]) -> DomeTile {
        DomeTile::new(id, colors.into_iter().map(DomeSpace::normal).collect(), 0)
    }

    #[test]
    fn default_aus_liefert_ueberall_none() {
        crate::column_build::set_active_override_for_test(Some(false));
        set_mode_override_for_test(Some(Modus::Aus));
        let game = drafting_game(1);
        assert_eq!(drafting_preference(&game.state), None);
        assert_eq!(dome_preference(&game.state), None);
        assert!(tiling_preference(&game.state, 0).is_none());
        set_mode_override_for_test(None);
        crate::column_build::set_active_override_for_test(None);
    }

    /// Kernabnahme Stufe 1: bei aktivem `MOSAIC_SPALTENBAU` muss die
    /// Abstraktion GENAU das liefern, was `column_build.rs` direkt liefert --
    /// reine Delegation, keine Nachbildung. Ueber mehrere Seeds/Zustaende,
    /// damit der Test nicht nur eine einzelne Zufallskonstellation trifft.
    #[test]
    fn mosaic_spaltenbau_on_is_behaviorally_identical_to_direct_targeting() {
        crate::column_build::set_active_override_for_test(Some(true));
        for seed in 0u64..30 {
            // Runde 4: `column_build::target_column` merkt sich jetzt die zuletzt
            // gewaehlte Spalte je Partie (Vollendbarkeits-Buchhaltung, siehe
            // dortige Doku) -- ohne Reset hier wuerde die Spalte des VORIGEN
            // Seeds in dieses (voellig andere) Brett hineinlecken, exakt das
            // Leck, vor dem `set_game_seed`s Doku schon immer warnt. Echte
            // Partien (self_play.rs) rufen `set_game_seed` ohnehin schon
            // pro Partie auf -- dieser Test muss es fuer sein eigenes
            // Pro-Seed-"Partie"-Modell jetzt auch tun.
            crate::column_build::set_game_seed(None);
            let mut game = drafting_game(seed);
            let pi = game.state.current_player;
            let tile = normal_tile(100 + seed as usize, [Rot, Blau, Gelb, Schwarz]);
            let _ = game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0);

            assert_eq!(
                drafting_preference(&game.state),
                crate::column_build::preference_move(&game.state),
                "Seed {seed}: drafting_preference muss column_build::preference_move entsprechen"
            );
            assert_eq!(
                dome_preference(&game.state),
                crate::column_build::preference_dome_choice(&game.state),
                "Seed {seed}: dome_preference muss column_build::preference_dome_choice entsprechen"
            );
            assert_eq!(
                tiling_preference(&game.state, pi),
                crate::column_build::preference_tiling_step(&game.state, pi),
                "Seed {seed}: tiling_preference muss column_build::preference_tiling_step entsprechen"
            );
        }
        crate::column_build::set_active_override_for_test(None);
    }

    /// `cells_cost` ueber einer Spalten-Zellenliste muss exakt
    /// `column_build::column_cost` fuer dieselbe Spalte liefern -- das ist
    /// der rechnerische Beleg, dass die Generalisierung fuer den Spalten-Fall
    /// nichts verschiebt (siehe Moduldoku).
    #[test]
    fn cells_cost_matches_column_cost_for_column_geometry() {
        let mut game = drafting_game(9);
        let pi = game.state.current_player;
        let tile = normal_tile(200, [Rot, Blau, Gelb, Schwarz]);
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("frei");
        let verbleibend = crate::provocation::remaining_colors(&game.state);
        for spalte in 0..6usize {
            let alt = crate::column_build::column_cost(&game.state.players[pi], spalte, &verbleibend);
            let neu = cells_cost(&game.state.players[pi], &cells_column(spalte), &verbleibend);
            assert!((alt - neu).abs() < 1e-9, "Spalte {spalte}: alt={alt} neu={neu}");
        }
    }

    #[test]
    fn mosaic_plattenbau_1_without_legacy_knob_returns_generic_column_path() {
        crate::column_build::set_active_override_for_test(Some(false));
        set_mode_override_for_test(Some(Modus::Fest(1)));
        let game = drafting_game(11);
        // Der generische Pfad muss ETWAS liefern koennen (keine strikte
        // Gleichheit zum Legacy-Pfad gefordert -- das ist der zweite, bewusst
        // getrennte Codepfad, siehe Moduldoku).
        let _ = drafting_preference(&game.state);
        assert_eq!(active_criterion(&game.state), Some(1));
        set_mode_override_for_test(None);
        crate::column_build::set_active_override_for_test(None);
    }

    #[test]
    fn mosaic_plattenbau_0_chooses_row_builder() {
        set_mode_override_for_test(Some(Modus::Fest(0)));
        let game = drafting_game(12);
        assert_eq!(active_criterion(&game.state), Some(0));
        set_mode_override_for_test(None);
    }

    #[test]
    fn auto_mode_scatters_over_game_scoring_tile_ids() {
        set_mode_override_for_test(Some(Modus::Auto));
        let mut game = drafting_game(13);
        game.state.scoring_tile_ids = vec![2, 4, 6];
        set_game_seed(None);
        assert_eq!(active_criterion(&game.state), Some(2), "ohne Seed: erstes aktives Kriterium");
        let mut gesehen = std::collections::HashSet::new();
        for seed in 0u64..40 {
            set_game_seed(Some(seed));
            let k = active_criterion(&game.state).expect("Auto mit gesetzten IDs muss liefern");
            assert!(game.state.scoring_tile_ids.contains(&k), "Kriterium {k} muss unter den 3 aktiven Platten sein");
            gesehen.insert(k);
        }
        set_game_seed(None);
        assert!(gesehen.len() >= 2, "40 Seeds sollten mehr als 1 der 3 IDs treffen: {gesehen:?}");
        set_mode_override_for_test(None);
    }

    #[test]
    fn auto_mode_without_scoring_tile_ids_returns_none() {
        set_mode_override_for_test(Some(Modus::Auto));
        let mut game = drafting_game(14);
        game.state.scoring_tile_ids = Vec::new();
        assert_eq!(active_criterion(&game.state), None);
        set_mode_override_for_test(None);
    }

    /// Kriterium 3 (Mehrfarbig): eine Wild-Zelle in Zeile 0 muss als Ziel
    /// erkannt werden -- jede angebotene Farbe qualifiziert.
    #[test]
    fn multicolor_builder_detects_open_wild_cell_as_target() {
        set_mode_override_for_test(Some(Modus::Fest(3)));
        let mut game = drafting_game(15);
        let pi = game.state.current_player;
        let tile = DomeTile::new(
            300,
            vec![DomeSpace::wild(), DomeSpace::normal(Blau), DomeSpace::normal(Gelb), DomeSpace::normal(Schwarz)],
            0,
        );
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("frei");
        game.state.factories[0].sun_tiles = vec![Rot, Rot];
        let ergebnis = drafting_preference(&game.state);
        assert!(ergebnis.is_some(), "Wild-Zelle muss als Ziel gelten, egal welche Farbe angeboten wird");
        set_mode_override_for_test(None);
    }

    /// Kriterium 4 (Rand): eine offene Randzelle (Zeile 0) muss als Ziel
    /// erkannt werden.
    #[test]
    fn border_builder_detects_open_border_cell_as_target() {
        set_mode_override_for_test(Some(Modus::Fest(4)));
        let mut game = drafting_game(16);
        let pi = game.state.current_player;
        let tile = normal_tile(400, [Rot, Blau, Gelb, Schwarz]);
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("frei");
        game.state.factories[0].sun_tiles = vec![Rot, Rot];
        let ergebnis = drafting_preference(&game.state);
        match ergebnis {
            Some(Action::Stone(m)) => assert_eq!(m.place.row_index, 0),
            other => panic!("erwartet einen Stein-Zug in Zeile 0 (Rand), bekam {other:?}"),
        }
        set_mode_override_for_test(None);
    }

    /// Kriterium 6 (Spezial): eine Special-Zelle mit offenen Nachbarn muss
    /// deren Nachbarn als Ziel liefern (nicht die Special-Zelle selbst).
    #[test]
    fn special_builder_targets_neighbours_not_the_special_cell_itself() {
        set_mode_override_for_test(Some(Modus::Fest(6)));
        let mut game = drafting_game(17);
        let pi = game.state.current_player;
        // Slot (0,0): si=0->Special(Zeile0,Spalte0), si=1..3 normal.
        let tile = DomeTile::new(
            600,
            vec![DomeSpace::special(), DomeSpace::normal(Blau), DomeSpace::normal(Gelb), DomeSpace::normal(Schwarz)],
            0,
        );
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("frei");
        let z = Spezialbauer.zellen(&game.state.players[pi]);
        assert!(!z.contains(&(0, 0)), "die Special-Zelle selbst darf kein Ziel sein");
        assert!(z.contains(&(0, 1)) || z.contains(&(1, 0)) || z.contains(&(1, 1)), "mindestens ein Nachbar muss Ziel sein: {z:?}");
        set_mode_override_for_test(None);
    }

    /// Kriterium 5 (Ecken): Zielzellen fuer Slot-Index 0 muessen exakt die 4
    /// Rasterzellen von Slot (0,0) sein.
    #[test]
    fn cells_corner_returns_the_four_cells_of_the_slot() {
        let mut z = cells_corner(0);
        z.sort();
        assert_eq!(z, vec![(0, 0), (0, 1), (1, 0), (1, 1)]);
        let mut z3 = cells_corner(3);
        z3.sort();
        assert_eq!(z3, vec![(4, 4), (4, 5), (5, 4), (5, 5)]);
    }

    /// Kriterium 7 (Farbenreich): die Kuppelplatten-Wahl muss eine Kachel mit
    /// einer NOCH NICHT vorhandenen Farbe in der Zielreihe einer bevorzugen,
    /// die nur Farben wiederholt, die schon in der Reihe stehen.
    #[test]
    fn colorful_builder_prefers_new_color_in_target_row() {
        set_mode_override_for_test(Some(Modus::Fest(7)));
        let mut game = drafting_game(18);
        let pi = game.state.current_player;
        // Zeile 0 hat schon ALLE VIER Farben Rot/Blau/Gelb/Schwarz stehen
        // (Slot (0,2) Top-Reihe = Rot+Blau, Slot (0,1) Top-Reihe = Gelb+
        // Schwarz) -- nur Slot (0,0) bleibt offen fuer den Vergleich. Damit
        // kann JEDE Rotation von Kachel 702 (nur diese vier Farben) in
        // Zeile 0 hoechstens Score 0 erreichen, unabhaengig von der
        // Rotations-Paarung -- kein Unentschieden wie in der ersten Fassung
        // dieses Tests (dort konnten beide Kacheln denselben Score
        // erreichen, und der erste Kandidat in `dome_display` gewann den
        // Gleichstand).
        let slot02 = normal_tile(701, [Rot, Blau, Gelb, Schwarz]);
        game.state.players[pi].dome_grid.place_dome_tile(slot02, 0, 2).expect("frei");
        {
            let slot = game.state.players[pi].dome_grid.dome_slots[0][2].as_mut().unwrap();
            slot.spaces[0].placed_color = Some(Rot);
            slot.spaces[1].placed_color = Some(Blau);
        }
        let slot01 = normal_tile(704, [Gelb, Schwarz, Rot, Blau]);
        game.state.players[pi].dome_grid.place_dome_tile(slot01, 0, 1).expect("frei");
        {
            let slot = game.state.players[pi].dome_grid.dome_slots[0][1].as_mut().unwrap();
            slot.spaces[0].placed_color = Some(Gelb);
            slot.spaces[1].placed_color = Some(Schwarz);
        }

        game.state.dome_display = vec![
            // Kachel A: nur Farben, die in Zeile 0 schon ALLE vorhanden sind.
            normal_tile(702, [Rot, Blau, Gelb, Schwarz]),
            // Kachel B: Tuerkis ist in Zeile 0 GARANTIERT neu.
            normal_tile(703, [Tuerkis, Blau, Gelb, Schwarz]),
        ];
        let a = Farbenreichbauer.dome_preference(&game.state);
        match a {
            Some(Action::ChooseDomeSlot(m)) => {
                assert_eq!(m.dome_tile_id, 703, "die Kachel mit einer NEUEN Farbe fuer Zeile 0 muss gewinnen");
                assert_eq!(m.slot_row, 0);
                assert_eq!(m.slot_col, 0);
            }
            other => panic!("erwartet ChooseDomeSlot, bekam {other:?}"),
        }
        set_mode_override_for_test(None);
    }
}

// ── v2-Zielbild: 1-2 Spalten + 1-2 Reihen, Nachbarn verbinden ────────────────

/// Zielzellen fuer `mcts::HeuristikVariante::V2` (Nutzer-Zielbild 2026-08-24:
/// "1-2 vollstaendige Spalten, 1-2 vollstaendige Reihen, und dann alles so gut
/// es geht mit Nachbarn verbinden. Eine Diagonale ist dann in der idealen Welt
/// das Beiwerk").
///
/// Waehlt die GUENSTIGSTE Spalte und die GUENSTIGSTE Zeile mit derselben
/// Kostenformel wie die uebrigen Bauer (`target_cells_generic`) und liefert
/// die Vereinigung ihrer Zellen. Der Schnittpunkt beider liegt zwangslaeufig
/// in der Menge -- er ist der natuerliche Anker fuer die Nachbarschaft, weil
/// ein Stein dort BEIDE Linien bedient und nach `engine_manual.md:143-147`
/// horizontal UND vertikal bezahlt wird.
///
/// **Warum eine Vereinigung und keine Auswahl:** die 21-Zellen-Identitaet
/// zeigt, dass eine volle Spalte je einen Abschluss JEDER Musterreihe braucht.
/// Eine Zeile dagegen braucht sechs Zellen DERSELBEN Musterreihe, also
/// mehrere Runden derselben Reihe. Beide Ziele zusammen decken die
/// Zellenmenge so ab, dass fast jeder Abschluss auf mindestens eine der
/// beiden Linien einzahlt -- und genau das fehlt dem Bestand, dessen
/// Platzierung nach reinen Sofortpunkten waehlt
/// (`tiling_solver.rs:49-56`, dort ausdruecklich als Befund vermerkt).
///
/// **Diagonale bewusst NICHT enthalten.** Sie ist laut Zielbild Beiwerk und
/// faellt an, wenn Spalte und Zeile stehen; als eigenes Ziel wuerde sie die
/// Zellenmenge verduennen. `Diagonalenbauer` bleibt fuer den Fall, dass sie
/// jemand ALS Ziel fahren will.
/// Nur die obersten zwei Rasterzeilen kommen als ZEILEN-Ziel in Frage
/// (Nutzer-Vorgabe 2026-08-24: "eigentlich brauchst nur die ersten zwei
/// Reihen anvisieren fuer volle Reihen. die anderen bekommst praktisch nicht
/// zu. das ist ok").
///
/// Deckt sich mit der Messung: Musterreihe 1 und 2 schliessen rund 4,9-mal je
/// Partie ab (`docs/domain_knowledge.md`, und in den Server-Logs 4,90/4,90 auf
/// der KI-Seite), liefern also die fuenf regulaeren Steine, zu denen ein
/// Spezialfeld die sechste Zelle beisteuern kann. Musterreihe 3 kommt auf
/// 2,8-3,3, Reihe 5 und 6 auf 0,7-1,3 -- dort sind sechs Zellen in fuenf
/// Runden auch mit Spezialfliese nicht zu holen. Eine solche Zeile als Ziel
/// anzubieten verduennt nur die Zellenmenge.
const ZEILEN_ZIEL_MAX: usize = 2;

pub(crate) fn v2_target_cells(state: &GameState, pi: usize) -> Option<Vec<(usize, usize)>> {
    let player = &state.players[pi];
    let spalten: Vec<_> = (0..6).map(cells_column).collect();

    // Ab Runde 3 die Spalte FESTNAGELN, in die schon investiert wurde.
    //
    // Befund 2026-08-24: 47,5 Prozent der Partien enden bei 5 von 6, und rund
    // 30 der 38 Beinahe-Treffer sind Routing-Fehler -- Rasterzeile 6 wurde
    // abgeschlossen (nur 10 Prozent der Partien haben gar keinen
    // R6-Abschluss), der Stein landete nur in einer anderen Spalte. Ursache
    // ist der frische Neuentscheid bei JEDEM Aufruf: wechselt das Ziel
    // zwischen dem Fuettern der Musterreihe und ihrem Tiling, ist die
    // Investition verstreut.
    //
    // Umgesetzt OHNE gespeicherten Zustand: "die Spalte mit dem hoechsten
    // Fuellstand" ist von sich aus stabil, weil sie ihren Vorsprung behaelt.
    // Damit entfaellt das Leck-Risiko, vor dem `column_build.rs` bei einer
    // persistenten Zielspalte ausdruecklich warnt (eine fruehere Fassung dort
    // wurde nach vier Messungen verworfen, weil die Bindung der Kostenformel
    // die Reaktionsfaehigkeit nahm). Gleichstand faellt weiter an die
    // Kostenformel, und in Runde 1-2 entscheidet sie allein -- da gibt es
    // noch nichts zu halten.
    let s = if state.round_number >= 3 {
        let fuellung = column_fill_local(player);
        let max = fuellung.iter().copied().max().unwrap_or(0);
        if max > 0 {
            let fuehrende: Vec<_> = (0..6)
                .filter(|&c| fuellung[c] == max)
                .map(cells_column)
                .collect();
            target_cells_generic(state, pi, &fuehrende)?
        } else {
            target_cells_generic(state, pi, &spalten)?
        }
    } else {
        target_cells_generic(state, pi, &spalten)?
    };

    // Zeilen NUR aus den obersten ZWEI Rasterzeilen und nur, wo ein
    // Spezialfeld sie ueberhaupt vollendbar macht (s. Doku unten).
    let zeilen: Vec<_> = (0..ZEILEN_ZIEL_MAX)
        .filter(|&r| row_is_completable(player, r))
        .map(cells_row)
        .collect();
    let mut alle = s;
    if let Some(z) = target_cells_generic(state, pi, &zeilen) {
        for zelle in z {
            if !alle.contains(&zelle) {
                alle.push(zelle);
            }
        }
    }
    Some(alle)
}

/// Kann Rasterzeile `r` ueberhaupt voll werden?
///
/// **Ohne Spezialfliese nicht.** Rasterzeile `r` wird ausschliesslich von
/// Musterreihe `r` gespeist (`round_end::validate_tiling_action` erzwingt die
/// Zuordnung), und die schliesst hoechstens EINMAL je Runde ab -- bei fuenf
/// Runden also maximal fuenf Steine fuer sechs Zellen. Die sechste Zelle kann
/// nur ein Spezialfeld sein, das automatisch belegt wird, sobald die drei
/// anderen regulaeren Zellen seiner Platte voll sind
/// (`docs/engine_manual.md:168-174`).
///
/// Fuer SPALTEN gilt das nicht: ihre sechs Zellen kommen aus sechs
/// VERSCHIEDENEN Musterreihen, je ein Abschluss je Runde genuegt. Die
/// Asymmetrie ist der Grund, warum die erste Fassung dieses Ziels die Zeilen
/// von 0,425 auf 0,188 gedrueckt hat: sie behandelte beide gleichrangig und
/// steckte Aufwand in Zeilen, die per Konstruktion nie fertig werden konnten.
///
/// Geprueft wird deshalb: traegt irgendein Slot dieser Rasterzeile ein
/// Spezialfeld, und ist es entweder schon belegt oder noch freischaltbar
/// (also nicht dauerhaft blockiert)? Wenn nicht, ist die Zeile als ZIEL
/// wertlos und wird gar nicht erst angeboten.
fn row_is_completable(player: &PlayerBoard, r: usize) -> bool {
    let tr = r / 2;
    let teilreihe = r % 2;
    (0..3).any(|tc| {
        let Some(slot) = player.dome_grid.dome_slots[tr][tc].as_ref() else {
            return false;
        };
        let Some(si) = slot.special_space_idx() else {
            return false;
        };
        // Liegt das Spezialfeld dieser Platte in DIESER Teilreihe? Ob es schon
        // belegt oder noch gesperrt ist, spielt keine Rolle: gesperrt heisst
        // freischaltbar (die drei regulaeren Zellen sind das Ziel), belegt
        // heisst, es fehlen nur noch fuenf regulaere Zellen. Ausgeschlossen
        // werden soll nur der Fall "in dieser Rasterzeile gibt es gar kein
        // Spezialfeld" -- dann sind sechs Zellen in fuenf Runden unmoeglich.
        si / 2 == teilreihe
    })
}


/// Orientierung der Zielhuelle nach der KOSTENFORMEL.
///
/// Verglichen werden die beiden RANDSPALTEN 0 und 5 -- Prio 1 der Leiter und
/// damit die Spalte, an der die ganze Huelle haengt. Bewusst NICHT die 28
/// Zellen der ganzen Karte: die sind zu grossen Teilen dieselben und
/// unterscheiden die beiden Seiten kaum noch. Die Randspalte ist derselbe
/// 6-Zellen-Vergleich, den [`v2_target_cells`] ueber alle sechs Spalten
/// fuehrt, nur auf die beiden zulaessigen Kanten eingeschraenkt -- und er
/// laeuft ueber [`target_index_generic`], behaelt also die Seed-Streuung, an
/// der die gestreute Start-Ecke haengt.
fn envelope_orientation_by_cost(state: &GameState, pi: usize) -> Option<usize> {
    let kandidaten = vec![cells_column(0), cells_column(5)];
    target_index_generic(state, pi, &kandidaten)
}

/// Zielkarte fuer `mcts::HeuristikVariante::V2Huelle`: die Prio-Leiter in
/// einer der beiden Orientierungen.
///
/// Unterschied zu [`v2_target_cells`]: dort ist das Ziel die Vereinigung aus
/// EINER billigsten Spalte und EINER billigsten oberen Zeile (6-12 Zellen,
/// alle gleich viel wert). Hier sind es 28 Zellen auf vier Prioritaetsstufen
/// ([`target_map`]), die die alte Menge als Teilmenge enthalten: Prio 1 ist
/// eine volle Randspalte, Prio 3 sind die beiden oberen Rasterzeilen.
///
/// **Die Festnagelung ab Runde 3 bleibt**, nur auf der Orientierung statt auf
/// der Spalte. Sie war der Bauschritt, der die Partien mit mindestens einer
/// vollen Spalte von 35 auf 50 Prozent gehoben hat; sie hier fallen zu lassen
/// waere ein zweiter, mit der Huelle konfundierter Unterschied.
pub(crate) fn v2_envelope_target(state: &GameState, pi: usize) -> Option<Zielkarte> {
    let player = &state.players[pi];
    let ids = &state.scoring_tile_ids;
    let orientierung = if state.round_number >= 3 {
        let f0 = map_fill(player, &target_map(player, ids, 0));
        let f1 = map_fill(player, &target_map(player, ids, 1));
        if f0 > f1 {
            0
        } else if f1 > f0 {
            1
        } else {
            // Gleichstand faellt wie in `v2_target_cells` an die Kostenformel;
            // in Runde 1-2 entscheidet sie ohnehin allein.
            envelope_orientation_by_cost(state, pi)?
        }
    } else {
        envelope_orientation_by_cost(state, pi)?
    };
    Some(target_map(player, ids, orientierung))
}

/// Drafting-Vorzug fuer v2 -- UNGEGATET, also ohne `MOSAIC_SPALTENBAU` und
/// ohne `MOSAIC_PLATTENBAU`.
///
/// Beide Bestandsknoepfe sind prozessweit. Fuer eine Partie v1 GEGEN v2 sind
/// sie damit unbrauchbar: sie gaelten fuer beide Seiten oder fuer keine. Die
/// Variante ist der einzige Weg, der die Seiten trennt.
pub(crate) fn v2_drafting_preference(
    state: &GameState,
    variante: crate::mcts::HeuristikVariante,
) -> Option<Action> {
    if let Some((karte, wert)) = v2_map_for(state, state.current_player, variante) {
        let z = cells_from_map(&karte);
        return envelope_drafting_preference(state, &karte, &z)
            .or_else(|| dome_preference_for_cells_weighted(state, &z, &karte, wert));
    }
    let z = v2_target_cells(state, state.current_player)?;
    // Erst der Stein-Zug, dann die KUPPELPLATTEN-Wahl. Die zweite war bis
    // 2026-08-24 nicht verdrahtet, und sie ist der Grund, warum die
    // gestreute Start-Ecke die vollen Zeilen von 0,400 auf 0,263 gedrueckt
    // hat: startet die Kuppel unten, liegt in den oberen Rasterzeilen frueh
    // keine Platte, und genau die sind das Zeilenziel. Nutzer-Vorgabe
    // 2026-08-24: "dann muss man halt Kuppel ziehen fuer die oberen
    // Rasterzeilen".
    //
    // `dome_preference_for_cells` waehlt Platte, Slot und Rotation so, dass die
    // Zielzellen bedienbar werden -- laut `column_build.rs`-Moduldoku die
    // Stelle, die "bisher nie gesteuert" wurde, obwohl sie `required_color`
    // der Zellen bestimmt.
    preference_move_for_cells(state, &z).or_else(|| dome_preference_for_cells(state, &z))
}

/// Tiling-Routing fuer v2 -- ungegatet, siehe [`v2_drafting_preference`].
///
/// Das ist die Haelfte, die der bisherige v2-Term GAR NICHT beruehrt hat und
/// die laut `PREREG_provocation.md` der eigentliche Engpass ist ("der Engpass
/// ist die PLATZIERBARKEIT, nicht die Plattenbewertung"): ohne sie waehlt
/// `best_first_step_inner` nach reinen Sofortpunkten und wirft jede
/// Draft-seitige Absicht wieder weg.
pub(crate) fn v2_tiling_preference(
    state: &GameState,
    pi: usize,
    variante: crate::mcts::HeuristikVariante,
) -> Option<TilingStep> {
    if let Some((karte, _)) = v2_map_for(state, pi, variante) {
        let z = cells_from_map(&karte);
        return v2_chip_preference(state, pi, &z)
            .or_else(|| tiling_preference_for_cells_weighted(state, pi, &z, &karte));
    }
    let z = v2_target_cells(state, pi)?;
    // Chip-Einsatz auf die BLOCKIERENDE Reihe zuerst. Befund 2026-08-24:
    // trotz Routing null Chip-Vollendungen von Rasterreihe 6 in 80 Partien,
    // und 7,5 Prozent der Partien haben ueberhaupt keinen R6-Abschluss --
    // ausnahmslos ohne jede volle Spalte. Die generische Suche unten
    // (`tiling_preference_for_cells`, ueber `top_k_tilings`) SCHLIESST
    // Chip-Schritte technisch ein (`legal_steps` -> `chippable_rows`), findet
    // sie aber im DFS-Budget (2000 Knoten, `NODE_BUDGET`) offenbar nicht
    // zuverlaessig -- die Verzweigung ueber Chip-Allokationen ist teuer.
    // Ein direkter Vorzug macht die Absicht explizit statt auf den
    // Suchzufall zu hoffen.
    v2_chip_preference(state, pi, &z).or_else(|| tiling_preference_for_cells(state, pi, &z))
}

/// Vollendet per Bonuschip die Musterreihe, die eine ZIELZELLE blockiert --
/// nur wenn diese Zelle sonst leer bliebe UND die Chip-Vollendung sofort
/// platzierbar ist (`row_has_open_matching_slot`). Kein Griff in fremde
/// Reihen: eine Reihe, die keine Zielzelle bedient, wird nie angefasst,
/// Bonuschips bleiben dafuer erhalten.
fn v2_chip_preference(state: &GameState, pi: usize, zellen: &[(usize, usize)]) -> Option<TilingStep> {
    let player = &state.players[pi];
    if player.bonus_chips.is_empty() {
        return None;
    }
    // `zellen` sind RASTER-Koordinaten (r, c) im 6x6-Raster -- dieselbe
    // Konvention wie `column_build::cell_cost`. Musterreihe r speist
    // GENAU Rasterreihe r (`round_end::row_has_open_matching_slot` benutzt
    // dieselbe Zuordnung: `dome_row = r/2, space_row = r%2`), ein Umweg ueber
    // Slot-Koordinaten ist unnoetig -- `get_space` uebernimmt die Umrechnung.
    for &(r, c) in zellen {
        let Some(sp) = player.dome_grid.get_space(r, c) else { continue };
        if sp.is_filled() || sp.is_locked {
            continue;
        }
        let row = &player.pattern_lines[r];
        if row.tiles.is_empty() || row.is_complete() {
            continue;
        }
        let Some(color) = row.color else { continue };
        if !sp.accepts(color) {
            continue; // diese Zelle nimmt eine ANDERE Farbe/keine Normalfarbe
        }
        if (r as i32) < player.tiled_max_row {
            continue; // Top-down-Sperre
        }
        if !crate::round_end::can_complete_row_with_chips(player, r) {
            continue;
        }
        if !crate::round_end::row_has_open_matching_slot(player, r, color) {
            continue;
        }
        if let Some(chips) = crate::round_end::greedy_chip_alloc(player, r) {
            return Some(TilingStep::Chips { row: r, chips });
        }
    }
    None
}


/// Fuellstand je Brett-Spalte. Lokale Kopie der Abbildung aus
/// `heuristic_v2::column_fill` (Slot `(tr,tc)`, Space `si` -> Spalte
/// `2*tc + si%2`), damit dieses Modul nicht auf ein anderes zugreifen muss.
fn column_fill_local(player: &PlayerBoard) -> [u32; 6] {
    let mut fill = [0u32; 6];
    for reihe in player.dome_grid.dome_slots.iter() {
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

#[cfg(test)]
mod huellen_tests {
    use super::*;
    use crate::dome::build_dome_tile_pool;

    /// Die Prio-Leiter, Zelle fuer Zelle (Nutzer-Vorgabe 2026-08-24,
    /// erweiterte Fassung). Ohne diesen Test waere eine vertauschte Stufe nur
    /// in einer Arena sichtbar -- und dort nicht von "das Konzept traegt
    /// nicht" zu unterscheiden.
    ///
    /// Leeres Brett: ohne Kuppelplatten greift die Prio-5-Auflage nicht, der
    /// Test sieht also das reine Grundbild.
    #[test]
    fn target_map_reflects_the_priority_ladder() {
        let p = crate::board::PlayerBoard::new(0, "P");
        let k = target_map(&p, &[], 0);
        for r in 0..6 {
            assert_eq!(k[r][0], PRIO_GEWICHT[0], "Prio 3: Randspalte 0, Zeile {r}");
            assert_eq!(k[r][1], PRIO_GEWICHT[1], "Prio 4: zweite Spalte 1, Zeile {r}");
        }
        for c in 2..6 {
            assert_eq!(k[0][c], PRIO_GEWICHT[3], "Prio 6: Rasterzeile 0, Spalte {c}");
            assert_eq!(k[1][c], PRIO_GEWICHT[3], "Prio 6: Rasterzeile 1, Spalte {c}");
            assert_eq!(k[2][c], PRIO_GEWICHT[4], "Prio 7: Nachbar Rasterzeile 2, Spalte {c}");
            assert_eq!(k[3][c], PRIO_GEWICHT[4], "Prio 7: Nachbar Rasterzeile 3, Spalte {c}");
            // Rasterzeile 4 und 5 ausserhalb der beiden Spalten: NICHT im
            // Grundbild. Jede Zelle dort kostet einen Abschluss von
            // Musterreihe 5 bzw. 6, und die sind in Prio 3/4 besser angelegt.
            assert_eq!(k[4][c], 0.0, "Rasterzeile 4, Spalte {c} darf nicht im Grundbild sein");
            assert_eq!(k[5][c], 0.0, "Rasterzeile 5, Spalte {c} darf nicht im Grundbild sein");
        }
        // Strenge Rangfolge -- die einzige Eigenschaft, die die Leiter fordert.
        for i in 0..4 {
            assert!(PRIO_GEWICHT[i] > PRIO_GEWICHT[i + 1], "Stufe {i} muss ueber {} liegen", i + 1);
        }
        assert!(PRIO_GEWICHT[4] > 0.0);
        // Prio 5 (Wertungsplatten) steht ueber Prio 6 (kurze Reihen) --
        // die Umstellung der erweiterten Fassung.
        assert!(PRIO_GEWICHT[2] > PRIO_GEWICHT[3]);
    }

    /// "Bei Verwendung der Diagonale wird Prio 7 aufgeweicht."
    #[test]
    fn active_diagonal_softens_the_neighbour_tiebreak() {
        let p = crate::board::PlayerBoard::new(0, "P");
        let ohne = target_map(&p, &[], 0);
        let mit = target_map(&p, &[K2_DIAGONALEN], 0);
        assert_eq!(ohne[2][3], PRIO_GEWICHT[4]);
        assert_eq!(mit[2][3], PRIO7_AUFGEWEICHT);
        assert!(PRIO7_AUFGEWEICHT < PRIO_GEWICHT[4]);
        // Die uebrigen Stufen bleiben unberuehrt.
        assert_eq!(ohne[0][0], mit[0][0]);
        assert_eq!(ohne[0][3], mit[0][3]);
    }

    /// Prio 5, Auflage: die leeren REGULAEREN Zellen einer Platte mit noch
    /// gesperrtem Spezialfeld steigen auf die Wertungsplatten-Stufe -- auch
    /// dort, wo das Grundbild 0 sagt. Der Ertrag haengt nicht an einem
    /// weiteren Musterreihen-Abschluss, sondern faellt beim Freischalten an
    /// (`round_end::check_special_trigger`).
    #[test]
    fn prio5_raises_unlock_cells_even_from_zero() {
        let mut p = crate::board::PlayerBoard::new(0, "P");
        // Platte 0 traegt ein Spezialfeld; in Slot (2,1) deckt sie die
        // Rasterzellen (4,2),(4,3),(5,2),(5,3) -- im Grundbild alle 0.
        let tile = build_dome_tile_pool()[0].clone();
        p.dome_grid.place_dome_tile(tile, 2, 1).unwrap();
        let k = target_map(&p, &[], 0);
        let angehoben = [(4, 2), (4, 3), (5, 2), (5, 3)]
            .iter()
            .filter(|&&(r, c)| k[r][c] >= PRIO_GEWICHT[2])
            .count();
        assert_eq!(angehoben, 3, "genau die drei REGULAEREN Zellen steigen, nicht das Spezialfeld selbst");
        // Gegenprobe: eine Zelle ohne Platte bleibt bei 0.
        assert_eq!(k[4][4], 0.0);
    }

    /// Strafpunkte sind MARGINAL ab dem aktuellen Fuellstand, gedeckelt bei
    /// `MAX_BROKEN` -- dieselbe Rechnung wie
    /// `round_end::projected_unplaceable_penalty`.
    #[test]
    fn floor_points_are_marginal_and_capped() {
        let mut p = crate::board::PlayerBoard::new(0, "P");
        assert_eq!(floor_points(&p, 0), 0);
        assert_eq!(floor_points(&p, 1), -1);
        assert_eq!(floor_points(&p, 2), -3); // -1 + -2
        assert_eq!(floor_points(&p, 9), -10, "gedeckelt bei MAX_BROKEN = 4");
        // Mit einer bereits liegenden Fliese kostet die naechste MEHR.
        p.broken_tiles.push(crate::tile::TileColor::Rot);
        assert_eq!(floor_points(&p, 1), -2);
        // Und die Schwelle greift erst ab dem vorgegebenen Punktwert.
        assert!(floor_points(&p, 1) > STRAF_SCHWELLE_PUNKTE);
        assert!(floor_points(&p, 2) <= STRAF_SCHWELLE_PUNKTE);
    }

    /// Orientierung 1 ist Orientierung 0, an der SPALTEN-Achse gespiegelt --
    /// und nur an ihr. Eine Spiegelung um die Reihen-Achse verlangte eine
    /// volle Rasterzeile 5 (nur von Musterreihe 6 gespeist, 0,74-1,31
    /// Abschluesse je Partie) und ist deshalb nicht vorgesehen.
    #[test]
    fn orientation_1_is_the_column_mirror() {
        let p = crate::board::PlayerBoard::new(0, "P");
        let links = target_map(&p, &[], 0);
        let rechts = target_map(&p, &[], 1);
        for r in 0..6 {
            for c in 0..6 {
                assert_eq!(links[r][c], rechts[r][5 - c], "Zelle ({r},{c})");
            }
        }
        // Gegenprobe: KEINE Reihen-Spiegelung. Zeile 0 traegt Prio 3, Zeile 5
        // ausserhalb der Spalten gar nichts -- waeren sie gespiegelt, muesste
        // das Bild dort gleich aussehen.
        assert_ne!(links[0][3], links[5][3]);
    }

    /// 28 Zellen: 2 volle Spalten (12) plus die beiden oberen Zeilen (8) plus
    /// die Nachbarzeilen 2 und 3 (8), jeweils ausserhalb der zwei Spalten.
    #[test]
    fn target_set_has_28_cells() {
        let p = crate::board::PlayerBoard::new(0, "P");
        let z = cells_from_map(&target_map(&p, &[], 0));
        assert_eq!(z.len(), 28);
        assert!(!z.contains(&(4, 3)), "Rasterzeile 4 ausserhalb der Spalten gehoert nicht dazu");
        assert!(z.contains(&(5, 0)) && z.contains(&(5, 1)), "beide Spalten reichen bis Rasterzeile 5");
    }

    /// Prio 2, Kern: auf Rasterzeile 5 schlaegt das Spezialfeld den Joker und
    /// beide jede Normalfarbe. Grund ist mechanisch -- das Spezialfeld wird
    /// gratis belegt (`round_end::check_special_trigger`), waehrend jede
    /// andere Zelle dort einen Musterreihe-6-Abschluss kostet.
    #[test]
    fn on_row_5_special_beats_wild() {
        let p = crate::board::PlayerBoard::new(0, "P");
        // Platte 0 = [Gelb, Schwarz, Tuerkis, Special]; Space 3 ist Special.
        let tile = build_dome_tile_pool()[0].clone();
        let special = &tile.spaces[3];
        let normal = &tile.spaces[0];
        assert_eq!(special.space_type, SpaceType::Special);
        assert_eq!(normal.space_type, SpaceType::Normal);

        let s_special = envelope_cell_value(&p, 5, 1, special);
        let s_normal = envelope_cell_value(&p, 5, 1, normal);
        assert!(s_special > s_normal, "Special {s_special} muss Normal {s_normal} schlagen");
        // Ausserhalb von Rasterzeile 5 unveraendert zum Bestand: dort gilt die
        // Knappheitsbegruendung nicht.
        for r in 0..5 {
            assert_eq!(
                envelope_cell_value(&p, r, 1, special),
                legacy_cell_value(&p, r, 1, special),
                "Rasterzeile {r} darf nicht abweichen"
            );
        }
    }

    /// Der gewichtete Fuellstand entscheidet die Orientierungs-Festnagelung ab
    /// Runde 3. Ein Brett mit Belegung LINKS muss links hoeher stehen.
    #[test]
    fn map_fill_detects_the_served_side() {
        let mut p = crate::board::PlayerBoard::new(0, "P");
        let tile = build_dome_tile_pool()[0].clone();
        p.dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        p.dome_grid.place_tile(0, 0, crate::tile::TileColor::Gelb).unwrap();
        let links = map_fill(&p, &target_map(&p, &[], 0));
        let rechts = map_fill(&p, &target_map(&p, &[], 1));
        assert!(links > rechts, "links {links} muss ueber rechts {rechts} liegen");
    }
}

#[cfg(test)]
mod v2_chip_vorzug_tests {
    use super::*;
    use crate::dome::{build_dome_tile_pool, BonusChip};
    use crate::tile::TileColor::*;
    use rand::SeedableRng;

    /// Baut einen Zustand mit: Kuppelplatte in Slot (0,0), Musterreihe 1
    /// (Kapazitaet 2) mit EINER Fliese (Rot), einem Space in Slot (0,0), das
    /// Rot akzeptiert und noch leer ist, und zwei passenden Chips. Erwartung:
    /// `v2_chip_preference` findet die Vollendung.
    #[test]
    fn finds_chip_completion_for_blocking_row() {
        let mut state = crate::game::Game::start(
            ["A".to_string(), "B".to_string()], 0, vec![], &mut rand::rngs::StdRng::seed_from_u64(1),
        ).state.clone();
        let pi = 0;
        let tile = build_dome_tile_pool()[0].clone();
        state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        // Musterreihe 1 (Index 1, Kapazitaet 2) mit einer Fliese TUERKIS --
        // cell_to_dome_space(1,0) = Slot(0,0) Space 2, und Platte pool[0] hat
        // dort Tuerkis (siehe board.rs-Test "Platte 0 = [Gelb, Schwarz,
        // Tuerkis, Special]").
        state.players[pi].pattern_lines[1].add_tiles(&[Tuerkis]);
        // Zwei tuerkise Chips.
        state.players[pi].bonus_chips = vec![
            BonusChip { chip_id: 100, colors: vec![Tuerkis] },
            BonusChip { chip_id: 101, colors: vec![Tuerkis] },
        ];
        // Zielzellen: die ganze Spalte 0 (enthaelt (1,0), die Zielzelle
        // dieser Musterreihe -- siehe cell_to_dome_space: Reihe 1 -> Slot
        // (0,0), Space 2).
        let zellen: Vec<(usize, usize)> = (0..6).map(|r| (r, 0)).collect();
        let ok = state.players[pi].dome_grid.get_space(1, 0).map(|s| !s.is_filled() && !s.is_locked);
        assert_eq!(ok, Some(true), "Vorbedingung: Zielzelle (1,0) muss offen sein");
        let schritt = v2_chip_preference(&state, pi, &zellen);
        assert!(matches!(schritt, Some(TilingStep::Chips { row: 1, .. })),
                "erwartet Chips{{row:1}}, bekam {schritt:?}");
    }
}
