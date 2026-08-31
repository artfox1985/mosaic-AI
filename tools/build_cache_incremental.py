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
Funktion wie sie (`corpus_dataset._is_policy_carrier`) und dieselben
Konstanten -- `V20_CARRIER_SHORTCUT_PREFIXES` fuer den Traeger-Kurzschluss,
`LEGACY_STRETCHED_PREFIXES` fuer `bootstrap_native`.

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

# Fortschrittszeilen tragen Emoji; auf einer cp1252-Konsole (Windows,
# Hintergrundlauf ohne -X utf8) stirbt sonst der ERSTE Fortschritts-print
# mit UnicodeEncodeError -- gemessen 2026-08-30, der Watch-Lauf brach nach
# Sekunden ab. Additiv, aendert nur die Ausgabe-Kodierung.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # noqa: PERF203 -- einmalig beim Start
        pass

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

    Der eingefrorene v20-Kurzschluss wird hier genauso gebildet wie dort
    (`V20_CARRIER_SHORTCUT_PREFIXES`), damit Schluessel und Bauweg nicht
    auseinanderlaufen koennen. Wer das nachbaut statt aufzurufen, hat den
    Fehler von morgen schon eingebaut. NICHT zu verwechseln mit
    `bootstrap_native` (Entstauchungs-Frage, eigene Blockliste seit
    2026-08-27) -- bis dahin war es dieselbe Groesse.
    """
    import neural_net
    import corpus_dataset  # C 2026-08-27: MosaicDataset ist ausgezogen
    v20_wdl_generator = basename.startswith(neural_net.V20_CARRIER_SHORTCUT_PREFIXES)
    return corpus_dataset._is_policy_carrier(basename, carrier_set, carrier_prefixes,
                                         v20_wdl_generator)


def _load_manifest(data_dir):
    """Traeger-Manifest wie `MosaicDataset.__init__` es liest (gleiche Env-Var,
    gleicher Default, gleiche Felder)."""
    # Default LEER seit 2026-08-29 (Nutzer-Auftrag, Merkliste 1e) -- gleiche
    # Semantik wie corpus_dataset.py.
    name = os.environ.get("MOSAIC_CARRIER_MANIFEST", "")
    path = os.path.join(data_dir, name) if name else ""
    if not name or not os.path.exists(path):
        return None, None, path
    with open(path, encoding="utf-8") as mf:
        m = json.load(mf)
    prefixes = list(m["carrier_prefixes"]) if "carrier_prefixes" in m else None
    return frozenset(m["policy_carrier_files"]), prefixes, path


def _block_path(data_dir, basename, kwargs):
    import neural_net
    import corpus_dataset  # C 2026-08-27: MosaicDataset ist ausgezogen
    key = neural_net.per_file_cache_key(
        basename, value_target_variant=kwargs["value_target_variant"],
        encoder=kwargs["encoder"], conjunction_head=kwargs["conjunction_head"],
        # Traegerstatus steht seit 2026-08-31 NICHT mehr im Schluessel: der Block
        # ist traegeragnostisch, die Maske kommt beim Zusammenfuegen
        # (merge(..., mask_parts=...)), siehe file_cache_key.per_file_cache_key.
        # Fuer `bootstrap_native` gilt die alte Regel weiter: DIESELBE Quelle wie
        # die Bauschleife (corpus_dataset), damit Schluessel und Bauweg nicht
        # auseinanderlaufen.
        bootstrap_native=not basename.startswith(neural_net.LEGACY_STRETCHED_PREFIXES))
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
    # C 2026-08-29: beim MosaicDataset-Auszug (C 2026-08-27) wurde hier der
    # Import vergessen -- der Neubau-Pfad starb seitdem im Worker mit
    # NameError, nur der Blocks-liegen-schon-Pfad lief. Gefunden durch den
    # --file-list-Funktions-Smoke.
    import corpus_dataset
    ds = corpus_dataset.MosaicDataset(data_dir, files=[path_pkl],
                                  cache_path_override=block_file, **kwargs)
    return basename, block_file, len(ds), True


def _files(data_dir, limit=None, explicit=None):
    """`explicit`: sortierte Basename-Liste aus --file-list -- definiert die
    EXAKTE Teilmenge. Fehlt eine gelistete Datei auf der Platte oder kollidiert
    sie mit MOSAIC_DATA_EXCLUDE, ist das ein harter Abbruch: eine still
    geschrumpfte Teilmenge waere ein anderer Zuschnitt als der beschlossene
    (dieselbe Fehlerklasse wie beim Traeger-Manifest, STATUS-Abschnitt
    TRAEGER-MANIFEST-GENERATOR)."""
    _excl = os.environ.get("MOSAIC_DATA_EXCLUDE")
    if explicit is not None:
        out = []
        for b in explicit:
            f = os.path.join(data_dir, b)
            if not os.path.exists(f):
                raise SystemExit(f"--file-list: {b} existiert nicht in {data_dir}")
            if _excl and re.search(_excl, b):
                raise SystemExit(f"--file-list: {b} kollidiert mit MOSAIC_DATA_EXCLUDE={_excl!r} "
                                 f"-- widerspruechliche Konfiguration, bitte aufloesen")
            out.append(f)
        return out
    file_list = sorted(glob.glob(os.path.join(data_dir, "*.pkl")))
    if _excl:
        file_list = [f for f in file_list if not re.search(_excl, os.path.basename(f))]
    return file_list[:limit] if limit else file_list


def _load_file_list(path):
    """Eine Datei je Zeile (Basename oder Pfad, nur der Basename zaehlt);
    Leerzeilen und #-Kommentare erlaubt. Rueckgabe SORTIERT -- die sortierte
    Reihenfolge ist die serielle Reihenfolge, Voraussetzung der
    Bit-Identitaet des Merges (siehe merge-Kommentar unten)."""
    names = []
    for line in open(path, encoding="utf-8"):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        names.append(os.path.basename(s))
    if not names:
        raise SystemExit(f"--file-list {path}: keine Dateinamen enthalten")
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        raise SystemExit(f"--file-list {path}: doppelte Eintraege {sorted(dupes)[:3]} ...")
    return sorted(names)


def _pass(data_dir, file_list, kwargs, carrier_set, carrier_prefixes, workers, t0):
    """Ein Durchgang ueber alle bekannten Dateien. Gibt (ergebnisse, n_neu)."""
    jobs = []
    for f in file_list:
        # Traegerstatus wird hier nicht mehr gebraucht: der Block ist
        # traegeragnostisch (2026-08-31), die Maske kommt beim Zusammenfuegen.
        jobs.append((data_dir, f, kwargs, _block_path(data_dir, os.path.basename(f), kwargs)))
    # Robustheit gegen Dateien, die WAEHREND eines Durchgangs verschwinden
    # (2026-08-30, erster Produktionstest: das Aufraeumen freigegebener
    # Messkorpora killte den --watch-Lauf mit FileNotFoundError, weil die
    # Liste am Durchgangsbeginn eingesammelt wird). Nur ueberspringen und
    # zaehlen -- ein Lauf, der stundenlang neben einer Erzeugung mitlaeuft,
    # darf an einem `rm` nicht sterben.
    jobs_alive = [a for a in jobs if os.path.exists(a[1])]
    n_verschwunden = len(jobs) - len(jobs_alive)
    if n_verschwunden:
        print(f"  {n_verschwunden} Datei(en) waehrend des Durchgangs verschwunden "
              f"-- uebersprungen", flush=True)
    jobs = jobs_alive
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
    ap.add_argument("--file-list", default=None,
                    help="Textdatei mit einem Dateinamen je Zeile (#-Kommentare erlaubt): "
                         "definiert die EXAKTE Fenster-Teilmenge fuer Bau und --merge-out, "
                         "z.B. ein Rotationsfenster v23+. Fehlende Dateien brechen hart ab. "
                         "Nicht kombinierbar mit --watch/--limit. Nutzer-Auftrag 2026-08-28 "
                         "(Merkliste 1e): Fenster-Monolithen in Minuten aus den Bloecken "
                         "fuegen statt ~40 min Neubau je Fenster")
    a = ap.parse_args()
    if a.file_list and (a.watch or a.limit):
        raise SystemExit("--file-list ist nicht mit --watch/--limit kombinierbar "
                         "(feste Teilmenge gegen mitwachsende/gestutzte Menge)")
    explicit = _load_file_list(a.file_list) if a.file_list else None

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
        file_list = _files(a.data_dir, a.limit, explicit)
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
    window_key = None
    if a.merge_out:
        from build_cache_parallel import merge
        import corpus_dataset
        parts, mask_parts = [], set()
        for f in all_entries:
            b = os.path.basename(f)
            p = _block_path(a.data_dir, b, kwargs)
            if not os.path.exists(p):
                raise SystemExit(f"Block fehlt: {p} (zu {b}) -- erst bauen, dann zusammensetzen.")
            parts.append(p)
            # Traeger-Maske (2026-08-31): der Block ist agnostisch, die
            # Maskierung passiert HIER, beim Fensterbau. Ohne Manifest ist
            # `_carrier_status` ueberall True und die Menge bleibt leer --
            # bestandsidentisch.
            if not _carrier_status(b, carrier_set, carrier_prefixes):
                mask_parts.add(p)
        if mask_parts:
            print(f"🔒 Traeger-Maske: {len(mask_parts)} von {len(parts)} Bloecken werden "
                  f"beim Zusammenfuegen policy-maskiert", flush=True)
        # Fenster-Schluessel der zusammengesetzten Datei (2026-08-28): ohne ihn
        # lehnt `train.py --cache-file` das Ergebnis ab. Die Datei-Bloecke
        # tragen ihn nicht -- ihr Schluessel gehoert je zu EINER Datei
        # (`per_file_cache_key`), nicht zum Fenster.
        window_key = corpus_dataset.window_cache_key(
            a.data_dir, all_entries, value_target_variant=a.value_target_variant,
            encoder=a.encoder, conjunction_head=a.conjunction_head)
        t1 = time.time()
        fields = merge(parts, a.merge_out, window_key=window_key,
                      mask_parts=mask_parts)
        merge_s = time.time() - t1
        print(f"⏱️  Zusammenfuegen: {merge_s:.1f}s ({len(fields)} Felder) -> {a.merge_out} "
              f"(Fenster-Schluessel {window_key.key})", flush=True)

    out = {
        "prereg": "PREREG_cache_build_time.md par.6 (Hebel 4)",
        "data_dir": a.data_dir, "dateien": len(all_entries), "neu_gebaut": built_total,
        "encoder": a.encoder, "value_target_variant": a.value_target_variant,
        "conjunction_head": a.conjunction_head,
        "traeger_manifest": manifest_path if carrier_set is not None else None,
        "watch": a.watch, "merge_out": a.merge_out,
        "file_list": a.file_list,
        "cache_key": window_key.key if window_key is not None else None,
        "cache_key_full": window_key.key_full if window_key is not None else None,
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
