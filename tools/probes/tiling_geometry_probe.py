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

ERGAENZUNG 2026-09-06 (par.8.13/8.14, Nutzer: "bau k3 f nach der messung"): Alter und
Haeufigkeit BLOCKIERTER langer Reihen. An jedem Rundenende wird fuer jede gebundene,
unvollstaendige Musterreihe 5/6 (Index 4/5) das Praedikat "Reihe kann die Huelle noch
bedienen" aus par.8.14 berechnet (JA: Huellenzelle der Zeile nimmt die Farbe heute an;
JA_WARTEND: plattenlose Huellenzelle der Zeile UND eine Platte mit passender Zelle an
dieser Position ist noch in Auslage/Stapel; sonst NEIN), Reihen-Episoden ueber die
Rundenenden verfolgt (Beginn, Alter in Rundenenden, voll geworden oder am Ende offen)
und nach Seite und Reihenlaenge zusammengefasst (`reihen_alter`). Rein additiv: die
par.8.12-Messung bleibt unveraendert, ein Fehler hier bricht sie nicht.

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
                 "apply_dome_stack_choose", "apply_bonus_chip", "apply_start_tile", "apply_pass"}


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



# ---------------------------------------------------------------------------
# par.8.13/8.14: Reihen-Alter blockierter langer Reihen (2026-09-06)
# ---------------------------------------------------------------------------
# Katalog der 18 Kuppelplatten, Reihenfolge der Zellen oben-links, oben-rechts,
# unten-links, unten-rechts -- abgeschrieben aus engine/src/dome.rs
# `build_dome_tile_pool` (Stand 2026-09-06). ("N", farbe) normal, ("W",) bunt,
# ("S",) Spezialfeld. Farbnamen wie TileColor::value() (tile.rs:26).
_N, _W, _S = "N", "W", "S"
DOME_DESIGNS = [
    ((_N, "gelb"), (_N, "schwarz"), (_N, "türkis"), (_S,)),
    ((_W,), (_N, "blau"), (_N, "türkis"), (_N, "schwarz")),
    ((_N, "türkis"), (_N, "rot"), (_N, "blau"), (_W,)),
    ((_N, "schwarz"), (_N, "gelb"), (_N, "rot"), (_W,)),
    ((_N, "schwarz"), (_S,), (_N, "türkis"), (_N, "rot")),
    ((_N, "türkis"), (_N, "gelb"), (_W,), (_N, "schwarz")),
    ((_S,), (_N, "schwarz"), (_N, "rot"), (_N, "blau")),
    ((_N, "gelb"), (_N, "blau"), (_N, "schwarz"), (_S,)),
    ((_N, "türkis"), (_N, "rot"), (_N, "blau"), (_S,)),
    ((_N, "gelb"), (_N, "rot"), (_W,), (_N, "blau")),
    ((_N, "gelb"), (_S,), (_N, "schwarz"), (_N, "rot")),
    ((_N, "türkis"), (_N, "schwarz"), (_N, "rot"), (_W,)),
    ((_N, "blau"), (_N, "schwarz"), (_S,), (_N, "türkis")),
    ((_N, "rot"), (_N, "türkis"), (_N, "gelb"), (_W,)),
    ((_N, "türkis"), (_N, "blau"), (_W,), (_N, "gelb")),
    ((_S,), (_N, "türkis"), (_N, "gelb"), (_N, "blau")),
    ((_N, "rot"), (_W,), (_N, "blau"), (_N, "schwarz")),
    ((_S,), (_N, "gelb"), (_N, "blau"), (_N, "rot")),
]
LONG_ROWS = (4, 5)  # Index 4 = Reihe 5 (5 Steine), Index 5 = Reihe 6
ROW_COLORS = ("blau", "gelb", "rot", "schwarz", "türkis")


def space_accepts(sp, color: str) -> bool:
    """DomeSpace::accepts (dome.rs:62) auf dem JSON von serialize_space (serialize.rs:82)."""
    if not sp or sp.get("filled") is not None or sp.get("locked"):
        return False
    t = sp.get("type")
    if t == "NORMAL":
        return sp.get("color") == color
    return t == "WILD"


