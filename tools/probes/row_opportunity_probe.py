#!/usr/bin/env python
"""PREREG_long_row_payoff.md par.2a, Stufe 2: Initiierung NORMIERT auf Gelegenheit.

Stufe 1 (`row_initiation_probe.py`) hat einen auffaelligen Zickzack im Anteil
"Initiierung geht in eine lange Reihe" gefunden (Champion R1-R5:
21,8 / 27,7 / 2,1 / 13,7 / 20,5 %; Heuristik 33,4 / 5,3 / 12,8 / 17,1 / 17,5 %).

**Dieser Anteil ist aber konfundiert**: eine lange Reihe laesst sich nur
INITIIEREN, wenn sie gerade leer ist. Wer in R2 viele lange Reihen anfaengt,
kann sie in R3 nicht mehr initiieren -- der R3-Einbruch koennte also reine
Belegung sein und gar keine Praeferenz. Diese Sonde normiert deshalb auf die
GELEGENHEIT:

    Rate(Runde) = initiierte lange Reihen / zu Rundenbeginn LEERE lange Reihen

Rekonstruktion der Belegung, vollstaendig aus dem Log:
  - Stein-Zug in Reihe R: fill[R] += (n - overflow)
  - Rundenende: Reihen, die in einer `TILING_SCORE`-Zeile
    (`Pokal-Emoji Name: +N Pkt (Reihe R -> Kuppel ...)`) oder einer
    `CHIPS_COMPLETE`-Zeile auftauchen, wurden vollendet und werden auf 0
    gesetzt; alle uebrigen behalten ihren Fuellstand (Uebertrag).

SELBSTTEST (laeuft vor jeder Kennzahl, hart abbrechend): die rekonstruierte
Belegung muss fuer JEDEN Zug den aus dem Log gelesenen Fuellstand
unabhaengig reproduzieren -- `fill_rekonstruiert_vorher + platziert ==
fill_aus_log_nachher`. Zwei unabhaengige Ableitungen derselben Groesse.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from analyze_game_log import PATTERNS, ROUND_PREFIX  # noqa: E402
from plate_points_from_arena import game_list  # noqa: E402

EVAL = ROOT / "evaluations"
OUT_JSON = EVAL / "artifacts" / "row_opportunity_probe.json"

TAKE_CATS = ("SUN_TAKE", "MOON_GLOBAL_TAKE")
LONG_ROWS = (5, 6)
SHORT_ROWS = (1, 2, 3)
ALL_ROWS = (1, 2, 3, 4, 5, 6)
RNG = np.random.default_rng(20260824)
N_BOOT = 1000


class Mismatch(Exception):
    pass


def walk_game(log_lines):
    """Rekonstruiert Reihenbelegung je Spieler und liefert je Runde:
    {(name, runde): dict(leer_lang=..., leer_kurz=..., init_lang=...,
                         init_kurz=..., ...)}
    Wirft `Mismatch`, wenn die Rekonstruktion vom Log abweicht."""
    fill = defaultdict(lambda: defaultdict(int))   # name -> row -> fill
    per_round = {}
    completed_this_round = defaultdict(set)
    cur_round = None
    snapshot_taken = set()

    def snapshot(rnd):
        """Leere Reihen zu Rundenbeginn festhalten (einmal je Runde/Spieler
        beim ERSTEN Zug dieses Spielers in der Runde)."""
        pass

    for roh in log_lines:
        if roh.startswith("#"):
            continue
        m = ROUND_PREFIX.match(roh)
        text = m.group(2) if m else roh
        rnd = int(m.group(1)) if m else cur_round
        if rnd != cur_round:
            cur_round = rnd
        # --- Rundenende: vollendete Reihen leeren ---
        mm = PATTERNS["TILING_SCORE"].match(text)
        if mm:
            completed_this_round[mm.group("name")].add(int(mm.group("row")))
            continue
        mm = PATTERNS["CHIPS_COMPLETE"].match(text)
        if mm:
            completed_this_round[mm.group("name")].add(int(mm.group("row")))
            continue
        mm = PATTERNS["ROUND_START"].match(text)
        if mm:
            for name, rows in completed_this_round.items():
                for r in rows:
                    fill[name][r] = 0
            completed_this_round.clear()
            snapshot_taken.clear()
            continue
        # --- Stein-Zug ---
        for cat in TAKE_CATS:
            mm = PATTERNS[cat].match(text)
            if not mm:
                continue
            name = mm.group("name")
            dest = mm.group("dest")
            key = (name, rnd)
            if key not in snapshot_taken:
                snapshot_taken.add(key)
                per_round[key] = dict(
                    leer_lang=sum(1 for r in LONG_ROWS if fill[name][r] == 0),
                    leer_kurz=sum(1 for r in SHORT_ROWS if fill[name][r] == 0),
                    leer_alle=sum(1 for r in ALL_ROWS if fill[name][r] == 0),
                    init_lang=0, init_kurz=0, init_alle=0,
                    zuege=0,
                )
            per_round[key]["zuege"] += 1
            if not dest.startswith("Reihe"):
                break
            row = int(dest.split()[1])
            n = int(mm.group("n"))
            overflow = int(mm.group("overflow") or 0)
            platziert = n - overflow
            vorher = fill[name][row]
            fill_log = mm.group("fill")
            if fill_log is not None and vorher + platziert != int(fill_log):
                raise Mismatch(
                    f"Rekonstruktion weicht ab: {name} Reihe {row} runde {rnd} -- "
                    f"rekonstruiert vorher={vorher} + platziert={platziert} "
                    f"!= log fill={fill_log}")
            fill[name][row] = vorher + platziert
            if vorher == 0:
                per_round[key]["init_alle"] += 1
                if row in LONG_ROWS:
                    per_round[key]["init_lang"] += 1
                elif row in SHORT_ROWS:
                    per_round[key]["init_kurz"] += 1
            break
    return per_round


def collect(path, arm, side_filter):
    """{label: {(seed, runde): counters}}, plus Mismatch-Zaehler."""
    out = defaultdict(dict)
    n_games = defaultdict(set)
    n_mismatch = 0
    n_total = 0
    for sp in game_list(path, arm):
        seed = sp.get("game_seed")
        n_total += 1
        try:
            per_round = walk_game(sp.get("log") or [])
        except Mismatch:
            n_mismatch += 1
            continue
        for (name, rnd), c in per_round.items():
            lab = side_filter(name)
            if lab is None:
                continue
            out[lab][(seed, rnd)] = c
            n_games[lab].add(seed)
    return out, {k: len(v) for k, v in n_games.items()}, n_mismatch, n_total


def rate_for(cells, rnd=None):
    """Gelegenheits-normierte Rate: Summe init_lang / Summe leer_lang."""
    sel = [c for (s, r), c in cells.items() if rnd is None or r == rnd]
    init = sum(c["init_lang"] for c in sel)
    chance = sum(c["leer_lang"] for c in sel)
    return (init / chance if chance else None), init, chance


def bootstrap_rate(cells, rnd=None):
    by_seed = defaultdict(list)
    for (s, r), c in cells.items():
        if rnd is None or r == rnd:
            by_seed[s].append(c)
    seeds = list(by_seed)
    if len(seeds) < 10:
        return None
    vals = []
    for _ in range(N_BOOT):
        pick = RNG.choice(len(seeds), size=len(seeds), replace=True)
        init = sum(c["init_lang"] for i in pick for c in by_seed[seeds[i]])
        chance = sum(c["leer_lang"] for i in pick for c in by_seed[seeds[i]])
        if chance:
            vals.append(init / chance)
    if not vals:
        return None
    a = np.array(vals)
    return dict(mean=round(float(a.mean()), 4), p2_5=round(float(np.percentile(a, 2.5)), 4),
                p97_5=round(float(np.percentile(a, 97.5)), 4))


def summarize(cells):
    out = {}
    for rnd in (None, 1, 2, 3, 4, 5):
        lbl = "gesamt" if rnd is None else f"R{rnd}"
        rate, init, chance = rate_for(cells, rnd)
        out[lbl] = dict(
            rate_init_lang_je_gelegenheit=round(rate, 4) if rate is not None else None,
            n_init_lang=init, n_gelegenheiten_lang=chance,
            bootstrap_95ci=bootstrap_rate(cells, rnd),
        )
    return out


def main():
    result = {}
    p_a02 = EVAL / "artifacts" / "paired_arena_env_imm_a02.json"
    for arm in ("0", "0.2"):
        cells, ngames, nmis, ntot = collect(
            p_a02, arm,
            lambda n: "Champion" if n == "Netz" else ("Heuristik" if n == "Heuristik" else None))
        if nmis:
            print(f"  WARNUNG arm{arm}: {nmis}/{ntot} Partien wegen "
                  f"Rekonstruktions-Abweichung verworfen", file=sys.stderr)
        else:
            print(f"  Selbsttest arm{arm}: Rekonstruktion stimmt in ALLEN "
                  f"{ntot} Partien mit dem Log ueberein.", file=sys.stderr)
        result[f"champion_vs_heuristik_arm{arm}"] = {
            lab: dict(n_partien=ngames.get(lab, 0), **summarize(c))
            for lab, c in cells.items()
        }
        result[f"champion_vs_heuristik_arm{arm}"]["_selbsttest"] = dict(
            n_partien_gesamt=ntot, n_verworfen_mismatch=nmis)

    for fname, key in (("paired_arena_env_imm_netvnet.json", "netvnet"),
                       ("paired_arena_env_imm_netvnet_swap.json", "netvnet_swap")):
        p = EVAL / "artifacts" / fname
        if not p.exists():
            continue
        d = json.load(open(p, encoding="utf-8"))

        def lab_of(spec):
            s = str(spec)
            return "alpha0.2" if "imm_a02" in s else ("frozen" if "frozen" in s else f"?{s}")

        la, lb = lab_of(d["spec_a"]), lab_of(d["spec_b"])
        cells, ngames, nmis, ntot = collect(
            p, None, lambda n, a=la, b=lb: a if n == "NetzA" else (b if n == "NetzB" else None))
        if nmis:
            print(f"  WARNUNG {key}: {nmis}/{ntot} Partien verworfen", file=sys.stderr)
        result[key] = {lab: dict(n_partien=ngames.get(lab, 0), **summarize(c))
                       for lab, c in cells.items()}
        result[key]["_selbsttest"] = dict(n_partien_gesamt=ntot, n_verworfen_mismatch=nmis)

    result["_meta"] = dict(
        frage="Initiierung langer Reihen, NORMIERT auf Gelegenheit (leere "
              "lange Reihen zu Rundenbeginn) -- entkonfundiert den Zickzack "
              "aus row_initiation_probe.py.",
        selbsttest="Rekonstruierte Belegung muss den Log-Fuellstand jedes "
                   "Zuges unabhaengig reproduzieren; abweichende Partien "
                   "werden verworfen und gezaehlt.",
    )
    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    buckets = ("gesamt", "R1", "R2", "R3", "R4", "R5")
    print(f"\n{'Quelle/Seite':38s} " + " ".join(f"{b:>8s}" for b in buckets))
    for src in sorted(k for k in result if k != "_meta"):
        for lab in sorted(k for k in result[src] if not k.startswith("_")):
            cells_s = []
            for b in buckets:
                v = result[src][lab][b]["rate_init_lang_je_gelegenheit"]
                cells_s.append(f"{v:.1%}" if v is not None else "-")
            print(f"{src + '/' + lab:38s} " + " ".join(f"{c:>8s}" for c in cells_s))
    print(f"\n-> {OUT_JSON}")


if __name__ == "__main__":
    main()
