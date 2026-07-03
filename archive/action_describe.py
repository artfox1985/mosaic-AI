"""
Klartext-Beschreibung von Action-IDs für Debugger / Visualisierung.

Action-ID Schema (siehe agent_env.py):
  pass        = 0
  end_tiling  = 1
  stone       = 10 + color_idx*48 + r_id*6 + factory_index
                 r_id=0 → Strafleiste, r_id=1..6 → Reihe 1-6
                 factory: 0-3=F1-F4, 4=GF, 5=Mond
  tiling      = 274-327
  dome        = 328-435
  dome_stack  = 436-471
  use_chips   = 472-477
  bonus_chip  = 478-481
"""

COLORS  = ['blau', 'gelb', 'rot', 'schwarz', 'türkis']
# factory_index Bedeutung (siehe agent_env.py _drafting_actions):
#   0-3 = kleine Fabriken F1-F4 (bzw. GF-Moon-Pool via factory_id, mehrdeutig)
#   4   = LARGE_FACTORY_SUN  → "GF" (große Fabrik, Sonnenseite)
#   5   = SMALL_FACTORY_MOON global → Mondaktion C
SOURCES = ['F1', 'F2', 'F3', 'F4', 'GF', 'Mond']


def describe_action_id(aid: int) -> str:
    """Gibt eine menschenlesbare Beschreibung einer Action-ID zurück."""
    if aid == 0:
        return "Pass"
    if aid == 1:
        return "Tiling beenden"

    # Stein-Züge: 10 - 249
    if 10 <= aid <= 249:
        a      = aid - 10
        f_idx  = a % 6
        r_id   = (a // 6) % 8
        c_id   = a // 48
        color  = COLORS[c_id]  if c_id  < len(COLORS)  else '?'
        source = SOURCES[f_idx] if f_idx < len(SOURCES) else '?'
        # r_id wird in action_to_id als (row + 1) kodiert:
        #   r_id=0 → row=-1 → Strafleiste, r_id=1..6 → Reihe 1..6
        row_str = 'Strafleiste' if r_id == 0 else f'Reihe {r_id}'
        return f"{color} von {source} → {row_str}"

    # Tiling: 274 - 327   (274 + pattern_row*9 + slot_row*3 + slot_col)
    if 274 <= aid <= 327:
        a  = aid - 274
        pr = a // 9
        sr = (a % 9) // 3
        sc = a % 3
        return f"Tiling: Reihe {pr+1} → Slot ({sr},{sc})"

    # Dome: 328 - 435   (328 + display_index*36 + slot_row*12 + slot_col*4 + rot_idx)
    if 328 <= aid <= 435:
        a       = aid - 328
        d_idx   = a // 36
        rest    = a % 36
        sr      = rest // 12
        sc      = (rest % 12) // 4
        rot_idx = rest % 4
        return f"Kuppel {d_idx} → Slot ({sr},{sc}) {rot_idx*90}°"

    # Dome-Stack: 436 - 471   (436 + slot_row*12 + slot_col*4 + rot_idx)
    if 436 <= aid <= 471:
        a       = aid - 436
        sr      = a // 12
        sc      = (a % 12) // 4
        rot_idx = a % 4
        return f"Kuppel vom Stapel → Slot ({sr},{sc}) {rot_idx*90}°"

    # Use-Chips: 472 - 477   (472 + pattern_row)
    if 472 <= aid <= 477:
        return f"Chips einsetzen → Reihe {aid - 472 + 1}"

    # Bonus-Chip: 478 - 481   (478 + factory_index)
    if 478 <= aid <= 481:
        f_idx = aid - 478
        src = SOURCES[f_idx] if f_idx < len(SOURCES) else f"#{f_idx}"
        return f"Bonus-Chip von {src}"

    return f"Unbekannt (ID {aid})"


def action_category(aid: int) -> str:
    """
    Grobe Kategorie für Farbcodierung im Frontend:
      'row'      → Stein in eine Musterreihe (gut, punkteträchtig)
      'penalty'  → Stein auf die Strafleiste (defensiv/schlecht)
      'tiling'   → Tiling-Platzierung
      'dome'     → Kuppel-Aktionen
      'chip'     → Chip-/Bonus-Aktionen
      'pass'     → Pass / Tiling beenden
      'other'    → Rest
    """
    if aid in (0, 1):
        return 'pass'
    if 10 <= aid <= 249:
        a    = aid - 10
        r_id = (a // 6) % 8
        return 'penalty' if r_id == 0 else 'row'
    if 274 <= aid <= 327:
        return 'tiling'
    if 328 <= aid <= 471:
        return 'dome'
    if 472 <= aid <= 481:
        return 'chip'
    return 'other'