//! Exakter Brute-Force-Solver (DFS) für die Tiling-Phase.
//!
//! Tiling ist ein Solo-Puzzle pro Spieler mit sehr geringer Tiefe (≤6 Reihen)
//! und — laut Regel: **während des Tilings werden KEINE Kuppelplatten gelegt** —
//! sehr wenig Verzweigung. Daher kein MCTS, sondern eine rekursive Maximierung:
//! finde die Platzierungs-/Chip-Folge, die den Runden-Score des Spielers
//! maximiert. Genutzt (a) als Pseudo-Terminal-Bewertung am Drafting→Tiling-
//! Übergang im MCTS und (b) für den echten Tiling-Zug der KI.
//!
//! Zugmenge: nur Steine auf BEREITS gelegte Kuppel-Spaces (`generate_tiling_actions`
//! erzeugt von sich aus nur solche -- kein separater Filter mehr nötig) +
//! Bonus-Chip-Komplettierung passender Reihen. Reihenfolge oben→unten
//! (Regelwerk S.7) steckt bereits in `validate_tiling_action`/`generate_tiling_actions`.

use crate::board::FIRST_PLAYER_MARKER_PENALTY;
use crate::round_end::{
    apply_bonus_chips_with, can_complete_row_with_chips, chip_allocations, execute_full_tiling,
    generate_tiling_actions, greedy_chip_alloc, row_has_open_matching_slot, TilingAction,
};
use crate::state::GameState;

/// Defensive Rekursionsgrenze (Branching ist klein; nur als Sicherung).
const MAX_DEPTH: u32 = 30;

/// Globales Knoten-Budget für EINEN Solver-Aufruf. `MAX_DEPTH` begrenzt nur die
/// Tiefe, nicht die Breite — bei `exact=true` verzweigt `legal_steps` bei JEDEM
/// Rekursionsschritt über ALLE Chip-Allokationen (2^n), nicht nur einmal. Bei
/// mehreren gleichzeitig „chippable" Reihen mit vielen Farboptionen kann das
/// kombinatorisch explodieren (beobachtet: Self-Play hing >30min in einem
/// einzelnen `best_first_step_exact`-Aufruf, unerreichbar für den Hänger-Schutz
/// in self_play.rs, der nur ZWISCHEN Zügen prüft). Bei Erschöpfung bricht die
/// Suche ab und liefert das bisher beste Ergebnis — degradiert graceful zu
/// suboptimal statt zu hängen.
///
/// WICHTIG: ein „Knoten" ist hier NICHT billig — `chip_allocations` (Aufruf in
/// `legal_steps`, einmal PRO chippable Reihe PRO Knoten) kann bis zu 2^14
/// Teilmengen prüfen (`CHIP_ALLOC_CAP=14`), inkl. Set-/String-Allokationen je
/// Teilmenge. Ein erster Versuch mit 200_000 war deshalb immer noch viel zu
/// hoch (200_000 Knoten × mehrere teure Chip-Allokations-Aufrufe ≈
/// Milliarden Operationen, erneut >30min gehangen). 2_000 hält den
/// Worst-Case auf niedrige zweistellige Sekunden begrenzt und liegt weit über
/// dem, was normale Partien tatsächlich brauchen (Branching ist laut
/// Doc-Kommentar oben klein).
const NODE_BUDGET: u32 = 2_000;

/// Task #16: Endwertungs-Bewusstsein für die Tiling-ZUGWAHL.
///
/// BEFUND (2026-07-28): `best_first_step_inner` maximiert `pts + solve_rec(..)`,
/// also **reine Sofortpunkte der Runde**. `calculate_end_scoring` bzw.
/// `wertung_progress` kommen im gesamten Modul nicht vor. Da
/// `best_first_step_exact` der Pfad für ALLE echten Platzierungen ist
/// (`self_play.rs:894`, `py.rs:687`, `round_transition.rs:135/323`), wählt die
/// KI ihre Steine, ohne die Wertungsplatten je zu berücksichtigen — auch wenn
/// die darüberliegende Suche sie sehr wohl bewertet.
///
/// Die Heuristik macht es seit jeher anders: `mcts::player_total` =
/// `solve_round_final_score` **+ `wertung_progress`** + Straf-Term. Dieses
/// Shaping überträgt denselben Term auf die Zugwahl des Solvers — deshalb
/// Gewicht 1.0, dieselben Einheiten (Rundenpunkte), dieselbe Ersatzformel.
///
/// BEWUSST NUR auf der ersten Stufe (`best_first_step_inner`), NICHT in
/// `solve_rec`: (a) `solve_rec` ist der Blatt-Bewertungs-Hot-Path des MCTS,
/// dort würde der Term mit `player_total`s eigenem `wertung_progress`
/// DOPPELT zählen; (b) die erste Stufe ist die, die den Zug tatsächlich
/// bestimmt. Der Fortschritts-Delta wird daher nur über den ersten Schritt
/// gemessen, nicht über den ganzen Rollout — Unterschätzung in Kauf genommen,
/// weil `solve_rec` nur den Score liefert, nicht den Endzustand.
///
/// STAND: **AUS -- A/B GEFAHREN UND VERWORFEN (2026-07-29).**
///
/// Gepaarter Arena-A/B, `v18_best`@400 vs `v17_best`@400, 1600 Spiele
/// (2 Blöcke à 400 je Arm, identischer Basis-Seed innerhalb jedes Blocks,
/// `tools/paired_arena_plate_ab.py` + `tools/pool_arena_ab.py`):
///
/// | Block | OFF | ON | b(nur ON) | c(nur OFF) | p |
/// |---|---|---|---|---|---|
/// | 1 (Seed 5150271)  | 226 | 245 | 63 | 44 | 0,0814 |
/// | 2 (Seed 77150271) | 228 | 219 | 50 | 59 | 0,4437 |
/// | gepoolt           | 454 | 464 | 113 | 103 | **0,5404** |
///
/// Block 1 sah mit p=0,0814 nach einem Effekt aus, Block 2 kehrte die Richtung
/// um. Gepoolt ein Münzwurf. Auch der Ø-Score beider Seiten ist inkonsistent
/// (Summe Block 1: 74,0 OFF vs 73,9 ON; gepoolt 73,4 vs 74,1) -- kein Signal.
///
/// LEHRE, die den Aufwand wert war: hätte man nach Block 1 auf p=0,08
/// übernommen, wäre eine wirkungslose Änderung eingebaut UND der Elo-Anker
/// unnötig entwertet worden (der Solver ist gemeinsamer Code, er ändert auch
/// die Heuristik-Spielstärke). Replizieren statt auf ein knappes p zu handeln.
///
/// Der Code bleibt inert erhalten -- der zugrundeliegende BEFUND stimmt ja
/// weiterhin (der Solver ist endwertungsblind, die Heuristik darüber nicht).
/// Er ist nur an dieser Stelle offenbar nicht spielentscheidend.
pub const TILING_SHAPING_ENABLED: bool = false;

