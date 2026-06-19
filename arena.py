import time
from agents.agents import RandomAgent, GreedyAgent
from agents.mcts import MCTSAgent, HeuristicMCTSAgent, run_episode_mcts
from agents.alphazero import AlphaZeroAgent
from agents.agent_env import MosaicEnv
import itertools
from config import INPUT_SIZE, MARGIN_CAP, MAX_WINNER_SCORE
from agents.neural_net import compute_win_val
import sys
sys.stdout.reconfigure(encoding='utf-8')

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
    penalties = {name: 0 for name in names}
    # Pro-Runde-Strafpunkte: {name: {runde_idx: [summe, anzahl]}} für echten
    # Durchschnitt je Runde (Runde 1, 2, ...) statt nur Gesamtschnitt.
    penalties_per_round = {name: {} for name in names}
    games_played = {name: 0 for name in names}
    
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
                
            agent_list = [agent_instances[p0], agent_instances[p1]]
            # Hinweis: run_episode_mcts erzeugt sein eigenes Env und ruft
            # set_env selbst — hier kein zusätzliches Env nötig.

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
            
            # Strafpunkte auslesen
            final_state = result.get("state")
            if final_state:
                penalties[p0] += final_state.players[0].total_floor_penalties
                penalties[p1] += final_state.players[1].total_floor_penalties
                # Pro-Runde-Aufschlüsselung sammeln
                for slot, pl_idx in ((p0, 0), (p1, 1)):
                    per_round = final_state.players[pl_idx].floor_penalties_per_round
                    for r_idx, pen in enumerate(per_round):
                        bucket = penalties_per_round[slot].setdefault(r_idx, [0, 0])
                        bucket[0] += pen   # Summe
                        bucket[1] += 1     # Anzahl Spiele die diese Runde erreichten
            games_played[p0] += 1
            games_played[p1] += 1
            
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
            
            # K-Faktor mit Strength skalieren: klare Punktsiege bewegen ELO stärker,
            # 0:0-Siege (Strength 0.1) nur schwach. Range: ~6 (0:0) bis 32 (klarer Sieg).
            _winner_idx_elo = 0 if scores[0] >= scores[1] else 1
            _strength_elo = compute_win_val(scores, _winner_idx_elo, MARGIN_CAP, MAX_WINNER_SCORE)
            k = 32 * _strength_elo   # Strength 0.1→k≈3.2, 0.5→16, 1.0→32
            new_elo_0, new_elo_1 = calculate_elo(old_elo_0, old_elo_1, score_a, k=k)
            
            elo_ratings[p0] = new_elo_0
            elo_ratings[p1] = new_elo_1
            
            # Strength via compute_win_val (config-Parameter)
            _winner_idx = 0 if scores[0] >= scores[1] else 1
            _strength = compute_win_val(scores, _winner_idx, MARGIN_CAP, MAX_WINNER_SCORE)
            print(f" {duration:.1f}s | Züge: {result['steps']} | Strength: {_strength:.3f} | {scores[0]:3d}:{scores[1]:<3d} -> Sieger: {winner_name}")

    total    = sum(wins[n] for n in names)
    zerozero = wins["ZeroZero"]
    pct      = zerozero / total * 100 if total > 0 else 0

    print("\n" + "=" * 50)
    print("🏆 ARENA ERGEBNISSE 🏆")
    for name in names:
        print(f"Siege {name}: {wins[name]}")
    print(f"0:0 Spiele:    {zerozero} / {total} ({pct:.1f}%)")
    # durchschnittliche Strafpunkte — pro Runde aufgeschlüsselt
    print("\n📉 DURCHSCHNITTLICHE STRAFPUNKTE (BODEN) pro Runde:")
    # Spaltenüberschrift: alle vorkommenden Runden ermitteln
    all_rounds = sorted({
        r for name in names for r in penalties_per_round[name].keys()
    })
    if all_rounds:
        #header = "   " + " ".join(f"R{r+1:>5}" for r in all_rounds) + "   |  Gesamt"
        #print(header)
        for name in names:
            cells = []
            for r in all_rounds:
                bucket = penalties_per_round[name].get(r)
                if bucket and bucket[1] > 0:
                    cells.append(f"{bucket[0] / bucket[1]:6.2f}")
                else:
                    cells.append(f"{'—':>6}")
            # Gesamtschnitt pro Runde (über alle Runden gemittelt)
            total_games = games_played[name]
            overall = (penalties[name] / total_games / len(all_rounds)) if total_games else 0
            print(f" - {name:17s}: " + " ".join(cells) + f"   |  {overall:6.2f}")
        print("   (Werte = Ø Strafpunkte in dieser Runde über alle Spiele)")
    
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
    agent_mcts_heuristic1 = HeuristicMCTSAgent(simulations=100, rollout_depth=0, dynamic_sims="play")
    agent_mcts_heuristic2 = HeuristicMCTSAgent(simulations=100, rollout_depth=0, dynamic_sims="play")
    #agent_mcts_heuristic3 = HeuristicMCTSAgent(simulations=100, rollout_depth=0)
    #agent_mcts_heuristic4 = HeuristicMCTSAgent(simulations=100, rollout_depth=1)
    #agent_mcts_heuristic5 = HeuristicMCTSAgent(simulations=200, rollout_depth=0)
    #agent_mcts_heuristic6 = HeuristicMCTSAgent(simulations=200, rollout_depth=1)
    #agent_alphazero2 = AlphaZeroAgent(
    #   model_version="v1d",
    #   input_size=INPUT_SIZE, 
    #   simulations=50,
    #   dynamic_sims="play"
     #  )
        
    # agent_alphazero1 = AlphaZeroAgent(
        # model_version="v1_noe_vw05",
        # input_size=INPUT_SIZE, 
        # simulations=100,
        # dynamic_sims="play"
        # )
        
    # agent_alphazero3d = AlphaZeroAgent(
        # model_version="v3d",
        # input_size=INPUT_SIZE, 
        # simulations=40,
        # dynamic_sims="play"
        # )
        
    # agent_alphazero3c = AlphaZeroAgent(
        # model_version="v3c",
        # input_size=INPUT_SIZE, 
        # simulations=40,
        # dynamic_sims="play"
        # )

    #competitors = {
    #    "Random": (agent_random, 1000),
    #    "Greedy": (agent_greedy, 1000),
    #    "MCTS_Heuristik": (agent_mcts_heuristic, 1000),
    #    "AlphaZero_V1": (agent_alphazero, 1000)
    #}

    # competitors = {
        # "MCTS 50-0": (agent_mcts_heuristic1, 1000),
        # "MCTS 50-1": (agent_mcts_heuristic2, 1000),
        # "MCTS 100-0": (agent_mcts_heuristic3, 1000),
        # "MCTS 100-1": (agent_mcts_heuristic4, 1000),
        # "MCTS 200-0": (agent_mcts_heuristic5, 1000),
        # "MCTS 200-1": (agent_mcts_heuristic6, 1000),
    # }
    
    competitors = {
       "MCTS 1 s100-d0": (agent_mcts_heuristic1, 1000),
       "MCTS 2 s100-d0": (agent_mcts_heuristic2, 1000),
    }

    # Jeder spielt gegen jeden
    #run_arena(competitors, games_per_matchup=5)
    run_arena(competitors, games_per_matchup=100)