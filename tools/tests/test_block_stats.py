"""Waechter fuer die EINE Blockmittel-Regel (Durchsicht 2026-09-21, par.8h Fund 3).

Anlass: dieselbe Zusammenfassung stand dreimal im Baum, mit drei verschiedenen
Regeln fuer den angebrochenen letzten Block -- `plate_points_from_arena` zaehlte
ihn ab halber Blockgroesse mit, `probes/env_ab_swap_eval` immer,
`probes/arena_block_sd_probe` nie. Daran haengt laut CLAUDE.md die
Entscheidungsmetrik JEDER Arena-Auswertung ("Arena-Block-Korrelation").

Gemessen war die Divergenz folgenlos -- `paired_gating` wertet je Block aus und
stoppt darum auf einer Blockgrenze; genau ein Artefakt im Baum hat einen Rest,
ein Rauchtest mit n = 2. Dieser Test haelt fest, dass es dabei bleibt: er pinnt
die Regel UND dass alle drei Aufrufer dieselbe benutzen.

Bezeichner englisch (CLAUDE.md 2026-08-24), Inhaltssprache deutsch.
"""

import pathlib
import sys
import unittest

_TOOLS = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_TOOLS))
sys.path.insert(0, str(_TOOLS / "probes"))

from block_stats import block_means, block_t  # noqa: E402


class BlockMeans(unittest.TestCase):
    def test_full_blocks_are_plain_means(self):
        self.assertEqual(block_means([1, 2, 3, 4, 5, 5, 5, 5, 5, 5], 5), [3.0, 5.0])

    def test_remainder_at_half_block_counts(self):
        """Schwelle ist `max(1, block // 2)` -- bei 5 also 2."""
        self.assertEqual(block_means([0, 0, 0, 0, 0, 4, 6], 5), [0.0, 5.0])

    def test_remainder_below_half_block_is_dropped(self):
        """Ein 1-Partie-Rest waere ein Datenpunkt mit der Streuung einer Einzelpartie."""
        self.assertEqual(block_means([0, 0, 0, 0, 0, 9], 5), [0.0])

    def test_block_one_keeps_every_value(self):
        self.assertEqual(block_means([1, 2, 3], 1), [1.0, 2.0, 3.0])

    def test_block_size_zero_is_refused(self):
        with self.assertRaises(ValueError):
            block_means([1, 2], 0)

    def test_empty_input_gives_no_blocks(self):
        self.assertEqual(block_means([], 5), [])


class BlockT(unittest.TestCase):
    def test_t_is_zero_below_two_blocks(self):
        """Kein auswertbarer Fall -- eine erkennbare 0 statt inf im Artefakt."""
        _, m, t = block_t([1, 2, 3], 5)
        self.assertEqual((m, t), (2.0, 0.0))

    def test_t_is_zero_without_spread(self):
        _, m, t = block_t([2] * 10, 5)
        self.assertEqual((m, t), (2.0, 0.0))

    def test_t_is_positive_for_a_positive_shift(self):
        _, m, t = block_t([1, 1, 1, 1, 1, 3, 3, 3, 3, 3], 5)
        self.assertEqual(m, 2.0)
        self.assertGreater(t, 0.0)


class AllThreeCallersShareTheRule(unittest.TestCase):
    """Der eigentliche Punkt: drei Aufrufer, eine Regel.

    Gemessen wird an der AUSGABE, nicht daran, ob der Import dasteht -- ein
    Waechter, der nur die Zeile prueft, faellt beim naechsten Umbau um.
    """

    WERTE = [0, 0, 0, 0, 0, 4, 6]   # Rest von 2 bei Blockgroesse 5: zaehlt mit

    def test_plate_points_from_arena(self):
        import plate_points_from_arena as a
        self.assertEqual(a.block_mean(self.WERTE, 5), block_means(self.WERTE, 5))

    def test_env_ab_swap_eval(self):
        import env_ab_swap_eval as b
        self.assertEqual(b.blocks(self.WERTE, 5), block_means(self.WERTE, 5))

    def test_arena_block_sd_probe(self):
        import arena_block_sd_probe as c
        self.assertEqual(c.block_sd(self.WERTE, 5)["bloecke"], len(block_means(self.WERTE, 5)))
