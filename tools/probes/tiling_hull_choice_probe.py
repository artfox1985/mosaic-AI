# -*- coding: utf-8 -*-
"""Tiling-Wahlfreiheit und Huellen-Konflikt (PREREG_geometric_envelope.md par.8.10,
2026-09-05, Nutzer: "Huelle nur im Drafting hat keinen Sinn").

Frage: Wie viele unterschiedliche Rundenabschluesse hat der Tiling-Loeser in
den Tiling-Zustaenden eines Korpus, wie oft weicht der HUELLENBESTE Abschluss
vom PUNKTBESTEN ab, was kostet er an Punkten, und liegt er ueberhaupt unter den
zwoelf punktbesten (dem Kandidatensatz des gemessenen W_TILE-Zweigs,
tiling_solver.rs::best_first_step_envelope_valued)?

Quelle: Tiling-Zustaende (`state.phase == "tiling"`) aus Korpusdateien, je
(Partie, Runde, Spieler) der ERSTE Zustand; Kandidaten ueber
`mosaic_rust.tiling_candidates_json` (= tiling_solver::top_k_tilings, Punkte
und Endzustand je Abschluss). H wie in triangle_hull_coverage_probe.py
(kosten-gewichteter Fuellanteil der bestpassenden Huelle minus Steine
ausserhalb, /56); volle Spalten aus der Brettgeometrie.

Aufruf:
    python -X utf8 -u tools/probes/tiling_hull_choice_probe.py \\
        --pattern "selfplay_v23-b01-value-argmax_*.pkl" --limit-files 2 --k 64
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools", "probes"))
from corpus_io import load_records  # noqa: E402
from triangle_hull_coverage_probe import occupancy, best_hull, row_weight  # noqa: E402

HULL_TOTAL = 56.0


def hull_score(dome_grid) -> float:
    cells = occupancy(dome_grid)
    if not cells:
        return 0.0
    hull = best_hull(cells)
    inside = sum(row_weight(c) for c in cells & hull) / HULL_TOTAL
    outside = sum(row_weight(c) for c in cells - hull) / HULL_TOTAL
    return inside - outside


def col_fill(dome_grid) -> list[int]:
    fill = [0] * 6
    for sr in range(3):
        row = dome_grid[sr] if sr < len(dome_grid) else []
        for sc in range(3):
            slot = row[sc] if sc < len(row) else None
            spaces = (slot or {}).get("spaces", []) if slot else []
            for si in range(4):
                sp = spaces[si] if si < len(spaces) else None
                if sp and sp.get("filled") is not None:
                    fill[sc * 2 + si % 2] += 1
    return fill


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--pattern", required=True)
    ap.add_argument("--limit-files", type=int, default=2)
    ap.add_argument("--k", type=int, default=64, help="Kandidatendeckel je Zustand (top_k_tilings)")
    ap.add_argument("--out", default="evaluations/artifacts/tiling_hull_choice_probe.json")
    a = ap.parse_args()

    import mosaic_rust as mr

    files = sorted(glob.glob(os.path.join(a.data_dir, a.pattern)))[: a.limit_files]
    if not files:
        raise SystemExit(f"keine Dateien fuer {a.pattern}")
    t0 = time.time()
    seen = set()
    states = []
    for f in files:
        for r in load_records(f):
            st = r["state"]
            if st.get("phase") != "tiling":
                continue
            key = (r["game_id"], st.get("round"), st.get("current_player"))
            if key in seen:
                continue
            seen.add(key)
            states.append((key, st))
    print(f"{len(files)} Dateien, {len(states)} Tiling-Zustaende (erster je Partie/Runde/Spieler)", flush=True)

    n_cands = Counter()
    per_round = defaultdict(lambda: {"states": 0, "choice": 0, "hull_differs": 0, "hull_outside_top12": 0,
                                     "col_differs": 0, "gap_pts": [], "gain_h": [], "gain_cols": []})
    rows = []
    for i, ((gid, rd, pi), st) in enumerate(states):
        cands = json.loads(mr.tiling_candidates_json(json.dumps(st), pi, a.k, 0))
        n = len(cands)
        n_cands[min(n, 20)] += 1
        pr = per_round[rd]
        pr["states"] += 1
        if n == 0:
            continue
        before_h = hull_score(st["players"][pi]["dome_grid"])
        before_cols = sum(1 for x in col_fill(st["players"][pi]["dome_grid"]) if x >= 6)
        scored = []
        for j, c in enumerate(cands):
            g = c["state"]["players"][pi]["dome_grid"]
            scored.append({"rank_pts": j, "points": c["points"], "h": hull_score(g),
                           "cols": sum(1 for x in col_fill(g) if x >= 6), "colsum": sum(col_fill(g))})
        best_pts = scored[0]  # top_k_tilings sortiert nach Punkten absteigend
        best_h = max(scored, key=lambda s: (s["h"], s["points"]))
        best_c = max(scored, key=lambda s: (s["colsum"], s["points"]))
        if n >= 2:
            pr["choice"] += 1
        if best_h["h"] > best_pts["h"] + 1e-9:
            pr["hull_differs"] += 1
            pr["gap_pts"].append(best_pts["points"] - best_h["points"])
            pr["gain_h"].append(best_h["h"] - best_pts["h"])
            if best_h["rank_pts"] >= 12:
                pr["hull_outside_top12"] += 1
        if best_c["colsum"] > best_pts["colsum"]:
            pr["col_differs"] += 1
            pr["gain_cols"].append(best_c["colsum"] - best_pts["colsum"])
        rows.append({"game_id": gid, "round": rd, "player": pi, "n_cands": n,
                     "pts_best": best_pts, "hull_best": best_h, "col_best": best_c,
                     "h_before": before_h, "cols_before": before_cols})
        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{len(states)} Zustaende ({time.time() - t0:.0f}s)", flush=True)

    def mean(xs):
        return sum(xs) / len(xs) if xs else None

    summary = {}
    for rd in sorted(per_round):
        p = per_round[rd]
        summary[str(rd)] = {
            "zustaende": p["states"], "mit_wahl": p["choice"],
            "huellenbester_weicht_ab": p["hull_differs"],
            "davon_ausserhalb_top12": p["hull_outside_top12"],
            "punktkosten_mittel": mean(p["gap_pts"]), "punktkosten_max": max(p["gap_pts"]) if p["gap_pts"] else None,
            "huellengewinn_mittel_kosteneinheiten": (mean(p["gain_h"]) or 0) * HULL_TOTAL if p["gain_h"] else None,
            "spaltenbester_weicht_ab": p["col_differs"], "spaltengewinn_mittel": mean(p["gain_cols"]),
        }
    wall = time.time() - t0
    out = {
        "prereg": "PREREG_geometric_envelope.md par.8.10",
        "quelle": {"pattern": a.pattern, "dateien": files, "zustaende": len(states), "k": a.k},
        "kandidaten_verteilung": {str(k): v for k, v in sorted(n_cands.items())},
        "je_runde": summary,
        "laufzeit": {"wanduhr_s": round(wall, 1), "cpu_s": round(time.process_time(), 1), "threads": 1,
                     "s_je_zustand": round(wall / max(1, len(states)), 3)},
        "zustaende": rows,
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("Kandidaten je Zustand (Anzahl -> Zustaende, 20 = >=20):", dict(sorted(n_cands.items())))
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print(f"Artefakt: {a.out} ({wall:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
