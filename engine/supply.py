"""
Beutel und Ablageturm für Mosaic-AI.

Beutel (Bag):
  - Enthält die 65 normalen Spielsteine (13 × 5 Farben)
  - Wird zu Beginn jeder Runde geleert um die Fabriken zu befüllen
  - Wenn der Beutel leer ist, wird der Ablageturm in den Beutel
    zurückgegeben und neu gemischt

Ablageturm (Tower):
  - Nimmt benutzte Steine auf (überschüssige aus Musterreihen + Strafsteine)
  - Wird in den Beutel zurückgegeben sobald dieser erschöpft ist

Special-Vorrat (SpecialSupply):
  - Separater Vorrat mit 9 weißen Steinen
  - Wird nie gemischt oder zurückgelegt — einmal platziert, weg
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field

from engine.tile import TileColor, NORMAL_COLORS, TILES_PER_COLOR, SPECIAL_TILES


@dataclass
class Bag:
    """
    Der Steinbeutel. Enthält normale farbige Steine.
    """
    _tiles: list[TileColor] = field(default_factory=list)

    @classmethod
    def full(cls) -> "Bag":
        """Erstellt einen vollen, gemischten Beutel mit allen 65 Normalsteinen."""
        tiles = [color for color in NORMAL_COLORS for _ in range(TILES_PER_COLOR)]
        random.shuffle(tiles)
        return cls(_tiles=tiles)

    @property
    def count(self) -> int:
        return len(self._tiles)

    @property
    def is_empty(self) -> bool:
        return len(self._tiles) == 0

    def draw(self, n: int) -> list[TileColor]:
        """
        Zieht bis zu n Steine aus dem Beutel.
        Gibt die gezogenen Steine zurück (kann weniger als n sein wenn
        der Beutel nicht genug Steine hat).
        """
        n = min(n, len(self._tiles))
        drawn = self._tiles[:n]
        self._tiles = self._tiles[n:]
        return drawn

    def refill_from_tower(self, tower: "Tower") -> int:
        """
        Füllt den Beutel mit allen Steinen aus dem Ablageturm auf
        und mischt ihn. Gibt die Anzahl zurückgelegter Steine zurück.
        """
        tiles = tower.empty()
        if not tiles:
            return 0
        self._tiles.extend(tiles)
        random.shuffle(self._tiles)
        return len(tiles)

    def color_counts(self) -> dict[TileColor, int]:
        """Gibt die Anzahl je Farbe im Beutel zurück."""
        counts = {c: 0 for c in NORMAL_COLORS}
        for t in self._tiles:
            counts[t] += 1
        return counts

    def __repr__(self) -> str:
        return f"Bag({self.count} Steine: {self.color_counts()})"

    def clone(self) -> "Bag":
        new_bag = Bag()
        # Flache Kopie der internen Liste reicht völlig aus
        new_bag._tiles = list(self._tiles) 
        return new_bag

@dataclass
class Tower:
    """
    Der Ablageturm. Nimmt benutzte Steine auf.
    """
    _tiles: list[TileColor] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self._tiles)

    @property
    def is_empty(self) -> bool:
        return len(self._tiles) == 0

    def add(self, tiles: list[TileColor]) -> None:
        """Legt Steine in den Turm."""
        self._tiles.extend(tiles)

    def empty(self) -> list[TileColor]:
        """Entnimmt alle Steine aus dem Turm (für Beutel-Auffüllung)."""
        tiles = list(self._tiles)
        self._tiles = []
        return tiles

    def color_counts(self) -> dict[TileColor, int]:
        counts = {c: 0 for c in NORMAL_COLORS}
        for t in self._tiles:
            counts[t] += 1
        return counts

    def __repr__(self) -> str:
        return f"Tower({self.count} Steine: {self.color_counts()})"

    def clone(self) -> "Tower":
        new_tower = Tower()
        new_tower._tiles = list(self._tiles)
        return new_tower

@dataclass
class SpecialSupply:
    """
    Der separate Vorrat der 9 weißen Special-Steine.
    Wird nie aufgefüllt — einmal verwendet, dauerhaft weg.
    """
    _remaining: int = SPECIAL_TILES  # 9

    @property
    def count(self) -> int:
        return self._remaining

    @property
    def is_empty(self) -> bool:
        return self._remaining == 0

    def take(self, n: int = 1) -> int:
        """
        Entnimmt n weiße Steine aus dem Vorrat.
        Gibt die tatsächlich entnommene Anzahl zurück.
        Raises ValueError wenn nicht genug vorhanden.
        """
        if n > self._remaining:
            raise ValueError(
                f"Nicht genug weiße Steine: {n} angefordert, "
                f"nur {self._remaining} verfügbar."
            )
        self._remaining -= n
        return n

    def __repr__(self) -> str:
        return f"SpecialSupply({self._remaining} weiße Steine)"

    def clone(self) -> "SpecialSupply":
        new_supply = SpecialSupply()
        new_supply._count = self._remaining
        return new_supply