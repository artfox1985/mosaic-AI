//! Spielsteuerung (Orchestrierung) — Port von engine/game.py.
//!
//! Schritt 5: Tiling-Phase (Aktionen, Validierung, Ausführung, Scoring),
//! Rundenende-Strafen und Rundenwechsel. Die scoring-tile-Endwertung
//! (engine/scoring.py) folgt als eigenes Modul in Schritt 6.

use rand::Rng;

use crate::execution::execute_move;
use crate::moves::{
    Action, DrawFromStackMove, PendingDomeChoice, PlaceDomeTileMove, TakeBonusChipMove,
};
use crate::round_end::{
    apply_bonus_chips_to_row, execute_full_tiling, generate_tiling_actions,
    process_unplaceable_rows, score_penalty, validate_tiling_action, TilingAction,
};
use crate::scoring::{calculate_end_scoring, EndScoring};
use crate::state::{setup_new_game, setup_new_round, GameState, Phase, NUM_PLAYERS, NUM_ROUNDS};
use crate::validation::{generate_valid_moves, validate_move, validate_moon_take};

/// Zug der Tiling-Phase — Port der dict-Move-Typen aus engine/game.py.apply().
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TilingMove {
    /// Einen Stein aus einer vollen Musterreihe auf die Kuppel legen.
    Place(TilingAction),
    /// Eine Reihe mit Bonusplättchen komplettieren (`use_chips`).
    UseChips { player: usize, pattern_row: usize },
    /// Tiling für einen Spieler beenden (`end_tiling`).
    EndTiling { player: usize },
}

// ── Dome-Zug ────────────────────────────────────────────────────────────────

pub fn validate_dome_move(state: &GameState, m: &PlaceDomeTileMove) -> Option<String> {
    let player = &state.players[state.current_player];
    if !player.can_place_dome_tile(state.round_number) {
        if state.round_number >= 5 {
            return Some("In Runde 5 werden keine Kuppeln mehr gelegt.".into());
        }
        if player.dome_tiles_placed_this_round >= 2 {
            return Some(format!("{} hat bereits 2 Kuppeln diese Runde gelegt.", player.name));
        }
        return Some("Das 3×3-Raster ist bereits voll.".into());
    }
    if player.has_unplaced_start_tile() {
        return Some("Die Startkuppel muss als erstes (in der Startphase) gelegt werden.".into());
    }
    if !state.dome_display.iter().any(|t| t.tile_id == m.dome_tile_id) {
        return Some(format!("Kuppel {} liegt nicht in der offenen Ablage.", m.dome_tile_id));
    }
    if m.slot_row > 2 || m.slot_col > 2 {
        return Some(format!("Ungültiger Slot ({},{}).", m.slot_row, m.slot_col));
    }
    if state.players[state.current_player].dome_grid.dome_slots[m.slot_row][m.slot_col].is_some() {
        return Some(format!("Slot ({},{}) ist bereits belegt.", m.slot_row, m.slot_col));
    }
    None
}

pub fn execute_dome_move(state: &mut GameState, m: &PlaceDomeTileMove) -> Result<(), String> {
    let idx = state
        .dome_display
        .iter()
        .position(|t| t.tile_id == m.dome_tile_id)
        .ok_or("Kuppel nicht im Display")?;
    let mut tile = state.dome_display.remove(idx);
    tile.apply_rotation(m.rotation)?;
    let pi = state.current_player;
    state.players[pi]
        .dome_grid
        .place_dome_tile(tile, m.slot_row, m.slot_col)?;
    state.players[pi].register_dome_placement()?;
    state.players[pi].use_player_token(state.round_number)?;
    let (name, tokens) = {
        let p = &state.players[pi];
        (p.name.clone(), p.player_tokens_used)
    };
    state.log_event(format!(
        "{name}: Kachel {} → Slot ({},{}) rot={}° [Plättchen {tokens}/2]",
        m.dome_tile_id, m.slot_row, m.slot_col, m.rotation
    ));
    Ok(())
}

/// Rotationen, die für diese (Kachel, Slot)-Kombination tatsächlich legal
/// sind (`validate_dome_move` selbst prüft `rotation` nicht -- die einzige
/// Fehlerquelle wäre `DomeTile::apply_rotation` auf einer bereits befüllten
/// Kachel, was für eine frisch gezogene, unplatzierte Kachel nie zutrifft --
/// daher aktuell immer alle 4, aber als echter Filter geschrieben statt
/// hartkodiert, falls künftige Regeln Rotation doch einschränken).
fn dome_slot_rotation_candidates(
    state: &GameState,
    dome_tile_id: usize,
    slot_row: usize,
    slot_col: usize,
) -> Vec<u32> {
    [0u32, 90, 180, 270]
        .into_iter()
        .filter(|&rotation| {
            let m = PlaceDomeTileMove { dome_tile_id, slot_row, slot_col, rotation };
            validate_dome_move(state, &m).is_none()
        })
        .collect()
}

/// Baustein B Stufe 1: eine Kachel aus dem offenen Display + Slot wählen.
/// Ein Kandidat je (Kachel, Slot)-Paar, das mindestens eine legale Rotation
/// hat (verhindert Sackgassen in Stufe 2) -- `rotation` im zurückgegebenen
/// Move ist Platzhalter (siehe `Action::ChooseDomeSlot`).
pub fn generate_dome_moves(state: &GameState) -> Vec<PlaceDomeTileMove> {
    let player = &state.players[state.current_player];
    if !player.can_place_dome_tile(state.round_number) || player.has_unplaced_start_tile() {
        return Vec::new();
    }
    let empty_slots = player.dome_grid.empty_slots();
    let mut moves = Vec::new();
    for tile in &state.dome_display {
        for &(sr, sc) in &empty_slots {
            if !dome_slot_rotation_candidates(state, tile.tile_id, sr, sc).is_empty() {
                moves.push(PlaceDomeTileMove {
                    dome_tile_id: tile.tile_id,
                    slot_row: sr,
                    slot_col: sc,
                    rotation: 0,
                });
            }
        }
    }
    moves
}

// ── Stapel-Zug (Aktion A) ─────────────────────────────────────────────────────
//
// Zwei Schritte, wie im Regelwerk: (1) `DrawStackPeek` -- eine weitere
// verdeckte Platte ziehen (−1 Pkt), Rückseite zeigt nur den TYP (Wild/
// Special, siehe DomeTile::is_special_type), nicht die Farbanordnung. Beendet
// den Zug NICHT, beliebig oft wiederholbar. (2) `DrawStack` -- aufhören,
// eine der bisher gezogenen Platten (state.pending_stack_draw) wählen und
// platzieren, Rest zurück unter den Stapel. Solange ein Zieh-Vorgang läuft
// (pending_stack_draw nicht leer), sind KEINE anderen Drafting-Aktionen
// erlaubt (siehe drafting_actions) -- Aktion A ist ein durchgängiger Zug.

