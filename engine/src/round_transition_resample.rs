//! PREREG_r4_value_calibration.md, Abschnitt "Vorbedingung": Stichprobe
//! alternativer Runde-5-Starts DESSELBEN Runde-4-Endbretts -- Ground Truth
//! für die Value-Kalibrierung (`ab_value` je Sample über `round5.rs`, siehe
//! PREREG-Dokument, Abschnitt "Ground Truth").
//!
//! Gegenstück zu `round_transition.rs`, das für die netzgeführte Suche
//! vorwärts läuft (Tiling-Leaf → Rundenübergang → nächste Runde). Hier wird
//! vom echten Runde-4-Endzustand aus deterministisch bis zum Rundenende
//! gespielt und dann n-fach neu befüllt.
//!
//! **Es gab bis zum 2026-09-21 einen zweiten, RÜCKWÄRTS gerichteten Weg**
//! (`invert_round5_fill`/`resample_round5_start` plus die PyO3-Hülle
//! `resample_round_transition_json`): er nahm einen fertig befüllten
//! Runde-5-Start und machte `fill_factories` rückgängig. Daran hing ein
//! Grenzfall -- `supply::Bag::refill_from_tower` leert den Turm IMMER
//! vollständig, ein beobachteter leerer Turm ist daher nicht unterscheidbar
//! zwischen "war schon leer" und "ein Refill hat ihn geleert". Die
//! konservative Regel lehnte jeden solchen Zustand ab.
//!
//! **BEFUND 2026-08-03 (voller v19-Korpus, 9.000 Partien): 87,6 % der echten
//! Runde-5-Starts haben einen leeren Turm.** Die Ausschlussregel hätte also
//! fast das ganze Substrat verworfen. Der PREREG-Pfad wurde deshalb noch am
//! selben Tag auf das Vorwärts-Sampling unten umgestellt, das beim echten
//! Runde-4-Zustand ansetzt (Beutel und Turm dort als EXAKTE Multisets
//! bekannt) und die Turm-Ambiguität gar nicht erst erzeugt.
//!
//! Der Rückwärts-Weg blieb danach als korrekter, aber unbenutzter Baustein
//! liegen -- 186 Zeilen Code und sieben Tests ohne einen einzigen Aufrufer.
//! Entfernt am 2026-09-21 auf Nutzer-Entscheid
//! (`PREREG_code_cleanup_closeout.md` par.8g Punkt 10, Ergebnis in par.8o).

use rand::rngs::StdRng;
use rand::SeedableRng;

use crate::state::{GameState, Phase};

