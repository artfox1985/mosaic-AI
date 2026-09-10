# -*- coding: utf-8 -*-
"""PRE/POST-Vergleich der Kuppelstapel-Prereg (PREREG_dome_stack_information_sets.md par.12/par.15a).

Liest zwei Orakel-Artefakte von `tools/analyze_game_log.py --oracle-json` (JSON-Zeilen,
eine je bewerteter Entscheidung) und stellt je Stapelzug Rang und Q des gespielten Zuges
gegenueber. PRE = Vollmischung (MOSAIC_DOME_POOL_KNOWLEDGE=0), POST = Variante A, beide auf
DEMSELBEN Wheel und dem exakten Zustand (`state_exact` im Record).

Aufruf:
    python -X utf8 tools/probes/dome_stack_pre_post_compare.py \
        evaluations/artifacts/replay_dome_stack_pre_exact.json \
        evaluations/artifacts/replay_dome_stack_post_exact.json \
        --out evaluations/artifacts/dome_stack_pre_post_compare.json
"""
import argparse
import io
import json
import sys
import time


def load(path):
    return [json.loads(l) for l in io.open(path, encoding="utf-8") if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pre")
    ap.add_argument("post")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    t0 = time.time()
    pre, post = load(a.pre), load(a.post)
    if len(pre) != len(post):
        sys.exit(f"Zeilenzahl verschieden: PRE {len(pre)}, POST {len(post)}")
    rows = []
    for x, y in zip(pre, post):
        if not (x.get("evaluated") and y.get("evaluated")):
            continue
        rows.append({
            "turn": x["turn_idx"], "round": x["round_num"], "kind": x["kind"], "actor": x["actor"],
            "played": x["played_desc"][:60],
            "rank_pre": x["played_rank"], "rank_post": y["played_rank"],
            "q_pre": x["played_q"], "q_post": y["played_q"],
            "root_pre": x["root_value"], "root_post": y["root_value"],
            "top_pre": (x.get("top_desc") or "")[:50], "top_post": (y.get("top_desc") or "")[:50],
            "state_exact": (x.get("state_exact"), y.get("state_exact")),
        })
    stack = [r for r in rows if r["kind"] in ("dome_stack", "dome_stack_peek")]
    changed = [r for r in rows if r["rank_pre"] != r["rank_post"] or abs((r["q_pre"] or 0) - (r["q_post"] or 0)) > 1e-9]
    print(f"bewertet {len(rows)} (PRE {len(pre)} Zeilen), Stapelzuege {len(stack)}, "
          f"Entscheidungen mit Aenderung {len(changed)}")
    print(f"exakter Zustand: PRE {sum(1 for r in rows if r['state_exact'][0])}, POST {sum(1 for r in rows if r['state_exact'][1])} von {len(rows)}")
    print(f"{'turn':>4} {'R':>2} {'kind':16} {'rk_pre':>6} {'rk_post':>7} {'q_pre':>7} {'q_post':>7} {'root_pre':>8} {'root_post':>9}  gespielt")
    for r in stack:
        print(f"{r['turn']:>4} {r['round']:>2} {r['kind']:16} {r['rank_pre']:>6} {r['rank_post']:>7} "
              f"{r['q_pre']:>7.3f} {r['q_post']:>7.3f} {r['root_pre']:>8.3f} {r['root_post']:>9.3f}  {r['played'][:44]}")
    for name, key in (("PRE", "rank_pre"), ("POST", "rank_post")):
        print(f"{name}: Rang-1-Anteil alle {sum(1 for r in rows if r[key] == 1)}/{len(rows)}, "
              f"Stapelzuege {sum(1 for r in stack if r[key] == 1)}/{len(stack)}, "
              f"mittlerer Rang Stapelzuege {sum(r[key] for r in stack) / max(1, len(stack)):.2f}")
    out = {"pre": a.pre, "post": a.post, "n_bewertet": len(rows), "n_stapelzuege": len(stack),
           "n_geaendert": len(changed), "rows": rows,
           "laufzeit": {"wanduhr_s": round(time.time() - t0, 3), "cpu_s": None, "threads": 1, "s_je_partie": None}}
    if a.out:
        io.open(a.out, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
        print("Artefakt:", a.out)


if __name__ == "__main__":
    main()
