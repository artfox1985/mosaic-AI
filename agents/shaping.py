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
                potential += 3
                
    # B: Eskalierende Strafe für den Boden
    broken_penalty = 0.0
    base_pen = 0.8
    for k in range(1, len(player.broken_tiles) + 1):
        broken_penalty += k * base_pen
        
    # C: Bonus für das Fundament (Kuppelplatten) ---
    dome_bonus = 0.0
    for r in player.dome_grid.dome_slots:
        for slot in r:
            if slot is not None:
                # Jede liegende Platte ist extrem wertvoll, 
                # da sie überhaupt erst Punkte ermöglicht!
                dome_bonus += 1 
    potential += dome_bonus
    
    # D: Bonus für tatsächlich erzielte Punkte (motiviert echte Punktevergabe)
    score_bonus = player.score * 0.45
    potential += score_bonus
        
    return potential - broken_penalty
