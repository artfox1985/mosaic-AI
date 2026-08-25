#!/usr/bin/env python
"""PREREG_heuristic_v2_long_rows.md par.13: Latin-Hypercube ueber STAERKE und
POSITION des Phasenfaktors.

par.11 hat EINE Form getestet (Gipfel 1,4 auf den Runden 2-3) und H0 geliefert.
Offen blieb, ob eine ANDERE Lage des Gipfels etwas bewegt -- das ist eine
andere Frage als "derselbe Faktor, anderer Wert", und deshalb ein eigener Arm.

Zwei Dimensionen, beide ueber Laufzeit-Knoepfe (`MOSAIC_PHASE_AMP`,
`MOSAIC_PHASE_PEAK`, Diagnose, Default aus):

    f(r) = 1 + (amp - 1) * exp(-(r - peak)^2 / (2 * sigma^2)),  sigma = 1,0 fest

* `amp` in [1,0; 2,5] -- Gipfelhoehe. **1,0 ist ein eingebauter NULLPUNKT**:
  die Kurve ist konstant 1 und der Arm identisch zur Huelle. Punkte nahe 1,0
  liefern damit den Rauschboden, gegen den alle uebrigen zu lesen sind.
* `peak` in [1,0; 5,0] -- Gipfel-Runde.

**Diese Stufe ENTSCHEIDET NICHTS** (par.13.1). Bei 16 Punkten ist das Maximum
einer t-Statistik auch unter reiner Nullhypothese deutlich von Null entfernt;
den besten Punkt hier abzulesen und als Befund zu melden waere genau der
Fehler, gegen den die Vorregistrierungs-Regeln geschrieben sind. Die
Bestaetigung laeuft auf FRISCHEN Seeds und ist par.13.2.

Jeder Punkt ist ein eigener PROZESS, weil die Knoepfe per `OnceLock` einmal je
Prozess gelesen werden.
"""
from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools" / "probes" / "v2_envelope_arena.py"
OUT_JSON = ROOT / "evaluations" / "phase_sweep.json"

N_PUNKTE = 16
AMP_BEREICH = (1.0, 2.5)
PEAK_BEREICH = (1.0, 5.0)
LHS_SEED = 20260825  # fest, damit der Entwurf reproduzierbar ist


def latin_hypercube(n: int, seed: int) -> list[tuple[float, float]]:
    """Klassisches LHS: je Dimension n gleich grosse Schichten, in jeder genau
    EIN Zug, danach die Dimensionen unabhaengig gemischt."""
    rng = random.Random(seed)
    spalten = []
    for lo, hi in (AMP_BEREICH, PEAK_BEREICH):
        werte = [lo + (hi - lo) * (i + rng.random()) / n for i in range(n)]
        rng.shuffle(werte)
        spalten.append(werte)
    return list(zip(spalten[0], spalten[1]))


def fahre_punkt(i: int, amp: float, peak: float) -> dict:
    umgebung = dict(os.environ)
    umgebung["MOSAIC_PHASE_AMP"] = f"{amp:.4f}"
    umgebung["MOSAIC_PHASE_PEAK"] = f"{peak:.4f}"
    umgebung["PYTHONIOENCODING"] = "utf-8"
    tag = f"sweep{i:02d}"
    # encoding explizit: `text=True` dekodiert unter Windows sonst cp1252 und
    # der Reader-Thread stirbt an den Umlauten der Sonde.
    subprocess.run(
        [sys.executable, "-u", str(PROBE), "--arms", "v2huelle:v2huellephase", "--tag", tag],
        env=umgebung, cwd=str(ROOT), check=True,
        capture_output=True, text=True, encoding="utf-8",
    )
    d = json.loads((ROOT / "evaluations" / f"v2_envelope_arena_{tag}.json").read_text(encoding="utf-8"))
    k = d["kennzahlen"]
    return {
        "i": i, "amp": round(amp, 4), "peak": round(peak, 4),
        "delta_volle_spalten": k["volle_spalten"]["delta"],
        "t_volle_spalten": k["volle_spalten"]["t_block"],
        "delta_punkte": k["punkte"]["delta"],
        "t_punkte": k["punkte"]["t_block"],
        "siegquote": d["siegquote_huelle"],
        "vollendungsquote": d["vollendungsquote"]["v2huellephase"],
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    entwurf = latin_hypercube(N_PUNKTE, LHS_SEED)
    t0, c0 = time.monotonic(), time.process_time()
    print(f"[sweep] {N_PUNKTE} Punkte, je 160 gepaarte Partien", flush=True)

    zeilen = []
    for i, (amp, peak) in enumerate(entwurf):
        r = fahre_punkt(i, amp, peak)
        zeilen.append(r)
        print(f"  [{i + 1:2d}/{N_PUNKTE}] amp={amp:.2f} peak={peak:.2f} | "
              f"Spalten {r['delta_volle_spalten']:+.3f} (t {r['t_volle_spalten']:+.2f}) | "
              f"Punkte {r['delta_punkte']:+.2f} | Sieg {r['siegquote']:.3f}", flush=True)

    wanduhr = time.monotonic() - t0
    ergebnis = {
        "prereg": "PREREG_heuristic_v2_long_rows.md par.13.1 (SCREENING, entscheidet nichts)",
        "n_punkte": N_PUNKTE, "amp_bereich": AMP_BEREICH, "peak_bereich": PEAK_BEREICH,
        "lhs_seed": LHS_SEED, "partien_je_punkt": 160,
        "laufzeit": {"wanduhr_s": round(wanduhr, 1),
                     "cpu_s": round(time.process_time() - c0, 1),
                     "threads": 0,
                     "s_je_punkt": round(wanduhr / N_PUNKTE, 1)},
        "punkte": zeilen,
    }
    OUT_JSON.write_text(json.dumps(ergebnis, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\nNach Entscheidungsmass sortiert (volle Spalten), OHNE Auswahl-Befugnis:")
    print(f"{'amp':>6}{'peak':>7}{'d_Spalten':>11}{'t':>7}{'d_Punkte':>10}{'Sieg':>7}")
    for r in sorted(zeilen, key=lambda x: -x["delta_volle_spalten"]):
        print(f"{r['amp']:>6.2f}{r['peak']:>7.2f}{r['delta_volle_spalten']:>11.3f}"
              f"{r['t_volle_spalten']:>7.2f}{r['delta_punkte']:>10.2f}{r['siegquote']:>7.3f}")

    nullpunkte = [r for r in zeilen if r["amp"] < 1.1]
    if nullpunkte:
        spanne = max(abs(r["delta_volle_spalten"]) for r in nullpunkte)
        print(f"\nRauschboden aus {len(nullpunkte)} Quasi-Nullpunkten (amp < 1,1): "
              f"|delta| bis {spanne:.3f}")
    print(f"\nLaufzeit {wanduhr:.0f} s -> {OUT_JSON}")
    print("SCREENING. Der beste Punkt ist ein KANDIDAT, kein Befund -- "
          "Bestaetigung auf frischen Seeds ist par.13.2.")


if __name__ == "__main__":
    main()
