# -*- coding: utf-8 -*-
"""PREREG_heuristic_v2_long_rows.md par.3b.8 Stufe A -- Karten-Diagnose an
Vollendungs-Stellen.

Frage: WARUM traegt der Ownership-Tiling-Pol nicht? Drei vorregistrierte
Messungen an Zwischenzustaenden des hv2-Korpus, an denen eine Spalte >= 4/6
gefuellt ist ("Vollendungs-Stellen"):

1. ZEILENVERTEILUNG der fehlenden Spaltenzellen (Nutzer-Hypothese
   2026-08-29: ueberwiegend Rasterzeile 5/6 -- teuer, weil lange
   Musterreihen die Vorleistung sind).
2. KARTENWERTE p_own der fehlenden Zellen, b01- gegen b04-Karte, je Zeile;
   dazu KALIBRIERUNG gegen den echten Ausgang (der Korpus traegt das
   Endbrett: wurde die Zelle tatsaechlich noch gefuellt?).
3. FORM-LUECKE Summen- vs. Mengen-Marginale der fehlenden Zellen je Spalte
   (k1-Formel, Herleitung in par.3b.8): joint = 7*(1 - PROD p_fehlend),
   summe = 7*SUM_f [PROD_{g fehlend, g!=f} p_g * (1 - p_f)] -- beide OHNE
   den Faktor der bereits gefuellten Zellen (p=1).

Netz-Seite: onnxruntime auf den exportierten ONNX (Ausgabe-Index 4 =
ownership, Logits -> Sigmoid; Perspektive: [0:36] = Spieler am Zug,
[36:72] = Gegner, neural_net.py "erst der Spieler am Zug, dann der
Gegner"). Zellindex-Ordnung slot-major (scoring.rs::ownership_field_index),
Raster (r,c) -> Index (r//2)*12 + (c//2)*4 + (r%2)*2 + (c%2).

Aufruf (exklusiv, ~Minuten):
    python -X utf8 -u tools/probes/ownership_map_completion_sites_probe.py
Smoke: --limit 5
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import pathlib
import sys
import time

import numpy as np

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))

from corpus_io import load_records  # noqa: E402

ARTIFACT = _ROOT / "evaluations" / "artifacts" / "ownership_map_completion_sites.json"
PREREG = "PREREG_heuristic_v2_long_rows.md par.3b.8 Stufe A"
MODELS = {
    "b01": _ROOT / "models" / "alphazero_v22-b01_best.onnx",
    "b04": _ROOT / "models" / "alphazero_v22-b04_best.onnx",
}


def grid_index(r, c):
    return (r // 2) * 12 + (c // 2) * 4 + (r % 2) * 2 + (c % 2)


def occupancy_grid(dome_grid):
    """6x6-Belegung aus dome_grid, Abbildung wie build_grid/scoring.rs."""
    grid = [[0] * 6 for _ in range(6)]
    for sr in range(3):
        row = dome_grid[sr] if sr < len(dome_grid) else []
        for sc in range(3):
            slot = row[sc] if sc < len(row) else None
            spaces = (slot or {}).get("spaces", []) if slot else []
            for si in range(4):
                sp = spaces[si] if si < len(spaces) else None
                grid[sr * 2 + si // 2][sc * 2 + si % 2] = (
                    1 if (sp and sp.get("filled") is not None) else 0)
    return grid


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--limit", type=int, default=300,
                    help="Anzahl hv2-Dateien (Default 300, Muster par.3b.5)")
    ap.add_argument("--min-fill", type=int, default=4)
    args = ap.parse_args()
    t0 = time.time()

    import onnxruntime as ort
    from neural_net import state_to_planes, state_to_tensor
    sessions = {k: ort.InferenceSession(str(p), providers=["CPUExecutionProvider"])
                for k, p in MODELS.items()}

    files = sorted(glob.glob(str(_ROOT / "data" / "selfplay_hv2_*.pkl")))[:args.limit]
    # Je (Datei) sammeln, Block-SE auf Dateiebene (stehende Regel).
    per_file = []
    row_missing_hist = {r: 0 for r in range(6)}
    sites_total = 0
    t_report = time.time()
    for fi, f in enumerate(files):
        recs = load_records(f)
        # Endzustand je Partie fuer den echten Ausgang.
        finals = {}
        for rec in recs:
            if rec.get("winner") is not None:
                finals[rec["game_id"]] = rec
        stats = {"p_missing": {"b01": {r: [] for r in range(6)}, "b04": {r: [] for r in range(6)}},
                 "cal": {"b01": [], "b04": []},   # (p_own, tatsaechlich_gefuellt)
                 "gap": {"b01": [], "b04": []}}   # (summe, menge) je Stelle
        seen_site_keys = set()
        for rec in recs:
            st = rec.get("state") or {}
            if st.get("round") not in (2, 3, 4):
                continue
            gid = rec.get("game_id")
            fin = finals.get(gid)
            if fin is None:
                continue
            for pi, p in enumerate(st.get("players", [])):
                cf = (p.get("score_geo") or {}).get("col_fill") or []
                grid = None
                for col, fill in enumerate(cf):
                    if not (args.min_fill <= fill < 6):
                        continue
                    # EINE Messung je (Partie, Seite, Spalte, Fuellstand):
                    # sonst dominiert dieselbe Stellung ueber viele Zuege.
                    key = (gid, pi, col, fill)
                    if key in seen_site_keys:
                        continue
                    seen_site_keys.add(key)
                    if grid is None:
                        grid = occupancy_grid(p["dome_grid"])
                    missing = [r for r in range(6) if not grid[r][col]]
                    if not missing:
                        continue
                    sites_total += 1
                    for r in missing:
                        row_missing_hist[r] += 1
                    # Karten beider Modelle auf DIESEM Zustand.
                    planes = state_to_planes(st).numpy()[None].astype(np.float32)
                    flat = state_to_tensor(st).numpy()[None].astype(np.float32)
                    fin_grid = occupancy_grid(fin["state"]["players"][pi]["dome_grid"])
                    for mk, sess in sessions.items():
                        ins = {i.name: (planes if i.shape[-1] == 6 or len(i.shape) == 4 else flat)
                               for i in sess.get_inputs()}
                        own = sess.run(None, ins)[4][0]
                        base = 0 if pi == st.get("current_player") else 36
                        ps = {r: float(sigmoid(own[base + grid_index(r, col)]))
                              for r in missing}
                        for r, v in ps.items():
                            stats["p_missing"][mk][r].append(v)
                            stats["cal"][mk].append((v, fin_grid[r][col]))
                        vals = list(ps.values())
                        joint = 7.0 * (1.0 - math.prod(vals))
                        summe = 7.0 * sum(
                            math.prod(vals[:i] + vals[i + 1:]) * (1.0 - v)
                            for i, v in enumerate(vals))
                        stats["gap"][mk].append((summe, joint))
        per_file.append(stats)
        if time.time() - t_report > 15:
            print(f"  {fi + 1}/{len(files)} Dateien, {sites_total} Stellen "
                  f"({time.time() - t0:.0f}s)", flush=True)
            t_report = time.time()

    def agg(getter):
        vals = [v for s in per_file for v in getter(s)]
        return (sum(vals) / len(vals)) if vals else float("nan")

    result = {"prereg": PREREG, "dateien": len(files), "stellen": sites_total,
              "min_fill": args.min_fill,
              "zeilenverteilung_fehlende_zellen": row_missing_hist,
              "modelle": {}}
    for mk in MODELS:
        cal = [c for s in per_file for c in s["cal"][mk]]
        gaps = [g for s in per_file for g in s["gap"][mk]]
        result["modelle"][mk] = {
            "p_own_fehlend_je_zeile": {
                r: agg(lambda s, r=r: s["p_missing"][mk][r]) for r in range(6)},
            "kalibrierung": {
                "mittel_p": sum(c[0] for c in cal) / len(cal) if cal else None,
                "tatsaechliche_fuellrate": sum(c[1] for c in cal) / len(cal) if cal else None,
                "n_zellen": len(cal),
            },
            "form_luecke": {
                "summe_mittel": sum(g[0] for g in gaps) / len(gaps) if gaps else None,
                "menge_mittel": sum(g[1] for g in gaps) / len(gaps) if gaps else None,
                "verhaeltnis_summe_zu_menge":
                    (sum(g[0] for g in gaps) / sum(g[1] for g in gaps))
                    if gaps and sum(g[1] for g in gaps) else None,
            },
        }
    result["laufzeit"] = {"wanduhr_s": round(time.time() - t0, 1), "threads": 1}
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(result, indent=1, ensure_ascii=False),
                        encoding="utf-8", newline="\n")
    print(f"\nStellen: {sites_total} | Zeilenverteilung fehlender Zellen: "
          f"{row_missing_hist}", flush=True)
    for mk, m in result["modelle"].items():
        k = m["kalibrierung"]; fl = m["form_luecke"]
        print(f"{mk}: p_own je Zeile "
              f"{ {r: round(v, 3) for r, v in m['p_own_fehlend_je_zeile'].items()} } | "
              f"Kalibrierung p={k['mittel_p']:.3f} vs real={k['tatsaechliche_fuellrate']:.3f} | "
              f"Form Summe/Menge={fl['verhaeltnis_summe_zu_menge']:.3f}", flush=True)
    print(f"Artefakt: {ARTIFACT}", flush=True)


if __name__ == "__main__":
    main()
