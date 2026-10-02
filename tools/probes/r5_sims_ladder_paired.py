# -*- coding: utf-8 -*-
"""tools/probes/r5_sims_ladder_paired.py -- Sim-Leiter der Netzsuche in Runde 5, Instrument 1
(PREREG_r5_net_vs_solver.md par.5b, Stufe 2S).

Die Stufen sind Self-Play-Laeufe mit demselben Seed, die sich NUR in den Sims der Netzsuche in Runde 5
unterscheiden. Bis zum ersten Runde-5-Record sind die Partien darum identisch (geprueft und berichtet);
alle Unterschiede entstehen in Runde 5. Je Stufe gegen die naechsthoehere, gepaart je Partie (beide
Seiten summiert, 95-%-Intervall ueber Partien): eigene Punkte, groesste Strafleiste in Runde 5, volle
Spalten, volle Reihen; dazu die Wanduhr je Partie aus dem Lauf-Manifest.

    python -X utf8 -u tools/probes/r5_sims_ladder_paired.py --data-dir data/probe_r5sims \
        --stages 100 200 400 800 --out evaluations/artifacts/r5_sims_ladder_v34-b01.json
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import re
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "tools"))
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

from corpus_io import load_records  # noqa: E402
from runtime_block import laufzeit_block  # noqa: E402

KEY = re.compile(r"(c\d+_g\d+)$")


def load_stage(data_dir: Path, n: int) -> dict:
    games: dict[str, list] = {}
    for f in sorted(glob.glob(str(data_dir / f"selfplay_r5sims-{n}_*.pkl"))):
        for r in load_records(f):
            m = KEY.search(str(r.get("game_id")))
            if m:
                games.setdefault(m.group(1), []).append(r)
    return games


def first_r5_players(recs):
    for r in recs:
        st = r.get("state") or {}
        if st.get("round") == 5:
            return json.dumps(st.get("players"), sort_keys=True)
    return None


def final(recs):
    for r in reversed(recs):
        if r.get("winner") is not None:
            return r
    return None


def per_game(recs):
    """Je Partie die Summe beider Seiten: Punkte, groesste R5-Strafleiste, volle Spalten/Reihen."""
    f = final(recs)
    if f is None or f.get("completed") is False:
        return None
    sc = f.get("scores") or [p["score"] for p in f["state"]["players"]]
    out = {"punkte": 0.0, "strafleiste_r5": 0.0, "volle_spalten": 0.0, "volle_reihen": 0.0}
    for pi in (0, 1):
        p = f["state"]["players"][pi]
        g = p.get("score_geo") or {}
        out["punkte"] += sc[pi]
        out["volle_spalten"] += sum(x >= 6 for x in (g.get("col_fill") or []))
        out["volle_reihen"] += sum(x >= 6 for x in (g.get("row_fill") or []))
        out["strafleiste_r5"] += max((len(((r.get("state") or {}).get("players") or [{}, {}])[pi].get("floor") or [])
                                      for r in recs if (r.get("state") or {}).get("round") == 5), default=0)
    return out


def compare(lo: dict, hi: dict) -> dict:
    keys = sorted(set(lo) & set(hi))
    same = sum(1 for k in keys if first_r5_players(lo[k]) == first_r5_players(hi[k]))
    res = {"partien_gepaart": len(keys), "identisch_bis_runde5": same}
    for name in ("punkte", "strafleiste_r5", "volle_spalten", "volle_reihen"):
        d = []
        for k in keys:
            a, b = per_game(lo[k]), per_game(hi[k])
            if a is not None and b is not None:
                d.append(b[name] - a[name])
        n = len(d)
        m = sum(d) / n if n else float("nan")
        sd = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1)) if n > 1 else float("nan")
        se = sd / math.sqrt(n) if n > 1 else float("nan")
        res[name] = {"n": n, "hoeher_minus_niedriger_je_partie": m,
                     "ci95": [m - 1.96 * se, m + 1.96 * se] if se == se else None,
                     "z": (m / se) if se and se == se else None,
                     "je_seite": m / 2 if n else None}
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--stages", nargs="+", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    t0, c0 = time.monotonic(), time.process_time()
    d = BASE_DIR / args.data_dir
    stages = {n: load_stage(d, n) for n in args.stages}
    out = {"prereg": "evaluations/PREREG_r5_net_vs_solver.md par.5b (2S, Instrument 1)",
           "grundmenge": "Self-Play-Partien je Stufe (gleicher Seed), Einheit Partie, beide Seiten summiert",
           "stufen": {}, "vergleiche": {}}
    for n in args.stages:
        mans = sorted(glob.glob(str(d / f"manifest_r5sims-{n}_*.json")))
        lz = json.load(open(mans[-1], encoding="utf-8")).get("laufzeit") if mans else None
        out["stufen"][str(n)] = {"partien": len(stages[n]), "laufzeit": lz}
        print(f"[r5-leiter] Stufe {n}: {len(stages[n])} Partien, laufzeit {lz}", flush=True)
    for lo, hi in zip(args.stages, args.stages[1:]):
        c = compare(stages[lo], stages[hi])
        out["vergleiche"][f"{hi}_gegen_{lo}"] = c
        print(f"[r5-leiter] {hi} gegen {lo}: gepaart {c['partien_gepaart']}, identisch bis R5 "
              f"{c['identisch_bis_runde5']}; " + "; ".join(
                  f"{k} {c[k]['hoeher_minus_niedriger_je_partie']:+.3f} (z {c[k]['z']:+.2f})"
                  for k in ("punkte", "strafleiste_r5", "volle_spalten", "volle_reihen")
                  if c[k]["z"] is not None), flush=True)
    out["laufzeit"] = laufzeit_block(t0, cpu_start=c0, threads=1,
                                     n_units=sum(len(s) for s in stages.values()), unit="partie")
    p = BASE_DIR / args.out
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Ergebnis: {p}", flush=True)


if __name__ == "__main__":
    main()
