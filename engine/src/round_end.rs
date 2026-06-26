//! Rundenende — Port von engine/round_end.py.
//!
//! Schritt 5: vollständige Tiling-Phase (Aktion, Validierung, Ausführung),
//! Scoring pro Stein, Special-Trigger, Bonus-Chip-Komplettierung und die
//! Rundenende-Strafen. Die scoring-tile-Endwertung (engine/scoring.py) folgt
//! als eigenes Modul in Schritt 6.

use crate::board::PlayerBoard;
use crate::dome::{DomeTile, SpaceType};
use crate::state::GameState;
use crate::supply::Tower;
use crate::tile::TileColor;

/// True, wenn die Dome-Reihe der Musterreihe `row_idx` mindestens einen gelegten
/// Slot mit offenem, passendem Space an gültiger Position hat. Single Source of
/// Truth für die Tiling-Platzierbarkeit einer Reihe — genutzt von Validierung
/// (Reihenfolge-Regel), Rundenende (unplatzierbare Reihen) und Serializer
/// (chippable rows); später auch vom MCTS.
pub fn row_has_open_matching_slot(player: &PlayerBoard, row_idx: usize, color: TileColor) -> bool {
    let dome_row = row_idx / 2;
    let space_row = row_idx % 2;
    let valid_si = [space_row * 2, space_row * 2 + 1];
    (0..3).any(|sc| {
        player.dome_grid.dome_slots[dome_row][sc]
            .as_ref()
            .map_or(false, |slot| {
                valid_si.iter().any(|&si| {
                    let sp = &slot.spaces[si];
                    !sp.is_filled() && !sp.is_locked && sp.accepts(color)
                })
            })
    })
}

// ── Tiling-Aktion ──────────────────────────────────────────────────────────────

/// Beschreibt, wie ein Spieler einen Stein aus einer vollen Musterreihe auf die
/// Kuppel legt. `dome_tile_id`/`rotation` nur relevant, wenn der Slot noch leer ist.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TilingAction {
    pub pattern_row: usize,
    pub slot_row: usize,
    pub slot_col: usize,
    pub space_index: usize,
    pub dome_tile_id: Option<usize>,
    pub rotation: u32,
}

// ── Pending/Unplatzierbare Reihen ───────────────────────────────────────────────

/// Indizes aller vollen Musterreihen (müssen noch gelegt werden).
pub fn get_pending_tiling_rows(player: &PlayerBoard) -> Vec<usize> {
    player
        .pattern_lines
        .iter()
        .enumerate()
        .filter(|(_, r)| r.is_complete())
        .map(|(i, _)| i)
        .collect()
}

/// Unplatzierbare Reihen am Rundenende: Reihe mit Steinen, deren Dome-Reihe
/// komplett belegt ist und keinen passenden freien Space hat → Strafleiste.
pub fn find_unplaceable_rows(player: &PlayerBoard) -> Vec<usize> {
    let mut unplaceable = Vec::new();
    for (row_idx, row) in player.pattern_lines.iter().enumerate() {
        let color = match row.color {
            Some(c) if !row.tiles.is_empty() => c,
            _ => continue,
        };
        let dome_row = row_idx / 2;
        let slots = &player.dome_grid.dome_slots[dome_row];
        // Noch freie Slots in der Dome-Reihe → Reihe bleibt liegen.
        if slots.iter().any(|s| s.is_none()) {
            continue;
        }
        if !row_has_open_matching_slot(player, row_idx, color) {
            unplaceable.push(row_idx);
        }
    }
    unplaceable
}

/// Verschiebt unplatzierbare Fliesen auf die Strafleiste (Überlauf → Turm).
/// Gibt die Anzahl verschobener Fliesen zurück.
pub fn process_unplaceable_rows(player: &mut PlayerBoard, tower: &mut Tower) -> usize {
    let mut total = 0;
    for row_idx in find_unplaceable_rows(player) {
        let tiles: Vec<_> = std::mem::take(&mut player.pattern_lines[row_idx].tiles);
        player.pattern_lines[row_idx].color = None;
        let n = tiles.len();
        let to_tower = player.add_broken(&tiles);
        tower.add(&to_tower);
        total += n;
    }
    total
}

