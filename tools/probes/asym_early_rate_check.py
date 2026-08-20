# -*- coding: utf-8 -*-
"""Fruehwarnung nach Block S1 des Asym-Korpus (PREREG_asymmetric_curriculum par.11).

Prueft auf den fertigen S1-Dateien die k1-Raten-Differenz Zwangsseite gegen
freie Seite. Die VERBINDLICHE Sperre (par.5, >= 20 pp) laeuft unveraendert auf
dem fertigen Korpus — dieses Gate hat nur eine ABBRUCH-Option: liegt die
Differenz nach 4.000 Partien unter --abbruch-pp (Default 10), lohnen die
restlichen ~20 h nicht (Exit 1 stoppt die Kette).

Zwangsseite je Partie aus den `[asym_vorzug]`-Zeilen des tee-Logs
(game_id -> zwangsseite); k1-Abschluss je Seite aus dem letzten Zustand jeder
Partie ueber `mosaic_rust.plate_completability_json` (col_fill == 6).

    python -X utf8 tools/probes/asym_early_rate_check.py \
        --korpus "data/asym_corpus/selfplay_v21_asymS_*.pkl" --log logs/asym_corpus_<datum>.log
"""
from __future__ import annotations

import argparse
import glob
import json
import pickle
import re
from pathlib import Path

BASIS = Path(__file__).resolve().parents[2]
ZEILE = re.compile(r"\[asym_vorzug\] game_id=(\S+) seed=\d+ zwangsseite=(\d)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--korpus", required=True, help="Glob der S1-Dateien")
    ap.add_argument("--log", required=True, help="tee-Log mit den [asym_vorzug]-Zeilen")
    ap.add_argument("--abbruch-pp", type=float, default=10.0)
    a = ap.parse_args()

    import mosaic_rust as mr  # noqa: PLC0415

    zwang = {}
    for m in ZEILE.finditer(Path(a.log).read_text(encoding="utf-8", errors="replace")):
        zwang[m.group(1)] = int(m.group(2))

    n = 0
    treffer = {"zwang": 0, "frei": 0}
    ohne_zuordnung = 0
    for f in sorted(glob.glob(str(BASIS / a.korpus))):
        data = pickle.load(open(f, "rb"))
        letzte = {}
        for s in data:
            letzte[s.get("game_id")] = s.get("state")
        for gid, st in letzte.items():
            seite = zwang.get(gid)
            if seite is None:
                ohne_zuordnung += 1
                continue
            n += 1
            for sp in (0, 1):
                d = json.loads(mr.plate_completability_json(json.dumps(st), sp))
                hat = any(fill == 6 for fill in d["col_fill"])
                if hat:
                    treffer["zwang" if sp == seite else "frei"] += 1
    if n == 0:
        raise SystemExit("keine Partien mit Seiten-Zuordnung -- Log-Pfad pruefen")
    rz = 100 * treffer["zwang"] / n
    rf = 100 * treffer["frei"] / n
    diff = rz - rf
    print(f"  {n} Partien ({ohne_zuordnung} ohne Log-Zuordnung uebersprungen)")
    print(f"  k1-Rate Zwangsseite {rz:.1f} %  |  freie Seite {rf:.1f} %  |  Differenz {diff:+.1f} pp")
    print(f"  (par.5-Sperre spaeter: >= 20 pp auf dem GESAMT-Korpus; Fruehwarn-Abbruch: < {a.abbruch_pp} pp)")
    if diff < a.abbruch_pp:
        print("  FRUEHWARNUNG VERLETZT -- Kette wird abgebrochen.")
        raise SystemExit(1)
    print("  FRUEHWARNUNG BESTANDEN -- Kette laeuft weiter.")


if __name__ == "__main__":
    main()
