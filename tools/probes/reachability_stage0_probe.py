# -*- coding: utf-8 -*-
"""PREREG_v23_reachability_recheck.md Stufe 0 (par.2/par.4) -- Karten-Diagnose.

FRAGE: untersagt der spaltenkompetente Ownership-Kopf Zellen, die das
Vorrats-Praedikat noch als vollendbar fuehrt? Messgroesse: Anteil der offenen
Zellen VOLLENDBARER Spalten, deren Kartenwert `p_own` unter der Schwelle liegt
("vom Kopf als tot kartiert").

ZWEI QUELLEN, KEIN NACHBAU:
  * Praedikat: `mosaic_rust.plate_completability_json(state, player)` liefert
    `columns[c]` (Spalte noch vollendbar) und `col_open_cells[c]`. Die Prereg
    verlangt ausdruecklich, die Pruefstelle nicht zu duplizieren; deshalb wird
    die SPALTEN-Aussage des Praedikats genommen und ueber ihre offenen Zellen
    gemittelt, statt `cell_is_completable` in Python nachzurechnen.
  * Karte: ONNX-Ausgabe-Index 4 (Ownership-Logits) -> Sigmoid, Zellindex
    slot-major wie in `ownership_map_completion_sites_probe.py`.

KALIBRIERUNG (par.4 Zusatz): fuer jede als tot kartierte Zelle wird am
Endzustand derselben Partie nachgesehen, ob sie TATSAECHLICH noch gefuellt
wurde. Das trennt "der Kopf irrt" von "der Kopf hat recht, das Praedikat ist
zu grosszuegig".
"""
import argparse
import glob
import json
import os
import sys
import time

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "engine", "py"))

from corpus_io import load_records  # noqa: E402

THRESHOLDS = (0.05, 0.10, 0.20)
PRIMARY = 0.10