// ── Validierung der Tiling-Aktion ───────────────────────────────────────────────

/// Gibt None zurück, wenn die Aktion gültig ist, sonst eine Fehlermeldung.
pub fn validate_tiling_action(
    state: &GameState,
    player_idx: usize,
    action: &TilingAction,
) -> Option<String> {
    if action.pattern_row >= 6 || action.slot_row >= 3 || action.slot_col >= 3 {
        return Some("Tiling-Aktion außerhalb des Rasters.".into());
    }
    let player = &state.players[player_idx];
    let row = &player.pattern_lines[action.pattern_row];

    if !row.is_complete() {
        return Some(format!("Musterreihe {} ist nicht voll.", action.pattern_row + 1));
    }

    // Regelwerk S.7: Reihen von oben nach unten — aber nur, wenn die frühere Reihe
    // tatsächlich platzierbar ist (passende Kuppelplatte vorhanden).
    let grid = &player.dome_grid;
    for ri in 0..action.pattern_row {
        let earlier = &player.pattern_lines[ri];
        if !earlier.is_complete() {
            continue;
        }
        let e_color = match earlier.color {
            Some(c) => c,
            None => continue,
        };
        if row_has_open_matching_slot(player, ri, e_color) {
            return Some(format!(
                "Reihe {} muss zuerst gelegt werden (von oben nach unten, Regelwerk S.7).",
                ri + 1
            ));
        }
    }

    let color = match row.color {
        Some(c) => c,
        None => return Some("Volle Reihe ohne Farbe.".into()),
    };
    let slot = &grid.dome_slots[action.slot_row][action.slot_col];

    match slot {
        None => {
            // Slot leer → Kachel muss neu platziert werden.
            let tile_id = match action.dome_tile_id {
                Some(id) => id,
                None => return Some("Slot ist leer — dome_tile_id muss angegeben werden.".into()),
            };
            let tile = match find_dome_tile(state, tile_id) {
                Some(t) => t,
                None => return Some(format!("Dome-Kachel {tile_id} nicht im Pool.")),
            };
            let rotated = match tile.rotated_spaces(action.rotation) {
                Ok(r) => r,
                Err(_) => return Some(format!("Ungültige Rotation: {}.", action.rotation)),
            };
            if action.space_index >= rotated.len() {
                return Some("Space-Index außerhalb der Kachel.".into());
            }
            if !rotated[action.space_index].accepts(color) {
                return Some(format!(
                    "Space {} nach Rotation {}° akzeptiert {} nicht.",
                    action.space_index,
                    action.rotation,
                    color.value()
                ));
            }
        }
        Some(slot) => {
            if action.space_index >= slot.spaces.len() {
                return Some("Space-Index außerhalb der Kachel.".into());
            }
            let space = &slot.spaces[action.space_index];
            if !space.accepts(color) {
                return Some(format!(
                    "Space {} in Slot ({},{}) akzeptiert {} nicht.",
                    action.space_index,
                    action.slot_row,
                    action.slot_col,
                    color.value()
                ));
            }
        }
    }

    None
}

// ── Ausführung der Tiling-Phase ─────────────────────────────────────────────────