/// Gewicht des Fortschritts-Terms. 1.0 = exakt die Gewichtung, mit der
/// `mcts::player_total` denselben Term seit jeher führt.
pub const TILING_SHAPING_WEIGHT: f64 = 1.0;

/// Task #21: exakte Endwertung in der Runde-5-Tiling-Zugwahl.
/// Standard AUS bis gemessen ist, wie oft sie ueberhaupt einen anderen Zug
/// waehlt -- dieselbe Disziplin wie bei TILING_SHAPING_ENABLED.
pub const ROUND5_ENDSCORING_ENABLED: bool = false;

/// Ein Tiling-Schritt im Solver. `Chips` trägt die konkrete Plättchen-Auswahl
/// (Indizes in `bonus_chips`), damit der reale KI-Zug exakt dem Solver-Plan folgt.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TilingStep {
    Place(TilingAction),
    Chips { row: usize, chips: Vec<usize> },
    End,
}

/// Mit Bonusplättchen komplettierbare Reihen, die danach platzierbar sind
/// (Reihenfolge oben→unten via `tiled_max_row` respektiert).
fn chippable_rows(state: &GameState, pi: usize) -> Vec<usize> {
    let player = &state.players[pi];
    if player.bonus_chips.is_empty() {
        return Vec::new();
    }
    let tiled_max = player.tiled_max_row;
    let mut out = Vec::new();
    for (ri, row) in player.pattern_lines.iter().enumerate() {
        if row.tiles.is_empty() || row.is_complete() {
            continue;
        }
        if (ri as i32) < tiled_max {
            continue;
        }
        if !can_complete_row_with_chips(player, ri) {
            continue;
        }
        let color = match row.color {
            Some(c) => c,
            None => continue,
        };
        if row_has_open_matching_slot(player, ri, color) {
            out.push(ri);
        }
    }
    out
}

/// Legale Solver-Schritte: Steine auf bestehende Platten (kein Display) + Chips.
///
/// `exact` steuert die Plättchen-Allokation:
/// - `false` (Hot-Path, MCTS-Blätter): EINE Greedy-Allokation pro Reihe. Das
///   Verzweigen über ALLE 2^n-Allokationen wäre hier unbezahlbar (E2E 8 s→75 s+).
/// - `true` (nur der echte KI-Zug, einmal pro Tiling-Schritt): alle distinkten
///   Allokationen → exakt optimale Chip-Nutzung im tatsächlich gespielten Zug.
fn legal_steps(state: &GameState, pi: usize, exact: bool) -> Vec<TilingStep> {
    let mut steps: Vec<TilingStep> = generate_tiling_actions(state, pi)
        .into_iter()
        .map(TilingStep::Place)
        .collect();
    for row in chippable_rows(state, pi) {
        if exact {
            for chips in chip_allocations(&state.players[pi], row) {
                steps.push(TilingStep::Chips { row, chips });
            }
        } else if let Some(chips) = greedy_chip_alloc(&state.players[pi], row) {
            steps.push(TilingStep::Chips { row, chips });
        }
    }
    steps
}

/// Wendet einen Schritt auf einen Klon an. Gibt (Folgezustand, Sofortpunkte)
/// zurück. None bei `End` oder fehlgeschlagenem Zug.
fn apply_step(state: &GameState, pi: usize, step: &TilingStep) -> Option<(GameState, i32)> {
    match step {
        TilingStep::Place(ta) => {
            let mut s = state.clone();
            let pts = execute_full_tiling(&mut s, pi, ta).ok()?;
            Some((s, pts))
        }
        TilingStep::Chips { row, chips } => {
            let mut s = state.clone();
            if !apply_bonus_chips_with(&mut s.players[pi], *row, chips) {
                return None;
            }
            Some((s, 0))
        }
        TilingStep::End => None,
    }
}

fn solve_rec(state: &GameState, pi: usize, depth: u32, exact: bool, budget: &mut u32) -> i32 {
    if depth >= MAX_DEPTH || *budget == 0 {
        return 0;
    }
    *budget -= 1;
    let steps = legal_steps(state, pi, exact);
    if steps.is_empty() {
        return 0;
    }
    // Baseline 0 = „hier aufhören". Platzierungen liefern stets ≥1, Chips 0
    // (schalten aber Platzierungen frei) — der maximierende Pfad gewinnt.
    let mut best = 0;
    for step in &steps {
        if *budget == 0 {
            break; // Budget erschöpft: bisher bestes Ergebnis liefern statt hängen.
        }
        if let Some((next, pts)) = apply_step(state, pi, step) {
            let total = pts + solve_rec(&next, pi, depth + 1, exact, budget);
            if total > best {
                best = total;
            }
        }
    }
    best
}

/// Maximal erreichbare Tiling-Punkte (Linien + Spezial-Boni) für Spieler `pi`,
/// ausgehend vom aktuellen Brett (Drafting-Ende). GREEDY-Chips (Hot-Path).
pub fn solve_max_tiling_points(state: &GameState, pi: usize) -> i32 {
    let mut budget = NODE_BUDGET;
    solve_rec(state, pi, 0, false, &mut budget)
}

/// Wie `solve_max_tiling_points`, aber mit exakter Chip-Allokationssuche.
/// Nur für den echten KI-Zug (einmalig) gedacht — NICHT für MCTS-Blätter.
pub fn solve_max_tiling_points_exact(state: &GameState, pi: usize) -> i32 {
    let mut budget = NODE_BUDGET;
    solve_rec(state, pi, 0, true, &mut budget)
}

