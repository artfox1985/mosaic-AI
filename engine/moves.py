"""
Zugdefinitionen für Mosaic-AI.

Ein Zug besteht immer aus zwei Teilen:
  1. TakeAction  — woher und welche Farbe genommen wird
  2. PlaceAction — in welche Musterreihe die Steine gelegt werden

TakeSource-Typen:
  - SMALL_FACTORY_SUN:  von der Sun-Seite einer kleinen Fabrik
  - SMALL_FACTORY_MOON: von der Moon-Seite einer kleinen Fabrik (Top-Stapel)
  - LARGE_FACTORY_SUN:  von der Sun-Seite der großen Fabrik
  - LARGE_FACTORY_MOON: aus dem Moon-Pool der großen Fabrik

Nach dem Nehmen:
  - Small Factory Sun: Spieler legt die übrigen Steine in gewählter
    Reihenfolge auf die Moon-Seite derselben Fabrik.
  - Large Factory Sun: übrige Steine landen im Moon-Pool der großen Fabrik.

Platzierung:
  - Steine kommen auf genau eine Musterreihe (0–5, Index = Zeilennummer).
  - Überschuss (Reihe voll oder Farbe nicht passend) → Strafleiste.
  - Sonderfall: Spieler kann auch direkt auf die Strafleiste legen (row_index = -1).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from engine.tile import TileColor


class TakeSource(Enum):
    SMALL_FACTORY_SUN  = auto()
    SMALL_FACTORY_MOON = auto()
    LARGE_FACTORY_SUN  = auto()
    LARGE_FACTORY_MOON = auto()


@dataclass
class TakeAction:
    """
    Beschreibt woher und welche Farbe ein Spieler nimmt.

    factory_id:    ID der kleinen Fabrik (1–4), None für große Fabrik
    source:        Sun oder Moon, kleine oder große Fabrik
    color:         die genommene Farbe
    moon_order:    nur bei SMALL_FACTORY_SUN — die gewählte Reihenfolge
                   der übrigen Steine die auf Moon gestapelt werden.
                   Muss alle übrigen Steine enthalten (Permutation).
    """
    source:     TakeSource
    color:      TileColor
    factory_id: Optional[int]       = None   # 1–4, None = große Fabrik
    moon_order: list[TileColor]     = field(default_factory=list)

    def __post_init__(self):
        if self.source in (TakeSource.SMALL_FACTORY_SUN, TakeSource.SMALL_FACTORY_MOON):
            assert self.factory_id is not None, \
                "factory_id muss gesetzt sein für kleine Fabriken"
        else:
            assert self.factory_id is None, \
                "factory_id muss None sein für die große Fabrik"


@dataclass
class PlaceAction:
    """
    Beschreibt wohin die genommenen Steine gelegt werden.

    row_index: 0–5 für Musterreihe, -1 für direkt auf Strafleiste
    """
    row_index: int   # 0–5 oder -1 (Strafleiste)

    def __post_init__(self):
        assert -1 <= self.row_index <= 5, \
            f"Ungültiger row_index: {self.row_index}"


@dataclass
class Move:
    """Ein vollständiger Spielzug: Steine nehmen + auf Musterreihe legen."""
    take:  TakeAction
    place: PlaceAction

    def __repr__(self) -> str:
        src = (
            f"Fabrik {self.take.factory_id} "
            f"({'Sun' if self.take.source == TakeSource.SMALL_FACTORY_SUN else 'Moon'})"
            if self.take.factory_id
            else f"Große Fabrik "
                 f"({'Sun' if self.take.source == TakeSource.LARGE_FACTORY_SUN else 'Moon'})"
        )
        dest = (
            f"Musterreihe {self.place.row_index + 1}"
            if self.place.row_index >= 0
            else "Strafleiste"
        )
        return f"Move({src} → {self.take.color.value} → {dest})"


@dataclass
class PlaceDomeTileMove:
    """
    Separater Zug: eine neue Kuppelkachel aus dem gemeinsamen Pool
    auf das eigene 3×3-Raster legen.

    Kann jederzeit während der Drafting-Phase als eigener Zug gespielt
    werden (anstelle eines Stein-Zuges). Jeder Spieler legt 2 Kacheln
    pro Runde (Runde 1: 1 Kachel vorgelegt + 1 weiterer Zug).

    dome_tile_id: ID der gewählten Kachel aus dem gemeinsamen Pool
    slot_row:     Ziel-Slot Zeile im 3×3-Raster (0–2)
    slot_col:     Ziel-Slot Spalte im 3×3-Raster (0–2)
    rotation:     Rotation beim Platzieren (0/90/180/270)
    """
    dome_tile_id: int
    slot_row:     int
    slot_col:     int
    rotation:     int = 0

    def __post_init__(self):
        assert 0 <= self.slot_row <= 2
        assert 0 <= self.slot_col <= 2
        assert self.rotation in (0, 90, 180, 270)

    def __repr__(self) -> str:
        return (
            f"PlaceDomeTile(id={self.dome_tile_id}, "
            f"slot=({self.slot_row},{self.slot_col}), rot={self.rotation}°)"
        )


@dataclass
class DrawFromStackMove:
    """
    [4] Aktion A (Stapel-Variante): Spieler zahlt je 1 Punkt um verdeckt
    vom Stapel zu ziehen. Mehrfach möglich. Erst nach dem Stoppen werden
    die gezogenen Karten aufgedeckt — Spieler wählt 1, Rest geht zurück
    unter den Stapel.

    Dieser Move repräsentiert den gesamten Stapel-Zug:
    num_drawn:    wie viele Karten gezogen wurden (je −1 Pkt)
    chosen_id:    tile_id der gewählten Kachel
    slot_row/col: Ziel-Slot auf der Kuppel
    rotation:     Rotation beim Platzieren
    """
    num_drawn:    int
    chosen_id:    int
    slot_row:     int
    slot_col:     int
    rotation:     int = 0

    def __post_init__(self):
        assert self.num_drawn >= 1
        assert 0 <= self.slot_row <= 2
        assert 0 <= self.slot_col <= 2
        assert self.rotation in (0, 90, 180, 270)

    def __repr__(self) -> str:
        return (
            f"DrawFromStack(gezogen={self.num_drawn}, "
            f"gewählt={self.chosen_id}, "
            f"slot=({self.slot_row},{self.slot_col}), rot={self.rotation}°)"
        )


@dataclass
class TakeBonusChipMove:
    """
    Aktion D: Nimm ein aufgedecktes Bonusplättchen.
    Jede Runde genau 2 Bonusplättchen nehmen.
    chip_id: Index des gewählten aufgedeckten Chips.
    """
    factory_id: int   # ID der kleinen Fabrik (1–4) deren Chip genommen wird

    def __repr__(self) -> str:
        return f"TakeBonusChip(Fabrik {self.factory_id})"


# Union-Typ für alle möglichen Züge
AnyMove = Move | PlaceDomeTileMove | DrawFromStackMove | TakeBonusChipMove
