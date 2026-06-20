"""
Heuristik-Funktionen für den Mosaic (Azul Duel) MCTS-Agenten.

Zwei öffentliche Funktionen:
  get_player_potential(player, round_number, scoring_tile_ids) → float
      Absolute Board-Bewertung für ein einzelnes PlayerBoard.
      Wird in evaluate_state() für beide Spieler aufgerufen.

  score_dome_action(action, player, state) → float
      Quick-Scan-Score für eine Kuppelplatten-Aktion.
      Wird in _sample_actions() für das Action-Ranking genutzt.

Kalibrierung (abgeleitet aus Term-Messung über heuristische Spiele):
  - C-Basis: 0.6 statt 1.0 (C dominierte mit 12.6 vs A 12.75 in R4)
  - D-Gewicht: 0.75 / 0.90 statt 0.45 / 0.60 (Punkte wurden stark unterschätzt)
  - B-base_pen: 1.1 statt 0.8 (Strafe zu schwach relativ zu C)
  - E-Dämpfung: 0.8 statt 0.5 (Spezialfeld-EV zu klein um Plattenentscheidung zu beeinflussen)
  - F-Start: ab R3 (statt R4), Multiplikatoren 1.0/2.5/5.0 für R3/R4/R5
"""

from __future__ import annotations

# ── Hilfskonstanten ──────────────────────────────────────────────────────────

# Reihen-Wahrscheinlichkeiten: wie wahrscheinlich wird Reihe i (0-basiert)
# in dieser Partie noch fertig? Obere Reihen füllen sich schnell, untere langsam.
_ROW_PROB_EARLY = [0.95, 0.85, 0.60, 0.35, 0.15, 0.05]   # Runden 1-3
_ROW_PROB_LATE  = [0.80, 0.40, 0.10, 0.00, 0.00, 0.00]   # Runden 4-5

# Scoring-Tile ID Konstanten (aus engine/scoring.py)
_ID_HORIZONTAL   = 0
_ID_VERTICAL     = 1
_ID_DIAGONAL     = 2
_ID_WILD         = 3
_ID_OUTER        = 4
_ID_CORNERS      = 5
_ID_EMPTY_SPEC   = 6   # Minuspunkte für leere Spezialfelder
_ID_COLORFUL     = 7

# ── Kalibrierungs-Parameter ──────────────────────────────────────────────────
# Hier zentral definiert, damit sie leicht nachjustiert werden können.

# C: Kuppelplatten-Fundament
_C_BASIS        = 0.6   # Basis pro Platte (war 1.0 → dominierte zu stark)
_C_POS_WEIGHT   = 0.3   # Positions-Bonus pro orthogonalen Nachbarn (unverändert)

# D: Erzielte Punkte
_D_WEIGHT       = 0.85  # Normal (war 0.75 → erhöht: echte Punkte attraktiver
                         # als Null-Risiko-Strategie)
_D_WEIGHT_CASH  = 1.00  # Runde 5 Cashout (war 0.90)

# B: Strafleiste
_B_BASE_PEN     = 1.8   # Eskalierender Faktor (war 1.1 → 0:0-Rate zu hoch).
                         # 1.8 ≈ 1.6× über echten Strafpunkten: Fluten kostet
                         # strategisch mehr als nominal, kompensiert vernichtete
                         # Zukunftspunkte. Nicht zu hoch (>2.5) sonst zu risikoscheu.

# E: Spezialfeld Expected Value
_E_WEIGHT       = 0.8   # Dämpfungsfaktor (war 0.5 → zu klein um Plattenentscheidung
                         # zu beeinflussen)

# F: Endgame-Wertungsplatten-Nähe
_F_START_ROUND  = 3     # Greift ab R3 (war R4 → zu spät)
_F_MULTI = {3: 1.0, 4: 2.5, 5: 5.0}  # Multiplikatoren je Runde


def _row_probs(round_number: int) -> list[float]:
    """Reihen-Wahrscheinlichkeiten je nach Spielphase."""
    return _ROW_PROB_LATE if round_number >= 4 else _ROW_PROB_EARLY


def _is_lategame(round_number: int) -> bool:
    return round_number >= _F_START_ROUND


