# -*- coding: utf-8 -*-
"""Bestehende Korpus-Dateien in-place komprimieren (corpus_io-Format).

Gemessen 2026-08-26: gzip-6 komprimiert die `.pkl` um Faktor 35,4 (12
ordnungsfrei gezogene Dateien, Spanne 35,1-35,7). Der hv2-Korpus faellt damit
von 32,9 GB auf rund 0,93 GB.

**Ueber die ROHBYTES, nicht ueber Entpickeln.** Der Umweg ueber
`pickle.load` + `pickle.dump` kostet 1,1 s je Datei statt 0,10 und aendert den
Pickle-Inhalt potenziell (Protokoll, Dict-Reihenfolge). Hier wird der
Byte-Strom unveraendert eingepackt -- der Inhalt kann sich gar nicht aendern.

**Der Dateiname bleibt.** Siehe `corpus_io`: Cache-Schluessel,
MOSAIC_DATA_EXCLUDE-Regexe und alle Globs haengen an `.pkl`.

**Sicherheitsnetz:** je Datei wird erst eine Nebendatei geschrieben, dann der
Rundlauf gegen die Originalbytes geprueft, und erst danach ersetzt. Schlaegt
die Pruefung fehl, bleibt das Original unberuehrt und der Lauf bricht ab.
Bereits komprimierte Dateien werden uebersprungen, der Lauf ist also
wiederholbar.

Aufruf:
    python -X utf8 -u tools/repack_corpus.py --data-dir data [--muster "selfplay_hv2_*.pkl"] [--dry-run]
"""
import argparse
import glob
import gzip
import json
import os
import pathlib
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from corpus_io import GZIP_MAGIC, COMPRESS_LEVEL


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--muster", default="*.pkl")
    ap.add_argument("--dry-run", action="store_true",
                    help="nur zaehlen und hochrechnen, nichts schreiben")
    a = ap.parse_args()

    dateien = sorted(glob.glob(os.path.join(a.data_dir, a.muster)))
    if not dateien:
        raise SystemExit(f"Keine Dateien fuer {a.muster} in {a.data_dir}")

    offen, schon = [], 0
    for f in dateien:
        with open(f, "rb") as fh:
            if fh.read(2) == GZIP_MAGIC:
                schon += 1
            else:
                offen.append(f)
    roh_offen = sum(os.path.getsize(f) for f in offen)
    print(f"{len(dateien)} Dateien: {schon} bereits komprimiert, {len(offen)} offen "
          f"({roh_offen/1e9:.2f} GB)", flush=True)
    if a.dry_run or not offen:
        print("(dry-run bzw. nichts zu tun)")
        return

    t0 = time.time()
    roh_s = komp_s = 0
    for i, f in enumerate(offen, 1):
        with open(f, "rb") as fh:
            b = fh.read()
        tmp = f + ".packing"
        with open(tmp, "wb") as out:
            with gzip.GzipFile(fileobj=out, mode="wb",
                               compresslevel=COMPRESS_LEVEL, mtime=0) as g:
                g.write(b)
        # Rundlauf GEGEN DIE ORIGINALBYTES -- staerker als ein Objektvergleich,
        # und er laeuft VOR dem Ersetzen.
        with open(tmp, "rb") as fh:
            zurueck = gzip.decompress(fh.read())
        if zurueck != b:
            os.remove(tmp)
            raise SystemExit(f"ABBRUCH: Rundlauf ungleich bei {f}. Original unveraendert.")
        roh_s += len(b)
        komp_s += os.path.getsize(tmp)
        os.replace(tmp, f)
        if i % 100 == 0 or i == len(offen):
            print(f"   {i}/{len(offen)} ({time.time()-t0:.0f}s, "
                  f"bisher Faktor {roh_s/max(1,komp_s):.1f}x)", flush=True)

    wand = time.time() - t0
    print(f"\n✅ {len(offen)} Dateien: {roh_s/1e9:.2f} GB -> {komp_s/1e9:.3f} GB "
          f"(Faktor {roh_s/komp_s:.1f}x) in {wand:.0f}s")

    erg = {"prereg": "corpus_io / PREREG_cache_build_time.md Umfeld",
           "verzeichnis": a.data_dir, "muster": a.muster,
           "dateien_umgepackt": len(offen), "dateien_schon_komprimiert": schon,
           "vorher_bytes": roh_s, "nachher_bytes": komp_s,
           "faktor": roh_s / komp_s,
           "pruefung": "Rundlauf gegen Originalbytes je Datei VOR dem Ersetzen",
           "laufzeit": {"wanduhr_s": round(wand, 1), "cpu_s": round(time.process_time(), 1),
                        "threads": 1, "s_je_partie": None}}
    ziel = pathlib.Path("evaluations/artifacts/repack_corpus.json")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(erg, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"Artefakt: {ziel}")


if __name__ == "__main__":
    main()
