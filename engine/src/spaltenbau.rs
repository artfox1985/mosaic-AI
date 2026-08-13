//! Spaltenbau-Spieler (Diagnose-/Korpus-Knopf `MOSAIC_SPALTENBAU`) --
//! Entscheidungsschicht UEBER dem Netzspieler, die gezielt EINE
//! Wertungsplatten-Spalte je Partie schliessen soll (Nutzer-Auftrag
//! 2026-08-13, siehe `evaluations/PREREG_provokation.md` §9 fuer die
//! Vorgeschichte: vier Mechanismen -- Injektion, Beschneidung, Vorzug-
//! Drafting, Vorzug-Drafting+Tiling -- enden alle bei 0,30 Spalten/Partie,
//! die 5/6-Mauer haelt in 9-13 von 20 Partien).
//!
//! Baut auf der EINZIGEN Linie, die dabei das Spiel intakt liess --
//! `provokation.rs`s "Vorzugszug: Praeferenz statt Verbot" -- und erweitert
//! sie um zwei Stellen, die dort noch NICHTS steuert:
//!
//!  1. [`vorzug_dome_wahl`]: die Kuppelplatten-Wahl (welche Platte, welcher
//!     Slot, welche Rotation) bestimmt `required_color` der Zellen -- bisher
//!     nie gesteuert (§9 selbst listet nur Drafting- und Tiling-Mechanismen).
//!  2. [`ziel_spalte`]: die Ziel-Spalte wird JE ENTSCHEID frisch aus dem
//!     aktuellen Brettzustand bestimmt (vorhandene Platten, Wild-/Special-
//!     Zellen, schon gefuellte Zellen, blockierte Musterreihen) statt fest
//!     0..5 zu sein -- ein Wechsel der Ziel-Spalte "geschieht" dadurch von
//!     selbst, es gibt keinen gespeicherten Zustand, der veralten koennte.
//!
//! [`vorzugszug`] (Stein-Zuege) ist eine duenne Huelle um
//! `provokation::vorzugszug_fuer_spalte` mit der dynamischen Spalte statt
//! des Env-Knopfs `MOSAIC_VORZUG_SPALTE` -- IDENTISCHE Praeferenzlogik,
//! wiederverwendet statt dupliziert (CLAUDE.md-Vorgabe). Ebenso
//! [`vorzug_tiling_step`] fuer `tiling_solver::vorzug_tiling_step_fuer_spalte`.
//!
//! Bewusst NICHT gebaut: eine Beschneidung der Aktionsmenge ("Musterreihe
//! fuer die Ziel-Zelle freihalten"). §7/§9 haben genau das gemessen und
//! game-zerstoerend befunden (Endstand 6-15 statt 47,80, Strafleiste bis 23)
//! -- ausserdem wuerde eine echte Umsetzung `net_mcts.rs`s Suchbaumaufbau
//! aendern muessen (die Suche kennt keine externe Kandidatenliste), was der
//! Auftrag explizit ausschliesst ("Anker mcts.rs bleibt unberuehrt"). Siehe
//! Bericht fuer die Begruendung und die ersatzweise gelieferte
//! Blocker-Klassifikation MIT Farbabgleich.
//!
//! DEFAULT AUS -> jede Funktion hier ist ein No-Op; alle Aufrufstellen
//! bleiben `.or_else(...)`-verkettet, byte-identisch zum Bestand ohne den
//! Knopf (gleiches Muster wie `provokation.rs`/`MOSAIC_VORZUG_SPALTE`).

use crate::board::PlayerBoard;
use crate::dome::{rotation_indices, DomeSpace, DomeTile, SpaceType};
use crate::moves::{Action, PendingDomeChoice, PlaceDomeTileMove};
use crate::state::GameState;
use crate::tile::TileColor;
use crate::tiling_solver::TilingStep;

/// Liest `MOSAIC_SPALTENBAU` einmalig (Prozess-Cache, gleiches Muster wie
/// `provokation::modus_env`). Jeder nicht-leere Wert ausser `"0"` schaltet
/// den Spaltenbauer ein.
fn aktiv_env() -> bool {
    static CELL: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| match std::env::var("MOSAIC_SPALTENBAU") {
        Err(_) => false,
        Ok(raw) => {
            let v = raw.trim();
            !v.is_empty() && v != "0"
        }
    })
}

// Test-Override -- gleiches Muster wie `provokation::MODUS_OVERRIDE`: ein
// `OnceLock` waere sonst prozessweit fuer ALLE parallelen `cargo test`-
// Threads fixiert, sobald der erste Test ihn liest.
#[cfg(test)]
thread_local! {
    static AKTIV_OVERRIDE: std::cell::Cell<Option<bool>> = const { std::cell::Cell::new(None) };
}

#[cfg(test)]
pub(crate) fn set_aktiv_override_for_test(v: Option<bool>) {
    AKTIV_OVERRIDE.with(|c| c.set(v));
}

pub(crate) fn ist_aktiv() -> bool {
    #[cfg(test)]
    {
        if let Some(v) = AKTIV_OVERRIDE.with(|c| c.get()) {
            return v;
        }
    }
    aktiv_env()
}

// ── Hauptaufgabe 2: dynamische Zielspaltenwahl ──────────────────────────────

