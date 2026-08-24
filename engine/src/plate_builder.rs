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
//! [`aktiver_bauer`] IMMER auf den Spaltenbauer-Wrapper auf, der die
//! bestehenden `column_build::{vorzugszug,vorzug_dome_wahl,vorzug_tiling_step}`
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
//! `column_build.rs`s Kosten-/Auswahlformeln (`special_kosten`,
//! `engpass_aufschlag`, `zellen_wert`, Toleranzband + Seed-Streuung), die
//! dafuer sichtbar gemacht wurden (`pub(crate)`). Die drei uebrigen
//! Kriterien -- Mehrfarbig (3, Jokerfelder), Rand (4, additiv-farbfrei),
//! Spezial (6, Slot-Vervollstaendigung) -- brauchen KEINE Kandidatenauswahl
//! (ihr Zielzellen-Satz ist eindeutig aus dem Brett ablesbar, keine
//! Alternative abzuwaegen) und rufen die generische Vorzugs-/Tiling-Mechanik
//! direkt mit diesem festen Satz auf. Farbenreiche Reihen (7) teilt sich die
//! Zeilen-Kandidatenauswahl, bekommt aber eine EIGENE Kuppelplatten-Logik
//! (Farbvielfalt statt Farbtreffer).

use crate::board::PlayerBoard;
use crate::dome::{rotation_indices, SpaceType};
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
    fn drafting_vorzug(&self, state: &GameState) -> Option<Action>;
    /// Kuppelplatten-Wahl-Vorzug: welche Platte/welcher Slot/welche Rotation
    /// (`Action::ChooseDomeSlot`/`Action::ChooseDomeRotation`).
    fn dome_vorzug(&self, state: &GameState) -> Option<Action>;
    /// Tiling-Routing-Vorzug: welcher naechste Tiling-Schritt.
    fn tiling_vorzug(&self, state: &GameState, pi: usize) -> Option<TilingStep>;
}

// ── Aktivierung: MOSAIC_PLATTENBAU=<0..7|auto>, MOSAIC_SPALTENBAU hat Vorrang ──

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum Modus {
    Aus,
    Fest(usize),
    Auto,
}