/// Schritt 1: darf gerade (noch) verdeckt gezogen werden?
pub fn validate_draw_stack_peek(state: &GameState) -> Option<String> {
    let player = &state.players[state.current_player];
    if state.round_number >= 5 {
        return Some("In Runde 5 werden keine Kuppelplatten mehr gelegt.".into());
    }
    // Token-/Platz-Check nur vor dem ERSTEN Zug eines Vorgangs -- danach ist
    // der Vorgang schon "im Gange" und muss zu Ende geführt werden (Slots
    // können sich währenddessen nicht ändern, da keine andere Aktion erlaubt ist).
    if state.pending_stack_draw.is_empty() {
        if player.has_used_all_tokens(state.round_number) {
            return Some(format!("{} hat bereits beide Spielerplättchen genutzt.", player.name));
        }
        if !player.can_place_dome_tile(state.round_number) {
            return Some("Das 3×3-Raster ist bereits voll.".into());
        }
    }
    // Regelbuch: Weiterziehen darf beliebig oft wiederholt werden (je Ziehung
    // -1 Pkt, Score klemmt bei 0 -- apply_score floort). Bei 0 Punkten ist
    // Weiterziehen also effektiv gratis, bis der Stapel leer ist. Die frühere
    // Hausregel "nur so viele Ziehungen wie Punkte" wurde per Nutzer-
    // Entscheidung (Vollaudit 2026-07-21) entfernt. `score_unclamped` wird
    // durch apply_score(-1) weiterhin ehrlich belastet -- das Trainingslabel
    // sieht die echten Kosten.
    if state.dome_tile_pool.is_empty() {
        return Some("Kein Stapel mehr vorhanden.".into());
    }
    None
}

pub fn execute_draw_stack_peek(state: &mut GameState) -> Result<(), String> {
    if let Some(e) = validate_draw_stack_peek(state) {
        return Err(e);
    }
    let pi = state.current_player;
    state.players[pi].apply_score(-1);
    let tile = state.dome_tile_pool.remove(0);
    let typ = if tile.is_special_type() { "Special" } else { "Wild" };
    state.pending_stack_draw.push(tile);
    let (name, score, n) = {
        let p = &state.players[pi];
        (p.name.clone(), p.score, state.pending_stack_draw.len())
    };
    state.log_event(format!(
        "📦 {name}: {n}. Kachel vom Stapel gezogen (Rückseite: {typ}) −1 Pkt → {score} Gesamt"
    ));
    Ok(())
}

/// Schritt 2: eine der gezogenen Platten wählen und platzieren.
pub fn validate_draw_from_stack(state: &GameState, m: &DrawFromStackMove) -> Option<String> {
    if state.pending_stack_draw.is_empty() {
        return Some("Kein laufender Stapel-Zug -- zuerst ziehen.".into());
    }
    if !state.pending_stack_draw.iter().any(|t| t.tile_id == m.chosen_id) {
        return Some(format!("Kachel {} nicht unter den gezogenen.", m.chosen_id));
    }
    let player = &state.players[state.current_player];
    if player.dome_grid.dome_slots[m.slot_row][m.slot_col].is_some() {
        return Some(format!("Slot ({},{}) ist bereits belegt.", m.slot_row, m.slot_col));
    }
    // return_order muss exakt die tile_ids der NICHT gewählten gezogenen
    // Platten als Multiset treffen (wie moon_order bei Sonnenzügen).
    let mut expected: Vec<usize> = state
        .pending_stack_draw
        .iter()
        .filter(|t| t.tile_id != m.chosen_id)
        .map(|t| t.tile_id)
        .collect();
    let mut got = m.return_order.clone();
    expected.sort_unstable();
    got.sort_unstable();
    if got != expected {
        return Some("return_order stimmt nicht mit den übrigen gezogenen Platten überein.".into());
    }
    None
}

pub fn execute_draw_from_stack(state: &mut GameState, m: &DrawFromStackMove) -> Result<(), String> {
    let pi = state.current_player;
    let drawn = std::mem::take(&mut state.pending_stack_draw);
    let mut chosen = None;
    let mut rest: std::collections::HashMap<usize, crate::dome::DomeTile> = std::collections::HashMap::new();
    for t in drawn {
        if t.tile_id == m.chosen_id && chosen.is_none() {
            chosen = Some(t);
        } else {
            rest.insert(t.tile_id, t);
        }
    }
    // Rest in der vom Spieler gewählten Reihenfolge zurück unter den Stapel
    // (Regelwerk: "in beliebiger Reihenfolge zurücklegen", siehe DrawFromStackMove).
    for id in &m.return_order {
        if let Some(t) = rest.remove(id) {
            state.dome_tile_pool.push(t);
        }
    }
    let mut chosen = chosen.ok_or("gewählte Kachel nicht gezogen")?;
    chosen.apply_rotation(m.rotation)?;
    state.players[pi]
        .dome_grid
        .place_dome_tile(chosen, m.slot_row, m.slot_col)?;
    state.players[pi].register_dome_placement()?;
    state.players[pi].use_player_token(state.round_number)?;
    let (name, tokens) = {
        let p = &state.players[pi];
        (p.name.clone(), p.player_tokens_used)
    };
    state.log_event(format!(
        "{name}: Kachel {} → Slot ({},{}) rot={}° [Plättchen {tokens}/2]",
        m.chosen_id, m.slot_row, m.slot_col, m.rotation
    ));
    Ok(())
}

// ── Bonus-Chip (Aktion D) ─────────────────────────────────────────────────────

pub fn validate_take_bonus_chip(state: &GameState, m: &TakeBonusChipMove) -> Option<String> {
    let player = &state.players[state.current_player];
    if !player.can_take_bonus_chip() {
        return Some(format!("{} hat bereits 2 Bonusplättchen diese Runde genommen.", player.name));
    }
    match state.factories.iter().find(|f| f.factory_id == m.factory_id) {
        None => Some(format!("Fabrik {} nicht gefunden.", m.factory_id)),
        Some(f) if !f.bonus_chip_revealed || f.bonus_chip.is_none() => {
            Some(format!("Kein aufgedecktes Bonusplättchen auf Fabrik {}.", m.factory_id))
        }
        Some(_) => None,
    }
}