/// "Leichtigkeit" der Spalte `spalte` fuer `player`, als additive Kosten
/// (kleiner = leichter). Je Zeile 0..=5 der Spalte:
///  - kein Slot dort -- neutral (unbekannt, weder Fortschritt noch Blockade).
///  - Zelle schon gefuellt -- Fortschritt, kostet nichts mehr.
///  - Wild -- keine Farbbindung, billig.
///  - Special -- TEUER, GEMESSENE Umbepreisung (Task 7b, Nutzer-Auftrag
///    2026-08-13, Abnahmelauf `fd2d15e`): eine Special-Zelle fuellt sich erst
///    automatisch, wenn ihre 3 Slot-Nachbarzellen komplett sind
///    (`round_end::check_special_trigger`) -- 10 von 12 Blockern der letzten
///    Runde 2-Messung waren genau solche Zellen. Die Kosten SKALIEREN mit der
///    Zahl der noch offenen Nachbarn (0 offen -> 0,3, so billig wie eine
///    passende Normal-Zelle; 3 offen -> 2,7, teurer als eine falsch gebundene
///    Normal-Zelle) statt eines fixen Werts -- das bildet "braucht 3
///    Slot-Nachbarzellen" direkt ab, nicht nur "ist irgendwie schwieriger".
///  - Normal, ungefuellt: billig, wenn die Musterreihe leer ist (offen) oder
///    schon GENAU die geforderte Farbe fuehrt; teuer, wenn sie an eine ANDERE
///    Farbe gebunden ist (diese Runde fuer diese Zeile blockiert -- Nutzer-
///    Vorgabe "schon gefuellte Zellen"/"Farbforderungen" einbeziehen). Eine
///    OFFENE Zeile bekommt zusaetzlich den Versorgungs-Aufschlag
///    [`engpass_aufschlag`] (Runde 3, Task 2, Nutzer-Auftrag 2026-08-13):
///    je knapper die geforderte Farbe oeffentlich noch verfuegbar ist, desto
///    teurer -- "eine Zelle, deren Farbe fast aufgebraucht ist, ist teuer,
///    auch wenn die Reihe frei ist" (wortgleiche Vorgabe). Der falsch-
///    gebundene Fall (`c != x`) bekommt KEINEN Aufschlag -- die Zeile ist
///    ohnehin schon blockiert, unabhaengig von der Versorgungslage von `x`.
///
/// Additiv aus dem Brett UND (seit Runde 3) der oeffentlichen Versorgungslage
/// ablesbar (`dome_grid`/`pattern_lines` + `verbleibend`, vom Aufrufer EINMAL
/// je Entscheid vorberechnet, siehe [`crate::provokation::verbleibende_farben`])
/// -- keine Suche, kein Blick in Beutel/Turm selbst -- daher weiterhin O(6) je
/// Spalte (die Special-Nachbarpruefung ist selbst O(1), feste 2x2-Slot-Geometrie).
pub(crate) fn spalten_kosten(player: &PlayerBoard, spalte: usize, verbleibend: &[i64; 5]) -> f64 {
    let mut kosten = 0.0;
    for r in 0..6usize {
        kosten += match player.dome_grid.get_space(r, spalte) {
            None => 1.0,
            Some(sp) if sp.is_filled() => 0.0,
            Some(sp) => match sp.space_type {
                SpaceType::Wild => 0.2,
                SpaceType::Special => special_kosten(player, r, spalte),
                SpaceType::Normal => {
                    let need = sp.required_color;
                    match (player.pattern_lines[r].color, need) {
                        (None, Some(x)) => 1.0 + engpass_aufschlag(verbleibend, x),
                        (None, None) => 1.0, // Normal hat laut dome.rs immer required_color=Some(..); defensiv.
                        (Some(c), Some(x)) if c == x => 0.3,
                        _ => 2.0,
                    }
                }
            },
        };
    }
    kosten
}

/// Versorgungs-Aufschlag fuer eine noch OFFENE Musterreihe, die `farbe`
/// fordert (Runde 3, Task 2). 0, solange nichts von `farbe` oeffentlich
/// verbraucht ist (`verbleibend == TILES_PER_COLOR`); steigt LINEAR bis
/// `ENGPASS_MAX`, wenn nichts mehr uebrig ist (`verbleibend <= 0`).
///
/// `ENGPASS_MAX = 2.5` ist so gewaehlt, dass eine RESTLOS aufgebrauchte
/// Farbe eine offene Zeile (Basis 1,0) teurer macht als eine an eine ANDERE
/// Farbe gebundene Zeile (2,0): 1,0 + 2,5 = 3,5 > 2,0 -- "auch wenn die Reihe
/// frei ist" (wortgleiche Nutzer-Vorgabe) gilt damit selbst im Extremfall.
const ENGPASS_MAX: f64 = 2.5;

pub(crate) fn engpass_aufschlag(verbleibend: &[i64; 5], farbe: TileColor) -> f64 {
    let Some(i) = crate::provokation::farben_index(farbe) else {
        return 0.0; // Wild ist keine ziehbare Farbe, kommt hier nie vor; defensiv.
    };
    let frac = (verbleibend[i].max(0) as f64 / crate::tile::TILES_PER_COLOR as f64).min(1.0);
    ENGPASS_MAX * (1.0 - frac)
}

/// Kosten einer noch unbefuellten Special-Zelle `(r, spalte)`: `0,3 + 0,8 *
/// n`, `n` = Zahl der noch NICHT gefuellten der 3 anderen Zellen im selben
/// 2x2-Dome-Slot. Geometrie wie `slot_score` (Slot `(r/2, spalte/2)` deckt
/// Rasterzeilen `2*(r/2)`/`2*(r/2)+1` und -spalten `2*(spalte/2)`/
/// `2*(spalte/2)+1` ab) -- hier reicht die Zeilen-/Spaltenrechnung direkt,
/// ohne Rotation/`tile.spaces`, weil nur der FUELLSTAND der Nachbarn zaehlt,
/// nicht ihre Farbe. Fehlt ein Nachbar-Slot ganz (kein `DomeSpace`, sollte bei
/// einer bereits platzierten Kachel nicht vorkommen), zaehlt er als GEFUELLT
/// (konservativ: kein Nachbar heisst hier kein zusaetzlicher Blocker).
pub(crate) fn special_kosten(player: &PlayerBoard, r: usize, spalte: usize) -> f64 {
    let slot_row = r / 2;
    let slot_col = spalte / 2;
    let mut offene_nachbarn = 0u32;
    for dr in 0..2usize {
        for dc in 0..2usize {
            let rr = slot_row * 2 + dr;
            let cc = slot_col * 2 + dc;
            if rr == r && cc == spalte {
                continue; // die Special-Zelle selbst ist kein eigener Nachbar.
            }
            let gefuellt = player.dome_grid.get_space(rr, cc).map_or(true, |s| s.is_filled());
            if !gefuellt {
                offene_nachbarn += 1;
            }
        }
    }
    0.3 + 0.8 * offene_nachbarn as f64
}

/// Toleranzband um das Kosten-Minimum, innerhalb dessen eine Spalte als
/// "nahe am Minimum" gilt (Task 7c). Kalibriert auf die Kosten-Skala oben:
/// deckt bis zu zwei Zeilen roher Geschmacksunterschiede ab (Wild 0,2 vs.
/// offene/passende Normal-Zelle 0,3, macht 0,1 je Zeile), schliesst aber
/// jede einzelne echte Blockade-Zeile aus (kleinster Blockade-Sprung: offene
/// Musterreihe 1,0 -> falsch gebundene Normal-Zelle 2,0, ein Sprung von 1,0).
const SPALTEN_TOLERANZ: f64 = 0.5;

/// Waehlt EINE Spalte aus den Kosten aller 6 Spalten: die guenstigste ODER --
/// bei gesetztem Partie-Seed (Task 7c, Nutzer-Auftrag 2026-08-13) -- eine
/// deterministisch GESTREUTE Wahl unter allen Spalten, deren Kosten
/// hoechstens `SPALTEN_TOLERANZ` ueber dem Minimum liegen. Ohne Seed
/// (Bestandsverhalten, auch in allen bisherigen Tests) gewinnt bei
/// Gleichstand/Naehe weiterhin die KLEINSTE Spaltennummer -- stabil,
/// deterministisch, `<` statt `<=` beim Minimum-Vergleich.
///
/// WARUM Streuung ueberhaupt noetig ist: ohne jede Platte sind alle 6 Spalten
/// exakt gleich teuer (6,0) -- ohne Streuung waere die Zielspalte damit fuer
/// JEDE Partie zu Beginn IMMER Spalte 0, und ein frueher Wechsel weg von
/// Spalte 0 braeuchte einen Kostenunterschied, der sich oft erst spaet
/// einstellt. Das Verteilungs-Gate (Nutzer-Ergaenzung) prueft genau das:
/// Ereignisse muessen auf allen sechs Spalten auftauchen, nicht nur auf 0.
fn waehle_spalte(kosten: [f64; 6]) -> usize {
    let min_kosten = kosten.iter().cloned().fold(f64::INFINITY, f64::min);
    let kandidaten: Vec<usize> = (0..6usize).filter(|&c| kosten[c] - min_kosten <= SPALTEN_TOLERANZ).collect();
    if kandidaten.len() <= 1 {
        return kandidaten.first().copied().unwrap_or(0);
    }
    match PARTIE_SEED.with(|c| c.get()) {
        None => kandidaten[0],
        Some(seed) => kandidaten[index_aus_seed(seed, kandidaten.len())],
    }
}

