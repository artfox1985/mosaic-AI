# -*- coding: utf-8 -*-
"""Arena-Streuung fuer PREREG_geometric_envelope.md par.12b Punkt 3 (C1-Aufloesung).

Aus VORHANDENEN Artefakten, reine Arithmetik: je gepaartem Gating-Artefakt die
Block-Standardabweichung (Bloecke a 5 Paare in Seed-Reihenfolge) der gepaarten
Punktemarge (a_score - b_score je Paar, Blockmittel), je Spalten-Artefakt
(`arena_column_probe`) die Block-SD der vollen Spalten je Seite (Bloecke a 5
Partien). Gleiche Konfiguration = derselbe Aufbau (paired_gating @400, Deckel
200 Paare; Tor-2b-Arena 2 x 80 mit Seed 20261014). Die Spannweite dieser Block-SD
ueber die Artefakte ist die Aufloesung eines Streuungs-VERGLEICHS (par.12b:
"gemessen, nicht gesetzt").

Aufruf:  python -X utf8 tools/probes/arena_block_sd_probe.py --out evaluations/artifacts/arena_block_sd_par12b.json
"""
from __future__ import annotations

import argparse
import glob
import json
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ART = REPO / "evaluations" / "artifacts"


def block_sd(values: list[float], block: int = 5) -> dict:
    blocks = [values[i:i + block] for i in range(0, len(values) - len(values) % block, block)]
    means = [statistics.mean(b) for b in blocks]
    return {"n": len(values), "bloecke": len(means), "mittel": round(statistics.mean(values), 3) if values else None,
            "block_sd": round(statistics.stdev(means), 3) if len(means) > 1 else None,
            "se_mittel": round(statistics.stdev(means) / len(means) ** 0.5, 3) if len(means) > 1 else None}


def gating_rows() -> list[dict]:
    rows = []
    for f in sorted(glob.glob(str(ART / "paired_gating_result_*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        pps = d.get("per_pair_scores") or []
        if len(pps) < 10:
            continue
        diffs = [p["a_score"] - p["b_score"] for p in pps]
        wins = [float(p["a_wins_pair"]) for p in pps]
        rows.append({"artefakt": Path(f).name, "name_a": d.get("name_a"), "name_b": d.get("name_b"),
                     "spec_a": d.get("spec_a"), "spec_b": d.get("spec_b"), "seed": d.get("base_seed"),
                     "marge": block_sd(diffs), "paarsieg_a": block_sd(wins)})
    return rows


def column_rows() -> list[dict]:
    rows = []
    for f in sorted(glob.glob(str(ART / "columns_*_s14.json"))):
        d = json.load(open(f, encoding="utf-8"))
        for arm, a in (d.get("arme") or {}).items():
            games = a.get("je_partie") or []
            if len(games) < 10:
                continue
            per_side = {0: [], 1: []}
            for g in games:
                vs = g.get("volle_spalten") or [None, None]
                for pi in (0, 1):
                    if vs[pi] is not None:
                        per_side[pi].append(float(vs[pi]))
            rows.append({"artefakt": Path(f).name, "arm": arm, "n": len(games),
                         "spalten_seite0": block_sd(per_side[0]), "spalten_seite1": block_sd(per_side[1])})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    g = gating_rows(); c = column_rows()
    margin_sds = [r["marge"]["block_sd"] for r in g if r["marge"]["block_sd"] is not None]
    win_sds = [r["paarsieg_a"]["block_sd"] for r in g if r["paarsieg_a"]["block_sd"] is not None]
    col_sds = [r[k]["block_sd"] for r in c for k in ("spalten_seite0", "spalten_seite1") if r[k]["block_sd"] is not None]
    summary = {
        "gating_artefakte": len(g),
        "marge_block_sd_spannweite": [min(margin_sds), max(margin_sds)] if margin_sds else None,
        "marge_block_sd_median": round(statistics.median(margin_sds), 3) if margin_sds else None,
        "paarsieg_block_sd_spannweite": [min(win_sds), max(win_sds)] if win_sds else None,
        "spalten_artefakte_seiten": len(col_sds),
        "spalten_block_sd_spannweite": [min(col_sds), max(col_sds)] if col_sds else None,
        "spalten_block_sd_median": round(statistics.median(col_sds), 3) if col_sds else None,
        "verhaeltnis_max_min_spalten": round(max(col_sds) / min(col_sds), 2) if col_sds and min(col_sds) > 0 else None,
        "verhaeltnis_max_min_marge": round(max(margin_sds) / min(margin_sds), 2) if margin_sds and min(margin_sds) > 0 else None,
    }
    out = {"prereg": "PREREG_geometric_envelope.md par.12b Punkt 3", "blockgroesse": 5,
           "zusammenfassung": summary, "gating": g, "spalten": c}
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    for r in g:
        print(f"  {r['artefakt']}: Marge Block-SD {r['marge']['block_sd']} (Mittel {r['marge']['mittel']}, {r['marge']['bloecke']} Bloecke) | Paarsieg Block-SD {r['paarsieg_a']['block_sd']}")
    for r in c:
        print(f"  {r['artefakt']} Arm {r['arm']}: Spalten Block-SD Seite0 {r['spalten_seite0']['block_sd']} Seite1 {r['spalten_seite1']['block_sd']} ({r['n']} Partien)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