/// Führt eine (bereits validierte) TilingAction aus: Reihe leeren, ggf. Kachel
/// platzieren, Stein auf den Space legen und Special freischalten.
pub fn execute_tiling_action(
    state: &mut GameState,
    player_idx: usize,
    action: &TilingAction,
) -> Result<(), String> {
    let (color, capacity) = {
        let row = &state.players[player_idx].pattern_lines[action.pattern_row];
        let color = row.color.ok_or("Reihe hat keine Farbe")?;
        (color, row.capacity())
    };

    // Reihenfolge-Tracking + Musterreihe leeren (1 Stein auf Kuppel, Rest in Turm).
    {
        let p = &mut state.players[player_idx];
        if action.pattern_row as i32 > p.tiled_max_row {
            p.tiled_max_row = action.pattern_row as i32;
        }
        let row = &mut p.pattern_lines[action.pattern_row];
        row.tiles.clear();
        row.color = None;
    }
    if capacity > 1 {
        let to_tower = vec![color; capacity - 1];
        state.tower.add(&to_tower);
    }

    // Neue Kachel platzieren, falls der Slot leer ist.
    let slot_empty =
        state.players[player_idx].dome_grid.dome_slots[action.slot_row][action.slot_col].is_none();
    if slot_empty {
        let tile_id = action
            .dome_tile_id
            .ok_or("Slot ist leer — dome_tile_id muss angegeben werden.")?;
        let mut tile = take_dome_tile(state, tile_id)
            .ok_or_else(|| format!("Dome-Kachel {tile_id} nicht gefunden"))?;
        tile.apply_rotation(action.rotation)?;
        state.players[player_idx]
            .dome_grid
            .place_dome_tile(tile, action.slot_row, action.slot_col)?;
    }

    // Stein auf den gewählten Space legen + Special ggf. freischalten.
    let slot = state.players[player_idx].dome_grid.dome_slots[action.slot_row][action.slot_col]
        .as_mut()
        .ok_or("Slot nach Platzierung unerwartet leer")?;
    if action.space_index >= slot.spaces.len() {
        return Err("Space-Index außerhalb der Kachel.".into());
    }
    slot.spaces[action.space_index].placed_color = Some(color);
    let newly_unlocked = slot.try_unlock_special();

    let name = state.players[player_idx].name.clone();
    state.log_event(format!(
        "{name}: {} → Slot ({},{}) Space {}{}",
        color.value(),
        action.slot_row,
        action.slot_col,
        action.space_index,
        if newly_unlocked { " [Special freigeschaltet!]" } else { "" }
    ));
    Ok(())
}

/// Komplette Tiling-Aktion inkl. Punktevergabe und Special-Trigger.
/// Gibt die insgesamt erzielten Punkte (Linien + Special-Bonus) zurück.
pub fn execute_full_tiling(
    state: &mut GameState,
    player_idx: usize,
    action: &TilingAction,
) -> Result<i32, String> {
    execute_tiling_action(state, player_idx, action)?;

    let (pts, explanation) = score_placed_tile(
        &state.players[player_idx],
        action.slot_row,
        action.slot_col,
        action.space_index,
    );
    state.players[player_idx].apply_score(pts);

    if pts > 0 {
        let name = state.players[player_idx].name.clone();
        state.log_event(format!(
            "🎯 {name}: +{pts} Pkt (Reihe {} → Kuppel {}/{} - {explanation})",
            action.pattern_row + 1,
            action.slot_row + 1,
            action.slot_col + 1
        ));
    }

    let bonus = check_special_trigger(state, player_idx, action.slot_row, action.slot_col);
    Ok(pts + bonus)
}

/// Prüft, ob der platzierte Stein einen freigeschalteten Special-Space abrechnet,
/// entnimmt dafür einen weißen Stein und vergibt den Kuppel-Bonus. Gibt die
/// Bonus-Punkte zurück.
pub fn check_special_trigger(
    state: &mut GameState,
    player_idx: usize,
    slot_row: usize,
    slot_col: usize,
) -> i32 {
    let sp_idx = {
        let slot = match &state.players[player_idx].dome_grid.dome_slots[slot_row][slot_col] {
            Some(s) => s,
            None => return 0,
        };
        match slot.spaces.iter().position(|s| s.space_type == SpaceType::Special) {
            Some(i) => i,
            None => return 0,
        }
    };

    let triggers = {
        let slot = state.players[player_idx].dome_grid.dome_slots[slot_row][slot_col]
            .as_ref()
            .unwrap();
        let sp = &slot.spaces[sp_idx];
        !sp.is_locked && !sp.placed_special
    };
    if !triggers {
        return 0;
    }

    // Kein Vorrats-Check nötig: exakt 9 Kuppelplatten tragen einen Special-Slot
    // und es gibt exakt 9 Special-Fliesen → der Vorrat kann nie leerlaufen.
    {
        let slot = state.players[player_idx].dome_grid.dome_slots[slot_row][slot_col]
            .as_mut()
            .unwrap();
        slot.spaces[sp_idx].placed_special = true;
    }

    let pattern_row = slot_row * 2 + sp_idx / 2;
    let bonus = (pattern_row + 1) as i32;
    state.players[player_idx].apply_score(bonus);
    let name = state.players[player_idx].name.clone();
    state.log_event(format!("⭐ {name}: +{bonus} Spezial-Punkte (Kuppel-Bonus)"));
    bonus
}