thread_local! {
    /// Partie-Seed fuer die Kosten-Streuung in [`waehle_spalte`] (Task 7c).
    /// `None` = kein Seed gesetzt -- Bestandsverhalten (kleinste
    /// Spaltennummer bei Gleichstand/Naehe).
    static PARTIE_SEED: std::cell::Cell<Option<u64>> = const { std::cell::Cell::new(None) };
}

/// Setzt (oder loescht mit `None`) den Partie-Seed fuer DIESEN Thread --
/// gleiches Muster wie `net_mcts::set_partie_shaping_weight`/
/// `provokation::set_ziel_spalte_seed`. Aufrufer MUSS am Partieende (oder vor
/// der naechsten Partie desselben Threads) mit `None`/dem neuen Seed
/// ueberschreiben, sonst leckt der Wert in die naechste Partie.
pub(crate) fn set_partie_seed(seed: Option<u64>) {
    PARTIE_SEED.with(|c| c.set(seed));
}

/// Deterministische Mischung Seed -> Index `0..n` -- identisches SplitMix64-
/// Muster wie `net_mcts::partie_gewicht_aus_seed`/`provokation::spalte_aus_
/// seed` (aufeinanderfolgende Partie-Seeds unterscheiden sich im Self-Play
/// oft nur in den unteren Bits, eine rohe Modulo-Bildung ergaebe eine Treppe
/// statt einer Streuung). `n == 0` kommt hier nie vor (Aufrufer filtert immer
/// mindestens den Minimum-Eintrag selbst ein), degradiert defensiv auf 0.
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

/// Ziel-Spalte fuer den AKTIVEN Spieler -- frisch aus `state` berechnet, KEIN
/// gespeicherter Zustand. Genau dadurch "erlaubt" die Funktion einen Wechsel,
/// wenn die bisherige Ziel-Spalte unbedienbar wird (Nutzer-Vorgabe): der
/// naechste Aufruf sieht den neuen Brettzustand und kann eine andere Spalte
/// liefern, ohne dass irgendwo ein Flag geloescht werden muesste (kein
/// Leck-Risiko wie bei `provokation::AUTO_SPALTE`/`set_ziel_spalte_seed`).
/// Auswahl unter den guenstigsten Kandidaten: siehe [`waehle_spalte`].
pub(crate) fn ziel_spalte(state: &GameState) -> Option<usize> {
    if !ist_aktiv() {
        return None;
    }
    let player = &state.players[state.current_player];
    let verbleibend = crate::provokation::verbleibende_farben(state);
    let kosten: [f64; 6] = std::array::from_fn(|c| spalten_kosten(player, c, &verbleibend));
    Some(waehle_spalte(kosten))
}

// ── Wiederverwendung: Stein-Zug- und Tiling-Praeferenz mit dynamischer Spalte ──

/// Stein-Zug-Praeferenz, IDENTISCHE Logik zu `provokation::vorzugszug`, aber
/// mit der je Entscheid dynamisch bestimmten Spalte statt `MOSAIC_VORZUG_SPALTE`.
pub(crate) fn vorzugszug(state: &GameState) -> Option<Action> {
    let spalte = ziel_spalte(state)?;
    crate::provokation::vorzugszug_fuer_spalte(state, spalte)
}

/// Tiling-Routing-Praeferenz, IDENTISCHE Logik zu
/// `tiling_solver::vorzug_tiling_step`, aber mit der dynamischen Spalte.
/// Aufrufstelle: `tiling_solver::best_first_step_exact_or_valued` (PRUEFT
/// diese Funktion ZUERST, dann erst den Env-Knopf-Pfad) -- ohne das wuerde
/// eine im Drafting korrekt gelieferte Farbe beim Tiling in eine andere
/// Rasterzelle wandern (der in `vorzug_tiling_step`s Doku genannte
/// 10-von-18-Blocker waere fuer den Spaltenbauer unadressiert).
pub(crate) fn vorzug_tiling_step(state: &GameState, pi: usize) -> Option<TilingStep> {
    if !ist_aktiv() {
        return None;
    }
    // `pi` bewusst NICHT durch `state.current_player` ersetzt und stattdessen
    // `ziel_spalte(state)` aufgerufen -- die beiden sind an dieser Aufrufstelle
    // in der Praxis identisch (siehe self_play.rs, `Phase::Tiling`-Arm), aber
    // die Signatur haelt die Unterscheidung bewusst offen, gleiche Auswahl-
    // Logik wie `ziel_spalte` ueber [`waehle_spalte`].
    let player = &state.players[pi];
    let verbleibend = crate::provokation::verbleibende_farben(state);
    let kosten: [f64; 6] = std::array::from_fn(|c| spalten_kosten(player, c, &verbleibend));
    let spalte = waehle_spalte(kosten);
    crate::tiling_solver::vorzug_tiling_step_fuer_spalte(state, pi, spalte)
}

// ── Hauptaufgabe 1: Kuppelplatten-Wahl steuert required_color ──────────────

/// Wie gut bedient `space` (bereits an Zeile `r` haengend gedacht) die
/// Ziel-Spalte, bevor die Platte ueberhaupt liegt? Wild/Special sind immer
/// gut (keine Farbbindung noetig); eine Normal-Farbe ist gut, wenn die
/// Musterreihe `r` schon leer ist oder GENAU diese Farbe fuehrt, und
/// ungeeignet (0), wenn die Reihe an eine andere Farbe gebunden ist.
pub(crate) fn zellen_wert(player: &PlayerBoard, r: usize, space: &DomeSpace) -> f64 {
    match space.space_type {
        SpaceType::Wild => 3.0,
        SpaceType::Special => 2.0,
        SpaceType::Normal => match (player.pattern_lines[r].color, space.required_color) {
            (None, _) => 1.5,
            (Some(c), Some(x)) if c == x => 2.5,
            _ => 0.0,
        },
    }
}

