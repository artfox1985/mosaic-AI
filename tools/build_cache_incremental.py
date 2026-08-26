# -*- coding: utf-8 -*-
"""Cache JE DATEI, auch WAEHREND der Erzeugung (PREREG_cache_build_time.md par.6,
Hebel 4).

WOFUER: heute entsteht der Cache NACH dem Korpus und kostet dort 36 min
(parallel) bzw. 2,58 h (seriell) auf dem kritischen Pfad. Jede fertige `.pkl`
kann ihren Block aber sofort bekommen -- dann ist der Cache fertig, wenn der
Korpus fertig ist, und der kritische Pfad ist leer.

VERHAELTNIS ZU HEBEL (1): derselbe Umbau, eine Stufe feiner. `build_cache_
parallel.py` teilt in ~57-Datei-Bloecke und cacht die; hier ist der Block EINE
Datei, und der Schluessel ist geteilt. Der Pool darueber bleibt derselbe
Gedanke -- Parallelisierung und Memoisierung auf derselben Zerlegung.

DIE SCHLUESSELTEILUNG ist die heikle Stelle (par.6) und liegt in
`neural_net.per_file_cache_key`:
  je DATEI  -> Inhalt des Blocks: Schema, Encoder, Sharpen, Value-Variante,
               Konjunktion/Reachability, Bitpacking, ignore_ptv, f32 UND der
               AUFGELOESTE Traegerstatus dieser Datei;
  je FENSTER -> welche Dateien, Manifest als Ganzes, Train/Val-Split: steht
               bewusst NICHT im Datei-Schluessel, sonst haengt jeder Block
               wieder am Fenster.
Beide Richtungen sind vor dem ersten Bau geprueft worden:
`tools/probes/file_cache_key_probe.py` (MISS je Parameter) und
`tools/probes/cache_parity_probe.py` (Bit-Identitaet gegen den seriellen Bau).

WARUM DER TRAEGERSTATUS HIER NOCH EINMAL AUFGELOEST WIRD, statt ihn dem
Bauweg zu ueberlassen: der Schluessel muss VOR dem Bau feststehen. Damit er
nicht von der Bauschleife abweichen kann, benutzt dieses Werkzeug DIESELBE
Funktion wie sie (`neural_net._is_policy_carrier`) und dieselbe Quelle fuer
`bootstrap_native` (`WDL_GENERATOR_PREFIXES`).

Aufruf:
    # einmalig ueber alles, was da ist
    python -X utf8 -u tools/build_cache_incremental.py --data-dir data \\
        --encoder 2d --workers 6

    # mitlaufend waehrend der Erzeugung: baut neu Dazugekommenes, endet, wenn
    # drei Durchgaenge nichts Neues mehr finden
    python -X utf8 -u tools/build_cache_incremental.py --data-dir data \\
        --encoder 2d --workers 6 --watch --leerlauf-abbruch 3

    # Fenster-Cache aus den Datei-Bloecken zusammensetzen
    python -X utf8 -u tools/build_cache_incremental.py --data-dir data \\
        --encoder 2d --merge-out data/.cache_window.h5
"""
import argparse
import glob
import json
import multiprocessing as mp
import os
import pathlib
import re
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent
# BEIDE Pfade: `neural_net` liegt in engine/py, importiert aber `config` aus
# der Projektwurzel (gleiche Begruendung wie in build_cache_parallel.py).
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))

# Das Zusammenfuegen ist bereits gebaut und auf Bit-Identitaet abgenommen --
# hier wird es benutzt, nicht nachgebaut (CLAUDE.md: erst schauen, was da ist).
sys.path.insert(0, str(_ROOT / "tools"))


def _carrier_status(basename, carrier_set, carrier_prefixes):
    """Traegerstatus EINER Datei -- mit der Funktion der Bauschleife.

    `bootstrap_native` wird hier genauso gebildet wie dort (Praefix-Test auf
    den WDL-Generator), damit Schluessel und Bauweg nicht auseinanderlaufen
    koennen. Wer das nachbaut statt aufzurufen, hat den Fehler von morgen
    schon eingebaut.
    """
    import neural_net
    import corpus_dataset  # C 2026-08-27: MosaicDataset ist ausgezogen
    bootstrap_native = basename.startswith(neural_net.WDL_GENERATOR_PREFIXES)
    return corpus_dataset._is_policy_carrier(basename, carrier_set, carrier_prefixes,
                                         bootstrap_native)