// ── Scoring-Phase ───────────────────────────────────────────────────────────────

/// Punkte für einen neu platzierten Stein: orthogonal verbundene Linien zählen
/// (horizontal + vertikal getrennt), allein stehend = 1 Punkt. Gibt zusätzlich
/// einen kurzen Erklärungstext zurück.
pub fn score_placed_tile(
    player: &PlayerBoard,
    slot_row: usize,
    slot_col: usize,
    space_index: usize,
) -> (i32, String) {
    let row6 = slot_row * 2 + space_index / 2;
    let col6 = slot_col * 2 + space_index % 2;

    let h = count_line(player, row6, col6, 0, 1);
    let v = count_line(player, row6, col6, 1, 0);

    if h == 1 && v == 1 {
        return (1, "alleinstehend".into());
    }

    let mut pts = 0;
    let mut parts: Vec<String> = Vec::new();
    if h > 1 {
        pts += h;
        parts.push(format!("{h} horizontal"));
    }
    if v > 1 {
        pts += v;
        parts.push(format!("{v} vertikal"));
    }
    (pts, parts.join(" + "))
}

/// Zählt die zusammenhängende, gefüllte Linie durch (row6, col6) in Richtung (dr,dc).
fn count_line(player: &PlayerBoard, row6: usize, col6: usize, dr: i32, dc: i32) -> i32 {
    let mut count = 1;
    for &sign in &[1i32, -1] {
        let mut r = row6 as i32 + sign * dr;
        let mut c = col6 as i32 + sign * dc;
        while (0..6).contains(&r) && (0..6).contains(&c) {
            match player.dome_grid.get_space(r as usize, c as usize) {
                Some(sp) if sp.is_filled() => {
                    count += 1;
                    r += sign * dr;
                    c += sign * dc;
                }
                _ => break,
            }
        }
    }
    count
}

/// Strafpunkte am Rundenende (Strafleiste −1/−2/−3/−4 + Startspieler-Marker −2).
/// Gibt das (negative) Delta zurück und protokolliert die Floor-Statistik.
pub fn score_penalty(player: &mut PlayerBoard) -> i32 {
    let mut penalty = player.broken_penalty();
    let floor_this_round = penalty.abs();
    player.total_floor_penalties += floor_this_round;
    player.floor_penalties_per_round.push(floor_this_round);

    if player.holds_first_player_marker {
        penalty += crate::board::FIRST_PLAYER_MARKER_PENALTY;
        player.holds_first_player_marker = false;
    }
    penalty
}

// ── Bonus-Chip-Komplettierung ───────────────────────────────────────────────────

/// Kann die (unvollständige) Reihe mit Bonusplättchen komplettiert werden?
/// Regel: pro fehlendem Slot 2 farbgleiche ODER 3 beliebige Chips.
pub fn can_complete_row_with_chips(player: &PlayerBoard, row_idx: usize) -> bool {
    let row = &player.pattern_lines[row_idx];
    let color = match row.color {
        Some(c) if !row.tiles.is_empty() => c,
        _ => return false,
    };
    let missing = row.spaces_left();
    if missing == 0 {
        return false;
    }
    // Greedy auf einer Kopie der Chip-Indizes (entfernte Chips = verbraucht).
    let mut pool: Vec<&crate::dome::BonusChip> = player.bonus_chips.iter().collect();
    for _ in 0..missing {
        let same: Vec<usize> = pool
            .iter()
            .enumerate()
            .filter(|(_, c)| c.colors.contains(&color))
            .map(|(i, _)| i)
            .collect();
        if same.len() >= 2 {
            let (a, b) = (same[0], same[1]);
            pool.remove(a.max(b));
            pool.remove(a.min(b));
        } else if pool.len() >= 3 {
            pool.drain(0..3);
        } else {
            return false;
        }
    }
    true
}

