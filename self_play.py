import os
import time
import copy
import pickle
import random
from datetime import datetime
import argparse

from agents.agent_env import MosaicEnv
from agents.mcts import MCTSNode
from agents.alphazero import AlphaZeroAgent
from config import MODELS_DIR, DATA_DIR

class SelfPlayAgent(AlphaZeroAgent):
    """
    Erweitert den Heuristik-Agenten. 
    Anstatt nur den besten Zug zurückzugeben, gibt er den Zug UND 
    die Wahrscheinlichkeitsverteilung (Policy) aller Züge zurück.
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

        sims_done = 0
        while sims_done < self.simulations:
            sim_env = env.clone()
            node = self._select(root, sim_env)
            node = self._expand(node, sim_env)
            result = self._rollout(sim_env)
            self._backpropagate(node, result, pi)
            sims_done += 1

        # 1. Policy (Wahrscheinlichkeiten) aus den Besuchszahlen berechnen
        policy = []
        total_visits = sum(child.visits for child in root.children)

        for child in root.children:
            prob = child.visits / total_visits if total_visits > 0 else 0.0
            policy.append({"action": child.action, "prob": prob})

        # 2. Zugauswahl mit "Temperatur"
        if temp > 0:
            # EXPLORATION: Wir wählen den Zug gewichtet nach Wahrscheinlichkeit.
            # So verläuft nicht jedes Spiel exakt gleich!
            r = random.uniform(0, 1)
            acc = 0.0
            chosen_action = root.children[-1].action
            for p in policy:
                acc += p["prob"]
                if r <= acc:
                    chosen_action = p["action"]
                    break
        else:
            # EXPLOITATION: Wir nehmen eiskalt den besten Zug.
            best_child = max(root.children, key=lambda c: c.visits)
            chosen_action = best_child.action

        return chosen_action, policy


def play_one_game(agent, game_index):
    """Spielt genau ein Spiel und zeichnet alle Daten auf."""
    env = MosaicEnv()
    obs, info = env.reset()
    agent.set_env(env)
    
    history = []
    steps = 0
    
    # Nach 15 Zügen schalten wir den Zufall (Temperatur) ab,
    # damit das Spiel auf einem hohen Niveau beendet wird.
    temperature_moves = 15 

    while True:
        actions = env.valid_actions()
        if not actions:
            break

        current_player = env.current_player()
        temp = 1.0 if steps < temperature_moves else 0.0

        if len(actions) == 1:
            action = actions[0]
            policy = [{"action": action, "prob": 1.0}]
        else:
            action, policy = agent.search_and_get_policy(env, actions, temp=temp)

        # Datensatz für diesen Zug speichern
        history.append({
            "state": copy.deepcopy(obs),  # Das genaue Brett
            "player": current_player,     # Wer war dran?
            "policy": policy              # Was dachte die KI?
        })

        # Zug ausführen
        obs, reward, done, step_info = env.step(action)
        steps += 1

        if done:
            break

    # Wer hat das Spiel gewonnen? (Inklusive Startspieler-Tie-Breaker)
    scores = env.scores()
    if scores[0] > scores[1]:
        winner = 0
    elif scores[1] > scores[0]:
        winner = 1
    else:
        winner = 0 if env.state.players[0].holds_first_player_marker else 1

    # RÜCKBLICK (Value Backfill):
    # Jetzt wissen wir, wer gewonnen hat. Wir gehen die Historie durch und
    # schreiben zu jedem Zug dazu, ob dieser Spieler am Ende gesiegt (+1.0) 
    # oder verloren (-1.0) hat.
    training_data = []
    for step in history:
        val = 1.0 if step["player"] == winner else -1.0
        training_data.append({
            "state": step["state"],
            "policy": step["policy"],
            "value": val
        })

    return training_data, winner, scores, steps


def generate_data(num_games=100, simulations=40, version_name="v1"):
    model_file = MODELS_DIR / f"alphazero_{version_name}.pth"
    model_path_str = str(model_file) # Sichergehen, dass PyTorch einen String bekommt
    print(f"🚀 Starte Data Generation: {num_games} Spiele (Sims: {simulations} | Model: {model_file.name})")
    
    os.makedirs("data", exist_ok=True)
    
    # --- Agent lädt das dynamische Modell ---
    agent = SelfPlayAgent(
        model_version=version_name, 
        input_size=129, 
        simulations=simulations
    )
    all_training_data = []
    
    t_start = time.time()
    
    for i in range(num_games):
        if hasattr(agent, 'reset_for_new_game'):
                agent.reset_for_new_game()
        
        t0 = time.time()
        print(f"Spiele Partie {i+1}/{num_games}... ", end="", flush=True)
        
        game_data, winner, scores, steps = play_one_game(agent, i)
        all_training_data.extend(game_data)
        
        duration = time.time() - t0
        print(f"Fertig in {duration:.1f}s | Sieger: P{winner} ({scores[0]}:{scores[1]}) | {steps} Züge gesammelt")

        if (i + 1) % 10 == 0 or (i + 1) == num_games:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            # --- Dynamischer Dateiname für die Trainingsdaten! ---
            filename = DATA_DIR / f"selfplay_{version_name}_{timestamp}_games_{i+1}.pkl"
            
            with open(filename, "wb") as f:
                pickle.dump(all_training_data, f)
            print(f"💾 {len(all_training_data)} Züge gespeichert in '{filename}'")
            
            all_training_data = []

    total_time = time.time() - t_start
    print(f"\n✅ Erfolgreich abgeschlossen in {total_time:.1f} Sekunden!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Starte das Mosaic-AI KI-Training")
    parser.add_argument("--games", type=int, default=100, help="Anzahl der zu simulierenden Spiele")
    parser.add_argument("--sims", type=int, default=40, help="MCTS Simulationen pro Zug")
    
    # NEU: Welche Modell-Version soll spielen? (Pflichtfeld)
    parser.add_argument("--version", type=str, required=True, help="Name des Models, z.B. v1")
    
    args = parser.parse_args()
    
    generate_data(num_games=args.games, simulations=args.sims, version_name=args.version)