/// Score einer (Kachel, Slot, Rotation)-Kombination fuer die Ziel-Spalte:
/// Summe von [`zellen_wert`] ueber die GENAU 2 Zellen, die nach Rotation in
/// die Ziel-Spalte fallen. `None`, wenn der Slot die Ziel-Spalte gar nicht
/// beruehrt (`slot_col != spalte / 2`) -- dann hat die Wahl fuer dieses Ziel
/// keine Bedeutung, der Spaltenbauer soll sich da nicht einmischen.
///
/// Geometrie (`DomeGrid::cell_to_dome_space`, board.rs:98, `dome.rs::
/// rotation_indices`): Slot `(slot_row, slot_col)` deckt Rasterzeilen
/// `2*slot_row`/`2*slot_row+1` und -spalten `2*slot_col`/`2*slot_col+1` ab.
/// Ziel-Spalte `spalte` liegt im Slot am Spalten-Offset `cc = spalte % 2`;
/// die zugehoerigen PLATZIERTEN Space-Indizes sind `cc` (obere Rasterzeile)
/// und `2+cc` (untere). `apply_rotation`/`rotated_spaces` setzen
/// `neue_spaces[i] = alte_spaces[idx[i]]` -- also liest man hier
/// UNROTIERT aus `tile.spaces[idx[i]]`, dieselbe Formel rueckwaerts.
fn slot_score(
    player: &PlayerBoard,
    tile: &DomeTile,
    slot_row: usize,
    slot_col: usize,
    rotation: u32,
    spalte: usize,
) -> Option<f64> {
    if slot_col != spalte / 2 {
        return None;
    }
    let idx = rotation_indices(rotation)?;
    let cc = spalte % 2;
    let top_row = slot_row * 2;
    let bottom_row = slot_row * 2 + 1;
    let top_space = &tile.spaces[idx[cc]];
    let bottom_space = &tile.spaces[idx[cc + 2]];
    Some(zellen_wert(player, top_row, top_space) + zellen_wert(player, bottom_row, bottom_space))
}

