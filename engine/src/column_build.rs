//! Spaltenbau-Spieler (Diagnose-/Korpus-Knopf `MOSAIC_SPALTENBAU`) --
//! Entscheidungsschicht UEBER dem Netzspieler, die gezielt EINE
//! Wertungsplatten-Spalte je Partie schliessen soll (Nutzer-Auftrag
//! 2026-08-13, siehe `evaluations/PREREG_provocation.md` §9 fuer die
//! Vorgeschichte: vier Mechanismen -- Injektion, Beschneidung, Vorzug-
//! Drafting, Vorzug-Drafting+Tiling -- enden alle bei 0,30 Spalten/Partie,
//! die 5/6-Mauer haelt in 9-13 von 20 Partien).
//!
//! Baut auf der EINZIGEN Linie, die dabei das Spiel intakt liess --
//! `provocation.rs`s "Vorzugszug: Praeferenz statt Verbot" -- und erweitert
//! sie um zwei Stellen, die dort noch NICHTS steuert:
//!
//!  1. [`vorzug_dome_wahl`]: die Kuppelplatten-Wahl (welche Platte, welcher
//!     Slot, welche Rotation) bestimmt `required_color` der Zellen -- bisher
//!     nie gesteuert (§9 selbst listet nur Drafting- und Tiling-Mechanismen).
//!  2. [`ziel_spalte`]: die Ziel-Spalte wird JE ENTSCHEID frisch aus dem
//!     aktuellen Brettzustand bestimmt (vorhandene Platten, Wild-/Special-
//!     Zellen, schon gefuellte Zellen, blockierte Musterreihen) statt fest
//!     0..5 zu sein. RUNDE 4 (§14) fuegt EIN Sicherheitsnetz DARUeBER hinzu
//!     ([`ist_spalte_vollendbar`]): ist die naturgemaess billigste Spalte
//!     gerade unvollendbar (eine offene Zeile braucht mehr Kopien einer
//!     Farbe, als noch erreichbar sind), wird auf die beste VOLLENDBARE
//!     Alternative ausgewichen -- eine FRUEHERE Fassung hielt die Spalte
//!     stattdessen ueber mehrere Entscheidungen persistent fest ("Wechsel
//!     nur bei Unvollendbarkeit") und wurde nach VIER vollen 20-Seed-
//!     Messungen wieder verworfen: die Bindung nahm der Kosten-Formel
//!     genau die Reaktionsfaehigkeit, die schon in Runde 1-3 funktionierte
//!     (0,70-2,45 statt 5,95 vertikale Punkte, siehe §14).
//!
//! [`vorzugszug`] (Stein-Zuege) ist eine duenne Huelle um
//! `provocation::vorzugszug_fuer_spalte` mit der dynamischen Spalte statt
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
//! RUNDE 4 (PREREG_provocation.md §14) fuegt zwei weitere Bausteine hinzu:
//! [`ist_spalte_vollendbar`]/[`waehle_beste_vollendbare_spalte`] (Vollendbar-
//! keits-Sicherheitsnetz mit Zielwechsel) und [`ueberpraesenz_vorzug`]
//! (Material-zuerst-Drafting, GEBAUT+GEMESSEN, aber NICHT verkettet -- brach
//! die Netz-Staerke auf 2/20 ein, siehe Kommentar in `vorzugszug`). Die
//! Kuppelwahl ([`zellen_wert`]) kann einen "Jackpot" (Zelle fordert exakt die
//! Farbe, die ihre Musterreihe schon fuehrt) dominant ueber Wild gewichten.
//!
//! §15 (Entkonfundierung, Koordinator-Auftrag 2026-08-13): Sicherheitsnetz
//! und Jackpot sind seither je ein EIGENER Diagnose-Knopf
//! (`MOSAIC_SPALTENBAU_SICHERHEITSNETZ`/`MOSAIC_SPALTENBAU_JACKPOT`,
//! [`sicherheitsnetz_aktiv`]/[`jackpot_aktiv`]), **Default AUS** -- keiner der
//! vier 2x2-Arme (Sicherheitsnetz x Jackpot) uebertraf auf denselben 20
//! k1-Seeds die Runde-3-Abnahme (5,95), also bleibt die Runde-3-Konfiguration
//! per Vorab-Regel der aktive Stand. Beide Bausteine bleiben im Code (per
//! Opt-in `=1` einschaltbar), sind aber NICHT mehr Default-Verhalten.
//!
//! DEFAULT AUS -> jede Funktion hier ist ein No-Op; alle Aufrufstellen
//! bleiben `.or_else(...)`-verkettet, byte-identisch zum Bestand ohne den
//! Knopf (gleiches Muster wie `provocation.rs`/`MOSAIC_VORZUG_SPALTE`).

use crate::board::PlayerBoard;
use crate::dome::{rotation_indices, DomeSpace, DomeTile, SpaceType};
use crate::moves::{Action, PendingDomeChoice, PlaceDomeTileMove};
use crate::state::GameState;
use crate::tile::TileColor;
use crate::tiling_solver::TilingStep;

/// Liest `MOSAIC_SPALTENBAU` einmalig (Prozess-Cache, gleiches Muster wie
/// `provocation::modus_env`). Jeder nicht-leere Wert ausser `"0"` schaltet
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

// Test-Override -- gleiches Muster wie `provocation::MODUS_OVERRIDE`: ein
// `OnceLock` waere sonst prozessweit fuer ALLE parallelen `cargo test`-
// Threads fixiert, sobald der erste Test ihn liest.
#[cfg(test)]
thread_local! {
    static AKTIV_OVERRIDE: std::cell::Cell<Option<bool>> = const { std::cell::Cell::new(None) };
}

#[cfg(test)]
pub(crate) fn set_aktiv_override_for_test(v: Option<bool>) {
    AKTIV_OVERRIDE.with(|c| c.set(v));
    // Runde 4: LETZTER_WECHSEL/LETZTER_JACKPOT sind Entscheidungs-Zustand
    // (kein Partie-Zustand mehr seit dem Verwurf der Zielspalten-Bindung,
    // siehe Moduldoku) -- `cargo test` teilt Worker-Threads zwischen Tests,
    // ein `thread_local!` ueberlebt das also. Ohne Reset hier koennte ein
    // Wechsel-/Jackpot-Vermerk eines VORIGEN Tests in den naechsten lecken.
    LETZTER_WECHSEL.with(|c| c.set(None));
    LETZTER_JACKPOT.with(|c| c.set(false));
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

// ── §15: Diagnose-Knoepfe zur Entkonfundierung von Baustein 1 (Sicherheits-
// netz) und Baustein 3a (Jackpot) -- Koordinator-Auftrag 2026-08-13, NICHT
// im Gating verwendet (Vorgabe: "Diagnose-Knoepfe sind erlaubt, nie in
// Gating"). POLARITAET NACH DER ENTKONFUNDIERUNGS-MESSUNG UMGEDREHT (§15,
// Vorab-Regel des Koordinators: "kein Arm > 5,95 -> Runde-3-Konfiguration
// bleibt der aktive Stand, Knoepfe default AUS"): unset -> BEIDE Bausteine
// AUS (reiner Runde-3-Stand, §11/§12), `=1` (oder jeder Wert ausser leer/`0`)
// schaltet den jeweiligen Baustein PER OPT-IN wieder ein -- fuer eine
// spaetere Fassung, die die 5,95-Schwelle tatsaechlich uebertrifft.

/// `MOSAIC_SPALTENBAU_SICHERHEITSNETZ=1` schaltet Baustein 1 (Vollendbarkeits-
/// Filter in [`ziel_spalte_fuer_player`]) EIN -- Default (unset) ist seit §15
/// AUS: die Zielspalte ist dann die reine Kostenwahl aus Runde 1-3, ohne jede
/// Vollendbarkeits-Pruefung (§15-Messung: 3,15 vs. 3,15 mit Filter -- kein
/// messbarer Unterschied auf den 20 k1-Seeds, siehe PREREG_provocation.md §15).
fn sicherheitsnetz_env() -> bool {
    static CELL: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| match std::env::var("MOSAIC_SPALTENBAU_SICHERHEITSNETZ") {
        Err(_) => false,
        Ok(raw) => {
            let v = raw.trim();
            !v.is_empty() && v != "0"
        }
    })
}

/// `MOSAIC_SPALTENBAU_JACKPOT=1` schaltet Baustein 3a (die dominante
/// Jackpot-Gewichtung in [`zellen_wert`]) EIN -- Default (unset) ist seit §15
/// AUS: eine Zelle, deren Musterreihe schon die geforderte Farbe fuehrt,
/// bewertet dann mit dem Runde-3-Wert 2,5 statt [`JACKPOT_WERT`] (4,0)
/// (§15-Messung: +0,70 Plattenpunkte mit Jackpot, t=0,81, NICHT signifikant
/// bei n=20).
fn jackpot_env() -> bool {
    static CELL: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| match std::env::var("MOSAIC_SPALTENBAU_JACKPOT") {
        Err(_) => false,
        Ok(raw) => {
            let v = raw.trim();
            !v.is_empty() && v != "0"
        }
    })
}