/// Komplettiert eine Musterreihe mit Bonusplättchen, falls möglich. Verbraucht
/// die genutzten Chips (entfernt sie). Gibt true zurück, wenn die Reihe voll wurde.
pub fn apply_bonus_chips_to_row(player: &mut PlayerBoard, row_idx: usize) -> bool {
    if !can_complete_row_with_chips(player, row_idx) {
        return false;
    }
    let color = player.pattern_lines[row_idx].color.expect("Reihe hat Farbe");
    let missing = player.pattern_lines[row_idx].spaces_left();
    for _ in 0..missing {
        let same: Vec<usize> = player
            .bonus_chips
            .iter()
            .enumerate()
            .filter(|(_, c)| c.colors.contains(&color))
            .map(|(i, _)| i)
            .collect();
        if same.len() >= 2 {
            let (a, b) = (same[0], same[1]);
            player.bonus_chips.remove(a.max(b));
            player.bonus_chips.remove(a.min(b));
            player.pattern_lines[row_idx].tiles.push(color);
        } else if player.bonus_chips.len() >= 3 {
            player.bonus_chips.drain(0..3);
            player.pattern_lines[row_idx].tiles.push(color);
        } else {
            break;
        }
    }
    player.pattern_lines[row_idx].is_complete()
}

/// Sicherheits-Cap für die Allokations-Enumeration (2^n Bitmasken).
const CHIP_ALLOC_CAP: usize = 14;

/// Kanonische Signatur eines Chips (sortierte Farben) — Chips mit gleicher
/// Signatur sind austauschbar (gleiche Restmenge nach Verbrauch).
fn chip_sig(chip: &crate::dome::BonusChip) -> String {
    let mut cs: Vec<&str> = chip.colors.iter().map(|c| c.value()).collect();
    cs.sort_unstable();
    cs.join(",")
}

/// Greedy-Verbrauch (2 farbgleiche bevorzugt, sonst 3 beliebige) als
/// ORIGINAL-Indizes — Fallback für den Cap.
fn greedy_chip_indices(player: &PlayerBoard, color: TileColor, missing: usize) -> Option<Vec<usize>> {
    let mut pool: Vec<usize> = (0..player.bonus_chips.len()).collect();
    let mut consumed = Vec::new();
    for _ in 0..missing {
        let same: Vec<usize> = pool
            .iter()
            .copied()
            .filter(|&i| player.bonus_chips[i].colors.contains(&color))
            .collect();
        if same.len() >= 2 {
            let (a, b) = (same[0], same[1]);
            consumed.push(a);
            consumed.push(b);
            pool.retain(|&i| i != a && i != b);
        } else if pool.len() >= 3 {
            let three: Vec<usize> = pool.iter().take(3).copied().collect();
            consumed.extend(&three);
            pool.retain(|&i| !three.contains(&i));
        } else {
            return None;
        }
    }
    Some(consumed)
}

/// Gültig (O(1)): `s` Chips, davon `cb` mit der Reihenfarbe, komplettieren
/// `missing` Slots gdw. `2·missing ≤ s ≤ 3·missing` und `cb ≥ 2·(3·missing − s)`.
fn chips_complete(s: usize, cb: usize, missing: usize) -> bool {
    if missing == 0 || s < 2 * missing || s > 3 * missing {
        return false;
    }
    let a = 3 * missing - s; // Anzahl 2-farbgleich-Gruppen
    cb >= 2 * a
}

/// Greedy-Allokation (Engine-Regel) als ORIGINAL-Index-Set. EINE Allokation,
/// O(missing·chips) — für den Hot-Path (DFS an jedem MCTS-Blatt) statt der
/// teuren 2^n-Enumeration von `chip_allocations`.
pub fn greedy_chip_alloc(player: &PlayerBoard, row_idx: usize) -> Option<Vec<usize>> {
    let row = &player.pattern_lines[row_idx];
    let color = match row.color {
        Some(c) if !row.tiles.is_empty() => c,
        _ => return None,
    };
    let missing = row.spaces_left();
    if missing == 0 {
        return None;
    }
    greedy_chip_indices(player, color, missing)
}

