//! E4: Angebots-Bedarfs-Abschnitt des Encoders (Trainings-Arm E4,
//! `evaluations/PREREG_evaluator_pretests.md` par.5c/par.8c,
//! `evaluations/PREREG_v34_window.md` par.3).
//!
//! FRAGE, die der Block beantwortet: welche Quelle der Auslage fuellt welche
//! Musterreihe, und zu welchem Preis? Heute muss das Netz diese Relation aus
//! den Zaehlungen der Fabriken und dem Fuellgrad der Reihen selbst bilden; der
//! Vortest (par.8c) hat gezeigt, dass der Trunk des Champions sie nur
//! teilweise traegt (alle 18 zulaessigen Paare "Luecke belegt", am
//! schwaechsten fuer die langen Reihen und fuer "genau fuellen").
//!
//! # Zuschnitt (je Spieler, Spieler am Zug zuerst, dann der Gegner)
//!
//! Je Musterreihe r = 0..5 vier Groessen, gebildet ueber ALLE Steinzuege, die
//! die Auslage gerade hergibt (jede Quelle: Sonnenseite je kleiner Fabrik,
//! Sonnenseite der grossen Fabrik, Aktion C ueber den Mondbereich):
//!
//! | Block | Groesse | Normierung |
//! | --- | --- | --- |
//! | A | groesste Steinzahl, die ein Zug OHNE Ueberlauf in die Reihe legt | / Kapazitaet der Reihe |
//! | B | ein Zug fuellt die Reihe GENAU (voll, kein Ueberlauf) | 0/1 |
//! | C | ein Zug fuellt die Reihe ueberhaupt (mit oder ohne Ueberlauf) | 0/1 |
//! | D | kleinster Ueberlauf eines Zugs, der die Reihe fuellt | min(x, 4) / 4, 0 ohne Fuellzug |
//!
//! A, B und D sind genau die drei Groessen des Vortests
//! (`tools/probes/e4_supply_demand_pretest.py::quantities`). C ist neu und
//! macht D eindeutig: der Vortest fuehrte D als NaN, wo kein Zug die Reihe
//! fuellt; im Vektor steht dort 0, und erst C trennt "fuellt ohne Ueberlauf"
//! (C=1, D=0) von "fuellt gar nicht" (C=0, D=0).
//!
//! Die Normierung von D an `board::MAX_BROKEN` (4 Strafleisten-Slots,
//! board.rs:212): mehr Ueberlauf als Slots wandert in den Turm
//! (`execution.rs::add_to_penalty`), die Kappung bei 4 haelt den Wert in
//! [0, 1].
//!
//! Gegner-Seite, obwohl der Vortest nur die EIGENEN Reihen gemessen hat: der
//! Gegner zieht als naechster, und mit dem Einpass-Konsum (E1,
//! `single_pass_other_val`) liest die Suche den Wert des Nicht-Ziehers als
//! `1 - p_zieher` aus DIESER Eingabe. Dieselbe Zugreihenfolge wie die
//! Abschnitte 5, 6, 13, 14, 16 und 17 in `features.rs`. Fuer den Gegner ist
//! es eine STATISCHE Sicht (die Auslage vor dem Zug des Ziehenden) -- genau
//! wie fuer den Ziehenden selbst.
//!
//! # Wahrheitsquelle und Kosten
//!
//! Die Folge eines Zugs ist nicht nachgebaut, sondern aus den Regelfunktionen
//! der Engine gelesen: Steinzahl der Nahme aus `mcts::tiles_taken`
//! (dieselbe Funktion, die die Stoerungs-Sonde fuer ihre Ueberlaufpruefung
//! nimmt), Zulaessigkeit aus `PatternLine::can_accept` (dieselbe Regel wie
//! `validation::validate_place`), Aufteilung Reihe/Ueberlauf wie
//! `PatternLine::add_tiles` (`n = spaces_left().min(tiles.len())`).
//!
//! Der E4-Export `lib.rs::stone_move_outcomes` fuehrt dagegen jeden legalen
//! Steinzug auf einem KLON des Zustands aus. Das ist die Wahrheitsquelle des
//! Vortests -- und als Encoder zu teuer: bis zu rund 30 Nahmen mal 7 Ziele
//! je Spieler, je ein voller `GameState`-Klon plus `execute_move` samt
//! Log-Formatierung, an JEDEM Blatt der Suche (HERLEITUNG, nicht gemessen).
//! Hier ist es eine Schleife ueber hoechstens rund 30 Nahmen mal 6 Reihen
//! mal 2 Spieler ohne einen einzigen Klon. Die Gleichheit mit dem
//! Klon-Export bewacht der Test
//! `matches_the_clone_based_export_for_both_players` (unten).
//!
//! # Warum der Block den JSON-Rueckweg nicht fuerchten muss
//!
//! `serialize::json_to_state` rekonstruiert offene Wahlen nicht
//! (`pending_dome_choice`, `pending_moon_order`, `pending_return_order`,
//! serialize.rs:1282-1292). Der Klon-Export liefert deshalb fuer Records
//! mitten in einer Wahl Steinzuege, die real nicht legal waren
//! (`PREREG_evaluator_pretests.md` par.5c, `PREREG_v34_window.md` par.3
//! "beim Encoder-Bau zu loesen"). Dieser Block liest KEINES der drei Felder:
//! er beschreibt, was die Auslage den Reihen anbietet, nicht, was in genau
//! diesem Halbzug erlaubt ist. Damit liefern Suchpfad (direkt am Zustand) und
//! Trainingspfad (ueber das Record-JSON) dieselben Werte, auch in Zustaenden
//! mit offener Wahl -- bewacht von `direct_matches_json_path_including_pending_states`.
//!
//! # Additivitaet
//!
//! Der Block ist KEIN Teil des 888er-Basisvertrags (`features::INPUT_SIZE`,
//! Vertragshash unveraendert). Er haengt nur an, wenn das MODELL ihn verlangt:
//! `features::features_for_layout` prueft die Flach-Breite des geladenen Netzes
//! gegen [`SUPPLY_DEMAND_INPUT_SIZE`]. Jedes heutige Modell (888) bekommt den
//! Block nicht einmal gerechnet.

