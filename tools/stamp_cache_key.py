# -*- coding: utf-8 -*-
"""Praegt einem VORHANDENEN Trainings-Cache seinen Fenster-Schluessel auf
(Schlachtplan A0 Schritt 2c, PREREG_cache_build_time.md par.6).

WOFUER: `train.py --cache-file` lehnt jeden Cache ohne hinterlegten
Fenster-Schluessel ab -- absichtlich, denn einer Datei ohne Selbstauskunft
sieht man nicht an, fuer WELCHES Fenster sie gebaut wurde, und ein
Voll-Korpus-Cache gegen ein Val-Split-Fenster ist genau der stille
Obermengen-Fehler, den der Waechter verhindern soll.

Vor dem 2026-08-28 gebaute Caches (z.B. `data/.par_full_79.h5`) tragen das
Attribut nicht. Sie deshalb NEU zu bauen kostet Stunden -- dieses Werkzeug
rechnet den Schluessel stattdessen neu aus und schreibt ihn als
DATEI-Attribut in die vorhandene h5. Die Datasets bleiben unberuehrt.

WAS DAS WERKZEUG NICHT KANN, und das ist wichtig: es PRUEFT nicht, ob der
Inhalt der Datei wirklich zu dem Schluessel gehoert, den es aufpraegt -- es
GLAUBT der Kommandozeile. Wer hier die falschen Parameter angibt, praegt der
Datei eine falsche Selbstauskunft auf und macht den Waechter blind. Die
Parameter (`--data-dir`, `--encoder`, `--value-target-variant`,
`--conjunction-head`, MOSAIC_DATA_EXCLUDE, MOSAIC_CARRIER_MANIFEST,
MOSAIC_CACHE_NOPACK, MOSAIC_CACHE_F32, MOSAIC_IGNORE_POLICY_TARGET_VALID,
MOSAIC_REACH_TARGET_K1) muessen deshalb EXAKT die des Bau-Laufs sein --
nachzulesen in dessen Artefakt (`evaluations/artifacts/cache_build_*.json`).
Der Zeilenzahl-Abgleich unten (`values.shape[0]`) ist der einzige billige
Gegencheck, den es gibt, und er ist schwach: er faengt eine falsche
DATEILISTE nur, wenn sie auch eine andere Zustandszahl hat.

Deshalb ist `--check` der Default: ohne `--write` wird nur verglichen und
berichtet, nichts geschrieben.

Aufruf:
    # nur nachsehen, was in der Datei steht und was erwartet waere
    python -X utf8 -u tools/stamp_cache_key.py --cache-file data/.par_full_79.h5 \
        --data-dir data --encoder 2d

    # tatsaechlich aufpraegen
    python -X utf8 -u tools/stamp_cache_key.py --cache-file data/.par_full_79.h5 \
        --data-dir data --encoder 2d --write
"""
import argparse
import glob
import os
import pathlib
import re
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
# BEIDE Pfade: `corpus_dataset` liegt in engine/py, importiert aber `config`
# aus der Projektwurzel (gleiche Begruendung wie in build_cache_parallel.py).
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cache-file", required=True, help="vorhandene HDF5-Cache-Datei")
    ap.add_argument("--data-dir", default="data",
                    help="Ordner, ueber dessen *.pkl der Cache gebaut wurde")
    ap.add_argument("--encoder", default="flat", choices=["flat", "2d"])
    ap.add_argument("--value-target-variant", default="default")
    ap.add_argument("--conjunction-head", action="store_true")
    ap.add_argument("--limit", type=int, default=None,
                    help="nur die ersten N Dateien -- NUR setzen, wenn der Bau-Lauf "
                         "dasselbe --limit hatte")
    ap.add_argument("--write", action="store_true",
                    help="Attribute wirklich schreiben (ohne: reiner Vergleich)")
    ap.add_argument("--force", action="store_true",
                    help="einen ABWEICHENDEN vorhandenen Schluessel ueberschreiben")
    a = ap.parse_args()

    import h5py
    import corpus_dataset

    if not os.path.exists(a.cache_file):
        raise SystemExit(f"❌ '{a.cache_file}' existiert nicht.")

    # Dateiliste GENAU wie die Bau-Werkzeuge sie bilden (sortiert, dann
    # MOSAIC_DATA_EXCLUDE, dann --limit). Die Exclude-Anwendung passiert in
    # `window_cache_key` noch einmal und ist idempotent -- hier steht sie, weil
    # `--limit` NACH dem Filtern greift (build_cache_parallel.py) und die
    # Reihenfolge sonst eine andere Teilmenge ergaebe.
    files = sorted(glob.glob(os.path.join(a.data_dir, "*.pkl")))
    excl = os.environ.get("MOSAIC_DATA_EXCLUDE")
    if excl:
        files = [f for f in files if not re.search(excl, os.path.basename(f))]
    if a.limit:
        files = files[:a.limit]
    if not files:
        raise SystemExit(f"❌ Keine .pkl-Dateien in {a.data_dir} -- Schluessel waere leer.")

    wk = corpus_dataset.window_cache_key(
        a.data_dir, files, value_target_variant=a.value_target_variant,
        encoder=a.encoder, conjunction_head=a.conjunction_head)

    with h5py.File(a.cache_file, "r") as hf:
        attrs = dict(hf.attrs)
        rows = int(hf["values"].shape[0]) if "values" in hf else None
        has_planes = ("planes" in hf) or ("planes_packed" in hf)

    def _text(v):
        # Gleiche Begruendung wie in `corpus_dataset.verify_cache_file`.
        return v.decode("utf-8") if isinstance(v, bytes) else (None if v is None else str(v))

    present = _text(attrs.get(corpus_dataset.CACHE_KEY_FULL_ATTR))
    present_short = _text(attrs.get(corpus_dataset.CACHE_KEY_ATTR))
    print(f"Datei          : {a.cache_file}")
    print(f"  Zustaende    : {rows}")
    print(f"  planes drin  : {has_planes}  (--encoder {a.encoder})")
    print(f"  Schluessel   : {present_short or '(keiner)'} (voll: {present or '(keiner)'})")
    print(f"Erwartet       : {wk.key} (voll: {wk.key_full})")
    print(f"  Fenster      : {len(wk.files)} Dateien "
          f"({os.path.basename(wk.files[0])} .. {os.path.basename(wk.files[-1])})")

    # Schwacher, aber kostenloser Gegencheck (siehe Modulkopf): ein 2D-Cache
    # ohne planes-Dataset kann nicht zu `--encoder 2d` gehoeren.
    if a.encoder == "2d" and not has_planes:
        raise SystemExit("❌ --encoder 2d verlangt, aber die Datei hat weder 'planes' noch "
                         "'planes_packed'. Falsche Parameter oder falsche Datei.")
    if a.encoder == "flat" and has_planes:
        raise SystemExit("❌ --encoder flat verlangt, aber die Datei traegt ein "
                         "planes-Dataset. Falsche Parameter oder falsche Datei.")

    if present is not None or present_short is not None:
        matches = (present == wk.key_full) if present is not None else (present_short == wk.key)
        if matches:
            print("✅ Schluessel steht schon drin und passt -- nichts zu tun.")
            return
        if not a.force:
            raise SystemExit(
                "❌ Die Datei traegt einen ANDEREN Schluessel als den erwarteten.\n"
                "   Das heisst im Normalfall: falsche Parameter oder falsche Datei --\n"
                "   NICHT 'das Attribut ist veraltet'. Erst klaeren, dann ggf. --force.")
        print("⚠️  --force: abweichender Bestandsschluessel wird ueberschrieben.")

    if not a.write:
        print("ℹ️  Nur geprueft (kein --write). Zum Aufpraegen: dieselbe Zeile mit --write.")
        return

    with h5py.File(a.cache_file, "r+") as hf:
        corpus_dataset.stamp_cache_key_attrs(hf, wk)
    print(f"✅ Schluessel {wk.key} aufgepraegt. Nutzbar als:")
    print(f"   python train.py ... --cache-file {a.cache_file}")


if __name__ == "__main__":
    main()
