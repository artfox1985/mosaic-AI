"""Waechter: Korpusdateien werden ueber `corpus_io` gelesen, nicht roh.

Anlass (Durchsicht 2026-09-21, par.8h Fund 1): 56 Lesestellen in 54 Werkzeugen
luden Korpus- und Eval-Set-Dateien mit rohem `pickle.load`. Seit
`dump_records(..., compress=True)` sind die Korpora unter `data/` gzip -- die
Endung bleibt `.pkl`, erkannt wird am Magic-Byte (`corpus_io.py`). Ein roher
`pickle.load` stirbt dort mit `UnpicklingError: invalid load key, '\\x1f'`.

**Was daran wirklich kaputt war, praezise:** die Dateien unter `data/` sind
gzip, die eingefrorenen Eval-Sets unter `evaluations/` sind es NICHT. Ein Teil
der Lesestellen war also live defekt, der andere nur zerbrechlich -- er haette
beim ersten komprimierten Eval-Set aufgehoert zu funktionieren. `load_records`
erkennt beide Formen und ist damit in beiden Faellen der richtige Weg.

**Die Fehlerpolitik war der eigentliche Schaden.** Zwei Sonden fingen die
Ausnahme ab und berichteten STILL ueber eine leere Grundmenge (in par.8h
Rang 2 behoben), eine baute einen eigenen Lader, der am AUSNAHMETYP statt am
Magic-Byte entschied, der Rest starb laut. Drei Politiken nebeneinander.

Dieser Test haelt den Zustand: keine neue rohe Lesestelle. Die Ausnahmen unten
sind namentlich begruendet -- eine Liste ohne Gruende waere eine Liste, die
wieder waechst.

Bezeichner englisch (CLAUDE.md 2026-08-24), Inhaltssprache deutsch.
"""

import ast
import pathlib
import re
import unittest

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_TOOLS = _ROOT / "tools"

# Werkzeuge, die bewusst roh lesen oder schreiben duerfen, je mit Grund.
ALLOWED = {
    "repack_corpus.py": "packt Korpusdateien selbst um und MUSS beide Formen roh anfassen",
    "corpus_io.py": "ist die Sammelstelle selbst",
}

_RAW_READ = re.compile(r"pickle\.loads?\s*\(")


def raw_read_sites() -> dict:
    """Je Datei die Zeilennummern mit rohem `pickle.load`/`loads` -- Kommentare
    und Doc-Kommentare zaehlen NICHT mit (dort steht die Begruendung)."""
    found = {}
    for path in sorted(_TOOLS.rglob("*.py")):
        if "tests" in path.parts or path.name in ALLOWED:
            continue
        text = path.read_text(encoding="utf-8")
        if not _RAW_READ.search(text):
            continue
        tree = ast.parse(text)
        lines = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if (isinstance(func, ast.Attribute) and func.attr in ("load", "loads")
                    and isinstance(func.value, ast.Name) and func.value.id == "pickle"):
                lines.append(node.lineno)
        if lines:
            found[str(path.relative_to(_ROOT))] = sorted(lines)
    return found


class NoToolReadsACorpusRaw(unittest.TestCase):
    def test_no_raw_pickle_load_outside_the_allowlist(self):
        sites = raw_read_sites()
        self.assertEqual(sites, {}, (
            "Rohe pickle.load-Lesestellen. Korpusdateien sind gzip "
            "(dump_records(..., compress=True)); `corpus_io.load_records` "
            "erkennt komprimiert UND unkomprimiert am Magic-Byte."
        ))

    def test_the_allowlist_entries_still_exist(self):
        """Eine Ausnahme fuer eine geloeschte Datei ist toter Text."""
        for name in ALLOWED:
            with self.subTest(name=name):
                self.assertTrue(list(_ROOT.rglob(name)), f"{name} liegt nicht mehr im Baum")

    def test_every_allowlist_entry_carries_a_reason(self):
        for name, reason in ALLOWED.items():
            with self.subTest(name=name):
                self.assertGreater(len(reason), 20)


class EveryImporterCanActuallyFindCorpusIo(unittest.TestCase):
    """Der Import nuetzt nichts, wenn die Wurzel nicht auf dem Pfad liegt.

    Genau diese Falle stand im Baum: `sys.path.insert(0, ".")` traegt nur,
    solange das Werkzeug aus der Projektwurzel gestartet wird.
    """

    _ANCHOR = re.compile(
        r"sys\.path\.insert\(\s*0,\s*(?:str\()?[^\n]*"
        r"(?:parents\[\d\]|parent\.parent|_?ROOT|_?REPO|_?BASE_DIR)"
    )

    def test_no_tool_relies_on_the_current_directory(self):
        guilty = [str(p.relative_to(_ROOT)) for p in sorted(_TOOLS.rglob("*.py"))
                  if "tests" not in p.parts
                  and 'sys.path.insert(0, ".")' in p.read_text(encoding="utf-8")]
        self.assertEqual(guilty, [], "sys.path.insert(0, \".\") haengt am Arbeitsverzeichnis")

    def test_every_corpus_io_importer_has_an_absolute_anchor(self):
        guilty = []
        for path in sorted(_TOOLS.rglob("*.py")):
            if "tests" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            if "from corpus_io import" not in text:
                continue
            if not self._ANCHOR.search(text):
                guilty.append(str(path.relative_to(_ROOT)))
        self.assertEqual(guilty, [])
