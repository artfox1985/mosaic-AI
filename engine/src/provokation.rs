//! Spalten-Provokation (Diagnose-Knopf `MOSAIC_PROVOKATION_SPALTE`) --
//! Beschneidung der Drafting-Aktionsmenge auf eine Ziel-Spalte, damit die
//! Suche ein Spiel plant, das gezielt auf eine geschlossene Wertungsplatten-
//! Spalte hinarbeitet. Siehe `evaluations/PREREG_provokation.md` §4 (der
//! Eingriff) fuer die volle Begruendung, warum das ueber eine
//! Aktionsmengen-Beschneidung geht und NICHT ueber einen neuen Bewerter
//! (fuenf Anlaeufe gescheitert: `PREREG_platzierungsseite.md` §7-14,
//! `PREREG_injektion_wertungsplatten.md`).
//!
//! DIAGNOSE-KNOPF, KEIN SPIELPARAMETER (Muster: `MOSAIC_VOLLE_VERSORGUNG`,
//! `state.rs::volle_versorgung`). Default AUS -> [`beschneide_moves`] ist ein
//! No-Op, `validation::generate_valid_moves` bleibt byte-identisch zum
//! Bestand. Eine mit gesetztem Knopf gespielte Partie ist NICHT regelkonform
//! im Sinne eines freien Spiels (eine Seite plant mit einer verkleinerten
//! Aktionsmenge) -- sie darf DESHALB NIE in ein Gating geraten (waere keine
//! faire Staerkemessung, eine Seite haette von vornherein weniger Optionen).
//! In einen TRAININGSKORPUS darf sie dagegen: die Ownership-Ziele sind die
//! realisierten Endzustands-Feldlabels, und die sind bei JEDER Steuerung
//! (auch mit Beschneidung) korrekt -- es aendert sich nur die
//! Zustandsverteilung, aus der gelernt wird (gleiche Begruendung wie
//! `net_mcts::set_partie_shaping_weight`/`MOSAIC_WERTUNG_STREUUNG_MAX`).

use crate::board::PlayerBoard;
use crate::dome::SpaceType;
use crate::moves::Move;
use crate::state::GameState;
use crate::tile::TileColor;

/// Aufgeloester Beschneidungsmodus aus `MOSAIC_PROVOKATION_SPALTE`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum Modus {
    /// Env-Var fehlt/leer -- Beschneidung aus, Bestandsverhalten.
    Aus,
    /// Env-Var ist eine Ziffer 0..=5 -- feste Ziel-Spalte fuer den gesamten Prozess.
    Fest(usize),
    /// Env-Var ist `"auto"` -- Ziel-Spalte wird je Partie aus dem Partie-Seed
    /// abgeleitet, siehe [`set_ziel_spalte_seed`]/[`spalte_aus_seed`]. Ohne
    /// einen per Aufruf gesetzten Seed ist dieser Modus wirkungslos (kein
    /// Rateweg) -- `ziel_spalte()` liefert dann `None`.
    Auto,
}

/// Liest `MOSAIC_PROVOKATION_SPALTE` einmalig (Prozess-Cache, gleiches Muster
/// wie `net_mcts::read_f64_env`/`state::volle_versorgung`). Ungueltiger Wert
/// (weder Ziffer 0..5 noch `"auto"`) -> einmalige Warnung + `Aus` (kein Panic,
/// Laufzeit-Konfiguration darf einen Prozess nie abstuerzen lassen).
fn modus_env() -> Modus {
    static CELL: std::sync::OnceLock<Modus> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| match std::env::var("MOSAIC_PROVOKATION_SPALTE") {
        Err(_) => Modus::Aus,
        Ok(raw) => {
            let v = raw.trim();
            if v.is_empty() {
                Modus::Aus
            } else if v.eq_ignore_ascii_case("auto") {
                Modus::Auto
            } else {
                match v.parse::<usize>() {
                    Ok(c) if c <= 5 => Modus::Fest(c),
                    _ => {
                        eprintln!(
                            "WARNUNG: MOSAIC_PROVOKATION_SPALTE={raw:?} ungueltig \
                             (erwartet eine Ziffer 0..5 oder \"auto\") -- Beschneidung bleibt AUS."
                        );
                        Modus::Aus
                    }
                }
            }
        }
    })
}

// Test-Override -- gleiches Muster wie `tiling_solver::STATS_OVERRIDE`/
// `CACHE_OVERRIDE` bzw. `net_mcts::ROOT_CHILD_Q_OVERRIDE`: verhindert, dass
// EIN Test per `std::env::set_var` + der obigen `OnceLock` den Modus fuer ALLE
// parallel laufenden `cargo test`-Threads festlegt. Nur unter `#[cfg(test)]`
// kompiliert.
#[cfg(test)]
thread_local! {
    static MODUS_OVERRIDE: std::cell::Cell<Option<Modus>> = const { std::cell::Cell::new(None) };
}

/// Setzt (oder loescht mit `None`) den Beschneidungsmodus fuer DIESEN Thread,
/// nur in Tests. Aufrufer MUSS am Testende mit `None` zuruecksetzen, sonst
/// leckt der Wert in den naechsten Test auf demselben Worker-Thread (`cargo
/// test` recycelt Threads).
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
    /// Pro-Partie aus dem Partie-Seed aufgeloeste Ziel-Spalte fuer den
    /// `Auto`-Modus, in DIESEM Thread. `None` = nicht gesetzt.
    static AUTO_SPALTE: std::cell::Cell<Option<usize>> = const { std::cell::Cell::new(None) };
}

