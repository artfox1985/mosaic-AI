"""
self_play.py — Self-Play Datengenerierung für Mosaic-AI

Unterstützt zwei Modi:
  --mode mcts      Verwendet HeuristicMCTSAgent (kein Netz, für erste Generation)
  --mode network   Verwendet AlphaZeroAgent (mit trainiertem Netz)

Verwendung:
  python self_play.py --mode mcts    --games 1500 --sims 50  --version v0
  python self_play.py --mode network --games 1500 --sims 40  --version v1
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
from config import MODELS_DIR, DATA_DIR, INPUT_SIZE, NUM_ACTIONS


# ---------------------------------------------------------------------------
# Gemeinsame Self-Play Logik
# ---------------------------------------------------------------------------

class SelfPlayMixin:
    """
    Mixin für Self-Play: erweitert einen MCTS-Agenten um search_and_get_policy.
    Führt alle Simulationen durch und gibt Policy + gewählte Aktion zurück.
    Temperature steuert Schärfe der Policy:
      temp=1.0 → proportional zu Visits (explorativ)
      temp=0.5 → moderater Fokus
      temp=0.1 → fast deterministisch
      temp=0.0 → argmax
    """

    def search_and_get_policy(self, env, actions, temp=1.0):
        pi = env.current_player()
        sampled = self._sample_actions(actions)

        root = MCTSNode(
            action=None,
            parent=None,
            untried_actions=sampled,
            player_who_acted=pi
        )
        root.visits = 1

        # Alle Simulationen durchführen
        for _ in range(self.simulations):
            sim_env = env.clone()
            node = self._select(root, sim_env)
            node = self._expand(node, sim_env)
            result = self._rollout(sim_env)
            self._backpropagate(node, result, pi)

        if not root.children:
            action = random.choice(actions)
            return action, [{"action": action, "prob": 1.0}]

        if temp == 0.0:
            best = max(root.children, key=lambda c: c.visits)
            policy = [{"action": c.action, "prob": 1.0 if c is best else 0.0}
                      for c in root.children]
            policy = [p for p in policy if p["prob"] > 0.0]
            return best.action, policy

        for _ in range(self.simulations):
            sim_env = env.clone()
            node = self._select(root, sim_env)
            node = self._expand(node, sim_env)
            result = self._rollout(sim_env)
            self._backpropagate(node, result, pi)

        # Cache leeren — Priors gelten nur für diesen Zug
        if hasattr(self, 'node_priors'):
            self.node_priors.clear()
        elif hasattr(self, '_az') and hasattr(self._az, 'node_priors'):
            self._az.node_priors.clear()

        # Temperature-gewichtete Policy: visits^(1/temp)
        total_visits = sum(c.visits for c in root.children)
        if total_visits == 0:
            action = random.choice(actions)
            return action, [{"action": action, "prob": 1.0}]

        raw = [(c, c.visits ** (1.0 / temp)) for c in root.children]
        total_raw = sum(r for _, r in raw)
        policy = [{"action": c.action, "prob": r / total_raw} for c, r in raw]

        chosen_action = random.choices(
            [p["action"] for p in policy],
            weights=[p["prob"] for p in policy]
        )[0]

        return chosen_action, policy


class MCTSSelfPlayAgent(SelfPlayMixin, HeuristicMCTSAgent):
    """MCTS-basierter Self-Play Agent (kein neuronales Netz)."""
    def __init__(self, simulations=50, rollout_depth=5, max_actions=10, **kwargs):
        super().__init__(simulations=simulations, rollout_depth=rollout_depth,
                         max_actions=max_actions, **kwargs)


class NetworkSelfPlayAgent(SelfPlayMixin):
    """AlphaZero-basierter Self-Play Agent (mit trainiertem Netz)."""
    def __init__(self, model_version: str, simulations=40, **kwargs):
        from agents.alphazero import AlphaZeroAgent
        # Wir erben nicht von AlphaZeroAgent sondern wrappen ihn
        # damit SelfPlayMixin._sample_actions etc. verfügbar sind
        self._az = AlphaZeroAgent(
            model_version=model_version,
            input_size=INPUT_SIZE,
            simulations=simulations,
            **kwargs
        )
        # Delegiere alle MCTS-Methoden an den AlphaZero-Agent
        self.simulations = simulations
        self._select = self._az._select
        self._expand = self._az._expand
        self._rollout = self._az._rollout
        self._backpropagate = self._az._backpropagate
        self._sample_actions = self._az._sample_actions

    def set_env(self, env):
        self._az.set_env(env)


# ---------------------------------------------------------------------------
# Spiel-Loop
# ---------------------------------------------------------------------------

def play_one_game(agent):
    """Spielt ein Spiel und gibt Trainingsdaten zurück."""
    env = MosaicEnv()
    obs, info = env.reset()

    if hasattr(agent, 'set_env'):
        agent.set_env(env)

    history = []
    steps = 0
    temperature_moves = 30

    while True:
        actions = env.valid_actions()
        if not actions:
            break

        current_player = env.current_player()

        # Sanfter Temperature-Übergang
        if steps < temperature_moves:
            temp = 1.0
        elif steps < 60:
            temp = 0.5
        else:
            temp = 0.1

        if len(actions) == 1:
            action = actions[0]
            policy = [{"action": action, "prob": 1.0}]
        else:
            action, policy = agent.search_and_get_policy(env, actions, temp=temp)

        history.append({
            "state":              copy.deepcopy(obs),
            "player":             current_player,
            "policy":             policy,
            "valid_actions":      actions,
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
            "state":             step["state"],
            "policy":            step["policy"],
            "value":             val,
            "valid_actions":     step["valid_actions"],
        })

    return training_data, winner, scores, steps


# ---------------------------------------------------------------------------
# Datengenerierung
# ---------------------------------------------------------------------------

def generate_data(mode: str, num_games: int, simulations: int, version_name: str, rollout_depth: int = 0):
    """
    Generiert Self-Play Trainingsdaten.

    mode:         'mcts' oder 'network'
    num_games:    Anzahl zu spielender Partien
    simulations:  MCTS-Simulationen pro Zug
    version_name: Versionsname für Dateinamen und Modell-Laden
    """
    if mode == "mcts":
        print(f"🚀 Starte MCTS Self-Play: {num_games} Spiele (Sims: {simulations})")
        agent = MCTSSelfPlayAgent(simulations=simulations, rollout_depth=rollout_depth)
    elif mode == "network":
        model_file = MODELS_DIR / f"alphazero_{version_name}.pth"
        if not model_file.exists():
            print(f"❌ Modell nicht gefunden: {model_file}")
            return
        print(f"🚀 Starte Network Self-Play: {num_games} Spiele "
              f"(Sims: {simulations} | Model: {model_file.name})")
        agent = NetworkSelfPlayAgent(model_version=version_name, simulations=simulations)
    else:
        print(f"❌ Unbekannter Modus: {mode}. Verwende 'mcts' oder 'network'.")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    all_training_data = []
    t_start = time.time()

    for i in range(num_games):
        t0 = time.time()
        print(f"Spiele Partie {i+1}/{num_games}... ", end="", flush=True)

        game_data, winner, scores, steps = play_one_game(agent)
        all_training_data.extend(game_data)
        duration = time.time() - t0

        print(f"Fertig in {duration:.1f}s | Sieger: P{winner} | "
              f"Scores: {scores[0]}:{scores[1]} | Züge: {steps}")

        if (i + 1) % 10 == 0 or (i + 1) == num_games:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = DATA_DIR / f"selfplay_{version_name}_{timestamp}_g{i+1}.pkl"
            with open(filename, "wb") as f:
                pickle.dump(all_training_data, f)
            print(f"💾 {len(all_training_data)} Züge gespeichert in '{filename}'")
            all_training_data = []

    print(f"\n✅ Fertig nach {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mosaic-AI Self-Play Datengenerierung")
    parser.add_argument("--mode",    type=str, required=True,
                        choices=["mcts", "network"],
                        help="'mcts' für MCTS-only, 'network' für AlphaZero-Netz")
    parser.add_argument("--games",   type=int, default=100,
                        help="Anzahl Spiele")
    parser.add_argument("--sims",    type=int, default=50,
                        help="MCTS-Simulationen pro Zug")
    parser.add_argument("--version", type=str, required=True,
                        help="Versionsname, z.B. v0 oder v1")
    parser.add_argument("--depth",   type=int, required=True,
                        help="Rollout-Tiefe (0=Heuristik, 1=1 Schritt, 5=5 Schritte)")
    args = parser.parse_args()

    generate_data(
        mode=args.mode,
        num_games=args.games,
        simulations=args.sims,
        version_name=args.version,
        rollout_depth=args.depth,
    )