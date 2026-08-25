# -*- coding: utf-8 -*-
"""PREREG_opponent_disruption.md §4 -- Auswertung der gepaarten Messung.

Zielgroesse: GEGNER-Plattenpunkte (Heuristik-Seite, da net_arena_match
einseitig ist -- die Heuristik liest MOSAIC_OPPONENT_DISRUPTION nicht,
siehe paired_arena_env_ab.py-Moduldoc). Nebenmessung: eigene (Netz-)Punkte,
Boden, Siege (McNemar, exakte Formel aus tools/paired_gating.py).

Reuse: PATTERNS/ROUND_PREFIX aus analyze_game_log.py (wie
tools/plate_points_from_arena.py) -- hier fuer die HEURISTIK-Seite statt
der Netz-Seite ausgewertet.
"""
import json
import math
import sys
from pathlib import Path

BASIS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASIS / "tools"))

from analyze_game_log import PATTERNS, ROUND_PREFIX  # noqa: E402
from paired_gating import mcnemar_exact_p  # noqa: E402
import re

KRITERIUM = re.compile(r"^\s+\S+ (?P<name>[^:]+): (?P<pkt>-?\d+) Pkt$")


def opponent_evaluation(sp: dict) -> dict:
    """Eine Partie -> Kennzahlen der HEURISTIK-Seite (der GEGNER aus Netz-Sicht)."""
    namen = sp["names"]
    ni = next((i for i, n in enumerate(namen) if "euristik" not in n), 0)  # Netz-Index
    hi = 1 - ni  # Heuristik-Index
    heurname = namen[hi]

    platten_gesamt, je_kriterium = None, {}
    aktiv = None
    for roh in sp.get("log") or []:
        m = ROUND_PREFIX.match(roh)
        text = m.group(2) if m else roh
        fs = PATTERNS["FINAL_SCORE"].match(text)
        if fs:
            aktiv = fs.group("name") == heurname
            if aktiv:
                platten_gesamt = int(fs.group("total"))
            continue
        if aktiv:
            k = KRITERIUM.match(text)
            if k:
                je_kriterium[k.group("name").strip()] = int(k.group("pkt"))
            else:
                aktiv = False

    boden = sp["total_floor"]
    return dict(
        seed=sp["game_seed"],
        gegner_punkte=sp["scores"][hi],
        gegner_platten=platten_gesamt,
        gegner_je_kriterium=je_kriterium,
        gegner_boden=boden[hi] if isinstance(boden, list) else boden,
        netz_punkte=sp["scores"][ni],
        netz_boden=boden[ni] if isinstance(boden, list) else boden,
        netz_sieg=1 if sp["winner"] == ni else 0,
    )


def t_value(werte: list[float]) -> tuple[float, float]:
    n = len(werte)
    if n < 2:
        return (werte[0] if werte else 0.0), 0.0
    m = sum(werte) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in werte) / (n - 1))
    return m, (m / (sd / math.sqrt(n)) if sd > 0 else 0.0)


def load(path_prefix: str) -> tuple[list[dict], list[dict]]:
    d = json.load(open(BASIS / "evaluations" / "artifacts" / f"{path_prefix}.json", encoding="utf-8"))
    games = d["games"]
    off = [opponent_evaluation(s) for s in games["0"]]
    on = [opponent_evaluation(s) for s in games["1"]]
    return off, on


def summarize(label: str, off: list[dict], on: list[dict]) -> dict:
    n = len(off)
    assert len(on) == n
    d_gpunkte = [on[i]["gegner_punkte"] - off[i]["gegner_punkte"] for i in range(n)]
    d_gplatten = [(on[i]["gegner_platten"] or 0) - (off[i]["gegner_platten"] or 0) for i in range(n)]
    d_npunkte = [on[i]["netz_punkte"] - off[i]["netz_punkte"] for i in range(n)]
    d_nboden = [on[i]["netz_boden"] - off[i]["netz_boden"] for i in range(n)]
    sieg_off = sum(g["netz_sieg"] for g in off)
    sieg_on = sum(g["netz_sieg"] for g in on)
    b = sum(1 for i in range(n) if on[i]["netz_sieg"] == 1 and off[i]["netz_sieg"] == 0)  # on gewinnt, off nicht
    c = sum(1 for i in range(n) if on[i]["netz_sieg"] == 0 and off[i]["netz_sieg"] == 1)  # off gewinnt, on nicht
    mc_p = mcnemar_exact_p(b, c)

    mgp, tgp = t_value(d_gpunkte)
    mgpl, tgpl = t_value(d_gplatten)
    mnp, tnp = t_value(d_npunkte)
    mnb, tnb = t_value(d_nboden)

    print(f"\n=== {label} (n={n}) ===")
    print(f"Netz-Siege: aus {sieg_off}/{n} -> an {sieg_on}/{n}  (b={b} c={c} McNemar p={mc_p:.4f})")
    print(f"Gegner-Punkte  Δ={mgp:+.2f} t={tgp:.2f}")
    print(f"Gegner-Platten Δ={mgpl:+.2f} t={tgpl:.2f}")
    print(f"Netz-Punkte    Δ={mnp:+.2f} t={tnp:.2f}")
    print(f"Netz-Boden     Δ={mnb:+.2f} t={tnb:.2f}")
    return dict(n=n, sieg_off=sieg_off, sieg_on=sieg_on, b=b, c=c, mcnemar_p=mc_p,
                d_gegner_punkte=(mgp, tgp), d_gegner_platten=(mgpl, tgpl),
                d_netz_punkte=(mnp, tnp), d_netz_boden=(mnb, tnb))


def main():
    off1, on1 = load("paired_arena_env_opp_disruption_run1")
    off2, on2 = load("paired_arena_env_opp_disruption_run2")

    r1 = summarize("Lauf 1 (Erstmessung, Basis-Seed 20260815)", off1, on1)
    r2 = summarize("Lauf 2 (Replikation, Basis-Seed 20260822)", off2, on2)
    pooled = summarize("GEPOOLT (Lauf 1 + Lauf 2)", off1 + off2, on1 + on2)

    # 2-Block-Vergleich (jeder Lauf = 1 Block, siehe Diskussion Block-Ebene):
    # Mittelwert je Block, damit ein einzelner Ausreisser-Lauf nicht als
    # Einzelspiel-Rauschen durchgeht.
    block_means_gpunkte = [r1["d_gegner_punkte"][0], r2["d_gegner_punkte"][0]]
    block_means_npunkte = [r1["d_netz_punkte"][0], r2["d_netz_punkte"][0]]
    print(f"\n=== 2-Block-Ebene (je Lauf EIN Block-Mittel) ===")
    print(f"Gegner-Punkte Block-Mittel: {block_means_gpunkte}")
    print(f"Netz-Punkte   Block-Mittel: {block_means_npunkte}")

    out = dict(lauf1=r1, lauf2=r2, gepoolt=pooled,
               block_means_gegner_punkte=block_means_gpunkte,
               block_means_netz_punkte=block_means_npunkte)
    with open(BASIS / "evaluations" / "artifacts" / "opponent_disruption_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("\n-> evaluations/opponent_disruption_summary.json")


if __name__ == "__main__":
    main()