def design_accepts_at(design, pos: int, color: str) -> bool:
    d = design[pos]
    return d[0] == _W or (d[0] == _N and d[1] == color)


def cell_slot_and_space(dome_grid, r: int, c: int):
    """(Platte-JSON oder None, Space-JSON oder None) fuer Rasterzelle (r, c); Abbildung wie
    triangle_hull_coverage_probe.occupancy: Slot (r//2, c//2), Zelle (r%2)*2 + c%2."""
    row = dome_grid[r // 2] if r // 2 < len(dome_grid) else []
    slot = row[c // 2] if c // 2 < len(row) else None
    if not slot:
        return None, None
    spaces = slot.get("spaces") or []
    pos = (r % 2) * 2 + (c % 2)
    return slot, (spaces[pos] if pos < len(spaces) else None)


def tile_can_still_come(state: dict, pos: int, color: str) -> bool:
    """Gibt es in Auslage (`dome_display`), im angefangenen Stapelzug (`pending_stack_draw`) oder im
    verdeckten Stapel (`dome_pool_mask`, Design-Ids) eine Platte, deren Zelle `pos` `color` annimmt?"""
    for t in (state.get("dome_display") or []) + (state.get("pending_stack_draw") or []):
        sps = t.get("spaces") or []
        if pos < len(sps) and space_accepts(sps[pos], color):
            return True
    mask = state.get("dome_pool_mask") or []
    for tid, present in enumerate(mask):
        if present and tid < len(DOME_DESIGNS) and design_accepts_at(DOME_DESIGNS[tid], pos, color):
            return True
    return False


def row_predicate(state: dict, pi: int, r: int, color: str, hull) -> dict:
    """par.8.14, Praedikat "Reihe kann die Huelle noch bedienen" fuer Musterreihe r mit Farbe color.
    Rueckgabe: {"pred": "ja" | "ja_wartend" | "nein" | "unbekannt", "annehmend_ausserhalb": bool,
    "plattenlos_huelle": int}. `annehmend_ausserhalb`: eine Zelle der Zeile AUSSERHALB der Huelle
    nimmt die Farbe heute an (Aussen-Legen moeglich, par.8.13)."""
    if color not in ROW_COLORS:
        return {"pred": "unbekannt", "annehmend_ausserhalb": False, "plattenlos_huelle": 0}
    grid = state["players"][pi].get("dome_grid") or []
    accept_in, accept_out, slots_free = False, False, []
    for c in range(6):
        slot, sp = cell_slot_and_space(grid, r, c)
        in_hull = (r, c) in hull
        if slot is None:
            if in_hull:
                slots_free.append(c)
            continue
        if space_accepts(sp, color):
            if in_hull:
                accept_in = True
            else:
                accept_out = True
    if accept_in:
        pred = "ja"
    elif slots_free and any(tile_can_still_come(state, (r % 2) * 2 + (c % 2), color) for c in slots_free):
        pred = "ja_wartend"
    else:
        pred = "nein"
    return {"pred": pred, "annehmend_ausserhalb": accept_out, "plattenlos_huelle": len(slots_free)}


def track_row_ages(state: dict, rnd: int, ctx_rows: dict, episodes: list, meta: dict):
    """Ein Rundenende (Zustand vor dem Tiling): Episoden der langen Reihen fortschreiben.
    ctx_rows: (pi, r) -> offene Episode. Eine Episode beginnt, wenn die Reihe gebunden ist, und endet,
    wenn sie am Rundenende VOLL ist (wird jetzt getilet) oder das Spiel endet (offen)."""
    import triangle_hull_coverage_probe as hullmod
    for pi in (0, 1):
        pl = state["players"][pi]
        occ = hullmod.occupancy(pl.get("dome_grid") or [])
        hull = hullmod.best_hull(occ)
        lines = pl.get("pattern_lines") or []
        for r in LONG_ROWS:
            if r >= len(lines):
                continue
            line = lines[r]
            k = len(line.get("tiles") or [])
            cap = int(line.get("capacity") or (r + 1))
            color = line.get("color")
            occ_row = frozenset(c for (rr, c) in occ if rr == r)
            ep = ctx_rows.get((pi, r))
            # Fassung 2 (2026-09-06): Ende einer Episode am Zellgewinn der Rasterzeile r seit dem
            # letzten Rundenende klassifizieren. Musterreihe r legt in Rasterzeile r (envelope.rs
            # projected_occupancy: get_space(r, c)). Gewinn -> die Reihe wurde GELEGT (auch wenn sie
            # erst im Tiling per Bonus-Chip voll wurde); kein Gewinn -> geraeumt (unplatzierbar) oder
            # anders geleert. Fassung 1 zaehlte nur "am Rundenende voll" und liess 35-56 % als Rest.
            if ep is not None:
                gained = bool(occ_row - ep["occ_row_letzt"])
                ends = (k == 0 or color is None or ep["color"] != color or k < ep["k_letzt"]
                        or ep.get("voll_runde") is not None)
                if ends:
                    if ep.get("voll_runde") is not None:
                        ep["ende"] = "voll_gelegt" if gained else "voll_geraeumt"
                    else:
                        ep["ende"] = "chip_gelegt" if gained else "geraeumt_oder_unklar"
                    ep["ende_runde"] = rnd
                    episodes.append(ep); ep = None; ctx_rows.pop((pi, r), None)
            if k == 0 or color is None:
                continue
            if ep is None:
                ep = {**meta, "pi": pi, "r": r, "reihe": r + 1, "color": color, "start_runde": rnd,
                      "rundenenden": 0, "praedikate": [], "blockiert_rundenenden": 0,
                      "aussen_moeglich_rundenenden": 0, "voll_runde": None, "k_letzt": 0,
                      "occ_row_letzt": occ_row}
                ctx_rows[(pi, r)] = ep
            ep["rundenenden"] += 1
            ep["k_letzt"] = k
            ep["occ_row_letzt"] = occ_row
            if k >= cap:
                ep["voll_runde"] = rnd  # wird in diesem Tiling gelegt (oder geraeumt) -- Episode endet
                ep["praedikate"].append("voll")
                continue
            pr = row_predicate(state, pi, r, color, hull)
            ep["praedikate"].append(pr["pred"])
            if pr["pred"] == "nein":
                ep["blockiert_rundenenden"] += 1
                if pr["annehmend_ausserhalb"]:
                    ep["aussen_moeglich_rundenenden"] += 1
                ep.setdefault("blockiert_ab_runde", rnd)


def close_row_ages(ctx_rows: dict, episodes: list, final_round: int, final_state: dict | None = None):
    """Spielende: offene Episoden schliessen. Mit `final_state` (Zustand NACH dem letzten Tiling)
    wird auch die letzte Runde am Zellgewinn klassifiziert; ohne ihn bleibt "voll" / "offen_am_ende"."""
    import triangle_hull_coverage_probe as hullmod
    for (pi, r), ep in list(ctx_rows.items()):
        gained = None
        if final_state is not None:
            try:
                occ = hullmod.occupancy(final_state["players"][pi].get("dome_grid") or [])
                gained = bool(frozenset(c for (rr, c) in occ if rr == r) - ep["occ_row_letzt"])
            except Exception:
                gained = None
        if ep.get("voll_runde") is not None:
            ep["ende"] = "voll" if gained is None else ("voll_gelegt" if gained else "voll_geraeumt")
        else:
            ep["ende"] = "offen_am_ende" if not gained else "chip_gelegt"
        ep["ende_runde"] = final_round
        episodes.append(ep)
    ctx_rows.clear()


def summarize_row_ages(episodes: list, side_of) -> dict:
    out = {}
    groups = defaultdict(list)
    for ep in episodes:
        groups[(side_of(ep), ep["reihe"])].append(ep)
    for (side, row_len), eps in sorted(groups.items()):
        n = len(eps)
        blocked = [e for e in eps if e["blockiert_rundenenden"] > 0]
        never = [e for e in eps if e["blockiert_rundenenden"] == 0]
        laid = ("voll", "voll_gelegt", "chip_gelegt")  # Reihe wurde ins Raster gelegt
        full_eps = [e for e in eps if e["ende"] in laid]
        open_eps = [e for e in eps if e["ende"] == "offen_am_ende"]

        def rate(sub, pred):
            return round(sum(1 for e in sub if pred(e)) / len(sub), 3) if sub else None
        out.setdefault(side, {})[f"Reihe{row_len}"] = {
            "episoden": n,
            "enden": {k: sum(1 for e in eps if e["ende"] == k) for k in
                      ("voll", "voll_gelegt", "voll_geraeumt", "chip_gelegt", "geraeumt_oder_unklar", "offen_am_ende")},
            "gelegt_anteil": rate(eps, lambda e: e["ende"] in laid),
            "voll_am_rundenende_anteil": rate(eps, lambda e: e["ende"] in ("voll", "voll_gelegt", "voll_geraeumt")),
            "chip_gelegt_anteil": rate(eps, lambda e: e["ende"] == "chip_gelegt"),
            "geraeumt_anteil": rate(eps, lambda e: e["ende"] in ("voll_geraeumt", "geraeumt_oder_unklar")),
            "offen_am_ende_anteil": rate(eps, lambda e: e["ende"] == "offen_am_ende"),
            "alter_bis_gelegt_mittel_rundenenden": round(statistics.mean(e["rundenenden"] for e in full_eps), 2) if full_eps else None,
            "alter_offen_mittel_rundenenden": round(statistics.mean(e["rundenenden"] for e in open_eps), 2) if open_eps else None,
            "je_blockiert_anteil": rate(eps, lambda e: e["blockiert_rundenenden"] > 0),
            "blockiert_rundenenden_mittel": round(statistics.mean(e["blockiert_rundenenden"] for e in blocked), 2) if blocked else None,
            "blockiert_gelegt_anteil": rate(blocked, lambda e: e["ende"] in laid),
            "nie_blockiert_gelegt_anteil": rate(never, lambda e: e["ende"] in laid),
            "blockiert_offen_am_ende_anteil": rate(blocked, lambda e: e["ende"] == "offen_am_ende"),
            "nie_blockiert_offen_am_ende_anteil": rate(never, lambda e: e["ende"] == "offen_am_ende"),
            "blockiert_aussen_moeglich_anteil": (round(sum(e["aussen_moeglich_rundenenden"] for e in blocked)
                                                        / sum(e["blockiert_rundenenden"] for e in blocked), 3) if blocked else None),
            "praedikat_je_rundenende": {p: sum(e["praedikate"].count(p) for e in eps)
                                        for p in ("ja", "ja_wartend", "nein", "unbekannt", "voll")},
            "blockiert_ab_runde_verteilung": {str(k): sum(1 for e in blocked if e.get("blockiert_ab_runde") == k)
                                              for k in range(1, 6)},
        }
    return out


def replay(log_path: pathlib.Path, mr, k: int, meta: dict, records: list, episodes: list | None = None) -> str | None:
    import analyze_game_log as agl
    orig_apply = agl.Replayer.apply
    orig_amb = agl.Replayer.apply_ambiguous
    ctx = {"in_tiling": False, "open": [], "rows": {}, "last_round": 0}

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
            if episodes is not None:  # par.8.13/8.14, additiv
                try:
                    st = json.loads(sj)
                    ctx["last_round"] = int(st.get("round", 0) or 0)
                    track_row_ages(st, ctx["last_round"], ctx["rows"], episodes, meta)
                except Exception as e:
                    ctx["row_err"] = str(e)[:120]
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
        if episodes is not None:
            try:
                try:
                    final_state = json.loads(rep.g.state_json())
                except Exception:
                    final_state = None
                close_row_ages(ctx["rows"], episodes, ctx["last_round"], final_state)
                if ctx.get("row_err"):
                    episodes.append({**meta, "fehler": ctx["row_err"]})
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
    episodes: list = []  # par.8.13/8.14 Reihen-Alter
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
                div = replay(pathlib.Path(f), mr, a.k, meta, records, episodes)
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
                div = replay(p, mr, a.k, meta, records, episodes)
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
    # par.8.13/8.14: Reihen-Alter (additiv, Fehler brechen die par.8.12-Messung nicht)
    try:
        eps_ok = [e for e in episodes if "reihe" in e]
        ra = summarize_row_ages(eps_ok, side_of)
        out["reihen_alter"] = {
            "prereg": "PREREG_geometric_envelope.md par.8.13/8.14", "version": "2026-09-06 Fassung 2 (Episodenende am Zellgewinn der Rasterzeile)",
            "definitionen": {
                "episode": "gebundene Musterreihe 5/6 von ihrem ersten Rundenende bis sie am Rundenende voll ist (Tiling) oder das Spiel endet",
                "praedikat": "ja = Huellenzelle der Zeile nimmt die Farbe heute an; ja_wartend = plattenlose Huellenzelle UND passende Platte noch in Auslage/Stapel (Katalog dome.rs); nein = Reihe kann die Huelle nicht mehr bedienen (par.8.14)",
                "huelle": "bestpassende Orientierung je Rundenende (triangle_hull_coverage_probe.best_hull)",
                "alter": "Zahl der Rundenenden, an denen die Reihe gebunden lag (die volle zaehlt mit)",
                "enden": "voll_gelegt = am Rundenende voll und danach Zellgewinn in Rasterzeile r; voll_geraeumt = voll, aber kein Zellgewinn (unplatzierbar); chip_gelegt = nicht voll am Rundenende, aber Zellgewinn (Bonus-Chip im Tiling); geraeumt_oder_unklar = Reihe weg ohne Zellgewinn; offen_am_ende = am Spielende unvollstaendig; voll = voll am letzten Rundenende ohne Endzustand",
                "aussen_moeglich": "an einem blockierten Rundenende nimmt eine Zelle der Zeile AUSSERHALB der Huelle die Farbe an",
            },
            "episoden": len(eps_ok), "fehler": [e for e in episodes if "fehler" in e][:20],
            "zusammenfassung": ra,
        }
        for side, rows in ra.items():
            for row_key, v in rows.items():
                print(f"{side} {row_key}: Episoden {v['episoden']} | gelegt {v['gelegt_anteil']} (voll am Rundenende {v['voll_am_rundenende_anteil']}, per Chip {v['chip_gelegt_anteil']}) | geraeumt {v['geraeumt_anteil']} | offen am Ende {v['offen_am_ende_anteil']} | "
                      f"je blockiert {v['je_blockiert_anteil']} ({v['blockiert_rundenenden_mittel']} Rundenenden) | "
                      f"gelegt wenn blockiert {v['blockiert_gelegt_anteil']} gegen nie blockiert {v['nie_blockiert_gelegt_anteil']} | "
                      f"Praedikate {v['praedikat_je_rundenende']}", flush=True)
    except Exception as e:
        out["reihen_alter"] = {"fehler": str(e)[:200]}
        print(f"  Reihen-Alter-Auswertung fehlgeschlagen: {e!r}", flush=True)
    out["laufzeit"] = {"wanduhr_s": round(time.time() - t0, 1), "cpu_s": round(time.process_time(), 1), "threads": 1,
                       "s_je_partie": round((time.time() - t0) / max(1, games), 2)}
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=lambda o: sorted(o) if isinstance(o, (set, frozenset)) else str(o))
    print(f"Partien {games}, Rundenenden {out['rundenenden']}, Divergenzen {len(divergences)} | Artefakt: {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
