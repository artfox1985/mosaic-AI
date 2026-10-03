# -*- coding: utf-8 -*-
"""tools/probes/tie_mirror_acceptance.py -- Abnahme des Spiegelknopfs (PREREG_tie_mirror.md par.3).

Punkt 2 (TOR): Anteil Partien mit `tie_mirrored: true` je Klasse, Grundmenge Hauptpartien
(Ausfluege `*_x1` erben den Wert und zaehlen nicht gesondert), Fenster 50 +- 3 Prozent bei p = 0,5.
Punkt 3 (BERICHTET): Anteil voller Spalten RECHTS (c4 + c5) an allen vollen Spalten, getrennt nach
`tie_mirrored`. Endbrett wie in `tools/corpus_sanity_check.py` (`score_geo.col_fill` des letzten
Records mit `winner`, Einheit Partie-Seite).

    python -X utf8 -u tools/probes/tie_mirror_acceptance.py --prefix v33-b01 \
        --out evaluations/artifacts/tie_mirror_acceptance_v34.json
"""
from __future__ import annotations

import argparse
import glob
import json
import math
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

CLASSES = ("policy", "value-wegc", "value-excursion")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--classes", nargs="+", default=list(CLASSES),
                    help="Klassen der Erzeugung (v35: value-deviate statt value-wegc, ohne policy)")
    args = ap.parse_args()
    t_start, c_start = time.monotonic(), time.process_time()
    out = {"prereg": "evaluations/PREREG_tie_mirror.md par.3", "prefix": args.prefix, "klassen": {}}
    n_total = 0
    for cls in args.classes:
        files = sorted(glob.glob(str(BASE_DIR / "data" / f"selfplay_{args.prefix}-{cls}_*.pkl")))
        mirrored: dict[str, set] = {}
        last: dict[str, dict] = {}
        for k, f in enumerate(files):
            for r in load_records(f):
                gid = str(r.get("game_id"))
                mirrored.setdefault(gid, set()).add(r.get("tie_mirrored"))
                if r.get("winner") is not None:
                    last[gid] = r
            if (k + 1) % 100 == 0 or k + 1 == len(files):
                print(f"[spiegel] {cls} {k + 1}/{len(files)} Dateien, {len(mirrored)} Partien, "
                      f"{time.monotonic() - t_start:.0f} s", flush=True)
        main_games = [g for g in mirrored if not g.endswith("_x1")]
        inconsistent = [g for g, v in mirrored.items() if len(v) != 1]
        missing = [g for g, v in mirrored.items() if v == {None}]
        n = len(main_games)
        k_true = sum(1 for g in main_games if mirrored[g] == {True})
        share = k_true / n if n else float("nan")
        se = math.sqrt(share * (1 - share) / n) if n else float("nan")
        # Punkt 3: volle Spalten je Index, getrennt nach tie_mirrored, alle beendeten Partien.
        cols = {True: [0] * 6, False: [0] * 6}
        sides = {True: 0, False: 0}
        for g, r in last.items():
            tm = next(iter(mirrored.get(g, {None})))
            if tm not in (True, False):
                continue
            for p in (r.get("state") or {}).get("players", []):
                cf = (p.get("score_geo") or {}).get("col_fill") or []
                if len(cf) != 6:
                    continue
                sides[tm] += 1
                for c in range(6):
                    cols[tm][c] += 1 if cf[c] >= 6 else 0
        def right_share(tm):
            tot = sum(cols[tm])
            return (cols[tm][4] + cols[tm][5]) / tot if tot else float("nan")
        out["klassen"][cls] = {
            "dateien": len(files), "hauptpartien": n, "ausfluege": len(mirrored) - n,
            "gespiegelt": k_true, "anteil_gespiegelt": share, "standardfehler": se,
            "tor_50_pm_3": bool(0.47 <= share <= 0.53),
            "partien_mit_uneinheitlichem_feld": len(inconsistent), "partien_ohne_feld": len(missing),
            "volle_spalten_je_index": {"gespiegelt": cols[True], "ungespiegelt": cols[False]},
            "seiten": {"gespiegelt": sides[True], "ungespiegelt": sides[False]},
            "anteil_rechts_c4c5": {"gespiegelt": right_share(True), "ungespiegelt": right_share(False)},
        }
        n_total += len(mirrored)
        print(f"[spiegel] {cls}: {k_true}/{n} Hauptpartien gespiegelt = {share:.4f} (SE {se:.4f}) "
              f"-> {'im Fenster' if out['klassen'][cls]['tor_50_pm_3'] else 'AUSSERHALB'}; "
              f"rechts c4+c5: gespiegelt {right_share(True):.3f}, ungespiegelt {right_share(False):.3f}; "
              f"uneinheitlich {len(inconsistent)}, ohne Feld {len(missing)}", flush=True)
    out["laufzeit"] = laufzeit_block(t_start, cpu_start=c_start, threads=1, n_units=n_total, unit="partie")
    op = BASE_DIR / args.out
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Ergebnis: {op} ({out['laufzeit']['wanduhr_s']} s)", flush=True)


if __name__ == "__main__":
    main()
