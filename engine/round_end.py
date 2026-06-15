"""
Rundenende für Mosaic-AI.

Das Rundenende besteht aus zwei Phasen:

1. TILING-PHASE
   Jeder Spieler hat eine oder mehrere volle Musterreihen.
   Für jede volle Reihe muss der Spieler aktiv entscheiden:
     a) Welche Kuppelkachel (DomeTile) aus seinem Vorrat er nehmen will
        (falls er noch keine auf dem Raster hat, wird sie neu platziert)
     b) In welchem Slot (3×3) die Kachel liegt / platziert wird
     c) In welcher Rotation (0°/90°/180°/270°) — nur beim erstmaligen Platzieren
     d) Auf welchen der 4 Spaces der Kachel der Stein kommt
   Der eine Stein der platziert wird kommt von der Musterreihe.
   Die restlichen (capacity - 1) Steine der Musterreihe gehen in den Turm.
   Unvollständige Musterreihen bleiben unverändert stehen.

2. SCORING-PHASE
   Für jeden platzierten Stein:
     - Orthogonal verbundene Steine zählen mit (horizontal + vertikal getrennt)
     - Steht der Stein allein: 1 Punkt
   Strafleiste: progressiv [−1, -2, -3, -4]
   Startspieler-Marker: −2 Punkt (zusätzlich zur Strafleiste)
   Punkte können nie unter 0 fallen.
   Special-Space freigeschaltet: Spieler nimmt sofort einen weißen Stein
   aus dem Sondervorrat und platziert ihn — gibt Bonus-Punkte.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

from engine.tile import TileColor
from engine.dome import DomeTile, SpaceType

if TYPE_CHECKING:
    from engine.setup import GameState
    from engine.board import PlayerBoard


# ---------------------------------------------------------------------------
# Tiling-Aktion: was ein Spieler für eine volle Musterreihe entscheidet
# ---------------------------------------------------------------------------

@dataclass
class TilingAction:
    """
    Beschreibt wie ein Spieler einen Stein aus einer vollen Musterreihe
    auf die Kuppel legt.

    pattern_row:  Index der vollen Musterreihe (0–5)
    slot_row:     Zeile im 3×3 Dome-Raster (0–2)
    slot_col:     Spalte im 3×3 Dome-Raster (0–2)
    space_index:  Index des Spaces auf der Kachel (0–3)
    dome_tile_id: ID der zu platzierenden Kachel (nur wenn Slot noch leer)
    rotation:     Rotation beim erstmaligen Platzieren (0/90/180/270)
    """
    pattern_row:  int
    slot_row:     int
    slot_col:     int
    space_index:  int
    dome_tile_id: Optional[int] = None   # None = Kachel bereits im Slot
    rotation:     int           = 0


# @dataclass
# class SpecialTilingAction:
    # """
    # Platzierung eines weißen Steins auf einen freigeschalteten Special-Space.

    # slot_row, slot_col: der Dome-Slot der den Special-Space enthält
    # space_index:        immer der Index des Special-Spaces auf der Kachel
    # """
    # slot_row:    int
    # slot_col:    int
    # space_index: int


# ---------------------------------------------------------------------------
# Validierung der Tiling-Aktion
# ---------------------------------------------------------------------------

