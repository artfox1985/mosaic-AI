import os
import time
import copy
import pickle
import random
from datetime import datetime
import argparse

# WICHTIG: Stelle sicher, dass die Imports zu deiner Ordnerstruktur passen
from agents.agent_env import MosaicEnv
from agents.mcts import MCTSNode, HeuristicMCTSAgent 

class SelfPlayAgent(HeuristicMCTSAgent):
    """
    Erweitert den Heuristik-Agenten für Self-Play Datengenerierung.
    """
    def __init__(self, simulations=200, rollout_depth=10, **kwargs):
        # Wir ignorieren model_path/input_size, da der heuristische MCTS das nicht braucht
        super().__init__(simulations=simulations, rollout_depth=rollout_depth, **kwargs)

    def search_and_get_policy(self, env, actions, temp=1.0):
        # Wir müssen den State klonen, damit der MCTS nicht das echte Spiel manipuliert

        pi = env.current_player()
        print(f"DEBUG: search_and_get_policy gestartet für Spieler {pi}")
        sampled = self._sample_actions(actions)
        
        root = MCTSNode(
            action=None, 
            parent=None, 
            untried_actions=sampled, 
            player_who_acted=pi
        )
        root.visits = 1

        sims_done = 0
        while sims_done < self.simulations:
            # Zeitmessung für Debugging
            start_time = time.perf_counter()
            
            # Simulation durchführen
            sim_env = env.clone()
            node = self._select(root, sim_env)
            node = self._expand(node, sim_env)
            result = self._rollout(sim_env)
            self._backpropagate(node, result, pi)
            
            sims_done += 1
            
            # Debug-Ausgabe nur alle 50 Simulationen
            if sims_done % 50 == 0:
                duration = (time.perf_counter() - start_time) * 1000
                print(f"#{sims_done} DEBUG: Letzte Simulation dauerte {duration:.2f}ms")

        # 1. Policy (Wahrscheinlichkeiten)
        total_visits = sum(child.visits for child in root.children)
        policy = []
        for child in root.children:
            prob = child.visits / total_visits if total_visits > 0 else 0.0
            policy.append({"action": child.action, "prob": prob})

        # 2. Zugauswahl
        if temp > 0:
            # Temperatur-Sampling
            r = random.uniform(0, 1)
            acc = 0.0
            chosen_action = root.children[-1].action
            for p in policy:
                acc += p["prob"]
                if r <= acc:
                    chosen_action = p["action"]
                    break
        else:
            best_child = max(root.children, key=lambda c: c.visits)
            chosen_action = best_child.action

        return chosen_action, policy

def play_one_game(agent, game_index):
    env = MosaicEnv()
    obs, info = env.reset()
    agent.set_env(env)
    
    history = []
    steps = 0
    temperature_moves = 15 

    while True:
        actions = env.valid_actions()
        if not actions:
            break

        # DEBUG: Was denkt das Environment?
        print(f"DEBUG: Aktuelle Phase: '{getattr(env.state, 'phase', 'N/A')}'")
        # DEBUG: Warum endet das Drafting nicht?
        if env.state.phase == "drafting":
            from engine.round_end import check_drafting_complete
            is_done = check_drafting_complete(env.state)
            if not is_done:
                 # Hier kannst du sehen, was dem Drafting-Ende im Weg steht
                 # Evtl. printen wir mal, wieviele Tokens oder Steine noch da sind
                 pass
        current_player = env.current_player()
        temp = 1.0 if steps < temperature_moves else 0.0

        # Der Bypass
        if getattr(env.state, 'phase', '') == "tiling":
            action = actions[0]
            policy = [{"action": action, "prob": 1.0}]
            
        elif len(actions) == 1:
            action = actions[0]
            policy = [{"action": action, "prob": 1.0}]
            
        else:
            action, policy = agent.search_and_get_policy(env, actions, temp=temp)
            action, policy = agent.search_and_get_policy(env, actions, temp=temp)

        history.append({
            "state": copy.deepcopy(obs),
            "player": current_player,
            "policy": policy 
        })

        obs, reward, done, step_info = env.step(action)
        steps += 1
        
        if done: 
            break

    scores = env.scores()
    # Winner-Logik passend zu deiner engine
    winner = 0 if scores[0] > scores[1] else (1 if scores[1] > scores[0] else (0 if env.state.players[0].holds_first_player_marker else 1))

    training_data = []
    for step in history:
        val = 1.0 if step["player"] == winner else -1.0
        training_data.append({"state": step["state"], "policy": step["policy"], "value": val})

    return training_data, winner, scores, steps

def generate_data(num_games=100, simulations=150, version_name="v1"):
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
        print(f"Fertig in {duration:.1f}s | | Sieger: P{winner} | Scores: {scores[0]}:{scores[1]} | Züge: {steps}")

        if (i + 1) % 10 == 0:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"data/selfplay_{version_name}_{timestamp}_g{i+1}.pkl"
            with open(filename, "wb") as f:
                pickle.dump(all_training_data, f)
            all_training_data = []

    print(f"✅ Fertig nach {time.time() - t_start:.1f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--sims", type=int, default=50)
    parser.add_argument("--version", type=str, default="v0")
    args = parser.parse_args()
    
    generate_data(args.games, args.sims, args.version)