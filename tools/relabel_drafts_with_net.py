# -*- coding: utf-8 -*-
"""PREREG_reanalyze_label_depth.md par.A4 -- Reanalyze im engeren Sinn: die
Draft-Policy-Ziele eines Korpus mit dem AKTUELLEN Netz bei tieferer Suche
nachrechnen.

Muster: tools/relabel_drafts_with_teacher.py (dort labelt der hv2-Lehrer per
One-Hot; hier labelt das Netz per Besuchsverteilung der Suche). Value-Felder
bleiben unveraendert (Partieausgang).

Ablauf je Datei:
  1. Datei nach `--out-dir` KOPIEREN, Praefix umschreiben
     (`selfplay_v22-b05-policy_*` -> `selfplay_v22-b05deep-policy_*`), damit der
     Datei-Cache-Schluessel (Basename!) nicht mit dem Original kollidiert
     (par.4b der Prereg).
  2. Draft-Records der Runden 1-4 des Spielers am Zug einsammeln, Zustaende
     in EINEM Stapel an `mosaic_rust.net_search_states_json_batch` geben
     (Netz wird einmal je Prozess geladen; der Einzel-Einstieg lud es je
     Aufruf und brauchte Sekunden je Zustand).
  3. Policy-Ziel = Besuchsanteile der Suche ueber ihre Kandidaten
     (`mcts_visits` / Summe), Kandidaten per `action_to_id` auf die
     `valid_actions` des Records abgebildet. Kein Treffer oder keine Besuche
     -> Record bleibt UNVERAENDERT und wird gezaehlt (stilles Wegwerfen ist
     ein Regelbruch).

Parallelisierung: N Worker-Prozesse ueber Dateien (jeder laedt das Netz
einmal). Aufruf (exklusiv, CPU):
    python -X utf8 -u tools/relabel_drafts_with_net.py \\
        --pattern "selfplay_v22-b05-policy_*.pkl" --in-dir data \\
        --out-dir data/relabeled_v23_deep --model models/alphazero_v23-b01_brierbest.onnx \\
        --sims 400 --workers 8
Smoke: --limit-files 1 --workers 1
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import pathlib
import sys
import time
from concurrent.futures import ProcessPoolExecutor

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))
from corpus_io import load_records, dump_records  # noqa: E402

OLD_PREFIX = "selfplay_v22-b05-policy_"
NEW_PREFIX = "selfplay_v22-b05deep-policy_"


def state_seed(state_json: str) -> int:
    return int(hashlib.md5(state_json.encode("utf-8")).hexdigest()[:15], 16)


def relabel_file(args):
    path, out_dir, model, sims, c_puct, batch_size = args
    import mosaic_rust as mr
    from neural_net import action_to_id
    recs = load_records(path)
    stats = {"records": len(recs), "kandidaten": 0, "relabelt": 0, "keine_besuche": 0,
             "nicht_abbildbar": 0, "keine_kandidaten": 0}
    idx, sjs, seeds = [], [], []
    for i, rec in enumerate(recs):
        st = rec.get("state") or {}
        if st.get("round") not in (1, 2, 3, 4) or st.get("phase") != "drafting":
            continue
        pi = rec.get("player")
        if pi is None or pi != st.get("current_player"):
            continue
        if not rec.get("policy") or not rec.get("valid_actions"):
            continue
        sj = json.dumps(st)
        idx.append(i); sjs.append(sj); seeds.append(state_seed(sj))
    stats["kandidaten"] = len(idx)
    t0 = time.monotonic()
    for start in range(0, len(idx), batch_size):
        chunk = slice(start, start + batch_size)
        outs = mr.net_search_states_json_batch(sjs[chunk], model, sims, c_puct, seeds[chunk])
        for i, out_s in zip(idx[chunk], outs):
            rec = recs[i]
            moves = (json.loads(out_s) or {}).get("moves") or []
            if not moves:
                stats["keine_kandidaten"] += 1
                continue
            by_id = {}
            for a in rec["valid_actions"]:
                try:
                    by_id.setdefault(action_to_id(a), a)
                except Exception:
                    continue
            visits = []
            for m in moves:
                if m.get("action") is None:
                    continue
                v = m.get("mcts_visits") or 0
                if v <= 0:
                    continue
                try:
                    aid = action_to_id(m["action"])
                except Exception:
                    continue
                if aid in by_id:
                    visits.append((by_id[aid], float(v)))
            if not visits:
                if all((m.get("mcts_visits") or 0) <= 0 for m in moves):
                    stats["keine_besuche"] += 1
                else:
                    stats["nicht_abbildbar"] += 1
                continue
            total = sum(v for _, v in visits)
            rec["policy"] = [{"action": a, "prob": v / total} for a, v in visits]
            stats["relabelt"] += 1
    stats["suche_s"] = round(time.monotonic() - t0, 1)
    base = os.path.basename(path)
    if not base.startswith(OLD_PREFIX):
        raise SystemExit("Unerwarteter Dateiname (Praefix): " + base)
    out_path = os.path.join(out_dir, NEW_PREFIX + base[len(OLD_PREFIX):])
    dump_records(out_path, recs)
    stats["out"] = os.path.basename(out_path)
    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--in-dir", default="data")
    ap.add_argument("--pattern", default="selfplay_v22-b05-policy_*.pkl")
    ap.add_argument("--out-dir", default="data/relabeled_v23_deep")
    ap.add_argument("--model", default="models/alphazero_v23-b01_brierbest.onnx")
    ap.add_argument("--sims", type=int, default=400)
    ap.add_argument("--c-puct", type=float, default=1.5)
    ap.add_argument("--batch-size", type=int, default=256)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit-files", type=int, default=None)
    ap.add_argument("--out", default=None, help="Artefakt (Default: evaluations/artifacts/relabel_net_<out-dir-name>.json)")
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(str(_ROOT), a.in_dir, a.pattern)))
    if a.limit_files:
        files = files[:a.limit_files]
    if not files:
        raise SystemExit("Keine Dateien fuer " + a.pattern + " in " + a.in_dir)
    out_dir = os.path.join(str(_ROOT), a.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    model = os.path.join(str(_ROOT), a.model)
    t0 = time.monotonic()
    agg = {"dateien": 0, "records": 0, "kandidaten": 0, "relabelt": 0, "keine_besuche": 0,
           "nicht_abbildbar": 0, "keine_kandidaten": 0}
    jobs = [(f, out_dir, model, a.sims, a.c_puct, a.batch_size) for f in files]
    n_workers = max(1, min(a.workers, len(files)))
    done = 0
    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        for st in ex.map(relabel_file, jobs):
            done += 1
            for k in agg:
                if k == "dateien":
                    continue
                agg[k] += st[k]
            agg["dateien"] += 1
            print("  " + str(done) + "/" + str(len(files)) + " " + st["out"] + ": " + str(st["relabelt"])
                  + "/" + str(st["kandidaten"]) + " relabelt (Suche " + str(st["suche_s"]) + " s), "
                  + str(round(time.monotonic() - t0)) + " s gesamt", flush=True)
    wall = round(time.monotonic() - t0, 1)
    result = {"prereg": "PREREG_reanalyze_label_depth.md par.A4 (Teil A2, Reanalyze i.e.S.)",
              "in_dir": a.in_dir, "pattern": a.pattern, "out_dir": a.out_dir, "model": a.model,
              "sims": a.sims, "c_puct": a.c_puct, "workers": n_workers, **agg,
              "laufzeit": {"wanduhr_s": wall, "cpu_s": None, "threads": n_workers,
                           "s_je_partie": None,
                           "s_je_zustand": round(wall * n_workers / max(1, agg["kandidaten"]), 4)}}
    out = a.out or os.path.join("evaluations", "artifacts", "relabel_net_" + os.path.basename(a.out_dir.rstrip("/\\")) + ".json")
    out_path = os.path.join(str(_ROOT), out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
    print("Fertig: " + str(agg["relabelt"]) + "/" + str(agg["kandidaten"]) + " relabelt, "
          + str(agg["nicht_abbildbar"]) + " nicht abbildbar, " + str(agg["keine_besuche"]) + " ohne Besuche, "
          + str(agg["keine_kandidaten"]) + " ohne Kandidaten; " + str(wall) + " s. Artefakt: " + out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
