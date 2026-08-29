# -*- coding: utf-8 -*-
"""par.3b.8 (Nachtrag Draft-Check) -- On-Policy-Lehrer-Treue, LIVE-Variante.

Frage: draftet das Netz auf seinen EIGENEN Brettern noch wie der Lehrer?
Die pkl-Variante scheiterte am exact-Schema (die Trainings-Records tragen
die verdeckten Felder wie dome_pool_order_exact nicht -- nicht treu
rekonstruierbar). Deshalb LIVE nach dem Golden-Probe-Muster: b04 spielt
gegen sich selbst (RefereeGame, in-process), und an jeder
Drafting-Entscheidung wird der exakte Zustand ZWEIMAL befragt:

  * Netz-Zug: net_arena_choice_state_json mit dem pending_search_seed der
    Partie -- deterministisch identisch mit dem gleich darauf gespielten Zug.
  * Lehrer-Zug: frozen_champion_worker des hv2_generator-Artefakts
    (kind=drafting, gleicher Zustand).

Kennzahlen je Runde, getrennt fuer Vollendungs-Stellen (eigene Spalte
4-5/6): Zug-Uebereinstimmung (type/factory_index/color/row, moon_order
ignoriert wie action_to_id), Anteil Drafts in lange Musterreihen (row 4/5),
und an Stellen: bedient der Zug die Rasterzeile der fehlenden Spaltenzelle.

Aufruf (exklusiv; Netz-Suche 400 Sims je Entscheidung, ~1 s je Zug):
    python -X utf8 -u tools/probes/onpolicy_teacher_draft_fidelity_probe.py --games 30
Smoke: --games 2
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

ARTIFACT = _ROOT / "evaluations" / "artifacts" / "onpolicy_teacher_draft_fidelity.json"
PREREG = "PREREG_heuristic_v2_long_rows.md par.3b.8 (Draft-Check, live)"
WORKER_ARTIFACT = _ROOT / "models" / "frozen_heuristics" / "hv2_generator"
MODEL = str(_ROOT / "models" / "alphazero_v22-b04_best.onnx")
SPEC = str(_ROOT / "models" / "champion_frozen.spec.json")
LONG_ROWS = (4, 5)


def worker_start():
    py = WORKER_ARTIFACT / "venv" / "Scripts" / "python.exe"
    if not py.exists():
        py = WORKER_ARTIFACT / "venv" / "bin" / "python"
    return subprocess.Popen(
        [str(py), str(_ROOT / "tools" / "frozen_champion_worker.py"), str(WORKER_ARTIFACT)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, encoding="utf-8", cwd=str(_ROOT))


def worker_ask(proc, state_json, seed):
    proc.stdin.write(json.dumps({"kind": "drafting", "state": state_json,
                                 "seed": seed}) + "\n")
    proc.stdin.flush()
    resp = json.loads(proc.stdout.readline())
    if not resp.get("ok"):
        raise RuntimeError(resp.get("error", "Worker-Fehler ohne Text"))
    return resp["action"]


def act_key(a):
    return (a.get("type"), a.get("factory_index"), a.get("color"), a.get("row"))


def occupancy_grid(dome):
    grid = [[0] * 6 for _ in range(6)]
    for sr in range(3):
        row = dome[sr] if sr < len(dome) else []
        for sc in range(3):
            slot = row[sc] if sc < len(row) else None
            spaces = (slot or {}).get("spaces", []) if slot else []
            for si in range(4):
                sp = spaces[si] if si < len(spaces) else None
                grid[sr * 2 + si // 2][sc * 2 + si % 2] = (
                    1 if (sp and sp.get("filled") is not None) else 0)
    return grid


def completion_site_rows(player):
    geo = player.get("score_geo") or {}
    cf = geo.get("col_fill") or []
    cols = [c for c, f in enumerate(cf) if 4 <= f < 6]
    if not cols:
        return []
    grid = occupancy_grid(player.get("dome_grid") or [])
    return sorted({r for c in cols for r in range(6) if not grid[r][c]})


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--games", type=int, default=30)
    ap.add_argument("--sims", type=int, default=400)
    ap.add_argument("--c-puct", type=float, default=1.5)
    ap.add_argument("--seed-base", type=int, default=926000)
    args = ap.parse_args()
    t0 = time.time()

    import mosaic_rust as mr
    proc = worker_start()
    agg = {}
    queries = errors = 0
    try:
        for g in range(args.games):
            rg = mr.RefereeGame(("A", "B"), g % 2, args.seed_base + g, None)
            guard = 0
            while True:
                guard += 1
                if guard > 100_000:
                    raise RuntimeError("Schritt-Limit ueberschritten")
                status = rg.advance_to_decision(MODEL, MODEL)
                if status == "game_over":
                    rg.finalize_scoring()
                    break
                if status == "stuck":
                    raise RuntimeError(f"Deadlock bei steps={rg.steps()}")
                rnd = rg.round_number()
                if guard % 25 == 0:
                    print(f"  Partie {g + 1}: Schritt {guard}, Runde {rnd}, "
                          f"{queries} Vergleiche ({time.time() - t0:.0f}s)", flush=True)
                state_json = rg.state_json()
                seed = rg.pending_search_seed()
                st = json.loads(state_json)
                pi = st.get("current_player")
                net_resp = json.loads(mr.net_arena_choice_state_json(
                    state_json, MODEL, args.sims, args.c_puct, seed, SPEC))
                # Antwort-Huelle: {"action": {...}, ...} (wie golden_probe sie liest)
                net_a = net_resp.get("action") or {}
                # weiterziehen unabhaengig vom Vergleich
                rg.drafting_decide_and_apply_inprocess(MODEL, SPEC, args.sims, args.c_puct)
                if rnd not in (1, 2, 3, 4) or net_a.get("type") != "stone":
                    continue
                site_rows = completion_site_rows(st["players"][pi])
                try:
                    t_a = worker_ask(proc, state_json, seed)
                except Exception:
                    errors += 1
                    if errors > 30:
                        raise
                    continue
                if t_a.get("type") != "stone":
                    continue
                queries += 1
                d = agg.setdefault((rnd, bool(site_rows)),
                                   {"n": 0, "gleich": 0, "lehrer_lang": 0,
                                    "netz_lang": 0, "lehrer_bedient": 0,
                                    "netz_bedient": 0, "site_n": 0})
                d["n"] += 1
                d["gleich"] += int(act_key(t_a) == act_key(net_a))
                d["lehrer_lang"] += int(t_a.get("row") in LONG_ROWS)
                d["netz_lang"] += int(net_a.get("row") in LONG_ROWS)
                if site_rows:
                    d["site_n"] += 1
                    d["lehrer_bedient"] += int(t_a.get("row") in site_rows)
                    d["netz_bedient"] += int(net_a.get("row") in site_rows)
            print(f"  Partie {g + 1}/{args.games} fertig, {queries} Vergleiche "
                  f"({time.time() - t0:.0f}s, {errors} Worker-Fehler)", flush=True)
    finally:
        try:
            proc.stdin.close(); proc.terminate()
        except Exception:
            pass

    result = {"prereg": PREREG, "modell": pathlib.Path(MODEL).name, "spiele": args.games,
              "sims": args.sims, "vergleiche": queries, "worker_fehler": errors,
              "je_runde_und_stelle": {}}
    for (rnd, site), d in sorted(agg.items()):
        n = d["n"]
        result["je_runde_und_stelle"][f"runde{rnd}_{'site' if site else 'normal'}"] = {
            "n": n,
            "zug_gleich": d["gleich"] / n,
            "lehrer_lange_reihe": d["lehrer_lang"] / n,
            "netz_lange_reihe": d["netz_lang"] / n,
            "lehrer_bedient_fehlzeile": (d["lehrer_bedient"] / d["site_n"]) if d["site_n"] else None,
            "netz_bedient_fehlzeile": (d["netz_bedient"] / d["site_n"]) if d["site_n"] else None,
        }
    result["laufzeit"] = {"wanduhr_s": round(time.time() - t0, 1), "threads": 1}
    ARTIFACT.write_text(json.dumps(result, indent=1, ensure_ascii=False),
                        encoding="utf-8", newline="\n")
    for k, v in result["je_runde_und_stelle"].items():
        print(f"{k}: n={v['n']} gleich={v['zug_gleich']:.3f} "
              f"langeReihe L/N={v['lehrer_lange_reihe']:.3f}/{v['netz_lange_reihe']:.3f} "
              f"bedient L/N={v['lehrer_bedient_fehlzeile']}/{v['netz_bedient_fehlzeile']}",
              flush=True)
    print(f"Artefakt: {ARTIFACT}", flush=True)


if __name__ == "__main__":
    main()
