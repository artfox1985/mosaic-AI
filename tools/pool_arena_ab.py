# -*- coding: utf-8 -*-
"""tools/pool_arena_ab.py -- mehrere Bloecke eines gepaarten Arm-A/Bs zu EINER
Auswertung zusammenfassen.

## Warum

`paired_arena_plate_ab.py --combine` wertet genau EIN Praefix-Paar aus
(`paired_arena_<prefix>_{off,on}_raw.json`) und besteht zu Recht darauf, dass
beide Arme denselben Basis-Seed und dieselbe Spielzahl haben. Wird ein A/B
nachtraeglich VERLAENGERT, entsteht ein zweiter Block mit einem ANDEREN
Basis-Seed -- die Bloecke sind dann jeder fuer sich paarungskompatibel, aber
nicht miteinander. Dieses Werkzeug poolt sie.

Gepaart wird weiterhin INNERHALB eines Blocks (Spiel i in OFF gegen Spiel i in
ON desselben Blocks, identische Startbedingungen). Nur die diskordanten Zaehler
b/c werden ueber die Bloecke aufsummiert und EINMAL per exaktem McNemar
getestet. Das ist zulaessig, weil die Paare unabhaengig sind.

## Nutzung

    python tools/pool_arena_ab.py --prefix tiling tiling2

## Vorbehalt, der mitzuberichten ist

Wurde die Verlaengerung NACH Sichtung eines Zwischenergebnisses beschlossen
(optionales Stoppen), ist der p-Wert optimistisch -- die Falsch-Positiv-Rate
liegt ueber dem nominellen Alpha. Das Werkzeug schreibt diesen Hinweis in die
Ausgabe, damit er nicht verlorengeht.
"""
from __future__ import annotations

import argparse
import json
from math import comb
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent.parent / "evaluations"


