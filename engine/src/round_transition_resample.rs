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
//! **BEFUND 2026-08-03 (Koordinator, volles v19-Korpus, 9000 Partien):** die
//! oben als "offene Einschränkung" benannte Vermutung war korrekt und
//! gravierender als angenommen -- **87,6 % der echten Runde-5-Starts haben
//! einen leeren Turm** (der frühere Verdacht auf 0 % war ein Messfehler:
//! `tower_colors` ist ein Farb-ZÄHL-Array, "leer" heißt Summe==0, nicht
//! `len()==0` -- ein leeres Array `[0,0,0,0,0]` hat trotzdem `len()==5`).
//! Die konservative Ausschlussregel dieses Moduls würde also fast das ganze
//! Substrat verwerfen. `invert_round5_fill`/`resample_round5_start` BLEIBEN
//! deshalb als bereits committeter, weiterhin korrekter Baustein bestehen
//! (der 12,4%-Rest mit nichtleerem Turm ist nach wie vor exakt invertierbar),
//! aber der PREREG-r4-Pfad selbst nutzt ab jetzt NICHT mehr diese Inversion,
//! sondern das VORWÄRTS-Binding [`autoplay_to_round5_and_resample`] weiter
//! unten -- das umgeht die Turm-Ambiguität komplett, weil es beim echten
//! Runde-4-Zustand (Beutel/Turm dort noch als EXAKTE Multisets bekannt,
//! keine Zähler-Rekonstruktion nötig) ansetzt, statt beim bereits befüllten
//! Runde-5-Start rückwärts zu rechnen.

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

// ═══════════════════════════════════════════════════════════════════════════
// Vorwärts-Pfad (2026-08-03, ersetzt die Inversion für den PREREG-r4-Pfad):
// autoplay_to_round5_and_resample
// ═══════════════════════════════════════════════════════════════════════════

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

    // ═══════════════════════════════════════════════════════════════════════
    // Vorwärts-Pfad: autoplay_to_round5_and_resample
    // ═══════════════════════════════════════════════════════════════════════

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
