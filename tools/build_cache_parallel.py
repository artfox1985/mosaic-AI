# -*- coding: utf-8 -*-
"""Parallel gebauter Trainings-Cache (PREREG_cache_build_time.md Hebel 1).

ANLASS, gemessen 2026-08-25: der Cache-Bau laeuft einkernig (~0,75 Kerne) und
brauchte 70 min fuer 890.000 Zustaende; der volle v22-Korpus laege bei rund 5 h.
Er liegt damit VOR jeder Trainingsfrage und hat am 2026-08-25 erzwungen, den
Traeger-A/B als Richtungstest auf einem Viertelkorpus zu fahren statt voll.

ZUSCHNITT -- bewusst OHNE Eingriff in die 500-Zeilen-Bauschleife:
`MosaicDataset` nimmt bereits eine explizite Dateiliste. Die Worker bauen je
eine zusammenhaengende TEILMENGE mit dem UNVERAENDERTEN Bestandscode und geben
nur ihren Cache-Pfad zurueck; der Elternprozess liest die Teil-Caches von der
Platte und fuegt sie zusammen. Arrays durch die Prozess-Pipe zu schicken waere
beim vollen Korpus ueber 11 GB.

WARUM DIE REIHENFOLGE STIMMT: die Dateien werden sortiert und in
ZUSAMMENHAENGENDE Bloecke geteilt; die Teil-Caches werden in Blockreihenfolge
konkateniert. Damit ist die Datensatz-Reihenfolge identisch zum seriellen Bau
-- Voraussetzung fuer die Bit-Identitaet, die das Tor verlangt.

NEBENEFFEKT MIT ABSICHT: die Teil-Caches bleiben liegen. Ein zweiter Lauf mit
derselben Blockteilung baut nur, was fehlt -- der Datei-Cache aus Hebel (4) in
grober Form, ohne dessen Schluesselteilung.

ABNAHME: `tools/probes/cache_parity_probe.py` gegen den seriell gebauten
Cache. Bit-Identitaet, nicht Toleranz.

Aufruf:
    python -X utf8 -u tools/build_cache_parallel.py --data-dir data --workers 6 \
        --out data/.cache_parallel.h5 [--encoder 2d] [--limit 200]
"""
import argparse
import json
import multiprocessing as mp
import os
import pathlib
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent
# BEIDE Pfade: `neural_net` liegt in engine/py, importiert aber `config`
# aus der Projektwurzel. train.py sieht das nicht, weil es selbst dort liegt.
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))

import h5py
import numpy as np


def _bau_teilmenge(args):
    """Laeuft im Worker: baut EINE Dateiteilmenge mit dem Bestandscode.

    Gibt nur den Cache-Pfad zurueck -- die Arrays bleiben auf der Platte.
    """
    data_dir, dateien, kwargs, idx = args
    import neural_net  # erst im Worker importieren (spawn-sicher)
    ds = neural_net.MosaicDataset(data_dir, files=list(dateien), **kwargs)
    return idx, ds.cache_path_h5, len(ds)


