# -*- coding: utf-8 -*-
"""Wertungsplatten-Punkte und Strafleiste aus gepaarten Arena-Ergebnissen ziehen.

ANLASS (2026-08-11): die Injektions-Versuche brauchen nicht die Siegquote,
sondern das VERHALTEN -- wieviele Plattenpunkte macht das Netz, und was kostet
ihn das an Strafpunkten. `paired_arena_env_ab.py --log-games` legt die vollen
Partie-Logs ins Ergebnis-JSON; hier werden sie gelesen.

WARUM KEIN EIGENER PARSER: `tools/analyze_game_log.py` hat den Ausdruck fuer die
Endwertungs-Zeile schon (`PATTERNS["FINAL_SCORE"]`, dort Zeile 124) und die
Praefix-Behandlung (`ROUND_PREFIX`). Beides wird hier IMPORTIERT statt
nachgebaut. Folge, und sie ist beabsichtigt: aendert jemand den Logtext, brechen
beide Seiten gemeinsam, statt dass diese hier stumm falsche Zahlen liefert.
(Genau davor warnt auch `tools/hooks/pre-push` bei Log-Text-Aenderungen.)

Die Aufschlueselung JE PLATTE (`   🔲 Eckplatten: 3 Pkt`) kennt
`analyze_game_log.py` NICHT -- die kommt hier dazu, und zwar streng auf die
Zeilen NACH einer Endwertungs-Zeile begrenzt, damit sie nichts anderes
einsammelt.

Aufruf:
    python -X utf8 tools/plate_points_from_arena.py w0 w01 uni --bezug w0
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

BASIS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASIS / "tools"))

from analyze_game_log import PATTERNS, ROUND_PREFIX  # noqa: E402  (bewusst nach sys.path)

# Nur auf Zeilen angewandt, die einer Endwertungs-Zeile FOLGEN -- siehe Modul-Doc.
KRITERIUM = re.compile(r"^\s+\S+ (?P<name>[^:]+): (?P<pkt>-?\d+) Pkt$")


def partien(pfad: Path) -> list[dict]:
    d = json.load(open(pfad, encoding="utf-8"))
    g = d["games"]
    if isinstance(g, dict):  # Mehr-Arm-Form: {armwert: [partien]}
        if len(g) != 1:
            raise SystemExit(f"{pfad.name}: {len(g)} Arme -- dieses Werkzeug erwartet einen")
        g = next(iter(g.values()))
    return g


def auswerten(sp: dict) -> dict:
    """Eine Partie -> Kennzahlen des NETZ-Spielers."""
    namen = sp["names"]
    ni = next((i for i, n in enumerate(namen) if "euristik" not in n), 0)
    netzname = namen[ni]

    platten_gesamt, je_kriterium = None, {}
    aktiv = None  # sammelt nur direkt nach der Endwertungs-Zeile des Netzes
    for roh in sp.get("log") or []:
        m = ROUND_PREFIX.match(roh)
        text = m.group(2) if m else roh
        fs = PATTERNS["FINAL_SCORE"].match(text)
        if fs:
            aktiv = fs.group("name") == netzname
            if aktiv:
                platten_gesamt = int(fs.group("total"))
            continue
        if aktiv:
            k = KRITERIUM.match(text)
            if k:
                je_kriterium[k.group("name").strip()] = int(k.group("pkt"))
            else:
                aktiv = False  # Block zu Ende

    boden = sp["total_floor"]
    return dict(
        seed=sp["game_seed"],
        punkte=sp["scores"][ni],
        platten=platten_gesamt,
        je_kriterium=je_kriterium,
        boden=boden[ni] if isinstance(boden, list) else boden,
        sieg=1 if sp["winner"] == ni else 0,
    )


def t_wert(werte: list[float]) -> tuple[float, float]:
    n = len(werte)
    if n < 2:
        return (werte[0] if werte else 0.0), 0.0
    m = sum(werte) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in werte) / (n - 1))
    return m, (m / (sd / math.sqrt(n)) if sd > 0 else 0.0)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("kuerzel", nargs="+",
                   help="Out-Praefix-Kuerzel (z.B. w0 uni) oder ein Pfad zur JSON")
    p.add_argument("--praefix", default="platten",
                   help="gemeinsamer Namensteil vor dem Kuerzel (Default: platten)")
    p.add_argument("--bezug", default=None,
                   help="Kuerzel, gegen das GEPAART verglichen wird (ueber den Seed)")
    a = p.parse_args()

    daten: dict[str, dict[int, dict]] = {}
    for k in a.kuerzel:
        pf = Path(k) if k.endswith(".json") else \
            BASIS / "evaluations" / f"paired_arena_env_{a.praefix}_{k}.json"
        if not pf.exists():
            print(f"{k}: FEHLT ({pf.name})")
            continue
        daten[k] = {r["seed"]: r for r in (auswerten(s) for s in partien(pf))}

    if not daten:
        raise SystemExit("keine Daten")

    fehlend = {k: sum(1 for r in v.values() if r["platten"] is None) for k, v in daten.items()}
    if any(fehlend.values()):
        print(f"WARNUNG: Endwertungs-Zeile nicht gefunden in {fehlend} Partien -- "
              f"Logtext geaendert? (siehe Modul-Doc)\n")

    bezug = daten.get(a.bezug) if a.bezug else None
    kopf = f"{'Kuerzel':<10} {'n':>3} {'Sieg':>7} {'Punkte':>7} {'Platten':>8} {'Boden':>7}"
    if bezug:
        kopf += f" | {'ΔPunkte':>8} {'t':>6} {'ΔPlatten':>9} {'t':>6} {'ΔBoden':>7} {'t':>6}"
    print(kopf)
    print("-" * len(kopf))
    for k, v in daten.items():
        ks = sorted(v)
        n = len(ks)
        mp = sum(v[s]["punkte"] for s in ks) / n
        mpl = sum(v[s]["platten"] or 0 for s in ks) / n
        mb = sum(v[s]["boden"] for s in ks) / n
        w = sum(v[s]["sieg"] for s in ks)
        zeile = f"{k:<10} {n:>3} {w:>3}/{n:<3} {mp:>7.2f} {mpl:>8.2f} {mb:>7.2f}"
        if bezug:
            gem = [s for s in ks if s in bezug]
            dp, tp = t_wert([v[s]["punkte"] - bezug[s]["punkte"] for s in gem])
            dl, tl = t_wert([(v[s]["platten"] or 0) - (bezug[s]["platten"] or 0) for s in gem])
            db, tb = t_wert([v[s]["boden"] - bezug[s]["boden"] for s in gem])
            zeile += f" | {dp:>+8.2f} {tp:>6.2f} {dl:>+9.2f} {tl:>6.2f} {db:>+7.2f} {tb:>6.2f}"
        print(zeile)

    # Je Kriterium: nur Platten, die ueberhaupt vorkommen
    namen = sorted({n for v in daten.values() for r in v.values() for n in r["je_kriterium"]})
    if namen:
        print(f"\nPlattenpunkte je Kriterium (Mittel ueber die Partien, in denen die Platte aktiv war):")
        print(f"{'Kuerzel':<10}" + "".join(f"{n[:17]:>19}" for n in namen))
        for k, v in daten.items():
            zeile = f"{k:<10}"
            for n in namen:
                tr = [r["je_kriterium"][n] for r in v.values() if n in r["je_kriterium"]]
                zeile += f"{(sum(tr)/len(tr) if tr else float('nan')):>15.2f}({len(tr):>2})"
            print(zeile)


if __name__ == "__main__":
    main()
