"""
Game Loop und Spielende für Mosaic-AI.

Ablauf einer kompletten Partie:

  SETUP
    setup_new_game() → GameState

  PRO RUNDE (5 Runden):
    DRAFTING-PHASE (abwechselnd, bis alle Fabriken leer):
      Jeder Spieler wählt einen von zwei Zug-Typen:
        a) Move         — Steine nehmen + auf Musterreihe legen
        b) PlaceDomeTileMove — neue Kuppelplatte aus Pool legen
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
    Bei Gleichstand: wer Startspielerstein hat

Das Game-Objekt steuert den Ablauf und stellt sicher dass Züge
nur in der richtigen Phase angenommen werden.
"""

from __future__ import annotations
import copy
from dataclasses import dataclass
from typing import Optional

from engine.setup import GameState, setup_new_game, setup_new_round, NUM_ROUNDS
from engine.moves import Move, PlaceDomeTileMove, AnyMove
from engine.validation import validate_move, generate_valid_moves
from engine.execution import execute_move
from engine.round_end import (
    TilingAction,
    validate_tiling_action,
    execute_full_tiling,
    check_drafting_complete, get_pending_tiling_rows,
    apply_round_scoring, score_placed_tile,
    process_unplaceable_rows, score_penalty,
    apply_bonus_chips_to_row,
)
from engine.dome import ROTATION_MAP, SpaceType


# ---------------------------------------------------------------------------
# PlaceDomeTileMove Validierung + Ausführung
# ---------------------------------------------------------------------------

def validate_dome_move(state: GameState, move: PlaceDomeTileMove) -> Optional[str]:
    """Prüft ob eine Kuppel-Platzierung gültig ist."""
    player = state.active_player

    if not player.can_place_dome_tile(state.round_number):
        if state.round_number >= 5:
            return "In Runde 5 werden keine Kuppeln mehr gelegt."
        if player.dome_tiles_placed_this_round >= 2:
            return f"{player.name} hat bereits 2 Kuppeln diese Runde gelegt."
        return "Das 3×3-Raster ist bereits voll."

    if player.has_unplaced_start_tile():
        if move.dome_tile_id != player.start_dome_tile.tile_id:
            return (
                f"Die Startkuppel (ID {player.start_dome_tile.tile_id}) "
                f"muss als erstes gelegt werden."
            )
    else:
        tile = _find_in_display(state, move.dome_tile_id)
        if tile is None:
            return f"Kuppel {move.dome_tile_id} liegt nicht in der offenen Ablage."

    slot = player.dome_grid.dome_slots[move.slot_row][move.slot_col]
    if slot is not None:
        return f"Slot ({move.slot_row},{move.slot_col}) ist bereits belegt."

    return None


def execute_dome_move(state: GameState, move: PlaceDomeTileMove) -> None:
    """Führt eine Kuppel-Platzierung aus."""
    player = state.active_player

    if player.has_unplaced_start_tile() and move.dome_tile_id == player.start_dome_tile.tile_id:
        tile = player.start_dome_tile
        player.start_dome_tile = None
    else:
        tile = _find_in_display(state, move.dome_tile_id)
        state.dome_display.remove(tile)

    tile.apply_rotation(move.rotation)
    player.dome_grid.place_dome_tile(tile, move.slot_row, move.slot_col)
    player.register_dome_placement()
    player.use_player_token(state.round_number)

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
    state.dome_tile_pool.extend(rest)
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

    tiles_to_consider = (
        [player.start_dome_tile]
        if player.has_unplaced_start_tile()
        else state.dome_display
    )

    for tile in tiles_to_consider:
        # Start-Kachel kann ein String-Platzhalter sein ("Muss_noch_gezogen_werden"),
        # solange der Spieler sie noch nicht vom Stapel gezogen hat → überspringen.
        if isinstance(tile, str):
            continue
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

        dome_row = row_idx // 2
        space_row = row_idx % 2
        valid_si = [space_row * 2, space_row * 2 + 1]

        for sc in range(3):
            slot = player.dome_grid.dome_slots[dome_row][sc]
            if slot is None:
                continue
            # valid_si für normale Spaces, aber WILD Spaces sind in allen 4 Positionen gültig
            all_si = list(range(len(slot.spaces)))
            for si in all_si:
                space = slot.spaces[si]
                if space.is_filled or space.is_locked:
                    continue
                # WILD und NORMAL: nur in valid_si (Reihenposition muss stimmen)
                # SPECIAL: nie hier
                if si not in valid_si:
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
                    for si in range(len(rotated)):
                        space = rotated[si]
                        # WILD und NORMAL: nur in valid_si (Reihenposition muss stimmen)
                        if si not in valid_si:
                            continue
                        if space.accepts(color):
                            a = TilingAction(pattern_row=row_idx, slot_row=dome_row,
                                             slot_col=sc, space_index=si,
                                             dome_tile_id=tile.tile_id, rotation=rotation)
                            if validate_tiling_action(state, player_idx, a) is None:
                                actions.append(a)

    return actions



