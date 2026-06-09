"""
Mosaic-AI — KI-Agenten-Umgebung

Stellt eine saubere Schnittstelle für KI-Agenten bereit:

  env = MosaicEnv()
  state, info = env.reset()           # neues Spiel, zufällige Wertungsplatten
  actions = env.valid_actions()       # Liste aller gültigen Aktionen
  state, reward, done, info = env.step(action)  # Aktion ausführen

Aktionstypen (alle als Dict — abstrakte Darstellung ohne State-Snapshots):
  {"type": "stone",      "factory_index": 0-5, "color": ..., "row": ...}
      factory_index: 0-3=kleine Fabriken F1-F4, 4=Große Fabrik, 5=Mondaktion (Aktion C)
  {"type": "dome",       "display_index": 0-2, "slot_row": ..., "slot_col": ..., "rotation": ...}
      display_index: Position im Kuppel-Display (0=links, 1=mitte, 2=rechts)
  {"type": "dome_stack", "num_drawn": ..., "slot_row": ..., "slot_col": ..., "rotation": ...}
  {"type": "bonus_chip", "factory_index": 0-3}
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
        """
        KI-seitige Startkachel-Platzierung via evaluate_state.
        Wird im Self-Play für MCTS und AlphaZero verwendet.
        Für AlphaZero im Server übernimmt /api/ai/start_tile diese Aufgabe.
        """
        player = self.state.players[player_idx]
        if player.start_dome_tile is None:
            return
        if not self.state.dome_display:
            return

        empty_slots = player.dome_grid.empty_slots()
        if not empty_slots:
            return

        try:
            import copy
            from agents.mcts import evaluate_state

            best_score = -float('inf')
            best_tile  = self.state.dome_display[0]
            best_row, best_col, best_rot = empty_slots[0][0], empty_slots[0][1], 0

            for tile in self.state.dome_display:
                for (r, c) in empty_slots:
                    for rot in [0, 90, 180, 270]:
                        test_game = copy.deepcopy(self._game)
                        try:
                            test_game.apply_start_placement(
                                player_idx=player_idx,
                                tile_id=tile.tile_id,
                                row=r, col=c, rot=rot,
                            )
                            score = evaluate_state(test_game.state).get(player_idx, 0.0)
                            if score > best_score:
                                best_score = score
                                best_tile  = tile
                                best_row, best_col, best_rot = r, c, rot
                        except Exception:
                            continue

            self._game.apply_start_placement(
                player_idx=player_idx,
                tile_id=best_tile.tile_id,
                row=best_row, col=best_col, rot=best_rot,
            )
        except Exception:
            # Fallback: zufällig
            tile     = random.choice(self.state.dome_display)
            row, col = random.choice(empty_slots)
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
            obs = serialize_state(self.state)
            return obs, -1.0, False, {"error": str(e)}

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

        # Temporär teure/unnötige Felder auslagern:
        # - log: wird in Simulationen nicht gebraucht
        # - dome_tile_pool: großes Objekt, wird beim Clone geteilt (read-mostly)
        #   und bei Bedarf neu gesetzt
        state = self.state
        saved_log   = state.log
        saved_pool  = state.dome_tile_pool
        saved_chips = state.bonus_chip_pool

        state.log            = []
        state.dome_tile_pool  = []
        state.bonus_chip_pool = []

        new_env.state = pickle.loads(pickle.dumps(state, -1))

        # Originale wiederherstellen
        state.log            = saved_log
        state.dome_tile_pool  = saved_pool
        state.bonus_chip_pool = saved_chips

        # Shared references für read-mostly Objekte (Copy-on-Write)
        new_env.state.dome_tile_pool  = saved_pool
        new_env.state.bonus_chip_pool = saved_chips
        new_env.state._pool_shared    = True

        new_env._game.state  = new_env.state
        new_env._prev_scores = list(self._prev_scores)
        return new_env

    # ── Aktions-Generatoren ───────────────────────────────────────────────────

    def _drafting_actions(self) -> list[dict]:
        from engine.validation import generate_valid_moves, _validate_place
        from engine.game import generate_dome_moves, generate_bonus_chip_moves

        actions = []
        state = self.state
        p = state.active_player

        # factory_index Mapping: 0-3 = kleine Fabriken (F1-F4), 4 = GF, 5 = Mondaktion
        factory_id_to_index = {f.factory_id: i for i, f in enumerate(state.factories)}

        for m in generate_valid_moves(state):
            src = m.take.source.name
            if src == "SMALL_FACTORY_MOON" and m.take.factory_id is None:
                f_idx = 5  # Aktion C: globaler Mondaktion
            elif src == "LARGE_FACTORY_SUN":
                f_idx = 4
            else:
                f_idx = factory_id_to_index.get(m.take.factory_id, 0)
            actions.append({
                "type":          "stone",
                "factory_index": f_idx,
                "color":         m.take.color.value,
                "row":           m.place.row_index,
            })

        if state.round_number < 5:
            for m in generate_dome_moves(state):
                # display_index: Position der Kachel im Display
                display_index = next(
                    (i for i, t in enumerate(state.dome_display)
                     if t.tile_id == m.dome_tile_id), 0
                )
                actions.append({
                    "type":          "dome",
                    "display_index": display_index,
                    "slot_row":      m.slot_row,
                    "slot_col":      m.slot_col,
                    "rotation":      m.rotation,
                })

            if (p.start_dome_tile is None
                    and p.can_place_dome_tile(state.round_number)
                    and state.dome_tile_pool):
                for slot_row in range(3):
                    for slot_col in range(3):
                        if state.players[state.current_player].dome_grid.dome_slots[slot_row][slot_col] is None:
                            for rot in [0, 90, 180, 270]:
                                actions.append({
                                    "type":      "dome_stack",
                                    "slot_row":  slot_row,
                                    "slot_col":  slot_col,
                                    "rotation":  rot,
                                })
                            break
                    else:
                        continue
                    break

        for m in generate_bonus_chip_moves(state):
            f_idx = factory_id_to_index.get(m.factory_id, 0)
            actions.append({
                "type":          "bonus_chip",
                "factory_index": f_idx,
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
            tiling_actions = generate_tiling_actions(self.state, pi)
            placeable_rows = {a.pattern_row for a in tiling_actions}
            for ri, row in enumerate(player.pattern_lines):
                if row.is_complete:
                    continue
                # Reihenfolge: keine frühere platzierbare Reihe noch offen
                earlier_open = any(
                    player.pattern_lines[r].is_complete and r in placeable_rows
                    for r in range(ri)
                )
                if earlier_open:
                    break
                # Chips verfügbar und Reihe vollmachbar?
                if not can_complete_row_with_chips(player, ri, self.state):
                    continue
                # Nach Vollmachen platzierbar? Prüfe Kuppelslot
                color    = row.color
                dome_row = ri // 2
                space_row = ri % 2
                valid_si = [space_row * 2, space_row * 2 + 1]
                grid = player.dome_grid
                has_slot = any(
                    slot is not None and
                    any(
                        not slot.spaces[si].is_filled and
                        not slot.spaces[si].is_locked and
                        slot.spaces[si].accepts(color)
                        for si in valid_si
                    )
                    for slot in [grid.dome_slots[dome_row][sc] for sc in range(3)]
                )
                if has_slot:
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

        # Copy-on-Write: geteilte Objekte kopieren wenn sie modifiziert werden
        if getattr(self.state, '_pool_shared', False):
            if t in ("dome", "dome_stack"):
                import pickle as _pk
                self.state.dome_tile_pool = _pk.loads(_pk.dumps(self.state.dome_tile_pool, -1))
            if t == "bonus_chip":
                import pickle as _pk
                self.state.bonus_chip_pool = _pk.loads(_pk.dumps(self.state.bonus_chip_pool, -1))
            self.state._pool_shared = False

        if t == "stone":
            color    = _color(action["color"])
            f_idx    = action.get("factory_index", 0)

            # factory_index → konkrete Fabrik + Source + moon_order aus aktuellem State
            if f_idx == 5:
                # Aktion C: globaler Mondaktion
                src  = TakeSource.SMALL_FACTORY_MOON
                f_id = None
                moon = []
            elif f_idx == 4:
                # Große Fabrik Sonnenseite
                src  = TakeSource.LARGE_FACTORY_SUN
                f_id = None
                moon_logits = getattr(self, '_moon_logits', None)
                moon = _strategic_moon_order(
                    [t for t in state.large_factory.sun_tiles if t != color],
                    state, moon_logits
                )
            else:
                # Kleine Fabrik (Index 0-3 → factory_id 1-4)
                factories = state.factories
                factory   = factories[f_idx] if f_idx < len(factories) else factories[0]
                src  = TakeSource.SMALL_FACTORY_SUN
                f_id = factory.factory_id
                moon_logits = getattr(self, '_moon_logits', None)
                moon = _strategic_moon_order(
                    [t for t in factory.sun_tiles if t != color],
                    state, moon_logits
                )

            move = Move(
                take=TakeAction(source=src, color=color, factory_id=f_id, moon_order=moon),
                place=PlaceAction(row_index=action["row"]),
            )
            self._game.apply(move)

        elif t == "dome":
            # display_index → aktuelle Kachel aus Display holen
            d_idx   = action.get("display_index", 0)
            display = state.dome_display
            if not display:
                return
            tile_id = display[min(d_idx, len(display) - 1)].tile_id
            move = PlaceDomeTileMove(
                dome_tile_id=tile_id,
                slot_row=action["slot_row"],
                slot_col=action["slot_col"],
                rotation=action.get("rotation", 0),
            )
            self._game.apply(move)

        elif t == "dome_stack":
            if not state.dome_tile_pool:
                return
            import copy
            from agents.mcts import evaluate_state

            slot_row = action["slot_row"]
            slot_col = action["slot_col"]
            rotation = action.get("rotation", 0)
            pi       = state.current_player

            # Implizite Strategie: ziehe Platten bis keine bessere mehr kommt.
            # Kosten: -1 Pkt je gezogener Platte (ab der 2. Platte).
            # Stoppe wenn Kosten > erwarteter Gewinn durch bessere Platte.
            best_score    = -float('inf')
            best_tile_id  = state.dome_tile_pool[0].tile_id
            best_num      = 1
            prev_score    = -float('inf')

            for num_drawn in range(1, len(state.dome_tile_pool) + 1):
                tile = state.dome_tile_pool[num_drawn - 1]
                try:
                    test_game = copy.deepcopy(self._game)
                    test_move = DrawFromStackMove(
                        num_drawn=num_drawn,
                        chosen_id=tile.tile_id,
                        slot_row=slot_row,
                        slot_col=slot_col,
                        rotation=rotation,
                    )
                    test_game.apply(test_move)
                    score = evaluate_state(test_game.state).get(pi, 0.0)

                    # Kosten der zusätzlichen Platten einrechnen (-1 Pkt ab Platte 2)
                    cost = (num_drawn - 1) * 0.01  # normalisiert (~1 Pkt)
                    net_score = score - cost

                    if net_score > best_score:
                        best_score   = net_score
                        best_tile_id = tile.tile_id
                        best_num     = num_drawn
                        prev_score   = score
                    elif score < prev_score - 0.05:
                        # Stapel wird schlechter → aufhören
                        break
                except Exception:
                    break

            move = DrawFromStackMove(
                num_drawn=best_num,
                chosen_id=best_tile_id,
                slot_row=slot_row,
                slot_col=slot_col,
                rotation=rotation,
            )
            self._game.apply(move)

        elif t == "bonus_chip":
            # factory_index → erste verfügbare Fabrik mit Chip
            f_idx     = action.get("factory_index", 0)
            factories = state.factories
            # Versuche zuerst die gewünschte Fabrik
            factory   = factories[f_idx] if f_idx < len(factories) else None
            if factory is None or not factory.bonus_chip_revealed or not factory.bonus_chip:
                # Fallback: erste Fabrik mit aufgedecktem Chip
                factory = next(
                    (f for f in factories if f.bonus_chip_revealed and f.bonus_chip), None
                )
            if factory is None:
                return
            move = TakeBonusChipMove(factory_id=factory.factory_id)
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


COLORS_ORDER = ['blau', 'gelb', 'rot', 'schwarz', 'türkis']

def _strategic_moon_order(moon_stones, state, moon_logits=None):
    """
    Sortiert die Mondsteine strategisch.
    Wenn moon_logits vorhanden (vom Moon-Order Head des Netzes):
      → Hoher Logit-Wert = Farbe tief im Stapel (defensiv)
    Sonst Fallback: seltenste Farben tief.
    """
    if len(moon_stones) <= 1:
        return moon_stones

    if moon_logits is not None:
        def net_rank(stone):
            v = stone.value if hasattr(stone, 'value') else str(stone)
            idx = COLORS_ORDER.index(v) if v in COLORS_ORDER else 0
            return -moon_logits[idx]
        return sorted(moon_stones, key=net_rank)

    # Heuristik-Fallback: seltenste Farben nach unten
    color_counts = {}
    for factory in state.factories:
        for stack in factory.moon_stacks:
            if stack:
                v = stack[-1].value if hasattr(stack[-1], 'value') else str(stack[-1])
                color_counts[v] = color_counts.get(v, 0) + 1
    for stone in getattr(state.large_factory, 'moon_pool', []):
        v = stone.value if hasattr(stone, 'value') else str(stone)
        color_counts[v] = color_counts.get(v, 0) + 1

    def rarity(stone):
        v = stone.value if hasattr(stone, 'value') else str(stone)
        return color_counts.get(v, 0)
    return sorted(moon_stones, key=rarity)


def _color(v: str):
    from engine.tile import TileColor
    for c in TileColor:
        if c.value == v:
            return c
    raise ValueError(f"Unbekannte Farbe: {v}")