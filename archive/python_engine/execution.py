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
    take_result = _execute_take(state, move)
    if len(take_result) == 4:
        tiles, got_marker, moon_log, chip_log = take_result
    else:
        tiles, got_marker = take_result
        moon_log, chip_log = None, None

    # 2. Startspieler-Marker
    if got_marker:
        _apply_first_player_marker(state)

    # 3. Logging VOR _execute_place — damit Aktions-Log vor Strafleisten-Warnung erscheint
    player = state.active_player
    color = move.take.color
    dest = f"Reihe {move.place.row_index+1}" if move.place.row_index >= 0 else "Strafleiste"
    src_map = {
        "SMALL_FACTORY_SUN": f"F{move.take.factory_id}",
        "LARGE_FACTORY_SUN": "GF",
    }
    src_str = src_map.get(move.take.source.name, str(move.take.source))
    # 4. Aktions-Log + Place + Mondstapel/Chip-Logs
    ri = move.place.row_index
    # Aktions-Log VOR place — Index merken um Füllstand später einzufügen
    state.log_event(
        f"☀️  {player.name}: {len(tiles)}× {color.value} "
        f"von {src_str} → {dest}"
    )
    action_log_idx = len(state.log) - 1
    _execute_place(state, tiles, move.take.color, ri)

    # Füllstand direkt in den Aktions-Log-Eintrag einbauen (nur bei Musterreihe)
    if ri >= 0:
        row = player.pattern_lines[ri]
        state.log[action_log_idx] += f" [{len(row.tiles)}/{row.capacity}]"

    # 5. Mondstapel-Log und Chip-Aufdeckung
    if moon_log:
        state.log_event(moon_log)
    if chip_log:
        state.log_event(chip_log)

def _execute_moon_take(state, color, row_index: int) -> None:
    """
    Sonderaktion (Aktion C): Nimmt alle obersten Fliesen der gewählten Farbe
    vom Mondbereich ALLER Manufakturen (klein + groß) gleichzeitig.
    """
    p = state.active_player
    taken = []

    # 1. Kleine Fabriken abräumen — pro Fabrik tracken
    sources = []  # [(label, count), ...]
    pending_logs = []  # Mond-Stapel und Chip-Logs — erst nach Aktions-Log schreiben
    for f in state.factories:
        if color in f.moon_top_colors():
            tiles_from_f = f.take_from_moon(color)
            if tiles_from_f:
                taken += tiles_from_f
                sources.append((f"F{f.factory_id}", len(tiles_from_f)))
            # Mondstapel nach Entnahme sammeln — auch wenn leer
            stack_str = _format_moon_stacks(f) if f.moon_stacks else "leer"
            pending_logs.append(
                f"🌙 F{f.factory_id} Mond-Stapel: {stack_str}"
            )
            # Bonus-Chip aufdecken wenn Fabrik jetzt komplett leer
            if f.is_fully_empty and f.bonus_chip and not f.bonus_chip_revealed:
                f.bonus_chip_revealed = True
                pending_logs.append(f"🎴 F{f.factory_id}: Bonusplättchen aufgedeckt!")

    # 2. Große Manufaktur (Moon) abräumen
    got_marker = False
    if color in state.large_factory.moon_colors():
        tiles, got_marker = state.large_factory.take_from_moon(color)
        if tiles:
            taken += tiles
            sources.append(("GF", len(tiles)))
            # GF Pool nach Entnahme loggen
            pool = state.large_factory.moon_pool
            pool_str = ", ".join(c.value for c in pool) if pool else ""
            pool_display = f"({pool_str})" if pool else "leer"
            pending_logs.append(f"🌙 GF Moon-Pool: {pool_display}")

    # 3. Sicherheitscheck
    if not taken:
        raise ValueError(f"Keine {color.value}-Fliesen oben auf Moon-Seiten gefunden.")

    # 4. Startspieler-Marker vergeben
    if got_marker:
        _apply_first_player_marker(state)

    # 5. Aktions-Log + Place + Mondstapel/Chip-Logs
    dest = f"Reihe {row_index+1}" if row_index >= 0 else "Strafleiste"
    src_detail = "+".join(str(c) for _, c in sources)
    src_labels = ", ".join(lbl for lbl, _ in sources)

    # Aktions-Log VOR place — Index merken um Füllstand später einzufügen
    state.log_event(
        f"🌙 {p.name}: {len(taken)} ({src_detail})× {color.value} "
        f"von {src_labels} → {dest}"
    )
    action_log_idx = len(state.log) - 1
    _execute_place(state, taken, color, row_index)

    # Füllstand direkt in den Aktions-Log-Eintrag einbauen (nur bei Musterreihe)
    if row_index >= 0:
        row = p.pattern_lines[row_index]
        state.log[action_log_idx] += f" [{len(row.tiles)}/{row.capacity}]"

    for log in pending_logs:
        state.log_event(log)

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



def _format_moon_stacks(f) -> str:
    """Formatiert alle Mondstapel einer Fabrik als lesbaren String.
    Jeder Stapel: [unten → oben], sichtbar = letzter Stein.
    """
    if not f.moon_stacks:
        return "leer"
    stacks = []
    for stack in f.moon_stacks:
        top = stack[-1].value if stack else "?"
        rest = ", ".join(c.value for c in stack[:-1]) if len(stack) > 1 else ""
        stacks.append(f"({rest}→{top})" if rest else f"({top})")
    return " | ".join(stacks)

def _take_small_sun(state: "GameState", move: Move) -> tuple[list[TileColor], bool]:
    f = _get_factory(state, move.take.factory_id)
    taken, remaining = f.take_from_sun(move.take.color)

    # Spieler legt übrige Steine in gewählter Reihenfolge auf Moon
    moon_log = None
    if remaining:
        f.place_on_moon(move.take.moon_order)
        moon_log = f"🌙 F{f.factory_id} Mond-Stapel: {_format_moon_stacks(f)}"

    # Bonus-Chip aufdecken wenn Fabrik jetzt komplett leer
    chip_log = None
    if f.is_fully_empty and f.bonus_chip and not f.bonus_chip_revealed:
        f.bonus_chip_revealed = True
        chip_log = f"🎴 F{f.factory_id}: Bonusplättchen aufgedeckt!"

    return taken, False, moon_log, chip_log   # kleine Fabrik hat keinen Startspieler-Marker


def _take_small_moon(state: "GameState", move: Move) -> tuple[list[TileColor], bool]:
    f = _get_factory(state, move.take.factory_id)
    taken = f.take_from_moon(move.take.color)

    # Mondstapel nach Entnahme loggen
    remaining_str = _format_moon_stacks(f)
    state.log_event(
        f"🌙 F{f.factory_id} Mond-Stapel nach Entnahme: {remaining_str}"
    )

    # Bonus-Chip aufdecken wenn Fabrik jetzt komplett leer
    if f.is_fully_empty and f.bonus_chip and not f.bonus_chip_revealed:
        f.bonus_chip_revealed = True
        state.log_event(f"🎴 F{f.factory_id}: Bonusplättchen aufgedeckt!")

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