/// Distinkte Chip-Index-Mengen, die Reihe `row_idx` komplettieren (dedupliziert
/// nach Farb-Set-Signatur der verbrauchten Chips → gleiche Restmenge = ein
/// Zweig). Bei sehr vielen Chips nur die Greedy-Allokation (Cap-Fallback).
pub fn chip_allocations(player: &PlayerBoard, row_idx: usize) -> Vec<Vec<usize>> {
    let row = &player.pattern_lines[row_idx];
    let color = match row.color {
        Some(c) if !row.tiles.is_empty() => c,
        _ => return Vec::new(),
    };
    let missing = row.spaces_left();
    if missing == 0 {
        return Vec::new();
    }
    let n = player.bonus_chips.len();
    if n > CHIP_ALLOC_CAP {
        return greedy_chip_indices(player, color, missing).into_iter().collect();
    }

    let mut seen: std::collections::HashSet<Vec<String>> = std::collections::HashSet::new();
    let mut out = Vec::new();
    for mask in 1u32..(1u32 << n) {
        let subset: Vec<usize> = (0..n).filter(|&i| mask & (1 << i) != 0).collect();
        let s = subset.len();
        if s < 2 * missing || s > 3 * missing {
            continue;
        }
        let cb = subset
            .iter()
            .filter(|&&i| player.bonus_chips[i].colors.contains(&color))
            .count();
        if !chips_complete(s, cb, missing) {
            continue;
        }
        let mut sig: Vec<String> = subset.iter().map(|&i| chip_sig(&player.bonus_chips[i])).collect();
        sig.sort_unstable();
        if seen.insert(sig) {
            out.push(subset);
        }
    }
    out
}

/// Komplettiert Reihe `row_idx` mit GENAU den angegebenen Chips (Indizes in
/// `player.bonus_chips`). Gibt false, wenn die Auswahl ungültig ist.
pub fn apply_bonus_chips_with(player: &mut PlayerBoard, row_idx: usize, chip_indices: &[usize]) -> bool {
    let color = match player.pattern_lines[row_idx].color {
        Some(c) if !player.pattern_lines[row_idx].tiles.is_empty() => c,
        _ => return false,
    };
    let missing = player.pattern_lines[row_idx].spaces_left();
    let n = player.bonus_chips.len();
    let mut idx: Vec<usize> = chip_indices.to_vec();
    idx.sort_unstable();
    idx.dedup();
    if idx.len() != chip_indices.len() || idx.iter().any(|&i| i >= n) {
        return false;
    }
    let s = idx.len();
    let cb = idx.iter().filter(|&&i| player.bonus_chips[i].colors.contains(&color)).count();
    if !chips_complete(s, cb, missing) {
        return false;
    }
    // Absteigend entfernen, damit Indizes stabil bleiben.
    for &i in idx.iter().rev() {
        player.bonus_chips.remove(i);
    }
    for _ in 0..missing {
        player.pattern_lines[row_idx].tiles.push(color);
    }
    player.pattern_lines[row_idx].is_complete()
}

// ── Tiling-Aktionsgenerierung ───────────────────────────────────────────────────

