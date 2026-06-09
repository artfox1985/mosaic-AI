"""
Serialisiert den GameState in ein JSON-kompatibles Dict für die API.
Das GUI braucht nur zu rendern — keine Spiellogik im Browser.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.setup import GameState


def serialize_space(sp) -> dict:
    return {
        "type":   sp.space_type.name,        # NORMAL / WILD / SPECIAL
        "color":  sp.required_color.value if sp.required_color else None,
        "filled": sp.placed_color.value if sp.placed_color else (
                  "special" if sp.placed_special else None),
        "locked": sp.is_locked,
    }


def serialize_dome_tile(tile) -> dict | None:
    if tile is None or isinstance(tile, str):
        return None
    
    return {
        "id":     tile.tile_id,
        "bonus":  tile.bonus_points,
        "spaces": [serialize_space(s) for s in tile.spaces],
    }


def serialize_factory(f) -> dict:
    return {
        "id":           f.factory_id,
        "sun":          [t.value for t in f.sun_tiles],
        "moon":         [[t.value for t in stack] for stack in f.moon_stacks],
        "bonus_chip":   _serialize_chip(f.bonus_chip) if f.bonus_chip else None,
        "chip_revealed": f.bonus_chip_revealed,
    }


def serialize_large_factory(lf) -> dict:
    return {
        "sun":    [t.value for t in lf.sun_tiles],
        "moon":   [t.value for t in lf.moon_pool],
        "marker": lf.has_first_player_marker,
    }


def _serialize_chip(chip) -> dict | None:
    if chip is None:
        return None
    return {"id": chip.chip_id, "colors": [c.value for c in chip.colors]}

def _estimate_round_score(p) -> int:
    """Berechnet die voraussichtlichen Punkte für die aktuelle Runde inkl. Nachbarn."""
    grid = [[False]*6 for _ in range(6)]
    valid_empty = {i: [] for i in range(6)}

    # 1. Virtuelles 6x6 Raster aufbauen
    for sr in range(3):
        for sc in range(3):
            slot = p.dome_grid.dome_slots[sr][sc]
            if slot is not None:
                spaces = slot.spaces
                abs_r, abs_c = sr * 2, sc * 2
                
                # Oben Links
                if spaces[0].placed_color or spaces[0].placed_special: grid[abs_r][abs_c] = True
                elif not spaces[0].is_locked: valid_empty[abs_r].append(abs_c)
                # Oben Rechts
                if spaces[1].placed_color or spaces[1].placed_special: grid[abs_r][abs_c+1] = True
                elif not spaces[1].is_locked: valid_empty[abs_r].append(abs_c+1)
                # Unten Links
                if spaces[2].placed_color or spaces[2].placed_special: grid[abs_r+1][abs_c] = True
                elif not spaces[2].is_locked: valid_empty[abs_r+1].append(abs_c)
                # Unten Rechts
                if spaces[3].placed_color or spaces[3].placed_special: grid[abs_r+1][abs_c+1] = True
                elif not spaces[3].is_locked: valid_empty[abs_r+1].append(abs_c+1)

    est = 0
    penalties = [-1, -2, -3, -4]

    # 2. Beste Platzierung für volle Musterreihen simulieren
    for ri, row in enumerate(p.pattern_lines):
        if len(row.tiles) == row.capacity and row.color is not None:
            best_score = 1
            for c in valid_empty[ri]:
                h, v = 1, 1
                # Horizontale Nachbarn
                for i in range(c-1, -1, -1):
                    if grid[ri][i]: h += 1
                    else: break
                for i in range(c+1, 6):
                    if grid[ri][i]: h += 1
                    else: break
                # Vertikale Nachbarn
                for i in range(ri-1, -1, -1):
                    if grid[i][c]: v += 1
                    else: break
                for i in range(ri+1, 6):
                    if grid[i][c]: v += 1
                    else: break
                    
                pts = 0
                if h > 1: pts += h
                if v > 1: pts += v
                if pts == 0: pts = 1
                
                if pts > best_score:
                    best_score = pts
            est += best_score

    # 3. Minuspunkte (Boden + Marker) abziehen
    for i, t in enumerate(p.broken_tiles):
        if i < len(penalties):
            est += penalties[i]
            
    if p.holds_first_player_marker:
        est -= 2

    return est

def serialize_player(p) -> dict:
    return {
        "id":    p.player_id,
        "name":  p.name,
        "score": p.score,
        "pattern_lines": [
            {
                "index":    i,
                "capacity": row.capacity,
                "tiles":    [t.value for t in row.tiles],
                "color":    row.color.value if row.color else None,
            }
            for i, row in enumerate(p.pattern_lines)
        ],
        "dome_grid": [
            [serialize_dome_tile(slot) for slot in row]
            for row in p.dome_grid.dome_slots
        ],
        "floor":    [t.value for t in p.broken_tiles],
        "marker":   p.holds_first_player_marker,
        "tokens_used":   p.player_tokens_used,
        "chips_taken":   p.bonus_chips_used_this_round,
        "bonus_chips":   [_serialize_chip(c) for c in p.bonus_chips if c],
        "start_placed":  p.start_dome_tile is None,  # None = already placed
        "start_tile":    serialize_dome_tile(p.start_dome_tile),
        "can_place_dome": p.can_place_dome_tile(0),  # round injected by caller
        "estimated_score": _estimate_round_score(p),
    }


def serialize_state(state: "GameState") -> dict:
    players = []
    for p in state.players:
        pd = serialize_player(p)
        pd["can_place_dome"] = p.can_place_dome_tile(state.round_number)
        
        # NEU: Chip-Bestand für KI-Input (Nur ungenutzte Chips)
        # Wir zählen die Chips nach Farben (oder einfach als Gesamtmenge, 
        # falls dein Netz flache Inputs mag)
        unused_chips = [c for c in p.bonus_chips if c is not None and not getattr(c, 'used', False)]
        pd["unused_chip_count"] = len(unused_chips)
        
        # Optional: Detailliertere Chip-Info für das Netz (falls du die Farben brauchst)
        pd["unused_chip_colors"] = [color_val.value for c in unused_chips for color_val in c.colors]
        
        players.append(pd)

    # Alle Moon-Fliesen zählen, die durch Aktion C genommen werden können:
    moon_counts = {}

    # 1. Kleine Manufakturen
    for f in state.factories:
        for stack in f.moon_stacks:
            if stack:
                c_val = stack[-1].value
                moon_counts[c_val] = moon_counts.get(c_val, 0) + 1
                
    # 2. Große Manufaktur
    for t in state.large_factory.moon_pool:
        c_val = t.value
        moon_counts[c_val] = moon_counts.get(c_val, 0) + 1

    # Passen erlaubt wenn keine Aktion möglich
    can_pass = False
    if state.phase == "drafting":
        pi = state.current_player
        p = state.players[pi]
        
        # Aktion A: Kuppel (Regel: Nicht in Runde 5)
        a_possible = (
            state.round_number < 5
            and p.start_dome_tile is None
            and not p.has_used_all_tokens(state.round_number)
            and p.can_place_dome_tile(state.round_number)
            and (state.dome_display or state.dome_tile_pool)
        )
        # Aktion B: Steine Sun
        b_possible = (
            any(f.sun_tiles for f in state.factories)
            or bool(state.large_factory.sun_tiles)
        )
        # Aktion C: Steine Moon
        c_possible = (
            any(f.moon_top_colors() for f in state.factories)
            or bool(state.large_factory.moon_colors())
        )
        # Aktion D: Bonus Chips
        d_possible = (
            p.can_take_bonus_chip()
            and any(f.bonus_chip_revealed and f.bonus_chip is not None
                    for f in state.factories)
        )
        can_pass = not (a_possible or b_possible or c_possible or d_possible)

    return {
        "round":          state.round_number,
        "scoring_confirmed": getattr(state, "scoring_confirmed", False),
        "phase":          state.phase,
        "current_player": state.current_player,
        "scoring_tile_ids": getattr(state, "scoring_tile_ids", [0, 1, 2]),
        "can_pass":       can_pass,
        "factories":      [serialize_factory(f) for f in state.factories],
        "large_factory":  serialize_large_factory(state.large_factory),
        "moon_top_counts": moon_counts,
        "moon_top_colors": sorted(moon_counts.keys()),
        "dome_display":   [serialize_dome_tile(t) for t in state.dome_display],
        "dome_stack_count": len(state.dome_tile_pool),
        "special_supply": state.special_supply.count,
        "bag_count":      state.bag.count,
        "players":        players,
        "log":            state.log[-30:],
        "valid_moves":    _serialize_valid_moves(state),
        "valid_tiling_rows": _serialize_valid_tiling_rows(state),
        "chippable_tiling_rows": _serialize_chippable_tiling_rows(state),
    }


def _serialize_chippable_tiling_rows(state: "GameState") -> list[dict]:
    """
    Reihen die mit Bonuschips vollgemacht werden können UND danach
    einen validen Kuppelslot haben. Nur die erste solche Reihe pro Spieler
    (von oben nach unten — Reihenfolge muss eingehalten werden).
    """
    if state.phase != "tiling":
        return []
    try:
        from engine.game import generate_tiling_actions
        from engine.round_end import can_complete_row_with_chips
        result = []
        for pi, player in enumerate(state.players):
            if not player.bonus_chips:
                continue
            # Finde platzierbare Reihen (für Reihenfolge-Prüfung)
            actions = generate_tiling_actions(state, pi)
            placeable_rows = set(a.pattern_row for a in actions)
            # Prüfe jede nicht-volle Reihe von oben nach unten
            for ri, row in enumerate(player.pattern_lines):
                if row.is_complete or not row.tiles:
                    continue
                # Früherer platzierbarer Reihe noch offen?
                earlier_open = any(
                    ri2 < ri and player.pattern_lines[ri2].is_complete and ri2 in placeable_rows
                    for ri2 in range(ri)
                )
                if earlier_open:
                    break  # Reihenfolge erzwingen — keine weiteren Chips möglich
                # Kann mit Chips vollgemacht werden?
                if not can_complete_row_with_chips(player, ri):
                    continue
                # Wäre nach Vollmachen platzierbar?
                color = row.color
                dome_row = ri // 2
                space_row = ri % 2
                valid_si = [space_row * 2, space_row * 2 + 1]
                grid = player.dome_grid
                has_slot = any(
                    slot is not None and
                    any(
                        not slot.spaces[si].is_filled and
                        not slot.spaces[si].is_locked and
                        slot.spaces[si].accepts(color)
                        for si in valid_si
                    )
                    for slot in [grid.dome_slots[dome_row][sc] for sc in range(3)]
                )
                if has_slot:
                    result.append({"pi": pi, "ri": ri})
        return result
    except Exception:
        return []


def _serialize_valid_tiling_rows(state: "GameState") -> list[dict]:
    """Welche vollständigen Reihen haben tatsächlich eine platzierbare Aktion."""
    if state.phase != "tiling":
        return []
    try:
        from engine.game import generate_tiling_actions
        result = []
        for pi, player in enumerate(state.players):
            actions = generate_tiling_actions(state, pi)
            placeable_rows = set(a.pattern_row for a in actions)
            for ri, row in enumerate(player.pattern_lines):
                if row.is_complete and ri in placeable_rows:
                    result.append({"pi": pi, "ri": ri, "placeable": True})
        return result
    except Exception:
        return []


def _serialize_valid_moves(state: "GameState") -> list[dict]:
    """Alle gültigen Züge als strukturierte Liste — das GUI zeigt nur was erlaubt ist."""
    from engine.game import (
        generate_dome_moves, generate_bonus_chip_moves,
        validate_draw_from_stack
    )
    from engine.validation import generate_valid_moves
    from engine.moves import DrawFromStackMove

    if state.phase != "drafting":
        return []

    p = state.active_player
    
    # NEU: Wenn die Startkachel noch nicht liegt, ist DAS der einzig mögliche Zug!
    # Der Server bricht hier ab und berechnet gar nicht erst andere Züge.
    if p.start_dome_tile is not None:
        return [{"type": "start_tile_pending"}]

    moves = []

    # Stein-Züge (Aktion B + per-Fabrik-Moon)
    seen_moon_global = set()
    for m in generate_valid_moves(state):
        moves.append({
            "type":       "stone",
            "source":     m.take.source.name,
            "factory_id": m.take.factory_id,
            "color":      m.take.color.value,
            "row":        m.place.row_index,
            "moon_order": [t.value for t in m.take.moon_order],
        })

    # Aktion C: globale Moon-Moves (alle Manufakturen gleichzeitig)
    moon_tops_global = set()
    for f in state.factories:
        moon_tops_global |= f.moon_top_colors()
    for c in state.large_factory.moon_colors():
        moon_tops_global.add(c)
    for color in moon_tops_global:
        for ri in list(range(6)) + [-1]:
            from engine.validation import _validate_place
            if _validate_place(state, color, ri) is None:
                moves.append({
                    "type":       "stone",
                    "source":     "SMALL_FACTORY_MOON",
                    "factory_id": None,   # None = Aktion C (alle Manufakturen)
                    "color":      color.value,
                    "row":        ri,
                    "moon_order": [],
                })
                break  # nur einen repräsentativen Eintrag pro Farbe

    # Kuppelplatten aus Ablage
    for m in generate_dome_moves(state):
        moves.append({
            "type":       "dome_display",
            "tile_id":    m.dome_tile_id,
            "slot_row":   m.slot_row,
            "slot_col":   m.slot_col,
            "rotation":   m.rotation,
        })

    #Prüfen, ob verdeckt vom Stapel ziehen möglich ist (Aktion A)
    p = state.active_player
    # Wenn die Startkuppel liegt, man Platz für eine Kuppel hat und der Stapel nicht leer ist:
    if p.start_dome_tile is None and p.can_place_dome_tile(state.round_number) and len(state.dome_tile_pool) > 0:
        moves.append({
            "type": "dome_stack"
        })

    # Bonusplättchen
    for m in generate_bonus_chip_moves(state):
        moves.append({
            "type":       "bonus_chip",
            "factory_id": m.factory_id,
        })

    return moves