/// Optimaler finaler Runden-Score für Spieler `pi`: aktueller Score +
/// max. Tiling-Punkte + (fixe) Boden-/Marker-Strafen.
pub fn solve_round_final_score(state: &GameState, pi: usize) -> i32 {
    let p = &state.players[pi];
    let penalty = p.broken_penalty()
        + if p.holds_first_player_marker { FIRST_PLAYER_MARKER_PENALTY } else { 0 };
    p.score + penalty + solve_max_tiling_points(state, pi)
}

/// Blatt-Rekursion für [`solve_round_final_score_endaware`]: wie `solve_rec`,
/// aber an jedem BLATT (keine legalen Schritte mehr, Tiefen-/Budget-Deckel
/// erreicht) wird zusätzlich `calculate_end_scoring` des dort erreichten
/// Bretts aufaddiert, und die SUMME aus Platzierungspunkten + Endwertung wird
/// maximiert statt nur die Punkte. Die "hier aufhören"-Baseline (siehe
/// `solve_rec`-Kommentar: Stoppen ist immer eine erlaubte Alternative) ist
/// hier folgerichtig nicht mehr 0, sondern die Endwertung des Bretts VOR
/// diesem Schritt -- Stoppen ist ja selbst ein gültiges Blatt.
///
/// EIGENE Rekursion statt Wiederverwendung von `solve_rec`: `solve_rec` ist
/// der Blatt-Bewertungs-Hot-Path der Runden 1-4 (MCTS, `solve_max_tiling_points`)
/// und bleibt unangetastet. GREEDY-Chip-Politik (`exact=false`, wie der
/// Hot-Path) und dasselbe `NODE_BUDGET`-Muster, weil diese Funktion an JEDEM
/// Alpha-Beta-Blatt in Runde 5 läuft (`round5::player_total_exact`, hinter
/// `ROUND5_ENDSCORING_ENABLED`) -- eine exakte Chip-Allokationssuche wäre dort
/// unbezahlbar teuer.
fn solve_rec_endaware(state: &GameState, pi: usize, depth: u32, budget: &mut u32) -> i32 {
    let end_here =
        crate::scoring::calculate_end_scoring(&state.players[pi], &state.scoring_tile_ids).total;
    if depth >= MAX_DEPTH || *budget == 0 {
        return end_here;
    }
    *budget -= 1;
    let steps = legal_steps(state, pi, false);
    if steps.is_empty() {
        return end_here;
    }
    // Baseline = Endwertung DIESES Bretts ("hier aufhören", siehe Doc oben).
    let mut best = end_here;
    for step in &steps {
        if *budget == 0 {
            break; // Budget erschöpft: bisher bestes Ergebnis liefern statt hängen.
        }
        if let Some((next, pts)) = apply_step(state, pi, step) {
            let total = pts + solve_rec_endaware(&next, pi, depth + 1, budget);
            if total > best {
                best = total;
            }
        }
    }
    best
}

/// Task #21: wie [`solve_round_final_score`], aber die Rekursion wertet am
/// BLATT zusätzlich `calculate_end_scoring` des dort erreichten Bretts aus und
/// maximiert die SUMME (Rundenpunkte + Endwertung) statt allein die Punkte.
///
/// Nur für Runde 5 sinnvoll -- dort ist `calculate_end_scoring` exakt (kein
/// Näherungsfehler, das Kuppelraster ändert sich nicht mehr, siehe
/// `round5.rs`-Modul-Kommentar). Aufgerufen von `round5::player_total_exact`
/// hinter `ROUND5_ENDSCORING_ENABLED` -- dort ersetzt sie die bisherige Summe
/// `solve_round_final_score(..) + calculate_end_scoring(Brett DAVOR, ..)`,
/// die sich auf zwei VERSCHIEDENE Brettzustände bezog (siehe Doc dort).
pub fn solve_round_final_score_endaware(state: &GameState, pi: usize) -> i32 {
    let p = &state.players[pi];
    let penalty = p.broken_penalty()
        + if p.holds_first_player_marker { FIRST_PLAYER_MARKER_PENALTY } else { 0 };
    let mut budget = NODE_BUDGET;
    p.score + penalty + solve_rec_endaware(state, pi, 0, &mut budget)
}

/// Optimaler nächster Tiling-Schritt für Spieler `pi`. `End`, wenn nichts mehr
/// platzierbar/komplettierbar ist. `exact` → exakte Chip-Allokationssuche
/// (nur für den echten Zug verwenden, NICHT pro MCTS-Blatt).
fn best_first_step_inner(state: &GameState, pi: usize, exact: bool) -> TilingStep {
    let steps = legal_steps(state, pi, exact);
    if steps.is_empty() {
        return TilingStep::End;
    }
    let mut budget = NODE_BUDGET;
    let mut best_step = TilingStep::End;
    let mut best_val = f64::NEG_INFINITY;
    // Basis-Fortschritt EINMAL vor der Schleife: der Shaping-Term ist ein
    // Delta gegen den Zustand VOR dem Schritt (siehe TILING_SHAPING_ENABLED).
    let base_progress = if TILING_SHAPING_ENABLED {
        crate::scoring::wertung_progress(&state.players[pi], &state.scoring_tile_ids)
    } else {
        0.0
    };
    for step in steps {
        if budget == 0 {
            break; // Budget erschöpft: bisher besten Schritt liefern statt hängen.
        }
        if let Some((next, pts)) = apply_step(state, pi, &step) {
            let mut val = f64::from(pts + solve_rec(&next, pi, 1, exact, &mut budget));
            if TILING_SHAPING_ENABLED {
                let delta = crate::scoring::wertung_progress(
                    &next.players[pi],
                    &next.scoring_tile_ids,
                ) - base_progress;
                val += TILING_SHAPING_WEIGHT * delta;
            }
            if val > best_val {
                best_val = val;
                best_step = step;
            }
        }
    }
    best_step
}

