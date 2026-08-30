# -*- coding: utf-8 -*-
"""Inventar der Datei-Cache-Bloecke: welcher Block gehoert zu welcher Datei?

Anlass (Nutzer 2026-08-30): "woher weiss ich welche caches zu welchen
dateien gehoeren? das ist fuer mich so nicht handelbar". Die Bloecke
heissen `.filecache_<inhaltsschluessel>.h5` -- der Quelldateiname steht
NUR in den HDF5-Attributen (`mosaic_files_first`/`_last`, gesetzt beim
Bau). Von aussen ist die Zuordnung damit unsichtbar, und geloeschte
Korpusdateien hinterlassen unauffindbare WAISEN.

Dieses Werkzeug liest die Attribute und beantwortet drei Fragen:
  * welcher Block gehoert zu welcher Quelldatei (--list),
  * welche Bloecke sind WAISEN, deren Quelldatei nicht mehr existiert
    (--orphans; Default-Ansicht ist eine Zusammenfassung),
  * wieviel Platz haengt daran.

Loeschen tut dieses Werkzeug NICHTS. Es druckt auf Wunsch die
Loeschliste (--print-delete-list), die Entscheidung bleibt beim Nutzer
(stehende Regel: kein rm ohne pfadgenaue Freigabe).

Aufruf:
    python -X utf8 tools/cache_inventory.py
    python -X utf8 tools/cache_inventory.py --list
    python -X utf8 tools/cache_inventory.py --orphans --print-delete-list
"""
from __future__ import annotations

import argparse
import glob
import os
import pathlib
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

_ROOT = pathlib.Path(__file__).resolve().parent.parent


def read_block(path: str) -> dict:
    """Quelldatei(en) und Schluessel eines Blocks; leer bei unlesbar."""
    import h5py
    try:
        with h5py.File(path, "r") as h:
            a = h.attrs
            first = a.get("mosaic_files_first")
            last = a.get("mosaic_files_last")
            n = int(a.get("mosaic_files_n", 0) or 0)
            key = a.get("mosaic_cache_key_full") or a.get("mosaic_cache_key")
            dec = lambda v: v.decode() if isinstance(v, bytes) else (str(v) if v is not None else None)  # noqa: E731
            return {"first": dec(first), "last": dec(last), "n": n, "key": dec(key)}
    except Exception as e:  # noqa: BLE001 -- unlesbar ist ein Befund, kein Absturz
        return {"fehler": repr(e)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default=str(_ROOT / "data"))
    ap.add_argument("--list", action="store_true",
                    help="jede Zuordnung Block -> Quelldatei ausgeben")
    ap.add_argument("--orphans", action="store_true",
                    help="nur die Waisen auflisten")
    ap.add_argument("--print-delete-list", action="store_true",
                    help="Loeschliste der Waisen ausgeben (loescht NICHTS)")
    a = ap.parse_args()

    data_dir = a.data_dir
    blocks = sorted(glob.glob(os.path.join(data_dir, ".filecache_*.h5")))
    korpus = {os.path.basename(p) for p in glob.glob(os.path.join(data_dir, "*.pkl"))}

    rows, orphans, broken = [], [], []
    total = orphan_bytes = 0
    for b in blocks:
        size = os.path.getsize(b)
        total += size
        info = read_block(b)
        if "fehler" in info:
            broken.append((b, info["fehler"]))
            continue
        src = info["first"]
        row = {"block": os.path.basename(b), "quelle": src,
               "n": info["n"], "mb": size / (1024 * 1024)}
        rows.append(row)
        if src and src not in korpus:
            orphans.append(row)
            orphan_bytes += size

    print(f"Cache-Bloecke: {len(blocks)} ({total / (1024 * 1024):,.0f} MB) in {data_dir}")
    print(f"Korpusdateien: {len(korpus)}")
    print(f"WAISEN (Quelldatei fehlt): {len(orphans)} ({orphan_bytes / (1024 * 1024):,.0f} MB)")
    if broken:
        print(f"UNLESBAR: {len(broken)} -- erste: {broken[0][0]}")

    # Waisen nach Praefix gruppieren: so sieht man auf einen Blick, welche
    # geloeschte Messreihe wieviel Platz haelt.
    if orphans:
        gruppen: dict[str, list] = {}
        for r in orphans:
            stamm = (r["quelle"] or "?").replace("selfplay_", "")
            stamm = stamm.split("_2026")[0]
            gruppen.setdefault(stamm, []).append(r)
        print("\nWaisen nach Quell-Praefix:")
        for k in sorted(gruppen):
            mb = sum(x["mb"] for x in gruppen[k])
            print(f"  {k:<28} {len(gruppen[k]):>5} Bloecke  {mb:>8,.0f} MB")

    if a.list or a.orphans:
        print()
        for r in (orphans if a.orphans else rows):
            mark = "WAISE" if r in orphans else "     "
            print(f"  {mark} {r['block']}  <-  {r['quelle']}  ({r['mb']:.1f} MB)")

    if a.print_delete_list and orphans:
        print("\n# Loeschliste (dieses Werkzeug loescht NICHTS):")
        for r in orphans:
            print(os.path.join(data_dir, r["block"]))


if __name__ == "__main__":
    main()