/// Deterministisch (kein `rng`-Verbrauch, s. [`autoplay_to_round5_and_resample`]-
/// Doku) bis unmittelbar vor den Rundenübergang vorgespult + `n_samples`-mal
/// frisch resampelt, PLUS der deterministisch erreichte Runde-Ende-Zustand
/// selbst -- für den Python-seitigen Konsistenz-Check (dessen Brett muss zum
/// ersten echten Folge-Record der Partie passen, modulo Befüllung).
///
/// `r4_state` muss ein "letzter R4-Record" sein: `round==4`, `phase==Tiling`
/// (PREREG_r4_value_calibration.md, "Positions-Substrat"). Nutzt
/// AUSSCHLIESSLICH bestehende Bausteine, nichts neu erfunden:
///   1. [`resolve_to_pre_chance`] spult BEIDE Spieler per exaktem
///      DFS-Tiling-Solver (`best_first_step_exact`, dieselbe Politik wie
///      Self-Play) bis unmittelbar vor den letzten `EndTiling`-Aufruf vor --
///      GEPRÜFT rng-frei (s.u.). Das Ergebnis (`pre.state`) IST der
///      zurückgegebene Runde-Ende-Zustand: `round_number` unverändert (noch
///      Runde 4), `phase` noch `Tiling` (ein `EndTiling` steht noch aus),
///      Strafen/Kuppel-Rundenreste (`clear_broken`→Turm) NOCH NICHT
///      angewendet -- die passieren erst als Teil des (deterministischen,
///      aber an den Zufallsschritt gekoppelten) letzten `EndTiling`-Aufrufs,
///      siehe `game.rs::execute_end_tiling`/`next_round`. Dokumentiert statt
///      stillschweigend verschoben: ein Python-Konsistenz-Check gegen den
///      ersten echten Runde-5-Record muss das (fehlende Strafabzüge/
///      Turm-Zugang aus dem Runde-4-Boden) mit einkalkulieren.
///   2. Je Sample: [`advance_one_chance`] (bestehende Funktion) auf einem
///      Klon von `pre.state` -- mischt Beutel + Bonuschip-Pool mit dem
///      Sample-RNG neu und wendet dann den TATSÄCHLICHEN letzten
///      `EndTiling`-Aufruf an (`game.rs::end_tiling`→`execute_end_tiling`→
///      `next_round`→`state::setup_new_round`) -- der natürliche
///      Beutel-leer→Turm-Reshuffle-Pfad läuft dabei einfach mit (kein
///      Sonderfall, keine Ausschlussregel, im Gegensatz zum
///      Inversions-Pfad oben).
///
/// **RNG-Freiheit des Vorlaufs, geprüft (nicht nur übernommen):**
/// `resolve_to_pre_chance` reicht für den ERSTEN `EndTiling`-Aufruf (den
/// Spieler, der zuerst fertig wird) einen `unused_rng` durch -- dessen
/// Zweig in `game.rs::end_tiling` (`if !tiling_done[other] { ...; return
/// Ok(()); }`) kehrt VOR jedem `rng`-Zugriff zurück, weil `execute_end_tiling`
/// (der einzige Ort, der `rng` in diesem Aufruf-Pfad überhaupt anfasst) nur
/// im ANDEREN Zweig aufgerufen wird. `apply_single_tiling`/
/// `apply_bonus_chips_with` (die übrigen beiden Schritte der Vorspul-Schleife)
/// nehmen laut Signatur gar keinen `rng`-Parameter entgegen. Der Vorlauf ist
/// also tatsächlich, nicht nur laut Doku-Kommentar, deterministisch -- ein
/// zusätzlicher fixer Seed dafür (wie ursprünglich angefragt) ist daher
/// NICHT nötig; `resolve_to_pre_chance` bringt intern bereits einen festen
/// Dummy-Seed (0) mit.
pub fn autoplay_to_round5_and_resample(
    r4_state: &GameState,
    n_samples: u32,
    seed: u64,
) -> Result<(GameState, Vec<GameState>), String> {
    if r4_state.round_number != 4 {
        return Err(format!(
            "autoplay_to_round5_and_resample: erwartet round==4, war {}",
            r4_state.round_number
        ));
    }
    if r4_state.phase != Phase::Tiling {
        return Err(format!(
            "autoplay_to_round5_and_resample: erwartet Phase::Tiling, war {:?}",
            r4_state.phase
        ));
    }

    let pre = crate::round_transition::resolve_to_pre_chance(r4_state).ok_or_else(|| {
        "autoplay_to_round5_and_resample: resolve_to_pre_chance konnte den Tiling-Rest nicht \
         auflösen (Solver-/Anwendungsfehler oder Sicherheitsnetz-Guard erreicht -- siehe dortige \
         Doku)"
            .to_string()
    })?;

    let mut samples = Vec::with_capacity(n_samples as usize);
    for i in 0..n_samples {
        let mut rng = StdRng::seed_from_u64(seed.wrapping_add(i as u64));
        let sample = crate::round_transition::advance_one_chance(&pre, &mut rng).ok_or_else(|| {
            format!("autoplay_to_round5_and_resample: advance_one_chance fehlgeschlagen (Sample-Index {i})")
        })?;
        samples.push(sample);
    }
    Ok((pre.state().clone(), samples))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::round5;
    use crate::round_transition::{drive_to_round_start, drive_to_round_tiling_leaf};
    // Fabrik-Fuellstaende je Sample -- nur hier gebraucht, nicht im Produktivcode.
    use crate::state::{NUM_SMALL_FACTORIES, TILES_PER_LARGE_FACTORY, TILES_PER_SMALL_FACTORY};

    /// Echter Runde-5-Start über die Engine (Memory
    /// `feedback_check_existing_tools_first`: `drive_to_round_start` existiert
    /// bereits in `round_transition.rs`, kein neuer Test-Fixture-Aufbau nötig).
    /// Echter "letzter R4-Record"-artiger Zustand (round==4, Phase::Tiling,
    /// VOR dem letzten Rundenübergang) -- über die neue Test-Hilfsfunktion
    /// `drive_to_round_tiling_leaf` (Memory `feedback_check_existing_tools_first`:
    /// mirrors `drive_to_first_round_end`s bestehendes Muster, kein neuer
    /// Spielaufbau erfunden).
    fn r4_tiling_leaf(seed: u64) -> GameState {
        drive_to_round_tiling_leaf(seed, 4)
    }

    /// Alle 5 Farben müssen je Zustand exakt `TILES_PER_COLOR` (13) ergeben
    /// -- derselbe, bereits an echten Zufallspartien verifizierte
    /// Bilanz-Invariante wie `self_play::tests::
    /// tile_color_accounting_invariant_holds_throughout_random_games`
    /// (wiederverwendet über `pub(crate) fn count_color`, nicht dupliziert).
    fn assert_full_tile_balance(state: &GameState, label: &str) {
        use crate::self_play::tests::count_color;
        use crate::tile::{TileColor, TILES_PER_COLOR};
        for &c in TileColor::NORMAL.iter() {
            assert_eq!(
                count_color(state, c),
                TILES_PER_COLOR,
                "{label}: Farb-Bilanz für {:?} muss {TILES_PER_COLOR} sein (Plättchen-Erhaltung)",
                c
            );
        }
    }

    #[test]
    fn tile_conservation_through_autoplay_and_resample() {
        let leaf = r4_tiling_leaf(21);
        assert_full_tile_balance(&leaf, "r4_tiling_leaf (Eingabe)");

        let (r4_end, samples) =
            autoplay_to_round5_and_resample(&leaf, 5, 999).expect("autoplay sollte gelingen");
        assert_full_tile_balance(&r4_end, "r4_end (deterministischer Vorlauf)");
        assert_eq!(samples.len(), 5);
        for s in &samples {
            assert_full_tile_balance(s, "r5-Sample");
        }
    }

    #[test]
    fn playout_is_deterministic_for_same_input() {
        let leaf = r4_tiling_leaf(22);
        let (r4_end_a, _) = autoplay_to_round5_and_resample(&leaf, 1, 1).expect("autoplay a");
        let (r4_end_b, _) = autoplay_to_round5_and_resample(&leaf, 1, 1).expect("autoplay b");
        assert_eq!(
            crate::serialize::state_to_json(&r4_end_a, true),
            crate::serialize::state_to_json(&r4_end_b, true),
            "der deterministische Vorlauf (resolve_to_pre_chance) muss bei gleicher Eingabe \
             IMMER denselben R4-Ende-Zustand liefern, unabhängig vom (hier ohnehin gleichen) \
             Resample-seed"
        );
    }

    #[test]
    fn resample_determinism_same_seed_identical_different_seed_varies() {
        let leaf = r4_tiling_leaf(23);

        let (_, a) = autoplay_to_round5_and_resample(&leaf, 4, 500).expect("autoplay a");
        let (_, b) = autoplay_to_round5_and_resample(&leaf, 4, 500).expect("autoplay b");
        let sig_a: Vec<_> = a.iter().map(|s| crate::serialize::state_to_json(s, true)).collect();
        let sig_b: Vec<_> = b.iter().map(|s| crate::serialize::state_to_json(s, true)).collect();
        assert_eq!(sig_a, sig_b, "gleicher seed muss identische Runde-5-Samples liefern");

        let (_, c) = autoplay_to_round5_and_resample(&leaf, 4, 501).expect("autoplay c");
        let sig_c: Vec<_> = c.iter().map(|s| crate::serialize::state_to_json(s, true)).collect();
        assert_ne!(
            sig_a, sig_c,
            "verschiedene seeds sollten (bei n_samples=4) nicht dieselben Runde-5-Samples ergeben"
        );
    }

    #[test]
    fn each_autoplay_sample_is_a_valid_round5_drafting_start() {
        let leaf = r4_tiling_leaf(24);
        let (_, samples) = autoplay_to_round5_and_resample(&leaf, 5, 77).expect("autoplay");
        for s in &samples {
            assert_eq!(s.round_number, 5);
            assert_eq!(s.phase, Phase::Drafting);
            assert!(round5::applies(s), "round5::applies muss für jeden Sample-Zustand true sein");
            assert_eq!(s.factories.len(), NUM_SMALL_FACTORIES);
            for f in &s.factories {
                assert_eq!(f.sun_tiles.len(), TILES_PER_SMALL_FACTORY);
                assert!(f.moon_stacks.is_empty());
                assert!(f.bonus_chip.is_some());
                assert!(!f.bonus_chip_revealed);
            }
            assert_eq!(s.large_factory.sun_tiles.len(), TILES_PER_LARGE_FACTORY);
            assert!(s.large_factory.moon_pool.is_empty());
            assert!(s.large_factory.has_first_player_marker);
        }
    }

    #[test]
    fn rejects_non_round4_input() {
        let mut s = r4_tiling_leaf(25);
        s.round_number = 3;
        assert!(autoplay_to_round5_and_resample(&s, 2, 1).is_err());
    }

    #[test]
    fn rejects_non_tiling_phase_input() {
        // Ein Runde-4-DRAFTING-Start (kein Tiling-Leaf) ist keine gültige
        // Eingabe -- der PREREG verlangt ausdrücklich `phase=="tiling"`.
        let s = drive_to_round_start(26, 4);
        assert_eq!(s.phase, Phase::Drafting);
        assert!(autoplay_to_round5_and_resample(&s, 2, 1).is_err());
    }
}
