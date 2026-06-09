"""
Kuppelplättchen-Definitionen für Mosaic-AI.

Jede Kuppelplatte ist eine 2×2-Platte. Die Spieler legen sie auf ihr 6×6-Raster
(3×3-Anordnung von Kuppelplättchen).

Space-Typen laut dome_color.csv:
  - NORMAL(farbe): nur diese Farbe darf hier platziert werden
  - WILD ("bunt"): jede Farbe darf hier platziert werden
  - SPECIAL ("weiß"): wird erst freigeschaltet wenn die anderen 3 Spaces
                      der Kuppel gefüllt sind; nimmt einen weißen Stein
                      aus dem separaten Vorrat auf

Die 18 Kuppeln stammen direkt aus dome_color.csv.
Reihenfolge der 4 Spaces pro Kuppel: [oben-links, oben-rechts, unten-links, unten-rechts]
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from engine.tile import TileColor


class SpaceType(Enum):
    NORMAL  = auto()   # nimmt genau eine Farbe an
    WILD    = auto()   # nimmt jede Farbe an
    SPECIAL = auto()   # weißer Stein, erst nach Unlock verfügbar


@dataclass
class DomeSpace:
    """
    Einer der 4 Spaces auf einer Kuppelplättchen.

    Normal/Wild-Spaces speichern welche TileColor platziert wurde.
    Special-Spaces (weiß) speichern nur ob sie befüllt wurden —
    weiße Steine haben keine Farbe.
    """
    space_type:     SpaceType
    required_color: Optional[TileColor] = None  # nur bei NORMAL gesetzt
    placed_color:   Optional[TileColor] = None  # befüllt bei NORMAL / WILD
    placed_special: bool                = False  # befüllt bei SPECIAL
    is_locked:      bool                = False  # True bei SPECIAL bis Unlock

    @property
    def is_filled(self) -> bool:
        if self.space_type == SpaceType.SPECIAL:
            return self.placed_special
        return self.placed_color is not None

    def accepts(self, color: TileColor) -> bool:
        """Kann dieser Space einen normalen Stein dieser Farbe aufnehmen?"""
        if self.is_filled or self.is_locked:
            return False
        if self.space_type == SpaceType.NORMAL:
            return color == self.required_color
        if self.space_type == SpaceType.WILD:
            return True
        return False  # SPECIAL nur via place_special_tile()

    def accepts_special(self) -> bool:
        """Kann dieser Space einen weißen Stein aufnehmen?"""
        return (
            self.space_type == SpaceType.SPECIAL
            and not self.is_locked
            and not self.placed_special
        )

    def place_special_tile(self) -> None:
        if not self.accepts_special():
            raise ValueError("Dieser Space kann keinen weißen Stein aufnehmen.")
        self.placed_special = True

    def __repr__(self) -> str:
        if self.space_type == SpaceType.NORMAL:
            filled = self.placed_color.value if self.placed_color else "leer"
            return f"Normal({self.required_color.value}, {filled})"
        if self.space_type == SpaceType.WILD:
            filled = self.placed_color.value if self.placed_color else "leer"
            return f"Wild({filled})"
        state = "gefüllt" if self.placed_special else ("offen" if not self.is_locked else "gesperrt")
        return f"Special({state})"
        
    def clone(self) -> "DomeSpace":
        new_space = self.__class__(self.space_type) # Nimmt den Typ (WILD, NORMAL, SPECIAL)
        new_space.placed_color = self.placed_color
        new_space.is_locked = self.is_locked
        new_space.placed_special = getattr(self, 'placed_special', False)
        return new_space    


# Rotations-Mapping: Rotation → neue Reihenfolge der Space-Indizes
# Layout vor Rotation:  [0][1]
#                       [2][3]
# 90° im Uhrzeigersinn: pos0←pos2, pos1←pos0, pos2←pos3, pos3←pos1
ROTATION_MAP: dict[int, list[int]] = {
      0: [0, 1, 2, 3],   # original
     90: [2, 0, 3, 1],   # 90° im Uhrzeigersinn
    180: [3, 2, 1, 0],   # 180°
    270: [1, 3, 0, 2],   # 270° im Uhrzeigersinn
}


@dataclass
class DomeTile:
    """
    Eine 2×2 Kuppelplättchen.

    spaces: 4 DomeSpace-Objekte, Index-Layout:
        [0] [1]   →   oben-links   oben-rechts
        [2] [3]   →   unten-links  unten-rechts

    bonus_points: Zusatzpunkte wenn der SPECIAL-Space befüllt wird
                  (0 wenn kein SPECIAL-Space vorhanden)
    tile_id: 0-basierter Index in der Kuppel-Tabelle (dome_color.csv)
    """
    tile_id:      int
    spaces:       list[DomeSpace]
    bonus_points: int = 0

    def __post_init__(self):
        assert len(self.spaces) == 4, "Eine Kuppelplättchen hat genau 4 Spaces"

    @property
    def is_complete(self) -> bool:
        return all(s.is_filled for s in self.spaces)

    @property
    def special_space(self) -> Optional[DomeSpace]:
        for s in self.spaces:
            if s.space_type == SpaceType.SPECIAL:
                return s
        return None

    def try_unlock_special(self) -> bool:
        """
        Prüft ob der SPECIAL-Space freigeschaltet werden soll
        (sobald die anderen 3 Spaces gefüllt sind).
        Gibt True zurück wenn gerade freigeschaltet wurde.
        """
        sp = self.special_space
        if sp is None or not sp.is_locked:
            return False
        other_filled = all(s.is_filled for s in self.spaces if s is not sp)
        if other_filled:
            sp.is_locked = False
            return True
        return False

    # ------------------------------------------------------------------
    # Rotation
    # ------------------------------------------------------------------

    def rotated_spaces(self, degrees: int) -> list[DomeSpace]:
        """
        Gibt die 4 Spaces in der gedrehten Reihenfolge zurück.
        degrees muss 0, 90, 180 oder 270 sein.
        Ändert die Kuppel selbst NICHT — nur für Vorschau/Validierung.
        """
        if degrees not in ROTATION_MAP:
            raise ValueError(f"Ungültige Rotation: {degrees}. Erlaubt: 0, 90, 180, 270.")
        indices = ROTATION_MAP[degrees]
        return [self.spaces[i] for i in indices]

    def apply_rotation(self, degrees: int) -> None:
        """
        Dreht die Kuppel dauerhaft um degrees Grad.
        Darf nur VOR dem Platzieren auf dem Brett aufgerufen werden.
        """
        if degrees not in ROTATION_MAP:
            raise ValueError(f"Ungültige Rotation: {degrees}. Erlaubt: 0, 90, 180, 270.")
        if degrees == 0:
            return
        if any(s.is_filled for s in self.spaces):
            raise ValueError("Eine bereits befüllte Kuppel kann nicht rotiert werden.")
        self.spaces = self.rotated_spaces(degrees)

    def open_spaces_for(self, color: TileColor) -> list[int]:
        """Indizes der Spaces die diese Farbe aufnehmen können."""
        return [i for i, s in enumerate(self.spaces) if s.accepts(color)]

    def __repr__(self) -> str:
        return (
            f"DomeTile(id={self.tile_id}, "
            f"spaces={self.spaces}, bonus={self.bonus_points})"
        )

    def clone(self) -> "DomeTile":
        # 1. Zuerst die 4 Spaces einzeln klonen
        cloned_spaces = [space.clone() for space in self.spaces]

        # 2. Das neue Tile direkt mit den geklonten Spaces initialisieren
        # (Das verhindert, dass __post_init__ sich über fehlende Spaces beschwert)
        new_tile = DomeTile(
            tile_id=self.tile_id,
            spaces=cloned_spaces
        )
        return new_tile

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _n(color: TileColor) -> DomeSpace:
    """Normal-Space für gegebene Farbe."""
    return DomeSpace(SpaceType.NORMAL, required_color=color)

def _w() -> DomeSpace:
    """Wild-Space (bunt)."""
    return DomeSpace(SpaceType.WILD)

def _s() -> DomeSpace:
    """Special-Space (weiß), startet gesperrt."""
    return DomeSpace(SpaceType.SPECIAL, is_locked=True)


# ---------------------------------------------------------------------------
# Die 18 Kuppelplättchen aus dome_colors.csv
# Reihenfolge der Spalten: oben-links, oben-rechts, unten-links, unten-rechts
# "weiß" → _s()  |  "bunt" → _w()  |  alles andere → _n(farbe)
# ---------------------------------------------------------------------------

def build_dome_tile_pool() -> list[DomeTile]:
    """
    Gibt den vollständigen Pool von 18 Kuppelplättchen zurück.
    Direkt aus dome_colors.csv übernommen.
    """
    B  = TileColor.BLAU
    G  = TileColor.GELB
    R  = TileColor.ROT
    S  = TileColor.SCHWARZ
    T  = TileColor.TUERKIS

    # Jede Zeile: (spaces_liste, bonus_points)
    # bonus_points für Special-Spaces: je nach Schwierigkeit 3-5 Pkt
    # (weiße Spaces = _s(), bunt = _w())
    definitions: list[tuple[list[DomeSpace], int]] = [
        # Zeile  1: gelb    schwarz  türkis  weiß
        ([_n(G), _n(S), _n(T), _s()], 3),
        # Zeile  2: bunt    blau     türkis  schwarz
        ([_w(),  _n(B), _n(T), _n(S)], 0),
        # Zeile  3: türkis  rot      blau    bunt
        ([_n(T), _n(R), _n(B), _w()], 0),
        # Zeile  4: schwarz gelb     rot     bunt
        ([_n(S), _n(G), _n(R), _w()], 0),
        # Zeile  5: schwarz weiß     türkis  rot
        ([_n(S), _s(),  _n(T), _n(R)], 3),
        # Zeile  6: türkis  gelb     bunt    schwarz
        ([_n(T), _n(G), _w(),  _n(S)], 0),
        # Zeile  7: weiß    schwarz  rot     blau
        ([_s(),  _n(S), _n(R), _n(B)], 3),
        # Zeile  8: gelb    blau     schwarz weiß
        ([_n(G), _n(B), _n(S), _s()], 3),
        # Zeile  9: türkis  rot      blau    weiß
        ([_n(T), _n(R), _n(B), _s()], 3),
        # Zeile 10: gelb    rot      bunt    blau
        ([_n(G), _n(R), _w(),  _n(B)], 0),
        # Zeile 11: gelb    weiß     schwarz rot
        ([_n(G), _s(),  _n(S), _n(R)], 3),
        # Zeile 12: türkis  schwarz  rot     bunt
        ([_n(T), _n(S), _n(R), _w()], 0),
        # Zeile 13: blau    schwarz  weiß    türkis
        ([_n(B), _n(S), _s(),  _n(T)], 3),
        # Zeile 14: rot     türkis   gelb    bunt
        ([_n(R), _n(T), _n(G), _w()], 0),
        # Zeile 15: türkis  blau     bunt    gelb
        ([_n(T), _n(B), _w(),  _n(G)], 0),
        # Zeile 16: weiß    türkis   gelb    blau
        ([_s(),  _n(T), _n(G), _n(B)], 3),
        # Zeile 17: rot     bunt     blau    schwarz
        ([_n(R), _w(),  _n(B), _n(S)], 0),
        # Zeile 18: weiß    gelb     blau    rot
        ([_s(),  _n(G), _n(B), _n(R)], 3),
    ]

    return [
        DomeTile(tile_id=i, spaces=spaces, bonus_points=bp)
        for i, (spaces, bp) in enumerate(definitions)
    ]


# ---------------------------------------------------------------------------
# Die 20 Bonusplättchen aus bonus_chips_colors.csv
# Jedes Plättchen hat 1 oder 2 Farbfelder.
# ---------------------------------------------------------------------------

@dataclass
class BonusChip:
    """
    Ein Bonusplättchen.
    colors: 1 oder 2 Farben die dieses Plättchen zeigt.
    chip_id: 0-basierter Index.
    """
    chip_id: int
    colors:  list[TileColor]

    def __repr__(self) -> str:
        return f"BonusChip({[c.value for c in self.colors]})"


def build_bonus_chip_pool() -> list[BonusChip]:
    """
    Gibt alle 20 Bonusplättchen zurück.
    Direkt aus bonus_chips_colors.csv
    """
    B = TileColor.BLAU
    G = TileColor.GELB
    R = TileColor.ROT
    S = TileColor.SCHWARZ
    T = TileColor.TUERKIS

    definitions: list[list[TileColor]] = [
        [B],        # Blau
        [T],        # Türkis
        [T, G],     # Türkis + gelb
        [B, R],     # Blau + rot
        [R],        # Rot
        [R, T],     # rot + türkis
        [S, B],     # schwarz + blau
        [G, S],     # gelb + schwarz
        [B],        # Blau
        [R],        # rot
        [B, R],     # blau + rot
        [S],        # schwarz
        [S, G],     # schwarz + gelb
        [S],        # schwarz
        [R, T],     # rot + türkis
        [B, S],     # Blau + schwarz
        [G],        # gelb
        [T, G],     # Türkis + gelb
        [T],        # Türkis
        [G],        # gelb
    ]

    return [
        BonusChip(chip_id=i, colors=colors)
        for i, colors in enumerate(definitions)
    ]
