# -*- coding: utf-8 -*-
"""tools/window_train_split.py -- den Train/Val-Split von train.py VORAB
nachbilden und den Fenster-Schluessel des Trainingsanteils ausgeben.

Wozu (PREREG_cache_build_time.md Hebel 3, Nachtprogramm 2026-09-01 N3): der
Fenster-Monolith (`build_cache_incremental.py --merge-out`) muss fuer GENAU die
Dateiliste gebaut werden, die train.py als Trainingsanteil verwendet -- also
das Fenster MINUS den Val-Split. Ohne dieses Werkzeug musste man dafuer
`--val-frac 0` fahren. Der Split hier ist zeilenweise der aus train.py
(Zeilen 1161-1305): Fensterliste sortiert nach vollem Pfad, Val-Kandidaten
per MOSAIC_VAL_POOL-Regex, `random.Random(20260707).shuffle`, n_val =
max(1, round(n * val_frac)). Aendert train.py seinen Split, MUSS diese Datei
mitziehen -- der Schluesselvergleich unten macht eine Drift sichtbar, weil
train.py dann einen anderen `.cache_<key>.h5` sucht und neu baut.

Beispiel:
    MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v23.json \\
    python tools/window_train_split.py --file-list data/window_v23.txt \\
        --val-frac 0.05 --val-pool '^selfplay_v22-b05-' \\
        --encoder 2d --value-target-variant nortv \\
        --train-list-out data/window_v23_train.txt
    # danach:
    python tools/build_cache_incremental.py --data-dir <ABSOLUTER data-Pfad> \\
        --encoder 2d --value-target-variant nortv --workers 6 \\
        --file-list data/window_v23_train.txt \\
        --merge-out <ABSOLUTER data-Pfad>/.cache_<KEY>.h5

Der `--data-dir` muss beim Zusammenfuegen als ABSOLUTER Pfad uebergeben werden
(derselbe wie `config.DATA_DIR`), weil der Schluessel die vollen Pfade der
Dateiliste enthaelt. train.py laedt `.cache_<key>.h5` dann ohne `--cache-file`.
"""
import argparse
import glob
import os
import random
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "engine", "py"))

SPLIT_SEED = 20260707   # train.py, Val-Split


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--file-list", required=True, help="Fensterliste (Basenames), wie fuer train.py")
    ap.add_argument("--val-frac", type=float, required=True)
    ap.add_argument("--val-pool", default=os.environ.get("MOSAIC_VAL_POOL"),
                    help="Regex der Val-Kandidaten (Default: MOSAIC_VAL_POOL aus der Umgebung)")
    ap.add_argument("--encoder", default="flat", choices=["flat", "2d"])
    ap.add_argument("--value-target-variant", default="default")
    ap.add_argument("--conjunction-head", action="store_true")
    ap.add_argument("--train-list-out", required=True)
    ap.add_argument("--val-list-out", default=None)
    a = ap.parse_args()

    from config import DATA_DIR
    import corpus_dataset

    wanted = [os.path.basename(l.strip()) for l in open(a.file_list, encoding="utf-8")
              if l.strip() and not l.startswith("#")]
    have = {os.path.basename(f): f for f in glob.glob(os.path.join(str(DATA_DIR), "*.pkl"))}
    missing = [n for n in wanted if n not in have]
    if missing:
        raise SystemExit("--file-list: " + str(len(missing)) + " Eintraege fehlen in "
                         + str(DATA_DIR) + ", z.B. " + str(missing[:3]))
    if len(set(wanted)) != len(wanted):
        raise SystemExit("--file-list: doppelte Eintraege.")
    all_files = sorted(have[n] for n in wanted)

    val_files, train_files = [], all_files
    if a.val_frac > 0 and len(all_files) >= 10:
        if a.val_pool:
            pool = [f for f in all_files if re.search(a.val_pool, os.path.basename(f))]
            rest = [f for f in all_files if not re.search(a.val_pool, os.path.basename(f))]
            n_val = max(1, round(len(all_files) * a.val_frac))
            if len(pool) < n_val:
                raise SystemExit("Val-Pool trifft nur " + str(len(pool)) + " Dateien, gebraucht " + str(n_val))
            shuffled = pool[:]
            random.Random(SPLIT_SEED).shuffle(shuffled)
            val_files = sorted(shuffled[:n_val])
            train_files = sorted(shuffled[n_val:] + rest)
        else:
            shuffled = all_files[:]
            random.Random(SPLIT_SEED).shuffle(shuffled)
            n_val = max(1, round(len(shuffled) * a.val_frac))
            val_files = sorted(shuffled[:n_val])
            train_files = sorted(shuffled[n_val:])

    wk = corpus_dataset.window_cache_key(str(DATA_DIR), train_files,
                                         value_target_variant=a.value_target_variant,
                                         encoder=a.encoder, conjunction_head=a.conjunction_head)
    with open(a.train_list_out, "w", encoding="utf-8") as fh:
        fh.write("# Trainingsanteil von " + a.file_list + " (val_frac " + str(a.val_frac)
                 + ", val_pool " + repr(a.val_pool) + ", Split-Seed " + str(SPLIT_SEED) + ")\n")
        for f in train_files:
            fh.write(os.path.basename(f) + "\n")
    if a.val_list_out:
        with open(a.val_list_out, "w", encoding="utf-8") as fh:
            for f in val_files:
                fh.write(os.path.basename(f) + "\n")
    print("Fenster " + str(len(all_files)) + " Dateien, Val " + str(len(val_files))
          + ", Train " + str(len(train_files)))
    print("Fenster-Schluessel des Trainingsanteils: " + wk.key
          + "  -> Monolith als " + os.path.join(str(DATA_DIR), ".cache_" + wk.key + ".h5"))
    print("Trainingsliste: " + a.train_list_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