/// Setzt (oder loescht mit `None`) die pro-Partie aufgeloeste Ziel-Spalte fuer
/// `MOSAIC_PROVOKATION_SPALTE=auto` in DIESEM Thread -- Muster identisch zu
/// `net_mcts::set_partie_shaping_weight` (Self-Play spielt mehrere Partien
/// GLEICHZEITIG in Threads; ein prozessweiter Wert waere fuer alle Partien
/// gleich, die Streuung entstuende gar nicht). Wirkt NUR im Modus `Auto`; in
/// `Aus`/`Fest` ist der Aufruf folgenlos (aber harmlos).
///
/// STUFE-1/STUFE-2-HINWEIS: diese Funktion ist gebaut und getestet, aber
/// bewusst NIRGENDS aus einem Self-Play-Einstieg heraus aufgerufen --
/// `PREREG_provokation.md` §6 haelt Stufe 1 (diese Datei) ausdruecklich VOR
/// Stufe 2 (Verdrahtung ins Self-Play), bis Stufe 1 ihre Abnahmezahl hat.
///
/// Aufrufer MUSS am Partieende mit `None` zuruecksetzen, sonst leckt der Wert
/// in die naechste Partie desselben Threads.
// Bewusst unverdrahtete Stufe-2-API (PREREG_provokation §6: bleibt unbenutzt,
// bis Stufe 1 ihre Zahl hat) -- kein toter Rest, sondern vorbereiteter Baustein.
#[allow(dead_code)]
pub(crate) fn set_ziel_spalte_seed(seed: Option<u64>) {
    AUTO_SPALTE.with(|c| c.set(seed.map(spalte_aus_seed)));
}

/// Deterministische Ableitung Ziel-Spalte 0..=5 aus dem Partie-Seed -- gleiche
/// SplitMix64-Mischung wie `net_mcts::partie_gewicht_aus_seed` (dort
/// kontinuierlich in `[0,max]`, hier ein Index; siehe dortige Begruendung,
/// warum die Mischung noetig ist: aufeinanderfolgende Partie-Seeds im
/// Self-Play unterscheiden sich oft nur in den unteren Bits).
#[allow(dead_code)]
fn spalte_aus_seed(seed: u64) -> usize {
    let mut z = seed.wrapping_add(0x9E37_79B9_7F4A_7C15);
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^= z >> 31;
    (z % 6) as usize
}

/// Aktive Ziel-Spalte fuer die aktuelle Partie in DIESEM Thread, oder `None`
/// = Beschneidung aus (Bestandsverhalten -- Default).
fn ziel_spalte() -> Option<usize> {
    match modus() {
        Modus::Aus => None,
        Modus::Fest(c) => Some(c),
        Modus::Auto => AUTO_SPALTE.with(|c| c.get()),
    }
}

/// Geforderte Farbe der Zelle `(row_idx, spalte)` -- `None`, wenn dort kein
/// Slot liegt oder die Zelle Wild/Special ist (beide `required_color: None`,
/// `dome.rs::DomeSpace::{wild,special}`), also keine Farbforderung, die
/// beschneiden koennte. Rasterabbildung: `DomeGrid::get_space`/
/// `cell_to_dome_space` (board.rs:98, getestet board.rs:417-422) --
/// Musterreihe `row_idx` speist Rasterreihe `row_idx` 1:1 (geprueft
/// scoring.rs:416-422, deckungsgleich mit `round_end::
/// row_has_open_matching_slot`s `dome_row=r/2,space_row=r%2`).
pub(crate) fn geforderte_farbe(player: &PlayerBoard, row_idx: usize, spalte: usize) -> Option<TileColor> {
    player.dome_grid.get_space(row_idx, spalte).and_then(|s| s.required_color)
}

