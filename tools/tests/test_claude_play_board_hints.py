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


def stack_state(current_player, phase="drafting"):
    """Zustand mit Kuppelstapel-Wissen: 4 verdeckte Platten, ein eigener und ein fremder Block."""
    return {
        "phase": phase,
        "current_player": current_player,
        "dome_stack_count": 4,
        "dome_wild_remaining_frac": 0.75,
        "dome_pool_mask": [1 if i in (2, 5) else 0 for i in range(18)],
        "dome_display": [{"id": 5, "spaces": [space("gelb"), space("rot"),
                                              space(None, "WILD"), space("blau")]}],
        "players": [],
        "dome_pool_view": {
            "unknown_prefix": 1,
            "blocks": [
                {"own": True, "len": 2, "special": 1, "wild": 1, "types": ["special", "wild"]},
                {"own": False, "len": 1, "special": 0, "wild": 1, "types": None},
            ],
        },
    }


class StackKnowledge(unittest.TestCase):
    """Die Stapel-Anzeige traegt die Groessen, die der Encoder seit v28-b02 bekommt
    (`features.rs:274-286` Maske und Wild-Anteil, `features.rs:744-754` Rueckgabe-Wissen);
    bis 2026-09-13 fehlten sie im Fenster (Sicht-Audit par.11b)."""

    def test_mask_and_wild_split(self):
        line = cp.stack_lines(stack_state(0), {"me": 0})[0]
        self.assertIn("3 wild / 1 spezial", line)   # 0,75 von 4
        self.assertIn("#2", line)
        self.assertIn("#5", line)

    def test_design_shown_only_when_the_plate_lies_open(self):
        line = cp.stack_lines(stack_state(0), {"me": 0})[0]
        # #5 liegt in der Auslage, sein Design ist oeffentlich; #2 lag nie offen.
        self.assertIn("#5[gr/*b]", line)
        self.assertNotIn("#2[", line)

    def test_pool_view_is_shown_when_claude_is_to_move(self):
        lines = cp.stack_lines(stack_state(0), {"me": 0})
        self.assertEqual(len(lines), 2, lines)
        self.assertIn("1 unbekannt", lines[1])
        self.assertIn("EIGEN 2: S W", lines[1])
        self.assertIn("fremd 1: 1W 0S", lines[1])

    def test_pool_view_is_hidden_while_the_net_is_to_move(self):
        """WAECHTER: `dome_pool_view` gilt fuer den Spieler AM ZUG (serialize.rs:99) -- ist die
        KI dran, waere das `own`-Flag ihres, und die Reihenfolge ihrer Rueckgabe."""
        self.assertEqual(len(cp.stack_lines(stack_state(1), {"me": 0})), 1)

    def test_pool_view_is_hidden_after_the_game(self):
        self.assertEqual(len(cp.stack_lines(stack_state(0, phase="end"), {"me": 0})), 1)


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


def moon_state(rows=None):
    """Zustand mit Mondbestand: drei kleine Stapel (oben tuerkis, blau, tuerkis) und ein
    Pool der grossen Fabrik mit zwei Tuerkis. Aktion C auf Tuerkis nimmt also 2 + 2 = 4."""
    return {
        "phase": "drafting",
        "current_player": 1,
        "factories": [
            {"id": 1, "sun": [], "moon": [["blau", "türkis"]]},          # oben tuerkis
            {"id": 2, "sun": [], "moon": [["türkis", "blau"]]},          # oben blau
            {"id": 3, "sun": [], "moon": [["rot", "rot", "türkis"]]},    # oben tuerkis
            {"id": 4, "sun": [], "moon": []},                            # leer
        ],
        "large_factory": {"sun": [], "moon": ["türkis", "gelb", "türkis"], "marker": False},
        "players": [
            {"pattern_lines": []},
            {"pattern_lines": rows if rows is not None else [
                {"index": 0, "capacity": 1, "color": None, "tiles": []},
                {"index": 1, "capacity": 2, "color": None, "tiles": []},
                {"index": 3, "capacity": 4, "color": None, "tiles": []},
            ]},
        ],
        "valid_moves": [
            {"type": "stone", "source": "SMALL_FACTORY_MOON", "factory_id": None,
             "color": "türkis", "row": r, "moon_order": []} for r in (0, 1, 3, -1)
        ] + [
            {"type": "stone", "source": "SMALL_FACTORY_SUN", "factory_id": 2,
             "color": "blau", "row": 1, "moon_order": []},
        ],
    }