#[cfg(test)]
thread_local! {
    static SICHERHEITSNETZ_OVERRIDE: std::cell::Cell<Option<bool>> = const { std::cell::Cell::new(None) };
    static JACKPOT_OVERRIDE: std::cell::Cell<Option<bool>> = const { std::cell::Cell::new(None) };
}

#[cfg(test)]
pub(crate) fn set_sicherheitsnetz_override_for_test(v: Option<bool>) {
    SICHERHEITSNETZ_OVERRIDE.with(|c| c.set(v));
}

#[cfg(test)]
pub(crate) fn set_jackpot_override_for_test(v: Option<bool>) {
    JACKPOT_OVERRIDE.with(|c| c.set(v));
}

fn sicherheitsnetz_aktiv() -> bool {
    #[cfg(test)]
    {
        if let Some(v) = SICHERHEITSNETZ_OVERRIDE.with(|c| c.get()) {
            return v;
        }
    }
    sicherheitsnetz_env()
}

fn jackpot_aktiv() -> bool {
    #[cfg(test)]
    {
        if let Some(v) = JACKPOT_OVERRIDE.with(|c| c.get()) {
            return v;
        }
    }
    jackpot_env()
}

/// §16 (Special-Zellen-Baustein, Koordinator-Auftrag 2026-08-13):
/// `MOSAIC_SPALTENBAU_SPECIAL=1` schaltet die geometrie-genaue
/// Special-Kosten/Vollendbarkeit/Vorzugs-Erweiterung ein -- Default (unset)
/// ist AUS, gleiches Muster wie [`sicherheitsnetz_env`]/[`jackpot_env`]
/// (§15: neue Bausteine starten als Diagnose-Knopf, nie im Gating, bis eine
/// Messung sie freigibt).
fn special_env() -> bool {
    static CELL: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| match std::env::var("MOSAIC_SPALTENBAU_SPECIAL") {
        Err(_) => false,
        Ok(raw) => {
            let v = raw.trim();
            !v.is_empty() && v != "0"
        }
    })
}

#[cfg(test)]
thread_local! {
    static SPECIAL_OVERRIDE: std::cell::Cell<Option<bool>> = const { std::cell::Cell::new(None) };
}

#[cfg(test)]
pub(crate) fn set_special_override_for_test(v: Option<bool>) {
    SPECIAL_OVERRIDE.with(|c| c.set(v));
}