use serde_json::Value;

use crate::moves::{TakeAction, TakeSource};
use crate::state::{GameState, Phase};
use crate::tile::TileColor;

/// Musterreihen je Spieler.
pub const SUPPLY_DEMAND_ROWS: usize = 6;

/// Groessen je Musterreihe (Bloecke A-D, siehe Modulkopf).
pub const SUPPLY_DEMAND_QUANTITIES: usize = 4;

/// Werte je Spieler.
pub const SUPPLY_DEMAND_VALUES_PER_PLAYER: usize = SUPPLY_DEMAND_ROWS * SUPPLY_DEMAND_QUANTITIES;

/// Laenge des Blocks: beide Spieler, Spieler am Zug zuerst. 2 x 6 x 4 = 48.
pub const SUPPLY_DEMAND_VALUES: usize = 2 * SUPPLY_DEMAND_VALUES_PER_PLAYER;

/// Feste Position des Blocks im Flachvektor: direkt hinter dem Basisvertrag.
///
/// BEWUSST ein Literal und nicht `features::INPUT_SIZE`: ein E4-Modell hat den
/// Block bei Index 888 gelernt. Wuerde der Basisvektor spaeter wachsen und der
/// Block mitwandern, saehe dasselbe Modell an denselben Indizes andere Werte.
/// Die Konstanten-Pruefung unten bricht den BAU, sobald `INPUT_SIZE` sich
/// bewegt -- dann ist ausdruecklich zu entscheiden, wohin neue Basiswerte und
/// wohin dieser Block gehoeren.
pub const SUPPLY_DEMAND_OFFSET: usize = 888;

/// Flach-Breite eines Modells MIT diesem Block (888 + 48 = 936).
pub const SUPPLY_DEMAND_INPUT_SIZE: usize = SUPPLY_DEMAND_OFFSET + SUPPLY_DEMAND_VALUES;

/// Kappung und Normierung des Ueberlaufs (Block D): die vier Slots der
/// Strafleiste (`board::MAX_BROKEN`).
pub const SUPPLY_DEMAND_OVERFLOW_NORM: usize = crate::board::MAX_BROKEN;

