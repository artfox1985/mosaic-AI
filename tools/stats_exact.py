# -*- coding: utf-8 -*-
"""tools/stats_exact.py -- exakte Tests ohne scipy, EINE Bauform.

Das Repo hat bewusst keine scipy-Abhaengigkeit (Praezedenz
`PREREG_ownership_gumbel.md`); die exakten Tests sind darum von Hand gebaut.
Bis zum 2026-09-21 stand derselbe Test **18-mal in 17 Dateien**, unter VIER
Namen: `mcnemar_exact_p` (10x), `sign_test_p` (5x), `binom_p` (2x) und
`binom_p_two_sided` (1x).

**Gemessen, bevor zusammengelegt wurde** (par.8h Punkt 4): alle 18 Fassungen
liefern auf 961 Eingabepaaren (0..30 x 0..30) bitgleiche Werte. Die
Vereinheitlichung aendert also KEINE registrierte Zahl -- was sie beseitigt,
ist die Moeglichkeit, dass eine der 18 beim naechsten Anfassen auseinanderlaeuft.
An diesem Test haengen die Gating-Entscheide.

**Die drei Namen bleiben**, sie sind keine Redundanz, sondern sagen, was der
Aufrufer MEINT:

* `binom_p_two_sided(k, n)` -- k Erfolge aus n Versuchen gegen p = 0,5.
* `mcnemar_exact_p(b, c)`   -- gepaarte Arena: b Siege hier, c Siege dort,
                               Unentschieden zaehlen nicht mit.
* `sign_test_p(n_pos, n_neg)` -- Vorzeichentest ueber gepaarte Seeds.

Alle drei sind derselbe Test; die Umrechnung steht je in einer Zeile.

Nutzung aus `tools/`:        from stats_exact import mcnemar_exact_p
Nutzung aus `tools/probes/`: sys.path.insert(0, str(... parents[2] / "tools"))
"""
from __future__ import annotations

from math import comb


def binom_p_two_sided(k: int, n: int) -> float:
    """Exakter zweiseitiger Binomialtest gegen p = 0,5.

    Summiert beide Schwaenze ab dem jeweils extremeren Rand und verdoppelt den
    kleineren -- die uebliche Konstruktion, wenn die Verteilung symmetrisch
    ist. `n == 0` gibt 1,0: ohne Beobachtung gibt es nichts abzulehnen.
    """
    if n == 0:
        return 1.0
    lo, hi = min(k, n - k), max(k, n - k)
    p_le = sum(comb(n, i) for i in range(0, lo + 1)) / (2 ** n)
    p_ge = sum(comb(n, i) for i in range(hi, n + 1)) / (2 ** n)
    return min(1.0, 2 * min(p_le, p_ge))


def mcnemar_exact_p(b: int, c: int) -> float:
    """Exakter McNemar-Test ueber die DISKORDANTEN Paare einer gepaarten Arena.

    `b` und `c` sind die Paare, in denen genau eine Seite gewonnen hat;
    beidseitig gleiche Ausgaenge tragen keine Information und bleiben draussen.
    """
    return binom_p_two_sided(b, b + c)


def sign_test_p(n_pos: int, n_neg: int) -> float:
    """Exakter zweiseitiger Vorzeichentest (z.B. ueber gepaarte Seeds)."""
    return binom_p_two_sided(n_pos, n_pos + n_neg)
