# -*- coding: utf-8 -*-
"""PREREG_heuristic_v2_long_rows.md par.3b.6 -- Auswertung der
Ownership-Pol-Konsument-Arena (MOSAIC_OWNERSHIP_TILING_W-Sweep mit b01-Kopf).

Liest die vier Arm-Korpora `data/selfplay_otw22b01w{00,05,10,20}_*.pkl`
(je 10 Dateien a 20 Partien, argmax-Instrument des Spalten-Tors) und rechnet
die vorregistrierten Masse:

* volle Spalten je Partie und Seite (`score_geo.col_fill` >= 6 am Endbrett),
* Vollendungsquote (Anzahl ==6 je Anzahl >=4, Definition wie
  `spalten_tor_v22.json`),
* gepaarter Block-t ueber die 10 Dateibloecke gegen den w0-Arm (Paarung ueber
  den Blockindex; Seeds identisch ueber die Arme), Schwelle |t| > 2,262 (df=9),
* Punkte-Waechter: eigene Punkte je Block, gepaart gegen w0 (Tor-Bedingung:
  kein signifikanter Punkteverlust).

Dazu die sechs Standard-Kennzahlen (CLAUDE.md 2026-08-23) je Arm aus den
pkl-Endzustaenden -- Feld-Herkunft identisch zu tools/corpus_sanity_check.py:
Endzustand = letzter Record mit `winner` je `game_id`; `score_geo.row_fill`/
`col_fill`; Strafleiste = Summe der Runden-Maxima der `floor`-Laenge;
`scoring_tile_points` je aktivem Kriterium; `scores`. Die Marge zum Gegner
entfaellt strukturell (Self-Play desselben Modells, der Knopf wirkt auf beide
Seiten) -- berichtet wird das Punkte-Niveau je Seite.

Instrument-Waechter (par.3b.6): ein w>0-Arm, der ZAHLENGLEICH mit w0 endet,
heisst "Knopf kam nicht an" (ALARM, kein H0-Befund). Der w0-Arm muss die
b01-Werte aus par.3b.2 reproduzieren (0,2975 volle Spalten).

Artefakt: evaluations/artifacts/ownership_tiling_consumer_v22.json
(inkl. laufzeit-Bloecke der Lauf-Manifeste je Arm und eigener Laufzeit).

Aufruf (reine Datenpassage, kein Netz, keine Engine):
    python -u tools/probes/ownership_tiling_consumer_eval.py
Smoke:
    python -u tools/probes/ownership_tiling_consumer_eval.py --limit 2
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import pathlib
import re
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from corpus_io import load_records  # noqa: E402

DATA_DIR = _ROOT / "data"
ARTIFACT = _ROOT / "evaluations" / "artifacts" / "ownership_tiling_consumer_v22.json"
PREREG = "PREREG_heuristic_v2_long_rows.md par.3b.6"

# Arm -> (Dateipraefix, gesetztes Env beim Lauf). Das Env steht hier
# ausdruecklich mit im Artefakt, weil das Lauf-Manifest Env-Knoepfe nicht
# erfasst (par.3b.6, Waechter 1).
ARMS = {
    "w00": ("selfplay_otw22b01w00_", "MOSAIC_OWNERSHIP_TILING_W=0"),
    "w05": ("selfplay_otw22b01w05_", "MOSAIC_OWNERSHIP_TILING_W=0.5"),
    "w10": ("selfplay_otw22b01w10_", "MOSAIC_OWNERSHIP_TILING_W=1.0"),
    "w20": ("selfplay_otw22b01w20_", "MOSAIC_OWNERSHIP_TILING_W=2.0"),
}
CONTROL = "w00"
T_THRESHOLD = 2.262  # df=9, zweiseitig 5 Prozent
FULL = 6
INIT = 4


def game_number(path: str) -> int:
    m = re.search(r"_g(\d+)\.pkl$", path)
    return int(m.group(1)) if m else 0


def newest_per_game_number(paths):
    """Je Partie-Nummer (g-Suffix) NUR die neueste Datei (Zeitstempel im
    Namen, datumsuebergreifend lexikographisch vergleichbar). Grund: der
    abgebrochene Erstlauf vom 2026-08-28 liegt lastkontaminiert im selben
    Praefix-Glob; ein Neustart unter gleichem Tag darf nicht gemischt
    werden (STATUS-Abschnitt zum Abbruch)."""
    best = {}
    dropped = 0
    for p in paths:
        m = re.search(r"_(\d{8}_\d{4})_g(\d+)\.pkl$", os.path.basename(p))
        if not m:
            continue
        ts, g = m.group(1), int(m.group(2))
        if g not in best or ts > best[g][0]:
            if g in best:
                dropped += 1
            best[g] = (ts, p)
        else:
            dropped += 1
    if dropped:
        print(f"  {dropped} aeltere Datei(en) je Partie-Nummer verworfen "
              f"(Erstlauf-Reste)", flush=True)
    return [p for _, p in sorted(best.values(), key=lambda x: game_number(x[1]))]


def mean(v):
    return sum(v) / len(v) if v else float("nan")


def sd(v):
    if len(v) < 2:
        return float("nan")
    m = mean(v)
    return (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5


def block_se(block_means):
    return sd(block_means) / math.sqrt(len(block_means))


def paired_t(a_blocks, b_blocks):
    """Gepaarter t ueber Blockindex: t, delta, se."""
    assert len(a_blocks) == len(b_blocks)
    d = [a - b for a, b in zip(a_blocks, b_blocks)]
    m, s = mean(d), sd(d)
    se = s / math.sqrt(len(d))
    return (m / se if se > 0 else float("inf") if m != 0 else 0.0), m, se


def eval_arm(prefix: str, limit: int | None):
    files = newest_per_game_number(glob.glob(str(DATA_DIR / f"{prefix}*.pkl")))
    if limit:
        files = files[:limit]
    if not files:
        return None
    blocks = []          # je Datei: dict der Blockwerte
    per_side = {         # arm-weit je Partie+Seite
        "full_cols": [], "cols_ge4": [], "cols_ge3": [], "col_max": [],
        "full_rows": [], "row_fill_mean": [], "points": [], "floor_stones": [],
    }
    tile_points = {i: [] for i in range(8)}
    tile_active = {i: 0 for i in range(8)}
    games_total = 0
    for f in files:
        recs = load_records(f)
        finals = {}
        floor_max = {}
        for r in recs:
            gid = r.get("game_id")
            st = r.get("state") or {}
            for pi, p in enumerate(st.get("players", [])):
                k = (gid, pi, st.get("round"))
                floor_max[k] = max(floor_max.get(k, 0), len(p.get("floor") or []))
            if r.get("winner") is not None:
                finals[gid] = r
        floor_per_side = {}
        for (g, pi, _rnd), v in floor_max.items():
            floor_per_side[(g, pi)] = floor_per_side.get((g, pi), 0) + v

        b_full, b_ge4, b_points = [], [], []
        for gid, r in finals.items():
            st = r["state"]
            games_total += 1
            ids = st.get("scoring_tile_ids") or []
            for i in ids:
                tile_active[i] += 1
            sc = r.get("scores") or [p.get("score") for p in st["players"]]
            for pi, p in enumerate(st["players"]):
                geo = p.get("score_geo") or {}
                cf = geo.get("col_fill") or []
                rf = geo.get("row_fill") or []
                full = sum(1 for x in cf if x >= FULL)
                ge4 = sum(1 for x in cf if x >= INIT)
                per_side["full_cols"].append(full)
                per_side["cols_ge4"].append(ge4)
                per_side["cols_ge3"].append(sum(1 for x in cf if x >= 3))
                per_side["col_max"].append(max(cf) if cf else 0)
                per_side["full_rows"].append(sum(1 for x in rf if x >= FULL))
                per_side["row_fill_mean"].append(mean(rf) if rf else 0.0)
                per_side["points"].append(sc[pi])
                per_side["floor_stones"].append(floor_per_side.get((gid, pi), 0))
                stp = p.get("scoring_tile_points") or []
                for i in ids:
                    if i < len(stp):
                        tile_points[i].append(stp[i])
                b_full.append(full)
                b_ge4.append(ge4)
                b_points.append(sc[pi])
        blocks.append({
            "file": os.path.basename(f),
            "full_cols": mean(b_full),
            "quota": (sum(b_full) / sum(b_ge4)) if sum(b_ge4) else float("nan"),
            "points": mean(b_points),
        })
        print(f"  {os.path.basename(f)}: {len(finals)} Partien, "
              f"volle Spalten {mean(b_full):.3f}", flush=True)

    full_blocks = [b["full_cols"] for b in blocks]
    return {
        "files": len(files),
        "games": games_total,
        "volle_spalten": mean(per_side["full_cols"]),
        "block_se": block_se(full_blocks),
        "quota_ge4": (sum(per_side["full_cols"]) / sum(per_side["cols_ge4"]))
                     if sum(per_side["cols_ge4"]) else float("nan"),
        "init4_seite": mean(per_side["cols_ge4"]),
        "standard_kennzahlen": {
            "reihen": {"volle_reihen": mean(per_side["full_rows"]),
                        "fuellstand_mittel": mean(per_side["row_fill_mean"])},
            "spalten": {"voll": mean(per_side["full_cols"]),
                         "ge4": mean(per_side["cols_ge4"]),
                         "ge3": mean(per_side["cols_ge3"]),
                         "max_hoehe": mean(per_side["col_max"])},
            "strafleiste_steine": mean(per_side["floor_stones"]),
            "punkte_je_platte": {f"k{i}": mean(tile_points[i])
                                  for i in range(8) if tile_active[i]},
            "eigene_punkte": mean(per_side["points"]),
            "marge": "strukturell entfallen (Self-Play desselben Modells, "
                      "Knopf wirkt auf beide Seiten); Niveau-Vergleich siehe "
                      "punkte_vs_w0",
        },
        "_blocks": blocks,
    }


def run_manifests(prefix_tag: str):
    """laufzeit-Bloecke der Lauf-Manifeste des Arms (data/manifest_<tag>_*)."""
    out = []
    for f in sorted(glob.glob(str(DATA_DIR / f"manifest_{prefix_tag}_*.json"))):
        try:
            m = json.load(open(f, encoding="utf-8"))
            out.append({"manifest": os.path.basename(f),
                        "laufzeit": m.get("laufzeit")})
        except Exception as e:
            out.append({"manifest": os.path.basename(f), "fehler": repr(e)})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--limit", type=int, default=None,
                    help="nur die ersten N Dateien je Arm (Smoke)")
    args = ap.parse_args()
    t0 = time.time()

    arms = {}
    for name, (prefix, env) in ARMS.items():
        print(f"Arm {name} ({env}):", flush=True)
        r = eval_arm(prefix, args.limit)
        if r is None:
            print(f"  KEINE Dateien fuer {prefix} -- Arm fehlt.", flush=True)
            continue
        r["env"] = env
        arms[name] = r

    result = {
        "prereg": PREREG,
        "modell": "alphazero_v22-b01_best.onnx",
        "instrument": "self_play.py --mode network --deterministic "
                      "--no-root-noise --sims 400 --games 200 --per-file 20 "
                      "--seed 20260828 --threads 11 (argmax, wie par.3b.2)",
        "quota_definition": "col_fill==6 / col_fill>=4 am Endbrett, "
                            "je Partie und Seite",
        "schwelle_t": T_THRESHOLD,
        "bloecke": None,
        "arms": {},
        "vergleiche": {},
    }
    for name, r in arms.items():
        result["arms"][name] = {k: v for k, v in r.items() if k != "_blocks"}

    if CONTROL in arms:
        ctrl = arms[CONTROL]["_blocks"]
        result["bloecke"] = len(ctrl)
        for name, r in arms.items():
            if name == CONTROL:
                continue
            b = r["_blocks"]
            if len(b) != len(ctrl):
                result["vergleiche"][name] = {
                    "fehler": f"Blockzahl {len(b)} != Kontrolle {len(ctrl)}"}
                continue
            cmp_out = {}
            for metric, key in (("volle_spalten", "full_cols"),
                                ("quota", "quota"),
                                ("punkte", "points")):
                t, d, se = paired_t([x[key] for x in b],
                                    [x[key] for x in ctrl])
                cmp_out[f"{metric}_vs_w0"] = {"delta": d, "se": se, "t": t}
            # Waechter 1: Zahlengleichheit mit w0 = Knopf kam nicht an.
            identical = all(abs(x["full_cols"] - y["full_cols"]) < 1e-12
                            and abs(x["points"] - y["points"]) < 1e-12
                            for x, y in zip(b, ctrl))
            cmp_out["waechter_zahlengleich_mit_w0"] = identical
            result["vergleiche"][name] = cmp_out

    result["lauf_manifeste"] = {
        name: run_manifests(f"otw22b01{name}") for name in arms
    }
    result["laufzeit_auswertung"] = {
        "wanduhr_s": round(time.time() - t0, 1), "cpu_s": None,
        "threads": 1, "s_je_partie": None,
    }

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1, ensure_ascii=False)
    print(f"\nArtefakt geschrieben: {ARTIFACT}", flush=True)

    for name, cmp_out in result["vergleiche"].items():
        vs = cmp_out.get("volle_spalten_vs_w0")
        if vs:
            print(f"{name}: volle Spalten delta {vs['delta']:+.4f} "
                  f"t {vs['t']:+.2f} | Punkte t "
                  f"{cmp_out['punkte_vs_w0']['t']:+.2f} | zahlengleich: "
                  f"{cmp_out['waechter_zahlengleich_mit_w0']}", flush=True)


if __name__ == "__main__":
    main()
