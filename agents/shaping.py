# agents/shaping.py

def get_player_potential(player) -> float:
    """
    Berechnet den heuristischen 'Wert' eines Spieler-Boards.
    Dient als absolute Heuristik für das MCTS und als Delta-Shaping für das NN.
    """
    potential = 0.0

    # A: Progressiver Bonus für alle liegenden Fliesen
    for i, row in enumerate(player.pattern_lines):
        capacity = i + 1
        if len(row.tiles) > 0:
            base_weight = 0.5
            
            # Jeder Stein zählt, je weiter rechts, desto wertvoller
            for k in range(1, len(row.tiles) + 1):
                potential += (k / capacity) * base_weight
            
            # Extra 'Zuckerguss'-Bonus, wenn die Reihe fertig ist
            # (Bleibt hoch, bis sie in Phase 2 abgeräumt und in echte Punkte verwandelt wird!)
            if row.is_complete:
                potential += 0.2
                
    # B: Eskalierende Strafe für den Boden
    broken_penalty = 0.0
    base_pen = 0.4
    for k in range(1, len(player.broken_tiles) + 1):
        broken_penalty += k * base_pen
        
    return potential - broken_penalty