"""
Mosaic-AI — KI-Agenten

RandomAgent:   Wählt zufällig aus allen gültigen Aktionen.
GreedyAgent:   Wählt die Aktion mit dem höchsten sofortigen Reward.

Beide Agenten implementieren dasselbe Interface:
    agent.choose(actions, observation) -> dict

Training:
    results = run_episode(env, agent0, agent1)
    stats = run_training(n_episodes=1000)
"""
from __future__ import annotations
import random
import time
from typing import Any

from agents.agent_env import MosaicEnv


# ── Agent-Interface ───────────────────────────────────────────────────────────

class BaseAgent:
    def choose(self, actions: list[dict], obs: dict) -> dict:
        raise NotImplementedError

    def on_episode_end(self, result: dict) -> None:
        """Callback am Ende einer Episode — für Lernagenten."""
        pass


class RandomAgent(BaseAgent):
    """Wählt gleichmäßig zufällig aus allen gültigen Aktionen."""
    def choose(self, actions: list[dict], obs: dict) -> dict:
        return random.choice(actions)


class GreedyAgent(BaseAgent):
    """
    Ein echter Greedy-Agent: 
    Testet alle validen Züge, schaut sich den Reward an und 
    wählt den Zug mit dem sofort höchsten Reward.
    """
    def choose(self, actions: list[dict], obs: dict) -> dict:
        # Wir benötigen Zugriff auf das Environment, um die Züge zu testen.
        # Da BaseAgent kein env standardmäßig hat, holen wir es uns aus 
        # der Observation (wenn dort wie in Mosaic-AI üblich das env liegt)
        # oder setzen es über eine set_env Methode.
        env = obs.get("_env")
        if env is None:
            # Fallback falls kein env vorhanden
            return random.choice(actions)

        best_action = None
        best_reward = -float('inf')
        
        # Teste alle Züge
        for action in actions:
            # Wir klonen das Environment, um den Zustand nicht wirklich zu verändern
            test_env = env.clone()
            
            # Führe die Aktion im geklonten Env aus
            _, reward, _, _ = test_env.step(action)
            
            # Suche das Maximum
            if reward > best_reward:
                best_reward = reward
                best_action = action
            elif reward == best_reward:
                # Bei Gleichstand zufällig entscheiden
                if random.random() < 0.5:
                    best_action = action
                    
        return best_action if best_action is not None else random.choice(actions)


# ── Episode ───────────────────────────────────────────────────────────────────

def run_episode(
    env: MosaicEnv,
    agents: list[BaseAgent],
    seed: int | None = None,
    max_steps: int = 500,
    verbose: bool = False,
) -> dict:
    """
    Führt eine vollständige Episode durch.

    Returns:
        {
          "scores": [int, int],
          "winner": 0 | 1 | -1 (Unentschieden),
          "steps": int,
          "rewards": [float, float],
          "scoring_tile_ids": [...],
          "duration_s": float,
        }
    """
    t0 = time.time()
    obs, info = env.reset(seed=seed)
    total_rewards = [0.0, 0.0]
    steps = 0

    while steps < max_steps:
        actions = env.valid_actions()
        if not actions:
            break

        pi = env.current_player()
        action = agents[pi].choose(actions, obs)

        obs, reward, done, step_info = env.step(action)
        total_rewards[pi] += reward
        steps += 1

        if verbose and steps % 20 == 0:
            scores = env.scores()
            print(f"  Step {steps:3d} | P{pi} {action['type']:12s} | "
                  f"reward={reward:+.1f} | scores={scores}")

        if done:
            break

    scores = env.scores()
    
    # 1. Sieger nach Punkten
    if scores[0] > scores[1]:
        winner = 0
    elif scores[1] > scores[0]:
        winner = 1
    else:
        # 2. TIE-BREAKER: Bei Gleichstand gewinnt der Besitzer des Startspieler-Markers!
        # Einer der beiden Spieler muss ihn zwingend haben.
        if env.state.players[0].holds_first_player_marker:
            winner = 0
        else:
            winner = 1

    result = {
        "scores":           scores,
        "winner":           winner,
        "steps":            steps,
        "rewards":          total_rewards,
        "scoring_tile_ids": info.get("scoring_tile_ids", []),
        "scoring_names":    info.get("scoring_tile_names", []),
        "duration_s":       round(time.time() - t0, 3),
    }

    for agent in agents:
        agent.on_episode_end(result)

    return result