/// Beschneidet `moves` (Stein-Zuege des aktiven Spielers, siehe
/// `validation::generate_valid_moves`) auf die aktive Ziel-Spalte, falls eine
/// gesetzt ist: eine Platzierung in Musterreihe `r` (0..=5) faellt raus, wenn
/// Zelle `(r, spalte)` eine andere Farbe fordert als `m.take.color`.
/// Bodenzuege (`row_index == -1`, Strafleiste) sind IMMER erlaubt und werden
/// nie geprueft (Nutzer-Vorgabe).
///
/// UNVERHANDELBARE BEDINGUNG (Nutzer-Vorgabe): bleibt nach der Beschneidung
/// nichts uebrig, gilt die UNBESCHNITTENE Menge -- expliziter Fallback hier,
/// nicht als Nebeneffekt. Daraus folgt die Invariante
/// `ergebnis.is_empty() == moves.is_empty()` FUER JEDEN Modus/Zustand --
/// `game::current_player_can_move` (game.rs:441) prueft `generate_valid_
/// moves` u.a. genau auf Leerheit (Teil der Rundenabschluss-Erkennung) und
/// verlaesst sich darauf, dass die Beschneidung diese Leerheit nie
/// veraendert.
pub(crate) fn beschneide_moves(state: &GameState, moves: Vec<Move>) -> Vec<Move> {
    let Some(spalte) = ziel_spalte() else {
        return moves; // Default aus -- byte-identisch zum Bestand.
    };
    let player = &state.players[state.current_player];
    let pruned: Vec<Move> = moves
        .iter()
        .filter(|m| match m.place.row_index {
            -1 => true, // Bodenzug: nie beschnitten (Nutzer-Vorgabe).
            r if (0..=5).contains(&r) => match geforderte_farbe(player, r as usize, spalte) {
                Some(x) => x == m.take.color,
                None => true, // kein Slot / Wild / Special -- keine Forderung.
            },
            _ => true, // defensiv; ROW_INDICES (validation.rs) kennt nur -1..=5.
        })
        .cloned()
        .collect();
    // VERFEINERUNG (PREREG_provokation.md §7 Punkt 2, gemessen begruendet):
    // die erste Fassung liess Bodenzuege immer durch und band alles andere --
    // blieb nach der Beschneidung nur noch die Strafleiste als Ziel, galt die
    // Menge trotzdem als "nicht leer" und der Fallback griff nie. Ergebnis war
    // eine Strafleiste von bis zu 23 (gegen 9,35 im Bezug) bei unveraenderten
    // 3-4 Spaltenabschluessen: die Bindung erzwang unplatzierbare Fliesen,
    // statt die Spalte zu schliessen.
    //
    // Jetzt gilt: gebunden wird nur, solange nach der Beschneidung ein
    // NICHT-Bodenzug uebrig bleibt. Gibt es die geforderte Farbe gerade nicht
    // als echte Platzierung, laesst die Bindung fuer DIESE Entscheidung los
    // (volle Menge) und greift bei der naechsten wieder -- opportunistisches
    // Binden statt totalem Zwang, wie es menschliche Spieler tun.
    let hat_echten_zug = pruned.iter().any(|m| m.place.row_index != -1);
    if pruned.is_empty() || !hat_echten_zug {
        moves // Fallback: nie leer, und nie NUR Strafleiste.
    } else {
        pruned
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dome::{DomeSpace, DomeTile};
    use crate::moves::{PlaceAction, TakeAction, TakeSource};
    use crate::tile::TileColor::*;
    use crate::validation::generate_valid_moves;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    fn names() -> [String; 2] {
        ["P1".into(), "P2".into()]
    }

    /// Baut ein spielbares Drafting-`GameState` (Startkuppel-Pflicht schon
    /// erledigt), Muster aus `game.rs`-Tests (`apply_drafting_blocked_while_
    /// start_tile_pending` etc.).
    fn drafting_game(seed: u64) -> crate::game::Game {
        let mut rng = StdRng::seed_from_u64(seed);
        let mut game = crate::game::Game::start(names(), 0, vec![0, 1, 2], &mut rng);
        for p in game.state.players.iter_mut() {
            p.start_tile_pending = false;
        }
        game
    }

    /// Testkachel mit 4 NORMAL-Spaces (keine Wild/Special -- fuer diesen Test
    /// irrelevant, `DomeTile::new` verlangt nur Laenge 4). Layout: [0][1] /
    /// [2][3].
    fn normal_tile(id: usize, colors: [TileColor; 4]) -> DomeTile {
        DomeTile::new(id, colors.into_iter().map(DomeSpace::normal).collect(), 0)
    }

    fn stone_move(color: TileColor, row_index: i32) -> Move {
        Move {
            take: TakeAction {
                source: TakeSource::SmallFactorySun,
                color,
                factory_id: Some(1),
                moon_order: Vec::new(),
            },
            place: PlaceAction { row_index },
        }
    }

    #[test]
    fn default_aus_ist_identitaet_auch_bei_konfliktfaehigen_zuegen() {
        // Test 1 (Pflicht): ungesetzter Knopf -> Aktionsmenge unveraendert --
        // hier direkt an `beschneide_moves` gezeigt, mit Zuegen, die bei
        // AKTIVER Beschneidung durchaus rausfallen wuerden (Kontrastprobe:
        // Aus ist nicht "zufaellig kein Konflikt", sondern echtes No-Op).
        set_modus_override_for_test(Some(Modus::Aus));
        for seed in [1u64, 2, 3, 4, 5] {
            let mut game = drafting_game(seed);
            let tile = normal_tile(0, [Rot, Blau, Gelb, Schwarz]);
            game.state.players[game.state.current_player]
                .dome_grid
                .place_dome_tile(tile, 0, 0)
                .expect("Slot (0,0) ist frei");
            let raw = vec![stone_move(Blau, 0), stone_move(Rot, 0), stone_move(Gelb, -1)];
            let out = beschneide_moves(&game.state, raw.clone());
            assert_eq!(out, raw, "Seed {seed}: Modus::Aus darf die Menge nicht veraendern");
        }
        set_modus_override_for_test(None);
    }

    #[test]
    fn beschneidung_entfernt_falsche_farbe_in_geforderter_reihe() {
        // Test 2 (Pflicht): bei gesetzter Ziel-Spalte faellt eine falsche
        // Farbe in der geforderten Musterreihe raus, die Bodenzug-Variante
        // UND die passende Farbe bleiben.
        set_modus_override_for_test(Some(Modus::Fest(0)));
        let mut game = drafting_game(11);
        // Slot (0,0): si=0 -> Rasterzelle (row=0,col=0) fordert Rot;
        // si=2 -> (row=1,col=0) fordert Gelb (cell_to_dome_space, board.rs:98).
        let tile = normal_tile(1, [Rot, Blau, Gelb, Schwarz]);
        game.state.players[game.state.current_player]
            .dome_grid
            .place_dome_tile(tile, 0, 0)
            .expect("Slot (0,0) ist frei");

        let raw = vec![
            stone_move(Blau, 0),  // Musterreihe 0, falsche Farbe -> muss raus
            stone_move(Rot, 0),   // Musterreihe 0, richtige Farbe -> bleibt
            stone_move(Blau, -1), // Bodenzug -> bleibt IMMER
        ];
        let out = beschneide_moves(&game.state, raw);
        assert!(
            !out.contains(&stone_move(Blau, 0)),
            "falsche Farbe in der geforderten Reihe muss beschnitten werden"
        );
        assert!(out.contains(&stone_move(Rot, 0)), "die geforderte Farbe darf nicht beschnitten werden");
        assert!(out.contains(&stone_move(Blau, -1)), "Bodenzuege sind nie beschnitten");
        set_modus_override_for_test(None);
    }

    #[test]
    fn wild_und_leerer_slot_beschneiden_nichts() {
        // Ergaenzend zu Test 2: Zellen ohne Farbforderung (kein Slot, oder
        // Wild/Special) duerfen laut Auftrag nichts beschneiden.
        set_modus_override_for_test(Some(Modus::Fest(0)));
        let game = drafting_game(12); // kein Dome-Tile an Slot (0,0) platziert
        let raw = vec![stone_move(Blau, 0), stone_move(Rot, 0)];
        let out = beschneide_moves(&game.state, raw.clone());
        assert_eq!(out, raw, "leerer Slot -- keine Forderung, keine Beschneidung");
        set_modus_override_for_test(None);
    }

    #[test]
    fn beschneidung_ueber_das_echte_generate_valid_moves() {
        // Wie Test 2, aber ueber den echten Generator (validation::
        // generate_valid_moves) statt einer handgebauten Liste -- deckt die
        // tatsaechliche Einbaustelle ab, nicht nur die reine Funktion.
        set_modus_override_for_test(Some(Modus::Fest(0)));
        let mut game = drafting_game(21);
        let tile = normal_tile(2, [Rot, Blau, Gelb, Schwarz]);
        let pi = game.state.current_player;
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("Slot frei");
        // Deterministische Fabrik-Belegung: beide Farben verfuegbar, damit
        // der Konflikt sicher entsteht (unabhaengig vom Beutel-RNG).
        game.state.factories[0].sun_tiles = vec![Blau, Blau];

        let moves = generate_valid_moves(&game.state);
        assert!(
            !moves.iter().any(|m| m.place.row_index == 0 && m.take.color == Blau),
            "Blau in Musterreihe 0 (fordert Rot) darf ueber den echten Generator nicht auftauchen"
        );
        assert!(
            moves.iter().any(|m| m.place.row_index == -1 && m.take.color == Blau),
            "Bodenzug fuer Blau muss weiterhin verfuegbar sein"
        );
        set_modus_override_for_test(None);
    }

    #[test]
    fn fallback_liefert_unbeschnittene_menge_statt_leer() {
        // Test 3 (Pflicht, "der wichtigste"): eine Kandidatenliste, die nach
        // der Beschneidung LEER waere (absichtlich OHNE Bodenzug-Eintrag,
        // damit der reale Rettungsanker -- Bodenzuege sind nie beschnitten --
        // hier nicht mitgreift und die Fallback-Logik selbst geprueft wird),
        // muss die UNBESCHNITTENE Menge zurueckgeben, nicht leer.
        set_modus_override_for_test(Some(Modus::Fest(0)));
        let mut game = drafting_game(31);
        let tile = normal_tile(3, [Rot, Blau, Gelb, Schwarz]); // (0,0) fordert Rot
        game.state.players[game.state.current_player]
            .dome_grid
            .place_dome_tile(tile, 0, 0)
            .expect("Slot frei");

        // Ausschliesslich Musterreihe-0-Platzierungen mit falscher Farbe --
        // JEDE davon wuerde einzeln beschnitten, kein Bodenzug im Angebot.
        let raw = vec![stone_move(Blau, 0), stone_move(Gelb, 0), stone_move(Schwarz, 0)];
        let out = beschneide_moves(&game.state, raw.clone());
        assert!(!out.is_empty(), "Fallback muss greifen -- die Aktionsmenge darf NIE leer werden");
        assert_eq!(out, raw, "im leeren Fall gilt exakt die unbeschnittene Ausgangsmenge");
        set_modus_override_for_test(None);
    }

    #[test]
    fn invariante_leerheit_bleibt_ueber_beschneidung_erhalten() {
        // Direktes Korrelat zur Dokumentation an `beschneide_moves`:
        // `ergebnis.is_empty() == moves.is_empty()`, fuer Aus UND Fest.
        let mut game = drafting_game(41);
        let tile = normal_tile(4, [Rot, Blau, Gelb, Schwarz]);
        game.state.players[game.state.current_player]
            .dome_grid
            .place_dome_tile(tile, 0, 0)
            .expect("Slot frei");

        for m in [Modus::Aus, Modus::Fest(0)] {
            set_modus_override_for_test(Some(m));
            let leer: Vec<Move> = Vec::new();
            assert!(beschneide_moves(&game.state, leer).is_empty(), "{m:?}: leer bleibt leer");
            let voll = vec![stone_move(Blau, 0)];
            assert_eq!(
                beschneide_moves(&game.state, voll).is_empty(),
                false,
                "{m:?}: nicht-leer darf durch Beschneidung nie leer werden"
            );
        }
        set_modus_override_for_test(None);
    }

    #[test]
    fn spalte_aus_seed_ist_deterministisch_und_liegt_in_0_bis_5() {
        for seed in [0u64, 1, 42, 999_999, u64::MAX] {
            let a = spalte_aus_seed(seed);
            let b = spalte_aus_seed(seed);
            assert_eq!(a, b, "gleiche Eingabe -> gleiche Spalte (reproduzierbar)");
            assert!(a <= 5, "Spalte muss in 0..=5 liegen, war {a}");
        }
    }

    #[test]
    fn auto_modus_ohne_gesetzten_seed_ist_wirkungslos() {
        // "auto" ohne vorherigen `set_ziel_spalte_seed`-Aufruf darf NICHT
        // raten -- `ziel_spalte()` muss `None` liefern (kein Beschneiden).
        set_modus_override_for_test(Some(Modus::Auto));
        set_ziel_spalte_seed(None); // explizit: kein Partie-Seed gesetzt
        assert_eq!(ziel_spalte(), None);
        set_ziel_spalte_seed(Some(123));
        assert_eq!(ziel_spalte(), Some(spalte_aus_seed(123)));
        set_ziel_spalte_seed(None); // Aufraeumen (Leck-Warnung in der Doku oben)
        set_modus_override_for_test(None);
    }
}

// ── Vorzugszug: Praeferenz statt Verbot ─────────────────────────────────────
//
// Nutzer-Leiter nach dem gemessenen Ende der Beschneidung (24 Zellen, beide
// Spieler zerstoert, max 0,20 Spalten/Partie): *"kannst fast schon eine
// heuristik bauen dafuer."* Der Unterschied zu ALLEM Gemessenen: die
// Praeferenz erzwingt nie einen schlechten Zug. Existiert in der Stellung ein
// konstruktiver Spaltenzug -- geforderte Farbe nehmbar UND legal in die
// passende Musterreihe legbar --, wird er gespielt; sonst spielt der normale
// Spieler. Kein Verbot, keine Blattwert-Verschiebung.

/// Ziel-Spalte des Vorzugsmodus, `MOSAIC_VORZUG_SPALTE` = 0..5.
/// Default aus. BEWUSST getrennt vom Beschneidungs-Knopf -- die beiden Modi
/// sind Alternativen und sollen nicht versehentlich kombiniert laufen.
pub(crate) fn vorzug_spalte() -> Option<usize> {
    static CELL: std::sync::OnceLock<Option<usize>> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| match std::env::var("MOSAIC_VORZUG_SPALTE") {
        Ok(v) => match v.trim().parse::<usize>() {
            Ok(c) if c <= 5 => Some(c),
            _ => {
                eprintln!("MOSAIC_VORZUG_SPALTE={v:?} ignoriert -- erwartet 0..5");
                None
            }
        },
        Err(_) => None,
    })
}

