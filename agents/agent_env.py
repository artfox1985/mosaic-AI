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
  {"type": "tiling",     "pi": ..., "pattern_row": ..., "slot_row": ..., "slot_col": ..., "space_index": ...}
  {"type": "use_chips",  "pi": ..., "pattern_row": ..., "method": ..., "color": ...}
  {"type": "end_tiling"}

Reward: Punkte-Delta des aktiven Spielers nach jedem Schritt.
"""
from __future__ import annotations
import random
import copy
from typing import Any
import sys
import os

from engine.setup import GameState, setup_new_game, setup_new_round, NUM_ROUNDS
from engine.serializer import serialize_state
from engine.scoring import ALL_SCORING_TILES, calculate_end_scoring
from engine.game import Game

class MosaicEnv:
    """
    Trainings-Umgebung für Mosaic-AI KI-Agenten.

    Unterstützt:
    - Selbstspiel (beide Spieler = KI)
    - Zufällige Wertungsplatten bei jedem Reset (für Generalisierung)
    - Vollständige Aktionsauflistung pro Schritt
    - Reward-Signal als Punkte-Delta
    """

    def __init__(self, random_scoring_tiles: bool = True):
        self.random_scoring_tiles = random_scoring_tiles
        self.state: GameState | None = None
        self._prev_scores: list[int] = [0, 0]
        self._game = Game()

    # ── Public API ────────────────────────────────────────────────────────────

    def reset(self, seed: int | None = None) -> tuple[dict, dict]:
        # 1. Spiel starten
        first_player = random.choice([0, 1])
        self.state = self._game.start(first_player=first_player, seed=seed, random_scoring=self.random_scoring_tiles)
        
        # 2. Regelkonforme Platzierung über die Engine
        self._place_initial_dome_tile_ai(1 - first_player) # Gegner
        self._place_initial_dome_tile_ai(first_player)     # Startspieler
        
        # 3. Spielphase fixieren
        self.state.phase = "drafting"
        self.state.current_player = first_player
        self._prev_scores = [p.score for p in self.state.players]

        # 4. Info-Objekt für KI
        ids = self.state.scoring_tile_ids
        info = {
            "scoring_tile_ids": ids,
            "scoring_tile_names": [t.name for t in ALL_SCORING_TILES if t.id in ids],
        }
        return serialize_state(self.state), info
        
    def _place_initial_dome_tile_ai(self, player_idx: int):
        """
        Nutzt die neue Game-Logik für die Platzierung.
        Die KI wählt hier (zuerst noch zufällig, kann später durch MCTS erweitert werden).
        """
        player = self.state.players[player_idx]
        
        # Falls Display leer, aber noch Kacheln da: Nachfüllen
        while not self.state.dome_display and self.state.dome_tile_pool:
            self.state.dome_display.append(self.state.dome_tile_pool.pop(0))
            
        if not self.state.dome_display:
            return # Keine Kacheln mehr für Startplatzierung verfügbar
        
        # Zufällige Wahl aus dem Display
        tile = random.choice(self.state.dome_display)
        
        # Zufälliger Slot aus den freien Feldern
        empty_slots = player.dome_grid.empty_slots()
        row, col = random.choice(empty_slots)
        rotation = random.choice([0, 90, 180, 270])
        
        # Aufruf der zentralen Logik in Game
        # Wir nutzen _game-Instanz, die in MosaicEnv verfügbar sein sollte
        self._game.apply_start_placement(
            player_idx=player_idx,
            tile_id=tile.tile_id,
            row=row,
            col=col,
            rot=rotation
        )

    def valid_actions(self) -> list[dict]:
        if self.state is None:
            return []
        if self.state.phase == "drafting":
            return self._drafting_actions()
        if self.state.phase == "tiling":
            from engine.game import generate_tiling_actions
            
            # Wir suchen den ERSTEN Spieler, der noch eine Tiling-Aktion hat
            for pi in range(2):
                player = self.state.players[pi]
                
                # Finde die oberste fertige Reihe dieses Spielers
                for ri, row in enumerate(player.pattern_lines):
                    if not row.is_complete:
                        continue
                        
                    tiling = generate_tiling_actions(self.state, pi)
                    
                    # Gibt es GÜLTIGE Aktionen für diese spezielle Reihe?
                    row_actions = [a for a in tiling if a.pattern_row == ri]
                    
                    if len(row_actions) > 0:
                        # BINGO! Dieser Spieler ist jetzt dran.
                        # Wir zwingen die Umgebung, auf diesen Spieler zu wechseln!
                        self.state.active_player_index = pi 
                        
                        actions = []
                        for a in row_actions:
                            actions.append({
                                "type":         "tiling",
                                "player":       pi,  # <-- WICHTIG: "player" statt "pi"
                                "pattern_row":  a.pattern_row,
                                "slot_row":     a.slot_row,
                                "slot_col":     a.slot_col,
                                "space_index":  a.space_index,
                                "dome_tile_id": getattr(a, "dome_tile_id", None),
                                "rotation":     getattr(a, "rotation", 0)
                            })
                            
                        # SOFORT ZURÜCKGEBEN! 
                        # Wir mischen niemals Züge von Spieler 1 und 2 in derselben Liste!
                        return actions 
                        
                    # Wenn die Reihe zwar voll ist, aber keine Aktionen generiert wurden 
                    # (z.B. unplatzierbar), brechen wir die Reihen-Suche ab.
                    break 
            
            # Wenn die gesamte Schleife durchläuft und NIEMAND mehr eine Aktion hat:
            return [{"type": "end_tiling"}]
        return []

    def step(self, action: dict) -> tuple[dict, float, bool, dict]:
        assert self.state is not None, "reset() zuerst aufrufen"

        from agents.shaping import get_player_potential

        pi = self.state.current_player
        player = self.state.players[pi]
        
        # 1. Zustand VOR dem Zug merken
        score_before = player.score
        potential_before = get_player_potential(player)

        # 2. Aktion ausführen
        try:
            self._apply_action(action)
        except Exception as e:
            obs = serialize_state(self.state)
            return obs, -1.0, False, {"error": str(e)}

        # 3. Zustand NACH dem Zug abfragen
        score_after = player.score
        potential_after = get_player_potential(player)
        
        done = self.state.phase in ("end", "final")

        # 4. MATHEMATISCH PERFEKTES REWARD SHAPING
        reward = 0.0
        
        # A: Echte Punkte (oder echte Minuspunkte) aus der Game-Engine
        reward += float(score_after - score_before)
        
        # B: Shaping-Delta (Hat sich mein abstraktes Potenzial verbessert?)
        reward += (potential_after - potential_before)

        # 5. Finale Spielende-Punkte
        info = {
            "phase": self.state.phase,
            "round": self.state.round_number,
            "scores": [p.score for p in self.state.players],
        }

        if done:
            score_before_end = player.score
            end_info = self._calculate_end_scoring()
            info.update(end_info)
            reward += float(player.score - score_before_end)

        obs = serialize_state(self.state)
        return obs, reward, done, info

    def current_player(self) -> int:
        if self.state is None:
            return 0
        return self.state.current_player

    def scores(self) -> list[int]:
        if self.state is None:
            return [0, 0]
        return [p.score for p in self.state.players]

    def clone(self) -> "MosaicEnv":
        import pickle
        new_env = MosaicEnv(self.random_scoring_tiles)
        new_env.state = pickle.loads(pickle.dumps(self.state, -1))
        new_env._game.state = new_env.state   # ← State synchronisieren
        new_env._prev_scores = list(self._prev_scores)
        return new_env

    # ── Aktions-Generatoren ───────────────────────────────────────────────────

    def _drafting_actions(self) -> list[dict]:
        from engine.validation import generate_valid_moves
        from engine.game import generate_dome_moves, generate_bonus_chip_moves
        from engine.serializer import _serialize_valid_moves

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

        from engine.validation import _validate_place
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

        # KORREKTUR: Aktion A (Kuppelplatten) nur erlaubt, wenn wir NICHT in Runde 5 sind
        if state.round_number < 5:
            # Aus der Auslage
            for m in generate_dome_moves(state):
                actions.append({
                    "type":     "dome",
                    "tile_id":  m.dome_tile_id,
                    "slot_row": m.slot_row,
                    "slot_col": m.slot_col,
                    "rotation": m.rotation,
                })

            # Vom Stapel
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

        actions = []

        # 1. Normale Tiling-Aktionen generieren
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
                            "type":        "tiling",
                            "pi":          pi,
                            "pattern_row": a.pattern_row,
                            "slot_row":    a.slot_row,
                            "slot_col":    a.slot_col,
                            "space_index": a.space_index,
                            "dome_tile_id": a.dome_tile_id,   # ← None wenn Slot schon belegt, sonst Kachel-ID
                            "rotation":    a.rotation,         # ← 0 wenn Slot schon belegt
                        })
                break 

         # 2. NEU: Bonus-Chips eintauschen generieren (Nur komplette Reihen-Auffüllung!)
        from engine.round_end import can_complete_row_with_chips
        
        for pi in range(2):
            player = self.state.players[pi]
            for ri, row in enumerate(player.pattern_lines):
                # Die Funktion aus deiner round_end.py prüft alle Regeln:
                # - Ist mind. 1 Fliese da?
                # - Sind genug Chips für den GANZEN Rest da (Paare oder Drillinge)?
                if not row.is_complete and can_complete_row_with_chips(player, ri):
                    actions.append({
                        "type": "use_chips",
                        "pi": pi,
                        "pattern_row": ri
                    })

        # Wenn absolut nichts gemacht werden kann → end_tiling
        if not actions:
            actions.append({"type": "end_tiling"})

        return actions

    # ── Aktions-Ausführung ────────────────────────────────────────────────────

    def _apply_action(self, action: dict) -> None:
        from engine.tile import TileColor
        from engine.moves import (
            Move, TakeAction, PlaceAction, TakeSource,
            PlaceDomeTileMove, DrawFromStackMove, TakeBonusChipMove,
        )
        from engine.validation import validate_move
        from engine.execution import execute_move
        from engine.game import (
            validate_dome_move, execute_dome_move,
            validate_draw_from_stack, execute_draw_from_stack,
            validate_take_bonus_chip, execute_take_bonus_chip,
            check_drafting_complete,
        )
        from engine.round_end import (
            TilingAction, validate_tiling_action, execute_full_tiling,
            score_placed_tile, process_unplaceable_rows, score_penalty,
        )

        t = action["type"]
        state = self.state

        if t == "stone":
            color = _color(action["color"])
            src = TakeSource[action["source"]]
            if src == TakeSource.SMALL_FACTORY_MOON and action.get("factory_id") is None:
                self._execute_aktion_c(color, action["row"])
            else:
                moon = [_color(c) for c in action.get("moon_order", [])]
                move = Move(
                    take=TakeAction(
                        source=src,
                        color=color,
                        factory_id=action.get("factory_id"),
                        moon_order=moon,
                    ),
                    place=PlaceAction(row_index=action["row"]),
                )
                err = validate_move(state, move)
                if err: raise ValueError(err)
                execute_move(state, move)
                state.switch_player()

        elif t == "dome":
            move = PlaceDomeTileMove(
                dome_tile_id=action["tile_id"],
                slot_row=action["slot_row"],
                slot_col=action["slot_col"],
                rotation=action.get("rotation", 0),
            )
            err = validate_dome_move(state, move)
            if err: raise ValueError(err)
            execute_dome_move(state, move)
            state.switch_player()

        elif t == "dome_stack":
            move = DrawFromStackMove(
                num_drawn=action["num_drawn"],
                chosen_id=action["chosen_id"],
                slot_row=action["slot_row"],
                slot_col=action["slot_col"],
                rotation=action.get("rotation", 0),
            )
            err = validate_draw_from_stack(state, move)
            if err: raise ValueError(err)
            execute_draw_from_stack(state, move)
            state.switch_player()

        elif t == "bonus_chip":
            from engine.moves import TakeBonusChipMove
            move = TakeBonusChipMove(factory_id=action["factory_id"])
            err = validate_take_bonus_chip(state, move)
            if err: raise ValueError(err)
            execute_take_bonus_chip(state, move)
            state.switch_player()

        elif t == "pass":
            state.switch_player()

        elif t == "tiling":
            pi = action["player"]
            ta = TilingAction(
                pattern_row=action["pattern_row"],
                slot_row=action["slot_row"],
                slot_col=action["slot_col"],
                space_index=action["space_index"],
                dome_tile_id=action.get("dome_tile_id"),  # ← None = Slot bereits belegt
                rotation=action.get("rotation", 0),
            )
            err = validate_tiling_action(state, pi, ta)
            if err: raise ValueError(err)
            execute_full_tiling(state, pi, ta)

        # NEU: Chips ausgeben und in virtuelle Fliese umwandeln
        elif t == "use_chips":
            pi = action["player"]
            ri = action["pattern_row"]
            player = state.players[pi]
            
            from engine.round_end import apply_bonus_chips_to_row
            
            # Diese Funktion aus deinem Backend zieht automatisch die richtigen Chips 
            # ab und füllt die Musterreihe in einem Rutsch komplett auf!
            success = apply_bonus_chips_to_row(player, ri)
            
            if not success:
                raise ValueError(f"Konnte Reihe {ri+1} nicht mit Chips komplettieren!")
                
            state.log_event(
                f"🎫 {player.name} komplettiert Reihe {ri + 1} vollständig mit Bonus-Chips!"
            )
            
            # WICHTIG: Kein state.switch_player() ! Man darf direkt die nächste Tiling-Aktion machen.

        elif t == "end_tiling":
            for player in state.players:
                process_unplaceable_rows(player, state.tower, state)
            for player in state.players:
                pen = score_penalty(player)
                if pen < 0:
                    player.apply_score(pen)
                    broken = player.clear_broken()
                    state.tower.add(broken)
            
            if state.round_number >= NUM_ROUNDS:
                state.phase = "end"
            else:
                while len(state.dome_display) < 3 and state.dome_tile_pool:
                    state.dome_display.append(state.dome_tile_pool.pop(0))
                setup_new_round(state)
                self._place_initial_dome_tile_ai(1 - state.current_player)
                self._place_initial_dome_tile_ai(state.current_player)

        if state.phase == "drafting":
            self._check_phase_transition()

    def _check_phase_transition(self) -> None:
        from engine.round_end import check_drafting_complete
        if check_drafting_complete(self.state):
            self.state.phase = "tiling"

    def _execute_aktion_c(self, color, row: int) -> None:
        from engine.tile import TileColor
        from engine.execution import _execute_place

        state = self.state
        p = state.active_player
        taken = []
        got_marker = False

        for f in state.factories:
            if color in f.moon_top_colors():
                taken += f.take_from_moon(color)

        if color in state.large_factory.moon_colors():
            tiles, marker = state.large_factory.take_from_moon(color)
            taken += tiles
            if marker:
                got_marker = True

        if not taken:
            raise ValueError(f"Keine {color.value}-Fliesen im Mondbereich")

        if got_marker:
            p.holds_first_player_marker = True
            state.first_player_next_round = state.current_player

        _execute_place(state, taken, color, row)
        state.switch_player()

    def _calculate_end_scoring(self) -> dict:
        from engine.scoring import calculate_end_scoring
        results = {}
        for pi, player in enumerate(self.state.players):
            res = calculate_end_scoring(player, self.state.scoring_tile_ids)
            player.apply_score(res["total"])
            results[pi] = res

            # Logging der Wertungsplatten
            self.state.log_event(
                f"🏆 {player.name}: Endwertung +{res['total']} Pkt "
                f"→ Gesamt: {player.score} Pkt"
            )
            for tid, detail in res.items():
                if tid == "total":
                    continue
                self.state.log_event(
                    f"   {detail['emoji']} {detail['name']}: {detail['score']:+d} Pkt"
                )

        self.state.phase = "final"
        return {"end_scoring": results}

def _color(v: str):
    from engine.tile import TileColor
    for c in TileColor:
        if c.value == v:
            return c
    raise ValueError(f"Unbekannte Farbe: {v}")
