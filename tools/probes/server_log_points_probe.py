# -*- coding: utf-8 -*-
"""Punktbilanz der Server-Partien Mensch gegen KI, je Runde und Kategorie
(Nutzer 2026-09-05: "die meisten Punkte kommen aus Runde 3+", "du hast viel mehr
Server-Logs fuer die Analyse").

Liest `static/log/game_*.log` (nur abgeschlossene Partien mit Endwertung) und
zaehlt je Seite und Runde: Tiling-Punkte (🎯), Kuppelbonus (⭐ Spezial-Punkte),
Strafleiste, Ziehkosten (📦 Stapel), Startspielerstein (❖), dazu die Endwertung
gesamt und nach Kategorie (Zeilen der Endwertungs-Aufschluesselung). Die
KI-Modelle der Logs koennen gemischt sein (aeltere Champions); das Artefakt
nennt die Dateien.

Aufruf:
    python -X utf8 -u tools/probes/server_log_points_probe.py
    python -X utf8 -u tools/probes/server_log_points_probe.py --pattern "static/log/game_20260904_*.log"
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import time
from collections import defaultdict

PATTERNS = {
    "tiling": (re.compile(r"^\[R(\d)\] 🎯 (Spieler 1|Spielerin|KI): \+(\d+) Pkt \(Reihe"), +1),
    "kuppelbonus": (re.compile(r"^\[R(\d)\] ⭐ (Spieler 1|Spielerin|KI): \+(\d+) Spezial-Punkte"), +1),
    "strafe": (re.compile(r"^\[R(\d)\] (Spieler 1|Spielerin|KI): Strafe -(\d+) Pkt"), -1),
    "ziehen": (re.compile(r"^\[R(\d)\] 📦 (Spieler 1|Spielerin|KI): .*−(\d+) Pkt"), -1),
    "marker": (re.compile(r"^\[R(\d)\] ❖ (Spieler 1|Spielerin|KI): Startspielerstein genommen \(−(\d+) Pkt"), -1),
}
END = re.compile(r"^\[R5\] 🏆 (Spieler 1|Spielerin|KI): Endwertung (-?\d+) Pkt → Gesamt: (\d+) Pkt")
END_CAT = re.compile(r"^\[R5\]\s+(\S+ [^:]+): (-?\d+) Pkt")


def side(name: str) -> str:
    return "KI" if name == "KI" else "Mensch"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pattern", default="static/log/game_*.log")
    ap.add_argument("--out", default="evaluations/artifacts/server_log_points_probe.json")
    a = ap.parse_args()
    t0 = time.time()
    files = []
    agg = defaultdict(lambda: defaultdict(float))
    finals = defaultdict(list)
    endcat = defaultdict(lambda: defaultdict(float))
    for f in sorted(glob.glob(a.pattern)):
        lines = open(f, encoding="utf-8", errors="replace").read().splitlines()
        if not any("Endwertung" in l for l in lines):
            continue
        files.append(os.path.basename(f))
        current = None
        for l in lines:
            hit = False
            for key, (pat, sign) in PATTERNS.items():
                m = pat.match(l)
                if m:
                    agg[side(m.group(2))][f"R{m.group(1)} {key}"] += sign * int(m.group(3))
                    hit = True
                    break
            if hit:
                continue
            m = END.match(l)
            if m:
                who = side(m.group(1))
                agg[who]["Endwertung"] += int(m.group(2))
                finals[who].append(int(m.group(3)))
                current = who
                continue
            m = END_CAT.match(l)
            if m and current:
                endcat[current][m.group(1)] += int(m.group(2))
    n = len(files)
    if n == 0:
        raise SystemExit(f"keine abgeschlossenen Partien unter {a.pattern}")
    out = {"prereg": "PREREG_special_tile_yield.md par.8; PREREG_geometric_envelope.md par.8.10",
           "partien": n, "dateien": files, "seiten": {}}
    for who in ("Mensch", "KI"):
        d = agg[who]
        fin = sum(finals[who]) / max(1, len(finals[who]))
        rows = {}
        cum = 0.0
        for r in range(1, 6):
            vals = {k: d.get(f"R{r} {k}", 0.0) / n for k in PATTERNS}
            net = sum(vals.values())
            cum += net
            rows[f"R{r}"] = {**{k: round(v, 2) for k, v in vals.items()}, "netto": round(net, 2), "kumuliert": round(cum, 2)}
        out["seiten"][who] = {
            "endstand_mittel": round(fin, 2), "n_endwertungen": len(finals[who]),
            "je_runde": rows,
            "endwertung_mittel": round(d.get("Endwertung", 0.0) / n, 2),
            "endwertung_nach_kategorie": {k: round(v / max(1, len(finals[who])), 2) for k, v in endcat[who].items()},
            "kuppelbonus_gesamt": round(sum(d.get(f"R{r} kuppelbonus", 0.0) for r in range(1, 6)) / n, 2),
            "tiling_gesamt": round(sum(d.get(f"R{r} tiling", 0.0) for r in range(1, 6)) / n, 2),
            "anteil_r1_r2_netto_am_endstand": round(100 * rows["R2"]["kumuliert"] / fin, 1) if fin else None,
        }
        print(f"{who}: Endstand {fin:.1f} | Tiling {out['seiten'][who]['tiling_gesamt']:.1f} | Kuppelbonus "
              f"{out['seiten'][who]['kuppelbonus_gesamt']:.1f} | Endwertung {out['seiten'][who]['endwertung_mittel']:.1f} "
              f"{out['seiten'][who]['endwertung_nach_kategorie']}")
        for r, row in rows.items():
            print(f"   {r}: {row}")
    out["laufzeit"] = {"wanduhr_s": round(time.time() - t0, 2), "cpu_s": round(time.process_time(), 2), "threads": 1}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(f"Artefakt: {a.out} ({n} Partien)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