/// Alle gültigen TilingActions eines Spielers: jede volle Musterreihe × freie
/// Spaces in bestehenden Slots sowie neu platzierbare Kacheln (alle Rotationen).
pub fn generate_tiling_actions(state: &GameState, player_idx: usize) -> Vec<TilingAction> {
    let player = &state.players[player_idx];
    let mut actions = Vec::new();

    for row_idx in get_pending_tiling_rows(player) {
        let color = match player.pattern_lines[row_idx].color {
            Some(c) => c,
            None => continue,
        };
        let dome_row = row_idx / 2;
        let space_row = row_idx % 2;
        let valid_si = [space_row * 2, space_row * 2 + 1];

        // Bereits gelegte Kacheln: passende offene Spaces.
        for sc in 0..3 {
            if let Some(slot) = &player.dome_grid.dome_slots[dome_row][sc] {
                for si in 0..slot.spaces.len() {
                    if !valid_si.contains(&si) {
                        continue;
                    }
                    let sp = &slot.spaces[si];
                    if sp.is_filled() || sp.is_locked || !sp.accepts(color) {
                        continue;
                    }
                    let a = TilingAction {
                        pattern_row: row_idx,
                        slot_row: dome_row,
                        slot_col: sc,
                        space_index: si,
                        dome_tile_id: None,
                        rotation: 0,
                    };
                    if validate_tiling_action(state, player_idx, &a).is_none() {
                        actions.push(a);
                    }
                }
            }
        }

        // Leere Slots: neue Kachel aus dem offenen Display, alle Rotationen.
        for sc in 0..3 {
            if player.dome_grid.dome_slots[dome_row][sc].is_some() {
                continue;
            }
            for tile in &state.dome_display {
                for &rotation in &[0u32, 90, 180, 270] {
                    let rotated = match tile.rotated_spaces(rotation) {
                        Ok(r) => r,
                        Err(_) => continue,
                    };
                    for si in 0..rotated.len() {
                        if !valid_si.contains(&si) {
                            continue;
                        }
                        if rotated[si].accepts(color) {
                            let a = TilingAction {
                                pattern_row: row_idx,
                                slot_row: dome_row,
                                slot_col: sc,
                                space_index: si,
                                dome_tile_id: Some(tile.tile_id),
                                rotation,
                            };
                            if validate_tiling_action(state, player_idx, &a).is_none() {
                                actions.push(a);
                            }
                        }
                    }
                }
            }
        }
    }
    actions
}

// ── Hilfsfunktionen ─────────────────────────────────────────────────────────────

/// Sucht eine Dome-Kachel im offenen Display oder im verdeckten Stapel (read-only).
fn find_dome_tile(state: &GameState, tile_id: usize) -> Option<&DomeTile> {
    state
        .dome_display
        .iter()
        .find(|t| t.tile_id == tile_id)
        .or_else(|| state.dome_tile_pool.iter().find(|t| t.tile_id == tile_id))
}

