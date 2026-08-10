# -*- coding: utf-8 -*-
"""Wieviele Fliesen landen je RASTERREIHE und RUNDE tatsaechlich auf der Kuppel?

Das **IST** zur Decke aus `tools/musterreihen_verfuegbarkeit.py`. Deren
Modulkopf nennt die drei Referenzpunkte und laesst diesen ausdruecklich offen:

    DECKE   musterreihen_verfuegbarkeit.py -- wie oft sind r gleichfarbige
            Steine ueberhaupt verfuegbar (policy-unabhaengig, reine Versorgung)
    BODEN   Zufalls-Drafting
    IST     Champion-Korpus   <-- DIESES SKRIPT

Nutzer-Auftrag 2026-08-11: *"wieviele fliesen je reihe und runde werden
gelegt"*, Zielformat "Reihe r insgesamt X Fliesen +- CI, im Schnitt Y je Runde".

## Was gemessen wird

`state.players[i].dome_grid` -> 3x3 Slots x 4 Spaces, Rasterabbildung
`grid[sr*2 + si//2][sc*2 + si%2]` (identisch zu `scoring.rs::build_grid`).
Gezaehlt werden BELEGTE Zellen je Rasterreihe 1..6.

Musterreihe r speist Rasterreihe r (eine Fliese je Kachelphase), also ist
"belegte Zellen in Rasterreihe r" = "so oft hat Musterreihe r abgeschlossen".

Zusaetzlich: der FUELLSTAND der Musterreihen am Rundenende
(`players[i].pattern_lines`) -- er zeigt, wo Fliesen haengenbleiben, ohne
abzuschliessen. Das unterscheidet "nicht gefuettert" von "gefuettert, aber nie
voll geworden".

## Methodik und ihre Grenzen

1. **Einheit der Auswertung ist die PARTIE, nicht der Datensatz.** Datensaetze
   derselben Partie sind stark korreliert (stehende Projektregel
   `feedback_arena_block_correlation`); je Partie wird ueber die beiden Bretter
   gemittelt, das CI laeuft ueber Partien. Ein CI ueber Datensaetze waere
   massiv zu eng.
2. **Monotonie-Trick statt Phasen-Logik**: Kuppelbelegung waechst nur. Je
   (Partie, Brett, Runde) wird das MAXIMUM der belegten Zellen genommen; die
   Rundendifferenz ist `max(runde) - max(runde-1)`, unten auf 0 geklemmt. Damit
   ist die Messung unabhaengig davon, an welchen Entscheidungspunkten
   Datensaetze entstehen.
3. **GRENZE, wichtig fuer Runde 5**: der letzte Datensatz einer Partie ist der
   letzte Kachel-SCHRITT, nicht der Endzustand (dieselbe Einschraenkung, die
   `evaluations/STATUS.md` fuer die Plattenkopf-Labels vermerkt). Die
   Rundensumme fuer Runde 5 -- und damit die Gesamtzahl -- ist deshalb eine
   leichte UNTERSCHAETZUNG, bis zu einer Fliese je Reihe.
4. Der Korpus ist Self-Play MIT Wurzelrauschen, also bewusst schwaecheres
   Spiel als der Champion in der Arena. Die Zahlen sind das IST dieses
   Regimes, keine Obergrenze des Koennens.

Aufruf:
    python tools/musterreihen_durchsatz.py --files 60
    python tools/musterreihen_durchsatz.py --glob "data/selfplay_v19wdl_*.pkl"
"""
from __future__ import annotations

import argparse
import glob
import math
import pickle
from collections import defaultdict

ROWS = 6
ROUNDS = 5