/// Task #20: bis zu `k` VOLLSTAENDIGE Tiling-Abschluesse mit ihren
/// Folgezustaenden, absteigend nach Rundenpunkten.
///
/// Der bestehende Solver liefert nur EINEN Schritt und nur dessen Score. Fuer
/// eine netz-gefuehrte Auswahl braucht es die fertigen Bretter -- das Netz
/// bewertet den Zustand, aus dem die naechste Runde startet.
///
/// BEWUSST eine eigene Funktion: der Hot-Path (`solve_rec`,
/// `solve_round_final_score`, MCTS-Blattbewertung) bleibt unangetastet.
///
/// Abbruch ueber dasselbe `NODE_BUDGET` wie der Solver plus eine Blatt-Obergrenze
/// -- bei mehreren chippable Reihen kann der Baum sonst explodieren.
/// Entartete Reihenfolgen (dieselben Steine, andere Reihenfolge) fuehren auf
/// dasselbe Brett; dedupliziert wird ueber die Belegungssignatur, sonst
/// erschiene die Value-Spreizung kuenstlich klein.
const MAX_TILING_LEAVES: usize = 400;

/// Kanonische Signatur eines Tiling-ABSCHLUSSES: Kuppelfuellung UND
/// verbleibender Bonuschip-Bestand.
///
/// BEFUND (2026-07-29): die alte Signatur (`dome_fill_signature`, nur die 36
/// Fuellungs-Bools) verschmolz zwei Abschluesse mit identischem Endbrett aber
/// UNTERSCHIEDLICHEM Chip-Rest -- verschiedene `chip_allocations` koennen
/// dieselbe Reihenkomplettierung mit verschiedenen Chips erreichen. Der
/// Abschluss mit weniger verbrauchten Chips wurde dabei verworfen, obwohl
/// uebrige Bonuschips Zukunftskapital fuer spaetere Runden sind (sie wandern
/// mit ins naechste Runden-Setup). Fuer die geplante netz-gefuehrte Auswahl
/// (das Netz bewertet den FOLGEZUSTAND, nicht nur die Rundenpunkte) ist der
/// Chip-Rest ein echter Unterschied zwischen zwei sonst identischen Brettern.
///
/// Jeder Chip wird durch die sortierte Liste seiner Farbnamen kodiert
/// (mehrfarbige Chips tragen 1-2 Farben), die Chip-Liste selbst wird
/// anschliessend sortiert -- die Signatur ist damit unabhaengig von der
/// Reihenfolge im `bonus_chips`-Vec (reine Permutationen desselben Bestands
/// duerfen NICHT als unterschiedlich gelten, sonst waechst die Kandidatenzahl
/// kuenstlich).
fn tiling_outcome_signature(state: &GameState, pi: usize) -> (Vec<bool>, Vec<String>) {
    let mut fill = Vec::with_capacity(36);
    for sr in 0..3 {
        for sc in 0..3 {
            match &state.players[pi].dome_grid.dome_slots[sr][sc] {
                Some(slot) => {
                    for si in 0..4 {
                        fill.push(slot.spaces.get(si).map_or(false, |sp| sp.placed_color.is_some()));
                    }
                }
                None => fill.extend_from_slice(&[false; 4]),
            }
        }
    }
    let mut chips: Vec<String> = state.players[pi]
        .bonus_chips
        .iter()
        .map(|c| {
            let mut colors: Vec<String> = c.colors.iter().map(|col| format!("{col:?}")).collect();
            colors.sort();
            colors.join(",")
        })
        .collect();
    chips.sort();
    (fill, chips)
}

/// Ein vollstaendiger Tiling-Abschluss: Rundenpunkte, der ERSTE Schritt dorthin
/// (das ist der Zug, den der Solver zurueckgeben muss) und das fertige Brett.
pub struct TilingOutcome {
    pub points: i32,
    pub first_step: TilingStep,
    pub final_state: GameState,
}

fn collect_tilings(
    state: &GameState,
    pi: usize,
    acc: i32,
    first: Option<&TilingStep>,
    depth: u32,
    budget: &mut u32,
    out: &mut Vec<TilingOutcome>,
) {
    if *budget == 0 || out.len() >= MAX_TILING_LEAVES || depth >= MAX_DEPTH {
        return;
    }
    let steps = legal_steps(state, pi, true);
    if steps.is_empty() {
        if let Some(f) = first {
            out.push(TilingOutcome {
                points: acc,
                first_step: f.clone(),
                final_state: state.clone(),
            });
        }
        return;
    }
    for step in steps {
        if *budget == 0 || out.len() >= MAX_TILING_LEAVES {
            break;
        }
        *budget -= 1;
        if let Some((next, pts)) = apply_step(state, pi, &step) {
            let f = first.unwrap_or(&step).clone();
            collect_tilings(&next, pi, acc + pts, Some(&f), depth + 1, budget, out);
        }
    }
}

/// Bis zu `k` vollstaendige Abschluesse, absteigend nach Punkten, ohne
/// Duplikate gleicher Endbelegung.
pub fn top_k_tilings(state: &GameState, pi: usize, k: usize) -> Vec<TilingOutcome> {
    let mut out: Vec<TilingOutcome> = Vec::new();
    let mut budget = NODE_BUDGET;
    collect_tilings(state, pi, 0, None, 0, &mut budget, &mut out);
    out.sort_by(|a, b| b.points.cmp(&a.points));
    let mut seen: Vec<(Vec<bool>, Vec<String>)> = Vec::new();
    let mut uniq: Vec<TilingOutcome> = Vec::new();
    for o in out {
        let sig = tiling_outcome_signature(&o.final_state, pi);
        if seen.iter().any(|s| *s == sig) {
            continue;
        }
        seen.push(sig);
        uniq.push(o);
        if uniq.len() >= k {
            break;
        }
    }
    uniq
}