/// Entnimmt eine Dome-Kachel aus Display oder Stapel (für die Platzierung).
fn take_dome_tile(state: &mut GameState, tile_id: usize) -> Option<DomeTile> {
    if let Some(i) = state.dome_display.iter().position(|t| t.tile_id == tile_id) {
        return Some(state.dome_display.remove(i));
    }
    if let Some(i) = state.dome_tile_pool.iter().position(|t| t.tile_id == tile_id) {
        return Some(state.dome_tile_pool.remove(i));
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dome::build_dome_tile_pool;
    use crate::state::setup_new_game;
    use crate::tile::TileColor::*;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    fn game() -> GameState {
        let mut rng = StdRng::seed_from_u64(99);
        let mut s = setup_new_game(["P1".into(), "P2".into()], 0, &mut rng);
        for p in s.players.iter_mut() {
            p.start_tile_pending = false;
        }
        s
    }

    #[test]
    fn full_row_detected_as_pending() {
        let mut p = PlayerBoard::new(0, "P");
        p.pattern_lines[0].add_tiles(&[Rot]); // cap 1 → voll
        p.pattern_lines[2].add_tiles(&[Blau, Blau]); // cap 3 → nicht voll
        assert_eq!(get_pending_tiling_rows(&p), vec![0]);
    }

    #[test]
    fn unplaceable_when_domerow_full_no_match() {
        let mut p = PlayerBoard::new(0, "P");
        p.pattern_lines[0].add_tiles(&[Rot]);
        let pool = build_dome_tile_pool();
        for sc in 0..3 {
            let mut t = pool[11].clone(); // [Tuerkis, Schwarz, Rot, Wild]
            t.tile_id = 100 + sc;
            p.dome_grid.place_dome_tile(t, 0, sc).unwrap();
        }
        assert_eq!(find_unplaceable_rows(&p), vec![0]);

        let mut tower = Tower::default();
        let moved = process_unplaceable_rows(&mut p, &mut tower);
        assert_eq!(moved, 1);
        assert_eq!(p.broken_tiles.len(), 1);
        assert!(p.pattern_lines[0].tiles.is_empty());
    }

    #[test]
    fn tiling_places_stone_and_scores_solo() {
        let mut s = game();
        // Slot (0,0) mit einer Kachel belegen, die oben (si 0/1) Rot akzeptiert.
        // Pool[2] = [Tuerkis, Rot, Blau, Wild] → si1 = Rot.
        let tile = build_dome_tile_pool()[2].clone();
        let tid = tile.tile_id;
        s.dome_display.clear();
        s.dome_display.push(tile);
        // Reihe 0 (cap 1) mit Rot füllen.
        s.players[0].pattern_lines[0].add_tiles(&[Rot]);

        let action = TilingAction {
            pattern_row: 0,
            slot_row: 0,
            slot_col: 0,
            space_index: 1, // si 1 = Rot in pool[2]
            dome_tile_id: Some(tid),
            rotation: 0,
        };
        assert!(validate_tiling_action(&s, 0, &action).is_none());
        let before = s.players[0].score;
        let pts = execute_full_tiling(&mut s, 0, &action).unwrap();
        assert_eq!(pts, 1, "alleinstehender Stein = 1 Pkt");
        assert_eq!(s.players[0].score, before + 1);
        assert!(s.players[0].pattern_lines[0].is_empty());
        // Stein liegt auf 6×6-Zelle (0,1).
        assert!(s.players[0].dome_grid.get_space(0, 1).unwrap().is_filled());
    }

    #[test]
    fn line_scoring_counts_horizontal() {
        // Zwei benachbarte Steine in Reihe 6 → Linie der Länge 2 = 2 Punkte.
        let mut p = PlayerBoard::new(0, "P");
        // Kachel mit zwei Rot oben nebeneinander gibt es nicht garantiert; baue
        // manuell: belege (0,0) und (0,1) als gefüllt.
        let mut t = build_dome_tile_pool()[0].clone(); // [Gelb, Schwarz, Tuerkis, Special]
        t.spaces[0].placed_color = Some(Gelb);
        t.spaces[1].placed_color = Some(Schwarz);
        p.dome_grid.place_dome_tile(t, 0, 0).unwrap();
        // Score für den eben gelegten Stein an Space 1 (6×6-Zelle (0,1)).
        let (pts, desc) = score_placed_tile(&p, 0, 0, 1);
        assert_eq!(pts, 2);
        assert!(desc.contains("horizontal"));
    }

    #[test]
    fn penalty_includes_first_player_marker() {
        let mut p = PlayerBoard::new(0, "P");
        p.add_broken(&[Rot, Rot]); // −1 −2 = −3
        p.holds_first_player_marker = true;
        let pen = score_penalty(&mut p);
        assert_eq!(pen, -3 + crate::board::FIRST_PLAYER_MARKER_PENALTY);
        assert!(!p.holds_first_player_marker);
        assert_eq!(p.floor_penalties_per_round, vec![3]);
        assert_eq!(p.total_floor_penalties, 3);
    }

    #[test]
    fn bonus_chips_complete_row() {
        use crate::dome::BonusChip;
        let mut p = PlayerBoard::new(0, "P");
        // Reihe 2 (cap 3) mit 1 Rot → 2 fehlen.
        p.pattern_lines[2].add_tiles(&[Rot]);
        // 2 fehlende Slots × 2 farbgleiche Chips = 4 Rot-Chips.
        for i in 0..4 {
            p.bonus_chips.push(BonusChip { chip_id: i, colors: vec![Rot] });
        }
        assert!(can_complete_row_with_chips(&p, 2));
        assert!(apply_bonus_chips_to_row(&mut p, 2));
        assert!(p.pattern_lines[2].is_complete());
        assert!(p.bonus_chips.is_empty());
    }

    #[test]
    fn generate_tiling_actions_nonempty_for_full_row() {
        let mut s = game();
        let tile = build_dome_tile_pool()[2].clone(); // si1 = Rot
        s.dome_display.clear();
        s.dome_display.push(tile);
        s.players[0].pattern_lines[0].add_tiles(&[Rot]);
        let actions = generate_tiling_actions(&s, 0);
        assert!(actions.iter().any(|a| a.pattern_row == 0));
    }
}