/// Der Vorzugszug selbst, oder `None` wenn keiner existiert / Modus aus.
///
/// Aufrufstellen: VOR der Netz-Suche in `run_net_arena_match`,
/// `run_net_vs_net_arena`, `run_net_self_play` (self_play.rs). Nur Runden
/// 1..=4 -- in Runde 5 entscheidet dort `round5::choose_action` exakt, und
/// der Vorzug darf die exakte Endrunden-Wahl nicht verdraengen.
///
/// Auswahl unter mehreren Kandidaten, deterministisch:
///  1. minimaler Ueberlauf auf die Strafleiste (der Zug soll bauen, nicht
///     bezahlen),
///  2. dann die am weitesten gefuellte Musterreihe (naechste Lieferung
///     zuerst fertig),
///  3. dann kleinste Reihe (billig vor teuer), dann stabile Reihenfolge.
///
/// Zwei Bedingungen je Kandidat, beide aus dem Brett ablesbar:
///  - Zelle `(r, spalte)` fordert GENAU `m.take.color` (`geforderte_farbe`)
///    und ist noch nicht gefuellt -- eine gefuellte Zelle braucht keine
///    Lieferung mehr.
///  - Die Platzierung ist ohnehin legal (`generate_valid_moves` liefert nur
///    legale Zuege; Farb-/Kapazitaetsregeln der Musterreihe stecken dort).
pub(crate) fn vorzugszug(state: &GameState) -> Option<crate::moves::Action> {
    let spalte = vorzug_spalte()?;
    vorzugszug_fuer_spalte(state, spalte)
}