def _load_manifest(data_dir):
    """Traeger-Manifest wie `MosaicDataset.__init__` es liest (gleiche Env-Var,
    gleicher Default, gleiche Felder)."""
    path = os.path.join(
        data_dir, os.environ.get("MOSAIC_CARRIER_MANIFEST", "policy_carrier_manifest_v20.json"))
    if not os.path.exists(path):
        return None, None, path
    with open(path, encoding="utf-8") as mf:
        m = json.load(mf)
    prefixes = list(m["carrier_prefixes"]) if "carrier_prefixes" in m else None
    return frozenset(m["policy_carrier_files"]), prefixes, path


def _block_path(data_dir, basename, kwargs, carrier):
    import neural_net
    import corpus_dataset  # C 2026-08-27: MosaicDataset ist ausgezogen
    key = neural_net.per_file_cache_key(
        basename, value_target_variant=kwargs["value_target_variant"],
        encoder=kwargs["encoder"], conjunction_head=kwargs["conjunction_head"],
        policy_carrier=carrier)
    return os.path.join(data_dir, f".filecache_{key}.h5")


def _build_one_file(args):
    """Laeuft im Worker: baut GENAU EINE Datei in ihren Block-Cache.

    Gibt (basename, pfad, n_zustaende, gebaut?) zurueck -- die Arrays bleiben
    auf der Platte (bei 2.400 Dateien waeren es sonst >11 GB durch die Pipe).
    """
    data_dir, path_pkl, kwargs, block_file = args
    basename = os.path.basename(path_pkl)
    if os.path.exists(block_file):
        import h5py
        with h5py.File(block_file, "r") as hf:
            n = hf["values"].shape[0] if "values" in hf else 0
        return basename, block_file, n, False
    import neural_net
    ds = corpus_dataset.MosaicDataset(data_dir, files=[path_pkl],
                                  cache_path_override=block_file, **kwargs)
    return basename, block_file, len(ds), True


def _files(data_dir, limit=None):
    file_list = sorted(glob.glob(os.path.join(data_dir, "*.pkl")))
    _excl = os.environ.get("MOSAIC_DATA_EXCLUDE")
    if _excl:
        file_list = [f for f in file_list if not re.search(_excl, os.path.basename(f))]
    return file_list[:limit] if limit else file_list


