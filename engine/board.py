"""
Player board for Mosaic-AI.

The player board has three main areas:

1. Pattern Lines  — 6 rows (lengths 1–6), tiles accumulate here during
                    the acquisition phase. At round end, a complete row
                    places one tile onto the Dome Grid.

2. Dome Grid      — a 6×6 grid built from nine 2×2 DomeTiles that the
                    player collects over the course of the game.
                    Arranged as a 3×3 arrangement of dome tiles:
                        (0,0) (0,1) (0,2)
                        (1,0) (1,1) (1,2)
                        (2,0) (2,1) (2,2)
                    Each dome tile occupies rows [2r, 2r+1] and
                    cols [2c, 2c+1] of the 6×6 grid.

3. Broken Tiles   — overflow / penalty area, max 4 tiles.
                    Tiles beyond 4 are discarded to the tower.
                    Penalty at round end: −1 per tile (1–4).

4. Bonus Chips    — collected during the round; used to substitute a
                    missing tile in a pattern line or placed directly
                    on the dome.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from engine.tile import TileColor, NORMAL_COLORS
from engine.dome import DomeTile, DomeSpace, SpaceType


# ---------------------------------------------------------------------------
# Pattern line
# ---------------------------------------------------------------------------

@dataclass
class PatternLine:
    """
    One of the 6 pattern lines on the player board.

    row_index: 0-based (row 0 has capacity 1, row 5 has capacity 6)
    tiles:     the tiles currently sitting on this line (all same color)
    color:     the color locked in for this line (None if empty)
    """
    row_index: int
    tiles:     list[TileColor] = field(default_factory=list)
    color:     Optional[TileColor] = None

    @property
    def capacity(self) -> int:
        return self.row_index + 1

    @property
    def is_complete(self) -> bool:
        return len(self.tiles) == self.capacity

    @property
    def is_empty(self) -> bool:
        return len(self.tiles) == 0

    @property
    def spaces_left(self) -> int:
        return self.capacity - len(self.tiles)

    def can_accept(self, color: TileColor) -> bool:
        """True if this line can accept tiles of the given color."""
        if self.is_complete:
            return False
        if self.color is not None and self.color != color:
            return False
        return True

    def add_tiles(self, tiles: list[TileColor]) -> list[TileColor]:
        """
        Add as many tiles as possible; return the overflow.
        All tiles must be the same color (caller's responsibility).
        """
        assert all(t == tiles[0] for t in tiles), "All tiles must be same color"
        if self.color is None:
            self.color = tiles[0]
        to_place = tiles[: self.spaces_left]
        overflow = tiles[self.spaces_left :]
        self.tiles.extend(to_place)
        return overflow

    def clear(self) -> TileColor:
        """
        Called at round end when the line is complete.
        Clears the line and returns the color that was placed
        (the one tile that moves to the dome).
        The remaining capacity-1 tiles go to the tower (handled by Game).
        """
        assert self.is_complete, "Cannot clear an incomplete pattern line"
        color = self.color
        self.tiles  = []
        self.color  = None
        return color

    def __repr__(self) -> str:
        filled = [c.value for c in self.tiles]
        return (
            f"PatternLine(row={self.row_index}, "
            f"cap={self.capacity}, tiles={filled}, color={self.color})"
        )
        
    def clone(self) -> "PatternLine":
        # Annahme: Deine PatternLine wird mit der Kapazität initialisiert
        new_line = PatternLine(row_index=self.row_index)
        new_line.color = self.color
        new_line.tiles = list(self.tiles) # Flache Kopie der Steine
        return new_line    


# ---------------------------------------------------------------------------
# Dome grid
# ---------------------------------------------------------------------------

@dataclass
class DomeGrid:
    """
    The 6×6 grid built from 9 dome tiles (3×3 arrangement).

    dome_slots: 3×3 array, None = not yet placed
    """
    dome_slots: list[list[Optional[DomeTile]]] = field(
        default_factory=lambda: [[None, None, None] for _ in range(3)]
    )

    # ------------------------------------------------------------------
    # Placement of dome tiles onto the grid
    # ------------------------------------------------------------------

    def place_dome_tile(self, dome_tile: DomeTile, slot_row: int, slot_col: int) -> None:
        """Place a dome tile in the given 3×3 slot (0-indexed)."""
        if not (0 <= slot_row < 3 and 0 <= slot_col < 3):
            raise ValueError(f"Invalid slot ({slot_row}, {slot_col})")
        if self.dome_slots[slot_row][slot_col] is not None:
            raise ValueError(f"Slot ({slot_row}, {slot_col}) is already occupied")
        self.dome_slots[slot_row][slot_col] = dome_tile

    def occupied_slots(self) -> list[tuple[int, int]]:
        return [
            (r, c)
            for r in range(3)
            for c in range(3)
            if self.dome_slots[r][c] is not None
        ]

    def empty_slots(self) -> list[tuple[int, int]]:
        return [
            (r, c)
            for r in range(3)
            for c in range(3)
            if self.dome_slots[r][c] is None
        ]

    # ------------------------------------------------------------------
    # Coordinate mapping: 6×6 cell ↔ dome slot + space index
    # ------------------------------------------------------------------

    @staticmethod
    def cell_to_dome_space(row6: int, col6: int) -> tuple[int, int, int]:
        """
        Map a 6×6 grid cell to (slot_row, slot_col, space_index).
        Space index layout within a dome tile:
            0 1
            2 3
        """
        slot_row   = row6 // 2
        slot_col   = col6 // 2
        local_row  = row6 % 2
        local_col  = col6 % 2
        space_idx  = local_row * 2 + local_col
        return slot_row, slot_col, space_idx

    def get_space(self, row6: int, col6: int) -> Optional[DomeSpace]:
        sr, sc, si = self.cell_to_dome_space(row6, col6)
        dome = self.dome_slots[sr][sc]
        return dome.spaces[si] if dome else None

    # ------------------------------------------------------------------
    # Tile placement on the 6×6 grid
    # ------------------------------------------------------------------

    def place_tile(self, row6: int, col6: int, color: TileColor) -> None:
        """Place a normal (colored) tile on a specific 6×6 cell."""
        space = self.get_space(row6, col6)
        if space is None:
            raise ValueError(f"No dome tile at ({row6}, {col6})")
        if not space.accepts(color):
            raise ValueError(
                f"Space at ({row6}, {col6}) does not accept color {color.value}"
            )
        space.placed_color = color

        # check if special space on that dome tile should be unlocked
        sr, sc, _ = self.cell_to_dome_space(row6, col6)
        dome = self.dome_slots[sr][sc]
        if dome:
            dome.try_unlock_special()

    def place_special_tile(self, row6: int, col6: int) -> int:
        """
        Place a special tile (from the separate reserve) onto an unlocked
        SPECIAL space.  Returns the bonus_points for that dome tile.
        Raises ValueError if the space is not a valid SPECIAL space.
        """
        space = self.get_space(row6, col6)
        if space is None:
            raise ValueError(f"No dome tile at ({row6}, {col6})")
        if not space.accepts_special():
            raise ValueError(f"Space at ({row6}, {col6}) is not an open SPECIAL space.")
        space.place_special_tile()
        sr, sc, _ = self.cell_to_dome_space(row6, col6)
        dome = self.dome_slots[sr][sc]
        return dome.bonus_points if dome else 0

    def valid_special_placements(self) -> list[tuple[int, int]]:
        """Return all 6×6 cells that currently accept a special tile."""
        results = []
        for r in range(6):
            for c in range(6):
                space = self.get_space(r, c)
                if space and space.accepts_special():
                    results.append((r, c))
        return results

    def valid_placements_for(self, color: TileColor) -> list[tuple[int, int]]:
        """
        Return all (row6, col6) cells where `color` can be placed.
        Only considers cells where a dome tile has been placed.
        """
        results = []
        for r in range(6):
            for c in range(6):
                space = self.get_space(r, c)
                if space and space.accepts(color):
                    results.append((r, c))
        return results

    # ------------------------------------------------------------------
    # Row / column completion queries (for end-game scoring)
    # ------------------------------------------------------------------

    def is_row_complete(self, row6: int) -> bool:
        return all(
            (self.get_space(row6, c) is not None and
             self.get_space(row6, c).is_filled)
            for c in range(6)
        )

    def is_col_complete(self, col6: int) -> bool:
        return all(
            (self.get_space(r, col6) is not None and
             self.get_space(r, col6).is_filled)
            for r in range(6)
        )

    def completed_rows(self) -> list[int]:
        return [r for r in range(6) if self.is_row_complete(r)]

    def completed_cols(self) -> list[int]:
        return [c for c in range(6) if self.is_col_complete(c)]

    def __repr__(self) -> str:
        rows = []
        for r in range(6):
            row = []
            for c in range(6):
                space = self.get_space(r, c)
                if space is None:
                    row.append("·")
                elif space.is_filled:
                    row.append(space.placed_color.value[0].upper())
                elif space.space_type == SpaceType.WILD:
                    row.append("W")
                elif space.space_type == SpaceType.SPECIAL:
                    row.append("S" if not space.is_locked else "s")
                else:
                    row.append(space.required_color.value[0].lower())
            rows.append(" ".join(row))
        return "\n".join(rows)

    def clone(self) -> "DomeGrid":
        new_grid = DomeGrid()
        # Kopiert das 3x3 Raster. Wenn ein Slot None ist, bleibt er None.
        # Wenn eine Kachel (DomeTile) drin liegt, wird sie geklont.
        new_grid.dome_slots = [
            [slot.clone() if slot is not None else None for slot in row]
            for row in self.dome_slots
        ]
        return new_grid
# ---------------------------------------------------------------------------
# Player board
# ---------------------------------------------------------------------------

@dataclass
class PlayerBoard:
    """
    The complete state of one player's board.

    player_id:    0 or 1
    name:         display name
    score:        current point total (never goes below 0)
    pattern_lines: 6 PatternLine objects (index 0 = capacity 1)
    dome_grid:    the 6×6 DomeGrid
    broken_tiles: overflow penalty tiles (max 4 kept, rest discarded)
    bonus_chips:  collected bonus chips (stored as TileColor, WILD = joker chip)
    tokens_left:  player tokens remaining this round (starts at 2 each round)
                  used to take dome tiles
    holds_first_player_marker: True if this player will go first next round
    """
    player_id:   int
    name:        str
    score:       int                    = 5
    pattern_lines: list[PatternLine]    = field(default_factory=list)
    dome_grid:   DomeGrid               = field(default_factory=DomeGrid)
    broken_tiles: list[TileColor]       = field(default_factory=list)
    bonus_chips:  list[TileColor]       = field(default_factory=list)
    dome_tiles_placed_this_round: int   = 0   # max 2 per round
    tiled_max_row: int                  = -1  # höchste in dieser Tiling-Phase gelegte Reihe (-1=keine)
    player_tokens_used:          int   = 0   # Spielerplättchen genutzt (max 2, außer Runde 5)
    holds_first_player_marker: bool     = False   # Startspielerstein → -2 Pkt am Rundenende
    first_player_marker_penalty: int    = -2      # dediziertes Straffeld laut Regelwerk
    start_dome_tile: object             = None  # DomeTile | None — zu legen in Runde 1
    bonus_chips_used_this_round: int    = 0     # Aktion D: max 2 pro Runde
    total_floor_penalties: int          = 0 # Zählt alle Boden Strafpunkte für die Arena Auswertung
    floor_penalties_per_round: list      = field(default_factory=list) # Strafpunkte je Runde (Index 0 = Runde 1) für die Arena-Auswertung

    def __post_init__(self):
        if not self.pattern_lines:
            self.pattern_lines = [PatternLine(row_index=i) for i in range(6)]

    # ------------------------------------------------------------------
    # Broken tiles
    # ------------------------------------------------------------------

    MAX_BROKEN = 4
    BROKEN_PENALTIES = [-1, -2, -3, -4]   # Strafpunkte pro Slot (S.9: −1/−2/−3/−4)

    def add_broken(self, tiles: list[TileColor]) -> list[TileColor]:
        """
        Legt Steine auf die Strafleiste (max 4 Slots: −1/−2/−3/−4).
        Gibt überzählige Steine zurück (gehen in den Turm).
        """
        space_left = self.MAX_BROKEN - len(self.broken_tiles)
        self.broken_tiles.extend(tiles[:space_left])
        return tiles[space_left:]   # überzählig → Turm

    def broken_penalty(self) -> int:
        """Strafpunkte für belegte Slots: −1, −2, −3, −4."""
        total = 0
        for i, _ in enumerate(self.broken_tiles):
            total += self.BROKEN_PENALTIES[i]
        return total

    def clear_broken(self) -> list[TileColor]:
        """Remove and return all broken tiles (sent to tower at round end)."""
        tiles = list(self.broken_tiles)
        self.broken_tiles = []
        return tiles

    # ------------------------------------------------------------------
    # Score helpers
    # ------------------------------------------------------------------

    def apply_score(self, delta: int) -> None:
        """Add delta to score, clamping at 0."""
        self.score = max(0, self.score + delta)

    # ------------------------------------------------------------------
    # Dome-Kachel Tracking
    # ------------------------------------------------------------------

    DOME_TILES_PER_ROUND = 2   # jeder Spieler legt 2 Kacheln pro Runde
    MAX_DOME_SLOTS       = 9   # 3×3 Raster

    TOKENS_PER_ROUND = 2   # Außer Runde 5

    def has_used_all_tokens(self, round_number: int) -> bool:
        """True wenn beide Spielerplättchen dieser Runde verbraucht sind."""
        if round_number >= 5:
            return True   # Runde 5: keine Plättchen
        return self.player_tokens_used >= self.TOKENS_PER_ROUND

    def use_player_token(self, round_number: int) -> None:
        """Verbraucht ein Spielerplättchen für die Kuppelplatten-Aktion."""
        if round_number >= 5:
            raise ValueError("In Runde 5 werden keine Spielerplättchen genutzt.")
        if self.player_tokens_used >= self.TOKENS_PER_ROUND:
            raise ValueError(f"{self.name} hat bereits beide Spielerplättchen genutzt.")
        self.player_tokens_used += 1

    def reset_player_tokens(self) -> None:
        self.player_tokens_used = 0

    def has_unplaced_start_tile(self) -> bool:
        """True wenn die Startkachel noch nicht gelegt wurde."""
        return self.start_dome_tile is not None

    def can_place_dome_tile(self, round_number: int) -> bool:
        """
        True wenn der Spieler noch eine Kachel legen kann:
          - In Runde 5 nie
          - Noch nicht 2 Kacheln diese Runde gelegt
          - Raster noch nicht voll (9 Slots)
        Startkachel (Runde 1) zählt als einer der 2 Züge.
        """
        if round_number >= 5:
            return False
        if self.dome_tiles_placed_this_round >= self.DOME_TILES_PER_ROUND:
            return False
        return len(self.dome_grid.occupied_slots()) < self.MAX_DOME_SLOTS

    def register_dome_placement(self) -> None:
        if self.dome_tiles_placed_this_round >= self.DOME_TILES_PER_ROUND:
            raise ValueError(f"{self.name} hat bereits 2 Kacheln diese Runde gelegt.")
        self.dome_tiles_placed_this_round += 1

    BONUS_CHIPS_PER_ROUND = 2

    def can_take_bonus_chip(self) -> bool:
        return self.bonus_chips_used_this_round < self.BONUS_CHIPS_PER_ROUND

    def take_bonus_chip(self, chip) -> None:
        if not self.can_take_bonus_chip():
            raise ValueError(f"{self.name} hat bereits 2 Bonusplättchen diese Runde genommen.")
        self.bonus_chips.append(chip)
        self.bonus_chips_used_this_round += 1

    def reset_dome_placements(self) -> None:
        self.dome_tiles_placed_this_round = 0
        self.player_tokens_used = 0
        self.bonus_chips_used_this_round = 0

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        lines = [f"=== {self.name}  (score: {self.score}) ==="]
        lines.append("Pattern lines:")
        for pl in self.pattern_lines:
            lines.append(f"  {pl}")
        lines.append("Dome grid:")
        for row in repr(self.dome_grid).split("\n"):
            lines.append(f"  {row}")
        lines.append(f"Broken: {[t.value for t in self.broken_tiles]}")
        lines.append(f"Bonus chips: {[t.value for t in self.bonus_chips]}")
        lines.append(f"Tokens used: {self.player_tokens_used}/{self.TOKENS_PER_ROUND}")
        return "\n".join(lines)

    def clone(self) -> "PlayerBoard":
        new_p = PlayerBoard(self.player_id, self.name)
        new_p.score                       = self.score
        new_p.holds_first_player_marker   = self.holds_first_player_marker
        new_p.player_tokens_used          = self.player_tokens_used
        new_p.dome_tiles_placed_this_round = self.dome_tiles_placed_this_round
        new_p.tiled_max_row                = self.tiled_max_row
        new_p.bonus_chips_used_this_round  = self.bonus_chips_used_this_round

        new_p.total_floor_penalties        = self.total_floor_penalties
        new_p.floor_penalties_per_round     = list(self.floor_penalties_per_round)

        # Flache Listenkopien
        new_p.broken_tiles = list(self.broken_tiles)
        new_p.bonus_chips  = list(self.bonus_chips)

        # Komplexe Objekte kaskadierend klonen
        new_p.pattern_lines = [line.clone() for line in self.pattern_lines]
        new_p.dome_grid     = self.dome_grid.clone()

        # Startkuppel kann ein String oder ein DomeTile sein
        if self.start_dome_tile is not None:
            new_p.start_dome_tile = (
                self.start_dome_tile
                if isinstance(self.start_dome_tile, str)
                else self.start_dome_tile.clone()
            )

        return new_p