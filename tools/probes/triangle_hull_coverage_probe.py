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


def _mr():
    import mosaic_rust
    return mosaic_rust
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


def row_weight(cell):
    """Bedien-Kosten der Zelle: Rasterzeile r braucht Musterreihe r, also
    r+1 Fliesen (Nutzer-Auftrag 2026-08-29: untere Reihen hoeher gewichten).
    Regel-hergeleitet, nicht gefittet."""
    return cell[0] + 1


def weighted_fill_share(cells, hull):
    """Kosten-gewichteter Fuellanteil der Huelle in [0,1]; Nenner ist die
    Gesamtkost der Huelle (56 fuer beide Orientierungen)."""
    total = sum(row_weight(x) for x in hull)
    return sum(row_weight(x) for x in (cells & hull)) / total


def depth(cell, hull):
    """Tiefe zur Huellen-Ecke: HULL_LEFT waechst von (0,0), gespiegelt von (0,5)."""
    r, c = cell
    return r + c if hull is HULL_LEFT else r + (5 - c)


def kendall_tau(pairs):
    """tau-a ueber ungebundene Paare; None bei < 2 verwertbaren Paaren."""
    conc = disc = 0
    n = len(pairs)
    for i in range(n):
        for j in range(i + 1, n):
            dx = pairs[i][0] - pairs[j][0]
            dy = pairs[i][1] - pairs[j][1]
            if dx == 0 or dy == 0:
                continue
            if dx * dy > 0:
                conc += 1
            else:
                disc += 1
    total = conc + disc
    return (conc - disc) / total if total else None


def best_hull(cells):
    return (HULL_LEFT if deviation(cells, HULL_LEFT) <= deviation(cells, HULL_RIGHT)
            else HULL_RIGHT)


def stufe_d2_metrics(boards, hull):
    """Stufe-D2-Kennzahlen 2-4 (par.3b.8) aus den Runden-Brettern in der
    FINALEN Orientierung: Frontier-tau, Halbzeit-Huelle, Orientierungs-
    Stabilitaet. Kennzahl 1 (lebende Huelle) braucht Zustaende und wird vom
    Aufrufer beigesteuert."""
    placed_round = {}
    for r in range(1, 6):
        for cell in boards[r] - boards[r - 1]:
            placed_round[cell] = r
    tau = kendall_tau([(rnd, depth(cell, hull)) for cell, rnd in placed_round.items()])
    halbzeit = {"fill3": len(boards[3] & hull), "dev3": deviation(boards[3], hull),
                "fill3_gewichtet": weighted_fill_share(boards[3], hull)}
    stability = 5
    for r in range(1, 6):
        if all(best_hull(boards[k]) is hull for k in range(r, 6)):
            stability = r
            break
    misoriented = sum(1 for cell, rnd in placed_round.items()
                      if rnd < stability and cell not in hull)
    return {"frontier_tau": tau, "halbzeit": halbzeit,
            "stabil_ab_runde": stability, "fehlorientiert_vor_stabil": misoriented}


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
    d2_stats = []
    end_wfill = []
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
                hull = best_hull(final_cells)
                d2 = stufe_d2_metrics(boards, hull)
                # Kennzahl 1 (lebende Huelle): tote unter den LEEREN
                # Huellen-Zellen am Ende von Runde 3 und 4 (Zustand = erster
                # Record der Folgerunde; Puffer < 0 bei kind=normal = tot).
                for r_end, key in ((3, "tot3"), (4, "tot4")):
                    st_next = first_by_round.get((gid, r_end + 1))
                    d2[key] = None
                    d2[key + "_gewichtet"] = None
                    if st_next is not None:
                        try:
                            comp = json.loads(_mr().plate_completability_json(
                                json.dumps(st_next), pi))
                            dead = set()
                            for c6, entries in enumerate(comp["col_open_cells"]):
                                for e in entries:
                                    if e.get("kind") == "normal" and e.get("buffer", 0) < 0:
                                        dead.add((e["r"], c6))
                            empty_hull = hull - boards[r_end]
                            if empty_hull:
                                d2[key] = len(dead & empty_hull) / len(empty_hull)
                                wtot = sum(row_weight(x) for x in empty_hull)
                                d2[key + "_gewichtet"] = (
                                    sum(row_weight(x) for x in (dead & empty_hull)) / wtot)
                        except Exception:
                            pass
                d2_stats.append(d2)
                for r in range(1, 6):
                    new = boards[r] - boards[r - 1]
                    round_new[r][0] += len(new & hull)
                    round_new[r][1] += len(new)
                end_hull_fill.append(len(final_cells & hull))
                end_wfill.append(weighted_fill_share(final_cells, hull))
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
            "huelle_fuellanteil_kosten_gewichtet": sum(end_wfill) / n,
            "aussen_fuellstand_mittel_von_15": sum(end_out_fill) / n,
            "dreiecks_abweichung_mittel": sum(end_dev) / n,
        },
        "laufzeit": {"wanduhr_s": round(time.time() - t0, 1), "threads": 1},
    }
    # Stufe D2 (par.3b.8): vier Huellen-Kennzahlen
    taus = [d["frontier_tau"] for d in d2_stats if d["frontier_tau"] is not None]
    tot3 = [d["tot3"] for d in d2_stats if d["tot3"] is not None]
    tot4 = [d["tot4"] for d in d2_stats if d["tot4"] is not None]
    result["stufe_d2"] = {
        "frontier_tau_mittel": (sum(taus) / len(taus)) if taus else None,
        "halbzeit_fill_mittel_von_21": sum(d["halbzeit"]["fill3"] for d in d2_stats) / len(d2_stats),
        "halbzeit_fuellanteil_kosten_gewichtet": sum(d["halbzeit"]["fill3_gewichtet"] for d in d2_stats) / len(d2_stats),
        "halbzeit_abweichung_mittel": sum(d["halbzeit"]["dev3"] for d in d2_stats) / len(d2_stats),
        "stabil_ab_runde_mittel": sum(d["stabil_ab_runde"] for d in d2_stats) / len(d2_stats),
        "stabil_ab_r1_anteil": sum(1 for d in d2_stats if d["stabil_ab_runde"] == 1) / len(d2_stats),
        "fehlorientiert_vor_stabil_mittel": sum(d["fehlorientiert_vor_stabil"] for d in d2_stats) / len(d2_stats),
        "tote_huelle_r3_mittel": (sum(tot3) / len(tot3)) if tot3 else None,
        "tote_huelle_r4_gewichtet_mittel": (lambda v: (sum(v) / len(v)) if v else None)(
            [d["tot4_gewichtet"] for d in d2_stats if d.get("tot4_gewichtet") is not None]),
        "tote_huelle_r4_mittel": (sum(tot4) / len(tot4)) if tot4 else None,
        "tote_huelle_n": [len(tot3), len(tot4)],
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
