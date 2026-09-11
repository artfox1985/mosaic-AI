# -*- coding: utf-8 -*-
"""Die Brett-Hilfen von `tools/claude_play.py` an nachgebauten Stellungen.

Der Anlass ist konkret: in g07 Runde 4 wurde Platte #10 auf Slot (2,1) mit Rotation 0 statt
180 gelegt. Dadurch landete ihre Schwarz-Zelle in z5 statt z4, die zwei geparkten Schwarz in
R4 verloren ihre letzte Zielzelle und wurden beim Tiling zwangsgeraeumt (rund -5 Punkte).
`forced_clears_after` ist genau die Vorschau, die das gezeigt haette; dieser Test haelt die
Stellung fest, damit die Rechnung nicht wieder still kaputtgeht.
"""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import claude_play as cp  # noqa: E402


def space(color=None, kind="NORMAL", filled=None):
    return {"type": kind, "color": color, "filled": filled}


def slot(*spaces):
    return {"spaces": list(spaces)}


def g07_round4_board():
    """z4/z5 von Claude kurz vor der Plattenwahl in g07 Runde 4; Slot (2,1) ist noch frei.

    z4: t G g . g r      z5: * s s . * b
    R4 haelt zwei Schwarz (Kapazitaet 5).
    """
    grid = [[None] * 3 for _ in range(3)]
    grid[2][0] = slot(space("türkis"), space("gelb", filled="gelb"), space(None, "WILD"), space("schwarz"))
    grid[2][2] = slot(space("gelb"), space("rot"), space(None, "WILD"), space("blau"))
    pl = {
        "dome_grid": grid,
        "pattern_lines": [
            {"index": 4, "capacity": 5, "color": "schwarz", "tiles": ["schwarz", "schwarz"]},
        ],
    }
    return pl


# Platte #10 aus der Auslage: [gelb, SPEZIAL, schwarz, rot] (Reihenfolge oben-links,
# oben-rechts, unten-links, unten-rechts).
TILE_10 = [space("gelb"), space(None, "SPECIAL"), space("schwarz"), space("rot")]


def rotated(spaces, deg):
    return [spaces[i] for i in cp.ROTATION_INDICES[deg]]


class ForcedClearPreview(unittest.TestCase):
    def test_rotation_0_orphans_the_black_row(self):
        """Der tatsaechlich gespielte Zug: Schwarz landet auf (5,2), z4 bleibt ohne Schwarz."""
        hits = cp.forced_clears_after(g07_round4_board(), 2, 1, rotated(TILE_10, 0))
        self.assertEqual(len(hits), 1, hits)
        self.assertIn("R4", hits[0])

    def test_rotation_180_keeps_a_home(self):
        """Die bessere Wahl: Schwarz auf (4,3) -- keine Zwangsraeumung."""
        self.assertEqual(cp.forced_clears_after(g07_round4_board(), 2, 1, rotated(TILE_10, 180)), [])

    def test_open_slot_is_never_a_forced_clear(self):
        """Solange ein Slot der Kuppelzeile frei ist, bleiben die Steine liegen."""
        pl = g07_round4_board()
        pl["dome_grid"][2][2] = None  # Slot (2,2) wieder offen
        self.assertEqual(cp.forced_clears_after(pl, 2, 1, rotated(TILE_10, 0)), [])

    def test_empty_row_is_not_at_risk(self):
        """Eine leere Musterreihe kann nicht geraeumt werden."""
        pl = g07_round4_board()
        pl["pattern_lines"][0]["tiles"] = []
        pl["pattern_lines"][0]["color"] = None
        self.assertEqual(cp.forced_clears_after(pl, 2, 1, rotated(TILE_10, 0)), [])


class RotationTable(unittest.TestCase):
    def test_matches_engine(self):
        """engine/src/dome.rs:89-97 -- rotated[i] = spaces[perm[i]] (dome.rs:162-165)."""
        self.assertEqual(cp.ROTATION_INDICES[0], (0, 1, 2, 3))
        self.assertEqual(cp.ROTATION_INDICES[90], (2, 0, 3, 1))
        self.assertEqual(cp.ROTATION_INDICES[180], (3, 2, 1, 0))
        self.assertEqual(cp.ROTATION_INDICES[270], (1, 3, 0, 2))

    def test_180_twice_is_identity(self):
        self.assertEqual(rotated(rotated(TILE_10, 180), 180), TILE_10)