def _cashout(round_number: int) -> bool:
    return round_number >= 5


# ── Adjacency-Schätzung ──────────────────────────────────────────────────────

def _estimate_cluster_value(player, slot_row: int, slot_col: int,
                             row_index: int) -> float:
    """
    Schätzt die Cluster-Punkte die eine neue Fliese in Reihe row_index
    (0-basiert) auf dem 6x6-Brett erzeugen würde.
    """
    slots = player.dome_grid.dome_slots

    h_neighbors = 0
    for dc in (-1, 1):
        nc = slot_col + dc
        if 0 <= nc < 3:
            neighbor = slots[slot_row][nc]
            if neighbor is not None:
                space_idx_start = 0 if row_index == slot_row * 2 else 2
                for si in range(space_idx_start, space_idx_start + 2):
                    if si < len(neighbor.spaces) and neighbor.spaces[si].placed_color:
                        h_neighbors += 1

    v_neighbors = 0
    for dr in (-1, 1):
        nr = slot_row + dr
        if 0 <= nr < 3:
            neighbor = slots[nr][slot_col]
            if neighbor is not None:
                filled = sum(1 for sp in neighbor.spaces if sp.placed_color)
                if filled > 0:
                    v_neighbors += 1

    return float(h_neighbors + v_neighbors)


# ── Dome-Platzierungs-Heuristik (Action-Ranking) ────────────────────────────

def score_dome_action(action: dict, player, state) -> float:
    """
    Quick-Scan-Score für eine Kuppelplatten-Aktion.
    Wird in _sample_actions() aufgerufen, um Aktionen vor dem MCTS zu ranken.

    Berücksichtigt:
    - Reihen-Wahrscheinlichkeiten (obere Reihen wertvoller)
    - Spezialfeld Expected Value (inkl. Straf-Penalty wenn ID 6 aktiv)
    - Nachbarschafts-Bonus (Cluster-Potenzial)
    - Capacity Matching: Bulk-Farben ins Auffangbecken (Reihen 4-6),
      Snipe-Farben in kurze Reihen (1-3)
    """
    round_number = state.round_number
    scoring_ids  = state.scoring_tile_ids
    row_probs    = _row_probs(round_number)
    special_pen  = 3.0 if _ID_EMPTY_SPEC in scoring_ids else 0.0
    lategame     = _is_lategame(round_number)

    slot_row = action.get("slot_row", 0)
    slot_col = action.get("slot_col", 0)

    display_index = action.get("display_index", -1)
    dome_tile = None
    if 0 <= display_index < len(state.dome_display):
        dome_tile = state.dome_display[display_index]
    if dome_tile is None:
        return 0.0

    score = 0.0

    # Reihen-Wahrscheinlichkeits-Bewertung der 4 Spaces
    for space_idx, space in enumerate(dome_tile.spaces):
        game_row  = slot_row * 2 + (0 if space_idx < 2 else 1)
        if game_row >= 6:
            continue
        prob       = row_probs[game_row]
        row_points = game_row + 1

        if space.is_locked:
            # Spezialfeld-EV: Verbundwahrscheinlichkeit der 3 normalen Spaces
            p_success = 1.0
            for si2, sp2 in enumerate(dome_tile.spaces):
                if not sp2.is_locked:
                    g2 = slot_row * 2 + (0 if si2 < 2 else 1)
                    if 0 <= g2 < 6:
                        p_success *= row_probs[g2]
            score += p_success * row_points - (1.0 - p_success) * special_pen
        else:
            score += prob * row_points

    # Cluster-Bonus (Nachbarschaft vorhandener Fliesen)
    cluster = _estimate_cluster_value(player, slot_row, slot_col, slot_row * 2)
    score += cluster * 0.5

    # Positions-Bonus: orthogonale Plattenachbarn
    slots   = player.dome_grid.dome_slots
    n_rows  = len(slots)
    n_cols  = len(slots[0]) if slots else 0
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = slot_row + dr, slot_col + dc
        if 0 <= nr < n_rows and 0 <= nc < n_cols and slots[nr][nc] is not None:
            score += _C_POS_WEIGHT

    # Capacity Matching
    color_counts: dict = {}
    for fac in getattr(state, "factories", []):
        for tile in getattr(fac, "tiles", []):
            c = str(getattr(tile, "color", ""))
            color_counts[c] = color_counts.get(c, 0) + 1
    for tile in getattr(state, "moon_pool", []):
        c = str(getattr(tile, "color", ""))
        color_counts[c] = color_counts.get(c, 0) + 1

    total_tiles = sum(color_counts.values()) or 1
    for space_idx, space in enumerate(dome_tile.spaces):
        req_color = str(getattr(space, "required_color", ""))
        if not req_color or space.is_locked:
            continue
        density    = color_counts.get(req_color, 0) / total_tiles
        game_row   = slot_row * 2 + (0 if space_idx < 2 else 1)
        lower_half = game_row >= 3
        if density > 0.25 and lower_half:      # Bulk → Auffangbecken
            score += 0.4
        elif density <= 0.10 and not lower_half:  # Snipe → kurze Reihen
            score += 0.3

    # Lategame: obere Slots dringend prioritisieren
    if lategame and slot_row == 0:
        score += 1.5

    return score