def zusammenfuegen(teile, ziel):
    """Konkateniert die Teil-Caches in Blockreihenfolge zu einem Cache.

    Feldweise und streamend: alle Teile eines Feldes werden gelesen,
    konkateniert und geschrieben, bevor das naechste Feld drankommt -- sonst
    laegen beim vollen Korpus alle Felder gleichzeitig im RAM.
    """
    with h5py.File(teile[0], "r") as hf:
        felder = sorted(hf.keys())
        attrs = {k: dict(hf[k].attrs) for k in felder}
    # Alle Teile muessen dieselben Felder haben -- sonst wurden sie mit
    # unterschiedlicher Konfiguration gebaut, und das Zusammenfuegen waere
    # stillschweigend falsch.
    for t in teile[1:]:
        with h5py.File(t, "r") as hf:
            if sorted(hf.keys()) != felder:
                raise SystemExit(
                    f"Teil-Caches haben verschiedene Felder:\n  {teile[0]}: {felder}\n"
                    f"  {t}: {sorted(hf.keys())}\nAbbruch -- das waere ein stiller Fehler.")
    with h5py.File(ziel, "w") as out:
        for k in felder:
            bloecke = []
            for t in teile:
                with h5py.File(t, "r") as hf:
                    bloecke.append(np.array(hf[k]))
            ganz = np.concatenate(bloecke, axis=0)
            out.create_dataset(k, data=ganz, compression="lzf")
            for a, v in attrs[k].items():
                out[k].attrs[a] = v
            del bloecke, ganz
    return felder


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--out", required=True, help="Zieldatei des zusammengefuegten Caches")
    ap.add_argument("--encoder", default="flat", choices=["flat", "2d"])
    ap.add_argument("--value-target-variant", default="default")
    ap.add_argument("--conjunction-head", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="nur die ersten N Dateien (Test)")
    a = ap.parse_args()

    import glob
    dateien = sorted(glob.glob(os.path.join(a.data_dir, "*.pkl")))
    _excl = os.environ.get("MOSAIC_DATA_EXCLUDE")
    if _excl:
        import re
        dateien = [f for f in dateien if not re.search(_excl, os.path.basename(f))]
    if a.limit:
        dateien = dateien[:a.limit]
    if not dateien:
        raise SystemExit(f"Keine .pkl-Dateien in {a.data_dir}")

    n_w = max(1, min(a.workers, len(dateien)))
    # ZUSAMMENHAENGENDE Bloecke, damit die Konkatenation die serielle
    # Reihenfolge reproduziert.
    grenzen = [round(i * len(dateien) / n_w) for i in range(n_w + 1)]
    bloecke = [dateien[grenzen[i]:grenzen[i + 1]] for i in range(n_w)]
    bloecke = [b for b in bloecke if b]

    kwargs = dict(encoder=a.encoder, value_target_variant=a.value_target_variant,
                  conjunction_head=a.conjunction_head)
    print(f"📦 {len(dateien)} Dateien auf {len(bloecke)} Bloecke, {a.workers} Worker angefordert")
    for i, b in enumerate(bloecke):
        print(f"   Block {i}: {len(b)} Dateien ({os.path.basename(b[0])} .. {os.path.basename(b[-1])})")

    t0 = time.time()
    with mp.Pool(len(bloecke)) as pool:
        ergebnisse = pool.map(_bau_teilmenge,
                              [(a.data_dir, b, kwargs, i) for i, b in enumerate(bloecke)])
    t_bau = time.time() - t0
    ergebnisse.sort()
    teile = [pfad for _, pfad, _ in ergebnisse]
    n_zustaende = sum(n for _, _, n in ergebnisse)
    print(f"\n⏱️  Teil-Bau: {t_bau:.1f}s, {n_zustaende} Zustaende")

    t1 = time.time()
    felder = zusammenfuegen(teile, a.out)
    t_merge = time.time() - t1
    wand = time.time() - t0
    print(f"⏱️  Zusammenfuegen: {t_merge:.1f}s ({len(felder)} Felder)")
    print(f"✅ {a.out}  --  gesamt {wand:.1f}s")

    erg = {
        "prereg": "PREREG_cache_build_time.md Hebel 1",
        "dateien": len(dateien), "bloecke": len(bloecke), "zustaende": n_zustaende,
        "ziel": a.out, "teil_caches": teile, "encoder": a.encoder,
        "laufzeit": {"wanduhr_s": round(wand, 1), "teilbau_s": round(t_bau, 1),
                     "zusammenfuegen_s": round(t_merge, 1),
                     "cpu_s": None, "threads": len(bloecke),
                     "s_je_partie": None},
    }
    ziel = pathlib.Path("evaluations/artifacts/cache_build_parallel.json")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(erg, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"Artefakt: {ziel}")


if __name__ == "__main__":
    main()
