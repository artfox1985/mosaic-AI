//! PREREG_r4_value_calibration.md, Abschnitt "Vorbedingung": Inversion +
//! Resampling der Fabrik-Neubefüllung eines Runde-5-STARTzustands.
//!
//! Gegenstück zu `round_transition.rs` (das läuft VORWÄRTS: Tiling-Leaf →
//! Rundenübergang → nächste Runde, für die netzgeführte Suche). Hier ist die
//! Eingabe bereits ein fertig befüllter Runde-5-Start (`GameState` direkt
//! nach `state::setup_new_round`, Phase::Drafting, VOR dem ersten Zug) --
//! die Aufgabe ist, `fill_factories` RÜCKGÄNGIG zu machen (Sonnenplättchen +
//! Bonuschips zurück in Beutel/Pool) und danach n-fach mit frischem RNG neu
//! zu befüllen, um eine Stichprobe alternativer Runde-5-Starts DESSELBEN
//! Runde-4-Endbretts zu erzeugen (Ground Truth für die Value-Kalibrierung
//! via `round5.rs`, siehe PREREG-Dokument, Abschnitt "Ground Truth").
//!
//! **Turm-Reshuffle-Grenzfall** (PREREG "Bekannte Einschränkungen"):
//! `supply::Bag::refill_from_tower` leert den Turm bei einem Refill IMMER
//! vollständig (`Tower::empty` == `std::mem::take`, kein Teil-Leeren
//! möglich). Ein beobachteter leerer Turm im Post-Fill-Zustand ist daher
//! entweder (a) "Turm war schon vor der Befüllung leer" (unbedenklich,
//! `pre_tower = []` ist exakt) oder (b) "ein Refill hat den Turm während
//! GENAU dieser Befüllung geleert" (Turm-Inhalt VOR der Befüllung ist dann
//! aus der Momentaufnahme nicht rekonstruierbar -- es gibt kein
//! Log-Ereignis dafür, `fill_factories`/`draw_with_refill` loggen nichts,
//! grep-geprüft). Diese zwei Fälle sind aus einem einzelnen `state_json`-
//! Schnappschuss NICHT unterscheidbar. Konservative Entscheidung (PREREG
//! erlaubt das explizit, "Umsetzung beim Implementierer", Detektion "z.B.
//! über ... die Beutel-Zählung"): JEDER Post-Fill-Zustand mit leerem Turm
//! gilt als nicht eindeutig invertierbar und wird abgelehnt. Ein NICHTleerer
//! Turm ist dagegen immer eindeutig (komplett-oder-gar-nicht-Leerung s.o.),
//! `pre_tower = post_tower` ist dann exakt -- kein Datenverlust in diesem
//! Fall.
//!
//! Offene Einschränkung (dokumentiert statt still entschieden, siehe
//! Abschlussbericht): bei häufigen Rundenübergängen ist ein geleerter Turm
//! ab Runde 4/5 vermutlich KEIN Randfall mehr, sondern die Regel (nur 65
//! Fliesen für bis zu 105 Ziehungen über 5 Runden) -- die Ausschlussquote
//! aus dieser Regel kann daher hoch ausfallen. Das Vorregistrierungs-
//! Dokument verlangt ausdrücklich nur, die Quote zu berichten, keine
//! bestimmte Obergrenze.

use rand::rngs::StdRng;
use rand::seq::SliceRandom;
use rand::SeedableRng;

use crate::dome::BonusChip;
use crate::state::{
    fill_factories_for_resample, GameState, Phase, NUM_SMALL_FACTORIES, TILES_PER_LARGE_FACTORY,
    TILES_PER_SMALL_FACTORY,
};
use crate::tile::TileColor;

