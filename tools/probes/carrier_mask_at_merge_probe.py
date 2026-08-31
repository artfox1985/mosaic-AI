# -*- coding: utf-8 -*-
"""Abnahme des Traeger-Umbaus (2026-08-31): Maske beim FENSTERBAU statt im Block.

Vorher stand der aufgeloeste Traegerstatus im Datei-Cache-Schluessel, weil er
den Block-INHALT aenderte (`pol_w = 0` fuer Nicht-Traeger). Folge: jeder
Manifest-Wechsel entwertete den gesamten Blockbestand -- beim v23-Fenster rund
2.600 Bloecke, obwohl sich an den DATEN nichts aendert.

Seither ist der Block **traegeragnostisch** und die Maske wird beim
Zusammenfuegen angewandt (`build_cache_parallel.merge(..., mask_parts=...)`).
Diese Sonde nagelt die Invariante fest, ohne die der Umbau ein stiller
Datenfehler waere:

  A) **Gleichheit**: ein Fenster, das DIREKT mit Manifest gebaut wird, und ein
     Monolith aus agnostischen Bloecken plus Merge-Maske muessen in
     `policy_weights` UND `ranking_mask` elementweise uebereinstimmen.
  B) **Gegenprobe ohne Manifest**: beide Wege muessen auch dann gleich sein,
     und die Maske muss leer bleiben (Bestandsverhalten).
  C) **Wirksamkeit**: mit Manifest muessen sich die Gewichte gegenueber "ohne
     Manifest" UNTERSCHEIDEN -- sonst wuerde der Test auch bei einer
     wirkungslosen Maske gruen.
  D) **Schluessel-Stabilitaet**: der Datei-Schluessel darf sich zwischen "mit"
     und "ohne" Manifest NICHT unterscheiden. Das ist der ganze Zweck des
     Umbaus.

Aufruf (netzfrei, drei Korpusdateien, Sekunden):
    python -X utf8 -u tools/probes/carrier_mask_at_merge_probe.py
"""
import argparse
import glob
import json
import os
import pathlib
import shutil
import sys
import tempfile
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))
# `merge` liegt in tools/, nicht im Paketpfad -- wie in build_cache_incremental.
sys.path.insert(0, str(_ROOT / "tools"))

PREREG = "PREREG_cache_build_time.md (Hebel 4, Traeger-Umbau 2026-08-31)"
MANIFEST_NAME = "policy_carrier_manifest_probe.json"
FIELDS = ("policy_weights", "ranking_mask")


def _window_weights(data_dir, files, manifest):
    """Der WAHRHEITS-Weg: Fenster direkt bauen, Maske in der Bauschleife."""
    prev = os.environ.pop("MOSAIC_CARRIER_MANIFEST", None)
    try:
        if manifest:
            os.environ["MOSAIC_CARRIER_MANIFEST"] = manifest
        import corpus_dataset
        ds = corpus_dataset.MosaicDataset(data_dir, files=files, encoder="flat")
        return {"policy_weights": [float(x) for x in ds.policy_weights.reshape(-1).tolist()],
                "ranking_mask": [float(x) for x in ds.ranking_mask.reshape(-1).tolist()]}
    finally:
        os.environ.pop("MOSAIC_CARRIER_MANIFEST", None)
        if prev is not None:
            os.environ["MOSAIC_CARRIER_MANIFEST"] = prev


def _block_then_merge(data_dir, files, manifest, out_path):
    """Der NEUE Weg: agnostische Bloecke bauen, beim Zusammenfuegen maskieren."""
    import h5py
    import corpus_dataset
    import neural_net
    from build_cache_parallel import merge

    parts, mask_parts, keys = [], set(), {}
    carrier_set = carrier_prefixes = None
    if manifest:
        with open(os.path.join(data_dir, manifest), encoding="utf-8") as f:
            m = json.load(f)
        carrier_set = frozenset(m["policy_carrier_files"])
        carrier_prefixes = list(m["carrier_prefixes"]) if "carrier_prefixes" in m else None

    for f in files:
        b = os.path.basename(f)
        key = neural_net.per_file_cache_key(
            b, value_target_variant="default", encoder="flat", conjunction_head=False,
            bootstrap_native=not b.startswith(neural_net.LEGACY_STRETCHED_PREFIXES))
        keys[b] = key
        block = os.path.join(data_dir, f".filecache_{key}.h5")
        if not os.path.exists(block):
            corpus_dataset.MosaicDataset(data_dir, files=[f], encoder="flat",
                                         cache_path_override=block)
        parts.append(block)
        if carrier_set is not None and not corpus_dataset._is_policy_carrier(
                b, carrier_set, carrier_prefixes,
                b.startswith(neural_net.V20_CARRIER_SHORTCUT_PREFIXES)):
            mask_parts.add(block)

    merge(parts, out_path, mask_parts=mask_parts)
    with h5py.File(out_path, "r") as hf:
        got = {k: [float(x) for x in hf[k][()].reshape(-1).tolist()] for k in FIELDS}
    return got, keys, len(mask_parts)