fn modus_env() -> Modus {
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
pub(crate) fn set_modus_override_for_test(m: Option<Modus>) {
    MODUS_OVERRIDE.with(|c| c.set(m));
}

fn modus() -> Modus {
    #[cfg(test)]
    {
        if let Some(m) = MODUS_OVERRIDE.with(|c| c.get()) {
            return m;
        }
    }
    modus_env()
}

thread_local! {
    /// Partie-Seed fuer die generische Kandidatenwahl (Auto-Kriterium +
    /// Kandidaten-Streuung bei Kosten-Gleichstand) -- gleiches Muster wie
    /// `column_build::PARTIE_SEED`. [`set_partie_seed`] versorgt BEIDE (siehe
    /// dort), damit self_play.rs nur noch EINE Stelle aufrufen muss.
    static PARTIE_SEED: std::cell::Cell<Option<u64>> = const { std::cell::Cell::new(None) };
}

/// Setzt (oder loescht mit `None`) den Partie-Seed fuer DIESEN Thread -- fuer
/// die generische Mechanik HIER und (Kaskade) fuer `column_build::PARTIE_SEED`,
/// damit self_play.rs an den vier Hook-Stellen nur noch die Abstraktion
/// aufrufen muss, statt zwei Module einzeln zu versorgen. Aufrufer MUSS am
/// Partieende (oder vor der naechsten Partie desselben Threads) mit `None`
/// ueberschreiben (Leck-Warnung wie bei `column_build::set_partie_seed`).
pub(crate) fn set_partie_seed(seed: Option<u64>) {
    PARTIE_SEED.with(|c| c.set(seed));
    crate::column_build::set_partie_seed(seed);
}

/// Deterministische Mischung Seed -> Index `0..n` -- identisches SplitMix64-
/// Muster wie `column_build::index_aus_seed`/`provocation::spalte_aus_seed`
/// (Projekt-Konvention: diese kleine Mischfunktion wird je Modul dupliziert
/// statt geteilt, siehe dortige Kommentare).
fn index_aus_seed(seed: u64, n: usize) -> usize {
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
/// [`aktiver_bauer`]); sonst entscheidet `MOSAIC_PLATTENBAU`. `Auto` streut
/// ueber `state.scoring_tile_ids` -- die tatsaechlich fuer DIESE Partie
/// gezogenen 3 Platten (`scoring.rs`-Doku: "zu Spielbeginn werden 3 ...
/// gewaehlt"), nicht ueber alle 8 -- ein Kriterium ohne Platte auf dem Tisch
/// waere ein wirkungsloser Vorzug.
// Noch UNVERDRAHTET: gedacht fuer die auto-Zielwahl ueber die aktiven Platten;
// die heutige auto-Streuung waehlt direkt. Bleibt als vorbereiteter Baustein.
#[allow(dead_code)]
fn aktives_kriterium(state: &GameState) -> Option<usize> {
    if crate::column_build::ist_aktiv() {
        return Some(1);
    }
    match modus() {
        Modus::Aus => None,
        Modus::Fest(k) => Some(k),
        Modus::Auto => auto_kriterium(state),
    }
}

fn auto_kriterium(state: &GameState) -> Option<usize> {
    let ids = &state.scoring_tile_ids;
    if ids.is_empty() {
        return None; // defensiv: vor Partie-Setup oder in einem Test ohne Platten.
    }
    match PARTIE_SEED.with(|c| c.get()) {
        None => Some(ids[0]),
        Some(seed) => Some(ids[index_aus_seed(seed, ids.len())]),
    }
}

// ── Dispatch: acht zustandslose Bauer + der Legacy-Wrapper ──────────────────

struct SpaltenbauerLegacy;
impl Plattenbauer for SpaltenbauerLegacy {
    fn drafting_vorzug(&self, state: &GameState) -> Option<Action> {
        crate::column_build::vorzugszug(state)
    }
    fn dome_vorzug(&self, state: &GameState) -> Option<Action> {
        crate::column_build::vorzug_dome_wahl(state)
    }
    fn tiling_vorzug(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        crate::column_build::vorzug_tiling_step(state, pi)
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

fn bauer_fuer(kriterium: usize) -> &'static dyn Plattenbauer {
    match kriterium {
        0 => &ZEILENBAUER,
        1 => &SPALTENBAUER_GENERISCH,
        2 => &DIAGONALENBAUER,
        3 => &MEHRFARBIGBAUER,
        4 => &RANDBAUER,
        5 => &ECKENBAUER,
        6 => &SPEZIALBAUER,
        7 => &FARBENREICHBAUER,
        _ => &ZEILENBAUER, // defensiv; aktives_kriterium liefert nie >7.
    }
}

fn aktiver_bauer(state: &GameState) -> Option<&'static dyn Plattenbauer> {
    if crate::column_build::ist_aktiv() {
        return Some(&SPALTENBAUER_LEGACY);
    }
    match modus() {
        Modus::Aus => None,
        Modus::Fest(k) => Some(bauer_fuer(k)),
        Modus::Auto => auto_kriterium(state).map(bauer_fuer),
    }
}

/// Aufrufstellen: die vier Drafting-Hook-Stellen in `self_play.rs`, ersetzt
/// `crate::column_build::vorzugszug(&game.state)` in der `.or_else(...)`-Kette.
///
/// `PREREG_opponent_disruption.md` §2: NACH dem aktiven Bauer haengt der
/// Stoerungs-Vorzug (`provocation::stoerungs_vorzug`) als `.or_else`-Zweig
/// an -- "erst die eigene Vollendung [des aktiven Bauers fuer DIESEN Zug],
/// dann die Stoerung [als Fallback, wenn der aktive Bauer hier nichts
/// vorschlaegt]" (Nutzer-Domaenenwissen, `docs/domain_knowledge.md`
/// "Spielstrategie aus Nutzer-Praxis" Punkt 4). Wirkt eigenstaendig ueber
/// den Knopf `MOSAIC_OPPONENT_DISRUPTION`, unabhaengig davon, ob ueberhaupt
/// ein Bauer (`MOSAIC_PLATTENBAU`/`MOSAIC_SPALTENBAU`) aktiv ist -- bei
/// unbesetztem Knopf liefert `stoerungs_vorzug` sofort `None` (Bestandsschutz).
pub(crate) fn drafting_vorzug(state: &GameState) -> Option<Action> {
    aktiver_bauer(state)
        .and_then(|b| b.drafting_vorzug(state))
        .or_else(|| crate::provocation::stoerungs_vorzug(state))
}

/// Aufrufstellen: dieselben vier Hook-Stellen, ersetzt
/// `crate::column_build::vorzug_dome_wahl(&game.state)`.
pub(crate) fn dome_vorzug(state: &GameState) -> Option<Action> {
    aktiver_bauer(state).and_then(|b| b.dome_vorzug(state))
}

/// Aufrufstelle: der Tiling-Hook in `self_play.rs`, ersetzt
/// `crate::column_build::vorzug_tiling_step(&game.state, pi)`.
pub(crate) fn tiling_vorzug(state: &GameState, pi: usize) -> Option<TilingStep> {
    aktiver_bauer(state).and_then(|b| b.tiling_vorzug(state, pi))
}

// ── Generische Zellen-Mechanik (Kriterien 0/1/2/5, Portierung aus column_build.rs) ──

/// Kosten EINER Zelle -- delegiert vollstaendig an `column_build::zelle_kosten`
/// (§16: dieselbe Formel, jetzt auch fuer die Special-Zellen-Slot-Nachbarn
/// gebraucht, deshalb dort `pub(crate)` und hier keine eigene Kopie mehr,
/// siehe CLAUDE.md "Bestehendes wiederverwenden"). Verifiziert aequivalent
/// per Test unten
/// (`zellen_kosten_stimmt_mit_spalten_kosten_fuer_spaltengeometrie_ueberein`).
fn zellen_kosten(player: &PlayerBoard, zellen: &[(usize, usize)], verbleibend: &[i64; 5]) -> f64 {
    zellen.iter().map(|&(r, c)| crate::column_build::zelle_kosten(player, r, c, verbleibend)).sum()
}

/// Toleranzband, identische Kalibrierung wie `column_build::SPALTEN_TOLERANZ`
/// (dieselbe Kosten-Skala, siehe dortige Begruendung).
const ZIEL_TOLERANZ: f64 = 0.5;

/// Waehlt einen Kandidaten-Index aus `kosten` -- guenstigster, oder bei
/// mehreren nahen (`ZIEL_TOLERANZ`) Kandidaten seed-gestreut, sonst der
/// kleinste Index (stabiler Tie-Break). Generalisierung von
/// `column_build::waehle_spalte` auf beliebig viele Kandidaten.
fn waehle_kandidat(kosten: &[f64], seed: Option<u64>) -> usize {
    let min_kosten = kosten.iter().cloned().fold(f64::INFINITY, f64::min);
    let kandidaten: Vec<usize> = (0..kosten.len()).filter(|&i| kosten[i] - min_kosten <= ZIEL_TOLERANZ).collect();
    if kandidaten.len() <= 1 {
        return kandidaten.first().copied().unwrap_or(0);
    }
    match seed {
        None => kandidaten[0],
        Some(s) => kandidaten[index_aus_seed(s, kandidaten.len())],
    }
}

/// §18 (Diagonalen-Baustein): wie [`ziel_zellen_generisch`], aber mit
/// `column_build::zelle_kosten_smart` statt der geteilten (§16/§17-Schalter-
/// abhaengigen) [`zellen_kosten`] -- fuer Bauern mit einer EIGENEN,
/// unabhaengig validierten Special-Zellen-Uebernahme (siehe dortige Doku).
fn ziel_zellen_generisch_smart(state: &GameState, pi: usize, kandidaten: &[Vec<(usize, usize)>]) -> Option<Vec<(usize, usize)>> {
    if kandidaten.is_empty() {
        return None;
    }
    let player = &state.players[pi];
    let verbleibend = crate::provocation::verbleibende_farben(state);
    let kosten: Vec<f64> = kandidaten
        .iter()
        .map(|z| z.iter().map(|&(r, c)| crate::column_build::zelle_kosten_smart(player, r, c, &verbleibend)).sum())
        .collect();
    let seed = PARTIE_SEED.with(|c| c.get());
    let idx = waehle_kandidat(&kosten, seed);
    Some(kandidaten[idx].clone())
}

/// Loest die aktive Zielzellen-Menge aus einer Kandidatenliste auf --
/// Generalisierung von `column_build::ziel_spalte` auf beliebige Geometrien.
fn ziel_zellen_generisch(state: &GameState, pi: usize, kandidaten: &[Vec<(usize, usize)>]) -> Option<Vec<(usize, usize)>> {
    if kandidaten.is_empty() {
        return None;
    }
    let player = &state.players[pi];
    let verbleibend = crate::provocation::verbleibende_farben(state);
    let kosten: Vec<f64> = kandidaten.iter().map(|z| zellen_kosten(player, z, &verbleibend)).collect();
    let seed = PARTIE_SEED.with(|c| c.get());
    let idx = waehle_kandidat(&kosten, seed);
    Some(kandidaten[idx].clone())
}

/// Drafting-Vorzug ueber einer beliebigen Zielzellen-Menge -- Generalisierung
/// von `provocation::vorzugszug_fuer_spalte`. Fuer eine Reihe `r`, die in
/// `zellen` mit MEHREREN Eintraegen vorkommt (Zeilen-/Ecken-Geometrie), zaehlt
/// "qualifiziert", wenn IRGENDEINE offene Zielzelle dieser Reihe die
/// angebotene Farbe fordert (eine Musterreihe fuehrt ohnehin nur eine Farbe
/// je Zug, welche der mehreren Zielzellen davon profitiert, ist fuer die
/// Zugwahl selbst gleichgueltig).
pub(crate) fn vorzugszug_fuer_zellen(state: &GameState, zellen: &[(usize, usize)]) -> Option<Action> {
    if state.phase != crate::state::Phase::Drafting || state.round_number > 4 {
        return None;
    }
    let player = &state.players[state.current_player];
    let verbleibend = crate::provocation::verbleibende_farben(state);
    let moves = crate::validation::generate_valid_moves(state);
    let mut best: Option<(i64, i32, i32, crate::moves::Move)> = None;
    for m in moves {
        let r = m.place.row_index;
        if !(0..=5).contains(&r) {
            continue;
        }
        let r = r as usize;
        let qualifiziert = zellen.iter().any(|&(zr, zc)| {
            if zr != r {
                return false;
            }
            let Some(sp) = player.dome_grid.get_space(zr, zc) else { return false };
            if sp.is_filled() {
                return false;
            }
            match sp.space_type {
                SpaceType::Wild => true,
                SpaceType::Normal => sp.required_color == Some(m.take.color),
                SpaceType::Special => false,
            }
        });
        if !qualifiziert {
            continue;
        }
        let zeile = &player.pattern_lines[r];
        let fuellung = zeile.tiles.len() as i32;
        let knappheit = crate::provocation::farben_index(m.take.color).map(|i| verbleibend[i]).unwrap_or(i64::MAX);
        let kandidat = (knappheit, -fuellung, r as i32, m);
        let besser = best.as_ref().map_or(true, |(k, f, rr, _)| (kandidat.0, kandidat.1, kandidat.2) < (*k, *f, *rr));
        if besser {
            best = Some(kandidat);
        }
    }
    best.map(|(_, _, _, m)| Action::Stone(m))
}

/// Score einer (Kachel, Slot, Rotation)-Kombination gegen eine beliebige
/// Zielzellen-Menge -- Generalisierung von `column_build::slot_score`: statt
/// nur die zwei Zellen EINER Spalte je Slot zu pruefen, werden alle vier
/// Platzierungspositionen des Slots gegen die Zielzellen-Mitgliedschaft
/// geprueft. Fuer eine Spalten-Zielzellenliste ist das rechnerisch identisch
/// zu `slot_score` (jeder Slot hat pro Spalten-Offset genau zwei Positionen,
/// exakt die dort gelesenen `idx[cc]`/`idx[cc+2]`).
fn slot_score_generic(
    player: &PlayerBoard,
    tile: &crate::dome::DomeTile,
    slot_row: usize,
    slot_col: usize,
    rotation: u32,
    zellen: &[(usize, usize)],
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
        summe += crate::column_build::zellen_wert(player, row, &tile.spaces[idx[i]]);
    }
    if beruehrt {
        Some(summe)
    } else {
        None
    }
}

/// Kuppelplatten-Wahl-Vorzug ueber einer beliebigen Zielzellen-Menge --
/// Generalisierung von `column_build::vorzug_dome_wahl`. Anders als dort wird
/// NICHT nach `slot_col` vorgefiltert (eine Zeilen-/Ecken-Zielmenge kann
/// mehrere Slot-Spalten beruehren) -- [`slot_score_generic`]s `beruehrt`-Flag
/// uebernimmt den gleichen Ausschluss implizit (Score 0, dann durch den
/// `>0.0`-Filter unten verworfen).
pub(crate) fn dome_vorzug_fuer_zellen(state: &GameState, zellen: &[(usize, usize)]) -> Option<Action> {
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
                    if let Some(score) = slot_score_generic(player, tile, *slot_row, *slot_col, rot, zellen) {
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
                if let Some(score) = slot_score_generic(player, tile, sr, sc, rot, zellen) {
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
/// Generalisierung von `column_build::vorzug_tiling_step_fuer_spalte`: zaehlt
/// gefuellte Zielzellen statt gefuellte Zellen EINER Spalte.
pub(crate) fn tiling_vorzug_fuer_zellen(state: &GameState, pi: usize, zellen: &[(usize, usize)]) -> Option<TilingStep> {
    if !(1..=4).contains(&state.round_number) {
        return None;
    }
    let ziel_zellen_count = |s: &GameState| -> usize {
        zellen
            .iter()
            .filter(|&&(r, c)| s.players[pi].dome_grid.get_space(r, c).map_or(false, |sp| sp.is_filled()))
            .count()
    };
    let vorher = ziel_zellen_count(state);
    let cands = crate::tiling_solver::top_k_tilings(state, pi, crate::tiling_solver::MAX_TILING_LEAVES);
    let best = cands
        .into_iter()
        .map(|c| {
            let z = ziel_zellen_count(&c.final_state);
            (z, c.points, c.first_step)
        })
        .max_by(|a, b| (a.0, a.1).cmp(&(b.0, b.1)))?;
    if best.0 > vorher {
        Some(best.2)
    } else {
        None
    }
}

// ── Geometrie-Bausteine ──────────────────────────────────────────────────────

fn zellen_zeile(r: usize) -> Vec<(usize, usize)> {
    (0..6).map(|c| (r, c)).collect()
}

fn zellen_spalte(c: usize) -> Vec<(usize, usize)> {
    (0..6).map(|r| (r, c)).collect()
}

fn zellen_diagonale_haupt() -> Vec<(usize, usize)> {
    (0..6).map(|i| (i, i)).collect()
}

fn zellen_diagonale_neben() -> Vec<(usize, usize)> {
    (0..6).map(|i| (i, 5 - i)).collect()
}

/// Die vier Eckslots aus `scoring::score_corner_tiles`: `(0,0)`/`(0,2)` (obere
/// Ecken, 3 Pkt) und `(2,0)`/`(2,2)` (untere Ecken, 8 Pkt) -- Slot-Koordinaten
/// im 3x3-Dome-Raster, je in die 4 Rasterzellen aufgeloest. Seit §20 nicht
/// mehr von `Eckenbauer` selbst genutzt (Spaltenpaar-Ziel ersetzt die
/// isolierten Eck-Slots, siehe dortige Doku) -- bleibt fuer den eigenen
/// Geometrietest stehen.
#[allow(dead_code)]
fn zellen_ecke(idx: usize) -> Vec<(usize, usize)> {
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
        let kand: Vec<_> = (0..6).map(zellen_zeile).collect();
        ziel_zellen_generisch(state, pi, &kand)
    }
}
impl Plattenbauer for Zeilenbauer {
    fn drafting_vorzug(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(state, state.current_player)?;
        vorzugszug_fuer_zellen(state, &z)
    }
    fn dome_vorzug(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(state, state.current_player)?;
        dome_vorzug_fuer_zellen(state, &z)
    }
    fn tiling_vorzug(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        let z = self.zellen(state, pi)?;
        tiling_vorzug_fuer_zellen(state, pi, &z)
    }
}

// ── Kriterium 1 (generisch, MOSAIC_PLATTENBAU=1 ohne den Altknopf): Spalten ──

struct SpaltenbauerGenerisch;
impl SpaltenbauerGenerisch {
    fn zellen(&self, state: &GameState, pi: usize) -> Option<Vec<(usize, usize)>> {
        let kand: Vec<_> = (0..6).map(zellen_spalte).collect();
        ziel_zellen_generisch(state, pi, &kand)
    }
}
impl Plattenbauer for SpaltenbauerGenerisch {
    fn drafting_vorzug(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(state, state.current_player)?;
        vorzugszug_fuer_zellen(state, &z)
    }
    fn dome_vorzug(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(state, state.current_player)?;
        dome_vorzug_fuer_zellen(state, &z)
    }
    fn tiling_vorzug(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        let z = self.zellen(state, pi)?;
        tiling_vorzug_fuer_zellen(state, pi, &z)
    }
}

// ── Kriterium 2: Diagonalen (10 Pkt je volle Diagonale, max 2x) ──────────────

struct Diagonalenbauer;
impl Diagonalenbauer {
    /// §18: nutzt `ziel_zellen_generisch_smart` (immer die echten Special-
    /// Nachbar-Kosten, siehe dortige Doku) statt der geteilten, §16/§17-
    /// Schalter-abhaengigen `ziel_zellen_generisch` -- die Diagonalen-
    /// Special-Erweiterung ist eine EIGENE, in §18 validierte Entscheidung
    /// (+2,61 Plattenpunkte, t=2,79, p=0,011, kein Sieg-Verlust), unabhaengig
    /// vom k1-Legacy-Befund (§17: final NEIN).
    fn zellen(&self, state: &GameState, pi: usize) -> Option<Vec<(usize, usize)>> {
        let kand = vec![zellen_diagonale_haupt(), zellen_diagonale_neben()];
        ziel_zellen_generisch_smart(state, pi, &kand)
    }
}
impl Plattenbauer for Diagonalenbauer {
    fn drafting_vorzug(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(state, state.current_player)?;
        vorzugszug_fuer_zellen(state, &z).or_else(|| {
            // §18 (Diagonalen-Baustein, Nutzer-Taktik domain_knowledge.md
            // §5): eine offene Special-Zelle in der Diagonalen-Slot-Reihe 3
            // braucht ihre Slot-Nachbarn, die oft NICHT selbst Diagonal-
            // zellen sind. UNBEDINGT (siehe `special_nachbar_zellen_immer`-
            // Doku) -- §18 hat diese Erweiterung EIGENSTAeNDIG validiert.
            let player = &state.players[state.current_player];
            let nz = crate::column_build::special_nachbar_zellen_immer(player, &z);
            if nz.is_empty() { None } else { vorzugszug_fuer_zellen(state, &nz) }
        })
    }
    fn dome_vorzug(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(state, state.current_player)?;
        dome_vorzug_fuer_zellen(state, &z)
    }
    fn tiling_vorzug(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        let z = self.zellen(state, pi)?;
        tiling_vorzug_fuer_zellen(state, pi, &z).or_else(|| {
            let player = &state.players[pi];
            let nz = crate::column_build::special_nachbar_zellen_immer(player, &z);
            if nz.is_empty() { None } else { tiling_vorzug_fuer_zellen(state, pi, &nz) }
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

fn zellen_spaltenpaar(c0: usize) -> Vec<(usize, usize)> {
    let mut v = Vec::with_capacity(12);
    for r in 0..6usize {
        v.push((r, c0));
        v.push((r, c0 + 1));
    }
    v
}

fn zellen_untere_ecke_paar(c0: usize) -> Vec<(usize, usize)> {
    let mut v = Vec::with_capacity(4);
    for r in 4..6usize {
        v.push((r, c0));
        v.push((r, c0 + 1));
    }
    v
}

fn zellen_obere_ecke_paar(c0: usize) -> Vec<(usize, usize)> {
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
    /// `ziel_zellen_generisch_smart` (§18) fuer die echte Special-Nachbar-
    /// Kostenrechnung, dieselbe Seed-Streuung/Zielwechsel-Logik wie alle
    /// anderen generischen Bauern (§14-Lehre: keine sture Bindung). Liefert
    /// die KLEINERE der beiden Spaltennummern des gewaehlten Paars.
    fn spalte0(&self, state: &GameState, pi: usize) -> Option<usize> {
        let kand = vec![zellen_spaltenpaar(0), zellen_spaltenpaar(4)];
        let z = ziel_zellen_generisch_smart(state, pi, &kand)?;
        z.iter().map(|&(_, c)| c).min()
    }
}
impl Plattenbauer for Eckenbauer {
    fn drafting_vorzug(&self, state: &GameState) -> Option<Action> {
        let c0 = self.spalte0(state, state.current_player)?;
        vorzugszug_fuer_zellen(state, &zellen_untere_ecke_paar(c0))
            .or_else(|| vorzugszug_fuer_zellen(state, &zellen_obere_ecke_paar(c0)))
            .or_else(|| vorzugszug_fuer_zellen(state, &zellen_spaltenpaar(c0)))
    }
    fn dome_vorzug(&self, state: &GameState) -> Option<Action> {
        let c0 = self.spalte0(state, state.current_player)?;
        dome_vorzug_fuer_zellen(state, &zellen_untere_ecke_paar(c0))
            .or_else(|| dome_vorzug_fuer_zellen(state, &zellen_obere_ecke_paar(c0)))
            .or_else(|| dome_vorzug_fuer_zellen(state, &zellen_spaltenpaar(c0)))
    }
    fn tiling_vorzug(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        let c0 = self.spalte0(state, pi)?;
        tiling_vorzug_fuer_zellen(state, pi, &zellen_untere_ecke_paar(c0))
            .or_else(|| tiling_vorzug_fuer_zellen(state, pi, &zellen_obere_ecke_paar(c0)))
            .or_else(|| tiling_vorzug_fuer_zellen(state, pi, &zellen_spaltenpaar(c0)))
    }
}

// ── Kriterium 3: Mehrfarbige Felder (Jokerfelder, 2 Pkt je Feld wenn ALLE voll) ──
//
// Kein Kandidatenvergleich noetig -- es gibt nur EINE sinnvolle Zielmenge:
// ALLE noch offenen Wild-Zellen des Bretts (jede Farbe qualifiziert dort
// ohnehin, siehe `vorzugszug_fuer_zellen`s `SpaceType::Wild => true`).

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
    fn drafting_vorzug(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(&state.players[state.current_player]);
        vorzugszug_fuer_zellen(state, &z)
    }
    fn dome_vorzug(&self, _state: &GameState) -> Option<Action> {
        // Bewusst kein Vorzug: mehr Wild-Zellen sind IMMER neutral-bis-gut
        // (jede Farbe qualifiziert), eine Rotationsentscheidung aendert die
        // Wild-ANZAHL einer Kachel nicht (Rotation permutiert nur Positionen,
        // nicht Typen) -- es gibt hier keine Entscheidung, die dieser
        // Vorzug besser treffen koennte als das Netz selbst.
        None
    }
    fn tiling_vorzug(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        let z = self.zellen(&state.players[pi]);
        tiling_vorzug_fuer_zellen(state, pi, &z)
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
    fn drafting_vorzug(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(&state.players[state.current_player]);
        vorzugszug_fuer_zellen(state, &z)
    }
    fn dome_vorzug(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(&state.players[state.current_player]);
        dome_vorzug_fuer_zellen(state, &z)
    }
    fn tiling_vorzug(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        let z = self.zellen(&state.players[pi]);
        tiling_vorzug_fuer_zellen(state, pi, &z)
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
    fn drafting_vorzug(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(&state.players[state.current_player]);
        vorzugszug_fuer_zellen(state, &z)
    }
    fn dome_vorzug(&self, state: &GameState) -> Option<Action> {
        // §19: `kuppeldraft_vorzug_k6` (Joker-Kuppeln auf untere Slots,
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
        dome_vorzug_fuer_zellen(state, &z)
    }
    fn tiling_vorzug(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        let z = self.zellen(&state.players[pi]);
        tiling_vorzug_fuer_zellen(state, pi, &z)
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
// Absichtlich NICHT verkettet (siehe `Spezialbauer::dome_vorzug`-Kommentar):
// gemessen und mit falschem Vorzeichen abgelehnt (§19).
#[allow(dead_code)]
fn kuppeldraft_vorzug_k6(state: &GameState) -> Option<Action> {
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
        let kand: Vec<_> = (0..6).map(zellen_zeile).collect();
        ziel_zellen_generisch(state, pi, &kand)
    }

    /// Farben, die in der Zielreihe (aus `zellen`, alle mit gleichem `row`)
    /// schon platziert sind -- gelesen aus `placed_color` der Slot-Zellen.
    fn vorhandene_farben(&self, player: &PlayerBoard, row: usize) -> std::collections::HashSet<crate::tile::TileColor> {
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
    fn drafting_vorzug(&self, state: &GameState) -> Option<Action> {
        let z = self.zellen(state, state.current_player)?;
        vorzugszug_fuer_zellen(state, &z)
    }
    fn dome_vorzug(&self, state: &GameState) -> Option<Action> {
        let zellen = self.zellen(state, state.current_player)?;
        let row = zellen.first()?.0;
        let player = &state.players[state.current_player];
        let vorhanden = self.vorhandene_farben(player, row);

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
    fn tiling_vorzug(&self, state: &GameState, pi: usize) -> Option<TilingStep> {
        let z = self.zellen(state, pi)?;
        tiling_vorzug_fuer_zellen(state, pi, &z)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dome::{DomeSpace, DomeTile};
    use crate::tile::TileColor::*;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

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
        crate::column_build::set_aktiv_override_for_test(Some(false));
        set_modus_override_for_test(Some(Modus::Aus));
        let game = drafting_game(1);
        assert_eq!(drafting_vorzug(&game.state), None);
        assert_eq!(dome_vorzug(&game.state), None);
        assert!(tiling_vorzug(&game.state, 0).is_none());
        set_modus_override_for_test(None);
        crate::column_build::set_aktiv_override_for_test(None);
    }

    /// Kernabnahme Stufe 1: bei aktivem `MOSAIC_SPALTENBAU` muss die
    /// Abstraktion GENAU das liefern, was `column_build.rs` direkt liefert --
    /// reine Delegation, keine Nachbildung. Ueber mehrere Seeds/Zustaende,
    /// damit der Test nicht nur eine einzelne Zufallskonstellation trifft.
    #[test]
    fn mosaic_spaltenbau_an_ist_verhaltensidentisch_zur_direkten_ansteuerung() {
        crate::column_build::set_aktiv_override_for_test(Some(true));
        for seed in 0u64..30 {
            // Runde 4: `column_build::ziel_spalte` merkt sich jetzt die zuletzt
            // gewaehlte Spalte je Partie (Vollendbarkeits-Buchhaltung, siehe
            // dortige Doku) -- ohne Reset hier wuerde die Spalte des VORIGEN
            // Seeds in dieses (voellig andere) Brett hineinlecken, exakt das
            // Leck, vor dem `set_partie_seed`s Doku schon immer warnt. Echte
            // Partien (self_play.rs) rufen `set_partie_seed` ohnehin schon
            // pro Partie auf -- dieser Test muss es fuer sein eigenes
            // Pro-Seed-"Partie"-Modell jetzt auch tun.
            crate::column_build::set_partie_seed(None);
            let mut game = drafting_game(seed);
            let pi = game.state.current_player;
            let tile = normal_tile(100 + seed as usize, [Rot, Blau, Gelb, Schwarz]);
            let _ = game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0);

            assert_eq!(
                drafting_vorzug(&game.state),
                crate::column_build::vorzugszug(&game.state),
                "Seed {seed}: drafting_vorzug muss column_build::vorzugszug entsprechen"
            );
            assert_eq!(
                dome_vorzug(&game.state),
                crate::column_build::vorzug_dome_wahl(&game.state),
                "Seed {seed}: dome_vorzug muss column_build::vorzug_dome_wahl entsprechen"
            );
            assert_eq!(
                tiling_vorzug(&game.state, pi),
                crate::column_build::vorzug_tiling_step(&game.state, pi),
                "Seed {seed}: tiling_vorzug muss column_build::vorzug_tiling_step entsprechen"
            );
        }
        crate::column_build::set_aktiv_override_for_test(None);
    }

    /// `zellen_kosten` ueber einer Spalten-Zellenliste muss exakt
    /// `column_build::spalten_kosten` fuer dieselbe Spalte liefern -- das ist
    /// der rechnerische Beleg, dass die Generalisierung fuer den Spalten-Fall
    /// nichts verschiebt (siehe Moduldoku).
    #[test]
    fn zellen_kosten_stimmt_mit_spalten_kosten_fuer_spaltengeometrie_ueberein() {
        let mut game = drafting_game(9);
        let pi = game.state.current_player;
        let tile = normal_tile(200, [Rot, Blau, Gelb, Schwarz]);
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("frei");
        let verbleibend = crate::provocation::verbleibende_farben(&game.state);
        for spalte in 0..6usize {
            let alt = crate::column_build::spalten_kosten(&game.state.players[pi], spalte, &verbleibend);
            let neu = zellen_kosten(&game.state.players[pi], &zellen_spalte(spalte), &verbleibend);
            assert!((alt - neu).abs() < 1e-9, "Spalte {spalte}: alt={alt} neu={neu}");
        }
    }

    #[test]
    fn mosaic_plattenbau_1_ohne_altknopf_liefert_generischen_spaltenpfad() {
        crate::column_build::set_aktiv_override_for_test(Some(false));
        set_modus_override_for_test(Some(Modus::Fest(1)));
        let game = drafting_game(11);
        // Der generische Pfad muss ETWAS liefern koennen (keine strikte
        // Gleichheit zum Legacy-Pfad gefordert -- das ist der zweite, bewusst
        // getrennte Codepfad, siehe Moduldoku).
        let _ = drafting_vorzug(&game.state);
        assert_eq!(aktives_kriterium(&game.state), Some(1));
        set_modus_override_for_test(None);
        crate::column_build::set_aktiv_override_for_test(None);
    }

    #[test]
    fn mosaic_plattenbau_0_waehlt_zeilenbauer() {
        set_modus_override_for_test(Some(Modus::Fest(0)));
        let game = drafting_game(12);
        assert_eq!(aktives_kriterium(&game.state), Some(0));
        set_modus_override_for_test(None);
    }

    #[test]
    fn auto_modus_streut_ueber_scoring_tile_ids_der_partie() {
        set_modus_override_for_test(Some(Modus::Auto));
        let mut game = drafting_game(13);
        game.state.scoring_tile_ids = vec![2, 4, 6];
        set_partie_seed(None);
        assert_eq!(aktives_kriterium(&game.state), Some(2), "ohne Seed: erstes aktives Kriterium");
        let mut gesehen = std::collections::HashSet::new();
        for seed in 0u64..40 {
            set_partie_seed(Some(seed));
            let k = aktives_kriterium(&game.state).expect("Auto mit gesetzten IDs muss liefern");
            assert!(game.state.scoring_tile_ids.contains(&k), "Kriterium {k} muss unter den 3 aktiven Platten sein");
            gesehen.insert(k);
        }
        set_partie_seed(None);
        assert!(gesehen.len() >= 2, "40 Seeds sollten mehr als 1 der 3 IDs treffen: {gesehen:?}");
        set_modus_override_for_test(None);
    }

    #[test]
    fn auto_modus_ohne_scoring_tile_ids_liefert_none() {
        set_modus_override_for_test(Some(Modus::Auto));
        let mut game = drafting_game(14);
        game.state.scoring_tile_ids = Vec::new();
        assert_eq!(aktives_kriterium(&game.state), None);
        set_modus_override_for_test(None);
    }

    /// Kriterium 3 (Mehrfarbig): eine Wild-Zelle in Zeile 0 muss als Ziel
    /// erkannt werden -- jede angebotene Farbe qualifiziert.
    #[test]
    fn mehrfarbigbauer_erkennt_offene_wild_zelle_als_ziel() {
        set_modus_override_for_test(Some(Modus::Fest(3)));
        let mut game = drafting_game(15);
        let pi = game.state.current_player;
        let tile = DomeTile::new(
            300,
            vec![DomeSpace::wild(), DomeSpace::normal(Blau), DomeSpace::normal(Gelb), DomeSpace::normal(Schwarz)],
            0,
        );
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("frei");
        game.state.factories[0].sun_tiles = vec![Rot, Rot];
        let ergebnis = drafting_vorzug(&game.state);
        assert!(ergebnis.is_some(), "Wild-Zelle muss als Ziel gelten, egal welche Farbe angeboten wird");
        set_modus_override_for_test(None);
    }

    /// Kriterium 4 (Rand): eine offene Randzelle (Zeile 0) muss als Ziel
    /// erkannt werden.
    #[test]
    fn randbauer_erkennt_offene_randzelle_als_ziel() {
        set_modus_override_for_test(Some(Modus::Fest(4)));
        let mut game = drafting_game(16);
        let pi = game.state.current_player;
        let tile = normal_tile(400, [Rot, Blau, Gelb, Schwarz]);
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("frei");
        game.state.factories[0].sun_tiles = vec![Rot, Rot];
        let ergebnis = drafting_vorzug(&game.state);
        match ergebnis {
            Some(Action::Stone(m)) => assert_eq!(m.place.row_index, 0),
            other => panic!("erwartet einen Stein-Zug in Zeile 0 (Rand), bekam {other:?}"),
        }
        set_modus_override_for_test(None);
    }

    /// Kriterium 6 (Spezial): eine Special-Zelle mit offenen Nachbarn muss
    /// deren Nachbarn als Ziel liefern (nicht die Special-Zelle selbst).
    #[test]
    fn spezialbauer_zielt_auf_nachbarn_nicht_auf_die_special_zelle_selbst() {
        set_modus_override_for_test(Some(Modus::Fest(6)));
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
        set_modus_override_for_test(None);
    }

    /// Kriterium 5 (Ecken): Zielzellen fuer Slot-Index 0 muessen exakt die 4
    /// Rasterzellen von Slot (0,0) sein.
    #[test]
    fn zellen_ecke_liefert_die_vier_zellen_des_slots() {
        let mut z = zellen_ecke(0);
        z.sort();
        assert_eq!(z, vec![(0, 0), (0, 1), (1, 0), (1, 1)]);
        let mut z3 = zellen_ecke(3);
        z3.sort();
        assert_eq!(z3, vec![(4, 4), (4, 5), (5, 4), (5, 5)]);
    }

    /// Kriterium 7 (Farbenreich): die Kuppelplatten-Wahl muss eine Kachel mit
    /// einer NOCH NICHT vorhandenen Farbe in der Zielreihe einer bevorzugen,
    /// die nur Farben wiederholt, die schon in der Reihe stehen.
    #[test]
    fn farbenreichbauer_bevorzugt_neue_farbe_in_der_zielreihe() {
        set_modus_override_for_test(Some(Modus::Fest(7)));
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
        let a = Farbenreichbauer.dome_vorzug(&game.state);
        match a {
            Some(Action::ChooseDomeSlot(m)) => {
                assert_eq!(m.dome_tile_id, 703, "die Kachel mit einer NEUEN Farbe fuer Zeile 0 muss gewinnen");
                assert_eq!(m.slot_row, 0);
                assert_eq!(m.slot_col, 0);
            }
            other => panic!("erwartet ChooseDomeSlot, bekam {other:?}"),
        }
        set_modus_override_for_test(None);
    }
}

// ── v2-Zielbild: 1-2 Spalten + 1-2 Reihen, Nachbarn verbinden ────────────────

/// Zielzellen fuer `mcts::HeuristikVariante::V2` (Nutzer-Zielbild 2026-08-24:
/// "1-2 vollstaendige Spalten, 1-2 vollstaendige Reihen, und dann alles so gut
/// es geht mit Nachbarn verbinden. Eine Diagonale ist dann in der idealen Welt
/// das Beiwerk").
///
/// Waehlt die GUENSTIGSTE Spalte und die GUENSTIGSTE Zeile mit derselben
/// Kostenformel wie die uebrigen Bauer (`ziel_zellen_generisch`) und liefert
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

pub(crate) fn v2_ziel_zellen(state: &GameState, pi: usize) -> Option<Vec<(usize, usize)>> {
    let player = &state.players[pi];
    let spalten: Vec<_> = (0..6).map(zellen_spalte).collect();
    let s = ziel_zellen_generisch(state, pi, &spalten)?;

    // Zeilen NUR aus den obersten ZWEI Rasterzeilen und nur, wo ein
    // Spezialfeld sie ueberhaupt vollendbar macht (s. Doku unten).
    let zeilen: Vec<_> = (0..ZEILEN_ZIEL_MAX)
        .filter(|&r| zeile_ist_vollendbar(player, r))
        .map(zellen_zeile)
        .collect();
    let mut alle = s;
    if let Some(z) = ziel_zellen_generisch(state, pi, &zeilen) {
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
fn zeile_ist_vollendbar(player: &PlayerBoard, r: usize) -> bool {
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


/// Drafting-Vorzug fuer v2 -- UNGEGATET, also ohne `MOSAIC_SPALTENBAU` und
/// ohne `MOSAIC_PLATTENBAU`.
///
/// Beide Bestandsknoepfe sind prozessweit. Fuer eine Partie v1 GEGEN v2 sind
/// sie damit unbrauchbar: sie gaelten fuer beide Seiten oder fuer keine. Die
/// Variante ist der einzige Weg, der die Seiten trennt.
pub(crate) fn v2_drafting_vorzug(state: &GameState) -> Option<Action> {
    let z = v2_ziel_zellen(state, state.current_player)?;
    // Erst der Stein-Zug, dann die KUPPELPLATTEN-Wahl. Die zweite war bis
    // 2026-08-24 nicht verdrahtet, und sie ist der Grund, warum die
    // gestreute Start-Ecke die vollen Zeilen von 0,400 auf 0,263 gedrueckt
    // hat: startet die Kuppel unten, liegt in den oberen Rasterzeilen frueh
    // keine Platte, und genau die sind das Zeilenziel. Nutzer-Vorgabe
    // 2026-08-24: "dann muss man halt Kuppel ziehen fuer die oberen
    // Rasterzeilen".
    //
    // `dome_vorzug_fuer_zellen` waehlt Platte, Slot und Rotation so, dass die
    // Zielzellen bedienbar werden -- laut `column_build.rs`-Moduldoku die
    // Stelle, die "bisher nie gesteuert" wurde, obwohl sie `required_color`
    // der Zellen bestimmt.
    vorzugszug_fuer_zellen(state, &z).or_else(|| dome_vorzug_fuer_zellen(state, &z))
}

/// Tiling-Routing fuer v2 -- ungegatet, siehe [`v2_drafting_vorzug`].
///
/// Das ist die Haelfte, die der bisherige v2-Term GAR NICHT beruehrt hat und
/// die laut `PREREG_provocation.md` der eigentliche Engpass ist ("der Engpass
/// ist die PLATZIERBARKEIT, nicht die Plattenbewertung"): ohne sie waehlt
/// `best_first_step_inner` nach reinen Sofortpunkten und wirft jede
/// Draft-seitige Absicht wieder weg.
pub(crate) fn v2_tiling_vorzug(state: &GameState, pi: usize) -> Option<TilingStep> {
    let z = v2_ziel_zellen(state, pi)?;
    tiling_vorzug_fuer_zellen(state, pi, &z)
}
