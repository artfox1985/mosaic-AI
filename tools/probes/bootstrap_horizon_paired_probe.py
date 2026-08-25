# -*- coding: utf-8 -*-
"""PREREG_bootstrap_horizon.md par.9: Horizont 2 gegen 3, GEPAART auf
denselben Zustaenden. Drei vorab festgelegte Kennzahlen.

Keine Python-Reimplementation der Label-Logik -- beide Horizonte laufen ueber
`mosaic_rust.bootstrap_horizon_stage0_probe_json`, also den produktiven
`bootstrap_value_after_rounds`-Pfad.

Aufruf:
    python -u tools/probes/bootstrap_horizon_paired_probe.py [N] [korpus.pkl]

Kostenhinweis: die pyo3-Sonde rechnet je Zustand zusaetzlich den ANKER
(rtv-Kette, ~4,9 s), der fuer diesen Vergleich nicht gebraucht wird -- der
reine Bootstrap-Aufruf kostet 0,16-0,25 s. Ein `with_anchor=false` am
Einstieg wuerde die Messung rund zwanzigfach verbilligen.
"""
import json, pickle, sys, time, random, pathlib
import mosaic_rust as mr

MODEL = "models/alphazero_v21_2d_brierbest.onnx"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
KORPUS = sys.argv[2] if len(sys.argv) > 2 else "data/probe_v2huelle_horizon.pkl"
SEED = 20260825

t_wand0, t_cpu0 = time.time(), time.process_time()

with open(KORPUS, "rb") as fh:
    recs = pickle.load(fh)
# Echten Partieausgang je game_id aus dem letzten Record der Partie.
ausgang = {}
for r in recs:
    if r.get("winner") is not None:
        ausgang[r.get("game_id")] = r["winner"]
tiling = [r for r in recs if (r.get("state") or {}).get("phase") == "tiling"
          and r.get("game_id") in ausgang]
gesamt_verfuegbar = len(tiling)
# Ordnungsfrei ziehen -- nicht die ersten N (Falle vom 2026-08-25).
random.Random(SEED).shuffle(tiling)
tiling = tiling[:N]

diffs, t2s, t3s, br2, br3 = [], [], [], [], []
for i, r in enumerate(tiling):
    sj = json.dumps(r["state"])
    a = json.loads(mr.bootstrap_horizon_stage0_probe_json(sj, MODEL, 1000 + i, 2))
    b = json.loads(mr.bootstrap_horizon_stage0_probe_json(sj, MODEL, 1000 + i, 3))
    pi = r["state"]["current_player"]
    v2, v3 = a["bootstrap_value"][pi], b["bootstrap_value"][pi]
    diffs.append(abs(v3 - v2))
    t2s.append(a["bootstrap_time_ms"]); t3s.append(b["bootstrap_time_ms"])
    gewonnen = 1.0 if ausgang[r["game_id"]] == pi else 0.0
    br2.append((v2 - gewonnen) ** 2); br3.append((v3 - gewonnen) ** 2)
    if (i + 1) % 20 == 0:
        print(f"  {i+1}/{len(tiling)} ...", flush=True)


def mw(v):
    return sum(v) / len(v)


def ci(v):
    m = mw(v)
    sd = (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5
    return 1.96 * sd / len(v) ** 0.5


dp = [x - y for x, y in zip(br3, br2)]
wand = time.time() - t_wand0
cpu = time.process_time() - t_cpu0

print(f"\nZustaende: {len(tiling)} von {gesamt_verfuegbar} (ordnungsfrei, Seed {SEED})")
print(f"1) |Label-Differenz| h3 gegen h2 : {mw(diffs):.4f} +- {ci(diffs):.4f}")
print(f"   Anteil mit Differenz > 0,01   : {100*sum(1 for d in diffs if d>0.01)/len(diffs):.1f} %")
print(f"2) Brier gegen echten Ausgang    : h2 {mw(br2):.4f} +- {ci(br2):.4f}   h3 {mw(br3):.4f} +- {ci(br3):.4f}")
print(f"   gepaart h3-h2                 : {mw(dp):+.4f} +- {ci(dp):.4f}  (negativ = h3 besser)")
print(f"3) Kosten je Label               : h2 {mw(t2s):.1f} ms   h3 {mw(t3s):.1f} ms   "
      f"Faktor {mw(t3s)/mw(t2s):.2f}x")

erg = {
    "prereg": "PREREG_bootstrap_horizon.md par.9",
    "korpus": KORPUS, "modell": MODEL, "seed": SEED,
    "zustaende": len(tiling), "zustaende_verfuegbar": gesamt_verfuegbar,
    "label_differenz": {"mittel": mw(diffs), "ci95": ci(diffs),
                        "anteil_ueber_0_01": sum(1 for d in diffs if d > 0.01) / len(diffs)},
    "brier": {"h2": mw(br2), "h2_ci95": ci(br2), "h3": mw(br3), "h3_ci95": ci(br3),
              "gepaart_h3_minus_h2": mw(dp), "gepaart_ci95": ci(dp)},
    "kosten_ms": {"h2": mw(t2s), "h3": mw(t3s), "faktor": mw(t3s) / mw(t2s)},
    "laufzeit": {"wanduhr_s": round(wand, 1), "cpu_s": round(cpu, 1), "threads": 1,
                 "s_je_partie": round(wand / max(1, len(tiling)), 3)},
}
ziel = pathlib.Path("evaluations/artifacts") / f"bootstrap_horizon_paired_{len(tiling)}.json"
ziel.parent.mkdir(parents=True, exist_ok=True)
for _ in range(5):
    try:
        ziel.write_text(json.dumps(erg, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
        print(f"\nArtefakt: {ziel}  (wanduhr {wand:.0f} s, {wand/max(1,len(tiling)):.1f} s je Zustand)")
        break
    except OSError as e:
        print("Retry:", e, flush=True); time.sleep(1)
