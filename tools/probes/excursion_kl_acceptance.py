# -*- coding: utf-8 -*-
"""tools/probes/excursion_kl_acceptance.py -- KL-Abnahme des Ausflugs (PREREG_targeted_branching.md par.7).

Greift der Knopf `MOSAIC_EXCURSION_KL_WEIGHT` 1, also zweigt der Ausflug an Stellen hoher
Policy-Diskrepanz ab? Beide Seiten in der OFFLINE-Definition (Praezisierung par.7):

  Abzweig     Werkzeug-KL am ersten Record jedes Ausflugs (der Record, der `branch_kl` traegt)
  Referenz    Werkzeug-KL aller Drafting-Records einer gezogenen Datei-Stichprobe der Erzeugung
              (je Klasse gleich viele Dateien, fester Seed)

  Abnahme     Median(Abzweig) > 75-%-Quantil(Referenz), sonst "greift nicht" (Bau pruefen, nicht deuten)

Die KL rechnet `targeted_branching_pretest.policy_kl` (eine Stelle der Formel), Prior aus dem
GENERATOR der Erzeugung. Daneben: `branch_kl` (Engine, f32, determinisierte Wurzel) gegen die
Werkzeug-KL derselben Records, Spearman. Filter je Record wie im Vortest-Werkzeug (Drafting,
Runde 1-4, `completed` nicht False, Policy-Ziel mit mindestens zwei Aktions-IDs), aber OHNE die
Bedingung `root_q`/`winner`, die nur die Brier-Rechnung braucht.

    python -X utf8 -u tools/probes/excursion_kl_acceptance.py --prefix v33-b01 \
        --model models/alphazero_v33-b01_brierbest.pth --out evaluations/artifacts/excursion_kl_acceptance_v34.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import sys
import time
from pathlib import Path

os.environ["MOSAIC_FEATURES_FROM_RUST"] = "1"   # vor dem Import von neural_net

import numpy as np  # noqa: E402

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "tools"))
sys.path.insert(0, str(BASE_DIR / "tools" / "probes"))
sys.path.insert(0, str(BASE_DIR / "engine" / "py"))
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

from runtime_block import laufzeit_block  # noqa: E402
from targeted_branching_pretest import policy_kl, spearman  # noqa: E402

ROUNDS = (1, 2, 3, 4)
CLASSES = ("policy", "value-wegc", "value-excursion")


def eligible(step, action_to_id):
    """(state, round, targ) oder None, Filter wie im Vortest-Werkzeug ohne root_q/winner."""
    st = step.get("state") or {}
    if not isinstance(st, dict) or st.get("phase") != "drafting" or step.get("completed", True) is False:
        return None
    rnd = int(st.get("round", 0))
    if rnd not in ROUNDS:
        return None
    targ: dict[int, float] = {}
    try:
        for pe in step.get("policy") or []:
            aid = action_to_id(pe["action"])
            targ[aid] = targ.get(aid, 0.0) + float(pe["prob"])
    except Exception:  # noqa: BLE001
        return None
    if len(targ) < 2 or sum(targ.values()) <= 0:
        return None
    return st, rnd, targ


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prefix", required=True, help="Versionspraefix der Erzeugung, z. B. v33-b01")
    ap.add_argument("--model", required=True, help="Generator der Erzeugung (.pth)")
    ap.add_argument("--files-per-class", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20261001)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--out", required=True)
    ap.add_argument("--classes", nargs="+", default=list(CLASSES),
                    help="Klassen der Erzeugung (v35: value-deviate statt value-wegc, ohne policy)")
    args = ap.parse_args()
    t_start, c_start = time.monotonic(), time.process_time()

    import torch
    import neural_net
    from neural_net import action_to_id, build_model_from_checkpoint, state_to_planes, state_to_tensor
    from corpus_io import load_records
    assert neural_net._FEATURES_FROM_RUST, "Rust-Bauer nicht aktiv"
    torch.set_num_threads(max(1, (os.cpu_count() or 2) - 1))
    blob = torch.load(BASE_DIR / args.model, map_location="cpu", weights_only=False)
    model, encoder = build_model_from_checkpoint(blob)[:2]
    model.eval()

    def kls(items):
        out = []
        for i in range(0, len(items), args.batch):
            chunk = items[i:i + args.batch]
            states = [c[0] for c in chunk]
            with torch.no_grad():
                flat = torch.stack([state_to_tensor(d) for d in states])
                o = model(torch.stack([state_to_planes(d) for d in states]), flat) if encoder == "2d" else model(flat)
            logits = o[0].numpy()
            out += [policy_kl(logits[j], c[2]) for j, c in enumerate(chunk)]
        return np.array(out)

    data = BASE_DIR / "data"
    # --- Abzweig: Records mit branch_kl in der Ausflug-Klasse ---------------------------------
    exc_files = sorted(glob.glob(str(data / f"selfplay_{args.prefix}-value-excursion_*.pkl")))
    branch, branch_engine, branch_round, n_branch_all, n_branch_filtered = [], [], [], 0, 0
    for k, f in enumerate(exc_files):
        for step in load_records(f):
            if "branch_kl" not in step:
                continue
            n_branch_all += 1
            e = eligible(step, action_to_id)
            if e is None:
                n_branch_filtered += 1
                continue
            branch.append(e); branch_engine.append(float(step["branch_kl"])); branch_round.append(e[1])
        if (k + 1) % 50 == 0 or k + 1 == len(exc_files):
            print(f"[kl-abnahme] Ausflug {k + 1}/{len(exc_files)} Dateien, {len(branch)} Abzweig-Records, "
                  f"{time.monotonic() - t_start:.0f} s", flush=True)
    kl_branch = kls(branch)

    # --- Referenz: alle Drafting-Records einer Datei-Stichprobe je Klasse -----------------------
    rng = random.Random(args.seed)
    ref_files = []
    for c in args.classes:
        fs = sorted(glob.glob(str(data / f"selfplay_{args.prefix}-{c}_*.pkl")))
        ref_files += sorted(rng.sample(fs, min(args.files_per_class, len(fs))))
    ref, ref_class = [], []
    for k, f in enumerate(ref_files):
        cls = Path(f).name[len(f"selfplay_{args.prefix}-"):].rsplit("_", 3)[0]
        for step in load_records(f):
            e = eligible(step, action_to_id)
            if e is not None:
                ref.append(e); ref_class.append(cls)
        print(f"[kl-abnahme] Referenz {k + 1}/{len(ref_files)} {Path(f).name}: gesamt {len(ref)}, "
              f"{time.monotonic() - t_start:.0f} s", flush=True)
    kl_ref = kls(ref)

    med_b = float(np.median(kl_branch))
    q75 = float(np.quantile(kl_ref, 0.75))
    rank_of_median = float((kl_ref < med_b).mean())
    ref_class = np.array(ref_class)
    out = {
        "prereg": "evaluations/PREREG_targeted_branching.md par.7", "prefix": args.prefix, "model": args.model,
        "grundmenge": {
            "abzweig": "erster Record jedes Ausflugs (traegt branch_kl), Filter Drafting R1-4, >= 2 IDs; Einheit Record",
            "referenz": f"alle Drafting-Records R1-4 aus {args.files_per_class} Dateien je Klasse (Seed {args.seed}); Einheit Record",
        },
        "n_abzweig_mit_branch_kl": n_branch_all, "n_abzweig_ausgefiltert": n_branch_filtered,
        "n_abzweig": int(len(kl_branch)), "n_referenz": int(len(kl_ref)),
        "referenz_dateien": [Path(f).name for f in ref_files],
        "abzweig_kl": {"median": med_b, "q25": float(np.quantile(kl_branch, 0.25)),
                       "q75": float(np.quantile(kl_branch, 0.75)), "mittel": float(kl_branch.mean())},
        "referenz_kl": {"median": float(np.median(kl_ref)), "q75": q75, "q90": float(np.quantile(kl_ref, 0.9)),
                        "mittel": float(kl_ref.mean()),
                        "je_klasse_median": {c: float(np.median(kl_ref[ref_class == c])) for c in sorted(set(ref_class))}},
        "median_abzweig_als_quantil_der_referenz": rank_of_median,
        "abnahme": "GREIFT" if med_b > q75 else "GREIFT NICHT",
        "branch_kl_engine": {"median": float(np.median(branch_engine)),
                             "spearman_gegen_werkzeug_kl": spearman(np.array(branch_engine), kl_branch)},
        "abzweig_je_runde": {str(r): int((np.array(branch_round) == r).sum()) for r in ROUNDS},
    }
    out["laufzeit"] = laufzeit_block(t_start, cpu_start=c_start, threads=torch.get_num_threads(),
                                     n_units=int(len(kl_branch) + len(kl_ref)), unit="record")
    op = BASE_DIR / args.out
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[kl-abnahme] Median Abzweig {med_b:.4f} gegen q75 Referenz {q75:.4f} "
          f"(Median liegt auf Quantil {rank_of_median:.3f}) -> {out['abnahme']}; "
          f"Spearman branch_kl/Werkzeug {out['branch_kl_engine']['spearman_gegen_werkzeug_kl']:+.3f}", flush=True)
    print(f"Ergebnis: {op} ({out['laufzeit']['wanduhr_s']} s)", flush=True)


if __name__ == "__main__":
    main()