/// Kern von [`vorzugszug`], mit EXPLIZITER Ziel-Spalte statt des Env-Knopfs
/// -- ausgelagert (2026-08-13, Spaltenbau-Auftrag), damit `spaltenbau.rs` die
/// IDENTISCHE Praeferenzlogik mit einer je Entscheid dynamisch bestimmten
/// Spalte wiederverwenden kann, statt sie zu duplizieren (CLAUDE.md:
/// "vorhandene scripts/Funktionen wiederverwenden"). Reiner Parameter-
/// Extrakt, keine Verhaltensaenderung -- `vorzugszug` selbst bleibt
/// byte-identisch.
pub(crate) fn vorzugszug_fuer_spalte(state: &GameState, spalte: usize) -> Option<crate::moves::Action> {
    if state.phase != crate::state::Phase::Drafting || state.round_number > 4 {
        return None;
    }
    let player = &state.players[state.current_player];
    // Runde 3 (Nutzer-Auftrag 2026-08-13, PREREG_provokation.md §11/§12):
    // einmal je Entscheid berechnet, nicht je Kandidat -- `verbleibende_
    // farben` iteriert den ganzen sichtbaren Zustand (siehe Doku dort), das
    // in der Kandidatenschleife zu wiederholen waere O(n^2) ohne Nutzen.
    let verbleibend = verbleibende_farben(state);
    let moves = crate::validation::generate_valid_moves(state);
    let mut best: Option<(usize, i64, i32, i32, crate::moves::Move)> = None;
    for m in moves {
        let r = m.place.row_index;
        if !(0..=5).contains(&r) {
            continue;
        }
        let r = r as usize;
        // Task 7a (Spaltenbau Runde 2, Nutzer-Auftrag 2026-08-13): Wild-Zellen
        // aktiv bedienen -- `geforderte_farbe` liefert fuer Wild `None`
        // (`dome.rs`, `required_color: None`), das alte `Some(x) if x ==
        // m.take.color`-Muster liess Wild-Zellen also NIE als Ziel gelten,
        // obwohl JEDE Farbe sie fuellen darf. Special bleibt ausgeschlossen
        // -- eine Special-Zelle nimmt gar keine Farbe per Stein-Zug entgegen,
        // sie fuellt sich erst automatisch, wenn ihre 3 Slot-Nachbarn
        // komplett sind (`round_end::check_special_trigger`).
        let Some(sp) = player.dome_grid.get_space(r, spalte) else {
            continue; // kein Slot an dieser Zelle -- kein Ziel.
        };
        if sp.is_filled() {
            continue; // Zelle schon gefuellt -> diese Lieferung baut die Spalte nicht.
        }
        let qualifiziert = match sp.space_type {
            SpaceType::Wild => true,
            SpaceType::Normal => sp.required_color == Some(m.take.color),
            SpaceType::Special => false,
        };
        if !qualifiziert {
            continue;
        }
        // KEIN Ueberlauf-Kriterium: `TakeAction` traegt keine Stueckzahl
        // (die haengt am Fabrikinhalt), und sie hier nachzuzaehlen hiesse
        // Quell-Logik zu duplizieren. Erste Messung ohne; zeigt die
        // Strafleiste einen Anstieg, ist das der naechste Verfeinerungspunkt.
        let zeile = &player.pattern_lines[r];
        let fuellung = zeile.tiles.len() as i32;
        // Task 3 (Runde 3, Nutzer-Auftrag 2026-08-13): unter mehreren
        // Kandidaten gewinnt jetzt die KNAPPSTE Farbe zuerst (PRIMAeR),
        // "vollste Reihe zuerst" bleibt nur noch der Tie-Break darunter --
        // was knapp ist und JETZT angeboten wird, kommt vielleicht nie
        // wieder (PREREG_provokation.md §11: 74,1% Blocker "Farbe nicht im
        // Angebot"). Kleinerer `knappheit`-Wert (wenig verbleibend) gewinnt,
        // weil `besser` auf Tupel-`<` sortiert.
        let knappheit = farben_index(m.take.color)
            .map(|i| verbleibend[i])
            .unwrap_or(i64::MAX); // TakeAction liefert nie Wild (kein ziehbarer Stein, tile.rs); defensiv.
        let kandidat = (0usize, knappheit, -fuellung, r as i32, m);
        let besser = match &best {
            None => true,
            Some((u, k, f, rr, _)) => {
                (kandidat.0, kandidat.1, kandidat.2, kandidat.3) < (*u, *k, *f, *rr)
            }
        };
        if besser {
            best = Some(kandidat);
        }
    }
    best.map(|(_, _, _, _, m)| crate::moves::Action::Stone(m))
}

// ── Runde 3: zaehlbare Versorgung (Nutzer-Auftrag 2026-08-13) ───────────────
//
// PREREG_provokation.md §11 letzter Satz: dominanter Blocker (74,1%) ist
// nicht mehr Farblogik, sondern die VERSORGUNG -- die fuer die Zielspalte
// geforderte Farbe war schlicht nirgends im Angebot. `verbleibende_farben`
// beantwortet die dafuer nötige Frage "wie viel von Farbe X ist ueberhaupt
// noch NICHT verbraucht", aus rein OEFFENTLICHER Information.

