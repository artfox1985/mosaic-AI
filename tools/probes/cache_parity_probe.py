# -*- coding: utf-8 -*-
"""Bit-Identitaet zweier Trainings-Caches (PREREG_cache_build_time.md par.4).

DAS TOR fuer alle vier Hebel jener Prereg: Parallelisierung, Rust-Export,
lzf-Abschaltung, Datei-Cache. Keiner von ihnen darf den Cache-INHALT aendern
-- ein schnellerer, aber anderer Cache entwertet jeden Vergleich mit
bestehenden Modellen und jede Messung, die auf ihnen aufbaut.

Bewusst VOR dem ersten Umbau geschrieben, damit die Abnahme nicht nachtraeglich
auf das Ergebnis zugeschnitten wird.

Verglichen wird FELD FUER FELD und BITGENAU, nicht mit Toleranz: die Felder
sind uint8-gepackt, int8 oder float16, Gleichheit ist exakt pruefbar. Eine
Toleranz waere hier kein Entgegenkommen, sondern das Aufgeben des Kriteriums.

Aufruf:
    python -X utf8 tools/probes/cache_parity_probe.py <cache_a.h5> <cache_b.h5>

Die beiden Caches findet man als `.cache_<hash>.h5` im jeweiligen
MOSAIC_DATA_DIR. Fuer einen Hebel-Test also: einmal mit Bestandscode bauen,
Datei wegsichern, umbauen, neu bauen, beide vergleichen.
"""
import json
import pathlib
import sys
import time

import h5py
import numpy as np


def felder(pfad):
    with h5py.File(pfad, "r") as hf:
        return {k: np.array(hf[k]) for k in hf.keys()}


def vergleiche(pfad_a, pfad_b):
    a, b = felder(pfad_a), felder(pfad_b)
    nur_a, nur_b = sorted(set(a) - set(b)), sorted(set(b) - set(a))
    gemeinsam = sorted(set(a) & set(b))

    befunde = []
    for k in gemeinsam:
        x, y = a[k], b[k]
        if x.shape != y.shape:
            befunde.append((k, f"SHAPE {x.shape} gegen {y.shape}"))
            continue
        if x.dtype != y.dtype:
            befunde.append((k, f"DTYPE {x.dtype} gegen {y.dtype}"))
            continue
        # Bitgenau: np.array_equal ist fuer float16 exakt (kein isclose!).
        if not np.array_equal(x, y):
            n_diff = int((x != y).sum())
            # Erste abweichende Stelle nennen -- ohne sie ist ein Befund nicht
            # nachverfolgbar, und "irgendwo anders" hilft beim Suchen nicht.
            idx = np.argwhere(x != y)
            erste = tuple(int(v) for v in idx[0]) if len(idx) else None
            befunde.append((k, f"{n_diff} von {x.size} Werten abweichend, "
                               f"erste Stelle {erste}: {x[erste]!r} gegen {y[erste]!r}"))
    return a, b, nur_a, nur_b, gemeinsam, befunde


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Aufruf: python -X utf8 tools/probes/cache_parity_probe.py <a.h5> <b.h5>")
    t0 = time.time()
    pa, pb = sys.argv[1], sys.argv[2]
    a, b, nur_a, nur_b, gemeinsam, befunde = vergleiche(pa, pb)

    print(f"A: {pa}")
    print(f"B: {pb}")
    print(f"Felder: {len(a)} / {len(b)}, gemeinsam {len(gemeinsam)}")
    if nur_a:
        print(f"  NUR in A: {nur_a}")
    if nur_b:
        print(f"  NUR in B: {nur_b}")

    if not befunde and not nur_a and not nur_b:
        print("\n>>> BIT-IDENTISCH. Tor bestanden.")
        status = "bit-identisch"
    else:
        print(f"\n>>> ABWEICHUNGEN in {len(befunde)} Feld(ern) -- Tor NICHT bestanden:")
        for k, txt in befunde:
            print(f"    {k:22s} {txt}")
        status = "abweichend"

    wand = time.time() - t0
    erg = {
        "prereg": "PREREG_cache_build_time.md par.4",
        "cache_a": pa, "cache_b": pb,
        "status": status,
        "felder_a": len(a), "felder_b": len(b),
        "nur_in_a": nur_a, "nur_in_b": nur_b,
        "abweichungen": [{"feld": k, "befund": t} for k, t in befunde],
        "laufzeit": {"wanduhr_s": round(wand, 1), "cpu_s": round(time.process_time(), 1),
                     "threads": 1, "s_je_partie": None},
    }
    ziel = pathlib.Path("evaluations/artifacts/cache_parity.json")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(5):
        try:
            ziel.write_text(json.dumps(erg, indent=2, ensure_ascii=False),
                            encoding="utf-8", newline="\n")
            print(f"\nArtefakt: {ziel}  (Laufzeit {wand:.1f}s)")
            break
        except OSError as e:
            print("Retry:", e, flush=True)
            time.sleep(1)
    # Exit-Code traegt das Verdikt, damit der Aufrufer nicht parsen muss.
    sys.exit(0 if status == "bit-identisch" else 1)
