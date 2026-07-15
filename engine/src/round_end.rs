//! Rundenende — Port von engine/round_end.py.
//!
//! Schritt 5: vollständige Tiling-Phase (Aktion, Validierung, Ausführung),
//! Scoring pro Stein, Special-Trigger, Bonus-Chip-Komplettierung und die
//! Rundenende-Strafen. Die scoring-tile-Endwertung (engine/scoring.py) folgt
//! als eigenes Modul in Schritt 6.

use crate::board::{PlayerBoard, BROKEN_PENALTIES, MAX_BROKEN};
use crate::dome::SpaceType;
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
/// Kuppel legt. Während des Tilings werden KEINE Kuppelplatten gelegt (Regel) --
/// der Ziel-Slot muss also immer bereits eine Platte tragen.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TilingAction {
    pub pattern_row: usize,
    pub slot_row: usize,
    pub slot_col: usize,
    pub space_index: usize,
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
/// Gibt je betroffener Reihe `(row_idx, Farbe, Anzahl Fliesen)` zurück --
/// Aufrufer nutzen das für die Logausgabe (Reihe+Farbe sichtbar machen,
/// sonst passiert dieser Strafleisten-Übergang komplett stumm).
pub fn process_unplaceable_rows(player: &mut PlayerBoard, tower: &mut Tower) -> Vec<(usize, TileColor, usize)> {
    let mut moved = Vec::new();
    for row_idx in find_unplaceable_rows(player) {
        let color = player.pattern_lines[row_idx].color.expect("unplatzierbare Reihe hat Farbe");
        let tiles: Vec<_> = std::mem::take(&mut player.pattern_lines[row_idx].tiles);
        player.pattern_lines[row_idx].color = None;
        let n = tiles.len();
        let to_tower = player.add_broken(&tiles);
        tower.add(&to_tower);
        moved.push((row_idx, color, n));
    }
    moved
}

/// Wie stark würde [`process_unplaceable_rows`] die Strafleiste bei diesem
/// Spieler treffen, wenn es JETZT ausgeführt würde? Rein lesend (keine
/// Mutation, keine Fliesen bewegt) -- für die Suche (`mcts.rs::player_total`),
/// die diese deterministische Konsequenz schon VOR dem tatsächlichen
/// Drafting→Tiling-Übergang einpreisen soll: der DFS-Solver
/// (`solve_max_tiling_points`) erkennt zwar bereits, dass eine unplatzierbare
/// Reihe 0 Punkte beiträgt, zieht aber nicht die Strafpunkte ab, die sie beim
/// tatsächlichen Rundenende verursachen wird.
pub fn projected_unplaceable_penalty(player: &PlayerBoard) -> i32 {
    let unplaceable = find_unplaceable_rows(player);
    if unplaceable.is_empty() {
        return 0;
    }
    let n_tiles: usize = unplaceable.iter().map(|&ri| player.pattern_lines[ri].tiles.len()).sum();
    let before = player.broken_tiles.len();
    let after = (before + n_tiles).min(MAX_BROKEN);
    (before..after).map(|i| BROKEN_PENALTIES[i]).sum()
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
    let slot = match &grid.dome_slots[action.slot_row][action.slot_col] {
        Some(slot) => slot,
        None => {
            return Some(format!(
                "Slot ({},{}) hat noch keine Kuppelplatte — während des Tilings werden keine \
                 neuen Platten gelegt (nur via Aktion A in der Drafting-Phase).",
                action.slot_row, action.slot_col
            ))
        }
    };
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

    None
}

// ── Ausführung der Tiling-Phase ─────────────────────────────────────────────────

