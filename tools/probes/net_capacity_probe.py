# -*- coding: utf-8 -*-
"""Netzauslastung eines Checkpoints (Dead-Neuronen, Aktiv-Rate, effektiver Rang je ReLU-Schicht).

Dieselbe Kennzahl wie train.py Schritt 5b ("NETZAUSLASTUNG"), aber nachtraeglich am
gespeicherten Checkpoint und fuer BEIDE Modellfamilien (`MosaicNet.analyze_capacity`,
`Mosaic2DNet.analyze_capacity`). Anlass 2026-09-06: fuer 2D-Netze sprang train.py den
Schritt seit v19 still ueber; Nutzer: "schau mal wie das b05 netz von der
netzauslastung/-gesundheit dasteht."

Eingabe: N Zustaende aus Korpusdateien (`corpus_io.load_records`), kodiert mit
`state_to_planes` / `state_to_tensor` (Flachteil auf die Modellbreite gekuerzt, das
Layout ist append-only). Vorwaertslauf auf CUDA, wenn vorhanden.

Aufruf:
    python -X utf8 tools/probes/net_capacity_probe.py --models v24-b05_brierbest v23-b01_brierbest \\
        --file-list data/window_v24.txt --n-states 512 --out evaluations/artifacts/net_capacity_v24.json
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))

import torch  # noqa: E402
import corpus_io  # noqa: E402
from neural_net import build_model_from_checkpoint, state_to_planes, state_to_tensor  # noqa: E402


def sample_states(file_list: Path, n: int, seed: int) -> list[dict]:
    files = [l.strip() for l in file_list.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    rng = random.Random(seed)
    rng.shuffle(files)
    states: list[dict] = []
    per_file = max(1, n // 16)
    for f in files:
        path = REPO / "data" / f if not (REPO / f).exists() else REPO / f
        try:
            recs = corpus_io.load_records(path)
        except Exception:
            continue
        cand = [r["state"] for r in recs if isinstance(r, dict) and isinstance(r.get("state"), dict)]
        rng.shuffle(cand)
        states.extend(cand[:per_file])
        if len(states) >= n:
            break
    return states[:n]


def encode(states: list[dict], input_size: int):
    planes = torch.stack([state_to_planes(s).float() for s in states])
    flat = torch.stack([state_to_tensor(s)[:input_size] for s in states])
    return planes, flat


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", nargs="+", required=True, help="Checkpoint-Namen ohne 'alphazero_' und '.pth'")
    ap.add_argument("--file-list", default="data/window_v24.txt")
    ap.add_argument("--n-states", type=int, default=512)
    ap.add_argument("--seed", type=int, default=20260906)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    t0 = time.time()
    states = sample_states(REPO / a.file_list, a.n_states, a.seed)
    print(f"{len(states)} Zustaende aus {a.file_list} (Seed {a.seed}, {time.time() - t0:.1f}s)", flush=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    out = {"n_states": len(states), "file_list": a.file_list, "seed": a.seed, "device": device, "modelle": {}}
    for name in a.models:
        pth = REPO / "models" / f"alphazero_{name}.pth"
        ckpt = torch.load(pth, map_location="cpu", weights_only=False)
        model, encoder = build_model_from_checkpoint(ckpt)
        model.to(device).eval()
        in_size = model.input_size if hasattr(model, "input_size") else ckpt.get("input_size")
        planes, flat = encode(states, in_size)
        with torch.no_grad():
            if encoder == "2d":
                cap = model.analyze_capacity(planes.to(device), flat.to(device))
            else:
                cap = model.analyze_capacity(flat.to(device))
        avg_dead = sum(m["dead_ratio"] for m in cap.values()) / len(cap)
        avg_rank = sum(m["rank_pct"] for m in cap.values()) / len(cap)
        verdict = ("ROT: viele tote Neuronen" if avg_dead > 0.4 else
                   "GELB: hohe Auslastung, bei Plateau mehr Neuronen erwaegen" if avg_rank > 0.7 else "GRUEN: gesunde Auslastung")
        print(f"\n== {name} ({encoder}, input {in_size}, hidden {ckpt.get('hidden_size')}, Epochen {ckpt.get('epochs')})")
        print(f"  {'Schicht':<9} {'Dead':>12} {'Aktiv-Rate':>11} {'Eff.Rank':>16}")
        for ln, m in cap.items():
            print(f"  {ln:<9} {m['dead']}/{m['n_neurons']} ({m['dead_ratio'] * 100:.0f}%)".ljust(24)
                  + f"{m['active_rate'] * 100:>10.0f}%  {m['eff_rank']:.0f}/{m.get('rank_base', m['n_neurons'])} ({m['rank_pct'] * 100:.0f}%)")
        print(f"  -> Dead {avg_dead * 100:.0f} %, Eff.Rank {avg_rank * 100:.0f} %: {verdict}", flush=True)
        out["modelle"][name] = {"encoder": encoder, "input_size": in_size, "hidden_size": ckpt.get("hidden_size"),
                                "epochs": ckpt.get("epochs"), "schichten": cap, "dead_mittel": avg_dead,
                                "rank_mittel": avg_rank, "verdikt": verdict}
    out["laufzeit"] = {"wanduhr_s": round(time.time() - t0, 1), "cpu_s": round(time.process_time(), 1), "threads": 1}
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(f"Artefakt: {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
