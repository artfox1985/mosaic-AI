# -*- coding: utf-8 -*-
"""Kopie eines Exploiter-Korpus mit den Records NUR einer Netz-Seite.

PREREG_asymmetric_selfplay.md par.7 und Bauplan evaluations/exploiter_build_plan.md
D3: die Zyklus-Partien schreiben Records BEIDER Seiten (`--record-sides both`),
trainiert wird E_k aber nur auf den Records der Gegner-Netz-Seite
(`net_label == "opponent"`). Die Datenschicht (engine/py/corpus_dataset.py) filtert
nicht nach Feldern; ein Filterknopf dort muesste in beide Cache-Schluessel. Darum
eine Kopie: gleiche Basenames, nur die gewaehlte Seite, in einem eigenen Ordner,
dazu eine Dateiliste fuer `train.py --file-list`.

Harte Fehler statt stiller Luecken: eine Datei ohne passende Records, ein Record
ohne `net_label` oder eine schon vorhandene Zieldatei brechen ab.

Aufruf:
    python -X utf8 tools/split_records_by_net_label.py --data-dir data/exploiter \\
        --pattern 'selfplay_x35-e00-cycle_*.pkl' --net-label opponent \\
        --out-dir data/exploiter/train_x35-e01
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from corpus_io import corpus_files, dump_records, load_records  # noqa: E402
from runtime_block import laufzeit_block  # noqa: E402

NET_LABELS = ("primary", "opponent")


def split_records(records: list, net_label: str) -> list:
    """Records mit `net_label == net_label`. Ein Record ohne das Feld ist ein Fehler:
    die Datei stammt dann nicht aus einem Exploiter-Lauf."""
    out = []
    for r in records:
        label = r.get("net_label")
        if label not in NET_LABELS:
            raise ValueError(f"Record ohne gueltiges net_label ({label!r}), game_id={r.get('game_id')!r}")
        if label == net_label:
            out.append(r)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--pattern", required=True, help="Glob innerhalb von --data-dir")
    ap.add_argument("--net-label", required=True, choices=NET_LABELS)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--list-name", default="files.txt", help="Dateiliste im --out-dir")
    args = ap.parse_args(argv)

    t0, c0 = time.monotonic(), time.process_time()
    files = corpus_files(args.data_dir, args.pattern)
    if not files:
        raise SystemExit(f"❌ keine Dateien {args.pattern!r} in {args.data_dir}")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    names, n_in, n_out, games = [], 0, 0, set()
    for i, f in enumerate(files, 1):
        name = os.path.basename(f)
        target = out_dir / name
        if target.exists():
            raise SystemExit(f"❌ {target} liegt schon -- Abbruch statt Ueberschreiben")
        recs = load_records(f)
        kept = split_records(recs, args.net_label)
        if not kept:
            raise SystemExit(f"❌ {name}: kein Record mit net_label={args.net_label}")
        dump_records(target, kept)
        names.append(name)
        n_in += len(recs)
        n_out += len(kept)
        games.update(r.get("game_id") for r in kept)
        print(f"  [{i}/{len(files)}] {name}: {len(kept)} von {len(recs)} Records", flush=True)
    list_path = out_dir / args.list_name
    with open(list_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(f"# {args.net_label}-Seite aus {args.data_dir}/{args.pattern} "
                 f"(tools/split_records_by_net_label.py)\n")
        fh.write("\n".join(names) + "\n")
    summary = {"files": len(names), "records_in": n_in, "records_out": n_out, "games": len(games),
               "net_label": args.net_label, "list": str(list_path),
               "laufzeit": laufzeit_block(t0, cpu_start=c0, threads=1, n_units=len(names), unit="datei")}
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