// Bau-Waechter (siehe `SUPPLY_DEMAND_OFFSET`): waechst der Basisvektor, bricht
// hier der Bau statt still die Bedeutung von Index 888.. zu verschieben.
const _: () = assert!(
    crate::features::INPUT_SIZE == SUPPLY_DEMAND_OFFSET,
    "features::INPUT_SIZE hat sich bewegt: der E4-Block (supply_demand.rs) sitzt fest bei Index 888. \
     Vor dem Weiterbauen entscheiden, ob neue Basiswerte HINTER den E4-Block gehoeren oder E4 neu \
     verankert wird (dann ist jedes E4-Modell neu zu trainieren)."
);

/// Die vier Groessen EINER Musterreihe, roh (vor der Normierung).
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct RowSupply {
    /// A: groesste Steinzahl, die ein Zug ohne Ueberlauf in die Reihe legt.
    pub max_into_no_overflow: usize,
    /// B: ein Zug fuellt die Reihe genau.
    pub fill_exact: bool,
    /// C: ein Zug fuellt die Reihe (mit oder ohne Ueberlauf).
    pub fill_possible: bool,
    /// D: kleinster Ueberlauf eines Zugs, der die Reihe fuellt; `None` ohne Fuellzug.
    pub min_overflow_fill: Option<usize>,
}

/// Gilt der Block in diesem Zustand? Nur im Drafting und nicht vor der
/// Startplatzierung -- dieselbe Grenze wie der Klon-Export
/// (`lib.rs::stone_move_outcomes`). In allen anderen Zustaenden sind alle
/// 48 Werte 0. `phase` und `start_tile_pending` (Feld `start_placed`) stehen
/// beide im Record, also gilt die Grenze in beiden Pfaden gleich.
pub fn supply_demand_applies(state: &GameState) -> bool {
    state.phase == Phase::Drafting
        && state.players.len() == 2
        && !state.players.iter().any(|p| p.start_tile_pending)
}

/// Steinzahl EINER Nahme, aus der Regel-Funktion der Engine.
fn taken(state: &GameState, source: TakeSource, factory_id: Option<usize>, color: TileColor) -> usize {
    crate::mcts::tiles_taken(state, &TakeAction { source, color, factory_id, moon_order: Vec::new() })
}

/// Alle Nahmen, die die Auslage gerade hergibt, als (Farbe, Steinzahl).
///
/// Dieselben drei Quellen wie `validation::generate_valid_moves`: Sonnenseite
/// je kleiner Fabrik, Sonnenseite der grossen Fabrik, Aktion C (globaler
/// Mondzug, `factory_id = None`). Eine Nahme ist dort genau dann erzeugt, wenn
/// die Farbe an der Quelle liegt (`sun_colors`, `available_moon_colors`) --
/// also genau dann, wenn ihre Steinzahl > 0 ist. Teil-Mondzuege aus EINER
/// Fabrik erzeugt der Generator nie (execution.rs:71-75), sie fehlen hier
/// darum auch. Nur die fuenf ziehbaren Farben: WILD ist "kein ziehbarer
/// Stein" (tile.rs:11).
///
/// Der Diagnose-Knopf `MOSAIC_PROVOKATION_SPALTE`
/// (`provocation::prune_moves`) bleibt bewusst AUSSEN vor: eine
/// Netz-Eingabe darf nicht an einem Diagnose-Schalter haengen.
pub fn take_sizes(state: &GameState) -> Vec<(TileColor, usize)> {
    let mut out: Vec<(TileColor, usize)> = Vec::with_capacity(32);
    for &color in TileColor::NORMAL.iter() {
        for f in &state.factories {
            let n = taken(state, TakeSource::SmallFactorySun, Some(f.factory_id), color);
            if n > 0 {
                out.push((color, n));
            }
        }
        let n = taken(state, TakeSource::LargeFactorySun, None, color);
        if n > 0 {
            out.push((color, n));
        }
        let n = taken(state, TakeSource::SmallFactoryMoon, None, color);
        if n > 0 {
            out.push((color, n));
        }
    }
    out
}