# ── Haupt-Potential-Funktion ─────────────────────────────────────────────────

def get_player_potential(player, round_number: int = 1,
                         scoring_tile_ids: list | None = None) -> float:
    """
    Heuristische Board-Bewertung eines Spielers.

    Terme:
      A — Musterreihen (Fortschritt + fertige Reihe Erwartungswert)
      B — Strafleisten-Penalty (eskalierend, base_pen=1.1)
      C — Kuppelplatten-Fundament (Basis 0.6 + Positions-Bonus 0.3)
      D — Erzielte Punkte (0.75 normal, 0.90 in R5)
      E — Spezialfeld Expected Value (Dämpfung 0.8)
      F — Endgame-Wertungsplatten-Nähe (ab R3, Mult 1.0/2.5/5.0)
    """
    if scoring_tile_ids is None:
        scoring_tile_ids = []

    row_probs = _row_probs(round_number)
    lategame  = _is_lategame(round_number)
    cashout   = _cashout(round_number)
    special_penalty = 3.0 if _ID_EMPTY_SPEC in scoring_tile_ids else 0.0

    potential = 0.0

    # ── A: Musterreihen ──────────────────────────────────────────────────────
    from engine.serializer import _estimate_row_values
    row_values = _estimate_row_values(player)

    open_rows = 0   # Reihen die angefangen aber noch nicht abgeschlossen sind
    for i, row in enumerate(player.pattern_lines):
        capacity = i + 1
        if len(row.tiles) > 0:
            for k in range(1, len(row.tiles) + 1):
                potential += (k / capacity) * 0.5
            if row.is_complete:
                potential += row_values.get(i, 1)
            else:
                open_rows += 1

    # A2: Sättigungs-Penalty für zu viele gleichzeitig offene Reihen.
    # Ab 4 offenen Reihen steigt die Wahrscheinlichkeit stark, dass zukünftige
    # Züge auf die Strafleiste gehen (kein Platz mehr für neue Farben).
    # Jede offene Reihe über dem Schwellenwert kostet zunehmend.
    _OPEN_ROW_THRESHOLD = 2   # bis 3 offene Reihen: kein Penalty
    _OPEN_ROW_PEN       = 1 # Penalty pro Reihe über dem Schwellenwert
    if open_rows > _OPEN_ROW_THRESHOLD:
        over = open_rows - _OPEN_ROW_THRESHOLD
        saturation_penalty = over * over * _OPEN_ROW_PEN
        potential -= saturation_penalty

    # ── B: Strafleiste (eskalierend) ─────────────────────────────────────────
    broken_penalty = 0.0
    for k in range(1, len(player.broken_tiles) + 1):
        broken_penalty += k * _B_BASE_PEN

    # ── C: Kuppelplatten-Fundament ───────────────────────────────────────────
    # C1: Basis (_C_BASIS pro Platte) — reduziert damit C A/D nicht überwächst.
    # C2: Positions-Bonus für orthogonale Nachbarn (geometrisch, stabil).
    slots  = player.dome_grid.dome_slots
    n_rows = len(slots)
    n_cols = len(slots[0]) if n_rows else 0
    dome_bonus = 0.0
    for r in range(n_rows):
        for c in range(n_cols):
            if slots[r][c] is not None:
                dome_bonus += _C_BASIS
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < n_rows and 0 <= nc < n_cols
                            and slots[nr][nc] is not None):
                        dome_bonus += 0.5 * _C_POS_WEIGHT
    potential += dome_bonus

    # ── D: Erzielte Punkte ───────────────────────────────────────────────────
    potential += player.score * (_D_WEIGHT_CASH if cashout else _D_WEIGHT)

    # ── E: Spezialfeld Expected Value ────────────────────────────────────────
    ev_bonus = 0.0
    for r in range(n_rows):
        for c in range(n_cols):
            tile = slots[r][c]
            if tile is None:
                continue
            if not any(sp.is_locked for sp in tile.spaces):
                continue
            p_success = 1.0
            for si, sp in enumerate(tile.spaces):
                if not sp.is_locked:
                    game_row = r * 2 + (0 if si < 2 else 1)
                    if 0 <= game_row < 6:
                        p_success *= 1.0 if sp.placed_color else row_probs[game_row]
            special_row = next(
                (r * 2 + (0 if si < 2 else 1)
                 for si, sp in enumerate(tile.spaces) if sp.is_locked),
                r * 2
            )
            ev = p_success * (special_row + 1) - (1.0 - p_success) * special_penalty
            ev_bonus += ev * _E_WEIGHT
    potential += ev_bonus

    # ── F: Endgame-Wertungsplatten-Nähe (ab R3) ──────────────────────────────
    if lategame and scoring_tile_ids:
        from engine.scoring import _build_grid
        try:
            grid = _build_grid(player)
        except Exception:
            grid = None

        if grid is not None:
            multi = _F_MULTI.get(round_number, 5.0)
            goal_bonus = 0.0

            for tid in scoring_tile_ids:
                if tid == _ID_HORIZONTAL:
                    for row_i in range(6):
                        filled = sum(1 for cc in range(6) if grid[row_i][cc])
                        if filled >= 4:
                            goal_bonus += 0.3 * multi
                        elif filled >= 2:
                            goal_bonus += 0.1 * multi

                elif tid == _ID_VERTICAL:
                    for col_i in range(6):
                        filled = sum(1 for ri in range(6) if grid[ri][col_i])
                        if filled >= 4:
                            goal_bonus += 0.3 * multi
                        elif filled >= 2:
                            goal_bonus += 0.1 * multi

                elif tid == _ID_DIAGONAL:
                    d1 = sum(1 for i in range(6) if grid[i][i])
                    d2 = sum(1 for i in range(6) if grid[i][5 - i])
                    goal_bonus += (d1 / 6.0 + d2 / 6.0) * 2.0 * multi

                elif tid == _ID_OUTER:
                    outer = (
                        [(0, c) for c in range(6)] +
                        [(5, c) for c in range(6)] +
                        [(r, 0) for r in range(1, 5)] +
                        [(r, 5) for r in range(1, 5)]
                    )
                    filled = sum(1 for (rr, cc) in outer if grid[rr][cc])
                    goal_bonus += (filled / 20.0) * 3.0 * multi

                elif tid == _ID_CORNERS:
                    filled = sum(
                        1 for (rr, cc) in [(0, 0), (0, 5), (5, 0), (5, 5)]
                        if grid[rr][cc]
                    )
                    goal_bonus += filled * 0.5 * multi

                elif tid == _ID_COLORFUL:
                    from engine.scoring import _get_row_colors
                    try:
                        for row_i in range(6):
                            colors = _get_row_colors(player, row_i)
                            unique = len(set(
                                col for col in colors
                                if col is not None and col != "special"
                            ))
                            if unique >= 4:
                                goal_bonus += 0.3 * multi
                            elif unique >= 2:
                                goal_bonus += 0.1 * multi
                    except Exception:
                        pass

            potential += goal_bonus

    return potential - broken_penalty