# ── Training-Loop ─────────────────────────────────────────────────────────────

def run_training(
    n_episodes: int = 100,
    agents: list[BaseAgent] | None = None,
    random_scoring_tiles: bool = True,
    verbose_every: int = 10,
    seed_start: int | None = None,
) -> dict:
    """
    Führt n_episodes vollständige Spiele durch.

    Args:
        n_episodes:            Anzahl Partien
        agents:                [agent0, agent1] — Standard: beide RandomAgent
        random_scoring_tiles:  Zufällige Wertungsplatten pro Spiel
        verbose_every:         Gibt alle N Episoden eine Zusammenfassung aus
        seed_start:            Startseed (None = echte Zufälligkeit)

    Returns:
        Statistiken über alle Episoden
    """
    if agents is None:
        agents = [RandomAgent(), RandomAgent()]

    env = MosaicEnv(random_scoring_tiles=random_scoring_tiles)

    wins = [0, 0, 0]  # [p0_wins, p1_wins, draws]
    all_scores = [[], []]
    all_steps = []
    all_durations = []
    scoring_tile_usage: dict[int, int] = {t.id: 0 for t in __import__(
        'engine.scoring', fromlist=['ALL_SCORING_TILES']
    ).ALL_SCORING_TILES}

    t_total = time.time()

    for ep in range(n_episodes):
        seed = (seed_start + ep) if seed_start is not None else None
        result = run_episode(env, agents, seed=seed)

        # Stats sammeln
        w = result["winner"]
        wins[w if w >= 0 else 2] += 1
        all_scores[0].append(result["scores"][0])
        all_scores[1].append(result["scores"][1])
        all_steps.append(result["steps"])
        all_durations.append(result["duration_s"])
        for tid in result["scoring_tile_ids"]:
            scoring_tile_usage[tid] = scoring_tile_usage.get(tid, 0) + 1

        if verbose_every and (ep + 1) % verbose_every == 0:
            _print_progress(ep + 1, n_episodes, wins, all_scores, all_steps, all_durations)

    total_time = time.time() - t_total

    stats = {
        "episodes":       n_episodes,
        "wins":           {"p0": wins[0], "p1": wins[1], "draw": wins[2]},
        "win_rate":       {"p0": wins[0]/n_episodes, "p1": wins[1]/n_episodes},
        "avg_scores":     {"p0": _avg(all_scores[0]), "p1": _avg(all_scores[1])},
        "avg_steps":      _avg(all_steps),
        "avg_duration_s": _avg(all_durations),
        "total_time_s":   round(total_time, 1),
        "scoring_tile_usage": scoring_tile_usage,
    }

    print(f"\n{'═'*50}")
    print(f"Training abgeschlossen: {n_episodes} Episoden in {total_time:.1f}s")
    print(f"  P0 Siege: {wins[0]} ({wins[0]/n_episodes:.1%})")
    print(f"  P1 Siege: {wins[1]} ({wins[1]/n_episodes:.1%})")
    print(f"  Unentschieden: {wins[2]}")
    print(f"  Ø Punkte: P0={_avg(all_scores[0]):.1f}  P1={_avg(all_scores[1]):.1f}")
    print(f"  Ø Schritte: {_avg(all_steps):.0f}")
    print(f"  Wertungsplatten-Nutzung: {scoring_tile_usage}")

    return stats


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _avg(lst: list) -> float:
    return sum(lst) / len(lst) if lst else 0.0


def _print_progress(ep, total, wins, all_scores, all_steps, durations):
    last = min(10, ep)
    recent_scores_0 = all_scores[0][-last:]
    recent_scores_1 = all_scores[1][-last:]
    print(
        f"Ep {ep:4d}/{total} | "
        f"P0:{wins[0]:4d}  P1:{wins[1]:4d}  D:{wins[2]:3d} | "
        f"Ø Pkt(letzte {last}): P0={_avg(recent_scores_0):.1f} P1={_avg(recent_scores_1):.1f} | "
        f"Ø {_avg(all_steps[-last:]):.0f} Schritte | "
        f"{_avg(durations[-last:])*1000:.0f}ms/Ep"
    )
