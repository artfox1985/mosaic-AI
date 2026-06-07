"""
archive/self_play_v0.py — MCTS-basierte Self-Play Datengenerierung

Verwendet HeuristicMCTSAgent (ohne neuronales Netz) um Trainingsdaten
für die erste AlphaZero-Generation zu erzeugen.

Verwendung:
    python -m archive.self_play_v0 --games 1500 --sims 50 --version v0
"""
import os
import time
import copy
import pickle
import random
from datetime import datetime
import argparse

from agents.agent_env import MosaicEnv
from agents.mcts import MCTSNode, HeuristicMCTSAgent


class SelfPlayAgent(HeuristicMCTSAgent):
    """
    Erweitert den Heuristik-Agenten für Self-Play Datengenerierung.
    Führt alle Simulationen durch bevor Policy und Aktion bestimmt werden.
    """
    def __init__(self, simulations=50, rollout_depth=5, **kwargs):
        super().__init__(simulations=simulations, rollout_depth=rollout_depth, max_actions=10, **kwargs)

    def search_and_get_policy(self, env, actions, temp=1.0):
        """
        Führt MCTS-Suche durch und gibt (aktion, policy) zurück.
        Policy enthält Visit-Wahrscheinlichkeiten aller Kindknoten.
        Temperature steuert wie stark die Policy geglättet wird:
          temp=1.0 → proportional zu Visits (explorativ)
          temp=0.5 → stärker auf häufig besuchte Aktionen fokussiert
          temp=0.1 → fast deterministisch
          temp=0.0 → argmax (immer die meistbesuchte Aktion)
        """
        pi = env.current_player()
        sampled = self._sample_actions(actions)

        root = MCTSNode(
            action=None,
            parent=None,
            untried_actions=sampled,
            player_who_acted=pi
        )
        root.visits = 1

        # ── Alle Simulationen durchführen ────────────────────────────────────
        for _ in range(self.simulations):
            sim_env = env.clone()
            node = self._select(root, sim_env)
            node = self._expand(node, sim_env)
            result = self._rollout(sim_env)
            self._backpropagate(node, result, pi)

        # ── Policy aus Visit-Counts berechnen ─────────────────────────────────
        if not root.children:
            # Kein Kind expandiert — Fallback
            action = random.choice(actions)
            return action, [{"action": action, "prob": 1.0}]

        if temp == 0.0:
            # Deterministisch: beste Aktion mit Wahrscheinlichkeit 1.0
            best = max(root.children, key=lambda c: c.visits)
            policy = [
                {"action": c.action, "prob": 1.0 if c is best else 0.0}
                for c in root.children
            ]
            # Nur Einträge mit prob > 0 behalten
            policy = [p for p in policy if p["prob"] > 0.0]
            return best.action, policy

        # Temperature-gewichtete Policy
        total_visits = sum(child.visits for child in root.children)
        if total_visits == 0:
            action = random.choice(actions)
            return action, [{"action": action, "prob": 1.0}]

        # Visits^(1/temp) berechnen → normalisieren
        raw = [(c, c.visits ** (1.0 / temp)) for c in root.children]
        total_raw = sum(r for _, r in raw)
        policy = [
            {"action": c.action, "prob": r / total_raw}
            for c, r in raw
        ]

        # Zugauswahl via Sampling
        probs = [p["prob"] for p in policy]
        chosen_action = random.choices(
            [p["action"] for p in policy],
            weights=probs
        )[0]

        return chosen_action, policy


def play_one_game(agent, game_index):
    """Spielt genau ein Spiel und zeichnet alle Daten auf."""
    env = MosaicEnv()
    obs, info = env.reset()

    history = []
    steps = 0
    temperature_moves = 30   # Exploration in den ersten 30 Zügen

    while True:
        actions = env.valid_actions()
        if not actions:
            break

        current_player = env.current_player()

        # Sanfter Temperature-Übergang
        if steps < temperature_moves:
            temp = 1.0    # Exploration
        elif steps < 60:
            temp = 0.5    # Moderates Mittelspiel
        else:
            temp = 0.1    # Fast deterministisch im Endspiel

        if len(actions) == 1:
            action = actions[0]
            policy = [{"action": action, "prob": 1.0}]
        else:
            action, policy = agent.search_and_get_policy(env, actions, temp=temp)

        history.append({
            "state":         copy.deepcopy(obs),
            "player":        current_player,
            "policy":        policy,
            "valid_actions": actions,
        })

        obs, reward, done, step_info = env.step(action)
        steps += 1

        if done:
            break

    scores = env.scores()
    winner = (
        0 if scores[0] > scores[1] else
        1 if scores[1] > scores[0] else
        0 if env.state.players[0].holds_first_player_marker else 1
    )

    training_data = []
    for step in history:
        val = 1.0 if step["player"] == winner else -1.0
        training_data.append({
            "state":         step["state"],
            "policy":        step["policy"],
            "value":         val,
            "valid_actions": step["valid_actions"],
        })

    return training_data, winner, scores, steps


def generate_data(num_games=100, simulations=50, version_name="v0"):
    print(f"🚀 Starte Data Generation: {num_games} Spiele (Sims: {simulations})")
    os.makedirs("data", exist_ok=True)

    agent = SelfPlayAgent(simulations=simulations, rollout_depth=5)
    all_training_data = []

    t_start = time.time()
    for i in range(num_games):
        t0 = time.time()
        print(f"Spiele Partie {i+1}/{num_games}... ", end="", flush=True)

        game_data, winner, scores, steps = play_one_game(agent, i)
        all_training_data.extend(game_data)
        duration = time.time() - t0
        print(f"Fertig in {duration:.1f}s | Sieger: P{winner} | "
              f"Scores: {scores[0]}:{scores[1]} | Züge: {steps}")

        if (i + 1) % 10 == 0:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"data/selfplay_{version_name}_{timestamp}_g{i+1}.pkl"
            with open(filename, "wb") as f:
                pickle.dump(all_training_data, f)
            print(f"💾 {len(all_training_data)} Züge gespeichert in '{filename}'")
            all_training_data = []

    print(f"✅ Fertig nach {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="MCTS Self-Play Datengenerierung für Mosaic-AI"
    )
    parser.add_argument("--games",   type=int, default=100)
    parser.add_argument("--sims",    type=int, default=50)
    parser.add_argument("--version", type=str, default="v0")
    args = parser.parse_args()

    generate_data(args.games, args.sims, args.version)