def validate_tiling_action(
    state: "GameState",
    player_idx: int,
    action: TilingAction,
) -> Optional[str]:
    """Gibt None zurück wenn gültig, sonst Fehlermeldung."""
    player = state.players[player_idx]
    row = player.pattern_lines[action.pattern_row]

    if not row.is_complete:
        return f"Musterreihe {action.pattern_row + 1} ist nicht voll."

    # Regelwerk S.7: Reihen von oben nach unten — aber nur wenn die frühere
    # Reihe auch tatsächlich platzierbar ist (passende Kuppelplatte vorhanden).
    # Nicht-platzierbare Reihen dürfen spätere platzierbare Reihen nicht blockieren.
    grid = player.dome_grid
    for ri in range(action.pattern_row):
        earlier = player.pattern_lines[ri]
        if not earlier.is_complete:
            continue
        # Prüfe ob diese frühere Reihe einen passenden Space hat
        e_color = earlier.color
        e_dome_row = ri // 2
        e_space_row = ri % 2
        e_valid_si = [e_space_row * 2, e_space_row * 2 + 1]
        e_has_action = any(
            slot is not None and
            any(
                not slot.spaces[si].is_filled and
                not slot.spaces[si].is_locked and
                slot.spaces[si].accepts(e_color)
                for si in e_valid_si
            )
            for slot in [grid.dome_slots[e_dome_row][sc] for sc in range(3)]
        )
        if e_has_action:
            return (
                f"Reihe {ri + 1} muss zuerst gelegt werden "
                f"(von oben nach unten, Regelwerk S.7)."
            )

    color = row.color
    grid = player.dome_grid
    slot = grid.dome_slots[action.slot_row][action.slot_col]

    # Slot leer → Kachel muss neu platziert werden
    if slot is None:
        if action.dome_tile_id is None:
            return "Slot ist leer — dome_tile_id muss angegeben werden."
        # Kachel muss im Pool des Spielers sein
        tile = _find_dome_tile(state, action.dome_tile_id)
        if tile is None:
            return f"Dome-Kachel {action.dome_tile_id} nicht im Pool."
        if action.rotation not in (0, 90, 180, 270):
            return f"Ungültige Rotation: {action.rotation}."
        # Prüfen ob der Space nach Rotation die Farbe akzeptiert
        from engine.dome import ROTATION_MAP
        rotated = [tile.spaces[i] for i in ROTATION_MAP[action.rotation]]
        space = rotated[action.space_index]
        if not space.accepts(color):
            return (
                f"Space {action.space_index} nach Rotation {action.rotation}° "
                f"akzeptiert {color.value} nicht."
            )
    else:
        # Slot bereits belegt → Space direkt prüfen
        space = slot.spaces[action.space_index]
        if not space.accepts(color):
            return (
                f"Space {action.space_index} in Slot ({action.slot_row},"
                f"{action.slot_col}) akzeptiert {color.value} nicht "
                f"(Typ: {space.space_type}, belegt: {space.is_filled})."
            )

    return None


# def validate_special_tiling(
    # state: "GameState",
    # player_idx: int,
    # action: SpecialTilingAction,
# ) -> Optional[str]:
    # if state.special_supply.is_empty:
        # return "Kein weißer Stein mehr im Vorrat."
    # player = state.players[player_idx]
    # slot = player.dome_grid.dome_slots[action.slot_row][action.slot_col]
    # if slot is None:
        # return f"Slot ({action.slot_row},{action.slot_col}) ist leer."
    # space = slot.spaces[action.space_index]
    # if not space.accepts_special():
        # return (
            # f"Space {action.space_index} ist kein offener Special-Space "
            # f"(locked={space.is_locked}, filled={space.is_filled})."
        # )
    # return None


# ---------------------------------------------------------------------------
# Ausführung der Tiling-Phase
# ---------------------------------------------------------------------------

def execute_tiling_action(
    state: "GameState",
    player_idx: int,
    action: TilingAction,
) -> None:
    """Führt eine TilingAction aus (bereits validiert)."""
    from engine.dome import ROTATION_MAP

    player = state.players[player_idx]
    row = player.pattern_lines[action.pattern_row]
    color = row.color
    capacity = row.capacity

    # Reihenfolge-Tracking: höchste (am weitesten unten gelegene) Reihe merken.
    # Sobald hier gelegt wird, sind frühere Reihen tabu (Chips/Abrechnung).
    prev = getattr(player, "tiled_max_row", -1)
    if action.pattern_row > prev:
        player.tiled_max_row = action.pattern_row

    # Musterreihe leeren: 1 Stein geht auf Kuppel, Rest in Turm
    row.tiles = []
    row.color = None
    to_tower = [color] * (capacity - 1)
    if to_tower:
        state.tower.add(to_tower)

    grid = player.dome_grid
    slot = grid.dome_slots[action.slot_row][action.slot_col]

    # Neue Kachel platzieren falls Slot leer
    if slot is None:
        tile = _find_dome_tile(state, action.dome_tile_id)
        if tile is None:
            raise ValueError(f"Dome-Kachel {action.dome_tile_id} nicht gefunden")
        tile.apply_rotation(action.rotation)
        grid.place_dome_tile(tile, action.slot_row, action.slot_col)
        if tile in state.dome_display:
            state.dome_display.remove(tile)
        elif tile in state.dome_tile_pool:
            state.dome_tile_pool.remove(tile)
        # Falls schon entfernt (doppelte Aktion) → kein Crash
        slot = tile

    # Stein auf den gewählten Space legen
    space = slot.spaces[action.space_index]
    space.placed_color = color

    # Special-Space ggf. freischalten
    newly_unlocked = slot.try_unlock_special()

    state.log_event(
        f"{player.name}: {color.value} → Slot "
        f"({action.slot_row},{action.slot_col}) Space {action.space_index}"
        + (" [Special freigeschaltet!]" if newly_unlocked else "")
    )

