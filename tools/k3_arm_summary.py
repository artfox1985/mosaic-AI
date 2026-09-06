#!/usr/bin/env python
"""Kennzahlen eines Knopf-Arms der Kette night_k3_knobs_b06.sh fuer die Registrierung
(PREREG_geometric_envelope.md, Muster par.8.11a). Reine Arithmetik ueber vorhandene Artefakte.

Aufruf:  python -X utf8 tools/k3_arm_summary.py <tag> [--suffix v24b06] [--ref 0.4975]
  tag: p2 | f10 | f05 | p2f10   (Instrument k3_<tag>_<suffix>.json,
       Arena paired_arena_env_k3<tag>_b06_vs_k3p_{first,second}_s14.json,
       columns_..., points_k3<tag>_b06_vs_k3p_s14.json)
Arm = Seite A in 'first', Seite B in 'second' (arm_wins zaehlt Siege von Seite A,
paired_arena_env_ab.py:271).
"""
import argparse, json, os, sys

ART = "evaluations/artifacts"


def load(name):
    p = os.path.join(ART, name)
    if not os.path.exists(p):
        print(f"FEHLT: {p}")
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--suffix", default="v24b06")
    ap.add_argument("--ref", type=float, default=0.4975, help="Bezug Instrument (Kontrolle)")
    a = ap.parse_args()
    tag = a.tag
    inst = load(f"k3_{tag}_{a.suffix}.json")
    if inst:
        arm = inst["arme"][0]
        print(f"INSTRUMENT k3_{tag}_{a.suffix}.json: Partien {arm['partien']}, volle Spalten "
              f"{arm['sp_voll']:.4f} (KI +-{arm['sp_voll_ci']:.3f}), Punkte {arm['punkte']:.1f}, "
              f"Zeilen {arm['zeilen_voll']:.3f}, Strafleiste {arm['floor']:.2f}; Bezug {a.ref} -> "
              f"Diff {arm['sp_voll']-a.ref:+.4f}; Laufzeit {inst['laufzeit']}")
    rows = {}
    wins_arm = []
    for side, arm_is_a in (("first", True), ("second", False)):
        p = load(f"paired_arena_env_k3{tag}_b06_vs_k3p_{side}_s14.json")
        c = load(f"columns_k3{tag}_b06_vs_k3p_{side}_s14.json")
        if not p:
            continue
        v = list(p["arm_wins"].keys())[0]
        games = p["games"][v]
        n = len(games)
        a_wins = sum(1 for g in games if g["winner"] == 0)
        b_wins = sum(1 for g in games if g["winner"] == 1)
        ties = n - a_wins - b_wins
        arm_w, ctl_w = (a_wins, b_wins) if arm_is_a else (b_wins, a_wins)
        wins_arm.append((arm_w, ctl_w))
        ia, ic = (0, 1) if arm_is_a else (1, 0)
        pts = [sum(g["scores"][i] for g in games) / n for i in (0, 1)]
        lrs = [sum(g["long_rows_started"][i] for g in games) / n for i in (0, 1)]
        lrc = [sum(g["long_rows_completed"][i] for g in games) / n for i in (0, 1)]
        lru = [sum(g["long_rows_cleared_unplaceable"][i] for g in games) / n for i in (0, 1)]
        fl = [sum(g["total_floor"][i] for g in games) / n for i in (0, 1)]
        margin_arm = pts[ia] - pts[ic]
        col = None
        if c:
            s = c["arme"][v]["seiten"]
            col = (s["NetzA"]["volle_spalten"], s["NetzB"]["volle_spalten"], s["NetzA"]["se"], s["NetzB"]["se"],
                   c["verdikt"], c["arme"][v]["divergiert"])
        print(f"ARENA {side} (Arm = {'A' if arm_is_a else 'B'}, spec_a {os.path.basename(p['spec_a'])}, "
              f"spec_b {os.path.basename(p['spec_b'])}, n {n}, Seed {p['base_seed']}, "
              f"Laufzeit {p['laufzeit']['wanduhr_s']:.0f} s / {p['laufzeit']['threads']} Threads):")
        print(f"   Siege Arm:Kontrolle {arm_w}:{ctl_w} (Remis {ties}); Punkte Arm {pts[ia]:.1f} gegen "
              f"Kontrolle {pts[ic]:.1f} (Marge {margin_arm:+.1f}); Strafleiste {fl[ia]:.1f} / {fl[ic]:.1f}")
        print(f"   lange Reihen Arm begonnen/vollendet/geraeumt {lrs[ia]:.2f}/{lrc[ia]:.2f}/{lru[ia]:.2f}; "
              f"Kontrolle {lrs[ic]:.2f}/{lrc[ic]:.2f}/{lru[ic]:.2f}")
        if col:
            ca, cb = (col[0], col[1]) if arm_is_a else (col[1], col[0])
            sa, sb = (col[2], col[3]) if arm_is_a else (col[3], col[2])
            print(f"   volle Spalten Arm {ca:.3f} (SE {sa:.3f}) gegen Kontrolle {cb:.3f} (SE {sb:.3f}); "
                  f"Sonde {col[4]}, divergiert {col[5]}")
    if len(wins_arm) == 2:
        tot_a = wins_arm[0][0] + wins_arm[1][0]
        tot_c = wins_arm[0][1] + wins_arm[1][1]
        print(f"ARENA GESAMT Arm:Kontrolle {tot_a}:{tot_c} (Brett 0: {wins_arm[0][0]}:{wins_arm[0][1]}, "
              f"Brett 1: {wins_arm[1][0]}:{wins_arm[1][1]})")
    pt = load(f"points_k3{tag}_b06_vs_k3p_s14.json")
    if pt:
        kb_arm, kb_ctl = [], []
        for f in pt["dateien"]:
            for seite, z in f["zuordnung"].items():
                kb = f["seiten"][seite]["kuppelbonus_gesamt"]
                (kb_ctl if z["spec"].endswith("v24-b06_brierbest.spec.json") else kb_arm).append(kb)
        print(f"KUPPEL-BONUS je Partie: Arm {' / '.join(f'{x:.1f}' for x in kb_arm)} gegen Kontrolle "
              f"{' / '.join(f'{x:.1f}' for x in kb_ctl)}")


if __name__ == "__main__":
    main()
