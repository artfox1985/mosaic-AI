# -*- coding: utf-8 -*-
"""PREREG_geometric_envelope.md par.8.15 Teil A -- gemessene Huelle.

Frage (Nutzer 2026-09-06, 23:05: "ja mach die gemessene huelle"): welche 21 (Kosten 56)
bzw. 22 (Kosten 62) Rasterzellen werden am Spielende tatsaechlich am haeufigsten belegt,
und deckt sich das mit der hergeleiteten Dreiecks-Huelle `r + c <= 5` (par.3, nur aus
Zeilensummen hergeleitet)?

Verfahren: Endzustand je Partie per Replayer (`analyze_game_log.run`), Belegung je Seite
(`triangle_hull_coverage_probe.occupancy`), Orientierung = kleinere Dreiecks-Abweichung,
rechts-orientierte Bretter an der senkrechten Achse gespiegelt (c -> 5 - c, par.3), dann
Fuellhaeufigkeit je Zelle und die Zellmenge mit maximaler Haeufigkeitssumme unter der
Kostenschranke (exakter 0/1-Rucksack, Kosten r + 1).

Aufruf (Projektordner, CPU-freies Fenster; reine Log-Arithmetik, Sekunden):
    python -X utf8 -u tools/probes/measured_hull_probe.py \\
        --server-logs "static/log/game_*.log" \\
        --artifact evaluations/artifacts/paired_arena_env_v24b06_vs_b01_first_s14.json ... \\
        --out evaluations/artifacts/measured_hull_probe.json
    python -X utf8 tools/probes/measured_hull_probe.py --selftest
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import pathlib
import sys
import tempfile
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools"))
sys.path.insert(0, str(_ROOT / "tools" / "probes"))

PREREG = "PREREG_geometric_envelope.md par.8.15 Teil A"
HULL_LEFT = frozenset((r, c) for r in range(6) for c in range(6) if r + c <= 5)
HULL_RIGHT = frozenset((r, c) for r in range(6) for c in range(6) if r <= c)
ALL_CELLS = [(r, c) for r in range(6) for c in range(6)]
PAR3_ROW_RATES = [4.88, 4.70, 2.88, 2.23, 1.71, 1.31]


def cost(cell) -> int:
    return cell[0] + 1


def hull_cost(cells) -> int:
    return sum(cost(x) for x in cells)


def normalize_left(occ: frozenset) -> tuple[frozenset, str]:
    """Orientierung nach kleinerer Dreiecks-Abweichung; rechts wird an der senkrechten
    Achse gespiegelt (c -> 5 - c), Gleichstand = links."""
    dev_l = len(HULL_LEFT ^ occ)
    dev_r = len(HULL_RIGHT ^ occ)
    if dev_r < dev_l:
        return frozenset((r, 5 - c) for (r, c) in occ), "rechts"
    return occ, "links"


def knapsack(freq: dict, budget: int) -> list:
    """Zellmenge mit maximaler Haeufigkeitssumme unter Kostenschranke `budget`
    (exakt, 0/1-Rucksack ueber die 36 Zellen; Gleichstand: weniger Kosten, dann
    Zeile, dann Spalte -- deterministisch)."""
    items = sorted(ALL_CELLS)
    # dp[b] = (wert, -kosten, gewaehlte Zellen) -- lexikografisch maximal
    best = [(0.0, 0, ()) for _ in range(budget + 1)]
    for cell in items:
        w = float(freq.get(cell, 0.0))
        k = cost(cell)
        for b in range(budget, k - 1, -1):
            cand_val, cand_negc, cand_set = best[b - k]
            cand = (cand_val + w, cand_negc - k, cand_set + (cell,))
            if (cand[0], cand[1]) > (best[b][0], best[b][1]):
                best[b] = cand
    return sorted(best[budget][2])


def occupancy_from_state(state: dict, pi: int) -> frozenset:
    import triangle_hull_coverage_probe as hullmod
    return frozenset(hullmod.occupancy(state["players"][pi].get("dome_grid") or []))


def final_state_of_log(log_path: pathlib.Path) -> dict | None:
    import analyze_game_log as agl
    rep, _lines, _li, _div = agl.run(log_path, model_path=None, sims=1, c_puct=0.3, do_oracle=False, limit=None)
    return json.loads(rep.g.state_json())


class Accumulator:
    def __init__(self):
        self.groups: dict = {}

    def add(self, group: str, occ: frozenset):
        g = self.groups.setdefault(group, {"n": 0, "counts": {}, "orient": {"links": 0, "rechts": 0}})
        occ_n, orient = normalize_left(occ)
        g["n"] += 1
        g["orient"][orient] += 1
        for cell in occ_n:
            g["counts"][cell] = g["counts"].get(cell, 0) + 1

    def report(self, group: str) -> dict:
        g = self.groups[group]
        n = max(1, g["n"])
        freq = {cell: g["counts"].get(cell, 0) / n for cell in ALL_CELLS}
        h56 = knapsack(freq, 56)
        h62 = knapsack(freq, 62)
        tri = sorted(HULL_LEFT)
        row_sums = [round(sum(freq[(r, c)] for c in range(6)), 2) for r in range(6)]
        p50 = freq[(5, 0)]
        both = g["counts"].get((5, 0), 0)
        # P((5,1) belegt | (5,0) belegt) aus den Zaehlern: braucht Paar-Zaehlung
        return {
            "n_seiten": g["n"], "orientierung": g["orient"],
            "haeufigkeit": [[round(freq[(r, c)], 3) for c in range(6)] for r in range(6)],
            "zeilensummen": row_sums, "par3_zeilenraten": PAR3_ROW_RATES,
            "huelle_56": {"zellen": h56, "kosten": hull_cost(h56), "gleich_mit_dreieck": len(set(h56) & HULL_LEFT),
                          "hinzu": sorted(set(h56) - HULL_LEFT), "weg": sorted(HULL_LEFT - set(h56)),
                          "wert": round(sum(freq[x] for x in h56), 3), "dreieck_wert": round(sum(freq[x] for x in tri), 3)},
            "huelle_62": {"zellen": h62, "kosten": hull_cost(h62), "gleich_mit_dreieck": len(set(h62) & HULL_LEFT),
                          "hinzu": sorted(set(h62) - HULL_LEFT), "weg": sorted(HULL_LEFT - set(h62)),
                          "enthaelt_5_1": (5, 1) in h62, "wert": round(sum(freq[x] for x in h62), 3)},
            "zeile6": {"(5,0)": round(freq[(5, 0)], 3), "(5,1)": round(freq[(5, 1)], 3), "(5,2)": round(freq[(5, 2)], 3)},
            "zeile5": {"(4,0)": round(freq[(4, 0)], 3), "(4,1)": round(freq[(4, 1)], 3), "(4,2)": round(freq[(4, 2)], 3)},
            "p_5_1_gegeben_5_0": round(g.get("pair_51_given_50", 0) / both, 3) if both else None,
        }


def add_pair_stats(acc: Accumulator, group: str, occ: frozenset):
    occ_n, _ = normalize_left(occ)
    g = acc.groups[group]
    if (5, 0) in occ_n and (5, 1) in occ_n:
        g["pair_51_given_50"] = g.get("pair_51_given_50", 0) + 1


def ingest(acc: Accumulator, state: dict, names: list, labels: list, extra: dict | None = None):
    scores = [state["players"][pi].get("score", 0) for pi in range(2)]
    for pi in range(2):
        occ = occupancy_from_state(state, pi)
        groups = ["alle", labels[pi]]
        if scores[0] != scores[1]:
            groups.append("gewinner" if scores[pi] > scores[1 - pi] else "verlierer")
        for grp in groups:
            acc.add(grp, occ)
            add_pair_stats(acc, grp, occ)


def selftest() -> int:
    # Spiegelung: ein rechts-orientiertes Dreieck wird zum linken
    occ_r = frozenset(HULL_RIGHT)
    occ_n, o = normalize_left(occ_r)
    assert o == "rechts" and occ_n == HULL_LEFT, (o, sorted(occ_n)[:5])
    occ_l, o2 = normalize_left(frozenset(HULL_LEFT))
    assert o2 == "links" and occ_l == HULL_LEFT
    # Rucksack: Dreiecks-Haeufigkeit 1 auf dem Dreieck, 0 sonst -> Dreieck bei 56
    freq = {cell: (1.0 if cell in HULL_LEFT else 0.0) for cell in ALL_CELLS}
    assert set(knapsack(freq, 56)) == HULL_LEFT, knapsack(freq, 56)
    # bei 62 kommt die guenstigste Nullzelle NICHT dazu (Wert 0 -> weniger Kosten gewinnt)
    assert set(knapsack(freq, 62)) == HULL_LEFT
    # (5,1) mit Haeufigkeit 0,9 verdraengt bei 56 keine Zelle mit Wert 1 (6 Kosten gegen 6 x 1,0)
    freq2 = dict(freq); freq2[(5, 1)] = 0.9
    assert (5, 1) not in knapsack(freq2, 56)
    assert (5, 1) in knapsack(freq2, 62)
    # (5,1) mit 0,9 und (0,5) nur 0,1 -> bei 56 tauscht der Rucksack (0,5)+(1,4)... nicht noetig;
    # Kostenprobe: Dreieck 56, Nutzer-Form 62
    assert hull_cost(HULL_LEFT) == 56 and hull_cost(HULL_LEFT | {(5, 1)}) == 62
    acc = Accumulator()
    acc.add("t", occ_r); add_pair_stats(acc, "t", occ_r)
    rep = acc.report("t")
    assert rep["orientierung"]["rechts"] == 1 and rep["huelle_56"]["gleich_mit_dreieck"] == 21
    assert rep["zeile6"]["(5,0)"] == 1.0 and rep["zeile6"]["(5,1)"] == 0.0
    print("selftest ok")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--server-logs", default=None, help="Glob auf Server-Logs (Mensch gegen KI)")
    ap.add_argument("--artifact", nargs="*", default=[], help="paired_arena_env_*.json (auch Globs)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.out:
        ap.error("--out fehlt")
    t0 = time.time()
    acc = Accumulator()
    games = 0
    fehler = []
    with tempfile.TemporaryDirectory() as tmp:
        if a.server_logs:
            files = sorted(glob.glob(a.server_logs))
            if a.limit:
                files = files[:a.limit]
            for f in files:
                txt = open(f, encoding="utf-8", errors="replace").read()
                if "Endwertung" not in txt:
                    continue
                names = ["Spieler 1", "KI"]
                try:
                    hdr = json.loads(txt.splitlines()[0][1:].strip()) if txt.startswith("#") else {}
                    names = hdr.get("players") or names
                except Exception:
                    pass
                labels = ["KI" if n == "KI" else "Mensch" for n in names]
                try:
                    st = final_state_of_log(pathlib.Path(f))
                    ingest(acc, st, names, labels)
                    games += 1
                except Exception as e:
                    fehler.append({"quelle": os.path.basename(f), "grund": str(e)[:120]})
                print(f"  {games} Partien ({time.time() - t0:.0f}s)", flush=True)
        for pat in a.artifact:
            for path in sorted(glob.glob(pat)) or [pat]:
                art = json.load(open(path, encoding="utf-8"))
                spec_a = os.path.basename(art.get("spec_a") or "A").replace(".spec.json", "")
                spec_b = os.path.basename(art.get("spec_b") or "B").replace(".spec.json", "")
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
                    labels = [f"Netz:{spec_a}", f"Netz:{spec_b}"]
                    try:
                        st = final_state_of_log(p)
                        ingest(acc, st, header["players"], labels)
                        games += 1
                    except Exception as e:
                        fehler.append({"quelle": os.path.basename(path), "index": i, "grund": str(e)[:120]})
                    if games % 20 == 0:
                        print(f"  {games} Partien ({time.time() - t0:.0f}s)", flush=True)
    out = {"prereg": PREREG, "partien": games, "fehler": fehler[:20],
           "definitionen": {"orientierung": "kleinere Dreiecks-Abweichung; rechts an der senkrechten Achse gespiegelt (c -> 5-c)",
                            "huelle_B": "Zellmenge mit maximaler Summe der Fuellhaeufigkeit unter Kosten <= B (Kosten r+1), exakter Rucksack",
                            "dreieck": "r + c <= 5 (links), 21 Zellen, Kosten 56"},
           "gruppen": {grp: acc.report(grp) for grp in sorted(acc.groups)},
           "laufzeit": {"wanduhr_s": round(time.time() - t0, 1), "cpu_s": round(time.process_time(), 1), "threads": 1,
                        "s_je_partie": round((time.time() - t0) / games, 3) if games else None}}
    pathlib.Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for grp, rep in out["gruppen"].items():
        h = rep["huelle_56"]; h2 = rep["huelle_62"]
        print(f"{grp}: n {rep['n_seiten']} | Huelle56 gleich {h['gleich_mit_dreieck']}/21, hinzu {h['hinzu']}, weg {h['weg']} | "
              f"Huelle62 hinzu {h2['hinzu']}, weg {h2['weg']}, (5,1) drin {h2['enthaelt_5_1']} | Zeile 6 {rep['zeile6']} | "
              f"Zeilensummen {rep['zeilensummen']}", flush=True)
    print(f"Artefakt {a.out} ({out['laufzeit']['wanduhr_s']} s)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
