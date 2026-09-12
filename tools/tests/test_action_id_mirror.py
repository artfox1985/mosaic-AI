# -*- coding: utf-8 -*-
"""Waechter gegen stille Aktions-ID-Kollisionen: Python-Spiegel gegen Rust.

Anlass 2026-09-12: `features.rs::action_to_id` hatte keinen Zweig fuer den
Aktionstyp "dome" (Startsetzung der Kuppelplatte, Record `type: dome,
is_start: true`). Der Rueckfall `_ => 405` legte alle bis zu 108
Startkandidaten auf die ID des verdeckten Ziehens (`dome_stack_peek`). Das
blieb wochenlang unbemerkt, weil `corpus_dataset.py` Start-Records mit
Policy-Gewicht 0 fuehrt -- und es ist ein SYMMETRISCHER Defekt: beide Seiten
jeder Arena lesen dieselbe Tabelle, er kuerzt sich in jeder Messung weg
(CLAUDE.md, Abschnitt "Symmetrische Defekte sieht keine Arena").

Dieser Test haelt beide Tabellen gegeneinander, ohne die Engine zu bauen:
die Rust-Seite wird aus dem QUELLTEXT geparst (Zweig-Strings und
`KNOWN_ACTION_TYPES`), die Python-Seite wird ausgefuehrt. Was er NICHT kann:
die Rust-ID-FORMELN ausrechnen -- dafuer steht auf der Rust-Seite
`features.rs::action_to_id_branches_cover_exactly_the_engine_action_types`.
Die erwarteten IDs unten sind deshalb als Literale gepinnt; verschiebt eine
Seite eine Familie, faellt es hier auf.
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FEATURES_RS = REPO / "engine" / "src" / "features.rs"
sys.path.insert(0, str(REPO / "engine" / "py"))
sys.path.insert(0, str(REPO))

try:
    import neural_net  # noqa: E402
    IMPORT_ERROR = None
except Exception as e:  # torch/config fehlen z.B. in einem Teil-Checkout
    neural_net = None
    IMPORT_ERROR = f"{type(e).__name__}: {e}"


# Je Aktionstyp EINE Beispielaktion plus die erwartete ID (Literal, siehe
# Modul-Doku). Die Beispiele tragen bewusst Werte ungleich 0, damit ein
# vertauschter Faktor (z.B. slot_row/slot_col) auffaellt.
EXAMPLES: list[tuple[dict, int]] = [
    ({"type": "pass"}, 0),
    ({"type": "end_tiling"}, 1),
    # 10 + c_id(blau=0)*48 + r_id(row 0 -> 1)*6 + factory_index 2
    ({"type": "stone", "color": "blau", "row": 0, "factory_index": 2}, 18),
    # 274 + pattern_row 2*9 + slot_row 1*3 + slot_col 2
    ({"type": "tiling", "pattern_row": 2, "slot_row": 1, "slot_col": 2}, 297),
    # 328 + display_index 1*9 + slot_row 2*3 + slot_col 0 (Startsetzung)
    ({"type": "dome", "display_index": 1, "slot_row": 2, "slot_col": 0,
      "rotation": 90, "is_start": True}, 343),
    ({"type": "choose_dome_slot", "display_index": 1, "slot_row": 2, "slot_col": 0}, 343),
    # 355 + pending_index 3*9 + slot_row 0*3 + slot_col 1
    ({"type": "choose_draw_stack_slot", "pending_index": 3, "slot_row": 0, "slot_col": 1}, 383),
    ({"type": "choose_dome_rotation", "rotation": 180}, 393),
    ({"type": "use_chips", "pattern_row": 4}, 399),
    ({"type": "bonus_chip", "factory_index": 3}, 404),
    ({"type": "dome_stack_peek"}, 405),
]


def rust_branch_types() -> set[str]:
    """Die Typ-Strings der `match`-Zweige in `features.rs::action_to_id`.

    Geparst statt importiert: der Test darf kein gebautes Wheel voraussetzen
    (und ein installiertes Wheel koennte aelter sein als der Quellstand --
    genau die plausible Zweitquelle, gegen die REGEL 0 gebaut ist).
    """
    text = FEATURES_RS.read_text(encoding="utf-8")
    start = text.index("pub fn action_to_id(")
    end = text.index("unknown_action_type_id(other)", start)
    body = text[start:end]
    # Arm-Kopf: "typ" => ... bzw. "typ" | "typ2" => ...
    return set(re.findall(r'"([a-z_]+)"\s*(?:=>|\|)', body))


def rust_known_action_types() -> list[str]:
    """Inhalt der Konstante `KNOWN_ACTION_TYPES` aus features.rs."""
    text = FEATURES_RS.read_text(encoding="utf-8")
    m = re.search(r"pub const KNOWN_ACTION_TYPES: \[&str; \d+\] = \[(.*?)\];", text, re.S)
    assert m is not None, "KNOWN_ACTION_TYPES nicht in features.rs gefunden"
    return re.findall(r'"([a-z_]+)"', m.group(1))


@unittest.skipIf(neural_net is None, f"neural_net nicht importierbar ({IMPORT_ERROR})")
class ActionIdMirror(unittest.TestCase):
    def test_python_table_matches_rust_known_types(self):
        self.assertEqual(
            list(neural_net.KNOWN_ACTION_TYPES),
            rust_known_action_types(),
            "KNOWN_ACTION_TYPES laeuft zwischen neural_net.py und features.rs auseinander",
        )

    def test_rust_branches_cover_exactly_the_known_types(self):
        self.assertEqual(
            rust_branch_types(),
            set(rust_known_action_types()),
            "die match-Zweige in features.rs::action_to_id und KNOWN_ACTION_TYPES "
            "stimmen nicht ueberein (ein Zweig ohne Eintrag oder umgekehrt)",
        )

    def test_every_known_type_has_an_example(self):
        self.assertEqual(
            {ex["type"] for ex, _ in EXAMPLES},
            set(neural_net.KNOWN_ACTION_TYPES),
            "jeder bekannte Aktionstyp braucht hier eine Beispielaktion",
        )

    def test_example_ids_match_pinned_values(self):
        for action, expected in EXAMPLES:
            with self.subTest(action_type=action["type"]):
                self.assertEqual(neural_net.action_to_id(action), expected)

    def test_start_placement_shares_ids_with_choose_dome_slot(self):
        """Der Vorfall selbst: "dome" und "choose_dome_slot" sind dieselbe
        Entscheidung und muessen dieselbe ID liefern -- fuer JEDE (Platte,
        Slot)-Kombination, und niemals 405."""
        for d in range(3):
            for r in range(3):
                for c in range(3):
                    a = {"type": "dome", "display_index": d, "slot_row": r,
                         "slot_col": c, "rotation": 90, "is_start": True}
                    b = {"type": "choose_dome_slot", "display_index": d,
                         "slot_row": r, "slot_col": c}
                    with self.subTest(d=d, r=r, c=c):
                        self.assertEqual(neural_net.action_to_id(a), neural_net.action_to_id(b))
                        self.assertNotEqual(neural_net.action_to_id(a), 405)

    def test_pending_index_stays_capped(self):
        """Ueber MAX_PENDING_STACK_TILES hinaus wird gedeckelt, nicht
        ueberlaufen (sonst liefe die ID in die Rotations-Familie)."""
        capped = neural_net.action_to_id(
            {"type": "choose_draw_stack_slot", "pending_index": 99, "slot_row": 2, "slot_col": 2}
        )
        self.assertEqual(capped, 355 + 3 * 9 + 2 * 3 + 2)
        self.assertLess(capped, 391)

    def test_unknown_type_raises_instead_of_colliding(self):
        with self.assertRaises(neural_net.UnknownActionTypeError):
            neural_net.action_to_id({"type": "voellig_unbekannter_typ"})
        # Auch der fehlende Schluessel ist ein Defekt, kein 405.
        with self.assertRaises(neural_net.UnknownActionTypeError):
            neural_net.action_to_id({})

    def test_unknown_sentinel_matches_rust(self):
        text = FEATURES_RS.read_text(encoding="utf-8")
        m = re.search(r"pub const UNKNOWN_ACTION_ID: usize = (\d+);", text)
        self.assertIsNotNone(m, "UNKNOWN_ACTION_ID nicht in features.rs gefunden")
        self.assertEqual(neural_net.UNKNOWN_ACTION_ID, int(m.group(1)))


if __name__ == "__main__":
    unittest.main()