fn special_aktiv() -> bool {
    #[cfg(test)]
    {
        if let Some(v) = SPECIAL_OVERRIDE.with(|c| c.get()) {
            return v;
        }
    }
    special_env()
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
/// je Entscheid vorberechnet, siehe [`crate::provocation::verbleibende_farben`])
/// -- keine Suche, kein Blick in Beutel/Turm selbst -- daher weiterhin O(6) je
/// Spalte (die Special-Nachbarpruefung ist selbst O(1), feste 2x2-Slot-Geometrie).
pub(crate) fn spalten_kosten(player: &PlayerBoard, spalte: usize, verbleibend: &[i64; 5]) -> f64 {
    (0..6usize).map(|r| zelle_kosten(player, r, spalte, verbleibend)).sum()
}

/// Kosten EINER Zelle -- die per-Zeile-Formel aus [`spalten_kosten`], aber
/// fuer ein beliebiges `(r, c)` statt nur `(r, spalte)`. §16 (Special-
/// Zellen-Baustein): dieselbe Funktion, die `spalten_kosten` fuer die
/// Zielspalte selbst aufruft, wird jetzt AUCH auf die Slot-Nachbarn einer
/// offenen Special-Zelle angewandt (siehe [`special_kosten`]) -- die
/// Nachbarn brauchen dieselbe Kostenrechnung wie jede andere Zelle,
/// unabhaengig davon, in welcher Spalte sie liegen.
pub(crate) fn zelle_kosten(player: &PlayerBoard, r: usize, c: usize, verbleibend: &[i64; 5]) -> f64 {
    match player.dome_grid.get_space(r, c) {
        None => 1.0,
        Some(sp) if sp.is_filled() => 0.0,
        Some(sp) => match sp.space_type {
            SpaceType::Wild => 0.2,
            SpaceType::Special => special_kosten(player, r, c, verbleibend),
            SpaceType::Normal => {
                let need = sp.required_color;
                match (player.pattern_lines[r].color, need) {
                    (None, Some(x)) => 1.0 + engpass_aufschlag(verbleibend, x),
                    (None, None) => 1.0, // Normal hat laut dome.rs immer required_color=Some(..); defensiv.
                    (Some(c2), Some(x)) if c2 == x => 0.3,
                    _ => 2.0,
                }
            }
        },
    }
}

/// Geometrie: die 3 Slot-Nachbarn von `(r, c)` -- die anderen 3 Zellen im
/// selben 2x2-Dome-Slot (Slot `(r/2, c/2)`). Reine Geometrie, kein
/// Spielzustand -- siehe `slot_score`s Doku fuer die Herleitung.
fn slot_nachbarn(r: usize, c: usize) -> [(usize, usize); 3] {
    let slot_row = r / 2;
    let slot_col = c / 2;
    let mut out = [(0usize, 0usize); 3];
    let mut i = 0usize;
    for dr in 0..2usize {
        for dc in 0..2usize {
            let rr = slot_row * 2 + dr;
            let cc = slot_col * 2 + dc;
            if rr == r && cc == c {
                continue; // die Zelle selbst ist kein eigener Nachbar.
            }
            out[i] = (rr, cc);
            i += 1;
        }
    }
    out
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
    let Some(i) = crate::provocation::farben_index(farbe) else {
        return 0.0; // Wild ist keine ziehbare Farbe, kommt hier nie vor; defensiv.
    };
    let frac = (verbleibend[i].max(0) as f64 / crate::tile::TILES_PER_COLOR as f64).min(1.0);
    ENGPASS_MAX * (1.0 - frac)
}

/// Kosten einer noch unbefuellten Special-Zelle `(r, spalte)`.
///
/// **§16-Default AUS** (`MOSAIC_SPALTENBAU_SPECIAL` unset): ALT-Formel
/// (Runde 1/2, §12) -- `0,3 + 0,8 * n`, `n` = Zahl der noch NICHT gefuellten
/// der 3 Slot-Nachbarn, ohne Ruecksicht auf DEREN Farbforderung.
///
/// **§16-EIN** (Koordinator-Auftrag 2026-08-13, "Slot-Nachbarzellen ... sind
/// der Weg zur Special-Zelle"): die Kosten sind die SUMME der echten
/// [`zelle_kosten`] ihrer 3 Slot-Nachbarn -- eine Special-Zelle ist billig,
/// wenn ihre Nachbarn billig sind (Wild, oder schon richtig gebunden), teuer,
/// wenn sie eine knappe/falsch gebundene Farbe brauchen. Bildet die
/// Nutzer-Taktik (`docs/domain_knowledge.md` §8: "erzwungene Spezialkuppeln
/// nach OBEN ... obere Slots haengen an billigen Musterreihen") OHNE eigene
/// Slot-Reihen-Sonderregel ab: obere Slots (Zeilen 0/1) haben Nachbarn mit
/// KLEINEM `r`, also kleiner `benoetigt`-Kopienzahl in [`zelle_kosten`]s
/// Normal-Zweig -- der Reihen-Tiefe-Effekt entsteht automatisch aus der
/// bestehenden Kostenformel, keine zusaetzliche Sonderregel noetig.
///
/// Geometrie ([`slot_nachbarn`], wie `slot_score`): Slot `(r/2, spalte/2)`
/// deckt Rasterzeilen `2*(r/2)`/`2*(r/2)+1` und -spalten `2*(spalte/2)`/
/// `2*(spalte/2)+1` ab.
pub(crate) fn special_kosten(player: &PlayerBoard, r: usize, spalte: usize, verbleibend: &[i64; 5]) -> f64 {
    if !special_aktiv() {
        let mut offene_nachbarn = 0u32;
        for &(rr, cc) in &slot_nachbarn(r, spalte) {
            let gefuellt = player.dome_grid.get_space(rr, cc).map_or(true, |s| s.is_filled());
            if !gefuellt {
                offene_nachbarn += 1;
            }
        }
        return 0.3 + 0.8 * offene_nachbarn as f64;
    }
    slot_nachbarn(r, spalte).iter().map(|&(rr, cc)| zelle_kosten(player, rr, cc, verbleibend)).sum()
}

/// §18 (Diagonalen-Baustein, Koordinator-Auftrag 2026-08-13): wie
/// [`special_kosten`]s "smart"-Zweig (echte Nachbar-Kosten statt der ALT-
/// Schaetzung), aber OHNE den §16/§17-Schalter [`special_aktiv`] -- der
/// gilt nur fuer den column_build-EIGENEN (Kriterium 1) Pfad, dessen
/// Uebernahme-Entscheidung in §17 final NEIN war. Andere Bauern
/// (`plate_builder.rs`) mit einer EIGENEN, unabhaengig gemessenen und
/// signifikant positiven Entscheidung (z.B. `Diagonalenbauer`, §18: +2,61
/// Plattenpunkte, t=2,79, p=0,011) rufen diese Funktion UNBEDINGT auf --
/// jeder Bauer hat seinen eigenen Uebernahme-Status, das globale
/// `MOSAIC_SPALTENBAU_SPECIAL` bleibt reserviert fuer den k1-Legacy-Pfad.
pub(crate) fn zelle_kosten_smart(player: &PlayerBoard, r: usize, c: usize, verbleibend: &[i64; 5]) -> f64 {
    match player.dome_grid.get_space(r, c) {
        None => 1.0,
        Some(sp) if sp.is_filled() => 0.0,
        Some(sp) => match sp.space_type {
            SpaceType::Wild => 0.2,
            SpaceType::Special => slot_nachbarn(r, c).iter().map(|&(rr, cc)| zelle_kosten_smart(player, rr, cc, verbleibend)).sum(),
            SpaceType::Normal => {
                let need = sp.required_color;
                match (player.pattern_lines[r].color, need) {
                    (None, Some(x)) => 1.0 + engpass_aufschlag(verbleibend, x),
                    (None, None) => 1.0,
                    (Some(c2), Some(x)) if c2 == x => 0.3,
                    _ => 2.0,
                }
            }
        },
    }
}

/// Wie [`special_nachbar_zellen_fuer_liste`], aber UNBEDINGT (kein
/// `special_aktiv`-Schalter) -- siehe [`zelle_kosten_smart`]-Doku fuer die
/// Begruendung (jeder generische Bauer hat seinen eigenen, unabhaengigen
/// Uebernahme-Status).
pub(crate) fn special_nachbar_zellen_immer(player: &PlayerBoard, zellen: &[(usize, usize)]) -> Vec<(usize, usize)> {
    let mut v = Vec::new();
    for &(r, c) in zellen {
        let Some(sp) = player.dome_grid.get_space(r, c) else { continue };
        if sp.is_filled() || sp.space_type != SpaceType::Special {
            continue;
        }
        v.extend_from_slice(&slot_nachbarn(r, c));
    }
    v
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

    /// Runde 4, Baustein 1: letzte Substitution durch [`ziel_spalte_fuer_
    /// player`]s Vollendbarkeits-Sicherheitsnetz (natuerlicher Kandidat, neue
    /// Spalte), fuer den naechsten [`trace_zeile`]-Aufruf zum Ablesen/
    /// Loeschen (Nutzer-Vorgabe: "Der Wechsel muss im [SB]-Trace als eigenes
    /// Ereignis erscheinen"). KEIN Partie-Zustand (anders als eine fruehere
    /// Fassung, siehe Moduldoku) -- wird bei jedem `ziel_spalte_fuer_player`-
    /// Aufruf frisch bewertet, nur bei einer tatsaechlichen Substitution
    /// gesetzt.
    static LETZTER_WECHSEL: std::cell::Cell<Option<(usize, usize)>> = const { std::cell::Cell::new(None) };

    /// Runde 4, Baustein 3 (zweite Nutzer-Korrektur, "Material zuerst,
    /// Forderung danach"): true, wenn die letzte [`vorzug_dome_wahl`]-
    /// Entscheidung eine Kachel/Rotation gewaehlt hat, die eine Zelle mit
    /// EXAKT der schon in ihrer Musterreihe liegenden Farbe versorgt (der
    /// "Jackpot" der Nutzer-Vorgabe). Wird bei jedem `vorzug_dome_wahl`-
    /// Aufruf frisch gesetzt (kein Leck-Risiko wie bei `PARTIE_SEED`, weil
    /// es keinen Partie-Bezug hat, sondern nur den letzten Dome-Entscheid).
    static LETZTER_JACKPOT: std::cell::Cell<bool> = const { std::cell::Cell::new(false) };
}

/// Setzt (oder loescht mit `None`) den Partie-Seed fuer DIESEN Thread --
/// gleiches Muster wie `net_mcts::set_partie_shaping_weight`/
/// `provocation::set_ziel_spalte_seed`. Aufrufer MUSS am Partieende (oder vor
/// der naechsten Partie desselben Threads) mit `None`/dem neuen Seed
/// ueberschreiben, sonst leckt der Wert in die naechste Partie.
pub(crate) fn set_partie_seed(seed: Option<u64>) {
    PARTIE_SEED.with(|c| c.set(seed));
}

/// Runde 4, Baustein 1: ist Spalte `spalte` fuer `player` unter der AKTUELLEN
/// oeffentlichen Versorgungslage `verbleibend` noch VOLLENDBAR? Prueft NUR
/// Normal-Zellen (Wild braucht keine Farbe; Special hat eine eigene, von der
/// Farbversorgung unabhaengige Trigger-Bedingung, siehe `special_kosten`-Doku
/// -- eine Special-Zelle als "unvollendbar wegen Farbe" zu werten waere
/// sachlich falsch, sie kennt gar keine Farbforderung):
///
///  - Zeile bereits an eine ANDERE Farbe als die geforderte gebunden -> nicht
///    bedienbar (Nutzer-Vorgabe: "die Zielreihe noch bedienbar").
///  - sonst: noch benoetigte Kopien = `(r+1) - schon_in_der_Reihe`; wenn
///    `verbleibend` fuer diese Farbe kleiner ist, ist die Zeile NICHT mehr
///    beschaffbar (Nutzer-Vorgabe: "Reihe r braucht r+1 Kopien", nicht nur
///    `> 0`).
///
/// Eine Spalte ist vollendbar, wenn ALLE ihre offenen Normal-Zellen es sind.
/// Kein Slot an einer Zeile (`None`) blockt nicht (neutral, wie ueberall
/// sonst in diesem Modul) -- eine Spalte mit noch unbelegten Slots ist per
/// Definition nicht ausgeschlossen, nur weil dort noch keine Platte liegt.
pub(crate) fn ist_spalte_vollendbar(player: &PlayerBoard, spalte: usize, verbleibend: &[i64; 5]) -> bool {
    for r in 0..6usize {
        let Some(sp) = player.dome_grid.get_space(r, spalte) else { continue };
        if sp.is_filled() {
            continue;
        }
        match sp.space_type {
            SpaceType::Wild => continue,
            SpaceType::Special => {
                // §16-Default AUS: Special-Zellen bleiben wie in §14
                // unberuecksichtigt (eigene, farbunabhaengige Trigger-
                // Bedingung). §16-EIN: eine offene Special-Zelle ist
                // vollendbar, wenn ihre 3 Slot-Nachbarn es sind -- SIE sind
                // die eigentliche Farbforderung, die Special-Zelle selbst
                // hat keine.
                if !special_aktiv() {
                    continue;
                }
                for &(rr, cc) in &slot_nachbarn(r, spalte) {
                    if !ist_zelle_vollendbar(player, rr, cc, verbleibend) {
                        return false;
                    }
                }
            }
            SpaceType::Normal => {
                let Some(need) = sp.required_color else { continue };
                let zeile = &player.pattern_lines[r];
                // WICHTIG (Fund aus der ersten vollen Runde-4-Messung: 5,25
                // Wechsel je Partie im Schnitt, vertikale Punkte brachen auf
                // 2,45 statt 5,95 ein): eine an eine ANDERE Farbe gebundene
                // Zeile ist NICHT permanent blockiert -- die Bindung ist
                // Runden-transient (sie loest sich, sobald die Reihe VOLL
                // ist und getilet wird, spaetestens beim naechsten
                // Rundenende via `round_end::process_unplaceable_rows` auf
                // die Strafleiste). Die eigene Teil-1-Aufspaltung (§14) zeigt
                // genau das empirisch: "falsch gebunden" macht 0 von 14
                // PERSISTENTEN Mauer-Blockern aus. Behandelt wie eine offene
                // Zeile (0 Fortschritt fuer `need`, volle r+1 Kopien noetig)
                // statt als Sofort-Blocker.
                let schon = if zeile.color == Some(need) { zeile.tiles.len() as i64 } else { 0 };
                let Some(i) = crate::provocation::farben_index(need) else { continue };
                let benoetigt = (r as i64 + 1) - schon;
                if verbleibend[i] < benoetigt {
                    return false;
                }
            }
        }
    }
    true
}

/// §16: dieselbe Vollendbarkeits-Pruefung wie [`ist_spalte_vollendbar`]s
/// Normal-Zweig, aber fuer eine EINZELNE Zelle `(r, c)` -- gebraucht fuer die
/// Slot-Nachbarn einer offenen Special-Zelle, die in einer ANDEREN Spalte
/// liegen koennen als die gerade gepruefte Zielspalte. Wild/Special selbst
/// gelten immer als vollendbar (Special-in-Special kommt laut Katalog nie
/// vor, ein zweiter Rekursionsschritt waere aber ohnehin terminierend).
pub(crate) fn ist_zelle_vollendbar(player: &PlayerBoard, r: usize, c: usize, verbleibend: &[i64; 5]) -> bool {
    let Some(sp) = player.dome_grid.get_space(r, c) else { return true };
    if sp.is_filled() {
        return true;
    }
    match sp.space_type {
        SpaceType::Wild | SpaceType::Special => true,
        SpaceType::Normal => {
            let Some(need) = sp.required_color else { return true };
            let zeile = &player.pattern_lines[r];
            let schon = if zeile.color == Some(need) { zeile.tiles.len() as i64 } else { 0 };
            let Some(i) = crate::provocation::farben_index(need) else { return true };
            let benoetigt = (r as i64 + 1) - schon;
            verbleibend[i] >= benoetigt
        }
    }
}

/// Runde 4, Baustein 1: die beste VOLLENDBARE Spalte, wenn die vom Kosten-
/// Kandidaten natuerlich gewaehlte Spalte unvollendbar ist. "Beste" heisst
/// zuerst meiste bereits gefuellte Zellen (Nutzer-Vorgabe: "vorhandene Zellen
/// hoch gewichten -- Umschwenken auf eine 4/6-Spalte schlaegt Neuanfang"),
/// dann die guenstigsten Kosten als Tie-Break. Ohne JEDE vollendbare Spalte
/// (spaetes Spiel, sehr seltener Grenzfall) faellt die Funktion auf die
/// gewohnte Kostenwahl zurueck -- ein Zwang zu einer nachweislich
/// unvollendbaren Spalte waere kein Fortschritt.
fn waehle_beste_vollendbare_spalte(player: &PlayerBoard, verbleibend: &[i64; 5], kosten: &[f64; 6]) -> usize {
    let gefuellte_zellen = |c: usize| -> i32 {
        (0..6usize)
            .filter(|&r| player.dome_grid.get_space(r, c).map_or(false, |sp| sp.is_filled()))
            .count() as i32
    };
    let mut kandidaten: Vec<usize> = (0..6usize).filter(|&c| ist_spalte_vollendbar(player, c, verbleibend)).collect();
    if kandidaten.is_empty() {
        return waehle_spalte(*kosten);
    }
    kandidaten.sort_by(|&a, &b| {
        gefuellte_zellen(b)
            .cmp(&gefuellte_zellen(a))
            .then(kosten[a].partial_cmp(&kosten[b]).unwrap())
    });
    kandidaten[0]
}

/// Zielspalte fuer Spieler `pi`: die gewohnte Kostenwahl aus [`waehle_spalte`]
/// (frisch bei jedem Aufruf), mit einem Vollendbarkeits-Sicherheitsnetz
/// (Runde 4, Baustein 1) darueber -- ist der natuerliche Kandidat unvollendbar,
/// weicht die Funktion auf [`waehle_beste_vollendbare_spalte`] aus und
/// vermerkt das in [`LETZTER_WECHSEL`] fuer den naechsten Trace-Aufruf.
fn ziel_spalte_fuer_player(state: &GameState, pi: usize) -> usize {
    let player = &state.players[pi];
    let verbleibend = crate::provocation::verbleibende_farben(state);
    let kosten: [f64; 6] = std::array::from_fn(|c| spalten_kosten(player, c, &verbleibend));
    // FRISCH bei jedem Aufruf, wie in Runde 1-3 -- KEIN gespeichertes
    // "bisheriges Ziel" mehr (fruehere Fassung dieser Funktion hielt eine
    // Spalte per `LETZTES_ZIEL`-Thread-Local fest und wechselte nur bei
    // Unvollendbarkeit; VIER volle 20-Seed-Messungen zeigten damit
    // durchgehend 0,70-2,45 statt Runde 3s 5,95 vertikale Punkte -- die
    // Stur-Bindung nahm der Kosten-Formel genau die Reaktionsfaehigkeit, die
    // Runde 3 bereits erfolgreich validiert hatte, ohne einen belegten
    // Gegenwert (Teil 1 der Blocker-Aufspaltung zeigt 0 von 14 Mauer-Zellen
    // in Kategorie "Farbe nie verfuegbar" -- das Problem, das die Bindung
    // loesen sollte, war empirisch gar nicht die dominante Ursache). Siehe
    // PREREG_provocation.md §14 fuer die volle Messreihe.
    let kandidat = waehle_spalte(kosten);

    // §15-Entscheidung: Default (unset) ist AUS -- kein Arm der
    // Entkonfundierung uebertraf 5,95, also bleibt die Runde-3-Konfiguration
    // der aktive Stand (Vorab-Regel des Koordinators). `MOSAIC_SPALTENBAU_
    // SICHERHEITSNETZ=1` schaltet Baustein 1 gezielt wieder ein.
    if !sicherheitsnetz_aktiv() {
        return kandidat;
    }

    // Runde 4, Baustein 1 (weiterhin aktiv, aber als reiner SICHERHEITSNETZ-
    // Filter ueber der unveraenderten Kostenwahl, nicht als Ersatz dafuer):
    // ist die naturgemaess billigste Spalte gerade unvollendbar (Farbe fuer
    // eine offene Zeile objektiv erschoepft), wird auf die beste VOLLENDBARE
    // Alternative ausgewichen. `noch_erreichbare_farben` (nicht `verbleibend`)
    // ist hier die richtige Zahl -- siehe dortige Doku.
    let erreichbar = crate::provocation::noch_erreichbare_farben(state, pi);
    if ist_spalte_vollendbar(player, kandidat, &erreichbar) {
        return kandidat;
    }
    let neu = waehle_beste_vollendbare_spalte(player, &erreichbar, &kosten);
    if neu != kandidat {
        LETZTER_WECHSEL.with(|c| c.set(Some((kandidat, neu))));
    }
    neu
}

/// Deterministische Mischung Seed -> Index `0..n` -- identisches SplitMix64-
/// Muster wie `net_mcts::partie_gewicht_aus_seed`/`provocation::spalte_aus_
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
/// Leck-Risiko wie bei `provocation::AUTO_SPALTE`/`set_ziel_spalte_seed`).
/// Auswahl unter den guenstigsten Kandidaten: siehe [`waehle_spalte`].
pub(crate) fn ziel_spalte(state: &GameState) -> Option<usize> {
    if !ist_aktiv() {
        return None;
    }
    Some(ziel_spalte_fuer_player(state, state.current_player))
}

// ── Wiederverwendung: Stein-Zug- und Tiling-Praeferenz mit dynamischer Spalte ──

/// Stein-Zug-Praeferenz, IDENTISCHE Logik zu `provocation::vorzugszug`, aber
/// mit der je Entscheid dynamisch bestimmten Spalte statt `MOSAIC_VORZUG_SPALTE`.
/// [`ueberpraesenz_vorzug`] als zweite Vorzugsstufe wurde GEBAUT und GEMESSEN,
/// ist aber NICHT verkettet -- siehe der lange Kommentar im Funktionskoerper
/// fuer den gemessenen Grund (2/20 statt 15-16/20 Netz-Siege).
pub(crate) fn vorzugszug(state: &GameState) -> Option<Action> {
    let spalte = ziel_spalte(state)?;
    crate::provocation::vorzugszug_fuer_spalte(state, spalte)
        // §16 (Special-Zellen-Baustein): `vorzugszug_fuer_spalte` sieht nur
        // die Zielspalte selbst -- eine offene Special-Zelle braucht aber
        // ihre 3 Slot-Nachbarn, die oft in der NACHBAR-Spalte liegen. Zweite
        // Vorzugsstufe (Default AUS, siehe `special_aktiv`): liefert `None`,
        // solange kein Nachbar offen ist -- KEIN zusaetzliches Risiko wie
        // `ueberpraesenz_vorzug` (siehe unten), weil sie nur bei einer
        // KONKRETEN, schon platzierten Special-Zelle ueberhaupt greift, nicht
        // bei jeder Fruehphasen-Entscheidung ohne Kandidat.
        .or_else(|| {
            let player = &state.players[state.current_player];
            let zellen = special_nachbar_zellen(player, spalte);
            if zellen.is_empty() {
                None
            } else {
                crate::plate_builder::vorzugszug_fuer_zellen(state, &zellen)
            }
        })
    // [`ueberpraesenz_vorzug`] BEWUSST NICHT verkettet: die erste volle
    // Runde-4-Messung mit dieser Stufe im Vorzugspfad brach von 15-16/20 auf
    // 2/20 Netz-Siege ein (McNemar p=0.0001, sofort mit einer 6-Seed-Sonde
    // ohne diese Stufe repliziert: 5/6 bleibt bei der gewohnten Grössenordnung
    // -- Isolation eindeutig). Grund vermutet: `vorzugszug_fuer_spalte`
    // greift nur, wenn eine ZIELSPALTEN-spezifische Zelle passt (schmal,
    // genau die Situationen aus §11/§12); `ueberpraesenz_vorzug` greift
    // JEDESMAL, wenn das nicht der Fall ist -- also auf einem GROSSEN Teil
    // aller Fruehphasen-Entscheidungen -- und ersetzt dort die Netz-Suche
    // durch eine Ein-Kriterium-Heuristik (nur Farbmenge + Zeilentiefe), die
    // Strafleiste/Gegner/andere Wertungsplatten komplett ignoriert. Exakt
    // das Muster aus §7 ("Beschneidung zu stark", Endstand-Kollaps) -- nur
    // ueber die Vorzugs- statt die Aktionsmengen-Seite. Bleibt als GETESTETE,
    // aber UNVERDRAHTETE Funktion stehen (siehe `ueberpraesenz_vorzug`-Tests)
    // fuer eine spaetere, enger gefasste Fassung (z.B. nur als zusaetzliches
    // Suchsignal statt als Suche-ersetzender Vorzug).
}

/// §16: Slot-Nachbarn ALLER noch offenen Special-Zellen der Zielspalte --
/// leere Liste, wenn Baustein AUS oder keine offene Special-Zelle vorliegt.
/// Geteilt zwischen [`vorzugszug`] (Drafting) und [`vorzug_tiling_step`]
/// (Tiling) -- beide reichen die Liste an die generische Zellen-Mechanik aus
/// `plate_builder.rs` durch (`vorzugszug_fuer_zellen`/`tiling_vorzug_fuer_
/// zellen`), statt eine eigene Praeferenzlogik zu duplizieren.
fn special_nachbar_zellen(player: &PlayerBoard, spalte: usize) -> Vec<(usize, usize)> {
    special_nachbar_zellen_fuer_liste(player, &zellen_spalte_liste(spalte))
}

/// §18 (Diagonalen-Baustein, Koordinator-Auftrag 2026-08-13): Generalisierung
/// von [`special_nachbar_zellen`] auf eine BELIEBIGE Zielzellen-Liste, nicht
/// nur eine Spalte -- fuer `plate_builder.rs`s generische Kriterien
/// (Diagonalen, Ecken, Zeilen, ...), die keine `spalte: usize` haben,
/// sondern eine `&[(usize, usize)]`-Liste. Findet alle offenen Special-Zellen
/// INNERHALB der Liste und liefert ihre Slot-Nachbarn (koennen ausserhalb der
/// Liste liegen, z.B. in einer Nachbar-Spalte -- das ist der Punkt).
pub(crate) fn special_nachbar_zellen_fuer_liste(player: &PlayerBoard, zellen: &[(usize, usize)]) -> Vec<(usize, usize)> {
    let mut v = Vec::new();
    if !special_aktiv() {
        return v;
    }
    for &(r, c) in zellen {
        let Some(sp) = player.dome_grid.get_space(r, c) else { continue };
        if sp.is_filled() || sp.space_type != SpaceType::Special {
            continue;
        }
        v.extend_from_slice(&slot_nachbarn(r, c));
    }
    v
}

fn zellen_spalte_liste(spalte: usize) -> [(usize, usize); 6] {
    std::array::from_fn(|r| (r, spalte))
}

/// Runde 4, Baustein 3 (zweite Nutzer-Korrektur 2026-08-13): "ich nehm
/// ueberpraesente farben aus der fabrik und platziere sie in den unteren
/// reihen. erst dann waehl ich die passende kuppel aus." -- eine ZWEITE
/// Vorzugsstufe, unabhaengig von einer bestimmten Zielspalte (die hat ja noch
/// keine Platte, kann also noch keine Farbforderung stellen): unter den JETZT
/// tatsaechlich nehmbaren Farben (`generate_valid_moves`) wird die
/// ueberpraesenteste gewaehlt (hoechster `verbleibende_farben`-Wert -- am
/// wenigsten verbraucht, nicht die im aktuellen Angebot haeufigste Kopie, das
/// waere ein reiner Momentaufnahme-Zufall) und in die TIEFSTE Musterreihe
/// gelegt, die diese Farbe laut Spielregeln gerade annehmen darf (`place.
/// row_index` aus einem bereits VALIDIERTEN Zug -- die Regel-Prüfung selbst
/// bleibt in `validation.rs`, hier wird nur unter den erlaubten Zuegen
/// gewaehlt). Tiefste Reihe zuerst, weil sie die meisten Kopien braucht (bis
/// zu 6) und die laengste Anlaufzeit hat -- Ueberfluss zaehlt dort am
/// meisten (wortgleiche Nutzer-Begruendung).
///
/// Bewusst KEINE Ziel-Zeilen-Pruefung wie `vorzugszug_fuer_spalte` -- diese
/// Stufe kennt noch keine feste Zielspalte, sie bindet nur Material, die
/// Kuppelwahl (Runde 4, Baustein 3, [`zellen_wert`]) entscheidet spaeter,
/// welche Zellen davon profitieren.
// Absichtlich NICHT in `vorzugszug` verkettet (siehe dortiger Kommentar) --
// bleibt fuer eine spaetere, enger gefasste Fassung UND die eigenen Tests
// stehen, produktiv also `dead_code` aus Compiler-Sicht.
#[allow(dead_code)]
pub(crate) fn ueberpraesenz_vorzug(state: &GameState) -> Option<Action> {
    if !ist_aktiv() {
        return None;
    }
    if state.phase != crate::state::Phase::Drafting || state.round_number > 4 {
        return None;
    }
    let verbleibend = crate::provocation::verbleibende_farben(state);
    let moves = crate::validation::generate_valid_moves(state);

    // Feste Farbreihenfolge (`TileColor::NORMAL`) statt eines HashSets --
    // dessen Iterationsreihenfolge ist PRO INSTANZ zufaellig (Rust
    // `RandomState`), zwei Aufrufe fuer DENSELBEN Zustand koennten bei einem
    // Gleichstand in `verbleibend` sonst unterschiedliche Farben liefern.
    // Gefunden ueber `plate_builder::mosaic_spaltenbau_an_ist_verhaltens
    // identisch_zur_direkten_ansteuerung`, die genau das prueft.
    let mut bestes: Option<(i64, TileColor)> = None;
    for &farbe in TileColor::NORMAL.iter() {
        let im_angebot = moves.iter().any(|m| m.take.color == farbe && (0..=5).contains(&m.place.row_index));
        if !im_angebot {
            continue;
        }
        let Some(i) = crate::provocation::farben_index(farbe) else { continue };
        let wert = verbleibend[i];
        if bestes.map_or(true, |(bw, _)| wert > bw) {
            bestes = Some((wert, farbe));
        }
    }
    let ueberpraesent = bestes?.1;

    moves
        .into_iter()
        .filter(|m| m.take.color == ueberpraesent && (0..=5).contains(&m.place.row_index))
        .max_by_key(|m| m.place.row_index)
        .map(Action::Stone)
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
    // `pi` bewusst NICHT durch `state.current_player` ersetzt, sondern direkt
    // an [`ziel_spalte_fuer_player`] durchgereicht (Runde 4: dieselbe
    // Vollendbarkeits-/Wechsel-Buchhaltung wie Drafting/Dome, sonst wuerde
    // Tiling eine ANDERE, veraltete Spalte ansteuern als der Rest der
    // Entscheidungen derselben Runde).
    let spalte = ziel_spalte_fuer_player(state, pi);
    crate::tiling_solver::vorzug_tiling_step_fuer_spalte(state, pi, spalte).or_else(|| {
        // §16: dieselbe Slot-Nachbar-Erweiterung wie in `vorzugszug` --
        // eine bereits gebundene Farbe muss beim Tiling auch tatsaechlich
        // in die Special-Nachbarzelle geroutet werden, nicht nur beim
        // Drafting genommen worden sein.
        let player = &state.players[pi];
        let zellen = special_nachbar_zellen(player, spalte);
        if zellen.is_empty() {
            None
        } else {
            crate::plate_builder::tiling_vorzug_fuer_zellen(state, pi, &zellen)
        }
    })
}

// ── Hauptaufgabe 1: Kuppelplatten-Wahl steuert required_color ──────────────

/// Runde 4, Baustein 3 (zweite Nutzer-Korrektur 2026-08-13): Score einer
/// Normal-Zelle, deren Musterreihe schon GENAU die geforderte Farbe fuehrt --
/// der "Jackpot" der Nutzer-Vorgabe ("Reihe traegt X UND Zelle wuerde X
/// fordern"). Bewusst UEBER Wild (3.0), weil die Kuppelwahl laut Vorgabe
/// "dominant" danach gewichten soll, ob bereits gesammeltes Material sofort
/// verwertbar wird -- Wild bleibt zwar immer brauchbar, bindet aber KEIN
/// bereits gebundenes Material frei, waehrend ein Jackpot-Treffer genau das
/// tut (die Reihe kann dadurch frueher zum Tiling). Exakter Literal-Wert
/// (keine Rechnung), damit `slot_score`/`vorzug_dome_wahl` einen Jackpot per
/// Gleichheitsvergleich sicher erkennen koennen (siehe `LETZTER_JACKPOT`).
const JACKPOT_WERT: f64 = 4.0;

/// Wie gut bedient `space` (bereits an Zeile `r` haengend gedacht) die
/// Ziel-Spalte, bevor die Platte ueberhaupt liegt? Wild ist immer gut (keine
/// Farbbindung noetig); Special neutral-gut (keine Farbbindung, aber auch
/// kein sofortiger Materialgewinn); eine Normal-Farbe ist am besten, wenn die
/// Musterreihe `r` schon GENAU diese Farbe fuehrt ([`JACKPOT_WERT`], Runde 4),
/// brauchbar, wenn die Reihe noch leer ist, und ungeeignet (0), wenn die
/// Reihe an eine andere Farbe gebunden ist.
pub(crate) fn zellen_wert(player: &PlayerBoard, r: usize, space: &DomeSpace) -> f64 {
    match space.space_type {
        SpaceType::Wild => 3.0,
        SpaceType::Special => 2.0,
        SpaceType::Normal => match (player.pattern_lines[r].color, space.required_color) {
            // §15-Entscheidung: Default (unset) ist AUS -> 2,5, der reine
            // Runde-3-Wert. `MOSAIC_SPALTENBAU_JACKPOT=1` schaltet Baustein 3a
            // gezielt wieder ein (JACKPOT_WERT=4,0).
            (Some(c), Some(x)) if c == x => {
                if jackpot_aktiv() {
                    JACKPOT_WERT
                } else {
                    2.5
                }
            }
            (None, _) => 1.5,
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
/// wie `provocation::vorzugszug` -- greift nur, wenn ein Kandidat echten
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
    // Runde 4, Baustein 3: pro Aufruf frisch gesetzt (kein Partie-Zustand,
    // siehe `LETZTER_JACKPOT`-Doku) -- eine Entscheidung ohne Kandidat darf
    // keinen Jackpot aus einer FRUEHEREN Entscheidung weitertragen.
    LETZTER_JACKPOT.with(|c| c.set(false));

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
                let ergebnis = best.filter(|(s, _)| *s > 0.0).map(|(_, rot)| Action::ChooseDomeRotation(rot));
                if let Some((_, rot)) = best.filter(|(s, _)| *s > 0.0) {
                    if kombination_hat_jackpot(player, tile, *slot_row, *slot_col, rot, spalte) {
                        LETZTER_JACKPOT.with(|c| c.set(true));
                    }
                }
                ergebnis
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
    let mut best: Option<(f64, usize, usize, u32)> = None; // (score, tile_id, slot_row, rotation)
    for tile in &state.dome_display {
        for &(sr, sc) in &player.dome_grid.empty_slots() {
            if sc != target_slot_col {
                continue;
            }
            let mut best_rot_score: Option<(f64, u32)> = None;
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
                    if best_rot_score.map_or(true, |(b, _)| score > b) {
                        best_rot_score = Some((score, rot));
                    }
                }
            }
            if let Some((score, rot)) = best_rot_score {
                if best.as_ref().map_or(true, |(bs, _, _, _)| score > *bs) {
                    best = Some((score, tile.tile_id, sr, rot));
                }
            }
        }
    }
    let gewinner = best.filter(|(s, _, _, _)| *s > 0.0);
    if let Some((_, tid, sr, rot)) = gewinner {
        if let Some(tile) = state.dome_display.iter().find(|t| t.tile_id == tid) {
            if kombination_hat_jackpot(player, tile, sr, target_slot_col, rot, spalte) {
                LETZTER_JACKPOT.with(|c| c.set(true));
            }
        }
    }
    gewinner.map(|(_, tid, sr, _)| {
        Action::ChooseDomeSlot(PlaceDomeTileMove {
            dome_tile_id: tid,
            slot_row: sr,
            slot_col: target_slot_col,
            rotation: 0,
        })
    })
}

/// Runde 4, Baustein 3: hat die (Kachel, Slot, Rotation)-Kombination fuer
/// `spalte` eine JACKPOT-Zelle unter den zwei betroffenen Positionen
/// (`slot_score`s Geometrie, siehe dortige Doku)? Exakter Gleichheitsvergleich
/// mit [`JACKPOT_WERT`] ist hier sicher, weil `zellen_wert` diesen Wert als
/// LITERAL zurueckgibt (keine Rechnung, kein Rundungsrisiko).
fn kombination_hat_jackpot(player: &PlayerBoard, tile: &DomeTile, slot_row: usize, _slot_col: usize, rotation: u32, spalte: usize) -> bool {
    let Some(idx) = rotation_indices(rotation) else { return false };
    let cc = spalte % 2;
    let top_row = slot_row * 2;
    let bottom_row = slot_row * 2 + 1;
    zellen_wert(player, top_row, &tile.spaces[idx[cc]]) == JACKPOT_WERT
        || zellen_wert(player, bottom_row, &tile.spaces[idx[cc + 2]]) == JACKPOT_WERT
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
/// Farbe qualifiziert dort, siehe `provocation::vorzugszug_fuer_spalte`).
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
/// (`column_build`/`provocation`, VOR dem Fallback auf die Netz-Suche) -- bei
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
    let verbleibend = crate::provocation::verbleibende_farben(state);
    let kosten: [f64; 6] = std::array::from_fn(|c| spalten_kosten(player, c, &verbleibend));
    // Runde 4: dieselbe Vollendbarkeits-/Wechsel-Buchhaltung wie die
    // eigentlichen Vorzugsfunktionen -- der Aufrufer hat sie fuer DIESE
    // Entscheidung bereits einmal durchlaufen (self_play.rs ruft den Vorzug
    // vor `trace_zeile` auf), ein zweiter Aufruf hier ist idempotent (siehe
    // `ziel_spalte_fuer_player`-Doku: kein erneuter Wechsel, wenn die Spalte
    // sich seit dem ersten Aufruf nicht veraendert hat) und stellt sicher,
    // dass die Trace-Zeile GENAU das Ziel zeigt, das der Vorzug tatsaechlich
    // verwendet hat -- nicht eine eigene, davon abweichende Neuberechnung.
    let ziel = ziel_spalte_fuer_player(state, pi);
    let wechsel = LETZTER_WECHSEL.with(|c| c.take());
    let jackpot = if entscheidungstyp == "Dome" { LETZTER_JACKPOT.with(|c| c.get()) } else { false };
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
        // Namen waeren fuer `tools/column_build_trace.py`s Parser nicht mehr
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
    // Runde 4: Zielwechsel und Kuppel-Jackpot als eigene, additive Felder --
    // beide bewusst NUR gesetzt, wenn sie diese Entscheidung betreffen (kein
    // "Wechsel=nein"/"Jackpot=nein"-Rauschen in jeder Zeile, das Parsen in
    // `tools/column_build_trace.py` bleibt einfach: Feld da -> Ereignis war da).
    let wechsel_teil = match wechsel {
        Some((alt, neu)) => format!(" Wechsel={alt}->{neu} Grund=unvollendbar"),
        None => String::new(),
    };
    let jackpot_teil = if jackpot { " Jackpot=ja".to_string() } else { String::new() };

    Some(format!(
        "[SB] Spieler={pi} Typ={entscheidungstyp} Ziel={ziel} Top2=[{top2}] \
         Vorzug={vorzug} Aktion={gespielte_aktion:?}{angebot_teil}{wechsel_teil}{jackpot_teil}"
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
        let i = crate::provocation::farben_index(Rot).unwrap();
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
        leer_rot[crate::provocation::farben_index(Rot).unwrap()] = 0;

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
        // `ziel_spalte` ist WIEDER die reine, bei jedem Aufruf frisch
        // berechnete Kostenwahl aus Runde 1-3 (siehe Moduldoku fuer den
        // Verwurf der Zielspalten-Bindung) -- dieser Test ist bewusst wieder
        // die urspruengliche Fassung. Ohne jede Platte sind alle Spalten
        // gleich teuer (6.0) -> Spalte 0 gewinnt (Tie-Break). Sobald Zeile 0
        // von Spalte 0 an eine ANDERE Farbe gebunden wird, muss die Wahl
        // wechseln (Spalte 1 profitiert vom selben geteilten Slot und wird
        // dadurch billiger).
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
        // Direkter Vergleich: `column_build::vorzugszug` muss fuer eine
        // Stellung, in der Spalte 0 Ziel ist, denselben Zug liefern wie
        // `provocation::vorzugszug_fuer_spalte(state, 0)`.
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
        let erwartet = crate::provocation::vorzugszug_fuer_spalte(&game.state, 0);
        assert_eq!(vorzugszug(&game.state), erwartet);
        assert!(erwartet.is_some(), "Testvoraussetzung: es sollte ueberhaupt einen Kandidaten geben");
        set_aktiv_override_for_test(None);
    }

    // ── Runde 4, Baustein 1: Vollendbarkeits-Buchhaltung + Zielwechsel ──────

    #[test]
    fn ist_spalte_vollendbar_erkennt_erschoepfte_farbe_als_unvollendbar() {
        let mut game = drafting_game(80);
        let pi = game.state.current_player;
        // Slot (2,2): si=2 -> (Zeile5, Spalte4) = Rot.
        let tile = normal_tile(80, [Blau, Gelb, Rot, Schwarz]);
        game.state.players[pi].dome_grid.place_dome_tile(tile, 2, 2).expect("frei");
        let voll = [crate::tile::TILES_PER_COLOR as i64; 5];
        assert!(
            ist_spalte_vollendbar(&game.state.players[pi], 4, &voll),
            "bei reichlicher Versorgung muss Spalte 4 vollendbar sein"
        );

        let mut knapp = voll;
        let i = crate::provocation::farben_index(Rot).unwrap();
        knapp[i] = 5; // Zeile 5 braucht r+1=6 Kopien -- 5 reicht nicht mehr.
        assert!(
            !ist_spalte_vollendbar(&game.state.players[pi], 4, &knapp),
            "Rot reicht nicht fuer die 6 Kopien von Zeile 5 -- Spalte 4 muss unvollendbar sein"
        );
    }

    #[test]
    fn ist_spalte_vollendbar_bleibt_bei_transienter_falschbindung_vollendbar() {
        // Korrigiertes Verhalten nach dem 5,25-Wechsel/Partie-Fund der ersten
        // vollen Runde-4-Messung (siehe Kommentar in `ist_spalte_
        // vollendbar`): eine JETZT falsch gebundene Zeile ist NUR transient
        // blockiert (die Bindung loest sich spaetestens beim naechsten
        // Rundenende) -- bei voller Rot-Versorgung bleibt Spalte 0 trotz der
        // Blau-Bindung in Zeile 0 vollendbar.
        let mut game = drafting_game(81);
        let pi = game.state.current_player;
        let tile = normal_tile(81, [Rot, Blau, Gelb, Schwarz]); // si=0 -> (Zeile0,Spalte0)=Rot.
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("frei");
        game.state.players[pi].pattern_lines[0].color = Some(Blau);
        game.state.players[pi].pattern_lines[0].tiles.push(Blau);
        let voll = [crate::tile::TILES_PER_COLOR as i64; 5];
        assert!(
            ist_spalte_vollendbar(&game.state.players[pi], 0, &voll),
            "eine transient falsch gebundene Zeile darf die Spalte bei voller Versorgung nicht als unvollendbar werten"
        );
    }

    #[test]
    fn ziel_spalte_wechselt_bei_unvollendbarer_spalte_und_meldet_wechsel() {
        // Baut Spalte 0 aus lauter Wild-Zellen (0,2 je Zelle, IGNORIERT die
        // Musterreihen-Bindung) bis auf eine erschoepfte Rot-Zeile --
        // Spalte 0 bleibt trotz der Erschoepfung die NATUERLICH billigste
        // Spalte per Kosten-Formel. Spalte 1 (im selben Slot, Spalten-Offset
        // 1) bekommt an ALLEN Zeilen eine falsch gebundene Normal-Zelle
        // (2,0 je Zelle), damit sie NICHT versehentlich noch billiger
        // erscheint als die leeren Spalten 2-5 -- ohne diesen Gegenpol
        // waere Spalte 1 durch die geteilten Wild-Zellen zufaellig billiger
        // als Spalte 0 UND als 2-5, und der Test wuerde das Sicherheitsnetz
        // gar nicht erst herausfordern (erste Fassung dieses Tests hatte
        // genau dieses Problem).
        set_aktiv_override_for_test(Some(true));
        // §15: Sicherheitsnetz ist seit der Entkonfundierung Default AUS --
        // dieser Test prueft den MECHANISMUS selbst, braucht ihn also
        // explizit eingeschaltet.
        set_sicherheitsnetz_override_for_test(Some(true));
        let mut game = drafting_game(90);
        let pi = game.state.current_player;

        for r in 0..5usize {
            game.state.players[pi].pattern_lines[r].color = Some(Blau);
            game.state.players[pi].pattern_lines[r].tiles.push(Blau);
        }
        let paar = |id: usize| DomeTile::new(id, vec![DomeSpace::wild(), DomeSpace::normal(Schwarz), DomeSpace::wild(), DomeSpace::normal(Schwarz)], 0);
        game.state.players[pi].dome_grid.place_dome_tile(paar(90), 0, 0).expect("frei"); // Zeile0/1.
        game.state.players[pi].dome_grid.place_dome_tile(paar(91), 1, 0).expect("frei"); // Zeile2/3.
        // Slot (2,0): si0=Wild(Zeile4,Spalte0), si1=Schwarz(Zeile4,Spalte1),
        // si2=Rot(Zeile5,Spalte0), si3=Schwarz(Zeile5,Spalte1).
        let t2 = DomeTile::new(92, vec![DomeSpace::wild(), DomeSpace::normal(Schwarz), DomeSpace::normal(Rot), DomeSpace::normal(Schwarz)], 0);
        game.state.players[pi].dome_grid.place_dome_tile(t2, 2, 0).expect("frei");

        game.state.players[pi].broken_tiles = vec![Rot; crate::tile::TILES_PER_COLOR];

        let neu = ziel_spalte(&game.state).expect("Spaltenbau aktiv");
        assert_ne!(neu, 0, "Spalte 0 ist unvollendbar (Rot fuer Zeile 5 komplett verbraucht) -- die Wahl muss abweichen");
        assert_ne!(neu, 1, "Spalte 1 ist ueberall falsch gebunden -- darf nicht als Ausweg gewaehlt werden");
        assert_eq!(
            LETZTER_WECHSEL.with(|c| c.get()),
            Some((0, neu)),
            "die Substitution muss vermerkt sein, damit trace_zeile sie im [SB]-Trace melden kann"
        );
        set_sicherheitsnetz_override_for_test(None);
        set_aktiv_override_for_test(None);
    }

    // ── Runde 4, Baustein 3: Material zuerst / Ueberpraesenz + Kuppel-Jackpot ──

    #[test]
    fn ueberpraesenz_vorzug_waehlt_tiefste_reihe_der_ueberpraesentesten_farbe() {
        set_aktiv_override_for_test(Some(true));
        let mut game = drafting_game(95);
        for f in game.state.factories.iter_mut() {
            f.sun_tiles.clear();
            f.moon_stacks.clear();
        }
        game.state.large_factory.sun_tiles.clear();
        game.state.large_factory.moon_pool.clear();
        game.state.factories[0].sun_tiles = vec![Blau, Rot];
        let pi = game.state.current_player;
        // Rot ist knapper als Blau (sichtbar verbraucht beim Gegner) -- Blau
        // muss trotz identischem Angebot als "ueberpraesent" gelten.
        game.state.players[1 - pi].broken_tiles = vec![Rot; 4];

        let a = ueberpraesenz_vorzug(&game.state).expect("Kandidat muss existieren");
        match a {
            Action::Stone(m) => {
                assert_eq!(m.take.color, Blau, "Blau hat mehr verbleibende Kopien als Rot -- muss gewinnen");
                assert_eq!(m.place.row_index, 5, "tiefste Reihe zuerst (Nutzer-Vorgabe: unten anfangen)");
            }
            other => panic!("erwartet Stone, bekam {other:?}"),
        }
        set_aktiv_override_for_test(None);
    }

    #[test]
    fn zellen_wert_jackpot_uebertrifft_wild_und_offene_zeile() {
        // §15: Jackpot ist seit der Entkonfundierung Default AUS -- dieser
        // Test prueft die GEWICHTUNG des Mechanismus selbst, braucht ihn
        // also explizit eingeschaltet.
        set_jackpot_override_for_test(Some(true));
        let mut game = drafting_game(96);
        let pi = game.state.current_player;
        game.state.players[pi].pattern_lines[2].color = Some(Rot);
        game.state.players[pi].pattern_lines[2].tiles.push(Rot);
        let passend = DomeSpace::normal(Rot);
        let unpassend = DomeSpace::normal(Blau);
        let wild = DomeSpace::wild();
        assert_eq!(zellen_wert(&game.state.players[pi], 2, &passend), JACKPOT_WERT);
        assert!(
            JACKPOT_WERT > zellen_wert(&game.state.players[pi], 2, &wild),
            "Jackpot muss dominant ueber Wild liegen (Nutzer-Vorgabe)"
        );
        assert_eq!(
            zellen_wert(&game.state.players[pi], 5, &unpassend),
            1.5,
            "eine offene, ungebundene Zeile bleibt beim alten Wert (kein Jackpot ohne bereits liegendes Material)"
        );
        set_jackpot_override_for_test(None);
    }

    // ── §15: Entkonfundierungs-Diagnose-Knoepfe ─────────────────────────────

    #[test]
    fn jackpot_knopf_aus_liefert_runde3_wert() {
        set_jackpot_override_for_test(Some(false));
        let mut game = drafting_game(97);
        let pi = game.state.current_player;
        game.state.players[pi].pattern_lines[2].color = Some(Rot);
        game.state.players[pi].pattern_lines[2].tiles.push(Rot);
        let passend = DomeSpace::normal(Rot);
        assert_eq!(
            zellen_wert(&game.state.players[pi], 2, &passend),
            2.5,
            "MOSAIC_SPALTENBAU_JACKPOT=0 muss den Runde-3-Wert 2,5 statt JACKPOT_WERT liefern"
        );
        set_jackpot_override_for_test(None);
    }

    #[test]
    fn jackpot_knopf_default_ist_seit_par15_der_runde3_wert() {
        // §15-Entscheidung: unset (kein Override, keine Env-Var) muss seit
        // der Entkonfundierung den reinen Runde-3-Wert 2,5 liefern, NICHT
        // mehr JACKPOT_WERT -- kein Arm uebertraf 5,95, also faellt der
        // Default auf die Runde-3-Konfiguration zurueck.
        let mut game = drafting_game(97);
        let pi = game.state.current_player;
        game.state.players[pi].pattern_lines[2].color = Some(Rot);
        game.state.players[pi].pattern_lines[2].tiles.push(Rot);
        let passend = DomeSpace::normal(Rot);
        assert_eq!(zellen_wert(&game.state.players[pi], 2, &passend), 2.5);
    }

    #[test]
    fn sicherheitsnetz_knopf_aus_ueberspringt_vollendbarkeits_filter() {
        // Dieselbe unvollendbare Spalte-0-Konstruktion wie in
        // `ziel_spalte_wechselt_bei_unvollendbarer_spalte_und_meldet_wechsel`
        // -- mit `MOSAIC_SPALTENBAU_SICHERHEITSNETZ=0` darf KEIN Wechsel
        // mehr stattfinden, `ziel_spalte` muss den reinen Kosten-Kandidaten
        // (Spalte 0) unveraendert durchreichen, obwohl er unvollendbar ist.
        set_aktiv_override_for_test(Some(true));
        set_sicherheitsnetz_override_for_test(Some(false));
        let mut game = drafting_game(90);
        let pi = game.state.current_player;

        for r in 0..5usize {
            game.state.players[pi].pattern_lines[r].color = Some(Blau);
            game.state.players[pi].pattern_lines[r].tiles.push(Blau);
        }
        let paar = |id: usize| DomeTile::new(id, vec![DomeSpace::wild(), DomeSpace::normal(Schwarz), DomeSpace::wild(), DomeSpace::normal(Schwarz)], 0);
        game.state.players[pi].dome_grid.place_dome_tile(paar(90), 0, 0).expect("frei");
        game.state.players[pi].dome_grid.place_dome_tile(paar(91), 1, 0).expect("frei");
        let t2 = DomeTile::new(92, vec![DomeSpace::wild(), DomeSpace::normal(Schwarz), DomeSpace::normal(Rot), DomeSpace::normal(Schwarz)], 0);
        game.state.players[pi].dome_grid.place_dome_tile(t2, 2, 0).expect("frei");
        game.state.players[pi].broken_tiles = vec![Rot; crate::tile::TILES_PER_COLOR];

        let neu = ziel_spalte(&game.state).expect("Spaltenbau aktiv");
        assert_eq!(neu, 0, "mit abgeschaltetem Sicherheitsnetz muss die reine Kostenwahl (Spalte 0) durchgereicht werden");
        assert_eq!(
            LETZTER_WECHSEL.with(|c| c.get()),
            None,
            "ohne Sicherheitsnetz darf kein Wechsel vermerkt werden"
        );
        set_sicherheitsnetz_override_for_test(None);
        set_aktiv_override_for_test(None);
    }

    // ── §16: Special-Zellen-Baustein ─────────────────────────────────────────

    #[test]
    fn special_kosten_par16_nutzt_echte_nachbarkosten() {
        set_special_override_for_test(Some(true));
        let mut game = drafting_game(51);
        let pi = game.state.current_player;
        let tile = DomeTile::new(61, vec![DomeSpace::special(), DomeSpace::wild(), DomeSpace::wild(), DomeSpace::wild()], 0);
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("frei");
        let voll = [crate::tile::TILES_PER_COLOR as i64; 5];
        let k = special_kosten(&game.state.players[pi], 0, 0, &voll);
        assert!(
            (k - 0.6).abs() < 1e-9,
            "3 Wild-Nachbarn muessen 3*0,2=0,6 kosten (statt der ALT-Formel 0,3+0,8*3=2,7): war {k}"
        );
        set_special_override_for_test(None);
    }

    #[test]
    fn ist_spalte_vollendbar_par16_prueft_special_nachbarn() {
        set_special_override_for_test(Some(true));
        let mut game = drafting_game(52);
        let pi = game.state.current_player;
        // Slot (0,0): si0=Special(Zeile0,Spalte0), si1=Rot(Zeile0,Spalte1),
        // si2=Wild(Zeile1,Spalte0), si3=Wild(Zeile1,Spalte1).
        let tile = DomeTile::new(62, vec![DomeSpace::special(), DomeSpace::normal(Rot), DomeSpace::wild(), DomeSpace::wild()], 0);
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("frei");
        let voll = [crate::tile::TILES_PER_COLOR as i64; 5];
        assert!(
            ist_spalte_vollendbar(&game.state.players[pi], 0, &voll),
            "bei voller Versorgung muss Spalte 0 vollendbar sein (Special-Nachbar Rot ist erreichbar)"
        );

        let mut leer_rot = voll;
        leer_rot[crate::provocation::farben_index(Rot).unwrap()] = 0;
        assert!(
            !ist_spalte_vollendbar(&game.state.players[pi], 0, &leer_rot),
            "Rot komplett verbraucht -- der Special-Nachbar (Zeile0,Spalte1) braucht 1 Kopie, die nicht mehr da ist"
        );
        set_special_override_for_test(None);
    }

    #[test]
    fn ist_spalte_vollendbar_default_ignoriert_special_wie_par14() {
        let mut game = drafting_game(52);
        let pi = game.state.current_player;
        let tile = DomeTile::new(62, vec![DomeSpace::special(), DomeSpace::normal(Rot), DomeSpace::wild(), DomeSpace::wild()], 0);
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("frei");
        let mut leer_rot = [crate::tile::TILES_PER_COLOR as i64; 5];
        leer_rot[crate::provocation::farben_index(Rot).unwrap()] = 0;
        assert!(
            ist_spalte_vollendbar(&game.state.players[pi], 0, &leer_rot),
            "Default AUS: Special-Zeilen bleiben unberuecksichtigt, auch wenn ihr Nachbar Rot ausgeschoepft ist"
        );
    }

    #[test]
    fn special_nachbar_zellen_liefert_die_drei_slot_nachbarn_nur_wenn_aktiv() {
        let mut game = drafting_game(53);
        let pi = game.state.current_player;
        let tile = DomeTile::new(63, vec![DomeSpace::special(), DomeSpace::normal(Rot), DomeSpace::wild(), DomeSpace::normal(Blau)], 0);
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("frei");

        assert!(
            special_nachbar_zellen(&game.state.players[pi], 0).is_empty(),
            "Default AUS muss leer liefern"
        );

        set_special_override_for_test(Some(true));
        let mut zellen = special_nachbar_zellen(&game.state.players[pi], 0);
        zellen.sort();
        assert_eq!(zellen, vec![(0, 1), (1, 0), (1, 1)]);
        set_special_override_for_test(None);
    }

    #[test]
    fn vorzugszug_bedient_special_nachbarn_wenn_zielspalte_selbst_nichts_findet() {
        set_aktiv_override_for_test(Some(true));
        set_special_override_for_test(Some(true));
        let mut game = drafting_game(54);
        let pi = game.state.current_player;
        // Slot (0,0): si0=Special(Zeile0,Spalte0), si1=Rot(Zeile0,Spalte1),
        // si2=Wild(Zeile1,Spalte0), si3=Wild(Zeile1,Spalte1).
        let tile = DomeTile::new(64, vec![DomeSpace::special(), DomeSpace::normal(Rot), DomeSpace::wild(), DomeSpace::wild()], 0);
        game.state.players[pi].dome_grid.place_dome_tile(tile, 0, 0).expect("frei");
        // Zeile1/Spalte0 (Wild) schon gefuellt -- Spalte 0s einzige noch
        // offene EIGENE Zelle ist danach die Special-Zeile selbst, die
        // `vorzugszug_fuer_spalte` nie qualifiziert (space_type Special).
        {
            let slot = game.state.players[pi].dome_grid.dome_slots[0][0].as_mut().unwrap();
            slot.spaces[2].placed_color = Some(Schwarz);
        }
        for f in game.state.factories.iter_mut() {
            f.sun_tiles.clear();
            f.moon_stacks.clear();
        }
        game.state.large_factory.sun_tiles.clear();
        game.state.large_factory.moon_pool.clear();
        game.state.factories[0].sun_tiles = vec![Rot, Rot];

        assert_eq!(ziel_spalte(&game.state), Some(0), "Testvoraussetzung: Spalte 0 muss Ziel sein");
        assert!(
            crate::provocation::vorzugszug_fuer_spalte(&game.state, 0).is_none(),
            "Testvoraussetzung: die Zielspalte selbst darf keinen Kandidaten liefern (Special qualifiziert nie)"
        );

        let aktion = vorzugszug(&game.state).expect("die Special-Nachbar-Stufe muss greifen");
        match aktion {
            Action::Stone(m) => {
                assert_eq!(m.take.color, Rot);
                assert_eq!(m.place.row_index, 0, "muss die Special-Nachbarzelle (Zeile0,Spalte1) bedienen");
            }
            other => panic!("erwartet Stone, bekam {other:?}"),
        }
        set_special_override_for_test(None);
        set_aktiv_override_for_test(None);
    }
}
