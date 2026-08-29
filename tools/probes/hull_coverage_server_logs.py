# -*- coding: utf-8 -*-
"""par.3b.8 Stufe D, Ergaenzung (Nutzer-Auftrag 2026-08-29): Huellen-Deckung
aus den SERVER-Spiellogs -- Mensch-gegen-Netz-Partien der Web-Oberflaeche,
die einzige Quelle mit gutem menschlichem Spiel (Memory: RMS-Marge ~21,
Mensch gewinnt fast immer; als Groessenordnungs-Beleg brauchbar, als
Verteilungsschaetzung nicht -- n ist klein).

Brett-Rekonstruktion: 1:1 wiederverwendet aus
tools/probes/column_build_structural_probe.py (reconstruct_game; dort gegen
die k1-Endwertung korrektheitsbewiesen). Huellen-Definition wie
triangle_hull_coverage_probe (r+c <= 5 bzw. gespiegelt, bestpassend am
Endbrett).

Aufruf:
    python -X utf8 -u tools/probes/hull_coverage_server_logs.py
"""
from __future__ import annotations

import glob
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools" / "probes"))
sys.path.insert(0, str(_ROOT / "tools"))

from column_build_structural_probe import reconstruct_game  # noqa: E402
from analyze_game_log import ROUND_PREFIX  # noqa: E402
from triangle_hull_coverage_probe import (HULL_LEFT, HULL_RIGHT,  # noqa: E402
                                          best_hull, deviation,
                                          forbidden_zone_stats, stufe_d2_metrics,
                                          weighted_fill_share)

ARTIFACT = _ROOT / "evaluations" / "artifacts" / "hull_coverage_server_logs.json"


def to_grid_cells(cells):
    return {(2 * tr + si // 2, 2 * tc + si % 2) for (tr, tc, si) in cells}


def main():
    rows = {"mensch": [], "ki": []}
    files = sorted(glob.glob(str(_ROOT / "static" / "log" / "game_*.log")))
    used = 0
    for f in files:
        lines = open(f, encoding="utf-8", errors="replace").read().split("\n")
        header = None
        for ln in lines:
            if ln.startswith("# {"):
                header = json.loads(ln[2:])
                break
        if header is None or not header.get("ai_enabled"):
            continue
        if not any("Endwertung" in ln for ln in lines):
            continue  # unfertige Partie
        used += 1
        cells_by_name = reconstruct_game(lines)
        # Runden-Bretter per KUMULATIVER Rekonstruktion (Stufe D2): jede
        # Zeile gehoert zur zuletzt gesehenen [R<n>]-Runde; reconstruct_game
        # wird auf dem Praefix bis Runde r wiederverwendet (keine zweite
        # Parser-Wahrheit).
        lines_by_round = {r: [] for r in range(1, 6)}
        cur = 1
        for ln in lines:
            m = ROUND_PREFIX.match(ln)
            if m:
                cur = min(int(m.group(1)), 5)
            lines_by_round[cur].append(ln)
        boards_by_name = {}
        prefix = []
        for r in range(1, 6):
            prefix.extend(lines_by_round[r])
            for name, cells in reconstruct_game(prefix).items():
                boards_by_name.setdefault(name, {0: set()})[r] = {
                    (2 * tr + si // 2, 2 * tc + si % 2) for (tr, tc, si) in cells}
        for name, b in boards_by_name.items():
            for r in range(1, 6):
                b.setdefault(r, b.get(r - 1, set()))
        players = header["players"]
        ai_idx = header["ai_player"]
        for idx, name in enumerate(players):
            role = "ki" if idx == ai_idx else "mensch"
            grid_cells = to_grid_cells(cells_by_name.get(name, set()))
            hull = (HULL_LEFT if deviation(grid_cells, HULL_LEFT)
                    <= deviation(grid_cells, HULL_RIGHT) else HULL_RIGHT)
            cf = [sum(1 for r in range(6) if (r, c) in grid_cells) for c in range(6)]
            boards = boards_by_name.get(name, {r: set() for r in range(6)})
            boards[0] = set()
            boards[5] = grid_cells  # Endbrett = volle Rekonstruktion
            d2 = stufe_d2_metrics(boards, hull)
            rows[role].append({
                "datei": pathlib.Path(f).name,
                "d2": d2,
                "huelle_fill": len(grid_cells & hull),
                "huelle_wfill": weighted_fill_share(grid_cells, hull),
                "aussen_fill": len(grid_cells - hull),
                "abweichung": deviation(grid_cells, hull),
                "volle_spalten": sum(1 for x in cf if x >= 6),
                "spalten_ge4": sum(1 for x in cf if x >= 4),
                "zone": forbidden_zone_stats(grid_cells, hull),
            })

    result = {"prereg": "par.3b.8 Stufe D Ergaenzung (Server-Logs)",
              "partien": used, "quellen": len(files), "seiten": {}}
    for role, rs in rows.items():
        n = len(rs)
        if not n:
            continue
        ge4 = sum(r["spalten_ge4"] for r in rs)
        result["seiten"][role] = {
            "n": n,
            "huelle_fill_mittel_von_21": sum(r["huelle_fill"] for r in rs) / n,
            "huelle_fuellanteil_kosten_gewichtet": sum(r["huelle_wfill"] for r in rs) / n,
            "aussen_fill_mittel_von_15": sum(r["aussen_fill"] for r in rs) / n,
            "abweichung_mittel": sum(r["abweichung"] for r in rs) / n,
            "volle_spalten_mittel": sum(r["volle_spalten"] for r in rs) / n,
            "vollendungsquote": (sum(r["volle_spalten"] for r in rs) / ge4) if ge4 else None,
            "zone_fehler_mittel": sum(r["zone"]["n"] for r in rs) / n,
        }
        taus = [r["d2"]["frontier_tau"] for r in rs if r["d2"]["frontier_tau"] is not None]
        result["seiten"][role]["stufe_d2"] = {
            "frontier_tau_mittel": (sum(taus) / len(taus)) if taus else None,
            "halbzeit_fill_mittel_von_21": sum(r["d2"]["halbzeit"]["fill3"] for r in rs) / n,
            "halbzeit_fuellanteil_kosten_gewichtet": sum(r["d2"]["halbzeit"]["fill3_gewichtet"] for r in rs) / n,
            "halbzeit_abweichung_mittel": sum(r["d2"]["halbzeit"]["dev3"] for r in rs) / n,
            "stabil_ab_runde_mittel": sum(r["d2"]["stabil_ab_runde"] for r in rs) / n,
            "fehlorientiert_vor_stabil_mittel": sum(r["d2"]["fehlorientiert_vor_stabil"] for r in rs) / n,
            "tote_huelle": "nicht rechenbar (Logs tragen keine Zustaende)",
        }
    ARTIFACT.write_text(json.dumps(result, indent=1, ensure_ascii=False),
                        encoding="utf-8", newline="\n")
    print(f"{used} fertige Partien von {len(files)} Logs")
    for role, s in result["seiten"].items():
        print(f"{role}: Huelle {s['huelle_fill_mittel_von_21']:.2f}/21 | "
              f"aussen {s['aussen_fill_mittel_von_15']:.2f}/15 | Abw. {s['abweichung_mittel']:.2f} | "
              f"volle Spalten {s['volle_spalten_mittel']:.2f} | Quote {s['vollendungsquote']:.3f} | "
              f"Zonen-Fehler {s['zone_fehler_mittel']:.2f}")
    print(f"Artefakt: {ARTIFACT}")


if __name__ == "__main__":
    main()