pub fn execute_take_bonus_chip(state: &mut GameState, m: &TakeBonusChipMove) -> Result<(), String> {
    let fidx = state
        .factories
        .iter()
        .position(|f| f.factory_id == m.factory_id)
        .ok_or("Fabrik nicht gefunden")?;
    let chip = state.factories[fidx].bonus_chip.take().ok_or("kein Chip")?;
    state.factories[fidx].bonus_chip_revealed = false;
    let pi = state.current_player;
    state.players[pi].take_bonus_chip(chip)?;
    let (name, used) = {
        let p = &state.players[pi];
        (p.name.clone(), p.bonus_chips_used_this_round)
    };
    state.log_event(format!(
        "{name}: Bonusplättchen von Fabrik {} genommen [{used}/2 diese Runde]",
        m.factory_id
    ));
    Ok(())
}

/// Darf gerade eine weitere verdeckte Platte gezogen werden (Aktion A,
/// Schritt 1)? Reine Verfügbarkeits-Frage, `Action::DrawStackPeek` hat keine
/// Felder.
pub fn can_draw_stack_peek(state: &GameState) -> bool {
    validate_draw_stack_peek(state).is_none()
}

/// Rotationen, die für diese (gewählte Stapel-Kachel, Slot)-Kombination
/// tatsächlich legal sind -- siehe `dome_slot_rotation_candidates`-Kommentar,
/// gleiche Begründung (aktuell immer alle 4, echter Filter für Zukunftssicherheit).
fn draw_stack_slot_rotation_candidates(
    state: &GameState,
    chosen_id: usize,
    slot_row: usize,
    slot_col: usize,
    return_order: &[usize],
) -> Vec<u32> {
    [0u32, 90, 180, 270]
        .into_iter()
        .filter(|&rotation| {
            let m = DrawFromStackMove {
                chosen_id,
                slot_row,
                slot_col,
                rotation,
                return_order: return_order.to_vec(),
            };
            validate_draw_from_stack(state, &m).is_none()
        })
        .collect()
}

/// Wahl-Züge (Aktion A, Schritt 2, Baustein B Stufe 1): je bereits gezogener
/// Kachel (in `pending_stack_draw`) × freiem Slot, gefiltert auf ≥1 legale
/// Rotation (verhindert Sackgassen in Stufe 2). Leer, solange kein
/// Zieh-Vorgang läuft. `chosen_id` fließt NICHT in die Policy-ID ein (wie
/// `moon_order` bei Sonnenzügen) -- `rotation` im zurückgegebenen Move ist
/// Platzhalter (siehe `Action::ChooseDrawStackSlot`).
pub fn generate_draw_stack_moves(state: &GameState) -> Vec<DrawFromStackMove> {
    if state.pending_stack_draw.is_empty() {
        return Vec::new();
    }
    let player = &state.players[state.current_player];
    let mut ids: Vec<usize> = state.pending_stack_draw.iter().map(|t| t.tile_id).collect();
    ids.sort_unstable();
    ids.dedup();
    let mut moves = Vec::new();
    for chosen_id in ids {
        // return_order wird -- wie moon_order bei Sonnenzuegen -- NICHT
        // kombinatorisch aufgefaechert (keine eigene Policy-Dimension,
        // s. DrawFromStackMove-Kommentar): ein Kandidat je (chosen_id, Slot),
        // Reihenfolge der uebrigen Platten kanonisch = die Ziehreihenfolge
        // aus `pending_stack_draw`.
        let return_order: Vec<usize> = state
            .pending_stack_draw
            .iter()
            .filter(|t| t.tile_id != chosen_id)
            .map(|t| t.tile_id)
            .collect();
        for (sr, sc) in player.dome_grid.empty_slots() {
            if !draw_stack_slot_rotation_candidates(state, chosen_id, sr, sc, &return_order).is_empty() {
                moves.push(DrawFromStackMove {
                    chosen_id,
                    slot_row: sr,
                    slot_col: sc,
                    rotation: 0,
                    return_order: return_order.clone(),
                });
            }
        }
    }
    moves
}

pub fn generate_bonus_chip_moves(state: &GameState) -> Vec<TakeBonusChipMove> {
    let player = &state.players[state.current_player];
    if !player.can_take_bonus_chip() {
        return Vec::new();
    }
    state
        .factories
        .iter()
        .filter(|f| f.bonus_chip_revealed && f.bonus_chip.is_some())
        .map(|f| TakeBonusChipMove { factory_id: f.factory_id })
        .collect()
}

// ── Drafting-Abschluss ────────────────────────────────────────────────────────

/// Kann der aktive Spieler (so wie state.current_player gesetzt ist) noch ziehen?
fn current_player_can_move(state: &GameState) -> bool {
    // Baustein B: eine offene Rotation-Wahl (Stufe 2) MUSS abgeschlossen
    // werden -- das zaehlt immer als "kann noch ziehen".
    if state.pending_dome_choice.is_some() {
        return true;
    }
    can_draw_stack_peek(state)
        || !generate_draw_stack_moves(state).is_empty()
        || !generate_valid_moves(state).is_empty()
        || !generate_dome_moves(state).is_empty()
        || !generate_bonus_chip_moves(state).is_empty()
}

/// Schreibt den kompletten Event-Log plus Diagnose-Kopf nach
/// `static/log/CRASH_dome_deadlock_<unix_ts>.log` und bricht den Prozess ab.
/// Wird nur aufgerufen, wenn die Invariante "beide Spieler nutzen pro Runde
/// (ausser Runde 5) exakt 2 Kuppel-Tokens" verletzt wird -- siehe
/// `check_drafting_complete`. Das darf laut Spielregel nie vorkommen; ein
/// stiller Rundenabschluss würde Trainingsdaten/Self-Play mit einem
/// regelwidrigen Zustand verseuchen, deshalb harter Abbruch statt Fallback.
fn panic_on_dome_deadlock(state: &GameState) -> ! {
    use std::time::{SystemTime, UNIX_EPOCH};
    let ts = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    let dir = std::path::Path::new("static/log");
    let _ = std::fs::create_dir_all(dir);
    let path = dir.join(format!("CRASH_dome_deadlock_{ts}.log"));

    let mut body = String::new();
    body.push_str("# MOSAIC CRASH DUMP: Kuppel-Deadlock (Invariante verletzt)\n");
    body.push_str(&format!(
        "# Runde {}: kein Spieler kann mehr handeln, obwohl nicht beide Spieler ihre \
         2 Kuppel-Tokens verbraucht haben (ausserhalb Runde 5 sollte das nie passieren).\n",
        state.round_number
    ));
    for (i, p) in state.players.iter().enumerate() {
        body.push_str(&format!(
            "# Spieler {i} ({}): tokens_used={}, dome_tiles_placed_this_round={}, freie Slots={}\n",
            p.name,
            p.player_tokens_used,
            p.dome_tiles_placed_this_round,
            p.dome_grid.empty_slots().len()
        ));
    }
    body.push_str(&format!(
        "# Display: {} Kacheln, Stapel: {} Kacheln\n",
        state.dome_display.len(),
        state.dome_tile_pool.len()
    ));
    body.push_str("# ============================================================\n");
    body.push_str(&state.log.join("\n"));
    body.push('\n');
    let _ = std::fs::write(&path, &body);

    panic!(
        "Kuppel-Deadlock in Runde {}: kein Spieler kann mehr ziehen, obwohl noch Kuppel-Tokens \
         offen sind (ausser Runde 5 darf das nie passieren). Log gespeichert unter: {}",
        state.round_number,
        path.display()
    );
}