/// Kuppelplatten-Praeferenz: steuert BEIDE Stufen des zweistufigen
/// Kuppel-Suchknotens (`moves.rs::PendingDomeChoice`/`Action::ChooseDomeSlot`/
/// `Action::ChooseDomeRotation`) auf die dynamische Ziel-Spalte, PRAEFERENZ
/// wie `provokation::vorzugszug` -- greift nur, wenn ein Kandidat echten
/// Nutzen zeigt (`score > 0`), sonst `None` und das Netz entscheidet frei.
///
/// Aufrufstelle: dieselben Drafting-Entscheidpunkte wie `vorzugszug`
/// (self_play.rs) -- `drafting_actions` liefert `ChooseDomeSlot`/
/// `ChooseDomeRotation` als Kandidaten in DERSELBEN Aktionsliste, es ist also
/// keine eigene Codestelle, sondern dieselbe `.or_else(...)`-Kette.
///
/// Stufe 2 (Rotation, `pending_dome_choice` gesetzt) zuerst geprueft, weil
/// dort die einzig noch offene Entscheidung eine Zahl (Rotation) ist und der
/// Fall haeufiger vorkommt, sobald Stufe 1 einmal gegriffen hat.
/// `FromDrawStack` (Stapel-Variante) bewusst NICHT abgedeckt -- seltener Pfad
/// (Aktion A), siehe Bericht.
pub(crate) fn vorzug_dome_wahl(state: &GameState) -> Option<Action> {
    if !ist_aktiv() {
        return None;
    }
    let spalte = ziel_spalte(state)?;
    let player = &state.players[state.current_player];

    if let Some(choice) = &state.pending_dome_choice {
        return match choice {
            PendingDomeChoice::FromDisplay { dome_tile_id, slot_row, slot_col } => {
                if *slot_col != spalte / 2 {
                    return None;
                }
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
                    if let Some(score) = slot_score(player, tile, *slot_row, *slot_col, rot, spalte) {
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
    let target_slot_col = spalte / 2;
    let mut best: Option<(f64, usize, usize)> = None; // (score, tile_id, slot_row)
    for tile in &state.dome_display {
        for &(sr, sc) in &player.dome_grid.empty_slots() {
            if sc != target_slot_col {
                continue;
            }
            let mut best_rot_score: Option<f64> = None;
            for rot in [0u32, 90, 180, 270] {
                let m = PlaceDomeTileMove {
                    dome_tile_id: tile.tile_id,
                    slot_row: sr,
                    slot_col: sc,
                    rotation: rot,
                };
                if crate::game::validate_dome_move(state, &m).is_some() {
                    continue;
                }
                if let Some(score) = slot_score(player, tile, sr, sc, rot, spalte) {
                    if best_rot_score.map_or(true, |b| score > b) {
                        best_rot_score = Some(score);
                    }
                }
            }
            if let Some(score) = best_rot_score {
                if best.as_ref().map_or(true, |(bs, _, _)| score > *bs) {
                    best = Some((score, tile.tile_id, sr));
                }
            }
        }
    }
    best.filter(|(s, _, _)| *s > 0.0).map(|(_, tid, sr)| {
        Action::ChooseDomeSlot(PlaceDomeTileMove {
            dome_tile_id: tid,
            slot_row: sr,
            slot_col: target_slot_col,
            rotation: 0,
        })
    })
}

// ── Entscheidungs-Spur (Nutzer-Ergaenzung 2026-08-13, VOR der Runde-2- ──────
// Abnahme angefordert): "damit die Iteration sieht, WIE die Entscheidungen
// fallen, nicht nur die Aggregate". `MOSAIC_SPALTENBAU_TRACE=1` (Default
// AUS, Paritaet unberuehrt) schreibt je Entscheidung EINE zusaetzliche
// Logzeile mit Praefix `[SB]` ueber den bestehenden `log_event`-Strom --
// ADDITIV, keine bestehende Logzeile aendert sich (der pre-push-Hook und
// `analyze_game_log.py`s Regexes haengen am Wortlaut der ALTEN Zeilen, siehe
// dortige Muster). `log_event` selbst haengt bereits `[R{runde}] ` vor jede
// Zeile -- die Zeilen hier tragen deshalb nur noch das `[SB]`-Praefix.

/// Liest `MOSAIC_SPALTENBAU_TRACE` einmalig (Prozess-Cache, gleiches Muster
/// wie `aktiv_env`).
fn trace_env() -> bool {
    static CELL: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| match std::env::var("MOSAIC_SPALTENBAU_TRACE") {
        Err(_) => false,
        Ok(raw) => {
            let v = raw.trim();
            !v.is_empty() && v != "0"
        }
    })
}

#[cfg(test)]
thread_local! {
    static TRACE_OVERRIDE: std::cell::Cell<Option<bool>> = const { std::cell::Cell::new(None) };
}

#[cfg(test)]
pub(crate) fn set_trace_override_for_test(v: Option<bool>) {
    TRACE_OVERRIDE.with(|c| c.set(v));
}

fn ist_trace_aktiv() -> bool {
    #[cfg(test)]
    {
        if let Some(v) = TRACE_OVERRIDE.with(|c| c.get()) {
            return v;
        }
    }
    trace_env()
}

/// Alle Farben, die JETZT irgendwo nehmbar sind (Fabriken, grosse Fabrik,
/// Mond, Stapel) -- direkt aus `validation::generate_valid_moves` extrahiert
/// statt Quellen einzeln nachzubauen (CLAUDE.md: Bestehendes wiederverwenden).
/// Gruppiert nach Quelle fuer die Log-Lesbarkeit ("welche Farben in welchen
/// Quellen verfuegbar" -- Nutzer-Vorgabe).
fn angebot_zusammenfassung(state: &GameState) -> String {
    let mut nach_quelle: std::collections::BTreeMap<String, std::collections::BTreeSet<String>> =
        std::collections::BTreeMap::new();
    for m in crate::validation::generate_valid_moves(state) {
        let quelle = match m.take.source {
            crate::moves::TakeSource::SmallFactorySun => {
                format!("F{}s", m.take.factory_id.unwrap_or(0))
            }
            crate::moves::TakeSource::SmallFactoryMoon => match m.take.factory_id {
                Some(id) => format!("F{id}m"),
                None => "Mond".to_string(),
            },
            crate::moves::TakeSource::LargeFactorySun => "GFs".to_string(),
            crate::moves::TakeSource::LargeFactoryMoon => "GFm".to_string(),
        };
        nach_quelle.entry(quelle).or_default().insert(format!("{:?}", m.take.color));
    }
    if nach_quelle.is_empty() {
        return "keine_zuege".to_string();
    }
    nach_quelle
        .into_iter()
        .map(|(q, farben)| format!("{q}:{}", farben.into_iter().collect::<Vec<_>>().join("+")))
        .collect::<Vec<_>>()
        .join(";")
}

/// Warum existierte KEIN Vorzugs-Kandidat fuer `spalte`? Erste Zeile in
/// `spalte` mit einem konkreten, benennbaren Blockade-Grund (Nutzer-Vorgabe:
/// "geforderte Farbe nicht im Angebot? Reihe blockiert mit anderer Farbe?
/// Zelle schon voll? Slot fehlt?"). Special-Zeilen werden uebersprungen (sie
/// nehmen nie eine Farbe entgegen, sind also kein Vorzugs-Blocker in diesem
/// Sinn); Wild-Zeilen nur, wenn ueberhaupt keine Farbe im Angebot ist (jede
/// Farbe qualifiziert dort, siehe `provokation::vorzugszug_fuer_spalte`).
fn kein_vorzug_grund(state: &GameState, player: &PlayerBoard, spalte: usize) -> String {
    let angebot: std::collections::HashSet<TileColor> = crate::validation::generate_valid_moves(state)
        .into_iter()
        .map(|m| m.take.color)
        .collect();
    for r in 0..6usize {
        let Some(sp) = player.dome_grid.get_space(r, spalte) else {
            continue; // "Slot fehlt" -- kein benennbarer Blocker in DIESER Zeile.
        };
        if sp.is_filled() {
            continue; // "Zelle schon voll" -- ebenfalls kein aktueller Blocker.
        }
        match sp.space_type {
            SpaceType::Special => continue,
            SpaceType::Wild => {
                if angebot.is_empty() {
                    return format!("Zeile{r}:keine_farbe_im_angebot(Wild)");
                }
            }
            SpaceType::Normal => {
                let Some(need) = sp.required_color else { continue };
                if let Some(gebunden) = player.pattern_lines[r].color {
                    if gebunden != need {
                        return format!("Zeile{r}:reihe_gebunden_an_{gebunden:?}_statt_{need:?}");
                    }
                }
                if !angebot.contains(&need) {
                    return format!("Zeile{r}:farbe_{need:?}_nicht_im_angebot");
                }
            }
        }
    }
    "keine_offene_zeile_in_zielspalte".to_string()
}

/// Baut (bei aktivem Trace-Knopf UND aktivem Spaltenbau) eine `[SB]`-Logzeile
/// fuer EINE Entscheidung, sonst `None`. Rein lesend (`&GameState`) -- der
/// Aufrufer schreibt die Zeile per `state.log_event(..)` NACH der
/// Entscheidung (dort ist wieder `&mut GameState` verfuegbar).
///
/// `entscheidungstyp`: "Drafting" | "Dome" | "Tiling".
/// `vorzug_kandidat`: die vom AUFRUFER schon ermittelte Praeferenz-Aktion
/// (`spaltenbau`/`provokation`, VOR dem Fallback auf die Netz-Suche) -- bei
/// `None` haelt diese Funktion selbst fest, WARUM keine existierte.
pub(crate) fn trace_zeile(
    state: &GameState,
    pi: usize,
    entscheidungstyp: &str,
    vorzug_kandidat: Option<&dyn std::fmt::Debug>,
    gespielte_aktion: &dyn std::fmt::Debug,
) -> Option<String> {
    if !ist_trace_aktiv() || !ist_aktiv() {
        return None;
    }
    let player = &state.players[pi];
    let verbleibend = crate::provokation::verbleibende_farben(state);
    let kosten: [f64; 6] = std::array::from_fn(|c| spalten_kosten(player, c, &verbleibend));
    let ziel = waehle_spalte(kosten);
    let mut sortiert: Vec<(usize, f64)> = (0..6usize).map(|c| (c, kosten[c])).collect();
    sortiert.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap());
    let top2 = sortiert
        .iter()
        .take(2)
        .map(|(c, k)| format!("{c}:{k:.2}"))
        .collect::<Vec<_>>()
        .join(",");

    let vorzug = match vorzug_kandidat {
        // "VorzugAktion" bewusst NICHT "Aktion" (Namenskollision mit dem
        // AEUSSEREN `Aktion=`-Feld der Zeile weiter unten, das die
        // tatsaechlich GESPIELTE Aktion trägt -- zwei Felder mit demselben
        // Namen waeren fuer `tools/spaltenbau_trace.py`s Parser nicht mehr
        // eindeutig trennbar, weil beide Rust-Debug-Text mit Leerzeichen
        // enthalten koennen).
        Some(a) => format!("ja VorzugAktion={a:?}"),
        None => format!("nein Grund={}", kein_vorzug_grund(state, player, ziel)),
    };

    let angebot_teil = if entscheidungstyp == "Drafting" {
        format!(" Angebot={}", angebot_zusammenfassung(state))
    } else {
        String::new()
    };

    Some(format!(
        "[SB] Spieler={pi} Typ={entscheidungstyp} Ziel={ziel} Top2=[{top2}] \
         Vorzug={vorzug} Aktion={gespielte_aktion:?}{angebot_teil}"
    ))
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
        set_aktiv_override_for_test(Some(false));
        let game = drafting_game(1);
        assert_eq!(ziel_spalte(&game.state), None);
        assert_eq!(vorzugszug(&game.state), None);
        assert_eq!(vorzug_dome_wahl(&game.state), None);
        assert!(vorzug_tiling_step(&game.state, 0).is_none());
        set_aktiv_override_for_test(None);
    }

    /// Nutzer-Ergaenzung 2026-08-13 (Trace-Knopf): ohne `MOSAIC_SPALTENBAU_
    /// TRACE` (auch bei aktivem Spaltenbau) darf `trace_zeile` NIE etwas
    /// liefern -- additiv heisst additiv, keine ungewollte Log-Flut.
    #[test]
    fn trace_zeile_ist_ohne_trace_knopf_immer_none() {
        set_aktiv_override_for_test(Some(true));
        set_trace_override_for_test(Some(false));
        let game = drafting_game(60);
        let pi = game.state.current_player;
        let aktion = Action::Pass;
        assert_eq!(
            trace_zeile(&game.state, pi, "Drafting", None, &aktion as &dyn std::fmt::Debug),
            None,
            "ohne MOSAIC_SPALTENBAU_TRACE darf nie eine Zeile entstehen"
        );
        set_trace_override_for_test(None);
        set_aktiv_override_for_test(None);
    }

    /// Bei aktivem Trace-Knopf muss die Zeile das `[SB]`-Praefix tragen und
    /// die Kernfelder enthalten -- UND ohne Spaltenbau selbst (`ist_aktiv`
    /// aus) trotzdem `None` bleiben (der Trace-Knopf allein schaltet nichts
    /// frei, er ist additiv ZUM Spaltenbauer, kein Ersatz).
    #[test]
    fn trace_zeile_hat_sb_praefix_und_kernfelder_bei_aktivem_knopf() {
        set_aktiv_override_for_test(Some(false));
        set_trace_override_for_test(Some(true));
        let game = drafting_game(61);
        let pi = game.state.current_player;
        let aktion = Action::Pass;
        assert_eq!(
            trace_zeile(&game.state, pi, "Drafting", None, &aktion as &dyn std::fmt::Debug),
            None,
            "Trace ohne aktiven Spaltenbauer muss weiterhin None liefern"
        );

        set_aktiv_override_for_test(Some(true));
        let zeile = trace_zeile(&game.state, pi, "Drafting", None, &aktion as &dyn std::fmt::Debug)
            .expect("bei beiden Knoepfen aktiv muss eine Zeile entstehen");
        assert!(zeile.starts_with("[SB] "), "Zeile muss mit [SB] beginnen: {zeile:?}");
        assert!(zeile.contains(&format!("Spieler={pi}")), "muss den Spieler tragen: {zeile:?}");
        assert!(zeile.contains("Typ=Drafting"), "muss den Entscheidungstyp tragen: {zeile:?}");
        assert!(zeile.contains("Ziel="), "muss die Zielspalte tragen: {zeile:?}");
        assert!(zeile.contains("Top2=["), "muss die zwei guenstigsten Spalten tragen: {zeile:?}");
        assert!(zeile.contains("Vorzug=nein"), "ohne Kandidat muss Vorzug=nein stehen: {zeile:?}");
        assert!(zeile.contains("Angebot="), "Drafting-Zeilen muessen das Angebot tragen: {zeile:?}");

        set_trace_override_for_test(None);
        set_aktiv_override_for_test(None);
    }

    /// Fuer Tiling-Zeilen darf KEIN `Angebot=`-Feld auftauchen (Nutzer-Vorgabe:
    /// nur Drafting braucht das aktuelle Angebot).
    #[test]
    fn trace_zeile_traegt_kein_angebot_bei_tiling() {
        set_aktiv_override_for_test(Some(true));
        set_trace_override_for_test(Some(true));
        let game = drafting_game(62);
        let pi = game.state.current_player;
        let aktion = Action::Pass;
        let zeile = trace_zeile(&game.state, pi, "Tiling", None, &aktion as &dyn std::fmt::Debug)
            .expect("Tiling-Zeile muss entstehen");
        assert!(!zeile.contains("Angebot="), "Tiling-Zeilen duerfen kein Angebot tragen: {zeile:?}");
        set_trace_override_for_test(None);
        set_aktiv_override_for_test(None);
    }

    /// Runde 3, Task 2: `engpass_aufschlag` muss 0 sein, solange nichts von
    /// der Farbe verbraucht ist, linear bis `ENGPASS_MAX` bei restlosem
    /// Verbrauch steigen, und dazwischen (halbe Versorgung) einen Wert
    /// STRIKT zwischen 0 und `ENGPASS_MAX` liefern.
    #[test]
    fn engpass_aufschlag_ist_linear_zwischen_voll_und_leer() {
        let voll = [crate::tile::TILES_PER_COLOR as i64; 5];
        let leer = [0i64; 5];
        let i = crate::provokation::farben_index(Rot).unwrap();
        assert_eq!(engpass_aufschlag(&voll, Rot), 0.0, "reichliche Farbe darf keinen Aufschlag tragen");
        assert!(
            (engpass_aufschlag(&leer, Rot) - ENGPASS_MAX).abs() < 1e-9,
            "restlos verbrauchte Farbe muss den vollen Aufschlag ENGPASS_MAX tragen"
        );
        let mut halb = voll;
        halb[i] = crate::tile::TILES_PER_COLOR as i64 / 2;
        let a_halb = engpass_aufschlag(&halb, Rot);
        assert!(
            a_halb > 0.0 && a_halb < ENGPASS_MAX,
            "bei halber Versorgung muss der Aufschlag strikt zwischen 0 und ENGPASS_MAX liegen: {a_halb}"
        );
    }

    /// Runde 3, Task 2 (Kernabnahme): eine OFFENE Musterreihe muss teurer
    /// werden, wenn ihre geforderte Farbe restlos verbraucht ist -- UND zwar
    /// so teuer, dass sie sogar eine FALSCH GEBUNDENE Zeile (Basis 2,0)
    /// uebersteigt ("auch wenn die Reihe frei ist", wortgleiche
    /// Nutzer-Vorgabe; ENGPASS_MAX-Kalibrierung: 1,0 + 2,5 = 3,5 > 2,0).
    #[test]
    fn spalten_kosten_offene_zeile_wird_teurer_bei_knapper_farbe() {
        set_aktiv_override_for_test(Some(true));
        let mut game = drafting_game(70);
        let pi = game.state.current_player;
        // Slot (0,0): si=0 -> (Zeile0,Spalte0) fordert Rot.
        let tile = normal_tile(70, [Rot, Blau, Gelb, Schwarz]);
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("frei");

        let voll = [crate::tile::TILES_PER_COLOR as i64; 5];
        let mut leer_rot = voll;
        leer_rot[crate::provokation::farben_index(Rot).unwrap()] = 0;

        let k_voll = spalten_kosten(&game.state.players[pi], 0, &voll);
        let k_knapp = spalten_kosten(&game.state.players[pi], 0, &leer_rot);
        assert!(
            k_knapp > k_voll,
            "restlos verbrauchtes Rot muss Spalte 0 teurer machen: voll={k_voll} knapp={k_knapp}"
        );
        assert!(
            k_knapp - k_voll > 2.0,
            "Aufschlag bei Vollverbrauch muss > 2,0 sein (uebersteigt die falsch-gebundene Basis 2,0): {}",
            k_knapp - k_voll
        );
        set_aktiv_override_for_test(None);
    }

    #[test]
    fn spalten_kosten_bevorzugt_wild_und_bestehende_farbe() {
        // Spalte 0 (leerer Slot ueberall) vs. Spalte 1 mit einer Wild-Zelle
        // in Zeile 0 -- Spalte 1 muss billiger sein.
        set_aktiv_override_for_test(Some(true));
        let mut game = drafting_game(2);
        let pi = game.state.current_player;
        let tile = DomeTile::new(
            9,
            vec![
                DomeSpace::wild(),
                DomeSpace::normal(Rot),
                DomeSpace::normal(Blau),
                DomeSpace::normal(Gelb),
            ],
            0,
        );
        // Slot (0,0) deckt Spalten 0/1 ab; si=0 -> (Zeile0,Spalte0)=Wild,
        // si=1 -> (Zeile0,Spalte1)=Rot.
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("frei");
        // Ueberall reichlich Versorgung (Runde 3): dieser Test prueft
        // Wild-vs-Normal, nicht Versorgung -- der Engpass-Aufschlag soll hier
        // 0 bleiben (siehe `engpass_aufschlag`-Kalibrierung).
        let voll = [crate::tile::TILES_PER_COLOR as i64; 5];
        let k_wild_spalte = spalten_kosten(&game.state.players[pi], 0, &voll);
        let k_normal_spalte = spalten_kosten(&game.state.players[pi], 1, &voll);
        assert!(
            k_wild_spalte < k_normal_spalte,
            "Spalte mit Wild-Zelle (0) muss billiger sein als Spalte mit gebundener Normal-Zelle (1): {k_wild_spalte} vs {k_normal_spalte}"
        );
        set_aktiv_override_for_test(None);
    }

    /// Task 7b: eine Special-Zelle MUSS teurer werden, je mehr ihrer 3
    /// Slot-Nachbarn noch offen sind -- 0 offene Nachbarn (alle gefuellt)
    /// muss so billig sein wie eine passende Normal-Zelle (0,3); 3 offene
    /// Nachbarn (keiner gefuellt) muss teurer sein als eine falsch gebundene
    /// Normal-Zelle (2,0).
    #[test]
    fn special_kosten_skaliert_mit_offenen_slot_nachbarn() {
        set_aktiv_override_for_test(Some(true));
        let mut game = drafting_game(50);
        let pi = game.state.current_player;
        // Slot (0,0): si=0->(Zeile0,Spalte0)=Special, si=1->(Zeile0,Spalte1),
        // si=2->(Zeile1,Spalte0), si=3->(Zeile1,Spalte1) -- alle drei
        // Nachbarn zunaechst NORMAL und ungefuellt (kein `placed_color`).
        let tile = DomeTile::new(
            60,
            vec![
                DomeSpace::special(),
                DomeSpace::normal(Rot),
                DomeSpace::normal(Blau),
                DomeSpace::normal(Gelb),
            ],
            0,
        );
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("frei");
        // Reichlich Versorgung (Runde 3): dieser Test prueft Special-Skalierung,
        // nicht Versorgung -- Aufschlag soll hier 0 bleiben.
        let voll = [crate::tile::TILES_PER_COLOR as i64; 5];
        let k_alle_offen = spalten_kosten(&game.state.players[pi], 0, &voll);

        // Alle drei Nachbarn direkt als gefuellt markieren (Farbe + Special-
        // Zelle selbst bleibt ungefuellt) -- die Special-Zelle muss jetzt
        // deutlich billiger sein.
        {
            let slot = game.state.players[pi].dome_grid.dome_slots[0][0].as_mut().unwrap();
            slot.spaces[1].placed_color = Some(Rot);
            slot.spaces[2].placed_color = Some(Blau);
            slot.spaces[3].placed_color = Some(Gelb);
        }
        let k_alle_gefuellt = spalten_kosten(&game.state.players[pi], 0, &voll);

        assert!(
            k_alle_gefuellt < k_alle_offen,
            "mehr gefuellte Nachbarn muss die Spalte billiger machen: offen={k_alle_offen} gefuellt={k_alle_gefuellt}"
        );
        // Untere Schranke: bei 0 offenen Nachbarn traegt die Special-Zelle
        // (Zeile 0) exakt 0,3 zu den Kosten bei; Zeile 1 ist der SIBLING
        // si=2 (Zeile1/Spalte0, siehe Slot-Geometrie oben) -- jetzt gefuellt,
        // traegt 0,0 bei; Zeilen 2-5 haben in Spalte 0 keinen Slot (1,0 je
        // Zeile, 4 Zeilen).
        assert!(
            (k_alle_gefuellt - (0.3 + 0.0 + 4.0)).abs() < 1e-9,
            "bei 0 offenen Nachbarn: 0,3 (Special) + 0,0 (Zeile1 gefuellt) + 4,0 (4 leere Zeilen): war {k_alle_gefuellt}"
        );
        // Obere Schranke: bei 3 offenen Nachbarn (0,3 + 0,8*3 = 2,7 fuer die
        // Special-Zelle) muss die Spalte teurer sein als dieselbe Spalte mit
        // einer falsch gebundenen NORMAL-Zelle (2,0) an derselben Stelle.
        assert!(
            k_alle_offen > 2.0 + 0.0 + 4.0,
            "bei 3 offenen Nachbarn muss Special (2,7+Rest) teurer sein als eine falsch gebundene Normal-Zelle (2,0+Rest): war {k_alle_offen}"
        );
        set_aktiv_override_for_test(None);
    }

    /// Task 7c: bei gesetztem Partie-Seed wird unter mehreren gleich guten
    /// Spalten GESTREUT statt immer Spalte 0 zu waehlen -- UND die Wahl ist
    /// fuer denselben Seed reproduzierbar. Ohne Seed bleibt Spalte 0
    /// (Bestandsverhalten, siehe `ziel_spalte_wechselt_wenn_bisherige_spalte_
    /// teurer_wird`).
    #[test]
    fn waehle_spalte_streut_unter_seed_und_bleibt_ohne_seed_stabil() {
        let kosten = [6.0; 6]; // wie beim leeren Brett: alle Spalten gleich teuer.
        assert_eq!(waehle_spalte(kosten), 0, "ohne Seed muss die kleinste Spaltennummer gewinnen");

        let mut gesehen = std::collections::HashSet::new();
        for seed in 0u64..40 {
            set_partie_seed(Some(seed));
            let c = waehle_spalte(kosten);
            assert!(c < 6, "Spalte muss in 0..6 liegen, war {c}");
            gesehen.insert(c);
            // Reproduzierbarkeit: derselbe Seed liefert immer dieselbe Spalte.
            assert_eq!(waehle_spalte(kosten), c, "Seed {seed} muss reproduzierbar dieselbe Spalte liefern");
        }
        set_partie_seed(None);
        assert!(
            gesehen.len() >= 3,
            "40 verschiedene Seeds sollten mehr als 1-2 Spalten treffen, gesehen: {gesehen:?}"
        );

        // Ausserhalb der Toleranz (Spalte 5 deutlich teurer) darf die
        // Streuung sie NIE waehlen, unabhaengig vom Seed.
        let mut kosten_schief = [1.0; 6];
        kosten_schief[5] = 10.0;
        for seed in 0u64..20 {
            set_partie_seed(Some(seed));
            assert_ne!(
                waehle_spalte(kosten_schief), 5,
                "Seed {seed}: eine Spalte weit ausserhalb der Toleranz darf nie gewaehlt werden"
            );
        }
        set_partie_seed(None);
    }

    #[test]
    fn ziel_spalte_wechselt_wenn_bisherige_spalte_teurer_wird() {
        // Ohne jede Platte sind alle Spalten gleich teuer (6.0) -> Spalte 0
        // gewinnt (stabile Tie-Break-Regel). Sobald Zeile 0 von Spalte 0 an
        // eine ANDERE Farbe gebunden wird, muss die Wahl wechseln.
        set_aktiv_override_for_test(Some(true));
        let mut game = drafting_game(3);
        let pi = game.state.current_player;
        assert_eq!(ziel_spalte(&game.state), Some(0));

        let tile = normal_tile(10, [Rot, Blau, Gelb, Schwarz]);
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("frei");
        // Zeile 0 an Blau binden (falsche Farbe fuer Spalte 0, die Rot fordert).
        game.state.players[pi].pattern_lines[0].color = Some(Blau);
        game.state.players[pi].pattern_lines[0].tiles.push(Blau);

        let neu = ziel_spalte(&game.state).expect("Spaltenbau aktiv");
        assert_ne!(neu, 0, "Spalte 0 ist jetzt teurer (Zeile 0 an falsche Farbe gebunden) -- Wahl muss wechseln");
        set_aktiv_override_for_test(None);
    }

    #[test]
    fn vorzug_dome_wahl_stufe1_waehlt_slot_in_zielspalte() {
        // Ziel-Spalte 0 (Default bei leerem Brett) -> target_slot_col = 0.
        // Zwei Kacheln im Display: eine mit Wild an Position 0 (gut fuer
        // Spalte 0), eine rein normal -- die Wild-Kachel muss gewinnen.
        set_aktiv_override_for_test(Some(true));
        let mut game = drafting_game(4);
        game.state.dome_display = vec![
            normal_tile(20, [Rot, Blau, Gelb, Schwarz]),
            DomeTile::new(
                21,
                vec![DomeSpace::wild(), DomeSpace::normal(Blau), DomeSpace::normal(Gelb), DomeSpace::normal(Schwarz)],
                0,
            ),
        ];
        let a = vorzug_dome_wahl(&game.state).expect("Spaltenbau muss hier eingreifen");
        match a {
            Action::ChooseDomeSlot(m) => {
                assert_eq!(m.dome_tile_id, 21, "die Wild-Kachel (mehr Nutzen fuer Spalte 0) muss gewaehlt werden");
                assert_eq!(m.slot_col, 0, "Slot muss in der Ziel-Spalten-Slotspalte liegen");
            }
            other => panic!("erwartet ChooseDomeSlot, bekam {other:?}"),
        }
        set_aktiv_override_for_test(None);
    }

    #[test]
    fn vorzug_dome_wahl_stufe2_waehlt_rotation_mit_bestem_score() {
        // Stufe 1 schon getroffen (pending_dome_choice gesetzt): eine Kachel
        // mit Wild an Original-Index 1 -- bei Rotation 0 landet Wild an
        // Platzierungsposition 1 (Spalte-Offset 1, NICHT Ziel-Spalte 0);
        // bei Rotation 90 (idx=[2,0,3,1]) landet Wild an Position 3
        // (Spalte-Offset 1) -- wir brauchen eine Rotation, die Wild an
        // Spalte-Offset 0 (Position 0 oder 2) bringt: idx[0]==1 oder
        // idx[2]==1. idx(180)=[3,2,1,0] -> idx[2]=1 -- Rotation 180 muss
        // also die beste sein.
        set_aktiv_override_for_test(Some(true));
        let mut game = drafting_game(5);
        let pi = game.state.current_player;
        let tile = DomeTile::new(
            22,
            vec![
                DomeSpace::normal(Rot),
                DomeSpace::wild(),
                DomeSpace::normal(Blau),
                DomeSpace::normal(Gelb),
            ],
            0,
        );
        game.state.dome_display = vec![tile];
        game.state.pending_dome_choice = Some(PendingDomeChoice::FromDisplay {
            dome_tile_id: 22,
            slot_row: 0,
            slot_col: 0,
        });
        let _ = pi;
        let a = vorzug_dome_wahl(&game.state).expect("Spaltenbau muss hier eingreifen");
        match a {
            Action::ChooseDomeRotation(rot) => {
                assert_eq!(rot, 180, "Rotation 180 bringt die Wild-Zelle in die Ziel-Spalte (Offset 0)");
            }
            other => panic!("erwartet ChooseDomeRotation, bekam {other:?}"),
        }
        set_aktiv_override_for_test(None);
    }

    #[test]
    fn vorzug_dome_wahl_ignoriert_slots_ausserhalb_der_zielspalte() {
        set_aktiv_override_for_test(Some(true));
        let mut game = drafting_game(6);
        let pi = game.state.current_player;
        game.state.pending_dome_choice = Some(PendingDomeChoice::FromDisplay {
            dome_tile_id: 30,
            slot_row: 0,
            slot_col: 2, // Slot-Spalte 2 -> Rasterspalten 4/5, nicht Ziel-Spalte 0.
        });
        game.state.dome_display = vec![normal_tile(30, [Rot, Blau, Gelb, Schwarz])];
        let _ = pi;
        assert_eq!(vorzug_dome_wahl(&game.state), None);
        set_aktiv_override_for_test(None);
    }

    #[test]
    fn vorzugszug_reicht_dynamische_spalte_an_provokation_kern_durch() {
        // Direkter Vergleich: `spaltenbau::vorzugszug` muss fuer eine
        // Stellung, in der Spalte 0 Ziel ist, denselben Zug liefern wie
        // `provokation::vorzugszug_fuer_spalte(state, 0)`.
        set_aktiv_override_for_test(Some(true));
        let mut game = drafting_game(7);
        let pi = game.state.current_player;
        let tile = normal_tile(40, [Rot, Blau, Gelb, Schwarz]);
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("frei");
        // Tischmitte deterministisch leeren (Runde 3): seit die Zielspalten-
        // Kosten die oeffentliche Versorgungslage einbeziehen
        // (`spalten_kosten`/`engpass_aufschlag`), wuerde der echte
        // Zufalls-Fabrikinhalt beim Partiestart die Kosten je Farbe VERZERREN
        // -- ohne dieses Leeren waere Spalte 0 nicht mehr zuverlaessig die
        // guenstigste, die Testvoraussetzung ("Spalte 0 ist Ziel") wuerde vom
        // Seed abhaengen statt vom hier explizit gebauten Zustand.
        for f in game.state.factories.iter_mut() {
            f.sun_tiles.clear();
            f.moon_stacks.clear();
        }
        game.state.large_factory.sun_tiles.clear();
        game.state.large_factory.moon_pool.clear();
        game.state.factories[0].sun_tiles = vec![Rot, Rot];
        let erwartet = crate::provokation::vorzugszug_fuer_spalte(&game.state, 0);
        assert_eq!(vorzugszug(&game.state), erwartet);
        assert!(erwartet.is_some(), "Testvoraussetzung: es sollte ueberhaupt einen Kandidaten geben");
        set_aktiv_override_for_test(None);
    }
}
