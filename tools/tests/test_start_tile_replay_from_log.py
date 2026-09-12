# -*- coding: utf-8 -*-
"""Die Startsetzung des Replays kommt AUS DEM LOG, nicht aus der Handregel.

Anlass (2026-09-12): der A/B-Lauf mit `MOSAIC_START_BY_SEARCH=1`
(`paired_gating_v28-b02_startsearch_vs_v28-b02_s48.json`) war zu 190 von 190
Partien nicht replaybar, und der erste Verdacht war, der Replayer loese die
Startsetzung per Handregel (`self_play::choose_start_placement`) auf statt aus
der `Startkachel`-Logzeile. Dieser Test haelt fest, dass das NICHT so ist:
`_run_loop` reicht Platte, Slot und Rotation BEIDER Spieler unveraendert an
`apply_start_tile` weiter -- auch den gesuchten Slot (2,0) rot=90, den die
Handregel nie waehlen wuerde.

Ohne Engine-Rechnung: geprueft wird die Zeilen-Klassifikation und der
Dispatch, die `Replayer`-Instanz ist ein Doppel."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import analyze_game_log as agl  # noqa: E402

# Zwei echte Zeilen aus dem Arena-Artefakt oben (Partie 0, Seed 20261048).
# Der NICHT-Starter legt zuerst (game.rs::apply_start_placement erzwingt die
# Reihenfolge), deshalb steht NetzB vor NetzA.
LINE_B = "[R1] NetzB: Startkachel 3 → (0,0) rot=0°"
LINE_A = "[R1] NetzA: Startkachel 4 → (2,0) rot=90°"


class StartTileLineTest(unittest.TestCase):
    def test_both_lines_classify_with_all_fields(self):
        for raw, name, tile, row, col, rot in (
            (LINE_B, "NetzB", "3", "0", "0", "0"),
            (LINE_A, "NetzA", "4", "2", "0", "90"),
        ):
            mm = agl.ROUND_PREFIX.match(raw)
            self.assertIsNotNone(mm, raw)
            cat, m = agl.classify(mm.group(2))
            self.assertEqual(cat, "START_TILE", raw)
            self.assertEqual(m.group("name"), name)
            self.assertEqual(m.group("tile"), tile)
            self.assertEqual(m.group("row"), row)
            self.assertEqual(m.group("col"), col)
            self.assertEqual(m.group("rot"), rot)

    def test_start_tile_is_a_primary_action_line(self):
        self.assertIn("START_TILE", agl.PRIMARY_CATEGORIES)


class _ApplySpy:
    """Minimal-Doppel des `Replayer`: merkt sich die `apply`-Aufrufe und
    schiebt den Zeilenzeiger um eine Zeile weiter (wie die echte Methode es
    fuer einen Ein-Zeilen-Block tut). `oracle_records` bleibt leer -- der
    Orakel-Zweig in `_run_loop` ist bei `do_oracle=False` unerreichbar."""

    def __init__(self):
        self.calls = []
        self.oracle_records = []

    def apply(self, lines, li, method, *args, **kwargs):
        self.calls.append((method, args))
        return li + 1


class StartTileDispatchTest(unittest.TestCase):
    def test_run_loop_applies_the_logged_placement_for_both_players(self):
        lines = []
        for raw in (LINE_B, LINE_A):
            mm = agl.ROUND_PREFIX.match(raw)
            lines.append(agl.LogLine(int(mm.group(1)), raw, mm.group(2)))
        rep = _ApplySpy()
        agl._run_loop(rep, lines, {"NetzA": 0, "NetzB": 1}, len(lines),
                      do_oracle=False, t_start=0.0)
        self.assertEqual(
            rep.calls,
            [
                # (Spielerindex, Platte, Slot-Zeile, Slot-Spalte, Rotation)
                ("apply_start_tile", (1, 3, 0, 0, 0)),
                ("apply_start_tile", (0, 4, 2, 0, 90)),
            ],
        )

    def test_searched_slot_is_not_replaced_by_the_hand_rule_corner(self):
        # Gezaehlt im Artefakt (380 Startsetzungen): 194x (0,0) rot=0, die
        # uebrigen fast alle (2,0) mit wechselnder Rotation -- die gesuchte
        # Setzung unterscheidet sich also sichtbar von der Handregel-Ecke und
        # darf beim Replay nicht auf sie zurueckfallen.
        mm = agl.ROUND_PREFIX.match(LINE_A)
        lines = [agl.LogLine(int(mm.group(1)), LINE_A, mm.group(2))]
        rep = _ApplySpy()
        agl._run_loop(rep, lines, {"NetzA": 0, "NetzB": 1}, 1,
                      do_oracle=False, t_start=0.0)
        _method, args = rep.calls[0]
        self.assertEqual(args[2:], (2, 0, 90))


if __name__ == "__main__":
    unittest.main()
