# -*- coding: utf-8 -*-
"""Exportiert die "sauberen" Phase::Drafting-Zustaende eines eingefrorenen
Auswertungssatzes (`--set`) als JSON-Array -- Bruecke fuer Rust-seitige
Analysen, die `net_search_state_json`/den PyO3-Wheel NICHT anfassen wollen
(z.B. ein `cargo test`-Vergleich, der kein installiertes `mosaic_rust`-Modul
braucht). Pickle ist Python-spezifisch, Rust kann die `.pkl`-Datei nicht
direkt lesen -- dieses Skript ist die einzige Bruecke.

Filterlogik 1:1 aus `tools/build_frozen_oracle_labels.py::is_start_adjacent`/
`is_pending_rotation` uebernommen (NICHT neu erfunden) -- exakt dieselben
zwei Ausschlusskategorien, die auch `evaluations/oracle_v21_own02.json`
(`n_start_placement_adjacent_excluded`/`n_pending_dome_choice_excluded`)
ausweist. Bei `--set evaluations/frozen_eval_set_v2.pkl` muss die
verbleibende Zahl exakt `oracle_v21_own02.json::n_labeled` (1148) treffen --
das Skript druckt die Zahlen zur Gegenprobe, aendert aber nichts, wenn sie
nicht passen (der Aufrufer entscheidet).

Aufruf:
    python tools/export_frozen_drafting_states.py \
        --set evaluations/frozen_eval_set_v2.pkl \
        --out <ziel.json>
"""
from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def is_start_adjacent(rec: dict) -> bool:
    return any(not p["start_placed"] for p in rec["state"]["players"])


def is_pending_rotation(rec: dict) -> bool:
    types = set(a.get("type") for a in rec["valid_actions"])
    return types == {"choose_dome_rotation"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", default="evaluations/frozen_eval_set_v2.pkl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--expect-n", type=int, default=None, help="Gegenprobe-Zahl (z.B. 1148)")
    args = ap.parse_args()

    pkl_path = REPO / args.set
    with pkl_path.open("rb") as fh:
        frozen = pickle.load(fh)
    records = frozen["records"]
    print(f"{pkl_path}: {len(records)} Records (Version {frozen.get('version')})")

    n_non_drafting = 0
    n_start_adjacent = 0
    n_pending_rotation = 0
    eligible = []
    for idx, rec in enumerate(records):
        if rec["state"].get("phase") != "drafting":
            n_non_drafting += 1
            continue
        if is_start_adjacent(rec):
            n_start_adjacent += 1
            continue
        if is_pending_rotation(rec):
            n_pending_rotation += 1
            continue
        eligible.append((idx, rec))

    print(f"  non-drafting: {n_non_drafting}")
    print(f"  start-placement-angrenzend (ausgeschlossen): {n_start_adjacent}")
    print(f"  PendingDomeChoice-Zwischenzustaende (ausgeschlossen): {n_pending_rotation}")
    print(f"  verbleiben (sauber): {len(eligible)}")

    if args.expect_n is not None:
        status = "OK" if len(eligible) == args.expect_n else "ABWEICHUNG"
        print(f"  Gegenprobe gegen --expect-n={args.expect_n}: {status}")

    out_records = [
        {
            "record_index": idx,
            "round": rec["round"],
            "recorded_valid_actions_len": len(rec["valid_actions"]),
            "state": rec["state"],
        }
        for idx, rec in eligible
    ]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_records), encoding="utf-8")
    print(f"Geschrieben: {out_path} ({len(out_records)} Zustaende)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
