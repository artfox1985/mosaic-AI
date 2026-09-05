# -*- coding: utf-8 -*-
"""Skala B_est fuer den Rundenschaetzer-Term (PREREG_round_estimate_leaf_term.md par.4).

Replayt die Partie-Logs eines Arena-Artefakts (`--log-games`) Zug fuer Zug und
nimmt an jedem DRAFT-Zustand fuer beide Spieler den Rundenschaetzer

    E(pi) = tiling_potenzial(pi) + floor_penalty(pi)

aus `mosaic_rust.scoring_shaping_e_json` (lib.rs: `solve_round_final_score -
score` = Solver-Rundenscore mit greedy Chips; `projected_unplaceable_penalty`
= Strafleisten-Busse, Vorzeichen wie in mcts.rs::player_total). Berichtet je
Runde 1..4 die Verteilung von D = E(0) - E(1) (Median, P90 des Betrags,
Maximum) und die Komponenten getrennt, dazu die Regel aus par.4:
B_est = P90(|D|) / atanh(0,75).

Aufruf (CPU-Kern, Minuten; NICHT neben einer laufenden Messung):
    python -X utf8 -u tools/probes/round_estimate_scale_probe.py \
        --artifact evaluations/artifacts/paired_arena_env_v24b01_vs_b01_first_s14.json \
                   evaluations/artifacts/paired_arena_env_v24b01_vs_b01_second_s14.json \
        --out evaluations/artifacts/round_estimate_scale_probe.json
Weg ueber den Replayer wie `arena_column_probe.py` (Header voranstellen, Log
in Datei, `analyze_game_log.run`); die Draft-Zustaende werden per Wrapper um
`Replayer.apply` VOR jedem Draft-Zug abgegriffen.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import statistics
import sys
import tempfile
import time
from collections import defaultdict

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))          # tools/  (analyze_game_log)
sys.path.insert(0, str(HERE.parent.parent))   # Projektwurzel

DRAFT_METHODS = {"apply_stone", "apply_dome", "apply_dome_stack_peek",
                 "apply_dome_stack_choose", "apply_bonus_chip", "apply_start_tile"}


def estimates(mr, state_json: str) -> dict:
    out = {}
    for pi in (0, 1):
        e = json.loads(mr.scoring_shaping_e_json(state_json, pi))
        out[pi] = {"pot": float(e["tiling_potenzial"]), "pen": float(e["floor_penalty"]),
                   "round": int(e["round"])}
    return out


def replay_collect(game: dict, tmp_dir: str, idx: int, mr, samples: list) -> int:
    import analyze_game_log as agl
    header = {"players": game.get("names") or ["A", "B"],
              "first_player": game.get("first_player", 0),
              "seed": game.get("game_seed", 0)}
    path = pathlib.Path(tmp_dir) / f"game_{idx:05d}.log"
    path.write_text("# " + json.dumps(header, ensure_ascii=False) + "\n" + "\n".join(game["log"]) + "\n",
                    encoding="utf-8", newline="\n")
    seen = {"n": 0}
    orig_apply = agl.Replayer.apply
    orig_amb = agl.Replayer.apply_ambiguous

    def capture(self):
        try:
            sj = self.g.state_json()
        except Exception:
            return
        st = json.loads(sj)
        if not str(st.get("phase", "")).lower().startswith("draft"):
            return
        est = estimates(mr, sj)
        samples.append({
            "round": int(st.get("round_number", est[0]["round"])),
            "E0": est[0]["pot"] + est[0]["pen"], "E1": est[1]["pot"] + est[1]["pen"],
            "pot0": est[0]["pot"], "pot1": est[1]["pot"], "pen0": est[0]["pen"], "pen1": est[1]["pen"],
        })
        seen["n"] += 1

    def apply(self, lines, li, method, *args, **kwargs):
        if method in DRAFT_METHODS:
            capture(self)
        return orig_apply(self, lines, li, method, *args, **kwargs)

    def apply_ambiguous(self, lines, li, method, candidates):
        if method in DRAFT_METHODS:
            capture(self)
        return orig_amb(self, lines, li, method, candidates)

    agl.Replayer.apply = apply
    agl.Replayer.apply_ambiguous = apply_ambiguous
    try:
        _rep, _lines, _li, div = agl.run(path, model_path=None, sims=1, c_puct=0.3, do_oracle=False, limit=None)
    finally:
        agl.Replayer.apply = orig_apply
        agl.Replayer.apply_ambiguous = orig_amb
    if div:
        raise RuntimeError(f"ReplayDivergence: {div}")
    return seen["n"]


def pct(xs, q):
    if not xs:
        return None
    ys = sorted(xs)
    k = (len(ys) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return ys[lo] if lo == hi else ys[lo] + (ys[hi] - ys[lo]) * (k - lo)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--artifact", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=None, help="nur die ersten N Partien je Artefakt")
    a = ap.parse_args()
    import mosaic_rust as mr
    t0 = time.time()
    samples: list = []
    games_done = 0
    with tempfile.TemporaryDirectory() as tmp:
        for path in a.artifact:
            art = json.load(open(path, encoding="utf-8"))
            g = art.get("games") or {}
            lst = [sp for arm in (g.values() if isinstance(g, dict) else [g]) for sp in arm]
            if a.limit:
                lst = lst[:a.limit]
            for i, sp in enumerate(lst):
                n = replay_collect(sp, tmp, games_done, mr, samples)
                games_done += 1
                if games_done % 10 == 0:
                    print(f"  {games_done} Partien, {len(samples)} Draft-Zustaende ({time.time() - t0:.0f}s)", flush=True)
    by_round = defaultdict(list)
    for s in samples:
        by_round[s["round"]].append(s)
    out = {"prereg": "PREREG_round_estimate_leaf_term.md par.4", "artefakte": a.artifact,
           "partien": games_done, "draft_zustaende": len(samples), "je_runde": {}}
    all_abs = []
    for r in sorted(by_round):
        rows = by_round[r]
        d = [x["E0"] - x["E1"] for x in rows]
        dabs = [abs(v) for v in d]
        if r <= 4:
            all_abs.extend(dabs)
        pen = [x["pen0"] for x in rows] + [x["pen1"] for x in rows]
        pot = [x["pot0"] for x in rows] + [x["pot1"] for x in rows]
        out["je_runde"][f"R{r}"] = {
            "n": len(rows),
            "D_median": round(statistics.median(d), 3), "D_abs_p50": round(pct(dabs, 0.5), 3),
            "D_abs_p90": round(pct(dabs, 0.9), 3), "D_abs_max": round(max(dabs), 3),
            "pot_mittel": round(statistics.mean(pot), 3), "pot_p90": round(pct(pot, 0.9), 3),
            "pen_mittel": round(statistics.mean(pen), 3), "pen_anteil_ungleich_null": round(sum(1 for v in pen if v != 0) / len(pen), 3),
            "B_est_regel": round(pct(dabs, 0.9) / math.atanh(0.75), 3),
        }
        print(f"R{r}: n {len(rows)} | D median {out['je_runde'][f'R{r}']['D_median']} | |D| p90 {out['je_runde'][f'R{r}']['D_abs_p90']} "
              f"max {out['je_runde'][f'R{r}']['D_abs_max']} | pot mittel {out['je_runde'][f'R{r}']['pot_mittel']} | "
              f"Busse mittel {out['je_runde'][f'R{r}']['pen_mittel']} (ungleich 0: {out['je_runde'][f'R{r}']['pen_anteil_ungleich_null']}) | B_est {out['je_runde'][f'R{r}']['B_est_regel']}",
              flush=True)
    if all_abs:
        p90 = pct(all_abs, 0.9)
        out["R1_R4_gepoolt"] = {"n": len(all_abs), "D_abs_p90": round(p90, 3), "B_est_regel": round(p90 / math.atanh(0.75), 3)}
        print(f"R1-R4 gepoolt: |D| p90 {p90:.3f} -> B_est = {p90 / math.atanh(0.75):.3f}")
    out["laufzeit"] = {"wanduhr_s": round(time.time() - t0, 1), "cpu_s": round(time.process_time(), 1), "threads": 1,
                       "s_je_partie": round((time.time() - t0) / max(1, games_done), 2)}
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(f"Artefakt: {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