def _cmp(label, a, b, findings, failures, want_equal=True):
    worst, n = 0.0, 0
    for k in FIELDS:
        for x, y in zip(a[k], b[k]):
            n += 1
            worst = max(worst, abs(x - y))
    equal = worst == 0.0
    ok = equal if want_equal else not equal
    findings[label] = {"verglichen": n, "groesste_differenz": worst, "gleich": equal, "ok": ok}
    print(f"  {'OK  ' if ok else 'ROT '} {label:44s} n={n:6d}  max|delta|={worst:.3e}", flush=True)
    if not ok:
        failures.append(label)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--n-files", type=int, default=3)
    args = ap.parse_args()
    t_wall, t_cpu = time.time(), time.process_time()

    src = sorted(glob.glob(str(_ROOT / "data" / "selfplay_hv2_*.pkl")))[:args.n_files]
    if len(src) < 2:
        print("ROT -- mindestens zwei data/selfplay_hv2_*.pkl noetig.", file=sys.stderr)
        return 1

    findings = {"prereg": PREREG, "quellen": [os.path.basename(f) for f in src]}
    failures = []

    with tempfile.TemporaryDirectory(prefix="carriermask_") as tmp:
        files = []
        for f in src:
            dst = os.path.join(tmp, os.path.basename(f))
            shutil.copyfile(f, dst)
            files.append(dst)
        files.sort()

        # Manifest: NUR die erste Datei traegt Policy.
        carrier_file = os.path.basename(files[0])
        with open(os.path.join(tmp, MANIFEST_NAME), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"policy_carrier_files": [carrier_file]}, f, ensure_ascii=False, indent=1)
        findings["carrier_file"] = carrier_file
        findings["non_carrier_files"] = [os.path.basename(x) for x in files[1:]]

        want_mf = _window_weights(tmp, files, MANIFEST_NAME)
        want_no = _window_weights(tmp, files, None)
        got_mf, keys_mf, n_masked = _block_then_merge(
            tmp, files, MANIFEST_NAME, os.path.join(tmp, "merged_mf.h5"))
        got_no, keys_no, n_masked_no = _block_then_merge(
            tmp, files, None, os.path.join(tmp, "merged_no.h5"))

        _cmp("A Merge-Maske == Fenster mit Manifest", got_mf, want_mf, findings, failures)
        _cmp("B ohne Manifest identisch", got_no, want_no, findings, failures)
        _cmp("C Maske wirkt (mit != ohne)", want_mf, want_no, findings, failures,
             want_equal=False)

        key_ok = keys_mf == keys_no
        findings["D schluessel-stabil"] = {"gleich": key_ok, "ok": key_ok,
                                           "beispiel": next(iter(keys_mf.values()))}
        print(f"  {'OK  ' if key_ok else 'ROT '} "
              f"{'D Datei-Schluessel unabhaengig vom Manifest':44s} "
              f"{len(keys_mf)} Dateien", flush=True)
        if not key_ok:
            failures.append("D schluessel-stabil")

        findings["maskierte_bloecke"] = {"mit_manifest": n_masked, "ohne": n_masked_no}
        if n_masked != len(files) - 1 or n_masked_no != 0:
            failures.append("Maskenzahl unerwartet")
            print(f"  ROT  Maskenzahl: {n_masked} (erwartet {len(files) - 1}) / "
                  f"{n_masked_no} (erwartet 0)", flush=True)
        else:
            print(f"  OK   {'Maskenzahl':44s} {n_masked} von {len(files)} Bloecken",
                  flush=True)

    findings["verdikt"] = "GRUEN" if not failures else "ROT"
    findings["versagt"] = failures
    findings["laufzeit"] = {"wanduhr_s": round(time.time() - t_wall, 2),
                            "cpu_s": round(time.process_time() - t_cpu, 2),
                            "threads": 1, "s_je_partie": None}
    target = _ROOT / "evaluations" / "artifacts" / "carrier_mask_at_merge_probe.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(findings, indent=2, ensure_ascii=False),
                      encoding="utf-8", newline="\n")
    print(f"\nArtefakt: {target}")
    if failures:
        print(f"\nROT -- {', '.join(failures)}", file=sys.stderr)
        return 1
    print("\nGRUEN -- die Maske am Merge liefert dasselbe wie die Maske im Block, "
          "und der Schluessel haengt nicht mehr am Manifest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