/// Anzahl normaler Farbsteine je Farbe, die JETZT weder auf einem der beiden
/// Spielerbretter verbaut noch in einer Fabrik/der Grossen Fabrik sichtbar
/// ausliegen -- also (noch ungezogen) im Beutel ODER (schon verworfen, wird
/// wieder eingemischt) im Ablageturm liegen. Rechnung: Gesamtvorrat
/// (`TILES_PER_COLOR`, Regelbuch-Konstante) minus jede sichtbar VERBAUTE oder
/// AUSLIEGENDE Kachel dieser Farbe.
///
/// BEWUSST NICHT `state.bag`/`state.tower` direkt gelesen -- das waere die
/// exakte Beutel-/Turm-ZUSAMMENSETZUNG, die kein menschlicher Spieler je
/// sieht (nur ihre Groesse, `supply.rs::Bag::count`/`Tower::count`, nicht die
/// Farbverteilung). Die Differenz aus oeffentlicher Information liefert
/// exakt dieselbe Zahl -- ein Mensch kaeme mit einer Strichliste ebenso
/// darauf: er zaehlt ab, was er auf beiden Brettern und in der Tischmitte
/// SIEHT, der Rest muss im Beutel oder Turm sein.
///
/// Gezaehlt (alles oeffentlich sichtbar, GameState-Felder):
///  - `state.factories[*].sun_tiles` + `.moon_stacks` (`factory.rs`),
///  - `state.large_factory.sun_tiles` + `.moon_pool` (`factory.rs`),
///  - je Spieler: `pattern_lines[*].tiles`, `broken_tiles` (Strafleiste),
///    `dome_grid.dome_slots[*][*]`s `spaces[*].placed_color` (`board.rs`,
///    `dome.rs`).
///
/// Ergebnis in der Reihenfolge von `TileColor::NORMAL`, siehe
/// [`farben_index`]. `i64` statt `usize`: eine Inkonsistenz soll als
/// sichtbar NEGATIVE Zahl auffallen statt in einem Unsigned-Underflow zu
/// verschwinden (defensiv, kein Panic) -- Aufrufer clampen selbst auf 0.
pub(crate) fn verbleibende_farben(state: &GameState) -> [i64; 5] {
    let mut verbaut = [0i64; 5];
    let mut zaehle = |c: TileColor| {
        if let Some(i) = farben_index(c) {
            verbaut[i] += 1;
        }
    };
    for f in &state.factories {
        for &c in &f.sun_tiles {
            zaehle(c);
        }
        for stack in &f.moon_stacks {
            for &c in stack {
                zaehle(c);
            }
        }
    }
    for &c in &state.large_factory.sun_tiles {
        zaehle(c);
    }
    for &c in &state.large_factory.moon_pool {
        zaehle(c);
    }
    for p in &state.players {
        for line in &p.pattern_lines {
            for &c in &line.tiles {
                zaehle(c);
            }
        }
        for &c in &p.broken_tiles {
            zaehle(c);
        }
        for row in &p.dome_grid.dome_slots {
            for slot in row {
                if let Some(tile) = slot {
                    for space in &tile.spaces {
                        if let Some(c) = space.placed_color {
                            zaehle(c);
                        }
                    }
                }
            }
        }
    }
    std::array::from_fn(|i| crate::tile::TILES_PER_COLOR as i64 - verbaut[i])
}

/// Runde 4, Baustein 1 (Nutzer-Auftrag `PREREG_provokation.md` §14): fuer
/// [`crate::spaltenbau::ist_spalte_vollendbar`] ist [`verbleibende_farben`]
/// die FALSCHE Zahl -- die zaehlt Fabrik-/Mond-Kacheln als "verbaut", obwohl
/// sie JETZT noch nehmbar sind (sie misst "im Beutel/Turm versteckt", nicht
/// "noch erreichbar"). Eine tiefe Reihe (braucht bis zu 6 Kopien) erschien
/// dadurch systematisch unvollendbar, sobald ein Teil ihrer Farbe gerade in
/// den Fabriken lag statt im Beutel -- GEFUNDEN ueber die erste volle
/// Runde-4-Messung: 3-5 Zielwechsel je Partie, vertikale Punkte auf 0,70
/// statt 5,95 eingebrochen (schlechter als ohne Spaltenbauer).
///
/// "Noch erreichbar" = Gesamtvorrat (13) minus nur das, was TATSAECHLICH
/// nicht mehr zurueckkommt: beider Spieler Strafleiste und platzierte
/// Kuppelzellen, PLUS die Musterreihen-Fliesen des GEGNERS (der haelt sie
/// bereits, sie sind fuer uns weg). Die eigenen Musterreihen NICHT
/// abgezogen -- das eigene Material fuer eine ANDERE Zeile ist bei einem
/// spaeteren Rundenende potenziell wieder frei (siehe `ist_spalte_
/// vollendbar`s "transiente Falschbindung"-Kommentar), es zusaetzlich
/// abzuziehen waere erneut zu pessimistisch. Fabrik-/Mond-/Beutel-/Turm-
/// Kacheln bleiben unangetastet -- sie sind (irgendwann) erreichbar.
pub(crate) fn noch_erreichbare_farben(state: &GameState, aktueller_spieler: usize) -> [i64; 5] {
    let mut verloren = [0i64; 5];
    let mut zaehle = |c: TileColor| {
        if let Some(i) = farben_index(c) {
            verloren[i] += 1;
        }
    };
    for p in &state.players {
        for &c in &p.broken_tiles {
            zaehle(c);
        }
        for row in &p.dome_grid.dome_slots {
            for slot in row {
                if let Some(tile) = slot {
                    for space in &tile.spaces {
                        if let Some(c) = space.placed_color {
                            zaehle(c);
                        }
                    }
                }
            }
        }
    }
    let gegner = 1 - aktueller_spieler;
    if let Some(p) = state.players.get(gegner) {
        for line in &p.pattern_lines {
            for &c in &line.tiles {
                zaehle(c);
            }
        }
    }
    std::array::from_fn(|i| crate::tile::TILES_PER_COLOR as i64 - verloren[i])
}

/// Index 0..=4 von `color` in `TileColor::NORMAL` -- `None` fuer `Wild`
/// (kein ziehbarer Stein, siehe `tile.rs`-Doku "kein ziehbarer Stein").
pub(crate) fn farben_index(color: TileColor) -> Option<usize> {
    TileColor::NORMAL.iter().position(|&c| c == color)
}