/// Führt eine (bereits validierte) TilingAction aus: Reihe leeren, ggf. Kachel
/// platzieren, Stein auf den Space legen und Special freischalten. Nur intern
/// genutzt (von `execute_full_tiling`) -- kein externer Aufrufer.
fn execute_tiling_action(
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

    // Stein auf den gewählten Space legen + Special ggf. freischalten. Der Slot
    // muss bereits eine Kuppelplatte tragen -- `validate_tiling_action` lehnt
    // leere Ziel-Slots ab, während des Tilings werden keine neuen Platten gelegt.
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
/// Bonus-Punkte zurück. Nur intern genutzt (von `execute_full_tiling`) -- kein
/// externer Aufrufer.
fn check_special_trigger(
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
///
/// WICHTIG: [`chips_complete`] ist hier NICHT anwendbar -- die Formel prüft
/// eine bereits konkret gewählte Teilmenge (`s` = deren Größe), nicht "gibt es
/// irgendeine passende Teilmenge im ganzen Pool". Mit überzähligen, für diese
/// Reihe irrelevanten Chips im Pool (`s` = `player.bonus_chips.len()`) würde
/// die Formel fälschlich "nicht komplettierbar" melden, sobald der Pool größer
/// als `3·missing` ist. Delegiert stattdessen an [`greedy_chip_alloc`], das
/// dieselbe Greedy-Regel korrekt über eine Index-Kopie simuliert.
pub fn can_complete_row_with_chips(player: &PlayerBoard, row_idx: usize) -> bool {
    greedy_chip_alloc(player, row_idx).is_some()
}

/// Komplettiert eine Musterreihe mit Bonusplättchen, falls möglich. Verbraucht
/// die genutzten Chips (entfernt sie). Gibt true zurück, wenn die Reihe voll wurde.
/// Greedy-Auswahl + Ausführung über [`greedy_chip_alloc`]/[`apply_bonus_chips_with`]
/// (dieselbe Regel, keine eigene zweite Simulation mehr).
pub fn apply_bonus_chips_to_row(player: &mut PlayerBoard, row_idx: usize) -> bool {
    match greedy_chip_alloc(player, row_idx) {
        Some(indices) => apply_bonus_chips_with(player, row_idx, &indices),
        None => false,
    }
}

/// Sicherheits-Cap für die Allokations-Enumeration (2^n Bitmasken).
const CHIP_ALLOC_CAP: usize = 14;

/// Kanonische Signatur eines Chips (Farb-Bitmaske) — Chips mit gleicher
/// Signatur sind austauschbar (gleiche Restmenge nach Verbrauch). `u8` statt
/// String: TileColor hat nur 6 Varianten, passt locker in ein Byte — spart
/// Allokation/Formatierung im heißen Pfad (`chip_allocations`, rekursiv oft
/// aufgerufen, siehe tiling_solver.rs NODE_BUDGET-Kommentar).
fn chip_sig(chip: &crate::dome::BonusChip) -> u8 {
    chip.colors.iter().fold(0u8, |acc, c| acc | (1 << (*c as u8)))
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

    // Perf: Größe erst aus der Bitmaske prüfen (billige count_ones()), BEVOR der
    // Subset-Vec gebaut wird — spart die Allokation für die meisten der bis zu
    // 2^14 Masken, da nur eine schmale Größen-Spanne (2·missing..=3·missing)
    // überhaupt infrage kommt. Dedup-Signatur als u8-Bitmaske (6 Farben passen
    // locker in ein Byte) statt String — keine Allokation/Formatierung/String-
    // Hashing mehr. Beides verhaltensgleich zur Vorversion, nur schneller
    // (relevant: dieser Pfad wird rekursiv sehr oft aufgerufen, siehe
    // tiling_solver.rs NODE_BUDGET-Kommentar).
    let mut seen: std::collections::HashSet<Vec<u8>> = std::collections::HashSet::new();
    let mut out = Vec::new();
    for mask in 1u32..(1u32 << n) {
        let s = mask.count_ones() as usize;
        if s < 2 * missing || s > 3 * missing {
            continue;
        }
        let subset: Vec<usize> = (0..n).filter(|&i| mask & (1 << i) != 0).collect();
        let cb = subset
            .iter()
            .filter(|&&i| player.bonus_chips[i].colors.contains(&color))
            .count();
        if !chips_complete(s, cb, missing) {
            continue;
        }
        let mut sig: Vec<u8> = subset.iter().map(|&i| chip_sig(&player.bonus_chips[i])).collect();
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
                    };
                    if validate_tiling_action(state, player_idx, &a).is_none() {
                        actions.push(a);
                    }
                }
            }
        }
    }
    actions
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
        assert_eq!(moved, vec![(0, Rot, 1)]);
        assert_eq!(p.broken_tiles.len(), 1);
        assert!(p.pattern_lines[0].tiles.is_empty());
    }

    #[test]
    fn projected_unplaceable_penalty_matches_actual_outcome() {
        // Gleiches Fixture wie unplaceable_when_domerow_full_no_match: die
        // projizierte Strafe (VOR jeder Mutation berechnet) muss exakt der
        // Strafe entsprechen, die process_unplaceable_rows danach wirklich
        // verursacht (broken_penalty-Differenz).
        let mut p = PlayerBoard::new(0, "P");
        p.pattern_lines[0].add_tiles(&[Rot]);
        let pool = build_dome_tile_pool();
        for sc in 0..3 {
            let mut t = pool[11].clone();
            t.tile_id = 300 + sc;
            p.dome_grid.place_dome_tile(t, 0, sc).unwrap();
        }
        assert_eq!(projected_unplaceable_penalty(&p), -1);

        let penalty_before = p.broken_penalty();
        let mut tower = Tower::default();
        process_unplaceable_rows(&mut p, &mut tower);
        let penalty_after = p.broken_penalty();
        assert_eq!(penalty_after - penalty_before, -1);
    }

    #[test]
    fn projected_unplaceable_penalty_escalates_with_existing_floor_tiles() {
        // Strafleiste hat schon 2 Fliesen (-1,-2 bereits verbraucht) -- die
        // naechste unplatzierbare Reihe muss mit -3 bewertet werden, nicht
        // wieder mit -1.
        use crate::tile::TileColor::{Blau, Schwarz};
        let mut p = PlayerBoard::new(0, "P");
        p.broken_tiles = vec![Blau, Schwarz];
        p.pattern_lines[0].add_tiles(&[Rot]);
        let pool = build_dome_tile_pool();
        for sc in 0..3 {
            let mut t = pool[11].clone();
            t.tile_id = 400 + sc;
            p.dome_grid.place_dome_tile(t, 0, sc).unwrap();
        }
        assert_eq!(projected_unplaceable_penalty(&p), -3);
    }

    #[test]
    fn projected_unplaceable_penalty_is_zero_when_row_still_placeable() {
        let mut p = PlayerBoard::new(0, "P");
        p.pattern_lines[0].add_tiles(&[Rot]);
        assert_eq!(projected_unplaceable_penalty(&p), 0);
    }

    #[test]
    fn tiling_places_stone_and_scores_solo() {
        let mut s = game();
        // Slot (0,0) mit einer Kachel belegen, die oben (si 0/1) Rot akzeptiert.
        // Pool[2] = [Tuerkis, Rot, Blau, Wild] → si1 = Rot. Waehrend des Tilings
        // werden KEINE neuen Kuppelplatten gelegt -- die Platte muss also schon
        // im Grid liegen (so, als waere sie zuvor per Aktion A gelegt worden).
        let tile = build_dome_tile_pool()[2].clone();
        s.players[0].dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        // Reihe 0 (cap 1) mit Rot füllen.
        s.players[0].pattern_lines[0].add_tiles(&[Rot]);

        let action = TilingAction {
            pattern_row: 0,
            slot_row: 0,
            slot_col: 0,
            space_index: 1, // si 1 = Rot in pool[2]
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
        // Slot muss schon eine Platte tragen (Tiling installiert keine neuen).
        let tile = build_dome_tile_pool()[2].clone(); // si1 = Rot
        s.players[0].dome_grid.place_dome_tile(tile, 0, 0).unwrap();
        s.players[0].pattern_lines[0].add_tiles(&[Rot]);
        let actions = generate_tiling_actions(&s, 0);
        assert!(actions.iter().any(|a| a.pattern_row == 0));
    }

    #[test]
    fn generate_tiling_actions_empty_for_row_with_no_templated_slot() {
        // Kein Slot in der passenden Dome-Reihe hat eine Platte -- waehrend des
        // Tilings duerfen KEINE neuen Kuppelplatten gelegt werden, also gibt es
        // fuer diese Reihe keine gueltige Tiling-Aktion (landet stattdessen auf
        // der Strafleiste via process_unplaceable_rows).
        let mut s = game();
        s.players[0].pattern_lines[0].add_tiles(&[Rot]);
        let actions = generate_tiling_actions(&s, 0);
        assert!(!actions.iter().any(|a| a.pattern_row == 0));
    }
}
