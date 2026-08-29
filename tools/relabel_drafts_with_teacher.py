# -*- coding: utf-8 -*-
"""par.3b.9 -- Lehrer-Relabeling der Draft-Entscheidungen (DAgger-Muster).

Liest die dagger-b04-Partien, legt jeden Draft-Zustand (Runden 1-4, Spieler
am Zug) dem gefrorenen hv2_generator-Worker vor und ersetzt das
Policy-Ziel des Records durch den One-Hot-Lehrerzug. Value-Felder bleiben
unveraendert (Ausgang der gespielten Partie).

Exact-Schema-Bruecke: mosaic_rust.state_json_to_exact_json determinisiert
die verdeckte Information seeded (registrierter Vorbehalt par.3b.9).
Ein Lehrerzug, der nicht auf eine Aktion der aufgezeichneten Policy-Liste
passt (type/factory_index/color/row), laesst den Record UNVERAENDERT und
wird gezaehlt -- stilles Wegwerfen ist ein Regelbruch.

Parallelisierung: N Worker-Prozesse, Dateien round-robin.

Aufruf (exklusiv):
    python -X utf8 -u tools/relabel_drafts_with_teacher.py \
        --in-dir data/onpolicy_v22-b05 --workers 8
Smoke: --limit-files 1 --workers 1
"""
from __future__ import annotations

import argparse
import glob
import json
import pathlib
import subprocess
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from corpus_io import load_records, dump_records  # noqa: E402

WORKER_ARTIFACT = _ROOT / "models" / "frozen_heuristics" / "hv2_generator"
ARTIFACT = _ROOT / "evaluations" / "artifacts" / "relabel_dagger_b04.json"


def worker_start():
    py = WORKER_ARTIFACT / "venv" / "Scripts" / "python.exe"
    if not py.exists():
        py = WORKER_ARTIFACT / "venv" / "bin" / "python"
    return subprocess.Popen(
        [str(py), str(_ROOT / "tools" / "frozen_champion_worker.py"), str(WORKER_ARTIFACT)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, encoding="utf-8", cwd=str(_ROOT))


def worker_ask(proc, exact_json, seed):
    proc.stdin.write(json.dumps({"kind": "drafting", "state": exact_json,
                                 "seed": seed}) + "\n")
    proc.stdin.flush()
    resp = json.loads(proc.stdout.readline())
    if not resp.get("ok"):
        raise RuntimeError(resp.get("error", "Worker-Fehler ohne Text"))
    return resp["action"]


def act_key(a):
    return (a.get("type"), a.get("factory_index"), a.get("color"), a.get("row"))


def relabel_file(path, proc, mr, stats, seed_base):
    recs = load_records(path)
    changed = 0
    for i, rec in enumerate(recs):
        st = rec.get("state") or {}
        if st.get("round") not in (1, 2, 3, 4):
            continue
        pol = rec.get("policy") or []
        if not pol:
            continue
        top = max(pol, key=lambda e: e.get("prob", 0.0)).get("action") or {}
        if top.get("type") != "stone":
            continue
        pi = rec.get("player")
        if pi is None or pi != st.get("current_player"):
            continue
        stats["kandidaten"] += 1
        try:
            exact = mr.state_json_to_exact_json(json.dumps(st), seed_base + i)
            t_a = worker_ask(proc, exact, seed_base + i)
        except Exception as e:
            stats["fehler"] += 1
            stats.setdefault("fehler_beispiele", [])
            if len(stats["fehler_beispiele"]) < 3:
                stats["fehler_beispiele"].append(str(e)[:160])
            continue
        if t_a.get("type") != "stone":
            stats["lehrer_kein_stone"] += 1
            continue
        tk = act_key(t_a)
        match = next((e for e in pol if act_key(e.get("action") or {}) == tk), None)
        if match is None:
            stats["nicht_abbildbar"] += 1
            continue
        # One-Hot-Lehrerziel: exakt der Eintrag aus der aufgezeichneten
        # Policy-Liste (traegt das komplette Action-Dict inkl. moon_order).
        rec["policy"] = [{"action": match["action"], "prob": 1.0}]
        stats["relabelt"] += 1
        changed += 1
    if changed:
        dump_records(path, recs)
    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--in-dir", default="data/onpolicy_v22-b05")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit-files", type=int, default=None)
    ap.add_argument("--seed-base", type=int, default=936000)
    args = ap.parse_args()
    t0 = time.time()

    import mosaic_rust as mr
    files = sorted(glob.glob(str(_ROOT / args.in_dir / "*.pkl")))
    if args.limit_files:
        files = files[:args.limit_files]
    if not files:
        raise SystemExit(f"keine Dateien in {args.in_dir}")

    # Ein Worker je Slot; Dateien sequenziell je Slot (multiprocessing im
    # Python-Teil lohnt nicht -- der Engpass ist der Worker-Prozess selbst).
    import threading
    n = max(1, min(args.workers, len(files)))
    slots = [files[k::n] for k in range(n)]
    stats_all = []
    lock = threading.Lock()
    done_files = [0]

    def run_slot(slot_files, slot_idx):
        proc = worker_start()
        stats = {"kandidaten": 0, "relabelt": 0, "fehler": 0,
                 "nicht_abbildbar": 0, "lehrer_kein_stone": 0}
        try:
            for fpath in slot_files:
                relabel_file(fpath, proc, mr, stats,
                             args.seed_base + hash(pathlib.Path(fpath).name) % 100000)
                with lock:
                    done_files[0] += 1
                    print(f"  {done_files[0]}/{len(files)} Dateien "
                          f"({time.time() - t0:.0f}s)", flush=True)
        finally:
            try:
                proc.stdin.close(); proc.terminate()
            except Exception:
                pass
        with lock:
            stats_all.append(stats)

    threads = [threading.Thread(target=run_slot, args=(s, k)) for k, s in enumerate(slots)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    agg = {k: sum(s[k] for s in stats_all)
           for k in ("kandidaten", "relabelt", "fehler", "nicht_abbildbar", "lehrer_kein_stone")}
    agg["fehler_beispiele"] = [b for s in stats_all for b in s.get("fehler_beispiele", [])][:5]
    result = {"prereg": "PREREG_heuristic_v2_long_rows.md par.3b.9",
              "in_dir": args.in_dir, "dateien": len(files), "workers": n, **agg,
              "laufzeit": {"wanduhr_s": round(time.time() - t0, 1), "threads": n,
                           "s_je_label": round((time.time() - t0) / max(1, agg["relabelt"]), 3)}}
    ARTIFACT.write_text(json.dumps(result, indent=1, ensure_ascii=False),
                        encoding="utf-8", newline="\n")
    print(f"\nrelabelt {agg['relabelt']}/{agg['kandidaten']} "
          f"(nicht abbildbar {agg['nicht_abbildbar']}, Fehler {agg['fehler']}, "
          f"kein Stone {agg['lehrer_kein_stone']})")
    print(f"Artefakt: {ARTIFACT}", flush=True)


if __name__ == "__main__":
    main()
