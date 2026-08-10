# -*- coding: utf-8 -*-
"""Teil 1 der GPU-Inferenz-Batcher-Machbarkeitsprobe
(`evaluations/PREREG_gpu_inferenz_batcher.md`, Alt-Nummer #82).

Messgroesse: **Evals/s des Vorwaerts-Passes** bei wachsender Batchgroesse,
auf der GPU. Die Frage ist NICHT "ist die GPU schneller als ein CPU-Kern"
(trivial ja), sondern: schlaegt sie den CPU-AGGREGATDURCHSATZ von 11
parallelen Self-Play-Threads bei dem Batch, der in unserer Architektur real
erreichbar ist?

## Warum die Messhygiene hier zaehlt

`torch.cuda.synchronize()` VOR jeder Zeitnahme. Ohne das misst man, wie
schnell Arbeit in die asynchrone CUDA-Queue geschoben wird, nicht wie
schnell sie gerechnet wird -- ein klassischer Weg, GPU-Durchsatz um
Groessenordnungen zu ueberschaetzen. Dazu Aufwaermlauf (cuDNN-Autotuning,
Speicher-Allokator) und Median statt Mittel ueber die Wiederholungen.

## Entscheidungspunkte (vorab, siehe PREREG)

Ausgewertet wird nicht bei Batch 11 allein, sondern gegen den BESTEN der
erreichbaren Punkte **11 / 22 / 44** -- 11 = Threadzahl ohne Umbau, 22/44 =
mit Verschraenkung von k=2/k=4 Suchen je Thread, was ohne Such-Umbau
machbar waere. `#82` wird nur geschlossen, wenn die GPU auch bei 44 den
CPU-Aggregatdurchsatz nicht schlaegt.

CPU-Referenz aus der Vorregistrierung: **17.600-35.200 Evals/s** (11
Threads). Diese Sonde misst sie NICHT nach -- der CPU-Pfad ist die
Rust/tract-Engine, nicht dieses torch-Modell; ein torch-CPU-Wert waere die
falsche Vergleichsgroesse und wuerde die Entscheidung verfaelschen.

Aufruf:

    python tools/gpu_batch_throughput.py --model models/alphazero_v21_2d_brierbest.pth
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))

BATCHES = (1, 2, 4, 8, 11, 16, 22, 32, 44, 64, 128, 256, 512)
REACHABLE = (11, 22, 44)          # ohne Such-Umbau erreichbar
CPU_AGGREGATE = (17_600, 35_200)  # Evals/s, 11 Threads (PREREG)


def build_model(path: Path, device: str):
    import torch

    import neural_net as nn_mod

    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    # Vorhandener gemeinsamer Lader (Task #11 M2.1) statt eigener Konstruktion:
    # er leitet Encoder-Art, Eingabegroesse und Kopf-Bestand aus dem
    # `state_dict` ab -- genau die Groessen, die man hier sonst raten muesste.
    model, encoder = nn_mod.build_model_from_checkpoint(ckpt)
    print(f"Encoder laut Checkpoint: {encoder}, input_size={model.input_size}")
    if encoder != "2d":
        print("  Hinweis: kein 2D-Encoder -- der Flach-Zweig wird alleine gemessen.")
    model.eval().to(device)
    return model, nn_mod, encoder


def measure(model, nn_mod, device: str, batch: int, reps: int, warmup: int) -> float:
    """Median-Evals/s fuer eine Batchgroesse."""
    import torch

    planes = torch.randn(batch, model.planes_channels, 6, 6, device=device)
    flat = torch.randn(batch, model.input_size, device=device)

    with torch.no_grad():
        for _ in range(warmup):
            model(planes, flat)
        if device == "cuda":
            torch.cuda.synchronize()

        rates = []
        for _ in range(reps):
            if device == "cuda":
                torch.cuda.synchronize()
            t0 = time.perf_counter()
            model(planes, flat)
            if device == "cuda":
                torch.cuda.synchronize()
            dt = time.perf_counter() - t0
            rates.append(batch / dt if dt > 0 else float("inf"))
    return statistics.median(rates)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="models/alphazero_v21_2d_brierbest.pth")
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=10)
    ap.add_argument("--out", default="evaluations/gpu_batch_throughput.json")
    args = ap.parse_args()

    import torch

    if not torch.cuda.is_available():
        print("KEINE CUDA-GPU verfuegbar -- Probe nicht durchfuehrbar.")
        return 1
    device = "cuda"
    print(f"GPU: {torch.cuda.get_device_name(0)}")

    path = REPO / args.model
    if not path.exists():
        print(f"Modell fehlt: {path}")
        return 1
    model, nn_mod, encoder = build_model(path, device)

    print(f"\n{'Batch':>6} {'Evals/s':>12}   Verhaeltnis zum CPU-Aggregat (17.600-35.200)")
    results = {}
    for batch in BATCHES:
        rate = measure(model, nn_mod, device, batch, args.reps, args.warmup)
        results[batch] = rate
        lo, hi = rate / CPU_AGGREGATE[1], rate / CPU_AGGREGATE[0]
        mark = " <- erreichbar" if batch in REACHABLE else ""
        print(f"{batch:>6} {rate:>12,.0f}   {lo:>5.2f}x .. {hi:>5.2f}x{mark}")

    best_reachable = max(results[b] for b in REACHABLE if b in results)
    best_at = max((b for b in REACHABLE if results.get(b) == best_reachable), default=None)
    print(f"\nBester erreichbarer Punkt: Batch {best_at} mit {best_reachable:,.0f} Evals/s")
    print(f"CPU-Aggregat (PREREG): {CPU_AGGREGATE[0]:,}-{CPU_AGGREGATE[1]:,} Evals/s")

    if best_reachable < CPU_AGGREGATE[0]:
        verdict = ("REGEL 1: GPU schlaegt das CPU-Aggregat auch bei Batch 44 NICHT "
                   "=> #82 geschlossen, 'nur mit blatt-paralleler Auswertung sinnvoll'")
    elif best_reachable < CPU_AGGREGATE[1]:
        verdict = ("UNENTSCHIEDEN im Referenzband: GPU liegt zwischen unterer und oberer "
                   "CPU-Schaetzung => die CPU-Referenz muss nachgemessen werden, bevor "
                   "entschieden wird (das Band ist zu breit fuer ein Verdikt)")
    else:
        verdict = ("GPU schlaegt das CPU-Aggregat am erreichbaren Batch => Batcher lohnt "
                   "die Implementierungs-Abwaegung; weiter mit Teil 2 des PREREG")
    print(f"\nVERDIKT: {verdict}")

    out = REPO / args.out
    out.write_text(json.dumps({
        "gpu": torch.cuda.get_device_name(0),
        "encoder": encoder,
        "model": args.model,
        "reps": args.reps,
        "warmup": args.warmup,
        "cpu_aggregate_reference": CPU_AGGREGATE,
        "reachable_batches": list(REACHABLE),
        "evals_per_s": {str(k): v for k, v in results.items()},
        "best_reachable_batch": best_at,
        "best_reachable_rate": best_reachable,
        "verdict": verdict,
    }, indent=2), encoding="utf-8")
    print(f"Ergebnis: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