#[cfg(test)]
mod vorzugszug_tests {
    use super::*;
    use crate::dome::{DomeSpace, DomeTile};
    use crate::moves::Action;
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

    /// Task 7a (Spaltenbau Runde 2): eine Wild-Zelle in der Ziel-Spalte MUSS
    /// jetzt als Ziel gelten, unabhaengig von der genommenen Farbe -- vor dem
    /// Fix lieferte `geforderte_farbe` fuer Wild `None` und das
    /// `Some(x) if x == m.take.color`-Muster verwarf JEDE Farbe.
    #[test]
    fn vorzugszug_fuer_spalte_akzeptiert_jede_farbe_an_einer_wild_zelle() {
        let mut game = drafting_game(101);
        let pi = game.state.current_player;
        // Slot (0,0): si=0 -> (Zeile0,Spalte0)=Wild, restliche normal.
        let tile = DomeTile::new(
            50,
            vec![DomeSpace::wild(), DomeSpace::normal(Blau), DomeSpace::normal(Gelb), DomeSpace::normal(Schwarz)],
            0,
        );
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("Slot frei");
        // Fabrik bietet nur eine Farbe an, die an KEINER Normal-Zelle der
        // Spalte 0 gefordert ist (Schwarz sitzt an (1,0), nicht (0,0)) --
        // waere die Wild-Zelle (0,0) nicht qualifiziert, gaebe es hier gar
        // keinen Kandidaten fuer Spalte 0.
        game.state.factories[0].sun_tiles = vec![Rot, Rot];
        let ergebnis = vorzugszug_fuer_spalte(&game.state, 0);
        match ergebnis.expect("Wild-Zelle muss JEDE Farbe als Kandidat zulassen") {
            Action::Stone(m) => {
                assert_eq!(m.place.row_index, 0, "muss Musterreihe 0 (die Wild-Zelle) treffen");
                assert_eq!(m.take.color, Rot, "muss die tatsaechlich angebotene Farbe nehmen");
            }
            other => panic!("erwartet Action::Stone, bekam {other:?}"),
        }
    }

    /// Gegenprobe: eine Special-Zelle darf weiterhin NICHT als Farb-Ziel
    /// gelten (sie nimmt gar keine Farbe entgegen). Direkter Aufruf der
    /// Qualifikations-Regel statt eines vollen Spiel-Setups (ein volles
    /// `drafting_game` deckt zufaellig zusaetzliche Fabriken/Farben aus dem
    /// Beutel auf, die ueber ANDERE Zeilen der Spalte einen Kandidaten
    /// liefern koennten und die Aussage damit verwaessern wuerden).
    /// Task 3 (Runde 3, Nutzer-Auftrag 2026-08-13): unter mehreren
    /// Kandidaten muss die KNAPPSTE Farbe gewinnen, nicht mehr nur die
    /// vollste Reihe. Aufbau: Zeile 0 fordert Rot (leer, Fuellung 0), Zeile 1
    /// fordert Gelb (schon 1 Fliese, Fuellung 1 -- unter der ALTEN Regel
    /// waere Gelb der Sieger). Rot wird bis auf das aktuelle Angebot restlos
    /// verbraucht (11 weitere Kopien sichtbar im Mondbereich der Grossen
    /// Fabrik + 2 angebotene = 13 von 13, Rest 0), Gelb bleibt reichlich
    /// (nur 3 von 13 sichtbar verbraucht).
    #[test]
    fn vorzugszug_fuer_spalte_bevorzugt_knappe_farbe_vor_vollerer_reihe() {
        let mut game = drafting_game(103);
        let pi = game.state.current_player;
        // Slot (0,0), Rotation 0: si=0 -> (Zeile0,Spalte0)=Rot,
        // si=2 -> (Zeile1,Spalte0)=Gelb (dieselbe Geometrie wie
        // `vorzugszug_fuer_spalte_akzeptiert_jede_farbe_an_einer_wild_zelle`).
        let tile = DomeTile::new(
            52,
            vec![
                DomeSpace::normal(Rot),
                DomeSpace::normal(Blau),
                DomeSpace::normal(Gelb),
                DomeSpace::normal(Schwarz),
            ],
            0,
        );
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("Slot frei");
        game.state.players[pi].pattern_lines[1].color = Some(Gelb);
        game.state.players[pi].pattern_lines[1].tiles.push(Gelb);

        game.state.factories[0].sun_tiles = vec![Rot, Rot];
        game.state.factories[1].sun_tiles = vec![Gelb, Gelb];
        game.state.large_factory.moon_pool = vec![Rot; 11];

        let ergebnis =
            vorzugszug_fuer_spalte(&game.state, 0).expect("es muss einen Kandidaten geben (Rot ODER Gelb)");
        match ergebnis {
            Action::Stone(m) => {
                assert_eq!(
                    m.place.row_index, 0,
                    "die KNAPPE Farbe (Rot, Zeile 0) muss gewinnen, nicht die vollere Zeile 1 (Gelb)"
                );
                assert_eq!(m.take.color, Rot);
            }
            other => panic!("erwartet Action::Stone, bekam {other:?}"),
        }
    }

    #[test]
    fn vorzugszug_fuer_spalte_ignoriert_special_zellen() {
        let mut game = drafting_game(102);
        let pi = game.state.current_player;
        // Slot (0,0), Rotation 0: si=0 -> (Zeile0,Spalte0)=Special,
        // si=2 -> (Zeile1,Spalte0)=Schwarz (siehe `slot_score`-Doku fuer die
        // Indexformel). Beide Zeilen dieser Spalte sind damit entweder
        // Special oder eine FESTE, hier nicht angebotene Farbe.
        let tile = DomeTile::new(
            51,
            vec![DomeSpace::special(), DomeSpace::normal(Blau), DomeSpace::normal(Schwarz), DomeSpace::normal(Gelb)],
            0,
        );
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("Slot frei");
        let ergebnis = vorzugszug_fuer_spalte(&game.state, 0);
        if let Some(Action::Stone(m)) = &ergebnis {
            assert_ne!(
                m.place.row_index, 0,
                "die Special-Zelle (Zeile 0) darf NIE als Ziel gewaehlt werden, Zug war {m:?}"
            );
        }
    }

