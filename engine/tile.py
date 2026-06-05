"""
Tile definitions for Mosaic-AI.

Farben laut Setup.xlsx:
  - 5 normale Farben: blau, gelb, rot, schwarz, türkis
  - weiß = Special-Space auf Dome-Kacheln (kein normaler Spielstein)
  - bunt = Wild-Space auf Dome-Kacheln (kein normaler Spielstein)

Steinvorräte:
  Normaler Beutel  — 13 Steine × 5 Farben = 65 Steine
  Special-Vorrat   —  9 weiße Steine (nur für weiße Dome-Spaces)
  Startspielerstein —  1 Stein
  ─────────────────────────────
  Gesamt            75 Steine
"""

from enum import Enum


class TileColor(Enum):
    """
    Die 5 normalen Spielfarben, die aus dem Beutel gezogen werden.
    WILD ist kein physischer Stein — nur ein Dome-Space-Marker.
    """
    BLAU    = "blau"
    GELB    = "gelb"
    ROT     = "rot"
    SCHWARZ = "schwarz"
    TUERKIS = "türkis"

    # Dome-Space-Marker — kein physischer Stein dieser Farbe
    WILD = "bunt"  # "bunt" laut Regelwerk


# Alle 5 ziehbaren Farben (ohne WILD)
NORMAL_COLORS: tuple[TileColor, ...] = (
    TileColor.BLAU,
    TileColor.GELB,
    TileColor.ROT,
    TileColor.SCHWARZ,
    TileColor.TUERKIS,
)

# Steinzahlen
TILES_PER_COLOR      = 13                                     # pro Normalfarbe im Beutel
SPECIAL_TILES        = 9                                      # weiße Steine (separater Vorrat)
FIRST_PLAYER_MARKERS = 1                                      # Startspielerstein
NORMAL_TILES         = TILES_PER_COLOR * len(NORMAL_COLORS)   # 65
TOTAL_TILES          = NORMAL_TILES + SPECIAL_TILES + FIRST_PLAYER_MARKERS  # 75
