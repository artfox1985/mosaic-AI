# -*- coding: utf-8 -*-
"""Mondreihenfolge eines Netz-Steinzugs aus den `choose_moon_top`-Zeilen
(Befund 2026-10-08, PREREG_claude_play_interface.md par.14a Werkzeug-Befund 1).

Das `#a`-Feld `moon_order` eines Netz-Steinzugs traegt nur die KANONISCHE
Restreihenfolge; die gespielte steht in den folgenden `choose_moon_top`-Zeilen
desselben Spielers. Der Replayer leitet sie dort ab
(`Replayer.derive_moon_order_from_nodes`) und probiert sie VOR Hinweis- und
kanonischer Reihenfolge.

Zwei Ebenen:
  * ohne Engine-Rechnung: Ableitung und Kandidatenliste (`Replayer` als Doppel);
  * mit Engine (`mosaic_rust`, echte Replays): ein Ausschnitt aus einer echten
    Partie Mensch gegen Netz (Runde 1, Zeilen bis zum dritten Netz-Mondknoten,
    `static/log/game_20261003_113013_seed576020.log`; Kopfzeile auf die vom
    Replayer gelesenen Felder gekuerzt), einmal so, wie er geloggt wurde, einmal
    ohne Knotenzeilen und einmal mit Knoten unter fremdem Spieler."""
import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import analyze_game_log as agl  # noqa: E402

HEADER = {"timestamp": "20261003_113013", "seed": 576020,
          "players": ["Spieler 1", "Tessa"], "first_player": 1}

# Original-Zeilen 4-32 des oben genannten Logs, unveraendert. Drei Netz-Steinzuege
# mit Knoten; der erste und der dritte weichen von der kanonischen Reihenfolge ab
# (der Bestand brach am ersten mit "Divergenz bei Original-Zeile 8" ab).
EXCERPT = """[R1] Spiel gestartet. Tessa beginnt.
[R1] Wertungsplatten gewählt: [2, 1, 0]
[R1] Spieler 1: Startkachel 6 → (0,0) rot=180°
[R1] Tessa: Startkachel 4 → (2,0) rot=180°
#a {"a":{"color":"türkis","factory_index":4,"moon_order":[],"row":4,"type":"stone"},"id":236,"p":1}
[R1] ☀️  Tessa: 2× türkis von GF → Reihe 5 [2/5]
#a {"a":{"color":"blau","factory_id":null,"moon_order":[],"row":0,"source":"SMALL_FACTORY_MOON","type":"stone"},"id":21,"p":0}
[R1] ❖ Spieler 1: Startspielerstein genommen (−2 Pkt am Rundenende → aktuell 5 Pkt)
[R1] 🌙 Spieler 1: 1 (1)× blau von GF → Reihe 1 [1/1]
[R1] 🌙 GF Moon-Pool: (schwarz, gelb)
#a {"a":{"color":"schwarz","factory_index":3,"moon_order":["türkis","gelb","blau"],"row":5,"type":"stone"},"id":193,"p":1}
[R1] ☀️  Tessa: 1× schwarz von F4 → Reihe 6 [1/6]
#a {"a":{"color":"türkis","type":"choose_moon_top"},"id":410,"p":1}
#a {"a":{"color":"blau","type":"choose_moon_top"},"id":406,"p":1}
[R1] 🌙 F4 Mond-Stapel: (gelb, blau→türkis)
#a {"a":{"color":"schwarz","factory_id":null,"moon_order":[],"row":1,"source":"SMALL_FACTORY_MOON","type":"stone"},"id":171,"p":0}
[R1] 🌙 Spieler 1: 1 (1)× schwarz von GF → Reihe 2 [1/2]
[R1] 🌙 GF Moon-Pool: (gelb)
#a {"a":{"color":"schwarz","factory_index":0,"moon_order":["türkis","gelb","rot"],"row":5,"type":"stone"},"id":190,"p":1}
[R1] ☀️  Tessa: 1× schwarz von F1 → Reihe 6 [2/6]
#a {"a":{"color":"türkis","type":"choose_moon_top"},"id":410,"p":1}
#a {"a":{"color":"rot","type":"choose_moon_top"},"id":408,"p":1}
[R1] 🌙 F1 Mond-Stapel: (gelb, rot→türkis)
#a {"a":{"color":"schwarz","factory_id":3,"moon_order":["gelb","rot","gelb"],"row":1,"source":"SMALL_FACTORY_SUN","type":"stone"},"id":168,"p":0}
[R1] ☀️  Spieler 1: 1× schwarz von F3 → Reihe 2 [2/2]
[R1] 🌙 F3 Mond-Stapel: (gelb, rot→gelb)
#a {"a":{"color":"türkis","factory_index":1,"moon_order":["rot","gelb","blau"],"row":4,"type":"stone"},"id":233,"p":1}
[R1] ☀️  Tessa: 1× türkis von F2 → Reihe 5 [3/5]
#a {"a":{"color":"rot","type":"choose_moon_top"},"id":408,"p":1}
#a {"a":{"color":"gelb","type":"choose_moon_top"},"id":407,"p":1}
[R1] 🌙 F2 Mond-Stapel: (blau, gelb→rot)
"""


