"""
Zugausführung für Mosaic-AI.

Führt einen bereits validierten Move auf dem GameState aus.
Reihenfolge:
  1. Steine nehmen (Take) — Fabrik aktualisieren, Marker vergeben
  2. Steine legen (Place) — Musterreihe befüllen, Überschuss → Strafleiste
  3. Startspieler-Marker verarbeiten
  4. Bonus-Chip aufdecken falls Fabrik jetzt leer

WICHTIG: execute_move() geht davon aus dass der Move bereits validiert
wurde. Ungültige Züge führen zu undefiniertem Verhalten.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from engine.moves import Move, TakeSource
from engine.tile import TileColor

if TYPE_CHECKING:
    from engine.setup import GameState


def execute_move(state: "GameState", move: Move) -> None:
    """
    Führt einen validierten Zug aus und aktualisiert den GameState.
    """
    is_global_moon_take = (
        move.take.source.name == "SMALL_FACTORY_MOON" and 
        move.take.factory_id is None
    )
    
    if is_global_moon_take:
        _execute_moon_take(state, move.take.color, move.place.row_index)
        return  # Fertig! Der Rest von execute_move wird übersprungen.
    
    # 1. Steine nehmen
    tiles, got_marker = _execute_take(state, move)

    # 2. Startspieler-Marker
    if got_marker:
        _apply_first_player_marker(state)

    # 3. Steine auf Musterreihe oder Strafleiste legen
    _execute_place(state, tiles, move.take.color, move.place.row_index)

    # 4. Logging
    player = state.active_player
    color = move.take.color
    dest = f"Reihe {move.place.row_index+1}" if move.place.row_index >= 0 else "Strafleiste"
    src_map = {
        "SMALL_FACTORY_SUN":  f"Fabrik {move.take.factory_id} Sonne",
        "SMALL_FACTORY_MOON": f"Fabrik {move.take.factory_id} Mond",
        "LARGE_FACTORY_SUN":  "Große Fabrik Sonne",
        "LARGE_FACTORY_MOON": "Große Fabrik Mond",
    }
    src_str = src_map.get(move.take.source.name, str(move.take.source))
    row = player.pattern_lines[move.place.row_index] if move.place.row_index >= 0 else None
    filled = f"{len(row.tiles)}/{row.capacity}" if row else ""
    state.log_event(
        f"☀️  {player.name}: {len(tiles)}× {color.value} "
        f"von {src_str} → {dest} {filled}"
    )

def _execute_moon_take(state, color, row_index: int) -> None:
    """
    Sonderaktion (Aktion C): Nimmt alle obersten Fliesen der gewählten Farbe
    vom Mondbereich ALLER Manufakturen (klein + groß) gleichzeitig.
    """
    p = state.active_player
    taken = []

    # 1. Kleine Fabriken abräumen
    for f in state.factories:
        if color in f.moon_top_colors():
            taken += f.take_from_moon(color)
            # Bonus-Chip Logik
            if f.is_fully_empty and f.bonus_chip and not f.bonus_chip_revealed:
                f.bonus_chip_revealed = True
                state.log_event(f"Fabrik {f.factory_id}: Bonus-Chip aufgedeckt!")

    # 2. Große Manufaktur (Moon) abräumen
    got_marker = False
    if color in state.large_factory.moon_colors():
        tiles, got_marker = state.large_factory.take_from_moon(color)
        taken += tiles

    # 3. Sicherheitscheck
    if not taken:
        raise ValueError(f"Keine {color.value}-Fliesen oben auf Moon-Seiten gefunden.")

    # 4. Startspieler-Marker vergeben
    if got_marker:
        _apply_first_player_marker(state)

    # 5. Steine auf die Musterreihe legen
    # (Ich nehme an, _execute_place ist ebenfalls in execution.py)
    _execute_place(state, taken, color, row_index)

    state.log_event(f"🌙 {p.name}: Mond-Aktion — {len(taken)}× {color.value} genommen.")

# ---------------------------------------------------------------------------
# Take
# ---------------------------------------------------------------------------

def _execute_take(state: "GameState", move: Move) -> tuple[list[TileColor], bool]:
    """
    Führt den Take-Teil aus.
    Gibt (genommene_steine, hat_marker_bekommen) zurück.
    """
    src = move.take.source
    color = move.take.color

    if src == TakeSource.SMALL_FACTORY_SUN:
        return _take_small_sun(state, move)

    if src == TakeSource.SMALL_FACTORY_MOON:
        return _take_small_moon(state, move)

    if src == TakeSource.LARGE_FACTORY_SUN:
        return _take_large_sun(state, move)

    if src == TakeSource.LARGE_FACTORY_MOON:
        return _take_large_moon(state, move)

    raise ValueError(f"Unbekannte TakeSource: {src}")


def _take_small_sun(state: "GameState", move: Move) -> tuple[list[TileColor], bool]:
    f = _get_factory(state, move.take.factory_id)
    taken, remaining = f.take_from_sun(move.take.color)

    # Spieler legt übrige Steine in gewählter Reihenfolge auf Moon
    if remaining:
        f.place_on_moon(move.take.moon_order)

    # Bonus-Chip aufdecken wenn Fabrik jetzt komplett leer
    if f.is_fully_empty and f.bonus_chip and not f.bonus_chip_revealed:
        f.bonus_chip_revealed = True
        state.log_event(
            f"Fabrik {f.factory_id}: Bonus-Chip aufgedeckt → {f.bonus_chip}"
        )

    return taken, False   # kleine Fabrik hat keinen Startspieler-Marker


def _take_small_moon(state: "GameState", move: Move) -> tuple[list[TileColor], bool]:
    f = _get_factory(state, move.take.factory_id)
    taken = f.take_from_moon(move.take.color)

    # Bonus-Chip aufdecken wenn Fabrik jetzt komplett leer
    if f.is_fully_empty and f.bonus_chip and not f.bonus_chip_revealed:
        f.bonus_chip_revealed = True
        state.log_event(
            f"Fabrik {f.factory_id}: Bonus-Chip aufgedeckt → {f.bonus_chip}"
        )

    return taken, False


def _take_large_sun(state: "GameState", move: Move) -> tuple[list[TileColor], bool]:
    lf = state.large_factory
    taken, remaining, got_marker = lf.take_from_sun(move.take.color)

    # Übrige Steine landen im Moon-Pool der großen Fabrik
    if remaining:
        lf.add_to_moon(remaining)

    return taken, got_marker


def _take_large_moon(state: "GameState", move: Move) -> tuple[list[TileColor], bool]:
    lf = state.large_factory
    taken, got_marker = lf.take_from_moon(move.take.color)
    return taken, got_marker


# ---------------------------------------------------------------------------
# Startspieler-Marker
# ---------------------------------------------------------------------------

def _apply_first_player_marker(state: "GameState") -> None:
    """
    Vergibt den Startspieler-Marker an den aktiven Spieler.
    Laut Regelwerk S.5: dediziertes −2-Feld, NICHT auf der Strafleiste.
    Die −2 Punkte werden am Rundenende via score_penalty() abgezogen.
    """
    player = state.active_player
    player.holds_first_player_marker = True
    state.first_player_next_round = state.current_player
    state.log_event(
        f"🏁 {player.name}: Startspielerstein genommen (−2 Pkt am Rundenende → aktuell {player.score} Pkt)"
    )


# ---------------------------------------------------------------------------
# Place
# ---------------------------------------------------------------------------

def _execute_place(
    state: "GameState",
    tiles: list[TileColor],
    color: TileColor,
    row_index: int,
) -> None:
    """
    Legt die Steine auf die Musterreihe oder Strafleiste.
    Überschuss geht auf die Strafleiste, der Rest vom Überschuss in den Turm.
    """
    player = state.active_player

    if row_index == -1:
        # Direkt auf Strafleiste
        _add_to_penalty(state, tiles)
        return

    row = player.pattern_lines[row_index]
    overflow = row.add_tiles(tiles)

    if overflow:
        _add_to_penalty(state, overflow)


def _add_to_penalty(
    state: "GameState",
    tiles: list[TileColor],
) -> None:
    """
    Legt Steine auf die Strafleiste des aktiven Spielers.
    Steine die nicht mehr drauf passen (max 4) gehen in den Turm.
    """
    player = state.active_player
    before = len(player.broken_tiles)
    to_tower = player.add_broken(tiles)
    after = len(player.broken_tiles)
    if after > before:
        pen_vals = [-1,-2,-3,-4]
        new_slots = [pen_vals[i] for i in range(before, after)]
        state.log_event(
            f"⚠️  {player.name}: {len(tiles)}× auf Strafleiste "
            f"(Slots {before+1}–{after}, {sum(new_slots)} Pkt Strafe)"
        )
    if to_tower:
        state.tower.add(to_tower)
        state.log_event(
            f"⚠️  {player.name}: {len(to_tower)} Stein(e) → Turm (Strafleiste voll)"
        )


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _get_factory(state: "GameState", factory_id: int):
    for f in state.factories:
        if f.factory_id == factory_id:
            return f
    raise ValueError(f"Fabrik {factory_id} nicht gefunden.")