/// Validiert `state` als unberührten Runde-5-Start und liefert den
/// Vor-Befüllungs-Zustand zurück (Fabriken leer, Beutel/Bonuschip-Pool um
/// die entnommenen Plättchen/Chips ergänzt, Turm unverändert) -- bereit für
/// n-faches erneutes `state::fill_factories_for_resample`.
pub fn invert_round5_fill(state: &GameState) -> Result<GameState, String> {
    if state.round_number != 5 {
        return Err(format!(
            "resample_round_transition_json: erwartet round==5, war {}",
            state.round_number
        ));
    }
    if state.phase != Phase::Drafting {
        return Err(format!(
            "resample_round_transition_json: erwartet Phase::Drafting, war {:?}",
            state.phase
        ));
    }
    if state.factories.len() != NUM_SMALL_FACTORIES {
        return Err(format!(
            "resample_round_transition_json: erwartet {NUM_SMALL_FACTORIES} kleine Fabriken, waren {}",
            state.factories.len()
        ));
    }
    for f in &state.factories {
        if f.sun_tiles.len() != TILES_PER_SMALL_FACTORY {
            return Err(format!(
                "resample_round_transition_json: Fabrik {} hat {} Sonnenplättchen, erwartet {TILES_PER_SMALL_FACTORY} \
                 (angerissene/schon bespielte Fabrik -- kein unberührter Runde-5-Start)",
                f.factory_id,
                f.sun_tiles.len()
            ));
        }
        if !f.moon_stacks.is_empty() {
            return Err(format!(
                "resample_round_transition_json: Fabrik {} hat bereits Mond-Stapel -- kein unberührter Runde-5-Start",
                f.factory_id
            ));
        }
        if f.bonus_chip.is_none() {
            return Err(format!(
                "resample_round_transition_json: Fabrik {} hat keinen Bonuschip -- kein unberührter Runde-5-Start",
                f.factory_id
            ));
        }
        if f.bonus_chip_revealed {
            return Err(format!(
                "resample_round_transition_json: Fabrik {} hat den Bonuschip bereits aufgedeckt -- kein unberührter Runde-5-Start",
                f.factory_id
            ));
        }
    }
    if state.large_factory.sun_tiles.len() != TILES_PER_LARGE_FACTORY {
        return Err(format!(
            "resample_round_transition_json: große Fabrik hat {} Sonnenplättchen, erwartet {TILES_PER_LARGE_FACTORY}",
            state.large_factory.sun_tiles.len()
        ));
    }
    if !state.large_factory.moon_pool.is_empty() {
        return Err(
            "resample_round_transition_json: große Fabrik hat bereits einen Mond-Vorrat -- kein unberührter Runde-5-Start"
                .to_string(),
        );
    }
    if !state.large_factory.has_first_player_marker {
        return Err(
            "resample_round_transition_json: Startspielerplättchen der großen Fabrik bereits vergeben -- \
             kein unberührter Runde-5-Start"
                .to_string(),
        );
    }

    // Turm-Reshuffle-Grenzfall, s.o. Moduldoku.
    if state.tower.is_empty() {
        return Err(
            "resample_round_transition_json: Turm ist im Post-Fill-Zustand leer -- die Befüllung ist nicht \
             eindeutig invertierbar (Turm-Reshuffle-Grenzfall, siehe PREREG_r4_value_calibration.md, \
             'Bekannte Einschränkungen')"
                .to_string(),
        );
    }

    let mut pre = state.clone();

    // Entnommene Sonnenplättchen + Bonuschips sammeln, BEVOR die Fabriken
    // zurückgesetzt werden -- absichtlich in zwei Schritten (erst sammeln,
    // dann erst in bag/bonus_chip_pool einfügen), damit kein gleichzeitiger
    // mutable-borrow von `pre.factories` UND `pre.bag`/`pre.bonus_chip_pool`
    // nötig ist.
    let mut returned_sun_tiles: Vec<TileColor> = Vec::new();
    let mut returned_chips: Vec<BonusChip> = Vec::new();
    for f in pre.factories.iter_mut() {
        returned_sun_tiles.append(&mut f.sun_tiles);
        if let Some(chip) = f.bonus_chip.take() {
            returned_chips.push(chip);
        }
        f.bonus_chip_revealed = false;
    }
    returned_sun_tiles.append(&mut pre.large_factory.sun_tiles);
    // Marker/monochrome_fallback/moon_pool wie beim echten Rundenwechsel
    // (`state.rs::setup_new_round`) VOR der (Re-)Befüllung zurücksetzen.
    pre.large_factory.reset_for_new_round();

    pre.bag.tiles.append(&mut returned_sun_tiles);
    pre.bonus_chip_pool.append(&mut returned_chips);

    Ok(pre)
}

