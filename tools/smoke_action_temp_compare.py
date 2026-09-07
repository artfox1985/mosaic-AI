#!/usr/bin/env python
"""Vergleicht die drei Korpora der Rauchprobe aus tools/smoke_action_temp_modes.sh.

Verglichen wird die ZUGFOLGE je Partie (Feld `action`), nicht die ganze Aufzeichnung:
die Zugwahl ist genau das, was `MOSAIC_ACTION_TEMP` veraendert. `game_id` traegt einen
Zeitstempel und faellt darum heraus (gleiche Ausnahme wie in `generator_repro_probe`).
"""
import glob
import hashlib
import json
import sys

sys.path.insert(0, ".")  # corpus_io liegt in der Projektwurzel, nicht in tools/
from corpus_io import load_records  # noqa: E402


def move_hash(mode: int) -> tuple[str, int]:
    files = sorted(glob.glob(f"data/selfplay_smoke-at{mode}_*.pkl"))
    if not files:
        raise SystemExit(f"FEHLT: keine Dateien fuer Modus {mode}")
    h = hashlib.sha256()
    n = 0
    for f in files:
        for rec in load_records(f):
            h.update(json.dumps(rec.get("action"), sort_keys=True, default=str).encode())
            n += 1
    return h.hexdigest()[:16], n


hashes = {m: move_hash(m) for m in (0, 1, 2)}
for m, (hx, n) in hashes.items():
    print(f"  Modus {m}: {n} Schritte, Zugfolge-Hash {hx}")

ok = True
for a, b in ((0, 1), (0, 2), (1, 2)):
    same = hashes[a][0] == hashes[b][0]
    verdict = "IDENTISCH -- der Knopf wirkt NICHT" if same else "verschieden (erwartet)"
    print(f"  {a} gegen {b}: {verdict}")
    ok &= not same
print("\nRAUCHPROBE GRUEN: alle drei Modi erzeugen verschiedene Zugfolgen." if ok
      else "\nRAUCHPROBE ROT: mindestens ein Modus ist wirkungslos.")
sys.exit(0 if ok else 1)
