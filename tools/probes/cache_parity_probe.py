# -*- coding: utf-8 -*-
"""Bit-Identitaet zweier Trainings-Caches (PREREG_cache_build_time.md par.4).

DAS TOR fuer alle Hebel jener Prereg: Parallelisierung, Rust-Export,
lzf-Abschaltung, Datei-Cache. Keiner von ihnen darf den Cache-INHALT aendern
-- ein schnellerer, aber anderer Cache entwertet jeden Vergleich mit
bestehenden Modellen und jede Messung, die auf ihnen aufbaut.

Bewusst VOR dem ersten Umbau geschrieben, damit die Abnahme nicht nachtraeglich
auf das Ergebnis zugeschnitten wird.

Verglichen wird FELD FUER FELD und BITGENAU, nicht mit Toleranz: die Felder
sind uint8-gepackt, int8 oder float16, Gleichheit ist exakt pruefbar. Eine
Toleranz waere hier kein Entgegenkommen, sondern das Aufgeben des Kriteriums.

Aufruf:
    python -X utf8 -u tools/probes/cache_parity_probe.py <cache_a.h5> <cache_b.h5> \
        [--out evaluations/artifacts/cache_parity_full_79.json] [--chunk-mb 64]

## Umbau 2026-08-28 fuer den VOLLEN Korpus (par.8: "wer den vollen Cache fuer
## eine Champion-Entscheidung benutzt, sollte die 2,58 h Referenz einmal fahren")

Drei Aenderungen, alle durch diesen Lauf erzwungen:

1. **Blockweises Lesen statt `np.array(hf[k])`.** Die Fassung der 120-Dateien-
   Abnahme hielt BEIDE Dateien vollstaendig im RAM. Beim vollen Korpus sind das
   je 11,77 GB Feldinhalt (par.8), also 23,5 GB fuer einen Vergleich, der
   nichts weiter tut als Bytes gegeneinander zu halten. Jetzt wandert je Feld
   ein Block von rund `--chunk-mb` durch den Speicher.
2. **Vergleich auf ROHBYTES** (`view(np.uint8)`) statt `np.array_equal` auf
   Werten. Fuer float16 waere `NaN != NaN` eine gemeldete Abweichung, obwohl
   die Bitmuster gleich sind -- ein Fehlalarm an einem Tor, das ueber das
   Weiterleben eines Hebels entscheidet. Umgekehrt sind `+0.0` und `-0.0`
   wertgleich, aber NICHT bitgleich; genau das soll dieses Tor sehen.
3. **h5-ATTRIBUTE werden mitverglichen.** Seit dem 2026-08-28 traegt ein Cache
   seinen Fenster-Schluessel als Datei-Attribut (`stamp_cache_key_attrs`,
   engine/py/corpus_dataset.py:462); Schluessel-GLEICHHEIT gehoert damit zum
   Tor. Unterschiedliche Werte bei beidseitig vorhandenem Attribut = FAIL.
   Ist nur EINE Datei gestempelt, ist das eine WARNUNG und kein FAIL: die
   Referenz kann aelter sein als der Stempel-Mechanismus, und ein Tor, das
   an Altbestand Fehlalarm schlaegt, wird umgangen statt beachtet.

Das `--out`-Artefakt heisst per Default NICHT mehr `cache_parity.json`: unter
dem festen Namen wuerde jeder neue Lauf die 120-Dateien-Abnahme vom 2026-08-26
ueberschreiben.

Die beiden Caches findet man als `.cache_<hash>.h5` im jeweiligen
MOSAIC_DATA_DIR. Fuer einen Hebel-Test also: einmal mit Bestandscode bauen,
Datei wegsichern, umbauen, neu bauen, beide vergleichen.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

import h5py
import numpy as np

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT / "tools"))

from runtime_block import laufzeit_block  # noqa: E402  (CLAUDE.md-Pflichtblock)

DEFAULT_OUT = "evaluations/artifacts/cache_parity_full_79.json"


def portable_path(path) -> str:
    """Pfad ohne Rechnerstruktur (CLAUDE.md: das Repo ist oeffentlich).

    Relativ zum Arbeitsverzeichnis, sonst relativ zur Repo-Wurzel, sonst nur
    der Dateiname -- ein Artefakt mit einem absoluten Nutzerpfad (Form Laufwerk:/Users/Name, hier bewusst nicht ausgeschrieben: der Waechter traefe sein eigenes Beispiel, Praezedenz pre-push 2026-08-27) darf nicht
    entstehen."""
    p = pathlib.Path(path)
    try:
        resolved = p.resolve()
    except OSError:
        return p.name
    for base in (pathlib.Path.cwd(), _ROOT):
        try:
            return resolved.relative_to(base.resolve()).as_posix()
        except ValueError:
            continue
    return resolved.name


def collect_datasets(hf) -> dict:
    """Alle Datasets der Datei, voll qualifiziert.

    Rekursiv statt `hf.keys()`: der heutige Cache ist flach, aber ein Feld,
    das jemand in eine Gruppe legt, duerfte nicht STILL aus dem Vergleich
    fallen -- ein Tor, das weniger prueft als es glaubt, ist schlimmer als
    keines."""
    found = {}

    def visit(name, obj):
        if isinstance(obj, h5py.Dataset):
            found[name] = obj

    hf.visititems(visit)
    return found


def attr_value(value):
    """h5-Attributwert in eine vergleichbare, JSON-faehige Form.

    h5py 3.x liefert Zeichenketten als `str`, aeltere Schreiber hinterlassen
    `bytes`; ein Vergleich, der an b"abc" != "abc" scheitert, waere ein
    Fehlalarm (dieselbe Ueberlegung wie in `verify_cache_file`)."""
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    if isinstance(value, np.ndarray):
        return [attr_value(v) for v in value.tolist()]
    if isinstance(value, np.generic):
        return attr_value(value.item())
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def compare_attrs(attrs_a, attrs_b, scope: str):
    """Attribut-Vergleich: beidseitig verschieden = FAIL, einseitig = WARNUNG.

    Begruendung der Asymmetrie steht im Modul-Docstring (Punkt 3)."""
    a = {k: attr_value(v) for k, v in dict(attrs_a).items()}
    b = {k: attr_value(v) for k, v in dict(attrs_b).items()}
    failures, warnings = [], []
    for key in sorted(set(a) | set(b)):
        in_a, in_b = key in a, key in b
        if in_a and in_b:
            if a[key] != b[key]:
                failures.append({"scope": scope, "attr": key,
                                 "a": portable_attr(a[key]), "b": portable_attr(b[key]),
                                 "reason": "beide Dateien tragen das Attribut mit "
                                           "verschiedenem Wert"})
        else:
            warnings.append({
                "scope": scope, "attr": key,
                "a": portable_attr(a[key]) if in_a else None,
                "b": portable_attr(b[key]) if in_b else None,
                "reason": "nur EINE Datei traegt das Attribut -- kein FAIL: der "
                          "Fenster-Schluessel-Stempel stammt vom 2026-08-28, aeltere "
                          "Referenz-Caches haben ihn nicht (nachruestbar mit "
                          "tools/stamp_cache_key.py)",
            })
    return failures, warnings


def portable_attr(value):
    """Attributwerte koennen Pfade enthalten -- dieselbe Regel wie oben."""
    if isinstance(value, str) and ("/" in value or "\\" in value):
        return portable_path(value)
    if isinstance(value, list):
        return [portable_attr(v) for v in value]
    return value


def rows_per_chunk(ds, chunk_bytes: int) -> int:
    row_items = int(np.prod(ds.shape[1:])) if ds.ndim > 1 else 1
    row_bytes = max(1, row_items * ds.dtype.itemsize)
    return max(1, chunk_bytes // row_bytes)


def compare_block(block_a, block_b, offset: int):
    """Bitgenauer Blockvergleich -> (n_differing_elements, first_index).

    Numerische dtypes werden als Rohbytes verglichen (Modul-Docstring, Punkt 2);
    fuer alles andere (Zeichenketten, Objekte) bleibt der elementweise
    Vergleich."""
    if block_a.dtype.kind in "biufc":
        flat_a = np.ascontiguousarray(block_a).reshape(-1)
        flat_b = np.ascontiguousarray(block_b).reshape(-1)
        raw_a, raw_b = flat_a.view(np.uint8), flat_b.view(np.uint8)
        neq_bytes = raw_a != raw_b
        if not neq_bytes.any():
            return 0, None
        itemsize = block_a.dtype.itemsize
        neq_elems = neq_bytes.reshape(-1, itemsize).any(axis=1)
        n_diff = int(neq_elems.sum())
        flat_idx = int(np.argmax(neq_elems))
    else:
        neq_elems = np.asarray(block_a != block_b).reshape(-1)
        if not neq_elems.any():
            return 0, None
        n_diff = int(neq_elems.sum())
        flat_idx = int(np.argmax(neq_elems))
    idx = list(np.unravel_index(flat_idx, block_a.shape)) if block_a.ndim else []
    if idx:
        idx[0] += offset
    return n_diff, tuple(int(v) for v in idx)


def compare_dataset(ds_a, ds_b, chunk_bytes: int, name: str) -> dict:
    """Ein Feld, blockweise. Gibt den Befundeintrag fuer das Artefakt zurueck."""
    result = {
        "field": name,
        "shape_a": list(ds_a.shape), "shape_b": list(ds_b.shape),
        "dtype_a": str(ds_a.dtype), "dtype_b": str(ds_b.dtype),
        "status": "OK", "detail": None,
        "n_differing": 0, "first_difference": None,
    }
    if ds_a.shape != ds_b.shape:
        result.update(status="FAIL",
                      detail=f"SHAPE {ds_a.shape} gegen {ds_b.shape}")
        return result
    if ds_a.dtype != ds_b.dtype:
        result.update(status="FAIL",
                      detail=f"DTYPE {ds_a.dtype} gegen {ds_b.dtype}")
        return result

    n_rows = ds_a.shape[0] if ds_a.ndim else 0
    if ds_a.ndim == 0 or n_rows == 0:
        block_a = np.atleast_1d(np.asarray(ds_a[()]))
        block_b = np.atleast_1d(np.asarray(ds_b[()]))
        n_diff, first = compare_block(block_a, block_b, 0)
        if n_diff:
            result.update(status="FAIL", n_differing=n_diff, first_difference=list(first or []),
                          detail=f"{n_diff} Werte abweichend, erste Stelle {first}")
        return result

    step = rows_per_chunk(ds_a, chunk_bytes)
    n_blocks = (n_rows + step - 1) // step
    n_diff_total, first = 0, None
    for block_i, start in enumerate(range(0, n_rows, step), start=1):
        stop = min(start + step, n_rows)
        block_a = ds_a[start:stop]
        block_b = ds_b[start:stop]
        n_diff, pos = compare_block(block_a, block_b, start)
        n_diff_total += n_diff
        if n_diff and first is None:
            first = pos
        del block_a, block_b
        if n_blocks > 1:
            print(f"      Block {block_i}/{n_blocks} ({stop}/{n_rows} Zeilen)"
                  f"{'' if n_diff_total == 0 else f'  -- bisher {n_diff_total} abweichend'}",
                  flush=True)
    if n_diff_total:
        result.update(status="FAIL", n_differing=n_diff_total,
                      first_difference=list(first or []),
                      detail=f"{n_diff_total} von {ds_a.size} Werten abweichend, "
                             f"erste Stelle {first}")
    return result


def compare_caches(path_a: str, path_b: str, chunk_bytes: int) -> dict:
    """Vollstaendiger Vergleich zweier Cache-Dateien."""
    with h5py.File(path_a, "r") as hf_a, h5py.File(path_b, "r") as hf_b:
        ds_a, ds_b = collect_datasets(hf_a), collect_datasets(hf_b)
        only_a = sorted(set(ds_a) - set(ds_b))
        only_b = sorted(set(ds_b) - set(ds_a))
        shared = sorted(set(ds_a) & set(ds_b))

        print(f"Felder: {len(ds_a)} / {len(ds_b)}, gemeinsam {len(shared)}", flush=True)
        if only_a:
            print(f"  NUR in A: {only_a}", flush=True)
        if only_b:
            print(f"  NUR in B: {only_b}", flush=True)

        attr_failures, attr_warnings = compare_attrs(hf_a.attrs, hf_b.attrs, "file")

        fields = []
        for i, name in enumerate(shared, start=1):
            print(f"[{i}/{len(shared)}] {name}  shape={ds_a[name].shape} "
                  f"dtype={ds_a[name].dtype}", flush=True)
            t_field = time.monotonic()
            entry = compare_dataset(ds_a[name], ds_b[name], chunk_bytes, name)
            f_fail, f_warn = compare_attrs(ds_a[name].attrs, ds_b[name].attrs,
                                           f"dataset:{name}")
            attr_failures.extend(f_fail)
            attr_warnings.extend(f_warn)
            if f_fail and entry["status"] == "OK":
                entry["status"] = "FAIL"
                entry["detail"] = "Feldattribute weichen ab (siehe attr_failures)"
            fields.append(entry)
            print(f"      -> {entry['status']}"
                  f"{'' if entry['detail'] is None else ': ' + entry['detail']}"
                  f"  ({time.monotonic() - t_field:.1f}s)", flush=True)

    failed = [f for f in fields if f["status"] != "OK"]
    verdict = "GRUEN" if not failed and not only_a and not only_b and not attr_failures \
        else "ROT"
    return {
        "fields": fields, "only_in_a": only_a, "only_in_b": only_b,
        "attr_failures": attr_failures, "attr_warnings": attr_warnings,
        "verdict": verdict, "n_fields_a": len(ds_a), "n_fields_b": len(ds_b),
        "n_fields_failed": len(failed),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cache_a", help="erste h5-Datei (Referenz)")
    ap.add_argument("cache_b", help="zweite h5-Datei (Kandidat)")
    ap.add_argument("--out", default=DEFAULT_OUT, help=f"Artefakt (Default {DEFAULT_OUT})")
    ap.add_argument("--chunk-mb", type=int, default=64,
                    help="Blockgroesse je Feld und Datei in MB (Default 64). Beide "
                         "Dateien vollstaendig zu laden waere beim vollen Korpus 23,5 GB.")
    args = ap.parse_args()

    t0, c0 = time.monotonic(), time.process_time()
    print(f"A: {portable_path(args.cache_a)}", flush=True)
    print(f"B: {portable_path(args.cache_b)}", flush=True)

    outcome = compare_caches(args.cache_a, args.cache_b, args.chunk_mb * 1024 * 1024)

    print("", flush=True)
    if outcome["verdict"] == "GRUEN":
        print(">>> GRUEN -- bit-identisch. Tor bestanden.", flush=True)
    else:
        print(f">>> ROT -- Tor NICHT bestanden "
              f"({len(outcome['only_in_a']) + len(outcome['only_in_b'])} Feld(er) einseitig, "
              f"{outcome['n_fields_failed']} Feld(er) abweichend, "
              f"{len(outcome['attr_failures'])} Attribut-Abweichung(en)):", flush=True)
        for name in outcome["only_in_a"]:
            print(f"    {name:24s} FEHLT in B", flush=True)
        for name in outcome["only_in_b"]:
            print(f"    {name:24s} FEHLT in A", flush=True)
        for f in outcome["fields"]:
            if f["status"] != "OK":
                print(f"    {f['field']:24s} {f['detail']}", flush=True)
        for a in outcome["attr_failures"]:
            print(f"    [{a['scope']}] {a['attr']}: {a['a']!r} gegen {a['b']!r}", flush=True)
    for w in outcome["attr_warnings"]:
        print(f"    WARNUNG [{w['scope']}] {w['attr']}: nur einseitig vorhanden "
              f"(A={w['a']!r}, B={w['b']!r})", flush=True)

    artifact = {
        "prereg": "PREREG_cache_build_time.md par.4 (Tor: Bit-Identitaet)",
        "cache_a": portable_path(args.cache_a),
        "cache_b": portable_path(args.cache_b),
        "chunk_mb": args.chunk_mb,
    }
    artifact.update(outcome)
    artifact["laufzeit"] = laufzeit_block(t0, cpu_start=c0, threads=1, n_games=None)

    target = pathlib.Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(5):
        try:
            target.write_text(json.dumps(artifact, indent=2, ensure_ascii=False),
                              encoding="utf-8", newline="\n")
            print(f"\nArtefakt: {portable_path(target)}  "
                  f"(Laufzeit {artifact['laufzeit']['wanduhr_s']}s)", flush=True)
            break
        except OSError as e:
            print("Retry:", e, flush=True)
            time.sleep(1)
    # Exit-Code traegt das Verdikt, damit der Aufrufer nicht parsen muss.
    return 0 if outcome["verdict"] == "GRUEN" else 1


if __name__ == "__main__":
    sys.exit(main())
