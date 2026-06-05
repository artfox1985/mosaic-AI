"""
Game Loop und Spielende für Mosaic-AI.

Ablauf einer kompletten Partie:

  SETUP
    setup_new_game() → GameState

  PRO RUNDE (5 Runden):
    DRAFTING-PHASE (abwechselnd, bis alle Fabriken leer):
      Jeder Spieler wählt einen von zwei Zug-Typen:
        a) Move         — Steine nehmen + auf Musterreihe legen
        b) PlaceDomeTileMove — neue Kuppelkachel aus Pool legen
                               (max 2 pro Runde, nicht in Runde 5)

    TILING-PHASE (nach Drafting, für jeden Spieler):
      Für jede volle Musterreihe: TilingAction ausführen
      (Stein auf Kuppel, Rotation/Slot bereits festgelegt)
      Falls Special-Space freigeschaltet: SpecialTilingAction

    SCORING-PHASE:
      apply_round_scoring()

    Falls Runde < 5: setup_new_round()

  SPIELENDE (nach Runde 5):
    Endwertung: keine weiteren Boni in Mosaic-AI
    Gewinner = höchste Punktzahl
    Bei Gleichstand: meiste gefüllte Spaces auf der Kuppel

Das Game-Objekt steuert den Ablauf und stellt sicher dass Züge
nur in der richtigen Phase angenommen werden.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Union

from engine.setup import GameState, setup_new_game, setup_new_round, NUM_ROUNDS
from engine.moves import Move, PlaceDomeTileMove, AnyMove
from engine.validation import validate_move, generate_valid_moves
from engine.execution import execute_move
from engine.round_end import (
    TilingAction, SpecialTilingAction,
    validate_tiling_action, validate_special_tiling,
    execute_tiling_action, execute_special_tiling,
    check_drafting_complete, get_pending_tiling_rows,
    apply_round_scoring, score_placed_tile,
)
from engine.dome import ROTATION_MAP


# ---------------------------------------------------------------------------
# PlaceDomeTileMove Validierung + Ausführung
# ---------------------------------------------------------------------------

def validate_dome_move(state: GameState, move: PlaceDomeTileMove) -> Optional[str]:
    """Prüft ob eine Kachel-Platzierung gültig ist."""
    player = state.active_player

    if not player.can_place_dome_tile(state.round_number):
        if state.round_number >= 5:
            return "In Runde 5 werden keine Kacheln mehr gelegt."
        if player.dome_tiles_placed_this_round >= 2:
            return f"{player.name} hat bereits 2 Kacheln diese Runde gelegt."
        return "Das 3×3-Raster ist bereits voll."

    # Startkachel muss zuerst gelegt werden
    if player.has_unplaced_start_tile():
        if move.dome_tile_id != player.start_dome_tile.tile_id:
            return (
                f"Die Startkachel (ID {player.start_dome_tile.tile_id}) "
                f"muss als erstes gelegt werden."
            )
        # Startkachel kommt aus player.start_dome_tile, nicht aus Display
    else:
        # Kachel muss im offenen Display (G) liegen
        tile = _find_in_display(state, move.dome_tile_id)
        if tile is None:
            return f"Kachel {move.dome_tile_id} liegt nicht im offenen Display (G)."

    # Slot frei?
    slot = player.dome_grid.dome_slots[move.slot_row][move.slot_col]
    if slot is not None:
        return f"Slot ({move.slot_row},{move.slot_col}) ist bereits belegt."

    return None


def execute_dome_move(state: GameState, move: PlaceDomeTileMove) -> None:
    """Führt eine Kachel-Platzierung aus."""
    player = state.active_player

    # Startkachel oder Kachel aus dem Display (G)?
    if player.has_unplaced_start_tile() and move.dome_tile_id == player.start_dome_tile.tile_id:
        tile = player.start_dome_tile
        player.start_dome_tile = None
    else:
        tile = _find_in_display(state, move.dome_tile_id)
        state.dome_display.remove(tile)
        # [3] Display wird NICHT sofort aufgefüllt — erst in Phase 3

    tile.apply_rotation(move.rotation)
    player.dome_grid.place_dome_tile(tile, move.slot_row, move.slot_col)
    player.register_dome_placement()
    player.use_player_token(state.round_number)   # [2] Spielerplättchen verbrauchen

    state.log_event(
        f"{player.name}: Kachel {move.dome_tile_id} → "
        f"Slot ({move.slot_row},{move.slot_col}) rot={move.rotation}° "
        f"[Plättchen {player.player_tokens_used}/2]"
    )


def validate_take_bonus_chip(state: GameState, move) -> Optional[str]:
    """[6] Aktion D: Bonusplättchen nehmen."""
    player = state.active_player
    if not player.can_take_bonus_chip():
        return f"{player.name} hat bereits 2 Bonusplättchen diese Runde genommen."
    f = next((f for f in state.factories if f.factory_id == move.factory_id), None)
    if f is None:
        return f"Fabrik {move.factory_id} nicht gefunden."
    if not f.bonus_chip_revealed or f.bonus_chip is None:
        return f"Kein aufgedecktes Bonusplättchen auf Fabrik {move.factory_id}."
    return None


def execute_take_bonus_chip(state: GameState, move) -> None:
    """[6] Nimmt aufgedecktes Bonusplättchen von einer Fabrik."""
    player = state.active_player
    f = next(f for f in state.factories if f.factory_id == move.factory_id)
    chip = f.bonus_chip
    f.bonus_chip = None
    f.bonus_chip_revealed = False
    player.take_bonus_chip(chip)
    state.log_event(
        f"{player.name}: Bonusplättchen von Fabrik {move.factory_id} genommen "
        f"[{player.bonus_chips_used_this_round}/2 diese Runde]"
    )


def generate_bonus_chip_moves(state: GameState):
    """Alle gültigen Bonusplättchen-Züge für den aktiven Spieler."""
    from engine.moves import TakeBonusChipMove
    player = state.active_player
    if not player.can_take_bonus_chip():
        return []
    return [
        TakeBonusChipMove(factory_id=f.factory_id)
        for f in state.factories
        if f.bonus_chip_revealed and f.bonus_chip is not None
    ]


def validate_draw_from_stack(state: GameState, move) -> Optional[str]:
    """[4] Validiert Stapel-Zug (−1 Pkt pro gezogener Karte)."""
    player = state.active_player
    if state.round_number >= 5:
        return "In Runde 5 werden keine Kuppelplatten mehr gelegt."
    if player.has_used_all_tokens(state.round_number):
        return f"{player.name} hat bereits beide Spielerplättchen genutzt."
    if not player.can_place_dome_tile(state.round_number):
        return "Das 3×3-Raster ist bereits voll."
    if not state.dome_tile_pool:
        return "Kein Stapel mehr vorhanden."
    if move.num_drawn < 1 or move.num_drawn > len(state.dome_tile_pool):
        return f"num_drawn muss zwischen 1 und {len(state.dome_tile_pool)} liegen."
    available = {t.tile_id for t in state.dome_tile_pool[:move.num_drawn]}
    if move.chosen_id not in available:
        return f"Kachel {move.chosen_id} nicht unter den {move.num_drawn} gezogenen."
    if player.dome_grid.dome_slots[move.slot_row][move.slot_col] is not None:
        return f"Slot ({move.slot_row},{move.slot_col}) ist bereits belegt."
    return None


def execute_draw_from_stack(state: GameState, move) -> None:
    """[4] Stapel-Zug: zahlt −1 Pkt pro gezogener Karte, wählt 1, Rest zurück."""
    player = state.active_player
    player.apply_score(-move.num_drawn)
    state.log_event(
        f"📦 {player.name}: {move.num_drawn}× vom Stapel gezogen "
        f"−{move.num_drawn} Pkt → {player.score} Gesamt"
    )
    drawn = state.dome_tile_pool[:move.num_drawn]
    state.dome_tile_pool = state.dome_tile_pool[move.num_drawn:]
    chosen = next(t for t in drawn if t.tile_id == move.chosen_id)
    rest = [t for t in drawn if t.tile_id != move.chosen_id]
    state.dome_tile_pool.extend(rest)   # Rest zurück unter Stapel
    chosen.apply_rotation(move.rotation)
    player.dome_grid.place_dome_tile(chosen, move.slot_row, move.slot_col)
    player.register_dome_placement()
    player.use_player_token(state.round_number)
    state.log_event(
        f"{player.name}: Kachel {move.chosen_id} → Slot ({move.slot_row},{move.slot_col}) "
        f"rot={move.rotation}° [Plättchen {player.player_tokens_used}/2]"
    )


def generate_dome_moves(state: GameState) -> list[PlaceDomeTileMove]:
    """Alle gültigen Kachel-Platzierungen für den aktiven Spieler."""
    player = state.active_player
    if not player.can_place_dome_tile(state.round_number):
        return []

    moves = []
    empty_slots = player.dome_grid.empty_slots()

    # Startkachel muss zuerst gelegt werden
    tiles_to_consider = (
        [player.start_dome_tile]
        if player.has_unplaced_start_tile()
        else state.dome_display          # nur die 3 offen liegenden Kacheln (G)
    )

    for tile in tiles_to_consider:
        for slot_row, slot_col in empty_slots:
            for rotation in (0, 90, 180, 270):
                m = PlaceDomeTileMove(
                    dome_tile_id=tile.tile_id,
                    slot_row=slot_row,
                    slot_col=slot_col,
                    rotation=rotation,
                )
                if validate_dome_move(state, m) is None:
                    moves.append(m)
    return moves


def _find_tile(state: GameState, tile_id: int):
    """Sucht im verdeckten Stapel (F)."""
    for t in state.dome_tile_pool:
        if t.tile_id == tile_id:
            return t
    return None

def _find_in_display(state: GameState, tile_id: int):
    """Sucht im offenen Display (G)."""
    for t in state.dome_display:
        if t.tile_id == tile_id:
            return t
    return None


# ---------------------------------------------------------------------------
# Tiling-Phase: alle vollen Reihen abarbeiten
# ---------------------------------------------------------------------------

def generate_tiling_actions(
    state: GameState,
    player_idx: int,
) -> list[TilingAction]:
    """
    Generiert alle gültigen TilingActions für einen Spieler.
    Berücksichtigt alle vollen Musterreihen × alle freien Slots ×
    alle Spaces × alle Rotationen (bei neuen Kacheln).
    """
    player = state.players[player_idx]
    actions = []

    for row_idx in get_pending_tiling_rows(player):
        color = player.pattern_lines[row_idx].color

        # [8] Musterreihe i → horizontale Kuppelreihe i
        dome_row = row_idx // 2         # Slot-Zeile: 0,0,1,1,2,2
        space_row = row_idx % 2         # 0=obere Spaces [0,1], 1=untere [2,3]
        valid_si = [space_row * 2, space_row * 2 + 1]

        for sc in range(3):
            slot = player.dome_grid.dome_slots[dome_row][sc]
            if slot is None:
                continue
            for si in valid_si:
                space = slot.spaces[si]
                if space.is_filled or space.is_locked:
                    continue
                if not space.accepts(color):
                    continue
                a = TilingAction(pattern_row=row_idx, slot_row=dome_row,
                                 slot_col=sc, space_index=si)
                if validate_tiling_action(state, player_idx, a) is None:
                    actions.append(a)

        for sc in range(3):
            if player.dome_grid.dome_slots[dome_row][sc] is not None:
                continue
            for tile in state.dome_display:
                for rotation in (0, 90, 180, 270):
                    rotated = [tile.spaces[i] for i in ROTATION_MAP[rotation]]
                    for si in valid_si:
                        if rotated[si].accepts(color):
                            a = TilingAction(pattern_row=row_idx, slot_row=dome_row,
                                             slot_col=sc, space_index=si,
                                             dome_tile_id=tile.tile_id, rotation=rotation)
                            if validate_tiling_action(state, player_idx, a) is None:
                                actions.append(a)

    return actions


def run_tiling_phase(
    state: GameState,
    tiling_decisions: dict[int, list[TilingAction]],
    special_decisions: dict[int, list[SpecialTilingAction]] | None = None,
) -> dict[int, int]:
    """
    Führt die Tiling-Phase für beide Spieler aus.

    tiling_decisions: {player_idx: [TilingAction, ...]}  — eine pro voller Reihe
    special_decisions: {player_idx: [SpecialTilingAction, ...]}  — optional

    Gibt {player_idx: tiling_punkte} zurück.
    """
    scores: dict[int, int] = {0: 0, 1: 0}

    for player_idx in range(2):
        actions = tiling_decisions.get(player_idx, [])
        for action in actions:
            # Re-validieren direkt vor Ausführung (State kann sich geändert haben)
            err = validate_tiling_action(state, player_idx, action)
            if err:
                state.log_event(f"TilingAction übersprungen: {err}")
                continue

            # Punkte vor der Ausführung berechnen (Stein noch nicht gelegt)
            # → nach execute wäre der Space schon gefüllt
            execute_tiling_action(state, player_idx, action)

            # Scoring für den gerade platzierten Stein
            pts = score_placed_tile(
                state.players[player_idx],
                action.slot_row, action.slot_col, action.space_index,
            )
            if isinstance(pts, tuple):
                scores[player_idx] += pts[0]
            else:
                scores[player_idx] += pts

        # Special-Tiles
        if special_decisions:
            for sp_action in special_decisions.get(player_idx, []):
                err = validate_special_tiling(state, player_idx, sp_action)
                if err:
                    raise ValueError(f"Ungültige SpecialTilingAction: {err}")
                bonus = execute_special_tiling(state, player_idx, sp_action)
                scores[player_idx] += bonus

    return scores


# ---------------------------------------------------------------------------
# Hauptspiel-Schleife
# ---------------------------------------------------------------------------

@dataclass
class GameResult:
    """Ergebnis einer abgeschlossenen Partie."""
    winner:        Optional[int]        # 0 oder 1, None = Unentschieden
    scores:        list[int]            # [score_p0, score_p1]
    filled_spaces: list[int]            # [spaces_p0, spaces_p1] — Info-Feld (Kein Tiebreaker!)
    log:           list[str]


class Game:
    """
    Steuert den kompletten Spielablauf.

    Verwendung:
        game = Game()
        state = game.start(["Alice", "Bob"])

        # Drafting-Phase:
        while not game.drafting_complete():
            moves = game.valid_moves()       # Move + PlaceDomeTileMove
            game.apply(chosen_move)

        # Tiling-Phase:
        for player_idx in range(2):
            actions = game.valid_tiling_actions(player_idx)
            game.apply_tiling(player_idx, chosen_actions)

        # Nächste Runde oder Spielende:
        if game.is_over():
            result = game.result()
        else:
            game.next_round()
    """

    def __init__(self):
        self.state: Optional[GameState] = None

    def start(
        self,
        player_names: list[str] | None = None,
        first_player: int = 0,
        seed: int | None = None,
    ) -> GameState:
        self.state = setup_new_game(player_names, first_player, seed)
        return self.state

    # ------------------------------------------------------------------
    # Drafting-Phase
    # ------------------------------------------------------------------

    def drafting_complete(self) -> bool:
        return check_drafting_complete(self.state)

    def valid_moves(self) -> list[AnyMove]:
        """Alle gültigen Züge (Stein + Kachel + Bonusplättchen) für aktiven Spieler."""
        stone_moves = generate_valid_moves(self.state)
        dome_moves  = generate_dome_moves(self.state)
        chip_moves  = generate_bonus_chip_moves(self.state)
        return stone_moves + dome_moves + chip_moves

    def apply(self, move: AnyMove) -> None:
        """Führt einen Zug aus und wechselt den aktiven Spieler."""
        assert self.state is not None
        assert self.state.phase == "drafting", "Nur in der Drafting-Phase möglich."

        from engine.moves import DrawFromStackMove, TakeBonusChipMove
        if isinstance(move, PlaceDomeTileMove):
            err = validate_dome_move(self.state, move)
            if err:
                raise ValueError(err)
            execute_dome_move(self.state, move)
            self.state.switch_player()
        elif isinstance(move, DrawFromStackMove):
            err = validate_draw_from_stack(self.state, move)
            if err:
                raise ValueError(err)
            execute_draw_from_stack(self.state, move)
            self.state.switch_player()
        elif isinstance(move, TakeBonusChipMove):
            err = validate_take_bonus_chip(self.state, move)
            if err:
                raise ValueError(err)
            execute_take_bonus_chip(self.state, move)
            self.state.switch_player()
        else:
            # Sobald das Wort "MOON" auftaucht, ist es Aktion C!
            is_moon_take = "MOON" in move.take.source.name
            
            if is_moon_take:
                # Da wir die Standard-Validierung überspringen, müssen wir kurz 
                # prüfen, ob die Ziellinie die Farbe überhaupt akzeptiert.
                from engine.validation import _validate_place
                err = _validate_place(self.state, move.take.color, move.place.row_index)
                if err:
                    raise ValueError(err)
            else:
                err = validate_move(self.state, move)
                if err:
                    raise ValueError(err)
                    
            execute_move(self.state, move)
            self.state.switch_player()

        if self.drafting_complete():
            self.state.phase = "tiling"

    # ------------------------------------------------------------------
    # Tiling-Phase
    # ------------------------------------------------------------------

    def valid_tiling_actions(self, player_idx: int) -> list[TilingAction]:
        return generate_tiling_actions(self.state, player_idx)

    def apply_tiling_phase(
        self,
        tiling_decisions: dict[int, list[TilingAction]],
        special_decisions: dict[int, list[SpecialTilingAction]] | None = None,
    ) -> None:
        """Führt die Tiling-Phase aus und berechnet Punkte."""
        assert self.state.phase == "tiling"
        # [9] Unplatzierbare Reihen vor Tiling auf Straffeld
        from engine.round_end import process_unplaceable_rows
        for p in self.state.players:
            process_unplaceable_rows(p, self.state.tower, self.state)
        scores = run_tiling_phase(self.state, tiling_decisions, special_decisions)
        apply_round_scoring(self.state, scores)
        self.state.phase = "end" if self.is_over() else "done"

    # ------------------------------------------------------------------
    # Rundenübergang / Spielende
    # ------------------------------------------------------------------

    def is_over(self) -> bool:
        return self.state.round_number >= NUM_ROUNDS

    def next_round(self) -> None:
        assert self.state.phase == "done", "Tiling-Phase muss abgeschlossen sein."
        assert not self.is_over(), "Spiel ist bereits beendet."
        # Phase 3: Display (G) auf 3 Kacheln auffüllen
        while len(self.state.dome_display) < 3 and self.state.dome_tile_pool:
            self.state.dome_display.append(self.state.dome_tile_pool.pop(0))
        setup_new_round(self.state)
        self.state.phase = "drafting"

    def result(self) -> GameResult:
        assert self.is_over()
        scores = [p.score for p in self.state.players]

        if scores[0] > scores[1]:
            winner = 0
        elif scores[1] > scores[0]:
            winner = 1
        elif self.state.players[0].holds_first_player_marker:
            winner = 0   # [13] Tiebreaker: wer Startspielerstein hat
        elif self.state.players[1].holds_first_player_marker:
            winner = 1
        else:
            winner = None  # echtes Unentschieden
            
        # FIX: Berechne die gefüllten Spaces für das Info-Feld sicher
        filled = []
        for p in self.state.players:
            count = 0
            for row in p.dome_grid.dome_slots:
                for slot in row:
                    if slot is not None:
                        count += sum(1 for space in slot.spaces if space.is_filled)
            filled.append(count)

        return GameResult(
            winner=winner,
            scores=scores,
            filled_spaces=filled,
            log=self.state.log,
        )
        
    def apply_single_tiling(self, player_idx: int, action: TilingAction):
        """Führt eine einzelne Tiling-Aktion sofort aus (für Web-Interaktivität)."""
        err = validate_tiling_action(self.state, player_idx, action)
        if err:
            raise ValueError(err)
            
        # Nutze die Funktion, die wir vorhin repariert haben!
        execute_full_tiling(self.state, player_idx, action)
