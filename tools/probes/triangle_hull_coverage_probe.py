# -*- coding: utf-8 -*-
"""PREREG_heuristic_v2_long_rows.md par.3b.8 Stufe D -- Huellen-Deckung.

Nutzer-Vorschlag 2026-08-29: legt der Lehrer die Steine in der
Dreiecks-Einhuellenden, und wie weit folgen ihm die Netze? Ergebnis ist ein
geometrischer RICHTWERT je Runde, kein Tor.

Definition (heuristic_v2.rs im Stand 65b48af^, dreiecks_abweichung):
erlaubter Bereich r+c <= 5 (21 Zellen); gespiegelte Orientierung r >= c
(Start-Ecke rechts); gemessen wird je Partie/Seite die am ENDBRETT besser
passende Orientierung (kleinere Abweichung) und dann das komplette
Runden-Profil in dieser Orientierung.

Je Runde r (Brett nach dem Runden-Tiling = erster Record der Folgerunde,
Runde 5 = Endbrett): Anteil der in der Runde NEU belegten Zellen in der
Huelle, Fuellstaende Huelle x/21 und Aussen x/15, Dreiecks-Abweichung.

Aufruf (Datenpassage):
    python -X utf8 -u tools/probes/triangle_hull_coverage_probe.py \
        --source lehrer --pattern "selfplay_hv2_*.pkl" --limit 300
    python -X utf8 -u tools/probes/triangle_hull_coverage_probe.py \
        --source b04r2 --pattern "selfplay_otw22b04r2*.pkl"
"""
from __future__ import annotations

import argparse
import glob
import json
import pathlib
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
from corpus_io import load_records  # noqa: E402

ARTIFACT_DIR = _ROOT / "evaluations" / "artifacts"
PREREG = "PREREG_heuristic_v2_long_rows.md par.3b.8 Stufe D"

HULL_LEFT = {(r, c) for r in range(6) for c in range(6) if r + c <= 5}
HULL_RIGHT = {(r, c) for r in range(6) for c in range(6) if r >= c}


