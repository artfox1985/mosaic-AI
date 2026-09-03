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
                    // 0..7 = Wertungskriterien, 8 = Huellen-Bauer (par.8.8).
                    Ok(k) if k <= 8 => Modus::Fest(k),
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
        // par.8.8 der Einhuellenden-Prereg (Nutzer 2026-09-03): kein Wertungs-
        // kriterium, sondern die Huelle selbst als Zielgeometrie.
        8 => &HULL_BUILDER,
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

/// Bester erreichbarer Wert EINER Kuppelplatte auf dem aktuellen Brett,
/// maximiert ueber Slot und Rotation. **Rohwert, nicht auf `> 0` gefiltert.**
///
/// Gebaut auf Anfrage der Parallelsitzung fuer die Reservationswert-Regel der
/// Blindziehung (`docs/research_heuristics_external.md` §3). Bisher rechnete
/// [`dome_preference_for_cells_weighted`] dieses Maximum intern aus und warf
/// es weg -- sie liefert nur die Aktion.
///
/// `wert` wird durchgereicht, damit derselbe Aufruf mit
/// [`legacy_cell_value`] (Praeferenz-Einheiten) ODER mit einer
/// Punktebewertung laufen kann. Fuer die Reservationsregel ist NUR die
/// Punktevariante zulaessig: die Regel loest `E[max(V - R, 0)] = c` mit
/// `c = 1 PUNKT`, und `legacy_cell_value` ist dimensionslos (Wild 3,0,
/// Special 2,0, ...) -- ein `R` aus gemischten Einheiten waere eine Zahl
/// ohne Bedeutung.
///
/// **Legalitaet nur geometrisch** (freier Slot, gueltige Rotation), NICHT
/// gegen `state.dome_display` geprueft. Fuer eine Reservationsregel ist die
/// Platte bereits in der Hand; die Frage lautet "was waere sie mir wert",
/// nicht "darf ich sie gerade nehmen". Wer Display-Legalitaet braucht, filtert
/// vorher.
///
/// **ZWEI SKALEN-VORBEHALTE, die diese Funktion NICHT abraeumt** (beide von
/// der Parallelsitzung benannt, hier festgehalten, damit sie beim Aufrufer
/// ankommen):
///
/// 1. **Die Summe ueber die vier Zellen ist keine Identitaet, sondern eine
///    Naeherung mit bekannter Richtung (eher zu hoch).**
///    `scoring::scoring_progress` ist ueber Zellen NICHT additiv -- zwei
///    Zellen, die zusammen eine Spalte schliessen, sind gemeinsam mehr wert
///    als einzeln, und der gemeinsame Anteil wird bei getrennter Zaehlung
///    doppelt gezaehlt. Wer den exakten Plattenwert braucht, belegt die vier
///    Zellen auf einem Probe-Brett GEMEINSAM und nimmt EINE
///    `scoring_progress`-Differenz.
/// 2. **Potenzial ist nicht Realisierung.** Eine Platte fuellt keine Zelle,
///    sie macht sie bedienbar; die Steine muessen noch gedraftet und
///    gekachelt werden. Ein `V` aus reinen Potenzialpunkten laesst eine
///    Reservationsregel zu oft ziehen. Der Abschlag ist messbar statt
///    schaetzbar: `docs/domain_knowledge.md:30-35` gibt die Abschluesse je
///    Musterreihe und Partie mit 4,80 / 4,77 / 2,84 / 1,89 / 0,84 / 0,58 an
///    (in dieser Sitzung nachgesehen).
#[allow(dead_code)] // Verbraucher ist die Reservationswert-Regel der Parallelsitzung
pub(crate) fn best_plate_value(
    player: &PlayerBoard,
    tile: &crate::dome::DomeTile,
    zellen: &[(usize, usize)],
    karte: &Zielkarte,
    wert: fn(&PlayerBoard, usize, usize, &DomeSpace) -> f64,
) -> Option<f64> {
    let mut best: Option<f64> = None;
    for &(sr, sc) in &player.dome_grid.empty_slots() {
        for rot in [0u32, 90, 180, 270] {
            if let Some(score) = slot_score_generic(player, tile, sr, sc, rot, zellen, karte, wert) {
                if best.is_none_or(|b| score > b) {
                    best = Some(score);
                }
            }
        }
    }
    best
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

/// par.15: **Erreichbarkeit als MASS statt als TOR.**
///
/// Je Rasterspalte der noch erreichbare Endfuellstand: aktueller Fuellstand
/// plus die leeren Zellen, die nach der Restversorgung noch bedienbar sind
/// (`column_build::cell_is_completable`, dieselbe Relaxation wie in par.12 --
/// nur gezaehlt statt als Ja/Nein gelesen).
/// Sichtbar fuer `serialize::serialize_player` (Erreichbarkeits-Felder im
/// Zustands-JSON) -- die Formel soll genau einmal existieren.
pub(crate) fn achievable_column_fill(player: &PlayerBoard, remaining: &[i64; 5]) -> [f64; 6] {
    let mut out = [0.0f64; 6];
    for (c, slot) in out.iter_mut().enumerate() {
        let mut n = 0u32;
        for r in 0..6 {
            let belegt = player.dome_grid.get_space(r, c).is_some_and(|sp| sp.is_filled());
            if belegt || crate::column_build::cell_is_completable(player, r, c, remaining) {
                n += 1;
            }
        }
        *slot = n.min(6) as f64;
    }
    out
}

// -- Prio 0/1/2: die Leiter oberhalb der Zielkarte ---------------------------

// -- Punkte-Heatmap (Nutzer-Vorschlag 2026-08-25) ---------------------------

/// Zellenwert fuer die PLATTENWAHL, Bestandsfassung: unveraendert
/// `column_build::cell_value`.
fn legacy_cell_value(player: &PlayerBoard, r: usize, _c: usize, space: &DomeSpace) -> f64 {
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

// ── par.8.8: Huellen-Bauer (MOSAIC_PLATTENBAU=8) ─────────────────────────────
//
// Nutzer 2026-09-03: "die Huelle wird kommen, um die ersten Runden stabiler
// zu gestalten" und "werden die Kuppelplatten entsprechend gelegt, um die
// Huelle zu unterstuetzen?" -- bisher nicht. Dieser Bauer legt die drei
// Vorzuege des Plattenbauers (Draft, Kuppelplatte, Tiling) auf die Zellen
// der bestpassenden Dreiecks-Huelle (`envelope::Hull`, Definitionen wie die
// Sonde), mit Zielkarte = Zellenkosten `r + 1` (par.8.1): eine Zelle der
// Rasterzeile 5 zaehlt sechsmal so viel wie eine der Zeile 0, und genau die
// Kuppelplatten, deren Zellen in der Huelle liegen UND zur Farbe der
// zugehoerigen Musterreihe passen, bekommen den Kuppel-Vorzug
// (`dome_preference_for_cells_weighted` mit `legacy_cell_value`).
// Orientierung: wie jeder Bauer per Kostenvergleich der beiden Kandidaten
// (`target_index_generic`, Seed-Streuung bei Gleichstand), NICHT per
// Abweichungsregel der Sonde -- auf dem leeren Brett gaebe die sonst immer
// LINKS.

struct HullBuilder;
impl HullBuilder {
    fn hull_cells(hull: crate::envelope::Hull) -> Vec<(usize, usize)> {
        let mut v = Vec::with_capacity(21);
        for r in 0..6 {
            for c in 0..6 {
                if hull.contains(r, c) {
                    v.push((r, c));
                }
            }
        }
        v
    }

    fn cells(&self, state: &GameState, pi: usize) -> Option<Vec<(usize, usize)>> {
        let kand = vec![
            Self::hull_cells(crate::envelope::Hull::Left),
            Self::hull_cells(crate::envelope::Hull::Right),
        ];
        let idx = target_index_generic(state, pi, &kand)?;
        Some(kand[idx].clone())
    }

    /// Zielkarte par.8.1: Zellenkosten `r + 1` auf den Huellenzellen, 0 sonst.
    fn target_map(cells: &[(usize, usize)]) -> Zielkarte {
        let mut k = [[0.0f64; 6]; 6];
        for &(r, c) in cells {
            k[r][c] = crate::envelope::row_cost(r);
        }
        k
    }
}
impl Plattenbauer for HullBuilder {
    fn drafting_preference(&self, state: &GameState) -> Option<Action> {
        let z = self.cells(state, state.current_player)?;
        preference_move_for_cells_weighted(state, &z, &Self::target_map(&z))
    }
    fn dome_preference(&self, state: &GameState) -> Option<Action> {
        let z = self.cells(state, state.current_player)?;
        dome_preference_for_cells_weighted(state, &z, &Self::target_map(&z), legacy_cell_value)
    }
    fn tiling_preference(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        let z = self.cells(state, pi)?;
        tiling_preference_for_cells_weighted(state, pi, &z, &Self::target_map(&z))
    }
}
static HULL_BUILDER: HullBuilder = HullBuilder;

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


    /// par.8.8: beide Huellen haben 21 Zellen mit Gesamtkost 56, die Zielkarte
    /// traegt genau die Zellenkosten r + 1 auf den Huellenzellen.
    #[test]
    fn hull_builder_cells_and_map_match_par_8_1() {
        for hull in [crate::envelope::Hull::Left, crate::envelope::Hull::Right] {
            let z = HullBuilder::hull_cells(hull);
            assert_eq!(z.len(), 21);
            let k = HullBuilder::target_map(&z);
            let total: f64 = z.iter().map(|&(r, c)| k[r][c]).sum();
            assert_eq!(total, crate::envelope::HULL_TOTAL_COST);
            assert_eq!(k[5][5], if hull == crate::envelope::Hull::Right { 6.0 } else { 0.0 });
        }
    }
}
