# -*- coding: utf-8 -*-
"""Tiling: Punkte gegen Nachbarschafts-Geometrie (PREREG_geometric_envelope.md par.8.12).

Nutzer 2026-09-05: "tiling ist greedy und geht immer auf punktemaximierung. die
meisten punkte fallen erst in runde 4-5. sprich tiling muss hier mehr auf die
geometrie und die potentiellen nachbarn gehen als auf die reinen punkte."

Die Sonde replayt Partien (Server-Logs Mensch gegen KI ODER Arena-Artefakte)
und haelt an jedem Rundenende (Zustand vor dem ersten Tiling-Zug) fuer beide
Spieler fest:

  * alle Tiling-Abschluesse des exakten Loesers (`mosaic_rust.tiling_candidates_json`,
    Top-K nach Punkten, K gross, damit auch punktferne Abschluesse dabei sind),
  * je Abschluss die Rundenpunkte des Loesers und zwei Geometrie-Masse der NEU
    belegten Zellen:
      G4    = Summe ueber neue Zellen der leeren 4-Nachbarn im 6x6-Raster
      Gline = Summe ueber neue Zellen der leeren Zellen in derselben Zeile und Spalte
    (leer = ohne Stein nach dem Abschluss; NAEHERUNG: Farb- und Vorratsbedingungen
    der Zelle werden nicht geprueft, das ist ein Obergrenzen-Mass fuer kuenftige
    Nachbarschaft),
  * den TATSAECHLICH gespielten Abschluss (Zellen, die bis zum naechsten
    Rundenanfang dazugekommen sind) und den Kandidaten, der dazu passt.

Fragen je Runde: Wie oft weicht der geometrie-beste Abschluss vom punkt-besten
ab, was kostet er an Rundenpunkten, was gewinnt er an Nachbarschaft? Und spielt
der Mensch den punkt-besten Abschluss oder laesst er Punkte fuer Geometrie
liegen -- im Vergleich zur KI-Seite und zu den Netz-Arenen?

Aufruf (CPU-Kern, Minuten; NICHT neben einer laufenden Messung):
    python -X utf8 -u tools/probes/tiling_geometry_probe.py --server-logs "static/log/game_*.log" \
        --out evaluations/artifacts/tiling_geometry_probe_human.json
    python -X utf8 -u tools/probes/tiling_geometry_probe.py --artifact <paired_arena_env_*.json> ... \
        --out evaluations/artifacts/tiling_geometry_probe_arena.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import pathlib
import statistics
import sys
import tempfile
import time
from collections import defaultdict

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent))

TILING_METHODS = {"apply_tiling", "apply_tiling_chips", "apply_tiling_chips_with"}
DRAFT_METHODS = {"apply_stone", "apply_dome", "apply_dome_stack_peek",
                 "apply_dome_stack_choose", "apply_bonus_chip", "apply_start_tile"}


def occ_of(state: dict, pi: int) -> frozenset:
    import triangle_hull_coverage_probe as hull
    return frozenset(hull.occupancy(state["players"][pi].get("dome_grid") or []))


def geometry(new_cells, occ_after) -> tuple:
    g4 = 0
    gline = 0
    for (r, c) in new_cells:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < 6 and 0 <= cc < 6 and (rr, cc) not in occ_after:
                g4 += 1
        gline += sum(1 for cc in range(6) if (r, cc) not in occ_after)
        gline += sum(1 for rr in range(6) if (rr, c) not in occ_after)
    return g4, gline


def analyze_round_end(mr, state_json: str, k: int, records: list, meta: dict):
    """Fuer beide Spieler: Kandidaten, Punkte, Geometrie; legt je Spieler einen
    offenen Datensatz an, den der naechste Rundenanfang mit dem tatsaechlichen
    Abschluss vervollstaendigt."""
    st = json.loads(state_json)
    rnd = int(st.get("round", st.get("round_number", 0)) or 0)  # serialize.rs:277: Schluessel "round"
    for pi in (0, 1):
        before = occ_of(st, pi)
        try:
            cands = json.loads(mr.tiling_candidates_json(state_json, pi, k))
        except Exception as e:  # defensiv: Loeser-Budget o.ae.
            records.append({**meta, "round": rnd, "pi": pi, "fehler": str(e)[:120]})
            continue
        rows = []
        for cnd in cands:
            after = occ_of(cnd["state"], pi)
            new = after - before
            g4, gl = geometry(new, after)
            rows.append({"points": int(cnd["points"]), "g4": g4, "gline": gl, "new": sorted(new), "after": after})
        if not rows:
            records.append({**meta, "round": rnd, "pi": pi, "fehler": "keine Kandidaten"})
            continue
        pbest = max(rows, key=lambda x: (x["points"], x["gline"], x["g4"]))
        gbest = max(rows, key=lambda x: (x["gline"], x["g4"], x["points"]))
        records.append({**meta, "round": rnd, "pi": pi, "n_cands": len(rows), "before": before,
                        "pbest": pbest, "gbest": gbest, "rows": rows,
                        "differs": pbest["after"] != gbest["after"],
                        "d_points": pbest["points"] - gbest["points"],
                        "d_gline": gbest["gline"] - pbest["gline"], "d_g4": gbest["g4"] - pbest["g4"]})


def complete_with_actual(state_json: str, open_records: list):
    """Naechster Rundenanfang: die tatsaechlich dazugekommenen Zellen je Spieler."""
    st = json.loads(state_json)
    for rec in open_records:
        if "rows" not in rec or "actual" in rec:
            continue
        pi = rec["pi"]
        after = occ_of(st, pi)
        new = after - rec["before"]
        g4, gl = geometry(new, after)
        match = next((r for r in rec["rows"] if r["after"] == after), None)
        rec["actual"] = {"new": sorted(new), "g4": g4, "gline": gl,
                         "points": match["points"] if match else None, "matched": match is not None,
                         "is_pbest": after == rec["pbest"]["after"], "is_gbest": after == rec["gbest"]["after"]}


def replay(log_path: pathlib.Path, mr, k: int, meta: dict, records: list) -> str | None:
    import analyze_game_log as agl
    orig_apply = agl.Replayer.apply
    orig_amb = agl.Replayer.apply_ambiguous
    ctx = {"in_tiling": False, "open": []}

    def before_method(self, method):
        try:
            sj = self.g.state_json()
        except Exception:
            return
        if method in TILING_METHODS and not ctx["in_tiling"]:
            ctx["in_tiling"] = True
            start = len(records)
            analyze_round_end(mr, sj, k, records, meta)
            ctx["open"] = records[start:]
        elif method in DRAFT_METHODS and ctx["in_tiling"]:
            ctx["in_tiling"] = False
            complete_with_actual(sj, ctx["open"])
            ctx["open"] = []

    def apply(self, lines, li, method, *args, **kwargs):
        before_method(self, method)
        return orig_apply(self, lines, li, method, *args, **kwargs)

    def apply_ambiguous(self, lines, li, method, candidates):
        before_method(self, method)
        return orig_amb(self, lines, li, method, candidates)

    agl.Replayer.apply = apply
    agl.Replayer.apply_ambiguous = apply_ambiguous
    try:
        rep, _lines, _li, div = agl.run(log_path, model_path=None, sims=1, c_puct=0.3, do_oracle=False, limit=None)
        # Runde 5: Abschluss aus dem Endzustand
        if ctx["open"]:
            try:
                complete_with_actual(rep.g.state_json(), ctx["open"])
            except Exception:
                pass
    finally:
        agl.Replayer.apply = orig_apply
        agl.Replayer.apply_ambiguous = orig_amb
    return div


def summarize(records: list, side_of) -> dict:
    out = {}
    groups = defaultdict(list)
    for r in records:
        if "rows" not in r:
            continue
        groups[(side_of(r), r["round"])].append(r)
    for (side, rnd), rs in sorted(groups.items()):
        n = len(rs)
        differs = [r for r in rs if r["differs"]]
        act = [r for r in rs if r.get("actual", {}).get("matched")]
        out.setdefault(side, {})[f"R{rnd}"] = {
            "n": n, "kandidaten_mittel": round(statistics.mean(r["n_cands"] for r in rs), 1),
            "anteil_gbest_ungleich_pbest": round(len(differs) / n, 3),
            "punktkosten_gbest_mittel": round(statistics.mean(r["d_points"] for r in differs), 2) if differs else None,
            "gline_gewinn_gbest_mittel": round(statistics.mean(r["d_gline"] for r in differs), 2) if differs else None,
            "g4_gewinn_gbest_mittel": round(statistics.mean(r["d_g4"] for r in differs), 2) if differs else None,
            "pbest_punkte_mittel": round(statistics.mean(r["pbest"]["points"] for r in rs), 2),
            "pbest_gline_mittel": round(statistics.mean(r["pbest"]["gline"] for r in rs), 2),
            "actual_zugeordnet": len(act),
            "actual_ist_pbest": round(sum(1 for r in act if r["actual"]["is_pbest"]) / len(act), 3) if act else None,
            "actual_ist_gbest": round(sum(1 for r in act if r["actual"]["is_gbest"]) / len(act), 3) if act else None,
            "actual_punkte_minus_pbest": round(statistics.mean(r["actual"]["points"] - r["pbest"]["points"] for r in act), 2) if act else None,
            "actual_gline_minus_pbest": round(statistics.mean(r["actual"]["gline"] - r["pbest"]["gline"] for r in act), 2) if act else None,
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--server-logs", default=None, help="Glob auf Server-Logs (Mensch gegen KI)")
    ap.add_argument("--artifact", nargs="*", default=[], help="paired_arena_env_*.json")
    ap.add_argument("--k", type=int, default=32, help="Top-K Abschluesse je Spieler und Rundenende")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import mosaic_rust as mr
    t0 = time.time()
    records: list = []
    divergences = []
    games = 0
    with tempfile.TemporaryDirectory() as tmp:
        if a.server_logs:
            files = sorted(glob.glob(a.server_logs))
            if a.limit:
                files = files[:a.limit]
            for f in files:
                txt = open(f, encoding="utf-8", errors="replace").read()
                if "Endwertung" not in txt:
                    continue
                names = None
                try:
                    hdr = json.loads(txt.splitlines()[0][1:].strip()) if txt.startswith("#") else {}
                    names = hdr.get("players")
                except Exception:
                    pass
                meta = {"quelle": os.path.basename(f), "names": names or ["Spieler 1", "KI"]}
                div = replay(pathlib.Path(f), mr, a.k, meta, records)
                games += 1
                if div:
                    divergences.append({"quelle": meta["quelle"], "grund": str(div)[:120]})
                print(f"  {games} Partien, {len(records)} Rundenenden ({time.time() - t0:.0f}s)", flush=True)
        for path in a.artifact:
            art = json.load(open(path, encoding="utf-8"))
            g = art.get("games") or {}
            lst = [sp for arm in (g.values() if isinstance(g, dict) else [g]) for sp in arm]
            if a.limit:
                lst = lst[:a.limit]
            for i, sp in enumerate(lst):
                header = {"players": sp.get("names") or ["NetzA", "NetzB"], "first_player": sp.get("first_player", 0),
                          "seed": sp.get("game_seed", 0)}
                p = pathlib.Path(tmp) / f"game_{games:05d}.log"
                p.write_text("# " + json.dumps(header, ensure_ascii=False) + "\n" + "\n".join(sp["log"]) + "\n",
                             encoding="utf-8", newline="\n")
                meta = {"quelle": os.path.basename(path), "names": header["players"], "index": i}
                div = replay(p, mr, a.k, meta, records)
                games += 1
                if div:
                    divergences.append({"quelle": meta["quelle"], "index": i, "grund": str(div)[:120]})
                if games % 10 == 0:
                    print(f"  {games} Partien, {len(records)} Rundenenden ({time.time() - t0:.0f}s)", flush=True)

    def side_of(r):
        name = (r.get("names") or ["?", "?"])[r["pi"]]
        if name == "KI":
            return "KI"
        if name.startswith("Netz"):
            return name
        return "Mensch"

    summary = summarize(records, side_of)
    out = {"prereg": "PREREG_geometric_envelope.md par.8.12", "k": a.k, "partien": games,
           "divergenzen": divergences, "rundenenden": sum(1 for r in records if "rows" in r),
           "fehler": [r for r in records if "fehler" in r][:20],
           "definitionen": {"G4": "leere 4-Nachbarn der neu belegten Zellen (Summe)",
                            "Gline": "leere Zellen in Zeile und Spalte jeder neu belegten Zelle (Summe)",
                            "pbest": "max Punkte, dann Gline, dann G4", "gbest": "max Gline, dann G4, dann Punkte",
                            "naeherung": "leer = ohne Stein; Farb-/Vorratsbedingungen nicht geprueft"},
           "zusammenfassung": summary}
    for side, rounds in summary.items():
        for rnd, v in rounds.items():
            print(f"{side} {rnd}: n {v['n']} | gbest != pbest {v['anteil_gbest_ungleich_pbest']} | kostet {v['punktkosten_gbest_mittel']} Pkt, "
                  f"gewinnt Gline {v['gline_gewinn_gbest_mittel']} | gespielt = pbest {v['actual_ist_pbest']} ({v['actual_zugeordnet']} zugeordnet), "
                  f"Punkte gegen pbest {v['actual_punkte_minus_pbest']}, Gline gegen pbest {v['actual_gline_minus_pbest']}", flush=True)
    out["laufzeit"] = {"wanduhr_s": round(time.time() - t0, 1), "cpu_s": round(time.process_time(), 1), "threads": 1,
                       "s_je_partie": round((time.time() - t0) / max(1, games), 2)}
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=lambda o: sorted(o) if isinstance(o, (set, frozenset)) else str(o))
    print(f"Partien {games}, Rundenenden {out['rundenenden']}, Divergenzen {len(divergences)} | Artefakt: {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
