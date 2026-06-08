"""
Mosaic-AI — KI-Agenten-Umgebung

Stellt eine saubere Schnittstelle für KI-Agenten bereit:

  env = MosaicEnv()
  state, info = env.reset()           # neues Spiel, zufällige Wertungsplatten
  actions = env.valid_actions()       # Liste aller gültigen Aktionen
  state, reward, done, info = env.step(action)  # Aktion ausführen

Aktionstypen (alle als Dict):
  {"type": "stone",      "source": ..., "factory_id": ..., "color": ..., "row": ..., "moon_order": [...]}
  {"type": "dome",       "tile_id": ..., "slot_row": ..., "slot_col": ..., "rotation": ...}
  {"type": "dome_stack", "num_drawn": ..., "chosen_id": ..., "slot_row": ..., "slot_col": ..., "rotation": ...}
  {"type": "bonus_chip", "factory_id": ...}
  {"type": "pass"}
  {"type": "tiling",     "player": ..., "pattern_row": ..., "slot_row": ..., "slot_col": ..., "space_index": ...}
  {"type": "use_chips",  "player": ..., "pattern_row": ...}
  {"type": "end_tiling"}

Reward: Punkte-Delta + Potential-Delta des aktiven Spielers nach jedem Schritt.
"""
from __future__ import annotations
import random
import copy

from engine.setup import GameState, setup_new_game, setup_new_round, NUM_ROUNDS
from engine.serializer import serialize_state
from engine.scoring import ALL_SCORING_TILES
from engine.game import Game