class SpecialAndCriteria(unittest.TestCase):
    def test_special_line_names_the_missing_cells(self):
        pl = g07_round4_board()
        pl["dome_grid"][2][1] = slot(*rotated(TILE_10, 0))
        lines = cp.special_lines(pl)
        self.assertEqual(len(lines), 1, lines)
        # Rotation 0 legt das Spezialfeld auf (4,3) -- Rasterzeile 5, also +5 beim Freischalten.
        # Fehlen tun die drei anderen Zellen DERSELBEN Platte: (4,2) gelb, (5,2) schwarz,
        # (5,3) rot. Genau so stand es in g07 auf dem Brett ("z4 t G g # g r").
        self.assertIn("(4,3) +5", lines[0])
        for cell in ("(4,2)", "(5,2)", "(5,3)"):
            self.assertIn(cell, lines[0])

    def test_colour_rich_row_counts_distinct_colours(self):
        """Farbenreiche Reihen: Spezialfliesen zaehlen als keine Farbe."""
        grid = [[None] * 3 for _ in range(3)]
        grid[0][0] = slot(space("rot", filled="rot"), space("gelb", filled="gelb"),
                          space("blau"), space("türkis"))
        grid[0][1] = slot(space("schwarz", filled="schwarz"), space("türkis", filled="türkis"),
                          space("blau"), space("rot"))
        grid[0][2] = slot(space(None, "SPECIAL", filled="special"), space("blau", filled="blau"),
                          space("gelb"), space("rot"))
        pl = {"dome_grid": grid, "pattern_lines": []}
        # z0 traegt rot, gelb, schwarz, tuerkis, blau = fuenf Farben, die Spezialfliese zaehlt nicht.
        self.assertEqual(cp._filled_colors_in_row(grid, 0),
                         {"rot", "gelb", "schwarz", "türkis", "blau"})
        self.assertIn("1 fertig z0", cp._criterion_state(pl, "farben"))

    def test_outer_counts_only_the_edge(self):
        grid = [[None] * 3 for _ in range(3)]
        grid[1][1] = slot(space("rot", filled="rot"), space("gelb", filled="gelb"),
                          space("blau", filled="blau"), space("türkis", filled="türkis"))
        pl = {"dome_grid": grid, "pattern_lines": []}
        # Slot (1,1) deckt (2,2), (2,3), (3,2), (3,3) -- keine davon liegt am Rand.
        self.assertEqual(cp._criterion_state(pl, "aussen"), "0 Fliesen am Rand")


class FakeGame:
    """Nur so viel Engine, wie `resolve_moon_order` liest."""

    def __init__(self, moon_order):
        import json
        self._json = json.dumps({"valid_moves": [
            {"type": "stone", "source": "SMALL_FACTORY_SUN", "factory_id": 1,
             "color": "gelb", "row": 2, "moon_order": moon_order}]})

    def state_json(self):
        return self._json


class MoonOrder(unittest.TestCase):
    """Weglassen darf man die Reihenfolge nur, wenn es nichts zu entscheiden gibt.

    Der Zuggenerator liefert je (Quelle, Farbe, Reihe) nur EINE Reihenfolge -- abweichende
    sind trotzdem legal, weil `apply_stone` die Menge prueft. Die Wahlfreiheit haengt also
    an der Laenge der Restliste, nicht an der Zahl der Zugeintraege.
    """

    def test_single_leftover_is_unambiguous(self):
        self.assertEqual(cp.resolve_moon_order(FakeGame(["blau"]), "1", "gelb", 2), ["blau"])

    def test_same_colour_leftovers_are_unambiguous(self):
        self.assertEqual(cp.resolve_moon_order(FakeGame(["rot", "rot", "rot"]), "1", "gelb", 2),
                         ["rot", "rot", "rot"])

    def test_no_leftovers_needs_nothing(self):
        self.assertEqual(cp.resolve_moon_order(FakeGame([]), "1", "gelb", 2), [])

    def test_mixed_leftovers_must_be_stated(self):
        with self.assertRaises(SystemExit) as ctx:
            cp.resolve_moon_order(FakeGame(["blau", "rot"]), "1", "gelb", 2)
        self.assertIn("mond:", str(ctx.exception))

    def test_source_key_matches_the_display(self):
        """Aktion C kommt ohne Fabrik-Id und heisst 'm' (moves.rs:39)."""
        self.assertEqual(cp.move_source_key({"source": "SMALL_FACTORY_MOON", "factory_id": None}), "m")
        self.assertEqual(cp.move_source_key({"source": "SMALL_FACTORY_SUN", "factory_id": 3}), "3")
        self.assertEqual(cp.move_source_key({"source": "LARGE_FACTORY_SUN"}), "gf")


if __name__ == "__main__":
    unittest.main()
