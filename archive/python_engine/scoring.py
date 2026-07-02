"""
Wertungsplatten (H)

8 verschiedene Wertungskriterien. Spieler 1 wählt zu Spielbeginn 3 davon.
Punkte werden am Spielende nach der Tiling-Phase der 5. Runde vergeben.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.board import PlayerBoard


@dataclass(frozen=True)
class ScoringTile:
    id:          int
    name:        str
    description: str
    emoji:       str

    def score(self, player: "PlayerBoard") -> int:
        raise NotImplementedError


# ── 1. Horizontale Reihen ────────────────────────────────────────────────────
class HorizontalRows(ScoringTile):
    """3 Punkte für jede vollständige horizontale Reihe (6 Fliesen)."""
    def score(self, player):
        grid = _build_grid(player)
        pts = 0
        for r in range(6):
            if all(grid[r][c] for c in range(6)):
                pts += 3
        return pts


# ── 2. Vertikale Reihen ──────────────────────────────────────────────────────
class VerticalRows(ScoringTile):
    """7 Punkte für jede vollständige vertikale Reihe (6 Fliesen)."""
    def score(self, player):
        grid = _build_grid(player)
        pts = 0
        for c in range(6):
            if all(grid[r][c] for r in range(6)):
                pts += 7
        return pts


# ── 3. Diagonale Reihen ──────────────────────────────────────────────────────
class DiagonalRows(ScoringTile):
    """10 Punkte für jede vollständige Diagonale (6 Fliesen, nur 2 möglich)."""
    def score(self, player):
        grid = _build_grid(player)
        pts = 0
        if all(grid[i][i] for i in range(6)):
            pts += 10
        if all(grid[i][5-i] for i in range(6)):
            pts += 10
        return pts


# ── 4. Mehrfarbige Felder ────────────────────────────────────────────────────
class WildFields(ScoringTile):
    """
    2 Punkte je mehrfarbiges Feld wenn ALLE mehrfarbigen Felder belegt.
    Sonst 0 Punkte.
    """
    def score(self, player):
        wild_spaces = _get_wild_spaces(player)
        if not wild_spaces:
            return 0
        if all(sp.is_filled for sp in wild_spaces):
            return 2 * len(wild_spaces)
        return 0


# ── 5. Äußere Felder ─────────────────────────────────────────────────────────
class OuterFields(ScoringTile):
    """1 Punkt für jede Fliese auf den äußeren Kuppelplattenfeldern."""
    def score(self, player):
        # Äußere Felder: Reihe 0, Reihe 5, Spalte 0, Spalte 5 im 6x6-Raster
        grid = _build_grid(player)
        pts = 0
        outer = set()
        for c in range(6):
            outer.add((0, c))
            outer.add((5, c))
        for r in range(1, 5):
            outer.add((r, 0))
            outer.add((r, 5))
        for (r, c) in outer:
            if grid[r][c]:
                pts += 1
        return pts


# ── 6. Eckkuppelplatten ──────────────────────────────────────────────────────
class CornerTiles(ScoringTile):
    """
    3 Punkte für jede vollständig gefüllte obere Eckplatte.
    8 Punkte für jede vollständig gefüllte untere Eckplatte.
    Vollständig bedeutet: Alle 4 Felder (Spaces) der Platte sind belegt.
    """
    def score(self, player):
        pts = 0
        
        # --- OBERE ECKEN (Je 3 Punkte) ---
        top_corners = [(0, 0), (0, 2)]
        for sr, sc in top_corners:
            slot = player.dome_grid.dome_slots[sr][sc]
            if slot is not None:
                filled = sum(1 for sp in slot.spaces if sp.is_filled)
                if filled == 4:
                    pts += 3
                    
        # --- UNTERE ECKEN (Je 8 Punkte) ---
        bottom_corners = [(2, 0), (2, 2)]
        for sr, sc in bottom_corners:
            slot = player.dome_grid.dome_slots[sr][sc]
            if slot is not None:
                filled = sum(1 for sp in slot.spaces if sp.is_filled)
                if filled == 4:
                    pts += 8
                    
        return pts


# ── 7. Leere Spezialfelder (Straf-Wertung) ──────────────────────────────────
class EmptySpecialFields(ScoringTile):
    """−3 Punkte für jedes leere Spezialfliesenfeld in der Kuppel."""
    def score(self, player):
        special_spaces = _get_special_spaces(player)
        empty = sum(1 for sp in special_spaces if not sp.is_filled)
        return -3 * empty


# ── 8. Farbenreiche Reihen ───────────────────────────────────────────────────
class ColorfulRows(ScoringTile):
    """
    4 Punkte für jede horizontale Reihe mit mindestens 5 verschiedenfarbigen
    Fliesen (kann 1 Spezialfliese und/oder Lücke enthalten).
    """
    def score(self, player):
        pts = 0
        for r in range(6):
            colors = _get_row_colors(player, r)
            # Zähle einzigartige Farben (exkl. Spezialfliesen/Lücken)
            unique = len(set(c for c in colors if c is not None and c != 'special'))
            if unique >= 5:
                pts += 4
        return pts


# ── Alle 8 Wertungsplatten ───────────────────────────────────────────────────
ALL_SCORING_TILES: list[ScoringTile] = [
    HorizontalRows(0,  "Horizontale Reihen",  "3 Pkt je vollständige horizontale Reihe (6 Fliesen)", "↔️"),
    VerticalRows(1,    "Vertikale Reihen",    "7 Pkt je vollständige vertikale Reihe (6 Fliesen)",   "↕️"),
    DiagonalRows(2,    "Diagonale Reihen",    "10 Pkt je vollständige Diagonale (max. 2×)",           "↗️"),
    WildFields(3,      "Mehrfarbige Felder",  "2 Pkt je Wildcard-Feld wenn ALLE belegt",              "🌈"),
    OuterFields(4,     "Äußere Felder",       "1 Pkt je Fliese auf dem Rand der Kuppel",             "⬜"),
    CornerTiles(5,     "Eckplatten",          "3/8 Pkt je Eckkuppelplatte (obere/untere)",          "🔲"),
    EmptySpecialFields(6, "Spezialfelder",    "−3 Pkt je leeres Spezialfliesenfeld",                 "⭐"),
    ColorfulRows(7,    "Farbenreiche Reihen", "4 Pkt je Reihe mit ≥5 verschiedenen Farben",          "🎨"),
]

# Sich gegenseitig ausschließende Wertungsplatten-Paare (Regel).
# Aus jedem Paar darf höchstens EINE Platte gewählt werden.
MUTUALLY_EXCLUSIVE_PAIRS: list[tuple[int, int]] = [
    (0, 7),   # Horizontale Reihen  ⟷ Farbenreiche Reihen
    (6, 3),   # Spezialfelder       ⟷ Mehrfarbige Felder
    (4, 1),   # Äußere Felder       ⟷ Vertikale Reihen
    (2, 5),   # Diagonale Reihen    ⟷ Eckplatten
]

def _exclusion_partner(tile_id: int) -> int | None:
    """Gibt die ID der ausschließenden Partnerplatte zurück, falls vorhanden."""
    for a, b in MUTUALLY_EXCLUSIVE_PAIRS:
        if tile_id == a:
            return b
        if tile_id == b:
            return a
    return None

def has_exclusion_conflict(tile_ids: list[int]) -> bool:
    """True, wenn zwei IDs aus demselben Ausschluss-Paar gewählt wurden."""
    s = set(tile_ids)
    for a, b in MUTUALLY_EXCLUSIVE_PAIRS:
        if a in s and b in s:
            return True
    return False

def sample_valid_scoring_ids(n: int = 3, rng=None) -> list[int]:
    """
    Wählt n Wertungsplatten zufällig, ohne zwei aus demselben Ausschluss-Paar.
    Vorgehen: höchstens eine Platte pro Paar in den Pool nehmen, dann ziehen.
    """
    import random as _random
    r = rng or _random
    chosen = []
    # Aus jedem Paar genau eine Seite als Kandidat zulassen
    pool = []
    for a, b in MUTUALLY_EXCLUSIVE_PAIRS:
        pool.append(r.choice([a, b]))
    # Falls Platten ohne Paar existieren, ebenfalls aufnehmen
    paired = {x for pair in MUTUALLY_EXCLUSIVE_PAIRS for x in pair}
    for t in ALL_SCORING_TILES:
        if t.id not in paired:
            pool.append(t.id)
    return r.sample(pool, min(n, len(pool)))


def calculate_end_scoring(player: "PlayerBoard", tile_ids: list[int]) -> dict:
    """
    Berechnet die Endwertung für einen Spieler basierend auf den gewählten
    3 Wertungsplatten. Gibt Dict mit Details zurück.
    """
    results = {}
    total = 0
    for tid in tile_ids:
        tile = next((t for t in ALL_SCORING_TILES if t.id == tid), None)
        if tile is None:
            continue
        pts = tile.score(player)
        results[str(tid)] = {       # String-Key für JSON-Kompatibilität
            "name":  tile.name,
            "emoji": tile.emoji,
            "desc":  tile.description,
            "score": pts,
        }
        total += pts
    results["total"] = total
    return results


# ── Hilfsfunktionen ──────────────────────────────────────────────────────────

def _build_grid(player: "PlayerBoard") -> list[list[bool]]:
    """Baut ein 6×6 Bool-Raster aus der Kuppel (True = Fliese vorhanden)."""
    grid = [[False]*6 for _ in range(6)]
    for sr in range(3):
        for sc in range(3):
            slot = player.dome_grid.dome_slots[sr][sc]
            if slot is None:
                continue
            for si, sp in enumerate(slot.spaces):
                r = sr*2 + si//2
                c = sc*2 + si%2
                if sp.is_filled:
                    grid[r][c] = True
    return grid


def _get_wild_spaces(player: "PlayerBoard"):
    """Gibt alle WILD-Spaces zurück."""
    from engine.dome import SpaceType
    spaces = []
    for sr in range(3):
        for sc in range(3):
            slot = player.dome_grid.dome_slots[sr][sc]
            if slot:
                spaces.extend(sp for sp in slot.spaces if sp.space_type == SpaceType.WILD)
    return spaces


def _get_special_spaces(player: "PlayerBoard"):
    """Gibt alle SPECIAL-Spaces zurück."""
    from engine.dome import SpaceType
    spaces = []
    for sr in range(3):
        for sc in range(3):
            slot = player.dome_grid.dome_slots[sr][sc]
            if slot:
                spaces.extend(sp for sp in slot.spaces if sp.space_type == SpaceType.SPECIAL)
    return spaces


def _get_row_colors(player: "PlayerBoard", row6: int) -> list:
    """Gibt die Farben einer horizontalen 6×6-Reihe zurück."""
    colors = []
    sr = row6 // 2
    si_row = row6 % 2  # 0 = obere Spaces (0,1), 1 = untere Spaces (2,3)
    for sc in range(3):
        slot = player.dome_grid.dome_slots[sr][sc]
        if slot is None:
            colors.extend([None, None])
            continue
        for si_col in range(2):
            si = si_row*2 + si_col
            sp = slot.spaces[si]
            if sp.placed_special:
                colors.append('special')
            elif sp.placed_color:
                colors.append(sp.placed_color.value)
            else:
                colors.append(None)
    return colors