class MosaicEnv:
    """
    Trainings-Umgebung für Mosaic-AI KI-Agenten.
    Delegiert alle Spiellogik an game.py — Single Source of Truth.
    """

    def __init__(self, random_scoring_tiles: bool = True):
        self.random_scoring_tiles = random_scoring_tiles
        self.state: GameState | None = None
        self._prev_scores: list[int] = [0, 0]
        self._game = Game()

    # ── Public API ────────────────────────────────────────────────────────────

    def reset(self, seed: int | None = None) -> tuple[dict, dict]:
        first_player = random.choice([0, 1])
        self.state = self._game.start(
            first_player=first_player,
            seed=seed,
            random_scoring=self.random_scoring_tiles
        )

        # Regelkonforme Platzierung: Nicht-Startspieler zuerst, dann Startspieler
        self._place_initial_dome_tile_ai(1 - first_player)
        self._place_initial_dome_tile_ai(first_player)

        self.state.phase = "drafting"
        self.state.current_player = first_player
        self._prev_scores = [p.score for p in self.state.players]

        ids = self.state.scoring_tile_ids
        info = {
            "scoring_tile_ids": ids,
            "scoring_tile_names": [t.name for t in ALL_SCORING_TILES if t.id in ids],
        }
        return serialize_state(self.state), info

    def _place_initial_dome_tile_ai(self, player_idx: int):
        """KI-seitige Startkachel-Platzierung — zufällig. Nur wenn ausstehend."""
        player = self.state.players[player_idx]
        # Keine ausstehende Startkachel (ab Runde 2 oder bereits gelegt)
        if player.start_dome_tile is None:
            return
        if not self.state.dome_display:
            return
        tile     = random.choice(self.state.dome_display)
        row, col = random.choice(player.dome_grid.empty_slots())
        rotation = random.choice([0, 90, 180, 270])
        self._game.apply_start_placement(
            player_idx=player_idx,
            tile_id=tile.tile_id,
            row=row, col=col, rot=rotation
        )

    def valid_actions(self) -> list[dict]:
        if self.state is None:
            return []
        if self.state.phase == "drafting":
            return self._drafting_actions()
        if self.state.phase == "tiling":
            return self._tiling_actions()
        return []

    def step(self, action: dict) -> tuple[dict, float, bool, dict]:
        assert self.state is not None, "reset() zuerst aufrufen"

        from agents.shaping import get_player_potential

        pi = self.state.current_player
        player = self.state.players[pi]

        score_before     = player.score
        potential_before = get_player_potential(player)

        try:
            self._apply_action(action)
        except Exception as e:
            print(f"FATALER FEHLER in MosaicEnv.step: {e}")
            print(f"Ungültiger Zug: {action}")
            #obs = serialize_state(self.state)
            #return obs, -1.0, False, {"error": str(e)}
            raise e

        score_after     = player.score
        potential_after = get_player_potential(player)

        done = self.state.phase in ("end", "final")

        reward  = float(score_after - score_before)
        reward += (potential_after - potential_before)

        info = {
            "phase":  self.state.phase,
            "round":  self.state.round_number,
            "scores": [p.score for p in self.state.players],
        }

        if done:
            score_before_end = player.score
            end_info = self._game._calculate_end_scoring()
            info.update(end_info)
            reward += float(player.score - score_before_end)

        obs = serialize_state(self.state)
        return obs, reward, done, info

    def current_player(self) -> int:
        return self.state.current_player if self.state else 0

    def scores(self) -> list[int]:
        return [p.score for p in self.state.players] if self.state else [0, 0]

    def clone(self) -> "MosaicEnv":
        import pickle
        new_env = MosaicEnv(self.random_scoring_tiles)
        new_env.state = pickle.loads(pickle.dumps(self.state, -1))
        new_env._game.state = new_env.state
        new_env._prev_scores = list(self._prev_scores)
        return new_env

    # ── Aktions-Generatoren ───────────────────────────────────────────────────

    def _drafting_actions(self) -> list[dict]:
        from engine.validation import generate_valid_moves, _validate_place
        from engine.game import generate_dome_moves, generate_bonus_chip_moves

        actions = []
        state = self.state
        p = state.active_player

        for m in generate_valid_moves(state):
            actions.append({
                "type":       "stone",
                "source":     m.take.source.name,
                "factory_id": m.take.factory_id,
                "color":      m.take.color.value,
                "row":        m.place.row_index,
                "moon_order": [t.value for t in m.take.moon_order],
            })

        moon_tops = set()
        for f in state.factories:
            moon_tops |= f.moon_top_colors()
        for c in state.large_factory.moon_colors():
            moon_tops.add(c)
        for color in moon_tops:
            for ri in list(range(6)) + [-1]:
                if _validate_place(state, color, ri) is None:
                    actions.append({
                        "type":       "stone",
                        "source":     "SMALL_FACTORY_MOON",
                        "factory_id": None,
                        "color":      color.value,
                        "row":        ri,
                        "moon_order": [],
                    })
                    break

        if state.round_number < 5:
            for m in generate_dome_moves(state):
                actions.append({
                    "type":     "dome",
                    "tile_id":  m.dome_tile_id,
                    "slot_row": m.slot_row,
                    "slot_col": m.slot_col,
                    "rotation": m.rotation,
                })

            if (p.start_dome_tile is None
                    and p.can_place_dome_tile(state.round_number)
                    and state.dome_tile_pool):
                top = state.dome_tile_pool[0]
                for slot_row in range(3):
                    for slot_col in range(3):
                        if state.players[state.current_player].dome_grid.dome_slots[slot_row][slot_col] is None:
                            for rot in [0, 90, 180, 270]:
                                actions.append({
                                    "type":      "dome_stack",
                                    "num_drawn": 1,
                                    "chosen_id": top.tile_id,
                                    "slot_row":  slot_row,
                                    "slot_col":  slot_col,
                                    "rotation":  rot,
                                })
                            break
                    else:
                        continue
                    break

        for m in generate_bonus_chip_moves(state):
            actions.append({
                "type":       "bonus_chip",
                "factory_id": m.factory_id,
            })

        if not actions:
            actions.append({"type": "pass"})

        return actions

    def _tiling_actions(self) -> list[dict]:
        from engine.game import generate_tiling_actions
        from engine.round_end import can_complete_row_with_chips

        actions = []

        for pi in range(2):
            player = self.state.players[pi]
            for ri, row in enumerate(player.pattern_lines):
                if not row.is_complete:
                    continue
                earlier_open = any(
                    player.pattern_lines[r].is_complete
                    for r in range(ri)
                )
                if earlier_open:
                    break

                tiling = generate_tiling_actions(self.state, pi)
                for a in tiling:
                    if a.pattern_row == ri:
                        actions.append({
                            "type":         "tiling",
                            "player":       pi,
                            "pattern_row":  a.pattern_row,
                            "slot_row":     a.slot_row,
                            "slot_col":     a.slot_col,
                            "space_index":  a.space_index,
                            "dome_tile_id": a.dome_tile_id,
                            "rotation":     a.rotation,
                        })
                break

        for pi in range(2):
            player = self.state.players[pi]
            for ri, row in enumerate(player.pattern_lines):
                if not row.is_complete and can_complete_row_with_chips(player, ri, self.state):
                    actions.append({
                        "type":        "use_chips",
                        "player":      pi,
                        "pattern_row": ri,
                    })

        if not actions:
            actions.append({"type": "end_tiling"})

        return actions

    # ── Aktions-Ausführung ────────────────────────────────────────────────────

    def _apply_action(self, action: dict) -> None:
        """
        Delegiert alle Aktionen an game.apply() — Single Source of Truth.
        Nur end_tiling benötigt zusätzliches KI-spezifisches Handling
        (Startkachel-Platzierung für neue Runde).
        """
        from engine.tile import TileColor
        from engine.moves import (
            Move, TakeAction, PlaceAction, TakeSource,
            PlaceDomeTileMove, DrawFromStackMove, TakeBonusChipMove,
        )

        t = action["type"]
        state = self.state

        if t == "stone":
            color = _color(action["color"])
            src   = TakeSource[action["source"]]
            moon  = [_color(c) for c in action.get("moon_order", [])]
            move  = Move(
                take=TakeAction(
                    source=src,
                    color=color,
                    factory_id=action.get("factory_id"),
                    moon_order=moon,
                ),
                place=PlaceAction(row_index=action["row"]),
            )
            self._game.apply(move)

        elif t == "dome":
            move = PlaceDomeTileMove(
                dome_tile_id=action["tile_id"],
                slot_row=action["slot_row"],
                slot_col=action["slot_col"],
                rotation=action.get("rotation", 0),
            )
            self._game.apply(move)

        elif t == "dome_stack":
            move = DrawFromStackMove(
                num_drawn=action["num_drawn"],
                chosen_id=action["chosen_id"],
                slot_row=action["slot_row"],
                slot_col=action["slot_col"],
                rotation=action.get("rotation", 0),
            )
            self._game.apply(move)

        elif t == "bonus_chip":
            move = TakeBonusChipMove(factory_id=action["factory_id"])
            self._game.apply(move)

        elif t == "pass":
            self._game.apply({"type": "pass"})

        elif t == "tiling":
            # Delegiere an game.apply() — apply_single_tiling ist dort die Source of Truth
            self._game.apply(action)

        elif t == "use_chips":
            # Delegiere an game.apply()
            self._game.apply(action)

        elif t == "end_tiling":
            # game.apply() übernimmt Strafen, Rundenübergang, Logging
            self._game.apply({"type": "end_tiling"})
            # KI-spezifisch: Startkacheln für neue Runde legen
            if state.phase == "drafting":
                self._place_initial_dome_tile_ai(1 - state.current_player)
                self._place_initial_dome_tile_ai(state.current_player)

    def _calculate_end_scoring(self) -> dict:
        """Delegiert an game._calculate_end_scoring() — Single Source of Truth."""
        return self._game._calculate_end_scoring()


def _color(v: str):
    from engine.tile import TileColor
    for c in TileColor:
        if c.value == v:
            return c
    raise ValueError(f"Unbekannte Farbe: {v}")
