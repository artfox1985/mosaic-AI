"""Waechter fuer den EINEN exakten Binomialtest (Durchsicht 2026-09-21, par.8h Punkt 4).

Anlass: derselbe Test stand **18-mal in 17 Dateien**, unter vier Namen
(`mcnemar_exact_p` 10x, `sign_test_p` 5x, `binom_p` 2x, `binom_p_two_sided` 1x).
Der Fund nannte "15-mal unter zwei Namen"; nachgezaehlt am Code sind es 18
unter vier. An diesem Test haengen die Gating-Entscheide.

**Vor dem Zusammenlegen gemessen:** alle 18 Fassungen liefern auf 961
Eingabepaaren (0..30 x 0..30) bitgleiche Werte. **Danach gegengeprueft:** alle
**126** registrierten `report_mcnemar_p` in `evaluations/artifacts/` lassen
sich aus ihren `pair_a_sweeps_b`/`pair_b_sweeps_c` exakt reproduzieren. Die
Vereinheitlichung bewegt also keine einzige registrierte Zahl.

Die Klasse `RegisteredArtifactsStillReproduce` haelt das fest -- sie ist der
eigentliche Waechter: sie prueft nicht eine Formel gegen sich selbst, sondern
gegen gemessene Ergebnisse, die im Baum liegen.

Bezeichner englisch (CLAUDE.md 2026-08-24), Inhaltssprache deutsch.
"""

import json
import pathlib
import re
import sys
import unittest
from math import comb

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_TOOLS = _ROOT / "tools"
sys.path.insert(0, str(_TOOLS))

from stats_exact import (  # noqa: E402
    binom_p_two_sided,
    mcnemar_exact_p,
    sign_test_p,
)


def brute_force(k: int, n: int) -> float:
    """Unabhaengig nachgebaut, damit der Test nicht die Formel gegen sich
    selbst prueft: alle Ausgaenge aufzaehlen, die mindestens so extrem sind."""
    if n == 0:
        return 1.0
    total = 2 ** n
    observed = abs(k - n / 2)
    mass = sum(comb(n, i) for i in range(n + 1) if abs(i - n / 2) >= observed)
    return min(1.0, mass / total)


class TheFormulaIsCorrect(unittest.TestCase):
    def test_matches_a_brute_force_enumeration(self):
        for n in range(0, 21):
            for k in range(0, n + 1):
                with self.subTest(k=k, n=n):
                    self.assertAlmostEqual(binom_p_two_sided(k, n), brute_force(k, n), places=12)

    def test_no_observation_cannot_be_rejected(self):
        self.assertEqual(binom_p_two_sided(0, 0), 1.0)

    def test_a_perfect_split_is_the_least_surprising(self):
        self.assertEqual(binom_p_two_sided(50, 100), 1.0)

    def test_it_is_symmetric(self):
        for n in (7, 20, 101):
            for k in range(n + 1):
                with self.subTest(k=k, n=n):
                    self.assertAlmostEqual(binom_p_two_sided(k, n),
                                           binom_p_two_sided(n - k, n), places=12)

    def test_it_never_exceeds_one(self):
        for n in range(0, 40):
            for k in range(n + 1):
                self.assertLessEqual(binom_p_two_sided(k, n), 1.0)


class TheThreeNamesAreTheSameTest(unittest.TestCase):
    """Die Namen sagen, was der Aufrufer MEINT -- gerechnet wird dasselbe."""

    def test_mcnemar_is_the_binomial_over_discordant_pairs(self):
        for b in range(0, 25):
            for c in range(0, 25):
                with self.subTest(b=b, c=c):
                    self.assertEqual(mcnemar_exact_p(b, c), binom_p_two_sided(b, b + c))

    def test_sign_test_is_the_same(self):
        for a in range(0, 25):
            for b in range(0, 25):
                with self.subTest(a=a, b=b):
                    self.assertEqual(sign_test_p(a, b), mcnemar_exact_p(a, b))


class NoToolKeepsItsOwnCopy(unittest.TestCase):
    _LOCAL_DEF = re.compile(
        r"^def (mcnemar_exact_p|sign_test_p|binom_p|binom_p_two_sided)\(", re.M)

    def test_the_definition_lives_in_exactly_one_place(self):
        guilty = [str(p.relative_to(_ROOT)) for p in sorted(_TOOLS.rglob("*.py"))
                  if p.name != "stats_exact.py" and "tests" not in p.parts
                  and self._LOCAL_DEF.search(p.read_text(encoding="utf-8"))]
        self.assertEqual(guilty, [], (
            "Eigene Kopie des exakten Binomialtests. Sie stand 18-mal im Baum; "
            "an diesem Test haengen die Gating-Entscheide."
        ))


class RegisteredArtifactsStillReproduce(unittest.TestCase):
    """Der wichtigste Test: gegen GEMESSENE Ergebnisse, nicht gegen die Formel.

    Jedes Gating-Artefakt traegt seine diskordanten Paare (`pair_a_sweeps_b`,
    `pair_b_sweeps_c`) NEBEN dem berechneten `report_mcnemar_p`. Weicht die
    Funktion ab, faellt das hier auf -- und zwar an echten Laeufen.
    """

    def test_every_recorded_mcnemar_p_is_reproduced(self):
        mismatches, checked = [], 0
        for path in sorted((_ROOT / "evaluations" / "artifacts").rglob("*.json")):
            # Vorfilter ueber die ROHBYTES: die Artefakte belegen zusammen rund
            # 1,3 GB, und jedes davon bei jedem Commit durch `json.loads` zu
            # schicken kostet 11,6 s. Der Substring-Test bringt das auf 3,9 s
            # und traegt dieselben 126 Treffer.
            try:
                raw = path.read_bytes()
            except OSError:
                continue
            if b'"pair_a_sweeps_b"' not in raw:
                continue
            try:
                data = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                continue
            if not isinstance(data, dict):
                continue
            b = data.get("pair_a_sweeps_b")
            c = data.get("pair_b_sweeps_c")
            recorded = data.get("report_mcnemar_p")
            if b is None or c is None or recorded is None:
                continue
            checked += 1
            if abs(mcnemar_exact_p(b, c) - recorded) > 1e-12:
                mismatches.append(f"{path.name}: b={b} c={c} registriert={recorded}")
        self.assertEqual(mismatches, [])
        self.assertGreater(checked, 100, "zu wenige Artefakte geprueft -- ist der Pfad noch richtig?")
