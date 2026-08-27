# -*- coding: utf-8 -*-
"""tools/runtime_block.py -- der `laufzeit`-Pflichtblock fuer Mess-Artefakte.

CLAUDE.md ("Laufzeiten messen, nicht schaetzen", Nutzer-Anweisung 2026-08-25)
verlangt in JEDEM Ergebnis-JSON eines Messlaufs:

    "laufzeit": {"wanduhr_s": ..., "cpu_s": ..., "threads": ..., "s_je_partie": ...}

Der Block stand bis 2026-08-27 rund zwanzigmal handgeschrieben im Baum, jedes
Mal mit leicht anderer Rundung und mal mit, mal ohne `threads`. Dieser Helfer
ist die eine Bauform; die bestehenden regelkonformen Werkzeuge bleiben
unangetastet (kein Umbau ohne Anlass), NEUE und bisher saeumige Werkzeuge
nehmen ihn.

`threads` gehoert laut CLAUDE.md dazu, weil dieselbe Zahl in zwei
Arena-Einstiegen Verschiedenes bedeutet (`run_heuristic_v1_vs_v2_arena`:
`0` = alle Kerne; `run_net_vs_heuristic_v2_arena`: `<= 1` = sequenziell).
Ohne sie ist `wanduhr_s` nicht vergleichbar.

Nutzung:

    import time
    from runtime_block import laufzeit_block   # konvention-ok: s.u.

    t0, c0 = time.monotonic(), time.process_time()
    ...
    ergebnis["laufzeit"] = laufzeit_block(t0, cpu_start=c0, threads=args.threads,
                                          n_games=n)

`cpu_start=None` (Default) schreibt `cpu_s: null` -- der ehrliche Wert fuer
Werkzeuge, deren Rechenlast in UNTERPROZESSEN liegt: `time.process_time()`
summiert zwar ueber alle Threads des eigenen Prozesses (in-process
PyO3-Rust-Threads zaehlen also mit), aber nicht ueber Kindprozesse; ein Wert
nahe null waere dort irrefuehrend statt informativ. Ebenso `n_games=None`
(-> `s_je_partie: null`) fuer Werkzeuge, die selbst keine Partien spielen
(Pooler, Auswerter).
"""
from __future__ import annotations

import time


def laufzeit_block(wall_start: float, *, cpu_start: float | None = None,  # konvention-ok: spiegelt den in CLAUDE.md festgelegten Artefakt-Feldnamen "laufzeit"
                   threads: int | None = None,
                   n_games: int | None = None) -> dict:
    """Baut den `laufzeit`-Block aus einem `time.monotonic()`-Startwert.

    `wall_start`   -- Rueckgabe von `time.monotonic()` VOR dem Messteil.
    `cpu_start`    -- Rueckgabe von `time.process_time()` zum selben Zeitpunkt,
                      oder None (siehe Modul-Docstring).
    `threads`      -- die Thread-Zahl, mit der gemessen wurde; None nur, wenn
                      der Begriff fuer das Werkzeug keinen Sinn hat.
    `n_games`      -- Partien des Laufs; None, wenn keine gespielt wurden.
    """
    wall = time.monotonic() - wall_start
    cpu = None if cpu_start is None else round(time.process_time() - cpu_start, 1)
    per_game = round(wall / n_games, 3) if n_games else None
    return {
        "wanduhr_s": round(wall, 1),
        "cpu_s": cpu,
        "threads": threads,
        "s_je_partie": per_game,
    }
