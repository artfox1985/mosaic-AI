"""E2E: spielt eine komplette Mensch-vs-KI-Partie über die HTTP-Routen
(Flask-Testclient). Mensch = einfache Greedy-Wahl, KI = Rust-MCTS."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

c = server.app.test_client()
AI = 1  # KI ist Spieler 2

def post(p, b=None): return c.post(p, json=b or {}).get_json()
def get(p): return c.get(p).get_json()

r = post('/api/new_game', {"names": ["Mensch", "KI"], "ai_enabled": True,
                           "ai_side": AI, "seed": 2024, "first_player": 0})
assert r["ok"], r
assert r.get("ai_player") == AI, r
print("new_game OK  ai_player:", r["ai_player"])

def free_slot(state, pi):
    g = state["players"][pi]["dome_grid"]
    for rr in range(3):
        for cc in range(3):
            if g[rr][cc] is None:
                return rr, cc
    return None

def state(): return get('/api/state')["state"]

def place_start_tiles():
    for _ in range(6):
        st = state()
        vm = st["valid_moves"]
        if not (vm and vm[0].get("type") == "start_tile_pending"):
            return
        pi = vm[0]["player"]
        if pi == AI:
            r = post('/api/ai/start_tile')
        else:
            tid = st["dome_display"][0]["id"]
            r = post('/api/move/start_tile', {"player": pi, "tile_id": tid,
                                              "slot_row": 0, "slot_col": 1, "rotation": 0})
        assert r["ok"], ("start", r)

def human_draft(st):
    vm = [m for m in st["valid_moves"] if m["type"] in ("stone", "dome_display", "bonus_chip")]
    if vm:
        m = vm[0]
        if m["type"] == "stone":
            return post('/api/move/stone', {"source": m["source"], "color": m["color"],
                                            "row": m["row"], "factory_id": m["factory_id"],
                                            "moon_order": m["moon_order"]})
        if m["type"] == "dome_display":
            return post('/api/move/dome', {"tile_id": m["tile_id"], "slot_row": m["slot_row"],
                                           "slot_col": m["slot_col"], "rotation": m.get("rotation", 0)})
        return post('/api/move/bonus_chip', {"factory_id": m["factory_id"]})
    if any(m["type"] == "dome_stack" for m in st["valid_moves"]):
        fs = free_slot(st, st["current_player"]) or (0, 0)
        peek = post('/api/stack/peek', {"num": 1})
        return post('/api/move/dome_stack', {"num_drawn": 1, "chosen_id": peek["tiles"][0]["id"],
                                             "slot_row": fs[0], "slot_col": fs[1], "rotation": 0})
    return post('/api/move/pass')

def human_tiling_place(st, pi):
    p = st["players"][pi]
    for ri, row in enumerate(p["pattern_lines"]):
        if len(row["tiles"]) != row["capacity"] or row["color"] is None:
            continue
        dr, sr = ri // 2, ri % 2
        for sc in range(3):
            slot = p["dome_grid"][dr][sc]
            if slot is None:
                continue
            for si in (sr*2, sr*2+1):
                if slot["spaces"][si]["filled"] is None and not slot["spaces"][si]["locked"]:
                    r = post('/api/tiling', {"player": pi, "pattern_row": ri,
                                             "slot_row": dr, "slot_col": sc, "space_index": si})
                    if r.get("ok"):
                        return True
        for sc in range(3):
            if p["dome_grid"][dr][sc] is not None:
                continue
            for tile in st["dome_display"]:
                for rot in (0, 90, 180, 270):
                    for si in (sr*2, sr*2+1):
                        r = post('/api/tiling', {"player": pi, "pattern_row": ri,
                                                 "slot_row": dr, "slot_col": sc, "space_index": si,
                                                 "dome_tile_id": tile["id"], "rotation": rot})
                        if r.get("ok"):
                            return True
    return False

place_start_tiles()
print("Startkacheln platziert. phase:", state()["phase"])

ai_moves = 0
debug_seen = 0
guard = 0
while state()["phase"] not in ("end", "final") and guard < 4000:
    st = state()
    ph, cur = st["phase"], st["current_player"]
    if ph == "drafting":
        if cur == AI:
            r = post('/api/ai/move')
            assert r["ok"], ("ai draft", r)
            ai_moves += 1
            if r.get("debug") and r["debug"].get("moves"):
                debug_seen += 1
        else:
            r = human_draft(st)
            assert r.get("ok"), ("human draft", r)
    elif ph == "tiling":
        # Mensch tilt zuerst komplett, dann beendet → KI tilt via /ai/move.
        if not human_tiling_place(st, 1 - AI):
            r = post('/api/end_tiling')      # Mensch beendet → wechselt zur KI
            assert r.get("ok"), ("human end_tiling", r)
            # KI tilt jetzt selbst (loop ruft /ai/move)
            while state()["phase"] == "tiling" and state()["current_player"] == AI:
                r = post('/api/ai/move')
                assert r["ok"], ("ai tiling", r)
                ai_moves += 1
    guard += 1

print(f"Spielende. phase={state()['phase']} ai_moves={ai_moves} debug_trees={debug_seen}")
hist = get('/api/ai/debug_history')
print("debug_history count:", hist["count"], "first entry has tree:",
      bool(hist["history"] and hist["history"][0].get("tree")))
res = post('/api/end_scoring')
print("end_scoring ok:", res.get("ok"), "scores:", [p["score"] for p in res["state"]["players"]])
assert ai_moves > 0 and debug_seen > 0 and hist["count"] > 0
print("OK - komplette Mensch-vs-KI-Partie ueber server.py (Rust-MCTS) durchgespielt.")