def _pass(data_dir, file_list, kwargs, carrier_set, carrier_prefixes, workers, t0):
    """Ein Durchgang ueber alle bekannten Dateien. Gibt (ergebnisse, n_neu)."""
    jobs = []
    for f in file_list:
        carrier = _carrier_status(os.path.basename(f), carrier_set, carrier_prefixes)
        jobs.append((data_dir, f, kwargs, _block_path(data_dir, os.path.basename(f),
                                                          kwargs, carrier)))
    pending = [a for a in jobs if not os.path.exists(a[3])]
    already_done = len(jobs) - len(pending)
    print(f"📦 {len(jobs)} Dateien: {already_done} Bloecke liegen schon, "
          f"{len(pending)} zu bauen", flush=True)
    results = []
    if pending:
        n_w = max(1, min(workers, len(pending)))
        with mp.Pool(n_w) as pool:
            for done, e in enumerate(pool.imap_unordered(_build_one_file, pending), 1):
                results.append(e)
                # Fortschritt JE DATEI: bei 2.400 Dateien ist das die einzige
                # Groesse, an der man den Stand ablesen kann (CLAUDE.md
                # "Zaehlen statt hochrechnen").
                print(f"   {done}/{len(pending)} gebaut  ({time.time()-t0:.0f}s, "
                      f"zuletzt {e[0]} mit {e[2]} Zustaenden)", flush=True)
    return results, len(pending)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--encoder", default="flat", choices=["flat", "2d"])
    ap.add_argument("--value-target-variant", default="default")
    ap.add_argument("--conjunction-head", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="nur die ersten N Dateien (Test)")
    ap.add_argument("--watch", action="store_true",
                    help="mitlaufen: neue Dateien aufsammeln, bis --leerlauf-abbruch "
                         "Durchgaenge nichts Neues mehr finden")
    ap.add_argument("--wartezeit", type=float, default=60.0,
                    help="Sekunden zwischen zwei Durchgaengen im --watch-Modus")
    ap.add_argument("--leerlauf-abbruch", type=int, default=3,
                    help="so viele leere Durchgaenge beenden den --watch-Modus")
    ap.add_argument("--merge-out", default=None,
                    help="Fenster-Cache aus den Datei-Bloecken zusammensetzen (Dateireihenfolge "
                         "sortiert, wie der serielle Bau)")
    a = ap.parse_args()

    kwargs = dict(encoder=a.encoder, value_target_variant=a.value_target_variant,
                  conjunction_head=a.conjunction_head)
    carrier_set, carrier_prefixes, manifest_path = _load_manifest(a.data_dir)
    print(f"Traeger-Manifest: {manifest_path if carrier_set is not None else 'KEINS (jede Datei traegt)'}",
          flush=True)

    t0 = time.time()
    t_cpu0 = time.process_time()
    all_entries = []
    built_total = 0
    empty = 0
    while True:
        file_list = _files(a.data_dir, a.limit)
        if not file_list:
            raise SystemExit(f"Keine .pkl-Dateien in {a.data_dir}")
        results, n_open = _pass(a.data_dir, file_list, kwargs, carrier_set,
                                         carrier_prefixes, a.workers, t0)
        all_entries = file_list
        built_total += sum(1 for e in results if e[3])
        if not a.watch:
            break
        empty = empty + 1 if n_open == 0 else 0
        if empty >= a.leerlauf_abbruch:
            print(f"✅ {empty} Durchgaenge ohne neue Datei -- Ende des Mitlaufens.", flush=True)
            break
        time.sleep(a.wartezeit)

    wall = time.time() - t0
    cpu = time.process_time() - t_cpu0

    # --- Zusammensetzen (optional): sortierte Dateireihenfolge = serielle
    # Reihenfolge, Voraussetzung fuer die Bit-Identitaet.
    merge_s = None
    if a.merge_out:
        from build_cache_parallel import merge
        parts = []
        for f in all_entries:
            b = os.path.basename(f)
            c = _carrier_status(b, carrier_set, carrier_prefixes)
            p = _block_path(a.data_dir, b, kwargs, c)
            if not os.path.exists(p):
                raise SystemExit(f"Block fehlt: {p} (zu {b}) -- erst bauen, dann zusammensetzen.")
            parts.append(p)
        t1 = time.time()
        fields = merge(parts, a.merge_out)
        merge_s = time.time() - t1
        print(f"⏱️  Zusammenfuegen: {merge_s:.1f}s ({len(fields)} Felder) -> {a.merge_out}",
              flush=True)

    out = {
        "prereg": "PREREG_cache_build_time.md par.6 (Hebel 4)",
        "data_dir": a.data_dir, "dateien": len(all_entries), "neu_gebaut": built_total,
        "encoder": a.encoder, "value_target_variant": a.value_target_variant,
        "conjunction_head": a.conjunction_head,
        "traeger_manifest": manifest_path if carrier_set is not None else None,
        "watch": a.watch, "merge_out": a.merge_out,
        # Pflichtfelder nach CLAUDE.md "Laufzeiten messen, nicht schaetzen".
        # `threads` ist hier die Worker-Zahl des Pools; `cpu_s` misst NUR den
        # Elternprozess (die Worker sind eigene Prozesse), taugt also als
        # Overhead-Mass, nicht als Rechenzeit -- deshalb steht es so dabei.
        "laufzeit": {
            "wanduhr_s": round(wall, 1),
            "cpu_s": round(cpu, 1),
            "cpu_s_hinweis": "nur Elternprozess, Worker sind eigene Prozesse",
            "threads": a.workers,
            "zusammenfuegen_s": round(merge_s, 1) if merge_s is not None else None,
            "s_je_datei": round(wall / built_total, 2) if built_total else None,
        },
    }
    target = pathlib.Path("evaluations/artifacts/cache_build_incremental.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"✅ {built_total} Bloecke neu gebaut, {len(all_entries)} Dateien abgedeckt, "
          f"{wall:.1f}s gesamt")
    print(f"Artefakt: {target}")


if __name__ == "__main__":
    main()
