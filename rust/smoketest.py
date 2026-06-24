"""Smoke-Test der PyO3-Bindings: spielt eine komplette Partie über die Rust-Engine."""
import json
import mosaic_rust as mr

print("version:", mr.version(), "ping(41):", mr.ping(41))

g = mr.PyGame(("Alice", "Bob"), first_player=0, seed=2024)
st = json.loads(g.state_json())
assert st["round"] == 1 and st["phase"] == "drafting"
print("scoring_tile_ids:", st["scoring_tile_ids"], "seed:", g.seed())

# Startkacheln: valid_moves zeigt start_tile_pending (Nicht-Startspieler zuerst).
for _ in range(2):
    st = json.loads(g.state_json())
    vm = st["valid_moves"]
    assert len(vm) == 1 and vm[0]["type"] == "start_tile_pending", vm
    pi = vm[0]["player"]
    tile_id = st["dome_display"][0]["id"]
    g.apply_start_tile(pi, tile_id, 0, 0 if pi == 1 else 1, 0)
assert g.both_start_placed()
print("Startkacheln platziert.")

def play_drafting():
    steps = 0
    while g.phase() == "drafting" and steps < 600:
        st = json.loads(g.state_json())
        vm = st["valid_moves"]
        if not vm:
            g.apply_pass(); steps += 1; continue
        m = vm[0]
        t = m["type"]
        if t == "stone":
            g.apply_stone(m["source"], m["color"], m["row"], m.get("factory_id"), m.get("moon_order"))
        elif t == "dome_display":
            g.apply_dome(m["tile_id"], m["slot_row"], m["slot_col"], m.get("rotation", 0))
        elif t == "dome_stack":
            top = json.loads(g.peek_stack_json(1))
            g.apply_dome_stack(1, top[0]["id"], _free_slot(st, st["current_player"]) or (0, 0), 0)
        elif t == "bonus_chip":
            g.apply_bonus_chip(m["factory_id"])
        else:
            g.apply_pass()
        steps += 1
    return steps

def _free_slot(st, pi):
    grid = st["players"][pi]["dome_grid"]
    for r in range(3):
        for c in range(3):
            if grid[r][c] is None:
                return (r, c)
    return None

# dome_stack braucht slot-Args separat; vereinfachte Variante umgeht das:
def play_drafting_simple():
    steps = 0
    while g.phase() == "drafting" and steps < 600:
        st = json.loads(g.state_json())
        vm = [m for m in st["valid_moves"] if m["type"] in ("stone", "dome_display", "bonus_chip")]
        if not vm:
            if st["can_pass"]:
                g.apply_pass()
            else:
                # nur dome_stack übrig -> einen Slot wählen
                allm = st["valid_moves"]
                if allm and allm[0]["type"] == "dome_stack":
                    fs = _free_slot(st, st["current_player"]) or (0, 0)
                    top = json.loads(g.peek_stack_json(1))
                    g.apply_dome_stack(1, top[0]["id"], fs[0], fs[1], 0)
                else:
                    g.apply_pass()
            steps += 1
            continue
        m = vm[0]
        if m["type"] == "stone":
            g.apply_stone(m["source"], m["color"], m["row"], m.get("factory_id"), m.get("moon_order"))
        elif m["type"] == "dome_display":
            g.apply_dome(m["tile_id"], m["slot_row"], m["slot_col"], m.get("rotation", 0))
        else:
            g.apply_bonus_chip(m["factory_id"])
        steps += 1
    return steps

def play_tiling():
    steps = 0
    while g.phase() == "tiling" and steps < 200:
        st = json.loads(g.state_json())
        rows = st["valid_tiling_rows"]
        pi = st["current_player"]
        mine = [r for r in rows if r["pi"] == pi]
        if mine:
            # Eine konkrete Aktion über generate ableiten: erste platzierbare Reihe,
            # passenden Slot/Space via dome_grid suchen ist komplex -> nutze
            # pending_tiling_count + brute force über bekannte Felder.
            placed = _try_place_any(st, pi)
            if not placed:
                g.end_tiling(pi)
        else:
            g.end_tiling(pi)
        steps += 1
    return steps

def _try_place_any(st, pi):
    """Versucht, irgendeine volle Reihe zu legen, indem alle Slot/Space-Kombis getestet werden."""
    player = st["players"][pi]
    for ri, row in enumerate(player["pattern_lines"]):
        if len(row["tiles"]) != row["capacity"] or row["color"] is None:
            continue
        dome_row = ri // 2
        space_row = ri % 2
        valid_si = [space_row * 2, space_row * 2 + 1]
        grid = player["dome_grid"]
        # bestehende Slots
        for sc in range(3):
            slot = grid[dome_row][sc]
            if slot is None:
                continue
            for si in valid_si:
                sp = slot["spaces"][si]
                if sp["filled"] is None and not sp["locked"]:
                    try:
                        g.apply_tiling(pi, ri, dome_row, sc, si, None, 0)
                        return True
                    except ValueError:
                        pass
        # neue Kachel aus Display
        for sc in range(3):
            if grid[dome_row][sc] is not None:
                continue
            for tile in st["dome_display"]:
                for rot in (0, 90, 180, 270):
                    for si in valid_si:
                        try:
                            g.apply_tiling(pi, ri, dome_row, sc, si, tile["id"], rot)
                            return True
                        except ValueError:
                            pass
    return False

total_steps = 0
guard = 0
while g.phase() not in ("end", "final") and guard < 12:
    r = g.round_number()
    ds = play_drafting_simple()
    ts = play_tiling()
    total_steps += ds + ts
    print(f"Runde {r}: drafting={ds} tiling={ts} -> phase={g.phase()} round={g.round_number()} scores={g.scores()}")
    guard += 1

print("Spielende. phase:", g.phase(), "is_over:", g.is_over())
res = json.loads(g.end_scoring_json())
totals = {pi: res["end_scoring"][pi]["total"] for pi in res["end_scoring"]}
print("Endwertung-Totals je Spieler:", totals)
print("Endstaende:", g.scores(), "phase:", g.phase())
print("OK - komplette Partie ueber die Rust-Engine durchgespielt.")