/// Die vier Groessen je Musterreihe von Spieler `pi` gegen die Nahmen `takes`.
///
/// Zulaessig ist eine Nahme fuer Reihe r, wenn `PatternLine::can_accept` sie
/// laesst (nicht voll, keine fremde Farbe) -- die Regel von
/// `validation::validate_place`. Die Aufteilung folgt `PatternLine::add_tiles`:
/// in die Reihe gehen `spaces_left().min(n)`, der Rest ist Ueberlauf. Die
/// Reihe ist danach voll, wenn alle freien Plaetze belegt sind.
pub fn row_supply_for_player(
    state: &GameState,
    takes: &[(TileColor, usize)],
    pi: usize,
) -> [RowSupply; SUPPLY_DEMAND_ROWS] {
    let mut out = [RowSupply::default(); SUPPLY_DEMAND_ROWS];
    let Some(player) = state.players.get(pi) else { return out };
    for (r, slot) in out.iter_mut().enumerate() {
        let Some(row) = player.pattern_lines.get(r) else { continue };
        // = `PatternLine::spaces_left` (board.rs:40), nur ohne Unterlauf-Panik
        // bei einem kaputten Zustand (mehr Steine als Kapazitaet).
        let space = row.capacity().saturating_sub(row.tiles.len());
        for &(color, n) in takes {
            if !row.can_accept(color) {
                continue;
            }
            let into = space.min(n);
            let overflow = n - into;
            if overflow == 0 && into > slot.max_into_no_overflow {
                slot.max_into_no_overflow = into;
            }
            if into == space {
                slot.fill_possible = true;
                if overflow == 0 {
                    slot.fill_exact = true;
                }
                slot.min_overflow_fill = Some(match slot.min_overflow_fill {
                    Some(m) => m.min(overflow),
                    None => overflow,
                });
            }
        }
    }
    out
}

/// Haengt die 24 Werte EINES Spielers an: Block A (6), B (6), C (6), D (6).
fn push_player_block(f: &mut Vec<f32>, state: &GameState, pi: usize, rows: &[RowSupply; SUPPLY_DEMAND_ROWS]) {
    let capacity = |r: usize| -> f32 {
        state
            .players
            .get(pi)
            .and_then(|p| p.pattern_lines.get(r))
            .map(|row| row.capacity() as f32)
            .unwrap_or(1.0)
            .max(1.0)
    };
    for (r, s) in rows.iter().enumerate() {
        f.push(s.max_into_no_overflow as f32 / capacity(r));
    }
    for s in rows {
        f.push(if s.fill_exact { 1.0 } else { 0.0 });
    }
    for s in rows {
        f.push(if s.fill_possible { 1.0 } else { 0.0 });
    }
    let norm = SUPPLY_DEMAND_OVERFLOW_NORM as f32;
    for s in rows {
        f.push(match s.min_overflow_fill {
            Some(x) => x.min(SUPPLY_DEMAND_OVERFLOW_NORM) as f32 / norm,
            None => 0.0,
        });
    }
}

/// Der Block direkt aus dem Zustand (Suchpfad, `features::features_for_layout`).
/// Immer genau [`SUPPLY_DEMAND_VALUES`] Werte.
pub fn supply_demand_values_direct(state: &GameState) -> Vec<f32> {
    let mut f: Vec<f32> = Vec::with_capacity(SUPPLY_DEMAND_VALUES);
    if !supply_demand_applies(state) {
        f.resize(SUPPLY_DEMAND_VALUES, 0.0);
        return f;
    }
    let takes = take_sizes(state);
    let curr = state.current_player.min(1);
    for pi in [curr, 1 - curr] {
        let rows = row_supply_for_player(state, &takes, pi);
        push_player_block(&mut f, state, pi, &rows);
    }
    debug_assert_eq!(f.len(), SUPPLY_DEMAND_VALUES);
    f
}

/// Der Block aus dem Record-JSON (Trainingspfad, ueber den pyo3-Export
/// `lib.rs::supply_demand_values_from_json`). Dieselbe Route wie die
/// Tiling-Projektion (`features::tiling_projection_from_json`):
/// `json_to_state` mit festem Seed 0; der RNG mischt nur verdeckte Bestaende
/// (Beutel, Kuppelstapel, Chips), die dieser Block nicht liest.
///
/// Scheitert die Rekonstruktion (Alt-Schnappschuss ohne Pflichtfeld), sind
/// alle 48 Werte 0 -- dieselbe Toleranz wie Abschnitt 17.
pub fn supply_demand_values_from_json(v: &Value) -> Vec<f32> {
    use rand::rngs::StdRng;
    use rand::SeedableRng;
    let mut rng = StdRng::seed_from_u64(0);
    match crate::serialize::json_to_state(v, &mut rng) {
        Ok(state) => supply_demand_values_direct(&state),
        Err(_) => vec![0.0; SUPPLY_DEMAND_VALUES],
    }
}