def _line(raw: str) -> agl.LogLine:
    m = agl.ROUND_PREFIX.match(raw)
    return agl.LogLine(int(m.group(1)), raw, m.group(2))


def _stone(order, p=1, id_=193):
    return {"a": {"color": "schwarz", "factory_index": 3, "moon_order": list(order),
                  "row": 5, "type": "stone"}, "id": id_, "p": p}


def _node(color, p=1):
    return {"a": {"color": color, "type": "choose_moon_top"}, "id": 406, "p": p}


def _bare_replayer(hints):
    rep = agl.Replayer.__new__(agl.Replayer)
    rep.hints = hints
    rep.moon_order_from_nodes = 0
    rep.hint_used = 0
    rep.hint_missing = 0
    rep.sun_used = {1: False, 2: False, 3: False, 4: False, "GF": False}
    return rep


ACTION = _line("[R1] ☀️  Tessa: 1× schwarz von F4 → Reihe 6 [1/6]")
STACK = _line("[R1] 🌙 F4 Mond-Stapel: (gelb, blau→türkis)")
NEXT_ACTION = _line("[R1] 🌙 Spieler 1: 1 (1)× schwarz von GF → Reihe 2 [1/2]")
LINES = [ACTION, STACK, NEXT_ACTION]


class DeriveMoonOrderTest(unittest.TestCase):
    """Ableitung ohne Engine: Regel wie `PendingMoonOrder::resolved_bottom_up`
    (engine/src/moves.rs:132-136), Entfernen des ERSTEN Vorkommens
    (engine/src/game.rs:1145, 1154)."""

    def test_non_canonical_choice_is_derived(self):
        stone = _stone(["türkis", "gelb", "blau"])
        rep = _bare_replayer({0: [stone], 1: [_node("türkis"), _node("blau")]})
        self.assertEqual(rep.derive_moon_order_from_nodes(LINES, 0, stone),
                         ["gelb", "blau", "türkis"])

    def test_duplicate_colours_remove_first_occurrence(self):
        # g11 R3: Rest (türkis, gelb, gelb), zweimal gelb gewaehlt.
        stone = _stone(["türkis", "gelb", "gelb"])
        rep = _bare_replayer({0: [stone], 1: [_node("gelb"), _node("gelb")]})
        self.assertEqual(rep.derive_moon_order_from_nodes(LINES, 0, stone),
                         ["türkis", "gelb", "gelb"])

    def test_without_node_lines_none(self):
        stone = _stone(["türkis", "gelb", "blau"])
        rep = _bare_replayer({0: [stone]})
        self.assertIsNone(rep.derive_moon_order_from_nodes(LINES, 0, stone))

    def test_nodes_of_other_player_are_not_used(self):
        stone = _stone(["türkis", "gelb", "blau"], p=1)
        rep = _bare_replayer({0: [stone], 1: [_node("türkis", p=0), _node("blau", p=0)]})
        self.assertIsNone(rep.derive_moon_order_from_nodes(LINES, 0, stone))

    def test_foreign_node_stops_the_scan(self):
        # Erst ein fremder Knoten, dann ein eigener: der eigene liegt hinter der
        # Sperre und zaehlt nicht.
        stone = _stone(["türkis", "gelb", "blau"], p=1)
        rep = _bare_replayer({0: [stone], 1: [_node("türkis", p=0), _node("blau", p=1)]})
        self.assertIsNone(rep.derive_moon_order_from_nodes(LINES, 0, stone))

    def test_nodes_after_the_stack_line_belong_elsewhere(self):
        # Knoten vor der NAECHSTEN Aktionszeile gehoeren nicht zu diesem Zug:
        # die Suche endet an der Mond-Stapel-Zeile.
        stone = _stone(["türkis", "gelb", "blau"])
        rep = _bare_replayer({0: [stone], 2: [_node("türkis"), _node("blau")]})
        self.assertIsNone(rep.derive_moon_order_from_nodes(LINES, 0, stone))

    def test_colour_outside_the_rest_falls_back(self):
        stone = _stone(["türkis", "gelb", "blau"])
        rep = _bare_replayer({0: [stone], 1: [_node("rot"), _node("blau")]})
        self.assertIsNone(rep.derive_moon_order_from_nodes(LINES, 0, stone))

    def test_hint_without_two_rest_tiles_none(self):
        stone = _stone(["gelb"])
        rep = _bare_replayer({0: [stone], 1: [_node("gelb")]})
        self.assertIsNone(rep.derive_moon_order_from_nodes(LINES, 0, stone))


class _FakeGame:
    def __init__(self, valid_moves):
        self._st = json.dumps({"valid_moves": valid_moves})

    def state_json(self):
        return self._st


