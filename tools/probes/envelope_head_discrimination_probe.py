# -*- coding: utf-8 -*-
"""PREREG_geometric_envelope.md Stufe 0 -- weiss der Kopf die Huelle schon?

FRAGE (par.5, Stufe 0): laesst sich die Huellen-Zugehoerigkeit einer offenen
Kuppelzelle aus den vorhandenen Ownership-Ausgaben ABLESEN, je Runde
getrennt? Vorab festgelegte Lesart steht in par.5a der Prereg.

AUFBAU (netzfrei bis auf Vorwaertspaesse, kein Bau):
* Zustaende: `evaluations/frozen_eval_set_v3.pkl` (b01-Aera, 1.800 Zustaende,
  360 je Runde), Modelle als ONNX aus `models/`.
* Je Zustand und Spielerbrett: Belegung aus `dome_grid` (wie
  `triangle_hull_coverage_probe.occupancy`), Huellen-Orientierung =
  bestpassend am Brett (HULL_LEFT r+c<=5 oder HULL_RIGHT r<=c, kleinere
  Abweichung; bei leerem Brett BEIDE Orientierungen als moeglich, Zelle gilt
  als "innen", wenn sie in einer der beiden liegt).
* Ownership-Kopf: 36 Werte je Seite (slot-major `grid_index`, Seite 0 =
  Spieler am Zug), Sigmoid -> P(am Ende belegt).
* Diskriminierung: unter den OFFENEN Zellen eines Bretts die AUC von P(belegt)
  fuer "innen" gegen "aussen" (Mann-Whitney-Form, Ties halb), gemittelt je
  Runde ueber alle Bretter mit mindestens einer offenen Zelle je Klasse; dazu
  Mittelwert P(belegt) innen/aussen und Block-SE ueber die Quell-Dateien
  (`source_file` der frozen-Records).
"""
import argparse
import collections
import json
import math
import os
import pickle
import sys
import time

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "engine", "py"))
sys.path.insert(0, os.path.join(_ROOT, "tools", "probes"))
from neural_net import state_to_planes, state_to_tensor  # noqa: E402
from triangle_hull_coverage_probe import HULL_LEFT, HULL_RIGHT, occupancy, deviation  # noqa: E402


