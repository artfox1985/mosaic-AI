//! Spiegelknopf (`evaluations/PREREG_tie_mirror.md`, Nutzer-Entscheid
//! 2026-09-26: *"Ja bau den spiegelknopf ein. Sollte dann 50:50 Aufteilung
//! sein im self play"*).
//!
//! ANLASS: Self-Play und Arena bauen volle Spalten nur links (c0/c1), obwohl
//! das Brett bis auf Gleichstandsregeln links-rechts-symmetrisch bewertet wird.
//! Zwei solche Regeln entscheiden deterministisch fuer LINKS:
//!
//! 1. die Huellenwahl `envelope.rs` (`best_hull_in`, `best_hull_frac_in`,
//!    `envelope_score_row6_in`): bei gleicher Abweichung gewinnt `Hull::Left`.
//!    Fruehe Bretter mit Steinen nur in Rasterzeile 0 liegen in BEIDEN
//!    Huellen, der Gleichstand ist dort der Normalfall -- die Suche
//!    (Such-Term (e), `SearchConfig::envelope_search_c`) bewertet dann ab
//!    Runde 1 den linken Aufbau hoeher und legt die Kuppelplatten links. Das
//!    ist der tragende Hebel (Koordinator-Praezisierung 2026-09-26; Herleitung
//!    aus dem Code, nicht gemessen -- Einzelheiten bei `envelope::pick_hull`).
//! 2. die Tiling-Wahl `tiling_solver.rs`: die Kandidaten entstehen in
//!    `generate_tiling_actions` mit Slot-Spalte aufsteigend, und jeder
//!    Waehler uebernimmt nur bei strikt besserem Wert -- bei Gleichstand
//!    gewinnt die linke Zelle.
//!
//! BAU: EINE Muenze je Partie, abgeleitet aus dem Partie-Seed (eigener
//! Distinguisher, der Partie-RNG wird NICHT verbraucht, Muster
//! `PREREG_search_rng_split.md`). Faellt sie, ist die Partie "gespiegelt":
//! ein THREAD-LOKALER Schalter ([`set_game_tie_mirror`]) kippt beide
//! Gleichstandsregeln nach RECHTS. Gesetzt wird er ausschliesslich in
//! `self_play.rs::run_net_self_play`, im Thread der Partie (und im Thread des
//! Ausflugs, der denselben Wert uebernimmt). Heuristik-, Arena-, Referee- und
//! GUI-Pfade setzen ihn NIE; dort bleibt er `false`, also Bestand.
//!
//! WARUM THREAD-LOKAL (gleiche Bauform wie `plate_builder::set_game_seed` und
//! `shaping::set_game_shaping_weight`): der Schalter wird an Stellen gelesen,
//! deren Signaturen oeffentlich und vielfach aufgerufen sind (Huellen-
//! Funktionen, Tiling-Waehler, Rundenuebergang in der Suche). Ein Parameter
//! haette jede dieser Signaturen geaendert. `run_with_watchdog` spawnt je
//! Partie einen FRISCHEN Thread; ein Leck in eine Folgepartie ist dort
//! strukturell ausgeschlossen.
//!
//! DEFAULT AUS = BYTE-IDENTISCH: `MOSAIC_TIE_MIRROR_P` ungesetzt heisst
//! `p = 0.0`, die Muenze wird dann gar nicht erst geworfen (Fruehausstieg in
//! [`tie_mirror_coin`]), der Schalter bleibt `false`, und es wird KEIN
//! Record-Feld geschrieben ([`tie_mirrored_field`]).

use serde_json::{json, Value};
use std::cell::Cell;

/// Stromindex der Spiegel-Muenze (`PREREG_search_rng_split.md`-Muster:
/// `derive_search_seed(game_seed ^ DISTINGUISHER, COUNTER)`). EIGENER Wert,
/// verschieden von allen Distinguishern im Baum (Stand 2026-09-26:
/// `RETURN_ORDER_SEED_DISTINGUISHER`, `RETURN_ORDER_NODE_SEED_DISTINGUISHER`,
/// `DEVIATE_SEED_DISTINGUISHER`, `EXCURSION_SEED_DISTINGUISHER`,
/// `MOON_ORDER_SEARCH_SEED_DISTINGUISHER`,
/// `ROUND_TRANSITION_LEAF_SEED_DISTINGUISHER` und die lokale Konstante in
/// `self_play.rs::asym_preference_side`) -- ein geteilter Wert koppelte die
/// Muenze an einen anderen Entscheid derselben Partie.
pub(crate) const TIE_MIRROR_SEED_DISTINGUISHER: u64 = 0x71E3_A1B0_5EED_C0DE;

/// Zaehler-Argument der Muenze. Es gibt genau EINEN Wurf je Partie, der Wert
/// ist darum beliebig; die Trennung von anderen Stroemen leistet der
/// Distinguisher.
const TIE_MIRROR_COIN_COUNTER: u64 = 0;

/// Name des Record-Felds (additiv, nur bei `p > 0`).
pub(crate) const TIE_MIRRORED_FIELD: &str = "tie_mirrored";

