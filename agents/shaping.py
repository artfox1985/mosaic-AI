def get_player_potential(player) -> float:
    """
    Berechnet den heuristischen 'Wert' eines Spieler-Boards.
    Dient als absolute Heuristik für das MCTS und als Delta-Shaping für das NN.
    """
    potential = 0.0

    # A: Progressiver Bonus für alle liegenden Fliesen
    # Fertige Reihen werden mit ihrem ERWARTBAREN Tiling-Punktwert bewertet,
    # nicht mit einem fixen Bonus. So ist potential-based shaping sauber:
    # Beim Tiling fällt genau dieser Wert weg und kommt als echter Punkt zurück
    # → der Übergang ist neutral statt bestrafend.
    from engine.serializer import _estimate_row_values
    row_values = _estimate_row_values(player)

    for i, row in enumerate(player.pattern_lines):
        capacity = i + 1
        if len(row.tiles) > 0:
            base_weight = 0.5

            # Jeder Stein zählt, je weiter rechts, desto wertvoller
            for k in range(1, len(row.tiles) + 1):
                potential += (k / capacity) * base_weight

            # Fertige Reihe: erwartbaren Tiling-Punktwert gutschreiben
            # (statt fixem +3). Fällt beim Tiling weg, kommt als Punkt zurück.
            if row.is_complete:
                potential += row_values.get(i, 1)
                
    # B: Eskalierende Strafe für den Boden
    broken_penalty = 0.0
    base_pen = 0.8
    for k in range(1, len(player.broken_tiles) + 1):
        broken_penalty += k * base_pen
        
    # C: Bonus für das Fundament (Kuppelplatten) ---
    # C1: Basis — jede liegende Platte ermöglicht überhaupt erst Punkte.
    # C2: Positions-Bonus (sanfter E-Term, geometrisch): Die reine ZÄHLUNG der
    #     Platten (C1) macht alle Platzierungen gleichwertig — die Bewertung kann
    #     dann nicht zwischen guten und schlechten Plattenpositionen unterscheiden
    #     (gemessene Spanne 0 → flache dome-Policy → das Netz setzt Platten
    #     beliebig). Dieser Term bewertet zusätzlich die POSITION: orthogonal
    #     benachbarte Platten ermöglichen zusammenhängende Linien (horizontal/
    #     vertikal) und sind damit wertvoller. Bewusst SANFT gewichtet, damit er
    #     diskriminiert ohne das Lernsignal zu dominieren. Hängt NUR an der
    #     Plattengeometrie (nicht an Fliesen darauf) → potential-sauber, der Bonus
    #     bleibt stabil solange die Platte liegt (kein Verschwinden beim Tiling
    #     wie beim alten, koppelnden E-Term). Wertungsplatten bleiben hier
    #     bewusst außen vor (vorläufig nur Geometrie).
    _DOME_POSITION_WEIGHT = 0.3
    slots = player.dome_grid.dome_slots
    n_rows = len(slots)
    n_cols = len(slots[0]) if n_rows else 0
    dome_bonus = 0.0
    for r in range(n_rows):
        for c in range(n_cols):
            if slots[r][c] is not None:
                dome_bonus += 1  # C1: Basis pro Platte
                # C2: Positions-Bonus für orthogonale Platten-Nachbarn.
                # Jede Kante wird von beiden Platten gezählt → Faktor 0.5,
                # damit ein Nachbarpaar in Summe genau _DOME_POSITION_WEIGHT ergibt.
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n_rows and 0 <= nc < n_cols and slots[nr][nc] is not None:
                        dome_bonus += 0.5 * _DOME_POSITION_WEIGHT
    potential += dome_bonus
    
    # D: Bonus für tatsächlich erzielte Punkte (motiviert echte Punktevergabe)
    score_bonus = player.score * 0.45
    potential += score_bonus
    
    # E: Synergie-Bonus (Musterreihe <-> Kuppelplatte) [NEU]
    # synergy_bonus = 0.0
    # for ri, row in enumerate(player.pattern_lines):
        # # Nur Reihen betrachten, in denen schon Farbe/Fliesen liegen
        # if len(row.tiles) > 0 and row.color is not None:
            # dome_row = ri // 2
            # space_row = ri % 2
            # # Relevante Indizes in der 2x2 Kuppel (0,1 oder 2,3 je nach Reihe)
            # valid_si = [space_row * 2, space_row * 2 + 1]
            
            # has_matching_slot = False
            
            # # Alle 3 Slots in der passenden Kuppel-Reihe prüfen
            # for sc in range(3):
                # slot = player.dome_grid.dome_slots[dome_row][sc]
                # if slot is not None:
                    # for si in valid_si:
                        # space = slot.spaces[si]
                        # # Ist das Feld noch frei, nicht gelockt und akzeptiert unsere Farbe?
                        # is_locked = getattr(space, 'is_locked', False)
                        # if not space.is_filled and not is_locked and space.accepts(row.color):
                            # has_matching_slot = True
                            # break
                # if has_matching_slot:
                    # break
                    
            # if has_matching_slot:
                # # Synergie-Bonus: Es gibt eine liegende Kuppel, die exakt diese Farbe braucht!
                # # Grundbonus (1.5) + Skalierung: Je voller die Musterreihe, desto wertvoller!
                # capacity = ri + 1
                # synergy_bonus += 1.5 + (len(row.tiles) / capacity)
                
    # potential += synergy_bonus
        
    return potential - broken_penalty