/// Port von round_end.check_drafting_complete. Braucht &mut, um current_player
/// temporär für die Pro-Spieler-Prüfung zu setzen (danach wiederhergestellt).
pub fn check_drafting_complete(state: &mut GameState) -> bool {
    let chips_available = state
        .factories
        .iter()
        .any(|f| f.bonus_chip.is_some() && f.bonus_chip_revealed);
    if chips_available {
        return false;
    }
    let factories_empty = state
        .factories
        .iter()
        .all(|f| f.is_fully_empty() && (f.bonus_chip.is_none() || f.bonus_chip_revealed))
        && state.large_factory.is_empty();
    if !factories_empty {
        return false;
    }
    if state.round_number >= 5 {
        return true;
    }
    let tokens_done = state
        .players
        .iter()
        .all(|p| p.has_used_all_tokens(state.round_number));
    if tokens_done {
        return true;
    }
    // Kann noch irgendein Spieler etwas tun?
    let orig = state.current_player;
    let mut anyone = false;
    for pi in 0..NUM_PLAYERS {
        state.current_player = pi;
        if current_player_can_move(state) {
            anyone = true;
            break;
        }
    }
    state.current_player = orig;
    if !anyone {
        panic_on_dome_deadlock(state);
    }
    false
}

// ── Startkuppel-Platzierung ───────────────────────────────────────────────────

pub fn apply_start_placement(
    state: &mut GameState,
    player_idx: usize,
    tile_id: usize,
    row: usize,
    col: usize,
    rot: u32,
) -> Result<(), String> {
    let first_player = state.current_player;
    let non_starter = 1 - first_player;
    if player_idx == first_player && state.players[non_starter].start_tile_pending {
        return Err("Nicht-Startspieler muss zuerst eine Kuppelplatte wählen.".into());
    }
    if !state.players[player_idx].start_tile_pending {
        return Err(format!("Spieler {player_idx} hat keine ausstehende Startkachel."));
    }
    if state.players[player_idx].dome_grid.dome_slots[row][col].is_some() {
        return Err(format!("Slot ({row},{col}) ist nicht frei."));
    }
    let idx = state
        .dome_display
        .iter()
        .position(|t| t.tile_id == tile_id)
        .ok_or_else(|| format!("Kachel {tile_id} nicht im Display."))?;
    let mut tile = state.dome_display.remove(idx);
    if !state.dome_tile_pool.is_empty() {
        // Nachziehen an dieselbe Display-Position, damit übrige Karten ihren Platz behalten.
        let refill = state.dome_tile_pool.remove(0);
        state.dome_display.insert(idx, refill);
    }
    tile.apply_rotation(rot)?;
    state.players[player_idx]
        .dome_grid
        .place_dome_tile(tile, row, col)?;
    state.players[player_idx].start_tile_pending = false;
    let name = state.players[player_idx].name.clone();
    state.log_event(format!("{name}: Startkachel {tile_id} → ({row},{col}) rot={rot}°"));
    Ok(())
}

// ── Sieger ────────────────────────────────────────────────────────────────────

pub fn determine_winner(state: &GameState) -> usize {
    let s0 = state.players[0].score;
    let s1 = state.players[1].score;
    if s0 > s1 {
        0
    } else if s1 > s0 {
        1
    } else {
        // Gleichstand: es gewinnt, wer die Startspielerfliese hält. ACHTUNG:
        // `holds_first_player_marker` taugt hier NICHT -- `score_penalty`
        // (round_end.rs) löscht das Flag bei JEDER Rundenwertung (auch
        // Runde 5), es ist zum Zeitpunkt der Siegerermittlung also immer
        // false. `first_player_next_round` wird bei der Marker-Nahme gesetzt
        // (execution.rs::apply_first_player_marker) und überlebt die Wertung.
        state.first_player_next_round
    }
}

// ── Game-Loop ─────────────────────────────────────────────────────────────────

/// Alle gültigen Drafting-Aktionen für den aktiven Spieler eines Zustands.
/// Leer → [Pass]. Single Source of Truth für Game-Loop und MCTS.
pub fn drafting_actions(state: &GameState) -> Vec<Action> {
    let mut actions: Vec<Action> = Vec::new();

    // Baustein B Stufe 2: eine Kuppel-Slot-Wahl ist bereits getroffen, nur
    // noch die Rotation fehlt -- NICHTS anderes ist erlaubt (gilt für BEIDE
    // Pfade gleich, geprüft VOR dem pending_stack_draw-Check, da bei der
    // Stapel-Variante beide Felder gleichzeitig gesetzt sein können).
    if let Some(choice) = &state.pending_dome_choice {
        let rotations = match choice {
            PendingDomeChoice::FromDisplay { dome_tile_id, slot_row, slot_col } => {
                dome_slot_rotation_candidates(state, *dome_tile_id, *slot_row, *slot_col)
            }
            PendingDomeChoice::FromDrawStack { chosen_id, slot_row, slot_col, return_order } => {
                draw_stack_slot_rotation_candidates(state, *chosen_id, *slot_row, *slot_col, return_order)
            }
        };
        for rot in rotations {
            actions.push(Action::ChooseDomeRotation(rot));
        }
        // Sollte laut Stufe-1-Sackgassen-Check nie leer sein -- Pass nur als
        // letzte Absicherung, kein regulärer Spielzustand.
        if actions.is_empty() {
            actions.push(Action::Pass);
        }
        return actions;
    }

    // Mitten in einem Stapel-Zug (Aktion A): NUR weiterziehen oder wählen
    // erlaubt, keine andere Aktion -- das Regelwerk behandelt Aktion A als
    // EINEN durchgängigen Zug, der nicht mit anderen Aktionen verschachtelt
    // werden darf.
    if !state.pending_stack_draw.is_empty() {
        if can_draw_stack_peek(state) {
            actions.push(Action::DrawStackPeek);
        }
        for m in generate_draw_stack_moves(state) {
            actions.push(Action::ChooseDrawStackSlot(m));
        }
        if actions.is_empty() {
            actions.push(Action::Pass);
        }
        return actions;
    }
    for m in generate_valid_moves(state) {
        actions.push(Action::Stone(m));
    }
    for m in generate_dome_moves(state) {
        actions.push(Action::ChooseDomeSlot(m));
    }
    for m in generate_bonus_chip_moves(state) {
        actions.push(Action::BonusChip(m));
    }
    if can_draw_stack_peek(state) {
        actions.push(Action::DrawStackPeek);
    }
    if actions.is_empty() {
        actions.push(Action::Pass);
    }
    actions
}

