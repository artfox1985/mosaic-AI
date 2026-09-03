# -*- coding: utf-8 -*-
"""Gepoolte Auswertung zweier `paired_arena_env_ab`-Laeufe mit Brett-Tausch
(Netz gegen dasselbe Netz, Knopf per Env auf EINER Seite, Spec `off` auf der
anderen; Konvention der K1/K3-Messung 2026-09-03):

  * Lauf "first":  Brett 0 = Env-Arm (Knopf an), Brett 1 = Spec aus
  * Lauf "second": Brett 0 = Spec aus,           Brett 1 = Env-Arm

Je Arm wird aus beiden Laeufen die Sicht der KNOPF-Seite gebildet
("Knopf gewinnt"), gegen den Kontrollarm desselben Spielindex gepaart
(McNemar exakt auf den diskordanten Paaren, gepoolt ueber beide Richtungen)
und auf BLOCK-Ebene gerechnet (Blockgroesse aus dem Artefakt-Aufruf, Default
5; der Seed faellt je Block, Memory "Arena-Block-Korrelation"): gepaarte
Siegdifferenz je Block gegen die Kontrolle, Block-SE, t. Dazu Punkte und
Margin der Knopf-Seite (aus `scores` der Partie-Records) und die K1-Zaehler
(`score_utility_stats`, Klammer-Anteile), sofern im Artefakt.

Aufruf:
    python -X utf8 tools/probes/env_ab_swap_eval.py \\
        --first evaluations/artifacts/paired_arena_env_k1_b01_first_s01.json \\
        --second evaluations/artifacts/paired_arena_env_k1_b01_second_s01.json \\
        --out evaluations/artifacts/k1_b01_swap_eval_s01.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics as st
import sys
import time
from math import comb

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass


def mcnemar_exact_p(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def knob_side_wins(games: list[dict], knob_board: int) -> list[int]:
    """1, wenn die Knopf-Seite (Brett `knob_board`) gewonnen hat."""
    return [1 if g["winner"] == knob_board else 0 for g in games]


def knob_side_points(games: list[dict], knob_board: int) -> tuple[list[float], list[float]]:
    own = [float(g["scores"][knob_board]) for g in games]
    marg = [float(g["scores"][knob_board] - g["scores"][1 - knob_board]) for g in games]
    return own, marg


def blocks(values: list[float], size: int) -> list[float]:
    return [sum(values[i:i + size]) / len(values[i:i + size]) for i in range(0, len(values), size)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--first", required=True, help="Lauf mit Knopf auf Brett 0")
    ap.add_argument("--second", required=True, help="Lauf mit Knopf auf Brett 1")
    ap.add_argument("--block-size", type=int, default=5)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.monotonic()

    first = json.loads(pathlib.Path(a.first).read_text(encoding="utf-8"))
    second = json.loads(pathlib.Path(a.second).read_text(encoding="utf-8"))
    arms = first["arms"]
    control = first["control"]
    assert second["arms"] == arms and second["control"] == control, "Arme/Kontrolle der beiden Laeufe verschieden"
    assert first.get("base_seed") == second.get("base_seed"), "Basis-Seed verschieden -- kein Brett-Tausch-Paar"

    out = {"first": pathlib.Path(a.first).name, "second": pathlib.Path(a.second).name,
           "env_name": first["env_name"], "control": control, "base_seed": first.get("base_seed"),
           "block_size": a.block_size, "arms": {}}

    # Knopf-Seite: first -> Brett 0, second -> Brett 1. Beim Kontrollarm ist
    # die "Knopf-Seite" dieselbe Brettnummer, nur ohne Knopf (Spiegelmatch):
    # ihr Ergebnis ist die Basislinie, gegen die gepaart wird.
    def knob_view(art: dict, arm: str, knob_board: int):
        games = art["games"][arm]
        return knob_side_wins(games, knob_board), knob_side_points(games, knob_board)

    ctrl_w = knob_view(first, control, 0)[0] + knob_view(second, control, 1)[0]
    ctrl_pts = knob_view(first, control, 0)[1]
    ctrl_pts2 = knob_view(second, control, 1)[1]
    ctrl_own = ctrl_pts[0] + ctrl_pts2[0]
    ctrl_marg = ctrl_pts[1] + ctrl_pts2[1]
    n = len(ctrl_w)

    print(f"Kontrolle ({control}): Knopf-Seite (ohne Knopf) {sum(ctrl_w)}/{n}, "
          f"Punkte {st.mean(ctrl_own):.2f}, Margin {st.mean(ctrl_marg):+.2f}")
    for arm in arms:
        w = knob_view(first, arm, 0)[0] + knob_view(second, arm, 1)[0]
        p1 = knob_view(first, arm, 0)[1]
        p2 = knob_view(second, arm, 1)[1]
        own = p1[0] + p2[0]
        marg = p1[1] + p2[1]
        assert len(w) == n
        b = sum(1 for i in range(n) if w[i] and not ctrl_w[i])
        c = sum(1 for i in range(n) if ctrl_w[i] and not w[i])
        p = mcnemar_exact_p(b, c)
        # Block-Ebene: Differenz je Block (Knopf minus Kontrolle), ueber beide
        # Richtungen; jeder Lauf hat n/2 Partien in Bloecken der Groesse
        # block_size. Bloecke beider Richtungen werden getrennt gebildet.
        half = n // 2
        d_w, d_m = [], []
        for lo, hi in ((0, half), (half, n)):
            bw = blocks([w[i] - ctrl_w[i] for i in range(lo, hi)], a.block_size)
            bm = blocks([marg[i] - ctrl_marg[i] for i in range(lo, hi)], a.block_size)
            d_w += bw
            d_m += bm
        nb = len(d_w)
        se_w = st.stdev(d_w) / nb ** 0.5 if nb > 1 else float("nan")
        se_m = st.stdev(d_m) / nb ** 0.5 if nb > 1 else float("nan")
        su = {}
        for art in (first, second):
            for k, v in (art.get("score_utility_stats", {}).get(arm) or {}).items():
                su[k] = su.get(k, 0) + v
        rec = {
            "knopf_siege": sum(w), "n": n, "kontrolle_siege": sum(ctrl_w),
            "diskordant_knopf_gewinnt": b, "diskordant_kontrolle_gewinnt": c, "p_mcnemar": p,
            "siegdifferenz_je_partie": (sum(w) - sum(ctrl_w)) / n,
            "bloecke": nb, "block_diff_siege_mittel": st.mean(d_w), "block_se_siege": se_w,
            "block_t_siege": (st.mean(d_w) / se_w) if se_w == se_w and se_w > 0 else None,
            "punkte_knopf": st.mean(own), "punkte_kontrolle": st.mean(ctrl_own),
            "margin_knopf": st.mean(marg), "margin_kontrolle": st.mean(ctrl_marg),
            "block_diff_margin_mittel": st.mean(d_m), "block_se_margin": se_m,
            "score_utility_stats": su,
            "klammer_anteil_marge": (su.get("margin_clamped", 0) / su["leaves"]) if su.get("leaves") else None,
            "klammer_anteil_einheit": (su.get("unit_clamped", 0) / su["leaves"]) if su.get("leaves") else None,
        }
        out["arms"][arm] = rec
        if arm == control:
            continue
        print(f"Arm {arm}: Knopf {sum(w)}/{n} gegen Basislinie {sum(ctrl_w)}/{n} | "
              f"diskordant {b}/{c}, McNemar p={p:.4f} | Block-Diff {st.mean(d_w):+.3f} "
              f"SE {se_w:.3f} (t {rec['block_t_siege'] if rec['block_t_siege'] is None else round(rec['block_t_siege'], 2)}) | "
              f"Punkte {st.mean(own):.2f} Margin {st.mean(marg):+.2f} "
              f"(Block-Diff Margin {st.mean(d_m):+.2f} SE {se_m:.2f}) | "
              f"Klammer Marge {rec['klammer_anteil_marge']} Einheit {rec['klammer_anteil_einheit']}")

    out["laufzeit"] = {"wanduhr_s": round(time.monotonic() - t0, 2), "cpu_s": None,
                       "threads": 1, "s_je_partie": None}
    pathlib.Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"Artefakt: {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
