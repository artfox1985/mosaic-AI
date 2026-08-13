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

fn ist_aktiv() -> bool {
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
///  - Wild/Special -- keine Farbbindung, billig.
///  - Normal, ungefuellt: billig, wenn die Musterreihe leer ist (offen) oder
///    schon GENAU die geforderte Farbe fuehrt; teuer, wenn sie an eine ANDERE
///    Farbe gebunden ist (diese Runde fuer diese Zeile blockiert -- Nutzer-
///    Vorgabe "schon gefuellte Zellen"/"Farbforderungen" einbeziehen).
///
/// Rein additiv aus dem Brett ablesbar (`dome_grid`/`pattern_lines`), keine
/// Suche, kein Blick in Fabriken/Beutel -- daher in O(6) je Spalte.
fn spalten_kosten(player: &PlayerBoard, spalte: usize) -> f64 {
    let mut kosten = 0.0;
    for r in 0..6usize {
        kosten += match player.dome_grid.get_space(r, spalte) {
            None => 1.0,
            Some(sp) if sp.is_filled() => 0.0,
            Some(sp) => match sp.space_type {
                SpaceType::Wild => 0.2,
                SpaceType::Special => 0.3,
                SpaceType::Normal => {
                    let need = sp.required_color;
                    match (player.pattern_lines[r].color, need) {
                        (None, _) => 1.0,
                        (Some(c), Some(x)) if c == x => 0.3,
                        _ => 2.0,
                    }
                }
            },
        };
    }
    kosten
}

/// Leichteste Spalte fuer den AKTIVEN Spieler -- frisch aus `state`
/// berechnet, KEIN gespeicherter Zustand. Genau dadurch "erlaubt" die
/// Funktion einen Wechsel, wenn die bisherige Ziel-Spalte unbedienbar wird
/// (Nutzer-Vorgabe): der naechste Aufruf sieht den neuen Brettzustand und
/// kann eine andere Spalte liefern, ohne dass irgendwo ein Flag geloescht
/// werden muesste (kein Leck-Risiko wie bei
/// `provokation::AUTO_SPALTE`/`set_ziel_spalte_seed`).
///
/// Bei Gleichstand gewinnt die KLEINERE Spaltennummer (stabile, deterministische
/// Wahl -- `<` statt `<=` beim Vergleich).
pub(crate) fn ziel_spalte(state: &GameState) -> Option<usize> {
    if !ist_aktiv() {
        return None;
    }
    let player = &state.players[state.current_player];
    let mut best: Option<(f64, usize)> = None;
    for c in 0..6usize {
        let k = spalten_kosten(player, c);
        best = match best {
            None => Some((k, c)),
            Some((bk, _)) if k < bk => Some((k, c)),
            other => other,
        };
    }
    best.map(|(_, c)| c)
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
    let spalte = {
        let player = &state.players[pi];
        let mut best: Option<(f64, usize)> = None;
        for c in 0..6usize {
            let k = spalten_kosten(player, c);
            best = match best {
                None => Some((k, c)),
                Some((bk, _)) if k < bk => Some((k, c)),
                other => other,
            };
        }
        best.map(|(_, c)| c)
    }?;
    crate::tiling_solver::vorzug_tiling_step_fuer_spalte(state, pi, spalte)
}

// ── Hauptaufgabe 1: Kuppelplatten-Wahl steuert required_color ──────────────

/// Wie gut bedient `space` (bereits an Zeile `r` haengend gedacht) die
/// Ziel-Spalte, bevor die Platte ueberhaupt liegt? Wild/Special sind immer
/// gut (keine Farbbindung noetig); eine Normal-Farbe ist gut, wenn die
/// Musterreihe `r` schon leer ist oder GENAU diese Farbe fuehrt, und
/// ungeeignet (0), wenn die Reihe an eine andere Farbe gebunden ist.
fn zellen_wert(player: &PlayerBoard, r: usize, space: &DomeSpace) -> f64 {
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
        let k_wild_spalte = spalten_kosten(&game.state.players[pi], 0);
        let k_normal_spalte = spalten_kosten(&game.state.players[pi], 1);
        assert!(
            k_wild_spalte < k_normal_spalte,
            "Spalte mit Wild-Zelle (0) muss billiger sein als Spalte mit gebundener Normal-Zelle (1): {k_wild_spalte} vs {k_normal_spalte}"
        );
        set_aktiv_override_for_test(None);
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
        game.state.factories[0].sun_tiles = vec![Rot, Rot];
        let erwartet = crate::provokation::vorzugszug_fuer_spalte(&game.state, 0);
        assert_eq!(vorzugszug(&game.state), erwartet);
        assert!(erwartet.is_some(), "Testvoraussetzung: es sollte ueberhaupt einen Kandidaten geben");
        set_aktiv_override_for_test(None);
    }
}