def grid_index(r, c):
    """slot-major, identisch zu ownership_map_completion_sites_probe.grid_index."""
    return (r // 2) * 12 + (c // 2) * 4 + (r % 2) * 2 + (c % 2)


def filled_at_end(final_state, pi, r, c):
    """War Zelle (r,c) im Endzustand gefuellt?"""
    grid = final_state["players"][pi]["dome_grid"]
    tile = grid[r // 2][c // 2]
    if not tile:
        return False
    si = (r % 2) * 2 + (c % 2)
    return tile["spaces"][si].get("filled") is not None


def mean_se(xs):
    if not xs:
        return None, None
    mean = sum(xs) / len(xs)
    if len(xs) < 2:
        return mean, None
    sd = (sum((x - mean) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5
    return mean, sd / (len(xs) ** 0.5)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pattern", default="archive_pre_v24/selfplay_frozenv3-b01_*.pkl")
    ap.add_argument("--n-states", type=int, default=300)
    ap.add_argument("--models", nargs="+", default=["v23-b01_brierbest", "v22-b05"])
    ap.add_argument("--runden", nargs="+", type=int, default=[2, 3, 4])
    ap.add_argument("--per-file", dest="per_file_max", type=int, default=8,
                    help="Hoechstzahl Zustaende JE DATEI -- ohne das kaeme die ganze "
                         "Stichprobe aus der ersten Datei und die Block-SE, die die "
                         "Prereg verlangt, waere nicht berechenbar (Fehler im Erstlauf "
                         "2026-09-01: n_dateien=1).")
    ap.add_argument("--out", default="evaluations/artifacts/reachability_stage0.json")
    a = ap.parse_args()

    import mosaic_rust as mr
    import onnxruntime as ort
    from neural_net import state_to_planes, state_to_tensor

    sess = {m: ort.InferenceSession(os.path.join(_ROOT, "models", "alphazero_" + m + ".onnx"),
                                    providers=["CPUExecutionProvider"]) for m in a.models}
    t0 = time.monotonic()
    files = sorted(glob.glob(os.path.join(_ROOT, "data", a.pattern)))
    if not files:
        # Lauter Abbruch statt stiller Null-Messung: am 2026-09-01 lief die
        # Sonde gegen ein inzwischen ARCHIVIERTES Korpusverzeichnis und
        # druckte `None` statt zu scheitern -- eine leere Messung, die wie ein
        # Ergebnis aussieht, ist schlimmer als ein Fehler.
        raise SystemExit("Kein Korpus gefunden fuer Muster data/" + a.pattern
                         + " -- Pfad pruefen (Daten archiviert?).")
    per_file_shares = {m: [] for m in a.models}
    curve = {m: {s: [] for s in THRESHOLDS} for m in a.models}
    calib = {m: {"tot_und_doch_gefuellt": 0, "tot_gesamt": 0} for m in a.models}
    n_cells = 0
    n_states_done = 0

    for f in files:
        if n_states_done >= a.n_states:
            break
        recs = load_records(f)
        finals = {r["game_id"]: r for r in recs if r.get("winner") is not None}
        file_counter = {m: [0, 0] for m in a.models}
        in_this_file = 0
        for rec in recs:
            if n_states_done >= a.n_states or in_this_file >= a.per_file_max:
                break
            st = rec.get("state") or {}
            if st.get("round") not in a.runden:
                continue
            fin = finals.get(rec.get("game_id"))
            if fin is None:
                continue
            sj = json.dumps(st)
            planes = np.asarray(state_to_planes(st), dtype=np.float32)[None, :]
            flat = np.asarray(state_to_tensor(st), dtype=np.float32)[None, :]
            pred_by_player = {pi: json.loads(mr.plate_completability_json(sj, pi)) for pi in range(2)}
            n_states_done += 1
            in_this_file += 1
            for m in a.models:
                net = sess[m]
                eingaben = {}
                for i in net.get_inputs():
                    eingaben[i.name] = planes if len(i.shape) > 2 else flat
                own = net.run(None, eingaben)[4][0]
                p_own_all = 1.0 / (1.0 + np.exp(-np.asarray(own, dtype=np.float64)))
                for pi in range(2):
                    pred = pred_by_player[pi]
                    side = 0 if pi == st.get("current_player", 0) else 1
                    for col, open_cells in enumerate(pred["col_open_cells"]):
                        if not pred["columns"][col]:
                            continue
                        for cell in open_cells:
                            r = cell["r"]
                            p = float(p_own_all[36 * side + grid_index(r, col)])
                            n_cells += 1
                            for s in THRESHOLDS:
                                curve[m][s].append(1.0 if p < s else 0.0)
                            file_counter[m][1] += 1
                            if p < PRIMARY:
                                file_counter[m][0] += 1
                                calib[m]["tot_gesamt"] += 1
                                if filled_at_end(fin["state"], pi, r, col):
                                    calib[m]["tot_und_doch_gefuellt"] += 1
        for m in a.models:
            tot, ges = file_counter[m]
            if ges:
                per_file_shares[m].append(tot / ges)

    result = {"prereg": "PREREG_v23_reachability_recheck.md Stufe 0 (par.2/par.4)",
                "pattern": a.pattern, "n_states_done": n_states_done, "n_cells": n_cells,
                "runden": a.runden, "schwelle_primaer": PRIMARY, "arme": {}}
    for m in a.models:
        mean, se = mean_se(per_file_shares[m])
        k = calib[m]
        result["arme"][m] = {
            "anteil_tot_kartiert": mean,
            "block_se": se,
            "n_dateien": len(per_file_shares[m]),
            "curve": {str(s): (sum(curve[m][s]) / len(curve[m][s]) if curve[m][s] else None)
                      for s in THRESHOLDS},
            "kalibrierung": {
                "tot_gesamt": k["tot_gesamt"],
                "tot_und_doch_gefuellt": k["tot_und_doch_gefuellt"],
                "anteil_doch_gefuellt": (k["tot_und_doch_gefuellt"] / k["tot_gesamt"]) if k["tot_gesamt"] else None,
            },
        }
    result["laufzeit"] = {"wanduhr_s": round(time.monotonic() - t0, 1), "cpu_s": None,
                            "threads": 1, "s_je_partie": None}
    target_path = os.path.join(_ROOT, a.out)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
    for m in a.models:
        e = result["arme"][m]
        print(m + ": tot-kartiert " + str(round(e["anteil_tot_kartiert"], 4))
              + " (Block-SE " + str(e["block_se"]) + ") | Kurve " + str(e["curve"])
              + " | davon doch gefuellt " + str(e["kalibrierung"]["anteil_doch_gefuellt"]), flush=True)
    print("Zustaende " + str(n_states_done) + ", Zellen " + str(n_cells) + ", Artefakt: " + target_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