/// Task #21: Tiling-Zugwahl in Runde 5 mit EXAKTER Endwertung.
///
/// In den Runden 1-4 ist die Zukunft offen -- jede Endwertungs-Beruecksichtigung
/// im Tiling ist dort eine Wette auf eine Absicht, die das Netz vielleicht gar
/// nicht hat. Genau daran ist Task #16 gescheitert (1600 Spiele, p=0,5404).
///
/// In Runde 5 endet das Spiel NACH dem Tiling. Die Endwertung des fertigen
/// Bretts ist damit exakt berechenbar -- kein Proxy, keine Unsicherheit, kein
/// Gewicht. Maximiert wird deshalb
///
/// ```text
/// Rundenpunkte(Abschluss) + calculate_end_scoring(Brett NACH dem Abschluss)
/// ```
///
/// statt allein die Rundenpunkte.
///
/// WARUM DAS EIN KORREKTHEITS-FIX IST, kein Tuning: `round5::player_total_exact`
/// rechnet heute `solve_round_final_score` (Punkte des punktemaximalen Tilings)
/// PLUS `calculate_end_scoring` des Bretts DAVOR. Die beiden Terme beziehen sich
/// auf verschiedene Brettzustaende -- gerade die Steine, die Reihen, Spalten und
/// Diagonalen schliessen und damit die Endwertung treiben, fehlen in der
/// Endwertungs-Rechnung. Zwei Drafting-Zuege mit gleichen Rundenpunkten, aber
/// unterschiedlich viel ERREICHBARER Endwertung, sind dadurch fuer die
/// Alpha-Beta-Suche ununterscheidbar.
///
/// Bedingung ist bewusst `round_number >= 5` und NICHT `round5::applies`:
/// letzteres verlangt zusaetzlich `phase == Drafting` und waere im Tiling --
/// also genau hier -- immer falsch.
///
/// Nur im echten Zug: `best_first_step_exact` ruft das, `solve_rec` und die
/// MCTS-Blattbewertung bleiben unberuehrt.
fn best_first_step_round5(state: &GameState, pi: usize) -> Option<TilingStep> {
    let cands = top_k_tilings(state, pi, MAX_TILING_LEAVES);
    let best = cands.into_iter().max_by_key(|o| {
        o.points
            + crate::scoring::calculate_end_scoring(
                &o.final_state.players[pi],
                &o.final_state.scoring_tile_ids,
            )
            .total
    })?;
    Some(best.first_step)
}

/// Greedy-Variante (Hot-Path / Tests).
pub fn best_first_step(state: &GameState, pi: usize) -> TilingStep {
    best_first_step_inner(state, pi, false)
}

