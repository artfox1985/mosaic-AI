# -*- coding: utf-8 -*-
"""Teil-1-Probe zu `evaluations/PREREG_gpu_offloading.md`: ist ein
effektiver Inferenz-Batch von >= 128 durch VERSCHRAENKUNG erreichbar?

Hintergrund: die GPU schlaegt den CPU-Aggregatdurchsatz erst ab Batch ~128
(`tools/gpu_batch_throughput.py`), heute liegt der Batch bei 11 -- so viele
Threads, je genau ein Blatt. Verschraenkung heisst: N Partien gleichzeitig,
ihre Suchen wechseln sich ab, bis zu N Blaetter warten gleichzeitig. Jede
Suche bleibt dabei bitgleich, sie wartet nur laenger.

Diese Sonde baut die Verschraenkung NICHT. Sie misst die zwei Groessen, die
entscheiden, ob sie den noetigen Batch ueberhaupt erreichen kann:

1. **Speicher je gleichzeitiger Suche.** Treiber ist nicht der Spielzustand,
   sondern der Suchbaum: `net_mcts.rs::Node` haelt je Knoten einen VOLLEN
   `GameState`. Gemessen als Zuwachs des **Peak Working Set** ueber einen
   Suchlauf -- Peak und nicht aktuelles RSS, weil der Baum am Ende des Aufrufs
   wieder freigegeben wird und ein RSS-Vergleich danach ~0 zeigen wuerde.
2. **Auslastungsgrad.** Ein Blatt je Partie gilt nur, solange eine Suche
   wirklich auf Bewertung wartet; zwischen Zug-Anwendung, Tiling und
   Rundenuebergang steht keines an. Nach oben begrenzt ihn der Inferenzanteil
   von 62-81 % (Task #81) -- er IST das Tastverhaeltnis. Diese Sonde nimmt
   ihn als BAND aus dem PREREG, sie misst ihn nicht neu.

Ausgabe: erwarteter effektiver Batch und der zugehoerige GPU-Durchsatz aus
der bereits gemessenen Kennlinie, plus das vorregistrierte Verdikt.

Aufruf:

    python tools/interleave_batch_probe.py
"""
from __future__ import annotations

import argparse
import json
import pickle
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))

CURVE = REPO / "evaluations" / "artifacts" / "gpu_batch_throughput.json"
FROZEN = REPO / "evaluations" / "frozen_eval_set.pkl"
MODEL = REPO / "models" / "alphazero_v21_2d_brierbest.onnx"

DUTY_BAND = (0.62, 0.81)      # Inferenzanteil der Self-Play-Zeit (Task #81)
MEMORY_CEILING_GIB = 16.0     # PREREG Regel 4
CPU_AGGREGATE = (17_600, 35_200)


def peak_working_set_bytes() -> int:
    """Peak Working Set des eigenen Prozesses (Windows, ohne psutil)."""
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"(Get-Process -Id {os_getpid()}).PeakWorkingSet64"],
        capture_output=True, text=True,
    )
    return int((out.stdout or "0").strip() or 0)


def os_getpid() -> int:
    import os

    return os.getpid()


def machine_ram_gib() -> tuple[float, float]:
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "$cs=Get-CimInstance Win32_ComputerSystem; $os=Get-CimInstance Win32_OperatingSystem; "
         "\"$($cs.TotalPhysicalMemory);$($os.FreePhysicalMemory)\""],
        capture_output=True, text=True,
    )
    total_b, free_kb = (out.stdout or "0;0").strip().split(";")
    return int(total_b) / 2**30, int(free_kb) / 2**20


def pick_state() -> dict:
    with FROZEN.open("rb") as fh:
        records = pickle.load(fh)["records"]
    for rec in records:
        st = rec["state"]
        if st["round"] == 2 and st["phase"] == "drafting":
            return st
    raise SystemExit("kein passender Zustand im frozen set")