pub struct Game {
    pub state: GameState,
}

impl Game {
    pub fn start<R: Rng + ?Sized>(
        player_names: [String; NUM_PLAYERS],
        first_player: usize,
        scoring_tile_ids: Vec<usize>,
        rng: &mut R,
    ) -> Self {
        let mut state = setup_new_game(player_names, first_player, rng);
        state.scoring_tile_ids = scoring_tile_ids;
        state.current_player = first_player;
        Game { state }
    }

    pub fn is_over(&self) -> bool {
        self.state.round_number >= NUM_ROUNDS
    }

    /// Wendet einen Drafting-Zug an (Stein/Kuppel/Stapel/Chip/Pass), wechselt den
    /// Spieler und prüft den Phasenübergang. Tiling-Züge folgen in Schritt 5.
    pub fn apply_drafting(&mut self, action: &Action) -> Result<(), String> {
        if self.state.phase != Phase::Drafting {
            return Err(format!("Zug in Phase '{}' nicht erlaubt.", self.state.phase.as_str()));
        }
        // Defensive: solange die Startkuppel-Platzierung (vor Runde 1) noch
        // aussteht, ist KEINE Drafting-Aktion erlaubt -- der Harness ruft
        // korrekt erst apply_start_placement auf, aber direkte Aufrufer
        // (z.B. Suche/Server) sollen hier hart abprallen.
        if self.state.players.iter().any(|p| p.start_tile_pending) {
            return Err("Startkuppel-Platzierung noch ausstehend -- keine Drafting-Aktion erlaubt.".into());
        }
        match action {
            Action::Stone(m) => {
                let err = if m.is_global_moon_take() {
                    validate_moon_take(&self.state, m)
                } else {
                    validate_move(&self.state, m)
                };
                if let Some(e) = err {
                    return Err(e);
                }
                execute_move(&mut self.state, m);
                self.state.switch_player();
            }
            Action::ChooseDomeSlot(m) => {
                if let Some(e) = validate_dome_move(&self.state, m) {
                    return Err(e);
                }
                self.state.pending_dome_choice = Some(PendingDomeChoice::FromDisplay {
                    dome_tile_id: m.dome_tile_id,
                    slot_row: m.slot_row,
                    slot_col: m.slot_col,
                });
                // Beendet den Zug NICHT -- Stufe 2 (Rotation) folgt direkt,
                // derselbe Spieler ist weiter am Zug.
            }
            Action::DrawStackPeek => {
                execute_draw_stack_peek(&mut self.state)?;
                // Beendet den Zug NICHT -- derselbe Spieler entscheidet als
                // naechstes erneut (weiterziehen oder waehlen).
            }
            Action::ChooseDrawStackSlot(m) => {
                if let Some(e) = validate_draw_from_stack(&self.state, m) {
                    return Err(e);
                }
                self.state.pending_dome_choice = Some(PendingDomeChoice::FromDrawStack {
                    chosen_id: m.chosen_id,
                    slot_row: m.slot_row,
                    slot_col: m.slot_col,
                    return_order: m.return_order.clone(),
                });
                // Beendet den Zug NICHT -- Stufe 2 (Rotation) folgt direkt.
            }
            Action::ChooseDomeRotation(rot) => {
                let choice = match &self.state.pending_dome_choice {
                    Some(c) => c.clone(),
                    None => return Err("Keine offene Kuppel-Wahl fuer Rotation.".into()),
                };
                match choice {
                    PendingDomeChoice::FromDisplay { dome_tile_id, slot_row, slot_col } => {
                        let m = PlaceDomeTileMove { dome_tile_id, slot_row, slot_col, rotation: *rot };
                        if let Some(e) = validate_dome_move(&self.state, &m) {
                            return Err(e);
                        }
                        execute_dome_move(&mut self.state, &m)?;
                    }
                    PendingDomeChoice::FromDrawStack { chosen_id, slot_row, slot_col, return_order } => {
                        let m = DrawFromStackMove { chosen_id, slot_row, slot_col, rotation: *rot, return_order };
                        if let Some(e) = validate_draw_from_stack(&self.state, &m) {
                            return Err(e);
                        }
                        execute_draw_from_stack(&mut self.state, &m)?;
                    }
                }
                self.state.pending_dome_choice = None;
                self.state.switch_player();
            }
            Action::BonusChip(m) => {
                if let Some(e) = validate_take_bonus_chip(&self.state, m) {
                    return Err(e);
                }
                execute_take_bonus_chip(&mut self.state, m)?;
                self.state.switch_player();
            }
            Action::Pass => {
                self.state.switch_player();
            }
        }
        self.check_phase_transition();
        Ok(())
    }

    /// Alle gültigen Drafting-Aktionen des aktiven Spielers (ohne Stapel-Zug,
    /// dessen Auswahl agentenseitig erfolgt). Leer → [Pass].
    pub fn valid_drafting_actions(&self) -> Vec<Action> {
        drafting_actions(&self.state)
    }

    fn check_phase_transition(&mut self) {
        if self.state.phase == Phase::Drafting && check_drafting_complete(&mut self.state) {
            self.state.phase = Phase::Tiling;
            self.state.tiling_done = [false, false];
            for p in self.state.players.iter_mut() {
                p.tiled_max_row = -1;
            }
            self.state.log_event("Tiling-Phase beginnt.");
            // Unplatzierbare Reihen → Strafleiste (für beide Spieler).
            for pi in 0..NUM_PLAYERS {
                let moved = {
                    let (players, tower) = (&mut self.state.players, &mut self.state.tower);
                    process_unplaceable_rows(&mut players[pi], tower)
                };
                for (row_idx, color, n) in moved {
                    let name = self.state.players[pi].name.clone();
                    self.state.log_event(format!(
                        "⚠️  {name}: Musterreihe {} ({}) nicht platzierbar → {n}× Strafleiste",
                        row_idx + 1,
                        color.value()
                    ));
                }
            }
        }
    }

    // ── Tiling-Phase ──────────────────────────────────────────────────────────

    /// Alle gültigen Tiling-Aktionen des Spielers (leer → Spieler kann `EndTiling`).
    pub fn valid_tiling_actions(&self, player_idx: usize) -> Vec<TilingAction> {
        generate_tiling_actions(&self.state, player_idx)
    }

    /// Führt eine einzelne, validierte Tiling-Aktion aus und gibt die Punkte zurück.
    pub fn apply_single_tiling(
        &mut self,
        player_idx: usize,
        action: &TilingAction,
    ) -> Result<i32, String> {
        if let Some(e) = validate_tiling_action(&self.state, player_idx, action) {
            return Err(e);
        }
        execute_full_tiling(&mut self.state, player_idx, action)
    }

