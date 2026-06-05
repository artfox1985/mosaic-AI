"""
Factory definitions for Mosaic-AI.

Mosaic-AI hat:
  - 4 kleine Fabriken (je 4 Steine auf der Sun-Seite)
  - 1 große Fabrik   (5 Steine auf der Sun-Seite + Moon-Pool für Reste)

Sun-Mechanik (kleine & große Fabrik):
  Spieler nimmt ALLE Steine einer Farbe von der Sun-Seite.
  Die restlichen Steine legt er in gewählter Reihenfolge auf die Moon-Seite.

Moon-Mechanik (nur kleine Fabriken):
  Spieler nimmt alle TOP-Steine einer Farbe von den Moon-Stapeln.

Moon-Pool (große Fabrik):
  Flacher Pool für Steine die direkt in der großen Fabrik übrig bleiben
  (nach Sun-Entnahme). Steine kleiner Fabriken bleiben auf deren eigenen
  Moon-Stapeln — sie wandern NICHT in den Moon-Pool der großen Fabrik.
  Spieler nimmt alle Steine einer Farbe aus dem Pool.

Der Startspieler-Marker liegt bei der großen Fabrik.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from engine.tile import TileColor
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from engine.dome import BonusChip


@dataclass
class Factory:
    """Eine kleine Fabrik."""
    factory_id:           int
    sun_tiles:            list[TileColor]        = field(default_factory=list)
    moon_stacks:          list[list[TileColor]]  = field(default_factory=list)
    bonus_chip:           Optional[object]       = None   # BonusChip | None (verdeckt)
    bonus_chip_revealed:  bool                   = False  # True sobald Fabrik leer

    # ------------------------------------------------------------------
    # Sun-Seite
    # ------------------------------------------------------------------

    @property
    def sun_is_empty(self) -> bool:
        return len(self.sun_tiles) == 0

    def sun_colors(self) -> set[TileColor]:
        return set(self.sun_tiles)

    def take_from_sun(self, color: TileColor) -> tuple[list[TileColor], list[TileColor]]:
        """
        Nimmt alle Steine der gewählten Farbe von der Sun-Seite.
        Gibt (genommene, übrige) zurück — übrige müssen auf Moon gelegt werden.
        """
        if color not in self.sun_colors():
            raise ValueError(
                f"Farbe {color.value} nicht auf Sun-Seite von Fabrik {self.factory_id}."
            )
        taken     = [t for t in self.sun_tiles if t == color]
        remaining = [t for t in self.sun_tiles if t != color]
        self.sun_tiles = []
        return taken, remaining

    def place_on_moon(self, ordered_tiles: list[TileColor]) -> None:
        """
        Legt alle verbleibenden Fliesen als EINEN Stapel auf die Moon-Seite.
        ordered_tiles: Reihenfolge vom Spieler gewählt — Index 0 = unten, letzter = oben (sichtbar).
        """
        if ordered_tiles:
            self.moon_stacks.append(list(ordered_tiles))

    # ------------------------------------------------------------------
    # Moon-Seite
    # ------------------------------------------------------------------

    @property
    def moon_is_empty(self) -> bool:
        return len(self.moon_stacks) == 0

    def moon_top_colors(self) -> set[TileColor]:
        return {stack[-1] for stack in self.moon_stacks if stack}

    def take_from_moon(self, color: TileColor) -> list[TileColor]:
        """
        Nimmt alle TOP-Steine der gewählten Farbe von den Moon-Stapeln.
        """
        if color not in self.moon_top_colors():
            raise ValueError(
                f"Farbe {color.value} nicht oben auf Moon-Stapeln von Fabrik {self.factory_id}."
            )
        taken = []
        surviving = []
        for stack in self.moon_stacks:
            if stack and stack[-1] == color:
                taken.append(stack.pop())
                if stack:
                    surviving.append(stack)
            else:
                surviving.append(stack)
        self.moon_stacks = surviving

        if self.sun_is_empty and self.moon_is_empty:
            self.bonus_chip_revealed = True

        return taken

    @property
    def is_fully_empty(self) -> bool:
        return self.sun_is_empty and self.moon_is_empty

    def __repr__(self) -> str:
        sun  = [c.value for c in self.sun_tiles]
        moon = [[c.value for c in s] for s in self.moon_stacks]
        chip = repr(self.bonus_chip) if self.bonus_chip_revealed and self.bonus_chip else ("[verdeckt]" if self.bonus_chip else "kein")
        return (
            f"Factory(id={self.factory_id}, sun={sun}, moon={moon}, "
            f"bonus={chip})"
        )


@dataclass
class LargeFactory:
    """
    Die große Fabrik (zentrales Display).

    Sun-Seite:  5 Steine zu Rundenbeginn, offen ausgelegt.
    Moon-Pool:  flacher Pool, Reste von kleinen Fabriken landen hier.

    Der Startspieler-Marker liegt hier. Wer Steine nimmt während
    has_first_player_marker=True ist, erhält den Marker.
    """
    sun_tiles:               list[TileColor] = field(default_factory=list)
    moon_pool:               list[TileColor] = field(default_factory=list)
    has_first_player_marker: bool            = True

    # ------------------------------------------------------------------
    # Sun-Seite
    # ------------------------------------------------------------------

    @property
    def sun_is_empty(self) -> bool:
        return len(self.sun_tiles) == 0

    def sun_colors(self) -> set[TileColor]:
        return set(self.sun_tiles)

    def take_from_sun(self, color: TileColor) -> tuple[list[TileColor], list[TileColor], bool]:
        """
        Nimmt alle Steine einer Farbe von der Sun-Seite.
        Gibt (genommene, übrige, hatte_marker) zurück.
        Übrige wandern in den Moon-Pool (Aufgabe des Aufrufers).
        """
        if color not in self.sun_colors():
            raise ValueError(f"Farbe {color.value} nicht auf Sun-Seite der großen Fabrik.")
        taken     = [t for t in self.sun_tiles if t == color]
        remaining = [t for t in self.sun_tiles if t != color]
        self.sun_tiles = []
        marker = self.has_first_player_marker
        self.has_first_player_marker = False
        return taken, remaining, marker

    # ------------------------------------------------------------------
    # Moon-Pool
    # ------------------------------------------------------------------

    @property
    def moon_is_empty(self) -> bool:
        return len(self.moon_pool) == 0

    def moon_colors(self) -> set[TileColor]:
        return set(self.moon_pool)

    def take_from_moon(self, color: TileColor) -> tuple[list[TileColor], bool]:
        """
        Nimmt alle Steine einer Farbe aus dem Moon-Pool.
        Gibt (genommene, hatte_marker) zurück.
        """
        if color not in self.moon_colors():
            raise ValueError(f"Farbe {color.value} nicht im Moon-Pool der großen Fabrik.")
        taken = [t for t in self.moon_pool if t == color]
        self.moon_pool = [t for t in self.moon_pool if t != color]
        marker = self.has_first_player_marker
        self.has_first_player_marker = False
        return taken, marker

    def add_to_moon(self, tiles: list[TileColor]) -> None:
        """Fügt Steine zum Moon-Pool hinzu (Reste von kleinen Fabriken)."""
        self.moon_pool.extend(tiles)

    # ------------------------------------------------------------------
    # Allgemein
    # ------------------------------------------------------------------

    @property
    def is_empty(self) -> bool:
        return self.sun_is_empty and self.moon_is_empty and not self.has_first_player_marker

    def reset_for_new_round(self) -> None:
        self.sun_tiles = []
        self.moon_pool = []
        self.has_first_player_marker = True

    def __repr__(self) -> str:
        sun  = [c.value for c in self.sun_tiles]
        moon = [c.value for c in self.moon_pool]
        marker = " ★" if self.has_first_player_marker else ""
        return f"LargeFactory(sun={sun}, moon={moon}{marker})"
