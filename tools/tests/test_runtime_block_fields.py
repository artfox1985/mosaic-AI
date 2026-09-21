"""Waechter: jeder `laufzeit`-Block traegt seine vier Pflichtfelder.

CLAUDE.md ("Laufzeiten messen, nicht schaetzen", Nutzer-Anweisung 2026-08-25)
verlangt in JEDEM Ergebnis-JSON eines Messlaufs:

    "laufzeit": {"wanduhr_s": ..., "cpu_s": ..., "threads": ..., "s_je_partie": ...}

`threads` gehoert dazu, weil dieselbe Zahl in zwei Arena-Einstiegen
Verschiedenes bedeutet (`0` = alle Kerne gegen `<= 1` = sequenziell). Ohne sie
ist `wanduhr_s` nicht vergleichbar.

ANLASS (Durchsicht 2026-09-21, par.8h Punkt 2): 13 Bloecke liessen Pflichtfelder
WEG -- drei davon `cpu_s` und `threads` zugleich. Der Fund sprach von "72
handgeschriebenen Bloecken"; das allein ist aber kein Defekt, sondern eine
registrierte Entscheidung: `tools/runtime_block.py` sagt seit 2026-08-27
ausdruecklich, bestehende REGELKONFORME Werkzeuge bleiben unangetastet, nur
saeumige nehmen den Helfer. Dieser Test prueft darum, was die Regel wirklich
verlangt -- die FELDER --, nicht die Bauform.

**Warum `s_je_*` mit Stern:** Werkzeuge, deren Laufeinheit keine Partie ist,
schreiben `s_je_record`, `s_je_zustand`, `s_je_fall`, `s_je_label`. Das ist
richtiger als ein `s_je_partie`, das luegen wuerde, und seit 2026-09-21 kann
der Helfer es ueber `n_units=...`/`unit=...` selbst.

Bezeichner englisch (CLAUDE.md 2026-08-24), Inhaltssprache deutsch.
"""

import pathlib
import re
import unittest

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_TOOLS = _ROOT / "tools"

# Ein Block-Literal: `"laufzeit": {...}` oder `[...]["laufzeit"] = {...}`.
_BLOCK = re.compile(
    r'"laufzeit"\s*:\s*\{(?P<a>[^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
    r'|\["laufzeit"\]\s*=\s*\{(?P<b>[^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
)
_PER_UNIT = re.compile(r'"s_je_\w+"')


def handwritten_blocks():
    """Je Fundstelle (Datei, Zeile, fehlende Felder). Werkzeuge, die den Helfer
    benutzen, kommen nicht vor -- der Helfer setzt alle vier Schluessel."""
    out = []
    for path in sorted(_TOOLS.rglob("*.py")):
        if "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if "laufzeit_block" in text:
            continue
        for match in _BLOCK.finditer(text):
            body = match.group("a") or match.group("b") or ""
            missing = [name for name, present in (
                ("wanduhr_s", "wanduhr_s" in body),
                ("cpu_s", "cpu_s" in body),
                ("threads", "threads" in body),
                ("s_je_*", bool(_PER_UNIT.search(body))),
            ) if not present]
            if missing:
                out.append((str(path.relative_to(_ROOT)),
                            text[:match.start()].count("\n") + 1, missing))
    return out


class EveryRuntimeBlockIsComplete(unittest.TestCase):
    def test_no_block_omits_a_mandatory_field(self):
        incomplete = handwritten_blocks()
        self.assertEqual(incomplete, [], (
            "laufzeit-Bloecke ohne Pflichtfeld. Nicht zutreffende Felder "
            "gehoeren als null hinein, nicht weggelassen -- `tools/runtime_block.py` "
            "macht das von selbst."
        ))

    def test_the_detector_would_actually_notice(self):
        """Ein Waechter, der nichts findet, weil er nichts sucht, ist keiner."""
        self.assertTrue(list(_TOOLS.rglob("*.py")))
        probe = '"laufzeit": {"wanduhr_s": 1.0}'
        match = _BLOCK.search(probe)
        self.assertIsNotNone(match)
        self.assertNotIn("cpu_s", match.group("a"))


class NobodyMixesTheTwoClocks(unittest.TestCase):
    """`t0 = time.monotonic()` und spaeter `time.time() - t0` ergibt die
    Epochenzeit minus der Laufzeit des Rechners -- eine Zahl in
    Milliardenhoehe, die in einem Fortschrittsdruck nicht auffaellt.

    Beim Umbau am 2026-09-21 ist genau das viermal passiert, weil die
    Ersetzung Leerzeichen um den Minus verlangte und die Druckzeilen
    `time.time()-t0` ohne schreiben.
    """

    def test_no_tool_subtracts_a_monotonic_start_from_wall_clock(self):
        guilty = []
        for path in sorted(_TOOLS.rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            for var in re.findall(r"^\s*(\w+)(?:,\s*\w+)? = time\.monotonic\(\)", text, re.M):
                if re.search(rf"time\.time\(\)\s*-\s*{var}\b", text):
                    guilty.append(f"{path.relative_to(_ROOT)}: {var}")
        self.assertEqual(guilty, [])


class TheHelperCanNameItsUnit(unittest.TestCase):
    """Die Erweiterung von 2026-09-21: drei Sonden hatten den Block von Hand
    gebaut, WEIL `s_je_partie` fuer sie gelogen haette."""

    def test_unit_parameter_renames_the_per_unit_field(self):
        import sys
        sys.path.insert(0, str(_TOOLS))
        import time

        from runtime_block import laufzeit_block
        start = time.monotonic()
        self.assertIn("s_je_record",
                      laufzeit_block(start, cpu_start=0.0, threads=1,
                                     n_units=10, unit="record"))
        self.assertIn("s_je_partie",
                      laufzeit_block(start, cpu_start=0.0, threads=1, n_games=10))

    def test_all_four_keys_are_present_even_when_nothing_applies(self):
        import sys
        sys.path.insert(0, str(_TOOLS))
        import time

        from runtime_block import laufzeit_block
        block = laufzeit_block(time.monotonic())
        self.assertEqual(sorted(block), ["cpu_s", "s_je_partie", "threads", "wanduhr_s"])
        self.assertIsNone(block["cpu_s"])