    /// Wendet einen Tiling-Phasen-Zug an (Stein legen / Chips nutzen / beenden).
    /// `EndTiling` kann den Rundenwechsel auslösen und braucht daher den RNG.
    pub fn apply_tiling<R: Rng + ?Sized>(
        &mut self,
        mv: &TilingMove,
        rng: &mut R,
    ) -> Result<(), String> {
        if self.state.phase != Phase::Tiling {
            return Err(format!(
                "Tiling-Zug in Phase '{}' nicht erlaubt.",
                self.state.phase.as_str()
            ));
        }
        match mv {
            TilingMove::Place(action) => {
                let pi = self.state.current_player;
                self.apply_single_tiling(pi, action)?;
                Ok(())
            }
            TilingMove::UseChips { player, pattern_row } => {
                if !apply_bonus_chips_to_row(&mut self.state.players[*player], *pattern_row) {
                    return Err(format!("Reihe {} nicht mit Chips komplettierbar.", pattern_row + 1));
                }
                let name = self.state.players[*player].name.clone();
                self.state.log_event(format!(
                    "🎫 {name} komplettiert Reihe {} vollständig mit Bonus-Chips!",
                    pattern_row + 1
                ));
                Ok(())
            }
            TilingMove::EndTiling { player } => self.end_tiling(*player, rng),
        }
    }

    /// Beendet das Tiling für einen Spieler; wechselt zum anderen oder schließt
    /// die Phase ab (Strafen + Rundenwechsel/Spielende).
    fn end_tiling<R: Rng + ?Sized>(&mut self, player: usize, rng: &mut R) -> Result<(), String> {
        if !self.valid_tiling_actions(player).is_empty() {
            return Err(format!("Noch Tiling-Züge offen für Spieler {player}."));
        }
        self.state.tiling_done[player] = true;
        let other = 1 - player;
        if !self.state.tiling_done[other] {
            self.state.current_player = other;
            return Ok(());
        }
        self.state.tiling_done = [false, false];
        self.execute_end_tiling(rng);
        Ok(())
    }

    /// Rundenende-Abschluss: unplatzierbare Reihen, Strafen, dann Rundenwechsel
    /// oder Spielende. Port von engine/game.py `_execute_end_tiling`.
    fn execute_end_tiling<R: Rng + ?Sized>(&mut self, rng: &mut R) {
        for pi in 0..NUM_PLAYERS {
            let moved = {
                let (players, tower) = (&mut self.state.players, &mut self.state.tower);
                process_unplaceable_rows(&mut players[pi], tower)
            };
            for (row_idx, color, n) in moved {
                let name = self.state.players[pi].name.clone();
                self.state.log_event(format!(
                    "⚠️  {name}: Musterreihe {} ({}) nicht platzierbar → {n}× Strafleiste",
                    row_idx + 1,
                    color.value()
                ));
            }
        }

        for pi in 0..NUM_PLAYERS {
            let pen = score_penalty(&mut self.state.players[pi]);
            let broken = self.state.players[pi].clear_broken();
            self.state.tower.add(&broken);
            if pen < 0 {
                self.state.players[pi].apply_score(pen);
                let (name, score) = {
                    let p = &self.state.players[pi];
                    (p.name.clone(), p.score)
                };
                self.state.log_event(format!("{name}: Strafe {pen} Pkt → {score} Gesamt"));
            }
        }

        if self.is_over() {
            self.state.phase = Phase::End;
            self.state.log_event("Das Spiel ist beendet!");
        } else {
            self.next_round(rng);
        }
    }

    /// Bereitet die nächste Runde vor: Display auf 3 auffüllen, dann setup_new_round.
    fn next_round<R: Rng + ?Sized>(&mut self, rng: &mut R) {
        while self.state.dome_display.len() < 3 && !self.state.dome_tile_pool.is_empty() {
            let t = self.state.dome_tile_pool.remove(0);
            self.state.dome_display.push(t);
        }
        setup_new_round(&mut self.state, rng);
        self.state.phase = Phase::Drafting;
    }

    // ── Endwertung ────────────────────────────────────────────────────────────

