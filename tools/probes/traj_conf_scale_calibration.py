# -*- coding: utf-8 -*-
"""Eichung der Skala s fuer den Konfidenz-Bootstrap (Arm v35-b15).

Vorregistriert in `evaluations/PREREG_v35_window.md` par.19.5: w = clip(Q-Abstand
bestes minus zweitbestes Kind / s, 0, 1) aus `root_child_q` des SPAETEREN Records;
s wird VOR dem Bau aus der Verteilung des Q-Abstands im b02-Fenster geeicht
(Median als Startwert).

Reine Datenauswertung: liest die Records der Fensterdateien, keine Netzbewertung,
kein Cache. Zwei Grundmengen, beide mit n, Grundmenge und Einheit im Artefakt
(CLAUDE.md, Regel 0 Zusatz 2):

- `support_drafting`: jede Drafting-Stuetzstelle (`state.phase == "drafting"`,
  `trajectory_bootstrap.is_support_record`) -- die Verteilung, nach der par.19.5
  woertlich fragt;
- `consumer_k<k>`: je VERBRAUCHENDEM Record (vollstaendige Partie, `scores` und
  `winner` vorhanden, `bootstrap_value` vorhanden -- dieselbe Menge, auf der die
  Bauschleife in `corpus_dataset.py` den Bootstrap einblendet) der Q-Abstand des
  spaeteren Records, den `trajectory_bootstrap_lookup_index` mit Obergrenze k
  findet. Das ist die Verteilung, die der Knopf tatsaechlich sieht: ein spaeterer
  Record zaehlt so oft, wie er als Bootstrap verbraucht wird.

Einheit beider Verteilungen: Differenz zweier completed-Q-Werte im Record-Raum
(Gewinnwahrscheinlichkeit des Ziehenden, [0,1]-Skala).

Nebenbei gezaehlt (Pruefstellen fuer Annahmen des Baus): Records mit `root_q`
ausserhalb der Drafting-Phase, Stuetzstellen ohne `root_child_q`, Stuetzstellen
mit weniger als zwei Kind-Eintraegen (je Runde), Spitzengleichstand (Abstand 0).

Aufruf (aus dem Repo-Wurzelverzeichnis):
    python -X utf8 -u tools/probes/traj_conf_scale_calibration.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))
sys.path.insert(0, str(REPO / "tools"))

from corpus_io import load_records  # noqa: E402
from runtime_block import laufzeit_block  # noqa: E402  # konvention-ok: Helfer-Name aus CLAUDE.md-Feld "laufzeit"
from trajectory_bootstrap import (  # noqa: E402
    is_support_record,
    root_child_q_gap,
    trajectory_bootstrap_lookup_index,
)

DEFAULT_FILE_LIST = "data/window_v35_b02.txt"
DEFAULT_OUT = "evaluations/artifacts/traj_conf_scale_calibration_v35_b02.json"
UNIT = "Differenz bestes minus zweitbestes completed-Q (Record-Raum, Gewinnwahrscheinlichkeit des Ziehenden, [0,1])"


def read_file_list(path) -> list:
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(os.path.basename(line))
    return out


def summarize(values) -> dict:
    """n, Quartile, Median, Mittel, Anteil exakt 0 einer Liste von Abstaenden."""
    if not values:
        return {"n": 0}
    arr = np.asarray(values, dtype=np.float64)
    q = np.percentile(arr, [5, 10, 25, 50, 75, 90, 95])
    return {
        "n": int(arr.size),
        "p05": float(q[0]), "p10": float(q[1]), "q1": float(q[2]), "median": float(q[3]),
        "q3": float(q[4]), "p90": float(q[5]), "p95": float(q[6]),
        "mean": float(arr.mean()), "min": float(arr.min()), "max": float(arr.max()),
        "share_exactly_zero": float((arr == 0.0).mean()),
    }


def scan_file(records, horizon, acc) -> None:
    """Zaehlt eine Datei in `acc` ein (beide Grundmengen und Nebenzaehlungen)."""
    positions_by_game: dict = {}
    for file_index, record in enumerate(records):
        positions_by_game.setdefault(record.get("game_id"), []).append(file_index)
        state = record.get("state") or {}
        phase = state.get("phase")
        rd = str(state.get("round"))
        if record.get("root_q") is not None and phase != "drafting":
            acc["root_q_outside_drafting"] += 1
        if phase != "drafting" or not is_support_record(record):
            continue
        acc["support_by_round"][rd] = acc["support_by_round"].get(rd, 0) + 1
        if record.get("root_child_q") is None:
            acc["support_without_root_child_q"] += 1
            continue
        gap = root_child_q_gap(record)
        if gap is None:
            acc["support_fewer_than_two_children_by_round"][rd] = \
                acc["support_fewer_than_two_children_by_round"].get(rd, 0) + 1
            continue
        acc["support_gaps"].append(gap)
    for positions in positions_by_game.values():
        game = [records[i] for i in positions]
        for game_index, record in enumerate(game):
            # Verbraucher-Menge wie corpus_dataset.py: vollstaendige Partie mit
            # Endstand, Record mit bootstrap_value.
            if record.get("completed", True) is False:
                continue
            if "scores" not in record or "winner" not in record:
                continue
            if record.get("bootstrap_value") is None:
                continue
            rd = str((record.get("state") or {}).get("round"))
            acc["consumer_by_round"][rd] = acc["consumer_by_round"].get(rd, 0) + 1
            later_index = trajectory_bootstrap_lookup_index(game, game_index, horizon)
            if later_index is None:
                acc["consumer_outcome_fallback"] += 1
                continue
            later = game[later_index]
            if later.get("root_child_q") is None:
                acc["consumer_later_without_root_child_q"] += 1
                continue
            gap = root_child_q_gap(later)
            if gap is None:
                lrd = str((later.get("state") or {}).get("round"))
                acc["consumer_later_fewer_than_two_children_by_later_round"][lrd] = \
                    acc["consumer_later_fewer_than_two_children_by_later_round"].get(lrd, 0) + 1
                continue
            acc["consumer_gaps"].append(gap)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file-list", default=DEFAULT_FILE_LIST)
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--horizon", type=int, default=1, help="Obergrenze k wie MOSAIC_BOOTSTRAP_HORIZON_ROUNDS (b15: 1)")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--limit", type=int, default=None, help="nur die ersten N Dateien (Rauchtest)")
    args = ap.parse_args(argv)

    t0, c0 = time.monotonic(), time.process_time()
    names = read_file_list(args.file_list)
    if args.limit:
        names = names[:args.limit]
    acc = {
        "support_gaps": [], "consumer_gaps": [],
        "support_by_round": {}, "support_fewer_than_two_children_by_round": {},
        "support_without_root_child_q": 0, "root_q_outside_drafting": 0,
        "consumer_by_round": {}, "consumer_outcome_fallback": 0,
        "consumer_later_without_root_child_q": 0,
        "consumer_later_fewer_than_two_children_by_later_round": {},
    }
    n_records = 0
    print(f"Eichung Konfidenz-Skala: {len(names)} Dateien aus {args.file_list}, Obergrenze k = {args.horizon}",
          flush=True)
    for i, name in enumerate(names, start=1):
        records = load_records(os.path.join(args.data_dir, name))
        n_records += len(records)
        scan_file(records, args.horizon, acc)
        if i % 50 == 0 or i == len(names):
            print(f"  {i}/{len(names)} Dateien, {n_records} Records, "
                  f"{len(acc['support_gaps'])} Stuetzstellen-Abstaende, "
                  f"{len(acc['consumer_gaps'])} Verbraucher-Abstaende, "
                  f"{time.monotonic() - t0:.1f} s", flush=True)

    support = summarize(acc["support_gaps"])
    consumer = summarize(acc["consumer_gaps"])
    recommended = float(f"{consumer['median']:.4g}") if consumer.get("n") else None
    out = {
        "prereg": "PREREG_v35_window.md par.19.5 (Arm v35-b15)",
        "file_list": args.file_list, "n_files": len(names), "n_records": n_records,
        "horizon_rounds": args.horizon,
        "unit": UNIT,
        "support_drafting": {
            "population": "Drafting-Records (state.phase == drafting) mit root_q und ohne dice_phase "
                          "(trajectory_bootstrap.is_support_record) und mindestens zwei root_child_q-Eintraegen",
            **support,
        },
        f"consumer_k{args.horizon}": {
            "population": "je verbrauchendem Record (completed, scores/winner, bootstrap_value vorhanden) "
                          f"der spaetere Record aus trajectory_bootstrap_lookup_index(k={args.horizon}) mit "
                          "mindestens zwei root_child_q-Eintraegen; ein spaeterer Record zaehlt so oft, wie "
                          "er verbraucht wird",
            **consumer,
        },
        "side_counts": {
            "support_by_round": acc["support_by_round"],
            "support_fewer_than_two_children_by_round": acc["support_fewer_than_two_children_by_round"],
            "support_without_root_child_q": acc["support_without_root_child_q"],
            "root_q_outside_drafting": acc["root_q_outside_drafting"],
            "consumer_by_round": acc["consumer_by_round"],
            "consumer_outcome_fallback": acc["consumer_outcome_fallback"],
            "consumer_later_without_root_child_q": acc["consumer_later_without_root_child_q"],
            "consumer_later_fewer_than_two_children_by_later_round":
                acc["consumer_later_fewer_than_two_children_by_later_round"],
        },
        "recommended_scale_s": recommended,
        "recommended_scale_basis": f"Median der Verbraucher-Verteilung consumer_k{args.horizon}, 4 signifikante Stellen",
        "laufzeit": laufzeit_block(t0, cpu_start=c0, threads=1, n_units=len(names), unit="datei"),
    }
    target = REPO / args.out
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"Stuetzstellen: n = {support.get('n')}, Q1 {support.get('q1')}, Median {support.get('median')}, "
          f"Q3 {support.get('q3')}", flush=True)
    print(f"Verbraucher k = {args.horizon}: n = {consumer.get('n')}, Q1 {consumer.get('q1')}, "
          f"Median {consumer.get('median')}, Q3 {consumer.get('q3')}", flush=True)
    print(f"Empfohlene Skala s = {recommended}; Artefakt {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
