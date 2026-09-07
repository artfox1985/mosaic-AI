#!/usr/bin/env python
"""Verteilung der Aktionszahl je Runde und Zug-Index innerhalb der Runde.

Grundmenge: Records mit `phase == "drafting"`, OHNE die Eroeffnungsplatzierung
(erkennbar daran, dass der einzige Aktionstyp `dome` ist -- der Nutzer hat sie am
2026-09-07 ausdruecklich ausgenommen, siehe docs/domain_knowledge.md "OFFEN: Darf die
Eroeffnungsplatzierung blind vom Stapel ziehen?").
Einheit: `len(valid_actions)` je Entscheidung.

Liefert je Korpus-Gruppe: Median je (Runde, Index), Zerfallsrate lambda je Runde
(Regression auf log-Median) mit R2, und die Rundenmassen unter dem Huellen-Rundenprofil.

Aufruf:
    python -X utf8 -u tools/probes/action_count_profile_probe.py \
        --group v23-b01-policy "data/selfplay_v23-b01-policy_*.pkl" \
        --group hv2 "data/selfplay_hv2_*.pkl" --max-files 400 \
        --out evaluations/artifacts/action_count_profile.json
"""
import argparse
import collections
import glob
import json
import math
import statistics as st
import sys
import time

sys.path.insert(0, ".")
from corpus_io import load_records  # noqa: E402

PROFILE = [1.0, 0.92, 0.67, 0.33, 0.0]   # ENVELOPE_PROFILE_DEFAULT (envelope.rs:37)


def scan(pattern: str, max_files: int, label: str):
    files = sorted(glob.glob(pattern))[:max_files]
    cell = collections.defaultdict(list)
    run, last = collections.Counter(), {}
    games, n, skipped = set(), 0, 0
    t0 = time.time()
    for k, f in enumerate(files, 1):
        for r in load_records(f):
            s = r["state"]
            if s.get("phase") != "drafting":
                continue
            actions = r.get("valid_actions") or []
            if {a["type"] for a in actions} == {"dome"}:
                skipped += 1
                continue
            g, rd = r["game_id"], s["round"]
            games.add(g)
            if last.get(g) != rd:
                run[g] = 0
                last[g] = rd
            run[g] += 1
            cell[(rd, run[g])].append(len(actions))
            n += 1
        if k % 25 == 0 or k == len(files):
            print(f"   [{label}] {k}/{len(files)} Dateien, {n} Entscheide, "
                  f"{len(games)} Partien, {time.time()-t0:.0f}s", flush=True)
    return cell, n, len(games), skipped, len(files)


def fit(cell, min_n: int = 50):
    med = {k: st.median(v) for k, v in cell.items() if len(v) >= min_n}
    out = {"decay": [], "r2": [], "mass": [], "median_by_index": {}}
    masses = []
    for rd in (1, 2, 3, 4, 5):
        pts = [(i, m) for (r, i), m in sorted(med.items()) if r == rd and m >= 1]
        out["median_by_index"][rd] = [med.get((rd, i), 0.0) for i in range(1, 13)]
        if len(pts) < 5:
            out["decay"].append(0.0); out["r2"].append(0.0); masses.append(0.0)
            continue
        xs = [i for i, _ in pts]
        ys = [math.log(m) for _, m in pts]
        k = len(xs); mx = sum(xs) / k; my = sum(ys) / k
        lam = -sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
        a = my + lam * mx
        ss_tot = sum((y - my) ** 2 for y in ys)
        r2 = 1 - sum((y - (a - lam * x)) ** 2 for x, y in zip(xs, ys)) / ss_tot if ss_tot else 0.0
        out["decay"].append(lam); out["r2"].append(r2)
        masses.append(PROFILE[rd - 1] * sum(m for _, m in pts))
    tot = sum(masses) or 1.0
    out["mass"] = [m / tot for m in masses]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", nargs=2, action="append", metavar=("NAME", "GLOB"), required=True)
    ap.add_argument("--max-files", type=int, default=400)
    ap.add_argument("--out", default="evaluations/artifacts/action_count_profile.json")
    a = ap.parse_args()
    t0 = time.time()
    res = {}
    for name, pattern in a.group:
        print(f"== Gruppe {name}: {pattern}", flush=True)
        cell, n, games, skipped, nf = scan(pattern, a.max_files, name)
        f = fit(cell)
        f.update({"n_entscheide": n, "n_partien": games, "n_dateien": nf,
                  "eroeffnungen_ausgelassen": skipped})
        res[name] = f
        print(f"   -> {n} Entscheide, {games} Partien")
        print(f"      lambda  {' '.join(f'{x:.4f}' for x in f['decay'])}")
        print(f"      R2      {' '.join(f'{x:.3f}' for x in f['r2'])}")
        print(f"      Massen  {' '.join(f'{x:.3f}' for x in f['mass'])}", flush=True)
    res["laufzeit"] = {"wanduhr_s": round(time.time() - t0, 1), "cpu_s": None,
                       "threads": 1, "s_je_partie": None}
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, ensure_ascii=False)
    print(f"Artefakt: {a.out}")


if __name__ == "__main__":
    main()