class MoonTakeCount(unittest.TestCase):
    """Die Stueckzahl eines Mondzugs (par.13). Zaehlweise geprueft an `execution.rs:262-300`:
    je kleinem Stapel HOECHSTENS EINER, und nur wenn er oben liegt (`factory.rs:86-108`,
    Index 0 = unten), aus dem Pool der grossen Fabrik dagegen ALLE der Farbe
    (`factory.rs:196-208`)."""

    def test_counts_tops_and_the_whole_pool(self):
        self.assertEqual(cp.moon_take_count(moon_state(), "türkis"), 4)   # 2 Spitzen + 2 Pool

    def test_buried_tiles_do_not_count(self):
        # Blau liegt in F1 und F3 unten und in F2 oben -> nur der eine zaehlt.
        self.assertEqual(cp.moon_take_count(moon_state(), "blau"), 1)

    def test_pool_only(self):
        self.assertEqual(cp.moon_take_count(moon_state(), "gelb"), 1)

    def test_absent_colour_is_zero(self):
        self.assertEqual(cp.moon_take_count(moon_state(), "schwarz"), 0)


class OverflowWarning(unittest.TestCase):
    """Die Warnzeile ist der eigentliche Zweck: viermal in g08-g10 sind Steine auf die
    Strafleiste gefallen, weil die Stueckzahl nirgends stand (par.13, -15 Punkte)."""

    def test_line_carries_count_and_overflow(self):
        out = cp.legal_moves_text(moon_state(), {"me": 1})
        line = [l for l in out.splitlines() if l.startswith("  s m ")][0]
        self.assertIn("s m türkis x4", line)
        self.assertIn("UEBERLAUF", line)
        self.assertIn("R0 +3", line)   # Kapazitaet 1, vier Steine
        self.assertIn("R1 +2", line)
        self.assertNotIn("R3", line.split("UEBERLAUF")[1])  # Kapazitaet 4 fasst alle

    def test_partly_filled_row_counts_only_the_free_places(self):
        rows = [{"index": 3, "capacity": 4, "color": "türkis", "tiles": ["türkis", "türkis"]}]
        st = moon_state(rows)
        st["valid_moves"] = [v for v in st["valid_moves"] if v.get("row") in (3, -1)]
        line = [l for l in cp.legal_moves_text(st, {"me": 1}).splitlines() if l.startswith("  s m ")][0]
        self.assertIn("R3 +2", line)   # 4 Steine, nur zwei Plaetze frei

    def test_no_warning_when_everything_fits(self):
        rows = [{"index": 5, "capacity": 6, "color": None, "tiles": []}]
        st = moon_state(rows)
        st["valid_moves"] = [{"type": "stone", "source": "SMALL_FACTORY_MOON", "factory_id": None,
                              "color": "türkis", "row": 5, "moon_order": []}]
        line = [l for l in cp.legal_moves_text(st, {"me": 1}).splitlines() if l.startswith("  s m ")][0]
        self.assertIn("x4", line)
        self.assertNotIn("UEBERLAUF", line)

    def test_sun_moves_keep_their_old_shape(self):
        """Nur Aktion C bekommt die Zahl -- bei einer Sonnenseite steht die Stueckzahl
        ablesbar in der Fabrikzeile, und die Zeile soll nicht laenger werden."""
        line = [l for l in cp.legal_moves_text(moon_state(), {"me": 1}).splitlines()
                if l.startswith("  s 2 ")][0]
        self.assertEqual(line, "  s 2 blau 1")


class MoveParserTolerance(unittest.TestCase):
    def test_count_token_is_ignored(self):
        """Wer die Zeile samt Anzeige kopiert, soll nicht abgewiesen werden."""
        calls = []

        class G:
            def state_json(self):
                import json as _j
                return _j.dumps({"valid_moves": []})

            def apply_stone(self, *a):
                calls.append(a)

        cp.apply_move(G(), {"me": 1}, "s m türkis x4 3")
        self.assertEqual(calls, [("SMALL_FACTORY_MOON", "türkis", 3, None, None)])


if __name__ == "__main__":
    unittest.main()
