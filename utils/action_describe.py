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
        row_str = 'Strafleiste' if r_id == 0 else f'Reihe {r_id}'
        return f"{color} von {source} → {row_str}"

    # Tiling: 274 - 327
    if 274 <= aid <= 327:
        return f"Tiling-Platzierung (#{aid - 274})"

    # Dome: 328 - 435
    if 328 <= aid <= 435:
        return f"Kuppel setzen (#{aid - 328})"

    # Dome-Stack: 436 - 471
    if 436 <= aid <= 471:
        return f"Kuppel vom Stapel (#{aid - 436})"

    # Use-Chips: 472 - 477
    if 472 <= aid <= 477:
        return f"Chips einsetzen (#{aid - 472})"

    # Bonus-Chip: 478 - 481
    if 478 <= aid <= 481:
        return f"Bonus-Chip ({COLORS[aid - 478]})" if (aid - 478) < len(COLORS) else f"Bonus-Chip (#{aid - 478})"

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