def nearest_rate(curve: dict[str, float], batch: float) -> tuple[int, float]:
    """Gemessener Kennlinien-Punkt, der `batch` am naechsten liegt (nach unten)."""
    points = sorted((int(k), v) for k, v in curve.items())
    best = points[0]
    for b, r in points:
        if b <= batch:
            best = (b, r)
    return best


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sims", type=int, default=400)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--out", default="evaluations/artifacts/interleave_batch_probe.json")
    args = ap.parse_args()

    if not CURVE.exists():
        raise SystemExit(f"Kennlinie fehlt: {CURVE} -- zuerst tools/gpu_batch_throughput.py laufen lassen")
    curve = json.loads(CURVE.read_text(encoding="utf-8"))["evals_per_s"]

    import mosaic_rust

    state = pick_state()
    payload = json.dumps(state)

    # Aufwaermen: Modell laden, Allokator einschwingen -- danach die Basislinie.
    mosaic_rust.net_search_state_json(payload, str(MODEL), 8, 1.5, 1)
    base = peak_working_set_bytes()

    per_search = []
    nodes_seen = []
    for i in range(args.repeats):
        before = peak_working_set_bytes()
        out = json.loads(
            mosaic_rust.net_search_state_json(payload, str(MODEL), args.sims, 1.5, 4242 + i)
        )
        after = peak_working_set_bytes()
        nodes_seen.append(out.get("node_visits") or out.get("simulations") or 0)
        if after > before:
            per_search.append(after - before)

    total_gib, free_gib = machine_ram_gib()
    print(f"Maschine: {total_gib:.1f} GiB RAM gesamt, {free_gib:.1f} GiB frei")
    print(f"Suche: {args.sims} Sims, Knotenbesuche {nodes_seen}")

    if not per_search:
        print("\nPeak Working Set wuchs ueber die Wiederholungen NICHT mehr an --")
        print("der erste Lauf hat das Hochwasser gesetzt. Gemessen wird deshalb der")
        print("Zuwachs des ERSTEN 400-Sims-Laufs gegen die Basislinie nach dem Aufwaermen.")
        peak_after_first = peak_working_set_bytes()
        growth = max(0, peak_after_first - base)
    else:
        growth = max(per_search)
    mib = growth / 2**20
    print(f"Speicherzuwachs je Suche (Peak-Working-Set-Hochwasser): {mib:.1f} MiB")

    if mib <= 0.5:
        print("\nWARNUNG: der Zuwachs ist zu klein zum Rechnen -- entweder ist der Baum")
        print("winzig, oder der Allokator hat schon genug Reserve gehalten. Das Ergebnis")
        print("unten ist dann eine UNTERGRENZE fuer N und damit optimistisch.")

    usable_gib = min(free_gib, MEMORY_CEILING_GIB)
    n_max = int((usable_gib * 2**30) / growth) if growth > 0 else 0
    print(f"\nNutzbarer Speicher (min(frei, Deckel {MEMORY_CEILING_GIB:.0f} GiB)): {usable_gib:.1f} GiB")
    print(f"N_max gleichzeitige Suchen: {n_max}")

    # KORREKTUR 2026-08-10, unmittelbar nach dem ersten Lauf (eigener
    # Denkfehler): aus dem Speicher ein N abzuleiten und mit dem
    # Auslastungsgrad zu multiplizieren, unterstellt Speicher als BINDENDE
    # Schranke. Er ist es nicht -- gemessen ~1-2 MiB je Suche, also N_max ueber
    # 10.000; als praktische Zahl offensichtlich unsinnig. Bindend ist die
    # CPU-seitige BAUMARBEIT (Auswahl, Backup, Zustands-Klonen), und die
    # verschwindet nicht, wenn die Inferenz auf die GPU wandert.
    #
    # Der Speicher beantwortet deshalb nur eine JA/NEIN-Frage: reicht er fuer
    # die Batches, an denen die GPU gewinnt?
    print("")
    print("--- Speicher: reicht er fuer die Gewinnzone? ---")
    mem_for = {}
    for cand in (128, 256, 512, 1024):
        need_gib = cand * growth / 2**30
        mem_for[cand] = need_gib
        ok = "passt" if need_gib <= usable_gib else "zu gross"
        print(f"  {cand:>4} gleichzeitige Suchen: {need_gib:>6.2f} GiB  ({ok})")

    # Der eigentliche Deckel: Amdahl auf der CPU-Restarbeit. Faellt die
    # Inferenz weg, kann die CPU 1/(1-p) mal mehr Blaetter erzeugen -- das ist
    # die NACHFRAGE, die die GPU decken muesste.
    print("")
    print("--- Nachfrage der CPU nach Wegfall der Inferenz (Amdahl) ---")
    for p_share in DUTY_BAND:
        speedup = 1.0 / (1.0 - p_share)
        print(f"  Inferenzanteil {p_share:.0%}: Deckel {speedup:.1f}x, Nachfrage "
              f"{CPU_AGGREGATE[0]*speedup:,.0f}-{CPU_AGGREGATE[1]*speedup:,.0f} Evals/s")
    if "512" in curve:
        print(f"  GPU-Angebot bei Batch 512: {curve['512']:,.0f} Evals/s")

    if mem_for[128] <= usable_gib:
        verdict = ("REGEL 1: Speicher ist KEIN Engpass -- Batch 128-512 passt muehelos "
                   f"({mem_for[128]:.2f}-{mem_for[512]:.2f} GiB) => Weg V (Verschraenkung) "
                   "wird gebaut. Der verbleibende Deckel ist Amdahl (2,6-5,3x), NICHT der "
                   "Batch; neuer Engpass wird die CPU-seitige Baumarbeit, und die ist als "
                   "naechstes zu messen.")
    else:
        verdict = ("REGEL 4: schon Batch 128 sprengt den Speicherdeckel => Verschraenkung "
                   "in dieser Groesse nicht erreichbar")
    print("")
    print(f"VERDIKT: {verdict}")

    (REPO / args.out).write_text(json.dumps({
        "sims": args.sims,
        "node_visits": nodes_seen,
        "memory_per_search_bytes": growth,
        "memory_per_search_mib": mib,
        "ram_total_gib": total_gib,
        "ram_free_gib": free_gib,
        "memory_ceiling_gib": MEMORY_CEILING_GIB,
        "n_max": n_max,
        "duty_band": list(DUTY_BAND),
        "memory_for_batch_gib": {str(k): v for k, v in mem_for.items()},
        "amdahl_ceiling": [1.0/(1.0-DUTY_BAND[0]), 1.0/(1.0-DUTY_BAND[1])],
        "verdict": verdict,
    }, indent=2), encoding="utf-8")
    print(f"Ergebnis: {REPO / args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
