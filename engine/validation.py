"""
Zugvalidierung für Mosaic-AI.

Prüft ob ein Move regelkonform ist BEVOR er ausgeführt wird.
Gibt bei Fehlern einen beschreibenden String zurück (None = gültig).

Validierungsregeln:
  Take-Validierung:
    - Quelle muss Steine der gewählten Farbe haben
    - Bei SMALL_FACTORY_SUN: moon_order muss alle übrigen Steine enthalten
    - Bei SMALL_FACTORY_MOON: Farbe muss oben auf mindestens einem Stapel liegen

  Place-Validierung:
    - row_index -1 (Strafleiste) ist immer erlaubt
    - Musterreihe darf nicht bereits voll sein
    - Musterreihe darf keine andere Farbe haben
    - Die entsprechende Wand-Position darf in dieser Runde noch nicht
      belegt sein (wird in Schritt 5 Scoring relevant)
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from engine.moves import Move, TakeAction, TakeSource
from engine.tile import TileColor

if TYPE_CHECKING:
    from engine.setup import GameState


def validate_move(state: "GameState", move: Move) -> Optional[str]:
    """
    Prüft ob der Zug für den aktiven Spieler gültig ist.
    Gibt None zurück wenn gültig, sonst eine Fehlermeldung.
    """
    err = _validate_take(state, move.take)
    if err:
        return err
    err = _validate_place(state, move.take.color, move.place.row_index)
    if err:
        return err
    return None


# ---------------------------------------------------------------------------
# Take-Validierung
# ---------------------------------------------------------------------------

def _validate_take(state: "GameState", take: TakeAction) -> Optional[str]:
    src = take.source

    if src == TakeSource.SMALL_FACTORY_SUN:
        return _validate_small_sun(state, take)
    if src == TakeSource.SMALL_FACTORY_MOON:
        return _validate_small_moon(state, take)
    if src == TakeSource.LARGE_FACTORY_SUN:
        return _validate_large_sun(state, take)
    if src == TakeSource.LARGE_FACTORY_MOON:
        return _validate_large_moon(state, take)
    return f"Unbekannte TakeSource: {src}"


def _get_small_factory(state: "GameState", factory_id: int):
    """Gibt die kleine Fabrik mit der ID zurück oder None."""
    for f in state.factories:
        if f.factory_id == factory_id:
            return f
    return None


def _validate_small_sun(state: "GameState", take: TakeAction) -> Optional[str]:
    f = _get_small_factory(state, take.factory_id)
    if f is None:
        return f"Fabrik {take.factory_id} nicht gefunden."
    if f.sun_is_empty:
        return f"Fabrik {take.factory_id}: Sun-Seite ist leer."
    if take.color not in f.sun_colors():
        return (
            f"Fabrik {take.factory_id}: Farbe {take.color.value} nicht "
            f"auf Sun-Seite. Verfügbar: {[c.value for c in f.sun_colors()]}"
        )
    # moon_order muss genau die übrigen Steine enthalten
    remaining = [t for t in f.sun_tiles if t != take.color]
    if sorted(take.moon_order, key=lambda c: c.value) != sorted(remaining, key=lambda c: c.value):
        return (
            f"moon_order {[c.value for c in take.moon_order]} stimmt nicht "
            f"mit übrigen Steinen {[c.value for c in remaining]} überein."
        )
    return None


def _validate_small_moon(state: "GameState", take: TakeAction) -> Optional[str]:
    f = _get_small_factory(state, take.factory_id)
    if f is None:
        return f"Fabrik {take.factory_id} nicht gefunden."
    if f.moon_is_empty:
        return f"Fabrik {take.factory_id}: Moon-Seite ist leer."
    if take.color not in f.moon_top_colors():
        return (
            f"Fabrik {take.factory_id}: Farbe {take.color.value} liegt nicht "
            f"oben auf Moon-Stapeln. Sichtbar: {[c.value for c in f.moon_top_colors()]}"
        )
    return None


def _validate_large_sun(state: "GameState", take: TakeAction) -> Optional[str]:
    lf = state.large_factory
    if lf.sun_is_empty:
        return "Große Fabrik: Sun-Seite ist leer."
    if take.color not in lf.sun_colors():
        return (
            f"Große Fabrik: Farbe {take.color.value} nicht auf Sun-Seite. "
            f"Verfügbar: {[c.value for c in lf.sun_colors()]}"
        )
    return None


def _validate_large_moon(state: "GameState", take: TakeAction) -> Optional[str]:
    lf = state.large_factory
    if lf.moon_is_empty:
        return "Große Fabrik: Moon-Pool ist leer."
    if take.color not in lf.moon_colors():
        return (
            f"Große Fabrik: Farbe {take.color.value} nicht im Moon-Pool. "
            f"Verfügbar: {[c.value for c in lf.moon_colors()]}"
        )
    return None


# ---------------------------------------------------------------------------
# Place-Validierung
# ---------------------------------------------------------------------------

def _validate_place(
    state: "GameState",
    color: TileColor,
    row_index: int,
) -> Optional[str]:
    # Strafleiste ist immer erlaubt
    if row_index == -1:
        return None

    player = state.active_player
    row = player.pattern_lines[row_index]

    if row.is_complete:
        return f"Musterreihe {row_index + 1} ist bereits voll."

    if row.color is not None and row.color != color:
        return (
            f"Musterreihe {row_index + 1} enthält bereits "
            f"{row.color.value} — {color.value} passt nicht."
        )

    return None


# ---------------------------------------------------------------------------
# Hilfsfunktion: alle gültigen Züge generieren
# ---------------------------------------------------------------------------

def generate_valid_moves(state: "GameState") -> list[Move]:
    """
    Optimierte Generierung gültiger Züge. 
    Vermeidet unnötige Permutationen und nutzt direkt Validatoren.
    """
    from engine.moves import PlaceAction, Move
    moves: list[Move] = []
    row_indices = list(range(6)) + [-1]

    # --- Kleine Fabriken (Sun & Moon) ---
    for f in state.factories:
        # Sun: Nur valide Farben, Moon: Nur valide Farben (Top)
        # Für Sun brauchen wir die moon_order nur einmalig, wenn sie valide ist
        for color in f.sun_colors():
            remaining = [t for t in f.sun_tiles if t != color]
            # Statt Permutationen: Nur eine eindeutige Reihenfolge der Reststeine nötig
            # da 'moon_order' nur für die Logik der Verteilung relevant ist
            take = TakeAction(
                source=TakeSource.SMALL_FACTORY_SUN,
                color=color,
                factory_id=f.factory_id,
                moon_order=remaining
            )
            for ri in row_indices:
                if _validate_place(state, color, ri) is None:
                    moves.append(Move(take=take, place=PlaceAction(ri)))

    # --- Große Fabrik ---
    for color in state.large_factory.sun_colors():
        take = TakeAction(source=TakeSource.LARGE_FACTORY_SUN, color=color)
        for ri in row_indices:
            if _validate_place(state, color, ri) is None:
                moves.append(Move(take=take, place=PlaceAction(ri)))

    # --- AKTION C: Globaler Mond-Zug (Aktion C) ---
    # Wir sammeln hier alle Farben, die irgendwo oben auf einem Mondstapel liegen
    available_moon_colors = set()
    
    # Aus den kleinen Fabriken
    for f in state.factories:
        available_moon_colors.update(f.moon_top_colors())
        
    # Aus der großen Fabrik
    available_moon_colors.update(state.large_factory.moon_colors())

    # Jetzt fügen wir diese Züge zur Liste hinzu
    for color in available_moon_colors:
        for ri in row_indices:
            # Erstelle den Move für Aktion C (TakeSource.SMALL_FACTORY_MOON mit factory_id=None)
            take = TakeAction(
                source=TakeSource.SMALL_FACTORY_MOON,
                color=color,
                factory_id=None # Das signalisiert Aktion C
            )
            m = Move(take=take, place=PlaceAction(ri))
            
            # Prüfe, ob dieser globale Mond-Zug valide ist
            if validate_moon_take(state, m) is None:
                moves.append(m)

    return moves

def validate_moon_take(state: "GameState", move: "Move") -> Optional[str]:
    """
    Validiert die Sonderaktion C (Globaler Mond-Zug).
    Prüft, ob die Fliesenfarbe auf den Mondbereichen verfügbar ist und 
    ob sie in die gewählte Musterreihe gelegt werden darf.
    """
    color = move.take.color
    row_index = move.place.row_index

    # 1. Ist die Farbe überhaupt oben auf den Mondbereichen verfügbar?
    available_moon_colors = set()
    for f in state.factories:
        available_moon_colors.update(f.moon_top_colors())
    available_moon_colors.update(state.large_factory.moon_colors())

    if color not in available_moon_colors:
        return f"Aktion C ungültig: Keine {color.value}-Fliesen liegen oben auf den Mondbereichen."

    # 2. Darf der Spieler diese Steine legal ablegen?
    # (Wir nutzen hier deine existierende Platzierungs-Prüfung)
    err = _validate_place(state, color, row_index)
    if err:
        return err

    return None