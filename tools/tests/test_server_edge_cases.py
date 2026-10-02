"""Code-Review 2 (2026-10-02), Paket Server: Randfaelle der HTTP-Schicht.

Befunde 8 (new_game halb umgestellt), 9 (kein Zugspieler-Check), 10 (Tiling nach
end_tiling, Server-Linie), 11/12 (500er aus dem Rumpf), 13 (replay_log halb
umgestellt), 14 (Namen), 15 (Sperren, Logname). Isoliert: eigene Profil-Datei
(MOSAIC_PROFILES_PATH, Regel in player_profiles.py) und eigenes Log-Verzeichnis.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

_TMP = tempfile.mkdtemp(prefix="mosaic_server_test_")
os.environ["MOSAIC_PROFILES_PATH"] = str(Path(_TMP) / "profiles.json")

import player_profiles  # noqa: E402

# Die Anker-Tabelle (Bradley-Terry-Fit ueber das ganze Register) braucht der
# Test nicht; server.py ruft sie beim Import auf.
player_profiles.refresh_anchor_table = lambda: {}

try:
    import server  # noqa: E402
except Exception as _e:  # pragma: no cover -- ohne Flask/Wheel kein Server
    server = None
    _IMPORT_ERROR = _e


@unittest.skipIf(server is None or getattr(server, "_mr", None) is None, "server.py oder mosaic_rust fehlt")
class ServerEdgeCases(unittest.TestCase):
    def setUp(self):
        self.log_dir = Path(tempfile.mkdtemp(prefix="log_", dir=_TMP))
        server.LOG_DIR = self.log_dir
        self.client = server.app.test_client()
        r = self.post("/api/new_game", {"names": ["A", "B"], "seed": 7, "first_player": 0})
        self.assertTrue(r["ok"], r)

    def post(self, url, body=None, raw=None):
        if raw is not None:
            resp = self.client.post(url, data=raw, content_type="application/json")
        else:
            resp = self.client.post(url, json=body)
        self.assertEqual(resp.status_code, 200, resp.data[:300])
        return resp.get_json()

    def snapshot(self):
        return (server._rust, server._game_log_path, server._profile_p0, server._game_rated)

    # Befund 8 / 12
    def test_bad_new_game_leaves_running_game_untouched(self):
        before = self.snapshot()
        for body in ({"seed": -1}, {"seed": 2**64}, {"model": 123, "ai_enabled": True},
                     {"names": ["nur einer"]}, {"names": "AB"}):
            r = self.post("/api/new_game", body)
            self.assertFalse(r["ok"], body)
            self.assertEqual(self.snapshot(), before, body)
        r = self.post("/api/new_game", raw='{"teacher_sims": Infinity}')
        self.assertFalse(r["ok"])
        self.assertEqual(self.snapshot(), before)

    def test_json_list_body_is_an_error_not_a_500(self):
        for url in ("/api/profiles", "/api/new_game", "/api/move/stone", "/api/teacher/config"):
            resp = self.client.post(url, data="[1, 2]", content_type="application/json")
            self.assertEqual(resp.status_code, 200, url)

    # Befund 14
    def test_names_are_sanitised_and_distinct(self):
        r = self.post("/api/new_game", {"names": ["Te\nssa", "Te ssa"], "seed": 3})
        self.assertTrue(r["ok"], r)
        names = [p["name"] for p in r["state"]["players"]]
        self.assertEqual(names[0], "Te ssa")
        self.assertNotEqual(names[0], names[1])
        self.assertNotIn("\n", "".join(names))

    def test_create_profile_rejects_non_text_and_newlines(self):
        self.assertFalse(self.post("/api/profiles", {"name": 5})["ok"])
        self.assertFalse(self.post("/api/profiles", {"name": "a\nb"})["ok"])
        self.assertTrue(self.post("/api/profiles", {"name": "Gast"})["ok"])

    # Befund 13 / 12
    def test_replay_rejects_bad_limit_without_switching_state(self):
        before = self.snapshot()
        r = self.post("/api/debug/replay_log", {"log": server._game_log_path.name, "limit": "abc"})
        self.assertFalse(r["ok"])
        self.assertEqual(self.snapshot(), before)

    # Befund 15
    def test_new_game_refused_while_ai_search_holds_the_lock(self):
        before = self.snapshot()
        self.assertTrue(server._ai_lock.acquire(blocking=False))
        try:
            r = self.post("/api/new_game", {"names": ["X", "Y"], "seed": 9})
        finally:
            server._ai_lock.release()
        self.assertFalse(r["ok"])
        self.assertEqual(self.snapshot(), before)

    def test_log_name_collision_gets_a_suffix(self):
        a = server._create_unique_log("game_same_seed1", ["# a"])
        b = server._create_unique_log("game_same_seed1", ["# b"])
        self.assertNotEqual(a, b)
        self.assertEqual(a.read_text(encoding="utf-8"), "# a\n")

    # Befund 9
    def _place_start_tiles(self):
        for _ in range(2):
            vm = server._rust_state().get("valid_moves", [])
            self.assertEqual(vm[0].get("type"), "start_tile_pending")
            server._rust.ai_start_tile_json(vm[0]["player"], 10)
        self.assertTrue(server._rust.both_start_placed())

    def test_start_tile_only_for_the_pending_player(self):
        vm = server._rust_state()["valid_moves"]
        wrong = 1 - vm[0]["player"]
        r = self.post("/api/move/start_tile", {"player": wrong, "tile_id": 0, "slot_row": 1, "slot_col": 1})
        self.assertFalse(r["ok"])
        self.assertIn("nicht dran", r["error"])

    def test_drafting_move_refused_when_ai_is_to_move(self):
        self._place_start_tiles()
        server._ai_player = server._rust.current_player()
        try:
            for url in ("/api/move/stone", "/api/move/dome", "/api/move/bonus_chip",
                        "/api/move/dome_stack_peek", "/api/move/pass"):
                r = self.post(url, {})
                self.assertFalse(r["ok"], url)
                self.assertIn("KI ist am Zug", r["error"], url)
        finally:
            server._ai_player = None

    # Befunde 9 / 10 / 11
    def test_tiling_player_checks(self):
        with server.app.test_request_context():
            for body in ({}, {"player": "x"}, {"player": 5}, {"player": float("inf")}):
                pi, e = server._tiling_player(body)
                self.assertIsNone(pi, body)
                self.assertFalse(e.get_json()["ok"], body)
            server._ai_player = 1
            try:
                pi, e = server._tiling_player({"player": 1})
                self.assertIsNone(pi)
            finally:
                server._ai_player = None
            rnd = server._rust_state().get("round")
            server._tiling_ended.add((rnd, 0))
            pi, e = server._tiling_player({"player": 0})
            self.assertIsNone(pi)
            self.assertIn("bereits beendet", e.get_json()["error"])
            pi, e = server._tiling_player({"player": 1})
            self.assertEqual(pi, 1)

    def test_bonus_chips_bad_body_outside_tiling_is_an_error(self):
        for body in ({}, {"player": None}, {"player": 0, "pattern_row": 1, "chip_uses": "abc"}):
            r = self.post("/api/tiling/bonus_chips", body)
            self.assertFalse(r["ok"], body)


if __name__ == "__main__":
    unittest.main()
