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
pub(crate) fn set_ziel_spalte_seed(seed: Option<u64>) {
    AUTO_SPALTE.with(|c| c.set(seed.map(spalte_aus_seed)));
}

/// Deterministische Ableitung Ziel-Spalte 0..=5 aus dem Partie-Seed -- gleiche
/// SplitMix64-Mischung wie `net_mcts::partie_gewicht_aus_seed` (dort
/// kontinuierlich in `[0,max]`, hier ein Index; siehe dortige Begruendung,
/// warum die Mischung noetig ist: aufeinanderfolgende Partie-Seeds im
/// Self-Play unterscheiden sich oft nur in den unteren Bits).
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
    let moves = crate::validation::generate_valid_moves(state);
    let mut best: Option<(usize, i32, i32, crate::moves::Move)> = None;
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
        let kandidat = (0usize, -fuellung, r as i32, m);
        let besser = match &best {
            None => true,
            Some((u, f, rr, _)) => {
                (kandidat.0, kandidat.1, kandidat.2) < (*u, *f, *rr)
            }
        };
        if besser {
            best = Some(kandidat);
        }
    }
    best.map(|(_, _, _, m)| crate::moves::Action::Stone(m))
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
}
