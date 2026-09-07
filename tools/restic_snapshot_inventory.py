#!/usr/bin/env python
"""Aggregiert `restic ls <snapshot> --json` (auf stdin) nach Verzeichnis und Endung.

Warum ein eigener Aufsatz: `restic ls` gibt eine Zeile je PFAD aus -- bei dem
legacy-mirror-Stand ueber 100 GiB sind das sehr viele Zeilen, und die Frage
"welche Pfade machen den Loewenanteil aus" beantwortet keine davon einzeln.

Fortschritt geht mit flush=True auf stderr, damit er im laufenden Betrieb
sichtbar ist (CLAUDE.md "Lange Laeufe NIE in eine Pipe" -- die Pipe ist hier
zulaessig, WEIL dieser Verbraucher selbst Fortschritt druckt).

Aufruf:
    restic ls <snapshot-id> --json | python -u tools/restic_snapshot_inventory.py [tiefe]
"""
import collections
import json
import sys

DEPTH = int(sys.argv[1]) if len(sys.argv) > 1 else 2

size_by_dir: collections.Counter = collections.Counter()
count_by_dir: collections.Counter = collections.Counter()
size_by_ext: collections.Counter = collections.Counter()
count_by_ext: collections.Counter = collections.Counter()
total = files = lines = 0

for line in sys.stdin:
    lines += 1
    if lines % 100_000 == 0:
        print(f"   ... {lines:,} Zeilen, {total / 2**30:.1f} GiB", file=sys.stderr, flush=True)
    line = line.strip()
    if not line or not line.startswith("{"):
        continue
    try:
        rec = json.loads(line)
    except json.JSONDecodeError:
        continue
    if rec.get("type") != "file":
        continue
    size = rec.get("size") or 0
    path = (rec.get("path") or "").replace("\\", "/").lstrip("/")
    parts = path.split("/")
    bucket = "/".join(parts[:DEPTH]) if len(parts) > DEPTH else "/".join(parts[:-1]) or "(Wurzel)"
    size_by_dir[bucket] += size
    count_by_dir[bucket] += 1
    name = parts[-1]
    ext = ("." + name.rsplit(".", 1)[1].lower()) if "." in name else "(ohne)"
    size_by_ext[ext] += size
    count_by_ext[ext] += 1
    total += size
    files += 1

print(f"\nGESAMT: {total / 2**30:.2f} GiB in {files:,} Dateien ({lines:,} Zeilen gelesen)\n")
print(f"Nach Verzeichnis (Tiefe {DEPTH}), groesste 25:")
for k, v in size_by_dir.most_common(25):
    print(f"  {v / 2**30:8.2f} GiB  {count_by_dir[k]:7,d} Dateien  {k}/")
print("\nNach Endung, groesste 15:")
for k, v in size_by_ext.most_common(15):
    print(f"  {v / 2**30:8.2f} GiB  {count_by_ext[k]:7,d} Dateien  {k}")