/// Verlangt ein Modell mit dieser Flach-Breite den Block?
///
/// `>=` und nicht `>`: eine Breite zwischen 888 und 936 waere ein kaputtes
/// Modell; sie bekommt den Block NICHT und scheitert dann laut an der
/// Tensorform (`net.rs::build_inputs`), statt still einen angeschnittenen
/// Block zu sehen.
pub fn supply_demand_wanted(flat_width: usize) -> bool {
    flat_width >= SUPPLY_DEMAND_INPUT_SIZE
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::board::PatternLine;
    use crate::game::{drafting_actions, Game};
    use crate::serialize::state_to_json;
    use crate::state::setup_new_game;
    use rand::rngs::StdRng;
    use rand::seq::IndexedRandom;
    use rand::SeedableRng;

    /// Zufallspartie wie `features.rs::tests::random_drafting_states`, aber
    /// MIT dem Zustand vor dem ersten Zug und ohne Vorauswahl: auch Zustaende
    /// mitten in einer Kuppel- oder Stapelwahl werden gesammelt.
    fn random_drafting_states(seed: u64, steps: usize) -> Vec<GameState> {
        let mut rng = StdRng::seed_from_u64(seed);
        let mut game = Game { state: setup_new_game(["P1".into(), "P2".into()], 0, &mut rng) };
        for p in game.state.players.iter_mut() {
            p.start_tile_pending = false;
        }
        let mut out = vec![game.state.clone()];
        for _ in 0..steps {
            if game.state.phase != Phase::Drafting {
                break;
            }
            let actions = drafting_actions(&game.state);
            if actions.is_empty() {
                break;
            }
            let action = actions.choose(&mut rng).unwrap().clone();
            if game.apply_drafting(&action).is_err() {
                break;
            }
            out.push(game.state.clone());
        }
        out
    }

    fn has_open_choice(s: &GameState) -> bool {
        s.pending_dome_choice.is_some()
            || !s.pending_stack_draw.is_empty()
            || s.pending_moon_order.is_some()
            || s.pending_return_order.is_some()
    }

    /// Die Vortest-Groessen aus der Ausgabe des Klon-Exports, Zeile fuer
    /// Zeile wie `tools/probes/e4_supply_demand_pretest.py::quantities`, plus C.
    fn pretest_quantities(outcomes: &[serde_json::Value]) -> [RowSupply; SUPPLY_DEMAND_ROWS] {
        let mut out = [RowSupply::default(); SUPPLY_DEMAND_ROWS];
        for (r, slot) in out.iter_mut().enumerate() {
            let mv: Vec<&serde_json::Value> =
                outcomes.iter().filter(|o| o["row"].as_i64() == Some(r as i64)).collect();
            slot.max_into_no_overflow = mv
                .iter()
                .filter(|o| o["overflow_to_floor"].as_u64() == Some(0))
                .map(|o| o["tiles_into_row"].as_u64().unwrap() as usize)
                .max()
                .unwrap_or(0);
            let fills: Vec<&&serde_json::Value> =
                mv.iter().filter(|o| o["row_full_after"].as_bool() == Some(true)).collect();
            slot.fill_possible = !fills.is_empty();
            slot.fill_exact = fills.iter().any(|o| o["overflow_to_floor"].as_u64() == Some(0));
            slot.min_overflow_fill =
                fills.iter().map(|o| o["overflow_to_floor"].as_u64().unwrap() as usize).min();
        }
        out
    }

    /// WAHRHEITSQUELLE: auf jedem Zustand OHNE offene Wahl stimmen die vier
    /// Groessen mit dem Klon-Export ueberein (jeder legale Steinzug auf einem
    /// Klon ausgefuehrt) -- fuer den Ziehenden direkt, fuer den Gegner auf
    /// einem Klon mit umgesetztem `current_player`.
    #[test]
    fn matches_the_clone_based_export_for_both_players() {
        let mut checked = 0usize;
        let mut saw_fill_exact = false;
        let mut saw_overflow_fill = false;
        for seed in 0..10u64 {
            for (i, s) in random_drafting_states(seed, 50).into_iter().enumerate() {
                if !supply_demand_applies(&s) || has_open_choice(&s) {
                    continue;
                }
                let takes = take_sizes(&s);
                for pi in [s.current_player, 1 - s.current_player] {
                    let mut probe = s.clone();
                    probe.current_player = pi;
                    let want = pretest_quantities(&crate::stone_move_outcomes(&probe));
                    let got = row_supply_for_player(&s, &takes, pi);
                    assert_eq!(got, want, "seed={seed} step={i} Spieler {pi}: weicht vom Klon-Export ab");
                    for r in &got {
                        saw_fill_exact |= r.fill_exact;
                        saw_overflow_fill |= r.min_overflow_fill.map_or(false, |x| x > 0);
                    }
                }
                checked += 1;
            }
        }
        assert!(checked >= 200, "nur {checked} Zustaende geprueft, >= 200 gefordert");
        assert!(saw_fill_exact, "kein einziger Zustand mit genauer Fuellung -- leer gruen");
        assert!(saw_overflow_fill, "kein einziger Fuellzug mit Ueberlauf -- leer gruen");
    }

    /// Suchpfad und Trainingspfad liefern Wert fuer Wert dasselbe, AUCH in
    /// Zustaenden mitten in einer Wahl (die der JSON-Rueckweg nicht
    /// rekonstruiert). Genau das ist der Punkt, an dem der Klon-Export
    /// auseinanderlaufen wuerde.
    #[test]
    fn direct_matches_json_path_including_pending_states() {
        let mut checked = 0usize;
        let mut pending = 0usize;
        // 12 statt 10 Seeds: Partien enden oft vor 60 Drafting-Schritten, 10 Seeds ergaben
        // gemessen 290 Zustaende (erster Lauf 2026-10-02), knapp unter der Mindestzahl.
        for seed in 0..12u64 {
            for (i, s) in random_drafting_states(seed, 60).into_iter().enumerate() {
                let direct = supply_demand_values_direct(&s);
                let via_json = supply_demand_values_from_json(&state_to_json(&s, true));
                assert_eq!(direct.len(), SUPPLY_DEMAND_VALUES, "seed={seed} step={i}: Laenge");
                assert_eq!(direct, via_json, "seed={seed} step={i}: direkter Pfad weicht vom JSON-Pfad ab");
                if has_open_choice(&s) {
                    pending += 1;
                }
                checked += 1;
            }
        }
        assert!(checked >= 300, "nur {checked} Zustaende geprueft, >= 300 gefordert");
        assert!(pending > 0, "kein Zustand mit offener Wahl -- der heikle Fall ist ungeprueft");
    }

    /// Wertebereich: jeder Wert liegt in [0, 1], B und C sind 0/1, und B
    /// impliziert C (genau fuellen ist ein Fuellen).
    #[test]
    fn values_are_normalised_and_consistent() {
        for seed in 0..6u64 {
            for (i, s) in random_drafting_states(seed, 50).into_iter().enumerate() {
                let f = supply_demand_values_direct(&s);
                for (k, v) in f.iter().enumerate() {
                    assert!((0.0..=1.0).contains(v), "seed={seed} step={i}: Wert #{k} = {v} ausserhalb [0, 1]");
                }
                for p in 0..2 {
                    let base = p * SUPPLY_DEMAND_VALUES_PER_PLAYER;
                    for r in 0..SUPPLY_DEMAND_ROWS {
                        let b = f[base + SUPPLY_DEMAND_ROWS + r];
                        let c = f[base + 2 * SUPPLY_DEMAND_ROWS + r];
                        let d = f[base + 3 * SUPPLY_DEMAND_ROWS + r];
                        assert!(b == 0.0 || b == 1.0, "B nicht binaer");
                        assert!(c == 0.0 || c == 1.0, "C nicht binaer");
                        assert!(b <= c, "seed={seed} step={i}: genau fuellen ohne fuellen");
                        if c == 0.0 {
                            assert_eq!(d, 0.0, "D ohne Fuellzug muss 0 sein");
                        }
                        if b == 1.0 {
                            assert_eq!(d, 0.0, "genau fuellen heisst kleinster Ueberlauf 0");
                        }
                    }
                }
            }
        }
    }

    /// Ausserhalb des Drafting (und vor der Startplatzierung) ist der Block 0.
    #[test]
    fn zero_outside_drafting_and_before_start_placement() {
        let leaf = crate::round_transition::drive_to_first_round_end(51);
        assert_ne!(leaf.phase, Phase::Drafting);
        assert_eq!(supply_demand_values_direct(&leaf), vec![0.0f32; SUPPLY_DEMAND_VALUES]);

        let mut rng = StdRng::seed_from_u64(3);
        let fresh = setup_new_game(["P1".into(), "P2".into()], 0, &mut rng);
        if fresh.players.iter().any(|p| p.start_tile_pending) {
            assert_eq!(supply_demand_values_direct(&fresh), vec![0.0f32; SUPPLY_DEMAND_VALUES]);
        }
    }

    /// Von Hand nachgerechnetes Brett: genau eine Quelle (Fabrik 0, Sonne
    /// Blau x3 + Rot x1), alles andere leer.
    ///
    /// Spieler 0 (am Zug): Reihe 2 (Kap. 3) traegt ein Blau, sonst leer.
    /// Spieler 1: Reihe 1 (Kap. 2) traegt ein Rot, Reihe 3 ist voll, sonst leer.
    ///
    /// Nahmen: (Blau, 3), (Rot, 1).
    #[test]
    fn known_board_by_hand() {
        let mut rng = StdRng::seed_from_u64(17);
        let mut s = setup_new_game(["P0".into(), "P1".into()], 0, &mut rng);
        for p in s.players.iter_mut() {
            p.start_tile_pending = false;
            p.pattern_lines = (0..6).map(PatternLine::new).collect();
        }
        s.phase = Phase::Drafting;
        s.current_player = 0;
        for f in s.factories.iter_mut() {
            f.sun_tiles.clear();
            f.moon_stacks.clear();
        }
        s.large_factory.sun_tiles.clear();
        s.large_factory.moon_pool.clear();
        s.factories[0].sun_tiles = vec![TileColor::Blau, TileColor::Blau, TileColor::Blau, TileColor::Rot];
        s.players[0].pattern_lines[2].tiles = vec![TileColor::Blau];
        s.players[0].pattern_lines[2].color = Some(TileColor::Blau);
        s.players[1].pattern_lines[1].tiles = vec![TileColor::Rot];
        s.players[1].pattern_lines[1].color = Some(TileColor::Rot);
        s.players[1].pattern_lines[3].tiles = vec![TileColor::Gelb; 4];
        s.players[1].pattern_lines[3].color = Some(TileColor::Gelb);

        let takes = take_sizes(&s);
        assert_eq!(takes, vec![(TileColor::Blau, 3), (TileColor::Rot, 1)]);

        // Spieler 0. Reihe 0 (Kap. 1): Blau 1+2, Rot 1+0 -> A=1, B, C, D=0.
        // Reihe 1 (Kap. 2): Blau 2+1 (voll), Rot 1+0 -> A=1, B nein, C, D=1.
        // Reihe 2 (Kap. 3, ein Blau): nur Blau, 2+1 (voll) -> A=0, B nein, C, D=1.
        // Reihe 3 (Kap. 4): Blau 3+0, Rot 1+0 -> A=3, kein Fuellzug.
        // Reihen 4/5: wie Reihe 3.
        let p0 = row_supply_for_player(&s, &takes, 0);
        let want0 = [
            RowSupply { max_into_no_overflow: 1, fill_exact: true, fill_possible: true, min_overflow_fill: Some(0) },
            RowSupply { max_into_no_overflow: 1, fill_exact: false, fill_possible: true, min_overflow_fill: Some(1) },
            RowSupply { max_into_no_overflow: 0, fill_exact: false, fill_possible: true, min_overflow_fill: Some(1) },
            RowSupply { max_into_no_overflow: 3, fill_exact: false, fill_possible: false, min_overflow_fill: None },
            RowSupply { max_into_no_overflow: 3, fill_exact: false, fill_possible: false, min_overflow_fill: None },
            RowSupply { max_into_no_overflow: 3, fill_exact: false, fill_possible: false, min_overflow_fill: None },
        ];
        assert_eq!(p0, want0);

        // Spieler 1. Reihe 0: wie oben. Reihe 1 (Kap. 2, ein Rot): nur Rot,
        // 1+0 (voll) -> A=1, B, C, D=0. Reihe 2 (Kap. 3, leer): Blau 3+0
        // (voll), Rot 1+0 -> A=3, B, C, D=0. Reihe 3 voll -> alles 0.
        let p1 = row_supply_for_player(&s, &takes, 1);
        assert_eq!(p1[0], want0[0]);
        assert_eq!(
            p1[1],
            RowSupply { max_into_no_overflow: 1, fill_exact: true, fill_possible: true, min_overflow_fill: Some(0) }
        );
        assert_eq!(
            p1[2],
            RowSupply { max_into_no_overflow: 3, fill_exact: true, fill_possible: true, min_overflow_fill: Some(0) }
        );
        assert_eq!(p1[3], RowSupply::default());

        // Normierte Werte von Spieler 0 (Block A durch die Kapazitaet).
        let f = supply_demand_values_direct(&s);
        let want_a: [f32; 6] = [1.0, 0.5, 0.0, 0.75, 0.6, 0.5];
        let want_b: [f32; 6] = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0];
        let want_c: [f32; 6] = [1.0, 1.0, 1.0, 0.0, 0.0, 0.0];
        let want_d: [f32; 6] = [0.0, 0.25, 0.25, 0.0, 0.0, 0.0];
        assert_eq!(&f[0..6], &want_a[..]);
        assert_eq!(&f[6..12], &want_b[..]);
        assert_eq!(&f[12..18], &want_c[..]);
        assert_eq!(&f[18..24], &want_d[..]);
        // Gegner-Block beginnt bei 24, Block A: Reihe 2 = 3/3.
        assert_eq!(f[24 + 2], 1.0f32);

        // Und dieselben Zahlen ueber den Klon-Export (Wahrheitsquelle).
        assert_eq!(pretest_quantities(&crate::stone_move_outcomes(&s)), want0);
    }

    /// Ueberlauf ueber die vier Strafleisten-Slots hinaus wird bei 4 gekappt.
    #[test]
    fn overflow_is_capped_at_the_floor_slots() {
        let mut rng = StdRng::seed_from_u64(5);
        let mut s = setup_new_game(["P0".into(), "P1".into()], 0, &mut rng);
        for p in s.players.iter_mut() {
            p.start_tile_pending = false;
            p.pattern_lines = (0..6).map(PatternLine::new).collect();
        }
        s.phase = Phase::Drafting;
        s.current_player = 0;
        for f in s.factories.iter_mut() {
            f.sun_tiles.clear();
            f.moon_stacks.clear();
        }
        s.large_factory.moon_pool.clear();
        // Sieben Schwarz in der grossen Fabrik: Reihe 0 nimmt 1, Ueberlauf 6.
        s.large_factory.sun_tiles = vec![TileColor::Schwarz; 7];
        let rows = row_supply_for_player(&s, &take_sizes(&s), 0);
        assert_eq!(rows[0].min_overflow_fill, Some(6));
        let f = supply_demand_values_direct(&s);
        assert_eq!(f[3 * SUPPLY_DEMAND_ROWS], 1.0f32, "6 Steine Ueberlauf -> gekappt auf 4/4");
    }

    #[test]
    fn layout_constants() {
        assert_eq!(SUPPLY_DEMAND_VALUES, 48);
        assert_eq!(SUPPLY_DEMAND_INPUT_SIZE, 936);
        assert_eq!(SUPPLY_DEMAND_OFFSET, crate::features::INPUT_SIZE);
        assert!(!supply_demand_wanted(crate::features::INPUT_SIZE));
        assert!(!supply_demand_wanted(SUPPLY_DEMAND_INPUT_SIZE - 1));
        assert!(supply_demand_wanted(SUPPLY_DEMAND_INPUT_SIZE));
    }
}