class CandidateListTest(unittest.TestCase):
    """Die Kandidatenliste des ID-Wegs: mit Knoten steht deren Reihenfolge
    vorn, ohne Knoten ist die Liste Eintrag fuer Eintrag die des Bestands
    (Hinweis, dann kanonisch, Duplikate entfernt)."""

    MOVE = {"type": "stone", "id": 193, "source": "SMALL_FACTORY_SUN", "color": "schwarz",
            "row": 5, "factory_id": 4, "moon_order": ["türkis", "gelb", "blau"]}

    def _candidates(self, hints, hint_order=None):
        rep = _bare_replayer(hints)
        rep.g = _FakeGame([dict(self.MOVE)])
        seen = {}

        def capture(lines, li, method, cand_calls):
            seen["calls"] = cand_calls
            return li + 1
        rep.apply_ambiguous = capture
        m = agl.PATTERNS["SUN_TAKE"].match(ACTION.body)
        self.assertIsNotNone(m)
        rep.resolve_stone(LINES, 0, m, False, 1)
        return [c[0][4] for c in seen["calls"]], rep

    def test_nodes_put_the_played_order_first(self):
        stone = _stone(["türkis", "gelb", "blau"])
        orders, rep = self._candidates({0: [stone], 1: [_node("türkis"), _node("blau")]})
        self.assertEqual(orders, [["gelb", "blau", "türkis"], ["türkis", "gelb", "blau"]])
        self.assertEqual(rep.moon_order_from_nodes, 1)

    def test_without_nodes_list_is_unchanged(self):
        stone = _stone(["türkis", "gelb", "blau"])
        orders, rep = self._candidates({0: [stone]})
        self.assertEqual(orders, [["türkis", "gelb", "blau"]])
        self.assertEqual(rep.moon_order_from_nodes, 0)

    def test_without_nodes_hint_then_canonical(self):
        # Bestandsfall mit abweichendem Hinweis (Mensch ueber die API):
        # erst Hinweis, dann kanonisch -- wie vor dem Fix.
        stone = _stone(["blau", "gelb", "türkis"])
        orders, _ = self._candidates({0: [stone]})
        self.assertEqual(orders, [["blau", "gelb", "türkis"], ["türkis", "gelb", "blau"]])

    def test_foreign_nodes_leave_list_unchanged(self):
        stone = _stone(["türkis", "gelb", "blau"], p=1)
        orders, rep = self._candidates({0: [stone], 1: [_node("türkis", p=0), _node("blau", p=0)]})
        self.assertEqual(orders, [["türkis", "gelb", "blau"]])
        self.assertEqual(rep.moon_order_from_nodes, 0)


def _write_log(directory: pathlib.Path, body: str) -> pathlib.Path:
    path = directory / "game_excerpt.log"
    path.write_text("# MOSAIC GAME LOG\n# " + json.dumps(HEADER, ensure_ascii=False) + "\n"
                    + "# " + "=" * 60 + "\n" + body, encoding="utf-8")
    return path


def _replay(body: str):
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_log(pathlib.Path(tmp), body)
        with contextlib.redirect_stdout(io.StringIO()):
            return agl.run(path, model_path=None, sims=1, c_puct=0.3, do_oracle=False, limit=None)


class RealReplayTest(unittest.TestCase):
    """Echte Replays ueber `mosaic_rust` (PyGame + apply_stone mit moon_order)."""

    def test_a_logged_excerpt_replays_without_divergence(self):
        rep, lines, li, div = _replay(EXCERPT)
        self.assertIsNone(div, div)
        self.assertEqual(li, len(lines))
        self.assertEqual(rep.moon_order_from_nodes, 3)

    def test_b_without_node_lines_old_behaviour(self):
        # Knotenzeilen entfernt: der Hinweis traegt nur die kanonische Folge, die
        # das Original nicht reproduziert -- Abbruch an derselben Stelle wie im
        # Bestand (Original-Zeile 8, erste Mond-Stapel-Abweichung).
        body = "\n".join(l for l in EXCERPT.split("\n") if "choose_moon_top" not in l)
        rep, _lines, li, div = _replay(body)
        self.assertIsNotNone(div)
        self.assertIn("Original-Zeile 8", div)
        self.assertEqual(rep.moon_order_from_nodes, 0)

    def test_c_nodes_of_other_player_are_ignored(self):
        body = EXCERPT.replace('"type":"choose_moon_top"},"id":410,"p":1',
                               '"type":"choose_moon_top"},"id":410,"p":0')
        body = body.replace('"type":"choose_moon_top"},"id":406,"p":1',
                            '"type":"choose_moon_top"},"id":406,"p":0')
        rep, _lines, li, div = _replay(body)
        self.assertIsNotNone(div)
        self.assertIn("Original-Zeile 8", div)


class WorkaroundSwitchTest(unittest.TestCase):
    def test_claude_play_no_longer_rewrites_logs(self):
        import claude_play
        self.assertFalse(claude_play.NORMALIZE_MOON_HINTS_BEFORE_REPLAY)
        self.assertTrue(callable(claude_play.normalize_moon_hints))


if __name__ == "__main__":
    unittest.main()