def _filled_per_row(dome_grid) -> list[int]:
    """Belegte Zellen je Rasterreihe 1..6 (Index 0..5) fuer EIN Brett."""
    out = [0] * ROWS
    for sr in range(3):
        row = dome_grid[sr] if sr < len(dome_grid) else []
        for sc in range(3):
            slot = row[sc] if sc < len(row) else None
            spaces = (slot or {}).get("spaces", []) if slot else []
            for si in range(4):
                sp = spaces[si] if si < len(spaces) else None
                if sp and sp.get("filled") is not None:
                    out[sr * 2 + si // 2] += 1
    return out


def _pattern_fill(player) -> list[int]:
    """Fuellstand der Musterreihen 1..6 (Zahl der liegenden Steine)."""
    lines = player.get("pattern_lines") or []
    out = []
    for r in range(ROWS):
        ln = lines[r] if r < len(lines) else None
        if isinstance(ln, dict):
            out.append(int(ln.get("count") or len(ln.get("tiles") or [])))
        elif isinstance(ln, (list, tuple)):
            out.append(len([t for t in ln if t is not None]))
        else:
            out.append(0)
    return out


def _ci95(vals: list[float]) -> tuple[float, float]:
    n = len(vals)
    if n < 2:
        return (vals[0] if vals else 0.0), 0.0
    m = sum(vals) / n
    var = sum((v - m) ** 2 for v in vals) / (n - 1)
    return m, 1.96 * math.sqrt(var / n)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default="data/selfplay_v20wdl_*.pkl")
    ap.add_argument("--files", type=int, default=60)
    args = ap.parse_args()

    files = sorted(glob.glob(args.glob))[: args.files]
    if not files:
        print(f"Keine Dateien fuer {args.glob!r}")
        return 1

    # (game_id, brett) -> runde -> max belegte Zellen je Reihe
    peak: dict[tuple, dict[int, list[int]]] = defaultdict(dict)
    # (game_id, brett) -> runde -> Musterreihen-Fuellstand (letzter gesehener)
    pat: dict[tuple, dict[int, list[int]]] = defaultdict(dict)

    for f in files:
        with open(f, "rb") as fh:
            recs = pickle.load(fh)
        for rec in recs:
            st = rec.get("state") or {}
            rnd = st.get("round")
            if not isinstance(rnd, int):
                continue
            gid = rec.get("game_id")
            for bi, pl in enumerate(st.get("players") or []):
                key = (gid, bi)
                cur = _filled_per_row(pl.get("dome_grid") or [])
                prev = peak[key].get(rnd)
                peak[key][rnd] = cur if prev is None else [max(a, b) for a, b in zip(prev, cur)]
                pat[key][rnd] = _pattern_fill(pl)

    # Je PARTIE ueber die Bretter mitteln
    games: dict[str, list[tuple]] = defaultdict(list)
    for (gid, bi) in peak:
        games[gid].append((gid, bi))

    per_game_total = {r: [] for r in range(ROWS)}
    per_game_round = {(r, rd): [] for r in range(ROWS) for rd in range(1, ROUNDS + 1)}
    per_game_stuck = {r: [] for r in range(ROWS)}

    for gid, keys in games.items():
        tot = [[] for _ in range(ROWS)]
        rnd_d = {(r, rd): [] for r in range(ROWS) for rd in range(1, ROUNDS + 1)}
        stuck = [[] for _ in range(ROWS)]
        for key in keys:
            byr = peak[key]
            seen = sorted(byr)
            last = byr[seen[-1]]
            for r in range(ROWS):
                tot[r].append(last[r])
            prev = [0] * ROWS
            for rd in range(1, ROUNDS + 1):
                cur = byr.get(rd, prev)
                for r in range(ROWS):
                    rnd_d[(r, rd)].append(max(0, cur[r] - prev[r]))
                prev = cur
            # Haengengeblieben: Fuellstand der Musterreihe im letzten Datensatz
            pf = pat[key][seen[-1]]
            for r in range(ROWS):
                stuck[r].append(pf[r])
        for r in range(ROWS):
            per_game_total[r].append(sum(tot[r]) / len(tot[r]))
            per_game_stuck[r].append(sum(stuck[r]) / len(stuck[r]))
            for rd in range(1, ROUNDS + 1):
                v = rnd_d[(r, rd)]
                per_game_round[(r, rd)].append(sum(v) / len(v))

    n_games = len(games)
    print(f"Korpus: {len(files)} Dateien, {n_games} Partien, {len(peak)} Bretter")
    print(f"Muster: {args.glob}")
    print("Einheit der Auswertung = PARTIE (ueber beide Bretter gemittelt); CI = 95 %.")
    print("ACHTUNG: Runde 5 und damit die Gesamtzahl sind leicht UNTERSCHAETZT")
    print("(letzter Datensatz = letzter Kachelschritt, nicht Endzustand).\n")

    print(f"{'Reihe':>5} {'Kapazitaet':>10} | {'gesamt':>14} | {'je Runde':>9} | "
          f"{'Rest in Musterreihe':>19}")
    print("-" * 74)
    for r in range(ROWS):
        m, ci = _ci95(per_game_total[r])
        ms, _ = _ci95(per_game_stuck[r])
        print(f"{r+1:>5} {r+1:>10} | {m:>7.2f} +- {ci:>4.2f} | {m/ROUNDS:>9.2f} | {ms:>19.2f}")

    print("\n--- je Runde einzeln (Mittel je Partie, CI 95 %) ---")
    hdr = "Reihe |" + "".join(f"    Runde {rd}    |" for rd in range(1, ROUNDS + 1))
    print(hdr)
    print("-" * len(hdr))
    for r in range(ROWS):
        cells = []
        for rd in range(1, ROUNDS + 1):
            m, ci = _ci95(per_game_round[(r, rd)])
            cells.append(f" {m:>5.2f}+-{ci:<4.2f} |")
        print(f"{r+1:>5} |" + "".join(cells))

    print("\nLESART: 'gesamt' = belegte Zellen der Rasterreihe am Ende = so oft hat")
    print("Musterreihe r abgeschlossen. 'Rest in Musterreihe' = Steine, die am Ende")
    print("noch in der Musterreihe liegen, ohne sie voll gemacht zu haben.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
