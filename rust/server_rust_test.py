"""End-to-End-Test: treibt eine komplette Mensch-vs-Mensch-Partie über die
HTTP-Routen von server.py mit engine=rust (Flask-Testclient)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

c = server.app.test_client()

def post(path, payload=None):
    r = c.post(path, json=payload or {})
    return r.get_json()

def get(path):
    return c.get(path).get_json()

r = post('/api/new_game', {"names": ["Alice", "Bob"],
                           "ai_enabled": False, "seed": 2024, "first_player": 0})
assert r["ok"], r
st = r["state"]
print("new_game OK  seed:", r.get("seed"), "phase:", st["phase"], "scoring:", st["scoring_tile_ids"])

def free_slot(state, pi):
    grid = state["players"][pi]["dome_grid"]
    for rr in range(3):
        for cc in range(3):
            if grid[rr][cc] is None:
                return rr, cc
    return None

# Startkacheln platzieren (valid_moves -> start_tile_pending).
for _ in range(2):
    st = get('/api/state')["state"]
    vm = st["valid_moves"]
    assert len(vm) == 1 and vm[0]["type"] == "start_tile_pending", vm
    pi = vm[0]["player"]
    tid = st["dome_display"][0]["id"]
    r = post('/api/move/start_tile', {"player": pi, "tile_id": tid,
                                      "slot_row": 0, "slot_col": 1 if pi == 0 else 0,
                                      "rotation": 0})
    assert r["ok"], r
print("Startkacheln platziert.")

def drive_drafting():
    steps = 0
    while True:
        st = get('/api/state')["state"]
        if st["phase"] != "drafting":
            return steps
        vm = st["valid_moves"]
        simple = [m for m in vm if m["type"] in ("stone", "dome_display", "bonus_chip")]
        if simple:
            m = simple[0]
            if m["type"] == "stone":
                r = post('/api/move/stone', {"source": m["source"], "color": m["color"],
                                             "row": m["row"], "factory_id": m["factory_id"],
                                             "moon_order": m["moon_order"]})
            elif m["type"] == "dome_display":
                r = post('/api/move/dome', {"tile_id": m["tile_id"], "slot_row": m["slot_row"],
                                            "slot_col": m["slot_col"], "rotation": m.get("rotation", 0)})
            else:
                r = post('/api/move/bonus_chip', {"factory_id": m["factory_id"]})
        elif any(m["type"] == "dome_stack" for m in vm):
            pi = st["current_player"]
            fs = free_slot(st, pi) or (0, 0)
            peek = post('/api/stack/peek', {"num": 1})
            cid = peek["tiles"][0]["id"]
            r = post('/api/move/dome_stack', {"num_drawn": 1, "chosen_id": cid,
                                              "slot_row": fs[0], "slot_col": fs[1], "rotation": 0})
        elif st["can_pass"]:
            r = post('/api/move/pass')
        else:
            r = post('/api/move/pass')
        if not r.get("ok"):
            raise SystemExit(f"Drafting-Zug abgelehnt: {r}")
        steps += 1
        if steps > 600:
            raise SystemExit("Drafting terminiert nicht")

def try_place(st, pi):
    player = st["players"][pi]
    for ri, row in enumerate(player["pattern_lines"]):
        if len(row["tiles"]) != row["capacity"] or row["color"] is None:
            continue
        dome_row, space_row = ri // 2, ri % 2
        valid_si = [space_row * 2, space_row * 2 + 1]
        grid = player["dome_grid"]
        for sc in range(3):
            slot = grid[dome_row][sc]
            if slot is None:
                continue
            for si in valid_si:
                sp = slot["spaces"][si]
                if sp["filled"] is None and not sp["locked"]:
                    r = post('/api/tiling', {"player": pi, "pattern_row": ri,
                                             "slot_row": dome_row, "slot_col": sc,
                                             "space_index": si})
                    if r.get("ok"):
                        return True
        for sc in range(3):
            if grid[dome_row][sc] is not None:
                continue
            for tile in st["dome_display"]:
                for rot in (0, 90, 180, 270):
                    for si in valid_si:
                        r = post('/api/tiling', {"player": pi, "pattern_row": ri,
                                                 "slot_row": dome_row, "slot_col": sc,
                                                 "space_index": si, "dome_tile_id": tile["id"],
                                                 "rotation": rot})
                        if r.get("ok"):
                            return True
    return False

def drive_tiling():
    steps = 0
    while True:
        st = get('/api/state')["state"]
        if st["phase"] != "tiling":
            return steps
        pi = st["current_player"]
        if not try_place(st, pi):
            r = post('/api/end_tiling')
            if not r.get("ok"):
                raise SystemExit(f"end_tiling abgelehnt: {r}")
        steps += 1
        if steps > 200:
            raise SystemExit("Tiling terminiert nicht")

guard = 0
while True:
    st = get('/api/state')["state"]
    if st["phase"] in ("end", "final"):
        break
    rnd = st["round"]
    ds = drive_drafting()
    ts = drive_tiling()
    st = get('/api/state')["state"]
    print(f"Runde {rnd}: drafting={ds} tiling={ts} -> phase={st['phase']} round={st['round']} "
          f"scores={[p['score'] for p in st['players']]}")
    guard += 1
    if guard > 12:
        raise SystemExit("Spiel terminiert nicht")

r = post('/api/end_scoring')
assert r["ok"], r
totals = {pi: r["end_scoring"][pi]["total"] for pi in r["end_scoring"]}
print("end_scoring OK  Totals:", totals, "Endstaende:", [p["score"] for p in r["state"]["players"]])
print("OK - komplette Partie ueber server.py (engine=rust) durchgespielt.")
