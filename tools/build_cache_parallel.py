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
    import corpus_dataset  # C 2026-08-27: MosaicDataset ist ausgezogen
    ds = corpus_dataset.MosaicDataset(data_dir, files=list(dateien), **kwargs)
    return idx, ds.cache_path_h5, len(ds)


# Felder, die die Traeger-Maske betreffen (2026-08-31). `ranking_mask` gehoert
# dazu, weil sie in der Bauschleife an `pol_w > 0` haengt.
CARRIER_MASKED_FIELDS = ("policy_weights", "ranking_mask")


def merge(parts, target, window_key=None, mask_parts=None):
    """Konkateniert die Teil-Caches in Blockreihenfolge zu einem Cache.

    Hiess bis 2026-08-28 `zusammenfuegen`; `build_cache_incremental.py:219`
    importierte schon immer `merge` und waere beim ersten `--merge-out` an
    einem ImportError gestorben. Umbenannt statt den Aufrufer zurueckzubiegen
    -- die Bezeichner-Konvention (CLAUDE.md 2026-08-24) will ohnehin Englisch.

    `window_key` (optional, `corpus_dataset.WindowCacheKey`): wird dem Ziel als
    DATEI-Attribut aufgepraegt, damit `train.py --cache-file` die Datei pruefen
    kann. Ohne das Attribut lehnt der Waechter sie ab -- absichtlich, siehe
    `corpus_dataset.verify_cache_file`. NICHT aus den Teil-Caches uebernehmbar:
    deren Schluessel gehoert je zu einer TEILMENGE der Dateien, nicht zum
    Fenster.

    `mask_parts` (2026-08-31, Traeger-Umbau): Menge von Teil-Pfaden, deren
    Policy-Gewichte beim Schreiben auf 0 gesetzt werden -- die Traeger-Maske.
    Sie steht seit dem Umbau NICHT mehr im Datei-Block (der ist
    traegeragnostisch, siehe `file_cache_key.per_file_cache_key`), sondern
    gehoert zum FENSTER und wird hier angewandt. Betroffen sind `policy_weights`
    UND `ranking_mask`: die Ranking-Maske haengt in der Bauschleife an
    `pol_w > 0` (corpus_dataset.py), sie muss also mitmaskiert werden, sonst
    lernte der Ranking-Loss auf Zuegen, deren Policy-Ziel maskiert ist.

    WIRKLICH streamend: das Zielfeld wird mit seiner ENDGUELTIGEN Form angelegt
    und dann Block fuer Block in seinen Schnitt geschrieben. Die erste Fassung
    las alle Bloecke eines Feldes ein und konkatenierte sie -- das haelt das
    Feld doppelt im RAM (beim vollen Korpus 6 GB Bloecke plus 6 GB Ergebnis)
    und war Teil desselben Speicherproblems wie die Blockzahl unten.
    """
    with h5py.File(parts[0], "r") as hf:
        felder = sorted(hf.keys())
        attrs = {k: dict(hf[k].attrs) for k in felder}
    # Alle Teile muessen dieselben Felder haben -- sonst wurden sie mit
    # unterschiedlicher Konfiguration gebaut, und das Zusammenfuegen waere
    # stillschweigend falsch.
    for t in parts[1:]:
        with h5py.File(t, "r") as hf:
            if sorted(hf.keys()) != felder:
                raise SystemExit(
                    f"Teil-Caches haben verschiedene Felder:\n  {parts[0]}: {felder}\n"
                    f"  {t}: {sorted(hf.keys())}\nAbbruch -- das waere ein stiller Fehler.")
    # Formen vorab einsammeln, damit das Ziel in einem Stueck angelegt werden
    # kann.
    formen = {}
    for t in parts:
        with h5py.File(t, "r") as hf:
            for k in felder:
                formen.setdefault(k, []).append((hf[k].shape, hf[k].dtype))
    with h5py.File(target, "w") as out:
        for k in felder:
            n_ges = sum(f[0][0] for f in formen[k])
            rest = formen[k][0][0][1:]
            dt = formen[k][0][1]
            d = out.create_dataset(k, shape=(n_ges,) + rest, dtype=dt, compression="lzf")
            off = 0
            for t in parts:
                with h5py.File(t, "r") as hf:
                    blk = np.array(hf[k])
                if mask_parts and t in mask_parts and k in CARRIER_MASKED_FIELDS:
                    blk = np.zeros_like(blk)
                d[off:off + blk.shape[0]] = blk
                off += blk.shape[0]
                del blk
            for a, v in attrs[k].items():
                d.attrs[a] = v
        if window_key is not None:
            import corpus_dataset
            corpus_dataset.stamp_cache_key_attrs(out, window_key)
    return felder


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2),
                    help="gleichzeitig laufende Prozesse")
    ap.add_argument("--blocks", type=int, default=None,
                    help="Zahl der Datei-Bloecke. NICHT an --workers koppeln: jeder Worker "
                         "haelt einen ganzen Block im Zwischenformat (~7 KB je Zustand). Bei "
                         "10 Bloecken auf dem vollen Korpus waren das 24 GB und 0,7 GB frei "
                         "-- Vorfall 2026-08-26. Default: so viele, dass ein Block rund 100k "
                         "Zustaende hat.")
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

    # Blockzahl aus dem SPEICHER, nicht aus der Workerzahl: rund 100k Zustaende
    # je Block, bei gemessenen ~174 Zustaenden je Partie und 10 Partien je Datei
    # also rund 57 Dateien. Wer mehr Worker will, bekommt mehr Gleichzeitigkeit,
    # nicht groessere Bloecke.
    n_b = a.blocks or max(1, round(len(dateien) / 57))
    n_b = max(1, min(n_b, len(dateien)))
    # ZUSAMMENHAENGENDE Bloecke, damit die Konkatenation die serielle
    # Reihenfolge reproduziert.
    grenzen = [round(i * len(dateien) / n_b) for i in range(n_b + 1)]
    bloecke = [dateien[grenzen[i]:grenzen[i + 1]] for i in range(n_b)]
    bloecke = [b for b in bloecke if b]
    n_w = max(1, min(a.workers, len(bloecke)))

    kwargs = dict(encoder=a.encoder, value_target_variant=a.value_target_variant,
                  conjunction_head=a.conjunction_head)
    print(f"📦 {len(dateien)} Dateien auf {len(bloecke)} Bloecke "
          f"(~{len(dateien)//max(1,len(bloecke))} Dateien je Block), {n_w} gleichzeitig",
          flush=True)

    t0 = time.time()
    ergebnisse = []
    with mp.Pool(n_w) as pool:
        # imap_unordered statt map: Fortschritt wird sichtbar, sobald ein Block
        # fertig ist (Regel "lange Laeufe zeigen Fortschritt"). Die Reihenfolge
        # stellt das `sort()` unten wieder her -- sie haengt am Block-Index,
        # nicht an der Fertigstellungsfolge.
        for fertig, e in enumerate(pool.imap_unordered(
                _bau_teilmenge,
                [(a.data_dir, b, kwargs, i) for i, b in enumerate(bloecke)]), 1):
            ergebnisse.append(e)
            print(f"   {fertig}/{len(bloecke)} Bloecke fertig "
                  f"({time.time()-t0:.0f}s, zuletzt Block {e[0]} mit {e[2]} Zustaenden)",
                  flush=True)
    t_bau = time.time() - t0
    ergebnisse.sort()
    teile = [pfad for _, pfad, _ in ergebnisse]
    n_zustaende = sum(n for _, _, n in ergebnisse)
    print(f"\n⏱️  Teil-Bau: {t_bau:.1f}s, {n_zustaende} Zustaende")

    # Fenster-Schluessel fuer die ZUSAMMENGEFUEGTE Datei: derselbe, den
    # `MosaicDataset` fuer genau diese Dateiliste rechnen wuerde -- und damit
    # der, den `train.py --cache-file` erwartet. Berechnet aus derselben
    # Konfiguration wie die Worker (`kwargs`) und aus DER Dateiliste, die
    # tatsaechlich gebaut wurde (inkl. --limit und MOSAIC_DATA_EXCLUDE).
    import corpus_dataset
    window_key = corpus_dataset.window_cache_key(
        a.data_dir, dateien, value_target_variant=a.value_target_variant,
        encoder=a.encoder, conjunction_head=a.conjunction_head)

    t1 = time.time()
    felder = merge(teile, a.out, window_key=window_key)
    t_merge = time.time() - t1
    wand = time.time() - t0
    print(f"⏱️  Zusammenfuegen: {t_merge:.1f}s ({len(felder)} Felder)")
    print(f"✅ {a.out}  --  gesamt {wand:.1f}s, Fenster-Schluessel {window_key.key}")
    print(f"   Nutzbar als: python train.py ... --cache-file {a.out}")

    erg = {
        "prereg": "PREREG_cache_build_time.md Hebel 1",
        "dateien": len(dateien), "bloecke": len(bloecke), "zustaende": n_zustaende,
        "ziel": a.out, "teil_caches": teile, "encoder": a.encoder,
        "cache_key": window_key.key, "cache_key_full": window_key.key_full,
        # Ohne diese beiden Felder ist der Schluessel nachtraeglich NICHT
        # reproduzierbar (Befund 2026-08-28 an .par_full_79.h5): das Artefakt
        # hielt nur `encoder`, und `--value-target-variant` hat hier den
        # Default "default", waehrend train.py "nortv" als Default fuehrt --
        # zwei verschiedene Schluessel auf demselben Korpus.
        "value_target_variant": a.value_target_variant,
        "conjunction_head": a.conjunction_head,
        "data_exclude": os.environ.get("MOSAIC_DATA_EXCLUDE"),
        "carrier_manifest": os.environ.get("MOSAIC_CARRIER_MANIFEST"),
        "limit": a.limit,
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