def occupancy(dome_grid):
    cells = set()
    for sr in range(3):
        row = dome_grid[sr] if sr < len(dome_grid) else []
        for sc in range(3):
            slot = row[sc] if sc < len(row) else None
            spaces = (slot or {}).get("spaces", []) if slot else []
            for si in range(4):
                sp = spaces[si] if si < len(spaces) else None
                if sp and sp.get("filled") is not None:
                    cells.add((sr * 2 + si // 2, sc * 2 + si % 2))
    return cells


def deviation(cells, hull):
    return len(hull - cells) + len(cells - hull)


def mirror(cell, hull):
    """Spiegelung an der Huellen-Kante. Linke Huelle (r+c<=5): Anti-Diagonale
    (r,c)->(5-c,5-r); rechte Huelle (r>=c): Hauptdiagonale (r,c)->(c,r)."""
    r, c = cell
    return (5 - c, 5 - r) if hull is HULL_LEFT else (c, r)


def forbidden_zone_stats(cells, hull):
    """Struktur der 'Fehler' (belegte Zellen AUSSERHALB der Huelle) --
    Nutzer-Analyseideen 2026-08-29, auf 6x6/15 Zellen uebersetzt:
    Cluster-Index (8er-Nachbarschaft), Symmetrie-Korrelation gegen die
    gespiegelte erlaubte Haelfte, Schwerpunkt, Diagonalabstand d (Band 1..5)
    mit Mittel/Varianz."""
    forbidden_all = [x for x in
                     ((r, c) for r in range(6) for c in range(6))
                     if x not in hull]
    errs = [x for x in cells if x not in hull]
    out = {"n": len(errs)}
    if errs:
        neigh = []
        errset = set(errs)
        for (r, c) in errs:
            neigh.append(sum(1 for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                             if (dr or dc) and (r + dr, c + dc) in errset))
        out["cluster_index"] = sum(neigh) / len(neigh)
        out["zentroid"] = (sum(r for r, _ in errs) / len(errs),
                           sum(c for _, c in errs) / len(errs))
        dists = [(r + c - 5) if hull is HULL_LEFT else (c - r) for r, c in errs]
        m = sum(dists) / len(dists)
        out["diag_abstand_mittel"] = m
        out["diag_abstand_var"] = sum((d - m) ** 2 for d in dists) / len(dists)
        out["band_histogramm"] = {d: dists.count(d) for d in range(1, 6)}
    # Symmetrie: verbotene Belegung vs. gespiegelte erlaubte Belegung
    a = [1.0 if x in cells else 0.0 for x in forbidden_all]
    b = [1.0 if mirror(x, hull) in cells else 0.0 for x in forbidden_all]
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((x - mb) ** 2 for x in b)
    if va > 0 and vb > 0:
        cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        out["sym_korrelation"] = cov / (va ** 0.5 * vb ** 0.5)
    else:
        out["sym_korrelation"] = None  # entartete Haelfte (leer/voll)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--source", required=True, help="Etikett fuers Artefakt")
    ap.add_argument("--pattern", required=True)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    t0 = time.time()

    files = sorted(glob.glob(str(_ROOT / "data" / args.pattern)))
    if args.limit:
        files = files[:args.limit]
    if not files:
        raise SystemExit(f"keine Dateien fuer {args.pattern}")

    # je Runde: [neu_in_huelle, neu_gesamt]; dazu Endstands-Groessen
    round_new = {r: [0, 0] for r in range(1, 6)}
    end_hull_fill, end_out_fill, end_dev = [], [], []
    fz_stats = []
    games = 0
    for fi, f in enumerate(files):
        recs = load_records(f)
        # je Partie: erster Record je Runde und letzter Record
        first_by_round = {}
        last = {}
        for rec in recs:
            st = rec.get("state") or {}
            gid = rec.get("game_id")
            rnd = st.get("round")
            key = (gid, rnd)
            if key not in first_by_round:
                first_by_round[key] = st
            if rec.get("winner") is not None:
                last[gid] = st
        gids = sorted({g for g, _ in first_by_round})
        for gid in gids:
            if gid not in last:
                continue
            games += 1
            for pi in range(2):
                # Brett NACH Runde r: erster Record von Runde r+1, fuer r=5 Endbrett.
                boards = {0: set()}
                for r in range(1, 6):
                    st = first_by_round.get((gid, r + 1)) if r < 5 else last[gid]
                    if st is None:
                        st = last[gid]
                    boards[r] = occupancy(st["players"][pi]["dome_grid"])
                final_cells = boards[5]
                hull = (HULL_LEFT if deviation(final_cells, HULL_LEFT)
                        <= deviation(final_cells, HULL_RIGHT) else HULL_RIGHT)
                for r in range(1, 6):
                    new = boards[r] - boards[r - 1]
                    round_new[r][0] += len(new & hull)
                    round_new[r][1] += len(new)
                end_hull_fill.append(len(final_cells & hull))
                end_out_fill.append(len(final_cells - hull))
                end_dev.append(deviation(final_cells, hull))
                fz_stats.append(forbidden_zone_stats(final_cells, hull))
        if fi % 50 == 49:
            print(f"  {fi + 1}/{len(files)} Dateien ({time.time() - t0:.0f}s)", flush=True)

    n = len(end_hull_fill)
    result = {
        "prereg": PREREG, "source": args.source, "pattern": args.pattern,
        "dateien": len(files), "partien": games, "seiten": n,
        "neu_in_huelle_anteil_je_runde": {
            r: (round_new[r][0] / round_new[r][1]) if round_new[r][1] else None
            for r in range(1, 6)},
        "endstand": {
            "huelle_fuellstand_mittel_von_21": sum(end_hull_fill) / n,
            "aussen_fuellstand_mittel_von_15": sum(end_out_fill) / n,
            "dreiecks_abweichung_mittel": sum(end_dev) / n,
        },
        "laufzeit": {"wanduhr_s": round(time.time() - t0, 1), "threads": 1},
    }
    # Struktur der verbotenen Zone (Nutzer-Analyseideen 2026-08-29)
    with_err = [s for s in fz_stats if s["n"] > 0]
    band_sum = {d: 0 for d in range(1, 6)}
    for s in with_err:
        for d, cnt in s.get("band_histogramm", {}).items():
            band_sum[d] += cnt
    syms = [s["sym_korrelation"] for s in fz_stats if s["sym_korrelation"] is not None]
    result["verbotene_zone"] = {
        "fehler_mittel_je_seite": sum(s["n"] for s in fz_stats) / len(fz_stats),
        "seiten_mit_fehlern": len(with_err) / len(fz_stats),
        "cluster_index_mittel": (sum(s["cluster_index"] for s in with_err) / len(with_err)) if with_err else None,
        "zentroid_mittel": ([sum(s["zentroid"][0] for s in with_err) / len(with_err),
                              sum(s["zentroid"][1] for s in with_err) / len(with_err)] if with_err else None),
        "diag_abstand_mittel": (sum(s["diag_abstand_mittel"] for s in with_err) / len(with_err)) if with_err else None,
        "diag_abstand_var_mittel": (sum(s["diag_abstand_var"] for s in with_err) / len(with_err)) if with_err else None,
        "band_histogramm_summe": band_sum,
        "sym_korrelation_mittel": (sum(syms) / len(syms)) if syms else None,
        "sym_korrelation_n": len(syms),
    }
    out = ARTIFACT_DIR / f"triangle_hull_coverage_{args.source}.json"
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False),
                   encoding="utf-8", newline="\n")
    print(f"\n{args.source}: neu-in-Huelle je Runde "
          f"{ {r: round(v, 3) if v is not None else None for r, v in result['neu_in_huelle_anteil_je_runde'].items()} }")
    print(f"Endstand: Huelle {result['endstand']['huelle_fuellstand_mittel_von_21']:.2f}/21, "
          f"aussen {result['endstand']['aussen_fuellstand_mittel_von_15']:.2f}/15, "
          f"Abweichung {result['endstand']['dreiecks_abweichung_mittel']:.2f}")
    print(f"Artefakt: {out}", flush=True)


if __name__ == "__main__":
    main()
