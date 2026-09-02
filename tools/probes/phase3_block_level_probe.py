# -*- coding: utf-8 -*-
"""PREREG_r5_value_calibration.md par.12 -- Phase-3-Stufe-0 auf BLOCK-Ebene.

Die Stufe-0-Tabelle (2026-09-01) rechnete die SE ueber die 400 Seiten je Arm
und die t-Werte als ungepaarte Quadratsumme, obwohl alle fuenf Laeufe denselben
Seed 20260931 tragen (Partie i hat ueberall denselben Start). Hier die
Rechnung, die die Projektregel verlangt: je Datei (10 Partien, ein Block)
volle Spalten je Seite gemittelt, dann die GEPAARTE Differenz Arm minus
Kontrolle je Block, t mit df = n_bloecke - 1. Die Seitenrechnung steht zum
Vergleich daneben.

Quelle der Spaltenzahl: `score_geo.col_fill` des Endzustands, wie in
tools/corpus_sanity_check.py (volle Spalte = Fuellstand >= 6).
"""
import argparse
import glob
import json
import math
import os
import re
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "tools"))
from corpus_io import load_records  # noqa: E402

ARMS = {
    "tor2a_kontrolle_400": "selfplay_tor2a-v23b01_*.pkl",
    "s100": "selfplay_p3s0-b01-s100_*.pkl",
    "calb20": "selfplay_p3s0-b01-calb20_*.pkl",
    "calb05": "selfplay_p3s0-b01-calb05_*.pkl",
    "pw01": "selfplay_p3s0-b01-pw01_*.pkl",
}
CONTROL = "tor2a_kontrolle_400"


def g_suffix(path):
    m = re.search(r"_g(\d+)\.pkl$", os.path.basename(path))
    return int(m.group(1)) if m else -1


def full_columns_per_side(path):
    """Liste der vollen Spalten je Seite (2 Eintraege je Partie) einer Datei."""
    finals = {}
    for r in load_records(path):
        if r.get("winner") is not None:
            finals[r.get("game_id")] = r
    out = []
    for gid in sorted(finals):
        st = finals[gid]["state"]
        for p in st["players"]:
            cf = (p.get("score_geo") or {}).get("col_fill") or []
            out.append(sum(1 for x in cf if x >= 6))
    return out


def mean_sd(xs):
    n = len(xs)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1)) if n > 1 else float("nan")
    return m, sd


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data-dir", default="data/archive_pre_v24",
                    help="Korpus-Ordner; seit 2026-09-02 liegen die Phase-3-Korpora unter "
                         "<Sicherungswurzel>/archive_pre_v24 (absoluten Pfad uebergeben)")
    ap.add_argument("--out", default="evaluations/artifacts/phase3_block_level.json")
    a = ap.parse_args()
    t0 = time.monotonic()

    per_arm = {}
    for arm, pat in ARMS.items():
        files = sorted(glob.glob(os.path.join(_ROOT, a.data_dir, pat)), key=g_suffix)
        if not files:
            raise SystemExit("Kein Korpus fuer " + arm + " (" + pat + ") unter " + a.data_dir)
        blocks = []
        sides = []
        for f in files:
            s = full_columns_per_side(f)
            sides.extend(s)
            blocks.append(sum(s) / len(s))
        per_arm[arm] = {"n_dateien": len(files), "n_seiten": len(sides),
                        "bloecke": blocks, "seiten": sides}
        print(arm + ": " + str(len(files)) + " Dateien, " + str(len(sides)) + " Seiten, "
              + "volle Spalten " + str(round(sum(sides) / len(sides), 4)), flush=True)

    ctrl = per_arm[CONTROL]
    result = {"prereg": "PREREG_r5_value_calibration.md par.12 (Block-Ebene, Nachtprogramm 2026-09-01 N4)",
              "kontrolle": CONTROL, "data_dir": a.data_dir, "arme": {}}
    for arm, d in per_arm.items():
        m_side, sd_side = mean_sd(d["seiten"])
        se_side = sd_side / math.sqrt(len(d["seiten"]))
        m_blk, sd_blk = mean_sd(d["bloecke"])
        se_blk = sd_blk / math.sqrt(len(d["bloecke"]))
        entry = {"volle_spalten": m_side, "se_seiten": se_side, "n_seiten": len(d["seiten"]),
                 "se_bloecke": se_blk, "n_bloecke": len(d["bloecke"])}
        if arm != CONTROL:
            nb = min(len(d["bloecke"]), len(ctrl["bloecke"]))
            diffs = [d["bloecke"][i] - ctrl["bloecke"][i] for i in range(nb)]
            md, sdd = mean_sd(diffs)
            se_d = sdd / math.sqrt(nb)
            t_paired = md / se_d if se_d > 0 else float("nan")
            # ungepaarte Seitenrechnung wie in der Erstfassung
            mc, sdc = mean_sd(ctrl["seiten"])
            se_c = sdc / math.sqrt(len(ctrl["seiten"]))
            t_unpaired = (m_side - mc) / math.sqrt(se_side ** 2 + se_c ** 2)
            entry.update({"differenz_zur_kontrolle": md, "se_differenz_bloecke": se_d,
                          "t_gepaart_bloecke": t_paired, "df": nb - 1,
                          "t_ungepaart_seiten_erstfassung": t_unpaired,
                          "differenz_je_block": diffs})
            print("  " + arm + " minus Kontrolle: " + str(round(md, 4)) + " (Block-SE "
                  + str(round(se_d, 4)) + ", t gepaart " + str(round(t_paired, 2))
                  + ", df " + str(nb - 1) + "; Erstfassung ungepaart t "
                  + str(round(t_unpaired, 2)) + ")", flush=True)
        result["arme"][arm] = entry

    result["laufzeit"] = {"wanduhr_s": round(time.monotonic() - t0, 1), "cpu_s": None,
                          "threads": 1, "s_je_partie": None}
    path = os.path.join(_ROOT, a.out)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
    print("Artefakt: " + path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