def mcnemar_exact_p(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    lo, hi = min(b, c), max(b, c)
    p_le = sum(comb(n, k) for k in range(0, lo + 1)) / (2 ** n)
    p_ge = sum(comb(n, k) for k in range(hi, n + 1)) / (2 ** n)
    return min(1.0, 2 * min(p_le, p_ge))


def _avg(games, key, idx):
    vals = [g[key][idx] for g in games if key in g and len(g[key]) > idx]
    return sum(vals) / len(vals) if vals else float("nan")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--prefix", nargs="+", required=True,
                   help="Praefixe der zu poolenden Bloecke, z.B. tiling tiling2")
    p.add_argument("--out", default=None)
    args = p.parse_args()

    tot = {"b": 0, "c": 0, "cc_win": 0, "cc_lose": 0, "off_wins": 0, "on_wins": 0, "n": 0}
    off_all, on_all, blocks = [], [], []

    for pref in args.prefix:
        off = json.loads((EVAL_DIR / "artifacts" / f"paired_arena_{pref}_off_raw.json").read_text(encoding="utf-8"))
        on = json.loads((EVAL_DIR / "artifacts" / f"paired_arena_{pref}_on_raw.json").read_text(encoding="utf-8"))
        if off["base_seed"] != on["base_seed"] or off["n_games"] != on["n_games"]:
            raise SystemExit(f"Block '{pref}' nicht paarungskompatibel: "
                             f"OFF seed={off['base_seed']} n={off['n_games']} vs "
                             f"ON seed={on['base_seed']} n={on['n_games']}")
        n = off["n_games"]
        b = c = cw = cl = ow = nw = 0
        for i in range(n):
            o = off["games"][i]["winner"] == 0
            v = on["games"][i]["winner"] == 0
            ow += int(o); nw += int(v)
            if v and not o: b += 1
            elif o and not v: c += 1
            elif o and v: cw += 1
            else: cl += 1
        blocks.append({"prefix": pref, "base_seed": off["base_seed"], "n_games": n,
                       "champion_wins_off": ow, "champion_wins_on": nw,
                       "b_on_only": b, "c_off_only": c, "mcnemar_p_block": mcnemar_exact_p(b, c)})
        tot["b"] += b; tot["c"] += c; tot["cc_win"] += cw; tot["cc_lose"] += cl
        tot["off_wins"] += ow; tot["on_wins"] += nw; tot["n"] += n
        off_all += off["games"]; on_all += on["games"]

    pval = mcnemar_exact_p(tot["b"], tot["c"])
    sc_off_a, sc_off_b = _avg(off_all, "scores", 0), _avg(off_all, "scores", 1)
    sc_on_a, sc_on_b = _avg(on_all, "scores", 0), _avg(on_all, "scores", 1)

    print("=" * 74)
    print(f"  GEPOOLTER ARM-A/B ueber {len(args.prefix)} Bloecke ({tot['n']} Spiele je Arm)")
    print("=" * 74)
    for bl in blocks:
        print(f"  Block {bl['prefix']:<10} Seed={bl['base_seed']:<10} n={bl['n_games']:<4} "
              f"OFF {bl['champion_wins_off']:>3}  ON {bl['champion_wins_on']:>3}   "
              f"b={bl['b_on_only']:>3} c={bl['c_off_only']:>3}  p={bl['mcnemar_p_block']:.4f}")
    print("-" * 74)
    print(f"  GESAMT  Champion-Siege:  OFF {tot['off_wins']}/{tot['n']} "
          f"({tot['off_wins']/tot['n']:.1%})   ON {tot['on_wins']}/{tot['n']} "
          f"({tot['on_wins']/tot['n']:.1%})")
    print(f"  Diskordant: b(nur ON)={tot['b']}  c(nur OFF)={tot['c']}   "
          f"konkordant {tot['cc_win']}/{tot['cc_lose']}")
    print(f"  Exakter McNemar ueber alle Bloecke: p = {pval:.4f}")
    print()
    print(f"  Ø Score  OFF: {sc_off_a:.2f} vs {sc_off_b:.2f}   (Summe {sc_off_a+sc_off_b:.2f})")
    print(f"  Ø Score  ON : {sc_on_a:.2f} vs {sc_on_b:.2f}   (Summe {sc_on_a+sc_on_b:.2f})")
    print(f"  Ø Floor  OFF: {_avg(off_all,'total_floor',0):.2f} vs {_avg(off_all,'total_floor',1):.2f}")
    print(f"  Ø Floor  ON : {_avg(on_all,'total_floor',0):.2f} vs {_avg(on_all,'total_floor',1):.2f}")
    print("=" * 74)
    verdict = "ON" if (pval < 0.05 and tot["on_wins"] > tot["off_wins"]) else "OFF"
    print(f"  Evidenzregel (p<0.05 UND Vorteil ON): -> {verdict}")
    if len(args.prefix) > 1:
        print("\n  VORBEHALT: gepoolt aus mehreren Bloecken. Wurde die Verlaengerung nach")
        print("  Sichtung eines Zwischenergebnisses beschlossen (optionales Stoppen), ist")
        print("  dieser p-Wert OPTIMISTISCH -- die Falsch-Positiv-Rate liegt ueber Alpha.")

    out = Path(args.out) if args.out else EVAL_DIR / "artifacts" / f"paired_arena_pooled_{args.prefix[0]}.json"
    out.write_text(json.dumps({
        "blocks": blocks, "n_games_per_arm": tot["n"],
        "champion_wins_off": tot["off_wins"], "champion_wins_on": tot["on_wins"],
        "discordant_b_on_only": tot["b"], "discordant_c_off_only": tot["c"],
        "concordant_both_win": tot["cc_win"], "concordant_both_lose": tot["cc_lose"],
        "mcnemar_p_pooled": pval, "verdict": verdict,
        "avg_score_champion_off": sc_off_a, "avg_score_opponent_off": sc_off_b,
        "avg_score_champion_on": sc_on_a, "avg_score_opponent_on": sc_on_b,
        "optional_stopping_caveat": len(args.prefix) > 1,
    }, indent=2), encoding="utf-8")
    print(f"\nErgebnis: {out}")


if __name__ == "__main__":
    main()
