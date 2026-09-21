"""Waechter fuer Regel 5 des Konventions-Linters (stille Test-Skips).

Die Regel soll Tests finden, die bei fehlender Voraussetzung STILL zurueckkehren
und damit leer gruen bestehen. Sie hat das am 2026-09-20 nicht getan: ein Test in
`net_mcts.rs` lud ein Modell, das nicht mehr im Baum lag, ueber

    let Some(net) = load_v18_legacy_test_net() else { return };

und lief monatelang leer durch. Weder der Ausloeser (`let Some(` fehlte in der
Liste) noch das Rueckgabemuster (verlangte `return;` ALLEIN auf der Zeile)
trafen diese Form. Gefunden hat es eine Durchsicht, nicht der Waechter
(par.8f Beifang 1).

Dieser Test pinnt beide Haelften an genau diesem Fall -- ein Waechter, dessen
Anlassfall nicht getestet ist, ist eine Behauptung.

Bezeichner englisch (CLAUDE.md 2026-08-24), Inhaltssprache deutsch.
"""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from check_conventions import (  # noqa: E402
    SILENT_SKIP_RETURN,
    SILENT_SKIP_TRIGGER,
    TEST_MODULE_START,
)

ANLASSFALL = "        let Some(net) = load_v18_legacy_test_net() else { return };"


class TheOriginalCaseIsCaught(unittest.TestCase):
    """Beide Haelften muessen greifen -- eine allein meldet nichts."""

    def test_return_pattern_matches(self):
        self.assertTrue(SILENT_SKIP_RETURN.search(ANLASSFALL))

    def test_trigger_matches(self):
        self.assertTrue(SILENT_SKIP_TRIGGER.search(ANLASSFALL))


class ReturnForms(unittest.TestCase):
    def test_plain_return_on_its_own_line(self):
        self.assertTrue(SILENT_SKIP_RETURN.search("        return;"))

    def test_return_ok_unit(self):
        self.assertTrue(SILENT_SKIP_RETURN.search("        return Ok(());"))

    def test_let_else_form(self):
        self.assertTrue(SILENT_SKIP_RETURN.search("    let Ok(x) = f() else { return };"))

    def test_panic_instead_of_return_is_not_flagged(self):
        """Ein lautes Scheitern ist genau das gewuenschte Verhalten."""
        self.assertFalse(SILENT_SKIP_RETURN.search('    let Some(x) = f() else { panic!("fehlt") };'))

    def test_a_return_with_a_value_is_not_a_skip(self):
        self.assertFalse(SILENT_SKIP_RETURN.search("        return 42;"))


class Triggers(unittest.TestCase):
    def test_known_triggers(self):
        for line in (
            "    if !path.exists() {",
            "    if res.is_err() {",
            "    let Ok(net) = load() else { return };",
            "    let Some(net) = load() else { return };",
            "    // uebersprungen: kein Modell",
        ):
            with self.subTest(line=line):
                self.assertTrue(SILENT_SKIP_TRIGGER.search(line))

    def test_ordinary_line_is_no_trigger(self):
        self.assertFalse(SILENT_SKIP_TRIGGER.search("    let net = load_test_net();"))


class TestModuleDetection(unittest.TestCase):
    """Die Regel heisst 'Test-Skips' und darf nur im Testteil suchen.

    Vorher scannte sie die ganze Datei und bat den Leser, Nicht-Test-Treffer zu
    ignorieren -- eine Warnung, die man wegsehen soll, verdeckt die naechste echte.
    """

    def test_recognises_the_usual_openers(self):
        for line in ("#[cfg(test)]", "mod tests {", "    mod tests {", "pub mod tests {"):
            with self.subTest(line=line):
                self.assertTrue(TEST_MODULE_START.match(line))

    def test_does_not_trip_on_a_similar_name(self):
        """Wortgrenze: `mod testsuite` ist kein Testmodul dieser Bauart."""
        self.assertFalse(TEST_MODULE_START.match("mod testsuite {"))

    def test_does_not_trip_on_production_code(self):
        self.assertFalse(TEST_MODULE_START.match("fn apply_step() {"))
