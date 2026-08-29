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

from column_build_structural_probe import reconstruct_game  # noqa: E402
from triangle_hull_coverage_probe import (HULL_LEFT, HULL_RIGHT,  # noqa: E402
                                          deviation, forbidden_zone_stats)

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
        players = header["players"]
        ai_idx = header["ai_player"]
        for idx, name in enumerate(players):
            role = "ki" if idx == ai_idx else "mensch"
            grid_cells = to_grid_cells(cells_by_name.get(name, set()))
            hull = (HULL_LEFT if deviation(grid_cells, HULL_LEFT)
                    <= deviation(grid_cells, HULL_RIGHT) else HULL_RIGHT)
            cf = [sum(1 for r in range(6) if (r, c) in grid_cells) for c in range(6)]
            rows[role].append({
                "datei": pathlib.Path(f).name,
                "huelle_fill": len(grid_cells & hull),
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
            "aussen_fill_mittel_von_15": sum(r["aussen_fill"] for r in rs) / n,
            "abweichung_mittel": sum(r["abweichung"] for r in rs) / n,
            "volle_spalten_mittel": sum(r["volle_spalten"] for r in rs) / n,
            "vollendungsquote": (sum(r["volle_spalten"] for r in rs) / ge4) if ge4 else None,
            "zone_fehler_mittel": sum(r["zone"]["n"] for r in rs) / n,
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