    #[test]
    fn farben_index_deckt_alle_fuenf_normalfarben_ab_und_verwirft_wild() {
        let mut gesehen = std::collections::HashSet::new();
        for c in crate::tile::TileColor::NORMAL {
            let i = farben_index(c).expect("jede Normalfarbe muss einen Index haben");
            assert!(i < 5);
            gesehen.insert(i);
        }
        assert_eq!(gesehen.len(), 5, "alle 5 Indizes muessen verschieden sein");
        assert_eq!(farben_index(crate::tile::TileColor::Wild), None, "Wild ist kein ziehbarer Stein");
    }

    /// Task 1 (Runde 3): `verbleibende_farben` muss Gesamtvorrat minus JEDE
    /// sichtbare Fundstelle liefern -- Fabrik, Grosse Fabrik (Sonne+Mond),
    /// beide Spielerbretter (Musterreihen, Strafleiste, verbaute Kuppelzellen).
    /// NICHT gezaehlt: `state.bag`/`state.tower` selbst (die Differenz IST
    /// das Ergebnis).
    #[test]
    fn verbleibende_farben_zaehlt_jede_sichtbare_fundstelle() {
        let mut game = drafting_game(104);
        let pi = game.state.current_player;
        let gegner = 1 - pi;

        // Tischmitte deterministisch leeren -- `drafting_game` fuellt beim
        // Partiestart ALLE Fabriken/die Grosse Fabrik aus dem echten
        // (zufaelligen) Beutel; ohne dieses Leeren koennten dort zufaellig
        // WEITERE Rot-Kopien liegen und die exakte Zaehlung unten verwaessern.
        for f in game.state.factories.iter_mut() {
            f.sun_tiles.clear();
            f.moon_stacks.clear();
        }
        game.state.large_factory.sun_tiles.clear();
        game.state.large_factory.moon_pool.clear();

        // 2 Rot in Fabrik 0, 1 Rot im Mond der Grossen Fabrik.
        game.state.factories[0].sun_tiles = vec![Rot, Rot];
        game.state.large_factory.moon_pool = vec![Rot];
        // 1 Rot auf der Strafleiste des Gegners.
        game.state.players[gegner].broken_tiles = vec![Rot];
        // 1 Rot in einer Musterreihe des aktiven Spielers.
        game.state.players[pi].pattern_lines[2].color = Some(Rot);
        game.state.players[pi].pattern_lines[2].tiles.push(Rot);
        // 1 Rot als VERBAUTE (platzierte) Kuppelzelle beim Gegner.
        let tile = DomeTile::new(53, vec![DomeSpace::normal(Rot), DomeSpace::normal(Blau), DomeSpace::normal(Gelb), DomeSpace::normal(Schwarz)], 0);
        game.state.players[gegner].dome_grid.place_dome_tile(tile, 0, 0).expect("Slot frei");
        game.state.players[gegner].dome_grid.dome_slots[0][0].as_mut().unwrap().spaces[0].placed_color = Some(Rot);

        let verbleibend = verbleibende_farben(&game.state);
        let i = farben_index(Rot).unwrap();
        // 2 (Fabrik) + 1 (Mond GF) + 1 (Strafleiste) + 1 (Musterreihe) + 1 (verbaut) = 6 sichtbare Rot.
        assert_eq!(
            verbleibend[i],
            crate::tile::TILES_PER_COLOR as i64 - 6,
            "muss 13 minus alle 6 sichtbaren Rot-Fundstellen sein: {verbleibend:?}"
        );
        // Blau wurde in diesem Test nirgends platziert und die Tischmitte ist
        // deterministisch leer -- muss exakt beim vollen Vorrat stehen.
        let bi = farben_index(Blau).unwrap();
        assert_eq!(verbleibend[bi], crate::tile::TILES_PER_COLOR as i64);
    }

    /// Runde 4, Baustein 1: `noch_erreichbare_farben` darf FABRIK-Kacheln
    /// NICHT abziehen (die sind jetzt noch nehmbar) -- anders als
    /// `verbleibende_farben` im Test oben. Abgezogen werden nur beider
    /// Spieler Strafleiste/verbaute Kuppelzellen UND die Musterreihen des
    /// GEGNERS (der haelt sie schon); die EIGENEN Musterreihen bleiben
    /// unangetastet.
    #[test]
    fn noch_erreichbare_farben_zaehlt_fabrikkacheln_nicht_als_verloren() {
        let mut game = drafting_game(105);
        let pi = game.state.current_player;
        let gegner = 1 - pi;

        for f in game.state.factories.iter_mut() {
            f.sun_tiles.clear();
            f.moon_stacks.clear();
        }
        game.state.large_factory.sun_tiles.clear();
        game.state.large_factory.moon_pool.clear();

        // 2 Rot in der Fabrik -- muss NICHT abgezogen werden (noch nehmbar).
        game.state.factories[0].sun_tiles = vec![Rot, Rot];
        // 1 Rot auf der Strafleiste des Gegners -- muss abgezogen werden.
        game.state.players[gegner].broken_tiles = vec![Rot];
        // 1 Rot in einer Musterreihe des AKTIVEN Spielers -- bleibt
        // erreichbar (eigenes Material, kann bei Rundenende wieder frei
        // werden), wird NICHT abgezogen.
        game.state.players[pi].pattern_lines[2].color = Some(Rot);
        game.state.players[pi].pattern_lines[2].tiles.push(Rot);
        // 1 Rot in einer Musterreihe des GEGNERS -- der haelt es schon,
        // muss abgezogen werden.
        game.state.players[gegner].pattern_lines[1].color = Some(Rot);
        game.state.players[gegner].pattern_lines[1].tiles.push(Rot);

        let erreichbar = noch_erreichbare_farben(&game.state, pi);
        let i = farben_index(Rot).unwrap();
        // 13 - 1 (Strafleiste Gegner) - 1 (Musterreihe Gegner) = 11.
        assert_eq!(
            erreichbar[i],
            crate::tile::TILES_PER_COLOR as i64 - 2,
            "Fabrik-Rot und die eigene Musterreihe duerfen nicht abgezogen werden: {erreichbar:?}"
        );
    }
}
