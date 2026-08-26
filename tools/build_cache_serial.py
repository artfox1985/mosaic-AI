# -*- coding: utf-8 -*-
"""Seriell gebauter Referenz-Cache (PREREG_cache_build_time.md par.4).

Gegenstueck zu `build_cache_parallel.py`: baut denselben Ausschnitt mit dem
UNVERAENDERTEN Bestandsweg und meldet Pfad und Wanduhr. Der so entstandene
Cache ist die Referenz, gegen die `cache_parity_probe.py` prueft.

Bewusst ein eigenes Skript statt eines Flags im parallelen: die Referenz soll
NICHTS von der neuen Bauform sehen, auch keinen gemeinsamen Codepfad.

Aufruf:
    python -X utf8 -u tools/build_cache_serial.py --data-dir data --limit 120 \
        --encoder 2d --out data/.ref_serial.h5
"""
import argparse
import glob
import json
import os
import pathlib
import shutil
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent
# BEIDE Pfade: `neural_net` liegt in engine/py, importiert aber `config`
# aus der Projektwurzel. train.py sieht das nicht, weil es selbst dort liegt.
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--encoder", default="flat", choices=["flat", "2d"])
    ap.add_argument("--value-target-variant", default="default")
    ap.add_argument("--conjunction-head", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    import neural_net

    dateien = sorted(glob.glob(os.path.join(a.data_dir, "*.pkl")))
    _excl = os.environ.get("MOSAIC_DATA_EXCLUDE")
    if _excl:
        import re
        dateien = [f for f in dateien if not re.search(_excl, os.path.basename(f))]
    if a.limit:
        dateien = dateien[:a.limit]
    print(f"📦 seriell: {len(dateien)} Dateien, encoder={a.encoder}")

    t0 = time.time()
    ds = neural_net.MosaicDataset(a.data_dir, files=dateien, encoder=a.encoder,
                                  value_target_variant=a.value_target_variant,
                                  conjunction_head=a.conjunction_head)
    wand = time.time() - t0
    print(f"⏱️  seriell fertig: {wand:.1f}s, {len(ds)} Zustaende")
    print(f"   Cache: {ds.cache_path_h5}")
    shutil.copy(ds.cache_path_h5, a.out)
    print(f"   Referenz kopiert nach {a.out}")

    erg = {"prereg": "PREREG_cache_build_time.md par.4 (Referenz)",
           "dateien": len(dateien), "zustaende": len(ds), "encoder": a.encoder,
           "quelle_cache": ds.cache_path_h5, "referenz": a.out,
           "laufzeit": {"wanduhr_s": round(wand, 1), "cpu_s": round(time.process_time(), 1),
                        "threads": 1, "s_je_partie": None}}
    ziel = pathlib.Path("evaluations/artifacts/cache_build_serial.json")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(erg, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"Artefakt: {ziel}")


if __name__ == "__main__":
    main()