# ---------------------------------------------------------------------------
# Hauptspiel-Schleife
# ---------------------------------------------------------------------------

@dataclass
class GameResult:
    """Ergebnis einer abgeschlossenen Partie."""
    winner:        Optional[int]
    scores:        list[int]
    filled_spaces: list[int]            # Info-Feld, kein Tiebreaker
    log:           list[str]


class Game:
    """
    Steuert den kompletten Spielablauf.
    Single Source of Truth für alle Spielaktionen.
    """

    def __init__(self):
        self.state: Optional[GameState] = None

    def start(
        self,
        player_names: list[str] | None = None,
        first_player: int = 0,
        seed: int | None = None,
        random_scoring: bool = True
    ) -> GameState:
        self.state = setup_new_game(player_names, first_player, seed)

        from engine.scoring import ALL_SCORING_TILES, sample_valid_scoring_ids
        import random

        if random_scoring:
            self.state.scoring_tile_ids = sample_valid_scoring_ids(3, rng=random)
        else:
            self.state.scoring_tile_ids = [0, 1, 2]

        self.state.current_player = first_player
        return self.state

    def apply_start_placement(self, player_idx: int, tile_id: int, row: int, col: int, rot: int):
        """
        Platziert die Startkuppelkachel eines Spielers.
        Erzwingt Reihenfolge: Nicht-Startspieler zuerst, dann Startspieler.
        Single Source of Truth — wird von Server und agent_env aufgerufen.
        """
        player = self.state.players[player_idx]
        first_player = self.state.current_player
        non_starter  = 1 - first_player

        # Reihenfolge: Nicht-Startspieler zuerst
        if player_idx == first_player and self.state.players[non_starter].start_dome_tile is not None:
            raise ValueError("Nicht-Startspieler muss zuerst eine Kuppelplatte wählen.")

        # start_dome_tile ist None wenn bereits gelegt ODER ab Runde 2 (kein Sentinel mehr)
        if player.start_dome_tile is None:
            raise ValueError(f"Spieler {player_idx} hat keine ausstehende Startkachel.")

        if player.dome_grid.dome_slots[row][col] is not None:
            raise ValueError(f"Slot ({row},{col}) ist nicht frei.")

        tile = _find_in_display(self.state, tile_id)
        if tile is None:
            raise ValueError(f"Kachel {tile_id} nicht im Display.")

        idx = self.state.dome_display.index(tile)
        self.state.dome_display.remove(tile)
        if self.state.dome_tile_pool:
            # Nachgezogene Karte an die Position der gewählten setzen (nicht ans
            # Ende), damit die verbleibenden Karten ihre Position behalten.
            self.state.dome_display.insert(idx, self.state.dome_tile_pool.pop(0))
        tile = copy.deepcopy(tile)
        tile.apply_rotation(rot)
        player.dome_grid.place_dome_tile(tile, row, col)
        player.start_dome_tile = None
        self.state.log_event(
            f"{player.name}: Startkachel {tile_id} → ({row},{col}) rot={rot}°"
        )

    # ------------------------------------------------------------------
    # Drafting-Phase
    # ------------------------------------------------------------------

    def drafting_complete(self) -> bool:
        return check_drafting_complete(self.state)

    def valid_moves(self) -> list[dict]:
        """Gibt alle validen Züge für den aktuellen Spieler zurück."""
        if self.state.phase != "drafting":
            return generate_tiling_actions(self.state, self.state.active_player_index)

        moves = []
        moves.extend(generate_valid_moves(self.state))
        moves.extend(generate_dome_moves(self.state))
        moves.extend(generate_bonus_chip_moves(self.state))

        if len(moves) == 0:
            moves.append({"type": "pass"})

        return moves

    def apply(self, move: AnyMove) -> None:
        """
        Führt einen Zug aus.
        Single Source of Truth für alle Spielaktionen —
        wird von Server, agent_env und self_play aufgerufen.
        """
        assert self.state is not None

        if isinstance(move, dict):
            t = move.get("type")

            # ── Tiling-Phase ─────────────────────────────────────────
            if t == "tiling":
                action = TilingAction(
                    pattern_row=move["pattern_row"],
                    slot_row=move["slot_row"],
                    slot_col=move["slot_col"],
                    space_index=move["space_index"],
                    dome_tile_id=move.get("dome_tile_id"),
                    rotation=move.get("rotation", 0),
                )
                self.apply_single_tiling(move["player"], action)
                return

            if t == "use_chips":
                pi = move["player"]
                ri = move["pattern_row"]
                player = self.state.players[pi]
                success = apply_bonus_chips_to_row(player, ri)
                if not success:
                    raise ValueError(f"Reihe {ri+1} nicht mit Chips komplettierbar.")
                self.state.log_event(
                    f"🎫 {player.name} komplettiert Reihe {ri+1} vollständig mit Bonus-Chips!"
                )
                return

            if t == "end_tiling":
                pi = move.get("player", self.state.current_player)
                
                # 1. Validierung (bestehend)
                if self.valid_tiling_actions(pi):
                    raise ValueError(f"Noch Züge offen für Spieler {pi}")
                
                # 2. Zwingende Zuweisung auf das State-Objekt!
                # Wir stellen sicher, dass das Array existiert
                if not hasattr(self.state, "_tiling_done"):
                    self.state._tiling_done = [False, False]
                
                # Hier der Fix: Wir setzen den Wert explizit im state
                tmp_done = list(self.state._tiling_done)
                tmp_done[pi] = True
                self.state._tiling_done = tmp_done
                
                print(f"DEBUG: Flag gesetzt für P{pi}. Neuer Status: {self.state._tiling_done}")

                # 3. Wechsel oder Abschluss (bestehend)
                other = 1 - pi
                if not self.state._tiling_done[other]:
                    self.state.current_player = other
                    return
                
                # 4. Phase beenden
                self.state._tiling_done = [False, False]
                self.state.phase = "drafting"
                self._execute_end_tiling()
                return

            if t == "pass":
                self.state.switch_player()
                self._check_phase_transition()
                return

        # ── Drafting-Phase ────────────────────────────────────────────
        assert self.state.phase == "drafting", \
            f"Zug {move} ist in Phase '{self.state.phase}' nicht erlaubt."

        from engine.moves import DrawFromStackMove, TakeBonusChipMove

        if isinstance(move, PlaceDomeTileMove):
            err = validate_dome_move(self.state, move)
            if err: raise ValueError(err)
            execute_dome_move(self.state, move)
            self.state.switch_player()

        elif isinstance(move, DrawFromStackMove):
            err = validate_draw_from_stack(self.state, move)
            if err: raise ValueError(err)
            execute_draw_from_stack(self.state, move)
            self.state.switch_player()

        elif isinstance(move, TakeBonusChipMove):
            err = validate_take_bonus_chip(self.state, move)
            if err: raise ValueError(err)
            execute_take_bonus_chip(self.state, move)
            self.state.switch_player()

        else:
            is_global_moon = (
                getattr(move, "take", None) is not None
                and move.take.source.name == "SMALL_FACTORY_MOON"
                and move.take.factory_id is None
            )
            if is_global_moon:
                from engine.validation import validate_moon_take
                err = validate_moon_take(self.state, move)
                if err: raise ValueError(err)
            else:
                err = validate_move(self.state, move)
                if err: raise ValueError(err)

            execute_move(self.state, move)
            self.state.switch_player()

        self._check_phase_transition()

    def _execute_end_tiling(self) -> None:
        """
        Schließt die Tiling-Phase ab: Strafen, Rundenübergang oder Spielende.
        Single Source of Truth — wird von apply() aufgerufen.
        KI-spezifisches Dome-Placement nach Rundenübergang wird NICHT hier gemacht
        (das ist Aufgabe von agent_env._place_initial_dome_tile_ai).
        """
        for player in self.state.players:
            process_unplaceable_rows(player, self.state.tower, self.state)

        for player in self.state.players:
            pen = score_penalty(player)
            if pen < 0:
                player.apply_score(pen)
                broken = player.clear_broken()
                self.state.tower.add(broken)
                self.state.log_event(
                    f"{player.name}: Strafe {pen} Pkt → {player.score} Gesamt"
                )
            else:
                player.clear_broken()

        if self.is_over():
            self.state.phase = "end"
            self.state.log_event("Das Spiel ist beendet!")
        else:
            self.next_round()
            self.state.phase = "drafting"
            self.state.log_event(f"Runde {self.state.round_number} beginnt.")

    def _check_phase_transition(self) -> None:
        """Wechselt automatisch zu Tiling wenn Drafting abgeschlossen."""
        if self.state.phase == "drafting" and check_drafting_complete(self.state):
            self.state.phase = "tiling"
            self.state._tiling_done = [False, False]
            # Reihenfolge-Tracking zurücksetzen: zu Beginn jeder Tiling-Phase
            # wurde noch keine Reihe gelegt.
            for p in self.state.players:
                p.tiled_max_row = -1
            process_unplaceable_rows(self.state.players[0], self.state.tower, self.state)
            process_unplaceable_rows(self.state.players[1], self.state.tower, self.state)
            self.state.log_event("Tiling-Phase beginnt.")

    # ------------------------------------------------------------------
    # Tiling-Phase
    # ------------------------------------------------------------------

    def valid_tiling_actions(self, player_idx: int) -> list[TilingAction]:
        return generate_tiling_actions(self.state, player_idx)

    def apply_single_tiling(self, player_idx: int, action: TilingAction) -> None:
        """Führt eine einzelne Tiling-Aktion aus (Single Source of Truth)."""
        err = validate_tiling_action(self.state, player_idx, action)
        if err:
            raise ValueError(err)
        execute_full_tiling(self.state, player_idx, action)

    # ------------------------------------------------------------------
    # Rundenübergang / Spielende
    # ------------------------------------------------------------------

    def is_over(self) -> bool:
        return self.state.round_number >= NUM_ROUNDS

    def next_round(self) -> None:
        assert self.state.phase == "done", "Tiling-Phase muss abgeschlossen sein."
        assert not self.is_over(), "Spiel ist bereits beendet."
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
            winner = 0
        elif self.state.players[1].holds_first_player_marker:
            winner = 1
        else:
            winner = None

        filled = []
        for p in self.state.players:
            count = sum(
                1 for row in p.dome_grid.dome_slots
                for slot in row if slot is not None
                for space in slot.spaces if space.is_filled
            )
            filled.append(count)

        return GameResult(
            winner=winner,
            scores=scores,
            filled_spaces=filled,
            log=self.state.log,
        )

    def _calculate_end_scoring(self) -> dict:
        """
        Führt die Endwertung durch und gibt Ergebnisse zurück.
        Single Source of Truth — wird von agent_env und Server aufgerufen.
        """
        from engine.scoring import calculate_end_scoring
        results = {}
        for pi, player in enumerate(self.state.players):
            res = calculate_end_scoring(player, self.state.scoring_tile_ids)
            player.apply_score(res["total"])
            results[pi] = res
            self.state.log_event(
                f"🏆 {player.name}: Endwertung {res['total']} Pkt "
                f"→ Gesamt: {player.score} Pkt"
            )
            for tid, detail in res.items():
                if tid == "total":
                    continue
                if not isinstance(detail, dict):
                    continue
                self.state.log_event(
                    f"   {detail['emoji']} {detail['name']}: {detail['score']} Pkt"
                )
        self.state.phase = "final"
        return {"end_scoring": results}