thread_local! {
    /// Ist die Partie DIESES Threads gespiegelt? `false` = Bestand.
    static GAME_TIE_MIRROR: Cell<bool> = Cell::new(false);
}

/// Setzt den Spiegel-Schalter der Partie auf DIESEM Thread. Nur
/// `self_play.rs::run_net_self_play` ruft das (Hauptpartie und Ausflug, beide
/// in einem frisch gespawnten Watchdog-Thread).
pub(crate) fn set_game_tie_mirror(on: bool) {
    GAME_TIE_MIRROR.with(|c| c.set(on));
}

/// Liest den Spiegel-Schalter der Partie auf DIESEM Thread. Die Leser sind
/// [`crate::envelope::pick_hull`] (Huellen-Gleichstand) und die
/// Kandidaten-Reihenfolge des echten Tiling-Zugs in `tiling_solver.rs`.
#[inline]
pub(crate) fn game_tie_mirror() -> bool {
    GAME_TIE_MIRROR.with(|c| c.get())
}

/// Gueltigkeitspruefung von `MOSAIC_TIE_MIRROR_P` -- `None` = ungueltig.
/// Eigene reine Funktion (Muster `self_play.rs::sanitize_start_slot_random_p`),
/// damit die Pruefung ohne den prozessweiten Cache testbar bleibt.
fn sanitize_tie_mirror_p(raw: f64) -> Option<f64> {
    (0.0..=1.0).contains(&raw).then_some(raw)
}

/// Erzeugungsknopf `MOSAIC_TIE_MIRROR_P`: Wahrscheinlichkeit JE PARTIE, dass
/// die Gleichstandsregeln nach rechts kippen. `0.5` ist die vom Nutzer
/// gewollte 50:50-Aufteilung.
///
/// Default `0.0` = AUS = byte-identisch (siehe Modulkopf). Ausserhalb `[0,1]`
/// -> Default mit EINMALIGER Warnung (OnceLock), kein Panik-Abbruch -- gleiche
/// Disziplin wie `self_play.rs::start_slot_random_p`. Prozessweit gecacht:
/// die Variable MUSS vor dem ersten Lesen gesetzt sein.
pub(crate) fn tie_mirror_p() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| {
        let raw = crate::net_mcts::read_f64_env("MOSAIC_TIE_MIRROR_P", 0.0);
        sanitize_tie_mirror_p(raw).unwrap_or_else(|| {
            eprintln!(
                "⚠️  MOSAIC_TIE_MIRROR_P={raw} liegt nicht in [0,1] -- Spiegelknopf bleibt AUS (0.0)."
            );
            0.0
        })
    })
}

/// Bildet einen `u64` gleichverteilt auf `[0, 1)` ab (obere 53 Bit, exakt als
/// `f64` darstellbar). Kein RNG-Objekt noetig: `derive_search_seed` ist
/// bereits ein SplitMix64-Finalizer.
#[inline]
fn unit_from_u64(x: u64) -> f64 {
    (x >> 11) as f64 * (1.0 / (1u64 << 53) as f64)
}

/// DIE Muenze als reine Funktion: gespiegelt genau dann, wenn die aus
/// `game_seed` abgeleitete Zahl `u` in `[0, 1)` kleiner als `p` ist.
///
/// Vertrag: bei `p <= 0.0` (oder NaN) Fruehausstieg mit `false`, ohne jede
/// Rechnung -- das ist die Bitidentitaets-Bedingung des Knopfs. Bei
/// `p >= 1.0` immer `true` (`u < 1`). Deterministisch: gleicher Seed, gleiche
/// Muenze; der Partie-RNG wird nicht beruehrt.
pub(crate) fn tie_mirror_coin(p: f64, game_seed: u64) -> bool {
    if !(p > 0.0) {
        return false;
    }
    let seed = crate::shaping::derive_search_seed(
        game_seed ^ TIE_MIRROR_SEED_DISTINGUISHER,
        TIE_MIRROR_COIN_COUNTER,
    );
    unit_from_u64(seed) < p
}

/// Additives Record-Feld: `None` bei `p <= 0` (kein Feld, der Record bleibt
/// byte-gleich zum Bestand und die Netz-Paritaets-Fixture unberuehrt), sonst
/// `Some(true/false)` -- bei aktivem Knopf traegt JEDER Record das Feld, auch
/// die ungespiegelten, damit eine Sonde die beiden Arme ohne Vermutung ueber
/// ein fehlendes Feld trennen kann.
pub(crate) fn tie_mirrored_field(p: f64, mirrored: bool) -> Option<Value> {
    (p > 0.0).then(|| json!(mirrored))
}

/// Stempelt [`TIE_MIRRORED_FIELD`] in jeden Record einer Partie (Hauptpartie
/// oder Ausflug). Bei `p <= 0` passiert nichts.
pub(crate) fn stamp_tie_mirrored(records: &mut [Value], p: f64, mirrored: bool) {
    let Some(v) = tie_mirrored_field(p, mirrored) else { return };
    for rec in records.iter_mut() {
        if let Some(m) = rec.as_object_mut() {
            m.insert(TIE_MIRRORED_FIELD.into(), v.clone());
        }
    }
}