/// Exakte Variante für den tatsächlich gespielten KI-Tiling-Zug: durchsucht die
/// Chip-Allokationen, damit mehrfarbige Plättchen im Engpass optimal verteilt
/// werden. Wird nur einmal pro Zug aufgerufen → bezahlbar.
pub fn best_first_step_exact(state: &GameState, pi: usize) -> TilingStep {
    // Task #21: in Runde 5 ist die Endwertung exakt berechenbar (das Spiel endet
    // nach diesem Tiling) -- dort wird sie mitmaximiert statt ignoriert.
    if ROUND5_ENDSCORING_ENABLED && state.round_number >= 5 {
        if let Some(step) = best_first_step_round5(state, pi) {
            return step;
        }
    }
    best_first_step_inner(state, pi, true)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::board::PlayerBoard;
    use crate::dome::build_dome_tile_pool;
    use crate::state::{setup_new_game, Phase};
    use crate::tile::TileColor::*;
    use rand::rngs::StdRng;
    use rand::RngExt;
    use rand::SeedableRng;

    fn tiling_state(seed: u64) -> GameState {
        let mut rng = StdRng::seed_from_u64(seed);
        let mut s = setup_new_game(["P1".into(), "P2".into()], 0, &mut rng);
        for p in s.players.iter_mut() {
            p.start_tile_pending = false;
        }
        s.phase = Phase::Tiling;
        s
    }

    #[test]
    fn solo_full_row_scores_one() {
        let mut s = tiling_state(7);
        // Slot (0,0) = pool[2] = [Tuerkis, Rot, Blau, Wild]; si1 = Rot.
        let tile = build_dome_tile_pool()[2].clone();
        s.players[0].dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        s.players[0].pattern_lines[0].add_tiles(&[Rot]); // volle Reihe 0
        // Genau ein platzierbarer Stein, alleinstehend → 1 Punkt.
        assert_eq!(solve_max_tiling_points(&s, 0), 1);
        // best_first_step platziert (kein End).
        assert!(matches!(best_first_step(&s, 0), TilingStep::Place(_)));
    }

    #[test]
    fn no_placeable_row_yields_end_and_zero() {
        let s = tiling_state(7); // leeres Brett, keine vollen Reihen
        assert_eq!(solve_max_tiling_points(&s, 0), 0);
        assert_eq!(best_first_step(&s, 0), TilingStep::End);
    }

    #[test]
    fn solver_matches_engine_when_played_out() {
        // Konsistenz: solve_round_final_score == real durchgespielter Score,
        // wenn man best_first_step bis End anwendet.
        let mut s = tiling_state(7);
        let tile = build_dome_tile_pool()[2].clone(); // si1 = Rot
        s.players[0].dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        s.players[0].pattern_lines[0].add_tiles(&[Rot]);
        let predicted = solve_round_final_score(&s, 0);

        // Real durchspielen (greedy nach Solver).
        let pi = 0;
        loop {
            match best_first_step(&s, pi) {
                TilingStep::Place(ta) => {
                    execute_full_tiling(&mut s, pi, &ta).unwrap();
                }
                TilingStep::Chips { row, chips } => {
                    apply_bonus_chips_with(&mut s.players[pi], row, &chips);
                }
                TilingStep::End => break,
            }
        }
        let realized = s.players[pi].score
            + s.players[pi].broken_penalty()
            + if s.players[pi].holds_first_player_marker { FIRST_PLAYER_MARKER_PENALTY } else { 0 };
        assert_eq!(predicted, realized);
    }

    #[test]
    fn counts_cross_row_vertical_line() {
        // Reihenübergreifende Linie: Reihe 1 (Schwarz) → 6x6 (0,1), Reihe 2
        // (Schwarz) → 6x6 (1,1, Wild). Zusammen vertikale Linie → 1 + 2 = 3
        // (NICHT 1 + 1 = 2, wie die per-Reihe-Heuristik schätzen würde).
        let mut s = tiling_state(7);
        let tile = build_dome_tile_pool()[11].clone(); // [Tuerkis, Schwarz, Rot, Wild]
        s.players[0].dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        s.players[0].pattern_lines[0].add_tiles(&[Schwarz]);
        s.players[0].pattern_lines[1].add_tiles(&[Schwarz, Schwarz]);
        assert_eq!(solve_max_tiling_points(&s, 0), 3);
        // Erwartete Rundenpunkte (estimated_score) = Solver-Score − aktueller Score.
        assert_eq!(solve_round_final_score(&s, 0) - s.players[0].score, 3);
    }

    #[test]
    fn uses_chips_to_complete_and_place() {
        use crate::dome::BonusChip;
        let mut s = tiling_state(7);
        // Reihe 2 (cap 3): 1 Rot → 2 fehlen; 4 Rot-Chips → komplettierbar.
        s.players[0].pattern_lines[2].add_tiles(&[Rot]);
        for i in 0..4 {
            s.players[0].bonus_chips.push(BonusChip { chip_id: i, colors: vec![Rot] });
        }
        // Dome-Reihe 1 (Reihe 2 → dome_row 1), Slot mit offenem Rot an si0/si1:
        // pool[2] si1 = Rot.
        let tile = build_dome_tile_pool()[2].clone();
        s.players[0].dome_grid.place_dome_tile(tile, 1, 0).unwrap();
        // Ohne Chips: Reihe 2 nicht voll → 0 Punkte. Mit Chips: komplettieren +
        // platzieren → ≥1 Punkt. Solver muss die Chip-Option nutzen.
        assert!(solve_max_tiling_points(&s, 0) >= 1);
        let first = best_first_step(&s, 0);
        assert!(matches!(first, TilingStep::Chips { row: 2, .. } | TilingStep::Place(_)));
    }

    #[test]
    fn greedy_chip_alloc_tradeoff_in_contention() {
        use crate::dome::BonusChip;
        // Engpass: 2 Doppel-Chips [blau,rot] + [blau] + [rot]. Reihe 3 (Rot,
        // fehlt 1) und Reihe 4 (Blau, fehlt 1) je per 2 farbgleichen Chips
        // komplettierbar. Der DFS nutzt im Hot-Path die GREEDY-Allokation: sie
        // verbrennt beide Doppel-Chips auf die erste Reihe → nur 1 Reihe legbar.
        // (Die exakte Allokationssuche käme auf 3, ist aber an jedem MCTS-Blatt
        // zu teuer — bewusster Tradeoff; `chip_allocations` bleibt dafür da.)
        let mut s = tiling_state(7);
        // Slot (1,0) = pool[2] [Tuerkis, Rot, Blau, Wild]:
        //   si1 = Rot @ 6x6 (2,1) → Reihe 3 (idx 2, valid_si [0,1]).
        //   si2 = Blau @ 6x6 (3,0) → Reihe 4 (idx 3, valid_si [2,3]).
        let tile = build_dome_tile_pool()[2].clone();
        s.players[0].dome_grid.place_dome_tile(tile, 1, 0).unwrap();
        s.players[0].pattern_lines[2].add_tiles(&[Rot, Rot]); // cap 3 → 1 fehlt
        s.players[0].pattern_lines[3].add_tiles(&[Blau, Blau, Blau]); // cap 4 → 1 fehlt
        s.players[0].bonus_chips = vec![
            BonusChip { chip_id: 0, colors: vec![Blau, Rot] },
            BonusChip { chip_id: 1, colors: vec![Blau, Rot] },
            BonusChip { chip_id: 2, colors: vec![Blau] },
            BonusChip { chip_id: 3, colors: vec![Rot] },
        ];
        // Greedy-DFS (Hot-Path): verbrennt beide Doppel-Chips → nur 1 Reihe = 1.
        assert_eq!(solve_max_tiling_points(&s, 0), 1);
        // EXAKT (echter Zug): beide Reihen legbar; Blau aufs Wild-Feld (3,1)
        // bildet mit Rot auf (2,1) eine vertikale Linie → 1 + 2 = 3.
        assert_eq!(solve_max_tiling_points_exact(&s, 0), 3);
        // Der erste exakte Schritt ist ein kontentionsschonender Chip-Schritt.
        assert!(matches!(best_first_step_exact(&s, 0), TilingStep::Chips { .. }));
    }

    #[test]
    fn chip_allocations_offers_distinct_choices() {
        use crate::dome::BonusChip;
        use crate::round_end::chip_allocations;
        let mut p = PlayerBoard::new(0, "P");
        p.pattern_lines[2].add_tiles(&[Rot, Rot]); // Reihe 3, 1 fehlt
        p.bonus_chips = vec![
            BonusChip { chip_id: 0, colors: vec![Blau, Rot] },
            BonusChip { chip_id: 1, colors: vec![Rot] },
            BonusChip { chip_id: 2, colors: vec![Rot] },
        ];
        // 1 fehlend → 2 rot-tragende ODER 3 beliebige. Mehrere distinkte
        // Allokationen (z.B. {0,1}, {1,2}); deduppliziert nach Farb-Signatur.
        let allocs = chip_allocations(&p, 2);
        assert!(allocs.len() >= 2, "mehrere distinkte Allokationen erwartet: {allocs:?}");
        // Jede Allokation komplettiert die Reihe.
        for a in &allocs {
            let mut q = p.clone();
            assert!(apply_bonus_chips_with(&mut q, 2, a));
            assert!(q.pattern_lines[2].is_complete());
        }
    }

    #[test]
    fn solver_counts_special_bonus_and_neighbor() {
        // Verifikation: (1) Special-Bonus = Reihennummer wird vom Solver gezählt,
        // (2) der ausgelöste Special zählt als Nachbar für eine spätere Fliese.
        //
        // Slot A (0,0) = pool[8] [Tuerkis(si0,(0,0)), Rot(si1,(0,1)),
        //   Blau(si2,(1,0)), Special(si3,(1,1))]. si0/si1 aus "Vorrunden" gefüllt.
        // Slot B (1,0) = pool[2] [Tuerkis(si0), Rot(si1,(2,1)), Blau, Wild].
        let mut s = tiling_state(7);
        s.dome_display.clear(); // nur bestehende Slots nutzbar (deterministisch)

        let mut a = build_dome_tile_pool()[8].clone();
        a.spaces[0].placed_color = Some(Tuerkis); // (0,0)
        a.spaces[1].placed_color = Some(Rot); // (0,1)
        s.players[0].dome_grid.place_dome_tile(a, 0, 0).unwrap();

        let mut b = build_dome_tile_pool()[2].clone();
        b.tile_id = 200;
        s.players[0].dome_grid.place_dome_tile(b, 1, 0).unwrap();

        // Reihe 2 (idx 1, cap 2) → Blau auf Slot A si2 (1,0): füllt das 3. Feld
        //   → Special si3 (1,1) löst aus. Reihe 3 (idx 2, cap 3) → Rot auf (2,1).
        s.players[0].pattern_lines[1].add_tiles(&[Blau, Blau]);
        s.players[0].pattern_lines[2].add_tiles(&[Rot, Rot, Rot]);

        // Erwartung:
        //  - Blau@(1,0): vertikale Linie (0,0)+(1,0) = 2. Special-Bonus: Reihe von
        //    si3 = slot_row*2 + 3/2 = 1 → +2. = 4.
        //  - Rot@(2,1): vertikale Linie (0,1)Rot + (1,1)Special + (2,1)Rot = 3
        //    (Special zählt als gefüllter Nachbar). = 3.
        //  Summe = 7. (Ohne Special-Bonus: 5; ohne Nachbar-Effekt: 5.)
        assert_eq!(solve_max_tiling_points(&s, 0), 7);
    }

    /// Referenz-Implementierung der Zugwahl, beide Varianten getrennt
    /// nachgerechnet -- bewusst dupliziert, damit der Test nicht dieselbe
    /// Codezeile prueft, die er absichern soll.
    fn reference_argmax(state: &GameState, pi: usize, shaped: bool) -> TilingStep {
        let steps = legal_steps(state, pi, true);
        if steps.is_empty() {
            return TilingStep::End;
        }
        let mut budget = NODE_BUDGET;
        let mut best_step = TilingStep::End;
        let mut best_val = f64::NEG_INFINITY;
        let base = crate::scoring::wertung_progress(&state.players[pi], &state.scoring_tile_ids);
        for step in steps {
            if budget == 0 {
                break;
            }
            if let Some((next, pts)) = apply_step(state, pi, &step) {
                let mut val = f64::from(pts + solve_rec(&next, pi, 1, true, &mut budget));
                if shaped {
                    val += TILING_SHAPING_WEIGHT
                        * (crate::scoring::wertung_progress(
                            &next.players[pi],
                            &next.scoring_tile_ids,
                        ) - base);
                }
                if val > best_val {
                    best_val = val;
                    best_step = step;
                }
            }
        }
        best_step
    }

    /// Reiche Tiling-Stellung: volles 3x3-Kuppelraster, ein Teil der Felder
    /// vorbefuellt (erzeugt fast-volle Mosaikreihen/-spalten/-diagonalen, wo
    /// `wertung_progress` grosse Deltas liefert), mehrere gefuellte Musterreihen.
    ///
    /// NOETIG, weil `tiling_state()` allein ein LEERES Kuppelraster hat: dort
    /// gibt `generate_tiling_actions` nichts zurueck, jeder Vergleich waere
    /// `End == End` und damit leer gruen.
    fn rich_state(seed: u64) -> GameState {
        let mut rng = StdRng::seed_from_u64(seed);
        let mut s = tiling_state(seed);
        s.dome_display.clear();
        s.scoring_tile_ids = vec![0, 1, 2]; // Reihen(3) / Spalten(7) / Diagonalen(10)
        let pool = build_dome_tile_pool();
        let mut tid = 300;
        for r in 0..3 {
            for c in 0..3 {
                let mut t = pool[rng.random_range(0..pool.len())].clone();
                t.tile_id = tid;
                tid += 1;
                for si in 0..4 {
                    // ~60% vorbefuellt: genug fuer fast-volle Linien, laesst aber
                    // noch freie Felder fuer echte Zugauswahl.
                    if rng.random_range(0..100) < 60 {
                        t.spaces[si].placed_color = t.spaces[si].required_color;
                    }
                }
                let _ = s.players[0].dome_grid.place_dome_tile(t, r, c);
            }
        }
        s.players[0].pattern_lines[1].add_tiles(&[Blau, Blau]);
        s.players[0].pattern_lines[2].add_tiles(&[Rot, Rot, Rot]);
        s.players[0].pattern_lines[3].add_tiles(&[Tuerkis, Tuerkis, Tuerkis, Tuerkis]);
        s
    }

    #[test]
    fn tiling_shaping_follows_toggle_and_position_discriminates() {
        // Erste Stellung suchen, in der Sofortpunkte und Plattenfortschritt
        // AUSEINANDER zeigen -- sonst wuerde der Test das Shaping nicht pruefen.
        let mut found = None;
        for seed in 1u64..=200 {
            let s = rich_state(seed);
            if legal_steps(&s, 0, true).len() < 2 {
                continue;
            }
            let shaped = reference_argmax(&s, 0, true);
            let unshaped = reference_argmax(&s, 0, false);
            if shaped != unshaped {
                found = Some((seed, s, shaped, unshaped));
                break;
            }
        }
        let (seed, s, shaped, unshaped) = found.expect(
            "keine diskriminierende Stellung in 200 Seeds gefunden -- entweder ist der \
             Shaping-Term wirkungslos oder rich_state() erzeugt keine echten Zugauswahlen",
        );

        let expected = if TILING_SHAPING_ENABLED { &shaped } else { &unshaped };
        assert_eq!(
            &best_first_step_exact(&s, 0),
            expected,
            "Seed {seed}: best_first_step_exact folgt TILING_SHAPING_ENABLED={TILING_SHAPING_ENABLED} nicht"
        );
    }

    #[test]
    fn tiling_shaping_off_is_pure_immediate_points() {
        // Paritaet des f64-Refactors: solange der Toggle AUS ist, muss die
        // Zugwahl exakt die alte i32-Sofortpunkte-Maximierung sein.
        if TILING_SHAPING_ENABLED {
            return;
        }
        let mut checked = 0;
        for seed in 1u64..=60 {
            let s = rich_state(seed);
            if legal_steps(&s, 0, true).is_empty() {
                continue;
            }
            checked += 1;
            assert_eq!(
                best_first_step_exact(&s, 0),
                reference_argmax(&s, 0, false),
                "Seed {seed}: OFF weicht von reiner Sofortpunkte-Maximierung ab"
            );
        }
        // Schutz gegen einen leer gruenen Test.
        assert!(checked >= 20, "nur {checked} Stellungen mit Zuegen geprueft");
    }

    /// Formeltest fuer `tiling_outcome_signature` selbst: gleiche Fuellung
    /// (hier: beide leer) + verschiedener Chip-Rest => verschiedene Signatur.
    /// Zusaetzlich: Chip-REIHENFOLGE darf keine Rolle spielen (Permutation
    /// desselben Bestands => gleiche Signatur), sonst waechst die
    /// Kandidatenzahl in `top_k_tilings` kuenstlich durch reine Vec-Ordnung.
    #[test]
    fn tiling_outcome_signature_distinguishes_chip_remainder() {
        use crate::dome::BonusChip;
        let mut a = tiling_state(7);
        let mut b = tiling_state(7);
        a.players[0].bonus_chips = vec![BonusChip { chip_id: 0, colors: vec![Rot] }];
        b.players[0].bonus_chips = vec![
            BonusChip { chip_id: 0, colors: vec![Rot] },
            BonusChip { chip_id: 1, colors: vec![Blau] },
        ];
        let sig_a = tiling_outcome_signature(&a, 0);
        let sig_b = tiling_outcome_signature(&b, 0);
        assert_eq!(sig_a.0, sig_b.0, "Fuellung sollte identisch sein (beide leer)");
        assert_ne!(sig_a.1, sig_b.1, "unterschiedlicher Chip-Rest muss unterschiedliche Signatur ergeben");
        assert_ne!(sig_a, sig_b);

        // Permutation desselben Bestands => gleiche Signatur.
        let mut c = tiling_state(7);
        c.players[0].bonus_chips = vec![
            BonusChip { chip_id: 1, colors: vec![Blau] },
            BonusChip { chip_id: 0, colors: vec![Rot] },
        ];
        assert_eq!(
            tiling_outcome_signature(&b, 0),
            tiling_outcome_signature(&c, 0),
            "reine Chip-Reihenfolge darf die Signatur nicht aendern"
        );
    }

    /// End-zu-End-Beleg ueber `top_k_tilings`: eine echte Stellung, in der
    /// ZWEI Chip-Allokationen dieselbe fehlende Musterreihe komplettieren
    /// (2 farbgleiche Chips ODER 3 beliebige, siehe `chip_allocations`/
    /// `chips_complete` in round_end.rs), danach folgt exakt EIN Platzierungs-
    /// zug und keine weiteren Schritte. Beide Pfade landen auf demselben
    /// Endbrett (identische Fuellung, identische Rundenpunkte), aber mit
    /// unterschiedlichem Chip-Rest (0 vs. 1 uebrig). Vor dem Fix (Signatur nur
    /// ueber die Fuellung) haette die Dedup-Schleife in `top_k_tilings` einen
    /// der beiden verworfen.
    #[test]
    fn top_k_tilings_keeps_both_outcomes_with_different_chip_remainder() {
        use crate::dome::BonusChip;
        let mut s = tiling_state(7);
        // Slot (1,0) = pool[2] [Tuerkis, Rot, Blau, Wild]; si1 = Rot @ 6x6(2,1)
        // -> Reihe 3 (idx 2). Reihe 4 (idx 3) bleibt leer, damit der Blau-Slot
        // (si2) NICHT platzierbar ist -- exakt ein Platzierungszug moeglich.
        let tile = build_dome_tile_pool()[2].clone();
        s.players[0].dome_grid.place_dome_tile(tile, 1, 0).unwrap();
        s.players[0].pattern_lines[2].add_tiles(&[Rot, Rot]); // cap 3, 1 fehlt
        // 2 rot-tragende Chips (s=2, komplettiert allein) + 1 fachfremder Chip,
        // der nur in der "3-beliebige"-Allokation (s=3) mitgenutzt wird.
        s.players[0].bonus_chips = vec![
            BonusChip { chip_id: 0, colors: vec![Rot] },
            BonusChip { chip_id: 1, colors: vec![Rot] },
            BonusChip { chip_id: 2, colors: vec![Blau] },
        ];

        let outcomes = top_k_tilings(&s, 0, 10);
        assert_eq!(
            outcomes.len(),
            2,
            "erwarte genau 2 ueberlebende Abschluesse (0 bzw. 1 Chip uebrig): {:?}",
            outcomes.iter().map(|o| o.final_state.players[0].bonus_chips.len()).collect::<Vec<_>>()
        );
        let mut remainders: Vec<usize> =
            outcomes.iter().map(|o| o.final_state.players[0].bonus_chips.len()).collect();
        remainders.sort_unstable();
        assert_eq!(remainders, vec![0, 1], "Chip-Reste muessen 0 und 1 sein");
        // Beide Abschluesse haben dieselben Rundenpunkte (identisches Endbrett).
        assert_eq!(outcomes[0].points, outcomes[1].points);
        // Und dieselbe Kuppelfuellung (nur der Chip-Rest unterscheidet sie).
        assert_eq!(
            tiling_outcome_signature(&outcomes[0].final_state, 0).0,
            tiling_outcome_signature(&outcomes[1].final_state, 0).0
        );
    }

    #[test]
    fn unused_player_helper() {
        // broken_penalty/Marker fließen ins Finale ein.
        let mut p = PlayerBoard::new(0, "P");
        p.add_broken(&[Rot, Rot]); // -1 -2 = -3
        p.holds_first_player_marker = true;
        let mut s = tiling_state(7);
        s.players[0] = p;
        // Keine vollen Reihen → 0 Tiling-Punkte; Score 5 (Start) - 3 - 2 = 0.
        assert_eq!(solve_round_final_score(&s, 0), 5 - 3 - 2);
    }
}