def grid_index(r, c):
    return (r // 2) * 12 + (c // 2) * 4 + (r % 2) * 2 + (c % 2)


def cell_exists(dome_grid, r, c):
    row = dome_grid[r // 2] if r // 2 < len(dome_grid) else []
    slot = row[c // 2] if c // 2 < len(row) else None
    return bool(slot)


def auc(pos, neg):
    """Mann-Whitney-AUC: P(score_innen > score_aussen), Ties halb."""
    if not pos or not neg:
        return None
    wins = 0.0
    for p in pos:
        for n in neg:
            wins += 1.0 if p > n else (0.5 if p == n else 0.0)
    return wins / (len(pos) * len(neg))


def mean_se(xs):
    if not xs:
        return None, None
    m = sum(xs) / len(xs)
    if len(xs) < 2:
        return m, None
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))
    return m, sd / math.sqrt(len(xs))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--frozen", default="evaluations/frozen_eval_set_v3.pkl")
    ap.add_argument("--models", nargs="+", default=["v23-b01_brierbest", "v22-b05", "v18_2d"])
    ap.add_argument("--out", default="evaluations/artifacts/envelope_head_discrimination.json")
    a = ap.parse_args()
    t0 = time.monotonic()
    import onnxruntime as ort

    with open(os.path.join(_ROOT, a.frozen), "rb") as fh:
        records = pickle.load(fh)["records"]
    print("frozen:", len(records), "Records", flush=True)

    result = {"prereg": "PREREG_geometric_envelope.md Stufe 0 (par.5, Lesart par.5a)",
              "frozen": a.frozen, "n_records": len(records), "modelle": {}}
    for m in a.models:
        path = os.path.join(_ROOT, "models", "alphazero_" + m + ".onnx")
        sess = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
        inputs = sess.get_inputs()
        want_planes = None
        for i in inputs:
            if len(i.shape) > 2:
                want_planes = i.shape[1] if isinstance(i.shape[1], int) else None
        want_flat = None
        for i in inputs:
            if len(i.shape) == 2:
                want_flat = i.shape[1] if isinstance(i.shape[1], int) else None
        per_round_auc = collections.defaultdict(list)       # round -> [auc je Brett]
        per_round_in = collections.defaultdict(list)
        per_round_out = collections.defaultdict(list)
        per_file_round_auc = collections.defaultdict(lambda: collections.defaultdict(list))
        orient_count = collections.defaultdict(collections.Counter)   # Runde -> Orientierung -> Bretter
        per_orient_auc = collections.defaultdict(list)                # (Runde, Orientierung) -> [auc]
        n_boards = collections.Counter()
        skipped_empty_side = 0
        for rec in records:
            st = rec["state"]
            rnd = int(st.get("round", 0))
            planes = np.asarray(state_to_planes(st), dtype=np.float32)[None, :]
            flat = np.asarray(state_to_tensor(st), dtype=np.float32)[None, :]
            if want_planes is not None and want_planes < planes.shape[1]:
                planes = planes[:, :want_planes]
            if want_flat is not None and want_flat < flat.shape[1]:
                flat = flat[:, :want_flat]
            feed = {}
            for i in inputs:
                feed[i.name] = planes if len(i.shape) > 2 else flat
            own = sess.run(None, feed)[4][0]
            p_own = 1.0 / (1.0 + np.exp(-np.asarray(own, dtype=np.float64)))
            cur = st.get("current_player", 0)
            for pi, player in enumerate(st["players"]):
                side = 0 if pi == cur else 1
                grid = player.get("dome_grid") or []
                filled = occupancy(grid)
                if filled:
                    dl, dr = deviation(filled, HULL_LEFT), deviation(filled, HULL_RIGHT)
                    hull = HULL_LEFT if dl <= dr else HULL_RIGHT
                    orient = "links" if dl < dr else ("rechts" if dr < dl else "gleich")
                    inside = hull
                else:
                    inside = HULL_LEFT | HULL_RIGHT
                    orient = "leer"
                orient_count[rnd][orient] += 1
                pos, neg = [], []
                for r in range(6):
                    for c in range(6):
                        if (r, c) in filled or not cell_exists(grid, r, c):
                            continue
                        p = float(p_own[36 * side + grid_index(r, c)])
                        (pos if (r, c) in inside else neg).append(p)
                if not pos or not neg:
                    skipped_empty_side += 1
                    continue
                val = auc(pos, neg)
                per_round_auc[rnd].append(val)
                per_orient_auc[(rnd, orient)].append(val)
                per_round_in[rnd].append(sum(pos) / len(pos))
                per_round_out[rnd].append(sum(neg) / len(neg))
                per_file_round_auc[rec.get("source_file", "?")][rnd].append(val)
                n_boards[rnd] += 1
        rounds = {}
        for rnd in sorted(per_round_auc):
            m_auc, _ = mean_se(per_round_auc[rnd])
            blocks = [sum(v[rnd]) / len(v[rnd]) for v in per_file_round_auc.values() if v.get(rnd)]
            _, se_blk = mean_se(blocks)
            rounds[str(rnd)] = {"n_bretter": n_boards[rnd], "auc_mittel": m_auc,
                                "auc_block_se": se_blk, "n_bloecke": len(blocks),
                                "p_belegt_innen": mean_se(per_round_in[rnd])[0],
                                "p_belegt_aussen": mean_se(per_round_out[rnd])[0],
                                "orientierung_bretter": dict(orient_count[rnd]),
                                "auc_je_orientierung": {o: mean_se(per_orient_auc[(rnd, o)])[0]
                                                        for o in ("links", "rechts", "gleich", "leer")
                                                        if per_orient_auc.get((rnd, o))}}
            print(f"  {m} R{rnd}: AUC {m_auc:.3f} (Block-SE {se_blk if se_blk is None else round(se_blk,3)}, {n_boards[rnd]} Bretter), P innen {rounds[str(rnd)]['p_belegt_innen']:.3f} aussen {rounds[str(rnd)]['p_belegt_aussen']:.3f} | Orientierung {dict(orient_count[rnd])} | AUC je Orientierung { {k: round(v,3) for k,v in rounds[str(rnd)]['auc_je_orientierung'].items()} }", flush=True)
        result["modelle"][m] = {"runden": rounds, "bretter_ohne_beide_klassen": skipped_empty_side,
                                "planes_kanaele_modell": want_planes, "flat_breite_modell": want_flat}
    result["laufzeit"] = {"wanduhr_s": round(time.monotonic() - t0, 1), "cpu_s": None,
                          "threads": 1, "s_je_partie": None}
    path = os.path.join(_ROOT, a.out)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
    print("Artefakt:", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