def execute_full_tiling(state, pi, ta) -> int:
    """
    Führt die komplette Tiling-Aktion aus: Platzieren, Punkten, Spezial-Trigger und Logging.
    """
    # 1. Stein platzieren
    execute_tiling_action(state, pi, ta)
    
    # 2. Spieler und Punkte ermitteln (TUPEL ENTPACKEN!)
    player = state.players[pi]
    pts, explanation = score_placed_tile(player, ta.slot_row, ta.slot_col, ta.space_index)
    
    # 3. Punkte gutschreiben
    player.apply_score(pts)
    
    # 4. DAS WICHTIGE LOGGING (Jetzt sogar mit dem Erklärungstext!)
    if pts > 0:
        msg = f"🎯 {player.name}: +{pts} Pkt (Reihe {ta.pattern_row+1} → Kuppel {ta.slot_row+1}/{ta.slot_col+1} - {explanation})"
        state.log_event(msg)
    
    # 5. Spezial-Trigger
    bonus_pts = check_special_trigger(state, player, ta.slot_row, ta.slot_col)

    # 6. Gesamte Punkte zurückgeben (für game.py Statistik)
    return pts + bonus_pts

def check_special_trigger(state, player, slot_row: int, slot_col: int) -> int:
    """
    Prüft, ob der platzierte Stein einen Kuppel-Bonus auslöst.
    Gibt die erreichten Bonus-Punkte zurück.
    """
    bonus = 0
    slot = player.dome_grid.dome_slots[slot_row][slot_col]
    
    # Suche das Spezial-Feld in diesem Slot
    sp_idx = next((i for i, s in enumerate(slot.spaces) if s.space_type.name == 'SPECIAL'), -1)
    
    if sp_idx != -1:
        sp = slot.spaces[sp_idx]
        # Prüfe ob es gerade durch dieses Tiling entsperrt und noch nicht abgerechnet wurde
        if not sp.is_locked and not getattr(sp, 'placed_special', False):
            
            # --- NEU HINZUGEFÜGT: Vorrat prüfen und Stein entnehmen ---
            if state.special_supply.is_empty:
                state.log_event("Kein Spezialfliesen-Vorrat mehr! (Kein Bonus)")
                return 0
            
            state.special_supply.take(1)
            # -----------------------------------------------------------
            
            sp.placed_special = True
            pattern_row = slot_row * 2 + (sp_idx // 2)
            bonus = pattern_row + 1
            
            if bonus > 0:
                player.apply_score(bonus)
                state.log_event(f"⭐ {player.name}: +{bonus} Spezial-Punkte (Kuppel-Bonus)")
                
    return bonus
    
# def execute_special_tiling(
    # state: "GameState",
    # player_idx: int,
    # action: SpecialTilingAction,
# ) -> int:
    # """
    # Platziert einen weißen Stein auf einen Special-Space.
    # Bonus = Tiling-Reihe (1-6) in der der Space liegt.
    # """
    # player = state.players[player_idx]
    # grid = player.dome_grid
    # slot = grid.dome_slots[action.slot_row][action.slot_col]
    # space = slot.spaces[action.space_index]
    # space.place_special_tile()
    # state.special_supply.take(1)

    # # Bonus = Tiling-Reihe (1-basiert) in der der Special-Space liegt
    # # pattern_row: 0-basierte Reihe aus Slot-Position + Space-Index
    # pattern_row = action.slot_row * 2 + (action.space_index // 2)
    # bonus = pattern_row + 1  # Reihe 1-6

    # player.apply_score(bonus)
    # state.log_event(
        # f"⭐ {player.name}: weißer Stein auf Special-Space "
        # f"({action.slot_row},{action.slot_col}) +{bonus} Pkt (Reihe {bonus})"
    # )
    # return bonus


# ---------------------------------------------------------------------------
# Scoring-Phase
# ---------------------------------------------------------------------------

def score_placed_tile(
    player: "PlayerBoard",
    slot_row: int,
    slot_col: int,
    space_index: int,
) -> tuple[int, str]:
    """
    Berechnet die Punkte für einen neu platzierten Stein auf der Kuppel.
    Gibt ein Tupel zurück: (Punkte, Erklärungstext)
    """
    # 6×6-Koordinaten des platzierten Steins
    row6 = slot_row * 2 + space_index // 2
    col6 = slot_col * 2 + space_index % 2

    h = _count_line(player, row6, col6, 0, 1)   # horizontal
    v = _count_line(player, row6, col6, 1, 0)   # vertikal

    # 1. Fall: Stein steht völlig allein
    if h == 1 and v == 1:
        return 1, "alleinstehend"
        
    # 2. Fall: Stein ist Teil einer oder mehrerer Linien
    pts = 0
    desc_parts = []
    
    if h > 1:
        pts += h
        desc_parts.append(f"{h} horizontal")
    if v > 1:
        pts += v
        desc_parts.append(f"{v} vertikal")
        
    return pts, " + ".join(desc_parts)


def _count_line(
    player: "PlayerBoard",
    row6: int,
    col6: int,
    dr: int,
    dc: int,
) -> int:
    """Zählt die zusammenhängende Linie durch (row6, col6) in Richtung (dr,dc)."""
    count = 1
    # vorwärts
    r, c = row6 + dr, col6 + dc
    while 0 <= r < 6 and 0 <= c < 6:
        space = player.dome_grid.get_space(r, c)
        if space and space.is_filled:
            count += 1
            r += dr
            c += dc
        else:
            break
    # rückwärts
    r, c = row6 - dr, col6 - dc
    while 0 <= r < 6 and 0 <= c < 6:
        space = player.dome_grid.get_space(r, c)
        if space and space.is_filled:
            count += 1
            r -= dr
            c -= dc
        else:
            break
    return count


def score_penalty(player: "PlayerBoard") -> int:
    """
    Strafpunkte am Rundenende:
    - Strafleiste: −1/−2/−3/-4 für Slot 1/2/3/4
    - Startspielerstein: −2 (dediziertes Feld, getrennt von Strafleiste)
    Gibt den (negativen) Delta zurück.
    """
    penalty = player.broken_penalty()   # −1/−2/−3/-4 pro Slot
    player.total_floor_penalties += abs(penalty)
    
    if player.holds_first_player_marker:
        penalty += player.first_player_marker_penalty   # −2
        player.holds_first_player_marker = False
    return penalty


# ---------------------------------------------------------------------------
# Vollständiges Rundenende
# ---------------------------------------------------------------------------

def can_complete_row_with_chips(
    player: "PlayerBoard",
    row_idx: int,
    state: "GameState | None" = None,
) -> bool:
    row = player.pattern_lines[row_idx]
    if not row.tiles or row.color is None:
        return False
    missing = row.spaces_left
    if missing == 0:
        return False

    # Chip-Verfügbarkeit prüfen (bestehende Logik)
    color = row.color
    unused = [c for c in player.bonus_chips if c is not None]
    same_color = [c for c in unused if hasattr(c, 'colors') and color in c.colors]
    has_chips = False
    if len(same_color) >= missing * 2:
        has_chips = True
    elif len(unused) >= missing * 3:
        has_chips = True
    else:
        chips_left = list(unused)
        for _ in range(missing):
            same = [c for c in chips_left if hasattr(c, 'colors') and color in c.colors]
            if len(same) >= 2:
                chips_left.remove(same[0]); chips_left.remove(same[1])
            elif len(chips_left) >= 3:
                chips_left = chips_left[3:]
            else:
                break
        else:
            has_chips = True

    if not has_chips:
        return False

    # NEU: Platzierbarkeit prüfen wenn State verfügbar
    if state is not None:
        from engine.game import generate_tiling_actions
        # Temporär auffüllen
        row.tiles.extend([color] * missing)
        pi = next(i for i, p in enumerate(state.players) if p is player)
        actions = generate_tiling_actions(state, pi)
        placeable = any(a.pattern_row == row_idx for a in actions)
        # Rückrollen
        del row.tiles[-missing:]
        if not placeable:
            return False

    return True


def apply_bonus_chips_to_row(
    player: "PlayerBoard",
    row_idx: int,
) -> bool:
    """
    [10] Vervollständigt eine Musterreihe mit Bonusplättchen falls möglich.
    Gibt True zurück wenn Reihe komplettiert wurde.
    Markiert verwendete Chips als genutzt (setzt sie auf None).
    """
    row = player.pattern_lines[row_idx]
    if not can_complete_row_with_chips(player, row_idx):
        return False
    color = row.color
    missing = row.spaces_left
    chips = player.bonus_chips
    for _ in range(missing):
        same_idx = next(
            (i for i, c in enumerate(chips)
             if c is not None and hasattr(c, 'colors') and color in c.colors),
            None
        )
        if same_idx is not None:
            second = next(
                (i for i, c in enumerate(chips)
                 if c is not None and i != same_idx
                 and hasattr(c, 'colors') and color in c.colors),
                None
            )
            if second is not None:
                chips[same_idx] = None; chips[second] = None
                row.tiles.append(color)
                continue
        # 3 beliebige
        avail = [i for i, c in enumerate(chips) if c is not None]
        if len(avail) >= 3:
            for i in avail[:3]:
                chips[i] = None
            row.tiles.append(color)
        else:
            break
    return row.is_complete


def check_drafting_complete(state: "GameState") -> bool:
    chips_available = any(
        f.bonus_chip is not None and f.bonus_chip_revealed
        for f in state.factories
    )
    if chips_available:
        return False

    factories_empty = (
        all(f.is_fully_empty and (f.bonus_chip is None or f.bonus_chip_revealed)
            for f in state.factories)
        and state.large_factory.is_empty
    )

    if not factories_empty:
        return False

    if state.round_number >= 5:
        return True

    tokens_done = all(p.has_used_all_tokens(state.round_number) for p in state.players)
    if tokens_done:
        return True

    # Fabriken leer aber Tokens noch nicht verbraucht —
    # Phase endet trotzdem wenn kein Spieler mehr irgendetwas tun kann
    from engine.game import generate_dome_moves, generate_bonus_chip_moves
    from engine.validation import generate_valid_moves
    original = state.current_player
    for pi in range(2):
        state.current_player = pi
        p = state.players[pi]
        # DrawFromStack prüfen: Token verfügbar + Stapel nicht leer + Platz im Grid
        can_draw_from_stack = (
            state.round_number < 5
            and not p.has_used_all_tokens(state.round_number)
            and bool(state.dome_tile_pool)
            and p.can_place_dome_tile(state.round_number)
        )
        if (generate_valid_moves(state)
                or generate_dome_moves(state)
                or generate_bonus_chip_moves(state)
                or can_draw_from_stack):
            state.current_player = original
            return False
    state.current_player = original
    return True


def get_pending_tiling_rows(player: "PlayerBoard") -> list[int]:
    """Gibt Indizes aller vollen Musterreihen zurück die noch gelegt werden müssen."""
    return [i for i, row in enumerate(player.pattern_lines) if row.is_complete]


def find_unplaceable_rows(player: "PlayerBoard", state=None) -> list[int]:
    """
    Ermittelt unplatzierbare Musterreihen am Rundenende.
    Eine Reihe ist unplatzierbar wenn:
    - Alle 3 Slots der Dome-Reihe belegt sind UND keine davon ein passendes Farbfeld hat
    → Fliesen gehen automatisch auf Strafleiste beim Rundenende.
    Reihen mit noch freien Slots bleiben liegen — der Spieler kann noch eine
    passende Kuppelplatte legen.
    """
    unplaceable = []
    for row_idx, row in enumerate(player.pattern_lines):
        if not row.tiles or row.color is None:
            continue
        color = row.color
        dome_row = row_idx // 2
        space_row = row_idx % 2
        valid_si = [space_row * 2, space_row * 2 + 1]
        slots_in_row = [player.dome_grid.dome_slots[dome_row][sc] for sc in range(3)]
        if not all(s is not None for s in slots_in_row):
            continue  # noch freie Slots → bleibt liegen
        has_match = any(
            slot.spaces[si].accepts(color)
            for slot in slots_in_row
            for si in valid_si
            if not slot.spaces[si].is_filled and not slot.spaces[si].is_locked
        )
        if not has_match:
            unplaceable.append(row_idx)
    return unplaceable


def process_unplaceable_rows(
    player: "PlayerBoard",
    tower,
    state,
) -> int:
    """
    [9] Verschiebt unplatzierbare Fliesen auf das Straffeld.
    Gibt Anzahl der verschobenen Fliesen zurück.
    """
    total = 0
    for row_idx in find_unplaceable_rows(player, state):
        row = player.pattern_lines[row_idx]
        tiles = list(row.tiles)
        row.tiles = []; row.color = None
        to_tower = player.add_broken(tiles)
        tower.add(to_tower)
        total += len(tiles)
        state.log_event(
            f"{player.name}: Reihe {row_idx+1} unplatzierbar → "
            f"{len(tiles)} Fliesen auf Straffeld"
        )
    return total


def clear_emptied_pattern_rows(player: "PlayerBoard", tower) -> None:
    """
    [11] Nach Phase 2: Reihen deren rechtestes Feld (index capacity-1) leer ist
    werden geleert — Fliesen in den Turm.
    Unvollständige Reihen bleiben stehen.
    """
    for row in player.pattern_lines:
        if not row.tiles:
            continue
        # Rechtes Feld = letzter Slot (capacity-1): leer wenn Reihe nicht komplett
        # UND die Fliese dort nicht in Phase 2 platziert wurde
        # Konkret: wenn row.tiles vorhanden aber row ist nicht komplett
        # und Phase 2 hat die rechte Fliese weggenommen → row.tiles[capacity-1] fehlt
        # Einfache Regel: Nach Tiling ist das rechte Feld leer wenn die Reihe
        # eine vollständige Reihe war (wurde geleert durch execute_tiling_action)
        # → Hier nur unvollständige Reihen prüfen die NICHT belegt wurden
        pass  # Vollständige Reihen werden durch execute_tiling_action geleert


def apply_round_scoring(state: "GameState", tiling_scores: dict[int, int]) -> None:
    """
    Wendet Punkte und Strafen am Rundenende an.

    tiling_scores: {player_idx: punkte_aus_tiling}
    Strafpunkte werden hier ebenfalls angewendet.
    """
    for player_idx, player in enumerate(state.players):
        # Tiling-Punkte
        tile_pts = tiling_scores.get(player_idx, 0)
        player.apply_score(tile_pts)

        # Strafpunkte
        penalty = score_penalty(player)
        player.apply_score(penalty)

        # Strafsteine in den Turm
        broken = player.clear_broken()
        if broken:
            state.tower.add(broken)

        state.log_event(
            f"{player.name}: +{tile_pts} Tiling, {penalty} Strafe "
            f"→ Gesamt: {player.score} Punkte"
        )


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _find_dome_tile(state: "GameState", tile_id: int) -> Optional[DomeTile]:
    """Sucht eine Dome-Kachel im offenen Display ODER im Pool anhand der ID."""
    # 1. Zuerst im offenen Display (G) suchen
    for tile in state.dome_display:
        if tile.tile_id == tile_id:
            return tile
            
    # 2. Falls nicht da, im verdeckten Stapel (F) suchen
    for tile in state.dome_tile_pool:
        if tile.tile_id == tile_id:
            return tile
            
    return None