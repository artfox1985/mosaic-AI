import time
from agents.agents import RandomAgent, GreedyAgent
from agents.mcts import MCTSAgent, HeuristicMCTSAgent, run_episode_mcts
from agents.alphazero import AlphaZeroAgent
from agents.agent_env import MosaicEnv
import itertools
from config import INPUT_SIZE

# Falls du den HeuristicMCTSAgent in einer anderen Datei gespeichert hast, importiere ihn entsprechend.
# from deine_datei import HeuristicMCTSAgent

def calculate_elo(rating_a, rating_b, actual_score_a, k=32):
    """Berechnet die neuen Elo-Ratings nach einer Partie."""
    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    expected_b = 1 - expected_a
    
    new_rating_a = rating_a + k * (actual_score_a - expected_a)
    new_rating_b = rating_b + k * ((1 - actual_score_a) - expected_b)
    
    return round(new_rating_a), round(new_rating_b)


def run_arena(agents_dict, games_per_matchup=10):
    """
    Round-Robin Turnier: Jeder Agent spielt gegen jeden anderen Agenten.
    """
    print(f"🏟️ WILLKOMMEN IN DER Mosaic-AI ARENA 🏟️")
    names = list(agents_dict.keys())
    print(f"Kämpfer: {names}")
    print("-" * 50)

    # Elo und Stats initialisieren
    elo_ratings = {name: data[1] for name, data in agents_dict.items()}
    agent_instances = {name: data[0] for name, data in agents_dict.items()}
    wins = {name: 0 for name in names}
    wins["Draw"] = 0
    wins["ZeroZero"] = 0
    all_avg_actions = []
    all_max_actions = []
    
    if games_per_matchup == 1:
        log = True
    else:
        log = False
            

    # Generiert alle Paarungen (z.B. (Random, Greedy), (Random, MCTS), (Greedy, MCTS))
    matchups = list(itertools.combinations(names, 2))

    for name_A, name_B in matchups:
        print(f"\n⚔️ NEUES MATCHUP: {name_A} vs {name_B} ({games_per_matchup} Spiele)")
        
        for i in range(games_per_matchup):
            # Wir wechseln fair ab, wer Startspieler ist
            if i % 2 == 0:
                p0, p1 = name_A, name_B
            else:
                p0, p1 = name_B, name_A
                
            env = MosaicEnv()
            agent_list = [agent_instances[p0], agent_instances[p1]]
            
            # Für MCTS die Umgebung übergeben
            for agent in agent_list:
                if hasattr(agent, 'set_env'):
                    agent.set_env(env)
                    
            print(f"  #{i+1}/{games_per_matchup}: ", end="", flush=True)
            t0 = time.time()
            
            result = run_episode_mcts(
                agents=agent_list, 
                max_steps=500, 
                verbose=log
            )
            duration = time.time() - t0
            
            # Auswertung
            scores = result["scores"]
            winner_idx = result["winner"]
            
            if winner_idx == 0:
                winner_name = p0
                score_a, score_b = 1.0, 0.0
            elif winner_idx == 1:
                winner_name = p1
                score_a, score_b = 0.0, 1.0
            else:
                winner_name = "Draw"
                score_a, score_b = 0.5, 0.5
                
            wins[winner_name] += 1
            if scores[0] == 0 and scores[1] == 0:
                wins["ZeroZero"] += 1
            all_avg_actions.append(result.get("avg_actions", 0))
            all_max_actions.append(result.get("max_actions", 0))

            # Elo Update
            old_elo_0 = elo_ratings[p0]
            old_elo_1 = elo_ratings[p1]
            
            # Reduzierter K-Faktor bei 0:0
            k = 16 if (scores[0] == 0 and scores[1] == 0) else 32
            new_elo_0, new_elo_1 = calculate_elo(old_elo_0, old_elo_1, score_a, k=k)
            
            elo_ratings[p0] = new_elo_0
            elo_ratings[p1] = new_elo_1
            
            # Strength berechnen (gleiche Formel wie self_play.py, cap=15)
            _margin = abs(scores[0] - scores[1])
            _ws     = max(scores[0], scores[1])
            if _margin == 0 and _ws < 5:
                _strength = 0.1
            else:
                _mp = min(0.45, (_margin / 15) * 0.45)
                _sp = min(0.45, (_ws     / 40) * 0.45)
                _strength = min(1.0, 0.1 + _mp + _sp)
            print(f" {duration:.1f}s | Züge: {result['steps']} | Strength: {_strength:.3f} | {scores[0]:3d}:{scores[1]:<3d} -> Sieger: {winner_name}")

    total    = sum(wins[n] for n in names)
    zerozero = wins["ZeroZero"]
    pct      = zerozero / total * 100 if total > 0 else 0

    print("\n" + "=" * 50)
    print("🏆 ARENA ERGEBNISSE 🏆")
    for name in names:
        print(f"Siege {name}: {wins[name]}")
    print(f"0:0 Spiele:    {zerozero} / {total} ({pct:.1f}%)")
    # Ø Strength über alle Spiele
    if all_avg_actions:  # Liste existiert noch (Kompatibilität)
        pass
    # Strength wurde pro Spiel ausgegeben

    
    print("\nFINALE ELO RATINGS:")
    # Sortiert die Tabelle absteigend nach Elo
    for name in sorted(elo_ratings, key=elo_ratings.get, reverse=True):
        print(f" - {name:15s}: {elo_ratings[name]} Elo")


if __name__ == "__main__":
    # --- DEINE STARTAUFSTELLUNG ---
    # Hier kannst du beliebig viele Agenten einfügen, das Skript baut
    # automatisch das perfekte Turnier daraus!
    
    #agent_random = RandomAgent()
    #agent_greedy = GreedyAgent()
    #agent_mcts_heuristic = HeuristicMCTSAgent(simulations=50, rollout_depth=0)
    agent_alphazero3a = AlphaZeroAgent(
        model_version="v3a",
        input_size=INPUT_SIZE, 
        simulations=40
        )
        
    agent_alphazero3new = AlphaZeroAgent(
        model_version="v3new",
        input_size=INPUT_SIZE, 
        simulations=40
        )
        
    agent_alphazero2 = AlphaZeroAgent(
        model_version="v2",
        input_size=INPUT_SIZE, 
        simulations=40
        )

    #competitors = {
    #    "Random": (agent_random, 1000),
    #    "Greedy": (agent_greedy, 1000),
    #    "MCTS_Heuristik": (agent_mcts_heuristic, 1000),
    #    "AlphaZero_V1": (agent_alphazero, 1000)
    #}

    competitors = {
        "AlphaZero V2": (agent_alphazero2, 1000),
        "AlphaZero V3new": (agent_alphazero3new, 1000),
        "AlphaZero V3old": (agent_alphazero3a, 1000)
    }

    # Jeder spielt gegen jeden
    #run_arena(competitors, games_per_matchup=5)
    run_arena(competitors, games_per_matchup=100)