/// Test-Helfer: setzt den Schalter fuer die Lebensdauer des Waechters und
/// stellt den vorherigen Wert beim Verlassen wieder her (auch bei Panik), damit
/// kein Test den Zustand in einen Folgetest desselben Threads leckt.
#[cfg(test)]
pub(crate) struct TieMirrorGuard {
    previous: bool,
}

#[cfg(test)]
impl TieMirrorGuard {
    pub(crate) fn set(on: bool) -> Self {
        let previous = game_tie_mirror();
        set_game_tie_mirror(on);
        TieMirrorGuard { previous }
    }
}

#[cfg(test)]
impl Drop for TieMirrorGuard {
    fn drop(&mut self) {
        set_game_tie_mirror(self.previous);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn tie_mirror_p_accepts_only_probabilities() {
        for ok in [0.0, 0.25, 0.5, 1.0] {
            assert_eq!(sanitize_tie_mirror_p(ok), Some(ok), "{ok} ist gueltig");
        }
        for bad in [-0.1, 1.5, f64::NAN, f64::INFINITY] {
            assert_eq!(sanitize_tie_mirror_p(bad), None, "{bad} darf nicht durchgehen");
        }
    }

    #[test]
    fn tie_mirror_p_is_off_by_default() {
        // Der Test-Prozess setzt die Variable nicht; ungesetzt heisst AUS.
        if std::env::var_os("MOSAIC_TIE_MIRROR_P").is_none() {
            assert_eq!(tie_mirror_p(), 0.0, "ungesetzt muss der Knopf 0.0 (= AUS) sein");
        }
    }

    #[test]
    fn coin_never_at_zero_always_at_one() {
        for seed in 0..2_000u64 {
            assert!(!tie_mirror_coin(0.0, seed), "p = 0 darf nie spiegeln (Seed {seed})");
            assert!(!tie_mirror_coin(-1.0, seed), "p < 0 darf nie spiegeln (Seed {seed})");
            assert!(!tie_mirror_coin(f64::NAN, seed), "NaN darf nie spiegeln (Seed {seed})");
            assert!(tie_mirror_coin(1.0, seed), "p = 1 muss immer spiegeln (Seed {seed})");
        }
    }

    /// Bei p = 0,5 ueber 10.000 Partie-Seeds etwa die Haelfte. Standardfehler
    /// sqrt(0,25 / 10.000) = 0,005; das Fenster 0,48..0,52 sind 4 Standardfehler.
    #[test]
    fn coin_at_half_splits_about_evenly() {
        let n = 10_000u64;
        // Partie-Seeds wie in `run_net_self_play`: Basis + i * goldener Schnitt.
        let base = 42u64;
        let hits = (0..n)
            .filter(|&i| tie_mirror_coin(0.5, base.wrapping_add(i.wrapping_mul(0x9E37_79B9_7F4A_7C15))))
            .count();
        let share = hits as f64 / n as f64;
        assert!((0.48..=0.52).contains(&share), "Anteil gespiegelt {share} bei p = 0,5");
    }

    #[test]
    fn coin_is_deterministic_per_seed() {
        for seed in [0u64, 1, 7, 12_345, u64::MAX] {
            assert_eq!(tie_mirror_coin(0.5, seed), tie_mirror_coin(0.5, seed));
        }
        // Monoton in p: wer bei p spiegelt, spiegelt auch bei jedem groesseren p.
        for seed in 0..500u64 {
            if tie_mirror_coin(0.3, seed) {
                assert!(tie_mirror_coin(0.7, seed), "Seed {seed}: Muenze nicht monoton in p");
            }
        }
    }

    #[test]
    fn record_field_only_when_knob_is_on() {
        assert_eq!(tie_mirrored_field(0.0, false), None);
        assert_eq!(tie_mirrored_field(0.0, true), None, "p = 0 schreibt nie ein Feld");
        assert_eq!(tie_mirrored_field(0.5, false), Some(json!(false)));
        assert_eq!(tie_mirrored_field(0.5, true), Some(json!(true)));

        let mut off = vec![json!({"a": 1}), json!({"b": 2})];
        let before = off.clone();
        stamp_tie_mirrored(&mut off, 0.0, true);
        assert_eq!(off, before, "p = 0 muss die Records byte-gleich lassen");

        let mut on = vec![json!({"a": 1}), json!({"b": 2})];
        stamp_tie_mirrored(&mut on, 0.5, true);
        for rec in &on {
            assert_eq!(rec.get(TIE_MIRRORED_FIELD), Some(&json!(true)));
        }
    }

    #[test]
    fn guard_restores_previous_state() {
        assert!(!game_tie_mirror(), "Default auf einem frischen Test-Thread ist AUS");
        {
            let _g = TieMirrorGuard::set(true);
            assert!(game_tie_mirror());
        }
        assert!(!game_tie_mirror(), "Waechter muss zuruecksetzen");
    }
}