    /// Wendet die Wertungsplatten-Endwertung an (nach dem Spielende), schreibt
    /// die Punkte gut und setzt die Phase auf `Final`. Gibt die Detailergebnisse
    /// je Spieler zurück. Port von engine/game.py `_calculate_end_scoring`.
    pub fn apply_end_scoring(&mut self) -> Vec<EndScoring> {
        let ids = self.state.scoring_tile_ids.clone();
        let mut results = Vec::with_capacity(NUM_PLAYERS);
        for pi in 0..NUM_PLAYERS {
            let res = calculate_end_scoring(&self.state.players[pi], &ids);
            self.state.players[pi].apply_score(res.total);
            let (name, score) = {
                let p = &self.state.players[pi];
                (p.name.clone(), p.score)
            };
            self.state
                .log_event(format!("🏆 {name}: Endwertung {} Pkt → Gesamt: {score} Pkt", res.total));
            for d in &res.details {
                self.state
                    .log_event(format!("   {} {}: {} Pkt", d.emoji, d.name, d.score));
            }
            results.push(res);
        }
        self.state.phase = Phase::Final;
        results
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    fn names() -> [String; 2] {
        ["P1".into(), "P2".into()]
    }

    #[test]
    fn stack_peek_at_zero_score_allows_unlimited_draws() {
        // Regelbuch-Variante (Vollaudit 2026-07-21): Weiterziehen darf
        // beliebig oft wiederholt werden, je Ziehung -1 Pkt, Score klemmt
        // bei 0 -- bei 0 Punkten also effektiv gratis, bis der Stapel leer
        // ist. `score_unclamped` sinkt dabei ehrlich weiter.
        let mut rng = StdRng::seed_from_u64(12);
        let mut game = Game::start(names(), 0, vec![0, 1, 2], &mut rng);
        for p in game.state.players.iter_mut() {
            p.start_tile_pending = false;
        }
        game.state.players[game.state.current_player].score = 0;
        let unclamped_before = game.state.players[0].score_unclamped;

        for i in 1..=4 {
            assert!(
                validate_draw_stack_peek(&game.state).is_none(),
                "{i}. Ziehung bei 0 Punkten muss erlaubt sein"
            );
            execute_draw_stack_peek(&mut game.state).expect("Ziehung");
            assert_eq!(game.state.players[0].score, 0, "Punkte duerfen nie unter 0 fallen");
            assert_eq!(
                game.state.players[0].score_unclamped,
                unclamped_before - i,
                "score_unclamped muss die echten Kosten weiter zaehlen"
            );
        }
    }

    #[test]
    fn tie_break_uses_first_player_next_round() {
        // R1 (Vollaudit 2026-07-21): bei Gleichstand gewinnt, wer die
        // Startspielerfliese genommen hat. `holds_first_player_marker` ist
        // nach der Runde-5-Wertung immer false (score_penalty räumt es),
        // daher entscheidet `first_player_next_round`.
        let mut rng = StdRng::seed_from_u64(7);
        let mut game = Game::start(names(), 0, vec![0, 1, 2], &mut rng);
        game.state.players[0].score = 30;
        game.state.players[1].score = 30;
        // score_penalty hat die Flags bereits geräumt (wie nach Runde 5).
        game.state.players[0].holds_first_player_marker = false;
        game.state.players[1].holds_first_player_marker = false;

        game.state.first_player_next_round = 0;
        assert_eq!(determine_winner(&game.state), 0);
        game.state.first_player_next_round = 1;
        assert_eq!(determine_winner(&game.state), 1);
    }

    #[test]
    fn apply_drafting_blocked_while_start_tile_pending() {
        // R5 (Vollaudit 2026-07-21): solange die Startkuppel-Platzierung
        // aussteht, darf apply_drafting KEINE Aktion durchlassen.
        let mut rng = StdRng::seed_from_u64(9);
        let mut game = Game::start(names(), 0, vec![0, 1, 2], &mut rng);
        assert!(game.state.players.iter().any(|p| p.start_tile_pending));
        assert!(game.apply_drafting(&Action::Pass).is_err());
    }

    #[test]
    fn draw_from_stack_returns_rest_in_chosen_order() {
        use crate::dome::build_dome_tile_pool;

        let mut rng = StdRng::seed_from_u64(5);
        let mut game = Game::start(names(), 0, vec![0, 1, 2], &mut rng);
        for p in game.state.players.iter_mut() {
            p.start_tile_pending = false;
        }
        let pool = build_dome_tile_pool();
        game.state.pending_stack_draw = vec![pool[0].clone(), pool[1].clone(), pool[2].clone()];
        game.state.dome_tile_pool.clear();

        let (sr, sc) = game.state.players[game.state.current_player]
            .dome_grid
            .empty_slots()[0];
        // Regelwerk-Zitat des Users: die zwei nicht gewaehlten Platten in
        // "beliebiger Reihenfolge" zurueck -- hier bewusst NICHT die
        // Ziehreihenfolge (waere [pool[1].tile_id, pool[2].tile_id]),
        // sondern umgekehrt.
        let mv = DrawFromStackMove {
            chosen_id: pool[0].tile_id,
            slot_row: sr,
            slot_col: sc,
            rotation: 0,
            return_order: vec![pool[2].tile_id, pool[1].tile_id],
        };
        assert!(validate_draw_from_stack(&game.state, &mv).is_none());
        execute_draw_from_stack(&mut game.state, &mv).expect("gueltiger Zug");

        assert_eq!(
            game.state.dome_tile_pool.iter().map(|t| t.tile_id).collect::<Vec<_>>(),
            vec![pool[2].tile_id, pool[1].tile_id],
            "Restplatten muessen exakt in der gewaehlten Reihenfolge unter dem Stapel liegen"
        );
    }

    #[test]
    fn draw_from_stack_rejects_incomplete_return_order() {
        use crate::dome::build_dome_tile_pool;

        let mut rng = StdRng::seed_from_u64(6);
        let mut game = Game::start(names(), 0, vec![0, 1, 2], &mut rng);
        for p in game.state.players.iter_mut() {
            p.start_tile_pending = false;
        }
        let pool = build_dome_tile_pool();
        game.state.pending_stack_draw = vec![pool[0].clone(), pool[1].clone(), pool[2].clone()];
        game.state.dome_tile_pool.clear();

        let (sr, sc) = game.state.players[game.state.current_player]
            .dome_grid
            .empty_slots()[0];
        // return_order fehlt eine der beiden Restplatten -- muss abgelehnt werden.
        let mv = DrawFromStackMove {
            chosen_id: pool[0].tile_id,
            slot_row: sr,
            slot_col: sc,
            rotation: 0,
            return_order: vec![pool[1].tile_id],
        };
        assert!(validate_draw_from_stack(&game.state, &mv).is_some());
    }

    #[test]
    fn drafting_loop_runs_to_tiling() {
        let mut rng = StdRng::seed_from_u64(123);
        let mut game = Game::start(names(), 0, vec![0, 1, 2], &mut rng);
        // Startkacheln als bereits gelegt markieren (Startphase separat getestet).
        for p in game.state.players.iter_mut() {
            p.start_tile_pending = false;
        }
        let mut steps = 0;
        while game.state.phase == Phase::Drafting && steps < 500 {
            let actions = game.valid_drafting_actions();
            // deterministisch ersten Zug nehmen
            game.apply_drafting(&actions[0]).expect("valider Zug");
            steps += 1;
        }
        assert_eq!(game.state.phase, Phase::Tiling, "Drafting endet in Tiling (steps={steps})");
        assert!(steps < 500, "Drafting terminiert");
    }

    #[test]
    fn unplaceable_row_logs_row_and_color_at_tiling_start() {
        use crate::dome::build_dome_tile_pool;
        use crate::tile::TileColor::Rot;

        let mut rng = StdRng::seed_from_u64(9);
        let mut game = Game::start(names(), 0, vec![0, 1, 2], &mut rng);
        for p in game.state.players.iter_mut() {
            p.start_tile_pending = false;
        }

        // Musterreihe 0 (Kapazität 1) mit Rot voll, Dome-Reihe 0 komplett mit
        // Platten ohne offenen Rot-/Wild-Space belegt -- exakt das Fixture aus
        // round_end::tests::unplaceable_when_domerow_full_no_match.
        let p0 = &mut game.state.players[0];
        p0.pattern_lines[0].add_tiles(&[Rot]);
        let pool = build_dome_tile_pool();
        for sc in 0..3 {
            let mut t = pool[11].clone(); // [Tuerkis, Schwarz, Rot, Wild]
            t.tile_id = 200 + sc;
            p0.dome_grid.place_dome_tile(t, 0, sc).unwrap();
        }

        // Alles leeren, was check_drafting_complete() sonst noch als
        // "es gibt noch einen Zug" werten wuerde (Fabriken, Kuppel-Stapel,
        // Kuppel-Display, Startspieler-Marker auf der grossen Fabrik).
        for f in game.state.factories.iter_mut() {
            f.sun_tiles.clear();
            f.moon_stacks.clear();
            // Wie beim echten Leerwerden: Bonusplaettchen gilt als bereits
            // aufgedeckt/genommen, sonst haengt check_drafting_complete() an
            // "chips_available"/"factories_empty" fest.
            f.bonus_chip_revealed = true;
            f.bonus_chip = None;
        }
        game.state.large_factory.sun_tiles.clear();
        game.state.large_factory.moon_pool.clear();
        game.state.large_factory.has_first_player_marker = false;
        game.state.dome_tile_pool.clear();
        game.state.dome_display.clear();
        // Fixture simuliert "beide Spieler haben ihre 2 Kuppel-Tokens diese
        // Runde schon anderweitig verbraucht" -- sonst wuerde
        // check_drafting_complete() jetzt (korrekt) einen Kuppel-Deadlock
        // erkennen und abbrechen, statt die Runde zu beenden.
        for p in game.state.players.iter_mut() {
            p.player_tokens_used = 2;
            p.dome_tiles_placed_this_round = 2;
        }

        game.check_phase_transition();

        assert_eq!(game.state.phase, Phase::Tiling);
        assert!(
            game.state.log.iter().any(|l| l.contains("Musterreihe 1 (rot) nicht platzierbar")),
            "Log fehlt Reihe+Farbe-Hinweis: {:?}",
            game.state.log
        );
        assert!(game.state.players[0].pattern_lines[0].tiles.is_empty());
    }

    #[test]
    fn full_round_drafting_through_tiling_to_next_round() {
        let mut rng = StdRng::seed_from_u64(2024);
        let mut game = Game::start(names(), 0, vec![0, 1, 2], &mut rng);
        for p in game.state.players.iter_mut() {
            p.start_tile_pending = false;
        }

        // Drafting bis Tiling.
        let mut steps = 0;
        while game.state.phase == Phase::Drafting && steps < 500 {
            let actions = game.valid_drafting_actions();
            game.apply_drafting(&actions[0]).expect("valider Drafting-Zug");
            steps += 1;
        }
        assert_eq!(game.state.phase, Phase::Tiling);

        // Tiling: jeder Spieler legt alle möglichen Steine, dann EndTiling.
        let round_before = game.state.round_number;
        let mut tsteps = 0;
        while game.state.phase == Phase::Tiling && tsteps < 200 {
            let pi = game.state.current_player;
            let actions = game.valid_tiling_actions(pi);
            let mv = match actions.first() {
                Some(a) => TilingMove::Place(*a),
                None => TilingMove::EndTiling { player: pi },
            };
            game.apply_tiling(&mv, &mut rng).expect("valider Tiling-Zug");
            tsteps += 1;
        }
        assert!(tsteps < 200, "Tiling terminiert");
        // Runde 1 ist nicht das Spielende → neue Runde, Phase wieder Drafting.
        assert_eq!(game.state.phase, Phase::Drafting);
        assert_eq!(game.state.round_number, round_before + 1);
        // Tiling-Flags zurückgesetzt; volle Reihen abgeräumt.
        assert_eq!(game.state.tiling_done, [false, false]);
    }

    #[test]
    fn start_placement_order_and_effect() {
        let mut rng = StdRng::seed_from_u64(50);
        let mut game = Game::start(names(), 0, vec![0, 1, 2], &mut rng);
        // first_player = 0 → Nicht-Startspieler (1) muss zuerst.
        let tid0 = game.state.dome_display[0].tile_id;
        // Startspieler zuerst → Fehler
        assert!(apply_start_placement(&mut game.state, 0, tid0, 0, 0, 0).is_err());
        // Nicht-Startspieler legt
        let tid = game.state.dome_display[0].tile_id;
        apply_start_placement(&mut game.state, 1, tid, 0, 0, 0).unwrap();
        assert!(!game.state.players[1].start_tile_pending);
        assert!(game.state.players[1].dome_grid.dome_slots[0][0].is_some());
        assert_eq!(game.state.dome_display.len(), 3); // nachgezogen
        // dann Startspieler
        let tid2 = game.state.dome_display[0].tile_id;
        apply_start_placement(&mut game.state, 0, tid2, 0, 0, 0).unwrap();
        assert!(!game.state.players[0].start_tile_pending);
    }

    /// Baustein B (zweistufiger Kuppel-Suchknoten): jeder Stufe-1-Kandidat
    /// (`generate_dome_moves`/`generate_draw_stack_moves`) MUSS mindestens
    /// eine legale Stufe-2-Rotation haben -- sonst würde Stufe 2 auf den
    /// Pass-Nothilfszweig zurückfallen und `pending_dome_choice` bliebe
    /// falsch hängen (siehe `drafting_actions`-Kommentar). Nicht optional:
    /// ohne diesen Test könnte eine künftige Regeländerung (z.B. eine
    /// rotationsabhängige Platzierungsregel) stillschweigend Sackgassen
    /// erzeugen.
    #[test]
    fn dome_slot_candidates_never_yield_a_dead_end_stage_two() {
        use rand::seq::IndexedRandom;

        let mut rng = StdRng::seed_from_u64(77);
        let mut game = Game::start(names(), 0, vec![0, 1, 2], &mut rng);
        for p in game.state.players.iter_mut() {
            p.start_tile_pending = false;
        }
        let mut checked_dome = 0;
        let mut checked_draw_stack = 0;
        let mut steps = 0;
        // Zufällig statt immer `actions[0]` waehlen -- sonst wuerde die
        // Auswahl (Stein-Zuege stehen zuerst in `drafting_actions`) einen
        // Stapel-Zug so gut wie nie tatsaechlich auslösen.
        while game.state.phase == Phase::Drafting && steps < 500 {
            for m in generate_dome_moves(&game.state) {
                assert!(
                    !dome_slot_rotation_candidates(&game.state, m.dome_tile_id, m.slot_row, m.slot_col)
                        .is_empty(),
                    "Kachel {} Slot ({},{}) hat keine legale Rotation",
                    m.dome_tile_id, m.slot_row, m.slot_col
                );
                checked_dome += 1;
            }
            for m in generate_draw_stack_moves(&game.state) {
                assert!(
                    !draw_stack_slot_rotation_candidates(
                        &game.state, m.chosen_id, m.slot_row, m.slot_col, &m.return_order
                    ).is_empty(),
                    "Kachel {} Slot ({},{}) hat keine legale Rotation",
                    m.chosen_id, m.slot_row, m.slot_col
                );
                checked_draw_stack += 1;
            }
            let actions = game.valid_drafting_actions();
            let action = actions.choose(&mut rng).unwrap().clone();
            game.apply_drafting(&action).expect("valider Zug");
            steps += 1;
        }
        assert!(checked_dome > 0, "Testvoraussetzung: mind. ein ChooseDomeSlot-Kandidat gesehen");
        assert!(checked_draw_stack > 0, "Testvoraussetzung: mind. ein ChooseDrawStackSlot-Kandidat gesehen");
    }
}