/// Invertiert `r5_start` (siehe [`invert_round5_fill`]) und befüllt daraus
/// `n_samples`-mal frisch -- je Sample ein deterministisch aus `seed` +
/// Sample-Index abgeleiteter RNG (`StdRng::seed_from_u64`).
///
/// `Bag::draw`/`bonus_chip_pool.pop()` ziehen nur vom Anfang/Ende des Vecs
/// (kein Mischen inline) -- `pre.bag`/`pre.bonus_chip_pool` selbst sind nach
/// [`invert_round5_fill`] NICHT gemischt (die zurückgelegten Plättchen/Chips
/// wurden einfach angehängt). Ohne ein Neumischen JE Sample würde
/// `fill_factories_for_resample` also für JEDEN Sample-Index aus einem Klon
/// derselben, bereits feststehenden Reihenfolge ziehen -- der `rng`-Seed
/// hätte dann (solange kein Turm-Refill einsetzt) gar keinen Effekt. Gleiches
/// Muster wie `round_transition.rs::sample_round_transition_value`/
/// `advance_one_chance` (dortiger Kommentar): Beutel + Bonuschip-Pool werden
/// mit demselben Sample-RNG neu gemischt, das anschließend auch die
/// Befüllung selbst treibt.
pub fn resample_round5_start(
    r5_start: &GameState,
    n_samples: u32,
    seed: u64,
) -> Result<Vec<GameState>, String> {
    let pre = invert_round5_fill(r5_start)?;
    let mut out = Vec::with_capacity(n_samples as usize);
    for i in 0..n_samples {
        let mut rng = StdRng::seed_from_u64(seed.wrapping_add(i as u64));
        let mut sample = pre.clone();
        sample.bag.tiles.shuffle(&mut rng);
        sample.bonus_chip_pool.shuffle(&mut rng);
        fill_factories_for_resample(&mut sample, &mut rng);
        out.push(sample);
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::round5;
    use crate::round_transition::drive_to_round_start;

    /// Echter Runde-5-Start über die Engine (Memory
    /// `feedback_check_existing_tools_first`: `drive_to_round_start` existiert
    /// bereits in `round_transition.rs`, kein neuer Test-Fixture-Aufbau nötig).
    fn r5_start(seed: u64) -> GameState {
        drive_to_round_start(seed, 5)
    }

    /// Farb-Zählvektor (Reihenfolge `TileColor::NORMAL`) über bag + tower +
    /// alle Fabrik-Sonnenplättchen -- der Teil des Spielzustands, den
    /// invert+resample tatsächlich umschichten. Der Turm ist bei einem
    /// eindeutig invertierbaren Zustand (s.o. Grenzfall-Ablehnung)
    /// unverändert, wird hier trotzdem mitgezählt (strengerer, aber
    /// weiterhin korrekter Test).
    fn tile_signature(state: &GameState) -> [usize; 5] {
        let mut counts = [0usize; 5];
        let mut bump = |t: TileColor| {
            if let Some(i) = TileColor::NORMAL.iter().position(|&c| c == t) {
                counts[i] += 1;
            }
        };
        for &t in &state.bag.tiles {
            bump(t);
        }
        for &t in &state.tower.tiles {
            bump(t);
        }
        for f in &state.factories {
            for &t in &f.sun_tiles {
                bump(t);
            }
        }
        for &t in &state.large_factory.sun_tiles {
            bump(t);
        }
        counts
    }

    fn factory_signature(state: &GameState) -> Vec<String> {
        let mut sig: Vec<String> = state
            .factories
            .iter()
            .map(|f| f.sun_tiles.iter().map(|t| t.value().to_string()).collect::<Vec<_>>().join(","))
            .collect();
        sig.push(state.large_factory.sun_tiles.iter().map(|t| t.value().to_string()).collect::<Vec<_>>().join(","));
        sig
    }

    /// Sucht unter mehreren Seeds einen r5-Start, dessen Turm NICHT leer ist
    /// (nur solche sind laut Grenzfall-Regel eindeutig invertierbar) --
    /// mehrere Seeds ausprobieren, damit der Test nicht zufällig auf einen
    /// ausgeschlossenen Zustand trifft.
    fn r5_start_with_nonempty_tower() -> GameState {
        for seed in 0..200u64 {
            let s = r5_start(seed);
            if !s.tower.is_empty() {
                return s;
            }
        }
        panic!("kein r5-Start mit nichtleerem Turm unter den ersten 200 Seeds gefunden -- Grenzfall-Annahme prüfen");
    }

    #[test]
    fn tile_conservation_before_and_after_resample() {
        let leaf = r5_start_with_nonempty_tower();
        let before = tile_signature(&leaf);

        let samples = resample_round5_start(&leaf, 6, 1234).expect("invertierbar");
        assert_eq!(samples.len(), 6);
        for s in &samples {
            assert_eq!(
                tile_signature(s),
                before,
                "Plättchen-Multiset (Beutel+Turm+Fabriken) muss vor Inversion und nach jedem Resample identisch sein"
            );
        }
    }

    #[test]
    fn determinism_same_seed_identical_different_seed_varies() {
        let leaf = r5_start_with_nonempty_tower();

        let a = resample_round5_start(&leaf, 4, 42).expect("invertierbar");
        let b = resample_round5_start(&leaf, 4, 42).expect("invertierbar");
        let sig_a: Vec<Vec<String>> = a.iter().map(factory_signature).collect();
        let sig_b: Vec<Vec<String>> = b.iter().map(factory_signature).collect();
        assert_eq!(sig_a, sig_b, "gleicher seed muss identische Fabrik-Belegung liefern");

        let c = resample_round5_start(&leaf, 4, 43).expect("invertierbar");
        let sig_c: Vec<Vec<String>> = c.iter().map(factory_signature).collect();
        assert_ne!(
            sig_a, sig_c,
            "verschiedene seeds sollten (bei n_samples=4) nicht dieselbe Fabrik-Belegung ergeben"
        );
    }

    #[test]
    fn each_resample_is_a_valid_round5_drafting_start() {
        let leaf = r5_start_with_nonempty_tower();
        let samples = resample_round5_start(&leaf, 5, 7).expect("invertierbar");
        for s in &samples {
            assert_eq!(s.round_number, 5);
            assert_eq!(s.phase, Phase::Drafting);
            assert!(round5::applies(s), "round5::applies muss für jeden Resample-Zustand true sein");
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
    fn rejects_non_round5_state() {
        let mut s = r5_start_with_nonempty_tower();
        s.round_number = 4;
        assert!(invert_round5_fill(&s).is_err());
    }

    #[test]
    fn rejects_non_drafting_phase() {
        let mut s = r5_start_with_nonempty_tower();
        s.phase = Phase::Tiling;
        assert!(invert_round5_fill(&s).is_err());
    }

    #[test]
    fn rejects_torn_factory() {
        let mut s = r5_start_with_nonempty_tower();
        // Eine Fabrik "angerissen": ein Plättchen bereits genommen (3 statt 4).
        s.factories[0].sun_tiles.pop();
        assert!(invert_round5_fill(&s).is_err());
    }

    #[test]
    fn rejects_empty_tower_as_ambiguous_reshuffle_case() {
        let mut s = r5_start_with_nonempty_tower();
        s.tower.tiles.clear();
        let err = invert_round5_fill(&s).expect_err("leerer Turm muss abgelehnt werden");
        assert!(err.contains("Turm"), "Fehlermeldung sollte den Turm-Grenzfall benennen: {err}");
    }
}
